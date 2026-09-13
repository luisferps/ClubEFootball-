begin;

-- FINALIZACAO AUTOMATICA POR LINHA
-- O segundo motor que chega dispara a mesma funcao idempotente. A linha publica
-- anterior fica preservada numa ponte ativa ate a nova composicao fechar.

create table clube_novo.build_publicacao_linha_ativa_v1 (
  linha_id bigint primary key references clube_novo.build_linha_card(id) on delete restrict,
  card_id text not null references clube_novo.carta_jogo(card_id) on delete restrict,
  funcao_id bigint not null references clube_novo.funcao_sistema(id) on delete restrict,
  posicao_id integer not null references clube_novo.posicao_jogo(id) on delete restrict,
  build_otimizador_id bigint not null references clube_novo.build_otimizador(id) on delete restrict,
  build_bonificador_id bigint not null references clube_novo.build_bonificador(id) on delete restrict,
  nota_final numeric not null,
  selo_final_fingerprint text not null,
  publicacao_fingerprint text not null,
  publicacao_v2_fingerprint text not null,
  proveniencia jsonb not null,
  publicada_em timestamptz not null,
  versao_publicacao bigint not null default 1 check (versao_publicacao > 0),
  atualizado_em timestamptz not null default clock_timestamp()
);

create table clube_novo.build_finalizacao_fila_v1 (
  linha_id bigint primary key references clube_novo.build_linha_card(id) on delete cascade,
  estado text not null check (estado in ('aguardando','processando','concluido','erro')),
  prioridade integer not null default 10,
  overall_origem integer,
  tentativas integer not null default 0 check (tentativas >= 0),
  origem_ultima text not null,
  motivo text,
  proxima_tentativa_em timestamptz not null default clock_timestamp(),
  ultima_tentativa_em timestamptz,
  concluido_em timestamptz,
  publicacao_fingerprint text,
  atualizado_em timestamptz not null default clock_timestamp()
);

create table clube_novo.build_finalizacao_evento_v1 (
  id bigint generated always as identity primary key,
  linha_id bigint not null references clube_novo.build_linha_card(id) on delete cascade,
  evento text not null,
  detalhe jsonb not null default '{}'::jsonb,
  criado_em timestamptz not null default clock_timestamp()
);

create table clube_novo.build_pontuacao_final_v2_delta_v1
as select * from clube_novo.build_pontuacao_final_v2 with no data;
alter table clube_novo.build_pontuacao_final_v2_delta_v1
  add primary key (linha_id);

-- Este bootstrap e deliberadamente valido apenas para o incidente em que a
-- origem publica foi comprovada vazia. Outro banco com geracao anterior nao
-- vazia deve receber uma migracao propria de semeadura da ponte antes de trocar
-- leitores; falha aqui evita qualquer janela publica vazia.
do $do$
declare v_origem bigint;
begin
  select count(*) into v_origem from clube_novo.build_pontuacao_final_v2_mat;
  if v_origem<>0 then
    raise exception 'bootstrap recusado: origem publica possui % linhas; semeie a ponte antes da troca',v_origem;
  end if;
end
$do$;

create index build_publicacao_linha_ativa_card_v1_idx
  on clube_novo.build_publicacao_linha_ativa_v1(card_id, nota_final desc, linha_id);
create index build_publicacao_linha_ativa_funcao_v1_idx
  on clube_novo.build_publicacao_linha_ativa_v1(funcao_id, nota_final desc, linha_id);
create index build_finalizacao_fila_estado_v1_idx
  on clube_novo.build_finalizacao_fila_v1(
    estado, prioridade, overall_origem desc nulls last, proxima_tentativa_em, linha_id)
  where estado in ('aguardando','erro');
create index build_finalizacao_evento_linha_v1_idx
  on clube_novo.build_finalizacao_evento_v1(linha_id, criado_em desc);
create index build_pontuacao_final_v2_delta_card_v1_idx
  on clube_novo.build_pontuacao_final_v2_delta_v1(card_id, overall_final desc, linha_id);
create index build_pontuacao_final_v2_delta_funcao_v1_idx
  on clube_novo.build_pontuacao_final_v2_delta_v1(funcao_id, overall_final desc, linha_id);

alter table clube_novo.build_publicacao_linha_ativa_v1 enable row level security;
alter table clube_novo.build_finalizacao_fila_v1 enable row level security;
alter table clube_novo.build_finalizacao_evento_v1 enable row level security;
alter table clube_novo.build_pontuacao_final_v2_delta_v1 enable row level security;
revoke all on clube_novo.build_publicacao_linha_ativa_v1,
  clube_novo.build_finalizacao_fila_v1,
  clube_novo.build_finalizacao_evento_v1,
  clube_novo.build_pontuacao_final_v2_delta_v1
  from public, anon, authenticated;
grant select on clube_novo.build_publicacao_linha_ativa_v1,
  clube_novo.build_finalizacao_fila_v1,
  clube_novo.build_finalizacao_evento_v1,
  clube_novo.build_pontuacao_final_v2_delta_v1
  to service_role;

comment on table clube_novo.build_publicacao_linha_ativa_v1 is
  'Ponte atomica da ultima versao validada de cada linha. Protege a leitura publica enquanto a proxima versao recebe os dois motores.';
comment on table clube_novo.build_finalizacao_fila_v1 is
  'Retry duravel da composicao, normalizacao e publicacao automatica por linha.';
comment on table clube_novo.build_pontuacao_final_v2_delta_v1 is
  'Read model incremental: uma linha e substituida na mesma transacao da ponte publica, sem refresh global.';

