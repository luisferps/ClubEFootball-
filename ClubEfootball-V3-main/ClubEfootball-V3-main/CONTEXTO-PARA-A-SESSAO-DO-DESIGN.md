# CONTEXTO PARA A SESSÃO DO DESIGN — Encaixe / TrueFootball
**Escrito em 17/08/2026 pela sessão da transformação. Tudo aqui foi medido contra o banco de verdade, não suposto.**

---

## 1 · O QUE É O SISTEMA, EM UM PARÁGRAFO

O Luis joga eFootball. Cada carta do jogo pode ocupar **19 funções** diferentes (Ponta criadora, Zagueiro de combate, Goleiro ofensivo…). Um motor calcula, para cada par **carta × função**, a melhor configuração possível — quais barras de progressão subir, qual ímpeto fabricar, qual técnico usar, quais 5 habilidades adicionar — e devolve uma **nota**. O site serve para olhar esse ranking: quem é bom em quê, e por quê.

Hoje há **12.370 pares carta × função calculados**, de **6.469 cartas**.

---

## 2 · A ARQUITETURA — o que foi decidido hoje

```
vigia coleta  ->  sobe INSUMO pro banco (Supabase)
                        |
                   motores LEEM do banco  ->  processam
                        |
                   resultado volta pro banco
                        |
          +-------------+-------------+
          |                           |
   tela do ADMIN (o Luis)      tela dos USUÁRIOS  <- é a que você vai desenhar
   arquivo com dados dentro    só interface, consulta ao vivo
   abre sem internet           precisa de internet
```

**A regra que manda em tudo:** o banco é a origem e o destino. Arquivo em computador é cópia descartável, nunca fonte. Nada de dado embutido no HTML.

O motivo é concreto: a tela antiga (a que ainda existe, `encaixe_v6_NOVO.html`) tem **39,1 MB**, sendo 36 MB de dados colados dentro. Ela congela no instante em que é gerada. A tela nova tem **15 KB** — 2.490 vezes menor — porque consulta em vez de carregar.

---

## 3 · COMO PEGAR OS DADOS

O Supabase expõe as tabelas por REST (PostgREST). Não precisa de biblioteca, `fetch` puro resolve.

```js
const URL  = 'https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/';
const CHAVE = 'sb_publishable_XTKGboY9RyYiirPiIsWMhw_P8B51cHj';
const H = { apikey: CHAVE, Authorization: 'Bearer ' + CHAVE };

const r = await fetch(URL + 'builds?select=card_id,funcao,b1&order=b1.desc&limit=50', { headers: H });
const linhas = await r.json();
```

**Sobre a chave:** ela é pública de propósito e pode ficar no HTML. Foi medido em 17/08 — ela **lê 14 tabelas e não escreve em nenhuma**. Tentativa de INSERT devolve `HTTP 401 · 42501`. O que protege o banco não é a chave estar escondida, é a regra (RLS).

**Filtros úteis do PostgREST:**

```
?funcao=eq.Ponta criadora          igual
?b1=gte.400                        maior ou igual
?card_id=in.("123","456")          lista
?nome=ilike.*messi*                busca sem acento-sensível
?order=b1.desc&limit=300           ordenar e limitar
?select=card_id,nome,ovr           só as colunas que você usa
```

### ⚠️ Três armadilhas medidas

1. **O PostgREST corta em 1000 linhas por resposta**, calado. Pedir 5.000 devolve 1.000 sem avisar. Pagine com `limit` + `offset`.
2. **Filtre no banco, não no navegador.** São 12.370 builds. Trazer tudo pra filtrar no cliente é exatamente o vício que fez o HTML antigo ter 39 MB.
3. **A URL tem limite de tamanho** — `in.(...)` com muitos ids estoura. Quebre em lotes de ~150.

---

## 4 · O CONTRATO — as 14 tabelas liberadas

Tabela que não estiver nesta lista **não responde** para essa chave. Se precisar de outra, tem que pedir ao Luis (é um comando SQL).

### `builds` — 12.370 linhas · **a tabela principal**
Um registro por **carta × função**.

```
card_id  funcao  b1  barras  impeto  tecnico  tecnico_id  habilidades
cadeia  vals  vals_carta  vals_tela  buff  cond  origem  estilo
sobra  insumos  versao  motor_versao  rodado_em  lote  na_fila  migrado
funcao_codigo  alvos  frows  tec_boost  bonus_corpo  bonus_ia  pun_estilo
nota  b1n  b2  b4  b5  b4r
```

