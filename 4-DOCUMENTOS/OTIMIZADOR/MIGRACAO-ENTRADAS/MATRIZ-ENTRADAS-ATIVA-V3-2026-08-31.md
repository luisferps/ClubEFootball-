# Matriz ativa de entradas do Otimizador — V3

Data: 31/08/2026. Esta é a matriz operacional exclusiva de `clube_novo`.
Fórmula, pesos, ordem, moldes e publicação não fazem parte desta troca.

| Slot consumido | Fonte/relação V3 física | Chave canônica | Consumidor | Gate e estado |
| --- | --- | --- | --- | --- |
| identidade e escalares da carta | clube_novo.carta_jogo por public.otimizador_carta_v3 | card_id | fonte_unica, roda_lote, serviço | falha fechada se o contrato não for otimizador_entradas_v3 |
| 26 atributos | carta_atributo_jogo -> atributo_jogo -> atributo_ordem_otimizador | card_id + codigo_atributo -> indice_otimizador | equacao/motor | 26 relações aptas obrigatórias |
| 12 medidas de corpo | carta_corpo_jogo -> corpo_ordem | card_id + codigo_corpo -> pos | motor | 12 relações usadas pelo motor obrigatórias |
| pé dominante, uso e precisão | carta_pe_jogo -> pe | card_id + chave composta campo/valor | motor | 3 relações canônicas obrigatórias |
| posição principal e aptidões | carta_posicao_principal_jogo e carta_posicao_jogo -> posicao_jogo | card_id + posicao_id | fila futura, motor, UI | IDs; posicao_id 0 é Goleiro canônico, não erro |
| funções/moldes | funcao_sistema + otimizador_molde | funcao_id + codigo_atributo | regua/motor | 19 funções x 26 entradas; pesos/alvos preservados |
| relação função -> posição | otimizador_funcao_posicao -> FKs para funcao_sistema e posicao_jogo | funcao_id + posicao_id | futura fábrica de fila | V18: 30 pares, 19 funções, zero ambiguidade; rótulos não participam |
| estilos de jogo e IA | carta_playstyle_jogo -> playstyle; carta_estilo_ia_jogo -> estilo_ia | card_id + IDs/bits físicos | motor | 2 playstyles; IA por bit |
| habilidades fixas | carta_habilidade_jogo -> habilidade_jogo | card_id + skill_id | motor | sem rótulo; habilidade bloqueada fecha a carta |
| pool de habilidades adicionáveis | public.otimizador_pool_habilidades_v3 sobre habilidade_jogo, carta_habilidade_jogo e habilidade_funcao_bloqueio_otimizador | card_id + funcao_id + skill_id | Otimizador e serviço | somente IDs; cartão/função devem passar no gate |
| Ímpetos físicos equipados | carta_impeto_jogo -> impeto_atributo_jogo -> atributo_ordem_otimizador | card_id + slot + codigo_impeto | worker | fixo materializado; condicional somente por código + nível físico selado |
| condições de Ímpeto na partida | não há consumidor de condição de partida | não aplicável | nenhum | continua desligado; o Otimizador não assume condição ativa |
| nacionalidade, clube, liga e tipo | FKs de carta_jogo para nacionalidade_jogo, clube_jogo, liga_jogo e tipo_carta_jogo | códigos físicos/compostos | gate de carta | ausência física legítima não é inventada; chave não nula sem catálogo apto bloqueia |
| técnicos e boosts | tecnico_jogo, tecnico_estilo_jogo e tecnico_atributo_jogo via regua_v2 | tecnico_id, codigo_estilo, indice_otimizador | equacao/motor | IDs/números; sem nome como chave |
| texto/nome de carta, função, posição, técnico e habilidade | otimizador_catalogos_apresentacao_v1 e otimizador_carta_apresentacao_v1 | ID já resolvido | interface | apresentação depois do cálculo; renomear não muda vínculo |
| fila produtiva, snapshots e resultados do Otimizador | contrato V3 preparado: lote/snapshot/linha/evento em clube_novo + build_linha_card/build_otimizador | lote_id + card_id + funcao_id + posicao_id + selos de carta/régua/fórmula | worker local V3, depois Bonificador separado | artefato local pronto, ainda não aplicado; sem fallback, sem publicação e com Ímpetos condicionais desligados |
| auditoria de entradas | otimizador_cartas_v3 | card_id + IDs físicos | auditar_entradas_v1.py | somente leitura; valida versão, gate, cardinalidade e fingerprint interno |

## Portas deliberadamente fechadas

- service_role, anon e authenticated não executam otimizador_proxima_fila_v1,
  gravar_build, fila_do_motor, cartas_da_fila, estado_da_fila, proxima_da_fila,
  otimizador_peso_ordem_v1, peso_da_ordem ou pool_da_funcao(text,text);
- fonte_unica.proxima_fila(), fonte_unica.gravar() e peso_da_ordem() encerram com
  erro explícito antes de qualquer RPC histórica;
- o corpo antigo de execução direta de roda_lote_v6.py permanece histórico e não é
  alcançável pelo main oficial; se for chamado indiretamente, a gravação histórica e
  a permissão do banco também falham fechadas.

## Encerramento da frente de legado — V22

Nenhum arquivo ativo consulta fonte, fila, build ou contrato histórico. A entrada
`fila_comparacao_legado_50.py` e seu lançador agora encerram imediatamente sem ler
arquivo, chamar RPC ou iniciar worker. A interface local não importa esse arquivo,
não possui RPC de fila V2 na lista permitida e mostra honestamente que não existe
fila V3 autorizada. Os artefatos já preservados em recuperação são somente prova
histórica e não fazem parte do fluxo operacional.

## Prova e recuperação

V16–V20 têm SQL e rollback separados no mesmo diretório. A auditoria pós-migração
verifica contrato da carta, cardinalidades, gates, ACL, relação função/posição e
resultado persistido. O lote V2 concluído 18690c93-4bb4-4b86-827a-f472fc92cc68
é uma fotografia de comparação; não é reaberto nem usado como fallback.

## Preparação V23 — fila produtiva completa, não aplicada

`FILA-PRODUCAO-V3/MIGRACAO-FILA-PRODUCAO-V3.sql` materializa a linha acima sem
trocar qualquer entrada de cálculo: snapshots vêm de `otimizador_carta_v3` e
`otimizador_regua_v2`, relações de função/posição vêm de FKs canônicas e o
resultado preserva os selos antes de entrar em `build_otimizador`. A migração
continua **não aplicada**; portanto a interface V23 não pode criar nem executar
lote até existir readback físico do contrato.
