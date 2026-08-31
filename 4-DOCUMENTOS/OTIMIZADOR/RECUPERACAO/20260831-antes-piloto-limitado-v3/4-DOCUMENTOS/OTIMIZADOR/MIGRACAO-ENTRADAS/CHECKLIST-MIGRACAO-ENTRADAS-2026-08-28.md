# Checklist oficial — migração de entradas do Otimizador

Data: 28/08/2026. Estado inicial: **não ativado em produção**.

## Regra imutável desta frente

- [x] fórmula vigente identificada e excluída dos hunks;
- [x] trava global: nenhum hunk pode alterar fórmula matemática, peso, ordem de
  cálculo, composição de molde ou regra de negócio; só endereço/chave de entrada
  pode mudar, com paridade obrigatória antes/depois;
- [x] nenhum lote produtivo será executado;
- [x] nenhum dado do jogo, Extrator ou schema legado será reescrito;
- [x] `clube_novo` continua privado e a UI não recebe acesso direto;
- [x] Ímpetos/condições continuam desligados.

## Recuperação

- [x] snapshot anterior criado em
  `4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/2026-08-28-ANTES-MIGRACAO-ENTRADAS`;
- [x] ZIP: SHA-256
  `83EA38FC52B01EF971B8DB588C1C554D1F82A61A79AD802C35824790C7977ACD`;
- [x] manifesto: SHA-256
  `3C4EAF4987BE893C4F0E3154B8ACD8C59CB88A6D9C1E547A05EF8AF2144FFAC3`;
- [x] patch do worktree anterior: SHA-256
  `88A7B33AD3115D0DE82C8FE332E3DA8C8E60F34F2904326B5DAF46969CC4311F`;
- [x] rollback SQL das identidades de carta revisado antes da migração;
- [x] segundo snapshot imediatamente antes dos hunks de consumidor em
  `4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/2026-08-28-ANTES-HUNKS-CONSUMIDORES.zip`,
  SHA-256 `CBE75C5836B7B9E183E5E911758B225AD3E515397C17BEA17841B02A7B42CB9E`;

## Auditoria pronta antes da troca

- [x] matriz antiga → significado → fonte nova → gate registrada;
- [x] comparador independente especificado por `card_id` e campo;
- [x] fingerprints determinísticos de listas/objetos especificados;
- [x] cardinalidades de atributos, corpo, posições, habilidades, IA e ímpetos
  entram no relatório;
- [x] divergência deve registrar origem antiga, origem nova e os dois valores;
- [x] ausência da RPC nova é falha explícita, nunca fallback;
- [x] testes unitários do comparador verdes: 8/8, incluindo cardinalidade e
  invariância de cálculo após renomear todos os rótulos de apresentação;
- [x] execução inicial registrou `otimizador_cartas_v1` ausente com HTTP 404 e
  mensagem `sem fallback` antes do DDL;
- [x] execução pós-DDL validada com Messi, uma carta apta sem ímpeto, Capello e Conte;
- [x] comparação total das 43.072 cartas classifica cada diferença como prova,
  correção ou bloqueio.

## Gates físicos lidos antes da troca

- [x] 43.072 cartas no modelo novo;
- [x] 26 atributos por carta e 12 relações de corpo/posição por carta;
- [x] 354 cartas com `pode_rodar_vinculos=false` permanecem recusadas;
- [x] tipos 4/0 e 7/0 preservam `tipo_provisorio=true`;
- [x] 1.478 técnicos atuais aptos; 116 históricos bloqueados;
- [x] 440/440 ímpetos com `pode_rodar=false`: consumidor desligado;
- [x] habilidade bloqueada em qualquer relação trava a carta;
- [x] causa das 200 incidências ausentes localizada: projeção por rótulo em nove
  habilidades; 1.139/1.139 traduzem sem ambiguidade por bit físico → `skill_id`;
- [x] 1.101 linhas de incidência dos 19 tipos ativos colapsam, sem conflito, em
  711 relações canônicas; 38 pertencem a uma função histórica fora do catálogo
  operacional e não serão inventadas como nova função;
- [x] as 246 regras de bloqueio traduzem sem ambiguidade para `skill_id+funcao_id`;
- [x] duas habilidades usadas em cartas, IDs 17 e 33, promovidas com a equivalência
  física de bit e os efeitos operacionais conhecidos;
