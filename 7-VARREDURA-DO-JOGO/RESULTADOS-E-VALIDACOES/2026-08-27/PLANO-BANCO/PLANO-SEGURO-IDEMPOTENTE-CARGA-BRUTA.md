# Plano seguro e idempotente para aplicar uma carga bruta aprovada

Este plano descreve uma etapa futura. **Nenhuma escrita foi autorizada ou executada em 27/08/2026.**

## Escopo do próximo teste, somente após nova autorização explícita

- destino: `clube_novo.carta_jogo`;
- referência que deve permanecer intocada: `clube.carta_jogo`;
- chave canônica: `card_id` original Konami;
- conjunto: somente itens selecionados em um diff atual, selado e validado;
- fora do lote: todas as tabelas de `clube`, relações normalizadas, catálogos, motores e tela.

## Procedimento

1. Congelar fonte, base anterior, manifesto e SHA-256.
2. Revisar novas, alteradas e possíveis inativas separadamente.
3. Executar o preflight somente leitura do executor local.
4. Bloquear se o manifesto expirou, mudou de hash, já foi usado ou não corresponde à seleção.
5. Bloquear se uma carta nova já existir com conteúdo diferente.
6. Bloquear se os valores `antes` de uma carta alterada não forem mais os do banco.
7. Não aplicar possível inativação enquanto não existir coluna canônica/adaptador aprovado.
8. Em tarefa com autorização explícita, habilitar temporariamente `write_enabled` e o selo de ambiente.
9. Abrir transação `SERIALIZABLE`, adquirir trava do lote e repetir as precondições.
10. Inserir novas por `card_id`; se o mesmo conteúdo já existir, tratar como idempotente e não reescrever.
11. Atualizar cartas existentes somente nos campos listados no diff.
12. Executar readback dentro da transação; qualquer divergência causa rollback total.
13. Confirmar commit e abrir nova conexão somente leitura.
14. Ler todos os `card_id` do lote, comparar os valores aprovados e gerar hash de readback.
15. Gravar manifesto de aplicação com seleção, antes/depois, contagens, hashes e plano de recuperação.
16. Exportar nova fotografia completa somente após o readback; ela vira a próxima base.

## Recuperação

- falha antes do commit: rollback automático;
- falha no readback transacional: rollback automático;
- falha pós-commit: usar `selected_items` e `recovery_plan` do manifesto para construir um diff inverso, revisar e aplicar em nova tarefa autorizada;
- novas cartas não são apagadas automaticamente;
- campos anteriores não são restaurados automaticamente.

## Particionamento se necessário

Se o lote ultrapassar limites de tempo, particionar por hash estável de `card_id`, mantendo o mesmo `execution_id` pai e um manifesto por partição. Cada partição precisa de transação, readback e hash próprios. O conjunto total só é considerado concluído quando todas as partições aprovadas fecharem sem anti-join ou divergência.

## Critério de aceite

- inseridos + já idempotentes = novas selecionadas;
- alterados + já idempotentes = alterações selecionadas;
- zero chaves fora da seleção;
- zero duplicidades;
- zero divergências no readback;
- manifesto permanente e recuperável.
