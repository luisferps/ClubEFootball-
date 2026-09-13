# Orçamento ainda não divulgado: regra diária

A regra é geral, sem lista fixa de IDs. Substitui o tratamento pontual anterior.
Cartas excluídas ficam fora da operação e das pendências.

O Extrator eFHUB reconhece resposta identificada com levelCap inteiro zero
como aguardando_orcamento. Não cria evidência de nível, não grava orçamento
zero, não conta como falha e continua o lote. Identidade divergente, valores
malformados e falhas HTTP continuam erros reais.

O banco registra a tentativa com prova e horário. O planejador não seleciona
novamente a mesma espera no mesmo dia (America/Sao_Paulo); a próxima execução
diária volta a consultar. Isso não agenda execução nem abre o aplicativo sozinho:
a regra é executada quando o operador roda a coleta normal.

A fonte carta_orcamento_pendente_automatico_v1 deriva o aviso do cadastro e da
prova corrente. A Ficha usa essa fonte, não a tabela histórica com dez IDs.
Nível zero/ausente ou estimado ainda sem prova e respostas explícitas aguardando
recebem o aviso. Nível 1 comprovado com orçamento 0 continua válido.
Dados conflitantes e falta de prova de um nível 1 informado não são classificados
cegamente como orçamento não divulgado. Valores manuais efetivos são respeitados.

Quando uma coleta aplica nível e orçamento válidos, o aviso desaparece e a
carta volta automaticamente à elegibilidade normal do Otimizador. A preparação
ou revisão da fila utiliza os fluxos existentes; pacotes selados já rodando não
são modificados por esta regra. No modo de extração integral, a preparação da
fila continua sendo etapa separada, conforme contrato do aplicativo.

O executável de níveis inicia executor/desktop_worker.py da pasta oficial;
este importa efhub_levels.py. A mudança no módulo é utilizada pelo launcher
existente, sem segunda versão de aplicativo. Relatório HTML e eventos incluem
contagem de orçamentos aguardando divulgação separada das falhas.

Validação em 13/09/2026:
- Nove casos do leitor: zero, nível 1, evolutivo, tipos inválidos e identidade.
- Ensaio transacional do planejador, writer e finalizador: zero falhas e nenhuma
  evidência inventada para resposta levelCap=0; revertido integralmente.
- Ensaio de transição: evidência válida remove aviso e devolve elegibilidade;
  rollback restaurou a condição anterior. Nenhum orçamento de teste persistiu.
- Fonte automática identifica atualmente dez cartas, sem IDs no código da regra.

SQL aplicado: SQL-ORCAMENTO-FLUXO-DIARIO.sql.
