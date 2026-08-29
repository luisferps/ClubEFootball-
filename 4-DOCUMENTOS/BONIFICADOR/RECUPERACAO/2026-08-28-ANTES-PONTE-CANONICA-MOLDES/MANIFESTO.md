# Snapshot anterior à ponte canônica dos moldes

- data: 28/08/2026
- escopo: somente referência externa dos moldes corporais
- SHA-256 do runtime: `D86937340FDAE579C466F09A61446115B0A3B0188C2DAFFDF340C9DBA5F9E119`
- fórmula do runtime: não será alterada
- função fotografada: `public.bonificador_regua_v1()`
- MD5 da definição no banco: `43d03e9995d41d46e2518d9cffde2012`
- baseline: 19 códigos usados, 17.798 referências e zero chaves técnicas resolvidas diretamente
- recuperação do runtime: restaurar `motor_bonus.py` deste diretório
- recuperação do banco: executar `SQL/ROLLBACK-PONTE-CANONICA-MOLDES-V1.sql`

O snapshot não contém chave, configuração, dado produtivo nem cópia operacional paralela.

## Readback da aplicação

- migration `20260828100000 bonificador_ponte_canonica_moldes_v1`;
- migration `20260828100222 bonificador_ponte_indices_corpo_v1`;
- MD5 final de `bonificador_regua_v1()`: `7417e765fc8b236b16f3b73e2e622300`;
- rollback específico executado dentro de transação e encerrado com `ROLLBACK`;
- após o ensaio, a definição final continuou com o mesmo MD5;
- trava matemática: runtime SHA-256
  `D86937340FDAE579C466F09A61446115B0A3B0188C2DAFFDF340C9DBA5F9E119`;
- AST matemático SHA-256
  `6f0bdcf30547f6a3981f891e78a85ea7238adba4aaf6056195e10ce29d08c731`.
