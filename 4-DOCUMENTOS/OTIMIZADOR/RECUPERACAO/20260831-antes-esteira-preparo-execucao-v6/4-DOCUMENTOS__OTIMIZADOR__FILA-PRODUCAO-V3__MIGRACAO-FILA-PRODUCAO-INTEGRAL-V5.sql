-- Fila integral do Otimizador: preparação incremental e selada.
--
-- Esta migração NÃO calcula builds, NÃO publica e NÃO habilita Ímpetos
-- condicionais. Ela apenas permite montar, em fatias pequenas e recuperáveis,
-- a mesma fila V3 que o worker já sabe executar depois de uma decisão explícita.
-- A fórmula aprovada continua selada pelo fingerprint abaixo.

begin;

do $$
begin
  -- Não é seguro introduzir linhagem por lote se houver produção antiga que
  -- não possa ser ligada ao lote que a originou.
  if exists (
    select 1
    from clube_novo.build_linha_card l
    where l.execucao_tipo='producao'
      and not exists (
        select 1
        from clube_novo.otimizador_lote_producao_linha_v3 q
        where q.linha_id=l.id
      )
  ) then
    raise exception 'migração V5 recusada: existe linha de produção sem lote V3 comprovado';
  end if;
end
$$;

alter table clube_novo.otimizador_lote_producao_v3
  add column if not exists tipo_lote text not null default 'piloto',
  add column if not exists preparo_total integer not null default 0,
  add column if not exists preparo_concluido integer not null default 0;

update clube_novo.otimizador_lote_producao_v3
set tipo_lote='piloto',
    preparo_total=cards,
    preparo_concluido=cards
where tipo_lote='piloto'
  and preparo_total=0
  and preparo_concluido=0;

alter table clube_novo.otimizador_lote_producao_v3
  add constraint otimizador_lote_producao_v3_tipo_lote_v5_check
  check (tipo_lote in ('piloto','integral'));

alter table clube_novo.otimizador_lote_producao_v3
  add constraint otimizador_lote_producao_v3_preparo_v5_check
  check (preparo_total >= 0 and preparo_concluido >= 0 and preparo_concluido <= preparo_total);

alter table clube_novo.otimizador_lote_producao_v3
  drop constraint otimizador_lote_producao_v3_estado_check;

alter table clube_novo.otimizador_lote_producao_v3
  add constraint otimizador_lote_producao_v3_estado_check
  check (estado in (
    'preparando','preparo_pausado',
    'parado','rodando','pausando','pausado',
    'encerrando','encerrado','concluido','falhou'
  ));

alter table clube_novo.build_linha_card
  add column if not exists lote_producao_id uuid;

update clube_novo.build_linha_card l
set lote_producao_id=q.lote_id
from clube_novo.otimizador_lote_producao_linha_v3 q
where q.linha_id=l.id
  and l.execucao_tipo='producao';

alter table clube_novo.build_linha_card
  add constraint build_linha_card_lote_producao_v5_fk
  foreign key (lote_producao_id)
  references clube_novo.otimizador_lote_producao_v3(id)
  on update restrict on delete restrict;

alter table clube_novo.build_linha_card
  add constraint build_linha_card_id_lote_producao_v5_key
  unique (id,lote_producao_id);

alter table clube_novo.otimizador_lote_producao_linha_v3
  add constraint otimizador_lote_producao_linha_v5_linhagem_fk
  foreign key (linha_id,lote_id)
  references clube_novo.build_linha_card(id,lote_producao_id)
  on update restrict on delete restrict;

drop index if exists clube_novo.build_linha_card_uma_ativa_por_contexto_uidx;

create unique index build_linha_card_contexto_por_lote_v5_uidx
  on clube_novo.build_linha_card(
    lote_producao_id,card_id,funcao_id,posicao_id,
    coalesce(impeto_condicional_codigo,-1),
    coalesce(impeto_condicional_nivel::integer,0)
  )
  where estado <> 'invalida' and execucao_tipo='producao';

alter table clube_novo.build_linha_card
  drop constraint build_linha_teste_campos_v1_check;

