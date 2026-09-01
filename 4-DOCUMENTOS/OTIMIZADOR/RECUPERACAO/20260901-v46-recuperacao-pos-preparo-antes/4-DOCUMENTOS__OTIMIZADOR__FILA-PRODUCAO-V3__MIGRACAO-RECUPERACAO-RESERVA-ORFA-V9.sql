-- V9 — recuperação manual e fail-closed de uma reserva órfã.
--
-- Este contrato existe somente quando uma pausa/encerramento já foi solicitado,
-- não existe worker local e a única linha ainda está presa em "processando".
-- Ele devolve exclusivamente essa linha a pendente e deixa o lote pausado.
-- Não altera fórmula, pesos, entradas, publicação, linhas concluídas ou dados do jogo.

begin;

create or replace function public.otimizador_producao_recuperar_reserva_orfa_v9(
  p_lote_id uuid,
  p_linha_id bigint,
  p_confirmado boolean default false
) returns jsonb
language plpgsql
security definer
set search_path to ''
as $function$
declare
  v_formula_aprovada constant text := '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad';
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_card_id text;
  v_worker_id uuid;
  v_reserva_token uuid;
  v_processando integer;
begin
  if p_confirmado is not true then
    raise exception 'recuperação exige confirmação explícita';
  end if;

  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id
  for update;

  if not found
     or v_lote.tipo_lote <> 'integral'
     or v_lote.estado not in ('pausando', 'encerrando')
     or v_lote.pode_publicar is not false
     or v_lote.formula_fingerprint <> v_formula_aprovada then
    raise exception 'recuperação recusada pelo selo/estado do lote';
  end if;

  select count(*) into v_processando
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id = q.linha_id
  where q.lote_id = p_lote_id
    and l.estado_otimizador = 'processando';

  if v_processando <> 1 then
    raise exception 'recuperação recusada: é exigida exatamente uma reserva processando';
  end if;

  select q.card_id, q.worker_id, q.reserva_token
  into v_card_id, v_worker_id, v_reserva_token
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id = q.linha_id
  where q.lote_id = p_lote_id
    and q.linha_id = p_linha_id
    and l.estado_otimizador = 'processando'
  for update of q, l;

  if not found or v_worker_id is null or v_reserva_token is null then
    raise exception 'recuperação recusada: a reserva informada não é a linha órfã atual';
  end if;

  update clube_novo.build_linha_card
  set estado_otimizador = 'pendente',
      erro_otimizador = null,
      otimizador_iniciado_em = null,
      otimizador_finalizado_em = null,
      atualizado_em = clock_timestamp()
  where id = p_linha_id
    and lote_producao_id = p_lote_id
    and estado_otimizador = 'processando';

  if not found then
    raise exception 'recuperação recusada: a linha mudou durante a confirmação';
  end if;

  update clube_novo.otimizador_lote_producao_linha_v3
  set reserva_token = null,
      worker_id = null,
      reservada_em = null
  where lote_id = p_lote_id
    and linha_id = p_linha_id
    and reserva_token = v_reserva_token;

  if not found then
    raise exception 'recuperação recusada: o token de reserva mudou durante a confirmação';
  end if;

  update clube_novo.otimizador_lote_producao_v3
  set estado = 'pausado',
      falha = null,
      finalizado_em = null,
      atualizado_em = clock_timestamp()
  where id = p_lote_id
    and estado = v_lote.estado;

  if not found then
    raise exception 'recuperação recusada: o estado do lote mudou durante a confirmação';
  end if;

  insert into clube_novo.otimizador_evento_producao_v3(lote_id, linha_id, evento, detalhe)
  values (
    p_lote_id,
    p_linha_id,
    'lote_pausado',
    jsonb_build_object(
      'recuperacao_reserva_orfa_v9', true,
      'estado_anterior', v_lote.estado,
      'linha_devolvida_a_pendente', p_linha_id,
      'card_id', v_card_id,
      'worker_id_anterior', v_worker_id,
      'pode_publicar', false,
      'formula_alterada', false,
      'linhas_concluidas_preservadas', true
    )
  );

  return public.otimizador_producao_status_v5(p_lote_id);
end
$function$;

revoke all on function public.otimizador_producao_recuperar_reserva_orfa_v9(uuid, bigint, boolean)
  from public, anon, authenticated;
grant execute on function public.otimizador_producao_recuperar_reserva_orfa_v9(uuid, bigint, boolean)
  to service_role;

commit;
