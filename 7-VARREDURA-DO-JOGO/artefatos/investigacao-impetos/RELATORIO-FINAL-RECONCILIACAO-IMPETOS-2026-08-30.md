# Relatório final — reconciliação de Ímpetos — 30/08/2026

## Frente 1 — especiais da categoria 0 e ponte de texto

Resultado operacional: **concluído**.

- Foram persistidos em `clube_novo.impeto_jogo` os 14 rótulos operacionais
  autorizados: códigos `56`, `57`, `58`, `134`, `135`, `142`, `143`, `144`,
  `250`, `261`, `263`, `265`, `266` e `267`.
- A transação alterou somente `nome_pt` e `falta_o_que` dessas 14 linhas.
- `secao_texto` e `id_texto` permaneceram nulos; `pode_rodar` permaneceu
  falso. A pendência `ponte_fisica_texto_codigo_pendente` continua registrada.
- `carta_impeto_jogo` permaneceu em 3.748 linhas, MD5
  `c7566b179906f1b63d856e9ab365a59e`.
- `impeto_atributo_jogo` permaneceu em 2.072 linhas, MD5
  `79a605fd139b05308696bf76b9cbb9a0`.
- `impeto_condicao_jogo` permaneceu em 407 linhas, MD5
  `9bfe008cafe620c7ee969f7cdecbec9d`.
- Snapshot, readback e rollback final estão respectivamente em
  `snapshot-antes-rotulos-especiais-categoria0-final.json`,
  `readback-rotulos-especiais-categoria0-final.json` e
  `ROLLBACK-ROTULOS-ESPECIAIS-CATEGORIA0-FINAL.sql`.

Resultado da ponte física: **não comprovada no DT870 atualizado**.

- Fonte examinada: DT870 da pasta de atualização Konami, SHA-256
  `44df868c2613d532292d87072c0863a907d6a5f0cc40f914d355e56d74edfcc5`.
- Os seis registros de atributo único foram localizados nos índices físicos
  `200–205` e os seis textos existem no dicionário oficial, mas não foi achado
  um layout comum que ligue código do Ímpeto a seção/id de texto.
- Os oito nomes exclusivos não aparecem como strings no CPK e não há arquivo
  `.locres` dentro dele.
- Coincidências numéricas isoladas foram descartadas; nenhum `secao_texto` ou
  `id_texto` foi inventado.

Evidência: `investigacao-ponte-rotulos-especiais-categoria0.json`.

## Frente 2 — códigos históricos deslocados

Resultado: **reconciliação fechada em modo fail-closed; nenhum par foi
promovido**.

- O `PlayerBooster.bin` do DT870 Steam tem 6.624 bytes, prefixo de 24 bytes e
  165 blocos de 40 bytes; SHA-256
  `e54720e512d2579b94136244a8a6a3f13c572eaada71b22f61919a87197c087b`.
- Os 22 registros candidatos foram relidos no número de registro indicado e
  todos reproduziram o padrão físico `código bruto = código histórico - 1`,
  com SHA-256 individual exato.
- Nenhum dos 22 alcançou prova semântica completa de condição, alvo, efeitos e
  faixas. Há colisões com variantes atuais reais nos códigos `208`, `268`,
  `308`, `334` e `368`; por isso não foi aplicada regra global `+1` nem escrita
  no banco.
- O runtime V5 agora isola o DT870 Steam em `historical_source`; essa fonte não
  entra na união canônica e não é decodificada com o layout atual.
- O validador classifica esses casos como
  `historico_deslocado_sem_prova_semantica`, fora de novo/removido/alterado e
  sempre pendentes de revisão.
- O worker V5 deixou de carregar `app/catalog-source-map.js`; o mapa local não
  é usado como autoridade operacional.

Prova read-only do runtime:

- 412 registros canônicos, apenas DT200/DT870 atualizado;
- zero registro canônico com origem DT870 Steam;
- 165 registros históricos preservados;
- 22/22 candidatos reproduzidos por código bruto, número do registro e hash;
- zero escrita de banco ou domínio.

Evidências:

- `diagnostico-layout-playerbooster-original.json`;
- `conclusao-reconciliacao-codigos-historicos.json`;
- `teste-runtime-historico-failclosed.json`;
- `teste-reconciliacao-historica-failclosed.json`.

## Estado final

Os rótulos operacionais autorizados estão gravados e protegidos pela pendência
da ponte física. A ponte de texto continua factual e explicitamente pendente.
Os deslocamentos históricos não foram mascarados nem promovidos: permanecem
alertas rastreáveis até que um decodificador semântico do formato legado seja
comprovado. Slots, efeitos, condições, jogo, legado e motores ficaram intactos.
