## Implementação principal: critérios atuais de Luis

Conferir banco, código dos aplicativos, documentação/manuais e tela em cada
etapa. A implementação integral v6 está autorizada; registros históricos de
pausa não substituem o plano atual aprovado.

Toda correção manual de dados sujeitos à extração deve ser registrada em
`clube_novo.valor_do_dono`, com chave primária completa, coluna, valor JSON e
motivo. O cadastro aplica a correção e grava histórico na mesma transação.
Não faça apenas UPDATE direto: ele não registra uma nova decisão do usuário.
O valor manual prevalece mesmo quando o jogo fornece outro valor; o Extrator
não tem autorização para remover essa proteção. Leia
`4-DOCUMENTOS/EXTRATOR/PRIORIDADE-CORRECOES-MANUAIS.md`.

## Complemento V14 — rodada encerrada em 10/09/2026

560 correcoes confirmadas no banco, todas com publicacao ativa; 524 exibiveis,
36 ocultas pela separacao aprovada de estilos de goleiro. Das 751 analisadas,
191 nao tinham candidata elegivel. Ver
`4-DOCUMENTOS/OTIMIZADOR/COMPLEMENTO-1009/ENCERRAMENTO-RODADA.md`.
Nao reabrir esta fila por confundir as 36 ocultas ou as 191 sem inclusoes
com falhas. Registros anteriores de instalacao/execucao pendentes sao historicos.

## Complemento V14 — precedencia sobre a regra historica de vagas vazias

Ler `4-DOCUMENTOS/OTIMIZADOR/COMPLEMENTO-1009/REGRA-APROVADA.md`.
Implementado no codigo e banco; frontend publicado. Maquina2 e correcao em
massa ainda dependem da instalacao/execucao do pacote. Nunca confundir os dois.
Nao excluir candidata por possuir gemea. Nao zerar artificialmente seus efeitos.
Preservar editor/busca alinhados; nao alterar normalizacao ou Bonificador.

## Encerramento do Bonificador — conferência de 10/09/2026

192.635 linhas de cartas disponíveis já possuem bonificação completa. As 12.868 sem bônus são integralmente de cartas com jogador_indisponivel=true, excluídas pela fila oficial; não criar fila de repetição nem retirar esse bloqueio por interpretar a contagem bruta como pendência. Resultados de altura/IA aguardando Otimizador já estão calculados. Ver 4-DOCUMENTOS/BONIFICADOR/ALTURA-0909/AUDITORIA-ENCERRAMENTO-BONIFICADOR.md. Encerramento limitado às cartas disponíveis atuais; novas entradas exigem nova auditoria.
> Atualização 10/09/2026: normalização vigente por amplitude: 100 + 50 × motor / (máximo teórico − mínimo teórico) + bônus. Consulte 4-DOCUMENTOS/NORMALIZACAO-0909/AMPLITUDE-VIGENTE.md; curvas anteriores são históricas.

## Altura e IA V13 — 10/09/2026

Política ativa nos writers e executor seletivo iniciado. [Contrato e operação](4-DOCUMENTOS/BONIFICADOR/ALTURA-0909/EXECUTOR-ALTURA-IA-V13.md). IA 0,1 por estilo até 0,5; altura independente em sete funções; demais parcelas preservadas. Não confundir execução iniciada com concluída.

## Altura independente — etapa estrutural 09/09/2026

Leia [4-DOCUMENTOS/BONIFICADOR/ALTURA-0909/REGRA-APROVADA.md](4-DOCUMENTOS/BONIFICADOR/ALTURA-0909/REGRA-APROVADA.md). Altura separada sem redistribuir pontos das demais medidas. Regra aprovada em sete funções, direção positiva; preparada no banco, ainda sem alterar notas. Não confundir separação neutra com recálculo aplicado. O registro V10 abaixo é a base histórica preservada.

# Decisões do projeto que devem sobreviver às sessões

## Normalização e estrelas — decisão de 09/09/2026

