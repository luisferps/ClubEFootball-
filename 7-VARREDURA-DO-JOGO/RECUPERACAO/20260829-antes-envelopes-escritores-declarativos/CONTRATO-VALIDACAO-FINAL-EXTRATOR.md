# Contrato de validação final do Extrator

Este documento é a lista fixa para a validação final. Não basta uma tarefa informar que atualizou o Extrator: depois que todas as frentes forem concluídas, o Extrator deverá ler novamente os arquivos atuais do jogo e cada item abaixo deverá ser conferido contra o banco `clube_novo`.

## Regra de aprovação

Cada item deve passar nestas três comparações:

1. o arquivo atual do jogo contém o dado;
2. o Extrator lê o mesmo dado a partir desse arquivo;
3. o banco recebe o mesmo dado na tabela e relação corretas, sem órfãos.

Falha em qualquer uma das três reabre a frente responsável. Nenhuma frente é aprovada por relatório ou por contagem isolada.

## Relações das cartas — encerrada, ainda entra na validação final

### Origem e contrato

- Fonte obrigatória: `DT870 atualizado`, arquivo `dt870_console_win.cpk`.
- Arquivos internos: `Player.bin` para atributos, habilidades, estilos de IA e aptidões de posição; `PlayerAppearance.bin` para as onze medidas corporais que, junto da altura de `Player.bin`, formam o corpo.
- Fotografia física aprovada: 43.072 `card_id` únicos; SHA-256 do CPK `44df868c2613d532292d87072c0863a907d6a5f0cc40f914d355e56d74edfcc5`.
- O Extrator deve resolver somente as chaves canônicas dos catálogos de `clube_novo`; nome físico não pode virar chave inventada.

### Relações e contagens esperadas

- `carta_atributo_jogo`: 1.119.872 linhas, 43.072 cartas, exatamente 26 atributos por carta. Origem: vetor `atributos` de `Player.bin`; ponte `atributo_jogo.idx_casa -> atributo_jogo.codigo`; valores entre 40 e 99.
- `carta_corpo_jogo`: 516.864 linhas, 43.072 cartas, exatamente 12 itens por carta. Origem: altura de `Player.bin` + 11 campos de `PlayerAppearance.bin`; ponte `corpo_ordem.pos -> corpo_ordem.codigo`.
- `carta_habilidade_jogo`: 179.189 linhas, 33.521 cartas, 65 chaves distintas. Origem: bits oficiais de habilidades em `Player.bin`; ponte `habilidade_jogo.nome_en -> habilidade_jogo.skill_id`; preservar `ordem` de 0 a 9.
- `carta_estilo_ia_jogo`: 54.435 linhas, 24.854 cartas, 7 chaves distintas. Origem: bits oficiais de estilos de IA em `Player.bin`; ponte `estilo_ia.nome_en -> estilo_ia.bit`.
- `carta_posicao_jogo`: 516.864 linhas, 43.072 cartas, exatamente 12 posições por carta. Origem: campos físicos de aptidão de dois bits em `Player.bin`; ponte `posicao_jogo.codigo_en -> posicao_jogo.id`; `nivel_aptidao` entre 0 e 2.

### Amostras obrigatórias

- `84` — Yamamoto Hideomi: perfil esparso, com 1 habilidade e 1 estilo de IA.
- `4522` — Cristiano Ronaldo: 10 habilidades, 5 estilos de IA e aptidões ofensivas.
- `7511` — Lionel Messi: 10 habilidades, 5 estilos de IA e múltiplas posições aptas.
- `60754` — Samuel Portugal: goleiro, 1 habilidade e nenhum estilo de IA; zero deve ser reconhecido como resultado válido, não ausência da fonte.
- `108959` — Declan Rice: 10 habilidades, 2 estilos de IA e aptidões de meio/defesa.

Para cada amostra, comparar o registro físico, a saída do Extrator e as cinco relações por `card_id` e chave canônica — não apenas o total da carta.

### Critérios de reprovação

- CPK, arquivo interno, endereço, largura física ou fingerprint diferente sem nova validação física.
- Contagem diferente de 43.072 cartas ou qualquer `card_id` duplicado na fotografia.
- Contagem de qualquer relação diferente da listada acima.
- Qualquer órfão de carta ou catálogo, chave sem resolução canônica, duplicidade de PK ou diferença simétrica entre fonte física e relação.
- Atributo fora de 40..99; aptidão fora de 0..2; quantidade por carta diferente de 26 atributos, 12 itens corporais ou 12 posições.
- Habilidade fora dos 10 slots, ordem repetida, estilo de IA não mapeado ou interpretação de zero como erro.
- Qualquer alteração em `carta_impeto_jogo`, Dimensões, schema `clube`, carta principal, motor ou interface durante esta validação.

## Técnicos — encerrada, ainda entra na validação final

- Cada versão de técnico deve manter seu identificador próprio.
- O Extrator deve reler: idade, nacionalidade, afinidade, estilos de jogo, proficiências e boosts.
- Sobreposição deve ser relida como estilo de jogo: a amostra obrigatória é Antônio Conte, com proficiência 96.
- A amostra de controle é Fabio Capello, sem Sobreposição.
- Link-up está fora deste escopo e não será cobrado nesta validação.

## Textos — encerrada, ainda entra na validação final

- O Extrator deve localizar o arquivo oficial de textos em português e reler as chaves oficiais de texto.
- A tabela central de textos deve receber os textos com a mesma chave do jogo.
- Catálogos que mostram nome, sigla ou descrição devem resolver os textos apenas pela tabela central, sem fallback para o legado.
- A leitura integral deve encontrar **11.679 textos** e **11.679 chaves oficiais únicas** (`secao`, `id_texto`), com zero duplicidade.
- As **11.679 linhas** devem conservar a procedência física integral: origem, arquivo, CPK, offsets, medidas físicas, fingerprints, presença na fonte e instante de extração conforme o contrato instalado.
- As **166 referências de catálogo** devem resolver pela chave oficial composta em `clube_novo.texto_do_jogo`.
- A validação deve encontrar **zero referência de catálogo sem texto**.
- As **oito FKs compostas** de texto devem existir e estar validadas: atributo, estilo de IA, habilidade, ímpeto, pé, playstyle, sigla de posição e nome de posição.
- A comparação automática da leitura atual do Extrator contra `clube_novo.texto_do_jogo` deve terminar com **zero novas, zero alteradas e zero ausentes** para a fonte vigente.

