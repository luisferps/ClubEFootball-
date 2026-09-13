# Bonificador — lote integral atual

Aplicativo: `2-MOTORES/BONIFICADOR/Bonificador ClubEfootball.exe`, versão
2.0.30. A primeira aba informa o lote da régua vigente e suas contagens.

1. Depois de preparar e selar a fila integral em pausado, use
   **REAPROVEITAR CONFORMES**. O banco confere entradas e componentes atuais,
   procura o sucessor válido e cria um resultado próprio por linha destino.
   A versão nominal antiga não determina recálculo.
2. Quando a conferência terminar sem impedimentos, use **CALCULAR EXCEÇÕES**.
   Somente as linhas classificadas para cálculo nesse lote são enviadas ao motor.
3. **PARAR APÓS A FATIA** preserva o trabalho confirmado para retomada.

O reaproveitamento grava auditoria por linha e mantém intacto o resultado
original. Mudanças relevantes nas entradas impedem reutilização. Técnico e
molde pertencem ao Otimizador; não mudam a fórmula dos bônus.

Sem lote preparado, com conferência pendente ou com impedimentos, o cálculo
fica bloqueado. Falha de consulta desabilita as ações. Fila vazia não declara
conclusão se o banco ainda informa exceções ou impedimentos.

## Evidência em 13/09

Banco e RPCs implantados. Ensaios de duas fatias reaproveitaram seis linhas
e foram revertidos; a consulta de cálculo devolveu apenas a linha do lote
temporário, também revertido. Cinco testes locais passaram. Executável
compilado e tela/conexão conferidas. Nenhuma rodada produtiva iniciada:
a fila integral v6 ainda precisa ser criada e preparada.
