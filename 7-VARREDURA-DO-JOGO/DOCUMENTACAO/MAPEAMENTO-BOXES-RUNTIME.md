# Mapeamento físico das boxes comerciais

Contrato `boxes-cmd-get-myclub-agentlist-detalhes-v2`, para eFootball 6.0.0.0, SHA-256
`a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4`.
O extrator lê a resposta `CmdGetMyclubAgentlist` já convertida e mantida pelo
jogo. Essa resposta cobre somente as ofertas carregadas na sessão atual; não
recupera boxes históricas. O histórico fixo vem do legado preservado em
`dados/boxes-historicas-legado.json`, copiando somente nome da Box, `card_id`
dos participantes e data `visto` como observação histórica, nunca como data da oferta. `PlayerVariationDetail.bin` descreve a
variação individual da carta e não é fonte de nome, identidade ou composição
comercial de Box.

## Raiz e vetor

`G=[base+0x86c9fc0]`, `A=[G+0x28]`, `B=[A+0x20]`. Colchetes significam
leitura de ponteiro UInt64. O vetor de agentes está em `B+0`, `B+8` e `B+0x10`
(início, fim e capacidade), com registros de `0x238` bytes.

| Campo | Objeto convertido | Tipo/largura | Origem no código do jogo |
|---|---:|---|---|
| `agent_id` | `agente+0x08` | UInt64, 8 bytes | campo bruto `+0x00`; conversor `0x1445d7d70` |
| `title` | `agente+0x68` | `std::string` MSVC x64, 32 bytes | campo bruto `+0x50`; parser `0x1457eb210`; conversor `0x1445d7d70` |
| `start_date` | `agente+0x1c` | UInt32, 4 bytes | campo bruto `+0xc8`; conversor `0x1445d7d70` |
| `expiration_date` | `agente+0x24` | UInt32, 4 bytes | campo bruto `+0xcc`; conversor `0x1445d7d70` |

## Listas de cartas

Cada cabeçalho é um vetor MSVC de três ponteiros. Em cada registro convertido,
o `card_id` é UInt64 em `+0x08`.

| Lista | Cabeçalho convertido | Registro | Cabeçalho bruto no parser |
|---|---:|---:|---:|
| `pickup_list` | `agente+0xe8` | `0xf8` bytes | `+0x128` |
| `banner_a_pickup_list` | `agente+0x200` | `0xf0` bytes | `+0x250` |
| `banner_c_pickup_list` | `agente+0x218` | `0xf0` bytes | `+0x268` |

As três listas são unificadas por `card_id`, preservando a primeira ordem
observada. O leitor rejeita agente duplicado, título vazio, ponteiro fora do
espaço de usuário, vetor desalinhado, card ausente da referência física e
qualquer cabeçalho que mude durante a captura.

## Persistência

### Catálogo de Ofertas — Operação Dedicada

O comando dedicado lê IDs, títulos, início, fim e total diretamente do vetor de
agentes. Não consulta listas de participantes nem exige uma referência de cards.
Usa o mesmo parser com `catalog_only=True`; a cobertura registrada é
`catalogo_agentes_carregado`. `record_offer_catalog` grava a captura e todos os
agentes, depois verifica os campos por outra conexão. Não substitui vínculos.

Prova de 13/09/2026: captura `f6124088-ec46-41bf-9968-aa45577f7468`, nove agentes e nove
IDs distintos confirmados no banco. O registro desta prova foi aplicado pelo
conector Supabase: a conexão direta configurada no ambiente de teste recusou a
autenticação. O fluxo local de gravação ainda precisa de credencial válida.
O teste do catálogo impede leituras dos vetores de participantes; oito testes passam.
Identificação do catálogo e alteração da classificação pública são operações
distintas: esta prova registra a origem e a lista, sem declarar a reclassificação
completa do site. Packs de outra coleção não estão cobertos por esse vetor.

`clube_novo.box_leitor_endereco_jogo_v1` é a cópia consultável deste contrato.
`box_captura_jogo_v1` guarda o payload e a prova de cada captura;
`box_agente_captura_jogo_v1` guarda título e datas por agente; e
`box_agente_card_captura_jogo_v1` guarda cada vínculo e sua ordem. A RPC
`clube_novo.sincronizar_boxes_jogo_v1(jsonb)` só aceita o contrato, leitor,
fonte e hash acima. Ela reconhece boxes atuais pelo título normalizado e passa a atualizar o contexto
com o agente, participantes e datas comerciais capturados. Novos títulos são
incluídos sem IDs especiais por jogador. O encerramento usa o fim comprovado e
preserva os vínculos para o histórico; ausência numa sessão não comprova o fim de
uma oferta de outra fonte. O job da leitura de Boxes verifica vencimentos a cada
minuto, mesmo sem novo resultado do motor.

