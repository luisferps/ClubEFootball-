# Snapshot anterior — contrato final de pontuação V1

Data: 01/09/2026.

Preflight independente no banco canônico:

- `clube_novo.build_pontuacao_final_v1`: inexistente;
- `public.frontend_build_publicada_v1`: inexistente;
- linhas com ambos os resultados: 613;
- linhas já publicadas: 0;
- linhas de teste bloqueadas: 613.

Consequência: a implantação não pode transformar o lote de teste em publicação. O
contrato novo deve classificá-lo como `bloqueada_lote_de_teste` e a RPC pública deve
retornar zero linhas até uma publicação explícita e válida.

Recuperação: executar `4-DOCUMENTOS/BONIFICADOR/SQL/ROLLBACK-CONTRATO-PONTUACAO-FINAL-V1.sql`.
O rollback remove somente a view e a RPC criadas por esta mudança; não remove,
recalcula ou publica `build_linha_card`, `build_otimizador` ou `build_bonificador`.
