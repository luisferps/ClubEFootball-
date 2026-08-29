# Manual do Extrator eFootball

**Versão:** 4.5 · 28 de agosto de 2026  
**Estado da entrega:** abertura automática, referências internas versionadas, envio manual operacional com idempotência e aplicação de cartas auditada  
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
| `Coach.bin` | técnicos | 176 bytes; ID u64 no bit 0; nomes nos bytes 32/78/124; cinco proficiências históricas, Sobreposição no bit 135/largura 7, dois slots de boost, idade no bit 231, nacionalidade no bit 170 e afinidade no bit 187 |
| `Country.bin` | nacionalidades de técnicos | 1.488 bytes por registro; código no bit 10, sigla no offset 708 e nome pt-BR UTF-8 no offset 788 |
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
3. Aguarde o painel **Resumo desta abertura** terminar as comparações automáticas.
4. Leia o indicador: verde significa **Tudo atualizado**; vermelho significa **Atualização disponível** ou uma verificação bloqueada que exige atenção.
5. Abra detalhes somente se quiser revisar o conjunto ou preparar uma aplicação manual. Em condições normais não é necessário escolher operação, arquivo ou pasta.

O `.cmd`, o PowerShell e o HTML não são opções concorrentes de uso comum; ficam apenas como componentes internos ou recuperação. O aplicativo abre o executor oculto, mantém a escrita desligada e apresenta somente a interface. A janela também se chama **Extrator eFootball**.

