# Contrato e mapeamento da Ficha v1

Data do fechamento: 2026-09-04  
Atualização de seleção/navegação: 2026-09-05  
Autoridade operacional: schema `clube_novo` do projeto Supabase `trqqpsnafpbudtvvicch`  
Autoridade visual: `PREVIA-FICHA.html` e `PREVIA-FICHA.png`, que permanecem congelados

## 1. Decisão de arquitetura

A página usa um único buscador público e versionado da Ficha (RPC, em termos técnicos):

`public.site_novo_ficha_v1(p_card_id text default null, p_linha_id bigint default null) returns jsonb`

O navegador não recebe acesso direto a tabelas ou views. O `ficha.js` faz uma única requisição na abertura inicial, valida o envelope e preenche `ficha.html`. Depois disso, uma escolha explícita de outra build faz uma única nova requisição à mesma RPC em segundo plano, valida card e linha e atualiza em conjunto somente o estado dependente da build. A URL recebe `linha` por `history.pushState` após o sucesso, sem abertura completa da página. Não existe segunda porta, servidor intermediário nem um arquivo por bloco da página.

O controlador cancela a leitura anterior quando há uma nova escolha e mantém uma versão monotônica da requisição para que nenhuma resposta antiga substitua a escolha mais recente. Voltar/Avançar usa `popstate` e a mesma porta. Se uma troca falhar, a última ficha válida e sua URL permanecem visíveis e o erro é explícito; o cliente não faz retry nem fallback silencioso.

O buscador é somente leitura, tem `SECURITY DEFINER`, `search_path` vazio, nomes de objetos totalmente qualificados e permissão de execução limitada a `anon`, `authenticated` e `service_role`. Nenhuma chave privilegiada entra no navegador.

## 2. Envelope

| Campo | Tipo | Nulo | Regra |
|---|---:|---:|---|
| `contrato` | texto | não | Sempre `site-novo-ficha-v1`. |
| `versao` | inteiro | não | Sempre `1`. |
| `status` | texto | não | Um dos estados fechados da seção 3. |
| `mensagem` | texto | não | Explicação curta para a tela; não contém detalhe interno. |
| `card_id` | texto | sim | Parâmetro normalizado com `btrim`; nulo quando ausente. |
| `dados` | objeto | sim | Nulo para parâmetro ausente ou card inexistente; objeto nos demais estados. |

O JavaScript rejeita payload que não seja objeto, contrato ou versão diferentes, status desconhecido e `dados` ausente nos estados que exigem card.

Na URL, os parâmetros canônicos são `?card=<card_id>` e `?linha=<linha_id>`. Por compatibilidade, `?card_id=` e `?linha_id=` também são aceitos. Quando as duas formas do mesmo parâmetro existem, a forma curta canônica tem precedência, inclusive se estiver vazia. `card` sozinho pede a build pública padrão de maior pontuação; uma página que já apresenta uma build deve acrescentar seu `linha_id`, pois `linha` é a autoridade exata e não aceita substituição silenciosa.

## 3. Estados fechados

| Estado | Condição | Comportamento visual |
|---|---|---|
| `parametro_ausente` | `p_card_id` nulo ou vazio | Ficha bloqueada com instrução de uso de `?card=`. |
| `card_nao_encontrado` | não existe `clube_novo.carta_jogo.card_id` exato | Ficha bloqueada; nenhum card parecido é usado. |
| `card_sem_build_publicada` | card existe, mas não há linha que cumpra integralmente o selo de publicação | Dados cadastrais aparecem; blocos de build ficam explicitamente indisponíveis. |
| `builds_em_atualizacao` | o card participa do lote V10, mas ainda não possui linha com os dois resultados compatíveis | A tela informa atualização; não calcula nem inventa build. |
| `linha_nao_encontrada_ou_nao_publicada` | `p_linha_id` foi informado, mas não pertence ao card ou não cumpre o selo | Dados cadastrais aparecem; a linha pedida não é substituída silenciosamente. |
| `atributos_em_atualizacao` | há nota oficial sem vetor final de 26 itens e existe registro vivo do card em lote não finalizado do Otimizador | Nota e demais valores persistidos aparecem; os 26 atributos mostram o estado temporário de atualização. |
| `atributos_aguardando_publicacao` | há nota oficial sem vetor final de 26 itens, mas não existe evidência viva de fila nas tabelas auditadas | Nota e demais valores persistidos aparecem; a ausência fica neutra, sem afirmar processamento. |
| `pronto` | card e build publicados, com vetor final de 26 itens | Todos os blocos de leitura suportados são preenchidos. |

