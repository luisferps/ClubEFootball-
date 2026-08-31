-- Rollback de V16. Não altera cartas, dimensões, fórmula, fila ou resultados.
begin;
revoke all on function public.otimizador_pool_habilidades_v3(text,bigint) from service_role;
revoke all on function public.otimizador_cartas_v3(jsonb) from service_role;
revoke all on function public.otimizador_carta_v3(text) from service_role;
drop function if exists public.otimizador_pool_habilidades_v3(text,bigint);
drop function if exists public.otimizador_cartas_v3(jsonb);
drop function if exists public.otimizador_carta_v3(text);
commit;
