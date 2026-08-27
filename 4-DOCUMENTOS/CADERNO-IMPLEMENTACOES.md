# CADERNO DE IMPLEMENTAÇÕES — arquitetura do sistema (aberto 25/08, reordenado 25/08)

**O que é isto:** a lista viva das mudanças que o Luis decidiu fazer no sistema.
**Nada aqui foi executado.** Estados: `ANOTADO` (a discutir) · `DECIDIDO` (Luis cravou,
falta executar) · `FEITO`. Só o Luis muda estado. Sessão nenhuma executa item `ANOTADO`.

---

# REGRA 00 — ONDE MORAM AS COISAS (Luis, 25/08)

> *"Não grave em outro lugar, sempre grava lá — senão a gente fica com várias cópias
> em vários lugares e fica ruim de gerenciar."*

**O arranjo da obra (decidido pelo Luis em 25/08):**

> *"Vou baixar a pasta do GitHub e colocar DENTRO da pasta que o GPT enviou. Essa pasta
> vai ser a ÚNICA em que a gente faz inserções e alterações. Quando finalizar tudo, a
> gente sobe ela e substitui a do GitHub — e depois disso não mexe mais nela: tudo passa
> a ser feito por lá."*

```
DURANTE A OBRA                           DEPOIS DA OBRA
SITE-ATUALIZADO-2026-08-24/              GitHub `truefootball-api`
 ├─ (o sistema/tela, do GPT)      ──►    volta a ser o ÚNICO lugar de código.
 └─ (o repo do GitHub, baixado)  sobe    A pasta local aposenta e não se toca mais.
 = A ÚNICA OFICINA. Toda inserção
   e alteração acontece aqui.
os dados ........................ Supabase (sempre)
coletas brutas (efootballdb) .... matéria-prima: entram no banco com assinatura
```

Regras: (1) arquivo solto FORA da oficina não é fonte — sessão nenhuma trabalha em cima
de cópia avulsa; (2) nenhuma cópia nova nasce em outro canto; (3) na substituição final
do GitHub, o que não foi tocado se preserva — em especial o cofre (`encaixe_B_v159.html.gz`)
e os registros históricos do repo; (4) é SISTEMA, não "site" — vocabulário oficial.

---

# PRINCÍPIO 0 — O BANCO É VIVO (Luis, 25/08)

> *"Esse retrato do banco hoje não é fixo, é dinâmico. Entram insumos diariamente,
> os motores processam e gravam o resultado, e os usuários gravam pelo site."*

O ciclo diário, com os papéis fechados:

```
COLETOR/VIGIA ──grava──► INSUMO (cartas, ímpetos, boxes)      só ele escreve aqui
MOTOR (máquina do Luis, sob ordem dele) ──grava──► RESULTADO  só ele escreve aqui
USUÁRIO (site, com login) ──grava──► a tabela DELE            só ele escreve aqui
                                     (FUTURO: o sistema ainda NÃO está publicado —
                                      esta porta nasce no lançamento)
DERIVADOS (topo, tela, mediana) ── NINGUÉM escreve ──         refazem-se sozinhos
```

Consequências que valem para TODOS os itens deste caderno:
1. Toda mudança de estrutura tem que dizer quem é o escritor diário da tabela e por
   qual porta (qual chave) ele entra. Tabela sem escritor declarado é derivada.
2. O furo das 6.824 cópias foi uma violação disto: escreveram na camada de
   apresentação, que não tem escritor.
3. **Item Z (a rota):** por ser banco vivo (insumos e rodadas continuam entrando mesmo
   sem público), antes de virar a chave roda-se um ACERTO DE DIFERENÇA (o que entrou no
   velho desde a cópia vai pro novo), em janela escolhida pelo Luis, sem rodada de motor
   no meio. Como ainda não há usuários, a janela é livre — sem pressão de tráfego.
5. **Contexto de fase (Luis, 25/08): o sistema está em PRÉ-LANÇAMENTO.** Ainda não foi
   publicado; a otimização atual é preparação para pôr na internet. Os itens A e B são
   condição de qualidade PRÉ-publicação, não conserto emergencial de produção.
4. A coleta do efootballdb (ímpetos/boxes) precisa deixar de ser evento único e virar
   rotina periódica — hoje é script manual no Console (o SOFTWARE-RECOLETA-BOXES já
   existe na máquina do Luis; avaliar encaixe no vigia). `ANOTADO`.