O aplicativo reaproveita a configuração já existente do projeto para identificar o Supabase e a credencial PostgreSQL já guardada com segurança no ambiente do Windows. A senha não é copiada para a pasta do extrator. A conexão direta usa SSL, conforme a documentação oficial: [Connect to your database](https://supabase.com/docs/guides/database/connecting-to-postgres). Nunca coloque senha no HTML, no JavaScript, em `configuracao.exemplo.json` ou em manifesto.

## 5. Modo 01 — Atualização por diff

Este é o modo normal.

### O que ele lê

1. `clube_novo.carta_jogo`, carregada automaticamente pelo executor em transação PostgreSQL somente leitura.
2. O DT870 da atualização localizado e validado automaticamente.

O usuário não escolhe CSV. Ao abrir o EXE, o aplicativo inicia a comparação assim que a fonte física e a conexão de leitura estiverem prontas. O conjunto revisável e o resumo aparecem antes das fontes e opções técnicas.

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
- **ímpetos:** união canônica de DT870 atualizado, DT200 e DT870 original, sempre com procedência; no layout atual, tipo no bit 296/largura 3 e espelho `u32` no bit 64;
- **playstyles:** DT200 como base semântica e DT870 atualizado como overlay;
- **posições:** `Player.bin` atualizado mais o mapa físico comprovado.
- **técnicos:** `Coach.bin` do DT870 atualizado; ID físico `u64`, nomes, cinco
  proficiências históricas de estilo de equipe, Sobreposição quando o campo físico é
  maior que zero e até dois boosts normalizados por atributo, ordem e delta; idade,
  nacionalidade e afinidade são extraídas do mesmo registro.
  A referência interna vigente contém 1.478 técnicos atuais.
- **nacionalidades de técnicos:** 214 códigos de `Country.bin`, com nome pt-BR,
  sigla, endereço, codificação, hash e presença nas três versões auditadas.
- **afinidades de técnicos:** códigos físicos 0–7; zero é ausência legítima e
  somente o código 5 expõe rótulo (`Jogadores de AT`/`Atacantes`) porque é o único
  vínculo código-texto comprovado.
- **textos oficiais:** `all.str` do `dt261_bra_console_win.cpk`, identificado pela
  chave canônica composta (`secao`, `id_texto`). A fotografia vigente contém
  11.679 chaves únicas, zero duplicidade e procedência física completa. O Extrator
  compara automaticamente com `clube_novo.texto_do_jogo` e só oferece envio manual
  do pacote integral que ele próprio acabou de extrair e validar.

A união de ímpetos validada contém 440 IDs. Trinta e dois não aparecem no DT870 atualizado: 3 existem somente no DT200, 28 somente no DT870 original e 1 nos dois legados. Remover os arquivos legados perderia dados reais.

Nos registros atuais de 40 bytes, o Extrator emite `tipo_condicao_raw`, registro,
hash do `PlayerBooster.bin`, bit 296/largura 3 e o espelho no bit 64/largura 32.
O valor físico 4 não é promovido a tipo de efeito: código 136 vira
`tipo_condicao_status=vaga_de_slot`; outros registros legados `raw4` permanecem
`registro_nao_impeto_raw4`. Rótulos de tipo não são inferidos pelo número.

O contrato operacional `clubef-impetos-physical-v1` relê também os 26 campos de
efeito (largura 5), os alvos de nacionalidade/liga/clube, as classes 299/302,
o corte 207, o nível 212, as faixas derivadas e os vínculos anterior/posterior
de `CompetitionUnit.bin`. A validação segura é feita por
`POST /api/impetos/validate`, sempre em transação somente leitura.

Os dois slots de `Player.bin` são lidos com 10 bits: slot 2 no bit 288 e slot 1
no bit 308. A nomenclatura histórica “slot condicional” não é usada como regra,
pois há tipos condicionais nos dois slots.

### Famílias não suportadas nesta atualização

Catálogo nominal de estilos de IA, times/vínculos,
POTW e habilidade extra de variação aparecem como
**Não suportada nesta atualização**. Dentro de técnicos, Link-up permanece adiado:
ainda não tem semântica/cardinalidade integralmente provadas e não bloqueia a família
Técnicos. Sobreposição deixou de ser pendência após a prova física do bit 135.
Essas famílias ou subfamílias geram diagnóstico, nunca itens carregáveis.

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
3. recusa manifesto expirado ou adulterado e identifica a execução por `execution_id` + hash da seleção;
4. deduplica as chaves selecionadas;
5. confere cada item selecionado contra seu SHA-256 individual selado no manifesto;
6. abre o banco em modo somente leitura para o preflight;
7. confirma que cartas novas ainda não existem e que os valores `antes` das alterações ainda batem;
8. mostra em português simples o tipo de carga, destino, quantas inserir/atualizar/inativar e que `clube` ficará intocado;
9. cria um token ligado ao hash da seleção e reutiliza o mesmo token quando o pré-voo da mesma execução é repetido;
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

Todo botão que inicia trabalho demorado muda imediatamente para **Preparando** ou **Aplicando**, desabilita os controles de ação e mostra progresso simples. O término obrigatório é sucesso com readback, sem mudanças ou erro/bloqueio com motivo. Se a resposta da aplicação se perder, a interface consulta o estado pelo `execution_id` antes de permitir nova tentativa. No servidor, uma segunda requisição simultânea recebe `applying`; uma execução já concluída reutiliza o manifesto persistido, sem gravar o lote de novo.

### Estado desta entrega

A conexão real está configurada e o envio manual está operacional, mas nunca fica armado ao abrir o aplicativo. O botão final nasce desativado e só é habilitado para o token do pacote atual depois de quatro condições: pré-voo de leitura aprovado, destino `clube_novo.carta_jogo`, caixa de conferência marcada e frase exata digitada.

Em 27 de agosto de 2026, uma aplicação manual autorizada concluiu 269 inserções, 34 alterações e zero inativações. A auditoria posterior, executada em transação somente leitura, provou `clube_novo.carta_jogo` com 43.072 IDs únicos e correspondência exata, por todos os 29 campos, à referência atual. `clube.carta_jogo` permaneceu intacta com 42.803 IDs e correspondência exata à carga legada. Depois dessa aplicação comprovada, nenhuma nova escrita foi feita durante as correções e testes da versão 4.4.

## 8.1 Abertura automática e metadados

Ao abrir, o aplicativo executa sem clique inicial:

1. localização das fontes conhecidas;
2. diff de cartas contra `clube_novo.carta_jogo` em leitura;
3. conferência das famílias de metadados contra a referência interna versionada;
4. consolidação em **Tudo atualizado**, **Atualização disponível** ou **Verificação bloqueada**.

Metadados não pedem mais `JSON`. A referência fica em `artefatos\referencias-metadados`,
com versões preservadas. A referência `meta-ref-eba124d25472-9db3bc3ebba1` contém
idade, nacionalidade e afinidade aos 1.478 técnicos, além dos catálogos comparáveis de
214 nacionalidades, oito códigos de afinidade e Sobreposição 96 somente em Antônio
Conte; a versão anterior foi preservada. Se as identidades físicas
forem iguais às da referência vigente, ela é reutilizada automaticamente. Se alguma
fonte mudar ou faltar, apenas as famílias dependentes ficam bloqueadas e a referência
anterior é preservada; não se inventa nem se promove conteúdo. Famílias sem cobertura
integral aparecem como **Não suportada nesta atualização**. Textos são a exceção já
fechada: possuem adaptador canônico específico, pré-voo, transação, idempotência,
readback e recuperação. Mesmo assim, nunca são escritos automaticamente; o usuário
precisa preparar e confirmar o pacote integral atual. As demais famílias continuam
bloqueadas para escrita.

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

A configuração distribuída mantém `write_enabled=false` ao iniciar. Ela permite a
armação manual de um pacote de cartas ou do pacote canônico integral de textos somente
depois do pré-voo. Os destinos são validados em código como
`clube_novo.carta_jogo` e `clube_novo.texto_do_jogo`; qualquer configuração que
aponte para `clube` é recusada. O schema `clube` permanece referência e recuperação.

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

Para Textos, confirme ainda: 11.679 chaves oficiais únicas na fotografia vigente,
zero duplicidade, procedência confirmada em todas as linhas, 166 referências de
catálogo resolvidas, zero referência sem texto e as oito FKs compostas validadas.
O fingerprint lógico do readback concluído em 28/08/2026 é
`56a205221af16addfe96f8452baffa8a`.

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

Registro histórico: no ensaio local anterior à aplicação de 27/08, as duas cópias
tinham 42.803 linhas e fingerprint `ff67b8a2e544570dae42ed71d8428821`.
Depois da aplicação autorizada, o estado vigente e relido é `clube.carta_jogo`
42.803 e `clube_novo.carta_jogo` 43.072.

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
- Técnicos são comparáveis para identidade, idade, nacionalidade, afinidade física,
  cinco proficiências históricas, Sobreposição e até dois boosts. Nacionalidades e códigos de afinidade também
  têm referência própria. Os rótulos de afinidade 1, 2, 3, 4, 6 e 7 permanecem
  bloqueados, sem inferência. Os
  Link-up continua explicitamente adiado;
  times/vínculos, POTW,
  habilidade extra de variação e catálogo nominal de estilos de IA continuam não
  suportados. Presença do arquivo não é confundida com mapeamento completo.
- Habilidades, ímpetos e playstyles têm presença comparável. Para ímpetos atuais, o tipo físico e sua procedência também integram o fingerprint; nome/comportamento continuam pendentes quando não há âncora oficial. Conteúdo interno sem fingerprint anterior não é chamado de alteração.
- O DT870 original tem formato legado próprio em `PlayerBooster.bin`. Seus 102 endereços são aceitos somente com o fingerprint selado do CPK auditado; se o arquivo mudar, a família falha fechada até o mapa ser revalidado.
- O executor não inventa nomes/traduções/efeitos ausentes nos bytes.
- `clube.carta_jogo` não tem uma coluna canônica de ativo; possíveis inativações ficam apenas para revisão.
- A aplicação real de catálogos permanece bloqueada, exceto para Textos, cujo
  adaptador canônico está testado e habilitado. O envio de Textos continua manual,
  integral e restrito a `clube_novo.texto_do_jogo`.
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
10. Atualizar catálogos em lote separado; Textos usam o próprio pacote integral
    selado do Extrator, e as demais famílias continuam sem aplicação genérica.
11. Nesta entrega de campos de técnico, `clube.carta_jogo` permaneceu com 42.803 e
    `clube_novo.carta_jogo` com 43.072; nenhuma carta foi escrita.
12. Só depois tratar relações normalizadas, catálogos, motores ou tela, cada um em sua própria etapa.

### Contrato de técnicos da versão 4.5

- `Coach.bin`: 176 bytes por registro, ID `u64` little-endian no bit 0;
- cinco proficiências: bits `206`, `238`, `224`, `199`, `213`, todos com 7 bits;
- Sobreposição (`overload`): bit `135`, largura 7; zero é ausência legítima e a
  relação só é criada quando o valor é maior que zero. No DT870 atual há uma única
  ocorrência: Antônio Conte (`17609097478250`) com 96;
- boosts: slots nos bits `160` e `148`, 5 bits; zero é ausência, valor-1 é o índice
  canônico do atributo e o delta atualmente comprovado é `+1`;
- idade: bit `231`, largura 7, transformação `valor físico + 14`;
- nacionalidade: código no bit `170`, largura 8, resolvido no `Country.bin` pelo
  código do bit 10, largura 9; nome pt-BR no offset 788 e sigla no offset 708;
- afinidade: código no bit `187`, largura 3; zero é ausência legítima; apenas o
  código 5 possui rótulo comprovado;
- destino canônico já validado: `clube_novo.tecnico_jogo`,
  `nacionalidade_jogo`, `afinidade_tecnico_jogo`, `tecnico_estilo_jogo` e
  `tecnico_atributo_jogo`;
- o Extrator compara e manifesta; a escrita de metadados permanece desabilitada até
  existir adaptador próprio com pré-voo, transação e readback.

O fonte operacional compara automaticamente essas três famílias contra a referência
interna. A validação de 28/08/2026 encontrou 1.478 IDs únicos, 214 nacionalidades,
oito afinidades e exatamente uma ocorrência de Sobreposição, com zero nova, alterada,
ausente ou sem fingerprint após selar a referência. O lançador
`Extrator eFootball.exe` não foi reconstruído nem executado nesta atualização; apenas
o núcleo-fonte validado foi instalado, com a versão anterior preservada em
`RECUPERACAO\2026-08-28-ANTES-SOBREPOSICAO-TECNICOS`.

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

Dentro dos componentes internos, `artefatos\referencias-cartas` e `artefatos\referencias-metadados` guardam as referências automáticas e suas versões. O usuário não precisa abrir essas pastas no uso normal.

## 17. Ícone e nome do aplicativo

O único lançador visível se chama `Extrator eFootball.exe`. Seu ícone de bola, lupa e seta de extração foi incorporado ao próprio executável em nove resoluções nativas do Windows, de 16 a 256 pixels. O título da janela é `Extrator eFootball`.

Se o Explorer estiver aberto durante uma troca de versão, pressione `F5` uma vez para atualizar a miniatura. A validação oficial não depende do cache visual: ela extrai o recurso do executável instalado, confirma o nome e a descrição do produto e compara o ícone com o lançador anterior.

O histórico completo da identidade e da reorganização está em `DOCUMENTACAO\IDENTIDADE-VISUAL-E-ORGANIZACAO.md`.

## 18. Nacionalidade, clube, liga e tipo de carta

Em 28/08/2026 o contrato `clubef-card-dimensions-physical-v2` passou a integrar o
fluxo automático de Metadados da mesma cópia cumulativa que contém Técnicos, Textos
e Relações das Cartas. O Extrator abre as quatro fontes por papel, relê as dimensões
e compara a fotografia integral com `clube_novo` por um endpoint exclusivamente
read-only. Nenhuma escrita é feita por essa verificação.

### Origem física

- `Player.bin`, registro de 400 bytes: `card_id` no offset 8; clube no offset 16;
  nacionalidade no bit 328/largura 10, resolvida por `floor(raw/2)`; tipo nos bits
  44–47 do `card_id`; subtipo no bit 104/largura 1.
- `Country.bin`, registro de 1.488 bytes: catálogo compartilhado por cartas e
  técnicos, byte-idêntico nas três fontes físicas comprovadas.
- `Team.bin`, registro de 1.600 bytes: união DT870 atualizado > DT200 > DT870
  original, sem fallback para legado.
- `CompetitionEntry.bin`, registro de 12 bytes, e `CompetitionUnit.bin`, registro de
  2.472 bytes: ponte clube → liga e catálogo de ligas.
- `PlayerDeleteList.bin`, registro de 8 bytes: associação operacional separada a
  `Jogador indisponível`.
- `all.str`: nomes oficiais dos tipos somente pelas chaves comprovadas.

### Resultado operacional vigente

A releitura encontrou 43.072 cartas únicas, 214 nacionalidades, 1.072 clubes, 75
ligas e 11 tipos. Todas as 43.072 cartas têm nacionalidade e tipo; 32.151 têm clube
e 30.157 têm liga. Há 7.598 cartas na lista de indisponíveis, 356 nos estados
provisórios e 354 bloqueios factuais por clube sem definição nominal. Todos os
órfãos e divergências de chave ficaram em zero.

Os estados `type=4/subtype=0` e `type=7/subtype=0` são mantidos como IDs técnicos
distintos, exibidos como `Desconhecido 1` e `Desconhecido 2`. O nome oficial e a
chave de texto permanecem nulos. A classificação de `PlayerDeleteList` não é usada
para preencher esses estados.

O status de evidência também é parte do readback. Os oito tipos jogáveis nomeados
usam `rotulo_dicionario_ancora_tela_sem_ponte_fisica`: o rótulo existe no
`all.str` e a associação foi guiada por tela, mas a auditoria DT200/DT870 não
encontrou uma ponte física estado → chave. `PlayerDeleteList` usa
`classificacao_operacional_usuario_sem_ponte_fisica`. Os dois desconhecidos usam
`provisorio_sem_prova_nominal`. Textos antigos `GOAT` e `Brilhante` foram
inventariados, mas não promovidos; ordem de dicionário não é prova.

Na abertura ou em **Comparar metadados novamente**, a interface garante que os bytes
das quatro fontes estejam carregados, executa a releitura e chama
`/api/card-dimensions/validate`. A validação só aprova quando cada linha e cada campo
normalizado de cartas, nacionalidades, clubes, ligas e tipos possui hash idêntico ao
banco, em transação `READ ONLY`. A amostra obrigatória Neymar Jr
`106755438714272` resolve para Brasil, Santos FC, Brasileirão Betano e
`Distinguido - Show Time` (`Any3W:422`).
