# Manual do Extrator eFootball

**Versão:** 4.3 · 27 de agosto de 2026  
**Estado da entrega:** diff automático pela base de `clube_novo`, referência interna versionada, envio manual operacional e zero escrita nos testes  
**Pasta operacional:** `C:\Users\Luis Fernando\Downloads\Clubefootball V4\7-VARREDURA-DO-JOGO`

## 1. Finalidade

O Extrator eFootball lê diretamente os arquivos físicos instalados pela Konami, converte os registros do jogo para o formato de `carta_jogo` e compara o estado atual com uma referência interna versionada ou com a base informada no modo incremental.

O fluxo normal não entrega uma recarga inteira. Ele entrega somente diferenças para conferência:

- cartas novas;
- campos comprovadamente alterados em cartas que já existem;
- cartas possivelmente inativas porque deixaram de aparecer na fonte atual;
- entradas novas, alteradas ou ausentes nos catálogos físicos.

A aplicação no Supabase é um segundo estágio, separado. Ela só pode acontecer no próprio aplicativo, por botão, depois de revisão, pré-voo e confirmação final. O usuário não abre o Supabase nem envia CSV manualmente. Não existe atualização automática.

## 2. Decisão de arquitetura

Esta versão foi construída como **um sistema novo e limpo**. Ela não depende do fluxo, do armazenamento interno nem do comportamento do extrator anterior.

Foi reaproveitado somente o que já tinha prova física: o mapa de bits, offsets, tamanhos de registro, chaves WESYS e leitura CPK. Esse contrato foi isolado em `app\mapeamento-fisico.js`, e o mapa de procedência legado em `app\catalog-source-map.js`. O extrator anterior e a versão imediatamente anterior à busca por família foram preservados para recuperação.

Arquitetura:

```text
arquivos físicos do jogo
        ↓ descoberta e validação por função
mapeamento-fisico.js + catalog-source-map.js → extrator-core.js → referência interna + interface e manifestos
                                             ↓ somente após revisão
                                      executor local seguro
                                             ↓ confirmação final
                                          Supabase
```