## Dimensões das cartas — encerrada, ainda entra na validação final

### Contrato físico e execução automática

- Contrato do núcleo: `clubef-card-dimensions-physical-v2`; contrato do banco: `clubef-card-dimensions-v2`.
- O fluxo automático de Metadados carrega as quatro fontes por papel, relê o conjunto integral e envia uma fotografia física ao endpoint read-only `/api/card-dimensions/validate`.
- Por carta, `Player.bin` do DT870 atualizado fornece `card_id`, índice do registro de 400 bytes, nacionalidade no bit 328/largura 10 com transformação `floor(raw/2)`, clube no offset 16/u32, tipo nos bits 44–47 do `card_id` e subtipo no bit 104/largura 1.
- `PlayerDeleteList.bin` fornece somente a associação operacional a `Jogador indisponível`, por `card_id` u64. Ela não é confundida com nenhum estado jogável.
- País usa o catálogo compartilhado `clube_novo.nacionalidade_jogo`; as FKs de cartas e técnicos devem continuar apontando para a mesma tabela.
- Clubes são a união comprovada de `Team.bin`, com prioridade DT870 atualizado > DT200 > DT870 original; códigos presentes apenas nas cartas permanecem em registros explícitos sem nome e com bloqueio factual.
- Liga resolve `Player.bin.codigo_clube -> CompetitionEntry.bin -> CompetitionUnit.bin`; os registros da liga têm 2.472 bytes.
- Rótulos oficiais de tipo resolvem somente pelas chaves comprovadas de `all.str`. `type=4/subtype=0` e `type=7/subtype=0` permanecem separados como `Desconhecido 1` e `Desconhecido 2`, com nome/chave oficial nulos.
- A qualidade da associação nominal é validada como dado: oito tipos nomeados devem ter `status_associacao=rotulo_dicionario_ancora_tela_sem_ponte_fisica`; `PlayerDeleteList`, `classificacao_operacional_usuario_sem_ponte_fisica`; e os dois desconhecidos, `provisorio_sem_prova_nominal`.
- A auditoria reversa não autoriza promoção por ordem: `GOAT` e `Brilhante` existem no dicionário, mas nenhuma chave legível, sequência estrutural ou campo por registro em DT200/DT870 os liga a 4/0 ou 7/0.

### Contagens e hashes de aceitação

- 43.072 cartas e 43.072 `card_id` únicos;
- 214 nacionalidades, 1.072 clubes, 75 ligas e 11 tipos;
- 43.072 nacionalidades, 32.151 clubes e 30.157 ligas vinculados;
- 7.598 cartas em `PlayerDeleteList`, 356 cartas nos dois tipos provisórios e 354 cartas bloqueadas somente por clube sem definição nominal;
- zero órfão e zero diferença de chave de tipo;
- SHA-256 normalizado fonte/banco: cartas `b85c8d31f9c74b72f8c6fbe1b1bcff0df367f72897188c8efe09883b51897e9e`; nacionalidades `aaaad42441b274e81055947e1d555d9f70b6742b4f7b84632b76f3248a74e275`; clubes `877b5023060d70196008aeb47e7bb94e2f9591d1d7471193a5766bef66eb9237`; ligas `ae995965638e2413c43770a17ad69112e00d38c053581f68e4dbfc1c04643353`; tipos `c1440eec096abf45140ab5f00aaa26edf8533e8dcf2a1c1ea85dc4d42f1d3016`.

### Amostra obrigatória

- Neymar Jr `106755438714272`: Brasil (`146`), Santos FC (`1254`), Brasileirão Betano (`149`), `player_type_6_subtype_1`, chave oficial `Any3W:422`, `Distinguido - Show Time`.

Aprovação exige a comparação integral, em transação READ ONLY, com hashes fonte/banco idênticos; contagem isolada não aprova esta frente.

## Ímpetos — encerrada; integração operacional aprovada

### Contrato obrigatório

- Núcleo: `clubef-impetos-physical-v1`; endpoint read-only: `/api/impetos/validate`.
- `PlayerBooster.bin`: registro de 40 bytes; código bit112/w10; tipo bit296/w3 e espelho bit64/w32.
- Efeitos: 26 campos comprovados, cada um com bit inicial próprio e largura 5; a releitura atual deve produzir 2.072 relações não zero para os 407 ímpetos reais do DT870 atualizado. Código 136/raw4 é vaga, não efeito.
- Condições: nacionalidade bit128/w9; liga/categoria bit96/w16; clube/equipe bit32/w18; classe candidata bit299/w3 comparada à classe do dono bit302/w3.
- Faixas: corte `bit207/w5 + 2`, nível máximo `bit212/w5`, fórmula `min(nível,max(1,floor(nível*n/corte)))`, agrupando quantidades consecutivas de mesmo delta.
- Liga cumulativa: `CompetitionUnit.bin`, registros de 2.472 bytes, vínculo anterior bit32/w16 e posterior bit48/w16, expansão pela rotina `0x144A52D40`.
- Slots: `Player.bin`, slot1 bit308/w10 e slot2 bit288/w10; zero é vaga e nunca tipo de ímpeto.
- País, clube, liga e classe são relações distintas; nenhum alvo pode ser inferido pelo nome.

### Checks de aprovação

