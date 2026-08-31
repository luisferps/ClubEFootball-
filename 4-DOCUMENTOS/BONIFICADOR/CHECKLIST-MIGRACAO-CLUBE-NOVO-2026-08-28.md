# Checklist oficial — migração do Bonificador para `clube_novo`

**Data:** 28/08/2026  
**Escopo:** somente leituras de dados do jogo do Bonificador  
**Estado inicial:** auditoria e plano criados antes de qualquer troca de runtime ou banco

## Fila V3 aplicada — 31/08/2026

- [x] Snapshot recuperável e ensaio integral com rollback: 613 linhas, 50 cartas, 345 pares distintos.
- [x] `clube_novo.bonificador_par` preenchida só por IDs canônicos (`card_id`, `funcao_id`).
- [x] `public.bonificador_contexto_fila_v3` privado, apenas `service_role`.
- [x] Motor e aplicativo local apontam para régua V2, carta V2 e fila V3.
- [x] `public.gravar_build_bonificador_v3` restringe-se ao lote de teste; nenhuma linha foi calculada, publicada ou gravada nesta aplicação.

## Regra de execução

- [x] trabalhar somente na cópia `C:\Users\Luis Fernando\Downloads\Clubefootball V4`;
- [x] não criar cópia operacional paralela;
- [x] preservar alterações existentes do Otimizador, Extrator, serviço e UI;
- [x] inventariar arquivos, portas, campos, semântica e origem antes de editar;
- [x] criar auditoria pós-migração antes da troca;
- [x] registrar origem antiga, origem nova e valor divergente;
- [x] proibir fallback silencioso e zero inventado;
- [x] trava global: não alterar fórmula matemática, pesos, cortes, ordem de cálculo,
  composição dos moldes ou regras de negócio sem nova autorização específica e prova;
- [x] limitar esta etapa a referências/origens: código de função → ID/nome canônico e
  medida → índice canônico;
- [x] deixar playstyle 291 bloqueado até decisão;
- [x] aplicar contratos versionados no banco;
- [x] aplicar troca no executável do Bonificador;
- [x] executar readback e auditoria pós-migração;
- [x] atualizar este checklist somente com resultados reais.

## Arquitetura confirmada

| item | resultado |
|---|---|
| executável ativo | `2-MOTORES/BONIFICADOR/motor_bonus.py`; o SHA pré-migração histórica é `AA7840998FEF77B5ABECF706456FCB8DF7AD6DCD20C85AEA7372A6AE9C4015E5` |
| chamadores | nenhum; os `.bat` existentes executam somente `roda_lote_v6.py` |
| entradas antigas | `regua_bonus`, `carta_do_motor`, REST direto de `clube.build` |
| saída | `gravar_bonus` → `clube.build.b_*` |
| consumidor | `public.casa_tela`, fora do escopo e sem mudança visual |
| build atual | 0 pares; não existe lote do Bonificador autorizado para rodar |
| referência independente | `clube.build_arquivo_2608`, 17.798 linhas; 17.795 têm carta nos dois modelos |

## Plano da auditoria pós-migração

Esta seção foi fechada antes de qualquer aplicação.

- [x] comparar campos por `card_id`: corpo por `codigo_corpo`, pé ruim, posição por ID,
  playstyles por `id_jogo` e IA por bit;
- [x] comparar cardinalidade das seis relações normalizadas, registrando que somente
  corpo e IA são consumidos por esta fórmula;
- [x] calcular fingerprints particionados por hash estável de `card_id`;
- [x] conferir gates de todos os catálogos consumidos;
- [x] comparar a saída de estilo da regra legada independente com a regra reindexada por
  IDs sobre os 17.795 pares de referência;
- [x] listar divergências de componente com `card_id`, função, origem e dois valores;
- [x] conferir privilégios das RPCs: `service_role=true`, `PUBLIC/anon/authenticated=false`;
- [x] conferir que o executável não contém chamadas a `regua_bonus`, `carta_do_motor`
  nem leitura direta de `clube.build` depois da troca;
