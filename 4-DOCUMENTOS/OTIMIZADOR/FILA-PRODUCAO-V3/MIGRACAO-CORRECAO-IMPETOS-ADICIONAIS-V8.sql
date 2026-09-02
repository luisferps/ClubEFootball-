-- Correção pontual de Ímpetos adicionais V8.
--
-- Escopo deliberadamente fechado:
--   * lote de origem: ddbcbc86-1ae7-4b95-b9f0-22601f41b61d;
--   * somente as 37 linhas concluídas com vaga física e sem Ímpeto adicional;
--   * apaga somente os Builds do Otimizador dessas linhas e dependências
--     diretas já verificadas; não apaga linha-base nem dados de carta;
--   * cria um lote integral novo, pausado e sem publicação, pronto para
--     fotografia local. Não inicia worker, esteira ou publicação.

begin;

do $$
begin
  if to_regclass('clube_novo.otimizador_lote_producao_v3') is null
     or to_regclass('clube_novo.otimizador_lote_producao_carta_v3') is null
     or to_regclass('clube_novo.otimizador_lote_producao_linha_v3') is null
     or to_regclass('clube_novo.build_linha_card') is null
     or to_regclass('clube_novo.build_otimizador') is null
     or to_regclass('clube_novo.otimizador_evento_producao_v3') is null
     or to_regclass('clube_novo.build_pontuacao_normalizada_v2') is null
     or to_regclass('clube_novo.bonificador_promocao_publicacao_snapshot_v1') is null
     or to_regprocedure('public.otimizador_regua_v2()') is null
     or to_regprocedure('clube_novo.otimizador_producao_contrato_fingerprint_v3(jsonb)') is null then
    raise exception 'V8 recusada: contratos produtivos necessários ausentes';
  end if;
end
$$;

-- Dá nome específico à auditoria da correção. Nenhum evento anterior muda.
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
    'linha_reaberta_impeto_adicional_v8'
  ]));

-- A operação local em JSON usa apenas as duas portas abaixo para criar uma
-- fotografia. Elas passam a aceitar tanto o lote histórico quanto o V8.
-- O motor de painel aposentado continua fora deste caminho.
create or replace function public.otimizador_producao_pacote_local_manifesto_v2(
  p_lote_id uuid
) returns jsonb
language plpgsql
stable
security definer
set search_path to ''
set statement_timeout to '30s'
as $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_cartas integer;
  v_linhas integer;
begin
  if p_lote_id is null then
    raise exception 'pacote local v2 recusado: lote obrigatório';
  end if;

  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id;

  if not found or v_lote.tipo_lote <> 'integral' then
    raise exception 'pacote local v2 recusado: lote integral inexistente';
  end if;
  if v_lote.estado <> 'pausado'
     or v_lote.preparo_concluido <> v_lote.preparo_total
     or v_lote.pode_publicar is distinct from false
     or v_lote.formula_fingerprint not in (
       '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad',
       'bf6040b6fdbbb4a6b8cf97fe66cb441507ee637ec7edb300cf2ebabb5814f070'
     )
     or not coalesce((v_lote.regua_snapshot -> 'gate' ->> 'pode_rodar')::boolean, false) then
    raise exception 'pacote local v2 recusado: lote não está pausado e apto para fotografia selada';
  end if;
  if exists (
    select 1
    from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id
      and l.estado_otimizador = 'processando'
  ) then
    raise exception 'pacote local v2 recusado: há reserva ativa no lote';
  end if;
  if exists (
    select 1
    from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id
      and l.estado_otimizador = 'pendente'
      and (l.impeto_condicional_codigo is not null or l.impeto_condicional_nivel is not null)
  ) then
    raise exception 'pacote local v2 recusado: Ímpeto condicional pendente continua desligado';
  end if;

  select count(*)::integer into v_cartas
  from clube_novo.otimizador_lote_producao_carta_v3 s
  where s.lote_id = p_lote_id;

  select count(*)::integer into v_linhas
  from clube_novo.build_linha_card l
  where l.lote_producao_id = p_lote_id
    and l.estado_otimizador = 'pendente';

  return jsonb_build_object(
    'contrato', 'otimizador_pacote_local_v2',
    'lote_id', v_lote.id,
    'formula_fingerprint', v_lote.formula_fingerprint,
    'contrato_fingerprint', v_lote.contrato_fingerprint,
    'motor_versao', v_lote.motor_versao,
    'lote_fingerprint', v_lote.fingerprint,
    'regua', v_lote.regua_snapshot,
    'pode_publicar', false,
    'impetos_condicionais', 'desligados',
    'cartas_total', coalesce(v_cartas, 0),
    'linhas_total', coalesce(v_linhas, 0),
    'paginacao', 'cursor_canonico',
    'fonte', 'clube_novo.otimizador_entrada_linha_v1'
  );
