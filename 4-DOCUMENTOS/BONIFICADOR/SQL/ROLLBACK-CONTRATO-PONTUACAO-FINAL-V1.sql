-- Rollback exclusivo do contrato de leitura V1. Nao apaga linhas nem resultados.
begin;

revoke all on function public.frontend_build_publicada_v1(text, bigint, integer, integer)
  from public, anon, authenticated, service_role;
drop function if exists public.frontend_build_publicada_v1(text, bigint, integer, integer);

revoke all on clube_novo.build_pontuacao_final_v1 from public, anon, authenticated, service_role, bonificador_runtime;
drop view if exists clube_novo.build_pontuacao_final_v1;

notify pgrst, 'reload schema';
commit;
