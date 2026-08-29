begin;
drop function if exists public.otimizador_controlar_lote_teste_v2(uuid,text,boolean);
alter table clube_novo.build_linha_card drop constraint build_linha_card_estado_otimizador_check;
alter table clube_novo.build_linha_card add constraint build_linha_card_estado_otimizador_check
 check(estado_otimizador in ('pendente','processando','concluido','bloqueado'));
alter table clube_novo.build_linha_card drop constraint build_linha_card_lote_estado_check;
alter table clube_novo.build_linha_card add constraint build_linha_card_lote_estado_check
 check(lote_estado is null or lote_estado in
 ('parado','rodando','pausando','pausado','concluido','falhou'));
commit;
