# Relatório final — cópia paralela `clube_novo`

Data: 27/08/2026  
Projeto Supabase: `trqqpsnafpbudtvvicch`  
Migração aplicada: `20260827183648_criar_clube_novo_copia_paralela_21_tabelas`

## Resultado

O schema `clube_novo` foi criado como cópia paralela do modelo novo. Nenhuma
tabela foi movida, renomeada ou removida de `clube`. Nenhum motor, rotina, view,
tela ou consumidor foi redirecionado.

`clube_novo` contém exatamente as 21 tabelas do manual e nenhuma outra tabela.
As 21 fontes continuam em `clube` com os mesmos OIDs, contagens e fingerprints
anteriores.

## Manifesto validado

| tabela | linhas em `clube` | linhas em `clube_novo` | status |
|---|---:|---:|---|
| `texto_do_jogo` | 211 | 211 | origem preservada; cópia idêntica |
| `atributo_jogo` | 26 | 26 | origem preservada; cópia idêntica |
| `corpo_ordem` | 15 | 15 | origem preservada; cópia idêntica |
| `pe` | 11 | 11 | origem preservada; cópia idêntica |
| `posicao_jogo` | 13 | 13 | origem preservada; cópia idêntica |
| `playstyle` | 36 | 36 | origem preservada; cópia idêntica |
| `estilo_ia` | 7 | 7 | origem preservada; cópia idêntica |
| `habilidade_jogo` | 72 | 72 | origem preservada; cópia idêntica |
| `impeto_jogo` | 440 | 440 | origem preservada; cópia idêntica |
| `tecnico_jogo` | 0 | 0 | estrutura oficial preservada; continua vazia |
| `carta_jogo` | 42.803 | 42.803 | tabela principal das cartas; cópia idêntica |
| `carta_atributo_jogo` | 0 | 0 | relação oficial criada; continua vazia |
| `carta_corpo_jogo` | 0 | 0 | relação oficial criada; continua vazia |
| `carta_habilidade_jogo` | 0 | 0 | relação oficial criada; continua vazia |
| `carta_estilo_ia_jogo` | 0 | 0 | relação oficial criada; continua vazia |
| `carta_posicao_jogo` | 0 | 0 | relação oficial criada; continua vazia |
| `carta_impeto_jogo` | 0 | 0 | relação oficial criada; continua vazia |
| `impeto_atributo_jogo` | 1.542 | 1.542 | incluída no modelo oficial; cópia idêntica |
| `funcao_sistema` | 19 | 19 | catálogo oficial; RLS/policy e gatilho preservados |
| `funcao_alias` | 14 | 14 | aliases oficiais; FK, identity, generated, RLS/policy preservados |
| `mapa_do_jogo` | 21 | 21 | registro técnico de procedência; cópia idêntica |

## Estrutura e dependências

- 74 constraints na origem e 74 na cópia; zero diferença semântica por nome,
  tipo, colunas, expressão, alvo/regras de FK, deferrability e validação.
- 41 índices na origem e 41 na cópia; zero diferença semântica por nome,
  método, propriedades, itens e predicado.
- 15 FKs em `clube_novo`, todas com origem e destino dentro de `clube_novo`.
- 2 tabelas com RLS e 2 policies em cada schema.
- 3 gatilhos de usuário em cada schema. Na cópia, suas funções permanecem em
  `clube` como dependências externas de transição:
  `clube.tg_cap_do_id()`, `clube.tg_carta_entrou()` e
  `clube.impedir_alteracao_funcao_sistema_id()`.
- Os gatilhos só foram recriados depois da carga; nenhum disparou durante a cópia.
- `clube.insumo_incompleto` continua em `clube`, consultável e sem referência a
  `clube_novo`.

## Consumidores e segurança

As dez rotinas consumidoras continuam lendo apenas `clube`:

1. `clube.fila_da_carta(text)`
2. `clube.montar_fila(boolean)`
3. `clube.posicoes_da_carta(text)`
4. `clube.refresh_jogo_aplicar(boolean)`
5. `public.carta_do_motor(text)`
6. `public.estado_da_fila()`
7. `public.fila_do_motor(integer, integer)`
8. `public.fila_do_motor(integer, text, integer)`
9. `public.peso_da_ordem()`
10. `public.regua_bonus()`

Nenhuma rotina lê `clube_novo`. O schema novo não concede `USAGE` a `anon`,
`authenticated`, `authenticator` ou `service_role`; somente `postgres` tem
`USAGE/CREATE`.

O Security Advisor não apresentou aviso para `clube_novo`. O Performance
Advisor apontou um FK sem índice de cobertura em
`impeto_atributo_jogo.codigo_atributo`, já existente na estrutura de origem, e
marcou índices clonados como ainda não utilizados, o que é esperado porque
nenhum consumidor foi ligado ao novo schema. Nada foi alterado para “corrigir”
esses avisos, preservando a equivalência exigida.

Referências do advisor:

- https://supabase.com/docs/guides/database/database-linter?lint=0001_unindexed_foreign_keys
- https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index

## Gates fail-closed e normalização comprovada

As execuções que detectaram divergências no pós-voo foram revertidas
integralmente. A diferença concreta relevante era apenas a convenção de nomes
usada por `CREATE TABLE ... LIKE`:

| objeto | nome recalculado por `LIKE` | nome canônico preservado |
|---|---|---|
| UNIQUE | `carta_impeto_jogo_card_id_ordem_key` | `carta_impeto_jogo_card_ordem_key` |
| UNIQUE | `funcao_alias_nome_alias_normalizado_key` | `funcao_alias_nome_normalizado_key` |
| PRIMARY KEY | `impeto_jogo_pkey` | `impeto_jogo_pkey1` |
| índice | `carta_habilidade_jogo_card_id_ordem_idx` | `carta_habilidade_jogo_card_ordem_uidx` |
| índice | `carta_jogo_roda_motor_overall_idx` | `carta_jogo_fila` |
| índice | `carta_jogo_lancamento_visto_em_idx` | `carta_jogo_lancamento` |

Antes do commit, cada renomeação exigiu correspondência semântica única. Depois
do commit, a leitura independente confirmou zero diferença entre as assinaturas.

## Rollback

O rollback foi ensaiado dentro de uma transação finalizada com `ROLLBACK`. Ele
remove somente as 21 cópias e o schema `clube_novo`, usa `RESTRICT` e aborta se
detectar FK, view ou rotina externa conectada ao novo schema. O ensaio terminou
com sucesso e a cópia real permaneceu íntegra.

## Arquivos

- Manual canônico: `C:\Users\Luis Fernando\Downloads\Clubefootball V4\4-DOCUMENTOS\MANUAL-DAS-TABELAS.md`
- Pacote permanente: `C:\Users\Luis Fernando\Downloads\Clubefootball V4\4-DOCUMENTOS\SEPARACAO-CLUBE-NOVO`
- Migração: `MIGRACAO-CLUBE-NOVO.sql`
- Rollback: `ROLLBACK-CLUBE-NOVO.sql`
- Validação reproduzível: `VALIDAR-CLUBE-NOVO.sql`

## Próximo limite

`clube_novo` é uma fotografia paralela, não uma réplica contínua. Alterações
futuras em `clube` não são sincronizadas automaticamente. O próximo trabalho
deve mapear cada leitura antiga X para a tabela nova Y e ter autorização própria
antes de alterar qualquer consumidor.
