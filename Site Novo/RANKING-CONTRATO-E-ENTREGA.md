# Ranking conectado — contrato e entrega

06/09/2026. Substitui o estado desconectado de `RANKING-PREVIA-VISUAL.md`. Autorização nesta tarefa: conectar Mix, por card e por jogador ao banco, preservar o design e paginar com números para futura integração dos anúncios nos banners.

## Abrir e usar

Abra `index.html` na pasta operacional `Site Novo` e clique em Ranking, ou use `outputs/ABRIR-RANKING.cmd`. Se já estiver aberto, atualize a página para carregar os arquivos novos.

- Geral: por card, por jogador e Mix.
- Setores e funções: carregados e filtrados pelo contrato do banco.
- Busca: digite o nome e pressione Enter ou Buscar. Busca por trecho, sem diferenciar maiúsculas; acentos continuam significativos.
- Filtros: estilo de jogo, posição nativa e função. Estilo considera qualquer slot físico do card.
- Páginas numeradas com Anterior/Próxima; primeira página com 33 resultados (3 no pódio e 30 na grade), seguintes com 30. Não há carregamento por rolagem. A última página contém somente os resultados restantes.
- Cada card abre `ficha.html?card=<id>&linha=<id>` em outra aba, com a build exata do resultado.
- Imagem ausente ou com erro aparece como Sem imagem. Não existe foto, nota ou resultado inventado.
- Apresentação atualizada: classificação junto da nota, função em destaque e posição em etiqueta. Filtros ativos ficam visíveis fora do painel e podem ser limpos em conjunto. Paginação no topo e rodapé, com os mesmos intervalos e evento de troca de página.

## Regra de seleção, exclusivamente no banco

Fonte: `clube_novo.build_publicacao_linha_ativa_v1`, mesma fonte de notas publicada da Ficha, com vínculo à linha, card, função e posição. Essa tabela já é a fronteira pública finalizada: somente recebe produção publicável, sem lote de teste nem marcador `teste_nao_publicado`. O Ranking não reabre `build_linha_card` para validar outra vez uma linha já publicada. Nota finita e data de publicação continuam obrigatórias.

O banco filtra primeiro. Depois:

- Mix mantém cada linha publicada.
- Por card mantém uma linha por `card_id`.
- Por jogador mantém uma linha por identidade física do jogador.

A mesma ordem serve à seleção e à classificação: `nota_final DESC`, `card_id COLLATE C`, `funcao_id`, `posicao_id`, `linha_id`, todos crescentes depois da nota. Os desempates só estabilizam a ordem; não modificam nem arredondam a nota. A classificação é ordinal, contínua, 1, 2, 3… O navegador apenas formata `nota_final` com duas casas decimais.

Identidade do jogador: `card_id::bigint & 262143`, parte baixa de 18 bits, conforme `4-DOCUMENTOS/MANUAL-TECNICO.md`, linhas 79–82, e o registro de evidência física `7-VARREDURA-DO-JOGO/RECUPERACAO/ARQUIVOS-LEGADOS-DA-PASTA/CONTEXTO-PARA-A-MAQUINA-DO-JOGO.md`, seção 3. A antiga regra de 23 bits citada em `A-CASCA-INTEIRA-o-que-sai-para-o-banco.md` não foi usada. Nenhuma função do schema antigo foi chamada. Validação atual dos 1.935 cards publicados: 872 identidades, nenhuma identidade zero, nenhuma divergência de nome dentro de uma identidade. `grupo_id` não identifica o jogador.

Setores usam o catálogo atual de funções; Volante de contenção (ID 17) entra em Defesa e Volante de construção em Meio, preservando a organização visual confirmada no legado. Os rótulos vêm do banco; não há catálogo operacional embutido na tela.

## Porta pública

`public.site_novo_ranking_v1` — contrato `site-novo-ranking-v1`, versão 1.

| Parâmetro | Regra |
|---|---|
| p_modo | card / jogador / mix; padrão card |
| p_setor | geral / goleiro / defesa / meio / ataque |
| p_funcao_id | ID textual de função ativa, ou null |
| p_busca | texto de até 100 caracteres |
| p_posicao_nativa_id | ID inteiro existente, inclusive 0 para GO, ou null |
| p_estilo_id | ID inteiro existente no catálogo, ou null |
| p_limite | inteiro de 1 a 60; interface usa 33 na primeira página e 30 nas demais |
| p_offset | inteiro de 0 a 100000 |

