# Aplicativo local do Bonificador

**Versão:** 1.1.0 · **Data:** 31/08/2026 · **Estado:** consulta e controle local do pipeline

Abra `2-MOTORES/BONIFICADOR/Bonificador ClubEfootball.exe`. Ele é um aplicativo local
com ícone próprio: o EXE inicia o executor oculto em `127.0.0.1:8766`, confirma a
saúde e abre a janela. `RODAR-INTERFACE-BONIFICADOR.bat` recompila somente esse
lançador, se necessário, e o abre.

Na tela, o usuário informa o `card_id` e escolhe a função. A resposta mostra corpo, pé
ruim, posição principal, os dois playstyles, IA, molde, régua, regras, bônus e gates.
Também mostra contrato, proveniência, cardinalidades e fingerprint do motor.

O browser não conhece Supabase: `app.js` não contém chave, URL, schema ou acesso a
tabelas. As consultas seguem por `GET`; os dois `POST` permitidos apenas iniciam ou
pedem a parada normal do processo local conhecido do Bonificador. O executor usa a
chave local, inicia `motor_bonus.py` em processo separado e mostra o estado
(`iniciando`, `processando`, `aguardando`, `parando`, `parado` ou `erro`) sem bloquear a
tela. O navegador não recebe endpoint de banco, writer, fórmula ou lote.

O botão **Iniciar Bonificador** é o fluxo normal do operador. O processo consulta
somente linhas que o Otimizador já confirmou; quando não houver linha apta, o estado
passa a **aguardando**. O botão **Parar normalmente** envia um sinal cooperativo: a
rodada em andamento termina e nenhuma outra é iniciada. Um único escritor Bonificador
por banco continua recomendado.

## Provas realizadas

- compilação do EXE com ícone multirresolução;
- abertura pelo EXE e health-check aprovado para `bonificador-regua-v1`;
- `TESTES/testar_interface_local.py`: Casillas determinístico, `b_estilo=1.5`, início
  e parada assíncronos do processo falso, health/status responsivo, POST desconhecido
  bloqueado (405) e frontend sem credencial;
- validação visual e online: Iker Casillas `88045755827028`, função #5, exibiu slots
  `291`/`336`, todos os gates aprovados, `b_estilo=1.5000`, `b_total=1.6875` e console
  sem erros.

O rollback de todos os arquivos exclusivos está em
`RECUPERACAO/2026-08-28-ANTES-INTERFACE-LOCAL`; ele não toca motor, `config.txt`,
contratos, banco, Otimizador ou Extrator.

O snapshot específico antes desta integração está em
`RECUPERACAO/2026-08-31-ANTES-INTEGRACAO-PIPELINE-APP`.

## Revisão V2: janela nativa e fila

O EXE V2.0.0 substitui a abertura no Edge por uma janela WinForms, como o Extrator.
A primeira aba replica a organização útil do Otimizador: controles de iniciar/parar,
estado, progresso, linha atual, totais, tabela e eventos. A fila não é local: o
servidor loopback lê somente `bonificador_contexto_escrita_v2`; a janela nunca recebe
credencial, URL de banco, schema ou acesso direto a tabelas. As abas de simulação e
auditoria permanecem separadas.

A leitura real de 31/08/2026 confirmou `bonificador_regua_v1` apta e revelou que
`bonificador_contexto_escrita_v2` ainda está ausente da cache do PostgREST (`PGRST202`).
A janela conserva esse detalhe seguro e o motor permanece fail-closed, sem fallback,
escrita ou lote. O rollback dos arquivos desta revisão é
`RECUPERACAO/2026-08-31-ANTES-INTERFACE-NATIVA-FILA`.
