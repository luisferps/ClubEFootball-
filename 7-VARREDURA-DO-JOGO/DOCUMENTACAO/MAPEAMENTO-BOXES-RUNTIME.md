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

## Fluxo Vigente

`record_offer_catalog` usa o mesmo parser com `catalog_only=True`: IDs, títulos,
datas e total, sem consultar vetores de participantes. Após a carga aprovada,
o worker registra a captura, aplica os contextos e atualiza a leitura do site.
O botão dedicado repete a operação. Oito testes passam, incluindo a ausência
de leitura de participantes no modo catálogo.

Banco: `box_captura_jogo_v1` preserva a prova; `box_agente_captura_jogo_v1`
preserva cada oferta. `box_catalogo_jogo_atual_v1` seleciona a última captura.
`aplicar_catalogo_boxes_jogo_v1` reconhece por ID ou nome exato, cria contextos
novos, aplica datas e classifica os contextos fora do catálogo como históricos.
Os vínculos existentes são preservados. `boxes_leitura_atualizar_v1` atualiza
a leitura usada pelas RPCs públicas, com o job periódico como recuperação.

Prova integrada: 97370683-107e-4d47-a420-f6251e07253b, nove agentes/contextos,
conexão protegida do aplicativo e releitura independente. As RPCs dos três graus
retornaram nove ofertas. A página renderizada mostrou nove boxes e 88 cards.
A falha de autenticação inicial era da variável de ambiente da sessão de teste;
a credencial DPAPI do aplicativo passou na execução real.

A correção pontual autorizada de hoje está documentada em
BOXES-CORRECAO-PONTUAL-1309.json: 25 vínculos para três ofertas, conferidos com
IDs físicos, catálogo do jogo e referência eFHUB. As decisões em valor_do_dono
preservam esses vínculos. A referência não virou fonte diária do extrator.

Os SQLs BOXES-CATALOGO-CONSULTA.sql, BOXES-CATALOGO-APLICAR.sql e
BOXES-MAPEAMENTO-V2.sql registram os contratos. O histórico de participantes
completos da Summer Transfer permanece na prova de 150 IDs/11 especiais.

## Limites da Fonte

A lista exige jogo aberto em Contratos. O catálogo de agentes não é lista de
participantes e não representa outras coleções, como packs. Novos vínculos
precisam de captura própria; prefixo de card_id não comprova box (há um prefixo
com 23 cartas de ofertas diferentes). Não declarar composição completa a partir
dos três destaques. Identidade/disponibilidade e composição são dados separados.
Datas do jogo são oficiais; data de captura não substitui início da oferta.
