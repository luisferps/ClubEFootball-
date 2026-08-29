-- Rollback deliberado da migração de campos de apresentação de técnicos.
-- Não executar automaticamente. Falha fechado se consumidores adicionais existirem.
begin;
set local lock_timeout = '10s';
select pg_advisory_xact_lock(hashtextextended('clubef-coach-display-fields-v1', 0));
delete from clube_novo.mapa_do_jogo where assunto = any(array['tecnico.idade','tecnico.nacionalidade','tecnico.afinidade','nacionalidade.codigo','nacionalidade.nome_pt_br','nacionalidade.sigla','afinidade_tecnico.rotulo.codigo_5']);
alter table clube_novo.tecnico_jogo
  drop constraint if exists tecnico_jogo_campos_apresentacao_completos_check,
  drop constraint if exists tecnico_jogo_codigo_afinidade_fkey,
  drop constraint if exists tecnico_jogo_codigo_nacionalidade_fkey,
  drop constraint if exists tecnico_jogo_idade_check;
drop index if exists clube_novo.tecnico_jogo_codigo_afinidade_idx;
drop index if exists clube_novo.tecnico_jogo_codigo_nacionalidade_idx;
alter table clube_novo.tecnico_jogo
  drop column if exists carregado_campos_apresentacao_em,
  drop column if exists contrato_campos_apresentacao,
  drop column if exists hash_campos_apresentacao,
  drop column if exists registro_campos_apresentacao,
  drop column if exists arquivo_campos_apresentacao,
  drop column if exists cpk_campos_apresentacao,
  drop column if exists fonte_campos_apresentacao,
  drop column if exists codigo_afinidade,
  drop column if exists codigo_nacionalidade,
  drop column if exists idade;
drop table clube_novo.afinidade_tecnico_jogo restrict;
drop table clube_novo.nacionalidade_jogo restrict;
commit;
