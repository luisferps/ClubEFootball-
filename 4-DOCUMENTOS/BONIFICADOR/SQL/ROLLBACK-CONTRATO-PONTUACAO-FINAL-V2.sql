-- Rollback exclusivo do contrato V2 normalizado.
-- Apaga somente a materialização V2; não toca nas linhas, nos resultados dos
-- motores nem na publicação V1 que já existia.
begin;

revoke all on function public.frontend_build_estado_v2(text)
  from public, anon, authenticated, service_role;
drop function if exists public.frontend_build_estado_v2(text);

revoke all on function public.frontend_build_publicada_v2(text, bigint, integer, integer)
  from public, anon, authenticated, service_role;
drop function if exists public.frontend_build_publicada_v2(text, bigint, integer, integer);

revoke all on clube_novo.build_pontuacao_final_v2
  from public, anon, authenticated, service_role;
drop view if exists clube_novo.build_pontuacao_final_v2;

revoke all on clube_novo.build_pontuacao_normalizada_v2
  from public, anon, authenticated, service_role;
drop table if exists clube_novo.build_pontuacao_normalizada_v2;

revoke all on function clube_novo.calcular_pontuacao_normalizada_v2(jsonb, jsonb)
  from public, anon, authenticated, service_role;
drop function if exists clube_novo.calcular_pontuacao_normalizada_v2(jsonb, jsonb);

notify pgrst, 'reload schema';
commit;