## 4. Selo de build publicada

A autoridade de exposição é `clube_novo.build_publicacao_linha_ativa_v1`. Cada
registro fixa os IDs exatos dos dois resultados, a nota oficial, os fingerprints
e a proveniência da versão ativa. A Ficha junta os detalhes pelos IDs dessa ponte,
nunca por um candidato ainda incompleto da linha operacional.

Uma linha só entra no Site Novo quando todos os predicados abaixo são verdadeiros em `clube_novo.build_linha_card`:

- `execucao_tipo = 'producao'`;
- `lote_teste_id is null`;
- `pendencias` não contém `teste_nao_publicado`;
- `publicacao_fingerprint is not null` e `publicada_em is not null`;
- `nota_final is not null`;
- `nota_publicacao_fingerprint_v1 is not null` e `nota_publicada_em_v1 is not null`;
- `build_otimizador_id is not null` e `build_bonificador_id is not null`.

Esses são os campos gravados pelo processo atual de publicação. `estado='pendente'` não é usado como atalho, pois há linhas oficialmente publicadas cujo estado operacional continua `pendente`.

Sem `p_linha_id`, a seleção é determinística: maior `nota_final` primeiro; persistindo empate, vetor final completo de 26 itens, publicação de nota mais recente e menor `id`. Com `p_linha_id`, somente a linha pedida pode ser selecionada. A regra foi instalada pela migração registrada no banco como `20260905215643 ficha_default_maior_nota_v2`; o artefato recuperável local é `20260905185410_MIGRACAO-FICHA-MAIOR-NOTA-V2.sql` e sua contraprova é `20260905185410_VALIDAR-FICHA-MAIOR-NOTA-V2.sql`.

## 5. Mapeamento campo a campo

### 5.1 Identidade e topo

