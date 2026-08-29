-- Rollback da Fase 1/2, somente se nenhuma fase posterior depender destas relações.
drop function if exists clube_novo.estagiar_execucao_leitura_contrato(text,text,text,text,text,text,jsonb);
drop function if exists clube_novo.obter_pedido_leitura_contrato_ativo();
drop trigger if exists contrato_leitura_jogo_ativacao_check on clube_novo.contrato_leitura_jogo;
drop function if exists clube_novo.validar_ativacao_contrato_leitura();
drop table if exists clube_novo.contrato_leitura_cadeia;
drop table if exists clube_novo.execucao_leitura_contrato;
drop table if exists clube_novo.contrato_leitura_requisito;
drop table if exists clube_novo.contrato_leitura_campo;
drop table if exists clube_novo.contrato_leitura_arquivo;
drop table if exists clube_novo.contrato_leitura_jogo;
