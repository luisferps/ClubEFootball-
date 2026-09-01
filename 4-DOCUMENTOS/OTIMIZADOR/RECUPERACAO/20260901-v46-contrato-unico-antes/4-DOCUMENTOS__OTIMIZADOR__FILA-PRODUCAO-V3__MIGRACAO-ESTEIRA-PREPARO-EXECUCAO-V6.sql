-- Esteira V6 do Otimizador.
--
-- Permite que a preparação integral continue criando snapshots/linhas enquanto
-- o worker local calcula SOMENTE as linhas já seladas. Não altera fórmula,
-- pesos, moldes, Ímpetos condicionais, publicação ou dados de jogo.
--
-- Invariantes:
--   * a fórmula aprovada continua selada pelo mesmo fingerprint;
--   * cada linha continua validando card_id + função + posição + snapshot;
--   * o fingerprint inicial do lote permanece estável enquanto há execução;
--   * o fingerprint final das linhas é gravado separadamente ao fechar o
--     preparo, sem invalidar uma linha que já esteja em cálculo;
--   * nenhuma função nova é exposta a anon/authenticated/PUBLIC.

begin;

alter table clube_novo.otimizador_lote_producao_v3
  add column if not exists preparo_fingerprint_final text;

alter table clube_novo.otimizador_lote_producao_v3
  drop constraint if exists otimizador_lote_producao_v3_preparo_fingerprint_final_check;

alter table clube_novo.otimizador_lote_producao_v3
  add constraint otimizador_lote_producao_v3_preparo_fingerprint_final_check
  check (
    preparo_fingerprint_final is null
    or preparo_fingerprint_final ~ '^[0-9a-f]{64}$'
  );

-- Transição explícita e selada: o lote integral passa de "preparando" para
-- "rodando" sem esperar a fotografia inteira. O worker V6 só poderá reservar
-- linhas que já existam com snapshot individual consistente.
create or replace function public.otimizador_producao_iniciar_esteira_v6(
  p_lote_id uuid
) returns jsonb
language plpgsql
security definer
set search_path to ''
as $function$
declare
  v_formula constant text := '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad';
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_evento text;
begin
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id
  for update;

  if not found or v_lote.tipo_lote <> 'integral' then
    raise exception 'esteira V6 recusada: lote integral inexistente';
  end if;
  if v_lote.formula_fingerprint <> v_formula or v_lote.pode_publicar is not false then
    raise exception 'esteira V6 recusada: selo do lote não é a fórmula aprovada';
  end if;

  if v_lote.estado = 'rodando' then
    return public.otimizador_producao_status_v5(p_lote_id);
  end if;
  if v_lote.estado not in ('preparando', 'preparo_pausado') then
    raise exception 'esteira V6 recusada pelo estado atual: %', v_lote.estado;
  end if;

  v_evento := case when v_lote.estado = 'preparo_pausado'
    then 'lote_retomado' else 'lote_iniciado' end;

  update clube_novo.otimizador_lote_producao_v3
  set estado = 'rodando',
      iniciado_em = coalesce(iniciado_em, clock_timestamp()),
      atualizado_em = clock_timestamp()
  where id = p_lote_id;

  insert into clube_novo.otimizador_evento_producao_v3(lote_id, evento, detalhe)
  values (
    p_lote_id,
    v_evento,
    jsonb_build_object(
      'esteira_v6', true,
      'preparo_concluido', v_lote.preparo_concluido,
      'preparo_total', v_lote.preparo_total,
      'pode_publicar', false,
      'impetos_condicionais', 'desligados'
    )
  );

  return public.otimizador_producao_status_v5(p_lote_id);
end
$function$;

-- Adaptador transacional para a preparação V5 já validada. Durante a fatia,
-- V5 vê o estado "preparando"; ao commit, o lote volta a "rodando" e as
-- linhas recém-seladas ficam imediatamente elegíveis para o worker V6.
create or replace function public.otimizador_producao_preparar_fatia_v6(
  p_lote_id uuid,
  p_limite integer default 10
) returns jsonb
language plpgsql
security definer
set search_path to ''
as $function$
declare
  v_formula constant text := '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad';
  v_antes clube_novo.otimizador_lote_producao_v3%rowtype;
  v_depois clube_novo.otimizador_lote_producao_v3%rowtype;
  v_seed_fingerprint text;
