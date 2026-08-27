# MANUAL TÉCNICO DO CLUBEFOOTBALL

**Atualizado em 27/08/2026.** Este documento tem três partes: **A — como está**,
**B — como vai ficar**, **C — o que mudou e quando**. O que fica pronto sai da B e
entra na A.

---

# PARTE A — COMO ESTÁ HOJE

## A.1 · O caminho do dado (atualizado 27/08 — nao existe mais arquivo no meio)

```
C:\ProgramData\KONAMI\eFootball\ST\Download\dt870_console_win.cpk
        |
  Extrator-ClubEfootball.html   (navegador do Luis, nada sai do PC)
        |
  CSV de 29 colunas  ->  import  ->  clube.carta_jogo      O CADASTRO
        |                                    |
        |                         gatilhos: cap_do_id + carta_entrou
        |                                    v
        |                              clube.fila
        |                                    |
        +--- o MOTOR (maquina do Luis, so com ordem dele) ---+
                     le:  carta_do_motor · regua_pacote · regua_bonus
                   grava: gravar_build · gravar_bonus
                                     |
                              clube.build
                                     |
                          public.casa_tela -> a tela
```

⛔ **O Alimentador saiu** (26/08) e **os arquivos de trabalho do motor saíram** (27/08).
Não existe mais `base_unica.json`, `fila_v6.json`, `linhas.jsonl`, `bonus.jsonl`,
`molde.json`, `tecnicos.json`, `insumos_bonus.json`, `FONTE-UNICA.txt` nem
`GRAVA-DIRETO.txt`. **O motor não tem interruptor: roda e funciona.**

## A.2 · A trava da entrada (reescrita 26/08)

Com a fonte virando o arquivo do jogo, a carga é **apaga-e-coloca**: o jogo é a verdade
para o que ele carrega. Sobra **uma** trava, e ela continua valendo:

**O que o dono pôs à mão não se toca.** Campo listado em `clube.valor_do_dono` não é
sobrescrito por carga nenhuma. Parte do dado veio do Luis, não da fonte.

E há dado que o arquivo do jogo **não tem** e continua vindo de fora:
`tier` · `votos` · `max_ovr` · `data_lancamento` (esta dá pra derivar da `clube.extracao`:
é a primeira extração em que o `card_id` apareceu).

## A.3 · A conta (a cadeia da equação, imutável)

```
base + barras   (= a REFERÊNCIA da habilidade)
   × multiplicador     (incremento truncado, piso 40, teto 99)
   + 1 do técnico      (passa de 99)
   + ímpetos NATIVO e ADICIONADO juntos   (passam de 99)
   + ceil(referência × pct/100 + flat)    (habilidade, SEM trava)
```

- **Régua:** 9 degraus `[1, 0.88, 0.76, 0.64, 0.52, 0.4, 0.28, 0.16, 0.04]`, punição com
  teto 9, incremento `0.25 × peso / 12`, peso 1 (acessório) não pune.
- **Regra da metade:** a comum vencedora entra inteira, cada perdedora × 0.5 (sem
  arredondar, sem cascata); as raras somam inteiras por cima.
- **A nota é o `b1`** (+ `bonus.b_total`). As colunas `nota`, `b1n`, `b2`, `b4`, `b5`,
  `b4r` da `builds` são legado 100% NULL.

## A.4 · As chaves

- **Função** é chaveada por `codigo`, nunca por nome. `rotulo` é etiqueta e muda.
- **Posição** é chaveada por `codigo` (13): GO · ZC · LD · LE · VOL · MLG · MLD · MLE ·
  MAT · PTD · PTE · SA · CA. Siglas velhas só em `sigla_antiga`; traduza com
  `clube.pos('MC')`.
- **`card_id` é composto:** `(variante << 18) | player_id do jogo`. Portanto
  `player_id = card_id & 262143` — `clube.player_id(card_id)`. Provado: 919 de 919 com
  nome idêntico, e a parte baixa dos 2.705 ids longos cai toda na faixa dos curtos.
  As 3.269 cartas são **1.182 jogadores distintos**.

