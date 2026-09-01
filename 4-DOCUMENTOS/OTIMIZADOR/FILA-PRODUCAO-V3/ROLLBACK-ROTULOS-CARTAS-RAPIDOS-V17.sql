-- Rollback técnico da V17. Não altera filas, linhas, estados, fórmulas ou resultados.
-- Só aplicar com o aplicativo V17 parado, pois remove o contrato de leitura novo.

begin;

revoke all on function public.otimizador_portal_local_v4(text, jsonb)
  from public, anon, authenticated, bonificador_runtime;
drop function if exists public.otimizador_portal_local_v4(text, jsonb);

revoke all on function public.otimizador_rotulos_cartas_fila_v1(text[])
  from public, anon, authenticated, service_role;
drop function if exists public.otimizador_rotulos_cartas_fila_v1(text[]);

notify pgrst, 'reload schema';

commit;
