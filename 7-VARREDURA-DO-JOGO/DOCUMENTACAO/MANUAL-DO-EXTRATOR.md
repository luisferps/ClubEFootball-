# Manual do Extrator eFootball

**Versão:** 4.6 · 29 de agosto de 2026  
**Estado da entrega:** migração para contrato de leitura como autoridade física; execução produtiva permanece bloqueada até a migração integral e o teste read-only  
**Pasta operacional:** `Clubefootball V4\7-VARREDURA-DO-JOGO`

## 1. Finalidade

O Extrator eFootball é a primeira etapa do pipeline produtivo do ClubEFootball V4.

```text
EXTRATOR -> OTIMIZADOR -> BONIFICADOR
```

Regra central da arquitetura V4.6:

> **O contrato determina onde e como ler. O Extrator somente valida e extrai.**

O Extrator não é autoridade para endereço físico de dado do jogo. Ele pode conhecer primitivas genéricas de leitura (inteiro little-endian, bitfield, texto UTF-8, descompressão e parsing de CPK), mas não deve decidir por conta própria em qual offset/bit um campo semântico está.

## 2. Autoridade de leitura

Antes de uma leitura produtiva, o Extrator recebe o contrato ativo do banco. O contrato deve informar, conforme a família:

- arquivo/fonte;
- fingerprint SHA-256 esperado;
- tamanho de registro e estrutura esperada;
- chave canônica do campo;
- offset de byte ou bit inicial;
- largura;
- tipo de leitura;
- transformação permitida;
- estado da prova do campo;
- catálogos/requisitos necessários.

O leitor neutro é `app/leitura-contrato.js`. Ele valida o pedido, o fingerprint físico e o tamanho do arquivo antes de decodificar os campos autorizados.

Se o contrato não descreve/prova um campo necessário, a leitura deve falhar fechada. Não existe fallback produtivo para endereço antigo.

## 3. Por que essa regra existe

Uma atualização do jogo pode deslocar um campo sem alterar outros. Com milhares de valores, uma leitura no endereço antigo pode produzir um número aparentemente válido e mascarar o erro. Esse valor contaminaria cards, Otimizador e Bonificador.

Por isso:

- mudança física não comprovada = bloqueio;
- endereço antigo não é tentativa alternativa;
- banco legado não completa byte desconhecido;
- valor plausível não é prova de leitura correta;
- uma família bloqueada não é liberada porque outras famílias passaram.

## 4. Estado da migração em 29/08/2026

A migração anterior estava parcialmente implementada, mas não integralmente concluída.

Já usam o contrato em partes relevantes do fluxo:

- atributos do card;
- habilidades;
- estilos de IA;
- aptidões;
- corpo;
- slots de ímpeto;
- validação do selo/fingerprint do pedido de leitura.

Foi adicionada em 29/08/2026 a camada `app/contrato-v46-runtime.js`, que inicia a retirada dos dados básicos do card do caminho antigo. Ela resolve campos por `chave_campo` no contrato e não contém offsets físicos próprios.

O `app/leitura-contrato.js` também foi endurecido para exigir `tamanho_registro` em qualquer arquivo `wesys_raw`; assim uma leitura tabular não pode avançar sem a cardinalidade física declarada pelo contrato.

Ainda existem trechos legados em `app/extrator-core.js` com constantes/endereço físico hardcoded, principalmente em Dimensões e em alguns catálogos. Esses trechos são dívida de migração e **não podem ser considerados autoridade produtiva depois da V4.6**.

Enquanto essa retirada não terminar e não houver teste read-only aprovado, o contrato produtivo permanece bloqueado.

## 5. Regra para dados básicos do card

Nome, posição, altura, peso, idade, pé, forma, resistência a lesão, nacionalidade e demais campos básicos devem ser resolvidos pelo contrato.

O runtime V4.6 procura as chaves canônicas no pedido ativo e usa o leitor neutro para decodificá-las. O código do runtime não define o endereço desses campos.

