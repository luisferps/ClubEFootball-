# Manual do Otimizador — ClubEfootball

**Versão 1.7 · 28/08/2026**

## 1. Finalidade e nome

O **Otimizador** recebe uma carta, uma função e os insumos válidos do jogo e procura a
combinação de barrinhas, ímpetos, técnico e habilidades que maximiza a nota dessa
função. Ele não cria atributos, não inventa regra ausente e não deve rodar quando um
insumo obrigatório está incompleto.

O nome principal do componente é **Otimizador**. Os nomes históricos `motor`,
`2-MOTORES` e funções como `fila_do_motor` continuam existindo no código e no banco
por compatibilidade técnica; não significam um segundo componente.

O executável local do Otimizador fica em `2-MOTORES/OTIMIZADOR/`. A pasta
`2-MOTORES/` conserva apenas a configuração compartilhada e arquivos comuns de
outros fluxos; o Bonificador fica separado em `2-MOTORES/BONIFICADOR/`.

## 2. O que entra e o que sai

### Entradas da carta

- `card_id` original da Konami;
- os 26 atributos-base, na ordem canônica;
- orçamento e níveis possíveis das dez barras;
- ímpetos nativos e, quando permitido por gate próprio, o ímpeto escolhido;
- habilidades fixas, raras e escolhidas;
- posições, função avaliada e demais travas de elegibilidade.

### Entradas do técnico

- identidade do técnico;
- proficiências dos estilos de jogo de técnico;
- até dois boosts de atributo, cada um com atributo, ordem e delta;
- para o cálculo atual, usa-se a **maior proficiência** do técnico.

Os dados canônicos de técnicos estão carregados em `clube_novo`: identidade em
`tecnico_jogo`, proficiências em `tecnico_estilo_jogo` e boosts em
`tecnico_atributo_jogo`. `regua_pacote()` passou a montar a parte de técnicos a partir
dessas relações e mantém as chaves antigas de saída apenas para compatibilidade dos
consumidores. Link-up e demais campos de apresentação do técnico não mudam a nota
nesta versão.

O catálogo vigente contém seis estilos de técnico. Sobreposição (`overload`) foi
fisicamente comprovada no bit 135, largura 7, do `Coach.bin`. Apenas Antônio Conte
(`17609097478250`) possui valor não zero: 96. Assim, a maior proficiência dele passa a
ser 96 e `overload` é seu estilo principal; os outros técnicos não recebem uma relação
de Sobreposição com valor zero.

### Régua da função

Cada função entrega, por atributo, uma linha `(atributo, alvo, peso)`. A chave
consumida é `funcao_id`, ID canônico de `clube_novo.funcao_sistema`; o código legado
é traduzido somente na fronteira do contrato e o rótulo é apresentação. Alvos,
pesos, degraus, custos e multiplicadores continuam vindo das regras operacionais
vigentes, sem cópia nem alteração dos 494 valores de molde.

### Saída

O resultado contém a distribuição de barras, técnico, ímpeto, habilidades, os 26
valores calculados e a nota `b1`. A nota final publicada pode ainda combinar o bônus
separado `b_total`, conforme o contrato vigente do banco.

## 3. Sequência vigente do cálculo de atributo

Para cada um dos 26 atributos:

1. **Barras:** `referencia = min(99, base + barras)`.
2. **Proficiência:** localizar `m` em `clube.multiplicador` e calcular
   `com_prof = min(99, max(40, referencia + trunc(referencia × (m - 1))))`.
3. **Boosts do técnico:** somar o delta de cada boost depois da proficiência.
4. **Ímpetos:** somar os ímpetos nativos e o ímpeto escolhido depois dos boosts.
5. **Valoração de habilidades:** quando aplicável à nota do sistema, somar
   `ceil(referencia × pct/100 + flat)`. Essa camada lê a referência do passo 1 e não
   altera o número exibido pelo jogo.

O `trunc` do Otimizador corta a parte decimal na direção de zero. A proficiência mantém
o piso 40 e o teto superior 99. Boosts e ímpetos são somados depois e podem levar o
valor final acima de 99.

### Experimento discriminante aprovado — Lionel Messi

- carta `89138556575063`, Finalização-base 80;
- 19 níveis em Chute: Finalização 99; o jogo recusou os sete pontos restantes porque
  os dois atributos limitantes da barra já estavam em 99;
- Fabio Capello em Contra-ataque com bolas longas, proficiência 89 (`m = 1,036`);
- boost de Capello em Finalização: `+1`;
- ímpeto fixo Precisão em Finalização: `+4`;
- resultado exibido no campo: **104**.

Pela regra vigente: a proficiência recebe 99 e continua em 99 pelo teto; o boost leva a
100; Precisão leva a 104. A tentativa posterior daria entrada 103 à proficiência e
previa 107 com o truncamento codificado ou 107,708 antes da apresentação. Mesmo que a
tela arredonde ou trunque um valor interno, 107/108 não pode virar 104.

## 4. Tentativa posterior reprovada e revogada

Em 27/08/2026 foi tentada, sem autorização prévia, a sequência:

```text
base+barras -> ímpetos -> proficiência sem teto -> boost
```

Ela foi motivada pelos números visíveis de Alessandro Nesta e Marcel Desailly. Esses
casos não eram discriminantes: as duas sequências chegavam respectivamente a 102 e 100.
Além disso, a tela do videogame mostra inteiros e não revela, sozinha, eventual fração
interna nem a regra de apresentação.

O experimento controlado de Messi separou as hipóteses por pelo menos três pontos. O
jogo mostrou 104, exatamente a regra anterior; a tentativa posterior previa 107 ou
mais. Por decisão expressa do usuário, a tentativa está **REPROVADA E REVOGADA**. Não
deve ser reintroduzida por comentário, teste ou réplica de tela sem nova autorização e
uma nova prova discriminante.

## 5. Multiplicadores e proficiência do técnico

O multiplicador é lido por proficiência em `clube.multiplicador`. O caso usado no
experimento discriminante é:

| proficiência | multiplicador |
|---:|---:|
| 89 | 1,036 |

A fórmula usa a tabela inteira 0–99. Não interpola e não arredonda a proficiência para
um multiplicador inventado.

