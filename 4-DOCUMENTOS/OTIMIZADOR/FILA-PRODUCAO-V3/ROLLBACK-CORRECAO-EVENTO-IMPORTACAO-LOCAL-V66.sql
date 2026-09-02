-- Rollback V66.
-- Execute somente se a importação local V65 também for retirada antes.

begin;

alter table clube_novo.otimizador_evento_producao_v3
  drop constraint if exists otimizador_evento_producao_v3_evento_check;

alter table clube_novo.otimizador_evento_producao_v3
  add constraint otimizador_evento_producao_v3_evento_check
  check (evento = any (array[
    'lote_criado',
    'lote_iniciado',
    'lote_retomado',
    'pausa_solicitada',
    'lote_pausado',
    'encerramento_solicitado',
    'lote_encerrado',
    'linha_reservada',
    'linha_concluida',
    'linha_bloqueada',
    'lote_concluido',
    'lote_falhou',
    'preparo_integral_criado',
    'preparo_fatia_concluida',
    'preparo_pausa_solicitada',
    'preparo_pausado',
    'preparo_retomado',
    'preparo_integral_concluido',
    'preparo_falhou'
  ]));

commit;
