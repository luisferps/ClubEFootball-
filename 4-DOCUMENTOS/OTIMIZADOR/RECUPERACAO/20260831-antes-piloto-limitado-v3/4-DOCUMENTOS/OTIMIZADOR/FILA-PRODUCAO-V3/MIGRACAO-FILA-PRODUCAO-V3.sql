-- FILA PRODUTIVA V3 DO OTIMIZADOR — ARTEFATO PREPARADO, NAO APLICADO
--
-- Escopo autorizado:
--   * somente clube_novo e portas public.otimizador_producao_*_v3;
--   * ordem deterministica: overall DESC, card_id, funcao_id, posicao_id;
--   * exclui cards incompletos e qualquer carta com Ímpeto condicional;
--   * reserva exclusiva por token; nao ha fallback para clube.*;
--   * resultado do Otimizador fica pronto para o Bonificador, sem publicar.
--
-- Esta migracao NAO deve ser aplicada automaticamente pelo executavel.
-- Aplicacao exige comando explicito do operador e readback posterior.

begin;

create table if not exists clube_novo.otimizador_lote_producao_v3 (
  id uuid primary key,
  contrato text not null default 'otimizador_fila_producao_v3'
    check (contrato='otimizador_fila_producao_v3'),
  estado text not null default 'parado'
    check (estado in ('parado','rodando','pausando','pausado','encerrando','encerrado','concluido','falhou')),
  formula_fingerprint text not null check (formula_fingerprint ~ '^[0-9a-f]{64}$'),
  contrato_fingerprint text not null check (contrato_fingerprint ~ '^[0-9a-f]{64}$'),
  motor_versao text not null check (btrim(motor_versao)<>''),
  regua_snapshot jsonb not null check (jsonb_typeof(regua_snapshot)='object'),
  fingerprint text not null unique check (fingerprint ~ '^[0-9a-f]{64}$'),
  cards integer not null default 0 check (cards>=0),
  linhas integer not null default 0 check (linhas>=0),
  excluidas_incompletas integer not null default 0 check (excluidas_incompletas>=0),
  excluidas_impeto_condicional integer not null default 0 check (excluidas_impeto_condicional>=0),
  excluidas_sem_linha integer not null default 0 check (excluidas_sem_linha>=0),
  pode_publicar boolean not null default false check (pode_publicar=false),
  falha text,
  criado_em timestamptz not null default clock_timestamp(),
  iniciado_em timestamptz,
  finalizado_em timestamptz,
  atualizado_em timestamptz not null default clock_timestamp()
);

create table if not exists clube_novo.otimizador_lote_producao_carta_v3 (
  lote_id uuid not null,
  card_id text not null,
  overall_snapshot integer not null,
  entrada_otimizador jsonb not null check (jsonb_typeof(entrada_otimizador)='object'),
  entrada_contrato text not null default 'otimizador_entradas_v3'
    check (entrada_contrato='otimizador_entradas_v3'),
  entrada_fingerprint text not null check (entrada_fingerprint ~ '^[0-9a-f]{64}$'),
  carta_versao_bonificador text not null check (btrim(carta_versao_bonificador)<>''),
  carta_fingerprint_bonificador text not null check (carta_fingerprint_bonificador ~ '^[0-9a-f]{64}$'),
  primary key (lote_id,card_id),
  constraint otimizador_lote_producao_carta_lote_fk
    foreign key (lote_id) references clube_novo.otimizador_lote_producao_v3(id)
    on update restrict on delete restrict,
  constraint otimizador_lote_producao_carta_card_fk
    foreign key (card_id) references clube_novo.carta_jogo(card_id)
    on update restrict on delete restrict
);

create table if not exists clube_novo.otimizador_lote_producao_linha_v3 (
  lote_id uuid not null,
  linha_id bigint not null,
  card_id text not null,
  ordem_fila bigint not null check (ordem_fila>0),
  overall_snapshot integer not null,
  entrada_fingerprint text not null check (entrada_fingerprint ~ '^[0-9a-f]{64}$'),
  reserva_token uuid,
  worker_id uuid,
  reservada_em timestamptz,
  finalizada_em timestamptz,
  tentativas integer not null default 0 check (tentativas>=0),
  resultado_fingerprint text,
  primary key (lote_id,linha_id),
  unique (linha_id),
  unique (lote_id,ordem_fila),
  constraint otimizador_lote_producao_linha_lote_fk
    foreign key (lote_id) references clube_novo.otimizador_lote_producao_v3(id)
    on update restrict on delete restrict,
  constraint otimizador_lote_producao_linha_card_fk
    foreign key (lote_id,card_id)
    references clube_novo.otimizador_lote_producao_carta_v3(lote_id,card_id)
    on update restrict on delete restrict,
  constraint otimizador_lote_producao_linha_build_fk
    foreign key (linha_id) references clube_novo.build_linha_card(id)
    on update restrict on delete restrict
);

create table if not exists clube_novo.otimizador_evento_producao_v3 (
  id bigint generated always as identity primary key,
  lote_id uuid not null,
  linha_id bigint,
  evento text not null check (evento in (
    'lote_criado','lote_iniciado','lote_retomado','pausa_solicitada','lote_pausado',
    'encerramento_solicitado','lote_encerrado','linha_reservada','linha_concluida',
    'linha_bloqueada','lote_concluido','lote_falhou'
  )),
  detalhe jsonb not null default '{}'::jsonb check (jsonb_typeof(detalhe)='object'),
  criado_em timestamptz not null default clock_timestamp(),
  constraint otimizador_evento_producao_lote_fk
    foreign key (lote_id) references clube_novo.otimizador_lote_producao_v3(id)
    on update restrict on delete restrict,
  constraint otimizador_evento_producao_linha_fk
    foreign key (linha_id) references clube_novo.build_linha_card(id)
    on update restrict on delete restrict
);

