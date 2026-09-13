## Fechamento do complemento — conferido em 10/09/2026

Instalacao da maquina2 e rodada corretiva concluidas: 751 linhas analisadas,
560 corrigidas, 191 sem candidata elegivel. As560 possuem publicacao ativa;
524 exibiveis e36 ocultas corretamente pela separacao dos estilos de goleiro.
Atributos, notas, etapas e adicionais foram conferidos em todas as560.

O editor site_novo_editor_avaliar_v1 chama build_editor.avaliar_v1, o mesmo
avaliador usado pelo writer corretivo para validar cada resultado. Runtime e
corretor coincidiram nos casos36564 e34628. Writers locais e v3/v6 validam e
persistem origem complementar. Frontend publicado conferido: chip discretamente
mais claro e hover Complementar; escolhas manuais nao sao preenchidas sozinhas.

O usuario informou retomada do otimizador/enviador. Na leitura deste fechamento,
ainda nao havia resultado novo em build_complemento_v14; isso nao desfaz as560
correcoes, guardadas em complemento_recibo_v14. Confirmacao da retomada pelo
usuario nao e prova de chegada do primeiro JSON novo ao banco.

Regras e evidencia: 4-DOCUMENTOS/OTIMIZADOR/COMPLEMENTO-1009/ENCERRAMENTO-RODADA.md.
Os registros de instalacao/correcao pendentes abaixo sao historicos.

## Complementares V14 — 10/09/2026

A ficha recebe `complementar` por habilidade do contrato site_novo_ficha_v2,
associado ao build efetivamente publicado. Mesmo formato, verde discretamente
mais claro, hover somente **Complementar**. Sem badge ou calculo local de nota.
O editor permanece manual; reavalia as builds locais no banco ao abrir,
preservando as regras atuais e as alteracoes de design. Regra completa:
[Complemento](../4-DOCUMENTOS/OTIMIZADOR/COMPLEMENTO-1009/REGRA-APROVADA.md).

# Manual do Site Novo

## Normalização e estrelas — decisão de 09/09/2026

A nota vem normalizada do banco pela versão `normalizacao-bonus-integral-20260909-v1`, com bônus integrais somados depois. Editor pessoal usa a mesma escala no servidor. Boxes exibem cinco estrelas de contratação (campo `estrelas`, inteiro 0–5), com legenda mantendo os seis textos anteriores. Não confundir com as estrelas nativas da imagem. Contratos sem a equivalência são recusados; não existe fallback por nota ou código. Separação de goleiros é feita nos leitores, sem alterar motores. Decisão completa: [../4-DOCUMENTOS/NORMALIZACAO-0909/REGRA-APROVADA.md](../4-DOCUMENTOS/NORMALIZACAO-0909/REGRA-APROVADA.md).

## Política vigente de habilidades — 09/09/2026

A política `habilidades-funcao-20260909-v1` está aplicada no `clube_novo` e no runtime oficial da Máquina 1. A matriz vigente tem 325 pares habilidade/função. O motor conserva de zero a cinco adicionais úteis; não preenche vagas sem ganho. Todas as sugestões automáticas, inclusive gêmeas de builds antigas, respeitam os bloqueios atuais da função. A escolha manual do usuário e as habilidades nativas continuam livres desses vetos estratégicos.

Banco, fontes, executável e fotografias locais foram sincronizados; lotes continuam pausados e na mesma ordem. A normalização da nota não mudou. A revisão local identificou 4.509 linhas para análise posterior; nenhum resultado antigo foi regravado ou despublicado nesta etapa. A instalação na Máquina 2 e a publicação do frontend são estados separados.

Regra completa, matriz, migrações, testes e evidências: [Habilidades por função V12](../4-DOCUMENTOS/OTIMIZADOR/HABILIDADES-0909/REGRA-APROVADA.md). Os registros anteriores abaixo conservam o contexto da época e não substituem esta revisão.

Versão inicial: 04/09/2026  
Projeto: reconstrução do frontend do ClubEfootball  
Primeira página: Ficha

## 1. Autoridade deste manual

Este é o manual autoritativo e vivo do **Site Novo**.

Ele deve ser atualizado em toda mudança importante de:

- arquitetura;
- contrato ou formato de dados;
- fonte de dados;
- layout aprovado;
- página ou módulo;
- estado operacional;
- fluxo de leitura ou escrita;
- decisão expressa do usuário.

Uma mudança importante não está concluída enquanto este manual não registrar:

1. o que mudou;
2. por que mudou;
3. quais partes foram afetadas;
4. qual evidência comprova a mudança;
5. qual readback confirmou o estado final.

Em caso de divergência, vale a decisão mais recente do usuário registrada aqui. Documentos de inventário e checkpoints continuam servindo como evidência datada, mas não substituem esta autoridade viva.

Documentos-base desta primeira versão:

- `ARQUITETURA-E-INVENTARIO-INICIAL.md`;
- `CHECKPOINT-REFORMA-A-2026-09-04.md`;
- `AUDITORIA-APOSENTADORIA-SITE-ANTIGO-2026-09-04.md`;
- `RECUPERACAO-VIEWS-SITE-ANTIGO-2026-09-04.sql`;
- `RECUPERACAO-VIEWS-FICHA-SITE-ANTIGO-2026-09-04.sql`;
- `PREVIA-FICHA.html`;
- `PREVIA-FICHA.png`.

## 2. Diretório oficial

Todo arquivo novo desta reconstrução pertence exclusivamente a:

`C:\Users\Luis Fernando\Downloads\ClubEFootball--main\ClubEFootball--main\Site Novo`

Arquivos antigos encontrados em outras pastas são evidência, referência visual ou inventário. Eles não são a implementação do Site Novo.

## 3. Regra fundamental da reconstrução

O Site Novo será reconstruído **do zero funcionalmente**.

É proibido usar como base do novo sistema:

- lógica do Encaixe antigo;
- funções antigas;
- fórmulas ou cálculos antigos;
- queries antigas;
- contratos antigos como arquitetura nova;
- componentes de dados antigos;
- regras de ranking, pontuação ou classificação antigas;
- processamento ou migrações antigas;
- arquitetura anterior;
- tabelas ou schemas legados como fallback.

Pode ser reaproveitado somente o desenho visual que o usuário aprovou.

Código antigo pode ser lido para inventário, rastreio ou prova de fronteira. Essa leitura não autoriza copiar seu comportamento.

## 4. Layout oficial e congelado da Ficha

O usuário confirmou como layout oficial e exato:

- `PREVIA-FICHA.html`;
- `PREVIA-FICHA.png`.
- para o Bloco 1, a decisão visual mais recente é `REFERENCIA-BLOCO-1-APROVADA-2026-09-04.png`.

A origem visual rastreada foi `1-SISTEMA/ficha-aprovada.css` e `4-DOCUMENTOS/FICHA-DESIGN-APROVADO-0409.html`. A origem não transfere JavaScript, fórmulas, queries, contratos ou comportamentos antigos para o projeto novo.

### 4.1 O que está congelado

Devem ser preservadas:

- a posição de todos os blocos;
- a hierarquia entre blocos e conteúdos;
- as relações verticais e laterais;
- a grade principal;
- a ordem visual das regiões;
- a identidade visual aprovada.

Podem evoluir dentro desse desenho:

- conteúdo;
- dados;
- estados;
- comportamento novo;
- acessibilidade;
- implementação modular.

Essas evoluções não podem redesenhar a grade nem deslocar a função visual de um bloco sem nova decisão expressa do usuário e atualização deste manual.

### 4.2 Quatro blocos oficiais

1. **Bloco superior:** identidade do jogador, `nota_final`, possibilidade de melhora já publicada, estilo e posição nativos, ação de elenco e campo de posições.
2. **Bloco de contexto da build:** identificação da build em exibição, acesso à melhor recomendação, atalhos preparados para builds do usuário e personalização, e faixa/lista de builds.
3. **Bloco de trabalho da build:** distribuição, otimização e técnico à esquerda; habilidades, ímpetos e ações à direita; atributos abaixo.
4. **Bloco inferior:** estilos de IA, dados físicos, pé e medidas corporais.

A largura visual de referência é aproximadamente 960 px no desktop.

Os Blocos 1 e 4 são regiões passivas de leitura e permanecem visualmente neutros, sem títulos redundantes que expliquem o conteúdo já evidente. Os Blocos 2 e 3 formam juntos a **Área da Build**, indicada por uma moldura compartilhada e um fundo verde-petróleo perceptivelmente diferente dos blocos passivos, sem brilho forte e sem `padding` horizontal que reduza a largura útil. O cabeçalho dessa área informa o estado corrente da relação com a build; nesta fase de leitura pública, `VISUALIZANDO RECOMENDAÇÃO`.

### 4.3 Referência mais recente do Bloco 1

Em 04/09/2026, o usuário aprovou uma nova captura específica para o Bloco 1: `REFERENCIA-BLOCO-1-APROVADA-2026-09-04.png`.

A captura confirma, sem mudar a hierarquia já implementada:

- identidade à esquerda, com card e nome;
- pontuação, “Pode melhorar” e elenco nas três primeiras faixas da coluna imediatamente à direita da identidade;
- estilo de jogo e posição nativa na quarta faixa dessa mesma coluna, abaixo dos três controles e ainda imediatamente ao lado da identidade;
- o conjunto de estilo de jogo e posição nativa fica apoiado no rodapé da quarta faixa; seu último conteúdo termina alinhado ao término do nome do jogador na coluna de identidade, sem flutuar no centro do espaço restante;
- quatro colunas de largura idêntica: identidade, pontuação/conteúdo nativo, respiro central e campo de posições;
- campo de posições ocupando toda a lateral direita.

Em 04/09/2026, após conferir a Ficha no navegador, o usuário corrigiu a divisão desigual anterior (`196px 172px 1fr 250px`). A largura útil geral permanece em `960px`, sem reduzir a área entre os banners; somente a grade interna do Bloco 1 passa a usar `repeat(4, minmax(0,1fr))`. Dentro da largura interna atual, cada coluna fica com aproximadamente `218px` em CSS, ou cerca de `273px` na escala de 125% do Windows. Essa decisão não altera os Blocos 2, 3 e 4.

Os controles do Paint e a área branca abaixo da seleção não integram o desenho do site. A referência vale somente para a área escura do Bloco 1.

## 5. Banco oficial e fronteira de acesso

O único banco operacional autorizado é `clube_novo`.

Nenhum schema legado pode ser fonte, destino, fallback ou mecanismo de compatibilidade do Site Novo.

O fato de uma tabela, view ou função existir não a transforma automaticamente em contrato do frontend. O contrato precisa ser:

- público pelo canal aprovado;
- explícito;
- versionado;
- validado;
- autorizado para o papel correto;
- estável no checkpoint usado pela implementação.

Como o banco estava sendo alterado durante esta reconstrução, snapshots transitórios não podem virar arquitetura. Todo consumo deve ser associado a um checkpoint estável e a um readback atual.

## 6. Arquitetura obrigatória de leitura

O fluxo de leitura da Ficha é:

```text
clube_novo
    ↓
RPC/API pública versionada
    ↓
módulo JavaScript de acesso / adaptador
    ↓
modelo de tela estável da Ficha
    ↓
renderizador JavaScript da Ficha
    ↓
HTML
```

Essa cadeia separa **responsabilidades conceituais**, não obriga um arquivo físico para cada seta. Na primeira implementação, chamada, validação, modelo de tela e renderização ficam organizados em seções internas de um único `ficha.js`.

### 6.1 Responsabilidade de cada camada

#### `clube_novo`

- guarda a autoridade operacional dos dados;
- publica somente os valores já finalizados pelo fluxo autorizado;
- não é consultado diretamente pelo HTML.

#### RPC/API pública versionada

- é o contrato de fronteira entre banco e frontend;
- define parâmetros, tipos, nulabilidade, ordenação, filtros, versão e estados;
- aplica a autorização própria do caso de uso;
- não será inventada pelo frontend.

Nenhum nome de contrato futuro está aprovado apenas por aparecer neste manual. O contrato exato será registrado quando for definido e validado.

#### Módulo JavaScript de acesso / adaptador

- é a única camada do Site Novo que conhece nomes e formatos do contrato público;
- isola a página de mudanças de view, RPC ou payload;
- valida versão, chaves, tipos, nulabilidade e estado de publicação;
- trata indisponibilidade, erro, resposta incompleta e contrato incompatível;
- transforma a resposta em DTO/modelo estável para a Ficha;
- falha fechado quando o contrato não pode ser comprovado.

O adaptador não cria dados ausentes, não calcula nota e não substitui o banco.

#### Modelo de tela da Ficha

- contém somente o que a página precisa renderizar;
- usa nomes estáveis do domínio visual da Ficha;
- não replica linha de tabela nem JSON bruto de RPC;
- representa explicitamente os estados `carregando`, `vazio`, `bloqueado`, `erro` e `pronto`.

#### Renderizador JavaScript

- recebe o modelo de tela validado;
- preenche os blocos oficiais;
- alterna estados visuais;
- não consulta banco, tabela, view ou RPC;
- não calcula regras de negócio.

#### HTML

- define estrutura e pontos de montagem;
- preserva o layout aprovado;
- não conhece tabelas;
- não conhece nomes internos do banco;
- não consulta o banco;
- não calcula nota, ranking, percentual, bônus ou composição.

### 6.2 Por que não consultar tabela diretamente

Uma consulta direta à tabela também exigiria JavaScript, mas faria esse JavaScript conhecer schema, tabela, colunas, relacionamentos e mudanças internas do banco. Isso acoplaria a Ficha à estrutura de persistência e multiplicaria os pontos de quebra.

Uma RPC/API pública versionada única para a leitura da Ficha reduz:

- o contrato exposto;
- o número de permissões públicas;
- o conhecimento do frontend sobre o banco;
- os pontos que podem quebrar quando o schema mudar.

O `ficha.js` conhece somente essa fronteira pública aprovada. Ele não conhece nem consulta `clube_novo.build_linha_card` diretamente.

### 6.3 Contratos do site antigo aposentados em 04/09/2026

Por autorização expressa, os read-models públicos provados como pertencentes à cadeia do site antigo foram aposentados. Não são contratos disponíveis nem candidatos automáticos do Site Novo:

- `public.frontend_boxes_v1`;
- `public.frontend_home_v1`;
- `public.frontend_busca_v1`;
- `public.frontend_ficha_v1`;
- `public.frontend_ficha_build_v1`;
- `public.frontend_ficha_builds_v1`, view auxiliar da mesma família necessária à remoção ordenada das duas views da Ficha.

O readback do catálogo confirmou ausência dos seis nomes depois das migrações `20260904210738 aposentar_views_site_antigo_20260904` e `20260904211109 aposentar_views_ficha_site_antigo_20260904`. Não foi usado `CASCADE`; tabelas, dados, funções/RPCs, schemas e roles foram preservados.

As definições, owners, opções, comentários e grants necessários à restauração deliberada foram capturados antes das remoções nos dois arquivos `RECUPERACAO-VIEWS-*.sql`. A prova completa está em `AUDITORIA-APOSENTADORIA-SITE-ANTIGO-2026-09-04.md`.

Permanecem no banco, sem autorização de remoção, a RPC `public.frontend_build_publicada_v2(...)` e os helpers `clube_novo.frontend_normalizar_texto_v1(text)` e `public.fn_pts_regua(...)`. A permanência deles não autoriza reutilização pelo Site Novo. Qualquer aposentadoria de função/RPC exige decisão separada.

## 7. Regra da `nota_final`

No checkpoint da Reforma A:

- `clube_novo.build_pontuacao_normalizada_v2` não existe mais;
- as 24 colunas `nota_*` foram colocadas em `clube_novo.build_linha_card`;
- `clube_novo.finalizar_publicar_linha_v1` grava o resultado automaticamente por linha quando os dois motores compatíveis existem;
- `nota_final` é a única nota que a tela exibe;
- a publicação grava `nota_final` uma vez;
- banco e tela não recalculam `nota_final` no caminho de leitura.

Fluxo obrigatório:

```text
build_linha_card.nota_final
    ↓ por contrato público versionado
adaptador valida publicação e tipo
    ↓
FichaViewModel.notaFinal
    ↓
renderizador apenas exibe
```

É proibido:

- somar componentes na tela;
- normalizar novamente;
- escolher outra coluna `nota_*` quando `nota_final` faltar;
- usar `nota_do_motor`, `nota_bruta_selada` ou `nota_bonus_total` como fallback;
- criar rótulo, percentual ou ranking por cálculo local.

Sem publicação válida ou sem `nota_final`, a tela entra em estado indisponível/bloqueado.

As outras 23 colunas `nota_*` são proveniência, componentes e selos do resultado. Elas não competem com `nota_final` pela exibição principal.

### 7.1 Como a nota é formada antes da leitura da Ficha

A nota bruta do Otimizador prova qual foi a melhor Build escolhida, mas não é a nota exibida pela Ficha.

Na formação dos atributos:

1. as barrinhas acrescentam evolução e param em 99;
2. a etapa de proficiência aplica piso 40 e teto 99;
3. depois entram o boost do técnico e os ímpetos, que podem levar o atributo acima de 99;
4. os efeitos de habilidades usados pelo motor também não recebem um corte final de 99.

A normalização usa os 26 atributos completos usados na conta do motor (`build_otimizador.atributos_internos`). O fallback físico histórico é `build_otimizador.atributos_finais`, somente quando `atributos_internos` está nulo. Os pesos e alvos vêm do retrato persistido do molde (`build_otimizador.arows_snapshot`).

Fórmula de publicação:

```text
nota_do_motor =
  100 * soma(peso * atributo_completo)
      / soma(peso * alvo_do_molde)

nota_final = nota_do_motor + nota_bonus_total
```

Essa normalização não usa arredondamento, piso, teto, constante K nem comparação com a população de cards. Só depois de o resultado final ser gravado a Ficha lê `build_linha_card.nota_final` e o formata com duas casas decimais.

### 7.2 Prova atual — Messi, linha 30015

- nota bruta do Otimizador: `466,8`;
- numerador: `10152`;
- denominador: `9184,5`;
- nota normalizada do motor: `110,5340519353258207`;
- bônus total: `2,0281`;
- nota final gravada: `112,5621519353258207`;
- valor exibido pela Ficha: `112,56`.

Contraprova: se a normalização usasse os 26 atributos reduzidos mostrados no jogo em vez dos 26 atributos completos usados na conta, a nota normalizada seria `104,9376667211062116`, a final seria `106,9657667211062116` e a tela mostraria `106,97`. Esse é exatamente o erro do site abolido e não pode voltar ao Site Novo.

### 7.3 Documentos históricos

Documentos V1 antigos que somam a nota bruta do Otimizador com o bônus, ou que descrevem contratos e views já abolidos, são evidência histórica. Eles não regem o Site Novo e não podem ser usados como fallback de leitura, fórmula ou arquitetura.

## 8. Degraus, listas e outros valores compostos

O checkpoint da Reforma A informa que:

- `frontend_degraus_da_linha_v1` lê a linha;
- três views foram recriadas para ler a linha;
- a lista pronta lê a linha;
- nomes e grants dessas superfícies foram preservados na reforma informada.

Para o Site Novo, degraus, listas, ordenações, pontuações, percentuais e rótulos chegam prontos pelo contrato público aprovado. O navegador não recompõe esses valores.

Os nomes exatos das três views não foram fornecidos no checkpoint. Este manual não os inventa.

## 9. Arquitetura obrigatória de escrita futura

O navegador nunca escreverá diretamente em tabelas.

Quando uma ação de escrita for autorizada, o fluxo deverá ser:

```text
ação do usuário
    ↓
controlador da página
    ↓
porta de escrita específica
    ↓
RPC/API específica, autorizada e validada
    ↓
persistência
    ↓
readback pelo contrato de leitura
    ↓
novo modelo de tela
```

Cada escrita futura precisa definir antes da implementação:

- usuário/proprietário do estado;
- autenticação e autorização;
- parâmetros e tipos;
- invariantes;
- concorrência e idempotência;
- resultado e códigos de erro;
- prova de persistência;
- readback.

Chaves privilegiadas e `service_role` nunca podem ser colocadas no navegador. Grants, RLS e o modo de segurança de views/RPCs devem ser auditados antes da exposição pública.

## 10. Checkpoint Reforma A — 04/09/2026

O registro integral está em `CHECKPOINT-REFORMA-A-2026-09-04.md`.

### 10.1 Migrações recebidas

