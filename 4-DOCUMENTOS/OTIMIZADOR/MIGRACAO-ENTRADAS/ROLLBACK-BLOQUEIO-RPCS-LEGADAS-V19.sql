-- Rollback de V19. Reabre somente ao service_role as portas históricas abaixo.
-- Usar apenas para recuperação autorizada; não reativa o caminho no código.
begin;

grant execute on function public.otimizador_proxima_fila_v1(integer) to service_role;
grant execute on function public.gravar_build(jsonb) to service_role;
grant execute on function public.fila_do_motor(integer,integer) to service_role;
grant execute on function public.fila_do_motor(integer,text,integer) to service_role;
grant execute on function public.cartas_da_fila() to service_role;
grant execute on function public.estado_da_fila() to service_role;
grant execute on function public.proxima_da_fila(integer) to service_role;
grant execute on function public.otimizador_peso_ordem_v1() to service_role;
grant execute on function public.peso_da_ordem() to service_role;
grant execute on function public.pool_da_funcao(text,text) to service_role;

commit;
