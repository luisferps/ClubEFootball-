# Site Novo — arquitetura e inventário inicial

Data da leitura: 04/09/2026  
Escopo: somente leitura, planejamento e criação deste documento dentro de `Site Novo`.  
Primeira página: **Ficha**.

## 1. Regra de reconstrução

O Site Novo será uma reconstrução independente.

Pode ser reaproveitado, após aprovação visual:

- o desenho da interface;
- a posição dos blocos;
- as relações verticais e laterais;
- a hierarquia visual;
- medidas, espaçamentos, cores e tipografia.

Não pode ser reaproveitado:

- código ou funções antigas;
- fórmulas e cálculos antigos;
- consultas antigas;
- contratos de dados antigos como arquitetura do novo site;
- componentes de dados antigos;
- regras de ranking, nota ou classificação;
- processamento, migrações ou arquitetura anterior;
- qualquer banco legado.

O banco operacional observado é somente `clube_novo`. Mesmo assim, a reconstrução não deve acoplar sua arquitetura às formas atuais: cada página precisa receber um contrato novo, explícito, versionado e validado quando o banco estiver estável.

Nenhum componente visual calculará nota, percentual, rótulo ou resultado como fallback. Ausência de dado é estado bloqueado/indisponível, não autorização para recompor informação no navegador.

## 2. Referência visual oficial e congelada da Ficha

Autoridade visual confirmada pelo usuário:

- `Site Novo/PREVIA-FICHA.html`;
- `Site Novo/PREVIA-FICHA.png`;
- origem visual rastreada: `1-SISTEMA/ficha-aprovada.css` e `4-DOCUMENTOS/FICHA-DESIGN-APROVADO-0409.html`.

Rastreio realizado:

- o próprio CSS informa que foi extraído de `4-DOCUMENTOS/FICHA-DESIGN-APROVADO-0409.html` e que suas classes usam o prefixo `fk-`;
- `1-SISTEMA/index.html` carrega esse arquivo;
- o HTML efetivo dessas classes está embutido em `1-SISTEMA/ficha-ajustes.js`;
- a renderização existente também está em `ficha-ajustes.js`.

Somente a forma visual serve de referência. O JavaScript, a renderização, os eventos, as fontes de dados e as decisões antigas não serão copiados.

### Geometria visual oficial a preservar

1. Bloco superior: identidade do jogador, pontuação total, possibilidade de melhora, estilo/posição nativos, ação de elenco e campo de posições.
2. Bloco de contexto: função selecionada, modos e faixa/lista de builds.
3. Bloco principal: distribuição/otimização/técnico à esquerda; habilidades/ímpetos/ações à direita; atributos abaixo.
4. Bloco inferior: estilos de IA, dados físicos, pé e medidas corporais.

O layout é calibrado para aproximadamente 960 px em desktop e está oficialmente congelado. Devem ser preservadas a posição, a hierarquia e a relação vertical/lateral entre todos os blocos. A evolução ocorrerá somente no conteúdo, nos dados e no comportamento novo dentro desse desenho; não haverá redesenho da grade aprovada.

### Situação da prévia

O usuário confirmou que `PREVIA-FICHA.html` e `PREVIA-FICHA.png` representam exatamente a prévia correta. O HTML permanece sem JavaScript e usa conteúdo fictício. Ele foi servido por HTTP local, conferido no navegador e registrado na PNG; o servidor e a aba temporários foram encerrados depois da validação.

## 3. Pareamento obrigatório: serviço → código → manual → contrato

