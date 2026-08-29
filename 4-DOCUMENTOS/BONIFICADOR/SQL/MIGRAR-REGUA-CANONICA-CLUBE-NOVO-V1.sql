-- Migração operacional do Bonificador: nenhuma leitura de `clube.*` em runtime.
-- Executar somente depois do ensaio integral com ROLLBACK e do preflight abaixo.
begin;

do $preflight$
declare
  regra_md5 text;
  carta_md5 text;
  pares_md5 text;
  n integer;
begin
  select md5(pg_get_functiondef('public.bonificador_regua_v1()'::regprocedure)) into regra_md5;
  select md5(pg_get_functiondef('public.bonificador_carta_v1(text)'::regprocedure)) into carta_md5;
  select md5(pg_get_functiondef('public.bonificador_pares_v1(integer,integer)'::regprocedure)) into pares_md5;
  if regra_md5 <> '7417e765fc8b236b16f3b73e2e622300'
     or carta_md5 <> '3717c3aa73d87ee3ff9e4fb659b05363'
     or pares_md5 <> '3b4b8ca05ac16d99a9cfbe424c29ab7b' then
    raise exception 'preflight: contrato alterado desde o snapshot (%, %, %)', regra_md5, carta_md5, pares_md5;
  end if;
  select count(*) into n from clube.bonus_parametro;
  if n <> 14 then raise exception 'preflight: bonus_parametro esperado 14, obtido %', n; end if;
  select count(*) into n from clube.molde_corpo;
  if n <> 384 then raise exception 'preflight: molde_corpo esperado 384, obtido %', n; end if;
  select count(*) into n from clube.estilo_regra;
  if n <> 90 then raise exception 'preflight: estilo_regra esperado 90, obtido %', n; end if;
  select count(*) into n from clube.posicao_slot;
  if n <> 13 then raise exception 'preflight: posicao_slot esperado 13, obtido %', n; end if;
  select count(*) into n from clube_novo.corpo_ordem where usado_pelo_motor and pode_rodar;
  if n <> 12 then raise exception 'preflight: corpo_ordem novo esperado 12, obtido %', n; end if;
  select count(*) into n from clube_novo.funcao_sistema where ativa and pode_rodar;
  if n <> 19 then raise exception 'preflight: funcao_sistema nova esperada 19, obtido %', n; end if;
end
$preflight$;

-- `pos` é a chave física da medida consumida pelo molde.
alter table clube_novo.corpo_ordem
  add constraint corpo_ordem_pos_key unique (pos);

create table clube_novo.bonificador_parametro (
  codigo text primary key check (btrim(codigo) <> ''),
  valor numeric not null,
  procedencia text not null check (procedencia in ('snapshot_regra_sistema','catalogo_fisico_pe')),
  criado_em timestamptz not null default now()
);

create table clube_novo.bonificador_molde_corpo (
  funcao_id bigint not null references clube_novo.funcao_sistema(id) on delete restrict,
  corpo_pos integer not null references clube_novo.corpo_ordem(pos) on delete restrict,
  direcao integer not null check (direcao in (-1,0,1)),
  peso numeric not null,
  corte1 numeric,
  corte2 numeric,
  corte3 numeric,
  corte4 numeric,
  primary key (funcao_id, corpo_pos)
);

create table clube_novo.bonificador_posicao_slot (
  posicao_id integer primary key references clube_novo.posicao_jogo(id) on delete restrict,
  slot text not null check (slot in ('ofensivo','defensivo'))
);

create table clube_novo.bonificador_regra_playstyle (
  id bigint generated always as identity primary key,
  playstyle_id integer not null references clube_novo.playstyle(id_jogo) on delete restrict,
  posicao_id integer not null references clube_novo.posicao_jogo(id) on delete restrict,
  funcao_id bigint references clube_novo.funcao_sistema(id) on delete restrict,
  da_bonus boolean not null
);
create unique index bonificador_regra_playstyle_sem_funcao_uidx
  on clube_novo.bonificador_regra_playstyle(playstyle_id, posicao_id)
  where funcao_id is null;
create unique index bonificador_regra_playstyle_com_funcao_uidx
  on clube_novo.bonificador_regra_playstyle(playstyle_id, posicao_id, funcao_id)
  where funcao_id is not null;

