# Manual do Extrator de Fotos — operação por batch

## Estrutura definitiva

Existem exatamente duas pastas:

- `8 - EXTRATOR DE FOTOS`: operação diária pelo batch novo.
- `8 - EXTRATOR DE FOTOS - LEGADO`: implementação anterior completa, interface HTML, testes, documentos, `output` e histórico existentes antes da separação.

Não misture os arquivos das duas pastas e não execute os dois fluxos ao mesmo tempo.

## As duas máquinas

- **Máquina 1 — `vaio`** (`C:\Users\Luis Fernando\Downloads\ClubEFootball--main\ClubEFootball--main\8 - EXTRATOR DE FOTOS`): máquina de trabalho.
- **Máquina 2** (`C:\Users\luis-\Downloads\ClubEFootball--main\8 - EXTRATOR DE FOTOS`): dedicada a rodar motores e extratores. **É nela que o extrator de fotos roda.**

As pastas são espelho, mas **correção feita numa não chega na outra sozinha**. Para propagar, copie o arquivo inteiro (Ctrl+C / Ctrl+V) — isso preserva a codificação UTF-8 com BOM e os acentos. Colar texto no GitHub web não preserva. Alternativa: `3-ATUALIZAR-O-GITHUB.bat` na origem + `4-BAIXAR-DO-GITHUB.bat` no destino.

O cofre de credenciais é DPAPI **por conta do Windows** — cada máquina precisa da própria configuração (opção 6).

## Os dois pontos de entrada

### `VIGIA-EXTRATOR-DE-FOTOS.cmd` — o jeito normal de rodar

É o que se usa para tocar a fila. Duplo clique e deixe a janela aberta. A cada **60 segundos** ele:

1. Reinicia o worker se ele tiver caído (e não faz nada se estiver rodando).
2. Reimprime o painel de status na tela, limpando a anterior.

Ou seja: **a tela se atualiza sozinha** e você não precisa ficar digitando `2`. Quando a fila acabar, ele mostra `FILA CONCLUÍDA` e para.

- **Fechar a janela do vigia não para o worker** — o worker roda por fora, em segundo plano. Fechar o vigia só desliga a vigilância e a atualização da tela.
- Para parar de verdade, use a opção `5` do menu manual e espere.
- **Antes de substituir qualquer arquivo da ferramenta, feche a janela do vigia.**

O vigia funciona porque `controle-operacional.ps1` aceita `-Acao Iniciar -Automatico`, que pula a confirmação `S/N`. Fora do vigia, esse parâmetro não é usado.

### `INICIAR-EXTRATOR-DE-FOTOS.cmd` — o menu manual

Para configurar credenciais, pausar, parar ou conferir na mão. É o mesmo controle de sempre.

No Windows, um arquivo `.cmd` é um batch. O nome antigo foi preservado para não criar dois botões concorrentes.

**Não rode os dois ao mesmo tempo** dando `1` no menu enquanto o vigia está aberto — não quebra nada (o segundo é recusado), mas confunde a leitura.

## Menu

- `1 - INICIAR/RETOMAR`: mostra o escopo, exige confirmação `S/N` e inicia o worker em segundo plano.
- `2 - STATUS`: lê somente processo e arquivos locais.
- `3 - PAUSAR`: solicita pausa no próximo ponto seguro.
- `4 - CONTINUAR`: libera uma execução pausada.
- `5 - PARAR`: solicita parada cooperativa, sem matar o processo.
- `6 - CONFIGURAR/ATUALIZAR`: salva as três credenciais no cofre DPAPI desta conta do Windows.
- `7 - VERIFICAR`: confere os arquivos e mostra o status, sem consultar Supabase ou Cloudinary.
- `0 - SAIR`: fecha apenas o menu.

O menu permanece aberto após cada ação até o operador pressionar ENTER. Depois que a opção 1 confirma que o worker está ativo, a janela pode ser fechada sem encerrar o processamento em segundo plano.

## Primeira utilização em cada computador

1. Abra o batch.
2. Leia `Credenciais locais` no topo.
3. Se aparecer `NÃO CONFIGURADAS`, escolha a opção 6.
4. Cole Cloudinary API Key, Cloudinary API Secret e Supabase Database URL completa.
5. Para rede IPv4 comum, use a URL do Supabase `Session pooler`, porta `5432`. A porta `6543` (Transaction pooler) é recusada.
6. Volte ao menu e escolha a opção 1.