alter table clube_novo.build_linha_card
  add constraint build_linha_teste_campos_v1_check
  check (
    (
      execucao_tipo='producao'
      and lote_teste_id is null
      and amostra_ordem is null
      and lote_producao_id is not null
    )
    or
    (
      execucao_tipo='teste_isolado'
      and lote_teste_id is not null
      and lote_teste_semente is not null
      and btrim(lote_teste_semente)<>''
      and lote_teste_fingerprint ~ '^[0-9a-f]{64}$'
      and amostra_ordem between 1 and 100
      and sorteada_em is not null
      and lote_producao_id is null
    )
  );

alter table clube_novo.build_linha_card
  drop constraint build_linha_card_lote_estado_check;

alter table clube_novo.build_linha_card
  add constraint build_linha_card_lote_estado_check
  check (lote_estado is null or lote_estado in (
    'preparando','preparo_pausado',
    'parado','rodando','pausando','pausado',
    'encerrando','encerrado','concluido','falhou'
  ));

create index if not exists build_linha_card_lote_producao_v5_idx
  on clube_novo.build_linha_card(lote_producao_id,estado_otimizador)
  where lote_producao_id is not null;

create table clube_novo.otimizador_lote_producao_candidata_v5 (
  lote_id uuid not null,
  card_id text not null,
  ordem_candidata bigint not null,
  overall_snapshot integer not null,
  carta_versao_snapshot text not null,
  estado text not null default 'pendente',
  motivo text,
  preparado_em timestamptz,
  criado_em timestamptz not null default clock_timestamp(),
  atualizado_em timestamptz not null default clock_timestamp(),
  constraint otimizador_lote_producao_candidata_v5_pkey primary key (lote_id,card_id),
  constraint otimizador_lote_producao_candidata_v5_ordem_key unique (lote_id,ordem_candidata),
  constraint otimizador_lote_producao_candidata_v5_lote_fk
    foreign key (lote_id) references clube_novo.otimizador_lote_producao_v3(id)
    on update restrict on delete restrict,
  constraint otimizador_lote_producao_candidata_v5_card_fk
    foreign key (card_id) references clube_novo.carta_jogo(card_id)
    on update restrict on delete restrict,
  constraint otimizador_lote_producao_candidata_v5_estado_check
    check (estado in ('pendente','preparada','incompleta','sem_linha','divergente'))
);

create index otimizador_lote_producao_candidata_v5_progresso_idx
  on clube_novo.otimizador_lote_producao_candidata_v5(lote_id,estado,ordem_candidata);

alter table clube_novo.otimizador_lote_producao_candidata_v5 enable row level security;
revoke all on table clube_novo.otimizador_lote_producao_candidata_v5
  from public,anon,authenticated,service_role;

alter table clube_novo.otimizador_evento_producao_v3
  drop constraint otimizador_evento_producao_v3_evento_check;

alter table clube_novo.otimizador_evento_producao_v3
  add constraint otimizador_evento_producao_v3_evento_check
  check (evento in (
    'lote_criado','lote_iniciado','lote_retomado','pausa_solicitada','lote_pausado',
    'encerramento_solicitado','lote_encerrado','linha_reservada','linha_concluida',
    'linha_bloqueada','lote_concluido','lote_falhou',
    'preparo_integral_criado','preparo_fatia_concluida','preparo_pausa_solicitada',
    'preparo_pausado','preparo_retomado','preparo_integral_concluido','preparo_falhou'
  ));

-- A consulta da fila integral é paginada. A interface nunca recebe milhares
-- de linhas de uma vez nem usa texto como identidade de cálculo.
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

create or replace function public.otimizador_producao_prevoo_integral_v5()
returns jsonb
language plpgsql
stable
security definer
set search_path to ''
as $$
declare
  v_regua jsonb; v_elegiveis integer:=0; v_condicionais integer:=0;