## A.5 · O que a tela lê

| view | o que entrega | para quê |
|---|---|---|
| `public.casa_lista` | a linha **sem** `arows` e **sem** `falta` | a lista |
| `public.casa_tela` | a linha inteira | a ficha de **um** card |
| `public.casa_arows` | `arows` + `falta` por card | sob demanda, quando abre a ficha |

Medido: 1.000 linhas — `casa_tela` 2.765 KB / 2.972 ms; `casa_lista` 1.718 KB / 1.160 ms.
No total, 44 MB de JSON viram 29 MB.

O `arows-sob-demanda.js` instala `arows` e `falta` como *getter*: só vão ao banco
quando alguém abre o card. Nenhuma das 193 funções da tela foi tocada.

## A.6 · Auditoria

`select * from clube.auditoria_completa() where status <> 'OK'`

| status | o que fazer |
|---|---|
| `OK` | seguir |
| `FALHA` | ⛔ **PARAR.** Divergência não investigada |
| `CONHECIDA` | seguir, citando o veredicto em `clube.divergencia_conhecida` |

Nunca mudar o esperado para o teste passar. Nunca relatar "pronto" com FALHA aberta.

## A.7 · A FONTE = CÓDIGO DO JOGO (atualizado 27/08 — carga completa)

O extrator (`7-VARREDURA-DO-JOGO\Extrator-ClubEfootball.html`) lê o `.cpk` no navegador
(decifra WESYS+CPK localmente, nada sai do PC) e entrega **42.803 cartas, 29 colunas**.

**A pasta certa** — a que o jogo atualiza toda semana:
```
C:\ProgramData\KONAMI\eFootball\ST\Download\dt870_console_win.cpk
```
⛔ **NÃO é a pasta do Steam.** A do Steam está velha. Esta é a Live Update.

**Os arquivos de dentro que a gente usa:**
```
Player.bin ................ 17.122.400 bytes → 42.806 cartas, registro de 400 bytes
PlayerAppearance.bin ....... 2.739.584 → o CORPO (registro de 64 bytes, card_id no offset 0)
PlayerVariationDetail.bin .. 2.246.160 → a BOX (registro de 168 bytes)
```

**As 29 colunas:**
`card_id · tipo · overall · roda_motor · nome · posicao · slot_ofensivo_id ·
slot_ofensivo_confirmado · slot_defensivo_id · slot_defensivo_confirmado · pe · altura ·
peso · idade · nacionalidade · pe_ruim_uso · pe_ruim_precisao · resistencia_lesao · forma ·
impeto_s1 · impeto_s2_cond · vaga_s1 · vaga_s2 · box · atributos · habilidades · aptidoes ·
estilos_ia · corpo`

**Onde mora cada coisa no registro:**
```
atributos ........ ABILITIES do editor, largura 6, valor +40
altura ........... bit 248 w8 +100      peso ..... bit 280 w7 +30
idade ............ bit 536 w6 +10       posicao .. bit 556 w4
nacionalidade .... bit 328 w10          pe ....... bit 654 w1
pe ruim uso ...... bit 478 w2           precisao . bit 578 w2
resistencia ...... bits 542 e 543       forma .... bit 582 w2
habilidades ...... 65 bits individuais  aptidoes . 12 campos de 2 bits
estilos de IA .... 7 bits individuais
impeto slot 1 .... bit 308 w8           slot 2 cond ... bit 288 w8   (136 = vaga livre)
nome latino ...... campo 3 da regiao de nomes (byte 88, stride 61)
corpo ............ PlayerAppearance.bin, appearance_cat_body
```

- `overall` é **calculado** dos atributos — o jogo não guarda. 94% ±1, correlação 0,98-0,99.
- `tipo`: **base** (id < 2^18, genérico sem arte) · **colecionavel** · **teste** (26 atributos em 99).
- `aptidoes`: 0 = apagada · 1 = meio acesa · 2 = pode ser comprada. **São as posições
  secundárias** — é delas que a fila tira as funções extras.
