-- Validação pós-migração 20260905213546.
-- Deve retornar contrato_ok=true, cache_exato=true e nenhum item em diagnostico.

with lote as (
  select id
  from clube_novo.bonificador_correcao_lote_v1
  where tipo = 'integral'
    and motor_versao = 'v10-0409-fisico-regra-aprovada-v1'
    and estado in ('preparado','rodando','pausando','pausado','processado')
  order by criado_em desc
  limit 1
), real as (
  select
    count(*)::bigint as total,
    count(*) filter (where i.estado_item = 'pendente')::bigint as pendente,
    count(*) filter (where i.estado_item = 'processando')::bigint as processando,
    count(*) filter (where i.estado_item = 'preparado')::bigint as preparado,
    count(*) filter (where i.estado_item = 'falha')::bigint as falha
  from lote l
  join clube_novo.bonificador_correcao_item_v1 i on i.lote_id = l.id
), cache as (
  select c.total, c.pendente, c.processando, c.preparado, c.falha
  from lote l
  join clube_novo.bonificador_correcao_status_cache_v1 c on c.lote_id = l.id
), resposta as (
  select public.site_novo_publicacao_status_v1('89136409091415') as j
)
select
  (select to_jsonb(real) = to_jsonb(cache) from real, cache) as cache_exato,
  j->>'contrato' = 'site-novo-publicacao-status-v1' as contrato_ok,
  (j->>'versao')::integer = 1 as versao_ok,
  j ?& array[
    'contrato','versao','estado','card_id','card_em_atualizacao',
    'linhas_publicadas_do_card','lote_v10'
  ] as chaves_raiz_ok,
  (j->'lote_v10') ?& array[
    'id','estado','total','preparadas','processando','falhas','pendentes'
  ] as chaves_lote_ok
from resposta;

select p.proname, pg_get_userbyid(p.proowner) as owner, p.prosecdef,
       p.provolatile, p.proconfig, p.proacl,
       obj_description(p.oid, 'pg_proc') as comentario
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public'
  and p.proname = 'site_novo_publicacao_status_v1';

explain (analyze, buffers, format text)
select public.site_novo_publicacao_status_v1('89136409091415');

explain (analyze, buffers, format text)
select public.site_novo_ficha_v1('89136409091415', null);
