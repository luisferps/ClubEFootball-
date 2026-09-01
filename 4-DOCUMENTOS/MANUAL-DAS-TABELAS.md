# MANUAL DAS TABELAS — ClubEFootball

**Aberto em 27/08/2026; atualizado em 28/08/2026.** Diz, assunto por assunto, **qual é a tabela oficial**.

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
Nas estruturas que expõem gate operacional, `pode_rodar` e `falta_o_que`
registram essa diferença. A view legada `clube.insumo_incompleto` continua em
`clube`; ela não transforma automaticamente o modelo novo em consumidor ativo.

---

## ESTADO DE HOJE

Fotografia final conferida em 28/08/2026 no banco e nos relatórios de fechamento.
Estrutura carregada não significa consumidor ligado.

| bloco | fotografia comprovada | pronto para leitura | bloqueio ou limite |
|---|---|---|---|
| Textos | `texto_do_jogo`: **11.679** chaves oficiais | dicionário integral, procedência integral, 166 referências resolvidas, zero sem texto e 8 FKs validadas | nenhuma pendência da frente Textos |
| Cartas | `carta_jogo`: **43.072** cartas | chave `card_id` e campos físicos disponíveis em `clube_novo` | não autoriza motor/UI a abandonar o legado |
| Relações normalizadas | atributos **1.119.872**; corpo **516.864**; habilidades **179.189**; IA **54.435**; posições **516.864**; slots de ímpeto **3.748** | zero duplicidade e zero órfão nas cargas fechadas | medidas de cabeça 12–14 continuam fora da relação corporal da carta |
| Dimensões | 214 nacionalidades; 1.072 clubes; 75 ligas; 11 tipos | 43.072 nacionalidades e tipos, 32.151 clubes e 30.157 ligas vinculados | 354 cartas ficam `pode_rodar_vinculos=false`; tipos 4/0 e 7/0 têm rótulos provisórios |
| Ímpetos | 440 códigos; 2.072 efeitos; 407 condições; 696 faixas; 35 membros de liga | estrutura e integração cumulativa do Extrator validadas; duas reexecuções read-only aprovadas | **0 condições liberadas**; consumidor desligado e três cartas sem clube físico fail-closed |
| Técnicos | 1.594 identidades; 1.478 atuais aptas; 116 históricas bloqueadas | Extrator integrado; nacionalidade compartilhada com cartas | históricos ausentes do DT870 atual não rodam |
| Catálogos-base | atributo 26; corpo 15; pé 11; posição 13; playstyle 36; IA 7; habilidade 72 | todos os catálogos existem por chave física/canônica | 9 habilidades continuam sem efeito/bit e não podem rodar |

A cópia legada `clube.carta_jogo` permanece com 42.803 linhas. Nenhum número acima
autoriza escrita no legado nem redirecionamento de motor, UI ou rotina.

Em 28/08/2026, `clube_novo.texto_do_jogo` foi carregada integralmente a partir de
`all.str`: 11.679 linhas, 11.679 chaves (`secao`,`id_texto`), zero duplicidade,
11.679 procedências confirmadas, 166 referências de catálogo resolvidas, zero
referência sem texto e oito FKs compostas validadas. Fingerprint do readback:
`56a205221af16addfe96f8452baffa8a`.

## MODELO NOVO — SCHEMA `clube_novo`

Esta é a fronteira oficial e fisicamente materializada do modelo novo. O schema
`clube_novo` nasceu com 21 tabelas e contém agora **42 tabelas** após as migrações
canônicas de Técnicos, Textos, tipos/condições de Ímpetos e Dimensões das Cartas.
A view derivada de principal/gêmeas não conta como tabela; índices, sequências,
gatilhos e funções auxiliares também não são tabelas adicionais.

**Status em 27/08/2026: cópia paralela aplicada.** A migração
`20260827183648_criar_clube_novo_copia_paralela_21_tabelas` criou e carregou
`clube_novo` sem mover, renomear, apagar ou alterar as fontes em `clube`.
Naquele checkpoint, as 21 cópias tinham as mesmas contagens e fingerprints das
fontes. As ampliações posteriores foram aplicadas somente em `clube_novo` e não
transformam o legado em espelho atual. Nenhum motor, rotina, view ou tela foi
redirecionado por esta documentação.