- **O extrator grava só o ID do estilo, nunca o nome.** O nome vem do catálogo por join.

## A.7.1 · LEVEL CAP E ORÇAMENTO — derivados do card_id (achado 27/08)

O tipo da carta está codificado **dentro do próprio card_id**:

```
grupo_id = (card_id >> 38) & 255
```

Achado caçando no `Player.bin`: **bit 102, largura 8** separa cresce/não-cresce com
**98,12% de acerto** contra 2.923 cartas de gabarito. Bits 64-127 são o card_id — então
é conta, não leitura de arquivo.

```
grupos 71 · 192 · 196 · 200 · 204  →  NÃO CRESCEM (cap 1, orçamento 0)   935 cartas, 934 acertos
grupos 0 · 64 · 68 · 128 · 129 · 132 → CRESCEM (cap 29 a 35)           2.309 cartas, 2.150 acertos
```

`orcamento = (level_cap − 1) × 2` — a fórmula do jogo, confirmada no `monta_fila.py`.

⚠️ **Carta com orçamento 0 CONTINUA na fila.** Ela não ganha barra, mas o motor ainda
escolhe ímpeto, técnico e habilidades — e nessas cartas isso é tudo que elas têm.

**O cap real vence sempre o estimado.** Hoje: 3.243 reais (do efHUB) · 39.560 estimados,
marcados `cap_estimado = true`. O gatilho `cap_do_id` preenche sozinho a cada carga.

⛔ **Onde o level cap NÃO está** (medido em 27/08, para ninguém procurar de novo):
`Player.bin` · `PlayerVariationDetail.bin` · `PlayerVariationPrSkill.bin` · os 12 cpk ·
a camada Unreal (`.utoc` com índice AES) · o mapa do editor oficial.

## A.8 · OS DOIS CAMPOS DE ESTILO (reescrito 26/08 — a versão anterior estava errada)

No `Player.bin` são **dois campos em endereços diferentes**, sem nome. O jogo não chama
nenhum dos dois de "ofensivo" ou "defensivo".

```
campo A  →  bit 372, largura 8   (valores múltiplos de 4: 0, 4, 8 ... 88)
campo B  →  bit 440, largura 6   (valores 0 a 33 — máximo aritmético 63)
```

Confirmado na tela do jogo pelo Luis: **campo A = slot ofensivo · campo B = slot defensivo.**

**Os dois campos têm catálogos INDEPENDENTES.**
⛔ A conversão `A = B × 4` **NÃO é regra** — é coincidência de numeração. O Casillas
(`88045755827028`) a quebra: A=64 é *Goleiro adiantado*, B=16 é *Goleiro ofensivo*, e são
estilos diferentes na tela.

⚠️ O campo A é o **slot legado** e sempre teve estilo defensivo dentro dele —
*Goleiro defensivo*, *Lateral defensivo*, *O destruidor* moram lá legitimamente.
Ver goleiro com "Goleiro defensivo" no slot ofensivo **não é erro**.

**Distribuição medida nas 42.803:**
```
só campo A ........ 34.264      os dois ...... 48
só campo B .........  5.011      nenhum ....... 3.480
```

**Catálogos** (ficam os dois, não são duplicatas — é onde moram os ids):
`clube.estilo_jogo` = campo A · `clube.estilo_defensivo` = campo B.

**Trava no banco:** campo B só aceita 0–63; campo A, 0–255. Foi assim que 959 cartas com
id impossível (64 e 68 num campo de 6 bits) foram pegas e corrigidas.

## A.9 · A ESTRUTURA — o que segura o quê (atualizado 27/08)

**O sistema inteiro pendura em duas tabelas.** O site faz **duas** chamadas ao banco:
`/rest/v1/casa_tela` e `/rest/v1/bonus_posicao`. E a `casa_tela` é view de
`clube.build` + `clube.funcao`. Mais nada.