create index if not exists otimizador_lote_producao_linha_ordem_idx
  on clube_novo.otimizador_lote_producao_linha_v3(lote_id,ordem_fila);
create index if not exists otimizador_evento_producao_lote_idx
  on clube_novo.otimizador_evento_producao_v3(lote_id,id desc);

alter table clube_novo.otimizador_lote_producao_v3 enable row level security;
alter table clube_novo.otimizador_lote_producao_carta_v3 enable row level security;
alter table clube_novo.otimizador_lote_producao_linha_v3 enable row level security;
alter table clube_novo.otimizador_evento_producao_v3 enable row level security;
revoke all on table clube_novo.otimizador_lote_producao_v3 from public,anon,authenticated;
revoke all on table clube_novo.otimizador_lote_producao_carta_v3 from public,anon,authenticated;
revoke all on table clube_novo.otimizador_lote_producao_linha_v3 from public,anon,authenticated;
revoke all on table clube_novo.otimizador_evento_producao_v3 from public,anon,authenticated;

-- A assinatura inclui somente o pacote de cálculo, a versão da entrada e o
-- gate deliberado de Ímpetos condicionais. Rótulos de tela não participam.
create or replace function clube_novo.otimizador_producao_contrato_fingerprint_v3(
  p_regua jsonb
) returns text
language sql
immutable
set search_path=''
as $function$
  select encode(extensions.digest(convert_to(jsonb_build_object(
    'contrato','otimizador_fila_producao_v3',
    'regua',p_regua,
    'entrada','otimizador_entradas_v3',
    'impetos_condicionais','desligados'
  )::text,'UTF8'),'sha256'),'hex')
$function$;

create or replace function public.otimizador_producao_status_v3(p_lote_id uuid default null)
returns jsonb
language plpgsql
stable
security definer
set search_path=''
as $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_cards integer:=0; v_linhas integer:=0; v_pendentes integer:=0;
  v_processando integer:=0; v_concluidas integer:=0; v_bloqueadas integer:=0;
  v_interrompidas integer:=0; v_bonificador_pendentes integer:=0;
  v_corrente jsonb:='[]'::jsonb; v_motivos jsonb:='[]'::jsonb;
  v_existe_algum boolean:=false;
begin
  select exists(select 1 from clube_novo.otimizador_lote_producao_v3) into v_existe_algum;
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3 x
  where x.id=coalesce(p_lote_id,(
    select y.id from clube_novo.otimizador_lote_producao_v3 y
    order by (y.estado not in ('encerrado','concluido','falhou')) desc,y.criado_em desc
    limit 1
  ));
  if not found then
    return jsonb_build_object(
      'contrato','otimizador_fila_producao_v3','lote_id',null,
      'estado','sem_lote','estado_lote','sem_lote','cards',0,'linhas',0,
      'pendentes',0,'processando',0,'concluidas',0,'bloqueadas',0,'interrompidas',0,
      'bonificador_pendentes',0,'corrente','[]'::jsonb,'motivos','[]'::jsonb,
      'acoes',jsonb_build_object('criar',not v_existe_algum,'iniciar',false,'retomar',false,
        'pausar',false,'parar',false,'console',false),
      'confirmacao',jsonb_build_object('parar_exige_confirmacao',true),
      'pode_publicar',false,'modo','producao_v3_sem_publicacao',
      'mensagem','Nenhuma fila produtiva V3 foi criada.'
    );
  end if;

  select count(distinct q.card_id),count(*),
         count(*) filter(where l.estado_otimizador='pendente'),
         count(*) filter(where l.estado_otimizador='processando'),
         count(*) filter(where l.estado_otimizador='concluido'),
         count(*) filter(where l.estado_otimizador='bloqueado'),
         count(*) filter(where l.estado_otimizador='interrompido'),
         count(*) filter(where l.estado_otimizador='concluido' and l.build_bonificador_id is null)
  into v_cards,v_linhas,v_pendentes,v_processando,v_concluidas,v_bloqueadas,
       v_interrompidas,v_bonificador_pendentes
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id=q.linha_id
  where q.lote_id=v_lote.id;

  select coalesce(jsonb_agg(jsonb_build_object(
    'linha_id',l.id,'card_id',l.card_id,'funcao_id',l.funcao_id,'posicao_id',l.posicao_id,
    'estado',l.estado_otimizador,'motivo',l.erro_otimizador,
    'iniciada_em',l.otimizador_iniciado_em,'worker_id',q.worker_id
  ) order by q.ordem_fila),'[]'::jsonb)
  into v_corrente
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id=q.linha_id
  where q.lote_id=v_lote.id and l.estado_otimizador='processando';

  select coalesce(jsonb_agg(jsonb_build_object(
    'linha_id',l.id,'card_id',l.card_id,'funcao_id',l.funcao_id,'posicao_id',l.posicao_id,
    'estado',l.estado_otimizador,'motivo',l.erro_otimizador
  ) order by q.ordem_fila),'[]'::jsonb)
  into v_motivos
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id=q.linha_id
  where q.lote_id=v_lote.id and l.estado_otimizador in ('bloqueado','interrompido');

  return jsonb_build_object(
    'contrato','otimizador_fila_producao_v3','lote_id',v_lote.id,
    'fingerprint',v_lote.fingerprint,'formula_fingerprint',v_lote.formula_fingerprint,
    'contrato_fingerprint',v_lote.contrato_fingerprint,'motor_versao',v_lote.motor_versao,
    'estado',v_lote.estado,'estado_lote',v_lote.estado,'falha_lote',v_lote.falha,
    'cards',v_cards,'linhas',v_linhas,'pendentes',v_pendentes,'processando',v_processando,
    'concluidas',v_concluidas,'bloqueadas',v_bloqueadas,'interrompidas',v_interrompidas,
    'bonificador_pendentes',v_bonificador_pendentes,'corrente',v_corrente,'motivos',v_motivos,
    'exclusoes',jsonb_build_object('incompletas',v_lote.excluidas_incompletas,
      'impeto_condicional_desligado',v_lote.excluidas_impeto_condicional,
      'sem_linha_canonica',v_lote.excluidas_sem_linha),
    'acoes',jsonb_build_object(
      'criar',false,
      'iniciar',v_lote.estado='parado' and v_pendentes>0,
      'retomar',v_lote.estado='pausado' and v_pendentes>0,
      'pausar',v_lote.estado='rodando',
      'parar',v_lote.estado in ('parado','rodando','pausando','pausado') and v_pendentes>0,
      'console',false
    ),
    'confirmacao',jsonb_build_object('parar_exige_confirmacao',true),
    'pode_publicar',false,'modo','producao_v3_sem_publicacao',
    'mensagem',case v_lote.estado
      when 'parado' then 'Fila V3 pronta; clique em Iniciar para processar as cartas mais fortes primeiro.'
      when 'rodando' then 'Otimizador em execução; a reserva exclusiva protege cada linha.'
      when 'pausando' then 'Pausa solicitada; a linha atômica atual será finalizada ou bloqueada.'
      when 'pausado' then 'Fila pausada com pendências preservadas.'
      when 'encerrando' then 'Encerramento solicitado; nenhuma nova linha será reservada.'
      when 'encerrado' then 'Lote encerrado sem publicação; pendências foram marcadas interrompidas.'
      when 'concluido' then 'Otimizador concluiu este lote; linhas concluídas aguardam o Bonificador.'
      else coalesce(v_lote.falha,'Lote falhou fechado; não há retomada automática.') end
  );
