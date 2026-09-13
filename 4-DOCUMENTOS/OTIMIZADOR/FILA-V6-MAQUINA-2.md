# Fila v6 — estado da implantação

Lote `39da8ff4-7a4a-4ec7-8641-e81b5677ad4c`, selado e pausado no banco.

| Ordem | Grupo | Cartas | Linhas |
|---|---|---:|---:|
| 1 | Novas cartas extraídas | 176 | 1.277 |
| 2 | Demais cartas com orçamento | 11.999 | 113.642 |
| 3 | Demais cartas sem orçamento | 7.030 | 78.624 |
| | Total elegível | 19.205 | 193.543 |

Dentro de cada grupo: overall decrescente; ausência de overall fica ao final.
Os overalls das cartas novas têm prova eFHUB registrada. Correções manuais
continuam prevalecendo. As 12.979 linhas sem prova coerente de nível/orçamento
foram retiradas da execução; não foram confundidas com orçamento zero.

Molde v6 aplicado no banco e nos consumidores; selo vigente atualizado.
As 187 novas cartas extraídas existem na fonte física. Dez pendências de
nível continuam sem prova válida no eFHUB; não foi inventado orçamento.

O Otimizador foi ajustado para quatro processos na Máquina 2, com um único
escritor de JSONs e barreira entre grupos. Sete testes de prioridade,
concorrência e tratamento de falha passaram. A fotografia completa foi baixada e validada. O executável calculou quatro linhas reais com quatro processos, zero falhas e nenhum envio ao banco.

O Bonificador iniciou a conferência/reutilização pelo aplicativo: 4.800
linhas já haviam sido conferidas antes da atualização visual para 2.0.31.
A bonificação integral ainda não foi encerrada. A conferência foi retomada na versão 2.0.31 e já ultrapassou 22.700 bônus reaproveitados, sem impedimentos nessa leitura. Técnicos pertencem ao
Otimizador; reaproveitamento de bônus depende dos componentes e entradas.

Selo do lote:
`fe3f1d2b0f038bf09555c68f3b893268ebdc7b129c58d8b8904a0382375b7098`.

Ainda faltam: encerrar a
conferência de bônus e calcular somente as exceções. A pasta consolidada da Máquina 2 foi entregue com a fotografia validada e cinco executáveis atuais. O processamento integral será feito nela.

A comparação dos quatro resultados em paralelo com os mesmos quatro cálculos seriais passou: igualdade integral dos resultados, exceto horário e duração. O banco confirmou zero linhas otimizadas neste lote; os testes não enviaram resultados.

Foram arquivados mais 4.150 arquivos temporários e anteriores (17.191.736.792 bytes), fora da pasta operacional. As duas extrações finais e suas provas foram mantidas. A conferência desta movimentação comparou contagens e tamanhos; não repetiu hashes de todo o material arquivado.