- [x] provar que carta bloqueada não entra no payload de gravação;
- [x] amostra de tela: `N/A`, pois nenhum arquivo ou contrato da UI é alterado.

Critério de aprovação: nenhuma divergência sem linha explicativa; zero fallback;
fingerprints registrados; gates verdadeiros para entradas gerais; Casillas 291
bloqueado; nenhuma escrita produtiva durante a validação.

## Baseline do banco

### Funções antigas — fingerprint da definição

| função | MD5 de `pg_get_functiondef` | grants |
|---|---|---|
| `public.carta_do_motor(text)` | `70bbd9e8bfef1320dfbec83c9ff168ce` | postgres, service_role |
| `public.regua_bonus()` | `809d1065b60bb83aae843dc7736b564a` | postgres, service_role |
| `public.gravar_bonus(jsonb)` | `6dd16fb81a04adff4e3e90e9e4899525` | postgres, service_role |

Os três contratos novos não existiam no baseline.

### Catálogos e regras

| conjunto | linhas/gate | fingerprint MD5 |
|---|---:|---|
| `clube_novo.corpo_ordem` | 15/15 aptas; 12 usadas | `e5272eb08a45f958a7a923676a343187` |
| `clube_novo.pe` | 11/11 aptas | `f9b1a837f5a4167b9acf17873fbcc5d9` |
| `clube_novo.posicao_jogo` | 13/13 aptas | `b3b01e7092621bb9907d9b22d24106ee` |
| `clube_novo.playstyle` | 36/36 aptas | `df8fd9983aac7a6179401e5ad4da17ee` |
| `clube_novo.estilo_ia` | 7/7 aptas | `6d8d6a6ea916ee23c9db94145d8f1c3e` |
| `clube.molde_corpo` — regra de sistema | 384; ponte 384/384 | `defc4d1d5036401c930d65f8fb2a1bb5` |
| `clube.estilo_regra` — regra de sistema | 31 estilos | `61e206eaf20069b66a473a286b6a9b52` |

### Fotografias por carta

| conjunto | antigo overlap | novo overlap | novo integral |
|---|---|---|---|
| corpo | `4237203e53a849d657b2988b8be854b6` | `68ba38300b65428ab372e8ad8f5dce94` | `a7ea1d6ca10a24cf0509bdc032f04a36` |
| pé/posição/slots, fotografia raw | `c812eed282218782bbbeddd514b7739a` | `3dc3235152ac886e1b887fa329d905f6` | `f6b095ef6e6456a3b7fd23d688645da2` |
| pé/posição/slots, relações consumidas por IDs | N/A | N/A | `244a88c7e9edd66099068494ba6b3f9d` |
| cardinalidade IA | `380ffa444a2ddefc34c8c0978c2a8ef2` | `447c52008b552fb608495d4fe68754c8` | relação nova `6a04d697d1f07725998003b467344846` |

Fingerprints diferentes são esperados e obrigam a lista nominal abaixo; não autorizam
fallback.

### Cardinalidade das relações normalizadas

| relação | linhas | cartas | mínimo–máximo por carta presente | consumida |
|---|---:|---:|---:|---|
| `carta_atributo_jogo` | 1.119.872 | 43.072 | 26–26 | não |
| `carta_corpo_jogo` | 516.864 | 43.072 | 12–12 | sim |
| `carta_habilidade_jogo` | 179.189 | 33.521 | 1–10 | não |
| `carta_estilo_ia_jogo` | 54.435 | 24.854 | 1–5 | sim |
| `carta_posicao_jogo` | 516.864 | 43.072 | 12–12 | não; a principal abaixo é consumida |
| `carta_impeto_jogo` | 3.748 | 2.641 | 1–2 | não |
| `carta_pe_jogo` | 129.216 | 43.072 | 3–3 | sim |
| `carta_posicao_principal_jogo` | 43.072 | 43.072 | 1–1 | sim |
| `carta_playstyle_jogo` | 86.144 | 43.072 | 2–2 | sim |