1. `20260904201650 a_nota_vai_para_a_linha_parte_1_colunas`
2. `20260904201701 a_nota_vai_para_a_linha_parte_2_carga`
3. `20260904201858 a_nota_vai_para_a_linha_parte_3_views`
4. `20260904201950 a_nota_vai_para_a_linha_parte_3b_ficha_e_lista`
5. `20260904202722 a_nota_vai_para_a_linha_parte_4_degraus_e_drop`

### 10.2 Evidência recebida

Conferência anterior ao drop informada:

| Medição | Resultado recebido |
|---|---:|
| Linhas na tabela antiga | 55.757 |
| Linhas com nota em `build_linha_card` | 55.757 |
| Divergências | 0 |

Testes públicos informados sob teto de 3 segundos:

- lista, primeira página: 500 linhas;
- lista, última página: 430 linhas;
- lista de uma função: 500 linhas;
- Ficha de um card: 16 linhas;
- estado do card: publicada.

Topo informado: Neymar 114,19; Modrić 112,83; Messi 112,56.

Esses resultados são evidência recebida e datada. Não representam nova consulta ao vivo feita na criação deste manual.

## 11. Ordem operacional bloqueante

A ordem decidida pelo usuário é:

1. recuperar/subir os números das **2.721 builds** pendentes;
2. confirmar que o ranking voltou a **55.757**;
3. somente depois considerar a junção de `build_otimizador` e `build_bonificador` em `build_linha_card`.

Não propor como próxima ação, preparar ou executar a junção antes das etapas 1 e 2 e de nova autorização expressa.

## 12. Junção futura das tabelas

A Reforma A não juntou `build_otimizador` nem `build_bonificador` em `build_linha_card`.

O checkpoint informa relação 1:1, sem órfão, com 57.950 resultados do motor e 57.950 bônus ligados a 57.950 linhas. Isso é evidência de viabilidade dos dados, não autorização de execução.

As funções escritoras que entregam resultados ao fluxo são:

1. `otimizador_producao_concluir_linha_v6`
2. `otimizador_producao_importar_json_local_v1`
3. `otimizador_completar_vals_v1`
4. `otimizador_producao_concluir_linha_v3`
5. `otimizador_concluir_linha_teste_v1`
6. `otimizador_concluir_linha_teste_v2`
7. `bonificador_gravar_resultados_v1`
8. `gravar_build_bonificador_v3`
9. `gravar_build_bonificador_v4`
10. `clube_novo.finalizar_publicar_linha_v1`, chamada apenas pelos gatilhos e pelo retry durável.

Desde 2026-09-05, todas essas chegadas convergem na mesma finalizadora idempotente por linha. Não existe corte manual, publicação global nem atualização global de lista. O segundo resultado que chega fecha, sela e publica somente aquela linha na mesma transação.

## 13. Método obrigatório de trabalho

Toda página, integração ou mudança estrutural segue esta sequência:

```text
serviço
    ↓
código/módulo que executa ou consome
    ↓
manual específico correspondente
    ↓
contrato e estado atual do banco
```

Para cada item:

1. identificar o serviço realmente ativo e seu entrypoint;
2. localizar o código proprietário do comportamento;
3. ler integralmente o manual específico aplicável;
4. conferir o contrato, tipos, grants, filtros, ordenação e estados no checkpoint autorizado;
5. registrar diferenças entre documentação e realidade;
6. bloquear o uso se a cadeia não puder ser provada.

Não basta localizar uma tabela ou fazer troca de texto. A auditoria precisa cobrir chaves, tipos, nulabilidade, filtros, ordenação, transformações, estados, resultados e interface.

Banco em mudança não vira arquitetura. Durante alteração ativa:

- registrar o resultado como snapshot transitório;
- não congelar nomes ou payloads;
- aguardar o checkpoint estável;
- repetir o readback dirigido à página antes de conectar.

## 14. Estrutura física inicial da Ficha

A primeira implementação será deliberadamente simples. Os arquivos ainda não foram criados:

```text
Site Novo/
├─ MANUAL-DO-SITE-NOVO.md
├─ ARQUITETURA-E-INVENTARIO-INICIAL.md
├─ CHECKPOINT-REFORMA-A-2026-09-04.md
├─ PREVIA-FICHA.html
├─ PREVIA-FICHA.png
├─ ficha.html
├─ ficha.css
└─ ficha.js
```

### 14.1 Responsabilidade dos três arquivos

- `ficha.html`: contém a estrutura semântica e o desenho aprovado; não consulta o banco e não calcula regras.
- `ficha.css`: preserva o visual, a posição, a hierarquia e as relações congeladas entre os blocos.
- `ficha.js`: reúne inicialmente a chamada à RPC/API pública versionada, a validação mínima do contrato, a criação do modelo de tela e o preenchimento/renderização do HTML.

### 14.2 Organização interna do `ficha.js`

Mesmo em um arquivo único, as responsabilidades devem aparecer em blocos internos claros:

1. configuração da fronteira pública;
2. chamada de leitura;
3. validação mínima de versão, tipos e estado;
4. transformação para o modelo de tela;
5. renderização dos estados e dos quatro blocos;
6. tratamento de indisponibilidade e erro.

O arquivo não contém fórmula de nota, regra de ranking, query direta de tabela nem fallback de negócio.

### 14.3 Regra para separar módulos no futuro

Mensageria, validação, modelo e renderização só viram arquivos físicos diferentes quando pelo menos uma destas condições for comprovada:

- `ficha.js` ficou grande a ponto de dificultar leitura, teste ou manutenção;
- uma responsabilidade passou a ser reutilizada por outra página;
- testes ou segurança exigem isolamento explícito;
- o usuário aprovou a mudança de arquitetura.

Até lá, criar vários arquivos para essas responsabilidades é complexidade desnecessária.

## 15. Estados mínimos da Ficha

O modelo e o renderizador devem distinguir:

- `carregando`: contrato ainda não respondeu;
- `pronto`: resposta completa e validada;
- `vazio`: consulta válida sem registro aplicável;
- `bloqueado`: publicação/contrato obrigatório ausente ou incompatível;
- `erro`: falha técnica identificada.

Esses estados não podem ser convertidos uns nos outros por fallback. Em especial, `bloqueado` não pode mostrar nota calculada localmente.

## 16. Sequência inicial da página Ficha

1. Manter o layout oficial congelado.
2. Definir o corte funcional da primeira entrega: cadastral, build publicado ou editável.
3. Aguardar a recuperação das 2.721 builds e a confirmação do ranking em 55.757.
4. Registrar o checkpoint estável usado pela implementação.
5. Definir o DTO/modelo da Ficha a partir dos blocos visuais.
6. Definir e aprovar o contrato público versionado sem inventá-lo no frontend.
7. Implementar o adaptador e seus estados fail-closed.
8. Implementar renderização com fixtures antes da conexão real.
9. Conectar somente leitura e fazer readback bloco a bloco.
10. Especificar escritas separadamente, apenas se autorizadas.

## 17. Diário de decisões

### 04/09/2026

- O diretório oficial e exclusivo da reconstrução é `Site Novo`.
- A reconstrução será feita do zero funcionalmente.
- Lógica, funções, fórmulas, queries, contratos, regras e arquitetura do Encaixe antigo são proibidos como base.
- Somente o visual aprovado pode ser reaproveitado.
- A Ficha é a primeira página.
- `PREVIA-FICHA.html` e `PREVIA-FICHA.png` são o layout oficial e congelado da Ficha.
- Posição, hierarquia e relações entre os quatro blocos serão preservadas.
- O único banco operacional autorizado é `clube_novo`.
- O frontend usará contrato público versionado e adaptador; HTML e renderizador não conhecem tabelas.
- A primeira implementação física da Ficha terá somente `ficha.html`, `ficha.css` e `ficha.js`.
- Chamada pública, validação mínima, modelo e renderização ficarão conceitualmente separados dentro de `ficha.js`; novos módulos só surgirão por tamanho ou reutilização comprovados.
- Consulta direta de tabela foi rejeitada porque também exige JavaScript e acopla o frontend ao schema; uma RPC/API pública única reduz contrato exposto e pontos de quebra.
- `nota_final` é a única nota exibida e não será recalculada no caminho de leitura.
- Escritas futuras usarão portas e RPCs/APIs específicas; nunca tabela direta pelo navegador.
- A Reforma A moveu as 24 colunas `nota_*` para `build_linha_card` e removeu `build_pontuacao_normalizada_v2`, conforme checkpoint recebido.
- Primeiro serão recuperadas as 2.721 builds e reconfirmado o ranking em 55.757.
- A junção de `build_otimizador` e `build_bonificador` só poderá ser considerada depois e mediante nova autorização.
- Este manual é a autoridade viva e deve acompanhar toda decisão importante.
- O Bloco 1 posiciona estilo de jogo e posição nativa abaixo dos controles de pontuação, “Pode melhorar” e elenco, na mesma coluna imediatamente à direita da identidade; a terceira coluna permanece como respiro central até o painel de posições.
- As quatro colunas do Bloco 1 têm a mesma largura; a área útil geral da Ficha continua em `960px` e os banners não foram deslocados.
- O campinho e a lista de builds têm ligação bidirecional pelo código de posição recebido na resposta pública; não existe mapa fixo entre função e posição.
- O campinho preserva três estados permanentes vindos do card — indisponível apagada, permitida claramente acesa e nativa com moldura dourada sem brilho — e reserva a luminosidade máxima exclusivamente para a seleção momentânea do usuário.
- A Ficha abre sem posição nem build momentaneamente iluminada. Todas as builds usam a mesma cor-base; a build oficialmente publicada continua identificada semanticamente, mas não ganha cor roxa própria.
- Um segundo clique na mesma posição do campo limpa o filtro momentâneo; a build visualizada permanece selecionada porque continua sendo a autoridade dos dados e da pontuação da Ficha.
- O conjunto de estilo de jogo e posição nativa fica preso ao rodapé da quarta faixa da coluna 2 e termina alinhado ao nome do jogador na coluna 1.
- No Bloco 2, duplicações exclusivamente posicionais da mesma função e da mesma `nota_final` formam um único botão; posição indica onde aquela build pode ser usada e não cria outra cópia. As posições reais aparecem juntas e na ordem recebida, separadas por `/`.
- No zoom padrão de 100%, os botões agrupados do Bloco 2 têm `28px` de altura e tipografia interna ampliada, preservando integralmente a largura e as quatro colunas da grade.
- A grade do Bloco 2 exibe até 20 builds, em quatro colunas e no máximo cinco linhas; com menos itens, a altura acompanha somente as linhas existentes. Builds do sistema e builds salvas convivem nessa grade, mas as salvas usam uma cor-base azul própria.
- O nome de uma build salva preserva a função canônica usada como base e acrescenta um número sequencial estável. Números removidos não são reaproveitados: se existiram `1`, `2` e `3`, a remoção da `1` faz a próxima receber `4`.
- A implementação do Site Novo permanece independente do frontend aposentado: uma leitura, uma renderização, um estado de seleção e um manipulador por botão, sem chamadas concorrentes, encadeadas ou duplicadas herdadas.
- As views públicas do site antigo foram auditadas pelo código e aposentadas sem `CASCADE`; a dependência auxiliar `frontend_ficha_builds_v1` também saiu após prova repo-wide e de catálogo de que não tinha consumidor atual.
- As migrações de aposentadoria foram `20260904210738 aposentar_views_site_antigo_20260904` e `20260904211109 aposentar_views_ficha_site_antigo_20260904`.
- A recuperação anterior ao drop está nos dois arquivos `RECUPERACAO-VIEWS-*.sql`; o readback e o inventário das funções preservadas estão em `AUDITORIA-APOSENTADORIA-SITE-ANTIGO-2026-09-04.md`.

### 05/09/2026

- Em produção, uma atualização de resultados não pode criar uma janela pública sem builds entre a retirada de uma geração e a publicação da seguinte.
- A geração substituta deve ser preparada e validada fora da leitura pública. A ativação é uma troca atômica de versão; se a validação ou a troca falhar, a última geração comprovadamente válida continua ativa.
- A geração anterior só pode ser limpa depois do readback do contrato público confirmar a nova versão. Uma versão identificada como incorreta não permanece exposta: a operação deve reativar uma geração anterior comprovadamente válida ou entrar explicitamente em manutenção, sem apresentar dado errado como correto.
- O estado observado após a retirada da V9 e antes da V10 — card cadastral presente, mas pontuação, builds e atributos publicados ausentes — é aceitável somente como incidente de reconstrução e é proibido como fluxo normal de atualização em produção.
- Nos estados sem conteúdo completo, a estrutura dos quatro blocos permanece montada e com altura mínima estável; somente os valores internos entram em espera. O estado `pronto` continua com altura guiada pela quantidade real de conteúdo, inclusive a grade de builds.
- A moldura da foto no Bloco 1 acompanha a proporção física `240 × 340` (`12:17`) dos arquivos de card. A arte inteira, inclusive estrelas e rodapé, deve permanecer visível; a correção não reduz a largura da foto nem altera as quatro colunas iguais.
- A origem do clique passa a fazer parte do único estado de seleção: clique numa build ilumina somente aquele botão e acende no campo todas as posições vinculadas a ele; clique numa posição do campo continua iluminando todas as builds que contêm aquela posição. Trocar a origem substitui o realce anterior, sem acionar manipuladores adicionais.
- No cabeçalho do Bloco 2, “POSIÇÕES” significa quantas casas do campinho o card realmente pode ocupar, contando uma vez cada posição nativa ou permitida. Entradas posicionais das builds e posições apagadas não entram nesse total.
- A pontuação total pertence à build visualizada, não ao card isoladamente. Os dois placares da Ficha recebem sempre a mesma `nota_final` corrente por uma única função de apresentação.
- A rota `?card=<card_id>` sem `linha` abre a melhor build pública disponível do card; quando outra página já apresenta uma build, ela deve navegar com `?card=<card_id>&linha=<linha_id>` para preservar exatamente o contexto clicado.
- O clique numa build do Bloco 2 deixa de ser apenas um realce local: ele consulta em segundo plano a linha publicada correspondente pela própria porta da Ficha, atualiza em conjunto todos os dados dependentes da build e mantém o grupo escolhido destacado, sem recarregar nem remontar o card inteiro. Não existe segunda fonte de nota nem segunda porta de leitura.
- A URL recebe `card` e `linha` por `history.pushState` somente depois de a nova linha ser validada. Voltar/Avançar usa a mesma leitura em segundo plano; uma falha mantém a última ficha válida, não altera a URL comprovada e mostra erro explícito. Não existe retry nem fallback silencioso.
- O `500` observado numa troca real foi identificado no banco como `SQLSTATE 57014` (`statement timeout`) durante o startup de `site_novo_ficha_base_publicada_v1`. A migração `20260905223427` moveu os três `EXISTS` grandes de filas para um helper interno privado, preservando assinatura, versão, JSON e lógica pública; a proteção visual do cliente continua obrigatória para qualquer falha futura.
- Quando a edição de build for autorizada, a pontuação corrente produzida por esse fluxo alimentará a mesma função que atualiza os dois placares e o comparador “Pode melhorar”; esta decisão não autoriza cálculo local nem escrita nesta entrega.
- A seleção default da porta pública foi corrigida para ordenar primeiro pela maior `nota_final`; a migração do banco é `20260905215643 ficha_default_maior_nota_v2`, com artefato recuperável local e validação somente leitura próprios. A auditoria fechou 21.633 linhas, 1.087 cards e zero divergência entre default e nota máxima.
- Os Blocos 2 e 3 passam a compartilhar uma moldura e um fundo verde-petróleo próprios sob o nome `ÁREA DA BUILD`, enquanto os Blocos 1 e 4 continuam neutros e sem rótulos explicativos redundantes. Após a primeira conferência visual indicar contraste insuficiente, o fundo subiu um degrau de luminosidade e saturação, a borda ficou um pouco mais definida e os dois blocos internos passaram a usar exatamente a mesma superfície. A região não acrescenta compressão horizontal nem usa halo concorrente.
- A faixa superior do Bloco 2 tem quatro células iguais: `BUILD EM EXIBIÇÃO` mostra nome, posição e nota correntes; `MELHOR / BUILD RECOMENDADA` abre por consulta a maior nota já publicada; `MINHAS / BUILDS SALVAS` mostra o contador público; e `PERSONALIZAR / ESTA BUILD` prepara o início futuro de uma cópia editável.
- Somente a ação `MELHOR` funciona nesta entrega, reutilizando a troca interna e a mesma porta pública. `MINHAS` e `PERSONALIZAR` permanecem desativadas até contratos de usuário e escrita serem autorizados. O salvamento continua uma ação separada no Bloco 3, identificado como `SALVAR MINHA BUILD` e ainda indisponível.
- O nome dentro de `BUILD EM EXIBIÇÃO` usa caixa alta e a mesma superfície verde-clara da build selecionada na lista, sem o halo externo reservado à seleção momentânea. `MINHAS` e `PERSONALIZAR` usam a mesma família azul por pertencerem ao futuro espaço pessoal do usuário.
- `BUILD EM EXIBIÇÃO` é a única autoridade visual que informa qual build está aberta. O botão `MELHOR / BUILD RECOMENDADA` conserva texto fixo, não recebe o sufixo `EM EXIBIÇÃO` e permanece uma ação idempotente mesmo quando a melhor já está aberta.

## 18. Procedimento para atualizar este manual

Toda mudança importante deve seguir este procedimento na mesma entrega:

1. **Identificar a decisão:** registrar pedido, data, escopo e limite de autorização.
2. **Ler a cadeia afetada:** serviço, código, manual correspondente e contrato/banco.
3. **Classificar o estado do banco:** estável, checkpoint datado ou snapshot transitório.
4. **Atualizar a regra:** editar a seção autoritativa deste manual; não apenas acrescentar nota solta.
5. **Atualizar o diário:** inserir a decisão com a data real.
6. **Atualizar referências:** apontar checkpoint, migração, contrato e artefatos aplicáveis.
7. **Executar somente o autorizado:** não ampliar escopo por causa da documentação.
8. **Verificar o artefato:** testar sintaxe, estrutura e comportamento proporcionalmente ao risco.
9. **Fazer readback:** reler arquivo, banco ou tela resultante e comparar com a decisão.
10. **Registrar evidência:** anotar contagens, estados, resultados, data e limitações.
11. **Reportar arquivos:** listar exatamente o que foi criado ou alterado.

### 18.1 Conteúdo mínimo de uma entrada futura

```text
Data:
Decisão do usuário:
Escopo autorizado:
Arquitetura/contrato afetado:
Estado anterior:
Estado novo:
Arquivos alterados:
Evidência/teste:
Readback:
Pendências ou bloqueios:
```

### 18.2 Regra de conclusão

Não declarar uma mudança concluída apenas porque o código ou dado existe. A conclusão exige distinguir:

- existência do dado;
- composição final;
- publicação;
- exposição pública;
- renderização na tela;
- readback do artefato real.

Sem evidência suficiente, registrar o estado como pendente ou bloqueado, nunca como concluído por inferência.

## 19. Estado desta versão do manual

- manual e artefatos de recuperação mantidos somente dentro de `Site Novo`;
- a primeira Ficha funcional foi criada em `ficha.html`, `ficha.css` e `ficha.js`, preservando a geometria e a hierarquia da prévia congelada;
- seis views públicas do site antigo foram removidas por duas migrações explícitas, sem `CASCADE`;
- nenhuma função/RPC, tabela, dado, schema, role, grant ou política fora das views removidas foi alterado;
- nenhum arquivo fora de `Site Novo` foi alterado;
- o catálogo confirmou a ausência dos seis nomes aposentados e a permanência das tabelas e funções inventariadas;
- a porta pública de leitura da Ficha foi fechada como `public.site_novo_ficha_v1(text,bigint)`; as demais páginas continuam sem contrato definido até decisão própria.

## 20. Caderno vivo de pendências

`CADERNO-DE-PENDENCIAS.md` é o registro obrigatório de toda pendência importante descoberta durante o Site Novo. Cada item usa identificador estável, data de abertura, contexto, impacto, estado humano (`PENDENTE`, `EM ANDAMENTO`, `RESOLVIDA` ou `BLOQUEADA`), fonte/objeto a conferir, critério objetivo de conclusão e evidência de fechamento.

Previsão, mensagem ou expectativa nunca autorizam marcar um item como `RESOLVIDA`. O fechamento exige readback, artefato ou teste verificável. Sempre que uma pendência importante surgir ou for resolvida, o caderno deve ser atualizado na mesma entrega.

## 21. Cards de nível 1 sem evolução

A evidência física usada pelo Site Novo é a combinação `clube_novo.carta_jogo.level_cap=1` e `orcamento=0`, também registrada no manual do Otimizador como “orçamento zero, teto de nível 1”. Esse é um estado válido do jogo, não uma build incompleta.

