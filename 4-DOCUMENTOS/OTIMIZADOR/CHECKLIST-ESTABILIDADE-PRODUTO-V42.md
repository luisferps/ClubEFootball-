# Checklist oficial — produto Otimizador V42

Data: 01/09/2026. Escopo: resposta imediata do painel da Fila integral e
empacotamento portátil. Esta entrega não altera fórmula, pesos, moldes, regras
de negócio, schema, contratos do banco, ordem de execução, dados de jogo,
publicação ou Bonificador.

## Separação de estado e página

- [x] `GET /api/fila/status` chama apenas o resumo
  `otimizador_producao_status_v6` pela allowlist local;
- [x] o resumo devolve estado, totais, ações, gates e linha corrente sem buscar
  `otimizador_producao_fila_operacional_v3`, rótulos ou nome de carta;
- [x] `GET /api/fila/linhas` mantém a leitura da página e os rótulos canônicos
  por ID, depois que o estado já foi desenhado;
- [x] enquanto a página chega, a tabela declara “Carregando linhas da fila em
  segundo plano”; ela não mostra estado falso, não altera linha e não bloqueia
  os controles;
- [x] refresh automático não duplica uma página já sendo carregada;
- [x] Fila continua com próximas linhas primeiro e finais por último; Resultados
  continua separado e mais recente primeiro.

## Fronteira e travas preservadas

- [x] dados de jogo e fila continuam em `clube_novo`; `public` é apenas a
  fachada RPC protegida;
- [x] browser continua restrito a `127.0.0.1` e não recebe URL privada, senha ou
  chave do banco;
- [x] nenhum texto/nome decide cálculo ou vínculo; rótulos continuam resolvidos
  por IDs canônicos;
- [x] fórmula aprovada preservada: barras teto 99 -> proficiência piso/teto
  40/99 -> boost técnico -> ímpetos;
- [x] Messi: 99 -> proficiência 99 -> boost 100 -> Precisão 104;
- [x] Ímpetos condicionais, publicação e Bonificador permanecem desligados neste
  painel.

## Provas executadas

- [x] `py_compile` de `interface/servidor.py` e `node --check` de
  `interface/app.js`;
- [x] `teste_interface_local_otimizador.py`: 23/23 verdes, incluindo status
  rápido sem leitura de página/rótulos;
- [x] `teste_esteira_preparo_execucao_v6.py`: 6/6 verdes;
- [x] `teste_formula_aprovada.py`: Messi/Capello/Precisão = 104;
- [x] serviço portátil V42 em porta isolada: saúde ok, versão
  `20260901-v42`, `worker_ativo=false`, `preparador_ativo=false`;
- [x] leitura real do resumo em 800 ms: `rodando`, 184.702 linhas, 245
  concluídas, 184.457 pendentes, 0 processando;
- [x] leitura real de uma página em 393 ms: linha 3399, pendente,
  `52781926899717 · Gerard Moreno`;
- [x] a prova não iniciou worker/preparador, não reservou linha, não calculou,
  não escreveu, não publicou e encerrou o serviço isolado ao final.

## Distribuição e recuperação

- [x] ponto único de abertura: `2-MOTORES/OTIMIZADOR/Otimizador ClubEfootball.exe`;
- [x] lançador versão `1.7.1.0`, mutex próprio V42, exige a interface
  `20260901-v42`, evitando reusar serviço anterior;
- [x] a pasta OTIMIZADOR inteira, inclusive `runtime/_internal/`, deve acompanhar
  o ícone em outra máquina;
- [x] snapshot pré-V42:
  `4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/20260831-v42-preparo-status-rapido-antes/`;
- [x] não houve migration/rollback de banco nesta revisão: a mudança é local,
  reversível pelo snapshot e pelo serviço/ícone anteriores.
