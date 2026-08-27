# O CRUZAMENTO — fui olhar no banco, campo por campo
**25/08/2026.** Não é conferência de valor: é *"você acha que tem — vai lá e olha se tem mesmo."*
Fui. Abaixo, o que existe de verdade, com contagem lida do banco.

---

## A DESCOBERTA QUE MUDA O PLANO

**Metade do que eu disse que "precisa nascer no banco" JÁ EXISTE** — não no `clube`,
mas no legado `public`, nas tabelas `insumo_*`. A casa nova simplesmente **não as
carregou**. É o mesmo erro do parâmetro da régua, e agora sei o tamanho dele:

| tabela do legado | linhas | é o quê no código | está na casa? |
|---|---:|---|---|
| `insumo_bonus_corpo` | **384** | **o `CORPO_MOLDE` inteiro** (32 funções × 12 medidas) | ❌ **NÃO** |
| `insumo_bonus_parametro` | 13 | a régua do motor de bônus (a vigente) | ❌ **NÃO** |
| `insumo_regra_funcao` | 2 | `TJ_REGRA` (12 posições) **e** `TJ_SA` (22 estilos) | ❌ **NÃO** |
| `insumo_corpo` | 12 | `CORPO_ORDEM` — a ordem das 12 medidas | ❌ **NÃO** |
| `insumo_barra` | 27 | `MB`/`MBN` — as 10 barras e o que cada uma sobe | ❌ **NÃO** |
| `insumo_custo_nivel` | 25 | `custoNivel` — o custo acumulado por nível | ❌ **NÃO** |
| `insumo_multiplicador` | 100 | `MS` — os multiplicadores do técnico | ❌ **NÃO** |
| `insumo_regua` | 6 | a régua: os 9 degraus, **o teto 9 da punição**, a bússola | ❌ **NÃO** |
| `insumo_bonus_posicao` | 60 | bônus por posição | ❌ **NÃO** |
| `meu_time` | **114** | o `MEU_TIME` cravado no código — os 114 ids | ❌ **NÃO** |
| `insumo_player_type` | 137 | tipos de carta — a casa tem `tipo_carta` com **3** | ⚠️ **divergente** |

**São 11 insumos a mais que faltam na casa** — somados aos que eu já tinha achado.

---

## O QUADRO, ITEM POR ITEM

### ✅ TEM NO BANCO, e conferi que é a mesma coisa

| do código | KB | onde está | prova |
|---|---:|---|---|
| `BONUS_PRONTO` | 1.050 | `clube.build.b_corpo/b_pe_ruim/b_estilo/b_ia` | **somas idênticas nas 19 funções** (corpo, pé ruim e estilo bateram até a 3ª casa). O banco tem **51 cartas novas** que o JS não conhece e **preencheu bônus de IA** que no JS eram "não sei" — provado em 2 funções, id por id |
| `CORPO_MOTOR` | 127 | `clube.carta.corpo` | **hash idêntico**: `61bf40c0…` nos dois lados — 2.783 cartas × 12 medidas = **33.396 números iguais** |
| `CORPO_MOLDE` | 15 | `public.insumo_bonus_corpo` | **hash idêntico**: `80bd70bc…` — as 384 linhas batem. O `teto` (32 valores) não está lá, mas é **derivável**: conferi que é Σ(peso×2) nas 32 funções |
| `CORPO_ORDEM` | 0,2 | `public.insumo_corpo` | mesma ordem, item a item (altura, coxa, panturrilha, cintura, peito, tamBraco, tamPescoco, comprPerna, comprBraco, comprPescoco, largOmbro, altOmbro) |
| `TJ_REGRA` / `TJ_SA` | 1,6 | `public.insumo_regra_funcao` | 12 posições e 22 estilos nos dois; conteúdo conferido por amostra (ZC, Pivô, Artilheiro) |
| `HABM` (65 habilidades) | 3,4 | `clube.habilidade` | **os 65 nomes são exatamente os mesmos** — conjunto idêntico, nenhum sobrando de um lado nem do outro |
| `CAT` (ímpetos fabricáveis) | 5,7 | `clube.impeto_fabricavel` (58) + `impeto` (430) + `impeto_efeito` (2.158) | tabelas existem e estão cheias |
| `PACOTE` / `BOXHIST` | 342 | `clube.box` (2.014) + `carta.box_id` (**6.287 cartas**) | o banco cobre **o dobro** das 3.133 do `PACOTE` |
| `TECS` | 4,4 | `clube.tecnico` (1.664) | existe |
| `ESTV` | 6,2 | `clube.estilo_valor` (144) + `estilo` (24) | existe (e a função que usa o ESTV **está morta** no código) |

### ⚠️ TEM O CAMPO, mas o banco cobre MENOS

| do código | o campo no banco | cobertura |
|---|---|---|
| `PR_RAW` — pé ruim de **3.216** cartas | `clube.carta.pe_ruim_uso` / `pe_ruim_precisao` | **2.757** cartas com os dois campos · 3.252 com o uso. **Faltam ~460** |
| `CORPO_EFHUB` — **10.056** cartas | `clube.carta.corpo` | 6.951 cartas no total do banco. **É a coleta que falta** |

### ❌ NÃO TEM MESMO — fui olhar e não existe em lugar nenhum

| do código | procurei em | veredito |
|---|---|---|
| `FILA` (28,8 KB) — a **incidência %** de cada habilidade na elite da função | `clube.molde` só tem `versao, funcao_codigo, atributo_idx, alvo, peso` — **nenhuma coluna de habilidade**; `comunidade_apurado` existe e está **VAZIA (0 linhas)** | **não existe** |
| `B5V` (8,2 KB) — o valor de cada habilidade **rara** por função | idem | **não existe** |
| `METAS` — os 98 jogadores "meta" | nenhuma tabela com esse nome ou conteúdo nos 3 schemas | **não existe** |
| `MT_FORM` — as 17 formações com as coordenadas | idem | **não existe** |
| malha do campo, travas de composição, `MT_FUNCS` | idem | **não existe** |
| escadas de cor, `CLS_F`, cortes das etiquetas, semáforo | idem | **não existe** |
| **todo o texto editorial** (~110 KB) | nenhuma tabela de conteúdo/texto | **não existe** |
| `MF_*` (o esqueleto das medidas: grupo A/B/C, GK invertido, exceções) | parcialmente coberto pelo `insumo_bonus_corpo` | **falta o resto** |

---

## O QUE ISSO MUDA

1. **A lista "precisa nascer" encolheu muito.** O molde do corpo, a ordem das medidas,
   as duas tabelas TJ, as barras, o custo por nível, os multiplicadores e a régua
   **já existem** — é carga, não projeto.
2. **O que sobra para projetar é pouco e é claro:** a incidência de habilidade
   (`FILA`/`B5V`), as formações e a malha do campo, a lista de metas, as escadas de
   apresentação, e uma casa para o texto editorial.
3. **Apareceu um trabalho que não estava na conta:** carregar os 11 insumos do legado
   para a casa. Sem isso, quando o motor passar a ler da casa, ele lê régua incompleta.

⛔ Nada foi tirado do código, nada foi criado no banco. Isto é só o retrato.
