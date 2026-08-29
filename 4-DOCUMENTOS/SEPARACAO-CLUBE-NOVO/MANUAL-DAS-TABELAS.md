# MANUAL DAS TABELAS — ClubEFootball

**Aberto em 27/08/2026.** Diz, assunto por assunto, **qual é a tabela oficial**.

Para que serve: quando estiver completo, a gente varre os motores e a tela e **troca
toda chamada por nome pela chamada por código**. Nada é apagado antes dessa troca.

---

## AS TRÊS REGRAS QUE VALEM PARA TUDO

**1 · A chave é o código do jogo, nunca o nome.**
Se a Konami renomear qualquer coisa amanhã, nada quebra — muda só a etiqueta.

**2 · O nome vem do código do jogo.**
Lido do `all.str` pelo `id_texto`. O nome que a casa usava fica em `nome_antigo`,
só para casar dado velho.

**3 · Zero é resposta. `null` é ausência de resposta.**
`efeito = {}` quer dizer *apurado, não tem efeito* — roda normal.
`efeito = null` quer dizer *nunca apurado* — **trava o motor**.
Toda tabela tem `pode_rodar` e `falta_o_que`, e a view `clube.insumo_incompleto`
junta os buracos de todas num lugar só.

---

## ESTADO DE HOJE

| tabela | linhas | rodam | **travam** |
|---|---:|---:|---:|
| `clube.texto_do_jogo` | 211 | — | — |
| `clube.atributo_jogo` | 26 | 26 | 0 |
| `clube.corpo_ordem` | 15 | 15 | 0 |
| `clube.pe` | 11 | 11 | 0 |
| `clube.posicao_jogo` | 13 | 13 | 0 |
| `clube.playstyle` | 36 | 36 | 0 |
| `clube.estilo_ia` | 7 | 7 | 0 |
| `clube.habilidade_jogo` | 72 | 63 | **9** |
| `clube.impeto_jogo` | 440 | 0 | **440** |
| `clube.tecnico_jogo` | **0** | 0 | 0 |

Fotografia conferida diretamente no banco em 27/08/2026. `carta_jogo` contém
42.803 cartas; `impeto_atributo_jogo`, 1.542 relações. As seis relações de carta
estão criadas e vazias; `funcao_sistema` tem 19 linhas, `funcao_alias` tem 14 e
`mapa_do_jogo` tem 21.

## MODELO NOVO — SCHEMA `clube_novo`

Esta é a fronteira oficial e fisicamente materializada do modelo novo. O schema
`clube_novo` contém **exatamente as 21 tabelas abaixo**;
índices e sequências pertencentes a elas serão objetos auxiliares do PostgreSQL,
não tabelas adicionais.

**Status em 27/08/2026: cópia paralela aplicada.** A migração
`20260827183648_criar_clube_novo_copia_paralela_21_tabelas` criou e carregou
`clube_novo` sem mover, renomear, apagar ou alterar as fontes em `clube`.
As duas versões têm as mesmas contagens e fingerprints da fotografia desta
rodada. As dez rotinas que consomem este conjunto continuam apontando somente
para `clube`; nenhum motor, rotina, view ou tela foi redirecionado.

O schema novo nasce privado: `anon`, `authenticated`, `authenticator` e
`service_role` não têm `USAGE`. As duas tabelas que já tinham RLS
(`funcao_sistema` e `funcao_alias`) preservam RLS e a policy pública de leitura;
as outras 19 preservam o estado sem RLS da fonte, sem ficarem expostas pela
Data API enquanto o schema continuar fechado.

