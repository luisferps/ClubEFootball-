begin;

create table clube_novo.atributo_ordem_otimizador (
  codigo_atributo text primary key references clube_novo.atributo_jogo(codigo),
  indice_otimizador smallint not null unique check (indice_otimizador between 0 and 25),
  bit integer not null unique
);

insert into clube_novo.atributo_ordem_otimizador(codigo_atributo,indice_otimizador,bit)
values
 ('PB:498:6',0,498),('PB:396:6',1,396),('PB:492:6',2,492),('PB:550:6',3,550),
 ('PB:524:6',4,524),('PB:448:6',5,448),('PB:530:6',6,530),('PB:402:6',7,402),
 ('PB:368:6',8,368),('PB:428:6',9,428),('PB:434:6',10,434),('PB:486:6',11,486),
 ('PB:384:6',12,384),('PB:408:6',13,408),('PB:518:6',14,518),('PB:504:6',15,504),
 ('PB:480:6',16,480),('PB:390:6',17,390),('PB:454:6',18,454),('PB:544:6',19,544),
 ('PB:512:6',20,512),('PB:472:6',21,472),('PB:416:6',22,416),('PB:466:6',23,466),
 ('PB:460:6',24,460),('PB:422:6',25,422);

do $$
begin
  if (select count(*) from clube_novo.atributo_ordem_otimizador) <> 26
     or exists (
       select 1 from clube_novo.atributo_ordem_otimizador o
       join clube_novo.atributo_jogo a on a.codigo=o.codigo_atributo
       where a.bit<>o.bit or not a.pode_rodar
     ) then
    raise exception 'ordem física dos 26 atributos não fecha';
  end if;
  if (select count(*) from clube.molde where versao=(select max(versao) from clube.molde)) <> 494
     or exists (
       select 1 from clube.molde m
       left join clube_novo.funcao_sistema f on f.codigo_legado=m.funcao_codigo
       where m.versao=(select max(versao) from clube.molde)
         and (f.id is null or not f.pode_rodar)
     ) then
    raise exception 'molde não fecha 19 funções canônicas x 26 atributos';
  end if;
  if (select count(*) from clube_novo.habilidade_jogo where pode_rodar) <> 65
     or exists (
       select 1 from clube_novo.carta_habilidade_jogo c
       join clube_novo.habilidade_jogo h on h.skill_id=c.skill_id
       where not h.pode_rodar
     ) then
    raise exception 'habilidade usada não está apta';
  end if;
end $$;

alter table clube_novo.atributo_ordem_otimizador enable row level security;
create policy atributo_ordem_otimizador_service_read
on clube_novo.atributo_ordem_otimizador for select to service_role using (true);
revoke all on clube_novo.atributo_ordem_otimizador from public, anon, authenticated;
grant select on clube_novo.atributo_ordem_otimizador to service_role;

