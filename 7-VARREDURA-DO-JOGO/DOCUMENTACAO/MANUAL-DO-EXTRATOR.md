# Manual do Extrator eFootball

**Versão:** 4.6 · 29 de agosto de 2026  
**Estado da entrega:** migração de referências físicas fixas para referências fornecidas pelos próprios catálogos do `clube_novo`; execução produtiva permanece bloqueada até a auditoria integral e o teste read-only  
**Pasta operacional:** `Clubefootball V4\7-VARREDURA-DO-JOGO`

## 1. Finalidade

O Extrator eFootball é a primeira etapa do pipeline produtivo do ClubEFootball V4.

```text
EXTRATOR -> OTIMIZADOR -> BONIFICADOR
```

Regra central da arquitetura V4.6:

> **A tabela/catálogo canônico diz onde está o dado. O Extrator somente valida, lê e devolve.**

A lógica do Extrator não muda. A mudança V4.6 é somente de referência física: onde antes um módulo continha `bit`, `offset`, `largura`, `arquivo` ou `tamanho_registro` escrito diretamente no código, ele passa a receber o valor equivalente das tabelas do `clube_novo`.

O Extrator pode conhecer primitivas genéricas de leitura (inteiro little-endian, bitfield, texto UTF-8, descompressão e parsing de CPK), mas não deve decidir por conta própria em qual endereço físico um dado semântico está.

## 2. Autoridade de leitura

Os próprios catálogos e tabelas normalizadas do `clube_novo` armazenam a referência física de seus dados. Exemplos:

- `atributo_jogo`: bit, largura, arquivo e endereço;
- `habilidade_jogo`: bit na carta, arquivo e endereço;
- `playstyle`: bit, arquivo, endereço e slot;
- `posicao_jogo`: bit de aptidão e endereço;
- `impeto_jogo`: arquivo, tamanho de registro, bit/largura do código e registros por fonte;
- `impeto_atributo_jogo`: bit/largura do delta, registro, arquivo, fonte e endereço;
- `tecnico_jogo`, `tecnico_estilo_jogo` e `tecnico_atributo_jogo`: arquivo, registro, bit/largura, hash e confirmação;
- `nacionalidade_jogo`, `clube_jogo` e `liga_jogo`: arquivo, registro, tamanho, offsets, larguras, hashes e contrato de extração.

O contrato ativo continua sendo o selo da execução: define versão autorizada, arquivos, fingerprints, campos e catálogos participantes. O executor local já carrega por `row_to_json` as linhas completas dos catálogos solicitados e as entrega ao Extrator em `catalogos`.

A hierarquia operacional é:

```text
TABELA/CATÁLOGO clube_novo
        ↓ fornece referência física
CONTRATO ATIVO
        ↓ sela versão/fingerprint e conjunto permitido
EXTRATOR + MÓDULOS ACESSÓRIOS
        ↓ executam a mesma lógica já existente
VALOR EXTRAÍDO
```

Se a tabela/catálogo não fornecer referência válida/confirmada para um item, a leitura correspondente deve falhar fechada. Não existe fallback produtivo para um endereço antigo escrito no código.

## 3. Por que essa regra existe

Uma atualização do jogo pode deslocar um único campo sem alterar os demais. Com milhares de valores, uma leitura no endereço antigo pode produzir um número aparentemente válido e mascarar o erro. Esse valor contaminaria cards, Otimizador e Bonificador.

Por isso:

- mudança física não comprovada = bloqueio;
- endereço antigo não é tentativa alternativa;
- banco legado não completa byte desconhecido;
- valor plausível não é prova de leitura correta;
- uma família bloqueada não é liberada porque outras famílias passaram;
- todos os módulos acessórios devem consumir as mesmas referências canônicas do Extrator principal.

## 4. Estado da migração em 29/08/2026

A migração anterior estava parcialmente implementada. Em 29/08/2026 a regra foi fechada de forma mais simples: **preservar a lógica existente e substituir apenas a origem das referências físicas**.

Já usam o caminho contratual em partes relevantes do fluxo:

- atributos do card;
- habilidades;
- estilos de IA;
- aptidões;
- corpo;
- slots de ímpeto;
- dados básicos do card no runtime V4.6;
- validação do selo/fingerprint do pedido de leitura.

Foram corrigidos também módulos acessórios:

- `executor/tecnicos.py`: removida a tabela local de bits das proficiências; bit/largura passam a ser exigidos da fotografia contratual/canônica;
- `executor/impetos.py`: removidos números físicos duplicados para catálogo, condições, parâmetros, alvos e membros; o módulo usa as próprias linhas canônicas do `clube_novo` como referência física;
- `executor/card_dimensions.py`: removidos endereços locais de nacionalidade, clube, liga, tipo e proveniência de vínculo; o comparador usa as referências das tabelas correspondentes.

O `app/leitura-contrato.js` exige fingerprint e tamanho de registro contratados antes da leitura.

Ainda existem trechos do `app/extrator-core.js` e rotinas de extração auxiliares que precisam ser auditados para garantir que nenhum endereço semântico residual permaneça como autoridade local. Até essa auditoria terminar, a escrita produtiva permanece bloqueada.

## 5. Regra para dados básicos do card

Nome, posição, altura, peso, idade, pé, forma, resistência a lesão, nacionalidade e demais campos básicos devem usar a referência entregue pelo banco/contrato, nunca uma cópia local do endereço.

Os campos novos da V4 — especialmente nacionalidade, clube e liga — seguem a mesma regra dos antigos: a lógica de leitura é a mesma; apenas o endereço vem da tabela/catálogo correspondente.

Transformações semânticas simples só podem ser aplicadas quando estiverem declaradas na referência/contrato ou forem tradução de apresentação que não altere o endereço físico.

