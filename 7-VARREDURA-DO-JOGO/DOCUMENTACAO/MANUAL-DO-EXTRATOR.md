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

A V4.6.12 usa:

- runtime: `executor/servidor_v4612.py`;
- porta local exclusiva: `8776`;
- leitor contratual e núcleo servidos com lotes cooperativos;
- UI servida pelo runtime com fluxo não bloqueante e painel intermediário;
- log: `logs/extrator-v46.log`.

Quando o launcher muda, o executável deve ser recompilado. O botão `4-BAIXAR-DO-GITHUB.bat` sincroniza o código e recompila o aplicativo, preservando `config.txt`.

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

### Metadados

`app/metadata-v46-runtime.js` preserva a lógica das leituras físicas. `app/patches-v4610/metadata-family-safe.jsfrag` é aplicado pelo servidor ao carregar esse runtime. Habilidades, Ímpetos, Playstyles, Textos, Técnicos, nacionalidades e afinidades são extraídos em blocos isolados: falha física de uma família produz um catálogo de erro e a função continua nas demais.

`app/metadados-v46.js` fornece o painel intermediário. Ele recebe os relatórios de Metadados e Cartas, abre a conferência de Dimensões, exige revisão explícita e só então habilita a etapa final.

`executor/servidor_v46.py` permanece como base compatível. `executor/servidor_v4610.py` preserva o fluxo não bloqueante e a conferência da V4.6.11. `executor/servidor_v4612.py` adiciona a camada de responsividade, isola o processo na porta 8776 e mantém a validação do `review_id` antes da escrita.

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