# Bonificação de estilos — regra vigente

Política `estilos-funcao-20260909-v1`. Operação atual no [manual](../MANUAL-DO-BONIFICADOR.md). O fechamento de correções anteriores não encerra a rodada atual.

## 1. Como pontuar

1. A **função da build** determina se o slot principal é ataque ou defesa.
2. A **posição escolhida na build** determina se cada estilo ativa, segundo o
   cadastro de posições compatíveis com o jogo.
3. Estilo principal ativo: **1,0 ponto**.
4. Estilo secundário ativo: **0,5 ponto**.
5. Básico e estilo que não ativa na posição: **zero ponto** naquela parcela.
6. O secundário pode receber 0,5 mesmo se o principal não ativar. Ele não herda
   automaticamente o ponto ausente.
7. O total é 0, 0,5, 1,0 ou 1,5, consideradas as duas exceções da seção 3.

A posição nativa da carta, a associação histórica entre estilo e molde e o nome
parecido entre função e estilo não substituem a verificação de ativação.
Aprender uma posição também não amplia a lista de ativação de um estilo.
Os slots de ataque/defesa devem refletir o estilo efetivo do jogo; a mera ordem
dos dois campos físicos de uma carta antiga não comprova essa classificação.

## 2. Slot principal das 19 funções

| ID da função | Função | Principal | Secundário |
|---:|---|---|---|
| 1 | Centroavante fixo | Ataque: 1,0 | Defesa: 0,5 |
| 2 | Centroavante móvel | Ataque: 1,0 | Defesa: 0,5 |
| 3 | Falso nove | Ataque: 1,0 | Defesa: 0,5 |
| 4 | Goleiro defensivo | Defesa: 1,0 | Ataque: 0,5 |
| 5 | Goleiro ofensivo | Defesa: 1,0 | Ataque: 0,5 |
| 6 | Lateral defensivo | Defesa: 1,0 | Ataque: 0,5 |
| 7 | Lateral ofensivo | Ataque: 1,0 | Defesa: 0,5 |
| 8 | Meia ofensivo | Ataque: 1,0 | Defesa: 0,5 |
| 9 | Atacante infiltrador | Ataque: 1,0 | Defesa: 0,5 |
| 10 | Meia armador | Ataque: 1,0 | Defesa: 0,5 |
| 11 | Meia de arranque | Ataque: 1,0 | Defesa: 0,5 |
| 12 | Ala driblador | Ataque: 1,0 | Defesa: 0,5 |
| 13 | Ala cruzador | Ataque: 1,0 | Defesa: 0,5 |
| 14 | Atacante criador | Ataque: 1,0 | Defesa: 0,5 |
| 15 | Atacante driblador | Ataque: 1,0 | Defesa: 0,5 |
| 16 | Volante de construção | Ataque: 1,0 | Defesa: 0,5 |
| 17 | Volante de contenção | Defesa: 1,0 | Ataque: 0,5 |
| 18 | Zagueiro de combate | Defesa: 1,0 | Ataque: 0,5 |
| 19 | Zagueiro de saída | Defesa: 1,0 | Ataque: 0,5 |

Esta classificação pertence ao bônus de estilo. Ela não redefine a família
cadastral da função nem os moldes, pesos ou decisões do Otimizador.

## 3. Somente duas exceções

| Estilo | ID do jogo | Slot no jogo | Função abrangida | Posição de ativação |
|---|---:|---|---|---|
| Defensor Criativo | 271 | Ataque | Zagueiro de combate (18) e Zagueiro de saída (19) | ZC |
| Lateral Defensivo | 268 | Ataque | Lateral defensivo (6) | LE e LD |

Nas funções indicadas, se o estilo de exceção estiver ativo e for o único ativo,
ele vale **1,0** em vez de 0,5. Isso inclui o outro slot em Básico ou com um
estilo que não ativa na posição.

Quando os dois estilos estão ativos, mantém-se a composição normal: defesa
principal 1,0 e ataque secundário 0,5, total **1,5**. Não se somam dois pontos.
Se o próprio estilo de exceção não ativar, recebe zero.

Atacante Surpresa não é exceção. O fato de um estilo ter sido o único da carta
antes de 2027 não cria uma exceção. Não há outras promoções aprovadas.

## 4. Exemplos esperados da regra aprovada

| Situação | Total do bônus de estilo |
|---|---:|
| Principal ativo e secundário ativo | 1,5 |
| Principal ativo e secundário Básico/inativo | 1,0 |
| Principal Básico/inativo e secundário ativo, sem exceção | 0,5 |
| Nenhum estilo ativo | 0 |
| Zagueiro em ZC: Defensor Criativo + Básico | 1,0 |
| Zagueiro em ZC: Defensor Criativo + O destruidor, ambos ativos | 1,5 |
| Zagueiro em ZC: Atacante Surpresa + Básico | 0,5 |
| Lateral defensivo em LE/LD: estilo Lateral Defensivo + Básico | 1,0 |
| Lateral defensivo em LE/LD: Lateral Defensivo + Cobertura, ambos ativos no cadastro | 1,5 |

São valores esperados da política aprovada, não uma declaração de que os
resultados publicados já foram corrigidos ou de que todos os dados de entrada
auditados estão corretos.

## 5. Quatro estilos aguardam definição de ativação

| ID do jogo | Estilo | Cartas vinculadas no banco em 09/09 | Posições cadastradas |
|---:|---|---:|---|
| 87 | Pressão recuada | 0 | Pendentes |
| 95 | Marcador forte | 0 | Pendentes |
| 96 | Defensor recuado | 0 | Pendentes |
| 34 | Goleiro construtor | 0 | Pendentes |

Os quatro estão marcados como inativos em `clube_novo.playstyle`. A leitura de
`clube_novo.carta_playstyle_jogo` encontrou zero vínculos, e nenhum deles apareceu
nas 43.451 cartas de `Player.bin` da extração instalada examinada. Esses números
são uma fotografia da auditoria, não uma garantia para versões futuras.

**Decisão do usuário:** manter os quatro pendentes. Quando uma próxima extração
trouxer a definição, validar as posições e completar o cadastro. A hipótese de
uso futuro não é uma confirmação de lançamento ou de posições de ativação.
Uma nova carta vinculada, isoladamente, não estabelece todas as posições onde
o estilo ativa. Ausência de definição também não significa uma regra oficial
de que o estilo não ativa em posição alguma.

O cadastro já existe: `clube_novo.bonificador_regra_playstyle`, ligado a
`clube_novo.posicao_jogo`. Não criar outra tabela para a mesma relação, nem
preencher essas quatro listas por semelhança de nome. O cadastro deve ser
completado junto da validação dos contratos que o consomem: a régua V11 atual
confere cardinalidades e fingerprints, portanto uma inserção avulsa pode
invalidar o contrato operacional.

Pressão no ataque, Defensor participativo, Cobertura e os demais estilos já
utilizados conservam as posições cadastradas. A pendência destes quatro não
torna indefinidos os estilos que já têm regras. Distinguir o cadastro existente
da confirmação independente no texto ou arquivo do jogo.
