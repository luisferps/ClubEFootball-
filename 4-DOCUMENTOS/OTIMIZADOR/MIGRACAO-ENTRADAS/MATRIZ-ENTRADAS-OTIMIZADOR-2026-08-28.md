# Matriz de entradas do Otimizador — 28/08/2026

Escopo: substituição de consumidores. Fórmula, fila produtiva, gravação de builds,
Extrator e dados do jogo não fazem parte desta troca. A fórmula vigente continua:
`barras com teto 99 → proficiência com piso 40/teto 99 → boost → ímpetos`.

## Legenda dos gates

- **MIGRADO**: consumidor local/serviço trocado para o contrato v1 por IDs, com
  auditoria anterior e posterior verde.
- **JÁ NOVO**: a leitura atual já chega de `clube_novo`.
- **BLOQUEADO**: há estrutura nova, mas o contrato não está apto ou não é completo.
- **MANTER OPERACIONAL**: regra/estado do próprio sistema, sem substituto físico em
  `clube_novo`; não é dado do jogo a ser migrado.
- **FORA DESTA ATIVAÇÃO**: a fonte nova pode ser exposta para auditoria, mas nenhum
  consumidor será ligado nesta etapa.

## Slots realmente consumidos

| slot do Otimizador | hoje pega em | chave e transformação atuais | consumidor | depois deve pegar em `clube_novo` | gate |
|---|---|---|---|---|---|
| identidade da carta | `public.carta_do_motor` → `clube.carta_jogo` | `card_id` textual; remove sufixo `@...` no cliente | lote, ficha e serviço | `carta_jogo.card_id`; nome anexado só para diagnóstico | MIGRADO por `otimizador_carta(s)_v1` |
| atributos-base (26) | `clube.carta_jogo.atributos` JSON → `public.atributos_na_ordem_da_casa` | array do editor reordenado para os 26 índices da equação | equação, régua, ranking e ficha | `carta_atributo_jogo.valor` + `atributo_jogo.codigo/bit`; ordem fixada pelos 26 bits físicos, nunca pelo nome nem por `idx_casa` isolado | MIGRADO; 26/26 e fingerprint validados |
| orçamento e evolução | `clube.carta_jogo.orcamento`, `level_cap`, `cap_estimado` | inteiros; `orcamento=0` desliga habilidades adicionais | busca de barras e ficha | `carta_jogo.orcamento`, `level_cap`, `cap_estimado` | MIGRADO; sem estimar valor ausente |
| overall | `clube.carta_jogo.overall` | inteiro de apresentação/ordenação | fila, ficha e ranking | `carta_jogo.overall` | MIGRADO |
| posição principal | `clube.carta_jogo.posicao` + `clube.posicao.sigla_jogo` | texto convertido para sigla legada | pool, regra de GO e ficha | `carta_posicao_principal_jogo(card_id,posicao_id)` → `posicao_jogo.id`; código/nome só para apresentação | MIGRADO; 43.072/43.072, sem ausência/ambiguidade; contrato ativo não compara texto |
| aptidões de posição | `clube.carta_jogo.aptidoes` JSON | objeto textual | ficha/serviço e regras de posição | `carta_posicao_jogo(card_id,posicao_id,nivel_aptidao)` + `posicao_jogo` | MIGRADO; exatamente 12 relações por carta |
| corpo (12 medidas usadas) | `clube.carta_jogo.corpo` JSON | lista posicional | `motor_bonus.py` e ficha | `carta_corpo_jogo` + `corpo_ordem`, somente `usado_pelo_motor=true`, em `pos` 0–11 | MIGRADO no contrato; consumidor de bônus continua separado/desligado |
| pé dominante | `clube.carta_jogo.pe` | rótulo `Direito`/`Esquerdo` | bônus/ficha | `carta_pe_jogo(card_id,campo,valor)` FK composta → `pe(campo,valor)`, campo físico `pe_dominante` | MIGRADO no contrato; 32.786/10.286 cartas; bônus separado continua desligado |
| uso e precisão do pé ruim | colunas numéricas de `clube.carta_jogo` | par `[uso,precisão]` | bônus/ficha | duas relações em `carta_pe_jogo`, FKs compostas para `pe_ruim_uso` e `pe_ruim_precisao` | MIGRADO no contrato; 43.072 × 2 valores, zero falta; bônus separado continua desligado |
| altura, peso, idade, lesão e forma | colunas de `clube.carta_jogo` | campos escalares | bônus/ficha | colunas homônimas de `carta_jogo`; sem casamento textual | MIGRADO no contrato; bônus separado continua desligado |
| habilidades nativas | JSON `clube.carta_jogo.habilidades` casado por nome em `clube.habilidade` | separa comum/rara e devolve rótulos; equação indexava por nome | pool, efeitos e ficha | `carta_habilidade_jogo.skill_id` + `habilidade_jogo`; rótulo só como apresentação | MIGRADO por `skill_id`; habilidade bloqueada trava a carta |
| efeitos das habilidades | `clube.habilidade.efeito` | dicionário por rótulo e índice 0–25 | `equacao.py` | `habilidade_jogo.efeito`, relacionado por `skill_id` | MIGRADO; 65 habilidades usadas aptas e efeitos presentes; nenhum adaptador textual ativo |
| tipo comum/rara da habilidade | `clube.habilidade.tipo` | comum entra no pool; rara soma como fixa | motor/lote | `habilidade_jogo.tipo`; contrato traduz `especial` para o valor de compatibilidade `rara`, preservando o ID/tipo canônico | MIGRADO com cardinalidade validada |
| vetadas e restrição GO/linha | duas listas codificadas + inferência pela base | rótulo textual | composição do pool | `habilidade_jogo.vetada`, `so_goleiro`, `so_de_linha` | MIGRADO por `skill_id`, sem inferir pela distribuição das cartas |
| bloqueio habilidade × função | `clube.bloqueio` (246 relações) via `regua_bonus` | `funcao_codigo` + nome da habilidade | composição do pool | relação normalizada `habilidade_funcao_bloqueio_otimizador(skill_id,funcao_id)` com FKs | MIGRADO: 246/246 por bit físico + função canônica, sem ambiguidade; array textual não é consumido |
| incidência da comunidade | arquivo local `encaixe_B_v171_datas_tela.html`, se existir; hoje a cópia operacional não contém o arquivo e retorna `{}` | `const FILA`, função e nome; só desempata | `roda_lote_v6._fila_incid` | relação normalizada `habilidade_funcao_incidencia_otimizador(skill_id,funcao_id,incidencia_pct)` | MIGRADO: 711 chaves estáveis; 38 linhas da função histórica não consumida continuam documentadas e não criam 20.ª função |
| estilo IA | JSON `clube.carta_jogo.estilos_ia` | lista textual | bônus/ficha | `carta_estilo_ia_jogo.bit_estilo_ia` + `estilo_ia_jogo` | MIGRADO no contrato por bit e fingerprint; bônus separado continua desligado |
| estilo ofensivo/defensivo da carta | números brutos em `clube.carta_jogo` + catálogos legados; nomes viram `modelo/modelo2` | ofensivo armazena bit; defensivo armazena índice | `motor_bonus.py` | `carta_playstyle_jogo(card_id,slot_fisico,playstyle_id)` FK → `playstyle.id_jogo`; `valor_raw` fica só como proveniência | IDENTIDADE MIGRADA: dois slots em 43.072/43.072; regras de bônus por nome continuam BLOQUEADAS e não são executadas |
| ímpetos equipados | `clube.carta_jogo.impeto_*` + `clube.impeto` + `clube.impeto_efeito` | IDs legados viram nomes e pares `[atributo,delta]` | equação e ficha | `carta_impeto_jogo` + `impeto_jogo` + `impeto_atributo_jogo` | FORA DESTA ATIVAÇÃO: 440/440 ímpetos com `pode_rodar=false`; carta com qualquer slot fica fail-closed |
| condição/faixa/alvo de ímpeto | legado mistura flag e efeito; não implementa toda a estrutura física | condição tratada por listas e degraus | lote | `impeto_condicao_*`, membros de liga, classes e faixas normalizadas | FORA DESTA ATIVAÇÃO: consumidor deliberadamente desligado; não contar argentinos nem ligar faixa nesta etapa |
| vaga/fabricação de ímpeto | `clube.impeto_fabricavel` | lista de candidatos por slot | `motor.py.CAT` | existe estrutura de slots/receitas, mas nenhum catálogo apto | FORA DESTA ATIVAÇÃO: contrato novo devolve catálogo vazio e gate desligado, sem fallback |
| nacionalidade da carta | texto/JSON legado e campos não normalizados | rótulo | ficha e futura condição de ímpeto | `carta_jogo.codigo_nacionalidade` FK → `nacionalidade_jogo.codigo_jogo` | MIGRADO no contrato; consumidor de condição continua desligado |
| clube da carta | fontes legadas/embutidas | rótulo ou ausência | ficha e futura condição | `carta_jogo.codigo_clube` FK → `clube_jogo.codigo_jogo` | MIGRADO no contrato; `pode_rodar_vinculos` é respeitado e cartas incompletas ficam fail-closed |
| liga da carta | fontes legadas/embutidas | rótulo ou ausência | ficha e futura condição | `carta_jogo.codigo_liga` FK → `liga_jogo.codigo_jogo` | MIGRADO no contrato; consumidor de condição continua desligado |
| tipo da carta | `clube.carta_jogo.tipo`/rótulos | texto | ficha/ranking | `carta_jogo.tipo_carta_id` FK → `tipo_carta_jogo` | MIGRADO no contrato; 4/0 e 7/0 continuam provisórios |
| técnicos: identidade | `regua_pacote`, já lendo `clube_novo.tecnico_jogo` | ID Konami; somente `pode_rodar` | equação, lote e serviço | mesma tabela pelo contrato versionado | MIGRADO da porta antiga para `otimizador_regua_v1`; dado já era novo |
| técnicos: proficiências | `regua_pacote` → `tecnico_estilo_jogo` | maior valor; empates preservam estilos gêmeos | multiplicador | mesma relação e `tecnico_estilo_principal_jogo` | JÁ NOVO; valores continuam numéricos e fórmula fica congelada |
| técnicos: boosts | `regua_pacote` → `tecnico_atributo_jogo` + `atributo_jogo.idx_casa` | convertia por índice incompatível | equação | mesma relação, mapeada por `atributo_ordem_otimizador`/bit físico ao índice da equação | MIGRADO/CORRIGIDO; 104 boosts, Capello `[6,10]`, Conte preservado |
| textos e rótulos canônicos | misto de nomes embutidos, catálogos legados e JSON | casamento textual | ficha, pool e tela | catálogos novos e `texto_do_jogo` pelas chaves oficiais | MIGRADO apenas como apresentação no lote/serviço; réplicas de tela continuam não migradas; texto nunca substitui FK/gate |
| molde de função | `clube.molde` | `funcao_codigo`, índice 0–25, alvo e peso | régua/ranking | sem equivalente físico comprovado em `clube_novo` | MANTER OPERACIONAL; é regra do Otimizador, não dado do jogo |
| parâmetros da régua | `clube.regua_parametro` | chave/valor | nota | sem equivalente físico comprovado | MANTER OPERACIONAL |
| barras e custo de nível | `clube.barra`, `clube.custo_nivel` | índices e acumulado | busca | sem equivalente novo | MANTER OPERACIONAL |
| multiplicadores de proficiência | `clube.multiplicador` | ponto → decimal | fórmula | sem equivalente novo | MANTER OPERACIONAL; não alterar valores nem casts |
| ordem de boost compatível | `clube.ordem_boost_tecnico` | posição antiga → índice | adaptador de técnico | contrato usa `atributo_ordem_otimizador` e o bit/código canônico | MIGRADO; tabela antiga fica só como compatibilidade não consumida |
| regras de bônus de corpo/estilo | `regua_bonus`: `bonus_parametro`, `molde_corpo`, `estilo_regra`, `posicao_slot`, `sa_familia` etc. | tabelas operacionais legadas | `motor_bonus.py` | não há pacote novo completo e comprovado | MANTER/BLOQUEADO; não migrar nem executar bônus produtivo |
| fila, prioridade e carimbo | `clube.fila`, RPCs `cartas_da_fila`, `proxima_da_fila`, `estado_da_fila`, `peso_da_ordem` | `card_id+funcao`, prioridade e estado | lote | sem substituto físico; `otimizador_proxima_fila_v1` traduz a fronteira para `funcao_id` e `otimizador_peso_ordem_v1` mantém o estado operacional | MANTER OPERACIONAL por contrato v1; conteúdo não migra |
| gravação de build | `clube.build` por `gravar_build` | saída do cálculo | ranking/ficha | sem substituto autorizado; é saída, não entrada física | MANTER OPERACIONAL; nenhum lote produtivo nesta migração |
| pool histórico por função | `clube.build.falta_pool` via `pool_da_funcao` | `card_id+funcao` | serviço de avaliação | não é catálogo físico; fotografia da rodada | MANTER OPERACIONAL, sem tratá-lo como fonte canônica de habilidade |
| ficha/ranking/escalação publicados | views/RPCs legados sobre builds (`tela_encaixe`, `casa_lista`, correlatos) | resultados já gravados | UI | não são entradas da equação e não devem mudar nesta etapa | FORA DESTA MIGRAÇÃO |

