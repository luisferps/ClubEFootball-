-- Rollback V50: remove apenas as funções novas do pacote local.
-- Não toca lote, build, resultado, fórmula, régua ou qualquer linha existente.

begin;

revoke all on function public.otimizador_portal_local_v7(text, jsonb)
  from public, anon, authenticated, bonificador_runtime;
revoke all on function public.otimizador_producao_concluir_lote_local_v1(uuid, jsonb)
  from public, anon, authenticated, service_role;
revoke all on function public.otimizador_producao_reservar_linha_local_v1(uuid, uuid, bigint, text, bigint, integer, text, text, text, text, text)
  from public, anon, authenticated, service_role;
revoke all on function public.otimizador_producao_pacote_local_linhas_v1(uuid, integer, integer)
  from public, anon, authenticated, service_role;
revoke all on function public.otimizador_producao_pacote_local_cartas_v1(uuid, integer, integer)
  from public, anon, authenticated, service_role;
revoke all on function public.otimizador_producao_pacote_local_manifesto_v1(uuid)
  from public, anon, authenticated, service_role;

drop function if exists public.otimizador_portal_local_v7(text, jsonb);
drop function if exists public.otimizador_producao_concluir_lote_local_v1(uuid, jsonb);
drop function if exists public.otimizador_producao_reservar_linha_local_v1(uuid, uuid, bigint, text, bigint, integer, text, text, text, text, text);
drop function if exists public.otimizador_producao_pacote_local_linhas_v1(uuid, integer, integer);
drop function if exists public.otimizador_producao_pacote_local_cartas_v1(uuid, integer, integer);
drop function if exists public.otimizador_producao_pacote_local_manifesto_v1(uuid);

notify pgrst, 'reload schema';

commit;