O schema novo continua privado: a conferência de 28/08/2026 mostrou que `anon`,
`authenticated`, `authenticator` e `service_role` não têm `USAGE` nem grants de
tabela em `clube_novo`. Na fotografia atual, 15 tabelas têm RLS habilitado e 27
não têm; isso não autoriza exposição pela Data API enquanto o schema continuar
sem `USAGE` e sem grants. RLS/policies não foram alteradas nesta documentação.

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
| catálogo | `tipo_impeto_jogo` | tipos físicos, comportamento de ativação e estado do rótulo oficial | `codigo_raw` | destino da FK `impeto_jogo.tipo_condicao_raw` |
| procedência | `tipo_impeto_evidencia_jogo` | âncoras reproduzíveis carta→ímpeto→tipo, com registro/bit/largura | (`codigo_raw`, `ordem`) | FKs para tipo e ímpeto |
| regra | `impeto_condicao_jogo` | uma condição canônica por código atual de ímpeto | `codigo_impeto` | FKs para `impeto_jogo` e `tipo_impeto_jogo` |
| alvo | `impeto_condicao_nacionalidade_jogo` | alvo físico de nacionalidade/região | `codigo_impeto` | FK para `impeto_condicao_jogo`; o código-alvo ainda não tem FK de dimensão |
| alvo | `impeto_condicao_liga_jogo` | alvo-base físico de liga/categoria | `codigo_impeto` | FK para `impeto_condicao_jogo` |
| alvo | `impeto_condicao_liga_membro_jogo` | membros físicos expandidos de cada condição de liga | (`codigo_impeto`, `codigo_liga_membro`) | FKs para condição de liga e, em ambos os códigos de liga, para `liga_jogo` |
| alvo | `impeto_condicao_clube_jogo` | forma física de equipe/clube, reservada sem linha fictícia | (`codigo_impeto`, `ordem`) | FK para `impeto_condicao_jogo`; tabela atual vazia |
| regra | `impeto_condicao_outro_jogo` | seletor físico genérico preservado para as condições de classe | `codigo_impeto` | FK para `impeto_condicao_jogo` |
| regra | `impeto_condicao_classe_jogo` | comparação classe do dono × classe candidata e regra de contagem | `codigo_impeto` | FK para `impeto_condicao_outro_jogo` |
| catálogo | `impeto_classe_candidato_jogo` | classe física candidata de cada código de ímpeto | `codigo_impeto` | FK para `impeto_jogo` |
| parâmetro | `impeto_condicao_parametro_faixa_jogo` | corte e efeito máximo que originam as faixas | `codigo_impeto` | FK para `impeto_condicao_jogo` |
| relação | `impeto_condicao_faixa_jogo` | intervalos ordenados de quantidade e delta | (`codigo_impeto`, `ordem`) | FK para `impeto_condicao_jogo` |
| procedência | `categoria_time_clube_jogo` | inventário físico categoria→clube de `CategoryTeamList.bin` | (`codigo_categoria`, `codigo_clube`) | sem FK na fotografia atual; não substitui a liga unitária da carta |
| catálogo | `tecnico_jogo` | identidade e procedência dos técnicos pelo id físico do jogo | `id` (`bigint`) | origem das relações canônicas de técnico |
| catálogo | `nacionalidade_jogo` | 214 códigos, nomes pt-BR e siglas extraídos de `Country.bin` | `codigo_jogo` | destino das FKs independentes de carta e técnico |
| catálogo | `clube_jogo` | 1.072 códigos de clube e sua procedência em `Team.bin` | `codigo_jogo` | destino da FK `carta_jogo.codigo_clube` |
| catálogo | `liga_jogo` | 75 códigos de liga/competição e vínculos físicos | `codigo_jogo` | FK opcional autorreferente `codigo_pai`; destino da carta e dos membros de liga |
| catálogo | `tipo_carta_jogo` | 11 estados técnicos de tipo, rótulo exibível e qualidade da associação nominal | `tipo_carta_id` | FK composta opcional para `texto_do_jogo`; destino das FKs de tipo da carta |
| catálogo | `afinidade_tecnico_jogo` | códigos físicos 0–7 de afinidade; rótulo somente quando comprovado | `codigo_jogo` | destino da FK de afinidade de `tecnico_jogo` |
| catálogo | `estilo_jogo_tecnico` | catálogo vivo dos estilos de equipe do técnico, separado do playstyle da carta | `codigo` | destino de `tecnico_estilo_jogo` |
| relação | `tecnico_estilo_jogo` | técnico × estilo de equipe, com proficiência 0–99 e procedência física | (`tecnico_id`, `codigo_estilo`) | FKs para técnico e estilo de técnico |
| relação | `tecnico_atributo_jogo` | até dois boosts normalizados por técnico: atributo, ordem e delta | (`tecnico_id`, `ordem`) | FKs para técnico e `atributo_jogo`; par técnico×atributo único |
| carta | `carta_jogo` | cadastro principal das 43.072 cartas pelo id original da Konami | `card_id` | origem das seis relações normalizadas de carta |
| carta | `carta_atributo_jogo` | carta × atributo, com o valor do atributo | (`card_id`, `codigo_atributo`) | FKs para `carta_jogo` e `atributo_jogo` |
| carta | `carta_corpo_jogo` | carta × medida corporal, com o valor | (`card_id`, `codigo_corpo`) | FKs para `carta_jogo` e `corpo_ordem` |
| carta | `carta_habilidade_jogo` | carta × habilidade, com a ordem quando informada | (`card_id`, `skill_id`) | FKs para `carta_jogo` e `habilidade_jogo` |
| carta | `carta_estilo_ia_jogo` | carta × bit de estilo de IA | (`card_id`, `bit_estilo_ia`) | FKs para `carta_jogo` e `estilo_ia` |
| carta | `carta_posicao_jogo` | carta × posição, com nível de aptidão | (`card_id`, `posicao_id`) | FKs para `carta_jogo` e `posicao_jogo` |
| carta | `carta_impeto_jogo` | os dois slots de ímpeto da carta; vaga é estado do slot e `condicional` é cópia derivada | (`card_id`, `slot`) | FKs para `carta_jogo` e `impeto_jogo` |
| catálogo | `impeto_atributo_jogo` | relação ímpeto × atributo publicada no arquivo | (`codigo_impeto`, `codigo_atributo`) | FKs para `impeto_jogo` e `atributo_jogo` |
| sistema | `funcao_sistema` | catálogo canônico das 19 funções internas | `id` | alvo de `funcao_alias`; id protegido por trigger |
| sistema | `funcao_alias` | aliases comprovados dos nomes legados | `id` | FK `id_funcao` para `funcao_sistema`; alias normalizado único |
| procedência | `mapa_do_jogo` | inventário de arquivo, chave, endereço e estado de apuração | (`assunto`, `arquivo`) | registros técnicos de procedência; não é consumidor |

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
as seis relações de carta, as dimensões e as relações estruturais de ímpeto ficam
integralmente em `clube_novo`, sem FKs cruzadas com tabelas do schema legado.
As seis relações de carta estão carregadas; catálogo existente ou relação carregada
não é, por si só, autorização para ligar um consumidor.

A view `clube.insumo_incompleto` permanece em `clube`, consultável e sem
redirecionamento. As rotinas legadas identificadas com nomes textuais qualificados
continuam lendo as fontes antigas de propósito, até o futuro mapeamento leitura
antiga X → tabela nova Y.

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