create view clube_novo.build_pontuacao_final_v2_publica_v1
with (security_invoker = true)
as
with base as (
  select d.publicacao_v2_fingerprint,d.linha_id,d.card_id,d.funcao_id,d.posicao_id,
    d.build_otimizador_id,d.build_bonificador_id,d.tecnico_id,d.barras,
    d.impeto_adicional_codigo,d.habilidades_adicionais,d.atributos_finais,d.arows_snapshot,
    d.pontuacao_otimizador_bruta_evidencia,d.pontuacao_otimizador_normalizada,
    d.bonus_pe,d.bonus_fisico_total,d.bonus_posicao,d.bonus_playstyle_1,
    d.bonus_playstyle_2,d.bonus_ia,d.bonus_outros,d.bonus_total_bonificador,
    d.overall_final,d.normalizacao_fingerprint,d.calculo_banco_fingerprint,
    d.carta_fingerprint,d.formula_fingerprint,d.contrato_fingerprint,
    d.otimizador_resultado_fingerprint,d.bonificador_resultado_fingerprint,
    d.publicacao_fingerprint_v1,d.publicada_em,d.publicacao_linha_fingerprint_v2,
    max(d.overall_final) over(partition by d.funcao_id) as topo_funcao,
    d.estado_final,d.motivo_final,d.proveniencia
  from clube_novo.build_pontuacao_final_v2_delta_v1 d
  join clube_novo.build_publicacao_linha_ativa_v1 a
    on a.linha_id=d.linha_id
   and a.build_otimizador_id=d.build_otimizador_id
   and a.build_bonificador_id=d.build_bonificador_id
)
select b.publicacao_v2_fingerprint,b.linha_id,b.card_id,b.funcao_id,b.posicao_id,
  b.build_otimizador_id,b.build_bonificador_id,b.tecnico_id,b.barras,
  b.impeto_adicional_codigo,b.habilidades_adicionais,b.atributos_finais,b.arows_snapshot,
  b.pontuacao_otimizador_bruta_evidencia,b.pontuacao_otimizador_normalizada,
  b.bonus_pe,b.bonus_fisico_total,b.bonus_posicao,b.bonus_playstyle_1,
  b.bonus_playstyle_2,b.bonus_ia,b.bonus_outros,b.bonus_total_bonificador,
  b.overall_final,b.normalizacao_fingerprint,b.calculo_banco_fingerprint,
  b.carta_fingerprint,b.formula_fingerprint,b.contrato_fingerprint,
  b.otimizador_resultado_fingerprint,b.bonificador_resultado_fingerprint,
  b.publicacao_fingerprint_v1,b.publicada_em,b.publicacao_linha_fingerprint_v2,
  b.topo_funcao,
  case when b.topo_funcao>0 then 100*b.overall_final/b.topo_funcao end as percentual_topo,
  b.estado_final,b.motivo_final,b.proveniencia,
  c.nome as carta_nome,c.tipo as carta_tipo,
  case when c.box is not null and btrim(c.box)<>''
    and lower(btrim(c.box))<>all(array['0','dummy','[[not use]]']) then btrim(c.box) end as carta_box,
  c.overall as carta_overall,
  case when c.foto_url_cloudinary ~ '^https://res\\.cloudinary\\.com/[A-Za-z0-9_-]+/image/upload/'
    then c.foto_url_cloudinary end as foto_url_cloudinary,
  coalesce(fs.sigla,'') as funcao_codigo,fs.rotulo as funcao_nome,
  coalesce(p.codigo_pt,'') as posicao_codigo,p.nome_pt as posicao_nome,
  coalesce(t.nome_en,b.tecnico_id::text) as tecnico_nome,
  case when b.impeto_adicional_codigo is not null then jsonb_build_object(
    'codigo',b.impeto_adicional_codigo,'nome',clube_novo.impeto_nome_v1(b.impeto_adicional_codigo),
    'de_goleiro',clube_novo.impeto_e_de_goleiro_v1(b.impeto_adicional_codigo),
    'efeitos',clube_novo.impeto_efeitos_v1(b.impeto_adicional_codigo)) end as impeto_adicional,
  case when bl.impeto_condicional_codigo is not null then jsonb_build_object(
    'codigo',bl.impeto_condicional_codigo,'nome',clube_novo.impeto_nome_v1(bl.impeto_condicional_codigo),
    'degrau',bl.impeto_condicional_nivel,'degraus',jsonb_build_array(1,2,3),
    'regra','degrau pela quantidade de jogadores da condicao em campo: 1 a 7 = +1, 8 a 10 = +2, 11 a 23 = +3',
    'efeitos',clube_novo.impeto_efeitos_v1(bl.impeto_condicional_codigo)) end as impeto_condicional,
  row_number() over(order by b.overall_final desc,b.card_id,b.funcao_id,b.posicao_id,b.linha_id) as ordem_geral,
  row_number() over(partition by b.funcao_id order by b.overall_final desc,b.card_id,b.posicao_id,b.linha_id) as ordem_na_funcao
from base b
join clube_novo.carta_jogo c on c.card_id=b.card_id
join clube_novo.build_linha_card bl on bl.id=b.linha_id
join clube_novo.funcao_sistema fs on fs.id=b.funcao_id
join clube_novo.posicao_jogo p on p.id=b.posicao_id
left join clube_novo.tecnico_jogo t on t.id=b.tecnico_id;

revoke all on clube_novo.build_pontuacao_final_v2_publica_v1
  from public, anon, authenticated;
grant select on clube_novo.build_pontuacao_final_v2_publica_v1 to service_role;

-- Migra a RPC V2 vigente para a fonte incremental. Nao cria alias legado.
do $do$
declare v_def text; v_nova text;
begin
  select pg_get_functiondef(p.oid) into v_def
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.proname='frontend_build_publicada_v2'
    and p.proargtypes='25 20 23 23'::oidvector;
  if v_def is null or position('clube_novo.build_pontuacao_final_v2_'||'mat' in v_def)=0 then
    raise exception 'RPC V2 vigente nao usa a materializacao esperada';
  end if;
  v_nova:=replace(v_def,
    'clube_novo.build_pontuacao_final_v2_'||'mat',
    'clube_novo.build_pontuacao_final_v2_publica_v1');
  execute v_nova;
end
$do$;
revoke all on function public.frontend_build_publicada_v2(text,bigint,integer,integer)
  from public, anon, authenticated;
grant execute on function public.frontend_build_publicada_v2(text,bigint,integer,integer)
  to anon, authenticated, service_role, bonificador_runtime;

-- A RPC V1 passa a ler exclusivamente a ponte ativa.
create or replace function public.frontend_build_publicada_v1(
  p_card_id text default null,
  p_funcao_id bigint default null,
  p_limit integer default 100,
  p_offset integer default 0
)
returns table(
  schema_versao text, linha_id bigint, card_id text, carta_nome text,
  carta_tipo text, carta_box text, carta_overall integer, funcao_id bigint,
  funcao_codigo text, funcao_nome text, posicao_id integer,
  posicao_codigo text, posicao_nome text, build_otimizador_id bigint,
  build_bonificador_id bigint, pontuacao_final numeric, estado_final text,
  motivo_final text, selo_final_fingerprint text, publicada_em timestamptz,
  proveniencia jsonb
)
language sql stable security definer set search_path=''
as $function$
  select 'clube-frontend-build-publicada-v1'::text,
    a.linha_id,a.card_id,c.nome,c.tipo,c.box,c.overall,
    a.funcao_id,coalesce(f.sigla,'')::text,f.rotulo,
    a.posicao_id,coalesce(p.codigo_pt,'')::text,p.nome_pt,
    a.build_otimizador_id,a.build_bonificador_id,a.nota_final,
    'publicada'::text,null::text,a.selo_final_fingerprint,a.publicada_em,a.proveniencia
  from clube_novo.build_publicacao_linha_ativa_v1 a
  join clube_novo.carta_jogo c on c.card_id=a.card_id
  join clube_novo.funcao_sistema f on f.id=a.funcao_id
  join clube_novo.posicao_jogo p on p.id=a.posicao_id
  where (p_card_id is null or a.card_id=p_card_id)
    and (p_funcao_id is null or a.funcao_id=p_funcao_id)
  order by a.nota_final desc,a.card_id,a.funcao_id,a.posicao_id,a.linha_id
  limit least(greatest(coalesce(p_limit,100),1),500)
  offset greatest(coalesce(p_offset,0),0)
