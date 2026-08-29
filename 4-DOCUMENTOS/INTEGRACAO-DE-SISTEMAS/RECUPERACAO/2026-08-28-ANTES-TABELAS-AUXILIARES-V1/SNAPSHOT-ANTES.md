# Snapshot antes das tabelas auxiliares de integração v1

Data: 2026-08-28

Este snapshot registra o estado lido no banco antes de qualquer DDL desta frente.

## Objetos comprovados

- `clube_novo.carta_jogo`: tabela canônica de cartas; PK `card_id text`; 43.072 linhas.
- `clube_novo.funcao_sistema`: catálogo canônico de funções; PK `id bigint`.
- `clube_novo.contrato_leitura_jogo`: contrato versionado do Extrator; PK `contrato_id text`.
- `clube_novo.bonificador_par`: projeção privada `card_id text + funcao_id bigint`; 0 linhas.
- `clube.build`: saída histórica vazia; PK textual `(card_id, funcao_codigo)` e FK para `clube.funcao(codigo)`.
- `public.builds`: estrutura histórica com 17.798 linhas; PK textual `(card_id, funcao, motor_versao)` e FK textual para `public.funcoes(nome)`.
- `public.builds_bruto`: estrutura histórica vazia; PK `(card_id, build_id)`.
- `public.builds_vigente` e `public.builds_atrasadas`: views sobre `public.builds`.

## Ausências comprovadas

- nenhum objeto cujo nome contenha `build` existe em `clube_novo`;
- não existe Build nova canônica com PK numérica/imutável no esquema novo;
- não existe FK entre uma Build nova e `clube_novo.carta_jogo`;
- não existe junção Build-Carta canônica;
- não existe fingerprint integral da carta materializado em `carta_jogo`; o campo `hash_player_bin_vinculos` cobre somente a fotografia física de vínculos correspondente ao seu contrato.

## Consequência

A migração desta frente pode criar apenas a área intermediária independente por carta, função e versão. Não pode criar a junção Build-Carta nem o publicador final até que a Build nova e sua PK sejam definidas por uma etapa própria.

Nenhum dado existente foi copiado, alterado ou excluído para produzir este snapshot.