begin
  if p_lote_id is null or coalesce(p_limite, 0) not between 1 and 20 then
    raise exception 'preparo da esteira V6 recusado: lote e limite 1..20 são obrigatórios';
  end if;

  select * into v_antes
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id
  for update;

  if not found or v_antes.tipo_lote <> 'integral' then
    raise exception 'preparo da esteira V6 recusado: lote integral inexistente';
  end if;
  if v_antes.formula_fingerprint <> v_formula or v_antes.pode_publicar is not false then
    raise exception 'preparo da esteira V6 recusado: selo do lote não é a fórmula aprovada';
  end if;
  if v_antes.estado <> 'rodando' then
    return public.otimizador_producao_status_v5(p_lote_id);
  end if;
  if v_antes.preparo_concluido >= v_antes.preparo_total then
    return public.otimizador_producao_status_v5(p_lote_id);
  end if;

  v_seed_fingerprint := v_antes.fingerprint;

  -- V5 continua sendo a única rotina que constrói os snapshots e as linhas.
  -- A mudança de estado fica invisível fora desta transação, pois o cabeçalho
  -- permanece travado até a volta a "rodando" abaixo.
  update clube_novo.otimizador_lote_producao_v3
  set estado = 'preparando', atualizado_em = clock_timestamp()
  where id = p_lote_id;

  perform public.otimizador_producao_preparar_fatia_v5(p_lote_id, p_limite);

  select * into v_depois
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id
  for update;

  if v_depois.estado = 'falhou' then
    return public.otimizador_producao_status_v5(p_lote_id);
  end if;
  if v_depois.estado not in ('preparando', 'parado') then
    raise exception 'preparo da esteira V6 retornou estado inesperado: %', v_depois.estado;
  end if;

  update clube_novo.otimizador_lote_producao_v3
  set estado = 'rodando',
      -- O worker usa este selo estável em cada reserva/conclusão.
      fingerprint = v_seed_fingerprint,
      -- Ao acabar V5 produz o fingerprint completo das linhas; ele é mantido
      -- para auditoria sem trocar o selo de uma linha já em processamento.
      preparo_fingerprint_final = case
        when v_depois.estado = 'parado' then v_depois.fingerprint
        else preparo_fingerprint_final
      end,
      atualizado_em = clock_timestamp()
  where id = p_lote_id;

  return public.otimizador_producao_status_v5(p_lote_id);
end
$function$;

-- Reserva de linha para a esteira. Quando a parte já pronta termina, mas o
-- preparo ainda tem candidatas pendentes, ela devolve "rodando" sem concluir
-- o lote; o worker aguarda a próxima linha selada.
create or replace function public.otimizador_producao_reservar_linha_v6(
  p_lote_id uuid,
  p_worker_id uuid
) returns jsonb
language plpgsql
security definer
set search_path to ''
as $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_q clube_novo.otimizador_lote_producao_linha_v3%rowtype;
  v_l clube_novo.build_linha_card%rowtype;
  v_c clube_novo.otimizador_lote_producao_carta_v3%rowtype;
  v_token uuid;