**Estado aplicado em 28/08/2026:** o dicionário central contém as 11.679 entradas
oficiais do `all.str`. O CPK usado tem SHA-256
`2419045a081a151f8a0cdcc70a9ca0c4ca1ca265b8467b9c182623baa05338db` e o
`all.str` descompactado tem SHA-256
`306741adab8376ed64620b618ae9721d316ae548b126419730b9bd5ff5f525a9`.
Os catálogos apontam por chave oficial composta; nenhum nome duplicado é usado como
identidade. Oito FKs foram validadas após provar zero referência órfã.

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

Há **7 bits atualmente observados nas relações de cartas**. `bit` é a chave
estável do domínio, e a tabela continua sendo o catálogo de apresentação e a
FK de `carta_estilo_ia_jogo`; ela não é a autoridade de localização física.

As colunas históricas `arquivo` e `endereco` registram a anotação
`Player.bin`/`bit N · largura 1`, mas não substituem o contrato: não têm
`arquivo_id`, papel de fonte, versão/hash, layout de registro, procedência
física tipada ou prova por item. Os textos (`secao_texto`, `id_texto`, nomes e
descrições) são somente apresentação. Eles nunca podem associar um texto a um
bit por semelhança de nome.

| bit | id_texto | Português | cartas |
|---:|---:|---|---:|
| 614 | 15 | Perito em cruzamento antecipado | 5.233 |
| 616 | 11 | Malandro | 5.351 |
| 647 | 19 | Perito em chute de fora da área | 10.004 |
| 649 | 18 | Corrida com gás | 7.820 |
| 674 | 76 | Rápido como uma bala | 7.989 |
| 678 | 77 | Perito em bola longa | 8.321 |
| 680 | 13 | Drible veloz | 9.521 |

Os sete endereços acima são lidos como **relações** no pedido tipado:
`contrato_leitura_campo` 214/212/210/213/215/216/211, cada um com
`Player.bin`, `bit_inicio` correspondente e largura 1, normalizado pela FK
`estilo_ia.bit`. A autoridade de arquivo, papel/fonte, SHA-256, versão,
tamanho de registro, leitor, tipo, bit/largura e prova está em
`contrato_leitura_arquivo`/`contrato_leitura_campo` e é exposta, sem cópia,
pela view read-only `catalogo_endereco_leitura_extrator_v1`.

### Cobertura do catálogo — 29/08/2026

Os sete bits provam presença/ausência de relações por carta; **não provam uma
enumeração completa do catálogo de estilos de IA**. Até a descoberta de uma
fonte física enumerável, o contrato declara
`clube_novo.estilo_ia` como `coverage_nao_verificavel` em
`contrato_leitura_catalogo_fisico` e na view derivada
`catalogo_cobertura_extrator_v1`: `artefato_fisico` e `papel_fonte` são nulos,
e a aprovação/aplicação das famílias `catalogos` e `relacoes` fica fail-closed.
Isto não impede as leituras independentes nem promove `Playstyle.bin`,
`all.str` ou um rótulo como fonte do catálogo.

Quando uma enumeração física for comprovada, endereço/arquivo/bit ou código,
largura, layout, versão, hash e procedência entram somente no contrato e em
sua view derivada. A alteração mínima adicional será um vínculo explícito e
versionado, com FK, de `campo_id` para `estilo_ia.bit`; ele transportará apenas
a chave estável, sem duplicar endereço ou estado de domínio no catálogo. A
saída seguirá envelope selado → revisão/aceite V5 → aplicação transacional.

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

**Estado estrutural concluído em 28/08/2026; consumidor desligado.** O catálogo
tem 440 códigos: 407 receitas físicas presentes na biblioteca atual e 33 códigos
históricos/ausentes. As 440 linhas de `impeto_jogo` continuam com
`pode_rodar=false`.

```
PlayerBooster.bin · 40 bytes por registro atual
  bit 112, w10 ... codigo_jogo
  bit 207, w5 .... corte bruto da faixa
  bit 212, w5 .... efeito máximo
  bit 299, w3 .... classe candidata
  bit 302, w3 .... classe do ímpeto dono
  bit 296, w3 .... tipo físico do ímpeto
  bit 64, w32 .... espelho do tipo físico
  bit 96, w16 .... alvo de nacionalidade/região ou liga/categoria
  bit 32, w18 .... alvo de equipe/clube, zero nos registros atuais
```

**Contrato canônico corrigido:** `codigo_jogo` representa a variação inteira
publicada pela Konami. A carta não separa o código em “família + grau”. `Duelo +3`,
por exemplo, é um código completo cuja receita fica em
`impeto_atributo_jogo`. Família visual pode existir apenas na apresentação.

`impeto_atributo_jogo` contém **2.072 relações** ímpeto × atributo, com delta,
ordem e procedência. Ela permanece a única receita dos efeitos; tabelas de tipo,
condição e faixa não duplicam atributos nem deltas.

`tipo_impeto_jogo` contém os cinco valores físicos reais (`raw0`, `raw1`, `raw2`,
`raw3`, `raw5`) e `tipo_impeto_evidencia_jogo` contém 9 âncoras. `raw4` não é
tipo: o código 136 é a sentinela `vaga_de_slot`. O relatório de procedência registra
`raw3 → Especial` como convenção autorizada de apresentação; o rótulo, sozinho,
não deve ser usado como se fosse prova física da ligação.

`impeto_jogo.tipo_condicao_raw` agora é FK para `tipo_impeto_jogo`. Os 407
registros cujo tipo é coletável no layout atual estão tipados; 33 registros sem
tipo permanecem `NULL` de forma rastreável. Nenhum desses 33 tem receita ou está
em slot. O booleano `condicional` de `impeto_jogo` e de `carta_impeto_jogo` é
derivado por trigger do tipo, nunca fonte canônica.

Na carta, os dois slots de `Player.bin` usam **10 bits**:

```
slot 2 ............. bit 288, largura 10
slot 1 ............. bit 308, largura 10
0 = sem ímpeto · 136 = vaga
```

A leitura anterior de 8 bits perdia 270 atribuições acima de 255. A fotografia
física e a carga canônica já usam 10 bits. A integração cumulativa de Ímpetos no
Extrator foi concluída e o arquivo oficial contém **2.072 efeitos**, exatamente os
2.072 de `clube_novo.impeto_atributo_jogo`: `missing=0`, `extra=0` e zero delta
divergente. Duas reexecuções somente leitura foram aprovadas e o checklist foi
atualizado. Isso comprova a integração do Extrator; não liga o consumidor ou motor.

`carta_impeto_jogo` tem 3.748 linhas: 2.381 slots preenchidos e 1.367 vagas.
As condições foram materializadas sem liberar consumo:

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

As 407 condições se dividem em 145 sempre ativas, 30 de avaliação ao vivo, 203
de nacionalidade/região, 19 de liga/categoria e 10 de classe. O consumidor não
pode somar faixas: escolhe no máximo o intervalo que contém a quantidade e deve
falhar fechado quando faltar uma dimensão exigida.

**Regra física das duas ligas do Neymar:** o alvo-base 149, lido no
`PlayerBooster.bin`, é expandido pelo `CompetitionUnit.bin` para `[588,149]`.
Isso corresponde a `2.ª Divisão Brasileira` e `Brasileirão Betano`. A lista é
física e reproduzível; não foi inferida pelo país nem pela semelhança dos nomes.

**Três cartas permanecem fail-closed por falta de clube físico:** Minamino Harumi
`105686528843807` (clube 1278), Esteban Andrada `106724568638035` (1778) e Juan
Brunetta `106724568710537` (1779). Os códigos não têm definição em `Team.bin` nos
três CPKs auditados; nenhum clube ou liga foi inventado.

Os testes somente leitura reproduzem as faixas de Messi/Argentina, Neymar/duas
ligas, classe 122 e sempre ativo. Isso prova a estrutura e os casos de aceitação;
não prova que motor, UI ou qualquer outro consumidor estejam prontos. Todas as
407 condições continuam com `pode_rodar=false`.

**Sem japonês:** `PlayerBooster.bin` não guarda texto, somente números.

**Vaga não é tipo:** `raw4`/código 136 é sentinela do slot e não possui linha em
`tipo_impeto_jogo`.

---

# 9 · TÉCNICO — `clube_novo.tecnico_jogo`

**Carga canônica aplicada e conferida em 27/08/2026, com Sobreposição fechada em
28/08/2026.** Não é mais um catálogo vazio nem uma importação manual pelo Table
Editor.

```
Coach.bin · 176 bytes por registro
  bit 0, largura 64 ... id (u64 little-endian) — a chave da Konami
  offset 32 .... nome japonês
  offset 78 .... nome latino
  offset 124 ... nome chinês

campos de apresentação
  idade .............. bit 231, largura 7; idade = valor físico + 14
  nacionalidade ...... bit 170, largura 8; resolve em Country.bin
  afinidade .......... bit 187, largura 3; zero = ausência legítima

proficiências (7 bits cada)
  possessionGame 206 · longBallCounter 238 · quickCounter 224
  longBall 199 · outWide 213
  overload/Sobreposição 135 — relação somente quando o valor físico for maior que zero

boosts (5 bits cada)
  slot 1 bit 160 · slot 2 bit 148
  zero = ausente · valor físico - 1 = atributo canônico · delta comprovado = +1
```

### Tabelas e contagens lidas de volta

| objeto | linhas | contrato |
|---|---:|---|
| `tecnico_jogo` | 1.594 | união de identidades: DT200, DT870 original e DT870 atualizado |
| técnicos com carga atual completa | 1.478 | `pode_rodar=true`, fonte autoritativa DT870 atualizado |
| identidades históricas | 116 | preservadas, bloqueadas por não existir registro no DT870 atualizado |
| técnicos atuais com idade/nacionalidade/afinidade | 1.478 | todos resolvidos pela fonte física atual; zero órfãos |
| `nacionalidade_jogo` | 214 | 214 códigos, nomes pt-BR e siglas únicos; 100 códigos usados por técnicos atuais |
| `afinidade_tecnico_jogo` | 8 | códigos 0–7; código 0 é ausência legítima; somente código 5 possui rótulo comprovado |
| `estilo_jogo_tecnico` | 6 | os seis estilos têm catálogo, texto e endereço físico comprovados; todos `pode_rodar=true` |
| `tecnico_estilo_jogo` | 7.391 | 7.390 relações dos cinco estilos históricos + Sobreposição 96 de Antônio Conte; PK e FKs conferidas |
| `tecnico_atributo_jogo` | 104 | atributo, ordem 1/2 e `delta=1`; PK/FKs e unicidade conferidas |

`clube_novo.tecnico_estilo_principal_jogo` é uma view: escolhe a maior proficiência;
em empate usa a ordem do catálogo como principal e mantém as demais como gêmeas. Há
82 técnicos com empate máximo e 124 relações gêmeas. Não se somam as proficiências.

### Amostra física e readback

Fabio Capello (`17601312850052`) foi relido com `46/89/57/89/64` na ordem dos cinco
estilos acima. O principal é `longBallCounter`, `longBall` é gêmeo, e os boosts são
`Finalização +1` (ordem 1) e `Talento defensivo +1` (ordem 2). Nos campos de
apresentação, o mesmo registro físico resulta em idade 44, nacionalidade 215
(`Itália`/`ITA`) e afinidade 5 (`Jogadores de AT`; rótulo de tela comprovado:
`Atacantes`).