⛔ **`nota`, `b1n`, `b2`, `b4`, `b5`, `b4r` estão TODAS NULL.** São resto de versões antigas do motor. **A nota é o `b1`.** Conferido nos três primeiros registros do ranking.

⚠️ **`funcao_codigo` está preenchida só em parte** — o primeiro registro do ranking tem `null`. Não use como chave; use `funcao` (o nome).

Campos que interessam pra tela:

| campo | o que é |
|---|---|
| `b1` | **a nota do motor**. É o número que ranqueia. |
| `barras` | quais barras de progressão subir, e quanto |
| `impeto` | lista. ex: `["Passe +1"]` |
| `tecnico` + `tecnico_id` | o técnico escolhido. **Use o id**: existem 5 "Jose Mourinho" diferentes |
| `habilidades` | lista das 5 habilidades que o motor escolheu |
| `origem` | `"nativa"` ou `"comprada:PE"` — se a função é natural da carta ou comprada |
| `estilo` | o estilo de jogo (ex: "Armador criativo") |
| `vals` / `vals_carta` / `vals_tela` | os 26 atributos finais, em três versões |

### `bonus` — 12.199 linhas
O bônus que soma na nota, também por carta × função.

```
card_id  funcao  b_corpo  b_pe_ruim  b_estilo  b_ia  b_total
corpo_soma  corpo_pct  detalhe  motor_bonus  rodado_em
```

**A nota que o usuário vê = `builds.b1` + `bonus.b_total`.**

⚠️ Existe um campo `faltou` (lista do que não foi possível medir) que **ainda não subiu para o banco** — está pendente uma coluna. Enquanto isso, `b_total` pode estar incompleto em algumas cartas, sem sinalização. É uma pendência conhecida.

### `cards_base` — 6.469 linhas
A carta em si. 90 colunas. As que interessam:

```
card_id  nome  ovr  max_ovr  tier  votos
posicao  posicao_nativa  posicoes_sec  estilo_de_jogo
orcamento  level_cap  atributos_base (lista de 26)
atr_ofensividade ... atr_alcance   (as 26 explodidas em coluna)
impeto_efeito  impeto_nomes  impeto_nativo  vagas_impeto  vaga_detalhe
hab_nativas  hab_faltantes  hab_raras
corpo  pe  altura  peso  pe_ruim  idade  forma  condicao
box  data_lancamento  boost_id  origem_ficha
```

⚠️ **Alguns `card_id` têm sufixo**, tipo `"57309@ZC"`. É variante da mesma carta. Ao cruzar com `builds`, corte no `@`.

### `funcoes` — 19 linhas
```
nome  familia  posicoes  codigo  rotulo  rotulo_curto  grupo  sigla_posicao
```
Tem `rotulo_curto` e `grupo` — bom para chips e agrupamento na interface.

### As outras nove (receita e apoio)
```
insumo_molde ........... 494   o alvo e o peso de cada atributo por função
insumo_habilidade ....... 65   o efeito de cada habilidade (44 comuns, 21 raras)
insumo_tecnico ....... 1.664   os técnicos
insumo_impeto_catalogo .. 58   os ímpetos que dá pra fabricar
insumo_bloqueio ........ 246   que habilidade não entra em que função
insumo_regra_funcao ...... 2   posição -> funções que ela pode ocupar
insumo_player_type ..... 137   o tipo da carta (Standard, POTW, Epic…)
campanha ................ 37   as box e as cartas de cada uma
estilo_valor ........... 144   quanto vale cada estilo em cada função
traducao ............... 438   de-para de nomes
```

---

## 5 · O VOCABULÁRIO — não traduza, não invente sinônimo

O Luis usa esses termos e **exige que ninguém fale em sigla com ele**. A interface deve usar as palavras dele:

| termo | significa | ⛔ não diga |
|---|---|---|
| **função** | um dos 19 ofícios (Ponta criadora, Volante de contenção…) | "role", "posição" |
| **nota** | o `b1`. Quanto a carta serve àquela função | "score", "rating" |
| **molde** | o alvo de atributos que define a função | "template" |
| **ímpeto** | o booster do jogo | "boost", "booster" |
| **vaga de ímpeto** | o espaço pra fabricar um ímpeto | "slot" |
| **barrinha / barra** | a barra de progressão que se sobe com pontos | "level bar" |
| **habilidade** | as skills. **comuns** competem, **raras** somam | "skill" |
| **espaço de habilidades** | quais habilidades a carta pode adicionar | "pool" |
| **pé ruim** | o pé não dominante | "weak foot", "wf" |
| **estilo de jogo da IA** | o comportamento quando o computador controla | "AI style", "com" |
| **carta** (não "card") | um jogador colecionável | — |
| **box / campanha** | o pacote de onde a carta veio | "banner" |

