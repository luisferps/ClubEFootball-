-- V19: contrato único de entrada e leitura da fila produtiva.
--
-- Uma view privada de clube_novo passa a ser a única fotografia de cada linha
-- para o worker e para o painel. O browser continua falando só com o servidor
-- loopback; somente RPCs allowlist recebem os dados. Não toca fórmula, pesos,
-- moldes, publicação, tabela legado ou resultados já gravados.
--
-- Também corrige duas falhas físicas comprovadas:
-- 1) o fecho do preparo V5 procurava funcao_id/posicao_id na tabela de
--    linhagem, que deliberadamente só guarda linha_id;
-- 2) a cache de status tentava inserir um delta negativo antes de resolver o
--    conflito da chave única, violando o check de pendentes.

begin;

do $$
begin
  if to_regprocedure('public.otimizador_producao_preparar_fatia_v5(uuid,integer)') is null
     or to_regprocedure('public.otimizador_producao_reservar_linha_v6(uuid,uuid)') is null
     or to_regprocedure('public.otimizador_portal_local_v5(text,jsonb)') is null
     or to_regclass('clube_novo.build_linha_card') is null
     or to_regclass('clube_novo.otimizador_lote_producao_linha_v3') is null
     or to_regclass('clube_novo.otimizador_lote_producao_carta_v3') is null
     or to_regclass('clube_novo.otimizador_lote_producao_status_v1') is null then
    raise exception 'V19 recusada: contratos/tabelas V5/V6/V18 exigidos não estão presentes';
  end if;
  if not exists (select 1 from pg_roles where rolname = 'bonificador_runtime') then
    raise exception 'V19 recusada: login local bonificador_runtime ausente';
  end if;
end
$$;

-- A recomposição é usada apenas quando a cache ainda não tem uma linha, ou
-- quando um delta demonstraria que ela já estava inconsistente. No caminho
-- normal, cada transição continua sendo um delta O(1).
create or replace function clube_novo.recalcular_status_lote_otimizador_v2(
  p_lote_id uuid
)
returns void
language plpgsql
security definer
set search_path to ''
as $$
declare
  v_pendentes integer := 0;
  v_processando integer := 0;
  v_concluidas integer := 0;
  v_bloqueadas integer := 0;
  v_interrompidas integer := 0;
  v_bonificador_pendentes integer := 0;
begin
  if p_lote_id is null then
    raise exception 'recomposição de status recusada: lote ausente';
  end if;

  select
    count(*) filter (where l.estado_otimizador = 'pendente')::integer,
    count(*) filter (where l.estado_otimizador = 'processando')::integer,
    count(*) filter (where l.estado_otimizador = 'concluido')::integer,
    count(*) filter (where l.estado_otimizador = 'bloqueado')::integer,
    count(*) filter (where l.estado_otimizador = 'interrompido')::integer,
    count(*) filter (
      where l.estado_otimizador = 'concluido'
        and l.build_bonificador_id is null
    )::integer
  into v_pendentes, v_processando, v_concluidas, v_bloqueadas,
       v_interrompidas, v_bonificador_pendentes
  from clube_novo.build_linha_card l
  where l.lote_producao_id = p_lote_id;

  insert into clube_novo.otimizador_lote_producao_status_v1 as s(
    lote_id, pendentes, processando, concluidas, bloqueadas, interrompidas,
    bonificador_pendentes, atualizado_em
  ) values (
    p_lote_id, v_pendentes, v_processando, v_concluidas, v_bloqueadas,
    v_interrompidas, v_bonificador_pendentes, clock_timestamp()
  )
  on conflict (lote_id) do update
  set pendentes = excluded.pendentes,
      processando = excluded.processando,
      concluidas = excluded.concluidas,
      bloqueadas = excluded.bloqueadas,
      interrompidas = excluded.interrompidas,
      bonificador_pendentes = excluded.bonificador_pendentes,
      atualizado_em = excluded.atualizado_em;
end
$$;