O navegador nunca recebe senha, connection string, `service_role` ou outra credencial privilegiada. O executor fica limitado a `127.0.0.1` e concentra toda conexão com o PostgreSQL/Supabase. Essa separação segue a recomendação do Supabase de manter segredos e chaves privilegiadas fora do frontend: [Securing your data](https://supabase.com/docs/guides/database/secure-data).

## 3. Fontes físicas e autoridade do mapeamento

O extrator trabalha **por família de dados**. Um CPK nunca substitui genericamente outro.

| Fonte | Operação | Papel comprovado |
|---|---|---|
| DT870 da atualização | cartas e catálogos | única fonte autoritativa da carga atual de cartas; habilidades; ímpetos atuais; overlay de playstyles |
| DT200 base | somente catálogos | base semântica de playstyles e ímpetos legados |
| DT870 original | somente catálogos | ímpetos legados exclusivos e conferência histórica |
| `dt261_bra` | somente catálogos | `all.str` e textos em português |

Fotografias validadas em 27/08/2026:

| Papel | Tamanho | SHA-256 |
|---|---:|---|
| DT870 da atualização | 9.415.400 bytes | `44df868c2613d532292d87072c0863a907d6a5f0cc40f914d355e56d74edfcc5` |
| DT200 base | 9.910.363 bytes | `fd920cd8e7f3f1089892ef4051c68c1c5c56c49000ecf6f751025a0ae2c94a50` |
| DT870 original | 5.007.376 bytes | `ae0d8cef26804439e9930ef8959f8d9425754d0e290d056b3e4d1f7b999edd5c` |
| Textos em português | 258.498 bytes | `2419045a081a151f8a0cdcc70a9ca0c4ca1ca265b8467b9c182623baa05338db` |

Arquivos internos comprovados:

| Arquivo físico | Papel | Contrato |
|---|---|---|
| `Player.bin` atualizado | cartas | 400 bytes por registro; `card_id` original Konami em u64 no offset 8 |
| `PlayerVariationDetail.bin` | box/coleção | 168 bytes; `card_id` u64 no offset 0 |
| `PlayerAppearance.bin` | corpo | 64 bytes; `card_id` u64 no offset 0 |
| `PlayerSkill.bin` | habilidades | 104 bytes; ID u32 little-endian no byte 0 |
| `PlayerBooster.bin` | ímpetos | DT200/atualização com registro de 40 bytes; DT870 original usa mapa legado selado por fingerprint |
| `Playstyle.bin` | playstyles | DT200 é conteúdo semântico; DT870 atualizado é overlay; o DT870 original não contém esse arquivo |
| `all.str` | textos | vem exclusivamente do `dt261_bra`; fonte validada antes de qualquer leitura de catálogo |

O mapa humano original continua em `4-DOCUMENTOS\MAPA-DO-CODIGO-DO-JOGO.md`. A leitura operacional fica em `app\mapeamento-fisico.js`; a procedência legada selada fica em `app\catalog-source-map.js`. Um formato, endereço ou fingerprint incompatível interrompe a família correspondente. O extrator não tenta adivinhar ordem, converter um CPK em outro nem completar lacunas com metadados antigos.

### Busca automática

Ao abrir o aplicativo, o executor local procura e valida separadamente as quatro fontes nos locais conhecidos do jogo. A tela informa, em linguagem simples, o que foi encontrado e para qual operação serve.

- Para cartas, somente a ausência do DT870 da atualização pede intervenção.
- Para catálogos, é pedido somente o arquivo que falta naquela operação.
- O botão **Escolher somente esta pasta** aparece apenas para fonte ausente ou inválida.
- A pasta escolhida é examinada localmente; nenhuma credencial ou arquivo é enviado à internet.
- Arquivo encontrado e válido em local conhecido é sempre usado automaticamente.
- Escolha manual só aparece quando a busca falha de forma verificável: fonte ausente, inacessível, inválida ou ambígua.
- Nunca existe seletor de CSV para a referência integral de cartas.

## 4. Como iniciar

1. Abra a pasta `7-VARREDURA-DO-JOGO`.
2. Dê dois cliques em `Extrator eFootball.exe`, identificado pelo ícone de bola, lupa e seta verde.
3. Aguarde a janela própria do aplicativo mostrar as fontes encontradas.
4. Escolha a operação desejada. Em condições normais não é necessário informar pasta nem executar comandos.

O `.cmd`, o PowerShell e o HTML não são opções concorrentes de uso comum; ficam apenas como componentes internos ou recuperação. O aplicativo abre o executor oculto, mantém a escrita desligada e apresenta somente a interface. A janela também se chama **Extrator eFootball**.

O aplicativo reaproveita a configuração já existente do projeto para identificar o Supabase e a credencial PostgreSQL já guardada com segurança no ambiente do Windows. A senha não é copiada para a pasta do extrator. A conexão direta usa SSL, conforme a documentação oficial: [Connect to your database](https://supabase.com/docs/guides/database/connecting-to-postgres). Nunca coloque senha no HTML, no JavaScript, em `configuracao.exemplo.json` ou em manifesto.

## 5. Modo 01 — Atualização por diff

Este é o modo normal.

### O que ele lê

1. `clube_novo.carta_jogo`, carregada automaticamente pelo executor em transação PostgreSQL somente leitura.
2. O DT870 da atualização localizado e validado automaticamente.

O usuário não escolhe CSV. Ao abrir ou clicar na aba **Atualização por diff**, o aplicativo inicia a comparação assim que a fonte física e a conexão de leitura estiverem prontas.

### O que ele faz

1. Valida exatamente as 29 colunas do contrato.
2. Extrai todas as cartas físicas válidas.
3. Deduplica e compara pelo `card_id` original Konami.
4. Compara todos os campos, não apenas uma assinatura resumida.
5. Gera três categorias:
   - **nova:** o `card_id` não existia na base;
   - **alterada:** o `card_id` existia e um ou mais campos mudaram; o manifesto registra `antes` e `depois`;
   - **possível inativa:** o `card_id` existia na base e não aparece na fonte atual.

Ao terminar, a interface sempre apresenta um estado visível:

- **NOVA CARGA IDENTIFICADA**, com contagens e o botão **OK — preparar envio ao clube_novo**;
- **SEM MUDANÇAS**, quando jogo e `clube_novo` já são iguais;
- **COMPARAÇÃO BLOQUEADA**, com o motivo em linguagem simples e sem habilitar envio.

### O que ele mostra e gera

- contagens atuais, novas, alteradas, possíveis inativas e duplicadas;
- tabela revisável por carta;
- CSV `carta_jogo_INCREMENTAL.csv`, somente com novas e alteradas;
- manifesto `MANIFESTO-CARTAS-DIFF.json`;
- CSV separado de possíveis inativas.

Novas e alteradas começam selecionadas para revisão. Possíveis inativas começam desmarcadas. A tabela `clube.carta_jogo` atualmente não tem uma coluna canônica de ativo; por isso o executor bloqueia inativação automática.

## 6. Modo 02 — Metadados

Este modo é independente das cartas.

### O que ele lê

1. Uma fotografia JSON dos catálogos atuais do sistema.
2. As quatro fontes localizadas automaticamente, cada uma usada somente em sua família.

### Famílias suportadas nesta atualização

- **habilidades:** DT870 atualizado;
- **ímpetos:** união canônica de DT870 atualizado, DT200 e DT870 original, sempre com procedência;
- **playstyles:** DT200 como base semântica e DT870 atualizado como overlay;
- **posições:** `Player.bin` atualizado mais o mapa físico comprovado.

A união de ímpetos validada contém 440 IDs. Trinta e dois não aparecem no DT870 atualizado: 3 existem somente no DT200, 28 somente no DT870 original e 1 nos dois legados. Remover os arquivos legados perderia dados reais.

### Famílias não suportadas nesta atualização

Textos por entrada, técnicos, catálogo nominal de estilos de IA, efeitos completos de ímpetos, nacionalidades, times/vínculos, POTW e habilidade extra de variação aparecem como **Não suportada nesta atualização**. A fonte de textos é corretamente identificada como `dt261_bra`, mas a atualização por entrada continua bloqueada enquanto o recorte canônico atual não fechar com o CPK. Essas famílias geram diagnóstico, nunca itens carregáveis.

### Regras

- a saída contém somente entradas novas, alteradas ou ausentes;
- nenhum item começa selecionado;
- mudança de conteúdo só é afirmada quando existe fingerprint físico anterior comparável;
- presença igual sem fingerprint anterior não é chamada de “alteração”;
- catálogo sem gabarito é identificado como `sem_gabarito`;
- itens sem adaptador canônico habilitado são bloqueados pelo executor, mesmo que sejam selecionados na tela.

Essa regra evita inventar nomes, traduções, efeitos, ordem ou significado a partir de bytes que só provam presença.

## 7. Modo 03 — Recarga completa

Este modo é contingência, não é o fluxo normal.

O usuário faz somente duas ações: marca a confirmação simples de operação pesada e clica em **Validar carga completa**. Não digita frase técnica e não escolhe CSV.

O executor mantém uma referência interna selada em `artefatos\referencias-cartas`:

- `referencia-vigente.json` aponta para a versão atual;
- cada versão fica em `versoes\ref-<hash-da-fonte>-<hash-da-carga>`;
- cada versão contém a carga integral e seu manifesto, ambos validados por SHA-256;
- versões anteriores nunca são substituídas ou apagadas pela promoção normal.

Se o DT870 físico tiver o mesmo SHA-256 da referência vigente, o aplicativo valida a integridade interna e mostra **VALIDAÇÃO CONCLUÍDA**. Não repete uma extração pesada sem necessidade.

Se o DT870 mudou, o aplicativo automaticamente:

1. extrai todas as cartas do zero;
2. confere as 29 colunas, contagem, `card_id` únicos, duplicidade e campos estruturados;
3. compara todos os campos pelo `card_id` contra a referência anterior;
4. mostra novas, alteradas e possíveis inativas;
5. se tudo estiver consistente, cria e sela uma nova versão e preserva a anterior.

Qualquer falha física, estrutural, de hash ou de comparação mantém a referência anterior e mostra **VALIDAÇÃO BLOQUEADA** com motivo simples. A recarga nunca envia dados ao banco automaticamente.

Os antigos CSVs e provas manuais continuam preservados em `RESULTADOS-E-VALIDACOES` e `RECUPERACAO` apenas como evidência histórica; o usuário não precisa localizá-los, escolhê-los ou mantê-los.

## 8. Enviar a carga validada — fluxo único

### Estágio 1: extrair e validar

É sempre somente leitura. O manifesto recebe:

- `execution_id` único;
- SHA-256 da fonte e da base;
- SHA-256 do próprio manifesto;
- prazo de validade;
- contagens e validações;
- alterações por campo.

### Estágio 2: OK, pré-voo e confirmação final

Depois da validação, aparece um único painel **Enviar carga validada ao banco**. O botão **OK — preparar envio ao clube_novo** usa exclusivamente o pacote da execução atual. Não há seletor de CSV, campo de caminho ou upload manual.

O aplicativo identifica sozinho:

- **atualização incremental:** envia integralmente novas, alteradas e inativações canonicamente suportadas do diff selado;
- **recarga completa:** abre a referência integral vigente, compara em leitura com `clube_novo.carta_jogo` e transforma somente as diferenças reais em operações idempotentes;
- **pacote já igual ao banco:** informa que não há nada para enviar e não cria confirmação.

O executor:

1. fixa o destino em `clube_novo.carta_jogo` e bloqueia qualquer configuração para `clube`;
2. verifica o contrato e o hash do manifesto;
3. recusa manifesto expirado, adulterado ou já consumido;
4. deduplica as chaves selecionadas;
5. confere cada item selecionado contra seu SHA-256 individual selado no manifesto;
6. abre o banco em modo somente leitura para o preflight;
7. confirma que cartas novas ainda não existem e que os valores `antes` das alterações ainda batem;
8. mostra em português simples o tipo de carga, destino, quantas inserir/atualizar/inativar e que `clube` ficará intocado;
9. cria um token descartável ligado ao hash da seleção;
10. exige caixa de revisão, frase final específica da execução e o clique **Aplicar esta carga no clube_novo**.

Quando a escrita estiver autorizada em uma tarefa futura, a aplicação:

- é executada inteiramente pelo aplicativo; o usuário nunca abre o Supabase;
- usa transação `SERIALIZABLE` e trava consultiva do lote;
- aplica por `card_id`/chave canônica;
- insere de forma idempotente;
- altera somente os campos comprovados no diff;
- falha e reverte tudo se qualquer precondição divergir;
- lê novamente dentro da transação;
- faz novo readback somente leitura depois do commit;
- grava manifesto de aplicação com a seleção, hashes, resultado e plano de recuperação.

### Estado desta entrega

A conexão real está configurada e o envio manual está operacional, mas nunca fica armado ao abrir o aplicativo. O botão final nasce desativado e só é habilitado para o token do pacote atual depois de quatro condições: pré-voo de leitura aprovado, destino `clube_novo.carta_jogo`, caixa de conferência marcada e frase exata digitada.

Nesta implementação, a aplicação real não foi clicada. O pré-voo real encontrou 269 inserções, 34 alterações e zero inativações; antes e depois dele, `clube` e `clube_novo` continuaram com 42.803 linhas e o mesmo fingerprint. Assim, o painel está pronto sem ter usado sua capacidade de escrita durante o teste.

## 9. Credenciais e configuração local

Arquivos distribuídos:

- `configuracao.exemplo.json`: configuração segura, com escrita desligada;
- `CREDENCIAIS-NAO-VAO-AQUI.txt`: lembrete permanente;
- `executor\executor_local.py`: backend local;
- `executor\vendor`: dependências já testadas;
- `requirements.txt`: alternativa para reinstalação.

Configuração usada, sem expor conteúdo sensível:

- o `config.txt` já existente na pasta principal identifica o projeto;
- `SUPABASE_DB_PASSWORD` já está guardada no ambiente do usuário do Windows e é herdada somente pelo executor local;
- `CLUBEF_SUPABASE_DB_URL` continua aceito apenas como substituição administrativa opcional;
- `CLUBEF_EXTRACTOR_PORT` define a porta local opcional; padrão 8765.

Não use `service_role` no navegador. Chaves secretas e `service_role` ignoram RLS e devem permanecer somente em backend seguro, conforme [Understanding API keys](https://supabase.com/docs/guides/getting-started/api-keys).

A configuração distribuída mantém `write_enabled=false` ao iniciar e permite apenas a armação manual de um pacote de cartas depois do pré-voo. O destino é validado em código como `clube_novo.carta_jogo`; qualquer configuração que aponte para `clube` é recusada. O schema `clube` permanece referência e recuperação.

## 10. Como validar cada execução

Antes de considerar um diff pronto para revisão, confirme:

1. o painel mostra o DT870 da atualização como fonte de cartas;
2. o modo de cartas exige somente essa fonte;
3. o modo de catálogos mostra separadamente DT870 atualizado, DT200, DT870 original e `dt261_bra`;
4. nenhuma fonte ausente foi substituída por outro CPK;
5. os hashes das fontes usadas estão no manifesto;
6. schema atual e anterior têm as mesmas 29 colunas;
7. `card_ids` únicos = total atual;
8. duplicadas = zero;
9. novas + alteradas + inalteradas = total atual;
10. possíveis inativas foram revisadas separadamente;
11. alterações mostram campos e valores `antes`/`depois`;
12. catálogos sem fingerprint anterior não aparecem falsamente como alterados;
13. famílias sem mapeamento integral aparecem como **Não suportada nesta atualização** e geram zero itens carregáveis;
14. o preflight informa `transaction_read_only=true` antes da confirmação final;
15. o resumo da aplicação é igual ao conjunto selecionado;
16. o manifesto de dry-run ou aplicação foi guardado.

Na recarga completa, a conferência de SHA-256 da fonte, do CSV integral e do manifesto é automática. O usuário aceita somente **VALIDAÇÃO CONCLUÍDA** ou **NOVA CARGA VALIDADA**. **VALIDAÇÃO BLOQUEADA** preserva a referência anterior e impede o envio.

## 11. Referência de leitura do banco

O banco é usado como referência de leitura, não como fonte que substitui os arquivos do jogo.

Nesta validação:

- `clube.carta_jogo`: 42.803 cartas e 42.803 `card_id` únicos;
- amostra determinística: 54 cartas, cobrindo dois exemplos por combinação de tipo e posição disponível;
- resultado: 54/54 iguais em todos os campos comparados;
- consulta: transação PostgreSQL confirmada como somente leitura.

As diferenças do patch não foram mascaradas pelo banco: 269 cartas novas e 34 cartas alteradas apareceram no manifesto.

A referência integral interna contém 43.072 cartas e 43.072 IDs únicos. Seu conjunto de IDs é exatamente a união comprovada da carga anterior de 42.803 com os 269 lançamentos, e 54/54 cartas da amostra do banco coincidiram em todos os campos.

Antes e depois do teste local, `clube.carta_jogo` e `clube_novo.carta_jogo` permaneceram com 42.803 linhas, 42.803 IDs únicos e fingerprint integral `ff67b8a2e544570dae42ed71d8428821`. As duas fotografias foram feitas com `transaction_read_only=true`; nenhuma escrita ocorreu.

## 12. Salvaguardas

- nenhuma credencial no HTML;
- servidor apenas em `127.0.0.1`;
- política de conteúdo restritiva na página;
- escrita desligada por padrão;
- manifesto selado e com validade curta;
- cada item aplicável selado individualmente; linha ou campo adulterado é bloqueado;
- token de aprovação descartável;
- execução não reutilizável;
- comparação pelo `card_id` original;
- duplicidade bloqueia o lote;
- conflito entre o diff e o estado atual do banco bloqueia o lote;
- possível inativação não é aplicada sem coluna/adaptador canônico;
- catálogo ambíguo não é aplicado;
- falha em qualquer etapa reverte a transação;
- readback obrigatório após eventual commit;
- legado preservado e nova versão instalada em pasta separada por finalidade.
- referência integral com apontador atômico; uma promoção só acontece depois de validação estrutural e comparação integral;
- versões de referência anteriores preservadas para recuperação;
- pacote de banco ligado ao manifesto da execução atual, sem aceitar CSV avulso.

## 13. Recuperação

### Falha antes do commit

A transação é revertida automaticamente. Nenhum dado parcial deve permanecer.

### Falha depois de um commit confirmado

1. Pare o executor local.
2. Abra o `MANIFESTO-APLICACAO-*.json` correspondente.
3. Use `selected_items` e `recovery_plan` para gerar um novo diff inverso.
4. Revise as cartas inseridas que seriam candidatas à remoção e os campos alterados que seriam restaurados.
5. Faça preflight/readback novamente.
6. Aplique a recuperação somente com autorização própria. O executor nunca apaga ou restaura automaticamente.

### Recuperar o extrator anterior

1. Pare o executor.
2. Não apague a pasta nova.
3. Use `RECUPERACAO\2026-08-27-ANTES-ICONE-E-NOME` para restaurar a versão 4.0 anterior, `RECUPERACAO\2026-08-27-ANTES-BUSCA-POR-FAMILIA` para a versão anterior à busca por família, ou `RECUPERACAO\2026-08-26` para o legado original.
4. Compare o SHA-256 com o manifesto da entrega antes de restaurar.

### Recuperar uma referência integral anterior

1. Pare o aplicativo.
2. Abra `artefatos\referencias-cartas\versoes` e localize a versão pelo manifesto.
3. Verifique o SHA-256 de `carta_jogo.csv` e de `manifesto.json`.
4. Atualize `referencia-vigente.json` somente por procedimento de recuperação autorizado; nunca apague a versão atual.
5. Reabra o aplicativo e aceite somente se a referência e a fonte forem validadas.

## 14. Limites conhecidos

- 19 cartas continuam sem nacionalidade; eram as mesmas 19 na base anterior, portanto não são regressão do novo extrator.
- Técnicos, textos por entrada, efeitos completos de ímpetos, nacionalidades, times/vínculos, POTW, habilidade extra de variação e catálogo nominal de estilos de IA ficam explicitamente não suportados nesta atualização; presença do arquivo não é confundida com mapeamento completo.
- Habilidades, ímpetos e playstyles têm presença comparável, mas a fotografia anterior do banco pode não conter o registro físico bruto. Conteúdo interno sem fingerprint anterior não é chamado de alteração.
- O DT870 original tem formato legado próprio em `PlayerBooster.bin`. Seus 102 endereços são aceitos somente com o fingerprint selado do CPK auditado; se o arquivo mudar, a família falha fechada até o mapa ser revalidado.
- O executor não inventa nomes/traduções/efeitos ausentes nos bytes.
- `clube.carta_jogo` não tem uma coluna canônica de ativo; possíveis inativações ficam apenas para revisão.
- A aplicação real de catálogos permanece bloqueada até existir adaptador canônico específico, testado e habilitado.
- O navegador precisa oferecer `DecompressionStream`, disponível em Chromium moderno.

## 15. Sequência posterior para uma carga aprovada

1. Guardar fonte, base, diff, manifesto e hashes.
2. Revisar as 269 cartas novas e as 34 alterações desta execução.
3. Decidir separadamente qualquer possível inativação; nesta execução foram zero.
4. Executar o preflight de leitura pelo botão.
5. Confirmar que as contagens e precondições continuam iguais.
6. Abrir uma tarefa específica com autorização explícita de escrita.
7. No próprio aplicativo, marcar a confirmação, digitar a frase do pacote atual e clicar **Aplicar esta carga no clube_novo**.
8. Guardar automaticamente o manifesto de aplicação/readback e o plano de recuperação.
9. Exportar nova fotografia completa e torná-la a próxima base somente depois do readback.
10. Atualizar catálogos em lote separado.
11. Nesta entrega, `clube` e `clube_novo` continuam intactos; um teste futuro do botão de subida deve ter nova autorização explícita e alvo limitado a `clube_novo.carta_jogo`.
12. Só depois tratar relações normalizadas, catálogos, motores ou tela, cada um em sua própria etapa.

## 16. Organização permanente

```text
7-VARREDURA-DO-JOGO\
├── Extrator eFootball.exe
├── DOCUMENTACAO\
│   ├── COMO-USAR.md
│   ├── MANUAL-DO-EXTRATOR.md
│   └── RELATORIO-FINAL-EXTRATOR-2026-08-27.md
├── RECUPERACAO\
│   ├── 2026-08-27-ANTES-ICONE-E-NOME\
│   ├── 2026-08-27-ANTES-BUSCA-POR-FAMILIA\
│   ├── 2026-08-26\
│   └── ARQUIVOS-LEGADOS-DA-PASTA\
└── RESULTADOS-E-VALIDACOES\2026-08-27\
    ├── FONTES-E-BASE\
    ├── DIFF-CARTAS\
    ├── DIFF-METADADOS\
    ├── VALIDACAO-E-TESTES\
    ├── GABARITO-TESTE\CPK-2026-08-27\
    ├── PLANO-BANCO\
    └── RECUPERACAO\
```

Os componentes internos necessários (`HTML`, `app`, `executor` e configuração segura) permanecem ocultos na raiz operacional. Essa árvore deixa visível um único lançador e permite encontrar documentação, resultados, provas e recuperação sem depender de diretórios temporários.

Dentro dos componentes internos, `artefatos\referencias-cartas\referencia-vigente.json` e `artefatos\referencias-cartas\versoes` guardam a referência automática. O usuário não precisa abrir essa pasta no uso normal.

## 17. Ícone e nome do aplicativo

O único lançador visível se chama `Extrator eFootball.exe`. Seu ícone de bola, lupa e seta de extração foi incorporado ao próprio executável em nove resoluções nativas do Windows, de 16 a 256 pixels. O título da janela é `Extrator eFootball`.

Se o Explorer estiver aberto durante uma troca de versão, pressione `F5` uma vez para atualizar a miniatura. A validação oficial não depende do cache visual: ela extrai o recurso do executável instalado, confirma o nome e a descrição do produto e compara o ícone com o lançador anterior.

O histórico completo da identidade e da reorganização está em `DOCUMENTACAO\IDENTIDADE-VISUAL-E-ORGANIZACAO.md`.
