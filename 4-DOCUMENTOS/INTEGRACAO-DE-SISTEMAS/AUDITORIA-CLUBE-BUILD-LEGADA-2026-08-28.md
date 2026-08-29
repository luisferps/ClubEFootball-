# Auditoria da `clube.build` legada

> Nota de decisão posterior: as interpretações M:N e “uma única Build apenas por carta” registradas historicamente foram revogadas. A regra vigente é uma linha campeã ativa por `(card_id, funcao_id, posicao_id)` em `clube_novo.build_linha_card`, sempre ligada aos resultados do Otimizador e do Bonificador. Este arquivo permanece apenas como evidência da auditoria do legado e não define o modelo novo.

Data: 2026-08-28

## Regra desta auditoria

`clube.build` e `clube.build_arquivo_2608` foram lidas somente como referência histórica para decidir o desenho novo. Nenhuma linha será copiada, migrada, usada como fallback, gate ou entrada operacional. A Build nova deverá nascer vazia e independente em `clube_novo`.

## Estado encontrado

| Objeto | Estado |
|---|---|
| `clube.build` | 0 linhas; tabela operacional histórica hoje vazia |
| `clube.build_arquivo_2608` | 17.798 linhas; fotografia histórica com as mesmas 33 colunas |
| PK histórica | `(card_id text, funcao_codigo text)` |
| FKs históricas | `funcao_codigo -> clube.funcao(codigo)` e `receita_versao -> clube.receita_versao(versao)` |
| FK de carta | inexistente |
| Índices | PK; função+nota; nota global quando há `linha`; fila parcial por `recalcular` |
| Trigger em `clube.build` | nenhum |

A fotografia contém 2.836 cartas, 19 funções, 17.798 pares únicos e zero duplicidade de `(card_id, funcao_codigo)`. Cada carta tem de 1 a 17 funções, média 6,276. Isso prova que cada linha histórica era o último resultado automático disponível para uma carta em uma função. A linha não tinha `build_id`, nome de Build nem histórico de versões; portanto não era a identidade completa da Build salva que existe na interface.

## Semântica comprovada de Build no produto

Há três camadas históricas distintas que antes recebiam o mesmo nome:

1. `public.builds` guardava uma saída do motor por `(card_id, funcao, motor_versao)` e ainda impunha unicidade em `(card_id, funcao)`;
2. `clube.build` consolidou somente a saída vigente por `(card_id, funcao_codigo)`, recebendo primeiro o Otimizador e depois as parcelas do Bonificador;
3. a tela de Build apresenta a combinação vencedora produzida pelo motor: função, distribuição (`lvl`), habilidades, Ímpeto, técnico, atributos por etapa, gates e pontuação. O estado local também permite criar cópias editáveis com `buildId`; essas cópias do usuário são outra camada e não definem a identidade da Build otimizada canônica.

O código atual da interface comprova:

- a entrada do motor é o contexto `card_id + funcao_id`, com molde/pesos, carta, técnico e candidatos permitidos;
- o motor avalia as combinações de distribuição, habilidades, técnico/boost e Ímpeto aplicável;
- o vencedor é atualizado somente quando encontra pontuação maior; em empate há desempate explícito pela incidência/popularidade das habilidades;
- `build_completo2` devolve somente o vencedor, com `lvl`, técnico, habilidades, Ímpetos, vetores de atributos e `nota`;
- `roda_lote_v6.py` chama esse resultado de “build campeã” e materializa a cadeia Base -> Barras -> Tela -> Final;
- a interface local mostra carta, função, técnico, atributos de entrada, barras vencedoras, gasto, sobra, boosts, habilidades escolhidas, Ímpetos, atributos em campo, gates e validação de paridade;
- a Ficha principal expande esse vencedor com atributos por etapa, distribuição, habilidades, Ímpetos, técnico, físico/Bonificador e pontuação final.

Assim, **Build é a combinação vencedora concreta: dentre as milhões avaliadas pelo motor para a carta no contexto de função exibido, é a que obteve a maior pontuação segundo o sistema de pesos e seu desempate aprovado**. A linha de `clube.build` é apenas um predecessor operacional incompleto desse conceito.

### Dimensão da relação muitos-para-muitos

