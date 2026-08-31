-- Correção V7 da esteira do Otimizador.
-- A V6 tentou preencher o ID de build_otimizador, que é ALWAYS IDENTITY no
-- banco. Esta correção preserva fórmula, inputs, linha, lote e publicação;
-- apenas deixa o próprio banco gerar o ID canônico.

begin;

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

  -- O ID é ALWAYS IDENTITY; a coluna não pode receber nextval/manualmente.
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

-- Recuperação circunscrita ao único estado que a V6 defeituosa pôde deixar:
-- nenhuma linha concluída é tocada, e a linha reservada volta a pendente.
create or replace function public.otimizador_producao_recuperar_esteira_v7(
  p_lote_id uuid,
  p_codigo text
) returns jsonb
language plpgsql
security definer
set search_path to ''
as $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_repostas integer;
begin
  if p_codigo <> 'identity_build_otimizador_v7' then
    raise exception 'recuperação V7 recusada: código de incidente divergente';
  end if;
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id
  for update;
  if not found or v_lote.tipo_lote <> 'integral'
     or v_lote.estado <> 'falhou'
     or v_lote.falha <> 'contrato recusou a consulta (400)'
     or v_lote.formula_fingerprint <> '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad'
     or v_lote.pode_publicar is not false then
    raise exception 'recuperação V7 recusada: lote não corresponde ao incidente selado';
  end if;

  update clube_novo.build_linha_card l
  set estado_otimizador = 'pendente',
      erro_otimizador = null,
      otimizador_iniciado_em = null,
      atualizado_em = clock_timestamp()
  from clube_novo.otimizador_lote_producao_linha_v3 q
  where q.lote_id = p_lote_id
    and q.linha_id = l.id
    and l.estado_otimizador = 'processando';
  get diagnostics v_repostas = row_count;

  update clube_novo.otimizador_lote_producao_linha_v3 q
  set reserva_token = null,
      worker_id = null,
      reservada_em = null
  from clube_novo.build_linha_card l
  where q.lote_id = p_lote_id
    and q.linha_id = l.id
    and l.estado_otimizador = 'pendente'
    and q.reserva_token is not null;

  update clube_novo.otimizador_lote_producao_v3
  set estado = 'preparo_pausado',
      falha = null,
      atualizado_em = clock_timestamp()
  where id = p_lote_id;

  insert into clube_novo.otimizador_evento_producao_v3(lote_id, evento, detalhe)
  values(
    p_lote_id,
    'preparo_pausado',
    jsonb_build_object(
      'incidente', 'identity_build_otimizador_v6',
      'recuperacao_v7', true,
      'linhas_devolvidas_a_pendente', v_repostas,
      'pode_publicar', false,
      'formula_alterada', false
    )
  );
  return public.otimizador_producao_status_v5(p_lote_id);
end
$function$;

revoke all on function public.otimizador_producao_recuperar_esteira_v7(uuid, text)
  from public, anon, authenticated;
grant execute on function public.otimizador_producao_recuperar_esteira_v7(uuid, text)
  to service_role;

commit;
