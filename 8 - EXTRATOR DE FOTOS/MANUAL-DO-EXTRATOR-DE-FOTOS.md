# Manual do Extrator de Fotos — operação por batch

## Estrutura definitiva

Existem exatamente duas pastas:

- `8 - EXTRATOR DE FOTOS`: operação diária pelo batch novo.
- `8 - EXTRATOR DE FOTOS - LEGADO`: implementação anterior completa, interface HTML, testes, documentos, `output` e histórico existentes antes da separação.

Não misture os arquivos das duas pastas e não execute os dois fluxos ao mesmo tempo.

## Único ponto de entrada operacional

Na pasta `8 - EXTRATOR DE FOTOS`, dê dois cliques em:

`INICIAR-EXTRATOR-DE-FOTOS.cmd`

No Windows, um arquivo `.cmd` é um batch. O nome antigo foi preservado para não criar dois botões concorrentes.

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
5. Para rede IPv4 comum, use a URL do Supabase `Session pooler`, porta `5432`.
6. Volte ao menu e escolha a opção 1.

As credenciais não aparecem no console. Elas são criptografadas com Windows DPAPI CurrentUser, não entram nos logs e são ignoradas pelo Git.

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

## Caminho de processamento

1. Consulta `clube_novo.carta_jogo` por registros com `foto_url_cloudinary IS NULL`.
2. Persiste uma fotografia da fila.
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

## Pausa, continuação e parada

Os pedidos são cooperativos e verificados entre etapas seguras.

- Durante uma etapa interna, o pedido pode aguardar a etapa terminar.
- Se um manifesto já estiver pronto, a parada ocorre antes do APPLY; o manifesto fica preservado e aquele lote não altera o banco.
- Continuar remove a pausa e usa o mesmo cursor.
- Iniciar após parada ou falha consulta novamente os registros atualmente `NULL`; lotes já aplicados não voltam à fila.
- Imagens já enviadas são reconhecidas no Cloudinary e não são sobrescritas.

## Estado e logs

- Estado atual: `output\operador\estado.json`
- Execuções: `output\operador\runs\<data-hora>`
- Log: `output\operador\runs\<data-hora>\execucao.log`
- Eventos: `output\operador\runs\<data-hora>\eventos.jsonl`
- Resumo: `output\operador\runs\<data-hora>\resumo.json`
- Descobertas: `output\discoveries`
- Preparação e manifestos: `output\runs`
- APPLY e releitura: `output\applies`

Se a opção 1 parecer não fazer nada, volte ao menu, escolha 2 e leia `Execução`, `Fase`, `Erro`, `Mensagem` e `Log`. O batch não deve mais fechar silenciosamente.

## Segurança

- Nenhuma credencial é colocada em navegador ou argumento de processo.
- `output` e o cofre DPAPI não são publicados pelo Git.
- O worker usa conexão PostgreSQL local, preferencialmente Session pooler 5432 em IPv4.
- Nenhum valor existente em `foto_url_cloudinary` é sobrescrito.

Referência oficial do Supabase:

https://supabase.com/docs/guides/database/connecting-to-postgres
