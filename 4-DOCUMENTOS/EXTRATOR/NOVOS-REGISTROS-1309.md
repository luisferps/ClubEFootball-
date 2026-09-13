# Novos registros — correções de 13/09/2026

A atualização passou a trazer cartas, técnicos e ímpetos que não existiam no banco. O escritor genérico já preservava campos fora do comando em registros existentes, mas isso não fornece metadados obrigatórios para inserções novas.

## Banco e código

- `impetos_v4610.py`: origem da condição recebe CPK/hash do contrato atual; regra semântica exige consenso entre referências canônicas do mesmo tipo/critério. Não herda índice/hash físico de outro ímpeto. Tipo e comportamento comprovados acompanham o catálogo para permitir os vínculos de slot.
- `tecnicos_v4610.py`: fonte, arquivo, CPK, hash e contratos de apresentação acompanham a comparação. O hash precisa coincidir com Coach.bin no contrato. O banco preenche a data de carga de uma apresentação nova; não fornece dados físicos ausentes.
- A ordem declarada dos escritores foi recalculada a partir das FKs, conservando dimensões da carta antes dos seus campos básicos. Catálogos entram antes de condições, técnicos antes de proficiências/boosts e cartas antes dos vínculos.
- As proteções de `valor_do_dono` permanecem ativas. A conferência do escritor considera a decisão manual efetiva e mantém o envelope físico original.

## Validação

Teste integral do pacote de 23.814 envelopes: todos os grupos gravados e relidos, restrições diferidas conferidas, transação inteira revertida. Esse teste não é importação concluída. Cinco testes locais cobrem consenso, regra ambígua, tipo desconhecido e origem atual obrigatória.

Nova varredura real iniciada às 00:26:02 pelo aplicativo. A confirmação final da aplicação ainda está pendente. Pacotes anteriores com carga parcial permanecem preservados para auditoria.

## Tela

Seleção compacta já conferida no EXE 5.4.0.6. Avisos de falha foram encurtados no fonte: os detalhes integrais ficam em ABRIR LOG, e a mensagem de carga parcial continua explícita. A compilação dessa última alteração visual aguarda o fim da varredura em execução.
