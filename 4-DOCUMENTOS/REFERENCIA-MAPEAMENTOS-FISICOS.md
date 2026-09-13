# Referência de mapeamentos físicos

Tabelas de identidade/endereço preservadas dos levantamentos de agosto–setembro de
2026. Contagens de cartas/versões são da evidência original, não valores atuais.
O contrato tipado e as provas da versão extraída governam a operação. Parâmetros de
bônus e estado de implantação devem ser lidos nos manuais atuais, não inferidos daqui.
Sobreposição dos técnicos foi corrigida para bit 192/largura 7; esta referência não
conserva a leitura antiga incorreta no bit 135.

## CORPO

| # | Código | Chinês | Inglês | Português | Arquivo | Endereço | motor |
|---:|---|---|---|---|---|---|---|
| 0 | `PB:248:8` | 身高 | Height (cm) | Altura | Player.bin | bit 248 · w8 · **valor + 100** | usa |
| 1 | `PA:12:0:4` | 大腿尺寸 | Thigh Size | Coxa | PlayerAppearance.bin | byte 12 · bit 0 · w4 | usa |
| 2 | `PA:12:4:4` | 小腿尺寸 | Calf Size | Panturrilha | PlayerAppearance.bin | byte 12 · bit 4 · w4 | usa |
| 3 | `PA:8:20:4` | 腰围 | Waist | Cintura | PlayerAppearance.bin | byte 8 · bit 20 · w4 | usa |
| 4 | `PA:8:16:4` | 胸围 | Chest | Peito | PlayerAppearance.bin | byte 8 · bit 16 · w4 | usa |
| 5 | `PA:8:24:4` | 手臂尺寸 | Arm Size | Tam. braço | PlayerAppearance.bin | byte 8 · bit 24 · w4 | usa |
| 6 | `PA:8:4:4` | 颈围 | Neck Size | Tam. pescoço | PlayerAppearance.bin | byte 8 · bit 4 · w4 | usa |
| 7 | `PA:12:8:4` | 腿长 | Leg Length | Compr. perna | PlayerAppearance.bin | byte 12 · bit 8 · w4 | usa |
| 8 | `PA:8:28:4` | 臂长 | Arm Length | Compr. braço | PlayerAppearance.bin | byte 8 · bit 28 · w4 | usa |
| 9 | `PA:8:0:4` | 颈长 | Neck Length | Compr. pescoço | PlayerAppearance.bin | byte 8 · bit 0 · w4 | usa |
| 10 | `PA:8:12:4` | 肩宽 | Shoulder Width | Larg. ombro | PlayerAppearance.bin | byte 8 · bit 12 · w4 | usa |
| 11 | `PA:8:8:4` | 肩高 | Shoulder Height | Alt. ombro | PlayerAppearance.bin | byte 8 · bit 8 · w4 | usa |
| 12 | `PA:12:12:4` | 头长 | Head Length | Compr. cabeça | PlayerAppearance.bin | byte 12 · bit 12 · w4 | não |
| 13 | `PA:12:16:4` | 头宽 | Head Width | Larg. cabeça | PlayerAppearance.bin | byte 12 · bit 16 · w4 | não |
| 14 | `PA:12:20:4` | 头厚 | Head Depth | Esp. cabeça | PlayerAppearance.bin | byte 12 · bit 20 · w4 | não |


## ESTILO DE IA

| bit | id_texto | Português | cartas |
|---:|---:|---|---:|
| 614 | 15 | Perito em cruzamento antecipado | 5.233 |
| 616 | 11 | Malandro | 5.351 |
| 647 | 19 | Perito em chute de fora da área | 10.004 |
| 649 | 18 | Corrida com gás | 7.820 |
| 674 | 76 | Rápido como uma bala | 7.989 |
| 678 | 77 | Perito em bola longa | 8.321 |
| 680 | 13 | Drible veloz | 9.521 |


## ATRIBUTO

