# eFootball 2027 (PC/Steam) — onde fica o 2º estilo de jogo por carta?
**Relatório técnico · 26/08/2026 · para consulta externa**

## O QUE EU QUERO DESCOBRIR
No eFootball 2027 cada carta passou a ter **dois estilos de jogo**: o slot antigo
(Artilheiro, Orquestrador, Lateral defensivo…) e um **segundo slot defensivo** novo
(Interceptador de passe, Mestre da linha alta, Pressão no ataque…).

**Eu decodifico o primeiro slot com sucesso. Não consigo achar onde fica o segundo.**

---

## O QUE JÁ ESTÁ RESOLVIDO (não preciso de ajuda aqui)

Escrevi meu próprio extrator (JavaScript, roda no navegador). Ele faz:
- **CPK**: parse da tabela @UTF (com a deobfuscação XOR seed `0x655f`, multiplicador
  `0x4115`) + descompressão CRILAYLA.
- **WESYS**: decifra com xorshift128. Nibble = `data[1] & 15`. Chaves:
  `KEY[1] = [378445824, 774547186, 214490323]`,
  `KEY[2] = [0xED5B2960, 1246903118, 0xF3A31BAD]`.
  `comp = u32(data,8)`, `orig = u32(data,12)`, payload a partir do byte 16, depois zlib inflate.
- Isso abre `Player.bin`, `PlayerVariationDetail.bin`, `all.str`, etc.

**Formatos de registro do Player.bin (medidos):**
- `dt200_console_all.cpk` → registro de **400 bytes**, 23.519 cartas (temporada 2026)
- `dt870_console_win.cpk` → registro de **392 bytes**, 34.303 cartas (temporada 2027)
- `card_id` = u64 little-endian no offset 8 dos dois formatos.
- Prova de que o dt870 é 1 ano mais novo: nas cartas presentes nos dois arquivos, a idade
  do dt870 é 100% dentro de ±1 da do dt200.

**Campos que mapeei no formato 392 (bit offsets, validados cruzando com o dt200):**
26 atributos (largura 6, valor +40) · altura (bit 248, w8, +100) · peso (280, w7, +30) ·
idade (**524**, w6, +10) · posição (548, w4) · nacionalidade (328, w10) · pé (644, w1) ·
pé-ruim freq (510, w2) / precisão (571, w2) · forma (576, w2) · lesão (567/568) ·
**65 habilidades** (bits individuais) · 12 aptidões (w2) · 7 estilos-IA ·
**ímpeto slot 1 (bit 308, w8) e slot 2 condicional (bit 288, w8)** — esses dois batem 100%
com o formato 400 · **nome latino** no byte 328 (no formato 400 é o campo 3 da região de
nomes: byte 271, stride 61).

**Primeiro slot de estilo:** bit **185**, largura 8, id = `valor - (valor % 4)`.
Validado: bate com meu banco (que tem o estilo em português por carta) com pureza de
96–100% por id — ex.: 267/267 no Artilheiro, 223/223 no Jogador de infiltração.
Tabela de ids: 4=Artilheiro, 8=Puxa marcação, 12=Homem de área, 16=Ala produtivo,
20=Clássico nº10, 24=Jogador de infiltração, 28=Meia versátil, 32=Primeiro volante,
36=O Destruidor, 40=Atacante surpresa, 44=Lateral ofensivo, 48=Lateral defensivo,
52=Atacante pivô, 56=Armador criativo, 60=Defensor criativo, 64=Goleiro ofensivo,
68=Goleiro defensivo, 72=Lateral móvel, 76=Perito em cruzamento, 80=Orquestrador,
84=Lateral atacante, 88=Pivô.

**Catálogo dos 13 estilos DEFENSIVOS** (extraí da tabela de textos em PT do próprio jogo:
`dt261_bra_console_win.cpk` → `all.str`, cifrado em WESYS), nesta ordem no arquivo:
1 Pressão recuada · 2 Pressão no ataque · 3 Ladrão no ataque · 4 Saída ofensiva ·
5 Defensor participativo · 6 Interceptador de passe · 7 Cobertura · 8 Mestre da linha alta ·
9 Marcador forte · 10 Defensor recuado · 11 Goleiro-líbero · 12 Goleiro construtor ·
13 Goleiro adiantado (+ Básico).

---

## O PROBLEMA 1 — não acho o campo do 2º estilo

Varri **todo o registro de 392 bytes**, larguras 4 a 8, em todas as posições de bit,
filtrando por várias assinaturas combinadas:
- valores dentro de 0..13 (índice) **ou** múltiplos de 4 (mesmo espaço de id do slot 1);
- goleiro só podendo receber os 3 estilos de goleiro, e esses valores não aparecendo fora
  do gol;
