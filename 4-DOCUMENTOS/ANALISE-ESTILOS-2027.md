# ANOTAÇÃO ESPECIAL — OS ESTILOS DE JOGO NOVOS DE 2027
**26/08/2026 · vai junto com o BRIEFING-SESSAO-NOVA.md**

Esta é a análise do assistente (recomendação, NÃO decisão — quem decide é o Luis) sobre
o que fazer com os estilos de jogo que o eFootball 2027 trouxe. O Luis pediu para eu
registrar o raciocínio pra decidir com calma na sessão nova.

---

## 1 · O QUE MUDOU NO JOGO (o fato)
Até 2026 cada carta tinha **UM** estilo de jogo (ofensivo). Em 2027 passou a ter **DOIS**:
- **Estilo ofensivo** (slot 1) — o de sempre (Artilheiro, Meia versátil, Orquestrador…).
- **Estilo defensivo** (slot 2) — **categoria nova**, define o comportamento sem a bola na
  fase defensiva (Pressão no ataque, Cobertura, Mestre da linha alta, Goleiro-líbero…).

Cartas antigas ficaram com "Básico"/duplicado no 2º slot; só os cards novos de 2027 têm
dois de verdade. Medido: **29 estilos novos** (ids fora do catálogo 2026) e **56 ímpetos
novos**. Os 13 defensivos oficiais em PT já estão em `clube.estilo_defensivo_ref`.

## 2 · A PERGUNTA CERTA (formulada pelo Luis)
O 2º estilo (defensivo) se comporta mais como:
- **(A) MOLDE** — afeta a nota/função, como o estilo ofensivo afeta hoje? ou
- **(B) parecido com ESTILO DE IA** — um comportamento/bônus, tratado FORA da régua do molde?

E o Luis já adiantou o lean dele: **não mexer no molde por causa deles.**

## 3 · MINHA ANÁLISE / RECOMENDAÇÃO

**O que um "estilo de jogo" É, por natureza:** uma instrução de comportamento pra IA — diz
COMO o jogador se posiciona e se move. **Ele NÃO altera os 26 atributos** da carta. Isso é
exatamente a mesma natureza do **"estilo de IA"** (`AI_PLAYING_STYLES`) que o nosso sistema
já trata como um FATOR/modificador da nota — não como alvo de atributo.

Por isso, minha recomendação é o **caminho B, com uma ressalva**:

1. **NÃO mexer no molde (nos alvos de atributo).** O molde ranqueia STATS. Os stats da
   carta **não mudaram** por causa do estilo defensivo — então não há motivo pra mexer em
   alvo nem em peso. Concordo 100% com o lean do Luis.

2. **Tratar o estilo defensivo como BÔNUS/MODIFICADOR**, no mesmo lugar onde o sistema já
   trata o estilo de IA e o pé ruim — não como função nova, não como alvo. É a "coisa
   parecida com estilo de IA" que o Luis intuiu.

3. **A ressalva (por que bônus e não zero):** um estilo defensivo que CASA com a função da
   carta a deixa genuinamente melhor naquela função (ex.: um ZC com "Mestre da linha alta",
   um VOL com "Cobertura"). Então faz sentido um **bônus pequeno e positivo** quando o
   estilo defensivo bate com o que a função precisa defensivamente — e **zero quando é
   irrelevante** (ex.: estilo defensivo de goleiro numa carta de ataque). A régua do bônus
   sai da relação estilo-defensivo × função, do mesmo jeito que o peso sai do alvo.

**Resumo da recomendação:** estilo defensivo = **bônus comportamental por função**, na
mesma família do estilo de IA. Molde (alvos) fica intacto. Ofensivo continua sendo o que
define o encaixe na função.

## 4 · O QUE PRECISA SER FEITO ANTES DE DECIDIR (ordem)
1. **Fechar o decode do slot defensivo.** Hoje só saiu 72% de confiança e a busca pelo
   campo real não fechou — **sem isso a gente nem sabe com certeza qual carta tem qual
   estilo defensivo.** É o primeiro passo, técnico. (As 586 cartas "Novo (2027)" dependem disso.)
2. **Mapear os ids novos → os 13 estilos defensivos** (nome PT já está no
   `estilo_defensivo_ref`; casar por posição + amostra em jogo).
3. **Observar em jogo** como cada defensivo funciona de verdade (confirmar que é
   comportamento, não stat) — o Luis pode ajudar aqui, é o que ele conhece.
4. **Montar a régua do bônus por função** (estilo defensivo × função) — aí sim, com o
   Luis, sob a auditoria, e SÓ com ordem dele.

## 5 · INCERTEZAS HONESTAS
- A afirmação "estilo defensivo é comportamento, não stat" vem de como o eFootball funciona
  em geral — **confirmar observando em jogo** antes de cravar.
- O decode defensivo a 72% torna o dado atual **não confiável** pra isso ainda. Não dá pra
  encaixar no bônus enquanto não fechar (pendência 1). Não supor.
