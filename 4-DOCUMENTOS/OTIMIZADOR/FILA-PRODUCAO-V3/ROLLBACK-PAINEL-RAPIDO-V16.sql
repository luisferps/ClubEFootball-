-- Rollback V16: remove os contratos de apresentação V16; dados e fórmula não mudam.

begin;

revoke execute on function public.otimizador_portal_local_v3(text, jsonb) from bonificador_runtime;
drop function if exists public.otimizador_portal_local_v3(text, jsonb);
revoke all on function public.otimizador_rotulos_fila_v1() from service_role;
drop function if exists public.otimizador_rotulos_fila_v1();
-- Mantém V3 disponível e delega toda leitura à V2, equivalente à rota anterior.
create or replace function public.otimizador_producao_fila_operacional_v3(
    p_lote_id uuid, p_offset integer default 0, p_limite integer default 100,
    p_grupo text default 'abertas'
)
returns jsonb language plpgsql stable security definer set search_path to '' as $$
begin
    return public.otimizador_producao_fila_operacional_v2(
        p_lote_id, p_offset, p_limite, p_grupo
    );
end;
$$;

notify pgrst, 'reload schema';

commit;