- distribuição dos valores compatível com as posições oficiais de cada estilo defensivo;
- campo majoritariamente "Básico" (a maioria das cartas não tem o 2º estilo);
- casos "duplicados" (mesmo estilo nos dois slots) existindo.

**Nenhum candidato passa em todos ao mesmo tempo.** Os melhores (bit 652 w5, bit 605 w4,
bit 445 w4) sempre falham em pelo menos um teste — tipicamente a distribuição por posição
não fecha, ou os valores de goleiro vazam para jogadores de linha.

Também suspeito de falso positivo fácil: como os ids de estilo são múltiplos de 4, **muito
campo do registro casa por coincidência** (atributos, aptidões), então "os valores caem na
tabela de estilos" não prova nada sozinho.

## O PROBLEMA 2 — as cartas atuais não estão no arquivo

Este talvez explique o problema 1. Testei com cartas concretas que existem no jogo hoje:

| Carta (como aparece no jogo) | No `Player.bin` do dt870? |
|---|---|
| Tijani Babangida, Épico, Nigeria 1998, 84 PTD, *Ala produtivo + Pressão no ataque* | **Ausente** (nem por nome, nem pelo box) |
| Shibasaki Gaku, Épico, Kashima Antlers 2016, 84 MLG, *Orquestrador + Interceptador de passe* | **Ausente** (box "Kashima Antlers 2016" tem 0 cartas) |
| Usami Takashi, Épico, Gamba Osaka 2014, 85 SA, *Clássico nº10 + Ladrão no ataque* | **Ausente** (box "Gamba Osaka 2014" só tem o Endo) |
| Paolo Maldini, Épico, Italy 2000, 89 ZC, *Defensor criativo + Mestre da linha alta* | **Presente mas diferente**: `88039045074370`, **LB**, ovr **86**, estilo *Lateral defensivo* |
| Jay-Jay Okocha, `88039850384107` | Presente, *Armador criativo* correto, **mas 2º slot vazio** |

O box link vem de `PlayerVariationDetail.bin` (registro de **168 bytes**: card_id u64 no
offset 0, u32 no 8, e o nome do box como string a partir do byte 12) — 11.522 vínculos,
1.724 boxes. A box mais recente ali é de **5 de janeiro de 2026**, embora o `.cpk` tenha
data de arquivo 13/08/2026. As boxes de 2026 (incl. a "Catenaccio" de 23/08/2026) não estão.

**Onde procurei o conteúdo atual e não achei:**
- Os 18 `.cpk` da pasta `cpk\` — só `dt200` e `dt870` têm dados de jogador. O `dt230`
  (203 MB) é só animação/motion. O `dt261_bra` é texto.
- `Steam\userdata\<id>\1665460\` — só 4 arquivos de config, ~5 KB.
- `Documents\KONAMI\eFootball\ST\SaveData\<steamid>\` — só `SYSTEM000` (454 KB, cifrado
  com esquema diferente, **não é WESYS**, alta entropia) e `GRAPHICS000000` (19 bytes).
  Procurei "Babangida", "Okocha", "Kanu", "Nigeria" como texto: nada.

---

## AS PERGUNTAS

1. **Em qual arquivo e em qual offset/bit fica o segundo estilo de jogo (defensivo) de
   cada carta no eFootball 2027 (PC/Steam)?** Se for no `Player.bin` do
   `dt870_console_win.cpk` (registro de 392 bytes), qual o bit e a largura, e a
   codificação é índice 1–13 ou id múltiplo de 4?

2. **As cartas Épicas recentes (ex.: Tijani Babangida, box Nigeria 1998) existem em algum
   arquivo local no PC?** Se sim, em qual — e como se extrai? Se não, confirma que a
   definição dessas cartas vem do servidor em tempo de execução?

3. **Como sites de banco de dados (efootballhub, efootballdb) obtêm as cartas novas no
   mesmo dia do lançamento da box?** Extração de arquivo ou captura da resposta do
   servidor/API?

4. Existe algum arquivo tipo `PlayStyle.bin` / `PlayerPlayStyle.bin` no eFootball 2027 PC?
   Não encontrei nenhum com esse nome nos 18 `.cpk` — os únicos arquivos de jogador são:
   `Player.bin`, `PlayerAppearance.bin`, `PlayerAssignment.bin`, `PlayerBooster.bin`,
   `PlayerDeleteList.bin`, `PlayerVariationDetail.bin`, `PlayerVariationPrSkill.bin`,
   `PlayerWeekly.bin` (e no dt200 também `PlayerSkill.bin` e
   `PlayerVariationAdditionalInfo.bin`).

5. O `PlayerVariationPrSkill.bin` (659 bytes no dt870, 1.021 no dt200) — "PrSkill" é
   *playing style*? É pequeno demais para ser por carta, mas pode ser uma tabela de
   definição. Vale decifrar?
