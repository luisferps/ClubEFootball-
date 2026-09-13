# Regra aprovada de habilidades por função — V12

Decisão de Luis Fernando em 09/09/2026. Esta é a regra vigente de seleção automática do Otimizador e de sugestões da Ficha. Não descreve restrições de ativação do jogo. Prevalece sobre a regra de 08/09 no que foi ampliado nesta revisão.

## Seleção automática e escolha pessoal

- A autoridade é `clube_novo.habilidade_funcao_bloqueio_otimizador`: 325 pares de habilidade/função, com 72 inclusões e três liberações nesta revisão.
- Toda sugestão automática usa os bloqueios atuais da função da build. Isso inclui gêmeas, substitutas e sugestões originadas de resultados antigos. Ser gêmea não libera uma habilidade bloqueada. Trocar a função exige filtrar novamente.
- O editor pessoal continua livre para escolher habilidades treináveis ou deixar vagas vazias. Os bloqueios não filtram seu seletor manual. Habilidades nativas e habilidades já gravadas em resultados antigos continuam sendo exibidas como são.
- A build automática pode ter de zero a cinco adicionais. Não se completa a lista com habilidades sem ganho. Após selecionar a solução vencedora, o motor verifica conjuntamente os subconjuntos das adicionais e conserva o menor subconjunto que mantém sua pontuação, com as mesmas barras, técnico e ímpetos. Em empate de quantidade e nota, usa incidência e IDs. Habilidades nativas não são retiradas.
- Nenhuma normalização de nota, bônus, peso, alvo ou fórmula de atributos foi alterada. A pontuação preservada pelo enxugamento é a pontuação bruta do motor; isso não prova que retirar uma habilidade de um resultado antigo preserve a nota final ou o bônus.

## Decisões desta revisão

| Habilidade | Permitida pelo novo critério |
|---|---|
| Cruzamento preciso; Arremesso lateral longo | Laterais defensivo/ofensivo, alas driblador/cruzador, atacantes criador/driblador |
| Controle da cavadinha | Centroavantes fixo/móvel e Falso nove |
| De letra | Centroavantes, Falso nove, meias, alas e atacantes; não volantes nem laterais |
| Cabeçada | Centroavantes, Falso nove, lateral defensivo, volantes e zagueiros |
| Dribles: Pedalada simples, Toque duplo, Elástico, Giro 360°, Chapéu, Corte com virada, Puxada de letra, Finta de letra e Controle com a sola (IDs 0–7 e 10) | Bloqueados em goleiros, lateral defensivo, volante de contenção e zagueiros; lateral ofensivo e volante de construção continuam permitidos. Chapéu mantém seu bloqueio anterior nos alas |
| Toque de calcanhar; Passe sem olhar | Acrescentado bloqueio no volante de contenção; demais bloqueios anteriores preservados |
| Marcação individual; Volta para marcar | Acrescentado bloqueio em goleiros; demais bloqueios anteriores preservados |

Os nomes exatos do catálogo constam na matriz abaixo. No volante de construção foram removidos os bloqueios antigos dos IDs 0, 2 e 4 conforme resposta explícita do usuário. Permissão não obriga o motor a selecionar: ainda se exige contribuição para sua nota.

## Gêmeas

Gêmeas cadastradas têm o mesmo vetor completo de efeitos, não apenas um atributo coincidente. Os vínculos são simétricos e os nomes são sincronizados. Passe em profundidade (32) e Cruzamento preciso (34) já eram gêmeas; foi corrigido, entre outros vínculos, Chute súbito (2457) com as habilidades de efeito idêntico.

Para substituição automática, além do mesmo efeito, é necessário ser fabricável, não vetada, ter o mesmo tipo e estar permitida na função. O agrupamento do motor preserva a distinção entre habilidades comuns e raras. O conceito cadastral de gêmeas não autoriza trocar tipos com regras diferentes de acumulação.

