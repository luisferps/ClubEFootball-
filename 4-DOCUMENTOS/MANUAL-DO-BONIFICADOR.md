# Manual do Bonificador — ClubEfootball

## Reparo de retomada HTTP 403 e encerramento — 09/09/2026

A execução na Máquina 2 expôs uma permissão ausente na consulta da carta V3, após a preparação já validada. Corrigido o acesso restrito ao catálogo no banco; HTTP e gravação testados. A única falha 488143 foi recuperada, com prioridade preservada. Bonificador agora retorna código 2 em falha e não anuncia conclusão indevida. Novo pacote único `REPARO-MOTORES-V12` inclui também a correção de prioridade do Otimizador; instalar em `2-MOTORES` por `APLICAR.cmd`, preservando os BATs anteriores. Ver `4-DOCUMENTOS/BONIFICADOR/REPARO-RETOMADA-403-V12.md`. Os registros de prontidão anteriores descrevem a conferência parcial daquela etapa.


## Retomada V12 conferida — 09/09/2026

Pacote do Bonificador completo validado (15 arquivos). Retomada, controle e primeira reserva passaram em transação revertida; lote continua pausado, com 14.107 pendentes. Corrigidos no banco o filtro da auditoria e as restrições de versão do lote, agora compatíveis com os conjuntos coerentes V11/V12. Usar o mesmo `OPERACAO-CORRECAO-FISICA/INICIAR-REPROCESSAMENTO.bat`. Nenhuma nova cópia necessária por esses ajustes. Detalhes em `4-DOCUMENTOS/BONIFICADOR/RETOMADA-CONFERIDA-0909.md`.


## Encerramento confirmado em 09/09/2026

A correção seletiva dos bônus de estilo terminou: **67.795 resultados e 7.455 publicações concluídos, zero pendências e erros nessa operação**. O banco e o painel confirmaram o encerramento em 2026-09-09T08:13:50.106412+00:00. As nove publicações finais foram conferidas no contrato da Ficha, preservando a revisão de habilidades do Otimizador e a ordem dos lotes. A falha do UPDATE de encerramento foi corrigida no banco e no SQL oficial.

Evidência e alcance: [Conclusão dos bônus de estilo](BONIFICADOR/CONCLUSAO-BONUS-ESTILOS-0909.md). A produção geral do Bonificador e as execuções do Otimizador têm estados próprios; este encerramento não significa que seus lotes foram executados. Os registros de andamento abaixo são históricos.

## Retomada futura na Máquina 2 — arquivos preparados

Os arquivos V12 do Bonificador completo estão preparados para cópia direta.
O operador usa o mesmo INICIAR-REPROCESSAMENTO.bat após terminar a correção de
estilos. Antes disso, o comando não inicia nem reserva linhas. A versão do lote
e a política geral só serão atualizadas no início solicitado pelo operador.
Detalhes: [Entrega da Máquina 2](BONIFICADOR/ENTREGA-MAQUINA-2-V12.md). Os registros anteriores abaixo são históricos.

## Operação atual — correção seletiva de estilos V12

O executor autônomo foi instalado e iniciado na máquina oficial. Corrige somente
os estilos de 67.795 resultados e atualiza 7.455 publicações, mantendo as notas
anteriores disponíveis até cada troca ser confirmada. Não declarar conclusão
antes do readback final do banco. Apenas o schema clube_novo é operacional.
A fila geral permanece pausada; a Máquina 2 será atualizada depois.
Código/EXE V12 estão preparados localmente. A política permanece com implantação
geral pendente; a execução seletiva já aplica a regra.
Fonte operacional: [Executor de estilos V12](BONIFICADOR/EXECUTOR-ESTILOS-V12.md).
Os registros anteriores abaixo descrevem etapas históricas.

**Versão 1.19 · 09/09/2026**

> **Decisão aprovada em 09/09, ainda não implantada:** a função define o slot
> principal (1,0) e o secundário (0,5); a posição escolhida determina a ativação
> de cada estilo. Há somente duas exceções: Defensor Criativo e Lateral Defensivo.
> A regra completa e os quatro estilos pendentes estão em
> [Regra de estilos aprovada em 09/09](BONIFICADOR/REGRA-ESTILOS-APROVADA-0909.md).
> A decisão está salva em `clube_novo.bonificador_politica_estilo`, versão
> `estilos-funcao-20260909-v1`. O registro não migrou motores, filas ou notas publicadas.

> **Referência operacional da V11, anterior à decisão acima:** o bônus de estilo verifica a ativação oficial do
> playstyle na **posição escolhida**. A função interna e o molde não decidem essa
> parcela. As seções V9 e V10 permanecem somente como histórico.

Há dois caminhos operacionais distintos:

- a fila incremental normal usa
  `2-MOTORES/BONIFICADOR/RODAR-LOTE-BONIFICADOR.bat`;
- o lote corretivo V11 usa
  `2-MOTORES/BONIFICADOR/OPERACAO-CORRECAO-FISICA/INICIAR-REPROCESSAMENTO.bat`
  e exige o UUID explícito `0ddaa775-24c1-4293-86ca-77fe698aa044`.

O aplicativo `Bonificador ClubEfootball.exe` V2.0.28 identifica a instalação e
oferece consulta/teste. A aba “Lote do Bonificador” preserva o lote V9 somente
para consulta histórica e não inicia produção.

## Processar Fila do Bonificador — batch físico

O batch é uma tarefa de console, no mesmo padrão físico de **Processar Fila** do
Otimizador. Ao dar dois cliques, ele pede confirmação explícita **S/N**. Digitar
`N`, fechar a tarefa, ou executar `status` não reserva linha, não calcula e não
grava resultado. Para processar, confirme `S` ou execute:

```bat
RODAR-LOTE-BONIFICADOR.bat processar
```

Enquanto está em execução, a própria janela de console mostra o progresso real do
motor. Um único `Ctrl+C` pede **pausa cooperativa**: a linha que já estiver em curso
termina de forma atômica, nenhuma próxima linha é reservada e o estado é relido do
banco. Os comandos `status`, `pausar` e `parar` também passam somente pelos contratos
versionados do lote. `status` é estritamente leitura.

O batch não depende de Excel, navegador, UI ou de uma instalação específica de
`psycopg`: se o driver local estiver disponível, usa o canal transacional local; se
não estiver, usa a mesma allowlist de RPC HTTPS autenticada. Em ambos os casos não há
acesso direto a tabela, schema exposto ou fallback legado.

Se aparecer **“a tarefa terminou com código 1”**, execute uma única vez:

```bat
RODAR-LOTE-BONIFICADOR.bat diagnostico
```

Esse modo não inicia o lote. Ele mostra, sem expor chave ou URL, a versão do Python,
presença de `config.txt`, presença do motor, disponibilidade do driver e o resultado
da leitura do contrato do lote. Os erros de instalação, Python incompatível,
configuração ausente e contrato/conexão recusado ficam descritos antes da pausa da
janela.