end
$function$;

create or replace function public.otimizador_producao_pacote_local_linhas_v2(
  p_lote_id uuid,
  p_depois_de_ordem bigint default null,
  p_limite integer default 1000
) returns jsonb
language plpgsql
stable
security definer
set search_path to ''
set statement_timeout to '30s'
as $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_itens jsonb := '[]'::jsonb;
  v_proxima_ordem bigint;
begin
  if p_lote_id is null or coalesce(p_limite, 0) not between 1 and 1000
     or coalesce(p_depois_de_ordem, 0) < 0 then
    raise exception 'página de linhas local v2 recusada: argumentos inválidos';
  end if;
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id;
  if not found or v_lote.tipo_lote <> 'integral'
     or v_lote.estado <> 'pausado'
     or v_lote.preparo_concluido <> v_lote.preparo_total
     or v_lote.pode_publicar is distinct from false
     or v_lote.formula_fingerprint not in (
       '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad',
       'bf6040b6fdbbb4a6b8cf97fe66cb441507ee637ec7edb300cf2ebabb5814f070'
     ) then
    raise exception 'página de linhas local v2 recusada: fotografia não está estável';
  end if;
  if exists (
    select 1 from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id and l.estado_otimizador = 'processando'
  ) then
    raise exception 'página de linhas local v2 recusada: há reserva ativa';
  end if;

  with pagina as materialized (
    select q.linha_id, q.ordem_fila, q.entrada_fingerprint,
           l.card_id, l.funcao_id, l.posicao_id,
           l.impeto_condicional_codigo, l.impeto_condicional_nivel,
           c.nome as carta_nome, f.rotulo as funcao_rotulo, p.nome_pt as posicao_rotulo
    from clube_novo.otimizador_lote_producao_linha_v3 q
    join clube_novo.build_linha_card l on l.id = q.linha_id
    left join clube_novo.carta_jogo c on c.card_id = l.card_id
    left join clube_novo.funcao_sistema f on f.id = l.funcao_id
    left join clube_novo.posicao_jogo p on p.id = l.posicao_id
    where q.lote_id = p_lote_id
      and (p_depois_de_ordem is null or q.ordem_fila > p_depois_de_ordem)
      and l.estado_otimizador = 'pendente'
      and l.impeto_condicional_codigo is null
      and l.impeto_condicional_nivel is null
    order by q.ordem_fila
    limit p_limite
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'linha_id', linha_id,
    'ordem_fila', ordem_fila,
    'card_id', card_id,
    'funcao_id', funcao_id,
    'posicao_id', posicao_id,
    'carta_entrada_fingerprint', entrada_fingerprint,
    'carta_nome', carta_nome,
    'funcao_rotulo', funcao_rotulo,
    'posicao_rotulo', posicao_rotulo,
    'impeto_condicional_codigo', impeto_condicional_codigo,
    'impeto_condicional_nivel', impeto_condicional_nivel
  ) order by ordem_fila), '[]'::jsonb), max(ordem_fila)
  into v_itens, v_proxima_ordem
  from pagina;

  return jsonb_build_object(
    'contrato', 'otimizador_pacote_local_v2',
    'lote_id', p_lote_id,
    'depois_de_ordem', p_depois_de_ordem,
    'proxima_ordem_fila', v_proxima_ordem,
    'limite', p_limite,
    'contagem_no_manifesto', true,
    'itens', v_itens,
    'pode_publicar', false,
    'impetos_condicionais', 'desligados'
  );
