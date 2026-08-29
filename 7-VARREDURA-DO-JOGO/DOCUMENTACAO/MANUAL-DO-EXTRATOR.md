# Manual do Extrator eFootball

**Versão:** 4.6 · 29 de agosto de 2026  
**Estado:** contrato V4.6 ativo para leitura e validação controlada; teste integral local ainda pendente  
**Pasta operacional:** `Clubefootball V4\7-VARREDURA-DO-JOGO`

## Regra estrutural

O Extrator já possui lógica de extração validada. A V4.6 não muda fórmula, sequência, semântica ou regra de extração.

> **A tabela/catálogo canônico de `clube_novo` diz onde está o dado. O Extrator somente valida, lê e devolve.**

Onde o código antigo tinha bit, offset, largura, arquivo ou tamanho de registro escrito diretamente, o caminho V4.6 recebe o valor equivalente das tabelas do `clube_novo` e do pedido de leitura. Primitivas genéricas de CPK, WESYS, little-endian, bitfield e UTF-8 podem permanecer no código; elas não são endereço semântico.

## Autoridade das referências

As referências físicas ficam nos próprios catálogos/tabelas, entre eles `atributo_jogo`, `habilidade_jogo`, `playstyle`, `posicao_jogo`, `nacionalidade_jogo`, `clube_jogo`, `liga_jogo`, `tipo_carta_jogo`, tabelas de técnico e tabelas de ímpeto.

O contrato ativo sela versão, arquivos atuais, fingerprints, campos permitidos e catálogos participantes. Sem referência canônica válida, a leitura bloqueia. Não existe fallback produtivo para endereço antigo escrito no código.

```text
clube_novo: tabela/catálogo
        ↓ referência física
contrato ativo
        ↓ versão/fingerprint/permissão
Extrator + acessórios
        ↓ mesma lógica existente
valor extraído
```

## Contrato ativo em 29/08/2026

O contrato `clubef-dt870-2026-r1`, versão `r1`, foi fechado para a etapa de leitura e validação controlada após a reconciliação da cadeia V4.6.

Estado conferido no momento da ativação:

- 214 campos ativos: 211 com prova `comprovado` e 3 com `convencao_aprovada`;
- 12 arquivos obrigatórios com fingerprint físico preenchido;
- 14 elos que exigem selo do contrato marcados `conforme` e 3 elos de transporte/launcher mantidos `neutro`;
- nenhum campo ativo sem prova aceita;
- nenhum arquivo obrigatório sem hash;
- nenhum elo selado pendente;
- consumidores condicionais de ímpeto permanecem desligados durante a validação (`pode_rodar = false`).

Fingerprints selados:

- contrato: `86723a63b116c3fb31fcc9c1f01728f5072869b548b34f1dab5196b710dcb2fd`;
- fontes: `719e580013a0eedb2d6a8a777653bc366eabd2d4a1becc7579a493493cb0cd35`.

Após a ativação, `clube_novo.obter_pedido_leitura_contrato_ativo()` passou a devolver o pedido `r1` com os 12 arquivos e os 214 campos. A ativação libera **leitura e validação**; ela não constitui aprovação do resultado de uma nova extração nem substitui o teste integral local.

## Descoberta automática das fontes físicas

O fluxo normal não exige que o usuário procure CPKs manualmente. A descoberta automática agora pertence ao próprio `executor/servidor_v46.py`, portanto funciona mesmo quando o Extrator é aberto sem depender das variáveis definidas pelo launcher `.cmd`.

Fontes padrão atuais:

- DT870 da atualização: raiz `C:\ProgramData\KONAMI\eFootball\ST\Download`, incluindo pesquisa recursiva por `dt870_console_win.cpk` em subpastas;
- DT200 base: `C:\Program Files (x86)\Steam\steamapps\common\eFootball\cpk\dt200_console_all.cpk`;
- DT870 original: `C:\Program Files (x86)\Steam\steamapps\common\eFootball\cpk\dt870_console_win.cpk`;
- textos em português: `C:\Program Files (x86)\Steam\steamapps\common\eFootball\cpk\dt261_bra_console_win.cpk`;
- a variante de Steam em `C:\Program Files\Steam\steamapps\common\eFootball` também é pesquisada.

O `all.str` **não é um arquivo que o usuário precisa localizar solto no Windows**. Ele fica dentro do `dt261_bra_console_win.cpk`; o Extrator abre esse CPK e extrai/consulta `all.str` conforme a lógica já existente.

A descoberta física responde somente à pergunta **onde está o arquivo**. Ela não aprova a fonte por assinatura local simplificada. Depois de localizar o CPK, o runtime recebe os bytes e valida fingerprint, tamanho e contrato antes de considerar a fonte pronta. Isso evita o falso `NÃO ENCONTRADO` causado pela antiga pré-validação dos quatro primeiros bytes do contêiner.

Ao iniciar o servidor V4.6, o terminal também imprime as quatro fontes detectadas. A seleção manual permanece apenas como recuperação se a busca automática realmente não encontrar o arquivo.

## Caminhos ativos V4.6

### Cartas e Dimensões

`app/contrato-v46-runtime.js` substitui o caminho produtivo de cartas. Dados básicos, nacionalidade, clube, liga, tipo, indisponibilidade, atributos, habilidades, estilos de IA, aptidões, corpo e slots usam referências canônicas.

A rotina ativa de Dimensões usa as referências de `nacionalidade_jogo`, `clube_jogo`, `liga_jogo`, `tipo_carta_jogo` e campos do contrato para `Country.bin`, `Team.bin`, `CompetitionUnit.bin`, `CompetitionEntry.bin`, `Player.bin` e `PlayerDeleteList.bin`.

