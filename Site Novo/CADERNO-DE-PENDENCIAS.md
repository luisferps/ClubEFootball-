# Caderno de pendências do Site Novo

## SITE-NOVO-NORM-0909 — normalização oficial e estrelas

- **Estado:** `RESOLVIDA` em 09/09/2026.
- **Entrega:** nota bruta do Otimizador convertida no banco pela curva fixa aprovada; bônus integral somado depois. Editor alinhado; estrelas nas Boxes com as seis etiquetas/limites preservados no banco.
- **Prova:** 55.151 publicações conferidas, zero divergência de soma, bruto, bônus, par ou componentes. Líderes das 19 funções: nota final do editor igual à publicação. Netlify publicado, deploy `6aa145d2cc4c3074ca5b98fa`, 21 arquivos conferidos.
- **Referência:** [Implantação e limites da auditoria](../4-DOCUMENTOS/NORMALIZACAO-0909/IMPLANTACAO.md). A discrepância histórica de Passe alto na linha 30016 está descrita no registro; esta conclusão é da normalização e apresentação, não da revisão geral das linhas dos motores.

Este é o registro vivo das pendências descobertas durante a construção do Site Novo.

## SITE-NOVO-PEND-014 — veto estratégico indevido no editor pessoal

- **Abertura e resolução:** 08/09/2026. **Estado:** `RESOLVIDA`.
- **Contexto:** a regra de Volta para marcar do Otimizador foi aplicada
  indevidamente ao catálogo, avaliador e seletor pessoal. Luis corrigiu o escopo.
- **Regra:** o editor não otimiza e não aplica os vetos estratégicos do motor;
  aceita escolhas treináveis e zero a cinco adicionais, conforme o manual.
- **Correção:** JavaScript restaurado; catálogo, avaliador e helper de sugestões
  restaurados exatamente às definições anteriores pela migração
  `20260908210044_restaurar_liberdade_editor_habilidades.sql`.
- **Prova:** Shevchenko / Centroavante móvel foi avaliado com `[56]` e com `[]`,
  ambos com 26 atributos. Três testes do editor e sintaxe passaram. Não houve
  salvamento pessoal de teste. Os dez bloqueios do motor permanecem no banco.
- **Controle de transporte:** `../CONTROLE-COPIA-MAQUINA-2-VOLTA-0809.md`.

## Regra de manutenção

- Todo item recebe identificador estável, data de abertura, contexto, impacto, estado, fonte a conferir, critério objetivo de conclusão e evidência de fechamento.
- Estados permitidos: `PENDENTE`, `EM ANDAMENTO`, `RESOLVIDA`, `BLOQUEADA`.
- Previsão, mensagem ou expectativa não fecham pendência. `RESOLVIDA` exige readback, artefato ou teste verificável.
- Uma descoberta ou resolução importante deve atualizar este arquivo na mesma entrega que a produziu.

## SITE-NOVO-PEND-001 — atributos finais de cartas processadas pelo motor anterior

- **Abertura:** 2026-09-04.
- **Estado:** `EM ANDAMENTO`.
- **Contexto:** cards oriundos de versão anterior do motor podem ter nota oficial publicada, mas não o vetor final de 26 atributos destinado à Ficha.
- **Amostra nominal:** Dani Olmo, `card_id=106787651039542`.
- **Informação operacional:** o usuário informou em 2026-09-04 que as cartas afetadas acabaram de entrar numa fila prioritária do Otimizador e que a expectativa é terminar até o dia seguinte. Isso é previsão, não comprovação de execução ou conclusão.
- **Impacto:** a Ficha pode mostrar card, nota e demais campos persistidos, mas não pode mostrar os 26 valores finais até que eles sejam publicados. É proibido usar fallback legado, atributo base ou cálculo local como substituto.
- **Não é pendência:** cards com `level_cap=1`, `orcamento=0`, vetor final completo, barras zero e habilidades adicionais vazias são cards válidos sem evolução. Esse caso não integra esta pendência.
- **Fontes/objetos a conferir:** `clube_novo.build_linha_card`, `clube_novo.build_otimizador.atributos_finais`, `clube_novo.otimizador_lote_producao_v3`, `clube_novo.otimizador_lote_producao_candidata_v5`, `clube_novo.otimizador_lote_producao_carta_v3`, `clube_novo.otimizador_lote_producao_linha_v3` e `public.site_novo_ficha_v1`.
- **Evidência atual:** em 2026-09-04, a linha selecionada de Dani era `2778`, com nota `109.82407297762478` e `atributos_finais=null`. A consulta viva não encontrou o card nas quatro tabelas de lote listadas acima. O readback de `public.site_novo_ficha_v1` sob a role `anon` e a tela local devolveram `atributos_aguardando_publicacao`, 26 nomes e zero valores finais. Portanto, o Site Novo não afirma que o banco já comprova a fila e não usa fallback.
- **Atualização de readback em 2026-09-04:** uma nova chamada pública devolveu Dani como `atributos_em_atualizacao`. Isso comprova que a porta passou a encontrar evidência viva de fila; a pendência continua `EM ANDAMENTO` até a publicação e o readback dos 26 valores finais.
- **Universo afetado:** ainda precisa ser identificado por evidência do lote/fila atual. A verificação final deve cobrir todas as cartas antigas afetadas, não apenas Dani.
- **Critério objetivo de conclusão:** identificar o universo do lote/fila; após processamento e publicação, comprovar no banco vivo que a linha selecionada de cada card afetado tem `atributos_finais` como array JSON de exatamente 26 itens; confirmar que o buscador da Ficha devolve `status=pronto` e 26 atributos finais para cada card, sem fallback nem cálculo local.
- **Evidência de fechamento:** ainda não existe.

## SITE-NOVO-PEND-002 — Pode Melhorar na edição — RESOLVIDA

- **Estado:** `RESOLVIDA` em 06/09/2026.
- **Regra vigente:** o mesmo comparador serve à vitrine e ao modal; usa a maior nota pública do mesmo card/função e a nota corrente recebida do avaliador. Até 0,05% mostra 0%; acima mostra uma casa decimal.
- **Entrega:** `FichaView.renderComparison` reutiliza a implementação existente. O modal apresenta nota e comparador no cabeçalho e invalida a indicação enquanto aguarda nova avaliação.
- **Provas:** DOM com máximo/nota superior, função distinta ignorada, 100→110 = +10,0%, limite 0,05% e acima do limite. Teste integrado passou.

## SITE-NOVO-PEND-003 — builds pessoais na grade — RESOLVIDA

