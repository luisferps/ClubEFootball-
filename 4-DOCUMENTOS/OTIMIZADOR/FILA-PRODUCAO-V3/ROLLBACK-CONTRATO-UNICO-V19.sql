-- Rollback V19. Não apaga linhas, builds, resultados, eventos ou estados do
-- lote. Restaura somente contratos/leitura e a cache de status V11 anterior.

begin;

drop trigger if exists build_linha_status_otimizador_v19_insert on clube_novo.build_linha_card;
drop trigger if exists build_linha_status_otimizador_v19_update on clube_novo.build_linha_card;
drop trigger if exists build_linha_status_otimizador_v19_delete on clube_novo.build_linha_card;

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

drop trigger if exists build_linha_status_otimizador_v11_insert on clube_novo.build_linha_card;
drop trigger if exists build_linha_status_otimizador_v11_update on clube_novo.build_linha_card;
drop trigger if exists build_linha_status_otimizador_v11_delete on clube_novo.build_linha_card;

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

do $v5$
declare
  v_def text;
  v_antigo constant text := $trecho$
        string_agg(q.card_id||':'||l.funcao_id::text||':'||l.posicao_id::text||':'||q.ordem_fila::text,
                   ',' order by q.ordem_fila),
        'UTF8'),'sha256'),'hex')
      into v_fingerprint
      from clube_novo.otimizador_lote_producao_linha_v3 q
      join clube_novo.build_linha_card l on l.id = q.linha_id
      where q.lote_id=p_lote_id;$trecho$;
  v_novo constant text := $trecho$
        string_agg(card_id||':'||funcao_id::text||':'||posicao_id::text||':'||ordem_fila::text,
                   ',' order by ordem_fila),
        'UTF8'),'sha256'),'hex')
      into v_fingerprint
      from clube_novo.otimizador_lote_producao_linha_v3
      where lote_id=p_lote_id;$trecho$;
begin
  select pg_get_functiondef(
    'public.otimizador_producao_preparar_fatia_v5(uuid,integer)'::regprocedure
  ) into v_def;
  if position(v_antigo in v_def) = 0
     or position(v_antigo in replace(v_def, v_antigo, '')) <> 0
     or position(v_novo in v_def) <> 0 then
    raise exception 'rollback V19 recusado: corpo V5 não corresponde ao hunk V19';
  end if;
  execute replace(v_def, v_antigo, v_novo);
end
$v5$;

drop function if exists public.otimizador_portal_local_v6(text, jsonb);
drop function if exists public.otimizador_producao_recuperar_falha_pre_reserva_v2(uuid);
drop function if exists public.otimizador_producao_fila_operacional_v4(uuid, integer, integer, text);
drop function if exists public.otimizador_producao_reservar_entrada_v7(uuid, uuid, text, text);
drop view if exists clube_novo.otimizador_entrada_linha_v1;
drop function if exists clube_novo.atualizar_status_lote_otimizador_v2();
drop function if exists clube_novo.aplicar_delta_status_lote_otimizador_v2(uuid, integer, integer, integer, integer, integer, integer);
drop function if exists clube_novo.recalcular_status_lote_otimizador_v2(uuid);

notify pgrst, 'reload schema';

commit;