Resposta: contrato, versão, status pronto/vazio, modo/setor, total após agrupamento, limite/offset, tem_mais, itens ordenados e catálogos. Cada item possui IDs textuais de linha/card/jogador/função, classificação inteira, nota_final numérica, publicada_em, nome, função, posição e setor; foto_url e box são opcionais/nulos. O adaptador rejeita contrato incompatível, nota ausente ou não finita, perda de tipos dos IDs, classificação incoerente, linhas duplicadas e respostas incompletas. Só aceita URL HTTPS para imagens. IDs de card/linha nunca passam por Number.

Cada mudança faz uma consulta nova; não há cópia persistida dos resultados nem recalculo de nota. A paginação reflete publicações disponíveis em cada consulta, sem congelamento de snapshot entre cliques. Publicações novas podem alterar totais e posições entre páginas.

## Banners

Após carga bem-sucedida, `ranking.js` emite `site-novo:ranking-pagina` no window com `pagina`, `limite`, `total`, `modo`, `setor` e `motivo`. Troca por número, Anterior ou Próxima usa `motivo: pagina`; carga inicial e filtros usam `consulta`. O controlador futuro dos banners pode ouvir apenas `motivo: pagina`.

Não emite evento em erro, resposta obsoleta/cancelada nem clique na página atual. Nenhum anúncio, rede publicitária, script de publicidade ou atualização real de banner foi conectado. A integração concreta depende da plataforma de anúncios escolhida e de suas regras de atualização.

## Segurança e fronteiras

Função nova STABLE, SECURITY DEFINER, search_path vazio, SQL fixo, parâmetros validados, JIT desligado e apenas SELECT. EXECUTE revogado de PUBLIC e concedido explicitamente a anon/authenticated/service_role. A função precisa ler publicações privadas para entregar somente campos públicos, sem conceder SELECT bruto em clube_novo. Verificação atual: anon e authenticated continuam sem SELECT na tabela de publicação ativa.

O advisor sinaliza execução pública de SECURITY DEFINER para anon/authenticated. É uma exposição intencional e limitada deste contrato de consulta pública; não contém SQL dinâmico, escrita, segredos, dados de usuário ou acesso ao editor. Outros avisos preexistentes do projeto não foram alterados.

Documentação consultada: https://supabase.com/docs/guides/database/functions . Changelog consultado; não houve uso dos endpoints de logs em mudança.

Não foram alterados arquivos da Ficha, documentos da Ficha, motores, fila, dados cadastrais, finalizadora ou publicação existente. A alteração remota foi adicionar esta RPC de leitura e seus grants. Não houve deploy do site, commit ou push.

## Arquivos

- `ranking-api.js`: única chamada pública e validação de dados.
- `ranking.js`: apresentação e interação, cancelamento e descarte de respostas antigas.
- `ranking.css`: desenho preservado, fotos reais e controles de páginas.
- `index.html`: carrega o adaptador antes do módulo do Ranking.
- `site-shell.js`: mantém a rota e atualiza avisos de disponibilidade do Ranking na Home.
- `supabase/migrations/20260906080603_site_novo_ranking_v1.sql`: criada pela CLI e aplicada remotamente; arquivo alinhado à versão 20260906080603 registrada pelo MCP no histórico remoto.
- `supabase/migrations/20260907043214_ranking_ler_publicacao_sem_reconsulta_operacional.sql`: remove a reconsulta da tabela operacional depois da publicação e mantém o mesmo contrato público.
- `tests/ranking.test.cjs`, `tests/fixtures/ranking-publico-20260906.json`: testes e snapshot REAL de leitura pública para regressão, nunca usado pela página.

## Evidência de validação

Atualização de design: paginação 33/30 para completar as fileiras de seis cards. Offsets 0, 33, 63 etc.; busca e filtros reiniciam com limite 33. O evento de banners calcula a página considerando esse primeiro bloco diferente. Em telas de duas colunas, o terceiro colocado ocupa a largura da grade e fecha o pódio antes dos cards comuns. HTTP público validou as posições 1–93, sem saltos ou cards repetidos; testes de navegação validaram ida/volta, eventos e limites de 33/34/63/64 resultados. Fixture real adicional: `tests/fixtures/ranking-publico-33-20260906.json`. Testes do Ranking, shell e sintaxe passaram; sem inspeção visual em navegador nesta atualização. As contagens de 30 por página abaixo documentam a validação anterior.