begin
  select public.otimizador_regua_v2() into v_regua;
  select count(*) into v_elegiveis
  from clube_novo.carta_jogo c
  where coalesce(c.roda_motor,false)
    and coalesce(c.pode_rodar_vinculos,false)
    and c.overall is not null
    and not exists (
      select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=c.card_id and coalesce(ci.condicional,false)
    );
  select count(*) into v_condicionais
  from clube_novo.carta_jogo c
  where coalesce(c.roda_motor,false)
    and coalesce(c.pode_rodar_vinculos,false)
    and exists (
      select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=c.card_id and coalesce(ci.condicional,false)
    );
  return jsonb_build_object(
    'contrato','otimizador_fila_producao_v5',
    'formula_fingerprint','7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad',
    'gate_regua',v_regua->'gate',
    'candidatas_basicas',v_elegiveis,
    'excluidas_impeto_condicional',v_condicionais,
    'pode_publicar',false,
    'observacao','Pré-voo somente leitura; não cria lote nem calcula carta.'
  );
end
$$;

create or replace function public.otimizador_producao_criar_lote_integral_v5(
  p_lote_id uuid,
  p_formula_fingerprint text,
  p_motor_versao text
)
returns jsonb
language plpgsql
security definer
set search_path to ''
as $$
declare
  v_formula constant text:='7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad';
  v_regua jsonb; v_contrato_fp text; v_fingerprint text;
  v_total integer:=0; v_condicionais integer:=0; v_inseridas integer:=0;
begin
  if p_lote_id is null or p_formula_fingerprint<>v_formula
     or nullif(btrim(coalesce(p_motor_versao,'')),'') is null then
    raise exception 'criação integral recusada: selo de fórmula ou versão local inválidos';
  end if;
  if exists(
    select 1 from clube_novo.otimizador_lote_producao_v3 where tipo_lote='integral'
  ) then
    raise exception 'criação integral recusada: já existe lote integral V5; a recuperação exige decisão explícita';
  end if;

  select public.otimizador_regua_v2() into v_regua;
  if not coalesce((v_regua->'gate'->>'pode_rodar')::boolean,false) then
    raise exception 'criação integral recusada: gate da régua do Otimizador está fechado';
  end if;
  v_contrato_fp:=clube_novo.otimizador_producao_contrato_fingerprint_v3(v_regua);

  select count(*) into v_total
  from clube_novo.carta_jogo c
  where coalesce(c.roda_motor,false)
    and coalesce(c.pode_rodar_vinculos,false)
    and c.overall is not null
    and not exists(
      select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=c.card_id and coalesce(ci.condicional,false)
    );
  if v_total=0 then
    raise exception 'criação integral recusada: não há candidata básica elegível';
  end if;

  select count(*) into v_condicionais
  from clube_novo.carta_jogo c
  where coalesce(c.roda_motor,false)
    and coalesce(c.pode_rodar_vinculos,false)
    and exists(
      select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=c.card_id and coalesce(ci.condicional,false)
    );

  v_fingerprint:=encode(extensions.digest(convert_to(
    'preparando:'||p_lote_id::text||':'||v_formula||':'||v_contrato_fp||':'||p_motor_versao,
    'UTF8'),'sha256'),'hex');

  insert into clube_novo.otimizador_lote_producao_v3(
    id,tipo_lote,estado,formula_fingerprint,contrato_fingerprint,motor_versao,
    regua_snapshot,fingerprint,cards,linhas,preparo_total,preparo_concluido,
    excluidas_incompletas,excluidas_impeto_condicional,excluidas_sem_linha,pode_publicar
  ) values (
    p_lote_id,'integral','preparando',v_formula,v_contrato_fp,p_motor_versao,
    v_regua,v_fingerprint,0,0,v_total,0,0,v_condicionais,0,false
  );

  insert into clube_novo.otimizador_lote_producao_candidata_v5(
    lote_id,card_id,ordem_candidata,overall_snapshot,carta_versao_snapshot
  )
  select p_lote_id,c.card_id,
         row_number() over(order by c.overall desc,c.card_id)::bigint,
         c.overall::integer,coalesce(c.extraido_em::text,'')
  from clube_novo.carta_jogo c
  where coalesce(c.roda_motor,false)
    and coalesce(c.pode_rodar_vinculos,false)
    and c.overall is not null
    and not exists(
      select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=c.card_id and coalesce(ci.condicional,false)
    );
  get diagnostics v_inseridas=row_count;
  if v_inseridas<>v_total then
    raise exception 'criação integral recusada: fotografia de candidatas não foi preservada (% de %)',v_inseridas,v_total;
  end if;

  insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
  values(p_lote_id,'preparo_integral_criado',jsonb_build_object(
    'candidatas_basicas',v_total,
    'excluidas_impeto_condicional',v_condicionais,
    'ordem','overall_desc_card_id',
    'preparo','somente snapshots e linhas; nenhum cálculo foi iniciado',
    'pode_publicar',false
  ));
  return public.otimizador_producao_status_v5(p_lote_id);
