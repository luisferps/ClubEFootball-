# Manual do Extrator ClubEfootball

**Versão:** 3.1 · 27 de agosto de 2026  
**Estado da entrega:** sistema novo, validado com gabarito integral e instalado com escrita real bloqueada  
**Pasta operacional:** `C:\Users\Luis Fernando\Downloads\Clubefootball V4\7-VARREDURA-DO-JOGO`

## 1. Finalidade

O Extrator ClubEfootball lê diretamente os arquivos físicos instalados pela Konami, converte os registros do jogo para o formato de `clube.carta_jogo` e compara o estado atual com uma base explícita.

O fluxo normal não entrega uma recarga inteira. Ele entrega somente diferenças para conferência:

- cartas novas;
- campos comprovadamente alterados em cartas que já existem;
- cartas possivelmente inativas porque deixaram de aparecer na fonte atual;
- entradas novas, alteradas ou ausentes nos catálogos físicos.

A aplicação no Supabase é um segundo estágio, separado. Ela só pode acontecer por botão, depois de revisão, confirmação e validação do executor local. Não existe atualização automática.

## 2. Decisão de arquitetura

Esta versão foi construída como **um sistema novo e limpo**. Ela não depende do fluxo, do armazenamento interno nem do comportamento do extrator anterior.

Foi reaproveitado somente o que já tinha prova física: o mapa de bits, offsets, tamanhos de registro, chaves WESYS e leitura CPK. Esse contrato foi isolado em `app\mapeamento-fisico.js`. O extrator anterior foi preservado intacto em `VERSOES-ANTERIORES\2026-08-26` para referência e recuperação.

Arquitetura:

```text
arquivos físicos do jogo
        ↓ somente leitura
mapeamento-fisico.js → extrator-core.js → interface e manifestos
                                             ↓ somente após revisão
                                      executor local seguro
                                             ↓ confirmação final
                                          Supabase
```

