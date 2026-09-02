# Checklist V63 — lista da fila sem timeout

- [x] A lista mantém o contrato, a view privada e a ordem canônica da fila.
- [x] O total vem do resumo canônico por lote; a página não reconta 184 mil linhas.
- [x] A página solicita somente as colunas usadas pela tela, sem fotografias pesadas.
- [x] O teto de cinco segundos falha fechado em uma regressão futura.
- [x] Fila, fórmula, motor, resultados, publicação e arquivos do front-end permanecem inalterados.

Rollback físico: `RECUPERACAO/20260901-v63-lista-leve-antes/`.
