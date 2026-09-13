> Substituído para operação na máquina 2 pelo modelo FILA-LOCAL-MAQUINA-2.md: baixar fila, processar offline e enviar JSONs em lotes por botão separado.

# Corretor de altura e IA — máquina dedicada

Copie esta pasta OPERACAO-ALTURA-IA-V13 para dentro de 2-MOTORES/BONIFICADOR no espelho da máquina dedicada.
Abra ABRIR-CORRETOR-ALTURA-IA.bat. Não é necessário instalar Python ou abrir o Codex.
O programa usa o config.txt já existente em 2-MOTORES. Não substitua esse arquivo.
Mantenha o Bonificador completo parado durante esta correção seletiva.

O aplicativo consulta o progresso no banco e continua automaticamente, incluindo o que foi feito na máquina 1.
Corrige altura e IA juntas, preservando os demais bônus, atributos e resultados do Otimizador.
IA: quantidade de estilos distintos × 0,1, limitada a 0,5.
Altura: regra aprovada para as sete funções; demais funções zero; demais componentes físicos inalterados.
Cada publicação já recebe a normalização por amplitude vigente.

Para desligar: clique Encerrar no painel e espere aparecer Encerrado com segurança. Depois pode desligar o computador.
Ao abrir novamente, os resultados confirmados não são repetidos. Uma interrupção de energia também não apaga transações já confirmadas.
Não copie ESTADO-LOCAL entre máquinas. O banco é a autoridade da retomada.

Correção de desempenho instalada no banco em 10/09: conferência direta da linha publicada, evitando calcular o ranking inteiro por resultado.
Medição após a correção: 100 linhas em aproximadamente 6 segundos; não é garantia de duração total.

Validação: 1.808 sucessores conferidos, zero divergências nos componentes físicos não-altura e bônus comparados. SQL: SQL/READBACK-PONTUAL.sql.