## Banco, runtime e sugestões

- Política: `clube_novo.otimizador_politica_habilidades`, versão `habilidades-funcao-20260909-v1`.
- Histórico anterior: `clube_novo.otimizador_historico_habilidades`; guarda catálogo, bloqueios e os sete lotes pausados antes da atualização. Ambas as tabelas são privadas, com RLS e sem políticas de acesso público por intenção.
- `otimizador_regua_v2` entrega política e matriz. Os sete lotes pausados receberam somente política/bloqueios/selos novos; pesos, alvos, efeitos e parâmetros anteriores foram preservados.
- 135.759 linhas pendentes tiveram os selos esperados alinhados. Estados, ordem dos lotes/linhas e ponteiros de resultados foram preservados. Os lotes continuam pausados.
- `fila_local_v1.py` recusa fotografias antigas sem a política aprovada. O importador JSON e as portas V3/V6 recusam novas adicionais bloqueadas, nativas duplicadas, listas inválidas e habilidades sem incidência em atributo ponderado. A validação matemática de ganho marginal e saturação pertence ao motor aprovado, não a uma segunda otimização em SQL. Recibos idempotentes antigos permanecem válidos.
- `site_novo_ficha_sugestoes_v1` e `frontend_build_publicada_v2` filtram pelas regras atuais. `filtrar_gemeas_funcao_v12` filtra as gêmeas por função. O catálogo pessoal entrega `bloqueios_sugestao` e `gemeas_cadastradas`; o campo antigo `gemeas` fica vazio para impedir sugestões indevidas em clientes antigos. O seletor manual mantém as habilidades treináveis.
- `Site Novo/ficha-editor.js` e `1-SISTEMA/ficha-ajustes.js` foram atualizados localmente. O segundo não inventa sugestões quando o banco retorna lista vazia. Não houve publicação no Netlify ou GitHub.

## Estado e retomada

Os arquivos oficiais da Máquina 1 e `OperacaoLocalJson.exe` foram atualizados. As fotografias locais foram renovadas com `--preservar-ordem`; os oito IDs de lotes e as duas prioridades mantiveram a ordem exata. Dois lotes sem pendências são apenas ignorados na leitura, sem reabertura. As fotografias anteriores ficam em `RENOVACOES`; resultados e recibos não foram apagados. A fotografia vigente contém 126.318 linhas elegíveis pelos filtros já existentes de orçamento, prioridade e entrada compatível. As 135.759 pendentes com selos atualizados incluem linhas que ainda não passam por esses filtros; não foram apagadas nem reordenadas.

Motor: `otimizador-fila-producao-v3-local-20260909-habilidades-v12`  
Fingerprint dos cinco fontes: `a1cc830af3366e2d0c9ac12138d892058b3e57ed216e43d68242d105b33cb9d2`

O pacote da Máquina 2 é uma entrega separada, preparada para instalação futura. Leia [Entrega e arquivos](ENTREGA-MAQUINA-2.md). Não está instalado por ter sido gerado aqui. Os atalhos continuam `PROCESSAR-FILA-PRINCIPAL.bat` e `ENVIAR-FILA-PRINCIPAL.bat`. A atualização e a renovação não iniciam processamento nem envio. Não usar pacotes ou executáveis antigos com a política nova.

## Revisão dos resultados antigos

Levantamento de 09/09: 57.383 linhas válidas com resultado; 12.175 reconstruídas em detalhe (todas as 10.899 com adicionais, mais as de volante de construção para conferir opções liberadas). Outras 45.208 não têm adicionais e não pertencem à função com liberações.

| Situação | Linhas | Publicadas |
|---|---:|---:|
| Exigem reotimização por perda ao remover | 3.352 | 3.296 |
| Permitem remoção sem perda na nota bruta do motor | 934 | 927 |
| Revalidar novas opções liberadas | 89 | 86 |
| Dados históricos incompletos | 110 | 0 |
| Divergência entre reconstrução e origem | 24 | 24 |
| Sem ajuste identificado entre as reconstruídas | 7.666 | 7.509 |