| Campo do DTO | Origem | Chave e grão | Tipo/nulabilidade | Regra e ausência |
|---|---|---|---|---|
| `card.card_id` | `carta_jogo.card_id` | PK; 1 card | texto, não nulo | Igualdade exata com o parâmetro. |
| `card.nome` | `carta_jogo.nome` | `card_id`; 1 card | texto, nulo | `null` vira `Nome não publicado`. |
| `card.foto_url` | `carta_jogo.foto_url_cloudinary` | `card_id`; 1 card | texto, nulo | O cliente aceita somente URL `https:`; caso contrário mantém o espaço visual de imagem. |
| `card.box` | `carta_jogo.box` | `card_id`; 1 card | texto, nulo | Texto cadastral, sem inferência. |
| `card.tipo_carta` | `tipo_carta_jogo.nome_exibicao` | `carta_jogo.tipo_carta_id = tipo_carta_jogo.tipo_carta_id`; 0..1 | texto, nulo | Sem fallback para rótulo legado. |
| `build.nota_final` | `build_linha_card.nota_final` | linha publicada selecionada; 0..1 | numérico, nulo | É a única nota mostrada. O cliente apenas formata duas casas. |
| Indicador visual `Pode melhorar` | `build.nota_final` corrente + maior `builds_publicadas[].nota_final` da mesma função | card + função corrente; 0..N referências prontas | percentual calculado na interface | Há uma única regra para qualquer estado da Ficha: comparar a pontuação total mostrada naquele instante com a melhor build pronta da mesma função. Não existe distinção entre build “estática” e “em construção”. Sem referência válida, mostra `não publicado`. |
| `card.no_elenco` | sem contrato de usuário nesta fase | — | nulo | Botão permanece informativo e desabilitado. |
| `card.estilo_jogo` | `carta_playstyle_jogo` + `playstyle.nome_tela` | card + `slot_fisico=1`; 0..1 | texto, nulo | Ordenação física do slot; sem rótulo legado. |
| `card.estilos_jogo[]` (V2) | `carta_playstyle_jogo` + `playstyle` | card + slot físico; 0..2 | array de `id,slot,tipo,nome` | Ambos os slots em ordem física: 1 ofensivo, 2 defensivo. A Ficha usa este array, sem duplicar o singular. A posição nativa só define destaque visual. |
| `card.posicao_nativa` | `carta_posicao_principal_jogo` + `posicao_jogo.codigo_pt,nome_pt` | card; 0..1 esperado | objeto, nulo | Menor `posicao_id` como desempate defensivo. |
| `card.posicoes[]` | `posicao_jogo` + `carta_posicao_jogo` + `carta_posicao_principal_jogo` | uma linha por posição cadastrada no catálogo | array de objetos | Ordem do gramado: PTE, CA, PTD, SA, MLE, MAT, MLD, MLG, VOL, LE, ZC, LD, GO. `principal=true` identifica a nativa; fora dela, `nivel > 0` identifica posição permitida e `nivel = 0` ou `null` identifica posição indisponível. GO pode ter `nivel=null` e ainda ser nativa porque a principal vem da relação própria. |

### 5.2 Contexto e lista de builds

| Campo do DTO | Origem | Chave e grão | Tipo/nulabilidade | Regra e ausência |
|---|---|---|---|---|
| `build.linha_id` | `build_linha_card.id` | PK; linha selecionada | bigint, nulo | Nulo se não houver build publicada. |
| `build.funcao.id,rotulo,sigla,grupo,familia` | `funcao_sistema` | `build_linha_card.funcao_id`; 0..1 | objeto, nulo | Só campos atuais; `nome_legado` e `codigo_legado` não saem. |
| `build.posicao.id,codigo,nome` | `posicao_jogo` | `build_linha_card.posicao_id`; 0..1 | objeto, nulo | Usa `codigo_pt` e `nome_pt`. |
| `builds_publicadas[]` | linhas que cumprem o selo + função + posição | card; 0..N | array | Mesma ordem da seleção: vetor completo primeiro, nota desc., publicação desc., id asc. Cada item tem apenas linha, função, posição, nota e seleção. |
| `builds_publicadas_total` | contagem do array anterior | card | inteiro | Zero quando não há build publicada. |
| `builds_salvas_total` | sem contrato de usuário nesta fase | — | inteiro | Sempre `0`; não se finge dado de usuário. |
| Faixa `BUILD EM EXIBIÇÃO` | `build.funcao.rotulo`, `build.posicao.codigo`, `build.nota_final` | linha selecionada | apresentação local | Informa a build que alimenta os dois placares e o Bloco 3; não é um segundo seletor. |
| Ação `MELHOR / BUILD RECOMENDADA` | maior `nota_final` finita entre os grupos já recebidos em `builds_publicadas[]` | card | seleção somente leitura | Mantém texto fixo e nunca informa qual build está aberta. Reutiliza a mesma troca assíncrona por `linha_id`; se a própria linha já estiver em exibição, o seletor termina localmente sem nova consulta. Não recalcula nota e não escreve. |
| Controle `MINHAS / BUILDS SALVAS` | `builds_salvas_total` | usuário não contratado | informativo desativado | Mostra `0` nesta versão e não abre lista inexistente. |
| Controle `PERSONALIZAR / ESTA BUILD` | sem contrato de rascunho nesta fase | — | desativado | Prepara a hierarquia visual, mas não cria cópia, estado local falso nem escrita. |
| `interacoes.referencia_ideal`, `build_atual`, `criar`, `ver_mais` | controle público desta fase | — | booleano | Permanecem `false`. A ação somente leitura `MELHOR` deriva exclusivamente da lista publicada já recebida e não transforma essas flags em autorização de escrita. |
| Ligação campinho ↔ builds ↔ rota | `card.posicoes[].codigo` + `builds_publicadas[].posicao.codigo,linha_id` | código de posição e linha dentro da mesma resposta | filtro local + troca assíncrona somente leitura | Clicar numa posição destaca localmente todas as builds renderizadas com o mesmo código. Clicar numa build consulta a mesma RPC com sua linha publicada, troca em conjunto os campos dependentes da build e destaca somente o grupo escolhido e suas posições, sem recarregar a página. A URL só muda após resposta válida. Não há lista fixa por nome de função, dedução pelas builds nem porta paralela. |