## Contrato aprovado para a troca

1. `public.otimizador_carta_v1(card_id)` e versão em lote leem somente relações e
   catálogos de `clube_novo` para dados da carta.
2. `public.otimizador_regua_v1()` identifica a proveniência de cada bloco. Dados do
   jogo aptos vêm de `clube_novo`; regras internas continuam nas tabelas operacionais.
3. Ímpetos/condições são expostos apenas como metadados de bloqueio. Efeitos,
   fabricação e ativação retornam desligados.
4. O cliente usa exclusivamente as novas RPCs para esses slots, com `service_role`;
   não existe acesso direto da UI ao schema privado nem fallback silencioso.
5. Uma carta só passa se os gates estruturais, as FKs, as cardinalidades e todos os
   catálogos consumidos estiverem aptos.
6. Cálculo, join, filtro e comparação usam `skill_id`, `funcao_id`, IDs de posição,
   bits/códigos físicos de atributo e as FKs canônicas. Nome só é apresentação. A
   tradução do contrato antigo fica isolada na migração e nunca vira chave nova.

## Resultado da substituição

O lote local e a cópia local do serviço usam o contrato v1 sem fallback silencioso.
A auditoria cobriu 43.072 cartas: 42.803 também existiam na fotografia antiga, 269
são adições físicas do jogo e 34 tiveram alteração física. As 84 diferenças de campo
nas 34 cartas correspondem integralmente ao manifesto selado do Extrator; depois
dessa classificação há zero divergência técnica pendente.