begin
  if p_worker_id is null then
    raise exception 'worker_id obrigatório';
  end if;

  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id
  for update;

  if not found or v_lote.tipo_lote <> 'integral' then
    raise exception 'reserva da esteira V6 recusada: lote integral inexistente';
  end if;
  if v_lote.estado <> 'rodando' then
    return jsonb_build_object(
      'contrato', 'otimizador_fila_producao_v3',
      'reservada', false,
      'estado_lote', v_lote.estado
    );
  end if;

  select q.* into v_q
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id = q.linha_id
  where q.lote_id = p_lote_id and l.estado_otimizador = 'pendente'
  order by q.ordem_fila
  for update of q, l skip locked
  limit 1;

  if not found then
    if v_lote.preparo_concluido < v_lote.preparo_total then
      return jsonb_build_object(
        'contrato', 'otimizador_fila_producao_v3',
        'reservada', false,
        'estado_lote', 'rodando',
        'aguardando_preparo', true
      );
    end if;

    if not exists (
      select 1
      from clube_novo.otimizador_lote_producao_linha_v3 q2
      join clube_novo.build_linha_card l2 on l2.id = q2.linha_id
      where q2.lote_id = p_lote_id
        and l2.estado_otimizador in ('pendente', 'processando')
    ) then
      update clube_novo.otimizador_lote_producao_v3
      set estado = 'concluido', finalizado_em = clock_timestamp(), atualizado_em = clock_timestamp()
      where id = p_lote_id;
      insert into clube_novo.otimizador_evento_producao_v3(lote_id, evento)
      values(p_lote_id, 'lote_concluido');
      return jsonb_build_object(
        'contrato', 'otimizador_fila_producao_v3',
        'reservada', false,
        'estado_lote', 'concluido'
      );
    end if;

    return jsonb_build_object(
      'contrato', 'otimizador_fila_producao_v3',
      'reservada', false,
      'estado_lote', 'rodando'
    );
  end if;

  select * into v_l
  from clube_novo.build_linha_card
  where id = v_q.linha_id;

  select * into v_c
  from clube_novo.otimizador_lote_producao_carta_v3
  where lote_id = p_lote_id and card_id = v_q.card_id;

  if not found or v_c.entrada_fingerprint <> v_q.entrada_fingerprint then
    raise exception 'reserva da esteira V6 recusada: snapshot de entrada inconsistente';
  end if;

  v_token := extensions.gen_random_uuid();
  update clube_novo.otimizador_lote_producao_linha_v3
  set reserva_token = v_token,
      worker_id = p_worker_id,
      reservada_em = clock_timestamp(),
      tentativas = tentativas + 1
  where lote_id = p_lote_id and linha_id = v_q.linha_id;

  update clube_novo.build_linha_card
  set estado_otimizador = 'processando',
      erro_otimizador = null,
      otimizador_iniciado_em = clock_timestamp(),
      atualizado_em = clock_timestamp()
  where id = v_q.linha_id and estado_otimizador = 'pendente';

  insert into clube_novo.otimizador_evento_producao_v3(lote_id, linha_id, evento, detalhe)
  values(
    p_lote_id,
    v_q.linha_id,
    'linha_reservada',
    jsonb_build_object('worker_id', p_worker_id, 'ordem_fila', v_q.ordem_fila, 'esteira_v6', true)
  );

  return jsonb_build_object(
    'contrato', 'otimizador_fila_producao_v3',
    'reservada', true,
    'lote_id', p_lote_id,
    'linha_id', v_q.linha_id,
    'reserva_token', v_token,
    'ordem_fila', v_q.ordem_fila,
    'card_id', v_l.card_id,
    'funcao_id', v_l.funcao_id,
    'posicao_id', v_l.posicao_id,
    'impeto_condicional_codigo', null,
    'impeto_condicional_nivel', null,
    'carta', v_c.entrada_otimizador,
    'carta_entrada_fingerprint', v_c.entrada_fingerprint,
    'formula_fingerprint', v_lote.formula_fingerprint,
    'contrato_fingerprint', v_lote.contrato_fingerprint,
    'motor_versao', v_lote.motor_versao,
    'lote_fingerprint', v_lote.fingerprint,
    'carta_versao', v_l.carta_versao,
    'carta_fingerprint', v_l.carta_fingerprint,
    'impetos_condicionais', 'desligados'
  );
end
$function$;

-- Conclusão equivalente à V3, com a única diferença de que o lote integral
-- não pode ser concluído enquanto ainda há candidatas a preparar.
create or replace function public.otimizador_producao_concluir_linha_v6(
  p_lote_id uuid,
  p_linha_id bigint,
  p_reserva_token uuid,
  p_resultado jsonb
) returns jsonb
language plpgsql
security definer
set search_path to ''
as $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_q clube_novo.otimizador_lote_producao_linha_v3%rowtype;
  v_l clube_novo.build_linha_card%rowtype;
  v_habilidades integer[];
  v_resultado_fp text;
  v_build_id bigint;
