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

## C · NÃO estão nos arquivos estáticos — medido ❌
| insumo | veredicto |
|---|---|
| **Box comercial** | A procura antiga nos `.bin` estava correta ao não encontrar a relação comercial. Ela fica na resposta de sessão `CmdGetMyclubAgentlist`, com `agent_id`, título, datas e participantes. `PlayerVariationDetail.bin` guarda variação de carta. |
| **histórico de Boxes** | A resposta atual do jogo não recupera ofertas encerradas. O acervo histórico vem da cópia preservada do legado, somente com nome, participantes e data. |
| tier / votos / preço | comunidade / mercado — nunca no jogo. **FALTA.** |

## D · O QUE FALTA (resumo)
1. **Box** — novas ofertas vêm de `CmdGetMyclubAgentlist`; histórico vem do
   acervo legado fixo. Não deduzir pelo rótulo da variação da carta.
2. **tier, votos, preço** — comunidade/mercado, continuam do coletor web.
3. **tipo de crescimento** — pra fechar overall/max/cap na fonte; caçável no Player.bin.

Todo o resto lê-se direto do arquivo.