### 5.3 Distribuição e técnico

| Campo do DTO | Origem | Chave e grão | Tipo/nulabilidade | Regra e ausência |
|---|---|---|---|---|
| `build.nivel_maximo` | `carta_jogo.level_cap` | card | inteiro, nulo | Exibição direta. |
| `build.orcamento_total` | `carta_jogo.orcamento` | card | inteiro, nulo | Exibição direta. |
| `build.orcamento_gasto` | sem coluna persistida atual | — | nulo | Sempre `null`; nenhuma soma das barras é feita. |
| `build.evolucao` | `carta_jogo.level_cap` + `carta_jogo.orcamento` | card | objeto | `nivel_1_sem_evolucao` somente quando o teto é 1 e o orçamento é 0; essa combinação está documentada no manual do Otimizador e comprovada em dados reais. |
| `build.barras[]` | `build_otimizador.barras` | `build_linha_card.build_otimizador_id`; 0..1 | JSON persistido convertido em array | Chaves aceitas e ordem: `shooting`, `passing`, `dribbling`, `dexterity`, `lowerBodyStrength`, `aerialStrength`, `defending`, `gk1`, `gk2`, `gk3`. Valor inexistente vira `null`. Em card `level_cap=1` + `orcamento=0`, as dez barras devem ser zero por regra do jogo. |
| `build.tecnico.id,nome` | `build_otimizador.tecnico_id` + `tecnico_jogo.nome_en` | build; 0..1 | objeto, nulo | Nome cadastrado no jogo; sem inventar abreviação. |
| `build.tecnico.atributos[]` | `tecnico_atributo_jogo` + `atributo_jogo.nome_pt` | técnico; 0..N | array | Ordem física `ordem`; expõe apenas nome atual e delta persistido. |
| `build.tecnico.estilos[]` | `tecnico_estilo_jogo` | técnico; 0..N | array | Proficiência persistida, ordem desc. e código atual. |
| `build.tecnico.alternativo` | sem seleção/publicação específica | — | nulo | Nenhuma escolha é fabricada. |
| `build.tecnico.sugeridos[]` (V2) | régua selada do lote + técnico escolhido + pesos do resultado publicado | build ativa; 0..N | array de `id,nome,estilos[],atributos[]` | Mesmo multiplicador e mesmos efeitos nos atributos com peso. Estilos indicados são os de proficiência máxima compatível; não basta o nome ou nível do técnico. |
| `build.tecnico.sugeridos[].atributos[]` | `tecnico_atributo_jogo` por ID exato + `atributo_jogo.nome_pt` | versão do substituto; 0..N | array de `codigo_atributo,nome,delta`, ordem física | Expõe todos os bônus cadastrados dessa versão, inclusive atributos sem peso na função; não altera a regra de equivalência nem a nota. Array vazio significa sem bônus cadastrados, não autoriza copiar os bônus do técnico escolhido. |
| `build.tecnico.sugeridos_estado` (V2) | helper privado de sugestões | build ativa | `pronto` ou `nao_publicado` | Distingue ausência real de equivalentes de ausência de contexto selado. |