end
$$;

create or replace function public.otimizador_producao_preparar_fatia_v5(
  p_lote_id uuid,
  p_limite integer default 10
)
returns jsonb
language plpgsql
security definer
set search_path to ''
as $$
declare
  v_formula constant text:='7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad';
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_c clube_novo.otimizador_lote_producao_candidata_v5%rowtype;
  v_entrada jsonb; v_bonificador jsonb; v_versao_atual text;
  v_motivo text; v_processadas integer:=0; v_linhas integer:=0;
  v_linhas_inseridas integer:=0; v_ordem_base bigint:=0;
  v_pendentes_preparo integer:=0; v_concluidas_preparo integer:=0;
  v_cards_final integer:=0; v_linhas_final integer:=0; v_fingerprint text;
begin
  if p_lote_id is null or coalesce(p_limite,0) not between 1 and 20 then
    raise exception 'preparo V5 recusado: lote e limite 1..20 são obrigatórios';
  end if;
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id=p_lote_id
  for update;
  if not found then raise exception 'lote integral V5 inexistente'; end if;
  if v_lote.tipo_lote<>'integral' then raise exception 'preparo V5 recusado: lote não é integral'; end if;
  if v_lote.formula_fingerprint<>v_formula or v_lote.pode_publicar is not false then
    raise exception 'preparo V5 recusado: selo do lote não é a fórmula aprovada';
  end if;
  if v_lote.estado<>'preparando' then
    return public.otimizador_producao_status_v5(p_lote_id);
  end if;

  loop
    exit when v_processadas>=p_limite;
    select * into v_c
    from clube_novo.otimizador_lote_producao_candidata_v5 c
    where c.lote_id=p_lote_id and c.estado='pendente'
    order by c.ordem_candidata
    for update skip locked
    limit 1;
    exit when not found;
    v_processadas:=v_processadas+1;

    begin
      v_versao_atual:=null;
      select coalesce(c.extraido_em::text,'') into v_versao_atual
      from clube_novo.carta_jogo c
      where c.card_id=v_c.card_id;
      if not found or v_versao_atual is distinct from v_c.carta_versao_snapshot then
        update clube_novo.otimizador_lote_producao_candidata_v5
        set estado='divergente',motivo='a versão física da carta mudou durante o preparo',
            atualizado_em=clock_timestamp()
        where lote_id=p_lote_id and card_id=v_c.card_id;
        update clube_novo.otimizador_lote_producao_v3
        set estado='falhou',falha='preparo recusado: a fonte de uma carta mudou; recrie a fotografia do lote',
            atualizado_em=clock_timestamp()
        where id=p_lote_id;
        insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
        values(p_lote_id,'preparo_falhou',jsonb_build_object(
          'card_id',v_c.card_id,'motivo','versão física divergente'
        ));
        return public.otimizador_producao_status_v5(p_lote_id);
      end if;

      select public.otimizador_carta_v3(v_c.card_id),
             public.bonificador_carta_v2(v_c.card_id)
      into v_entrada,v_bonificador;

      if v_entrada is null or v_bonificador is null
         or not coalesce((v_entrada->'gate'->>'pode_rodar')::boolean,false)
         or not coalesce((v_bonificador->>'pode_rodar')::boolean,false)
         or not (v_bonificador ? 'carta_versao')
         or not (v_bonificador ? 'carta_fingerprint') then
        v_motivo:=coalesce(v_entrada#>>'{gate,motivos}',v_bonificador#>>'{gate,motivos}',
          'contrato de entrada incompleto ou gate fechado');
        update clube_novo.otimizador_lote_producao_candidata_v5
        set estado='incompleta',motivo=left(v_motivo,1000),preparado_em=clock_timestamp(),
            atualizado_em=clock_timestamp()
        where lote_id=p_lote_id and card_id=v_c.card_id;
        update clube_novo.otimizador_lote_producao_v3
        set excluidas_incompletas=excluidas_incompletas+1,
            preparo_concluido=preparo_concluido+1,atualizado_em=clock_timestamp()
        where id=p_lote_id;
      else
        select count(*) into v_linhas
        from (
          select distinct fp.funcao_id,fp.posicao_id
          from (
            select cpp.posicao_id
            from clube_novo.carta_posicao_principal_jogo cpp
            where cpp.card_id=v_c.card_id
            union
            select cp.posicao_id
            from clube_novo.carta_posicao_jogo cp
            where cp.card_id=v_c.card_id and cp.nivel_aptidao>0
          ) px
          join clube_novo.otimizador_funcao_posicao fp on fp.posicao_id=px.posicao_id
          join clube_novo.funcao_sistema fs on fs.id=fp.funcao_id and fs.ativa and fs.pode_rodar
          join clube_novo.posicao_jogo p on p.id=fp.posicao_id and p.pode_rodar
        ) linhas;

        if v_linhas=0 then
          update clube_novo.otimizador_lote_producao_candidata_v5
          set estado='sem_linha',motivo='não há posição e função canônicas aptas para a carta',
              preparado_em=clock_timestamp(),atualizado_em=clock_timestamp()
          where lote_id=p_lote_id and card_id=v_c.card_id;
          update clube_novo.otimizador_lote_producao_v3
          set excluidas_sem_linha=excluidas_sem_linha+1,
              preparo_concluido=preparo_concluido+1,atualizado_em=clock_timestamp()
          where id=p_lote_id;
        else
          insert into clube_novo.otimizador_lote_producao_carta_v3(
            lote_id,card_id,overall_snapshot,entrada_otimizador,entrada_fingerprint,
            carta_versao_bonificador,carta_fingerprint_bonificador
          ) values (
            p_lote_id,v_c.card_id,v_c.overall_snapshot,v_entrada,
            encode(extensions.digest(convert_to(v_entrada::text,'UTF8'),'sha256'),'hex'),
            v_bonificador->>'carta_versao',v_bonificador->>'carta_fingerprint'
          );

          select coalesce(max(ordem_fila),0) into v_ordem_base
          from clube_novo.otimizador_lote_producao_linha_v3
          where lote_id=p_lote_id;

          with linhas_base as (
            select distinct fp.funcao_id,fp.posicao_id
            from (
              select cpp.posicao_id
              from clube_novo.carta_posicao_principal_jogo cpp
              where cpp.card_id=v_c.card_id
              union
              select cp.posicao_id
              from clube_novo.carta_posicao_jogo cp
              where cp.card_id=v_c.card_id and cp.nivel_aptidao>0
            ) px
            join clube_novo.otimizador_funcao_posicao fp on fp.posicao_id=px.posicao_id
            join clube_novo.funcao_sistema fs on fs.id=fp.funcao_id and fs.ativa and fs.pode_rodar
            join clube_novo.posicao_jogo p on p.id=fp.posicao_id and p.pode_rodar
          ), inseridas as (
            insert into clube_novo.build_linha_card(
              card_id,funcao_id,posicao_id,lote_producao_id,carta_versao,carta_fingerprint,
              estado,pendencias,execucao_tipo,estado_otimizador,
              otimizador_formula_fingerprint_esperado,otimizador_contrato_fingerprint_esperado,
              otimizador_motor_versao_esperada,impeto_condicional_codigo,impeto_condicional_nivel
            )
            select v_c.card_id,b.funcao_id,b.posicao_id,p_lote_id,
                   v_bonificador->>'carta_versao',v_bonificador->>'carta_fingerprint',
                   'pendente','{}'::text[],'producao','pendente',
                   v_lote.formula_fingerprint,v_lote.contrato_fingerprint,v_lote.motor_versao,
                   null::integer,null::smallint
            from linhas_base b
            order by b.funcao_id,b.posicao_id
            returning id,card_id,funcao_id,posicao_id
          )
          insert into clube_novo.otimizador_lote_producao_linha_v3(
            lote_id,linha_id,card_id,ordem_fila,overall_snapshot,entrada_fingerprint
          )
          select p_lote_id,i.id,i.card_id,
                 v_ordem_base+row_number() over(order by b.funcao_id,b.posicao_id),
                 v_c.overall_snapshot,
                 encode(extensions.digest(convert_to(v_entrada::text,'UTF8'),'sha256'),'hex')
          from inseridas i
          join linhas_base b
            on b.funcao_id=i.funcao_id and b.posicao_id=i.posicao_id;
          get diagnostics v_linhas_inseridas=row_count;
          if v_linhas_inseridas<>v_linhas then
            raise exception 'preparo recusado: cardinalidade de linhas divergente para card_id %',v_c.card_id;
          end if;

          update clube_novo.otimizador_lote_producao_candidata_v5
          set estado='preparada',motivo=null,preparado_em=clock_timestamp(),atualizado_em=clock_timestamp()
          where lote_id=p_lote_id and card_id=v_c.card_id;
          update clube_novo.otimizador_lote_producao_v3
          set cards=cards+1,linhas=linhas+v_linhas,
              preparo_concluido=preparo_concluido+1,atualizado_em=clock_timestamp()
          where id=p_lote_id;
        end if;
      end if;
    exception when others then
      v_motivo:=left(sqlerrm,1000);
      update clube_novo.otimizador_lote_producao_candidata_v5
      set estado='divergente',motivo=v_motivo,atualizado_em=clock_timestamp()
      where lote_id=p_lote_id and card_id=v_c.card_id;
      update clube_novo.otimizador_lote_producao_v3
      set estado='falhou',falha='preparo V5 falhou fechado: '||v_motivo,
          atualizado_em=clock_timestamp()
      where id=p_lote_id;
      insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
      values(p_lote_id,'preparo_falhou',jsonb_build_object('card_id',v_c.card_id,'motivo',v_motivo));
      return public.otimizador_producao_status_v5(p_lote_id);
    end;
  end loop;

  select count(*) filter(where estado='pendente'),count(*) filter(where estado<>'pendente')
  into v_pendentes_preparo,v_concluidas_preparo
  from clube_novo.otimizador_lote_producao_candidata_v5
  where lote_id=p_lote_id;

  if v_pendentes_preparo=0 then
    select count(distinct card_id),count(*) into v_cards_final,v_linhas_final
    from clube_novo.otimizador_lote_producao_linha_v3
    where lote_id=p_lote_id;
    if v_linhas_final=0 then
      update clube_novo.otimizador_lote_producao_v3
      set estado='falhou',falha='preparo V5 terminou sem linha canônica apta',
          preparo_concluido=v_concluidas_preparo,atualizado_em=clock_timestamp()
      where id=p_lote_id;
      insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
      values(p_lote_id,'preparo_falhou',jsonb_build_object('motivo','nenhuma linha apta'));
    else
      select encode(extensions.digest(convert_to(
        p_lote_id::text||':'||v_lote.formula_fingerprint||':'||v_lote.contrato_fingerprint||':'||
        v_lote.motor_versao||':'||
        string_agg(card_id||':'||funcao_id::text||':'||posicao_id::text||':'||ordem_fila::text,
                   ',' order by ordem_fila),
        'UTF8'),'sha256'),'hex')
      into v_fingerprint
      from clube_novo.otimizador_lote_producao_linha_v3
      where lote_id=p_lote_id;
      update clube_novo.otimizador_lote_producao_v3
      set estado='parado',cards=v_cards_final,linhas=v_linhas_final,
          preparo_concluido=v_concluidas_preparo,fingerprint=v_fingerprint,
          atualizado_em=clock_timestamp()
      where id=p_lote_id;
      insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
      values(p_lote_id,'preparo_integral_concluido',jsonb_build_object(
        'cards',v_cards_final,'linhas',v_linhas_final,'fingerprint',v_fingerprint,
        'impetos_condicionais','desligados','pode_publicar',false
      ));
    end if;
  elsif v_processadas>0 then
    insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
    values(p_lote_id,'preparo_fatia_concluida',jsonb_build_object(
      'candidatas_processadas',v_processadas,'pendentes_preparo',v_pendentes_preparo
    ));
  end if;
  return public.otimizador_producao_status_v5(p_lote_id);
