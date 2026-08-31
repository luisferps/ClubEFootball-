-- V13: os dois contadores são obrigatórios em cada resultado do Otimizador.
-- Não há valor padrão: uma conclusão sem telemetria deve falhar fechada.

do $$
begin
  if exists (
    select 1
    from clube_novo.build_otimizador
    where builds_comparadas is null or builds_possiveis is null
  ) then
    raise exception 'existem builds sem os dois contadores; classifique-os antes de aplicar a V13';
  end if;
end $$;

alter table clube_novo.build_otimizador
  alter column builds_comparadas set not null,
  alter column builds_possiveis set not null;

alter table clube_novo.build_otimizador
  drop constraint if exists build_otimizador_builds_comparadas_nao_negativas;
alter table clube_novo.build_otimizador
  drop constraint if exists build_otimizador_builds_possiveis_v12_check;
alter table clube_novo.build_otimizador
  drop constraint if exists build_otimizador_contadores_v13_check;
alter table clube_novo.build_otimizador
  add constraint build_otimizador_contadores_v13_check check (
    builds_comparadas >= 0
    and builds_possiveis >= 0
    and trunc(builds_possiveis) = builds_possiveis
    and builds_comparadas <= builds_possiveis
  );

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
  if jsonb_typeof(p_resultado->'builds_comparadas') <> 'number'
     or coalesce(p_resultado->>'builds_comparadas','') !~ '^[0-9]+$' then
    raise exception 'telemetria builds_comparadas invalida';
  end if;
  if jsonb_typeof(p_resultado->'builds_possiveis') <> 'number'
     or coalesce(p_resultado->>'builds_possiveis','') !~ '^[0-9]+$' then
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

revoke all on function public.otimizador_concluir_linha_teste_v2(bigint,uuid,jsonb)
  from public,anon,authenticated;
grant execute on function public.otimizador_concluir_linha_teste_v2(bigint,uuid,jsonb)
  to service_role;
