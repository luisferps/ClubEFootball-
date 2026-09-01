# Manual do Otimizador — ClubEfootball

**Versão 2.1 · 31/08/2026**

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

### Ciclo de vida do aplicativo local — V30

O aplicativo oficial é 2-MOTORES/OTIMIZADOR/Otimizador ClubEfootball.exe.
Um clique abre o painel e mantém um único controlador do Otimizador no ícone perto
do relógio do Windows. Esse ícone é a referência do processo local:

- **Worker ativo · linha N · calculando**: este computador está de fato avaliando
  aquela linha; o painel pode ser fechado e reaberto pelo ícone sem interromper
  o trabalho;
- **Servidor local ativo · nenhum worker local**: o aplicativo está pronto, mas
  não afirma que uma linha esteja sendo calculada neste computador;
- **Servidor local indisponível**: não inicie nem retome por tentativa; o painel
  deixa claro que não consegue falar com o serviço local.

Fechar a janela do navegador não pausa, não encerra e não “esconde” uma decisão de
fila: apenas fecha a visualização. Para pausar ou parar, usar exclusivamente os
botões **Pausar** ou **Parar** do painel. O controlador permanece visível perto do
relógio justamente para que o operador não precise procurar processos no Gerenciador
de Tarefas para saber se uma execução ainda existe.

Se a fila do banco mostrar uma linha processando, mas o estado local disser que
não há worker, a interface mostra a divergência como **Reserva sem worker local**.
Ela não mostra contador verde de cálculo, não chama a reserva de “processando agora”
e não tenta reassumir, recalcular ou tomar a reserva automaticamente: a recuperação
dessa linha exige o contrato/ação segura apropriado, preservando o token, os
resultados concluídos e a proibição de publicação.

O snapshot imediatamente anterior a esse ajuste é
4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/20260831-antes-ciclo-vida-worker-v30/.
O ajuste V30 só acrescenta observabilidade e o controlador persistente: não muda
fórmula, pesos, moldes, fila, resultado, banco ou publicação.

### Recuperação de reserva órfã — V31

Se uma pausa ou um encerramento já foi pedido, mas o computador perdeu o worker
antes de ele terminar a linha atômica, o painel não finge que a fila está
rodando. Nessa condição excepcional aparece **Recuperar fila**. A ação exige uma
confirmação e só é oferecida se este serviço local não tiver worker nem
preparador, o lote estiver em `pausando` ou `encerrando` e houver exatamente uma
linha em `processando`.

O contrato privado
`otimizador_producao_recuperar_reserva_orfa_v9(lote_id, linha_id, confirmado)`
repete os gates no banco: lote integral, fórmula aprovada, `pode_publicar=false`,
estado compatível e reserva vigente. Ele devolve apenas a linha órfã para
`pendente`, limpa o token/worker daquela reserva, preserva tentativas e todas as
linhas concluídas e registra o evento de recuperação. O lote termina em
**Pausado**; ele não recalcula nada nem retoma sozinho. Depois, o operador usa o
botão normal **Retomar**.

O snapshot anterior está em
`4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/20260831-antes-recuperacao-reserva-orfa-v31/`.
A migração e seu rollback de contrato estão em
`4-DOCUMENTOS/OTIMIZADOR/FILA-PRODUCAO-V3/MIGRACAO-RECUPERACAO-RESERVA-ORFA-V9.sql`
e `ROLLBACK-RECUPERACAO-RESERVA-ORFA-V9.sql`. O rollback não apaga evidência nem
desfaz uma recuperação já registrada.

Se uma consulta de leitura ao contrato falhar momentaneamente, o painel mantém o
erro visível e tenta carregar de novo após cinco segundos. Essa tentativa é só de
leitura: não inicia, não retoma, não pausa e não recupera nenhuma linha. O snapshot
imediatamente anterior desse ajuste visual é
`4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/20260831-antes-retry-consulta-fila-v31/`.

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

## 11. Fila integral V5: histórico do preparo sequencial

> Este trecho preserva o desenho que criou snapshots em fatias antes do cálculo.
> A operação vigente é a **Esteira V6**, documentada mais abaixo: ela usa a mesma
> fotografia V5, mas começa a calcular as linhas já seladas em paralelo.

A fila integral não reutiliza o lote-piloto concluído. O piloto
`100635db-56d9-4297-b22c-6cde52bf81c8` continua como evidência: 3 cartas, 45
linhas, todas concluídas e sem publicação. A fila geral possui outro `lote_id` e
linhagem explícita em cada linha de `clube_novo.build_linha_card`.

O caminho é deliberadamente dividido em duas decisões do operador:

```text
Preparar fila integral
  -> fotografia ordenada de candidatas (overall DESC, card_id)
  -> fatias de até 10 cartas: entrada V3, gate, posições/funções por IDs, snapshot
  -> fila selada, estado "Pronto para iniciar"
  -> [decisão separada] Iniciar
  -> worker V3 calcula uma linha reservada por vez
```

