-- Rollback da camada de consulta. Não remove nenhum dado de domínio.
drop view if exists clube_novo.catalogo_endereco_leitura_extrator_v1;
-- Restaurar a versão/fingerprint anteriores somente a partir do snapshot de contrato anterior.
