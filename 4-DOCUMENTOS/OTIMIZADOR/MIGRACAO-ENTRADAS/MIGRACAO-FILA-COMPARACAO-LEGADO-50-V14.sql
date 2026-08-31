-- Fila isolada de comparação: 50 cards do arquivo anterior e todas as linhas atuais.
-- clube.build_arquivo_2608 é somente referência de seleção/comparação.
-- Toda fila e todo resultado permanecem em clube_novo.

create or replace function public.otimizador_status_teste_v2(p_lote_id uuid)
returns jsonb language sql stable security definer set search_path='' as $$
with s as (
  select max(lote_teste_fingerprint) fingerprint,min(sorteada_em) sorteada_em,
    min(lote_estado) estado_lote,max(lote_estado_atualizado_em) estado_atualizado_em,
    max(lote_falha) falha_lote,count(distinct card_id) cards,count(*) linhas,
    count(*) filter(where estado_otimizador='pendente') pendentes,
    count(*) filter(where estado_otimizador='processando') processando,
    count(*) filter(where estado_otimizador='concluido') concluidas,
    count(*) filter(where estado_otimizador='bloqueado') bloqueadas,
    count(*) filter(where estado_otimizador='interrompido') interrompidas,
    coalesce(jsonb_agg(jsonb_build_object(
      'linha_id',id,'card_id',card_id,'funcao_id',funcao_id,'posicao_id',posicao_id,
      'impeto_condicional_codigo',impeto_condicional_codigo,
      'impeto_condicional_nivel',impeto_condicional_nivel,
      'estado',estado_otimizador,'motivo',erro_otimizador,
      'iniciada_em',otimizador_iniciado_em) order by otimizador_iniciado_em)
      filter(where estado_otimizador='processando'),'[]'::jsonb) corrente,
    coalesce(jsonb_agg(jsonb_build_object(
      'linha_id',id,'card_id',card_id,'funcao_id',funcao_id,'posicao_id',posicao_id,
      'impeto_condicional_codigo',impeto_condicional_codigo,
      'impeto_condicional_nivel',impeto_condicional_nivel,
      'estado',estado_otimizador,'motivo',erro_otimizador) order by id)
      filter(where estado_otimizador in ('bloqueado','interrompido')),'[]'::jsonb) motivos
  from clube_novo.build_linha_card where lote_teste_id=p_lote_id
)
select jsonb_build_object(
  'contrato','otimizador_teste_lote_v14','lote_id',p_lote_id,'fingerprint',fingerprint,
  'sorteada_em',sorteada_em,'estado',estado_lote,'estado_lote',estado_lote,
  'estado_atualizado_em',estado_atualizado_em,'falha_lote',falha_lote,
  'cards',cards,'linhas',linhas,'pendentes',pendentes,'processando',processando,
  'concluidas',concluidas,'bloqueadas',bloqueadas,'interrompidas',interrompidas,
  'corrente',corrente,'motivos',motivos,
  'acoes',jsonb_build_object(
    'criar',false,
    'iniciar',estado_lote in ('parado','pausado') and pendentes>0,
    'pausar',estado_lote='rodando',
    'parar',estado_lote in ('parado','rodando','pausando','pausado','falhou') and pendentes>0,
    'retomar',estado_lote in ('pausado','falhou') and pendentes>0,
    'console',estado_lote is not null),
  'confirmacao',jsonb_build_object('parar_exige_confirmacao',true),
  'pode_publicar',false,'modo','teste_nao_publicado')
from s
$$;

revoke all on function public.otimizador_status_teste_v2(uuid)
  from public,anon,authenticated;
grant execute on function public.otimizador_status_teste_v2(uuid) to service_role;

create or replace function public.otimizador_criar_fila_comparacao_legado_50_v1(
  p_lote_id uuid,p_semente text,p_formula_fingerprint text,
  p_contrato_fingerprint text,p_motor_versao text
) returns jsonb language plpgsql security definer set search_path='' as $$
declare
  v_cards integer;
  v_linhas integer;
  v_condicionais integer;
  v_fp text;
  v_quando timestamptz:=clock_timestamp();
