-- ÍMPETOS ADICIONAIS V14
-- Fonte canônica: somente clube_novo.impeto_jogo + impeto_atributo_jogo.
-- Não lê os Ímpetos já equipados na carta para formar candidatos.
-- Não inicia lote, não reserva linha e não publica resultado.

begin;

do $$
begin
  if to_regclass('clube_novo.impeto_jogo') is null
     or to_regclass('clube_novo.impeto_atributo_jogo') is null
     or to_regclass('clube_novo.atributo_ordem_otimizador') is null
     or to_regprocedure('clube_novo.impeto_nivel_maximo_v1(integer)') is null then
    raise exception 'V14 recusada: catálogo físico de Ímpetos ou função de nível ausente';
  end if;
end $$;

create or replace function public.otimizador_regua_v2()
returns jsonb language plpgsql stable security definer set search_path='' as $$
declare
  v_versao integer;
  v_atributos integer;
  v_funcoes integer;
  v_adicionais_validos integer;
  v_pacotes_total integer;
  v_pacotes_total_validos integer;
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

  -- Regra aprovada: todos os efeitos são +1 e o Ímpeto não é condicional.
  -- Exceção explícita: Pacote total, condicional, mas todos os efeitos são +3.
  select count(*) into v_adicionais_validos
  from clube_novo.impeto_jogo i
  where (
    i.condicional is false
    and exists (
      select 1 from clube_novo.impeto_atributo_jogo a
      where a.codigo_impeto=i.codigo_jogo
    )
    and not exists (
      select 1 from clube_novo.impeto_atributo_jogo a
      where a.codigo_impeto=i.codigo_jogo and a.delta<>1
    )
  ) or (
    i.nome_pt='Pacote total'
    and i.condicional is true
    and exists (
      select 1 from clube_novo.impeto_atributo_jogo a
      where a.codigo_impeto=i.codigo_jogo
    )
    and not exists (
      select 1 from clube_novo.impeto_atributo_jogo a
      where a.codigo_impeto=i.codigo_jogo and a.delta<>3
    )
  );
  select count(*) into v_pacotes_total
  from clube_novo.impeto_jogo
  where nome_pt='Pacote total';
  select count(*) into v_pacotes_total_validos
  from clube_novo.impeto_jogo i
  where i.nome_pt='Pacote total'
    and i.condicional is true
    and exists (
      select 1 from clube_novo.impeto_atributo_jogo a
      where a.codigo_impeto=i.codigo_jogo
    )
    and not exists (
      select 1 from clube_novo.impeto_atributo_jogo a
      where a.codigo_impeto=i.codigo_jogo and a.delta<>3
    );
  if v_adicionais_validos<1 then
    v_motivos:=array_append(v_motivos,'catalogo_impetos_adicionais_ausente');
  end if;
  if v_pacotes_total<>v_pacotes_total_validos then
    v_motivos:=array_append(v_motivos,'pacote_total_excecao_invalido');
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
      from clube_novo.impeto_jogo i),
    'impetos_adicionais',(select coalesce(jsonb_agg(jsonb_build_object(
      'codigo_impeto',i.codigo_jogo,
      'nome_pt',i.nome_pt,
      'regra',case when i.nome_pt='Pacote total' then 'pacote_total_excecao' else 'delta_mais_um' end,
      'slots',jsonb_build_array(1,2),
      'efeitos',coalesce((select jsonb_agg(jsonb_build_object(
        'indice_otimizador',o.indice_otimizador,'codigo_atributo',a.codigo_atributo,'delta',a.delta)
        order by o.indice_otimizador) from clube_novo.impeto_atributo_jogo a
        join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=a.codigo_atributo
        where a.codigo_impeto=i.codigo_jogo),'[]'::jsonb)
    ) order by i.codigo_jogo),'[]'::jsonb)
    from clube_novo.impeto_jogo i
    where (
      i.condicional is false
      and exists (select 1 from clube_novo.impeto_atributo_jogo a where a.codigo_impeto=i.codigo_jogo)
      and not exists (select 1 from clube_novo.impeto_atributo_jogo a where a.codigo_impeto=i.codigo_jogo and a.delta<>1)
    ) or (
      i.nome_pt='Pacote total'
      and i.condicional is true
      and exists (select 1 from clube_novo.impeto_atributo_jogo a where a.codigo_impeto=i.codigo_jogo)
      and not exists (select 1 from clube_novo.impeto_atributo_jogo a where a.codigo_impeto=i.codigo_jogo and a.delta<>3)
    ))
  );
end $$;

revoke all on function public.otimizador_regua_v2() from public,anon,authenticated;
grant execute on function public.otimizador_regua_v2() to service_role;

commit;