create table clube_novo.bonificador_par (
  card_id text not null references clube_novo.carta_jogo(card_id) on delete restrict,
  funcao_id bigint not null references clube_novo.funcao_sistema(id) on delete restrict,
  primary key (card_id, funcao_id)
);

create table clube_novo.bonificador_migracao_snapshot_v1 (
  chave text primary key,
  valor jsonb,
  definicao text,
  md5 text,
  capturado_em timestamptz not null default now()
);

alter table clube_novo.bonificador_parametro enable row level security;
alter table clube_novo.bonificador_molde_corpo enable row level security;
alter table clube_novo.bonificador_posicao_slot enable row level security;
alter table clube_novo.bonificador_regra_playstyle enable row level security;
alter table clube_novo.bonificador_par enable row level security;
alter table clube_novo.bonificador_migracao_snapshot_v1 enable row level security;
revoke all on table clube_novo.bonificador_parametro, clube_novo.bonificador_molde_corpo,
  clube_novo.bonificador_posicao_slot, clube_novo.bonificador_regra_playstyle,
  clube_novo.bonificador_par, clube_novo.bonificador_migracao_snapshot_v1
  from public, anon, authenticated;

insert into clube_novo.bonificador_migracao_snapshot_v1(chave, definicao, md5)
select 'funcao:' || p.proname || ':' || pg_get_function_identity_arguments(p.oid),
       pg_get_functiondef(p.oid), md5(pg_get_functiondef(p.oid))
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public'
  and p.proname in ('bonificador_regua_v1','bonificador_carta_v1','bonificador_pares_v1');
insert into clube_novo.bonificador_migracao_snapshot_v1(chave, valor, md5)
select 'payload:regua', public.bonificador_regua_v1(), md5(public.bonificador_regua_v1()::text)
union all
select 'payload:casillas', public.bonificador_carta_v1('88045755827028'),
       md5(public.bonificador_carta_v1('88045755827028')::text);

-- Snapshot fiel: pé vem do catálogo físico; os cinco parâmetros restantes são
-- regras do sistema congeladas sem alteração de valor.
insert into clube_novo.bonificador_parametro(codigo, valor, procedencia)
select bp.chave,
       coalesce(nf.valor_bonus, bp.valor),
       case when nf.valor_bonus is null then 'snapshot_regra_sistema' else 'catalogo_fisico_pe' end
from clube.bonus_parametro bp
left join lateral (
  select p.valor_bonus
  from clube_novo.pe p
  where p.pode_rodar and p.valor_bonus is not null and (
    (bp.chave='pe_ruim_teto' and p.campo='pe_ruim_teto') or
    (bp.chave='pe_ruim_frequencia_' || p.valor and p.campo='pe_ruim_uso') or
    (bp.chave='pe_ruim_precisao_' || p.valor and p.campo='pe_ruim_precisao')
  )
) nf on true;

insert into clube_novo.bonificador_molde_corpo
  (funcao_id, corpo_pos, direcao, peso, corte1, corte2, corte3, corte4)
select fs.id, co.pos, mc.direcao, mc.peso, mc.corte1, mc.corte2, mc.corte3, mc.corte4
from clube.molde_corpo mc
join clube_novo.funcao_sistema fs on fs.nome_legado=mc.funcao and fs.ativa and fs.pode_rodar
join clube.corpo_ordem lo on lo.nosso=mc.medida
join clube_novo.corpo_ordem co on co.codigo=lo.codigo and co.usado_pelo_motor and co.pode_rodar;

insert into clube_novo.bonificador_posicao_slot(posicao_id, slot)
select pj.id, ps.slot
from clube.posicao_slot ps
join clube_novo.posicao_jogo pj on pj.codigo_antigo=ps.posicao and pj.pode_rodar;