A regra de produto determina que Build e Carta sejam muitos-para-muitos. A dimensão correta é a **combinação vencedora compartilhável**, não uma rodada nem uma receita genérica:

- a identidade da Build é a combinação vencedora: função, distribuição, técnico/boost, habilidades, Ímpetos e versões das regras que a definem;
- a mesma combinação pode ser vencedora para várias cartas;
- uma carta pode ter várias combinações vencedoras, especialmente em funções/contextos diferentes;
- `Build-Carta` registra para qual versão da carta aquela combinação venceu, a pontuação e a tela histórica específica;
- a tela individual é reconstruída pelo conjunto `Build + Build-Carta + snapshots do resultado`;
- a aplicação da Build em campo/banco/reserva é outra relação, com ocorrências do elenco, e não deve ser confundida com a junção canônica Build-Carta.

### Prova quantitativa da cardinalidade

Foi calculada uma assinatura somente leitura sobre `funcao_codigo + barras + impeto + tecnico_id + habilidades` nas 17.798 linhas históricas:

- 402 combinações vencedoras aparecem em mais de uma carta;
- essas combinações cobrem 6.210 resultados históricos;
- uma mesma combinação vencedora aparece em até 253 cartas;
- 2.834 cartas possuem mais de uma combinação vencedora no histórico.

Mesmo excluindo as combinações totalmente zeradas, há vencedores completos compartilhados. Exemplo: a combinação de Zagueiro de combate com Defesa 20, Força aérea 4, Força inferior 4, Ímpeto Duelo +1, o mesmo técnico e cinco habilidades iguais venceu em três cartas distintas.

Isso prova os dois lados da relação M:N. A assinatura histórica usa textos porque é a única fotografia disponível; a chave nova deve usar exclusivamente IDs canônicos e fingerprints de contrato.

## Cobertura contra o modelo novo

- 17.795 das 17.798 linhas históricas ainda encontram `card_id` em `clube_novo.carta_jogo`; as três ausentes são histórico e não serão carregadas.
- 17.798/17.798 códigos de função encontram `clube_novo.funcao_sistema.id`.
- 17.135/17.135 técnicos não nulos encontram `clube_novo.tecnico_jogo.id`.
- a existência dessas pontes serve apenas para o desenho de FKs; não autoriza migração de dados.

## Quem gravava

### Otimizador — `public.gravar_build(jsonb)`

Fazia `INSERT ... ON CONFLICT` por carta+função e escrevia:

- `b1`, `barras`, `impeto`, `tecnico_id`, `tecnico_nome`;
- `habilidades`, `vals`, `falta_pool`, `sobra`;
- `receita_versao`, `motor_versao`, `rodado_em`, `origem`;
- limpava `recalcular`/`motivo_recalculo`;
- apagava a mesma carta+função de `clube.fila` na mesma função.

A ponte atual do código ainda traduz `funcao_id` canônico de volta para `funcao_codigo` textual somente para essa saída histórica. Isso não pode existir no caminho novo.

### Bonificador — `public.gravar_bonus(jsonb)`

Atualizava a mesma linha da Build histórica com:

- `b_corpo`, `b_pe_ruim`, `b_estilo`, `b_ia`, `b_total`;
- `bonus_rodado_em` e `atualizado_em`.

Esse desenho permitia que dois motores atualizassem a mesma linha. O modelo novo deve manter os resultados separados até uma publicação transacional.

## Quem consumia

| Consumidor legado | Campos usados |
|---|---|
| `clube.tela` | nota, `b1`, parcelas/total do bônus, barras, ímpeto, técnico, habilidades, `vals_tela`, origem e estado |
| `public.casa_tela` | cache JSON `linha`, força, data e recálculo |
| `public.casa_lista` | cache JSON `linha_enxuta`, força, data e recálculo |
| `public.casa_arows` | `arows`, `falta_pool` e parcelas do Bonificador |
| `clube.topo_funcao` / `mediana_funcao` | `nota_final` por função |
| `clube.fila_da_rodada` e `public.fila_do_motor` | existência da Build, `recalcular` e motivo |
| `public.pool_da_funcao` | fotografia `falta_pool` usada pelo Otimizador naquela função |
| auditorias legadas | contagens, completude, recálculo e comparação histórica |

