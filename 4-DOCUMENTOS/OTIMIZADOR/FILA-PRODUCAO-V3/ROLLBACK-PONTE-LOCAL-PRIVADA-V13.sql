-- Rollback V13: remove apenas a ponte privada local do Otimizador.
-- Não apaga linhas, resultados, lotes, fórmulas ou contratos de produção.

begin;

revoke execute on function public.otimizador_portal_local_v1(text, jsonb) from bonificador_runtime;
drop function if exists public.otimizador_portal_local_v1(text, jsonb);

notify pgrst, 'reload schema';

commit;