with style_names as (
  select distinct estilo from clube.estilo_regra
), legacy_candidates as (
  select sn.estilo, eo.id/4 as indice from style_names sn join clube.estilo_jogo eo on eo.nome=sn.estilo
  union
  select sn.estilo, ed.id as indice from style_names sn join clube.estilo_defensivo ed on ed.nome=sn.estilo
), legacy_unique as (
  select estilo, min(indice) as indice from legacy_candidates group by estilo having count(distinct indice)=1
), canonical_override(estilo, playstyle_id) as (
  values ('Goleiro adiantado'::text, 291::integer)
), mapped as (
  select er.posicao, er.funcao_codigo, er.da_bonus,
         coalesce(ov.playstyle_id, p.id_jogo) as playstyle_id
  from clube.estilo_regra er
  left join canonical_override ov on ov.estilo=er.estilo
  left join legacy_unique lu on lu.estilo=er.estilo
  left join clube_novo.playstyle p on p.indice=lu.indice and p.pode_rodar
)
insert into clube_novo.bonificador_regra_playstyle(playstyle_id, posicao_id, funcao_id, da_bonus)
select m.playstyle_id, pj.id, fs.id, m.da_bonus
from mapped m
join clube_novo.playstyle p on p.id_jogo=m.playstyle_id and p.pode_rodar
join clube_novo.posicao_jogo pj on pj.codigo_antigo=m.posicao and pj.pode_rodar
left join clube_novo.funcao_sistema fs on fs.codigo_legado=m.funcao_codigo and fs.pode_rodar;

-- Projeção separada do universo de pares. No estado atual `clube.build` está vazio;
-- o runtime passa a ler somente esta relação canônica, nunca a tabela do Otimizador.
insert into clube_novo.bonificador_par(card_id, funcao_id)
select b.card_id, fs.id
from clube.build b
join clube_novo.carta_jogo c on c.card_id=b.card_id
join clube_novo.funcao_sistema fs on fs.codigo_legado=b.funcao_codigo and fs.pode_rodar;

do $seed_check$
declare n integer;
begin
  select count(*) into n from clube_novo.bonificador_parametro;
  if n <> 14 then raise exception 'seed: parametros novos esperado 14, obtido %', n; end if;
  select count(*) into n from clube_novo.bonificador_molde_corpo;
  if n <> 228 then raise exception 'seed: moldes canonicos esperado 228, obtido %', n; end if;
  select count(*) into n from (
    select funcao_id from clube_novo.bonificador_molde_corpo group by funcao_id having count(*)<>12
  ) x;
  if n<>0 then raise exception 'seed: funcao canonica sem exatamente 12 moldes'; end if;
  select count(*) into n from clube_novo.bonificador_posicao_slot;
  if n <> 13 then raise exception 'seed: slots novos esperado 13, obtido %', n; end if;
  select count(*) into n from clube_novo.bonificador_regra_playstyle;
  if n <> 90 then raise exception 'seed: regras de playstyle esperado 90, obtido %', n; end if;
  select count(distinct playstyle_id) into n from clube_novo.bonificador_regra_playstyle;
  if n <> 31 then raise exception 'seed: playstyles de regra esperado 31, obtido %', n; end if;
  if not exists (select 1 from clube_novo.bonificador_regra_playstyle r join clube_novo.posicao_jogo p on p.id=r.posicao_id where r.playstyle_id=291 and p.codigo_antigo='GO' and r.da_bonus) then
    raise exception 'seed: referencia canonica de Goleiro adiantado/291 ausente';
  end if;
end
$seed_check$;

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
  select coalesce(jsonb_object_agg(x.codigo_legado, x.medidas),'{}'::jsonb) as valor
  from (
    select f.codigo_legado,
           jsonb_object_agg(co.nosso, jsonb_build_object(
             'idx', co.pos, 'direcao', m.direcao, 'peso', m.peso,
             'cortes', jsonb_build_array(m.corte1,m.corte2,m.corte3,m.corte4)
           ) order by co.pos) as medidas
    from clube_novo.bonificador_molde_corpo m
    join funcoes f on f.id=m.funcao_id and f.pode_rodar
    join clube_novo.corpo_ordem co on co.pos=m.corpo_pos and co.usado_pelo_motor and co.pode_rodar
    group by f.codigo_legado
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
    select r.playstyle_id, jsonb_object_agg(r.posicao_id::text,f.codigo_legado) as mapa
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
    'estilo_regra','clube_novo.bonificador_regra_playstyle.playstyle_id',
    'corpo_ordem','clube_novo.corpo_ordem.pos',
    'funcao','clube_novo.funcao_sistema.id',
    'playstyle','clube_novo.playstyle.id_jogo'
  ),
  'cardinalidades',jsonb_build_object('parametros',14,'moldes',228,'funcoes',19,'posicao_slots',13,'regras_playstyle',90,'playstyles_regra',31)
)
from g cross join parametros pa cross join molde mo cross join ponte_funcao pf cross join ordem_corpo oc cross join casa ca cross join liga li cross join slots sl;
$function$;