begin
  if p_lote_id is null or nullif(btrim(p_semente),'') is null
     or nullif(btrim(p_formula_fingerprint),'') is null
     or nullif(btrim(p_contrato_fingerprint),'') is null
     or nullif(btrim(p_motor_versao),'') is null then
    raise exception 'lote, semente e selos sao obrigatorios';
  end if;

  if exists(select 1 from clube_novo.build_linha_card where lote_teste_id=p_lote_id) then
    return public.otimizador_status_teste_v2(p_lote_id);
  end if;

  if exists(select 1 from clube_novo.build_linha_card)
     or exists(select 1 from clube_novo.build_otimizador)
     or exists(select 1 from clube_novo.build_bonificador) then
    raise exception 'fila de comparacao exige tabelas de motor zeradas';
  end if;

  create temporary table _candidatos_legado_50_v14 on commit drop as
  with base as materialized (
    select c.card_id,c.extraido_em,c.extracao_id
    from clube_novo.carta_jogo c
    where c.roda_motor and c.pode_rodar_vinculos
      and exists (
        select 1 from clube.build_arquivo_2608 ar where ar.card_id=c.card_id
      )
    order by encode(extensions.digest(p_semente||':'||c.card_id,'sha256'),'hex')
    limit 400
  ), pacotes as materialized (
    select b.*,public.otimizador_carta_v2(b.card_id) pacote from base b
  )
  select * from pacotes p
  where coalesce((p.pacote->'gate'->>'pode_rodar')::boolean,false)
    and (
      select count(*) from clube_novo.carta_impeto_jogo ci
      where ci.card_id=p.card_id and ci.codigo_impeto is not null and ci.condicional
    ) <= 1;

  create temporary table _linhas_legado_50_v14 on commit drop as
  select distinct a.card_id,fs.id funcao_id,fs.codigo_legado,px.posicao_id
  from _candidatos_legado_50_v14 a
  join lateral (
    select cpp.posicao_id
    from clube_novo.carta_posicao_principal_jogo cpp where cpp.card_id=a.card_id
    union
    select cp.posicao_id
    from clube_novo.carta_posicao_jogo cp
    where cp.card_id=a.card_id and cp.nivel_aptidao>0
  ) px on true
  join clube_novo.posicao_jogo p on p.id=px.posicao_id and p.pode_rodar
  join clube_novo.funcao_sistema fs
    on fs.ativa and fs.pode_rodar and p.codigo_pt=any(fs.posicoes);

  create temporary table _amostra_legado_50_v14 on commit drop as
  select x.* from (
    select c.*,(row_number() over(
      order by encode(extensions.digest(p_semente||':'||c.card_id,'sha256'),'hex')
    ))::smallint ordem
    from _candidatos_legado_50_v14 c
    where exists(
      select 1 from _linhas_legado_50_v14 l where l.card_id=c.card_id
    )
      and not exists(
        select 1 from _linhas_legado_50_v14 l
        where l.card_id=c.card_id
          and not exists(
            select 1 from clube.build_arquivo_2608 ar
            where ar.card_id=l.card_id and ar.funcao_codigo=l.codigo_legado
          )
      )
  ) x where x.ordem<=50;

  select count(*) into v_cards from _amostra_legado_50_v14;
  if v_cards<>50 then
    raise exception 'pre-voo recusado: somente % cards integralmente comparaveis',v_cards;
  end if;

  create temporary table _variantes_legado_50_v14 on commit drop as
  select a.card_id,a.extraido_em,a.extracao_id,a.pacote,a.ordem,
    l.funcao_id,l.codigo_legado,l.posicao_id,
    v.impeto_condicional_codigo,v.impeto_condicional_nivel
  from _amostra_legado_50_v14 a
  join _linhas_legado_50_v14 l on l.card_id=a.card_id
  cross join lateral (
    select null::integer impeto_condicional_codigo,null::smallint impeto_condicional_nivel
    where not exists(
      select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=a.card_id and ci.codigo_impeto is not null and ci.condicional)
    union all
    select ci.codigo_impeto,g.nivel::smallint
    from clube_novo.carta_impeto_jogo ci
    cross join lateral generate_series(
      1,clube_novo.impeto_nivel_maximo_v1(ci.codigo_impeto)::integer
    ) g(nivel)
    where ci.card_id=a.card_id and ci.codigo_impeto is not null and ci.condicional
  ) v;

  select count(*),count(distinct card_id) filter(
    where impeto_condicional_codigo is not null
  ) into v_linhas,v_condicionais
  from _variantes_legado_50_v14;
  if v_linhas<50 then raise exception 'fila recusada: nenhuma linha util'; end if;
  if v_condicionais=0 then
    raise exception 'amostra recusada: nao exercita impeto condicional';
  end if;

  select encode(extensions.digest(p_semente||':'||string_agg(
    card_id||':'||funcao_id::text||':'||posicao_id::text||':'||
    coalesce(impeto_condicional_codigo::text,'-')||':'||
    coalesce(impeto_condicional_nivel::text,'-'),','
    order by ordem,funcao_id,posicao_id,
             impeto_condicional_codigo,impeto_condicional_nivel),'sha256'),'hex')
  into v_fp from _variantes_legado_50_v14;

  insert into clube_novo.build_linha_card(
    card_id,funcao_id,posicao_id,impeto_condicional_codigo,impeto_condicional_nivel,
    carta_versao,carta_fingerprint,estado,pendencias,execucao_tipo,
    lote_teste_id,lote_teste_semente,lote_teste_fingerprint,amostra_ordem,sorteada_em,
    estado_otimizador,lote_estado,lote_estado_atualizado_em,
    otimizador_formula_fingerprint_esperado,otimizador_contrato_fingerprint_esperado,
    otimizador_motor_versao_esperada
  )
  select v.card_id,v.funcao_id,v.posicao_id,
    v.impeto_condicional_codigo,v.impeto_condicional_nivel,
    coalesce(v.extracao_id::text,v.extraido_em::text,'sem_versao'),
    encode(extensions.digest(v.pacote::text,'sha256'),'hex'),
    'pendente',array['teste_nao_publicado','bonificador_nao_executado']::text[],
    'teste_isolado',p_lote_id,p_semente,v_fp,v.ordem,v_quando,
    'pendente','parado',v_quando,p_formula_fingerprint,p_contrato_fingerprint,p_motor_versao
  from _variantes_legado_50_v14 v
  order by v.ordem,v.funcao_id,v.posicao_id,
           v.impeto_condicional_codigo,v.impeto_condicional_nivel;

  if (select count(distinct card_id) from clube_novo.build_linha_card
      where lote_teste_id=p_lote_id)<>50 then
    raise exception 'fila recusada: nao preservou 50 cards distintos';
  end if;
  if (select count(*) from clube_novo.build_linha_card
      where lote_teste_id=p_lote_id)<>v_linhas then
    raise exception 'fila recusada: perdeu linhas durante a gravacao';
  end if;
  if exists(
    select 1
    from clube_novo.build_linha_card l
    join clube_novo.funcao_sistema fs on fs.id=l.funcao_id
    where l.lote_teste_id=p_lote_id
      and not exists(
        select 1 from clube.build_arquivo_2608 ar
        where ar.card_id=l.card_id and ar.funcao_codigo=fs.codigo_legado
      )
  ) then
    raise exception 'fila recusada: existe linha sem par no arquivo anterior';
  end if;

  return public.otimizador_status_teste_v2(p_lote_id);
end $$;

revoke all on function public.otimizador_criar_fila_comparacao_legado_50_v1(
  uuid,text,text,text,text
) from public,anon,authenticated;
grant execute on function public.otimizador_criar_fila_comparacao_legado_50_v1(
  uuid,text,text,text,text
) to service_role;
