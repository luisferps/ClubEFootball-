-- Rollback V12: remove apenas a leitura de apresentação V2.
-- O contrato V11, fila, resultados, fórmula e publicação permanecem intactos.

begin;

revoke all on function public.otimizador_producao_fila_operacional_v2(uuid,integer,integer,text)
  from public,anon,authenticated,service_role;
drop function if exists public.otimizador_producao_fila_operacional_v2(uuid,integer,integer,text);

notify pgrst, 'reload schema';

commit;
