# Manual do Extrator eFootball

## Atualização dos arquivos do jogo, versão 5.4.0.2

Se o CPK local tiver hash diferente do contrato, a varredura abre seus membros
obrigatórios, verifica a presença e a divisibilidade pelos tamanhos de registro
contratados e salva `atualizacao-fonte.json`. Esse diagnóstico contém os hashes
anteriores e observados e as contagens por arquivo. A janela identifica a
atualização e mantém o envio bloqueado. Estrutura compatível não comprova ainda
o significado de todos os campos: `validacao_semantica_concluida=false`.

A fonte nova só pode participar da comparação e da aplicação após a revisão
do contrato. Não substituir o hash antigo cegamente nem remover a verificação.

## Correções manuais do usuário

O valor registrado em `clube_novo.valor_do_dono` prevalece inclusive quando
o jogo informa outro valor. A conferência do envio respeita essa decisão;
outros campos continuam atualizáveis. O relatório mostra os campos protegidos.
Consulte [Prioridade das correções manuais](../../4-DOCUMENTOS/EXTRATOR/PRIORIDADE-CORRECOES-MANUAIS.md).

## Carga retomável e confirmação de conclusão, versão 5.4.0.1

Cada lote é gravado, relido e confirmado separadamente. Se a carga falhar,
os lotes já confirmados permanecem no banco. Preserve o mesmo pacote para a
retomada. Uma falha não significa que nenhuma escrita ocorreu.

O registro `clube_novo.aplicacao_pacote_revisao_extrator` passa por três estados:

- `aplicando`: carga em andamento ou interrompida antes de completar os lotes.
- `aguardando_conferencia`: lotes concluídos, confirmação independente pendente.
- `aplicado`: leitura integral por nova conexão passou e a conclusão foi gravada.

`aplicado_em` fica vazio durante a execução nova e só recebe a data após a
conferência. A evidência fica em `auditoria_familias.readback_independente`.
Os registros anteriores permanecem históricos; esta correção não certifica
retroativamente cargas antigas. A tela informa a possibilidade de carga parcial
quando não consegue confirmar a conclusão.

Esta seção substitui descrições históricas de transação única para a aplicação
integral de cartas. Níveis, boxes e instalação de proteção têm fluxos próprios.

## Registro de 09/09/2026 — estilos aguardando definição

Pressão recuada (87), Marcador forte (95), Defensor recuado (96) e Goleiro
construtor (34) permanecem pendentes de posições de ativação. Na auditoria de
09/09, tinham zero cartas vinculadas no banco, estavam inativos no catálogo e
não apareceram nas 43.451 cartas da extração examinada. Isso não garante o
mesmo estado em versões futuras.

Quando uma extração futura fornecer a definição, preservar arquivo, registro,
campo e versão de origem; validar as posições antes de completar
`clube_novo.bonificador_regra_playstyle`. Uma carta com o estilo não comprova
sozinha a lista completa de ativação. Não inferir posições pelo nome, não
registrar uma lista vazia como se significasse incompatibilidade confirmada.

A decisão está em `clube_novo.bonificador_politica_estilo`, versão
`estilos-funcao-20260909-v1`. Consulte
[Regra aprovada e pendências](../../4-DOCUMENTOS/BONIFICADOR/REGRA-ESTILOS-APROVADA-0909.md).
Este registro documental não implementa monitoramento automático nem altera o
executável do Extrator. A versão operacional abaixo permanece a mesma.

**Versão operacional:** 5.4.0.2 (protocolo desktop 5.4.0)

**Estado:** aplicativo desktop autônomo; varredura somente leitura; envio de dados e proteção dos motores são ações explícitas, separadas e conferidas

**Pasta operacional:** `7-VARREDURA-DO-JOGO`

As seções marcadas como V4.6 ou V5.1 abaixo preservam o histórico de como o
contrato e os leitores foram validados. Elas não descrevem os cliques atuais.
Para o uso diário, siga **Operação autônoma diária** e **Revisão manual e
sequência de cliques**.

## Níveis máximos e orçamentos — V5.3.0.2

O botão **EFHUB: PRÓXIMO LOTE** funciona com o jogo fechado. Ele pede ao banco
até 100 `card_id` ainda não conferidos, abre a sessão do próprio site e consulta
`https://efhub.com/api/public/players/{card_id}`. A resposta só é aceita quando
`id`, `playerId` e o ID pedido são iguais e `levelCap` é um inteiro de 1 a 99.

Cada lote guarda o nível e o orçamento anteriores, a resposta validada, URL,
hash, horário e o valor novo. O orçamento gravado é sempre
`2 * levelCap - 2`. Valores já existentes também são comparados e reescritos
quando divergirem; a operação não se limita a campos vazios. Uma evidência da
memória do jogo prevalece: se o eFHUB divergir dela, o item vira
`conflito_fisico` e o cadastro não é sobrescrito.

Depois da comparação, entradas antigas do Otimizador que fotografaram outro
orçamento são substituídas no lote corretivo. Publicações dessas linhas são
retiradas somente depois de a linha nova existir. O mesmo clique grava o resumo
do reparo e faz uma leitura independente do banco. Falhas de rede ficam no
checkpoint; nenhuma falha é convertida em nível 1.

A ordem do catálogo é: cartas especiais atualmente classificadas como
evolutivas, especiais atualmente classificadas sem evolução e cartas base.
Dentro de cada grupo, overall decrescente. Cartas que já possuem entradas ou
resultados do motor vêm antes das demais para que erros publicados sejam
corrigidos cedo. O nível confirmado pelo lote passa a determinar a classificação
real da fila seguinte.

O lançador continua sendo `ABRIR-EXTRATOR.cmd`, que abre `Extrator eFootball.exe`.
Com o jogo aberto e suas coleções carregadas, use **INICIAR VARREDURA**. A família
**Níveis reais** localiza automaticamente o processo, a base do executável e os
vetores registrados no contrato. A leitura não escreve no jogo.

Em **VER RESULTADO**, abra **Conferir níveis e orçamentos por carta**. O relatório
mostra o máximo observado, o orçamento correspondente e os valores do cadastro.
**ATUALIZAR NÍVEIS** grava somente os IDs capturados e cadastrados, depois de
reconferir contrato, executável, provas e identidades. O botão só fica disponível
após uma captura válida. A gravação é transacional e a confirmação usa outra
conexão ao banco. A credencial protegida já configurada no aplicativo é reutilizada.

O orçamento é `2 * nível máximo - 2`: máximo 1 produz orçamento **0**, sem valor
substituto. O nível atual pertence à instância e não substitui o máximo da carta.
Uma carta não observada continua **pendente**; ausência não significa nível 1 nem
ausência de evolução. A frase da tela “Impossível desenvolver mais” isolada não
classifica uma carta, pois também aparece quando o saldo de pontos está zerado.

A leitura dos arquivos físicos abrange o cadastro, enquanto a coleta de níveis
abrange somente os vetores carregados na sessão: cartas próprias, listas das boxes
e lista de recrutamento StandardDraft/Procurable. A captura guarda contagens,
total informado e índice de página; não presume cobertura completa por esses
valores. Jogo fechado, versão não reconhecida, mudança da sessão ou contrato
incompatível deixam essa família pendente e preservam as demais leituras.

Artefatos da rodada: `niveis-runtime.json`, `niveis-runtime-pacote.json`,
`niveis-runtime.html` e, após gravação confirmada, `niveis-runtime-aplicacao.json`.
O [mapeamento físico de níveis](MAPEAMENTO-NIVEIS-RUNTIME.md) descreve origem,
offsets, contrato, cobertura e verificações. O nível não é atribuído a `Player.bin`.

## Regra estrutural

O Extrator preserva a lógica de extração validada. A V5.3 acrescenta a operação
desktop autônoma e a proteção separada dos motores; não muda fórmula, sequência,
semântica nem regra de leitura do jogo.

> **A tabela/catálogo canônico de `clube_novo` diz o que deve ser buscado e onde está o dado. O Extrator valida, lê, compara e devolve um relatório.**

Onde o código antigo tinha bit, offset, largura, arquivo, tamanho de registro ou cardinalidade escritos diretamente, o caminho V4.6 recebe o valor equivalente das tabelas de `clube_novo` e do pedido ativo de leitura. Primitivas genéricas de CPK, WESYS, little-endian, bitfield e UTF-8 podem permanecer no código; elas não são autoridade semântica.

## Regra de continuidade da varredura

A varredura não é uma validação “tudo ou nada”.

Para cada família, o banco informa o conjunto solicitado. O Extrator tenta obter todos os itens e registra:

- encontrado e igual ao banco;
- encontrado, mas alterado;
- solicitado pelo banco e não encontrado;
- encontrado fisicamente, mas ainda ausente do pedido do banco;
- duplicado;
- erro de leitura restrito àquela família.

Uma divergência de conteúdo **não interrompe as famílias seguintes**. Ela bloqueia somente a aplicação da família afetada e permanece visível no relatório e no manifesto.

Exemplo:

