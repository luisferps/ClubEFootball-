begin transaction read only;

-- 1. Objetos, definição, segurança e nenhuma exposição para UI.
select n.nspname as schema_name,
       p.proname,
       pg_get_function_identity_arguments(p.oid) as args,
       p.prosecdef as security_definer,
       p.provolatile as volatility,
       p.proconfig,
       p.proacl,
       md5(pg_get_functiondef(p.oid)) as definition_md5,
       has_function_privilege('service_role', p.oid, 'EXECUTE') as service_role_executes,
       has_function_privilege('anon', p.oid, 'EXECUTE') as anon_executes,
       has_function_privilege('authenticated', p.oid, 'EXECUTE') as authenticated_executes
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public'
  and p.proname in (
    'bonificador_regua_v1',
    'bonificador_carta_v1',
    'bonificador_pares_v1'
  )
order by p.proname;

-- 2. Readback sem escrita: receita, uma carta com divergência física e o gate 291.
select public.bonificador_regua_v1() as regua;

select x.card_id, public.bonificador_carta_v1(x.card_id) as contrato
from (values
  ('176844'::text),            -- pé/IA divergentes: deve usar a fonte nova e rodar
  ('155498'::text),            -- corpo/IA divergentes: deve usar a fonte nova e rodar
  ('160233'::text),            -- posição/slot 1 divergentes: deve usar IDs novos e rodar
  ('182363'::text),            -- posição/slot 1 divergentes: deve usar IDs novos e rodar
  ('88045755827028'::text),    -- playstyle 291: deve bloquear
  ('card-inexistente'::text)   -- ausência: deve bloquear, sem fallback
) x(card_id);

-- 3. Cardinalidades e gates do modelo novo consumido.
select jsonb_build_object(
  'carta_jogo', (select count(*) from clube_novo.carta_jogo),
  'carta_corpo_jogo', (select count(*) from clube_novo.carta_corpo_jogo),
  'corpo_cards', (select count(distinct card_id) from clube_novo.carta_corpo_jogo),
  'carta_atributo_jogo', (select count(*) from clube_novo.carta_atributo_jogo),
  'carta_habilidade_jogo', (select count(*) from clube_novo.carta_habilidade_jogo),
  'carta_posicao_jogo', (select count(*) from clube_novo.carta_posicao_jogo),
  'carta_impeto_jogo', (select count(*) from clube_novo.carta_impeto_jogo),
  'carta_pe_jogo', (select count(*) from clube_novo.carta_pe_jogo),
  'carta_posicao_principal_jogo', (select count(*) from clube_novo.carta_posicao_principal_jogo),
  'carta_playstyle_jogo', (select count(*) from clube_novo.carta_playstyle_jogo),
  'corpo_cards_fora_de_12', (
    select count(*) from (
      select cc.card_id
      from clube_novo.carta_corpo_jogo cc
      join clube_novo.corpo_ordem co on co.codigo = cc.codigo_corpo
      where co.usado_pelo_motor
      group by cc.card_id
      having count(*) <> 12
    ) q
  ),
  'carta_estilo_ia_jogo', (select count(*) from clube_novo.carta_estilo_ia_jogo),
  'corpo_ordem_gate', (
    select jsonb_build_object('total', count(*), 'aptas', count(*) filter (where pode_rodar))
    from clube_novo.corpo_ordem
  ),
  'pe_gate', (
    select jsonb_build_object('total', count(*), 'aptas', count(*) filter (where pode_rodar))
    from clube_novo.pe
  ),
  'posicao_gate', (
    select jsonb_build_object('total', count(*), 'aptas', count(*) filter (where pode_rodar))
    from clube_novo.posicao_jogo
  ),
  'playstyle_gate', (
    select jsonb_build_object('total', count(*), 'aptas', count(*) filter (where pode_rodar))
    from clube_novo.playstyle
  ),
  'ia_gate', (
    select jsonb_build_object('total', count(*), 'aptas', count(*) filter (where pode_rodar))
    from clube_novo.estilo_ia
  ),
  'build_atual', (select count(*) from clube.build),
  'build_referencia', (select count(*) from clube.build_arquivo_2608)
) as cardinalidades;