Há ainda uma função antiga ligada à carta que apagava Builds quando posição, estilo, atributos ou overall mudavam. No modelo novo isso deve virar invalidação versionada, nunca exclusão silenciosa.

## Medidas que impedem cópia cega

- 9.446/17.798 linhas estavam com `recalcular=true`.
- 720 linhas tinham uma ou mais parcelas do Bonificador ausentes.
- `impeto` só estava preenchido em 5.145 linhas.
- `linha`, `linha_enxuta`, `arows` e `falta_pool` faltavam em 294 linhas.
- `extras` estava preenchido nas 17.798 linhas, mas repetia carta, valores, ímpetos, bônus e dados de tela num pacote sem FKs.
- `migrado` era `false` nas 17.798 linhas.
- `sobra` era `0` nas 17.798 linhas.

## Fórmulas estruturais comprovadas, sem alterar motores

- `nota_final` era coluna gerada por `coalesce(b1,0) + coalesce(b_total,0)`; zero divergências nas 17.798 linhas.
- quando `b_total` existia, ele era exatamente `b_corpo + b_pe_ruim + b_estilo + b_ia`; zero divergências.

Isso prova a composição histórica da publicação. Não autoriza recalcular ou reimplementar fórmulas dos motores no banco; o novo publicador apenas poderá juntar resultados já selados.

## Classificação campo por campo

Legenda:

- **A — resultado essencial**: pertence ao resultado selado de um motor ou à publicação.
- **B — identificação/proveniência**: deve virar FK, versão, fingerprint ou data estruturada.
- **C — legado/redundante**: não migrar para o núcleo canônico.
- **D — lacuna do novo modelo**: precisa nascer explicitamente, sem ser copiada do legado.

| Campo legado | Classe | Destino conceitual novo |
|---|---:|---|
| `card_id` | B | FK da junção para `clube_novo.carta_jogo(card_id)` |
| `funcao_codigo` | B | substituir por FK `funcao_id -> funcao_sistema(id)` |
| `b1` | A | resultado do Otimizador |
| `b_corpo` | A | resultado do Bonificador |
| `b_pe_ruim` | A | resultado do Bonificador |
| `b_estilo` | A | resultado do Bonificador |
| `b_ia` | A | resultado do Bonificador |
| `b_total` | A | total declarado pelo Bonificador, com coerência contra as parcelas |
| `nota_final` | A | resultado publicado derivado somente após juntar os dois motores da mesma versão |
| `barras` | A | resultado do Otimizador |
| `impeto` | A/B | escolha do Otimizador, mas no novo deve usar ID canônico; texto legado não migra |
| `tecnico_id` | A/B | escolha do Otimizador com FK para `tecnico_jogo(id)` |
| `tecnico_nome` | C | rótulo derivável pela FK; não guardar no núcleo |
| `habilidades` | A/B | escolhas do Otimizador por IDs canônicos; nomes legados não migram |
| `vals` | A | vetor final pontuado pelo Otimizador |
| `vals_tela` | A | vetor observável anterior às habilidades; necessário enquanto consumidores o exigirem |
| `origem` | C | texto livre; substituir por contrato/fingerprints estruturados |
| `estilo` | C | rótulo de apresentação derivável; não guardar no núcleo |
| `sobra` | A | resultado do Otimizador, embora o histórico só tenha zero |
| `migrado` | C | marcador obsoleto; a Build nova nasce canônica |
| `receita_versao` | B | versão/fingerprint do contrato de régua/receita do Otimizador |
| `motor_versao` | B | separar em versão do Otimizador e do Bonificador |
| `rodado_em` | B | data do resultado do Otimizador |
| `bonus_rodado_em` | B | data do resultado do Bonificador |
| `recalcular` | D | substituir por estado explícito e invalidação versionada |
| `motivo_recalculo` | D | motivo estruturado da invalidação/falha |
| `extras` | C | pacote duplicado sem FKs; não migrar |
| `atualizado_em` | B | metadado técnico da linha nova |
| `linha` | C | cache de UI; não copiar o JSON, mas preservar em relações/snapshots canônicos todos os fatos que ele apresentava |
| `linha_gerada_em` | C | data do cache de UI |
| `arows` | C | não copiar o bloco opaco; peso, alvo, etapas e valor exibido de cada atributo devem virar linhas explícitas por ID canônico |
| `linha_enxuta` | C | segundo cache de UI; não núcleo |
| `falta_pool` | A/B | fotografia do pool realmente usado, mas por `skill_id` e fingerprint do contrato |

