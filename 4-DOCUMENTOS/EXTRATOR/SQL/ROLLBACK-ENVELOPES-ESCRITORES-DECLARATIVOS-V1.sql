-- Rollback do contrato declarativo. Executar somente se não houver pacote aplicado que dependa destas linhas.
drop table if exists clube_novo.contrato_leitura_escritor_destino;
drop table if exists clube_novo.contrato_leitura_escritor_dominio;
-- Os três alvos corrigidos devem ser restaurados apenas com os valores registrados no snapshot anterior.
