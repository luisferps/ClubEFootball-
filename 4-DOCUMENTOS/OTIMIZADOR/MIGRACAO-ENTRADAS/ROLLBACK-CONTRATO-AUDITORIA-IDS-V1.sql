begin;

revoke all on function public.otimizador_ids_cartas_auditoria_v1()
from public, anon, authenticated, service_role;
drop function if exists public.otimizador_ids_cartas_auditoria_v1();

commit;
