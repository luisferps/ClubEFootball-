-- Readback somente leitura da V68.
-- Não chama a função de importação e não altera nenhuma linha.

with alvo as (
  select p.oid,
         p.prosecdef,
         p.proconfig,
         pg_get_functiondef(p.oid) as definicao,
         obj_description(p.oid, 'pg_proc') as comentario
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.oid = to_regprocedure(
      'public.otimizador_producao_importar_json_local_v1(uuid,bigint,jsonb,timestamptz)'
    )
)
select
  count(*) = 1 as funcao_unica,
  bool_and(prosecdef) as security_definer,
  bool_and(proconfig @> array['search_path=""']) as search_path_vazio,
  bool_and(definicao like '%v_l.otimizador_formula_fingerprint_esperado%') as usa_formula_da_linha,
  bool_and(definicao like '%v_l.otimizador_contrato_fingerprint_esperado%') as usa_contrato_da_linha,
  bool_and(definicao like '%v_l.otimizador_motor_versao_esperada%') as usa_motor_da_linha,
  bool_and(definicao not like $$%p_resultado->>'lote_fingerprint' <> v_lote.fingerprint%$$)
    as nao_compara_agregado_mutavel,
  bool_and(definicao not like $$%e.evento = 'preparo_integral_concluido'%$$)
    as nao_exige_historico_incompleto,
  bool_and(definicao like $$%v_lote_fingerprint_recebido !~ '^[0-9a-f]{64}$'%$$)
    as exige_fingerprint_bem_formado,
  bool_and(comentario like 'V68:%') as comentario_v68,
  not has_function_privilege(
    'anon',
    'public.otimizador_producao_importar_json_local_v1(uuid,bigint,jsonb,timestamptz)',
    'EXECUTE'
  ) as anon_bloqueado,
  not has_function_privilege(
    'authenticated',
    'public.otimizador_producao_importar_json_local_v1(uuid,bigint,jsonb,timestamptz)',
    'EXECUTE'
  ) as authenticated_bloqueado,
  has_function_privilege(
    'service_role',
    'public.otimizador_producao_importar_json_local_v1(uuid,bigint,jsonb,timestamptz)',
    'EXECUTE'
  ) as service_role_liberado
from alvo;

select
  l.id as linha_id,
  l.estado_otimizador,
  lote.estado as lote_estado,
  lote.tipo_lote,
  lote.pode_publicar,
  l.otimizador_formula_fingerprint_esperado is not null as formula_da_linha_presente,
  l.otimizador_contrato_fingerprint_esperado is not null as contrato_da_linha_presente,
  l.otimizador_motor_versao_esperada is not null as motor_da_linha_presente,
  q.entrada_fingerprint is not null as entrada_da_linha_presente,
  l.impeto_condicional_codigo,
  l.impeto_condicional_nivel,
  l.build_otimizador_id
from clube_novo.build_linha_card l
join clube_novo.otimizador_lote_producao_linha_v3 q
  on q.lote_id = l.lote_producao_id
 and q.linha_id = l.id
join clube_novo.otimizador_lote_producao_v3 lote
  on lote.id = l.lote_producao_id
where l.id = 367908;

select
  evento,
  detalhe->>'fingerprint' as lote_fingerprint_confirmado,
  criado_em
from clube_novo.otimizador_evento_producao_v3
where lote_id = 'ddbcbc86-1ae7-4b95-b9f0-22601f41b61d'::uuid
  and evento = 'preparo_integral_concluido'
order by criado_em;

select
  l.otimizador_formula_fingerprint_esperado,
  l.otimizador_contrato_fingerprint_esperado,
  l.otimizador_motor_versao_esperada,
  count(*)::bigint as linhas,
  count(*) filter (where l.estado_otimizador = 'pendente')::bigint as pendentes
from clube_novo.build_linha_card l
where l.lote_producao_id = 'ddbcbc86-1ae7-4b95-b9f0-22601f41b61d'::uuid
group by 1, 2, 3
order by min(l.id);
