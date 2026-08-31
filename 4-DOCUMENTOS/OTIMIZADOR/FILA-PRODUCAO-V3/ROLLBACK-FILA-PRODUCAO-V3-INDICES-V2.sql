-- ROLLBACK DOS ÍNDICES DE COBERTURA DA FILA V3
-- Não apaga lote, linha, resultado ou evento.

begin;

drop index if exists clube_novo.otimizador_evento_producao_linha_idx;
drop index if exists clube_novo.otimizador_lote_producao_linha_card_idx;
drop index if exists clube_novo.otimizador_lote_producao_carta_card_idx;

commit;