- [x] sete habilidades novas sem endereço em carta permanecem fora apenas após
  comprovar que nenhuma relação de carta as usa e registrar o limite físico;
- [x] nenhuma regra ativa de habilidade usa rótulo; teste de renomeação verde.

## Identidades físicas normalizadas antes do contrato

- [x] posição principal: 43.072/43.072 resolvem `codigo_en → posicao_jogo.id`,
  sem ausência, ambiguidade ou catálogo bloqueado;
- [x] pé dominante: o legado novo contém somente `Direito` (32.786) e
  `Esquerdo` (10.286); a tradução única será materializada em FK composta e
  nunca executada pelo consumidor;
- [x] uso/precisão do pé ruim: 43.072/43.072 cobertos pelas chaves compostas
  de `pe`, zero valor fora do catálogo;
- [x] playstyle ofensivo: o número bruto é o bit físico; 43.072/43.072 resolvem
  para `playstyle.id_jogo`, zero ausência/ambiguidade/bloqueio;
- [x] playstyle defensivo: o número bruto é o índice físico; 43.072/43.072
  resolvem para `playstyle.id_jogo`, zero ausência/ambiguidade/bloqueio;
- [x] auditoria pós-migração desenhada: 43.072 posições, 129.216 relações de pé
  e 86.144 relações de playstyle, com FKs, cardinalidade por carta e comparação
  independente contra os valores brutos;
- [x] relações normalizadas aplicadas: 43.072 posições, 129.216 relações de pé e
  86.144 relações de playstyle;
- [x] comparação pós-DDL: zero divergência contra os valores físicos/brutos e
  zero cardinalidade inválida por carta;
- [x] seis FKs presentes, RLS ativo, três políticas de leitura exclusivas para
  `service_role`, zero privilégio de tabela para `PUBLIC`/`anon`/`authenticated`;
- [x] advisory de segurança sem ocorrência para as três tabelas novas após as
  políticas; avisos preexistentes e fora do escopo não foram alterados.

## Banco — contrato versionado

- [x] plano pós-DDL preparado antes da troca: readback de função/ACL, 26 IDs de
  atributo, 19 funções × 26 linhas de molde, 65 habilidades usadas aptas,
  1.478 técnicos aptos e amostras Messi/Capello/Conte;
- [x] contrato definido para retornar somente `skill_id`, `funcao_id`,
  `posicao_id`, `playstyle_id`, bits/códigos físicos e FKs nos blocos de cálculo;
- [x] compatibilidade textual isolada no bloco `compatibilidade_legado`, consumido
  apenas pelo comparador e nunca pelo Otimizador;
- [x] SQL local revisado contém criação e rollback;
- [x] DDL aplicado por migração, de forma transacional;
- [x] funções com `search_path=''` e objetos totalmente qualificados;
- [x] `anon` e `authenticated` sem `EXECUTE`;
- [x] `service_role` com somente os grants necessários;
- [x] readback de definições, ACLs e cardinalidades;
- [x] advisory de segurança conferido após o DDL: zero ocorrência relacionada ao
  contrato novo; 130 avisos preexistentes e fora do escopo permaneceram intocados;
- [x] funções antigas preservadas somente para sombra/auditoria e não chamadas pelos
  consumidores migrados.

## Consumidores

- [x] `2-MOTORES/OTIMIZADOR/fonte_unica.py` usa exclusivamente `otimizador_*_v1` nos slots
  migrados;
- [x] habilidades atravessam carta, pool, efeito, bloqueio e incidência por
  `skill_id`; rótulo é anexado somente na saída;
- [x] `2-MOTORES/OTIMIZADOR/roda_lote_v6.py` não contém fallback ativo para arquivo/HTML nos
  slots migrados;
- [x] `2-MOTORES/OTIMIZADOR/travas.py` recusa o gate devolvido pelo contrato;
- [x] `2-MOTORES/OTIMIZADOR/motor.py` recebe catálogo de Ímpetos vazio sem ler legado;
- [x] serviço Railway local usa o mesmo contrato v1 de carta/régua;
- [x] réplicas de UI auditadas e preservadas byte a byte: continuam não migradas,
  pois não existe endpoint implantado e comprovado que lhes entregue IDs canônicos
  sem expor `clube_novo`; nenhuma troca insegura foi feita;
