# Snapshot anterior ao consumo de `funcao_id`

- Escopo: somente a chave operacional de função no Bonificador.
- Fotografia recuperável das RPCs em `clube_novo.bonificador_migracao_snapshot_v2`.
- Recuperação: `SQL/ROLLBACK-CHAVES-FUNCAO-ID-CANONICO-V1.sql`.
- O rollback foi ensaiado integralmente com `ROLLBACK` após a aplicação, sem
  persistir a recuperação.
- A alteração substitui chave textual por `funcao_sistema.id`; não muda direção,
  peso, cortes, ordem, composição ou fórmula.