-- A carta já vem exclusivamente do modelo novo; remove somente o gate histórico 291.
do $carta_sem_291$
declare d text;
begin
  select pg_get_functiondef('public.bonificador_carta_v1(text)'::regprocedure) into d;
  if position(E'           case when b.slot1_id_jogo = 291 or b.slot2_id_jogo = 291\n             then \'playstyle 291: regra Goleiro adiantado aguarda decisao\' end' in d)=0 then
    raise exception 'migração: gate 291 esperado não encontrado em bonificador_carta_v1';
  end if;
  d := replace(d,
    E'           case when b.ia_bloqueadas <> 0 then \'estilo de IA: relacao sem catalogo apto\' end,\n           case when b.slot1_id_jogo = 291 or b.slot2_id_jogo = 291\n             then \'playstyle 291: regra Goleiro adiantado aguarda decisao\' end',
    E'           case when b.ia_bloqueadas <> 0 then \'estilo de IA: relacao sem catalogo apto\' end');
  execute d;
end
$carta_sem_291$;

create or replace function public.bonificador_pares_v1(p_limit integer default 1000, p_offset integer default 0)
returns table(card_id text, funcao_codigo text)
language sql stable security definer set search_path = '' as $function$
  select p.card_id, f.codigo_legado
  from clube_novo.bonificador_par p
  join clube_novo.funcao_sistema f on f.id=p.funcao_id and f.pode_rodar
  order by p.card_id, f.codigo_legado
  limit least(greatest(coalesce(p_limit,1000),1),5000)
  offset greatest(coalesce(p_offset,0),0)
$function$;

revoke all on function public.bonificador_regua_v1() from public, anon, authenticated;
grant execute on function public.bonificador_regua_v1() to service_role;
revoke all on function public.bonificador_carta_v1(text) from public, anon, authenticated;
grant execute on function public.bonificador_carta_v1(text) to service_role;
revoke all on function public.bonificador_pares_v1(integer,integer) from public, anon, authenticated;
grant execute on function public.bonificador_pares_v1(integer,integer) to service_role;

do $readback$
declare r jsonb := public.bonificador_regua_v1(); c jsonb := public.bonificador_carta_v1('88045755827028'); n integer;
begin
  if coalesce((r->>'pode_rodar')::boolean,false) is not true or r->'falta_o_que' <> '[]'::jsonb
     or (r#>>'{cardinalidades,regras_playstyle}')::integer<>90
     or (r#>>'{cardinalidades,playstyles_regra}')::integer<>31
     or r->'estilos_bloqueados' <> '[]'::jsonb then
    raise exception 'readback: régua canônica não ficou apta: %',r;
  end if;
  if coalesce((c->>'pode_rodar')::boolean,false) is not true
     or (c->>'slot1_id_jogo')::integer<>291 or (c->>'slot2_id_jogo')::integer<>336
     or c->'falta_o_que' <> '[]'::jsonb then
    raise exception 'readback: Casillas não ficou apto: %',c;
  end if;
  select count(*) into n from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
    where ns.nspname='public' and p.proname in ('bonificador_regua_v1','bonificador_carta_v1','bonificador_pares_v1')
      and pg_get_functiondef(p.oid) ~ '(^|[^a-z_])clube\\.';
  if n<>0 then raise exception 'readback: ainda há consulta clube.* em contrato operacional'; end if;
  if not has_function_privilege('service_role','public.bonificador_regua_v1()','execute')
     or has_function_privilege('public','public.bonificador_regua_v1()','execute')
     or has_function_privilege('anon','public.bonificador_regua_v1()','execute')
     or has_function_privilege('authenticated','public.bonificador_regua_v1()','execute') then
    raise exception 'readback: grants de régua incorretos';
  end if;
end
$readback$;

commit;