As três réplicas de UI continuam deliberadamente **não migradas**. Elas têm catálogos
embutidos e acessam a projeção pública histórica, enquanto a pasta local do serviço
não prova qual implantação está publicada. Expor `clube_novo` ou uma chave privada ao
navegador seria inválido. A migração ponta a ponta exige primeiro um endpoint seguro
implantado que entregue esses mesmos IDs; até lá, as telas foram preservadas byte a
byte e não contam como consumidor migrado.

## Exemplos de jogo

- **Messi `89138556575063`:** o contrato o localiza por `card_id`, monta os 26
  atributos pelas relações físicas e encontra suas habilidades/posições por IDs.
  Hoje ele contém habilidade e ímpetos ainda bloqueados no modelo novo; portanto é
  amostra de auditoria e de fórmula, não carta liberada para lote migrado.
- **Contagem de argentinos para Ímpeto:** a nacionalidade física é acessível por FK,
  mas a condição/faixa permanece desligada. O Otimizador não conta nem soma o efeito.
- **Capello `17601312850052`:** identidade, cinco proficiências e boosts vêm das
  relações canônicas. O contrato deve preservar `46/89/57/89/64`, empate principal
  e gêmeo, e boosts canônicos `[6,10]`; a fórmula vigente não é alterada.
- **Conte `17609097478250`:** a relação de Sobreposição 96 deve continuar sendo a
  maior proficiência, sem inventar relação para os demais técnicos.
