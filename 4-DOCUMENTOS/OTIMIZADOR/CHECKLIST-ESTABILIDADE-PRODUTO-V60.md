# Checklist — entrega portátil V60

Data: 01/09/2026  
Substitui operacionalmente o checklist V59 para cópia entre computadores.

## Entrega verificada

- [x] O pacote de entrada integral está dentro de `OTIMIZADOR/PACOTE-FILA-INTEGRAL/`.
- [x] Ele traz 183.287 pendências em 184 blocos de até 1.000 linhas, sem
  credenciais.
- [x] O estado de trabalho é separado por máquina; copiar a pasta inteira não
  reaproveita reserva, spool ou envio pendente de outra máquina.
- [x] A ausência do pacote falha antes de iniciar uma linha; não há download
  escondido no computador de destino.
- [x] O envio usa resultado gravado localmente e confirma no máximo 100 linhas
  por chamada, de forma idempotente.
- [x] A fórmula, pesos, ordem, moldes e Ímpetos condicionais permanecem como
  estavam; publicação continua desligada.

## Prova real e executável

- [x] Uma única linha real foi calculada e persistida: ordem 1.541, linha 4694,
  Ademola Lookman; o lote voltou automaticamente a `pausado`.
- [x] Readback: 1.541 concluídas, 183.286 pendentes, 0 processando, 0
  bloqueadas, 0 interrompidas e `pode_publicar=false`.
- [x] A proteção do piloto também para depois da primeira linha bloqueada; não
  procura a segunda linha.
- [x] 11 testes do pacote/worker e 32 testes do painel passaram.
- [x] `Otimizador ClubEfootball.exe` iniciou o serviço portátil real em
  loopback; saúde e fila retornaram o estado esperado sem iniciar worker.
- [x] O serviço de teste foi encerrado; porta 8769 ficou livre e a fila ficou
  pausada.

## Uso

- [x] Copie a pasta `2-MOTORES/OTIMIZADOR/` inteira, incluindo `runtime`,
  `interface` e `PACOTE-FILA-INTEGRAL`.
- [x] Abra somente `Otimizador ClubEfootball.exe`.
- [ ] Para rodar todas as pendências, o operador deve clicar deliberadamente em
  **Retomar** após conferir o estado `Pausado`.

## Recuperação

- [x] Snapshot V60: `4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/20260901-v60-estado-local-por-maquina-antes/`.
- [x] Snapshots V57–V59 permanecem disponíveis; nenhum rollback apaga resultado
  já confirmado.
