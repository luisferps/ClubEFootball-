-- Rollback V53: restaura o timeout herdado do papel do banco.
-- Não altera lote, linhas, resultados, fórmula, publicação ou gates.

begin;

alter function public.otimizador_producao_pacote_local_manifesto_v2(uuid)
  reset statement_timeout;
alter function public.otimizador_producao_pacote_local_cartas_v2(uuid, text, integer)
  reset statement_timeout;
alter function public.otimizador_producao_pacote_local_linhas_v2(uuid, bigint, integer)
  reset statement_timeout;

notify pgrst, 'reload schema';
commit;
