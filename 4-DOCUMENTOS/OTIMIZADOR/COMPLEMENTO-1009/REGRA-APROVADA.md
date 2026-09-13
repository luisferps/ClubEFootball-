## Encerramento conferido no banco — 10/09/2026

O operador confirmou instalacao e execucao na maquina 2. Fotografia: 751
linhas; 560 corrigidas e 191 sem candidata elegivel. O enviador confirmou as
oito paginas. Readback em clube_novo: 560 recibos, 560 vinculadas ao resultado
novo, 560 selos e vetores de atributos corretos, 560 cadeias/arows, notas e
listas de adicionais corretas, 560 publicacoes ativas.

524 aparecem no contrato exibivel. As outras 36 sao goleiros na funcao de
estilo oposto: 20 recuados e 16 avancados, todos sem o playstyle requerido
pela respectiva funcao. O filtro ja aprovado de nao misturar goleiros oculta
essas builds. Nao e falha de envio ou finalizacao; nao remover o filtro.

Universo conferido de linhas validas concluidas que aceitam adicionais: 7.754.
Antes do complemento, 7.003 ja tinham cinco adicionais e 751 tinham vagas.
Nao confundir esta operacao de preenchimento com auditoria/troca de vagas
ocupadas. Varane36564 devolve Carrinho e Passe aereo baixo como complementares.

Rodada encerrada. Pode fechar os dois programas de complemento e retomar os
botoes habituais do otimizador/enviador. O reparo posterior de busca de config
ficou preparado nos arquivos oficiais; sua instalacao na maquina2 nao foi
confirmada e nao foi necessaria para esta rodada, que terminou com sucesso.

---

Registro anterior preservado como historico:

# Complemento de habilidades — aprovado em 10/09/2026

Estado: codigo oficial e contratos no banco implementados; frontend publicado.
Instalacao na maquina 2 e execucao em massa dependem do operador; nao estao concluidas.

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
   parada). No molde V5 atual, 69 atende funcoes 1/2/3; 48 atende 1/2/3/9/14.
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
8. Ordem antiga da fila, historicos e recibos preservados. Arquivos oficiais
   atualizados na maquina 1; pacote com backup para maquina 2. Nao iniciar
   processos da maquina 2 nem assumir pausa sem confirmacao.

## Implementacao e operacao

- Snapshot vivo: habilidade_incidencia_snapshot_v14 recalcula apos invalidacao por mudancas nas fontes nativas. Contexto SHA-256 arquivado por complemento_contexto_v14; cache direto nao e fonte garantidamente atual.
- Runtime: complemento_runtime_v14 chama a busca oficial e complementa sua solucao antes do formatador oficial. Adaptadores local e producao ligados. EXE OperacaoLocalJson recompilado.
- Formula da busca permanece a V12, sem mudar os cinco arquivos do nucleo. Versao e SHA-256 do complemento sao separados e viajam no resultado; os writers validam e persistem sua origem.
- Correcao: exportador exclui invalidas, fila pendente do otimizador, revisao de orcamento e cartas nao elegiveis. Recompositor preserva barras, tecnico e impetos; atualiza 26 atributos, cadeia, arows e nota. Writer compara com build_editor.avaliar_v1 e rejeita divergencia ou linha concorrente.
- Resultado anterior e preservado; grava nova build, recibo e tenta finalizacao/publicacao pelos contratos vigentes. Nao inventa bonus nem dispensa seus selos. Reenvio do mesmo resultado e idempotente.
- Tela consulta origem persistida, verde discretamente mais claro, title exatamente Complementar. O editor pessoal continua manual; calculo no banco, sem preenchimento automatico. Ao abrir builds locais, reavalia com o servidor; preservadas as correcoes de altura/IA/normalizacao da tarefa de design.
- Netlify publicado: 6aa262c0f0efb9f3b5bd0576. Quatro arquivos alterados conferidos byte a byte na URL publica; demais arquivos do deploy anterior preservados.

### Maquina 2 — ordem obrigatoria

1. Processador/enviador parados: copiar ATUALIZACAO-COMPLEMENTO-V14 para OTIMIZADOR e executar APLICAR.bat. Instalador verifica hashes e salva backup, sem mexer em filas/config/resultados/recibos.
2. COMPLEMENTO-LOCAL-V14/0-ENVIAR-JSONS-ANTIGOS.bat, com processador parado. Terminar sem erro ANTES de baixar a fila corretiva: JSONs antigos prontos precisam entrar no banco para serem incluidos na fotografia.
3. Abrir 1-CALCULAR-COMPLEMENTOS.bat e 2-ENVIAR-COMPLEMENTOS.bat simultaneamente. Download com cursor, calculo local, paginas ate 100, recibos e retomada.
4. Somente depois de concluir ambos, retomar PROCESSAR-FILA-PRINCIPAL.bat e ENVIAR-FILA-PRINCIPAL.bat na pasta habitual. Novas buscas ja aplicam o complemento.

Nao apagar marcadores/paginas para fingir uma fila nova. Uma nova rodada posterior exige novo diretorio operacional e nova fotografia. Em erro, preservar pasta e mensagem. Nao iniciar nova busca concorrente com esta correcao.

## Validacao

- Nove testes da selecao: corte inclusivo, gêmeas permitidas, nativa duplicada, bloqueios, excecoes por atributos e carta inelegivel.
- Varane, linha 36564: [67] -> [67,60,43], Carrinho e Passe aereo baixo; bruto350.8, editor350.8, nota110.99349512002111. Todos os26 atributos fisicos/internos e cadeia conferidos.
- Centroavante linha34628: [22,19,20] -> [22,19,20,31,27], bruto338.8; importador em lote com paridade do editor aprovado em transacao revertida.
- Carta tipo4 rejeitada pelo writer; runtime restringe complemento aos tipos0/1/5/6 com orcamento positivo.
- Varane: teste transacional de gravacao, segunda chamada idempotente e flags da ficha aprovado, com rollback. Nenhuma build de teste ficou publicada.
- EXE complementar calculou fotografia isolada e retomou sem duplicar resultados. Instalador isolado conferiu hashes e preservou arquivos sentinelas de configuracao/fila/resultados.

A execucao em massa NAO foi feita nesta tarefa: o pacote e para a maquina dedicada. Nao afirmar que todas as builds ja possuem complementares.