### Metadados

`app/metadata-v46-runtime.js` preserva a lógica cumulativa existente para habilidades, playstyles, técnicos, nacionalidades, afinidades, ímpetos, efeitos/condições e relações de liga.

O `executor/servidor_v46.py` amplia o payload de catálogos do pedido ativo e entrega diretamente as linhas reais das tabelas canônicas necessárias aos módulos acessórios, sem copiar bit, offset, largura ou tamanho para o servidor. Entre as tabelas entregues explicitamente estão `estilo_jogo_tecnico`, `afinidade_tecnico_jogo`, `atributo_ordem_otimizador`, `impeto_jogo`, `impeto_atributo_jogo`, `tipo_impeto_jogo`, `impeto_condicao_jogo`, `impeto_condicao_nacionalidade_jogo`, `impeto_condicao_liga_jogo`, `impeto_condicao_classe_jogo`, `impeto_condicao_parametro_faixa_jogo`, `impeto_condicao_liga_membro_jogo` e `posicao_jogo`.

`app/metadata-v46-compat.js` não fabrica mais catálogos nem projeta endereços. Ele apenas mantém a descoberta das fontes históricas `dt200` e `dt870_original`, que ainda não possuem fingerprint autoritativo próprio no contrato ativo, e falha fechado se alguma tabela canônica obrigatória chegar sem as colunas físicas necessárias.

### Leitor neutro

`app/leitura-contrato.js` valida pedido, fingerprint e tamanho de registro. Campos `all_str_parser` pertencem ao parser específico de `all.str` e não são tratados como campo binário genérico.

## Módulos acessórios

- `executor/tecnicos.py`: sem `STYLE_BITS`; proficiências e boosts exigem evidência física recebida da fotografia canônica;
- `executor/card_dimensions.py`: referências de nacionalidade, clube, liga, tipo e vínculo vêm das tabelas canônicas;
- `executor/impetos.py`: bit/largura do tipo, espelho, alvos, classes, corte, efeito máximo, arquivos e tamanhos são obrigatórios no `field_contract`/fotografia, sem fallback físico produtivo local;
- `executor/card_impetus.py`: endereços dos slots vêm do contrato ativo;
- `executor/card_relations.py`: resolve chaves pelos catálogos sem decidir endereço de extração.

## Técnicos

`Coach.bin` permanece a fonte física. Arquivo, registro, bit, largura e hash pertencem às tabelas e ao contrato. Proficiências usam `estilo_jogo_tecnico`; afinidade usa `afinidade_tecnico_jogo`; boosts usam os campos contratados e a ordem canônica de atributos.

## Ímpetos

Ímpetos vêm dos arquivos físicos do jogo. Código/tamanho vêm de `impeto_jogo`; efeitos de `impeto_atributo_jogo`; espelho de tipo de `tipo_impeto_jogo`; parâmetros, classes, nacionalidade, liga e membros usam suas respectivas referências canônicas. A fórmula existente de faixas não muda.

A verificação feita em 29/08/2026 encontrou referências físicas preenchidas para todos os registros auditados de `estilo_jogo_tecnico`, `afinidade_tecnico_jogo`, `impeto_jogo`, `impeto_atributo_jogo`, `impeto_condicao_parametro_faixa_jogo` e `impeto_condicao_liga_membro_jogo`.

## Textos e Boxes

Textos oficiais vêm de `all.str` dentro de `dt261_bra_console_win.cpk`, com chave seção + ID. O usuário não precisa localizar `all.str` manualmente; o parser textual existente é responsável por abrir a fonte e encontrar o conteúdo interno. Boxes continuam bloqueadas enquanto sua referência física canônica completa não estiver no fluxo ativo.

## Segurança e liberação

A auditoria estrutural necessária para ativar o contrato de leitura foi concluída. A sequência restante é:

1. executar a leitura integral local, sem aplicação automática;
2. validar fingerprints, tamanhos e cardinalidades contra as fontes físicas encontradas na máquina;
3. comparar a fotografia extraída com a referência já aprovada;
4. investigar toda divergência antes de qualquer promoção;
5. somente depois liberar/aplicar os metadados e cards aprovados;
6. depois liberar Otimizador e Bonificador.

Ativar o contrato não significa aceitar automaticamente uma nova carga. O primeiro ciclo após a ativação é de validação e comparação.

## Arquivos ativos

- `app/leitura-contrato.js`
- `app/contrato-v46-runtime.js`
- `app/metadata-v46-runtime.js`
- `app/metadata-v46-compat.js`
- `app/extrator-core.js` — núcleo legado preservado; runtimes V4.6 substituem os caminhos migrados
- `executor/tecnicos.py`
- `executor/impetos.py`
- `executor/card_dimensions.py`
- `executor/card_impetus.py`
- `executor/card_relations.py`
- `executor/card_dimensions_apply.py`
- `executor/executor_local.py`
- `executor/servidor_v46.py`
- `INICIAR-EXTRATOR-V46.cmd`
- `Extrator-ClubEfootball.html`

## Critério de conclusão

A migração termina quando o caminho efetivamente executado provar que nenhum dado semântico usa endereço local como autoridade, as referências vêm das tabelas/catálogos correspondentes, os arquivos atuais passam pelos fingerprints contratados, fontes históricas não recebem fingerprint inventado, não existe fallback para endereço legado e a leitura read-only reproduz a referência aprovada ou toda divergência foi investigada.

## Regra de documentação

Toda implementação, alteração ou exclusão no V4 deve atualizar o manual correspondente no mesmo conjunto de trabalho. Código e documentação divergentes são pendência, não conclusão.
