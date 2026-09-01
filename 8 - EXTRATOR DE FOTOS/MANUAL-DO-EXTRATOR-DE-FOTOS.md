# Manual do Extrator de Fotos

Atualizado em 31/08/2026 para a interface local de execução direta, Session pooler, retomada segura, diagnóstico por logs e operação em computador dedicado.

## O que o aplicativo faz

Depois de um único clique em **INICIAR**, o Extrator:

1. consulta `clube_novo.carta_jogo` no Supabase;
2. cria sozinho a fila das cartas cujo `foto_url_cloudinary` está NULL;
3. verifica se a imagem do mesmo `card_id` já existe no Cloudinary;
4. busca no EFHub somente as imagens que ainda não existem no Cloudinary;
5. publica a imagem sem permitir overwrite;
6. cria um manifesto local durável para o lote;
7. grava o link no registro do mesmo `card_id`, somente se o campo continua NULL;
8. relê o banco por uma conexão independente;
9. só depois começa o próximo lote de até 100 cartas.

O operador não informa `card_id`, não escolhe arquivo e não precisa apertar um botão para cada lote. A preparação do manifesto e o APPLY continuam sendo fases técnicas separadas, mas o clique em **INICIAR** autoriza a sequência completa na interface simplificada.

## As três credenciais

A tela pede somente:

1. **Cloudinary API Key**;
2. **Cloudinary API Secret**;
3. **Supabase Database URL**.

O terceiro campo não recebe Secret Key, `service_role` nem chave `anon` do Supabase. Ele recebe a conexão PostgreSQL completa, parecida com:

```text
postgresql://postgres:[SUA-SENHA]@db.SEUPROJETO.supabase.co:5432/postgres
```

Para obtê-la no computador que executará o Extrator:

1. abra o projeto no Supabase;
2. clique em **Connect**;
3. escolha **Session pooler** quando o computador estiver em uma rede IPv4 comum;
4. copie a connection string;
5. confirme que a porta é `5432`;
6. se a URL contiver `[YOUR-PASSWORD]`, substitua somente esse trecho pela senha atual do banco. Se o painel já entregar a URL preenchida, não acrescente outro texto.

A conexão **Direct connection** usa `db.<project-ref>.supabase.co:5432` e normalmente exige IPv6. A conexão **Session pooler** usa `aws-<região>.pooler.supabase.com:5432` e é a opção adequada para este aplicativo persistente quando a rede é somente IPv4. Não use o Transaction pooler da porta `6543` para esta execução longa.

Se a senha contiver `@`, `:`, `/`, `#`, `%` ou outro caractere reservado de URL, ela precisa estar percent-encoded dentro da connection string. Quando a senha foi esquecida, use **Reset database password** no painel e monte novamente a URL com a nova senha. O reset não atualiza automaticamente o cofre do Extrator: preencha novamente os três campos em cada computador que executa o aplicativo.

O nome técnico `direct_postgres_transaction` nos logs significa que o Extrator está usando o driver PostgreSQL e uma transação direta com o banco. Ele também aparece quando o endereço de rede escolhido é o Session pooler; não significa que o host IPv6 da opção **Direct connection** foi usado.

## Como iniciar

1. Dê dois cliques em `INICIAR-EXTRATOR-DE-FOTOS.cmd`.
2. Na primeira utilização, aguarde a instalação automática das dependências verificadas. A mensagem `added 14 packages` é normal.
3. Aguarde a janela preta informar o endereço local `http://127.0.0.1:PORTA`.
4. Aguarde o navegador abrir a tela **Extrator de Fotos**.
5. Na primeira utilização desse computador, cole as três credenciais.
6. Clique uma vez em **INICIAR**.
7. Não clique novamente enquanto aparecer execução em andamento.

Depois que a descoberta do Supabase for aceita, os campos mostram **Salva nesta máquina**. Nas próximas aberturas, basta clicar em **INICIAR**. Se a descoberta falhar antes de validar a coluna, as credenciais novas não são salvas e os três campos precisam ser preenchidos de novo. Se os três campos forem preenchidos novamente, o cofre anterior só é substituído depois de a nova conexão ser aceita.

Se a janela preta mostrar acentos como `dependÃªncias` ou `utilizaÃ§Ã£o`, isso é somente uma diferença de codificação visual do console do Windows. Não altera chaves, URLs, imagens ou banco e não representa falha de execução.

## Quais janelas precisam ficar abertas

