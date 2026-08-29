-- Troca somente chaves operacionais de função: texto técnico -> funcao_sistema.id.
-- Fórmula, pesos, cortes, ordem e conteúdo dos moldes não são alterados.
begin;

create table if not exists clube_novo.bonificador_migracao_snapshot_v2 (
  chave text primary key,
  definicao text not null,
  md5 text not null,
  capturado_em timestamptz not null default now()
);
alter table clube_novo.bonificador_migracao_snapshot_v2 enable row level security;
revoke all on table clube_novo.bonificador_migracao_snapshot_v2 from public, anon, authenticated;

insert into clube_novo.bonificador_migracao_snapshot_v2(chave, definicao, md5)
select 'funcao:' || p.proname || ':' || pg_get_function_identity_arguments(p.oid),
       pg_get_functiondef(p.oid), md5(pg_get_functiondef(p.oid))
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname in ('bonificador_regua_v1','bonificador_pares_v1')
on conflict (chave) do nothing;

do $preflight$
declare r jsonb := public.bonificador_regua_v1(); n integer;
begin
  if coalesce((r->>'pode_rodar')::boolean,false) is not true
     or r->'falta_o_que' <> '[]'::jsonb then
    raise exception 'preflight: régua atual não está apta';
  end if;
  if not (r->'molde_corpo' ? 'centroavante_fixo')
     or not (r->'casa' ? '336') then
    raise exception 'preflight: contrato textual esperado não encontrado';
  end if;
  select count(*) into n from clube_novo.bonificador_molde_corpo;
  if n <> 228 then raise exception 'preflight: moldes esperados 228, obtido %', n; end if;
end
$preflight$;

