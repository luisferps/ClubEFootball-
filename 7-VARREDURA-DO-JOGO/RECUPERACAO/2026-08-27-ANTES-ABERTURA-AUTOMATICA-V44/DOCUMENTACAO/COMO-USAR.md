# Como usar o Extrator eFootball

1. Dê dois cliques em **Extrator eFootball.exe**.
2. Aguarde o aplicativo localizar sozinho os arquivos do jogo e conectar a base de `clube_novo` em leitura.
3. Clique em **Atualização por diff**. A comparação começa automaticamente e mostra o resumo; você não escolhe CSV. Na recarga completa, marque apenas a confirmação simples e clique em **Validar carga completa**.
4. Leia o resumo. Se quiser preparar o envio futuro, clique em **OK — preparar envio ao clube_novo**.
5. O envio só pode ocorrer depois de um pré-voo aprovado e de uma confirmação final inequívoca dentro do próprio aplicativo.

Não procure nem selecione CSV de base ou gabarito. A base incremental vem automaticamente de `clube_novo.carta_jogo` em somente leitura, e a referência integral é interna e versionada. O aplicativo só pede uma pasta quando não consegue localizar uma fonte física obrigatória ou encontra uma situação ambígua.

Ao terminar, a tela sempre mostra uma destas respostas: nova carga com as contagens, **SEM MUDANÇAS** ou comparação bloqueada com o motivo. Quando existem diferenças, o botão seguinte é **OK — preparar envio ao clube_novo**.

O usuário nunca precisa abrir o Supabase nem fazer upload manual de CSV. A conexão já existente é usada pelo executor local; nenhum segredo aparece na tela. O envio só fica disponível depois do pré-voo, da caixa de conferência e da frase final do pacote atual.
