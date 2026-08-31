# Matriz ativa de entradas do Otimizador — V3

Data: 31/08/2026. Esta é a matriz operacional; registros anteriores V1/V2 são
histórico de auditoria. A migração altera somente endereço e identidade de entrada.
Fórmula, pesos, ordem, moldes e publicação não fazem parte desta troca.

| Slot consumido | Fonte antiga que existia | Fonte nova ativa / relação física | Chave canônica | Consumidor | Gate e estado |
| --- | --- | --- | --- | --- | --- |
| identidade e escalares da carta | carta_do_motor / projeções locais | clube_novo.carta_jogo por public.otimizador_carta_v3 | card_id | fonte_unica, roda_lote, serviço | V3 falha fechada se o contrato não for otimizador_entradas_v3 |
| 26 atributos | JSON/colunas projetadas | carta_atributo_jogo -> atributo_jogo -> atributo_ordem_otimizador | card_id + codigo_atributo -> indice_otimizador | equacao/motor | 26 relações aptas obrigatórias |
| 12 medidas de corpo | corpo embutido/arquivo | carta_corpo_jogo -> corpo_ordem | card_id + codigo_corpo -> pos | motor | 12 relações usadas pelo motor obrigatórias |
| pé dominante, uso e precisão | projeção antiga | carta_pe_jogo -> pe | card_id + chave composta campo/valor | motor | 3 relações canônicas obrigatórias |
| posição principal e aptidões | código/rótulo de posição | carta_posicao_principal_jogo e carta_posicao_jogo -> posicao_jogo | card_id + posicao_id | fila, motor, UI | IDs; posicao_id 0 é Goleiro canônico, não erro |
| funções/moldes | funcao_codigo/nome legado | funcao_sistema + otimizador_molde | funcao_id + codigo_atributo | regua/motor | 19 funções x 26 entradas; pesos/alvos preservados |
| relação função -> posição na geração de linhas | funcao_sistema.posicoes e codigo_pt textual | otimizador_funcao_posicao -> FKs para funcao_sistema e posicao_jogo | funcao_id + posicao_id | três fábricas de fila | V18: 30 pares, 19 funções, zero ambiguidade; rótulos não participam |
| estilos de jogo e IA | campos/nomes projetados | carta_playstyle_jogo -> playstyle; carta_estilo_ia_jogo -> estilo_ia | card_id + IDs/bits físicos | motor | 2 playstyles; IA por bit |
| habilidades fixas | chaves/nome legado | carta_habilidade_jogo -> habilidade_jogo | card_id + skill_id | motor | sem rótulo; habilidade bloqueada fecha a carta |
| pool de habilidades adicionáveis | pool legado por carta/função | public.otimizador_pool_habilidades_v3 sobre habilidade_jogo, carta_habilidade_jogo e habilidade_funcao_bloqueio_otimizador | card_id + funcao_id + skill_id | Otimizador e serviço | somente IDs; cartão/função devem passar no gate |
| Ímpetos físicos equipados | JSON/efeitos embutidos | carta_impeto_jogo -> impeto_atributo_jogo -> atributo_ordem_otimizador | card_id + slot + codigo_impeto | worker | fixo materializado; condicional somente por código + nível físico selado |
| condições de Ímpeto na partida | inferência por rótulo | não há consumidor de condição de partida | não aplicável | nenhum | continua desligado; o Otimizador não assume condição ativa |
| nacionalidade, clube, liga e tipo | IDs/textos projetados | FKs de carta_jogo para nacionalidade_jogo, clube_jogo, liga_jogo e tipo_carta_jogo | códigos físicos/compostos | gate de carta | ausência física legítima não é inventada; chave não nula sem catálogo apto bloqueia |
| técnicos e boosts | tecnicos.json/tabelas antigas | tecnico_jogo, tecnico_estilo_jogo e tecnico_atributo_jogo via regua_v2 | tecnico_id, codigo_estilo, indice_otimizador | equacao/motor | IDs/números; sem nome como chave |
| texto/nome de carta, função, posição, técnico e habilidade | lógica de cálculo por nome | otimizador_catalogos_apresentacao_v1 e otimizador_carta_apresentacao_v1 | ID já resolvido | interface | apresentação depois do cálculo; renomear não muda vínculo |
| criação de linhas de teste | clube.fila / fila_do_motor | build_linha_card pelas fábricas V3 | lote_id + card_id + funcao_id + posicao_id + níveis | fila_comparacao_legado_50 | teste/não publicado, selo de fórmula/contrato/carta |
| resultado vencedor | public.gravar_build -> clube.build | build_otimizador por concluir_linha_teste_v2 | linha_id e snapshots selados | worker/UI | resultado real persistido; sem publicação/Bonificador |
| comparação histórica | clube.build / tabela de builds | clube.build_arquivo_2608 apenas leitura | card_id + código legado traduzido de função | comparador V14 | referência isolada; não é entrada/destino do motor |
| auditoria de paridade | cartas_do_motor somente como referência | otimizador_cartas_v3 | card_id + IDs físicos | auditar_entradas_v1.py | comparação somente leitura; `--todos-da-fila` antigo foi revogado, sem fallback |

## Portas deliberadamente fechadas

- service_role, anon e authenticated não executam otimizador_proxima_fila_v1,
  gravar_build, fila_do_motor, cartas_da_fila, estado_da_fila, proxima_da_fila,
  otimizador_peso_ordem_v1, peso_da_ordem ou pool_da_funcao(text,text);
- fonte_unica.proxima_fila(), fonte_unica.gravar() e peso_da_ordem() encerram com
  erro explícito antes de qualquer RPC histórica;
- o corpo antigo de execução direta de roda_lote_v6.py permanece histórico e não é
  alcançável pelo main oficial; se for chamado indiretamente, a gravação histórica e
  a permissão do banco também falham fechadas.

## Prova e recuperação

V16–V20 têm SQL e rollback separados no mesmo diretório. A auditoria pós-migração
verifica contrato da carta, cardinalidades, gates, ACL, relação função/posição e
resultado persistido. O lote V2 concluído 18690c93-4bb4-4b86-827a-f472fc92cc68
é uma fotografia de comparação; não é reaberto nem usado como fallback.
