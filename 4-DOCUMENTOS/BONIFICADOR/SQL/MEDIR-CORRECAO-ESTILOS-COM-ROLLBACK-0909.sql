-- MEDICAO REVERTIDA. NAO E UM MIGRADOR DE RESULTADOS.
do $bench$
declare
 r record; b clube_novo.build_bonificador%rowtype; e jsonb; s jsonb; f jsonb;
 id_novo bigint; t0 timestamptz; t1 timestamptz; t2 timestamptz; t3 timestamptz;
 rel jsonb:='[]'; novos bigint[]:='{}'; inicio timestamptz:=clock_timestamp();
begin
 begin
  for r in select l.id,l.card_id,l.funcao_id,l.posicao_id,l.build_bonificador_id,p.nota_final
    from clube_novo.build_linha_card l join clube_novo.build_publicacao_linha_ativa_v1 p on p.linha_id=l.id
    where l.id in (371187,371188,371193,371194,371199,371200,2569,2731,2570,2734,2543,2544,2545,2546,371328,371329,371331,371332,2563,2702,2564,2703,2705,2706,2707,2708,371151,371152,371157,371158,2567,2709,2568,2710,2880,2982,2881,2983) order by l.id
  loop
   t0:=clock_timestamp();
   select * into strict b from clube_novo.build_bonificador where id=r.build_bonificador_id;
   s:=clube_novo.carta_estilos_efetivos_v12(r.card_id);
   e:=clube_novo.conferir_bonus_estilo_0909_v1(r.funcao_id,r.posicao_id,(s->>'ataque_id')::int,(s->>'defesa_id')::int);
   if e->>'pode_calcular'<>'true' then raise exception 'estilo pendente'; end if;
   t1:=clock_timestamp();
   -- Selo V11 conservado APENAS nesta simulacao que sera revertida.
   -- Mede o caminho atual de publicacao sem ativar V12.
   insert into clube_novo.build_bonificador(
    bonus_pe,bonus_fisico_total,bonus_posicao,bonus_playstyle_1,bonus_playstyle_2,bonus_ia,bonus_outros,bonus_total,
    contrato_versao,contrato_fingerprint,carta_versao,carta_fingerprint,formula_fingerprint,resultado_fingerprint,
    concluido_em,bonus_fisico_detalhe,criado_em,motor_versao,b_corpo,b_pe_ruim,b_estilo,b_total,faltou,corpo_soma,corpo_pct,entrada_bonificador_fingerprint)
   values(b.bonus_pe,b.bonus_fisico_total,b.bonus_posicao,(e->>'bonus_ataque')::numeric,(e->>'bonus_defesa')::numeric,b.bonus_ia,b.bonus_outros,
    b.bonus_total-b.bonus_playstyle_1-b.bonus_playstyle_2+(e->>'bonus_total')::numeric,
    b.contrato_versao,b.contrato_fingerprint,b.carta_versao,b.carta_fingerprint,b.formula_fingerprint,
    encode(extensions.digest('benchmark-estilo-rollback:'||r.id||':'||clock_timestamp(),'sha256'),'hex'),
    clock_timestamp(),b.bonus_fisico_detalhe,clock_timestamp(),b.motor_versao,b.b_corpo,b.b_pe_ruim,(e->>'bonus_total')::numeric,
    b.b_total-b.b_estilo+(e->>'bonus_total')::numeric,b.faltou,b.corpo_soma,b.corpo_pct,b.entrada_bonificador_fingerprint)
   returning id into id_novo;
   novos:=array_append(novos,id_novo);
   perform set_config('clube_novo.finalizacao_linha_em_curso',r.id::text,true);
   update clube_novo.build_linha_card l set build_bonificador_id=id_novo,
    snapshot_bonificador_fingerprint=n.resultado_fingerprint
   from clube_novo.build_bonificador n where l.id=r.id and n.id=id_novo;
   t2:=clock_timestamp();
   f:=clube_novo.finalizar_publicar_linha_v1(r.id,'benchmark_estilos_desfeito_0909');
   if f->>'estado'<>'publicada' then raise exception 'benchmark publicacao recusada: %',f; end if;
   if (f->>'nota_final')::numeric is distinct from r.nota_final-b.bonus_playstyle_1-b.bonus_playstyle_2+(e->>'bonus_total')::numeric then
    raise exception 'nota publicada diverge da mudanca exclusiva de estilo';
   end if;
   t3:=clock_timestamp();
   rel:=rel||jsonb_build_array(jsonb_build_object('linha',r.id,'funcao',r.funcao_id,
    'calculo_ms',round(extract(epoch from t1-t0)*1000,2),
    'gravar_vincular_ms',round(extract(epoch from t2-t1)*1000,2),
    'publicar_ms',round(extract(epoch from t3-t2)*1000,2),
    'nota_simulada',f->'nota_final'));
  end loop;
  raise sqlstate 'PZ001' using message='desfazer benchmark completo';
 exception when sqlstate 'PZ001' then null;
 end;
 if exists(select 1 from clube_novo.build_bonificador where id=any(novos)) then raise exception 'rollback nao preservou resultados'; end if;
 perform set_config('clube_novo.resultado_benchmark_estilos',
  jsonb_build_object('simulacoes',rel,'total_ms',round(extract(epoch from clock_timestamp()-inicio)*1000,2),'desfeito',true)::text,true);
end $bench$;
select current_setting('clube_novo.resultado_benchmark_estilos')::jsonb medicao;
