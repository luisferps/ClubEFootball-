-- Fechamento manual autorizado das seis publicacoes preservadas.
-- Reusa o calculo e o formatador do finalizador oficial; nao restaura O na fila.
do $manual$
declare
 a clube_novo.correcao_estilos_item_v12%rowtype;
 l clube_novo.build_linha_card%rowtype;
 o clube_novo.build_otimizador%rowtype;
 b clube_novo.build_bonificador%rowtype;
 bp clube_novo.build_bonificador%rowtype;
 p clube_novo.build_publicacao_linha_ativa_v1%rowtype;
 d clube_novo.build_pontuacao_final_v2_delta_v1%rowtype;
 f record;
 v_agora timestamptz:=clock_timestamp();
 v_nota_motor numeric; v_nota_final numeric; v_linha_publicacao_fp text;
 v_publicacao_v2_fp text; v_proveniencia jsonb; v_nfp text; v_cfp text;
 v_lantes jsonb; v_qantes jsonb; v_fantes jsonb; v_count integer;
 v_lcampos text[]:=array['build_bonificador_id','bonificador_motor_versao','bonificador_contrato_versao','snapshot_bonificador_fingerprint',
 'publicacao_fingerprint','publicada_em','nota_bonificador_resultado_fingerprint','nota_bonus_playstyle_1','nota_bonus_playstyle_2','nota_bonus_total','nota_final',
 'nota_normalizacao_fingerprint','nota_calculo_fingerprint','nota_publicacao_fingerprint_v1','nota_publicada_em_v1','nota_calculada_em','atualizado_em'];