| idx | código | Português (da Konami) | era, nosso |
|---:|---|---|---|
| 0 | `PB:498:6` | Talento ofensivo | Ofensividade |
| 2 | `PB:492:6` | Drible | |
| 6 | `PB:530:6` | Finalização | |
| 12 | `PB:384:6` | Força do chute | |
| 19 | `PB:544:6` | Dedicação defensiva | Envolv. defensivo |
| 21 | `PB:472:6` | Talento de GO | Talento de goleiro |
| 22 | `PB:416:6` | Firmeza do GO | Encaixe |
| 23 | `PB:466:6` | Defesa do GO | Defesa (GO) |


## HABILIDADE

| campo | o que é |
|---|---|
| `efeito` | a tradução numérica. `{"2":{"pct":5}}` |
| `efeito_por_codigo` | o mesmo, por código de atributo: `{"PB:492:6":{"pct":5}}` |
| `efeito_legivel` | `Drible +5%` |
| `codigo_casa` | `sombrero` — a ponte com o motor de hoje |
| `bloqueia_funcoes` | 28 delas bloqueiam alguma função |
| `incidencia` | quão comum é em cada função |
| `gemeas` | efeito idêntico |
| `dominada_por` | 40 têm alguém que as domina em todo atributo |
| `vetada` | 2 — não podem vir como adicional |
| `acessorio` | 3 — condicionais, efeito rebaixado de propósito |
| `so_de_linha` / `so_goleiro` | 36 e 8 |
| `fabricavel` | comum sim, especial não |
| `nome_no_motor` | **ponte temporária**, sai depois da troca |
| | atributo 4 | atributo 5 |
|---|---|---|
| a régua | 10 + 5 + 2,5 = 17,5% | 10 + 5 = 15% |
| se percentual | ceil(72 × 17,5%) = **13** | ceil(74 × 15%) = **12** |
| se ponto | 18 | 15 |
| **o motor gravou** | **13** ✅ | **12** ✅ |


## ÍMPETO

| raw/estado | tipo oficial | asset | cor física medida | hex dominante | UserData | offset no UCAS | Zlib/export | início do payload BC7 |
|---|---|---|---|---|---:|---:|---:|---:|
| `raw0` | Normal | `CmnIconBooster_1` | ciano/turquesa | `#00FFFF` | 84866 | 2213242880 | 5851/11941 B | +1101 |
| `raw1` | Conexão ao vivo | `CmnIconBooster_2` | verde | `#00FF00` | 84867 | 2213249024 | 5523/11941 B | +1101 |
| `raw2` | Conexão com o time | `CmnIconBooster_3` | laranja/âmbar | `#FFA42E` | 84868 | 2213255168 | 6828/11941 B | +1101 |
| `raw3` | Especial | `CmnIconBooster_4` | magenta/roxo | `#FF20FF` | 84869 | 2213263360 | 6486/11941 B | +1101 |
| `raw5` | Vantagem | `CmnIconBooster_5` | amarelo | `#FFE650` | 84870 | 2213271552 | 6722/11941 B | +1101 |
| vaga 136 / marcador `raw4` | não é tipo | `CmnIconBooster_Empty` | cinza escuro | `#4C4C4C` | 84871 | 2213279744 | 5769/11957 B | +1117 |
| estrutura | linhas | o que registra | estado de consumo |
|---|---:|---|---|
| `impeto_condicao_jogo` | 407 | condição canônica, tipo, fonte e regra semântica | 0 aptas |
| `impeto_condicao_nacionalidade_jogo` | 203 | alvo físico de nacionalidade/região | desligado |
| `impeto_condicao_liga_jogo` | 19 | alvo-base de liga/categoria | desligado |
| `impeto_condicao_liga_membro_jogo` | 35 | membros físicos das 19 condições de liga | desligado |
| `impeto_condicao_clube_jogo` | 0 | forma de equipe/clube; nenhum registro atual a usa | vazia de propósito |
| `impeto_condicao_classe_jogo` | 10 | classe do dono, candidato e regra de contagem | desligado |
| `impeto_classe_candidato_jogo` | 408 | classe candidata dos códigos atuais | desligado |
| `impeto_condicao_parametro_faixa_jogo` | 232 | corte bruto e efeito máximo | desligado |
| `impeto_condicao_faixa_jogo` | 696 | três intervalos ordenados por condição | desligado |
| `categoria_time_clube_jogo` | 107 | inventário físico categoria→clube | apoio estrutural; não é consumidor |