- **Estado:** `RESOLVIDA` em 06/09/2026.
- **Regra vigente:** pessoais azuis na mesma grade das canônicas verdes. Função-base + número permanente, com nome livre no título/gerenciador. Cada origem (navegador/conta) mantém seu contador. O contador não reutiliza números excluídos.
- **Entrega:** cálculo sem login, salvamento local por padrão sem conta, nuvem opcional autenticada. A grade recarrega após salvar/excluir/alterar conta; clicar na pessoal exibe seus próprios atributos, escolhas e nota. Editar abre a pessoal correta, sem sobrescrever o sistema.
- **Expansão:** decisão posterior do usuário substituiu paginação: até 20 entradas recolhidas, linha fina Ver Mais/Ver Menos expande ou recolhe as demais.
- **Provas:** servidor com isolamento, revisão, recibo, exclusão lógica, novo número 2 após excluir 1; HTTP sem login e armazenamento local com recarga; DOM com 35 builds, expansão/recolhimento e reabertura para edição. Testes não enviaram e-mails nem deixaram builds sintéticas no banco.

## SITE-NOVO-PEND-004 — troca atômica da geração publicada — CONCLUÍDA

- **Abertura:** 2026-09-05.
- **Estado:** `PENDENTE`.
- **Contexto:** a retirada da publicação V9 incorreta ocorreu antes de a V10 estar pronta para a leitura pública. Nesse intervalo, cards existentes ficaram sem pontuação, builds e atributos publicados. O usuário determinou que esse comportamento não pode existir em produção.
- **Regra confirmada pelo usuário:** uma geração nova deve ser preparada e validada sem retirar a geração pública comprovadamente válida. A ativação ocorre de forma atômica; a geração substituída só é limpa depois do readback público da nova. Versão comprovadamente errada não pode ser mantida apenas para evitar vazio: deve haver rollback para a última geração válida ou manutenção explícita.
- **Impacto:** o cliente continua corretamente fail-closed e não inventa dados, mas isso não substitui continuidade transacional da publicação. Sem o gate, uma operação administrativa pode deixar a Ficha publicamente vazia entre versões.
- **Fontes/objetos a conferir:** processo de publicação V10, versão/geração das linhas publicadas, ponteiro ou selo de geração ativa, transação de ativação, rollback para última versão válida e `public.site_novo_ficha_v1`.
- **Critério objetivo de conclusão:** em ensaio controlado, preparar uma geração substituta completa sem alterar a resposta pública; provar que falha de validação mantém a geração ativa; ativar a nova em uma única operação; confirmar por readback que não existe instante observável com zero builds; só então limpar a anterior. Repetir a prova com falha de ativação e rollback.
- **Evidência de fechamento (2026-09-05):** foi instalada a finalização idempotente por linha com ponte ativa, fila durável, gatilhos nas chegadas dos dois motores e retry por cron. O primeiro backfill publicou 25/25 sem erro; Alisson Santos `105870138684343`, linha `378966`, teve `98,86167644015178 + 2,5686 = 101,43027644015177` com o mesmo valor na linha, na ponte, no leitor V2 e em `public.site_novo_ficha_v1`. O catálogo devolveu nulo para os objetos globais/manuais removidos, com zero V9 ativa e zero composição divergente.
- **Limite de bootstrap:** esta migração específica só troca leitores quando a origem anterior foi comprovada com zero linhas, como ocorreu neste incidente. Em outro banco com geração anterior não vazia, ela falha antes da troca; é obrigatório semear e validar a ponte numa migração própria para preservar continuidade.
- **Readback final do estoque pronto:** 3.460 linhas ativas, 3.460 linhas no delta e 3.460 eventos de publicação; 0 aguardando no backfill, 0 erros, 0 duplicações de `linha_id`, 0 V9, 0 vetor incompleto e 0 divergência na soma. Duas sessões concorrentes reais publicaram uma linha distinta cada; o teste transacional confirmou as duas ordens de chegada e idempotência com a ponte preservada.
- **Mitigação visual de 2026-09-05:** a Ficha passou a preservar a altura mínima e a posição relativa dos quatro blocos durante estados incompletos, sem inventar conteúdo. Essa estabilidade do chassi evita o recolhimento da página, mas não substitui nem conclui a troca atômica da geração publicada.
- **Evidência de fechamento:** ainda não existe.

## SITE-NOVO-PEND-005 — enquadramento integral da foto no Bloco 1

- **Abertura:** 2026-09-05.
- **Estado:** `RESOLVIDA`.
- **Contexto:** a moldura usava proporção `3:4`, embora os arquivos reais de card meçam `240 × 340`. A diferença cortava visualmente a faixa inferior da arte, deixando as estrelas pela metade.
- **Impacto:** o card parecia amputado no rodapé mesmo com a imagem correta na origem.
- **Resolução:** a moldura passou a usar a proporção física `12:17` e deixou de poder encolher na coluna de identidade. A largura da foto, as quatro colunas iguais e `object-fit: contain` foram preservados.
- **Critério objetivo de conclusão:** confirmar que a moldura tem a mesma proporção dos arquivos, preserva a arte inteira e não altera a geometria horizontal aprovada do Bloco 1.
- **Evidência de fechamento:** os arquivos reais de Alisson Santos `105870138684343`, Lionel Messi `89136409091415` e John Stones `56167703296681` medem `240 × 340`; o readback de `ficha.css` confirmou `aspect-ratio: 12 / 17`, `flex: none` e `object-fit: contain`, sem mudança em HTML, JavaScript ou banco.

## SITE-NOVO-PEND-006 — seleção individual da build no Bloco 2

- **Abertura:** 2026-09-05.
- **Estado:** `RESOLVIDA`.
- **Contexto:** o clique numa build reutilizava apenas o conjunto de posições como identidade da seleção. Por isso, qualquer outra build que compartilhasse uma posição também recebia o realce máximo, mesmo sem ter sido clicada.
- **Impacto:** a interface não distinguia a escolha explícita de uma build do filtro amplo iniciado pelo campo.
- **Resolução:** o único estado de interação passou a registrar origem, posições e identidade da build. O clique numa build ilumina somente o botão escolhido e suas posições no campo; o clique no campo continua iluminando todas as builds ligadas àquela posição. Trocar a origem substitui a seleção anterior e repetir o mesmo clique limpa o estado.
- **Critério objetivo de conclusão:** provar uma build com múltiplas posições e outra build que compartilhe essas posições; no clique da build deve haver exatamente um botão realçado, enquanto no clique do campo devem aparecer todas as correspondentes, com `aria-pressed` coerente e sem nova chamada ou manipulador duplicado.
- **Evidência de fechamento:** teste real no navegador com Andriy Shevchenko `88045755964138`: `Centroavante móvel · CA/SA` selecionou exatamente uma build e duas posições; o clique posterior em CA selecionou `Centroavante móvel`, `Centroavante fixo` e `Falso nove`; o retorno à build isolou novamente um botão e o segundo clique limpou tudo. `node --check` passou, e o arquivo manteve uma única chamada `fetch`.

## SITE-NOVO-PEND-007 — contador de posições ocupáveis no Bloco 2