- [x] `2-MOTORES/BONIFICADOR/motor_bonus.py` permanece fora até existir equivalência completa das regras;
- [x] fila e gravação continuam operacionais/legadas, sem lote produtivo; a fila é
  lida pela ponte v1 por `funcao_id` e `gravar_build` permanece somente como saída.

## Paridade e não regressão

- [x] fingerprint por coleção e cardinalidade por carta;
- [x] diferenças da fotografia física nova classificadas e não ocultadas: 269 cartas
  somente novas e 34 alteradas coincidem exatamente com a extração física selada;
  84/84 campos antigos/novos correspondem ao antes/depois físico após a permutação
  comprovada de atributos e a tradução de posições por IDs;
- [x] nenhuma chamada ativa a `carta_do_motor`, `cartas_do_motor`,
  `carta_para_simular` ou `regua_pacote` nos consumidores migrados;
- [x] as únicas chamadas antigas remanescentes estão nos comparadores independentes
  `auditar_entradas_v1.py`/`auditar_moldes_v1.py` e não no caminho de execução;
- [x] fórmula Python local, serviço e três réplicas de tela continuam concordando;
- [x] Messi 99 + Capello 89/+1 + Precisão +4 continua 104 no teste de fórmula
  (teste da fórmula, não gate de entrada);
- [x] Capello preserva estilos gêmeos e boosts `[6,10]`;
- [x] Conte preserva Sobreposição 96;
- [x] 17/17 testes permanentes verdes e todos os módulos Python tocados compilam;
- [x] auditoria não executa `gravar_build` nem altera fila/build.

## Gate que permanece fechado

- [ ] migração ponta a ponta das réplicas de UI: depende de um endpoint de serviço
  efetivamente implantado, identificado e testável que devolva o contrato por IDs.
  A pasta `6-AVALIADOR-NO-RAILWAY` declara que sua cópia não prova o serviço hoje
  publicado. Até essa prova/implantação separada, a UI não deve receber chave privada,
  acessar `clube_novo` diretamente nem reimplementar os catálogos por nome.

## Auditoria de cadeia satélite

- [x] lançadores `RODAR-O-MOTOR.bat` e `RODAR-TUDO.bat` rastreados até
  `roda_lote_v6.py`; `CONFERIR-UMA-LINHA.bat` rastreado até a mesma fonte v1;
- [x] lote, fonte única, equação, régua, busca, travas, fila e gravador foram
  analisados por import/chamada/RPC; nenhum leitor de entrada legado/fallback ficou
  alcançável no caminho do lote;
- [x] `app.py` confirmado como único entrypoint local do `Procfile`; banco, régua,
  avaliador e otimizador do serviço local usam IDs e RPCs v1;
- [x] `servidor.py`, `motor-no-servidor.js`, `funcao_nativa.py` e
  `regras_do_card.py` classificados: não são alcançados pelos lançadores, HTML atual
  ou `Procfile`; o adaptador de navegador antigo é incompatível e não conta como
  fallback ativo;
- [x] `grava_direto.py` classificado como escritor histórico sem payload na rota
  atual; `gravar_build` permanece saída histórica, jamais entrada/fallback;
- [x] oito scripts carregados pela UI e as duas réplicas foram rastreados; há leitura
  de `casa_lista`, `casa_arows`, `bonus_posicao` e catálogos embutidos, portanto a
  UI permanece não migrada e não pode ser declarada pronta;
- [x] matriz e plano de paridade por elo registrados em
  `AUDITORIA-CADEIA-SATELITES-2026-08-28.md`;
- [x] Manual oficial atualizado com a cadeia, contratos, gates, paridade e rollback;
- [x] executável local do Otimizador criado em `2-MOTORES/OTIMIZADOR/`: navegador
  fala só com servidor `127.0.0.1`; Individual usa `otimizador_regua_v1` e
  `otimizador_carta_v1`, e Fila usa apenas os RPCs v1 selados do lote de teste;
- [x] interface local escolhe carta, função e técnico por IDs canônicos, executa o
  cálculo Python aprovado e exibe entradas, resultado, gates e cardinalidades;
- [x] botão de paridade compara a equação legível ao cálculo inline; escrita geral,
  lote produtivo e Ímpetos condicionais permanecem recusados/desligados;
- [x] smoke test de HTTP local, compilação do executável e bootstrap de saúde pela
  configuração operacional concluídos sem escrita;
- [x] consulta real de Messi `89138556575063`/função `2`/Capello
  `17601312850052` recusada explicitamente pelo gate
  `impetos_consumidor_desligado`, sem fallback ou escrita;