```
clube.carta_jogo          ← O CADASTRO. 42.803 cartas, chave card_id
        ↓  gatilho carta_entrou
clube.fila                ← 125.932 linhas · 6,04 funcoes por carta
        ↓  proxima_da_fila()
     O MOTOR              ← carta_do_motor() + regua_pacote() + regua_bonus()
        ↓  gravar_build()  (grava E TIRA a linha da fila)
clube.build               ← nota_final = b1 + b_total, calculada pelo banco
        ↓
public.casa_tela          ← a view que a tela le
```

**As portas do motor** (nenhum arquivo, tudo no banco):

| porta | o que entrega | substituiu |
|---|---|---|
| `fila_do_motor(limite, modo)` | a fila · modo `tudo`/`faltantes`/`recalcular` | `fila_v6.json` |
| `proxima_da_fila(limite)` | o próximo lote, na ordem | — |
| `carta_do_motor(card_id)` | a carta inteira, os dois slots pelo nome | `base_unica.json` |
| `regua_pacote()` | molde, régua, atributos, barras, técnicos, ímpetos | 10 arquivos JSON |
| `regua_bonus()` | bloqueios, corpo, a regra dos dois estilos | `insumos_bonus.json` |
| `gravar_build(json)` | a volta do otimizador | `linhas.jsonl` + `grava_direto` |
| `gravar_bonus(json)` | a volta do bônus | `bonus.jsonl` + `public.bonus` |
| `estado_da_fila()` | o painel | — |

**A ORDEM DA FILA** (decisão do Luis, 27/08):
```
prioridade 0  →  as que JA RODARAM antes   ← primeiro, para conferir a migracao
prioridade 1  →  lancamento (fura a fila)
prioridade 5  →  o resto, por overall desc
```
*"Se estiver errado, a gente para nas primeiras."* Compara-se o `b1` novo com o
`clube.build_arquivo_2608`, que é a fotografia das 17.798 builds antigas.

**A REGRA DA FILA** — de onde saem as funções de cada carta, lida no `monta_fila.py` e
no `funcao_nativa.py`: a carta disputa **as DUAS funções da família** (`clube.regra_funcao`)
de **CADA posição que ela joga** — nativa + aptidões. `SA` não tem família própria: o
estilo decide se vai para a casa do `MAT` ou do `CA` (`clube.sa_familia`, chaveada por id).
**Falso nove** = `CA` + estilo *Atacante pivô* (52).

**O que é AUTOMÁTICO** (ninguém aperta nada):
- `carta_entrou` — carta nova entra → a fila se enche. Carta que mudou → a build velha é
  apagada e ela volta pra fila. Lançamento fura a fila.
- `cap_do_id` — deriva `grupo_id`, `level_cap` e `orcamento` do card_id.
- `gravar_build()` — tira a linha da fila no mesmo comando em que grava.

⛔ **NUNCA APAGAR:** `clube.build` · `clube.funcao` · `clube.carta_jogo` · `clube.fila` ·
`public.casa_tela` · `casa_lista` · `casa_arows` · `bonus_posicao` · as 8 RPCs ·
`clube.estilo_jogo` · `clube.estilo_defensivo` · `clube.regra_funcao` · `clube.sa_familia`.

# PARTE B — COMO VAI FICAR

## B.1 · A conta sai do navegador (etapas 10 e 11 são a mesma obra)

Hoje a tela faz a conta no navegador e por isso precisa do `arows` — que carrega
**peso e alvo**, ou seja, **o molde**. Com a chave que está no próprio JS, as 19 funções
se reconstroem em **2,4 segundos**.

Quando a conta for para o servidor (`MODO='servidor'`), o `arows` para de sair do banco:
a tela recebe a nota e as linhas **sem peso e sem alvo**. É isso que fecha o segredo
industrial. **Enquanto o serviço não passar na homologação, o molde continua aberto.**

## B.2 · Antes disso, dois bloqueios