| grupo | tabela | finalidade | chave primária | relações principais |
|---|---|---|---|---|
| catálogo | `texto_do_jogo` | dicionário de textos oficiais por seção e idioma | (`secao`, `id_texto`) | nomes usados pelos demais catálogos |
| catálogo | `atributo_jogo` | catálogo dos 26 atributos pelo endereço estável | `codigo` | destino de `carta_atributo_jogo` |
| catálogo | `corpo_ordem` | catálogo ordenado das 15 medidas e endereços do corpo | `codigo` | destino de `carta_corpo_jogo` |
| catálogo | `pe` | domínio dos três campos de pé e seus valores | (`campo`, `valor`) | dado estruturado da carta |
| catálogo | `posicao_jogo` | catálogo das 13 posições do jogo | `id` | destino de `carta_posicao_jogo` |
| catálogo | `playstyle` | catálogo dos 36 estilos de jogo | `id_jogo` | dado estruturado da carta |
| catálogo | `estilo_ia` | catálogo dos sete bits de estilo de IA | `bit` | destino de `carta_estilo_ia_jogo` |
| catálogo | `habilidade_jogo` | catálogo das 72 habilidades pelo id da Konami | `skill_id` | destino de `carta_habilidade_jogo` |
| catálogo | `impeto_jogo` | catálogo de ímpetos publicado nos arquivos do jogo | `codigo_jogo` | destino de `carta_impeto_jogo` |
| catálogo | `tecnico_jogo` | catálogo de técnicos pelo id do jogo | `id` | ainda vazio |
| carta | `carta_jogo` | cadastro principal das 42.803 cartas pelo id original da Konami | `card_id` | origem das seis relações normalizadas de carta |
| carta | `carta_atributo_jogo` | carta × atributo, com o valor do atributo | (`card_id`, `codigo_atributo`) | FKs para `carta_jogo` e `atributo_jogo` |
| carta | `carta_corpo_jogo` | carta × medida corporal, com o valor | (`card_id`, `codigo_corpo`) | FKs para `carta_jogo` e `corpo_ordem` |
| carta | `carta_habilidade_jogo` | carta × habilidade, com a ordem quando informada | (`card_id`, `skill_id`) | FKs para `carta_jogo` e `habilidade_jogo` |
| carta | `carta_estilo_ia_jogo` | carta × bit de estilo de IA | (`card_id`, `bit_estilo_ia`) | FKs para `carta_jogo` e `estilo_ia` |
| carta | `carta_posicao_jogo` | carta × posição, com nível de aptidão | (`card_id`, `posicao_id`) | FKs para `carta_jogo` e `posicao_jogo` |
| carta | `carta_impeto_jogo` | os dois slots de ímpeto da carta, incluindo vaga e condição | (`card_id`, `slot`) | FKs para `carta_jogo` e `impeto_jogo` |
| catálogo | `impeto_atributo_jogo` | relação ímpeto × atributo publicada no arquivo | (`codigo_impeto`, `codigo_atributo`) | FKs para `impeto_jogo` e `atributo_jogo` |
| sistema | `funcao_sistema` | catálogo canônico das 19 funções internas | `id` | alvo de `funcao_alias`; id protegido por trigger |
| sistema | `funcao_alias` | aliases comprovados dos nomes legados | `id` | FK `id_funcao` para `funcao_sistema`; alias normalizado único |
| procedência | `mapa_do_jogo` | inventário de arquivo, chave, endereço e estado de apuração | (`assunto`, `arquivo`) | 21 registros técnicos de procedência |

### Por que as três tabelas de sistema entram

- `funcao_sistema` declara no próprio catálogo a procedência
  `regra_interna_sistema`, tem 19 ids numéricos imutáveis e é descrita no banco
  como catálogo oficial das funções criadas pelo sistema.
- `funcao_alias` foi criada pela migração
  `20260827161638_criar_funcao_alias_compatibilidade_legado`; seus 14 aliases
  apontam por FK para `funcao_sistema` e não criam funções adicionais.
- `mapa_do_jogo` é o registro técnico de procedência do modelo: identifica a
  fonte, a chave, o endereço, o tamanho do registro e o estado de apuração.

### Relações internas e fronteira com o legado

`carta_jogo` e `impeto_atributo_jogo` fazem parte da fronteira oficial. Assim,
as seis relações de carta e as duas relações de ímpeto ficam integralmente em
`clube_novo`, sem FKs cruzadas com tabelas do schema legado.

A view `clube.insumo_incompleto` permanece em `clube`, consultável e sem
redirecionamento. As dez rotinas com nomes textuais qualificados continuam
lendo as fontes antigas de propósito, até o futuro mapeamento leitura antiga X
→ tabela nova Y.

