-- V11 — leitura de status resiliente da esteira integral.
--
-- O resumo de estados é derivado/transacional: não altera fórmula, pesos,
-- moldes, snapshots, cartas, resultados, publicação ou estados de negócio.
-- Ele elimina varreduras repetidas da fila integral durante acompanhamento.

begin;

do $$
begin
  if to_regclass('clube_novo.otimizador_lote_producao_v3') is null
     or to_regclass('clube_novo.build_linha_card') is null
     or to_regprocedure('public.otimizador_producao_status_v5(uuid)') is null then
    raise exception 'V11 recusada: fila produtiva V5 não está presente';
  end if;
end
$$;

create table if not exists clube_novo.otimizador_lote_producao_status_v1 (
  lote_id uuid primary key
    references clube_novo.otimizador_lote_producao_v3(id) on delete cascade,
  pendentes integer not null default 0 check (pendentes >= 0),
  processando integer not null default 0 check (processando >= 0),
  concluidas integer not null default 0 check (concluidas >= 0),
  bloqueadas integer not null default 0 check (bloqueadas >= 0),
  interrompidas integer not null default 0 check (interrompidas >= 0),
  bonificador_pendentes integer not null default 0 check (bonificador_pendentes >= 0),
  atualizado_em timestamptz not null default clock_timestamp()
);

-- Uma única leitura de recuperação, restrita à fila integral ainda aberta.
-- Não varre lotes históricos. Não toca linhas, resultados ou estados; após o
-- commit, cada mudança atualiza só este resumo.
insert into clube_novo.otimizador_lote_producao_status_v1(
  lote_id, pendentes, processando, concluidas, bloqueadas, interrompidas,
  bonificador_pendentes, atualizado_em
)
select
  lote.id,
  (select count(*)::integer from clube_novo.build_linha_card l
   where l.lote_producao_id = lote.id and l.estado_otimizador = 'pendente'),
  (select count(*)::integer from clube_novo.build_linha_card l
   where l.lote_producao_id = lote.id and l.estado_otimizador = 'processando'),
  (select count(*)::integer from clube_novo.build_linha_card l
   where l.lote_producao_id = lote.id and l.estado_otimizador = 'concluido'),
  (select count(*)::integer from clube_novo.build_linha_card l
   where l.lote_producao_id = lote.id and l.estado_otimizador = 'bloqueado'),
  (select count(*)::integer from clube_novo.build_linha_card l
   where l.lote_producao_id = lote.id and l.estado_otimizador = 'interrompido'),
  (select count(*)::integer from clube_novo.build_linha_card l
   where l.lote_producao_id = lote.id
     and l.estado_otimizador = 'concluido'
     and l.build_bonificador_id is null),
  clock_timestamp()
from clube_novo.otimizador_lote_producao_v3 lote
where lote.tipo_lote = 'integral'
  and lote.estado not in ('encerrado','concluido','falhou')
on conflict (lote_id) do update
set pendentes = excluded.pendentes,
    processando = excluded.processando,
    concluidas = excluded.concluidas,
    bloqueadas = excluded.bloqueadas,
    interrompidas = excluded.interrompidas,
    bonificador_pendentes = excluded.bonificador_pendentes,
    atualizado_em = excluded.atualizado_em;

