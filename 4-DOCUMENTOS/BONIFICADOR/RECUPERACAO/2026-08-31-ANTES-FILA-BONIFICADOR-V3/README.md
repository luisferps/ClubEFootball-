# Snapshot anterior — fila Bonificador V3

Data: 2026-08-31.

Estado comprovado antes da aplicação:

- `clube_novo.bonificador_par`: 0 pares.
- Lote canônico de teste elegível ao Bonificador: 613 linhas, 50 cartas, 19 funções e 345 pares distintos carta×função. A projeção é distinta porque uma mesma combinação pode ocorrer em mais de uma linha de teste; a fila preserva as 613 linhas pela chave `build_linha_card.id`.
- Cada linha tem `pendencias = {teste_nao_publicado, bonificador_nao_executado}`. Essas marcas são estado de execução; não são entrada da fórmula nem falta física da carta.
- Nenhum cálculo, publicação ou escrita de resultado foi executado neste snapshot.

Recuperação: executar somente o rollback pareado `ROLLBACK-FILA-BONIFICADOR-V3.sql` após conferir que nenhum resultado V3 foi gravado.