## Histórico do batch operacional V1 — fila, resultados e controles

Na fotografia de 04/09, o aplicativo estava na versão **V2.0.26**. Ele mostrava um
**lote identificado** antes de executar qualquer cálculo. O lote histórico era
`a69a67b0-7443-45b3-a859-334ab90919af`, criado em 02/09/2026. Preparar ou apenas
abrir a tela não chama o writer nem altera uma carta.

⚠️ **Os contadores deste lote mudam a cada sincronização — não decore número daqui.**
O tamanho da fila é uma função do que o Otimizador já concluiu, e ele continua
concluindo. Retrato em **04/09/2026, 01h27 (Goiânia)**, com o lote `rodando`:

```
itens no snapshot ....... 57.337
pendentes ...............	52.657
concluídas + sem bônus ..  4.680
falhas ..................      0
resultados gravados .....  5.293   (clube_novo.build_bonificador)
```

Para o número de agora, sempre `bonificador_lote_status_v1()` — nunca este texto.
Quando este lote foi criado, em 02/09, ele tinha 10.585 elegíveis; três dias de
Otimizador depois, são cinco vezes mais.

A descoberta é direta, contínua e exclusiva do modelo novo: uma linha só aparece se
`build_otimizador_id` existe, `estado_otimizador='concluido'` e
`build_bonificador_id` ainda está vazio. O lote não usa marcador, lote do Otimizador,
fila manual ou tabela legada. Quando o operador iniciar, novas linhas que chegarem a
esse mesmo estado entram na sincronização do lote; um vínculo Bonificador existente,
inclusive com total **0**, é resultado final e jamais volta à fila.

Na aba **Lote do Bonificador**, a tela mostra o ID do lote, publicação desligada,
contadores de elegíveis, pendentes, em processamento, concluídas, sem bônus e falhas,
além da linha atual por nome humano. A lista é paginada em 100 linhas e usa carta,
função e posição por extenso. A aba **Fila de resultados** mostra as parcelas reais e
o total já confirmado; ela não recalcula nada na janela.

Os botões têm papéis distintos:

- **Iniciar / Retomar** cria o snapshot estável das linhas elegíveis ou continua um
  lote pausado e só então abre o motor local.
- **Pausar** pede a parada cooperativa e espera terminar a linha atômica atual; os
  pendentes permanecem preservados para retomar.
- **Parar lote** encerra o lote após a linha atômica, preserva os resultados já
  gravados e marca os pendentes interrompidos; não apaga nenhuma linha.

Publicação permanece bloqueada no próprio lote (`publicacao_liberada=false`). A tela
fala com o componente local em loopback, que chama apenas RPCs versionadas; o
navegador não recebe credencial, schema nem acesso direto a `clube_novo`.

O ensaio de controle de 02/09 foi executado integralmente em rollback: reservou
10.585 itens, selecionou a linha canônica 3091, fez a transição iniciar → pausar →
pausado e reverteu tudo, sem iniciar o batch real.

**Em 04/09/2026 o batch real foi iniciado** e está em produção: lote `rodando`,
snapshot de 57.337 itens persistidos, resultados sendo gravados a **78 linhas por
minuto**, zero falhas. O histórico do ensaio fica acima só como registro; o estado
vigente é o de produção.

## Pontuação final canônica para Ranking, Elenco e Ficha

O Bonificador não entrega uma segunda pontuação solta para a tela somar. A projeção
privada `clube_novo.build_pontuacao_final_v1` une, pela mesma linha canônica, a
Build candidata do Otimizador e o resultado do Bonificador. Ela preserva os IDs da
linha, carta, função, posição e dos dois resultados, os selos, versões, fingerprints,
proveniência e o motivo de qualquer bloqueio.

A pontuação final candidata é calculada pelo banco com a composição já aprovada:
**pontuação do Otimizador + bônus total do Bonificador**. O navegador nunca recebe
as duas parcelas para decidir ou somar por conta própria. O resultado só fica
`elegivel_para_publicacao` quando os dois motores concluíram a mesma versão de carta
e todos os seus selos coincidem. Lote de teste, selo incompatível ou resultado ausente
continuam bloqueados.

Para a interface existe somente a RPC de leitura
`public.frontend_build_publicada_v2(card_id, funcao_id, limit, offset)`. Ela devolve
apenas Builds já publicadas e seladas; não devolve candidatas, não grava nada e não
expõe as tabelas de `clube_novo`. Em 02/09/2026, as 613 linhas que concluíram a
paridade foram promovidas de forma transacional para publicação: **613 publicadas,
0 excluídas e 0 divergências entre snapshot, projeção e RPC**. A promoção não
recalculou fórmula, pesos, ordem, Otimizador nem bônus; apenas retirou o selo de
teste após conferir os dois resultados e seus selos.

⚠️ Corrigido na v1.16: este trecho dizia `frontend_build_publicada_v1`. **A tela lê
a v2** (`MANUAL-DA-TELA`, 04/09). A v1 ainda existe no banco e é legado de leitura.

🔑 **Publicada não é um `estado`.** Medido em 04/09: as 224.602 linhas de
`build_linha_card` estão todas com `estado='pendente'`, inclusive as 613 publicadas.
O que marca uma linha publicada é o par `publicacao_fingerprint` + `publicada_em`
(613/613 preenchidos). Quem procurar `estado='publicada'` vai contar zero e concluir
errado — já aconteceu.

Cada promoção fica ligada ao lote privado de proveniência
`clube_novo.bonificador_lote_publicacao_v1`. O lote registra contrato, fingerprint,
estado e evidência; a cópia integral anterior de cada linha fica em
`clube_novo.bonificador_promocao_publicacao_snapshot_v1`. O rollback documentado
restaura somente esses campos de promoção e não apaga resultados já calculados.

## Ciclo operacional: Extrator → Bonificador

O Bonificador não é uma fila eterna e não recalcula uma linha que já foi
confirmada. Em 31/08/2026, a rodada aberta pelo operador calculou e confirmou
**613 linhas**. O contrato canônico voltou a **0 pendências**: cada uma dessas
linhas recebeu seu resultado em `clube_novo.build_bonificador` e deixou a fila.

Por isso, abrir o **Extrator** depois de uma rodada concluída não repete nem
altera esses 613 resultados. O propósito dele é trazer cartas novas ou suas
atualizações. Uma linha aparece na **Fila do Bonificador** quando possui resultado
concluído do Otimizador (`build_otimizador_id` presente e
`estado_otimizador='concluido'`) e ainda não possui resultado do Bonificador
(`build_bonificador_id` vazio). A identidade é a própria `build_linha_card.id`; não
há marcador, recorte de lote ou fila manual. Se o Bonificador estiver iniciado, ele
consulta a fila a cada 5 segundos e capta linhas novas sem recriar batch.

