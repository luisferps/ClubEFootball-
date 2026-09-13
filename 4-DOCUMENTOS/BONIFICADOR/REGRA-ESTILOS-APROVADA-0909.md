# Bonificação de estilos — decisão aprovada em 09/09/2026

## Encerramento confirmado em 09/09/2026

A correção seletiva dos bônus de estilo terminou: **67.795 resultados e 7.455 publicações concluídos, zero pendências e erros nessa operação**. O banco e o painel confirmaram o encerramento em 2026-09-09T08:13:50.106412+00:00. As nove publicações finais foram conferidas no contrato da Ficha, preservando a revisão de habilidades do Otimizador e a ordem dos lotes. A falha do UPDATE de encerramento foi corrigida no banco e no SQL oficial.

Evidência e alcance: [Conclusão dos bônus de estilo](CONCLUSAO-BONUS-ESTILOS-0909.md). A produção geral do Bonificador e as execuções do Otimizador têm estados próprios; este encerramento não significa que seus lotes foram executados. Os registros de andamento abaixo são históricos.

## Retomada futura na Máquina 2 — arquivos preparados

Os arquivos V12 do Bonificador completo estão preparados para cópia direta.
O operador usa o mesmo INICIAR-REPROCESSAMENTO.bat após terminar a correção de
estilos. Antes disso, o comando não inicia nem reserva linhas. A versão do lote
e a política geral só serão atualizadas no início solicitado pelo operador.
Detalhes: [Entrega da Máquina 2](ENTREGA-MAQUINA-2-V12.md). Os registros anteriores abaixo são históricos.

## Operação atual — correção seletiva de estilos V12

O executor autônomo foi instalado e iniciado na máquina oficial. Corrige somente
os estilos de 67.795 resultados e atualiza 7.455 publicações, mantendo as notas
anteriores disponíveis até cada troca ser confirmada. Não declarar conclusão
antes do readback final do banco. Apenas o schema clube_novo é operacional.
A fila geral permanece pausada; a Máquina 2 será atualizada depois.
Código/EXE V12 estão preparados localmente. A política permanece com implantação
geral pendente; a execução seletiva já aplica a regra.
Fonte operacional: [Executor de estilos V12](EXECUTOR-ESTILOS-V12.md).
Os registros anteriores abaixo descrevem etapas históricas.

**Estado: regra aprovada, salva no banco e documentada; integração com a execução
do Bonificador pendente.**

Versão persistida: `estilos-funcao-20260909-v1`, em
`clube_novo.bonificador_politica_estilo`. Estado confirmado:
`aprovada_implantacao_pendente`. Fingerprint:
`7ed53bbab831180cde9d247782dd133fe072acadb69bd34871c3f83f28773dc5`.

Esta decisão substitui, para a próxima implantação, a escolha do slot principal
pela posição e a promoção genérica do secundário descritas na V11. A documentação
da V11 permanece como registro da operação anterior. A migração de registro
da política foi aplicada; ela não migra os consumidores, não recalcula resultados
e não modifica o Otimizador.

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

## 6. Evidência e alcance desta revisão

- Consulta em 09/09/2026: `clube_novo.playstyle`, `carta_playstyle_jogo`,
  `bonificador_regra_playstyle`, `posicao_jogo` e `bonificador_regua_v1()`.
- Regra de ativação existente: 31 estilos, 90 relações na régua consultada.
- `Player.bin` examinado, SHA-256:
  `a679eec7804fa487bb09ba586c822fa8f9a22652d7934fe6ea3b96bcb502b888`.
- `Playstyle.bin` examinado, SHA-256:
  `67a3f34ba9c63e5b84396e2891e3b0ac10a315125f4a6ae0eebeb032a06d0d38`.

Esta revisão salva decisões no manual oficial e no banco, preservando o histórico V11.
Não houve alteração de posições de ativação, código de motor, notas, publicação,
ordem de lotes ou pacotes da Máquina 2. A implantação da nova política de bônus
e as correções de interpretação dos estilos das cartas continuam pendentes.

## 7. Conferência executável e proteção contra esquecimento

A migração `registrar_politica_bonus_estilos_funcao_20260909_v1` criou o registro
versionado e a calculadora interna de leitura
`clube_novo.conferir_bonus_estilo_0909_v1`. Ela recebe função, posição e estilos
efetivos de ataque/defesa. Não grava builds e não é consumida pela produção V11.

O arquivo `SQL/VALIDAR-POLITICA-ESTILOS-0909-V1.sql` conferiu 25 casos numéricos
com valores manuais esperados, os quatro estilos pendentes e duas entradas
inválidas. Todos passaram em 09/09. Exemplos incluem Vieira, Desailly, Shevchenko,
Makélélé, Čech, Gerrard e contraprovas das duas exceções. A conferência não usa a
V11 como gabarito nem afirma que as cartas já foram corrigidas em produção.

A regra de uma versão é imutável: há fingerprint e gatilhos contra alteração
silenciosa e eliminação do histórico. O `AGENTS.md` na raiz exige a leitura desta
decisão nas próximas sessões. Os manuais e cadernos apontam para este documento.

Segurança: tabela com RLS; sem acesso de `anon`/`authenticated`; nenhuma nova RPC
pública. O aviso informativo de [RLS sem política de acesso público](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy)
é esperado para este registro interno fechado, não motivo para liberar acesso.

## 8. Pendências de execução que não devem ser confundidas com decisões em aberto

1. Integrar a política aprovada ao Bonificador, aos contratos e aos selos de
   resultados, com versão compatível para a Máquina 2.
2. Corrigir a projeção dos estilos efetivos das cartas antigas nas entradas do
   Bonificador e na Ficha, preservando os campos físicos originais. Conferir
   especialmente Primeiro Volante e Meia versátil nos dois slots, além de
   O destruidor no slot de defesa.
3. Conferir e reconciliar as parcelas de estilo afetadas com os novos contratos.
   O registro da regra não corrigiu as notas publicadas.
4. Manter apenas os quatro estilos da seção 5 aguardando definição futura.

Os critérios de pontuação estão fechados. Essas pendências são de implementação
ou de obtenção de dados do jogo; não são motivo para refazer a discussão da regra.