end
$$;

create or replace function public.otimizador_producao_controlar_preparo_v5(
  p_lote_id uuid,
  p_acao text
)
returns jsonb
language plpgsql
security definer
set search_path to ''
as $$
declare v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
begin
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id=p_lote_id
  for update;
  if not found or v_lote.tipo_lote<>'integral' then
    raise exception 'controle de preparo recusado: lote integral inexistente';
  end if;
  if p_acao='pausar' then
    if v_lote.estado<>'preparando' then raise exception 'pausa de preparo não autorizada pelo estado atual'; end if;
    -- O lock do cabeçalho aguarda a fatia atômica já em curso antes de pausar.
    update clube_novo.otimizador_lote_producao_v3
    set estado='preparo_pausado',atualizado_em=clock_timestamp()
    where id=p_lote_id;
    insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento)
    values(p_lote_id,'preparo_pausado');
  elsif p_acao='retomar' then
    if v_lote.estado<>'preparo_pausado' then raise exception 'retomada de preparo não autorizada pelo estado atual'; end if;
    update clube_novo.otimizador_lote_producao_v3
    set estado='preparando',atualizado_em=clock_timestamp()
    where id=p_lote_id;
    insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento)
    values(p_lote_id,'preparo_retomado');
  else
    raise exception 'ação de preparo inválida';
  end if;
  return public.otimizador_producao_status_v5(p_lote_id);
