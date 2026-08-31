-- Rollback de V20. Reabre a ponte histórica somente ao service_role.
-- Não devolve execução pública/anon/authenticated.
begin;
grant execute on function public.pool_da_funcao(text,text) to service_role;
commit;
