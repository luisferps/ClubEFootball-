-- Reabre somente Totti, Adriano e Shevchenko depois da prova física do
-- Chute súbito (skill_id 2457, Player.bin bit 639/w1).
--
-- A fila integral principal já foi fotografada e está sendo calculada em
-- outra máquina. Por isso esta correção NÃO altera o cabeçalho, a régua nem
-- os selos daquele lote. Ela cria um lote corretivo independente, pausado e
-- pronto para gerar um pacote local novo com as 36 linhas afetadas.
--
-- O histórico dos Builds antigos é preservado. Só as ligações/publicações
-- ativas das 36 linhas são retiradas enquanto o novo cálculo não termina.

begin;

set local statement_timeout = '120s';
set local lock_timeout = '10s';

do $$
begin
  if to_regclass('clube_novo.otimizador_lote_producao_v3') is null
     or to_regclass('clube_novo.otimizador_lote_producao_carta_v3') is null
     or to_regclass('clube_novo.otimizador_lote_producao_linha_v3') is null
     or to_regclass('clube_novo.build_linha_card') is null
     or to_regclass('clube_novo.build_publicacao_linha_ativa_v1') is null
     or to_regclass('clube_novo.build_pontuacao_final_v2_delta_v1') is null
     or to_regclass('clube_novo.build_finalizacao_fila_v1') is null
     or to_regclass('clube_novo.otimizador_evento_producao_v3') is null
     or to_regprocedure('public.otimizador_regua_v2()') is null
     or to_regprocedure('public.otimizador_carta_v3(text)') is null
     or to_regprocedure('clube_novo.otimizador_producao_contrato_fingerprint_v3(jsonb)') is null then
    raise exception 'Chute súbito V1 recusada: contratos produtivos necessários ausentes';
  end if;
end
$$;

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
    'linha_reaberta_impeto_adicional_v10',
    'lote_correcao_chute_subito_v1',
    'linha_reaberta_chute_subito_v1'
  ]));

do $correcao$
declare
  v_lote_origem constant uuid := 'ddbcbc86-1ae7-4b95-b9f0-22601f41b61d';
  v_lote_novo constant uuid := '7b1d16ea-012a-45a6-b3f6-639f8565f76c';
  v_formula constant text := '5a7446b3dfa7b6b45ece1f611b1751fc1221f06e76c53cbd0827a83962c76e89';
  v_motor constant text := 'otimizador-fila-producao-v3-local-20260903-goleiro-e-condicional-v11';
  v_agora timestamptz := clock_timestamp();
  v_origem clube_novo.otimizador_lote_producao_v3%rowtype;
  v_regua jsonb;
  v_contrato_fp text;
  v_fingerprint text;
  v_linhas integer;
  v_cartas integer;
  v_afetadas integer;
  v_publicas integer;
