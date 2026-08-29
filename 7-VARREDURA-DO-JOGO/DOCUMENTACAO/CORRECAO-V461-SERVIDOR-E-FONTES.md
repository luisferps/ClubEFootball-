# Correção V4.6.1 — servidor local e descoberta de fontes

**Data:** 29/08/2026 — São Paulo

Esta correção registra um defeito operacional identificado no aplicativo Windows do Extrator.

## Defeito

O executável verificava se já havia um servidor respondendo em `127.0.0.1:8765`. Se um processo Python de uma execução anterior continuasse vivo em segundo plano, o aplicativo aceitava esse servidor antigo e abria a interface sobre código obsoleto. Por isso alterações corretas em `executor/servidor_v46.py` podiam estar no disco e ainda assim a tela continuar exibindo as quatro fontes como `NÃO ENCONTRADO`.

## Correção

A versão Windows foi elevada para **4.6.1** e passa a usar a porta local `8766`. O launcher e `INICIAR-EXTRATOR-V46.cmd` usam a mesma porta, evitando reutilizar o servidor antigo que permaneceu na `8765`.

A descoberta automática continua pertencendo ao Extrator e usa os caminhos físicos confirmados:

- DT870 da atualização: `C:\ProgramData\KONAMI\eFootball\ST\Download\dt870_console_win.cpk`, com busca recursiva na pasta `Download` se necessário;
- DT200 base: `C:\Program Files (x86)\Steam\steamapps\common\eFootball\cpk\dt200_console_all.cpk`;
- DT870 original: `C:\Program Files (x86)\Steam\steamapps\common\eFootball\cpk\dt870_console_win.cpk`;
- textos em português: `C:\Program Files (x86)\Steam\steamapps\common\eFootball\cpk\dt261_bra_console_win.cpk`; o `all.str` fica dentro desse CPK.

A seleção manual continua apenas como recuperação caso a fonte realmente não exista nos caminhos conhecidos.

## Regra preservada

A localização física do CPK não define endereço semântico de dado. A tabela/catálogo canônico do `clube_novo` continua dizendo onde está cada informação dentro da fonte. O Extrator apenas localiza a fonte física, valida o contrato, lê e devolve.

## Arquivos alterados

- `windows-app/ClubEfootballExtractorLauncher.cs`
- `INICIAR-EXTRATOR-V46.cmd`
- documentação desta correção

Nenhum arquivo de dados foi excluído nesta correção.