O navegador nunca recebe senha, connection string, `service_role` ou outra credencial privilegiada. O executor fica limitado a `127.0.0.1` e concentra toda conexão com o PostgreSQL/Supabase. Essa separação segue a recomendação do Supabase de manter segredos e chaves privilegiadas fora do frontend: [Securing your data](https://supabase.com/docs/guides/database/secure-data).

## 3. Fontes físicas e autoridade do mapeamento

Fonte usada nesta versão:

```text
C:\ProgramData\KONAMI\eFootball\ST\Download\dt870_console_win.cpk
```

Fotografia validada em 27/08/2026:

- tamanho: 9.415.400 bytes;
- SHA-256: `44df868c2613d532292d87072c0863a907d6a5f0cc40f914d355e56d74edfcc5`;
- modificação física: 27/08/2026 04:08:04, horário de Brasília.

Arquivos internos usados:

| Arquivo físico | Papel | Contrato comprovado |
|---|---|---|
| `Player.bin` | cartas | 400 bytes por registro; `card_id` original Konami em u64 no offset 8 |
| `PlayerVariationDetail.bin` | box/coleção | 168 bytes; `card_id` u64 no offset 0 |
| `PlayerAppearance.bin` | corpo | 64 bytes; `card_id` u64 no offset 0 |
| `PlayerSkill.bin` | catálogo de habilidades | 104 bytes; ID u32 little-endian no byte 0 |
| `PlayerBooster.bin` | catálogo de ímpetos | 40 bytes; ID no bit 112, largura 10 |
| `Playstyle.bin` | catálogo de playstyles | 168 bytes; ID u32 little-endian no byte 0 |
| `Coach.bin` | catálogo de técnicos | 176 bytes; ID u32 little-endian no byte 0 |

O arquivo `4-DOCUMENTOS\MAPA-DO-CODIGO-DO-JOGO.md` é a referência humana original. A leitura operacional está congelada no arquivo `app\mapeamento-fisico.js`. Se um `Player.bin` deixar de ser múltiplo de 400 bytes ou um catálogo deixar de respeitar seu tamanho, a execução falha fechada; o extrator não tenta adivinhar uma nova ordem.

## 4. Como iniciar

1. Abra a pasta `7-VARREDURA-DO-JOGO`.
2. Dê dois cliques em `INICIAR-EXTRATOR.cmd`.
3. Quando perguntado se deseja conectar ao Supabase:
   - responda `N` para extrair e comparar sem banco;
   - responda `S` para fazer o preflight de leitura do botão de aplicação e cole a connection string PostgreSQL quando solicitada. Ela fica somente na memória do processo e não é salva.
4. O navegador abrirá `http://127.0.0.1:8765/Extrator-ClubEfootball.html`.

Para uma conexão local persistente, use uma connection string apropriada ao ambiente conforme a documentação oficial: [Connect to your database](https://supabase.com/docs/guides/database/connecting-to-postgres). Nunca coloque a senha no HTML, no JavaScript, em `configuracao.exemplo.json` ou em qualquer manifesto.

## 5. Modo 01 — Atualização por diff

Este é o modo normal.

### O que ele lê

1. Um CSV completo que representa a base atual aprovada do sistema.
2. O `dt870_console_win.cpk` atual.

### O que ele faz

1. Valida exatamente as 29 colunas do contrato.
2. Extrai todas as cartas físicas válidas.
3. Deduplica e compara pelo `card_id` original Konami.
4. Compara todos os campos, não apenas uma assinatura resumida.
5. Gera três categorias:
   - **nova:** o `card_id` não existia na base;
   - **alterada:** o `card_id` existia e um ou mais campos mudaram; o manifesto registra `antes` e `depois`;
   - **possível inativa:** o `card_id` existia na base e não aparece na fonte atual.

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
2. O `dt870_console_win.cpk` atual.

### Catálogos observados

- habilidades;
- ímpetos;
- playstyles;
- técnicos;
- posições;
- estilos de IA.

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

Para executá-lo é obrigatório:

1. selecionar o CPK atual;
2. marcar a caixa de entendimento;
3. digitar exatamente `RECARREGAR COMPLETO`.

Ele gera uma fotografia completa e um manifesto de validação. Uma base anterior pode ser adicionada para produzir um diff comparável. A carga completa nunca é enviada ao banco automaticamente. Qualquer aplicação posterior volta ao conjunto revisável por diff.

### Prova exata com o gabarito integral

O gabarito oficial desta entrega fica em `ENTREGAS\2026-08-27\GABARITO-TESTE\CPK-2026-08-27`. Ele foi extraído novamente do CPK, sem usar a extração ou o diff anterior como entrada, e depois validado por referências externas.

Para repetir a prova manual:

1. selecione o CPK cujo SHA-256 é `44df868c2613d532292d87072c0863a907d6a5f0cc40f914d355e56d74edfcc5`;
2. em **Gabarito ou base para comparar**, selecione `carta_jogo_GABARITO-INTEGRAL.csv`;
3. marque a caixa e digite `RECARREGAR COMPLETO`;
4. execute;
5. aceite somente se a tela mostrar **GABARITO EXATO**, 43.072 cartas, 43.072 IDs únicos, zero duplicadas, 29 campos e SHA-256 `07c9b8cf9690b1f177cd724ada4329351424b71fb8c6d09e4cd35d3875389c38`.

O gabarito tem atributo de somente leitura e é acompanhado de manifesto, fingerprints, amostra e instruções. Se a tela disser **DIVERGENTE**, nenhuma preparação ou aplicação deve continuar.

## 8. Aplicar dados aprovados — dois estágios

### Estágio 1: extrair e comparar

É sempre somente leitura. O manifesto recebe:

- `execution_id` único;
- SHA-256 da fonte e da base;
- SHA-256 do próprio manifesto;
- prazo de validade;
- contagens e validações;
- alterações por campo.

### Estágio 2: preparar e aplicar

Depois da revisão, o botão **Preparar aplicação / dry-run** envia somente a seleção da execução atual ao executor local.

O executor:

1. verifica o contrato e o hash do manifesto;
2. recusa manifesto expirado, adulterado ou já consumido;
3. deduplica as chaves selecionadas;
4. confere cada item selecionado contra seu SHA-256 individual selado no manifesto;
5. abre o banco em modo somente leitura para o preflight;
6. confirma que cartas novas ainda não existem e que os valores `antes` das alterações ainda batem;
7. mostra o resumo objetivo de inserções, alterações e inativações;
8. cria um token descartável ligado ao hash da seleção;
9. exige caixa de revisão e frase final específica da execução.

Quando a escrita estiver autorizada em uma tarefa futura, a aplicação:

- usa transação `SERIALIZABLE` e trava consultiva do lote;
- aplica por `card_id`/chave canônica;
- insere de forma idempotente;
- altera somente os campos comprovados no diff;
- falha e reverte tudo se qualquer precondição divergir;
- lê novamente dentro da transação;
- faz novo readback somente leitura depois do commit;
- grava manifesto de aplicação com a seleção, hashes, resultado e plano de recuperação.

### Estado desta entrega

A escrita real está bloqueada. Foram exigidas duas travas fora da tela:

1. `write_enabled=true` em uma cópia local chamada `configuracao.local.json`;
2. variável de processo `CLUBEF_ENABLE_REAL_WRITE=EU_AUTORIZO_ESCRITA_REAL`.

Nenhuma dessas travas foi habilitada nesta tarefa. O botão final permanece desativado e o endpoint de aplicação devolve bloqueio HTTP 403. O ensaio final preparou exatamente 269 inserções e 34 alterações, confirmou `transaction_read_only=true`, encontrou 303 itens prontos e gravou somente o manifesto de dry-run. Isso é intencional.

## 9. Credenciais e configuração local

Arquivos distribuídos:

- `configuracao.exemplo.json`: configuração segura, com escrita desligada;
- `CREDENCIAIS-NAO-VAO-AQUI.txt`: lembrete permanente;
- `executor\executor_local.py`: backend local;
- `executor\vendor`: dependências já testadas;
- `requirements.txt`: alternativa para reinstalação.

Variáveis aceitas:

- `CLUBEF_SUPABASE_DB_URL`: connection string PostgreSQL;
- `CLUBEF_ENABLE_REAL_WRITE`: selo adicional para uma autorização futura;
- `CLUBEF_EXTRACTOR_PORT`: porta local opcional; padrão 8765.

Não use `service_role` no navegador. Chaves secretas e `service_role` ignoram RLS e devem permanecer somente em backend seguro, conforme [Understanding API keys](https://supabase.com/docs/guides/getting-started/api-keys).

A configuração segura distribuída aponta preventivamente para `clube_novo.carta_jogo`, mas mantém `write_enabled=false`. Não existe `configuracao.local.json` na instalação. O schema `clube` não deve ser configurado como destino de testes; ele permanece referência e recuperação.

## 10. Como validar cada execução

Antes de considerar um diff pronto para revisão, confirme:

1. o CPK exibido é o arquivo da atualização desejada;
2. o hash da fonte está no manifesto;
3. schema atual e anterior têm as mesmas 29 colunas;
4. `card_ids` únicos = total atual;
5. duplicadas = zero;
6. novas + alteradas + inalteradas = total atual;
7. possíveis inativas foram revisadas separadamente;
8. alterações mostram campos e valores `antes`/`depois`;
9. catálogos sem fingerprint anterior não aparecem falsamente como alterados;
10. o preflight informa `transaction_read_only=true` antes da confirmação final;
11. o resumo da aplicação é igual ao conjunto selecionado;
12. o manifesto de dry-run ou aplicação foi guardado.

Para o teste de recarga completa desta entrega, confira também o arquivo `FINGERPRINTS.sha256` da pasta de gabarito. A igualdade precisa ser dupla: zero diferenças lógicas por `card_id` e campos, e o mesmo SHA-256 do CSV integral.

## 11. Gabarito do banco

O banco é usado como gabarito de leitura, não como fonte que substitui os arquivos do jogo.

Nesta validação:

- `clube.carta_jogo`: 42.803 cartas e 42.803 `card_id` únicos;
- amostra determinística: 54 cartas, cobrindo dois exemplos por combinação de tipo e posição disponível;
- resultado: 54/54 iguais em todos os campos comparados;
- consulta: transação PostgreSQL confirmada como somente leitura.

As diferenças do patch não foram mascaradas pelo banco: 269 cartas novas e 34 cartas alteradas apareceram no manifesto.

A carga integral independente usada como gabarito contém 43.072 cartas e 43.072 IDs únicos. Seu conjunto de IDs é exatamente a união comprovada da carga anterior de 42.803 com os 269 lançamentos, e 54/54 cartas da amostra do banco coincidiram em todos os campos.

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
3. Abra `VERSOES-ANTERIORES\2026-08-26\Extrator-ClubEfootball.html` para consulta ou copie-o para outro nome.
4. Compare o SHA-256 com o manifesto da entrega antes de restaurar.

## 14. Limites conhecidos

- 19 cartas continuam sem nacionalidade; eram as mesmas 19 na base anterior, portanto não são regressão do novo extrator.
- O catálogo físico de técnicos tem 1.478 registros, mas `clube.tecnico_jogo` não oferecia gabarito carregado; o modo informa `sem_gabarito`.
- Habilidades, ímpetos e playstyles têm presença comparável, mas a fotografia anterior do banco não contém o registro físico bruto. Nesta primeira execução, conteúdo interno sem fingerprint anterior não é chamado de alteração.
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
7. Habilitar as duas travas externas apenas durante essa tarefa.
8. Aplicar o conjunto aprovado e salvar o manifesto de aplicação/readback.
9. Exportar nova fotografia completa e torná-la a próxima base somente depois do readback.
10. Atualizar catálogos em lote separado.
11. Nesta entrega, `clube` e `clube_novo` continuam intactos; um teste futuro do botão de subida deve ter nova autorização explícita e alvo limitado a `clube_novo.carta_jogo`.
12. Só depois tratar relações normalizadas, catálogos, motores ou tela, cada um em sua própria etapa.

## 16. Organização permanente

```text
7-VARREDURA-DO-JOGO\
├── Extrator-ClubEfootball.html
├── INICIAR-EXTRATOR.cmd
├── INICIAR-EXTRATOR.ps1
├── app\
├── executor\
├── DOCUMENTACAO\
│   └── MANUAL-DO-EXTRATOR.md
├── VERSOES-ANTERIORES\2026-08-26\
└── ENTREGAS\2026-08-27\
    ├── FONTES-E-BASE\
    ├── DIFF-CARTAS\
    ├── DIFF-METADADOS\
    ├── VALIDACAO-E-TESTES\
    ├── GABARITO-TESTE\CPK-2026-08-27\
    ├── PLANO-BANCO\
    └── RECUPERACAO\
```

Essa árvore permite encontrar a versão operacional, a anterior, as fontes, a prova, os manifestos e o procedimento de recuperação sem depender de diretórios temporários.
