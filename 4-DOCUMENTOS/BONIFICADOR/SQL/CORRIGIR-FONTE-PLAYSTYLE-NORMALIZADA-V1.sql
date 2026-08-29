begin;

create or replace function public.bonificador_carta_v1(p_card_id text)
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
base as (
  select c.card_id, c.nome, c.posicao as posicao_raw,
         c.pe_ruim_uso, c.pe_ruim_precisao,
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
         b.valores as corpo, b.n as corpo_n, b.bloqueadas as corpo_bloqueadas,
         a.bits as estilos_ia, a.n as estilos_ia_n, a.bloqueadas as ia_bloqueadas
  from (select 1 as seed) s
  left join c on true
  cross join body b
  cross join ai a
  cross join principal_position pp
  cross join playstyle_slots ps
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
    'pe', 'clube_novo.carta_jogo -> pe(campo,valor)',
    'posicao', 'clube_novo.carta_posicao_principal_jogo.posicao_id -> posicao_jogo.id',
    'slot1', 'clube_novo.carta_playstyle_jogo(slot_fisico=1).playstyle_id -> playstyle.id_jogo',
    'slot2', 'clube_novo.carta_playstyle_jogo(slot_fisico=2).playstyle_id -> playstyle.id_jogo',
    'ia', 'clube_novo.carta_estilo_ia_jogo.bit_estilo_ia'
  )
)
from gated g;
$function$;

revoke all on function public.bonificador_carta_v1(text) from public, anon, authenticated;
grant execute on function public.bonificador_carta_v1(text) to service_role;

do $readback$
declare
  ok jsonb := public.bonificador_carta_v1('176844');
  blocked jsonb := public.bonificador_carta_v1('88045755827028');
begin
  if coalesce((ok ->> 'pode_rodar')::boolean, false) is not true
     or (ok ->> 'posicao_relacao_cardinalidade')::integer <> 1
     or (ok ->> 'playstyle_relacao_cardinalidade')::integer <> 2 then
    raise exception 'readback: relacoes normalizadas da carta controle nao aptas: %', ok;
  end if;
  if coalesce((blocked ->> 'pode_rodar')::boolean, true) is not false then
    raise exception 'readback: playstyle 291 deixou de bloquear';
  end if;
end
$readback$;

commit;