Antes de alterar normalização, notas ou estrelas, leia `4-DOCUMENTOS/NORMALIZACAO-0909/REGRA-APROVADA.md`. A versão oficial aprovada é `normalizacao-bonus-integral-20260909-v1`: curvas fixas por função, molde 100, teto 110, depois bônus integrais. Esta autorização posterior substitui “normalização inalterada” nos registros históricos abaixo. Não alterar motores, pesos, moldes, habilidades, atributos ou filas nesta frente. Estrelas são apenas equivalência das seis etiquetas existentes; manter labels e limites no banco. A tela só desenha o campo `estrelas`. A calibração teve exemplos de jogadores; não alegar independência nem instalar alternativa sem aprovação. Só declarar implantação após readback e Netlify após conferir o deploy.

## Enviador e critério de encerramento V12 — 09/09/2026

O critério aprovado é terminar com toda linha vigente correta e gravada em `clube_novo`, reaproveitando o que já está correto e refazendo somente o necessário. Não declarar encerramento a partir de instalação, JSON local ou ausência de linhas elegíveis de um lote. Preservar históricos, antecessores e a ordem existente. A normalização permanece inalterada.

O operador confirmou a instalação do reparo anterior `REPARO-MOTORES-V12` (backup `motores-retomada-v12-9866126a7fa84046b2e713e53878ce31`). O **novo REPARO-ENVIADOR-V12** corrige a leitura de fotografias antigas e preserva JSONs de outra fórmula sem enviá-los. Atualiza fonte e EXE com backup; mesmos BATs. 44 testes e instalador/EXE conferidos. A instalação deste novo reparo na Máquina 2 ainda não foi confirmada.

Correção de terminologia dos registros anteriores: `lotes_sem_pendentes` significa **sem linhas elegíveis na fotografia atual**, não necessariamente lote inteiro concluído. Dos 1.220 IDs antigos, 1.138 têm resultado e 82 já estão no prefixo. Os demais seis lotes têm 126.318 elegíveis esperando V12. Os 28 antecessores com bloqueios já têm substitutas V12; as seis exclusões anteriores por falta de evidência são cartas removidas, sem publicação. Não reabrir antecessores nem inventar entradas de cartas removidas.

Detalhes e limites da conferência: `4-DOCUMENTOS/OTIMIZADOR/HABILIDADES-0909/AUDITORIA-ENVIO-E-COBERTURA-V12.md`. Esta auditoria foi somente leitura; não declara que a produção ou o envio terminaram.


## Reparo de retomada HTTP 403 e encerramento — 09/09/2026

A execução na Máquina 2 expôs uma permissão ausente na consulta da carta V3, após a preparação já validada. Corrigido o acesso restrito ao catálogo no banco; HTTP e gravação testados. A única falha 488143 foi recuperada, com prioridade preservada. Bonificador agora retorna código 2 em falha e não anuncia conclusão indevida. Novo pacote único `REPARO-MOTORES-V12` inclui também a correção de prioridade do Otimizador; instalar em `2-MOTORES` por `APLICAR.cmd`, preservando os BATs anteriores. Ver `4-DOCUMENTOS/BONIFICADOR/REPARO-RETOMADA-403-V12.md`. Os registros de prontidão anteriores descrevem a conferência parcial daquela etapa.


## Reparo de prioridades concluídas — 09/09/2026

O processador aceita lotes prioritários que a fotografia declarou sem pendências, mantendo-os na seleção histórica. A execução filtra somente esses lotes já concluídos; prioridades desconhecidas/repetidas continuam bloqueadas. Fonte e EXE oficiais atualizados, 36 testes aprovados e instalador/EXE conferidos em espelho isolado. Ordem, resultados e recibos preservados. Entrega incremental `REPARO-PRIORIDADE-V12`; copiar para `OPERACAO-LOCAL-JSON` e executar `APLICAR.cmd`. Os BATs principais permanecem iguais. O pacote consolidado REFILA-V12 também incorpora o reparo. A instalação incremental na Máquina 2 ainda depende do operador. Registro: `4-DOCUMENTOS/OTIMIZADOR/HABILIDADES-0909/REPARO-PRIORITARIOS-CONCLUIDOS.md`.