-- 4. Fingerprints particionados, sem depender da ordem física das tabelas.
with
body_rows as (
  select cc.card_id, co.pos, cc.valor
  from clube_novo.carta_corpo_jogo cc
  join clube_novo.corpo_ordem co on co.codigo = cc.codigo_corpo
  where co.usado_pelo_motor
),
body_parts as (
  select ((hashtextextended(card_id, 0) % 64) + 64) % 64 as part,
         md5(string_agg(card_id || '|' || pos || '|' || valor,
                        E'\n' order by card_id, pos)) as fp
  from body_rows
  group by 1
),
normalized_scalar_rows as (
  select c.card_id,
         max(pe.valor) filter (where pe.campo = 'pe_ruim_uso') as pe_ruim_uso,
         max(pe.valor) filter (where pe.campo = 'pe_ruim_precisao') as pe_ruim_precisao,
         pp.posicao_id,
         max(ps.playstyle_id) filter (where ps.slot_fisico = 1) as slot1_id_jogo,
         max(ps.playstyle_id) filter (where ps.slot_fisico = 2) as slot2_id_jogo
  from clube_novo.carta_jogo c
  join clube_novo.carta_pe_jogo pe using (card_id)
  join clube_novo.carta_posicao_principal_jogo pp using (card_id)
  join clube_novo.carta_playstyle_jogo ps using (card_id)
  group by c.card_id, pp.posicao_id
),
scalar_parts as (
  select ((hashtextextended(card_id, 0) % 64) + 64) % 64 as part,
         md5(string_agg(
           card_id || '|' || coalesce(pe_ruim_uso::text, '∅') || '|' ||
           coalesce(pe_ruim_precisao::text, '∅') || '|' ||
           coalesce(posicao_id::text, '∅') || '|' ||
           coalesce(slot1_id_jogo::text, '∅') || '|' ||
           coalesce(slot2_id_jogo::text, '∅'),
           E'\n' order by card_id
         )) as fp
  from normalized_scalar_rows
  group by 1
),
ai_parts as (
  select ((hashtextextended(card_id, 0) % 64) + 64) % 64 as part,
         md5(string_agg(card_id || '|' || bit_estilo_ia,
                        E'\n' order by card_id, bit_estilo_ia)) as fp
  from clube_novo.carta_estilo_ia_jogo
  group by 1
)
select
  (select md5(string_agg(part || ':' || fp, E'\n' order by part)) from body_parts)
    as corpo_novo_integral,
  (select md5(string_agg(part || ':' || fp, E'\n' order by part)) from scalar_parts)
    as pe_posicao_slots_novo_integral,
  (select md5(string_agg(part || ':' || fp, E'\n' order by part)) from ai_parts)
    as ia_nova_integral;

