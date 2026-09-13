-- Validacao da selecao por maior nota da Ficha V2.
-- Somente leitura.

-- 1. Metadados e regra instalada.
select
  p.oid::regprocedure::text as assinatura,
  md5(pg_get_functiondef(p.oid)) as definicao_md5,
  p.provolatile,
  p.prosecdef,
  p.proconfig,
  has_function_privilege('anon', p.oid, 'EXECUTE') as anon_executa_base,
  has_function_privilege('authenticated', p.oid, 'EXECUTE') as autenticado_executa_base,
  has_function_privilege('service_role', p.oid, 'EXECUTE') as service_role_executa_base,
  strpos(
    pg_get_functiondef(p.oid),
    E'order by\n    p.nota_final desc nulls last,'
  ) > 0 as default_ordena_nota_primeiro
from pg_proc p
where p.oid =
  'public.site_novo_ficha_base_publicada_v1(text,bigint)'::regprocedure::oid;

-- 2. Universo publico: a linha escolhida pela V2 deve ter MAX(nota_final) em todo card.
with publicadas as materialized (
  select
    l.card_id,
    l.id as linha_id,
    a.nota_final,
    a.publicada_em,
    case
      when jsonb_typeof(bo.atributos_finais) = 'array'
        then jsonb_array_length(bo.atributos_finais) = 26
      else false
    end as atributos_completos
  from clube_novo.build_linha_card l
  join clube_novo.build_publicacao_linha_ativa_v1 a
    on a.linha_id = l.id
  join clube_novo.build_otimizador bo
    on bo.id = a.build_otimizador_id
  where l.execucao_tipo = 'producao'
    and l.lote_teste_id is null
    and not (l.pendencias @> array['teste_nao_publicado'::text])
),
escolhidas as (
  select p.*,
    row_number() over (
      partition by p.card_id
      order by
        p.nota_final desc nulls last,
        p.atributos_completos desc,
        p.publicada_em desc,
        p.linha_id asc
    ) as rn
  from publicadas p
)
select
  count(*) as cards_publicos,
  count(*) filter (
    where e.nota_final is distinct from x.nota_max
  ) as cards_default_diverge_max,
  count(*) filter (
    where e.nota_final is null
  ) as cards_default_nota_nula
from escolhidas e
join (
  select card_id, max(nota_final) as nota_max
  from publicadas
  group by card_id
) x using (card_id)
where e.rn = 1;

-- 3. McKennie: default e linhas explicitas.
with casos(card_id, linha_pedida) as (
  values
    ('55068997045101'::text, null::bigint),
    ('55068997045101'::text, 8475::bigint),
    ('55068997045101'::text, 8474::bigint)
),
respostas as (
  select c.*, public.site_novo_ficha_v1(c.card_id,c.linha_pedida) as j
  from casos c
)
select
  card_id,
  linha_pedida,
  j#>>'{dados,build,linha_id}' as linha_retornada,
  j#>>'{dados,build,nota_final}' as nota_retornada,
  (
    select jsonb_agg(e->>'linha_id')
    from jsonb_array_elements(j#>'{dados,builds_publicadas}') e
    where coalesce((e->>'selecionada')::boolean,false)
  ) as linhas_marcadas_selecionadas
from respostas
order by linha_pedida nulls first;

-- 4. Plano e tempo do anon devem permanecer abaixo de 3 s.
explain (analyze, buffers, format json)
select public.site_novo_ficha_v1('55068997045101',null);