end
$function$;

create or replace function public.otimizador_producao_contexto_lote_v3(p_lote_id uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path=''
as $function$
declare v clube_novo.otimizador_lote_producao_v3%rowtype;
begin
  select * into v from clube_novo.otimizador_lote_producao_v3 where id=p_lote_id;
  if not found then raise exception 'lote V3 inexistente'; end if;
  return jsonb_build_object(
    'contrato','otimizador_fila_producao_v3','lote_id',v.id,
    'formula_fingerprint',v.formula_fingerprint,'contrato_fingerprint',v.contrato_fingerprint,
    'motor_versao',v.motor_versao,'fingerprint',v.fingerprint,'regua',v.regua_snapshot,
    'impetos_condicionais','desligados','pode_publicar',false
  );
end
$function$;

create or replace function public.otimizador_producao_fila_v3(p_lote_id uuid)
returns jsonb
language sql
stable
security definer
set search_path=''
as $function$
  select jsonb_build_object(
    'contrato','otimizador_fila_producao_v3','lote_id',p_lote_id,
    'itens',coalesce(jsonb_agg(jsonb_build_object(
      'linha_id',l.id,'ordem_fila',q.ordem_fila,'card_id',l.card_id,
      'funcao_id',l.funcao_id,'posicao_id',l.posicao_id,
      'estado',l.estado_otimizador,'motivo',l.erro_otimizador,
      'iniciada_em',l.otimizador_iniciado_em,'finalizada_em',l.otimizador_finalizado_em,
      'overall_snapshot',q.overall_snapshot,'tecnico_id',o.tecnico_id,
      'pontuacao_final',o.pontuacao,'b1',o.pontuacao,'barras',o.barras,
      'impeto_adicional_codigo',o.impeto_adicional_codigo,
      'habilidades_adicionais',coalesce(to_jsonb(o.habilidades_adicionais),'[]'::jsonb),
      'builds_comparadas',o.builds_comparadas::text,
      'builds_possiveis',o.builds_possiveis::text,
      'duracao_segundos',case when l.otimizador_iniciado_em is not null
        and l.otimizador_finalizado_em is not null
        then extract(epoch from l.otimizador_finalizado_em-l.otimizador_iniciado_em) end,
      'bonificador',case when l.build_bonificador_id is not null then 'concluido'
        when l.estado_otimizador='concluido' then 'pendente' else 'aguardando_otimizador' end
    ) order by q.ordem_fila),'[]'::jsonb)
  )
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id=q.linha_id
  left join clube_novo.build_otimizador o on o.id=l.build_otimizador_id
  where q.lote_id=p_lote_id
$function$;

create or replace function public.otimizador_producao_eventos_v3(p_lote_id uuid)
returns jsonb
language sql
stable
security definer
set search_path=''
as $function$
  select jsonb_build_object(
    'contrato','otimizador_fila_producao_v3','lote_id',p_lote_id,
    'itens',coalesce(jsonb_agg(jsonb_build_object(
      'evento_id',e.id,'linha_id',e.linha_id,'evento',e.evento,
      'detalhe',e.detalhe,'instante',e.criado_em,
      'card_id',l.card_id,'estado',l.estado_otimizador
    ) order by e.id),'[]'::jsonb)
  )
  from clube_novo.otimizador_evento_producao_v3 e
  left join clube_novo.build_linha_card l on l.id=e.linha_id
  where e.lote_id=p_lote_id
$function$;

create or replace function public.otimizador_producao_criar_lote_v3(
  p_lote_id uuid,
  p_formula_fingerprint text,
  p_motor_versao text,
  p_limite_cards integer default 0
) returns jsonb
language plpgsql
security definer
set search_path=''
as $function$
declare
  v_formula constant text := '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad';
  v_regua jsonb; v_contrato_fp text; v_fingerprint text;
  v_cards integer; v_linhas integer; v_incompletas integer;
  v_condicionais integer; v_sem_linha integer;
begin
  if p_lote_id is null or p_formula_fingerprint<>v_formula
     or nullif(btrim(coalesce(p_motor_versao,'')),'') is null then
    raise exception 'criação recusada: selo de fórmula ou versão do worker inválidos';
  end if;
  if coalesce(p_limite_cards,0)<0 or coalesce(p_limite_cards,0)>50000 then
    raise exception 'criação recusada: limite de cartas fora da faixa 0..50000';
  end if;
  if exists(select 1 from clube_novo.otimizador_lote_producao_v3) then
    raise exception 'criação recusada: já existe lote V3; arquivamento explícito é obrigatório antes de outro';
  end if;

  select public.otimizador_regua_v2() into v_regua;
  if not coalesce((v_regua->'gate'->>'pode_rodar')::boolean,false) then
    raise exception 'criação recusada: gate da régua do Otimizador está fechado';
  end if;
  v_contrato_fp:=clube_novo.otimizador_producao_contrato_fingerprint_v3(v_regua);

  select count(*) into v_condicionais
  from clube_novo.carta_jogo c
  where coalesce(c.roda_motor,false) and coalesce(c.pode_rodar_vinculos,false)
    and exists(select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=c.card_id and coalesce(ci.condicional,false));

  create temporary table _otimizador_producao_candidatas_v3 on commit drop as
  select c.card_id,c.overall,c.extraido_em,
         public.otimizador_carta_v3(c.card_id) entrada_otimizador,
         public.bonificador_carta_v2(c.card_id) entrada_bonificador
  from clube_novo.carta_jogo c
  where coalesce(c.roda_motor,false) and coalesce(c.pode_rodar_vinculos,false)
    and c.overall is not null
    and not exists(select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=c.card_id and coalesce(ci.condicional,false));

  create temporary table _otimizador_producao_aptas_v3 on commit drop as
  select * from _otimizador_producao_candidatas_v3 x
  where coalesce((x.entrada_otimizador->'gate'->>'pode_rodar')::boolean,false)
    and coalesce((x.entrada_bonificador->>'pode_rodar')::boolean,false)
    and x.entrada_bonificador ? 'carta_versao'
    and x.entrada_bonificador ? 'carta_fingerprint';

  select (select count(*) from _otimizador_producao_candidatas_v3)-count(*)
  into v_incompletas from _otimizador_producao_aptas_v3;

  create temporary table _otimizador_producao_linhas_base_v3 on commit drop as
  select distinct a.card_id,a.overall,a.extraido_em,a.entrada_otimizador,a.entrada_bonificador,
    fp.funcao_id,fp.posicao_id
  from _otimizador_producao_aptas_v3 a
  join lateral (
    select cpp.posicao_id
    from clube_novo.carta_posicao_principal_jogo cpp where cpp.card_id=a.card_id
    union
    select cp.posicao_id
    from clube_novo.carta_posicao_jogo cp
    where cp.card_id=a.card_id and cp.nivel_aptidao>0
  ) px on true
  join clube_novo.otimizador_funcao_posicao fp on fp.posicao_id=px.posicao_id
  join clube_novo.funcao_sistema fs on fs.id=fp.funcao_id and fs.ativa and fs.pode_rodar
  join clube_novo.posicao_jogo p on p.id=fp.posicao_id and p.pode_rodar;

  select count(*) into v_sem_linha
  from _otimizador_producao_aptas_v3 a
  where not exists(select 1 from _otimizador_producao_linhas_base_v3 l where l.card_id=a.card_id);

  create temporary table _otimizador_producao_cards_v3 on commit drop as
  select distinct on (card_id) card_id,overall,extraido_em,entrada_otimizador,entrada_bonificador
  from _otimizador_producao_linhas_base_v3
  order by card_id,overall desc;

  create temporary table _otimizador_producao_selecionadas_v3 on commit drop as
  select * from _otimizador_producao_cards_v3
  order by overall desc,card_id
  limit case when coalesce(p_limite_cards,0)=0 then 50000 else p_limite_cards end;

  create temporary table _otimizador_producao_linhas_v3 on commit drop as
  select b.*,
    row_number() over(order by b.overall desc,b.card_id,b.funcao_id,b.posicao_id)::bigint ordem_fila
  from _otimizador_producao_linhas_base_v3 b
  join _otimizador_producao_selecionadas_v3 s using(card_id);

  select count(distinct card_id),count(*) into v_cards,v_linhas
  from _otimizador_producao_linhas_v3;
  if v_cards=0 or v_linhas=0 then
    raise exception 'criação recusada: não há carta apta com posição e função canônicas';
  end if;

  select encode(extensions.digest(convert_to(
    p_lote_id::text||':'||v_formula||':'||v_contrato_fp||':'||p_motor_versao||':'||
    string_agg(card_id||':'||funcao_id::text||':'||posicao_id::text||':'||ordem_fila::text,
               ',' order by ordem_fila),'UTF8'),'sha256'),'hex')
  into v_fingerprint
  from _otimizador_producao_linhas_v3;

  insert into clube_novo.otimizador_lote_producao_v3(
    id,formula_fingerprint,contrato_fingerprint,motor_versao,regua_snapshot,fingerprint,
    cards,linhas,excluidas_incompletas,excluidas_impeto_condicional,excluidas_sem_linha
  ) values (
    p_lote_id,v_formula,v_contrato_fp,p_motor_versao,v_regua,v_fingerprint,
    v_cards,v_linhas,v_incompletas,v_condicionais,v_sem_linha
  );

  insert into clube_novo.otimizador_lote_producao_carta_v3(
    lote_id,card_id,overall_snapshot,entrada_otimizador,entrada_fingerprint,
    carta_versao_bonificador,carta_fingerprint_bonificador
  )
  select s_card.lote_id,s_card.card_id,s_card.overall,s_card.entrada_otimizador,
    encode(extensions.digest(convert_to(s_card.entrada_otimizador::text,'UTF8'),'sha256'),'hex'),
    s_card.entrada_bonificador->>'carta_versao',s_card.entrada_bonificador->>'carta_fingerprint'
  from _otimizador_producao_selecionadas_v3 s_card;

  with inseridas as (
    insert into clube_novo.build_linha_card(
      card_id,funcao_id,posicao_id,carta_versao,carta_fingerprint,
      estado,pendencias,execucao_tipo,estado_otimizador,
      otimizador_formula_fingerprint_esperado,otimizador_contrato_fingerprint_esperado,
      otimizador_motor_versao_esperada,impeto_condicional_codigo,impeto_condicional_nivel
    )
    select l.card_id,l.funcao_id,l.posicao_id,
      l.entrada_bonificador->>'carta_versao',l.entrada_bonificador->>'carta_fingerprint',
      'pendente','{}'::text[],'producao','pendente',v_formula,v_contrato_fp,p_motor_versao,
      null::integer,null::smallint
    from _otimizador_producao_linhas_v3 l
    order by l.ordem_fila
    returning id,card_id,funcao_id,posicao_id
  )
  insert into clube_novo.otimizador_lote_producao_linha_v3(
    lote_id,linha_id,card_id,ordem_fila,overall_snapshot,entrada_fingerprint
  )
  select p_lote_id,i.id,l.card_id,l.ordem_fila,l.overall,
    encode(extensions.digest(convert_to(l.entrada_otimizador::text,'UTF8'),'sha256'),'hex')
  from inseridas i
  join _otimizador_producao_linhas_v3 l
    on l.card_id=i.card_id and l.funcao_id=i.funcao_id and l.posicao_id=i.posicao_id;

  if (select count(*) from clube_novo.otimizador_lote_producao_linha_v3 where lote_id=p_lote_id)<>v_linhas then
    raise exception 'criação recusada: a fila não preservou todas as linhas';
  end if;
  if exists(
    select 1
    from clube_novo.otimizador_lote_producao_linha_v3 q
    join clube_novo.build_linha_card l on l.id=q.linha_id
    where q.lote_id=p_lote_id
      and (l.impeto_condicional_codigo is not null or l.impeto_condicional_nivel is not null)
  ) then
    raise exception 'criação recusada: uma linha habilitou Ímpeto condicional';
  end if;

  insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
  values(p_lote_id,'lote_criado',jsonb_build_object(
    'cards',v_cards,'linhas',v_linhas,'ordem','overall_desc_card_id_funcao_id_posicao_id',
    'impetos_condicionais','desligados','pode_publicar',false
  ));
  return public.otimizador_producao_status_v3(p_lote_id);
end
$function$;

create or replace function public.otimizador_producao_controlar_lote_v3(
  p_lote_id uuid,
  p_acao text,
  p_confirmado boolean default false
) returns jsonb
language plpgsql
security definer
set search_path=''
as $function$
declare v clube_novo.otimizador_lote_producao_v3%rowtype; v_processando integer; v_pendentes integer;
begin
  select * into v from clube_novo.otimizador_lote_producao_v3 where id=p_lote_id for update;
  if not found then raise exception 'lote V3 inexistente'; end if;
  select count(*) filter(where l.estado_otimizador='processando'),
         count(*) filter(where l.estado_otimizador='pendente')
  into v_processando,v_pendentes
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id=q.linha_id where q.lote_id=p_lote_id;

  if p_acao='iniciar' then
    if v.estado<>'parado' or v_pendentes=0 then raise exception 'iniciar não autorizado pelo estado atual'; end if;
    update clube_novo.otimizador_lote_producao_v3 set estado='rodando',iniciado_em=coalesce(iniciado_em,clock_timestamp()),atualizado_em=clock_timestamp() where id=p_lote_id;
    insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento) values(p_lote_id,'lote_iniciado');
  elsif p_acao='retomar' then
    if v.estado<>'pausado' or v_pendentes=0 then raise exception 'retomar não autorizado pelo estado atual'; end if;
    update clube_novo.otimizador_lote_producao_v3 set estado='rodando',atualizado_em=clock_timestamp() where id=p_lote_id;
    insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento) values(p_lote_id,'lote_retomado');
  elsif p_acao='pausar' then
    if v.estado<>'rodando' then raise exception 'pausar não autorizado pelo estado atual'; end if;
    update clube_novo.otimizador_lote_producao_v3
    set estado=case when v_processando>0 then 'pausando' else 'pausado' end,atualizado_em=clock_timestamp()
    where id=p_lote_id;
    insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento) values(
      p_lote_id,case when v_processando>0 then 'pausa_solicitada' else 'lote_pausado' end);
  elsif p_acao='confirmar_pausa' then
    if v.estado='pausando' and v_processando=0 then
      update clube_novo.otimizador_lote_producao_v3 set estado='pausado',atualizado_em=clock_timestamp() where id=p_lote_id;
      insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento) values(p_lote_id,'lote_pausado');
    end if;
  elsif p_acao='parar' then
    if not p_confirmado then raise exception 'parar exige confirmação explícita'; end if;
    if v.estado not in ('parado','rodando','pausando','pausado') or v_pendentes=0 then raise exception 'parar não autorizado pelo estado atual'; end if;
    if v_processando>0 then
      update clube_novo.otimizador_lote_producao_v3 set estado='encerrando',atualizado_em=clock_timestamp() where id=p_lote_id;
      insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento) values(p_lote_id,'encerramento_solicitado');
    else
      update clube_novo.build_linha_card l set estado_otimizador='interrompido',erro_otimizador='encerrada pelo operador antes da execução',otimizador_finalizado_em=clock_timestamp(),atualizado_em=clock_timestamp()
      from clube_novo.otimizador_lote_producao_linha_v3 q
      where q.lote_id=p_lote_id and q.linha_id=l.id and l.estado_otimizador='pendente';
      update clube_novo.otimizador_lote_producao_v3 set estado='encerrado',finalizado_em=clock_timestamp(),atualizado_em=clock_timestamp() where id=p_lote_id;
      insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento) values(p_lote_id,'lote_encerrado');
    end if;
  elsif p_acao='confirmar_encerramento' then
    if not p_confirmado then raise exception 'confirmação de encerramento exige selo do worker'; end if;
    if v.estado='encerrando' and v_processando=0 then
      update clube_novo.build_linha_card l set estado_otimizador='interrompido',erro_otimizador='encerrada pelo operador antes da execução',otimizador_finalizado_em=clock_timestamp(),atualizado_em=clock_timestamp()
      from clube_novo.otimizador_lote_producao_linha_v3 q
      where q.lote_id=p_lote_id and q.linha_id=l.id and l.estado_otimizador='pendente';
      update clube_novo.otimizador_lote_producao_v3 set estado='encerrado',finalizado_em=clock_timestamp(),atualizado_em=clock_timestamp() where id=p_lote_id;
      insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento) values(p_lote_id,'lote_encerrado');
    end if;
  else
    raise exception 'ação de controle inválida';
  end if;
  return public.otimizador_producao_status_v3(p_lote_id);