create or replace function public.bonificador_regua_v1()
returns jsonb language sql stable security definer set search_path = '' as $function$
with
parametros as (
  select coalesce(jsonb_object_agg(codigo, valor),'{}'::jsonb) as valor
  from clube_novo.bonificador_parametro
),
funcoes as (
  select id, codigo_legado, rotulo, pode_rodar
  from clube_novo.funcao_sistema where ativa
),
molde as (
  select coalesce(jsonb_object_agg(x.funcao_id::text, x.medidas),'{}'::jsonb) as valor
  from (
    select f.id as funcao_id,
           jsonb_object_agg(co.nosso, jsonb_build_object(
             'idx', co.pos, 'direcao', m.direcao, 'peso', m.peso,
             'cortes', jsonb_build_array(m.corte1,m.corte2,m.corte3,m.corte4)
           ) order by co.pos) as medidas
    from clube_novo.bonificador_molde_corpo m
    join funcoes f on f.id=m.funcao_id and f.pode_rodar
    join clube_novo.corpo_ordem co on co.pos=m.corpo_pos and co.usado_pelo_motor and co.pode_rodar
    group by f.id
  ) x
),
ponte_funcao as (
  select coalesce(jsonb_object_agg(codigo_legado,jsonb_build_object('id',id,'rotulo',rotulo,'pode_rodar',pode_rodar) order by id),'{}'::jsonb) as valor
  from funcoes
),
ordem_corpo as (
  select coalesce(jsonb_object_agg(pos::text,jsonb_build_object('codigo',codigo,'nosso',nosso,'pode_rodar',pode_rodar) order by pos),'{}'::jsonb) as valor
  from clube_novo.corpo_ordem where usado_pelo_motor
),
casa as (
  select coalesce(jsonb_object_agg(x.playstyle_id::text,x.mapa),'{}'::jsonb) as valor
  from (
    select r.playstyle_id, jsonb_object_agg(r.posicao_id::text,f.id) as mapa
    from clube_novo.bonificador_regra_playstyle r
    join funcoes f on f.id=r.funcao_id and f.pode_rodar
    group by r.playstyle_id
  ) x
),
liga as (
  select coalesce(jsonb_object_agg(x.playstyle_id::text,x.posicoes),'{}'::jsonb) as valor
  from (
    select r.playstyle_id, jsonb_agg(distinct r.posicao_id order by r.posicao_id) as posicoes
    from clube_novo.bonificador_regra_playstyle r where r.da_bonus group by r.playstyle_id
  ) x
),
slots as (
  select coalesce(jsonb_object_agg(posicao_id::text,slot),'{}'::jsonb) as valor from clube_novo.bonificador_posicao_slot
),
g as (
  select array_remove(array[
    case when (select count(*) from clube_novo.bonificador_parametro)<>14 then 'bonificador_parametro: cardinalidade diferente de 14' end,
    case when (select count(*) from clube_novo.bonificador_molde_corpo)<>228 then 'bonificador_molde_corpo: cardinalidade diferente de 228' end,
    case when (select count(*) from funcoes where pode_rodar)<>19 then 'funcao_sistema: cardinalidade apta diferente de 19' end,
    case when (select count(*) from molde where valor='{}'::jsonb)<>0 then 'bonificador_molde_corpo: molde vazio' end,
    case when (select count(*) from clube_novo.bonificador_posicao_slot)<>13 then 'bonificador_posicao_slot: cardinalidade diferente de 13' end,
    case when (select count(*) from clube_novo.bonificador_regra_playstyle)<>90 then 'bonificador_regra_playstyle: cardinalidade diferente de 90' end,
    case when (select count(distinct playstyle_id) from clube_novo.bonificador_regra_playstyle)<>31 then 'bonificador_regra_playstyle: playstyles diferentes de 31' end,
    case when not exists(select 1 from clube_novo.bonificador_regra_playstyle r join clube_novo.posicao_jogo p on p.id=r.posicao_id where r.playstyle_id=291 and p.codigo_antigo='GO' and r.da_bonus) then 'playstyle 291: referencia canonica ausente' end
  ]::text[],null) as faltas
)
select jsonb_build_object(
  'contrato','bonificador-regua-v1', 'pode_rodar',cardinality(g.faltas)=0,'falta_o_que',to_jsonb(g.faltas),
  'parametro',pa.valor,'molde_corpo',mo.valor,'funcao_molde',pf.valor,'corpo_ordem',oc.valor,
  'casa',ca.valor,'liga',li.valor,'posicao_slot',sl.valor,
  'estilos_bloqueados','[]'::jsonb,
  'proveniencia',jsonb_build_object(
    'parametro','clube_novo.bonificador_parametro',
    'molde_corpo','clube_novo.bonificador_molde_corpo(funcao_id,corpo_pos)',
    'posicao_slot','clube_novo.bonificador_posicao_slot.posicao_id',
    'estilo_regra','clube_novo.bonificador_regra_playstyle(playstyle_id,posicao_id,funcao_id)',
    'corpo_ordem','clube_novo.corpo_ordem.pos',
    'funcao','clube_novo.funcao_sistema.id',
    'playstyle','clube_novo.playstyle.id_jogo'
  ),
  'cardinalidades',jsonb_build_object('parametros',14,'moldes',228,'funcoes',19,'posicao_slots',13,'regras_playstyle',90,'playstyles_regra',31)
)
from g cross join parametros pa cross join molde mo cross join ponte_funcao pf cross join ordem_corpo oc cross join casa ca cross join liga li cross join slots sl;
$function$;

drop function public.bonificador_pares_v1(integer,integer);
create function public.bonificador_pares_v1(p_limit integer default 1000, p_offset integer default 0)
returns table(card_id text, funcao_id bigint, funcao_codigo text)
language sql stable security definer set search_path = '' as $function$
  select p.card_id, p.funcao_id, f.codigo_legado
  from clube_novo.bonificador_par p
  join clube_novo.funcao_sistema f on f.id=p.funcao_id and f.pode_rodar
  order by p.card_id, p.funcao_id
  limit least(greatest(coalesce(p_limit,1000),1),5000)
  offset greatest(coalesce(p_offset,0),0)
$function$;

revoke all on function public.bonificador_regua_v1() from public, anon, authenticated;
grant execute on function public.bonificador_regua_v1() to service_role;
revoke all on function public.bonificador_pares_v1(integer,integer) from public, anon, authenticated;
grant execute on function public.bonificador_pares_v1(integer,integer) to service_role;

do $readback$
declare r jsonb := public.bonificador_regua_v1(); n integer;
begin
  if coalesce((r->>'pode_rodar')::boolean,false) is not true
     or not (r->'molde_corpo' ? '1')
     or (r->'molde_corpo' ? 'centroavante_fixo')
     or (r#>>'{casa,336,0}')::bigint <> 5
     or r->'falta_o_que' <> '[]'::jsonb then
    raise exception 'readback: IDs de função não publicados corretamente: %', r;
  end if;
  select count(*) into n from public.bonificador_pares_v1(1,0);
  if n <> 0 then raise exception 'readback: projeção de pares deveria continuar vazia'; end if;
end
$readback$;
commit;