$function$;
revoke all on function public.frontend_build_publicada_v1(text,bigint,integer,integer)
  from public, anon, authenticated;
grant execute on function public.frontend_build_publicada_v1(text,bigint,integer,integer)
  to anon, authenticated, service_role;

-- Substitui a CTE publicadas da Ficha vigente pelos IDs e nota da ponte ativa.
do $do$
declare v_def text; v_nova text; v_antiga text; v_ativa text;
begin
  select pg_get_functiondef(p.oid) into v_def
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.proname='site_novo_ficha_v1'
    and p.proargtypes='25 20'::oidvector;
  v_antiga:=$old$publicadas as (
  select
    l.id,
    l.card_id,
    l.funcao_id,
    l.posicao_id,
    l.build_otimizador_id,
    l.build_bonificador_id,
    l.nota_final,
    l.nota_publicada_em_v1,
    l.impeto_condicional_codigo,
    l.impeto_condicional_nivel,
    bo.tecnico_id,
    bo.barras,
    bo.impeto_adicional_codigo,
    bo.habilidades_adicionais,
    bo.atributos_finais,
    bb.bonus_pe,
    bb.bonus_fisico_total,
    bb.bonus_posicao,
    bb.bonus_playstyle_1,
    bb.bonus_playstyle_2,
    bb.bonus_ia,
    bb.bonus_outros,
    bb.bonus_total,
    bb.bonus_fisico_detalhe
  from entrada e
  join clube_novo.build_linha_card l
    on l.card_id = e.card_id
  join clube_novo.build_otimizador bo
    on bo.id = l.build_otimizador_id
  join clube_novo.build_bonificador bb
    on bb.id = l.build_bonificador_id
  where l.execucao_tipo = 'producao'
    and l.lote_teste_id is null
    and not (l.pendencias @> array['teste_nao_publicado'::text])
    and l.publicacao_fingerprint is not null
    and l.publicada_em is not null
    and l.nota_final is not null
    and l.nota_publicacao_fingerprint_v1 is not null
    and l.nota_publicada_em_v1 is not null
    and l.build_otimizador_id is not null
    and l.build_bonificador_id is not null
),
$old$;
  v_ativa:=$new$publicadas as (
  select
    l.id,
    l.card_id,
    l.funcao_id,
    l.posicao_id,
    a.build_otimizador_id,
    a.build_bonificador_id,
    a.nota_final,
    a.publicada_em as nota_publicada_em_v1,
    l.impeto_condicional_codigo,
    l.impeto_condicional_nivel,
    bo.tecnico_id,
    bo.barras,
    bo.impeto_adicional_codigo,
    bo.habilidades_adicionais,
    bo.atributos_finais,
    bb.bonus_pe,
    bb.bonus_fisico_total,
    bb.bonus_posicao,
    bb.bonus_playstyle_1,
    bb.bonus_playstyle_2,
    bb.bonus_ia,
    bb.bonus_outros,
    bb.bonus_total,
    bb.bonus_fisico_detalhe
  from entrada e
  join clube_novo.build_linha_card l
    on l.card_id = e.card_id
  join clube_novo.build_publicacao_linha_ativa_v1 a
    on a.linha_id = l.id
  join clube_novo.build_otimizador bo
    on bo.id = a.build_otimizador_id
  join clube_novo.build_bonificador bb
    on bb.id = a.build_bonificador_id
  where l.execucao_tipo = 'producao'
    and l.lote_teste_id is null
    and not (l.pendencias @> array['teste_nao_publicado'::text])
),
$new$;
  if v_def is null or position(v_antiga in v_def)=0 then
    raise exception 'CTE publicadas da Ficha vigente divergiu do contrato auditado';
  end if;
  v_nova:=replace(v_def,v_antiga,v_ativa);
  execute v_nova;
end
$do$;

create function public.site_novo_publicacao_status_v1(p_card_id text default null)
returns jsonb
language plpgsql stable security definer set search_path=''
as $function$
declare
  v_lote clube_novo.bonificador_correcao_lote_v1%rowtype;
  v_total integer:=0; v_preparadas integer:=0; v_processando integer:=0; v_falhas integer:=0;
  v_card_fila boolean:=false; v_publicadas integer:=0; v_estado text;
begin
  select * into v_lote from clube_novo.bonificador_correcao_lote_v1
  where tipo='integral' and motor_versao='v10-0409-fisico-regra-aprovada-v1'
    and estado in ('preparado','rodando','pausando','pausado','processado')
  order by criado_em desc limit 1;
  if v_lote.id is not null then
    select count(*),count(*)filter(where estado_item='preparado'),
      count(*)filter(where estado_item='processando'),count(*)filter(where estado_item='falha')
    into v_total,v_preparadas,v_processando,v_falhas
    from clube_novo.bonificador_correcao_item_v1 where lote_id=v_lote.id;
  end if;
  if nullif(btrim(p_card_id),'') is not null then
    select count(*) into v_publicadas from clube_novo.build_publicacao_linha_ativa_v1
      where card_id=btrim(p_card_id);
    if v_lote.id is not null then
      select exists(select 1 from clube_novo.build_linha_card l
        join clube_novo.bonificador_correcao_item_v1 i
          on i.lote_id=v_lote.id and i.build_linha_card_id=l.id
        where l.card_id=btrim(p_card_id)) into v_card_fila;
    end if;
  end if;
  v_estado:=case
    when v_publicadas>0 and v_card_fila then 'card_publicado_em_atualizacao'
    when v_publicadas>0 then 'card_publicado'
    when v_card_fila then 'builds_em_atualizacao'
    when p_card_id is null and v_lote.id is not null then 'publicacao_incremental_em_andamento'
    else 'card_sem_build_publicada' end;
  return jsonb_build_object(
    'contrato','site-novo-publicacao-status-v1','versao',1,'estado',v_estado,
    'card_id',nullif(btrim(p_card_id),''),'card_em_atualizacao',v_card_fila,
    'linhas_publicadas_do_card',v_publicadas,
    'lote_v10',case when v_lote.id is null then null else jsonb_build_object(
      'id',v_lote.id,'estado',v_lote.estado,'total',v_total,'preparadas',v_preparadas,
      'processando',v_processando,'falhas',v_falhas,
      'pendentes',v_total-v_preparadas-v_processando-v_falhas) end
  );
