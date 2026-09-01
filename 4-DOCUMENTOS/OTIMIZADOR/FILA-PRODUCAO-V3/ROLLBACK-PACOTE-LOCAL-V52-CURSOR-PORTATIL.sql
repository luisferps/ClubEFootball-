-- Rollback V52: remove somente os contratos V2 adicionados por esta migração.
-- Não altera lote, linhas, resultados, fórmula, publicação ou os contratos V1.

begin;

drop function if exists public.otimizador_portal_local_v8(text, jsonb);
drop function if exists public.otimizador_producao_pacote_local_linhas_v2(uuid, bigint, integer);
drop function if exists public.otimizador_producao_pacote_local_cartas_v2(uuid, text, integer);
drop function if exists public.otimizador_producao_pacote_local_manifesto_v2(uuid);

notify pgrst, 'reload schema';
commit;
