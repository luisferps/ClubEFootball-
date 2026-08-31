-- V12 - Otimizador oficial em clube_novo e uma linha por nivel de impeto.
-- A leitura de clube.* abaixo acontece uma unica vez, dentro desta migracao,
-- para formar a fotografia oficial das regras. Nenhuma funcao operacional V2
-- consulta ou grava fora de clube_novo.

begin;

create table if not exists clube_novo.otimizador_regua_parametro (
  chave text primary key,
  valor jsonb not null,
  descricao text,
  origem text,
  atualizado_em timestamptz
);

create table if not exists clube_novo.otimizador_barra_atributo (
  barra text not null,
  ordem smallint not null,
  codigo_atributo text not null references clube_novo.atributo_jogo(codigo),
  descricao text,
  atualizado_em timestamptz,
  primary key (barra, ordem),
  unique (barra, codigo_atributo)
);

create table if not exists clube_novo.otimizador_custo_nivel (
  nivel smallint primary key check (nivel between 1 and 25),
  custo smallint not null check (custo > 0),
  acumulado smallint not null check (acumulado > 0),
  descricao text,
  atualizado_em timestamptz
);

create table if not exists clube_novo.otimizador_multiplicador (
  ponto smallint primary key check (ponto between 0 and 99),
  multiplicador numeric not null check (multiplicador > 0),
  descricao text,
  atualizado_em timestamptz
);

create table if not exists clube_novo.otimizador_molde (
  versao integer not null,
  funcao_id bigint not null references clube_novo.funcao_sistema(id),
  codigo_atributo text not null references clube_novo.atributo_jogo(codigo),
  alvo numeric not null,
  peso smallint not null,
  primary key (versao, funcao_id, codigo_atributo)
);

insert into clube_novo.otimizador_regua_parametro(chave,valor,descricao,origem,atualizado_em)
select chave,valor,o_que_e,vem_de,atualizado_em
from clube.regua_parametro
on conflict (chave) do update set
  valor=excluded.valor,descricao=excluded.descricao,origem=excluded.origem,
  atualizado_em=excluded.atualizado_em;

insert into clube_novo.otimizador_barra_atributo(barra,ordem,codigo_atributo,descricao,atualizado_em)
select b.barra,b.ordem::smallint,o.codigo_atributo,b.o_que_e,b.atualizado_em
from clube.barra b
join clube_novo.atributo_ordem_otimizador o on o.indice_otimizador=b.attr
on conflict (barra,ordem) do update set
  codigo_atributo=excluded.codigo_atributo,descricao=excluded.descricao,
  atualizado_em=excluded.atualizado_em;

insert into clube_novo.otimizador_custo_nivel(nivel,custo,acumulado,descricao,atualizado_em)
select nivel::smallint,custo::smallint,acumulado::smallint,o_que_e,atualizado_em
from clube.custo_nivel
on conflict (nivel) do update set
  custo=excluded.custo,acumulado=excluded.acumulado,descricao=excluded.descricao,
  atualizado_em=excluded.atualizado_em;

insert into clube_novo.otimizador_multiplicador(ponto,multiplicador,descricao,atualizado_em)
select ponto::smallint,multiplicador,o_que_e,atualizado_em
from clube.multiplicador
on conflict (ponto) do update set
  multiplicador=excluded.multiplicador,descricao=excluded.descricao,
  atualizado_em=excluded.atualizado_em;

insert into clube_novo.otimizador_molde(versao,funcao_id,codigo_atributo,alvo,peso)
select m.versao,f.id,o.codigo_atributo,m.alvo,m.peso
from clube.molde m
join clube_novo.funcao_sistema f on f.codigo_legado=m.funcao_codigo
join clube_novo.atributo_ordem_otimizador o on o.indice_otimizador=m.atributo_idx
on conflict (versao,funcao_id,codigo_atributo) do update set
  alvo=excluded.alvo,peso=excluded.peso;

do $$
begin
  if (select count(*) from clube_novo.otimizador_regua_parametro)
     <> (select count(*) from clube.regua_parametro) then
    raise exception 'copia da regua recusada: parametros divergentes';
  end if;
  if (select count(*) from clube_novo.otimizador_barra_atributo)
     <> (select count(*) from clube.barra) then
    raise exception 'copia da regua recusada: barras divergentes';
  end if;
  if (select count(*) from clube_novo.otimizador_custo_nivel)
     <> (select count(*) from clube.custo_nivel) then
    raise exception 'copia da regua recusada: custos divergentes';
  end if;
  if (select count(*) from clube_novo.otimizador_multiplicador)
     <> (select count(*) from clube.multiplicador) then
    raise exception 'copia da regua recusada: multiplicadores divergentes';
  end if;
  if (select count(*) from clube_novo.otimizador_molde)
     <> (select count(*) from clube.molde) then
    raise exception 'copia da regua recusada: moldes divergentes';
  end if;
end $$;

alter table clube_novo.otimizador_regua_parametro enable row level security;
alter table clube_novo.otimizador_barra_atributo enable row level security;
alter table clube_novo.otimizador_custo_nivel enable row level security;
alter table clube_novo.otimizador_multiplicador enable row level security;
alter table clube_novo.otimizador_molde enable row level security;

revoke all on clube_novo.otimizador_regua_parametro from public,anon,authenticated;
revoke all on clube_novo.otimizador_barra_atributo from public,anon,authenticated;
revoke all on clube_novo.otimizador_custo_nivel from public,anon,authenticated;
revoke all on clube_novo.otimizador_multiplicador from public,anon,authenticated;
revoke all on clube_novo.otimizador_molde from public,anon,authenticated;
grant select on clube_novo.otimizador_regua_parametro to service_role;
grant select on clube_novo.otimizador_barra_atributo to service_role;
grant select on clube_novo.otimizador_custo_nivel to service_role;
grant select on clube_novo.otimizador_multiplicador to service_role;
grant select on clube_novo.otimizador_molde to service_role;

create or replace function clube_novo.impeto_nivel_maximo_v1(p_codigo integer)
returns smallint language sql stable set search_path='' as $$
  select case when i.condicional then coalesce(
    (select p.efeito_maximo::smallint
       from clube_novo.impeto_condicao_parametro_faixa_jogo p
      where p.codigo_impeto=i.codigo_jogo),
    (select max(a.delta)::smallint
       from clube_novo.impeto_atributo_jogo a
      where a.codigo_impeto=i.codigo_jogo)
  ) end
  from clube_novo.impeto_jogo i
  where i.codigo_jogo=p_codigo