Pé, posição principal e playstyles têm zero divergência contra os escalares novos.
Os escalares ficam somente como contraprova; o contrato lê as relações normalizadas.

## Divergências nominais da entrada

Resumo integral no overlap de 42.803 cartas:

| campo | divergências |
|---|---:|
| corpo | 23 valores em 12 cartas |
| uso do pé ruim | 0 |
| precisão do pé ruim | 1 |
| cardinalidade de IA | 2 cartas |
| posição | 3 cartas |
| slot 1 | 3 cartas |
| slot 2 | 8 cartas |

Cartas afetadas: `108959`, `116575`, `122897`, `126622`, `132859`, `142185`,
`152929`, `155498`, `157714`, `159560`, `160233`, `160344`, `162270`, `168494`,
`172103`, `176844`, `177921`, `179438`, `179667`, `182363`, `183754`, `184827`,
`60754` e `63474`. Uma carta pode divergir em mais de uma família.

Casos discriminantes:

- `176844`: precisão antiga `1`, nova `2`; IA antiga `[]`, nova bits
  `616/647/680`;
- `155498`: altura antiga `180`, nova `185`; IA antiga `[]`, nova bit `678`;
- `160233`: posição antiga `DMF/VOL`, nova `CMF/id 5`; slot 1 antigo raw `32`,
  novo raw `28` → `playstyle.id_jogo=391`;
- `182363`: posição antiga `CF/CA`, nova `AMF/id 8`; slot 1 antigo raw `4`,
  novo raw `20` → `playstyle.id_jogo=261`.

O SQL de validação em `SQL/VALIDAR-CONTRATOS-BONIFICADOR-V1.sql` lista cada valor
antigo e novo, sem truncar a origem.

## Regra de estilo: prova e bloqueio

- [x] 30 de 31 estilos de `estilo_regra` resolvem por um único índice físico legado e
  pelo `playstyle.id_jogo` correspondente;
- [x] zero ambiguidade entre os índices dos dois slots para esses 30 estilos;
- [x] fórmula legada independente × fórmula reindexada: zero divergência em 17.795
  pares de referência;
- [x] o snapshot antigo de `b_estilo` diverge da regra v7 em 10.086 pares e não é usado
  como autoridade da fórmula atual;
- [x] playstyle 291 aparece em Iker Casillas `88045755827028`, dois pares de referência;
- [x] 291 fica bloqueado, porque ligar a regra textual pode acrescentar `+0,5` e requer
  decisão do usuário.

## Ponte canônica do molde corporal

- [x] pares usam `funcao_codigo` técnico; molde v7/v1 usa rótulo humano;
- [x] match direto `0/19` funções da referência;
- [x] 17.798/17.798 pares da referência resultavam em corpo ausente no v7;
- [x] ponte canônica `funcao_sistema.codigo_legado → nome_legado` cobre `19/19`;
- [x] usuário autorizou corrigir exclusivamente a referência, sem mudar o molde;
- [x] `clube_novo.funcao_sistema.id` publicado como identidade canônica das 19 funções;
- [x] medida antiga → `clube_novo.corpo_ordem.pos`: `228/228` regras resolvidas;
- [x] cada função tem 12 índices distintos, aptos e usados pelo motor;
- [x] 17.798/17.798 referências resolvem função e molde depois da ponte;
- [x] 19/19 estruturas antigas por nome são idênticas às novas por código/ID;
- [x] tabela de moldes permaneceu com 384 linhas e fingerprint inalterado
  `defc4d1d5036401c930d65f8fb2a1bb5`;
- [x] paridade matemática: 17.795 pares com insumo novo, 0 divergências;
- [x] 3 referências sem carta nova continuam sem cálculo e sem fallback;
- [x] fingerprints antigo canônico e novo por código iguais:
  `d76ee2c7544bc311a71cfb43cc6a70c0`.