O Otimizador usa a maior das proficiências brutas do técnico. Se dois ou mais estilos
empatam no máximo, eles são **estilos gêmeos**: usam o mesmo multiplicador e produzem a
mesma pontuação. A view `clube_novo.tecnico_estilo_principal_jogo` escolhe o principal
pela ordem canônica de `estilo_jogo_tecnico` e devolve as demais chaves empatadas sem
duplicar a relação-base. No estado carregado há 82 técnicos com empate máximo e 124
relações gêmeas; empates com três ou mais estilos explicam a diferença entre as duas
contagens.

## 6. Como nasce a nota

A régua é uma valoração do ClubEfootball, não uma regra interna do videogame.

- Acima do alvo, contam nove degraus: `1; 0,88; 0,76; 0,64; 0,52; 0,40; 0,28; 0,16; 0,04`, multiplicados pelo peso da função.
- Abaixo do alvo, a punição usa incremento `0,25 × peso / 12` e para no nono ponto.
- Peso 1 é acessório e não pune quando fica abaixo do alvo.
- A nota é a soma das contribuições por atributo, arredondada para uma casa decimal.
- O Otimizador maximiza essa mesma régua por programação dinâmica; a antiga “bússola” de punição ×100 não é a nota vigente.

As habilidades comuns que atingem o mesmo atributo usam a vencedora inteira e cada
perdedora pela metade; raras somam inteiras. Essa é uma regra declarada do sistema e
deve permanecer separada das regras observadas no jogo.

## 7. Escolha e empates

O Otimizador procura o máximo exato dentro dos candidatos permitidos. Empates de nota
não criam pontos extras. Para proficiência, estilos empatados no maior valor são
equivalentes. Para habilidades de efeito equivalente, a incidência da comunidade pode
desempatar somente qual representante aparece; não altera a nota.

## 8. Fontes e caminhos ativos

| responsabilidade | caminho atual |
|---|---|
| fórmula canônica e multiplicador | `2-MOTORES/OTIMIZADOR/equacao.py` |
| busca local do ótimo | `2-MOTORES/OTIMIZADOR/motor.py` |
| execução em lotes | `2-MOTORES/OTIMIZADOR/roda_lote_v6.py` |
| avaliador do servidor | `6-AVALIADOR-NO-RAILWAY/avaliador.py` |
| otimizador de barras do servidor | `6-AVALIADOR-NO-RAILWAY/otimizador.py` |
| rotas do serviço | `6-AVALIADOR-NO-RAILWAY/app.py` e `servidor.py` |
| reprodução/conferência na tela vigente | `1-SISTEMA/motor-e-ficha-base.js` |
| fotografia publicada da tela | `SITE-ATUALIZADO-2026-08-24/motor-e-ficha-base.js` e `TELA-CLUBEFOOTBALL-UNICA.html` |
| técnicos canônicos do banco | `clube_novo.tecnico_jogo`, `tecnico_estilo_jogo`, `tecnico_atributo_jogo` |

As portas de **entrada** atuais do lote e da cópia local do serviço são
`otimizador_carta_v3`, `otimizador_cartas_v3`, `otimizador_regua_v2` e
`otimizador_pool_habilidades_v3`. Elas entregam somente IDs, números, bits e vetores.
Rótulos entram por portas separadas, `otimizador_catalogos_apresentacao_v1` e
`otimizador_carta_apresentacao_v1`, e nunca voltam para o cálculo.

A fila oficial usa `clube_novo.build_linha_card`. O resultado usa
`clube_novo.build_otimizador`. No lote da amostra, criação V3, estado/fila/eventos V2
e conclusão V2 operam essas mesmas tabelas. Os controles atômicos de iniciar,
pausar, parar e bloquear permanecem nas versões que já estavam seladas e também
atuam somente em `clube_novo`.

As portas são `SECURITY DEFINER`, têm `search_path=''`, usam nomes de objeto
totalmente qualificados e podem ser executadas somente por `service_role`. A UI não
acessa `clube_novo` diretamente. Os contratos V1 e `gravar_build` são históricos e
não participam do caminho oficial V2.

### Estado da migração de entradas

O lote local e a cópia local do serviço foram migrados para carta/pool V3 e régua V2. Os dados
de carta, atributos, corpo, posições, habilidades, estilo IA, identidades físicas,
dimensões e técnicos chegam por IDs estáveis/FKs. Nome ou texto só é anexado depois,
para apresentação e diagnóstico. A prova de renomeação confirma que trocar todos os
rótulos não muda vínculos, cálculo ou seleção dos 19 moldes.

Ímpetos já equipados estão ligados por `codigo_impeto`. O fixo entra em todas as
linhas; o condicional cria uma linha para cada nível físico de 1 até o máximo. O
motor não decide se a condição está ativa numa partida. Ímpeto adicional fabricável
continua fechado porque ainda não existe catálogo oficial correspondente em
`clube_novo`. `motor_bonus.py` continua separado e não foi ativado.

A interface própria do Otimizador está migrada: acompanha fila e resultados reais,
mostra rótulos somente após receber os IDs e exibe nível do Ímpeto, candidatas
avaliadas e total possível. As réplicas da tela principal do ClubeEfootball são outro
consumidor e não foram alteradas nesta etapa.

### A cadeia completa, em linguagem de jogo

Quando alguém roda **RODAR O MOTOR**, o lançador abre o aplicativo oficial do
Otimizador. O worker lê as linhas autorizadas em `build_linha_card`; cada linha chega
como carta, função, posição e, quando houver, código e nível do Ímpeto condicional.
Em seguida ele pede a ficha da carta e o pool ao contrato V3, e a régua/técnicos ao
contrato V2.
Tudo chega de `clube_novo`, com IDs ou bits físicos. Só a interface transforma esses
IDs em texto.

```text
RODAR-O-MOTOR.bat / RODAR-TUDO.bat
  -> OTIMIZADOR/RODAR-OTIMIZADOR.bat -> interface/servidor.py + fila_comparacao_legado_50.py
  -> roda_lote_v6.py -> fonte_unica.py -> carta/pool V3 + régua V2
  -> equacao.py + regua.py + motor.py + travas.py -> resultado de build
  -> otimizador_concluir_linha_teste_v2 -> clube_novo.build_otimizador
```

