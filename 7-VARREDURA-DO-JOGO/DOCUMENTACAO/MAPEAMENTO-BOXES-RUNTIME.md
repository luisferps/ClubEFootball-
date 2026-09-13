# Mapeamento físico das boxes comerciais

Contrato `boxes-cmd-get-myclub-agentlist-v1`, para eFootball 6.0.0.0, SHA-256
`a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4`.
O extrator lê a resposta `CmdGetMyclubAgentlist` já convertida e mantida pelo
jogo. Essa resposta cobre somente as ofertas carregadas na sessão atual; não
recupera boxes históricas. O histórico fixo vem do legado preservado em
`dados/boxes-historicas-legado.json`, copiando somente nome da Box, `card_id`
dos participantes e data `visto`. `PlayerVariationDetail.bin` descreve a
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

`clube_novo.box_leitor_endereco_jogo_v1` é a cópia consultável deste contrato.
`box_captura_jogo_v1` guarda o payload e a prova de cada captura;
`box_agente_captura_jogo_v1` guarda título e datas por agente; e
`box_agente_card_captura_jogo_v1` guarda cada vínculo e sua ordem. A RPC
`clube_novo.sincronizar_boxes_jogo_v1(jsonb)` só aceita o contrato, leitor,
fonte e hash acima. Ela reconhece boxes atuais de outra fonte pelo título sem
alterá-las, cria somente títulos novos e atualiza ou encerra apenas registros
que já pertençam à fonte `jogo:CmdGetMyclubAgentlist`. O readback usa as tabelas
de captura, por isso também confirma uma rodada em que todas as boxes já eram
conhecidas.

O acervo histórico tem manifesto em `box_acervo_legado_v1`. A relação comercial
unificada usa `box_contexto_contratacao_v1` e `box_card_em_andamento_v1`; a tela
lê apenas `public.frontend_boxes_v1`. O campo `carta_jogo.box` não participa e
não deve ser preenchido pelo leitor de Boxes.

