# Manual do Extrator

O Extrator lê os arquivos reais do eFootball, compara com o contrato do banco e
aplica os itens selecionados pelo operador. A operação é feita pelo aplicativo;
SQL manual não é uma etapa normal de extração.

## Rotina após atualizar o jogo

1. Termine o download/aplicação da atualização e deixe os arquivos estáveis.
2. Abra `7-VARREDURA-DO-JOGO/ABRIR-EXTRATOR.cmd` na pasta oficial.
3. Execute a leitura e comparação. Confira a origem/versão e os itens apresentados.
4. Selecione e aplique pelo próprio aplicativo. Aguarde a conferência final que relê
   o banco: extração local ou envio de um lote não prova a carga inteira concluída.
5. Execute a obtenção de níveis/orçamentos no fluxo disponível. Para a fonte eFHUB,
   use `ABRIR-EXTRATOR-NIVEIS-EFHUB.cmd`. A coleta aplica e confere por lotes.
6. Prepare/revise a fila pelo fluxo do sistema. Extração integral não altera uma
   fotografia selada que a Máquina 2 já está processando.

Se houver interrupção, preserve relatórios, provas e estado local. Lotes já aplicados
não se tornam pendentes apenas porque a execução seguinte começou. Examine erros
reais; não declarar conclusão sem releitura independente dos valores persistidos.

## Ofertas do Jogo

Deixe o eFootball aberto em Contratos. Não precisa abrir cada box.
Após aplicar a extração aprovada, o extrator captura e registra o catálogo,
atualiza os contextos comerciais e solicita a atualização da leitura do site.
Não há envio manual adicional dessa etapa. A varredura somente leitura continua
sem gravação; Atualizar Boxes Novas permite repetir apenas a consulta de ofertas.

A conexão usa a credencial protegida do aplicativo. Se o jogo estiver fechado,
a sessão não estiver carregada ou a conexão falhar, a captura anterior é preservada.
Os relatórios ficam na pasta da rodada. `box_catalogo_jogo_atual_v1` fornece a
última captura, com fonte e horário. Não inventar participantes quando um agente
novo ainda não tem vínculos extraídos. Ver MAPEAMENTO-BOXES-RUNTIME.md.

## Como os dados são protegidos

O contrato tipado define arquivo, registro, campo, tipo, bit/largura, versão/hash e
destino. Nomes traduzidos são apresentação; não associar identidades por semelhança.
As relações normalizadas de posições, habilidades, ímpetos e estilos alimentam os
consumidores. A leitura física conserva a origem mesmo quando há correção manual.

Toda correção manual pedida pelo usuário deve ser registrada em
`clube_novo.valor_do_dono`: destino, chave primária completa, coluna, valor JSON e
motivo. O banco aplica, protege e registra histórico atomicamente. Um UPDATE direto
não cria essa decisão. O Extrator nunca remove a proteção para substituir o valor.
Outros campos não protegidos do mesmo registro continuam atualizáveis.

[Prioridade manual e conferência](../../4-DOCUMENTOS/EXTRATOR/PRIORIDADE-CORRECOES-MANUAIS.md).

## Níveis e orçamento

- Nível comprovado de 1 a 99: orçamento `2 × (nível − 1)` conforme a fonte válida.
- Nível 1 comprovado: orçamento zero válido, carta sem evolução.
- Estimativa pelo ID não é comprovação física de nível/orçamento.
- Resposta eFHUB com identidade correta e `levelCap` inteiro zero significa
  `aguardando_orcamento`. Não grava nível/orçamento inventado nem conta como falha.
- Identidade divergente, valor malformado e falha HTTP continuam erros.
- A mesma espera não é consultada novamente no mesmo dia em `America/Sao_Paulo`.
  A próxima execução diária pode tentar de novo; o aplicativo não abre sozinho.

A Ficha mostra **Orçamento ainda não divulgado** pela regra automática. Ao chegar
prova válida, o aviso sai e a carta recupera a elegibilidade normal. A inclusão em
fila respeita o fluxo de preparação/revisão, sem modificar pacotes selados em uso.
Cartas excluídas ficam fora dos levantamentos operacionais; só uma extração futura
com nova evidência pode trazê-las de volta. [Regra diária](../../4-DOCUMENTOS/ORCAMENTO-REGRA-DIARIA.md).

## Cuidados de manutenção

Sobreposição do técnico: `Coach.bin`, bit 192/largura 7. A antiga leitura no bit 135
estava errada. Conte: 69. Técnicos são insumos do Otimizador, não do Bonificador.
[Prova](../../4-DOCUMENTOS/EXTRATOR/SOBREPOSICAO-192-1209.md).

O EXE de níveis inicia `executor/desktop_worker.py`, que importa `efhub_levels.py`;
esses fontes externos fazem parte da entrega. Não conservar apenas os executáveis.
Credenciais, arquivos de jogo, estados e provas locais não devem ser enviados ao GitHub.
Mantenha as dependências e os leitores declarados no contrato.

[Textos oficiais](../../4-DOCUMENTOS/MANUAL-DOS-TEXTOS-DO-JOGO.md) ·
[Mapa físico](../../4-DOCUMENTOS/MAPA-DO-CODIGO-DO-JOGO.md) ·
[Contratos do banco](../../4-DOCUMENTOS/MANUAL-DAS-TABELAS.md).
