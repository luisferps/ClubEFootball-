-- Rollback recuperável da V10.
-- Restaura literalmente as definições V5/V3 de status que estavam vigentes
-- antes da V10. Não toca em lote, linhas, resultados, fórmula ou publicação.

begin;

create or replace function public.otimizador_producao_status_v5(p_lote_id uuid default null)
returns jsonb
language plpgsql
stable
security definer
set search_path to ''
as $$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_existe_integral boolean:=false;
  v_cards integer:=0; v_linhas integer:=0; v_pendentes integer:=0;
  v_processando integer:=0; v_concluidas integer:=0; v_bloqueadas integer:=0;
  v_interrompidas integer:=0; v_bonificador_pendentes integer:=0;
  v_preparo_total integer:=0; v_preparo_concluido integer:=0; v_preparo_pendentes integer:=0;
  v_preparo_incompletas integer:=0; v_preparo_sem_linha integer:=0; v_preparo_divergentes integer:=0;
  v_corrente jsonb:='[]'::jsonb; v_motivos jsonb:='[]'::jsonb;
begin
  select exists(
    select 1 from clube_novo.otimizador_lote_producao_v3
    where tipo_lote='integral'
  ) into v_existe_integral;

  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3 x
  where x.id=coalesce(p_lote_id,(
    select y.id
    from clube_novo.otimizador_lote_producao_v3 y
    order by
      (y.tipo_lote='integral' and y.estado not in ('encerrado','concluido','falhou')) desc,
      (y.tipo_lote='integral') desc,
      (y.estado not in ('encerrado','concluido','falhou')) desc,
      y.criado_em desc
    limit 1
  ));

  if not found then
    return jsonb_build_object(
      'contrato','otimizador_fila_producao_v5','lote_id',null,
      'estado','sem_lote','estado_lote','sem_lote','tipo_lote',null,
      'cards',0,'linhas',0,'pendentes',0,'processando',0,'concluidas',0,
      'bloqueadas',0,'interrompidas',0,'bonificador_pendentes',0,
      'corrente','[]'::jsonb,'motivos','[]'::jsonb,
      'preparo',jsonb_build_object('estado','nao_iniciado','total',0,'concluido',0,'pendentes',0),
      'acoes',jsonb_build_object('criar',true,'preparar',false,'iniciar',false,
        'retomar',false,'pausar',false,'parar',false,'console',false),
      'confirmacao',jsonb_build_object('parar_exige_confirmacao',true),
      'pode_publicar',false,'modo','producao_v5_sem_publicacao',
      'mensagem','Nenhuma fila integral foi criada; preparar não executa cartas.'
    );
  end if;

  select count(distinct q.card_id),count(*),
         count(*) filter(where l.estado_otimizador='pendente'),
         count(*) filter(where l.estado_otimizador='processando'),
         count(*) filter(where l.estado_otimizador='concluido'),
         count(*) filter(where l.estado_otimizador='bloqueado'),
         count(*) filter(where l.estado_otimizador='interrompido'),
         count(*) filter(where l.estado_otimizador='concluido' and l.build_bonificador_id is null)
  into v_cards,v_linhas,v_pendentes,v_processando,v_concluidas,v_bloqueadas,
       v_interrompidas,v_bonificador_pendentes
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id=q.linha_id
  where q.lote_id=v_lote.id;

  if v_lote.tipo_lote='integral' then
    select count(*),
           count(*) filter(where estado<>'pendente'),
           count(*) filter(where estado='pendente'),
           count(*) filter(where estado='incompleta'),
           count(*) filter(where estado='sem_linha'),
           count(*) filter(where estado='divergente')
    into v_preparo_total,v_preparo_concluido,v_preparo_pendentes,
         v_preparo_incompletas,v_preparo_sem_linha,v_preparo_divergentes
    from clube_novo.otimizador_lote_producao_candidata_v5
    where lote_id=v_lote.id;
  else
    v_preparo_total:=v_lote.preparo_total;
    v_preparo_concluido:=v_lote.preparo_concluido;
  end if;

  select coalesce(jsonb_agg(jsonb_build_object(
    'linha_id',l.id,'card_id',l.card_id,'funcao_id',l.funcao_id,'posicao_id',l.posicao_id,
    'estado',l.estado_otimizador,'motivo',l.erro_otimizador,
    'iniciada_em',l.otimizador_iniciado_em,'worker_id',q.worker_id
  ) order by q.ordem_fila),'[]'::jsonb)
  into v_corrente
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id=q.linha_id
  where q.lote_id=v_lote.id and l.estado_otimizador='processando';

  select coalesce(jsonb_agg(jsonb_build_object(
    'linha_id',l.id,'card_id',l.card_id,'funcao_id',l.funcao_id,'posicao_id',l.posicao_id,
    'estado',l.estado_otimizador,'motivo',l.erro_otimizador
  ) order by q.ordem_fila),'[]'::jsonb)
  into v_motivos
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id=q.linha_id
  where q.lote_id=v_lote.id and l.estado_otimizador in ('bloqueado','interrompido');

  return jsonb_build_object(
    'contrato','otimizador_fila_producao_v5','lote_id',v_lote.id,
    'tipo_lote',v_lote.tipo_lote,'fingerprint',v_lote.fingerprint,
    'formula_fingerprint',v_lote.formula_fingerprint,
    'contrato_fingerprint',v_lote.contrato_fingerprint,
    'motor_versao',v_lote.motor_versao,'estado',v_lote.estado,'estado_lote',v_lote.estado,
    'falha_lote',v_lote.falha,'cards',v_cards,'linhas',v_linhas,
    'pendentes',v_pendentes,'processando',v_processando,'concluidas',v_concluidas,
    'bloqueadas',v_bloqueadas,'interrompidas',v_interrompidas,
    'bonificador_pendentes',v_bonificador_pendentes,'corrente',v_corrente,'motivos',v_motivos,
    'preparo',jsonb_build_object(
      'estado',case when v_lote.tipo_lote='integral' then v_lote.estado else 'nao_aplicavel' end,
      'total',v_preparo_total,'concluido',v_preparo_concluido,'pendentes',v_preparo_pendentes,
      'incompletas',v_preparo_incompletas,'sem_linha',v_preparo_sem_linha,
      'divergentes',v_preparo_divergentes
    ),
    'exclusoes',jsonb_build_object(
      'incompletas',v_lote.excluidas_incompletas,
      'impeto_condicional_desligado',v_lote.excluidas_impeto_condicional,
      'sem_linha_canonica',v_lote.excluidas_sem_linha
    ),
    'acoes',jsonb_build_object(
      'criar',not v_existe_integral,
      'preparar',v_lote.tipo_lote='integral' and v_lote.estado='preparando',
      'iniciar',v_lote.estado='parado' and v_pendentes>0,
      'retomar',(
        v_lote.tipo_lote='integral' and v_lote.estado='preparo_pausado' and v_preparo_pendentes>0
      ) or (v_lote.estado='pausado' and v_pendentes>0),
      'pausar',v_lote.estado in ('preparando','rodando'),
      'parar',v_lote.estado in ('parado','rodando','pausando','pausado') and v_pendentes>0,
      'console',false
    ),
    'confirmacao',jsonb_build_object('parar_exige_confirmacao',true),
    'pode_publicar',false,'modo','producao_v5_sem_publicacao',
    'mensagem',case
      when v_lote.tipo_lote='integral' and v_lote.estado='preparando'
        then 'Preparando snapshots em fatias; nenhuma carta está sendo calculada.'
      when v_lote.tipo_lote='integral' and v_lote.estado='preparo_pausado'
        then 'Preparação pausada com candidatos e linhas já selados preservados.'
      when v_lote.estado='parado'
        then 'Fila selada e pronta; Iniciar é uma decisão separada para calcular cartas.'
      when v_lote.estado='rodando'
        then 'Otimizador em execução; cada linha possui reserva exclusiva.'
      when v_lote.estado='pausando'
        then 'Pausa solicitada; a linha atômica atual será finalizada ou bloqueada.'
      when v_lote.estado='pausado'
        then 'Fila pausada com pendências preservadas.'
      when v_lote.estado='encerrando'
        then 'Encerramento solicitado; nenhuma nova linha será reservada.'
      when v_lote.estado='encerrado'
        then 'Lote encerrado sem publicação; pendências foram marcadas interrompidas.'
      when v_lote.estado='concluido'
        then 'Otimizador concluiu este lote; resultados permanecem teste/não publicado.'
      else coalesce(v_lote.falha,'Lote falhou fechado; não há retomada automática.')
    end
  );