**Regra do Luis, escrita na memória do projeto:** *"nunca falar com o Luis em sigla"*. Vale para a interface também.

---

## 6 · A TELA v1 QUE JÁ EXISTE

Está em `truefootball-motor-v6\encaixe-web\index.html`, **15,3 KB**, testada contra o banco real. Ela é um ponto de partida funcional, **não um desenho aprovado** — sinta-se livre pra refazer a aparência inteira. O que ela já resolve e vale preservar em comportamento:

- **Consulta filtrada no banco** (função, tier, busca por nome, quantidade)
- **Tabela ordenável** por carta, ovr, função, nota
- **Detalhe expansível** na linha: nota decomposta (motor + bônus), técnico, ímpeto, estilo, as 5 habilidades, id
- **"Meu time"** — o usuário clica numa ★ e a carta entra no time dele, guardado **no navegador dele** (`localStorage`), com queda para memória se o navegador recusar
- **Erros em português**, explicando a causa provável (permissão, rede, configuração)

**Um comportamento que parece bug e não é:** marcar 1 carta acende várias estrelas. Certo — o time é por **carta**, e a mesma carta aparece em várias funções.

---

## 7 · O QUE AINDA NÃO EXISTE — e é onde o design entra

1. **Login.** Decisão do Luis, 17/08: *"cada usuário vai ter o seu [time]. A pessoa entra, se ela não fizer login ela usa e depois apaga, ficando no navegador dela. Se quiser guardar, precisa de login."*
   Quando entrar, o time vai pra uma tabela por usuário com regra de linha (`auth.uid()`). Na tela atual só mudam duas funções de dez linhas.

2. **Onde publicar.** Ainda não decidido. O Luis usa **Netlify** nos outros sistemas dele (arrasta o `index.html` no Netlify Drop). É o caminho natural.

3. **A tela do admin** continua sendo o arquivo grande e offline. Não é seu escopo, mas saiba que existe e que ele **precisa** dela funcionando sem internet, pra manutenção.

4. **Comparar cartas**, gráficos de atributo, o simulador de build — nada disso existe na v1.

---

## 8 · REGRAS QUE NÃO PODEM SER QUEBRADAS

⛔ **Nada de escrita pelo navegador.** A chave pública não escreve, e é assim que fica. Qualquer coisa que grave passa pelos programas do Luis, com a chave secreta.

⛔ **A chave do `config.txt` nunca entra em arquivo de tela.** Ela é a `service_role`, escreve em tudo e ignora as regras de proteção.

⛔ **Nada de dado embutido no HTML.** Foi a causa dos 39 MB. Se o desenho precisar de um dado, ele vira consulta.

⛔ **Não inventar número.** Regra do Luis, 15/08: *"quando não souber o número, tem que avisar que não foi possível puxar. Não tem que inventar número velho, tem que falar não sei."* Campo vazio na tela mostra "não sei", nunca zero.

---

## 9 · COMO O LUIS TRABALHA — importante pra entrega

- Ele **não é programador** e **nunca usa terminal**. Tudo por navegador: GitHub online, Netlify, Supabase, Railway.
- Ele quer **arquivos completos**, prontos pra copiar e colar. Nunca trecho solto, nunca "só a parte que mudou".
- Ele quer **passo a passo numerado com links clicáveis**.
- Ele responde em português e espera resposta em português.
- Ele valoriza **medição acima de opinião**. Se você afirmar algo, tenha o número.

---

## 10 · UM TESTE RÁPIDO PRA VOCÊ CONFERIR QUE ESTÁ TUDO VIVO

Cole no console do navegador, em qualquer página:

```js
const K='sb_publishable_XTKGboY9RyYiirPiIsWMhw_P8B51cHj';
const U='https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/';
const H={apikey:K,Authorization:'Bearer '+K};
const b=await (await fetch(U+'builds?select=card_id,funcao,b1&order=b1.desc&limit=5',{headers:H})).json();
console.table(b);
```

Em 17/08 isso devolvia, no topo: **Ponta criadora 466,8** (carta `89136409091415`) e **Ponta criadora 460,1** (`89138288266704`). Se voltar isso ou parecido, está tudo ligado.
