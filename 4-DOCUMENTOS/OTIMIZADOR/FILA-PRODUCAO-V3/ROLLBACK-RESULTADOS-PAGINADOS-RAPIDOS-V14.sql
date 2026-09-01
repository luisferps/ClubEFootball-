-- Rollback V14: volta a leitura V2; não toca lotes, linhas, resultados ou fórmula.

begin;

revoke execute on function public.otimizador_portal_local_v2(text, jsonb) from bonificador_runtime;
drop function if exists public.otimizador_portal_local_v2(text, jsonb);
revoke all on function public.otimizador_producao_fila_operacional_v3(uuid, integer, integer, text)
  from service_role;
drop function if exists public.otimizador_producao_fila_operacional_v3(uuid, integer, integer, text);

notify pgrst, 'reload schema';

commit;