create or replace function clube_novo.atualizar_status_lote_otimizador_v1()
returns trigger
language plpgsql
security definer
set search_path to ''
as $$
begin
  if tg_op = 'INSERT' then
    insert into clube_novo.otimizador_lote_producao_status_v1(
      lote_id, pendentes, processando, concluidas, bloqueadas, interrompidas,
      bonificador_pendentes, atualizado_em
    )
    select
      n.lote_producao_id,
      count(*) filter (where n.estado_otimizador = 'pendente')::integer,
      count(*) filter (where n.estado_otimizador = 'processando')::integer,
      count(*) filter (where n.estado_otimizador = 'concluido')::integer,
      count(*) filter (where n.estado_otimizador = 'bloqueado')::integer,
      count(*) filter (where n.estado_otimizador = 'interrompido')::integer,
      count(*) filter (
        where n.estado_otimizador = 'concluido'
          and n.build_bonificador_id is null
      )::integer,
      clock_timestamp()
    from novas_linhas n
    where n.lote_producao_id is not null
    group by n.lote_producao_id
    on conflict (lote_id) do update
    set pendentes = clube_novo.otimizador_lote_producao_status_v1.pendentes + excluded.pendentes,
        processando = clube_novo.otimizador_lote_producao_status_v1.processando + excluded.processando,
        concluidas = clube_novo.otimizador_lote_producao_status_v1.concluidas + excluded.concluidas,
        bloqueadas = clube_novo.otimizador_lote_producao_status_v1.bloqueadas + excluded.bloqueadas,
        interrompidas = clube_novo.otimizador_lote_producao_status_v1.interrompidas + excluded.interrompidas,
        bonificador_pendentes = clube_novo.otimizador_lote_producao_status_v1.bonificador_pendentes + excluded.bonificador_pendentes,
        atualizado_em = excluded.atualizado_em;
  elsif tg_op = 'DELETE' then
    insert into clube_novo.otimizador_lote_producao_status_v1(
      lote_id, pendentes, processando, concluidas, bloqueadas, interrompidas,
      bonificador_pendentes, atualizado_em
    )
    select
      a.lote_producao_id,
      -count(*) filter (where a.estado_otimizador = 'pendente')::integer,
      -count(*) filter (where a.estado_otimizador = 'processando')::integer,
      -count(*) filter (where a.estado_otimizador = 'concluido')::integer,
      -count(*) filter (where a.estado_otimizador = 'bloqueado')::integer,
      -count(*) filter (where a.estado_otimizador = 'interrompido')::integer,
      -count(*) filter (
        where a.estado_otimizador = 'concluido'
          and a.build_bonificador_id is null
      )::integer,
      clock_timestamp()
    from antigas_linhas a
    where a.lote_producao_id is not null
    group by a.lote_producao_id
    on conflict (lote_id) do update
    set pendentes = clube_novo.otimizador_lote_producao_status_v1.pendentes + excluded.pendentes,
        processando = clube_novo.otimizador_lote_producao_status_v1.processando + excluded.processando,
        concluidas = clube_novo.otimizador_lote_producao_status_v1.concluidas + excluded.concluidas,
        bloqueadas = clube_novo.otimizador_lote_producao_status_v1.bloqueadas + excluded.bloqueadas,
        interrompidas = clube_novo.otimizador_lote_producao_status_v1.interrompidas + excluded.interrompidas,
        bonificador_pendentes = clube_novo.otimizador_lote_producao_status_v1.bonificador_pendentes + excluded.bonificador_pendentes,
        atualizado_em = excluded.atualizado_em;
  else
    with mudancas as (
      select
        a.lote_producao_id as lote_antigo,
        a.estado_otimizador as estado_antigo,
        a.build_bonificador_id as bonificador_antigo,
        n.lote_producao_id as lote_novo,
        n.estado_otimizador as estado_novo,
        n.build_bonificador_id as bonificador_novo
      from antigas_linhas a
      join novas_linhas n using (id)
      where a.lote_producao_id is distinct from n.lote_producao_id
         or a.estado_otimizador is distinct from n.estado_otimizador
         or a.build_bonificador_id is distinct from n.build_bonificador_id
    ), transicoes as (
      select lote_antigo as lote_id, estado_antigo as estado,
             bonificador_antigo as build_bonificador_id, -1 as sinal
      from mudancas
      union all
      select lote_novo, estado_novo, bonificador_novo, 1
      from mudancas
    ), delta as (
      select
        lote_id,
        sum(case when estado = 'pendente' then sinal else 0 end)::integer as pendentes,
        sum(case when estado = 'processando' then sinal else 0 end)::integer as processando,
        sum(case when estado = 'concluido' then sinal else 0 end)::integer as concluidas,
        sum(case when estado = 'bloqueado' then sinal else 0 end)::integer as bloqueadas,
        sum(case when estado = 'interrompido' then sinal else 0 end)::integer as interrompidas,
        sum(case when estado = 'concluido' and build_bonificador_id is null then sinal else 0 end)::integer as bonificador_pendentes
      from transicoes
      where lote_id is not null
      group by lote_id
    )
    insert into clube_novo.otimizador_lote_producao_status_v1(
      lote_id, pendentes, processando, concluidas, bloqueadas, interrompidas,
      bonificador_pendentes, atualizado_em
    )
    select
      lote_id, pendentes, processando, concluidas, bloqueadas, interrompidas,
      bonificador_pendentes, clock_timestamp()
    from delta
    where pendentes <> 0 or processando <> 0 or concluidas <> 0
       or bloqueadas <> 0 or interrompidas <> 0 or bonificador_pendentes <> 0
    on conflict (lote_id) do update
    set pendentes = clube_novo.otimizador_lote_producao_status_v1.pendentes + excluded.pendentes,
        processando = clube_novo.otimizador_lote_producao_status_v1.processando + excluded.processando,
        concluidas = clube_novo.otimizador_lote_producao_status_v1.concluidas + excluded.concluidas,
        bloqueadas = clube_novo.otimizador_lote_producao_status_v1.bloqueadas + excluded.bloqueadas,
        interrompidas = clube_novo.otimizador_lote_producao_status_v1.interrompidas + excluded.interrompidas,
        bonificador_pendentes = clube_novo.otimizador_lote_producao_status_v1.bonificador_pendentes + excluded.bonificador_pendentes,
        atualizado_em = excluded.atualizado_em;
  end if;
  return null;
