# Manifesto do snapshot anterior

- origem: `2-MOTORES/motor_bonus.py`
- cópia: `motor_bonus.py`
- SHA-256 origem: `AA7840998FEF77B5ABECF706456FCB8DF7AD6DCD20C85AEA7372A6AE9C4015E5`
- SHA-256 cópia: `AA7840998FEF77B5ABECF706456FCB8DF7AD6DCD20C85AEA7372A6AE9C4015E5`
- comparação: idêntica
- banco antes: `bonificador_regua_v1`, `bonificador_carta_v1` e
  `bonificador_pares_v1` não existiam
- recuperação do runtime: restaurar esta cópia no caminho de origem
- recuperação do banco: executar `SQL/ROLLBACK-CONTRATOS-BONIFICADOR-V1.sql`
- runtime pós-migração SHA-256:
  `D86937340FDAE579C466F09A61446115B0A3B0188C2DAFFDF340C9DBA5F9E119`
- patch `mudancas.patch` SHA-256:
  `641C32ACC01525D238CA2425154A0343678FB05D60054E0CB2F1FD50346BA386`

O snapshot não contém chave, `config.txt`, dado produtivo ou cópia operacional do
projeto.