## Encerramento confirmado em 09/09/2026

A correção seletiva dos bônus de estilo terminou: **67.795 resultados e 7.455 publicações concluídos, zero pendências e erros nessa operação**. O banco e o painel confirmaram o encerramento em 2026-09-09T08:13:50.106412+00:00. As nove publicações finais foram conferidas no contrato da Ficha, preservando a revisão de habilidades do Otimizador e a ordem dos lotes. A falha do UPDATE de encerramento foi corrigida no banco e no SQL oficial.

Evidência e alcance: [Conclusão dos bônus de estilo](4-DOCUMENTOS/BONIFICADOR/CONCLUSAO-BONUS-ESTILOS-0909.md). A produção geral do Bonificador e as execuções do Otimizador têm estados próprios; este encerramento não significa que seus lotes foram executados. Os registros de andamento abaixo são históricos.

## Política vigente de habilidades — 09/09/2026

Antes de trabalhar em habilidades, Otimizador, gêmeas ou sugestões da Ficha, leia `4-DOCUMENTOS/OTIMIZADOR/HABILIDADES-0909/REGRA-APROVADA.md`. A política vigente é `habilidades-funcao-20260909-v1`, no `clube_novo`. Todos os bloqueios por função filtram sugestões automáticas, inclusive gêmeas; o seletor manual permanece livre. O motor não preenche vagas sem ganho e preserva nativas. Dribles continuam permitidos para lateral ofensivo e volante de construção.

Esta frente de habilidades foi autorizada após a frente de estilos descrita abaixo. A restrição histórica de não alterar Otimizador naquela frente não impede as mudanças de habilidades aqui aprovadas. Normalização, pesos, moldes e bônus não mudam. Não corrigir ou reordenar os resultados antigos sem a etapa autorizada de revisão. Não declarar instalação na Máquina 2 ou publicação a partir de arquivos locais preparados.

Antes de trabalhar em estilos, Bonificador, notas ou extração de playstyles,
leia `4-DOCUMENTOS/BONIFICADOR/REGRA-ESTILOS-APROVADA-0909.md` e o adendo inicial
de `4-DOCUMENTOS/MANUAL-DAS-TABELAS.md`.

- A política aprovada é `estilos-funcao-20260909-v1`, persistida em
  `clube_novo.bonificador_politica_estilo`. Consulte o estado no banco antes de
  afirmar que está em produção. `aprovada_implantacao_pendente` não é implantação.
- Função define principal; posição escolhida define ativação. Principal ativo
  vale 1,0, secundário ativo 0,5. Básico/inativo valem zero. Só há duas exceções:
  Defensor Criativo e Lateral Defensivo, com o alcance definido no documento.
- Não restaurar a promoção genérica do secundário nem tratar associação com o
  molde como prova de ativação. Não reabrir a decisão por perda de contexto.
- Pressão recuada (87), Marcador forte (95), Defensor recuado (96) e Goleiro
  construtor (34) aguardam definição em extração futura. Não inventar posições
  nem interpretar ausência de definição como ativação oficialmente vazia.
- A implantação deve passar nos casos manuais de
  `4-DOCUMENTOS/BONIFICADOR/SQL/VALIDAR-POLITICA-ESTILOS-0909-V1.sql` e apresentar
  prova de que o consumidor real usa a regra. Uma calculadora de conferência
  aprovada não prova que os resultados publicados foram corrigidos.
- Alteração posterior solicitada pelo usuário exige uma nova versão e atualização
  conjunta do banco, manual, casos esperados e estado de implantação, preservando
  o histórico. As instruções atuais do usuário têm precedência.
- Nesta frente, o Otimizador, seus moldes e a ordem dos lotes permanecem intactos.
  O bloqueio de Volta para marcar no motor não restringe a escolha pessoal na Ficha.

- A correção seletiva V12 está em operação própria: leia
  `4-DOCUMENTOS/BONIFICADOR/EXECUTOR-ESTILOS-V12.md`. Manter publicações atuais
  até a substituição atômica. Não confundir produção geral bloqueada com
  executor seletivo não instalado. Só declarar término após readback do banco.

