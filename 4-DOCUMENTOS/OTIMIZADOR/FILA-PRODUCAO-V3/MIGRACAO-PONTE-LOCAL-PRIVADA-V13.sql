-- V13: ponte privada do servidor local para os contratos canônicos do Otimizador.
-- Não concede acesso a tabelas, não publica e não toca fórmulas, linhas ou resultados.
-- O único chamador adicional é o login local já protegido bonificador_runtime;
-- ele recebe exclusivamente esta allowlist fechada de RPCs do Otimizador.

begin;

do $$
begin
    if not exists (select 1 from pg_roles where rolname = 'bonificador_runtime') then
        raise exception 'V13 recusada: login local bonificador_runtime ausente';
    end if;
    if to_regprocedure('public.otimizador_producao_status_v6(uuid)') is null
       or to_regprocedure('public.otimizador_producao_fila_operacional_v2(uuid,integer,integer,text)') is null then
        raise exception 'V13 recusada: contratos V6/V12 exigidos estão ausentes';
    end if;
end;
$$;

create or replace function public.otimizador_portal_local_v1(
    p_operacao text,
    p_corpo jsonb default '{}'::jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
begin
    case p_operacao
        when 'otimizador_regua_v2' then
            return public.otimizador_regua_v2();
        when 'otimizador_carta_v3' then
            return public.otimizador_carta_v3(p_corpo ->> 'p_card_id');
        when 'otimizador_catalogos_apresentacao_v1' then
            return public.otimizador_catalogos_apresentacao_v1();
        when 'otimizador_carta_apresentacao_v1' then
            return public.otimizador_carta_apresentacao_v1(p_corpo ->> 'p_card_id');
        when 'otimizador_cartas_apresentacao_v2' then
            return public.otimizador_cartas_apresentacao_v2(
                coalesce(array(
                    select jsonb_array_elements_text(coalesce(p_corpo -> 'p_card_ids', '[]'::jsonb))
                ), array[]::text[])
            );
        when 'otimizador_producao_status_v3' then
            return public.otimizador_producao_status_v3(nullif(p_corpo ->> 'p_lote_id', '')::uuid);
        when 'otimizador_producao_status_v5' then
            return public.otimizador_producao_status_v5(nullif(p_corpo ->> 'p_lote_id', '')::uuid);
        when 'otimizador_producao_status_v6' then
            return public.otimizador_producao_status_v6(nullif(p_corpo ->> 'p_lote_id', '')::uuid);
        when 'otimizador_producao_controle_lote_v1' then
            return public.otimizador_producao_controle_lote_v1((p_corpo ->> 'p_lote_id')::uuid);
        when 'otimizador_producao_fila_operacional_v1' then
            return public.otimizador_producao_fila_operacional_v1(
                (p_corpo ->> 'p_lote_id')::uuid, (p_corpo ->> 'p_offset')::integer,
                (p_corpo ->> 'p_limite')::integer, p_corpo ->> 'p_grupo'
            );
        when 'otimizador_producao_fila_operacional_v2' then
            return public.otimizador_producao_fila_operacional_v2(
                (p_corpo ->> 'p_lote_id')::uuid, (p_corpo ->> 'p_offset')::integer,
                (p_corpo ->> 'p_limite')::integer, p_corpo ->> 'p_grupo'
            );
        when 'otimizador_producao_fila_paginada_v5' then
            return public.otimizador_producao_fila_paginada_v5(
                (p_corpo ->> 'p_lote_id')::uuid, (p_corpo ->> 'p_offset')::integer,
                (p_corpo ->> 'p_limite')::integer, (p_corpo ->> 'p_somente_finais')::boolean
            );
        when 'otimizador_producao_eventos_paginados_v5' then
            return public.otimizador_producao_eventos_paginados_v5(
                (p_corpo ->> 'p_lote_id')::uuid, (p_corpo ->> 'p_offset')::integer,
                (p_corpo ->> 'p_limite')::integer
            );
        when 'otimizador_producao_contexto_lote_v3' then
            return public.otimizador_producao_contexto_lote_v3((p_corpo ->> 'p_lote_id')::uuid);
        when 'otimizador_producao_controlar_lote_v3' then
            return public.otimizador_producao_controlar_lote_v3(
                (p_corpo ->> 'p_lote_id')::uuid, p_corpo ->> 'p_acao',
                coalesce((p_corpo ->> 'p_confirmado')::boolean, false)
            );
        when 'otimizador_producao_controlar_preparo_v5' then
            return public.otimizador_producao_controlar_preparo_v5(
                (p_corpo ->> 'p_lote_id')::uuid, p_corpo ->> 'p_acao'
            );
        when 'otimizador_producao_prevoo_integral_v5' then
            return public.otimizador_producao_prevoo_integral_v5();
        when 'otimizador_producao_criar_lote_integral_v5' then
            return public.otimizador_producao_criar_lote_integral_v5(
                (p_corpo ->> 'p_lote_id')::uuid, p_corpo ->> 'p_formula_fingerprint',
                p_corpo ->> 'p_motor_versao'
            );
        when 'otimizador_producao_iniciar_esteira_v6' then
            return public.otimizador_producao_iniciar_esteira_v6((p_corpo ->> 'p_lote_id')::uuid);
        when 'otimizador_producao_preparar_fatia_v5' then
            return public.otimizador_producao_preparar_fatia_v5(
                (p_corpo ->> 'p_lote_id')::uuid, (p_corpo ->> 'p_limite')::integer
            );
        when 'otimizador_producao_preparar_fatia_v6' then
            return public.otimizador_producao_preparar_fatia_v6(
                (p_corpo ->> 'p_lote_id')::uuid, (p_corpo ->> 'p_limite')::integer
            );
        when 'otimizador_producao_reservar_linha_v3' then
            return public.otimizador_producao_reservar_linha_v3(
                (p_corpo ->> 'p_lote_id')::uuid, (p_corpo ->> 'p_worker_id')::uuid
            );
        when 'otimizador_producao_reservar_linha_v6' then
            return public.otimizador_producao_reservar_linha_v6(
                (p_corpo ->> 'p_lote_id')::uuid, (p_corpo ->> 'p_worker_id')::uuid
            );
        when 'otimizador_producao_concluir_linha_v3' then
            return public.otimizador_producao_concluir_linha_v3(
                (p_corpo ->> 'p_lote_id')::uuid, (p_corpo ->> 'p_linha_id')::bigint,
                (p_corpo ->> 'p_reserva_token')::uuid, p_corpo -> 'p_resultado'
            );
        when 'otimizador_producao_concluir_linha_v6' then
            return public.otimizador_producao_concluir_linha_v6(
                (p_corpo ->> 'p_lote_id')::uuid, (p_corpo ->> 'p_linha_id')::bigint,
                (p_corpo ->> 'p_reserva_token')::uuid, p_corpo -> 'p_resultado'
            );
        when 'otimizador_producao_bloquear_linha_v3' then
            return public.otimizador_producao_bloquear_linha_v3(
                (p_corpo ->> 'p_lote_id')::uuid, (p_corpo ->> 'p_linha_id')::bigint,
                (p_corpo ->> 'p_reserva_token')::uuid, p_corpo ->> 'p_motivo'
            );
        when 'otimizador_producao_recuperar_reserva_orfa_v9' then
            return public.otimizador_producao_recuperar_reserva_orfa_v9(
                (p_corpo ->> 'p_lote_id')::uuid, (p_corpo ->> 'p_linha_id')::bigint,
                coalesce((p_corpo ->> 'p_confirmado')::boolean, false)
            );
        when 'otimizador_producao_falhar_lote_v3' then
            return public.otimizador_producao_falhar_lote_v3(
                (p_corpo ->> 'p_lote_id')::uuid, p_corpo ->> 'p_motivo'
            );
        else
            raise exception using errcode = '22023',
                message = 'Operação do Otimizador não permitida na ponte local';
    end case;
end;
$$;

revoke all on function public.otimizador_portal_local_v1(text, jsonb) from public;
grant execute on function public.otimizador_portal_local_v1(text, jsonb) to bonificador_runtime;

comment on function public.otimizador_portal_local_v1(text, jsonb) is
    'V13: ponte privada allowlist do servidor local do Otimizador; sem tabelas, legado ou publicação.';

notify pgrst, 'reload schema';

commit;