Um resultado Bonificador ligado à linha, inclusive quando o bônus total é `0`,
significa que ela já foi processada e fica fora da fila. A ausência de vínculo é o
único estado pendente; o writer trava a linha e devolve readback idempotente se outra
instância já a confirmou. A publicação continua sendo um gate separado.

Em resumo: **Extrator prepara dados novos; Bonificador calcula os bônus das
linhas novas prontas; linhas confirmadas ficam gravadas e não voltam para a
fila.** Apenas abrir qualquer uma das telas não cria, recalcula ou grava uma
linha.

## O que a tela mostra enquanto roda

Na aba **Fila do Bonificador**, a lista inicial contém as cartas e funções prontas
para receber bônus. Ela mostra nome da carta, coleção, overall, função e posição por
extenso. A aba separada **Fila de resultados** mostra somente o resultado real da
rodada: corpo, pé ruim, estilo, IA, total e bloqueio, se houver. A aba usa os resultados
confirmados no banco, portanto continua mostrando a identidade humana mesmo depois que
a linha deixa a lista de pendências. A tela não mistura
pendência com resultado nem inventa valores.

Os textos do aplicativo são UTF-8 de ponta a ponta: tanto o componente local quanto a
janela WinForms leem a resposta do contrato em UTF-8. Portanto, acentos e as 613 linhas da fila não dependem de arquivo de texto,
navegador ou conversão manual. O botão **Parar normalmente** termina a rodada atual e
impede a próxima, sem travar a janela.

## Fila canônica V6

O Bonificador usa `public.bonificador_contexto_fila_v6`, contrato privado que
lista diretamente as linhas canônicas em `clube_novo.build_linha_card` cujo Otimizador
já concluiu e cujo Bonificador ainda não existe. A identidade permanece em
`build_linha_card.id`; não há marcador, recorte de teste, lote do Otimizador ou
dependência de `bonificador_par`. Isso não consulta uma fila externa.

Motor e aplicativo local leem `bonificador_regua_v3`, `bonificador_carta_v2`
e a fila V6. O escritor `gravar_build_bonificador_v5` é transacional, aceita
somente linha que ainda tenha a marca canônica e confere identidade, gates,
versões, fingerprints e a soma das parcelas. Ele não publica nem cria lote.

Recuperação: `BONIFICADOR/SQL/ROLLBACK-FILA-BONIFICADOR-V4.sql`, antes de
haver resultado. Snapshot: `BONIFICADOR/RECUPERACAO/2026-08-31-ANTES-FILA-OPERACIONAL-V4`.

## Desempenho: o teto de tempo e o ritmo real (04/09/2026)

Em 04/09 o lote parou de iniciar. A mensagem era enganosa:

```
ERRO DE CONTRATO: contrato recusou a consulta (500):
{"code":"57014","message":"canceling statement due to statement timeout"}
```

Isso **não** é credencial, rede nem contrato recusado. É um cronômetro que
ninguém tinha declarado. Três causas somadas, todas medidas em `begin … rollback`:

### 1. O teto de 8 segundos

O `service_role` não tinha `statement_timeout` próprio e herdava o do
`authenticator`. Toda RPC do Bonificador tinha **8 segundos** para terminar.

```
authenticator ... statement_timeout=8s · lock_timeout=8s
service_role .... (sem nada — herdava os 8s)
```

Corrigido: `alter role service_role set statement_timeout = '60s'` +
`notify pgrst, 'reload config'`. O `anon` (3s) e o `authenticated` (8s), que são
os papéis da tela pública, **não** foram alterados.

### 2. Faltava índice para o critério da fila

O INSERT do snapshot varria `build_linha_card_build_otimizador_id_key` inteira
(57.950 linhas, 336 mil buffers) para achar as elegíveis. Migração
`indice_fila_bonificador_elegivel_v5`:

```sql
create index build_linha_card_bonificador_elegivel_v5_idx
on clube_novo.build_linha_card (id)
where build_otimizador_id is not null
  and estado_otimizador = 'concluido'
  and build_bonificador_id is null;
```

É exatamente o critério hoje projetado por `bonificador_contexto_fila_v6`, do bloco `elegiveis`
de `bonificador_lote_status_v1` e do INSERT do sincronizador — os três passaram a
usar o mesmo índice. INSERT de 28.152 itens: **6,43 s → 2,03 s**.

### 3. ⛔ O sincronizador rodava a cada linha reservada

Esta era a grande. `bonificador_lote_proxima_linha_v1` chamava
`clube_novo.bonificador_lote_sincronizar_itens_v1` **antes de cada reserva**.

```
reservar a linha em si .......... 4,6 ms
o sincronizador antes dela ...... 10.170 ms
```

O sincronizador varre as dezenas de milhares de elegíveis e reconcilia o snapshot
inteiro. Fazer isso por linha é o trabalho do lote todo repetido a cada linha.

Migração `bonificador_proxima_linha_sincroniza_so_quando_a_fila_seca`: a função
tenta primeiro o **caminho rápido** (pegar um item já pendente, ~5 ms) e só chama
o sincronizador **quando não há mais pendente** — que é justamente o momento em
que faz sentido procurar linha nova do Otimizador.

Semântica preservada: nada é apagado, nada é pulado, a reserva continua atômica
com `for update … skip locked`, e linha que deixou de ser elegível nunca é
escolhida (o filtro da própria reserva a exclui).

```
reservar 1 linha:  10.170 ms  →  60 ms
```

### O ritmo real, medido em produção

Com as três correções, na Máquina 2, contra o banco pela rota HTTPS:

```
78 linhas por minuto, constante   (~0,77 s por linha)
antes: ~10,5 s por linha
```

Para 53.857 linhas pendentes: **~11h30**, contra 6 dias e meio no ritmo antigo.

⚠️ O custo restante por linha é quase todo **ida-e-volta de rede**, não conta: são
5 chamadas HTTPS por linha (`proxima_linha` → `regua` → `carta` → `gravar` →
`registrar`). A conta do Bonificador em si é milissegundos. Quem quiser acelerar
mais ataca a rede, não o cálculo — o motor já sabe falar direto com o Postgres se
o `config.txt` trouxer `BONIFICADOR_DATABASE_URL` e o `psycopg` estiver instalado.

### Como destravar um lote preso em `rodando`

Se a janela do motor for fechada sem `Ctrl+C`, o lote fica em `rodando` e o
próximo `iniciar` é recusado — **e isso não é defeito, é a trava funcionando**:

```
ERRO DE CONTRATO: contrato recusou a consulta (400):
{"code":"P0001","message":"lote não pode iniciar no estado rodando"}
```

`iniciar` só aceita `preparado` ou `pausado`. A saída é a sequência oficial, nesta
ordem, **nunca um UPDATE na mão**:

```sql
select public.bonificador_lote_controlar_v1('pausar');            -- rodando  -> pausando
select public.bonificador_lote_assentar_parada_v1(<lote>,'pausar'); -- pausando -> pausado
```