begin
  if jsonb_typeof(p_resultado) <> 'object' then
    raise exception 'resultado do Otimizador deve ser objeto';
  end if;

  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id
  for update;
  select * into v_q
  from clube_novo.otimizador_lote_producao_linha_v3
  where lote_id = p_lote_id and linha_id = p_linha_id
  for update;
  select * into v_l
  from clube_novo.build_linha_card
  where id = p_linha_id
  for update;

  if v_lote.id is null or v_lote.tipo_lote <> 'integral'
     or v_q.linha_id is null or v_l.id is null then
    raise exception 'conclusão da esteira V6 recusada: lote ou linha inexistente';
  end if;
  if v_l.estado_otimizador <> 'processando'
     or v_q.reserva_token is distinct from p_reserva_token then
    raise exception 'conclusão da esteira V6 recusada: reserva não pertence ao worker';
  end if;
  if p_resultado->>'card_id' <> v_l.card_id
     or (p_resultado->>'funcao_id')::bigint <> v_l.funcao_id
     or (p_resultado->>'posicao_id')::integer <> v_l.posicao_id then
    raise exception 'conclusão da esteira V6 recusada: identidade da linha diverge';
  end if;
  if p_resultado->>'formula_fingerprint' <> v_lote.formula_fingerprint
     or p_resultado->>'contrato_fingerprint' <> v_lote.contrato_fingerprint
     or p_resultado->>'motor_versao' <> v_lote.motor_versao
     or p_resultado->>'lote_fingerprint' <> v_lote.fingerprint
     or p_resultado->>'carta_entrada_fingerprint' <> v_q.entrada_fingerprint then
    raise exception 'conclusão da esteira V6 recusada: selo divergente';
  end if;
  if coalesce(p_resultado->>'impeto_condicional_codigo', '') <> ''
     or coalesce(p_resultado->>'impeto_condicional_nivel', '') <> '' then
    raise exception 'conclusão da esteira V6 recusada: Ímpeto condicional continua desligado';
  end if;
  if not (p_resultado ?& array['b1', 'barras', 'tecnico_id', 'habilidades', 'builds_comparadas', 'builds_possiveis']) then
    raise exception 'conclusão da esteira V6 recusada: resultado incompleto';
  end if;
  if jsonb_typeof(p_resultado->'barras') <> 'object'
     or jsonb_typeof(p_resultado->'habilidades') <> 'array' then
    raise exception 'conclusão da esteira V6 recusada: build inválida';
  end if;

  select coalesce(array_agg(x.valor::integer order by x.ordem), '{}'::integer[])
  into v_habilidades
  from jsonb_array_elements_text(p_resultado->'habilidades') with ordinality x(valor, ordem);

  v_resultado_fp := encode(extensions.digest(convert_to(p_resultado::text, 'UTF8'), 'sha256'), 'hex');

  insert into clube_novo.build_otimizador(
    tecnico_id, barras, impeto_adicional_codigo, habilidades_adicionais, pontuacao,
    contrato_versao, contrato_fingerprint, carta_versao, carta_fingerprint,
    formula_fingerprint, resultado_fingerprint, motor_versao, builds_comparadas, builds_possiveis
  ) values (
    (p_resultado->>'tecnico_id')::bigint,
    p_resultado->'barras',
    nullif(p_resultado->>'impeto_adicional_codigo', '')::integer,
    v_habilidades,
    (p_resultado->>'b1')::numeric,
    'otimizador_regua_v2',
    v_lote.contrato_fingerprint,
    v_l.carta_versao,
    v_l.carta_fingerprint,
    v_lote.formula_fingerprint,
    v_resultado_fp,
    v_lote.motor_versao,
    (p_resultado->>'builds_comparadas')::integer,
    (p_resultado->>'builds_possiveis')::numeric
  ) returning id into v_build_id;

  update clube_novo.build_linha_card
  set build_otimizador_id = v_build_id,
      estado_otimizador = 'concluido',
      erro_otimizador = null,
      otimizador_finalizado_em = clock_timestamp(),
      pendencias = '{}'::text[],
      atualizado_em = clock_timestamp()
  where id = p_linha_id;

  update clube_novo.otimizador_lote_producao_linha_v3
  set reserva_token = null,
      worker_id = null,
      finalizada_em = clock_timestamp(),
      resultado_fingerprint = v_resultado_fp
  where lote_id = p_lote_id and linha_id = p_linha_id;

  insert into clube_novo.otimizador_evento_producao_v3(lote_id, linha_id, evento, detalhe)
  values(
    p_lote_id,
    p_linha_id,
    'linha_concluida',
    jsonb_build_object(
      'build_otimizador_id', v_build_id,
      'resultado_fingerprint', v_resultado_fp,
      'bonificador', 'pendente',
      'esteira_v6', true
    )
  );

  if v_lote.estado = 'rodando'
     and v_lote.preparo_concluido >= v_lote.preparo_total
     and not exists (
       select 1
       from clube_novo.otimizador_lote_producao_linha_v3 q2
       join clube_novo.build_linha_card l2 on l2.id = q2.linha_id
       where q2.lote_id = p_lote_id
         and l2.estado_otimizador in ('pendente', 'processando')
     ) then
    update clube_novo.otimizador_lote_producao_v3
    set estado = 'concluido', finalizado_em = clock_timestamp(), atualizado_em = clock_timestamp()
    where id = p_lote_id;
    insert into clube_novo.otimizador_evento_producao_v3(lote_id, evento)
    values(p_lote_id, 'lote_concluido');
  end if;

  return jsonb_build_object(
    'contrato', 'otimizador_fila_producao_v3',
    'linha_id', p_linha_id,
    'build_otimizador_id', v_build_id,
    'bonificador', 'pendente',
    'pode_publicar', false
  );
end
$function$;

revoke all on function public.otimizador_producao_iniciar_esteira_v6(uuid)
  from public, anon, authenticated;
revoke all on function public.otimizador_producao_preparar_fatia_v6(uuid, integer)
  from public, anon, authenticated;
revoke all on function public.otimizador_producao_reservar_linha_v6(uuid, uuid)
  from public, anon, authenticated;
revoke all on function public.otimizador_producao_concluir_linha_v6(uuid, bigint, uuid, jsonb)
  from public, anon, authenticated;

grant execute on function public.otimizador_producao_iniciar_esteira_v6(uuid) to service_role;
grant execute on function public.otimizador_producao_preparar_fatia_v6(uuid, integer) to service_role;
grant execute on function public.otimizador_producao_reservar_linha_v6(uuid, uuid) to service_role;
grant execute on function public.otimizador_producao_concluir_linha_v6(uuid, bigint, uuid, jsonb) to service_role;

commit;