end
$$;

drop trigger if exists build_linha_status_otimizador_v11_insert
  on clube_novo.build_linha_card;
drop trigger if exists build_linha_status_otimizador_v11_update
  on clube_novo.build_linha_card;
drop trigger if exists build_linha_status_otimizador_v11_delete
  on clube_novo.build_linha_card;

create trigger build_linha_status_otimizador_v11_insert
after insert on clube_novo.build_linha_card
referencing new table as novas_linhas
for each statement execute function clube_novo.atualizar_status_lote_otimizador_v1();

create trigger build_linha_status_otimizador_v11_update
after update on clube_novo.build_linha_card
referencing old table as antigas_linhas new table as novas_linhas
for each statement execute function clube_novo.atualizar_status_lote_otimizador_v1();

create trigger build_linha_status_otimizador_v11_delete
after delete on clube_novo.build_linha_card
referencing old table as antigas_linhas
for each statement execute function clube_novo.atualizar_status_lote_otimizador_v1();

create or replace function public.otimizador_producao_status_v6(p_lote_id uuid default null)
returns jsonb
language plpgsql
stable
security definer
set search_path to ''
as $$
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
$$;

create or replace function public.otimizador_producao_controle_lote_v1(p_lote_id uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path to ''
as $$
declare v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
begin
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id;
  if not found then
    raise exception 'controle V1 recusado: lote inexistente';
  end if;
  return jsonb_build_object(
    'contrato','otimizador_fila_producao_v3',
    'lote_id',v_lote.id,
    'estado',v_lote.estado,
    'estado_lote',v_lote.estado,
    'tipo_lote',v_lote.tipo_lote,
    'pode_publicar',false
  );
end
$$;

-- Página operacional: as linhas que ainda podem rodar vêm primeiro, na ordem
-- real de reserva. As finais só entram depois delas. Isso é apresentação; a
-- ordem canônica da fila, os estados e a fórmula permanecem inalterados.
create or replace function public.otimizador_producao_fila_operacional_v1(
  p_lote_id uuid,
  p_offset integer default 0,
  p_limite integer default 100,
  p_grupo text default 'abertas'
)
returns jsonb
language plpgsql
stable
security definer
set search_path to ''
as $$
declare
  v_total integer := 0;
  v_itens jsonb := '[]'::jsonb;
begin
  if p_lote_id is null
     or coalesce(p_offset, 0) < 0
     or coalesce(p_limite, 0) not between 1 and 200
     or p_grupo not in ('abertas','finais') then
    raise exception 'leitura operacional V1 recusada: parâmetros fora da faixa';
  end if;

  select case when p_grupo = 'abertas'
              then s.pendentes + s.processando
              else s.concluidas + s.bloqueadas + s.interrompidas end
  into v_total
  from clube_novo.otimizador_lote_producao_status_v1 s
  where s.lote_id = p_lote_id;

  if not found then
    raise exception 'leitura operacional V1 recusada: resumo do lote ausente';
  end if;

  select coalesce(jsonb_agg(to_jsonb(x) order by x.grupo_ordem, x.ordem_fila),'[]'::jsonb)
  into v_itens
  from (
    select
      case when l.estado_otimizador = 'processando' then 0 else 1 end as grupo_ordem,
      q.ordem_fila,l.id as linha_id,l.card_id,l.funcao_id,l.posicao_id,
      l.estado_otimizador as estado,l.erro_otimizador as motivo,
      l.otimizador_iniciado_em as iniciada_em,l.otimizador_finalizado_em as finalizada_em,
      q.overall_snapshot,o.tecnico_id,o.pontuacao as pontuacao_final,o.pontuacao as b1,
      o.barras,o.impeto_adicional_codigo,
      coalesce(to_jsonb(o.habilidades_adicionais),'[]'::jsonb) as habilidades_adicionais,
      o.builds_comparadas::text as builds_comparadas,
      o.builds_possiveis::text as builds_possiveis,
      case when l.otimizador_iniciado_em is not null and l.otimizador_finalizado_em is not null
        then extract(epoch from l.otimizador_finalizado_em - l.otimizador_iniciado_em) end as duracao_segundos,
      case when l.build_bonificador_id is not null then 'concluido'
           when l.estado_otimizador = 'concluido' then 'pendente' else 'aguardando_otimizador' end as bonificador
    from clube_novo.otimizador_lote_producao_linha_v3 q
    join clube_novo.build_linha_card l on l.id = q.linha_id
    left join clube_novo.build_otimizador o on o.id = l.build_otimizador_id
    where q.lote_id = p_lote_id
      and (
        (p_grupo = 'abertas' and l.estado_otimizador in ('processando','pendente'))
        or
        (p_grupo = 'finais' and l.estado_otimizador in ('concluido','bloqueado','interrompido'))
      )
    order by
      case when p_grupo = 'abertas' and l.estado_otimizador = 'processando' then 0 else 1 end,
      q.ordem_fila
    offset p_offset limit p_limite
  ) x;

  return jsonb_build_object(
    'contrato','otimizador_fila_producao_v6','lote_id',p_lote_id,
    'grupo',p_grupo,'total',coalesce(v_total, 0),
    'offset',p_offset,'limite',p_limite,'itens',v_itens
  );
end
$$;

revoke all on function public.otimizador_producao_status_v6(uuid)
  from public,anon,authenticated;
revoke all on function public.otimizador_producao_controle_lote_v1(uuid)
  from public,anon,authenticated;
revoke all on function public.otimizador_producao_fila_operacional_v1(uuid,integer,integer,text)
  from public,anon,authenticated;
grant execute on function public.otimizador_producao_status_v6(uuid) to service_role;
grant execute on function public.otimizador_producao_controle_lote_v1(uuid) to service_role;
grant execute on function public.otimizador_producao_fila_operacional_v1(uuid,integer,integer,text)
  to service_role;

notify pgrst, 'reload schema';

commit;