Enquanto o estado for **Preparando fila** ou **Preparação pausada**, nenhuma
função matemática roda: não há chamada a `roda_lote_v6.py`, não há `b1`, nem
resultado do Otimizador. Pausar espera a fatia atômica já em curso e preserva as
demais candidatas. Somente quando todas as candidatas estiverem fotografadas e
o banco mudar para `parado` o botão passa a significar **Iniciar**.

Cada candidata guarda `card_id`, `overall`, a versão física da carta e a ordem da
fotografia. Antes de criar sua linha, a V5 compara a versão atual da carta com a
fotografia; se houver mudança, o lote falha fechado. Carta bloqueada pelo contrato
fica registrada como incompleta; carta sem posição/função canônica fica registrada
como sem linha. Nenhum dos dois casos é substituído por uma fonte antiga ou nome
textual.

As telas de Fila e Resultados consultam `otimizador_producao_fila_paginada_v5` em
blocos de no máximo 100 linhas. A UI recebe rótulos apenas de
`otimizador_cartas_apresentacao_v2` e dos catálogos existentes por ID. Isso evita
carregar a fila integral inteira no navegador e mantém o browser sem credencial.
As RPCs novas e a tabela de candidatas têm RLS, acesso direto revogado e execução
concedida exclusivamente ao backend `service_role`.

O contrato continua com `pode_publicar=false`; o Bonificador não inicia por esse
fluxo; Ímpetos condicionais seguem excluídos desde a fotografia inicial. A fórmula,
pesos, moldes, seleção de build e ordem de cálculo não são tocados pela V5.

### Como operar quando a V5 estiver aplicada

1. Dar dois cliques em `Otimizador ClubEfootball.exe`. Esse é o único ícone de
   uso diário; não use `.bat`, não abra `runtime/` e não digite endereço no navegador.
2. Conferir o selo **Motor pronto** e o pré-voo mostrado pela interface.
3. Clicar **Preparar fila integral**. A tela passa a mostrar candidatas preparadas
   e linhas já geradas; isso ainda não roda o Otimizador.
4. Se necessário, clicar **Pausar**; depois **Retomar preparação**. Não use
   **Parar** durante o preparo, pois ainda não existe execução de builds a encerrar.
5. Quando o estado chegar a **Pronto para iniciar**, conferir contagens, exclusões,
   fingerprint e uma página de linhas. Só então clicar **Iniciar** para calcular.
6. Para recuperar antes da criação do lote integral, usar o snapshot
   `4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/20260831-antes-preparo-integral-v4/` e o
   rollback V5. Depois de um lote integral existir, o rollback falha fechado: a
   recuperação deve usar snapshot aprovado, sem apagar evidência.

### Estado de liberação em 31/08/2026

A V5 está aplicada e o pré-voo foi relido no banco: 19.363 candidatas básicas,
1.169 exclusões condicionais, fórmula aprovada e publicação desligada. Um ensaio
transacional preparou uma candidata e 18 linhas e foi revertido; portanto nenhuma
fila integral foi criada nem calculada como efeito da validação. A interface V25 e
o executável foram testados contra as RPCs V5 em loopback. A ação restante é apenas
operacional: clicar **Preparar fila integral**, conferir o lote selado e, em decisão
separada, clicar **Iniciar**.

### Roteiro operacional da fila completa

O Otimizador está **pronto para preparar todas as 19.363 cartas atualmente
elegíveis**. As 1.169 cartas com Ímpeto condicional não entram nesta rodada porque
esse consumidor continua deliberadamente desligado; isso não é falha nem fallback.

1. Abra o executável e, na aba **Fila automatizada**, confirme o selo **Motor
   pronto** e o rótulo **SEM PUBLICAÇÃO**.
2. Clique **Preparar fila integral** uma única vez. A preparação cria snapshots e
   linhas por fatias, sem calcular builds. Acompanhe `Candidatas preparadas` até
   o estado **Pronto para iniciar**.
3. Confira contagens, exclusões e fingerprint. Se precisar interromper apenas a
   preparação, use **Pausar** e depois **Retomar preparação**; as candidatas já
   seladas não são perdidas.
4. Somente depois dessa conferência clique **Iniciar**. Esse é o único passo que
   calcula linhas; o resultado continua de teste, sem publicação e sem Bonificador.

O snapshot de recuperação pré-V5 e o rollback continuam indicados no item 6 acima.
O rollback falha fechado se uma fila integral já existir, para não apagar a evidência
de execução. A validação de liberação executou 48 testes e não alterou fórmula,
pesos, moldes ou regras de negócio.

### Abrir com um clique em qualquer computador — V26

Para o uso diário existe **um único ícone**: `Otimizador ClubEfootball.exe`, na raiz
da pasta `OTIMIZADOR`. Ao clicar nele, o aplicativo inicia sozinho o componente
interno `runtime/OtimizadorServico.exe`, espera a resposta local e abre a tela. O
computador de uso **não precisa ter Python instalado** e não exige abrir `.bat`,
PowerShell ou URL manualmente. A porta `8769` é interna; o usuário não precisa
conhecê-la nem operar nela.

