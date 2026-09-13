-- Rollback da refila Chute súbito V1.
-- Só aceita desfazer enquanto o lote corretivo continua pausado, integralmente
-- pendente e sem qualquer resultado/reserva. Os Builds e as publicações antigas
-- são restaurados das fotografias guardadas nos eventos da própria correção.

begin;

set local statement_timeout = '120s';
set local lock_timeout = '10s';

do $rollback$
declare
  v_lote_origem constant uuid := 'ddbcbc86-1ae7-4b95-b9f0-22601f41b61d';
  v_lote_novo constant uuid := '7b1d16ea-012a-45a6-b3f6-639f8565f76c';
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_agora timestamptz := clock_timestamp();
  v_afetadas integer;
begin
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = v_lote_novo
  for update;

  if not found or v_lote.estado <> 'pausado' or v_lote.linhas <> 36 then
    raise exception 'Rollback Chute súbito V1 recusado: lote corretivo ausente ou já mudou';
  end if;

  create temporary table _rollback_chute_subito_v1 on commit drop as
  select
    e.linha_id,
    e.detalhe->'linha_antes' as linha_antes,
    e.detalhe->'fila_antes' as fila_antes,
    e.detalhe->'publicacao_ativa_antes' as ativa_antes,
    e.detalhe->'delta_publico_antes' as delta_antes,
    e.detalhe->'finalizacao_antes' as finalizacao_antes
  from clube_novo.otimizador_evento_producao_v3 e
  where e.lote_id = v_lote_novo
    and e.evento = 'linha_reaberta_chute_subito_v1';

  if (select count(*) from _rollback_chute_subito_v1) <> 36
     or exists (
       select 1
       from _rollback_chute_subito_v1 r
       join clube_novo.build_linha_card l on l.id = r.linha_id
       join clube_novo.otimizador_lote_producao_linha_v3 q
         on q.lote_id = v_lote_novo and q.linha_id = r.linha_id
       where l.estado_otimizador <> 'pendente'
          or l.build_otimizador_id is not null
          or l.build_bonificador_id is not null
          or q.reserva_token is not null
          or q.worker_id is not null
          or q.reservada_em is not null
          or q.finalizada_em is not null
          or q.resultado_fingerprint is not null
     ) then
    raise exception 'Rollback Chute súbito V1 recusado: lote já tem cálculo, reserva ou escopo divergente';
  end if;

  delete from clube_novo.build_finalizacao_fila_v1 f
  using _rollback_chute_subito_v1 r
  where f.linha_id = r.linha_id;

  delete from clube_novo.otimizador_lote_producao_linha_v3 q
  using _rollback_chute_subito_v1 r
  where q.lote_id = v_lote_novo and q.linha_id = r.linha_id;

  update clube_novo.build_linha_card l
     set lote_producao_id = (r.linha_antes->>'lote_producao_id')::uuid,
         build_otimizador_id = nullif(r.linha_antes->>'build_otimizador_id', '')::bigint,
         build_bonificador_id = nullif(r.linha_antes->>'build_bonificador_id', '')::bigint,
         estado_otimizador = r.linha_antes->>'estado_otimizador',
         erro_otimizador = r.linha_antes->>'erro_otimizador',
         otimizador_iniciado_em = nullif(r.linha_antes->>'otimizador_iniciado_em', '')::timestamptz,
         otimizador_finalizado_em = nullif(r.linha_antes->>'otimizador_finalizado_em', '')::timestamptz,
         lote_estado = r.linha_antes->>'lote_estado',
         lote_estado_atualizado_em = nullif(r.linha_antes->>'lote_estado_atualizado_em', '')::timestamptz,
         lote_falha = r.linha_antes->>'lote_falha',
         otimizador_formula_fingerprint_esperado = r.linha_antes->>'otimizador_formula_fingerprint_esperado',
         otimizador_contrato_fingerprint_esperado = r.linha_antes->>'otimizador_contrato_fingerprint_esperado',
         otimizador_motor_versao_esperada = r.linha_antes->>'otimizador_motor_versao_esperada',
         pendencias = coalesce(
           array(select jsonb_array_elements_text(r.linha_antes->'pendencias')),
           '{}'::text[]
         ),
         publicacao_fingerprint = r.linha_antes->>'publicacao_fingerprint',
         publicada_em = nullif(r.linha_antes->>'publicada_em', '')::timestamptz,
         atributos_snapshot = nullif(r.linha_antes->'atributos_snapshot', 'null'::jsonb),
         atributos_snapshot_fingerprint = r.linha_antes->>'atributos_snapshot_fingerprint',
         snapshot_otimizador_fingerprint = r.linha_antes->>'snapshot_otimizador_fingerprint',
         snapshot_bonificador_fingerprint = r.linha_antes->>'snapshot_bonificador_fingerprint',
         otimizador_motor_versao = r.linha_antes->>'otimizador_motor_versao',
         otimizador_contrato_versao = r.linha_antes->>'otimizador_contrato_versao',
         bonificador_motor_versao = r.linha_antes->>'bonificador_motor_versao',
         bonificador_contrato_versao = r.linha_antes->>'bonificador_contrato_versao',
         bonificador_lote_publicacao_id = nullif(r.linha_antes->>'bonificador_lote_publicacao_id', '')::uuid,
         nota_contrato = r.linha_antes->>'nota_contrato',
         nota_otimizador_resultado_fingerprint = r.linha_antes->>'nota_otimizador_resultado_fingerprint',
         nota_bonificador_resultado_fingerprint = r.linha_antes->>'nota_bonificador_resultado_fingerprint',
         nota_carta_fingerprint = r.linha_antes->>'nota_carta_fingerprint',
         nota_formula_fingerprint = r.linha_antes->>'nota_formula_fingerprint',
         nota_contrato_fingerprint = r.linha_antes->>'nota_contrato_fingerprint',
         nota_bruta_selada = nullif(r.linha_antes->>'nota_bruta_selada', '')::numeric,
         nota_bonus_pe = nullif(r.linha_antes->>'nota_bonus_pe', '')::numeric,
         nota_bonus_fisico_total = nullif(r.linha_antes->>'nota_bonus_fisico_total', '')::numeric,
         nota_bonus_posicao = nullif(r.linha_antes->>'nota_bonus_posicao', '')::numeric,
         nota_bonus_playstyle_1 = nullif(r.linha_antes->>'nota_bonus_playstyle_1', '')::numeric,
         nota_bonus_playstyle_2 = nullif(r.linha_antes->>'nota_bonus_playstyle_2', '')::numeric,
         nota_bonus_ia = nullif(r.linha_antes->>'nota_bonus_ia', '')::numeric,
         nota_bonus_outros = nullif(r.linha_antes->'nota_bonus_outros', 'null'::jsonb),
         nota_bonus_total = nullif(r.linha_antes->>'nota_bonus_total', '')::numeric,
         nota_numerador = nullif(r.linha_antes->>'nota_numerador', '')::numeric,
         nota_denominador = nullif(r.linha_antes->>'nota_denominador', '')::numeric,
         nota_do_motor = nullif(r.linha_antes->>'nota_do_motor', '')::numeric,
         nota_final = nullif(r.linha_antes->>'nota_final', '')::numeric,
         nota_normalizacao_fingerprint = r.linha_antes->>'nota_normalizacao_fingerprint',
         nota_calculo_fingerprint = r.linha_antes->>'nota_calculo_fingerprint',
         nota_publicacao_fingerprint_v1 = r.linha_antes->>'nota_publicacao_fingerprint_v1',
         nota_publicada_em_v1 = nullif(r.linha_antes->>'nota_publicada_em_v1', '')::timestamptz,
         nota_calculada_em = nullif(r.linha_antes->>'nota_calculada_em', '')::timestamptz
  from _rollback_chute_subito_v1 r
  where l.id = r.linha_id;
  get diagnostics v_afetadas = row_count;
  if v_afetadas <> 36 then
    raise exception 'Rollback Chute súbito V1 recusado: restaurou % linhas, esperadas 36', v_afetadas;
  end if;

  insert into clube_novo.otimizador_lote_producao_linha_v3
  select (x).*
  from _rollback_chute_subito_v1 r
  cross join lateral jsonb_populate_record(
    null::clube_novo.otimizador_lote_producao_linha_v3,
    r.fila_antes
  ) x;

  insert into clube_novo.build_publicacao_linha_ativa_v1
  select (x).*
  from _rollback_chute_subito_v1 r
  cross join lateral jsonb_populate_record(
    null::clube_novo.build_publicacao_linha_ativa_v1,
    r.ativa_antes
  ) x
  where r.ativa_antes is not null
    and r.ativa_antes <> 'null'::jsonb
  on conflict (linha_id) do nothing;

  insert into clube_novo.build_pontuacao_final_v2_delta_v1
  select (x).*
  from _rollback_chute_subito_v1 r
  cross join lateral jsonb_populate_record(
    null::clube_novo.build_pontuacao_final_v2_delta_v1,
    r.delta_antes
  ) x
  where r.delta_antes is not null
    and r.delta_antes <> 'null'::jsonb
  on conflict (linha_id) do nothing;

  insert into clube_novo.build_finalizacao_fila_v1
  select (x).*
  from _rollback_chute_subito_v1 r
  cross join lateral jsonb_populate_record(
    null::clube_novo.build_finalizacao_fila_v1,
    r.finalizacao_antes
  ) x
  where r.finalizacao_antes is not null
    and r.finalizacao_antes <> 'null'::jsonb
  on conflict (linha_id) do nothing;

  update clube_novo.otimizador_lote_producao_v3 l
     set linhas = (
           select count(*)::integer
           from clube_novo.otimizador_lote_producao_linha_v3 q
           where q.lote_id = v_lote_origem
         ),
         atualizado_em = v_agora
   where l.id = v_lote_origem;

  delete from clube_novo.otimizador_evento_producao_v3 where lote_id = v_lote_novo;
  delete from clube_novo.otimizador_lote_producao_carta_v3 where lote_id = v_lote_novo;
  delete from clube_novo.otimizador_lote_producao_v3 where id = v_lote_novo;
end
$rollback$;

alter table clube_novo.otimizador_evento_producao_v3
  drop constraint if exists otimizador_evento_producao_v3_evento_check;

alter table clube_novo.otimizador_evento_producao_v3
  add constraint otimizador_evento_producao_v3_evento_check
  check (evento = any (array[
    'lote_criado', 'lote_iniciado', 'lote_retomado', 'pausa_solicitada',
    'lote_pausado', 'encerramento_solicitado', 'lote_encerrado',
    'linha_reservada', 'linha_concluida', 'linha_bloqueada',
    'lote_concluido', 'lote_falhou', 'preparo_integral_criado',
    'preparo_fatia_concluida', 'preparo_pausa_solicitada', 'preparo_pausado',
    'preparo_retomado', 'preparo_integral_concluido', 'preparo_falhou',
    'linha_importada_json_local', 'lote_correcao_impeto_adicional_v8',
    'linha_reaberta_impeto_adicional_v8',
    'lote_correcao_impeto_adicional_v10',
    'linha_reaberta_impeto_adicional_v10'
  ]));

commit;
