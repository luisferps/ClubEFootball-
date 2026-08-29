# Atualizador do GitHub — comportamento operacional

**Atualizado em:** 29/08/2026 04:20 (São Paulo)

O arquivo `4-BAIXAR-DO-GITHUB.bat` é o atualizador oficial da pasta V4.

Regras atuais:

- a janela do atualizador não fecha automaticamente ao terminar;
- em sucesso ou erro, a janela permanece aberta até o usuário fechá-la manualmente;
- o resultado também é gravado em `_ULTIMO-BAIXAR-DO-GITHUB.txt`, na raiz da pasta V4;
- o atualizador sincroniza `origin/main`, confere o commit local e remoto e recompila o `Extrator eFootball.exe` com o código atual e o ícone oficial;
- `config.txt` continua preservado e não é enviado ao GitHub;
- o primeiro uso em pasta baixada por **Download ZIP** é suportado: o atualizador inicializa `.git`, busca `origin/main`, adota o índice remoto com `git reset --mixed FETCH_HEAD` e materializa os arquivos rastreados;
- uma tentativa de bootstrap interrompida é retomada quando `.git` existe mas ainda não existe `HEAD`;
- em uma cópia de trabalho já inicializada, a sincronização usa `git reset --hard FETCH_HEAD` antes da recompilação. Isso é intencional porque o `Extrator eFootball.exe` local pode estar diferente após a compilação anterior; o código é primeiro alinhado ao GitHub e o executável é recompilado imediatamente em seguida;
- a versão atual recompilada pelo botão 4 é a V4.6.2 do launcher, que procura automaticamente as fontes físicas nas pastas do eFootball antes de iniciar o servidor.

O objetivo é que tanto uma pasta clonada quanto uma pasta originalmente baixada como ZIP possam ser atualizadas pelo mesmo botão sem perder `config.txt`, sem fechamento automático da janela e sem executar silenciosamente um launcher antigo.
