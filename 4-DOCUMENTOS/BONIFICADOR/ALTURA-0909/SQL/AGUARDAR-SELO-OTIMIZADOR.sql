CREATE OR REPLACE FUNCTION public.correcao_altura_ia_tick_v13(p_limite integer DEFAULT 100, p_linhas bigint[] DEFAULT NULL::bigint[])
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
 SET statement_timeout TO '55s'
AS $function$
declare r record;l clube_novo.build_linha_card%rowtype;b clube_novo.build_bonificador%rowtype;
 nb clube_novo.build_bonificador%rowtype;p clube_novo.build_publicacao_linha_ativa_v1%rowtype;
 novo bigint;v_pronto boolean;f jsonb;v_erro text;ini timestamptz:=clock_timestamp();qt int:=0;
begin
 if not pg_try_advisory_xact_lock(hashtextextended('correcao-altura-ia-v13',0)) then return jsonb_build_object('ocupado',true);end if;
 if exists(select 1 from clube_novo.bonificador_correcao_lote_v1 where estado in('rodando','pausando')) then raise exception 'Pause o Bonificador completo antes da correÃ§Ã£o seletiva';end if;
 if exists(select 1 from clube_novo.correcao_altura_ia_v13 where estado='erro') then return public.correcao_altura_ia_status_v13();end if;
 for r in select * from clube_novo.correcao_altura_ia_v13 where (estado='pendente' or (estado='aguardando_otimizador' and exists(select 1 from clube_novo.build_linha_card z where z.id=linha_id and z.estado_otimizador='concluido' and z.build_otimizador_id is not null and exists(select 1 from clube_novo.build_otimizador oz where oz.id=z.build_otimizador_id and jsonb_array_length(oz.atributos_finais)=26 and jsonb_array_length(coalesce(oz.atributos_internos,oz.atributos_finais))=26 and oz.arows_snapshot is not null and oz.resultado_fingerprint=z.snapshot_otimizador_fingerprint and oz.carta_versao=z.carta_versao)))) and (p_linhas is null or linha_id=any(p_linhas)) order by era_publicada desc,linha_id limit least(greatest(p_limite,1),250) loop
  begin
   f:=null;
   select * into l from clube_novo.build_linha_card where id=r.linha_id for update;
   select exists(select 1 from clube_novo.build_otimizador ox where ox.id=l.build_otimizador_id
 and l.estado_otimizador='concluido' and ox.resultado_fingerprint=l.snapshot_otimizador_fingerprint
 and ox.carta_versao=l.carta_versao and jsonb_array_length(ox.atributos_finais)=26
 and jsonb_array_length(coalesce(ox.atributos_internos,ox.atributos_finais))=26 and ox.arows_snapshot is not null) into v_pronto;
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
    bonificador_contrato_versao=nb.contrato_versao,snapshot_bonificador_fingerprint=nb.resultado_fingerprint where id=l.id and (p.linha_id is null or v_pronto);
   if not v_pronto then f:=jsonb_build_object('estado','aguardando');end if;
   if v_pronto then
    f:=clube_novo.finalizar_publicar_linha_v1(l.id,'correcao_altura_ia_v13');
    if f->>'estado' not in('publicada','ja_publicada','aguardando') then raise exception 'FinalizaÃ§Ã£o recusada: %',f;end if;
    if f->>'estado'<>'aguardando' and p.linha_id is not null and not exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 x where x.linha_id=l.id and x.build_bonificador_id=novo and x.build_otimizador_id=l.build_otimizador_id and abs(x.nota_final-((select clube_novo.normalizar_motor_v3(l.funcao_id,o.pontuacao,(select round(sum((j->>1)::numeric)*4.68,1) from jsonb_array_elements(o.arows_snapshot) j)) from clube_novo.build_otimizador o where o.id=l.build_otimizador_id)+nb.bonus_total))<0.000001) then raise exception 'Readback da nota final falhou';end if;
   end if;
   if not exists(select 1 from clube_novo.build_linha_card x where x.id=l.id and x.build_otimizador_id is not distinct from l.build_otimizador_id and x.snapshot_otimizador_fingerprint is not distinct from l.snapshot_otimizador_fingerprint) then raise exception 'Otimizador alterado';end if;
   update clube_novo.correcao_altura_ia_v13 set estado=case when f->>'estado'='aguardando' then 'aguardando_otimizador' when p.linha_id is not null and (l.estado_otimizador<>'concluido' or l.build_otimizador_id is null) then 'aguardando_otimizador' else 'concluida' end,novo_id=novo,concluida_em=clock_timestamp(),erro=null where linha_id=l.id;
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

