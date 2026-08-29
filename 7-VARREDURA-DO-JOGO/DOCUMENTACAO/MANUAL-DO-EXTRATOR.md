# Manual do Extrator eFootball

**Versão:** 4.6.10 · 29 de agosto de 2026  
**Estado:** contrato V4.6 ativo; varredura orientada pelo banco e isolada por família; teste integral local da V4.6.10 pendente  
**Pasta operacional:** `7-VARREDURA-DO-JOGO`

## Regra estrutural

O Extrator já possui lógica de extração validada. A V4.6 não muda fórmula, sequência, semântica ou regra de extração.

> **A tabela/catálogo canônico de `clube_novo` diz o que deve ser buscado e onde está o dado. O Extrator valida, lê, compara e devolve um relatório.**

Onde o código antigo tinha bit, offset, largura, arquivo, tamanho de registro ou cardinalidade escritos diretamente, o caminho V4.6 recebe o valor equivalente das tabelas de `clube_novo` e do pedido ativo de leitura. Primitivas genéricas de CPK, WESYS, little-endian, bitfield e UTF-8 podem permanecer no código; elas não são autoridade semântica.

## Regra de continuidade da varredura — V4.6.10

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

Cardinalidades como `440`, `407`, `2.072`, `696` ou `35` não são regras permanentes no código. O valor vigente é obtido das tabelas canônicas na própria execução.

Só constituem bloqueio estrutural geral:

- impossibilidade de obter um contrato ativo e íntegro;
- impossibilidade de abrir o executor local;
- ausência da conexão de leitura quando a família depende do banco;
- fonte física inteira indisponível para todas as famílias que dependem dela;
- arquivo incompatível com o fingerprint/tamanho exigido pelo contrato.

Mesmo nesses casos, o bloqueio deve identificar as famílias afetadas e preservar os resultados já obtidos.

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
        ↓ somente famílias exatas podem ser aplicadas
clube_novo
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

A V4.6.10 usa:

- runtime: `executor/servidor_v4610.py`;
- porta local exclusiva: `8774`;
- UI servida pelo runtime com o fluxo não bloqueante;
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

### Metadados

`app/metadata-v46-runtime.js` preserva a leitura cumulativa para habilidades, playstyles, técnicos, nacionalidades, afinidades, ímpetos, efeitos, condições e relações de liga.

`executor/servidor_v46.py` permanece como base compatível. `executor/servidor_v4610.py` aplica o runtime V4.6.10, isola o processo na porta 8774 e serve a UI que continua a varredura após divergências de uma família.

### Ímpetos

`executor/impetos_v4610.py` substitui, no caminho ativo V4.6.10, a validação legada com cardinalidades congeladas. Em cada execução, ele lê as tabelas:

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

### Técnicos, Textos e demais famílias

Técnicos, nacionalidades, afinidades, textos e Dimensões são tratados separadamente na UI V4.6.10. Falha ou divergência de uma delas gera aviso e relatório; as demais continuam.

A aplicação continua manual, selada e restrita às famílias aprovadas.

## Segurança e sequência

1. consultar o contrato e os catálogos;
2. localizar as fontes;
3. executar todas as famílias possíveis;
4. registrar ausentes, novos, alterados, duplicados e erros;
5. concluir a varredura mesmo com avisos;
6. bloquear somente a aplicação das famílias divergentes;
7. revisar o relatório;
8. aplicar apenas o que estiver aprovado;
9. somente depois liberar consumidores posteriores.

Nenhuma divergência deve ser escondida por fallback. Nenhuma família válida deve ser descartada porque outra falhou.

## Arquivos ativos

- `app/leitura-contrato.js`
- `app/contrato-v46-runtime.js`
- `app/metadata-v46-runtime.js`
- `app/metadata-v46-compat.js`
- `app/extrator-core.js`
- `app/extrator-ui.js` — fonte-base; a V4.6.10 aplica o patch não bloqueante ao servi-la
- `app/patches-v4610/post-json-report.jsfrag`
- `app/patches-v4610/family-block.jsfrag`
- `app/patches-v4610/status-block.jsfrag`
- `executor/tecnicos.py`
- `executor/impetos.py` — validador legado preservado para histórico
- `executor/impetos_v4610.py` — validador ativo orientado pelo banco
- `executor/card_dimensions.py`
- `executor/card_dimensions_apply.py`
- `executor/card_impetus.py`
- `executor/card_relations.py`
- `executor/executor_local.py`
- `executor/servidor_v46.py`
- `executor/servidor_v4610.py`
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
- somente famílias aprovadas podem ser aplicadas;
- a leitura integral local foi testada e o resultado foi conferido.

## Regra de documentação

Toda implementação, alteração ou exclusão no V4 deve atualizar este manual no mesmo conjunto de trabalho. Código e documentação divergentes são pendência, não conclusão.
