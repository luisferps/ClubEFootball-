-- V18: uma indisponibilidade transitória de contrato não invalida o lote.
-- Escopo cirúrgico: status de apresentação V7, recuperação de UMA falha já
-- comprovada sem linha ativa e ponte privada allowlist V5. Não toca fórmula,
-- pesos, moldes, cards, linhas, resultados, publicação ou tabelas legadas.

begin;

do $$
begin
    if to_regprocedure('public.otimizador_producao_status_v6(uuid)') is null
       or to_regprocedure('public.otimizador_portal_local_v3(text,jsonb)') is null
       or to_regprocedure('public.otimizador_rotulos_cartas_fila_v1(text[])') is null then
        raise exception 'V18 recusada: contratos V6/V16/V17 ausentes';
    end if;
end;
$$;

-- A V7 mantém a saída V6. A única diferença é tornar recuperável, de forma
-- explícita, o incidente em que ambos os canais falharam ANTES de reservar uma
-- linha. A condição é repetida na função de escrita abaixo; o texto da tela
-- nunca é a autoridade para recuperar o lote.
create or replace function public.otimizador_producao_status_v7(p_lote_id uuid default null)
returns jsonb
language plpgsql
stable
security definer
set search_path to ''
as $$
declare
    v_status jsonb;
begin
    v_status := public.otimizador_producao_status_v6(p_lote_id);
    if v_status ->> 'estado_lote' = 'falhou'
       and v_status ->> 'falha_lote' =
           'nenhum contrato seguro respondeu (ponte privada local e Data API); nenhuma linha foi iniciada'
       and coalesce((v_status ->> 'processando')::integer, -1) = 0
       and coalesce((v_status ->> 'pendentes')::integer, 0) > 0
       and coalesce((v_status ->> 'pode_publicar')::boolean, false) is false then
        v_status := jsonb_set(
            v_status,
            array['acoes'],
            coalesce(v_status -> 'acoes', '{}'::jsonb)
                || jsonb_build_object('retomar', true),
            true
        );
        v_status := jsonb_set(
            v_status,
            array['mensagem'],
            to_jsonb('Falha transitória de conexão antes de iniciar linha; Retomar recupera somente este lote selado.'::text),
            true
        );
    end if;
    return v_status;
end;
$$;

-- Não recria resultados e não devolve linha a pendente. Só pode reabrir o
-- incidente textual exato, no lote integral com a fórmula aprovada, sem linha
-- processando e ainda sem possibilidade de publicação.
create or replace function public.otimizador_producao_recuperar_falha_transporte_v1(
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
    v_falha text;
begin
    if p_lote_id is null then
        raise exception 'recuperação V18 recusada: lote ausente';
    end if;

    select * into v_lote
      from clube_novo.otimizador_lote_producao_v3
     where id = p_lote_id
     for update;
    if not found then
        raise exception 'recuperação V18 recusada: lote inexistente';
    end if;

    v_falha := coalesce(v_lote.falha, '');
    if v_lote.tipo_lote <> 'integral'
       or v_lote.estado <> 'falhou'
       or v_falha <>
           'nenhum contrato seguro respondeu (ponte privada local e Data API); nenhuma linha foi iniciada'
       or v_lote.formula_fingerprint <>
           '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad'
       or v_lote.pode_publicar is not false
       or v_lote.linhas <= 0
       or v_lote.preparo_concluido > v_lote.preparo_total then
        raise exception 'recuperação V18 recusada: selo/estado do lote não é o incidente transitório autorizado';
    end if;

    select count(*)::integer into v_processando
      from clube_novo.build_linha_card
     where lote_producao_id = p_lote_id
       and estado_otimizador = 'processando';
    if v_processando <> 0 then
        raise exception 'recuperação V18 recusada: existe linha ativa';
    end if;

    update clube_novo.otimizador_lote_producao_v3
       set estado = 'rodando',
           falha = null,
           atualizado_em = clock_timestamp()
     where id = p_lote_id;

    -- Usa um evento já pertencente ao contrato para não ampliar o catálogo de
    -- eventos de negócio. O detalhe mantém a prova da recuperação específica.
    insert into clube_novo.otimizador_evento_producao_v3(lote_id, evento, detalhe)
    values (
        p_lote_id,
        'lote_retomado',
        jsonb_build_object(
            'motivo', 'recuperacao_falha_transporte_v18',
            'falha_anterior', v_falha,
            'linhas_processando', v_processando,
            'formula_alterada', false,
            'pode_publicar', false
        )
    );

    return public.otimizador_producao_status_v7(p_lote_id);
end;
$$;

revoke all on function public.otimizador_producao_status_v7(uuid)
  from public, anon, authenticated;
revoke all on function public.otimizador_producao_recuperar_falha_transporte_v1(uuid)
  from public, anon, authenticated;
grant execute on function public.otimizador_producao_status_v7(uuid) to service_role;
grant execute on function public.otimizador_producao_recuperar_falha_transporte_v1(uuid)
  to service_role;

-- A ponte local preserva a allowlist anterior e acrescenta somente os dois
-- contratos V18 e os rótulos leves de V17. Não há SQL ou tabela livre para a UI.
create or replace function public.otimizador_portal_local_v5(
    p_operacao text,
    p_corpo jsonb default '{}'::jsonb
)
returns jsonb
language plpgsql
security definer
set search_path to ''
as $$
declare
    v_card_ids text[];
begin
    if p_operacao = 'otimizador_producao_status_v7' then
        return public.otimizador_producao_status_v7(
            nullif(p_corpo ->> 'p_lote_id', '')::uuid
        );
    end if;
    if p_operacao = 'otimizador_producao_recuperar_falha_transporte_v1' then
        return public.otimizador_producao_recuperar_falha_transporte_v1(
            (p_corpo ->> 'p_lote_id')::uuid
        );
    end if;
    if p_operacao = 'otimizador_rotulos_cartas_fila_v1' then
        if jsonb_typeof(coalesce(p_corpo, '{}'::jsonb) -> 'p_card_ids') <> 'array' then
            raise exception 'ponte V18 recusou card_ids fora do contrato';
        end if;
        select coalesce(array_agg(x.card_id), '{}'::text[])
          into v_card_ids
          from jsonb_array_elements_text(p_corpo -> 'p_card_ids') as x(card_id);
        return public.otimizador_rotulos_cartas_fila_v1(v_card_ids);
    end if;
    return public.otimizador_portal_local_v3(p_operacao, p_corpo);
end;
$$;

revoke all on function public.otimizador_portal_local_v5(text, jsonb)
  from public, anon, authenticated;
grant execute on function public.otimizador_portal_local_v5(text, jsonb)
  to bonificador_runtime;

comment on function public.otimizador_producao_status_v7(uuid) is
  'V18: status V6 com única retomada permitida para falha de transporte pré-reserva.';
comment on function public.otimizador_producao_recuperar_falha_transporte_v1(uuid) is
  'V18: recupera somente falha transitória pré-reserva, com fórmula selada, zero linha ativa e sem publicação.';
comment on function public.otimizador_portal_local_v5(text, jsonb) is
  'V18: allowlist privada local V13/V16 com status/recovery de transporte e rótulos por ID.';

notify pgrst, 'reload schema';

commit;