| Serviço/arquivo lido | Manual específico pareado | Contrato/estado validado | Conclusão para o Site Novo |
|---|---|---|---|
| `6-AVALIADOR-NO-RAILWAY/Procfile` e `app.py` | `6-AVALIADOR-NO-RAILWAY/LEIA-ME-PRIMEIRO.md`, `4-DOCUMENTOS/MANUAL-DA-TELA.md` | O Procfile inicia `gunicorn app:app`; rotas locais: `/saude`, `/recarregar`, `/avaliar`, `/otimizar` | É inventário do serviço atual, não base reutilizável |
| `6-AVALIADOR-NO-RAILWAY/servidor.py` | `LEIA-ME-PRIMEIRO.md` | Possui `/nota` e outra `/otimizar`, mas não é importado por `app.py` nem iniciado pelo Procfile | Não há prova de que esteja ativo no deploy atual |
| `6-AVALIADOR-NO-RAILWAY/banco.py` | `4-DOCUMENTOS/OTIMIZADOR/MIGRACAO-ENTRADAS/MATRIZ-ENTRADAS-ATIVA-V3-2026-08-31.md` e trechos atuais de `4-DOCUMENTOS/MANUAL-DO-OTIMIZADOR.md` | Chama `otimizador_regua_v2`, `otimizador_carta_v3` e `otimizador_pool_habilidades_v3` com serviço privilegiado | Acesso atual é privado e específico do Otimizador; não será reutilizado na Ficha nova |
| `monta_regua.py` e `regua_do_banco.py` | `MANUAL-DO-OTIMIZADOR.md` | Esperam contrato `otimizador_regua_v2`, versão, chaves e gate | Forma antiga/currente é apenas evidência de consumo |
| `avaliador.py` e `otimizador.py` | `MANUAL-DO-OTIMIZADOR.md` e `AUDITORIA-CADEIA-SATELITES-2026-08-28.md` | Contêm cálculo e decisões de avaliação/otimização | Reuso expressamente proibido; comportamento novo exigirá especificação nova |
| `1-SISTEMA/ficha-aprovada.css`, `index.html` e `ficha-ajustes.js` | `4-DOCUMENTOS/MANUAL-DA-TELA.md` e `4-DOCUMENTOS/CONTRATO-DA-FICHA-o-que-falta-o-banco-publicar.md` | CSS/HTML confirmam a composição visual; contratos públicos atuais cobrem partes da leitura | Geometria pode ser aprovada; código e contratos não migram |

Também foram lidos `MANUAL-DAS-TABELAS.md`, `MANUAL-DE-INTERLIGACAO-DE-SISTEMAS.md` e `AUDITORIA-MOLDES-ID-2026-08-28.md` como contexto de fronteiras e deriva. Eles não substituem o pareamento específico acima.

## 4. Inventário dirigido do banco atual

Snapshot observado em 04/09/2026, aproximadamente entre 20:18 e 20:21 UTC. O banco estava sendo alterado durante a própria leitura; portanto, isto é uma fotografia transitória, não uma autoridade arquitetural.

### 4.1 Acesso privado do serviço atual

As funções abaixo existiam, estavam `STABLE`, `SECURITY DEFINER`, com `search_path` vazio, sem execução para `anon`/`authenticated` e com execução para `service_role`:

- `public.otimizador_regua_v2()`;
- `public.otimizador_carta_v3(text)`;
- `public.otimizador_pool_habilidades_v3(text, bigint)`;
- `public.otimizador_cartas_v3(jsonb)`.

Amostras devolveram gates positivos e os contratos esperados pelo serviço atual. Isso comprova o pareamento presente, mas não autoriza uso no Site Novo.

### 4.2 Leitura pública atualmente visível

Views públicas com `SELECT` para `anon`/`authenticated` e dependência de `clube_novo` observadas:

- `frontend_home_v1`;
- `frontend_busca_v1`;
- `frontend_boxes_v1`;
- `frontend_ficha_v1`;
- `frontend_ficha_build_v1`;
- `frontend_ficha_builds_v1`.

RPCs públicos de leitura observados:

- `frontend_build_estado_v2`;
- `frontend_build_publicada_v1` e `frontend_build_publicada_v2`;
- `frontend_catalogo_impetos_v1`;
- `frontend_degraus_da_linha_v1`;
- `frontend_habilidades_adicionais_v1`;
- `frontend_habilidades_do_card_v1`;
- `frontend_impetos_adicionaveis_v1`;
- `frontend_impetos_do_card_v1`.

Esses objetos são candidatos a comparação de cobertura, não contratos herdados. Duas views de Ficha/Build eram proprietárias de `postgres` e não apresentavam opção `security_invoker`; isso exige revisão de segurança e desenho antes de qualquer consumo novo.

### 4.3 Grupos privados relevantes à Ficha

Foram encontrados no schema `clube_novo`:

- identidade e cadastro: `carta_jogo` e catálogos/dimensões relacionados;
- atributos e corpo: `carta_atributo_jogo`, `carta_corpo_jogo`;
- habilidades e IA: `carta_habilidade_jogo`, `carta_estilo_ia_jogo`;
- ímpetos: `carta_impeto_jogo`;
- pé, playstyle e posições: `carta_pe_jogo`, `carta_playstyle_jogo`, `carta_posicao_jogo`, `carta_posicao_principal_jogo`;
- build no snapshot inicial: `build_linha_card`, `build_otimizador`, `build_bonificador`, a então existente `build_pontuacao_normalizada_v2` e views de pontuação final;
- contratação/box: `box_contexto_contratacao_v1`, `box_card_em_andamento_v1`, `box_card_contratacao_snapshot_v1` e relações de régua de contratação.

O inventário geral contou 101 tabelas e 8 views naquele instante.

### 4.4 Deriva confirmada durante a auditoria