Para levar a outro computador, copie a pasta `OTIMIZADOR` inteira, inclusive as
subpastas `interface/` e `runtime/`. A conexão é a única preparação feita uma vez:
o `config.txt` deve estar em `2-MOTORES/` ou dentro de `OTIMIZADOR/`, com URL e chave
válidas. Ele fica apenas no processo local e nunca é enviado ao navegador. Depois
disso, todo uso normal volta a ser um clique no mesmo ícone.

Se o pacote ou a configuração estiverem ausentes, o aplicativo mostra o motivo e
grava `ERRO-ABERTURA-OTIMIZADOR.txt` na pasta do Otimizador; não falha silenciosamente.
Os parágrafos de lançadores V1.x mais abaixo pertencem ao histórico e não substituem
esta abertura V26.

`RODAR-OTIMIZADOR.bat` também só abre esse mesmo ícone para compatibilidade; ele não
compila, não pede Python e não deve ser usado para instalar nada no computador de uso.

### Esteira V6 — preparar e calcular ao mesmo tempo

**Regra vigente.** A V5 permanece a fonte de fotografia e criação de linhas; a V6
apenas organiza a execução. Ao clicar uma vez em **Iniciar fila integral**, o
aplicativo liga a esteira para o mesmo `lote_id`: o preparador cria snapshots e
linhas em fatias de até 20 cartas e o Otimizador começa a calcular imediatamente
as linhas que já foram seladas. Não espera as 19.363 candidatas terminarem para
produzir a primeira build.

```text
fotografia/snapshot V5 (até 20 cartas) ──> linhas seladas ──> worker V6
             continua em paralelo                         calcula uma por vez
```

A V6 conserva o fingerprint inicial do lote durante toda a execução, para não
invalidar uma linha já reservada. Quando o preparo termina, a impressão digital
completa das linhas é gravada separadamente em `preparo_fingerprint_final`. A
fórmula aprovada, pesos, moldes, ordem de cálculo, entradas canônicas, Ímpetos
condicionais e `pode_publicar=false` não mudam. O Bonificador continua fora deste
fluxo.

**Uso diário:** dê dois cliques em `Otimizador ClubEfootball.exe` e clique uma vez
em **Iniciar fila integral**. A tela atualiza sozinha: `Candidatas preparadas` é a
fotografia em andamento; `Concluídas` é o cálculo real já feito. Se a aplicação for
fechada ou o computador reiniciar, abra o mesmo ícone e clique **Retomar**: a
esteira reaproveita o mesmo lote, os snapshots já gravados e somente as linhas
pendentes. Não recria o lote nem duplica resultado.

**Pausar** espera a operação atômica atual e mantém candidatas/linhas pendentes.
**Parar** exige confirmação e encerra a rodada sem publicação; não apaga as linhas
concluídas. O rollback V6 em
`4-DOCUMENTOS/OTIMIZADOR/FILA-PRODUCAO-V3/ROLLBACK-ESTEIRA-PREPARO-EXECUCAO-V6.sql`
recusa executar enquanto houver esteira ativa, precisamente para não interromper
uma execução ou apagar sua evidência. O snapshot anterior está em
`4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/20260831-antes-esteira-preparo-execucao-v6/`.

### Evidência de ativação e correção V7/V8 — 31/08/2026

O lote integral `ddbcbc86-1ae7-4b95-b9f0-22601f41b61d` foi preservado durante a
transição: não foi recriado. A V6 adicionou quatro RPCs privadas e o campo
`preparo_fingerprint_final`, com `anon` e `authenticated` sem execução e apenas
`service_role` autorizado. O primeiro teste real revelou uma única falha de
infraestrutura: a conclusão tentou preencher o ID de `build_otimizador`, que é
gerado pelo banco. A V7 removeu essa escrita manual; a V8 trocou o evento de
recuperação por `preparo_pausado`, que é o evento canônico permitido. Nenhuma
fórmula, peso, molde, entrada, carta, técnico, Ímpeto condicional ou regra de
negócio foi alterada.

O readback posterior confirmou a primeira execução válida: a preparação foi de
15.850 para 15.930 candidatas enquanto quatro builds foram concluídas; depois
seguiu para 16.230 candidatas e 19 builds concluídas, sem falha, com
`pode_publicar=false`. Cada build trouxe o mesmo fingerprint de fórmula aprovado,
o fingerprint de contrato e a impressão digital de resultado. Esta é a prova de
que produtor e consumidor operaram no mesmo lote em paralelo.

### Recuperação do painel local V27 — 31/08/2026

Fechar a janela visual não encerra automaticamente o serviço local: isso preserva
uma linha atômica em andamento, mas a mesma janela deve poder ser recuperada pelo
ícone. Foi encontrado e corrigido o defeito que impedia essa recuperação: o RPC
`otimizador_producao_status_v5` tem `p_lote_id uuid DEFAULT NULL`, porém a ponte
enviava um corpo vazio. O PostgREST não escolhe a sobrecarga somente pelo default;
por isso a tela recebia HTTP 500 em vez do estado da fila. A ponte V27 envia
explicitamente `{"p_lote_id": null}`. O contrato continua escolhendo o lote ativo;
a interface não consulta tabela, não guarda ID por texto e não expõe credencial.