end
$$;

create or replace function public.otimizador_producao_status_v3(p_lote_id uuid default null)
returns jsonb
language plpgsql
stable
security definer
set search_path=''
as $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_cards integer:=0; v_linhas integer:=0; v_pendentes integer:=0;
  v_processando integer:=0; v_concluidas integer:=0; v_bloqueadas integer:=0;
  v_interrompidas integer:=0; v_bonificador_pendentes integer:=0;
  v_corrente jsonb:='[]'::jsonb; v_motivos jsonb:='[]'::jsonb;
  v_existe_algum boolean:=false;
begin
  select exists(select 1 from clube_novo.otimizador_lote_producao_v3) into v_existe_algum;
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3 x
  where x.id=coalesce(p_lote_id,(
    select y.id from clube_novo.otimizador_lote_producao_v3 y
    order by (y.estado not in ('encerrado','concluido','falhou')) desc,y.criado_em desc
    limit 1
  ));
  if not found then
    return jsonb_build_object(
      'contrato','otimizador_fila_producao_v3','lote_id',null,
      'estado','sem_lote','estado_lote','sem_lote','cards',0,'linhas',0,
      'pendentes',0,'processando',0,'concluidas',0,'bloqueadas',0,'interrompidas',0,
      'bonificador_pendentes',0,'corrente','[]'::jsonb,'motivos','[]'::jsonb,
      'acoes',jsonb_build_object('criar',not v_existe_algum,'iniciar',false,'retomar',false,
        'pausar',false,'parar',false,'console',false),
      'confirmacao',jsonb_build_object('parar_exige_confirmacao',true),
      'pode_publicar',false,'modo','producao_v3_sem_publicacao',
      'mensagem','Nenhuma fila produtiva V3 foi criada.'
    );
  end if;

  select count(distinct q.card_id),count(*),
         count(*) filter(where l.estado_otimizador='pendente'),
         count(*) filter(where l.estado_otimizador='processando'),
         count(*) filter(where l.estado_otimizador='concluido'),
         count(*) filter(where l.estado_otimizador='bloqueado'),
         count(*) filter(where l.estado_otimizador='interrompido'),
         count(*) filter(where l.estado_otimizador='concluido' and l.build_bonificador_id is null)
  into v_cards,v_linhas,v_pendentes,v_processando,v_concluidas,v_bloqueadas,
       v_interrompidas,v_bonificador_pendentes
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id=q.linha_id
  where q.lote_id=v_lote.id;

  select coalesce(jsonb_agg(jsonb_build_object(
    'linha_id',l.id,'card_id',l.card_id,'funcao_id',l.funcao_id,'posicao_id',l.posicao_id,
    'estado',l.estado_otimizador,'motivo',l.erro_otimizador,
    'iniciada_em',l.otimizador_iniciado_em,'worker_id',q.worker_id
  ) order by q.ordem_fila),'[]'::jsonb)
  into v_corrente
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id=q.linha_id
  where q.lote_id=v_lote.id and l.estado_otimizador='processando';

  select coalesce(jsonb_agg(jsonb_build_object(
    'linha_id',l.id,'card_id',l.card_id,'funcao_id',l.funcao_id,'posicao_id',l.posicao_id,
    'estado',l.estado_otimizador,'motivo',l.erro_otimizador
  ) order by q.ordem_fila),'[]'::jsonb)
  into v_motivos
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id=q.linha_id
  where q.lote_id=v_lote.id and l.estado_otimizador in ('bloqueado','interrompido');

  return jsonb_build_object(
    'contrato','otimizador_fila_producao_v3','lote_id',v_lote.id,
    'fingerprint',v_lote.fingerprint,'formula_fingerprint',v_lote.formula_fingerprint,
    'contrato_fingerprint',v_lote.contrato_fingerprint,'motor_versao',v_lote.motor_versao,
    'estado',v_lote.estado,'estado_lote',v_lote.estado,'falha_lote',v_lote.falha,
    'cards',v_cards,'linhas',v_linhas,'pendentes',v_pendentes,'processando',v_processando,
    'concluidas',v_concluidas,'bloqueadas',v_bloqueadas,'interrompidas',v_interrompidas,
    'bonificador_pendentes',v_bonificador_pendentes,'corrente',v_corrente,'motivos',v_motivos,
    'exclusoes',jsonb_build_object('incompletas',v_lote.excluidas_incompletas,
      'impeto_condicional_desligado',v_lote.excluidas_impeto_condicional,
      'sem_linha_canonica',v_lote.excluidas_sem_linha),
    'acoes',jsonb_build_object(
      'criar',false,
      'iniciar',v_lote.estado='parado' and v_pendentes>0,
      'retomar',v_lote.estado='pausado' and v_pendentes>0,
      'pausar',v_lote.estado='rodando',
      'parar',v_lote.estado in ('parado','rodando','pausando','pausado') and v_pendentes>0,
      'console',false
    ),
    'confirmacao',jsonb_build_object('parar_exige_confirmacao',true),
    'pode_publicar',false,'modo','producao_v3_sem_publicacao',
    'mensagem',case v_lote.estado
      when 'parado' then 'Fila V3 pronta; clique em Iniciar para processar as cartas mais fortes primeiro.'
      when 'rodando' then 'Otimizador em execução; a reserva exclusiva protege cada linha.'
      when 'pausando' then 'Pausa solicitada; a linha atômica atual será finalizada ou bloqueada.'
      when 'pausado' then 'Fila pausada com pendências preservadas.'
      when 'encerrando' then 'Encerramento solicitado; nenhuma nova linha será reservada.'
      when 'encerrado' then 'Lote encerrado sem publicação; pendências foram marcadas interrompidas.'
      when 'concluido' then 'Otimizador concluiu este lote; linhas concluídas aguardam o Bonificador.'
      else coalesce(v_lote.falha,'Lote falhou fechado; não há retomada automática.') end
  );
end
$function$;

revoke all on function public.otimizador_producao_status_v5(uuid)
  from public,anon,authenticated;
grant execute on function public.otimizador_producao_status_v5(uuid) to service_role;
revoke all on function public.otimizador_producao_status_v3(uuid)
  from public,anon,authenticated;
grant execute on function public.otimizador_producao_status_v3(uuid) to service_role;

commit;