As credenciais não aparecem no console. Elas são criptografadas com Windows DPAPI CurrentUser, não entram nos logs e são ignoradas pelo Git.

Na primeira execução da máquina, a dependência `pg` é instalada pelo `npm ci` (precisa de internet) e o Node é preparado. Pode levar um minuto — não é travamento.

## O que a opção 1 faz

1. Confere se não existe outro worker ativo.
2. Recusa o início se detectar o Extrator LEGADO ainda ativo.
3. Confere o cofre local sem mostrar as credenciais.
4. Exibe o que será feito e solicita `S/N`.
5. Prepara Node e a dependência fixada no `package-lock.json`, se necessário.
6. Inicia `photo-batch-worker.mjs` oculto e aguarda até 10 segundos pelo estado inicial.
7. Mostra imediatamente uma destas respostas:
   - worker ativo e consultando a fila;
   - falha ao iniciar, com motivo e caminho do log;
   - processo ativo, mas estado ainda indisponível, com o caminho esperado.

Se a consulta encontrar zero cartas elegíveis, o estado termina como `completed`, mostra a mensagem de fila concluída e registra `final_missing: 0`.

## A ORDEM DA FILA — prioridade por overall

⚠️ **Mudou em 04/09/2026.** Antes a descoberta ordenava por `card_id`, que é o número do registro — ordem arbitrária em termos de importância, com carta base e colecionável embaralhadas.

A fila agora sai ordenada assim (`card-image-extractor.mjs`, na consulta da descoberta):

```sql
ORDER BY roda_motor DESC NULLS LAST, overall DESC NULLS LAST, card_id
```

- **`roda_motor DESC`** — as cartas que o motor roda vêm primeiro. Sem isso, carta base de OVR 92 passa na frente de colecionável de 88.
- **`overall DESC`** — é a mesma regra que o otimizador usa: `otimizador_lote_producao_candidata_v5` ordena `ordem_candidata` por `overall_snapshot` decrescente (correlação medida: −0,97).
- **`card_id`** — desempate, mantém a fila determinística e reproduzível.

A ordem é recalculada a cada descoberta. Como a descoberta só busca quem está `NULL`, retomar nunca repete trabalho: o que já ganhou link sai da fila sozinho.

**Prova medida (04/09/2026):** depois de 5 lotes com a fila priorizada, as 500 fotos que entraram eram **todas** de cartas com `roda_motor = true` e `overall >= 90`. Nenhuma carta base furou a fila.

## Caminho de processamento

1. Consulta `clube_novo.carta_jogo` por registros com `foto_url_cloudinary IS NULL`, na ordem de prioridade acima.
2. Persiste uma fotografia da fila, com SHA-256.
3. Processa lotes de até 100, concorrência 4 e intervalo mínimo de 500 ms.
4. Para cada `card_id`, verifica primeiro o Cloudinary.
5. Se já existe, não sobrescreve.
6. Se não existe, busca `<card_id>_l.png` no EFHub e envia com `overwrite=false`.
7. Cria um manifesto durável com identidade, origem, URL candidata, verificações e resultado.
8. Só executa APPLY quando o manifesto do lote estiver integral.
9. Atualiza somente a mesma linha de `card_id` e somente quando o campo ainda estiver `NULL`.
10. Preserva conflitos e relê o banco independentemente.
11. Só fecha o lote como seguro com `conditional_null_only=true`, `conflicts=0` e `independently_read_back=true`.
12. Ao final, consulta novamente o banco e só conclui normalmente com zero pendências elegíveis.

## Quanto tempo leva

Depende do que o lote encontra no Cloudinary:

| situação do lote | ritmo medido |
|---|---|
| imagens **precisam subir** (`cloudinary_uploaded`) | **~6 min 20 s** por lote de 100 |
| imagens **já estão** no Cloudinary (`cloudinary_existing`) | **menos de 1 minuto** por lote — só liga o link |

Em 05/09, com a fila só de cartas `base` (quase todas já no Cloudinary), foram **~5.000 cards em poucos minutos**.

O gargalo é o upload das imagens, **não** o banco nem a ordenação — ordenar 30 mil cartas leva segundos.

Com a fila priorizada, não é preciso esperar o fim: as cartas boas saem primeiro e as `base` terminam por último.

## Pausa, continuação e parada

Os pedidos são cooperativos e verificados entre etapas seguras.

