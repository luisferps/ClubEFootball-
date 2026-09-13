# CONTRATO DA FICHA — o que falta o banco publicar

> **A regra, na palavra do Luis (04/09):**
> *"Essa tela de ficha não tem que fazer conta, ela não tem que fazer nada. As contas
> que vêm quando eu clico numa função têm que vir direto do banco de dados. A única
> coisa que ela recalcula é quando o cara mexe nas barrinhas, nas habilidades, nos
> ímpetos que dá pra mexer e no técnico — aí ela chama o espelho do motor. E quando
> ele clicar em gravar, tem que gravar o espelho da tela do jeito que está."*

Este documento é a lista do que o motor precisa passar a gravar para essa regra valer.
**Enquanto esses campos não existirem, a tela não tem como parar de calcular** — apagar
os cálculos hoje deixa metade da ficha em branco.

---

## 1 · O QUE JÁ FOI RESOLVIDO (04/09)

Três números estavam publicados no banco **e mesmo assim** eram recalculados na tela,
em cima do catálogo congelado do `dados-e-catalogos.js`. Davam outro resultado.

Medido no James Rodríguez (`106788187841133` · Meia ofensivo · nota 109.09):

| na tela | o banco tem | a tela mostrava | fonte errada |
|---|---|---|---|
| ESTILO DE JOGO DA IA · TOTAL | `bonus_ia` = **+0.7500** | 0.00 | `BONUS_PRONTO` |
| FÍSICO · TOTAL | `bonus_fisico_total` = **+0.2812** | 0.00 | `CORPO_MOTOR` + `CORPO_MOLDE` |
| PÉ · bônus | `bonus_pe` = **+0.1400** | recalculado | `PR_TAB` |

Os três agora são lidos de `__cn.bonusComponentes`, que o contrato de leitura já
entregava e **nenhuma tela consumia**.

Junto, dois textos que eram do molde da designer e apareciam iguais em toda carta:

- os chips "Passe cortante · Driblador incisivo · Jogo de infiltração" — agora saem de
  `estilos_ia` (contrato da Ficha), que existia e nunca era desenhado
- a linha "3 de 5 · bônus +0.9 na nota" — removida; quem diz o bônus é o TOTAL, lido

Onde a linha publicada não trouxer o valor, a tela agora escreve **"não apurado"** —
regra 3 do sistema: nunca zero, nunca inventado.

---

## 2 · O QUE FALTA PUBLICAR — por ordem de dor

### 2.1 · A decomposição por etapa de cada atributo 🔴

A tabela de atributos tem 13 colunas. O banco publica só o **vetor final**
(`atributos_finais`) e o `arows_snapshot` (índice, peso, alvo, final, delta). As colunas
do meio são **todas reconstruídas no navegador**:

```
Base · +barras · +ímpeto · +técnico · Na tela · +hab. nativas · +hab. adicionadas
```

Quem reconstrói: `etapas()` (`motor-e-ficha-base.js:3983`) e `_e4nat()` (`:4004`),
usando `c.base` e `c.nm` — que vêm de **outro contrato** (a Ficha física), não da build.

**Publicar:** `atributos_etapas` — por linha de build, 26 posições × 5 etapas
(`e0` base, `e1` após barras, `e2` após ímpeto, `e3` após técnico, `e4` após habilidades),
mais o valor após as **nativas** separado do valor após as **adicionadas**.

### 2.2 · A coluna "Pontos" de cada atributo 🔴

`ptsAttr()` (`motor-e-ficha-base.js:1503`) roda a régua `P.DEG` (`:896`) no navegador.
A régua é do molde — **segredo industrial, sem leitura pública**. A tela não deveria
nem conseguir rodar isso.

**Publicar:** `pontos_por_atributo[26]`, ou um sexto elemento em `arows_snapshot[i]`.

### 2.3 · As 12 medidas do corpo 🔴

Nada em `BUILD_FIELDS` descreve as medidas. Existe só o agregado `bonus_fisico_total`.
As 4 colunas (Avaliação, No card, Ideal, Na nota) saem de `CORPO_MOTOR` e `CORPO_MOLDE`,
congelados no `dados-e-catalogos.js`.

**Publicar:** `fisico_medidas[]` com
`{medida, valor_no_card, alvo, avaliacao, peso, direcao, pontos}`.

### 2.4 · Os estilos de IA que contaram 🟡