- **Abertura:** 2026-09-05.
- **Estado:** `RESOLVIDA`.
- **Contexto:** o cabeçalho exibia `builds_publicadas_total` como se fosse a quantidade de posições do jogador. Esse campo conta entradas posicionais publicadas das builds e pode repetir a mesma posição muitas vezes.
- **Impacto:** Weston McKennie aparecia com `28 POSIÇÕES`, número impossível para o campinho e sem o significado apresentado pela interface.
- **Resolução:** o contador passou a usar exatamente as casas do campinho. Cada posição `primary` ou `allowed` conta uma vez; cada posição `absent` fica fora. A mesma lista canônica de casas alimenta desenho e contagem.
- **Critério objetivo de conclusão:** o número exibido deve coincidir com a quantidade de casas nativas ou permitidas no campo, independentemente da quantidade de entradas posicionais das builds, sem nova consulta e sem alteração do contrato.
- **Evidência de fechamento:** readback público somente leitura confirmou Weston McKennie `55068997045101` com 28 entradas posicionais e 12 posições ocupáveis, Shevchenko com 12 e 4, e Alisson Santos com 6 e 3. `node --check` passou; `ficha.js` manteve uma única chamada `fetch` e deixou de usar o total de entradas das builds no cabeçalho.

## SITE-NOVO-PEND-008 — pontuação e navegação vinculadas à build visualizada

- **Abertura:** 2026-09-05.
- **Estado:** `RESOLVIDA`.
- **Contexto:** o clique numa build do Bloco 2 alterava apenas o realce visual. A build detalhada e os dois campos de pontuação total continuavam presos à linha escolhida na abertura da página, confundindo seleção visual com build efetivamente visualizada.
- **Regra confirmada pelo usuário:** toda pontuação total pertence à build corrente. `?card=<card_id>` sem linha abre a melhor build pública disponível; `?card=<card_id>&linha=<linha_id>` abre exatamente a linha mostrada na página de origem. Os dois placares e, futuramente, a edição usam a mesma autoridade de pontuação.
- **Resolução de frontend aplicada:** o clique numa build agora escolhe uma linha publicada do grupo e a consulta pela mesma RPC em segundo plano. Após validar card e linha, atualiza em conjunto todos os campos dependentes da build e canonicaliza `card` e `linha` por `history.pushState`, sem recarregar a página nem remontar a identidade do card. Os dois placares e os dois comparadores “Pode melhorar” são atualizados por uma única função. Link explícito com `linha` destaca o grupo correspondente; link genérico não cria seleção luminosa artificial.
- **Continuidade diante de falha:** uma resposta inválida ou HTTP de erro mantém a ficha e a URL anteriores e mostra a falha explicitamente. Não existe retry ou fallback silencioso. Um clique novo cancela a leitura anterior ainda em voo e respostas antigas não podem vencer a escolha mais recente; Voltar/Avançar usa a mesma leitura interna por `popstate`.
- **Escolha dentro de grupo posicional:** se o campo tiver um filtro compatível, usa a linha dessa posição; senão preserva a linha já selecionada no grupo; por fim usa a primeira linha na ordem pública. Uma página externa não usa esse desempate: transporta o `linha_id` exato que exibiu.
- **Impacto:** Ranking, listas e futuras páginas devem sempre incluir `linha` quando o usuário clicar numa build específica. Links que conhecem apenas o card devem omitir `linha` e aceitar a melhor build pública como default.
- **Fontes/objetos a conferir:** `public.site_novo_ficha_v1`, `build.nota_final`, `build.linha_id`, `builds_publicadas[].linha_id`, `score-top`, `score-main`, `improve-top`, `improve-main` e futuros emissores de links para a Ficha.
- **Critério objetivo de conclusão:** provar no mesmo card que `card` sozinho abre a maior nota pública; provar que duas `linha` diferentes abrem suas respectivas funções, posições, notas e 26 atributos; clicar numa build deve canonicalizar a URL sem recarregar a página e manter exatamente um grupo realçado; os dois placares devem ter o mesmo valor; identidade e foto devem permanecer montadas; falha de troca deve preservar conteúdo e URL; confirmar uma requisição por linha nova, um manipulador por botão, um controlador de histórico e nenhum cálculo local de `nota_final`. A auditoria do universo público deve confirmar que a ordem default da porta sempre representa a maior nota publicamente visualizável.
- **Evidência de fechamento:** a migração registrada no banco como `20260905215643 ficha_default_maior_nota_v2` colocou `nota_final DESC NULLS LAST` em primeiro lugar; completude, data e ID ficaram somente como desempate. A auditoria encontrou 21.633 linhas de 1.087 cards e zero divergência entre a linha default e `MAX(nota_final)`. Os artefatos locais são `20260905185410_MIGRACAO-FICHA-MAIOR-NOTA-V2.sql` e `20260905185410_VALIDAR-FICHA-MAIOR-NOTA-V2.sql`. O readback público de Weston McKennie `55068997045101` confirmou default na linha `8477`, Lateral ofensivo LD, `101,89903756033348`; linha explícita `8475`, Lateral defensivo LD, `95,02574835983803`; e linha explícita `8474`, Lateral defensivo LE, com a mesma nota. As três respostas foram `pronto` e trouxeram 26 atributos. A regressão local de troca interna comprovou `?card=55068997045101&linha=8475`, os dois placares em `95,03`, exatamente um botão Lateral defensivo realçado, LD/LE acesos, o mesmo nó da foto e zero `location.assign`; uma segunda troca não duplicou o rodapé. Um `500` controlado manteve nota e URL anteriores, e Voltar restaurou a rota genérica com `101,90` sem remontar a identidade. `node --check` passou; o arquivo contém uma expressão `fetch`, um manipulador de `popstate`, zero intervalos, zero observadores e zero escrita. O readback independente posterior repetiu o default três vezes e as duas linhas explícitas, todas com HTTP 200; o default coincidiu com a maior nota da lista.

## SITE-NOVO-PEND-009 — HTTP 500 intermitente na leitura pública da Ficha