- A janela preta do iniciador deve permanecer aberta até a conclusão. Pode ser minimizada, mas não deve ser fechada.
- A aba do navegador também pode ser minimizada. É recomendável mantê-la aberta para conservar e exibir o acompanhamento ao vivo.
- Atualizar a página com F5 não interrompe o processamento; a tela volta a ler o estado do servidor local.
- Apagar a tela ou bloquear o Windows com `Win+L`, por si só, não encerra o Extrator.
- Suspensão, hibernação, reinício, fechamento da janela preta, encerramento do processo ou perda de internet interrompem a execução.
- Em uma máquina dedicada, mantenha-a ligada à tomada e configure o Windows para não suspender enquanto estiver conectada à energia. Não é necessário impedir apenas o desligamento da tela.

Depois de aparecer **Concluído**, a aba e a janela preta podem ser fechadas.

## Como interpretar a tela

- **Consultando o Supabase**: está criando uma fotografia ordenada das cartas atualmente sem link. Em universos grandes e usando Session pooler, essa etapa pode levar alguns minutos; a versão atual permite até 5 minutos.
- **Buscando e enviando fotos**: está verificando Cloudinary e, quando necessário, EFHub.
- **Gravando e conferindo o lote**: o manifesto está sendo validado, aplicado e relido.
- **Lote conferido**: aquele lote já fechou com segurança e o próximo pode começar.
- **Concluído**: todo o universo descoberto no início dessa execução terminou.
- Mensagem vermelha: a execução parou; nenhum lote seguinte é iniciado automaticamente.

O total mostrado é a fotografia inicial das linhas NULL. O contador só considera um lote fechado depois do APPLY e da leitura independente.

## Como a identidade da foto é garantida

O vínculo não é feito pelo nome do jogador. A única chave de identidade é o `card_id` numérico:

```text
Supabase card_id X
→ EFHub .../X_l.png
→ Cloudinary .../X.png
→ Supabase carta_jogo.card_id = X
```

Para cada item, o manifesto exige que `card_id`, URL do EFHub, Public ID do Cloudinary, URL candidata e linha do Supabase contenham o mesmo código. Qualquer divergência invalida o item antes da gravação.

## Cloudinary primeiro, EFHub depois

Em cada lote, todas as verificações do Cloudinary terminam antes da primeira chamada ao EFHub:

- HTTP 200 no Cloudinary: usa o asset existente e não faz download nem upload;
- HTTP 404 no Cloudinary: busca `https://efimg.com/efootballhub22/images/player_cards/{card_id}_l.png`;
- upload: usa Public ID `{card_id}` e `overwrite=false`;
- depois do upload: aguarda e repete o readback até a URL responder HTTP 200;
- erro permanente, rate limit esgotado ou imagem inválida: o lote falha fechado.

O processamento usa concorrência máxima 4, intervalo mínimo de 500 ms entre inícios, timeout e retries com backoff. Um asset existente nunca é substituído.

## Gravação no Supabase

Cada manifesto de até 100 itens é aplicado em uma transação PostgreSQL. O único destino permitido é:

```text
clube_novo.carta_jogo.foto_url_cloudinary
```

O update é parametrizado pelo mesmo `card_id` e inclui `foto_url_cloudinary IS NULL`:

- se continua NULL, recebe a URL validada;
- se outra execução preencheu o campo, o valor existente é preservado como conflito;
- se ocorrer erro, a transação inteira do manifesto sofre rollback;
- depois do commit, uma nova conexão relê todos os itens e compara as URLs.

Para considerar um APPLY seguro, o `summary.json` correspondente precisa mostrar:

```text
conditional_null_only: true
conflicts_preserved: true
independently_read_back: true
counts.conflict_preserved: ausente ou 0
```

Quando não existe conflito, o campo `counts.conflict_preserved` pode não ser gravado no JSON; a ausência desse contador equivale a zero. Se ele aparecer com valor maior que zero, nenhum valor existente foi sobrescrito, mas o lote precisa ser registrado e conferido como lote com conflito preservado, não como lote de conflito zero.

O fluxo operacional usa conexão PostgreSQL no servidor local, que é um processo confiável e não o código do navegador. Não é necessário expor `clube_novo` na Data API, conceder acesso a `anon`/`authenticated` nem colocar Secret Key do Supabase no navegador. A mudança do Supabase que exige opt-in explícito para novas tabelas na Data API não afeta este acesso PostgreSQL direto.

A descoberta inicial é somente leitura e possui `statement_timeout` de até 5 minutos porque precisa contar e ordenar dezenas de milhares de cartas. O APPLY continua com limite independente de 30 segundos por transação de lote; aumentar o tempo da descoberta não afrouxa a proteção das gravações.