Antônio Conte (`17609097478250`, registro 1.476) foi relido com os cinco valores
históricos `68/73/90/68/89` e **Sobreposição 96**. A view deriva `overload` como
principal, máxima 96 e sem gêmea. O mesmo campo vale zero nos outros 1.477 registros;
por isso nenhuma relação de Sobreposição é criada para eles. Fabio Capello, usado
como controle negativo, permaneceu sem essa relação.

### Rastreabilidade dos campos de apresentação

| campo | fonte física | registro/endereço | transformação e presença |
|---|---|---|---|
| idade | DT870 atualizado → `Coach.bin` | registro de 176 bytes identificado pelo ID u64; bit 231, largura 7 | `idade = valor físico + 14`; presente nos 1.478 registros atuais |
| nacionalidade do técnico | DT870 atualizado → `Coach.bin` | mesmo registro; bit 170, largura 8 | código com FK para `nacionalidade_jogo`; 1.478/1.478 resolvidos |
| afinidade | DT870 atualizado → `Coach.bin` | mesmo registro; bit 187, largura 3 | código 0 significa ausência legítima; 1.478/1.478 códigos válidos |
| código da nacionalidade | `Country.bin` | registro de 1.488 bytes; bit 10, largura 9 | 214 códigos únicos; arquivo byte-idêntico em DT200, DT870 original e DT870 atualizado |
| nome pt-BR | `Country.bin` | offset 788, largura máxima 70 bytes | UTF-8 terminado por NUL; 214 nomes válidos |
| sigla | `Country.bin` | offset 708, largura máxima 10 bytes | ASCII/UTF-8 terminado por NUL; 214 siglas válidas |
| rótulo da afinidade 5 | `dt261_bra` → `all.str` | seção `Any1W`, `id_texto=495` | texto oficial `Jogadores de AT`; demais códigos continuam sem rótulo por falta de vínculo físico comprovado |

Cada linha atual de `tecnico_jogo` guarda ainda a função da fonte
(`dt870_updated`), CPK, arquivo, índice do registro, hash do `Coach.bin`, versão do
contrato e carimbo de carga. `nacionalidade_jogo` guarda também tamanhos, offsets,
codificação, hash de `Country.bin` e presença nas três versões auditadas. Os sete
itens acima estão materializados em `clube_novo.mapa_do_jogo`; Sobreposição acrescenta
o assunto `tecnico.estilo.sobreposicao`, com bit 135, largura 7, hash e amostras. A
extração pode ser repetida quando o arquivo do jogo mudar, sem depender dos valores
atuais.

### Proveniência e limites

Identidade, relação de proficiência e relação de boost guardam fonte, CPK, arquivo,
registro, bit/largura e hash de `Coach.bin` quando a unidade física foi provada. A
migração foi transacional, idempotente e possui rollback no pacote
`RESULTADOS-E-VALIDACOES/2026-08-28/TECNICOS-CAMPOS-E-AFINIDADE` do Extrator. A
reexecução real preservou os fingerprints semânticos de técnicos, nacionalidades,
afinidades e as 7.390 relações históricas; o readback final registrou 7.391 relações
de estilo, 104 relações de boost e zero órfãos. A extensão de Sobreposição tem migração
e rollback próprios no pacote permanente `sobreposicao-v1`.

**Sobreposição/Overload está comprovada.** No `Coach.bin` atual, o campo começa no bit
135 e ocupa 7 bits. A distribuição integral dos 1.478 registros é `0 × 1.477` e
`96 × 1`; o único valor não zero pertence a Antônio Conte. O texto oficial é
`Any10T:793 = Sobreposição`, e o texto explicativo `Any7T:255` confirma que ela é o
sexto estilo de jogo do time. Não foi criada tabela ou coluna nova: o catálogo
existente foi promovido e a associação foi inserida em `tecnico_estilo_jogo`.

Link-up foi adiado por decisão de produto para uma frente futura separada e **não
bloqueia mais a família Técnicos**. Nenhuma relação de Link-up foi inventada nem
carregada nesta conclusão.

O Extrator cumulativo está integrado para Técnicos. `tecnico_jogo` e `carta_jogo`
usam FKs independentes para a mesma `nacionalidade_jogo.codigo_jogo`; não existe
catálogo duplicado de nacionalidade para cada família.

---

# 10 · RELAÇÕES NORMALIZADAS DAS CARTAS

As seis relações estão carregadas em `clube_novo` e apontam por FK para
`carta_jogo` e para seu catálogo canônico. A cardinalidade é a do dado físico,
não uma lista de nomes deduzida.

| relação | PK | cardinalidade comprovada | procedência e limite |
|---|---|---|---|
| `carta_atributo_jogo` | (`card_id`,`codigo_atributo`) | 26 por carta; 1.119.872 linhas | 26 valores de `Player.bin`; diferença simétrica zero |
| `carta_corpo_jogo` | (`card_id`,`codigo_corpo`) | 12 por carta; 516.864 linhas | altura + 11 medidas; cabeça 12–14 não está no JSON físico atual |
| `carta_habilidade_jogo` | (`card_id`,`skill_id`) | uma por habilidade presente; 179.189 linhas em 33.521 cartas | `skill_id` oficial; `ordem` é zero-based |
| `carta_estilo_ia_jogo` | (`card_id`,`bit_estilo_ia`) | uma por bit presente; 54.435 linhas em 24.854 cartas | chave pelo bit físico, não pelo nome |
| `carta_posicao_jogo` | (`card_id`,`posicao_id`) | 12 aptidões por carta; 516.864 linhas | nível 0–2; GO é a posição principal e não uma 13.ª aptidão gravada |
| `carta_impeto_jogo` | (`card_id`,`slot`) | até dois slots; 3.748 linhas | 2.381 preenchidos e 1.367 vagas; código físico de 10 bits |