Para esses cards:

- os atributos iniciais e após evolução são iguais;
- não existe acréscimo por evolução: as dez barras devem estar persistidas em zero;
- não aceitam habilidades adicionais: a lista deve estar vazia;
- habilidades e ímpetos nativos continuam sendo exibidos normalmente;
- alguns cards desse grupo têm ímpeto nativo e outros não; a ausência de ímpeto não é preenchida artificialmente;
- o técnico e os efeitos publicados continuam válidos;
- completude continua dependendo do vetor final publicado de 26 itens, nunca de barras positivas;
- a nota continua sendo lida de `build_linha_card.nota_final`.

A amostra de regressão é Kubo Takefusa, `card_id=105840610761736`: teto 1, orçamento 0, `cap_estimado=false`, linha publicada `5790`, vetor final com 26 itens e as dez barras em zero. O cliente não reaplica barra, técnico ou ímpeto.

Auditoria física somente leitura de 2026-09-04 sobre as linhas publicadas encontrou 49.287 linhas de 3.064 cards com `level_cap=1` e `orcamento=0`: zero linhas com qualquer barra diferente de zero, zero linhas com habilidade adicional e zero linhas sem técnico. A prova confirma a regra categórica; não foi necessária alteração na porta pública nem nos arquivos funcionais da Ficha.

## 22. Primeira Ficha funcional

### 22.1 Arquivos físicos

- `ficha.html`: estrutura semântica e ligações de todos os campos dentro da geometria congelada.
- `ficha.css`: desenho da prévia separado do conteúdo.
- `ficha.js`: uma chamada pública, validação de envelope e renderização.
- `CONTRATO-E-MAPEAMENTO-FICHA-V1.md`: origem, chave, cardinalidade, tipo, ausência e regra de escolha de cada campo.
- `MIGRACAO-SITE-NOVO-FICHA-V1.sql`: definição recuperável da porta pública.
- `20260905185410_MIGRACAO-FICHA-MAIOR-NOTA-V2.sql`: alteração recuperável que torna a maior `nota_final` a primeira autoridade do default.
- `20260905185410_VALIDAR-FICHA-MAIOR-NOTA-V2.sql`: contraprova somente leitura do default, das linhas explícitas, dos grants e do tempo público.
- `CADERNO-DE-PENDENCIAS.md`: pendências vivas com fechamento por evidência.

### 22.2 Porta pública

`public.site_novo_ficha_v1(p_card_id text default null, p_linha_id bigint default null)` retorna um único objeto JSON. O navegador chama somente `/rest/v1/rpc/site_novo_ficha_v1`; não consulta tabela ou view.

A função:

- é somente leitura e `STABLE`;
- usa `SECURITY DEFINER` e `search_path` vazio;
- revoga execução de `PUBLIC`;
- concede execução somente a `anon`, `authenticated` e `service_role`;
- usa consultas estáticas totalmente qualificadas;
- não retorna atributos internos, pesos, fórmulas ou fingerprints;
- não recalcula nota, pontos por atributo, barra, técnico ou ímpeto;
- entrega na mesma resposta a pontuação corrente e a lista das builds prontas, que alimentam o único comparador visual de “Pode melhorar”;
- prioriza linha publicada com vetor final de 26 itens e depois aplica a ordem determinística de nota, publicação e ID.

O assessor de segurança do Supabase registra avisos por a função ser executável por `anon` e `authenticated` com `SECURITY DEFINER`. Nesta porta esses avisos são esperados e intencionais: a finalidade é justamente expor somente o DTO permitido sem liberar as tabelas. Não apareceu aviso de desempenho ligado à função.

### 22.3 Estados de interface

- `pronto`: linha publicada e 26 valores finais.
- `atributos_em_atualizacao`: vetor ausente e registro vivo do card em lote não finalizado.
- `atributos_aguardando_publicacao`: vetor ausente sem evidência viva de fila.
- `card_sem_build_publicada`: card existe sem linha publicada.
- `linha_nao_encontrada_ou_nao_publicada`: linha explícita inválida para aquele card.
- `card_nao_encontrado` e `parametro_ausente`: entrada inválida sem fallback.

As ações de escrita continuam visíveis na posição aprovada, porém desabilitadas e identificadas como indisponíveis.

### 22.4 Readback e regressão

Testes feitos com a função sob a role `anon` e também no navegador com a chave pública:

- Messi `89136409091415`: `pronto`, linha `30015`, nota `112.5621519353258207`, 26 valores finais renderizados.
- Dani Olmo `106787651039542`: `atributos_aguardando_publicacao`, linha `2778`, nota `109.8240729776247849`, 26 nomes e zero valores finais; nenhum fallback.
- Kubo Takefusa `105840610761736`: `pronto`, linha `5790`, nível 1 sem evolução, dez barras zero, zero habilidades adicionais e 26 valores finais.
- card inexistente: `card_nao_encontrado`.
- parâmetro ausente: `parametro_ausente`.
- `anon` e `authenticated` têm execução; `PUBLIC` não tem.
- as seis views aposentadas continuam ausentes do catálogo.

O JavaScript passou em `node --check` e o navegador mostrou somente uma chamada `fetch`, dirigida à porta pública da Ficha.

### 22.5 Parâmetros de navegação

Os nomes canônicos dos parâmetros da Ficha são:

- `?card=<card_id>`;
- `?linha=<linha_id>`, opcional.

Os nomes longos `?card_id=` e `?linha_id=` continuam aceitos como aliases de compatibilidade. Se a forma curta e a longa aparecerem juntas, a forma curta tem precedência. O endereço sem `card` continua fazendo uma única consulta pública e recebe o estado `parametro_ausente`.

Quando `linha` não é informada, a porta escolhe a build pública padrão do card; para a navegação do Site Novo, essa escolha representa a melhor build pública disponível. Quando `linha` é informada, não existe substituição silenciosa: somente a linha pedida pode alimentar a Ficha. Ranking, listas e qualquer outra página que já esteja mostrando uma build devem transportar seu `linha_id`; links genéricos que conhecem apenas o card usam somente `card`.

A primeira abertura monta a Ficha a partir de uma única resposta. Depois dela, a troca de build faz uma única nova requisição à mesma porta em segundo plano e atualiza apenas o estado dependente da build: os dois placares e comparadores, função/posição selecionada, builds, distribuição, técnico, habilidades adicionadas, ímpetos, atributos, bônus, pé e medidas corporais. Identidade, foto, nome, dados cadastrais, habilidades nativas/especiais, estilos de IA e chassi permanecem montados. A URL só avança após o sucesso; em erro, o conteúdo e o endereço válidos permanecem e a falha é apresentada sem retry ou reaproveitamento silencioso de dados.

No Bloco 3, cada Ímpeto é identificado pelo próprio nome, bônus e cor visual. As etiquetas redundantes “Ímpeto 1” e “Ímpeto 2” não são exibidas; o slot e o tipo permanecem disponíveis semanticamente para acessibilidade, e o cadeado continua marcando visualmente o Ímpeto fixo. As duas caixas ocupam colunas de mesma largura e se estendem à mesma altura, independentemente da quantidade de efeitos de cada Ímpeto.

A fileira de ações “Copiar do máximo”, “Limpar tudo” e “Salvar minha build” é o rodapé da coluna direita do Bloco 3 e permanece alinhada ao final dessa caixa, ainda que habilidades e Ímpetos ocupem alturas diferentes.

Em 05/09/2026, a migração registrada no banco como `20260905215643 ficha_default_maior_nota_v2` tornou `nota_final DESC NULLS LAST` o primeiro critério da seleção default; completude dos 26 atributos, data de publicação e ID passaram a ser somente desempates. A auditoria de 21.633 linhas em 1.087 cards encontrou zero divergência entre o default e `MAX(nota_final)`. A linha explícita permaneceu soberana, sem mudança de assinatura, wrapper ou JSON. Os artefatos recuperáveis locais são `20260905185410_MIGRACAO-FICHA-MAIOR-NOTA-V2.sql` e `20260905185410_VALIDAR-FICHA-MAIOR-NOTA-V2.sql`.

O teste local do próprio `ficha.js` confirmou os corpos enviados por `?card=` para Messi, Dani e Kubo, corpo com card nulo na ausência, bloqueio de `?linha=abc` antes da requisição, suporte aos dois aliases longos e precedência dos nomes curtos. As mesmas cargas válidas foram confirmadas pela requisição pública: Messi e Kubo `pronto`, Dani aguardando publicação e ausência como `parametro_ausente`.

### 22.6 Regra única do “Pode melhorar”

O usuário corrigiu expressamente uma separação indevida entre build pronta e build em construção. O indicador tem uma única regra em qualquer estado da Ficha:

1. ler a pontuação total que estiver aparecendo naquele momento;
2. localizar, entre as builds prontas do mesmo card, a maior pontuação da mesma função;
3. mostrar quanto falta para a pontuação corrente alcançar essa referência.

O cálculo comprovado na versão correta do arquivo anterior é:

```text
(melhor nota pronta da função - nota corrente) / nota corrente × 100
```

Se a nota corrente já alcança ou supera a referência, o resultado é `0%`. Quando a diferença não passa de `0,05%`, a tela também mostra `0%`. Acima disso, mostra uma casa decimal precedida de `+`.

Exemplo confirmado: Messi como Atacante criador tem builds prontas de `112,56`. Enquanto a pontuação total corrente é `112,56`, o indicador mostra `0%`. Se uma alteração nas barras reduzir a pontuação corrente, o mesmo comparador passa a mostrar a distância positiva até `112,56`. Não se cria outro cálculo para o modo de edição.

Havia duas implementações no material aposentado. A mais antiga lia `_notaMot` e podia ficar presa em `0%`; a correção posterior usa a referência do Otimizador. Esses nomes e esse código não são arquitetura do Site Novo: servem apenas para distinguir a prova correta da versão defeituosa. No Site Novo, a referência vem de `builds_publicadas[]`, já entregue pela porta pública, e o comparador reutilizável fica no módulo da Ficha.

Os dois elementos de pontuação total (`score-top` no Bloco 1 e `score-main` no Bloco 3) e os dois elementos de “Pode melhorar” são atualizados juntos por uma única função. A entrada dessa função é a build corrente: hoje, a linha publicada selecionada pela porta; futuramente, a build em edição quando esse fluxo for autorizado. O cliente formata e compara valores publicados, mas não recompõe `nota_final`.

Readback de 04/09/2026:

- a captura aprovada foi preservada em `REFERENCIA-BLOCO-1-APROVADA-2026-09-04.png`, SHA-256 `C5E7C471F7521536FA11BEBF65980A67440CA2C795195E0C0ED2EE1599953AC2`;
- `ficha.css` mantém `.native` em `grid-column: 2` e `grid-row: 4`, abaixo de pontuação, “Pode melhorar” e elenco, e divide o Bloco 1 em quatro colunas iguais com `repeat(4, minmax(0,1fr))`; a terceira coluna continua livre e a largura útil geral permanece em `960px`;
- o contrato público entrega todas as builds prontas com função e nota; não entrega um percentual fixo;
- chamada HTTP pública do Messi `89136409091415` retornou `pronto`, linha `30015`, função `Atacante criador`, posição `PTD`, nota corrente `112.5621519353258207` e duas referências prontas de Atacante criador com a mesma nota;
- o JavaScript passou em `node --check`; o comparador encontra a maior nota da mesma função e retorna `0%` para o caso acima;
- os grants permaneceram fechados para `PUBLIC` e abertos intencionalmente para `anon`, `authenticated` e `service_role`;
- os assessores não apontaram aviso de desempenho para a função; os dois avisos de segurança são os já documentados para uma porta pública `SECURITY DEFINER` executável pelas roles públicas autorizadas.

### 22.7 Campinho e builds por posição

A ligação entre o campo de posições do Bloco 1 e as builds do Bloco 2 é bidirecional e usa somente os códigos reais recebidos na mesma chamada pública:

- ao clicar numa posição, a Ficha destaca essa casa do campo e todas as builds renderizadas cujo próprio `posicao.codigo` seja igual;
- ao clicar numa build, a Ficha consulta a linha publicada correspondente em segundo plano, atualiza pontuação e todos os detalhes dependentes da build e destaca somente o botão escolhido no Bloco 2; no campo, acende todas as posições escritas naquele grupo, sem recarregar a página;
- ao trocar de uma seleção iniciada pelo campo para uma build, a linha compatível com a posição filtrada tem precedência dentro do grupo; sem filtro do campo, vale a linha já selecionada naquele grupo ou a primeira linha na ordem pública;
- clicar novamente na build visualizada mantém essa build como autoridade da Ficha; somente o segundo clique na mesma posição do campo limpa o filtro momentâneo iniciado pelo campo;
- nomes de função não determinam posição no cliente; cada build usa exclusivamente o objeto `posicao` publicado para ela;
- todas as builds usam a mesma cor-base, inclusive a build oficialmente selecionada; seu `aria-current` continua registrando a semântica de publicação, sem criar uma quarta cor visual;
- o realce iniciado pelo campo usa preenchimento verde-claro, texto escuro, moldura clara e halo forte em todas as builds correspondentes; quando iniciado por uma build, esse mesmo acabamento se restringe ao botão clicado. O campo apenas filtra visualmente; a build carrega a linha exata pela mesma porta e registra a rota sem refresh. Nenhum caminho recalcula ou publica a nota;
- a abertura genérica com somente `card` não aplica realce momentâneo e mostra a build padrão de maior pontuação; a abertura explícita com `linha` destaca o grupo da linha pedida, inclusive quando veio de outra página.

O campinho tem três estados permanentes, derivados de fontes físicas distintas do `clube_novo`:

1. **Nativa:** `carta_posicao_principal_jogo`, publicada como `card.posicoes[].principal=true`; mantém uma moldura dourada própria, sem halo ou brilho permanente, inclusive quando outra posição é selecionada.
2. **Secundária/permitida:** `carta_posicao_jogo.nivel_aptidao > 0`, publicada como `card.posicoes[].nivel > 0`; aparece claramente mais acesa que a indisponível, mas sem disputar luminosidade com a seleção momentânea.
3. **Indisponível:** `nivel_aptidao = 0` ou ausência física representada por `null`; aparece apagada. Para goleiros, GO pode ter `nivel=null` e continuar nativa porque `principal=true` tem precedência.

O clique acrescenta uma quarta camada momentânea de seleção, deliberadamente a mais luminosa do campo: preenchimento verde-claro, texto escuro, contorno claro e halo forte. Ela não altera `principal`, `nivel`, a borda permanente da nativa nem a aptidão do card.

Readback somente leitura de 04/09/2026:

- no banco, Messi `89136409091415` tem PTD como principal; PTE `1`, CA `2`, SA `2`, MAT `2` e MLD `1` como permitidas; níveis `0` e GO `null` como indisponíveis;
- a porta `site_novo_ficha_v1` devolveu os mesmos campos `codigo`, `nivel`, `principal` e `selecionada`, portanto não exigiu migração nem mudança no banco vivo;
- entre as builds agrupadas e renderizadas do Messi, CA correspondeu a `Centroavante móvel`, `Falso nove` e `Centroavante fixo`; MLD correspondeu a `Ala finalizador` e `Ala cruzador`;
- clicar no botão agrupado `Atacante infiltrador · MAT/SA` seleciona a build e acende MAT e SA no campo; o comportamento antigo de limpar a build no segundo clique foi substituído pela seleção navegável em 05/09/2026;
- em Juan Carlos `100012`, a porta devolveu GO com `principal=true` e `nivel=null`, comprovando a precedência da nativa para goleiros;
- o teste do próprio `ficha.js` confirmou abertura sem seleção luminosa, clique em CA iluminando exatamente `Centroavante móvel` e `Falso nove`, clique na build MAT selecionando MAT no campo e permanência da moldura nativa sem brilho concorrente;
- o mesmo teste confirmou que o segundo clique em CA remove a seleção do campo, apaga os destaques das builds e restaura `aria-pressed=false`;
- o readback do CSS confirmou a remoção do estado roxo `.build.active`, a base visual única das builds, a moldura nativa sem halo externo e o preenchimento luminoso compartilhado por posição selecionada e builds correspondentes;
- o readback do CSS confirmou `.native` com `justify-content:flex-end` e margem interna inferior de `7px`, alinhando o fim de `PTD Ponta direita` ao fim de `Lionel Messi` sem alterar as quatro colunas iguais;
- nenhuma tabela, função, grant, política ou payload público foi alterado.

Readback local de 05/09/2026:

- em Andriy Shevchenko `88045755964138`, clicar em `Centroavante móvel · CA/SA` deixou exatamente uma build com `position-match` e `aria-pressed=true`, enquanto CA e SA ficaram selecionadas no campo;
- em seguida, clicar em CA no campo substituiu a seleção individual e destacou as três builds que contêm CA: `Centroavante móvel`, `Centroavante fixo` e `Falso nove`;
- o comportamento anterior de um segundo clique limpar `Centroavante móvel` foi substituído em 05/09/2026: a build visualizada permanece selecionada e somente o filtro iniciado no campo continua alternável;
- o teste foi executado na página real com a resposta pública vigente; `ficha.js` continuou com uma única chamada `fetch`, um estado de seleção e um manipulador por botão.

### 22.8 Agrupamento visual das builds no Bloco 2

A porta pública atual entrega entradas posicionais, mas o Bloco 2 não repete a mesma build quando função e pontuação são idênticas e somente a posição varia. O agrupamento é somente de apresentação e obedece às seguintes regras:

- a identidade do grupo é `funcao.id + nota_final` exata; posição e `linha_id` não criam outro botão;
- as posições únicas de todas as linhas do grupo aparecem dentro do mesmo botão, na ordem publicada e separadas por `/`;
- resultados da mesma função com `nota_final` realmente diferente permanecem em botões separados; o cliente não escolhe uma nota, não funde resultados diferentes e não confunde igualdade apenas visual após arredondamento com igualdade real;
- a build oficialmente selecionada preserva `aria-current=true` no botão agrupado quando qualquer linha do grupo for a selecionada;
- clicar no botão agrupado abre uma de suas linhas publicadas e destaca somente esse botão e todas as suas posições no campo; clicar em uma posição do campo apenas destaca todos os botões que contenham aquele código;
- a linha do botão agrupado é escolhida de forma determinística: a posição filtrada no campo, se compatível; senão, a linha já selecionada no grupo; por fim, a primeira linha na ordem pública. Uma entrada externa com `linha` nunca usa essa escolha de grupo e abre exatamente o ID recebido;
- o segundo clique na mesma build mantém a seleção da build; o segundo clique na mesma posição que iniciou um filtro no campo limpa somente esse filtro;
- o cabeçalho mostra separadamente a quantidade de builds agrupadas e a quantidade de posições que o card pode ocupar no campinho; posição nativa ou permitida conta uma vez e posição indisponível não conta;
- `builds_publicadas_total` representa a quantidade de entradas posicionais publicadas das builds e não é usado como contador de posições do jogador;
- a leitura e a área de clique foram ampliadas no zoom padrão de 100%: cada botão tem `28px` de altura, o nome e a pontuação usam `10.5px` e o código de posição usa `7.5px`; a largura não mudou e a grade continua com quatro colunas iguais.
- a grade renderiza até 20 botões (`4 × 5`) e cria somente as linhas exigidas pelos itens existentes; o limite anterior de 12 foi removido.
- a classe visual `.build.saved` reserva às builds salvas uma base azul distinta da base verde das canônicas; a seleção momentânea luminosa continua tendo precedência sobre ambas.

Readback somente leitura de 04/09/2026:

- o Messi `89136409091415` recebeu 16 entradas posicionais pela porta pública e formou 10 botões visuais, pois suas repetições de função têm a mesma pontuação e diferem somente pela posição;
- `Atacante criador` agrupou PTD e PTE no botão `Atacante criador · PTD/PTE · 112,56`;
- `Atacante finalizador` agrupou PTE e PTD; `Atacante infiltrador` agrupou MAT e SA; `Centroavante móvel` agrupou SA e CA; `Meia ofensivo` agrupou MAT e SA; `Falso nove` agrupou CA e SA;
- `Ala finalizador`, `Ala cruzador`, `Meia de arranque` e `Centroavante fixo` permaneceram com uma posição cada;
- a regressão com Dani Olmo confirmou que resultados da mesma função com pontuações diferentes continuam separados e não colocam a Ficha em erro;
- o teste confirmou que cada botão possui um único manipulador e que o módulo continua fazendo uma única chamada à porta pública, sem importar ou acionar código do frontend aposentado;
- o readback do CSS confirmou `height: 28px` e a tipografia ampliada, mantendo `grid-template-columns: repeat(4,minmax(0,1fr))` e, portanto, sem crescimento horizontal;
- o código limita a faixa a 20 botões e não fixa altura ou cinco linhas vazias; sem 20 itens, o Bloco 2 encolhe com a grade;
- a porta pública V1 ainda publica somente `builds_salvas_total=0` e não entrega a lista, a função-base nem o contador das builds do usuário; a renderização real das salvas permanece pendente até contrato de usuário e escrita próprios, sem dado simulado;
- nenhuma mudança foi feita no banco, na RPC pública, na nota ou na ordem recebida.
- a regressão de 05/09/2026 com `Centroavante móvel · CA/SA` comprovou que `Falso nove · CA/SA` não acende junto no clique da build, embora ambas continuem acendendo quando o clique parte de CA no campo; a seleção navegável posterior preserva essa distinção ao reabrir a linha exata.
- a leitura pública de Weston McKennie `55068997045101` devolveu 28 entradas posicionais de builds, mas o campinho comprovou 12 posições ocupáveis; o cabeçalho passa a mostrar `12 POSIÇÕES`;
- a mesma regra foi conferida em Andriy Shevchenko `88045755964138` (`12` entradas posicionais e `4` posições ocupáveis) e Alisson Santos `105870138684343` (`6` entradas posicionais e `3` posições ocupáveis);
- `ficha.js` usa a mesma lista de casas e a mesma classificação `primary`/`allowed`/`absent` para desenhar e contar o campinho, mantendo uma única chamada pública e sem mudança no banco ou no contrato.
- a regressão de navegação com Weston McKennie confirmou que `card` sozinho abre a linha `8477`, Lateral ofensivo LD, `101,90`, enquanto `linha=8475` abre exatamente Lateral defensivo LD, `95,03`, e `linha=8474` abre Lateral defensivo LE com a mesma nota; todas as leituras voltaram `pronto` com 26 atributos;
- o clique simulado sobre o botão agrupado Lateral defensivo canonicalizou a URL como `?card=55068997045101&linha=8475` sem `location.assign`; a troca interna mostrou `95,03` nos dois placares, manteve exatamente um botão realçado, acendeu LD/LE e preservou o mesmo nó da foto;
- uma segunda troca interna para Volante de construção confirmou que os dados do pé foram substituídos sem duplicação; Voltar para a rota genérica restaurou `101,90` sem remontar a identidade e sem realce artificial;
- uma resposta `500` forçada durante outra troca manteve nota, URL e conteúdo anteriores e exibiu a mensagem explícita de preservação; não houve retry nem fallback silencioso;
- `node --check` passou e o readback estrutural confirmou uma única expressão `fetch`, uma única função de pontuação corrente, um manipulador de `popstate`, zero `location.assign`, zero intervalos, zero observadores e zero escrita no banco.

### 22.9 Continuidade da publicação em produção

A leitura pública da Ficha não pode observar uma troca de geração como duas operações separadas de “apagar a atual” e “publicar a nova”. O protocolo obrigatório é:

1. gravar a nova geração sem torná-la pública;
2. validar integralmente contagem, selos, `nota_final`, vetor final de 26 atributos, funções, posições e relações exigidas;
3. ativar a geração completa numa única transação ou por um único ponteiro/versionador atômico;
4. fazer readback pelo mesmo contrato público consumido pelo navegador;
5. somente após o readback, retirar a geração substituída.

Se qualquer etapa anterior ao readback falhar, a ativação não acontece. A recuperação aponta para a última geração comprovadamente válida; nunca para uma versão apenas existente. Se nenhuma geração válida puder ser servida, a Ficha continua fail-closed e mostra manutenção explícita, sem calcular, inventar ou reutilizar números não comprovados.

Readback transitório de 05/09/2026:

- após a retirada deliberada da publicação V9 incorreta e antes de a V10 repopular os resultados, `site_novo_ficha_v1` devolveu para Messi `89136409091415` o estado `card_sem_build_publicada`;
- a tela preservou os dados cadastrais permitidos, mas mostrou `FICHA INDISPONÍVEL`, zero builds e pontuação/atributos ausentes;
- esse readback comprova o fail-closed do cliente, mas também comprova a janela vazia que o protocolo atômico deve impedir antes de produção;
- nenhuma alteração de banco foi autorizada ou executada nesta decisão; a implementação e a prova do mecanismo atômico permanecem na pendência `SITE-NOVO-PEND-004`.

### 22.10 Chassi estável nos estados sem dados completos

A ausência transitória de publicação, uma falha de consulta ou outro estado incompleto não pode recolher a Ficha nem mudar a posição relativa dos quatro blocos. Estrutura e conteúdo têm responsabilidades separadas:

- o HTML mantém os quatro blocos montados desde o carregamento;
- o renderizador aplica uma única classe de estado estrutural quando o envelope não está `pronto`;
- o CSS reserva a altura mínima das regiões do Bloco 2, do Bloco 3 e do Bloco 4 que normalmente dependem de listas publicadas;
- pontuação, builds, distribuição, atributos e demais valores ausentes continuam vazios ou indisponíveis, sem fixture, cálculo ou dado reaproveitado;
- quando o estado é `pronto`, a classe estrutural sai e o conteúdo volta a determinar naturalmente a altura, preservando a regra da grade de builds de crescer apenas conforme a quantidade real até o limite aprovado.

Readback local de 05/09/2026:

- `ficha.html` inicia com os quatro blocos montados e com `layout-incomplete`, evitando o recolhimento durante a única consulta pública;
- `ficha.js` remove essa classe somente para `pronto` e a mantém para entrada inválida, ausência de publicação, atributos incompletos e falha técnica, sem criar nova chamada, observador ou manipulador;
- `ficha.css` reserva apenas alturas mínimas no estado incompleto; não altera as quatro colunas do Bloco 1 nem fixa a altura do estado publicado;
- a mitigação visual não resolve nem encerra a troca atômica de geração registrada em `SITE-NOVO-PEND-004`.

### 22.11 Proporção integral da foto do card

Os arquivos reais de Alisson Santos `105870138684343`, Lionel Messi `89136409091415` e John Stones `56167703296681` foram inspecionados e medem `240 × 340`. A moldura anterior usava `3:4`, proporção mais baixa que a imagem, e cortava visualmente a faixa inferior onde ficam as estrelas.

A regra do Bloco 1 é:

- `.photo` usa `aspect-ratio: 12 / 17`, a mesma proporção do arquivo físico;
- a moldura não encolhe dentro da coluna de identidade (`flex: none`);
- a imagem continua com `object-fit: contain`, sem corte, ampliação artificial ou manipulação do arquivo;
- naquela correção, a largura da foto, a largura útil da página e as quatro colunas iguais permaneceram inalteradas. A autorização posterior de compactação, em 06/09/2026, limita a foto a 160px conforme a seção abaixo.

Readback local de 05/09/2026: `ficha.css` confirmou a proporção `12 / 17`, `flex: none` e `object-fit: contain`. A correção foi exclusivamente de CSS; HTML, JavaScript, chamada pública e banco não foram alterados.

### 22.12 Troca de build sem recarregar a Ficha

Uma build altera muitos valores, mas não altera a identidade física do card nem exige fechar e reabrir a página. A implementação mantém uma única autoridade assíncrona dentro de `ficha.js`:

- a abertura inicial continua consultando uma vez e montando os quatro blocos;
- cada escolha de uma linha diferente consulta uma vez a mesma `site_novo_ficha_v1` em segundo plano;
- um clique novo cancela a leitura anterior ainda em voo; a versão monotônica da requisição também impede que uma resposta antiga substitua a escolha mais recente, sem criar manipuladores concorrentes;
- após validar card e linha exatos, o renderizador troca em conjunto somente os campos dependentes da build;
- `history.pushState` grava a linha somente após sucesso; `popstate` atende Voltar/Avançar pela mesma leitura interna;
- falha técnica ou linha divergente não chama o renderizador de falha inicial, não apaga o card atual e não muda a URL válida: mostra erro explícito e mantém a build anterior;
- não há retry automático, segunda porta, cache de número como fallback nem aumento do timeout público.

Readback local de 05/09/2026 com Weston McKennie `55068997045101`: a troca de Lateral ofensivo para Lateral defensivo consultou a linha `8475`, atualizou ambos os placares para `95,03`, destacou um botão e `LE/LD`, preservou o mesmo nó da foto e realizou zero navegações completas. Uma nova troca não duplicou o chip de bônus do pé. Uma resposta `500` controlada preservou a ficha e a URL válidas; Voltar para `?card=55068997045101` recuperou `101,90` internamente. O teste contou uma expressão `fetch` e um único manipulador de `popstate`.

O `500` real capturado pelo usuário ao abrir a linha `8477` era uma falha de origem separada. Os logs localizaram `SQLSTATE 57014` (`statement timeout`) no startup de `site_novo_ficha_base_publicada_v1` às `2026-09-05 22:22:25Z`. A migração `20260905223427` retirou do startup os três `EXISTS` grandes das filas e os concentrou num helper interno privado, com comparação de 50 cards e zero divergência; wrapper, assinatura, versão e JSON públicos permaneceram iguais.

Readback pós-migração informado pelo responsável do banco, com o Bonificador rodando: 6/6 chamadas sequenciais HTTP 200, máximo 511 ms; 3/3 simultâneas no mesmo segundo do cron HTTP 200, máximo 1,312 s; cron em 213 ms e apenas 200 nos logs posteriores. O readback independente desta frente repetiu a linha `8477` seis vezes: 6/6 HTTP 200, `pronto`, linha correta, entre 118 e 290 ms. A pendência `SITE-NOVO-PEND-009` foi encerrada pela correção de origem, não pela mitigação do navegador.

### 22.13 Área da Build e hierarquia dos quatro controles

O usuário distinguiu duas naturezas dentro da Ficha: Blocos 1 e 4 são leitura do card e não oferecem edição; Blocos 2 e 3 tratam da build e formarão o espaço de consulta, personalização e salvamento. Essa diferença é apresentada sem renomear o conteúdo evidente dos blocos passivos e sem redesenhar a grade aprovada.

A implementação aprovada usa uma única moldura ao redor dos Blocos 2 e 3, com o cabeçalho `ÁREA DA BUILD` e o estado `VISUALIZANDO RECOMENDAÇÃO`. Seu fundo verde-petróleo é claramente diferente dos fundos neutros dos Blocos 1 e 4, mas não possui halo. Depois de o usuário considerar a primeira versão próxima demais do restante da página, o gradiente passou de `#18342a` a `#10231c`, o contorno ganhou opacidade moderada e o cabeçalho recebeu uma faixa translúcida fina. Os dois blocos internos compartilham a mesma sobreposição, reforçando que pertencem à mesma área. A região continua sem `padding` horizontal, portanto não estreita os painéis, a grade de quatro colunas nem os botões de builds.

Na faixa superior do Bloco 2:

- `BUILD EM EXIBIÇÃO` é o único indicador da build aberta e expõe o nome da função em caixa alta e, abaixo, posição e nota da linha corrente; sua superfície repete o verde-claro da build selecionada na lista, mas sem o halo externo da seleção momentânea;
- `MELHOR` é o termo dominante de `BUILD RECOMENDADA`; seu texto nunca muda para informar a build corrente. Um único `onclick` reutiliza `selectPublishedBuild`, a consulta assíncrona e a validação existentes; quando a mesma linha já está aberta, o caminho termina localmente sem nova consulta;
- `MINHAS` é o termo dominante de `BUILDS SALVAS · N`; nesta versão `N` vem de `builds_salvas_total`, permanece `0` e o controle fica desativado porque não há contrato autenticado nem lista publicada;
- `PERSONALIZAR` é o termo dominante de `ESTA BUILD`; usa a mesma família azul de `MINHAS`, pois ambos pertencem ao futuro espaço pessoal, e fica desativado até existir o fluxo autorizado que copie uma recomendação para um rascunho editável;
- `SALVAR MINHA BUILD` continua separado no Bloco 3 e permanece indisponível. Personalizar e salvar não são sinônimos: o primeiro deverá iniciar/alterar um rascunho, e o segundo deverá persistir esse rascunho quando houver contrato.

Readback local de 05/09/2026 com Weston McKennie `55068997045101`: a abertura default mostrou `LATERAL OFENSIVO · LD · 101,90`, manteve `BUILD RECOMENDADA` como texto fixo e deixou `MINHAS` e `PERSONALIZAR` desativados na mesma família azul. Um clique em `MELHOR` com a própria linha `8477` aberta terminou localmente sem nova consulta. Depois de abrir `LATERAL DEFENSIVO · 95,03`, a mesma ação retornou internamente a `LATERAL OFENSIVO · 101,90`, com um único manipulador, rota validada em `linha=8477` e nenhuma navegação completa. `node --check` passou; nenhuma escrita, porta nova, retry ou fallback foi introduzido.

Readback de contraste de 05/09/2026: `.build-workspace` usa o gradiente sólido moderado `#18342a → #142b22 → #10231c`, contorno `rgba(103,201,163,.43)` e marca lateral interna de `4px`. `.b2` e `.b3` recebem a mesma sobreposição `rgba(255,255,255,.025)`. Não foi adicionado halo externo, margem ou preenchimento horizontal. A confirmação visual final permanece com o usuário no navegador a 100%.

Em 05/09/2026, o primeiro experimento isolado do Bloco 3 — acrescentar um selo ao estado e recuar visualmente os controles indisponíveis — foi rejeitado pelo usuário porque a mudança não ficou clara e fez o conteúdo adicionado parecer ausente. O experimento foi removido integralmente: `ficha.html`, `ficha.css` e `ficha.js` voltaram exatamente aos hashes anteriores. O smoke público posterior abriu Alisson Santos `105870138684343`, linha `378966`, e renderizou novamente as cinco habilidades adicionadas publicadas. Portanto, esse experimento não integra o desenho vigente e nenhum segundo ajuste do Bloco 3 foi iniciado.

### 22.14 Geometria estável das caixas da Ficha

A Ficha adota uma régua comum de dimensões para impedir deslocamentos visuais entre cards e builds, sem cortar conteúdo variável:

- os quatro controles do Bloco 2, os botões de build, os controles compactos, os chips e a fileira de ações do Bloco 3 possuem alturas padronizadas;
- as colunas dos Blocos 1, 2, 3 e 4 continuam definidas pelas grades existentes, e toda caixa passa a ocupar integralmente a largura da célula que lhe pertence;
- placares, distribuição, técnico, habilidades, Ímpetos, atributos e os três painéis do Bloco 4 possuem alturas fixas ou mínimas compatíveis com sua função; caixas equivalentes sempre começam com a mesma geometria;
- distribuição, habilidades, Ímpetos, builds, atributos e medidas podem crescer quando o conteúdo real ultrapassar a reserva; nenhum texto ou dado pode ser cortado para manter uma altura artificial;
- a grade de builds mantém a decisão anterior: até 20 itens em quatro colunas e cinco linhas, encolhendo conforme a quantidade publicada no estado `pronto`;
- nos estados incompletos, as reservas estruturais anteriores continuam impedindo que os quatro blocos se recolham;
- em larguras menores, permanecem as regras responsivas existentes; a padronização atua dentro da largura disponível e não cria uma segunda versão da Ficha.

Na caixa de habilidades do Bloco 3, o título genérico `HABILIDADES` não é exibido. A seção começa diretamente em `HABILIDADES ESPECIAIS`, com cadeado `FIXA`, assim como as nativas. A expressão anterior `(não alteram a nota)` estava errada: ser fixa não significa não participar da pontuação. O cálculo continua sendo responsabilidade dos motores e não foi alterado nesta revisão visual.

Na caixa de técnico, o título auxiliar é `TÉCNICOS SUGERIDOS (não altera nota)`. A expressão anterior `MESMA NOTA` não é usada, pois o texto aprovado explica diretamente o efeito de trocar entre as sugestões apresentadas.

Nos grupos de atributos, o cabeçalho e as linhas usam a mesma grade interna: nome do grupo, coluna `BASE →` e coluna `FINAL`. Assim, cada título fica centralizado exatamente sobre os valores correspondentes, sem compor `BASE → FINAL` como um texto único encostado à direita.

### 22.15 Densidade da distribuição dos pontos

No zoom padrão de 100%, a área de construção deve permitir que o usuário veja a pontuação final, os elementos da build e a tabela de atributos na mesma tela, facilitando a comparação imediata durante os ajustes. Para aproximar esse objetivo sem reduzir a legibilidade do restante do Bloco 3:

- somente as linhas de `DISTRIBUIÇÃO DOS PONTOS` foram compactadas nesta etapa;
- o cabeçalho redundante `DISTRIBUIÇÃO DOS PONTOS` não é exibido; o resumo de nível, orçamento e gasto foi posteriormente substituído pelo contador descrito em 22.17;
- cada linha passa de `25px` para `22px`, o intervalo vertical cai de `4px` para `1px` e os controles laterais passam de `22px` para `20px`;
- o botão `OTIMIZAR` dessa caixa usa uma altura compacta própria de `32px`;
- nomes e valores continuam inteiros, centralizados e sem corte;
- habilidades, Ímpetos, técnico, ações e atributos mantêm as dimensões anteriormente aprovadas.

A área de atributos não exibe faixa explicativa nem aviso interno acima das colunas. O próprio cabeçalho `BASE → FINAL` comunica a leitura, e a remoção definitiva da faixa economiza uma linha vertical em todos os estados. A ausência ou atualização dos valores continua representada pelos próprios campos sem publicação e pelo estado geral da Ficha.

### 22.16 Gêmeas, comandos e estilos duplos — 06/09/2026

- As gêmeas aparecem individualmente em `HABILIDADES SUGERIDAS`, em itens compactos com quebra de linha. O hover da sugestão lista as habilidades adicionadas que ela pode substituir; o hover da habilidade adicionada apresenta as sugestões correspondentes. É sempre uma troca por vez, nunca substituir o grupo inteiro. Nativas e especiais não são alvos.
- A relação vem da publicação selecionada, do catálogo de gêmeas e da régua selada do resultado do Otimizador: efeitos e tipo idênticos, elegibilidade para fabricação, bloqueios da função, exclusão das habilidades nativas e das já adicionadas. Não há recálculo de nota no navegador.
- Técnicos equivalentes são derivados da mesma régua, comparando multiplicador e efeitos nos atributos com peso para a função. A sugestão informa os estilos compatíveis. Sem equivalência comprovada, a lista permanece vazia; sem contexto publicado, informa ausência de publicação.
- As builds do sistema permanecem somente leitura. Não existem manipuladores de substituição nas gêmeas. No futuro editor pessoal, a troca deverá validar a relação origem/destino atual, uma vaga por vez, sem duplicatas, inclusive no salvamento. O hover não substitui essa validação.
- A etiqueta auxiliar `DA BUILD` foi retirada do título de habilidades adicionadas; o título e o contador permanecem.
- O futuro botão `ADICIONAR HABILIDADE` usa um catálogo distinto das sugestões do Otimizador. A seleção pessoal admite toda habilidade adicionável pelo jogo àquela carta, inclusive as não recomendadas ou vetadas por decisão nossa. Não usar `bloqueia_funcoes`, incidência, dominância ou veto estratégico como permissão do editor. A origem de cada restrição deve ser explícita: jogo versus política do motor. A separação goleiro/jogador de linha será respeitada conforme os campos físicos validados; não foi confirmada aqui como sendo a única restrição existente.
- São fluxos diferentes: a gêmea é um atalho de equivalência para trocar uma habilidade compatível por vez; a substituição manual pode escolher outra habilidade permitida pelo jogo e alterar a nota. Os limites da carta, as cinco vagas adicionais, as nativas imutáveis e a proibição de duplicatas continuam valendo. O salvamento e o avaliador do futuro editor também devem aceitar escolhas legais que o gerador automático não selecionaria. Não habilitar a ação sem esse contrato; nenhuma regra dos motores foi alterada nesta etapa.
- A área de comandos ganhou moldura própria e maior contraste, com `SALVAR MINHA BUILD` mais destacado. A entrada `CRIAR NOVA BUILD` foi incluída no Bloco 2 para começar do zero; `PERSONALIZAR` significa partir de uma cópia. Criar, personalizar e salvar continuam indisponíveis enquanto não houver contrato do editor pessoal.
- A caixa de pontuação teve a altura mínima reduzida de 80 para 64 pixels, preservando o número de 38 pixels e os controles de distribuição de 20 pixels. Não foi reduzido novamente o tamanho de `+` e `−`. A intenção é liberar altura; o encaixe completo no viewport do usuário ainda requer conferência visual a 100%.
- O Bloco 1 apresenta ambos os slots físicos dos estilos de jogo. O slot 1 é ofensivo e o slot 2 defensivo, mesmo quando o catálogo do estilo aceita ambos. A posição nativa define apenas a hierarquia visual: GO/ZC/LE/LD/VOL priorizam o defensivo; CA/SA/PTE/PTD/MAT priorizam o ofensivo; MLG/MLE/MLD mantêm igual destaque. Mudar a build não altera a identidade do card.
- Os ícones em uso são os mesmos PNGs da referência eFHUB: `https://efhub.com/icons/CmnIconOffense_Small.png` e `https://efhub.com/icons/CmnIconDefense_Small.png`. Os bytes estão incorporados em `PLAYSTYLE_ICONS`, sem redesenho nem requisição extra. Os SVGs da primeira reprodução permanecem preservados, mas não são usados. Não foi feita extração própria do jogo. A origem dos nomes e slots continua no banco.
- No Bloco 4 foram retirados os totais visuais de bônus da IA e do físico, o chip de bônus do pé e a coluna de bônus das medidas. Permanecem os dados descritivos e os valores de `No card`, com os nomes de medidas por extenso. Os bônus continuam no contrato e no cálculo publicado, sem alterações.
- Os três campos do pé aparecem em três linhas, com valor textual. A RPC fornece `rotulo_valor`: `pe.nome_pt` para dominante e a etiqueta de valor preservada em `pe.nome_antigo` para uso/precisão. O frontend não converte o número em uma etiqueta presumida. No Shevchenko: Direito, Ocasionalmente e Muito alta. Números brutos e fatores de bônus continuam separados desses rótulos.