```text
Ímpetos solicitados pelo banco: 440
Encontrados fisicamente: 438
Ausentes: 172, 315
Novos: nenhum
Resultado da família: aplicação bloqueada
Resultado da varredura: continuar para Dimensões, clubes, ligas, tipos e cartas
```

Cardinalidades como `440`, `407`, `2.072`, `696`, `35`, `1.478`, `214` ou `8` não são regras permanentes no código. O valor vigente é obtido das tabelas canônicas na própria execução.

Só constituem bloqueio estrutural geral:

- impossibilidade de obter um contrato ativo e íntegro;
- impossibilidade de abrir o executor local;
- ausência da conexão de leitura quando a família depende do banco;
- fonte física inteira indisponível para todas as famílias que dependem dela;
- arquivo incompatível com o fingerprint/tamanho exigido pelo contrato.

Mesmo nesses casos, o bloqueio deve identificar as famílias afetadas e preservar os resultados já obtidos.

## Regra de responsividade — V4.6.12

A leitura física de dezenas de milhares de cartas não pode monopolizar a thread visual do navegador.

A V4.6.12 preserva a mesma lógica e os mesmos resultados da extração, mas divide o trabalho pesado em lotes cooperativos. Entre os lotes, o Extrator devolve o controle ao Microsoft Edge para que a interface continue pintando o progresso, aceitando rolagem e respondendo ao Windows.

Foram tornadas cooperativas, sem alterar a semântica:

- desofuscação e abertura WESYS;
- decodificação contratual de `Player.bin` e arquivos relacionados;
- composição das 43 mil cartas;
- leitura de slots, atributos, relações e corpo;
- geração das linhas canônicas e do CSV de comparação;
- comparação das cartas com a fotografia do banco;
- leitura e validação de nacionalidade, clube, liga, tipo e vínculos.

O leitor contratual também passou a separar previamente campos diretos e campos derivados por máscara, evitando refazer o mesmo filtro para cada registro.

A mudança é exclusivamente operacional: bits, offsets, transformações, cardinalidades solicitadas, valores produzidos e regras de bloqueio continuam vindo do contrato e dos catálogos canônicos. A responsividade não autoriza pular registros nem reduzir a leitura.

## Conferência intermediária obrigatória — V4.6.11+

A leitura e a escrita são etapas separadas.

```text
Leitura física e comparação
        ↓ nenhuma escrita
Área intermediária de conferência
        ↓ mostra iguais, novos, alterados, ausentes e duplicados
Preparação do pacote aprovado
        ↓ gera review_id temporário e vinculado à fotografia atual
Confirmação explícita do usuário
        ↓ somente o escopo mostrado
Aplicação no clube_novo
```

Regras:

1. a abertura do Extrator e a varredura nunca gravam automaticamente;
2. o painel **Conferência antes do banco** mostra as divergências de Metadados, Cartas e relações;
3. a conferência de Dimensões lista exatamente as tabelas incluídas e as famílias excluídas;
4. abrir ou atualizar a conferência é uma operação somente leitura;
5. o servidor gera um `review_id` temporário, válido por 30 minutos e amarrado à fotografia e ao readback atuais;
6. a aplicação exige o mesmo `review_id`, a marcação de que a conferência foi revisada e a frase exata;
7. nova leitura invalida a conferência anterior;
8. conferência usada, vencida ou pertencente a outra fotografia não pode ser aplicada;
9. família divergente permanece fora do pacote;
10. nenhuma exclusão de linha é autorizada por esse fluxo.

O botão de Dimensões aplica somente:

- `clube_novo.nacionalidade_jogo`;
- `clube_novo.clube_jogo`;
- `clube_novo.liga_jogo`;
- `clube_novo.tipo_carta_jogo`;
- vínculos físicos correspondentes em `clube_novo.carta_jogo`.

Esse botão não aplica Ímpetos, Técnicos, Textos, Habilidades nem relações normalizadas de cartas.

### Cartas e relações

A divergência de uma relação de carta não deve aparecer apenas como `HTTP 409`.

Na V4.6.12, o retorno de `card_relations.py` permanece preservado como relatório revisável. O Extrator continua até gerar o diff das cartas, mostra a família divergente e amostras linha a linha, mas não cria pacote de envio enquanto as relações não forem exatas.

## Autoridade das referências

As referências físicas ficam nos próprios catálogos/tabelas, entre eles:

- `atributo_jogo`;
- `habilidade_jogo`;
- `playstyle`;
- `posicao_jogo`;
- `nacionalidade_jogo`;
- `clube_jogo`;
- `liga_jogo`;
- `tipo_carta_jogo`;
- tabelas de técnico;
- tabelas de ímpeto.

O contrato ativo sela versão, arquivos atuais, fingerprints, campos permitidos e catálogos participantes. Sem referência canônica válida, a família correspondente não pode ser aplicada. Não existe fallback produtivo para endereço antigo escrito no código.

```text
clube_novo: pedido, tabela e catálogo
        ↓ campos, códigos e referências físicas
Extrator
        ↓ tenta ler tudo e registra cada resultado
relatório por família
        ↓ conferência explícita
somente famílias exatas podem ser aplicadas
```

## Contrato ativo em 29/08/2026

O contrato `clubef-dt870-2026-r1`, versão `r1`, foi fechado para leitura e validação controlada após a reconciliação da cadeia V4.6.

Estado documentado na ativação:

- 214 campos ativos;
- 12 arquivos obrigatórios com fingerprint;
- cadeia de consumidores condicionais ainda bloqueada durante a validação;
- pedido fornecido por `clube_novo.obter_pedido_leitura_contrato_ativo()`.

A ativação libera leitura e comparação. Ela não constitui aprovação automática de uma nova carga.

## Aplicativo Windows e executável oficial

`7-VARREDURA-DO-JOGO/Extrator eFootball.exe` é o aplicativo Windows oficial. Seu código-fonte fica em:

- `windows-app/ClubEfootballExtractorLauncher.cs`;
- `windows-app/COMPILAR-APLICATIVO.ps1`.

A versão operacional é V5.3.0. O único fluxo de abertura é
`ABRIR-EXTRATOR.cmd` -> `Extrator eFootball.exe` V5.3.0 ->
`executor/desktop_worker.py`. O launcher cria uma pasta única em
`artefatos/desktop/`, chama o worker com `--root`, `--run-dir` e `--cancel`,
e mostra os eventos JSON de progresso. Ele não abre navegador, localhost nem
servidor HTTP.

O launcher também envia `--protocol-version 5.3.0`. O worker declara a mesma
versão e falha fechada antes de abrir banco ou fonte se o selo for diferente;
assim EXE, launcher e runtime não podem operar misturados.

O worker recebe o pedido selado em transação somente leitura, cria
`pedido-leitura.json`, `fontes.json`, `baseline-cartas.csv`, as fotografias
físicas, `resultado-normalizado.json` e `resultado.json`. Todo evento e
resultado registra `database_write: false`; o worker devolve o resultado
normalizado ao fluxo de `clube_novo`, sem criar uma carga manual paralela.

### Leitura humana e rastreabilidade por execução

Depois de gravar o `resultado.json`, o worker gera, na mesma pasta
`artefatos/desktop/run-...`, o `resultado.html` e o
`manifesto-execucao.json`. O botão **VER RESULTADO** abre apenas o HTML no
navegador padrão; ele nunca abre o JSON técnico no Bloco de Notas. O HTML é
permanentemente **humano-primeiro**: mostra primeiro cartas/jogadores,
habilidades, estilos de IA, posições, atributos, clubes, ligas,
nacionalidades, técnicos, textos e ímpetos com os rótulos já disponíveis nos
artefatos da própria execução. Esses rótulos são obtidos somente depois da
comparação, por consulta exata da chave canônica já presente no resultado; um
nome nunca identifica, une ou altera registros.

A página começa pelo resumo e organiza os exemplos em grupos fechados de dados
do jogo e, dentro deles, pelo tipo de mudança. Cada grupo mostra dez exemplos
por vez e libera os próximos sob demanda, para abrir rapidamente mesmo quando
o resultado técnico é grande. Cada assunto recebe um nome concreto para o
operador, como **Listas e nomes usados pelo jogo** ou **Arquivos necessários
para a leitura**; a tela principal não usa o rótulo vago “Informações técnicas
para investigar”. IDs,
chaves, bits, hashes, arquivos, offsets, valores brutos e demais diagnóstico
ficam exclusivamente no expansível **Detalhes técnicos** de cada exemplo. As
contagens vêm da varredura integral do resultado salvo; o limite é somente de
apresentação, explicitado na página.

O manifesto preserva `execution_id`, data, versão do programa, selo do pedido,
fingerprints de contrato/fontes, estado por família e nomes dos artefatos. A
renderização é local e somente leitura: não relê o jogo, não consulta o banco
e não altera dados de domínio.

## Prontidão de sincronização integral

`resultado.json` contém `sync_readiness`, calculado contra as famílias
obrigatórias do próprio pedido. Para cada chave de família, o gate exige:

- contrato completo de leitor, schema de saída e normalizador versionado;
- campos com tipo, identidade estável, schema de envelope e prova física ou
  `convencao_aprovada` rastreável;