Depois disso o `RODAR-LOTE-BONIFICADOR.bat` volta a aceitar `S`. Nenhum item e
nenhum resultado se perde: o que tem readback confirmado está gravado, e o item
que ficou em `processando` volta para `pendente` no próximo `iniciar`.

🔑 **A lição, e ela vale para o sistema inteiro:** toda RPC de lote no Supabase
corre contra um cronômetro que ninguém declarou. O padrão de falha é sempre o
mesmo — funciona por meses, a tabela cresce, e um dia a operação passa do teto e
o erro que aparece é `57014`/500, que parece contrato recusado, credencial ou
rede, e não é. Ao ver `57014`: medir a operação em `begin … rollback` primeiro e
conferir o `statement_timeout` do papel, antes de mexer em qualquer código.

> Este é o manual oficial de funcionamento do Bonificador. O checklist e a pasta
> `4-DOCUMENTOS/BONIFICADOR` guardam a prova técnica, SQL de recuperação e auditorias;
> este documento explica o que o motor faz no jogo e como ele opera com segurança.

## Leitura rápida

O **Bonificador** acrescenta quatro parcelas de bônus a uma carta quando ela é usada
numa função de jogo: leitura corporal, pé ruim, estilo de jogo e estilos de IA. Ele não
cria atributos novos nem muda a carta. Ele apenas lê a fotografia canônica da carta,
aplica a régua vigente e prepara o resultado para a build do Otimizador.

O pipeline do Bonificador usa sua própria fila, mas **nenhuma carta é gravada ao abrir
a tela**. Ele só toca uma linha depois do clique do operador e quando os gates canônicos
da carta e da régua a devolverem como apta.

### O que ele lê da carta

| família da carta | leitura em linguagem de jogo | para que serve no bônus |
|---|---|---|
| corpo | as 12 medidas físicas da carta | compara cada medida com o molde da função e calcula a parcela corporal |
| pé ruim | frequência de uso e precisão do pé não dominante | determina a parcela de pé ruim pela régua vigente |
| posição principal | a posição principal da carta, como GO ou CA | escolhe qual dos dois slots de estilo manda naquela posição |
| dois playstyles | o playstyle físico de cada slot | decide a casa do estilo e a ativação complementar do outro slot |
| estilos de IA | os bits de IA ativos na carta | soma a parcela de IA conforme a régua |

**Não entram no cálculo atual:** os 26 atributos de carta, habilidades, posições
secundárias, técnico, clube, liga, nacionalidade, tipo de carta e ímpetos. Eles não são
tratados como zero: simplesmente não pertencem a esta fórmula.

### O papel das regras do Bonificador

- **Régua** é a receita publicada para o motor: reúne os parâmetros, as regras de
  playstyle, os slots dominantes por posição e os gates.
- **Molde corporal** é o perfil de uma função. Ele diz como as 12 medidas são lidas,
  com direção, pesos e cortes já aprovados. O Bonificador não altera esse conteúdo.
- **Parâmetros** são os valores da régua, como tetos e escalas do pé ruim, estilo e IA.
- **Regra de playstyle** liga um playstyle físico às posições em que ele ativa no
  jogo. A comparação é feita por IDs de playstyle e posição, não por nome, função
  interna ou casa do molde.

### Uma carta só segue quando é segura

O Bonificador trabalha em modo **fail-closed**: se uma relação estiver incompleta, sem
catálogo apto ou sem regra comprovada, a carta fica marcada como “não sei” e não entra
no payload de gravação. Ele nunca consulta a fotografia legada para completar um dado e
nunca inventa zero para uma ausência.

### Origem canônica e contratos

O motor de lote não abre tabelas diretamente. Ele lê `bonificador_regua_v3`,
`bonificador_carta_v2` e `public.bonificador_contexto_fila_v6`, e grava somente
por `public.gravar_build_bonificador_v5`. Esses contratos usam
IDs físicos/canônicos para carta, posição, playstyle, corpo e função. A referência
legada sobrevive apenas como fotografia de auditoria e recuperação, fora de gates e da
decisão do motor.

O aplicativo local usa o login `bonificador_runtime`, restrito a essas quatro RPCs.
Assim a janela continua sem credencial de administrador e sem acesso a tabela; ela fala
somente com o componente local e este chama contratos versionados.

O motor de lote permanece em `2-MOTORES/BONIFICADOR/motor_bonus.py`. O ponto normal de
uso é o batch físico `RODAR-LOTE-BONIFICADOR.bat`, que chama
`OPERACAO-LOCAL-LOTE/PROCESSAR-FILA-BONIFICADOR.bat` e mantém o console aberto com o
progresso. O aplicativo `Bonificador ClubEfootball.exe` é somente uma consulta visual
separada; não substitui a tarefa em lote. Testes, SQL e recuperação permanecem em
`4-DOCUMENTOS/BONIFICADOR`, fora do runtime.

### Auditoria, paridade e recuperação

Antes de uma troca de origem, a versão anterior é fotografada. A auditoria compara
cardinalidades, gates, fingerprints e resultado das regras contra a referência de
sombra; divergências são registradas por carta e campo. A aplicação e o rollback são
ensaiados em transação antes do readback. As rotinas e os artefatos estão em
`4-DOCUMENTOS/BONIFICADOR/SQL` e `4-DOCUMENTOS/BONIFICADOR/RECUPERACAO`.

## 1. Finalidade e nome

O **Bonificador** calcula quatro parcelas separadas para cada par `card_id × função`:
corpo, pé ruim, estilo de jogo e estilos de IA. O runtime V9 preserva exatamente essas
parcelas, mas prepara a saída para `clube_novo.build_bonificador`. O estilo agregado é
acompanhado das duas contribuições dos slots físicos que já formavam o mesmo total;
isso não muda a fórmula.

`motor_bonus.py` e `motor dos bônus` são nomes técnicos históricos. O nome de produto
e de documentação é **Bonificador**.

O Bonificador não escolhe barrinhas, técnico, habilidades ou ímpetos. Essas famílias
podem existir na carta e no modelo novo, mas não são entradas da fórmula atual do
Bonificador.

## 2. Arquitetura ativa

