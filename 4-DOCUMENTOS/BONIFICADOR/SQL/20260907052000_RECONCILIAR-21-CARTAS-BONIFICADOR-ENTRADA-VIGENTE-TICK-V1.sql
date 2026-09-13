-- Reconcilia as 21 cartas cujo resultado V10 ja foi calculado com a entrada
-- vigente, mas cuja linha ainda conserva um fingerprint antigo.
--
-- Os motores permanecem independentes: o Otimizador prova o proprio resultado;
-- o Bonificador prova a propria entrada. Nada e apagado e nenhum bonus e
-- recalculado. O processamento de dados e feito depois, em ticks curtos.

begin;

set local lock_timeout = '5s';
set local statement_timeout = '120s';

do $migration$
declare
  v_def text;
  v_old text := $old$
    elsif o.carta_versao<>l.carta_versao or b.carta_versao<>l.carta_versao
       or o.carta_fingerprint<>l.carta_fingerprint or b.carta_fingerprint<>l.carta_fingerprint then
      v_estado:='erro'; v_motivo:='versao ou fingerprint da carta incompatível';
$old$;
  v_new text := $new$
    elsif o.carta_versao<>l.carta_versao or b.carta_versao<>l.carta_versao
       or b.carta_fingerprint is distinct from l.carta_fingerprint
       or b.entrada_bonificador_fingerprint is distinct from l.carta_fingerprint then
      v_estado:='erro'; v_motivo:='versao ou entrada do Bonificador incompatível';
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
    raise exception 'finalizador mudou: validacao independente dos motores nao reconhecida';
  end if;
end
$migration$;

do $migration$
declare
  v_def text;
  v_old text := $old$
  if v_otim.carta_fingerprint <> new.carta_fingerprint
     or v_bonus.carta_fingerprint <> new.carta_fingerprint
     or v_otim.carta_fingerprint <> v_bonus.carta_fingerprint then
    raise exception 'linha recusada: fingerprints da carta divergem';
$old$;
  v_new text := $new$
  if v_bonus.carta_fingerprint is distinct from new.carta_fingerprint
     or v_bonus.entrada_bonificador_fingerprint is distinct from new.carta_fingerprint then
    raise exception 'linha recusada: entrada do Bonificador diverge da linha';
$new$;
begin
  select pg_catalog.pg_get_functiondef(
    'clube_novo.validar_build_linha_publicavel_v3()'::regprocedure
  ) into v_def;

  if pg_catalog.strpos(v_def, v_new) > 0 then
    null;
  elsif pg_catalog.strpos(v_def, v_old) > 0 then
    execute pg_catalog.replace(v_def, v_old, v_new);
  else
    raise exception 'gate publicavel mudou: validacao independente dos motores nao reconhecida';
  end if;
end
$migration$;

create or replace function public.bonificador_reconciliar_entrada_vigente_tick_v1(
  p_lote_id uuid,
  p_limite integer default 20
)
returns jsonb
language plpgsql
security definer
set search_path = ''
set lock_timeout = '5s'
set statement_timeout = '120s'
as $function$
declare
  v_lote clube_novo.bonificador_correcao_lote_v1%rowtype;
  v_linha clube_novo.build_linha_card%rowtype;
  v_bonus clube_novo.build_bonificador%rowtype;
  v_fila clube_novo.build_finalizacao_fila_v1%rowtype;
  v_entrada jsonb;
  v_resposta jsonb;
  v_finalizacao jsonb;
  v_detalhes jsonb := '[]'::jsonb;
  v_erro text;
  v_fingerprint_anterior text;
  v_processadas integer := 0;
  v_vinculadas integer := 0;
  v_publicadas integer := 0;
  v_aguardando_otimizador integer := 0;
  v_retentar integer := 0;
  v_erros integer := 0;
  r record;
