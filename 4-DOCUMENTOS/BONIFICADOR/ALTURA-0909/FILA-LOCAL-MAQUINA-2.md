# Altura e IA — fila local e enviador separado

## Instalação na máquina 2
Copie a pasta ALTURA-IA-FILA-LOCAL para dentro de 2-MOTORES/BONIFICADOR.
Este é o pacote NOVO. Substitui para esta operação o anterior OPERACAO-ALTURA-IA-V13, que deve ficar parado.
Não substitui o Bonificador completo nem os botões do Otimizador. Não sobrescreve configuração, resultados ou recibos anteriores.
Usa o config.txt já existente em 2-MOTORES. Não exige Python instalado.

## Rodar
1. Abra PROCESSAR-FILA-ALTURA-IA.bat: baixa a fila pendente em páginas, salva em FILA e calcula no computador, gravando lotes de até 100 linhas em RESULTADOS.
2. Abra ENVIAR-RESULTADOS-ALTURA-IA.bat ao mesmo tempo: espera os JSONs, envia lotes de até 100 e grava RECIBOS.
O download precisa de internet. Terminada a fotografia, o cálculo é offline. O cálculo não grava no banco.
O enviador usa o resultado local; o banco valida a conta, identidade e versão antes de gravar e publicar com amplitude.
Mantenha o Bonificador completo e o corretor antigo parados durante esta operação.

## Retomar ou desligar
Ctrl+C em cada janela interrompe com os arquivos confirmados preservados. Depois pode desligar.
Abra os mesmos botões para retomar. Não apague FILA, RESULTADOS, RECIBOS ou o manifesto.
JSONs sem recibo são reenviados com segurança: o banco reconhece o que já confirmou e não duplica.
Linhas já corrigidas pela máquina 1 não entram novamente na fila baixada.
As linhas cujo Otimizador ainda não está completo recebem bônus corrigidos, mas aguardam publicação. O recibo distingue esse estado de concluida.

## Regras e validação
IA = min(quantidade de estilos distintos, 5) × 0,1.
Altura conta nas sete funções aprovadas; demais funções zero. Os outros 11 componentes físicos permanecem iguais.
Demais bônus e todos os atributos, etapas e escolhas do Otimizador são preservados.
Testados 10 resultados locais publicados e 10 aguardando atributos; reenvio do lote publicado corrigiu zero linhas adicionais. Testes no banco com rollback.
Readback pontual evita recalcular o ranking inteiro por linha. Sem consumo de IA ou tokens na operação.