`fonte_unica.py` é o porteiro: se a RPC nova não responder ou algum gate recusar a
carta, ele para. Não volta para JSON, HTML ou RPC histórica. `equacao.py`, `regua.py`
e `motor.py` recebem vetores e IDs já resolvidos; os nomes de atributos, técnicos e
habilidades não decidem vínculo algum. `travas.py` faz a carta incompleta falhar
fechada. A rotina manual `CONFERIR-UMA-LINHA.bat` usa a mesma porta nova.

O serviço local tem outra porta de entrada, mas a mesma origem:

```text
Procfile: gunicorn app:app
  -> app.py -> banco.py -> carta/pool V3 + régua V2
  -> monta_regua.py + regua_do_banco.py -> avaliador.py + otimizador.py
```

Ele aceita `card_id`, `funcao_id`, `tecnico_id`, `skill_ids` e barras. Assim, a
interface nunca deve mandar “Capello”, “centroavante móvel” ou o nome de uma
habilidade como chave de cálculo. Para Ímpeto condicional, ela manda somente código
e nível; a condição de uso na partida continua sendo assunto de apresentação.

`gravar_build`, `grava_direto.py` e o corpo antigo de execução direta de
`roda_lote_v6.py` não fazem parte do lançamento oficial. A entrada direta antiga do
runner falha fechada para impedir que uma chamada acidental volte a `clube.fila` ou
`clube.build`.

## 9. O que está confirmado e o que continua pendente

### Confirmado por observação do jogo

- barrinhas param em 99;
- Messi com 19 níveis em Chute fica com Finalização 99 antes do campo;
- com Capello 89, boost `+1` e Precisão `+4`, a Finalização exibida no campo é 104;
- entre as duas fórmulas comparadas, esse resultado confirma proficiência com teto 99,
  depois boost e depois ímpeto, e rejeita a tentativa de pôr o ímpeto antes da
  proficiência sem teto.

### Regra do sistema, não prova do jogo

- pesos, alvos, degraus e punições da régua;
- valoração das habilidades e regra da metade;
- desempate por popularidade entre efeitos equivalentes.

### Pendente

- comportamento de outros pontos da tabela fora do cenário discriminante;
- existência de frações internas não exibidas pela interface: a busca somente leitura
  nas bibliotecas disponíveis não expôs uma representação intermediária fracionária;
- semântica e cardinalidade integral de `CoachLink.bin` para Link-up.

Não se conclui, a partir dos inteiros mostrados pela tela, se o jogo guarda uma fração
entre a proficiência e a apresentação. O Otimizador vigente usa truncamento explícito
como sua regra aprovada; o experimento do Messi decide a ordem e o teto entre as duas
hipóteses comparadas, mas não prova ausência de estado fracionário interno no jogo.

## 10. Validação e recuperação

Os testes permanentes ficam em `4-DOCUMENTOS/OTIMIZADOR/TESTES`:

- `teste_formula_aprovada.py` executa fórmula, Otimizador local,
  avaliador e otimizador do servidor;
- `teste_interface_formula_aprovada.js` executa a função vigente da tela e verifica a
  ordem proficiência com teto → boost → ímpetos nas três cópias atuais da interface;
- `teste_trava_formula_migracao.py` compara as rotinas matemáticas por AST e as
  réplicas preservadas byte a byte contra o snapshot anterior aos hunks;
- `teste_auditoria_entradas.py` valida divergências, cardinalidades, ausência de
  fallback e invariância sob renomeação de rótulos;
- `teste_auditoria_moldes.py` cobre os 19 moldes, 494 linhas e bloqueio de qualquer
  ponte sem ID comprovado.
- `teste_impetos_linhas_v12.py` cobre níveis 1 a 5, identidade da linha, contagem
  real de candidatas avaliadas e universo total possível.
- `teste_interface_local_otimizador.py` cobre a fila, os rótulos separados dos IDs
  e a exibição dos dois contadores.

Critério discriminante obrigatório: Messi `99 → proficiência 99 → boost 100 → Precisão
104`; sintaxe Python e JavaScript sem erro e concordância entre as implementações. A
carga de técnicos é validada ainda por Capello:
proficiências `46/89/57/89/64`, principal `longBallCounter`, gêmeo `longBall`, boosts
`Finalização +1` e `Talento defensivo +1`. A extensão de estilos é validada por Antônio Conte:
`68/73/90/68/89` nos cinco históricos, `Sobreposição=96`, principal `overload`, sem
gêmea; Capello continua sem essa relação.

O estado anterior à reversão está em
`4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/2026-08-28-ANTES-REVERSAO-FORMULA`, com arquivo
compactado das cópias afetadas e patch completo do worktree rastreado. Para recuperação,
usar preferencialmente `arquivos-antes-com-caminhos.zip`, que preserva os caminhos
relativos e foi conferido byte a byte contra as 16 entradas do snapshot original. A
carga canônica de Técnicos não foi revertida.

O registro verificável de arquivos, preservações, hashes e resultados está em
`4-DOCUMENTOS/OTIMIZADOR/CHECKLIST-REVERSAO-FORMULA-2026-08-28.md`.

O registro da migração de entradas está em
`4-DOCUMENTOS/OTIMIZADOR/MIGRACAO-ENTRADAS/`. A auditoria total cobriu 43.072 cartas;
as 269 cartas novas e as 34 alteradas coincidem exatamente com o manifesto físico
selado do Extrator. Nas 34 alteradas, 84/84 campos correspondem ao antes/depois
físico após as traduções comprovadas. O conjunto permanente fechou 17/17 testes.

O grafo de todos os satélites, suas entradas/saídas, linguagens, contratos e plano de
paridade está em
`4-DOCUMENTOS/OTIMIZADOR/MIGRACAO-ENTRADAS/AUDITORIA-CADEIA-SATELITES-2026-08-28.md`.
Antes de qualquer hunk novo, a paridade deverá comparar por `card_id` e campo:
origem antiga, contrato V2, IDs, cardinalidades, fingerprints, gates e a saída da
tela quando ela for afetada. Um rótulo renomeado não pode mudar a seleção. O rollback
restaura apenas o adaptador daquele elo a partir do snapshot da etapa; nunca repõe
um arquivo inteiro nem muda a fórmula.

### Comparação controlada com a versão anterior em 30/08/2026

