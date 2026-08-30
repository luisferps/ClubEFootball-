# Manual do Extrator de Fotos dos Cards

## Onde fica a ferramenta

A pasta oficial é `Extrator de Fotos`, diretamente na raiz do repositório Main. Todos os arquivos do aplicativo, o iniciador, o manual, os exemplos, os testes, os logs e os resultados pertencem somente a essa pasta.

## Para que serve

Esta ferramenta busca a foto de uma carta no eFootballHub, publica a imagem no Cloudinary e grava a URL no próprio cadastro da carta em `clube_novo.carta_jogo.foto_url_cloudinary`.

Ela baixa e envia somente as fotos ausentes. Se a foto do mesmo `card_id` já estiver no Cloudinary, a ferramenta não a substitui; apenas confere e grava a URL no cadastro da carta.

A única chave usada do começo ao fim é o `card_id`. O nome do jogador, a aparência da foto, o tamanho da imagem e o hash não são usados para decidir a identidade da carta.

## O que ela faz automaticamente

Para cada `card_id`, a ferramenta:

1. confirma que a carta existe em `clube_novo.carta_jogo`;
2. procura no Cloudinary uma imagem cujo Public ID é exatamente o mesmo `card_id`;
3. se a imagem já existe, não envia outra e não sobrescreve nada;
4. se não existe, baixa `https://efimg.com/efootballhub22/images/player_cards/{card_id}_l.png`;
5. publica uma única imagem com Public ID igual ao `card_id`;
6. lê a imagem de volta no Cloudinary;
7. grava `https://res.cloudinary.com/demsusjwf/image/upload/{card_id}.png` na coluna `foto_url_cloudinary` da mesma carta;
8. lê o registro do banco de volta e salva o resultado no log.

## Onde buscar os IDs

Use um arquivo CSV, JSON, JSONL ou TXT que contenha `card_id`. No CSV, a coluna deve se chamar `card_id` ou `id`. Em TXT, coloque um ID numérico por linha.

Não use nome de jogador. Se dois registros têm nomes parecidos, isso não importa: somente o `card_id` identifica a carta.

A pasta `exemplos` contém `cards-exemplo.txt` para uma prova pequena.

## Preparar a autenticação sem expor segredo

Abra no navegador:

- Cloudinary → Settings → API Keys;
- Supabase → Project Settings → API Keys.

No Cloudinary, copie a linha completa chamada **API Environment variable**, no formato `cloudinary://...`. No Supabase, copie a chave `service_role`. Não cole esses valores em conversa, README, arquivo TXT, print ou log.

Ao iniciar a ferramenta, ela pedirá somente esses dois valores, ambos em campos ocultos. Eles ficam somente na memória daquela execução e são removidos do processo ao terminar. Esta ferramenta não oferece upload unsigned e não grava credenciais em arquivo.

## Como executar

1. No outro computador, baixe o ZIP do repositório no GitHub e extraia a pasta.
2. Dê dois cliques em `INICIAR-EXTRATOR-DE-FOTOS.cmd`.
3. Na primeira utilização, o iniciador baixa automaticamente o Node.js oficial portátil e confere o SHA-256 antes de executar.
4. Cole a **API Environment variable** do Cloudinary e a chave `service_role` do Supabase quando solicitado. Os valores não aparecerão na tela.
5. Aguarde a mensagem de conclusão. O iniciador usa automaticamente `exemplos\cards-exemplo.txt` e processa somente o primeiro `card_id` como amostra idempotente.

Durante um lote, mantenha o computador ligado, conectado à internet e com a janela do extrator aberta. O trabalho para se o computador desligar ou entrar em suspensão. Se isso acontecer, ligue novamente e siga a seção **Como retomar depois de falha**.

O duplo clique sempre executa primeiro a amostra segura de uma carta. Uma carga maior só deve ser iniciada depois de essa prova passar e continua limitada a no máximo 100 cartas por execução.

## Como evita duplicação

Antes de baixar, a ferramenta consulta a URL pública determinada pelo `card_id`. Resposta HTTP 200 significa que a imagem já existe: o upload é pulado e somente o vínculo no banco é conferido. Resposta HTTP 404 permite um novo upload.

O envio usa `overwrite=false`. Portanto, mesmo se duas execuções tentarem o mesmo `card_id`, a ferramenta não tem autorização para substituir o asset existente.

## Como a URL fica no cadastro da carta

O banco não usa tabela paralela. A URL fica na própria linha de `clube_novo.carta_jogo`, coluna `foto_url_cloudinary`.

Uma constraint do banco exige que a URL seja exatamente:

`https://res.cloudinary.com/demsusjwf/image/upload/{card_id}.png`

Assim, a aplicação futura resolve `card_id → foto` sem nome, comparação visual ou inferência.

## Onde consultar resultado e log

Cada execução cria uma pasta em `output\runs\DATA-DA-EXECUCAO\` com:

- `events.jsonl`: uma linha por carta, com sucesso, existência anterior ou erro;
- `summary.json`: contagens finais da execução;
- `images\`: somente imagens novas baixadas naquela execução.

Credenciais nunca aparecem nesses arquivos.

## Como retomar depois de falha

Execute novamente o mesmo arquivo de IDs e o mesmo limite. A retomada é idempotente:

- imagem já existente no Cloudinary é pulada;
- URL já correta no banco é gravada novamente com o mesmo valor, sem duplicar;
- se o upload terminou mas a gravação no banco falhou, a nova execução encontra a imagem existente e tenta somente concluir o vínculo;
- erros técnicos permanecem no `events.jsonl` para conferência.

Não apague os logs antes de confirmar o `summary.json`. Se houver falha de autenticação, não troque de fonte nem use preset público: confirme as credenciais locais e rode novamente.

## Exemplo pequeno

O arquivo `exemplos\cards-exemplo.txt` contém dois IDs. O iniciador por duplo clique testa automaticamente apenas o primeiro. Se a foto já estiver no Cloudinary, o resultado esperado é `existing_synced`; se for nova, o resultado esperado é `uploaded`. Nos dois casos, a URL final deve aparecer em `clube_novo.carta_jogo.foto_url_cloudinary` para o mesmo `card_id`.

## Distribuição pelo GitHub

Não é necessário instalar Git nem configurar o GitHub no computador de uso. Baixe o ZIP, extraia a pasta e use o iniciador.

O pacote inclui `.gitignore` rigoroso para bloquear `.env`, credenciais locais, chaves, runtime, imagens e logs. O arquivo `.env.example` contém somente nomes e valores públicos de exemplo; o uso normal não lê esse arquivo. Nunca renomeie um `.env` real para incluí-lo no repositório.
