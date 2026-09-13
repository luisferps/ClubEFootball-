# Processador JSON: falha explícita

Erro de cálculo permanece gravado em FALHAS-CALCULO, mas agora também produz
código de saída 2. O agregador global conserva a falha de qualquer trecho,
inclusive depois de fechar journals parciais que terminaram sem novos erros.

O painel imprime COM FALHAS e o estado por lote inclui estado/codigo_saida.
ESTADO-PROCESSAMENTO-GLOBAL.json preserva o resultado global da execução.
O BAT existente já propaga o código de saída e informa que os resultados
salvos permanecem preservados. Sucesso desta execução não certifica todos
os históricos nem publicação no banco.

Banco: processamento continua local, sem escritor ativo; envio e publicação
têm estados separados. Fórmula, ordem e selo do pacote não foram alterados.

Quatorze testes de prioridade/processamento passaram, incluindo falha de
cálculo com arquivo persistido e propagação da falha após fechamento dos
journals. OperacaoLocalJson.exe recompilado em 12/09 às 23:05, 22.060.693 bytes.
Instalação e execução na Máquina 2 ainda fazem parte da entrega integral.
