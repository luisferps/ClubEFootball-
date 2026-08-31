-- V20 — Fecha o grant PUBLIC herdado da ponte histórica pool_da_funcao.
-- O serviço atual usa somente otimizador_pool_habilidades_v3 por IDs.

begin;
revoke all on function public.pool_da_funcao(text,text) from public, anon, authenticated, service_role;
commit;