- 440 códigos na união com procedência; 408 registros preferidos do DT870 atualizado, dos quais 407 são ímpetos e um é vaga raw4.
- 2.072 efeitos físicos e igualdade simétrica integral com `clube_novo.impeto_atributo_jogo` por `(codigo_impeto,codigo_atributo,delta)`.
- 407 condições, 696 faixas, 35 membros de liga e igualdade simétrica integral com as tabelas canônicas.
- 3.748 slots: 2.381 preenchidos e 1.367 vagas; nenhum slot preenchido sem receita.
- Messi507: Argentina e faixas 1–7/+1, 8–10/+2, 11–23/+3.
- Neymar170: alvo149 expandido fisicamente para `[588,149]` e faixas 1–13/+1, 14–19/+2, 20–23/+3.
- Consumidor deve permanecer com zero condições aptas durante esta validação.
- Toda comparação deve informar `transaction_read_only=true`, `database_write=false` e `preserved_schema=clube`.

### Readback definitivo de 28/08/2026

- A divergência inicial foi corrigida mediante carga das 52 receitas inteiras que haviam sido omitidas por não aparecerem nos slots atuais: 38×4 + 14×26 = 516 relações.
- Fonte física e banco: 2.072/2.072 efeitos; zero ausente, zero extra e zero delta divergente.
- Passaram também: 407 condições, 696 faixas, 35 membros de liga e 3.748 slots.
- Duas reexecuções read-only idênticas, SHA-256 `A309374CF4C94C8FD0B87D8ED31C9EFAFE52A0E3D9891B7A119934B2BFF21125`, retornaram `passed=true` e `result=aprovado`.
- Consumidor permanece deliberadamente desligado; encerramento da validação não é autorização para liberar motor.

## Execução final

Quando todas as cinco frentes estiverem concluídas, executar uma leitura nova do jogo e gerar um relatório único com, para cada frente:

- campos e relações exigidos;
- contagens esperadas e encontradas;
- amostras obrigatórias;
- diferenças encontradas;
- resultado: aprovado ou reabrir a frente.

O relatório final só será aprovado se não houver campo faltante, relação órfã, amostra divergente ou dado que o Extrator deixou de reler.

## Gate adicional: contrato tipado e chave canônica — 29/08/2026

Antes de uma nova aprovação, o pedido de leitura deve vir de
`clube_novo.obter_pedido_leitura_tipado_ativo()` e conter leitor/versionamento,
tipo de saída, normalizador, identidade/FK, nulidade, serialização e procedência
para toda família/campo solicitado. A comparação usa somente a chave estável do
contrato (código físico/FK/ID imutável); nome, rótulo e ordem são apresentação e
nunca são chave de diff ou escrita. O resultado deve apresentar envelopes com valor
bruto, normalizado, identidade, FK e arquivo/hash/registro/campo, além de snapshots
por família selados por fonte+contrato+payload. Falha de uma família deve ficar
explícita sem impedir a leitura das demais; nenhuma carga é autorizada por este gate.

## Revisão cumulativa final — 28/08/2026

- **Resultado: APROVADO para o Extrator, não para motor/UI de negócio/consumidor.** Duas execuções integrais e read-only produziram o mesmo SHA-256 cumulativo `fa58000199416844ed3a788b0f891d115487c0a0d88303fdc86af638c2b15c73`; todos os endpoints retornaram `transaction_read_only=true` e `database_write=false`.
- Técnicos: 1.478 atuais, 214 nacionalidades compartilhadas, 8 afinidades, 7.391 proficiências/Sobreposição, 104 boosts e zero órfão. Textos: 11.679/11.679 chaves, 166 referências resolvidas, 8 FKs validadas e zero nova/alterada/ausente.
- Relações: 1.119.872 atributos, 516.864 corpo, 179.189 habilidades, 54.435 estilos de IA e 516.864 posições, com zero diferença e hashes fonte/banco iguais. Dimensões: 43.072 cartas, 214 nacionalidades, 1.072 clubes, 75 ligas e 11 tipos; os dois tipos sem prova nominal continuaram provisórios.
- Ímpetos: 440 códigos, 2.072/2.072 efeitos, 407 condições, 696 faixas, 10 relações de classe, 35 membros de liga e 3.748 slots; endereços e hashes de registro conferidos. As 407 condições continuam bloqueadas para o consumidor (`pode_rodar=0`). A interface mostrou 270 diferenças apenas na projeção de slots de `carta_jogo`; são pendência de aplicação/consumidor e nada foi escrito.
- O EXE reiniciou o executor da própria pasta operacional (PID novo, comando apontando para `7-VARREDURA-DO-JOGO\executor\executor_local.py`); quatro fontes encontradas, operações prontas, `write_enabled=false`, adaptadores de Técnicos/Ímpetos desligados e schema `clube` preservado. Snapshot anterior: `RECUPERACAO\2026-08-28-ANTES-REVISAO-CUMULATIVA-FINAL`.
- Arquivos operacionais atualizados por necessidade: `Extrator-ClubEfootball.html`; `app\extrator-core.js`; `app\extrator-ui.js`; `executor\executor_local.py`; `executor\card_relations.py`; `executor\texto_do_jogo.py`; `executor\impetos.py`; novo `executor\tecnicos.py`; `RESULTADOS-E-VALIDACOES\TESTES\teste-tecnicos-fisicos.js`; novo `RESULTADOS-E-VALIDACOES\TESTES\teste-revisao-cumulativa-read-only.js`.
- Confirmados já compatíveis, sem alteração: `Extrator eFootball.exe`; `windows-app\ClubEfootballExtractorLauncher.cs`; `configuracao.exemplo.json`; `app\mapeamento-fisico.js`; `app\catalog-source-map.js`; `app\extrator.css`; `executor\card_dimensions.py`; `RESULTADOS-E-VALIDACOES\TESTES\teste-impetos-fisicos.js`; `DOCUMENTACAO\MANUAL-DO-EXTRATOR.md`.

## Correção final da projeção e readback de slots — 28/08/2026

