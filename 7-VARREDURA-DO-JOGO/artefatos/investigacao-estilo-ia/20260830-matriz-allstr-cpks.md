# Matriz bounded — textos de estilo IA → CPKs de dados

Data: 2026-08-30  
Modo: somente leitura; nenhuma tabela de domínio, contrato ou arquivo do jogo foi alterado.

## Regra de evidência

A matriz começa no `all.str`. Só uma referência serializada comprovável em estrutura
física poderia ligar texto a código. Rótulos, ordem de entradas e o catálogo atual não
são chaves nem prova de associação a um bit.

## Fonte textual e âncoras

`dt261_bra_console_win.cpk` SHA-256:
`2419045a081a151f8a0cdcc70a9ca0c4ca1ca265b8467b9c182623baa05338db`.
`all.str` descompactado SHA-256:
`306741adab8376ed64620b618ae9721d316ae548b126419730b9bd5ff5f525a9`.

| Âncora física | Entrada | Offset entrada | Offset texto | Texto físico | Contexto atual, não-probatório |
|---|---:|---:|---:|---|---|
| `E15W:11` | 3 | 636268 | 637590 | Malandro | catálogo atual associa bit 616 |
| `E15W:13` | 4 | 636280 | 637599 | Drible veloz | catálogo atual associa bit 680 |
| `E15W:15` | 5 | 636292 | 637612 | Perito em cruzamento antecipado | catálogo atual associa bit 614 |
| `E15W:18` | 6 | 636304 | 637644 | Corrida com gás | catálogo atual associa bit 649 |
| `E15W:19` | 7 | 636316 | 637661 | Perito em chute de fora da área | candidato para 647, sem ponte |
| `E15W:76` | 25 | 636532 | 638005 | Rápido como uma bala | catálogo atual associa bit 674 |
| `E15W:77` | 26 | 636544 | 638027 | Perito em bola longa | catálogo atual associa bit 678 |

A descrição conjunta está em `Any1T:933`: seção índice 10, entrada 666,
offset de entrada 102784 e offset de texto 153519. Ela confirma o conjunto de
apresentação, não a codificação estrutural.

Foram procurados nomes de seção ASCII/UTF-16LE e os cabeçalhos exatos de 12 bytes
das oito entradas; não houve associação por aproximação de nome.

## Referências nos CPKs de dados

| Fonte | SHA-256 do CPK | Entradas | WESYS decodificados | Bytes | Seção/UTF-16 | Cabeçalho exato |
|---|---|---:|---:|---:|---:|---:|
| DT200 | `fd920cd8e7f3f1089892ef4051c68c1c5c56c49000ecf6f751025a0ae2c94a50` | 2991 | 1177 | 15494454 | 0 | 0 |
| DT870 Steam | `ae0d8cef26804439e9930ef8959f8d9425754d0e290d056b3e4d1f7b999edd5c` | 50 | 41 | 21766470 | 0 | 0 |
| DT870 atualização | `44df868c2613d532292d87072c0863a907d6a5f0cc40f914d355e56d74edfcc5` | 96 | 83 | 27284104 | 0 | 0 |

Os IDs isolados 11, 13, 15, 18, 19, 76 e 77 aparecem centenas ou milhares de
vezes sem seção, cabeçalho, tipo ou sequência validada. Foram rejeitados como
coincidência.

`all_diff.str` no DT870 de atualização tem 78 bytes compactados
(SHA `8052ed634bf40905402a14fdd2f9fc1b56afe6400c0207f68618d12839ed2ec4`) e 80
bytes após `inflate` (SHA `c9bd5984052b49b1316cd2cf62e90250806bd798f9846722e3c6c95f3a8cb3cd`).
Contém uma diferença `Any4W`, não uma âncora de estilo.

Os blocos restantes `ff22025745535953` foram classificados sem promovê-los como
fonte: no DT870, oito ou nove são stubs de 16 bytes sem payload; no DT200, 1.803
blocos têm 112 bytes e tamanho compactado igual ao original (96). A forma disponível
não contém seção/UTF-16/cabeçalho observado. O decodificador WESYS atual devolve
`TypeError` para suas amostras, portanto não foi usado para inventar uma leitura.

A pasta de referência `VER DADOS DO JOGO` foi consultada só como pista. Seus
relatórios e cópias históricas não foram usados como prova nem copiados para o
contrato; não contêm associação física nova texto → bit.

## Validação cruzada e bit 647

Os sete campos comprovados ficam nos bits 614, 616, 647, 649, 674, 678 e 680,
bytes relativos 76, 77, 80, 81, 84, 84 e 85 do registro de 400 bytes de
`Player.bin`. Eles estão intercalados com habilidades e outro campo de carta;
não há faixa contínua ou tabela enumerável.

O catálogo atual aponta 647 para `E13W:19`, cujo texto físico é `Categoria`.
`E15W:19` é semanticamente plausível, mas só candidato. Consultas read-only
não acharam `E15W`/`E13W` em `contrato_leitura_campo`,
`contrato_leitura_envelope_mapeamento` ou `mapa_do_jogo`; este mapa registra
o arquivo do catálogo como `(a achar)`. Não existe prova independente para
corrigir o 647 nesta fase.

## Próximo teste bounded

Inspecionar os blocos não-WESYS restantes dos mesmos três CPKs, começando pelo
formato `ff22025745535953`, apenas para verificar se contêm payload textual ou
índice. O executável está deliberadamente excluído.
