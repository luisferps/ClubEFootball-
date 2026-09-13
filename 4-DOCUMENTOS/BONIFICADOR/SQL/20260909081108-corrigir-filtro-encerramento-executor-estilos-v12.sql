CREATE OR REPLACE FUNCTION public.correcao_estilos_tick_v12(p_limite integer DEFAULT 250, p_linhas bigint[] DEFAULT NULL::bigint[])
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
 SET statement_timeout TO '55s'
AS $function$
declare v_regua jsonb; v_n integer; v_publicadas integer:=0; r record; f jsonb;
 v_inicio timestamptz:=clock_timestamp(); v_erro text; v_lock boolean;
begin
 v_lock:=pg_try_advisory_xact_lock(hashtextextended('correcao-estilos-v12-executor',0));
 if not v_lock then return jsonb_build_object('ocupado',true); end if;
 if not exists(select 1 from clube_novo.correcao_estilos_execucao_v12) then raise exception 'auditoria nao preparada'; end if;
 if exists(select 1 from clube_novo.bonificador_correcao_item_v1 where estado_item='processando')
  or exists(select 1 from clube_novo.bonificador_correcao_lote_v1 where estado='rodando') then
  raise exception 'Bonificador geral em execucao; preserve a pausa durante a correcao seletiva';
 end if;
 if exists(select 1 from clube_novo.correcao_estilos_item_v12 where estado='erro') then return public.correcao_estilos_status_v12(); end if;
 v_regua:=public.bonificador_regua_v4();
 if v_regua->>'formula_fingerprint'<>'4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8'
  or not coalesce((v_regua->>'pode_rodar')::boolean,false) then raise exception 'regua V12 incompatível'; end if;
 perform set_config('clube_novo.correcao_estilos_v12','1',true);
 drop table if exists pg_temp._estilos_v12_batch;
 create temporary table _estilos_v12_batch on commit drop as
 select a.*,null::bigint criado_id
 from clube_novo.correcao_estilos_item_v12 a
 where a.estado='pendente' and (p_linhas is null or a.linha_id=any(p_linhas))
 order by a.era_publicada desc,a.linha_id
 limit least(greatest(coalesce(p_limite,250),1),500);
 get diagnostics v_n=row_count;
 if v_n>0 then
  perform 1 from clube_novo.build_linha_card l join _estilos_v12_batch a on a.linha_id=l.id order by l.id for update of l;
  if exists(select 1 from _estilos_v12_batch a join clube_novo.build_linha_card l on l.id=a.linha_id
   join clube_novo.build_bonificador b on b.id=a.antigo_id
   where l.estado<>'pendente' or l.card_id<>a.card_id or l.funcao_id<>a.funcao_id or l.posicao_id<>a.posicao_id
    or l.carta_fingerprint is distinct from a.carta_fingerprint
    or l.build_otimizador_id is distinct from a.otimizador_id
    or l.snapshot_otimizador_fingerprint is distinct from a.otimizador_fingerprint
    or b.carta_fingerprint is distinct from l.carta_fingerprint
    or b.entrada_bonificador_fingerprint is distinct from l.carta_fingerprint
    or b.carta_versao is distinct from l.carta_versao or coalesce(cardinality(b.faltou),-1)<>0
    or b.motor_versao<>'v11-0709-estilo-posicao-oficial-v1'
    or b.formula_fingerprint<>'2e80a07d51f2bc8f456f9710c82717d38e3142cb3d52fd325b7b587c58ed2879'
    or (l.build_bonificador_id is distinct from a.antigo_id and not exists(
     select 1 from clube_novo.bonificador_correcao_item_v1 i
     where i.build_linha_card_id=l.id and i.estado_item='preparado' and i.build_bonificador_id_novo=a.antigo_id))
    or exists(select 1 from clube_novo.orcamento_revisao_linha_v1 x where x.linha_anterior_id=l.id)
  ) then raise exception 'entrada ou identidade mudou desde a auditoria; nao corrigir sem nova conferência'; end if;
  for r in select distinct card_id,ataque,defesa from _estilos_v12_batch loop
   f:=clube_novo.carta_estilos_efetivos_v12(r.card_id);
   if not coalesce((f->>'pode_rodar')::boolean,false) or (f->>'ataque_id')::int<>r.ataque or (f->>'defesa_id')::int<>r.defesa then
    raise exception 'estilos da carta mudaram desde a auditoria'; end if;
  end loop;
  for r in select distinct funcao_id,posicao_id,ataque,defesa,novo_1,novo_2 from _estilos_v12_batch loop
   f:=clube_novo.conferir_bonus_estilo_0909_v1(r.funcao_id,r.posicao_id,r.ataque,r.defesa);
   if not coalesce((f->>'pode_calcular')::boolean,false) or (f->>'bonus_ataque')::numeric<>r.novo_1 or (f->>'bonus_defesa')::numeric<>r.novo_2 then
    raise exception 'regra mudou desde a auditoria'; end if;
  end loop;
  update _estilos_v12_batch a set resultado_novo_fingerprint=encode(extensions.digest(jsonb_build_object(
   'contrato','correcao-estilos-v12','linha',a.linha_id,'origem',b.resultado_fingerprint,
   'regua',v_regua->>'contrato_fingerprint','formula',v_regua->>'formula_fingerprint',
   'ataque',a.ataque,'defesa',a.defesa,'bonus_1',a.novo_1,'bonus_2',a.novo_2)::text,'sha256'),'hex')
  from clube_novo.build_bonificador b where b.id=a.antigo_id;
  insert into clube_novo.build_bonificador(
   bonus_pe,bonus_fisico_total,bonus_posicao,bonus_playstyle_1,bonus_playstyle_2,bonus_ia,bonus_outros,bonus_total,
   contrato_versao,contrato_fingerprint,carta_versao,carta_fingerprint,formula_fingerprint,resultado_fingerprint,
   concluido_em,bonus_fisico_detalhe,criado_em,motor_versao,b_corpo,b_pe_ruim,b_estilo,b_total,faltou,corpo_soma,corpo_pct,entrada_bonificador_fingerprint)
  select b.bonus_pe,b.bonus_fisico_total,b.bonus_posicao,a.novo_1,a.novo_2,b.bonus_ia,b.bonus_outros,
   round(b.bonus_total-b.bonus_playstyle_1-b.bonus_playstyle_2+a.novo_1+a.novo_2,4),
   'bonificador-regua-v4',v_regua->>'contrato_fingerprint',b.carta_versao,b.carta_fingerprint,v_regua->>'formula_fingerprint',a.resultado_novo_fingerprint,
   clock_timestamp(),b.bonus_fisico_detalhe,clock_timestamp(),'v12-0909-estilo-funcao-ativacao-v1',
   b.b_corpo,b.b_pe_ruim,a.novo_1+a.novo_2,round(b.b_total-b.b_estilo+a.novo_1+a.novo_2,4),
   b.faltou,b.corpo_soma,b.corpo_pct,b.entrada_bonificador_fingerprint
  from _estilos_v12_batch a join clube_novo.build_bonificador b on b.id=a.antigo_id
  on conflict(resultado_fingerprint) do nothing;
  update _estilos_v12_batch a set criado_id=b.id from clube_novo.build_bonificador b where b.resultado_fingerprint=a.resultado_novo_fingerprint;
  if exists(select 1 from _estilos_v12_batch where criado_id is null) then raise exception 'resultado novo ausente'; end if;
  -- Apenas o ponteiro atual muda. Os campos anteriores/snapshots historicos ficam intactos.
  update clube_novo.bonificador_correcao_item_v1 i set build_bonificador_id_novo=a.criado_id
  from _estilos_v12_batch a where not a.era_publicada and i.build_linha_card_id=a.linha_id and i.build_bonificador_id_novo=a.antigo_id;
  update clube_novo.build_linha_card l set build_bonificador_id=a.criado_id,
   bonificador_motor_versao='v12-0909-estilo-funcao-ativacao-v1',bonificador_contrato_versao='bonificador-regua-v4',
   snapshot_bonificador_fingerprint=a.resultado_novo_fingerprint
  from _estilos_v12_batch a where not a.era_publicada and l.id=a.linha_id and l.build_bonificador_id=a.antigo_id;
  update clube_novo.correcao_estilos_item_v12 i set novo_id=a.criado_id,
   resultado_novo_fingerprint=a.resultado_novo_fingerprint,corrigida_em=clock_timestamp(),
   estado=case when i.era_publicada then 'corrigida' else 'concluida' end,
   concluida_em=case when not i.era_publicada then clock_timestamp() end
  from _estilos_v12_batch a where i.linha_id=a.linha_id;
 end if;
 -- Republicacao em pequenos lotes. Todo erro fica registrado para parada visivel.
 for r in select * from clube_novo.correcao_estilos_item_v12
  where estado='corrigida' and (p_linhas is null or linha_id=any(p_linhas))
  order by linha_id limit least(greatest(coalesce(p_limite,20),1),20)
 loop
  begin
   perform 1 from clube_novo.build_linha_card where id=r.linha_id for update;
   if not exists(select 1 from clube_novo.build_linha_card l
    join clube_novo.build_publicacao_linha_ativa_v1 p on p.linha_id=l.id
    where l.id=r.linha_id and l.build_bonificador_id=r.antigo_id
     and p.build_bonificador_id=(r.publicacao_anterior->>'build_bonificador_id')::bigint
     and p.publicacao_fingerprint is not distinct from r.publicacao_anterior->>'publicacao_fingerprint'
     and exists(select 1 from clube_novo.build_bonificador bp
      join clube_novo.build_bonificador ba on ba.id=r.antigo_id
      where bp.id=p.build_bonificador_id
       and (bp.bonus_pe,bp.bonus_fisico_total,bp.bonus_posicao,bp.bonus_ia,bp.bonus_outros,bp.bonus_playstyle_1,bp.bonus_playstyle_2,bp.bonus_total)
        is not distinct from
        (ba.bonus_pe,ba.bonus_fisico_total,ba.bonus_posicao,ba.bonus_ia,ba.bonus_outros,ba.bonus_playstyle_1,ba.bonus_playstyle_2,ba.bonus_total))
     and l.build_otimizador_id is not distinct from r.otimizador_id
     and l.snapshot_otimizador_fingerprint is not distinct from r.otimizador_fingerprint
     and p.nota_final is not distinct from r.nota_anterior)
   then raise exception 'publicacao ou Otimizador mudou desde a auditoria'; end if;
   -- Troca dos ponteiros e da publicacao no MESMO bloco transacional.
   -- Ate a confirmacao, a publicacao antiga continua integralmente visivel.
   update clube_novo.bonificador_correcao_item_v1 set build_bonificador_id_novo=r.novo_id
    where build_linha_card_id=r.linha_id and build_bonificador_id_novo=r.antigo_id;
   update clube_novo.build_linha_card set build_bonificador_id=r.novo_id,
    bonificador_motor_versao='v12-0909-estilo-funcao-ativacao-v1',bonificador_contrato_versao='bonificador-regua-v4',
    snapshot_bonificador_fingerprint=r.resultado_novo_fingerprint
    where id=r.linha_id;
   f:=clube_novo.finalizar_publicar_linha_v1(r.linha_id,'correcao_estilos_v12');
   if f->>'estado' not in ('publicada','ja_publicada') then raise exception 'publicacao recusada: %',f; end if;
   if not exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 p
    join clube_novo.build_bonificador b on b.id=r.antigo_id
    where p.linha_id=r.linha_id and p.build_bonificador_id=r.novo_id
     and p.build_otimizador_id is not distinct from r.otimizador_id
     and p.nota_final=r.nota_anterior-b.bonus_playstyle_1-b.bonus_playstyle_2+r.novo_1+r.novo_2)
   then raise exception 'readback nao confirmou mudanca exclusiva de estilo'; end if;
   update clube_novo.correcao_estilos_item_v12 set estado='concluida',concluida_em=clock_timestamp(),erro=null where linha_id=r.linha_id;
   v_publicadas:=v_publicadas+1;
  exception when others then
   get stacked diagnostics v_erro=message_text;
   update clube_novo.correcao_estilos_item_v12 set estado='erro',erro=v_erro where linha_id=r.linha_id;
   exit;
  end;
 end loop;
 if not exists(select 1 from clube_novo.correcao_estilos_item_v12 where estado<>'concluida') then
  update clube_novo.correcao_estilos_execucao_v12 set concluida_em=coalesce(concluida_em,clock_timestamp())
   where id='estilos-funcao-20260909-v1' and concluida_em is null;
 end if;
 return public.correcao_estilos_status_v12()||jsonb_build_object('corrigidas_neste_lote',v_n,
  'publicadas_neste_lote',v_publicadas,'duracao_ms',round(extract(epoch from clock_timestamp()-v_inicio)*1000,2));
end $function$

