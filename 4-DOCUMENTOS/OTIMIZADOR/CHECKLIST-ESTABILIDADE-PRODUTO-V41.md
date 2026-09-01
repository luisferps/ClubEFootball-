# Checklist oficial — produto Otimizador V41

Data: 31/08/2026. Escopo: abertura portátil, leitura da Fila integral e ordem
operacional de apresentação. Esta entrega não autoriza iniciar worker, preparar
lote, reservar linha, publicar resultado, alterar fórmula, pesos, moldes, regras
de negócio, estados ou dados de jogo.

## Fonte e fronteira de dados

- [x] `clube_novo` continua sendo a única fonte operacional de dados do jogo;
- [x] `public` é somente a fachada de RPC protegida; não é fonte/tabela de
  cartas, builds ou fila;
- [x] V17 criou `otimizador_rotulos_cartas_fila_v1`, que lê
  `clube_novo.carta_jogo` por `card_id` e devolve apenas o rótulo necessário à
  Fila;
- [x] a ponte `otimizador_portal_local_v4` aceita o contrato V17 apenas por
  allowlist; acesso anônimo não pode chamá-lo;
- [x] o navegador continua limitado ao loopback e não recebe credencial;
- [x] função/posição usam IDs canônicos e `otimizador_rotulos_fila_v1`; nenhum
  texto legado controla cálculo ou vínculo.

## Ordem útil na tela

- [x] Fila integral: processando (se houver), depois pendentes em
  `ordem_fila` crescente, depois estados finais;
- [x] primeira página real: `246..345`, todas pendentes;
- [x] primeiro rótulo real: `52781926899717 · Gerard Moreno`;
- [x] último rótulo da página real: `52847425204350 · Kylian Mbappé`;
- [x] Resultados continua como histórico: somente finais, mais recentes primeiro;
- [x] nenhuma reordenação visual modifica prioridade, reserva ou ordem real de
  execução.

## Provas de produto executadas

- [x] `py_compile` de `interface/servidor.py` e `node --check` de
  `interface/app.js`;
- [x] `teste_interface_local_otimizador.py`: 20/20 testes verdes;
- [x] fórmula aprovada: Messi 99 -> proficiência 99 -> boost 100 -> Precisão
  104;
- [x] serviço portátil V41 em porta isolada: página completa de 100 linhas sem
  timeout; primeiras 100 em 11,527 s na leitura fria e leituras repetidas em
  2,710 s, 109 ms e 75 ms;
- [x] ícone oficial V41 em porta oficial livre: sem worker/preparador, página
  fria de 100 próximas linhas em 13,412 s sem timeout; releituras em 190 ms,
  82 ms e 45 ms;
- [x] eventos (100) em 3,367 s e Resultados (100) em 1,405 s pela instância
  aberta pelo ícone;
- [x] readback V17: nomes oficiais de Gerard Moreno e Welington Pauletto;
- [x] os serviços iniciados exclusivamente para estas provas foram encerrados
  após confirmar o caminho do executável e a porta;
- [x] nenhum worker, preparador, reserva, linha, resultado ou publicação foi
  criado ou modificado na validação.

## Recuperação e distribuição

- [x] snapshot anterior à V17:
  `4-DOCUMENTOS/OTIMIZADOR/RECUPERACAO/20260831-v41-rotulos-carta-antes/`;
- [x] migração aplicada: `MIGRACAO-ROTULOS-CARTAS-RAPIDOS-V17.sql`;
- [x] rollback correspondente: `ROLLBACK-ROTULOS-CARTAS-RAPIDOS-V17.sql`;
- [x] ponto único de abertura:
  `2-MOTORES/OTIMIZADOR/Otimizador ClubEfootball.exe`;
- [x] arquivo do ícone em versão `1.7.0.0` e mutex próprio V41: uma bandeja V40
  ociosa pode ser substituída depois da verificação segura de que não há worker;
- [x] o aviso de abertura é descartado antes de `Application.Run` manter a
  bandeja viva; ele não permanece sobre o painel já aberto;
- [x] a cópia para outro PC deve conter toda a pasta OTIMIZADOR, incluindo
  `runtime/_internal/`; o `.exe` isolado não é um pacote válido.

## Travas preservadas

- [x] fórmula: barras teto 99 -> proficiência piso/teto 40/99 -> boost técnico
  -> ímpetos;
- [x] Ímpetos condicionais continuam sujeitos aos gates existentes;
- [x] Bonificador e publicação não são acionados pelo painel;
- [x] não existe fallback para fila, build, nome ou tabela legado.
- [x] abrir o painel não retoma worker automaticamente: quando o lote está
  Rodando sem worker local, apenas o clique explícito em **Retomar worker
  local** pode reassumir as pendências.
