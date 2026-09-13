begin;
with ofertas as(select value b from jsonb_array_elements($j$[{"referencia":"https://efhub.com/pt-BR/new-players","titulo":"National Teams Selection 10 Sep '26","cards":["105874165112743","105874165182687","105874165183676","105874165184248","105874165188527","105874165191335","105874165191683","105874165198697","105874165198910","105874165213340","105874165214108"],"agente_id":1366},{"referencia":"https://efhub.com/pt-BR/new-players","titulo":"Anticipated Standouts 26-27","cards":["105880876076204","105880876084074","105880876084697","105880876086992","105880876091925","105880876118884","105880876119249","105880876137536"],"agente_id":1367},{"referencia":"https://efhub.com/packs/potm-brasileir-o-betano-27-aug-26","titulo":"POTM Brasileirão Betano 27 Aug '26","cards":["53990691741940","53990691759915","53990691764136","53990691828711","53990691853358","53990691863762"],"agente_id":1357}]$j$::jsonb))
insert into clube_novo.box_card_em_andamento_v1(box_id,card_id,capturado_em)
select x.box_id,c.card_id,now() from ofertas o join clube_novo.box_contexto_contratacao_v1 x on x.agente_jogo_id=(o.b->>'agente_id')::bigint
cross join lateral jsonb_array_elements_text(o.b->'cards') c(card_id)
join clube_novo.carta_jogo j on j.card_id=c.card_id
on conflict do nothing;
insert into clube_novo.valor_do_dono(destino_schema,destino_tabela,chave,coluna,valor,porque)
select 'clube_novo','box_card_em_andamento_v1',jsonb_build_object('box_id',m.box_id,'card_id',m.card_id),
'capturado_em',to_jsonb(m.capturado_em),'Correcao pontual autorizada em 13/09: vinculo conferido na referencia eFHUB, ID fisico e oferta do jogo; preservar esta associacao.'
from clube_novo.box_card_em_andamento_v1 m join clube_novo.box_contexto_contratacao_v1 x using(box_id)
where x.agente_jogo_id in(1357,1366,1367)
and not exists(select 1 from clube_novo.valor_do_dono v where v.destino_tabela='box_card_em_andamento_v1' and v.chave=jsonb_build_object('box_id',m.box_id,'card_id',m.card_id) and v.coluna='capturado_em');
insert into clube_novo.box_card_em_andamento_v1(box_id,card_id,capturado_em)
select target.box_id,m.card_id,now() from (values(1351::bigint,18::bigint),(1362,2266),(1363,2268)) a(agente,origem)
join clube_novo.box_contexto_contratacao_v1 target on target.agente_jogo_id=a.agente
join clube_novo.box_card_em_andamento_v1 m on m.box_id=a.origem
on conflict do nothing;
commit;