$$;
revoke all on function clube_novo.impeto_nivel_maximo_v1(integer) from public,anon,authenticated;
grant execute on function clube_novo.impeto_nivel_maximo_v1(integer) to service_role;

alter table clube_novo.build_linha_card
  add column if not exists impeto_condicional_codigo integer,
  add column if not exists impeto_condicional_nivel smallint;

alter table clube_novo.build_linha_card
  drop constraint if exists build_linha_impeto_condicional_par_v12_check,
  drop constraint if exists build_linha_impeto_condicional_codigo_v12_fkey;

alter table clube_novo.build_linha_card
  add constraint build_linha_impeto_condicional_par_v12_check check (
    (impeto_condicional_codigo is null and impeto_condicional_nivel is null)
    or
    (impeto_condicional_codigo is not null and impeto_condicional_nivel between 1 and 5)
  ),
  add constraint build_linha_impeto_condicional_codigo_v12_fkey
    foreign key (impeto_condicional_codigo)
    references clube_novo.impeto_jogo(codigo_jogo);

create or replace function clube_novo.validar_impeto_build_linha_v12()
returns trigger language plpgsql set search_path='' as $$
declare
  v_quantidade integer;
  v_codigo integer;
  v_maximo smallint;
begin
  select count(*),min(ci.codigo_impeto)
    into v_quantidade,v_codigo
  from clube_novo.carta_impeto_jogo ci
  where ci.card_id=new.card_id
    and ci.codigo_impeto is not null
    and ci.condicional;

  if v_quantidade > 1 then
    raise exception 'linha recusada: carta possui mais de um impeto condicional';
  end if;
  if v_quantidade = 0 then
    if new.impeto_condicional_codigo is not null or new.impeto_condicional_nivel is not null then
      raise exception 'linha recusada: carta nao possui impeto condicional';
    end if;
    return new;
  end if;
  if new.impeto_condicional_codigo is null or new.impeto_condicional_nivel is null then
    raise exception 'linha recusada: codigo e nivel do impeto condicional sao obrigatorios';
  end if;
  if new.impeto_condicional_codigo <> v_codigo then
    raise exception 'linha recusada: impeto condicional nao pertence a carta';
  end if;
  v_maximo := clube_novo.impeto_nivel_maximo_v1(v_codigo);
  if v_maximo is null or v_maximo not between 1 and 5 then
    raise exception 'linha recusada: nivel maximo fisico do impeto nao comprovado';
  end if;
  if new.impeto_condicional_nivel > v_maximo then
    raise exception 'linha recusada: nivel % excede o maximo %',new.impeto_condicional_nivel,v_maximo;
  end if;
  return new;
end $$;

drop trigger if exists build_linha_impeto_v12 on clube_novo.build_linha_card;
create trigger build_linha_impeto_v12
before insert or update of card_id,impeto_condicional_codigo,impeto_condicional_nivel
on clube_novo.build_linha_card for each row
execute function clube_novo.validar_impeto_build_linha_v12();

drop index if exists clube_novo.build_linha_card_uma_ativa_por_contexto_uidx;
drop index if exists clube_novo.build_linha_teste_contexto_v1_uidx;
create unique index build_linha_card_uma_ativa_por_contexto_uidx
on clube_novo.build_linha_card(
  card_id,funcao_id,posicao_id,
  coalesce(impeto_condicional_codigo,-1),coalesce(impeto_condicional_nivel,0)
)
where estado <> 'invalida' and execucao_tipo='producao';
create unique index build_linha_teste_contexto_v1_uidx
on clube_novo.build_linha_card(
  lote_teste_id,card_id,funcao_id,posicao_id,
  coalesce(impeto_condicional_codigo,-1),coalesce(impeto_condicional_nivel,0)
)
where lote_teste_id is not null;

create or replace function clube_novo.controlar_build_linha_auditoria_v5()
returns trigger language plpgsql set search_path='' as $$
begin
  if new.criado_em is distinct from old.criado_em then
    raise exception 'linha recusada: criado_em e imutavel';
  end if;
  if old.estado in ('pronta','publicada','invalida') and (
       new.card_id is distinct from old.card_id
       or new.funcao_id is distinct from old.funcao_id
       or new.posicao_id is distinct from old.posicao_id
       or new.impeto_condicional_codigo is distinct from old.impeto_condicional_codigo
       or new.impeto_condicional_nivel is distinct from old.impeto_condicional_nivel
       or new.build_otimizador_id is distinct from old.build_otimizador_id
       or new.build_bonificador_id is distinct from old.build_bonificador_id
       or new.carta_versao is distinct from old.carta_versao
       or new.carta_fingerprint is distinct from old.carta_fingerprint
       or new.otimizador_motor_versao is distinct from old.otimizador_motor_versao
       or new.otimizador_contrato_versao is distinct from old.otimizador_contrato_versao
       or new.bonificador_motor_versao is distinct from old.bonificador_motor_versao
       or new.bonificador_contrato_versao is distinct from old.bonificador_contrato_versao
       or new.atributos_snapshot is distinct from old.atributos_snapshot
       or new.atributos_snapshot_fingerprint is distinct from old.atributos_snapshot_fingerprint
       or new.snapshot_otimizador_fingerprint is distinct from old.snapshot_otimizador_fingerprint
       or new.snapshot_bonificador_fingerprint is distinct from old.snapshot_bonificador_fingerprint
  ) then
    raise exception 'linha recusada: identidade e selos da linha montada sao imutaveis';
  end if;
  if old.montada_em is not null and new.montada_em is distinct from old.montada_em then
    raise exception 'linha recusada: montada_em e imutavel';
  end if;
  if old.montada_em is null and new.estado in ('pronta','publicada') then new.montada_em:=now(); end if;
  new.atualizado_em:=now();
  return new;
end $$;
drop trigger if exists build_linha_auditoria_v4 on clube_novo.build_linha_card;
drop trigger if exists build_linha_auditoria_v5 on clube_novo.build_linha_card;
create trigger build_linha_auditoria_v5 before update on clube_novo.build_linha_card
for each row execute function clube_novo.controlar_build_linha_auditoria_v5();

create or replace function public.otimizador_regua_v2()
returns jsonb language plpgsql stable security definer set search_path='' as $$
declare
  v_versao integer;
  v_atributos integer;
  v_funcoes integer;
  v_motivos text[] := '{}';
