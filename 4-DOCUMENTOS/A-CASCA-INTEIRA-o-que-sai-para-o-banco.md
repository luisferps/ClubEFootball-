# A CASCA INTEIRA — o inventário do que tem que sair para o banco
**25/08/2026.** Ordem do Luis: *"esses dados que a gente usa, que a gente mostra, eles
vivem dentro dessa casca, eles têm que sair — foi a primeira coisa que eu te pedi. Os
cálculos também… Você tem que dar uma lida nela INTEIRA, se for só por alto você vai errar."*

**Foi lida inteira:** 9 arquivos · **3.088.952 bytes** · **~14.500 linhas**, linha por linha.
Tudo abaixo é medido.

---

## O RETRATO EM UMA TABELA

| arquivo | tamanho | quanto dele é DADO/TEXTO congelado |
|---|---:|---:|
| `dados-e-catalogos.js` | 1.579 KB | **1.532 KB — 99,3%** (8 constantes em 8 linhas) |
| `motor-e-ficha-base.js` | 751 KB | **495 KB — 66%** |
| `ficha-ajustes.js` | 339 KB | **~110 KB — 32%** (94 KB só do molde das telas) |
| `elenco.js` | 242 KB | ~18 KB (CSS + tabelas de regra) |
| `modulos-elenco-paginas.js` | 87 KB | ~14 KB |
| `paginas-e-navegacao.js` | 30 KB | ~4 KB (a Home inteira em string) |
| `index.html` | 26 KB | **25 KB — 97% inline** (+145 linhas em branco) |
| `como-funciona.js` | 8 KB | 4,5 KB (texto editorial puro) |
| `user-state-repository.js` | 19 KB | 0 — é o único arquivo limpo |
| **TOTAL** | **3.089 KB** | **≈ 2.200 KB — 71% da casca é dado e texto, não lógica** |

E os 8 scripts carregam **síncronos, sem `defer`, sem `async`** (index.html linhas 331-338):
3,0 MB travando o parser **antes** de a tela pedir a primeira linha ao banco.

---

# PARTE 1 · OS DADOS — o que sai, para onde, e o que ainda não tem casa

## 1.1 · SAI HOJE, o banco já tem tudo (**≈ 1.630 KB, 74% do dado congelado**)

| constante | onde | KB | vai para |
|---|---|---:|---|
| `BONUS_PRONTO` | dados-e-catalogos:9 | **1.050,0** | `clube.build` — `b_corpo/b_pe_ruim/b_estilo/b_ia` (17.798 linhas) |
| `BOXHIST` | motor:3020 | **191,7** | `clube.box` (2.014) + `carta.box_id` — e os 6.731 ids dela **nunca são lidos** |
| `PACOTE` | motor:420 | **150,6** | `clube.box` + `carta.box_id` |
| `CORPO_MOTOR` | dados:10 | **126,6** | `clube.carta.corpo` — **99 de 99 ids conferidos existem no banco** |
| `PR_RAW` (pé ruim) | motor:1148 | **54,1** | `clube.carta.pe_ruim_uso` / `pe_ruim_precisao` |
| `PIMP` | dados:155 | 30,2 | `clube.impeto` (430) + `impeto_efeito` (2.158) + `carta_impeto` (13.904 · o JS só tem 1.340 cartas) |
| `FILA` | motor:399 | 28,8 | `clube.habilidade` + `molde` — ⚠️ falta a **incidência %** |
| `B5V` | motor:400 | 8,2 | `clube.molde` — ⚠️ o valor por função precisa conferência |
| `CORPO97` | motor:419 | 6,5 | `clube.carta.corpo` |
| `ESTV` | motor:316 | 6,2 | `clube.estilo_valor` — a função que a usa **está morta** |
| `MF_DIRF` | motor:543 | 6,5 | `clube.molde` (é o molde do físico) |
| `CAT` (ímpetos) | motor:247 | 5,7 | `clube.impeto` + `impeto_fabricavel` (58) |
| `FIS_P` | motor:414 | 5,2 | `clube.molde` |
| `FIS_M` | motor:413 | 3,9 | `clube.carta.corpo` |
| `HABM` (65) | motor:3620 | 3,4 | `clube.habilidade` — **bate exatamente: 65 = 65** |
| `TECS` (124) + `window.TECS` (64) | motor:747 e 3243 | 4,4 | `clube.tecnico` (1.664) |
| `HABEF` (151) | motor:759 | 2,4 | `clube.habilidade` — ⚠️ **151 > 65: a tela conhece MAIS habilidade que o banco** |

## 1.2 · SAI, mas o banco precisa receber carga antes

| constante | KB | o que falta |
|---|---:|---|
| `CORPO_EFHUB` | **308,1** | tem **10.056 cartas**; `clube.carta` tem 6.953 — numa amostra de 101 ids, **só 21 existem no banco**. É a coleta que falta (o marco zero) |
| `MEU_TIME` (114 ids) | 1,9 | é o elenco do Luis **cravado no código** — vai para `clube.usuario_estado` |

## 1.3 · PRECISA NASCER NO BANCO — hoje não existe em lugar nenhum

