-- Rollback V54: restaura o corpo V11 de otimizador_producao_status_v6.
-- Não apaga lote, linha, resultado, fotografia local, fórmula ou publicação.

begin;

create or replace function public.otimizador_producao_status_v6(p_lote_id uuid default null)
returns jsonb
language plpgsql
stable
security definer
set search_path to ''
as $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_resumo clube_novo.otimizador_lote_producao_status_v1%rowtype;
  v_existe_integral boolean := false;
  v_preparo_pendentes integer := 0;
  v_preparo_divergentes integer := 0;
  v_corrente jsonb := '[]'::jsonb;
  v_motivos jsonb := '[]'::jsonb;
begin
  select exists(
    select 1 from clube_novo.otimizador_lote_producao_v3 where tipo_lote = 'integral'
  ) into v_existe_integral;

  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3 x
  where x.id = coalesce(p_lote_id, (
    select y.id
    from clube_novo.otimizador_lote_producao_v3 y
    order by
      (y.tipo_lote = 'integral' and y.estado not in ('encerrado','concluido','falhou')) desc,
      (y.tipo_lote = 'integral') desc,
      (y.estado not in ('encerrado','concluido','falhou')) desc,
      y.criado_em desc
    limit 1
  ));

  if not found then
    return jsonb_build_object(
      'contrato','otimizador_fila_producao_v6','lote_id',null,
      'estado','sem_lote','estado_lote','sem_lote','tipo_lote',null,
      'cards',0,'linhas',0,'pendentes',0,'processando',0,'concluidas',0,
      'bloqueadas',0,'interrompidas',0,'bonificador_pendentes',0,
      'corrente','[]'::jsonb,'motivos','[]'::jsonb,
      'preparo',jsonb_build_object('estado','nao_iniciado','total',0,'concluido',0,'pendentes',0),
      'acoes',jsonb_build_object('criar',true,'preparar',false,'iniciar',false,
        'retomar',false,'pausar',false,'parar',false,'console',false),
      'confirmacao',jsonb_build_object('parar_exige_confirmacao',true),
      'pode_publicar',false,'modo','producao_v6_sem_publicacao',
      'mensagem','Nenhuma fila integral foi criada; preparar não executa cartas.'
    );
  end if;

  select * into v_resumo
  from clube_novo.otimizador_lote_producao_status_v1
  where lote_id = v_lote.id;
  if not found then
    if coalesce(v_lote.linhas, 0) > 0 then
      raise exception 'V11 recusada: resumo de estado ausente para lote %', v_lote.id;
    end if;
    v_resumo.pendentes := 0;
    v_resumo.processando := 0;
    v_resumo.concluidas := 0;
    v_resumo.bloqueadas := 0;
    v_resumo.interrompidas := 0;
    v_resumo.bonificador_pendentes := 0;
  end if;

  v_preparo_pendentes := greatest(0, v_lote.preparo_total - v_lote.preparo_concluido);
  if v_lote.estado = 'falhou' and coalesce(v_lote.falha, '') like 'preparo%' then
    select count(*) into v_preparo_divergentes
    from clube_novo.otimizador_lote_producao_candidata_v5
    where lote_id = v_lote.id and estado = 'divergente';
  end if;

  select coalesce(jsonb_agg(jsonb_build_object(
    'linha_id',l.id,'card_id',l.card_id,'funcao_id',l.funcao_id,'posicao_id',l.posicao_id,
    'estado',l.estado_otimizador,'motivo',l.erro_otimizador,
    'iniciada_em',l.otimizador_iniciado_em,'worker_id',q.worker_id
  ) order by q.ordem_fila),'[]'::jsonb)
  into v_corrente
  from clube_novo.build_linha_card l
  join clube_novo.otimizador_lote_producao_linha_v3 q
    on q.lote_id = v_lote.id and q.linha_id = l.id
  where l.lote_producao_id = v_lote.id
    and l.estado_otimizador = 'processando';

  if v_resumo.bloqueadas + v_resumo.interrompidas <= 100 then
    select coalesce(jsonb_agg(jsonb_build_object(
      'linha_id',l.id,'card_id',l.card_id,'funcao_id',l.funcao_id,'posicao_id',l.posicao_id,
      'estado',l.estado_otimizador,'motivo',l.erro_otimizador
    ) order by q.ordem_fila),'[]'::jsonb)
    into v_motivos
    from clube_novo.build_linha_card l
    join clube_novo.otimizador_lote_producao_linha_v3 q
      on q.lote_id = v_lote.id and q.linha_id = l.id
    where l.lote_producao_id = v_lote.id
      and l.estado_otimizador in ('bloqueado','interrompido');
  end if;

  return jsonb_build_object(
    'contrato','otimizador_fila_producao_v6','lote_id',v_lote.id,
    'tipo_lote',v_lote.tipo_lote,'fingerprint',v_lote.fingerprint,
    'formula_fingerprint',v_lote.formula_fingerprint,
    'contrato_fingerprint',v_lote.contrato_fingerprint,
    'motor_versao',v_lote.motor_versao,'estado',v_lote.estado,'estado_lote',v_lote.estado,
    'falha_lote',v_lote.falha,'cards',v_lote.cards,'linhas',v_lote.linhas,
    'pendentes',v_resumo.pendentes,'processando',v_resumo.processando,
    'concluidas',v_resumo.concluidas,'bloqueadas',v_resumo.bloqueadas,
    'interrompidas',v_resumo.interrompidas,
    'bonificador_pendentes',v_resumo.bonificador_pendentes,
    'corrente',v_corrente,'motivos',v_motivos,
    'preparo',jsonb_build_object(
      'estado',case when v_lote.tipo_lote = 'integral' then v_lote.estado else 'nao_aplicavel' end,
      'total',v_lote.preparo_total,'concluido',v_lote.preparo_concluido,
      'pendentes',v_preparo_pendentes,
      'incompletas',v_lote.excluidas_incompletas,'sem_linha',v_lote.excluidas_sem_linha,
      'divergentes',v_preparo_divergentes
    ),
    'exclusoes',jsonb_build_object(
      'incompletas',v_lote.excluidas_incompletas,
      'impeto_condicional_desligado',v_lote.excluidas_impeto_condicional,
      'sem_linha_canonica',v_lote.excluidas_sem_linha
    ),
    'acoes',jsonb_build_object(
      'criar',not v_existe_integral,
      'preparar',v_lote.tipo_lote = 'integral' and v_lote.estado = 'preparando',
      'iniciar',v_lote.estado = 'parado' and v_resumo.pendentes > 0,
      'retomar',(
        v_lote.tipo_lote = 'integral' and v_lote.estado = 'preparo_pausado'
        and v_preparo_pendentes > 0
      ) or (v_lote.estado = 'pausado' and v_resumo.pendentes > 0),
      'pausar',v_lote.estado in ('preparando','rodando'),
      'parar',v_lote.estado in ('parado','rodando','pausando','pausado') and v_resumo.pendentes > 0,
      'console',false
    ),
    'confirmacao',jsonb_build_object('parar_exige_confirmacao',true),
    'pode_publicar',false,'modo','producao_v6_sem_publicacao',
    'mensagem',case
      when v_lote.tipo_lote = 'integral' and v_lote.estado = 'preparando'
        then 'Preparando snapshots em fatias; nenhuma carta está sendo calculada.'
      when v_lote.tipo_lote = 'integral' and v_lote.estado = 'preparo_pausado'
        then 'Preparação pausada com candidatos e linhas já selados preservados.'
      when v_lote.estado = 'parado'
        then 'Fila selada e pronta; Iniciar é uma decisão separada para calcular cartas.'
      when v_lote.estado = 'rodando'
        then 'Otimizador em execução; cada linha possui reserva exclusiva.'
      when v_lote.estado = 'pausando'
        then 'Pausa solicitada; a linha atômica atual será finalizada ou bloqueada.'
      when v_lote.estado = 'pausado'
        then 'Fila pausada com pendências preservadas.'
      when v_lote.estado = 'encerrando'
        then 'Encerramento solicitado; nenhuma nova linha será reservada.'
      when v_lote.estado = 'encerrado'
        then 'Lote encerrado sem publicação; pendências foram marcadas interrompidas.'
      when v_lote.estado = 'concluido'
        then 'Otimizador concluiu este lote; resultados permanecem teste/não publicado.'
      else coalesce(v_lote.falha,'Lote falhou fechado; não há retomada automática.')
    end
  );
end
$function$;

alter function public.otimizador_producao_status_v6(uuid) reset statement_timeout;
revoke all on function public.otimizador_producao_status_v6(uuid)
  from public, anon, authenticated;
grant execute on function public.otimizador_producao_status_v6(uuid) to service_role;

notify pgrst, 'reload schema';
commit;