Transformações semânticas simples só podem ser aplicadas quando estiverem declaradas no contrato ou forem tradução de apresentação que não altere o endereço físico.

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

O módulo de aplicação segura de dimensões continua separado da leitura. Ele só poderá gravar depois que a fotografia física tiver sido produzida pelo caminho contratual aprovado.

Nenhum catálogo ou vínculo ausente é apagado automaticamente.

## 7. Ímpetos

Ímpetos vêm dos arquivos físicos do próprio jogo. O fluxo antigo de site externo não é fonte oficial do V4.

Os slots do card já possuem leitura contratual. Efeitos, condições, alvos, faixas e relações de competição que ainda contenham endereço hardcoded no caminho operacional devem ser migrados antes de o consumidor ser liberado.

## 8. Boxes/coleções

O V4 não deve usar o coletor antigo de site como autoridade de box.

Há evidência e código físico relacionados a `PlayerVariationDetail.bin`, mas a documentação anterior dizia de forma ampla que a relação card-box já fazia parte integral do contrato produtivo. Essa afirmação fica corrigida: **box só é considerada pronta quando sua chave, endereço, cardinalidade e prova estiverem presentes no contrato ativo e forem consumidos pelo leitor contratual**. Até lá, a família permanece bloqueada para uso produtivo.

## 9. Técnicos

`Coach.bin` é a fonte física dos técnicos. Qualquer campo de técnico cujo endereço ainda esteja codificado diretamente no extrator precisa ser migrado para o contrato antes de ser considerado parte da arquitetura final.

Link-up permanece fora do contrato enquanto sua semântica/cardinalidade não estiver comprovada.

## 10. Textos oficiais

Textos oficiais vêm de `all.str` no `dt261_bra`. A chave canônica é seção + ID de texto. O adaptador de textos permanece separado, com preflight, confirmação, transação e readback.

## 11. Escrita e segurança

A escrita nunca é feita diretamente pelo navegador. O servidor local concentra credenciais e só pode operar contra `clube_novo`.

Mesmo existindo os módulos de aplicação V4.6, **nenhuma carga produtiva deve ser executada enquanto a migração contratual de leitura estiver incompleta**.

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

- `app/leitura-contrato.js` — leitor neutro; endereço vem do contrato;
- `app/contrato-v46-runtime.js` — runtime contratual para substituir leituras semânticas hardcoded;
- `app/extrator-core.js` — núcleo atual; ainda contém dívida de migração que deve ser eliminada do caminho produtivo;
- `executor/card_dimensions_apply.py` — aplicação segura de catálogos/vínculos, posterior à leitura aprovada;
- `executor/servidor_v46.py` — servidor local V4.6;
- `app/metadados-v46.js` — painel da etapa de metadados;
- `INICIAR-EXTRATOR-V46.cmd` — iniciador direto da V4.6;
- `COMPILAR-EXTRATOR-V46.cmd` — reconstrução local do EXE.

## 14. Critério de conclusão da migração

A migração só é considerada concluída quando uma auditoria do caminho produtivo provar que:

- nenhum campo semântico depende de offset/bit hardcoded no Extrator;
- todo arquivo tabular tem cardinalidade/tamanho definido pelo contrato;
- todo campo consumido está aprovado no contrato;
- todo arquivo exigido passa pelo fingerprint contratado;
- não há fallback para mapa/endereço antigo;
- a leitura integral read-only reproduz a referência aprovada ou toda divergência foi explicada e aprovada.

Constantes puramente genéricas de formato (por exemplo, estruturas CPK/WESYS) podem permanecer no código desde que não indiquem a localização semântica de um dado do jogo.

## 15. Regra de documentação

Toda implementação, alteração, exclusão ou mudança de comportamento no V4 deve atualizar o manual correspondente no mesmo conjunto de trabalho.

Código e documentação divergentes são pendência, não conclusão.