- A pendência de 270 cartas registrada acima foi encerrada no Extrator, sem escrita no banco: 214 diferenças em `impeto_s1`, 56 em `impeto_s2_cond`, uma concomitante em cada campo de vaga; fingerprint diagnóstico `bac29621ce14b549b018842749cb8eba04cb25ee54ee0750cbae908f88a9168d`. A causa era a leitura dos quatro campos-resumo antigos de `carta_jogo`; a projeção e o pré-voo integral agora os derivam exclusivamente de `clube_novo.carta_impeto_jogo`.
- Prova final: 43.072 cartas, 3.748 slots (2.381 preenchidos, 1.367 vagas), 1.170 condicionais e 1.211 sempre ativos; zero duplicidade, órfão, estado contraditório, receita ausente ou diferença entre `Player.bin`, a projeção entregue e a relação normalizada. Duas reexecuções integrais read-only produziram o mesmo SHA-256 `366ddc34f78bd62bd7ccc9a5d6add94052e07648fc659b90285ed2d1c60cb28f`, com `database_write=false`.
- O endpoint read-only `/api/card-impetus/readback` entrega, para qualquer carta solicitada e para os slots 1 e 2, estado, código, ativação (`sempre_ativo`/`condicional`), efeitos, tipo, alvo(s), faixas, parâmetros, classe e proveniência. Amostras aprovadas: Messi `106781476920663`/Argentina 144; Neymar `106755438714272`/ligas 588 e 149; cinco tipos físicos 0/1/2/3/5; cinco classes funcionais; slot sempre ativo e vaga. Consumidor permanece desligado e `pode_rodar=0`.
- Arquivos adicionais atualizados: `executor\executor_local.py`, novo `executor\card_impetus.py` e `RESULTADOS-E-VALIDACOES\TESTES\teste-revisao-cumulativa-read-only.js`. Rollback recuperável: `7-VARREDURA-DO-JOGO\RECUPERACAO\2026-08-28-ANTES-CORRECAO-PROJECAO-SLOTS` (restaurar os três arquivos existentes e remover somente o novo `card_impetus.py`). Lançador, núcleo, HTML/JS/CSS, configurações, banco, jogo, legado, motor e UI visual foram confirmados sem alteração.

## Retificação independente dos slots w8 — 28/08/2026

- A seção anterior de projeção por `carta_impeto_jogo` foi reprovada: mascarava a fonte física. O leitor correto é `Player.bin` slot 1 `bit308/w8` e slot 2 `bit288/w8`; `w10` incorporava campos vizinhos e somava 256. Prova determinística: registro 33281, carta `56160992464525`, `w8=45` (não 301).
- O Extrator, a projeção e o readback agora partem exclusivamente da fotografia física w8; baseline e pré-voo não sobrepõem slots do banco. Duas reexecuções read-only idênticas: `35dc6baa30208dd1795560985c20de7a79111daac574f965ffee7bc562ea3606`, `database_write=false`; 43.072 cartas × 2 slots, 2.378 preenchidos, 1.369 vagas e 82.397 vazios, com zero diferença físico=Extrator=projeção.
- `clube_novo.carta_impeto_jogo` ficou explicitamente **divergente/reprovada**: 3.748 linhas contra 3.747 estados físicos e 272 diferenças de campo; foi somente comparada, sem escrita. Isso é bloqueio factual externo ao Extrator e impede declarar a relação/banco ou consumidor prontos. Motor e consumidor continuam desligados.
- Rollback: `7-VARREDURA-DO-JOGO\RECUPERACAO\2026-08-28-ANTES-CORRECAO-SLOTS-W8-INDEPENDENTE`; arquivos alterados: `app\extrator-core.js`, `executor\executor_local.py`, `executor\card_impetus.py` e `RESULTADOS-E-VALIDACOES\TESTES\teste-revisao-cumulativa-read-only.js`.

## Reconciliação canônica dos slots w10 — 28/08/2026

- A retificação w8 foi revertida cirurgicamente: o código completo de `Player.bin` é slot1 `bit308/w10` e slot2 `bit288/w10`, com correspondência direta em `PlayerBooster.bin bit112/w10`. Os dois bits superiores pertencem ao identificador; Ronwen `56160992464525` confirma `301`, enquanto Zlatan `89136140651034` confirma `45` para o mesmo baixo 45 e adjacente distinto.
- O Extrator mantém a fotografia física como origem, consulta o catálogo apenas para nome/efeitos/condições e compara — sem sobreposição — `carta_impeto_jogo`. Duas reexecuções read-only idênticas, SHA-256 `16ca403168cdfe87c0ad31be24dc0c7bc6a5a28bd86a07dd4232313ea71d8f77`: 43.072 cartas, 2.381 preenchidos, 1.367 vagas, 82.396 vazios e zero diferença físico=Extrator=projeção=relação.
- Consumidor e motor permanecem desligados (`pode_rodar=0`). Rollback recuperável desta restauração: `7-VARREDURA-DO-JOGO\RECUPERACAO\2026-08-28-ANTES-RESTAURACAO-SLOTS-W10-CANONICO`.

## Republicação canônica do baseline de slots w10 — 28/08/2026

- O endpoint `/api/card-baseline/current.csv` passou a projetar, somente em memória, os quatro campos-resumo de slots a partir de `clube_novo.carta_impeto_jogo`, relação previamente reconciliada de forma independente com `Player.bin` w10. A validação física continua a partir do CSV físico, sem usar essa projeção como origem ou fallback.
- A publicação corrigiu 270 cartas-resumo desatualizadas (272 campos: 214 `impeto_s1`, 56 `impeto_s2_cond` e uma vaga em cada campo). `carta_jogo` e qualquer tabela do banco permaneceram imutáveis. Ronwen `56160992464525` é publicado como código `301`, coerente com físico e catálogo.
- Prova: duas reexecuções integrais read-only idênticas, SHA-256 `16ca403168cdfe87c0ad31be24dc0c7bc6a5a28bd86a07dd4232313ea71d8f77`; 43.072 cartas, 2.381 slots preenchidos, 1.367 vagas, 82.396 vazios e zero diferença físico=Extrator=relação=baseline publicado. Os cabeçalhos do endpoint declaram a projeção canônica, zero diferença publicada e 270 cartões-resumo armazenados divergentes; `database_write=false`.
- Rollback recuperável: `7-VARREDURA-DO-JOGO\RECUPERACAO\2026-08-28-ANTES-PUBLICACAO-BASELINE-SLOTS-W10`, restaurando somente `executor\executor_local.py`, `executor\card_impetus.py` e `RESULTADOS-E-VALIDACOES\TESTES\teste-revisao-cumulativa-read-only.js`.