create or replace function clube_novo.aplicar_delta_status_lote_otimizador_v2(
  p_lote_id uuid,
  p_pendentes integer,
  p_processando integer,
  p_concluidas integer,
  p_bloqueadas integer,
  p_interrompidas integer,
  p_bonificador_pendentes integer
)
returns void
language plpgsql
security definer
set search_path to ''
as $$
begin
  if p_lote_id is null then
    return;
  end if;

  -- Preparador e worker podem tocar o mesmo lote. O lock por lote garante que
  -- a decisão delta/recomposição usa uma única base de contagem por vez.
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(p_lote_id::text, 31959)
  );

  update clube_novo.otimizador_lote_producao_status_v1 as s
     set pendentes = s.pendentes + p_pendentes,
         processando = s.processando + p_processando,
         concluidas = s.concluidas + p_concluidas,
         bloqueadas = s.bloqueadas + p_bloqueadas,
         interrompidas = s.interrompidas + p_interrompidas,
         bonificador_pendentes = s.bonificador_pendentes + p_bonificador_pendentes,
         atualizado_em = clock_timestamp()
   where s.lote_id = p_lote_id
     and s.pendentes + p_pendentes >= 0
     and s.processando + p_processando >= 0
     and s.concluidas + p_concluidas >= 0
     and s.bloqueadas + p_bloqueadas >= 0
     and s.interrompidas + p_interrompidas >= 0
     and s.bonificador_pendentes + p_bonificador_pendentes >= 0;

  if found then
    return;
  end if;

  -- Sem linha de cache, ou cache impossível: reconta o lote após a transação
  -- da própria linha. Nunca insere delta negativo em uma tabela checada.
  perform clube_novo.recalcular_status_lote_otimizador_v2(p_lote_id);
end
$$;

create or replace function clube_novo.atualizar_status_lote_otimizador_v2()
returns trigger
language plpgsql
security definer
set search_path to ''
as $$
declare
  v_delta record;
begin
  if tg_op = 'INSERT' then
    for v_delta in
      select
        n.lote_producao_id as lote_id,
        count(*) filter (where n.estado_otimizador = 'pendente')::integer as pendentes,
        count(*) filter (where n.estado_otimizador = 'processando')::integer as processando,
        count(*) filter (where n.estado_otimizador = 'concluido')::integer as concluidas,
        count(*) filter (where n.estado_otimizador = 'bloqueado')::integer as bloqueadas,
        count(*) filter (where n.estado_otimizador = 'interrompido')::integer as interrompidas,
        count(*) filter (
          where n.estado_otimizador = 'concluido'
            and n.build_bonificador_id is null
        )::integer as bonificador_pendentes
      from novas_linhas n
      where n.lote_producao_id is not null
      group by n.lote_producao_id
    loop
      perform clube_novo.aplicar_delta_status_lote_otimizador_v2(
        v_delta.lote_id, v_delta.pendentes, v_delta.processando,
        v_delta.concluidas, v_delta.bloqueadas, v_delta.interrompidas,
        v_delta.bonificador_pendentes
      );
    end loop;
  elsif tg_op = 'DELETE' then
    for v_delta in
      select
        a.lote_producao_id as lote_id,
        -count(*) filter (where a.estado_otimizador = 'pendente')::integer as pendentes,
        -count(*) filter (where a.estado_otimizador = 'processando')::integer as processando,
        -count(*) filter (where a.estado_otimizador = 'concluido')::integer as concluidas,
        -count(*) filter (where a.estado_otimizador = 'bloqueado')::integer as bloqueadas,
        -count(*) filter (where a.estado_otimizador = 'interrompido')::integer as interrompidas,
        -count(*) filter (
          where a.estado_otimizador = 'concluido'
            and a.build_bonificador_id is null
        )::integer as bonificador_pendentes
      from antigas_linhas a
      where a.lote_producao_id is not null
      group by a.lote_producao_id
    loop
      perform clube_novo.aplicar_delta_status_lote_otimizador_v2(
        v_delta.lote_id, v_delta.pendentes, v_delta.processando,
        v_delta.concluidas, v_delta.bloqueadas, v_delta.interrompidas,
        v_delta.bonificador_pendentes
      );
    end loop;
  else
    for v_delta in
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
      )
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
    loop
      perform clube_novo.aplicar_delta_status_lote_otimizador_v2(
        v_delta.lote_id, v_delta.pendentes, v_delta.processando,
        v_delta.concluidas, v_delta.bloqueadas, v_delta.interrompidas,
        v_delta.bonificador_pendentes
      );
    end loop;
  end if;
  return null;
