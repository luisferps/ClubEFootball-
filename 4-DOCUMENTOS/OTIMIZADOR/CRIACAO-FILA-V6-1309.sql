begin;
set local lock_timeout='10s';
do $guard$ begin
 if exists(select 1 from clube_novo.build_linha_card where lote_producao_id='12090000-0000-4000-8000-000000001209' and estado_otimizador='processando') then raise exception 'Fila antiga tem processamento ativo'; end if;
 if (select max(versao) from clube_novo.otimizador_molde)<>6 then raise exception 'Molde v6 obrigatório';end if;
 if exists(select 1 from jsonb_to_recordset(public.complemento_contexto_v14()->'pesos') as p(funcao_id bigint,codigo_atributo text,peso numeric) join clube_novo.otimizador_molde m using(funcao_id,codigo_atributo) where m.versao=6 and m.peso is distinct from p.peso) then raise exception 'Complemento divergente';end if;
end $guard$;
insert into clube_novo.otimizador_lote_aposentado_v1(lote_id,motivo,estado_anterior)
select id,'molde v6 e atualização física 13/09: fila integral substituta 39da8ff4-7a4a-4ec7-8641-e81b5677ad4c',estado
from clube_novo.otimizador_lote_producao_v3 where id='12090000-0000-4000-8000-000000001209';
update clube_novo.build_linha_card set estado_otimizador='interrompido',erro_otimizador='retirada: molde v6, fila refeita',otimizador_finalizado_em=clock_timestamp(),atualizado_em=clock_timestamp()
where lote_producao_id='12090000-0000-4000-8000-000000001209' and estado_otimizador='pendente';
select public.otimizador_producao_criar_lote_integral_v6('39da8ff4-7a4a-4ec7-8641-e81b5677ad4c','a1cc830af3366e2d0c9ac12138d892058b3e57ed216e43d68242d105b33cb9d2','otimizador-fila-producao-v3-local-20260909-habilidades-v12');
do $cond$ declare v_base bigint; v_ins integer; begin
select coalesce(max(ordem_candidata),0) into v_base from clube_novo.otimizador_lote_producao_candidata_v5 where lote_id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c';
insert into clube_novo.otimizador_lote_producao_candidata_v5(lote_id,card_id,ordem_candidata,overall_snapshot,carta_versao_snapshot)
select '39da8ff4-7a4a-4ec7-8641-e81b5677ad4c',c.card_id,v_base+row_number() over(order by case when coalesce(c.orcamento,0)>0 then 0 else 1 end,c.overall desc nulls last,c.card_id collate "C"),c.overall::integer,coalesce(c.extraido_em::text,'')
from clube_novo.carta_jogo c where coalesce(c.roda_motor,false) and coalesce(c.pode_rodar_vinculos,false)
and exists(select 1 from clube_novo.carta_impeto_jogo ci where ci.card_id=c.card_id and coalesce(ci.condicional,false))
and exists(select 1 from clube_novo.otimizador_prioridade_orcamento_v1 p where p.card_id=c.card_id)
and not exists(select 1 from clube_novo.otimizador_lote_producao_candidata_v5 k where k.lote_id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c' and k.card_id=c.card_id);
get diagnostics v_ins=row_count;
update clube_novo.otimizador_lote_producao_v3 set preparo_total=preparo_total+v_ins,excluidas_impeto_condicional=0,atualizado_em=clock_timestamp() where id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c';
end $cond$;
select id,estado,preparo_total from clube_novo.otimizador_lote_producao_v3 where id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c';
commit;
