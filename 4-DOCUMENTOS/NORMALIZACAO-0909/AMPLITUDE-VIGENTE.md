# Regra vigente — 10/09/2026
Substitui as curvas por função de 09/09, preservadas como histórico.
Nota final = 100 + 50 × pontuação bruta / amplitude + bônus integrais.
Amplitude = máximo teórico − mínimo teórico; limites congelados do comparativo aprovado.
Zero no motor vale 100. Cada 2% da amplitude vale 1 ponto. Não é imposto teto 110.
Não se altera o cálculo do Otimizador, suas etapas, atributos, escolhas ou resultados.
Os limites são teóricos; não implicam uma carta legal capaz de atingir todos os extremos.
Implementação: normalizar_motor_v3, normalizar_publicacao_v3 e finalização automática por linha.
Editor usa a mesma normalizar_motor_v3. Executor externo em 2-MOTORES/BONIFICADOR/OPERACAO-NORMALIZACAO-AMPLITUDE.
Histórico: normalizacao_publicacao_historico_v3. Retomada idempotente e readback transacional.
Altura e IA são corrigidas em operação separada; demais bônus permanecem integrais.
