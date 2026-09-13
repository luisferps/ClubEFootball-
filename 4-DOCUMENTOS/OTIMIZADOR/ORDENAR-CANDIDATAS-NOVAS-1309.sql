begin; set local lock_timeout='30s';
select id from clube_novo.otimizador_lote_producao_v3 where id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c' for update;
update clube_novo.otimizador_lote_producao_candidata_v5 set ordem_candidata=ordem_candidata+100000000 where lote_id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c';
with ranked as (
select k.card_id,coalesce(c.overall,n.overall_extraido)::integer overall,
row_number() over(order by case when n.card_id is not null then 0 when coalesce(c.orcamento,0)>0 then 1 else 2 end,coalesce(c.overall,n.overall_extraido) desc nulls last,k.card_id collate "C") ordem
from clube_novo.otimizador_lote_producao_candidata_v5 k join clube_novo.carta_jogo c using(card_id)
left join clube_novo.otimizador_lote_cartas_novas_v1 n on n.lote_id=k.lote_id and n.card_id=k.card_id where k.lote_id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c')
update clube_novo.otimizador_lote_producao_candidata_v5 k set ordem_candidata=r.ordem,overall_snapshot=r.overall from ranked r where k.lote_id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c' and k.card_id=r.card_id;
select k.ordem_candidata,c.nome,k.overall_snapshot,n.card_id is not null as nova
from clube_novo.otimizador_lote_producao_candidata_v5 k join clube_novo.carta_jogo c using(card_id) left join clube_novo.otimizador_lote_cartas_novas_v1 n on n.lote_id=k.lote_id and n.card_id=k.card_id
where k.lote_id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c' order by k.ordem_candidata limit 5; commit;