create or replace function public.otimizador_carta_v1(p_card_id text)
returns jsonb
language sql stable security definer
set search_path=''
as $$
with c as (
  select * from clube_novo.carta_jogo where card_id=p_card_id
)
select jsonb_build_object(
 'contrato','otimizador_entradas_v1',
 'card_id',c.card_id,
 'apresentacao',jsonb_build_object(
   'nome',c.nome,'posicao',pp.nome_pt,'nacionalidade',n.nome_pt_br,
   'clube',cl.nome_pt_br,'liga',lg.nome_pt_br,'tipo_carta',tc.nome_exibicao),
 'escalares',jsonb_build_object(
   'overall',c.overall,'altura',c.altura,'peso',c.peso,'idade',c.idade,
   'level_cap',c.level_cap,'orcamento',c.orcamento,'cap_estimado',c.cap_estimado,
   'grupo_id',c.grupo_id,'forma',c.forma),
 'dimensoes',jsonb_build_object(
   'nacionalidade_id',c.codigo_nacionalidade,'clube_id',c.codigo_clube,
   'liga_id',c.codigo_liga,'tipo_carta_id',c.tipo_carta_id,
   'tipo_fisico',c.codigo_tipo_carta_fisico,
   'subtipo_fisico',c.marcador_subtipo_tipo_carta,
   'tipo_provisorio',tc.tipo_provisorio),
 'posicao_principal_id',cpp.posicao_id,
 'atributos',a.dados,'corpo',co.dados,'posicoes',ps.dados,
 'habilidades',hs.dados,'estilos_ia',ia.dados,'pes',pe.dados,
 'playstyles',pl.dados,'impetos',im.dados,
 'cardinalidades',jsonb_build_object(
   'atributos',a.n,'corpo',co.n,'posicoes',ps.n,'posicao_principal',case when cpp.card_id is null then 0 else 1 end,
   'habilidades',hs.n,'estilos_ia',ia.n,'pes',pe.n,'playstyles',pl.n,'impetos',im.n),
 'gate',jsonb_build_object(
   'pode_rodar',cardinality(g.motivos)=0,
   'motivos',to_jsonb(g.motivos),
   'impetos_consumidor_ligado',false),
 'compatibilidade_legado',jsonb_build_object(
   'overall',c.overall,'posicao',pp.codigo_pt,'atributos',a.valores,
   'altura',c.altura,'peso',c.peso,'idade',c.idade,'pe',pe.nome_dominante,
   'pe_ruim_uso',pe.uso,'pe_ruim_precisao',pe.precisao,
   'resistencia_lesao',c.resistencia_lesao,'forma',c.forma,'corpo',co.valores,
   'level_cap',c.level_cap,'orcamento',c.orcamento,'cap_estimado',c.cap_estimado,
   'habilidades_bits',hs.bits,'aptidoes',ps.compat,
   'slot1_id',pl.raw1,'slot2_id',pl.raw2,'vaga_s1',c.vaga_s1,'vaga_s2',c.vaga_s2,
   'box',c.box,'tipo',c.tipo)
)
from c
left join clube_novo.carta_posicao_principal_jogo cpp on cpp.card_id=c.card_id
left join clube_novo.posicao_jogo pp on pp.id=cpp.posicao_id
left join clube_novo.nacionalidade_jogo n on n.codigo_jogo=c.codigo_nacionalidade
left join clube_novo.clube_jogo cl on cl.codigo_jogo=c.codigo_clube
left join clube_novo.liga_jogo lg on lg.codigo_jogo=c.codigo_liga
left join clube_novo.tipo_carta_jogo tc on tc.tipo_carta_id=c.tipo_carta_id
cross join lateral (
 select coalesce(jsonb_agg(jsonb_build_object(
          'indice_otimizador',o.indice_otimizador,'codigo',aj.codigo,
          'bit',aj.bit,'valor',ca.valor,'nome_apresentacao',aj.nome_pt)
          order by o.indice_otimizador),'[]'::jsonb) dados,
        coalesce(jsonb_agg(ca.valor order by o.indice_otimizador),'[]'::jsonb) valores,
        count(*)::int n,coalesce(bool_and(aj.pode_rodar),false) aptos
 from clube_novo.carta_atributo_jogo ca
 join clube_novo.atributo_jogo aj on aj.codigo=ca.codigo_atributo
 join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=ca.codigo_atributo
 where ca.card_id=c.card_id
) a
cross join lateral (
 select coalesce(jsonb_agg(jsonb_build_object('pos',ord.pos,'codigo',ord.codigo,
          'valor',cc.valor,'nome_apresentacao',ord.nome_pt) order by ord.pos),'[]'::jsonb) dados,
        coalesce(jsonb_agg(cc.valor order by ord.pos),'[]'::jsonb) valores,
        count(*)::int n,coalesce(bool_and(ord.pode_rodar),false) aptos
 from clube_novo.carta_corpo_jogo cc join clube_novo.corpo_ordem ord on ord.codigo=cc.codigo_corpo
 where cc.card_id=c.card_id and ord.usado_pelo_motor and ord.pos between 0 and 11
) co
cross join lateral (
 select coalesce(jsonb_agg(jsonb_build_object('posicao_id',cp.posicao_id,
          'nivel_aptidao',cp.nivel_aptidao,'codigo_apresentacao',p.codigo_pt,
          'nome_apresentacao',p.nome_pt) order by cp.posicao_id),'[]'::jsonb) dados,
        coalesce(jsonb_object_agg(p.codigo_en,cp.nivel_aptidao),'{}'::jsonb) compat,
        count(*)::int n,coalesce(bool_and(p.pode_rodar),false) aptos
 from clube_novo.carta_posicao_jogo cp join clube_novo.posicao_jogo p on p.id=cp.posicao_id
 where cp.card_id=c.card_id
) ps
cross join lateral (
 select coalesce(jsonb_agg(jsonb_build_object('skill_id',h.skill_id,'ordem',ch.ordem,
          'bit_na_carta',h.bit_na_carta,'tipo',h.tipo,'fabricavel',h.fabricavel,
          'vetada',h.vetada,'nome_apresentacao',h.nome_pt) order by h.skill_id),'[]'::jsonb) dados,
        coalesce(jsonb_agg(h.bit_na_carta order by h.bit_na_carta),'[]'::jsonb) bits,
        count(*)::int n,coalesce(bool_and(h.pode_rodar),true) aptos
 from clube_novo.carta_habilidade_jogo ch join clube_novo.habilidade_jogo h on h.skill_id=ch.skill_id
 where ch.card_id=c.card_id
) hs
cross join lateral (
 select coalesce(jsonb_agg(jsonb_build_object('bit_estilo_ia',e.bit,
          'codigo',e.codigo,'nome_apresentacao',e.nome_pt) order by e.bit),'[]'::jsonb) dados,
        count(*)::int n,coalesce(bool_and(e.pode_rodar),true) aptos
 from clube_novo.carta_estilo_ia_jogo ce join clube_novo.estilo_ia e on e.bit=ce.bit_estilo_ia
 where ce.card_id=c.card_id
) ia
cross join lateral (
 select coalesce(jsonb_agg(jsonb_build_object('campo',p.campo,'valor',p.valor,
          'codigo',p.codigo,'nome_apresentacao',p.nome_pt) order by p.campo),'[]'::jsonb) dados,
        count(*)::int n,coalesce(bool_and(p.pode_rodar),false) aptos,
        max(p.nome_pt) filter(where p.campo='pe_dominante') nome_dominante,
        max(p.valor) filter(where p.campo='pe_ruim_uso') uso,
        max(p.valor) filter(where p.campo='pe_ruim_precisao') precisao
 from clube_novo.carta_pe_jogo cp join clube_novo.pe p on (p.campo,p.valor)=(cp.campo,cp.valor)
 where cp.card_id=c.card_id
) pe
cross join lateral (
 select coalesce(jsonb_agg(jsonb_build_object('slot_fisico',cp.slot_fisico,
          'playstyle_id',p.id_jogo,'valor_raw',cp.valor_raw,
          'nome_apresentacao',p.nome_pt) order by cp.slot_fisico),'[]'::jsonb) dados,
        count(*)::int n,coalesce(bool_and(p.pode_rodar),false) aptos,
        max(cp.valor_raw) filter(where cp.slot_fisico=1) raw1,
        max(cp.valor_raw) filter(where cp.slot_fisico=2) raw2
 from clube_novo.carta_playstyle_jogo cp join clube_novo.playstyle p on p.id_jogo=cp.playstyle_id
 where cp.card_id=c.card_id
) pl
cross join lateral (
 select coalesce(jsonb_agg(jsonb_build_object('slot',ci.slot,'codigo_impeto',ci.codigo_impeto,
          'vaga',ci.vaga,'condicional',ci.condicional,'catalogo_apto',coalesce(i.pode_rodar,false),
          'nome_apresentacao',i.nome_pt) order by ci.slot),'[]'::jsonb) dados,
        count(*)::int n,count(*) filter(where ci.codigo_impeto is not null)::int equipados
 from clube_novo.carta_impeto_jogo ci left join clube_novo.impeto_jogo i on i.codigo_jogo=ci.codigo_impeto
 where ci.card_id=c.card_id
) im
cross join lateral (
 select array_remove(array[
   case when not coalesce(c.roda_motor,false) then 'carta.roda_motor=false' end,
   case when not coalesce(c.pode_rodar_vinculos,false) then 'carta.pode_rodar_vinculos=false' end,
   case when a.n<>26 or not a.aptos then 'atributos_incompletos_ou_bloqueados' end,
   case when co.n<>12 or not co.aptos then 'corpo_incompleto_ou_bloqueado' end,
   case when ps.n<>12 or not ps.aptos or cpp.card_id is null or not coalesce(pp.pode_rodar,false)
        then 'posicoes_incompletas_ou_bloqueadas' end,
   case when hs.n>0 and not hs.aptos then 'habilidade_bloqueada' end,
   case when ia.n>0 and not ia.aptos then 'estilo_ia_bloqueado' end,
   case when pe.n<>3 or not pe.aptos then 'pe_incompleto_ou_bloqueado' end,
   case when pl.n<>2 or not pl.aptos then 'playstyle_incompleto_ou_bloqueado' end,
   case when n.codigo_jogo is null or not n.pode_rodar then 'nacionalidade_bloqueada' end,
   case when cl.codigo_jogo is null or not cl.pode_rodar then 'clube_bloqueado' end,
   case when lg.codigo_jogo is null or not lg.pode_rodar then 'liga_bloqueada' end,
   case when tc.tipo_carta_id is null or not tc.pode_rodar then 'tipo_carta_bloqueado' end,
   case when im.equipados>0 then 'impetos_consumidor_desligado' end
 ],null)::text[] motivos
) g;
$$;

