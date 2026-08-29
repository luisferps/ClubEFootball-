# Atualizador do GitHub

`4-BAIXAR-DO-GITHUB.bat` só sincroniza arquivos de `origin/main` e registra o commit instalado em `_ULTIMO-BAIXAR-DO-GITHUB.txt`.

- não compila nem abre o Extrator;
- não usa `git reset --hard`;
- atualiza uma cópia existente somente com `git merge --ff-only`;
- em conflito local, para sem sobrescrever arquivos;
- para antes de sincronizar se o remoto tentar versionar `config.txt`, `2-MOTORES\config.txt` ou `7-VARREDURA-DO-JOGO\configuracao.local.json`;
- para também se alguma dessas configurações ainda estiver rastreada no índice local.

Em uma pasta original baixada como ZIP, o botão inicializa o repositório e materializa o primeiro commit remoto somente depois dessas mesmas proteções. O usuário decide quando compilar o EXE desktop com `COMPILAR-EXTRATOR-V46.cmd`.