As cinco primeiras relações têm zero duplicidade, zero órfão e comparação exata
contra os campos-fonte de `carta_jogo`. A sexta foi carregada e validada pela frente
Ímpetos. O Extrator cumulativo instalado preserva os blocos de Técnicos e Textos e
compara as cinco relações em modo somente leitura; nenhum desses comparadores grava
automaticamente no banco.

### Limite operacional de `estilo_ia`

`carta_estilo_ia_jogo` usa exclusivamente a chave estável
(`card_id`,`bit_estilo_ia`) e a procedência do campo em `Player.bin`. Os bits
atualmente lidos são uma projeção **observada nas cartas e monitorada**, não uma
enumeração integral do catálogo `clube_novo.estilo_ia`. Se o Extrator receber um
membro físico ativo fora dessa projeção, ele registra alerta com card, bit,
registro/arquivo/hash e mantém a aplicação dessa relação bloqueada. Ele não cria
linha de catálogo, não converte nomes em bits e não infere rótulo; a descoberta
integral permanece cobertura não verificável até existir fonte física enumerável.

---

# 11 · DIMENSÕES UNITÁRIAS DAS CARTAS

Cada carta tem no máximo uma nacionalidade, um clube, uma liga e um tipo. Por isso,
essas quatro dimensões são colunas com FK em `carta_jogo`, não novas tabelas de
cruzamento carta×dimensão. As relações multivaloradas necessárias já estão nas
tabelas normalizadas descritas neste manual.

| dimensão | PK do catálogo | vínculos em `carta_jogo` | cardinalidade/ausência legítima |
|---|---|---:|---|
| `nacionalidade_jogo` | `codigo_jogo` | 43.072 | exatamente uma por carta; catálogo compartilhado com Técnicos |
| `clube_jogo` | `codigo_jogo` | 32.151 | zero ou um; 10.921 cartas sem código físico de clube |
| `liga_jogo` | `codigo_jogo` | 30.157 | zero ou uma; 12.915 sem entrada física de competição |
| `tipo_carta_jogo` | `tipo_carta_id` | 43.072 | exatamente uma chave técnica por carta |

As FKs canônicas são `carta_jogo.codigo_nacionalidade`, `codigo_clube`,
`codigo_liga` e `tipo_carta_id`. Tipo também possui as FKs de texto/consistência
que impedem associar uma chave oficial ao estado técnico errado. Todas foram
validadas com zero órfão.

## Convenções e provisórios de tipo de carta

- `player_type_4_subtype_0` exibe **Desconhecido 1** em 313 cartas.
- `player_type_7_subtype_0` exibe **Desconhecido 2** em 43 cartas.
- Nos dois casos, `nome_pt_br` e `chave_texto` permanecem `NULL` e o status é
  `provisorio_sem_prova_nominal`. Esses rótulos não são nomes oficiais do jogo.
- `PlayerDeleteList → Jogador indisponível` é uma classificação operacional
  separada, usada em 7.598 cartas. Não é sinônimo de 4/0 nem de 7/0.
- Os oito tipos jogáveis nomeados têm dicionário oficial e âncora de tela, mas a
  qualidade da ponte física estado→chave continua registrada no próprio catálogo;
  nomes não substituem essa procedência.

O Extrator cumulativo relê `Player.bin`, `PlayerDeleteList.bin`, `Country.bin`,
`Team.bin`, `CompetitionEntry.bin`, `CompetitionUnit.bin` e as chaves necessárias
de `all.str`. A validação instalada é somente leitura e terminou sem diferenças.
Para vínculos, 42.718 cartas estão liberadas e 354 ficam fail-closed por clube sem
definição física; três dessas 354 têm slot de ímpeto preenchido e estão nomeadas na
seção de Ímpetos.

---

# 12 · LEITURA, EXTRATOR E CONSUMIDORES

| família | banco | Extrator cumulativo | consumidor |
|---|---|---|---|
| Textos | completo e pronto para leitura canônica | integrado; compara/prepara pacote sem escrita automática | leitores podem usar a chave oficial; UI não foi redirecionada por esta etapa |
| Relações das cartas | seis relações carregadas e com FKs | cinco relações integradas em comparação read-only; slots pertencem à frente Ímpetos | dados disponíveis para leitura; motor/UI continuam sem migração automática |
| Dimensões | quatro vínculos unitários aplicados | integrado e validado em modo read-only | respeitar `pode_rodar_vinculos`; 354 cartas falham fechado |
| Técnicos | catálogo e relações canônicas carregados | integrado; compartilha nacionalidades | 1.478 atuais aptos; 116 históricos bloqueados |
| Ímpetos | receita, condições, alvos, membros, classes e faixas estruturados | integrado cumulativamente; 2.072 efeitos exatos, duas reexecuções read-only aprovadas e checklist atualizado | **não pode rodar**; 0/407 condições aptas e três cartas sem clube físico fail-closed |

Este quadro é o gate operacional. Documentação de estrutura não liga consumidor,
não autoriza inferir dados ausentes e não substitui uma migração própria de leitura.

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

*Próximo: qualquer ativação de consumidor de Ímpetos deve ter migração própria e
comprovada. A integração cumulativa do Extrator e seu checklist estão concluídos,
mas nenhuma tabela deste manual redireciona ou liga o motor por existir.*

## Contrato tipado do Extrator — 29/08/2026

`clube_novo` passou a manter a camada versionada de descoberta do Extrator:
`contrato_leitura_familia`, `contrato_leitura_fonte_localizador` e
`contrato_leitura_expectativa`, além da semântica de saída em
`contrato_leitura_arquivo` e `contrato_leitura_campo`. Cada campo declara família,
tipo esperado, normalizador/versionamento, identidade estável, FK de destino,
nulidade e serialização; cada arquivo declara leitor/versionamento e cada fonte é
localizada pelo template versionado no banco. A função
`clube_novo.obter_pedido_leitura_tipado_ativo()` é somente leitura e entrega esse
pedido ao Extrator.

