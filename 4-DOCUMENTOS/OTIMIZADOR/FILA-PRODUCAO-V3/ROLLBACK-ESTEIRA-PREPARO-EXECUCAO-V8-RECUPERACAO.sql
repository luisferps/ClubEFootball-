-- V8 só corrige a telemetria de recuperação; não há retorno à variante que
-- falhava por violar o catálogo de eventos.
begin;
select 1;
commit;