Após uma carga de cartas aprovada, o executor tenta atualizar as boxes automaticamente.
A leitura sem aplicação permanece sem gravação. É necessário o jogo com a área de
Contratos carregada; se faltar a sessão, a pendência fica em `boxes-resultado.json`
e no progresso. O botão Atualizar Boxes Novas consulta e registra somente o catálogo,
sem abrir cada box. Seu readback verifica IDs, títulos e datas. A aplicação de
participantes completos mantém seu próprio readback de vínculos.


O acervo histórico tem manifesto em `box_acervo_legado_v1`. A relação comercial
unificada usa `box_contexto_contratacao_v1` e `box_card_em_andamento_v1`; o Site Novo
lê as RPCs de Boxes sobre `boxes_leitura_pronta_v1`. O campo `carta_jogo.box` não participa e
não deve ser preenchido pelo leitor de Boxes.


## Datas

`visto` do acervo foi separado em `data_observada_legado`. A data comercial legada
só é derivada quando há dia, mês e ano completos no título validado; sem prova,
fica nula. Datas impossíveis também ficam nulas. Ofertas do jogo usam o início
oficial do agente em UTC, que pode representar uma reoferta. Nunca usar a data de
captura como início. Migrações vigentes: `20260913092000_boxes_datas_corretas.sql`
e `20260913092500_boxes_ciclo_ofertas.sql` em `Site Novo/supabase/migrations`.

## Leitura completa validada em 13/09

`pickup_list` e banners são somente destaques. O leitor V2 usa também o vetor
StandardDraft/Procurable já mapeado: B+0x380, stride 0xf0, ID em +8, total em
B+0x398 e índice inicial em B+0x3d4. Exige índice zero, quantidade igual ao total,
IDs físicos válidos e únicos, releitura estável dos dados/cabeçalhos e um único
agente cujos destaques estejam todos na lista completa. Ambiguidade ou paginação
incompleta impedem publicação; não ligar lista de recrutamento a uma box por suposição.

A captura comercial completa preserva todos os IDs nas tabelas de prova. A relação
exibida inclui somente `carta_jogo.codigo_tipo_carta_fisico>0`, mantendo o padrão de especiais.
A Summer Transfer vol.3 comprovou 150 participantes, dos quais 11 especiais.
O ID consultado em B+0x280 também deve coincidir com o agente identificado e
permanecer estável. O produtor 0x14467d8d3 copia esse ID para Option+0x228;
o serializador 0x1452b9eb3 o envia como `agent_id`. Foi validado com o agente
1365, Worldwide 10 Sep '26, com 11 participantes. Sete testes cobrem lista completa,
página parcial, agente ambíguo, ID desconhecido, detalhes de outra seleção,
divergência entre total do agente e detalhes e lista completa sem abrir detalhes.
O registro do banco foi atualizado por `BOXES-MAPEAMENTO-V2.sql`: V1 permanece
inativo como histórico; V2 registra também o vetor completo, total, índice e agente consultado.

O total oficial também existe no agente convertido em +0x128 (UInt32): parser
0x1457ebbff lê `player_list_total` em raw+0x158; conversor 0x1445d87ae copia
para destino+0x128. Se a união de IDs físicos distintos das listas do próprio
agente já coincide com esse total positivo, ela é completa sem abrir detalhes.
Na PFA TOTY, foram conferidos 11 IDs contra total 11. Captura persistida
f13bbd9d-d0af-47fb-81b6-948aa5d3ab82: PFA e Worldwide, 11 vínculos cada,
confirmados por leitura independente no banco. O caminho de detalhes também
exige que seu total coincida com o total oficial do agente.

Os detalhes são carregados sob demanda pelo jogo: ler o binário não fabrica uma
resposta que o servidor ainda não enviou. Na última sessão, duas das nove ofertas
tinham listas completas disponíveis; a Summer Transfer tem captura completa anterior.
Não declarar sincronização de todas as ofertas, nem encerrar registros sem fim
comprovado, com base apenas nessa captura. É pendência automatizar a cobertura das
demais ofertas. Ver `20260913094000_boxes_detalhes_completos_v2.sql`.

O botão dedicado não exige IDs físicos das cartas: a identificação das ofertas
é independente da captura de seus participantes.
