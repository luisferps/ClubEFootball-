# Fechamento da discrepância de habilidades por ID físico

Estado antes da correção: **falha de migração/projeção confirmada**. Não é uma
lacuna aceita e não é prova de que o jogo não possui o dado.

## Identidade usada

- `PlayerSkill.bin`: `skill_id` u32 no offset 0, 72 registros de 104 bytes;
- `Player.bin`: 65 endereços/bit de habilidade; o bit é endereço e pode mudar entre
  versões, não é a identidade;
- `habilidade_jogo.skill_id`: identidade canônica;
- `carta_habilidade_jogo(card_id,skill_id)`: relação canônica com FK.

Nome em português, inglês, japonês, `codigo_casa` e `nome_antigo` não participam do
vínculo. Eles existem somente para apresentação e para explicar a tradução histórica.

## O que divergia e por quê

### Incidência

A referência contém 1.139 linhas. O JSON novo reproduzia 939 e perdia 200 em nove
habilidades porque a carga tentou casar o rótulo. A tradução isolada correta é:

`rótulo da referência antiga → clube.habilidade.nome_antigo → endereço físico/bit
→ habilidade_jogo.skill_id`.

Essa tradução fechou 1.139/1.139, com zero sem mapa e zero ambiguidade. Ela serve
somente para converter a fotografia antiga; o contrato novo guarda e lê
`skill_id+funcao_id`.

| skill_id | endereço na carta | rótulo antigo explicado | relações recuperadas |
|---:|---:|---|---:|
| 3 | 621 | 360 graus | 28 |
| 15 | 625 | Cabeceio | 29 |
| 17 | 676 | Efeito de longe | 28 |
| 22 | 630 | Chutes com decolagem | 29 |
| 26 | 669 | Finaliz. acrobática | 29 |
| 33 | 610 | Passe na medida | 29 |
| 44 | 617 | Repos. baixa do GO | 2 |
| 46 | 666 | Arrem. lateral longo | 24 |
| 47 | 667 | Arrem. longo do GO | 2 |

Nos 19 tipos de função do Otimizador, 1.101 linhas/aliases colapsam sem conflito em
711 pares canônicos. As 38 restantes pertencem exclusivamente a `Meia ofensivo
infiltrador`, função presente na casca histórica, mas ausente dos 19 moldes atuais e
de `funcao_sistema`. Elas não são consumidas hoje e não autorizam inventar uma 20.ª
função ou escolher um ID por semelhança de nome.

### Efeito dos IDs 17 e 33

O legado duplicou cada identidade: uma linha física do `PlayerSkill.bin` tinha
`skill_id` e japonês, enquanto outra linha operacional tinha o endereço da carta e
o efeito, mas não o `skill_id`. O modelo novo já comprovou as pontes físicas:

- skill 17 ↔ bit 676, usado por milhares de cartas;
- skill 33 ↔ bit 610, usado por milhares de cartas.

A projeção descartou o efeito ao escolher a metade com `skill_id`. A correção une as
duas metades pela ponte física já materializada, preserva `skill_id` e converte os
índices do efeito para códigos físicos de atributo:

| skill_id | efeito operacional preservado | efeito por ID físico de atributo |
|---:|---|---|
| 17 | índice 6 +2%; índice 9 +3% | `PB:530:6` +2%; `PB:428:6` +3% |
| 33 | índice 5 +4%; índice 9 +1% | `PB:448:6` +4%; `PB:428:6` +1% |

`PlayerSkill.bin` prova identidade e texto, não contém nesse contrato medido a tabela
percentual do Otimizador. Portanto os percentuais são preservação explícita do
contrato operacional conhecido, não uma alegação falsa de extração binária.

## Relações das cartas

No overlap de 42.803 cartas, 42.799 têm o mesmo conjunto de IDs de habilidade. As
quatro diferenças (`152929`, `155498`, `160233`, `176844`) constam na fotografia
física incremental de 27/08: o novo `Player.bin` adicionou habilidades junto com
outras mudanças reais de atributos/corpo/overall. Elas são atualização física, não
erro de casamento por nome.

Após a promoção de 17 e 33, todos os 65 `skill_id` realmente usados por
`carta_habilidade_jogo` devem estar aptos. Os sete IDs novos sem endereço em carta
continuam fora porque têm zero relações de carta e o endereço físico ainda não foi
aberto; isso não remove nenhum insumo atualmente consumido.

## Prova de independência do rótulo

O gate final deve alterar nomes de apresentação em fixture e repetir:

1. conjunto de habilidades nativas por `skill_id`;
2. efeitos por código físico de atributo;
3. pool, bloqueio e incidência por `skill_id+funcao_id`;
4. resultado da equação.

Os quatro fingerprints e a nota precisam permanecer idênticos; somente o texto de
saída pode mudar.