create or replace function public.otimizador_cartas_v1(p_ids jsonb)
returns jsonb
language sql stable security definer
set search_path=''
as $$
 select coalesce(jsonb_agg(q.carta order by q.ord) filter(where q.carta is not null),'[]'::jsonb)
 from (
   select x.ord,public.otimizador_carta_v1(x.id) carta
   from jsonb_array_elements_text(p_ids) with ordinality x(id,ord)
 ) q;
$$;

create or replace function public.otimizador_regua_v1()
returns jsonb
language sql stable security definer
set search_path=''
as $$
select jsonb_build_object(
 'contrato','otimizador_regua_v1',
 'gate',jsonb_build_object(
   'pode_rodar',
     (select count(*)=26 from clube_novo.atributo_ordem_otimizador)
     and (select count(*)=19 from clube_novo.funcao_sistema where ativa and pode_rodar)
     and (select count(*)=494 from clube.molde where versao=(select max(versao) from clube.molde))
     and not exists(select 1 from clube_novo.carta_habilidade_jogo ch join clube_novo.habilidade_jogo h using(skill_id) where not h.pode_rodar),
   'impetos_consumidor_ligado',false),
 'versao_molde',(select max(versao) from clube.molde),
 'parametros',(select coalesce(jsonb_object_agg(chave,valor),'{}'::jsonb) from clube.regua_parametro),
 'barras',(select coalesce(jsonb_object_agg(barra,a),'{}'::jsonb) from (
   select barra,jsonb_agg(attr order by attr) a from clube.barra group by barra) x),
 'custo_nivel',(select coalesce(jsonb_object_agg(nivel,acumulado),'{}'::jsonb) from clube.custo_nivel),
 'multiplicadores',(select coalesce(jsonb_object_agg(ponto,multiplicador),'{}'::jsonb) from clube.multiplicador),
 'atributos',(select jsonb_agg(jsonb_build_object('indice_otimizador',o.indice_otimizador,
   'codigo',a.codigo,'bit',a.bit,'nome_apresentacao',a.nome_pt) order by o.indice_otimizador)
   from clube_novo.atributo_ordem_otimizador o join clube_novo.atributo_jogo a on a.codigo=o.codigo_atributo),
 'funcoes',(select jsonb_agg(jsonb_build_object('funcao_id',f.id,
   'codigo_compatibilidade',f.codigo_legado,'rotulo_apresentacao',f.rotulo,
   'ordem',f.ordem) order by f.id) from clube_novo.funcao_sistema f where f.ativa and f.pode_rodar),
 'molde',(select jsonb_agg(jsonb_build_object('funcao_id',f.id,
   'indice_otimizador',m.atributo_idx,'alvo',m.alvo,'peso',m.peso)
   order by f.id,m.atributo_idx)
   from clube.molde m join clube_novo.funcao_sistema f on f.codigo_legado=m.funcao_codigo
   where m.versao=(select max(versao) from clube.molde)),
 'habilidades',(select jsonb_agg(jsonb_build_object(
   'skill_id',h.skill_id,'bit_na_carta',h.bit_na_carta,'tipo',h.tipo,
   'fabricavel',h.fabricavel,'vetada',h.vetada,'pode_rodar',h.pode_rodar,
   'nome_apresentacao',h.nome_pt,
   'efeitos',coalesce((select jsonb_agg(jsonb_build_object(
      'indice_otimizador',o.indice_otimizador,'codigo_atributo',e.key,
      'pct',coalesce((e.value->>'pct')::numeric,0),
      'flat',coalesce((e.value->>'flat')::numeric,0)) order by o.indice_otimizador)
     from jsonb_each(coalesce(h.efeito_por_codigo,'{}'::jsonb)) e
     join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=e.key),'[]'::jsonb))
   order by h.skill_id) from clube_novo.habilidade_jogo h where h.pode_rodar),
 'bloqueios',(select coalesce(jsonb_agg(jsonb_build_object('skill_id',skill_id,
   'funcao_id',funcao_id) order by funcao_id,skill_id),'[]'::jsonb)
   from clube_novo.habilidade_funcao_bloqueio_otimizador),
 'incidencias',(select coalesce(jsonb_agg(jsonb_build_object('skill_id',skill_id,
   'funcao_id',funcao_id,'incidencia_pct',incidencia_pct) order by funcao_id,skill_id),'[]'::jsonb)
   from clube_novo.habilidade_funcao_incidencia_otimizador),
 'tecnicos',(select jsonb_agg(jsonb_build_object(
   'tecnico_id',t.id,'nome_apresentacao',t.nome_en,
   'proficiencias',coalesce((select jsonb_agg(jsonb_build_object(
      'codigo_estilo',e.codigo_estilo,'valor',e.proficiencia) order by e.codigo_estilo)
      from clube_novo.tecnico_estilo_jogo e where e.tecnico_id=t.id),'[]'::jsonb),
   'proficiencia_maxima',(select max(e.proficiencia) from clube_novo.tecnico_estilo_jogo e where e.tecnico_id=t.id),
   'estilos_principais',coalesce((select jsonb_agg(jsonb_build_object(
      'codigo_estilo',p.codigo_estilo,'valor',p.proficiencia,'gemea',p.gemea)
      order by p.codigo_estilo) from clube_novo.tecnico_estilo_principal_jogo p
      where p.tecnico_id=t.id and (p.principal or p.gemea)),'[]'::jsonb),
   'boosts',coalesce((select jsonb_agg(jsonb_build_object(
      'indice_otimizador',o.indice_otimizador,'codigo_atributo',b.codigo_atributo,
      'delta',b.delta) order by b.ordem)
      from clube_novo.tecnico_atributo_jogo b join clube_novo.atributo_ordem_otimizador o
        on o.codigo_atributo=b.codigo_atributo where b.tecnico_id=t.id),'[]'::jsonb))
   order by t.id) from clube_novo.tecnico_jogo t where t.pode_rodar),
 'impetos','[]'::jsonb
);
$$;