- [x] executável reorganizado em uma única interface com abas **Fila automatizada**,
  **Teste unitário** e **Resultados**; Individual foi preservado;
- [x] Fila/Resultados ligados ao contrato real do lote selado
  `912c518e-091c-4583-ae91-97b3e717517e`: 100 cartas, 896 linhas e fingerprint
  `026fbb…a0dc`; a ponte rejeita ID, fingerprint, modo, publicação, contagem, estado
  ou `acoes` incompatíveis e não cria mock/fallback;
- [x] controles **Iniciar**, **Pausar**, **Parar** e **Abrir console** habilitados
  exclusivamente por `acoes` do status V8. Iniciar/retomar usa só pendências do
  mesmo `lote_id`; Pausar preserva pendências depois da linha atômica;
- [x] **Parar** usa somente `otimizador_controlar_lote_teste_v2` com
  `p_confirmado=true` após confirmação explícita da UI. Sem confirmação, a ponte
  recusa HTTP 409; o contrato passa por `encerrando`, preserva concluídas e marca
  pendências como `interrompido`, sem remoção ou publicação;
- [x] gate de pausa atômica fechado pela V7: a definição física de
  `otimizador_iniciar_linha_teste_v1` condiciona o mesmo `UPDATE` a
  `lote_estado='rodando'`. Readback confirmou `gate_fisico_presente=true`; com lote
  pausado, a tentativa na linha pendente 925 devolveu `false`, sem iniciar linha
  (`processando=0`, `concluidas=1`, `pendentes=895`). Migração e rollback estão em
  `MIGRACAO-FILA-TESTE-100-PAUSA-ATOMICA-V7.sql` e
  `ROLLBACK-FILA-TESTE-100-PAUSA-ATOMICA-V7.sql`;
- [x] leitura real em loopback conferiu lote pausado, 100 cartas, 896 linhas, uma
  concluída, 895 pendentes, zero publicação, 896 eventos e um resultado; nenhum
  comando de execução foi disparado durante a validação;
- [x] reteste V8 em loopback confirmou Individual/Fila/Resultados, contrato
  `otimizador_teste_100_v8`, ações/estados reais, 0 interrompidas e recusa de Parar
  sem confirmação (HTTP 409), preservando o lote real pausado com 895 pendentes;
- [x] projeção de leitura V9 da fila: `b1`/`pontuacao_final`, barras, técnico por
  ID, timestamps e `segundos` reais expostos por join FK de leitura, sem mudança de
  tabela, fórmula, lote, estado ou publicação; migration/rollback em
  `MIGRACAO-FILA-TESTE-LEITURA-RESULTADO-V9.sql` e
  `ROLLBACK-FILA-TESTE-LEITURA-RESULTADO-V9.sql`;
- [x] rótulos da interface resolvidos por IDs canônicos: carta por
  `otimizador_carta_v1`, função pela régua e posição pelo catálogo da carta; ID sem
  catálogo é explícito, sem fallback “não informado”;
- [x] prova visual/loopback após reinício do executável: linha 924 / carta 8538111
  mostra `8538111 · Welington Pauletto`, `Centroavante fixo`, `Centroavante`,
  b1 `-1253.3`, duração real `1 s` e resumo da build; lote preservado em pausa;
- [x] V10 acrescentou as habilidades adicionais persistidas por ID ao contrato de
  leitura; a UI as traduz pelo catálogo canônico e mantém a tabela compacta: barras
  são só a sequência numérica e rótulos/detalhes ficam no hover. Medição visual da
  linha 924: ~35 px de altura, sem quebra; migration/rollback V10 documentados;
- [x] V11 acrescentou somente a telemetria persistida `builds_comparadas`: cada
  unidade é uma candidata realmente comparada pelo executor da fila. O contador
  fica fora da fórmula; o selo do lote permaneceu
  `7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad`.
  Pausa segura confirmada antes da atualização: 203 concluídas, 693 pendentes,
  zero em processamento. Linhas históricas ficam nulas, sem estimativa;
  migration/rollback V11 documentados;
- [x] Resultados agora mantém a coluna própria **Build campeã**: cada concluída
  tem o atalho `Ver build campeã`, que abre somente barras, técnico, habilidades,
  pontuação e demais campos realmente expostos pelo resultado persistido. Tempo
  foi compactado sem remover frações reais (`1.31s`, `1m05s`); nenhum cálculo,
  banco, estado de fila ou publicação foi alterado;