## 6. Metadados e Dimensões

A ordem produtiva permanece:

```text
METADADOS / CATÁLOGOS
        ↓
VÍNCULOS FÍSICOS DOS CARDS
        ↓
CARDS NOVOS / ALTERADOS
        ↓
READBACK
```

Nacionalidade, clube, liga e tipo de carta precisam ser coletados antes de liberar os cards para os motores.

`executor/card_dimensions.py` preserva a comparação já existente, mas não fabrica mais `Player.bin`, `Country.bin`, bit de subtipo ou offsets como autoridade local. Esses valores são obtidos das linhas das tabelas `carta_jogo`, `nacionalidade_jogo`, `clube_jogo`, `liga_jogo` e `tipo_carta_jogo`.

O módulo de aplicação segura de dimensões continua separado da leitura. Nenhum catálogo ou vínculo ausente é apagado automaticamente.

## 7. Ímpetos

Ímpetos vêm dos arquivos físicos do próprio jogo. O fluxo antigo de site externo não é fonte oficial do V4.

`executor/impetos.py` mantém as mesmas comparações, contagens e validações, mas os endereços físicos usados como referência agora vêm de `impeto_jogo`, `impeto_atributo_jogo`, `impeto_condicao_jogo`, `impeto_condicao_parametro_faixa_jogo`, `impeto_condicao_nacionalidade_jogo`, `impeto_condicao_liga_jogo`, `impeto_condicao_classe_jogo` e `impeto_condicao_liga_membro_jogo`.

Os slots do card continuam usando a leitura contratual já implementada.

## 8. Boxes/coleções

O V4 não deve usar o coletor antigo de site como autoridade de box.

Há evidência física relacionada a `PlayerVariationDetail.bin`, mas box só é considerada pronta quando sua chave, endereço, cardinalidade e prova estiverem representados no catálogo/contrato ativo e forem consumidos pelo leitor. Até lá, a família permanece bloqueada para uso produtivo.

## 9. Técnicos

`Coach.bin` é a fonte física dos técnicos, mas o endereço de cada campo não pertence ao código do validador.

`executor/tecnicos.py` não mantém mais `STYLE_BITS`. Proficiências e boosts exigem bit/largura fornecidos pela fotografia canônica; as relações de técnico no banco armazenam arquivo, registro, bit, largura e hash.

Link-up permanece fora do contrato enquanto sua semântica/cardinalidade não estiver comprovada.

## 10. Textos oficiais

Textos oficiais vêm de `all.str` no `dt261_bra`. A chave canônica é seção + ID de texto. O adaptador de textos permanece separado, com preflight, confirmação, transação e readback.

## 11. Escrita e segurança

A escrita nunca é feita diretamente pelo navegador. O servidor local concentra credenciais e só pode operar contra `clube_novo`.

Nenhuma carga produtiva deve ser executada enquanto a auditoria de referências físicas estiver incompleta.

Após a migração:

1. executar leitura integral sem escrita;
2. validar fingerprints e cardinalidades;
3. comparar a fotografia com a referência já aprovada;
4. investigar qualquer divergência;
5. somente então selar/ativar o contrato;
6. aplicar metadados;
7. fazer readback;
8. aplicar cards;
9. reconciliar novamente os vínculos de cards novos;
10. liberar o Otimizador apenas com gates completos.

## 12. Relação com Otimizador e Bonificador

O Extrator produz insumos. Ele não altera a fórmula do Otimizador nem do Bonificador.

```text
Extrator aprovado
    ↓
Otimizador — validação contra builds legadas
    ↓
Bonificador — validação dos efeitos/condicionais
```

Nenhum card segue para os motores com falta causada por coleta incompleta.

## 13. Arquivos relevantes da V4.6

- `app/leitura-contrato.js` — leitor neutro; executa primitivas de leitura;
- `app/contrato-v46-runtime.js` — runtime contratual dos cards;
- `app/extrator-core.js` — núcleo existente; lógica deve ser preservada e referências fixas residuais substituídas;
- `executor/tecnicos.py` — validação de técnicos guiada por referência canônica;
- `executor/impetos.py` — validação de ímpetos guiada pelas tabelas canônicas;
- `executor/card_dimensions.py` — validação de dimensões guiada pelas tabelas canônicas;
- `executor/card_dimensions_apply.py` — aplicação segura posterior à leitura aprovada;
- `executor/servidor_v46.py` — servidor local V4.6;
- `app/metadados-v46.js` — painel da etapa de metadados;
- `INICIAR-EXTRATOR-V46.cmd` — iniciador direto da V4.6;
- `COMPILAR-EXTRATOR-V46.cmd` — reconstrução local do EXE.

## 14. Critério de conclusão da migração

A migração só é considerada concluída quando uma auditoria do caminho produtivo provar que:

- nenhum campo semântico depende de offset/bit hardcoded no Extrator ou em módulos acessórios;
- toda referência física aplicável vem da tabela/catálogo correspondente do `clube_novo`;
- todo arquivo exigido passa pelo fingerprint contratado;
- não há fallback para mapa/endereço antigo;
- a lógica de cálculo e extração permanece inalterada;
- a leitura integral read-only reproduz a referência aprovada ou toda divergência foi explicada e aprovada.

Constantes puramente genéricas de formato (por exemplo, estruturas CPK/WESYS) podem permanecer no código desde que não indiquem a localização semântica de um dado do jogo.

## 15. Regra de documentação

Toda implementação, alteração, exclusão ou mudança de comportamento no V4 deve atualizar o manual correspondente no mesmo conjunto de trabalho.

Código e documentação divergentes são pendência, não conclusão.