- fotografia física concluída;
- fotografia, comparação e classificação por chave canônica/procedência
  concluídas; uma comparação informa integridade técnica, mas não aceita nem
  rejeita alteração de conteúdo por contagem.

Uma única família ausente, pendente ou com violação técnica torna o resultado
integral `incomplete`. Divergência de conteúdo é classificada como `novo`,
`removido`, `alterado`, `repetido` ou `inválido`, com chave e procedência; não
é decisão de busca do Extrator. O estado de Dimensões não libera Cartas,
Relações, Ímpetos, Técnicos, Textos nem Catálogos.

O pedido define o que deve ser lido e a leitura sempre percorre tudo que ele
declara. Diagnósticos e avisos não alteram nem selecionam registros durante a
varredura. Somente depois da leitura, mudanças `novas` ou `alteradas` com
destino, chave, tipo e procedência completos ficam disponíveis em **ESCOLHER O
QUE ENVIAR**. O pacote selecionado ainda exige aprovação e aplicação separadas;
abrir o aplicativo, iniciar a varredura ou visualizar o relatório nunca concede
permissão de escrita.

## Varredura integral, sem teto de cardinalidade — 29/08/2026

O pedido define **endereços, layout, leitor, tipo, catálogo e procedência**;
nunca define quantos registros o leitor pode ler. Para cada arquivo/campo
solicitado, o leitor percorre integralmente o conteúdo físico atual conforme o
layout declarado. Isso vale para cartas e seus atributos, corpo, posições,
habilidades, estilos, nacionalidades, clubes, ligas, tipos, textos, técnicos,
ímpetos, efeitos, condições, faixas, membros, classes e demais relações.

Contagem anterior, snapshot e expectativa versionada são somente observações
posteriores no relatório por chave/procedência. Não filtram, truncam, rejeitam
nem selecionam registros durante a leitura. Uma atualização com menos ou mais
linhas gera diagnóstico por chave/procedência; não é mascarada pelo runtime.

`executor/servidor_v4612.py` e `executor/servidor_v4612_hotfix.py` são
entradas históricas aposentadas. Elas não executam patches textuais de UI nem
iniciam uma varredura. Atalhos `INICIAR-EXTRATOR-V46.cmd` apenas encaminham
para `ABRIR-EXTRATOR.cmd` por compatibilidade.

Quando `ClubEfootballExtractorLauncher.cs` ou `desktop_worker.py` mudar,
execute `windows-app/COMPILAR-APLICATIVO.ps1` para instalar o EXE V5.3.0
correspondente. O botão `4-BAIXAR-DO-GITHUB.bat` sincroniza o código e
recompila o aplicativo, preservando `config.txt`.

## Descoberta automática das fontes físicas

O fluxo normal não pede ao usuário para localizar CPKs.

Raízes conhecidas:

- atualização do jogo: `C:\ProgramData\KONAMI\eFootball\ST\Download`;
- Steam x86: `C:\Program Files (x86)\Steam\steamapps\common\eFootball`;
- Steam alternativa: `C:\Program Files\Steam\steamapps\common\eFootball`.

Fontes:

- `dt870_updated`: `dt870_console_win.cpk` da atualização;
- `dt200`: `dt200_console_all.cpk`;
- `dt870_original`: `dt870_console_win.cpk` da instalação;
- `dt261_bra`: `dt261_bra_console_win.cpk`.

O `all.str` fica dentro do `dt261_bra_console_win.cpk`.

## Caminhos ativos

### Cartas e Dimensões

`app/contrato-v46-runtime.js` conduz o caminho produtivo das cartas. Dados básicos, nacionalidade, clube, liga, tipo, indisponibilidade, atributos, habilidades, estilos de IA, aptidões, corpo e slots usam referências canônicas.

Dimensões usam `Country.bin`, `Team.bin`, `CompetitionUnit.bin`, `CompetitionEntry.bin`, `Player.bin` e `PlayerDeleteList.bin`, conforme o contrato.

`executor/card_relations.py` continua somente leitura. A V4.6.12 captura seu retorno de conflito como relatório, mostra as famílias divergentes e impede a criação do pacote de cartas até a aprovação integral.

#### Estilos de IA: projeção observada e monitorada

Os bits de Estilo IA que já aparecem fisicamente em `Player.bin` são uma
**projeção observada**, nunca a alegação de um catálogo mestre completo. A
identidade da relação é sempre `card_id` + bit físico, com registro, arquivo e
hash de procedência; o rótulo vindo de `clube_novo.estilo_ia` serve apenas à
apresentação. Um membro físico ativo fora da projeção produz alerta de revisão
por carta/procedência, não cria catálogo nem infere nome, e mantém somente a
relação afetada sem aplicação. As demais famílias continuam sua leitura e
comparação normal.

### Metadados

`app/metadata-v46-runtime.js` preserva a lógica das leituras físicas. `app/patches-v4610/metadata-family-safe.jsfrag` é aplicado pelo servidor ao carregar esse runtime. Habilidades, Ímpetos, Playstyles, Textos, Técnicos, nacionalidades e afinidades são extraídos em blocos isolados: falha física de uma família produz um catálogo de erro e a função continua nas demais.

`app/metadados-v46.js` fornece o painel intermediário. Ele recebe os relatórios de Metadados e Cartas, abre a conferência de Dimensões, exige revisão explícita e só então habilita a etapa final.

`executor/servidor_v46.py`, `executor/servidor_v4610.py` e
`executor/servidor_v4612.py` permanecem somente como referência histórica;
não são runtime, endpoint nem autoridade operacional. A execução atual é
inteiramente pelo worker desktop V5 e mantém a escrita produtiva bloqueada.

### Ímpetos

`executor/impetos_v4610.py` substitui, no caminho ativo, a validação legada com cardinalidades congeladas. Em cada execução, ele lê as tabelas:

- `impeto_jogo`;
- `impeto_atributo_jogo`;
- `impeto_condicao_jogo`;
- `impeto_condicao_faixa_jogo`;
- `impeto_condicao_parametro_faixa_jogo`;
- `impeto_condicao_nacionalidade_jogo`;
- `impeto_condicao_liga_jogo`;
- `impeto_condicao_clube_jogo`;
- `impeto_condicao_classe_jogo`;
- `impeto_condicao_liga_membro_jogo`.

Depois compara o conjunto solicitado com a fotografia física e devolve códigos ausentes, novos, alterados e duplicados. O retorno inclui `continue_pipeline=true`; divergência bloqueia a aplicação de Ímpetos, não a continuação da varredura.

#### Rótulo apresentado pelo jogo — 30/08/2026

O código de Ímpeto continua sendo a identidade técnica e a origem de cada slot
é sempre o `Player.bin` físico. O nome exibido ao usuário é outra evidência: o
Extrator só o mostra quando o pedido da própria execução declara a FK exata
`codigo_impeto -> secao_texto + id_texto` e essa chave existe em `all.str` com
arquivo, CPK e fingerprints físicos válidos. O relatório nunca usa
`impeto_jogo.nome_pt` ou `nome_en` históricos como substituto dessa ligação e
nunca fabrica um texto a partir dos efeitos.

Sem a FK física, a apresentação humana fica explicitamente como **“rótulo do
jogo ainda não comprovado”**; o código, a condição, os efeitos e a procedência
continuam recolhidos em **Detalhes técnicos**. Para a carta Vózinha
`106799462259226`, o slot físico 1 é o código `79` e os quatro bônus de
goleiro `+3` foram lidos corretamente de `PlayerBooster.bin`, mas o pedido
vigente deixa `secao_texto` e `id_texto` nulos. Assim, o Extrator não reaproveita
o rótulo histórico “Defesaça” nem monta “Defesa +3” por inferência; a ligação
oficial de texto precisa ser declarada e comprovada antes de aparecer no
relatório.

Há um segundo estado, deliberadamente distinto da prova do dicionário:
**rótulo operacional monitorado**. Ele só é usado quando `clube_novo.impeto_jogo`
traz simultaneamente um `nome_pt` revisado e o marcador
`rotulo_operacional_monitorado` em `falta_o_que`. Nesse estado o relatório
mostra o nome humano, mas conserva visível que a ponte oficial
`secao_texto/id_texto` ainda está pendente; o rótulo jamais é descrito como
físico nem participa da identidade do Ímpeto.

Os códigos `96`, `101`, `132`, `133`, `170`, `171` e `208` usam esse estado
para **Pacote total**. A base da revisão é o mesmo conjunto físico de 26
atributos e a confirmação visual do nome. O efeito não é `+3` fixo: os sete
códigos continuam condicionais, com faixas `1–13 = +1`, `14–19 = +2` e
`20–23 = +3`. A categoria especial `0` não pertence a essa associação. Uma
execução futura deve continuar alertando sobre a ponte textual oficial ausente,
sem preencher `secao_texto` ou `id_texto` por inferência.