## Credenciais e segurança local

- A interface é servida somente em `127.0.0.1`, em porta temporária.
- O HTML/JavaScript não contém Cloudinary Secret, senha do banco ou chave privilegiada.
- Os campos são `password` e são limpos depois que a execução é aceita.
- O navegador envia as credenciais somente ao servidor loopback autenticado da própria sessão.
- O servidor passa as credenciais ao processo de trabalho em memória.
- Para lembrar os valores, o Windows grava apenas um cofre DPAPI `CurrentUser` em `output\state\credentials.windows-dpapi.json`.
- Esse cofre não revela texto aberto, não entra no Git e não funciona em outra conta ou computador.

Nunca cole as credenciais em conversa, commit, manifesto, log ou captura pública.

## Onde ficam os registros

- descoberta do universo: `output\discoveries\<run_id>\`;
- manifesto, eventos e imagens baixadas do lote: `output\runs\<run_id>\`;
- APPLY e readback: `output\applies\<run_id>\`;
- cofre e checkpoints: `output\state\`.

Arquivos principais:

- `card-ids-sem-link.txt`: fotografia ordenada da fila descoberta;
- `manifest.json`: identidade, candidato, proveniência, verificações, resultado e falha/skip de cada carta;
- `events.jsonl`: eventos detalhados, um JSON por linha;
- `summary.json`: resultado fechado da descoberta, lote ou APPLY;
- `images\{card_id}.png`: cópia local somente quando houve download do EFHub.

O manifesto recebe SHA-256 canônico. Se for alterado depois de criado, o APPLY é recusado.

Para uma falha ocorrida ainda em **Consultando o Supabase**, abra primeiro:

```text
output\discoveries\<pasta-mais-recente>\summary.json
output\discoveries\<pasta-mais-recente>\events.jsonl
```

Para uma falha durante download/upload, use a pasta mais recente de `output\runs`. Para uma falha durante gravação ou readback do banco, use a pasta mais recente de `output\applies`. O `summary.json` mostra o resultado geral; o `events.jsonl` contém a causa exata. Não envie arquivos de credenciais nem URLs que contenham senha.

## Se ocorrer uma falha

1. Não fique clicando repetidamente em **INICIAR**.
2. Leia a mensagem vermelha.
3. Confira o `summary.json` e o fim de `events.jsonl` nas pastas mais recentes.
4. Considere seguros somente os lotes que já têm APPLY com `independently_read_back: true`.
5. Corrija a causa e inicie novamente.

Na retomada, o aplicativo consulta o Supabase de novo e começa pelo primeiro `card_id` que ainda está NULL. Cartas já gravadas deixam a fila. Se uma imagem chegou ao Cloudinary, mas o banco não foi atualizado antes da interrupção, a nova execução detecta o asset existente e reaplica apenas o link. Por isso não há overwrite nem dependência de um contador antigo.

Um lote pode terminar, por exemplo, com 99 uploads confirmados e uma falha de readback Cloudinary. Nesse caso:

- o manifesto do lote é preservado com a falha explícita;
- o APPLY daquele lote não começa e o banco não recebe uma atualização parcial;
- as 99 imagens que já chegaram ao Cloudinary permanecem válidas;
- na próxima execução, os HEADs do Cloudinary encontram essas imagens e evitam novo upload;
- a fila é reconstruída pelo estado atual do Supabase, e não pelo número exibido antes da interrupção.

Erros comuns:

- **Password authentication failed**: a senha na Database URL está errada ou desatualizada;
- **connection refused/timeout**: confirme internet, firewall e o tipo de conexão; em rede IPv4, tente Session pooler;
- **canceling statement due to statement timeout** com `column_verified: false`, `selected: 0` e `database_modified: false`: a conexão funcionou, mas a consulta inicial ultrapassou o limite de 30 segundos da versão antiga. Atualize o aplicativo; a descoberta agora possui até 5 minutos, sem alterar o limite curto e seguro do APPLY;
- **Cloudinary HTTP 401**: API Key ou API Secret incorretos;
- **Cloudinary/EFHub 429 ou falha temporária**: o programa tenta novamente; se esgotar, o lote para com log;
- **Operação terminou com falha**: abra o resumo e o log mais recentes para encontrar a causa específica.

## Levar para outro computador

### Na máquina de origem

1. Feche o Extrator e outros programas que possam estar gravando arquivos dentro do projeto.
2. Na raiz de `ClubEFootball--main`, abra somente `3-ATUALIZAR-O-GITHUB.bat`. Esse é o botão central de publicação de todo o projeto; a cópia existente na pasta `GitHub` apenas chama esse mesmo botão.
3. Confira o resumo de arquivos novos, alterados e excluídos. Não confirme exclusões que você não reconhece.
4. Para autorizar o conjunto inteiro, pressione **S** quando aparecer `Confirmação [S/N]`. Não é necessário copiar texto nem pressionar Enter. Se houver exclusões, o botão apresenta uma segunda confirmação **S/N** separada.
5. Antes de executar `git add`, criar commit ou enviar qualquer coisa, o botão cria e compara um backup físico completo, inclusive com `.git`, em:

```text
C:\Users\Luis Fernando\Downloads\ClubEFootball--main\_BACKUPS-ANTES-GITHUB\ClubEFootball--main-AAAAMMDD-HHMMSS
```

6. Aguarde a mensagem **SUBIU E FOI CONFERIDO NO GITHUB**. Ela só aparece depois de o botão reler a branch remota e confirmar o mesmo commit.
7. Conserve o backup físico pelo menos até a nova máquina iniciar o Extrator corretamente. Os backups não são apagados automaticamente.

### Na máquina dedicada

1. Baixe o ZIP do repositório ou faça um clone limpo do GitHub depois da confirmação acima.
2. Não copie a pasta `output` nem o cofre DPAPI da máquina antiga. Eles não são necessários para retomar e o cofre não funciona em outro computador.
3. Execute `8 - EXTRATOR DE FOTOS\INICIAR-EXTRATOR-DE-FOTOS.cmd`.
4. Cole novamente Cloudinary API Key, Cloudinary API Secret e Supabase Database URL.
5. Clique uma vez em **INICIAR** e mantenha a janela preta aberta e o computador sem suspensão.
6. Use a máquina dedicada somente para executar o Extrator. Continue fazendo as futuras publicações do GitHub pela máquina principal, evitando dois clones com alterações diferentes.

O cofre DPAPI do computador anterior não deve ser copiado e não funcionará no novo computador. Os links já gravados no Supabase e os assets já existentes no Cloudinary serão detectados; portanto, a nova máquina continua somente o que ainda falta.

### Atualizar um clone que já existe na máquina dedicada

1. Na máquina principal, publique primeiro pelo botão 3 e aguarde **SUBIU E FOI CONFERIDO NO GITHUB**.
2. Na máquina dedicada, espere a execução atual terminar ou falhar e feche a aba do Extrator e a janela preta.
3. Confirme que esse clone dedicado não possui alterações de código que precisem ser publicadas. A pasta `output`, os logs e o cofre DPAPI são locais e não contam como alteração de código.
4. Na raiz do clone dedicado, execute `4-BAIXAR-DO-GITHUB.bat`.
5. O botão 4 usa avanço `fast-forward` e para diante de conflito local; ele não executa reset forçado. Não use o botão 4 em uma máquina que possua alterações de código ainda não publicadas.
6. Depois da confirmação da atualização, abra novamente `8 - EXTRATOR DE FOTOS\INICIAR-EXTRATOR-DE-FOTOS.cmd`.
7. O cofre DPAPI e os registros de `output` permanecem nessa máquina. Se a senha do banco tiver sido resetada, preencha os três campos novamente; caso contrário, clique em **INICIAR** usando as credenciais lembradas.

Uma atualização do código não apaga o progresso real: a autoridade de retomada é o estado atual do Supabase e os assets existentes no Cloudinary. Ao reiniciar, a fila é reconstruída somente com os registros que continuam NULL.

## Referências oficiais do Supabase

Orientações verificadas novamente em 31/08/2026. O changelog não apresentou mudança posterior que altere o uso deste aplicativo: Session pooler permanece na porta 5432 para clientes persistentes em IPv4, enquanto a porta 6543 permanece no modo Transaction pooler.

- [Conectar ao banco Postgres](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Proteger os dados e as conexões diretas](https://supabase.com/docs/guides/database/secure-data)
- [Usar schemas personalizados na Data API](https://supabase.com/docs/guides/api/using-custom-schemas)
- [Segurança da Data API](https://supabase.com/docs/guides/api/securing-your-api)
- [Tipos e segurança das API keys](https://supabase.com/docs/guides/getting-started/api-keys)
- [Mudança: novas tabelas não são expostas automaticamente na Data API](https://supabase.com/changelog/45329-breaking-change-tables-not-exposed-to-data-and-graphql-api-automatically)
- [Changelog do Supabase](https://supabase.com/changelog)
