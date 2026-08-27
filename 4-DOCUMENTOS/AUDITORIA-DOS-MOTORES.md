# AUDITORIA DOS MOTORES — a que você pediu em 15/08
**25/08/2026.** Lidos linha a linha: `motor.py` (957) · `regua.py` (179) ·
`equacao.py` (270) · `motor_bonus.py` (840). **32 achados.** Depois da revisão contra o dado (ver abaixo): **8 críticos · 19 graves · 5 atenção**.
Todos gravados em `clube.achado_motor`.

> Sua ordem, literal: *"procurar número inventado ou valor padrão disfarçado"*.
> O motivo: *"se faltar um insumo o motor roda também, mas dá resultado errado e a
> gente pensa que está certo."*

**Veredicto: a suspeita estava certa, e é pior do que parecia. O motor não pode ir
para o Railway como está.**

---

## OS TRÊS PIORES

### 1 ⛔ O motor sempre monta 5 habilidades — mas a regra é de 0 a 5
`motor.py` linhas 499, 504, 582. O número 5 está cravado no código. A regra do
sistema (documento `REGRA-1708`) diz que **o espaço de habilidades varia de 0 a 5 por
carta**, e o motor **não lê campo nenhum de vaga**.

**Consequência:** toda carta com menos de 5 vagas recebe uma build com 5 habilidades e
**nota inflada**. Não há erro, não há aviso, e a nota é plausível. Isso afeta o ranking.

### 2 ⛔ O motor de bônus não lê o banco — e o `b_total` transforma "não sei" em zero
`motor_bonus.py`. Dois problemas encadeados:

- **A fonte é um arquivo que não está no repositório:** `dados/insumos_bonus.json`.
  O banco é **destino**, não fonte — a `insumo_bonus_parametro` de 16/08 é uma
  *fotografia* daquele JSON num dia, não a origem. Por isso a tela em JavaScript
  diverge: são **três cópias** da mesma constante (JSON, tabela, JS) e nenhuma é dona.
- **A soma que vai para a nota trata ausência como zero** (linhas 505-506): os `None`
  são filtrados fora da soma do `b_total`. A honestidade do "não sei" está nos campos
  que ninguém soma; **o campo operacional não a respeita**.

E o caso mais direto: **o estilo de jogo ativo não tem "não sei"**. Card sem estilo
recebe `0.0`, **não entra na lista `faltou`**, não aparece no NAO-SEI.txt — e perde
**1 ponto inteiro** na nota final, com o sistema informando que está tudo certo.

⚠️ E o log **mente sobre isso**: nas linhas 829-836 ele imprime *"bônus ficou 0"* nos
três casos em que ficou `None` (onde acertou), e **omite** justamente o caso que virou
zero de verdade. Quem auditar pelo log conclui o oposto da verdade.

### 3 ⛔ Três insumos faltando produzem três resultados plausíveis e errados
`motor.py`, sem uma linha de aviso — **não existe um único `assert` ou `raise` em 957
linhas**:

| falta | o que sai | parece |
|---|---|---|
| orçamento (`orc`, linha 113) | build com **todas as barras zeradas** | "carta fraca" |
| vagas de ímpeto (`sl`, linha 120) | build **sem nenhum ímpeto** | "carta sem ímpeto bom" |
| **molde** (`arows` com pesos 0, 115) | **nota 0,0 com build vazia** | "carta ruim" |

O terceiro é o pior: molde ausente disfarçado de carta ruim.

---

## O RESTO, POR ASSUNTO

**Defaults que mudam a nota em silêncio**
- `equacao.py:187` — tática nula ou com nome errado cai em `max(sk.values())`: usa a
  **maior proficiência** do técnico. Um typo (`"4231"` × `"4-2-3-1"`) infla a nota do
  elenco inteiro sem erro. ⚠️ Grave para o simulador, onde o nome vem do cliente.
- `equacao.py:206` — **habilidade desconhecida é descartada calada**. O usuário marca,
  ela não existe no JSON, e a nota volta como se ele não tivesse marcado nada.