begin
  select max(versao) into v_versao from clube_novo.otimizador_molde;
  select count(*) into v_atributos from clube_novo.atributo_ordem_otimizador;
  select count(*) into v_funcoes from clube_novo.funcao_sistema where ativa and pode_rodar;
  if v_atributos<>26 then v_motivos:=array_append(v_motivos,'atributos_da_regua_incompletos'); end if;
  if v_funcoes<1 then v_motivos:=array_append(v_motivos,'funcoes_ativas_ausentes'); end if;
  if exists(
    select 1 from clube_novo.funcao_sistema f
    where f.ativa and f.pode_rodar and
      (select count(*) from clube_novo.otimizador_molde m
       where m.versao=v_versao and m.funcao_id=f.id)<>v_atributos
  ) then v_motivos:=array_append(v_motivos,'molde_incompleto_por_funcao'); end if;
  if (select count(*) from clube_novo.otimizador_regua_parametro)<>8 then
    v_motivos:=array_append(v_motivos,'parametros_da_regua_incompletos');
  end if;
  if (select count(*) from clube_novo.otimizador_custo_nivel)<>25 then
    v_motivos:=array_append(v_motivos,'custos_de_nivel_incompletos');
  end if;
  if (select count(*) from clube_novo.otimizador_multiplicador)<>100
     or (select min(ponto) from clube_novo.otimizador_multiplicador)<>0
     or (select max(ponto) from clube_novo.otimizador_multiplicador)<>99 then
    v_motivos:=array_append(v_motivos,'multiplicadores_incompletos');
  end if;
  if exists(select 1 from clube_novo.carta_habilidade_jogo ch
            join clube_novo.habilidade_jogo h using(skill_id) where not h.pode_rodar) then
    v_motivos:=array_append(v_motivos,'habilidade_de_carta_bloqueada');
  end if;

  return jsonb_build_object(
    'contrato','otimizador_regua_v2',
    'gate',jsonb_build_object('pode_rodar',cardinality(v_motivos)=0,'motivos',to_jsonb(v_motivos)),
    'versao_molde',v_versao,
    'parametros',(select coalesce(jsonb_object_agg(chave,valor),'{}'::jsonb)
                  from clube_novo.otimizador_regua_parametro),
    'barras',(select coalesce(jsonb_object_agg(barra,indices),'{}'::jsonb) from (
      select b.barra,jsonb_agg(o.indice_otimizador order by b.ordem) indices
      from clube_novo.otimizador_barra_atributo b
      join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=b.codigo_atributo
      group by b.barra) x),
    'custo_nivel',(select coalesce(jsonb_object_agg(nivel,acumulado),'{}'::jsonb)
                   from clube_novo.otimizador_custo_nivel),
    'multiplicadores',(select coalesce(jsonb_object_agg(ponto,multiplicador),'{}'::jsonb)
                       from clube_novo.otimizador_multiplicador),
    'atributos',(select jsonb_agg(jsonb_build_object(
      'indice_otimizador',o.indice_otimizador,'codigo',a.codigo,'bit',a.bit)
      order by o.indice_otimizador)
      from clube_novo.atributo_ordem_otimizador o
      join clube_novo.atributo_jogo a on a.codigo=o.codigo_atributo),
    'funcoes',(select jsonb_agg(jsonb_build_object('funcao_id',f.id,'ordem',f.ordem) order by f.id)
      from clube_novo.funcao_sistema f where f.ativa and f.pode_rodar),
    'molde',(select jsonb_agg(jsonb_build_object(
      'funcao_id',m.funcao_id,'indice_otimizador',o.indice_otimizador,
      'alvo',m.alvo,'peso',m.peso) order by m.funcao_id,o.indice_otimizador)
      from clube_novo.otimizador_molde m
      join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=m.codigo_atributo
      where m.versao=v_versao),
    'habilidades',(select jsonb_agg(jsonb_build_object(
      'skill_id',h.skill_id,'bit_na_carta',h.bit_na_carta,'tipo',h.tipo,
      'fabricavel',h.fabricavel,'vetada',h.vetada,'pode_rodar',h.pode_rodar,
      'efeitos',coalesce((select jsonb_agg(jsonb_build_object(
        'indice_otimizador',o.indice_otimizador,'codigo_atributo',e.key,
        'pct',coalesce((e.value->>'pct')::numeric,0),
        'flat',coalesce((e.value->>'flat')::numeric,0)) order by o.indice_otimizador)
        from jsonb_each(coalesce(h.efeito_por_codigo,'{}'::jsonb)) e
        join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=e.key),'[]'::jsonb)
      ) order by h.skill_id) from clube_novo.habilidade_jogo h where h.pode_rodar),
    'bloqueios',(select coalesce(jsonb_agg(jsonb_build_object(
      'skill_id',skill_id,'funcao_id',funcao_id) order by funcao_id,skill_id),'[]'::jsonb)
      from clube_novo.habilidade_funcao_bloqueio_otimizador),
    'incidencias',(select coalesce(jsonb_agg(jsonb_build_object(
      'skill_id',skill_id,'funcao_id',funcao_id,'incidencia_pct',incidencia_pct)
      order by funcao_id,skill_id),'[]'::jsonb)
      from clube_novo.habilidade_funcao_incidencia_otimizador),
    'tecnicos',(select jsonb_agg(jsonb_build_object(
      'tecnico_id',t.id,
      'proficiencias',coalesce((select jsonb_agg(jsonb_build_object(
        'codigo_estilo',e.codigo_estilo,'valor',e.proficiencia) order by e.codigo_estilo)
        from clube_novo.tecnico_estilo_jogo e where e.tecnico_id=t.id),'[]'::jsonb),
      'proficiencia_maxima',(select max(e.proficiencia) from clube_novo.tecnico_estilo_jogo e where e.tecnico_id=t.id),
      'estilos_principais',coalesce((select jsonb_agg(jsonb_build_object(
        'codigo_estilo',p.codigo_estilo,'valor',p.proficiencia,'gemea',p.gemea)
        order by p.codigo_estilo) from clube_novo.tecnico_estilo_principal_jogo p
        where p.tecnico_id=t.id and (p.principal or p.gemea)),'[]'::jsonb),
      'boosts',coalesce((select jsonb_agg(jsonb_build_object(
        'indice_otimizador',o.indice_otimizador,'codigo_atributo',b.codigo_atributo,'delta',b.delta)
        order by b.ordem) from clube_novo.tecnico_atributo_jogo b
        join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=b.codigo_atributo
        where b.tecnico_id=t.id),'[]'::jsonb)) order by t.id)
      from clube_novo.tecnico_jogo t where t.pode_rodar),
    'impetos',(select coalesce(jsonb_agg(jsonb_build_object(
      'codigo_impeto',i.codigo_jogo,'condicional',i.condicional,
      'nivel_maximo',clube_novo.impeto_nivel_maximo_v1(i.codigo_jogo),
      'efeitos',coalesce((select jsonb_agg(jsonb_build_object(
        'indice_otimizador',o.indice_otimizador,'codigo_atributo',a.codigo_atributo,'delta',a.delta)
        order by o.indice_otimizador) from clube_novo.impeto_atributo_jogo a
        join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=a.codigo_atributo
        where a.codigo_impeto=i.codigo_jogo),'[]'::jsonb)) order by i.codigo_jogo),'[]'::jsonb)
      from clube_novo.impeto_jogo i)
  );
