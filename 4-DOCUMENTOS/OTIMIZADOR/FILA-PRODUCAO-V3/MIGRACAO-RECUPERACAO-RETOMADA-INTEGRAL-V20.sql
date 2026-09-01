-- V20 — recuperação cirúrgica da única falha de retomada pós-preparo.
--
-- Escopo: uma linha reservada por um worker que tomou o contrato V3 depois de
-- a preparação integral já ter terminado. A função só aceita o selo exato
-- observado no incidente; não toca fórmula, pesos, dados de jogo, builds já
-- gravadas, publicação, Bonificador nem fontes legadas.

begin;

do $$
begin
  if to_regprocedure('public.otimizador_producao_status_v5(uuid)') is null
     or to_regclass('clube_novo.otimizador_lote_producao_v3') is null
     or to_regclass('clube_novo.otimizador_lote_producao_linha_v3') is null
     or to_regclass('clube_novo.build_linha_card') is null then
    raise exception 'V20 recusada: contratos/tabelas da fila produtiva ausentes';
  end if;
end;
$$;

create or replace function public.otimizador_producao_recuperar_falha_retomada_integral_v1(
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
  v_falha_exata constant text := 'contrato recusou a consulta (400)';
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_card_id text;
  v_worker_id uuid;
  v_reserva_token uuid;
  v_processando integer;
  v_resultados integer;
begin
  if p_confirmado is not true then
    raise exception 'recuperação V20 exige confirmação explícita';
  end if;

  select * into v_lote
    from clube_novo.otimizador_lote_producao_v3
   where id = p_lote_id
   for update;

  if not found
     or v_lote.tipo_lote <> 'integral'
     or v_lote.estado <> 'falhou'
     or v_lote.falha <> v_falha_exata
     or v_lote.pode_publicar is not false
     or v_lote.formula_fingerprint <> v_formula_aprovada
     or v_lote.linhas <= 0
     or v_lote.preparo_total <= 0
     or v_lote.preparo_concluido <> v_lote.preparo_total then
    raise exception 'recuperação V20 recusada: selo/estado não corresponde à falha pós-preparo autorizada';
  end if;

  select count(*)::integer into v_processando
    from clube_novo.otimizador_lote_producao_linha_v3 q
    join clube_novo.build_linha_card l on l.id = q.linha_id
   where q.lote_id = p_lote_id
     and l.estado_otimizador = 'processando';

  if v_processando <> 1 then
    raise exception 'recuperação V20 recusada: é exigida exatamente uma linha processando';
  end if;

  select q.card_id, q.worker_id, q.reserva_token
    into v_card_id, v_worker_id, v_reserva_token
    from clube_novo.otimizador_lote_producao_linha_v3 q
    join clube_novo.build_linha_card l on l.id = q.linha_id
   where q.lote_id = p_lote_id
     and q.linha_id = p_linha_id
     and l.estado_otimizador = 'processando'
     and l.build_otimizador_id is null
     and l.build_bonificador_id is null
     and l.otimizador_finalizado_em is null
   for update of q, l;

  if not found or v_worker_id is null or v_reserva_token is null then
    raise exception 'recuperação V20 recusada: a linha não é a reserva órfã sem resultado';
  end if;

  select count(*)::integer into v_resultados
    from clube_novo.build_linha_card l
   where l.id = p_linha_id
     and (l.build_otimizador_id is not null or l.build_bonificador_id is not null);

  if v_resultados <> 0 then
    raise exception 'recuperação V20 recusada: a linha já possui resultado persistido';
  end if;

  update clube_novo.build_linha_card
     set estado_otimizador = 'pendente',
         erro_otimizador = null,
         otimizador_iniciado_em = null,
         otimizador_finalizado_em = null,
         atualizado_em = clock_timestamp()
   where id = p_linha_id
     and lote_producao_id = p_lote_id
     and estado_otimizador = 'processando'
     and build_otimizador_id is null
     and build_bonificador_id is null;

  if not found then
    raise exception 'recuperação V20 recusada: a linha mudou durante a confirmação';
  end if;

  update clube_novo.otimizador_lote_producao_linha_v3
     set reserva_token = null,
         worker_id = null,
         reservada_em = null
   where lote_id = p_lote_id
     and linha_id = p_linha_id
     and reserva_token = v_reserva_token;

  if not found then
    raise exception 'recuperação V20 recusada: o token de reserva mudou durante a confirmação';
  end if;

  update clube_novo.otimizador_lote_producao_v3
     set estado = 'pausado',
         falha = null,
         finalizado_em = null,
         atualizado_em = clock_timestamp()
   where id = p_lote_id
     and estado = 'falhou'
     and falha = v_falha_exata;

  if not found then
    raise exception 'recuperação V20 recusada: o lote mudou durante a confirmação';
  end if;

  insert into clube_novo.otimizador_evento_producao_v3(lote_id, linha_id, evento, detalhe)
  values (
    p_lote_id,
    p_linha_id,
    'lote_pausado',
    jsonb_build_object(
      'recuperacao_falha_retomada_integral_v20', true,
      'falha_anterior', v_falha_exata,
      'linha_devolvida_a_pendente', p_linha_id,
      'card_id', v_card_id,
      'worker_id_anterior', v_worker_id,
      'preparo_concluido', v_lote.preparo_concluido,
      'preparo_total', v_lote.preparo_total,
      'resultado_existia', false,
      'pode_publicar', false,
      'formula_alterada', false,
      'linhas_concluidas_preservadas', true
    )
  );

  return public.otimizador_producao_status_v5(p_lote_id);
end
$function$;

revoke all on function public.otimizador_producao_recuperar_falha_retomada_integral_v1(uuid, bigint, boolean)
  from public, anon, authenticated;
grant execute on function public.otimizador_producao_recuperar_falha_retomada_integral_v1(uuid, bigint, boolean)
  to service_role;

comment on function public.otimizador_producao_recuperar_falha_retomada_integral_v1(uuid, bigint, boolean) is
  'V20: devolve a pendente somente a reserva sem resultado criada pela retomada integral que escolheu o contrato V3 após preparo completo.';

notify pgrst, 'reload schema';

commit;