- Durante uma etapa interna, o pedido pode aguardar a etapa terminar.
- Se um manifesto já estiver pronto, a parada ocorre antes do APPLY; o manifesto fica preservado e aquele lote não altera o banco.
- Continuar remove a pausa e usa o mesmo cursor.
- Iniciar após parada ou falha consulta novamente os registros atualmente `NULL`; lotes já aplicados não voltam à fila.
- Imagens já enviadas são reconhecidas no Cloudinary e não são sobrescritas.

**Antes de substituir qualquer arquivo da ferramenta, pare com a opção 5 e espere.**

## Estado e logs

- Estado atual: `output\operador\estado.json`
- Execuções: `output\operador\runs\<data-hora>`
- Log: `output\operador\runs\<data-hora>\execucao.log`
- Eventos: `output\operador\runs\<data-hora>\eventos.jsonl`
- Resumo: `output\operador\runs\<data-hora>\resumo.json`
- Descobertas: `output\discoveries`
- Preparação e manifestos: `output\runs`
- APPLY e releitura: `output\applies`

Se a opção 1 parecer não fazer nada, volte ao menu, escolha 2 e leia `Execução`, `Fase`, `Erro`, `Mensagem` e `Log`.

## Como conferir por fora (auditoria independente)

Não confie só no que a tela informa. No Supabase, esta consulta é o placar real:

```sql
select
  count(*) filter (where foto_url_cloudinary is not null) com_foto,
  count(*) filter (where foto_url_cloudinary is null) sem_foto,
  count(*) filter (where foto_url_cloudinary is null and roda_motor and overall >= 90) falta_top90,
  count(*) filter (where foto_url_cloudinary is null and roda_motor) falta_motor
from clube_novo.carta_jogo;
```

`com_foto` tem que subir de 100 em 100 a cada lote fechado, e `falta_top90` tem que cair junto enquanto a prioridade estiver no topo da fila.

## Problemas já resolvidos — não voltar a caçar

### A opção 1 imprimia o escopo e parecia travar (04/09/2026)

A tela parava logo depois de `- reler o banco após cada APPLY.` com o cursor piscando. **Não estava travado.** A confirmação era feita por `choice.exe`, que escreve o prompt **sem quebra de linha**; o PowerShell só entrega a saída de programa externo quando a linha fecha, então a pergunta ficava presa no buffer e nunca aparecia. O `chcp 65001` do `.cmd` agrava isso.

Corrigido: `Confirmar-Inicio`, em `controle-operacional.ps1`, usa `Read-Host` nativo. **Não voltar a usar `choice.exe` neste projeto.**

### Caminho do Node cravado na mão (04/09/2026)

`bootstrap-node.ps1` tinha `C:\Users\Luis Fernando\.cache\codex-runtimes\...` fixo, então o atalho nunca valia na máquina 2. Passou a usar `$env:USERPROFILE`.

## Carta sem imagem na fonte (efHub 404)

Nem todo card tem foto no efHub. Quando a fonte responde **HTTP 404**, isso **não é erro** — é ausência de dado, e o extrator trata assim desde 05/09/2026:

- o card sai como `fonte_sem_imagem`, **não** conta como falha e não derruba o lote;
- ele **não entra no manifesto**, então o APPLY nem olha para ele;
- fica registrado no log da preparação, com o `card_id`, e a contagem aparece no STATUS como **`Sem imagem na fonte (efHub 404)`**;
- se um lote inteiro for só de cards assim, o manifesto ficaria vazio: o lote é marcado `batch_sem_imagem_na_fonte`, **nada é aplicado**, o banco não é tocado e a fila avança.

⚠️ Esses cards continuam com `foto_url_cloudinary` NULL e voltam à fila em toda descoberta. É esperado: se um dia o efHub publicar a imagem, o extrator pega. Para saber quais são, procure `fonte_sem_imagem` no `execucao.log`.

**Por que isso foi preciso:** em 05/09 o lote 1 tinha 99 cards prontos e **1** com 404 (`card_id 169387`). A regra antiga jogava fora o lote inteiro por causa desse um — e, como a fila é determinística, ele caía sempre no lote 1. O extrator ficou travado do mesmo jeito por horas.

**O que continua igual:** nunca sobrescrever link existente, gravar só onde é NULL, reler o banco depois de cada APPLY, e parar de verdade em erro de rede, de Cloudinary ou de banco.

## O banco lento derruba o extrator (e não é culpa dele)

