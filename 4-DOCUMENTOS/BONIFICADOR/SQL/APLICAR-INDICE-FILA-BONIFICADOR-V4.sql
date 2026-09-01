-- Índice físico da fila V4. Não altera linhas nem resultados.
-- A condição coincide exatamente com a fila canônica pronta para Bonificador.
create index concurrently if not exists build_linha_card_bonificador_pronta_v4_idx
  on clube_novo.build_linha_card (id)
  include (card_id,funcao_id,posicao_id,carta_versao,carta_fingerprint)
  where build_bonificador_id is null
    and lote_estado='concluido'
    and estado='pendente'
    and estado_otimizador='concluido'
    and pendencias @> array['bonificador_nao_executado']::text[];
