# Manual do Extrator eFootball

**Versão:** 4.6 · 29 de agosto de 2026  
**Estado:** migração de referências físicas em execução; escrita produtiva bloqueada até a validação integral read-only  
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

## Caminhos ativos V4.6

### Cartas e Dimensões

`app/contrato-v46-runtime.js` substitui o caminho produtivo de cartas. Dados básicos, nacionalidade, clube, liga, tipo, indisponibilidade, atributos, habilidades, estilos de IA, aptidões, corpo e slots usam referências canônicas.

A rotina ativa de Dimensões usa as referências de `nacionalidade_jogo`, `clube_jogo`, `liga_jogo`, `tipo_carta_jogo` e campos do contrato para `Country.bin`, `Team.bin`, `CompetitionUnit.bin`, `CompetitionEntry.bin`, `Player.bin` e `PlayerDeleteList.bin`.

### Metadados

`app/metadata-v46-runtime.js` preserva a lógica cumulativa existente para habilidades, playstyles, técnicos, nacionalidades, afinidades, ímpetos, efeitos/condições e relações de liga.

`app/metadata-v46-compat.js` existe somente para compatibilidade de dependências antigas e não possui endereço próprio:

- `dt200` e `dt870_original` não têm fingerprint autoritativo publicado no contrato ativo; sua validação estrutural é feita no consumo pelas referências canônicas;
- o espelho do tipo de condição é projetado de `tipo_impeto_jogo`;
- quando as tabelas de alvo de nacionalidade ou liga não vêm no payload do contrato, a projeção temporária recebe `bit/largura` dos campos contratados `impeto.condicao.nacionalidade` e `impeto.condicao.liga`;
- todas essas projeções são removidas depois da extração e não viram uma segunda autoridade.

### Leitor neutro

`app/leitura-contrato.js` valida pedido, fingerprint e tamanho de registro. Campos `all_str_parser` pertencem ao parser específico de `all.str` e não são tratados como campo binário genérico.

## Módulos acessórios

- `executor/tecnicos.py`: sem `STYLE_BITS`; proficiências e boosts exigem evidência física recebida da fotografia canônica;
- `executor/card_dimensions.py`: referências de nacionalidade, clube, liga, tipo e vínculo vêm das tabelas canônicas;
- `executor/impetos.py`: a maior parte dos bits/tamanhos já vem do `field_contract`; qualquer fallback numérico semântico residual deve ser eliminado antes da liberação produtiva;
- `executor/card_impetus.py`: endereços dos slots vêm do contrato ativo;
- `executor/card_relations.py`: resolve chaves pelos catálogos sem decidir endereço de extração.

## Técnicos

`Coach.bin` permanece a fonte física. Arquivo, registro, bit, largura e hash pertencem às tabelas e ao contrato. Proficiências usam `estilo_jogo_tecnico`; afinidade usa `afinidade_tecnico_jogo`; boosts usam os campos contratados e a ordem canônica de atributos.

## Ímpetos

Ímpetos vêm dos arquivos físicos do jogo. Código/tamanho vêm de `impeto_jogo`; efeitos de `impeto_atributo_jogo`; espelho de tipo de `tipo_impeto_jogo`; parâmetros, classes, nacionalidade, liga e membros usam suas respectivas referências canônicas. A fórmula existente de faixas não muda.

A verificação feita em 29/08/2026 encontrou referências físicas preenchidas para todos os registros auditados de `estilo_jogo_tecnico`, `afinidade_tecnico_jogo`, `impeto_jogo`, `impeto_atributo_jogo`, `impeto_condicao_parametro_faixa_jogo` e `impeto_condicao_liga_membro_jogo`.

## Textos e Boxes

Textos oficiais vêm de `all.str` em `dt261_bra`, com chave seção + ID. Boxes continuam bloqueadas enquanto sua referência física canônica completa não estiver no fluxo ativo.

## Segurança e liberação

Nenhuma carga produtiva deve ser feita durante a migração. A ordem é:

1. terminar a auditoria dos caminhos ativos e acessórios;
2. eliminar fallback numérico semântico residual;
3. executar leitura integral sem escrita;
4. validar fingerprints, tamanhos e cardinalidades;
5. comparar com a referência já aprovada;
6. investigar qualquer divergência;
7. só então liberar aplicação de metadados/cards;
8. depois liberar Otimizador e Bonificador.

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
- `Extrator-ClubEfootball.html`

## Critério de conclusão

A migração termina quando o caminho efetivamente executado provar que nenhum dado semântico usa endereço local como autoridade, as referências vêm das tabelas/catálogos correspondentes, os arquivos atuais passam pelos fingerprints contratados, fontes históricas não recebem fingerprint inventado, não existe fallback para endereço legado e a leitura read-only reproduz a referência aprovada ou toda divergência foi investigada.

## Regra de documentação

Toda implementação, alteração ou exclusão no V4 deve atualizar o manual correspondente no mesmo conjunto de trabalho. Código e documentação divergentes são pendência, não conclusão.
