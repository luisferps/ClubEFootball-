# Manual do Otimizador — ClubEfootball

**Versão 1.5 · 28/08/2026**

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

As portas de **entrada** atuais do lote e da cópia local do serviço são:

- `otimizador_carta_v1` e `otimizador_cartas_v1`, para cartas e relações por IDs;
- `otimizador_regua_v1`, para moldes, regras operacionais e técnicos;
- `otimizador_pool_habilidades_v1`, por `skill_id + funcao_id`;
- `otimizador_proxima_fila_v1`, que traduz a fila operacional para `funcao_id`;
- `otimizador_peso_ordem_v1`, para o estado operacional da ordem.

Todas são `SECURITY DEFINER`, têm `search_path=''`, usam nomes de objeto totalmente
qualificados e podem ser executadas somente por `service_role`. A UI não acessa
`clube_novo` diretamente. As portas históricas de leitura permanecem apenas para os
comparadores independentes; não há fallback silencioso no caminho migrado.
`gravar_build` continua sendo uma porta de **saída** e não foi executada nesta
migração.

### Estado da migração de entradas

O lote local e a cópia local do serviço foram migrados para o contrato v1. Os dados
de carta, atributos, corpo, posições, habilidades, estilo IA, identidades físicas,
dimensões e técnicos chegam por IDs estáveis/FKs. Nome ou texto só é anexado depois,
para apresentação e diagnóstico. A prova de renomeação confirma que trocar todos os
rótulos não muda vínculos, cálculo ou seleção dos 19 moldes.

Ímpetos, condições e faixas continuam desligados: o contrato devolve catálogo ativo
vazio e recusa cartas afetadas pelo gate, sem tratá-las como efeito incondicional.
Tipos 4/0 e 7/0 continuam provisórios. `motor_bonus.py` continua separado e não foi
ativado.

As três réplicas de tela ainda **não estão migradas**. Elas conservam catálogos
embutidos e não há prova de qual serviço está efetivamente publicado; o próprio
diretório local do Railway informa que não representa necessariamente a implantação
atual. Migrá-las exige primeiro um endpoint seguro implantado que entregue os IDs
canônicos. Até isso existir, elas foram preservadas byte a byte, sem expor chave
privada nem reimplementar a regra por nomes.

### A cadeia completa, em linguagem de jogo

Quando alguém roda **RODAR O MOTOR**, o lote pede ao banco quais pares de carta e
função estão na fila. Cada par chega como `card_id + funcao_id`. Em seguida ele pede
a ficha da carta: os 26 atributos, posições, corpo, habilidades, técnico e travas.
Esses itens chegam pelo contrato v1 a partir de `clube_novo`, sempre com IDs ou bits
físicos. Só depois o Otimizador dá um nome legível ao resultado para mostrar no log
ou na ficha.

```text
RODAR-O-MOTOR.bat / RODAR-TUDO.bat
  -> OTIMIZADOR/roda_lote_v6.py -> fonte_unica.py -> RPCs otimizador_*_v1
  -> equacao.py + regua.py + motor.py + travas.py -> resultado de build
```

`fonte_unica.py` é o porteiro: se a RPC nova não responder ou algum gate recusar a
carta, ele para. Não volta para JSON, HTML ou RPC histórica. `equacao.py`, `regua.py`
e `motor.py` recebem vetores e IDs já resolvidos; os nomes de atributos, técnicos e
habilidades não decidem vínculo algum. `travas.py` faz a carta incompleta falhar
fechada. A rotina manual `CONFERIR-UMA-LINHA.bat` usa a mesma porta nova.

O serviço local tem outra porta de entrada, mas a mesma origem:

```text
Procfile: gunicorn app:app
  -> app.py -> banco.py -> RPCs otimizador_*_v1
  -> monta_regua.py + regua_do_banco.py -> avaliador.py + otimizador.py
```

Ele aceita `card_id`, `funcao_id`, `tecnico_id`, `skill_ids` e barras. Assim, a
interface nunca deve mandar “Capello”, “centroavante móvel” ou o nome de uma
habilidade como chave de cálculo. Ímpeto escolhido, nome de ímpeto e condição são
recusados enquanto o gate de Ímpetos estiver desligado.

Há três cuidados importantes nesta fotografia:

- `gravar_build` ainda grava a **saída** na estrutura histórica de build/fila. Há
  uma tradução de `funcao_id` para o código técnico legado somente na borda de
  gravação. Ela não entra de volta no cálculo e não autoriza tabela histórica como
  entrada nova.