end
$$;

drop trigger if exists build_linha_status_otimizador_v11_insert on clube_novo.build_linha_card;
drop trigger if exists build_linha_status_otimizador_v11_update on clube_novo.build_linha_card;
drop trigger if exists build_linha_status_otimizador_v11_delete on clube_novo.build_linha_card;
drop trigger if exists build_linha_status_otimizador_v19_insert on clube_novo.build_linha_card;
drop trigger if exists build_linha_status_otimizador_v19_update on clube_novo.build_linha_card;
drop trigger if exists build_linha_status_otimizador_v19_delete on clube_novo.build_linha_card;

create trigger build_linha_status_otimizador_v19_insert
after insert on clube_novo.build_linha_card
referencing new table as novas_linhas
for each statement execute function clube_novo.atualizar_status_lote_otimizador_v2();

create trigger build_linha_status_otimizador_v19_update
after update on clube_novo.build_linha_card
referencing old table as antigas_linhas new table as novas_linhas
for each statement execute function clube_novo.atualizar_status_lote_otimizador_v2();

create trigger build_linha_status_otimizador_v19_delete
after delete on clube_novo.build_linha_card
referencing old table as antigas_linhas
for each statement execute function clube_novo.atualizar_status_lote_otimizador_v2();

-- Repara somente a cache derivada de lotes integrais ainda relevantes; não
-- mexe em cartas, linhas, resultados, fórmula ou publicação.
do $$
declare v_lote_id uuid;
begin
  for v_lote_id in
    select id
    from clube_novo.otimizador_lote_producao_v3
    where tipo_lote = 'integral'
      and estado not in ('encerrado', 'concluido')
  loop
    perform clube_novo.recalcular_status_lote_otimizador_v2(v_lote_id);
  end loop;
end
$$;

-- A única troca no preparo V5 é de endereço: funcao_id e posicao_id pertencem
-- à build_linha_card, não à tabela de linhagem. A substituição é assertiva,
-- feita sobre o corpo exatamente instalado, e falha se a V5 não for a esperada.
do $v5$
declare
  v_def text;
  v_antigo constant text := $trecho$
        string_agg(card_id||':'||funcao_id::text||':'||posicao_id::text||':'||ordem_fila::text,
                   ',' order by ordem_fila),
        'UTF8'),'sha256'),'hex')
      into v_fingerprint
      from clube_novo.otimizador_lote_producao_linha_v3
      where lote_id=p_lote_id;$trecho$;
  v_novo constant text := $trecho$
        string_agg(q.card_id||':'||l.funcao_id::text||':'||l.posicao_id::text||':'||q.ordem_fila::text,
                   ',' order by q.ordem_fila),
        'UTF8'),'sha256'),'hex')
      into v_fingerprint
      from clube_novo.otimizador_lote_producao_linha_v3 q
      join clube_novo.build_linha_card l on l.id = q.linha_id
      where q.lote_id=p_lote_id;$trecho$;
begin
  select pg_get_functiondef(
    'public.otimizador_producao_preparar_fatia_v5(uuid,integer)'::regprocedure
  ) into v_def;
  if position(v_antigo in v_def) = 0
     or position(v_antigo in replace(v_def, v_antigo, '')) <> 0
     or position(v_novo in v_def) <> 0 then
    raise exception 'V19 recusada: corpo do preparo V5 não corresponde ao hunk físico esperado';
  end if;
  execute replace(v_def, v_antigo, v_novo);
