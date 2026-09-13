do $fechar$
declare r jsonb;
begin
 perform pg_advisory_xact_lock(hashtextextended('correcao-estilos-v12-executor',0));
 perform 1 from clube_novo.build_linha_card where id=any(array[403298,403305,403306,403307,403308,403309,403310,403323,403328]) order by id for update;
 if (select count(*) from clube_novo.correcao_estilos_item_v12 where estado='corrigida' and linha_id=any(array[403298,403305,403306,403307,403308,403309,403310,403323,403328]))<>9 then raise exception 'O conjunto pendente mudou'; end if;
 insert into clube_novo.build_finalizacao_evento_v1(linha_id,evento,detalhe)
 select a.linha_id,'arquivo_antes_fechamento_manual_estilos_v12',jsonb_build_object('correcao',to_jsonb(a),'linha',to_jsonb(l),'publicacao',to_jsonb(p),'delta',to_jsonb(d),'finalizacao',to_jsonb(f),'fila_otimizador',(select jsonb_agg(to_jsonb(q)) from clube_novo.otimizador_lote_producao_linha_v3 q where q.linha_id=a.linha_id),'item_bonificador',(select jsonb_agg(to_jsonb(i)) from clube_novo.bonificador_correcao_item_v1 i where i.build_linha_card_id=a.linha_id))
 from clube_novo.correcao_estilos_item_v12 a join clube_novo.build_linha_card l on l.id=a.linha_id join clube_novo.build_publicacao_linha_ativa_v1 p on p.linha_id=a.linha_id join clube_novo.build_pontuacao_final_v2_delta_v1 d on d.linha_id=a.linha_id left join clube_novo.build_finalizacao_fila_v1 f on f.linha_id=a.linha_id where a.linha_id=any(array[403298,403305,403306,403307,403308,403309,403310,403323,403328])
 and not exists(select 1 from clube_novo.build_finalizacao_evento_v1 e where e.linha_id=a.linha_id and e.evento='arquivo_antes_fechamento_manual_estilos_v12');
 r:=public.correcao_estilos_tick_v12(20,array[403307,403308,403328]::bigint[]);
 if (r->>'publicadas_neste_lote')::int<>3 or (r->>'erros')::int<>0 then raise exception 'Tres publicacoes nao confirmadas: %',r; end if;
 update clube_novo.correcao_estilos_execucao_v12 set auditoria=auditoria||jsonb_build_object('fechamento_manual',jsonb_build_object('autorizado_pelo_usuario',true,'iniciado_em',clock_timestamp(),'linhas',to_jsonb(array[403298,403305,403306,403307,403308,403309,403310,403323,403328]),'confirmadas_pelo_executor',to_jsonb(array[403307,403308,403328]),'fila_otimizador_preservada',true)) where id='estilos-funcao-20260909-v1';
end $fechar$;
select public.correcao_estilos_status_v12() as status;
