-- Migration: 20260905213546_otimizar_status_publicacao_site_novo_v2
-- Objetivo: manter o contrato site-novo-publicacao-status-v1 sem varrer os
-- 211 mil itens do lote em cada abertura de Ficha.
-- Escopo: troca somente a leitura das contagens globais pelo cache transacional
-- já mantido pelos gatilhos do lote corretivo. Não altera notas, filas, cron,
-- publicação, timeout de role ou qualquer contrato JSON exposto.

begin;

set local lock_timeout = '3s';
set local statement_timeout = '30s';

do $preflight$
declare
  v_definition_md5 text;
  v_lote_id uuid;
  v_cache_exato boolean;
  v_gatilhos_cache integer;
begin
  if to_regprocedure('public.site_novo_publicacao_status_v1(text)') is null then
    raise exception 'preflight V2: public.site_novo_publicacao_status_v1(text) ausente';
  end if;

  select md5(pg_get_functiondef(p.oid))
  into v_definition_md5
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.proname = 'site_novo_publicacao_status_v1'
    and pg_get_function_identity_arguments(p.oid) = 'p_card_id text';

  if v_definition_md5 is distinct from 'c80851eccb9420decf0e8fa4d0922609' then
    raise exception 'preflight V2: função vigente divergiu do corpo auditado (%)',
      v_definition_md5;
  end if;

  if to_regclass('clube_novo.bonificador_correcao_status_cache_v1') is null then
    raise exception 'preflight V2: cache transacional do lote V10 ausente';
  end if;

  select count(*)
  into v_gatilhos_cache
  from pg_trigger t
  join pg_class c on c.oid = t.tgrelid
  join pg_namespace n on n.oid = c.relnamespace
  where not t.tgisinternal
    and n.nspname = 'clube_novo'
    and t.tgname in (
      'bonificador_correcao_cache_insert_v1_trg',
      'bonificador_correcao_cache_update_v1_trg',
      'bonificador_correcao_cache_delete_v1_trg',
      'bonificador_correcao_cache_novo_lote_v1_trg'
    );

  if v_gatilhos_cache <> 4 then
    raise exception 'preflight V2: conjunto de gatilhos do cache incompleto (%)',
      v_gatilhos_cache;
  end if;

  select id
  into v_lote_id
  from clube_novo.bonificador_correcao_lote_v1
  where tipo = 'integral'
    and motor_versao = 'v10-0409-fisico-regra-aprovada-v1'
    and estado in ('preparado','rodando','pausando','pausado','processado')
  order by criado_em desc
  limit 1;

  if v_lote_id is not null then
    with real as (
      select
        count(*)::bigint as total,
        count(*) filter (where estado_item = 'pendente')::bigint as pendente,
        count(*) filter (where estado_item = 'processando')::bigint as processando,
        count(*) filter (where estado_item = 'preparado')::bigint as preparado,
        count(*) filter (where estado_item = 'falha')::bigint as falha
      from clube_novo.bonificador_correcao_item_v1
      where lote_id = v_lote_id
    ), cache as (
      select total, pendente, processando, preparado, falha
      from clube_novo.bonificador_correcao_status_cache_v1
      where lote_id = v_lote_id
    )
    select
      r.total = c.total
      and r.pendente = c.pendente
      and r.processando = c.processando
      and r.preparado = c.preparado
      and r.falha = c.falha
    into v_cache_exato
    from real r
    cross join cache c;

    if v_cache_exato is distinct from true then
      raise exception 'preflight V2: cache do lote % não confere com os itens',
        v_lote_id;
    end if;
  end if;
end
$preflight$;

create or replace function public.site_novo_publicacao_status_v1(
  p_card_id text default null
)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $function$
declare
  v_lote clube_novo.bonificador_correcao_lote_v1%rowtype;
  v_total bigint := 0;
  v_preparadas bigint := 0;
  v_processando bigint := 0;
  v_falhas bigint := 0;
  v_card_fila boolean := false;
  v_publicadas bigint := 0;
  v_estado text;
begin
  select *
  into v_lote
  from clube_novo.bonificador_correcao_lote_v1
  where tipo = 'integral'
    and motor_versao = 'v10-0409-fisico-regra-aprovada-v1'
    and estado in ('preparado','rodando','pausando','pausado','processado')
  order by criado_em desc
  limit 1;

  if v_lote.id is not null then
    select c.total, c.preparado, c.processando, c.falha
    into v_total, v_preparadas, v_processando, v_falhas
    from clube_novo.bonificador_correcao_status_cache_v1 c
    where c.lote_id = v_lote.id;

    if not found then
      raise exception 'site novo: cache de status V10 ausente para o lote %',
        v_lote.id;
    end if;
  end if;

  if nullif(btrim(p_card_id), '') is not null then
    select count(*)
    into v_publicadas
    from clube_novo.build_publicacao_linha_ativa_v1
    where card_id = btrim(p_card_id);

    if v_lote.id is not null then
      select exists (
        select 1
        from clube_novo.build_linha_card l
        join clube_novo.bonificador_correcao_item_v1 i
          on i.lote_id = v_lote.id
         and i.build_linha_card_id = l.id
        where l.card_id = btrim(p_card_id)
      )
      into v_card_fila;
    end if;
  end if;

  v_estado := case
    when v_publicadas > 0 and v_card_fila then 'card_publicado_em_atualizacao'
    when v_publicadas > 0 then 'card_publicado'
    when v_card_fila then 'builds_em_atualizacao'
    when p_card_id is null and v_lote.id is not null
      then 'publicacao_incremental_em_andamento'
    else 'card_sem_build_publicada'
  end;

  return jsonb_build_object(
    'contrato', 'site-novo-publicacao-status-v1',
    'versao', 1,
    'estado', v_estado,
    'card_id', nullif(btrim(p_card_id), ''),
    'card_em_atualizacao', v_card_fila,
    'linhas_publicadas_do_card', v_publicadas,
    'lote_v10', case
      when v_lote.id is null then null
      else jsonb_build_object(
        'id', v_lote.id,
        'estado', v_lote.estado,
        'total', v_total,
        'preparadas', v_preparadas,
        'processando', v_processando,
        'falhas', v_falhas,
        'pendentes', v_total - v_preparadas - v_processando - v_falhas
      )
    end
  );
end
$function$;

comment on function public.site_novo_publicacao_status_v1(text) is
  'Contrato público V1; contagens globais V10 lidas do cache transacional desde a migração 20260905213546.';

revoke all on function public.site_novo_publicacao_status_v1(text)
  from public, anon, authenticated;

grant execute on function public.site_novo_publicacao_status_v1(text)
  to anon, authenticated, service_role;

commit;
