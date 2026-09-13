create or replace function clube_novo.bonificador_resultado_conforme_componentes_v1(resultado jsonb, esperado jsonb)
returns boolean language plpgsql immutable security invoker set search_path to ''
as $function$
declare k text;
begin
 if jsonb_typeof(resultado) is distinct from 'object' or jsonb_typeof(esperado) is distinct from 'object'
 or resultado->'faltou' is distinct from '[]'::jsonb then return false; end if;
 foreach k in array array['bonus_pe','bonus_fisico_total','bonus_posicao','bonus_playstyle_1','bonus_playstyle_2','bonus_ia','bonus_total'] loop
  if jsonb_typeof(resultado->k) is distinct from 'number' or jsonb_typeof(esperado->k) is distinct from 'number'
  or resultado->k is distinct from esperado->k then return false; end if;
 end loop;
 if jsonb_typeof(esperado->'bonus_fisico_detalhe') is distinct from 'object'
 or resultado->'bonus_fisico_detalhe' is distinct from esperado->'bonus_fisico_detalhe'
 or (select count(*) from jsonb_each(esperado->'bonus_fisico_detalhe'))<>12
 or exists(select 1 from jsonb_each(esperado->'bonus_fisico_detalhe') e where jsonb_typeof(e.value)<>'number')
 then return false; end if;
 if resultado->'bonus_outros' is distinct from '{}'::jsonb
 then return false; end if;
 return resultado->'b_corpo' is not distinct from esperado->'bonus_fisico_total'
 and resultado->'b_pe_ruim' is not distinct from esperado->'bonus_pe'
 and resultado->'b_total' is not distinct from esperado->'bonus_total'
 and resultado->'b_estilo' is not distinct from to_jsonb((esperado->>'bonus_playstyle_1')::numeric+(esperado->>'bonus_playstyle_2')::numeric);
end $function$;
revoke all on function clube_novo.bonificador_resultado_conforme_componentes_v1(jsonb,jsonb) from public,anon,authenticated;
comment on function clube_novo.bonificador_resultado_conforme_componentes_v1(jsonb,jsonb) is 'Compara parcelas completas sem selecionar pela versão; identidade, procedência, entradas e selos devem ser conferidos pelo vinculador.';