- `grava_direto.py` é carregado pelo lote, mas não recebe payload na rota atual;
  permanece como escritor histórico alternativo e não pode ser religado como fallback.
- `servidor.py` e `motor-no-servidor.js` existem no repositório, mas não são a rota
  alcançada: o `Procfile` sobe `app.py` e o `index.html` não carrega o adaptador.
  Esse adaptador antigo usa formato incompatível e não prova uma integração.

### O que a tela ainda faz e por que isso bloqueia a conclusão

A tela operacional carrega `motor-e-ficha-base.js`, `ficha-ajustes.js`,
`dados-e-catalogos.js`, `elenco.js`, `modulos-elenco-paginas.js` e
`arows-sob-demanda.js`. Ela consulta as projeções públicas históricas `casa_lista`,
`casa_arows` e `bonus_posicao` e também conserva catálogos e cálculos embutidos. A
cópia publicada e o HTML único repetem essa mesma situação.

Portanto, **lote local e serviço local já recebem as entradas novas por IDs; a UI não**.
Não é aceitável entregar a chave privada à tela, acessar `clube_novo` diretamente ou
adivinhar IDs a partir de rótulos. Antes de qualquer troca da tela, é preciso provar
qual serviço está implantado e publicar um contrato seguro que transporte os mesmos
IDs. A fórmula de navegador não será alterada por essa troca de endereço.

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
origem antiga, contrato v1, IDs, cardinalidades, fingerprints, gates e a saída da
tela quando ela for afetada. Um rótulo renomeado não pode mudar a seleção. O rollback
restaura apenas o adaptador daquele elo a partir do snapshot da etapa; nunca repõe
um arquivo inteiro nem muda a fórmula.

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

## 12. Aplicativo local do Otimizador

Para abrir sem depender da interface web antiga, dê dois cliques em
`2-MOTORES/OTIMIZADOR/Otimizador ClubEfootball.exe`. Se o arquivo ainda não existir,
use uma vez `RODAR-OTIMIZADOR.bat`; ele compila o mesmo executável e o abre. O ícone
inicia um pequeno servidor privado em `127.0.0.1` e abre uma única janela de app no
navegador. A chave fica no `2-MOTORES/config.txt` compartilhado e nunca é entregue à
página.

Uso: informe o `card_id`, escolha a função e o técnico; clique **Simular**. A tela
mostra os IDs/entradas, barras e resultado, gates, cardinalidades e proveniência.
**Validar paridade** compara a função legível da equação aprovada contra o cálculo
inline do próprio Otimizador para a mesma simulação. A aplicação só permite as RPCs
`otimizador_regua_v1` e `otimizador_carta_v1`; não possui rota POST, lote, fila,
`gravar_build`, acesso direto a schema ou consumidor de Ímpetos condicionais.

Arquivos da aplicação: `interface/servidor.py`, `interface/index.html`,
`interface/app.js`, `interface/style.css`, `windows-app/ClubEfootballOtimizadorLauncher.cs`
e `windows-app/COMPILAR-APLICATIVO.ps1`. O snapshot imediatamente anterior está em
`4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/2026-08-28-ANTES-EXECUTAVEL-LOCAL/`; rollback
remove apenas esses arquivos novos e restaura os itens daquele ZIP, sem tocar em
fórmulas, banco, UI geral, Extrator ou Bonificador.

Prova operacional de gate: a consulta local de Messi `89138556575063` com função
`2` e Capello `17601312850052` foi recusada com
`impetos_consumidor_desligado`. A tela apresenta essa recusa; não tenta retirar o
Ímpeto, consultar legado ou gravar uma build para produzir uma resposta.

A validação isolada positiva também foi concluída em 28/08/2026 com Axel Witsel
`105553384739779`, função Volante de construção `16` e Antonio Conte
`17609097478250`. A consulta online terminou com 26 atributos, nota `-441.5` e
gasto `56`; a paridade entre a equação legível e o cálculo inline fechou com o mesmo
SHA-256 `8486821d2c61bf9aed093f493c545450a10e3620f2a7e59210e2ba56f5254a3e`.
O relatório completo está em
`4-DOCUMENTOS/OTIMIZADOR/VALIDACAO-ISOLADA-EXECUTAVEL-2026-08-28.md`.