### 5.4 Habilidades e ímpetos

| Campo do DTO | Origem | Chave e grão | Tipo/nulabilidade | Regra e ausência |
|---|---|---|---|---|
| `card.habilidades_especiais[]` | `carta_habilidade_jogo` + `habilidade_jogo` | card + `tipo='especial'`; 0..N | array | Ordem da carta, depois ordem de catálogo e ID. |
| `card.habilidades_nativas[]` | mesmas tabelas | card + tipo diferente de `especial`; 0..N | array | Mesma ordem; nomes de `nome_pt`. |
| `build.habilidades_adicionadas[]` | `build_otimizador.habilidades_adicionais` + catálogo | ordem do array persistido; 0..N | array | `unnest ... with ordinality`; IDs não catalogados continuam identificados com nome nulo. Em card `level_cap=1` + `orcamento=0`, o array deve estar vazio porque esse tipo não aceita habilidade adicional. |
| `build.habilidades_sugeridas[]` (V2) | `habilidade_jogo.gemeas` + régua selada + adicionais do resultado ativo | build + candidata; 0..N | array de `id,nome,substitui[]` | `substitui` lista somente os IDs/nomes adicionados que a candidata pode substituir individualmente. Efeitos/tipo idênticos, fabricável, elegível, sem bloqueio na função, não nativa e não já adicionada. |
| `build.habilidades_sugeridas_estado` (V2) | helper privado `site_novo_ficha_sugestoes_v1` | build ativa e fingerprint do resultado | `pronto` ou `nao_publicado` | Só consulta; não altera notas, filas nem habilidades. Trocas futuras exigem validação no editor/salvamento. |

As sugestões acima **não são o catálogo de permissões para adicionar habilidades manualmente**. No futuro editor, a lista do botão Adicionar deverá refletir somente elegibilidade pelo jogo, por carta e tipo goleiro/linha, sem aplicar decisões estratégicas do Otimizador. A política de seleção automática deve permanecer separada da permissão manual. Habilidades legais mas não recomendadas poderão ser adicionadas/substituídas e mudar a nota; somente o fluxo específico de gêmeas promete equivalência. O contrato de edição ainda não está implementado e `editar_habilidades` continua falso.

| Campo do DTO | Origem | Chave e grão | Tipo/nulabilidade | Regra e ausência |
|---|---|---|---|---|
| `build.impetos[]` | `carta_impeto_jogo`, `build_otimizador.impeto_adicional_codigo`, `impeto_jogo`, `impeto_atributo_jogo` | card, dois slots | array | Slot nativo usa o código da carta; slot marcado `vaga` usa somente o código adicional persistido da build. |
| `build.impetos[].efeitos[]` | `impeto_atributo_jogo` + `atributo_jogo.nome_pt` | código final do ímpeto; 0..N | array | Exibe deltas persistidos por atributo, na ordem física. |
| `build.impetos[].delta_uniforme` | mesmos deltas persistidos | código final | smallint, nulo | Só recebe valor quando todos os efeitos têm o mesmo delta; é compactação de apresentação, não cálculo de atributo ou nota. |
| `build.impetos[].condicao_nivel` | `build_linha_card.impeto_condicional_nivel` | linha selecionada + código condicional | smallint, nulo | Só é associado quando `impeto_condicional_codigo` coincide com o ímpeto final. |

### 5.5 Atributos finais

