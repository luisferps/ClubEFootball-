-- Catalogo cadastral publico: sem motores, notas ou estado comercial inferido.
create function public.site_novo_boxes_em_andamento_v1(p_box text default null,p_busca text default '',p_limite integer default 24,p_offset integer default 0)
returns jsonb language plpgsql stable security definer set search_path='' set statement_timeout='5s' set jit=off
as $$
declare resultado jsonb;
begin
 if p_limite is null or p_limite<1 or p_limite>60 or p_offset is null or p_offset<0 or p_offset>100000 or p_busca is null or length(p_busca)>100 or length(p_box)>500 then
 raise exception 'Parametros invalidos' using errcode='22023'; end if;
 if p_box is null then
 with avaliadas as materialized (
 select b.card_id,b.linha_id,b.funcao_id,b.funcao_nome,b.posicao_codigo,b.percentual_topo,b.overall_final,
 row_number() over(partition by b.card_id,b.funcao_id order by b.percentual_topo desc,b.linha_id) rn
 from clube_novo.build_pontuacao_final_v2_publica_v1 b
 where exists(select 1 from clube_novo.box_card_em_andamento_v1 m where m.card_id=b.card_id)
 and b.percentual_topo is not null and b.percentual_topo::text not in ('NaN','Infinity','-Infinity')
 ), base as materialized (
 select c.card_id,c.nome,x.box_nome as box,c.overall,c.posicao,c.foto_url_cloudinary,
 coalesce((select jsonb_agg(jsonb_build_object('linha_id',v.linha_id::text,'funcao',v.funcao_nome,'posicao',v.posicao_codigo,'pontuacao',v.overall_final,'percentual_topo',v.percentual_topo,'etiqueta',et.item->>'etiqueta_rotulo','codigo',et.item->>'etiqueta_codigo','regua_versao',et.item->>'regua_versao') order by v.percentual_topo desc,v.linha_id)
 from avaliadas v cross join lateral jsonb_array_elements(clube_novo.contratacoes_por_box_build_v1(v.card_id,v.funcao_nome,v.percentual_topo)) et(item)
 where v.card_id=c.card_id and v.rn=1 and et.item->>'box_id'=x.box_id::text and et.item->>'estado_box'='em_andamento'),'[]'::jsonb) analises
 from clube_novo.box_contexto_contratacao_v1 x join clube_novo.box_card_em_andamento_v1 m on m.box_id=x.box_id join clube_novo.carta_jogo c on c.card_id=m.card_id
 where x.estado_box='em_andamento'
 ), grupos as (
 select box,count(*)::integer total_cards from base
 where strpos(lower(box),lower(btrim(p_busca)))>0 group by box
 ), pagina as (select * from grupos order by box collate "C" limit p_limite offset p_offset),
 itens as (
 select p.box,p.total_cards,coalesce((select jsonb_agg(to_jsonb(t) order by t.overall desc nulls last,t.card_id collate "C")
 from (select b.card_id,b.nome,b.posicao,b.overall,b.foto_url_cloudinary as foto_url,b.analises from base b where b.box=p.box order by b.overall desc nulls last,b.card_id collate "C" limit 3)t),'[]'::jsonb) cards from pagina p
 )
 select jsonb_build_object('contrato','site-novo-boxes-v1','versao',1,'modo','boxes','box',null,'busca',p_busca,'total',(select count(*) from grupos),'total_cards',(select coalesce(sum(total_cards),0) from grupos),'limite',p_limite,'offset',p_offset,'itens',coalesce((select jsonb_agg(to_jsonb(i) order by i.box collate "C") from itens i),'[]'::jsonb)) into resultado;
 else
 with avaliadas as materialized (
 select b.card_id,b.linha_id,b.funcao_id,b.funcao_nome,b.posicao_codigo,b.percentual_topo,b.overall_final,
 row_number() over(partition by b.card_id,b.funcao_id order by b.percentual_topo desc,b.linha_id) rn
 from clube_novo.build_pontuacao_final_v2_publica_v1 b
 where exists(select 1 from clube_novo.box_card_em_andamento_v1 m where m.card_id=b.card_id)
 and b.percentual_topo is not null and b.percentual_topo::text not in ('NaN','Infinity','-Infinity')
 ), base as materialized (
 select c.card_id,c.nome,x.box_nome as box,c.overall,c.posicao,c.foto_url_cloudinary,
 coalesce((select jsonb_agg(jsonb_build_object('linha_id',v.linha_id::text,'funcao',v.funcao_nome,'posicao',v.posicao_codigo,'pontuacao',v.overall_final,'percentual_topo',v.percentual_topo,'etiqueta',et.item->>'etiqueta_rotulo','codigo',et.item->>'etiqueta_codigo','regua_versao',et.item->>'regua_versao') order by v.percentual_topo desc,v.linha_id)
 from avaliadas v cross join lateral jsonb_array_elements(clube_novo.contratacoes_por_box_build_v1(v.card_id,v.funcao_nome,v.percentual_topo)) et(item)
 where v.card_id=c.card_id and v.rn=1 and et.item->>'box_id'=x.box_id::text and et.item->>'estado_box'='em_andamento'),'[]'::jsonb) analises
 from clube_novo.box_contexto_contratacao_v1 x join clube_novo.box_card_em_andamento_v1 m on m.box_id=x.box_id join clube_novo.carta_jogo c on c.card_id=m.card_id
 where x.estado_box='em_andamento'
 ), selecionadas as (select card_id,nome,posicao,overall,foto_url_cloudinary as foto_url,analises from base where box=p_box), pagina as (select * from selecionadas order by overall desc nulls last,card_id collate "C" limit p_limite offset p_offset)
 select jsonb_build_object('contrato','site-novo-boxes-v1','versao',1,'modo','cards','box',p_box,'busca',p_busca,'total',(select count(*) from selecionadas),'total_cards',(select count(*) from selecionadas),'limite',p_limite,'offset',p_offset,'itens',coalesce((select jsonb_agg(to_jsonb(p) order by p.overall desc nulls last,p.card_id collate "C") from pagina p),'[]'::jsonb)) into resultado;
 end if;
 return resultado || jsonb_build_object('tem_mais',(resultado->>'total')::bigint>p_offset+p_limite,'status',case when jsonb_array_length(resultado->'itens')=0 then 'vazio' else 'pronto' end);
end $$;
revoke all on function public.site_novo_boxes_em_andamento_v1(text,text,integer,integer) from public;
grant execute on function public.site_novo_boxes_em_andamento_v1(text,text,integer,integer) to anon,authenticated,service_role;
comment on function public.site_novo_boxes_em_andamento_v1(text,text,integer,integer) is 'Boxes em andamento do contexto oficial e avaliacoes da regua existente, por funcao publicada.';