A rota de saúde do ícone também deixou de chamar a régua completa. Ela agora é uma
sonda local de loopback, rápida e sem leitura de fórmula, fila ou banco; os gates
continuam sendo conferidos somente nas rotas próprias do painel. Assim, com o
serviço V27 já em execução, dar dois cliques novamente em
`Otimizador ClubEfootball.exe` só reabre o painel — não cria outro worker nem
retoma a fila sozinho.

Na correção, o lote `ddbcbc86-1ae7-4b95-b9f0-22601f41b61d` foi pausado pelo
controle atômico antes de reiniciar o serviço: 18.770/19.363 candidatas já
preparadas, 178.759 linhas, 109 builds concluídas, zero linha em processamento,
`falha=null` e `pode_publicar=false`. O readback V27 em `127.0.0.1:8769` devolveu
saúde imediata, o mesmo lote em `pausado` e as ações reais. Nenhuma fórmula, peso,
molde, entrada, estado de resultado ou publicação foi alterado. O snapshot anterior
está em
`4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/20260831-antes-correcao-retorno-painel-v27/`.

**Como pausar daqui em diante:** abra o mesmo ícone, clique **Pausar** e espere o
estado **Pausado** com `0 em processamento`; só então feche a janela, copie arquivos
ou troque de computador. Nunca use o Gerenciador de Tarefas como substituto de
Pausar.

### Troca segura entre computadores

Nunca faça `git push`, `git pull`, cópia de pasta ou atualização do executável
enquanto o lote estiver **Rodando**. Primeiro use **Pausar** e espere a tela mostrar
**Pausado**, com zero linhas em processamento. Os resultados já concluídos e as
linhas pendentes permanecem no banco; não é necessário recriar a fila.

Depois da pausa, publique apenas as alterações do Otimizador já revisadas e baixe
a mesma revisão no outro computador. Confirme que a pasta inteira
`2-MOTORES/OTIMIZADOR` chegou, inclusive `Otimizador ClubEfootball.exe`,
`runtime/OtimizadorServico.exe` e `interface/`; mantenha o `config.txt` local com
as credenciais daquele computador. Por fim, dê dois cliques em
`Otimizador ClubEfootball.exe` e clique **Retomar** uma vez. A retomada usa o
mesmo `lote_id`, continua somente as linhas pendentes e não duplica builds. A fila
não continua executando durante a troca de computador; ela retoma com segurança
depois desse único comando.

## 12. Histórico

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

O executável local era versão 20260831-v22 nesta etapa histórica. A versão V23
descrita abaixo exige reinicialização controlada ao encontrar servidor mais
antigo, para nunca mostrar código anterior como se fosse a fila produtiva.

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

## 14. Preparação histórica da fila produtiva V3 (31/08/2026)

Esta seção registra o estado anterior à aplicação. Ela foi superada pela seção 15;
não descreve o estado operacional atual. A
fórmula continua imutável: **barras com teto 99 -> proficiência com piso 40 e
teto 99 -> boost do técnico -> Ímpetos**. Pesos, moldes, critérios de busca e
resultado da mesma carta também não foram alterados.

O que foi preparado localmente é uma fila produtiva completa, mas **sem
publicação**. A cadeia planejada é:

`executável/Edge -> servidor somente em 127.0.0.1 -> RPCs V3 seladas -> lote e
snapshots em clube_novo -> worker local -> build_otimizador -> build_linha_card
concluída -> entrada pendente para o Bonificador`.

O navegador não recebe chave de banco e não chama Supabase. O worker é criado
somente pelo servidor loopback depois de uma ação autorizada pelo contrato. Ele
reserva uma linha de cada vez, recebe a fotografia selada da carta e da régua,
executa a mesma fórmula local e devolve o resultado com seus selos. Não há
fallback para `clube.fila`, `clube.build`, arquivos de fila, nomes/rótulos ou
projeções antigas.

### Contrato V3 preparado

Os artefatos ainda não aplicados são:

- `OTIMIZADOR/FILA-PRODUCAO-V3/MIGRACAO-FILA-PRODUCAO-V3.sql`;
- `OTIMIZADOR/FILA-PRODUCAO-V3/ROLLBACK-FILA-PRODUCAO-V3.sql`.

Quando aplicada explicitamente, a migração cria quatro registros privados em
`clube_novo`: lote, snapshot de carta, linha reservável e evento. As únicas
portas públicas de leitura/controle são RPCs V3 com `SECURITY DEFINER`,
`search_path` vazio, RLS ligado e execução somente para `service_role`. O
rollback recusa apagar qualquer coisa se já houver lote V3 criado.

A criação usa apenas cartões com gate de carta e vínculos aptos, relação canônica
`funcao_id + posicao_id`, gate do Bonificador e `overall` conhecido. A ordem é
determinística: maior overall, depois `card_id`, `funcao_id` e `posicao_id`.
Cartas com Ímpeto condicional são excluídas; esse consumidor continua desligado.
`posicao_id = 0` continua sendo o Goleiro canônico, não erro.

### Operação depois da aplicação explícita

