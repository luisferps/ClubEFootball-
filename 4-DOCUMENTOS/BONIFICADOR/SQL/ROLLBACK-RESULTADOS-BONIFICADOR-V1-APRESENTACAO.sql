begin;
revoke execute on function public.bonificador_resultados_v1(integer,integer) from bonificador_runtime,service_role,public,anon,authenticated;
drop function if exists public.bonificador_resultados_v1(integer,integer);
commit;
