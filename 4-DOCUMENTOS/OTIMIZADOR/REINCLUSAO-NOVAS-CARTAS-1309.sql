begin;
set local lock_timeout='10s';
select id from clube_novo.otimizador_lote_producao_v3 where id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c' for update;
do $f$ begin
 if exists(select 1 from clube_novo.otimizador_lote_producao_carta_v3 c join clube_novo.otimizador_lote_cartas_novas_v1 n using(lote_id,card_id) where c.lote_id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c') then raise exception 'Nova carta ja fotografada'; end if;
end $f$;
update clube_novo.carta_posicao_principal_jogo p set posicao_id=p.posicao_id
where not exists(select 1 from clube_novo.recalculo_1209_entrada_antes_v1 b where b.card_id=p.card_id);
update clube_novo.carta_playstyle_jogo p set valor_raw=p.valor_raw
where not exists(select 1 from clube_novo.recalculo_1209_entrada_antes_v1 b where b.card_id=p.card_id);
do $f$ begin
 if exists(select 1 from clube_novo.otimizador_lote_cartas_novas_v1 n where lote_id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c' and not coalesce((public.bonificador_carta_v2(n.card_id)->>'pode_rodar')::boolean,false)) then raise exception 'Nova carta ainda bloqueada'; end if;
end $f$;
with reset as(
 update clube_novo.otimizador_lote_producao_candidata_v5 c
 set estado='pendente',motivo=null,preparado_em=null,carta_versao_snapshot=j.extraido_em::text,atualizado_em=clock_timestamp()
 from clube_novo.otimizador_lote_cartas_novas_v1 n,clube_novo.carta_jogo j
 where c.lote_id=n.lote_id and c.card_id=n.card_id and j.card_id=c.card_id and c.estado='incompleta'
 and c.lote_id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c' returning 1
)
update clube_novo.otimizador_lote_producao_v3 set preparo_concluido=preparo_concluido-(select count(*) from reset),
 excluidas_incompletas=excluidas_incompletas-(select count(*) from reset),estado='preparando'
 where id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c';
select estado,count(*) n from clube_novo.otimizador_lote_producao_candidata_v5 c join clube_novo.otimizador_lote_cartas_novas_v1 n using(lote_id,card_id) where lote_id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c' group by estado;
commit;
