# MAPA — Onde fica cada coisa dentro do código do jogo (eFootball)
_Build do Steam do Luis · medido em 25/08/2026 abrindo o CPK._

Marcação: ✅ ABERTO e parseado · 🔶 CONVENÇÃO (tamanho/nome, não aberto — não é afirmação fechada).

## 1 · Os três mundos do jogo
Pasta de instalação: `...\Steam\steamapps\common\eFootball\`

| pasta | o que é | tem estatística de carta? |
|---|---|---|
| **`cpk/`** | dicionário de dados (CRI CPK). Jogador, time, técnico, competição, ímpeto. | **SIM — é aqui** |
| **`pak/`** | assets em Unreal Engine 5 (.ucas/.utoc/.pak): modelo 3D, textura, UI. | não |
| **`Engine/` + `Binaries/`** | motor UE5 + executável | não |

## 2 · As camadas `dt` do cpk
Regra: número maior + `_win` **SOBRESCREVE**. Banco vivo = **dt870 sobre dt200**.

| arquivo | tamanho | estado | conteúdo |
|---|---|---|---|
| dt000_all | 832 MB | 🔶 | base/master |
| **dt200_all** | 9,9 MB | ✅ | **banco de jogador base — 23.519 cartas** + catálogos |
| dt220_all | 3 MB | ✅ | esqueleto/animação |
| dt230_win | 203 MB | 🔶 | aparência/rosto |
| dt240_all | 5,9 MB | ✅ | malha |
| dt250_all | 2,3 MB | ✅ | 1094 modelos |
| dt251·270·520 | <0,2 MB | ✅ | config |
| dt260·261_bra | <0,3 MB | 🔶 | texto/região |
| dt500_all | 256 MB | 🔶 | textura/modelo |
| dt510_bra·jpn | 1,2·1,5 GB | 🔶 | áudio de narração |
| dt530_bra·jpn | <0,3 MB | 🔶 | texto/região |
| dt540_all | 957 MB | 🔶 | modelo/textura |
| **dt870_win** | 5 MB | ✅ | **banco de jogador ATUAL — 33.616 cartas** + competição/equipamento |

**dt870 é o "33 mil".** 33.616 registros, 11.013 especiais, 11.860 IDs que o dt200 não tinha.

## 3 · Dentro do banco — arquivo por arquivo (cada .bin é um container WESYS)
| arquivo | o que guarda |
|---|---|
| **Player.bin** | uma linha por carta, 400 bytes — ver seção 4 |
| PlayerBooster.bin | catálogo de ímpetos (195 definições) — não é por carta |
| PlayerVariationDetail.bin | coleções Epic/Legend (time-temporada), 1375 variações |
| PlayerWeekly.bin | POTW |
| PlayerSkill.bin | catálogo de habilidades |
| Playstyle.bin | catálogo de estilos |
| PlayerAssignment.bin | jogador → time |
| SpecialPlayerAssignment.bin | carta especial → coleção |
| Team/Coach/Country.bin | times, técnicos, nacionalidades |
| Competition*/BootsList.bin | campeonatos, equipamento |

## 4 · Dentro do Player.bin — os 400 bytes da carta (offsets em BIT)
| campo | posição |
|---|---|
| ID da carta (PID) — mesmo esquema do nosso card_id | offset 8 · u64 |
| Posição | bit 556 · w4 |
| Nacionalidade | bit 328 · w10 |
| Estilo de jogo | bit 372 · w8 |
| Estilo secundário | bit 440 · w6 |
| Atributos (26) | bit 480 · 6b cada |
| Habilidades | bit 664 |
| Estilos de IA | bit 678 |
| Pé (uso/precisão) | bit 654 / 478 / 578 |
| Nome (especiais em japonês) | offset 88 |
| **ÍMPETO — vaga + ímpeto de fábrica** | **bytes 36–39** (sem vaga → byte38=0; vaga vazia → bits 311/315; cheia+vaga → byte36=0x88; qual ímpeto → bits 308–312) |

## 5 · Featured / Epic / POTW
No **Player.bin do dt870** (33.616 cartas, 11.013 especiais). Nome da coleção no
PlayerVariationDetail.bin; POTW no PlayerWeekly.bin. ID = mesmo esquema do card_id.
**94% das bases das nossas featured (3.007/3.189) estão no arquivo.** Casamento por
base + digital (atributos/estilo), não por ID cru.

## 6 · Como se abre
1. **CPK** (CRI): `CPK ` + tabelas `@UTF` + compressão **CRILAYLA**. Extrator próprio OK.
2. **WESYS** (cada .bin): 16 bytes header + XOR-stream (xorshift128, chave do eFootball.exe) + zlib.

_Método: extração real do CPK do Steam, decifra WESYS, cruzamento por card_id e base
(18 bits) contra 23.519 (dt200) e 33.616 (dt870). O que não foi aberto = convenção._

## 7 · Técnicos e nacionalidades — mapeamento comprovado em 28/08/2026

Fonte autoritativa para os técnicos atuais: DT870 atualizado. A identidade é cada
registro/card-versão, pelo ID físico `u64`; o nome não é chave.

| dado | arquivo | registro/endereço | decodificação |
|---|---|---|---|
| ID do técnico | `Coach.bin` | 176 bytes; byte 0 | u64 little-endian |
| nomes JP/latino/CN | `Coach.bin` | offsets 32/78/124 | UTF-8 terminado por NUL |
| idade | `Coach.bin` | bit 231, largura 7 | valor físico + 14 |
| nacionalidade | `Coach.bin` | bit 170, largura 8 | FK para código de `Country.bin` |
| afinidade | `Coach.bin` | bit 187, largura 3 | código 0 = ausência legítima |
| Posse de bola | `Coach.bin` | bit 206, largura 7 | proficiência 0–99 |
| Contra-ataque | `Coach.bin` | bit 238, largura 7 | proficiência 0–99 |
| Contra-ataque rápido | `Coach.bin` | bit 224, largura 7 | proficiência 0–99 |
| Passe longo | `Coach.bin` | bit 199, largura 7 | proficiência 0–99 |
| Por fora | `Coach.bin` | bit 213, largura 7 | proficiência 0–99 |
| Sobreposição | `Coach.bin` | bit 135, largura 7 | zero = ausência legítima; no arquivo atual, somente Antônio Conte tem 96 |
| código da nacionalidade | `Country.bin` | registro de 1.488 bytes; bit 10, largura 9 | inteiro sem sinal |
| sigla | `Country.bin` | offset 708, largura máxima 10 | ASCII/UTF-8 terminado por NUL |
| nome pt-BR | `Country.bin` | offset 788, largura máxima 70 | UTF-8 terminado por NUL |
| rótulo da afinidade 5 | `all.str` de `dt261_bra` | `Any1W:495` | `Jogadores de AT`; tela observada `Atacantes` |

O `Country.bin` auditado é byte-idêntico em DT200, DT870 original e DT870 atualizado.
São 214 códigos únicos; os 1.478 técnicos atuais resolvem todos, sem órfãos. Os
rótulos das afinidades 1, 2, 3, 4, 6 e 7 não foram vinculados fisicamente e não devem
ser inferidos. A procedência reproduzível também está registrada nas linhas
granulares correspondentes de `clube_novo.mapa_do_jogo`, inclusive
`tecnico.estilo.sobreposicao`.