- `equacao.py:262` — barra com nome errado = zero níveis, conta segue normal.
- `regua.py:149` — peso **nulo** (molde incompleto) é descartado como se fosse zero.
- `regua.py:148` — não verifica se vieram os 26 atributos. Com 20, roda e entrega a
  nota de 20 como se fosse completa.
- `motor_bonus.py:283` — molde vazio vira bônus **0,0**, não `None`.
- `motor_bonus.py:252-263` — **molde parcial**: função com 3 das 12 medidas calcula o
  teto sobre 3. Resultado sempre plausível — sobrevive a qualquer conferência por
  amostragem. É o modo de falha mais difícil de enxergar.

**Números sem origem que mudam o resultado**
- `motor.py` **`+40`** (384, 817, 860): folga assumida na janela que mede o teto usado
  por **três podas**. Subestimado, **poda o ótimo em silêncio** — e o próprio código
  registra que isso já aconteceu: *"perdeu o ótimo em 1 de 30, Pape Gueye, −6,2"*.
- `equacao.py:228` **`/2.0`** — "a habilidade perdedora vale metade". Decisão sua de
  05/08, mas **não existe em `bonus_parametro` nem em tabela nenhuma**.
- `equacao.py:126` **`PISO = 40`** · `equacao.py:101-105` **a ordem `AM`** dos 26
  atributos do boost do técnico (com a ordem errada, **41 de 62 técnicos** dão +1 no
  atributo errado) · `motor_bonus.py:241` **peso 5 da altura** — que sobe para a tabela
  como se fosse dado medido, sem marca de que foi default.

**Regras que estão fora do motor**
- **`bloqueio` (246 habilidades proibidas por função) nunca é consultado pelo motor** —
  mora no chamador. Um serviço que importe `motor.py` direto entrega build com
  habilidade proibida.
- Os cortes (`MARG_OVERRIDE`, `CORTE9/11/13`) são lidos por `globals().get()` com
  default e injetados de fora. **Importar o motor direto = rodar com o corte de margem
  ligado**, o mesmo que já perdeu o ótimo.

**Zero proveniência**
O motor **não registra com que versão de molde ou régua rodou**. Molde v4 e v5 dão
notas diferentes e saídas indistinguíveis.

**Divergências internas** (o mesmo cálculo escrito duas vezes, e as duas discordam)
- `notaDe` × `nota_por_tabela` — o docstring diz que são idênticas; a segunda clampa em
  [0,260] e trunca. **O DP maximiza uma e a tela exibe a outra** nos extremos.
- `Card.dist` × `_grupos+_dp` · `Card.aplicar` × `vals_finais` (uma aplica o buff da
  habilidade, a outra não — e `Card.build` usa a errada).
- A fórmula da punição está escrita **três vezes** em `regua.py`.

**E a divergência com a tela, explicada**
`round()` do Python é *banker's rounding* (`round(0.5)=0`); `Math.round()` do
JavaScript é meio-para-cima. **Os dois divergem no último dígito em qualquer empate de
meio décimo.** É mais um motivo para a conta ser feita num lugar só.

---

## PARA VIRAR SERVIÇO ONLINE — o que impede hoje

1. **`os.chdir()` e `sys.path` mutados no import** (os três arquivos). Isso é estado do
   processo inteiro: num servidor, uma requisição atropela a outra.
2. **`import equacao` falha agora, aqui.** Ele lê 3 arquivos JSON locais por caminho
   relativo e **nenhum dos três está no repositório** (`tabm_medido.json`,
   `tecnicos.json`, `HAB_EFEITOS_FINAL.json`) — nem o `insumos_bonus.json` do bônus,
   nem o `config.txt`. É a definição de "só funciona na máquina do Luis".
3. **`motor_bonus.py` executa tudo no import**: escreve arquivos, sequestra a saída
   padrão e faz upsert no Supabase. Importar o módulo roda o motor.
4. **Chave do Supabase em `config.txt` em texto plano**, validada só por
   `'COLE_AQUI' in KEY`.
5. **Nenhuma validação de entrada em lugar nenhum** — todo insumo malformado ou vira um
   dos defaults acima, ou vira traceback cru no meio do pedido.

---

# ⚠️ REVISÃO DA AUDITORIA — cada crítico confrontado com o DADO (25/08, tarde)

