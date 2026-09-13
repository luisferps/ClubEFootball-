# Ranking — prévia visual para discussão

> Registro histórico da prévia. A conexão atual está documentada em RANKING-CONTRATO-E-ENTREGA.md.

06/09/2026. Etapa autorizada: mesmo procedimento do esqueleto. Reproduzir o visual legado no Site Novo para debater melhorias; sem importar programação, funções, fórmulas, consultas ou dependências antigas.

## Abrir

Abra `Site Novo/index.html` e clique em Ranking. O abridor `outputs/ABRIR-RANKING.cmd` aponta diretamente para `index.html#ranking` no checkout operacional. A Home e o cabeçalho aprovados permanecem com seu desenho anterior.

## Nesta versão

- Faixa de setores Geral, Goleiro, Defesa, Meio e Ataque.
- Faixa de funções e modos visuais conforme os rótulos da referência legada.
- Seleção visual com realce verde; conserva a escolha enquanto a página local estiver aberta.
- Busca contextual desativada e botão Filtros com abertura, fechamento e Escape.
- Filtros por estilo de jogo, posição nativa e função desativados e identificados como aguardando catálogo.
- Três molduras largas de pódio, ouro/prata/bronze, e seis molduras compactas abaixo; são espaços reservados, não uma classificação real.
- Adaptação móvel e uso dos temas claro/escuro já existentes no shell.

Não há jogadores, fotos, notas, quantidade de resultados ou resultados inventados. Os travessões representam ausência de nota. Os números 1º, 2º e 3º identificam somente os espaços visuais do pódio. Os nomes e agrupamentos de funções são rótulos desta prévia, não catálogo operacional nem filtros de uma consulta.

## Referência consultada somente para apresentação

`1-SISTEMA/clubefut.css`: faixa `#mline`/`.rksetores`/`.rkfuncoes`/`.rktools`, regras finais do pódio e grade (seções próximas às linhas 3650, 3691, 3770, 3805 e 3900).

`1-SISTEMA/motor-e-ficha-base.js`: leitura dos rótulos exibidos na faixa do Ranking. Nenhum código desse arquivo foi copiado, importado ou executado no Site Novo.

## Implementação própria

`ranking.js` controla exclusivamente a seleção visual e abertura dos filtros. Sua interface é `window.SiteNovoRanking.mount(root)` / `unmount()`, responsável por remover os próprios eventos ao trocar de página. Não lê nem escreve dados externos.

`ranking.css` contém apenas estilos `.nr-*`, com os tokens do shell. `index.html` carrega esses dois arquivos locais antes de `site-shell.js`. A rota `#ranking` monta o módulo; as demais rotas continuam no shell. Os arquivos e documentos da Ficha não foram alterados.

## Validação

- Sintaxe de `ranking.js` e `site-shell.js`: passou.
- `tests/ranking.test.cjs`: passou; valida seleção dos cinco setores, funções, filtros, Escape, foco, índices inválidos, remontagem e remoção dos eventos.
- `tests/site-shell.test.cjs`: passou; sete rotas e links locais permanecem válidos.
- Sem acesso a rede, banco, motores ou armazenamento pelo módulo de Ranking.

Não houve teste de interação no navegador ou comparação de screenshots. Esta é uma prévia visual de código verificado, para a conferência e discussão solicitadas pelo usuário. Conexão de dados, classificação, busca e filtros reais são etapas futuras.

