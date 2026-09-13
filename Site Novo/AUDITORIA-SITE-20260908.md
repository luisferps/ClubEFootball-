# Auditoria do Site Novo — 08/09/2026

## Resultado e publicação

O site foi atualizado no projeto Netlify existente, usando somente os 21 arquivos públicos da pasta oficial Site Novo. Deploy final: `6aa0946c7a2721d1c2966e1f`, publicado às 20:04, horário de Brasília. GitHub não foi atualizado nesta operação. Motores, filas, dados de produção e builds pessoais não foram alterados pela auditoria.

Foram corrigidos dois defeitos do Ranking: envio indevido do estado visual `eixo` ao contrato público e restauração de filtros invisíveis pertencentes a outra aba. A restauração agora mantém somente o filtro da aba selecionada. As referências dos scripts foram versionadas para buscar os arquivos novos. A suíte completa passou: 15 testes, zero falhas; houve também verificação no Chrome local e publicado.

## Prioridades de melhoria

| Prioridade | Constatação | Ação recomendada |
|---|---|---|
| Alta | A Box mostra pontuação máxima do card junto da especialidade e do link de outra análise. Makélélé, card 88045755964130: Box mostra 109,55 / Volante de contenção e abre linha 379892 com 109,45. Na Ficha, 109,55 pertence a Volante de construção. | Apresentar nota, especialidade, etiqueta e destino coerentes com a mesma análise. Caso a maior nota do card seja mantida, identificá-la separadamente. Preservar os critérios de contratação aprovados. |
| Alta | Ficha em largura efetiva de 375 px fragmenta Claude Makélélé e Defensor Participativo em várias linhas; o campo de posições fica muito estreito. | Adaptar a organização interna dos blocos ao celular, preservando a apresentação de desktop aprovada. Nome e estilo devem ficar legíveis sem quebra letra a letra. |
| Média | Início oferece Organizar elenco; o destino declara Ainda não conectado. | Sinalizar Em breve no convite e reduzir a ênfase até existir funcionalidade. Não inventar contrato de Elenco. |
| Média | No celular, as três abas, filtros e paginação do Ranking ocupam quase toda a primeira tela. | Compactar controles e paginação para mostrar resultados mais cedo, preservando os três critérios exclusivos. |
| Média | Como funciona diz que um card aparece várias vezes por especialidade, mas o padrão por card mostra uma entrada. Também diz que o seletor faz o site calcular, embora as notas sejam lidas já publicadas. | Explicar separadamente por card, por jogador e Mix; dizer que o seletor troca os resultados publicados exibidos. |
| Média | Navegação móvel exige rolagem horizontal; parte dos destinos fica fora da primeira tela. | Melhorar a indicação de continuidade ou organizar menu acessível de navegação. |
| Baixa | Não há robots.txt ou sitemap.xml publicados; index tem descrição, mas não metadados sociais específicos. | Planejar descoberta e compartilhamento: domínio próprio, metadados de prévia e estratégia para rotas por fragmento. Não prometer indexação sem verificar os buscadores. |
| Baixa | Resposta HTML tem HTTPS/HSTS, mas não apresentou CSP, X-Content-Type-Options ou política de enquadramento. | Avaliar cabeçalhos compatíveis com Supabase, imagens e integrações antes de habilitar; ausência de cabeçalho isoladamente não comprova exploração. |

## Evidências e cobertura

- Chrome: Início, Ranking, mudança de critério, Boxes em andamento e detalhe, Ficha vinculada, busca global Messi e abertura dos 59 resultados, Como funciona, Elenco e alternância de tema. Revisão de tela pequena com largura efetiva medida em 375 px; Início e Ranking mantiveram conteúdo legível, com ressalvas de densidade. Na Ficha avaliada não havia imagens quebradas.
- Ranking após correção exibiu 3.864 cards publicados na consulta geral. Esse total é um retrato da consulta e pode mudar com a operação dos motores.
- Testes: contratos públicos, busca, paginação, estado/restauração, resposta fora de ordem, erros, degraus, editor, tema e shell. Boxes consultadas: 1.022 cadastradas; 11 em andamento com 109 relações de cards. Ausência de análise apareceu explicitamente, sem nota inventada.
- Causa da divergência Box/Ficha em `boxes.js`, função `card`: identidade e destino vêm de `analises[0]`; nota usa `pontuacao_maxima`. O dado da Ficha confirma que as notas pertencem a especialidades diferentes. A auditoria registrou o defeito; não alterou o critério comercial nem dados para escondê-lo.
- Pacote contém HTML, JS, CSS e SVG públicos. Os dois manuais consultados por URL responderam 404. Não foram enviados SQL, manuais, motores ou credenciais privadas no pacote.
- Netlify reescreve links de `index.html#...` para `/#...` em ficha.html. Por isso esse HTML não é idêntico byte a byte; a diferença completa foi registrada em DIFF-FICHA-NETLIFY.txt. Os demais arquivos foram comparados por conteúdo.

## Limites

Auditoria funcional e visual com leitura de código e testes automatizados. Não é certificação WCAG, teste de invasão, medição de Core Web Vitals ou auditoria exaustiva de todas as cartas. Não foram medidos contraste de cada cor, todos os tamanhos de tela nem sessões autenticadas. As melhorias acima permanecem propostas, exceto as duas correções do Ranking já entregues. O painel escuro da Ficha é uma decisão visual previamente documentada, não foi repaletizado.