- `MANUAL-DAS-TABELAS.md`, datado de 28/08, menciona 42 tabelas; o snapshot ao vivo contou 101.
- O contrato da Ficha documentava `atributos_etapas` e `pontos_por_atributo` como ausentes; a view ao vivo já possuía as duas colunas, mas a linha publicada amostrada ainda retornou `atributos_etapas = NULL`.
- O snapshot inicial revelou uma lista materializada global inconsistente. Essa rota foi removida do catálogo em 2026-09-05 após a migração de todos os leitores para o read model incremental por linha.

Consequência: nenhum nome, retorno ou disponibilidade observado aqui deve ser congelado no Site Novo antes de um checkpoint formal do banco.

### 4.5 Checkpoint posterior — Reforma A de 04/09

O registro recebido em `CHECKPOINT-REFORMA-A-2026-09-04.md` substitui o snapshot inicial somente nos pontos que ele declara:

- `build_pontuacao_normalizada_v2` deixou de existir;
- `build_linha_card` recebeu 24 colunas normais `nota_*`;
- `nota_final` passou a ser a única nota exibível, gravada pela finalizadora canônica a partir do vetor real do motor;
- banco e tela não recalculam `nota_final`;
- degraus, três views e lista pronta foram informados como leitores da linha;
- a conferência recebida foi 55.757 linhas antigas, 55.757 notas na linha e zero divergência;
- testes públicos foram informados sob teto de 3 segundos.

Trata-se de evidência recebida e datada, não de nova validação ao vivo. Como o banco continuava em mudança, a conexão futura ainda exige readback no checkpoint autorizado.

### 4.6 Segurança observada

A inspeção automática sinalizou 55 tabelas de `clube_novo` sem RLS. A validação direta, porém, mostrou que `anon` e `authenticated` não tinham `USAGE` no schema nem `SELECT` bruto em `clube_novo.carta_jogo`; o acesso público ocorria pelos objetos de `public` acima. Isso reduz a exposição direta no estado observado, mas a advertência precisa ser revalidada sempre que grants ou exposição da Data API mudarem. Nenhuma correção foi aplicada.

## 5. Arquitetura limpa proposta

```text
Site Novo
├─ shell visual fixo
│  ├─ layout e tokens aprovados
│  └─ regiões imutáveis da página
├─ paginas/ficha
│  ├─ componentes somente de apresentação
│  ├─ modelo de tela tipado
│  ├─ estados loading/vazio/bloqueado/erro/pronto
│  └─ controlador da página
├─ portas
│  ├─ FichaReadPort
│  └─ FichaActionPort (somente se ações forem autorizadas)
├─ adaptadores
│  └─ SupabaseFichaAdapter novo e versionado
└─ infraestrutura
   ├─ cliente de leitura
   ├─ identidade/sessão
   ├─ telemetria e erro
   └─ roteamento
```

Regras:

- o shell preserva apenas o visual aprovado;
- componentes recebem dados prontos e nunca consultam o banco;
- o modelo de tela não replica JSON de RPC nem linha de tabela;
- o adaptador é a única camada que conhece o contrato do banco;
- o adaptador versionado recebe `nota_final`, valida publicação/tipo e a entrega como `FichaViewModel.notaFinal`;
- a Ficha apenas renderiza `nota_final`; não soma, normaliza, recompõe nem escolhe outra coluna `nota_*`;
- degraus e listas chegam prontos pelo contrato de leitura;
- leitura e ação/escrita são portas diferentes;
- nenhuma camada recompõe pontuação, classificação ou rótulo;
- nenhum dado ausente recebe fallback calculado;
- toda resposta é validada antes de entrar na página;
- o contrato novo deve falhar fechado por versão e completude.

Nomes como `nova_plataforma_ficha_v1` e `nova_plataforma_ficha_build_v1` são apenas propostas para contratos futuros. Nada foi criado no banco.

## 6. Mapa inicial da página Ficha

