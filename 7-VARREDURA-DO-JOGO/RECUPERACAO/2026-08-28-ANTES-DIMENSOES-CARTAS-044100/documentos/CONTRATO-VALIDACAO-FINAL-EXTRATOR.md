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
- SHA-256 normalizado fonte/banco: cartas `b85c8d31f9c74b72f8c6fbe1b1bcff0df367f72897188c8efe09883b51897e9e`; nacionalidades `aaaad42441b274e81055947e1d555d9f70b6742b4f7b84632b76f3248a74e275`; clubes `877b5023060d70196008aeb47e7bb94e2f9591d1d7471193a5766bef66eb9237`; ligas `ae995965638e2413c43770a17ad69112e00d38c053581f68e4dbfc1c04643353`; tipos `2bfe82639105e44b3665422b08a8348bb17805bcaee46d5ef365482e6f098160`.

### Amostra obrigatória

- Neymar Jr `106755438714272`: Brasil (`146`), Santos FC (`1254`), Brasileirão Betano (`149`), `player_type_6_subtype_1`, chave oficial `Any3W:422`, `Distinguido - Show Time`.

Aprovação exige a comparação integral, em transação READ ONLY, com hashes fonte/banco idênticos; contagem isolada não aprova esta frente.

## Ímpetos — em aberto

- O Extrator deve reler os dois slots de ímpeto de cada carta, incluindo vaga real.
- Cada ímpeto deve resolver seus atributos afetados, efeito máximo, tipo, ativação e faixas de efeito.
- País, clube e liga são relações distintas quando usados como condição; nunca texto livre ou inferência pelo nome.
- Amostras obrigatórias: Vózinha para efeito sempre ativo; Messi para Proteção de posse por nacionalidade; Neymar Jr para Pacote completo por ligas brasileiras.

## Execução final

Quando todas as cinco frentes estiverem concluídas, executar uma leitura nova do jogo e gerar um relatório único com, para cada frente:

- campos e relações exigidos;
- contagens esperadas e encontradas;
- amostras obrigatórias;
- diferenças encontradas;
- resultado: aprovado ou reabrir a frente.

O relatório final só será aprovado se não houver campo faltante, relação órfã, amostra divergente ou dado que o Extrator deixou de reler.
