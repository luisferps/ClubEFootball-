# COMO RODAR A RECOLETA TOTAL (V7) — sua parte, passo a passo

**O que este coletor faz:** recoleta TODOS os cards (38.494 na fila), com FOTO,
começando pelos mais fortes: os 2.785 que já temos, do OVR 102 para baixo → depois
os 29.222 que nunca tivemos → por último os 8.521 já completos (recoleta de conferência).
Intervalo de 3s por card (~1.200/hora). Ímpetos e boxes NÃO entram — já estão completos
do efootballdb.

**Onde o resultado fica:** **na pasta que você escolher** (não vai direto pro banco — de
propósito). Sugestão: `5-COLETA-EM-PARALELO\Resultado da Coleta`, dentro da pasta de
trabalho — mas pode ser qualquer uma. O progresso/checkpoint fica no Chrome
(IndexedDB `clubefootball-t7-recoleta-total-v7`).
Quando os lotes fecharem, eu subo para a caixa de entrada do banco (clube.recebimento),
confiro, e só então entra na casa. Coleta de dias não se perde por queda de internet.

⚠️ **Crie a pasta antes de começar** (botão direito → Nova pasta), porque o seletor do
Chrome não cria pasta nova.

## Os passos — agora é só colar

1. Abra o Chrome em: **https://efhub.com/pt-BR/players**
2. Aperte **F12** → aba **Console**
3. Abra `5-COLETA-EM-PARALELO\COLETOR-RECOLETA-TOTAL-V7.js` no Bloco de Notas,
   **Ctrl+A**, **Ctrl+C**
4. Clique no Console, **Ctrl+V**, **Enter**

**Acabou.** Ele começa sozinho — não precisa digitar mais nada.

- **Se a pasta já foi autorizada antes:** ele reconhece, avisa *"Pasta já autorizada.
  Retomando sozinho…"* e continua de onde parou.
- **Se for a primeira vez:** abre o seletor uma única vez. Escolha a pasta e clique em
  **Permitir** — daí em diante ele nunca mais pergunta.

⚠️ A primeira escolha de pasta é exigência do Chrome (nenhum site pode escrever no seu
computador sem você apontar onde). Só acontece uma vez.

## No dia a dia

- **Parou / fechou o Chrome / caiu a luz?** Reabra efhub.com/pt-BR/players, F12 e cole o
  script — ele retoma sozinho de onde parou.
- **Quer forçar na mão?** `await ClubEFT7.retomar()`
- **Ver o andamento:** `await ClubEFT7.status()`
- Se aparecer HTTP 429 ele pausa e volta sozinho (espera de 1 a 15 min). Não mexe.

## ⛔ NUNCA

- limpar dados de navegação do Chrome (apaga o checkpoint)
- apagar ou mover a pasta que você escolheu
- rodar em duas abas ao mesmo tempo
