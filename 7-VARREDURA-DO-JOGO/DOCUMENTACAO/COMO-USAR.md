# Como usar o Extrator eFootball Desktop V5.3

**Fluxo atual:** aplicativo desktop, Radar de Lançamentos V2 e varredura
somente leitura.

Abra somente `7-VARREDURA-DO-JOGO\ABRIR-EXTRATOR.cmd`. O uso diário não exige
navegador, localhost, ChatGPT nem comandos manuais. O manual completo está em
[MANUAL-DO-EXTRATOR.md](MANUAL-DO-EXTRATOR.md).

## O que nunca acontece sozinho

- **INICIAR VARREDURA** não altera o banco nem os arquivos do jogo;
- nenhum item é enviado ao banco sem seleção, aprovação e confirmação;
- avisos conhecidos, registros antigos e observações do Radar não entram no
  pacote;
- Otimizador e Bonificador não são executados pelo Extrator;
- a proteção dos motores só é instalada ou atualizada por um clique próprio.

## Primeira configuração

1. Clique **CONFIGURAR CONEXÃO**.
2. No Supabase, use **Connect** e copie a connection string Postgres completa,
   já com a senha atual. Se a conexão direta não funcionar, use **Session
   pooler**.
3. Cole no campo mascarado e clique **TESTAR E SALVAR**. O teste é somente
   leitura e a credencial fica protegida pelo Windows para este usuário.

## Rotina de varredura

1. Quando o jogo tiver uma atualização pública, abra o jogo e espere o download
   terminar. Para procurar pré-cargas, também é permitido fazer uma varredura
   diária.
2. Abra `ABRIR-EXTRATOR.cmd` e clique **INICIAR VARREDURA**.
3. Aguarde a frase **conferência concluída — somente leitura**.
4. Clique **VER RESULTADO** e leia primeiro:
   - o resultado geral;
   - o que mudou hoje;
   - se alguma ação é necessária;
   - o que o programa recomenda fazer agora.
5. Leia o **Radar de boxes e possíveis lançamentos** e a seção de uso nos
   motores antes de decidir qualquer envio.

## Como reconhecer uma varredura válida

Uma varredura válida:

- termina com **conferência concluída — somente leitura**;
- permite abrir `resultado.html` pelo botão **VER RESULTADO**;
- declara que não alterou banco, cartas nem arquivos do jogo;
- cria a prova local do Radar em `radar-lancamentos.json`;
- pode terminar com avisos amarelos ou azuis sem ter falhado.

Na primeira rodada do Radar V2 não existe histórico V2 comparável. Essa rodada
vira a referência local e não chama todas as boxes de novas. A partir da próxima
rodada comparável, o relatório separa boxes novas, conhecidas e alteradas.

## Avisos normais do Radar V2

### Card identificado, mas sem nome de box

O arquivo pode trazer o identificador do card e deixar completamente vazio o
nome da box. O relatório mostra **registro físico possui card, mas ainda não
possui nome de box**.

Isso é um aviso acompanhado, não uma falha da varredura. O programa:

- não inventa o nome da box;
- não chama o card de lançamento por causa desse registro;
- não coloca o registro nas boxes, no pacote ou no banco;
- não bloqueia outras mudanças comprovadas;
- verifica o caso novamente em toda nova varredura.

### Ligação antiga entre box e card

O arquivo de boxes também pode conservar uma ligação completa para um card que
já não existe no `Player.bin` atual. O relatório mostra **referência física
antiga, fora dos lançamentos atuais**.

Essa relação fica apenas como referência: não vira lançamento, publicação ou
item de pacote. Não recrie o card nem troque seu identificador manualmente.

As quantidades desses dois avisos podem mudar quando a Konami atualizar os
arquivos. O importante é o relatório explicar o significado, o efeito nos
dados de hoje e o que deve ser feito.

## Como reconhecer uma pendência real

Não aplique nada desta execução quando ocorrer qualquer um destes sinais:

- a janela mostrar **worker encerrado com código 2**;
- a janela disser que terminou sem confirmação final completa;
- o relatório mostrar problema técnico vermelho ou Radar indisponível;
- houver falha de conexão, fonte ausente, arquivo inválido ou leitura
  incompleta;
- o botão **VER RESULTADO** informar que o resumo HTML não existe.

Clique **ABRIR LOG**, leia a causa, corrija o problema e faça outra varredura.
Uma falha não deve ser resolvida selecionando menos itens nem forçando um
pacote.

## Quando é permitido aplicar dados

Só aplique quando a varredura tiver terminado corretamente e o relatório
separar dados novos ou alterados que estejam disponíveis para seleção.

1. Clique **ESCOLHER O QUE ENVIAR**.
2. Nada começa marcado. Marque somente os dados atuais que deseja enviar.
3. Crie o pacote com os marcados e confira a lista.
4. Clique **APROVAR PACOTE**.
5. Clique **APLICAR PACOTE** e confirme a ação separada.

Antes de gravar, o aplicativo confere novamente execução, fontes, seleção e
pacote. A aplicação usa uma transação: divergência anterior à confirmação
desfaz tudo. Depois, outra conexão lê o banco novamente para conferir o
resultado.

Não existe aplicação quando o resultado disser **nada para enviar**. Pendências
já conhecidas, registros antigos, itens inválidos e avisos do Radar não são
oferecidos para seleção. Eles continuam visíveis para acompanhamento.

## Proteção dos motores

Depois de aplicar dados, faça outra varredura. Somente quando ela terminar
corretamente e disser **nada para enviar**, use **INSTALAR/ATUALIZAR PROTEÇÃO
DOS MOTORES**. Leia a prévia e confirme somente se concordar com a quantidade
de cards e resultados que precisarão ser refeitos.

A proteção não impede inserir, mostrar ou publicar cards. Ela impede somente
que Otimizador e Bonificador usem um card cuja coleta atual ainda não foi
comprovada. Espaço realmente conferido e vazio significa que o card não possui
aquele item; isso continua sendo uma coleta completa.

Na primeira ativação, o botão instala as travas e registra todos os cards
conferidos. Depois, registra somente cards novos ou alterados. Se tudo já estiver
atual, a prévia informa isso e nenhuma escrita é feita.

## Falhas e logs

Falhas de conexão, leitura, pacote, transação ou conferência final aparecem na
janela e ficam registradas no botão **ABRIR LOG**. Se a janela disser que o
COMMIT ficou incerto, não repita a ação: abra o log para auditoria.
