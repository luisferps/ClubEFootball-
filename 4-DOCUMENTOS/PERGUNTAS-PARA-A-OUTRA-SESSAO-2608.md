# PERGUNTAS PARA A OUTRA SESSÃO — 26/08/2026

> Sessão do extrator / `carta_jogo`. As perguntas abaixo saíram de medições feitas
> hoje na `clube.carta_jogo` (42.803 linhas, extração id 2).
> **Responder com o endereço no `Player.bin`, não com "não tem".**

---

## 1 · CAMPOS QUE ESTÃO VAZIOS NA `carta_jogo` E EXISTEM NO JOGO

Medido agora, sobre as 42.803 linhas:

| coluna | preenchidas | de |
|---|---|---|
| `habilidades` | **0** | 42.803 |
| `aptidoes` | **0** | 42.803 |
| `estilos_ia` | **0** | 42.803 |
| `impeto_s1` | 2.304 | 42.803 |
| `impeto_s2_cond` | 54 | 42.803 |

**Perguntas:**

1.1 · `habilidades` está zerada em 100% das cartas. O extrator lê esse campo? Em que
bit/largura? Se lê, por que não gravou?

1.2 · `aptidoes` idem — zerada em 100%.

1.3 · `estilos_ia` idem — zerada em 100%. (O sistema usa isso no bônus:
`bonus_parametro.estilo_ia_ponto = 1,0`, teto 4 estilos.)

1.4 · `impeto_s1` só tem 2.304 de 42.803 (5%). É assim mesmo — a maioria das cartas
não tem ímpeto nativo — ou a leitura falhou nas outras 40.499?

1.5 · `impeto_s2_cond` tem 54. Mesma pergunta.

---

## 2 · CAMPOS QUE NÃO EXISTEM COMO COLUNA E O JOGO MOSTRA NA TELA

Nenhum destes existe na `carta_jogo`. Todos aparecem na ficha do jogador dentro do jogo:

| dado | onde o sistema usa |
|---|---|
| **uso do pé ruim** (0–3) | entra na nota: `pe_ruim_frequencia_0..3` |
| **precisão do pé ruim** (0–3) | entra na nota: `pe_ruim_precisao_0..3` |
| **resistência a lesão** | ficha |
| **nível máximo / level cap** | ficha e progressão |
| **vagas de ímpeto** | quantas vagas a carta tem |
| **condição / forma** (as setas) | ficha |

**Perguntas:**

2.1 · Qual o endereço (bit + largura) de **uso do pé ruim** e **precisão do pé ruim**
no `Player.bin`? São dois campos separados, valores 0 a 3.

2.2 · Qual o endereço de **resistência a lesão**?

2.3 · Qual o endereço de **level cap**?

2.4 · Qual o endereço das **vagas de ímpeto**?
Observação: existem `vaga_s1` e `vaga_s2` (booleanos, 318 e 1.046 em `true`). Isso é
a mesma coisa que "vagas de ímpeto" ou é outra coisa? Se for outra, qual é qual?

2.5 · Qual o endereço de **condição/forma** (as setas)?

2.6 · Para cada um destes: **o campo foi procurado e não achado, ou não foi procurado?**

---

## 3 · A `carta_jogo` × A `carta`

A `clube.carta` (41.404, a que a tela e o motor leem) tem 11 campos que a `carta_jogo`
não tem. O plano é a `carta_jogo` virar o cadastro único. Antes disso:

3.1 · Destes, quais o extrator **consegue** trazer do jogo hoje ou com trabalho?
`tier` · `votos` · `max_ovr` · `data_lancamento` · `estilo_ia` · `level_cap` ·
`pe_ruim_uso` · `pe_ruim_precisao` · `resistencia_lesao` · `vagas_impeto`

3.2 · A `carta_jogo` tem 42.803 e a `carta` tem 41.404 — **1.399 de diferença.**
São cartas novas da extração 2? Ou a `carta` tem cartas que a `carta_jogo` não tem?

---

## 4 · OS DOIS CAMPOS DE ESTILO — CONFIRMAR A LEITURA

Medido hoje e **conferido pelo Luis na tela do jogo**:

| campo A (bit 372, 8 bits) | campo B (bit 440, 6 bits) | cartas |
|---|---|---|
| tem | vazio | 34.264 |
| vazio | tem | 5.011 |
| **tem** | **tem** | **48** |
| vazio | vazio | 3.480 |

Provas na tela (Luis, 26/08):
- Konaté `105873091445023` → tela: ofensivo *Defensor criativo*, defensivo *O destruidor*.
  Extração bate.
- Konaté `52897622638879` e as outras 865 com *O destruidor* no campo A → tela mostra
  **no ofensivo**. Extração bate.
- Casillas `88045755827028` → tela: ofensivo *Goleiro adiantado*, defensivo *Goleiro
  ofensivo*. **São estilos diferentes** (o Luis repetiu isso várias vezes).

**Perguntas:**

4.1 · Confirma que **campo A = slot ofensivo** e **campo B = slot defensivo**, sem
exceção?

4.2 · O Casillas prova que **A e B são catálogos independentes** — 64 no A é *Goleiro
adiantado*, 16 no B é *Goleiro ofensivo*. A conversão `A = B × 4` que aparece em
Meia versátil (28/7), Primeiro volante (32/8), O destruidor (36/9) e nos goleiros
(64/16, 68/17) é **coincidência de codificação ou regra**? Se for regra, o Casillas
a quebra.

4.3 · Encontrei **959 cartas com id fora da faixa no campo B**: 660 com id 64 e 299
com id 68. O campo B tem 6 bits — o máximo é 63. **De onde vieram esses valores?**
O extrator escreveu id do campo A na coluna do campo B?

> Já corrigidos hoje (64→16, 68→17) e travados com `check (0..63)`. Preciso saber
> se a origem foi o extrator, para não voltar na próxima carga.

4.4 · O id **140** estava cadastrado como *Goleiro adiantado* no catálogo do campo A e
não tem nenhuma carta. O id **68** idem. De onde saíram? Já removidos.

---

## 5 · REGRA QUE PASSA A VALER (para o extrator não desfazer)

O **nome** do estilo em `carta_jogo.slot_ofensivo` / `slot_defensivo` agora é
**etiqueta derivada do id**, ressincronizada pelos catálogos `estilo_jogo` (campo A) e
`estilo_defensivo` (campo B).

**O extrator deve gravar o ID. O nome, se gravar, será sobrescrito pelo catálogo.**

Motivo: nome escrito à mão já quebrou três vezes — Provocador→Defensor criativo,
Zagueiro defensivo/ofensivo→Lateral defensivo/ofensivo, e o Casillas.

5.1 · O extrator pode passar a gravar **só os ids**?

---

## 6 · A ARQUITETURA QUE O LUIS MANDOU

> *"A gente só precisa de uma tabela com os dados do jogador, e as tabelas com os
> catálogos. Depois auxiliares, moldes. O resto apaga tudo."*
>
> *"Os dados do cadastro da carta são só aquela tabela"* — a `carta_jogo`.

6.1 · Alguma coisa do extrator ou da carga depende da `clube.carta` (a velha)?

6.2 · A `clube.extracao` (histórico de cargas) é escrita pelo extrator? Ela fica.

---

*Documento gerado em 26/08/2026 para o Luis levar à sessão do extrator.*