- **Abertura:** 2026-09-05.
- **Estado:** `RESOLVIDA`.
- **Contexto:** durante um clique normal em Lateral ofensivo, a abertura pública de Weston McKennie `55068997045101`, linha `8477`, devolveu `Falha na consulta pública (500)`. A navegação completa então apagou a ficha; esse efeito visual foi corrigido separadamente na pendência 008.
- **Impacto:** mesmo com a interface agora preservando a última ficha válida, a linha escolhida não pode ser mostrada enquanto a chamada falha. A proteção do cliente não resolve nem mascara o erro da origem.
- **Mitigação de frontend:** a troca mantém conteúdo e URL anteriores, mostra erro explícito e não repete a chamada automaticamente. Não foi criado fallback e o timeout público não foi aumentado.
- **Evidência anterior à correção:** seis chamadas públicas sequenciais imediatamente posteriores com `p_card_id=55068997045101` e `p_linha_id=8477` retornaram HTTP 200, estado `pronto`, linha `8477`, entre 220 e 719 ms. Os request IDs foram `01a073ae-0867-7f81-bb7b-3ca457cefc1f`, `01a073ae-0b0a-7266-b386-6671a2951a8a`, `01a073ae-0c59-7e29-87c3-6638bd549657`, `01a073ae-0d38-73f4-9dc0-d939aab7e967`, `01a073ae-0e45-7f30-b829-40fec6b6ffa8` e `01a073ae-0f50-7c46-a9a2-1c41dbc13734`. Isso comprovou intermitência e orientou a inspeção dos logs.
- **Fonte/objeto a conferir:** logs do Data API/PostgREST e execução de `public.site_novo_ficha_v1` na janela aproximada de 2026-09-05 22:22 UTC, incluindo concorrência com o processo automático; plano e duração da chamada anon sob o teto vigente.
- **Critério objetivo de conclusão:** identificar a causa real do 500 na origem; aplicar correção sem aumentar o timeout anon; repetir chamadas de usuário durante atividade real do processo automático e comprovar ausência do erro, preservando uma única resposta pública e sem retry/fallback no cliente.
- **Causa confirmada:** os logs registraram `SQLSTATE 57014` (`statement timeout`) no startup de `site_novo_ficha_base_publicada_v1` às `2026-09-05 22:22:25Z`. Os três `EXISTS` grandes das filas eram executados antes da seleção final da linha e faziam a leitura ultrapassar o teto sob concorrência real.
- **Correção de origem:** a migração `20260905223427` moveu esses três `EXISTS` para um helper interno privado, sem aumentar o timeout e sem alterar wrapper, assinatura, versão, JSON ou semântica da porta pública. A comparação de 50 cards encontrou zero divergência.
- **Evidência de fechamento:** com o Bonificador rodando, 6/6 chamadas sequenciais retornaram HTTP 200 com máximo de 511 ms; 3/3 chamadas simultâneas no mesmo segundo do cron retornaram HTTP 200 com máximo de 1,312 s; o cron levou 213 ms e os logs posteriores registraram somente 200. O readback independente desta frente fez outras seis chamadas da linha `8477`: todas HTTP 200, `pronto`, linha correta, entre 118 e 290 ms. McKennie default, `8477` e `8475` permaneceram semanticamente corretos. A proteção do frontend foi mantida para falhas futuras, sem retry nem fallback silencioso.

## SITE-NOVO-PEND-010 — Área da Build e modal — IMPLEMENTADA

- **Estado:** `RESOLVIDA` quanto à implementação em 06/09/2026.
- **Decisão vigente:** ficha somente consulta. Build em Exibição ocupa metade da faixa, em destaque; Criar Nova Build e Editar Build ficam ao lado como comandos secundários. Melhor e Minhas foram removidos porque a grade já dá acesso às builds. Excluir fica só no modal de uma build pessoal, com confirmação. Ver Mais fica abaixo como linha fina.
- **Entrega visual:** pares Distribuição/Habilidades e Técnico/Ímpetos em linhas fixas; título nas barras e valores dourados; dois ímpetos iguais. Graduação de verde conforme pontuação, mantendo pessoais azuis. Maiúsculas existentes preservadas.
- **Modal:** foco no conteúdo da build, nota/comparador no cabeçalho, comandos compactos, sem avisos repetidos; conta opcional recolhida. Criação começa zerada, edição parte da escolhida, salvamento não substitui sistema.
- **Verificação:** testes estruturais/DOM de agrupamento, grade, cores, rascunho, comandos, comparação e armazenamento passaram. A renderização visual final no Chrome a 100% não foi automatizada; não se confunde teste DOM com aprovação visual do usuário.

## SITE-NOVO-PEND-011 — tema claro completo da Ficha

- **Abertura:** 2026-09-07.
- **Estado:** `PENDENTE`.
- **Contexto:** o site tem tema claro e escuro. O `ficha.css` não possuía nenhuma regra para
  `data-theme`: no tema claro o cabeçalho da Ficha ficava com fundo claro e texto claro — a marca
  CLUBeFOOTBALL desaparecia — e o corpo permanecia escuro. Medido em 07/09:
  `headerBg rgba(239,243,240,.96)` com `color rgb(230,235,232)`.
- **Correção aplicada em 07/09 (parcial, e assumida como tal):** no tema claro a moldura da página
  — `html`, `body`, cabeçalho, rodapé e os espaços de banner — passou a usar as variáveis do
  `site-shell.css`. O painel da Ficha (`.stage`) mantém a paleta escura aprovada. Readback:
  `bodyBg rgb(255,255,255)`, `headerCor rgb(20,24,27)`, `marcaCor rgb(20,24,27)`,
  `stageFundo rgb(23,28,25)`. A ilegibilidade acabou.
- **O que continua pendente:** um tema claro **de verdade** para os quatro blocos. Medição de
  07/09: fora do bloco `:root`, o `ficha.css` tem **173 cores hexadecimais e 113 valores `rgba`
  fixos** — cerca de 286 cores escritas à mão, incluindo o verde-petróleo da Área da Build, as
  cinco intensidades de verde das builds do sistema, o azul das pessoais, o dourado dos números e
  as cinco cores de Ímpeto. Todas são desenho congelado pelo manual.
- **Impacto:** quem usa o site no tema claro vê a moldura clara e o painel da Ficha escuro. É
  legível e coerente, mas é um salto visual em relação às demais telas.
- **Por que não foi feito agora:** repaletizar 286 cores congeladas é decisão de design do usuário,
  não correção de defeito, e exige aprovação visual dele. Fazer isso sem conferência seria trocar
  um problema por outro maior.
- **Critério objetivo de conclusão:** o usuário decidir entre (a) manter o painel da Ficha sempre
  na paleta escura aprovada, e então esta pendência se fecha como decisão registrada; ou (b) criar
  a paleta clara dos quatro blocos, e então provar cada bloco em captura no Chrome a 100%, com
  contraste conferido, sem alterar geometria, hierarquia nem semântica das cores.
- **Evidência de fechamento:** ainda não existe.

## SITE-NOVO-PEND-012 — testes com rede não rodam fora da máquina do usuário

- **Abertura:** 2026-09-07.
- **Estado:** `CONCLUÍDA EM 2026-09-08`.
- **Contexto:** seis testes da pasta `tests` fazem chamada HTTP real ao Supabase: `ranking`,
  `boxes`, `boxes-search`, `search`, `degrau` e `ficha-degree`. Em 07/09 eles não puderam ser
  executados porque o ambiente usado não alcança `supabase.co`. Os testes sem rede
  (`site-shell`, `site-theme`, `boxes-state`, `ranking-state`, os três do editor e o novo
  `home`) passaram.