Os três gatilhos de usuário foram recriados na cópia somente depois da carga,
portanto não dispararam durante a replicação. Suas funções continuam no schema
`clube`, como dependências externas de transição:
`clube.tg_cap_do_id()`, `clube.tg_carta_entrou()` e
`clube.impedir_alteracao_funcao_sistema_id()`. Não existe FK de
`clube_novo` para fora do próprio schema.

---

# 0 · A CHAVE DO JOGO — `clube_novo.texto_do_jogo`

O `all.str` é um **dicionário indexado**: cada texto tem um **id explícito**.
Esse id é a chave da Konami para tudo que aparece na tela.

```
all.str  (dt261_bra_console_win.cpk · bra/string · WESYS+zlib · 783.360 bytes)

header ......... u32 nº de seções (188), depois 12 bytes por seção:
                 offset do nome · início · tamanho
cada seção ..... 8 bytes de cabeçalho (quantas entradas · tamanho)
cada entrada ... 12 bytes:  id (u32) · tamanho · tamanho visível · offset
```

| seção | o que tem |
|---|---|
| `E13W` | habilidades, estilos de IA, estilos defensivos, Básico |
| `E5T` | atributos e os rótulos do pé ruim |
| `E6T` | estilos de jogo ofensivos |
| `Any3T` | **a lista oficial dos 26 atributos** (ids 483–508) e os nomes de ímpeto |
| `Any2T` | as 11 famílias de ímpeto (ids 842–852) |
| `PlayC` | as posições, sigla e nome com ids separados |

O idioma é coluna, não chave: troque o `dt261_bra` por outro idioma e os ids são os mesmos.

---

# 1 · CORPO — `clube_novo.corpo_ordem`

**15 medidas**, todas com endereço exato.

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

**Três coisas de propósito:** não tem japonês (o extrator veio de editor chinês);
não tem id da Konami (o jogo não cataloga medida, só grava o número — a identidade
é o endereço); a altura mora no `Player.bin` e o valor gravado é a altura **menos 100**.

**O dado atual:** `clube.carta_jogo.corpo` · **A régua:** `clube.molde_corpo` (384/384 batendo)

---

# 2 · PÉ — `clube_novo.pe`

Três campos, 11 linhas. `Player.bin` nos três.

| campo | bit | valores | bônus |
|---|---:|---|---|
| pé dominante | 654 · w1 | Right / Left | — |
| pé ruim · frequência | 478 · w2 | Almost Never · Rarely · Occasionally · Regularly | 0 · 0,35 · 0,70 · **1,00** |
| pé ruim · precisão | 578 · w2 | Low · Medium · High · Very High | 0 · 0,40 · 0,75 · **1,00** |
| teto (régua nossa) | — | — | **1,00** |

**A conta:** `frequência × precisão × teto`. Máximo 1,00 ponto.

⚠️ Os 9 pesos também estão em `clube.bonus_parametro`, de onde o motor lê hoje.
Na troca, o motor passa a ler `clube_novo.pe.valor_bonus` e aquelas 9 linhas saem.

---

# 3 · ESTILO DE JOGO — `clube_novo.playstyle`

**36 estilos.**

| pacote | Playstyle.bin | o que é |
|---|---|---|
| `dt200` (Steam) | 872 bytes | o catálogo — 36 registros de 168 bytes |
| `dt870` (Steam) | **não existe** | — |
| `dt870` (`ST\Download`) | 135 bytes | só a flag de lançado |

**A atualização sobrepõe:** o byte 1 é a flag. O `dt870` **ligou dois** que estavam
desligados no `dt200`: `PS_COVERING` e `PS_SWEEPER_GK`.

```
Playstyle.bin · common\etc\pesdb\ · 168 bytes por registro
  offset 0 ..... id_jogo (u16)      offset 1 ..... flag de lançado
  offset 4 ..... nome japonês       offset 104 ... o código PS_XXX
```