end
$$;

create or replace function public.otimizador_producao_fila_paginada_v5(
  p_lote_id uuid,
  p_offset integer default 0,
  p_limite integer default 100,
  p_somente_finais boolean default false
)
returns jsonb
language plpgsql
stable
security definer
set search_path to ''
as $$
declare v_total integer:=0; v_itens jsonb:='[]'::jsonb;
begin
  if p_lote_id is null or coalesce(p_offset,0)<0 or coalesce(p_limite,0) not between 1 and 200 then
    raise exception 'leitura paginada V5 recusada: parâmetros fora da faixa';
  end if;
  select count(*) into v_total
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id=q.linha_id
  where q.lote_id=p_lote_id
    and (not p_somente_finais or l.estado_otimizador in ('concluido','bloqueado','interrompido'));
  select coalesce(jsonb_agg(to_jsonb(x) order by x.ordem_fila),'[]'::jsonb) into v_itens
  from (
    select q.ordem_fila,l.id as linha_id,l.card_id,l.funcao_id,l.posicao_id,
      l.estado_otimizador as estado,l.erro_otimizador as motivo,
      l.otimizador_iniciado_em as iniciada_em,l.otimizador_finalizado_em as finalizada_em,
      q.overall_snapshot,o.tecnico_id,o.pontuacao as pontuacao_final,o.pontuacao as b1,
      o.barras,o.impeto_adicional_codigo,
      coalesce(to_jsonb(o.habilidades_adicionais),'[]'::jsonb) as habilidades_adicionais,
      o.builds_comparadas::text as builds_comparadas,
      o.builds_possiveis::text as builds_possiveis,
      case when l.otimizador_iniciado_em is not null and l.otimizador_finalizado_em is not null
        then extract(epoch from l.otimizador_finalizado_em-l.otimizador_iniciado_em) end as duracao_segundos,
      case when l.build_bonificador_id is not null then 'concluido'
           when l.estado_otimizador='concluido' then 'pendente' else 'aguardando_otimizador' end as bonificador
    from clube_novo.otimizador_lote_producao_linha_v3 q
    join clube_novo.build_linha_card l on l.id=q.linha_id
    left join clube_novo.build_otimizador o on o.id=l.build_otimizador_id
    where q.lote_id=p_lote_id
      and (not p_somente_finais or l.estado_otimizador in ('concluido','bloqueado','interrompido'))
    order by q.ordem_fila
    offset p_offset limit p_limite
  ) x;
  return jsonb_build_object(
    'contrato','otimizador_fila_producao_v5','lote_id',p_lote_id,
    'total',v_total,'offset',p_offset,'limite',p_limite,
    'somente_finais',p_somente_finais,'itens',v_itens
  );
