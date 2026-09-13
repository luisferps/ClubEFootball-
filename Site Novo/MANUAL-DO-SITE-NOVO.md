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

## Grau global

O grau 1, 2 ou 3 do cabeçalho controla todas as visualizações e valores derivados:
Ranking, Boxes nas duas abas, Ficha, notas, referências de estrelas, ordenações e
consulta de builds pessoais. Consultas e caches são separados por grau; respostas
atrasadas não podem substituir a seleção atual, inclusive em trocas rápidas.

Links de Ficha não alteram o grau global. A consulta recebe o grau explicitamente.
Se não houver publicação elegível, mostrar os dados nativos e **Análise Ainda Não
Publicada**, sem nota ou estrelas de outro grau. Linhas não condicionais seguem a
elegibilidade do contrato, sem inventar equivalência entre linhas condicionais.

Builds pessoais são reavaliadas para consulta no grau global sem alterar o registro
salvo. Somente o editor pessoal permite mudar o grau local do rascunho; ao mudar o
cabeçalho, o editor acompanha a nova seleção e invalida o resultado anterior.

## Boxes: leitura pronta e atualização automática

As duas abas consultam `clube_novo.boxes_leitura_pronta_v1`, que mantém as ordens
Melhores/Últimas e os cards ordenados separadamente nos graus 1, 2 e 3. Melhores
compara quantidades de cinco estrelas, depois quatro, três, duas e uma; empata
pela maior nota e nome. As referências de estrelas pertencem ao mesmo grau.

Publicação de notas, mudanças de boxes, dados nativos e réguas invalidam a leitura.
O job `boxes_leitura_pronta_v1` verifica a revisão a cada minuto e atualiza apenas
quando necessário. Uma nova nota máxima recalcula a classificação inteira, inclusive
estrelas das demais cartas. A troca é atômica e não bloqueia a consulta da versão
anterior. A revisão aplicada só avança após sucesso; falhas ficam registradas no cron
e a revisão pendente é tentada no próximo ciclo. Há uma pequena defasagem até esse ciclo.

A consulta do visitante não recalcula estrelas nem ordena todos os cards. Ela lê a
ordem pronta, recorta 24 boxes e retorna somente três cards de prévia por box. Ao
abrir a box, retorna só a página de cards pedida. Fotos usam carregamento sob demanda.
Depois de exibir a página, o navegador antecipa apenas a próxima, com validade de
30 segundos; mudança de grau, busca, ordenação ou saída cancela o trabalho anterior.
Nenhuma página de outro grau serve como substituta. Sem análise: Análise Ainda Não Publicada.

Manutenção: [estrutura, invalidação e job](SQL-BOXES-LEITURA-PRONTA.sql).
Mudança de código SQL que altere regras de seleção/classificação também deve marcar
`boxes_leitura_revisao_v1.solicitada` e executar `boxes_leitura_atualizar_v1()` após
implantar. Essa é uma tarefa de migração, nunca do operador diário.

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

“Pode melhorar” compara a maior nota pública da mesma carta/especialidade e do mesmo grau com a nota
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
## Identidade e apresentação das Boxes

Nas duas abas, prévia e detalhe mostram foto ampla, nome e número destacados,
posição nativa somente pela sigla e Estilo de Jogo cadastral em bloco discreto.
Especialidade/build não aparece. Nota, estrelas e clique na Ficha usam a mesma
linha publicada de maior nota elegível no grau selecionado; empate pelo ID da linha.
Fotografias históricas permanecem como prova, sem escolher a análise atual.

Cards seguem estrelas decrescentes, depois nota decrescente e identidade estável.
Sem análise fica depois dos avaliados. A prévia contém os três primeiros cards
nessa mesma ordem; seleção e ordenação precedem a paginação.

Cinco estrelas usam verde forte sem brilho; quatro, verde suave; três, amarelo;
duas, laranja; uma, vermelho. Contornos seguem a cor da categoria. Zero mostra
cinco contornos vermelhos discretos, sem preenchimento, com legenda apagada.
A legenda é texto discreto, sem aparência de botão. Não exibir “Veja o Significado
das Estrelas” nem a informação redundante “Maior Pontuação” no cabeçalho da box.

Blocos equivalentes têm dimensões iguais, mesmo sem análise ou foto. Reservar o
espaço necessário e alinhar avaliação e botão. O interior usa grade compacta de
cinco cards no desktop, responsiva, preservando a foto. Bordas externas reforçadas
e cabeçalhos contrastantes distinguem as boxes; divisórias internas são discretas.

Capitalização em todas as telas: inicial maiúscula nas palavras, artigos e
preposições minúsculos no meio das expressões (Estilo de Jogo). Siglas preservadas.
O apresentador compartilhado formata textos novos incrementalmente, sem alterar
valores de formulários nem dados persistidos.

## Manutenção e validação

A classificação é centralizada em `site_novo_boxes_classificacao_v1`.
[Seleção da melhor linha](SQL-BOXES-MELHOR-LINHA.sql) e
[leitura pronta](SQL-BOXES-LEITURA-PRONTA.sql) são os contratos atuais.
`pontuacao` permanece apenas como identificador compatível da opção Melhores na API.
O desempate entre boxes considera maior nota e nome após as quantidades de estrelas;
contam todos os cards distintos, não somente os três da prévia.

O Ranking calcula o selo e agrupa posições nas linhas da página. O índice de
cobertura e a consulta otimizada estão em `SQL-DESEMPENHO-RANKING-BOXES.sql`.
O prazo das RPCs de Boxes é de dez segundos; aumentar timeout não substitui a
leitura pronta e a paginação. Latência depende da carga e não é garantida.

Antes de concluir publicação, conferir arquivos servidos, contrato público e tela.
Testes de referência: `tests/grau-global-regressao.test.cjs`,
`tests/boxes-hiring-order.test.cjs` e `tests/boxes-prefetch.test.cjs`.
[Conferências realizadas](CONFERENCIA-SITE-1309.md).

[Pendências atuais](../4-DOCUMENTOS/ESTADO-ATUAL.md) ·
[Integração](../4-DOCUMENTOS/MANUAL-DE-INTERLIGACAO-DE-SISTEMAS.md) ·
[Orçamento](../4-DOCUMENTOS/ORCAMENTO-REGRA-DIARIA.md).
