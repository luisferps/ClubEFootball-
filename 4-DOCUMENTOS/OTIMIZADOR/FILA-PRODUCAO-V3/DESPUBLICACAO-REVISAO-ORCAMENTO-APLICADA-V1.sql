CREATE OR REPLACE FUNCTION clube_novo.finalizar_publicar_linha_v1(p_linha_id bigint, p_origem text DEFAULT 'desconhecida'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  l clube_novo.build_linha_card%rowtype;
  o clube_novo.build_otimizador%rowtype;
  b clube_novo.build_bonificador%rowtype;
  f record;
  v_bonus_id bigint;
  v_agora timestamptz:=clock_timestamp();
  v_numerador numeric; v_denominador numeric; v_nota_motor numeric; v_nota_final numeric;
  v_linha_publicacao_fp text; v_publicacao_v2_fp text; v_proveniencia jsonb;
  v_delta integer; v_ativa clube_novo.build_publicacao_linha_ativa_v1%rowtype;
  v_erro text; v_estado text; v_motivo text;
begin
  if p_linha_id is null then raise exception 'finalizacao: linha obrigatoria'; end if;
  select * into l from clube_novo.build_linha_card where id=p_linha_id for update;
  if l.id is null then return jsonb_build_object('ok',false,'estado','erro','motivo','linha inexistente'); end if;

  if exists(select 1 from clube_novo.orcamento_revisao_linha_v1 r where r.linha_anterior_id=l.id) then
    update clube_novo.build_finalizacao_fila_v1 set estado='erro',
      motivo='resultado anterior invalidado por correcao de orcamento',
      proxima_tentativa_em='infinity'::timestamptz, atualizado_em=clock_timestamp()
    where linha_id=l.id;
    return jsonb_build_object('ok',false,'linha_id',l.id,'estado','invalidada',
      'motivo','resultado anterior substituido por revisao de orcamento');
  end if;

  insert into clube_novo.build_finalizacao_fila_v1(
    linha_id,estado,prioridade,overall_origem,tentativas,origem_ultima,
    proxima_tentativa_em,ultima_tentativa_em,atualizado_em)
  select l.id,'processando',coalesce((
      select min(i.prioridade_grupo)::integer
      from clube_novo.bonificador_correcao_item_v1 i
      join clube_novo.bonificador_correcao_lote_v1 lo on lo.id=i.lote_id
      where i.build_linha_card_id=l.id and i.estado_item='preparado'
        and lo.motor_versao='v10-0409-fisico-regra-aprovada-v1'
    ),10),c.overall,1,coalesce(nullif(p_origem,''),'desconhecida'),v_agora,v_agora,v_agora
  from clube_novo.carta_jogo c where c.card_id=l.card_id
  on conflict(linha_id) do update set estado='processando',
    tentativas=clube_novo.build_finalizacao_fila_v1.tentativas+1,
    prioridade=least(clube_novo.build_finalizacao_fila_v1.prioridade,excluded.prioridade),
    overall_origem=excluded.overall_origem,origem_ultima=excluded.origem_ultima,
    ultima_tentativa_em=v_agora,atualizado_em=v_agora;

  select i.build_bonificador_id_novo into v_bonus_id
  from clube_novo.bonificador_correcao_item_v1 i
  join clube_novo.bonificador_correcao_lote_v1 lo on lo.id=i.lote_id
  join clube_novo.build_bonificador bx on bx.id=i.build_bonificador_id_novo
  where i.build_linha_card_id=l.id and i.estado_item='preparado'
    and bx.motor_versao='v10-0409-fisico-regra-aprovada-v1'
    and bx.formula_fingerprint='756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
    and bx.contrato_versao='bonificador-regua-v3'
  order by lo.criado_em desc,i.preparado_em desc limit 1;
  if v_bonus_id is null then
    select bx.id into v_bonus_id
    from clube_novo.build_bonificador bx
    where bx.id=l.build_bonificador_id
      and bx.motor_versao='v10-0409-fisico-regra-aprovada-v1'
      and bx.formula_fingerprint='756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
      and bx.contrato_versao='bonificador-regua-v3';
  end if;

  if l.build_otimizador_id is null or l.estado_otimizador<>'concluido' then
    v_estado:='aguardando'; v_motivo:='aguardando Otimizador concluido';
  elsif v_bonus_id is null then
    v_estado:='aguardando'; v_motivo:='aguardando Bonificador V10';
  else
    select * into o from clube_novo.build_otimizador where id=l.build_otimizador_id;
    select * into b from clube_novo.build_bonificador where id=v_bonus_id;
    if o.id is null then v_estado:='erro'; v_motivo:='resultado do Otimizador inexistente';
    elsif b.id is null then v_estado:='erro'; v_motivo:='resultado do Bonificador inexistente';
    elsif b.motor_versao<>'v10-0409-fisico-regra-aprovada-v1'
       or b.formula_fingerprint<>'756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
       or b.contrato_versao<>'bonificador-regua-v3' then
      v_estado:='erro'; v_motivo:='Bonificador V9 ou V10 sem selo aprovado';
    elsif o.carta_versao<>l.carta_versao or b.carta_versao<>l.carta_versao
       or o.carta_fingerprint<>l.carta_fingerprint or b.carta_fingerprint<>l.carta_fingerprint then
      v_estado:='erro'; v_motivo:='versao ou fingerprint da carta incompatível';
    elsif o.resultado_fingerprint is distinct from l.snapshot_otimizador_fingerprint then
      v_estado:='erro'; v_motivo:='selo do Otimizador nao coincide com a linha';
    elsif jsonb_typeof(o.atributos_finais)<>'array' or jsonb_array_length(o.atributos_finais)<>26
       or jsonb_typeof(coalesce(o.atributos_internos,o.atributos_finais))<>'array'
       or jsonb_array_length(coalesce(o.atributos_internos,o.atributos_finais))<>26
       or o.arows_snapshot is null then
      v_estado:='aguardando'; v_motivo:='aguardando 26 atributos e arows do Otimizador';
    elsif cardinality(l.pendencias)<>0 or l.execucao_tipo<>'producao' or l.lote_teste_id is not null
       or l.pendencias @> array['teste_nao_publicado'::text] then
      v_estado:='erro'; v_motivo:='linha nao e publicavel pelo contrato produtivo';
    end if;
  end if;

  if v_estado is not null then
    update clube_novo.build_finalizacao_fila_v1 set estado=v_estado,motivo=v_motivo,
      proxima_tentativa_em=v_agora+case when v_estado='erro' then interval '1 hour' else interval '5 minutes' end,
      atualizado_em=v_agora where linha_id=l.id;
    return jsonb_build_object('ok',v_estado<>'erro','linha_id',l.id,'estado',v_estado,'motivo',v_motivo);
  end if;

  select * into v_ativa from clube_novo.build_publicacao_linha_ativa_v1 where linha_id=l.id;
  if v_ativa.linha_id is not null
     and v_ativa.build_otimizador_id=l.build_otimizador_id
     and v_ativa.build_bonificador_id=v_bonus_id
     and l.build_bonificador_id=v_bonus_id
     and l.nota_final is not distinct from v_ativa.nota_final
     and l.nota_bonificador_resultado_fingerprint is not distinct from b.resultado_fingerprint
     and l.nota_otimizador_resultado_fingerprint is not distinct from o.resultado_fingerprint
     and exists(select 1 from clube_novo.build_pontuacao_final_v2_delta_v1 d where d.linha_id=l.id) then
    update clube_novo.build_finalizacao_fila_v1 set estado='concluido',motivo='idempotente',
      concluido_em=coalesce(concluido_em,v_agora),publicacao_fingerprint=v_ativa.publicacao_fingerprint,
      atualizado_em=v_agora where linha_id=l.id;
    return jsonb_build_object('ok',true,'linha_id',l.id,'estado','ja_publicada',
      'publicacao_fingerprint',v_ativa.publicacao_fingerprint,'idempotente',true);
  end if;

  begin
    perform set_config('clube_novo.finalizacao_linha_em_curso',l.id::text,true);
    update clube_novo.build_linha_card set
      build_bonificador_id=v_bonus_id,
      bonificador_motor_versao=b.motor_versao,
      bonificador_contrato_versao=b.contrato_versao,
      snapshot_bonificador_fingerprint=b.resultado_fingerprint,
      publicacao_fingerprint=null,publicada_em=null,
      nota_contrato=null,nota_otimizador_resultado_fingerprint=null,
      nota_bonificador_resultado_fingerprint=null,nota_carta_fingerprint=null,
      nota_formula_fingerprint=null,nota_contrato_fingerprint=null,
      nota_bruta_selada=null,nota_bonus_pe=null,nota_bonus_fisico_total=null,
      nota_bonus_posicao=null,nota_bonus_playstyle_1=null,nota_bonus_playstyle_2=null,
      nota_bonus_ia=null,nota_bonus_outros=null,nota_bonus_total=null,
      nota_numerador=null,nota_denominador=null,nota_do_motor=null,nota_final=null,
      nota_normalizacao_fingerprint=null,nota_calculo_fingerprint=null,
      nota_publicacao_fingerprint_v1=null,nota_publicada_em_v1=null,nota_calculada_em=null,
      atualizado_em=v_agora
    where id=l.id;

    select * into f from clube_novo.build_pontuacao_final_v1 where linha_id=l.id;
    if f.linha_id is null or f.estado_final<>'elegivel_para_publicacao'
       or f.selo_final_fingerprint is null then
      raise exception 'linha nao ficou elegivel: %',coalesce(f.motivo_final,'sem contrato final');
    end if;

    v_numerador:=clube_novo.calcular_numerador_normalizacao_v2(
      coalesce(o.atributos_internos,o.atributos_finais),o.arows_snapshot);
    v_denominador:=clube_novo.calcular_denominador_normalizacao_v2(o.arows_snapshot);
    v_nota_motor:=clube_novo.calcular_pontuacao_normalizada_v2(
      coalesce(o.atributos_internos,o.atributos_finais),o.arows_snapshot);
    v_nota_final:=v_nota_motor+b.bonus_total;

    update clube_novo.build_linha_card set
      publicacao_fingerprint=f.selo_final_fingerprint,publicada_em=v_agora,
      nota_contrato='clube-novo-pontuacao-normalizada-v2',
      nota_otimizador_resultado_fingerprint=o.resultado_fingerprint,
      nota_bonificador_resultado_fingerprint=b.resultado_fingerprint,
      nota_carta_fingerprint=o.carta_fingerprint,
      nota_formula_fingerprint=o.formula_fingerprint,
      nota_contrato_fingerprint=o.contrato_fingerprint,
      nota_bruta_selada=f.pontuacao_otimizador,
      nota_bonus_pe=b.bonus_pe,nota_bonus_fisico_total=b.bonus_fisico_total,
      nota_bonus_posicao=b.bonus_posicao,nota_bonus_playstyle_1=b.bonus_playstyle_1,
      nota_bonus_playstyle_2=b.bonus_playstyle_2,nota_bonus_ia=b.bonus_ia,
      nota_bonus_outros=coalesce(b.bonus_outros,'{}'::jsonb),nota_bonus_total=b.bonus_total,
      nota_numerador=v_numerador,nota_denominador=v_denominador,
      nota_do_motor=v_nota_motor,nota_final=v_nota_final,
      nota_normalizacao_fingerprint=clube_novo.fingerprint_normalizacao_v2(
        l.id,o.id,b.id,o.resultado_fingerprint,b.resultado_fingerprint,f.selo_final_fingerprint),
      nota_calculo_fingerprint=clube_novo.fingerprint_calculo_pontuacao_v2(
        l.id,coalesce(o.atributos_internos,o.atributos_finais),o.arows_snapshot,b.bonus_total),
      nota_publicacao_fingerprint_v1=f.selo_final_fingerprint,
      nota_publicada_em_v1=v_agora,nota_calculada_em=v_agora,atualizado_em=v_agora
    where id=l.id;

    v_linha_publicacao_fp:=pg_catalog.encode(extensions.digest(pg_catalog.convert_to(
      jsonb_build_object(
        'contrato','clube-novo-pontuacao-final-v2','linha_id',l.id,
        'calculo_banco_fingerprint',clube_novo.fingerprint_calculo_pontuacao_v2(
          l.id,coalesce(o.atributos_internos,o.atributos_finais),o.arows_snapshot,b.bonus_total),
        'bonificador_resultado_fingerprint',b.resultado_fingerprint,
        'overall_final',v_nota_final,'publicacao_fingerprint_v1',f.selo_final_fingerprint
      )::text,'UTF8'::name),'sha256'),'hex');
    v_publicacao_v2_fp:=pg_catalog.encode(extensions.digest(pg_catalog.convert_to(
      jsonb_build_object('contrato','clube-novo-publicacao-automatica-por-linha-v1',
        'linha_id',l.id,'publicacao_linha_fingerprint_v2',v_linha_publicacao_fp)::text,
      'UTF8'::name),'sha256'),'hex');
    v_proveniencia:=jsonb_build_object(
      'contrato','clube-novo-pontuacao-final-v2','modo','automatico_por_linha',
      'linha_id',l.id,
      'otimizador',jsonb_build_object('id',o.id,'resultado_fingerprint',o.resultado_fingerprint,
        'pontuacao_bruta_apenas_evidencia',f.pontuacao_otimizador,
        'pontuacao_normalizada',v_nota_motor),
      'bonificador',jsonb_build_object('id',b.id,'resultado_fingerprint',b.resultado_fingerprint,
        'componentes',jsonb_build_object('pe',b.bonus_pe,'fisico',b.bonus_fisico_total,
          'posicao',b.bonus_posicao,'playstyle_1',b.bonus_playstyle_1,
          'playstyle_2',b.bonus_playstyle_2,'ia',b.bonus_ia,
          'outros',coalesce(b.bonus_outros,'{}'::jsonb)),
        'bonus_total',b.bonus_total),
      'pontuacao_final_oficial',v_nota_final,
      'publicacao_v1',f.selo_final_fingerprint,'publicacao_v2',v_linha_publicacao_fp);

    delete from clube_novo.build_pontuacao_final_v2_delta_v1 where linha_id=l.id;
    insert into clube_novo.build_pontuacao_final_v2_delta_v1(
      publicacao_v2_fingerprint,linha_id,card_id,funcao_id,posicao_id,
      build_otimizador_id,build_bonificador_id,tecnico_id,barras,
      impeto_adicional_codigo,habilidades_adicionais,atributos_finais,arows_snapshot,
      pontuacao_otimizador_bruta_evidencia,pontuacao_otimizador_normalizada,
      bonus_pe,bonus_fisico_total,bonus_posicao,bonus_playstyle_1,bonus_playstyle_2,
      bonus_ia,bonus_outros,bonus_total_bonificador,overall_final,
      normalizacao_fingerprint,calculo_banco_fingerprint,carta_fingerprint,
      formula_fingerprint,contrato_fingerprint,otimizador_resultado_fingerprint,
      bonificador_resultado_fingerprint,publicacao_fingerprint_v1,publicada_em,
      publicacao_linha_fingerprint_v2,topo_funcao,percentual_topo,
      estado_final,motivo_final,proveniencia)
    values(
      v_publicacao_v2_fp,l.id,l.card_id,l.funcao_id,l.posicao_id,
      o.id,b.id,o.tecnico_id,o.barras,o.impeto_adicional_codigo,o.habilidades_adicionais,
      o.atributos_finais,o.arows_snapshot,f.pontuacao_otimizador,v_nota_motor,
      b.bonus_pe,b.bonus_fisico_total,b.bonus_posicao,b.bonus_playstyle_1,
      b.bonus_playstyle_2,b.bonus_ia,coalesce(b.bonus_outros,'{}'::jsonb),b.bonus_total,
      v_nota_final,
      clube_novo.fingerprint_normalizacao_v2(l.id,o.id,b.id,o.resultado_fingerprint,
        b.resultado_fingerprint,f.selo_final_fingerprint),
      clube_novo.fingerprint_calculo_pontuacao_v2(l.id,
        coalesce(o.atributos_internos,o.atributos_finais),o.arows_snapshot,b.bonus_total),
      o.carta_fingerprint,o.formula_fingerprint,o.contrato_fingerprint,
      o.resultado_fingerprint,b.resultado_fingerprint,f.selo_final_fingerprint,v_agora,
      v_linha_publicacao_fp,null,null,'publicada',
      'PUBLICADA_AUTOMATICAMENTE_POR_LINHA',v_proveniencia);
    get diagnostics v_delta=row_count;
    if v_delta<>1 then raise exception 'read model incremental recebeu % linhas',v_delta; end if;

    insert into clube_novo.build_publicacao_linha_ativa_v1(
      linha_id,card_id,funcao_id,posicao_id,build_otimizador_id,build_bonificador_id,
      nota_final,selo_final_fingerprint,publicacao_fingerprint,publicacao_v2_fingerprint,
      proveniencia,publicada_em,versao_publicacao,atualizado_em)
    select l.id,l.card_id,l.funcao_id,l.posicao_id,o.id,b.id,v_nota_final,
      f.selo_final_fingerprint,f.selo_final_fingerprint,d.publicacao_v2_fingerprint,
      v_proveniencia,v_agora,1,v_agora
    from clube_novo.build_pontuacao_final_v2_delta_v1 d where d.linha_id=l.id
    on conflict(linha_id) do update set
      card_id=excluded.card_id,funcao_id=excluded.funcao_id,posicao_id=excluded.posicao_id,
      build_otimizador_id=excluded.build_otimizador_id,
      build_bonificador_id=excluded.build_bonificador_id,nota_final=excluded.nota_final,
      selo_final_fingerprint=excluded.selo_final_fingerprint,
      publicacao_fingerprint=excluded.publicacao_fingerprint,
      publicacao_v2_fingerprint=excluded.publicacao_v2_fingerprint,
      proveniencia=excluded.proveniencia,publicada_em=excluded.publicada_em,
      versao_publicacao=clube_novo.build_publicacao_linha_ativa_v1.versao_publicacao+1,
      atualizado_em=excluded.atualizado_em;

    if not exists(select 1 from clube_novo.build_pontuacao_final_v2_publica_v1 p
      join clube_novo.build_publicacao_linha_ativa_v1 a using(linha_id)
      where p.linha_id=l.id and p.build_otimizador_id=a.build_otimizador_id
        and p.build_bonificador_id=a.build_bonificador_id and p.overall_final=a.nota_final) then
      raise exception 'readback da ponte publica falhou';
    end if;
  exception when others then
    get stacked diagnostics v_erro=message_text;
    update clube_novo.build_finalizacao_fila_v1 set estado='erro',motivo=v_erro,
      proxima_tentativa_em=clock_timestamp()+interval '10 minutes',atualizado_em=clock_timestamp()
      where linha_id=l.id;
    insert into clube_novo.build_finalizacao_evento_v1(linha_id,evento,detalhe)
      values(l.id,'falhou',jsonb_build_object('origem',p_origem,'erro',v_erro));
    return jsonb_build_object('ok',false,'linha_id',l.id,'estado','erro','motivo',v_erro);
  end;

  update clube_novo.build_finalizacao_fila_v1 set estado='concluido',motivo=null,
    concluido_em=v_agora,publicacao_fingerprint=f.selo_final_fingerprint,
    atualizado_em=v_agora where linha_id=l.id;
  insert into clube_novo.build_finalizacao_evento_v1(linha_id,evento,detalhe)
    values(l.id,'publicada',jsonb_build_object('origem',p_origem,
      'build_otimizador_id',o.id,'build_bonificador_id',b.id,
      'nota_final',v_nota_final,'selo',f.selo_final_fingerprint));
  update clube_novo.orcamento_revisao_linha_v1 set estado='republicada'
    where linha_nova_id=l.id;
  return jsonb_build_object('ok',true,'linha_id',l.id,'card_id',l.card_id,
    'estado','publicada','nota_final',v_nota_final,'publicacao_fingerprint',f.selo_final_fingerprint,
    'build_otimizador_id',o.id,'build_bonificador_id',b.id,'idempotente',false);
end
$function$
;
create or replace function public.despublicar_revisoes_orcamento_v1(p_linhas bigint[])
returns jsonb language plpgsql security definer set search_path='' as $fn$
declare v_id bigint; v_r clube_novo.orcamento_revisao_linha_v1%rowtype;
v_l clube_novo.build_linha_card%rowtype; v_total int:=0; v_publicadas int:=0;
begin
 if coalesce(cardinality(p_linhas),0) not between 1 and 1000
    or cardinality(p_linhas)<>(select count(distinct x) from unnest(p_linhas)x)
 then raise exception 'despublicacao: lista de linhas revisadas obrigatoria'; end if;
 perform pg_advisory_xact_lock(hashtextextended('orcamento-despublicar-v1',0));
 foreach v_id in array p_linhas loop
   select * into v_r from clube_novo.orcamento_revisao_linha_v1 where linha_anterior_id=v_id for update;
   if not found or v_r.linha_nova_id is null then raise exception 'despublicacao: linha % sem revisao pronta',v_id; end if;
   select * into v_l from clube_novo.build_linha_card where id=v_id for update;
   if not found or v_l.estado_otimizador='processando' then raise exception 'despublicacao: linha % inexistente ou em processamento',v_id; end if;
   if v_l.build_otimizador_id is distinct from (v_r.linha_anterior_snapshot->>'build_otimizador_id')::bigint then
     raise exception 'despublicacao: resultado mudou apos auditoria da linha %',v_id; end if;
   if not exists(select 1 from clube_novo.build_linha_card nova
       join clube_novo.otimizador_lote_producao_carta_v3 s on s.lote_id=nova.lote_producao_id and s.card_id=nova.card_id
       join clube_novo.carta_nivel_evidencia_v1 e on e.card_id=nova.card_id
       where nova.id=v_r.linha_nova_id and nova.card_id=v_l.card_id
       and (s.entrada_otimizador#>>'{escalares,orcamento}')::integer=e.orcamento_real)
   then raise exception 'despublicacao: nova entrada nao confere com evidencia'; end if;
   update clube_novo.orcamento_revisao_linha_v1 r set
     publicacao_anterior_snapshot=case when r.publicacao_anterior_snapshot is not null
       and not r.publicacao_anterior_snapshot ? '_delta_preservado'
       then r.publicacao_anterior_snapshot || jsonb_build_object('_delta_preservado',
         (select to_jsonb(d) from clube_novo.build_pontuacao_final_v2_delta_v1 d where d.linha_id=v_id))
       else r.publicacao_anterior_snapshot end,
     estado=case when r.estado='republicada' then r.estado else 'em_fila' end
   where linha_anterior_id=v_id;
   if exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 where linha_id=v_id) then v_publicadas:=v_publicadas+1; end if;
   delete from clube_novo.build_publicacao_linha_ativa_v1 where linha_id=v_id;
   delete from clube_novo.build_pontuacao_final_v2_delta_v1 where linha_id=v_id;
   update clube_novo.build_linha_card set estado='invalida',
     estado_otimizador=case when estado_otimizador='pendente' then 'bloqueado' else estado_otimizador end,
     erro_otimizador=case when estado_otimizador='pendente' then 'entrada_substituida_por_revisao_de_orcamento' else erro_otimizador end,
     pendencias=case when pendencias @> array['orcamento_invalido'] then pendencias else array_append(pendencias,'orcamento_invalido') end,
     publicada_em=null,publicacao_fingerprint=null,nota_contrato=null,nota_otimizador_resultado_fingerprint=null,nota_bonificador_resultado_fingerprint=null,nota_carta_fingerprint=null,nota_formula_fingerprint=null,nota_contrato_fingerprint=null,nota_bruta_selada=null,nota_bonus_pe=null,nota_bonus_fisico_total=null,nota_bonus_posicao=null,nota_bonus_playstyle_1=null,nota_bonus_playstyle_2=null,nota_bonus_ia=null,nota_bonus_outros=null,nota_bonus_total=null,nota_numerador=null,nota_denominador=null,nota_do_motor=null,nota_final=null,nota_normalizacao_fingerprint=null,nota_calculo_fingerprint=null,nota_publicacao_fingerprint_v1=null,nota_publicada_em_v1=null,nota_calculada_em=null,
     atualizado_em=clock_timestamp()
     where id=v_id;
   update clube_novo.build_finalizacao_fila_v1 set estado='erro',
     motivo='resultado invalidado por orcamento; nova linha '||v_r.linha_nova_id,
     proxima_tentativa_em='infinity'::timestamptz,publicacao_fingerprint=null,atualizado_em=clock_timestamp()
     where linha_id=v_id;
   v_total:=v_total+1;
 end loop;
 if exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 where linha_id=any(p_linhas))
    or exists(select 1 from clube_novo.build_linha_card where id=any(p_linhas) and (estado<>'invalida' or publicada_em is not null or nota_publicada_em_v1 is not null))
 then raise exception 'despublicacao: conferencia final falhou'; end if;
 return jsonb_build_object('ok',true,'linhas_invalidadas',v_total,'publicacoes_retiradas',v_publicadas,'historico_preservado',true);
end;
$fn$;
revoke all on function public.despublicar_revisoes_orcamento_v1(bigint[]) from public,anon,authenticated;
grant execute on function public.despublicar_revisoes_orcamento_v1(bigint[]) to service_role;
notify pgrst,'reload schema';

