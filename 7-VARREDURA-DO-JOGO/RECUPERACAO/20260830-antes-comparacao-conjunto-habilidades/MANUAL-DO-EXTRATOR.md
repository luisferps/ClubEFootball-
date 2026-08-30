# Manual do Extrator eFootball

**Versão:** 4.6.12 · 29 de agosto de 2026  
**Estado:** contrato V4.6 ativo; varredura orientada pelo banco, isolada por família, responsiva e com conferência intermediária obrigatória antes de qualquer escrita  
**Pasta operacional:** `7-VARREDURA-DO-JOGO`

## Regra estrutural

O Extrator já possui lógica de extração validada. A V4.6 não muda fórmula, sequência, semântica ou regra de extração.

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

A versão operacional é V5.0.0. O único fluxo de abertura é
`ABRIR-EXTRATOR.cmd` -> `Extrator eFootball.exe` V5.0.0 ->
`executor/desktop_worker.py`. O launcher cria uma pasta única em
`artefatos/desktop/`, chama o worker com `--root`, `--run-dir` e `--cancel`,
e mostra os eventos JSON de progresso. Ele não abre navegador, localhost nem
servidor HTTP.

O launcher também envia `--protocol-version 5.0.0`. O worker declara a mesma
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
`manifesto-execucao.json`. O botão **VER DIVERGÊNCIAS** abre apenas o HTML no
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
o resultado técnico é grande. Dados sem rótulo de jogo aparecem sob
**Informações técnicas para investigar**, também fechados por padrão. IDs,
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
declara. Diagnósticos não selecionam registros, não aguardam autorização nem
se tornam uma seleção manual de dados. O worker atual não contém aplicador de dados do
jogo; a fronteira de escrita permanece bloqueada para impedir schema errado,
mas o resultado normalizado e selado está pronto para retorno ao fluxo de
`clube_novo`.

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
execute `windows-app/COMPILAR-APLICATIVO.ps1` para instalar o EXE V5.0.0
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
`box`, títulos e rótulos legíveis não participam de identidade nem de carga;
continuam no CSV público apenas para apresentação. A migração e rollback
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

O botão **APROVAR PACOTE** da janela V5 invoca o worker local com o caminho do
`pacote-revisao.json`. Antes de registrar a decisão, o worker recalcula o SHA-256
do pacote, relê o contrato ativo, confere o selo completo (contrato, versão do
jogo, fontes e catálogos), confirma a cobertura técnica por família e verifica
as fontes declaradas. A decisão persistida contém exatamente o hash e o selo;
ela não autoriza qualquer outro pacote.

O botão **APLICAR PACOTE** chama o aplicador interno. Ele bloqueia se a decisão
não for do mesmo hash/selo, se qualquer fonte sumiu, se a cobertura deixou de
ser integral ou se houver divergência no readback. Em uma única transação ele
estagia `execucao_leitura_contrato`, registra a auditoria por família em
`clube_novo.aplicacao_pacote_revisao_extrator`, lê de volta os selos e só então
teria permissão de confirmar os envelopes tipados. Identidade e FK são sempre
as chaves canônicas declaradas; rótulos nunca são usados como chave ou destino.

Durante este desenvolvimento `PRODUCTIVE_WRITES_LOCKED` permanece verdadeiro.
O pacote atual contém diagnóstico/comparação, não envelopes normalizados de
escrita de domínio; por isso o aplicador recusa produção antes de qualquer dado
real. O smoke controlado usa transação integral com rollback e só valida o
gate, estágio, auditoria e readback. A migração e seu rollback são
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
de teste foi restaurado. `PRODUCTIVE_WRITES_LOCKED=true` permanece: não houve
dados reais de jogo aplicados.

### Comparação canônica de Cartas — 29/08/2026

O leitor físico não compara CSV de apresentação. A comparação de Cartas ocorre
depois da leitura de Dimensões, com `projecoes_cartas` do pedido, `card_id` e
códigos/FKs canônicos. Nomes, rótulos de nacionalidade e a ordem de
habilidades/estilos não geram falsos deltas nem chegam à etapa de aprovação
como decisão de domínio.
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