end
$v5$;

-- Fotografia única, privada e baseada em IDs canônicos. Os rótulos são apenas
-- apresentação; worker e reservas continuam usando card_id/funcao_id/posicao_id.
create or replace view clube_novo.otimizador_entrada_linha_v1
with (security_invoker = true)
as
select
  lote.id as lote_id,
  lote.contrato as lote_contrato,
  lote.tipo_lote,
  lote.estado as estado_lote,
  lote.formula_fingerprint,
  lote.contrato_fingerprint,
  lote.motor_versao,
  lote.regua_snapshot as regua,
  lote.fingerprint as lote_fingerprint,
  lote.pode_publicar,
  q.linha_id,
  q.ordem_fila,
  q.reserva_token,
  q.worker_id,
  q.reservada_em,
  q.finalizada_em as fila_finalizada_em,
  q.tentativas,
  q.entrada_fingerprint as carta_entrada_fingerprint,
  l.card_id,
  l.funcao_id,
  l.posicao_id,
  l.estado_otimizador as estado,
  l.erro_otimizador as motivo,
  l.otimizador_iniciado_em as iniciada_em,
  l.otimizador_finalizado_em as finalizada_em,
  l.carta_versao,
  l.carta_fingerprint,
  l.impeto_condicional_codigo,
  l.impeto_condicional_nivel,
  l.build_otimizador_id,
  l.build_bonificador_id,
  snapshot.entrada_otimizador as carta,
  snapshot.entrada_fingerprint as snapshot_entrada_fingerprint,
  snapshot.overall_snapshot,
  carta.nome as carta_nome,
  funcao.rotulo as funcao_rotulo,
  posicao.nome_pt as posicao_rotulo,
  resultado.tecnico_id,
  resultado.pontuacao as pontuacao_final,
  resultado.pontuacao as b1,
  resultado.barras,
  resultado.impeto_adicional_codigo,
  coalesce(to_jsonb(resultado.habilidades_adicionais), '[]'::jsonb) as habilidades_adicionais,
  resultado.builds_comparadas::text as builds_comparadas,
  resultado.builds_possiveis::text as builds_possiveis,
  case
    when l.otimizador_iniciado_em is not null and l.otimizador_finalizado_em is not null
      then extract(epoch from l.otimizador_finalizado_em - l.otimizador_iniciado_em)
  end as duracao_segundos,
  case
    when l.build_bonificador_id is not null then 'concluido'
    when l.estado_otimizador = 'concluido' then 'pendente'
    else 'aguardando_otimizador'
  end as bonificador
from clube_novo.otimizador_lote_producao_v3 lote
join clube_novo.otimizador_lote_producao_linha_v3 q
  on q.lote_id = lote.id
join clube_novo.build_linha_card l
  on l.id = q.linha_id and l.lote_producao_id = lote.id
join clube_novo.otimizador_lote_producao_carta_v3 snapshot
  on snapshot.lote_id = lote.id and snapshot.card_id = q.card_id
left join clube_novo.carta_jogo carta
  on carta.card_id = l.card_id
left join clube_novo.funcao_sistema funcao
  on funcao.id = l.funcao_id
left join clube_novo.posicao_jogo posicao
  on posicao.id = l.posicao_id
left join clube_novo.build_otimizador resultado
  on resultado.id = l.build_otimizador_id;

revoke all on clube_novo.otimizador_entrada_linha_v1 from public, anon, authenticated;

create or replace function public.otimizador_producao_reservar_entrada_v7(
  p_lote_id uuid,
  p_worker_id uuid,
  p_formula_fingerprint text,
  p_motor_versao text
)
returns jsonb
language plpgsql
security definer
set search_path to ''
as $$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_q clube_novo.otimizador_lote_producao_linha_v3%rowtype;
  v_entrada record;
  v_token uuid;