Na aba **Fila produtiva**, o botão **Criar e iniciar** forma uma única fila
completa das cartas aptas, começando pelas mais fortes, e inicia o worker local.
**Pausar** conclui ou bloqueia a linha atômica atual e preserva as pendentes.
**Parar** pede confirmação e marca as pendentes como interrompidas, sem apagar
as concluídas e sem publicar. A conclusão do Otimizador deixa builds elegíveis
para o Bonificador, mas não o executa automaticamente; Bonificador e publicação
são passos separados.

Enquanto a migração não for aplicada, a interface V23 mostra
`Aguardando aplicação da fila V3`, deixa todos os controles desabilitados e
responde 409 às tentativas de criar/iniciar. Isso é intencional: nesta preparação
não foi criado lote, não foi iniciada linha, não foi gravado resultado e não foi
publicado nada.

### Recuperação e conferência

- Snapshot local pré-V23:
  `OTIMIZADOR/RECUPERACAO/20260831-antes-fila-producao-v23/`.
- Worker: `2-MOTORES/OTIMIZADOR/fila_producao_v3.py`.
- Teste offline do protocolo: `OTIMIZADOR/TESTES/teste_fila_producao_v3.py`.
- O executável requer servidor `20260831-v23`, impedindo que uma janela antiga
  se apresente como esta versão.

Este parágrafo é histórico. A infraestrutura e um piloto limitado foram
executados depois; o estado atual está na seção 16.

## 15. Fila produtiva V3 aplicada, sem lote — registro histórico (31/08/2026)

A infraestrutura oficial da fila produtiva V3 está aplicada em `clube_novo`. Isso
**não** criou uma fila, não processou carta, não produziu build e não iniciou o
Bonificador. O estado atual devolvido pelo contrato é `sem_lote`, com `criar=true`
e `pode_publicar=false`.

As migrações registradas são `20260831133727_otimizador_fila_producao_v3` e
`20260831134002_otimizador_fila_producao_v3_indices_v2`. Elas criam a fotografia
de lote/carta, a fila por linha e os eventos privados, além dos índices que cobrem
as FKs. A reserva física só aceita uma linha quando o lote está `rodando`; a
fórmula selada permanece
`7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad`.

O navegador continua falando somente com o servidor em `127.0.0.1`. A credencial
moderna do backend fica em `2-MOTORES/config.txt`, segue apenas no cabeçalho
`apikey` e nunca é enviada ao browser. A interface real foi validada em loopback:
saúde da régua, Fila, Eventos e Resultados retornaram contrato V3, `sem_lote`,
zero resultados e publicação desligada. O servidor temporário de validação foi
encerrado.

As quatro tabelas V3 têm RLS e nenhum acesso direto para `anon` ou
`authenticated`; as RPCs `otimizador_producao_*_v3` só têm execução por
`service_role`. O aviso do advisor sobre RLS sem política é esperado neste desenho:
as tabelas não recebem acesso direto; as portas seladas fazem toda a mediação.

Recuperação: o snapshot local é
`OTIMIZADOR/RECUPERACAO/20260831-antes-aplicacao-v3-credencial/`. Enquanto não
existe lote, `ROLLBACK-FILA-PRODUCAO-V3.sql` pode desfazer a infraestrutura; depois
de existir lote ele falha fechado para não apagar histórico. O rollback isolado dos
índices é `ROLLBACK-FILA-PRODUCAO-V3-INDICES-V2.sql`.

O próximo passo descrito nesta seção foi superado pelo piloto limitado da seção
16. Ímpetos condicionais, Bonificador e publicação continuam desligados e
independentes.

## 16. Piloto limitado V3 concluído, sem publicação (31/08/2026)

Foi criado um único lote piloto `100635db-56d9-4297-b22c-6cde52bf81c8`, limitado
a 3 cartas e 45 linhas. Ele não é uma liberação da fila completa. Depois da
primeira linha e de mais cinco, uma autorização de cobertura transversal executou
exatamente 22 linhas: as 12 pendentes da primeira carta, as 9 da segunda e uma
da terceira. A autorização seguinte concluiu as 17 restantes. O lote está
`concluido`, com 45 concluídas, nenhuma pendente, nenhuma em processamento e
nenhuma bloqueada. `pode_publicar=false`; as 45 linhas aguardam Bonificador como
etapa separada e nada foi publicado.

O piloto revelou dois defeitos de infraestrutura, corrigidos sem alterar fórmula,
pesos, moldes, cartas ou regras de negócio:

- V3.1/V3.2 aplicam o limite de um piloto antes das projeções, sem tocar no
  caminho integral; V3.3 usa o `lote_id` correto ao criar as linhas;
- V3.4 respeita que `clube_novo.build_otimizador.id` é `GENERATED ALWAYS AS
  IDENTITY`: o `INSERT` não informa a PK e recebe o ID retornado pelo banco.

O readback físico da V3.4 confirmou ausência de `nextval`, ausência de `id` no
`INSERT` e preservação dos selos. O histórico de migrações contém duas entradas
V3.4 com o mesmo conteúdo idempotente (`CREATE OR REPLACE`); não houve duplicação
de linha, build ou cálculo.

