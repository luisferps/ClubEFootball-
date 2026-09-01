-- Rollback V18: retira somente as portas V18. Não apaga linha, resultado,
-- evento ou a recuperação já registrada; esses dados são evidência operacional.

begin;

drop function if exists public.otimizador_portal_local_v5(text, jsonb);
drop function if exists public.otimizador_producao_recuperar_falha_transporte_v1(uuid);
drop function if exists public.otimizador_producao_status_v7(uuid);

notify pgrst, 'reload schema';

commit;
