# Conversão dos códigos de boost de técnicos

O código de Coach.bin não é o índice canônico do motor mais um. A antiga
regra `raw-1` acertava 42 de 106 boosts conferidos e errava 64.

Referência: 106 pares técnico/ordem da tabela `tecnico_efhub_20260912`,
resolvidos por nome em `atributo_jogo`. Todos os 106 boosts presentes no
Coach.bin atual pertencem a essa referência. Vinte códigos físicos foram
observados, cada um associado sem conflito a um único índice canônico.

| Código físico | Índice canônico |
|---|---|
| 1 | 0 |
| 2 | 1 |
| 3 | 3 |
| 4 | 2 |
| 5 | 4 |
| 6 | 5 |
| 7 | 6 |
| 8 | 8 |
| 10 | 7 |
| 11 | 10 |
| 12 | 11 |
| 13 | 12 |
| 14 | 21 |
| 15 | 19 |
| 16 | 20 |
| 17 | 23 |
| 18 | 24 |
| 19 | 22 |
| 20 | 25 |
| 26 | 13 |

Zero conserva ausência legítima. Códigos não comprovados são recusados;
não se inferiu a correspondência dos seis índices ainda não observados.
Fonte: Coach.bin hash `cb2484b8d29d4d966a22202cf463719c51c968a75f83fad05667263f4955eced`,
registro 176 bytes, bit160/w5 para ordem1 e bit148/w5 para ordem2.

Banco: campos 302 e 303 usam transformação `mapa_codigo_para_indice` e
normalizador `v2-boost-tecnico-mapa-1209`. Os 106 boosts manuais possuem
318 proteções por campo (atributo, delta e confirmação); readback 106/106.
Código: núcleo e leitor por contrato usam conversão estrita, sem raw-1.
Teste físico permanente: 106/106, mais rejeição de código desconhecido.
Tela: próximo relatório da varredura usará os atributos convertidos.

As referências individuais estão em
`7-VARREDURA-DO-JOGO/RESULTADOS-E-VALIDACOES/TESTES/boosts-conferidos-1209.json`.
A varredura 225832 iniciou antes dessa correção e seu pacote não deve ser
aplicado. Gerar outra pela interface com o contrato atual.
