do $$
declare n integer;
begin
 update clube_novo.contrato_leitura_campo
 set transformacao=transformacao || jsonb_build_object('indice_atributo','mapa_codigo_para_indice','mapa_codigo_para_indice','{"1":0,"2":1,"3":3,"4":2,"5":4,"6":5,"7":6,"8":8,"10":7,"11":10,"12":11,"13":12,"14":21,"15":19,"16":20,"17":23,"18":24,"19":22,"20":25,"26":13}'::jsonb),
 versao_normalizador='v2-boost-tecnico-mapa-1209',
 prova='Coach.bin bit160/w5 ordem1 e bit148/w5 ordem2; codigo fisico nao e indice canonico. Mapa de 20 codigos conferido em 106/106 boosts contra tecnico_efhub_20260912; hash cb2484b8d29d4d966a22202cf463719c51c968a75f83fad05667263f4955eced. Codigos nao comprovados bloqueiam leitura.'
 where contrato_id='clubef-dt870-2026-r1' and campo_id in (302,303)
 and chave_campo in ('tecnico.boost.1','tecnico.boost.2') and transformacao->>'indice_atributo'='raw-1';
 get diagnostics n=row_count;
 if n<>2 then raise exception 'Esperados dois campos de boost antigos, recebidos %',n; end if;
end $$;
