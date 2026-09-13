set local lock_timeout = '5s';
set local statement_timeout = '30s';
alter table clube_novo.aplicacao_pacote_revisao_extrator drop constraint aplicacao_pacote_revisao_extrator_estado_check;
alter table clube_novo.aplicacao_pacote_revisao_extrator alter column aplicado_em drop not null;
alter table clube_novo.aplicacao_pacote_revisao_extrator add constraint aplicacao_pacote_revisao_extrator_estado_check check (estado in ('aplicando','aguardando_conferencia','aplicado'));
comment on column clube_novo.aplicacao_pacote_revisao_extrator.estado is 'Aplicando: carga retomavel em andamento ou interrompida; aguardando_conferencia: lotes gravados, sem confirmacao independente; aplicado: conferencia concluida. Historicos anteriores preservados.';
