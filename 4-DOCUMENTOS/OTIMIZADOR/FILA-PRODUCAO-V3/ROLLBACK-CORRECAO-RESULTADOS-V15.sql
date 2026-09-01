-- Rollback V15: V3 volta a delegar a V2, sem tocar nos dados.

begin;

create or replace function public.otimizador_producao_fila_operacional_v3(
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
begin
    return public.otimizador_producao_fila_operacional_v2(
        p_lote_id, p_offset, p_limite, p_grupo
    );
end;
$$;

notify pgrst, 'reload schema';

commit;
