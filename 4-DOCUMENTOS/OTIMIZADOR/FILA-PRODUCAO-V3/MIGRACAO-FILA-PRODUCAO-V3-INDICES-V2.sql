-- FILA PRODUTIVA V3 DO OTIMIZADOR — ÍNDICES DE COBERTURA
--
-- Complementa a migração V3 já aplicada. Não toca em fórmulas, dados de carta,
-- filas existentes, estados ou publicação; somente cobre FKs apontadas pelo
-- advisor de desempenho antes de qualquer lote ser criado.

begin;

create index if not exists otimizador_lote_producao_carta_card_idx
  on clube_novo.otimizador_lote_producao_carta_v3(card_id);

create index if not exists otimizador_lote_producao_linha_card_idx
  on clube_novo.otimizador_lote_producao_linha_v3(lote_id,card_id);

create index if not exists otimizador_evento_producao_linha_idx
  on clube_novo.otimizador_evento_producao_v3(linha_id);

commit;
