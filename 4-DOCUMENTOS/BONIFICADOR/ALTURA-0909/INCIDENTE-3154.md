RESOLVIDO em 10/09/2026: Robert Lewandowski, centroavante fixo. O evento de importação de 05/09 comprova o resultado 60041; a linha conservava metadados do resultado anterior 1531, de 31/08. Carta, versão, fórmula, contrato e pontuação bruta (-52,1) conferidos. Sincronizados somente os metadados da linha. Publicação confirmada com nota 100,5345657095811464 e correção concluída; resultado do Otimizador preservado. SQL: SQL/RECONCILIAR-LEWANDOWSKI-3154.sql. O texto abaixo registra o diagnóstico anterior.

# Envio local — linha 3154

O lote parou na finalização: selo do Otimizador nao coincide com a linha.
Linha 3154, resultado do Otimizador 60041. Não estava publicada.
Selo na linha: 72133f08438b82e5263b04081cc9fbf9807fbffdda423574e30587ea541e1433.
Selo no resultado: 957b8519bf392771dfe2376fd4cc523a7f6caddc698be5f61fc188d3a2b60d06.

Correção do fluxo: receber altura/IA mantendo estado aguardando_otimizador quando faltarem atributos completos ou houver incompatibilidade de selo/versão. Não alterar os resultados ou selos do Otimizador nem autorizar publicação incompatível. Casos publicados conservam a referência antiga enquanto a nova não puder ser publicada.
Teste transacional da linha passou, sem erros, com rollback. Liberada apenas a entrada 3154 do erro de envio para nova tentativa pelo mesmo JSON. Não alterada a fila do Otimizador.
A divergência do Otimizador continua pendente de diagnóstico; receber os bônus não significa corrigir essa divergência.
Não exige substituir o executável da máquina 2: reabrir ENVIAR-RESULTADOS-ALTURA-IA.bat.