O arquivo `clube.build_arquivo_2608` foi usado somente como referência de
comparação, nunca como entrada nem destino operacional. A ligação foi feita pela
chave `card_id + funcao_codigo`. Todos os insumos da execução atual vieram do
contrato V2 e das tabelas de `clube_novo`.

Uma amostra determinística de 50 linhas elegíveis terminou sem erro. Ela foi
limitada a linhas com orçamento zero, teto de nível 1 e sem Ímpeto condicional,
para permitir uma conferência curta sem disparar lote produtivo. O resultado foi:

- 20/50 tiveram a mesma nota `b1`;
- 9/50 tiveram a mesma nota `b1` e o mesmo vetor final dos 26 atributos;
- 11/50 empataram na nota `b1`, mas terminaram com vetor de atributos diferente;
- 30/50 tiveram nota `b1` diferente;
- portanto, 41/50 não foram integralmente iguais à referência anterior.

Esse resultado não aprova a integridade entre versões, mas também não prova sozinho
uma falha da fórmula: a execução atual usa os dados atuais de `clube_novo`, enquanto
o arquivo guarda uma fotografia anterior. Continua pendente separar, linha por linha,
o que é mudança legítima de insumo do que seria divergência com os mesmos insumos
selados. Como a amostra tinha orçamento zero, ela também não cobre distribuição de
barras nem os níveis do Ímpeto condicional.

Na cópia operacional atual, os testes vigentes do V12 passam. Dois guardas históricos
de recuperação não conseguem concluir porque não estão presentes o ZIP antigo de
`2026-08-28-ANTES-MIGRACAO-ENTRADAS` e os arquivos da pasta antiga
`SITE-ATUALIZADO-2026-08-24`. Essa ausência é uma pendência de recuperação histórica,
não uma falha de execução do caminho V2 atual.

### Checklist da reversão de 28/08/2026

- [x] experimento discriminante do Messi registrado com saída real 104;
- [x] tentativa posterior marcada como reprovada e revogada;
- [x] fórmula local restaurada sem desfazer entradas canônicas de Técnicos;
- [x] serviço e três réplicas de interface alinhados à fórmula aprovada;
- [x] testes antigos da hipótese revogada substituídos por regressões de 104;
- [x] banco, esquema, Extrator e consumidores permaneceram desligados e sem alteração.

## 11. Histórico

| data | decisão |
|---|---|
| 27/08/2026 | Nesta 102 e Desailly 100 motivaram a hipótese de ímpetos antes da proficiência sem teto; depois se comprovou que esses casos não distinguiam as fórmulas. |
| 27/08/2026 | A hipótese posterior foi replicada localmente sem autorização; este estado não é regra aprovada. |
| 28/08/2026 | Messi `89138556575063`, Chute 19, Finalização 99, Capello 89/+1 e Precisão +4 exibiu 104; a hipótese posterior previa 107 ou mais. |
| 28/08/2026 | Hipótese posterior reprovada e revogada; restaurada a regra vigente: barras → proficiência com teto 99 → boost → ímpetos. |
| 27/08/2026 | “Otimizador” passou a ser o nome principal do componente. |
| 27/08/2026 | Técnicos canônicos carregados: 1.594 identidades, 7.390 proficiências e 104 boosts; `regua_pacote()` passou a ler as três relações de `clube_novo`. |
| 28/08/2026 | Sobreposição foi comprovada no `Coach.bin` bit 135/largura 7 e carregada somente para Antônio Conte com 96; total de relações passou a 7.391. |
| 27/08/2026 | Frações internas permaneceram inconclusas; não foi criada regra de jogo por inferência. |
| 28/08/2026 | Entradas do lote e da cópia local do serviço migradas para o contrato `otimizador_*_v1`, exclusivamente por IDs canônicos, sem fallback e sem alterar fórmulas. |
| 28/08/2026 | 43.072 cartas auditadas contra extração física; 269 adições e 34 alterações físicas classificadas, zero divergência técnica remanescente. |
| 28/08/2026 | Réplicas de UI permaneceram não migradas e byte a byte intactas até existir endpoint seguro efetivamente implantado por IDs. |
| 28/08/2026 | Auditoria satélite confirmou que lançadores, lote e `app.py` local usam contrato v1; UI, projeções públicas e catálogos embutidos continuam bloqueio explícito de migração ponta a ponta. |
| 30/08/2026 | Contrato V2 passou a usar somente `clube_novo`, com linhas separadas por código e nível do Ímpeto condicional e entrada/saída exclusivamente por IDs. |
| 30/08/2026 | A saída passou a guardar separadamente candidatas realmente avaliadas e universo total possível da linha; prova real controlada registrou 9 de 41 nos níveis 1 e 3. |
| 30/08/2026 | V13 tornou os dois contadores obrigatórios no próprio banco e fechou a aceitação acidental de resultado com uma das chaves ausente. |
| 30/08/2026 | Comparação controlada de 50 linhas com `clube.build_arquivo_2608` encontrou 9 linhas integralmente iguais e 41 divergências ainda pendentes de separação entre mudança de insumo e diferença de cálculo. |
| 30/08/2026 | O lote anterior de 896 linhas foi removido do banco e dos arquivos locais; a V14 criou do zero uma fila parada com 50 cards do arquivo anterior e 613 linhas atuais, todas comparáveis por card + função. |
| 30/08/2026 | A V15 corrigiu o fechamento natural da rodada e a renovação do painel: sem pendentes/processando, o lote vira concluído, a linha atual some e Pausar é desligado. |

## 12. Aplicativo local do Otimizador

Para abrir sem depender da interface web antiga, dê dois cliques em
`RODAR-O-MOTOR.bat` na pasta principal ou em
`2-MOTORES/OTIMIZADOR/Otimizador ClubEfootball.exe`. O atalho
`RODAR-OTIMIZADOR.bat` confere a data do código e recompila o executável quando ele
estiver ausente ou desatualizado; depois abre a aplicação. O ícone
inicia um pequeno servidor privado em `127.0.0.1` e abre uma única janela de app no
navegador. A chave fica no `2-MOTORES/config.txt` compartilhado e nunca é entregue à
página.

