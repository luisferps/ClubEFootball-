# PERGUNTAS — 19/08/2026
## O que eu NÃO sei, e preciso de quem fez o encaixe anterior

Contexto: estou refazendo a **ficha do card** no molde da designer (camada
`TELAS_1808`, em `ClubEfootball/programas/telas.py`). A casca antiga continua
viva no mesmo HTML e é ela quem calcula. Onze coisas eu resolvi lendo o
arquivo; estas abaixo eu **não consegui provar** e não quero adivinhar.

Cada item traz **o que eu medi**, para a resposta poder ser curta.

---

## 1 · O ÍMPETO NATIVO SAI ERRADO — qual é a fonte certa?

**Medido:** o card `Ruud Gullit` (base `88039045074410`) mostra na ficha
`Fantasia +2 · Drible · Controle de bola · Finalização · Agilidade`.
O Luis afirma que o ímpeto nativo dessa carta é **`Chute +3`**.

A cadeia que a casca usa, na ordem: `pimpNativos(c)` → `pimpDoCard(c)` (tabela
`PIMP`, por `boostId`) → `c.nmn` → `_natDoVetor(c)`.

**Perguntas:**
1. Qual dos quatro é a fonte confiável hoje? Algum deles está sabidamente podre?
2. O `PIMP` foi gerado quando, e contra qual coleta? Ele cobre os 2.387 cards?
3. O `pimpNativos` v2 (linha ~6515 do HTML) decompõe `+4`/`+5` em dois ímpetos.
   Essa decomposição foi conferida contra o jogo, ou é heurística?
4. Existe algum card com decomposição conhecida-correta que eu possa usar como
   gabarito para testar?

---

## 2 · `frows` VEM SEMPRE VAZIO — a ficha do corpo está em branco

**Medido:** no `gera_encaixe.py`, o dicionário do card traz literalmente
`'arows': arows, 'frows': []`. Nunca é preenchido.

Resultado na tela: o bloco `MEDIDAS DO CORPO` mostra
`TOTAL · soma 0 · peso 0 · bônus -0.27 · 0%` — sem uma única medida.

**Perguntas:**
1. A ficha antiga montava as medidas na hora, a partir de `FIS_M` / `CORPO97` /
   `fisEspelho(c)`? Qual é a função que devolve as 12 medidas prontas
   (nome, peso, alvo, valor, pontos)?
2. O `frows` foi esvaziado de propósito (para o HTML não crescer) ou é regressão?
3. O `bônus -0.27` que aparece no TOTAL vem de onde, se as medidas estão vazias?

---

## 3 · `Base Konami` e `Máximo Konami`

**Medido:** a ficha lia `c.ovr` (Base) e `c.maxOvr` (Máximo). O `maxOvr` vinha de
`m.get('maxOvr')`, que é a **pontuação que a tela antiga mostrava** — por isso
saía quebrado (`100.18`) num campo que a Konami publica inteiro. Já troquei a
prioridade para `c.get('max_ovr')`.

**O que sobrou:**
1. Para o Gullit, `ovr = 87` no banco. O Luis diz que o mínimo da carta é **88**.
   De onde sai o 88? É `ovr + 1`? É outro campo do efHub? É o `level 1` da carta?
2. Depois da troca, o `Máximo Konami` caiu para 87 nesse card — ou seja,
   `max_ovr` veio **vazio**. Quantos cards têm `max_ovr` preenchido, e o que
   preenche? (`temMax` existe como flag, então alguém sabia disso.)
3. Existe diferença entre "OVR base da carta" e "OVR no nível 1"? A tela deveria
   mostrar qual dos dois?

*(Enquanto isso, o Luis mandou tirar o bloco da tela.)*

---

## 4 · A DATA — existe data de lançamento de verdade?

**Medido:** `c.dt` vem do `box_por_card.json` (`unificar_base.py`, linha ~293),
sobe como `data_lancamento` (`subir_base.py`) e volta com esse nome
(`baixar_base.py`). **O nome da coluna mente:** o conteúdo é a data da BOX.

**Perguntas:**
1. Alguma fonte que a gente já lê publica a data de lançamento real da carta
   (efHub? efootballdb? `variation_details`)?
2. Se não, vale renomear a coluna do banco para `data_do_box`? O Luis mandou
   tirar a data da ficha por enquanto.

---

## 5 · AS TABELAS INDEXADAS POR NOME DE FUNÇÃO — quantas ainda estão quebradas?

**Medido, e é o defeito mais caro do dia:** clicar em **9 das 15 funções** da
ficha não fazia nada. Causa:

```
MED['Meia de lado por fora']  ->  undefined
notaMed()                     ->  Cannot read properties of undefined (reading 'b1n')
abrir()                       ->  morre antes de escrever o #box
```

O nome na TELA foi fechado em 15/08; a CHAVE do banco continua a antiga. Parte
das tabelas da casca foi regravada com o nome novo, o `c.tipo` de cada linha não.

Já construí uma ponte no gerador (`patch_ponte_dos_nomes`) que dá as duas
grafias a **13 tabelas**: `MED · REGUA · FX_ANC · FX_K · FIS_KON · FIS_P ·
MF_TIPO · MF_FAIXA · FILA · B5V · ESTV · MF_DIRF · FUNC_POS` — 130 chaves.

