# Correções técnicas do frontend — 13/09/2026

## Resultado

- Ranking aceita busca sem acento, usando a mesma normalização da busca geral.
  Joao/João, Alvaro/Álvaro e Soares/Soáres retornaram os mesmos IDs e totais.
- Busca fechada não reabre por resposta atrasada; nova digitação cancela a anterior.
- Trocas equivalentes de habilidade e catálogos do editor respeitam a última escolha.
- Início mostra Ranking e Boxes independentemente. Ficha mostra dados públicos antes
  de terminar foto e avaliações pessoais; estas têm concorrência limitada a três.
- Transporte HTTP, configuração pública, escape e validação de fotos compartilhados
  em `site-common.js`. Prazo limite, cancelamento e repetição limitada de leituras;
  gravações não têm repetição automática.
- Removidos helpers sem uso, listener antigo de estilos, ramificação/CSS de paginação
  superior e implementação alternativa do Início no shell.
- “Como funciona” corrigido para a normalização vigente por amplitude.

## Consultas de Boxes

A consulta medida de Boxes em andamento caiu de 15.388,945 ms para 1.683,305 ms
com agregação da fonte materializada. JSON completo antes/depois idêntico na mesma
fotografia de leitura. A ordenação das Boxes cadastradas por pontuação também
estourava o prazo: removida a apuração de selo que não era utilizada nesse caminho
e materializada a fonte das notas; JSON antes/depois idêntico e HTTP público aprovado.

Definições aplicadas: `SQL-RANKING-BUSCA-SEM-ACENTO.sql`,
`SQL-BOXES-SELO-AVALIADAS.sql` e `SQL-BOXES-ORDENACAO-PONTUACAO.sql`.
Não houve mudança de fórmula, população elegível ou fotografia de avaliação.

## Validação

Os 17 arquivos de testes passaram em execuções direcionadas, incluindo contratos
HTTP públicos, três degraus, buscas, paginação, estados, editor, tema e navegação.
`frontend-lifecycle.test.cjs` reproduz fechamento/retorno atrasado, troca equivalente
concorrente, seção independente e limites/repetição do transporte.
Fixtures antigos foram adaptados ao campo de estilos atual; notas mutáveis não são
mais comparadas com um valor histórico fixo. Sintaxe dos 14 JavaScripts aprovada.
Ficha e editor conferidos no navegador; avaliação recebida do servidor.

Pacote público contém somente 20 arquivos HTML/CSS/JS. Manuais e SQL não são enviados
ao site. Otimizador, Bonificador e envios continuam independentes desta manutenção.

Publicado no site oficial, deploy `6aa64673c5c59a15f4dc1e23`. Os 20 arquivos servidos
por HTTP foram comparados por SHA-256 e são idênticos aos fontes locais.