begin
  select * into v_origem
  from clube_novo.otimizador_lote_producao_v3
  where id = v_lote_origem
  for update;

  if not found
     or v_origem.tipo_lote <> 'integral'
     or v_origem.estado <> 'pausado'
     or v_origem.pode_publicar is distinct from false
     or v_origem.formula_fingerprint <> v_formula
     or v_origem.motor_versao <> v_motor then
    raise exception 'Chute súbito V1 recusada: lote de origem não está integral, pausado e selado como esperado';
  end if;

  if exists (
    select 1
    from clube_novo.otimizador_evento_producao_v3 e
    where e.evento = 'lote_correcao_chute_subito_v1'
      and e.detalhe->>'lote_origem' = v_lote_origem::text
  ) or exists (
    select 1 from clube_novo.otimizador_lote_producao_v3 where id = v_lote_novo
  ) then
    raise exception 'Chute súbito V1 recusada: esta correção já foi aplicada';
  end if;

  select public.otimizador_regua_v2() into v_regua;
  v_contrato_fp := clube_novo.otimizador_producao_contrato_fingerprint_v3(v_regua);

  if not coalesce((v_regua->'gate'->>'pode_rodar')::boolean, false)
     or not exists (
       select 1
       from jsonb_array_elements(coalesce(v_regua->'habilidades', '[]'::jsonb)) h
       where (h->>'skill_id')::integer = 2457
         and h->>'tipo' = 'especial'
         and coalesce((h->>'fabricavel')::boolean, true) is false
         and coalesce((h->>'pode_rodar')::boolean, false) is true
         and exists (
           select 1
           from jsonb_array_elements(coalesce(h->'efeitos', '[]'::jsonb)) e
           where (e->>'indice_otimizador')::integer = 6
             and (e->>'pct')::numeric = 5
             and coalesce((e->>'flat')::numeric, 0) = 0
         )
     ) then
    raise exception 'Chute súbito V1 recusada: régua não confirma skill 2457 especial, não fabricável e Finalização +5%%';
  end if;

  create temporary table _cartas_chute_subito_v1 on commit drop as
  select
    ids.card_id,
    public.otimizador_carta_v3(ids.card_id) as entrada_otimizador
  from (values
    ('88045755960771'::text),
    ('88045755960841'::text),
    ('88045755964138'::text)
  ) ids(card_id);

  if (select count(*) from _cartas_chute_subito_v1) <> 3
     or exists (
       select 1
       from _cartas_chute_subito_v1 c
       where not coalesce((c.entrada_otimizador->'gate'->>'pode_rodar')::boolean, false)
          or (c.entrada_otimizador->'cardinalidades'->>'habilidades')::integer <> 10
          or not exists (
            select 1
            from jsonb_array_elements(coalesce(c.entrada_otimizador->'habilidades', '[]'::jsonb)) h
            where (h->>'skill_id')::integer = 2457
              and h->>'tipo' = 'especial'
              and coalesce((h->>'fabricavel')::boolean, true) is false
          )
     ) then
    raise exception 'Chute súbito V1 recusada: as três cartas não confirmam gate, 10 habilidades e skill 2457';
  end if;

  create temporary table _alvo_chute_subito_v1 on commit drop as
  select
    l.id as linha_id,
    l.card_id,
    q.ordem_fila as ordem_origem,
    q.overall_snapshot,
    c.entrada_otimizador,
    encode(extensions.digest(convert_to(c.entrada_otimizador::text, 'UTF8'), 'sha256'), 'hex') as entrada_fingerprint_nova,
    s.carta_versao_bonificador,
    s.carta_fingerprint_bonificador,
    to_jsonb(l) as linha_antes,
    to_jsonb(q) as fila_antes,
    (select to_jsonb(a) from clube_novo.build_publicacao_linha_ativa_v1 a where a.linha_id = l.id) as ativa_antes,
    (select to_jsonb(d) from clube_novo.build_pontuacao_final_v2_delta_v1 d where d.linha_id = l.id) as delta_antes,
    (select to_jsonb(f) from clube_novo.build_finalizacao_fila_v1 f where f.linha_id = l.id) as finalizacao_antes
  from clube_novo.build_linha_card l
  join clube_novo.otimizador_lote_producao_linha_v3 q
    on q.lote_id = v_lote_origem and q.linha_id = l.id
  join clube_novo.otimizador_lote_producao_carta_v3 s
    on s.lote_id = q.lote_id and s.card_id = l.card_id
  join _cartas_chute_subito_v1 c on c.card_id = l.card_id
  where l.card_id in ('88045755960771', '88045755960841', '88045755964138');

  select count(*)::integer, count(distinct card_id)::integer
  into v_linhas, v_cartas
  from _alvo_chute_subito_v1;

  if v_linhas <> 36 or v_cartas <> 3 then
    raise exception 'Chute súbito V1 recusada: esperadas 36 linhas de 3 cartas, recebidas % de %', v_linhas, v_cartas;
  end if;

  if exists (
    select 1
    from _alvo_chute_subito_v1 a
    join clube_novo.build_linha_card l on l.id = a.linha_id
    join clube_novo.otimizador_lote_producao_linha_v3 q
      on q.lote_id = v_lote_origem and q.linha_id = a.linha_id
    where l.estado <> 'pendente'
       or l.estado_otimizador not in ('concluido', 'bloqueado')
       or q.reserva_token is not null
       or q.worker_id is not null
       or q.reservada_em is not null
  ) then
    raise exception 'Chute súbito V1 recusada: alguma linha alvo mudou, está reservada ou não está reabrível';
  end if;

  if exists (
    select 1
    from _alvo_chute_subito_v1 a
    where a.entrada_fingerprint_nova = a.fila_antes->>'entrada_fingerprint'
  ) then
    raise exception 'Chute súbito V1 recusada: uma entrada nova ainda coincide com o snapshot antigo';
  end if;

  select encode(extensions.digest(convert_to(
    'correcao-chute-subito-v1:' || v_lote_novo::text || ':' || v_formula || ':' ||
    v_contrato_fp || ':' || v_motor || ':' ||
    (select string_agg(
      linha_id::text || ':' || card_id || ':' || ordem_origem::text || ':' || entrada_fingerprint_nova,
      ',' order by ordem_origem
    ) from _alvo_chute_subito_v1),
    'UTF8'), 'sha256'), 'hex')
  into v_fingerprint;

  insert into clube_novo.otimizador_lote_producao_v3(
    id, contrato, tipo_lote, estado, formula_fingerprint, contrato_fingerprint,
    motor_versao, regua_snapshot, fingerprint, cards, linhas,
    excluidas_incompletas, excluidas_impeto_condicional, excluidas_sem_linha,
    pode_publicar, preparo_total, preparo_concluido, preparo_fingerprint_final,
    criado_em, atualizado_em
  ) values (
    v_lote_novo, 'otimizador_fila_producao_v3', 'integral', 'pausado',
    v_formula, v_contrato_fp, v_motor, v_regua, v_fingerprint, v_cartas, v_linhas,
    0, 0, 0, false, v_cartas, v_cartas, v_fingerprint, v_agora, v_agora
  );

  insert into clube_novo.otimizador_lote_producao_carta_v3(
    lote_id, card_id, overall_snapshot, entrada_otimizador, entrada_contrato,
    entrada_fingerprint, carta_versao_bonificador, carta_fingerprint_bonificador
  )
  select
    v_lote_novo,
    a.card_id,
    max(a.overall_snapshot),
    max(a.entrada_otimizador::text)::jsonb,
    'otimizador_entradas_v3',
    max(a.entrada_fingerprint_nova),
    max(a.carta_versao_bonificador),
    max(a.carta_fingerprint_bonificador)
  from _alvo_chute_subito_v1 a
  group by a.card_id;

  insert into clube_novo.otimizador_evento_producao_v3(lote_id, evento, detalhe)
  values (
    v_lote_novo,
    'lote_correcao_chute_subito_v1',
    jsonb_build_object(
      'contrato', 'otimizador_correcao_chute_subito_v1',
      'lote_origem', v_lote_origem,
      'linhas_reabertas', v_linhas,
      'cartas_reabertas', v_cartas,
      'skill_id', 2457,
      'bit_na_carta', 639,
      'efeito', 'Finalização +5%',
      'formula_fingerprint', v_formula,
      'contrato_fingerprint', v_contrato_fp,
      'motor_versao', v_motor,
      'pode_publicar', false,
      'criado_em_utc', v_agora
    )
  );

  insert into clube_novo.otimizador_evento_producao_v3(lote_id, linha_id, evento, detalhe)
  select
    v_lote_novo,
    a.linha_id,
    'linha_reaberta_chute_subito_v1',
    jsonb_build_object(
      'contrato', 'otimizador_correcao_chute_subito_v1',
      'lote_origem', v_lote_origem,
      'skill_id', 2457,
      'efeito', 'Finalização +5%',
      'ordem_origem', a.ordem_origem,
      'entrada_fingerprint_nova', a.entrada_fingerprint_nova,
      'linha_antes', a.linha_antes,
      'fila_antes', a.fila_antes,
      'publicacao_ativa_antes', a.ativa_antes,
      'delta_publico_antes', a.delta_antes,
      'finalizacao_antes', a.finalizacao_antes,
      'reaberta_em_utc', v_agora
    )
  from _alvo_chute_subito_v1 a;

  delete from clube_novo.build_pontuacao_final_v2_delta_v1 d
  using _alvo_chute_subito_v1 a
  where d.linha_id = a.linha_id;

  delete from clube_novo.build_publicacao_linha_ativa_v1 p
  using _alvo_chute_subito_v1 a
  where p.linha_id = a.linha_id;
  get diagnostics v_publicas = row_count;
  if v_publicas <> 34 then
    raise exception 'Chute súbito V1 recusada: foram retiradas % publicações ativas, esperadas 34', v_publicas;
  end if;

  -- A FK composta liga a fila ao lote gravado na linha-base. Primeiro sai a
  -- referência da fila antiga; depois a linha é movida e a nova fila entra.
  delete from clube_novo.otimizador_lote_producao_linha_v3 q
  using _alvo_chute_subito_v1 a
  where q.lote_id = v_lote_origem and q.linha_id = a.linha_id;
  get diagnostics v_afetadas = row_count;
  if v_afetadas <> v_linhas then
    raise exception 'Chute súbito V1 recusada: foram liberadas % linhas antigas, esperadas %', v_afetadas, v_linhas;
  end if;

  update clube_novo.build_linha_card l
     set lote_producao_id = v_lote_novo,
         build_otimizador_id = null,
         build_bonificador_id = null,
         estado_otimizador = 'pendente',
         erro_otimizador = null,
         otimizador_iniciado_em = null,
         otimizador_finalizado_em = null,
         lote_estado = 'pausado',
         lote_estado_atualizado_em = v_agora,
         lote_falha = null,
         otimizador_formula_fingerprint_esperado = v_formula,
         otimizador_contrato_fingerprint_esperado = v_contrato_fp,
         otimizador_motor_versao_esperada = v_motor,
         pendencias = '{}'::text[],
         publicacao_fingerprint = null,
         publicada_em = null,
         atributos_snapshot = null,
         atributos_snapshot_fingerprint = null,
         snapshot_otimizador_fingerprint = null,
         snapshot_bonificador_fingerprint = null,
         otimizador_motor_versao = null,
         otimizador_contrato_versao = null,
         bonificador_motor_versao = null,
         bonificador_contrato_versao = null,
         bonificador_lote_publicacao_id = null,
         nota_contrato = null,
         nota_otimizador_resultado_fingerprint = null,
         nota_bonificador_resultado_fingerprint = null,
         nota_carta_fingerprint = null,
         nota_formula_fingerprint = null,
         nota_contrato_fingerprint = null,
         nota_bruta_selada = null,
         nota_bonus_pe = null,
         nota_bonus_fisico_total = null,
         nota_bonus_posicao = null,
         nota_bonus_playstyle_1 = null,
         nota_bonus_playstyle_2 = null,
         nota_bonus_ia = null,
         nota_bonus_outros = null,
         nota_bonus_total = null,
         nota_numerador = null,
         nota_denominador = null,
         nota_do_motor = null,
         nota_final = null,
         nota_normalizacao_fingerprint = null,
         nota_calculo_fingerprint = null,
         nota_publicacao_fingerprint_v1 = null,
         nota_publicada_em_v1 = null,
         nota_calculada_em = null
  from _alvo_chute_subito_v1 a
  where l.id = a.linha_id;
  get diagnostics v_afetadas = row_count;
  if v_afetadas <> v_linhas then
    raise exception 'Chute súbito V1 recusada: foram reabertas % linhas, esperadas %', v_afetadas, v_linhas;
  end if;

  insert into clube_novo.otimizador_lote_producao_linha_v3(
    lote_id, linha_id, card_id, ordem_fila, overall_snapshot, entrada_fingerprint,
    reserva_token, worker_id, reservada_em, finalizada_em, tentativas, resultado_fingerprint
  )
  select
    v_lote_novo,
    a.linha_id,
    a.card_id,
    row_number() over (order by a.ordem_origem)::bigint,
    a.overall_snapshot,
    a.entrada_fingerprint_nova,
    null, null, null, null, 0, null
  from _alvo_chute_subito_v1 a
  order by a.ordem_origem;

  insert into clube_novo.build_finalizacao_fila_v1(
    linha_id, estado, prioridade, overall_origem, tentativas, origem_ultima,
    motivo, proxima_tentativa_em, ultima_tentativa_em, concluido_em,
    publicacao_fingerprint, atualizado_em
  )
  select
    a.linha_id, 'aguardando', 0, a.overall_snapshot,
    coalesce((a.finalizacao_antes->>'tentativas')::integer, 0),
    'correcao_chute_subito_v1',
    'aguardando Otimizador recalculado com Chute súbito',
    v_agora + interval '5 minutes', null, null, null, v_agora
  from _alvo_chute_subito_v1 a
  on conflict (linha_id) do update
     set estado = 'aguardando',
         prioridade = 0,
         overall_origem = excluded.overall_origem,
         origem_ultima = excluded.origem_ultima,
         motivo = excluded.motivo,
         proxima_tentativa_em = excluded.proxima_tentativa_em,
         ultima_tentativa_em = null,
         concluido_em = null,
         publicacao_fingerprint = null,
         atualizado_em = excluded.atualizado_em;

  update clube_novo.otimizador_lote_producao_v3 l
     set linhas = (
           select count(*)::integer
           from clube_novo.otimizador_lote_producao_linha_v3 q
           where q.lote_id = v_lote_origem
         ),
         atualizado_em = v_agora
   where l.id = v_lote_origem;

  if (select count(*) from clube_novo.otimizador_lote_producao_linha_v3 where lote_id = v_lote_novo) <> 36
     or (select count(*) from clube_novo.build_linha_card where lote_producao_id = v_lote_novo and estado_otimizador = 'pendente') <> 36
     or exists (select 1 from clube_novo.build_publicacao_linha_ativa_v1 where linha_id in (select linha_id from _alvo_chute_subito_v1))
     or exists (select 1 from clube_novo.build_pontuacao_final_v2_delta_v1 where linha_id in (select linha_id from _alvo_chute_subito_v1)) then
    raise exception 'Chute súbito V1 recusada: readback transacional não confirmou fila/publicação esperadas';
  end if;
end
$correcao$;

commit;

