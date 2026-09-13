-- O resultado ligado na linha e a autoridade do Bonificador.
-- Resultado preparado antigo so pode servir de fallback quando todos os selos
-- de entrada continuam identicos. Nada e apagado e nenhum bonus e recalculado aqui.

begin;

set local lock_timeout = '5s';
set local statement_timeout = '120s';

do $migration$
declare
  v_def text;
  v_old text := $old$
  select i.build_bonificador_id_novo into v_bonus_id
  from clube_novo.bonificador_correcao_item_v1 i
  join clube_novo.bonificador_correcao_lote_v1 lo on lo.id=i.lote_id
  join clube_novo.build_bonificador bx on bx.id=i.build_bonificador_id_novo
  where i.build_linha_card_id=l.id and i.estado_item='preparado'
    and bx.motor_versao='v10-0409-fisico-regra-aprovada-v1'
    and bx.formula_fingerprint='756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
    and bx.contrato_versao='bonificador-regua-v3'
  order by lo.criado_em desc,i.preparado_em desc limit 1;
  if v_bonus_id is null then
    select bx.id into v_bonus_id
    from clube_novo.build_bonificador bx
    where bx.id=l.build_bonificador_id
      and bx.motor_versao='v10-0409-fisico-regra-aprovada-v1'
      and bx.formula_fingerprint='756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
      and bx.contrato_versao='bonificador-regua-v3';
  end if;
$old$;
  v_new text := $new$
  select bx.id into v_bonus_id
  from clube_novo.build_bonificador bx
  where bx.id=l.build_bonificador_id
    and bx.motor_versao='v10-0409-fisico-regra-aprovada-v1'
    and bx.formula_fingerprint='756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
    and bx.contrato_versao='bonificador-regua-v3'
    and bx.carta_versao is not distinct from l.carta_versao
    and bx.carta_fingerprint is not distinct from l.carta_fingerprint
    and bx.entrada_bonificador_fingerprint is not distinct from l.carta_fingerprint
    and coalesce(cardinality(bx.faltou), -1)=0
  limit 1;
  if v_bonus_id is null then
    select i.build_bonificador_id_novo into v_bonus_id
    from clube_novo.bonificador_correcao_item_v1 i
    join clube_novo.bonificador_correcao_lote_v1 lo on lo.id=i.lote_id
    join clube_novo.build_bonificador bx on bx.id=i.build_bonificador_id_novo
    where i.build_linha_card_id=l.id and i.estado_item='preparado'
      and bx.motor_versao='v10-0409-fisico-regra-aprovada-v1'
      and bx.formula_fingerprint='756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
      and bx.contrato_versao='bonificador-regua-v3'
      and bx.carta_versao is not distinct from l.carta_versao
      and bx.carta_fingerprint is not distinct from l.carta_fingerprint
      and bx.entrada_bonificador_fingerprint is not distinct from l.carta_fingerprint
      and coalesce(cardinality(bx.faltou), -1)=0
    order by lo.criado_em desc,i.preparado_em desc limit 1;
  end if;
$new$;
begin
  select pg_catalog.pg_get_functiondef(
    'clube_novo.finalizar_publicar_linha_v1(bigint,text)'::regprocedure
  ) into v_def;

  if pg_catalog.strpos(v_def, v_new) > 0 then
    null;
  elsif pg_catalog.strpos(v_def, v_old) > 0 then
    execute pg_catalog.replace(v_def, v_old, v_new);
  else
    raise exception 'finalizador mudou: bloco de resolucao do Bonificador nao reconhecido';
  end if;
end
$migration$;

do $migration$
declare
  v_def text;
  v_old text := '     or cardinality(v_bonus.faltou) <> 0 then';
  v_new text := '     or coalesce(cardinality(v_bonus.faltou), -1) <> 0 then';
begin
  select pg_catalog.pg_get_functiondef(
    'clube_novo.vincular_bonificador_v10_independente_v1(bigint,bigint,bigint,text)'::regprocedure
  ) into v_def;

  if pg_catalog.strpos(v_def, v_new) > 0 then
    null;
  elsif pg_catalog.strpos(v_def, v_old) > 0 then
    execute pg_catalog.replace(v_def, v_old, v_new);
  else
    raise exception 'vinculador mudou: validacao de campos faltantes nao reconhecida';
  end if;
end
$migration$;

-- Registra de forma reproduzivel a priorizacao aplicada durante o backfill:
-- primeiro os pares que ja possuem Otimizador integralmente compativel.
do $migration$
declare
  v_def text;
  v_old_join text := $old$
    join clube_novo.build_linha_card destino
      on destino.id = coalesce(rv.linha_nova_id, i.build_linha_card_id)
    where i.lote_id = p_lote_id
$old$;
  v_new_join text := $new$
    join clube_novo.build_linha_card destino
      on destino.id = coalesce(rv.linha_nova_id, i.build_linha_card_id)
    left join clube_novo.build_otimizador otim
      on otim.id = destino.build_otimizador_id
    where i.lote_id = p_lote_id
$new$;
  v_old_order text := $old$
    order by
      i.prioridade_grupo,
$old$;
  v_new_order text := $new$
    order by
      case when destino.build_otimizador_id is not null
                  and destino.estado_otimizador = 'concluido'
                  and otim.resultado_fingerprint is not distinct from destino.snapshot_otimizador_fingerprint
                  and jsonb_typeof(otim.atributos_finais) = 'array'
                  and jsonb_array_length(otim.atributos_finais) = 26
                  and jsonb_typeof(coalesce(otim.atributos_internos, otim.atributos_finais)) = 'array'
                  and jsonb_array_length(coalesce(otim.atributos_internos, otim.atributos_finais)) = 26
                  and otim.arows_snapshot is not null
             then 0 else 1 end,
      i.prioridade_grupo,
$new$;
begin
  select pg_catalog.pg_get_functiondef(
    'public.bonificador_vincular_preparados_tick_v1(uuid,integer)'::regprocedure
  ) into v_def;

  if pg_catalog.strpos(v_def, v_new_join) = 0 then
    if pg_catalog.strpos(v_def, v_old_join) = 0 then
      raise exception 'tick mudou: bloco de join nao reconhecido';
    end if;
    v_def := pg_catalog.replace(v_def, v_old_join, v_new_join);
  end if;

  if pg_catalog.strpos(v_def, v_new_order) = 0 then
    if pg_catalog.strpos(v_def, v_old_order) = 0 then
      raise exception 'tick mudou: bloco de ordenacao nao reconhecido';
    end if;
    v_def := pg_catalog.replace(v_def, v_old_order, v_new_order);
  end if;

  execute v_def;
end
$migration$;

notify pgrst, 'reload schema';

commit;