- [ ] nenhuma troca adicional em satélite/UI antes de snapshot, endpoint implantado
  comprovado e auditoria de sombra recuperável por ID/campo.

## Fecho V16–V20 — 31/08/2026

- [x] snapshot recuperável criado antes da troca de gate:
  RECUPERACAO/20260831-antes-gate-dimensoes-v16/;
- [x] V16 criou carta, lote e pool V3, com SECURITY DEFINER, search_path vazio,
  execução só por service_role e rollback isolado;
- [x] a carta 105647068843182 (clube/liga físicos ausentes) passou no V3; a
  105553116303042, com vínculo físico inválido, continuou bloqueada;
- [x] V17 fez as três fábricas de fila selarem o fingerprint de
  otimizador_carta_v3; o lote V2 já concluído foi preservado, sem reexecução;
- [x] V18 confirmou 19 funções e 30 relações uma-a-uma, materializou
  clube_novo.otimizador_funcao_posicao com 2 FKs e RLS, e trocou o consumidor
  para funcao_id + posicao_id; zero divergências entre a relação e a tradução
  física/canônica de origem;
- [x] V19/V20 retiraram do service_role e do PUBLIC as portas históricas que
  liam/escreviam clube.fila ou clube.build; readback confirmou 10/10 sem execute;
- [x] consumidores ativos locais (fonte_unica.py, roda_lote_v6.py,
  interface/servidor.py), worker e banco.py do serviço usam carta/pool V3 e
  recusam versão inesperada; a régua permanece V2;
- [x] a auditoria de paridade passou a consultar ficha V3 e valida sua versão;
  a referência `cartas_do_motor` ficou restrita à comparação somente leitura e
  a opção de fila histórica agora falha explicitamente, sem chamar `clube.fila`;
- [x] fórmula, pesos, moldes, critérios de seleção e publicação não foram
  alterados; os testes de fórmula continuam independentes;
- [x] teste local completo: 35 testes verdes. Quando o ZIP histórico de
  28/08 não acompanha este checkout, a trava de arquivo do serviço compara o
  `HEAD` Git limpo (prova de que esta migração não o modificou), enquanto o
  cenário determinístico da fórmula continua independente. As duas réplicas
  datadas ausentes continuam apenas históricas e não foram recriadas no runtime;
- [x] executável elevado a interface 20260831-v21 para não aceitar processo V20
  como se fosse o código V3; snapshot pré-ativação em
  RECUPERACAO/20260831-antes-ativacao-v21/.

## Rollback

1. Repor somente os hunks de consumidor pelo patch/snapshot da etapa.
2. Revogar execução das RPCs v1 e removê-las com o rollback SQL versionado.
3. Não restaurar arquivos inteiros nem desfazer mudanças preexistentes do usuário.
4. Reexecutar os testes somente leitura e confirmar que fórmula, fila, builds e
   `clube_novo` não foram alterados.

## Fecho da frente de legado — V22 (31/08/2026)

- [x] snapshot recuperável pré-fecho criado em
  `RECUPERACAO/20260831-antes-fecho-legado-v22/`;
- [x] auditoria de entradas convertida para validar somente
  `otimizador_cartas_v3`; não recebe, compara ou consulta fonte histórica;
- [x] o lançador e a entrada histórica encerram antes de qualquer leitura de
  arquivo, RPC, worker ou escrita;
- [x] interface V22 removeu os contratos de fila V2 da lista permitida, não
  importa runner histórico e devolve estado explícito `aguardando_fila_v3`, com
  Iniciar/Pausar/Parar/Console recusados até contrato V3 autorizado;
- [x] executável V22 recompilado e aberto em validação controlada: saúde local
  retornou V22, fila/resultados indisponíveis, quatro ações desabilitadas e
  POST Iniciar recusado com HTTP 409; o servidor temporário foi encerrado e a
  porta 8767 ficou livre;
- [x] nenhuma migração de banco, criação de fila, execução de lote ou publicação
  foi disparada neste fecho;
- [ ] antes de uma fila operacional, exigir contrato V3 específico, autorizado e
  testado em `clube_novo`; não reabrir nenhum caminho histórico.

## Preparação da fila produtiva V3 — 31/08/2026