end
$$;

create or replace function public.otimizador_producao_eventos_paginados_v5(
  p_lote_id uuid,
  p_offset integer default 0,
  p_limite integer default 100
)
returns jsonb
language plpgsql
stable
security definer
set search_path to ''
as $$
declare v_total integer:=0; v_itens jsonb:='[]'::jsonb;
begin
  if p_lote_id is null or coalesce(p_offset,0)<0 or coalesce(p_limite,0) not between 1 and 200 then
    raise exception 'leitura de eventos V5 recusada: parâmetros fora da faixa';
  end if;
  select count(*) into v_total
  from clube_novo.otimizador_evento_producao_v3 where lote_id=p_lote_id;
  select coalesce(jsonb_agg(to_jsonb(x) order by x.id desc),'[]'::jsonb) into v_itens
  from (
    select id,linha_id,evento,detalhe,criado_em
    from clube_novo.otimizador_evento_producao_v3
    where lote_id=p_lote_id
    order by id desc offset p_offset limit p_limite
  ) x;
  return jsonb_build_object(
    'contrato','otimizador_fila_producao_v5','lote_id',p_lote_id,
    'total',v_total,'offset',p_offset,'limite',p_limite,'itens',v_itens
  );
end
$$;

create or replace function public.otimizador_cartas_apresentacao_v2(p_card_ids text[])
returns jsonb
language plpgsql
stable
security definer
set search_path to ''
as $$
declare v_itens jsonb:='[]'::jsonb;
begin
  if p_card_ids is null or cardinality(p_card_ids)>200 then
    raise exception 'apresentação V2 recusada: lote de card_id vazio ou maior que 200';
  end if;
  select coalesce(jsonb_agg(jsonb_build_object(
    'card_id',c.card_id,'nome',c.nome,'overall',c.overall,
    'posicao_principal_id',cpp.posicao_id
  ) order by c.card_id),'[]'::jsonb)
  into v_itens
  from clube_novo.carta_jogo c
  left join clube_novo.carta_posicao_principal_jogo cpp on cpp.card_id=c.card_id
  where c.card_id=any(p_card_ids);
  return jsonb_build_object('contrato','otimizador_apresentacao_v2','itens',v_itens);