create or replace function public.otimizador_pool_habilidades_v1(p_card_id text,p_funcao_id bigint)
returns jsonb
language sql stable security definer
set search_path=''
as $$
with carta as (select public.otimizador_carta_v1(p_card_id) j),
f as (select id from clube_novo.funcao_sistema where id=p_funcao_id and ativa and pode_rodar),
g as (select coalesce((carta.j->'gate'->>'pode_rodar')::boolean,false) carta_apta,
             exists(select 1 from f) funcao_apta from carta)
select jsonb_build_object(
 'card_id',p_card_id,'funcao_id',p_funcao_id,
 'gate',jsonb_build_object('pode_rodar',g.carta_apta and g.funcao_apta,
   'motivos',to_jsonb(array_remove(array[
     case when not g.carta_apta then 'carta_bloqueada' end,
     case when not g.funcao_apta then 'funcao_bloqueada' end],null))),
 'skill_ids',case when g.carta_apta and g.funcao_apta then coalesce((
   select jsonb_agg(h.skill_id order by h.skill_id)
   from clube_novo.habilidade_jogo h
   where h.pode_rodar and h.fabricavel and not coalesce(h.vetada,false)
     and not exists(select 1 from clube_novo.carta_habilidade_jogo ch
                    where ch.card_id=p_card_id and ch.skill_id=h.skill_id)
     and not exists(select 1 from clube_novo.habilidade_funcao_bloqueio_otimizador b
                    where b.skill_id=h.skill_id and b.funcao_id=p_funcao_id)
 ),'[]'::jsonb) else '[]'::jsonb end)