Snapshot observado em 06/09/2026, aproximadamente 08:06–08:15 UTC:

| Modo | Total confirmado |
|---|---:|
| Mix | 35.027 linhas |
| Por card | 1.935 cards |
| Por jogador | 872 jogadores |

Contagem independente das publicações confirmou os três totais. Nas primeiras 60 linhas de cada modo, nenhuma seleção por card/jogador omitiu uma nota maior do mesmo grupo.

As notas das três primeiras linhas do Ranking por card foram conferidas contra `site_novo_ficha_v2`:

| Linha | Nota exata em ambos | Ficha |
|---|---|---|
| 5852 | 114.823086424372 | pronto |
| 5765 | 114.53447071084982 | pronto |
| 13720 | 113.33383903876673 | pronto |

HTTP público com publishable key: modos card/jogador/mix, setor Goleiro, posição nativa 0, função 18, estilo 270, segunda página e resultado vazio passaram. Segunda página: 30 linhas, classificação inicial 31, sem sobreposição de card com a primeira página na conferência. Parâmetro inválido retornou HTTP 400. Origem `null` (arquivo local) foi aceita pelo CORS. Tempos de três chamadas iniciais: 2.141 ms, 883 ms e 1.063 ms, incluindo rede.

Testes de sintaxe e `node tests/ranking.test.cjs` / `node tests/site-shell.test.cjs` passaram. Cobertura: resposta real, rejeições de contrato, renderização e link da linha exata, escape de texto, filtros, páginas numeradas, evento de banner, clique na mesma página, cancelamento, respostas fora de ordem, desmontagem e erro sem resultados antigos.

Não houve teste visual de interação em navegador nesta etapa. A entrega foi conferida por HTTP público, SQL independente e testes de contrato/apresentação; a conferência visual está disponível no site local.

### Correção da carga fria em 07/09/2026

Após novas publicações, a primeira consulta de Ataque levou 4.284 ms e ficou próxima do limite interno de cinco segundos. O plano mostrou que a RPC voltava à tabela operacional para cada publicação candidata. A auditoria das 53.228 linhas ativas encontrou zero linha ausente, zero linha fora de produção ou de lote de teste, zero identidade divergente e zero ímpeto divergente. A dependência redundante foi removida na fonte.

Depois da migração, as 15 combinações de cinco setores por três degraus responderam HTTP 200. O maior tempo observado foi 1.659 ms; Ataque respondeu entre 316 e 392 ms. A regressão também impede que o SQL canônico volte a juntar `build_linha_card`. Nenhuma fila, motor, resultado ou publicação foi alterada.



## Ranking — reorganização visual de 10/09/2026

Implementação local autorizada: modos por card / por jogador / Mix centralizados na primeira linha; abas Posição / Estilo de jogo / Especialidade na segunda; escolhas em botões maiores ocupando toda a largura e quebrando em linhas conforme o espaço. Posições preservam a sequência existente. Estilos ficam em ordem alfabética em português. Especialidades seguem goleiros, zagueiros, laterais, volantes, meias, alas e ataque. Os rótulos continuam vindo do catálogo. Removida a linha EXIBIR RANKING POR e sua explicação, conforme correção posterior do usuário.

Busca centralizada abaixo dos filtros e da contagem, no lugar da paginação superior. Paginação somente no rodapé. A faixa acompanha a rolagem para que a lista aberta de estilos não cubra os resultados. Seleção, consultas, notas, motores e filas preservados. Arquivos: ranking.js, ranking.css e versão dos recursos no index.html; expectativa da paginação atualizada no teste existente.

Validação: sintaxe e três testes do Ranking aprovados; navegador local confirmou posições em largura completa, estilos em botões alfabéticos e remoção do cabeçalho. Publicação não realizada nesta etapa; aguarda o usuário encerrar suas solicitações. Esta seção substitui a organização visual histórica com seletor fechado, modos abaixo e paginação duplicada.