Em 05/09 o extrator ficou horas parado em `discovering` com `Fila 0 de 0`. **Não era o extrator.** O **bonificador** estava rodando no mesmo Supabase e saturou o banco: um `COUNT` simples levava mais de 1 minuto, e no pico nem um `select 1` conseguia conectar.

Como reconhecer:

- fase presa em `discovering` por muitos minutos;
- `pg_stat_activity` mostrando a consulta de contagem do extrator ativa há mais de 1 min, e algo esperando `DataFileRead`;
- consultas simples estourando o tempo limite.

O que fazer: **parar quem está pesando** (bonificador, outro motor) e esperar. Se sobrarem conexões penduradas de um processo que morreu, reiniciar o projeto no Supabase (Settings → General → **Restart project**) zera as conexões sem perder dado.

**Regra prática: não rode o bonificador e o extrator ao mesmo tempo.**

## Falha conhecida em aberto

### `A etapa prepare terminou sem resumo válido (código 3221226505)`

`3221226505` é `0xC0000409` — o processo Node morreu de forma abrupta, **sem escrever nada no stderr**. Não é erro de banco, de rede nem de credencial. Se fosse estouro de memória do V8, o log traria `FATAL ERROR: heap out of memory` — não traz. Causas prováveis, ainda não separadas: antivírus derrubando o processo, falha em biblioteca nativa, ou uma imagem que quebra o download.

**Não há dano.** O crash ocorre entre lotes; nenhum APPLY fica pela metade e o que já foi gravado está conferido no banco.

**Como isso é contornado hoje:** o `VIGIA-EXTRATOR-DE-FOTOS.cmd` reinicia sozinho em até 60 segundos. Ele nasceu exatamente por causa desta falha — antes dele, o worker caiu e ficou **2 horas parado** sem ninguém perceber. Enquanto a causa raiz não for resolvida, **rode sempre pelo vigia**.

O que fazer se quiser investigar:

1. Opção `1` → `S`. A descoberta é refeita, o que já tem link sai da fila e ele continua do ponto certo.
2. Se voltar a cair **perto do mesmo ponto da fila**, é dado de alguma carta — abrir o `execucao.log` da execução e ver o último `card_id` processado.
3. Se cair em pontos diferentes, é ambiente da máquina (antivírus / memória).

Ocorrências em 04/09/2026: lote 4 da primeira execução e lote 6 da segunda — **pontos diferentes da fila, cards diferentes**, o que descarta dado ruim e aponta para ambiente da máquina 2.

**Teste que ainda não foi feito:** excluir a pasta `8 - EXTRATOR DE FOTOS` do Windows Defender na máquina 2 e ver se as quedas somem.

## Segurança

- Nenhuma credencial é colocada em navegador ou argumento de processo.
- `output` e o cofre DPAPI não são publicados pelo Git.
- O worker usa conexão PostgreSQL local, preferencialmente Session pooler 5432 em IPv4.
- Nenhum valor existente em `foto_url_cloudinary` é sobrescrito.
- **Esquema ativo é só o `clube_novo`.** Nada fora dele é fonte da verdade nem destino de escrita.

Referência oficial do Supabase:

https://supabase.com/docs/guides/database/connecting-to-postgres
# Atualização operacional de 12/09/2026: fontes sem imagem

Uma execução consulta cada carta no máximo uma vez. Depois de percorrer a
fotografia, relê o banco: cartas novas ainda não tentadas podem ser incluídas;
as mesmas cartas que continuam sem foto não voltam ao ciclo automaticamente.

Se restarem apenas cartas já tentadas, o estado é `waiting_sources`
(aguardando fonte), com a quantidade ainda sem foto e o log das ausências.
Isso não significa fila zerada nem conclusão de todas as fotos. Uma nova
execução permite consultar novamente, pois a imagem pode aparecer depois.

Código: `photo-batch-worker.mjs` confere hash, IDs e contagem da fotografia
e preserva a lista de tentativas da execução. Tela: o controle operacional
apresenta o estado aguardando fonte. Banco: permanece a escrita condicional
somente de URL vazia, com leitura independente e prioridade manual; não
se grava URL fictícia nem se marca carta como fotografada para removê-la da fila.

Validação local: redescoberta de 404 com chegada de carta nova, nova execução
permitida, adulteração, duplicatas e contagem inválida. Dois testes passaram;
sintaxe PowerShell conferida. O lote real depende da incorporação das cartas
novas pelo Extrator físico e ainda não foi executado nesta etapa.