-- 5. Divergências por card_id e campo. A lista completa é intencional.
with
new_foot as (
  select card_id,
         max(valor) filter (where campo = 'pe_ruim_uso') as uso,
         max(valor) filter (where campo = 'pe_ruim_precisao') as precisao
  from clube_novo.carta_pe_jogo
  group by card_id
),
new_position as (
  select cp.card_id, cp.posicao_id, pj.codigo_en
  from clube_novo.carta_posicao_principal_jogo cp
  join clube_novo.posicao_jogo pj on pj.id = cp.posicao_id
),
new_playstyle as (
  select card_id,
         max(valor_raw) filter (where slot_fisico = 1) as slot1_raw,
         max(valor_raw) filter (where slot_fisico = 2) as slot2_raw
  from clube_novo.carta_playstyle_jogo
  group by card_id
),
overlap as (
  select o.card_id,
         o.corpo as old_corpo,
         o.pe_ruim_uso as old_uso, nf.uso as new_uso,
         o.pe_ruim_precisao as old_prec, nf.precisao as new_prec,
         o.posicao as old_pos, np.codigo_en as new_pos,
         o.slot_ofensivo_id as old_s1, ns.slot1_raw as new_s1,
         o.slot_defensivo_id as old_s2, ns.slot2_raw as new_s2,
         jsonb_array_length(coalesce(o.estilos_ia, '[]'::jsonb)) as old_ia_n
  from clube.carta_jogo o
  join clube_novo.carta_jogo n using (card_id)
  join new_foot nf using (card_id)
  join new_position np using (card_id)
  join new_playstyle ns using (card_id)
),
old_body as (
  select o.card_id, (e.ord - 1)::integer as pos,
         (e.value #>> '{}')::integer as valor
  from overlap o
  cross join lateral jsonb_array_elements(coalesce(o.old_corpo, '[]'::jsonb))
    with ordinality e(value, ord)
),
new_body as (
  select cc.card_id, co.pos, co.codigo, cc.valor
  from clube_novo.carta_corpo_jogo cc
  join clube_novo.corpo_ordem co on co.codigo = cc.codigo_corpo
  where co.usado_pelo_motor
),
new_ai as (
  select card_id, count(*)::integer as n
  from clube_novo.carta_estilo_ia_jogo
  group by card_id
),
diffs as (
  select coalesce(ob.card_id, nb.card_id) as card_id,
         'corpo:' || coalesce(nb.codigo, 'pos=' || coalesce(ob.pos, nb.pos)) as campo,
         'clube.carta_jogo.corpo' as origem_antiga,
         ob.valor::text as valor_antigo,
         'clube_novo.carta_corpo_jogo' as origem_nova,
         nb.valor::text as valor_novo
  from old_body ob
  full join new_body nb using (card_id, pos)
  join overlap o on o.card_id = coalesce(ob.card_id, nb.card_id)
  where ob.valor is distinct from nb.valor

  union all

  select card_id, 'pe_ruim_uso', 'clube.carta_jogo.pe_ruim_uso', old_uso::text,
         'clube_novo.carta_pe_jogo(campo=pe_ruim_uso)', new_uso::text
  from overlap where old_uso is distinct from new_uso

  union all

  select card_id, 'pe_ruim_precisao', 'clube.carta_jogo.pe_ruim_precisao', old_prec::text,
         'clube_novo.carta_pe_jogo(campo=pe_ruim_precisao)', new_prec::text
  from overlap where old_prec is distinct from new_prec

  union all

  select card_id, 'posicao', 'clube.carta_jogo.posicao', old_pos,
         'clube_novo.carta_posicao_principal_jogo -> posicao_jogo.id', new_pos
  from overlap where old_pos is distinct from new_pos

  union all

  select card_id, 'slot1_raw', 'clube.carta_jogo.slot_ofensivo_id', old_s1::text,
         'clube_novo.carta_playstyle_jogo(slot=1) -> playstyle.id_jogo', new_s1::text
  from overlap where old_s1 is distinct from new_s1

  union all

  select card_id, 'slot2_raw', 'clube.carta_jogo.slot_defensivo_id', old_s2::text,
         'clube_novo.carta_playstyle_jogo(slot=2) -> playstyle.id_jogo', new_s2::text
  from overlap where old_s2 is distinct from new_s2

  union all

  select o.card_id, 'estilos_ia_cardinalidade', 'clube.carta_jogo.estilos_ia', o.old_ia_n::text,
         'clube_novo.carta_estilo_ia_jogo', coalesce(n.n, 0)::text
  from overlap o
  left join new_ai n using (card_id)
  where o.old_ia_n is distinct from coalesce(n.n, 0)
)
select * from diffs order by card_id, campo;

-- 6. Sombra da parcela estilo: referência independente por nomes/ids antigos
-- contra a mesma regra reindexada por IDs novos. O playstyle 291 é listado e bloqueado.
with
par as (
  select max(valor) filter (where chave = 'estilo_ativo')::numeric as pri,
         max(valor) filter (where chave = 'estilo_ativo_secundario')::numeric as sec
  from clube.bonus_parametro
),
style_candidates as (
  select er.estilo, eo.id / 4 as indice
  from (select distinct estilo from clube.estilo_regra) er
  join clube.estilo_jogo eo on eo.nome = er.estilo
  union
  select er.estilo, ed.id as indice
  from (select distinct estilo from clube.estilo_regra) er
  join clube.estilo_defensivo ed on ed.nome = er.estilo
),
style_unique as (
  select estilo, min(indice) as indice
  from style_candidates
  group by estilo
  having count(distinct indice) = 1
),
stable_rules as (
  select er.estilo, p.id_jogo, pj.id as pos_id, er.funcao_codigo, er.da_bonus
  from clube.estilo_regra er
  join style_unique su using (estilo)
  join clube_novo.playstyle p on p.indice = su.indice and p.pode_rodar
  join clube_novo.posicao_jogo pj
    on pj.codigo_antigo = er.posicao and pj.pode_rodar
),
pairs as (
  select b.card_id, b.funcao_codigo, b.b_estilo as snapshot_b_estilo,
         lp.codigo as old_pos, ps.slot,
         e1.nome as old_s1, e2.nome as old_s2,
         np.id as new_pos_id,
         p1.id_jogo as new_s1, p2.id_jogo as new_s2
  from clube.build_arquivo_2608 b
  join clube.carta_jogo o on o.card_id = b.card_id
  join clube_novo.carta_jogo n on n.card_id = b.card_id
  left join clube.posicao lp on lp.sigla_jogo = o.posicao
  left join clube.posicao_slot ps on ps.posicao = lp.codigo
  left join clube.estilo_jogo e1 on e1.id = o.slot_ofensivo_id
  left join clube.estilo_defensivo e2 on e2.id = o.slot_defensivo_id
  left join clube_novo.posicao_jogo np on np.codigo_en = n.posicao
  left join clube_novo.playstyle p1 on p1.indice = n.slot_ofensivo_id / 4
  left join clube_novo.playstyle p2 on p2.indice = n.slot_defensivo_id
),
oriented as (
  select p.*,
         case when slot = 'defensivo' then old_s2 else old_s1 end as old_dono,
         case when slot = 'defensivo' then old_s1 else old_s2 end as old_outro,
         case when slot = 'defensivo' then new_s2 else new_s1 end as new_dono,
         case when slot = 'defensivo' then new_s1 else new_s2 end as new_outro
  from pairs p
),
calc as (
  select o.*,
         round(least(
           case when exists (
             select 1 from clube.estilo_regra r
             where r.estilo = o.old_dono and r.posicao = o.old_pos
               and r.funcao_codigo = o.funcao_codigo
           ) then par.pri else 0 end
           + case when exists (
             select 1 from clube.estilo_regra r
             where r.estilo = o.old_outro and r.posicao = o.old_pos and r.da_bonus
           ) then par.sec else 0 end,
           par.pri + par.sec
         ), 4) as old_calc,
         round(least(
           case when exists (
             select 1 from stable_rules r
             where r.id_jogo = o.new_dono and r.pos_id = o.new_pos_id
               and r.funcao_codigo = o.funcao_codigo
           ) then par.pri else 0 end
           + case when exists (
             select 1 from stable_rules r
             where r.id_jogo = o.new_outro and r.pos_id = o.new_pos_id and r.da_bonus
           ) then par.sec else 0 end,
           par.pri + par.sec
         ), 4) as new_calc,
         (o.new_dono = 291 or o.new_outro = 291) as blocked_291
  from oriented o
  cross join par
)
select jsonb_build_object(
  'pares', count(*),
  'referencia_legada_vs_ids_novos', count(*) filter (where old_calc is distinct from new_calc),
  'snapshot_antigo_vs_regra_v7', count(*) filter (where snapshot_b_estilo is distinct from old_calc),
  'pares_bloqueados_291', count(*) filter (where blocked_291),
  'fingerprint_legado', md5(string_agg(
    card_id || '|' || funcao_codigo || '|' || old_calc,
    E'\n' order by card_id, funcao_codigo
  )),
  'fingerprint_novo', md5(string_agg(
    card_id || '|' || funcao_codigo || '|' || new_calc,
    E'\n' order by card_id, funcao_codigo
  ))
) as sombra_estilo
from calc;

rollback;