## Reabertura — contrato ativo de leitura pelo banco — 28/08/2026

- **Resultado: bloqueado por lacuna canônica, sem migração parcial.** A auditoria read-only encontrou 499 ocorrências materiais de arquivo/layout/offset/bit/largura no núcleo e executores, concentradas também no mapa JavaScript `app\mapeamento-fisico.js` (76.035 bytes). Elas ainda são a verdade operacional de leitura.
- O candidato canônico `clube_novo.mapa_do_jogo` possui 39 linhas e somente `assunto`, `cpk`, `arquivo`, `chave`, `endereco`, `registro`, `aberto`, `medido_em` e `observacao`: endereço e layout são texto livre. Não há versão reconhecida do jogo, fingerprint do mapa ou do arquivo, tipos/endianness, offset/bit/largura tipados, catálogo/FK, requisito, estado de estágio/carga, chave idempotente nem regra de aceitação transacional.
- Cobertura insuficiente: 3 referências com fonte “a achar”, 7 não verificadas e 5 sem endereço; entre elas há famílias usadas pelo Extrator. Não foi criado schema, alterado banco, nem mantido fallback numérico, pois isso inventaria contrato inexistente e violaria fail-closed.
- A negociação banco → pedido versionado → leitura física → resposta etiquetada → estágio/readback/transação idempotente permanece pendente de um contrato canônico completo para cada campo. Até então, motor e consumidor continuam desligados. O único ajuste desta auditoria foi corrigir o rótulo residual de proveniência do readback de slots para `Player.bin w10`; não mudou a leitura física.

## Construção do contrato ativo — fases 1 e 2 — 28/08/2026

- A reabertura anterior não é encerramento: foi criada a base versionada em `clube_novo`, sem tocar dados de jogo, tabelas legadas, motor, fórmulas ou UI. Relações novas: `contrato_leitura_jogo`, `contrato_leitura_arquivo`, `contrato_leitura_campo`, `contrato_leitura_requisito` e `execucao_leitura_contrato`.
- O gate `clube_novo.estagiar_execucao_leitura_contrato` é `SECURITY INVOKER`, idempotente e fail-closed: só aceita um contrato `ativo` com cobertura integral e versão/fingerprint de contrato e fontes exatamente iguais. Ensaio controlado com fingerprint divergente foi recusado antes de qualquer escrita porque o contrato ainda é `rascunho`.
- O rascunho `clubef-dt870-2026-r1` já contém quatro arquivos com SHA-256 físico e 18 campos comprovados tipados: Player.bin, Coach.bin, Country.bin e all.str; incluem cartões, slots de ímpeto w10, tipo, nacionalidade, playstyles, técnicos e textos. Ainda não há leitor runtime usando essa base nem fallback numérico.
- Cobertura pendente em investigação: 687 folhas numéricas estruturais no mapa JavaScript e 449 ocorrências relevantes fora de dependências no núcleo/executores. Cada uma será promovida como `comprovado`, classificada `nao_usado` e removida do runtime, ou seguirá investigação física. Rollback de fase: `RESULTADOS-E-VALIDACOES\2026-08-28\CONTRATO-LEITURA-ATIVO\SQL\ROLLBACK-20260828_contrato_leitura_ativo_fase1.sql`; snapshot de arquivos: `RECUPERACAO\2026-08-28-ANTES-CONTRATO-LEITURA-ATIVO`.

## Construção do contrato ativo — fase 3 em curso — 28/08/2026

- A etapa intermediária chegou a 168 campos físicos comprovados e tipados, em nove arquivos fingerprintados. As promoções posteriores de corpo, `PlayerSkill.bin`, `Playstyle.bin`, ficha escalar, Técnico completo e condições de Ímpeto elevaram o rascunho a **214 campos em 12 arquivos**: all.str, Coach, CompetitionEntry, CompetitionUnit, Country, Player, PlayerAppearance, PlayerBooster, PlayerDeleteList, PlayerSkill, Playstyle e Team. Cada fonte tem SHA-256, tamanho de registro e transformação por campo; não houve carga de cartas nem ativação de runtime.
- Cobertura promovida: 26 atributos, 65 habilidades, 7 estilos de IA, 13 leituras de posição/aptidão, slots de ímpeto w10, catálogo/tipo e 26 efeitos de ímpeto, além de dimensões de clube/liga e lista de indisponíveis. As fontes de Dimensões foram relidas diretamente dos CPKs nesta fase, confirmando 43.072 cartas, 214 países, 1.072 clubes, 75 ligas e 11 tipos.
- A primeira tentativa de promoção coletiva foi revertida pela própria transação ao detectar que códigos históricos de atributo contêm `:` e não são chaves técnicas válidas. A correção passou a usar `bit` físico como chave do contrato e mantém o código histórico em metadado. Nenhuma linha parcial foi aceita.

## Auditoria de cadeia satélite do contrato — 28/08/2026

