# Recuperação — contrato de fila do Bonificador

Snapshot local criado antes de instalar `bonificador_contexto_escrita_v2` e
`gravar_build_bonificador_v1` no banco. O estado lido antes da aplicação é registrado
em `PREFLIGHT-ANTES.md`; não há credenciais neste diretório.

Se for necessária reversão, execute somente o rollback composável já revisado:
`4-DOCUMENTOS/BONIFICADOR/SQL/ROLLBACK-ESCRITOR-TRANSACIONAL-BONIFICADOR-V1-COMPOSAVEL.sql`,
em transação explícita, seguido de readback por nova conexão. Esse rollback não toca
fórmula, régua, Otimizador, legado ou lote produtivo.
