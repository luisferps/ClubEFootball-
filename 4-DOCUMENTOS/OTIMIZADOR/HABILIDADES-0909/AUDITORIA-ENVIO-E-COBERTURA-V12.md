# Enviador e cobertura das regras V12 — 09/09/2026

## Critério de encerramento aprovado

Luis Fernando confirmou nesta sessão: cada linha vigente deve terminar gravada em `clube_novo` e condizente com as últimas regras. Reaproveitar integralmente o que já estiver correto; corrigir ou refazer somente o necessário, sem duplicar linhas e sem reordenar os lotes existentes. A correção inclui todas as etapas, atributos, distribuição, adicionais, sugestões, selos e resultado final; nunca apenas a nota ou IDs de habilidades.

Históricos, antecessores e cartas removidas permanecem preservados como evidência. Não reapresentá-los como resultados atuais, não inventar orçamento de carta removida e não declarar a produção encerrada enquanto houver linhas vigentes aguardando os motores ou confirmação do banco. O Bonificador segue a política de estilos já aprovada; a normalização da nota continua inalterada. A publicação anterior, quando existente, permanece durante o processamento até a substituição normal autorizada.

## Auditoria dos pacotes que provocaram o erro

Consulta somente de leitura em `clube_novo`, cruzada com os IDs das fotografias oficiais locais:

| Situação das 1.220 linhas dos dois pacotes antigos | Quantidade |
|---|---:|
| Resultado atual já recebido no lote antigo | 465 |
| Correção pontual V12 já recebida no prefixo novo | 673 |
| Busca integral já encaminhada ao prefixo novo | 82 |
| Sem resultado e sem encaminhamento | 0 |

Fotografias anteriores: `57071c55-9ebc-4ad1-b7d8-bf8729b4ae56` (1.213 IDs) e `0789ae01-111c-41f1-98ef-7b4311f2de0d` (7 IDs). As 82 pendentes já pertencem ao lote `c48f3425-d717-4e30-b64a-bf10effa3148`; não as inserir novamente. As 673 pontuais fazem parte das 938 correções completas já confirmadas anteriormente, não são nova gravação nesta auditoria.

O banco ainda contém duas pendências no primeiro lote antigo: 379929 e 379937, Imad Jasem (8562459). A carta está em `player_delete_list`, não tem evidência atual de nível/orçamento e não tem publicação. Essas duas linhas não estavam nas 1.220 IDs das fotografias preservadas. Não é correto chamar o lote inteiro de concluído.

`lotes_sem_pendentes` significa que a fotografia atual não contém linhas **elegíveis**. O manifesto consulta `otimizador_fila_prioridade_v1`; cartas removidas, sem evidência ou com entradas incompatíveis ficam fora. O processador e o enviador respeitam essa seleção sem apagar o histórico.

## Demais lotes e cobertura dos bloqueios

Os outros seis lotes têm **126.318 linhas elegíveis**, todas com motor esperado `otimizador-fila-producao-v3-local-20260909-habilidades-v12`. A conferência encontrou exatamente as contagens das fotografias renovadas, mantendo a ordem:

| Lote | Linhas elegíveis |
|---|---:|
| ddbcbc86-1ae7-4b95-b9f0-22601f41b61d | 18.324 |
| 7581b184-dccb-4a4b-9ad9-c767d4f4947c | 824 |
| c5e38fd5-877c-416e-8063-977e24d229db | 17.138 |
| b02cf0df-d271-4659-8e42-64a8b88b0134 | 89.615 |
| 1833e4d0-1707-4ea2-8ba3-3733b5101310 | 22 |
| 5c9614ce-55a2-4f9d-9ead-435e703e9058 | 395 |

