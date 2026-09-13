# Correcoes de habilidades e refila — 09/09/2026

## Decisao e alcance

Somente `clube_novo`. A normalizacao, pesos, moldes e bonificacao nao foram alterados nesta frente. A politica vigente continua `habilidades-funcao-20260909-v1` (325 bloqueios). O editor pessoal continua livre; sugestoes automaticas respeitam todos os bloqueios, inclusive gemeas.

Correcao rapida nao e editar somente uma habilidade nem preservar apenas a pontuacao. Ela deve reconstruir a saida completa do otimizador, incluindo os 26 atributos com e sem peso, etapas base/barras/proficiencia/boost/impetos/habilidades, distribuicao/custo/sobra de pontos, tecnicos e habilidades sugeridos, quantidade de builds possiveis e os selos atuais. Usa o mesmo formatador de `roda_lote_v6.trabalha`, substituindo apenas a busca por uma solucao anterior cuja composicao foi validada. Qualquer falha de entrada, molde, orcamento, elegibilidade ou nota encaminha a linha para busca integral. O campo de comparadas registra uma solucao recomposta; os contadores da busca antiga ficam explicitamente na proveniencia, sem simular nova busca.

O importador oficial grava novo `build_otimizador` com atributos fisicos/internos e arows atuais; o finalizador normal recalcula a normalizacao vigente, soma o Bonificador compativel e troca a publicacao atomica. O anterior permanece no historico. Linha sem Bonificador confirmado continua aguardando; nao publicar incompleta. A conferencia final compara resultado, 26 atributos, barras, tecnico, impeto, adicionais, arows, nota e ponteiro publico. A ficha le o novo resultado persistido.

## Particao da auditoria

- 4.509 registros inicialmente sinalizados, dentre 57.383 resultados validos.
- 938 aptos a correcao sem busca: seis trocas completas de Arremesso lateral longo (46) por De letra (37), mais 932 retiradas sem perda da pontuacao bruta. As etapas e a nota exibida sao recompostas; nao prometer nota normalizada inalterada.
- 3.537 exigem busca integral. Incluem 110 com saida historica incompleta, 89 com opcoes de drible liberadas a revalidar e casos cuja retirada reduz o objetivo. Cruzamento preciso nao tem troca direta por Passe em profundidade: os 3.284 casos ja possuem esta ultima.
- 28 antecessores ja possuem substitutas na fila de revisao de orcamento. Nao duplicar nem reabrir os antecessores.
- 6 linhas sem orcamento fisico confirmado: 379930, 379931, 379932, 379933, 379947 e 379953. Nao ultrapassar o gate.

As seis trocas completas sao as linhas 30098 (Pavel Nedved), 367604 (Raphael Veiga), 375003/375004/375005 (Gustavo Silva) e 383825 (Park Ji-Sung), funcao Meia de arranque. A equivalencia foi conferida no vetor completo de efeitos e tipo, nao apenas nos atributos ponderados.

## Banco e fila

Migration aplicada: `20260909072123_refila_habilidades_v12_correcao_pontual_e_motor`.

Prefixo corretivo, nesta ordem:
1. `c48f3425-d717-4e30-b64a-bf10effa3148`: 4.458 registros reabertos, 936 pontuais e 3.522 buscas.
2. `3554c09c-1dbc-48e5-921a-6b45d56b2c26`: 17 registros de outros contextos de lote, dois pontuais e 15 buscas.

Os dois lotes foram criados pausados. A separacao respeita a unicidade carta/funcao/posicao/degrau por lote; nao elimina historicos duplicados. Os oito lotes anteriores e sua ordem relativa foram preservados. A cauda local tinha 126.318 linhas elegiveis; SHA-256 da ordem: `2be0f2629e0a90d6690817fb9a859b2c079687af33251f1e084fefc5428b52c8`.

Os 4.475 registros foram arquivados integralmente em eventos `arquivo_linha_antes_habilidades_0909_v12`, inclusive linha, fila, publicacao, delta e finalizacao anteriores. Nao houve exclusao dos Builds O/B antigos. As 55.151 publicacoes existentes foram preservadas na reabertura, incluindo 4.305 dos alvos. Cada nova confirmacao substitui somente a sua publicacao quando ha Bonificador compativel. O processador pesado nao foi iniciado.

## Arquivos e transferencia

`correcao_pontual_habilidades_v12.py` e o recompositor oficial em processo exclusivo, sem escrita propria no banco. O envio pontual usa o mesmo enviador e recibos da operacao local. O registro detalhado contem 46 campos na saida completa.

