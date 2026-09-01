# Aplicativo local do Bonificador

**Versão:** 2.0.24 · **Data:** 31/08/2026 · **Estado:** filas humanas, resultados persistidos e controle local do pipeline

## Revisão V2.0.24 — resultados preservam a referência humana

A aba **Fila de resultados** usa `bonificador_resultados_v1`, contrato privado que
lê o resultado já confirmado em `build_bonificador` e o associa novamente à carta,
função e posição canônicas. Ela não tenta usar a fila de pendências como dicionário:
uma linha confirmada deixa essa fila e por isso não pode mais depender dela para
mostrar o nome humano.

## Revisão V2.0.23 — filas para o operador

A tela separa **Fila do Bonificador** (somente pendentes) de **Fila de resultados**
(somente linhas calculadas na rodada). A segunda aba mostra as parcelas reais e os
bloqueios; a primeira não mistura pendência com resultado.

O contrato privado `bonificador_contexto_fila_v5` projeta apenas a apresentação
humana necessária da mesma linha canônica: nome da carta, coleção, overall, função e
posição por extenso. Readback: 613 de 613 linhas possuem os três nomes. A janela não
consulta tabelas diretamente, e os IDs permanecem internos ao motor.

O escritor V4 também passou a deixar a coluna de identidade gerada pelo próprio banco.
O erro de identidade (`cannot insert a non-DEFAULT value into column id`) foi corrigido
sem alterar fórmula, parcelas, pesos, moldes, gates ou regra. A tentativa anterior teve
0 confirmações e nenhuma escrita parcial.

## Revisão V2.0.22 — UTF-8 na leitura do contrato

O servidor local já enviava JSON UTF-8. A falha remanescente estava no cliente
WinForms: `WebClient` usava a página de código padrão do Windows ao ler a resposta.
Agora ele força `Encoding.UTF8` em todo GET e POST local. Nomes recebidos como
`Função` deixam de aparecer como `FunÃ§Ã£o`; não houve alteração de dados, contrato,
fórmula ou fila.

## Revisão V2.0.21 — resultado visível e texto correto

A primeira aba agora mostra cada linha da fila que o processo acabou de tratar, sem
reconstruir resultado no navegador: situação (`apta` ou `bloqueada`), corpo, pé ruim,
estilo, IA, total e, se houver, o motivo do gate. A tabela continua mostrando as 613
linhas pendentes antes da execução; durante a execução ela é atualizada com os eventos
`FILA_RESULTADO` que o próprio motor emite.

Foi corrigida a conversão do retorno JSON da RPC no aplicativo WinForms: o retorno
canônico é uma coleção e não uma `ArrayList`; antes a janela recebia a fila, mas
descartava suas linhas ao montar a grade. O processo local também fixa a saída em UTF-8
e a janela lê essa saída em UTF-8, para que acentos como **função**, **posição** e
**não executado** não apareçam corrompidos.

O gate de proveniência foi alinhado aos contratos canônicos: a versão da carta ainda
precisa ser a mesma da linha da build, mas o fingerprint de `build_linha_card` não é
comparado ao fingerprint de `bonificador_carta_v2`, pois são fotografias diferentes.
O resultado e o escritor V4 usam o fingerprint da carta canônica. Da mesma forma,
`bonificador-regua-v2` e `bonificador-carta-v2` não são tratados como se fossem uma
única versão. Isso remove apenas um bloqueio falso de selos; não altera fórmula,
pesos, moldes, ordem, regras ou valores matemáticos.

## Estado operacional atual — fila V4

A fila exibida pelo único EXE é `public.bonificador_contexto_fila_v4`. Ela lista
somente as linhas canônicas de `clube_novo.build_linha_card` que ainda têm o marcador
`bonificador_nao_executado` e já concluíram os estados de prontidão. Não usa
`bonificador_par`, recorte de teste, `clube.build` ou qualquer tabela legada.

O componente local usa o login restrito `bonificador_runtime`, que só pode chamar
`bonificador_regua_v2`, `bonificador_carta_v2`, a fila V4 e o escritor V4; a janela
nunca recebe acesso a tabela ou a credencial administrativa. A leitura empacotada
confirmou 613 linhas, 50 cartas e 19 funções. Abrir ou atualizar a tela não calcula
nem grava bônus. O botão de iniciar continua sendo a única ação que pode iniciar o
motor local.

A abertura prioriza a fila. O catálogo de funções só é consultado quando a aba
**Testar uma carta** é aberta; ele não pode atrasar, bloquear ou apagar a lista de
pendências. O processo iniciado pelo botão recebe o caminho explícito da configuração
do Bonificador, inclusive quando o componente está empacotado.

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
- `TESTES/testar_interface_local.py` e `TESTES/testar_pipeline_incremental.py`:
  aprovados após a emissão de `FILA_RESULTADO`, a parada cooperativa por arquivo local
  e a leitura da lista JSON; a tela permanece responsiva.

O rollback de todos os arquivos exclusivos está em
`RECUPERACAO/2026-08-28-ANTES-INTERFACE-LOCAL`; ele não toca motor, `config.txt`,
contratos, banco, Otimizador ou Extrator.

O snapshot específico antes desta integração está em
`RECUPERACAO/2026-08-31-ANTES-INTEGRACAO-PIPELINE-APP`.

## Histórico de revisão V2: janela nativa e fila

O EXE V2.0.0 substitui a abertura no Edge por uma janela WinForms, como o Extrator.
A primeira aba replica a organização útil do Otimizador: controles de iniciar/parar,
estado, progresso, linha atual, totais, tabela e eventos. Essa revisão foi substituída
pela fila V4 descrita no início deste documento; não é uma rota de runtime atual.
As abas de simulação e auditoria permanecem separadas.

A leitura desta revisão revelou uma indisponibilidade de cache do PostgREST. Ela foi
superada pela leitura local restrita das RPCs V2/V4, confirmada no pacote atual.
O rollback dos arquivos desta revisão é
`RECUPERACAO/2026-08-31-ANTES-INTERFACE-NATIVA-FILA`.

## Prova de abertura do pacote V2.0.19

Em 31/08/2026, o componente incorporado ao único EXE respondeu por loopback à fila
V4 e à saúde da régua: 613 linhas, primeira linha `2433`, contrato
`bonificador_contexto_fila_v4`, régua `bonificador-regua-v2` apta. O ensaio encerrou
a árvore temporária do componente ao fim e não iniciou o pipeline nem escreveu bônus.

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
