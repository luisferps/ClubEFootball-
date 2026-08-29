-- Recuperação da migração parcial de efeitos de ímpeto.
-- Não remove as 1.542 relações originais nem altera catálogos/cartas.
begin;
set local lock_timeout = '5s';
select pg_advisory_xact_lock(hashtextextended('clube_novo:impetos_normalizados:v1', 0));

alter table clube_novo.impeto_atributo_jogo
  drop constraint if exists impeto_atributo_confirmado_ck,
  drop constraint if exists impeto_atributo_largura_delta_ck,
  drop constraint if exists impeto_atributo_bit_delta_ck,
  drop constraint if exists impeto_atributo_delta_ck,
  drop column if exists falta_o_que,
  drop column if exists confirmado,
  drop column if exists presente_dt870_atualizacao,
  drop column if exists presente_dt870_original,
  drop column if exists presente_dt200,
  drop column if exists endereco_origem,
  drop column if exists fonte_origem,
  drop column if exists registro_origem,
  drop column if exists largura_delta,
  drop column if exists bit_delta,
  drop column if exists delta;

alter table clube_novo.impeto_jogo
  drop constraint if exists impeto_jogo_condicao_estado_ck,
  drop column if exists condicao_estado;

commit;