Identidade de logística é exclusivamente `card_id`, id físico, código de catálogo
ou FK declarada. Nome, rótulo, ordem e posição visual não unem nem sobrescrevem
registros. Um envelope carrega `bruto`, `normalizado`, tipo, identidade/FK e
procedência; rótulos derivados são apenas `apresentacao` para a interface. A carga
produtiva continua desligada: snapshots e comparações são por família e selados por
fonte, contrato e payload; qualquer aplicação futura exigirá lote, validação de FK,
unicidade e readback no próprio `clube_novo`.

## Matriz física R2 do Extrator — 29/08/2026 (em validação)

O contrato declara `dt200` (Steam), `dt870_original` (Steam) e
`dt870_updated` (atualização Konami), cada qual com localizador e SHA-256 do
CPK. `dt261_bra` é fonte textual separada e só aparece quando `textos` a
solicita. A precedência é dado de comparação, nunca fallback:
`dt870_updated`, `dt870_original`, `dt200`.

Cada família também declara `catalogos_requeridos`; o executor só consulta
esses catálogos e os já referidos pelos campos. Condições, efeitos e vínculos
de liga de Ímpetos, portanto, não podem voltar a depender de lista local.

## Fluxo de sincronização do Extrator — 29/08/2026

`clube_novo` é a única autoridade do pedido: informa o que buscar, onde e
como decodificar, o tipo, normalizador, identidade e FK. O Extrator sempre lê
integralmente o universo físico solicitado, normaliza por chave canônica e
devolve o resultado selado ao fluxo de `clube_novo`. Não existe aprovação
manual de carga, política de contagem ou decisão externa sobre quais registros
buscar.

O resultado classifica novo, removido, alterado, repetido e inválido por chave
e procedência; essa classificação é diagnóstico para investigação de mudança e
nunca impede a leitura seguinte. O worker atual não aplica dados de jogo; sua
trava de escrita protege exclusivamente contra destino/schema indevido e não
transforma o resultado em uma carga manual separada.

### Retificação: aprovação no próprio Extrator

O pacote de revisão selado é apresentado na UI do Extrator. O usuário aprova
ali; o contrato registra esse aceite e somente então a aplicação ao
`clube_novo` pode ser habilitada. A aprovação não muda o pedido nem reduz a
varredura física.

### Cardinalidade é observação, não limite

O contrato de `clube_novo` especifica como localizar e decodificar uma família,
mas não limita sua cardinalidade. Cada leitura percorre todos os registros do
arquivo físico atual. Contagens/snapshots registrados servem somente para
comparação posterior por chave canônica e procedência, e uma diferença vai para
diagnóstico — nunca reduz o universo lido.

## Cobertura de catálogos e projeção de Cartas — 29/08/2026

As novas tabelas de metadados operacionais são
`clube_novo.contrato_leitura_catalogo_fisico` e
`clube_novo.contrato_leitura_projecao_cartas`. A primeira vincula cada catálogo
requisitado à sua chave física ou a uma dependência normalizada declarada; a
segunda vincula cada `chave_campo` de Carta a artefato físico, coluna, tipo e
coluna de destino de `clube_novo.carta_jogo`. Ambas se ligam por
`contrato_id`, não armazenam dados do jogo e só são expostas pelo pedido ativo.

`carta_jogo.jogador_indisponivel` é o destino correto do campo booleano
`carta.tipo.indisponivel.id`; `tipo_carta_jogo.tipo_carta_id` continua sendo
catálogo, não destino de escrita desse booleano. `card_id` é a única identidade
da projeção. Rótulos como nome exibido, caixa e nacionalidade textual são de
apresentação e não são usados para união, comparação de FK ou futura carga.

## Auditoria de aplicação interna do Extrator — 29/08/2026

`clube_novo.aplicacao_pacote_revisao_extrator` é a auditoria exclusiva de uma
aplicação aprovada pelo Extrator. Ela vincula `idempotency_key`, a execução
estagiada, `contrato_id`, SHA-256 do pacote, selo de contrato, manifesto de
fontes, cobertura e auditoria por família. A chave única
`(contrato_id, pacote_sha256)` impede que outro pacote seja associado ao mesmo
aceite. A linha é criada e relida na mesma transação da aplicação; qualquer
divergência provoca rollback.

Ela não recebe rótulos humanos nem altera tabela de domínio por si só. Um
aplicador só pode gravar dados quando o pacote trouxer envelopes tipados por
família com as chaves/FKs previstas no contrato; relatório de comparação sem
esses envelopes é recusado antes da escrita. O ambiente de desenvolvimento usa
o mesmo estágio e readback sob rollback, portanto não promove dado físico real.
## Catálogo único de endereços do Extrator — 29/08/2026

`clube_novo.catalogo_endereco_leitura_extrator_v1` é a **view read-only** que
o Extrator consulta para descobrir campos físicos. Ela é derivada diretamente
das linhas canônicas do contrato, famílias, arquivos e localizadores já
existentes: não é tabela-espelho, não tem trigger de sincronização, não contém
estado próprio e não duplica dado de domínio.

Cada linha preserva `familia_id` e `campo_id` originais, além de fonte/papel,
arquivo, caminho físico, versão, precedência, endereço, largura/tipo,
catálogo/FK, normalizador e procedência. Um mesmo campo aparece para cada
papel físico declarado pela família; a identidade continua sendo a FK do campo,
nunca nome ou posição. A coluna `papel_fonte_arquivo_canonico` conserva a fonte
do arquivo do campo quando ela difere do papel que torna a fonte disponível.

Na validação do contrato ativo, a view retornou 602 localizações para 214
campos canônicos, cobrindo os papéis `dt200`, `dt261_bra`, `dt870_original` e
`dt870_updated`. `obter_pedido_leitura_tipado_sem_revisao_v1()` deriva dela as
projeções `catalogo_enderecos`, `arquivos`, `localizadores_fontes` e `campos`;
portanto o código não pode escolher endereço, precedência ou fonte fora da
view. O rollback estrutural é
`4-DOCUMENTOS/EXTRATOR/SQL/ROLLBACK-CATALOGO-ENDERECOS-VIEW-V1.sql`.

