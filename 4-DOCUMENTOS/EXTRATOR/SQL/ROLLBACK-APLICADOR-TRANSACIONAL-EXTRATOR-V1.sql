-- Rollback estrutural. Só executar se não houver auditoria de aplicação preservada.
drop table if exists clube_novo.aplicacao_pacote_revisao_extrator;
