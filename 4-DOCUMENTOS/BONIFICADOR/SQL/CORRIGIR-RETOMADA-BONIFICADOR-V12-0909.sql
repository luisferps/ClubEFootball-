CREATE OR REPLACE FUNCTION public.bonificador_preparar_retomada_v12(p_lote_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare l clube_novo.bonificador_correcao_lote_v1%rowtype; p clube_novo.bonificador_politica_estilo%rowtype;
begin
 if not exists(select 1 from clube_novo.correcao_estilos_execucao_v12 where concluida_em is not null)
  or exists(select 1 from clube_novo.correcao_estilos_item_v12 where estado<>'concluida') then
  return jsonb_build_object('liberada',false,'motivo','Aguarde a conclusao da correcao de estilos. Nenhuma linha foi reservada.');
 end if;
 perform pg_advisory_xact_lock(hashtextextended('correcao-estilos-v12-executor',0));
 select * into l from clube_novo.bonificador_correcao_lote_v1 where id=p_lote_id for update;
 if l.id is null or l.estado not in ('pausado','preparado') then raise exception 'lote inexistente ou nao esta pausado/preparado'; end if;
 if exists(select 1 from clube_novo.bonificador_correcao_item_v1 where lote_id=l.id and estado_item in ('processando','falha')) then
  raise exception 'o lote tem linha em processamento ou falha pendente'; end if;
 if l.motor_versao not in ('v11-0709-estilo-posicao-oficial-v1','v12-0909-estilo-funcao-ativacao-v1') then
  raise exception 'versao anterior do lote nao foi aprovada para esta retomada'; end if;
 select * into strict p from clube_novo.bonificador_politica_estilo where versao='estilos-funcao-20260909-v1' for update;
 if p.politica_fingerprint<>'7ed53bbab831180cde9d247782dd133fe072acadb69bd34871c3f83f28773dc5'
  or p.estado not in ('aprovada_implantacao_pendente','ativa') then raise exception 'politica de estilos mudou'; end if;
 if l.motor_versao<>'v12-0909-estilo-funcao-ativacao-v1' then
  update clube_novo.correcao_estilos_execucao_v12 set auditoria=auditoria||jsonb_build_object(
   'retomada_bonificador_completo',jsonb_build_object('solicitada_em',clock_timestamp(),'lote_antes',to_jsonb(l),'politica_estado_antes',p.estado))
  where id='estilos-funcao-20260909-v1';
  update clube_novo.bonificador_correcao_lote_v1 set
   motor_versao='v12-0909-estilo-funcao-ativacao-v1',
   contrato_regua='bonificador-regua-v4',
   formula_fingerprint='4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8',
   observacao=coalesce(observacao,'')||' | Retomada V12 apos conclusao seletiva; ordem, estados e resultados preservados.',
   atualizado_em=clock_timestamp()
  where id=l.id;
 end if;
 update clube_novo.bonificador_politica_estilo set estado='ativa' where versao=p.versao and estado<>'ativa';
 return jsonb_build_object('liberada',true,'lote_id',l.id,'estado',l.estado,
  'motor','v12-0909-estilo-funcao-ativacao-v1','nenhuma_linha_reservada',true);
end $function$
;
alter table clube_novo.bonificador_correcao_lote_v1
 drop constraint bonificador_correcao_lote_v1_contrato_regua_check,
 drop constraint bonificador_correcao_lote_v1_formula_fingerprint_check,
 drop constraint bonificador_correcao_lote_v1_motor_versao_check,
 add constraint bonificador_correcao_lote_v1_motor_contrato_formula_check check (
 (motor_versao='v11-0709-estilo-posicao-oficial-v1'
  and contrato_regua='bonificador-regua-v3'
  and formula_fingerprint='2e80a07d51f2bc8f456f9710c82717d38e3142cb3d52fd325b7b587c58ed2879')
 or
 (motor_versao='v12-0909-estilo-funcao-ativacao-v1'
  and contrato_regua='bonificador-regua-v4'
  and formula_fingerprint='4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8')
);