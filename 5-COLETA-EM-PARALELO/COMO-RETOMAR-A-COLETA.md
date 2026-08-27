# COLETA EM PARALELO — como retomar AGORA (5 minutos)

**O que é:** o script de navegador que busca as **28.776 fichas que faltam** do
efHub (das 29.222 da Tarefa 7; 446 já foram coletadas). Ele roda no teu Chrome,
em paralelo com a obra — **não escreve no banco**: salva arquivos na pasta.
A entrada no banco acontece depois, pela porta da casa, na hora certa.

## Se for o MESMO Chrome de sempre (o checkpoint está vivo nele)

1. Abre 👉 https://efhub.com/pt-BR/players
2. Aperta **F12** → aba **Console**
3. Digita e dá Enter:
   ```js
   await ClubEFT7.retomar()
   ```
4. Se aparecer `ClubEFT7 is not defined`: abre o arquivo
   `COLETAR-CARDS-FALTANTES-EFHUB-CONSOLE.js` (desta pasta) no Bloco de Notas,
   **Ctrl+A, Ctrl+C**, cola no Console, Enter — e aí repete o passo 3.
   Na primeira vez ele pede pra escolher a pasta: aponta para
   `Downloads\coleta-efhub-dados-fotos` (a MESMA de sempre).

## O que esperar
- Ele anda **um lote por execução** (até 1.000 cartas), com pausas educadas —
  parou em HTTP 429 uma vez, e o ritmo dele já foi calibrado pra isso.
- Terminou um lote? Roda `await ClubEFT7.retomar()` de novo pro próximo.
  São 30 lotes ao todo. Pode fazer aos poucos, quando o computador estiver ligado.
- Pra ver onde está: `await ClubEFT7.status()`

## ⛔ AS DUAS PROIBIÇÕES (perder isto = perder a retomada)
1. **NÃO limpar dados de navegação** desse Chrome (o checkpoint vive dentro dele).
2. **NÃO apagar nem mover** `Downloads\coleta-efhub-dados-fotos`.

## E depois?
Quando os lotes forem fechando, me avisa — eu confiro os manifestos e preparo a
entrada na casa (com assinatura, pela camada de coleta). Nada entra sozinho.