- **Impacto:** as correções de 07/09 não têm regressão HTTP conferida.
- **Critério objetivo de conclusão:** rodar os seis na máquina do usuário e registrar o resultado
  aqui. `tests/ranking.test.cjs` também exige `APLICAR-RANKING-LEITURA-OTIMIZADA.sql` na pasta.
- **Evidência de fechamento:** suíte completa executada nesta máquina em 08/09: 15 arquivos de teste aprovados, zero falhas, incluindo consultas HTTP públicas de Boxes, busca, Ranking, degraus e Ficha. As expectativas antigas de filtros e do termo função foram atualizadas para a interface aprovada. A cobertura não substitui inspeção visual no navegador.

## SITE-NOVO-PEND-013 — Elenco sem contrato

- **Abertura:** 2026-09-07.
- **Estado:** `BLOQUEADA`.
- **Contexto:** o Elenco é a única aba do site sem nada. A Início conectada em 07/09 continua
  declarando "Elenco e análises ainda não conectados", porque não existe contrato nem definição
  do que é "meu elenco".
- **Bloqueio:** depende de decisão do usuário sobre o que a área deve ser — lista dos cards que
  ele possui, escalação no campinho, ou os dois — e de um contrato de usuário e de escrita, que
  o manual exige especificar antes da implementação.
- **Critério objetivo de conclusão:** decisão registrada, contrato definido e validado, e a área
  entregue lendo dados reais.
- **Evidência de fechamento:** ainda não existe.


## SITE-NOVO-PEND-014 — coerência Box e Ficha

Estado: PENDENTE. Box combina pontuacao_maxima com identidade de analises[0]. Caso reproduzido: Makélélé 88045755964130, linha 379892, 109,55 na Box e 109,45 na Ficha; 109,55 é construção, destino é contenção. Critério: nota, rótulo, etiqueta e link devem ter escopo explícito e coerente, preservando o contrato de contratação.

## SITE-NOVO-PEND-015 — Ficha em celular

Estado: PENDENTE. A 375 px, nome e estilo quebram em fragmentos e campo fica estreito. Critério: conteúdo legível em 375/390 px, sem alterar desktop aprovado. Ver AUDITORIA-SITE-20260908.md para outras recomendações.

## Correções do Ranking — 08/09

Concluídas: excluir eixo do corpo RPC e limpar filtros invisíveis de outras abas na restauração. Testes de transporte e restauração cobrem os três eixos; suíte 15/15. Deploy 6aa0946c7a2721d1c2966e1f.

## SITE-NOVO-PEND-016 — Ficha lenta e 500 intermitente

- **Abertura:** 2026-09-11. **Estado:** `RESOLVIDA` em 11/09/2026.
- **Contexto:** a Ficha ficava em "Consultando a Ficha", devolvia 500 de vez em quando e
  levava ate 2 s para trocar de especialidade. Medido no navegador: um clique gera uma
  chamada so, nao havia funcao duplicada na tela.
- **Causa:** `site_novo_ficha_v2` consultava `build_pontuacao_final_v3_exibivel`, que tem
  `row_number()` e `max() over (partition by funcao_id)`. Funcao de janela nao deixa o
  filtro descer, entao o banco montava as 59 mil linhas inteiras para achar uma. O plano
  mostrava cerca de 52 MB de arquivo temporario por requisicao, origem do 500.
- **Correcao:** migracao `ficha_v2_sem_varredura_da_view_de_ranking`. A consulta passou a
  ler `build_publicacao_exibivel_v3`, sem funcao de janela, aceitando filtro pela chave.
- **Prova:** o trecho isolado caiu de 1.522 ms para 0,66 ms; a ficha pela internet, de 1,1
  a 2,0 s para 134 ms de media em 14 cards; abrir do zero no navegador, 85 ms. As duas
  views tem as mesmas 59.122 linhas, zero divergencia, e o vetor de ids bateu em 40 de 40
  linhas testadas.
- **Metodo que fica:** view com funcao de janela nao serve para buscar uma linha pela
  chave. E 500 intermitente quase nunca e rede.

## SITE-NOVO-PEND-017 — nota do Zagueiro de Saida e inflada

- **Abertura:** 2026-09-12. **Estado:** `PENDENTE`, por decisao do usuario.
- **Contexto:** os dois moldes de zagueiro tem 25 dos 26 pesos identicos; so Aceleracao
  difere (3 no Combate, 0 na Saida). Os alvos da Saida sao mais baixos, e como a nota e
  soma(peso x valor) / soma(peso x alvo) x 100, alvo menor no denominador produz nota
  maior sem merito. A Saida ganha do Combate em 941 de 1.013 cards, 92,9%, por 3,49
  pontos em media.
- **Impacto:** no ranking geral e no POR CARD, os zagueiros de saida sobem por causa do
  denominador, nao por rendimento, contra todas as outras especialidades.
- **Decisao do usuario em 12/09:** nao mexer no molde por enquanto; resolver apenas a
  mistura das listas.
- **Criterio objetivo de conclusao:** alvos da Saida no mesmo nivel de dificuldade do
  Combate, ou molde refeito. Invalida as linhas da funcao 19.

## SITE-NOVO-PEND-018 — o molde do Zagueiro de Saida nao mede saida de bola

- **Abertura:** 2026-09-12. **Estado:** `PENDENTE`, por decisao do usuario.
- **Contexto:** peso ZERO em Passe rasteiro, Passe alto, Controle de bola e Conducao
  firme. A especialidade cujo nome e "de saida" mede so defender. Achado ja registrado em
  12/08 e reconfirmado agora.
- **Criterio objetivo de conclusao:** peso real nos atributos de bola, com remontagem das
  linhas da funcao 19.

## SITE-NOVO-PEND-019 — bonus de estilo depois da regra nova dos zagueiros

- **Abertura:** 2026-09-12. **Estado:** `RESOLVIDA` em 12/09/2026, sem necessidade de
  remontar linha nenhuma.
- **Contexto:** ao acrescentar Cobertura (349) e Mestre da Linha Alta (350) na
  `bonificador_regra_playstyle`, a suspeita era que as cartas com esses estilos passassem
  a receber bonus novo, deixando as notas ja publicadas defasadas.
- **O que se descobriu:** os dois estilos **ja estavam** na tabela, em linhas com
  `funcao_id` NULO, dando bonus **por posicao**. As duas linhas novas apenas amarraram os
  estilos a funcao 18. O valor do bonus nao mudou.
- **Prova:** `conferir_bonus_estilo_0909_v1` rodado com a regra vigente sobre **todas as
  2.682 linhas publicadas** das funcoes 18 e 19, usando os estilos efetivos de
  `carta_estilos_efetivos_v12`: 1.341 e 1.341, **zero divergencia** entre o bonus gravado e
  o recalculado.