end
$function$;

do $correcao$
declare
  v_lote_origem constant uuid := 'ddbcbc86-1ae7-4b95-b9f0-22601f41b61d';
  v_formula constant text := 'bf6040b6fdbbb4a6b8cf97fe66cb441507ee637ec7edb300cf2ebabb5814f070';
  v_motor constant text := 'otimizador-fila-producao-v3-local-20260902-impeto-adicional-v8';
  v_origem clube_novo.otimizador_lote_producao_v3%rowtype;
  v_regua jsonb;
  v_contrato_fp text;
  v_lote_novo uuid := extensions.gen_random_uuid();
  v_fingerprint text;
  v_agora timestamptz := clock_timestamp();
  v_linhas integer;
  v_cartas integer;
  v_builds integer;
  v_restantes integer;
begin
  select * into v_origem
  from clube_novo.otimizador_lote_producao_v3
  where id = v_lote_origem
  for update;

  if not found
     or v_origem.tipo_lote <> 'integral'
     or v_origem.estado <> 'pausado'
     or v_origem.pode_publicar is not false
     or v_origem.formula_fingerprint <> '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad' then
    raise exception 'V8 recusada: lote de origem não está integral, pausado e selado como esperado';
  end if;
  if exists (
    select 1
    from clube_novo.otimizador_evento_producao_v3 e
    where e.evento = 'lote_correcao_impeto_adicional_v8'
      and e.detalhe->>'lote_origem' = v_lote_origem::text
  ) then
    raise exception 'V8 recusada: a correção deste lote já foi aplicada';
  end if;

  select public.otimizador_regua_v2() into v_regua;
  if not coalesce((v_regua->'gate'->>'pode_rodar')::boolean, false)
     or coalesce(jsonb_array_length(v_regua->'impetos_adicionais'), 0) < 1 then
    raise exception 'V8 recusada: catálogo canônico de Ímpetos adicionais não está apto';
  end if;
  v_contrato_fp := clube_novo.otimizador_producao_contrato_fingerprint_v3(v_regua);

  create temporary table _alvo_impeto_v8 on commit drop as
  select
    l.id as linha_id,
    l.card_id,
    l.build_otimizador_id,
    q.ordem_fila as ordem_origem,
    q.overall_snapshot,
    q.entrada_fingerprint
  from clube_novo.build_linha_card l
  join clube_novo.otimizador_lote_producao_linha_v3 q
    on q.lote_id = v_lote_origem and q.linha_id = l.id
  join clube_novo.otimizador_lote_producao_carta_v3 c
    on c.lote_id = q.lote_id and c.card_id = l.card_id
  join clube_novo.build_otimizador b on b.id = l.build_otimizador_id
  where l.estado_otimizador = 'concluido'
    and b.impeto_adicional_codigo is null
    and exists (
      select 1
      from jsonb_array_elements(coalesce(c.entrada_otimizador->'impetos', '[]'::jsonb)) i
      where coalesce(i->>'vaga', 'false') in ('true', 't', '1')
    );

  select count(*)::integer, count(distinct card_id)::integer
  into v_linhas, v_cartas
  from _alvo_impeto_v8;
  if v_linhas <> 37 or v_cartas <> 4 then
    raise exception 'V8 recusada: escopo mudou; esperadas 37 linhas de 4 cartas, recebidas % de %', v_linhas, v_cartas;
  end if;
  if exists (
    select 1
    from _alvo_impeto_v8 a
    join clube_novo.build_linha_card l on l.id = a.linha_id
    join clube_novo.otimizador_lote_producao_linha_v3 q
      on q.lote_id = v_lote_origem and q.linha_id = a.linha_id
    where l.estado <> 'pendente'
       or l.build_bonificador_id is not null
       or l.publicacao_fingerprint is not null
       or l.publicada_em is not null
       or q.reserva_token is not null
       or q.worker_id is not null
  ) then
    raise exception 'V8 recusada: alguma linha alvo tem publicação, Bonificador ou reserva';
  end if;

  select encode(extensions.digest(convert_to(
    'reabertura-impeto-adicional-v8:' || v_lote_novo::text || ':' || v_formula || ':' ||
    v_contrato_fp || ':' || v_motor || ':' ||
    (select string_agg(
      linha_id::text || ':' || card_id || ':' || ordem_origem::text || ':' || entrada_fingerprint,
      ',' order by ordem_origem
    ) from _alvo_impeto_v8),
    'UTF8'), 'sha256'), 'hex') into v_fingerprint;

  insert into clube_novo.otimizador_lote_producao_v3(
    id, contrato, tipo_lote, estado, formula_fingerprint, contrato_fingerprint,
    motor_versao, regua_snapshot, fingerprint, cards, linhas,
    excluidas_incompletas, excluidas_impeto_condicional, excluidas_sem_linha,
    pode_publicar, preparo_total, preparo_concluido, preparo_fingerprint_final,
    criado_em, atualizado_em
  ) values (
    v_lote_novo, 'otimizador_fila_producao_v3', 'integral', 'pausado', v_formula,
    v_contrato_fp, v_motor, v_regua, v_fingerprint, v_cartas, v_linhas,
    0, 0, 0, false, v_cartas, v_cartas, v_fingerprint, v_agora, v_agora
  );

  insert into clube_novo.otimizador_lote_producao_carta_v3(
    lote_id, card_id, overall_snapshot, entrada_otimizador, entrada_contrato,
    entrada_fingerprint, carta_versao_bonificador, carta_fingerprint_bonificador
  )
  select
    v_lote_novo, c.card_id, c.overall_snapshot, c.entrada_otimizador,
    c.entrada_contrato, c.entrada_fingerprint, c.carta_versao_bonificador,
    c.carta_fingerprint_bonificador
  from clube_novo.otimizador_lote_producao_carta_v3 c
  join (select distinct card_id from _alvo_impeto_v8) a using (card_id)
  where c.lote_id = v_lote_origem;
  if (select count(*) from clube_novo.otimizador_lote_producao_carta_v3 where lote_id = v_lote_novo) <> v_cartas then
    raise exception 'V8 recusada: a fotografia das 4 cartas não foi copiada integralmente';
  end if;

  delete from clube_novo.build_pontuacao_normalizada_v2 n
  using _alvo_impeto_v8 a
  where n.build_otimizador_id = a.build_otimizador_id;

  delete from clube_novo.bonificador_promocao_publicacao_snapshot_v1 s
  using _alvo_impeto_v8 a
  where s.build_otimizador_id = a.build_otimizador_id;

  -- A FK composta exige remover a referência de fila antiga antes de trocar
  -- o lote da linha-base. Os eventos continuam preservados por linha.
  delete from clube_novo.otimizador_lote_producao_linha_v3 q
  using _alvo_impeto_v8 a
  where q.lote_id = v_lote_origem and q.linha_id = a.linha_id;
  if not found then
    raise exception 'V8 recusada: não foi possível liberar as linhas antigas';
  end if;

  update clube_novo.build_linha_card l
     set lote_producao_id = v_lote_novo,
         build_otimizador_id = null,
         estado_otimizador = 'pendente',
         erro_otimizador = null,
         otimizador_iniciado_em = null,
         otimizador_finalizado_em = null,
         otimizador_formula_fingerprint_esperado = v_formula,
         otimizador_contrato_fingerprint_esperado = v_contrato_fp,
         otimizador_motor_versao_esperada = v_motor,
         lote_estado = 'pausado',
         lote_estado_atualizado_em = v_agora,
         lote_falha = null,
         atualizado_em = v_agora
  from _alvo_impeto_v8 a
  where l.id = a.linha_id;
  get diagnostics v_builds = row_count;
  if v_builds <> v_linhas then
    raise exception 'V8 recusada: foram reabertas % linhas, esperadas %', v_builds, v_linhas;
  end if;

  delete from clube_novo.build_otimizador b
  using _alvo_impeto_v8 a
  where b.id = a.build_otimizador_id;
  get diagnostics v_builds = row_count;
  if v_builds <> v_linhas then
    raise exception 'V8 recusada: foram removidos % Builds, esperados %', v_builds, v_linhas;
  end if;

  insert into clube_novo.otimizador_lote_producao_linha_v3(
    lote_id, linha_id, card_id, ordem_fila, overall_snapshot, entrada_fingerprint,
    reserva_token, worker_id, reservada_em, finalizada_em, tentativas, resultado_fingerprint
  )
  select
    v_lote_novo, a.linha_id, a.card_id,
    row_number() over (order by a.ordem_origem)::bigint,
    a.overall_snapshot, a.entrada_fingerprint,
    null, null, null, null, 0, null
  from _alvo_impeto_v8 a
  order by a.ordem_origem;
  get diagnostics v_builds = row_count;
  if v_builds <> v_linhas then
    raise exception 'V8 recusada: a nova fila recebeu % linhas, esperadas %', v_builds, v_linhas;
  end if;

  select count(*)::integer into v_restantes
  from clube_novo.otimizador_lote_producao_linha_v3
  where lote_id = v_lote_origem;
  update clube_novo.otimizador_lote_producao_v3
     set linhas = v_restantes,
         atualizado_em = v_agora
   where id = v_lote_origem;

  insert into clube_novo.otimizador_evento_producao_v3(lote_id, evento, detalhe)
  values (
    v_lote_novo,
    'lote_correcao_impeto_adicional_v8',
    jsonb_build_object(
      'contrato', 'otimizador_correcao_impeto_adicional_v8',
      'lote_origem', v_lote_origem,
      'linhas_reabertas', v_linhas,
      'cartas_reabertas', v_cartas,
      'formula_fingerprint', v_formula,
      'contrato_fingerprint', v_contrato_fp,
      'motor_versao', v_motor,
      'pode_publicar', false,
      'criado_em_utc', v_agora
    )
  );

  insert into clube_novo.otimizador_evento_producao_v3(lote_id, linha_id, evento, detalhe)
  select
    v_lote_origem,
    a.linha_id,
    'linha_reaberta_impeto_adicional_v8',
    jsonb_build_object(
      'contrato', 'otimizador_correcao_impeto_adicional_v8',
      'lote_correcao', v_lote_novo,
      'build_otimizador_removido', a.build_otimizador_id,
      'formula_fingerprint_nova', v_formula,
      'reaberta_em_utc', v_agora,
      'pode_publicar', false
    )
  from _alvo_impeto_v8 a;
end
$correcao$;

comment on function public.otimizador_producao_pacote_local_manifesto_v2(uuid) is
  'V8: fotografia local V2 aceita somente os selos histórico e Ímpetos adicionais V8, ambos sem publicação.';
comment on function public.otimizador_producao_pacote_local_linhas_v2(uuid,bigint,integer) is
  'V8: páginas locais V2 para fotografia selada; suporta o lote corretivo de Ímpetos adicionais.';

notify pgrst, 'reload schema';

commit;