- [x] snapshot recuperável pré-V23 criado em
  `RECUPERACAO/20260831-antes-fila-producao-v23/`, com manifesto SHA-256;
- [x] migração e rollback V3 preparados em
  `FILA-PRODUCAO-V3/`; rollback falha fechado se um lote V3 existir;
- [x] contrato desenhado por IDs e FKs: lote, snapshot de carta, linha reservada
  e evento; browser usa somente servidor em loopback, sem credenciais;
- [x] criação preparada para todas as cartas aptas ordenadas por
  `overall DESC, card_id, funcao_id, posicao_id`; uma mesma fila V3 não é
  recriada silenciosamente;
- [x] cada reserva contém a fotografia V3 de carta e da régua; o worker não relê
  carta/régua durante o lote e recusa selo, gate ou Ímpeto condicional divergente;
- [x] conclusão preparada para gravar somente `build_otimizador` e fechar a
  linha por token de reserva, deixando Bonificador como etapa separada e sem
  publicação;
- [x] controles V23 preparados: Criar/Iniciar ou Retomar, Pausar atômico e Parar
  confirmado; estado, ações e eventos vêm do contrato, sem console/lote legado;
- [x] fórmula, pesos, moldes, ordem da busca e regra de negócio não foram
  alterados; o selo aprovado continua
  `7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad`;
- [x] bateria local: 41 testes Python verdes, incluindo protocolo V3, interface,
  entradas, moldes e fórmula; `teste_interface_formula_aprovada.js` não foi
  executado porque este Windows não tem Node instalado;
- [ ] pré-voo de credencial: a chave atualmente configurada devolveu HTTP 401 em
  `otimizador_regua_v2`; a chave não foi exibida nem alterada e precisa ser
  corrigida antes do readback/uso real;
- [ ] aplicar explicitamente `MIGRACAO-FILA-PRODUCAO-V3.sql` no Supabase;
- [ ] fazer readback de DDL/RLS/grants/RPCs e criar somente então o primeiro lote;
- [ ] executar piloto mínimo e validar snapshot, reserva, pausa, resultado e
  handoff pendente ao Bonificador antes de liberar a fila completa.

## Aplicação da fila produtiva V3 — 31/08/2026

- [x] autorização explícita recebida somente para aplicar o schema V3; ela não
  autorizou criar nem iniciar lote;
- [x] snapshot recuperável pré-aplicação criado em
  `RECUPERACAO/20260831-antes-aplicacao-v3-credencial/`; o manifesto SHA-256 foi
  conferido imediatamente antes do DDL e não contém `config.txt` ou credencial;
- [x] credencial moderna validada somente no backend: `otimizador_regua_v2` e
  `otimizador_carta_v3(8538111)` responderam HTTP 200. Os consumidores locais
  `interface/servidor.py`, `fonte_unica.py` e a auditoria passaram a enviar chave
  `sb_*` apenas em `apikey`; JWT legado preserva `Authorization`;
- [x] aplicada `20260831133727_otimizador_fila_producao_v3`: quatro tabelas V3,
  RPCs privadas, RLS, FKs, snapshots, controle atômico e selo de fórmula;
- [x] aplicada `20260831134002_otimizador_fila_producao_v3_indices_v2`: índices
  de cobertura para as três FKs apontadas pelo advisor, sem dados ou mudança de
  comportamento;
- [x] readback: `status_v3` devolve `sem_lote`, `criar=true` e
  `pode_publicar=false`; há zero lote e zero linha V3. `anon` e `authenticated`
  não têm execução das 10 RPCs; `service_role` tem. As quatro tabelas têm RLS e
  nenhum `SELECT` direto de cliente;
- [x] validação real em servidor temporário `127.0.0.1:8768`: Saúde, Fila,
  Eventos e Resultados responderam com contrato ativo, zero itens e publicação
  desligada. O processo de teste foi encerrado; nenhuma porta produtiva ou lote
  foi iniciado;
- [x] testes locais focados: 18 verdes (protocolo V3, interface e trava de
  fórmula), incluindo o cenário Messi 104. Não houve alteração de fórmula, pesos,
  moldes, Ímpetos condicionais, Bonificador ou publicação;
- [ ] antes de clicar **Criar e iniciar**, obter autorização operacional separada:
  a ação cria a fila completa e inicia o worker. Depois, validar um piloto
  controlado de snapshot, reserva, pausa, resultado persistido e handoff pendente
  ao Bonificador.
