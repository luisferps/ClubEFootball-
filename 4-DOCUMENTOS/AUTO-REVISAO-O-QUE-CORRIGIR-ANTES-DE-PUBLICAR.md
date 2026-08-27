# AUTO-REVISÃO — o que eu corrigiria ANTES de publicar
**25/08/2026, manhã.** Pedido do Luis: *"Revise seu próprio trabalho e sinalize
qualquer coisa que você corrigiria antes de eu publicar isso."*
Tudo aqui é **medido**, não opinado. Nada foi publicado.

---

## VEREDICTO EM UMA LINHA

⛔ **Não publicar.** A virada (fase 8) trocou a torneira certa, mas o cano continua
entortado e a régua guardada na casa está com três valores mortos. São **5 coisas**
que eu corrigiria antes, e duas delas eu deixei passar por conta própria.

---

## 1 · A RÉGUA DA CASA ESTÁ COM VALOR MORTO — o erro meu mais grave

**O que eu fiz:** carreguei `clube.parametro` (a receita, camada 3) a partir de
`public.parametros` — 13 chaves em MAIÚSCULO, sem data.

**O que eu deveria ter olhado:** `public.insumo_bonus_parametro` — 13 chaves em
minúsculo, **datadas 16/08**, com descrição em português. É de onde o motor lê:

```
programas/motor_bonus.py:336   ins['parametros']['estilo_ativo']
programas/motor_bonus.py:343   ins['parametros']['estilo_ia_ponto']
programas/motor_bonus.py:344   ins['parametros']['estilo_ia_teto']
programas/motor_bonus.py:360   CORPO_MAX = ins['parametros']['bonus_corpo_max']
```

**Três regras estão vivas em duas versões, e a casa guardou a MORTA:**

| regra | na casa (o que eu pus) | o que o motor usa | quem está certo |
|---|---|---|---|
| bônus de corpo | `BONUS_CORPO={20:−2,70:+2,90:+4}` | `bonus_corpo_max = 1.5` | o motor — a de −2/+4 está morta desde 10/08 |
| estilo de jogo da IA | `BONUS_IA_PONTO=0.4` · `BONUS_IA_TETO=5` | `estilo_ia_ponto=1.0` · `estilo_ia_teto=4` | o motor — **zero cartas têm 5**; o máximo do jogo é 4 |
| — | (não carregado) | `estilo_ativo`, e os **9 do pé ruim** | faltam na casa |

**A prova de que o teto é 4:** a tela mostra `2 de 5 · bônus +0.5`. Pela régua velha
(0,4 × 2, teto 5) daria **+0,8**. Pela vigente (2÷4 × 1,0) dá **+0,5** — que é o que
está na tela. A conta já é a nova; só o rótulo e a minha carga ficaram para trás.

**O tamanho do estrago, com honestidade:** os números de hoje **estão certos** — foram
gerados pelo motor lendo a régua certa. O perigo é o futuro: **na fase 9 o motor passa
a ler da casa** — e leria a régua errada, recalculando 17.798 linhas com a regra morta.

⚠️ **E a auditoria não pegou.** As 33 conferências olham dicionário, receita, carta,
resultado e o espelho da tela — **nenhuma pergunta se a régua que a casa guarda é a
mesma que o motor lê**. Ponto cego meu. Vai virar conferência nova.

---

## 2 · A TELA CONTINUA BAIXANDO O BANCO INTEIRO (a sua reclamação de hoje)

Você disse: *"está carregando linhas ainda, não é pra carregar linhas não aí — ele não
é pra puxar diretamente do banco de dados?"* Está certo. Medido:

| o que acontece hoje | número |
|---|---|
| linhas que o navegador baixa antes de trabalhar | **17.504** |
| peso de cada linha (JSON) | **3.051 bytes** |
| **total que desce pelo cabo** | **51 MB** |
| requisições para montar a tela | **~19** |
| dessas, **síncronas** (travam a renderização) | **3** — 2.000 + 1.000 + 1.000 linhas |
| o que o Ranking realmente usa de cada linha | **~20 campos escalares** |
| o que vem junto e ele não usa | `arows` (591 B), `pool`, `falta`, `fab`, `sis`, `base`, `HAB`, `adds`… |

É **20× mais dado do que a tela precisa**, e as 3 chamadas síncronas são exatamente o
"demora pra renderizar". O aviso verde no canto (`_carregando_banco`) é o "carregando
linhas" que você viu.

**E ainda tem dado congelado dentro do próprio código:**

| constante | arquivo | tamanho | o que é |
|---|---|---:|---|
| `BONUS_PRONTO` | dados-e-catalogos.js | **1.050 KB** | 17.463 bônus já calculados |
| `CORPO_EFHUB` | dados-e-catalogos.js | 308 KB | medidas de corpo de 10.056 cartas |
| `BOXHIST` | motor-e-ficha-base.js | 192 KB | 1.026 boxes históricas |
| `PACOTE` | motor-e-ficha-base.js | 151 KB | 3.133 ids → campanha |
| `PR_RAW`, `FILA`, `CAT`, `ESTV`, `FIS_*`… | os dois | 297 KB | resto |
| **soma** | | **2.021 KB** | **67% do JS é dado, não lógica** |

Tudo isso já existe no banco (`box`, `carta.corpo`, `bonus`, `impeto_fabricavel`).
Isto é o item **1B do plano — "o sistema arrumado"** — que eu **pulei** para ir direto
à virada. Foi o erro de sequência que você apontou.

⚠️ **Tamanho da cirurgia, para você decidir com o número na mão:** **126 pontos** do
código leem o array global `D`. Por isso proponho em dois tempos: primeiro a lista fica
leve (a tela pede só os campos do ranking, e a ficha pede o resto do card **quando
abre**) — cai de 51 MB para ~2,5 MB sem mexer nos 126; depois, ordenar/filtrar/paginar
no banco.