- **Efeito colateral corrigido na mesma entrega:** o insert levou a tabela de 90 para 92
  linhas e derrubou a trava de cardinalidade da `bonificador_regua_v1`, que passou a
  devolver `pode_rodar: false` com a falta
  `bonificador_regra_playstyle: cardinalidade diferente de 90`. **O Bonificador ficaria
  impedido de rodar.** Consertado pela migracao
  `bonificador_regua_cardinalidade_92_regras_de_playstyle`, que atualizou a constante da
  trava e o bloco `cardinalidades` para 92. Readback: `pode_rodar: true`, `falta_o_que`
  vazio, em `clube_novo.bonificador_regua_v1` e na porta `public.bonificador_regua_v2`.
- **Licao:** a `bonificador_regua_v1` tem travas de cardinalidade escritas na unha. Toda
  linha inserida ou removida em `bonificador_parametro`, `bonificador_molde_corpo`,
  `bonificador_posicao_slot` ou `bonificador_regra_playstyle` exige atualizar a constante
  correspondente na mesma entrega, e conferir `pode_rodar` depois.

## SITE-NOVO-PEND-020 — o Otimizador monta as duas funcoes de zagueiro

- **Abertura:** 2026-09-12. **Estado:** `RESOLVIDA` em 12/09/2026, por decisao do usuario:
  **fica como esta, de proposito.**
- **Contexto:** `otimizador_funcao_posicao` roteia so por posicao, nao por estilo. Toda
  carta ZC recebe build de Combate e de Saida.
- **Decisao do Luis:** deixar o Otimizador montar as duas. Se a regra do estilo mudar
  depois, as builds ja estao prontas e basta trocar o filtro da view; nao ha nada para
  recalcular. O custo de fila e o preco da reversibilidade.
- **Nao reabrir** este item como desperdicio de fila sem decisao nova do usuario.

## SITE-NOVO-PEND-021 — os 318 que ficaram fora das duas listas de zagueiro

- **Abertura e resolucao:** 2026-09-12. **Estado:** `RESOLVIDA`.
- **Contexto:** a primeira versao da regra do estilo deixava **fora das duas listas** o card
  que nao e ZC nativo e nao tinha estilo de zagueiro. Eram 318 cards. Isso foi apresentado
  ao Luis como "o estilo separa sozinho", olhando so os rotulos dos estilos.
- **O erro:** os 318 nunca foram olhados pelo nome nem pela nota. Entre eles estavam Paolo
  Maldini lateral (110,92), Lilian Thuram (110,68), Giuseppe Bergomi (109,98), Aurelien
  Tchouameni (108,94) e Javier Zanetti (108,40). O Luis pegou na tela.
- **Decisao do Luis:** *"o cara tem um lateral, ele pode comprar a posicao de zagueiro, e
  precisa saber se ele rende mais na contencao ou saindo jogando."* Ninguem fica de fora.
- **Correcao:** migracoes `roteamento_de_estilo_dos_zagueiros_sem_bonus`,
  `bonificador_regua_cardinalidade_105_regras_de_playstyle` e
  `zagueiros_ninguem_fora_roteamento_completo_por_estilo`. Todos os 18 estilos que aparecem
  em carta com build de ZC foram roteados: Lateral Defensivo, Primeiro Volante e
  Interceptador De Passe para o Combate; Lateral Ofensivo, Meia Versatil, Orquestrador,
  Perito Em Cruzamento, Jogador De Infiltracao, Lateral Atacante, Homem De Area, Classico
  N 10, Armador Criativo e Atacante Pivo para a Saida.
- **`da_bonus = false` nas 13 linhas novas**, de proposito: o card de outra posicao
  **aparece** na lista certa mas **nao ganha ponto** por um estilo que nao e do oficio. E o
  problema do impostor, registrado em 26/08.
- **Prova:** Combate 404 cards, Saida 621, 10 nas duas, **zero fora**. Goleiros intactos em
  181 e 314. Regua do Bonificador `pode_rodar: true`. Bonus conferido nas 2.682 linhas
  publicadas das duas funcoes, **zero divergencia**. Site no ar mostra 404 e 621, com
  Maldini, Pepe e Thuram no topo do Combate.
- **Licao de metodo:** classificar por rotulo nao e medir. Antes de declarar um grupo como
  ruido, olhar os nomes e as notas de quem esta dentro dele.

## SITE-NOVO-PEND-022 — o sistema nao tem a descricao oficial de nenhum estilo de jogo

- **Abertura:** 2026-09-12. **Estado:** `PENDENTE`.
- **Contexto:** `clube_novo.playstyle` tem `id_texto` e `secao_texto` apontando para
  `texto_do_jogo`, mas nenhum dos 36 estilos devolve uma descricao de comportamento.
- **Medido nos 36 estilos:**
  - secao `E15W`, 21 estilos: o texto devolvido e **o proprio nome** do estilo, sem
    descricao;
  - secao `E6W`, 5 estilos: idem, so o nome;
  - secao `E6T`, 9 estilos, e `E13W`, 1 estilo: o texto devolvido **nao e do estilo**. Sao
    textos de atributo de goleiro e de habilidade. Exemplos: Defensor Criativo devolve
    "capacidade do goleiro de afastar chutes evitando rebotes"; Lateral Ofensivo devolve
    "capacidade do goleiro em segurar a bola"; Orquestrador devolve "agressividade da
    marcacao"; Perito Em Cruzamento devolve "mudar a direcao ao driblar".
- **Impacto:** nao existe fonte oficial no sistema para dizer o que um estilo faz em campo.
  Toda afirmacao sobre comportamento de estilo hoje vem de pesquisa externa ou de deducao,
  nunca do arquivo do jogo.
- **Criterio objetivo de conclusao:** achar no `all.str` a secao das descricoes de estilo,
  carregar em `texto_do_jogo` e religar os 36 `id_texto`. Ate la, `falta_o_que` dos estilos
  deveria registrar essa ausencia, e hoje esta nulo nos 36.

## SITE-NOVO-PEND-023 — a divisao dos 13 estilos entre Combate e Saida nao foi medida

- **Abertura:** 2026-09-12. **Estado:** `PENDENTE`.
- **Contexto:** o roteamento de Lateral Defensivo, Primeiro Volante, Interceptador De
  Passe, Lateral Ofensivo, Meia Versatil, Orquestrador, Perito Em Cruzamento, Jogador De
  Infiltracao, Lateral Atacante, Homem De Area, Classico N 10, Armador Criativo e Atacante
  Pivo entre as duas especialidades de zagueiro foi **julgamento**, pelo criterio "trabalho
  sem bola vai para o Combate, quem sai com a bola ou sobe vai para a Saida".
- **Por que nao foi medido:** a descricao oficial de estilo nao existe no sistema
  (PEND-022). Nao havia dado do proprio sistema para consultar.
