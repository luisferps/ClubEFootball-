begin;
drop function if exists public.otimizador_controlar_lote_teste_v1(uuid,text);
alter table clube_novo.build_linha_card
 drop column if exists lote_falha,
 drop column if exists lote_estado_atualizado_em,
 drop column if exists lote_estado;
commit;
