-- Validação somente leitura da correção física V10.
select public.bonificador_regua_v3() #> '{semantica_fisico}' as semantica_fisica;

select
  motor_versao,formula_fingerprint,contrato_versao,count(*) as resultados
from clube_novo.build_bonificador
where motor_versao='v10-0409-fisico-regra-aprovada-v1'
group by motor_versao,formula_fingerprint,contrato_versao;

select count(*) as resultados_v10_invalidos
from clube_novo.build_bonificador b
where b.motor_versao='v10-0409-fisico-regra-aprovada-v1'
  and (
    b.formula_fingerprint<>'756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
    or b.contrato_versao<>'bonificador-regua-v3'
    or jsonb_typeof(b.bonus_fisico_detalhe)<>'object'
    or (select count(*) from jsonb_each(b.bonus_fisico_detalhe))<>12
    or (select sum((e.value::text)::numeric) from jsonb_each(b.bonus_fisico_detalhe) e)
       <>b.bonus_fisico_total
    or b.bonus_fisico_total not between -1.5 and 1.5
  );

select public.bonificador_correcao_status_v1(null::uuid) as ultimo_lote;

select
  i.lote_id,i.build_linha_card_id,i.build_bonificador_id_novo,
  b.bonus_fisico_total,b.corpo_soma,b.corpo_pct,
  b.bonus_fisico_detalhe->'altura' as altura,
  (select sum((e.value::text)::numeric) from jsonb_each(b.bonus_fisico_detalhe) e)
    as soma_detalhe,
  b.motor_versao,b.formula_fingerprint
from clube_novo.bonificador_correcao_item_v1 i
join clube_novo.build_linha_card l on l.id=i.build_linha_card_id
join clube_novo.build_bonificador b on b.id=i.build_bonificador_id_novo
where l.card_id='89136409091415' and l.funcao_id=14
order by i.preparado_em desc nulls last;

select
  count(*) filter(where b.motor_versao='v10-0409-fisico-regra-aprovada-v1'
                    and b.formula_fingerprint='756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b')
    as vinculos_v10,
  count(*) filter(where b.motor_versao<>'v10-0409-fisico-regra-aprovada-v1'
                    or b.formula_fingerprint<>'756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b')
    as mistura_ativa,
  count(*) filter(where l.publicada_em is not null) as publicadas,
  count(*) filter(where l.publicada_em is not null and l.nota_final is null)
    as publicadas_sem_nota
from clube_novo.build_linha_card l
join clube_novo.build_bonificador b on b.id=l.build_bonificador_id;

