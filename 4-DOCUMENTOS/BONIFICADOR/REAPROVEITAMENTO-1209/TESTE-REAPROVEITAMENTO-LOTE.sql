begin;
set local statement_timeout='25s';
do $$
declare refused boolean:=false; r jsonb; primeiro jsonb;
begin
 begin
  perform clube_novo.reaproveitar_bonificador_lote_fatia_v1('12090000-0000-4000-8000-000000001209',1);
 exception when others then
  if sqlerrm like '%integral preparado%' then refused:=true; else raise; end if;
 end;
 if not refused then raise exception 'lote não selado aceito'; end if;
 -- Simulação restrita a esta transação: nenhuma selagem de produção é realizada.
 update clube_novo.otimizador_lote_producao_v3 set preparo_fingerprint_final=fingerprint
 where id='12090000-0000-4000-8000-000000001209';
 r:=clube_novo.reaproveitar_bonificador_lote_fatia_v1('12090000-0000-4000-8000-000000001209',3);
 if (r->>'processadas')::integer<>3 or (r->>'reaproveitadas')::integer<>3 then
  raise exception 'primeira fatia divergente: %',r;
 end if;
 select jsonb_agg(to_jsonb(a) order by linha_id) into primeiro
 from clube_novo.bonificador_reaproveitamento_lote_v1 a;
 r:=clube_novo.reaproveitar_bonificador_lote_fatia_v1('12090000-0000-4000-8000-000000001209',3);
 if (r->>'processadas')::integer<>3 or (r->>'bloqueadas')::integer<>0
    or (select count(*) from clube_novo.bonificador_reaproveitamento_lote_v1)<>6 then
  raise exception 'retomada da fatia divergente: %',r;
 end if;
 if exists(select 1 from jsonb_array_elements(primeiro) x
   join clube_novo.bonificador_reaproveitamento_lote_v1 a on a.linha_id=(x->>'linha_id')::bigint
   where to_jsonb(a) is distinct from x) then raise exception 'primeira fatia foi reprocessada'; end if;
end $$;
select estado,count(*) from clube_novo.bonificador_reaproveitamento_lote_v1 group by estado;
rollback;
