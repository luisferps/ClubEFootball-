-- V7 corrige uma escrita incompatível com a coluna ALWAYS IDENTITY.
-- Não há rollback automático para a versão defeituosa: reintroduzi-la faria a
-- primeira conclusão falhar outra vez. Para abandonar V6/V7, pare a esteira e
-- use o rollback V6, que falha fechado enquanto existir preparo em paralelo.
begin;
revoke all on function public.otimizador_producao_recuperar_esteira_v7(uuid, text)
  from public, anon, authenticated, service_role;
drop function if exists public.otimizador_producao_recuperar_esteira_v7(uuid, text);
commit;