## Recuperação

- [x] snapshot de `motor_bonus.py` criado antes da troca;
- [x] hash do snapshot igual ao original;
- [x] rollback de banco preparado antes da aplicação;
- [x] SQL de validação preparado antes da aplicação;
- [x] patch pós-migração salvo em `RECUPERACAO/.../mudancas.patch`;
- [x] hashes pós-migração registrados;
- [x] rollback ensaiado por transação com `ROLLBACK`, assinatura e readback.
- [x] snapshot específico anterior à ponte em
  `RECUPERACAO/2026-08-28-ANTES-PONTE-CANONICA-MOLDES`;
- [x] rollback específico `SQL/ROLLBACK-PONTE-CANONICA-MOLDES-V1.sql` ensaiado e
  confirmado sem perda da versão aplicada.

## Resultados pós-migração

### Banco

- [x] migration `20260828093708 contratos_bonificador_v1_clube_novo` aplicada;
- [x] migration `20260828094605 bonificador_posicao_principal_normalizada_v1`;
- [x] migration `20260828094756 bonificador_playstyle_normalizado_v1`;
- [x] migration `20260828094854 bonificador_pe_normalizado_v1`;
- [x] migration `20260828100000 bonificador_ponte_canonica_moldes_v1`;
- [x] migration `20260828100222 bonificador_ponte_indices_corpo_v1`;
- [x] as migrations do Bonificador nesta lista foram transacionais, precedidas por dry-run com `ROLLBACK`
  e encerradas por readback;
- [x] `bonificador_regua_v1()` MD5 pós-ponte
  `7417e765fc8b236b16f3b73e2e622300`;
- [x] `bonificador_carta_v1(text)` MD5 `3717c3aa73d87ee3ff9e4fb659b05363`;
- [x] `bonificador_pares_v1(integer,integer)` MD5 `3b4b8ca05ac16d99a9cfbe424c29ab7b`;
- [x] três funções `SECURITY DEFINER`, `search_path=""`;
- [x] `service_role=true`; `PUBLIC/anon/authenticated=false` nas três;
- [x] nenhum grant direto nem policy adicionada em `clube_novo`;
- [x] advisor pós-DDL: nenhum aviso cita os três contratos; avisos gerais existentes
  são alheios ao escopo e não foram alterados.

### Readback e sombra

- [x] carta `176844`: apta, corpo 12, pé 3, posição principal 1,
  playstyles 2, IA bits `616/647/680`, precisão nova `2`;
- [x] carta inexistente: bloqueada, sem fallback;
- [x] Iker Casillas `88045755827028`: bloqueado pelo ID 291;
- [x] sombra de estilo: 17.795 pares; legado intencional × IDs novos = 0
  divergências; fingerprint dos dois lados `f1ba831285e5819292e90d5a87adbb95`;
- [x] 2 pares com ID 291 identificados e bloqueados;
- [x] lista integral de divergências de entrada retornou origem antiga, origem nova e
  ambos os valores por `card_id/campo`;
- [x] `clube.build` permaneceu com 0 linhas; nenhum lote produtivo executado;
- [x] teste local/online somente leitura: `LOCAL_OK`, `ONLINE_OK` e
  `ONLINE_BRIDGE_OK molde_corpo_codigo_para_id_canonico`;
- [x] readback SHA-256 `6ae41b6b489e3c9a4fe2f0f7da8d0087401847c97c88e821822f6857c4041182`;
- [x] fotografia histórica antes da troca final de chave: runtime SHA-256
  `d86937340fdae579c466f09a61446115b0a3b0188c2daffdf340c9dba5f9e119`;
  a etapa final altera exclusivamente a busca de mapa e o argumento de função para ID;
- [x] Casillas/playstyle 291 ficou apto na etapa posterior por ID físico canônico;

