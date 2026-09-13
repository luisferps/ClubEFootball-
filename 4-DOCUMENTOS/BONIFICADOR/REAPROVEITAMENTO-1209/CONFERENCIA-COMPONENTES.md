# Conferência de componentes para reaproveitamento

Duas funções internas foram implantadas; ainda não estão ligadas à seleção
ou à clonagem em produção. Elas não alteram resultados nem publicações.

bonificador_componentes_vigentes_v1 calcula a referência de conferência com
as mesmas operações aprovadas do editor: doze medidas físicas, altura
independente, pé, IA e estilos por função/posição. Não considera técnico.
bonificador_resultado_conforme_componentes_v1 compara as parcelas e aliases
numéricos completos. O nome da versão não decide a equivalência.

Validação inicial: um resultado V13 de cada uma das 19 funções coincidiu em
detalhe físico, pé, IA e total. O comparador aceitou um resultado válido mesmo
com outro rótulo de versão; rejeitou IA alterada, parcela ausente, faltou não
vazio e bônus extra não declarado. bonus_outros é objeto JSON vazio, não número.

Ainda é obrigatório: conferir identidade/entradas/selos e procedência antes
da clonagem; comparar snapshot anterior com entrada posterior à extração;
selecionar sucessores válidos; criar resultado próprio por linha; verificar
idempotência e finalização. As funções aqui não substituem essas travas.

A seleção geral bonificador_contexto_fila_v7 ainda contém o filtro V12 e não
foi liberada nem executada. Sua integração deve usar conferência persistida
por lote, evitando recalcular referências para toda a população em cada
pedido de página. Nenhuma fórmula de bônus foi alterada.

Permissões: SECURITY INVOKER, search_path vazio, EXECUTE revogado de PUBLIC,
anon e authenticated. Conferências executadas administrativamente.


## Integração implantada em 13/09

`reaproveitar_bonificador_conforme_v1` clona um resultado próprio da linha destino após conferir contexto, posse do resultado, selos, igualdade das entradas efetivas e componentes atuais. A origem permanece imutável. Mudança apenas de data/nome/procedência pode receber nova certificação, apoiada no snapshot anterior; medida corporal alterada é recusada. O novo resultado preserva parcelas e registra auditoria de revalidação sem recálculo.

A fila `bonificador_contexto_fila_v7` não exige rótulo V12: verifica selos e componentes, com certificado descartável por linha. Lotes concluídos e linhas inválidas não reabrem. A verificação é invalidada quando mudam dados da carta, regras/catalogos relevantes ou o resultado. O fingerprint do código da conferência também impede usar certificado emitido por outro código.

Testes com rollback: clone sem alterar origem/parcelas; repetição idempotente; rejeição de contexto/posse divergentes; data nova aceita sem recálculo; medida corporal nova recusada; alteração corporal invalidou certificado; a RPC real da fila deixou de oferecer uma linha com bônus conforme, com e sem cache. Tentativa de alterar resultado continuou proibida pelo guard de imutabilidade.

Ainda falta executar a seleção/reutilização por lote novo, medir cobertura e tratar somente as exceções. Nenhuma rodada produtiva de Bonificador foi iniciada por estes testes.

## Seleção por lote implantada — 13/09

`reaproveitar_bonificador_lote_fatia_v1` exige lote integral explícito, preparado, pausado e com contrato vigente. Seleciona por identidade e entradas; prioriza sucessor de altura/IA, depois correção preparada e resultado vinculado. O cloner aceita sucessor auditado sem exigir que a linha histórica já tenha trocado seu vínculo.

A tabela `bonificador_reaproveitamento_lote_v1` registra origem e motivo por linha, distinguindo reaproveitado, recalcular e bloqueado. Uma falha de conferência não é classificada como necessidade automática de recálculo. A seleção continua da próxima linha sem repetir as conferidas com as mesmas entradas/regras.

Teste em rollback: lote não selado recusado; duas fatias de três linhas reaproveitadas; primeira fatia preservada; zero auditorias de teste persistidas. A alteração do estado de preparo usada no ensaio foi revertida junto com todos os clones. Nenhuma selagem nem reutilização produtiva ocorreu no lote antigo.