| Elo percorrido | Encaminhamento atual comprovado | Estado perante o contrato ativo |
| --- | --- | --- |
| `Extrator eFootball.exe` → `windows-app\\ClubEfootballExtractorLauncher.cs` → `executor_local.py` | Inicia somente a pasta operacional, fixa a porta local e remove flags de escrita real. Não decodifica jogo. | Neutro; deverá apenas preservar a negociação iniciada pelo servidor, sem mapa próprio. |
| HTML → `mapeamento-fisico.js`/`catalog-source-map.js` → `extrator-core.js` | O HTML carrega ambos antes do núcleo; o núcleo lê `K`, `IMP`, `STYLE_CAT` e `DEF_CAT` diretamente. | **Não conforme ainda**: mapa estrutural local é verdade operacional paralela. |
| `extrator-ui.js` → núcleo → endpoints | A UI lê CPK localmente pelo núcleo e envia fotografias a `/api/*`; também consulta baseline, textos, dimensões, ímpetos e técnicos. | **Não conforme ainda**: a UI não recebe contrato/fingerprint antes de decodificar. |
| `executor_local.py` → leitores | Importa `texto_do_jogo`, `card_relations`, `card_dimensions`, `impetos`, `tecnicos` e `card_impetus`; expõe seus resultados em endpoints read-only. | **Não conforme ainda**: chama leitores sem `contrato_id`/fingerprint e o `/api/status` não os informa. |
| Leitores de relações/dimensões/textos/técnicos/ímpetos | Consultam relações normalizadas em `clube_novo`; preservam read-only, mas ainda carregam campos físicos e contratos de validação locais. | **Não conforme ainda**: deverão receber o mesmo pedido tipado do banco. |
| `card_impetus.py` → baseline/readback | A validação física é independente, porém as etiquetas `Player.bin bit308/w10` e `bit288/w10` ainda estão materializadas no módulo; baseline é projetado em memória. | **Não conforme ainda**: origem, etiquetas e projeção devem vir do contrato carregado. |
| Materializadores/baselines/pré-voo | `current_card_baseline`, textos, relações e preparação usam tabelas normalizadas diretamente; nenhuma saída porta versão/fingerprint do mapa. | **Não conforme ainda**: devem propagar o mesmo selo e rejeitar mismatch. |
| Validadores/testes | A cadeia cumulativa compara físico, relação e baseline; ainda invoca endpoints e leitores anteriores. | **Não conforme ainda**: será estendida para provar que toda saída usa o contrato. |
| Dependências `psycopg` vendorizadas | Somente biblioteca de transporte PostgreSQL, sem referência de jogo. | Compartilhada/neutra; fora do domínio de mapeamento. |

- Prova de status: `/api/status` retornou `write_enabled=false`, mas não retornou `contrato_id`, versão ou fingerprints; nenhuma saída pode ser declarada migrada antes de esse selo atravessar toda a matriz acima. A migração futura será única e em lote, com cache derivado e versionado, sem fallback numérico.

- A matriz passou a ser gate persistente do rascunho: `clube_novo.contrato_leitura_cadeia` registra 17 elos (14 pendentes de migração e 3 neutros, que não decodificam o jogo), e o gatilho `clube_novo.validar_ativacao_contrato_leitura()` recusou, em ensaio transacional, a tentativa de ativar o contrato enquanto esses 14 elos não estiverem conformes. A rejeição não escreveu carga nem alterou o rascunho (`estado=rascunho`, `cobertura_total=false`). O rollback da fase passa a remover também essa matriz e o gatilho correspondente.

- O mesmo gate agora exige que **todo campo ativo tenha `status_prova=comprovado`**. Os três endereços GO `PlayerBooster.bin` (bits 192, 197 e 256) continuam rastreados, porém foram classificados `provisorio`: o conjunto físico existe, mas a associação individual Talento/Defesa/Reflexos de GO ainda é só convenção de ordenação. Ensaio transacional de ativação com cobertura forçada foi recusado por esse motivo, sem escrita. Portanto, eles não podem ser levados ao leitor ativo até prova física individual; não serão mascarados por catálogo ou fallback.

- Foi criada a origem única `clube_novo.obter_pedido_leitura_contrato_ativo()`, `SECURITY INVOKER`. Ela só devolve versão, fingerprints, arquivos, layouts, campos, catálogos/FKs e requisitos depois de conferir contrato ativo, cobertura integral, prova individual e cadeia inteira conforme. No estado atual, a chamada read-only falha fechada com “contrato de leitura ativo e integral não encontrado”; nenhum executor recebeu ainda uma rota alternativa ou permissiva.

- **Correção de direção do usuário:** os três campos GO não são pendência física aberta. `bit192 → Talento de GO`, `bit197 → Defesa de GO` e `bit256 → Reflexos de GO` foram restabelecidos como `convencao_aprovada`, com a decisão rastreável nas três entradas correspondentes de `clube_novo.mapa_do_jogo` e no Manual das Tabelas. O contrato e o pedido versionado expõem explicitamente `status_base=convencao_aprovada`; eles não os apresentam como prova física individual. O gate aceita somente `comprovado` ou `convencao_aprovada`, e o ensaio de ativação continuou recusado apenas pelos 14 elos satélites pendentes.

- A borda do executor passou a expor `GET /api/reading-contract/current`, que chama exclusivamente `clube_novo.obter_pedido_leitura_contrato_ativo()` dentro de transação read-only e retorna o selo do plano junto de `database_write=false`. No rascunho, o endpoint e seu teste direto retornam conflito fail-closed; ele não monta mapa local nem habilita os leitores antigos. A troca dos demais elos para esse pedido continua pendente da migração conjunta.

## Migração da borda selada — 28/08/2026, em curso

- A borda HTTP da cópia operacional foi fechada contra o pedido canônico: todo `/api/*`, exceto a saúde e a própria consulta do contrato, obtém `clube_novo.obter_pedido_leitura_contrato_ativo()` em transação read-only antes de responder. Se o contrato estiver rascunho, incompleto, com fingerprint sentinela, campo sem base ou elo pendente, a rota devolve `409` e `database_write=false`; não há rota anterior em paralelo.
- Toda resposta dependente recebe os cabeçalhos `X-Clubef-Contract-Id`, versão e os dois fingerprints. Respostas JSON incluem o mesmo selo. A interface agora busca esse pedido antes de localizar fontes, confere os selos de resposta e anexa obrigatoriamente `leitura_contrato` a cada POST. O executor recusa corpo sem selo exatamente igual ao pedido ativo.
- A rota de slots, a projeção de baseline e o readback de Ímpetos passaram a resolver os endereços publicados a partir de `carta.impeto.slot1` e `carta.impeto.slot2` no pedido; as etiquetas não carregam mais `Player.bin bit...` fixo. A leitura física ainda não foi declarada migrada como um todo: núcleo, dimensões, textos, técnicos e demais leitores seguem na conversão conjunta.
- Como a autorização vigente exclui carga produtiva, `PRODUCTIVE_WRITES_LOCKED=true` bloqueia independentemente de configuração tanto cartão como texto e a rota `/api/apply`. O status não anuncia mais envio manual disponível. Esta trava é adicional ao gate de contrato e não é autorização futura de escrita.
- Verificações desta etapa: `executor_local.py` e `card_impetus.py` compilam; `extrator-ui.js` passou no parser Node. Em servidor isolado, com o contrato ainda rascunho, `GET /api/reading-contract/current`, `/api/card-baseline/current.csv` e `/api/sources/status` retornaram `409` com `database_write=false`. Nenhum dado do jogo foi carregado ou alterado.

