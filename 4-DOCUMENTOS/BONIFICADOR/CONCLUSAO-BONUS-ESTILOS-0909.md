# Bônus de estilo — correção concluída

Conferência final em 2026-09-09T08:13:50.106412+00:00.

- **67.795 resultados corrigidos e concluídos.**
- **7.455 publicações atualizadas e concluídas.**
- **Zero publicações pendentes e zero erros nesta operação de estilos.**
- Nove publicações finais conferidas na tabela ativa e no contrato `public.site_novo_ficha_v2`, com as mesmas notas.
- Os outros bônus, os resultados anteriores do Otimizador e a ordem das filas foram preservados.

O erro de encerramento era um UPDATE sem filtro na rotina do executor. A migração `20260909081108_corrigir_filtro_encerramento_executor_estilos_v12` incluiu o identificador da execução no WHERE. A correção consta do SQL oficial; não houve mudança de fórmula ou do executável.

Três linhas foram finalizadas pelo executor oficial. Nas outras seis, a revisão de habilidades já havia colocado o Otimizador em espera. Foi atualizada a publicação preservada com o bônus correto, usando o mesmo cálculo e formatador do finalizador oficial, sem restaurar o ponteiro antigo do Otimizador nem alterar sua fila. Os 26 atributos, barras, ímpetos, habilidades e arows da publicação foram conferidos. A linha, o registro público, a projeção incremental e seus selos foram atualizados conjuntamente.

Os estados anteriores foram arquivados em `clube_novo.build_finalizacao_evento_v1`, evento `arquivo_antes_fechamento_manual_estilos_v12`. A autorização e a conclusão manual estão em `clube_novo.correcao_estilos_execucao_v12.auditoria.fechamento_manual`.

| Linha | Bônus de estilo | Nota publicada | Estado da correção |
|---:|---:|---:|---|
| 403298 | 1,5 | 101.5878657889148439 | Concluída |
| 403305 | 1,5 | 100.9998523010655180 | Concluída |
| 403306 | 1,5 | 103.4775307834804402 | Concluída |
| 403307 | 1,5 | 97.9917391771404018 | Concluída |
| 403308 | 1,5 | 98.9724915782706525 | Concluída |
| 403309 | 1,5 | 103.2341917331095258 | Concluída |
| 403310 | 1,5 | 101.2472891696750903 | Concluída |
| 403323 | 1 | 101.0717037347880822 | Concluída |
| 403328 | 1 | 104.0352741114523914 | Concluída |

O painel local foi atualizado pela própria API do aplicativo, que consultou o encerramento no banco e passou a exibir “Correção concluída e confirmada pelo banco”.

A correção seletiva de estilos está encerrada. A execução geral do Bonificador é uma operação separada, com a liberação e os lotes controlados pelo início explícito do operador; não foi iniciada aqui. As seis linhas citadas continuam normalmente na revisão de habilidades do Otimizador, sem pendência de publicação dos bônus de estilo.

A atualização do pacote do Otimizador na Máquina 2 foi confirmada pelo operador: revisão `5ff9a0bc25cf408982348990cb4c800b`, com ordem preservada e nenhum processador/enviador iniciado pelo instalador. Nenhum conteúdo foi enviado ao GitHub ou Netlify.
