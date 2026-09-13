insert into clube_novo.normalizacao_regra_v3(versao,estado,parametros,parametros_fingerprint,origem)
values('normalizacao-amplitude-20260910-v1','preparada',$p${"fator": 50, "formula": "100+50*motor/(maximo-minimo)+bonus", "limites": {"1": {"amplitude": 1943.4, "maximo": 430.6, "minimo": -1512.8}, "10": {"amplitude": 1991.1, "maximo": 444.6, "minimo": -1546.5}, "11": {"amplitude": 2086.7, "maximo": 472.7, "minimo": -1614.0}, "12": {"amplitude": 2086.7, "maximo": 472.7, "minimo": -1614.0}, "13": {"amplitude": 2086.7, "maximo": 472.7, "minimo": -1614.0}, "14": {"amplitude": 2086.7, "maximo": 472.7, "minimo": -1614.0}, "15": {"amplitude": 1991.1, "maximo": 444.6, "minimo": -1546.5}, "16": {"amplitude": 2096.0, "maximo": 482.0, "minimo": -1614.0}, "17": {"amplitude": 2091.4, "maximo": 477.4, "minimo": -1614.0}, "18": {"amplitude": 1943.4, "maximo": 430.6, "minimo": -1512.8}, "19": {"amplitude": 1895.5, "maximo": 416.5, "minimo": -1479.0}, "2": {"amplitude": 1943.4, "maximo": 430.6, "minimo": -1512.8}, "3": {"amplitude": 2091.4, "maximo": 477.4, "minimo": -1614.0}, "4": {"amplitude": 1427.4, "maximo": 313.6, "minimo": -1113.8}, "5": {"amplitude": 1427.4, "maximo": 313.6, "minimo": -1113.8}, "6": {"amplitude": 1943.4, "maximo": 430.6, "minimo": -1512.8}, "7": {"amplitude": 2091.4, "maximo": 477.4, "minimo": -1614.0}, "8": {"amplitude": 2086.7, "maximo": 472.7, "minimo": -1614.0}, "9": {"amplitude": 2086.7, "maximo": 472.7, "minimo": -1614.0}}}$p$::jsonb,'75f44c56bc49ce72f826ee6f3160d9a02fb84e607085ecff29e8e48510250ffb','Amplitude teórica aprovada: cada 2% equivale a 1 ponto; molde 100; bônus integrais. Limites do comparativo aprovado.') on conflict(versao) do nothing;
create or replace function clube_novo.normalizar_motor_v3(p_funcao_id bigint,p_motor numeric,p_teto numeric)
returns numeric language plpgsql stable strict security definer set search_path='' as $$
declare lim jsonb; den numeric;
begin
 select parametros#>array['limites',p_funcao_id::text] into lim from clube_novo.normalizacao_regra_v3 where versao='normalizacao-amplitude-20260910-v1';
 if lim is null or p_teto is distinct from (lim->>'maximo')::numeric or p_motor::text in ('NaN','Infinity','-Infinity') then raise exception 'Amplitude: função, teto ou pontuação inválida';end if;
 den:=(lim->>'amplitude')::numeric;
 if den<=0 then raise exception 'Amplitude inválida';end if;
 return 100+50*p_motor/den;
end $$;
CREATE OR REPLACE FUNCTION clube_novo.normalizar_publicacao_v3(p_linha_id bigint)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
 l clube_novo.build_linha_card%rowtype;
 a clube_novo.build_publicacao_linha_ativa_v1%rowtype;
 d clube_novo.build_pontuacao_final_v2_delta_v1%rowtype;
 o clube_novo.build_otimizador%rowtype;
 b clube_novo.build_bonificador%rowtype;
 v_teto numeric;v_motor numeric;v_final numeric;v_nf text;v_cf text;v_lf text;v_pf text;
 v_normalizacao jsonb;v_prov jsonb;v_linha jsonb;v_agora timestamptz:=clock_timestamp();v_qtd integer;