⚠️ **Os dois slots gravam em escalas diferentes.** Slot 1 (bit 372) guarda
`indice × 4`; slot 2 (bit 440) guarda o `indice` cru. Quem lê tem que converter.

**32 lançados · 4 não lançados:** `PS_PRESS_BACK`, `PS_HARD_MARKER`,
`PS_DEEP_LINE_DEFENDER`, `PS_BUILD_UP_GK` — exatamente os 4 que não aparecem em
nenhuma das 42.803 cartas. A flag bate 100% com o dado real.

**Slot:** 22 só ofensivos · 10 só defensivos · **3 nos dois**
(`PS_ATTK_PREVENTER`, `PS_LIBERO_GK`, `PS_CLASSICAL_GK`) · e o `NONE`.

---

# 4 · ESTILO DE IA — `clube_novo.estilo_ia`

São **7**, e o jogo os guarda diferente de tudo: **não existe arquivo de catálogo**.
Varri os 12 CPK — o único `.bin` com código textual é o `Playstyle.bin`. O
`eFootball-WESYS-Unzlib-Tool.exe` também não tem (abri o módulo `wesys`: só as duas
chaves de descriptografia). E o extrator tem os 7 nomes ingleses **digitados à mão**.

| bit | id_texto | Português | cartas |
|---:|---:|---|---:|
| 614 | 15 | Perito em cruzamento antecipado | 5.233 |
| 616 | 11 | Malandro | 5.351 |
| 647 | 19 | Perito em chute de fora da área | 10.004 |
| 649 | 18 | Corrida com gás | 7.820 |
| 674 | 76 | Rápido como uma bala | 7.989 |
| 678 | 77 | Perito em bola longa | 8.321 |
| 680 | 13 | Drible veloz | 9.521 |

⚠️ **Falta casar id ↔ bit.** São duas numerações diferentes da Konami. A prova está
montada: 7 cartas, cada uma com **um único** estilo ligado — Juninho Capixaba (614),
Frank Zambo Anguissa (616), Harry Kane (647), Robert Lewandowski (649),
Luke Shaw (674), William Saliba (678), Conor Gallagher (680).

---

# 5 · POSIÇÃO — `clube_novo.posicao_jogo`

**13 posições.** A chave é o valor gravado no bit 556 (w4).

| id | EN | PT | id_texto sigla | id_texto nome | bit aptidão | cartas |
|---:|---|---|---:|---:|---:|---:|
| 0 | GK | GO · Goleiro | 1 | 0 | — | 4.467 |
| 1 | CB | ZC · Zagueiro central | 7 | 6 | 584 | 7.043 |
| 2 | LB | LE · Lateral esquerdo | 13 | 66 | 318 | 2.752 |
| 3 | RB | LD · Lateral direito | 15 | 67 | 592 | 3.013 |
| 4 | DMF | VOL · Volante | 19 | 18 | 594 | 3.373 |
| 5 | CMF | MLG · Meia de ligação | 21 | 20 | 510 | 4.901 |
| 6 | LMF | MLE · Meia esquerda | 25 | 64 | 588 | 1.184 |
| 7 | RMF | MLD · Meia direita | 27 | 65 | 576 | 1.266 |
| 8 | AMF | MAT · Meia atacante | 29 | 28 | 580 | 3.162 |
| 9 | LWF | PTE · Ponta esquerda | 37 | 62 | 590 | 2.609 |
| 10 | RWF | PTD · Ponta direita | 39 | 63 | 596 | 2.358 |
| 11 | SS | SA · Segundo atacante | 50 | 49 | 598 | 573 |
| 12 | CF | CA · Centroavante | 33 | 32 | 586 | 6.102 |

**A ordem 0–12 está provada no dado:** os 959 cards com estilo de goleiro estão
**todos** em `id=0`; os 5.461 com estilo de lateral, em `id=2` e `id=3`.

---

# 6 · ATRIBUTO — `clube_novo.atributo_jogo`

**26 atributos.** O jogo não cataloga atributo com id — a identidade estável é o
endereço, então a chave é `PB:<bit>:6`.

Os nomes vêm da lista oficial `Any3T`, ids 483 a 508.

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