O contrato atual das três cartas foi igual aos respectivos snapshots selados. A
reexecução local de uma linha representativa de cada carta conferiu exatamente
com o resultado persistido; a primeira teve pontuação `-52,1`, técnico, barras,
habilidades, Ímpeto adicional, 11 builds comparadas e 39 possíveis. As 45 linhas
concluídas tiveram os fingerprints de fórmula, contrato, carta e resultado
conferidos. Nenhuma saída foi publicada e o Bonificador não rodou. As 1.169 cartas
com Ímpeto condicional continuam excluídas.

Recuperação: os snapshots estão em
`OTIMIZADOR/RECUPERACAO/20260831-antes-aplicacao-v3-credencial/` e
`OTIMIZADOR/RECUPERACAO/20260831-antes-piloto-limitado-v3/`. Como o lote existe,
o rollback-base V3 é fail-closed para não apagar histórico. Os rollbacks V3.1 a
V3.4 são apenas recuperação técnica e não devem ser aplicados sem decisão
explícita de retenção/arquivamento e readback.

O próximo passo **não é rodar todas as cartas**: requer paridade independente
suficiente e autorização explícita para criar uma fila integral. O navegador
continua somente em loopback; a credencial fica no backend, nunca no browser.

## 17. Ordem visual mais recente primeiro — V32 (31/08/2026)

Esta alteração é somente de apresentação. A aba **Fila integral** e a aba
**Resultados** mostram primeiro as linhas mais recentes; os botões de página
passaram a se chamar **Mais recentes** e **Mais antigas**. A primeira página
visual corresponde ao fim da paginação canônica e as páginas seguintes seguem
para linhas mais antigas.

O banco, a ordem real de execução (`ordem_fila` crescente), a fórmula, pesos,
moldes, gates, estados, publicação e o worker não foram alterados. O servidor
local usa o total devolvido pelo contrato V5 para pedir o intervalo canônico
equivalente e inverte somente a resposta enviada à tela. Se o total mudar entre
as duas leituras, ele faz no máximo uma releitura de alinhamento; não há fallback
para tabela legada nem mudança da ordem da fila.

Snapshot recuperável: `OTIMIZADOR/RECUPERACAO/20260831-antes-ordem-recentes-v32/`.
O executável foi elevado a interface `20260831-v32` / arquivo `1.6.1.0`, e a
saúde, HTML e JavaScript V32 foram conferidos em loopback. O teste offline cobre
as páginas visuais `5,4`, depois `3,2`, depois `1`, preservando a paginação
canônica crescente no contrato.

Na data deste registro, a consulta real do lote integral com 184.702 linhas foi
recusada pelo banco com `57014: statement timeout` no contrato
`otimizador_producao_status_v5`. Portanto, a ordenação V32 está pronta, mas não
deve ser considerada validada sobre esse lote enquanto a consulta de status não
for otimizada e retestada. Isto é um bloqueio de desempenho do contrato, não uma
alteração de fórmula ou resultado.

## 18. Produto portátil e recuperação automática — V38 (31/08/2026)

Esta é a regra operacional atual para abrir o Otimizador em um PC Windows
compatível. Ela substitui qualquer instrução antiga que peça para abrir `.bat`,
PowerShell, URL local ou o executável dentro de `runtime/`.

### Um ícone, sem terminal

O único arquivo que o operador abre é:

`2-MOTORES/OTIMIZADOR/Otimizador ClubEfootball.exe`

No primeiro clique ele mostra imediatamente **Abrindo o Otimizador**, inicia em
segundo plano `runtime/OtimizadorServico.exe`, espera a saúde local e abre o painel.
Não requer Python instalado no computador de operação. Fechar a janela do painel só
fecha a visualização; o ícone perto do relógio continua responsável por reabri-la e
por informar se há worker local.

Um segundo clique durante a abertura não cria serviço duplicado nem pede outro
clique: espera até 15 segundos pelo primeiro processo e abre o painel quando ele
responder. Ao encontrar na porta interna uma cópia anterior do próprio Otimizador
com `worker_ativo=false`, o lançador a substitui automaticamente. Um worker ativo
nunca é encerrado por essa troca.

### Levar para outro computador

Copie/baixe o checkout com a pasta **OTIMIZADOR inteira**, principalmente:

- `Otimizador ClubEfootball.exe`;
- `runtime/`, inclusive `runtime/_internal/`;
- `interface/`.

Não copie somente o `.exe`. O runtime portátil usa vários arquivos ao lado dele.
Na primeira abertura de uma cópia que ainda não tiver conexão, o próprio aplicativo
mostra a janela **Configurar conexão do Otimizador**. Basta colar uma vez a URL
`https://...` e a chave privada do aplicativo; ele grava `OTIMIZADOR/config.txt`
somente naquela máquina. Esse arquivo é ignorado pelo Git, não entra no navegador e
nunca deve ser enviado para GitHub. Nas aberturas seguintes, volta a ser apenas um
clique no mesmo ícone.

### Quando o banco oscila