O executável V1.1 só aceita como servidor já aberto a aplicação
`otimizador_clubefootball` na versão de interface esperada. Se outra cópia ou versão
antiga estiver usando a mesma porta, ele não abre silenciosamente a tela errada:
informa que a janela antiga deve ser fechada. O localizador do Python também consulta
o runtime empacotado, instalações locais, WindowsApps e o `PATH`.

Uso: informe o `card_id`, escolha a função e o técnico; clique **Simular**. A tela
mostra os IDs/entradas, barras e resultado, gates, cardinalidades e proveniência.
**Validar paridade** compara a função legível da equação aprovada contra o cálculo
inline do próprio Otimizador para a mesma simulação. No módulo Individual, a aplicação
usa `otimizador_regua_v2` e `otimizador_carta_v3`, que entregam somente IDs e valores
ao motor. Os nomes vêm separadamente de `otimizador_catalogos_apresentacao_v1` e
`otimizador_carta_apresentacao_v1`. O módulo Fila usa os contratos V2 de status,
fila, eventos e conclusão, além do controle V2 já existente. A página continua sem
credencial, acesso direto ao schema, `gravar_build`, lote produtivo ou cálculo de
condição do Ímpeto.

Arquivos da aplicação: `interface/servidor.py`, `interface/index.html`,
`interface/app.js`, `interface/style.css`, `windows-app/ClubEfootballOtimizadorLauncher.cs`
e `windows-app/COMPILAR-APLICATIVO.ps1`. O snapshot imediatamente anterior está em
`4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/2026-08-28-ANTES-EXECUTAVEL-LOCAL/`; rollback
remove apenas esses arquivos novos e restaura os itens daquele ZIP, sem tocar em
fórmulas, banco, UI geral, Extrator ou Bonificador.

O motor não decide quando a condição de um Ímpeto acontece. Para uma carta com
Ímpeto condicional, a fila cria uma linha por nível físico, e a tela identifica o
código e o nível. A condição de exibição continua sendo responsabilidade da tela.

## 13. Painel permanente e abas do executável local

O executável é uma única aplicação com três abas. **Rodada ativa** é a tela
principal e não possui texto, botão ou quantidade fixos de uma amostra antiga. Ela
acompanha a rodada selada que estiver ativa e mostra somente o resumo operacional,
os controles autorizados, a linha corrente e a lista pesquisável. A rodada atual tem
50 cartas e 613 linhas porque esses são os números devolvidos pelo contrato V14, não
porque a interface foi desenhada para essa quantidade.

**Rodada ativa** acompanha linhas `card_id + funcao_id + posicao_id +
impeto_condicional_codigo + impeto_condicional_nivel`, seu estado, motivo,
linha atual, totais e eventos reais do worker. **Resultados** mostra as mesmas linhas
depois de executadas, com a saída do Otimizador ou o bloqueio/falha final. Ambos são
marcados conforme `pode_publicar`; o lote vigente aparece como **TESTE · NÃO
PUBLICA**. **Testar uma carta** conserva a consulta
manual por `card_id`, função e técnico para investigar uma carta isolada.

A lista da rodada fica em uma área própria de rolagem, com altura limitada e
cabeçalho congelado. Assim uma fila de milhares de linhas não aumenta a página até o
fim. O navegador mantém no máximo 200 linhas desenhadas por página, oferece busca por
carta/função/posição, filtro de estado, navegação anterior/próxima e o botão **Ir para
o andamento**, que abre a página da linha corrente ou da primeira pendente. O mesmo
limite de 200 itens e o cabeçalho congelado valem para Resultados. Detalhes de
contrato, fingerprint, identificador da rodada e os 30 eventos mais recentes ficam
recolhidos em **Detalhes técnicos e eventos recentes**.

As colunas **Comparadas** e **Possíveis** aparecem em cada linha concluída nas duas
listas. Para não alargar a tela, valores grandes são abreviados (`mil`, `mi`, `bi`,
`tri`, `quadr.` e seguintes). O valor inteiro exato continua disponível ao passar o
mouse e dentro de **Ver build campeã**. O servidor entrega esses contadores como texto
à interface, evitando arredondamento quando `builds_possiveis` ultrapassa o limite de
inteiros exatos do navegador.

O contrato real está ligado ao lote selado registrado em
`teste-legado-50/estado-lote.json`. O lote contém exatamente 50 cards escolhidos entre
os 2.836 cards do arquivo anterior. Para cada card entram todas as funções e posições
atuais que possuem par antigo por `card_id + funcao_codigo`; uma mesma carta, função e
posição recebe ainda uma linha por nível do Ímpeto condicional. O navegador não pode
mandar outro `lote_id`. Antes de qualquer leitura ou controle, a ponte confere ID,
fingerprint, presença de cartas e linhas, modo
`teste_nao_publicado`, `pode_publicar=false`, estado ASCII permitido e o objeto
`acoes` devolvido pelo banco. Se algum selo não conferir, ela fecha a operação.
O worker específico desta comparação continua conferindo exatamente 50 cartas; o
painel visual usa as quantidades reais recebidas e permanece aproveitável para as
próximas rodadas seladas.

A V15 fecha automaticamente o lote quando a última linha deixa de estar pendente ou
em processamento. Nesse estado, a leitura devolve `concluido`, a linha atual fica
vazia e **Pausar** é desligado. A atualização automática da página é sempre agendada
depois que a leitura completa termina; assim uma resposta que demore mais de três
segundos não interrompe silenciosamente as próximas atualizações.

Fila e Resultados mostram linhas, totais e eventos reais do contrato. **Iniciar** só
habilita quando `acoes` autoriza iniciar ou retomar; texto, contagem ou estado visual
não autorizam ação. A ponte escolhe `iniciar` ou `retomar` somente entre as ações
autorizadas e executa o worker do lote selado. A retomada usa somente pendências, e a
conclusão idempotente impede resultado duplicado.

O contrato V8 diferencia os três controles. **Pausar** chama a ação `pausar`: solicita
`pausando` quando houver linha atômica, preserva as pendências e o worker confirma
`pausado` somente sem corrente. **Parar** só habilita quando `acoes.parar=true` e
`confirmacao.parar_exige_confirmacao=true`; a página exibe uma confirmação clara e
somente então envia `p_confirmado=true` à `otimizador_controlar_lote_teste_v2`.

