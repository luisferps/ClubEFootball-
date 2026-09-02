-- Bonificador: lote operacional persistente V1.
--
-- Escopo: controle e rastreio da fila canônica. Não altera fórmula, pesos,
-- moldes, régua, Otimizador nem publicação. A seleção continua estritamente:
--   build_otimizador_id IS NOT NULL
--   estado_otimizador = 'concluido'
--   build_bonificador_id IS NULL
--
-- Aplicar de forma transacional. O lote inicial fica somente PREPARADO;
-- esta migração não inicia o motor e não grava nenhum bônus.

begin;

create table if not exists clube_novo.bonificador_lote_operacional_v1 (
  id uuid primary key default gen_random_uuid(),
  contrato_fila text not null default 'bonificador_contexto_fila_v5'
    check (contrato_fila = 'bonificador_contexto_fila_v5'),
  estado text not null default 'preparado'
    check (estado in ('preparado','rodando','pausando','pausado','encerrando','encerrado','erro')),
  publicacao_liberada boolean not null default false check (publicacao_liberada = false),
  criado_em timestamptz not null default now(),
  iniciado_em timestamptz,
  pausado_em timestamptz,
  encerrado_em timestamptz,
  atualizado_em timestamptz not null default now(),
  observacao text
);

create unique index if not exists bonificador_lote_operacional_v1_um_aberto
  on clube_novo.bonificador_lote_operacional_v1 ((true))
  where estado in ('preparado','rodando','pausando','pausado','encerrando');

create table if not exists clube_novo.bonificador_lote_item_v1 (
  lote_id uuid not null references clube_novo.bonificador_lote_operacional_v1(id)
    on update restrict on delete restrict,
  build_linha_card_id bigint not null references clube_novo.build_linha_card(id)
    on update restrict on delete restrict,
  estado_item text not null default 'pendente'
    check (estado_item in ('pendente','processando','concluida','sem_bonus','falha','interrompida')),
  tentativas integer not null default 0 check (tentativas >= 0),
  iniciado_em timestamptz,
  finalizado_em timestamptz,
  build_bonificador_id bigint references clube_novo.build_bonificador(id)
    on update restrict on delete restrict,
  bonus_total numeric,
  motivo text,
  atualizado_em timestamptz not null default now(),
  primary key (lote_id, build_linha_card_id),
  check (
    (estado_item = 'sem_bonus' and bonus_total = 0)
    or (estado_item = 'concluida' and bonus_total is not null and bonus_total <> 0)
    or (estado_item not in ('sem_bonus','concluida'))
  )
);

create index if not exists bonificador_lote_item_v1_fila_idx
  on clube_novo.bonificador_lote_item_v1 (lote_id, estado_item, build_linha_card_id);

alter table clube_novo.bonificador_lote_operacional_v1 enable row level security;
alter table clube_novo.bonificador_lote_item_v1 enable row level security;
revoke all on table clube_novo.bonificador_lote_operacional_v1, clube_novo.bonificador_lote_item_v1 from public, anon, authenticated;

-- Sincroniza o snapshot com a descoberta direta. É uma função interna:
-- nenhuma UI a chama e ela não usa tabela/estado legado.
create or replace function clube_novo.bonificador_lote_sincronizar_itens_v1(p_lote_id uuid)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into clube_novo.bonificador_lote_item_v1 (lote_id, build_linha_card_id)
  select p_lote_id, l.id
  from clube_novo.build_linha_card l
  where l.build_otimizador_id is not null
    and l.estado_otimizador = 'concluido'
    and l.build_bonificador_id is null
  on conflict (lote_id, build_linha_card_id) do nothing;

  -- Se o writer confirmou antes de uma queda local, o readback do banco vence.
  update clube_novo.bonificador_lote_item_v1 i
     set estado_item = case when b.b_total = 0 then 'sem_bonus' else 'concluida' end,
         build_bonificador_id = b.id,
         bonus_total = b.b_total,
         finalizado_em = coalesce(i.finalizado_em, now()),
         motivo = null,
         atualizado_em = now()
    from clube_novo.build_linha_card l
    join clube_novo.build_bonificador b on b.id = l.build_bonificador_id
   where i.lote_id = p_lote_id
     and i.build_linha_card_id = l.id
     and i.estado_item in ('pendente','processando');

  -- Linha que deixou de ser elegível sem resultado não é apagada nem reexecutada.
  update clube_novo.bonificador_lote_item_v1 i
     set estado_item = 'interrompida',
         finalizado_em = coalesce(i.finalizado_em, now()),
         motivo = coalesce(i.motivo, 'A linha deixou de atender ao contrato direto antes do cálculo.'),
         atualizado_em = now()
    from clube_novo.build_linha_card l
   where i.lote_id = p_lote_id
     and i.build_linha_card_id = l.id
     and i.estado_item = 'pendente'
     and l.build_bonificador_id is null
     and not (l.build_otimizador_id is not null and l.estado_otimizador = 'concluido');
