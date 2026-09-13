# Conferência do site publicado — 13/09/2026

Site oficial: https://imaginative-granita-ace1ca.netlify.app/

Os 19 arquivos HTML, CSS e JavaScript publicados foram comparados byte a byte
com a pasta oficial: todos iguais. Não foi necessário novo deploy de frontend.
O endereço extraordinary-twilight-cc1b29 é uma prévia histórica citada no manual.

## Falha encontrada e corrigida

Ranking retornava HTTP 500, SQLSTATE 57014, timeout de 5 segundos.
O plano consultava build_otimizador para cerca de 40 mil linhas antes da paginação.
A migração ranking_selo_regua_somente_pagina calcula regua_vigente apenas para
os itens da página. Filtros, notas, ordenação e contrato JSON preservados.
SQL reproduzível: SQL-RANKING-SELO-PAGINA.sql. Estatísticas da tabela
regua_vigente_v1 também atualizadas via ANALYZE.

Comparação integral do JSON anterior e novo no mesmo ensaio transacional passou
(por card, degrau 1, 20 itens). A definição original foi restaurada ao final
do ensaio e a correção foi aplicada pela migração oficial em seguida.
HTTP público após correção: por card/degrau 1 em 2,27 s; por jogador/degrau 2
em 1,37 s; mix/degrau 3 em 1,39 s. Todos retornaram pronto.

## Tela conferida

Ranking carregou 4.503 resultados no degrau 1. Pirlo 88039581945312 aparece
com 113,39 e Régua antiga. Sua Ficha repete a nota e o selo e mostra BASE,
JOGO e FINAL. Boxes carregou 1.022 boxes/6.698 cards e os selos antigos.
O selo vigente no banco corresponde ao molde v6, contrato
19125a2b7ac906a702198266f051f2039df75c4658555f9b76fcba07d93623ec.

Esta conferência valida a disponibilidade e a apresentação atual. Não declara
concluído o recálculo integral nem a publicação dos resultados da Máquina 2.
As primeiras publicações v6 ainda precisam de conferência de ponta a ponta
quando chegarem; não é necessário esperar a fila inteira terminar.
Nenhum processo de Bonificador ou Otimizador foi interrompido.

Busca por Pirlo conferida: 11 resultados, nota 113,39 e selo antigo coincidentes com Ranking e Ficha.
