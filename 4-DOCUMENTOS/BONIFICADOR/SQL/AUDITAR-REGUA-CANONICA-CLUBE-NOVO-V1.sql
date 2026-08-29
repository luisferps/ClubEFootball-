-- Auditoria pós-migração, somente leitura. O legado pode aparecer apenas como sombra.
with contratos as (
  select p.proname, pg_get_functiondef(p.oid) as definicao
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.proname in ('bonificador_regua_v1','bonificador_carta_v1','bonificador_pares_v1')
), referencias as (
  select proname, coalesce(jsonb_agg(distinct m[1] order by m[1]),'[]'::jsonb) as relacoes
  from contratos c left join lateral regexp_matches(lower(c.definicao),'(clube(?:_novo)?[.][a-z_]+)','g') m on true
  group by proname
), sombra as (
  select jsonb_build_object(
    'parametros', (select count(*) from clube_novo.bonificador_parametro),
    'moldes', (select count(*) from clube_novo.bonificador_molde_corpo),
    'slots', (select count(*) from clube_novo.bonificador_posicao_slot),
    'regras_playstyle', (select count(*) from clube_novo.bonificador_regra_playstyle),
    'playstyles_distintos', (select count(distinct playstyle_id) from clube_novo.bonificador_regra_playstyle),
    'pares', (select count(*) from clube_novo.bonificador_par),
    'funcao_por_id', jsonb_build_object(
      'molde_1_presente', (public.bonificador_regua_v1()->'molde_corpo') ? '1',
      'molde_textual_ausente', not ((public.bonificador_regua_v1()->'molde_corpo') ? 'centroavante_fixo'),
      'casa_336_go_funcao_id_5', (public.bonificador_regua_v1()#>>'{casa,336,0}')::bigint = 5
    ),
    'casillas', public.bonificador_carta_v1('88045755827028'),
    'regua', public.bonificador_regua_v1()
  ) as valor
)
select jsonb_build_object(
  'referencias_operacionais', (select jsonb_object_agg(proname,relacoes) from referencias),
  'consultas_legadas', (select count(*) from contratos where definicao ~ '(^|[^a-z_])clube[.]'),
  'sombra', (select valor from sombra)
) as auditoria;
