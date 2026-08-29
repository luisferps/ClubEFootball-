# Snapshot anterior à régua canônica do Bonificador

- Escopo: somente as três RPCs do Bonificador e suas fontes de leitura.
- `bonificador_regua_v1()` MD5: `7417e765fc8b236b16f3b73e2e622300`.
- `bonificador_carta_v1(text)` MD5: `3717c3aa73d87ee3ff9e4fb659b05363`.
- `bonificador_pares_v1(integer,integer)` MD5: `3b4b8ca05ac16d99a9cfbe424c29ab7b`.
- Runtime `2-MOTORES/motor_bonus.py` SHA-256: `d86937340fdae579c466f09a61446115b0a3b0188c2daffdf340c9dba5f9e119`.
- Baseline: Casillas `88045755827028` bloqueado somente pelo gate histórico do
  playstyle 291; os demais campos normalizados já estavam completos.
- O script de migração persiste as três definições e os payloads de baseline em
  `clube_novo.bonificador_migracao_snapshot_v1`; o rollback local usa esse snapshot.
- Ensaio completo em transação com `ROLLBACK`: aprovado antes da aplicação.