| responsabilidade | origem ativa em 07/09/2026 |
|---|---|
| motor de lote incremental | `2-MOTORES/BONIFICADOR/motor_bonus.py` |
| aplicativo local de consulta e controle | `2-MOTORES/BONIFICADOR/Bonificador ClubEfootball.exe` |
| payload interno de compilação | `2-MOTORES/BONIFICADOR/windows-app/assets/BonificadorComponente.bin` |
| receita | `public.bonificador_regua_v3()` |
| carta | `public.bonificador_carta_v2(card_id)` |
| fila canônica **sem lote** | `public.bonificador_contexto_fila_v6(limit, offset)` — paginada, usada quando não há lote explícito |
| **reserva atômica em modo lote** | `public.bonificador_lote_proxima_linha_v1(lote)` — uma linha por vez, `for update … skip locked` |
| **confirmação do item do lote** | `public.bonificador_lote_registrar_v1(lote, linha, estado, total, motivo)` — idempotente |
| controle do lote | `public.bonificador_lote_controlar_v1('iniciar'\|'pausar'\|'parar')` · `public.bonificador_lote_assentar_parada_v1(lote, modo)` · `public.bonificador_lote_status_v1()` |
| gravação preparada | `public.gravar_build_bonificador_v5(p_resultado jsonb)` |
| destino | `clube_novo.build_bonificador` ligado à linha exata em `build_linha_card` |

⚠️ **A tabela acima esteve incompleta até a v1.16.** Ela listava só a
`contexto_fila_v6` e dava a entender que era por ela que o motor pegava trabalho.
Não é, em modo lote. Quando `operacao_lote.py` exporta `CLUBEF_BONIFICADOR_LOTE_ID`,
o `motor_bonus.py` reserva **uma linha por vez** com
`bonificador_lote_proxima_linha_v1` e confirma cada uma com
`bonificador_lote_registrar_v1`; a `contexto_fila_v6` só é usada no modo sem lote.
A allowlist do `interface/servidor.py` (nove RPCs) cobre a **janela de consulta**, e
não o motor — as duas RPCs do lote não estão nela e mesmo assim são o caminho vivo.
Foi essa leitura parcial que fez uma sessão declarar as duas como código morto.

`RODAR-O-MOTOR.bat` e `RODAR-TUDO.bat` executam somente o Otimizador
(`roda_lote_v6.py`). Eles não executam o Bonificador.

O arquivo executava tudo no corpo do módulo. A chave vinha de `config.txt`, não era
gravada nem impressa. O lote produtivo não foi executado nesta migração.

## 3. Mapa técnico das entradas e sua proveniência histórica

| entrada do cálculo | origem antiga | significado | fonte canônica nova | chave/gate |
|---|---|---|---|---|
| corpo da carta | `clube.carta_jogo.corpo` via `carta_do_motor` | 12 medidas usadas pela régua física | `clube_novo.carta_corpo_jogo` + `corpo_ordem` | (`card_id`,`codigo_corpo`); 12 relações; catálogo `pode_rodar` |
| ordem do corpo | `clube.corpo_ordem` via `regua_bonus` | posição de cada medida no vetor | `clube_novo.corpo_ordem` | `codigo`; `pos`; `usado_pelo_motor`; `pode_rodar` |
| molde do corpo | `clube.molde_corpo` | regra ClubEfootball por função, medida, peso e cortes | `clube_novo.bonificador_molde_corpo` | (`funcao_id`,`corpo_pos`); 228 regras operacionais, 12 por função; valores copiados fielmente |
| referência externa do molde | rótulo humano de `molde_corpo.funcao` | liga o par técnico ao molde, sem participar da matemática | `clube_novo.funcao_sistema.id` | 19 IDs aptos; motor, molde e regra de estilo comparam somente o ID |
| índice da medida no molde | ausente no JSON antigo | localiza a mesma medida no vetor corporal | `clube_novo.corpo_ordem.pos` | 228/228 regras resolvidas; 12 índices únicos por função |
| uso do pé ruim | `clube.carta_jogo.pe_ruim_uso` | valor físico do bit 478, largura 2 | `clube_novo.carta_pe_jogo` | (`card_id`,`campo=pe_ruim_uso`); valor 0–3; catálogo `clube_novo.pe` apto |
| precisão do pé ruim | `clube.carta_jogo.pe_ruim_precisao` | valor físico do bit 578, largura 2 | `clube_novo.carta_pe_jogo` | (`card_id`,`campo=pe_ruim_precisao`); valor 0–3; catálogo `clube_novo.pe` apto |
| pesos do pé ruim | `clube.bonus_parametro` | conversão dos dois valores e teto | `clube_novo.pe.valor_bonus` | (`campo`,`valor`); nove valores aptos; igualdade comprovada com a régua antiga |
| posição principal | `clube.carta_jogo.posicao` + `clube.posicao` | posição que escolhe o slot de estilo | `clube_novo.carta_posicao_principal_jogo` + `posicao_jogo` | (`card_id`,`posicao_id`); exatamente uma relação; catálogo apto |
| playstyle do slot 1 | `slot_ofensivo_id` + `clube.estilo_jogo` | estilo físico gravado no primeiro slot | `clube_novo.carta_playstyle_jogo` + `playstyle` | (`card_id`,`slot_fisico=1`); `playstyle_id=id_jogo`; catálogo apto |
| playstyle do slot 2 | `slot_defensivo_id` + `clube.estilo_defensivo` | estilo físico gravado no segundo slot | `clube_novo.carta_playstyle_jogo` + `playstyle` | (`card_id`,`slot_fisico=2`); `playstyle_id=id_jogo`; catálogo apto |
| regra de estilo | `clube.estilo_regra` + `posicao_slot` | fotografia histórica de casa/ativação | `clube_novo.bonificador_regra_playstyle` + `bonificador_posicao_slot` | `playstyle.id_jogo`, `posicao_jogo.id` e `da_bonus`; a V11 não usa `funcao_id` para ligar o bônus |
| estilos de IA | JSON `clube.carta_jogo.estilos_ia` | quantidade de bits de IA ligados na carta | `clube_novo.carta_estilo_ia_jogo` + `estilo_ia` | (`card_id`,`bit_estilo_ia`); catálogo pelo bit físico e `pode_rodar` |
| pares card × função | `clube.build` | universo histórico já calculado | `clube_novo.build_linha_card` filtrado pela prontidão vigente | `build_linha_card.id`, `card_id`, `funcao_id`, `posicao_id`; fonte operacional V6, sem `clube.build` nem `bonificador_par` |
| parâmetros não físicos | `clube.bonus_parametro` | tetos e pesos da regra ClubEfootball | `clube_novo.bonificador_parametro` | 14 valores preservados, sem semântica por texto legado |
| saída | `clube.build.b_*` via writer legado | fotografia histórica | `clube_novo.build_bonificador` via `gravar_build_bonificador_v5` | writer canônico e resultado imutável |

As dimensões de nacionalidade, clube, liga e tipo, as habilidades, as posições
secundárias, os técnicos e os ímpetos foram inventariados e deliberadamente não entram
na fórmula vigente. Sua existência no modelo novo não autoriza adicioná-los ao cálculo.

## 4. Contratos seguros e versionados

A aplicação não lê `clube_novo` diretamente. A migração cria somente três portas
allowlisted em `public`, todas `SECURITY DEFINER`, com `search_path` vazio, referências
qualificadas e `EXECUTE` apenas para `service_role`:

- `bonificador_regua_v3()` — receita allowlisted, chaves estáveis e gates;
- `bonificador_carta_v2(card_id)` — somente os campos usados pelo Bonificador, com
  proveniência, cardinalidades, completude vigente, versões, fingerprints e
  `pode_rodar`;
- `public.bonificador_contexto_fila_v6(limit, offset)` — identidade exata da
  linha marcada, card, função, posição e fingerprints calculados pelo banco.

`PUBLIC`, `anon` e `authenticated` não recebem execução. Nenhuma tabela de
`clube_novo` é exposta e nenhuma policy/RLS existente é alterada.

O runtime produtivo não chama mais `public.gravar_bonus` e não escreve em
`clube.build`. Para cada resultado apto ele chama exclusivamente
`public.gravar_build_bonificador_v5`, que relê a completude, confere identidade,
selos, parcelas, total e ligação, tudo na mesma transação. O retorno só é aceito se
trouxer `readback=ok`, a mesma linha, os mesmos selos e um fingerprint SHA-256.
`bonus_fisico_detalhe` leva a contribuição efetiva de cada medida e sua soma decimal
precisa ser exatamente igual a `bonus_fisico_total`. A última medida recebe somente o
residual de arredondamento. `bonus_posicao` é zero porque posição condiciona a regra
atual, mas não soma uma quinta parcela; as contribuições dos slots 1 e 2 somam
exatamente o mesmo bônus de estilo agregado da V8.

## 5. Gates e ausência de fallback

Uma carta só pode ser gravada quando todos estes gates passam:

1. a carta existe em `clube_novo.carta_jogo`;
2. há exatamente 12 medidas corporais usadas pelo Bonificador;
3. pé, posição principal e playstyles têm cardinalidades normalizadas `3/1/2`;
4. corpo, pé, posição, playstyles e IA resolvem em catálogos com `pode_rodar=true`;
5. os dois valores de pé ruim resolvem na régua física nova;
6. a regra do playstyle possui ponte estável;
7. todas as quatro parcelas são numéricas;
8. a carta está apta na completude vigente e os fingerprints coincidem;
9. o par traz o ID da linha, função e posição exigidos pelo writer novo.

Falha de RPC, relação incompleta, catálogo bloqueado ou regra sem ponte deixa a carta
em `NAO-SEI.txt` e exclui todos os seus pares da chamada ao writer novo. O código
não volta a `carta_do_motor`, não usa o JSON antigo e não transforma ausência em zero.

## 6. Divergências conhecidas da fotografia antiga

No universo comum há 42.803 cartas antigas e 43.072 novas; 269 existem somente no
modelo novo. A comparação integral encontrou:

- corpo: 23 valores divergentes, distribuídos em 12 cartas;
- pé ruim: uma precisão divergente (`176844`);
- IA: duas cartas com cardinalidade nova maior (`155498` e `176844`);
- posição principal: três cartas divergentes;
- slot 1: três cartas divergentes;
- slot 2: oito cartas divergentes.

Essas divergências são registradas por `card_id`, campo, origem e valor no checklist e
na auditoria. A fonte nova é a fotografia física/canônica atual; a fotografia antiga é
referência de sombra, não fallback.

As relações normalizadas foram auditadas mesmo quando não participam da fórmula:

| relação | linhas | cartas | cardinalidade por carta presente | uso pelo Bonificador |
|---|---:|---:|---:|---|
| atributos | 1.119.872 | 43.072 | 26 | não usa |
| corpo | 516.864 | 43.072 | 12 | usa |
| habilidades | 179.189 | 33.521 | 1–10 | não usa |
| estilo de IA | 54.435 | 24.854 | 1–5 | usa; ausência significa nenhum bit ligado |
| posições | 516.864 | 43.072 | 12 | não usa a lista; usa a relação principal 1/1 |
| ímpetos | 3.748 | 2.641 | 1–2 | não usa |

As relações adicionais efetivamente consumidas têm cobertura integral: pé
`129.216 = 3 × 43.072`, playstyles `86.144 = 2 × 43.072` e posição principal
`43.072 = 1 × 43.072`. Elas têm zero divergência contra os escalares canônicos,
que permanecem somente como contraprova do gate.

## 7. Ponte canônica aplicada aos moldes corporais

O v7 recebe `funcao_codigo` técnico, como `centroavante_fixo`, porém
`regua_bonus()` e o contrato v1 antes da ponte indexavam `molde_corpo` pelo rótulo
`Centroavante fixo`. O match direto é `0/19` funções usadas e, na referência,
os 17.798 pares devolvem corpo ausente. O v7 seguia somando as outras parcelas;
isso era fallback silencioso e não pode ser preservado nesta migração.

O usuário autorizou corrigir exclusivamente essa referência. O contrato agora usa
`clube_novo.funcao_sistema.id` como identidade canônica e publica o mesmo molde sob o
ID esperado pelo motor. A associação histórica
`codigo_legado → nome_legado` foi usada uma única vez para materializar o snapshot;
não é lida em runtime. A medida resolve o índice físico `clube_novo.corpo_ordem.pos`.

Nenhum peso, corte, direção, ordem, composição ou operação matemática foi alterado.
A auditoria confirmou:

- 19/19 funções, com IDs canônicos únicos e `pode_rodar=true`;
- 228/228 regras e índices resolvidos, 12 por função;
- 17.798/17.798 referências externas resolvidas;
- zero divergência estrutural entre o molde por nome e o molde por código/ID;
- zero divergência matemática nos 17.795 pares com carta no modelo novo;
- três referências sem carta nova continuam sem cálculo e sem fallback.

## 8. Playstyle 291 resolvido pelo dado físico

No modelo novo, raw `140 / 4 = índice 35` resolve fisicamente para
`playstyle.id_jogo=291` (`Goleiro adiantado`). A regra foi materializada por esse ID,
não pelo rótulo histórico. Iker Casillas `88045755827028` lê `291` no slot 1 e `336`
(`Goleiro ofensivo`) no slot 2; a posição GO manda no segundo slot e a mesma fórmula
entrega `1,5`. A carta está apta e não há bloqueio por nomenclatura.

## 9. Histórico da migração canônica anterior e trava global

Esta seção registra a migração canônica anterior à V11. Naquela operação era
proibido alterar fórmulas, pesos, cortes, moldes ou regras. Em 07/09/2026 houve
autorização específica posterior para corrigir **somente** a parcela de estilo;
corpo, pé ruim, IA, pesos, cortes e moldes continuaram intactos.

As operações matemáticas, pesos, cortes, ordem e arredondamentos das funções do arquivo
permanecem iguais ao snapshot. `bonus_do_corpo` trocou apenas a busca de chave do mapa
para aceitar `funcao_id`, e o chamador passa esse ID a `bonus_do_corpo` e
`bonus_do_estilo`; não há alteração aritmética. Três comportamentos pré-existentes ficam
documentados separadamente:

- `regua_bonus()` não devolvia `casa`/`liga`, embora o código as lesse; o resultado era
  zero silencioso. O contrato canônico atual entrega as mesmas regras reindexadas por
  IDs;
- a referência código técnico → rótulo do molde estava quebrada e foi corrigida pela
  ponte canônica autorizada, sem tocar no conteúdo do molde;
- `molde_corpo.direcao` é numérico (`-1/0/1`), enquanto o código histórico testa o
  texto `"-"`. Esta migração não corrige essa fórmula.

Nenhuma UI, Otimizador, Extrator, ímpeto, dado do jogo ou lote produtivo é alterado.

## 10. Auditoria e recuperação

O checklist oficial, SQL de aplicação, rollback, readback e auditoria permanente ficam
em `4-DOCUMENTOS/BONIFICADOR`. O snapshot anterior do executável fica em
`4-DOCUMENTOS/BONIFICADOR/RECUPERACAO/2026-08-28-ANTES-REGUA-CANONICA-CLUBE-NOVO`.

O consumidor `casa_tela` permanece intacto. A validação visual do aplicativo local é
registrada em `4-DOCUMENTOS/BONIFICADOR/INTERFACE-LOCAL.md`; ela não toca a UI
principal, o Otimizador ou o Extrator.

## 11. Estado operacional e gates

O caminho efetivo lê `bonificador_regua_v3`, `bonificador_carta_v2` e
`bonificador_contexto_fila_v6`. A gravação normal passa somente por
`gravar_build_bonificador_v5`; o lote corretivo explícito usa
`gravar_build_bonificador_correcao_v1`. As relações de `clube_novo` continuam privadas: a
janela não recebe URL de banco, chave, schema nem acesso direto a tabela.

`funcao_id` liga o par ao molde corporal. A ativação do playstyle usa exclusivamente
`posicao_id`; `funcao_codigo`, casa e rótulos humanos não ligam nem desligam essa
parcela. Carta incompleta, catálogo sem `pode_rodar`, fingerprint divergente ou contrato
indisponível deixam a linha bloqueada. Não existe fallback legado.

Quando não há linha apta, o motor fica em **aguardando** e consulta a fila novamente.
Ele não fabrica fila, checkpoint, cache ou resultado local. Um lote produtivo continua
dependendo dos gates e da autorização operacional; este manual não autoriza dispará-lo.

## 12. Aplicativo local único

Abra somente **Bonificador ClubEfootball.exe** pelo ícone. Ele é uma janela nativa do
Windows: não abre Edge, navegador nem página web. Ao abrir, o EXE cria um componente
interno temporário em porta livre de `127.0.0.1`, confirma o `ping` e mostra a janela.
O componente não é um segundo aplicativo: fica invisível, é encerrado junto com a
janela e sua cópia temporária é apagada ao fechar.

A raiz `2-MOTORES/BONIFICADOR` contém um único `.exe`. O motor-fonte, o servidor-fonte
e os arquivos de compilação permanecem porque são necessários para manutenção; runtime
portátil, cache Python, interface web, lançadores `.bat` paralelos e logs automáticos
não fazem parte do pacote operacional.

### O que a tela mostra

- **Fila do Bonificador:** estado, progresso, linha atual, pendentes, calculadas,
  confirmadas, eventos e pares retornados pela fila V5.
- **Testar uma carta:** consulta somente leitura de corpo, pé ruim, posição principal,
  slots 1 e 2 de playstyle, IA, molde, régua, parcelas e gates.
- **Auditoria e paridade:** contrato, proveniência, cardinalidades e fingerprints.

As consultas rodam em segundo plano. A fila V5 e a régua são verificadas
separadamente: a fila não consulta a régua apenas para montar rótulos. Se a régua
falhar, a tela continua mostrando a fila já lida como **Fila disponível; régua
indisponível** e mantém o início bloqueado. Se a fila falhar, a tela mostra **Fila
indisponível**. Assim ela não mistura uma fila existente com erro de contrato. A janela
permanece responsiva; o tempo máximo de uma chamada local é de dez segundos.

Se o contrato responder que a credencial foi recusada, a tela mostra a mensagem do
componente local e mantém o início bloqueado. A correção é atualizar a credencial
privada de serviço no `2-MOTORES/config.txt`; não há fallback para legado, acesso direto
ao schema ou uso de credencial no navegador.

## 13. Operação segura

O botão **Iniciar Bonificador** inicia o único processo local do motor. O botão
**Parar normalmente** pede que ele conclua a rodada atual e não inicie outra. Mantenha
um único escritor Bonificador para o mesmo banco.

Falha de rede, contrato ou gate nunca vira sucesso silencioso. A linha sem todos os
insumos canônicos permanece fora da gravação, marcada como ausência conhecida, sem
valor inventado. Fórmulas, pesos, ordem de cálculo, moldes e regras de jogo não são
alterados pela aplicação.

Para recuperação, auditoria e prova de paridade, consulte
`4-DOCUMENTOS/BONIFICADOR/INTERFACE-LOCAL.md`, o checklist oficial e
`4-DOCUMENTOS/BONIFICADOR/RECUPERACAO`. A limpeza do pacote único tem recuperação em
`RECUPERACAO/2026-08-31-ANTES-LIMPEZA-PACOTE-UNICO`.

## 14. Correção física V10 — regra vigente

### Fórmula física aprovada

A V10 corrige a incompatibilidade registrada na seção 9. Para cada medida, os
quatro cortes produzem exatamente as faixas `-2, -1, 0, +1, +2`; o valor igual ao
corte fica na faixa encerrada por esse corte (`valor <= corte`). A direção do molde
é sempre o inteiro `-1`, `0` ou `+1`:

- direção `+1`: conserva o sinal da faixa;
- direção `-1`: inverte o sinal;
- direção `0`: aparece com contribuição zero no detalhe e fica fora do numerador e
  do máximo possível;
- o peso multiplica a contribuição; por isso `altura` com peso `5` pode valer
  `-10`, `-5`, `0`, `+5` ou `+10` pontos;
- o máximo é a soma de `2 × peso` somente das medidas com direção ativa;
- `percentual = clamp(soma / máximo, -1, +1)` e
  `bônus físico = clamp(percentual × 1,5, -1,5, +1,5)`.

O detalhe persiste as 12 medidas e a soma decimal delas precisa fechar exatamente
com `bonus_fisico_total`. A prova adicional guarda `corpo_soma`, `corpo_maximo` e
`corpo_pct`. O caso-ouro obrigatório é Messi `89136409091415` × função `14`:
físico `+0,9750`, soma `13`, máximo `20`, percentual `0,65` e altura `+0,75`.

Identidade vigente:

- motor `v11-0709-estilo-posicao-oficial-v1`;
- régua `bonificador-regua-v3`;
- fórmula SHA-256
  `2e80a07d51f2bc8f456f9710c82717d38e3142cb3d52fd325b7b587c58ed2879`;