## Regra nova: uma Build salva deve reconstruir integralmente sua tela

A Build nova não pode guardar apenas os IDs da carta e uma pontuação final. Ela deve conservar os fatos necessários para renderizar no futuro a mesma tela que foi publicada, mesmo que a carta, os catálogos ou os rótulos atuais mudem depois.

Isso não autoriza copiar `linha`, `linha_enxuta`, `arows`, `extras` ou a carta inteira como JSON opaco. A separação correta é:

- **relações normalizadas** para identidades estáveis e pesquisáveis, sempre por IDs/FKs do `clube_novo`;
- **snapshots históricos imutáveis** para os valores efetivamente usados e mostrados naquela publicação;
- **projeção de UI** reconstruída a partir dessas relações e snapshots, sem consultar o legado e sem recalcular com a carta atual.

### Atributos — granularidade obrigatória

O modelo novo já possui a identidade canônica `atributo_jogo.codigo`, a ordem do motor em `atributo_ordem_otimizador.indice_otimizador` e a relação física atual `carta_atributo_jogo(card_id, codigo_atributo, valor)`. Para cada atributo apresentado na Build, a publicação precisa conservar uma linha própria ligada ao par Build-Carta-Função com, no mínimo:

- FK `codigo_atributo -> atributo_jogo(codigo)`;
- ordem de apresentação usada naquela tela;
- peso/classe daquela função e alvo usado pela régua;
- valor físico/base de origem;
- contribuição da distribuição de evolução/barras;
- valor após barras e o teto aplicável naquela etapa;
- contribuição de Ímpetos nativos/adicionados, quando ativos;
- efeito da proficiência do técnico e boost de técnico, quando aplicáveis;
- contribuição de habilidades nativas e adicionadas, quando aplicáveis;
- valor interno final usado na conta;
- valor final exibido pela tela e a regra/versão de apresentação;
- diferença contra o alvo e parcela da pontuação exibida, quando essa coluna fizer parte da tela publicada.

A tela atual comprova que esses degraus existem na apresentação: Base, Barras, Ímpeto, Técnico, habilidades nativas, habilidades adicionadas, total/no jogo, alvo, diferença e pontos. O contrato de saída do Otimizador ainda precisa nomear e selar cada etapa antes do DDL; não é seguro inferir as colunas definitivas apenas pelas posições do vetor legado.

### Outras seções visíveis que precisam sobreviver

| Seção da tela | Relação normalizada | Snapshot histórico necessário |
|---|---|---|
| Identidade da carta | FK `card_id -> carta_jogo` | nome/versão visual publicada, versão e fingerprint integral da carta |
| Função e posições | FKs para `funcao_sistema` e `posicao_jogo` | função avaliada, posição nativa, posições exercidas e proficiência mostrada |
| Distribuição | identidade canônica de cada grupo de evolução quando formalizada | nível por grupo, custo, orçamento, pontos gastos e sobra |
| Técnico | FK `tecnico_id -> tecnico_jogo` | estilo/proficiência escolhida, multiplicador efetivo, atributos de boost e valores aplicados |
| Playstyles | FKs para `playstyle(id_jogo)` | slots, ordem e estado efetivamente mostrado |
| Habilidades | FKs para `habilidade_jogo(skill_id)` | nativa/adicionada/especial, ordem, estado selecionado e contribuição usada |
| Ímpetos | FKs para `impeto_jogo(codigo_jogo)` | slot, nativo/adicionado, condicionalidade, condição/nível resolvido e efeitos efetivamente aplicados |
| Bônus | resultado selado do Bonificador por carta+função+versão | corpo e suas medidas, pé ruim, playstyles, IA, parcelas, total e gates usados |
| Gates e travas | códigos canônicos de regra/estado quando existirem | estado, motivo, dados faltantes e decisão fail-closed daquela execução |
| Resultado | ligação aos resultados selados dos dois motores | `b1`, parcelas, `b_total`, nota publicada, arredondamento/exibição e posição/ranking apresentados |
| Proveniência | contratos e versões dos motores | fingerprints, datas, versões da fórmula/regra/apresentação e publicador |

