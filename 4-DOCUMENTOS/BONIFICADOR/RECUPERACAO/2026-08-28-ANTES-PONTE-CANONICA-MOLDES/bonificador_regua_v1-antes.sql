create or replace function public.bonificador_regua_v1()
returns jsonb
language sql
stable
security definer
set search_path = ''
as $function$
with
style_names as (
  select distinct er.estilo
  from clube.estilo_regra er
),
style_candidates as (
  select sn.estilo, eo.id / 4 as indice
  from style_names sn
  join clube.estilo_jogo eo on eo.nome = sn.estilo
  union
  select sn.estilo, ed.id as indice
  from style_names sn
  join clube.estilo_defensivo ed on ed.nome = sn.estilo
),
style_unique as (
  select estilo, min(indice) as indice
  from style_candidates
  group by estilo
  having count(distinct indice) = 1
),
stable_rules as (
  select er.estilo, p.id_jogo, pj.id as posicao_id,
         er.funcao_codigo, er.da_bonus
  from clube.estilo_regra er
  join style_unique su using (estilo)
  join clube_novo.playstyle p
    on p.indice = su.indice and p.pode_rodar
  join clube_novo.posicao_jogo pj
    on pj.codigo_antigo = er.posicao and pj.pode_rodar
),
unresolved_styles as (
  select sn.estilo
  from style_names sn
  left join style_unique su using (estilo)
  where su.estilo is null
),
new_foot as (
  select case
           when p.campo = 'pe_ruim_teto' then 'pe_ruim_teto'
           when p.campo = 'pe_ruim_uso' then 'pe_ruim_frequencia_' || p.valor
           when p.campo = 'pe_ruim_precisao' then 'pe_ruim_precisao_' || p.valor
         end as chave,
         p.valor_bonus as valor
  from clube_novo.pe p
  where p.campo like 'pe_ruim%'
    and p.pode_rodar
),
params as (
  select coalesce(
           (select jsonb_object_agg(bp.chave, bp.valor) from clube.bonus_parametro bp),
           '{}'::jsonb
         ) || coalesce(
           (select jsonb_object_agg(nf.chave, nf.valor) from new_foot nf),
           '{}'::jsonb
         ) as valor
),
body_map as (
  select mc.funcao, mc.medida, co.codigo
  from clube.molde_corpo mc
  left join clube.corpo_ordem legacy_order on legacy_order.nosso = mc.medida
  left join clube_novo.corpo_ordem co on co.codigo = legacy_order.codigo
),
position_slots as (
  select pj.id as posicao_id, ps.slot
  from clube.posicao_slot ps
  join clube_novo.posicao_jogo pj
    on pj.codigo_antigo = ps.posicao and pj.pode_rodar
),
gate_values as (
  select
    (select count(*) from clube_novo.corpo_ordem where usado_pelo_motor) as body_used,
    (select count(*) from clube_novo.corpo_ordem where usado_pelo_motor and pode_rodar) as body_ready,
    (select count(*) from clube.molde_corpo) as body_rules,
    (select count(*) from body_map where codigo is not null) as body_rules_mapped,
    (select count(*) from new_foot where chave is not null and valor is not null) as foot_ready,
    (select count(*) from clube_novo.posicao_jogo where pode_rodar) as position_ready,
    (select count(*) from clube_novo.playstyle where pode_rodar) as playstyle_ready,
    (select count(*) from clube_novo.estilo_ia where pode_rodar) as ai_ready,
    (select count(*) from position_slots) as position_slots_mapped,
    (select count(*) from style_names) as style_names_total,
    (select count(*) from style_unique) as style_names_mapped,
    (select count(*) from unresolved_styles) as style_names_unresolved,
    (select array_agg(estilo order by estilo) from unresolved_styles) as unresolved_names
),
gate as (
  select g.*,
         array_remove(array[
           case when body_used <> 12 then 'corpo_ordem: cardinalidade usada diferente de 12' end,
           case when body_ready <> 12 then 'corpo_ordem: catalogo usado sem pode_rodar' end,
           case when body_rules <> 384 then 'molde_corpo: cardinalidade diferente de 384' end,
           case when body_rules_mapped <> body_rules then 'molde_corpo: medida sem codigo novo' end,
           case when foot_ready <> 9 then 'pe: regua fisica incompleta' end,
           case when position_ready <> 13 then 'posicao_jogo: catalogo incompleto ou bloqueado' end,
           case when playstyle_ready <> 36 then 'playstyle: catalogo incompleto ou bloqueado' end,
           case when ai_ready <> 7 then 'estilo_ia: catalogo incompleto ou bloqueado' end,
           case when position_slots_mapped <> 13 then 'posicao_slot: ponte incompleta' end,
           case when style_names_total <> 31 then 'estilo_regra: cardinalidade inesperada' end,
           case when style_names_mapped <> 30 then 'estilo_regra: pontes estaveis diferentes de 30' end,
           case when style_names_unresolved <> 1
                  or unresolved_names is distinct from array['Goleiro adiantado']::text[]
                then 'estilo_regra: pendencia especifica mudou' end
         ]::text[], null) as faltas
  from gate_values g
),
body_shape as (
  select jsonb_object_agg(x.funcao, x.medidas) as valor
  from (
    select mc.funcao,
           jsonb_object_agg(mc.medida, jsonb_build_object(
             'direcao', mc.direcao,
             'peso', mc.peso,
             'cortes', jsonb_build_array(mc.corte1, mc.corte2, mc.corte3, mc.corte4)
           )) as medidas
    from clube.molde_corpo mc
    group by mc.funcao
  ) x
),
body_order as (
  select jsonb_object_agg(co.pos::text, jsonb_build_object(
           'codigo', co.codigo,
           'nosso', co.nosso,
           'pode_rodar', co.pode_rodar
         ) order by co.pos) as valor
  from clube_novo.corpo_ordem co
  where co.usado_pelo_motor
),
style_house as (
  select coalesce(jsonb_object_agg(x.id_jogo::text, x.mapa), '{}'::jsonb) as valor
  from (
    select sr.id_jogo,
           jsonb_object_agg(sr.posicao_id::text, sr.funcao_codigo) as mapa
    from stable_rules sr
    where sr.funcao_codigo is not null
    group by sr.id_jogo
  ) x
),
style_active as (
  select coalesce(jsonb_object_agg(x.id_jogo::text, x.posicoes), '{}'::jsonb) as valor
  from (
    select sr.id_jogo,
           jsonb_agg(sr.posicao_id order by sr.posicao_id) as posicoes
    from stable_rules sr
    where sr.da_bonus
    group by sr.id_jogo
  ) x
),
position_slot_json as (
  select jsonb_object_agg(ps.posicao_id::text, ps.slot) as valor
  from position_slots ps
)
select jsonb_build_object(
  'contrato', 'bonificador-regua-v1',
  'pode_rodar', cardinality(g.faltas) = 0,
  'falta_o_que', to_jsonb(g.faltas),
  'parametro', p.valor,
  'molde_corpo', coalesce(bs.valor, '{}'::jsonb),
  'corpo_ordem', coalesce(bo.valor, '{}'::jsonb),
  'casa', sh.valor,
  'liga', sa.valor,
  'posicao_slot', coalesce(psj.valor, '{}'::jsonb),
  'estilos_bloqueados', jsonb_build_array(291),
  'bloqueio_291', jsonb_build_object(
    'id_jogo', 291,
    'motivo', 'regra legada Goleiro adiantado sem identidade estavel; decisao pendente',
    'card_id_amostra', '88045755827028'
  ),
  'bloqueio', coalesce((
    select jsonb_object_agg(x.funcao_codigo, x.habilidades)
    from (
      select b.funcao_codigo,
             jsonb_agg(b.habilidade_nome order by b.habilidade_nome) as habilidades
      from clube.bloqueio b
      group by b.funcao_codigo
    ) x
  ), '{}'::jsonb),
  'sa_familia', coalesce((
    select jsonb_object_agg(sf.estilo_id, sf.casa) from clube.sa_familia sf
  ), '{}'::jsonb),
  'regra_funcao', coalesce((
    select jsonb_object_agg(x.posicao, x.funcoes)
    from (
      select rf.posicao,
             jsonb_agg(rf.funcao_codigo order by rf.funcao_codigo) as funcoes
      from clube.regra_funcao rf
      group by rf.posicao
    ) x
  ), '{}'::jsonb),
  'posicao_sigla', coalesce((
    select jsonb_object_agg(pj.codigo_en, pj.id) from clube_novo.posicao_jogo pj
    where pj.pode_rodar
  ), '{}'::jsonb),
  'proveniencia', jsonb_build_object(
    'corpo_ordem', 'clube_novo.corpo_ordem',
    'pe', 'clube_novo.pe.valor_bonus',
    'posicao', 'clube_novo.posicao_jogo.id',
    'playstyle', 'clube_novo.playstyle.id_jogo',
    'estilo_ia', 'clube_novo.estilo_ia.bit',
    'molde_corpo', 'clube.molde_corpo: regra ClubEfootball, nao dado do jogo',
    'estilo_regra', 'clube.estilo_regra: regra ClubEfootball reindexada por IDs'
  ),
  'cardinalidades', jsonb_build_object(
    'corpo_usado', g.body_used,
    'molde_corpo', g.body_rules,
    'pe', g.foot_ready,
    'posicoes', g.position_ready,
    'playstyles', g.playstyle_ready,
    'estilos_ia', g.ai_ready,
    'estilos_regra_mapeados', g.style_names_mapped,
    'estilos_regra_bloqueados', g.style_names_unresolved
  )
)
from gate g
cross join params p
cross join body_shape bs
cross join body_order bo
cross join style_house sh
cross join style_active sa
cross join position_slot_json psj;
$function$;;