---

# ✅ O QUE JÁ FOI FEITO (25/08, madrugada) — a CASA está de pé

| item | estado | prova |
|---|---|---|
| **Z · a casa nova (fases 0-7)** | ✅ **FEITO** | schema `clube`: 27 tabelas + 3 views, 15 migrações. Auditoria: 29 OK · 2 CONHECIDAS · 0 FALHAS |
| **B · furo dos nomes** | ✅ **FEITO na casa** | função chaveada por `codigo`; as 6.824 cópias não migraram (17.798 = builds) |
| **D · MED duplicada** | ✅ **FEITO na casa** | view `mediana_funcao` — Falso nove e CA móvel com medianas próprias |
| **E · uma tabela de resultado** | ✅ **FEITO** | `clube.build` = builds ⋈ bonus, `nota_final` gerada pelo banco |
| **A · os 870 ímpetos** | ✅ **carregados e marcados** | verdade do efootballdb na `carta_impeto`; **1.321 cartas · 5.711 builds** marcadas com motivo. ⏳ falta a rodada do motor (tua ordem) |
| **auditoria** | ✅ **FEITO** | `clube.auditoria_completa()` + a **skill** `clubefootball-auditoria` |
| limpeza do stage_v2 do GPT | ✅ **FEITO** | 951 MB liberados; banco 1.472 → 612 MB |
| **fase 8 · a virada do site** | ✅ **FEITA NO CÓDIGO** | view `public.casa_tela` no contrato da `tela_encaixe`; site trocou só o endpoint em 3 pontos; provas REST: abertura 200/2,4 s · Ala cruzador 300→1.288 · forca nula 0 · Neymar 441,4. Auditoria: 0 FALHAS · 2 CONHECIDAS. ⏳ homologação do Luis antes do Netlify |
| **coleta em paralelo (T7)** | ✅ **ENTREGUE** | `5-COLETA-EM-PARALELO\`: coletor V6 (Console do efhub) + guia de retomada; 446 feitos · 28.776 faltam |

**Erros meus que a auditoria pegou e foram corrigidos:** molde rotulado v1 sendo
**v5** (achado pelo Luis) · posições secundárias grudadas em 2.090 cartas ·
7 insumos faltando (3 deles impediam o motor de rodar).

**Ganho não planejado:** o estilo de jogo da IA saltou de 1.606 para **6.445
cartas** (93%) — o dado estava no canônico do GPT.

⏳ **Próximo passo, esperando teu aval:** homologar a virada (abrir `1-SISTEMA\index.html` e navegar) → publicar no Netlify → fase 9 (acerto de diferença + aposentar o legado).

---

# ORDEM DE EXECUÇÃO — v3, decidida pelo Luis em 25/08 (à noite)

> *"A gente vai arrumar a CASA primeiro. Depois coloca os MORADORES novos.
> Aproveitando o que já tem; refazendo só o que foi feito errado."*

```
FASE 1 · A CASA      reestruturação completa (banco 6 camadas + sistema),
                     com os dados que JÁ existem — itens B, D, E, F, H, Z
                     e a verdade dos 870 embutida (item A, sem rodar motor)
FASE 2 · MORADORES   marco zero da coleta (T7) → RODADA ÚNICA do motor
                     (novas + 870) → Alimentador (item I) → login/comercial
                     (item G) → chaves (por último) → LANÇAR