São 4.509 linhas para revisão, sem abertura de lote corretivo nesta etapa. 3.612 contêm adicionais bloqueadas (3.555 publicadas); as categorias de problema podem se sobrepor. As 3.284 linhas com Cruzamento preciso bloqueado já têm Passe em profundidade, nativo ou adicional, nos casos reconstruídos: não existe troca direta livre por essa gêmea.

Este levantamento não reotimizou nem gravou os resultados antigos e não retirou publicações. As 55.151 publicações existentes foram preservadas. Uma linha apta a retirar habilidade sem perder nota do motor ainda exige conferir normalização e bônus antes de gravar. Dados incompletos/divergentes não são candidatos a correção cega.

## Verificação obrigatória em alterações futuras

Conferir matriz/política no banco, casos manuais de ganho zero e saturação, preservação das nativas, filtragem de gêmeas e liberdade do seletor pessoal. Validar runtime compilado e fotografias com o mesmo hash. Testar a ordem dos lotes e os recibos existentes. Registrar o estado real de cada máquina; não confundir arquivo pronto com instalação ou publicação.

Testes: `../TESTES/teste_habilidades_sem_ganho_v12.py`, `teste_pacote_volta_marcar_v1.py`, `teste_prioridade_orcamento_v1.py`, `teste_operacao_local_json.py` e demais verificações de fórmula/ímpetos. Migrações aplicadas: `20260909063652` e `20260909063910`; SQL e política ficam nesta pasta.

## Matriz completa de exclusões automáticas