## Escritores declarativos por família — 29/08/2026

`contrato_leitura_escritor_dominio` e
`contrato_leitura_escritor_destino` registram, no `clube_novo`, a serialização
autorizada de envelopes normalizados. O worker não escolhe uma tabela nem uma
chave por condição local: recebe `escritor_id`, destinos, chaves, colunas de
escrita, tipos e exigência de procedência do pedido. As sete famílias cobertas
somam 29 destinos (Cartas 1, Catálogos 2, Dimensões 3, Ímpetos 11, Relações 7,
Técnicos 4 e Textos 1).

O envelope usa exclusivamente identidade/FKs canônicas e procedência; rótulos
seguem como projeção de apresentação. A ausência de escritor ou destino no
pedido falha fechada. A migração e rollback são
`APLICAR-ENVELOPES-ESCRITORES-DECLARATIVOS-V1.sql` e
`ROLLBACK-ENVELOPES-ESCRITORES-DECLARATIVOS-V1.sql`.
## Fronteira de destino do Extrator — 29/08/2026

Há três camadas que não se confundem. A view
`catalogo_endereco_leitura_extrator_v1` é somente índice de descoberta: suas
tabelas-origem de endereço, versão e procedência nunca recebem valores físicos
extraídos. A execução produz envelope selado para estágio/revisão; a V5 exibe
o pacote e grava uma decisão vinculada a hash. Somente após o aceite válido o
aplicador transacional pode escrever os destinos canônicos de domínio do
`clube_novo`, declarados em `contrato_leitura_escritor_destino`.

O aplicador não possui destino implícito: valida chaves/FKs e readback para
cada envelope, abre uma transação e registra a auditoria em
`aplicacao_pacote_revisao_extrator`. Catálogo de leitura, estágio/revisão e
domínio ficam deliberadamente separados. Dados legados e estruturas de mapa
nunca são alvo. Enquanto `PRODUCTIVE_WRITES_LOCKED=true`, inclusive os
destinos canônicos continuam fechados.

## Views públicas por tela do front-end — 01/09/2026

O navegador não monta mais um catálogo genérico nem junta tabelas do banco.
Cada superfície cadastral lê um único contrato `SELECT-only` em `public`,
derivado do cadastro atual de `clube_novo`:

| View | Consumidor | Grão e responsabilidade |
|---|---|---|
| `public.frontend_boxes_v1` | Boxes cadastradas | Uma linha por `card_id` com Box válida, posição, tipo, overall, total da Box e `rank_box_overall`. |
| `public.frontend_home_v1` | Home | No máximo três cards da Box destaque, já ordenados e contados pelo banco. |
| `public.frontend_busca_v1` | Busca global | Uma linha cadastral por card. `busca_documento` é o `tsvector` prefixável indexado; os playstyles do resultado são agregados por `LATERAL` somente depois do recorte. |
| `public.frontend_ficha_v1` | Ficha cadastral | Uma linha por `card_id`, com identidade, dados físicos e grupos JSON de atributos, posições, habilidades, IA, pés, playstyles e ímpetos. |
| `clube_novo.build_pontuacao_final_v1` | Projeção interna de Build final | Liga uma linha canônica à Build candidata e ao resultado do Bonificador, com IDs, selos, estado, motivo, elegibilidade, score final e proveniência. Não é exposta ao navegador. |
| `public.frontend_build_publicada_v1` | RPC de Build para Ranking/Elenco/Ficha | Leitura limitada e somente de Builds já publicadas e seladas. Retorna a pontuação final pronta; o front-end não soma parcelas nem acessa `clube_novo`. |

`frontend_busca_v1` pesquisa somente campos mantidos na própria
`carta_jogo` (`card_id`, nome, Box, posição, estilo e nacionalidade). Tipo,
posição principal e playstyles continuam no resultado, mas não entram no
documento indexado. Isso mantém a view sempre atual sem tabela-espelho nem
trigger. O índice é
`clube_novo.carta_jogo_frontend_busca_v1_fts_idx`.

`anon` e `authenticated` têm `SELECT` somente nessas quatro views e não têm
`USAGE` nem privilégios de tabela no schema bruto `clube_novo`. As views
pertencem a `clube_frontend_view_owner`, role sem login, herança, escrita ou
`BYPASSRLS`, com leitura limitada às tabelas cadastrais declaradas. Boxes,
Home e Ficha usam `security_barrier=true`. Busca usa a exceção explícita
`security_barrier=false`: ela não esconde linhas e precisa permitir que o
filtro FTS desça ao índice antes da agregação lateral.

O contrato canônico de pontuação final é `clube_novo.build_pontuacao_final_v1`.
Ele só declara elegibilidade depois de os dois motores concluírem a mesma versão da
carta com selos válidos, e a única porta para o navegador é a RPC
`public.frontend_build_publicada_v1`. Ela devolve exclusivamente linhas com
publicação explícita; candidatos e lotes de teste continuam fora. Ranking, Elenco e
Ficha devem consumir essa RPC e nunca somar localmente saídas do Otimizador e do
Bonificador. Enquanto a interface não trocar o contrato antigo por essa RPC, ela
continua corretamente bloqueada. As contagens observadas em validação são
diagnóstico, nunca cardinalidade contratual.

Migração e retorno estrutural:
`4-DOCUMENTOS/INTEGRACAO-DE-SISTEMAS/MIGRACAO-VIEWS-FRONTEND-POR-TELA-V1.sql`
e
`4-DOCUMENTOS/INTEGRACAO-DE-SISTEMAS/ROLLBACK-VIEWS-FRONTEND-POR-TELA-V1.sql`.