| Campo do DTO | Origem | Chave e grão | Tipo/nulabilidade | Regra e ausência |
|---|---|---|---|---|
| `build.atributos[]` | `atributo_ordem_otimizador`, `atributo_jogo`, `carta_atributo_jogo`, `build_otimizador.atributos_finais` | 26 índices `0..25` | array de 26 objetos quando catálogo completo | Nome/grupo vêm do catálogo; valor base da carta; valor final do índice correspondente no vetor publicado. |
| `build.atributos[].grupo_tela` | índice do atributo | atributo | texto | Partição apenas visual: ataque `0..6,8,9`; físico `7,13,14`; atletismo `10..12,15,16`; defesa `17..20`; goleiro `21..25`. |
| `build.atributos[].pontos` | sem coluna publicada por atributo | — | nulo | Sempre `null`; a tela mostra travessão. Nenhum peso ou fórmula é exposto. |
| `build.atributos[].valor_pos_evolucao` | `carta_atributo_jogo.valor` somente para card sem evolução | card + atributo | smallint, nulo | Em card nível 1 sem evolução, o valor após evolução é o próprio valor inicial por regra do jogo. Nos demais cards fica nulo; não se soma barra. |
| `build.atributos_total_pontos` | sem total publicado atual | — | nulo | Sempre `null`. |
| `build.atributos_completos` | forma/tamanho de `atributos_finais` | build | booleano | Verdadeiro apenas para array JSON com exatamente 26 itens. |
| `build.atualizacao_atributos` | `otimizador_lote_producao_candidata_v5`, `otimizador_lote_producao_carta_v3`, `otimizador_lote_producao_linha_v3` e `otimizador_lote_producao_v3` | card em lote não finalizado | objeto | `fila_confirmada` somente quando há registro vivo; caso contrário `sem_evidencia_de_fila`. Não usa a previsão do operador como dado. |

`build_otimizador.atributos_internos` e `arows_snapshot` não saem no contrato. `nota_do_motor`, pesos, numerador, denominador e fórmulas também não saem.

Esses campos, embora não sejam expostos ao navegador, explicam a proveniência da nota gravada. A publicação normaliza os 26 atributos completos usados na conta (`atributos_internos`; fallback físico histórico `atributos_finais` apenas quando o primeiro é nulo) contra pesos e alvos do molde em `arows_snapshot`. A fórmula é `100 * soma(peso * atributo_completo) / soma(peso * alvo_do_molde)`, sem arredondamento, piso, teto, K ou comparação populacional. Depois, `nota_final = nota_do_motor + nota_bonus_total`.

A nota bruta do Otimizador comprova a Build vencedora, mas não é nota de tela. No caminho dos atributos, barrinhas e proficiência param em 99; boost de técnico, ímpetos e efeitos de habilidades vêm depois e podem produzir valores completos acima de 99. O Site Novo não refaz essas etapas: lê somente `build_linha_card.nota_final` e formata duas casas.

Na prova do Messi, linha `30015`, a nota bruta é `466,8`, o numerador `10152`, o denominador `9184,5`, a normalizada `110,5340519353258207`, o bônus total `2,0281` e a final gravada `112,5621519353258207`, exibida como `112,56`. Usar os 26 atributos mostrados no jogo reduziria a normalizada para `104,9376667211062116` e a final para `106,9657667211062116`, exibida como `106,97`; esse comportamento pertence ao site abolido.

Documentos V1 que descrevem soma de nota bruta com bônus, ou contratos/views abolidos, são somente históricos e não regem este contrato.

Card com `level_cap=1` e `orcamento=0` é um estado válido e completo. A regra é categórica: atributo inicial é igual ao atributo pós-evolução; não há acréscimo por evolução e as dez barras devem ser zero; o card não aceita habilidades adicionais e o array deve estar vazio. As habilidades nativas permanecem. Os ímpetos nativos permanecem quando o card os possui; não se inventa ímpeto quando não possui. O técnico continua válido para todos e seus deltas vêm da build. A nota e o vetor final continuam sendo os valores prontos publicados, sem reaplicar qualquer modificador no navegador. A completude depende do vetor oficial com 26 atributos, não de barra positiva.

A auditoria física somente leitura de 2026-09-04 confirmou a regra em todas as linhas publicadas encontradas desse grupo: 49.287 linhas de 3.064 cards, zero linhas com barra diferente de zero, zero linhas com habilidade adicional e zero linhas sem técnico.

### 5.6 Rodapé: IA, físico, pé e corpo

