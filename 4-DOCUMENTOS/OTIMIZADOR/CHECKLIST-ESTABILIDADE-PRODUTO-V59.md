# Checklist — fila portátil em blocos V59

Data: 01/09/2026  
Escopo: execução local da fila integral já existente, sem alterar fórmula,
pesos, ordem de cálculo, moldes, publicação, banco de origem ou Ímpetos
condicionais.

## Pacote que viaja entre computadores

- [x] A fotografia integral está em
  `2-MOTORES/OTIMIZADOR/PACOTE-FILA-INTEGRAL/ddbcbc86-1ae7-4b95-b9f0-22601f41b61d/`.
- [x] Ela contém 19.363 cartas e 183.287 linhas pendentes, separadas em 20
  arquivos de cartas e 184 blocos de no máximo 1.000 linhas.
- [x] A fotografia tem hashes e selos de fórmula, contrato, lote e carta.
- [x] Não contém URL, chave `SUPABASE`, segredo `sb_*`, resultado, reserva ou
  estado de execução.
- [x] O estado mutável fica separado em `runtime/fila-local/` e é identificado
  pela máquina; até uma cópia física da pasta inteira não reutiliza reservas ou
  resultados pendentes de outra máquina.
- [x] O aplicativo recusa iniciar se a fotografia não vier junto; ele não baixa
  a fila escondidamente no computador de destino.

## Cálculo e envio

- [x] O worker chama a mesma `roda_lote_v6.trabalha()` aprovada; nenhuma fórmula
  ou peso foi alterado.
- [x] Condicionais de Ímpeto continuam desligados e `pode_publicar=false`.
- [x] Resultados são gravados primeiro no disco local e enviados por contrato
  selado em grupos de até 100, sem duplicar uma linha já confirmada.
- [x] A reserva continua exclusiva no banco por `linha_id` e IDs canônicos.
- [x] O piloto de uma linha para mesmo se a primeira linha bloquear; ele não
  procura uma segunda linha para compensar uma falha.

## Provas executadas

- [x] Integridade do pacote e selo da fórmula aprovados antes do piloto.
- [x] 10 testes offline do pacote/worker passaram, inclusive o caso de falha
  da primeira linha no piloto.
- [x] O serviço portátil foi recompilado depois da trava do piloto.
- [x] Leitura real do painel mostrou 19.363 cartas, 184.827 linhas, 1.540
  concluídas, 183.287 pendentes e 0 em andamento antes do piloto.
- [x] Piloto real: ordem 1.541 / linha 4694 / Ademola Lookman foi concluída em
  uma única tentativa e o lote voltou a `pausado`.
- [x] Readback pós-piloto confirmou `b1=-401.9`, 3 Builds comparadas de 55,
  duração `3,34272 s`, técnico canônico e resultado persistido.
- [x] Estado pós-piloto: 1.541 concluídas, 183.286 pendentes, 0 processando,
  0 bloqueadas, 0 interrompidas e nenhuma publicação.

## Operação liberada

- [x] O operador abre somente `Otimizador ClubEfootball.exe`.
- [x] A aba Fila mostra as pendências primeiro, por nomes legíveis; a foto de
  abertura confirmou a primeira pendência no painel.
- [ ] Rodada integral: só começa quando o operador clicar **Retomar** de forma
  deliberada, depois de conferir que o painel está `Pausado`.

## Recuperação

- [x] Snapshot imediatamente anterior à proteção do piloto:
  `4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/20260901-v59-piloto-limite-antes/`.
- [x] Snapshots anteriores do pacote e serviço: V57 e V58, na mesma pasta de
  recuperação.
- [x] A recuperação não apaga linhas, Builds, eventos ou publicação já
  confirmados.
