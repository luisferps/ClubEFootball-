-- V8 corrige somente o nome de evento da recuperação V7.
-- A tabela aceita `preparo_pausado`; a recuperação continua sem alterar fórmula,
-- entradas, pesos, estado de publicação ou linhas já concluídas.
begin;

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

commit;