| Campo do DTO | Origem | Chave e grão | Tipo/nulabilidade | Regra e ausência |
|---|---|---|---|---|
| `card.estilos_ia[]` | `carta_estilo_ia_jogo` + `estilo_ia.nome_tela` | card; 0..N | array | Ordem por bit físico; não usa o array JSON redundante de `carta_jogo`. |
| `build.bonus_ia` | `build_bonificador.bonus_ia` | build; 0..1 | numérico, nulo | Persistido; somente formatação de sinal no cliente. |
| `card.altura_cm,peso_kg,idade_anos,resistencia_lesao` | `carta_jogo.altura,peso,idade,resistencia_lesao` | card | inteiro/texto, nulos | Exibição direta com unidade acrescentada pelo cliente. |
| `card.pe[]` | `carta_pe_jogo` + `pe.nome_pt` | card + campo/valor; 0..N | array | Três campos esperados: dominante, uso e precisão. Rótulo vem do catálogo. |
| `card.pe[].rotulo_valor` (V2) | `pe.nome_pt` para dominante; `pe.nome_antigo` para uso/precisão | campo + valor físico | texto, nulo | O catálogo conserva nessa coluna as etiquetas dos níveis (ex.: Ocasionalmente, Muito alta); `nome_pt` nos dois últimos campos é o título, não o nível. A tela mostra o rótulo recebido, nunca o número bruto ou fator de bônus. |
| `build.bonus_pe` | `build_bonificador.bonus_pe` | build | numérico, nulo | Valor final persistido; não soma `pe.valor_bonus`. |
| `card.corpo[]` | `carta_corpo_jogo` + `corpo_ordem` | card + código; 0..N | array | Somente medidas `usado_pelo_motor=true`, na ordem física `pos`. |
| `card.corpo[].bonus` | `build_bonificador.bonus_fisico_detalhe -> corpo_ordem.nosso` | build + medida | numérico, nulo | Leitura direta da chave JSON persistida. |
| `build.bonus_fisico_total` | `build_bonificador.bonus_fisico_total` | build | numérico, nulo | Persistido; não soma as medidas no navegador. |

### 5.7 Ações sem escrita nesta entrega

`OTIMIZAR`, ajustes `−/+`, seleção de técnico, adicionar/remover habilidade, copiar, limpar, `SALVAR MINHA BUILD`, elenco, `MINHAS BUILDS` e `PERSONALIZAR ESTA BUILD` mantêm tamanho, posição e hierarquia do desenho, mas ficam desabilitados e com texto de apoio. `MELHOR BUILD RECOMENDADA` é a única ação adicional desta faixa: apenas seleciona por `linha_id` uma build já publicada usando a mesma porta de leitura da Ficha. Esta entrega não autoriza portas de escrita.

## 6. Provas de amostra que o contrato deve preservar

- Weston McKennie `55068997045101`: sem `linha`, a porta selecionou a linha `8477`, Lateral ofensivo LD, nota `101,89903756033348`, que coincide com a maior nota de `builds_publicadas[]`; com `linha=8475`, selecionou exatamente Lateral defensivo LD, nota `95,02574835983803`; com `linha=8474`, selecionou exatamente Lateral defensivo LE com a mesma nota. As três leituras retornaram `pronto` e 26 atributos.
- Messi `89136409091415`: linha determinística `30015`, nota oficial `112.56215193532582`, função `Atacante criador`, posição `PTD`, técnico `Rudi Garcia` e vetor final de 26 itens; estado esperado `pronto`.
- No mesmo readback público de 04/09/2026, a lista pronta do Messi trouxe Atacante criador em `112.56215193532582`; ao comparar a pontuação corrente idêntica, o Bloco 1 deve mostrar `0%`.
- Dani Olmo `106787651039542`: linha determinística `2778`, nota oficial `109.82407297762478`, função `Atacante infiltrador`, posição `MAT`, técnico `Xabi Alonso`, porém sem vetor final. A leitura de 2026-09-04 não encontrou Dani nas tabelas vivas de lote auditadas; por isso o estado esperado naquele instante é o neutro `atributos_aguardando_publicacao`, apesar da previsão operacional informada pelo usuário. Se surgir registro de lote não finalizado, o mesmo código muda para `atributos_em_atualizacao`; quando uma nova linha completa for publicada, muda para `pronto`.
- Kubo Takefusa `105840610761736`: `level_cap=1`, `orcamento=0`, `cap_estimado=false`, linha publicada `5790`, vetor final de 26 itens e dez barras persistidas em zero; é a amostra válida de card nível 1 sem evolução e deve retornar `pronto`.
- Card inexistente: `card_nao_encontrado`.
- Parâmetro vazio: `parametro_ausente`.

