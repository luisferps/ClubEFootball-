# Como usar o Extrator eFootball Desktop V5

1. Execute `4-BAIXAR-DO-GITHUB.bat` somente para sincronizar os arquivos. Ele não compila, não abre o Extrator e não toca em `config.txt` nem em `configuracao.local.json`.
2. Depois de uma atualização de código, execute uma vez `7-VARREDURA-DO-JOGO\COMPILAR-EXTRATOR-V46.cmd` para gerar o EXE desktop V5.
3. Abra `7-VARREDURA-DO-JOGO\ABRIR-EXTRATOR.cmd` e clique em **INICIAR VARREDURA**.
4. A janela permanece disponível enquanto o worker separado lê as fontes. Acompanhe Banco, Fontes, Progresso e o estado de cada família.
5. Use **VER DIVERGÊNCIAS** para abrir o resultado local da execução. Itens iguais, novos, alterados, ausentes, duplicados e erros permanecem separados por família.

Esta versão é exclusivamente de leitura e comparação:

`pedido canônico do banco -> leitura física -> comparação -> relatório local`

Não há botão, endpoint ou fluxo de aplicação na interface desktop. `database_write=false` acompanha o worker e seus resultados. Uma família com divergência ou erro é reportada e não cancela as famílias seguintes. Sem contrato canônico, fonte física ou conexão read-only, a execução falha fechada antes de ler ou alterar qualquer dado.

Não use o antigo servidor/HTML diretamente. A V5 não abre Edge, Chrome, localhost ou a interface web.