end
$function$;

create or replace function public.otimizador_producao_reservar_linha_v3(
  p_lote_id uuid,
  p_worker_id uuid
) returns jsonb
language plpgsql
security definer
set search_path=''
as $function$
declare v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_q clube_novo.otimizador_lote_producao_linha_v3%rowtype;
  v_l clube_novo.build_linha_card%rowtype;
  v_c clube_novo.otimizador_lote_producao_carta_v3%rowtype;
  v_token uuid;
begin
  if p_worker_id is null then raise exception 'worker_id obrigatório'; end if;
  select * into v_lote from clube_novo.otimizador_lote_producao_v3 where id=p_lote_id for update;
  if not found then raise exception 'lote V3 inexistente'; end if;
  if v_lote.estado<>'rodando' then
    return jsonb_build_object('contrato','otimizador_fila_producao_v3','reservada',false,'estado_lote',v_lote.estado);
  end if;
  select q.* into v_q
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id=q.linha_id
  where q.lote_id=p_lote_id and l.estado_otimizador='pendente'
  order by q.ordem_fila
  for update of q,l skip locked
  limit 1;
  if not found then
    if not exists(select 1 from clube_novo.otimizador_lote_producao_linha_v3 q join clube_novo.build_linha_card l on l.id=q.linha_id where q.lote_id=p_lote_id and l.estado_otimizador in ('pendente','processando')) then
      update clube_novo.otimizador_lote_producao_v3 set estado='concluido',finalizado_em=clock_timestamp(),atualizado_em=clock_timestamp() where id=p_lote_id;
      insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento) values(p_lote_id,'lote_concluido');
      return jsonb_build_object('contrato','otimizador_fila_producao_v3','reservada',false,'estado_lote','concluido');
    end if;
    return jsonb_build_object('contrato','otimizador_fila_producao_v3','reservada',false,'estado_lote','rodando');
  end if;
  select * into v_l from clube_novo.build_linha_card where id=v_q.linha_id;
  select * into v_c from clube_novo.otimizador_lote_producao_carta_v3 where lote_id=p_lote_id and card_id=v_q.card_id;
  if not found or v_c.entrada_fingerprint<>v_q.entrada_fingerprint then
    raise exception 'reserva recusada: snapshot de entrada inconsistente';
  end if;
  v_token:=extensions.gen_random_uuid();
  update clube_novo.otimizador_lote_producao_linha_v3 set reserva_token=v_token,worker_id=p_worker_id,reservada_em=clock_timestamp(),tentativas=tentativas+1 where lote_id=p_lote_id and linha_id=v_q.linha_id;
  update clube_novo.build_linha_card set estado_otimizador='processando',erro_otimizador=null,otimizador_iniciado_em=clock_timestamp(),atualizado_em=clock_timestamp() where id=v_q.linha_id and estado_otimizador='pendente';
  insert into clube_novo.otimizador_evento_producao_v3(lote_id,linha_id,evento,detalhe) values(p_lote_id,v_q.linha_id,'linha_reservada',jsonb_build_object('worker_id',p_worker_id,'ordem_fila',v_q.ordem_fila));
  return jsonb_build_object(
    'contrato','otimizador_fila_producao_v3','reservada',true,'lote_id',p_lote_id,
    'linha_id',v_q.linha_id,'reserva_token',v_token,'ordem_fila',v_q.ordem_fila,
    'card_id',v_l.card_id,'funcao_id',v_l.funcao_id,'posicao_id',v_l.posicao_id,
    'impeto_condicional_codigo',null,'impeto_condicional_nivel',null,
    'carta',v_c.entrada_otimizador,'carta_entrada_fingerprint',v_c.entrada_fingerprint,
    'formula_fingerprint',v_lote.formula_fingerprint,'contrato_fingerprint',v_lote.contrato_fingerprint,
    'motor_versao',v_lote.motor_versao,'lote_fingerprint',v_lote.fingerprint,
    'carta_versao',v_l.carta_versao,'carta_fingerprint',v_l.carta_fingerprint,
    'impetos_condicionais','desligados'
  );
