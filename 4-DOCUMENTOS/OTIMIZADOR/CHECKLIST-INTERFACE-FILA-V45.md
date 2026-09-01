# Checklist — Interface da Fila V45

Data: 01/09/2026  
Escopo: atualização visual da Fila integral e de Resultados. Não altera motor,
fórmula, dados, estados da fila, publicação ou Bonificador.

## Correções

- [x] A página usa `app.js?v=20260901-v45`, não a chave antiga V32.
- [x] Toda consulta visual pelo loopback possui timeout de 15 segundos.
- [x] Falha de `/api/fila/linhas` fica visível na tabela e é tentada novamente.
- [x] Eventos e Resultados são resolvidos de forma independente; falha em
  Eventos não descarta a lista de Resultados.
- [x] A linha atual continua no resumo e a página detalhada traz os rótulos e
  campos completos quando responde.

## Provas

- [x] `node --check interface/app.js` passou.
- [x] `teste_interface_local_otimizador.py`: 29 testes passaram.
- [x] Serviço local ativo serviu o HTML V45 e o JS com timeout e mensagens
  explícitas.
- [x] Readback HTTP real: 100 linhas da Fila, 100 Resultados e linha atual
  retornados por contratos de `clube_novo`.
- [x] Nenhuma ação `POST`, reserva, cálculo, pausa, parada ou publicação foi
  emitida nesta revisão.

## Recuperação

Snapshot anterior:
`4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/20260901-v45-ui-atualizacao-antes/`.
Para desfazer, restaure somente `interface/app.js` e `interface/index.html`
desse snapshot com o aplicativo parado; não toque em banco, fila ou Builds.
