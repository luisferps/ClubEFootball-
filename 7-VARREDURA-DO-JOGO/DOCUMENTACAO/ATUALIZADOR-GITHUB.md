# Atualizador do GitHub — comportamento operacional

**Atualizado em:** 29/08/2026 03:46 (São Paulo)

O arquivo `4-BAIXAR-DO-GITHUB.bat` é o atualizador oficial da pasta V4.

Regras atuais:

- a janela do atualizador não fecha automaticamente ao terminar;
- em sucesso ou erro, a janela permanece aberta até o usuário fechá-la manualmente;
- o resultado completo também é gravado em `_ULTIMO-BAIXAR-DO-GITHUB.txt`, na raiz da pasta V4;
- o atualizador sincroniza `origin/main`, confere o commit local e remoto e recompila o `Extrator eFootball.exe` a partir do código V4.6 atual;
- um executável antigo não pode sobreviver silenciosamente a uma falha de compilação;
- `config.txt` continua preservado e não é enviado ao GitHub.

Essa regra existe para que erros de download, Git ou recompilação permaneçam visíveis e possam ser diagnosticados sem depender do tempo em que a janela do CMD fica aberta.