Publicação confirmada em 10/09/2026: projeto imaginative-granita-ace1ca, deploy 6aa224a6ba9f17d19cc04436. Pacote de 21 arquivos públicos obtidos da versão já publicada, substituindo somente ranking.js, ranking.css e as versões desses recursos no index.html. HTTP 200 e igualdade integral dos três arquivos com o pacote; navegador público confirmou o novo layout com resultados carregados. GitHub não alterado.


Correção visual posterior de 10/09: usuário rejeitou os botões largos de estilos/especialidades. Agora têm largura pelo texto, altura mínima de 30px, padding 6x10px e não crescem para preencher a última linha; grupos centralizados e ordem preservada. Posições mantêm a distribuição anterior. Conferência visual local dos dois eixos e HTTP público dos arquivos CSS/index aprovados. Publicado no mesmo projeto Netlify, deploy 6aa22562694a4935b0b31922. Apenas CSS e sua versão no index mudaram nesta correção.


Ajuste solicitado em seguida: fonte dos botões de estilos/especialidades reduzida de 12px para 10px, altura mínima 24px e padding 4x7px. Posições preservadas em 12px. Publicado e conferido por HTTP e navegador: deploy 6aa225cb26045a94b72926ec; CSS versão 2026091003.


## Correção do ranking por posição — 10/09/2026
Autorização posterior à frente de design: filtrar pela posição da linha publicada antes do agrupamento por card/jogador/Mix. O parâmetro histórico p_posicao_nativa_id continua com o mesmo nome por compatibilidade, mas compara a.posicao_id; a posição principal do card não participa mais. Fonte vigente build_publicacao_exibivel_v3 preservada, assim como degrau, notas, agrupamento e ordenação. Nenhum motor, fila ou resultado foi alterado.
Aplicada migration ranking_filtrar_posicao_da_linha_publicada. Definição integral vigente: CORRECAO-RANKING-POSICAO-LINHA-1009.sql. A correção substitui a descrição antiga de filtro por posição nativa neste manual.
Validação: 60 resultados em cada uma das 13 posições, zero fora da posição; VOL nos três modos e três degraus, 60 resultados por consulta e zero divergências. Caso Pirlo: antes linha 36411 em MLG (114,2832) com VOL selecionado; agora o card 88039581945312 usa linha 36413, VOL, Volante de construção, 113,9056. A leitura pública pelo adaptador real confirmou as linhas VOL 36666, 36413 e 32620. Mudança no leitor já atende o site publicado, sem novo deploy de frontend.


## Estilo ativo antes da seleção — 10/09/2026
Regra confirmada pelo usuário: um estilo selecionado exige vínculo do estilo ao card e ativação na posição da linha publicada. Usa bonificador_regra_playstyle por playstyle_id/posicao_id com da_bonus=true, como na política vigente; Básico 256 não ativa. Não exige associação histórica à função. Só depois escolhe a maior nota por card, jogador ou card/especialidade no Mix. Posições exibidas derivam desse mesmo conjunto elegível. Estilos sem ativação cadastrada não geram resultados; nenhuma regra foi inventada.
Migration aplicada: ranking_selecionar_somente_estilo_ativo_na_linha. Definição integral em CORRECAO-RANKING-ESTILO-ATIVO-1009.sql, sucessora da correção por posição. Notas, motores, filas e cadastro de ativação preservados. Validação: Artilheiro (257) somente CA, 60 resultados por modo sem divergência; 36 estilos consultados e 139 linhas verificadas sem inconsistência; adaptador público confirmou 33 linhas CA por modo.
Botões POR CARD / POR JOGADOR / MIX em maiúsculas. CSS 2026091004 publicado no projeto imaginative-granita-ace1ca, deploy 6aa22e9f7c0ca1dc58c6b219, conteúdo público igual ao pacote.


10/09: TODAS e TODOS OS ESTILOS em maiúsculas nos três critérios do Ranking. Botão geral com borda verde reforçada e preenchimento verde/texto escuro quando selecionado; variante compatível com tema claro. Publicado, arquivos conferidos por HTTP e visual público inspecionado. Deploy 6aa22ffeb9c9604a064ee771, CSS 2026091005.