end
$function$;

alter function public.site_novo_ficha_v1(text,bigint)
  rename to site_novo_ficha_base_publicada_v1;

create function public.site_novo_ficha_v1(p_card_id text default null,p_linha_id bigint default null)
returns jsonb
language plpgsql stable security definer set search_path=''
as $function$
declare v_base jsonb; v_pub jsonb;
begin
  v_base:=public.site_novo_ficha_base_publicada_v1(p_card_id,p_linha_id);
  v_pub:=public.site_novo_publicacao_status_v1(p_card_id);
  if v_base->>'status' in ('card_sem_build_publicada','linha_nao_encontrada_ou_nao_publicada')
     and coalesce((v_pub->>'card_em_atualizacao')::boolean,false) then
    v_base:=jsonb_set(v_base,'{status}','"builds_em_atualizacao"'::jsonb,true);
    v_base:=jsonb_set(v_base,'{mensagem}',to_jsonb(
      'As builds deste card estao em atualizacao. Cada linha aparecera assim que os dois motores forem validados.'::text),true);
  end if;
  return v_base||jsonb_build_object('publicacao',v_pub);
end
$function$;

revoke all on function public.site_novo_ficha_base_publicada_v1(text,bigint),
  public.site_novo_publicacao_status_v1(text),
  public.site_novo_ficha_v1(text,bigint)
  from public, anon, authenticated;
grant execute on function public.site_novo_publicacao_status_v1(text),
  public.site_novo_ficha_v1(text,bigint)
  to anon, authenticated, service_role;

create function clube_novo.finalizar_publicar_linha_v1(p_linha_id bigint,p_origem text default 'desconhecida')
returns jsonb
language plpgsql
security definer
set search_path=''
as $function$
declare
  l clube_novo.build_linha_card%rowtype;
  o clube_novo.build_otimizador%rowtype;
  b clube_novo.build_bonificador%rowtype;
  f record;
  v_bonus_id bigint;
  v_agora timestamptz:=clock_timestamp();
  v_numerador numeric; v_denominador numeric; v_nota_motor numeric; v_nota_final numeric;
  v_linha_publicacao_fp text; v_publicacao_v2_fp text; v_proveniencia jsonb;
  v_delta integer; v_ativa clube_novo.build_publicacao_linha_ativa_v1%rowtype;
  v_erro text; v_estado text; v_motivo text;