Os 14 especiais de categoria física `0` usam um estado operacional ainda mais
explícito: `rotulo_operacional_confirmado_usuario`. Os códigos `56`, `57`,
`58`, `134`, `135`, `142`, `143` e `144` conservam os nomes exclusivos
confirmados individualmente; os códigos `250`, `261`, `263`, `265`, `266` e
`267` exibem, como rótulo operacional, o único atributo físico `+6` de cada
registro. Essa apresentação não cria identidade textual. Todos continuam com
`secao_texto` e `id_texto` nulos, `pode_rodar=false` e a pendência
`ponte_fisica_texto_codigo_pendente`. O código `261` pertence ao pacote de
atualização e é mantido no catálogo para monitoramento, mas Maeda Daizen não é
apresentado como carta lançada na fotografia atual.

O teste físico do DT870 atualizado (CPK SHA-256
`44df868c2613d532292d87072c0863a907d6a5f0cc40f914d355e56d74edfcc5`)
localizou os seis registros de atributo nos índices `200–205`, porém não
encontrou em seus 40 bytes, nem nas demais 96 entradas do CPK, um layout comum
`codigo_impeto -> secao/id_texto`. Os oito nomes exclusivos também não aparecem
como strings nesse CPK. Por isso a execução diária mostra os rótulos como
operacionais e continua alertando sobre a ponte, em vez de convertê-los em
texto físico comprovado.

#### DT870 Steam histórico: reconciliação fail-closed — 30/08/2026

O `PlayerBooster.bin` do DT870 Steam antigo não é decodificado com o layout
semântico da atualização atual. A fonte física observada contém prefixo de 24
bytes e 165 blocos de 40 bytes; os códigos e hashes de cada bloco são
preservados em `historical_source`, mas essa fonte não participa da união
canônica por código e não fornece condição, alvo, efeito ou faixa enquanto não
existir um decodificador legado fisicamente comprovado.

Os 22 registros candidatos ao deslocamento histórico foram relidos pelo número
de registro e hash: em todos, o código bruto é uma unidade menor que o código
histórico registrado. Esse padrão isolado não prova identidade semântica e não
autoriza uma regra global `+1`; há colisões com variantes atuais reais. O
validador os classifica separadamente como
`historico_deslocado_sem_prova_semantica`: não são escondidos, reconciliados ou
misturados às categorias novo/removido/alterado. A revisão de Ímpetos permanece
pendente apenas para esses registros, e nenhuma linha de domínio é modificada.

O caminho V5 não carrega mais `app/catalog-source-map.js`; o mapa local antigo
de índices não é autoridade operacional. O teste read-only confirmou 412
registros canônicos formados apenas por DT200/DT870 atualizado, zero registro
canônico com origem DT870 Steam, 165 registros históricos preservados e os 22
candidatos reproduzidos exatamente por código bruto, número de registro e
SHA-256.

### Técnicos

`executor/tecnicos_v4610.py` substitui, no caminho ativo, as contagens antigas fixas de técnicos, nacionalidades e afinidades. Ele lê o conteúdo atual das tabelas de `clube_novo`, compara os conjuntos completos e devolve um relatório com `continue_pipeline=true`. O arquivo `executor/tecnicos.py` permanece preservado como implementação legada.

### Textos e demais famílias

Textos e Dimensões são tratados separadamente. Falha ou divergência de uma família gera aviso e relatório; as demais continuam.

A aplicação continua manual, selada e restrita às famílias aprovadas.

## Segurança e sequência

1. consultar o contrato e os catálogos;
2. localizar as fontes;
3. executar todas as famílias possíveis em lotes cooperativos;
4. registrar ausentes, novos, alterados, duplicados e erros;
5. concluir a varredura mesmo com avisos;
6. carregar os resultados na área intermediária;
7. mostrar as divergências antes de qualquer escrita;
8. preparar somente o pacote aprovado e gerar `review_id`;
9. exigir revisão, aceite e frase exata;
10. aplicar apenas o escopo exibido;
11. fazer readback posterior;
12. somente depois liberar consumidores posteriores.

Nenhuma divergência deve ser escondida por fallback. Nenhuma família válida deve ser descartada porque outra falhou. Nenhuma escrita pode ocorrer apenas por abrir ou executar a varredura.

## Arquivos ativos

- `app/leitura-contrato.js` — fonte-base servida com decodificação cooperativa na V4.6.12
- `app/contrato-v46-runtime.js`
- `app/metadata-v46-runtime.js` — fonte-base servida com isolamento físico
- `app/metadata-v46-compat.js`
- `app/extrator-core.js` — fonte-base servida com operações cooperativas na V4.6.12
- `app/extrator-ui.js` — fonte-base servida com patches de continuidade, conferência e responsividade
- `app/revisao-intermediaria.js` — revisão do comparador normal e responsivo
- `app/metadados-v46.js` — painel intermediário obrigatório
- `app/patches-v4610/metadata-family-safe.jsfrag`
- `app/patches-v4610/post-json-report.jsfrag`
- `app/patches-v4610/family-block.jsfrag`
- `app/patches-v4610/status-block.jsfrag`
- `app/patches-v4610/card-relations-block.jsfrag`
- `app/patches-v4610/card-result-block.jsfrag`
- `executor/tecnicos.py` — validador legado preservado
- `executor/tecnicos_v4610.py` — validador ativo orientado pelo banco
- `executor/impetos.py` — validador legado preservado
- `executor/impetos_v4610.py` — validador ativo orientado pelo banco
- `executor/card_dimensions.py`
- `executor/card_dimensions_apply.py`
- `executor/card_impetus.py`
- `executor/card_relations.py`
- `executor/executor_local.py`
- `executor/servidor_v46.py`
- `executor/servidor_v4610.py`
- `executor/servidor_v4612.py`
- `INICIAR-EXTRATOR-V46.cmd`
- `windows-app/ClubEfootballExtractorLauncher.cs`
- `windows-app/COMPILAR-APLICATIVO.ps1`
- `Extrator eFootball.exe`
- `Extrator-ClubEfootball.html`

## Critério de conclusão

A migração termina quando:

- o pedido do banco determina os dados e cardinalidades;
- nenhum endereço semântico local atua como autoridade;
- cada família conclui ou registra seu próprio erro;
- uma divergência não interrompe famílias independentes;
- o relatório identifica ausentes, novos, alterados e duplicados;
- a interface continua respondendo durante a leitura integral;
- a área intermediária mostra as divergências antes da escrita;
- pacote algum pode ser aplicado sem `review_id` atual e aceite explícito;
- somente famílias aprovadas podem ser aplicadas;
- a leitura integral local e o fluxo de conferência foram testados e conferidos.

## Regra de documentação

Toda implementação, alteração ou exclusão no V4 deve atualizar este manual no mesmo conjunto de trabalho. Código e documentação divergentes são pendência, não conclusão.

## Pedido tipado e identidade de logística — 29/08/2026

O pedido novo é obtido somente por `clube_novo.obter_pedido_leitura_tipado_ativo()`.
Ele contém famílias, localizadores de fontes, leitor/versionamento, schema de
payload, tipo esperado, normalizador/versionamento, identidade, FK, nulidade,
serialização e expectativas versionadas. O desktop não escolhe caminho Steam,
papel de fonte, offset, enumeração ou prioridade: se uma fonte/família não estiver
no pedido, registra o estado e continua as independentes.

Todo registro físico é entregue no envelope `envelope_campo_v1`: valor bruto,
valor normalizado, tipo esperado, normalizador, identidade/FK e arquivo/hash/
registro/campo de origem. A chave de comparação é exclusivamente a identidade
canônica; rótulos legíveis são derivados por catálogo em apresentação e não servem
para identificar, unir, substituir ou carregar. A camada foi aplicada sem carga de
dados do jogo; a escrita produtiva permanece bloqueada.

## Política de revisão no contrato — 29/08/2026

Esta seção foi substituída pelo fluxo banco → leitura → resultado normalizado.
O pedido ativo não contém política de aprovação manual: divergências continuam
visíveis como diagnóstico, mas nunca interferem no universo físico solicitado.

## Fontes físicas e catálogos declarados — R2, 29/08/2026

O pedido tipado emite `papeis_fonte`, `precedencia_fontes` e
`catalogos_requeridos` por família. `dt200`, `dt870_original` e
`dt870_updated` são selados pelo SHA-256 do CPK informado pelo localizador do
banco; `dt261_bra` não é implícito e só é aberto pela família de Textos.
Precedência preserva procedência de comparação, não autoriza substituir fonte.

Mesmo uma fonte sem campo materializado é validada pelo hash do CPK, sem
inventar layout. Dependências auxiliares, como condições de Ímpeto, vêm no
pedido; ausentes nele fazem a família falhar fechada. A saída inclui selo de
fonte + contrato + payload por família.

## Catálogos e Cartas canônicos — 29/08/2026

`clube_novo.contrato_leitura_catalogo_fisico` cobre os 23 catálogos pedidos
na execução atual. Cinco têm chave física direta (`habilidade_jogo`,
`playstyle`, `posicao_jogo`, `nacionalidade_jogo` e
`afinidade_tecnico_jogo`); os demais declaram explicitamente qual validação
normalizada de Relações, Dimensões, Técnicos, Textos ou Ímpetos lhes dá
cobertura. O executor não guarda lista paralela: ausência, chave repetida ou
dependência não íntegra é `inválido` no resultado normalizado.