### Runtime e recuperação

- [x] `2-MOTORES/BONIFICADOR/motor_bonus.py` após a chave por ID SHA-256
  `a0909796e8932426a3b72d677ef77fcf50d820eaced95253449828f4d2bfe7cb`;
- [x] AST válido; chamadas RPC limitadas a `bonificador_regua_v1`,
  `bonificador_carta_v1`, `bonificador_pares_v1` e a saída `gravar_bonus`;
- [x] pares com qualquer falta têm `b_total=None` e são excluídos do payload;
- [x] UI, Otimizador, Extrator, fórmula, ímpetos e dados do jogo não foram alterados;
- [x] amostra de tela `N/A`: nenhum arquivo/contrato visual mudou.

**Estado final desta etapa:** ponte de função e índice instalada, referências resolvidas
e paridade aprovada. Nenhum lote produtivo foi executado; Casillas/playstyle 291
permanece bloqueado.

## Fechamento — cadeia canônica integral (substitui os estados provisórios acima)

Esta seção é o estado oficial posterior à materialização completa. As anotações acima
que tratavam `291` como bloqueado, regras de sistema como legadas em runtime, ou
`clube.build` como fonte de pares são somente histórico do preflight.

- [x] snapshot pré-aplicação persistido em
  `clube_novo.bonificador_migracao_snapshot_v1`, com as três definições e as
  fotografias de régua/Casillas;
- [x] ensaio integral de aplicação e ensaio posterior do rollback, ambos encerrados
  por `ROLLBACK`; a versão aplicada permaneceu íntegra no readback seguinte;
- [x] estruturas privadas canônicas criadas com RLS e FKs:
  `bonificador_parametro`, `bonificador_molde_corpo`, `bonificador_posicao_slot`,
  `bonificador_regra_playstyle` e `bonificador_par`;
- [x] cardinalidades aplicadas: 14 parâmetros, 228 moldes (19 × 12), 13 slots,
  90 regras de playstyle/31 IDs e 0 pares — este último é esperado enquanto o lote
  produtivo permanecer desligado;
- [x] as três RPCs retornam somente de `clube_novo`; auditoria por definição de
  função encontrou `0` referências a `clube.*`; `PUBLIC`, `anon` e `authenticated`
  não executam as RPCs, apenas `service_role`;
- [x] readback em nova conexão: `bonificador_regua_v1` MD5
  `da2dd3d138f117f1931755cbf3a9d632`, `bonificador_carta_v1`
  `894f1ceac653ba99f5ddc38d515d5545` e `bonificador_pares_v1`
  `510446b33b23c5dd53b5eed3137e86a4` (retorno inclui `funcao_id`);
- [x] paridade da régua contra o snapshot: parâmetros, molde corporal, ordem corporal,
  casa, slots e `liga` sem o novo ID 291 são idênticos; a única extensão é
  `liga[291]=[0]`, prova física para GO;
- [x] o contrato não publica mais `nome_legado` como semântica. A diferença estrutural
  de `funcao_molde` é apenas a remoção desse campo histórico; `id`, `rotulo` e
  `pode_rodar` preservam-se;
- [x] Iker Casillas `88045755827028` está apto: slot 1 `291` Goleiro adiantado,
  slot 2 `336` Goleiro ofensivo, posição GO; a função matemática existente retorna
  `1,5`;
- [x] teste somente-leitura final: `LOCAL_OK`, `ONLINE_OK`,
  `ONLINE_BRIDGE_OK molde_corpo_e_estilo_por_funcao_id_canonico`;
- [x] `bonificador_pares_v1` fornece `funcao_id`; motor, moldes e casa de playstyle
  usam esse ID. `funcao_codigo` é preservado exclusivamente para a saída desligada
  `gravar_bonus`, sem participação em gate ou cálculo;
- [x] snapshot v2, patch de recuperação e rollback por `ROLLBACK` preparados e
  ensaiados antes/depois dessa última troca de chave;