begin
  if p_linha_id is null then raise exception 'finalizacao: linha obrigatoria'; end if;
  select * into l from clube_novo.build_linha_card where id=p_linha_id for update;
  if l.id is null then return jsonb_build_object('ok',false,'estado','erro','motivo','linha inexistente'); end if;

  insert into clube_novo.build_finalizacao_fila_v1(
    linha_id,estado,prioridade,overall_origem,tentativas,origem_ultima,
    proxima_tentativa_em,ultima_tentativa_em,atualizado_em)
  select l.id,'processando',coalesce((
      select min(i.prioridade_grupo)::integer
      from clube_novo.bonificador_correcao_item_v1 i
      join clube_novo.bonificador_correcao_lote_v1 lo on lo.id=i.lote_id
      where i.build_linha_card_id=l.id and i.estado_item='preparado'
        and lo.motor_versao='v10-0409-fisico-regra-aprovada-v1'
    ),10),c.overall,1,coalesce(nullif(p_origem,''),'desconhecida'),v_agora,v_agora,v_agora
  from clube_novo.carta_jogo c where c.card_id=l.card_id
  on conflict(linha_id) do update set estado='processando',
    tentativas=clube_novo.build_finalizacao_fila_v1.tentativas+1,
    prioridade=least(clube_novo.build_finalizacao_fila_v1.prioridade,excluded.prioridade),
    overall_origem=excluded.overall_origem,origem_ultima=excluded.origem_ultima,
    ultima_tentativa_em=v_agora,atualizado_em=v_agora;

  select i.build_bonificador_id_novo into v_bonus_id
  from clube_novo.bonificador_correcao_item_v1 i
  join clube_novo.bonificador_correcao_lote_v1 lo on lo.id=i.lote_id
  join clube_novo.build_bonificador bx on bx.id=i.build_bonificador_id_novo
  where i.build_linha_card_id=l.id and i.estado_item='preparado'
    and bx.motor_versao='v10-0409-fisico-regra-aprovada-v1'
    and bx.formula_fingerprint='756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
    and bx.contrato_versao='bonificador-regua-v3'
  order by lo.criado_em desc,i.preparado_em desc limit 1;
  if v_bonus_id is null then
    select bx.id into v_bonus_id
    from clube_novo.build_bonificador bx
    where bx.id=l.build_bonificador_id
      and bx.motor_versao='v10-0409-fisico-regra-aprovada-v1'
      and bx.formula_fingerprint='756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
      and bx.contrato_versao='bonificador-regua-v3';
  end if;

  if l.build_otimizador_id is null or l.estado_otimizador<>'concluido' then
    v_estado:='aguardando'; v_motivo:='aguardando Otimizador concluido';
  elsif v_bonus_id is null then
    v_estado:='aguardando'; v_motivo:='aguardando Bonificador V10';
  else
    select * into o from clube_novo.build_otimizador where id=l.build_otimizador_id;
    select * into b from clube_novo.build_bonificador where id=v_bonus_id;
    if o.id is null then v_estado:='erro'; v_motivo:='resultado do Otimizador inexistente';
    elsif b.id is null then v_estado:='erro'; v_motivo:='resultado do Bonificador inexistente';
    elsif b.motor_versao<>'v10-0409-fisico-regra-aprovada-v1'
       or b.formula_fingerprint<>'756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
       or b.contrato_versao<>'bonificador-regua-v3' then
      v_estado:='erro'; v_motivo:='Bonificador V9 ou V10 sem selo aprovado';
    elsif o.carta_versao<>l.carta_versao or b.carta_versao<>l.carta_versao
       or o.carta_fingerprint<>l.carta_fingerprint or b.carta_fingerprint<>l.carta_fingerprint then
      v_estado:='erro'; v_motivo:='versao ou fingerprint da carta incompatível';
    elsif o.resultado_fingerprint is distinct from l.snapshot_otimizador_fingerprint then
      v_estado:='erro'; v_motivo:='selo do Otimizador nao coincide com a linha';
    elsif jsonb_typeof(o.atributos_finais)<>'array' or jsonb_array_length(o.atributos_finais)<>26
       or jsonb_typeof(coalesce(o.atributos_internos,o.atributos_finais))<>'array'
       or jsonb_array_length(coalesce(o.atributos_internos,o.atributos_finais))<>26
       or o.arows_snapshot is null then
      v_estado:='aguardando'; v_motivo:='aguardando 26 atributos e arows do Otimizador';
    elsif cardinality(l.pendencias)<>0 or l.execucao_tipo<>'producao' or l.lote_teste_id is not null
       or l.pendencias @> array['teste_nao_publicado'::text] then
      v_estado:='erro'; v_motivo:='linha nao e publicavel pelo contrato produtivo';
    end if;
  end if;

  if v_estado is not null then
    update clube_novo.build_finalizacao_fila_v1 set estado=v_estado,motivo=v_motivo,
      proxima_tentativa_em=v_agora+case when v_estado='erro' then interval '1 hour' else interval '5 minutes' end,
      atualizado_em=v_agora where linha_id=l.id;
    return jsonb_build_object('ok',v_estado<>'erro','linha_id',l.id,'estado',v_estado,'motivo',v_motivo);
  end if;

  select * into v_ativa from clube_novo.build_publicacao_linha_ativa_v1 where linha_id=l.id;
  if v_ativa.linha_id is not null
     and v_ativa.build_otimizador_id=l.build_otimizador_id
     and v_ativa.build_bonificador_id=v_bonus_id
     and l.build_bonificador_id=v_bonus_id
     and l.nota_final is not distinct from v_ativa.nota_final
     and l.nota_bonificador_resultado_fingerprint is not distinct from b.resultado_fingerprint
     and l.nota_otimizador_resultado_fingerprint is not distinct from o.resultado_fingerprint
     and exists(select 1 from clube_novo.build_pontuacao_final_v2_delta_v1 d where d.linha_id=l.id) then
    update clube_novo.build_finalizacao_fila_v1 set estado='concluido',motivo='idempotente',
      concluido_em=coalesce(concluido_em,v_agora),publicacao_fingerprint=v_ativa.publicacao_fingerprint,
      atualizado_em=v_agora where linha_id=l.id;
    return jsonb_build_object('ok',true,'linha_id',l.id,'estado','ja_publicada',
      'publicacao_fingerprint',v_ativa.publicacao_fingerprint,'idempotente',true);
  end if;

  begin
    perform set_config('clube_novo.finalizacao_linha_em_curso',l.id::text,true);
    update clube_novo.build_linha_card set
      build_bonificador_id=v_bonus_id,
      bonificador_motor_versao=b.motor_versao,
      bonificador_contrato_versao=b.contrato_versao,
      snapshot_bonificador_fingerprint=b.resultado_fingerprint,
      publicacao_fingerprint=null,publicada_em=null,
      nota_contrato=null,nota_otimizador_resultado_fingerprint=null,
      nota_bonificador_resultado_fingerprint=null,nota_carta_fingerprint=null,
      nota_formula_fingerprint=null,nota_contrato_fingerprint=null,
      nota_bruta_selada=null,nota_bonus_pe=null,nota_bonus_fisico_total=null,
      nota_bonus_posicao=null,nota_bonus_playstyle_1=null,nota_bonus_playstyle_2=null,
      nota_bonus_ia=null,nota_bonus_outros=null,nota_bonus_total=null,
      nota_numerador=null,nota_denominador=null,nota_do_motor=null,nota_final=null,
      nota_normalizacao_fingerprint=null,nota_calculo_fingerprint=null,
      nota_publicacao_fingerprint_v1=null,nota_publicada_em_v1=null,nota_calculada_em=null,
      atualizado_em=v_agora
    where id=l.id;

    select * into f from clube_novo.build_pontuacao_final_v1 where linha_id=l.id;
    if f.linha_id is null or f.estado_final<>'elegivel_para_publicacao'
       or f.selo_final_fingerprint is null then
      raise exception 'linha nao ficou elegivel: %',coalesce(f.motivo_final,'sem contrato final');
    end if;

    v_numerador:=clube_novo.calcular_numerador_normalizacao_v2(
      coalesce(o.atributos_internos,o.atributos_finais),o.arows_snapshot);
    v_denominador:=clube_novo.calcular_denominador_normalizacao_v2(o.arows_snapshot);
    v_nota_motor:=clube_novo.calcular_pontuacao_normalizada_v2(
      coalesce(o.atributos_internos,o.atributos_finais),o.arows_snapshot);
    v_nota_final:=v_nota_motor+b.bonus_total;

    update clube_novo.build_linha_card set
      publicacao_fingerprint=f.selo_final_fingerprint,publicada_em=v_agora,
      nota_contrato='clube-novo-pontuacao-normalizada-v2',
      nota_otimizador_resultado_fingerprint=o.resultado_fingerprint,
      nota_bonificador_resultado_fingerprint=b.resultado_fingerprint,
      nota_carta_fingerprint=o.carta_fingerprint,
      nota_formula_fingerprint=o.formula_fingerprint,
      nota_contrato_fingerprint=o.contrato_fingerprint,
      nota_bruta_selada=f.pontuacao_otimizador,
      nota_bonus_pe=b.bonus_pe,nota_bonus_fisico_total=b.bonus_fisico_total,
      nota_bonus_posicao=b.bonus_posicao,nota_bonus_playstyle_1=b.bonus_playstyle_1,
      nota_bonus_playstyle_2=b.bonus_playstyle_2,nota_bonus_ia=b.bonus_ia,
      nota_bonus_outros=coalesce(b.bonus_outros,'{}'::jsonb),nota_bonus_total=b.bonus_total,
      nota_numerador=v_numerador,nota_denominador=v_denominador,
      nota_do_motor=v_nota_motor,nota_final=v_nota_final,
      nota_normalizacao_fingerprint=clube_novo.fingerprint_normalizacao_v2(
        l.id,o.id,b.id,o.resultado_fingerprint,b.resultado_fingerprint,f.selo_final_fingerprint),
      nota_calculo_fingerprint=clube_novo.fingerprint_calculo_pontuacao_v2(
        l.id,coalesce(o.atributos_internos,o.atributos_finais),o.arows_snapshot,b.bonus_total),
      nota_publicacao_fingerprint_v1=f.selo_final_fingerprint,
      nota_publicada_em_v1=v_agora,nota_calculada_em=v_agora,atualizado_em=v_agora
    where id=l.id;

    v_linha_publicacao_fp:=pg_catalog.encode(extensions.digest(pg_catalog.convert_to(
      jsonb_build_object(
        'contrato','clube-novo-pontuacao-final-v2','linha_id',l.id,
        'calculo_banco_fingerprint',clube_novo.fingerprint_calculo_pontuacao_v2(
          l.id,coalesce(o.atributos_internos,o.atributos_finais),o.arows_snapshot,b.bonus_total),
        'bonificador_resultado_fingerprint',b.resultado_fingerprint,
        'overall_final',v_nota_final,'publicacao_fingerprint_v1',f.selo_final_fingerprint
      )::text,'UTF8'::name),'sha256'),'hex');
    v_publicacao_v2_fp:=pg_catalog.encode(extensions.digest(pg_catalog.convert_to(
      jsonb_build_object('contrato','clube-novo-publicacao-automatica-por-linha-v1',
        'linha_id',l.id,'publicacao_linha_fingerprint_v2',v_linha_publicacao_fp)::text,
      'UTF8'::name),'sha256'),'hex');
    v_proveniencia:=jsonb_build_object(
      'contrato','clube-novo-pontuacao-final-v2','modo','automatico_por_linha',
      'linha_id',l.id,
      'otimizador',jsonb_build_object('id',o.id,'resultado_fingerprint',o.resultado_fingerprint,
        'pontuacao_bruta_apenas_evidencia',f.pontuacao_otimizador,
        'pontuacao_normalizada',v_nota_motor),
      'bonificador',jsonb_build_object('id',b.id,'resultado_fingerprint',b.resultado_fingerprint,
        'componentes',jsonb_build_object('pe',b.bonus_pe,'fisico',b.bonus_fisico_total,
          'posicao',b.bonus_posicao,'playstyle_1',b.bonus_playstyle_1,
          'playstyle_2',b.bonus_playstyle_2,'ia',b.bonus_ia,
          'outros',coalesce(b.bonus_outros,'{}'::jsonb)),
        'bonus_total',b.bonus_total),
      'pontuacao_final_oficial',v_nota_final,
      'publicacao_v1',f.selo_final_fingerprint,'publicacao_v2',v_linha_publicacao_fp);

    delete from clube_novo.build_pontuacao_final_v2_delta_v1 where linha_id=l.id;
    insert into clube_novo.build_pontuacao_final_v2_delta_v1(
      publicacao_v2_fingerprint,linha_id,card_id,funcao_id,posicao_id,
      build_otimizador_id,build_bonificador_id,tecnico_id,barras,
      impeto_adicional_codigo,habilidades_adicionais,atributos_finais,arows_snapshot,
      pontuacao_otimizador_bruta_evidencia,pontuacao_otimizador_normalizada,
      bonus_pe,bonus_fisico_total,bonus_posicao,bonus_playstyle_1,bonus_playstyle_2,
      bonus_ia,bonus_outros,bonus_total_bonificador,overall_final,
      normalizacao_fingerprint,calculo_banco_fingerprint,carta_fingerprint,
      formula_fingerprint,contrato_fingerprint,otimizador_resultado_fingerprint,
      bonificador_resultado_fingerprint,publicacao_fingerprint_v1,publicada_em,
      publicacao_linha_fingerprint_v2,topo_funcao,percentual_topo,
      estado_final,motivo_final,proveniencia)
    values(
      v_publicacao_v2_fp,l.id,l.card_id,l.funcao_id,l.posicao_id,
      o.id,b.id,o.tecnico_id,o.barras,o.impeto_adicional_codigo,o.habilidades_adicionais,
      o.atributos_finais,o.arows_snapshot,f.pontuacao_otimizador,v_nota_motor,
      b.bonus_pe,b.bonus_fisico_total,b.bonus_posicao,b.bonus_playstyle_1,
      b.bonus_playstyle_2,b.bonus_ia,coalesce(b.bonus_outros,'{}'::jsonb),b.bonus_total,
      v_nota_final,
      clube_novo.fingerprint_normalizacao_v2(l.id,o.id,b.id,o.resultado_fingerprint,
        b.resultado_fingerprint,f.selo_final_fingerprint),
      clube_novo.fingerprint_calculo_pontuacao_v2(l.id,
        coalesce(o.atributos_internos,o.atributos_finais),o.arows_snapshot,b.bonus_total),
      o.carta_fingerprint,o.formula_fingerprint,o.contrato_fingerprint,
      o.resultado_fingerprint,b.resultado_fingerprint,f.selo_final_fingerprint,v_agora,
      v_linha_publicacao_fp,null,null,'publicada',
      'PUBLICADA_AUTOMATICAMENTE_POR_LINHA',v_proveniencia);
    get diagnostics v_delta=row_count;
    if v_delta<>1 then raise exception 'read model incremental recebeu % linhas',v_delta; end if;

    insert into clube_novo.build_publicacao_linha_ativa_v1(
      linha_id,card_id,funcao_id,posicao_id,build_otimizador_id,build_bonificador_id,
      nota_final,selo_final_fingerprint,publicacao_fingerprint,publicacao_v2_fingerprint,
      proveniencia,publicada_em,versao_publicacao,atualizado_em)
    select l.id,l.card_id,l.funcao_id,l.posicao_id,o.id,b.id,v_nota_final,
      f.selo_final_fingerprint,f.selo_final_fingerprint,d.publicacao_v2_fingerprint,
      v_proveniencia,v_agora,1,v_agora
    from clube_novo.build_pontuacao_final_v2_delta_v1 d where d.linha_id=l.id
    on conflict(linha_id) do update set
      card_id=excluded.card_id,funcao_id=excluded.funcao_id,posicao_id=excluded.posicao_id,
      build_otimizador_id=excluded.build_otimizador_id,
      build_bonificador_id=excluded.build_bonificador_id,nota_final=excluded.nota_final,
      selo_final_fingerprint=excluded.selo_final_fingerprint,
      publicacao_fingerprint=excluded.publicacao_fingerprint,
      publicacao_v2_fingerprint=excluded.publicacao_v2_fingerprint,
      proveniencia=excluded.proveniencia,publicada_em=excluded.publicada_em,
      versao_publicacao=clube_novo.build_publicacao_linha_ativa_v1.versao_publicacao+1,
      atualizado_em=excluded.atualizado_em;

    if not exists(select 1 from clube_novo.build_pontuacao_final_v2_publica_v1 p
      join clube_novo.build_publicacao_linha_ativa_v1 a using(linha_id)
      where p.linha_id=l.id and p.build_otimizador_id=a.build_otimizador_id
        and p.build_bonificador_id=a.build_bonificador_id and p.overall_final=a.nota_final) then
      raise exception 'readback da ponte publica falhou';
    end if;
  exception when others then
    get stacked diagnostics v_erro=message_text;
    update clube_novo.build_finalizacao_fila_v1 set estado='erro',motivo=v_erro,
      proxima_tentativa_em=clock_timestamp()+interval '10 minutes',atualizado_em=clock_timestamp()
      where linha_id=l.id;
    insert into clube_novo.build_finalizacao_evento_v1(linha_id,evento,detalhe)
      values(l.id,'falhou',jsonb_build_object('origem',p_origem,'erro',v_erro));
    return jsonb_build_object('ok',false,'linha_id',l.id,'estado','erro','motivo',v_erro);
  end;

  update clube_novo.build_finalizacao_fila_v1 set estado='concluido',motivo=null,
    concluido_em=v_agora,publicacao_fingerprint=f.selo_final_fingerprint,
    atualizado_em=v_agora where linha_id=l.id;
  insert into clube_novo.build_finalizacao_evento_v1(linha_id,evento,detalhe)
    values(l.id,'publicada',jsonb_build_object('origem',p_origem,
      'build_otimizador_id',o.id,'build_bonificador_id',b.id,
      'nota_final',v_nota_final,'selo',f.selo_final_fingerprint));
  return jsonb_build_object('ok',true,'linha_id',l.id,'card_id',l.card_id,
    'estado','publicada','nota_final',v_nota_final,'publicacao_fingerprint',f.selo_final_fingerprint,
    'build_otimizador_id',o.id,'build_bonificador_id',b.id,'idempotente',false);
