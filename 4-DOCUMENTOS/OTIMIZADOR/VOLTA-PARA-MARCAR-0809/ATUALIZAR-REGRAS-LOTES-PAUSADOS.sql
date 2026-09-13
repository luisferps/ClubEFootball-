begin;
set local lock_timeout='5s';
set local statement_timeout='120s';
create temporary table _volta_lotes on commit drop as
select id,contrato_fingerprint antigo,regua_snapshot antes,
 jsonb_set(regua_snapshot,'{bloqueios}',(
 select jsonb_agg(jsonb_build_object('skill_id',skill,'funcao_id',funcao) order by funcao,skill)
 from (select (x->>'skill_id')::int skill,(x->>'funcao_id')::bigint funcao
       from jsonb_array_elements(regua_snapshot->'bloqueios') x
       union select 56,unnest(array[1,2,6,7,10,11,16,17,18,19]::bigint[])) b)) depois
from clube_novo.otimizador_lote_producao_v3
where id in ('1833e4d0-1707-4ea2-8ba3-3733b5101310','5c9614ce-55a2-4f9d-9ead-435e703e9058','7581b184-dccb-4a4b-9ad9-c767d4f4947c','b02cf0df-d271-4659-8e42-64a8b88b0134','c5e38fd5-877c-416e-8063-977e24d229db','ddbcbc86-1ae7-4b95-b9f0-22601f41b61d');
alter table _volta_lotes add column novo text;
update _volta_lotes set novo=clube_novo.otimizador_producao_contrato_fingerprint_v3(depois);
do $check$
begin
 perform 1 from clube_novo.otimizador_lote_producao_v3 where id in (select id from _volta_lotes) order by id for update;
 if (select count(*) from _volta_lotes)<>6 or exists(
 select 1 from clube_novo.otimizador_lote_producao_v3 l join _volta_lotes a using(id)
 where l.estado<>'pausado' or l.regua_snapshot<>a.antes or l.contrato_fingerprint<>a.antigo
 or md5(l.regua_snapshot::text)<>'dc31c0451edcce0fa31d6b77dd0e82f8'
 ) then raise exception 'Lotes mudaram ou nao estao pausados'; end if;
 if exists(select 1 from clube_novo.build_linha_card where lote_producao_id in(select id from _volta_lotes) and estado_otimizador='processando')
 then raise exception 'Ha linha em processamento'; end if;
end $check$;
update clube_novo.otimizador_lote_producao_v3 l
set regua_snapshot=a.depois,contrato_fingerprint=a.novo
from _volta_lotes a where l.id=a.id;
update clube_novo.build_linha_card l
set otimizador_contrato_fingerprint_esperado=a.novo
from _volta_lotes a
where l.lote_producao_id=a.id and l.estado_otimizador='pendente'
 and l.otimizador_contrato_fingerprint_esperado is distinct from a.novo;
select id,antigo,clube_novo.otimizador_producao_contrato_fingerprint_v3(depois) novo from _volta_lotes order by id;
commit;
