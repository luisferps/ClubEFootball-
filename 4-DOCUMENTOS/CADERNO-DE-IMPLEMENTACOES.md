# CADERNO DE IMPLEMENTAÇÕES — arquitetura do sistema
**Aberto 25/08 · atualizado 27/08 (sessão da carga nova + motores no banco)**

Estados: `ANOTADO` (a discutir) · `DECIDIDO` (Luis cravou, falta executar) · `FEITO`.
Só o Luis muda estado. Sessão nenhuma executa item `ANOTADO`.

---

# 🔥 27/08 — O QUE FECHOU HOJE

| item | estado | prova |
|---|---|---|
| **Carga nova completa** | ✅ FEITO | 42.803 cartas · **todas** com corpo, aptidões, habilidades, estilos de IA e pé ruim |
| **Estilo defensivo (slot 2)** | ✅ FEITO | bit **440** largura 6, no arquivo certo (`ST\Download`). Era 72%, agora fechado. 4.100 cartas com o 2º slot |
| **Habilidades / aptidões / IA** | ✅ FEITO | eram 0 de 42.803. O extrator lia e descartava na exportação |
| **Corpo (12 medidas)** | ✅ FEITO | `PlayerAppearance.bin`, registro de 64 bytes. Antes vinha do site |
| **Pé ruim · lesão · forma** | ✅ FEITO | bits 478, 578, 542/543, 582 |
| **Level cap** | ✅ RESOLVIDO POR DERIVAÇÃO | `(card_id >> 38) & 255` = o tipo da carta. Separa cresce/não-cresce com **98,12%** |
| **A fila** | ✅ FEITO | `clube.fila`, **125.932 linhas** · 6,04 funções por carta (o arquivo morto tinha 6,28) |
| **Motores lendo do banco** | ✅ FEITO | `fonte_unica.py` v2 · `roda_lote_v6.py` sem interruptor · `motor_bonus.py` v7 |
| **Bônus por FUNÇÃO** | ✅ FEITO no motor | 1,0 na casa do estilo + 0,5 do 2º slot, teto 1,5 |
| **`clube.build` truncada** | ✅ FEITO | arquivo morto em `clube.build_arquivo_2608` (17.798) |

**Auditoria depois de tudo: 0 FALHA · 15 CONHECIDA · 36 OK.**

## O achado do dia: o tipo da carta mora no card_id

```
(card_id >> 38) & 255

grupos 71, 192, 196, 200, 204  →  NÃO CRESCEM (cap 1, orçamento 0)  · 935 cartas, 934 acertos
grupos 0, 64, 68, 128, 129, 132 → CRESCEM (cap 29 a 35)             · 2.309 cartas, 2.150 acertos
```

Sai de uma conta no id. Sem arquivo, sem coleta, sem efHUB.

## A fila agora confere a migração

```
prioridade 0 →  16.381 linhas · 2.756 cartas  ← JÁ RODARAM ANTES, vão primeiro
prioridade 1 →  lançamentos (furam a fila)
prioridade 5 → 109.551 linhas · 18.669 cartas · por overall desc
```

Ordem do Luis, 27/08: *"é importante a gente rodar primeiro as que a gente já rodou antes,
pra ver se está certo. Se estiver errado, a gente para nas primeiras."*

## Automático, sem ninguém apertar nada

- Gatilho `carta_entrou`: carta nova entra → a fila se enche sozinha. Carta que mudou →
  a build velha é apagada e ela volta pra fila.
- Gatilho `cap_do_id`: deriva `grupo_id`, `level_cap` e `orcamento` do próprio `card_id`.
- `gravar_build()`: grava na `clube.build` **e tira a linha da fila**, no mesmo comando.

---

# 👉 A PRÓXIMA COISA — RODAR O MOTOR

Tudo pronto. Falta o Luis rodar o `roda_lote_v6.py` na máquina dele.

**A conferência:** as 2.756 primeiras já rodaram antes. Comparar o `b1` novo com
`clube.build_arquivo_2608` nas primeiras dezenas. Divergiu → para.

`marcar ≠ rodar`. O motor só dispara sob ordem do Luis.

---

# 📌 O QUE AINDA FALTA

## 1 · Limpeza do banco — `DECIDIDO`, falta rodar
Blocos 1 a 4 do `4-DOCUMENTOS\LIMPEZA-DO-BANCO.sql`. Tira 21 tabelas do `clube` (76 → 55).
O bloco 5 depende de reescrever 3 funções de auditoria. O bloco 6 (schema `public` inteiro)
só depois que o motor estiver rodando pelo banco e provado.

## 2 · Etapa 7 — a conta sai do navegador
O `arows` que a tela recebe carrega **peso e alvo** — que *são* o molde. Com a chave que
está no próprio JS, as 19 funções se reconstroem em 2,4 segundos. Só fecha quando a conta
for pro servidor e o `arows` parar de sair do banco. **É um deploy só, atômico.**

## 3 · O Railway roda um arquivo que não está na pasta
`servidor:app` no Custom Start Command; a pasta tem `app.py`. O serviço responde `POST /nota`,
rota que não existe no `app.py`. **Baixar do repositório o que está realmente no ar.**

## 4 · A validação do /avaliar recusa as builds do próprio motor
**Não é decisão do Luis — é conserto, e ele já está pronto no banco.**