Nova busca global de adicionais bloqueadas nos resultados ainda referenciados: os 28 registros não invalidados de cartas ativas com bloqueio são antecessores de revisão de orçamento. Suas **28 substitutas existem e já estão na fila V12**. Quatro outros registros são do Imad removido, sem publicação. Os registros invalidados são históricos e não devem ser reabertos. Não foram encontradas novas linhas de cartas ativas com bloqueio sem esse encaminhamento.

As seis exclusões da auditoria anterior por ausência de evidência são cartas removidas, todas sem publicação: Imad Jasem (379930–379933), Rasul Luay (379947) e Sattar Ezzeddin (379953). Essa é a explicação atual da exclusão, não uma autorização para estimar atributos ou orçamento. As oito linhas mencionadas acima permanecem no banco com seu histórico original.

A auditoria detalhada anterior de ganho marginal e opções liberadas continua registrada em `CORRECAO-PONTUAL-E-REFILA.md`: 938 correções já confirmadas, 3.537 buscas no prefixo. A consulta atual dos bloqueios não substitui essa análise de ganho marginal nem significa que as buscas pendentes terminaram.

## Reparo de envio

O erro ocorria ao abrir uma fotografia V11 preservada, embora a seleção a tivesse marcado sem linhas elegíveis. O enviador agora:

1. Mantém a ordem de `FILA-ATIVA.json` e pula somente os lotes explicitamente listados sem linhas elegíveis.
2. Não abre manifesto nem configuração quando não existe JSON pronto.
3. Preserva, sem enviar, envelopes de outra fórmula/contrato/motor, permitindo continuar nos resultados atuais.
4. Recusa envelope misturado ou sem selos. Não troca selos para converter V11 em V12.
5. Não rejeita um resultado só porque o agregado do lote mudou. Identidade, versão da entrada e selos por linha continuam validados pelo importador canônico.
6. Mantém a validação de integridade de pacotes atuais e identifica o lote no erro operacional.

A decisão usa a fórmula do resultado, não a idade do arquivo. Resultado antigo ainda compatível com os selos da linha pode seguir para validação oficial. Resultado de regras anteriores para linha agora V12 permanece no histórico e a fila atual produz sua substituição. O enviador não cria novas filas nem faz correções parciais.

Os JSONs que existem somente na Máquina 2 não foram lidos remotamente nesta conferência; o inventário local do enviador verifica seus selos quando for executado. O cruzamento de banco/fotografia acima cobre os IDs dos dois pacotes antigos identificados, não comprova o conteúdo de todo arquivo remoto.

## Entrega e validação

Novo pacote **REPARO-ENVIADOR-V12**, posterior ao REPARO-MOTORES-V12 já instalado. Substitui dois arquivos oficiais: `bin/OperacaoLocalJson.exe` e `programas/operacao_local_json.py`. Instalar a pasta dentro de `OTIMIZADOR/OPERACAO-LOCAL-JSON`, por `APLICAR.cmd`, após parar processador e enviador com Ctrl+C. Bonificador pode continuar rodando. Os BATs continuam **PROCESSAR-FILA-PRINCIPAL.bat** e **ENVIAR-FILA-PRINCIPAL.bat**.

44 testes aprovados (29 de operação e 15 de prioridade). EXE e instalador executados em espelho isolado: ausência de linhas elegíveis/JSONs atuais não causa erro; selo antigo num lote ativo continua recusado com código 2; fila e JSONs permanecem idênticos. Os cinco fontes de cálculo embutidos são iguais aos oficiais. Os três pacotes anteriores com esses dois arquivos foram sincronizados para não restaurarem a falha.

O operador confirmou a instalação do **reparo anterior** pelo backup `motores-retomada-v12-9866126a7fa84046b2e713e53878ce31`; depois mostrou o cálculo de 403222. Isso comprova retomada do cálculo anterior, não envio confirmado. A instalação deste novo reparo do enviador ainda depende da cópia e execução na Máquina 2. A auditoria não gravou resultados nem modificou fila no banco. Produção integral ainda em andamento; não declarar encerramento.
