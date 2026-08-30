begin;
alter table clube_novo.contrato_leitura_envelope_mapeamento drop constraint if exists contrato_leitura_envelope_mapeamento_destino_id_coluna_destino_key;
alter table clube_novo.contrato_leitura_envelope_mapeamento add column if not exists ordem_regra integer not null default 0;
alter table clube_novo.contrato_leitura_envelope_mapeamento add column if not exists grupo_repeticao text not null default 'escalar';
alter table clube_novo.contrato_leitura_envelope_mapeamento add constraint contrato_leitura_envelope_mapeamento_membro_unico unique(destino_id,coluna_destino,campo_id,ordem_regra,grupo_repeticao);
commit;
