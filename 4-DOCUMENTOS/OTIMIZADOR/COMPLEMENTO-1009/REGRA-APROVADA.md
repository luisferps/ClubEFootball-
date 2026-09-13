# Complemento V14 — regra vigente

Integrado à busca atual. O executor separado atende correções de resultados prontos. [Operação](../../MANUAL-DO-OTIMIZADOR.md). A correção histórica de 560 linhas foi encerrada; ela não mede o progresso da rodada v6.

Esta decisao substitui a proibicao absoluta de preencher vagas sem ganho da V12.
A busca e seu enxugamento continuam preservados; o complemento acontece depois.

1. Ranking vivo por funcao, usando todas as cartas da combinacao de posicao
   principal nativa e estilo de fabrica, sem exigir nota, evolucao ou build rodada.
   Uma carta conta uma vez por funcao. Nao usar aptidao adquirida como posicao nativa.
2. Incidencia = cartas com a habilidade nativa / cartas totais do grupo.
   Corte inclusivo de 10%; ordem decrescente, desempate deterministico por ID.
3. Preservar adicionais vencedoras; preencher apenas vagas livres de cartas que
   aceitam adicionais. Pular somente IDs ja presentes, bloqueadas e vetadas. Ter uma gemea
   presente NAO exclui a candidata: movimentos distintos podem ter utilidade
   propria mesmo com efeitos iguais. Nativas e raras nao sao removidas.
4. Apos o ranking, considerar Super substituto (69) e Especialista em penalti (48)
   como excecoes ao veto global, somente se TODOS os atributos respectivos forem
   indispensaveis (peso 12) ou desejaveis (peso 7) na funcao. Bloqueios por funcao permanecem.
   Super substituto exige talento ofensivo e finalizacao; Especialista exige
   finalizacao (criterio de utilidade, sem alterar seu efeito em cobranca de bola
   parada). As funções elegíveis são derivadas dos pesos do molde vigente; não congelar a lista da versão 5.
5. Recompor todos os atributos, etapas, metadados e nota usando o caminho oficial.
   Nao forcar nota igual: as excecoes podem alterar a pontuacao. Nao refazer busca
   de barras/tecnico/impetos para complementar uma solucao ja valida.
6. A ficha apresenta adicionais com aparencia normal e contador total. Apenas
   o hover das complementares mostra exatamente `Complementar`, sem badge,
   explicacao adicional. Decisao posterior: verde discretamente mais claro,
   mantendo o mesmo formato. Persistir origem por habilidade.
7. Mesmo algoritmo no otimizador e no executor separado de resultados prontos.
   Executor usa fila local, JSONs em lotes, enviador simultaneo e recibos,
   retomada idempotente e comparacao da versao anterior antes de substituir.
8. Preservar históricos e recibos. A entrega atual já incorpora o complemento; não repetir instaladores de rodadas encerradas.

## Implementacao e operacao

- Snapshot vivo: habilidade_incidencia_snapshot_v14 recalcula apos invalidacao por mudancas nas fontes nativas. Contexto SHA-256 arquivado por complemento_contexto_v14; cache direto nao e fonte garantidamente atual.
- Runtime: complemento_runtime_v14 chama a busca oficial e complementa sua solucao antes do formatador oficial. Adaptadores local e producao ligados. EXE OperacaoLocalJson recompilado.
- Formula da busca permanece a V12, sem mudar os cinco arquivos do nucleo. Versao e SHA-256 do complemento sao separados e viajam no resultado; os writers validam e persistem sua origem.
- Correcao: exportador exclui invalidas, fila pendente do otimizador, revisao de orcamento e cartas nao elegiveis. Recompositor preserva barras, tecnico e impetos; atualiza 26 atributos, cadeia, arows e nota. Writer compara com build_editor.avaliar_v1 e rejeita divergencia ou linha concorrente.
- Resultado anterior e preservado; grava nova build, recibo e tenta finalizacao/publicacao pelos contratos vigentes. Nao inventa bonus nem dispensa seus selos. Reenvio do mesmo resultado e idempotente.
- Tela consulta origem persistida, verde discretamente mais claro, title exatamente Complementar. O editor pessoal continua manual; calculo no banco, sem preenchimento automatico. Ao abrir builds locais, reavalia com o servidor; preservadas as correcoes de altura/IA/normalizacao da tarefa de design.
- Netlify publicado: 6aa262c0f0efb9f3b5bd0576. Quatro arquivos alterados conferidos byte a byte na URL publica; demais arquivos do deploy anterior preservados.
