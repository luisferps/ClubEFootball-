-- Correção V66: evento de auditoria da importação local em JSON.
--
-- V65 já grava o resultado e, na mesma transação, registra o evento
-- linha_importada_json_local. A lista permitida pela tabela de eventos ainda
-- não conhecia esse nome, o que fazia a transação inteira ser desfeita.
-- Esta migração apenas acrescenta esse evento à lista existente. Não altera
-- filas, Builds, resultados, publicação ou dados já gravados.

begin;

do $$
begin
  if to_regclass('clube_novo.otimizador_evento_producao_v3') is null then
    raise exception 'V66 recusada: tabela de eventos da produção ausente';
  end if;
end
$$;

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
    'preparo_falhou',
    'linha_importada_json_local'
  ]));

commit;
