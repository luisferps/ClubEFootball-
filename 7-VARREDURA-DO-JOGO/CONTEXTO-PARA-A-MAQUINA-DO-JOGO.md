# CONTEXTO — varredura dos arquivos do eFootball para achar os insumos que faltam

**Cole este arquivo inteiro numa sessão nova, no computador onde estão os arquivos do
jogo.** Ele é autossuficiente: quem ler isto não participou da conversa anterior.

---

## 1 · QUEM SOU E COMO TRABALHO

Sou o Luis Fernando. **Não sou programador.** Trabalho só pelo navegador e por
interface — nunca por terminal, a não ser que você me dê o comando **já montado,
pronto pra colar**, e me diga exatamente onde colar.

- Me entregue **arquivos completos**, nunca trechos soltos nem "só a parte que mudou".
- Passo a passo **numerado**, com links clicáveis.
- Responda em **português**.
- **Não suponha nada.** Se não souber, meça. Se não der pra medir, diga que não sabe.

---

## 2 · O QUE EU QUERO

Tenho um sistema (ClubEfootball) que ranqueia cartas de eFootball por função. Os dados
das cartas vêm de sites (efootballhub, efootballdb) que, por sua vez, **extraem dos
arquivos do próprio jogo**.

Esses sites **falham de vez em quando** — vêm cartas sem campo, de forma intermitente.
Já tive que preencher coisa à mão.

**A ideia:** se os sites tiram do arquivo do jogo, e eu tenho o arquivo do jogo, então
posso ir direto na fonte e parar de depender deles.

**A tarefa imediata:** varrer os arquivos do jogo, achar os jogadores pelo ID, e me
dizer se dá para ler de lá os campos que estão faltando.

### ⭐ Mas o prêmio de verdade é maior que isso

Se der certo, **acaba o problema de entrada de dados de uma vez**. Hoje a minha
esteira é assim:

```
navegador varre o site  ->  30 lotes de 1.000 cartas  ->  horas de coleta
                            uns campos vêm, outros falham, de forma imprevisível
                            eu preencho na mão o que falhou
                            e a cada atualização do jogo, tudo de novo
```

Com o arquivo do jogo seria:

```
leio o arquivo  ->  todos os campos, de todos os jogadores, de uma vez
                    sem falha intermitente, sem esperar site, sem preencher à mão
```

**Por isso: não se limite aos 795 da lista.** Eles são o ponto de partida — os que eu
sei que estão furados, e que servem de gabarito porque eu conheço a resposta. Se você
conseguir ler o registro de um jogador, você consegue ler o de **todos**, e aí a lista
deixa de importar.

Me diga no relatório final **quantos jogadores existem no arquivo no total** e
**quais dos campos da tabela abaixo dá para ler para todos eles**. É essa resposta que
decide se eu aposento a coleta pelo site.

---

## 3 · A CHAVE — isto já foi medido e provado, pode confiar

O ID que o meu banco usa (`card_id`) **é composto**:

```
card_id  =  (variante da carta  <<  18)   |   player_id do jogo
player_id  =  card_id  AND  262143          (262143 = 2^18 - 1)
```

**A prova** (7.161 cartas coletadas em 25/08/2026):

- Dos 2.705 `card_id` longos, **919** têm a parte baixa igual a um `card_id` curto já
  coletado — e os **919 com o nome do jogador idêntico**. Zero falso positivo.
- A parte baixa dos **2.705** vai de **52 a 181.428** — exatamente a mesma faixa dos
  IDs curtos (84 a 179.676). **Nenhum caiu fora.**

Exemplos:
```
card_id 105866917449491  ->  player_id 134931
card_id 33185            ->  player_id 33185     (carta base: já é o número puro)
```

A parte alta é a variante (evento, POTW, Big Time…). **944 variantes distintas** nas
7.161 cartas.

**Consequência prática:** 3.269 cartas do meu banco são só **1.182 jogadores
distintos**. Você não procura 3.269 números — procura 1.182.