Esta é a lista que importa: **se a casca sumisse, isto se perderia.**

| o quê | onde | o que é |
|---|---|---|
| `CORPO_MOLDE` | dados:12 | **o molde do CORPO**: 32 funções × 12 medidas, com direção, peso, alvo e os 4 cortes. `clube.molde` só tem os 26 atributos — **as medidas do corpo não têm molde no banco** |
| `CORPO_ORDEM` + `MF_ARQIDX` | dados:11 / motor:556 | a ordem das 12 medidas — é a **chave de leitura** do array `carta.corpo`. Sem ela o array é ilegível |
| `TJ_SA` | dados:64 | 22 estilos que decidem se um Segundo atacante joga como meia ou centroavante |
| `MT_FORM` | motor:1674 | **17 formações táticas** com as coordenadas x,y das 11 vagas |
| `MT_FUNCS` · malha do campo · `opcoesDaVaga` | motor:1660 · elenco:1970-1994 | que posição cabe em que região do campo |
| travas de composição | elenco:1995-2005 | máx 3 ZC, 1 MLE, 1 MLD, 2 CA, 1 PE, 1 PD |
| `SA ↔ CA` intercambiáveis | elenco:1937 | regra de vaga |
| `METAS` (98 jogadores) | motor:22 | a lista curada de cards "meta" |
| `SET`/`SIG`/`ROT`/`FAM` | motor:22 | a árvore 4 setores → 10 grupos → 19 funções do Ranking |
| `_NOME_NA_TELA` (14) · `siglaTela` (5) · `_POR_EXTENSO` (10) · `NOMEGRUPO` (2) | ficha:1113 · 249 · 1086 · elenco:1168 | **os nomes novos das funções** — o comentário admite: *"o banco continua com a chave velha, o motor não sabe que o nome mudou"* |
| `CLS_F` + `_stCls` | ficha:1002-1046 | a escada peso → Indispensável/Desejável/Útil/Acessório + cor e desenho |
| os 4 estados do semáforo do Elenco | elenco:2380-2394 | cor **e a frase** de cada estado |
| as 6 etiquetas de contratação | ficha:744 e 806 | os nomes vêm do banco; **os cortes (99/98/97/96) e as cores, não** — em duas cópias divergentes |
| `player_id = card_id mod 8.388.608` | elenco:1425 | a regra que identifica duas versões do mesmo jogador |
| `TETO_TIT` 11 · `TETO_BANCO` 12 · `TETO_BUILDS` 30 · teto 5 habilidades | vários | limites do produto |
| `GRUPOS` (26 atributos em 4 setores) · `colsAttr` (13 colunas) · `T6_CAMPO` (7×3) | ficha:2286 · 2382 · 950 | organização da ficha |
| **todo o texto editorial** | ficha:187 (94 KB) · como-funciona (4,5 KB) · paginas (3 KB) | a tela "Como funciona" inteira, a Home, a régua verbal *"CONTRATAR ≥99% · SE SOBRAR 96-99% · DEIXA PASSAR <96%"*, os ~10 balõezinhos, os 3 textos de estado de ímpeto, os 3 de vaga, os 3 de sugestão, as ~25 mensagens de erro |

---

# PARTE 2 · AS CONTAS — o que já é duplicata do motor

## 2.1 · A TELA REFAZ O QUE O MOTOR JÁ FEZ (sai inteiro)

| conta na tela | linhas | o motor Python que já faz |
|---|---|---|
| `notaDe` (a régua de 9 degraus) | motor:257 | `regua.py:145` — **idêntica** |
| `_bon` / `_fal` (bônus e punição) | motor:896 | `regua.py` |
| `aplicar` (base + barras, teto 99) | motor:259 | `equacao.py:256` |
| `custoNivel` / `gastoDe` | motor:253 · ficha:2280 | `equacao.py:95` — **duplicata literal, em dois arquivos** |
| `buffDe` / `buff` (regra da metade) | motor:765 e 3629 | `equacao.py:205` — **duas cópias na tela** |
| `cadeia` / `conta` (a Equação 1) | motor:793 e 3669 | `equacao.py:265` |
| `distOtima` / `buildOtimo` | motor:262-314 | `motor.py:_dp` — o próprio comentário diz que **a da tela é mais fraca** |
| `corpoSoma/Pct/Impacto` | ficha:2355 | `motor_bonus.py:289` — **duplicata literal, com o mesmo clamp ±100** |
| `prBonus` (pé ruim) | motor:1158 | `motor_bonus.py:314` |
| `iaBonus` (estilo da IA) | motor:1133 | `motor_bonus.py:340` |
| `estiloAtiva`/`bonEstilo` | motor:373 | `motor_bonus.py:329` |
| `pct` / `topoDoTipo` (% do topo) | ficha:240 · motor:1284 | **`clube.topo_funcao` — a view já existe e a tela recalcula assim mesmo** |
| `pctDoMolde`/`b1n` | elenco:3412 · ficha:1441 **e** 3285 | `equacao.py` — **a mesma fórmula escrita 2× só na ficha** |
| `achaM` | motor:3685 | descobre **por força bruta** qual dos 6 multiplicadores o motor usou — bastava o banco gravar o `m` |
| `_notaDoMotor` | ficha:1256 | **desmonta e remonta o card inteiro** para reobter um número que o motor já gravou |
| `notaMed` (mediana) | motor:1191 | **`clube.mediana_funcao` — a view já existe** |

