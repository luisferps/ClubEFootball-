# Esqueleto do Site Novo — entrega local

Data: 06/09/2026.

## Abrir

Na pasta operacional `Site Novo`, dê dois cliques em `ABRIR-SITE-NOVO.cmd` ou `index.html`. Não precisa instalar nada nem iniciar servidor. O abridor entregue em `outputs` aponta para essa mesma pasta, sem cópia do site.

## Entregue

- Cabeçalho compartilhado com marca CLUB/e/FOOTBALL, abas agrupadas, entrada da busca e alternância claro/escuro.
- Home com destaque dourado de builds, bloco de elenco verde e Ranking/Boxes lado a lado, conforme o legado.
- Rotas locais `#inicio`, `#elenco`, `#ranking`, `#boxes`, `#busca`, `#ficha`, `#como-funciona`.
- Estados explícitos de módulos não conectados. Não há card fictício, nota, barra de pontuação, ranking ou resultado simulado.
- Navegação por links, URL, Voltar/Avançar; foco após navegação; link para pular ao conteúdo; resposta para endereço desconhecido.
- Ficha em aba separada por formulário com ID real do card e linha opcional.

## Referências visuais conferidas

1. Legado operacional: `1-SISTEMA/clubefut.css`, regras `#t6bar`, `#t6logo`, `#t6tabs`, `.t6tab` e Home `.t6home2`/`.t6h-hero`/`.t6h-elenco`/`.t6h-free`.
2. Cópia preservada em Downloads: `SITE-ATUAL-EXATO-2026-08-24/clubefut.css`.
3. As oito regras acima coincidem entre as fontes depois de normalizar quebras de linha CRLF/LF. O markup da Home operacional foi consultado em `1-SISTEMA/paginas-e-navegacao.js`, somente como referência visual.
4. A tarefa “Desenvolver design do Site Novo” confirmou as fronteiras da Ficha; não declarou uma aprovação anterior específica da Home. A reprodução visual segue a instrução direta do usuário nesta tarefa e o confronto das duas fontes.

O shell reexpressa a apresentação em classes `sn-`, sem carregar arquivos do legado. Mantém fonte Calibri, faixa desktop de 56px, abas arredondadas, cores, gradientes, proporções e ordem da Home. Texto que afirmava estatísticas ou superioridade de resultados foi substituído por estados honestos. Os espaços de card, build, elenco e amostras mantêm área reservada, sem preencher dados. As páginas internas são pontos de entrada com visão geral e estado não conectado; a implementação visual completa de cada módulo continua pendente.

## Arquivos próprios

- `index.html`: documento de entrada e cabeçalho/rodapé compartilhados.
- `site-shell.css`: identidade visual, Home, estados e responsividade.
- `site-shell.js`: único controlador das rotas do shell e tema da sessão.
- `ABRIR-SITE-NOVO.cmd`: abertura local, sem servidor.
- `tests/site-shell.test.cjs`: verificação independente das rotas e fronteiras.
- `ESQUELETO-NAVEGACAO-ENTREGA.md`: este registro, separado dos documentos da Ficha.

## Ponto de integração da Ficha

Destino atual: `ficha.html?card=<id>` ou `ficha.html?card=<id>&linha=<id>`.

O formulário usa GET nativo, abre uma aba separada e omite `linha` quando vazia. IDs permanecem strings decimais, sem conversão a Number ou perda de precisão. Exige ID de card positivo, permite linha positiva opcional. A Ficha permanece responsável por validar existência, relação card/linha e dados publicados. Não embutir via iframe nem importar seus scripts no shell. A Ficha não é carregada automaticamente ao abrir o site.

Futuras listas que conheçam uma build deverão transportar sua linha; listas apenas de cards enviam só o card. O shell não escolhe nem calcula uma build. O usuário fecha a aba da Ficha para continuar no site.

## Fronteiras

Não foram editados `ficha.html`, `ficha.css`, `ficha.js`, `ficha-editor.js`, `ficha-editor-api.js`, testes/documentos da Ficha ou `2-MOTORES/EDITOR-BUILD`. Não foram importadas funções, motores, consultas ou contratos antigos. Não há acesso ao banco, filas ou processos operacionais no shell. Nenhuma publicação na internet, commit ou push foi realizado.

## Verificação

- `node --check site-shell.js`: passou.
- `node tests/site-shell.test.cjs`: passou. Cobre sete rotas, links locais, estado ativo de abas, foco, tema claro/escuro, rota desconhecida sem injeção, ausência de rede e entrada da Ficha com IDs grandes e linha opcional.
- Referências de CSS/JS em `index.html` existem no diretório operacional.
- Conferência das regras visuais com as duas fontes acima.

Não houve teste de interação em navegador nem comparação de captura de tela. Os testes são de código, estrutura e contrato de navegação; a conferência visual do usuário deve ser feita abrindo o site. O conteúdo público e o editor da Ficha são mantidos e validados pela tarefa responsável pela Ficha.