```
Plano detalhado: `PLANO-DE-ACAO-LANCAMENTO.md` v3. A rodada 3 do GPT fechou as
perguntas (lote-0001 válido; V3/V4 arquiváveis; lista dos 8.521 em
`IDS-JA-COMPLETOS-EXCLUIDOS.txt`; rebuild 25→100→250; MED duplicada datada de 18/08).

---

## A · AS OTIMIZADAS FEITAS COM ÍMPETO ERRADO — `DECIDIDO` · PRIORIDADE 1

> Ordem do Luis, 25/08: *"A gente tem que verificar quais [otimizadas] foram feitas com
> ímpetos errados, agora que a gente tem a fonte da verdade. E tem que MARCÁ-LAS pra
> poder refazer. Não posso esquecer disso. É muito importante. Isso é um furo."*

**Contexto:** foi detectado (~600–700 cards) que os ímpetos no sistema estavam errados.
A fonte da verdade agora é o **efootballdb** (coleta completa na máquina do Luis:
24.744 + 5.063 = 29.807 cards, com booster/booster2/booster3 por card + catálogo de 410
ímpetos com efeito por atributo). O banco tem `card_impeto` com 6.626 linhas, sendo
1.977 com id em dúvida e 28 "não sei".

**O plano (3 passos, cada um com prova):**
1. **Montar a verdade:** ler os 31 lotes do efootballdb e extrair, por card, os ímpetos
   nativos reais. Vira uma tabela de conferência no banco (aditiva, não mexe em nada).
2. **Cruzar:** verdade × `card_impeto`/`cards_base` → relatório: quais cards estavam com
   ímpeto errado no insumo. Depois: quais linhas da `builds` (as otimizadas) foram
   calculadas usando esses insumos errados.
3. **Marcar:** as builds atingidas ganham marca de "refazer" (a `builds` já tem o
   mecanismo de fila — `na_fila` — ou coluna própria de suspeita, a decidir na hora).
   ⛔ **Marcar ≠ rodar.** O motor é do Luis, roda na máquina dele, sob ordem dele.

**Pré-requisito:** transferir/ler os ~1,5 GB de lotes (estão em Downloads, conectado).

## B · O FURO DO NOME DAS FUNÇÕES — `DECIDIDO` · PRIORIDADE 2

A função passa a ser chaveada pelo `codigo` (a chave já existe na `funcoes`); apagar as
6.824 cópias com etiqueta da `tela_encaixe` e regenerar da `builds` completa e com
`forca`; o site pergunta por código e mostra o rótulo.
Fatos medidos e pré-requisitos: FKs de `builds`/`molde`/`estilo_valor` → `funcoes(nome)`
tratadas primeiro; gatilhos `atualiza_topos` na jogada; `tela_encaixe` é tabela física
sem FK; 294 pares da `builds` faltam na tela (120 GO def, 44 GO of…).
Consequência visível: 3.574 encaixes voltam ao site (ex.: Neymar 87 recupera a melhor
função dele, 441,4) e o % do topo das 8 funções volta a ter âncora.

## D · CONSERTAR A MED (mediana por função no site) — ✅ **FEITO no banco** · ⏳ falta no site

A view `clube.mediana_funcao` existe e mede a mediana de verdade — Falso nove e
Centroavante móvel têm medianas próprias e diferentes. **Falta:** o site parar de usar
a constante `MED` do código (é a Etapa 3 do plano de implementação).

## E · UMA TABELA DE RESULTADO SÓ — ✅ **FEITO**

`clube.build` = `builds` ⋈ `bonus`, 17.798 linhas, `nota_final` gerada pelo banco.
As 6.824 cópias não migraram. Nada mais escreve na camada de apresentação.

## F · TIRAR O DADO CONGELADO DO SITE — ⏳ **começou (0027)**: FILA, B5V, formações e sugestões já saíram do JS para o banco. Falta o resto (BONUS_PRONTO, CORPO_*, PACOTE, BOXHIST, PR_RAW, textos) — sai junto com o simulador.

Revisado com a leitura da casca inteira (25/08): **não é 1,5 MB, é 2,2 MB** — 71% de
todo o JS. `BONUS_PRONTO` 1.050 KB · `CORPO_EFHUB` 308 KB · `BOXHIST` 192 KB ·
`PACOTE` 151 KB · `PR_RAW` 54 KB · `CORPO_MOTOR` 127 KB · `PIMP` 30 KB ·
`CORPO_MOLDE` 15 KB + ~110 KB de texto editorial + 25 KB de CSS congelado.
Conferido campo a campo contra o banco: **1.630 KB já têm casa** (e o `CORPO_MOTOR` e o
`CORPO_MOLDE` foram provados idênticos, por hash). É a Etapa 3 do plano.

## G · TABELA DO USUÁRIO + LOGIN (RLS) — ⏳ **a tabela existe, o login não**

`clube.usuario_estado` criada com RLS por `auth.uid()`, **0 linhas**. O estado do
usuário continua inteiro no `localStorage` (`MT_v1` + `CLUBEFOOTBALL_USER_STATE_V2` +
um diário de transação artesanal), e o `ownerId` do repositório está **fixo em `null`**
— é exatamente o slot onde o `auth.uid()` entra. Vira a Etapa do comercial.

## H · CARGA DO SITE SEM TELA PRETA — ⏳ **medido, não executado**

Medido em 25/08: **51 MB em ~19 requisições**, sendo **3 síncronas** (2.000 + 1.000 +
1.000 linhas) que travam a renderização. Se a rede falhar, `erroNaTela()` reescreve o
`<body>` inteiro. É a Etapa 3 do plano, junto com o F.

## C · AUDITORIA DO CÓDIGO — ✅ **FEITA, as duas metades**

✅ **A casca**, lida inteira (25/08): 9 arquivos, 3,0 MB, ~14.500 linhas.
✅ **Os motores**, lidos linha a linha (25/08): `motor.py` 957 · `regua.py` 179 ·
`equacao.py` 270 · `motor_bonus.py` 840. **32 achados: 14 CRÍTICOS, 16 GRAVES**,
gravados em `clube.achado_motor`. Documento: `AUDITORIA-DOS-MOTORES.md`.

🔴 **O gate reprovou: o motor não pode subir para o Railway como está.** Os três
piores: (1) o motor **sempre monta 5 habilidades** quando a regra é 0 a 5 — nota
inflada invisível; (2) o motor de bônus **não lê o banco** (lê um JSON que não está no
repositório) e o `b_total` **soma tratando ausência como zero**; (3) orçamento, vagas
ou molde ausentes produzem build **plausível e errada**, sem uma linha de aviso —
não há um único `assert` em 957 linhas.

## I · O ALIMENTADOR — ⏳ **não começou** · o primeiro tijolo dele é a coleta nova

Decisão de 25/08 (recoleta total) muda o começo: a coleta ampliada — todos os cards,
com imagem — **já é a primeira esteira do Alimentador**. O desenho dele deve ser feito
com ela, não depois.

## Z · A ROTA DAS NOVE FASES — ✅ **fases 0-8 FEITAS** · ⏳ falta a 9

O banco novo das seis camadas construído DO LADO, enchido com o que existe, provado pela
prova dos nove, chave virada consumidor por consumidor. Documento:
`ROTA-2508-CONSTRUIR-O-NOVO-DO-LADO-as-nove-fases.md`. Só começa quando A–H estiverem
resolvidos ou conscientemente dispensados.

---

# ✅ FEITO EM 25/08 (tarde) — migrações 0022 a 0027

| o quê | número |
|---|---|
| 11 insumos do legado → casa | régua 6 · bônus_parametro 13 · molde_corpo 384 · barra 27 · custo 25 · mult 100 · elenco 114 · tipos 137 |
| caixa de entrada da coleta | `clube.recebimento`, INSERT-only, fotos no Cloudinary |
| **cadastro único** | carta **3.269** · carta_posicao_comprada **3.684** (prova: ímpeto e habilidade idênticos, 3.684/3.684) |
| proveniência por campo | `clube.proveniencia` |
| completude por finalidade | v1, 25 regras, 3 finalidades · otim 2.760/509 · bônus 2.480/789 · ficha 2.072/1.197 |
| 🔴 builds rodadas com carta incompleta | **1.342 de 356 cartas** — marcadas |
| o que só existia no código | FILA 1.139 · B5V 330 · formações 187 · sugestões 27 |
| auditoria | **39 OK · 0 FALHAS · 12 CONHECIDAS** |

---

# REGRA 01 — QUEM É CASA E QUEM É MATÉRIA-PRIMA (Luis, 25/08)

> *"Eu não estou entendendo por que você está olhando ainda a tabela do GPT. Você vai
> gravar os dados nela? Eu pensei que você já tinha feito uma tabela para repaginar o
> banco."*

**Resposta e regra, cravada:**

| schema | papel | escreve-se nele? |
|---|---|---|
| **`clube`** | **A CASA.** Único lugar vivo: onde tudo mora e de onde tudo é consultado | **SIM — só aqui** |
| `public` (legado) | **matéria-prima.** De onde a casa PUXA (`cards_base`, `cards_efhub`, `insumo_*`, `builds`, `bonus`) | ⛔ **NÃO** |
| `clubef_read_v2` (GPT) | **matéria-prima.** A normalização canônica das 42.807 cartas | ⛔ **NÃO** |

Eu estava **lendo** essas tabelas como fonte para achar dado que a casa não tinha —
nunca gravando. Mas a confusão é justa, porque na carga de 25/08 eu tratei o canônico
do GPT como fonte de fato (`estilo_ia do canonico`, migração 0004) sem declarar isso em
lugar nenhum. **Agora está declarado.**

**Destino das duas:** depois que tudo for puxado e conferido, elas se aposentam
(`_legado`) e só a casa fica de pé. E quando a **recoleta total** entrar, a coleta nova
passa a ser a fonte — as duas viram arquivo histórico, não fonte de consulta.

---

# REGRA 02 — A AUDITORIA DE COBERTURA (Luis, 25/08) — ✅ IMPLEMENTADA

> *"Se eu pudesse mudar uma coisa só no processo seria essa. Implementa também."*

A auditoria antiga provava **igualdade** contra a fonte que a sessão escolheu — nunca
perguntava se existia outra fonte ignorada. Foi assim que 3.160 valores ficaram de fora
sem ninguém notar.

**O que passou a existir (migração 0021):**
- `clube.campo_fonte` — 34 regras, 13 campos: onde procurar cada campo quando ele
  estiver vazio na casa, com ordem de prioridade e observação;
- `clube.auditoria_cobertura()` — para cada campo vazio, responde: **existe valor em
  alguma outra tabela nossa?** Se existe, é **FALHA** (dado que ninguém puxou), não é
  buraco de coleta;
- acoplada à `clube.auditoria_completa()` — que passou de 36 para **46 conferências**.

**Primeira rodada: 10 FALHAS** — e elas são a lista de serviço da carga:
estilo da IA **393 de 393** · pé ruim precisão **506 de 509** · data **458** ·
lesão **409** · votos **382** · altura e peso **340** cada · tier **307** ·
pé ruim uso 14 · idade 11.

E o contrário também ficou provado: **`max_ovr` (701) dá OK** — não existe em fonte
nenhuma nossa. Esse é coleta de verdade.

---

## REGISTRO DE DECISÕES DE FONTE

- **Ímpetos e boxes: efootballdb. Todo o resto: efHub.** (Luis, 25/08)
- Coletas na máquina do Luis, manifestos conferidos sem falhas (24.744 + 5.063).

## ⛔ PROTEÇÕES IMEDIATAS (respostas da rodada 2, 25/08)

- **NÃO limpar o perfil/dados do Chrome** que rodou a Tarefa 7 (o checkpoint vivo da
  coleta está no IndexedDB, banco `clubefootball-t7-efhub-fresh-v6`).
- **NÃO apagar `Downloads\coleta-efhub-dados-fotos`** (os 446 payloads reais da T7).
- **NÃO apagar as pastas do Codex** listadas no manual A9 (normalização 42.806,
  comparação dos 870, snapshot do Supabase) nem `cards_efhub_COMPLETO.csv`.
- `config.txt` tem chave: nunca entra em ZIP nem em repositório.
- A conta do universo: 42.806 = 29.222 (T7 faltantes) + 8.521 (efHub completos)
  + 5.063 (complemento efootballdb). T7 real: 446 feitos, 28.776 faltam.

## PERGUNTAS ABERTAS

- O cadeado comercial do MODO B (🔒) nas seis páginas do Elenco: fica ou sai?
- ~~`cards_efhub` × `cards_base`: qual é a fonte única?~~ → **RESPONDIDO em 25/08: nenhuma das duas.** A decisão do Luis é **recoletar todos os cards** e a coleta nova passa a ser a fonte, com data e assinatura. As tabelas velhas viram consulta de emergência, não fonte.
- ~~Respostas do GPT~~ → **recebidas** (3 rodadas) e absorvidas.
- **NOVA (25/08):** a ficha mostra a coluna "Alvo" — é ferramenta do Luis, sai para o usuário. Resolvido no desenho: quem decide o que entrega é o **servidor**, não a flag local.
- **NOVA (25/08):** o cadeado comercial do MODO B (🔒) — continua aberta.

---

# ITEM — A REGRA DOS DOIS ESTILOS · `FEITO` (banco) / `DECIDIDO` (motor)

**Aberto e decidido em 26/08/2026. Banco executado às 16:56 de 26/08/2026.**

> Toda alteração deste caderno entra com **data e hora**. Não sobrescrever entrada
> antiga — só acrescentar embaixo.

## A regra (Luis, 26/08/2026)

1. **Cada estilo aponta a ficha dele.** 1,0 na ficha do estilo; +0,5 se o segundo slot
   também ativar na posição — **repetido ou não**. Teto 1,5.
2. **O primário só diz qual ficha é a recomendada.** Defesa (ZC/LD/LE/GO) e VOL → slot
   defensivo. Meio (MLG/MLD/MLE/MAT) e ataque (CA/SA/PTD/PTE) → slot ofensivo.
3. **Cascata.** Slot recomendado Básico → o molde sai do outro, com 1,0 cheio.
4. **Estilo sem casa não roteia** — só paga o 0,5.

> *"O molde serve pra saber como fazer a build do cara."* — a build é uma só, então
> tem que existir um primário.

> *"O volante é a fronteira entre ataque e defesa."* — e é a única posição que já tinha
> as duas fichas montadas de lados opostos antes do 2027.

## `FEITO` — 26/08/2026 16:56 · migração `regra_dois_estilos_casa_e_secundario`

| # | o que | resultado |
|---|---|---|
| 1 | `bonus_parametro.estilo_ativo_secundario = 0.5` | ✔ |
| 2 | Etiqueta: "Zagueiro defensivo/ofensivo" → "Lateral defensivo/ofensivo" | ✔ 0 sobras · **4.997 laterais destravados** |
| 3 | Cadastro dos 8 estilos novos de 2027 em `bonus_posicao_regra` | ✔ 8 |
| 4 | **`clube.estilo_funcao`** — a casa de cada estilo | ✔ **57 linhas** |
| 5 | **`clube.posicao_slot`** — o slot que manda | ✔ 13 posições |

Auditoria rodada depois: **0 FALHA** (só OK e CONHECIDA).
SQL guardado em `4-DOCUMENTOS\REGRA-2608-DOIS-ESTILOS.sql`.

## `DECIDIDO` — falta executar (é motor, não banco)

- O motor ler `clube.estilo_funcao` para o bônus (por **ficha**, não por posição) e
  somar o segundo slot com o `estilo_ativo_secundario`.
- Sincronizar `regra_posicao_estilo` — está sem a linha do Falso nove de 12/08.

## Efeito medido

- **1 carta** troca de molde: **Konaté 82** (Defensor criativo + O destruidor) sai de
  Zagueiro de saída e passa a ter as duas fichas, com **combate** como recomendada.
- **47 cartas** passam a 1,5.
- **10.545 defensores** (61% da defesa) não mudam nada — protegidos pela cascata.
- **42.802 de 42.803** mantêm o molde.

## Decisões e achados anexos (26/08/2026)

- **`clube.estilo_valor` não é lida pelo motor** e **não serve para pontuar**: em toda
  função o estilo que a define vale 100, porque a função era definida pelo estilo. É
  distribuição, não mérito. Confirma o que o Luis já dizia: *"nunca fiz ele processual"*.
- **`bonus_posicao_regra` × lista oficial do jogo: bate 100%.**
- **Falso nove: pendência de 13/08 ENCERRADA.** Não existe como estilo — nem no catálogo
  nem em nenhum slot das 42.803 cartas. *"É função"* (Luis). A regra de 12/08
  (`CA ou SA + Atacante Pivô = Falso nove`) continua válida; a fila pode rodar.
- **Só O destruidor é combate; todo o resto é saída.** Não nasce "Zagueiro posicional".
- **Casa nova aprovada:** `O destruidor + LD/LE → Lateral defensivo` — sem ela, um
  lateral marcador cairia em Lateral ofensivo e o sistema mandaria montá-lo pra subir.
- **Estilo repetido nos dois slots paga o 0,5.** Cheguei a propor travar; o Luis
  derrubou: quem é Primeiro volante nos dois faz aquilo com e sem a bola — travar o
  deixaria empatado com quem tem o segundo slot Básico e desliga na defesa.

## Propostas recusadas (não reabrir sem dado novo)

| proposta | motivo |
|---|---|
| Função "Zagueiro posicional" p/ Mestre da linha alta e Cobertura | não são de combate nem coisa nova: são saída |
| Bônus proporcional pela `estilo_valor` | a tabela é distribuição, não mérito |
| Bônus binário só por função (secundário zera) | apaga o segundo estilo do Konaté |
| Um primário único escolhendo a única ficha | perde a leitura dupla; no volante as duas fichas são legítimas |
| Travar o 0,5 no estilo repetido | deixaria o cara defasado |