## 2.2 · O QUE NÃO PODE SAIR (é o usuário mexendo, na hora)

Barras arrastadas · ímpeto escolhido · técnico escolhido · até 5 habilidades adicionadas ·
os pesos `W` dos 5 blocos · o degrau do ímpeto condicional · as 3 abas (Máximo / Com o que
eu tenho / Do meu jeito) · a escalação, a formação e as builds salvas do Elenco.
**Isto é conta de simulação: continua na tela — mas lendo régua e catálogo do banco, não de
constante congelada.**

---

# PARTE 3 · O QUE A LEITURA ACHOU DE ERRADO (não estava na lista de ninguém)

1. **O `BONUS_PRONTO` da tela é uma FOTO VELHA.** Tem **17.463** pares; o banco tem **17.798**
   — **335 a menos**. E as faltas não batem: no JS 385 sem bônus de IA, no banco 566. A tela
   está mostrando bônus de uma geração anterior.
2. **Três alturas diferentes para a mesma carta.** `CORPO97` × `CORPO_MOTOR`: **67 das 97
   divergem**. `FIS_M` × `CORPO_MOTOR`: **48 das 58 divergem**. Três tabelas de corpo no
   código, discordando entre si.
3. **A tela conhece 151 habilidades; o banco tem 65** (`HABEF` × `clube.habilidade`).
4. **`eval()` em produção** (motor:3782-3794): o código procura um trecho de texto dentro da
   própria função `distOtima` e a reescreve em tempo de execução. **Se o trecho não bater, a
   flag vira `false` e a tela segue calculando errado, calada.**
5. **Senha em texto limpo:** `"encaixepro"` (motor:2104) libera o modo PRO.
6. **22 funções definidas duas ou mais vezes** só no `motor-e-ficha-base.js` — `_trocaHabs`
   tem **4 versões**, `valsDeLvl` 3, `restaurarMotor` 3, `editImp` 3. E o `ficha-ajustes.js`
   **substitui `abrir`, `reabrir` e `fechar`** da casca (linhas 1793-1797) *porque não
   confia neles* — está escrito no comentário: *"a casca tem três `_grava` empilhados"*.
7. **9 listeners de `DOMContentLoaded`** e **2 de `popstate`** — o segundo (`como-funciona.js:130`)
   é **anônimo, não pode ser removido**, e dispara ANTES do dono da rota; o remendo é um
   `setTimeout(…,0)`.
8. **A tela reescreve a régua do motor:** `elenco.js:866` troca o `_fal` por uma versão com
   **teto 9**. Se o `regua.py` mudar, a tela diverge em silêncio.
9. **Quatro variáveis globais para a mesma coisa** (`_SELPOS`, `_T6PENDENTE_POS`,
   `_T6SELPOS_FORCADA`, `_T6SELPOS_CARD`), escritas em bloco em 8 lugares.
10. **O contador "mais de 10,6 bilhões de cenários" é um relógio** que sobe 23.000 por
    segundo sozinho (motor:3127). Não mede nada.
11. **Estado do usuário só no navegador:** `MT_v1`, `CLUBEFOOTBALL_USER_STATE_V2` e um
    diário de transação artesanal. `ownerId` está **fixo em `null`** — é exatamente o slot
    do `auth.uid()`. Um elenco povoado chega a **50-300 KB** de localStorage (teto ~5 MB).
    As 8 invariantes que o arquivo valida à mão são constraints de banco.
12. **A foto do card vem do efHub** (`efimg.com/…/<id>_l.png`) em **13 lugares** dos arquivos.

---

# PARTE 4 · A ORDEM QUE ISSO PEDE

```
0 · a régua da casa            corrigir o parâmetro morto (o motor lê insumo_bonus_parametro)
1 · o que já tem casa          BONUS_PRONTO, BOXHIST, PACOTE, CORPO_MOTOR, PR_RAW, PIMP,
                               CAT, TECS, HABM… → 1.630 KB saem do código
2 · o que precisa nascer       CORPO_MOLDE, ordem das medidas, TJ_SA, formações, malha do
                               campo, travas, nomes novos das funções, escadas e cortes,
                               e o TEXTO EDITORIAL (uma tabela de conteúdo)
3 · a carga vira consulta      lista leve paginada no banco + ficha sob demanda
                               (hoje: 51 MB e 19 requisições, 3 síncronas)
4 · as contas duplicadas saem  a tela lê o número do motor em vez de refazê-lo
5 · o estado do usuário        localStorage → clube.usuario_estado com auth.uid()
6 · a coleta                   CORPO_EFHUB (10.056) e as imagens, no marco zero
```

⛔ Nada disso mexe no motor. **Marcar ≠ rodar** — a rodada continua sendo ordem do Luis.
