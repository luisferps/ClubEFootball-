-- Recuperação da apresentação humana V5. Não altera resultados nem dados de jogo.
begin;
revoke execute on function public.bonificador_contexto_fila_v5(integer,integer)
  from bonificador_runtime,service_role,public,anon,authenticated;
drop function if exists public.bonificador_contexto_fila_v5(integer,integer);
commit;
