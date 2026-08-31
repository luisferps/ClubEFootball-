-- V19 — Fecha as portas de serviço que ainda apontam para clube.fila/clube.build.
-- As funções permanecem preservadas para recuperação/auditoria, mas o service_role
-- do Otimizador não pode mais chamá-las. Nenhuma tabela, fórmula ou resultado muda.

begin;

revoke execute on function public.otimizador_proxima_fila_v1(integer) from service_role;
revoke execute on function public.gravar_build(jsonb) from service_role;
revoke execute on function public.fila_do_motor(integer,integer) from service_role;
revoke execute on function public.fila_do_motor(integer,text,integer) from service_role;
revoke execute on function public.cartas_da_fila() from service_role;
revoke execute on function public.estado_da_fila() from service_role;
revoke execute on function public.proxima_da_fila(integer) from service_role;
revoke execute on function public.otimizador_peso_ordem_v1() from service_role;
revoke execute on function public.peso_da_ordem() from service_role;
revoke execute on function public.pool_da_funcao(text,text) from service_role;

commit;
