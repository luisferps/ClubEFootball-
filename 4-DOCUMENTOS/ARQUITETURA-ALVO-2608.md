# ARQUITETURA-ALVO DO BANCO — 26/08/2026 17:40

> Ordem do Luis: *"a gente só precisa de uma tabela com os dados do jogador, e as
> tabelas com os catálogos. Depois tabelas auxiliares, moldes. O restante apaga tudo."*
>
> **NADA FOI APAGADO.** Este documento é o desenho + o mapa de acoplamento.
> Sequência mandada pelo Luis: **1)** desenhar · **2)** varrer o código das que saem ·
> **3)** corrigir o código · **4)** só então apagar.

---

## 1. O DESENHO

```
JOGADOR         clube.carta                  ← UMA tabela, o dado do jogo
  filhas 1:N    carta_impeto
                carta_habilidade
                carta_posicao_comprada

CATÁLOGOS       estilo · impeto · impeto_efeito · impeto_fabricavel
(o dicionário   habilidade · habilidade_rara_valor · tecnico · box
 do jogo)       funcao · posicao · atributo · tipo_carta
                barra · multiplicador · custo_nivel · formacao · traducao

AUXILIARES      molde · molde_corpo · receita_versao
(o método)      parametro · bonus_parametro · regua_parametro
                bloqueio · corpo_ordem · ordem_boost_tecnico
                regra_completude · estilo_valor
                estilo_regra          ← NOVA (funde 3)
                posicao_slot

RESULTADO       build · elenco_luis · usuario_estado

TRAVA           migracao · valor_do_dono · divergencia_conhecida
```

**70 tabelas hoje → 41.**

---

## 2. O QUE ACONTECE COM CADA UMA

### 2.1 FUNDE (o dado vive, a tabela some) — 5

| some | vai para | por quê |
|---|---|---|
| `carta_jogo` (42.803) | **`carta`** | mesmos jogadores em dois lugares. A `carta_jogo` tem o dado NOVO e ninguém lê; a `carta` é lida por tudo e está com a extração velha. **O dado da `carta_jogo` vence** — ela é promovida, não apagada. O nome `carta` sobrevive só porque as FKs e o gerador apontam para ele. |
| `carta_box_jogo` (11.522) | coluna `box` da `carta` | a box já existe como coluna na `carta_jogo` |
| `bonus_posicao_regra` (60) | **`estilo_regra`** | mesma informação repartida |
| `regra_posicao_estilo` (2) | **`estilo_regra`** | idem |
| `estilo_funcao` (57) | **`estilo_regra`** | criada hoje; entra na fusão |

### 2.2 NASCE — 1

**`clube.estilo_regra`** — a regra de estilo num lugar só:

```
estilo · posicao · funcao_codigo (a casa; null = não roteia) · da_bonus (bool)
```

Hoje isso está em três tabelas: `bonus_posicao_regra` (onde o estilo liga),
`regra_posicao_estilo` (o interruptor gatilho→função) e `estilo_funcao` (a casa).

### 2.3 APAGA — 24

**Duplicatas do jogador (5):** `carta_velha_2608` 3.269 · `carta_meta` 98 ·
`carta_impeto_arroba` 7.368 · `carta_habilidade_arroba` 75.406 · `carta_tipo_legado` 137

**Catálogos de estilo repetidos (4):** `estilo_jogo` 52 · `estilo_defensivo` 14 ·
`estilo_defensivo_ref` 13 · `estilo_jogo_traducao` 25

**Regras espalhadas (3):** `regra_funcao` 24 · `posicao_funcao_sugerida` 27 ·
`funcao_apelido` 14

**Andaime da coleta velha (9):** `proveniencia` 1.650 · `campo_fonte` 34 · `coleta` 3 ·
`extracao` 2 · `fotografia` 23 · `impeto_divergencia` 870 · `achado_motor` 32 ·
`habilidade_incidencia` 1.139 · `prova_avaliador` 11

**Vazias (6):** `jogo_variacao` · `jogo_ficha` · `perda_evitada` · `recebimento` ·
`_busca_tmp` · `tatica_time_traducao`

---

## 3. O MAPA DE ACOPLAMENTO (varredura feita em 26/08 17:40)