- [x] nenhum lote, UI, Otimizador, Extrator, ímpeto, fórmula, peso, corte, ordem ou
  dado de jogo foi alterado.

### Matriz operacional antiga → canônica

| referência histórica | significado | fonte canônica efetiva | prova |
|---|---|---|---|
| `clube.carta_jogo.corpo` | 12 medidas | `carta_corpo_jogo` + `corpo_ordem.pos` | 12 relações/gates por carta |
| `clube.carta_jogo.pe_*` | pé ruim | `carta_pe_jogo` + `pe` | 3 relações/gates; parâmetros iguais |
| `clube.carta_jogo.posicao` | posição principal | `carta_posicao_principal_jogo` + `posicao_jogo.id` | cardinalidade 1 |
| tabelas de estilo dos slots | playstyles físicos | `carta_playstyle_jogo` + `playstyle.id_jogo` | cardinalidade 2; Casillas 291/336 |
| JSON de IA | estilos de IA | `carta_estilo_ia_jogo` + `estilo_ia` | bits físicos/gates |
| `clube.molde_corpo` | direção, peso e cortes | `bonificador_molde_corpo(funcao_id,corpo_pos)` | 228 valores idênticos; 19 × 12; consumo por ID |
| `clube.bonus_parametro` | tetos e pesos | `bonificador_parametro` | 14 valores idênticos |
| `clube.estilo_regra`/`posicao_slot` | casa, liga e slot dominante | `bonificador_regra_playstyle`/`bonificador_posicao_slot` | 90 regras; casa por `funcao_id`, paridade e ID 291 físico |
| `clube.build` | pares card × função | `bonificador_par(card_id,funcao_id)` | FK e 0 pares, sem lote |

**Estado final canônico:** a cadeia operacional lê apenas `clube_novo` por contratos
versionados; a única consulta a legado ficou no SQL de materialização/auditoria e no
snapshot histórico, jamais em gate, fallback ou decisão de runtime. Lote produtivo e
consumidor de saída seguem desligados.

## Organização física do runtime

- [x] executável único movido para `2-MOTORES/BONIFICADOR/motor_bonus.py`;
- [x] caminho histórico `2-MOTORES/motor_bonus.py` ausente; não há import nem
  lançador normal que o alcance;
- [x] `2-MOTORES/config.txt` mantido comum: é dependência de vários motores e não foi
  copiado para o Bonificador;
- [x] inventário do executável: somente biblioteca padrão Python, sem módulo local a
  mover; testes, SQL e recuperação permanecem sob `4-DOCUMENTOS/BONIFICADOR`;
- [x] snapshot e rollback de movimento em
  `RECUPERACAO/2026-08-28-ANTES-ORGANIZACAO-OPERACIONAL`;
- [x] testes sem escrita: `ORGANIZACAO_OK`, `LANCAMENTO_ISOLADO_OK`,
  `FORMULA_LOCK_OK`, `LOCAL_OK` e `ONLINE_OK`.

## Aplicativo local somente leitura — 28/08/2026

- [x] padrão do Extrator documentado antes da implementação: EXE WinForms, ícone,
  executor Python oculto em loopback, health-check e janela de aplicativo;
- [x] criado `2-MOTORES/BONIFICADOR/Bonificador ClubEfootball.exe`, ícone próprio e
  `RODAR-INTERFACE-BONIFICADOR.bat`;
- [x] executor exclusivo limita-se a `127.0.0.1:8766`, `GET`,
  `bonificador_regua_v1` e `bonificador_carta_v1`; `POST` retorna `405`;
- [x] navegador não recebe segredo, schema, tabela, lote ou endpoint de escrita;
- [x] a simulação chama as funções puras do próprio motor; fórmula, pesos, cortes,
  ordem e regras permanecem inalterados;