end;
$$;

-- Um lote preparado já identificado para a tela. Não contém itens até o operador
-- escolher Iniciar/Retomar, portanto não congela nem processa as candidatas.
insert into clube_novo.bonificador_lote_operacional_v1 (observacao)
select 'Preparado pela migração do batch V1; sem processamento automático.'
where not exists (
  select 1 from clube_novo.bonificador_lote_operacional_v1
  where estado in ('preparado','rodando','pausando','pausado','encerrando')
);

create or replace function public.bonificador_lote_status_v1()
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
  with lote as (
    select l.*
    from clube_novo.bonificador_lote_operacional_v1 l
    order by (l.estado in ('preparado','rodando','pausando','pausado','encerrando')) desc,
             l.criado_em desc
    limit 1
  ), elegiveis as (
    select count(*)::integer as total
    from clube_novo.build_linha_card l
    where l.build_otimizador_id is not null
      and l.estado_otimizador = 'concluido'
      and l.build_bonificador_id is null
  ), contagem as (
    select i.lote_id,
      count(*) filter (where i.estado_item = 'pendente')::integer as pendentes,
      count(*) filter (where i.estado_item = 'processando')::integer as processando,
      count(*) filter (where i.estado_item = 'concluida')::integer as concluidas,
      count(*) filter (where i.estado_item = 'sem_bonus')::integer as sem_bonus,
      count(*) filter (where i.estado_item = 'falha')::integer as falhas,
      count(*) filter (where i.estado_item = 'interrompida')::integer as interrompidas,
      count(*)::integer as itens_snapshot
    from clube_novo.bonificador_lote_item_v1 i
    group by i.lote_id
  ), atual as (
    select jsonb_build_object(
      'linha_id', i.build_linha_card_id, 'card_id', bl.card_id,
      'carta_nome', c.nome, 'funcao_nome', f.rotulo, 'posicao_nome', p.nome_pt
    ) as valor
    from lote l
    join clube_novo.bonificador_lote_item_v1 i on i.lote_id = l.id and i.estado_item = 'processando'
    join clube_novo.build_linha_card bl on bl.id = i.build_linha_card_id
    join clube_novo.carta_jogo c on c.card_id = bl.card_id
    join clube_novo.funcao_sistema f on f.id = bl.funcao_id
    join clube_novo.posicao_jogo p on p.id = bl.posicao_id
    order by i.iniciado_em asc, i.build_linha_card_id asc
    limit 1
  )
  select coalesce(jsonb_build_object(
    'existe', true,
    'lote_id', l.id,
    'contrato_fila', l.contrato_fila,
    'estado', l.estado,
    'publicacao_liberada', l.publicacao_liberada,
    'criado_em', l.criado_em,
    'iniciado_em', l.iniciado_em,
    'atualizado_em', l.atualizado_em,
    'elegiveis', e.total,
    'pendentes', case when l.estado = 'preparado' then e.total else coalesce(c.pendentes, 0) end,
    'em_processamento', coalesce(c.processando, 0),
    'concluidas', coalesce(c.concluidas, 0),
    'sem_bonus', coalesce(c.sem_bonus, 0),
    'falhas', coalesce(c.falhas, 0),
    'interrompidas', coalesce(c.interrompidas, 0),
    'itens_snapshot', coalesce(c.itens_snapshot, 0),
    'linha_atual', coalesce(a.valor, 'null'::jsonb),
    'pode_iniciar', l.estado in ('preparado','pausado'),
    'pode_pausar', l.estado = 'rodando',
    'pode_parar', l.estado in ('preparado','rodando','pausando','pausado','encerrando')
  ), jsonb_build_object(
    'existe', false, 'estado', 'sem_lote', 'publicacao_liberada', false,
    'elegiveis', e.total, 'pendentes', e.total, 'em_processamento', 0,
    'concluidas', 0, 'sem_bonus', 0, 'falhas', 0, 'interrompidas', 0,
    'itens_snapshot', 0, 'linha_atual', null,
    'pode_iniciar', false, 'pode_pausar', false, 'pode_parar', false
  ))
  from elegiveis e
  left join lote l on true
  left join contagem c on c.lote_id = l.id
  left join atual a on true;
