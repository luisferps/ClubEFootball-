# Origem física das cartas e orçamento manual — 12/09/2026

## Cartas novas

O leitor tipado registra em `card_provenance` a fonte, o CPK, o arquivo Player.bin e seu SHA-256 conferido pelo contrato. O comparador usa essa origem também para cartas novas; não exige que o cadastro antigo tenha procedência preenchida. Capturas antigas sem esse objeto mantêm a validação anterior. Origem incompleta ou hash incompatível bloqueiam a comparação.

Validado com 43.635 cartas físicas e cinco testes de origem/recusa. Miura (50) e duas cartas de Buffon (48) permanecem incluídos pela correção de idade documentada separadamente. A primeira varredura 233254 antecede este ajuste de procedência: seus 187 vínculos adiados precisam de nova comparação após a aplicação.

## Prioridade manual de nível e orçamento

A vista `otimizador_prioridade_orcamento_v1`, a montagem da revisão `otimizador_preparar_revisao_orcamento_v1` e a seleção de revisões no eFHUB usam os valores efetivos de `carta_jogo`. A evidência física continua em `carta_nivel_evidencia_v1` e em `nivel_evidencia`; o pacote registra também `nivel_efetivo`. Os valores efetivos precisam ser completos e coerentes para executar o motor; uma inconsistência bloqueia a revisão, sem substituir a decisão manual.

Teste transacional com correções de level_cap/orcamento registradas em `valor_do_dono`: a vista retornou o valor manual e a evidência física não mudou. O teste foi integralmente revertido. As 19.393 cartas elegíveis com evidência existentes antes da carga mantiveram os mesmos valores. Nove testes do coletor eFHUB passaram.

## Tela de seleção

A próxima compilação usa `selecao-disponivel.json`, um resumo pequeno vinculado por SHA-256 ao arquivo completo do pacote. A seleção não precisa desserializar centenas de MB apenas para mostrar 29 opções. O worker continua validando o pacote completo, os selos e a seleção antes de aprovar/aplicar. Pacotes antigos conservam a leitura anterior. Fonte C# 5.4.0.6 compilada em validação; instalação operacional aguarda término da aplicação atual.