- [x] teste isolado: `INTERFACE_LOCAL_OK simulacao=casillas estilo=1.5 post=405
  frontend_sem_credencial=sim`;
- [x] EXE abriu e `/api/saude` retornou `bonificador-regua-v1` apto;
- [x] teste visual/online de Iker Casillas `88045755827028` na função #5: entradas
  291/336, gates aprovados, `b_estilo=1.5000`, `b_total=1.6875` e console sem erros;
- [x] UI principal, Otimizador, Extrator, banco, lote, fórmulas e dados do jogo não
  foram alterados;
- [x] recuperação específica em `RECUPERACAO/2026-08-28-ANTES-INTERFACE-LOCAL`.

## Pipeline incremental por linha — 31/08/2026

- [x] o runtime V9 deixou de encerrar ao receber contexto vazio: aguarda intervalo
  configurável e consulta novamente apenas `bonificador_contexto_escrita_v2`;
- [x] cada rodada relê a régua, o contexto e as cartas vigentes; não há checkpoint,
  fila persistida, cache ou segredo novo no disco;
- [x] a condição de escrita continua ser a linha já concluída pelo Otimizador e apta
  nos gates canônicos; fórmula, parâmetros, moldes, writer e `SELECT FOR UPDATE` não
  foram alterados;
- [x] `Ctrl+C` encerra o pipeline normalmente e resultados já confirmados permanecem
  transacionais no banco; falha HTTP/validação continua explícita e fail-closed;
- [x] criado `RODAR-BONIFICADOR-PIPELINE.bat`; um único escritor Bonificador por banco
  continua recomendado;
- [x] snapshot anterior em `RECUPERACAO/2026-08-31-ANTES-PIPELINE-INCREMENTAL`;
- [x] testes offline: vazio → espera → par apto → writer, par incompleto sem writer,
  smoke de lançamento, writer canônico, trava da fórmula e organização operacional.

## Pipeline pelo aplicativo local — 31/08/2026

- [x] o aplicativo local passou a ser o ponto normal de iniciar/parar o pipeline;
  o `.bat` permanece apenas técnico;
- [x] o executor loopback inicia `motor_bonus.py` em processo separado, atualiza estado
  em memória e continua atendendo consulta/simulação enquanto o motor trabalha;
- [x] botões expõem estado de iniciando/processando/aguardando/parando/parado/erro,
  sem chave, URL de banco ou schema no navegador;
- [x] parada pela UI envia sinal cooperativo: termina a rodada em andamento e não cria
  arquivo de controle, checkpoint ou fila local;
- [x] teste offline de responsividade cobre início, leitura imediata de estado e parada
  de processo falso; POST fora das duas ações de controle continua 405;
- [x] snapshot antes da integração em
  `RECUPERACAO/2026-08-31-ANTES-INTEGRACAO-PIPELINE-APP`.

## Janela nativa e fila visível — 31/08/2026

- [x] substituída a abertura no navegador por EXE WinForms V2.0.0, no padrão do
  Extrator; a aba inicial adota a organização de fila do Otimizador;
- [x] a fila é leitura do contrato canônico privado
  `bonificador_contexto_escrita_v2`, mediada pelo serviço loopback, sem tabela direta,
  `clube.build`, fallback ou gate legado;
- [x] expostos estado, progresso, linha atual, pendentes, calculadas, confirmadas,
  eventos e selos por linha; simulação e auditoria continuam separadas;
- [x] mensagens de saída não são mais reduzidas a “código 1”: o detalhe seguro do
  contrato é mantido no estado da janela;
- [x] snapshot recuperável em
  `RECUPERACAO/2026-08-31-ANTES-INTERFACE-NATIVA-FILA`;
- [!] leitura viva bloqueada com evidência: `bonificador_regua_v1` apta, porém
  `bonificador_contexto_escrita_v2` ausente da cache do PostgREST (`PGRST202`). Banco
  não foi modificado nesta revisão; o pipeline permanece fail-closed e sem lote.