$$;

create or replace function public.bonificador_lote_listar_v1(
  p_limit integer default 100, p_offset integer default 0
)
returns table(
  build_linha_card_id bigint, card_id text, carta_nome text, carta_tipo text,
  carta_box text, carta_overall integer, funcao_id bigint, funcao_codigo text,
  funcao_nome text, posicao_id integer, posicao_codigo text, posicao_nome text,
  carta_versao text, carta_fingerprint text, contrato_versao text,
  contrato_fingerprint text, formula_fingerprint text, estado text, motivo text,
  b_corpo numeric, b_pe_ruim numeric, b_estilo numeric, b_ia numeric, b_total numeric
)
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_lote clube_novo.bonificador_lote_operacional_v1%rowtype;
  v_limit integer := least(greatest(coalesce(p_limit, 100), 1), 500);
  v_offset integer := greatest(coalesce(p_offset, 0), 0);
begin
  select l.* into v_lote
  from clube_novo.bonificador_lote_operacional_v1 l
  order by (l.estado in ('preparado','rodando','pausando','pausado','encerrando')) desc,
           l.criado_em desc
  limit 1;
  if not found then return; end if;

  if v_lote.estado = 'preparado' then
    return query
    select q.build_linha_card_id, q.card_id, q.carta_nome, q.carta_tipo, q.carta_box,
           q.carta_overall, q.funcao_id, q.funcao_codigo, q.funcao_nome, q.posicao_id,
           q.posicao_codigo, q.posicao_nome, q.carta_versao, q.carta_fingerprint,
           q.contrato_versao, q.contrato_fingerprint, q.formula_fingerprint,
           'pendente'::text, null::text, null::numeric, null::numeric, null::numeric,
           null::numeric, null::numeric
    from public.bonificador_contexto_fila_v5(v_limit, v_offset) q;
    return;
  end if;

  return query
  select i.build_linha_card_id, bl.card_id, c.nome, c.tipo, c.box, c.overall,
         bl.funcao_id, coalesce(f.sigla,'')::text, f.rotulo, bl.posicao_id,
         coalesce(p.codigo_pt,'')::text, p.nome_pt, bl.carta_versao, bl.carta_fingerprint,
         'bonificador-regua-v2'::text,
         'regua_lida_pelo_motor_antes_do_calculo'::text,
         'ad8427acf268cf695bf69eca87704be95d8e1f13213d3ddec3d21955f705ce09'::text,
         i.estado_item, i.motivo, b.b_corpo, b.b_pe_ruim, b.b_estilo, b.b_ia, b.b_total
  from clube_novo.bonificador_lote_item_v1 i
  join clube_novo.build_linha_card bl on bl.id = i.build_linha_card_id
  join clube_novo.carta_jogo c on c.card_id = bl.card_id
  join clube_novo.funcao_sistema f on f.id = bl.funcao_id
  join clube_novo.posicao_jogo p on p.id = bl.posicao_id
  left join clube_novo.build_bonificador b on b.id = coalesce(i.build_bonificador_id, bl.build_bonificador_id)
  where i.lote_id = v_lote.id
  order by i.build_linha_card_id
  limit v_limit offset v_offset;
end;
$$;

