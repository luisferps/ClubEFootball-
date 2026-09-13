CREATE OR REPLACE FUNCTION clube_novo.corrigir_altura_ia_resultado_v13(p_linha bigint, p_antigo bigint)
 RETURNS bigint
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare l clube_novo.build_linha_card%rowtype;b clube_novo.build_bonificador%rowtype;
 n bigint;h jsonb;ia numeric;fp text;total numeric;den numeric;novo bigint; local_result jsonb;
begin
 select * into l from clube_novo.build_linha_card where id=p_linha for update;
 select * into b from clube_novo.build_bonificador where id=p_antigo;
 if l.id is null or b.id is null then raise exception 'Linha ou resultado ausente';end if;
 if b.motor_versao='v13-1009-altura-ia-v1' then return b.id;end if;
 select novo_id into novo from clube_novo.bonificador_altura_ia_sucessor_v13 where linha_id=l.id and antigo_id=b.id;
 if novo is not null then return novo;end if;
 if not clube_novo.bonus_estilo_conforme_v12(b.id,l.card_id,l.funcao_id,l.posicao_id)
  or b.carta_fingerprint is distinct from l.carta_fingerprint
  or b.entrada_bonificador_fingerprint is distinct from l.carta_fingerprint
  or b.carta_versao is distinct from l.carta_versao or coalesce(cardinality(b.faltou),-1)<>0 then
  raise exception 'Base incompatível: identidade ou estilos não conferem';end if;
 if not (l.build_bonificador_id=b.id or exists(select 1 from clube_novo.bonificador_correcao_item_v1 i where i.build_linha_card_id=l.id and i.build_bonificador_id_novo=b.id and i.estado_item='preparado')) then
  raise exception 'Resultado não é referência vigente';end if;
 h:=clube_novo.separar_altura_v1(b.bonus_fisico_detalhe,l.funcao_id,true);
 select count(distinct bit_estilo_ia) into n from clube_novo.carta_estilo_ia_jogo where card_id=l.card_id;
 ia:=least(n,5)*0.1;
 total:=round(b.bonus_total+(h->>'delta')::numeric-b.bonus_ia+ia,4);
 select value into local_result from jsonb_array_elements(coalesce(nullif(current_setting('clube_novo.altura_ia_resultados_locais',true),''),'[]')::jsonb) where (value->>'linha_id')::bigint=l.id;
 if local_result is not null then
  if local_result->'detalhe' is distinct from h->'detalhe'
   or (local_result->>'ia')::numeric is distinct from ia
   or (local_result->>'total')::numeric is distinct from total
   or (local_result->>'fisico')::numeric is distinct from (h->>'total')::numeric
   then raise exception 'Resultado local diverge da regra de altura/IA';end if;
  h:=jsonb_set(h,'{detalhe}',local_result->'detalhe');
  h:=jsonb_set(h,'{total}',to_jsonb((local_result->>'fisico')::numeric));
  ia:=(local_result->>'ia')::numeric;total:=(local_result->>'total')::numeric;
 end if;

 select sum(2*(x->>'peso')::numeric) into den
 from clube_novo.bonificador_altura_politica_v1 p,jsonb_array_elements(p.regra->'molde_base')x
 where p.versao='altura-independente-20260909-v1' and (x->>'funcao_id')::bigint=l.funcao_id and (x->>'direcao')::int<>0;
 if den is null or den<=0 then raise exception 'Referência física congelada ausente';end if;
 fp:=encode(extensions.digest(jsonb_build_object('regra','afa495d927fe99730fa154e5d91c227e56c36c51bd048cd8881b688bc2aa126f',
 'linha',l.id,'base',b.resultado_fingerprint,'altura',h,'ia',ia)::text,'sha256'),'hex');
 insert into clube_novo.build_bonificador(bonus_pe,bonus_fisico_total,bonus_posicao,bonus_playstyle_1,bonus_playstyle_2,bonus_ia,bonus_outros,bonus_total,
 contrato_versao,contrato_fingerprint,carta_versao,carta_fingerprint,formula_fingerprint,resultado_fingerprint,concluido_em,bonus_fisico_detalhe,
 motor_versao,b_corpo,b_pe_ruim,b_estilo,b_total,faltou,corpo_soma,corpo_pct,entrada_bonificador_fingerprint)
 values(b.bonus_pe,(h->>'total')::numeric,b.bonus_posicao,b.bonus_playstyle_1,b.bonus_playstyle_2,ia,b.bonus_outros,total,
 'bonificador-altura-ia-v13','afa495d927fe99730fa154e5d91c227e56c36c51bd048cd8881b688bc2aa126f',b.carta_versao,b.carta_fingerprint,
 'afa495d927fe99730fa154e5d91c227e56c36c51bd048cd8881b688bc2aa126f',fp,clock_timestamp(),h->'detalhe',
 'v13-1009-altura-ia-v1',(h->>'total')::numeric,b.b_pe_ruim,b.b_estilo,total,b.faltou,
 (h->>'total')::numeric/1.5*den,round((h->>'total')::numeric/1.5,4),b.entrada_bonificador_fingerprint)
 on conflict(resultado_fingerprint) do nothing returning id into novo;
 if novo is null then select id into novo from clube_novo.build_bonificador where resultado_fingerprint=fp;end if;
 if not exists(select 1 from clube_novo.build_bonificador x where x.id=novo
  and x.bonus_fisico_detalhe-'altura'=b.bonus_fisico_detalhe-'altura'
  and (x.bonus_pe,x.bonus_posicao,x.bonus_playstyle_1,x.bonus_playstyle_2,x.bonus_outros) is not distinct from
      (b.bonus_pe,b.bonus_posicao,b.bonus_playstyle_1,b.bonus_playstyle_2,b.bonus_outros)
  and x.bonus_total=total and x.bonus_ia=ia) then raise exception 'Readback das parcelas falhou';end if;
 insert into clube_novo.bonificador_altura_ia_sucessor_v13 values(l.id,b.id,novo,(h->>'altura_anterior')::numeric,(h->>'altura')::numeric,b.bonus_ia,ia,clock_timestamp());
 return novo;