Rótulos podem ser derivados dos catálogos atuais para telas atuais, mas uma Build histórica precisa também manter o rótulo efetivamente publicado ou a versão imutável do catálogo textual usada. Isso evita que uma renomeação futura mude retroativamente a tela de uma Build já salva.

## Lacunas que a Build nova precisa cobrir

1. PK imutável da entidade Build nova.
2. definição funcional do que uma Build representa.
3. junção muitos-para-muitos Build-Carta com FKs canônicas.
4. `funcao_id` canônico no resultado por carta/função.
5. versão e fingerprint integral da carta.
6. versões/fingerprints independentes do Otimizador e do Bonificador.
7. resultados separados, para um motor não apagar o outro.
8. estados `pendente`, `pronto`, `nao_aplicavel` e `invalido`.
9. invalidação de resultados anteriores quando a carta muda.
10. publicador transacional que só aceite os dois resultados necessários da mesma versão.
11. proveniência da publicação e possibilidade de readback/rollback.
12. snapshots normalizados suficientes para reconstruir integralmente a tela histórica da Build.
13. contrato explícito das etapas por atributo; nenhum vetor posicional opaco como fonte única.

## Proposta factual de modelo novo — ainda sem DDL

### `build`

Identidade imutável da combinação vencedora: `build_id`, `funcao_id`, fingerprint canônico da combinação, versões/fingerprints da fórmula, régua, busca e desempate, estado e proveniência. Seus filhos normalizados registram distribuição, técnico/boost, habilidades e Ímpetos que compõem a combinação. Não contém atributos próprios de uma carta.

### `build_carta`

Junção M:N e unidade de resultado/tela. Liga `build_id` a `carta_jogo.card_id` e carrega versão/fingerprint da carta, estado, pontuação vencedora, posição/rank vencedor e fingerprint do payload de tela. Deve possuir identidade própria de resultado para que todas as relações filhas apontem sem repetir uma chave composta extensa.

Como a função pertence à identidade da combinação vencedora, a unicidade do resultado deve considerar `build_id + card_id + versão/fingerprint da carta`. Uma nova versão da carta produz uma nova avaliação, mesmo que a combinação vencedora continue idêntica.

### Resultados intermediários separados

- resultado selado do Otimizador por vínculo Build-Carta;
- resultado selado do Bonificador por vínculo Build-Carta;
- estado independente `pendente`, `pronto`, `nao_aplicavel` ou `invalido`;
- versões/fingerprints dos contratos e fórmulas;
- número de combinações avaliadas, número podado quando disponível, pontuação objetiva vencedora, critério de desempate e assinatura da busca;
- marca/rank de vencedor igual a 1; não basta guardar uma combinação sem provar por qual execução ela venceu;
- nenhuma parte atualiza ou apaga a linha da outra.

### Relações filhas do vínculo Build-Carta

- atributos por `atributo_jogo.codigo`, com todas as etapas e valor exibido;
- distribuição por grupo canônico de evolução;
- posições por `posicao_jogo.id`;
- técnico por `tecnico_jogo.id`, estilo/proficiência e boosts efetivos;
- playstyles, habilidades e Ímpetos por seus IDs canônicos, com origem/ordem/estado;
- bônus detalhado e gates/travas;
- proveniência e snapshots de rótulos/apresentação necessários à reprodução histórica.

### Publicação

O publicador só torna o resultado Build-Carta pronto quando o vencedor do Otimizador e o Bonificador necessário pertencem à mesma versão/fingerprint da carta. Nenhum resultado parcial é exposto como Build final. Uma ligação posterior de outra carta à mesma Build só é aceita se a combinação canônica e seus contratos tiverem exatamente o mesmo fingerprint vencedor.

Antes do DDL ainda falta uma auditoria mecânica dos contratos de saída dos motores para fixar nomes, tipos e nulidade das colunas de cada etapa; não falta uma nova definição conceitual do que seja Build.