end
$$;

-- A criação e a leitura V3 completa eram seguras apenas para o piloto pequeno.
-- Após V5, ficam sem execução pelo service_role para não haver fallback integral
-- que carregue todas as cartas numa única transação ou resposta HTTP.
revoke all on function public.otimizador_producao_criar_lote_v3(uuid,text,text,integer)
  from public,anon,authenticated,service_role;
revoke all on function public.otimizador_producao_fila_v3(uuid)
  from public,anon,authenticated,service_role;

revoke all on function public.otimizador_producao_status_v5(uuid)
  from public,anon,authenticated;
revoke all on function public.otimizador_producao_prevoo_integral_v5()
  from public,anon,authenticated;
revoke all on function public.otimizador_producao_criar_lote_integral_v5(uuid,text,text)
  from public,anon,authenticated;
revoke all on function public.otimizador_producao_preparar_fatia_v5(uuid,integer)
  from public,anon,authenticated;
revoke all on function public.otimizador_producao_controlar_preparo_v5(uuid,text)
  from public,anon,authenticated;
revoke all on function public.otimizador_producao_fila_paginada_v5(uuid,integer,integer,boolean)
  from public,anon,authenticated;
revoke all on function public.otimizador_producao_eventos_paginados_v5(uuid,integer,integer)
  from public,anon,authenticated;
revoke all on function public.otimizador_cartas_apresentacao_v2(text[])
  from public,anon,authenticated;

grant execute on function public.otimizador_producao_status_v5(uuid) to service_role;
grant execute on function public.otimizador_producao_prevoo_integral_v5() to service_role;
grant execute on function public.otimizador_producao_criar_lote_integral_v5(uuid,text,text) to service_role;
grant execute on function public.otimizador_producao_preparar_fatia_v5(uuid,integer) to service_role;
grant execute on function public.otimizador_producao_controlar_preparo_v5(uuid,text) to service_role;
grant execute on function public.otimizador_producao_fila_paginada_v5(uuid,integer,integer,boolean) to service_role;
grant execute on function public.otimizador_producao_eventos_paginados_v5(uuid,integer,integer) to service_role;
grant execute on function public.otimizador_cartas_apresentacao_v2(text[]) to service_role;

commit;
