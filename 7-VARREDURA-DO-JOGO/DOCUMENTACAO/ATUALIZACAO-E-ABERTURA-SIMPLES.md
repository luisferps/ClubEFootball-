# Atualização e abertura simples do Extrator

**Data:** 29 de agosto de 2026

## Regra operacional

O uso normal do Extrator não exige compilação.

### Atualizar a pasta

Execute, na pasta principal:

```text
4-BAIXAR-DO-GITHUB.bat
```

O botão deve somente:

1. baixar o estado atual de `main`;
2. substituir os arquivos versionados da pasta pelo conteúdo atual do GitHub;
3. preservar o `config.txt` local;
4. registrar o commit instalado;
5. terminar sem compilar e sem abrir o Extrator.

Ele não deve listar centenas de arquivos em paginador, não deve iniciar o motor e não deve executar o compilador do EXE.

### Abrir o Extrator

Execute:

```text
7-VARREDURA-DO-JOGO\ABRIR-EXTRATOR.cmd
```

O fluxo normal chama `INICIAR-EXTRATOR-V46.cmd`, que inicia diretamente o runtime Python `executor/servidor_v4612.py` e abre a interface no Microsoft Edge. Nenhuma compilação ocorre nessa abertura.

O arquivo `COMPILAR-EXTRATOR-V46.cmd` permanece apenas para manutenção opcional do EXE antigo e não faz parte do uso diário.

## Segurança

- `config.txt` não é substituído pela atualização;
- abrir o Extrator não grava automaticamente no banco;
- leitura, comparação, conferência e aplicação continuam separadas;
- nenhuma rotina de Otimizador ou Bonificador é executada por esses botões.