## 09/09/2026 — correcao pontual completa e refila V12

Correcao rapida de habilidades exige recompor a saida completa do Otimizador, inclusive 26 atributos sem peso, etapas, distribuicao, sugestoes e selos. Reusar o formatador oficial; nunca apenas editar IDs ou manter atributos/nota antigos. Sem prova completa, busca integral. Particao e prefixo vigentes: `4-DOCUMENTOS/OTIMIZADOR/HABILIDADES-0909/CORRECAO-PONTUAL-E-REFILA.md`. Os 28 antecessores de revisao de orcamento nao devem ser reabertos; seis linhas ainda dependem de evidencia fisica. Preservar cauda da fila, Builds antigos e publicacao ate nova confirmacao.


## Revisão das fotografias de Boxes — 09/09/2026

Autorização posterior: atualizar as avaliações congeladas para a normalização vigente, não apenas o desenho das estrelas. `clube_novo.box_avaliacao_revisao_0909` guarda nova fotografia por box/card/degrau, consumida por `site_novo_box_card_analise_snapshot_v1`; o leitor original e os 2.621 snapshots antigos permanecem preservados. Esta revisão substitui a orientação anterior de manter exclusivamente a avaliação antiga na tela.

Foram capturadas 20.094 fotografias (6.698 vínculos de cards, 1.022 boxes, três degraus), contendo 44.827 análises. Cards sem publicação elegível ficam sem avaliação; nenhuma nota foi inventada. As faixas de contratação e os motores permanecem iguais. Não há atualização contínua dessa fotografia: nova revisão exige decisão própria. Fontes: publicações exibíveis vigentes, melhor linha por função/degrau e topo global da função, como na régua de contratação existente.

Readback: zero divergências de identidade, nota, degrau ou estrelas inválidas. Cristiano Ronaldo `89138556572074`, Living Legends 2026, degrau 3: Centroavante fixo, linha 364310, nota 111,3542550014243, cinco estrelas. SQL de implantação: `4-DOCUMENTOS/NORMALIZACAO-0909/06-RENOVAR-AVALIACOES-BOXES.sql`. A correção é no banco e já é consumida pelo site publicado; não exige novo deploy nem pacote para a Máquina 2.

## Regra primordial — paridade entre motor e editor do site (10/09/2026)
Decisao expressa de Luis Fernando: o editor do site e o motor devem falar a mesma lingua. Esta e uma condicao obrigatoria de conclusao, nao uma melhoria opcional.
Para as mesmas entradas e a mesma versao das regras, motor e editor devem produzir os mesmos atributos, parcelas de bonus e nota final. Toda alteracao de regras deve conferir todos os consumidores: criar, editar, avaliar, salvar e reabrir builds pessoais, alem da apresentacao das builds publicadas. Preferir uma fonte canonica compartilhada; onde houver implementacoes diferentes, exigir testes de paridade antes de declarar conclusao.
A verificacao deve cobrir as especialidades e os casos afetados (barras, habilidades, tecnico, impetos e degraus, estilos, corpo/altura, pe, IA, normalizacao e arredondamento). Corrigir apenas o exemplo relatado nao encerra uma divergencia de contrato.
Se houver publicacoes historicas com regras antigas, identificar explicitamente a versao e a divergencia; nao mascarar os valores, nao chamar de paridade completa e nao regravar historicos ou filas sem autorizacao correspondente.


## Complemento de habilidades aprovado em 10/09/2026

Consultar `4-DOCUMENTOS/OTIMIZADOR/COMPLEMENTO-1009/REGRA-APROVADA.md` antes de
alterar o preenchimento adicional. A aprovacao substitui a proibicao absoluta
de preencher vagas sem ganho: primeiro busca original, depois incidencia nativa
>=10%, depois excecoes 69/48 por atributos de peso 7 ou 12. GEMEAS NAO EXCLUEM
candidatas no complemento; somente o mesmo ID ja presente e duplicidade.
Nao confundir decisao aprovada com implantacao: consultar progresso no documento.
