# Extrator de fotos de cards eFootballHub → Cloudinary

O extrator usa exclusivamente `card_id` numérico como identidade. Ele nunca associa uma imagem pelo nome do jogador.

Contrato:

- fonte: `https://efimg.com/efootballhub22/images/player_cards/{card_id}_l.png`;
- Public ID no Cloudinary: `{card_id}`;
- pasta dinâmica: `clubefutebol/cards/efootballhub`;
- URL pública recuperável: `https://res.cloudinary.com/demsusjwf/image/upload/{card_id}.png`;
- vínculo canônico: `clube_novo.carta_jogo.foto_url_cloudinary`, na própria linha do `card_id`;
- tags: `efootballhub` e `card_id_{card_id}`;
- contexto: `card_id`, `source` e `source_url`;
- upload preset: `clubefutebol_cards_no_overwrite`;
- sobrescrita: proibida. O inventário HEAD ocorre antes do download e uploads unsigned também recusam colisões.

## Uso seguro

Use o Node empacotado no Codex ou Node 20+.

Para uso sem programação, baixe o ZIP do GitHub, extraia a pasta e dê dois cliques em `INICIAR-EXTRATOR-DE-FOTOS.cmd`. O iniciador prepara um Node.js portátil verificado e pede somente a API Environment variable do Cloudinary e a `service_role` do Supabase, ambas em campos ocultos. O passo a passo completo está em `MANUAL-DO-EXTRATOR-DE-FOTOS.md`.

Inventário sem gravar:

```powershell
node card-image-extractor.mjs --input "C:\Users\Luis Fernando\Downloads\cards_efhub_COMPLETO.csv" --limit 10
```

Uma amostra explícita com upload:

```powershell
node card-image-extractor.mjs --card-id 17592722922839 --limit 1 --apply
```

O preset atual do projeto é assinado. Para automação de backend, defina `CLOUDINARY_API_KEY` e `CLOUDINARY_API_SECRET` no ambiente; os valores nunca são gravados nos logs. O extrator usa autenticação HTTP Basic e envia `overwrite=false`. Não existe rota de upload unsigned nesta ferramenta.

Toda execução com `--apply` também exige `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` no ambiente local. Antes de publicar, o extrator confirma que o `card_id` existe em `clube_novo.carta_jogo`. Após o readback do Cloudinary, grava a URL na coluna `foto_url_cloudinary` e confere a mesma linha. Nenhuma credencial aparece no ledger.

`--limit` é obrigatório e aceita no máximo 100 cards por execução. Sem `--apply`, nenhuma imagem é baixada nem enviada. Cada execução grava `output/runs/<data>/events.jsonl`, `summary.json` e, somente para novos uploads, a imagem recebida.

Entradas aceitas: CSV com coluna `card_id` ou `id`, JSON, JSONL e TXT com um ID por linha. Duplicatas são removidas pela string exata de `card_id` antes de qualquer chamada.

## Verificação

```powershell
npm test
```

O ledger registra o status anterior no Cloudinary, resposta de upload, readback público e readback do banco. SHA-256, MIME e dimensões são somente auditoria técnica: não bloqueiam a publicação. A identidade é decidida exclusivamente pela igualdade do `card_id`. Um evento `uploaded` só é produzido quando o pré-check foi 404, o readback do Cloudinary foi 200 e `clube_novo.carta_jogo.foto_url_cloudinary` retornou a URL esperada.

## Inventário sem rede

O inventário cruza um universo de `card_id` com um ou mais ledgers já lidos do Cloudinary, sem consultar imagem por imagem:

```powershell
node inventory-card-images.mjs `
  --universe "C:\caminho\cards.csv" `
  --registered-manifest "C:\caminho\ledger-1.jsonl" `
  --registered-manifest "C:\caminho\ledger-2.jsonl" `
  --output ".\output\inventory"
```

São produzidas listas separadas de registrados, ausentes e IDs registrados fora do universo escolhido, além de um resumo com hashes SHA-256 e conferência da partição.