begin
  if p_worker_id is null
     or nullif(trim(coalesce(p_formula_fingerprint, '')), '') is null
     or nullif(trim(coalesce(p_motor_versao, '')), '') is null then
    raise exception 'reserva V7 recusada: worker, fórmula e versão são obrigatórios';
  end if;

  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id
  for update;

  if not found or v_lote.tipo_lote <> 'integral' then
    raise exception 'reserva V7 recusada: lote integral inexistente';
  end if;
  if v_lote.formula_fingerprint <> p_formula_fingerprint
     or v_lote.motor_versao <> p_motor_versao
     or v_lote.formula_fingerprint <> '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad'
     or v_lote.pode_publicar is distinct from false then
    raise exception 'reserva V7 recusada: selo da fórmula/versão/publicação não confere';
  end if;
  if v_lote.estado <> 'rodando' then
    return jsonb_build_object(
      'contrato', 'otimizador_entrada_linha_v1',
      'reservada', false,
      'estado_lote', v_lote.estado
    );
  end if;

  select q.* into v_q
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id = q.linha_id
  where q.lote_id = p_lote_id
    and l.estado_otimizador = 'pendente'
  order by q.ordem_fila
  for update of q, l skip locked
  limit 1;

  if not found then
    if v_lote.preparo_concluido < v_lote.preparo_total then
      return jsonb_build_object(
        'contrato', 'otimizador_entrada_linha_v1',
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
        'contrato', 'otimizador_entrada_linha_v1',
        'reservada', false,
        'estado_lote', 'concluido'
      );
    end if;
    return jsonb_build_object(
      'contrato', 'otimizador_entrada_linha_v1',
      'reservada', false,
      'estado_lote', 'rodando'
    );
  end if;

  select * into v_entrada
  from clube_novo.otimizador_entrada_linha_v1 e
  where e.lote_id = p_lote_id and e.linha_id = v_q.linha_id;

  if not found
     or v_entrada.card_id <> v_q.card_id
     or v_entrada.carta_entrada_fingerprint <> v_q.entrada_fingerprint
     or v_entrada.snapshot_entrada_fingerprint <> v_q.entrada_fingerprint
     or v_entrada.carta is null
     or v_entrada.impeto_condicional_codigo is not null
     or v_entrada.impeto_condicional_nivel is not null
     or not coalesce((v_entrada.regua -> 'gate' ->> 'pode_rodar')::boolean, false) then
    raise exception 'reserva V7 recusada: fotografia única da entrada não passou os gates';
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
    jsonb_build_object(
      'worker_id', p_worker_id,
      'ordem_fila', v_q.ordem_fila,
      'contrato_entrada_v7', true,
      'origem', 'clube_novo.otimizador_entrada_linha_v1'
    )
  );

  return jsonb_build_object(
    'contrato', 'otimizador_entrada_linha_v1',
    'reservada', true,
    'lote_id', v_entrada.lote_id,
    'linha_id', v_entrada.linha_id,
    'reserva_token', v_token,
    'ordem_fila', v_entrada.ordem_fila,
    'card_id', v_entrada.card_id,
    'funcao_id', v_entrada.funcao_id,
    'posicao_id', v_entrada.posicao_id,
    'impeto_condicional_codigo', null,
    'impeto_condicional_nivel', null,
    'carta', v_entrada.carta,
    'carta_entrada_fingerprint', v_entrada.carta_entrada_fingerprint,
    'formula_fingerprint', v_entrada.formula_fingerprint,
    'contrato_fingerprint', v_entrada.contrato_fingerprint,
    'motor_versao', v_entrada.motor_versao,
    'lote_fingerprint', v_entrada.lote_fingerprint,
    'carta_versao', v_entrada.carta_versao,
    'carta_fingerprint', v_entrada.carta_fingerprint,
    'regua', v_entrada.regua,
    'impetos_condicionais', 'desligados'
  );
end
$$;

