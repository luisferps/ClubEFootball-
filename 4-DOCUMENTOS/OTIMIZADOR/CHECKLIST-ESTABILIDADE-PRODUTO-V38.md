# Checklist oficial — estabilidade do produto Otimizador V38

Data: 31/08/2026. Escopo: abertura, portabilidade e recuperação da interface
local. Não autoriza rodada, publicação, alteração de fórmula, pesos, moldes,
regras de negócio ou schema.

## Entrega de produto

- [x] existe um único ponto de abertura: `2-MOTORES/OTIMIZADOR/Otimizador ClubEfootball.exe`;
- [x] o lançador embute ícone e inicia o serviço portátil sem Python instalado;
- [x] `runtime/` foi trocado de `onefile` para `onedir`; a pasta `_internal/` é
  exigida antes de abrir;
- [x] uma tela imediata informa que o painel está abrindo, em vez de deixar o
  primeiro clique silencioso;
- [x] clique repetido aguarda a inicialização em curso e reabre o painel, sem
  iniciar um segundo serviço;
- [x] um Otimizador antigo e ocioso na porta local é substituído somente quando
  ele se identifica e declara `worker_ativo=false`;
- [x] serviço com worker ativo não é encerrado automaticamente;
- [x] uma cópia nova pode ser configurada pelo próprio ícone; URL/chave ficam em
  `OTIMIZADOR/config.txt`, local e ignorado pelo Git;
- [x] navegador continua em `127.0.0.1` e nunca recebe credenciais.

## Indisponibilidade do contrato

- [x] boot do servidor não importa fórmula, motor nem régua; estes módulos só
  carregam quando uma simulação ou linha autorizada realmente precisa deles;
- [x] erro remoto `503`, `PGRST*`, `57014` ou timeout devolve estado local
  `banco_indisponivel`, nunca “rodando”;
- [x] todas as ações de fila ficam desabilitadas quando a leitura não foi
  confirmada;
- [x] circuito local de 30 s impede tempestade de RPCs durante uma queda;
- [x] a UI faz retentativa espaçada 5/10/20/40/60 s;
- [x] não há fallback para tabela, fila, build ou rótulo legado.

## Provas executadas

- [x] `python -m py_compile 2-MOTORES/OTIMIZADOR/interface/servidor.py`;
- [x] `node --check 2-MOTORES/OTIMIZADOR/interface/app.js`;
- [x] `4-DOCUMENTOS/OTIMIZADOR/TESTES/teste_interface_local_otimizador.py`: 17/17;
- [x] executável recompilado: `Otimizador ClubEfootball.exe` versão `1.6.7.0`;
- [x] lançamento controlado V38 em loopback: saúde respondeu em 3,993 s,
  `worker_ativo=false`;
- [x] indisponibilidade real do Data API: RPC limitado a 5 s; leitura completa em
  5,110 s retorna fail-closed; segunda leitura local em 2 ms, com zero ações
  habilitadas;
- [x] o serviço iniciado apenas para validação foi encerrado depois da prova,
  após confirmar que não possuía worker.

## Recuperação

- [x] snapshot pré-alteração:
  `4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/20260831-produto-portatil-v37-antes/`;
- [x] manifesto SHA-256 dos arquivos anteriores no mesmo diretório;
- [x] o snapshot anterior V36 continua disponível em
  `4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/20260831-estabilizacao-produto-v36/`.

## Bloqueio externo atual

- [ ] o Data API remoto ainda precisa voltar a responder `otimizador_producao_status_v5`;
- [x] enquanto isso, o aplicativo abre normalmente, mostra reconexão honesta e
  impede a execução de qualquer linha.
