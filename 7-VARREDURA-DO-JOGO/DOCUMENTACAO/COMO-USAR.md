# Como usar o Extrator eFootball V4.6

1. Abra a pasta **7-VARREDURA-DO-JOGO** e execute **INICIAR-EXTRATOR-V46.cmd**. Nesta correção, o `Extrator eFootball.exe` ainda é o binário preservado da V4.5.
2. Aguarde a localização das fontes e a comparação automática.
3. Deixe a aba/painel de **Metadados** terminar a leitura física de nacionalidade, clube, liga e tipo de carta.
4. No painel **Etapa 1 · Metadados antes dos cards**, clique em **Aplicar metadados e vínculos**. Confirme a operação. O executor grava os catálogos primeiro e só depois os vínculos dos cards; nenhuma linha é apagada automaticamente.
5. Compare os metadados novamente. Se houver card novo que ainda não existia na tabela, ele pode aparecer como vínculo pendente até a etapa de cards.
6. Revise o diff de cards e use **OK — preparar envio ao clube_novo** para novas/alteradas. Aguarde o preflight, marque a conferência, digite a frase da execução e aplique.
7. Se a carga inseriu cards que estavam pendentes de vínculo, execute novamente a reconciliação de metadados/vínculos.
8. Só considere o Extrator concluído quando os cards destinados aos motores estiverem completos ou quando uma ausência estiver registrada como ausência legítima do próprio jogo.

A ordem operacional é:

`METADADOS -> VÍNCULOS -> CARDS -> READBACK -> OTIMIZADOR -> BONIFICADOR`

Não selecione CSV ou JSON manualmente. As fontes físicas são lidas pelo próprio Extrator, e a conexão segura já existente é usada pelo executor local. Nenhuma senha vai para o HTML/JavaScript.

Se alguma fonte, estrutura, chave, FK ou prova física não conferir, a operação deve terminar como **bloqueada**. Não preencha clube, liga, nacionalidade, tipo, ímpeto ou outro insumo por suposição.
