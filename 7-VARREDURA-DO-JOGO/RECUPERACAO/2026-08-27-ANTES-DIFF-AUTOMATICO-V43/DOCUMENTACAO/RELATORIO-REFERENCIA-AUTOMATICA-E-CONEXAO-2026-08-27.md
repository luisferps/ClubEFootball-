# Relatório — referência automática e conexão segura

**Data:** 27 de agosto de 2026  
**Resultado:** concluído sem escrita de dados

## Entrega

O Extrator eFootball passou a manter a carga integral de referência internamente. O usuário não procura, escolhe nem conserva CSV de gabarito. Quando a fonte física é a mesma, a referência vigente é verificada e reutilizada. Quando a fonte muda, o aplicativo extrai, valida, compara e somente então sela uma nova versão; uma falha preserva a versão anterior.

Depois de uma carga incremental ou completa validada, existe um único painel **Enviar carga validada ao banco**. O botão **OK — preparar envio ao clube_novo** abre o pré-voo do pacote que o próprio extrator acabou de gerar. Não existe upload de CSV externo. O envio final continua dependendo da caixa de revisão, da frase específica da execução e do clique **Aplicar esta carga no clube_novo**.

## Conexão existente reutilizada

- projeto identificado pelo `config.txt` já existente na pasta principal do ClubEfootball;
- senha PostgreSQL lida somente do ambiente seguro do usuário do Windows;
- nenhuma credencial foi copiada para HTML, JavaScript, executável, configuração distribuída, manifesto ou relatório;
- executor restrito a `127.0.0.1` e conexão PostgreSQL com SSL;
- destino fixo e validado: `clube_novo.carta_jogo`;
- qualquer tentativa de apontar para `clube` é recusada.

## Evidência de validação

- referência integral: 43.072 cartas, 43.072 `card_id` únicos e zero duplicadas;
- comparação contra o alvo atual: 269 inserções, 34 atualizações e zero inativações;
- pré-voo real autenticado em transação somente leitura;
- interface confirmou destino, tipo e contagens antes de habilitar a confirmação final;
- pacote integral e pacote incremental foram classificados automaticamente;
- CSV avulso e destino `clube` foram bloqueados;
- o endpoint final de aplicação não foi acionado;
- antes e depois do pré-voo, `clube.carta_jogo` e `clube_novo.carta_jogo` permaneceram com 42.803 linhas, 42.803 IDs únicos e fingerprint `ff67b8a2e544570dae42ed71d8428821`.

## Artefatos principais

- sistema operacional: `SISTEMA-EXTRATOR`;
- referência interna: `SISTEMA-EXTRATOR\artefatos\referencias-cartas`;
- manual: `DOCUMENTACAO\MANUAL-DO-EXTRATOR.md`;
- conexão somente leitura: `03-validacao\VALIDACAO-CONEXAO-REAL-SOMENTE-LEITURA-2026-08-27.json`;
- prova da interface: `03-validacao\VALIDACAO-INTERFACE-ENVIO-MANUAL-2026-08-27.json`;
- prova da referência automática: `03-validacao\VALIDACAO-REFERENCIA-AUTOMATICA-2026-08-27.json`;
- prova do fluxo único: `03-validacao\VALIDACAO-FLUXO-UNICO-BANCO-2026-08-27.json`.

## Estado final

A conexão e o botão estão operacionais, mas nenhuma carga foi aplicada nesta etapa. Ao abrir o aplicativo, nada é escrito automaticamente. O único caminho de escrita é o pacote atual, validado e deliberadamente confirmado pelo usuário dentro do próprio aplicativo.
