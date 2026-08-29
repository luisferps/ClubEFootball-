begin;

do $preflight$
begin
  if to_regprocedure('public.bonificador_regua_v1()') is not null
     or to_regprocedure('public.bonificador_carta_v1(text)') is not null
     or to_regprocedure('public.bonificador_pares_v1(integer,integer)') is not null then
    raise exception 'preflight: um contrato Bonificador v1 ja existe; nada foi sobrescrito';
  end if;
end
$preflight$;

create function public.bonificador_regua_v1()
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
canonical_body_functions as (
  select fs.id, fs.codigo_legado, fs.nome_legado, fs.rotulo, fs.pode_rodar
  from clube_novo.funcao_sistema fs
  where fs.ativa
),
canonical_body_rules as (
  select cf.id as funcao_id, cf.codigo_legado, cf.nome_legado, cf.rotulo,
         cf.pode_rodar, mc.medida, mc.direcao, mc.peso,
         mc.corte1, mc.corte2, mc.corte3, mc.corte4,
         co.pos as idx, co.codigo as codigo_corpo,
         co.pode_rodar as medida_pode_rodar, co.usado_pelo_motor
  from canonical_body_functions cf
  left join clube.molde_corpo mc on mc.funcao = cf.nome_legado
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
    (select count(*) from canonical_body_functions) as body_functions,
    (select count(*) from canonical_body_functions
      where pode_rodar and codigo_legado is not null and nome_legado is not null
    ) as body_functions_ready,
    (select count(*) from canonical_body_rules
      where medida is not null and idx is not null
        and medida_pode_rodar and usado_pelo_motor
    ) as body_canonical_rules,
    (select count(*) from (
      select funcao_id from canonical_body_rules
      group by funcao_id
      having count(medida) = 12 and count(idx) = 12 and count(distinct idx) = 12
    ) x) as body_functions_with_12,
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
           case when body_functions <> 19 then 'funcao_sistema: cardinalidade ativa diferente de 19' end,
           case when body_functions_ready <> 19 then 'funcao_sistema: codigo/nome canonico ausente ou bloqueado' end,
           case when body_canonical_rules <> 228 then 'molde_corpo: ponte canonica de funcao/indice diferente de 19 x 12' end,
           case when body_functions_with_12 <> 19 then 'molde_corpo: funcao canonica sem 12 indices unicos' end,
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
  select jsonb_object_agg(x.codigo_legado, x.medidas) as valor
  from (
    select cr.codigo_legado,
           jsonb_object_agg(cr.medida, jsonb_build_object(
             'idx', cr.idx,
             'direcao', cr.direcao,
             'peso', cr.peso,
             'cortes', jsonb_build_array(cr.corte1, cr.corte2, cr.corte3, cr.corte4)
           )) as medidas
    from canonical_body_rules cr
    where cr.pode_rodar and cr.medida is not null
      and cr.medida_pode_rodar and cr.usado_pelo_motor and cr.idx is not null
    group by cr.codigo_legado
  ) x
),
body_function_bridge_json as (
  select jsonb_object_agg(cf.codigo_legado, jsonb_build_object(
           'id', cf.id,
           'nome_legado', cf.nome_legado,
           'rotulo', cf.rotulo,
           'pode_rodar', cf.pode_rodar
         ) order by cf.id) as valor
  from canonical_body_functions cf
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
  'funcao_molde', coalesce(bfj.valor, '{}'::jsonb),
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
    'funcao_molde', 'clube_novo.funcao_sistema.id por codigo_legado e nome_legado',
    'medida_molde', 'clube_novo.corpo_ordem.pos por codigo fisico e nome legado',
    'estilo_regra', 'clube.estilo_regra: regra ClubEfootball reindexada por IDs'
  ),
  'cardinalidades', jsonb_build_object(
    'corpo_usado', g.body_used,
    'molde_corpo', g.body_rules,
    'funcoes_molde_canonicas', g.body_functions_ready,
    'regras_molde_canonicas', g.body_canonical_rules,
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
cross join body_function_bridge_json bfj
cross join body_order bo
cross join style_house sh
cross join style_active sa
cross join position_slot_json psj;
$function$;

create function public.bonificador_carta_v1(p_card_id text)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $function$
with
c as (
  select j.*
  from clube_novo.carta_jogo j
  where j.card_id = p_card_id
),
body as (
  select coalesce(jsonb_agg(cc.valor order by co.pos), '[]'::jsonb) as valores,
         count(*)::integer as n,
         count(*) filter (where not coalesce(co.pode_rodar, false))::integer as bloqueadas
  from clube_novo.carta_corpo_jogo cc
  join clube_novo.corpo_ordem co on co.codigo = cc.codigo_corpo
  where cc.card_id = p_card_id
    and co.usado_pelo_motor
),
ai as (
  select coalesce(jsonb_agg(ce.bit_estilo_ia order by ce.bit_estilo_ia), '[]'::jsonb) as bits,
         count(*)::integer as n,
         count(*) filter (where i.bit is null or not coalesce(i.pode_rodar, false))::integer as bloqueadas
  from clube_novo.carta_estilo_ia_jogo ce
  left join clube_novo.estilo_ia i on i.bit = ce.bit_estilo_ia
  where ce.card_id = p_card_id
),
principal_position as (
  select count(*)::integer as n, min(cp.posicao_id) as posicao_id
  from clube_novo.carta_posicao_principal_jogo cp
  where cp.card_id = p_card_id
),
playstyle_slots as (
  select count(*)::integer as n,
         max(cp.valor_raw) filter (where cp.slot_fisico = 1) as slot1_raw,
         max(cp.playstyle_id) filter (where cp.slot_fisico = 1) as slot1_id_jogo,
         max(cp.valor_raw) filter (where cp.slot_fisico = 2) as slot2_raw,
         max(cp.playstyle_id) filter (where cp.slot_fisico = 2) as slot2_id_jogo
  from clube_novo.carta_playstyle_jogo cp
  where cp.card_id = p_card_id
),
foot_values as (
  select count(*)::integer as n,
         max(cp.valor) filter (where cp.campo = 'pe_ruim_uso') as pe_ruim_uso,
         max(cp.valor) filter (where cp.campo = 'pe_ruim_precisao') as pe_ruim_precisao
  from clube_novo.carta_pe_jogo cp
  where cp.card_id = p_card_id
),
base as (
  select c.card_id, c.nome, c.posicao as posicao_raw,
         fv.pe_ruim_uso, fv.pe_ruim_precisao,
         c.pe_ruim_uso as pe_ruim_uso_escalar,
         c.pe_ruim_precisao as pe_ruim_precisao_escalar,
         ps.slot1_raw, ps.slot2_raw,
         c.slot_ofensivo_id as slot1_scalar_raw,
         c.slot_defensivo_id as slot2_scalar_raw,
         pj.id as posicao_id, pj.codigo_antigo as posicao_codigo,
         pj.pode_rodar as posicao_pode_rodar,
         p1.id_jogo as slot1_id_jogo, p1.nome_pt as slot1_nome,
         p1.pode_rodar as slot1_pode_rodar,
         p2.id_jogo as slot2_id_jogo, p2.nome_pt as slot2_nome,
         p2.pode_rodar as slot2_pode_rodar,
         pp.n as posicao_relacao_n,
         ps.n as playstyle_relacao_n,
         fv.n as pe_relacao_n,
         b.valores as corpo, b.n as corpo_n, b.bloqueadas as corpo_bloqueadas,
         a.bits as estilos_ia, a.n as estilos_ia_n, a.bloqueadas as ia_bloqueadas
  from (select 1 as seed) s
  left join c on true
  cross join body b
  cross join ai a
  cross join principal_position pp
  cross join playstyle_slots ps
  cross join foot_values fv
  left join clube_novo.posicao_jogo pj
    on pj.id = pp.posicao_id
  left join clube_novo.playstyle p1
    on p1.id_jogo = ps.slot1_id_jogo
  left join clube_novo.playstyle p2
    on p2.id_jogo = ps.slot2_id_jogo
),
gated as (
  select b.*,
         array_remove(array[
           case when b.card_id is null then 'carta ausente em clube_novo.carta_jogo' end,
           case when b.corpo_n <> 12 then 'corpo: cardinalidade diferente de 12' end,
           case when b.corpo_bloqueadas <> 0 then 'corpo: catalogo sem pode_rodar' end,
           case when b.card_id is not null and not exists (
             select 1 from clube_novo.pe p
             where p.campo = 'pe_ruim_uso' and p.valor = b.pe_ruim_uso
               and p.pode_rodar and p.valor_bonus is not null
           ) then 'pe ruim: uso sem valor apto' end,
           case when b.card_id is not null and not exists (
             select 1 from clube_novo.pe p
             where p.campo = 'pe_ruim_precisao' and p.valor = b.pe_ruim_precisao
               and p.pode_rodar and p.valor_bonus is not null
           ) then 'pe ruim: precisao sem valor apto' end,
           case when b.card_id is not null and b.pe_relacao_n <> 3
             then 'pe: cardinalidade normalizada diferente de 3' end,
           case when b.card_id is not null and (
             b.pe_ruim_uso is distinct from b.pe_ruim_uso_escalar
             or b.pe_ruim_precisao is distinct from b.pe_ruim_precisao_escalar
           ) then 'pe: escalares e relacao normalizada divergem' end,
           case when b.card_id is not null and (b.posicao_id is null or not coalesce(b.posicao_pode_rodar, false))
             then 'posicao: relacao principal sem catalogo apto' end,
           case when b.card_id is not null and b.posicao_relacao_n <> 1
             then 'posicao: cardinalidade principal diferente de 1' end,
           case when b.card_id is not null and b.posicao_raw is distinct from (
             select pj2.codigo_en from clube_novo.posicao_jogo pj2 where pj2.id = b.posicao_id
           ) then 'posicao: escalar e relacao principal divergem' end,
           case when b.card_id is not null and (b.slot1_id_jogo is null or not coalesce(b.slot1_pode_rodar, false))
             then 'playstyle slot 1: raw sem catalogo apto' end,
           case when b.card_id is not null and (b.slot2_id_jogo is null or not coalesce(b.slot2_pode_rodar, false))
             then 'playstyle slot 2: raw sem catalogo apto' end,
           case when b.card_id is not null and b.playstyle_relacao_n <> 2
             then 'playstyle: cardinalidade normalizada diferente de 2' end,
           case when b.card_id is not null and (
             b.slot1_raw is distinct from b.slot1_scalar_raw
             or b.slot2_raw is distinct from b.slot2_scalar_raw
           ) then 'playstyle: escalares e relacao normalizada divergem' end,
           case when b.ia_bloqueadas <> 0 then 'estilo de IA: relacao sem catalogo apto' end,
           case when b.slot1_id_jogo = 291 or b.slot2_id_jogo = 291
             then 'playstyle 291: regra Goleiro adiantado aguarda decisao' end
         ]::text[], null) as faltas
  from base b
)
select jsonb_build_object(
  'contrato', 'bonificador-carta-v1',
  'card_id', g.card_id,
  'nome', g.nome,
  'pode_rodar', cardinality(g.faltas) = 0,
  'falta_o_que', to_jsonb(g.faltas),
  'corpo', g.corpo,
  'corpo_cardinalidade', g.corpo_n,
  'pe_ruim_uso', g.pe_ruim_uso,
  'pe_ruim_precisao', g.pe_ruim_precisao,
  'pe_relacao_cardinalidade', g.pe_relacao_n,
  'posicao_id', g.posicao_id,
  'posicao_relacao_cardinalidade', g.posicao_relacao_n,
  'posicao_codigo', g.posicao_codigo,
  'posicao_raw', g.posicao_raw,
  'slot1_id_jogo', g.slot1_id_jogo,
  'playstyle_relacao_cardinalidade', g.playstyle_relacao_n,
  'slot1_nome', g.slot1_nome,
  'slot1_raw', g.slot1_raw,
  'slot2_id_jogo', g.slot2_id_jogo,
  'slot2_nome', g.slot2_nome,
  'slot2_raw', g.slot2_raw,
  'estilos_ia', g.estilos_ia,
  'estilos_ia_cardinalidade', g.estilos_ia_n,
  'proveniencia', jsonb_build_object(
    'carta', 'clube_novo.carta_jogo',
    'corpo', 'clube_novo.carta_corpo_jogo -> corpo_ordem.codigo',
    'pe', 'clube_novo.carta_pe_jogo(campo,valor) -> clube_novo.pe(campo,valor)',
    'posicao', 'clube_novo.carta_posicao_principal_jogo.posicao_id -> posicao_jogo.id',
    'slot1', 'clube_novo.carta_playstyle_jogo(slot_fisico=1).playstyle_id -> playstyle.id_jogo',
    'slot2', 'clube_novo.carta_playstyle_jogo(slot_fisico=2).playstyle_id -> playstyle.id_jogo',
    'ia', 'clube_novo.carta_estilo_ia_jogo.bit_estilo_ia'
  )
)
from gated g;
$function$;

create function public.bonificador_pares_v1(
  p_limit integer default 1000,
  p_offset integer default 0
)
returns table(card_id text, funcao_codigo text)
language sql
stable
security definer
set search_path = ''
as $function$
  select b.card_id, b.funcao_codigo
  from clube.build b
  order by b.card_id, b.funcao_codigo
  limit least(greatest(coalesce(p_limit, 1000), 1), 5000)
  offset greatest(coalesce(p_offset, 0), 0);
$function$;

revoke all on function public.bonificador_regua_v1() from public, anon, authenticated;
revoke all on function public.bonificador_carta_v1(text) from public, anon, authenticated;
revoke all on function public.bonificador_pares_v1(integer, integer) from public, anon, authenticated;

grant execute on function public.bonificador_regua_v1() to service_role;
grant execute on function public.bonificador_carta_v1(text) to service_role;
grant execute on function public.bonificador_pares_v1(integer, integer) to service_role;

comment on function public.bonificador_regua_v1() is
  'Contrato privado v1 do Bonificador. Le clube_novo por chaves fisicas e regras ClubEfootball allowlisted.';
comment on function public.bonificador_carta_v1(text) is
  'Contrato privado v1 da carta para o Bonificador. Fail-closed, sem fallback para o legado.';
comment on function public.bonificador_pares_v1(integer, integer) is
  'Contrato privado v1 dos pares ja produzidos pelo Otimizador para o Bonificador.';

do $readback$
declare
  regua jsonb;
  carta_ok jsonb;
  carta_bloqueada jsonb;
begin
  regua := public.bonificador_regua_v1();
  if coalesce((regua ->> 'pode_rodar')::boolean, false) is not true then
    raise exception 'readback: regua v1 bloqueada: %', regua -> 'falta_o_que';
  end if;

  carta_ok := public.bonificador_carta_v1('176844');
  if coalesce((carta_ok ->> 'pode_rodar')::boolean, false) is not true then
    raise exception 'readback: carta controle 176844 bloqueada: %', carta_ok -> 'falta_o_que';
  end if;

  carta_bloqueada := public.bonificador_carta_v1('88045755827028');
  if coalesce((carta_bloqueada ->> 'pode_rodar')::boolean, true) is not false
     or not (carta_bloqueada -> 'falta_o_que' @> '["playstyle 291: regra Goleiro adiantado aguarda decisao"]'::jsonb) then
    raise exception 'readback: gate do playstyle 291 nao funcionou';
  end if;

  if not has_function_privilege('service_role', 'public.bonificador_regua_v1()', 'EXECUTE')
     or has_function_privilege('anon', 'public.bonificador_regua_v1()', 'EXECUTE')
     or has_function_privilege('authenticated', 'public.bonificador_regua_v1()', 'EXECUTE') then
    raise exception 'readback: privilegios incorretos em bonificador_regua_v1';
  end if;

  if not has_function_privilege('service_role', 'public.bonificador_carta_v1(text)', 'EXECUTE')
     or has_function_privilege('anon', 'public.bonificador_carta_v1(text)', 'EXECUTE')
     or has_function_privilege('authenticated', 'public.bonificador_carta_v1(text)', 'EXECUTE') then
    raise exception 'readback: privilegios incorretos em bonificador_carta_v1';
  end if;

  if not has_function_privilege('service_role', 'public.bonificador_pares_v1(integer,integer)', 'EXECUTE')
     or has_function_privilege('anon', 'public.bonificador_pares_v1(integer,integer)', 'EXECUTE')
     or has_function_privilege('authenticated', 'public.bonificador_pares_v1(integer,integer)', 'EXECUTE') then
    raise exception 'readback: privilegios incorretos em bonificador_pares_v1';
  end if;
end
$readback$;

commit;
