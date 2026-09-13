# Retomada dos motores — reparos de 09/09/2026

O teste inicial de preparação do Bonificador não cobria a leitura HTTP da carta. Na execução da Máquina 2, a linha 488143 falhou com 403: faltava SELECT das colunas id_jogo e nome_pt do catálogo clube_novo.playstyle para service_role, usadas pela RPC invoker bonificador_carta_v3.

Migração corrigir_leitura_catalogo_estilos_bonificador_v12: somente SELECT dessas duas colunas ao service_role. Acesso integral à tabela não concedido; anon/authenticated seguem sem EXECUTE nessa RPC. Advisors sem alerta relacionado à alteração.

Readback HTTP com a configuração oficial retornou 200 e carta apta. O motor calculou corpo=0,25, pé ruim=0,14, estilo=1,0, IA=0 e total=1,39, faltou=[]. A preparação, reserva e gravação da mesma linha passaram em transação revertida, com readback ok. Nenhum bônus desse teste foi persistido. Em seguida, apenas a falha 488143 foi arquivada e recuperada: lote pausado, 14.107 pendentes, zero falhas/processando, mesma prioridade. Auditoria no campo recuperacao_403_retomada da execução estilos-funcao-20260909-v1.

O código oficial do Bonificador passa a retornar código 2 quando a rodada tem bloqueados ou o lote continua pendente/falho sem reserva. Não mostra PRONTO nem SEM PENDÊNCIAS nessas situações. Os testes dos três estados passaram; os seis testes V12 incluindo 25 casos manuais também passaram. EXE/componente recompilados e manifesto/pacote completo atualizados.

O Otimizador teve corrigida a validação das prioridades já sem pendências. Passaram 36 testes e execução do EXE em espelho isolado. A seleção e a ordem permanecem intactas. Ver OTIMIZADOR/HABILIDADES-0909/REPARO-PRIORITARIOS-CONCLUIDOS.md.

Entrega única: REPARO-MOTORES-V12, seis arquivos, copiável para 2-MOTORES. Executar APLICAR.cmd com os motores parados. Instalador testado, faz backup, preserva fila/resultados/configuração, não renova fotografias nem inicia workers. Inclui o reparo incremental do Otimizador. Os BATs anteriores permanecem iguais. A instalação na Máquina 2 ainda deve ser confirmada pelo operador.