end
$function$;

create or replace function public.otimizador_producao_concluir_linha_v3(
  p_lote_id uuid,
  p_linha_id bigint,
  p_reserva_token uuid,
  p_resultado jsonb
) returns jsonb
language plpgsql
security definer
set search_path=''
as $function$
declare v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_q clube_novo.otimizador_lote_producao_linha_v3%rowtype;
  v_l clube_novo.build_linha_card%rowtype; v_habilidades integer[];
  v_resultado_fp text; v_build_id bigint;
begin
  if jsonb_typeof(p_resultado)<>'object' then raise exception 'resultado do Otimizador deve ser objeto'; end if;
  select * into v_lote from clube_novo.otimizador_lote_producao_v3 where id=p_lote_id for update;
  select * into v_q from clube_novo.otimizador_lote_producao_linha_v3 where lote_id=p_lote_id and linha_id=p_linha_id for update;
  select * into v_l from clube_novo.build_linha_card where id=p_linha_id for update;
  if v_lote.id is null or v_q.linha_id is null or v_l.id is null then raise exception 'conclusão recusada: lote ou linha inexistente'; end if;
  if v_l.estado_otimizador<>'processando' or v_q.reserva_token is distinct from p_reserva_token then raise exception 'conclusão recusada: reserva não pertence ao worker'; end if;
  if p_resultado->>'card_id'<>v_l.card_id or (p_resultado->>'funcao_id')::bigint<>v_l.funcao_id or (p_resultado->>'posicao_id')::integer<>v_l.posicao_id then raise exception 'conclusão recusada: identidade da linha diverge'; end if;
  if p_resultado->>'formula_fingerprint'<>v_lote.formula_fingerprint or p_resultado->>'contrato_fingerprint'<>v_lote.contrato_fingerprint or p_resultado->>'motor_versao'<>v_lote.motor_versao or p_resultado->>'lote_fingerprint'<>v_lote.fingerprint or p_resultado->>'carta_entrada_fingerprint'<>v_q.entrada_fingerprint then raise exception 'conclusão recusada: selo divergente'; end if;
  if coalesce(p_resultado->>'impeto_condicional_codigo','')<>'' or coalesce(p_resultado->>'impeto_condicional_nivel','')<>'' then raise exception 'conclusão recusada: Ímpeto condicional continua desligado'; end if;
  if not (p_resultado ?& array['b1','barras','tecnico_id','habilidades','builds_comparadas','builds_possiveis']) then raise exception 'conclusão recusada: resultado incompleto'; end if;
  if jsonb_typeof(p_resultado->'barras')<>'object' or jsonb_typeof(p_resultado->'habilidades')<>'array' then raise exception 'conclusão recusada: build inválida'; end if;
  select coalesce(array_agg(x.valor::integer order by x.ordem),'{}'::integer[]) into v_habilidades from jsonb_array_elements_text(p_resultado->'habilidades') with ordinality x(valor,ordem);
  v_resultado_fp:=encode(extensions.digest(convert_to(p_resultado::text,'UTF8'),'sha256'),'hex');
  insert into clube_novo.build_otimizador(
    id,tecnico_id,barras,impeto_adicional_codigo,habilidades_adicionais,pontuacao,
    contrato_versao,contrato_fingerprint,carta_versao,carta_fingerprint,
    formula_fingerprint,resultado_fingerprint,motor_versao,builds_comparadas,builds_possiveis
  ) values (
    nextval('clube_novo.build_otimizador_id_seq'::regclass),
    (p_resultado->>'tecnico_id')::bigint,p_resultado->'barras',
    nullif(p_resultado->>'impeto_adicional_codigo','')::integer,v_habilidades,(p_resultado->>'b1')::numeric,
    'otimizador_regua_v2',v_lote.contrato_fingerprint,v_l.carta_versao,v_l.carta_fingerprint,
    v_lote.formula_fingerprint,v_resultado_fp,v_lote.motor_versao,
    (p_resultado->>'builds_comparadas')::integer,(p_resultado->>'builds_possiveis')::numeric
  ) returning id into v_build_id;
  update clube_novo.build_linha_card set build_otimizador_id=v_build_id,estado_otimizador='concluido',erro_otimizador=null,otimizador_finalizado_em=clock_timestamp(),pendencias='{}'::text[],atualizado_em=clock_timestamp() where id=p_linha_id;
  update clube_novo.otimizador_lote_producao_linha_v3 set reserva_token=null,worker_id=null,finalizada_em=clock_timestamp(),resultado_fingerprint=v_resultado_fp where lote_id=p_lote_id and linha_id=p_linha_id;
  insert into clube_novo.otimizador_evento_producao_v3(lote_id,linha_id,evento,detalhe) values(p_lote_id,p_linha_id,'linha_concluida',jsonb_build_object('build_otimizador_id',v_build_id,'resultado_fingerprint',v_resultado_fp,'bonificador','pendente'));
  if v_lote.estado='rodando' and not exists(select 1 from clube_novo.otimizador_lote_producao_linha_v3 q join clube_novo.build_linha_card l on l.id=q.linha_id where q.lote_id=p_lote_id and l.estado_otimizador in ('pendente','processando')) then
    update clube_novo.otimizador_lote_producao_v3 set estado='concluido',finalizado_em=clock_timestamp(),atualizado_em=clock_timestamp() where id=p_lote_id;
    insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento) values(p_lote_id,'lote_concluido');
  end if;
  return jsonb_build_object('contrato','otimizador_fila_producao_v3','linha_id',p_linha_id,'build_otimizador_id',v_build_id,'bonificador','pendente','pode_publicar',false);
