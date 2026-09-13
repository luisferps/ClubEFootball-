# Manual do Site Novo

Site oficial: https://imaginative-granita-ace1ca.netlify.app/.
Fonte oficial: `Site Novo` nesta pasta de trabalho. O endereço
`extraordinary-twilight-cc1b29.netlify.app` é uma prévia antiga.

## Navegação e apresentação

Início, Ranking, Boxes, Boxes em andamento e Busca usam os contratos públicos do
banco. A Ficha abre por `ficha.html?card=ID`; `linha` pode selecionar uma build.
Uma carta sem resultado completo continua com informação disponível e estado explícito.
Não inventar nota, atributo final ou orçamento para preencher espaços.

No Ranking, POR CARD / POR JOGADOR / MIX ficam no topo e centralizados. Abaixo vêm
Posição / Estilo de jogo / Especialidade. Estilos em ordem alfabética; especialidades
na sequência do campo. Botões de estilos/especialidades têm largura pelo texto.
Busca acima dos resultados, paginação apenas no rodapé. Rótulos vêm do catálogo.
O estilo Básico não aparece como opção de filtro; os demais estilos são preservados.

O filtro de posição usa a posição da linha publicada, antes do agrupamento.
O filtro de estilo exige vínculo à carta e ativação na posição da linha. Não usar
posição nativa ou nome semelhante como substituto. Cartas de estilos defensivos
seguem os contratos específicos de seleção, não uma exclusão inventada na tela.

## Ficha

Preservar os quatro blocos aprovados, seu chassi e a proporção integral da foto,
inclusive durante carregamento ou dados incompletos. Trocar build não recarrega
a página inteira. Posições indisponíveis permanecem bloqueadas.

BASE mostra o atributo de origem; JOGO mostra o valor efetivo do jogo publicado;
FINAL inclui a valorização do sistema. Não confundir efeito interno de habilidade
com aumento efetivo do atributo no jogo. A nota exibida é recebida do banco.

Builds de régua anterior recebem **Régua antiga**. O selo não torna uma linha nova
sem recálculo. Falta de orçamento divulgado recebe **Orçamento ainda não divulgado**
por consulta à fonte automática, sem lista fixa de cartas. Nível 1 comprovado com
orçamento zero é válido. Excluídas não entram como pendências operacionais.

As habilidades complementares usam verde discretamente mais claro e hover
`Complementar`, sem explicação técnica adicional no fluxo normal.

## Editor pessoal

O avaliador consulta o molde mais recente no banco; v6 confirmado em 13/09.
[Conferência e divergência de atributos identificada](PARIDADE-EDITOR-MOLDE-V6.md).

Editar não altera a build canônica. Escolhas pessoais continuam livres dos vetos
estratégicos de sugestão automática. Avaliação usa o servidor; salvar localmente é
possível sem conta, e nuvem usa autenticação. Builds pessoais azuis e canônicas verdes
compartilham a grade; numeração pessoal é permanente e não recicla exclusões.

Para as mesmas entradas e versão, editor e motor devem concordar em atributos,
parcelas e nota: barras, habilidades, técnico, ímpetos, degraus, estilos, corpo/altura,
pé, IA, normalização e arredondamento. Conferir criar/editar/avaliar/salvar/reabrir e
apresentação pública. Corrigir um único exemplo não encerra divergência de contrato.

“Pode melhorar” compara a maior nota pública da mesma carta/especialidade com a nota
avaliada corrente. Até 0,05% mostra 0%; acima, uma casa decimal. Não comparar outra função.

## Banco, publicação e desempenho

A busca normaliza os nomes e o texto digitado, sem exigir acentos, inclusive no
Ranking. Fechar a busca ou digitar novamente invalida respostas anteriores.

`site-common.js` concentra transporte HTTP e utilidades comuns. Consultas têm prazo
limite e cancelamento; gravações não são repetidas automaticamente. O Início exibe
cada seção assim que chega. A Ficha não espera a foto nem as builds pessoais para
mostrar a publicação disponível; avaliações pessoais usam até três consultas juntas.

No editor, somente a resposta da escolha mais recente pode alterar a tela, inclusive
na troca equivalente de habilidade e no catálogo dependente da posição.