---

## 4 · O QUE PROCURAR

O arquivo **`PLAYER-IDS-A-PROCURAR.txt`** (vai junto com este) tem **795 player_id**,
um por linha. São os jogadores cujas cartas estão com campo faltando no meu banco.

Comece por estes cinco, que eu sei que existem e conheço bem:

```
33185    Manuel Neuer
40571    David de Gea
127038   Diogo Costa
143196   Moises Caicedo
112932   Ronaldo Vieira
```

---

## 5 · OS CAMPOS QUE ME INTERESSAM

Em ordem de importância:

| campo | o que é | falta em (cartas) |
|---|---|---|
| **pé ruim — uso e precisão** | dois números de 0 a 3 | **512** |
| **estilo de jogo** | "Goleiro ofensivo", "O destruidor", "Artilheiro"… | **498** |
| **estilo de jogo da IA** | a lista de estilos de IA da carta | **393** |
| posição nativa e secundárias | GK, CB, DMF, CMF… | 484 |
| altura · peso | em cm e kg | 484 |
| vagas de ímpeto · orçamento | quantos pontos a carta tem | 484 |
| resistência a lesão | 1 a 3 | 563 |
| tier · max_ovr · data de lançamento | ficha | 701 / 701 / 668 |

⛔ **NÃO preciso dos 26 atributos e NÃO preciso das medidas do corpo.** Medido no meu
banco hoje: **3.269 de 3.269 cartas com os 26 atributos completos**, e só 2 sem corpo.
Isso já está resolvido — se o editor mostrar esses campos, **ignore**. Não perca tempo
com eles e não me entregue eles.

⚠️ As **484** são sempre as mesmas cartas: entraram só com os atributos e nunca
receberam ficha nenhuma.

**O mais importante de longe é o estilo de jogo**, porque cada carta sem ele perde
1 ponto inteiro na nota final e o sistema não acusa nada.

---

## 6 · O MÉTODO — descobrir, não supor

⛔ **Não assuma a estrutura dos arquivos.** Eu não sei qual é, e você provavelmente
também não. Descubra assim:

### Passo 0 — o que já sabemos do arquivo (não precisa descobrir isto)

Publicado em **25/08/2026** por **RBsGameLab**, em
`pesmodding.com/2026/08/efootball-2027-playerbin-editor-by.html` — um editor do
**`Player.bin`** do eFootball 2027. O que a página afirma, literal:

```
arquivo ................. Player.bin
registro ................ 400 BYTES FIXOS  (antes era comprimento variável)
dataset validado ........ 42.369 jogadores
chave ................... PID de 64 bits completo
                          "multi-card stars (Messi, Kane, Bellingham…)
                           no longer collide with each other"
                          e cai para casamento de 32 bits quando não há exato
criptografia ............ contêiner WESYS, decifrado e recifrado na hora
                          (não precisa desempacotar .cpk por fora)
```

**O "400 bytes fixos" é a resposta do passo 3 abaixo** — é o espaçamento constante
que provaria a tabela. Confira mesmo assim: se os IDs aparecerem de 400 em 400,
está confirmado no meu arquivo também.

**E o PID de 64 bits confirma o que medimos aqui.** "Multi-card stars não colidem
mais" é exatamente a nossa descoberta: o ID longo carrega a variante na parte alta e
o jogador nos 18 bits baixos. O editor trata isso como um PID de 64 bits inteiro.

Os campos que o editor declara ler e escrever — **e que são exatamente os que me
faltam**:

```
os 26 atributos · Skills e AI Playing Styles (separados por barra vertical)
Attacking & Defensive Playing Styles · Weak Foot Usage & Accuracy
Height · Weight · Age · Position · Preferred Foot · Nationality
e os parâmetros do PlayerAppearance.bin
```

