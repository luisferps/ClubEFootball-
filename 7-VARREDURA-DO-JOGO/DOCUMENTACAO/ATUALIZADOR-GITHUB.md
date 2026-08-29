# Atualizador do GitHub — comportamento operacional

**Atualizado em:** 29/08/2026 04:09 (São Paulo)

O arquivo `4-BAIXAR-DO-GITHUB.bat` é o atualizador oficial da pasta V4.

Regras atuais:

- a janela do atualizador não fecha automaticamente ao terminar;
- em sucesso ou erro, a janela permanece aberta até o usuário fechá-la manualmente;
- o resultado completo também é gravado em `_ULTIMO-BAIXAR-DO-GITHUB.txt`, na raiz da pasta V4;
- o atualizador sincroniza `origin/main`, confere o commit local e remoto e recompila o `Extrator eFootball.exe` a partir do código V4.6 atual;
- `config.txt` continua preservado e não é enviado ao GitHub;
- o primeiro uso em uma pasta baixada por **Download ZIP** é suportado explicitamente: como a pasta não possui `.git`, o atualizador inicializa o repositório, busca `origin/main`, adota o índice do commit remoto com `git reset --mixed FETCH_HEAD` e materializa os arquivos rastreados com `git checkout-index -a -f`;
- esse bootstrap evita o erro em que `git checkout -B main FETCH_HEAD` recusava sobrescrever os arquivos do ZIP, que ainda apareciam ao Git como arquivos não rastreados;
- uma tentativa anterior interrompida também é reconhecida: se `.git` existir, mas ainda não houver `HEAD`, o atualizador retoma o mesmo bootstrap em vez de tratar a pasta como um repositório normal;
- após o primeiro bootstrap concluído, as execuções seguintes usam o fluxo normal de sincronização do branch `main`.

Essa regra existe para que uma pasta baixada inteira do GitHub possa virar uma cópia de trabalho atualizável pelo botão 4 sem o usuário precisar clonar manualmente o repositório e sem perder `config.txt`.