Somente portas públicas dedicadas: por exemplo `site_novo_ficha_v2`,
`site_novo_ranking_v1` e avaliador do editor. Não consultar tabelas administrativas
diretamente nem buscar fallback em `clube`. Chave publicável pode estar no cliente;
credenciais administrativas não podem.

Fluxo: contratos/adaptadores → estado → apresentação. JavaScript não recalcula a
nota oficial. A normalização vigente é por amplitude, somando o bônus integral;
as antigas curvas molde 100/teto 110 não são a regra atual.

O selo de régua do Ranking é calculado na página selecionada, não para todo o universo
antes de paginar. [SQL da correção](SQL-RANKING-SELO-PAGINA.sql).
Boxes exibem a melhor linha publicada disponível no grau selecionado. Não inventar avaliação para carta sem publicação elegível.

Nas duas abas de Boxes, cards seguem estrelas de contratação decrescentes e,
no empate, a pontuação exibida decrescente. Sem análise fica depois das categorias
avaliadas. A prévia contém os três primeiros cards da mesma ordem do detalhe;
ordenação ocorre no banco antes de limitar/paginar, inclusive após buscas.
Contrato: `SQL-BOXES-ORDEM-CONTRATACAO.sql`. Regressão:
`tests/boxes-hiring-order.test.cjs` compara prévia e detalhe nos três degraus.

Categorias de contratação: cinco estrelas verde forte sem brilho, quatro verde suave,
três amarelo, duas laranja e uma vermelho. Estrelas vazias têm contorno na cor da categoria; zero mostra cinco contornos vermelhos discretos, sem preenchimento, e legenda apagada. Tema claro adapta o contraste.
A legenda de contratação é texto discreto, sem fundo, borda ou aparência de botão.

Prévias e detalhes compartilham o padrão: foto ampla, nome e número destacados;
posição nativa apenas pela sigla (VOL, MAT), sem etiqueta; estilo cadastral em bloco discreto. Especialidade/build não aparece. Nota, estrelas e clique correspondem à linha de maior pontuação publicada. Contrato vigente: SQL-BOXES-MELHOR-LINHA.sql.

Capitalização em todas as telas: inicial maiúscula nas palavras, artigos e
preposições minúsculos no meio das expressões (Estilo de Jogo). Siglas preservadas.
O apresentador compartilhado formata textos novos incrementalmente, sem alterar
valores de formulários nem dados persistidos.

Boxes em andamento e ordenação por pontuação agregam a fonte materializada para
evitar varreduras ordenadas caras. O selo é consultado nas linhas necessárias.
As consultas corrigidas preservam o resultado público e os critérios de avaliação.

Antes de declarar deploy concluído, conferir arquivos publicados, resposta do contrato
público e interface real. Em 13/09 os arquivos do site foram comparados com a pasta
oficial e a consulta do Ranking foi corrigida no banco. Isso não encerra a auditoria
dos novos resultados que ainda estão sendo processados.

[Pendências atuais](../4-DOCUMENTOS/ESTADO-ATUAL.md) ·
[Integração](../4-DOCUMENTOS/MANUAL-DE-INTERLIGACAO-DE-SISTEMAS.md) ·
[Orçamento](../4-DOCUMENTOS/ORCAMENTO-REGRA-DIARIA.md).

O interior das boxes usa cards verticais nas duas abas: classificação no canto sem reservar uma linha, foto grande, nome, sigla, blocos de identidade e avaliação centralizada abaixo. A grade compacta acomoda cinco cards no desktop, ajustando a quantidade à largura disponível, sem reduzir as fotos.

Nas duas listagens, cada box tem borda externa reforçada e cabeçalho contrastante; divisórias entre jogadores permanecem discretas para destacar o agrupamento da coleção.

Nas duas abas, a análise principal é a linha publicada de maior nota no grau selecionado, com desempate pelo ID da linha. Nota, estrelas e link da ficha correspondem a ela. A tela mostra posição nativa e estilo cadastral, sem especialidade/build. Os cards são ordenados por estrelas e depois pela nota dessa linha. Snapshots históricos permanecem armazenados, mas não são usados para escolher a linha exibida. Contrato: SQL-BOXES-MELHOR-LINHA.sql.
