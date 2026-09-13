# Fila principal v6 — Máquina 2

Lote: `39da8ff4-7a4a-4ec7-8641-e81b5677ad4c`.

1. Abra `BAIXAR-FILA-PRINCIPAL.bat` e aguarde a confirmação.
2. Abra `PROCESSAR-FILA-PRINCIPAL.bat`: usa quatro processos de cálculo.
3. Abra `ENVIAR-FILA-PRINCIPAL.bat` para enviar os JSONs prontos.

A ordem é: cartas novas; demais cartas com orçamento; demais sem orçamento.
Dentro de cada grupo, overall do maior para o menor. Overall ausente fica no
final do seu grupo. O próximo grupo só começa quando o atual terminar.

Os trabalhadores calculam; um único processo grava os resultados na ordem
da fila. O envio continua separado. Ctrl+C interrompe; os resultados já
gravados ficam preservados e são reconhecidos na retomada.

Não abra quatro cópias do aplicativo: uma instância já coordena os quatro
processos. A trava impede outra instância de gravar na mesma fila.

Cartas sem prova coerente de nível e orçamento não entram no pacote. Ausência
de prova não significa orçamento zero. A fila antiga 1209 foi aposentada.