---

## 3 · AS IMAGENS ESTÃO PENDURADAS NO SERVIDOR DO EFHUB

Sua ordem de hoje (trazer as imagens no coletor) tem um motivo maior do que parecia.
O site monta a foto assim, em **6 lugares** do código:

```
https://efimg.com/efootballhub22/images/player_cards/{id}_l.png
```

É **hotlink direto do efHub**. Se eles bloquearem ou mudarem o caminho, **some a foto de
todas as cartas** — num sistema que vai ser pago. E a casa nova (`clube.carta`) **não tem
coluna de imagem nenhuma**.

O que já existe hoje: `cards_v2` com **2.080 de 42.807** com Cloudinary · `cards_efhub`
com **9.719 de 10.218** com imagem. Ou seja: a maior parte não está guardada em lugar
nosso. Entra no coletor (id + ficha + **imagem**) e numa tabela de imagem com procedência.

---

## 4 · A PASTA DE TRABALHO NÃO FOI ORGANIZADA DE VERDADE

Você pediu: apagar duplicados, juntar em pastas internas, **renomear para nomes
intuitivos**. Eu organizei — e entreguei dentro de `CLUBEFOOTBALL-OFICINA.zip`.
**A pasta continua bagunçada**, com o site velho solto na raiz:

```
Clubefootball 2026-08-25\
  ├ 1-SISTEMA\ 4-DOCUMENTOS\ 5-COLETA-EM-PARALELO\      ← o novo, certo
  ├ CLUBEFOOTBALL-OFICINA.zip                            ← a organização presa no ZIP
  ├ ClubEfootball-V3-main\  SITE-ATUALIZADO-2026-08-24\  ← duas cópias do mesmo site
  ├ TELA-CLUBEFOOTBALL-UNICA.html (3,1 MB)
  └ 11 arquivos .js/.css soltos na raiz (a cópia VELHA — foi a que você abriu primeiro)
```

**Foi isso que te fez abrir o arquivo errado.** Tem que ficar uma árvore só.

---

## 5 · AS PENDÊNCIAS DO GPT — eu não tinha lido a lista dele

Li agora (`3-TRANSFERENCIA-GPT\03-CADERNOS-E-PENDENCIAS`). São **12 consertos** (16/08)
e **8 passos de reforma**, dos quais 4 fechados por ele e **4 ainda abertos**.

### O que a casa nova já matou (conferido, com número)
| item do GPT | estado hoje na casa |
|---|---|
| passo 1 · tradutor (438 linhas) | ✅ `clube.traducao` = 438 |
| passo 2 · código fixo da função | ✅ `clube.funcao` por `codigo`, 19 |
| passo 3 · versões do molde | ✅ `receita_versao` v1→v5, **v5 vigente**, 494 itens |
| passo 4 · os quatro estados | ✅ `carta.estado` + os campos que faltavam |
| #5 e #8 · campos que só existiam no HTML | ✅ viraram coluna: idade 3.255 · forma/condição 3.230 · pé ruim 3.252/2.760 · lesão 2.706 · máx/tier 6.252 |
| a chave dupla (carta × carta@posição) | ✅ `card_id` e posição separados |

### O que continua aberto (é isto que falta)
| # | o quê | de quem |
|---|---|---|
| 1 | ímpeto condicional **+3 rende menos que +2** (Messi, 112,20 × 112,23) | motor — **não conferido** |
| 2 | estilo da IA mostra **"2 de 5"**, o teto é **4** | tela (é o mesmo erro do item 1 daqui) |
| 3+7 | tabela do físico na ficha com a **régua velha** (escala −2/+2, "+64%") | tela + banco |
| 4 | carta que **sobe de posição** não recebe as duas funções novas | fila/motor |
| 6 | o "NÃO SEI" saiu do modal e **ficou sem lugar nenhum** (29.695 medidos) | tela |
| 10 | a trava da impressão digital **não sabe o que mudou** | nossa trava |
| 11 | **1.561 conflitos entre fontes** resolvidos em silêncio | banco |
| 12 | a pontuação da tela **muda sozinha** quando entra carta | tela (é o `_TOPO` recalculado a cada leva) |
| P5 | **o motor de atualização** (é o Alimentador) | não existe ainda |
| P6 | o vigia vira **boca do motor** (vê 137 cartas inéditas e não faz nada) | não existe ainda |
| P7 | **a volta automática**: insumo mais novo que o produto volta pra fila sozinho | não existe ainda |
| P8 | **os motores leem do banco e a tela para de calcular** | é o item 2 daqui |

E as **dívidas sem proveniência** dele, que continuam de pé: o peso 5 da altura sem
conta escrita · o molde do físico sem programa que o reproduza · a metade da habilidade
perdedora nunca testada contra o jogo · **o motor de atributos nunca auditado** (pendência
aberta por sua ordem em 15/08) · 15 códigos de ímpeto órfãos · a pontuação não comparável
entre funções (teto do goleiro 314 × volante 482).

---

## ORDEM QUE EU PROPONHO

```
1º  a régua da casa           (item 1) — é rápido e é o que corrompe o motor depois
2º  a pasta organizada        (item 4) — uma árvore só, pra parar de abrir arquivo velho
3º  a tela sob demanda        (item 2) — em dois tempos, o leve primeiro
4º  as imagens no coletor     (item 3) — pode rodar em paralelo com o 3º
5º  os consertos do GPT       (item 5) — um a um, começando pelos da tela
6º  só então: homologar e publicar
```

O motor continua parado — **marcar ≠ rodar**, e a rodada é ordem sua.
