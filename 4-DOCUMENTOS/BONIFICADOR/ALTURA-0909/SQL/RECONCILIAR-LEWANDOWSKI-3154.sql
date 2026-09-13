begin;
do $fix$
declare l clube_novo.build_linha_card%rowtype; o clube_novo.build_otimizador%rowtype; f jsonb;
begin
 select * into strict l from clube_novo.build_linha_card where id=3154 for update;
 select * into strict o from clube_novo.build_otimizador where id=l.build_otimizador_id;
 if o.id<>60041 or o.carta_fingerprint is distinct from l.carta_fingerprint or o.carta_versao is distinct from l.carta_versao
 or o.formula_fingerprint is distinct from l.otimizador_formula_fingerprint_esperado
 or o.contrato_fingerprint is distinct from l.otimizador_contrato_fingerprint_esperado
 or not exists(select 1 from clube_novo.otimizador_evento_producao_v3 e where e.linha_id=l.id and e.evento='linha_importada_json_local' and (e.detalhe->>'build_otimizador_id')::bigint=o.id and e.detalhe->>'resultado_fingerprint'=o.resultado_fingerprint) then raise exception 'Evidencia mudou';end if;
 update clube_novo.build_linha_card set snapshot_otimizador_fingerprint=o.resultado_fingerprint,
 otimizador_motor_versao=o.motor_versao,otimizador_contrato_versao=o.contrato_versao where id=l.id;
 f:=clube_novo.finalizar_publicar_linha_v1(l.id,'reconciliar_metadados_importacao_comprovada');
 if f->>'estado' not in('publicada','ja_publicada') then raise exception 'Publicacao falhou: %',f;end if;
 insert into clube_novo.otimizador_evento_producao_v3(lote_id,linha_id,evento,detalhe)
 values(l.lote_producao_id,l.id,'linha_concluida',jsonb_build_object('acao','reconciliacao_metadados_sem_recalculo','resultado_id',o.id,'selo_anterior',l.snapshot_otimizador_fingerprint,'selo_confirmado',o.resultado_fingerprint,'motor_anterior',l.otimizador_motor_versao,'motor_confirmado',o.motor_versao,'evidencia','linha_importada_json_local de 2026-09-05','resultado_preservado',true));
 update clube_novo.correcao_altura_ia_v13 c set estado='concluida',erro=null,concluida_em=clock_timestamp()
 where c.linha_id=l.id and c.novo_id=(f->>'build_bonificador_id')::bigint;
end $fix$;
commit;