Parar muda o lote para `encerrando` até a linha atual terminar ou falhar. O worker
chama `confirmar_encerramento` e o contrato torna o lote `encerrado`, preserva as
linhas concluídas e marca pendências como `interrompido`, sem apagá-las ou publicar.
Os estados exibidos são `parado`, `rodando`, `pausando`, `pausado`, `encerrando`,
`encerrado`, `concluido` e `falhou`; a interface apresenta `concluido` como
“concluído”.

### Leitura útil de Resultados (V9)

Cada linha da Fila e de Resultados é apresentada a partir de IDs canônicos: **Carta**
é sempre `card_id · nome oficial`; **Função** vem de `funcao_id` no catálogo da
régua; e **Posição** vem de `posicao_id` no catálogo da própria carta. Um ID que
realmente não tenha catálogo aparece como `ID n · catálogo ausente`, nunca como
“não informado”. Renomear qualquer rótulo não muda cálculo, vínculo ou fila.

Para uma linha concluída, o contrato de leitura V9 expõe a pontuação real persistida
(`build_otimizador.pontuacao`, apresentada também como `b1`), as barras e o técnico
canônico. A coluna **Tempo de processamento** usa os timestamps reais de início/fim
da mesma linha e retorna segundos reais (`42 s`; a partir de um minuto,
`1 min 05 s`). A interface não recalcula pontuação nem estima duração. Enquanto há
uma linha `processando`, a Fila mostra `Em processamento há …` a partir do timestamp
de início; sem linha corrente, o contador é removido.

Na tabela **Resultados**, a coluna compacta **Tempo** mostra a mesma duração real
sem espaços (`42s`, `1m05s`; quando houver fração real, por exemplo `1.31s`, ela é
mantida); não trunca nem altera o valor de origem. A coluna
**Build campeã** é própria e visível: o botão **Ver build campeã** abre a combinação
vencedora já persistida para a linha — barras, técnico, habilidades adicionais,
pontuação, candidatas comparadas e total possível da linha. Ímpeto adicional só é mostrado se
estiver presente no resultado persistido; quando o lote não o registrou, a tela diz
isso explicitamente e não inventa um valor.

O resumo de uma concluída só é montado dos campos reais recebidos (pontuação, barras
e técnico). Bloqueada, falhada ou interrompida mostra o motivo do contrato. A frase
técnica “Detalhe não exposto pelo contrato da fila” não é apresentada.

A tabela de Resultados é compacta: cada build ocupa uma linha. As barras aparecem
somente como a sequência de números, na ordem persistida; passar o mouse sobre o
resumo revela os rótulos correspondentes. As habilidades adicionadas são resolvidas
por `skill_id` no catálogo da régua e aparecem após as barras; o mesmo detalhe mostra
a lista completa. Isso é apresentação — não altera pesos, fórmulas ou a build.

Snapshot anterior a essa projeção/UI:
`4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/2026-08-28-ANTES-TEMPO-RESULTADOS/antes-tempo-resultados.zip`
(SHA-256 `C1BFE0F28C6237541853078762483057C1EABBAD7BD1F1503FAEC1A023EF7DF7`).
O rollback do contrato é
`ROLLBACK-FILA-TESTE-LEITURA-RESULTADO-V9.sql`; ele restaura só a projeção de
leitura, sem alterar tabela, fórmula, fila, publicação ou resultados.

A extensão V10 acrescenta somente `habilidades_adicionais` já persistidas à mesma
projeção. Seus scripts são `MIGRACAO-FILA-TESTE-HABILIDADES-RESULTADO-V10.sql` e
`ROLLBACK-FILA-TESTE-HABILIDADES-RESULTADO-V10.sql`.

### Telemetria de builds comparadas (V11, corrigida na V12)

`builds_comparadas` é o número real de candidatas finais que chegaram à comparação
naquela linha, depois das travas e reduções já aprovadas. É medido pelo executor
ao somar as avaliações internas da busca; uma rodada que avalia nove candidatas
registra nove, e não uma. Essa contagem não muda fórmula, pesos,
ordem, desempate ou a build vencedora. O campo é persistido junto ao resultado
de teste e aparece em **Fila automatizada** e **Resultados**. Linhas concluídas
antes da V11 mostram **Não registrada**: a interface não estima nem recalcula o
número. Pendentes mostram **Aguardando processamento**.

Na primeira instrumentação da V11, o contador observava apenas as rodadas externas
da busca. A prova V12 mostrou que uma única rodada pode avaliar várias candidatas;
por isso a coleta foi corrigida para somar o contador interno já produzido pelo
motor, sem tocar na fórmula nem na ordem da busca.

A V11 foi aplicada somente após a pausa segura do lote selado. O selo da fórmula
permanece `7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad`;
o contador foi colocado fora da fórmula exatamente para manter essa proteção.
Migração e rollback: `MIGRACAO-FILA-TESTE-BUILDS-COMPARADAS-V11.sql` e
`ROLLBACK-FILA-TESTE-BUILDS-COMPARADAS-V11.sql`.

### IDs, níveis e universo possível da linha (V12)

O V12 não cria outra tabela de resultados. A identidade da linha existente passa a
ser `card_id + funcao_id + posicao_id + impeto_condicional_codigo +
impeto_condicional_nivel`; em lote de teste, `lote_teste_id` também participa. Assim,
níveis 1, 2 e 3 da mesma carta e função não colidem. Se o máximo físico for 5, são
geradas cinco linhas. Carta sem Ímpeto condicional mantém código e nível nulos.

O nível máximo vem de `impeto_condicao_parametro_faixa_jogo.efeito_maximo`; quando
essa linha não existe para uma condição de avaliação ao vivo, usa-se o delta da
receita física em `impeto_atributo_jogo`. A própria tabela recusa código que não
pertença à carta, nível fora da faixa, nível ausente ou mais de um Ímpeto condicional.
O motor recebe e devolve somente IDs. A interface converte esses IDs em nomes por uma
porta de apresentação separada.

`builds_comparadas` continua registrando quantas candidatas finais o executor
avaliou até chegar à campeã. `builds_possiveis` registra outro número: o universo completo
daquela linha antes das podas de velocidade. Ele é calculado como combinações de
barras que cabem no orçamento × opções de Ímpeto adicional disponíveis × técnicos
válidos × combinações de habilidades permitidas. O nível condicional já identifica a
linha e não é multiplicado outra vez. O campo é numérico sem limite de inteiro curto,
pois o universo pode ser muito grande. A tela mostra os dois valores separadamente.