`bonus_ia` existe, mas não **quais** estilos entraram e quanto cada um valeu.

**Publicar:** `ia_estilos[]` com `{nome, codigo, pontos}`.

### 2.5 · Nível, gasto e custo por barra 🟡

`nivel_total` e `pontos_gastos` não existem — a tela soma (`ficha-ajustes.js:2079`) e
chama `gastoDe()` (`motor:268`). O custo por barra é a curva `ceil(k/4)` reimplementada
em `ficha-ajustes.js:2071`. O `orcamento` existe, mas no contrato **da Ficha**, não no
da Build (`clube-novo-read-model.js:904` zera o `orc` da build).

**Publicar:** `nivel_total`, `pontos_gastos`, `orcamento` e `barras_custo` por chave.

### 2.6 · O teto da função — o "PODE MELHORAR" 🟡

`topo_funcao` e `pontuacao_otimizador_bruta_evidencia` são **deletados de propósito**
pelo contrato (`clube-novo-read-model.js:929-931`). Sem eles o indicador é
estruturalmente **sempre 0%** (`ficha-ajustes.js:2299-2308`) — não é conta errada, é
conta sem insumo.

**Publicar:** o percentual já resolvido, ou o teto da função para esta carta.

### 2.7 · Ímpeto: nome, efeitos e o condicional 🟡

O contrato aceita só `impeto_adicional_codigo` — **o código, sem nome nem efeito**.
Os campos `impeto_adicional` e `impeto_condicional` **existem na RPC e são descartados**
pelo `BUILD_FIELDS` (`clube-novo-read-model.js:99-115`). O condicional (`c.CD`, `c.cmode`)
não existe em contrato nenhum, então o bloco dele nunca aparece.

**Publicar:** aceitar `impeto_adicional` e `impeto_condicional` no contrato — o banco
já manda.

### 2.8 · Os boosts do técnico 🟡

`tecnico_id` e `tecnico_nome` existem; **quais atributos ele mexe, não**. `c.TECB` é
zerado (`clube-novo-read-model.js:895`) e a linha de efeitos vira "sem técnico".

**Publicar:** `tecnico_boosts[]` com `{indice_otimizador, delta}`.

### 2.9 · Pé ruim: os rótulos 🟢

`pe_ruim_uso` e `pe_ruim_precisao` existem no contrato da Ficha, mas a tela ignora e lê
a tabela hexadecimal `PR_RAW` (`motor-e-ficha-base.js:1149`). É só passar a ler o que
já chega.

### 2.10 · Habilidades especiais e o pool de sugestões 🟢

`raras` e `NEU` são zerados (`clube-novo-read-model.js:900`). A tela mostra "nenhuma" e
"o motor ainda não mediu as trocas" para toda carta.

---

## 3 · O QUE A TELA PODE CONTINUAR CALCULANDO

Uma exceção, e só ela: **o espelho do motor.**

Vale quando o usuário mexe em algo que ele pode mexer:

```
as barrinhas (arrastar a trilha, ou os − / +)
as habilidades adicionadas
o ímpeto adicional
o técnico
```

Aí a tela chama `distOtima` / `buildOtimo` / `_grava` / `notaDe` e recalcula ao vivo.
As portas: `ficha-ajustes.js:3297-3336` (arrasto), `:3338-3341` (± ), `:3582-3594`
(OTIMIZAR), `:3343-3350` (chips de habilidade).

**Fora dessas quatro ações, nenhuma conta.** Clicar numa função é leitura do banco.

---

## 4 · O GRAVAR

Ordem do Luis: quando o usuário clica em **SALVAR MINHA BUILD**, grava-se o **espelho
da tela como ele está** — as barras que estiverem, as habilidades que estiverem, o
ímpeto e o técnico que estiverem. Não é regravar a build publicada: é a build **dele**.

Existe um módulo Python separado para essa escrita. A tela só entrega o espelho.

---

## 5 · O TESTE DE ACEITE

A ficha está certa quando, com a rede desligada logo após a carga:

1. clicar em qualquer função da lista **não muda nenhum número** que não estivesse na
   linha publicada daquela função;
2. nenhuma célula da tela vem de `dados-e-catalogos.js`;
3. onde a linha publicada não tem o campo, a tela escreve **"não apurado"** — nunca 0;
4. mexer numa barrinha muda os números; **soltar sem salvar e reabrir devolve o que o
   banco tem**.
