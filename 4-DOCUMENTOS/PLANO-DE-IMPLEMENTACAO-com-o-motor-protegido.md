# PLANO DE IMPLEMENTAÇÃO — v2, revisado (25/08, Fable)
Regras que o plano obedece: o motor não fica exposto · a nota da tela é a nota do
motor · recoleta total decidida (V7 rodando na máquina do Luis) · marcar ≠ rodar.

---

## O QUE A REVISÃO ACHOU E CORRIGIU NO PLANO v1

**1 · A "Etapa 0 urgente" era impossível de executar primeiro.** Cortar `arows`/
`frows`/`pool` da view derruba a ficha do site atual — ela lê essas chaves para
desenhar. E o vazamento **não nasceu na casa_tela**: a `tela_encaixe` do site
publicado entrega o mesmo `arows` há semanas. Conclusão: não existe conserto rápido
que não quebre a tela; **a porta só fecha de verdade junto com o simulador** (a troca
é atômica: a ficha passa a pedir ao servidor → a view emagrece no mesmo deploy).
Enquanto isso a regra é uma só: **nada novo é publicado**.

**2 · Faltava a etapa da SUBIDA da coleta.** O caminho dos dados desenha a
`clube.recebimento`, mas nenhuma etapa a criava, nem o mecanismo de subir os lotes
que o V7 grava em `Downloads\coleta-efhub-dados-fotos`. Virou o passo 2.

**3 · A Etapa 5 estava desatualizada pela decisão da recoleta total.** A lista de
"1.300 para coletar" morreu: o V7 recoleta tudo (fila de 38.494, fortes primeiro,
com foto, 3s/card). As fontes velhas (`cards_base`, `cards_efhub`, `cards_v2`) viram
**conferência**, não carga. E ficou registrada a pendência: **4.312 cards** do
universo (42.806) não estão no efHub — são do efootballdb; a ficha deles precisa de
outra fonte.

**4 · Três pedidos seus estavam no desenho mas fora da ordem:** proveniência por
campo, completude por finalidade (2 motores + ficha), e a auditoria dos MOTORES
(aberta desde 15/08) — que agora é pré-requisito do simulador, porque é o motor que
vai ficar online. Entraram na ordem.

---

# A ORDEM (revisada)

```
JÁ RODANDO   a recoleta V7 na máquina do Luis (fila 38.494, fortes primeiro, fotos)

 1 · a receita completa      11 insumos do legado → casa (0022, EM ANDAMENTO)
 2 · a caixa de entrada      clube.recebimento + a porta INSERT-only + o subidor
                             dos lotes do V7 (para a coleta não ficar presa no PC)
 3 · o cadastro único        carta (3.269) separada de carta@posição (3.684)
                             ⚠️ a auditoria muda de critério junto, documentado
 4 · proveniência + completude   fonte e data POR CAMPO · pronto_p_motor_otimizacao /
                             pronto_p_motor_bonus / pronto_p_ficha (regra versionada)
                             ⛔ motor só lê card marcado pronto
 5 · o que nasce do código   FILA, B5V, formações, malha, METAS, escadas, textos,
                             nomes novos das funções (FILA/B5V na receita = segredo)
 6 · auditoria dos MOTORES   equação/régua/bônus/otimização — antes de ir pro Railway
 7 · o simulador + a porta   AVALIAR no Railway (a conta do próprio motor) · a ficha
                             pede ao servidor · a view pública emagrece (sem alvo,
                             peso, direção, pool) · admin autenticado vê tudo ·
                             casca tira as duplicatas, o eval(), a senha, o 2º popstate
 8 · QUANDO A COLETA FECHAR  conferência lote a lote → entra na casa → compara
                             linha->base × atributo novo → marca o que mudou
 9 · A RODADA ÚNICA          ordem sua, na sua máquina (novas + 5.711 marcadas)
10 · homologação → fase 9    você testa o 1-SISTEMA → publica → aposenta o legado
11 · login + comercial → CHAVES (por último, ordem sua) → LANÇAR
```

---

# AS ETAPAS, NO DETALHE QUE IMPORTA

## 1 · A receita completa
Os 11 insumos copiados do legado para a casa, sem leitura pública: régua (6, com o
teto 9), bonus_parametro (13, **a vigente** — a morta na `clube.parametro` fica
marcada), molde_corpo (384, hash idêntico ao do código), corpo_ordem (12), barra (27),
custo_nivel (25), multiplicador (100), regra_posicao_estilo (2), bonus_posicao (60),
elenco_luis (114), carta_tipo (137).

## 2 · A caixa de entrada e o subidor
`clube.recebimento`: payload cru + sha + fonte + quando, INSERT-only pela porta
pública, ninguém lê de fora. O subidor: script de navegador que lê a pasta da coleta
e sobe os lotes com assinatura — mesma lógica do coletor, na direção contrária.
**Decisão pendente sua:** onde as fotos moram (Supabase Storage × Cloudinary já usado).

## 3 · O cadastro único
`clube.carta` = só as 3.269 cartas. As 3.684 `@posição` → `carta_posicao_comprada`.
Prova de que são coisas diferentes: nenhuma `@posição` tem pé ruim, idade ou lesão.
A `build` já usa só a base (zero `@`).

## 4 · Proveniência + completude
Cada valor com fonte e data (a recoleta V7 já traz isso por construção — uma fonte,
uma data, um sha por card). Completude por finalidade com regra versionada, no molde
que o GPT desenhou (`missing_calculation_fields` etc.) — mas morando na casa.

## 5 · O que nasce do código (não vem de coleta)
FILA (1.139 pares) · B5V (360) · 17 formações + malha do campo + travas · METAS (98) ·
escadas de apresentação · ~110 KB de texto editorial · `_NOME_NA_TELA` (14).

## 6 · Auditoria dos motores
Atrás de número inventado, valor padrão disfarçado, constante que devia ser tabela.
Aberta por ordem sua desde 15/08. Vira gate: o AVALIAR só sobe depois dela.

## 7 · O simulador e o fechamento da porta (atômicos)
- AVALIAR no Railway = o próprio motor Python. A nota da tela **é** a nota do motor.
- A ficha manda o estado (barras, ímpeto, técnico, habilidades) e recebe nota + 26
  valores + ganho por etapa. Alvo, peso, régua, degraus nunca saem do servidor.
- Defesas contra sondagem: barras mexem 2-4 atributos juntas · login para simular ·
  limite por conta/minuto · nota arredondada · o valor real está nas 42 mil medidas.
- Fora do ar = "não sei agora", nunca conta local. Os casos do PROVA viram teste de
  regressão do servidor.
- No mesmo deploy: view pública emagrece (lista leve — hoje 51 MB/19 requisições, 3
  síncronas), a casca perde 2,2 MB de dado congelado, o eval(), a senha em texto
  limpo, as 22 funções duplicadas e o 2º popstate.
- Quem decide o que cada um vê é o **servidor** (admin autenticado = cascata inteira;
  usuário = sem alvo/peso). `MODO_ADM` local vira só desenho.

## 8-9 · O acerto e a rodada
Máquina já testada: `build.linha->base` × `carta.atributos` → 17.504 comparadas,
205 divergentes em 51 cartas, hoje. Depois da coleta, é essa régua que monta a fila.
A rodada é ordem sua.

## Pendências conhecidas (não bloqueiam)
- 4.312 cards fora do efHub (efootballdb-only) — ficha por outra fonte, depois.
- Cadeado comercial 🔒 do MODO B: fica ou sai (decisão de produto).
- Depósito das fotos (etapa 2).