`clube_novo.contrato_leitura_projecao_cartas` declara a fonte física e a
coluna de destino para cada campo de Carta. O executor cria um baseline interno
somente leitura com essas colunas e compara por `card_id`; FKs de clube, liga,
nacionalidade, tipo e indisponibilidade são lidas de `dimensoes-fisicas.json`.
Títulos e rótulos legíveis não participam de identidade nem de carga. O rótulo
físico de `PlayerVariationDetail.bin` também não entra no CSV de cartas: ele é
somente uma prova auxiliar da variação individual da carta e nunca vira box ou
vínculo de oferta. A migração e rollback
cumulativos estão em `4-DOCUMENTOS/EXTRATOR/SQL/APLICAR-CATALOGO-FISICO-CONTRATO-V1.sql`
e `ROLLBACK-CATALOGO-FISICO-CONTRATO-V1.sql`.

O smoke integral read-only `preparacao-carga-integral-4-20260829-215407`
confirmou 43.072 Cartas sem diferença canônica, os 23 catálogos cobertos sem
novo/removido/alterado/repetido/inválido e nenhum `database_write`. O manifesto
normalizado é `f3c1806b09625d9c9472640160098d6effc9dce393e68f3c4dadcb2d3f3c66f0`.
As divergências classificadas de Relações e do catálogo de Ímpetos seguem como
diagnóstico do resultado; não suspendem a próxima leitura e não promovem
alteração automática de dados.

## Correção de fluxo — banco → leitura → resultado normalizado — 29/08/2026

O pedido ativo não contém mais `politica_revisao`, `cobertura_aprovada` nem
`carga_autorizada`. `clube_novo` declara campos, fontes, leitores, tipos,
normalizadores e FKs; o Extrator lê integralmente esses endereços e devolve um
`resultado-normalizado.json` selado por contrato, fonte e payload. As
divergências são diagnóstico de mudança, nunca um bloqueio de leitura ou uma
decisão externa sobre o que buscar. A migração reversível desta correção é
`4-DOCUMENTOS/EXTRATOR/SQL/APLICAR-FLUXO-SINCRONIZACAO-CONTRATO-V1.sql`.

### Retificação urgente — aprovação interna do Extrator

A aprovação não foi removida: `clube_novo` volta a fornecer
`politica_revisao`, e o worker produz `pacote-revisao.json`. A UI/fluxo do
próprio Extrator apresenta esse pacote ao usuário e registra o aceite antes de
qualquer aplicação posterior ao `clube_novo`. O gate controla exclusivamente a
aplicação; não seleciona nem suspende a leitura integral. Migração:
`APLICAR-APROVACAO-INTERNA-EXTRATOR-V1.sql`.

## Aplicador transacional após aceite V5 — 29/08/2026

O botão **ESCOLHER O QUE ENVIAR** abre uma lista na qual nada vem marcado. Só
dados `novos` ou `alterados` com destino, tipo, chave e procedência completos
podem ser marcados. Pendências conhecidas, registros históricos, remoções,
duplicidades e itens inválidos continuam no relatório, mas não são convertidos
em dados de envio. A escolha gera `pacote-selecionado.json` e
`plano-selecionado.json`, preservando o pacote original.

O botão **APROVAR PACOTE** da janela V5 invoca o worker local somente com
`pacote-selecionado.json`. Antes de registrar a decisão, o worker recalcula o SHA-256
do pacote, relê o contrato ativo, confere o selo completo (contrato, versão do
jogo, fontes e catálogos), confirma a cobertura técnica por família e verifica
as fontes declaradas. A decisão persistida contém exatamente o hash e o selo;
ela não autoriza qualquer outro pacote.

O botão **APLICAR PACOTE** chama o aplicador interno. Ele bloqueia se a decisão
não for do mesmo hash/selo/seleção, se qualquer fonte sumiu, se algum item
marcado deixou de ser representável ou se houver divergência no readback. Em uma única transação ele
estagia `execucao_leitura_contrato`, registra a auditoria por família em
`clube_novo.aplicacao_pacote_revisao_extrator`, lê de volta os selos e só então
teria permissão de confirmar os envelopes tipados. Identidade e FK são sempre
as chaves canônicas declaradas; rótulos nunca são usados como chave ou destino.

`PRODUCTIVE_WRITES_LOCKED` permanece verdadeiro no aplicativo, na varredura, na
visualização, na seleção e na aprovação. Somente o processo novo criado depois
da confirmação em **APLICAR PACOTE** recebe autorização efêmera para executar
os envelopes normalizados que o operador marcou. O smoke controlado usa a mesma
transação integral, força rollback e valida gate, estágio, auditoria e readback
sem confirmar dados reais. A migração e seu rollback são
`APLICAR-APLICADOR-TRANSACIONAL-EXTRATOR-V1.sql` e
`ROLLBACK-APLICADOR-TRANSACIONAL-EXTRATOR-V1.sql`.

### Smoke controlado

O smoke `smoke-aplicador-controlado-20260829-221610` exerceu o mesmo comando
de aprovação que a V5 chama, com pacote SHA-256
`7f6ed397c672a1cf99417034f3c5b1d2f46e6ad18efa4ed03926270c66cec18f`.
Depois, `--apply-review --test-rollback` confirmou estágio e readback da
auditoria e fez rollback integral. A decisão de teste foi restaurada para
`aguarda_aprovacao_no_extrator`. Pacotes adulterado e expirado foram recusados
antes da escrita. Nenhum dado de jogo, tabela de domínio, motor ou UI visual
foi alterado.
## Descoberta autônoma e aplicação declarativa — 29/08/2026

Em cada execução, o worker consulta o pedido ativo de `clube_novo`. A descoberta
física ocorre exclusivamente por `catalogo_endereco_leitura_extrator_v1`: a
view entrega a FK da família/campo, fonte/papel, arquivo, endereço, largura,
decodificador, catálogo, normalizador e procedência. O worker abre somente as
fontes devolvidas, lê o universo físico completo dos endereços solicitados,
normaliza por chave canônica e produz `resultado.json` e
`pacote-revisao.json` selados. Não há seleção manual de fonte, caminho Steam,
offset ou fallback de leitura no código.

O pacote mostra divergências por chave/procedência para revisão na V5. O aceite
na própria V5 é vinculado ao SHA-256 e aos fingerprints atuais; antes de aplicar,
o worker relê contrato, fontes, cobertura e selo. Escritores e destinos vêm de
`escritores_dominio` do pedido, com envelope
`clubef-envelopes-aplicacao-v1`; identidades e FKs são validadas antes de SQL
parametrizado derivado do contrato. Rótulos humanos não são aceitos como chave.

O smoke `smoke-catalogo-view-20260829-223810` percorreu as quatro fontes
declaradas e concluiu a conferência de todas as famílias sem escrita. Seu pacote
SHA-256 é `2eea6148608e9184869960d98fc8cdb7985e089f6ae5a56421d05419508cd156`.
O aceite e `--apply-review --test-rollback` confirmaram estágio, auditoria e
readback para os 29 destinos declarados, retornando rollback integral; o aceite
de teste foi restaurado. Nesse smoke, `PRODUCTIVE_WRITES_LOCKED=true` foi
mantido e nenhum dado real de jogo foi aplicado.

### Comparação canônica de Cartas — 29/08/2026

O leitor físico não compara CSV de apresentação. A comparação de Cartas ocorre
depois da leitura de Dimensões, com `projecoes_cartas` do pedido, `card_id` e
códigos/FKs canônicos. Nomes e rótulos de nacionalidade não geram falsos
deltas nem chegam à etapa de aprovação como decisão de domínio.
## Separação de catálogo, revisão e domínio — 29/08/2026

O fluxo operacional é: `view de catálogo` → leitura física → envelope/pacote
selado de estágio e revisão → aceite na V5 → transação para destinos canônicos
do `clube_novo`. O catálogo serve exclusivamente para localizar/decodificar e
nunca é escrito pelo Extrator. Tampouco são usados schema legado ou tabelas de
endereço/procedência como destino de dados.

O aceite é ligado ao hash do pacote. Antes de aplicar, o worker confere outra
vez contrato, fontes, chaves/FKs, cobertura e selo; a auditoria e o readback
ocorrem na mesma transação. Sem envelope declarado, destino declarado e aceite
válido, a execução falha fechada. A trava produtiva continua habilitada durante
o desenvolvimento.

## Retificação de ficha e totais do relatório — 30/08/2026

O runtime V46 normaliza `forma`, `pe_ruim_uso` e `pe_ruim_precisao` como
códigos numéricos declarados no pedido. A projeção CSV agora apenas transporta
esses códigos; ela não volta a interpretá-los por mapas de rótulos legados.
Em prova somente leitura com o `Player.bin` de `dt870_updated`, as 43.072
cartas tiveram zero diferença nesses três campos contra a fotografia canônica.