- **O que esta no ar:** a divisao aprovada pelo Luis em 12/09, aplicada na
  `bonificador_regra_playstyle` e na `build_publicacao_exibivel_v3`. Ela nao afeta nota
  nenhuma, so a lista em que o card aparece, e as 13 linhas tem `da_bonus = false`.
- **Criterio objetivo de conclusao:** com PEND-022 resolvida, reconferir cada um dos 13
  contra a descricao do jogo e corrigir o que divergir. Enquanto isso, **nao apresentar
  essa divisao como medida**.

## SITE-NOVO-PEND-024 — o Extrator le a Sobreposicao no endereco errado

- **Abertura:** 2026-09-12. **Estado:** `PENDENTE`. **Gravidade:** alta.
- **Contexto:** o jogo tem 6 estilos de tecnico; o banco carregou 5. Os cinco antigos vieram
  do `Coach.bin` numa faixa vizinha (bits 199, 206, 213, 224, 238, largura 7) no
  carregamento de 28/08 02:23:18. A Sobreposicao foi lida no bit **135**, fora da faixa, num
  carregamento separado as 04:24:57, e pegou **um unico tecnico**: Antonio Conte, com o valor
  **96**, quando o real e **69**.
- **Impacto ja medido:** o 96 fantasma fazia do Conte o maior multiplicador da base inteira.
- **O que foi feito em 12/09:** os 64 tecnicos que entram no Otimizador foram conferidos no
  efHub e corrigidos a mao. **O Extrator nao foi corrigido.**
- **Risco de regressao:** quando o Extrator rodar de novo, ele reescreve pelo `Coach.bin` e
  volta a gravar 96 no Conte e a nao gravar Sobreposicao nos outros.
- **Criterio objetivo de conclusao:** achar no `Coach.bin` o bit correto da Sobreposicao
  (deve continuar a faixa dos outros cinco, largura 7), conferir contra o efHub em pelo menos
  5 tecnicos, e so entao recarregar.

## SITE-NOVO-PEND-025 — 1.414 tecnicos continuam com o dado velho

- **Abertura:** 2026-09-12. **Estado:** `PENDENTE`.
- **Contexto:** a conferencia de 12/09 cobriu os **65** tecnicos que entram no Otimizador
  (os que tem impeto). Os outros **1.414** de `tecnico_jogo` continuam com 5 estilos e com o
  impeto como veio do Extrator.
- **Por que nao entrou agora:** tecnico sem impeto nao e escolhido pelo motor
  (`carrega_tecnicos_do_banco` descarta quem nao tem boost). Nao afeta nota nenhuma hoje.
- **Quando vira problema:** se algum deles ganhar impeto numa atualizacao do jogo, entra na
  disputa com o dado errado.
- **Criterio objetivo de conclusao:** PEND-024 resolvida e recarga completa pelo Extrator,
  com conferencia por amostra contra o efHub.

## SITE-NOVO-PEND-026 — `otimizador_producao_preparar_fatia_v6` esta pareada com a formula errada

- **Abertura:** 2026-09-12. **Estado:** `PENDENTE`. **Gravidade:** media.
- **Contexto:** a criacao do lote integral (v5 e v6) exige
  `formula_fingerprint = a1cc830a...`. A `preparar_fatia_v6` exige `7aaa3ccc...`, que e a
  formula de 31/08. Resultado: ela recusa qualquer lote criado pela via vigente com
  "selo do lote nao e a formula aprovada".
- **O que esta em uso:** `otimizador_producao_preparar_fatia_v5`, que aceita `a1cc830a...` e
  exige o lote em estado `preparando`.
- **Criterio objetivo de conclusao:** decidir qual das duas e a vigente e alinhar o selo, ou
  aposentar a v6.

## SITE-NOVO-PEND-027 — `tests/ranking.test.cjs` e `tests/search.test.cjs` ja estavam quebrados

- **Abertura:** 2026-09-12. **Estado:** `PENDENTE`. **Gravidade:** baixa.
- **Contexto:** ao mexer em `ranking.js` e `search.js` para o selo da regua, rodei os testes.
  Os dois falham. Rodei tambem com os arquivos **originais, intocados**: falham igual.
- **Erro:** `Error: Resposta do Ranking incompativel.` — o `validate` de `ranking-api.js`
  recusa o fixture `tests/fixtures/ranking-publico-33-20260906.json`. O fixture e de 06/09 e
  o contrato do ranking mudou depois. `search.test.cjs` cai na mesma familia.
- **Nao e regressao do selo.** Registrado para nao atribuir a falha a mudanca errada depois.
- **Criterio objetivo de conclusao:** regravar os fixtures a partir da RPC vigente e voltar
  os dois testes ao verde.

## SITE-NOVO-PEND-028 — as 57.891 linhas da tela estao todas com a regua antiga

- **Abertura:** 2026-09-12. **Estado:** `EM ANDAMENTO`.
- **Contexto:** com os tecnicos corrigidos, nenhuma linha publicada foi calculada com a regua
  vigente. Medido: `regua_vigente = false` em **57.891 linhas, 4.503 cards**; `true` em zero.
- **O que foi feito:** a tela passou a marcar cada linha com a etiqueta "Regua antiga"
  (SITE-NOVO no MANUAL, secao de 12/09), e a fila nova do Otimizador
  (`12090000-0000-4000-8000-000000001209`) foi criada com a regua corrigida selada. Depois do
  aditivo das cartas de Impeto condicional e da limpeza das linhas presas em lotes aposentados
  (PEND-029 e PEND-030), a fila fechou com **20.602 candidatas, 19.030 cartas e 192.276 linhas
  pendentes**, unica fila pendente do banco.
- **Criterio objetivo de conclusao:** `select count(*) from
  clube_novo.build_publicacao_exibivel_v3 where regua_vigente is false` chegar a zero.
- **Rede de seguranca:** `clube_novo.publicacao_snapshot_antes_1209` guarda as 59.714
  publicacoes como estavam antes de 12/09.

## SITE-NOVO-PEND-029 — `criar_lote_integral_v6` exclui as cartas de Impeto condicional

- **Abertura:** 2026-09-12. **Estado:** `PENDENTE`. **Gravidade:** alta.
- **Contexto:** `public.otimizador_producao_criar_lote_integral_v6` (herdado da v5) seleciona
  candidatas com `not exists (carta_impeto_jogo where condicional)` e conta o resto em
  `excluidas_impeto_condicional`. So que o contrato do pacote local v2 ja declara
  `impetos_condicionais = 'por_degrau'`, `preparar_fatia_v5` ja multiplica a carta pelos 3
  degraus, e o banco ja tem **29.511 linhas condicionais concluidas, 27.430 publicadas**.
- **Efeito medido na fila 1209:** 1.184 cartas condicionais elegiveis ficaram de fora
  (7.434 linhas pendentes orfas em lotes aposentados). Sem correcao, as 27.430 publicacoes
  condicionais ficariam marcadas "Regua antiga" para sempre.