Do que ele lê, **o que me interessa é**: AI Playing Styles · Attacking & Defensive
Playing Styles · Weak Foot Usage & Accuracy · Height · Weight · Position.
Os 26 atributos e o PlayerAppearance eu já tenho completos — **ignore**.

⚠️ **Duas ressalvas, e são suas de resolver comigo, não sozinho:**

1. É um **`.exe` de terceiro, baixado do MediaFire**. Não instale nem execute sem
   me falar antes. Se for usar, use numa máquina onde isso não seja problema, e
   **nunca aponte para a instalação principal sem uma cópia do `Player.bin` antes**.
2. A página **não diz se ele exporta em lote**. Se for carta a carta pela interface,
   não serve para 42 mil jogadores — serve para **descobrir os offsets**: abra um
   jogador que eu conheço (Neuer, 33185), veja os valores na tela, e ache esses mesmos
   valores dentro do registro de 400 bytes dele. Feito isso uma vez, a extração em
   massa é nossa e não depende mais do editor.

### Passo 1 — achar onde estão os arquivos
Me pergunte a pasta de instalação, ou procure por `eFootball` em Arquivos de Programas
e na pasta do Steam (`steamapps/common`). Liste o que tem lá: extensões, tamanhos.
Os candidatos costumam ser `.cpk`, `.bin`, `.dat`, e um `DpFileList`.

Eu também tenho na pasta Downloads um arquivo chamado
`Update_eFootball_2024_Player_Data_Editor_Beta_V3.6.0.0.rar` — **um editor de dados de
jogador**. Se ele abrir e mostrar os campos, metade do trabalho está feita: veja quais
campos ele lê e de qual arquivo. **Confira antes se ele abre os arquivos da versão que
eu tenho instalada** — editor de 2024 pode não servir para o jogo de agora.

### Passo 2 — caçar os IDs no binário
Procure no **`Player.bin`**. Um ID como `33185` dentro de um arquivo binário aparece
como 4 bytes (e o PID completo, como 8). Procure nas
**duas ordens** (little-endian e big-endian) e também como 2 bytes:

```
33185  =  0x000081A1
little-endian:  A1 81 00 00
big-endian:     00 00 81 A1
```

Faça isso com **vários IDs da lista de uma vez**. É a parte que importa:

### Passo 3 — a prova de que achou a tabela certa
Se você achar muitos IDs da lista **espaçados por uma distância constante**, achou a
tabela de jogadores, e essa distância é o **tamanho do registro**. Exemplo do que
esperar:

```
33185 no byte 4.812.416
40571 no byte 4.812.816     -> 400 bytes de distância
43133 no byte 4.813.216     -> 400 bytes de novo
```

**Isso é a prova.** Sem espaçamento constante, você achou coincidência, não a tabela.

⚠️ **A distância esperada é 400** — é o que o autor do editor publicou. Se der outro
número no meu arquivo, **me diga**: pode ser versão diferente do jogo, e aí o resto do
que está no Passo 0 também precisa ser reconferido antes de usar.

### Passo 4 — decifrar o registro
Com o registro isolado, os campos se acham por **eliminação com casos conhecidos**:

- **Altura**: Manuel Neuer tem 193 cm. Procure o byte que vale 193 no registro dele e
  veja se no registro do Diogo Costa (que é mais baixo) o mesmo deslocamento tem um
  valor plausível. Um byte que vale entre 160 e 205 em todos os registros é altura.
- **Os 26 atributos**: valores entre 40 e 99, **26 seguidos**. É o bloco mais fácil de
  reconhecer — procure uma sequência longa de bytes nessa faixa. ⚠️ **Sirva-se deles só
  como âncora para localizar o registro e conferir que acertou** (eu já tenho os 26 de
  todas as cartas, e posso comparar contra os meus para você provar que decifrou
  certo). **Não é dado que eu preciso receber.**