`resistencia_lesao` é uma composição física declarada de dois bits: os estados
ativos `Alta` e `Média` são normalizados pela precedência recebida no contrato.
Para o estado físico `00`, o runtime consulta o catálogo de textos físico já
selado no pedido e só aceita um nível-base quando encontra, na mesma seção,
uma sequência de IDs consecutivos `[nível-base, prioridade 1, prioridade 2]`
compatível com os dois rótulos declarados. Na execução atual, isso deriva
`Baixa` sem mapa local. Se a sequência não for unívoca, o runtime falha fechado
em vez de inventar rótulo. A prova read-only confirmou zero diferença nos quatro
campos para as 43.072 cartas: `10 → Alta` (4.806), `01 → Média` (32.783) e
`00 → Baixa` (5.483).

O relatório HTML apresenta antes de cada grupo o total real de entidades e de
diferenças. Para Cartas, por exemplo, a execução mostra
`43.072 cartas afetadas; 172.288 diferenças em 4 informações`; os 50/10 itens
renderizados são identificados explicitamente como exemplos paginados, nunca
como o total. A geração do HTML continua somente leitura sobre o
`resultado.json` já produzido.

## Habilidades: comparação por conjunto — 30/08/2026

Para `carta_habilidade_jogo`, a identidade de comparação é exclusivamente o
par canônico `card_id + skill_id`. A propriedade `ordem` que chega da leitura
física é preservada apenas como informação opcional de apresentação e
procedência: ela não é regravada, nem usada para escolher uma ordem visual, nem
entra no fingerprint lógico. Portanto, uma permutação pura da ordem não cria
`alterado`; uma habilidade ausente ou adicional continua classificada por sua
chave canônica.

O teste read-only do comparador usou o mesmo conjunto `{7, 9}` em ordens
distintas e retornou `exact_match=true`, `mismatch_count=0` e fingerprints
iguais. No controle `{7, 9}` versus `{7, 11}`, retornou exatamente uma
habilidade nova e uma removida. Não houve conexão ou escrita de domínio nesse
teste.

## Operação autônoma diária — atualizada em 31/08/2026

O fluxo normal do operador usa exclusivamente `ABRIR-EXTRATOR.cmd` (ou
`Extrator eFootball.exe`) na própria pasta operacional:

1. clicar **INICIAR VARREDURA** para criar uma nova execução somente leitura;
2. aguardar a conclusão e clicar **VER RESULTADO**;
3. ler primeiro **Resultado geral da varredura** e **O que você deve fazer
   agora**. Todo aviso responde, no próprio HTML: **O que significa**, **Afeta
   os dados de hoje?**, **Impede enviar alterações ao banco?** e **O que você
   deve fazer**. `Pendência já conhecida` continua visível até ser resolvida,
   sem ser chamada de falha da extração. `Registro antigo guardado como
   referência` explica que o item pertence a uma versão antiga e não é tratado
   como mudança do jogo atual;
4. se houver dados novos ou alterados, clicar **ESCOLHER O QUE ENVIAR**. Nada
   vem marcado: selecionar somente os itens que devem subir e criar o pacote;
5. conferir a quantidade marcada, clicar **APROVAR PACOTE** e confirmar;
6. somente depois, clicar **APLICAR PACOTE** e confirmar a ação separada;
7. usar **ABRIR LOG** para consultar o log persistido em `logs`.

A aplicação é permitida somente quando a execução terminou com confirmação
final, há dados atuais novos ou alterados disponíveis para seleção, o operador
marcou pelo menos um item, o pacote corresponde à execução atual e a aprovação
continua válida. Mesmo assim, **APLICAR PACOTE** exige uma confirmação separada
e repete as conferências antes da transação.

A aplicação não é permitida quando a varredura falhou ou ficou incompleta,
quando existe trava estrutural, quando o pacote/aprovação ficou desatualizado ou
quando o resultado é **nada para enviar**. Avisos conhecidos, registros antigos
e registros isolados pelo Radar V2 permanecem visíveis, mas nunca são caixas
marcáveis. Uma observação amarela que declara não bloquear outras mudanças não
impede selecionar e aplicar os demais itens comprovados.

Cada execução preserva em `artefatos/desktop/run-<data-hora>` o resultado
técnico, o HTML de revisão, o manifesto, o pacote selado e
`plano-aplicacao.json`. Falha de conexão, fonte ausente, erro do worker,
aprovação recusada ou aplicação recusada aparece na janela e também no log
local. Abrir o aplicativo ou iniciar a varredura nunca define a permissão de
escrita.

O plano de aplicação é fail-closed. Ele materializa apenas `UPSERT` cuja
família, tabela, chaves, colunas, tipos e procedência estão declarados no pedido
ativo do `clube_novo`. Remoções não são inferidas por ausência. Remoção,
duplicidade, item inválido, pendência conhecida, registro histórico ou mudança
sem destino físico unívoco permanece visível, mas não aparece como caixa
marcável. Uma falha estrutural do contrato bloqueia o pacote; uma observação
não selecionada não bloqueia os itens válidos marcados. O botão de aplicação só
injeta a autorização de escrita no processo criado depois da confirmação do
operador.

A aplicação usa uma única transação. Todos os valores gravados são relidos por
`SELECT` antes do `COMMIT`; qualquer diferença causa `ROLLBACK`. Depois do
`COMMIT`, uma segunda conexão relê os mesmos valores e grava no log o hash do
readback independente. O desenvolvimento e os testes desta entrega usam apenas
pacotes sintéticos e resultados salvos: não executam varredura viva nem
aplicação no banco.

## Registro histórico do encerramento do Extrator V5.1 — 30/08/2026

Esta seção preserva a prova da rodada que encerrou a V5.1; ela não informa a
versão atualmente instalada. A versão operacional atual está no início deste
manual. Naquela rodada, `Extrator eFootball.exe` V5.1.0.0 já comprovava o fluxo
de varredura somente leitura, relatório humano, seleção explícita, aprovação
separada e aplicação transacional separada. Nada vinha previamente marcado para
envio.

A execução real de fechamento foi `run-20260830-132440`, registrada em
`logs/extrator-desktop-20260830-132138.log`. O worker V5.1.0 iniciou às 13:24:40
e concluiu às 13:27:09. As quatro fontes obrigatórias foram localizadas. Foram
lidas 43.072 cartas, 72 habilidades, 11.679 textos e 1.478 técnicos, além das
demais famílias declaradas pelo pedido ativo.

As oito comparações registraram `classification_complete=true` e
`technical_integrity=true`. O resultado final teve:

- 0 dados novos;
- 0 dados alterados;
- 0 dados removidos;
- 0 duplicidades;
- 0 itens inválidos;
- 0 itens disponíveis para seleção;
- 0 envelopes de aplicação;
- 0 bloqueios no pacote.

O plano terminou em `no_changes`, com `database_write=false`. O log não contém
erro, falha, recusa ou traceback, e os 13 artefatos do manifesto conferiram em
tamanho e SHA-256. Portanto, nessa execução, não havia nada para subir e nenhuma
escrita automática foi feita.

Continuam visíveis uma pendência conhecida do catálogo completo de Estilos de
IA e 101 registros históricos de Ímpeto. Eles são observações preservadas para
auditoria: não são mudanças atuais, não viram dados de envio e não bloqueiam
outras mudanças válidas que venham a aparecer numa execução futura. Este
encerramento não afirma que os arquivos brutos do jogo são armazenados no banco
nem que a lista física completa de Estilos de IA foi localizada; afirma que as
partes cobertas e comparadas nessa rodada correspondiam ao estado salvo em
`clube_novo`.

## Inventário diário de variações de carta — V5.4 — 07/09/2026

A varredura diária pode detectar cartas pré-carregadas antes da liberação
pública. O módulo `radar-lancamentos.js` lê `PlayerVariationDetail.bin` e
preserva a relação física entre `card_id` e **rótulo da variação individual da
carta**. Esse texto não identifica uma box comercial e nunca entra em
`box_contexto_contratacao_v1`, `box_card_em_andamento_v1` nem no pacote de
publicação das boxes.

O artefato `radar-lancamentos.json` continua sendo uma comparação local entre
rodadas do arquivo: registra origem, hash, índice e rótulos adicionados ou
removidos. Os nomes internos antigos do contrato são mantidos apenas para ler
artefatos já produzidos. Nenhum resultado desse radar cria, renomeia, agrupa ou
finaliza uma box.

Registros vazios, bytes residuais, UTF-8 inválido e relações com cartas ausentes
da referência física ficam isolados ou bloqueiam a comparação conforme o
contrato do radar. Essas validações dizem respeito somente ao inventário de
variações de carta.

### Como reconhecer sucesso, aviso acompanhado e falha real

O estado de sucesso da janela é **conferência concluída — somente leitura**. O
botão **VER RESULTADO** deve abrir `resultado.html`, o texto inicial deve
declarar que nada foi alterado e a pasta da execução deve conter
`radar-lancamentos.json`. Uma execução pode ser válida e ainda mostrar avisos:

- **registro físico possui card, mas ainda não possui nome de box** é um aviso
  acompanhado. Só esse registro fica fora da conclusão de lançamento;
- **referência física antiga, fora dos lançamentos atuais** informa uma relação
  preservada para auditoria, mas fora do jogo atual;
- os dois avisos devem explicar o significado, o efeito nos dados de hoje, o
  que fica bloqueado e o que o operador deve fazer;