begin
 perform pg_advisory_xact_lock(hashtextextended('correcao-estilos-v12-executor',0));
 perform set_config('clube_novo.correcao_estilos_v12','1',true);
 if (select count(*) from clube_novo.correcao_estilos_item_v12 where estado<>'concluida')<>6 then raise exception 'O conjunto pendente mudou'; end if;
 perform 1 from clube_novo.build_linha_card where id=any(array[403298,403305,403306,403309,403310,403323]) order by id for update;
 for a in select * from clube_novo.correcao_estilos_item_v12 where linha_id=any(array[403298,403305,403306,403309,403310,403323]) order by linha_id for update loop
  select * into strict l from clube_novo.build_linha_card where id=a.linha_id;
  select * into strict p from clube_novo.build_publicacao_linha_ativa_v1 where linha_id=a.linha_id for update;
  select * into strict d from clube_novo.build_pontuacao_final_v2_delta_v1 where linha_id=a.linha_id for update;
  select * into strict o from clube_novo.build_otimizador where id=p.build_otimizador_id;
  select * into strict bp from clube_novo.build_bonificador where id=p.build_bonificador_id;
  select * into strict b from clube_novo.build_bonificador where id=a.novo_id;
  if a.estado<>'corrigida' or l.estado<>'pendente' or l.estado_otimizador<>'pendente' or l.build_otimizador_id is not null
   or (l.card_id,l.funcao_id,l.posicao_id,l.carta_fingerprint) is distinct from (a.card_id,a.funcao_id,a.posicao_id,a.carta_fingerprint)
   or l.build_bonificador_id is distinct from a.antigo_id
   or (p.card_id,p.funcao_id,p.posicao_id,p.build_otimizador_id,p.nota_final,p.publicacao_fingerprint)
      is distinct from (a.card_id,a.funcao_id,a.posicao_id,a.otimizador_id,a.nota_anterior,a.publicacao_anterior->>'publicacao_fingerprint')
   or p.build_bonificador_id is distinct from (a.publicacao_anterior->>'build_bonificador_id')::bigint
   or o.resultado_fingerprint is distinct from a.otimizador_fingerprint
   or b.resultado_fingerprint is distinct from a.resultado_novo_fingerprint
   or b.carta_fingerprint is distinct from l.carta_fingerprint or b.entrada_bonificador_fingerprint is distinct from l.carta_fingerprint
   or b.carta_versao is distinct from o.carta_versao
   or not clube_novo.bonus_estilo_conforme_v12(b.id,l.card_id,l.funcao_id,l.posicao_id)
  then raise exception 'Fonte ou estado mudou: %',a.linha_id; end if;
  if (b.bonus_pe,b.bonus_fisico_total,b.bonus_posicao,b.bonus_ia,b.bonus_outros,b.bonus_fisico_detalhe,b.b_corpo,b.b_pe_ruim,b.corpo_soma,b.corpo_pct,b.faltou)
    is distinct from (bp.bonus_pe,bp.bonus_fisico_total,bp.bonus_posicao,bp.bonus_ia,bp.bonus_outros,bp.bonus_fisico_detalhe,bp.b_corpo,bp.b_pe_ruim,bp.corpo_soma,bp.corpo_pct,bp.faltou)
    or b.bonus_total-bp.bonus_total is distinct from b.b_estilo-bp.b_estilo
  then raise exception 'Diferenca fora dos estilos: %',a.linha_id; end if;
  if (d.build_otimizador_id,d.build_bonificador_id,d.overall_final,d.publicacao_v2_fingerprint,d.otimizador_resultado_fingerprint,
      d.tecnico_id,d.barras,d.impeto_adicional_codigo,d.habilidades_adicionais,d.atributos_finais,d.arows_snapshot)
    is distinct from (o.id,bp.id,p.nota_final,p.publicacao_v2_fingerprint,o.resultado_fingerprint,
      o.tecnico_id,o.barras,o.impeto_adicional_codigo,o.habilidades_adicionais,o.atributos_finais,o.arows_snapshot)
  then raise exception 'Publicacao/delta inconsistente: %',a.linha_id; end if;
  v_nota_motor:=clube_novo.calcular_pontuacao_normalizada_v2(coalesce(o.atributos_internos,o.atributos_finais),o.arows_snapshot);
  v_nota_final:=v_nota_motor+b.bonus_total;
  if v_nota_motor is distinct from d.pontuacao_otimizador_normalizada or
   v_nota_final is distinct from p.nota_final-bp.bonus_total+b.bonus_total
  then raise exception 'Normalizacao anterior nao confere: %',a.linha_id; end if;
  -- Mesmo selo V1 da view oficial, usando o O atualmente publicado.
  select o.pontuacao as pontuacao_otimizador,
   encode(extensions.digest(convert_to(jsonb_build_object(
    'contrato','clube-novo-pontuacao-final-v1','linha_id',l.id,'card_id',l.card_id,'funcao_id',l.funcao_id,'posicao_id',l.posicao_id,
    'build_otimizador_id',o.id,'otimizador_resultado_fingerprint',o.resultado_fingerprint,
    'build_bonificador_id',b.id,'bonificador_resultado_fingerprint',b.resultado_fingerprint,
    'pontuacao_final',round(o.pontuacao+b.bonus_total,4))::text,'UTF8'),'sha256'),'hex') as selo_final_fingerprint into f;
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


  v_nfp:=clube_novo.fingerprint_normalizacao_v2(l.id,o.id,b.id,o.resultado_fingerprint,b.resultado_fingerprint,f.selo_final_fingerprint);
  v_cfp:=clube_novo.fingerprint_calculo_pontuacao_v2(l.id,coalesce(o.atributos_internos,o.atributos_finais),o.arows_snapshot,b.bonus_total);
  v_lantes:=to_jsonb(l);
  select jsonb_agg(to_jsonb(q) order by q.lote_id,q.ordem_fila) into v_qantes from clube_novo.otimizador_lote_producao_linha_v3 q where q.linha_id=l.id;
  select to_jsonb(q) into v_fantes from clube_novo.build_finalizacao_fila_v1 q where q.linha_id=l.id;
  update clube_novo.build_pontuacao_final_v2_delta_v1 set
   build_bonificador_id=b.id,bonus_playstyle_1=b.bonus_playstyle_1,bonus_playstyle_2=b.bonus_playstyle_2,
   bonus_total_bonificador=b.bonus_total,overall_final=v_nota_final,normalizacao_fingerprint=v_nfp,calculo_banco_fingerprint=v_cfp,
   bonificador_resultado_fingerprint=b.resultado_fingerprint,publicacao_fingerprint_v1=f.selo_final_fingerprint,
   publicacao_v2_fingerprint=v_publicacao_v2_fp,publicacao_linha_fingerprint_v2=v_linha_publicacao_fp,proveniencia=v_proveniencia,publicada_em=v_agora
   where linha_id=l.id and publicacao_v2_fingerprint=d.publicacao_v2_fingerprint;
  get diagnostics v_count=row_count; if v_count<>1 then raise exception 'Delta nao atualizado: %',l.id; end if;
  update clube_novo.build_publicacao_linha_ativa_v1 set
   build_bonificador_id=b.id,nota_final=v_nota_final,selo_final_fingerprint=f.selo_final_fingerprint,
   publicacao_fingerprint=f.selo_final_fingerprint,publicacao_v2_fingerprint=v_publicacao_v2_fp,
   proveniencia=v_proveniencia,publicada_em=v_agora,versao_publicacao=versao_publicacao+1,atualizado_em=v_agora
   where linha_id=l.id and publicacao_fingerprint=p.publicacao_fingerprint;
  get diagnostics v_count=row_count; if v_count<>1 then raise exception 'Publicacao nao atualizada: %',l.id; end if;
  update clube_novo.bonificador_correcao_item_v1 set build_bonificador_id_novo=b.id
   where build_linha_card_id=l.id and build_bonificador_id_novo=a.antigo_id;
  update clube_novo.build_linha_card set build_bonificador_id=b.id,bonificador_motor_versao=b.motor_versao,
   bonificador_contrato_versao=b.contrato_versao,snapshot_bonificador_fingerprint=b.resultado_fingerprint,
   publicacao_fingerprint=f.selo_final_fingerprint,publicada_em=v_agora,
   nota_bonificador_resultado_fingerprint=b.resultado_fingerprint,
   nota_bonus_playstyle_1=b.bonus_playstyle_1,nota_bonus_playstyle_2=b.bonus_playstyle_2,nota_bonus_total=b.bonus_total,
   nota_final=v_nota_final,nota_normalizacao_fingerprint=v_nfp,nota_calculo_fingerprint=v_cfp,
   nota_publicacao_fingerprint_v1=f.selo_final_fingerprint,nota_publicada_em_v1=v_agora,nota_calculada_em=v_agora
   where id=l.id and build_otimizador_id is null and build_bonificador_id=a.antigo_id;
  get diagnostics v_count=row_count; if v_count<>1 then raise exception 'Linha nao atualizada: %',l.id; end if;
  if (select to_jsonb(x)-v_lcampos from clube_novo.build_linha_card x where x.id=l.id) is distinct from v_lantes-v_lcampos
   or (select jsonb_agg(to_jsonb(q) order by q.lote_id,q.ordem_fila) from clube_novo.otimizador_lote_producao_linha_v3 q where q.linha_id=l.id) is distinct from v_qantes
   or (select to_jsonb(q) from clube_novo.build_finalizacao_fila_v1 q where q.linha_id=l.id) is distinct from v_fantes
  then raise exception 'Fila/estado do Otimizador alterado: %',l.id; end if;
  if not exists(select 1 from clube_novo.build_pontuacao_final_v2_publica_v1 v join clube_novo.build_publicacao_linha_ativa_v1 pp using(linha_id)
   where v.linha_id=l.id and v.build_otimizador_id=o.id and v.build_bonificador_id=b.id
    and v.overall_final=v_nota_final and pp.nota_final=v_nota_final and pp.build_bonificador_id=b.id
    and v.bonus_playstyle_1=a.novo_1 and v.bonus_playstyle_2=a.novo_2
    and v.barras=d.barras and v.atributos_finais=d.atributos_finais and v.arows_snapshot=d.arows_snapshot)
  then raise exception 'Ponte publica nao confirmou: %',l.id; end if;
  update clube_novo.correcao_estilos_item_v12 set estado='concluida',concluida_em=v_agora,erro=null where linha_id=l.id and novo_id=b.id;
  insert into clube_novo.build_finalizacao_evento_v1(linha_id,evento,detalhe) values(l.id,'publicada',
   jsonb_build_object('origem','fechamento_manual_estilos_v12','build_otimizador_id',o.id,'build_bonificador_id',b.id,
   'nota_final',v_nota_final,'selo',f.selo_final_fingerprint,'otimizador_em_revisao_preservado',true,
   'publicacao_anterior',to_jsonb(p),'delta_anterior',to_jsonb(d),'linha_anterior',v_lantes,'fila_otimizador',v_qantes));
 end loop;
 if exists(select 1 from clube_novo.correcao_estilos_item_v12 where estado<>'concluida') then raise exception 'Restaram estilos incompletos'; end if;
 update clube_novo.correcao_estilos_execucao_v12 set concluida_em=coalesce(concluida_em,v_agora),
  auditoria=auditoria||jsonb_build_object('fechamento_manual',coalesce(auditoria->'fechamento_manual','{}'::jsonb)||jsonb_build_object(
    'concluido_em',v_agora,'publicacoes_confirmadas',9,'restantes',0,'seis_publicacoes_preservadas',to_jsonb(array[403298,403305,403306,403309,403310,403323]),
    'fila_otimizador_preservada',true))
  where id='estilos-funcao-20260909-v1';
end $manual$;
select public.correcao_estilos_status_v12() as status;