- writer normal `public.gravar_build_bonificador_v5(jsonb)`;
- writer de staging `public.gravar_build_bonificador_correcao_v1(uuid,jsonb)`.

### Fluxo obrigatório e sem mistura de versões

O único caminho operacional de composição é
`clube_novo.finalizar_publicar_linha_v1(bigint,text)`. A função é interna e é
acionada por gatilhos quando chega o segundo resultado da linha, seja ele do
Otimizador ou do Bonificador. O complemento posterior dos 26 atributos também
dispara a mesma função. Um cron consome a fila durável com `SKIP LOCKED` para
recuperar qualquer evento perdido.

Na mesma transação e sob trava da linha, a finalizadora:

1. exige produção, zero pendências, dois resultados concluídos e compatíveis;
2. exige Bonificador `v11-0709-estilo-posicao-oficial-v1` com a fórmula aprovada;
3. valida os 26 valores do vetor efetivamente usado e o `arows_snapshot`;
4. calcula a nota normalizada do Otimizador e soma `bonus_total` V10;
5. grava todos os campos `nota_*`, os fingerprints e a proveniência;
6. substitui somente a linha correspondente no read model incremental;
7. ativa a ponte pública somente depois do readback interno fechar.

Não existe mais corte, reversão para V9, publicação em lote ou refresh global. Se
um motor ainda não terminou, a linha fica aguardando; se houver incompatibilidade,
fica fora da publicação com diagnóstico durável. Linhas já publicadas com a mesma
dupla de resultados são idempotentes.

A migração de 2026-09-05 foi autorizada porque a geração pública de origem tinha
zero linhas em readback. O arquivo canônico recusa outro ambiente cuja origem não
esteja vazia; nesse caso, uma migração separada deve semear e validar a ponte antes
de mudar qualquer leitor.

### Operação em duas máquinas

A pasta oficial editável fica na Máquina 1. A Máquina 2 executa um espelho no mesmo
caminho. Nunca copie arquivos avulsos por memória e nunca leve somente o EXE.
Transfira o pacote portátil completo pelo gerenciador de arquivos do AnyDesk e, na
Máquina 2, siga esta sequência:

1. feche o Bonificador e confirme que não há processo do componente local;
2. coloque o pacote em uma pasta temporária, fora da pasta oficial;
3. execute `APLICAR-ATUALIZACAO.bat` e informe a raiz oficial. Ele valida a raiz e
   os hashes do pacote, cria backup, copia exclusivamente o manifesto e confirma os
   hashes pós-cópia; ele nunca inicia produção;
4. execute `VALIDAR-MAQUINA-2.bat` para provar arquivos, versão, fórmula e caso-ouro
   sem reservar ou gravar linha;
5. depois de a migração estar aplicada e do lote correto estar preparado, use
   `INICIAR-REPROCESSAMENTO.bat`, informe o UUID e digite `REPROCESSAR`;
6. use `OPERAR-CORRECAO-FISICA.bat status <UUID>` para acompanhar e `pausar <UUID>`
   para a pausa cooperativa;
7. não há comando posterior de corte: cada linha aparece automaticamente quando os
   dois motores forem validados pelo banco.

O EXE oficial V2.0.28, o `BonificadorComponente.bin`, `interface/servidor.py` e
`motor_bonus.py` são uma unidade de versão. O recurso incorporado no EXE deve ter o
mesmo SHA-256 do componente ao lado do fonte. A operação corretiva mantém estado
visível, pausa cooperativa e confirmação do lote, mas não oferece controles de
publicação manual ou restauração de resultado incorreto.

## 15. Correção V11 — referência anterior à decisão de 09/09

A descrição abaixo registra a regra V11. A política aprovada para a próxima
implantação está na seção 16: ela substitui a escolha do slot principal por
posição e a promoção genérica do secundário quando o principal é Básico.

A parcela de estilo não depende da função criada pelo ClubeEfootball. Ela depende
somente de o estilo de jogo ativar na posição escolhida, conforme o texto do jogo.
O slot que manda continua valendo `1,0`, o outro slot continua valendo `0,5` e o
teto continua em `1,5`. Se o slot que manda estiver em Básico, o outro assume a
parcela cheia. Corpo, pé ruim, IA, moldes e pesos não mudam.

Identidade vigente: motor `v11-0709-estilo-posicao-oficial-v1` e fórmula
`2e80a07d51f2bc8f456f9710c82717d38e3142cb3d52fd325b7b587c58ed2879`.
Os resultados V10 já calculados são reaproveitados: somente as duas parcelas de
estilo e os selos derivados são reconciliados no banco; não se roda novamente o
Bonificador inteiro.

### Readback de encerramento da correção publicada

Em 07/09/2026, a leitura direta confirmou:

- zero publicação ainda exibindo valor de estilo diferente do V11;
- zero item prioritário dessa correção aguardando;
- zero item prioritário dessa correção com erro;
- linha `405776`, processada na Máquina 2, persistida com motor V11,
  `b_estilo=1,0` e `b_total=2,0958`;
- o lote integral permaneceu `rodando`, com 91.657 linhas preparadas e 100.978
  pendentes no instante do readback.

Publicações que ainda exibiam selo V10, mas tinham valor numericamente idêntico ao
V11, não foram tratadas como erro de pontuação. A fila automática pode republicá-las
gradualmente para renovar a proveniência sem mudar a nota.

## 16. Regra de estilos aprovada em 09/09/2026 — implantação pendente

O documento canônico desta decisão é
[Regra de estilos aprovada em 09/09](BONIFICADOR/REGRA-ESTILOS-APROVADA-0909.md).
Ele contém a classificação das 19 funções, as duas exceções e exemplos esperados.

- A função define qual slot é principal; a posição escolhida define a ativação.
- Principal ativo vale 1,0; secundário ativo vale 0,5; Básico ou inativo vale zero.
- Não há promoção geral do secundário. Somente Defensor Criativo nas funções de
  zagueiro e Lateral Defensivo na função Lateral defensivo recebem 1,0 quando
  são o único estilo ativo. Dois estilos ativos continuam limitados a 1,5.
- Pressão recuada, Marcador forte, Defensor recuado e Goleiro construtor ficam
  pendentes de definição de posições. Na consulta de 09/09, os quatro tinham zero
  cartas vinculadas, cadastro inativo e nenhuma regra de ativação. Nenhum deles
  apareceu nas 43.451 cartas da extração examinada.
- Uma extração futura que forneça a definição permite validar e cadastrar essas
  posições na tabela existente `clube_novo.bonificador_regra_playstyle`. A simples
  aparição de uma carta vinculada não prova todas as posições de ativação.

Nesta revisão foram salvos os critérios aprovados no manual e no banco, com
calculadora interna de conferência e 25 casos numéricos validados. A execução V11, as parcelas
gravadas e a publicação não foram migradas por esta alteração documental.