Retificado em 25/08: o que se dizia (*"o pool do banco discorda do do motor em 2.681 de
2.836 cartas"*) comparava duas coisas diferentes. O `falta_pool` varia **por função** na
mesma carta (a carta `89130772077328` tem 8 tamanhos em 10 funções, de 22 a 30);
`carta_habilidade` relação `espaco` é outra lista, **por carta**.

**A medida certa:** 6.000 habilidades usadas em builds não marcadas — **6.000 de 6.000
estão no `falta_pool` da própria build. Zero fora.** O motor nunca escolheu fora do pool.

Quem erra é a validação do `/avaliar`, que confere contra `carta_habilidade` — lista mais
curta, onde só 3.552 das 6.000 aparecem.

**Conserto:** o serviço passa a chamar `public.pool_da_funcao(card_id, funcao)`, que
devolve o `clube.build.falta_pool` gravado quando o motor rodou. Nenhuma fórmula a deduzir.
⚠️ **Depende do item 3** — não dá pra consertar um arquivo que não está na pasta.

## 5 · Level cap real — sem pressa
3.243 reais · 39.560 estimados pelo grupo. O coletor do efHUB (`coletor_efhub.js`) roda
quando o Luis quiser e continua de onde parou. Cap real sempre vence o estimado.

## 6 · O site ler os dois estilos
O `motor-e-ficha-base.js` só conhece **um** estilo (`c.modelo`). O `EST_POS` dele tem nomes
velhos (Provocador, Zagueiro ofensivo/defensivo) e nenhum dos 8 de 2027.
⚠️ Mas o bônus **vem pronto do motor** — o JS é rede de segurança. Prioridade baixa.

## 7 · Vaga de habilidade estourada — 2.941 builds
O motor sempre montou 5 habilidades, mas a regra é de 0 a 5 por carta. Medido: cartas com
0 vagas receberam builds com média 4,98 habilidades; com 1 vaga, 4,95. **A nota dessas
está inflada.** São 2.941 builds de 488 cartas, todas já marcadas para recalcular.
**A rodada nova resolve sozinha** — não se conserta na mão.

## 8 · Menores
- 149 cartas sem nome no arquivo do jogo.
- Etiquetas de algumas funções vão mudar (falta a lista de/para do Luis).
- As 720 builds com bônus furado: some na rodada nova.

---

# ⛔ ERROS DESTA SESSÃO — para não repetir

1. **Chamei o slot 1 de "ofensivo".** É o slot **legado**, e nele convivem estilos ofensivos
   e defensivos (*Goleiro defensivo*, *Lateral defensivo*, *O destruidor* moram lá).
   Isso gerou alarme falso de "299 goleiros errados".
2. **Disse que ímpeto e level cap eram "dado de servidor".** Desculpa de quem não achou —
   o ímpeto a gente extrai desde sempre (bits 308/288).
3. **Cacei no arquivo errado** (dt200 do Steam) quando o certo é o `ST\Download\dt870`.
4. **Afirmei `A = B × 4` como regra** dos dois catálogos de estilo. É coincidência —
   o Casillas quebra (64 no A é *Goleiro adiantado*, 16 no B é *Goleiro ofensivo*).
5. **Marquei `regra_funcao` para apagar** — e é ela que define a fila. Por pouco.
6. **Ia coletar 400 fichas no efHUB** quando o banco já tinha 3.165 caps.
7. **Não usei os documentos do projeto antes de medir e opinar.** Sete erros já estavam
   respondidos lá.

**A lição:** ler o caderno e os documentos ANTES. E medir na fonte, nunca supor.

---

# REGRA 00 — ONDE MORAM AS COISAS

```
1-SISTEMA\              a tela que vale (lê casa_tela)
2-MOTORES\              travas.py
4-DOCUMENTOS\           manual e relatórios
5-COLETA-EM-PARALELO\   o coletor V8
6-AVALIADOR-NO-RAILWAY\ o serviço  ⚠️ não é o que está no ar
7-VARREDURA-DO-JOGO\    Extrator-ClubEfootball.html  ← o arquivo do jogo
ClubEfootball-V3-main\...\programas\   ← É AQUI QUE OS MOTORES RODAM
os dados ..............  Supabase, sempre
```

**A tabela principal é a `clube.carta_jogo`** — o cadastro do jogador, 42.803 linhas.
A `clube.carta` (41.404) é a velha; hoje só guarda os 3.243 level_cap reais. Quando eles
migrarem, ela pode ser apagada.

---

# PRINCÍPIO 0 — O BANCO É VIVO

```
EXTRATOR (navegador do Luis) ──grava──► clube.carta_jogo
MOTOR (máquina do Luis, sob ordem dele) ──grava──► clube.build
USUÁRIO (site, com login) ──grava──► a tabela DELE
DERIVADOS (casa_tela, topo, mediana) ── NINGUÉM escreve ──
```

**Chave sempre pelo CÓDIGO, nunca pelo nome:** `card_id`, `slot_ofensivo_id`,
`slot_defensivo_id`, `impeto_s1`, `funcao.codigo`, `posicao.codigo`.
O nome é etiqueta e já quebrou três vezes.

⛔ **Uma sessão por vez escrevendo no banco.** Duas ao mesmo tempo foi como 959 cartas
ganharam id 64/68 numa coluna de 6 bits (máximo 63).

---

# ORDEM DE EXECUÇÃO — onde estamos

```
✅ 1 · a receita completa
✅ 2 · a caixa de entrada        (o Alimentador foi aposentado — a fonte é o jogo)
✅ 3 · o cadastro único           clube.carta_jogo, 42.803
✅ 4 · proveniência + completude
✅ 5 · o que nasce do código
✅ 6 · auditoria dos motores
🔄 7 · O SIMULADOR E A PORTA      o AVALIAR está no ar. Falta a ficha pedir ao servidor
✅ 8 · A FONTE = O JOGO           extrator 29 colunas · carga completa · fila montada
👉 9 · A RODADA DE TODAS AS LINHAS   TUDO PRONTO. Falta o Luis rodar.
  10 · homologação → publicar
  11 · login + comercial → CHAVES → LANÇAR
```
