# Como usar o Extrator eFootball

1. Dê dois cliques em **Extrator eFootball.exe**.
2. Aguarde o resumo automático. O aplicativo localiza as fontes e compara cartas e metadados sozinho.
3. Veja o indicador: **Tudo atualizado** em verde significa que não há ação; **Atualização disponível** em vermelho significa que há novidades para revisar.
4. Se houver novidades de cartas, abra os detalhes e clique em **OK — preparar envio ao clube_novo** somente quando quiser aplicar.
5. Aguarde sempre o estado visível **Preparando** ou **Aplicando**. O botão fica bloqueado durante a operação; não clique novamente.
6. O envio só ocorre depois do pré-voo, da caixa de conferência, da frase final e do clique explícito. Metadados sem adaptador canônico permanecem apenas para consulta.

Não procure nem selecione CSV de base ou gabarito. A base incremental vem automaticamente de `clube_novo.carta_jogo` em somente leitura, e a referência integral é interna e versionada. O aplicativo só pede uma pasta quando não consegue localizar uma fonte física obrigatória ou encontra uma situação ambígua.

Ao terminar, a tela sempre mostra uma destas respostas: atualização disponível com contagens, **Tudo atualizado** ou verificação bloqueada com o motivo. O conjunto revisável aparece antes das fontes e opções técnicas.

O usuário nunca precisa abrir o Supabase, escolher JSON de metadados nem fazer upload manual de CSV. A conexão já existente é usada pelo executor local; nenhum segredo aparece na tela. Cada pacote possui um identificador único, e o servidor bloqueia ou reutiliza com segurança cliques repetidos.
