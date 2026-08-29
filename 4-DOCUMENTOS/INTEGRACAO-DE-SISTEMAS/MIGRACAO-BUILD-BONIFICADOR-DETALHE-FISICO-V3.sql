begin;

alter table clube_novo.build_bonificador
  rename column bonus_corpo_fisico to bonus_fisico_total;

alter table clube_novo.build_bonificador
  add column bonus_fisico_detalhe jsonb not null default '{}'::jsonb,
  add constraint build_bonificador_bonus_fisico_detalhe_check
    check (jsonb_typeof(bonus_fisico_detalhe) = 'object');

comment on column clube_novo.build_bonificador.bonus_fisico_detalhe is
  'Snapshot chave/codigo da medida corporal -> contribuicao numerica da formula existente; nao altera pesos, ordem, molde ou calculo.';

commit;
