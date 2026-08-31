# Aplicativo local do Bonificador

**Versão:** 2.0.15 · **Data:** 31/08/2026 · **Estado:** consulta e controle local do pipeline

Abra `2-MOTORES/BONIFICADOR/Bonificador ClubEfootball.exe`. Ele é um aplicativo local
com ícone próprio: o EXE extrai o componente local incorporado para a área local do
Windows, escolhe uma porta livre apenas em `127.0.0.1`, confirma o `ping` e abre a
janela. Não depende de Python instalado, pasta `runtime` copiada ou porta fixa. O
payload interno não é um segundo aplicativo do operador: ele fica incorporado no EXE
principal, só é extraído para a área local do Windows enquanto a aplicação está ativa e
é apagado ao fechar.

Na tela, o usuário informa o `card_id` e escolhe a função. A resposta mostra corpo, pé
ruim, posição principal, os dois playstyles, IA, molde, régua, regras, bônus e gates.
Também mostra contrato, proveniência, cardinalidades e fingerprint do motor.

A janela WinForms conversa somente com o componente local em loopback. As consultas
seguem por `GET`; os dois `POST` permitidos apenas iniciam ou pedem a parada normal do
processo local conhecido do Bonificador. Não há navegador, página web, credencial,
URL de banco, schema ou acesso direto a tabelas. O executor usa a chave local, inicia
`motor_bonus.py` em processo separado e mostra o estado (`iniciando`, `processando`,
`aguardando`, `parando`, `parado` ou `erro`) sem bloquear a tela.

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
  bloqueado (405) e ausência comprovada de rotas/página web;
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

## Correção de responsividade V2.0.7 — 31/08/2026

A janela nativa nunca executa consulta HTTP, contrato ou banco na thread visual. Ao
abrir, atualizar fila, simular, auditar ou enviar iniciar/parar, ela mostra o estado
imediatamente e realiza a chamada no trabalhador em segundo plano. A comunicação com
o componente local tem limite de 10 segundos; indisponibilidade do banco aparece como
erro de consulta, sem travar a janela ou o Windows marcar “Não está respondendo”.

Não houve alteração de fórmula, molde, pesos, regras, dados, banco, fila produtiva,
Otimizador ou Extrator. O snapshot imediatamente anterior está em
`RECUPERACAO/SNAPSHOT-UI-ANTES-ASSINCRONO-20260831-194509.cs`; para voltar, restaure
esse arquivo como `windows-app/ClubEfootballBonificadorLauncher.cs` e recompile pelo
script oficial.

## Distribuição limpa V2.0.15 — 31/08/2026

Na raiz operacional `2-MOTORES/BONIFICADOR` existe um único aplicativo abrível:
`Bonificador ClubEfootball.exe`. O componente interno é um recurso binário de
compilação em `windows-app/assets/BonificadorComponente.bin`, não um segundo `.exe`.
Os caches Python, runtime portátil experimental, lançadores paralelos e logs de erro
antigos foram retirados; não participam da operação, da recuperação nem do cálculo.
Cada abertura cria um componente próprio em porta livre e encerra a árvore inteira
desse componente ao fechar a janela; componentes antigos não são reutilizados nem
ficam vivos em segundo plano.
Falhas de abertura são apresentadas na própria janela de erro; o aplicativo não cria
arquivos de log ou erro na raiz operacional.