begin
 -- Mesma ordem de locks da finalizaÃ§Ã£o; sÃ³ notas e seus selos sÃ£o alterados.
 select * into l from clube_novo.build_linha_card where id=p_linha_id for update;
 select * into a from clube_novo.build_publicacao_linha_ativa_v1 where linha_id=p_linha_id for update;
 if a.linha_id is null then return jsonb_build_object('estado','sem_publicacao','linha_id',p_linha_id);end if;
 select * into strict d from clube_novo.build_pontuacao_final_v2_delta_v1
 where linha_id=a.linha_id and build_otimizador_id=a.build_otimizador_id and build_bonificador_id=a.build_bonificador_id for update;
 if a.proveniencia#>>'{normalizacao,versao}'='normalizacao-amplitude-20260910-v1'
    and d.proveniencia#>>'{normalizacao,versao}'='normalizacao-amplitude-20260910-v1' and a.nota_final=d.overall_final then
   return jsonb_build_object('estado','ja_normalizada','linha_id',p_linha_id,'nota_final',a.nota_final);
 end if;
 select * into strict o from clube_novo.build_otimizador where id=a.build_otimizador_id;
 select * into strict b from clube_novo.build_bonificador where id=a.build_bonificador_id;
 if d.pontuacao_otimizador_bruta_evidencia is distinct from o.pontuacao
    or d.bonus_total_bonificador is distinct from b.bonus_total
    or d.otimizador_resultado_fingerprint is distinct from o.resultado_fingerprint
    or d.bonificador_resultado_fingerprint is distinct from b.resultado_fingerprint
    or d.arows_snapshot is distinct from o.arows_snapshot then
   raise exception 'normalizacao V3: resultados divergem da publicacao %',p_linha_id;
 end if;
 select round(sum((x->>1)::numeric)*4.68,1) into v_teto from jsonb_array_elements(o.arows_snapshot)x;
 v_motor:=clube_novo.normalizar_motor_v3(a.funcao_id,o.pontuacao,v_teto);
 v_final:=v_motor+b.bonus_total;
 v_normalizacao:=jsonb_build_object('versao','normalizacao-amplitude-20260910-v1','parametros_fingerprint','75f44c56bc49ce72f826ee6f3160d9a02fb84e607085ecff29e8e48510250ffb',
   'amplitude',(select (parametros#>>array['limites',a.funcao_id::text,'amplitude'])::numeric from clube_novo.normalizacao_regra_v3 where versao='normalizacao-amplitude-20260910-v1'),'fator',50,'motor_bruto',o.pontuacao,'teto_teorico',v_teto,'fracao_teto',o.pontuacao/v_teto,
   'motor_normalizado',v_motor,'bonus_integral',b.bonus_total,'nota_final',v_final);
 v_nf:=encode(extensions.digest(convert_to(jsonb_build_object('contrato','clube-novo-normalizacao-v3',
   'linha_id',a.linha_id,'otimizador',o.resultado_fingerprint,'bonificador',b.resultado_fingerprint,
   'publicacao_v1',a.publicacao_fingerprint,'normalizacao',v_normalizacao)::text,'UTF8'),'sha256'),'hex');
 v_cf:=encode(extensions.digest(convert_to(jsonb_build_object('contrato','clube-novo-calculo-normalizacao-v3',
   'linha_id',a.linha_id,'normalizacao',v_normalizacao,'arows_snapshot',o.arows_snapshot,
   'atributos_internos',coalesce(o.atributos_internos,o.atributos_finais))::text,'UTF8'),'sha256'),'hex');
 v_lf:=encode(extensions.digest(convert_to(jsonb_build_object('contrato','clube-novo-pontuacao-final-v2',
   'linha_id',a.linha_id,'calculo_banco_fingerprint',v_cf,'bonificador_resultado_fingerprint',b.resultado_fingerprint,
   'overall_final',v_final,'publicacao_fingerprint_v1',a.publicacao_fingerprint)::text,'UTF8'),'sha256'),'hex');
 v_pf:=encode(extensions.digest(convert_to(jsonb_build_object('contrato','clube-novo-publicacao-automatica-por-linha-v1',
   'linha_id',a.linha_id,'publicacao_linha_fingerprint_v2',v_lf)::text,'UTF8'),'sha256'),'hex');
 v_prov:=jsonb_set(d.proveniencia,'{otimizador,pontuacao_normalizada}',to_jsonb(v_motor))
   ||jsonb_build_object('normalizacao',v_normalizacao,'calculo_banco_fingerprint',v_cf,
     'pontuacao_final_oficial',v_final,'publicacao_v2',v_lf);
 if l.build_otimizador_id=a.build_otimizador_id and l.build_bonificador_id=a.build_bonificador_id
    and l.nota_otimizador_resultado_fingerprint=o.resultado_fingerprint
    and l.nota_bonificador_resultado_fingerprint=b.resultado_fingerprint then
   v_linha:=jsonb_build_object('nota_numerador',l.nota_numerador,'nota_denominador',l.nota_denominador,
     'nota_do_motor',l.nota_do_motor,'nota_final',l.nota_final,'nota_normalizacao_fingerprint',l.nota_normalizacao_fingerprint,
     'nota_calculo_fingerprint',l.nota_calculo_fingerprint,'nota_calculada_em',l.nota_calculada_em,'atualizado_em',l.atualizado_em);
 end if;
 insert into clube_novo.normalizacao_publicacao_historico_v3(regua_versao,linha_id,build_otimizador_id,build_bonificador_id,
   publicacao_anterior_fingerprint,ativa_anterior,delta_anterior,linha_nota_anterior,motor_normalizado_novo,nota_final_nova)
 values('normalizacao-amplitude-20260910-v1',a.linha_id,o.id,b.id,a.publicacao_v2_fingerprint,
   jsonb_build_object('nota_final',a.nota_final,'publicacao_v2_fingerprint',a.publicacao_v2_fingerprint,
     'proveniencia',a.proveniencia,'versao_publicacao',a.versao_publicacao,'atualizado_em',a.atualizado_em),
   jsonb_build_object('pontuacao_otimizador_normalizada',d.pontuacao_otimizador_normalizada,'overall_final',d.overall_final,
     'normalizacao_fingerprint',d.normalizacao_fingerprint,'calculo_banco_fingerprint',d.calculo_banco_fingerprint,
     'publicacao_linha_fingerprint_v2',d.publicacao_linha_fingerprint_v2,'publicacao_v2_fingerprint',d.publicacao_v2_fingerprint,
     'proveniencia',d.proveniencia),v_linha,v_motor,v_final)
 on conflict(regua_versao,linha_id,publicacao_anterior_fingerprint) do nothing;
 update clube_novo.build_pontuacao_final_v2_delta_v1 set pontuacao_otimizador_normalizada=v_motor,overall_final=v_final,
   normalizacao_fingerprint=v_nf,calculo_banco_fingerprint=v_cf,publicacao_linha_fingerprint_v2=v_lf,
   publicacao_v2_fingerprint=v_pf,proveniencia=v_prov
 where publicacao_v2_fingerprint=d.publicacao_v2_fingerprint and linha_id=a.linha_id;
 get diagnostics v_qtd=row_count;
 if v_qtd<>1 then raise exception 'normalizacao V3: delta alterado concorrentemente';end if;
 update clube_novo.build_publicacao_linha_ativa_v1 set nota_final=v_final,publicacao_v2_fingerprint=v_pf,
   proveniencia=v_prov,versao_publicacao=versao_publicacao+1,atualizado_em=v_agora where linha_id=a.linha_id;
 if v_linha is not null then
   update clube_novo.build_linha_card set nota_numerador=o.pontuacao,nota_denominador=(select (parametros#>>array['limites',a.funcao_id::text,'amplitude'])::numeric from clube_novo.normalizacao_regra_v3 where versao='normalizacao-amplitude-20260910-v1'),
    nota_do_motor=v_motor,nota_final=v_final,nota_normalizacao_fingerprint=v_nf,nota_calculo_fingerprint=v_cf,
    nota_calculada_em=v_agora where id=a.linha_id;
 end if;
 if not exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 ax
     join clube_novo.build_pontuacao_final_v2_delta_v1 dx on dx.linha_id=ax.linha_id
     and dx.publicacao_v2_fingerprint=ax.publicacao_v2_fingerprint
     where ax.linha_id=a.linha_id and ax.nota_final=v_final and dx.overall_final=v_final
       and dx.pontuacao_otimizador_normalizada=v_motor and dx.bonus_total_bonificador=b.bonus_total) then
   raise exception 'normalizacao V3: readback divergiu';
 end if;
 return jsonb_build_object('estado','normalizada','linha_id',a.linha_id,'nota_final',v_final,
   'motor_normalizado',v_motor,'bonus_integral',b.bonus_total,'normalizacao_versao','normalizacao-amplitude-20260910-v1');
end $function$
;
CREATE OR REPLACE FUNCTION clube_novo.finalizar_publicar_linha_v1(p_linha_id bigint, p_origem text DEFAULT 'desconhecida'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare r jsonb;n jsonb;v_erro text;
begin
 begin
   r:=clube_novo.finalizar_publicar_linha_antes_normalizacao_0909(p_linha_id,p_origem);
   if (r->>'ok')::boolean is true and r->>'estado' in ('publicada','ja_publicada') then
     n:=clube_novo.normalizar_publicacao_v3(p_linha_id);
     if n->>'estado' not in ('normalizada','ja_normalizada') then raise exception 'normalizacao apos publicacao falhou: %',n;end if;
     r:=r||jsonb_build_object('nota_final',n->'nota_final','normalizacao_versao','normalizacao-amplitude-20260910-v1');
   end if;
   return r;
 exception when others then
   get stacked diagnostics v_erro=message_text;
 end;
 update clube_novo.build_finalizacao_fila_v1 set estado='erro',motivo=v_erro,
   proxima_tentativa_em=clock_timestamp()+interval '10 minutes',atualizado_em=clock_timestamp() where linha_id=p_linha_id;
 insert into clube_novo.build_finalizacao_evento_v1(linha_id,evento,detalhe)
 values(p_linha_id,'falhou',jsonb_build_object('origem',p_origem,'erro',v_erro,'etapa','normalizacao_v3'));
 return jsonb_build_object('ok',false,'linha_id',p_linha_id,'estado','erro','motivo',v_erro);
end $function$
;
CREATE OR REPLACE FUNCTION public.correcao_altura_ia_tick_v13(p_limite integer DEFAULT 100, p_linhas bigint[] DEFAULT NULL::bigint[])
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
 SET statement_timeout TO '55s'
AS $function$
declare r record;l clube_novo.build_linha_card%rowtype;b clube_novo.build_bonificador%rowtype;
 nb clube_novo.build_bonificador%rowtype;p clube_novo.build_publicacao_linha_ativa_v1%rowtype;
 novo bigint;f jsonb;v_erro text;ini timestamptz:=clock_timestamp();qt int:=0;
begin
 if not pg_try_advisory_xact_lock(hashtextextended('correcao-altura-ia-v13',0)) then return jsonb_build_object('ocupado',true);end if;
 if exists(select 1 from clube_novo.bonificador_correcao_lote_v1 where estado in('rodando','pausando')) then raise exception 'Pause o Bonificador completo antes da correÃ§Ã£o seletiva';end if;
 if exists(select 1 from clube_novo.correcao_altura_ia_v13 where estado='erro') then return public.correcao_altura_ia_status_v13();end if;
 for r in select * from clube_novo.correcao_altura_ia_v13 where (estado='pendente' or (estado='aguardando_otimizador' and exists(select 1 from clube_novo.build_linha_card z where z.id=linha_id and z.estado_otimizador='concluido' and z.build_otimizador_id is not null))) and (p_linhas is null or linha_id=any(p_linhas)) order by era_publicada desc,linha_id limit least(greatest(p_limite,1),250) loop
  begin
   select * into l from clube_novo.build_linha_card where id=r.linha_id for update;
   select * into b from clube_novo.build_bonificador where id=r.antigo_id;
   select * into p from clube_novo.build_publicacao_linha_ativa_v1 where linha_id=l.id;
   if l.estado<>'pendente' or exists(select 1 from clube_novo.orcamento_revisao_linha_v1 where linha_anterior_id=l.id) then raise exception 'Linha deixou de ser vigente';end if;
   if p.linha_id is not null and p.build_bonificador_id<>b.id and not exists(select 1 from clube_novo.build_bonificador x where x.id=p.build_bonificador_id and
    (x.bonus_fisico_detalhe,x.bonus_ia,x.bonus_total,x.bonus_playstyle_1,x.bonus_playstyle_2,x.bonus_pe) is not distinct from
    (b.bonus_fisico_detalhe,b.bonus_ia,b.bonus_total,b.bonus_playstyle_1,b.bonus_playstyle_2,b.bonus_pe)) then raise exception 'PublicaÃ§Ã£o usa outra base de bÃ´nus';end if;
   novo:=clube_novo.corrigir_altura_ia_resultado_v13(l.id,b.id);
   select * into nb from clube_novo.build_bonificador where id=novo;
   update clube_novo.bonificador_correcao_item_v1 set build_bonificador_id_novo=novo where build_linha_card_id=l.id and build_bonificador_id_novo=b.id and estado_item='preparado';
   update clube_novo.build_linha_card set build_bonificador_id=novo,bonificador_motor_versao=nb.motor_versao,
    bonificador_contrato_versao=nb.contrato_versao,snapshot_bonificador_fingerprint=nb.resultado_fingerprint where id=l.id and (p.linha_id is null or (l.estado_otimizador='concluido' and l.build_otimizador_id is not null));
   if l.estado_otimizador='concluido' and l.build_otimizador_id is not null then
    f:=clube_novo.finalizar_publicar_linha_v1(l.id,'correcao_altura_ia_v13');
    if f->>'estado' not in('publicada','ja_publicada') then raise exception 'FinalizaÃ§Ã£o recusada: %',f;end if;
    if p.linha_id is not null and not exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 x where x.linha_id=l.id and x.build_bonificador_id=novo and x.build_otimizador_id=l.build_otimizador_id and abs(x.nota_final-((select clube_novo.normalizar_motor_v3(l.funcao_id,o.pontuacao,(select round(sum((j->>1)::numeric)*4.68,1) from jsonb_array_elements(o.arows_snapshot) j)) from clube_novo.build_otimizador o where o.id=l.build_otimizador_id)+nb.bonus_total))<0.000001) then raise exception 'Readback da nota final falhou';end if;
   end if;
   if not exists(select 1 from clube_novo.build_linha_card x where x.id=l.id and x.build_otimizador_id is not distinct from l.build_otimizador_id and x.snapshot_otimizador_fingerprint is not distinct from l.snapshot_otimizador_fingerprint) then raise exception 'Otimizador alterado';end if;
   update clube_novo.correcao_altura_ia_v13 set estado=case when p.linha_id is not null and (l.estado_otimizador<>'concluido' or l.build_otimizador_id is null) then 'aguardando_otimizador' else 'concluida' end,novo_id=novo,concluida_em=clock_timestamp(),erro=null where linha_id=l.id;
   qt:=qt+1;
  exception when others then
   get stacked diagnostics v_erro=message_text;
   update clube_novo.correcao_altura_ia_v13 set estado='erro',erro=v_erro where linha_id=r.linha_id;
   return public.correcao_altura_ia_status_v13();
  end;
  exit when clock_timestamp()-ini>interval '20 seconds';
 end loop;
 return public.correcao_altura_ia_status_v13()||jsonb_build_object('corrigidas_neste_lote',qt);
end $function$
;
update clube_novo.normalizacao_regra_v3 set estado='historica' where estado='vigente';update clube_novo.normalizacao_regra_v3 set estado='vigente' where versao='normalizacao-amplitude-20260910-v1';
create or replace function public.normalizacao_amplitude_status_v1()
returns jsonb language sql stable security definer set search_path='' as $$
select jsonb_build_object('preparada',true,'total',count(*),'concluidas',count(*) filter(where proveniencia#>>'{normalizacao,versao}'='normalizacao-amplitude-20260910-v1'), 'erros',0,'publicacoes_total',count(*),'publicacoes_concluidas',count(*) filter(where proveniencia#>>'{normalizacao,versao}'='normalizacao-amplitude-20260910-v1')) from clube_novo.build_publicacao_linha_ativa_v1 $$;
revoke all on function public.normalizacao_amplitude_status_v1() from public,anon,authenticated;
grant execute on function public.normalizacao_amplitude_status_v1() to service_role;
create or replace function public.normalizacao_amplitude_tick_v1(p_limite integer default 100)
returns jsonb language plpgsql security definer set search_path='' set statement_timeout='55s' as $$
declare r record; n integer:=0; ini timestamptz:=clock_timestamp();
begin
 if not pg_try_advisory_xact_lock(hashtextextended('normalizacao-amplitude-v1',0)) then return public.normalizacao_amplitude_status_v1();end if;
 for r in select a.linha_id from clube_novo.build_publicacao_linha_ativa_v1 a join clube_novo.build_linha_card l on l.id=a.linha_id
 where a.proveniencia#>>'{normalizacao,versao}' is distinct from 'normalizacao-amplitude-20260910-v1' order by a.linha_id limit least(greatest(p_limite,1),250) for update of l skip locked loop
 perform clube_novo.normalizar_publicacao_v3(r.linha_id);n:=n+1;
 exit when clock_timestamp()-ini>interval '15 seconds';
 end loop;
 return public.normalizacao_amplitude_status_v1()||jsonb_build_object('corrigidas_neste_lote',n);
end $$;
revoke all on function public.normalizacao_amplitude_tick_v1(integer) from public,anon,authenticated;
grant execute on function public.normalizacao_amplitude_tick_v1(integer) to service_role;