O Luis pegou um erro meu: eu classifiquei como crítico o "motor sempre monta 5
habilidades" sem conferir contra o banco. **A regra dele é "ou 0 ou 5"** — carta que
evolui tem 5 vagas, carta que não evolui tem 0, não existe meio-termo. Medido:
**11.416 builds de carta que evolui com 5 · 5.873 de carta que não evolui com 0 ·
ZERO erradas.** O motor obedece. Meu erro foi ler `carta_habilidade.relacao='espaco'`
como vaga — ela é o **pool** de habilidades possíveis (média 17,58 por carta, até 33).

Por isso refiz o teste de **todos** os críticos contra o dado real. Resultado:
**de 14 críticos, 8 se confirmaram, 5 caíram para grave ou atenção, 1 era falso alarme.**

### Caíram — o risco existe no código, mas não se materializou

| achado | o que o dado disse |
|---|---|
| "sempre 5 habilidades" | **falso alarme** — o motor está certo pela regra 0-ou-5 |
| "molde ausente vira nota 0,0" | `arows` tem **sempre 26** atributos nas 17.504 builds (min=26, max=26). Nota zero: **0**. Nota nula: **0**. Nunca aconteceu |
| "régua não confere se vieram 26 atributos" | idem — nunca chegou com menos |
| orçamento ausente (`or 0`) | **confirmado, mas contido:** 125 builds de 32 cartas com **sobra negativa** (pior: −112) — build impossível de montar no jogo. **100% delas são de carta com orçamento NULL e 100% já estavam na fila** pela trava de completude |
| vagas de ímpeto ausentes | **confirmado, mas pequeno:** 21 builds com "o motor pôs" em carta de vaga **desconhecida**. Em carta com vaga 0 **conhecida: zero**. O motor respeita a vaga quando ela existe |
| estilo ativo sem "não sei" | **confirmado, mas menor:** das 8.118 builds com `b_estilo = 0`, **8.009 são zero legítimo** (a carta tem estilo e ele não liga naquela função). Só **109 de 53 cartas** são "não sei" virado zero. Todas já na fila |

### Confirmaram-se, com número

| achado | o dado |
|---|---|
| **`b_total` soma tratando buraco como zero** | **590 builds de 157 cartas** com `b_total` preenchido e pelo menos um dos quatro bônus nulo. 587 já estavam na fila; **as 3 que escaparam foram marcadas agora** |
| tática nula usa a maior proficiência · habilidade desconhecida descartada | não há rastro no banco (entram por chamada). **Risco real no simulador**, onde o nome vem do cliente |
| motor de bônus não lê o banco · JSONs fora do repositório · `os.chdir` no import | risco de **virar serviço**, não mensurável no resultado |
| molde parcial do corpo | mora no JSON local. **Deixa de existir** se o motor ler `clube.molde_corpo` (384 = 32×12, denso) |
| nenhum gate em 957 linhas | confirmado por leitura — e os testes que rodei hoje (sobra negativa, arows=26, vaga de ímpeto, b_total) **são exatamente o gate que falta lá dentro** |

### A lição

A auditoria olhou o **código** e classificou pela gravidade do que *poderia* acontecer.
Metade não acontece no dado real. **A regra nova: nenhum achado de código vira crítico
sem um teste contra o banco.** E o inverso também vale — a `sobra negativa` só apareceu
porque fui procurar; nenhuma leitura de código teria dado esse número.

**Placar corrigido: 8 críticos · 19 graves · 5 atenção.** Fila do motor: **6.690
builds / 1.500 cartas**.


---

## O QUE ISSO MUDA NO PLANO

A Etapa 6 era o **gate** da Etapa 7 (o simulador no Railway). O gate **reprovou**. A
ordem continua a mesma, mas a Etapa 6 deixa de ser "auditar" e passa a ser
**"consertar antes de subir"**, com esta lista de 32 itens como escopo — e os 14
críticos como obrigatórios.

A boa notícia: **a casa está protegida**. A trava de completude (migração 0026) impede
que carta incompleta entre na fila do motor, e já marcou as **1.342 builds** que foram
rodadas assim. O que falta é a trava **dentro** do motor.

⛔ O motor continua parado. **Marcar ≠ rodar.**
