# Bonificador completo V12 — retomada conferida em 09/09/2026

Os 15 arquivos do pacote entregue à Máquina 2 conferem com o manifesto SHA-256 e com os arquivos oficiais. Motor v12-0909-estilo-funcao-ativacao-v1; aplicativo 2.0.29.0.

Restam 14.107 linhas de bonificação completa: corpo, pé ruim, estilos de jogo e IA. O operador retoma pelo mesmo OPERACAO-CORRECAO-FISICA/INICIAR-REPROCESSAMENTO.bat. A ordem e os resultados concluídos são preservados.

A revisão da retomada encontrou e corrigiu dois impedimentos no banco: o UPDATE de auditoria não tinha filtro; três restrições da tabela de lote ainda aceitavam somente o conjunto V11. A auditoria agora identifica a execução e a restrição exige um conjunto coerente motor/contrato/fórmula V11 ou V12, sem aceitar combinações cruzadas.

Migrações aplicadas: corrigir_filtro_auditoria_retomada_bonificador_v12 e permitir_contrato_v12_coerente_lote_bonificador. As fontes SQL oficiais foram atualizadas. Nenhuma fórmula foi alterada.

Teste em transação revertida: preparar a retomada liberou V12; o controle aceitou iniciar; a reserva devolveu a primeira linha 488143 com contrato bonificador-regua-v4. Após ROLLBACK, o banco confirmou o lote pausado, 14.107 pendentes, zero processando/falha e política aguardando o início pelo operador. Nenhum motor foi iniciado e nenhuma reserva ficou persistida.

Esses dois ajustes são somente no banco. Não é necessário copiar novamente o pacote do Bonificador.