from g;
$$;

create or replace function public.otimizador_proxima_fila_v1(p_limite integer default 200)
returns jsonb
language sql stable security definer
set search_path=''
as $$
select coalesce(jsonb_agg(jsonb_build_object(
 'card_id',q.card_id,'funcao_id',q.funcao_id,
 'funcao_codigo_compat',q.funcao_codigo,'overall',q.overall,
 'prioridade',q.prioridade) order by q.prioridade,q.overall desc,q.card_id),'[]'::jsonb)
from (
 select f.card_id,fs.id funcao_id,f.funcao_codigo,f.overall,f.prioridade
 from clube.fila f join clube_novo.funcao_sistema fs on fs.codigo_legado=f.funcao_codigo
 where fs.ativa and fs.pode_rodar
 order by f.prioridade,f.overall desc,f.card_id
 limit least(greatest(p_limite,1),1000000)
) q;
$$;

create or replace function public.otimizador_peso_ordem_v1()
returns jsonb
language sql stable security definer
set search_path=''
as $$
select coalesce(jsonb_object_agg(c.card_id,jsonb_build_array(
  (case when c.vaga_s1 then 1 else 0 end)+(case when c.vaga_s2 then 1 else 0 end),
  coalesce(c.orcamento,0))),'{}'::jsonb)
from clube_novo.carta_jogo c
where exists(select 1 from clube.fila f where f.card_id=c.card_id);
$$;

revoke all on function public.otimizador_carta_v1(text) from public,anon,authenticated;
revoke all on function public.otimizador_cartas_v1(jsonb) from public,anon,authenticated;
revoke all on function public.otimizador_regua_v1() from public,anon,authenticated;
revoke all on function public.otimizador_pool_habilidades_v1(text,bigint) from public,anon,authenticated;
revoke all on function public.otimizador_proxima_fila_v1(integer) from public,anon,authenticated;
revoke all on function public.otimizador_peso_ordem_v1() from public,anon,authenticated;
grant execute on function public.otimizador_carta_v1(text) to service_role;
grant execute on function public.otimizador_cartas_v1(jsonb) to service_role;
grant execute on function public.otimizador_regua_v1() to service_role;
grant execute on function public.otimizador_pool_habilidades_v1(text,bigint) to service_role;
grant execute on function public.otimizador_proxima_fila_v1(integer) to service_role;
grant execute on function public.otimizador_peso_ordem_v1() to service_role;

commit;
