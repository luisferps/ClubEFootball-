# Mapeamento físico dos níveis da sessão

Leitor `card-level-runtime-v2`, entregue no Extrator 5.3.0.1. Contrato publicado
por `public.extrator_contrato_niveis_runtime_v1()`, com registros nas tabelas
`clube_novo.contrato_leitura_nivel_runtime_v1` e
`clube_novo.contrato_leitura_campo_runtime_v1`. O extrator exige equivalência de
hash, versão, layout, offsets, tipos, transformações e destinos antes de coletar.

Executável validado: eFootball 6.0.0.0, SHA-256
`a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4`.
A base é descoberta no módulo do processo, sem pressupor endereço fixo.

`G = [base + 0x86c9fc0]`, `A = [G + 0x28]`, `C = [A + 0x08]`,
`B = [A + 0x20]`. Os colchetes representam leitura de ponteiro u64.

| Coleção | Cabeçalho início/fim/capacidade | Registro |
|---|---|---|
| Cartas próprias | C + 0/8/16 | 0xf0 bytes |
| Agentes das boxes | B + 0/8/16 | 0x238 bytes por agente |
| Pickup do agente | agente + 0xe8, três ponteiros | 0xf8 bytes por carta |
| Banner A do agente | agente + 0x200, três ponteiros | 0xf0 bytes por carta |
| Banner C do agente | agente + 0x218, três ponteiros | 0xf0 bytes por carta |
| StandardDraft/Procurable | B + 0x380/0x388/0x390 | 0xf0 bytes por carta |

No último vetor, `B+0x398` é total informado (u32), `B+0x3d0` é tamanho de
página informado (u32), `B+0x3d4` é índice inicial informado (u32). Os dois
consumidores usam a mesma estrutura; a captura não afirma qual resposta a
preencheu nem converte o total em cobertura de todo o catálogo.

| Campo da carta | Byte / bit / largura | Leitura e destino |
|---|---|---|
| Identidade | +8 / 64 / 64 | u64 little-endian; ID textual, conferido na extração física atual |
| Nível atual | +0x28 / 320 / 32 | u32 com representação XOR interna; somente prova da instância |
| Nível máximo | +0x2c / 352 / 32 | mesma representação; `carta_jogo.level_cap` |
| Orçamento máximo | derivado | `2 * nivel_maximo - 2`; `carta_jogo.orcamento` |

## Regra categorial física do tipo 3 — 07/09/2026

`Player.bin` é a fonte do código e do subtipo físicos já mapeados no cadastro.
Para `codigo_tipo_carta_fisico=3`, nos subtipos 0 e 1 observados, a família
POTW/POTM/POTS não recebe progresso: nível máximo1 e orçamento0. A prova fica
no contrato `clubef-player-type3-sem-evolucao-v1`, vinculada ao SHA-256 físico
`2afe17a686bef320dce3c4096355ba99b56bfb8a42b08018f0ae2fe444b05853`.

Essa regra não é uma inferência pelo texto da arte. Ela usa o campo físico do
tipo da carta e prevalece sobre o eFHUB, que registrou 26 divergências positivas
entre 3.524 cards tipo3. `carta_jogo.sem_evolucao` materializa o contrato como
campo gerado; a restrição `carta_jogo_tipo3_sem_evolucao_chk` e as triggers de
cadastro/evidência impedem nível ou orçamento positivos nessa categoria.

A representação usa o valor interno de `base+0x8686608`, relido para estabilidade.
O coletor não grava esse valor, bytes codificados ou dump de memória. A fórmula
foi rastreada no EXE (RVA 0x452b499), e a prévia real de Hicky mostrou nível 52
produzindo 102 pontos. Os controles adicionais foram Adriano 34/66, Totti 34/66,
Shevchenko 32/62 e Vitinha 1/0. Atributos divergentes de Hicky não foram incorporados.

Cada captura revalida os cabeçalhos dos vetores, ponteiros, identidade e níveis
de cada ocorrência, paginação e representação. Um ID com máximos conflitantes é
isolado; ID ausente da extração física não é promovido. A coleta não contém limite
46: esse foi o total observado na validação de 6 de setembro. Também há teste de
103 registros no vetor de recrutamento, sem truncamento à página nominal de 100.

`public.extrator_aplicar_niveis_runtime_v1` recebe captura e cartas. Lotes maiores
que 1.000 usam UUIDs derivados de forma estável e uma única transação. São
preservados captura, executável/hash, leitor, endereços de ocorrência, layout,
hash do artefato físico, cobertura e valores anteriores. O extrator confirma
valores e proveniência dentro da transação e em nova conexão após o commit.
`carta_nivel_evidencia_v1` registra a prova atual; o histórico permanece separado.

Nunca usar ausência como nível 1, inferir máximo por atributos ou copiar um máximo
de outra versão da carta. `Player.bin` confirma a identidade e os demais campos
que já possuem mapeamento; a fonte deste nível máximo é a memória da sessão.
