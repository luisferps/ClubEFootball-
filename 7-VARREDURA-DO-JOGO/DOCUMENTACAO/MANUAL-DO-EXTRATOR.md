# Manual do Extrator eFootball

**Versão:** 4.6 · 29 de agosto de 2026  
**Estado:** migração das referências físicas em execução; escrita produtiva bloqueada até a primeira validação integral read-only  
**Pasta operacional:** `Clubefootball V4\7-VARREDURA-DO-JOGO`

## 1. Regra estrutural

O Extrator já possui lógica de extração validada e essa lógica deve ser preservada.

> **A tabela/catálogo canônico de `clube_novo` diz onde está o dado. O Extrator somente valida, lê e devolve.**

A alteração V4.6 não muda fórmula, sequência, semântica ou regra de extração. Ela substitui referências físicas escritas no código — bit, offset, largura, arquivo e tamanho de registro — pelas referências já armazenadas nas tabelas do `clube_novo` e entregues no pedido de leitura.

Primitivas genéricas de formato, como parsing de CPK, WESYS, inteiro little-endian, bitfield e UTF-8, podem permanecer no código. Elas não são endereço semântico de dado do jogo.

## 2. Autoridade das referências

As referências físicas pertencem aos próprios catálogos/tabelas. Entre as fontes já utilizadas estão:

- `atributo_jogo`;
- `habilidade_jogo`;
- `playstyle`;
- `posicao_jogo`;
- `nacionalidade_jogo`;
- `clube_jogo`;
- `liga_jogo`;
- `tipo_carta_jogo`;
- `tecnico_jogo`;
- `estilo_jogo_tecnico`;
- `afinidade_tecnico_jogo`;
- `tecnico_estilo_jogo`;
- `tecnico_atributo_jogo`;
- `impeto_jogo`;
- `impeto_atributo_jogo`;
- `tipo_impeto_jogo`;
- tabelas de condição, faixa, classe e membros de liga dos ímpetos.

O contrato ativo continua sendo o selo de execução: versão, arquivos atuais, fingerprints, campos permitidos e catálogos participantes. O executor local entrega ao navegador as linhas completas dos catálogos solicitados.

Fluxo:

```text
clube_novo: tabela/catálogo
        ↓ referência física
contrato ativo
        ↓ versão/fingerprint/permissão
Extrator + acessórios
        ↓ mesma lógica existente
valor extraído
```

Sem referência canônica válida, a família deve bloquear. Não existe fallback produtivo para endereço antigo escrito no código.

## 3. Estado atual da implementação

### Cartas

`app/contrato-v46-runtime.js` está ativo antes da interface e substitui o caminho produtivo de cartas. Dados básicos, nacionalidade, clube, liga, tipo, indisponibilidade, atributos, habilidades, estilos de IA, aptidões, corpo e slots usam contrato/catálogos como fonte das referências físicas.

A rotina de Dimensões também foi substituída no runtime V4.6. `Country.bin`, `Team.bin`, `CompetitionUnit.bin`, `CompetitionEntry.bin`, `Player.bin` e `PlayerDeleteList.bin` deixam de depender, no caminho ativo, dos offsets antigos existentes no núcleo legado.

### Metadados

`app/metadata-v46-runtime.js` está ativo e preserva a lógica cumulativa existente para:

- habilidades;
- playstyles;
- técnicos;
- nacionalidades;
- afinidades;
- ímpetos e seus efeitos/condições;
- relações de liga usadas por ímpetos.

Os endereços são obtidos das tabelas canônicas e dos campos do contrato. O módulo não deve criar uma segunda tabela local de bits.

`app/metadata-v46-compat.js` trata duas situações transitórias sem inventar endereço:

1. `dt200` e `dt870_original` são fontes históricas auxiliares e não possuem fingerprints próprios no contrato ativo atual. A descoberta do contêiner é aceita e a validação estrutural fica para o leitor canônico de metadados, que usa tamanhos e referências das tabelas;
2. uma dependência antiga da rotina de ímpetos recebe o endereço do espelho de condição exclusivamente de `tipo_impeto_jogo`. A projeção é temporária e não vira autoridade paralela.

### Leitor neutro

`app/leitura-contrato.js` valida o pedido, fingerprints atuais e tamanhos de registro antes da leitura binária. Campos `all_str_parser` são aceitos no pedido, mas ficam para o parser específico de `all.str`; não são tratados como campo binário genérico.

### Módulos acessórios