### Registro objetivo de substituições nesta etapa

- `executor\card_impetus.py`: substitui as etiquetas fixas `Player.bin bit308/w10` e `Player.bin bit288/w10` pelos campos do pedido `carta.impeto.slot1` e `carta.impeto.slot2`, incluindo arquivo, bit e largura.
- `app\extrator-ui.js`: substitui a aceitação implícita das respostas da cadeia pelo selo retornado por `contrato_id`, `versao_jogo`, `versao_contrato`, `fingerprint_contrato_sha256` e `fingerprint_fontes_sha256` do pedido.
- `executor\executor_local.py`: substitui o encaminhamento sem versão dos endpoints e POSTs pela validação do mesmo conjunto de cinco campos de selo antes de qualquer readback, baseline, pré-voo ou validador.
- `app\leitura-contrato.js` e `app\extrator-core.js`: substituem a validação inicial fixa por papel de fonte pelos itens `arquivos` do pedido (`papel_fonte`, `arquivo`, `decodificador`, `tamanho_registro` e `sha256_arquivo`); a leitura dos slots usa `carta.id`, `carta.impeto.slot1` e `carta.impeto.slot2` diretamente do contrato.
- `app\extrator-core.js`: remove da decodificação de carta as leituras fixas de slots `readBits(..., 308, 10)` e `readBits(..., 288, 10)`; `extractCardsFromCpk` agora exige o pedido e só preenche os dois slots após `extractCardSlotsByContract` decodificar `carta.id`, `carta.impeto.slot1` e `carta.impeto.slot2` do contrato.
- Prova física read-only dessa substituição: o DT870 oficial foi aberto localmente com um pedido controlado montado apenas das três linhas tipadas do rascunho; `Player.bin` conferiu SHA-256 `2afe17a686bef320dce3c4096355ba99b56bfb8a42b08018f0ae2fe444b05853`, o decodificador retornou 43.075 registros físicos e a extração filtrada retornou 43.072 cartas válidas. Ronwen `56160992464525` resultou no código `301`, por `carta.impeto.slot1`; nenhuma tabela recebeu escrita.
- `executor\executor_local.py`: substitui os dicionários de tradução locais a serem consumidos pelo núcleo por `catalogo_schema`, `catalogo_tabela` e `catalogo_chave` já referidos nos campos do pedido; o executor devolve somente esses catálogos em leitura protegida e acrescenta `fingerprint_catalogos_sha256` ao selo. A migração dos consumidores desses catálogos permanece pendente.
- `app\extrator-core.js`: substitui `K.ABILITIES`/`K.ABIL_WIDTH` na leitura e serialização dos 26 atributos pelos 26 campos `carta.atributo.*`; a ordem vem de `atributo_jogo.idx_casa` no catálogo selado, e o valor base vem de `transformacao.base` de cada campo.
- `app\extrator-core.js`: substitui `K.SKILL_BITS`, `K.AI_PLAYING_STYLES` e `K.POSITION_APTITUDE_BITS` pelas famílias `carta.habilidade.*`, `carta.estilo_ia.*` e `carta.posicao.aptidao.*`; nomes e ordem vêm de `habilidade_jogo`, `estilo_ia` e `posicao_jogo` no catálogo selado.
- `app\extrator-core.js`: substitui `BODY_FIELDS` e a decodificação direta de `PlayerAppearance.bin` pelos campos `carta.corpo.card_id` e `carta.corpo.pos.1..11`; o pedido determina arquivo, registro, bits, ordem e fingerprint, e a altura continua sendo composta somente depois da leitura de `carta.corpo.altura` do mesmo contrato.
- Família de imagens: a fonte física foi identificada como contêiner Unreal da instalação (`pak/*.pak`, `.utoc`, `.ucas`), com caminhos virtuais `PesData/render/symbol/player` (minifaces) e `PesData/render/symbol/card` (artes/bordas). Não havia leitor de índice/asset instalado nem referência correspondente em `clube_novo.mapa_do_jogo`; por isso esta família permanece **fail-closed**, sem associação inferida de imagem a `card_id`, até haver prova do asset individual e da ponte canônica.
- Pré-condição ainda em construção para retirar o perfil escalar fixo: os campos físicos de altura, peso, idade, pé, posição, estilos, forma, lesão, nacionalidade e nome já estão tipados, mas o contrato precisa declarar também as semânticas antes guardadas no núcleo — normalização do playstyle primário, precedência da lesão e tradução canônica da nacionalidade. Elas serão promovidas como transformação/catálogo versionado; o núcleo não receberá fallback local.
- Retificação do rascunho (transação em `clube_novo`, sem carga): `carta.playstyle.primario` passou a declarar `floor(raw/4)*4`, `carta.playstyle.secundario` e `carta.forma` declaram `raw`, os dois bits de lesão declaram precedência versionada e `carta.nacionalidade.raw` declara a saída `codigo_jogo`. Rollback cirúrgico: restaurar os seis `transformacao` anteriores registrados no log desta execução; nenhuma carta ou dado produtivo foi escrito.

## Resultado normalizado do pedido — 29/08/2026