- **Contorno aplicado em 12/09:** as 1.184 cartas foram inseridas a mao em
  `otimizador_lote_producao_candidata_v5`, `preparo_total` somou 1.184, o lote voltou a
  `preparando` e o preparo rodou ate 20.602/20.602. Documentado no MANUAL-DO-OTIMIZADOR,
  secao de 12/09.
- **Criterio objetivo de conclusao:** tirar o filtro do corpo da `criar_lote_integral_v6`
  (ou publicar uma v7) e confirmar, criando um lote de teste, que as cartas condicionais
  entram como candidatas sem aditivo manual.

## SITE-NOVO-PEND-030 — linhas pendentes ficam presas em lotes aposentados

- **Abertura:** 2026-09-12. **Estado:** `CONTORNADA`. **Gravidade:** alta.
- **Contexto:** `preparar_fatia_v5` cria linhas **novas** em `build_linha_card` para cada
  (carta, funcao, posicao, degrau); nao reaproveita as linhas que a carta ja tinha. Quando um
  lote integral e aposentado, as linhas dele que estavam `pendente` continuam `pendente`
  apontando para o lote morto. Como a maquina 2 processa somente o lote vivo, essas linhas
  nunca rodam e nunca aparecem em contagem nenhuma da fila.
- **Medido em 12/09:** **131.938 linhas pendentes** em 7 lotes `concluido` — 124.504 delas
  gemeas exatas de linhas da fila 1209, e 7.434 das cartas condicionais da PEND-029.
  Nenhuma tinha build nem publicacao ativa.
- **Contorno aplicado:** todas foram marcadas `estado_otimizador = 'interrompido'` com
  `erro_otimizador = 'retirada: linha equivalente vive na fila integral 12090000-...-1209'`.
  Conferencia: nenhuma linha `pendente` fora do lote 1209 em todo o banco.
- **Criterio objetivo de conclusao:** a aposentadoria de lote passar a retirar as linhas
  pendentes dele no mesmo ato, para a conferencia nao depender de varredura manual.

## SITE-NOVO-PEND-031 — 1.571 cartas sem evidencia fisica de nivel/orcamento

- **Abertura:** 2026-09-12. **Estado:** `PENDENTE`. **Gravidade:** media.
- **Contexto:** `clube_novo.otimizador_prioridade_orcamento_v1` exige linha em
  `clube_novo.carta_nivel_evidencia_v1` com `nivel_maximo >= 1` e
  `orcamento_real = 2 * (nivel_maximo - 1)`. 1.571 cartas nao tem essa evidencia capturada;
  **1.561 delas sao `tipo_carta_id = 'player_delete_list'`** (cartas fora do jogo) e 10 sao
  cartas comuns (Raphinha 83, Ruben Dias 82, Rodrigo De Paul 82, Pavlovic 81, Grimaldo 81,
  Dean Henderson 81, Malen 80, Akliouche 80, Lamlaoui 79, Sawakami 76).
- **Efeito:** o criador do lote as aceita como candidatas, mas a fotografia as exclui. Na fila
  1209 isso deixaria 12.955 pendentes eternas. Foram retiradas com
  `erro_otimizador = 'retirada da fila 1209: carta sem evidencia fisica de nivel/orcamento em
  carta_nivel_evidencia_v1'`. Nenhuma tinha publicacao ativa.
- **Criterio objetivo de conclusao:** decidir se `player_delete_list` deve ser excluida ja na
  criacao do lote, e capturar a evidencia fisica das 10 cartas comuns.

## SITE-NOVO-PEND-032 — o `complemento_contexto_v14()` tem a versao do molde escrita fixa

- **Abertura:** 2026-09-12. **Estado:** `PENDENTE`. **Gravidade:** alta.
- **Contexto:** so duas funcoes do banco leem `clube_novo.otimizador_molde`:
  `public.otimizador_regua_v2()`, que usa `select max(versao)`, e
  `public.complemento_contexto_v14()`, que tem **`where m.versao=5` cravado no
  corpo**. Ao publicar o molde v6, a regua adota sozinha e o complemento fica
  com os pesos velhos — as duas pecas divergem sem aviso.
- **Conserto:** trocar por `(select max(versao) from clube_novo.otimizador_molde)`.
- **Criterio objetivo de conclusao:** `prosrc` da `complemento_contexto_v14()`
  nao conter mais numero de versao literal.

## SITE-NOVO-PEND-033 — a mediana por familia e muito desigual (defesa e goleiro somem do ranking)

- **Abertura:** 2026-09-12. **Estado:** `PENDENTE`. **Gravidade:** media.
- **Contexto:** o ranking geral tem, no top 100, 45 cards de MEIO, 39 de ATAQUE,
  **13 de DEFESA e ZERO de GOLEIRO** — sendo que defesa tem 1.127 cards e
  goleiro 377.
- **Nao e a normalizacao.** Medido o aproveitamento sobre o teto de cada funcao,
  o topo de todas as familias chega quase ao mesmo lugar: MEIO 97,8%,
  DEFESA 97,2%, ATAQUE 97,0%, GOLEIRO 93,8%. A regua e justa no topo.
- **O que separa e a MEDIANA:** MEIO −25,0 · ATAQUE −36,8 · DEFESA −58,0 ·
  GOLEIRO −80,1. A massa de cards defensivos esta muito mais longe dos proprios
  alvos que a massa do meio.
- **Portanto:** ou os moldes de defesa e goleiro cobram mais do que a posicao
  entrega, ou os cards defensivos do jogo sao mesmo mais fracos em relacao a
  elite deles. Assunto de molde por funcao, **nao** de formula de normalizacao.
- **Criterio objetivo de conclusao:** decidir se se revisa os moldes de defesa e
  goleiro; se sim, medir alvo x p90 de cada uma como foi feito no Meia Armador.

## SITE-NOVO-PEND-034 — molde v6 publicado: fila e publicacoes precisam ser refeitas

- **Abertura:** 2026-09-12. **Estado:** `EM ANDAMENTO`.
- **Contexto:** o molde v6 (Meia Ofensivo Finalizacao 89; Meia Armador
  Velocidade e Aceleracao 85) muda o `contrato_fingerprint`. Toda publicacao
  existente passa a ser "Regua antiga" e a fila em curso fica invalida.
- **O que a mudanca exige:** molde v6 no banco, conserto da PEND-032,
  `clube_novo.regua_vigente_v1` atualizada, fila 1209 aposentada, fila nova
  criada e preparada (com o aditivo das condicionais da PEND-029), maquina 2
  baixando o pacote novo.
- **Passo a passo completo:** `4-DOCUMENTOS/CONTEXTO-E-PLANO-1209-MOLDE-V6.md`.
- **Criterio objetivo de conclusao:** `select count(*) from
  clube_novo.build_publicacao_exibivel_v3 where regua_vigente is false` chegar
  a zero, com o molde v6 vigente.