**A ligação com o extrator é pelo bit, e fecha 26 de 26.** Nome nenhum entra nessa
conta: o extrator lê o bit 492, a tabela tem `PB:492:6`, e pronto.

---

# 7 · HABILIDADE — `clube_novo.habilidade_jogo`

**72 habilidades.** `PlayerSkill.bin`, `skill_id` u32 no offset 0, japonês no offset 4,
registro de 104 bytes. **dt200 e dt870 são idênticos** — a atualização não mexe aqui.

**24 campos.** Os que importam além dos nomes:

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

**Habilidade dá percentual, nunca ponto — provado.** Weerathep Pomphan, cap 1, sem
ímpeto: isolei o técnico (multiplicador 1,034 uniforme nos 24 atributos sem
habilidade). Sobrou atributo 4 com +13 e atributo 5 com +12.

| | atributo 4 | atributo 5 |
|---|---|---|
| a régua | 10 + 5 + 2,5 = 17,5% | 10 + 5 = 15% |
| se percentual | ceil(72 × 17,5%) = **13** | ceil(74 × 15%) = **12** |
| se ponto | 18 | 15 |
| **o motor gravou** | **13** ✅ | **12** ✅ |

Confirma também a regra da **perdedora valendo metade**.

**O `flat` existiu numa só:** Força de vontade dava `+8` direto em Finalização e Força
do chute. Você trocou por percentual em 05/08 por ela ser condicional. A linha no
`equacao.py` que soma `flat` é o resto desse desenho — hoje soma zero sempre.

**As 9 que travam:** só têm japonês, sem efeito e **sem bit** — o extrator não as
enxerga. `シャープカット` · `ビーストドライブ` · `コントロールカーブ` ·
`ラピッドトリガーフィニッシュ` · `バックスピンロブ` · `ディサイシブパス` ·
`GKラッシュアウト` · `GKエアリアルクレイム` · `パワータックル`.

---

# 8 · ÍMPETO — `clube_novo.impeto_jogo`

**Estado auditado em 27/08/2026: 440 linhas**, união dos códigos publicados: 195
aparecem no DT200, 102 no DT870 Steam original e 408 no DT870 da atualização,
com sobreposição. As 440 continuam com `pode_rodar=false`.

```
PlayerBooster.bin · 40 bytes por registro atual
  bit 112, w10 ... codigo_jogo
  bit 212, w3 .... nível físico
  campos de efeito ... deltas de 5 bits por atributo
```

**Contrato canônico corrigido:** `codigo_jogo` representa a variação inteira
publicada pela Konami. A carta não separa o código em “família + grau”. `Duelo +3`,
por exemplo, é um código completo cuja receita fica em
`impeto_atributo_jogo`. Família visual pode existir apenas na apresentação.

Foram reconciliadas fisicamente **350 receitas**, totalizando **1.542 relações**
ímpeto × atributo, com deltas de 1 a 6 e zero divergência contra o dicionário.
Há endereço individual comprovado para 23 atributos. Os campos de goleiro nos
bits 192, 197 e 256 são distintos, mas aparecem sempre juntos e com o mesmo delta;
a permutação entre as três chaves canônicas continua bloqueada.

Condição é separada de nome: 131 códigos conhecidos não têm condição física e
219 têm marcador de condição. A semântica e os parâmetros dos 219 ainda não
foram decodificados. A carga preparada aceita **488 relações incondicionais e não
ambíguas** e mantém **1.054 bloqueadas**, sem inferir condição por nome.

Na carta, os dois slots de `Player.bin` usam **10 bits**:

```
slot condicional ... bit 288, largura 10
slot principal ..... bit 308, largura 10
0 = sem ímpeto · 136 = vaga
```

A leitura anterior de 8 bits perde 270 atribuições acima de 255; uma vira
falsamente `0` e duas viram `136`. Corrigir carta/Extrator pertence à frente das
relações de carta, não a esta carga de catálogo.