create or replace function public.otimizador_producao_fila_operacional_v4(
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
     or p_grupo not in ('abertas', 'finais') then
    raise exception 'leitura operacional V4 recusada: parâmetros fora da faixa';
  end if;

  select count(*)::integer into v_total
  from clube_novo.otimizador_entrada_linha_v1 e
  where e.lote_id = p_lote_id
    and (
      (p_grupo = 'abertas' and e.estado in ('pendente', 'processando'))
      or
      (p_grupo = 'finais' and e.estado in ('concluido', 'bloqueado', 'interrompido', 'falhou'))
    );

  with pagina as materialized (
    select e.*
    from clube_novo.otimizador_entrada_linha_v1 e
    where e.lote_id = p_lote_id
      and (
        (p_grupo = 'abertas' and e.estado in ('pendente', 'processando'))
        or
        (p_grupo = 'finais' and e.estado in ('concluido', 'bloqueado', 'interrompido', 'falhou'))
      )
    order by e.ordem_fila
    offset p_offset limit p_limite
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'ordem_fila', p.ordem_fila,
    'linha_id', p.linha_id,
    'card_id', p.card_id,
    'carta_nome', p.carta_nome,
    'funcao_id', p.funcao_id,
    'funcao_rotulo', p.funcao_rotulo,
    'posicao_id', p.posicao_id,
    'posicao_rotulo', p.posicao_rotulo,
    'estado', p.estado,
    'motivo', p.motivo,
    'iniciada_em', p.iniciada_em,
    'finalizada_em', p.finalizada_em,
    'overall_snapshot', p.overall_snapshot,
    'tecnico_id', p.tecnico_id,
    'pontuacao_final', p.pontuacao_final,
    'b1', p.b1,
    'barras', p.barras,
    'impeto_adicional_codigo', p.impeto_adicional_codigo,
    'habilidades_adicionais', p.habilidades_adicionais,
    'builds_comparadas', p.builds_comparadas,
    'builds_possiveis', p.builds_possiveis,
    'duracao_segundos', p.duracao_segundos,
    'bonificador', p.bonificador
  ) order by p.ordem_fila), '[]'::jsonb)
  into v_itens
  from pagina p;

  return jsonb_build_object(
    'contrato', 'otimizador_fila_producao_v7',
    'fonte', 'clube_novo.otimizador_entrada_linha_v1',
    'lote_id', p_lote_id,
    'grupo', p_grupo,
    'total', coalesce(v_total, 0),
    'offset', p_offset,
    'limite', p_limite,
    'itens', v_itens
  );
end
$$;