end
$function$;

create or replace function public.otimizador_producao_bloquear_linha_v3(
  p_lote_id uuid,
  p_linha_id bigint,
  p_reserva_token uuid,
  p_motivo text
) returns jsonb
language plpgsql
security definer
set search_path=''
as $function$
declare v_q clube_novo.otimizador_lote_producao_linha_v3%rowtype; v_l clube_novo.build_linha_card%rowtype;
begin
  if nullif(btrim(coalesce(p_motivo,'')),'') is null then raise exception 'motivo do bloqueio é obrigatório'; end if;
  select * into v_q from clube_novo.otimizador_lote_producao_linha_v3 where lote_id=p_lote_id and linha_id=p_linha_id for update;
  select * into v_l from clube_novo.build_linha_card where id=p_linha_id for update;
  if v_q.linha_id is null or v_l.id is null or v_l.estado_otimizador<>'processando' or v_q.reserva_token is distinct from p_reserva_token then raise exception 'bloqueio recusado: reserva não pertence ao worker'; end if;
  update clube_novo.build_linha_card set estado_otimizador='bloqueado',erro_otimizador=left(p_motivo,1000),otimizador_finalizado_em=clock_timestamp(),atualizado_em=clock_timestamp() where id=p_linha_id;
  update clube_novo.otimizador_lote_producao_linha_v3 set reserva_token=null,worker_id=null,finalizada_em=clock_timestamp() where lote_id=p_lote_id and linha_id=p_linha_id;
  insert into clube_novo.otimizador_evento_producao_v3(lote_id,linha_id,evento,detalhe) values(p_lote_id,p_linha_id,'linha_bloqueada',jsonb_build_object('motivo',left(p_motivo,1000)));
  return jsonb_build_object('contrato','otimizador_fila_producao_v3','linha_id',p_linha_id,'estado','bloqueado');