| Função | Habilidades bloqueadas (nome e ID) |
|---|---|
| Centroavante fixo (1) | Cruzamento preciso [34], Reposição baixa do GO [44], Reposição alta do GO [45], Arremesso lateral longo [46], Arremesso longo do GO [47], Pegador de pênaltis [49], Marcação individual [55], Volta para marcar [56], Interceptação [57], Bloqueador [58], Carrinho [60], Afastamento acrobático [64], Comandante da defesa (GO) [1716], Grito Motivacional (GO) [2101] |
| Centroavante móvel (2) | Cruzamento preciso [34], Reposição baixa do GO [44], Reposição alta do GO [45], Arremesso lateral longo [46], Arremesso longo do GO [47], Pegador de pênaltis [49], Marcação individual [55], Volta para marcar [56], Interceptação [57], Bloqueador [58], Carrinho [60], Afastamento acrobático [64], Comandante da defesa (GO) [1716], Grito Motivacional (GO) [2101] |
| Falso nove (3) | Cruzamento preciso [34], Reposição baixa do GO [44], Reposição alta do GO [45], Arremesso lateral longo [46], Arremesso longo do GO [47], Pegador de pênaltis [49], Marcação individual [55], Interceptação [57], Bloqueador [58], Carrinho [60], Afastamento acrobático [64], Comandante da defesa (GO) [1716], Grito Motivacional (GO) [2101] |
| Goleiro defensivo (4) | Pedalada simples [0], Toque duplo [1], Elástico [2], Giro 360° [3], Chapéu [4], Corte com virada [5], Puxada de letra [6], Finta de letra [7], Controle com a sola [10], Cabeçada [15], Efeito de longe [17], Controle da cavadinha [19], Chute com o peito do pé [20], Folha seca [21], Chute ascendente [22], Precisão à distância [23], Finalização acrobática [26], Toque de calcanhar [27], Chute de primeira [28], Cruzamento preciso [34], Curva para fora [36], De letra [37], Passe sem olhar [38], Arremesso lateral longo [46], Especialista em pênalti [48], Malícia [54], Marcação individual [55], Volta para marcar [56], Interceptação [57], Bloqueador [58], Superioridade aérea [59], Carrinho [60] |
| Goleiro ofensivo (5) | Pedalada simples [0], Toque duplo [1], Elástico [2], Giro 360° [3], Chapéu [4], Corte com virada [5], Puxada de letra [6], Finta de letra [7], Controle com a sola [10], Cabeçada [15], Efeito de longe [17], Controle da cavadinha [19], Chute com o peito do pé [20], Folha seca [21], Chute ascendente [22], Precisão à distância [23], Finalização acrobática [26], Toque de calcanhar [27], Chute de primeira [28], Cruzamento preciso [34], Curva para fora [36], De letra [37], Passe sem olhar [38], Arremesso lateral longo [46], Especialista em pênalti [48], Malícia [54], Marcação individual [55], Volta para marcar [56], Interceptação [57], Bloqueador [58], Superioridade aérea [59], Carrinho [60] |
| Lateral defensivo (6) | Pedalada simples [0], Toque duplo [1], Elástico [2], Giro 360° [3], Chapéu [4], Corte com virada [5], Puxada de letra [6], Finta de letra [7], Controle com a sola [10], Controle da cavadinha [19], Chute com o peito do pé [20], De letra [37], Reposição baixa do GO [44], Reposição alta do GO [45], Arremesso longo do GO [47], Pegador de pênaltis [49], Volta para marcar [56], Comandante da defesa (GO) [1716], Grito Motivacional (GO) [2101] |
| Lateral ofensivo (7) | Cabeçada [15], Controle da cavadinha [19], Chute com o peito do pé [20], De letra [37], Reposição baixa do GO [44], Reposição alta do GO [45], Arremesso longo do GO [47], Pegador de pênaltis [49], Volta para marcar [56], Comandante da defesa (GO) [1716], Grito Motivacional (GO) [2101] |
| Meia ofensivo (8) | Cabeçada [15], Controle da cavadinha [19], Cruzamento preciso [34], Reposição baixa do GO [44], Reposição alta do GO [45], Arremesso lateral longo [46], Arremesso longo do GO [47], Pegador de pênaltis [49], Carrinho [60], Afastamento acrobático [64], Comandante da defesa (GO) [1716], Grito Motivacional (GO) [2101] |
| Atacante infiltrador (9) | Cabeçada [15], Controle da cavadinha [19], Cruzamento preciso [34], Reposição baixa do GO [44], Reposição alta do GO [45], Arremesso lateral longo [46], Arremesso longo do GO [47], Pegador de pênaltis [49], Marcação individual [55], Interceptação [57], Bloqueador [58], Carrinho [60], Afastamento acrobático [64], Comandante da defesa (GO) [1716], Grito Motivacional (GO) [2101] |
| Meia armador (10) | Cabeçada [15], Controle da cavadinha [19], Cruzamento preciso [34], Reposição baixa do GO [44], Reposição alta do GO [45], Arremesso lateral longo [46], Arremesso longo do GO [47], Pegador de pênaltis [49], Volta para marcar [56], Comandante da defesa (GO) [1716], Grito Motivacional (GO) [2101] |
| Meia de arranque (11) | Cabeçada [15], Controle da cavadinha [19], Cruzamento preciso [34], Reposição baixa do GO [44], Reposição alta do GO [45], Arremesso lateral longo [46], Arremesso longo do GO [47], Pegador de pênaltis [49], Volta para marcar [56], Comandante da defesa (GO) [1716], Grito Motivacional (GO) [2101] |
| Ala driblador (12) | Chapéu [4], Cabeçada [15], Controle da cavadinha [19], Reposição baixa do GO [44], Reposição alta do GO [45], Arremesso longo do GO [47], Pegador de pênaltis [49], Afastamento acrobático [64], Comandante da defesa (GO) [1716], Grito Motivacional (GO) [2101] |
| Ala cruzador (13) | Chapéu [4], Cabeçada [15], Controle da cavadinha [19], Reposição baixa do GO [44], Reposição alta do GO [45], Arremesso longo do GO [47], Pegador de pênaltis [49], Afastamento acrobático [64], Comandante da defesa (GO) [1716], Grito Motivacional (GO) [2101] |
| Atacante criador (14) | Cabeçada [15], Controle da cavadinha [19], Reposição baixa do GO [44], Reposição alta do GO [45], Arremesso longo do GO [47], Pegador de pênaltis [49], Marcação individual [55], Interceptação [57], Bloqueador [58], Superioridade aérea [59], Carrinho [60], Afastamento acrobático [64], Comandante da defesa (GO) [1716], Grito Motivacional (GO) [2101] |
| Atacante driblador (15) | Cabeçada [15], Controle da cavadinha [19], Reposição baixa do GO [44], Reposição alta do GO [45], Arremesso longo do GO [47], Pegador de pênaltis [49], Marcação individual [55], Interceptação [57], Bloqueador [58], Superioridade aérea [59], Carrinho [60], Afastamento acrobático [64], Comandante da defesa (GO) [1716], Grito Motivacional (GO) [2101] |
| Volante de construção (16) | Controle da cavadinha [19], Finalização acrobática [26], Cruzamento preciso [34], De letra [37], Reposição baixa do GO [44], Reposição alta do GO [45], Arremesso lateral longo [46], Arremesso longo do GO [47], Pegador de pênaltis [49], Volta para marcar [56], Comandante da defesa (GO) [1716], Grito Motivacional (GO) [2101] |
| Volante de contenção (17) | Pedalada simples [0], Toque duplo [1], Elástico [2], Giro 360° [3], Chapéu [4], Corte com virada [5], Puxada de letra [6], Finta de letra [7], Controle com a sola [10], Controle da cavadinha [19], Finalização acrobática [26], Toque de calcanhar [27], Cruzamento preciso [34], De letra [37], Passe sem olhar [38], Reposição baixa do GO [44], Reposição alta do GO [45], Arremesso lateral longo [46], Arremesso longo do GO [47], Pegador de pênaltis [49], Volta para marcar [56], Comandante da defesa (GO) [1716], Grito Motivacional (GO) [2101] |
| Zagueiro de combate (18) | Pedalada simples [0], Toque duplo [1], Elástico [2], Giro 360° [3], Chapéu [4], Corte com virada [5], Puxada de letra [6], Finta de letra [7], Controle com a sola [10], Efeito de longe [17], Controle da cavadinha [19], Chute com o peito do pé [20], Folha seca [21], Chute ascendente [22], Precisão à distância [23], Finalização acrobática [26], Chute de primeira [28], Cruzamento preciso [34], De letra [37], Passe sem olhar [38], Reposição baixa do GO [44], Reposição alta do GO [45], Arremesso lateral longo [46], Arremesso longo do GO [47], Pegador de pênaltis [49], Malícia [54], Volta para marcar [56], Comandante da defesa (GO) [1716], Grito Motivacional (GO) [2101] |
| Zagueiro de saída (19) | Pedalada simples [0], Toque duplo [1], Elástico [2], Giro 360° [3], Chapéu [4], Corte com virada [5], Puxada de letra [6], Finta de letra [7], Controle com a sola [10], Efeito de longe [17], Controle da cavadinha [19], Chute com o peito do pé [20], Folha seca [21], Chute ascendente [22], Precisão à distância [23], Finalização acrobática [26], Chute de primeira [28], Cruzamento preciso [34], De letra [37], Passe sem olhar [38], Reposição baixa do GO [44], Reposição alta do GO [45], Arremesso lateral longo [46], Arremesso longo do GO [47], Pegador de pênaltis [49], Malícia [54], Volta para marcar [56], Comandante da defesa (GO) [1716], Grito Motivacional (GO) [2101] |
