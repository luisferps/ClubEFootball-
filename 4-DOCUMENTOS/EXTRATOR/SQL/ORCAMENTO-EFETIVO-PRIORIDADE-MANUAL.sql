CREATE OR REPLACE FUNCTION public.otimizador_preparar_revisao_orcamento_v1(p_lote_modelo uuid, p_lote_corretivo uuid, p_linhas bigint[])
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
 v_modelo clube_novo.otimizador_lote_producao_v3%rowtype;
 v_old clube_novo.build_linha_card%rowtype;
 v_s clube_novo.otimizador_lote_producao_carta_v3%rowtype;
 v_e clube_novo.carta_nivel_evidencia_v1%rowtype;
 v_c clube_novo.carta_jogo%rowtype;
 v_id bigint; v_new bigint; v_ordem bigint; v_entrada jsonb; v_fp text;
 v_bonificador jsonb; v_total integer:=0; v_ja integer:=0; v_pub jsonb; v_cards integer;
begin
 if p_lote_modelo is null or p_lote_corretivo is null or p_lote_modelo=p_lote_corretivo
    or coalesce(cardinality(p_linhas),0) not between 1 and 500
    or cardinality(p_linhas)<>(select count(distinct x) from unnest(p_linhas) x)
 then raise exception 'Revisão recusada: argumentos inválidos ou IDs repetidos'; end if;
 perform pg_advisory_xact_lock(hashtext('revisao_orcamento:'||p_lote_corretivo::text));
 select * into v_modelo from clube_novo.otimizador_lote_producao_v3 where id=p_lote_modelo for share;
 if not found or v_modelo.estado<>'pausado' or v_modelo.pode_publicar is distinct from false
 then raise exception 'Revisão recusada: lote modelo não está pausado'; end if;
 if exists(select 1 from clube_novo.build_linha_card where lote_producao_id in(p_lote_modelo,p_lote_corretivo) and estado_otimizador='processando')
 then raise exception 'Revisão recusada: há reserva ativa'; end if;
 insert into clube_novo.otimizador_lote_producao_v3(
   id,tipo_lote,estado,formula_fingerprint,contrato_fingerprint,motor_versao,regua_snapshot,fingerprint,
   cards,linhas,preparo_total,preparo_concluido,pode_publicar)
 values(p_lote_corretivo,'integral','pausado',v_modelo.formula_fingerprint,v_modelo.contrato_fingerprint,
   v_modelo.motor_versao,v_modelo.regua_snapshot,
   encode(extensions.digest(convert_to('revisao_orcamento_v1:'||p_lote_corretivo::text,'UTF8'),'sha256'),'hex'),0,0,0,0,false)
 on conflict(id) do nothing;
 perform 1 from clube_novo.otimizador_lote_producao_v3 where id=p_lote_corretivo and estado='pausado'
   and formula_fingerprint=v_modelo.formula_fingerprint and contrato_fingerprint=v_modelo.contrato_fingerprint
   and motor_versao=v_modelo.motor_versao and pode_publicar=false for update;
 if not found then raise exception 'Revisão recusada: lote corretivo incompatível'; end if;
 select coalesce(max(ordem_fila),0) into v_ordem from clube_novo.otimizador_lote_producao_linha_v3 where lote_id=p_lote_corretivo;
 foreach v_id in array p_linhas loop
   if exists(select 1 from clube_novo.orcamento_revisao_linha_v1 where linha_anterior_id=v_id) then
     if not exists(select 1 from clube_novo.orcamento_revisao_linha_v1
       where linha_anterior_id=v_id and lote_corretivo_id=p_lote_corretivo and linha_nova_id is not null)
     then raise exception 'Revisão % já pertence a outro lote ou está incompleta',v_id; end if;
     v_ja:=v_ja+1; continue;
   end if;
   select * into v_old from clube_novo.build_linha_card where id=v_id for update;
   if not found or v_old.execucao_tipo<>'producao' or v_old.estado='invalida' or v_old.estado_otimizador='processando'
   then raise exception 'Linha % não pode ser revisada',v_id; end if;
   select * into v_s from clube_novo.otimizador_lote_producao_carta_v3
     where lote_id=v_old.lote_producao_id and card_id=v_old.card_id;
   if not found then raise exception 'Linha % sem entrada histórica',v_id; end if;
   select * into v_e from clube_novo.carta_nivel_evidencia_v1 where card_id=v_old.card_id;
   if not found or v_e.nivel_maximo<1 or v_e.orcamento_real<>2*(v_e.nivel_maximo-1)
   then raise exception 'Linha % sem evidência física íntegra',v_id; end if;
   select * into v_c from clube_novo.carta_jogo where card_id=v_old.card_id for share;
   if not found or v_c.level_cap is null or v_c.level_cap<1 or v_c.orcamento is null
      or v_c.orcamento<>2*(v_c.level_cap-1) or v_c.cap_estimado is distinct from false
      or v_c.orcamento is not distinct from (v_s.entrada_otimizador#>>'{escalares,orcamento}')::integer
   then raise exception 'Linha % sem divergência válida nos valores efetivos',v_id; end if;
   if not exists(select 1 from clube_novo.otimizador_prioridade_orcamento_v1 where card_id=v_old.card_id and prioridade_grupo is not null)
   then raise exception 'Linha % sem tipo físico reconhecido',v_id; end if;
   if exists(select 1 from clube_novo.otimizador_lote_producao_linha_v3 where linha_id=v_id and reserva_token is not null and finalizada_em is null)
   then raise exception 'Linha % possui reserva ativa',v_id; end if;
   v_entrada:=jsonb_set(v_s.entrada_otimizador,'{escalares}',(v_s.entrada_otimizador->'escalares')||
     jsonb_build_object('level_cap',v_c.level_cap,'orcamento',v_c.orcamento,'cap_estimado',v_c.cap_estimado),false)||
     jsonb_build_object('nivel_evidencia',jsonb_build_object('contrato_id',v_e.contrato_id,'fonte',v_e.fonte,
       'captura_id',v_e.captura_id,'nivel_maximo',v_e.nivel_maximo,'orcamento_real',v_e.orcamento_real,'comprovado_em',v_e.comprovado_em),
       'nivel_efetivo',jsonb_build_object('level_cap',v_c.level_cap,'orcamento',v_c.orcamento,'cap_estimado',v_c.cap_estimado,'origem','carta_jogo_com_prioridade_manual'));
   v_fp:=encode(extensions.digest(convert_to(v_entrada::text,'UTF8'),'sha256'),'hex');
   v_bonificador:=public.bonificador_carta_v2(v_old.card_id);
   if not coalesce((v_bonificador->>'pode_rodar')::boolean,false)
      or nullif(v_bonificador->>'carta_versao','') is null or nullif(v_bonificador->>'carta_fingerprint','') is null
   then raise exception 'Linha % sem entrada compatível do Bonificador',v_id; end if;
   insert into clube_novo.otimizador_lote_producao_carta_v3(
      lote_id,card_id,overall_snapshot,entrada_otimizador,entrada_contrato,entrada_fingerprint,
      carta_versao_bonificador,carta_fingerprint_bonificador)
   values(p_lote_corretivo,v_old.card_id,(select overall from clube_novo.carta_jogo where card_id=v_old.card_id),
      v_entrada,v_s.entrada_contrato,v_fp,v_bonificador->>'carta_versao',v_bonificador->>'carta_fingerprint')
   on conflict(lote_id,card_id) do nothing;
   if not exists(select 1 from clube_novo.otimizador_lote_producao_carta_v3 where lote_id=p_lote_corretivo
     and card_id=v_old.card_id and entrada_fingerprint=v_fp
     and carta_fingerprint_bonificador=v_bonificador->>'carta_fingerprint')
   then raise exception 'Card % tem entradas históricas diferentes; separar revisão por versão',v_old.card_id; end if;
   select to_jsonb(a) into v_pub from clube_novo.build_publicacao_linha_ativa_v1 a where linha_id=v_id;
   insert into clube_novo.orcamento_revisao_linha_v1(
      linha_anterior_id,lote_corretivo_id,orcamento_anterior,orcamento_real,captura_id,motivo,
      linha_anterior_snapshot,publicacao_anterior_snapshot,entrada_anterior_snapshot)
   values(v_id,p_lote_corretivo,(v_s.entrada_otimizador#>>'{escalares,orcamento}')::integer,
      v_c.orcamento,v_e.captura_id,'orcamento_divergente_do_valor_efetivo',
      to_jsonb(v_old),v_pub,to_jsonb(v_s));
   insert into clube_novo.build_linha_card(
      card_id,funcao_id,posicao_id,lote_producao_id,carta_versao,carta_fingerprint,
      estado,pendencias,execucao_tipo,estado_otimizador,
      otimizador_formula_fingerprint_esperado,otimizador_contrato_fingerprint_esperado,
      otimizador_motor_versao_esperada,impeto_condicional_codigo,impeto_condicional_nivel)
   values(v_old.card_id,v_old.funcao_id,v_old.posicao_id,p_lote_corretivo,
      v_bonificador->>'carta_versao',v_bonificador->>'carta_fingerprint','pendente','{}','producao','pendente',
      v_modelo.formula_fingerprint,v_modelo.contrato_fingerprint,v_modelo.motor_versao,
      v_old.impeto_condicional_codigo,v_old.impeto_condicional_nivel) returning id into v_new;
   v_ordem:=v_ordem+1;
   insert into clube_novo.otimizador_lote_producao_linha_v3(lote_id,linha_id,card_id,ordem_fila,overall_snapshot,entrada_fingerprint)
   values(p_lote_corretivo,v_new,v_old.card_id,v_ordem,(select overall from clube_novo.carta_jogo where card_id=v_old.card_id),v_fp);
   update clube_novo.orcamento_revisao_linha_v1 set linha_nova_id=v_new where linha_anterior_id=v_id;
   v_total:=v_total+1;
 end loop;
 select count(*) into v_cards from clube_novo.otimizador_lote_producao_carta_v3 where lote_id=p_lote_corretivo;
 update clube_novo.otimizador_lote_producao_v3 set cards=v_cards,
   linhas=(select count(*) from clube_novo.otimizador_lote_producao_linha_v3 where lote_id=p_lote_corretivo),
   preparo_total=v_cards,preparo_concluido=v_cards,atualizado_em=clock_timestamp() where id=p_lote_corretivo;
 perform public.otimizador_reordenar_prioridade_v1(array[p_lote_corretivo]);
 insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
 values(p_lote_corretivo,'revisao_orcamento_preparada',jsonb_build_object('novas',v_total,'ja_revisadas',v_ja,'worker_iniciado',false));
 return jsonb_build_object('lote_corretivo_id',p_lote_corretivo,'novas',v_total,'ja_revisadas',v_ja,'worker_iniciado',false);
end $function$
;
CREATE OR REPLACE VIEW clube_novo.otimizador_prioridade_orcamento_v1 AS
 SELECT c.card_id,
    c.overall,
    c.level_cap AS nivel_maximo,
    c.orcamento AS orcamento_real,
    e.captura_id,
        CASE
            WHEN COALESCE(c.orcamento, 0) > 0 THEN 1
            ELSE 2
        END AS prioridade_grupo
   FROM clube_novo.carta_jogo c
     JOIN clube_novo.carta_nivel_evidencia_v1 e ON e.card_id = c.card_id
  WHERE c.level_cap >= 1 AND c.orcamento = 2*(c.level_cap-1) AND c.cap_estimado IS FALSE AND e.nivel_maximo >= 1 AND e.orcamento_real = (2 * (e.nivel_maximo - 1)) AND c.tipo_carta_id <> 'player_delete_list'::text;
