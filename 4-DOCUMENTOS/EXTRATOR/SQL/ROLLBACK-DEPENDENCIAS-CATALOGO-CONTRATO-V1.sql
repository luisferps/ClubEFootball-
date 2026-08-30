begin;
update clube_novo.contrato_leitura_familia set catalogos_requeridos='[]'::jsonb
where contrato_id='clubef-dt870-2026-r1';
commit;
