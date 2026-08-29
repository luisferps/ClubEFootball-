# Auditoria dos moldes por ID — 28/08/2026

## Fato de banco: catálogo migrado não é molde migrado

- `clube_novo.funcao_sistema` está migrada: 19 linhas, PK canônica `id`,
  `codigo_legado` único e gatilho `funcao_sistema_id_imutavel`.
- `clube_novo.funcao_alias` tem 14 aliases de compatibilidade; PK `id` e FK
  `id_funcao → funcao_sistema(id)` com `ON UPDATE/DELETE RESTRICT`.
- Não existe tabela de molde em `clube_novo`. O conteúdo vigente continua apenas
  em `clube.molde`: versão 5, 494 linhas (19 × 26).
- Portanto, antes deste contrato o catálogo de funções estava migrado, mas os
  pesos/alvos dos moldes não estavam. A existência de `funcao_sistema` sozinha
  não tornava o Otimizador consumidor por ID.

## Ponte autorizada, sem mudar molde

`otimizador_regua_v1()` é a única ponte: compara o código técnico estável
`clube.molde.funcao_codigo` com o `codigo_legado` único de `funcao_sistema` e
entrega ao consumidor somente `funcao_id + indice_otimizador + alvo + peso`.
O rótulo canônico e os 14 aliases são apresentação/diagnóstico e não participam.

Não foi criada cópia dos 494 pesos/alvos no modelo novo, e nenhum valor, peso,
regra, composição ou versão do molde foi alterado.

## Prova dos 19 moldes

O readback encontrou 19/19 códigos, zero ausência, zero ambiguidade e 26 índices
distintos (0–25) em cada função. A fila tem 125.445 referências e zero código sem
`funcao_id`. Cada função recebeu fingerprint próprio de seus 26 pares
`(índice, alvo, peso)`; a auditoria automatizada compara esse fingerprint e cada
valor antes/depois.

Exemplos que não podem ser unidos por nome:

- ID 1 = código `centroavante_fixo`, molde preservado pelo fingerprint
  `8081643e3e877c3a796c91be0e252826`;
- ID 2 = código `centroavante_movel`, fingerprint
  `a16e2398ffef8f567ae0a017fe901e45`;
- ID 8 tem rótulo novo `Meia ofensivo`, mas o molde vigente é identificado pelo
  código comprovado `meia_ofensivo_armador` e pelo ID 8;
- ID 9 tem rótulo novo `Atacante infiltrador`, mas o molde vigente é o código
  `segundo_atacante`, ID 9. O nome novo não foi usado para deduzir a ligação.

O script `2-MOTORES/OTIMIZADOR/auditar_moldes_v1.py` reprova qualquer ausência, duplicidade,
mudança de alvo/peso ou cardinalidade. O teste de renomeação altera todos os
rótulos de apresentação e exige fingerprints e seleção de moldes idênticos.

## Referências ativas e estado da troca

| referência | antes | contrato/estado |
|---|---|---|
| lote `roda_lote_v6.py` | dicionário por `funcao_codigo` textual | aplicado: indexa molde, bloqueios, incidência e fila por `funcao_id` |
| serviço Railway local | aceitava `funcao` textual e indexava `regua.molde[funcao]` | aplicado: recebe/responde `funcao_id`; a implantação pública ainda não foi comprovada |
| `clube.fila` | guarda `funcao_codigo` | `otimizador_proxima_fila_v1` traduz na fronteira e devolve `funcao_id`; conteúdo da fila não muda |
| `clube.molde` | guarda `funcao_codigo` | `otimizador_regua_v1` traduz na fronteira; os 494 valores ficam intocados |
| JSON local de molde | fallback histórico | removido do caminho ativo; ausência do contrato v1 encerra a execução sem fallback |
| `clube.molde_corpo`/`motor_bonus.py` | rótulos de função | consumidor separado e deliberadamente bloqueado; não faz parte da troca do molde de atributos |
| réplicas de tela | rótulos para apresentação/rota e catálogos embutidos | preservadas byte a byte e ainda não migradas; dependem de endpoint seguro implantado por IDs |

## Tabela completa da tradução estável

Esta tabela traduz somente o endereço externo do molde. O `codigo_legado` é a
chave técnica única já gravada em `clube.molde`; não é rótulo apresentado nem nova
identidade do modelo. A identidade consumida depois da fronteira é sempre o ID.

| ID canônico | `codigo_legado` comprovado |
|---:|---|
| 1 | `centroavante_fixo` |
| 2 | `centroavante_movel` |
| 3 | `falso_nove` |
| 4 | `goleiro_defensivo` |
| 5 | `goleiro_ofensivo` |
| 6 | `lateral_defensivo` |
| 7 | `lateral_ofensivo` |
| 8 | `meia_ofensivo_armador` |
| 9 | `segundo_atacante` |
| 10 | `meia_central_armador` |
| 11 | `meia_central_de_chegada` |
| 12 | `meia_de_lado_por_dentro` |
| 13 | `meia_de_lado_por_fora` |
| 14 | `ponta_criadora` |
| 15 | `ponta_finalizadora` |
| 16 | `volante_de_construcao` |
| 17 | `volante_de_contencao` |
| 18 | `zagueiro_de_combate` |
| 19 | `zagueiro_de_saida` |

## Paridade posterior

`AUDITORIA-MOLDES-POS-CONSUMIDOR-2026-08-28.json` aprovou os 19 moldes,
494/494 linhas, 26 índices por função e os fingerprints exatos de alvo/peso. O
teste de renomeação manteve seleção e saída idênticas. Nenhum conteúdo, texto,
peso, ordem, fórmula ou regra do molde foi alterado.