- `executor/tecnicos.py`: não mantém mais `STYLE_BITS`; proficiências e boosts exigem evidência física recebida da fotografia canônica;
- `executor/card_dimensions.py`: referências de nacionalidade, clube, liga, tipo e vínculo vêm das tabelas canônicas;
- `executor/impetos.py`: a maior parte dos bits/tamanhos já vem do `field_contract` produzido pelo Extrator. A auditoria final ainda deve remover qualquer fallback numérico residual antes da liberação produtiva;
- `executor/card_impetus.py`: os dois slots de ímpeto recebem seus endereços do contrato ativo;
- `executor/card_relations.py`: resolve chaves pelos catálogos de `clube_novo`, sem decidir endereço de extração.

## 4. Fontes atuais e históricas

O contrato ativo `clubef-dt870-2026-r1` possui arquivos obrigatórios com fingerprint para `dt870_updated` e para `dt261_bra/all.str`.

`dt200` e `dt870_original` continuam sendo fontes auxiliares históricas usadas pela mesma lógica cumulativa de metadados. Como o contrato ativo não publica fingerprints dessas duas fontes, elas não podem receber um fingerprint inventado. O leitor V4.6 valida sua estrutura no momento do consumo usando as referências canônicas aplicáveis.

## 5. Campos novos da V4

Nacionalidade, clube e liga seguem exatamente a mesma regra dos campos antigos: o Extrator não possui autoridade sobre o endereço.

A carta fornece o código físico conforme a referência canônica; o catálogo correspondente resolve a entidade. Liga é ligada ao clube/equipe pela estrutura física contratada, sem alterar a lógica de relacionamento.

## 6. Técnicos

`Coach.bin` permanece a fonte física. Arquivo, registro, bit, largura e hash pertencem às tabelas de técnico e ao contrato.

Proficiências usam `estilo_jogo_tecnico`. Afinidade usa `afinidade_tecnico_jogo`. Boosts usam os campos contratados e a ordem canônica de atributos. O validador apenas compara o que foi extraído com o que está armazenado.

## 7. Ímpetos

Ímpetos vêm dos arquivos físicos do jogo.

O código do ímpeto e o tamanho de registro são referenciados por `impeto_jogo`; efeitos por `impeto_atributo_jogo`; o espelho de tipo por `tipo_impeto_jogo`; parâmetros, classes, nacionalidade, liga e membros usam suas respectivas tabelas canônicas.

A fórmula já existente de faixas permanece inalterada. A migração só troca a origem dos endereços físicos.

## 8. Textos

Textos oficiais vêm de `all.str` em `dt261_bra`. A chave canônica continua sendo seção + ID. O parser textual é específico e separado do leitor binário genérico.

## 9. Boxes

Boxes não são consideradas liberadas enquanto sua referência física canônica completa não estiver disponível no fluxo ativo. Nenhum coletor externo antigo é autoridade do V4.

## 10. Segurança e escrita

Nenhuma carga produtiva deve ser feita durante esta migração. O primeiro teste é integral e somente leitura.

Ordem de liberação:

1. terminar auditoria dos caminhos ativos e acessórios;
2. eliminar fallback numérico semântico residual;
3. executar a leitura integral sem escrita;
4. validar fingerprints, tamanhos e cardinalidades;
5. comparar a nova fotografia com a referência já aprovada;
6. investigar qualquer divergência;
7. somente então liberar aplicação de metadados/cards;
8. depois liberar Otimizador e Bonificador.

## 11. Arquivos ativos da V4.6

- `app/leitura-contrato.js` — primitivas neutras de leitura;
- `app/contrato-v46-runtime.js` — cartas e Dimensões por referência canônica;
- `app/metadata-v46-runtime.js` — metadados por referência canônica;
- `app/metadata-v46-compat.js` — compatibilidade transitória sem endereço hardcoded;
- `app/extrator-core.js` — núcleo legado cuja lógica é preservada; rotinas V4.6 substituem os caminhos produtivos migrados;
- `executor/tecnicos.py`;
- `executor/impetos.py`;
- `executor/card_dimensions.py`;
- `executor/card_impetus.py`;
- `executor/card_relations.py`;
- `executor/card_dimensions_apply.py`;
- `executor/executor_local.py`;
- `Extrator-ClubEfootball.html` — ordem oficial de carregamento dos runtimes.

## 12. Critério de conclusão

A migração termina quando o caminho efetivamente executado provar que:

- nenhum dado semântico usa endereço físico local como autoridade;
- referências aplicáveis vêm das tabelas/catálogos correspondentes de `clube_novo`;
- arquivos atuais exigidos passam pelo fingerprint contratado;
- fontes históricas não recebem fingerprint inventado;
- não existe fallback para endereço legado;
- a lógica original do Extrator permanece inalterada;
- a leitura integral read-only reproduz a referência aprovada ou toda divergência foi investigada.

## 13. Regra de documentação

Toda implementação, alteração ou exclusão no V4 deve atualizar o manual correspondente no mesmo conjunto de trabalho. Código e documentação divergentes são pendência, não conclusão.