`renovar_pacotes_prioridade_v1.py` conserva `lotes_sem_pendentes` ao antepor correcoes; um prefixo novo nao pode reativar fotografias de lotes encerrados. O console usa UTF-8 inclusive em logs redirecionados, para nao interromper o envio de nomes como Nedved com caracteres fora de cp1252. O executavel e recompilado com os fontes oficiais; os cinco fontes da formula permanecem intactos.

Pacote consolidado novo: `ATUALIZACAO-OTIMIZADOR-REFILA-V12.zip`, substitui `ATUALIZACAO-OTIMIZADOR-HABILIDADES-V12.zip`. Copiar a pasta extraida para dentro de `2-MOTORES/OTIMIZADOR/OPERACAO-LOCAL-JSON` da Maquina 2 e executar seu `ATUALIZAR.cmd`. Faz backup, atualiza 19 arquivos, insere o prefixo uma unica vez e renova fotografias pelo banco, excluindo correcoes pontuais ja confirmadas. Preserva configuracao, resultados, recibos e ordem dos lotes antigos. Nao inicia processador/enviador. Continuam `PROCESSAR-FILA-PRINCIPAL.bat` e `ENVIAR-FILA-PRINCIPAL.bat`.

Nao confundir pacote preparado com instalacao na Maquina 2, nem resultado O confirmado com publicacao final. A transferencia remota e as publicacoes GitHub/Netlify nao foram executadas nesta etapa.

## Encerramento conferido — 938 resultados confirmados

As 938 correcoes pontuais foram gravadas pelo enviador oficial e conferidas no banco e nos recibos locais. A conferencia cobriu os 46 campos da saida, 24.388 atributos fisicos, 24.388 internos, as 938 cadeias de etapas e a distribuicao de pontos. Os 4.475 Builds O anteriores continuam preservados.

933 publicacoes foram atualizadas. As linhas 380321, 403370, 403371, 403412 e 403413 continuam aguardando Bonificador com estilos conferidos; ja nao estavam publicadas antes. O total de publicacoes permaneceu em 55.151. Nenhuma bonificacao ou normalizacao foi alterada nesta frente.

A renovacao final excluiu as 938 correcoes ja confirmadas. Restam 3.537 linhas no prefixo corretivo, antes das 126.318 linhas da cauda anterior, na mesma ordem (129.855 no total). Os dois lotes corretivos continuam pausados e nao ha linha do otimizador em processamento. O instalador da Maquina 2 repetira a consulta ao banco ao instalar, preservando a cauda daquela maquina.

Comprovantes: CORRECAO-PONTUAL-READBACK-FINAL.json, REFILA-READBACK-BANCO-FINAL.json e REFILA-FOTOGRAFIAS-FINAIS.json. A Maquina 2 ainda nao recebeu a instalacao. GitHub e Netlify nao foram publicados.


## Enviador e critério de encerramento V12 — 09/09/2026

O critério aprovado é terminar com toda linha vigente correta e gravada em `clube_novo`, reaproveitando o que já está correto e refazendo somente o necessário. Não declarar encerramento a partir de instalação, JSON local ou ausência de linhas elegíveis de um lote. Preservar históricos, antecessores e a ordem existente. A normalização permanece inalterada.

O operador confirmou a instalação do reparo anterior `REPARO-MOTORES-V12` (backup `motores-retomada-v12-9866126a7fa84046b2e713e53878ce31`). O **novo REPARO-ENVIADOR-V12** corrige a leitura de fotografias antigas e preserva JSONs de outra fórmula sem enviá-los. Atualiza fonte e EXE com backup; mesmos BATs. 44 testes e instalador/EXE conferidos. A instalação deste novo reparo na Máquina 2 ainda não foi confirmada.

Correção de terminologia dos registros anteriores: `lotes_sem_pendentes` significa **sem linhas elegíveis na fotografia atual**, não necessariamente lote inteiro concluído. Dos 1.220 IDs antigos, 1.138 têm resultado e 82 já estão no prefixo. Os demais seis lotes têm 126.318 elegíveis esperando V12. Os 28 antecessores com bloqueios já têm substitutas V12; as seis exclusões anteriores por falta de evidência são cartas removidas, sem publicação. Não reabrir antecessores nem inventar entradas de cartas removidas.

Detalhes e limites da conferência: `4-DOCUMENTOS/OTIMIZADOR/HABILIDADES-0909/AUDITORIA-ENVIO-E-COBERTURA-V12.md`. Esta auditoria foi somente leitura; não declara que a produção ou o envio terminaram.