Validação: a leitura HTTP pública do Shevchenko `88045755964138`, linha `379897`, retornou `pronto`, nota `110,83`, `Artilheiro`/`Pressão No Ataque` e cinco sugestões. Toque duplo, Pedalada simples, Elástico, Chapéu e Finta de letra podem substituir individualmente Puxada de letra, Corte com virada ou Giro 360°. R. Martínez não possui equivalente comprovado nessa build. O teste de DOM com esse retorno real confirmou os dois sentidos do hover, consulta sem mutação, nomes completos e ausência das colunas/totais retirados. Não houve verificação visual pelo navegador nesta etapa.

A leitura foi otimizada para não reler a régua comprimida para cada técnico. O JIT foi desativado somente dentro da RPC `site_novo_ficha_v2`, pois a compilação da consulta composta excedia o timeout público; nenhuma configuração global, fila, motor ou resultado foi alterado. As migrações ficam em `Site Novo/supabase/migrations`; a definição anterior à adição de sugestões foi preservada em `RECUPERAR-FICHA-ANTES-SUGESTOES-20260906.sql`.

### 22.17 Contador e compactação complementar — 06/09/2026

- A distribuição apresenta somente `restantes/total`, com explicação acessível no hover. O DTO `build.pontos_distribuicao` vem da RPC; não há soma de custos no navegador. Campo ausente não vira zero: aparece `—/64` ou `—/—`. Uma carta sem evolução, com dez barras zero e orçamento zero, apresenta `0/0`.
- O helper privado `site_novo_contador_pontos_v1` valida dez chaves distintas, valores inteiros entre 0 e 25 e orçamento não negativo. Reproduz apenas o custo cumulativo de progressão já usado pelo Otimizador, sem alterar barras, resultados ou pontuação. No Shevchenko, níveis 5/8/13/10 custam 6/12/28/18: 64 gastos, zero restantes.
- A faixa superior redundante de atributos foi removida integralmente, incluindo `PONTOS POR ATRIBUTO · NÃO PUBLICADOS`; permanecem os cabeçalhos dos grupos, BASE e FINAL alinhados.
- A pontuação ocupa 64px; habilidades e Ímpetos usam menos preenchimento e intervalos. As duas caixas de Ímpetos continuam iguais e a fileira de comandos permanece ao fundo da coluna. A distribuição não se estica para preencher espaço vazio. Os controles `+` e `−` continuam em 20px, linhas de distribuição em 22px e número principal em 38px.
- A compactação não usa corte de conteúdo nem altura máxima forçada. O conteúdo pode crescer em telas estreitas. O objetivo de caber todo o Bloco 3 a 100% ainda depende de conferência visual no viewport do usuário; teste de DOM não mede geometria renderizada.
- `ADICIONAR HABILIDADE` é um botão desativado de forma explícita. O editor pessoal e a persistência continuam pendentes; a interface não simula salvamento nem libera edição de builds do sistema.

Validação atual: sintaxe JavaScript e smoke de DOM passaram com DTO lido diretamente da RPC no banco. O Shevchenko manteve nota 110,83, contador 0/64, cinco gêmeas e três hovers inversos. Foram testados também contador parcial 31/64, orçamento zero e valores ausentes/inválidos. Seis casos SQL de custo cumulativo passaram, incluindo os degraus 4→5 e 8→13.

Bloqueio de integração separado: o último teste HTTP público retornou 503 / `PGRST002` (falha do cache de schema do PostgREST). A consulta SQL da RPC funciona, mas isso não prova abertura pelo navegador. Não foram alteradas configurações globais nem reiniciado o projeto para contornar o erro. A validação visual e a leitura HTTP ponta a ponta permanecem pendentes.

### 22.18 Primeira apresentação sem quadros vazios — 06/09/2026

O HTML já entrega `#ficha-content` com `hidden`, protegido por regra crítica inline `display:none!important` antes do CSS externo. Portanto, a Ficha crua não é apresentada enquanto o JavaScript e a consulta carregam. Uma mensagem simples ocupa seu lugar, sem os quadros internos nem a moldura da Ficha.

`revealPopulatedFicha` libera o conteúdo somente depois de completar todos os renderizadores e validar o envelope. Não há temporizador, fade nem liberação no `finally`. Falha HTTP, parâmetros inválidos e card inexistente exibem mensagem sem revelar o desenho vazio. Respostas válidas ainda em publicação mostram o conteúdo real e seu estado explícito; a geometria aprovada desses estados permanece preservada.

Ao trocar de build, a anterior continua preenchida enquanto a consulta corre. A nova substitui a anterior no mesmo ciclo de renderização; uma falha conserva a anterior. Não foram adicionados retries, consultas extras nem mudanças na API.

Testes de DOM: primeira carga pendente oculta, sucesso preenchido visível, falha HTTP 503 oculta e erro na troca preservando a build anterior. A sintaxe passou e os hovers/contador/nota do teste anterior permanecem corretos. Esses testes verificam a barreira de apresentação; não são uma medição visual do viewport.

Complemento: a foto é carregada e decodificada antes da primeira apresentação, usando o próprio elemento que será anexado à Ficha. Se falhar ou não responder em seis segundos, a região apresenta `sem imagem`; não surge uma foto atrasada depois. Trocas dentro do mesmo card reutilizam a imagem e não fazem nova carga. A preparação respeita cancelamento de navegação.

O preenchimento direito das linhas de atributos passou a ser igual ao dos cabeçalhos (6px), eliminando a diferença horizontal entre os centros de BASE/FINAL. Os testes adicionais cobrem prioridade defensiva, meio-campo equilibrado, cinco cores, vaga cinza e cancelamento da imagem. Os exemplos reais por cor estão em `EXEMPLOS-CORES-IMPETOS.md`.

Diagnóstico adicional somente leitura: no Dashboard, o log de 06/09/2026 02:51:38 confirmou `57014` ao construir o cache com os schemas existentes `public,graphql_public`. O detalhe Postgres de 02:51:37 mostrou consulta de metadados de tabelas/tipos executada por `authenticator`; a configuração verificada desse papel tem `statement_timeout=8s`. O Dashboard também alertava esgotamento de múltiplos recursos, e chamadas do Bonificador apresentavam o mesmo 503. A causa da lentidão em si não foi atribuída a uma query de negócio sem evidência; nenhuma alteração de recurso/timeout global ou parada de worker foi feita.

### Compactação autorizada do Bloco 1 — 06/09/2026

Após o pedido para reduzir a altura sem deformar a arte, a foto passou a `width:100%; max-width:160px; height:auto`, mantendo `aspect-ratio:12/17`, `flex:none` e `object-fit:contain`. Assim, a carta inteira é reduzida proporcionalmente, sem recorte ou alongamento. O nome usa 18px, margem superior de 6px e pode quebrar sem truncamento.

As linhas da coluna 2 passaram a `66px 36px 32px minmax(116px,1fr)`, com estilos/posição centralizados e menor preenchimento. O campo acompanha a altura do bloco, com mínimo de 196px e preenchimento de 6px; os controles de posição conservam mínimo de 26px. A grade continua com quatro colunas iguais e a terceira coluna de respiro. Não foi imposta altura máxima que esconda textos longos.

Escopo: somente CSS do Bloco 1. Largura geral, Blocos 2–4, dados, fórmulas e comportamento da seleção não mudaram. Testes estruturais confirmam proporção, contenção integral da foto e controles preservados; testes de comportamento da Ficha continuam passando. Não houve captura visual do arquivo local nesta etapa.

### Bloqueio de posições indisponíveis — 06/09/2026

O campo continua mostrando todas as posições para orientação, mas só recebe interação onde o DTO informa posição principal ou aptidão maior que zero. Posições com nível zero, ausentes, nulas ou inválidas ficam com `disabled` e `aria-disabled=true`, sem listener de clique nem instrução acessível para selecionar. Não se infere permissão pela existência de build.

`togglePitchPosition` também rejeita códigos indisponíveis antes de modificar a seleção vinculada. Isso impede marcar uma posição proibida mantendo a build anterior na tela. O cursor das posições desativadas não sugere clique. Posições permitidas continuam destacando suas builds normalmente; regras do jogo, banco e cálculo não foram alterados.

Testes com o DTO real do Shevchenko verificaram todas as posições: tentativas nas indisponíveis não alteram campo, build, nota, URL ou número de consultas; PTD permitida segue selecionável. Casos de campo ausente, nível nulo e inválido também foram testados como bloqueados. Sintaxe e regressão dos hovers/contador/carregamento passaram.

### Legibilidade dos atributos — 06/09/2026

Aumento moderado solicitado: nomes dos atributos de 9,5 para 10,5px; valores BASE/FINAL de 8,5 para 10px; títulos de grupo de 8 para 9px; cabeçalhos BASE/FINAL de 9 para 10px. Linhas de atributos permanecem com 17px, agora com entrelinha explícita de 13px. Cabeçalhos usam entrelinha de 12px para não aumentar a altura do bloco. As três colunas, seus alinhamentos e espaçamentos foram mantidos. Testes estruturais e de comportamento passaram; não foi feita captura visual em zoom 100%.

### Restaurar altura ao atualizar — 06/09/2026

A posição horizontal/vertical é guardada por URL da ficha no `sessionStorage` da aba e no estado da entrada do histórico, preservando os demais campos desse estado. A gravação ocorre após rolagem (debounce de 150ms) e em `pagehide`, cobrindo atualização imediata. Falhas de acesso ao armazenamento não interrompem a Ficha.

Na primeira montagem, a posição só é restaurada depois dos dados e da foto, no momento em que o conteúdo preenchido deixa de estar oculto. A ficha temporariamente curta durante consulta/erro não sobrescreve a altura salva com zero. A restauração é instantânea e acontece uma vez; trocas de build não repetem esse salto. URLs diferentes não herdam o deslocamento de outro card/build. O navegador limita naturalmente o destino ao fim da página caso o conteúdo tenha ficado menor.

Testes de DOM verificaram destino de 620px após a montagem, captura imediata de 850px em `pagehide`, preservação do histórico, alternativa pelo armazenamento da aba, isolamento por URL e conservação da altura em falha HTTP. A validação não incluiu uma atualização visual automatizada do arquivo local.

### Vitrine e editor integrado — contrato vigente de 06/09/2026

A Ficha é uma vitrine somente leitura. Toda edição ocorre no modal. A faixa superior contém Build em Exibição, Criar Nova Build e Editar Build. A build em exibição ocupa metade da largura, com nome de 14px e superfície verde-clara; os comandos secundários têm altura fixa de 38px, frente aos 50px da identificação. Melhor e Minhas foram removidos, incluindo seus manipuladores: a grade já dá acesso às builds do sistema e pessoais.

Criar Nova Build inicia as barras zeradas. Editar Build abre os valores da build selecionada. Builds do sistema só podem ser usadas como modelo e salvas como cópia pessoal. As pessoais aceitam atualização ou cópia; na nuvem, o servidor confere propriedade e revisão.

Não é necessário login para consultar opções, calcular ou salvar no navegador. A conta fica recolhida em “Conta (opcional)”. Sem login, o salvamento usa o armazenamento local do navegador; limpar os dados do site remove essas cópias. Com conta, novas builds podem ser salvas no servidor. O cálculo depende de internet e continua privado em `2-MOTORES/EDITOR-BUILD`; nenhuma fórmula está no frontend e nenhum motor aposentado é chamado.

As builds pessoais aparecem na mesma grade em azul, com função-base e número permanente. Cada origem mantém seu contador; números excluídos não voltam a ser usados. O nome livre permanece no título/editor. Selecione a pessoal na grade e use Editar Build; o modal permite excluir, com confirmação. Excluir não aparece para modelos do sistema nem rascunhos novos. A exclusão na nuvem é lógica e verifica a revisão. Falha de exclusão mantém o rascunho aberto, permitindo tentar novamente.

Builds do sistema e pessoais participam da mesma classificação decrescente, usando a nota original recebida, antes do arredondamento visual. Em empate exato, o sistema precede a pessoal; os demais empates mantêm ordem estável. Valores sem nota válida ficam ao final, sem inventar zero. As do sistema mantêm cinco intensidades de verde (maior nota mais forte, menor mais suave) e as pessoais continuam azuis. A seleção não é alterada pela ordenação. Cada item da grade tem três colunas: nome à esquerda, posições centralizadas em 42px e nota à direita em 47px, com algarismos tabulares. O destaque superior mantém 50px, com espaçamento interno de 4px e linhas sem compressão para não cortar o nome. A grade recolhida mostra as primeiras 20 entradas da classificação conjunta; “Ver mais” aparece somente acima desse total e expande as demais, enquanto “Ver menos” recolhe. Esse crescimento é deliberado, somente após o comando do usuário.

No Bloco 3, Distribuição de Pontos e Habilidades compartilham a mesma linha de altura fixa; Técnico e Ímpetos compartilham outra. As larguras seguem a divisão aprovada de uma e duas partes. Os números das barras usam dourado claro, distinto dos nomes. Os nomes das habilidades e sugestões usam 11px. Os dois ímpetos têm caixas iguais. Os atributos do técnico ficam na caixa do nome; Talento Ofensivo/Defensivo só são abreviados quando falta espaço. Nomes têm iniciais maiúsculas, preservando títulos e textos já em CAIXA ALTA.

O modal dedica o miolo aos itens da build. A nota e Pode Melhorar ficam no cabeçalho; os comandos são compactos, e a autenticação só aparece quando solicitada. A comparação usa o mesmo comparador da vitrine, limitado à função corrente e às notas públicas do mesmo card. O resultado anterior não é apresentado como atual enquanto há avaliação pendente.

Na vitrine e no modal, os atributos em três colunas vêm acima de Distribuição/Habilidades e Técnico/Ímpetos. A ordem está no HTML compartilhado; o modal herda essa estrutura sem precisar de outra inversão por script. A vitrine permanece somente consulta. No modal, título/jogador, função, nome da build e pontuação compartilham o cabeçalho. O rótulo do campo de nome é acessível sem ocupar uma linha extra. A largura máxima é 1000px, deixando mais espaço lateral; não há banners novos inseridos. Conta, estado da avaliação e salvamento ficam no rodapé. A altura acompanha o conteúdo até o limite da janela, com margem externa de 8px por lado. As linhas pareadas preservam alturas mínimas de 280px e 114px; em desktop com altura útil até 820px, usam 240px e 92px, com atributos em linhas de 19px e entrelinha de 16px, usando o espaço liberado no cabeçalho sem aumentar sua fonte. O modo compacto reduz padding, elimina a caixa duplicada do seletor de técnico e a linha de bônus vazia; controles de pontos mantêm 24px de largura e 21px de altura. A inversão não altera dimensões nem espaçamentos. Habilidades e substitutas não têm rolagem própria nem corte. Não se usa overflow hidden para disfarçar itens fora da área: a rolagem geral continua como proteção em janelas excepcionalmente pequenas ou conteúdos maiores. BASE e FINAL não quebram de linha, e cabeçalhos e valores compartilham as mesmas colunas: Base em 42px e Final em 58px. Base mostra o atributo original da carta; Final mostra o atributo calculado do sistema, incluindo habilidades. O atributo de jogo permanece nos dados, sem coluna visível. O pós-evolução permanece no detalhe de cada linha. A antiga regra que deslocava atributos para a lateral em telas baixas foi removida. Validação automatizada é estrutural/DOM; a ausência de overflow no Chrome real não foi medida nesta sessão.

O cabeçalho ÁREA DA BUILD usa fonte de 10px e não exibe mais “Visualizando Recomendação/Minha Build”. A identificação da seleção continua no destaque e na grade. BUILDS DESTE CARD tem título próprio e três etiquetas discretas com quantidades reais: do Sistema, Posições e Salvas. Os textos “canônicas” e “ordem publicada” foram retirados desse cabeçalho; a ordenação não mudou.

Na vitrine e no modal, as habilidades de fábrica preenchem a altura da coluna esquerda. As quantidades reais de especiais e nativas definem linhas de mesma altura, com mínimo de 20px por habilidade e títulos separados. Isso não estica nem redistribui a coluna de adicionadas/substitutas. Grupos vazios mantêm sua indicação, sem criar habilidades fictícias.

