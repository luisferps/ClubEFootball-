begin;
set local statement_timeout='120s';
set local lock_timeout='10s';
do $f$ declare v clube_novo.otimizador_lote_producao_v3%rowtype; begin
 select * into v from clube_novo.otimizador_lote_producao_v3 where id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c' for update;
 if v.estado<>'parado' or v.preparo_concluido<>v.preparo_total or v.pode_publicar then raise exception 'preparo nao encerrado'; end if;
 if exists(select 1 from clube_novo.build_linha_card where lote_producao_id=v.id and estado_otimizador<>'pendente') then raise exception 'lote ja processado'; end if;
end $f$;
create temp table prioridade_final on commit drop as
 select * from clube_novo.otimizador_fila_prioridade_v1 where lote_id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c';
create unique index on prioridade_final(linha_id);
do $f$ begin
 if exists(select 1 from clube_novo.otimizador_lote_producao_linha_v3 q
 join clube_novo.otimizador_prioridade_orcamento_v1 p on p.card_id=q.card_id
 where q.lote_id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c' and not exists(select 1 from prioridade_final f where f.linha_id=q.linha_id)) then raise exception 'linha com evidencia excluida por outra divergencia'; end if;
 if (select count(distinct card_id) from prioridade_final where prioridade_grupo=0)<>176 then raise exception 'novas cartas incompletas'; end if;
end $f$;
update clube_novo.build_linha_card l set estado_otimizador='interrompido',
 erro_otimizador='retirada: carta sem evidencia fisica coerente de nivel e orcamento',
 otimizador_finalizado_em=clock_timestamp(),atualizado_em=clock_timestamp()
 where l.lote_producao_id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c'
 and not exists(select 1 from prioridade_final p where p.linha_id=l.id);
create temp table ordem_final on commit drop as
 select q.linha_id,row_number() over(order by coalesce(p.prioridade_grupo,3),
 p.overall_prioridade desc nulls last,q.card_id collate "C",l.funcao_id,l.posicao_id,
 l.impeto_condicional_codigo nulls first,l.impeto_condicional_nivel nulls first,q.linha_id) ordem
 from clube_novo.otimizador_lote_producao_linha_v3 q
 join clube_novo.build_linha_card l on l.id=q.linha_id
 left join prioridade_final p on p.linha_id=q.linha_id
 where q.lote_id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c';
update clube_novo.otimizador_lote_producao_linha_v3 set ordem_fila=ordem_fila+100000000
 where lote_id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c';
update clube_novo.otimizador_lote_producao_linha_v3 q set ordem_fila=n.ordem
 from ordem_final n where q.lote_id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c' and q.linha_id=n.linha_id;
do $f$ declare v clube_novo.otimizador_lote_producao_v3%rowtype; fp text; begin
 select * into v from clube_novo.otimizador_lote_producao_v3 where id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c';
 select encode(extensions.digest(convert_to(
 v.id::text||':'||v.formula_fingerprint||':'||v.contrato_fingerprint||':'||v.motor_versao||':'||
 string_agg(q.card_id||':'||l.funcao_id::text||':'||l.posicao_id::text||':'||q.ordem_fila::text,',' order by q.ordem_fila),
 'UTF8'),'sha256'),'hex') into fp
 from clube_novo.otimizador_lote_producao_linha_v3 q join clube_novo.build_linha_card l on l.id=q.linha_id where q.lote_id=v.id;
 update clube_novo.otimizador_lote_producao_v3 set fingerprint=fp,preparo_fingerprint_final=fp,atualizado_em=clock_timestamp() where id=v.id;
 perform public.otimizador_producao_controlar_lote_v3(v.id,'iniciar');
 perform public.otimizador_producao_controlar_lote_v3(v.id,'pausar');
end $f$;
select prioridade_grupo,count(distinct card_id) cards,count(*) linhas,min(overall_prioridade) overall_min,max(overall_prioridade) overall_max from prioridade_final group by prioridade_grupo order by prioridade_grupo;
commit;