- Correção posterior de arquitetura: a política manual foi removida do pedido ativo pela migração `4-DOCUMENTOS/EXTRATOR/SQL/APLICAR-FLUXO-SINCRONIZACAO-CONTRATO-V1.sql`. O Extrator não mantém meta de quantidade, aceite/rejeição de divergência, promoção de baseline/snapshot nem caminho local de revisão; ele lê o pedido e devolve diagnóstico normalizado.
- Toda família devolve resultado normalizado e classificação por chave canônica/procedência (`novo`, `removido`, `alterado`, `repetido`, `inválido`). Dimensões, Textos, Técnicos, slots de Ímpeto e Relações não derivam decisão de contagem ou `passed`; a contagem é observação do conteúdo integralmente relido.
- A varredura nunca recebe teto do pedido: percorre integralmente cada arquivo/endereço solicitado, incluindo Cartas e relações, catálogos/dimensões, Textos, Técnicos e Ímpetos. Snapshot/expectativa anterior é exclusivamente comparador pós-leitura. Escrita produtiva segue bloqueada por `PRODUCTIVE_WRITES_LOCKED=true`; não houve alteração de cartas, dados do jogo, motor, fórmulas, UI visual ou legado.

## Normalização cumulativa de Cartas e Catálogos — 29/08/2026

- Snapshot prévio: `7-VARREDURA-DO-JOGO\artefatos\snapshots\catalogo-fisico-20260829-214900`; rollback limitado a `4-DOCUMENTOS\EXTRATOR\SQL\ROLLBACK-CATALOGO-FISICO-CONTRATO-V1.sql`.
- Mudanças de contrato: `contrato_leitura_catalogo_fisico` cobre os 23 catálogos solicitados (chave física direta ou dependência normalizada declarada) e `contrato_leitura_projecao_cartas` fornece 19 projeções físicas para `carta_jogo`. A definição de `carta.tipo.indisponivel.id` foi corrigida de `tipo_carta_jogo.tipo_carta_id` para `carta_jogo.jogador_indisponivel`.
- Substituição objetiva: `executor\desktop_worker.py` deixou de usar o diff de CSV de apresentação para validar Cartas; agora consome somente as projeções devolvidas pelo pedido e compara `card_id` + FKs/códigos físicos. `executor\executor_local.py` deixou de oferecer colunas fixas para essa validação e seleciona a união das colunas de destino declaradas pelo contrato. `box`, títulos e rótulos não entram na identidade.
- Prova: smoke V5 `preparacao-carga-integral-4-20260829-215407`, `database_write=false`, 43.072 Cartas físicas e 43.072 no alvo. Cartas e os 23 catálogos: zero novo/removido/alterado/repetido/inválido; Dimensões, Técnicos, Textos e slots de Ímpeto também sem delta técnico. Selo do resultado normalizado: `f3c1806b09625d9c9472640160098d6effc9dce393e68f3c4dadcb2d3f3c66f0`.
- Diagnóstico preservado: Relações registrou 147.724 itens `alterado`; catálogo de Ímpetos registrou 18 novos, 21 removidos e 143 alterados. Não são mascarados por contagem e não suspendem a próxima leitura. Integridade técnica ficou verdadeira (zero repetido/inválido); a escrita de dados segue indisponível neste worker por segurança de destino, sem depender de aprovação manual.

### Retificação urgente de fluxo

- A aprovação permanece obrigatória, mas é interna ao Extrator: leitura integral → pacote de revisão → aceite na UI do Extrator → aplicação autorizada ao `clube_novo`.
- `APLICAR-APROVACAO-INTERNA-EXTRATOR-V1.sql` restaurou `politica_revisao` no pedido ativo com estado `aguarda_aprovacao_no_extrator`. O gate não interfere na leitura nem na classificação; limita somente a aplicação.

## Aplicador interno transacional V5 — 29/08/2026

- Snapshot recuperável anterior: `7-VARREDURA-DO-JOGO\RECUPERACAO\20260829-antes-aplicador-transacional`. Mudanças limitadas a `executor\desktop_worker.py`, `windows-app\ClubEfootballExtractorLauncher.cs`, o executável recompilado, os manuais e as migrações `APLICAR-APLICADOR-TRANSACIONAL-EXTRATOR-V1.sql` / `ROLLBACK-APLICADOR-TRANSACIONAL-EXTRATOR-V1.sql`.
- Substituição objetiva: a UI V5 não termina mais no registro de aceite. Ela passa o pacote selado ao worker com `--apply-review`; este substitui qualquer aplicação implícita por pacote por verificação de SHA-256, selo atual de contrato/fontes/catálogos, fontes presentes, cobertura integral e decisão persistida vinculada ao mesmo hash. O código não aceita rótulo humano como identidade; auditoria e estágio usam contrato, `idempotency_key` e FKs canônicas.
- Banco: `clube_novo.aplicacao_pacote_revisao_extrator` foi criada vazia, com unicidade de pacote por contrato e FK para `execucao_leitura_contrato`. Ela é auditoria de transação, não tabela de dados do jogo. O rollback estrutural está documentado e não foi executado.
- Smoke integral read-only: `7-VARREDURA-DO-JOGO\artefatos\desktop\smoke-aplicador-controlado-20260829-221610` releu as quatro fontes declaradas e gerou o pacote SHA-256 `7f6ed397c672a1cf99417034f3c5b1d2f46e6ad18efa4ed03926270c66cec18f`; 43.072 cartas foram relidas. A aprovação vinculada, o estágio, a inserção de auditoria e seu readback ocorreram numa transação de teste e receberam rollback (`application_test_rolled_back`). Em seguida a política foi restaurada para `aguarda_aprovacao_no_extrator`; `aplicacao_pacote_revisao_extrator=0` e `execucao_leitura_contrato` não reteve linha desse pacote.
- Fail-closed comprovado: `pacote-adulterado-teste.json` foi recusado por hash divergente; `pacote-expirado-teste.json` foi recusado por selo contrato/fontes divergente. Ambos tiveram saída 1, `database_write=false`, e não alteraram a política nem criaram auditoria.
- Limite factual para uso produtivo: o pacote atual ainda é relatório de comparação; não contém envelopes normalizados aplicáveis de todas as famílias nem escritores de domínio registrados no contrato. Portanto `PRODUCTIVE_WRITES_LOCKED=true` continua e o aplicador recusa antes de tocar dados reais. O fluxo/gate está ligado; a aplicação produtiva só pode ser liberada depois de esses envelopes e escritores canônicos completos existirem e serem validados.