As regras que não tinham equivalente em `clube_novo` foram fotografadas nas tabelas
`otimizador_regua_parametro`, `otimizador_barra_atributo`,
`otimizador_custo_nivel`, `otimizador_multiplicador` e `otimizador_molde`. A cópia
inicial confere as quantidades na mesma transação; depois disso, todo contrato V2 lê
somente `clube_novo`. `clube.fila`, `clube.build` e as antigas tabelas de régua ficam
somente como história/conferência e não são fonte nem destino operacional.

O catálogo oficial de Ímpeto adicional fabricável ainda não existe em `clube_novo`.
Por isso essa escolha continua vazia e fechada, sem reconstrução por nome nem retorno
ao legado. Os Ímpetos já equipados na carta, fixos ou condicionais, estão ligados.

Migração: `MIGRACAO-ENTRADAS/MIGRACAO-OTIMIZADOR-CLUBE-NOVO-IMPETOS-V12.sql`.
Teste permanente: `TESTES/teste_impetos_linhas_v12.py`.

A migração `otimizador_clube_novo_impetos_v12` foi aplicada e relida em 30/08/2026.
As cinco tabelas oficiais fecharam, respectivamente, 8 parâmetros, 27 ligações de
barra, 25 custos, 100 multiplicadores e 1.430 linhas de molde, sendo 494 da versão 5.
As doze portas usadas pelo caminho V2 do Otimizador foram encontradas sem leitura de
`clube.*`. A prova curta usou a carta `105854837821566`, função `6` e Ímpeto `339`:
nível 1 e nível 3 produziram linhas distintas, cada uma com 41 builds possíveis e
9 candidatas realmente avaliadas. A gravação conjunta dos valores `9` e `41` foi
confirmada dentro de transação e revertida; nenhuma linha de prova permaneceu.

A conferência posterior encontrou uma abertura: os campos ainda aceitavam vazio e a
validação inicial não recusava com segurança uma chave ausente. A migração
`MIGRACAO-ENTRADAS/MIGRACAO-OTIMIZADOR-CONTADORES-OBRIGATORIOS-V13.sql` fechou essa
abertura. Agora `builds_comparadas` e `builds_possiveis` são obrigatórios em toda linha
de `clube_novo.build_otimizador`; ambos devem ser inteiros não negativos e a quantidade
avaliada não pode ultrapassar o universo possível. Não existe valor automático que
mascare uma contagem ausente. A rotina oficial também recusa explicitamente qualquer
resultado que não envie os dois números.

**Abrir console do lote** abre visivelmente o worker do mesmo lote de teste e obedece
aos mesmos selos. Não cria nova amostra, não agenda, não inicia lote produtivo, não
publica, não chama o Bonificador e não altera a fórmula.

O snapshot desta refatoração é
`4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/2026-08-28-ANTES-ABAS-FILA/antes-abas-fila.zip`.
Ele restaura somente a interface local e sua documentação, jamais fórmula, worker,
banco, Extrator, Bonificador ou UI principal.

Antes da ponte real, foram gravados snapshots recuperáveis em
`4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/2026-08-28-ANTES-PONTE-FILA-REAL/`
(`antes-ponte-fila-real.zip`, SHA-256
`40DAC8988E41CCB144589A7A89E7B8B3F2CF9A14E21693DD51D642259D67E28B`) e
`4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/2026-08-28-ANTES-WORKER-FILA-SELADA/`
(`antes-worker-fila-selada.zip`, SHA-256
`E58B4D0FE5276EA6B9C9D67E70CE395DEA7636B56D50500D585218750A3329EB`). O rollback
restaura somente a ponte ou o worker correspondente; não reverte banco, fórmula ou
outras alterações.

O snapshot anterior à separação visual **Pausar/Parar** está em
`4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/2026-08-28-ANTES-CONTROLES-PAUSAR-PARAR/`
(`antes-controles-pausar-parar.zip`, SHA-256
`15AFC101630327583ED7CE5427367D1426AE8C87DF5DE0A8C6E94590D76C5B02`).

O snapshot anterior à ponte V8 está em
`4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/2026-08-28-ANTES-PONTE-CONTROLES-V8/`
(`antes-ponte-controles-v8.zip`, SHA-256
`FABEA1AA771943D8CD2AA9E02BF5ADEB65DCFFBA3016AE81DE0A712B0DB1117E`).

A validação isolada positiva também foi concluída em 28/08/2026 com Axel Witsel
`105553384739779`, função Volante de construção `16` e Antonio Conte
`17609097478250`. A consulta online terminou com 26 atributos, nota `-441.5` e
gasto `56`; a paridade entre a equação legível e o cálculo inline fechou com o mesmo
SHA-256 `8486821d2c61bf9aed093f493c545450a10e3620f2a7e59210e2ba56f5254a3e`.
O relatório completo está em
`4-DOCUMENTOS/OTIMIZADOR/VALIDACAO-ISOLADA-EXECUTAVEL-2026-08-28.md`.

### Histórico encerrado da fila de 100 cartas

O lote anterior `912c518e-091c-4583-ae91-97b3e717517e` teve 100 cartas e 896 linhas;
866 chegaram a ser concluídas. Em 30/08/2026 ele foi encerrado como referência
histórica: suas linhas e resultados não existem mais no banco oficial, e os arquivos
locais `teste-100/estado-lote.json` e `teste-100/execucao.log` foram removidos. Nenhum
dado desse lote participa da nova rodada.

### Registro histórico encerrado da comparação anterior

A migração histórica
`MIGRACAO-ENTRADAS/MIGRACAO-FILA-COMPARACAO-LEGADO-50-V14.sql` criou a porta selada
da rodada atual. Ela só aceita criar a fila quando `build_linha_card`,
`build_otimizador` e `build_bonificador` estiverem zeradas. O arquivo
`clube.build_arquivo_2608` é somente referência: escolhe os cards e confirma o par
`card_id + funcao_codigo`; nenhuma linha é gravada, atualizada ou apagada nele.

Registro criado em 30/08/2026:

- lote `18690c93-4bb4-4b86-827a-f472fc92cc68`;
- fingerprint `d4552dcc5e768e435c3225f1ac456d5b8a660a45627d3a325091f352154cf465`;
- 50 cards distintos entre os 2.836 existentes no arquivo anterior;
- 613 linhas atuais, todas com par antigo por card e função;
- 8 cards com Ímpeto condicional, totalizando 210 linhas com nível;
- rodada concluída com 613 de 613 linhas, 0 pendentes, 0 processando e 0 falhas;
- 613 resultados do Otimizador preservados, sem publicação e sem execução do Bonificador;
- estado `concluido`, modo `teste_nao_publicado`.

Não existe executor nem atalho operacional para esse registro. A entrada e o
lançador históricos encerram imediatamente, sem ler o estado local, consultar RPC
ou iniciar worker. A interface atual também não os importa.

## 12. Fecho da migração de entradas — V16 a V20 (31/08/2026)

Esta seção prevalece sobre referências históricas a V1/V2 no restante do manual.
A fórmula aprovada não foi alterada: barras com teto 99 -> proficiência com piso
40/teto 99 -> boost do técnico -> Ímpetos. Pesos, alvos, moldes, ordem e critérios
de seleção também não foram alterados.

### Contratos ativos

| Slot do Otimizador | Contrato/tabela atual | Chaves aceitas | Proteção |
| --- | --- | --- | --- |
| ficha de carta, atributos, corpo, pé, posições, IA, habilidades, dimensões e Ímpetos físicos | public.otimizador_carta_v3 / otimizador_cartas_v3 | card_id, IDs físicos/FKs | recusa contrato diferente; não há fallback |
| pool de habilidades por função | public.otimizador_pool_habilidades_v3 | card_id + funcao_id | somente skill_id; gate da carta e da função |
| régua, 19 moldes, técnicos, pesos e multiplicadores | public.otimizador_regua_v2 + tabelas clube_novo.otimizador_* | funcao_id, tecnico_id, índice de atributo | régua selada; nenhum rótulo decide cálculo |
| compatibilidade função/posição usada para gerar linhas | clube_novo.otimizador_funcao_posicao | funcao_id + posicao_id | 30 pares, 19 funções, 2 FKs, RLS ativo |
| fila e resultados de teste | clube_novo.build_linha_card + clube_novo.build_otimizador | IDs da linha, carta, função e posição | teste/não publicado; gravação atômica selada |
| textos de tela | RPCs de apresentação V1 | IDs já resolvidos | não retornam ao cálculo |

V16 corrigiu somente o gate de dimensão: clube ou liga fisicamente ausentes não
são inventados nem bloqueiam por si. Chave física não nula sem catálogo apto segue
bloqueando. A prova é a carta 105647068843182: V2 devolvia
clube_bloqueado + liga_bloqueada; V3 devolve gate apto. Uma carta com vínculo físico
inválido (105553116303042) continua recusada.

V17 faz as três fábricas de amostra selarem a ficha V3. V18 materializou a tradução
já comprovada dos 30 pares de posição dos 19 moldes em FKs; depois da migração, a
geração consulta somente funcao_id + posicao_id, e não codigo_pt/rótulo. V19/V20
retiraram do service_role as portas históricas de clube.fila, clube.build,
gravar_build e pool_da_funcao. Elas foram preservadas apenas para recuperação,
mas o Otimizador não consegue chamá-las.

O lote concluído 18690c93-4bb4-4b86-827a-f472fc92cc68 permanece fotografia V2
histórica (613/613). Ele não é reexecutado nem misturado ao V3. Uma nova amostra
nasce com V3, selos próprios e a mesma fórmula.

### Recuperação e verificação

- Snapshot antes dos gates: RECUPERACAO/20260831-antes-gate-dimensoes-v16/.
- Snapshot antes da ativação do executável V21:
  RECUPERACAO/20260831-antes-ativacao-v21/.
- Rollbacks SQL isolados: ROLLBACK-OTIMIZADOR-GATE-DIMENSOES-V16.sql,
  ROLLBACK-FILA-SNAPSHOT-CARTA-V3-V17.sql,
  ROLLBACK-FUNCAO-POSICAO-IDS-V18.sql,
  ROLLBACK-BLOQUEIO-RPCS-LEGADAS-V19.sql e
  ROLLBACK-FECHO-POOL-LEGADO-V20.sql.
- TESTES/teste_contrato_v3_migracao.py protege consumidores V3, selos, FKs e o
  bloqueio do legado. O teste de fórmula continua independente.
- TESTES/teste_trava_formula_migracao.py compara o ZIP anterior quando ele está
  disponível; nesta cópia oficial, em que o ZIP não acompanha o checkout, ele
  compara o arquivo rastreado com o `HEAD` Git limpo para provar que esta
  migração não mudou a fórmula. As duas réplicas datadas ausentes continuam
  histórico, sem serem recolocadas no runtime apenas para teste.

O executável local é versão 20260831-v22: ao encontrar servidor V21 ou anterior, ele exige
reinicialização controlada para nunca mostrar código antigo como se fosse V3.

## 13. Fecho definitivo da frente de legado — V22 (31/08/2026)

`clube_novo` é a única autoridade operacional. A interface local, o serviço, o
carregador de cartas, a auditoria e os lançadores ativos usam exclusivamente os
contratos atuais por ID. Não existe fallback, consulta comparativa, fila, build ou
arquivo histórico em caminho operacional.

A aba Fila não apresenta uma rodada antiga: enquanto não houver contrato de fila
V3 explicitamente autorizado, ela mostra **Fila V3 não autorizada**, mantém todos
os controles desabilitados e não faz RPC de fila. Individual continua disponível
para consulta e validação local segura por `card_id`, `funcao_id` e `tecnico_id`.

O snapshot `RECUPERACAO/20260831-antes-fecho-legado-v22/` permite recuperar os
arquivos anteriores se houver autorização específica. Ele é evidência histórica,
não é importado, lido nem usado pelo Otimizador.

Validação V22: o executável recompilado respondeu em loopback com a versão V22,
fila e resultados indisponíveis, todos os controles desabilitados e POST de
Iniciar recusado com HTTP 409. O servidor usado nesse teste foi encerrado ao fim.
