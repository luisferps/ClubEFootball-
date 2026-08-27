# Coletor de dados e fotos dos cards faltantes do eFootballHub

Este pacote consulta somente os **29.222 `card_id` que ainda faltam**. Os **8.521 já completos** foram removidos da fila antes da execução. Cada chamada processa um lote com no máximo 1.000 cards.

## Como iniciar no Chrome

1. Abra `https://efhub.com/pt-BR/players` no Chrome normal, não em janela anônima.
2. Abra o Console do DevTools, copie todo o arquivo `COLETAR-CARDS-FALTANTES-EFHUB-CONSOLE.js`, cole e pressione Enter.
3. Confirme a mensagem `Coletor T7 V6 carregado`. Carregar o arquivo **não inicia rede**.
4. Execute somente `await ClubEFT7.iniciar()`.
5. Será aberto um seletor de **diretório**: dentro de Downloads, escolha a pasta comum **coleta-efhub-dados-fotos** já criada. Não escolha Downloads e não escolha arquivo.
6. O coletor grava diretamente nessa pasta e inicia o primeiro lote de dados.

Os 29.222 IDs estão embutidos. Não há seletor de arquivo. Antes da primeira chamada, o script confere SHA-256, IDs únicos e a partição `37.743 = 8.521 já completos + 29.222 faltantes`.

## Pasta obrigatória, sem arquivos soltos

O seletor aparece uma única vez em `iniciar()` e serve somente para escolher `Downloads/coleta-efhub-dados-fotos`. O Chrome pode bloquear Downloads por ser diretório do sistema, por isso Downloads não deve ser selecionada. Se a API estiver indisponível, a seleção for cancelada, outra pasta for escolhida ou a escrita não for autorizada, o coletor para **antes da rede**. Não existe fallback para arquivos soltos.

Com pasta autorizada, a organização é:

`coleta-efhub-dados-fotos/LOTE-.../dados/`

`coleta-efhub-dados-fotos/LOTE-.../imagens/`

Cada foto usa o próprio `card_id`, como `15452_l.png`, sempre dentro da subpasta exclusiva.

Cada exportação de lote contém:

- `01-expected.txt`
- `02-collected.txt`
- `03-failed.txt`
- `04-pending.txt`
- `05-dados-estruturados.jsonl`
- `06-manifesto-fotos.jsonl`
- `07-falhas.jsonl`
- `08-excluidos.jsonl`
- `09-checkpoint.json`
- `10-estado-final.json`

## Retomada

`await ClubEFT7.retomar()`

O V6 usa um banco/checkpoint novo: começa com 29.222 pendentes e não aproveita o avanço do V4/V5. Os arquivos e checkpoints antigos não são apagados e permanecem como evidência. `retomar()` conclui primeiro todos os lotes de dados; somente depois entra nos lotes de fotos. Um JSON já salvo nunca é consultado novamente por causa de foto pendente.

Antes da sequência há uma única sonda. HTTP 429 encerra o lote sem falhar o ID, respeita `Retry-After` e grava cooldown persistente. Chamar `retomar()` durante o cooldown não envia rede. Se a página for recarregada, cole o arquivo novamente e execute a mesma linha; não limpe os dados do site nem troque de perfil.

Outros comandos:

- Pausar depois da chamada atual: `ClubEFT7.pausar()`
- Ver o resumo: `await ClubEFT7.resumo()`
- Reexportar o lote 1: `await ClubEFT7.exportar(1)`
- Liberar explicitamente só falhas do lote 1: `await ClubEFT7.repetirFalhas(1)`

## Contrato e propriedade dos dados

A fonte de atributos é somente o JSON de `https://efhub.com/api/public/players/{card_id}`. O `payload.id` deve coincidir exatamente com o `card_id` pedido. Atributos, medidas, habilidades e metadados são validados antes de serem salvos.

O JSON exportado remove deliberadamente chaves `boost*`, `booster*`, `box*` e `pack*`. Ímpetos, boosters e boxes permanecem sob responsabilidade do eFootballDB e nunca são substituídos por este coletor.

A foto não fornece atributos. `payload.imageUrl` só é aceito quando coincide exatamente com `https://efimg.com/efootballhub22/images/player_cards/{card_id}_l.png`. A URL é registrada como `efhub_source_url`; `cloudinary_url` permanece nulo. A imagem é salva como `{card_id}_l.png`.

Se CORS impedir a leitura da imagem, ela permanece `photo_pending`; nenhum download direto ou arquivo solto é disparado. HTTP 429 na imagem preserva o JSON e usa um cooldown exclusivo de fotos, sem bloquear a fase de dados.

HTTP 2xx segue para parsing JSON antes de qualquer classificação terminal. 404/410 vira `inactive_excluded`; identidade ausente ou divergente vira `ambiguous_excluded`; incompatibilidade de schema vira `schema_pending` e interrompe o lote; 401/403 pausa; 429/rede/JSON transitório nunca viram falha terminal.

## Segurança validada

- Lotes de no máximo 1.000.
- Dados em série: mínimo de 5 segundos e jitter de até 1,5 segundo.
- Fotos em série: mínimo de 1,5 segundo e jitter de até 0,75 segundo.
- Pausa de 15 segundos depois de uma sonda bem-sucedida.
- Cooldown e checkpoint persistentes.
- SHA-256 do payload bruto, JSON sanitizado, imagens lidas como blob e manifestos.
- Zero escrita no Supabase; zero upload ao Cloudinary.

Foram executados 28 testes locais, usando 179 respostas estruturadas já salvas, os 36 registros reais do incidente e respostas 200/429 sintéticas. Nenhuma coleta real foi executada neste ambiente.
