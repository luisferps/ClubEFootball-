# Snapshot anterior — promoção pública do Bonificador V1

Data: 02/09/2026.

Preflight independente:

- 613 candidatas, 613 linhas distintas e 50 cartas;
- 613 com resultado do Otimizador e Bonificador, score final e selo final;
- 0 sem selo/paridade, 0 já publicadas;
- 613 com `lote_teste_id` e marcador `teste_nao_publicado`.

A migração criou o snapshot privado
`clube_novo.bonificador_promocao_publicacao_snapshot_v1` dentro da mesma transação.
Ele conserva o estado anterior de cada linha e permite rollback exato, sem apagar
IDs, resultados, regras ou proveniência.

Recuperação: `SQL/ROLLBACK-PROMOCAO-PUBLICA-BONIFICADOR-V1.sql`.

Nota de segurança da aplicação: a primeira tentativa transacional foi recusada pelo
check físico de `execucao_tipo`; ele permite somente `producao` ou `teste_isolado`.
A transação inteira foi revertida automaticamente, inclusive sem criar o snapshot.
A promoção final usa o valor canônico `producao`, conserva o valor anterior no
snapshot de auditoria e acrescenta somente o lote privado de proveniência
`clube_novo.bonificador_lote_publicacao_v1`, sem ampliar a lista permitida pelo
banco nem reutilizar um lote do Otimizador.

Resultado aplicado e conferido em nova conexão: 613/613 linhas promovidas e
publicadas; 0 excluídas; 0 diferenças de ID, selo ou paridade da pontuação final
entre snapshot, `clube_novo.build_pontuacao_final_v1` e as duas páginas da RPC
`public.frontend_build_publicada_v1`.