end $$;

revoke all on function public.otimizador_regua_v2() from public,anon,authenticated;
grant execute on function public.otimizador_regua_v2() to service_role;

create or replace function public.otimizador_carta_v2(p_card_id text)
returns jsonb language sql stable security definer set search_path='' as $$
with b as (
  select public.otimizador_carta_v1(p_card_id) j
), antigos as (
  select coalesce(array_agg(valor order by ordem)
    filter(where valor<>'impetos_consumidor_desligado'),'{}'::text[]) motivos
  from b cross join lateral
    jsonb_array_elements_text(coalesce(b.j#>'{gate,motivos}','[]'::jsonb))
    with ordinality x(valor,ordem)
), impetos as (
  select coalesce(jsonb_agg(jsonb_build_object(
    'slot',ci.slot,'codigo_impeto',ci.codigo_impeto,'vaga',ci.vaga,
    'condicional',ci.condicional,
    'nivel_maximo',case when ci.condicional then clube_novo.impeto_nivel_maximo_v1(ci.codigo_impeto) end,
    'efeitos',coalesce(ef.dados,'[]'::jsonb)
  ) order by ci.slot),'[]'::jsonb) dados,
  count(*)::int n,
  count(*) filter(where ci.codigo_impeto is not null and ci.condicional)::int condicionais,
  count(*) filter(where ci.codigo_impeto is not null and coalesce(ef.n,0)=0)::int sem_receita,
  count(*) filter(where ci.codigo_impeto is not null and ci.condicional and
    coalesce(clube_novo.impeto_nivel_maximo_v1(ci.codigo_impeto),0) not between 1 and 5)::int sem_nivel
  from clube_novo.carta_impeto_jogo ci
  left join lateral (
    select jsonb_agg(jsonb_build_object(
      'indice_otimizador',o.indice_otimizador,'codigo_atributo',a.codigo_atributo,'delta',a.delta)
      order by o.indice_otimizador) dados,count(*)::int n
    from clube_novo.impeto_atributo_jogo a
    join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=a.codigo_atributo
    where a.codigo_impeto=ci.codigo_impeto
  ) ef on true
  where ci.card_id=p_card_id
), novos as (
  select array_remove(array[
    case when i.condicionais>1 then 'mais_de_um_impeto_condicional' end,
    case when i.sem_receita>0 then 'impeto_equipado_sem_receita_fisica' end,
    case when i.sem_nivel>0 then 'impeto_condicional_sem_nivel_maximo_fisico' end
  ],null)::text[] motivos
  from impetos i
), gate as (
  select antigos.motivos||novos.motivos motivos from antigos,novos
)
select (b.j
  - 'contrato' - 'apresentacao' - 'compatibilidade_legado'
  - 'atributos' - 'corpo' - 'posicoes' - 'habilidades'
  - 'estilos_ia' - 'pes' - 'playstyles' - 'impetos' - 'gate')
  || jsonb_build_object(
    'contrato','otimizador_entradas_v2',
    'atributos',(select coalesce(jsonb_agg(jsonb_build_object(
      'indice_otimizador',(x->>'indice_otimizador')::smallint,
      'codigo',x->>'codigo','bit',(x->>'bit')::integer,'valor',(x->>'valor')::integer)
      order by (x->>'indice_otimizador')::smallint),'[]'::jsonb)
      from jsonb_array_elements(coalesce(b.j->'atributos','[]'::jsonb)) x),
    'corpo',(select coalesce(jsonb_agg(jsonb_build_object(
      'pos',(x->>'pos')::smallint,'codigo',x->>'codigo','valor',(x->>'valor')::integer)
      order by (x->>'pos')::smallint),'[]'::jsonb)
      from jsonb_array_elements(coalesce(b.j->'corpo','[]'::jsonb)) x),
    'posicoes',(select coalesce(jsonb_agg(jsonb_build_object(
      'posicao_id',(x->>'posicao_id')::integer,'nivel_aptidao',(x->>'nivel_aptidao')::integer)
      order by (x->>'posicao_id')::integer),'[]'::jsonb)
      from jsonb_array_elements(coalesce(b.j->'posicoes','[]'::jsonb)) x),
    'habilidades',(select coalesce(jsonb_agg(jsonb_build_object(
      'skill_id',(x->>'skill_id')::integer,'ordem',(x->>'ordem')::integer,
      'bit_na_carta',(x->>'bit_na_carta')::integer,'tipo',x->>'tipo',
      'fabricavel',coalesce((x->>'fabricavel')::boolean,false),
      'vetada',coalesce((x->>'vetada')::boolean,false))
      order by (x->>'skill_id')::integer),'[]'::jsonb)
      from jsonb_array_elements(coalesce(b.j->'habilidades','[]'::jsonb)) x),
    'estilos_ia',(select coalesce(jsonb_agg(jsonb_build_object(
      'bit_estilo_ia',(x->>'bit_estilo_ia')::integer,'codigo',x->>'codigo')
      order by (x->>'bit_estilo_ia')::integer),'[]'::jsonb)
      from jsonb_array_elements(coalesce(b.j->'estilos_ia','[]'::jsonb)) x),
    'pes',(select coalesce(jsonb_agg(jsonb_build_object(
      'campo',x->>'campo','valor',(x->>'valor')::integer,'codigo',x->>'codigo')
      order by x->>'campo'),'[]'::jsonb)
      from jsonb_array_elements(coalesce(b.j->'pes','[]'::jsonb)) x),
    'playstyles',(select coalesce(jsonb_agg(jsonb_build_object(
      'slot_fisico',(x->>'slot_fisico')::integer,'playstyle_id',(x->>'playstyle_id')::integer,
      'valor_raw',(x->>'valor_raw')::integer) order by (x->>'slot_fisico')::integer),'[]'::jsonb)
      from jsonb_array_elements(coalesce(b.j->'playstyles','[]'::jsonb)) x),
    'impetos',i.dados,
    'gate',jsonb_build_object('pode_rodar',cardinality(g.motivos)=0,'motivos',to_jsonb(g.motivos))
  )
from b,impetos i,gate g
where b.j is not null
$$;

create or replace function public.otimizador_cartas_v2(p_ids jsonb)
returns jsonb language sql stable security definer set search_path='' as $$
  select coalesce(jsonb_agg(q.carta order by q.ord) filter(where q.carta is not null),'[]'::jsonb)
  from (
    select x.ord,public.otimizador_carta_v2(x.id) carta
    from jsonb_array_elements_text(p_ids) with ordinality x(id,ord)
  ) q
$$;

create or replace function public.otimizador_pool_habilidades_v2(p_card_id text,p_funcao_id bigint)
returns jsonb language sql stable security definer set search_path='' as $$
with carta as (select public.otimizador_carta_v2(p_card_id) j),
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
from g
$$;

create or replace function public.otimizador_catalogos_apresentacao_v1()
returns jsonb language sql stable security definer set search_path='' as $$
select jsonb_build_object(
  'contrato','otimizador_catalogos_apresentacao_v1',
  'funcoes',(select jsonb_agg(jsonb_build_object('funcao_id',id,'rotulo',rotulo) order by ordem,id)
    from clube_novo.funcao_sistema where ativa and pode_rodar),
  'posicoes',(select jsonb_agg(jsonb_build_object('posicao_id',id,'rotulo',nome_pt,'codigo',codigo_pt) order by id)
    from clube_novo.posicao_jogo where pode_rodar),
  'tecnicos',(select jsonb_agg(jsonb_build_object('tecnico_id',id,'rotulo',nome_en) order by id)
    from clube_novo.tecnico_jogo where pode_rodar),
  'habilidades',(select jsonb_agg(jsonb_build_object('skill_id',skill_id,'rotulo',nome_pt) order by skill_id)
    from clube_novo.habilidade_jogo where pode_rodar),
  'impetos',(select jsonb_agg(jsonb_build_object('codigo_impeto',codigo_jogo,'rotulo',nome_pt) order by codigo_jogo)
    from clube_novo.impeto_jogo)
)
$$;

create or replace function public.otimizador_carta_apresentacao_v1(p_card_id text)
returns jsonb language sql stable security definer set search_path='' as $$
select jsonb_build_object(
  'card_id',c.card_id,'nome',c.nome,'overall',c.overall,
  'posicao_principal_id',cpp.posicao_id
)
from clube_novo.carta_jogo c
left join clube_novo.carta_posicao_principal_jogo cpp on cpp.card_id=c.card_id
where c.card_id=p_card_id
$$;

revoke all on function public.otimizador_carta_v2(text) from public,anon,authenticated;
revoke all on function public.otimizador_cartas_v2(jsonb) from public,anon,authenticated;
revoke all on function public.otimizador_pool_habilidades_v2(text,bigint) from public,anon,authenticated;
revoke all on function public.otimizador_catalogos_apresentacao_v1() from public,anon,authenticated;
revoke all on function public.otimizador_carta_apresentacao_v1(text) from public,anon,authenticated;
grant execute on function public.otimizador_carta_v2(text) to service_role;
grant execute on function public.otimizador_cartas_v2(jsonb) to service_role;
grant execute on function public.otimizador_pool_habilidades_v2(text,bigint) to service_role;
grant execute on function public.otimizador_catalogos_apresentacao_v1() to service_role;
grant execute on function public.otimizador_carta_apresentacao_v1(text) to service_role;

alter table clube_novo.build_otimizador
  add column if not exists builds_possiveis numeric;
alter table clube_novo.build_otimizador
  drop constraint if exists build_otimizador_builds_possiveis_v12_check;
alter table clube_novo.build_otimizador
  add constraint build_otimizador_builds_possiveis_v12_check
  check (builds_possiveis is null or builds_possiveis>=0 and trunc(builds_possiveis)=builds_possiveis);

create or replace function public.otimizador_status_teste_v2(p_lote_id uuid)
returns jsonb language sql stable security definer set search_path='' as $$
with s as (
  select max(lote_teste_fingerprint) fingerprint,min(sorteada_em) sorteada_em,
    min(lote_estado) estado_lote,max(lote_estado_atualizado_em) estado_atualizado_em,
    max(lote_falha) falha_lote,count(distinct card_id) cards,count(*) linhas,
    count(*) filter(where estado_otimizador='pendente') pendentes,
    count(*) filter(where estado_otimizador='processando') processando,
    count(*) filter(where estado_otimizador='concluido') concluidas,
    count(*) filter(where estado_otimizador='bloqueado') bloqueadas,
    count(*) filter(where estado_otimizador='interrompido') interrompidas,
    coalesce(jsonb_agg(jsonb_build_object(
      'linha_id',id,'card_id',card_id,'funcao_id',funcao_id,'posicao_id',posicao_id,
      'impeto_condicional_codigo',impeto_condicional_codigo,
      'impeto_condicional_nivel',impeto_condicional_nivel,
      'estado',estado_otimizador,'motivo',erro_otimizador,
      'iniciada_em',otimizador_iniciado_em) order by otimizador_iniciado_em)
      filter(where estado_otimizador='processando'),'[]'::jsonb) corrente,
    coalesce(jsonb_agg(jsonb_build_object(
      'linha_id',id,'card_id',card_id,'funcao_id',funcao_id,'posicao_id',posicao_id,
      'impeto_condicional_codigo',impeto_condicional_codigo,
      'impeto_condicional_nivel',impeto_condicional_nivel,
      'estado',estado_otimizador,'motivo',erro_otimizador) order by id)
      filter(where estado_otimizador in ('bloqueado','interrompido')),'[]'::jsonb) motivos
  from clube_novo.build_linha_card where lote_teste_id=p_lote_id
)
select jsonb_build_object(
  'contrato','otimizador_teste_100_v12','lote_id',p_lote_id,'fingerprint',fingerprint,
  'sorteada_em',sorteada_em,'estado',estado_lote,'estado_lote',estado_lote,
  'estado_atualizado_em',estado_atualizado_em,'falha_lote',falha_lote,
  'cards',cards,'linhas',linhas,'pendentes',pendentes,'processando',processando,
  'concluidas',concluidas,'bloqueadas',bloqueadas,'interrompidas',interrompidas,
  'corrente',corrente,'motivos',motivos,
  'acoes',jsonb_build_object(
    'criar',false,
    'iniciar',estado_lote in ('parado','pausado') and pendentes>0,
    'pausar',estado_lote='rodando',
    'parar',estado_lote in ('parado','rodando','pausando','pausado','falhou') and pendentes>0,
    'retomar',estado_lote in ('pausado','falhou') and pendentes>0,
    'console',estado_lote is not null),
  'confirmacao',jsonb_build_object('parar_exige_confirmacao',true),
  'pode_publicar',false,'modo','teste_nao_publicado')
from s
$$;

create or replace function public.otimizador_fila_teste_v2(p_lote_id uuid)
returns jsonb language sql stable security definer set search_path='' as $$
select coalesce(jsonb_agg(jsonb_build_object(
  'linha_id',l.id,'card_id',l.card_id,'funcao_id',l.funcao_id,'posicao_id',l.posicao_id,
  'impeto_condicional_codigo',l.impeto_condicional_codigo,
  'impeto_condicional_nivel',l.impeto_condicional_nivel,
  'ordem_card',l.amostra_ordem,'estado',l.estado_otimizador,
  'carta_versao',l.carta_versao,'carta_fingerprint',l.carta_fingerprint,
  'lote_fingerprint',l.lote_teste_fingerprint,'erro',l.erro_otimizador,
  'b1',b.pontuacao,'pontuacao_final',b.pontuacao,'barras',b.barras,
  'tecnico_id',b.tecnico_id,'impeto_adicional_codigo',b.impeto_adicional_codigo,
  'habilidades_adicionais',b.habilidades_adicionais,
  'builds_comparadas',b.builds_comparadas,'builds_possiveis',b.builds_possiveis,
  'segundos',case when l.otimizador_iniciado_em is not null and l.otimizador_finalizado_em is not null
                  then round(extract(epoch from (l.otimizador_finalizado_em-l.otimizador_iniciado_em))::numeric,2) end,
  'otimizador_iniciado_em',l.otimizador_iniciado_em,
  'otimizador_finalizado_em',l.otimizador_finalizado_em
) order by l.amostra_ordem,l.funcao_id,l.posicao_id,
           coalesce(l.impeto_condicional_codigo,-1),coalesce(l.impeto_condicional_nivel,0)),'[]'::jsonb)
from clube_novo.build_linha_card l
left join clube_novo.build_otimizador b on b.id=l.build_otimizador_id
where l.lote_teste_id=p_lote_id and l.execucao_tipo='teste_isolado'
$$;

create or replace function public.otimizador_eventos_teste_v2(p_lote_id uuid)
returns jsonb language sql stable security definer set search_path='' as $$
select coalesce(jsonb_agg(jsonb_build_object(
  'ordem',ordem,'instante',instante,'linha_id',id,'card_id',card_id,
  'funcao_id',funcao_id,'posicao_id',posicao_id,
  'impeto_condicional_codigo',impeto_condicional_codigo,
  'impeto_condicional_nivel',impeto_condicional_nivel,
  'estado',estado_otimizador,'motivo',erro_otimizador) order by instante,id),'[]'::jsonb)
from (
  select x.*,row_number() over(order by instante,id) ordem from (
    select *,coalesce(otimizador_finalizado_em,otimizador_iniciado_em,sorteada_em) instante
    from clube_novo.build_linha_card where lote_teste_id=p_lote_id
  ) x
) e
$$;

create or replace function public.otimizador_concluir_linha_teste_v2(
  p_linha_id bigint,p_lote_id uuid,p_resultado jsonb
) returns bigint language plpgsql security definer set search_path='' as $$
declare
  v_linha clube_novo.build_linha_card%rowtype;
  v_id bigint;
  v_habs integer[];
  v_builds integer;
  v_possiveis numeric;
  v_codigo integer;
  v_nivel smallint;
  v_impeto_adicional integer;
begin
  select * into v_linha from clube_novo.build_linha_card
  where id=p_linha_id and lote_teste_id=p_lote_id and execucao_tipo='teste_isolado' for update;
  if v_linha.id is null then raise exception 'linha de teste inexistente'; end if;
  if v_linha.build_otimizador_id is not null and v_linha.estado_otimizador='concluido' then
    return v_linha.build_otimizador_id;
  end if;
  if v_linha.estado_otimizador<>'processando' then raise exception 'linha nao esta processando'; end if;

  v_codigo:=nullif(p_resultado->>'impeto_condicional_codigo','')::integer;
  v_nivel:=nullif(p_resultado->>'impeto_condicional_nivel','')::smallint;
  if p_resultado->>'card_id'<>v_linha.card_id
     or (p_resultado->>'funcao_id')::bigint<>v_linha.funcao_id
     or (p_resultado->>'posicao_id')::integer<>v_linha.posicao_id
     or v_codigo is distinct from v_linha.impeto_condicional_codigo
     or v_nivel is distinct from v_linha.impeto_condicional_nivel then
    raise exception 'resultado nao pertence a linha selada';
  end if;
  if p_resultado->>'carta_versao'<>v_linha.carta_versao
     or p_resultado->>'carta_fingerprint'<>v_linha.carta_fingerprint
     or p_resultado->>'lote_fingerprint'<>v_linha.lote_teste_fingerprint then
    raise exception 'versao/fingerprint da entrada diverge';
  end if;
  if p_resultado->>'formula_fingerprint'<>v_linha.otimizador_formula_fingerprint_esperado
     or p_resultado->>'contrato_fingerprint'<>v_linha.otimizador_contrato_fingerprint_esperado
     or p_resultado->>'motor_versao'<>v_linha.otimizador_motor_versao_esperada then
    raise exception 'selos do motor/contrato/formula divergem';
  end if;
  if (p_resultado->>'builds_comparadas') !~ '^[0-9]+$' then
    raise exception 'telemetria builds_comparadas invalida';
  end if;
  if (p_resultado->>'builds_possiveis') !~ '^[0-9]+$' then
    raise exception 'telemetria builds_possiveis invalida';
  end if;
  v_builds:=(p_resultado->>'builds_comparadas')::integer;
  v_possiveis:=(p_resultado->>'builds_possiveis')::numeric;
  if v_builds>v_possiveis then
    raise exception 'telemetria invalida: comparadas excedem universo possivel';
  end if;
  v_impeto_adicional:=nullif(p_resultado->>'impeto_adicional_codigo','')::integer;
  select coalesce(array_agg(x::integer),'{}'::integer[]) into v_habs
  from (select jsonb_array_elements_text(coalesce(p_resultado->'habilidades','[]'::jsonb)) x limit 5) q;

  insert into clube_novo.build_otimizador(
    tecnico_id,barras,impeto_adicional_codigo,habilidades_adicionais,pontuacao,
    contrato_versao,contrato_fingerprint,carta_versao,carta_fingerprint,
    formula_fingerprint,resultado_fingerprint,motor_versao,builds_comparadas,builds_possiveis
  ) values(
    (p_resultado->>'tecnico_id')::bigint,p_resultado->'barras',v_impeto_adicional,v_habs,
    (p_resultado->>'b1')::numeric,coalesce(p_resultado#>>'{insumos,fonte}','otimizador_regua_v2'),
    p_resultado->>'contrato_fingerprint',v_linha.carta_versao,v_linha.carta_fingerprint,
    p_resultado->>'formula_fingerprint',encode(extensions.digest(p_resultado::text,'sha256'),'hex'),
    p_resultado->>'motor_versao',v_builds,v_possiveis
  ) returning id into v_id;

  update clube_novo.build_linha_card set
    build_otimizador_id=v_id,estado_otimizador='concluido',
    otimizador_finalizado_em=clock_timestamp(),otimizador_motor_versao=p_resultado->>'motor_versao',
    otimizador_contrato_versao=coalesce(p_resultado#>>'{insumos,fonte}','otimizador_regua_v2'),
    snapshot_otimizador_fingerprint=(select resultado_fingerprint from clube_novo.build_otimizador where id=v_id),
    erro_otimizador=null
  where id=v_linha.id;
  return v_id;
end $$;

revoke all on function public.otimizador_status_teste_v2(uuid) from public,anon,authenticated;
revoke all on function public.otimizador_fila_teste_v2(uuid) from public,anon,authenticated;
revoke all on function public.otimizador_eventos_teste_v2(uuid) from public,anon,authenticated;
revoke all on function public.otimizador_concluir_linha_teste_v2(bigint,uuid,jsonb) from public,anon,authenticated;
grant execute on function public.otimizador_status_teste_v2(uuid) to service_role;
grant execute on function public.otimizador_fila_teste_v2(uuid) to service_role;
grant execute on function public.otimizador_eventos_teste_v2(uuid) to service_role;
grant execute on function public.otimizador_concluir_linha_teste_v2(bigint,uuid,jsonb) to service_role;

create or replace function public.otimizador_criar_amostra_teste_v3(
  p_lote_id uuid,p_semente text,p_formula_fingerprint text,
  p_contrato_fingerprint text,p_motor_versao text
) returns jsonb language plpgsql security definer set search_path='' as $$
declare
  v_cards integer;
  v_fp text;
  v_quando timestamptz:=clock_timestamp();
begin
  if p_lote_id is null or nullif(btrim(p_semente),'') is null
     or nullif(btrim(p_formula_fingerprint),'') is null
     or nullif(btrim(p_contrato_fingerprint),'') is null
     or nullif(btrim(p_motor_versao),'') is null then
    raise exception 'lote, semente e selos sao obrigatorios';
  end if;
  if exists(select 1 from clube_novo.build_linha_card where lote_teste_id=p_lote_id) then
    return public.otimizador_status_teste_v2(p_lote_id);
  end if;

  create temporary table _amostra_100_v12 on commit drop as
  with base as materialized (
    select c.card_id,c.extraido_em,c.extracao_id
    from clube_novo.carta_jogo c
    where c.roda_motor and c.pode_rodar_vinculos
    order by encode(extensions.digest(p_semente||':'||c.card_id,'sha256'),'hex')
    limit 180
  ), candidatos as materialized (
    select b.*,public.otimizador_carta_v2(b.card_id) pacote from base b
  ), aptas as (
    select *,row_number() over(
      order by encode(extensions.digest(p_semente||':'||card_id,'sha256'),'hex')) ordem
    from candidatos where coalesce((pacote->'gate'->>'pode_rodar')::boolean,false)
  ) select * from aptas where ordem<=100;

  select count(*) into v_cards from _amostra_100_v12;
  if v_cards<>100 then
    raise exception 'pre-voo recusado: somente % cartas aptas entre 180 candidatos',v_cards;
  end if;

  create temporary table _variantes_100_v12 on commit drop as
  select a.*,v.impeto_condicional_codigo,v.impeto_condicional_nivel
  from _amostra_100_v12 a
  cross join lateral (
    select null::integer impeto_condicional_codigo,null::smallint impeto_condicional_nivel
    where not exists(
      select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=a.card_id and ci.codigo_impeto is not null and ci.condicional)
    union all
    select ci.codigo_impeto,g.nivel::smallint
    from clube_novo.carta_impeto_jogo ci
    cross join lateral generate_series(
      1,clube_novo.impeto_nivel_maximo_v1(ci.codigo_impeto)::integer
    ) g(nivel)
    where ci.card_id=a.card_id and ci.codigo_impeto is not null and ci.condicional
  ) v;

  select encode(extensions.digest(p_semente||':'||string_agg(
    card_id||':'||coalesce(impeto_condicional_codigo::text,'-')||':'||
    coalesce(impeto_condicional_nivel::text,'-'),','
    order by ordem,impeto_condicional_codigo,impeto_condicional_nivel),'sha256'),'hex')
  into v_fp from _variantes_100_v12;

  insert into clube_novo.build_linha_card(
    card_id,funcao_id,posicao_id,impeto_condicional_codigo,impeto_condicional_nivel,
    carta_versao,carta_fingerprint,estado,pendencias,execucao_tipo,
    lote_teste_id,lote_teste_semente,lote_teste_fingerprint,amostra_ordem,sorteada_em,
    estado_otimizador,lote_estado,lote_estado_atualizado_em,
    otimizador_formula_fingerprint_esperado,otimizador_contrato_fingerprint_esperado,
    otimizador_motor_versao_esperada
  )
  select distinct a.card_id,fs.id,px.posicao_id,
    a.impeto_condicional_codigo,a.impeto_condicional_nivel,
    coalesce(a.extracao_id::text,a.extraido_em::text,'sem_versao'),
    encode(extensions.digest(a.pacote::text,'sha256'),'hex'),
    'pendente',array['teste_nao_publicado','bonificador_nao_executado']::text[],
    'teste_isolado',p_lote_id,p_semente,v_fp,a.ordem,v_quando,
    'pendente','parado',v_quando,p_formula_fingerprint,p_contrato_fingerprint,p_motor_versao
  from _variantes_100_v12 a
  join lateral (
    select cpp.posicao_id from clube_novo.carta_posicao_principal_jogo cpp where cpp.card_id=a.card_id
    union
    select cp.posicao_id from clube_novo.carta_posicao_jogo cp
    where cp.card_id=a.card_id and cp.nivel_aptidao>0
  ) px on true
  join clube_novo.posicao_jogo p on p.id=px.posicao_id and p.pode_rodar
  join clube_novo.funcao_sistema fs on fs.ativa and fs.pode_rodar and p.codigo_pt=any(fs.posicoes)
  order by a.ordem,fs.id,px.posicao_id,
           a.impeto_condicional_codigo,a.impeto_condicional_nivel;

  if (select count(distinct card_id) from clube_novo.build_linha_card where lote_teste_id=p_lote_id)<>100 then
    raise exception 'fila recusada: nao preservou exatamente 100 cards unicos';
  end if;
  return public.otimizador_status_teste_v2(p_lote_id);
end $$;

create or replace function public.otimizador_criar_amostra_controlada_50_v2(
  p_lote_id uuid,p_semente text,p_formula_fingerprint text,
  p_contrato_fingerprint text,p_motor_versao text,p_itens jsonb
) returns jsonb language plpgsql security definer set search_path='' as $$
declare
  v_qtd integer;
  v_fp text;
  v_quando timestamptz:=clock_timestamp();
begin
  if p_lote_id is null or nullif(btrim(p_semente),'') is null
     or nullif(btrim(p_formula_fingerprint),'') is null
     or nullif(btrim(p_contrato_fingerprint),'') is null
     or nullif(btrim(p_motor_versao),'') is null then
    raise exception 'lote, semente e selos sao obrigatorios';
  end if;
  if jsonb_typeof(p_itens)<>'array' or jsonb_array_length(p_itens)<>50 then
    raise exception 'amostra controlada deve conter exatamente 50 itens';
  end if;
  if exists(select 1 from clube_novo.build_linha_card where lote_teste_id=p_lote_id) then
    return public.otimizador_status_teste_v2(p_lote_id);
  end if;

  create temporary table _amostra_50_v12 on commit drop as
  with itens as (
    select ord::smallint ordem,nullif(btrim(x->>'card_id'),'') card_id,
      (x->>'funcao_id')::bigint funcao_id
    from jsonb_array_elements(p_itens) with ordinality t(x,ord)
  ), validados as (
    select i.ordem,i.card_id,i.funcao_id,c.extraido_em,c.extracao_id,
      public.otimizador_carta_v2(i.card_id) pacote,px.posicao_id
    from itens i
    join clube_novo.carta_jogo c on c.card_id=i.card_id
    join clube_novo.funcao_sistema fs on fs.id=i.funcao_id and fs.ativa and fs.pode_rodar
    join lateral (
      select z.posicao_id from (
        select cpp.posicao_id,0 prio from clube_novo.carta_posicao_principal_jogo cpp
        where cpp.card_id=i.card_id
        union all
        select cp.posicao_id,1 prio from clube_novo.carta_posicao_jogo cp
        where cp.card_id=i.card_id and cp.nivel_aptidao>0
      ) z
      join clube_novo.posicao_jogo p on p.id=z.posicao_id
      where p.pode_rodar and p.codigo_pt=any(fs.posicoes)
      order by z.prio,z.posicao_id limit 1
    ) px on true
    where c.roda_motor and c.pode_rodar_vinculos
  ) select * from validados;

  select count(*) into v_qtd from _amostra_50_v12;
  if v_qtd<>50 then raise exception 'pre-voo recusado: somente % dos 50 pares estao aptos',v_qtd; end if;
  if (select count(distinct card_id) from _amostra_50_v12)<>50 then
    raise exception 'amostra recusada: os 50 casos devem usar 50 cards distintos';
  end if;
  if exists(select 1 from _amostra_50_v12
            where not coalesce((pacote->'gate'->>'pode_rodar')::boolean,false)) then
    raise exception 'amostra recusada: existe card com gate fechado';
  end if;

  create temporary table _variantes_50_v12 on commit drop as
  select a.*,v.impeto_condicional_codigo,v.impeto_condicional_nivel
  from _amostra_50_v12 a
  cross join lateral (
    select null::integer impeto_condicional_codigo,null::smallint impeto_condicional_nivel
    where not exists(
      select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=a.card_id and ci.codigo_impeto is not null and ci.condicional)
    union all
    select ci.codigo_impeto,g.nivel::smallint
    from clube_novo.carta_impeto_jogo ci
    cross join lateral generate_series(
      1,clube_novo.impeto_nivel_maximo_v1(ci.codigo_impeto)::integer
    ) g(nivel)
    where ci.card_id=a.card_id and ci.codigo_impeto is not null and ci.condicional
  ) v;

  select encode(extensions.digest(p_semente||':'||string_agg(
    card_id||':'||funcao_id::text||':'||coalesce(impeto_condicional_codigo::text,'-')||':'||
    coalesce(impeto_condicional_nivel::text,'-'),','
    order by ordem,impeto_condicional_codigo,impeto_condicional_nivel),'sha256'),'hex')
  into v_fp from _variantes_50_v12;

  insert into clube_novo.build_linha_card(
    card_id,funcao_id,posicao_id,impeto_condicional_codigo,impeto_condicional_nivel,
    carta_versao,carta_fingerprint,estado,pendencias,execucao_tipo,
    lote_teste_id,lote_teste_semente,lote_teste_fingerprint,amostra_ordem,sorteada_em,
    estado_otimizador,lote_estado,lote_estado_atualizado_em,
    otimizador_formula_fingerprint_esperado,otimizador_contrato_fingerprint_esperado,
    otimizador_motor_versao_esperada
  )
  select a.card_id,a.funcao_id,a.posicao_id,
    a.impeto_condicional_codigo,a.impeto_condicional_nivel,
    coalesce(a.extracao_id::text,a.extraido_em::text,'sem_versao'),
    encode(extensions.digest(a.pacote::text,'sha256'),'hex'),
    'pendente',array['teste_nao_publicado','bonificador_nao_executado']::text[],
    'teste_isolado',p_lote_id,p_semente,v_fp,a.ordem,v_quando,
    'pendente','parado',v_quando,p_formula_fingerprint,p_contrato_fingerprint,p_motor_versao
  from _variantes_50_v12 a
  order by a.ordem,a.impeto_condicional_codigo,a.impeto_condicional_nivel;

  if (select count(distinct card_id) from clube_novo.build_linha_card where lote_teste_id=p_lote_id)<>50 then
    raise exception 'fila recusada: nao preservou exatamente 50 cards';
  end if;
  return public.otimizador_status_teste_v2(p_lote_id);
end $$;

revoke all on function public.otimizador_criar_amostra_teste_v3(uuid,text,text,text,text) from public,anon,authenticated;
revoke all on function public.otimizador_criar_amostra_controlada_50_v2(uuid,text,text,text,text,jsonb) from public,anon,authenticated;
grant execute on function public.otimizador_criar_amostra_teste_v3(uuid,text,text,text,text) to service_role;
grant execute on function public.otimizador_criar_amostra_controlada_50_v2(uuid,text,text,text,text,jsonb) to service_role;

commit;
