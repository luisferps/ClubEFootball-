# Medição da correção de estilos — 09/09/2026

## Resultado
38 publicações simuladas, duas por função (19 funções), em **15,95 segundos**.
- Calcular os estilos: **0,041 segundo** no total.
- Gravar o resultado e vincular à linha: **0,153 segundo**.
- Finalizar e publicar pela rotina canônica: **15,725 segundos**.
- Projeção linear para 7.455 republicações: **51,4 minutos**.

A projeção não é promessa: a carga do banco, o aquecimento das consultas e a
composição dos lotes mudam o tempo. Não inclui toda a preparação e a correção
dos 67.795 resultados. O custo dominante medido é a publicação.

## Método e preservação
O teste percorreu o finalizador atual, com resultado temporário contendo os
pontos da política V12. Conservou o selo V11 apenas dentro da simulação para
medir o caminho que já existe; não prova que a integração produtiva V12 foi
concluída. Uma exceção controlada reverteu toda a simulação antes do retorno.
O SQL verifica que os resultados temporários não sobreviveram.

Readback posterior: 55.151 publicações ativas, zero resultados V12, lote
Bonificador pausado, zero itens processando. IDs, notas e selos dos três casos
Vieira/Desailly permaneceram iguais aos anteriores. Nenhuma fila foi reordenada.

## Encaminhamento
Usar execução autônoma em lotes, com progresso, retomada e recibo, para corrigir
somente os estilos e publicar pelo contrato canônico. Um calculador externo
não elimina o tempo gasto no banco; sua vantagem é trabalhar sem rodadas do
assistente por linha/lote. Não foi iniciado nenhum executor por esta medição.

## Estado dos arquivos oficiais
A pasta oficial desta máquina contém o código V12, os contratos preparados,
testes e o EXE 2.0.29.0. A produção V12 continua bloqueada, os resultados antigos
ainda não foram substituídos e a Máquina 2 não foi atualizada.
Otimizador, normalização e demais parcelas de bônus foram preservados.

Evidência: MEDICAO-CORRECAO-ESTILOS-0909.json.
Script de medição: SQL/MEDIR-CORRECAO-ESTILOS-COM-ROLLBACK-0909.sql.
