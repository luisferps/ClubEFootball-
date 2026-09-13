-- Catalogo cadastral publico: sem motores, notas ou estado comercial inferido.
create function public.site_novo_boxes_v1(p_box text default null,p_busca text default '',p_limite integer default 24,p_offset integer default 0)
returns jsonb language plpgsql stable security definer set search_path='' set statement_timeout='5s' set jit=off
as $$
declare resultado jsonb;
begin
 if p_limite is null or p_limite<1 or p_limite>60 or p_offset is null or p_offset<0 or p_offset>100000 or p_busca is null or length(p_busca)>100 or length(p_box)>500 then
 raise exception 'Parametros invalidos' using errcode='22023'; end if;
 if p_box is null then
 with base as materialized (
 select c.card_id,c.nome,c.box,c.overall,c.posicao,c.foto_url_cloudinary
 from clube_novo.carta_jogo c where nullif(btrim(c.box),'') is not null
 ), grupos as (
 select box,count(*)::integer total_cards from base
 where strpos(lower(box),lower(btrim(p_busca)))>0 group by box
 ), pagina as (select * from grupos order by box collate "C" limit p_limite offset p_offset),
 itens as (
 select p.box,p.total_cards,coalesce((select jsonb_agg(to_jsonb(t) order by t.overall desc nulls last,t.card_id collate "C")
 from (select b.card_id,b.nome,b.posicao,b.overall,b.foto_url_cloudinary as foto_url from base b where b.box=p.box order by b.overall desc nulls last,b.card_id collate "C" limit 3)t),'[]'::jsonb) cards from pagina p
 )
 select jsonb_build_object('contrato','site-novo-boxes-v1','versao',1,'modo','boxes','box',null,'busca',p_busca,'total',(select count(*) from grupos),'total_cards',(select coalesce(sum(total_cards),0) from grupos),'limite',p_limite,'offset',p_offset,'itens',coalesce((select jsonb_agg(to_jsonb(i) order by i.box collate "C") from itens i),'[]'::jsonb)) into resultado;
 else
 with base as materialized (
 select c.card_id,c.nome,c.posicao,c.overall,c.foto_url_cloudinary as foto_url from clube_novo.carta_jogo c where c.box=p_box and nullif(btrim(c.box),'') is not null
 ), pagina as (select * from base order by overall desc nulls last,card_id collate "C" limit p_limite offset p_offset)
 select jsonb_build_object('contrato','site-novo-boxes-v1','versao',1,'modo','cards','box',p_box,'busca',p_busca,'total',(select count(*) from base),'total_cards',(select count(*) from base),'limite',p_limite,'offset',p_offset,'itens',coalesce((select jsonb_agg(to_jsonb(p) order by p.overall desc nulls last,p.card_id collate "C") from pagina p),'[]'::jsonb)) into resultado;
 end if;
 return resultado || jsonb_build_object('tem_mais',(resultado->>'total')::bigint>p_offset+p_limite,'status',case when jsonb_array_length(resultado->'itens')=0 then 'vazio' else 'pronto' end);
end $$;
revoke all on function public.site_novo_boxes_v1(text,text,integer,integer) from public;
grant execute on function public.site_novo_boxes_v1(text,text,integer,integer) to anon,authenticated,service_role;
comment on function public.site_novo_boxes_v1(text,text,integer,integer) is 'Leitura cadastral do Site Novo agrupada pelo nome exato carta_jogo.box; nao representa disponibilidade ou analise de contratacao.';
