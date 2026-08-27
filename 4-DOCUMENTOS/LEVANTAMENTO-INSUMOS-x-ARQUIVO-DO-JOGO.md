# LEVANTAMENTO — Cada insumo do sistema × o arquivo do jogo
_Medido em 25/08/2026, carta por carta, com cartas que batem exato (card_id = PID)._

## A · ESTÃO no arquivo — leitura direta ✅
| insumo | onde |
|---|---|
| card_id | Player.bin offset 8 |
| nome | Player.bin offset 88 (especiais em japonês) |
| posição nativa | bit 556 |
| posições secundárias / aptidão | bit 510 |
| atributos (26) | bit 480 (6b cada) |
| habilidades nativas | bit 664 + PlayerSkill.bin |
| estilo de jogo | bit 372 + Playstyle.bin |
| estilo de IA | bit 678 |
| pé bom | bit 654 |
| pé ruim — uso / precisão | bit 478 / 578 |
| altura, peso, idade, resistência, forma | Player.bin |
| nacionalidade | bit 328 + Country.bin |
| corpo | PlayerAppearance.bin |
| ímpeto — vaga + fábrica | bytes 36-39 + PlayerBooster.bin |
| tipo Epic/Legend/POTW | PlayerVariationDetail.bin + PlayerWeekly.bin |

## B · SE PRODUZEM do arquivo (não é campo gravado) 🔢
| insumo | como | prova |
|---|---|---|
| overall mínimo | conta sobre atributos | "guarda o mínimo, o máximo faz a conta" |
| overall máximo | atributos + curva de crescimento | é decimal (98,04) |
| level_cap | mesma curva de crescimento | corr (max−ovr)×cap = 0,90 |

Pendência: achar o campo de **tipo de crescimento** por carta → fecha overall/max/cap 100% na fonte.

## C · NÃO estão no arquivo — medido ❌
| insumo | veredicto |
|---|---|
| **box_id** | procurado em u64 (LE/BE) e texto em 16 decifrados + cpk crus → **0 de 6**. É id do efootballdb, não da Konami. **FALTA.** |
| tier / votos / preço | comunidade / mercado — nunca no jogo. **FALTA.** |
| data de lançamento | hoje vem do efootballdb. **A CONFERIR** na variação. |

## D · O QUE FALTA (resumo)
1. **box** — não está no arquivo (0/6). Continua do efootballdb.
2. **tier, votos, preço** — comunidade/mercado, continuam do coletor web.
3. **tipo de crescimento** — pra fechar overall/max/cap na fonte; caçável no Player.bin.

Todo o resto lê-se direto do arquivo.
