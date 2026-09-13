create or replace function clube_novo.bonificador_componentes_vigentes_v1(cid text, fid bigint, pos integer)
returns jsonb language plpgsql stable security invoker set search_path to ''
as $function$
declare
 r record; par jsonb; body_detail jsonb:='{}'; body_scaled jsonb:='{}';
 body_acc numeric:=0; body_part numeric; body_last text;
 body_sum numeric:=0; body_max numeric:=0; body_bonus numeric; body_count integer:=0;
 height_result jsonb; foot_use integer; foot_precision integer; foot_bonus numeric;
 ia_bonus numeric; style_effective jsonb; style_result jsonb; style_bonus numeric;
begin
 if cid is null or fid is null or pos is null then raise exception 'Identidade de conferência incompleta'; end if;
 select jsonb_object_agg(bp.codigo,bp.valor) into par from clube_novo.bonificador_parametro bp;
 for r in select b.*,o.nosso,c.valor from clube_novo.bonificador_altura_politica_v1 policy cross join lateral jsonb_to_recordset(policy.regra->'molde_base') as b(funcao_id bigint,corpo_pos integer,peso numeric,direcao integer,corte1 numeric,corte2 numeric,corte3 numeric,corte4 numeric)
 join clube_novo.corpo_ordem o on o.pos=b.corpo_pos
 left join clube_novo.carta_corpo_jogo c on c.codigo_corpo=o.codigo and c.card_id=cid where policy.versao='altura-independente-20260909-v1' and b.funcao_id=fid order by length(o.nosso),o.nosso collate "C" loop
   body_count:=body_count+1;
   if r.valor is null or r.direcao not in (-1,0,1) or r.peso is null or r.corte1 is null or r.corte2 is null or r.corte3 is null or r.corte4 is null then raise exception 'Físico sem dados confirmados.'; end if;
   body_detail:=body_detail||jsonb_build_object(r.nosso,build_editor.faixa_corpo_v1(r.valor,r.corte1,r.corte2,r.corte3,r.corte4)*r.direcao*r.peso);
   if r.direcao<>0 then
     body_last:=r.nosso;
     body_sum:=body_sum+build_editor.faixa_corpo_v1(r.valor,r.corte1,r.corte2,r.corte3,r.corte4)*r.direcao*r.peso;
     body_max:=body_max+2*r.peso;
   end if;
 end loop;
 if body_count<>12 then raise exception 'Medidas físicas incompletas.'; end if;
 body_bonus:=case when body_max=0 then 0 else round(greatest(-1,least(1,body_sum/body_max))*(par->>'bonus_corpo_max')::numeric,4) end;
 if body_max<=0 or body_last is null then raise exception 'Referência física incompleta.'; end if;
 for r in select key,value::text::numeric points from jsonb_each(body_detail) order by length(key),key collate "C" loop
   if r.key=body_last then continue; end if;
   body_part:=round(r.points/body_max*(par->>'bonus_corpo_max')::numeric,8);
   body_acc:=body_acc+body_part;
   body_scaled:=body_scaled||jsonb_build_object(r.key,body_part);
 end loop;
 body_scaled:=body_scaled||jsonb_build_object(body_last,round(body_bonus-body_acc,8));
 height_result:=clube_novo.separar_altura_v1(body_scaled,fid,true);
 body_bonus:=(height_result->>'total')::numeric;
 select valor into foot_use from clube_novo.carta_pe_jogo where card_id=cid and campo='pe_ruim_uso';
 select valor into foot_precision from clube_novo.carta_pe_jogo where card_id=cid and campo='pe_ruim_precisao';
 foot_bonus:=round((par->>('pe_ruim_frequencia_'||foot_use))::numeric*(par->>('pe_ruim_precisao_'||foot_precision))::numeric*(par->>'pe_ruim_teto')::numeric,4);
 select round(least(count(distinct bit_estilo_ia),5)*0.1,4) into ia_bonus from clube_novo.carta_estilo_ia_jogo where card_id=cid;
 style_effective:=clube_novo.carta_estilos_efetivos_v12(cid);
 if coalesce((style_effective->>'pode_rodar')::boolean,false)=false then raise exception 'Estilos efetivos ainda não confirmados.'; end if;
 style_result:=clube_novo.conferir_bonus_estilo_0909_v1(fid,pos,(style_effective->>'ataque_id')::integer,(style_effective->>'defesa_id')::integer);
 if coalesce((style_result->>'pode_calcular')::boolean,false)=false then raise exception 'Ativação dos estilos ainda não confirmada.'; end if;
 style_bonus:=(style_result->>'bonus_total')::numeric;

 if body_bonus is null or foot_bonus is null or ia_bonus is null or style_bonus is null then raise exception 'Componente vigente sem evidência'; end if;
 return jsonb_build_object('bonus_fisico_detalhe',height_result->'detalhe',
 'bonus_fisico_total',body_bonus,'bonus_pe',foot_bonus,'bonus_ia',ia_bonus,
 'bonus_playstyle_1',style_result->'bonus_ataque','bonus_playstyle_2',style_result->'bonus_defesa',
 'bonus_posicao',0,'bonus_outros','{}'::jsonb,'bonus_total',round(body_bonus+foot_bonus+ia_bonus+style_bonus,4));
end $function$;
revoke all on function clube_novo.bonificador_componentes_vigentes_v1(text,bigint,integer) from public,anon,authenticated;
comment on function clube_novo.bonificador_componentes_vigentes_v1(text,bigint,integer) is 'Conferência somente leitura por componentes atuais, independente do rótulo de versão; espelha as operações aprovadas do editor, não grava nem processa fila.';