end
$function$;

create function clube_novo.disparar_finalizacao_linha_v1()
returns trigger language plpgsql security definer set search_path=''
as $function$
begin
  if current_setting('clube_novo.finalizacao_linha_em_curso',true)=new.id::text
     or pg_trigger_depth()>1 then return new; end if;
  perform clube_novo.finalizar_publicar_linha_v1(new.id,'build_linha_card:'||tg_op);
  return new;
end
$function$;

create function clube_novo.disparar_finalizacao_correcao_v1()
returns trigger language plpgsql security definer set search_path=''
as $function$
begin
  if new.estado_item='preparado' and new.build_bonificador_id_novo is not null then
    if tg_op='INSERT' then
      perform clube_novo.finalizar_publicar_linha_v1(new.build_linha_card_id,'bonificador_correcao:INSERT');
    elsif old.estado_item is distinct from new.estado_item
       or old.build_bonificador_id_novo is distinct from new.build_bonificador_id_novo then
      perform clube_novo.finalizar_publicar_linha_v1(new.build_linha_card_id,'bonificador_correcao:UPDATE');
    end if;
  end if;
  return new;
end
$function$;

create function clube_novo.disparar_finalizacao_otimizador_vals_v1()
returns trigger language plpgsql security definer set search_path=''
as $function$
declare r record;
begin
  if new.atributos_finais is distinct from old.atributos_finais
     or new.atributos_internos is distinct from old.atributos_internos
     or new.arows_snapshot is distinct from old.arows_snapshot then
    for r in select id from clube_novo.build_linha_card where build_otimizador_id=new.id loop
      perform clube_novo.finalizar_publicar_linha_v1(r.id,'otimizador_vals');
    end loop;
  end if;
  return new;