### 3.1 A TELA NÃO FALA COM O BANCO

Varri `motor-e-ficha-base.js`, `elenco.js`, `ficha-ajustes.js`,
`modulos-elenco-paginas.js`, `paginas-e-navegacao.js`, `user-state-repository.js`:
**zero `fetch`, zero cliente Supabase, zero nome de tabela em contexto de consulta.**

Os dados chegam embutidos no **`dados-e-catalogos.js`** (1,5 MB), que é **gerado**.

> **Consequência:** mexer em tabela **não quebra a tela**. Quebra o **gerador** do
> `dados-e-catalogos.js`. É lá que a correção tem que ser feita.

### 3.2 O AVALIADOR (Railway) NÃO TOCA TABELA

`6-AVALIADOR-NO-RAILWAY/banco.py` é a única porta e usa **três RPCs**:

- `public.regua_pacote()`
- `public.carta_para_simular(p_card_id)`
- `public.pool_da_funcao(p_card_id, p_funcao)`

> **Consequência:** o avaliador não quebra por mudança de tabela, desde que as três
> RPCs continuem devolvendo o mesmo formato.

### 3.3 O ALIMENTADOR

`3-ALIMENTADOR/index.html` chama `public.receber_lote` e `public.estado_da_caixa` —
as duas leem `clube.recebimento`, que está **vazia** e está na lista de apagar.
**Conferir se o alimentador ainda é usado antes de apagar.**

### 3.4 O EXTRATOR

`VER DADOS DO JOGO/Extrator-ClubEfootball.html` gera INSERT para **`carta_jogo`** e
cita `estilo_jogo`. Com a fusão, ele passa a gerar para **`carta`**.

### 3.5 FUNÇÕES DO BANCO QUE LEEM AS CONDENADAS

| tabela condenada | usada por |
|---|---|
| `carta_jogo` | `clube.refresh_jogo_aplicar` |
| `proveniencia` | `clube.refresh_jogo_aplicar` |
| `campo_fonte` | `clube.auditoria_cobertura` |
| `impeto_divergencia` | `clube.auditoria_completa` |
| `regra_funcao` | `clube.auditoria` |
| `perda_evitada` | `clube.aplicar_recebimento` |
| `recebimento` | `clube.aplicar_recebimento`, `clube.conferir_recebimento`, `public.estado_da_caixa`, `public.receber_lote` |
| `jogo_ficha` | `public.receber_ficha_do_jogo` |

**São 9 funções a ajustar.** Três delas são a auditoria — se apagar sem ajustar, a
trava de qualidade quebra. `refresh_jogo_aplicar` foi superada pelo apaga-e-coloca e
provavelmente morre junto.

---

## 4. ORDEM DE EXECUÇÃO (nada feito)

| # | passo | risco |
|---|---|---|
| 1 | Criar `estilo_regra` e migrar as 3 tabelas de regra para ela | baixo |
| 2 | Apagar as 6 vazias + o andaime que ninguém lê | baixo |
| 3 | Ajustar as 3 funções de auditoria (`campo_fonte`, `impeto_divergencia`, `regra_funcao`) | médio — mexe na trava |
| 4 | Apagar os 4 catálogos de estilo repetidos e as 5 duplicatas do jogador | médio |
| 5 | **Fundir `carta_jogo` na `carta`** + `carta_box_jogo` | alto — é o dado |
| 6 | Ajustar o **gerador do `dados-e-catalogos.js`** e o **Extrator** | alto — é o que a tela come |
| 7 | Conferir as 3 RPCs do avaliador | médio |

Auditoria (`clube.auditoria_completa()`) entre cada passo. **FALHA = para.**

---

## 5. O QUE A FUSÃO DA `carta` RESOLVE DE QUEBRA

- **1.014 cartas** com `estilo_codigo` diferente do slot ofensivo — some, porque passa
  a existir uma foto só.
- **1.399 cartas** que estão na `carta_jogo` e nunca entraram na `carta`.
- Os **dois slots de estilo** ficam onde o motor lê, destravando a regra de 26/08.

---

*Documento de 26/08/2026 17:40. Desenho e varredura feitos; nada executado.*
