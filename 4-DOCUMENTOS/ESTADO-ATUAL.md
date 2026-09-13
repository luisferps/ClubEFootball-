# Estado da implantação — 13/09/2026

Este é o registro único das pendências do plano principal. Não é um painel em tempo real.
A documentação foi consolidada; a rodada de produção continua em andamento.

## Implementado

- Boxes com ordem e análises prontas no banco nos três graus. Atualização automática
  quando a fonte muda, verificada a cada minuto e aplicada sem bloquear a leitura.
  A página consulta somente sua fatia; a próxima é antecipada em segundo plano.


- Grau global: notas e estrelas das boxes usam linhas e referências do mesmo grau.
  Ficha recebe o grau explicitamente, descarta respostas antigas e não mostra nota
  de outro grau quando falta publicação. Builds pessoais são reavaliadas para
  consulta sem alterar o registro salvo. Só o editor permite variar o grau local.


- Extrator corrigido e atualização do jogo extraída, aplicada e relida no banco.
- Correções manuais protegidas por campo em `valor_do_dono`, com histórico.
- Técnicos corrigidos e Mourinho ASTROS incluído no contrato do Otimizador.
- Molde v6 aplicado nos consumidores; fila antiga aposentada e nova fotografia entregue.
- Máquina 2 configurada com quatro processos e envio paralelo ao cálculo.
- Bonificador com conferência/reuso pelas regras atuais e cálculo de exceções.
- Site conferido; coluna JOGO, selo de régua e correção do tempo de consulta do Ranking.
- Cartas excluídas fora da operação; orçamento não divulgado tratado por regra geral,
  com aviso na Ficha e nova consulta em uma próxima execução diária do Extrator.
- Pasta oficial consolidada e manuais atuais separados das referências técnicas.
- Frontend: busca sem acentos, cancelamento de respostas ultrapassadas, carregamento
  independente de seções e remoção dos trechos mortos identificados. Consultas de
  Boxes usam leitura pronta e paginada, substituindo o cálculo integral a cada consulta.

Datas das boxes corrigidas em todo o acervo legado: 727 com data completa no título,
296 sem data comprovada; as 1.023 datas de observação foram preservadas separadamente.
Captura de boxes passa a atualizar contextos reconhecidos; vencimentos comprovados
encerram automaticamente sem apagar participantes. A leitura V2 dos detalhes foi validada na Summer Transfer vol.3: 150 IDs físicos
persistidos como prova, 11 especiais vinculados para exibição. Página parcial ou
agente ambíguo não publica. Oito ofertas da sessão ainda precisam ter os detalhes
capturados; a cobertura automática de todas as ofertas não está concluída.


## O que continua esperando

Pendência técnica descoberta na conferência do editor: o Otimizador omite boost
do técnico em atributos de peso zero em alguns resultados. Duas linhas comprovadas,
sem diferença na pontuação; extensão ainda não medida. Corrigir a composição e
preparar atualização compatível da Máquina 2. Ver
[prova](../Site%20Novo/PARIDADE-EDITOR-MOLDE-V6.md).

1. Máquina 2 terminar o Otimizador e o enviador entregar seus resultados.
2. Conferir composição e exposição pública do restante da rodada; o fechamento
   integral depende do término dos motores e da auditoria dos resultados.
3. Concluir a aba Elenco e as alterações de interface ainda não implementadas.

## Bonificador e publicações: conferência de 13/09/2026

No lote abaixo, o contrato oficial confirmou 193.543 linhas com bônus vinculados:
192.266 reaproveitadas e 1.277 exceções calculadas. Restavam zero exceções,
zero linhas sem conferência e zero impedimentos. O Bonificador está concluído
para essa população; cartas novas posteriores exigem nova conferência.

A consulta de publicação confirmou 2.900 resultados recebidos e 2.900 publicações
ativas, abrangendo 340 cards: nenhum recebido sem publicação, sem bônus, sem
Otimizador ou sem selo; todos os 2.900 com régua vigente. A última publicação dessa
consulta foi às 05:34:40 BRT. Isso confirma persistência e publicação ativa, não
recalcula todas as fórmulas nem garante exposição de toda linha pela fonte exibível.

A associação corrente do lote retornou 193.630 linhas; esse universo é diferente
das 193.543 linhas da fotografia conferida. Não usar um total como substituto do
outro. Estas contagens são evidência datada, não acompanhamento em tempo real.

## Fotografia da rodada

Lote: `39da8ff4-7a4a-4ec7-8641-e81b5677ad4c`.
Fotografia selada: 193.543 linhas elegíveis, 19.205 cartas.

| Prioridade | Cartas | Linhas |
|---|---:|---:|
| Novas extraídas | 176 | 1.277 |
| Demais com orçamento para evoluir | 11.999 | 113.642 |
| Demais sem orçamento para evoluir | 7.030 | 78.624 |

Overall decrescente dentro de cada grupo. Pacote selado não é alterado pela chegada
de novos dados; inclusão posterior passa pelo fluxo próprio de preparação/revisão.
O estado pausado do lote no banco não significa que o cálculo local esteja parado.

Selo do pacote: `fe3f1d2b0f038bf09555c68f3b893268ebdc7b129c58d8b8904a0382375b7098`.
Contrato: `19125a2b7ac906a702198266f051f2039df75c4658555f9b76fcba07d93623ec`.

## Histórico que explica a rodada

O recálculo integral reúne a correção dos técnicos e o molde v6 na mesma rodada.
As publicações anteriores continuam identificadas como régua antiga até substituição
válida. O snapshot `clube_novo.publicacao_snapshot_antes_1209` preserva a situação anterior.

Foram retiradas 12.892 linhas não calculadas de 1.563 cartas excluídas; elas não são
defeitos ou pendências operacionais. As dez cartas disponíveis sem orçamento divulgado
aguardam a fonte, sem orçamento inventado. O aviso atual é derivado dos dados, sem lista
fixa de IDs. Ver [regra diária](ORCAMENTO-REGRA-DIARIA.md).

O fechamento das correções de estilos/altura/complemento anteriores não significa
fechamento desta rodada. Não reabrir lotes históricos a partir de contagens antigas.
