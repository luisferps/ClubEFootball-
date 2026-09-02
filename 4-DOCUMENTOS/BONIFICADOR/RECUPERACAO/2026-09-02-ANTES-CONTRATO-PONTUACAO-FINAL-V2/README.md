# Snapshot anterior ao contrato de pontuação final V2

Data da prova: 2026-09-02.

Escopo preservado:

- 613 linhas V1 já publicadas;
- 50 cartas;
- 345 pares carta/função;
- fingerprint da fórmula: 7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad;
- fingerprint da régua V2: 07a79d1a28baa112010f66ed339d684a3536680078e6786d8229650f5b8c7bfd;
- 613 resultados brutos reproduzidos exatamente, sem divergência.

builds-publicadas-v1-snapshot.json contém a entrada selada anterior à V2.
builds-normalizadas-v2.json contém a recomposição controlada usada no
backfill. relatorio-recomputacao-v2.json contém o resumo da prova.

O rollback não restaura estes arquivos no banco automaticamente: ele apenas
remove os objetos V2, preservando integralmente a V1 e os resultados dos
motores.