1. **Qual pool de habilidades vale** — o do motor (49.780 espaços) ou o do banco
   (27.408)? Divergem em 2.681 de 2.836 cartas, **nos dois sentidos**. Não se prova de
   que lado está o certo: é decisão do Luis.
2. **Qual é o código que está no ar** — o Railway roda `servidor:app`, arquivo que não
   está na pasta de trabalho, e responde numa rota (`/nota`) que o `app.py` não tem.

## B.3 · A fonte deixou de ser o site — ✅ FEITO (migrou para A.1 e A.7)

## B.4 · A RODADA DE TODAS AS LINHAS (decisão do Luis, 26/08)

Como o banco foi **refeito** (tabelas novas), o único dado velho que sobra é o
**resultado dos motores** (`clube.build`). Decisão: **rodar o motor em TODAS as linhas de
novo** — elimina risco de duplicata e de carta faltando, deixa o resultado consistente
com a base nova. Ordem:
1. Aplicar `carta_jogo → clube.carta` (refresca as 1.963 com as travas).
2. Montar a fila **ordenada por overall desc** (mais fortes primeiro).
3. Luis roda o motor na máquina dele — roda contínuo e **sobe direto pro sistema**, de
   forma que o site sempre tenha as cartas mais fortes no topo (o que o pessoal procura).
`marcar ≠ rodar` — o motor só dispara sob ordem do Luis.

## B.4 · Login e cadeado comercial

O cadeado do plano pago roda no navegador do visitante — **não protege nada**. A chave
saiu do texto claro hoje (virou impressão), mas isso é higiene, não segurança. A
proteção de verdade é sessão no servidor.

---

# PARTE C — O QUE MUDOU E QUANDO

| migração | o que foi |
|---|---|
| `0049` | Conferidos os 3 `.jsonl` de bônus: batem exato com o banco, nada novo a carregar |
| `0050` | Corte das 6 chaves mortas do `linha` (17.504/17.504) |
| `0051` | **Achado 24 fechado**: o `insumos_bonus.json` não é mais necessário — md5 do molde idêntico, 32/32 tetos, 12/12 índices |
| `0052` | A rota enxuta da lista: `casa_lista` + `casa_arows`, −38% de bytes, 2,6× mais rápida |
| `0053` | O `eval()` saiu (0 diferenças em 40.610 casos); a chave PRO saiu do texto claro; duplicatas medidas — nenhuma acidental |
| `0054` | **Etapa 8**: a trava do nulo e a conferência lote a lote |
| `0055` | **Etapa 9**: 59 combinações de motivo viraram 9; 6.339 builds podem rodar já |
| `0056` | A trava do `valor_do_dono` — nem valor errado sobrescreve o que o dono pôs |
| `0057` | O campo de carta completa conferido, campo a campo |
| `0058` | **A chave do jogo**: `player_id = card_id & 262143` |
| `0059` | **Etapa 10: homologação REPROVADA** — o serviço recusa a build do motor |
| `0060` | **Etapa 11: o molde está público** dentro do `arows` |
| `0037` | **A fonte virou o jogo**: `clube.carta_jogo` (insumo, 40.100 cartas) + catálogo `estilo_jogo` com os 22 estilos 2027 reservados |
| `0038` | `carta_jogo`: `overall` nativo calculado, `tipo` base/colecionavel/teste, `roda_motor`, índice da fila |
| `0039` | Catálogo-tradutor: `estilo_jogo` com nome PT + posições dos 23 estilos ofensivos; `estilo_defensivo_ref` (13 defensivos 2027); `carta_jogo.estilo_of_pos`. 29 estilos + 56 ímpetos marcados `novo_2027` |
| `0076` | **Colunas mortas da `carta_jogo` apagadas**: `temporada`, `existia_2026`, `estilo_antigo`, `estilo_antigo_id` — 0 de 42.803 preenchidas. De 36 colunas para 32 |
| `0077` | **Extrator v2**: 28 colunas. Entram `habilidades` (65 bits), `aptidoes` (12×2 bits), `estilos_ia` (7 bits), `pe_ruim_uso` (bit 478), `pe_ruim_precisao` (578), `resistencia_lesao` (542/543), `forma` (582) — todos já eram lidos e eram descartados na exportação. Colunas renomeadas para `slot1_*`/`slot2_*`; o extrator passa a gravar **só o id**, nunca o nome |
| `0078` | **Varredura de acoplamento medida**: o site faz 2 chamadas ao banco (`casa_tela`, `bonus_posicao`); `casa_tela` é view de `clube.build` + `clube.funcao`; o avaliador usa 3 RPCs e nenhuma tabela |
| `0079` | `ARQUITETURA-2608-UMA-TABELA-DE-JOGADOR` **REVOGADO** — 4 erros: mandava fundir `carta_jogo` na `carta` (é o contrário), tratava `estilo_jogo`/`estilo_defensivo` como duplicatas (são os catálogos), dizia que a tela não lê o banco (lê), e o SQL do passo 2 apagava tabela boa |

