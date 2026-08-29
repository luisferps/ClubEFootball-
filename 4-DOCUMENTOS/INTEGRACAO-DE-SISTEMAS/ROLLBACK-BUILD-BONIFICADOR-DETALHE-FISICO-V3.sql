begin;

alter table clube_novo.build_bonificador
  drop constraint if exists build_bonificador_bonus_fisico_detalhe_check,
  drop column if exists bonus_fisico_detalhe;

alter table clube_novo.build_bonificador
  rename column bonus_fisico_total to bonus_corpo_fisico;

commit;