**Estado de aplicação:** nenhuma migração de ímpetos foi aplicada enquanto o
PostgreSQL estava sem espaço e em recuperação. Preflight, migração parcial e
rollback estão em `4-DOCUMENTOS/IMPETOS-NORMALIZADOS`; só a parte comprovada pode
ser promovida depois de `preflight_ok=true`.

**Sem japonês:** `PlayerBooster.bin` não guarda texto, somente números.

⚠️ **`da_vaga` não apurado.** A vaga usada pela carta vem de `vaga_s1`/`vaga_s2`,
não de uma família inventada no catálogo.

---

# 9 · TÉCNICO — `clube_novo.tecnico_jogo`

**Criada e vazia.** As 1.472 linhas estão em `4-DOCUMENTOS/CATALOGO-TECNICOS.csv`,
para importar pelo Table Editor.

```
Coach.bin · 176 bytes por registro
  offset 0 ..... id (u32) — a chave da Konami
  offset 32 .... nome japonês
  offset 78 .... nome latino
  offset 124 ... nome chinês
```

**A atualização sobrepõe:** dt200 tem 982, dt870 tem **1.472** — 490 novos, nenhum
removido, nenhum nome alterado. É o único catálogo que traz **três idiomas de uma vez**.

---

# ⚠️ AS TABELAS VELHAS — a lista da troca

Nada aqui foi apagado. Quando o manual fechar, a gente troca cada chamada.

**Onde o motor casa por texto hoje:**

| catálogo | onde | vai virar |
|---|---|---|
| habilidade | `POR_NOME` (equacao.py 208), `TEM_EFEITO`, `VETADAS`, `_EF` | `skill_id` |
| estilo | `casa.get(dono)` / `liga.get(outro)` (motor_bonus.py 197-199) | `id_jogo` |
| posição | `if p in ('GK','GO','Goleiro')` — três grafias numa condição só | `id` 0–12 |
| atributo | o efeito aponta para a **posição** 0–25 | `codigo` |
| **técnico** | já casa por id | ✅ certo |

**Assunto 1 — corpo.** Já apagadas em 27/08: `insumo_bonus_corpo`, `cards_efhub`,
`carta_velha_2608`, as colunas `corpo` de `carta`/`carta_posicao_comprada`/`cards_base`,
`cards.medidas`, as views `faltas_agora` e `o_que_o_efhub_trouxe`, e 10 linhas de
`campo_fonte`. Ainda existe: `public.bonus.corpo_soma`/`corpo_pct`.

**Assunto 2 — pé.** `clube.carta` (40.954) · `public.cards_base` (6.469) ·
`carta_posicao_comprada` (3.684) · `public.cards` (2.568) · `jogo_ficha` (0).

**Assunto 3 — estilo.** `estilo_jogo` (23) · `estilo` (33, por texto) ·
`estilo_defensivo` · `estilo_defensivo_ref` (13) · `estilo_jogo_traducao` ·
`estilo_valor` (144) · `estilo_regra` (90, por nome PT) · `sa_familia` ·
`regra_posicao_estilo` · `posicao_slot` (13).

**Assunto 7 — habilidade.** `clube.habilidade` (74) · `public.insumo_habilidade` (65) ·
`habilidade_incidencia` (1.139) · `bloqueio` (246) · `pool_de_habilidades` ·
`habilidade_rara_valor` (330).

⚠️ **`habilidade_rara_valor` — órfã e não explicada.** 17 habilidades × 30 funções,
valores de 0 a 64,4. **Nenhum motor a lê.** Não é a incidência: onde as duas tabelas
falam da mesma habilidade na mesma função, divergem (Finalizador nato no Falso nove:
60,1 contra 16,8). Significado não provado.

**Assunto 8 — ímpeto.** `clube.impeto` (486) · `impeto_efeito` · `impeto_fabricavel`
(com o número grudado no nome) · `public.impeto` · `insumo_impeto` ·
`insumo_impeto_catalogo` · `impeto_atributo` · `impeto_orfao` · `impeto_degrau`.

---

*Próximo: fechar o técnico e mapear cada leitura antiga X para a tabela nova Y;
somente uma migração futura e própria poderá redirecionar o motor.*