create or replace function public.bonificador_lote_proxima_linha_v1(p_lote_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_linha bigint;
begin
  if not exists (
    select 1 from clube_novo.bonificador_lote_operacional_v1
    where id = p_lote_id and estado = 'rodando'
  ) then
    return null;
  end if;

  perform clube_novo.bonificador_lote_sincronizar_itens_v1(p_lote_id);

  select i.build_linha_card_id into v_linha
  from clube_novo.bonificador_lote_item_v1 i
  join clube_novo.build_linha_card l on l.id = i.build_linha_card_id
  where i.lote_id = p_lote_id
    and i.estado_item = 'pendente'
    and l.build_otimizador_id is not null
    and l.estado_otimizador = 'concluido'
    and l.build_bonificador_id is null
  order by i.build_linha_card_id
  for update of i skip locked
  limit 1;
  if v_linha is null then return null; end if;

  update clube_novo.bonificador_lote_item_v1
     set estado_item='processando', tentativas=tentativas+1, iniciado_em=now(),
         atualizado_em=now(), motivo=null
   where lote_id=p_lote_id and build_linha_card_id=v_linha;

  return (
    select jsonb_build_object(
      'build_linha_card_id', l.id, 'card_id', l.card_id,
      'funcao_id', l.funcao_id, 'funcao_codigo', coalesce(f.sigla,''),
      'posicao_id', l.posicao_id, 'carta_versao', l.carta_versao,
      'carta_fingerprint', l.carta_fingerprint,
      'contrato_versao', 'bonificador-regua-v2',
      'contrato_fingerprint', 'regua_lida_pelo_motor_antes_do_calculo',
      'formula_fingerprint', 'ad8427acf268cf695bf69eca87704be95d8e1f13213d3ddec3d21955f705ce09'
    )
    from clube_novo.build_linha_card l
    join clube_novo.funcao_sistema f on f.id=l.funcao_id
    where l.id=v_linha
  );
end;
$$;

create or replace function public.bonificador_lote_registrar_v1(
  p_lote_id uuid, p_linha_id bigint, p_estado text, p_bonus_total numeric default null,
  p_motivo text default null
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_item clube_novo.bonificador_lote_item_v1%rowtype;
  v_resultado clube_novo.build_bonificador%rowtype;
begin
  select * into v_item from clube_novo.bonificador_lote_item_v1
  where lote_id=p_lote_id and build_linha_card_id=p_linha_id for update;
  if not found then raise exception 'item de lote inexistente'; end if;
  if v_item.estado_item in ('concluida','sem_bonus','falha','interrompida') then
    return jsonb_build_object('ok',true,'idempotente',true,'estado',v_item.estado_item);
  end if;
  if p_estado not in ('concluida','sem_bonus','falha') then
    raise exception 'estado final inválido';
  end if;
  if p_estado = 'falha' then
    update clube_novo.bonificador_lote_item_v1
       set estado_item='falha', motivo=left(coalesce(p_motivo,'Falha sem motivo informado.'),1000),
           finalizado_em=now(), atualizado_em=now()
     where lote_id=p_lote_id and build_linha_card_id=p_linha_id;
    return jsonb_build_object('ok',true,'idempotente',false,'estado','falha');
  end if;
  select b.* into v_resultado
  from clube_novo.build_linha_card l
  join clube_novo.build_bonificador b on b.id=l.build_bonificador_id
  where l.id=p_linha_id;
  if not found then raise exception 'writer ainda não confirmou a linha %', p_linha_id; end if;
  if p_estado='sem_bonus' and v_resultado.b_total <> 0 then raise exception 'resultado não é sem bônus'; end if;
  if p_estado='concluida' and v_resultado.b_total = 0 then raise exception 'resultado zero deve ser sem_bonus'; end if;
  if p_bonus_total is not null and v_resultado.b_total <> p_bonus_total then raise exception 'total do writer diverge do registro de lote'; end if;
  update clube_novo.bonificador_lote_item_v1
     set estado_item=p_estado, build_bonificador_id=v_resultado.id,
         bonus_total=v_resultado.b_total, motivo=null, finalizado_em=now(), atualizado_em=now()
   where lote_id=p_lote_id and build_linha_card_id=p_linha_id;
  return jsonb_build_object('ok',true,'idempotente',false,'estado',p_estado,
                            'build_bonificador_id',v_resultado.id,'b_total',v_resultado.b_total);
end;
$$;

create or replace function public.bonificador_lote_assentar_parada_v1(p_lote_id uuid, p_modo text)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare v_estado text;
begin
  select estado into v_estado from clube_novo.bonificador_lote_operacional_v1
  where id=p_lote_id for update;
  if not found then raise exception 'lote inexistente'; end if;
  perform clube_novo.bonificador_lote_sincronizar_itens_v1(p_lote_id);
  if p_modo='pausar' then
    update clube_novo.bonificador_lote_operacional_v1
       set estado='pausado', pausado_em=now(), atualizado_em=now(),
           observacao='Pausado após a linha atômica em processamento.'
     where id=p_lote_id and estado='pausando';
  elsif p_modo='parar' then
    update clube_novo.bonificador_lote_item_v1
       set estado_item='interrompida', finalizado_em=now(), atualizado_em=now(),
           motivo=coalesce(motivo,'Interrompida pelo operador; nenhum resultado foi apagado.')
     where lote_id=p_lote_id and estado_item in ('pendente','processando');
    update clube_novo.bonificador_lote_operacional_v1
       set estado='encerrado', encerrado_em=now(), atualizado_em=now(),
           observacao='Encerrado pelo operador após a linha atômica.'
     where id=p_lote_id and estado in ('preparado','rodando','pausando','pausado','encerrando');
  else
    raise exception 'modo de assentamento inválido';
  end if;
  return public.bonificador_lote_status_v1();
end;
$$;

create or replace function public.bonificador_lote_controlar_v1(p_acao text)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare v_lote clube_novo.bonificador_lote_operacional_v1%rowtype;
begin
  select * into v_lote from clube_novo.bonificador_lote_operacional_v1
  where estado in ('preparado','rodando','pausando','pausado','encerrando')
  order by criado_em desc limit 1 for update;
  if not found then
    insert into clube_novo.bonificador_lote_operacional_v1(observacao)
    values ('Novo lote preparado pelo controle local.') returning * into v_lote;
  end if;
  if p_acao='iniciar' then
    if v_lote.estado not in ('preparado','pausado') then raise exception 'lote não pode iniciar no estado %',v_lote.estado; end if;
    update clube_novo.bonificador_lote_operacional_v1
       set estado='rodando', iniciado_em=coalesce(iniciado_em,now()), atualizado_em=now(),
           observacao='Rodando pelo aplicativo local; publicação permanece desligada.'
     where id=v_lote.id;
    perform clube_novo.bonificador_lote_sincronizar_itens_v1(v_lote.id);
    update clube_novo.bonificador_lote_item_v1 i
       set estado_item='pendente', iniciado_em=null, atualizado_em=now(),
           motivo='Retomada após pausa; a linha ainda não tinha resultado confirmado.'
     where i.lote_id=v_lote.id and i.estado_item='processando'
       and not exists (select 1 from clube_novo.build_linha_card l where l.id=i.build_linha_card_id and l.build_bonificador_id is not null);
  elsif p_acao='pausar' then
    if v_lote.estado <> 'rodando' then raise exception 'lote não está rodando'; end if;
    update clube_novo.bonificador_lote_operacional_v1
       set estado='pausando', atualizado_em=now(), observacao='Pausa solicitada; aguardando a linha atômica.'
     where id=v_lote.id;
  elsif p_acao='parar' then
    if v_lote.estado in ('preparado','pausado') then
      perform public.bonificador_lote_assentar_parada_v1(v_lote.id,'parar');
    elsif v_lote.estado in ('rodando','pausando') then
      update clube_novo.bonificador_lote_operacional_v1
         set estado='encerrando', atualizado_em=now(), observacao='Parada solicitada; aguardando a linha atômica.'
       where id=v_lote.id;
    else
      raise exception 'lote não pode parar no estado %',v_lote.estado;
    end if;
  else
    raise exception 'ação de lote inválida';
  end if;
  return public.bonificador_lote_status_v1();
end;
$$;

revoke all on function clube_novo.bonificador_lote_sincronizar_itens_v1(uuid) from public;
revoke all on function public.bonificador_lote_status_v1() from public, anon, authenticated;
revoke all on function public.bonificador_lote_listar_v1(integer,integer) from public, anon, authenticated;
revoke all on function public.bonificador_lote_proxima_linha_v1(uuid) from public, anon, authenticated;
revoke all on function public.bonificador_lote_registrar_v1(uuid,bigint,text,numeric,text) from public, anon, authenticated;
revoke all on function public.bonificador_lote_assentar_parada_v1(uuid,text) from public, anon, authenticated;
revoke all on function public.bonificador_lote_controlar_v1(text) from public, anon, authenticated;
grant execute on function public.bonificador_lote_status_v1() to postgres, service_role, bonificador_runtime;
grant execute on function public.bonificador_lote_listar_v1(integer,integer) to postgres, service_role, bonificador_runtime;
grant execute on function public.bonificador_lote_proxima_linha_v1(uuid) to postgres, service_role, bonificador_runtime;
grant execute on function public.bonificador_lote_registrar_v1(uuid,bigint,text,numeric,text) to postgres, service_role, bonificador_runtime;
grant execute on function public.bonificador_lote_assentar_parada_v1(uuid,text) to postgres, service_role, bonificador_runtime;
grant execute on function public.bonificador_lote_controlar_v1(text) to postgres, service_role, bonificador_runtime;

commit;