O título HABILIDADES SUBSTITUTAS não exibe mais o sufixo “(gêmeas)”; as regras e hovers permanecem. Nos atributos, os nomes dos grupos usam dourado (#e4bc79), BASE usa azul-claro (#bacddb) e FINAL azul-claro mais luminoso (#e0ebf5). Valores da carta base ficam em azul-claro; valores finais do sistema em verde. Os nomes dos atributos usam peso 400, sem negrito; os títulos dos grupos e o destaque dos resultados são preservados. O rótulo aprovado é FINAL, mas o valor exibido é do sistema, não do jogo. Habilidades não acrescentam atributos ao valor de jogo, mas sua valoração entra no valor do sistema. Os dois vêm do servidor: a vitrine lê os vetores da build publicada e o modal recebe as duas saídas da avaliação privada. A nota e as fórmulas não mudaram. Snapshots pessoais antigos sem valor de sistema mostram ausência até novo salvamento explícito; nunca usam o valor do jogo como substituto.

Entrar / Criar conta abre e-mail, senha, Entrar e Criar conta no próprio rodapé, substituindo o botão. Os campos e comandos usam 28px de altura; a área da build não é deslocada. O resumo de status cede seu espaço visual enquanto os campos estão abertos (continua acessível), e mensagens de autenticação aparecem junto ao formulário, sem aumentar sua altura. × ou Escape recolhem somente os campos, preservando o rascunho e devolvendo o foco. O login continua opcional e suas chamadas ao serviço não foram alteradas. Com login, o rodapé mostra o nome disponível na sessão (full_name, name ou display_name), ou o e-mail quando não há nome, junto do comando Sair. A identificação usa textContent e não concede permissões; o ID autenticado continua sendo a identidade de autorização.

Os controles do editor reutilizam o desenho da vitrine: habilidades adicionadas verdes com remoção compacta; títulos dos ímpetos centralizados e coloridos, bônus uniforme em caixa separada e efeitos em mini-etiquetas da mesma cor. O bônus exibido deriva apenas dos efeitos recebidos do catálogo; não é cálculo de nota. O nível condicional continua editável na caixa do bônus. Técnico e seus atributos ficam na mesma caixa, com o seletor integrado. As alterações mantêm a vitrine somente para consulta.

O comando de zerar a distribuição se chama Limpar Pontos. Continua exigindo confirmação, pois fica perto de Salvar Minha Build. A confirmação informa que habilidades, técnico e ímpetos serão mantidos. Cancelar não altera nada; confirmar zera apenas as barras do rascunho e reavalia, sem salvar automaticamente nem alterar o modelo.

No cabeçalho de pontuação do modal, Pode Melhorar ocupa coluna de 70px sem encolhimento. O título preserva somente a quebra explícita em duas linhas de 9px, e o percentual ocupa outra linha de 14px sem margem adicional. O conjunto cabe no cartão compacto de 38px, sem alterar a altura do modal.

O técnico escolhido tem mais destaque: nome de 11px em peso 750 e caixa verde; substitutos usam nome de 9,5px em peso 500 e fundo discreto. Cada substituto exibe à direita os atributos da sua própria versão, sem agrupar por nome. A descrição dos estilos (por exemplo, Contra-ataque ou Passe Longo) foi retirada da interface. O substituto mantém apenas nome e atributos da versão; os dados e a regra de equivalência permanecem intactos. No editor, os atributos também acompanham o botão de substituição. A migração `20260906080929_ficha_substitutos_atributos_v1.sql` acrescenta somente a projeção de atributos ao helper privado já existente, com privilégios preservados. As linhas 379010 e 379011 foram comparadas antes/depois: o payload inteiro permanece igual ao remover apenas os novos campos de atributos; nota, habilidades e seleção de equivalentes não mudaram. O teste HTTP/DOM `technicians-public.cjs` conferiu Rudi Garcia e a versão 17602655027637 de M. Allegri, com Talento Ofensivo +1 e Controle de Bola +1.

Habilidades disponíveis seguem o catálogo de treino, sem os vetos estratégicos do Otimizador. Os títulos são HABILIDADES SUBSTITUTAS e TÉCNICOS SUBSTITUTOS. As gêmeas mostram hovers em ambos os sentidos e só substituem uma origem compatível por vez; a equivalência é conferida no servidor. Entradas inválidas, habilidades repetidas/nativas, orçamento excedido, ímpetos proibidos e posições sem aptidão são rejeitados.

Reafirmado por Luis em 08/09/2026: a proibição de Volta para marcar nas dez
especialidades do Otimizador não restringe o usuário. O editor admite essa
habilidade quando treinável na carta, outras escolhas pessoais e zero habilidades
adicionais. A restrição estratégica inserida indevidamente nesta data foi retirada
do JavaScript, catálogo e avaliador; a migração
`20260908210044_restaurar_liberdade_editor_habilidades.sql` restaura as definições
anteriores. O gerador automático continua sujeito à sua tabela de bloqueios.

A atualização conserva a posição de rolagem. O conteúdo inicial só é revelado depois do preenchimento. Fechar um rascunho alterado exige confirmação; salvar bloqueia fechamento até a resposta. Reenvios são idempotentes. A vitrine não muda enquanto se edita o rascunho; dados pessoais confirmados são recarregados na grade.

Testes executados: casos manuais de fórmula, 26 atributos do Shevchenko, entradas inválidas, gêmeas, propriedade, revisão, numeração e exclusão com rollback; HTTP real de cálculo sem login e recusa de gravação anônima na nuvem; armazenamento local, recuperação após recarga e não reutilização de números; DOM integrado de edição, comparação, grade mista, expansão, cores e comandos. Testes de DOM não equivalem à validação visual no Chrome. O envio de e-mail e o login com conta real do usuário não foram executados.
## Correção France 1998 e busca aproximada — 07/09/2026

A relação pública recebeu `Big Time & Epic: France 1998` com as cartas Marcel
Desailly (`89138288270047`), Lilian Thuram (`88044145351392`) e Patrick Vieira
(`88044145348029`). A data permaneceu nula porque não havia prova confiável para
preenchê-la. Os rótulos antigos `Big Time France` continuam preservados sem
fonte e fora do site; não voltaram a ser tratados como nome de Box.

A RPC cadastrada mantém a pesquisa por trecho sem acento e acrescenta
similaridade somente para termos de cinco ou mais caracteres. O readback público
confirmou que `desailly` e `desaily` retornam a mesma Box, com três cards, e que
o DTO não expõe `percentual_topo`. O total público após a correção é 1.022 Boxes
e 6.698 vínculos.

## Conferência visual do site publicado e correções — 07/09/2026

**Decisão do usuário:** conferir visualmente o que já está construído e corrigir tudo o que
estivesse errado, com exceção da busca: o nome do jogador se repete por natureza e é a **arte
do card** que diferencia um card do outro, por isso a busca mostra a foto. Nada a mudar ali.

**Escopo autorizado:** correções de apresentação e a conexão da Início. Nenhuma alteração de
banco, motor, fila, publicação ou contrato público.

**Como foi conferido:** a pasta foi publicada no Netlify Drop
(`extraordinary-twilight-cc1b29.netlify.app`) e percorrida no Chrome real do usuário — Início,
Ranking com filtro de setor e paginação, Boxes cadastradas, Boxes em andamento, busca por
"messi", Ficha completa de Lionel Messi `89136409091415`, Elenco e a troca de tema. Console
limpo em todas as telas. As notas conferiram entre Ranking e Ficha (113,77 nos dois).

### O que foi corrigido

1. **Tema claro deixava o cabeçalho da Ficha ilegível.** `ficha.css` não tinha nenhuma regra
   para `data-theme`, então no tema claro o cabeçalho ficava com fundo claro e texto claro — a
   marca CLUBeFOOTBALL desaparecia — enquanto o corpo continuava escuro. Medido:
   `headerBg rgba(239,243,240,.96)` com `color rgb(230,235,232)`.
   **Regra nova:** no tema claro a *moldura* da página (fundo, cabeçalho, rodapé e o espaço dos
   banners) acompanha o tema do site; o **painel da Ficha (`.stage`) mantém a paleta escura
   aprovada**, porque as cores dos quatro blocos são desenho congelado. Readback:
   `bodyBg rgb(255,255,255)`, `headerCor rgb(20,24,27)`, `stageFundo rgb(23,28,25)`.
2. **Altura sem unidade em Medidas do Corpo.** A altura é a primeira medida da relação corporal
   e a de maior bônus (0,75 no Messi); o valor `170` aparecia no meio de índices de 2 a 10. O
   dado do banco está certo — faltava a unidade. Agora a linha da altura exibe `170 cm`. Nenhuma
   mudança de contrato, de dado ou do bônus.
3. **ELENCO · INDISPONÍVEL** continuava na posição aprovada, porém com moldura e texto dourados,
   competindo com a pontuação. Passou a usar a cor apagada dos controles indisponíveis. Texto e
   posição preservados, conforme a regra de manter a ação visível e identificada como indisponível.
4. **Rótulo `BANNER 160 × 600`** removido dos dois espaços laterais da Ficha. O espaço reservado
   e sua área continuam iguais.
5. **Faixa "Filtros ativos" repetia o que já estava aceso.** Setor e função têm botão visível
   permanente no Ranking; viravam etiqueta de novo logo abaixo, empurrando o pódio. A faixa agora
   só aparece quando existe filtro **sem** controle visível (busca, posição nativa ou estilo), e
   nesse caso lista todos, inclusive setor e função, com o botão Limpar todos.
6. **"Sem pontuação publicada" saía em verde** na busca, a mesma cor da pontuação real. Passou a
   usar a cor apagada. Ausência não se anuncia como valor.
7. **Nome de card cortado nas Boxes** ("Alejandro Grimal…"). A regra genérica de uma linha vencia
   por ordem no arquivo. O nome agora ocupa até duas linhas dentro da altura já reservada, sem
   corte. Readback: 68 nomes na primeira página, zero cortados.
8. **Legenda das etiquetas de contratação** ficava centralizada e sem título, parecendo controle
   clicável. Recebeu o rótulo `Vale a pena contratar?`. O texto do seletor de ordenação passou de
   "Boxes fora das ofertas em andamento" para "Esta lista não inclui as boxes em andamento."
9. **Rodapé** deixou de dizer "Estrutura em construção · módulos conectados por etapa".

### A Início conectada

A Home anunciava que o site não funcionava — "Card em destaque · Aguardando conexão",
"PUBLICAÇÃO DAS BUILDS · Não conectada" e dois painéis vazios — enquanto Ranking e Boxes já
estavam conectados e respondendo.

Arquivo novo `home.js`, com `window.SiteNovoHome.mount(node)` / `unmount()`, montado pela rota
`inicio` do `site-shell.js`. Ele **não cria contrato novo**: lê exatamente as duas portas públicas
já aprovadas, `public.site_novo_ranking_v1` (modo card, 5 itens) e `public.site_novo_boxes_v1`
(catálogo, 5 boxes), pelos mesmos adaptadores `SiteNovoRankingAPI` e `SiteNovoBoxesAPI`, com o
degrau escolhido no cabeçalho. Não calcula nota: formata `nota_final` com duas casas, como as
demais telas.

- Card em destaque: o primeiro do Ranking, com foto, nome, função e posição, abrindo
  `ficha.html?card=&linha=` da linha exata.
- Placar do herói: total de cards com build publicada, vindo do `total` da própria porta.
- Painel "Quem tá no topo?": os cinco primeiros, cada um com sua linha publicada.
- Painel "Boxes cadastradas": as cinco boxes mais recentes, com data da oferta e contagem.
- Elenco continua declarado como **não conectado** — não existe contrato de elenco.

Falha de uma porta não derruba a outra metade e nunca vira número inventado: cada painel mostra
seu próprio estado (`carregando`, `pronto`, indisponível). Uma leitura por porta, cancelável, e
recarga quando o degrau muda.

**Prova:** `tests/home.test.cjs`, 7 blocos, sem rede — carregamento sem número, uso exato do que
a porta entregou, formatação de nota sem imprimir o valor cru, link com card e linha, escape de
HTML no nome recebido, recusa de foto fora de `https`, falha total e falha parcial sem dado
reaproveitado, e uma única leitura por porta. `node --check` passou em `home.js`, `site-shell.js`,
`ficha.js`, `ranking.js`, `search.js` e `boxes.js`. Os testes que rodam sem rede continuam
passando: `site-shell`, `site-theme`, `boxes-state`, `ranking-state` e os três do editor.

**O que não foi provado:** os testes que fazem chamada HTTP real (`ranking`, `boxes`,
`boxes-search`, `search`, `degrau`, `ficha-degree`) não puderam rodar neste ambiente, que não
alcança o Supabase; precisam ser rodados na máquina do usuário. A conferência visual das telas
corrigidas foi feita em navegador com resposta pública real das Boxes e com o payload real do
Ranking; a Ficha corrigida não foi vista com dados nesta etapa.

## Filtros por assunto, hover do degrau e Como funciona — 07/09/2026

**Decisões do usuário nesta sessão (revisão do site publicado):**

- **Contexto/régua da nota: SUSPENSO.** Ele não quer poluir a tela, e a referência é variável — o
  jogador pode querer ler por posição, por função ou por outro corte, e uma etiqueta ancorada num
  só recorte confunde em vez de ajudar. Não implementar até ele decidir o recorte.
- **Comparador de dois cards: aprovado, mas depois.** Vai ser **aba separada**, e só depois de
  fechar o que já está na tela.
- **"Publicados nas últimas horas": recusado.** O site só vai ao ar quando todos os cards
  estiverem publicados; depois a atualização é semanal, acompanhando o jogo. Uma faixa de recentes
  não faz sentido nesse ciclo.
- **Etiqueta agregada na capa das Boxes: recusada** pelo mesmo motivo — quando o site for ao ar,
  tudo estará publicado e a informação já estará nos cards.
- **Filtro na busca: recusado.** Regra registrada pelo usuário: **as pessoas buscam pela arte do
  card.** O nome do jogador se repete por natureza (são dezenas de Messi) e muita gente não lembra
  de cabeça a especialidade da carta — lembra da imagem. A memória visual é mais forte, e é por
  isso que a busca mostra a foto. Não acrescentar filtros ali.
- **Explicar o que é Ímpeto: desnecessário** — quem joga sabe. O que faltava era explicar o efeito
  do **seletor de degrau**.
- **Entrada da Ficha por ID: removida.** Ninguém sabe o ID de um card; a busca já resolve.
- **Elenco:** o usuário vai fazer, depois de fechar as outras áreas. É página bem mais complexa.
  Existiam partes dela no legado, mas o legado está desorganizado e não será reaproveitado.

### O que foi feito

1. **Filtros do Ranking, uma coluna por assunto.** O painel já era de três colunas, mas na ordem
   Estilo → Posição → Função, com rótulos apagados que não pareciam colunas. Passou a ser
   **POSIÇÃO → FUNÇÃO → ESTILO DE JOGO**, com posição na frente porque é como o jogador pensa.
   Cada coluna recebeu título próprio, uma linha explicativa ("Onde o card joga no campo", "O
   ofício dentro do time", "O comportamento do card") e divisória vertical. Em telas estreitas as
   colunas empilham sem divisória. Nenhuma mudança de contrato, parâmetro ou consulta.
2. **Hover do degrau condicional.** O `title` do seletor passou a dizer o efeito real: o site
   inteiro passa a mostrar as notas calculadas naquele degrau, do primeiro nível ao máximo. Vale
   no `index.html` e na `ficha.html`.
3. **"Abrir Ficha pelo ID"** saiu da vitrine da Início.
4. **Cabeçalho no celular.** Abaixo de 560px a marca CLUBeFOOTBALL era coberta pelo bloco do
   ímpeto condicional. O rótulo "Ímpeto condicional" some nessa faixa (ficam o ícone e os botões
   1 · 2 · 3, com o hover explicando), a marca e o ícone encolhem, e as abas rolam sem cortar
   palavra.
5. **Lugar da foto no tema claro.** Quando a foto não carrega, o espaço usava uma cor escura fixa
   e virava um retângulo preto sobre fundo claro. Passou a usar a superfície do tema.
6. **"Como funciona" reescrito.** A página ainda dizia que o site estava "sendo conectado por
   etapas" e que "as demais áreas estão identificadas como não conectadas" — falso desde que
   Ranking, Boxes, Busca e Ficha entraram. Agora explica, em linguagem de jogador: função não é
   posição, de onde vem a nota (e que ela não é o overall do jogo), o que o degrau do ímpeto faz,
   e o que cada área mostra. O Elenco continua declarado como ainda não pronto.
7. **Card em destaque da Início.** Em tela estreita o "Atacante criador · PTD / PTE" vazava para
   fora da moldura porque a caixa tinha altura travada em 232px; agora cresce com o conteúdo.

**Prova:** `node --check` em `ranking.js`, `home.js` e `site-shell.js`. Os testes sem rede
continuam passando: `site-shell`, `home`, `site-theme`, `ranking-state` e `boxes-state`.
Renderização conferida em navegador a 1440px e a 390px, com a resposta pública real das Boxes e
o fixture real do Ranking: painel de filtros nas três colunas, marca legível no celular, Início
sem a entrada por ID e "Como funciona" com o texto novo. Console limpo em todas as telas.

**O que não foi provado:** os seis testes que fazem chamada HTTP real continuam pendentes
(`SITE-NOVO-PEND-012`). A conferência do site publicado depois deste lote depende de novo deploy.

## EXIBIR RANKING POR, e os rótulos que o peso não sustentava — 07-08/09/2026

### A faixa do Ranking passou a ser EXIBIÇÃO, não filtro combinável

Duas correções do próprio usuário, nesta ordem. Primeiro: o que ele queria não eram filtros, e sim
as **classificações**. Depois: elas **não se combinam** — "vai uma exibição; se ele clicar lá em
posição, vai aparecer exibido por posição, o ranking por posição".

Removidos: a barra de setores (Geral · Goleiro · Defesa · Meio · Ataque), o botão **Filtros**, o
painel escondido, a faixa "Filtros ativos" e também a versão intermediária de três colunas
combináveis, que foi descartada por essa segunda correção.

No lugar entrou a faixa **EXIBIR RANKING POR**: três abas de largura cheia, nesta ordem exigida por
ele — **POSIÇÃO · ESTILO DE JOGO · ESPECIALIDADE** — e, abaixo da aba acesa, o escolhedor do item
daquele eixo. Posição vem primeiro porque é como o jogador pensa o campo. Posição (13) e
especialidade (19) usam chips, porque cabem; estilo de jogo usa `<select>`, porque são 36 opções e
como chips a faixa viraria um paredão. Ao lado da faixa fica uma linha curta explicando o eixo
aceso. As abas empilham abaixo de 640px.

**Uma exibição por vez, garantido no código:** trocar de aba zera os três parâmetros
(`p_posicao_nativa_id`, `p_estilo_id`, `p_funcao_id`), e escolher um item de um eixo zera os outros
dois. Não existe estado em que dois eixos estejam ativos ao mesmo tempo.

"por card · por jogador · Mix" continua abaixo, porque é modo de leitura, não exibição.

**Cuidado registrado:** `p_setor` deixou de ter controle na tela. Um valor herdado do
`sessionStorage` filtraria a lista sem o leitor ver de onde. O estado restaurado agora força
`p_setor='geral'` e valida `eixo`, aceitando estado antigo que não tinha esse campo.

### A palavra "função" não aparece mais na tela

Regra do usuário: **função é termo estritamente interno**. O ID, a tabela, a coluna, o parâmetro da
RPC e este manual continuam dizendo função; a **tela** não. A palavra escolhida foi
**especialidade** — a que ele mesmo usou ao falar do leitor ("as pessoas nem sequer lembram de
cabeça qual é a especialidade da carta").

Trocado em: aba do Ranking (`ranking.js`, array `eixos` — **um único lugar**, é só trocar a string
se ele preferir outra palavra), Início (`home.js`), Boxes (`boxes.js`, ajuda da etiqueta), Ficha
(`ficha.js`, "Especialidade não publicada") e Como funciona (`site-shell.js`, seção inteira
reescrita). **Não** foi trocado no editor interno da Ficha (`ficha-editor.js`,
`ficha-editor-api.js`), que é ferramenta de uso próprio.

### Rótulo é dado do banco, nunca texto na tela

Regra do usuário: tudo que aparece na tela é variável ligada a campo do banco. Rótulo de função se
muda em `clube_novo.funcao_sistema.rotulo`, que é a fonte única lida por todas as telas — **não se
mapeia nome na tela**.

Migração `rotulo_publico_das_duas_funcoes_de_driblador`:

- id 12: `Ala finalizador` → **`Ala driblador`**
- id 15: `Atacante finalizador` → **`Atacante driblador`**

Motivo, medido no `arows_snapshot`: as duas funções chamadas "finalizador" eram justamente as que
menos valorizavam Finalização — **peso 3** numa escala que vai a 12 — enquanto Controle de bola,
Drible, Condução firme, Velocidade e Aceleração estavam todas no máximo. Id, grupo, ordem, molde,
pesos, alvos e notas ficaram intactos. Readback: a RPC do Ranking já devolve "Atacante driblador"
sem nenhum arquivo do site ter sido alterado.

A medição completa dos 26 atributos das 19 funções está em
`claude/MEDICAO-0709-OS-MOLDES-DAS-19-FUNCOES-e-o-rotulo-que-nao-bate-com-o-peso.md`.

### Erro meu, registrado para não se repetir

Eu afirmei que cinco pares de funções tinham "molde idêntico". **Estava errado.** Eu havia
comparado apenas o conjunto dos cinco atributos de peso 12. Comparando os 26 completos, peso e
alvo, nenhum par é igual — os meias diferem em 7 pesos, os zagueiros em 1 peso e 17 alvos, os
goleiros em 20 alvos. **Comparar molde é comparar os 26 com peso e alvo, nunca só o topo.**


## Auditoria e publicação de 08/09/2026

O adaptador ranking-api.js envia somente os parâmetros públicos da RPC, nunca o estado visual eixo. Ao restaurar uma sessão, ranking.js limpa os filtros das outras abas e mantém p_setor=geral. Os scripts corrigidos têm versão 2026090803 no index. A suíte passou com 15 testes. Registro de auditoria: AUDITORIA-SITE-20260908.md. Publicação final Netlify: 6aa0946c7a2721d1c2966e1f. Pacote público: 21 arquivos, sem documentos internos. Não houve alteração em banco, motores, filas ou liberdade do editor pessoal por esta auditoria.

## 09/09/2026 — correcao pontual completa e refila V12

A correcao pontual de habilidades recompõe os 26 atributos e etapas no servidor; a ficha le o novo O pela publicacao ativa, inclusive atributos sem peso na funcao. Sem Bonificador compativel, a linha permanece aguardando. Nenhuma mudanca na liberdade do editor pessoal. Ver `../4-DOCUMENTOS/OTIMIZADOR/HABILIDADES-0909/CORRECAO-PONTUAL-E-REFILA.md`.


## Revisão das fotografias de Boxes — 09/09/2026

Autorização posterior: atualizar as avaliações congeladas para a normalização vigente, não apenas o desenho das estrelas. `clube_novo.box_avaliacao_revisao_0909` guarda nova fotografia por box/card/degrau, consumida por `site_novo_box_card_analise_snapshot_v1`; o leitor original e os 2.621 snapshots antigos permanecem preservados. Esta revisão substitui a orientação anterior de manter exclusivamente a avaliação antiga na tela.

Foram capturadas 20.094 fotografias (6.698 vínculos de cards, 1.022 boxes, três degraus), contendo 44.827 análises. Cards sem publicação elegível ficam sem avaliação; nenhuma nota foi inventada. As faixas de contratação e os motores permanecem iguais. Não há atualização contínua dessa fotografia: nova revisão exige decisão própria. Fontes: publicações exibíveis vigentes, melhor linha por função/degrau e topo global da função, como na régua de contratação existente.

Readback: zero divergências de identidade, nota, degrau ou estrelas inválidas. Cristiano Ronaldo `89138556572074`, Living Legends 2026, degrau 3: Centroavante fixo, linha 364310, nota 111,3542550014243, cinco estrelas. SQL de implantação: `4-DOCUMENTOS/NORMALIZACAO-0909/06-RENOVAR-AVALIACOES-BOXES.sql`. A correção é no banco e já é consumida pelo site publicado; não exige novo deploy nem pacote para a Máquina 2.


## Ranking — reorganização visual de 10/09/2026

Implementação local autorizada: modos por card / por jogador / Mix centralizados na primeira linha; abas Posição / Estilo de jogo / Especialidade na segunda; escolhas em botões maiores ocupando toda a largura e quebrando em linhas conforme o espaço. Posições preservam a sequência existente. Estilos ficam em ordem alfabética em português. Especialidades seguem goleiros, zagueiros, laterais, volantes, meias, alas e ataque. Os rótulos continuam vindo do catálogo. Removida a linha EXIBIR RANKING POR e sua explicação, conforme correção posterior do usuário.

Busca centralizada abaixo dos filtros e da contagem, no lugar da paginação superior. Paginação somente no rodapé. A faixa acompanha a rolagem para que a lista aberta de estilos não cubra os resultados. Seleção, consultas, notas, motores e filas preservados. Arquivos: ranking.js, ranking.css e versão dos recursos no index.html; expectativa da paginação atualizada no teste existente.

Validação: sintaxe e três testes do Ranking aprovados; navegador local confirmou posições em largura completa, estilos em botões alfabéticos e remoção do cabeçalho. Publicação não realizada nesta etapa; aguarda o usuário encerrar suas solicitações. Esta seção substitui a organização visual histórica com seletor fechado, modos abaixo e paginação duplicada.


Publicação confirmada em 10/09/2026: projeto imaginative-granita-ace1ca, deploy 6aa224a6ba9f17d19cc04436. Pacote de 21 arquivos públicos obtidos da versão já publicada, substituindo somente ranking.js, ranking.css e as versões desses recursos no index.html. HTTP 200 e igualdade integral dos três arquivos com o pacote; navegador público confirmou o novo layout com resultados carregados. GitHub não alterado.


Correção visual posterior de 10/09: usuário rejeitou os botões largos de estilos/especialidades. Agora têm largura pelo texto, altura mínima de 30px, padding 6x10px e não crescem para preencher a última linha; grupos centralizados e ordem preservada. Posições mantêm a distribuição anterior. Conferência visual local dos dois eixos e HTTP público dos arquivos CSS/index aprovados. Publicado no mesmo projeto Netlify, deploy 6aa22562694a4935b0b31922. Apenas CSS e sua versão no index mudaram nesta correção.


Ajuste solicitado em seguida: fonte dos botões de estilos/especialidades reduzida de 12px para 10px, altura mínima 24px e padding 4x7px. Posições preservadas em 12px. Publicado e conferido por HTTP e navegador: deploy 6aa225cb26045a94b72926ec; CSS versão 2026091003.


## Correção do ranking por posição — 10/09/2026
Autorização posterior à frente de design: filtrar pela posição da linha publicada antes do agrupamento por card/jogador/Mix. O parâmetro histórico p_posicao_nativa_id continua com o mesmo nome por compatibilidade, mas compara a.posicao_id; a posição principal do card não participa mais. Fonte vigente build_publicacao_exibivel_v3 preservada, assim como degrau, notas, agrupamento e ordenação. Nenhum motor, fila ou resultado foi alterado.
Aplicada migration ranking_filtrar_posicao_da_linha_publicada. Definição integral vigente: CORRECAO-RANKING-POSICAO-LINHA-1009.sql. A correção substitui a descrição antiga de filtro por posição nativa neste manual.
Validação: 60 resultados em cada uma das 13 posições, zero fora da posição; VOL nos três modos e três degraus, 60 resultados por consulta e zero divergências. Caso Pirlo: antes linha 36411 em MLG (114,2832) com VOL selecionado; agora o card 88039581945312 usa linha 36413, VOL, Volante de construção, 113,9056. A leitura pública pelo adaptador real confirmou as linhas VOL 36666, 36413 e 32620. Mudança no leitor já atende o site publicado, sem novo deploy de frontend.


## Estilo ativo antes da seleção — 10/09/2026
Regra confirmada pelo usuário: um estilo selecionado exige vínculo do estilo ao card e ativação na posição da linha publicada. Usa bonificador_regra_playstyle por playstyle_id/posicao_id com da_bonus=true, como na política vigente; Básico 256 não ativa. Não exige associação histórica à função. Só depois escolhe a maior nota por card, jogador ou card/especialidade no Mix. Posições exibidas derivam desse mesmo conjunto elegível. Estilos sem ativação cadastrada não geram resultados; nenhuma regra foi inventada.
Migration aplicada: ranking_selecionar_somente_estilo_ativo_na_linha. Definição integral em CORRECAO-RANKING-ESTILO-ATIVO-1009.sql, sucessora da correção por posição. Notas, motores, filas e cadastro de ativação preservados. Validação: Artilheiro (257) somente CA, 60 resultados por modo sem divergência; 36 estilos consultados e 139 linhas verificadas sem inconsistência; adaptador público confirmou 33 linhas CA por modo.
Botões POR CARD / POR JOGADOR / MIX em maiúsculas. CSS 2026091004 publicado no projeto imaginative-granita-ace1ca, deploy 6aa22e9f7c0ca1dc58c6b219, conteúdo público igual ao pacote.


10/09: TODAS e TODOS OS ESTILOS em maiúsculas nos três critérios do Ranking. Botão geral com borda verde reforçada e preenchimento verde/texto escuro quando selecionado; variante compatível com tema claro. Publicado, arquivos conferidos por HTTP e visual público inspecionado. Deploy 6aa22ffeb9c9604a064ee771, CSS 2026091005.


## Capitalização e auditoria de nomes — 10/09/2026
19 especialidades padronizadas em funcao_sistema.rotulo com iniciais maiúsculas em todas as palavras. Estilos Konami preservados. Quatro colisões exatas encontradas: Goleiro Defensivo, Goleiro Ofensivo, Lateral Defensivo e Lateral Ofensivo. Propostas de Recuado/Avançado aguardam escolha do usuário; não foram aplicadas nesta etapa.
Leitor site_novo_box_card_analise_snapshot_v1 passa a resolver o rótulo atual pelo funcao_id da linha, mantendo intactos os snapshots. SQL: ESPECIALIDADES-ROTULOS-1009.sql. Conferência de 60 fotografias/438 análises: zero alterações fora do campo funcao e zero nomes fora do padrão. Ranking e Ficha devolveram Volante De Construção pelo banco; todas as 19 especialidades conferidas. Não houve recálculo, mudança de IDs, fórmulas ou filas. Demais famílias de nomes de jogo não foram alteradas por esta etapa.


## Renomeação aprovada e aplicada — 10/09/2026
Após aprovação dos quatro nomes: ID 4 Goleiro Recuado; ID 5 Goleiro Avançado; ID 6 Lateral Recuado; ID 7 Lateral Avançado. Alterado apenas funcao_sistema.rotulo. IDs, notas, motores, filas e estilos oficiais preservados. Readback dos quatro nomes no Ranking, Ficha e leitor de Boxes confirmou os rótulos novos; zero colisões exatas com playstyle.nome_tela. A pendência de aprovação anterior está encerrada. A mudança já atende o site publicado sem deploy de frontend.


10/09: corrigida ambiguidade visual do botão TODAS inativo. Usa borda tracejada e texto neutro quando não selecionado; verde exclusivo do estado selecionado. Mesma regra em TODOS OS ESTILOS, com tema claro contemplado. Conferência visual pública com Centroavante Fixo selecionado confirmou TODAS neutro. Deploy 6aa2329c7c0ca1fca6c6b074, CSS 2026091006, arquivos públicos conferidos.


### 10/09/2026 — Estado dourado do filtro Todas
TODAS / TODOS OS ESTILOS usa fundo dourado preenchido e texto escuro quando selecionado; quando inativo, fundo escuro com texto e borda dourados. Tema claro tem contraste correspondente. Publicado no projeto imaginative-granita-ace1ca, deploy 6aa233ef26045ae7402926bd, ranking.css v2026091007. CSS e index públicos conferidos contra o pacote; aria-pressed e cores dos dois estados verificados no navegador.

### 10/09/2026 — Informacoes complementares no Ranking
Em Todas nos tres eixos, exibir Especialidade e Estilo de Jogo, mantendo a etiqueta de posicao. Posicao especifica tambem mostra ambos; estilo especifico mostra somente Especialidade; especialidade especifica mostra somente Estilo de Jogo. Regra igual em POR CARD, POR JOGADOR e MIX. Removidos os nomes e links de boxes de origem dos cards do Ranking.
RPC site_novo_ranking_v1 recebe campo aditivo estilos (id/nome), lido de carta_playstyle_jogo e playstyle.nome_tela em ordem de slot fisico; a tela apresenta os nomes distintos. Se nao houver nome cadastrado, informa Nao informado. Filtros, selecao, classificacao, notas e permissões existentes preservados. SQL registrado em RANKING-ESTILOS-POR-CARD-1009.sql; migration ranking_incluir_nomes_estilos_por_card.
Validacao: contrato publico com 33 itens; teste de Ranking aprovado; 18 combinacoes de eixo/filtro/modo aprovadas; leitura no navegador confirmou Todas e especialidade especifica sem boxes e sem transbordamento nos tres cards do podio. Advisors consultados: aviso de SECURITY DEFINER publico corresponde ao contrato publico existente; nenhum grant ampliado nesta alteracao.
Publicado no deploy 6aa2356644f065c71e259021, recursos Ranking v2026091008. index.html, ranking.js, ranking-api.js e ranking.css publicos conferidos byte a byte com o pacote.

### 10/09/2026 — Ordem visual das medidas do corpo
Altura primeiro; depois Panturrilha, Coxa, Comprimento da Perna, Cintura, Peito, Tamanho do Braco, Comprimento do Braco, Largura do Ombro, Altura do Ombro, Tamanho do Pescoco, Comprimento do Pescoco. Leitura desce a coluna esquerda e continua na direita. Nao existe medida de pe no contrato atual. Apenas ordenacao visual em renderBody, sem modificar valores ou banco. ficha.js v2026091001, deploy 6aa23b4cde18cb714deb19d7; arquivos publicos e sequencia no navegador conferidos.

### 10/09/2026 — Card inteiro abre a Ficha
Cards do Ranking agora sao links nativos completos, com card_id e linha_id preservados, abertura na mesma aba e foco visivel pelo teclado. Removido Ver Ficha. Vale para podio e compactos. Teste Ranking aprovado; arquivos publicos conferidos; clique real em Diego Maradona abriu a Ficha. Recursos Ranking v2026091009, deploy 6aa23c3170fa1764a9338376.

### 10/09/2026 — Editar Build: IA alinhada com a regra V13
Caso reproduzido: Messi 299067699633495, Centroavante Fixo/CA, tecnico 17606144688129, lowerBodyStrength=8 e demais barras zero, habilidades 26/70/22/20. A copia das entradas e dos 26 atributos estava correta. Ficha 87,83 contra editor 88,33: avaliador ainda usava IA antiga de 1,00 para cinco estilos.
Migration editor_alinhar_bonus_ia_regra_v13 altera somente a parcela de IA em build_editor.avaliar_v1 para min(quantidade,5)*0,1 conforme regra V13 aprovada. Nenhum UPDATE em builds, filas, publicacoes ou resultados salvos. Normalizacao, corpo, pe, estilos e atributos preservados.
Readback: IA=0,5; corpo=-0,5; pe=0; estilos=0; bonus_total=0; nota=87.83317896470103. Editor reaberto no navegador mostrou 87,83, igual a ficha, e os 26 atributos permaneceram identicos. Advisors consultados sem apontamento do build_editor. Correcao no servidor, sem necessidade de deploy Netlify. SQL integral: EDITOR-IA-VIGENTE-1009.sql.

### 10/09/2026 — Auditoria completa do avaliador do editor
A correcao anterior de IA era parcial. Revisados avaliar_v1, atributo_v1, apresentar_v1, chamadas salvar/gemea/listar, inicializacao e transporte do editor contra equacao.py, regua.py, motor_bonus.py, altura independente V13, ativacao de estilos V12 e normalizacao por amplitude.
Correcoes: fisico recomposto da referencia congelada, preservando as onze parcelas e seu residuo; altura aplica separar_altura_v1(true). IA conta bits distintos, 0,1 ate 0,5. Bonus total arredondado a quatro casas como writer. Pontuacao bruta usa soma incremental double e arredondamento para par, como notaDe, antes de normalizar_motor_v3. Isso elimina diferencas de 0,1 bruto observadas nas linhas 18829 e 12977. Introduzido regras_versao=editor-regras-v13-20260910-v1 para atualizar apresentacao de builds pessoais locais e remotas mesmo quando a normalizacao ja era por amplitude. Nenhum registro pessoal e sobrescrito automaticamente.
Validacao: 76 linhas cobrindo as 19 funcoes; amostra ampliada de 180 publicacoes V13 (18 funcoes disponiveis nesse recorte), todas as notas exatamente iguais. Funcao 5 coberta pela primeira amostra. Quatro casos manuais da equacao (teto, truncamento, tecnico ausente e habilidade) conferidos. Quatro testes editor-*.test.cjs aprovados. Copia do Messi 299067699633495/9126 no navegador: 87,83 nas duas telas e 26 atributos iguais.
Limites encontrados nos dados: linha 371860 ainda tinha Bonificador V12, IA 0,25 e fisico antigo; avaliador vigente usa IA 0,1 e altura retirada. Na amostra ampliada, 15 snapshots antigos do Otimizador apresentam diferencas de atributos de tecnico, embora as 180 notas coincidam; isso nao autoriza anunciar identidade de todos os atributos historicos. Nenhuma fila, motor externo, snapshot, publicacao ou build salva foi regravada nesta frente.
SQL vigente completo: EDITOR-REGRAS-VIGENTES-1009.sql; substitui o patch parcial EDITOR-IA-VIGENTE-1009.sql. Migrations editor_altura_independente_e_versao_regras_v13 e editor_arredondamento_compativel_regua_oficial. Deploy 6aa242df5dd6e17e91c55f22, ficha-editor-api.js v2026091001. HTML e JS publicos conferidos contra o pacote.

## Regra primordial — paridade entre motor e editor do site (10/09/2026)
Decisao expressa de Luis Fernando: o editor do site e o motor devem falar a mesma lingua. Esta e uma condicao obrigatoria de conclusao, nao uma melhoria opcional.
Para as mesmas entradas e a mesma versao das regras, motor e editor devem produzir os mesmos atributos, parcelas de bonus e nota final. Toda alteracao de regras deve conferir todos os consumidores: criar, editar, avaliar, salvar e reabrir builds pessoais, alem da apresentacao das builds publicadas. Preferir uma fonte canonica compartilhada; onde houver implementacoes diferentes, exigir testes de paridade antes de declarar conclusao.
A verificacao deve cobrir as especialidades e os casos afetados (barras, habilidades, tecnico, impetos e degraus, estilos, corpo/altura, pe, IA, normalizacao e arredondamento). Corrigir apenas o exemplo relatado nao encerra uma divergencia de contrato.
Se houver publicacoes historicas com regras antigas, identificar explicitamente a versao e a divergencia; nao mascarar os valores, nao chamar de paridade completa e nao regravar historicos ou filas sem autorizacao correspondente.

## Ficha lenta e a regra do estilo nos dois zagueiros, 11-12/09/2026

```text
Data: 11 e 12/09/2026
Decisao do usuario: (1) consertar a falha de carregamento da Ficha, que ficava em
  "Consultando a Ficha", devolvia 500 intermitente e demorava para trocar de
  especialidade; (2) separar Zagueiro de Combate e Zagueiro de Saida no ranking pelo
  estilo de jogo, igual ja e feito com os goleiros, MANTENDO os moldes como estao.
Escopo autorizado: banco e documentacao. Nenhum molde, alvo, peso ou regua foi tocado.
  Nenhuma build foi invalidada, nenhuma fila foi mexida, nenhum motor rodou.
Arquitetura/contrato afetado:
  public.site_novo_ficha_v2
  clube_novo.build_publicacao_exibivel_v3
  clube_novo.bonificador_regra_playstyle
Estado anterior:
  A Ficha custava 1,1 a 2,0 s por abertura e escrevia cerca de 52 MB de arquivo
  temporario no banco a cada requisicao. As duas especialidades de zagueiro tinham
  1.339 linhas e 1.013 cards cada uma, as MESMAS cartas, com correlacao de 0,985 e 97
  dos 100 primeiros em comum.
Estado novo:
  Ficha em 77 a 134 ms, zero temporario. Zagueiro de Combate com 393 linhas e 297
  cards; Zagueiro de Saida com 533 linhas e 405 cards; 6 cards nas duas listas; 317
  cards fora das duas, nenhum deles ZC nativo.
Arquivos alterados: nenhum arquivo do site. As duas entregas sao de banco, e a tela
  leu a mudanca sozinha porque ranking, busca e ficha consomem a mesma view.
Evidencia/teste: EXPLAIN ANALYZE antes e depois; 40 de 40 linhas com complemento
  devolvendo ids identicos pelos dois caminhos; 59.122 linhas nas duas views sem
  divergencia; goleiros intactos em 181 e 314; leitura no navegador mostrando 297 e
  405 nas duas abas de especialidade.
Readback: ranking por especialidade em 245 ms e 210 ms, ranking geral em 727 ms,
  ficha em 77 ms. Site publicado aberto e conferido.
Pendencias ou bloqueios: SITE-NOVO-PEND-016 a SITE-NOVO-PEND-020 no caderno.
```

### 11/09/2026 — a Ficha varria a view do ranking inteira para achar uma linha

`site_novo_ficha_v2` e apenas um involucro: ele chama
`site_novo_ficha_sem_complemento_v14`, que entrega a ficha inteira, e depois acrescenta
a marca de habilidade complementar. Cronometrado no mesmo card, a ficha inteira custava
**39 ms** e o involucro custava **1.504 ms**.

A causa: para achar o `build_otimizador_id` da linha, ele consultava
`clube_novo.build_pontuacao_final_v3_exibivel`, que e a view do ranking e tem
`row_number()` e `max() over (partition by funcao_id)`. **Funcao de janela nao deixa o
filtro descer**, entao o Postgres era obrigado a montar as 59 mil linhas inteiras,
numerar todas e descartar todas menos uma. O plano mostrava `temp written=6672`, ou
seja, cerca de 52 MB de arquivo temporario por abertura de ficha. Duas ou tres fichas
ao mesmo tempo estouravam o servidor, e era dai que vinha o **erro 500 intermitente**.

Conserto, migracao `ficha_v2_sem_varredura_da_view_de_ranking`: a consulta passou a ler
`clube_novo.build_publicacao_exibivel_v3`, que nao tem funcao de janela e aceita o filtro
pela chave. E a mesma view que o `v14` ja usa para os degraus, respeitando "uma tela, uma
porta".

```
o trecho isolado ....... 1.522 ms  ->  0,66 ms
a ficha pelo banco ..... ~1.500 ms ->  51 a 129 ms
a ficha pela internet .. 1.100 a 2.000 ms -> media 134 ms
abrir do zero .......... ~1.900 ms ->  85 ms
temporario em disco .... ~52 MB    ->  zero
```

Equivalencia provada antes de aplicar: as duas views tem as mesmas 59.122 linhas, zero
linhas com complemento presentes numa e ausentes na outra, e em 40 de 40 linhas testadas
o vetor de ids devolvido foi identico.

Medido tambem no navegador, com o `fetch` instrumentado: **um clique gera uma chamada
so**. Nao existia funcao duplicada na tela nem dois carregadores disputando a ficha; a
sensacao de "precisa clicar duas vezes" vinha do 1,5 s sem retorno visual.

**Metodo que fica:** view com `row_number()` ou `over (partition by ...)` nao serve para
buscar uma linha pela chave. E 500 intermitente quase nunca e rede; foi consulta cara
escrevendo temporario em disco.

### 12/09/2026 — a regra do estilo nos dois zagueiros

Os dois moldes de zagueiro sao o mesmo molde. Dos 26 atributos, **25 tem peso identico**;
o unico que difere e Aceleracao, peso 3 no Combate e 0 na Saida. Os alvos da Saida sao
todos um pouco mais baixos, e como a nota e
`soma(peso x valor) / soma(peso x alvo) x 100`, ela pontua mais alto sem merito: a Saida
ganha do Combate em **941 dos 1.013 cards**, 92,9%, por 3,49 pontos em media.

O **molde da Saida da peso zero a Passe rasteiro, Passe alto, Controle de bola e Conducao
firme**. Nao existe saida de bola dentro dele. Isso foi apresentado ao usuario, que
decidiu **nao mexer no molde** e resolver a mistura apenas na exibicao.

Distancia entre os moldes dos pares de cada grupo, medida em 12/09:

| grupo | atributos com peso diferente |
|---|---|
| GOLEIRO | 0 |
| ZAGUEIRO | 1 |
| Ponta, Meia de ligacao, Meia atacante, Meia lateral | 6 a 7 |
| Centroavante, Volante | 8 a 13 |
| Lateral | 15 |

Os goleiros tem molde identico, e e por isso que a regra do estilo existe para eles. O
zagueiro e o segundo caso, e o unico outro.

**A tabela da regra**, em `clube_novo.bonificador_regra_playstyle`, depois da migracao
`zagueiro_combate_ganha_cobertura_e_mestre_da_linha_alta`:

| funcao | posicao | estilos |
|---|---|---|
| 4 Goleiro Recuado | GO | 337 Goleiro Defensivo |
| 5 Goleiro Avancado | GO | 336 Goleiro Ofensivo |
| 18 Zagueiro De Combate | ZC | 329 O Destruidor, 349 Cobertura, 350 Mestre Da Linha Alta |
| 19 Zagueiro De Saida | ZC | 266 Atacante Surpresa, 271 Defensor Criativo |

O principio: quem quebra a linha e avanca sobre o portador e combate; quem recua para
receber e sair jogando e saida; estilo que organiza a defesa fica com o combate, porque o
trabalho dele e a linha e nao a bola.

**O filtro de exibicao**, migracao
`regra_do_estilo_nos_dois_zagueiros_na_view_exibivel`, entrou em
`clube_novo.build_publicacao_exibivel_v3`, que e onde a regra do goleiro ja morava:

```sql
WHERE CASE
  WHEN a.funcao_id = 4  THEN EXISTS (playstyle 337)
  WHEN a.funcao_id = 5  THEN EXISTS (playstyle 336)
  WHEN a.funcao_id = 18 THEN EXISTS (playstyle IN (329,349,350))
                          OR (NOT EXISTS (playstyle IN (329,349,350,271,266))
                              AND EXISTS (posicao principal = 1))
  WHEN a.funcao_id = 19 THEN EXISTS (playstyle IN (271,266))
  ELSE true
END
```

A carta **sem nenhum dos estilos vai para o Combate se for ZC nativo, e fica fora das
duas listas se nao for**. O Basico e o defensor generico e o Combate e exatamente isso com
alvo mais duro; na base inteira sao 5.869 zagueiros Basico contra 1.272 Destruidor, entao
o balde que recebe o Basico vira a lista gigante quando o Otimizador terminar de publicar.
Quem nao e ZC nativo e nao tem estilo de zagueiro e lateral, volante ou meia que comprou
build de ZC, e sai.

A regra **nao precisa de clausula de posicao**. Medido nas 1.013 cartas publicadas:

| | total | estilo de combate | estilo de saida | nenhum dos dois |
|---|---:|---:|---:|---:|
| zagueiro nativo | 670 | 270 | 398 | 2 |
| veio de outra posicao | 343 | 25 | 1 | 317 |

Dos 343 migrantes, 317 nao carregam estilo de zagueiro nenhum. Os 25 que carregam sao os
legitimos, o lateral ou volante com O Destruidor que realmente joga de zagueiro.

**Achado de catalogo, importante para qualquer regra futura:** `O Destruidor` e o **unico
estilo do jogo que aparece nos dois slots**, 866 cartas no ofensivo e 1.597 no defensivo,
nenhuma nos dois ao mesmo tempo. Todos os outros ficam de um lado so. Por isso a regra
pergunta "o card tem o estilo Y", e nunca "o card tem estilo no slot X".

Nenhum arquivo do site foi alterado nesta entrega. Ranking, busca e ficha leem a view, e a
separacao apareceu sozinha no site publicado: a aba ESPECIALIDADE mostra 297 em Zagueiro
De Combate e 405 em Zagueiro De Saida.

### 12/09/2026 — a trava de cardinalidade do Bonificador, quebrada e consertada

Ao acrescentar as duas linhas em `bonificador_regra_playstyle`, a tabela foi de 90 para 92
linhas. A `clube_novo.bonificador_regua_v1` tem **travas de cardinalidade escritas na
unha**, e uma delas exige exatamente 90. A regua passou a devolver `pode_rodar: false` com
a falta `bonificador_regra_playstyle: cardinalidade diferente de 90`, ou seja, **o
Bonificador ficaria impedido de rodar**.

Consertado na mesma sessao pela migracao
`bonificador_regua_cardinalidade_92_regras_de_playstyle`, que atualizou a constante da
trava e o bloco `cardinalidades` de 90 para 92. Readback: `pode_rodar: true` e
`falta_o_que` vazio, tanto em `clube_novo.bonificador_regua_v1` quanto na porta publica
`public.bonificador_regua_v2`. O mapa `casa` passou a trazer `349 -> {1:18}` e
`350 -> {1:18}`.

**Regra que fica:** toda linha inserida ou removida em `bonificador_parametro`,
`bonificador_molde_corpo`, `bonificador_posicao_slot` ou `bonificador_regra_playstyle`
exige atualizar a constante correspondente na `bonificador_regua_v1` na mesma entrega, e
conferir `pode_rodar` depois.

### 12/09/2026 — nenhuma linha precisou ser remontada

A suspeita era que as cartas com Cobertura e Mestre da Linha Alta passassem a receber
bonus novo, deixando as publicacoes defasadas. Conferido: os dois estilos **ja estavam** na
tabela, em linhas com `funcao_id` NULO, dando bonus **por posicao**; as duas linhas novas
so amarraram os estilos a funcao 18, e o valor nao mudou.

Prova: `conferir_bonus_estilo_0909_v1` rodado com a regra vigente sobre as **2.682 linhas
publicadas** das funcoes 18 e 19, com os estilos efetivos de
`carta_estilos_efetivos_v12`: 1.341 em cada funcao, **zero divergencia** entre o bonus
gravado e o recalculado.

### 12/09/2026 — carta com um estilo de cada lado aparece nas duas listas

Pergunta do usuario: e se a carta tiver estilo de combate num slot e de saida no outro? A
regra e por estilo, nao por slot, entao ela **aparece nas duas especialidades**, cada uma
com a sua build e a sua nota. Sao 6 cards hoje, todos com Defensor Criativo de um lado:

| card | um slot | outro slot |
|---|---|---|
| Paolo Maldini | Defensor Criativo | Mestre Da Linha Alta |
| Ibrahima Konate | Defensor Criativo | O Destruidor |
| Bremer | Defensor Criativo | O Destruidor |
| William Saliba | Defensor Criativo | Cobertura |
| Marc Guehi | Defensor Criativo | Mestre Da Linha Alta |
| Tomiyasu Takehiro | Defensor Criativo | Mestre Da Linha Alta |

E o comportamento correto: o jogo deu as duas instrucoes a carta, entao ela disputa os dois
oficios. Precedente registrado em 26/08 com o Konate.

### 12/09/2026 — ninguem fica de fora das duas listas de zagueiro

A primeira versao da regra do estilo deixava **fora das duas listas** o card que nao e ZC
nativo e nao tinha estilo de zagueiro: 318 cards. Isso foi apresentado ao Luis como "o
estilo separa sozinho", com base nos rotulos dos estilos (lateral ofensivo, primeiro
volante, meia versatil, orquestrador). **Os 318 nunca foram olhados pelo nome nem pela
nota.** Entre eles estavam Paolo Maldini lateral (110,92), Lilian Thuram (110,68), Giuseppe
Bergomi (109,98), Aurelien Tchouameni (108,94) e Javier Zanetti (108,40). O Luis pegou na
tela.

Decisao dele: *"o cara tem um lateral, ele pode comprar a posicao de zagueiro, e precisa
saber se ele rende mais na contencao ou saindo jogando."* Esconder isso e esconder decisao
de time. Entao **todo card com build de ZC aparece numa das duas listas**, nativo ou nao, e
o estilo decide em qual.

Os 18 estilos que aparecem em carta com build de ZC, roteados por inteiro:

| vai para o COMBATE | vai para a SAIDA |
|---|---|
| 329 O Destruidor | 271 Defensor Criativo |
| 349 Cobertura | 266 Atacante Surpresa |
| 350 Mestre Da Linha Alta | 267 Lateral Ofensivo |
| 268 Lateral Defensivo | 391 Meia Versatil |
| 392 Primeiro Volante | 276 Orquestrador |
| 348 Interceptador De Passe | 275 Perito Em Cruzamento |
| | 262 Jogador De Infiltracao |
| | 277 Lateral Atacante |
| | 259 Homem De Area |
| | 261 Classico N 10 |
| | 270 Armador Criativo |
| | 269 Atacante Pivo |

Criterio: trabalho sem bola, contencao e organizacao da linha vao para o Combate; quem sai
com a bola ou sobe para o ataque vai para a Saida. O card sem estilo nenhum vai para o
Combate se for ZC nativo.

⚠️ **As 13 linhas de roteamento entraram com `da_bonus = false`, de proposito.** A
`bonificador_regra_playstyle` faz duas coisas: `funcao_id` diz a que oficio o estilo
pertence (mapa `casa`) e `da_bonus` diz se ele ganha bonus ali (mapa `liga`). Um Lateral
Ofensivo jogando de Zagueiro de Saida deve **aparecer** na lista, mas nao deve **ganhar
ponto** por um estilo que nao e do oficio. E o problema do impostor, registrado em 26/08.

A tabela foi de 92 para 105 linhas, e a trava de cardinalidade da `bonificador_regua_v1`
foi atualizada junto, migracao `bonificador_regua_cardinalidade_105_regras_de_playstyle`.

Resultado medido: **Combate 404 cards, Saida 621, 10 nas duas, zero fora.** Goleiros
intactos em 181 e 314. Regua `pode_rodar: true` no banco e na porta publica. Bonus conferido
nas 2.682 linhas publicadas das duas funcoes, **zero divergencia**: as linhas com
`da_bonus = false` nao deram ponto a ninguem. No site no ar, a aba ESPECIALIDADE mostra 404
e 621, com Maldini, Pepe e Thuram no topo do Combate.

Migracoes: `roteamento_de_estilo_dos_zagueiros_sem_bonus`,
`bonificador_regua_cardinalidade_105_regras_de_playstyle`,
`zagueiros_ninguem_fora_roteamento_completo_por_estilo`.

**Licao de metodo que fica:** classificar por rotulo nao e medir. Antes de declarar um
grupo como ruido, olhar os nomes e as notas de quem esta dentro dele.

---

# 12/09 — OS TECNICOS ESTAVAM ERRADOS NO BANCO, E A TELA PASSOU A DIZER QUAL LINHA E VERIDICA

## O que comecou o assunto

O Luis mandou o link de um tecnico novo no efHub: Jose Mourinho ASTROS, id `17608560707469`,
impeto **Finalizacao +1 e Agressividade +1**. Ele nao existia no banco.

Ao medir o impacto, apareceu o que importava de verdade.

## Achado 1 — o tecnico nao e so o +1

`2-MOTORES/OTIMIZADOR/equacao.py`, passo 3 da Equacao 1: o tecnico entrega um
**multiplicador** lido pela **maior proficiencia** dele, e esse multiplicador age nos **26
atributos**. O boost `+1` e a segunda parte do pacote, no passo 4.

```
m = mult_de(max(proficiencias do tecnico))
x = x + TRUNCA(x * (m-1)) ; x = MIN(99, MAX(40, x))
```

Consequencia de metodo: nao se corta fila de reotimizacao por "essa funcao tem peso no
atributo do boost". O multiplicador pega todo mundo.

## Achado 2 — faltava a Sobreposicao em 1.477 tecnicos

O jogo tem **6** estilos; o banco tinha **5**. Os cinco antigos foram lidos do `Coach.bin`
numa faixa vizinha de enderecos, todos no mesmo carregamento de 28/08 02:23:18:

| estilo | bit | tecnicos |
|---|---|---|
| Passe longo | 199 | 1.478 |
| Posse de bola | 206 | 1.478 |
| Por fora | 213 | 1.478 |
| Contra-ataque rapido | 224 | 1.478 |
| Contra-ataque | 238 | 1.478 |
| **Sobreposicao** | **135** | **1** |

Sobreposicao foi lida no bit **135**, fora da faixa, num carregamento separado as 04:24:57.
So pegou o Antonio Conte, e pegou **errado**: gravou 96 onde o valor real e 69.

Esse 96 fantasma fazia do Conte o **maior multiplicador da base inteira**.

## Achado 3 — o impeto do tecnico estava errado em 57 de 64

O proprio `equacao.py` ja registrava o sintoma: *"com a ordem errada, 41 dos 62 tecnicos
recebiam o +1 no atributo errado"*. A equacao foi corrigida; **o que estava gravado no banco
nao**.

Conferencia dos 64 tecnicos que entram no Otimizador, um a um no efHub:

| conferencia | resultado |
|---|---|
| as 5 proficiencias antigas | **0 divergentes** |
| Sobreposicao ausente | 63 |
| Sobreposicao errada | 1 (Conte, 96 em vez de 69) |
| **impeto divergente** | **57** |
| multiplicador que muda ao corrigir | 1 (so o Conte, e para baixo) |

Exemplos: Conte tinha `Velocidade + Salto` e e `Talento defensivo + Forca do chute`; Tuchel
tinha `Dedicacao defensiva` e e `Resistencia`; Cruyff tinha `Drible + Desarme` e e
`Conducao firme + Salto`; Guardiola tinha `Salto` e e `Agressividade`.

Tambem caiu uma afirmacao anterior: **ja existiam tecnicos com Agressividade** — R. Martinez,
Guardiola e Klopp. O banco e que nao sabia.

## O que foi aplicado no banco

- `clube_novo.tecnico_efhub_20260912`: tabela nova com os 65 tecnicos conferidos (os 64 mais
  o Mourinho ASTROS), 6 proficiencias e 2 impetos cada. E a prova da conferencia.
- Sobreposicao carregada nos 64 e o 96 do Conte corrigido para 69.
- Impeto refeito nos 57 divergentes.
- Mourinho ASTROS cadastrado em `tecnico_jogo`, `tecnico_estilo_jogo` e
  `tecnico_atributo_jogo`.
- Tudo que entrou manualmente esta com `fonte = 'efhub_manual_20260912'` e
  `confirmado = false`. Quando o Extrator rodar, ele sobrescreve com o `Coach.bin` sem
  conflito, e da para ver na hora o que veio de onde.
- `tecnico_estilo_principal_jogo` e **view derivada**: se ajustou sozinha.

Conferencia final: 65 tecnicos, 6 estilos cada, **0 proficiencias divergentes, 0 impetos
divergentes**, gate da regua `pode_rodar: true`.

Migracoes: `tecnicos_efhub_20260912_staging_da_conferencia`,
`tecnico_mourinho_astros_cadastro_manual_efhub_v2`,
`tecnicos_proficiencias_e_boosts_corrigidos_pelo_efhub_v3`.

## O selo da regua na tela

Com os tecnicos corrigidos, **todas as 57.891 linhas publicadas viraram linha defasada**. A
decisao do Luis foi nao despublicar e sim **marcar**, para nao conviver com nota veridica e
nota falsa sem saber qual e qual.

- `clube_novo.regua_vigente_v1`: uma linha, guarda o `contrato_fingerprint` da regua que vale.
- `build_publicacao_exibivel_v3` ganhou a coluna **`regua_vigente`**, que compara o contrato
  do `build_otimizador` da linha com esse fingerprint. Nao e rotulo de versao: e a regua real.
- As tres portas publicas passaram a expor o selo:

| porta | campo |
|---|---|
| `site_novo_ranking_v1` | `itens[].regua_vigente` |
| `site_novo_busca_v1` | `itens[].regua_vigente` |
| `site_novo_ficha_v2` | `dados.build.regua_vigente` |

Na tela, quem esta com `false` recebe a etiqueta **"Regua antiga"**: `.nr-selo-antiga` no
card do Ranking, `.sn-regua-antiga` na busca do topo, `.fc-selo-antiga` ao lado da nota na
Ficha. A linha nova nao recebe nada — ausencia de etiqueta e o normal.

Arquivos tocados: `ranking.js`, `ranking.css`, `search.js`, `ficha.js`, `ficha.css`,
`site-shell.css`, e o `?v=` de todos eles em `index.html` e `ficha.html` foi para
`2026091201`.

Migracoes: `selo_regua_vigente_na_tela_1209`,
`ranking_e_busca_expoem_o_selo_regua_vigente`, `ficha_expoe_o_selo_regua_vigente`.

## A fila nova do Otimizador

Os 15 lotes antigos foram **aposentados**, nao apagados: `build_linha_card.lote_producao_id`
tem FK `ON DELETE RESTRICT`, e apagar o lote levaria junto as 317.335 linhas de build. O
registro fica em `clube_novo.otimizador_lote_aposentado_v1`.

Lote novo: **`12090000-0000-4000-8000-000000001209`**, estado `preparando`, 19.418
candidatas, com a regua corrigida selada em `regua_snapshot`.

A ordem mudou. A prioridade de lancamento saiu (nao ha carta de lancamento na base) e a
`clube_novo.otimizador_prioridade_orcamento_v1` passou a ser dois blocos:

| bloco | criterio | cartas |
|---|---|---|
| 1 | `orcamento > 0` | 12.245 |
| 2 | `orcamento = 0` (as 1/1 e 0/1) | 7.148 |

Dentro de cada bloco, **overall decrescente**. A regra foi mudada na view porque e ela que o
preparo (`otimizador_producao_preparar_fatia_v5`) e o motor consultam — assim os dois seguem
o mesmo criterio, sem funcao duplicada.

A criacao integral virou `public.otimizador_producao_criar_lote_integral_v6`: mesma coisa da
v5, com a ordem nova e com a trava trocada de "ja existe lote integral" para "ja existe lote
integral **vivo**", isto e, nao aposentado.

Migracoes: `otimizador_fila_nova_1209_orcamento_primeiro_overall_desc`,
`prioridade_da_fila_1209_orcamento_primeiro_sem_lancamento`.

## Rede de seguranca

`clube_novo.publicacao_snapshot_antes_1209` guarda as **59.714** publicacoes como estavam
antes de qualquer mexida de hoje. Migracao `snapshot_da_tela_antes_de_despublicar_1209`.

## Consertos de percurso

**O Otimizador parou com HTTP 400 e a causa fui eu.** Inserir as regras de estilo dos
zagueiros marcou o ranking de habilidades como sujo; a
`clube_novo.habilidade_incidencia_snapshot_v14()` entao tentava reconstruir e a primeira
coisa que ela faz e `delete from ... habilidade_incidencia_nativa_v14;` **sem WHERE**. O
Supabase recusa DELETE sem WHERE pela API. Ultimo 200 as 00:44, migracoes de zagueiro as
01:13, primeiro 400 as 01:23.

Conserto: `delete ... where true`. Nao muda calculo nenhum, passa na trava. Ranking
reconstruido: 886 linhas, 19 funcoes. Migracao
`incidencia_v14_delete_com_where_para_passar_no_safeupdate`.

**Fila do Bonificador destravada.** 3.654 linhas ja corrigidas estavam marcadas
`aguardando_otimizador` e o tick as repescava, batendo na guarda "Publicacao usa outra base
de bonus" uma por vez. Marcadas como concluidas. A fila foi para 57.168 concluidas, 119.138
aguardando, **zero erro**.

**Grant indevido revogado.** Ao recriar `bonificador_lote_registrar_v1` eu havia aberto
execute para `anon` e `authenticated`. Voltou a ser so `bonificador_runtime`, como a funcao
irma.


## Conferência da publicação em 13/09/2026

Site oficial: https://imaginative-granita-ace1ca.netlify.app/. Os 19 arquivos
publicados coincidem com a pasta oficial. Timeout do Ranking corrigido no banco,
calculando o selo de régua após a paginação. Ver CONFERENCIA-SITE-1309.md.
O recálculo em andamento não impede a utilização e conferência do site.