Os números acima são provas de leitura do estado encontrado em 2026-09-04; não são valores codificados na página nem no buscador.

### 6.1 Contador de distribuição no envelope V2

`dados.build.pontos_distribuicao` contém `estado`, `total`, `gastos` e `restantes`. É enriquecimento somente leitura de `site_novo_ficha_v2`, feito pelo helper privado `clube_novo.site_novo_contador_pontos_v1(jsonb,integer)`, sem modificar o campo histórico `orcamento_gasto` nem qualquer resultado persistido.

Somente `estado=valido` e valores inteiros coerentes permitem mostrar `restantes/total`. Dados insuficientes retornam `incompleto`; gasto acima do orçamento retorna `invalido`. Nesses estados, `restantes` é nulo, não zero. O frontend apresenta a ausência, nunca estima o gasto. Migração: `20260906054543_ficha_contador_pontos_v1.sql`; recuperação do wrapper anterior: `RECUPERAR-FICHA-ANTES-CONTADOR-20260906.sql`.

## 6.1 Atributos no jogo e no sistema

A projeção publicada expõe `valor_jogo` a partir de `build_otimizador.atributos_finais` e `valor_sistema` a partir de `build_otimizador.atributos_internos`, ambos da mesma build ativa publicada, pelo índice oficial. Não recalcula nenhum vetor. `valor_final` permanece compatível com `valor_jogo`; não pode preencher `valor_sistema`. Ausência de um vetor completo de 26 itens retorna nulo para a respectiva projeção.

Vitrine e modal usam somente os títulos BASE / FINAL. BASE lê `valor_base` (no editor, `base`), o atributo original da carta, em azul-claro. FINAL lê `valor_sistema` (no editor, `sistema`), incluindo a valoração de habilidades, em verde. O vetor de jogo permanece separado nos dados, sem coluna na interface; nunca é usado para preencher FINAL. Pós-evolução permanece no detalhe. Os nomes dos atributos usam peso normal, sem negrito. A nomenclatura BASE / FINAL foi escolhida pelo usuário. O frontend não aplica limite de 100 nem converte efeitos de habilidade em atributos: apenas mostra a resposta. Builds pessoais seguem o mesmo contrato via `build_editor.apresentar_v1`; registros antigos sem o valor de sistema exibem ausência até novo salvamento explícito.

Migrações: `20260906084200_atributos_jogo_sistema_v1.sql` (leitura pública) e `20260906084238_editor_atributos_jogo_sistema_v1.sql` (projeção privada no diretório do motor). Permissões, nota publicada e snapshots existentes preservados.

## 7. Fora do contrato

- as seis views públicas aposentadas;
- `public.frontend_build_publicada_v2`;
- acesso direto do navegador ao schema `clube_novo`;
- tabelas, filas ou serviços do Otimizador, Bonificador, Extrator ou Railway;
- cálculo/recomposição de nota, pontos por atributo ou orçamento gasto; a única conta visual autorizada nesta fase é a comparação simples do `Pode melhorar` entre a pontuação corrente e as builds prontas da mesma função;
- gravação de elenco, build, técnico, habilidade ou ímpeto;
- publicação, hospedagem ou deploy do Site Novo.
