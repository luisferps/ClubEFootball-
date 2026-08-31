# Pré-voo e readback — fila produtiva V3

Estado atual: **infraestrutura V3 aplicada e piloto limitado concluído**. O
lote `100635db-56d9-4297-b22c-6cde52bf81c8` contém 3 cartas e 45 linhas; todas
foram concluídas, sem pendências ou bloqueios.
Não há publicação nem execução do Bonificador.

## Pré-voo concluído

1. A credencial atual do backend respondeu HTTP 200 a `otimizador_regua_v2` e
   `otimizador_carta_v3(8538111)`. Chave moderna `sb_*` segue somente no
   cabeçalho `apikey`; ela nunca é enviada ao navegador.
2. O snapshot adicional foi preservado em
   `../RECUPERACAO/20260831-antes-aplicacao-v3-credencial/`, com manifesto
   SHA-256 conferido antes do DDL.
3. Não havia tabela, função ou lote V3 anterior.
4. O selo de fórmula foi confirmado sem mudança:
   `7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad`.

## Aplicação e readback concluídos

As migrações registradas no Supabase foram:

- `20260831133727_otimizador_fila_producao_v3`;
- `20260831134002_otimizador_fila_producao_v3_indices_v2`;
- `20260831135509_otimizador_fila_producao_v3_piloto_limitado_v1`;
- `20260831135747_otimizador_fila_producao_v3_piloto_janela_v2`;
- `20260831135839_otimizador_fila_producao_v3_piloto_lote_id_v3`;
- `20260831140053_otimizador_fila_producao_v3_conclusao_identity_v4`;
- `20260831140146_otimizador_fila_producao_v3_conclusao_identity_v4`.

A segunda entrada V4 é a mesma substituição idempotente de função (`CREATE OR
REPLACE`); ela não executou linha, não duplicou build e não alterou fórmula.

O readback comprovou, antes de qualquer clique de início:

- quatro tabelas V3 existentes em `clube_novo`, com RLS e sem `SELECT` direto
  para `anon` ou `authenticated`;
- todas as RPCs `otimizador_producao_*_v3` existentes, com `SECURITY DEFINER`
  e `search_path` vazio; `anon` e `authenticated` não executam nenhuma e
  `service_role` executa todas;
- `otimizador_producao_status_v3()` retornando `sem_lote`,
  `pode_publicar=false` e ação `criar=true`;
- a interface V23 em loopback (`127.0.0.1`, porta temporária 8768) recebendo
  esse estado, sem credencial no browser; o servidor de teste foi encerrado;
- zero lotes e zero linhas V3; nenhum resultado do Otimizador, Bonificador ou
  publicação foi criado.

O advisor de segurança lista RLS sem política nas quatro tabelas novas como
informação esperada: elas têm acesso direto revogado e são acessadas apenas pelas
RPCs privadas concedidas a `service_role`. Os três índices de cobertura de FKs
foram acrescentados; restam apenas avisos de índice ainda não usado, esperados
enquanto não existe lote.

## Piloto limitado executado e readback

O piloto foi autorizado com limite de 3 cartas. A V3.1 limitou a consulta antes
das projeções apenas no caminho de piloto; V3.2 reduziu a janela a cinco
candidatas para três cartas; V3.3 corrigiu o endereço do lote gravado nas
linhas. Esses ajustes não mudam fórmula, pesos, régua ou seleção da fila
integral (`p_limite_cards=0`).

A primeira conclusão revelou que `build_otimizador.id` é `GENERATED ALWAYS AS
IDENTITY`: a função inicial tentava informar `nextval(...)`. V3.4 removeu
somente essa PK do `INSERT`; o banco passou a gerar o ID. A definição física
foi relida: não contém `nextval`, omite `id` e preserva a validação dos selos.

Readback das 45 linhas concluídas:

- cartão/entrada atual é idêntico ao snapshot selado;
- a primeira pontuação persistida foi `-52,1`, com 11 builds comparadas e 39
  possíveis; todas as 45 concluíram sem bloqueio e tiveram os selos persistidos
  conferidos;
- um segundo cálculo local conferiu barras, técnico, habilidades, Ímpeto e
  contadores em uma linha representativa de cada uma das três cartas;
- fórmula, contrato, carta e resultado conferem pelos fingerprints;
- `publicada_em` é nulo, `pode_publicar=false`, Bonificador permanece pendente
  e os 1.169 cartões com Ímpeto condicional continuam excluídos.

Após a autorização para cobertura transversal, foram executadas exatamente mais
22 linhas: as 12 pendentes da primeira carta, as 9 da segunda e a primeira da
terceira. A autorização seguinte concluiu as 17 restantes. O contrato devolve
`concluido`, 45 concluídas, 0 pendentes, 0 processando e 0 bloqueadas. Todas
aguardam o Bonificador como etapa separada; `pode_publicar` continua `false`.

## Próxima autorização: ampliar a execução

O lote completo não está liberado por este piloto. Antes de ampliar a execução,
é necessária decisão explícita após a paridade independente das entradas e dos
resultados. O piloto já está encerrado; criar uma fila integral formaria todas
as cartas aptas, em ordem de overall decrescente.
Em ambos os casos, Ímpetos condicionais continuam fora, Bonificador é passo
manual separado e não há publicação nesta cadeia.

## Recuperação

O snapshot anterior ao piloto é
`../RECUPERACAO/20260831-antes-piloto-limitado-v3/`. Como já existe lote V3,
`ROLLBACK-FILA-PRODUCAO-V3.sql` recusa remoção para preservar histórico. Os
rollbacks V3.1 a V3.4 são artefatos de recuperação técnica; não devem ser
aplicados sobre este lote sem decisão explícita de retenção/arquivamento e
readback.

## Preparação integral V5 — pré-voo e readback em 31/08/2026

A V5 foi desenhada para substituir somente a montagem integral insegura da V3.
Ela não toca em `equacao.py`, pesos, moldes ou qualquer cálculo. A fotografia
inicial é somente de candidatas elegíveis sem Ímpeto condicional; as projeções dos
contratos de carta e as linhas canônicas entram em fatias de no máximo 20, com a UI
usando 10 por chamada.

O banco mediu **19.363 candidatas básicas** e **1.169 cartas excluídas por Ímpeto
condicional**. O lote-piloto concluído permanece intocado. O readback V5 confirmou
DDL, RLS, grants, FKs e RPCs; a candidata integral não aceita leitura/gravação
direta de `anon`, `authenticated` ou `service_role`, e as RPCs privadas só executam
pelo backend local. O pré-voo devolveu fórmula aprovada e `pode_publicar=false`.

O ensaio recuperável criou uma rodada integral dentro de transação, preparou uma
única candidata e suas 18 linhas, e fez rollback. O readback posterior confirmou
zero candidatas integrais persistidas e preservou o piloto (3 cartas, 45 linhas,
45 concluídas). O loopback V24 recebeu status, paginação, Resultados e Eventos da
V5; o executável verificou a mesma versão sem abrir browser nem iniciar lote. A
criação, o preparo e o cálculo reais da fila integral continuam ações explícitas do
operador.