end $function$
;
create or replace function public.altura_ia_baixar_fila_v1(p_apos bigint default 0,p_limite integer default 500)
returns jsonb language sql stable security definer set search_path='' as $$
select jsonb_build_object('versao','altura-ia-local-v1','linhas',coalesce(jsonb_agg(to_jsonb(q) order by q.linha_id),'[]')) from (
select c.linha_id,c.antigo_id,l.card_id,l.funcao_id,b.resultado_fingerprint base_fingerprint,
b.bonus_fisico_detalhe detalhe,b.bonus_total::text bonus_total,b.bonus_ia::text ia_anterior,
(select count(*) from clube_novo.carta_estilo_ia_jogo where card_id=l.card_id) quantidade_ia
from clube_novo.correcao_altura_ia_v13 c join clube_novo.build_linha_card l on l.id=c.linha_id
join clube_novo.build_bonificador b on b.id=c.antigo_id
where c.estado='pendente' and c.linha_id>p_apos order by c.linha_id limit least(greatest(p_limite,1),1000)
)q $$;
revoke all on function public.altura_ia_baixar_fila_v1(bigint,integer) from public,anon,authenticated;
grant execute on function public.altura_ia_baixar_fila_v1(bigint,integer) to service_role;

create or replace function public.altura_ia_enviar_lote_v1(p_resultados jsonb)
returns jsonb language plpgsql security definer set search_path='' set statement_timeout='55s' as $$
declare r jsonb; ids bigint[]; estado jsonb; recibos jsonb;
begin
 if jsonb_typeof(p_resultados)<>'array' or jsonb_array_length(p_resultados) not between 1 and 100 then raise exception 'Lote deve conter entre 1 e 100 resultados';end if;
 if exists(select 1 from jsonb_array_elements(p_resultados) x group by x->>'linha_id' having count(*)>1) then raise exception 'Linha repetida no lote';end if;
 for r in select value from jsonb_array_elements(p_resultados) loop
  if r->>'versao'<>'altura-ia-local-v1' or not exists(select 1 from clube_novo.correcao_altura_ia_v13 c join clube_novo.build_bonificador b on b.id=c.antigo_id where c.linha_id=(r->>'linha_id')::bigint and c.antigo_id=(r->>'antigo_id')::bigint and b.resultado_fingerprint=r->>'base_fingerprint') then raise exception 'Identidade ou fotografia divergente';end if;
 end loop;
 select array_agg((value->>'linha_id')::bigint) into ids from jsonb_array_elements(p_resultados);
 perform set_config('clube_novo.altura_ia_resultados_locais',p_resultados::text,true);
 estado:=public.correcao_altura_ia_tick_v13(100,ids);
 select jsonb_agg(jsonb_build_object('linha_id',c.linha_id,'estado',c.estado,'novo_id',c.novo_id,'erro',c.erro) order by c.linha_id) into recibos from clube_novo.correcao_altura_ia_v13 c where c.linha_id=any(ids);
 return jsonb_build_object('versao','altura-ia-local-v1','recibos',recibos,'status',estado);
end $$;
revoke all on function public.altura_ia_enviar_lote_v1(jsonb) from public,anon,authenticated;
grant execute on function public.altura_ia_enviar_lote_v1(jsonb) to service_role;