| Região visual fixa | Necessidade do novo modelo de tela | Cobertura atual apenas para comparação | Pendência de produto/contrato |
|---|---|---|---|
| Identidade superior | card, nome, foto, raridade/tipo, posição/estilo nativos | `frontend_ficha_v1` cobre grande parte | definir obrigatórios, nulos e proveniência |
| Nota e melhora | `nota_final`, estado e rótulo já publicados | o checkpoint da Reforma A informa `nota_final` na linha; o contrato público definitivo ainda será escolhido | renderizar somente `nota_final`; sem publicação ou valor válido, bloquear |
| Posições | principal e lista visual pronta | Ficha atual expõe grupos relacionados | fixar ordenação e distinção nativa/adicional |
| Função e builds | função ativa e lista de builds selecionáveis | `frontend_ficha_builds_v1` e `frontend_ficha_build_v1` | decidir se a primeira versão só lê ou também edita |
| Distribuição | degraus/barras e custos já compostos | contratos atuais têm partes | definir representação nova sem herdar fórmula |
| Técnico | técnico aplicado e efeitos publicados | fontes atuais têm cobertura parcial | decidir se é dado cadastral, de build ou resultado |
| Habilidades e ímpetos | nativos/adicionais, origem, estado visual | RPCs atuais fornecem listas | ordenar, distinguir origem e fechar nulabilidade |
| Atributos | valores por etapa e finais prontos | coluna existe; completude amostral não está garantida | contrato precisa bloquear quando faltar etapa exigida |
| IA e físico | estilos IA, pé, altura/peso e corpo | `frontend_ficha_v1` cobre o cadastral | definir rótulos e unidades canônicas |
| Ações | selecionar build, otimizar, salvar ou contratar | comportamento antigo existe fora da arquitetura nova | cada ação exige regra e serviço novos, autorizados separadamente |

## 7. Sequência de implementação

### Fase 0 — aprovação visual concluída

- `PREVIA-FICHA.html` e `PREVIA-FICHA.png` foram confirmados pelo usuário como a autoridade visual exata;
- os quatro blocos, suas posições, hierarquia e relações verticais/laterais estão congelados;
- conteúdo, dados e comportamento poderão evoluir sem alterar esse desenho.

### Fase 1 — checkpoint do banco e escopo da Ficha

- registrar a Reforma A pelas cinco migrações do checkpoint de 04/09;
- primeiro recuperar/subir os números das 2.721 builds pendentes;
- confirmar o ranking novamente em 55.757;
- somente depois dessa confirmação considerar, com nova autorização, a junção de `build_otimizador` e `build_bonificador` em `build_linha_card`;
- não propor nem executar essa junção nesta fase;
- usuário informa quando a mudança de banco estiver estabilizada para o readback;
- refazer somente o inventário dirigido à Ficha;
- decidir entre Ficha cadastral, build publicado ou build editável.

### Fase 2 — esqueleto visual puro

- criar do zero HTML/CSS/componentes dentro de `Site Novo`;
- usar fixtures novas, sem consulta e sem código antigo;
- validar fidelidade visual e estados de tela.

### Fase 3 — contrato novo da página

- definir DTO da Ficha a partir das necessidades da tela;
- definir chaves, tipos, nulos, filtros, ordenação, estados e versão;
- só depois desenhar uma view/RPC nova para atendê-lo;
- qualquer mudança no banco exige autorização separada.

### Fase 4 — conexão somente leitura

- implementar adaptador novo;
- mapear exclusivamente `nota_final` para a nota exibida;
- validar versão e completude;
- falhar fechado;
- provar cada região por leitura real e readback visual.

### Fase 5 — interações, se fizerem parte do produto

- especificar cada ação do zero;
- separar avaliação/otimização/persistência da apresentação;
- definir autenticação, identidade do usuário e concorrência;
- implementar escrita somente com autorização explícita.

### Fase 6 — validação e próxima página

- testar geometria, dados, erros, autorização e desempenho;
- obter aceite da Ficha;
- repetir a sequência serviço → código → manual → contrato para a próxima página.

## 8. Decisões necessárias antes do código

1. Definir o primeiro corte funcional: Ficha cadastral, Ficha com build publicado ou Ficha editável.
2. Informar quando as 2.721 builds tiverem seus números recuperados e o ranking tiver sido reconfirmado em 55.757, formando o próximo checkpoint estável.
3. Confirmar se os contratos públicos atuais podem ser apenas fontes internas de um adaptador novo ou se a primeira entrega já exige contratos de banco inteiramente novos. Pela regra de não reuso, a recomendação é contrato novo por página desde o primeiro dia.
4. Se houver salvar/editar/contratar, definir autenticação, proprietário do estado e regra de persistência antes de qualquer ação.

## 9. Busca por JQL

Não foi encontrado arquivo, diretório nem ocorrência textual de `JQL` no escopo pesquisado do projeto e da documentação. Nenhuma consulta SQL foi tratada silenciosamente como substituta de JQL.

## 10. Declaração de não alteração

- nenhum arquivo preexistente do sistema fora de `Site Novo` foi alterado;
- nenhum código antigo foi copiado;
- nenhuma migração ou escrita de banco foi executada;
- nenhuma consulta de produção foi incorporada ao Site Novo;
- nenhum arquivo de preview foi criado fora de `Site Novo`;
- `PREVIA-FICHA.html` e `PREVIA-FICHA.png` são os únicos artefatos visuais novos desta etapa.