O painel não chama mais a falha remota de “rodando”. Se o contrato privado em
`clube_novo` estiver indisponível, ele mostra **Reconectando ao banco**, desabilita
todos os controles e não inicia, retoma, pausa ou para nenhuma linha. A primeira
falha abre um circuito local de 30 segundos: abas, cliques e atualizações não
repetem a mesma RPC contra o banco durante essa janela. A página tenta de novo de
forma espaçada (5, 10, 20, 40 e 60 segundos).

Isso é uma proteção de produto, não um fallback de dados: a interface não inventa
estado de fila, não lê legado e não usa cache para autorizar trabalho. Quando o
contrato voltar, a próxima leitura confirmada reabilita apenas as ações que ele
selar.

No momento deste registro, o Data API remoto respondeu `503`/timeout também para
`otimizador_producao_status_v5`; portanto o aplicativo abre e se recupera sozinho,
mas nenhuma linha deve ser iniciada até que o serviço remoto volte a responder. Não
é seguro tentar compensar esse estado com repetição de cliques ou com execução
manual de lote.

### Prova e recuperação

- snapshot anterior: `4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/20260831-produto-portatil-v37-antes/`;
- checklist desta entrega: `4-DOCUMENTOS/OTIMIZADOR/CHECKLIST-ESTABILIDADE-PRODUTO-V38.md`;
- executável V38: arquivo `1.6.7.0`, interface `20260831-v38`;
- validação controlada: abertura do ícone em **3,993 s**, sem worker ativo;
- sob indisponibilidade real: o RPC fica limitado a 5 s; a leitura completa medida
  foi **5,110 s** e foi devolvida fail-closed; a segunda resposta local saiu em
  **2 ms**, com zero controles habilitados;
- `teste_interface_local_otimizador.py`: 17/17 testes verdes, além de sintaxe
  Python e JavaScript válidas.

Nenhum item desta seção altera fórmula, pesos, moldes, regras de negócio, banco,
linhas, resultados, publicação ou a política de Ímpetos condicionais.

## 19. Fila operacional acompanhável e abertura V40 (31/08/2026)

Esta é a regra atual da tela **Fila integral**. Ela substitui a apresentação V32
que colocava as linhas mais recentes no alto e dificultava ver o que ainda seria
calculado.

### Ordem que aparece na tela

A primeira página da aba **Fila integral** é uma fila de trabalho, e não um
histórico:

1. uma linha em processamento, se existir;
2. as pendentes, em `ordem_fila` canônica crescente — a próxima a rodar aparece
   no topo;
3. as linhas já concluídas, bloqueadas, falhas ou interrompidas, somente depois
   das abertas.

Assim que uma linha termina, ela deixa a cabeça de trabalho e fica no fim da
fila. A aba **Resultados** continua sendo o histórico: mostra somente estados
finais, com os mais recentes primeiro. Esta é apenas uma troca de leitura e
apresentação; não altera reserva, prioridade real, fórmula, pesos, moldes,
gates, publicação ou qualquer resultado do Otimizador.

O contrato de leitura que garante isso é
`otimizador_producao_fila_operacional_v3`. A primeira página verificada do lote
ativo devolveu as ordens **246, 247, 248, 249 e 250**, todas pendentes; a primeira
página de Resultados devolveu **245, 244, 243, 242 e 241**, todas finalizadas. A
interface exibe explicitamente `próximas primeiro; concluídas por último` para
evitar ambiguidade.

### Abertura e leitura rápida

O único ícone continua sendo
`2-MOTORES/OTIMIZADOR/Otimizador ClubEfootball.exe`. O lançador V40 verifica a
saúde local e abre `runtime/OtimizadorServico.exe` em segundo plano. A Fila não
espera o catálogo pesado de técnicos/régua: ela lê primeiro apenas os rótulos
canônicos leves de função e posição por ID. O catálogo completo só é solicitado
quando se abre **Testar uma carta** ou o detalhe de um Resultado.

Para evitar que uma oscilação do Data API faça a tela parar por timeout, o
servidor local pode usar a ponte privada restrita
`otimizador_portal_local_v3`, configurada somente no computador. Ela aceita uma
lista fechada de contratos de leitura do Otimizador e não expõe tabelas,
credenciais ou acesso ao banco para o navegador. Sem uma leitura confirmada, a
interface falha fechada e não habilita controles de fila.

As migrações de recuperação desta entrega são
`MIGRACAO-PONTE-LOCAL-PRIVADA-V13.sql` e
`MIGRACAO-PAINEL-RAPIDO-V16.sql`, cada uma com o rollback correspondente. A V16
substitui a tentativa intermediária V14 para a paginação de Resultados; a V15
ficou apenas como arquivo histórico e **não foi aplicada**. O snapshot anterior
está em `4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/20260831-v40-ponte-privada-antes/`.

### Prova controlada desta versão

Sem iniciar worker, preparar lote, reservar, calcular ou escrever linha, foram
confirmados:

- 20/20 testes da interface e o teste da fórmula aprovada: Messi 99 + Capello
  +1 + Precisão +4 = **104**;
- serviço portátil V40: saúde local, leitura do banco, ordem operacional e
  Resultados responderam corretamente;
