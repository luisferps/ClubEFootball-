# Extrator de Fotos ClubEfootball

Ferramenta local e independente que descobre no Supabase os cards sem link, verifica primeiro as fotos que já existem no Cloudinary, busca no EFHub somente o que realmente falta, produz um manifesto durável e aplica as URLs em `clube_novo.carta_jogo.foto_url_cloudinary` depois do clique explícito em **INICIAR**.

## Contrato fechado

- identidade: somente `card_id` numérico;
- universo operacional: consulta somente leitura a `clube_novo.carta_jogo`, filtrada por `foto_url_cloudinary IS NULL`;
- fonte: `https://efimg.com/efootballhub22/images/player_cards/{card_id}_l.png`;
- candidato Cloudinary: `https://res.cloudinary.com/demsusjwf/image/upload/{card_id}.png`;
- Public ID: `{card_id}`;
- pasta do asset: `clubefutebol/cards/efootballhub`;
- ordem de rede: todos os HEADs Cloudinary do lote terminam antes da primeira busca no EFHub;
- upload: autenticado, `overwrite=false`, somente depois de HEAD 404 e antes de readback HTTP 200;
- banco: somente `clube_novo.carta_jogo.foto_url_cloudinary`, na linha do mesmo `card_id`, somente quando o valor atual é NULL;
- conflitos: preservados, nunca sobrescritos;
- confirmação: nenhum processamento ou APPLY começa sem o clique do operador em **INICIAR**;
- lotes internos: até 100 cartas; cada lote precisa ser aplicado e relido antes de o seguinte começar.

## Operação sem ChatGPT

Dê dois cliques em `INICIAR-EXTRATOR-DE-FOTOS.cmd`. O iniciador prepara Node/dependências verificadas e abre a interface em uma porta temporária de `127.0.0.1`. As chaves são coladas nos campos password da própria tela.

Nenhuma credencial é embutida no HTML/JavaScript nem gravada em URL, cookie, `localStorage`, manifesto ou log. O JavaScript envia os valores somente ao servidor loopback autenticado da mesma sessão; o servidor cria um cofre local criptografado pelo Windows DPAPI para o usuário atual, repassa os valores ao processo filho em memória e limpa os campos assim que aceita a execução. `output/` não entra no Git e o cofre não pode ser reutilizado em outra conta ou computador.

Na interface:

1. cole Cloudinary API Key, Cloudinary API Secret e `SUPABASE_DB_URL`;
2. clique em **INICIAR**;
3. o aplicativo confirma a coluna e cria sozinho um snapshot ordenado dos `card_id` com URL NULL;
4. ele processa lotes internos de até 100, verificando todo o Cloudinary antes de chamar o EFHub;
5. cada lote gera manifesto, é validado, aplicado somente sobre valores ainda NULL e relido de forma independente;
6. se um lote falhar, o fluxo para e preserva manifesto, eventos e resumo para diagnóstico.

A interface principal não pede arquivo de IDs. A descoberta persiste `output/discoveries/<run_id>/card-ids-sem-link.txt`, `events.jsonl` e `summary.json`; seu checkpoint é retomável pelo SHA-256 em `output/state/`. A CLI continua aceitando arquivo somente para diagnóstico isolado.

## Manifesto intermediário

Cada preparação persiste `output/runs/<run_id>/manifest.json`. Cada item contém:

- `card_id` e `candidate_url` determinística;
- proveniência física (`source_url`, Public ID, pasta e chave de identidade);
- pré-check/readback Cloudinary;
- `outcome` (`cloudinary_existing`, `cloudinary_uploaded`, `cloudinary_missing_dry_run` ou `failed`);
- `failure_or_skip_state` explícito;
- prova de que não houve tentativa de overwrite;
- recibo técnico do upload/arquivo quando aplicável.

O documento inteiro recebe SHA-256 canônico. O APPLY recalcula esse hash, rejeita duplicatas/caminhos divergentes, relê cada candidato no Cloudinary e ignora itens não elegíveis.

## Aplicação do manifesto e acesso Supabase

O fluxo da interface exige `SUPABASE_DB_URL` no servidor local. Ele usa uma transação para cada manifesto de até 100 itens, updates parametrizados com `foto_url_cloudinary IS NULL`, rollback em erro e uma nova conexão para readback independente depois do commit.

Na CLI, uma Secret Key (ou `service_role` legado) ainda pode usar a Data API no processo servidor. Esse método exige que `clube_novo` esteja exposto e que a role de servidor tenha `USAGE`, `SELECT` e `UPDATE`; ele não é oferecido nos três campos da interface operacional.

Não conceda acesso a `anon` ou `authenticated`. Não grave nem distribua a chave: cole-a somente nesta interface local, no computador do operador.

O estado externo conhecido em 30/08/2026 continua bloqueado: `clube_novo` retorna PGRST106 porque não está exposto na Data API, e o `service_role` disponível não tem o acesso necessário a `carta_jogo`. Isso não invalida os manifestos; apenas impede o APPLY por Data API até correção administrativa. A conexão Postgres direta requer a URL/senha obtida no botão **Connect** do projeto.

Orientação oficial consultada:

- https://supabase.com/docs/guides/getting-started/api-keys
- https://supabase.com/docs/guides/database/connecting-to-postgres
- https://supabase.com/docs/guides/api/using-custom-schemas
- https://supabase.com/docs/guides/api/securing-your-api

## CLI para diagnóstico

Descobrir automaticamente o universo sem link, sem modificar o banco:

```powershell
node card-image-extractor.mjs --discover-missing --database-method auto
```

Dry-run sem upload e sem banco:

```powershell
node card-image-extractor.mjs --input "C:\caminho\cards.csv" --limit 3
```

Preparar/uploadar sem tocar no banco:

```powershell
node card-image-extractor.mjs --input "C:\caminho\cards.csv" --offset 0 --limit 100 --concurrency 4 --delay-ms 500 --upload
```

APPLY separado:

```powershell
node card-image-extractor.mjs --apply-manifest "C:\caminho\manifest.json" --database-method auto
```

O argumento antigo `--apply` é recusado para impedir o acoplamento entre upload e banco.

## Testes

```powershell
npm test
```

Os testes usam apenas mocks e diretórios temporários. Não publicam imagem e não alteram banco real.