end
$function$;

create trigger build_linha_finalizar_automatico_v1
after update of build_otimizador_id,build_bonificador_id on clube_novo.build_linha_card
for each row when (
  old.build_otimizador_id is distinct from new.build_otimizador_id
  or old.build_bonificador_id is distinct from new.build_bonificador_id
)
execute function clube_novo.disparar_finalizacao_linha_v1();

create trigger bonificador_correcao_inserir_finalizar_automatico_v1
after insert
on clube_novo.bonificador_correcao_item_v1
for each row execute function clube_novo.disparar_finalizacao_correcao_v1();

create trigger bonificador_correcao_atualizar_finalizar_automatico_v1
after update of estado_item,build_bonificador_id_novo
on clube_novo.bonificador_correcao_item_v1
for each row execute function clube_novo.disparar_finalizacao_correcao_v1();

create trigger otimizador_vals_finalizar_automatico_v1
after update of atributos_finais,atributos_internos,arows_snapshot
on clube_novo.build_otimizador
for each row execute function clube_novo.disparar_finalizacao_otimizador_vals_v1();

revoke all on function clube_novo.finalizar_publicar_linha_v1(bigint,text),
  clube_novo.disparar_finalizacao_linha_v1(),
  clube_novo.disparar_finalizacao_correcao_v1(),
  clube_novo.disparar_finalizacao_otimizador_vals_v1()
  from public, anon, authenticated;