## Capitalização e auditoria de nomes — 10/09/2026
19 especialidades padronizadas em funcao_sistema.rotulo com iniciais maiúsculas em todas as palavras. Estilos Konami preservados. Quatro colisões exatas encontradas: Goleiro Defensivo, Goleiro Ofensivo, Lateral Defensivo e Lateral Ofensivo. Propostas de Recuado/Avançado aguardam escolha do usuário; não foram aplicadas nesta etapa.
Leitor site_novo_box_card_analise_snapshot_v1 passa a resolver o rótulo atual pelo funcao_id da linha, mantendo intactos os snapshots. SQL: ESPECIALIDADES-ROTULOS-1009.sql. Conferência de 60 fotografias/438 análises: zero alterações fora do campo funcao e zero nomes fora do padrão. Ranking e Ficha devolveram Volante De Construção pelo banco; todas as 19 especialidades conferidas. Não houve recálculo, mudança de IDs, fórmulas ou filas. Demais famílias de nomes de jogo não foram alteradas por esta etapa.


## Renomeação aprovada e aplicada — 10/09/2026
Após aprovação dos quatro nomes: ID 4 Goleiro Recuado; ID 5 Goleiro Avançado; ID 6 Lateral Recuado; ID 7 Lateral Avançado. Alterado apenas funcao_sistema.rotulo. IDs, notas, motores, filas e estilos oficiais preservados. Readback dos quatro nomes no Ranking, Ficha e leitor de Boxes confirmou os rótulos novos; zero colisões exatas com playstyle.nome_tela. A pendência de aprovação anterior está encerrada. A mudança já atende o site publicado sem deploy de frontend.


10/09: corrigida ambiguidade visual do botão TODAS inativo. Usa borda tracejada e texto neutro quando não selecionado; verde exclusivo do estado selecionado. Mesma regra em TODOS OS ESTILOS, com tema claro contemplado. Conferência visual pública com Centroavante Fixo selecionado confirmou TODAS neutro. Deploy 6aa2329c7c0ca1fca6c6b074, CSS 2026091006, arquivos públicos conferidos.


### 10/09/2026 — Estado dourado do filtro Todas
TODAS / TODOS OS ESTILOS usa fundo dourado preenchido e texto escuro quando selecionado; quando inativo, fundo escuro com texto e borda dourados. Tema claro tem contraste correspondente. Publicado no projeto imaginative-granita-ace1ca, deploy 6aa233ef26045ae7402926bd, ranking.css v2026091007. CSS e index públicos conferidos contra o pacote; aria-pressed e cores dos dois estados verificados no navegador.

### 10/09/2026 — Informacoes complementares no Ranking
Em Todas nos tres eixos, exibir Especialidade e Estilo de Jogo, mantendo a etiqueta de posicao. Posicao especifica tambem mostra ambos; estilo especifico mostra somente Especialidade; especialidade especifica mostra somente Estilo de Jogo. Regra igual em POR CARD, POR JOGADOR e MIX. Removidos os nomes e links de boxes de origem dos cards do Ranking.
RPC site_novo_ranking_v1 recebe campo aditivo estilos (id/nome), lido de carta_playstyle_jogo e playstyle.nome_tela em ordem de slot fisico; a tela apresenta os nomes distintos. Se nao houver nome cadastrado, informa Nao informado. Filtros, selecao, classificacao, notas e permissões existentes preservados. SQL registrado em RANKING-ESTILOS-POR-CARD-1009.sql; migration ranking_incluir_nomes_estilos_por_card.
Validacao: contrato publico com 33 itens; teste de Ranking aprovado; 18 combinacoes de eixo/filtro/modo aprovadas; leitura no navegador confirmou Todas e especialidade especifica sem boxes e sem transbordamento nos tres cards do podio. Advisors consultados: aviso de SECURITY DEFINER publico corresponde ao contrato publico existente; nenhum grant ampliado nesta alteracao.
Publicado no deploy 6aa2356644f065c71e259021, recursos Ranking v2026091008. index.html, ranking.js, ranking-api.js e ranking.css publicos conferidos byte a byte com o pacote.

### 10/09/2026 — Card inteiro abre a Ficha
Cards do Ranking agora sao links nativos completos, com card_id e linha_id preservados, abertura na mesma aba e foco visivel pelo teclado. Removido Ver Ficha. Vale para podio e compactos. Teste Ranking aprovado; arquivos publicos conferidos; clique real em Diego Maradona abriu a Ficha. Recursos Ranking v2026091009, deploy 6aa23c3170fa1764a9338376.
