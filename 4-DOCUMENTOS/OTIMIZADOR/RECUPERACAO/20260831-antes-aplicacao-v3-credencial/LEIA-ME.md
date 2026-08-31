# Snapshot antes da aplicação da fila V3

Criado antes do ajuste de compatibilidade da chave `sb_secret` e da aplicação da migração da fila produtiva V3.

- Este snapshot não contém `config.txt` nem qualquer credencial.
- Restauração local: recupere somente os arquivos correspondentes deste diretório.
- Reversão de banco, caso a V3 seja aplicada: use `4-DOCUMENTOS/OTIMIZADOR/FILA-PRODUCAO-V3/ROLLBACK-FILA-PRODUCAO-V3.sql` somente depois de encerrar/arquivar explicitamente qualquer lote V3 existente.
- A criação ou início da fila não faz parte deste snapshot nem desta etapa de aplicação do schema.