- **Estilo de jogo**: é um código pequeno (provavelmente 1 byte), não texto. Compare
  cinco goleiros que eu sei que são "Goleiro ofensivo" — o byte que for **igual nos
  cinco e diferente nos zagueiros** é o estilo. A tradução do código para o nome você
  monta comparando com o que já sei (vai na tabela abaixo).
- **Pé ruim**: dois valores de 0 a 3 lado a lado.

### Passo 5 — conferir antes de me entregar
**Nunca me entregue um campo sem provar.** Para cada campo que você achar, confira em
pelo menos 20 jogadores contra o que eu já tenho no banco. Se bater em 20 de 20,
está certo. Se bater em 17, **pare e me diga** — não arredonde.

---

## 7 · O QUE EU JÁ SEI, PARA VOCÊ CONFERIR CONTRA

Cinco casos com resposta conhecida (use como gabarito no passo 4):

| player_id | nome | estilo de jogo | altura |
|---|---|---|---|
| 33185 | Manuel Neuer | Goleiro ofensivo | 193 |
| 40571 | David de Gea | Goleiro ofensivo | — |
| 127038 | Diogo Costa | Goleiro ofensivo | — |
| 143196 | Moises Caicedo | O destruidor | 178 |
| 112932 | Ronaldo Vieira | O destruidor | 178 |

⚠️ **O estilo do Diogo Costa fui eu que pus à mão** — a fonte falhou nele. Se o arquivo
do jogo disser outra coisa, **me avise em vez de "corrigir"**: pode ser que eu esteja
errado, e pode ser que o arquivo esteja desatualizado. Quem decide sou eu.

Os 28 estilos de jogo que o meu sistema conhece:

```
Artilheiro · Homem de área · Pivô · Atacante pivô · Puxa marcação · Clássico nº 10
Armador criativo · Jogador de infiltração · Ala produtivo · Lateral móvel
Perito em cruzamento · Meia versátil · Orquestrador · Primeiro volante · O destruidor
Defensor criativo · Provocador · Atacante surpresa · Zagueiro ofensivo
Lateral atacante · Zagueiro defensivo · Goleiro ofensivo · Goleiro defensivo
Goleiro adiantado
```

---

## 8 · O QUE ME ENTREGAR

Um arquivo **`.jsonl`** — uma linha JSON por jogador — assim:

```json
{"player_id": 33185, "estilo_de_jogo": "Goleiro ofensivo", "altura": 193, "peso": 93, "pe_ruim_uso": 2, "pe_ruim_precisao": 2, "posicao_nativa": "GK", "fonte": "arquivo-do-jogo", "arquivo": "<qual>", "byte": 4812416}
```

Regras do conteúdo:

- **Campo que você não achou não entra na linha.** Não escreva `null`, não escreva `0`.
  Ausente quer dizer "não sei", e isso é uma resposta legítima. **Zero no lugar de
  "não sei" é o pior erro possível no meu sistema** — ele vira nota errada que parece
  certa.
- Junto, um **relatório em português** dizendo: qual arquivo, quantos dos 795 você
  achou, o tamanho do registro, quais campos você decifrou, e **em quantos casos cada
  campo bateu com o gabarito**.
- Se um campo bateu em menos de 100% dos casos conferidos, **diga o número exato** e
  não entregue esse campo como certo.

---

## 9 · O QUE **NÃO** FAZER

- ⛔ Não modifique, não renomeie e não apague **nenhum** arquivo do jogo. É só leitura.
- ⛔ Não instale nada sem me perguntar antes.
- ⛔ Não invente valor. Faltou, faltou.
- ⛔ Não me entregue "provavelmente é isso". Ou provou, ou não provou.

---

## 10 · SE NÃO DER

Se os arquivos forem criptografados, ou se em duas ou três tentativas nada aparecer,
**pare e me diga o que tentou e onde travou**. Não fique tentando a mesma coisa. Não é
o fim do mundo: hoje o sistema já funciona com os sites, e a trava que protege o dado
manual já está no banco. Isto aqui é para **melhorar a fonte**, não para salvar nada.