- ícone oficial V40: abriu o serviço em loopback, declarou
  `worker_ativo=false`, conectou ao banco e devolveu as cinco próximas linhas
  pendentes acima;
- o processo usado exclusivamente para a prova foi encerrado ao final.

O checklist correspondente é
`4-DOCUMENTOS/OTIMIZADOR/CHECKLIST-ESTABILIDADE-PRODUTO-V40.md`.

## 20. Leitura da Fila integral estável — V41 (31/08/2026)

Esta versão conclui a correção de produto da tela **Fila integral**: ela abre pelo
único ícone do Otimizador e mostra primeiro as linhas que ainda serão calculadas.
Uma linha concluída sai da cabeça operacional e fica depois das abertas; a aba
**Resultados** permanece sendo o histórico, em ordem de término mais recente
primeiro.

### De onde vêm os dados

Os dados continuam no modelo operacional **`clube_novo`**. O schema `public` não
é uma cópia, fonte alternativa nem tabela de jogo: ele abriga somente a porta
restrita de RPC que o servidor local usa para pedir dados permitidos. O navegador
fala apenas com `127.0.0.1` e nunca recebe uma credencial ou acesso direto ao
banco.

Para os nomes da tabela de Fila, a V17 adicionou o contrato mínimo
`otimizador_rotulos_cartas_fila_v1`. Ele lê somente `clube_novo.carta_jogo` por
`card_id` e devolve apenas `card_id` e nome oficial. A ponte local V4 aceita esse
contrato em allowlist; acesso anônimo foi revogado. O readback de segurança
confirmou, entre outros, `52781926899717 · Gerard Moreno` e
`8538111 · Welington Pauletto`. Não existe fallback para `clube`, tabela legada
ou nome inventado.

Função e posição seguem sendo resolvidas pelos IDs canônicos através de
`otimizador_rotulos_fila_v1`. A tabela normal não carrega o catálogo amplo de
técnicos/régua/habilidades para desenhar as próximas linhas; esses detalhes só
são necessários no Resultado ou no detalhe de uma build campeã.

### Prova real do executável

Com o lote preservado, sem iniciar worker, preparador, reserva, cálculo ou
publicação, a versão `20260831-v41` foi verificada duas vezes:

- serviço portátil em porta isolada: a primeira página completa de 100 linhas
  respondeu sem timeout; mostrou as ordens 246 a 345, todas pendentes;
- o ícone oficial `2-MOTORES/OTIMIZADOR/Otimizador ClubEfootball.exe` abriu a
  mesma versão na porta normal, sem worker/preparador, e devolveu as 100 próximas
  linhas sem timeout; a primeira leitura fria final levou 13,412 s e as três
  leituras seguintes levaram 190 ms, 82 ms e 45 ms;
- a primeira linha foi `246 · 52781926899717 · Gerard Moreno` e a última foi
  `345 · 52847425204350 · Kylian Mbappé`;
- Eventos (100) e Resultados (100) também responderam pela instância aberta pelo
  ícone, sem expor credencial.

Isso prova a leitura e a apresentação. Não é uma autorização para disparar um
lote nem uma alteração da fórmula. A fórmula aprovada foi testada de novo:
Messi 99 + Capello +1 + Precisão +4 = **104**.

### Recuperação e distribuição

- snapshot anterior à V17:
  `4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/20260831-v41-rotulos-carta-antes/`;
- migração e rollback: `OTIMIZADOR/FILA-PRODUCAO-V3/MIGRACAO-ROTULOS-CARTAS-RAPIDOS-V17.sql`
  e `ROLLBACK-ROTULOS-CARTAS-RAPIDOS-V17.sql`;
- checklist desta entrega:
  `4-DOCUMENTOS/OTIMIZADOR/CHECKLIST-ESTABILIDADE-PRODUTO-V41.md`.

Em outro computador, copie a pasta **OTIMIZADOR inteira**, incluindo
`runtime/_internal/`, e abra somente `Otimizador ClubEfootball.exe`. Não abra o
executável de `runtime/` diretamente e não copie apenas o arquivo `.exe` do
ícone. A configuração local continua fora do Git e fora do navegador.

O arquivo de abertura V41 tem versão de arquivo `1.7.0.0` e mutex próprio V41.
Assim, se houver uma bandeja V40 ociosa em outro computador, o novo ícone chega
à checagem segura da porta e a substitui; se houver worker ativo, a proteção
permanece e o novo aplicativo não o encerra.

O aviso curto **Abrindo o Otimizador** fecha assim que o painel é solicitado. A
bandeja continua viva em segundo plano, mas o aviso não pode mais permanecer
sobre a tela do painel durante a sessão.

Se a tela disser **Rodando**, mas também disser **nenhum worker local**, isso
significa que o lote selado está em estado Rodando no banco e este computador
ainda não reassumiu o cálculo. Não é seguro retomar automaticamente só porque o
painel foi aberto. O botão **Retomar worker local** é a ação explícita que
continua somente as pendências, sem duplicar linha; abrir ou fechar o painel não
aciona essa ação por conta própria.
