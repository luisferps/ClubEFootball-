## Atualização de 10/09/2026

IA de 0,5 aprovada e política V13 instalada nos writers; correção seletiva em execução. Leia [EXECUTOR-ALTURA-IA-V13.md](EXECUTOR-ALTURA-IA-V13.md). O estado de preparação abaixo é histórico.

# Altura independente — decisão aprovada em 09/09/2026

## Estado desta etapa

Separação estrutural implementada e regra cadastrada como preparada em
clube_novo.bonificador_altura_politica_v1. Nenhuma nota oficial foi alterada.
O runtime V12 usa a separação em modo neutro; não anuncia a nova regra como ativa.
O recálculo seletivo e a ativação dos contratos de escrita são a etapa seguinte.
Não copiar esta etapa como se já ativasse a política nova na máquina 2.

## Regra aprovada

Altura conta com peso 5 nas funções 1,4,5,6,17,18,19: centroavante fixo,
goleiro defensivo/ofensivo, lateral defensivo, volante de contenção e zagueiros.
Nas outras 12 funções, altura vale zero, sem prêmio nem desconto.
Nas sete ativas, a direção é +1: maior altura é favorecida. Corrigir as antigas
inversões de goleiro defensivo e lateral defensivo. Não modificar os cortes.

| Faixa | Goleiros | Demais cinco funções ativas | Nível |
|---|---|---|---:|
| 1 | até 179 cm | até 171 cm | -2 |
| 2 | 180–184 cm | 172–178 cm | -1 |
| 3 | 185–189 cm | 179–184 cm | 0 |
| 4 | 190–194 cm | 185–191 cm | +1 |
| 5 | 195 cm ou mais | 192 cm ou mais | +2 |

## Independência e preservação

Cada uma das outras onze parcelas mantém exatamente seus pontos atuais.
Não recalcular o denominador usando o novo conjunto de medidas ativas.
A base original foi congelada dentro da política no banco para rastreabilidade.
Separar a altura sem aplicar a regra nova não altera nenhum número.
Aplicar a regra muda apenas detalhe.altura e os totais derivados.
Os resíduos existentes de arredondamento nas outras parcelas são preservados.
O físico mantém precisão suficiente para fechar exatamente o detalhe; o bônus
total e a exibição seguem a precisão contratual. Não jogar resíduos em outra medida.

IA no comparativo: min(quantidade,5)*0,1, teto 0,5. A confirmação sobre incluí-la
na implantação atual foi solicitada; nenhuma alteração de IA foi aplicada.
Normalização por amplitude permanece comparativo; a normalização oficial não muda.

## Auditoria no banco

192.635 linhas vigentes/candidatas em staging, sem antecessores de orçamento.
118.479 mudam a parcela da altura; 74.156 não mudam.
Zero divergências na soma física após separação neutra.
Zero modificações das outras onze parcelas ao simular a política aprovada.
São contagens da consulta desta etapa, não prova de migração concluída.

## Como recalcular somente altura

1. Capturar por linha o ID e selo do Bonificador, carta, Otimizador e publicação.
2. Usar as doze parcelas já gravadas: manter onze e trocar somente a altura.
3. Recalcular total físico, total de bônus, campos derivados e selos compatíveis.
4. Criar resultado sucessor com histórico; nunca sobrescrever o resultado-base.
5. Atualizar referência e publicação na mesma transação, validando os selos antes.
6. Reutilizar finalizador oficial; não rerodar Otimizador nem reorganizar lotes.
7. Recusar referência que tenha mudado; repetir chamada sem duplicar correção.
8. Conferir pelo banco que somente altura e derivados mudaram e nenhuma linha ficou fora.

A rotina de escrita precisa de versão/contrato próprios. O helper instalado é puro
e NÃO é um executor de migração. Não usar UPDATE direto de bonus_total.

## Arquivos

- 2-MOTORES/BONIFICADOR/altura_independente.py: cálculo puro.
- motor_bonus.py: integração neutra na saída física oficial.
- windows-app/COMPILAR-COMPONENTE.ps1: empacota o módulo novo.
- SQL/PREPARAR-ALTURA-INDEPENDENTE.sql: política e calculadora no banco.
- TESTES/testar_altura_independente.py: independência, caso Ronaldinho e entradas inválidas.