-- A falha atual foi registrada antes de uma linha ser reservada. Esta é uma
-- recuperação propositalmente estreita; outras falhas continuam fechadas.
create or replace function public.otimizador_producao_recuperar_falha_pre_reserva_v2(
  p_lote_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path to ''
as $$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_processando integer := 0;
  v_falha constant text := 'contrato recusou a consulta (400); ponte privada local também indisponível (contrato privado local indisponível (CheckViolation))';
begin
  if p_lote_id is null then
    raise exception 'recuperação V19 recusada: lote ausente';
  end if;

  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id
  for update;

  if not found
     or v_lote.tipo_lote <> 'integral'
     or v_lote.estado <> 'falhou'
     or coalesce(v_lote.falha, '') <> v_falha
     or v_lote.formula_fingerprint <> '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad'
     or v_lote.pode_publicar is distinct from false
     or v_lote.linhas <= 0
     or v_lote.preparo_concluido > v_lote.preparo_total then
    raise exception 'recuperação V19 recusada: selo/estado não corresponde à falha pré-reserva comprovada';
  end if;

  select count(*)::integer into v_processando
  from clube_novo.build_linha_card
  where lote_producao_id = p_lote_id
    and estado_otimizador = 'processando';
  if v_processando <> 0 then
    raise exception 'recuperação V19 recusada: existe linha ativa';
  end if;

  update clube_novo.otimizador_lote_producao_v3
  set estado = 'rodando',
      falha = null,
      atualizado_em = clock_timestamp()
  where id = p_lote_id;

  insert into clube_novo.otimizador_evento_producao_v3(lote_id, evento, detalhe)
  values (
    p_lote_id,
    'lote_retomado',
    jsonb_build_object(
      'motivo', 'recuperacao_falha_pre_reserva_v19',
      'falha_anterior', v_falha,
      'linhas_processando', v_processando,
      'formula_alterada', false,
      'pode_publicar', false,
      'contrato_entrada', 'clube_novo.otimizador_entrada_linha_v1'
    )
  );

  return public.otimizador_producao_status_v6(p_lote_id);
end
$$;

revoke all on function public.otimizador_producao_reservar_entrada_v7(uuid, uuid, text, text)
  from public, anon, authenticated;
revoke all on function public.otimizador_producao_fila_operacional_v4(uuid, integer, integer, text)
  from public, anon, authenticated;
revoke all on function public.otimizador_producao_recuperar_falha_pre_reserva_v2(uuid)
  from public, anon, authenticated;
grant execute on function public.otimizador_producao_reservar_entrada_v7(uuid, uuid, text, text)
  to service_role;
grant execute on function public.otimizador_producao_fila_operacional_v4(uuid, integer, integer, text)
  to service_role;
grant execute on function public.otimizador_producao_recuperar_falha_pre_reserva_v2(uuid)
  to service_role;

-- A ponte privada continua ser uma contingência de transporte. Ela recebe a
-- mesma allowlist; não ganha SELECT em view/tabela e não recebe SQL livre.
create or replace function public.otimizador_portal_local_v6(
  p_operacao text,
  p_corpo jsonb default '{}'::jsonb
)
returns jsonb
language plpgsql
security definer
set search_path to ''
as $$
begin
  if p_operacao = 'otimizador_producao_reservar_entrada_v7' then
    return public.otimizador_producao_reservar_entrada_v7(
      (p_corpo ->> 'p_lote_id')::uuid,
      (p_corpo ->> 'p_worker_id')::uuid,
      p_corpo ->> 'p_formula_fingerprint',
      p_corpo ->> 'p_motor_versao'
    );
  end if;
  if p_operacao = 'otimizador_producao_fila_operacional_v4' then
    return public.otimizador_producao_fila_operacional_v4(
      (p_corpo ->> 'p_lote_id')::uuid,
      (p_corpo ->> 'p_offset')::integer,
      (p_corpo ->> 'p_limite')::integer,
      p_corpo ->> 'p_grupo'
    );
  end if;
  if p_operacao = 'otimizador_producao_recuperar_falha_pre_reserva_v2' then
    return public.otimizador_producao_recuperar_falha_pre_reserva_v2(
      (p_corpo ->> 'p_lote_id')::uuid
    );
  end if;
  return public.otimizador_portal_local_v5(p_operacao, p_corpo);
end
$$;

revoke all on function public.otimizador_portal_local_v6(text, jsonb)
  from public, anon, authenticated;
grant execute on function public.otimizador_portal_local_v6(text, jsonb)
  to bonificador_runtime;

comment on view clube_novo.otimizador_entrada_linha_v1 is
  'V19: única fotografia privada por linha para worker e painel; IDs canônicos para cálculo e rótulos só para apresentação.';
comment on function public.otimizador_producao_reservar_entrada_v7(uuid, uuid, text, text) is
  'V19: reserva atômica e entrada do worker pela view privada única; valida fórmula/motor antes de reservar.';
comment on function public.otimizador_producao_fila_operacional_v4(uuid, integer, integer, text) is
  'V19: página do painel derivada da mesma view privada da reserva; sem leitura de tabela pela UI.';
comment on function public.otimizador_producao_recuperar_falha_pre_reserva_v2(uuid) is
  'V19: reabre somente a falha V18/CheckViolation comprovada antes de qualquer reserva, sem publicar nem reexecutar linhas.';

notify pgrst, 'reload schema';

commit;