- nenhum deles torna outras mudanças comprovadas inelegíveis para seleção.

O dry-run físico de validação do Radar V2 em 31/08/2026 leu 13.411 registros:
13.366 tinham layout card/box completo; após a junção com o `Player.bin` atual,
13.363 relações formaram 2.002 boxes. Quarenta e cinco registros com card sem
nome de box e três relações completas para cards fora do `Player.bin` atual
foram isolados. Esses números comprovam essa fotografia e podem mudar em
atualizações futuras.

Há falha real quando a janela mostra **worker encerrado com código 2**, quando
termina sem confirmação final completa, quando o resumo HTML não existe ou
quando o relatório apresenta problema técnico vermelho/Radar indisponível.
Nesse estado, aplicação e conclusão sobre lançamentos ficam bloqueadas. O
operador deve usar **ABRIR LOG**, corrigir a causa e executar outra varredura;
selecionar menos itens não corrige uma leitura incompleta.

Publicar e rodar motores são decisões independentes. Um card pré-carregado pode
ser enviado ao banco e mostrado no site ou na home para anunciar a novidade.
Isso não libera o mesmo card no Otimizador ou no Bonificador. Os dois motores
só podem usar um card quando a versão atual de todos os insumos necessários
estiver comprovada; a mesma verificação é repetida antes de aceitar o trabalho
e antes de salvar o resultado. Se o fingerprint dos insumos mudar, o resultado
antigo fica vencido e o card volta à fila como trabalho novo.

### O que significa card completo

Cada componente guarda um estado explícito:

- `conferido_com_valor`: foi lido e possui valor;
- `conferido_sem_valor`: foi lido e o card realmente não possui aquele item;
- `conferido_sem_vinculo_atual`: o código histórico foi lido, mas o catálogo
  atual já não contém o vínculo;
- `nao_conferido`: a região ou o campo não foi lido;
- `leitura_com_problema`: a leitura ocorreu, mas falhou ou voltou inválida.

Lista vazia, zero ou `NULL` nunca prova sozinho que o dado foi conferido. A
prova vem do leitor e de sua procedência. Quando essa prova existe, zero itens é
uma resposta completa. Na fotografia salva de 43.072 cards, 9.551 cards sem
habilidade, 18.218 sem Estilo de IA e 40.748 sem Ímpeto foram corretamente
classificados como conferidos sem valor.

Os 354 cards cujo código de clube permanece no `Player.bin`, mas cujo clube não
existe mais no `Team.bin`, são cards órfãos por mudança de licença. Eles estão
completos: o código original é preservado, o relatório explica a ausência e
nenhum clube substituto é inventado. Um cálculo que dependa do clube atual os
trata explicitamente como sem vínculo atual.

O segundo estilo de jogo usa índice físico, enquanto o primeiro usa o bit
equivalente a `índice × 4`. Por isso o segundo slot é resolvido por
`playstyle.indice`, não por `id_jogo` nem pelo bit. Exemplos já comprovados:
índice 9 é **O destruidor** (`id_jogo=329`), índice 17 é **Goleiro defensivo**
(`337`) e índice 30 é **Mestre da linha alta** (`350`). Esses estilos não são
pendências nem cards incompletos.

### Configurar a conexão do banco

Se a janela mostrar **Banco: disconnected**, **senha recusada** ou encerrar o
worker com código 2, use o botão **CONFIGURAR CONEXÃO**. No painel do Supabase,
abra o projeto, clique em **Connect** e copie a connection string Postgres
completa. Confirme que `[YOUR-PASSWORD]` foi substituído pela senha atual. Se a
conexão direta não funcionar na rede do computador, copie a opção **Session
pooler** mostrada no mesmo painel.

Cole a string no campo mascarado e clique **TESTAR E SALVAR**. O teste abre uma
transação marcada pelo próprio Postgres como somente leitura, confirma com uma
leitura mínima e desfaz a transação. Somente depois desse teste a string é
salva em
`artefatos/estado-operador/credencial-banco.windows-dpapi.json`, cifrada pelo
Windows DPAPI para o usuário atual. A senha não é gravada em texto aberto, não
entra no relatório, não aparece no log e não é passada na linha de comando.

O launcher remove senhas herdadas do ambiente e entrega a string decifrada
somente no ambiente privado do processo worker. Arquivo ausente, alterado,
truncado, de outro usuário do Windows ou substituído por link é recusado por
segurança. Uma falha de teste fica explicada no log local sem endereço, usuário
ou senha. Configurar a conexão não instala migração, não ativa motores e não
altera dados.

### Revisão manual e sequência de cliques

Depois da varredura, **REVISAR USO NOS MOTORES** abre uma tela pesquisável de
cards colecionáveis. Nada é bloqueado manualmente por padrão. O operador marca
somente o card que sabe ter sido pré-carregado parcialmente e escreve o motivo.
A marcação `incompleto_confirmado` nunca bloqueia publicação ou o envio normal
do card; bloqueia apenas Otimizador e Bonificador. Desmarcar uma observação não
força o estado “completo”: a leitura automática continua sendo a autoridade.

O fluxo diário V5.3 é:

1. quando houver atualização pública, abrir o jogo e esperar o download;
2. clicar duas vezes em `ABRIR-EXTRATOR.cmd`;
3. somente no primeiro uso ou após troca de senha, clicar **CONFIGURAR
   CONEXÃO**, colar a string do botão Connect e clicar **TESTAR E SALVAR**;
4. clicar **INICIAR VARREDURA**;
5. clicar **VER RESULTADO** e ler o resumo de mudanças, boxes e motores;
6. se necessário, clicar **REVISAR USO NOS MOTORES**, marcar somente cards
   sabidamente parciais e salvar;
7. clicar **ESCOLHER O QUE ENVIAR** para selecionar, separadamente, os dados
   novos ou alterados que irão ao banco;
8. clicar **APROVAR PACOTE** e depois **APLICAR PACOTE**;
9. se algum dado foi aplicado, iniciar outra varredura somente leitura. Quando
   ela confirmar **nada para enviar**, clicar **INSTALAR/ATUALIZAR PROTEÇÃO DOS
   MOTORES**, ler a prévia e decidir. A atualização registra somente os cards
   novos ou alterados; se a proteção já estiver atual, nada é gravado.

**INSTALAR/ATUALIZAR PROTEÇÃO DOS MOTORES** não substitui o envio normal dos
dados. É uma ação separada: serve para a primeira ativação e, depois, para
registrar nos motores somente cards novos ou alterados já conferidos.
O botão só fica disponível depois de uma varredura concluída com
`no_changes`, prontidão materializada e seed íntegro. Ele não aparece como
alternativa para ignorar dados novos: se houver algo para enviar, primeiro é
necessário resolver o pacote normal e fazer outra varredura de confirmação.

A revisão local gera `prontidao-motores.json`,
`resumo-prontidao-motores.json` e `revisao-prontidao-motores.json`. Marcações do
operador ficam em
`artefatos/estado-operador/prontidao-motores-operador.json`. Nenhum desses
arquivos escreve no banco por existir ou por ser aberto.

### Banco e consumidores

O banco deve guardar, por card e componente, estado de coleta, estado de
resolução, procedência, versão da regra, fingerprint dos insumos e data da
validação. Ausência confirmada e card órfão são estados próprios; não são
inferidos de campo vazio. A carga inicial cria uma fotografia versionada; nas
rodadas seguintes só card novo ou fingerprint alterado precisa ser atualizado.
Marca manual é armazenada separadamente da prova física.

A instalação ou atualização da proteção é uma ação explícita e separada. O
botão **INSTALAR/ATUALIZAR PROTEÇÃO DOS MOTORES** primeiro executa uma prévia
realmente somente leitura. Essa prévia compara todas as identidades da execução
atual com todas as cartas do banco,
reconfere o contrato vigente e calcula no estado atual do banco quantos
resultados de teste serão marcados inválidos para refazer. O número mostrado na
confirmação vem dessa consulta; não é um número fixado no aplicativo.

Depois da prévia, a janela explica três pontos antes de pedir o aceite: a
proteção não bloqueia inserir, exibir ou publicar cartas; afeta somente
Otimizador e Bonificador; e resultados atuais incompatíveis precisarão ser
refeitos. Cancelar nessa tela não executa nenhuma escrita.

Somente a confirmação positiva inicia uma transação produtiva dedicada. Nela,
na primeira ativação o banco recebe a migração de completude, o escritor
transacional do Bonificador, uma execução aceita, uma aplicação auditada e os
11 componentes de cada carta atual. Nas atualizações seguintes, a migração não
é repetida e somente cards novos ou alterados são registrados. O `aplicacao_id`
não vem pronto no arquivo: ele é
o ID real retornado pelo banco nessa mesma transação e é então usado pelo
registrador. O seed é enviado por tabela temporária em fluxo, evitando 43 mil
conexões ou chamadas individuais. Qualquer falha anterior ao commit desfaz o
conjunto inteiro. Depois do commit, uma nova conexão somente leitura confere
aplicação, totais, 11 componentes por carta, resultados invalidados e escritor
do Bonificador. O resultado local fica em
`instalacao-protecao-motores.json`; a prévia fica em
`previa-protecao-motores.json`.

