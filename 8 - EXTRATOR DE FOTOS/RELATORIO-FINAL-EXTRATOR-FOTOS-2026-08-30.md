# Relatório final — Extrator de Fotos — 30/08/2026

## Resultado

A ferramenta local foi implementada no diretório operacional real. O universo agora é descoberto diretamente em `clube_novo.carta_jogo`: a aplicação confirma a coluna `foto_url_cloudinary`, seleciona somente valores NULL e não pede arquivo de IDs ao operador. Em cada amostra/lote, todos os links Cloudinary são verificados antes da primeira chamada ao EFHub. O fluxo de preparação e o fluxo de escrita continuam fisicamente separados por manifesto SHA-256.

Durante o desenvolvimento não houve upload real nem modificação de banco.

## Arquivos principais alterados/criados

- `card-image-extractor.mjs`: descoberta automática dos NULLs, confirmação de coluna, preparação em duas passagens Cloudinary→EFHub, manifestos, rate limit, retries, concorrência, APPLY separado, Postgres transacional e Data API fallback;
- `photo-manifest.mjs`: contrato, SHA-256 canônico, validação fail-closed, elegibilidade, conflito e readback independente;
- `interface-local-server.mjs`: servidor loopback, sessão local, descoberta/snapshots/checkpoint, rotas separadas e credenciais efêmeras recebidas da interface;
- `interface-local.html`, `interface-local.js`, `interface-local.css`: fluxo visual Supabase → Cloudinary/EFHub → APPLY MANIFEST;
- `abrir-interface.ps1`: prepara dependências e abre diretamente a tela onde o operador cola as chaves;
- `bootstrap-node.ps1`: Node portátil com npm verificado;
- `package.json`, `package-lock.json`: `pg` 8.16.3 fixado e lock com integridade;
- `executar-extrator.ps1`: CLI de upload gera manifesto sem banco;
- `test/card-image-extractor.test.mjs`: mocks, dry-run, servidor loopback, manifesto e APPLY validado;
- `README.md`, `MANUAL-DO-EXTRATOR-DE-FOTOS.md`, `.env.example`: operação e bloqueios atualizados.

## Testes executados

Comando:

`node --test`

Resultado: 17 testes, 17 aprovados, 0 falhas.

Cobertura material:

- servidor somente `127.0.0.1` e token de sessão;
- quatro campos password ligados ao servidor local, sem valor embutido, persistência ou log;
- parsing/deduplicação de `card_id`;
- descoberta Data API mockada: coluna confirmada, contagens e snapshot somente dos NULLs, usando apenas GET;
- prova de ordenação: todos os HEADs Cloudinary do lote ocorreram antes da primeira busca no EFHub;
- pool de 100 itens com pico de concorrência 4;
- dry-run com 3 cards: somente HEAD Cloudinary, manifesto persistido, zero upload e zero banco;
- upload completo mockado: HEAD 404, download PNG, POST Cloudinary, readback 200, manifesto elegível e zero banco;
- manifesto adulterado recusado por SHA-256;
- APPLY mockado: update condicional, decisão por card e readback independente;
- parse de todos os scripts PowerShell e `node --check` dos módulos JavaScript.

## Fluxo exato do operador

1. Abrir `INICIAR-EXTRATOR-DE-FOTOS.cmd`.
2. Colar Cloudinary API Key/Secret nos campos password da tela local.
3. Colar `SUPABASE_DB_URL` ou a chave secreta de servidor e clicar em **Consultar campo e cards sem link**.
4. Confirmar na tela a coluna, os já vinculados e a fila automática dos NULLs.
5. Executar a amostra de 1 card; Cloudinary é consultado antes de eventual EFHub.
6. Revisar o resultado; o banco continua inalterado.
7. Confirmar explicitamente cada lote de até 100 descobertos no banco.
8. Revisar `manifest.json`, `events.jsonl` e `summary.json`.
9. Usar o último manifesto ou selecionar outro, marcar a confirmação e clicar em **APPLY MANIFEST**.
10. Revisar `output/applies/<run_id>/events.jsonl` e `summary.json` para update, conflito, skip e readback.

## Método de acesso escolhido

O modo `auto` prefere `SUPABASE_DB_URL`:

- conexão Postgres direta somente no processo local;
- uma transação cobre todo o manifesto;
- update parametrizado apenas quando `foto_url_cloudinary IS NULL`;
- rollback em erro;
- conflitos preservados;
- nova conexão para readback independente depois do commit.

Sem DB URL, existe fallback por Data API com Supabase Secret Key (ou `service_role` legado) somente no servidor local. Ele usa `Accept-Profile/Content-Profile: clube_novo`, PATCH condicionado a NULL e GET separado de readback. O fallback é atômico por card, não pelo lote inteiro.

## Orientação oficial verificada

- Supabase recomenda que chaves secretas permaneçam em backend: https://supabase.com/docs/guides/getting-started/api-keys. Nesta ferramenta local, o valor é colado conscientemente pelo operador e encaminhado imediatamente ao backend loopback, sem ser embutido ou persistido.
- clientes Postgres de servidor devem usar connection string; conexão direta é indicada para sessão única/backend persistente e SSL deve ser usado: https://supabase.com/docs/guides/database/connecting-to-postgres
- schemas customizados precisam ser adicionados explicitamente a Exposed schemas e receber grants para as roles que realmente os usam: https://supabase.com/docs/guides/api/using-custom-schemas
- grants e RLS são camadas diferentes; não foi concedido acesso a `anon`/`authenticated`: https://supabase.com/docs/guides/api/securing-your-api
- o changelog de 28/04/2026 confirma a mudança para exposição opt-in de tabelas/Data API: https://supabase.com/changelog/45329-breaking-change-tables-not-exposed-to-data-and-graphql-api-automatically

## Acesso real e bloqueios externos restantes

Não havia `SUPABASE_DB_URL`, Supabase Secret Key ou `service_role` disponível no processo desta validação; portanto não foi aberta nova conexão real.

A evidência somente leitura já existente `EVIDENCIA-HTTP406-E-LOTE-2026-08-30.json` registra:

- 43.072 linhas e 43.072 `card_id` distintos em `clube_novo.carta_jogo`;
- 6 URLs preenchidas;
- `service_role` com USAGE no schema, mas sem SELECT/UPDATE na tabela;
- Data API com HTTP 406/PGRST106 porque `clube_novo` não está exposto;
- zero alteração aplicada.

Para operação real ainda é necessário um destes gates externos:

1. colar uma `SUPABASE_DB_URL` válida na interface; ou
2. expor `clube_novo` somente para a Data API necessária e conceder à role secreta de servidor USAGE/SELECT/UPDATE mínimos em `carta_jogo` — sem grants a `anon`/`authenticated`.

Também continuam necessários os segredos Cloudinary para a primeira amostra real. Essa amostra e o primeiro lote real foram deliberadamente deixados para o operador, porque desenvolvimento/teste não autorizava upload real.
