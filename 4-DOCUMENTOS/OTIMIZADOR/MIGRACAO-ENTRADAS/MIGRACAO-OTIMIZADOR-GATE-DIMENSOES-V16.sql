-- V16 — Gate de dimensões físicas do Otimizador.
--
-- Escopo: somente o endereço/critério do contrato de leitura de carta.
-- Fórmula, pesos, moldes, fila, resultados e tabelas de jogo não mudam.
--
-- Problema corrigido: V1 exigia clube e liga mesmo quando Player.bin não trazia
-- essas dimensões. V3 preserva os bloqueios do V2, mas só bloqueia uma dimensão
-- quando a chave física existe e não resolve para um catálogo apto.

begin;

create or replace function public.otimizador_carta_v3(p_card_id text)
returns jsonb
language sql
stable
security definer
set search_path=''
as $function$
with base as (
  select public.otimizador_carta_v2(p_card_id) as j
),
motivos_v2 as (
  select coalesce(
    array_agg(x.motivo order by x.ordem)
      filter (where x.motivo not in ('clube_bloqueado','liga_bloqueada')),
    '{}'::text[]
  ) as motivos
  from base
  cross join lateral jsonb_array_elements_text(
    coalesce(base.j#>'{gate,motivos}','[]'::jsonb)
  ) with ordinality as x(motivo,ordem)
),
motivos_dimensao as (
  select array_remove(array[
    case when c.codigo_clube is not null
              and (cl.codigo_jogo is null or not coalesce(cl.pode_rodar,false))
         then 'clube_bloqueado' end,
    case when c.codigo_liga is not null
              and (lg.codigo_jogo is null or not coalesce(lg.pode_rodar,false))
         then 'liga_bloqueada' end
  ],null)::text[] as motivos
  from clube_novo.carta_jogo c
  left join clube_novo.clube_jogo cl on cl.codigo_jogo=c.codigo_clube
  left join clube_novo.liga_jogo lg on lg.codigo_jogo=c.codigo_liga
  where c.card_id=p_card_id
),
gate as (
  select v.motivos || coalesce(d.motivos,'{}'::text[]) as motivos
  from motivos_v2 v
  left join motivos_dimensao d on true
)
select
  (base.j - 'contrato' - 'gate') ||
  jsonb_build_object(
    'contrato','otimizador_entradas_v3',
    'gate',jsonb_build_object(
      'pode_rodar',cardinality(gate.motivos)=0,
      'motivos',to_jsonb(gate.motivos)
    )
  )
from base
cross join gate
where base.j is not null
$function$;

create or replace function public.otimizador_cartas_v3(p_ids jsonb)
returns jsonb
language sql
stable
security definer
set search_path=''
as $function$
  select coalesce(jsonb_agg(q.carta order by q.ord) filter(where q.carta is not null),'[]'::jsonb)
  from (
    select x.ord,public.otimizador_carta_v3(x.id) carta
    from jsonb_array_elements_text(p_ids) with ordinality x(id,ord)
  ) q
$function$;

create or replace function public.otimizador_pool_habilidades_v3(
  p_card_id text,
  p_funcao_id bigint
)
returns jsonb
language sql
stable
security definer
set search_path=''
as $function$
with carta as (select public.otimizador_carta_v3(p_card_id) j),
f as (
  select id
  from clube_novo.funcao_sistema
  where id=p_funcao_id and ativa and pode_rodar
),
g as (
  select coalesce((carta.j->'gate'->>'pode_rodar')::boolean,false) carta_apta,
         exists(select 1 from f) funcao_apta
  from carta
)
select jsonb_build_object(
  'card_id',p_card_id,
  'funcao_id',p_funcao_id,
  'gate',jsonb_build_object(
    'pode_rodar',g.carta_apta and g.funcao_apta,
    'motivos',to_jsonb(array_remove(array[
      case when not g.carta_apta then 'carta_bloqueada' end,
      case when not g.funcao_apta then 'funcao_bloqueada' end
    ],null))
  ),
  'skill_ids',case when g.carta_apta and g.funcao_apta then coalesce((
    select jsonb_agg(h.skill_id order by h.skill_id)
    from clube_novo.habilidade_jogo h
    where h.pode_rodar and h.fabricavel and not coalesce(h.vetada,false)
      and not exists(
        select 1 from clube_novo.carta_habilidade_jogo ch
        where ch.card_id=p_card_id and ch.skill_id=h.skill_id
      )
      and not exists(
        select 1 from clube_novo.habilidade_funcao_bloqueio_otimizador b
        where b.skill_id=h.skill_id and b.funcao_id=p_funcao_id
      )
  ),'[]'::jsonb) else '[]'::jsonb end
)
from g
$function$;

revoke all on function public.otimizador_carta_v3(text) from public, anon, authenticated;
revoke all on function public.otimizador_cartas_v3(jsonb) from public, anon, authenticated;
revoke all on function public.otimizador_pool_habilidades_v3(text,bigint) from public, anon, authenticated;
grant execute on function public.otimizador_carta_v3(text) to service_role;
grant execute on function public.otimizador_cartas_v3(jsonb) to service_role;
grant execute on function public.otimizador_pool_habilidades_v3(text,bigint) to service_role;

commit;
