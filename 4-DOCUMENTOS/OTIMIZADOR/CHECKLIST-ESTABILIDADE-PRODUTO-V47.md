# Checklist — conclusão segura de Build V47

Data: 01/09/2026  
Escopo: corrigir somente a identidade canônica obrigatória do técnico na saída
persistida do Otimizador. Fórmula, pesos, moldes, dados, fila, publicação,
Bonificador e contratos de entrada permanecem inalterados.

## Defeito comprovado

- [x] A linha integral `3675` calculou e a conclusão V6 foi recusada antes de
  gravar em `clube_novo.build_otimizador`.
- [x] O erro físico do banco foi `tecnico_id` nulo em uma FK obrigatória.
- [x] O caso ocorre quando o multiplicador do técnico é corretamente usado pela
  fórmula, mas nenhum boost dele atinge o atributo ponderado e a saída deixa de
  transportar a identidade canônica.
- [x] Não houve resultado, publicação ou alteração de fórmula na linha
  recuperada.

## Correção limitada

- [x] `roda_lote_v6.py` completa apenas o `tecnico_id` ausente a partir do
  multiplicador que a fórmula já escolheu e dos IDs canônicos do contrato.
- [x] Empates usam menor ID canônico, nunca nome/rótulo, e não recalculam a
  Build.
- [x] `fila_producao_v3.py` rejeita uma saída sem `tecnico_id` antes da RPC de
  conclusão e bloqueia somente a linha afetada.
- [x] Uma recusa HTTP 400 confirmada antes da escrita bloqueia somente a linha;
  timeout ou rede continuam ambíguos e não recebem retentativa cega.
- [x] `motor.py`, `equacao.py` e `regua.py` não foram alterados; Messi/Capello
  continua `104`.

## Prova e pacote

- [x] Transação revertida da linha `3676`: a saída trouxe
  `tecnico_id=17606144688129`; a conclusão V6 aceitou a Build temporária e o
  rollback não executou linha produtiva.
- [x] `teste_fila_producao_v3.py`: 10 testes passaram.
- [x] `teste_impetos_linhas_v12.py`: 7 testes passaram.
- [x] `teste_formula_aprovada.py`: Messi/Capello = 104.
- [x] `teste_interface_local_otimizador.py`: 32 testes passaram.
- [x] Python e JavaScript passaram nas verificações de sintaxe.
- [x] `Otimizador ClubEfootball.exe` e `runtime/OtimizadorServico.exe` foram
  recompilados como pacote V47 / versão do arquivo 1.7.5.0.
- [x] Saúde do loopback: `versao_interface=20260901-v47`, sem worker e sem
  credencial exposta à tela.

## Estado liberado

- [x] Lote `ddbcbc86-1ae7-4b95-b9f0-22601f41b61d` está `pausado`.
- [x] Linha `3675` voltou a `pendente`; reserva e worker foram limpos.
- [x] Readback: 521 concluídas, 184.306 pendentes, 0 processando, 0 bloqueadas
  e `SEM PUBLICAÇÃO`.
- [x] Próxima ação humana é abrir o ícone oficial e clicar uma vez em
  **Retomar**; a abertura isolada não calcula por acidente.

## Recuperação

- [x] Snapshot recuperável:
  `4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/20260901-v47-tecnico-canonico-antes/`.
- [x] A recuperação troca somente os arquivos deste checklist; não exige SQL e
  não apaga Builds, linhas, eventos ou publicação.
