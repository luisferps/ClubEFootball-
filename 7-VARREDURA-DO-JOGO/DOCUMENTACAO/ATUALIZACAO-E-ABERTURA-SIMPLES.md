# Atualização e abertura simples do Extrator

**Data:** 29 de agosto de 2026

## Regra operacional

Depois de uma atualização de código, compile uma vez o EXE desktop. O uso diário seguinte não exige nova compilação.

### Atualizar a pasta

Execute, na pasta principal:

```text
4-BAIXAR-DO-GITHUB.bat
```

O botão deve somente:

1. baixar o estado atual de `main`;
2. avançar somente quando os arquivos locais não conflitam com `main`;
3. preservar `config.txt`, `2-MOTORES\config.txt` e `configuracao.local.json` sem copiá-los ou regravá-los;
4. registrar o commit instalado;
5. terminar sem compilar e sem abrir o Extrator.

Ele não deve listar centenas de arquivos em paginador, não deve iniciar o motor, não deve executar o compilador do EXE e não deve usar `git reset --hard`.

### Abrir o Extrator

Execute:

```text
7-VARREDURA-DO-JOGO\ABRIR-EXTRATOR.cmd
```

O fluxo normal abre o EXE desktop V5. Ele cria uma janela WinForms e inicia a leitura pesada em worker separado; não abre Microsoft Edge, Chrome, `localhost` ou a página HTML.

Quando o código for atualizado, execute uma vez `COMPILAR-EXTRATOR-V46.cmd`. O compilador gera o EXE V5; `ABRIR-EXTRATOR.cmd` recusa abrir um EXE web V4 anterior.

## Segurança

- `config.txt` não é substituído pela atualização;
- abrir o Extrator não grava automaticamente no banco;
- leitura, comparação, conferência e aplicação continuam separadas;
- nenhuma rotina de Otimizador ou Bonificador é executada por esses botões.