create function public.finalizacao_publica_tick_v1(p_limite integer default 100)
returns jsonb
language plpgsql security definer set search_path=''
as $function$
declare r record; v jsonb; v_processadas integer:=0; v_publicadas integer:=0; v_erros integer:=0;
begin
  if coalesce(p_limite,0) not between 1 and 1000 then raise exception 'limite fora de 1..1000'; end if;

  insert into clube_novo.build_finalizacao_fila_v1(
    linha_id,estado,prioridade,overall_origem,origem_ultima,proxima_tentativa_em)
  select l.id,'aguardando',
    coalesce((select min(ip.prioridade_grupo)::integer
      from clube_novo.bonificador_correcao_item_v1 ip
      join clube_novo.bonificador_correcao_lote_v1 lp on lp.id=ip.lote_id
      where ip.build_linha_card_id=l.id and ip.estado_item='preparado'
        and lp.motor_versao='v10-0409-fisico-regra-aprovada-v1'),10),
    c.overall,'descoberta_tick',clock_timestamp()
  from clube_novo.build_linha_card l
  join clube_novo.carta_jogo c on c.card_id=l.card_id
  where l.execucao_tipo='producao' and l.lote_teste_id is null
    and l.estado_otimizador='concluido' and l.build_otimizador_id is not null
    and (
      exists(select 1 from clube_novo.build_bonificador bd
        where bd.id=l.build_bonificador_id
          and bd.motor_versao='v10-0409-fisico-regra-aprovada-v1'
          and bd.formula_fingerprint='756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
          and bd.contrato_versao='bonificador-regua-v3')
      or exists(select 1 from clube_novo.bonificador_correcao_item_v1 i
        join clube_novo.build_bonificador b on b.id=i.build_bonificador_id_novo
        where i.build_linha_card_id=l.id and i.estado_item='preparado'
          and b.motor_versao='v10-0409-fisico-regra-aprovada-v1'
          and b.formula_fingerprint='756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b')
    )
    and not exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 a
      where a.linha_id=l.id and a.build_otimizador_id=l.build_otimizador_id
        and (a.build_bonificador_id=l.build_bonificador_id
          or exists(select 1 from clube_novo.bonificador_correcao_item_v1 i
            where i.build_linha_card_id=l.id and i.estado_item='preparado'
              and i.build_bonificador_id_novo=a.build_bonificador_id)))
  order by 3,c.overall desc,l.id limit p_limite
  on conflict(linha_id) do update set
    estado=case when clube_novo.build_finalizacao_fila_v1.estado='concluido' then 'aguardando'
                else clube_novo.build_finalizacao_fila_v1.estado end,
    prioridade=least(clube_novo.build_finalizacao_fila_v1.prioridade,excluded.prioridade),
    overall_origem=excluded.overall_origem,
    proxima_tentativa_em=least(clube_novo.build_finalizacao_fila_v1.proxima_tentativa_em,clock_timestamp()),
    atualizado_em=clock_timestamp();

  for r in
    select linha_id from clube_novo.build_finalizacao_fila_v1
    where estado in ('aguardando','erro') and proxima_tentativa_em<=clock_timestamp()
    order by prioridade,overall_origem desc nulls last,
      case estado when 'aguardando' then 0 else 1 end,proxima_tentativa_em,linha_id
    limit p_limite
    for update skip locked
  loop
    v:=clube_novo.finalizar_publicar_linha_v1(r.linha_id,'retry_tick');
    v_processadas:=v_processadas+1;
    if v->>'estado' in ('publicada','ja_publicada') then v_publicadas:=v_publicadas+1;
    elsif v->>'estado'='erro' then v_erros:=v_erros+1; end if;
  end loop;
  return jsonb_build_object('ok',true,'processadas',v_processadas,'publicadas',v_publicadas,'erros',v_erros,
    'pendentes',(select count(*) from clube_novo.build_finalizacao_fila_v1 where estado in ('aguardando','erro')));
end
$function$;

revoke all on function public.finalizacao_publica_tick_v1(integer)
  from public, anon, authenticated;
grant execute on function public.finalizacao_publica_tick_v1(integer)
  to service_role, bonificador_runtime;

create or replace function public.frontend_build_estado_v2(p_card_id text)
returns table(build_publicada boolean,build_indisponivel_codigo text)
language sql stable security definer set search_path=''
as $function$
  select exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 a
                where a.card_id=p_card_id),
    case
      when exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 a
                  where a.card_id=p_card_id) then null::text
      when exists(select 1 from clube_novo.build_linha_card l
                  where l.card_id=p_card_id and l.estado_otimizador='concluido')
        then 'AGUARDANDO_BONIFICADOR_V10'
      when exists(select 1 from clube_novo.build_linha_card l where l.card_id=p_card_id)
        then 'AGUARDANDO_OTIMIZADOR'
      else 'SEM_BUILD_PUBLICADA'
    end
  where exists(select 1 from clube_novo.carta_jogo c where c.card_id=p_card_id)
$function$;
revoke all on function public.frontend_build_estado_v2(text) from public,anon,authenticated;
grant execute on function public.frontend_build_estado_v2(text)
  to anon,authenticated,service_role;

-- Descoberta inicial das linhas que ja possuem os dois resultados.
insert into clube_novo.build_finalizacao_fila_v1(
  linha_id,estado,prioridade,overall_origem,origem_ultima,proxima_tentativa_em)
select l.id,'aguardando',coalesce(i.prioridade_grupo,10)::integer,c.overall,
  'backfill_instalacao',clock_timestamp()
from clube_novo.build_linha_card l
join clube_novo.carta_jogo c on c.card_id=l.card_id
join lateral (
  select ix.*
  from clube_novo.bonificador_correcao_item_v1 ix
  join clube_novo.bonificador_correcao_lote_v1 lx on lx.id=ix.lote_id
  where ix.build_linha_card_id=l.id and ix.estado_item='preparado'
    and lx.motor_versao='v10-0409-fisico-regra-aprovada-v1'
  order by lx.criado_em desc,ix.preparado_em desc limit 1
) i on true
join clube_novo.build_bonificador b on b.id=i.build_bonificador_id_novo
join clube_novo.build_otimizador o on o.id=l.build_otimizador_id
where i.estado_item='preparado' and l.estado_otimizador='concluido'
  and b.motor_versao='v10-0409-fisico-regra-aprovada-v1'
  and b.formula_fingerprint='756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
  and jsonb_typeof(o.atributos_finais)='array' and jsonb_array_length(o.atributos_finais)=26
  and jsonb_typeof(coalesce(o.atributos_internos,o.atributos_finais))='array'
  and jsonb_array_length(coalesce(o.atributos_internos,o.atributos_finais))=26
  and o.arows_snapshot is not null
on conflict(linha_id) do update set estado='aguardando',origem_ultima='backfill_instalacao',
  prioridade=excluded.prioridade,overall_origem=excluded.overall_origem,
  proxima_tentativa_em=clock_timestamp(),atualizado_em=clock_timestamp();

-- Depois que todos os leitores e writers usam a rota por linha, apaga de vez
-- o corte manual, a reversao V9, o publicador global e seu refresh.
drop function public.bonificador_correcao_cortar_v1(uuid);
drop function public.bonificador_correcao_reverter_v1(uuid);
drop function clube_novo.publicar_e_normalizar_v2(integer,boolean);
drop function clube_novo.atualizar_lista_publicada_v1();
drop materialized view clube_novo.build_pontuacao_final_v2_mat;

do $do$
declare v_job bigint;
begin
  select jobid into v_job from cron.job where jobname='finalizacao_publica_por_linha_v1' limit 1;
  if v_job is not null then perform cron.unschedule(v_job); end if;
  perform cron.schedule('finalizacao_publica_por_linha_v1','* * * * *',
    $cron$select public.finalizacao_publica_tick_v1(100);$cron$);
end
$do$;

notify pgrst,'reload schema';
commit;
