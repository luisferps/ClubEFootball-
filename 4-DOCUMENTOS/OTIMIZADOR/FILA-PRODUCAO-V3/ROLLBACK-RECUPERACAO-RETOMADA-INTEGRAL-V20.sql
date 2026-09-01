-- Rollback V20.
-- Não desfaz uma recuperação já registrada e não apaga linha, Build ou evento.
-- Remove somente a porta futura de recuperação cirúrgica.

begin;

revoke all on function public.otimizador_producao_recuperar_falha_retomada_integral_v1(uuid, bigint, boolean)
  from public, anon, authenticated, service_role;
drop function if exists public.otimizador_producao_recuperar_falha_retomada_integral_v1(uuid, bigint, boolean);

notify pgrst, 'reload schema';

commit;