Essa ação nunca é disparada por **INICIAR VARREDURA**, **ESCOLHER O QUE
ENVIAR**, **APROVAR PACOTE** ou **APLICAR PACOTE**. Enquanto não tiver sido
confirmada e relida, a situação correta continua sendo **preparado, mas ainda
não instalado no banco**.

Depois do aceite na janela, o EXE cria uma autorização curta, de uso único,
vinculada à execução, ao seed, ao resumo mostrado e ao próprio processo da
janela. O worker recusa a escrita se for chamado diretamente fora desse clique.
Antes do COMMIT, ele confere a partição completa dos resultados que ficam,
mudam ou serão refeitos. Se a confirmação do COMMIT ficar incerta, a janela
manda não repetir a operação, mesmo que o arquivo local de resultado não possa
ser salvo.

O lote antigo do Bonificador não faz parte do fluxo clicável e não deve ser
iniciado manualmente. Ele ainda tenta gravar em `clube.build`. A instalação V1
fecha essa porta de forma explícita e recuperável, sem redirecionar a gravação,
e instala o escritor novo para `clube_novo.build_bonificador` dentro da mesma
transação do gate e do seed. O uso produtivo do escritor continua condicionado
ao readback final. A interface local de consulta continua somente leitura.

### Habilidade especial Chute súbito (05/09/2026)

O contrato físico ativo reconhece `carta.habilidade.2457` em `Player.bin`, bit
`639`, largura `1`. O bit foi confirmado exatamente nos cards Francesco Totti
`88045755960771`, Adriano `88045755960841` e Andriy Shevchenko
`88045755964138`. A relação normalizada usa ordem `35`; o catálogo registra a
habilidade como especial, somente de linha e não fabricável.

O texto funcional confirmado na tela do jogo é que o jogador executa o chute
mais rapidamente, reduzindo o tempo até o contato com a bola. Essa descrição
manual não é apresentada como texto fisicamente extraído: o localizador físico
do texto continua separado da prova do bit. Para o motor, a regra aprovada é
`Finalização +5%`. A carga e o rollback versionados ficam em
`4-DOCUMENTOS/EXTRATOR/SQL/APLICAR-HABILIDADE-CHUTE-SUBITO-BIT639-V1.sql` e
`ROLLBACK-HABILIDADE-CHUTE-SUBITO-BIT639-V1.sql`.

## Boxes comerciais — legado fixo e atualização de novas boxes — 07/09/2026

O acervo histórico foi copiado do legado e preservado em
`dados/boxes-historicas-legado.json`. O manifesto ao lado fixa a origem, o
SHA-256 `ec5aaaef830ea03fbea3983037b4eaa9ab1014d25f6a7f082336d59d9255bbae`,
1.023 boxes e 6.708 vínculos. Essa base não é reconstruída por
`PlayerVariationDetail.bin`; o texto desse arquivo é versão da carta. O escopo
da cópia é fechado: nome da Box, `card_id` dos participantes e data preservada
em `visto`. Nenhum cálculo, rótulo, percentual, função ou rotina do legado foi
importado.

A ação dedicada **ATUALIZAR BOXES NOVAS** lê somente a resposta
`CmdGetMyclubAgentlist` mantida na memória do eFootball. A varredura principal e
a aplicação geral de cartas não alteram boxes. Ao receber uma captura, o banco
reconhece pelo título normalizado as boxes atuais que já estavam cadastradas,
preserva fonte, cartas, estado e datas desses registros e cria apenas títulos
novos. Capturas posteriores atualizam ou encerram somente boxes que nasceram da
própria fonte `jogo:CmdGetMyclubAgentlist`.

O leitor parte de `G=[base+0x86c9fc0]`, `A=[G+0x28]`, `B=[A+0x20]`, percorre
o vetor de agentes de stride `0x238` e lê `agent_id`, título comercial, datas e
as três listas de cards. O contrato integral, inclusive parser, conversor,
offsets, larguras e validações, está em `DOCUMENTACAO/MAPEAMENTO-BOXES-RUNTIME.md`
e na tabela `clube_novo.box_leitor_endereco_jogo_v1`.

Cada captura recebe UUID e hash, é preservada em `box_captura_jogo_v1` e tem
agentes/cards normalizados em `box_agente_captura_jogo_v1` e
`box_agente_card_captura_jogo_v1`. O readback confere a captura recebida, mesmo
quando todas as boxes já eram conhecidas e nenhuma linha pública precisou ser
criada. Jogo fechado, área de contratos ainda não carregada, versão desconhecida,
título vazio, vetor instável ou card sem cadastro físico bloqueiam a captura.

Arquivos da rodada: `boxes-jogo-captura.json`, `boxes-jogo-envio.json` e
`boxes-resultado.json`.

No banco, `box_acervo_legado_v1` guarda o manifesto; os registros comerciais
ficam em `box_contexto_contratacao_v1` e os participantes em
`box_card_em_andamento_v1`. Apesar do nome histórico da segunda relação, ela
contém vínculos finalizados e atuais. `carta_box_oferta_v1` é a leitura interna
unificada. A tela consulta somente `public.frontend_boxes_v1`, que exclui da
listagem cadastrada um título histórico enquanto existir oferta em andamento
com o mesmo título. `carta_jogo.box` permanece fora do contrato.

## Extrator separado de níveis e orçamento eFHUB — 06/09/2026

O aplicativo dedicado fica em `7-VARREDURA-DO-JOGO/Extrator Niveis eFHUB.exe`
e abre por `ABRIR-EXTRATOR-NIVEIS-EFHUB.cmd`. Ele não executa a varredura do
jogo e não pede quantidade: **EXTRAIR CARTAS DO OTIMIZADOR** continua até o banco
informar que não existe mais carta elegível para o Otimizador pendente.

A seleção começa pelos cards com publicação ativa, continua por todos os cards
que já possuem resultado concluído do Otimizador e só depois alcança os ainda
não otimizados. Dentro de cada faixa, a prioridade é: cartas evolutivas
não-base, cartas não-base sem evolução/orçamento e cartas base; em cada grupo,
overall decrescente e desempate estável por `card_id`. A cobertura permanece
restrita aos elegíveis ao Otimizador, identificados por `roda_motor is not
false`. Registros da
`player_delete_list` são marcadores de remoção e não são tratados como cards.

A execução percorre somente cards com `roda_motor is not false`, em lotes
independentes de no máximo 1.000. Para cada lote, consulta e valida os IDs no
eFHUB, grava nível/orçamento e o antes/depois no `clube_novo`, faz a leitura de
volta e somente então inicia o lote seguinte. Nesta fase não clona linhas do
Otimizador, não reorganiza a fila e não altera publicações. Cancelar durante um
lote não o aplica; todos os lotes anteriores já confirmados permanecem
gravados. O comparativo, a devolução das cartas divergentes à fila e a nova
ordenação são uma etapa posterior. Uma carta já otimizada só recebe nova linha
quando o orçamento da entrada histórica for diferente do orçamento comprovado;
orçamento coincidente preserva resultado, linha e publicação atuais. Os relatórios ficam em
`artefatos/efhub-niveis/run-*/`.

Desde 07/09, cards com `codigo_tipo_carta_fisico=3` não são enviados ao eFHUB.
O código físico 3, subtipos 0 e 1, cobre POTW/POTM/POTS e determina nível
máximo1/orçamento0. A evidência `tipo_carta_fisico` prevalece sobre a resposta
bruta do eFHUB, que continua armazenada apenas para auditoria. A trigger do
cadastro impede uma resposta eFHUB futura de reintroduzir nível positivo nessa
família. Cards com nível0 continuam pendentes; não são convertidos em nível1.

A correção categorial de 07/09 criou 441 entradas para 26 cards no bloco de
cartas sem evolução. Publicações antigas continuam visíveis até a publicação
compatível da nova linha, quando a troca ocorre na mesma transação. O extrator
sempre cria um UUID corretivo novo; nunca reaproveita o maior lote corretivo.
Prévia das boxes: os três cards seguem a ordem da home eFHUB guardada na sincronização, inclusive quando não têm análise publicada. O contrato público existente resolve essa ordem no banco; a tela apenas exibe.
# Atualização de 12/09: Sobreposição e valores manuais

Sobreposição usa Coach.bin bit 192/largura 7. O endereço 135 foi rejeitado
por comparação dos 65 técnicos já conferidos: 192 acertou 65/65 e 135, 0/65.
Conte tem 69. Evidência completa em
`4-DOCUMENTOS/EXTRATOR/SOBREPOSICAO-192-1209.md` na raiz do projeto.

Use nova varredura após atualizar o contrato. Um pacote da leitura antiga
não pode ser aplicado com o contrato novo. A varredura compara; a aplicação
é feita pelo pacote selecionado. Boxes e níveis têm fluxos próprios.

Na atualização de níveis, a prova conserva o valor coletado. O cadastro
conserva a correção manual registrada, quando houver. A conferência aceita
essa diferença somente para a carta e o campo protegidos.