end
$function$;

create or replace function public.otimizador_producao_falhar_lote_v3(
  p_lote_id uuid,
  p_motivo text
) returns jsonb
language plpgsql
security definer
set search_path=''
as $function$
begin
  if nullif(btrim(coalesce(p_motivo,'')),'') is null then raise exception 'motivo da falha é obrigatório'; end if;
  update clube_novo.otimizador_lote_producao_v3
  set estado='falhou',falha=left(p_motivo,1000),atualizado_em=clock_timestamp()
  where id=p_lote_id and estado in ('parado','rodando','pausando','pausado');
  if not found then raise exception 'falha do lote recusada pelo estado atual'; end if;
  insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe) values(p_lote_id,'lote_falhou',jsonb_build_object('motivo',left(p_motivo,1000)));
  return public.otimizador_producao_status_v3(p_lote_id);
end
$function$;

-- Nenhuma dessas portas é navegável pelo browser. Somente o servidor loopback,
-- usando service_role local, pode chamá-las.
revoke all on function public.otimizador_producao_status_v3(uuid) from public,anon,authenticated;
revoke all on function public.otimizador_producao_contexto_lote_v3(uuid) from public,anon,authenticated;
revoke all on function public.otimizador_producao_fila_v3(uuid) from public,anon,authenticated;
revoke all on function public.otimizador_producao_eventos_v3(uuid) from public,anon,authenticated;
revoke all on function public.otimizador_producao_criar_lote_v3(uuid,text,text,integer) from public,anon,authenticated;
revoke all on function public.otimizador_producao_controlar_lote_v3(uuid,text,boolean) from public,anon,authenticated;
revoke all on function public.otimizador_producao_reservar_linha_v3(uuid,uuid) from public,anon,authenticated;
revoke all on function public.otimizador_producao_concluir_linha_v3(uuid,bigint,uuid,jsonb) from public,anon,authenticated;
revoke all on function public.otimizador_producao_bloquear_linha_v3(uuid,bigint,uuid,text) from public,anon,authenticated;
revoke all on function public.otimizador_producao_falhar_lote_v3(uuid,text) from public,anon,authenticated;
grant execute on function public.otimizador_producao_status_v3(uuid) to service_role;
grant execute on function public.otimizador_producao_contexto_lote_v3(uuid) to service_role;
grant execute on function public.otimizador_producao_fila_v3(uuid) to service_role;
grant execute on function public.otimizador_producao_eventos_v3(uuid) to service_role;
grant execute on function public.otimizador_producao_criar_lote_v3(uuid,text,text,integer) to service_role;
grant execute on function public.otimizador_producao_controlar_lote_v3(uuid,text,boolean) to service_role;
grant execute on function public.otimizador_producao_reservar_linha_v3(uuid,uuid) to service_role;
grant execute on function public.otimizador_producao_concluir_linha_v3(uuid,bigint,uuid,jsonb) to service_role;
grant execute on function public.otimizador_producao_bloquear_linha_v3(uuid,bigint,uuid,text) to service_role;
grant execute on function public.otimizador_producao_falhar_lote_v3(uuid,text) to service_role;

commit;