---
| `0080` | **Carga completa 27/08**: 42.803 cartas com corpo, aptidões, habilidades, estilos de IA, pé ruim, lesão e forma. Antes eram 0 |
| `0081` | **O corpo saiu do site**: `PlayerAppearance.bin`, 12 medidas na ordem do `corpo_ordem` |
| `0082` | **`grupo_id` = `(card_id >> 38) & 255`** — level cap e orçamento derivados, 98,12% |
| `0083` | **`clube.fila`** — 125.932 linhas, prioridade 0 para as que já rodaram |
| `0084` | **Os motores leem e gravam no banco.** `fonte_unica.py` v2 · `roda_lote_v6.py` sem interruptor · `motor_bonus.py` v7 com bônus por função |
| `0085` | `clube.build` truncada · fotografia em `clube.build_arquivo_2608` (17.798) |

# PARTE D — COMO FUNCIONA DE AGORA EM DIANTE

## D.1 · A rotina da semana

1. O jogo atualiza `C:\ProgramData\KONAMI\eFootball\ST\Download\dt870_console_win.cpk`
2. Luis abre o `Extrator-ClubEfootball.html` e arrasta o `.cpk`
3. **Baixar SÓ AS NOVIDADES** (o extrator guarda foto da extração anterior no navegador)
4. O que aparece em "Só os lançamentos" é a **box em andamento**
5. Importar o CSV na `clube.carta_jogo`
6. Rodar a auditoria. **FALHA = parar.**
7. Motor só com ordem explícita do Luis. **Marcar ≠ rodar.**

## D.2 · As regras que não se negociam

- **A chave é sempre o código, nunca o nome.** `card_id`, `slot1_id`, `slot2_id`,
  `impeto_s1`, `funcao.codigo`, `posicao.codigo`. Nome é etiqueta e já quebrou três vezes.
- **O nome do estilo deriva do id por join.** Ninguém escreve nome à mão.
- **Uma sessão por vez escrevendo no banco.** Duas ao mesmo tempo foi como 959 cartas
  ganharam id 64/68 numa coluna de 6 bits (máximo 63) — valor que o extrator não produz.
- **Quando a foto do jogo e a lista da internet discordam, o jogo ganha.** Quando o Luis
  dita da tela do jogo, ele ganha dos dois.
- **Não supor.** Medir. Onde não deu pra medir, escrever "não medido".
- **Auditoria depois de toda mudança.** `FALHA` = parar, investigar, registrar veredicto
  em `clube.divergencia_conhecida`. Nunca mudar o esperado pro teste passar.

## D.3 · O que nunca se apaga

```
clube.build · clube.funcao          ← a tela inteira pendura aqui
public.casa_tela · casa_lista · casa_arows
public.bonus_posicao
public.regua_pacote() · carta_para_simular() · pool_da_funcao()   ← o avaliador
clube.estilo_jogo · clube.estilo_defensivo   ← os catálogos dos dois campos
clube.carta_jogo                     ← o cadastro
```