Depois disso descobri que **`TJ_REGRA` também usa os nomes novos**, e por isso o
clique no campinho só funcionava em `CA`, `ZC`, `GK`, `LD` e `VOL`. Resolvi por
comparação tolerante no meu lado.

**Perguntas:**
1. Existe a lista completa das estruturas indexadas por nome de função?
   Achei mais: `TJ_REGRA`, `TJ_SA`, `FAM`, `SIG`, `MT_FUNCS`, `ORDEM_DAS_FUNCOES`,
   `EST_POS`, `ALT_FUNC`, `_baseFunc`. Falta alguma?
2. Por que a renomeação foi aplicada em algumas e não em outras? Foi um replace
   global que pegou só parte do arquivo?
3. **A decisão de fundo:** vale renomear no BANCO de uma vez e acabar com as duas
   grafias? O que quebra se isso for feito? (`builds`, `linhas.jsonl`, `MT_v1` do
   localStorage, `tela_encaixe`...)

---

## 6 · O `cmode` TEM DUAS CONVENÇÕES

**Medido:** `_aplica` (HTML ~4380) lê `c.cmode||1` como degrau direto (1,2,3).
O `setCondCard` (HTML ~5769) grava `c.cmode = degrau - 1` (0,1,2). O
`painelBuild` escreve `degrau ${c.cmode||1}`.

O comentário do próprio arquivo registra o erro medido no Can Uzun: a tela dava
`111,6 · 111,6 · 132,2` quando o gravado era `111,6 · 132,2 · 151,7`.

**Pergunta:** qual das duas é a convenção oficial? Eu passei a chamar
`setCondCard(key, degrau)` com degrau absoluto 1/2/3 — está certo?

---

## 7 · `c.NEU` — as sugestões neutras

O Luis: *"sugestões são as habilidades que, se trocasse por alguma das
adicionadas, a nota não mudava"*. Passei a usar `c.NEU`
(`x.get('neutras')` no gerador).

**Perguntas:**
1. O `NEU` está preenchido para as 17.463 linhas, ou só para parte?
2. Ele é neutro **contra a build do motor** ou contra qualquer build?
3. `TECIG` (técnicos iguais) é o equivalente para técnico? Vale mostrar?

---

## 8 · `sl` × `slot` — a vaga de ímpeto

**Medido no gerador:** `sl` = vagas que ainda cabem (`[0,1]`), `slot` = retorno de
`impeto_da_carta` (`0` = carta anterior a 12/09/2024, sem vaga; `None` = não
conferida; número = vagas livres).

**Perguntas:**
1. Está certo que `slot === 0` é o ÚNICO caso em que a tela grita "SEM VAGA"?
2. Quantos cards estão hoje com `slot === null` (não conferida)?
3. A regra "só ímpeto `+1` pode ser escolhido" continua valendo?

---

## 9 · OS DOIS BÔNUS QUE O LUIS MANDOU TIRAR

Ele mandou excluir **depois de conferir contra o banco**:

- `bônus +0.70 na nota` (perto do técnico)
- `3 de 5 · bônus +0.9 na nota` (perto das habilidades)

**Perguntas:**
1. Esses dois números são calculados na tela ou vêm da tabela `bonus`?
2. Se são da tela, batem com o que o `motor_bonus.py` gravou? Existe algum lugar
   onde essa conferência já foi feita?

---

## 10 · O ÍCONE DO ESTILO DE JOGO

O Luis pediu, no cabeçalho novo da ficha: foto → nome → posição → **ícone do
estilo de jogo** → nome do estilo.

**Pergunta:** esse ícone existe em algum lugar do sistema (arquivo, sprite, URL
do efHub), ou é imagem nova que precisa entrar? Pus um marcador redondo
provisório.

---

## 11 · O `% DO TOPO` DAS BOXES FECHADAS

Item 21 da lista de pendências: *congelar o `% do topo` das boxes fechadas*.

**Perguntas:**
1. O que exatamente deve congelar: o denominador (o topo daquela função na data
   do fechamento) ou o percentual inteiro?
2. Existe carimbo de "box fechada" no banco, ou isso se deduz do `BOXATIVA`?

---

## O QUE EU JÁ RESOLVI — para não perguntarem de novo

- a foto da ficha (a URL sai do `c.id`, mesma `url()` da lista e da home)
- o `visto_na_casca` que o `baixar_base` jogava fora, com trava para não voltar
- a coluna `faltou` da tabela `bonus` (o `sql/23-bonus-faltou.sql` não existia)
- os botões da ficha que não gravavam (`t6Bar`, `t6Hab`, `t6Tec`)
- o `style-hover` da designer, que o navegador ignora — 60 elementos mudos
- a ponte dos dois nomes em 13 tabelas
- `SALVAR MINHA BUILD` e `COPIAR DO MÁXIMO`, que estavam órfãos por causa do `.bhd`
- o clique que disparava duas vezes (pai e filho com o mesmo `onclick`)