begin
  if p_lote_id is distinct from
     '0ddaa775-24c1-4293-86ca-77fe698aa044'::uuid then
    raise exception 'reconciliacao das 21 cartas: lote nao autorizado';
  end if;
  if p_limite is null or p_limite < 1 or p_limite > 50 then
    raise exception 'reconciliacao das 21 cartas: limite deve estar entre 1 e 50';
  end if;

  select * into v_lote
  from clube_novo.bonificador_correcao_lote_v1
  where id = p_lote_id;

  if v_lote.id is null
     or v_lote.motor_versao <> 'v10-0409-fisico-regra-aprovada-v1'
     or v_lote.formula_fingerprint <> '756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
     or v_lote.contrato_regua <> 'bonificador-regua-v3' then
    raise exception 'reconciliacao das 21 cartas: lote V10 selado nao localizado';
  end if;

  for r in
    select
      i.build_linha_card_id as linha_id,
      i.build_bonificador_id_novo as bonus_id,
      i.prioridade_grupo,
      i.prioridade_overall,
      i.prioridade_card_id,
      i.prioridade_funcao_id,
      i.prioridade_posicao_id,
      l.card_id,
      c.overall,
      entrada.payload as entrada_atual,
      case
        when l.build_otimizador_id is not null
         and l.estado_otimizador = 'concluido'
         and o.resultado_fingerprint is not distinct from l.snapshot_otimizador_fingerprint
         and o.carta_versao is not distinct from l.carta_versao
         and jsonb_typeof(o.atributos_finais) = 'array'
         and jsonb_array_length(o.atributos_finais) = 26
         and jsonb_typeof(coalesce(o.atributos_internos, o.atributos_finais)) = 'array'
         and jsonb_array_length(coalesce(o.atributos_internos, o.atributos_finais)) = 26
         and o.arows_snapshot is not null
        then 0 else 1
      end as ordem_publicavel
    from clube_novo.bonificador_correcao_item_v1 i
    join clube_novo.build_linha_card l
      on l.id = i.build_linha_card_id
    join clube_novo.build_bonificador b
      on b.id = i.build_bonificador_id_novo
    join clube_novo.carta_jogo c
      on c.card_id = l.card_id
    left join clube_novo.build_otimizador o
      on o.id = l.build_otimizador_id
    cross join lateral (
      select public.bonificador_carta_v2(l.card_id) as payload
    ) entrada
    where i.lote_id = p_lote_id
      and i.estado_item = 'preparado'
      and i.build_bonificador_id_novo is not null
      and l.estado = 'pendente'
      and l.execucao_tipo = 'producao'
      and l.lote_teste_id is null
      and not (l.pendencias @> array['teste_nao_publicado'::text])
      and l.build_bonificador_id is null
      and l.publicacao_fingerprint is null
      and l.publicada_em is null
      and l.nota_final is null
      and not exists (
        select 1
        from clube_novo.orcamento_revisao_linha_v1 rv
        where rv.linha_anterior_id = l.id
      )
      and coalesce((entrada.payload->>'pode_rodar')::boolean, false)
      and b.motor_versao = 'v10-0409-fisico-regra-aprovada-v1'
      and b.formula_fingerprint = '756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
      and b.contrato_versao = 'bonificador-regua-v3'
      and coalesce(cardinality(b.faltou), -1) = 0
      and b.carta_versao is not distinct from l.carta_versao
      and b.carta_versao is not distinct from entrada.payload->>'carta_versao'
      and b.carta_fingerprint is not distinct from entrada.payload->>'carta_fingerprint'
      and b.entrada_bonificador_fingerprint is not distinct from entrada.payload->>'carta_fingerprint'
      and l.carta_fingerprint is distinct from entrada.payload->>'carta_fingerprint'
    order by
      ordem_publicavel,
      i.prioridade_grupo nulls last,
      i.prioridade_overall desc nulls last,
      i.prioridade_card_id,
      i.prioridade_funcao_id,
      i.prioridade_posicao_id,
      i.build_linha_card_id
    limit p_limite
    for update of i skip locked
  loop
    begin
      -- A fila e travada antes da linha, a mesma ordem usada pelo cron de
      -- publicacao. Isso evita o ciclo de deadlock visto no ensaio integral.
      insert into clube_novo.build_finalizacao_fila_v1(
        linha_id,
        estado,
        prioridade,
        overall_origem,
        tentativas,
        origem_ultima,
        proxima_tentativa_em,
        atualizado_em
      ) values (
        r.linha_id,
        'aguardando',
        coalesce(r.prioridade_grupo, 10)::integer,
        r.overall,
        0,
        'reconciliacao_entrada_bonificador_21_cards_v1',
        pg_catalog.clock_timestamp(),
        pg_catalog.clock_timestamp()
      )
      on conflict (linha_id) do nothing;

      select * into v_fila
      from clube_novo.build_finalizacao_fila_v1
      where linha_id = r.linha_id
      for update;

      if v_fila.linha_id is null then
        raise exception 'fila de finalizacao nao foi localizada para a linha %', r.linha_id;
      end if;

      select * into v_linha
      from clube_novo.build_linha_card
      where id = r.linha_id
      for update;

      select * into v_bonus
      from clube_novo.build_bonificador
      where id = r.bonus_id;

      if v_linha.id is null or v_bonus.id is null then
        raise exception 'linha ou resultado desapareceu durante a reconciliacao';
      end if;

      v_entrada := public.bonificador_carta_v2(v_linha.card_id);
      if not coalesce((v_entrada->>'pode_rodar')::boolean, false)
         or v_linha.estado <> 'pendente'
         or v_linha.execucao_tipo <> 'producao'
         or v_linha.lote_teste_id is not null
         or v_linha.build_bonificador_id is not null
         or v_linha.publicada_em is not null
         or v_linha.nota_final is not null
         or v_bonus.carta_versao is distinct from v_linha.carta_versao
         or v_bonus.carta_versao is distinct from v_entrada->>'carta_versao'
         or v_bonus.carta_fingerprint is distinct from v_entrada->>'carta_fingerprint'
         or v_bonus.entrada_bonificador_fingerprint is distinct from v_entrada->>'carta_fingerprint'
         or v_linha.carta_fingerprint is not distinct from v_entrada->>'carta_fingerprint' then
        raise exception 'linha % mudou e nao e mais candidata exata', r.linha_id;
      end if;

      v_fingerprint_anterior := v_linha.carta_fingerprint;

      update clube_novo.build_linha_card
      set carta_fingerprint = v_entrada->>'carta_fingerprint',
          atualizado_em = pg_catalog.clock_timestamp()
      where id = v_linha.id
        and carta_fingerprint is not distinct from v_fingerprint_anterior;

      if not found then
        raise exception 'linha % mudou durante a atualizacao do selo', r.linha_id;
      end if;

      v_resposta := clube_novo.vincular_bonificador_v10_independente_v1(
        v_linha.id,
        v_linha.id,
        v_bonus.id,
        'reconciliacao_entrada_bonificador_21_cards_v1'
      );
      v_finalizacao := v_resposta->'finalizacao';

      if not coalesce((v_resposta->>'ok')::boolean, false)
         or not coalesce((v_resposta->>'vinculado')::boolean, false)
         or coalesce((v_resposta->>'clonado')::boolean, false)
         or not coalesce((v_finalizacao->>'ok')::boolean, false) then
        raise exception 'readback recusado na linha %: %', r.linha_id, v_resposta::text;
      end if;

      if not exists (
        select 1
        from clube_novo.build_linha_card x
        where x.id = v_linha.id
          and x.carta_fingerprint is not distinct from v_bonus.carta_fingerprint
          and x.build_bonificador_id = v_bonus.id
          and x.snapshot_bonificador_fingerprint is not distinct from v_bonus.resultado_fingerprint
      ) then
        raise exception 'readback final da linha % nao confirmou o vinculo', r.linha_id;
      end if;

      insert into clube_novo.build_finalizacao_evento_v1(linha_id, evento, detalhe)
      values (
        v_linha.id,
        'bonificador_v10_entrada_reconciliada',
        jsonb_build_object(
          'origem', 'reconciliacao_entrada_bonificador_21_cards_v1',
          'build_bonificador_id', v_bonus.id,
          'fingerprint_anterior', v_fingerprint_anterior,
          'fingerprint_vigente', v_bonus.carta_fingerprint,
          'build_otimizador_id_preservado', v_linha.build_otimizador_id,
          'resultado_recalculado', false,
          'resultado_clonado', false
        )
      );

      v_processadas := v_processadas + 1;
      v_vinculadas := v_vinculadas + 1;
      if v_finalizacao->>'estado' in ('publicada', 'ja_publicada') then
        v_publicadas := v_publicadas + 1;
      else
        v_aguardando_otimizador := v_aguardando_otimizador + 1;
      end if;
    exception
      when deadlock_detected or lock_not_available or query_canceled or serialization_failure then
        get stacked diagnostics v_erro = message_text;
        v_retentar := v_retentar + 1;
        v_detalhes := v_detalhes || jsonb_build_array(jsonb_build_object(
          'linha_id', r.linha_id,
          'estado', 'retentar',
          'erro', v_erro
        ));
      when others then
        get stacked diagnostics v_erro = message_text;
        v_erros := v_erros + 1;
        v_detalhes := v_detalhes || jsonb_build_array(jsonb_build_object(
          'linha_id', r.linha_id,
          'estado', 'erro',
          'erro', v_erro
        ));
    end;
  end loop;

  return jsonb_build_object(
    'ok', v_erros = 0,
    'lote_id', p_lote_id,
    'limite', p_limite,
    'processadas', v_processadas,
    'vinculadas', v_vinculadas,
    'publicadas', v_publicadas,
    'aguardando_otimizador', v_aguardando_otimizador,
    'retentar', v_retentar,
    'erros', v_erros,
    'detalhes', v_detalhes
  );
end
$function$;

revoke all on function public.bonificador_reconciliar_entrada_vigente_tick_v1(uuid, integer)
from public, anon, authenticated;
grant execute on function public.bonificador_reconciliar_entrada_vigente_tick_v1(uuid, integer)
to service_role;

comment on function public.bonificador_reconciliar_entrada_vigente_tick_v1(uuid, integer) is
  'Reconcilia em blocos curtos as 21 cartas ja calculadas com a entrada Bonificador vigente; preserva o Otimizador e nao recalcula resultados.';

notify pgrst, 'reload schema';

commit;
