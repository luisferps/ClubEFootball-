begin transaction read only;

with
regua as (
  select public.bonificador_regua_v1() valor
),
referencias as (
  select b.card_id, b.funcao_codigo,
         fs.id as funcao_id, fs.nome_legado, fs.rotulo, fs.pode_rodar
  from clube.build_arquivo_2608 b
  left join clube_novo.funcao_sistema fs
    on fs.codigo_legado = b.funcao_codigo
),
funcoes_usadas as (
  select funcao_codigo, funcao_id, nome_legado, rotulo, pode_rodar,
         count(*) as referencias
  from referencias
  group by funcao_codigo, funcao_id, nome_legado, rotulo, pode_rodar
),
old_shapes as (
  select f.funcao_codigo, f.funcao_id, f.nome_legado, f.rotulo,
         f.pode_rodar, f.referencias,
         jsonb_object_agg(mc.medida, jsonb_build_object(
           'idx', co.pos,
           'direcao', mc.direcao,
           'peso', mc.peso,
           'cortes', jsonb_build_array(mc.corte1, mc.corte2, mc.corte3, mc.corte4)
         )) as old_shape,
         count(mc.*)::integer as regras,
         md5(string_agg(
           mc.medida || '|' || co.pos || '|' || mc.direcao || '|' || mc.peso || '|' ||
           coalesce(mc.corte1::text, '∅') || '|' || coalesce(mc.corte2::text, '∅') || '|' ||
           coalesce(mc.corte3::text, '∅') || '|' || coalesce(mc.corte4::text, '∅'),
           E'\n' order by mc.medida
         )) as conteudo_md5
  from funcoes_usadas f
  left join clube.molde_corpo mc on mc.funcao = f.nome_legado
  left join clube.corpo_ordem legacy_order on legacy_order.nosso = mc.medida
  left join clube_novo.corpo_ordem co on co.codigo = legacy_order.codigo
  group by f.funcao_codigo, f.funcao_id, f.nome_legado, f.rotulo,
           f.pode_rodar, f.referencias
),
shape_comparison as (
  select o.*,
         r.valor -> 'molde_corpo' -> o.funcao_codigo as new_shape,
         r.valor -> 'funcao_molde' -> o.funcao_codigo as ponte_publicada
  from old_shapes o
  cross join regua r
),
body_values as (
  select cc.card_id, co.pos, co.nosso as medida, cc.valor::numeric as valor
  from clube_novo.carta_corpo_jogo cc
  join clube_novo.corpo_ordem co
    on co.codigo = cc.codigo_corpo and co.usado_pelo_motor
),
old_formula as (
  select r.card_id, r.funcao_codigo,
         round(((sum((
           (case when bv.valor >= mc.corte1 then 1 else 0 end +
            case when bv.valor >= mc.corte2 then 1 else 0 end +
            case when bv.valor >= mc.corte3 then 1 else 0 end +
            case when bv.valor >= mc.corte4 then 1 else 0 end)::numeric / 4
         ) * mc.peso) / sum(mc.peso)) * 2 - 1) *
         (select valor from clube.bonus_parametro where chave = 'bonus_corpo_max'), 4) as bonus
  from referencias r
  join clube.molde_corpo mc on mc.funcao = r.nome_legado
  join body_values bv on bv.card_id = r.card_id and bv.medida = mc.medida
  group by r.card_id, r.funcao_codigo
),
new_rules as (
  select r.card_id, r.funcao_codigo, e.key as medida,
         (e.value ->> 'idx')::integer as idx,
         (e.value ->> 'direcao')::numeric as direcao,
         (e.value ->> 'peso')::numeric as peso,
         (e.value -> 'cortes' ->> 0)::numeric as corte1,
         (e.value -> 'cortes' ->> 1)::numeric as corte2,
         (e.value -> 'cortes' ->> 2)::numeric as corte3,
         (e.value -> 'cortes' ->> 3)::numeric as corte4
  from referencias r
  cross join regua rg
  cross join lateral jsonb_each(rg.valor -> 'molde_corpo' -> r.funcao_codigo) e
),
new_formula as (
  select nr.card_id, nr.funcao_codigo,
         round(((sum((
           (case when bv.valor >= nr.corte1 then 1 else 0 end +
            case when bv.valor >= nr.corte2 then 1 else 0 end +
            case when bv.valor >= nr.corte3 then 1 else 0 end +
            case when bv.valor >= nr.corte4 then 1 else 0 end)::numeric / 4
         ) * nr.peso) / sum(nr.peso)) * 2 - 1) *
         (select valor from clube.bonus_parametro where chave = 'bonus_corpo_max'), 4) as bonus
  from new_rules nr
  join body_values bv on bv.card_id = nr.card_id and bv.pos = nr.idx
  group by nr.card_id, nr.funcao_codigo
),
formula_comparison as (
  select r.card_id, r.funcao_codigo, o.bonus old_bonus, n.bonus new_bonus
  from referencias r
  left join old_formula o using (card_id, funcao_codigo)
  left join new_formula n using (card_id, funcao_codigo)
)
select jsonb_build_object(
  'trava_formula', jsonb_build_object(
    'runtime_alterado', false,
    'referencia_indice', 'medida antiga resolve corpo_ordem.pos canonico',
    'direcao', 'preservada como entrada; a matematica Python nao foi alterada',
    'pesos_cortes_ordem', 'identicos por JSONB e fingerprint'
  ),
  'ponte', jsonb_build_object(
    'referencias', (select count(*) from referencias),
    'referencias_resolvidas', (
      select count(*) from referencias r
      cross join regua rg
      where r.funcao_id is not null
        and r.pode_rodar
        and rg.valor -> 'molde_corpo' ? r.funcao_codigo
        and (select count(*) from jsonb_object_keys(
          rg.valor -> 'molde_corpo' -> r.funcao_codigo
        )) = 12
    ),
    'funcoes', (select count(*) from shape_comparison),
    'ids_distintos', (select count(distinct funcao_id) from shape_comparison),
    'funcoes_12_regras', (select count(*) from shape_comparison where regras = 12),
    'divergencias_estruturais', (
      select count(*) from shape_comparison
      where old_shape is distinct from new_shape
    ),
    'mapeamento', (
      select jsonb_agg(jsonb_build_object(
        'id', funcao_id,
        'codigo', funcao_codigo,
        'nome', nome_legado,
        'rotulo', rotulo,
        'referencias', referencias,
        'regras', regras,
        'conteudo_md5', conteudo_md5,
        'estrutura_igual', old_shape = new_shape,
        'ponte_publicada', ponte_publicada
      ) order by funcao_id)
      from shape_comparison
    )
  ),
  'paridade_formula', jsonb_build_object(
    'referencias', (select count(*) from formula_comparison),
    'pares_com_insumo_novo', (
      select count(*) from formula_comparison
      where old_bonus is not null and new_bonus is not null
    ),
    'pares_sem_carta_nova', (
      select count(*) from formula_comparison
      where old_bonus is null and new_bonus is null
    ),
    'divergencias', (
      select count(*) from formula_comparison
      where old_bonus is distinct from new_bonus
    ),
    'fingerprint_antigo_canonico', (
      select md5(string_agg(
        card_id || '|' || funcao_codigo || '|' || coalesce(old_bonus::text, '∅'),
        E'\n' order by card_id, funcao_codigo
      )) from formula_comparison
    ),
    'fingerprint_novo_codigo', (
      select md5(string_agg(
        card_id || '|' || funcao_codigo || '|' || coalesce(new_bonus::text, '∅'),
        E'\n' order by card_id, funcao_codigo
      )) from formula_comparison
    )
  ),
  'casillas_291', public.bonificador_carta_v1('88045755827028')
) as auditoria_ponte_moldes;

rollback;
