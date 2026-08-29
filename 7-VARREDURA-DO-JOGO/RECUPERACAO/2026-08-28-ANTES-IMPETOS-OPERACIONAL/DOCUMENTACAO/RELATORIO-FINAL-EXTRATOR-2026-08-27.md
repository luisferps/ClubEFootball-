# Relatório final — Extrator eFootball 4.1

## Resultado

O extrator novo e limpo foi concluído, validado e instalado em modo protegido. Nenhuma escrita foi feita no Supabase nesta etapa. `clube.carta_jogo` e `clube_novo.carta_jogo` continuam com 42.803 cartas e o mesmo fingerprint integral anterior.

## O que foi entregue

- três modos inequívocos: atualização por diff, metadados e recarga completa de contingência;
- fonte física governada pelo mapeamento comprovado, sem inferência de offsets;
- manifesto selado, validade curta, `execution_id`, seleção revisável e hash individual de cada item aplicável;
- executor local sem credenciais no HTML, com preflight somente leitura, token descartável, confirmação final, transação fail-closed, idempotência e readback preparados para uma etapa futura;
- versão anterior preservada e procedimento de recuperação;
- Manual do Extrator autocontido;
- gabarito integral independente e somente leitura para o teste manual final.

## Prova da carga integral independente

A carga foi extraída novamente do CPK atual usando somente os bytes físicos e o mapeamento como entradas de extração. Nenhum diff ou CSV extraído anteriormente foi consumido como entrada.

- CPK: 9.415.400 bytes; SHA-256 `44df868c2613d532292d87072c0863a907d6a5f0cc40f914d355e56d74edfcc5`;
- saída: 43.072 cartas, 43.072 `card_id` únicos, zero duplicidades, 29 campos;
- CSV integral: 19.908.897 bytes; SHA-256 `07c9b8cf9690b1f177cd724ada4329351424b71fb8c6d09e4cd35d3875389c38`;
- conjunto esperado de IDs: exato, sem ID inesperado e sem ID ausente;
- comparação com a referência anterior: 269 novas, 34 alteradas, zero possivelmente inativas e 42.769 inalteradas;
- amostra do banco: 54/54 cartas exatamente iguais em todos os campos comparados.

## Prova pela interface

No navegador real, o modo **Recarga completa** foi acionado com o CPK, o gabarito, a caixa de entendimento e a frase `RECARREGAR COMPLETO`. A interface mostrou:

- 43.072 cartas;
- 43.072 IDs únicos;
- zero duplicadas;
- 29 campos;
- status **GABARITO EXATO**;
- SHA-256 exatamente igual ao arquivo selado.

O executor estava visivelmente em `dry-run`, com “banco protegido; sem escrita real”.

## Prova do executor protegido

O fluxo de preparação recebeu um manifesto novo de 269 inserções e 34 alterações:

- banco consultado em `transaction_read_only=true`;
- 303 itens prontos e zero já aplicados;
- contagens e itens ligados ao manifesto selado;
- tentativa do endpoint de aplicação bloqueada por HTTP 403;
- escrita real desabilitada na configuração distribuída.

## Prova de zero escrita

Fotografias somente leitura antes e depois do teste registraram, para `clube.carta_jogo` e `clube_novo.carta_jogo`, 42.803 linhas, 42.803 IDs únicos e fingerprint `ff67b8a2e544570dae42ed71d8428821`. Nenhum catálogo ou outra tabela foi alterado.

## Próxima etapa

O usuário pode repetir o teste manual seguindo `INSTRUCOES-COMPARACAO.md`. O botão de subida ao banco não deve ser testado até uma nova autorização explícita. Quando autorizado, o alvo deve ser configurado de forma restrita como `clube_novo.carta_jogo`, mantendo todo o schema `clube` como referência e rollback.

## Atualização 4.0 — fontes separadas por família

A descoberta automática deixou de tratar os CPKs como um conjunto genérico. Cada operação agora pede apenas suas próprias fontes:

- **cartas:** somente o DT870 da atualização, obrigatório e autoritativo;
- **catálogos:** DT870 atualizado, DT200, DT870 original e `dt261_bra`, cada qual identificado e validado separadamente;
- **ímpetos:** união canônica com procedência por arquivo, preservando 32 IDs que não aparecem no DT870 atualizado;
- **playstyles:** DT200 como base semântica e DT870 atualizado como overlay;
- **textos:** o `dt261_bra` é reconhecido como fonte física, mas a atualização por entrada permanece bloqueada até o mapeamento integral fechar;
- **famílias ainda incompletas:** aparecem como **Não suportada nesta atualização** e produzem zero item aplicável.

O painel mostra, em linguagem simples, quais fontes foram encontradas e para que servem. A escolha manual só aparece para a fonte que falta na operação selecionada. A ausência de DT200, DT870 original ou `dt261_bra` não bloqueia a recarga de cartas.

A prova física passou com quatro fontes reais: 72 habilidades, união de 440 ímpetos, 36 playstyles de base e 2 overlays novos mantidos somente para revisão. O DT870 original é aceito apenas com seu fingerprint selado porque seu `PlayerBooster.bin` usa formato legado. Nenhuma escrita no banco foi realizada durante essa atualização ou seus testes.

O executável instalado também passou no teste de abertura real: iniciou um executor oculto, abriu uma janela própria do Edge e permaneceu em `dry-run`, com escrita desabilitada. Na prova visual de ausência, somente o DT200 foi retirado da descoberta; a tela exibiu um único botão **Escolher somente esta pasta** para o DT200, informou que catálogos aguardavam uma fonte e manteve as cartas liberadas pelo DT870 atualizado. Os componentes técnicos e lançadores antigos ficaram preservados, mas fora da visão normal da pasta operacional.

## Identidade e organização final

O único lançador visível passou a se chamar `Extrator eFootball.exe`, e a janela passou a se chamar `Extrator eFootball`. O ícone próprio de bola, lupa, seta de extração e base de dados foi incorporado ao recurso nativo do executável em nove tamanhos. O Explorer/Shell extraiu o novo ícone com sucesso, e seu fingerprint visual difere do lançador anterior.

A raiz operacional foi reduzida a quatro itens visíveis: o executável e as pastas `DOCUMENTACAO`, `RESULTADOS-E-VALIDACOES` e `RECUPERACAO`. O antigo `VERSOES-ANTERIORES` virou `RECUPERACAO`; `ENTREGAS` virou `RESULTADOS-E-VALIDACOES`; arquivos antigos soltos e cache temporário foram movidos para recuperação. Nenhum CPK, gabarito, prova, manual, relatório ou versão foi apagado.
