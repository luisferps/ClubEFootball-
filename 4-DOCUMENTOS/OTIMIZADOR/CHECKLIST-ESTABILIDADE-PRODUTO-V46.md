# Checklist — Retomada integral V46

Data: 01/09/2026  
Escopo: corrigir a retomada da fila integral já 100% preparada. Não altera
fórmula, pesos, moldes, dados do jogo, publicação, Bonificador ou legado.

## Defeito confirmado

- [x] A linha 3675 foi reservada após **Retomar** para o lote integral
  `ddbcbc86-1ae7-4b95-b9f0-22601f41b61d`.
- [x] O lote falhou com `contrato recusou a consulta (400)` antes de qualquer
  resultado da linha: `build_otimizador_id`, `build_bonificador_id` e término
  estavam nulos.
- [x] A causa no aplicativo foi localizada: após `preparo.pendentes = 0`,
  `ServicoOtimizador.iniciar_fila()` iniciava o worker comum V3 em vez do
  worker da esteira V7.

## Correção e segurança

- [x] Toda retomada de lote `integral` agora chama
  `_iniciar_worker_producao(..., esteira=True)`, inclusive depois de a preparação
  acabar.
- [x] Foi criada a recuperação V20, limitada ao selo do incidente real, uma
  única reserva e zero resultado persistido.
- [x] A função V20 usa trava de lote/linha, `security definer`,
  `search_path=''`, `REVOKE` para público/anon/authenticated e `GRANT` somente
  para `service_role`.
- [x] A V20 devolveu a linha 3675 a `pendente`, removeu worker/token, deixou o
  lote `pausado` e preservou as 521 linhas concluídas.
- [x] Readback confirmou: zero em processamento, 184.306 pendentes, publicação
  desligada, fórmula aprovada intacta e nenhum resultado na linha recuperada.

## Aplicativo

- [x] `Otimizador ClubEfootball.exe` e `runtime/OtimizadorServico.exe` foram
  recompilados como V46.
- [x] Abertura limpa pelo ícone oficial respondeu em `127.0.0.1:8769` com
  `versao_interface=20260901-v46`.
- [x] O HTML ativo carregou `app.js?v=20260901-v46`.
- [x] Fila e Resultados devolveram páginas reais em loopback; não houve POST de
  início, reserva, cálculo, pausa, parada ou publicação durante a prova do
  pacote.
- [x] O estado liberado é `pausado` com `retomar=true`; o próximo clique do
  operador inicia somente o worker V7 correto.

## Testes

- [x] `teste_interface_local_otimizador.py`: 32 testes passaram.
- [x] Nova regressão: fila integral já preparada chama exclusivamente o worker
  com `esteira=True`.
- [x] Nova regressão: recuperação V20 requer confirmação e usa o RPC V20
  exato.
- [x] `node --check interface/app.js` passou.

## Recuperação

- Snapshot local: `4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/20260901-v46-recuperacao-pos-preparo-antes/`.
- Migration: `MIGRACAO-RECUPERACAO-RETOMADA-INTEGRAL-V20.sql`.
- Rollback: `ROLLBACK-RECUPERACAO-RETOMADA-INTEGRAL-V20.sql`. Ele remove a
  função futura; não desfaz eventos, linhas ou Builds já existentes.
