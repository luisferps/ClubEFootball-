CREATE OR REPLACE FUNCTION clube_novo.site_novo_boxes_melhores_linhas_v1(p_cards text[],p_degrau integer)
RETURNS TABLE(card_id text,analises jsonb) LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO '' AS $$
with fonte as not materialized (
 select a.card_id,a.linha_id,a.funcao_id,a.posicao_id,a.build_otimizador_id,a.nota_final,a.impeto_condicional_codigo,a.impeto_condicional_nivel
 from clube_novo.build_publicacao_exibivel_v3 a where a.nota_final::text not in ('NaN','Infinity','-Infinity')
), topos as materialized (
 select f.id funcao_id,t.nota_final topo from clube_novo.funcao_sistema f
 cross join lateral (select a.nota_final from clube_novo.build_publicacao_exibivel_v3 a
 where a.funcao_id=f.id and a.nota_final::text not in ('NaN','Infinity','-Infinity')
 order by a.nota_final desc,a.linha_id limit 1) t
),
melhores as (
 select distinct on (a.card_id) a.* from fonte a where a.card_id=any(p_cards)
 and (a.impeto_condicional_codigo is null or a.impeto_condicional_nivel=p_degrau)
 order by a.card_id,a.nota_final desc,a.linha_id
)
select a.card_id,jsonb_build_array(jsonb_build_object('linha_id',a.linha_id::text,'funcao',f.rotulo,'posicao',p.codigo_pt,
'pontuacao',a.nota_final,'regua_vigente',(bo.contrato_fingerprint=rv.contrato_fingerprint),'percentual_topo',100*a.nota_final/t.topo,
'codigo',r.codigo,'etiqueta',r.rotulo,'regua_versao',r.regua_versao))
from melhores a left join clube_novo.build_otimizador bo on bo.id=a.build_otimizador_id cross join clube_novo.regua_vigente_v1 rv join topos t on t.funcao_id=a.funcao_id and t.topo>0
join clube_novo.funcao_sistema f on f.id=a.funcao_id join clube_novo.posicao_jogo p on p.id=a.posicao_id
cross join lateral (
 select r.* from clube_novo.regua_contratacao_faixa_v1 r join clube_novo.regua_contratacao_versao_v1 v on v.versao=r.regua_versao and v.estado='vigente'
 where 100*a.nota_final/t.topo>=r.percentual_minimo order by r.percentual_minimo desc limit 1
) r;
$$;
REVOKE ALL ON FUNCTION clube_novo.site_novo_boxes_melhores_linhas_v1(text[],integer) FROM PUBLIC;
CREATE OR REPLACE FUNCTION clube_novo.site_novo_boxes_calculo_v1(p_box text DEFAULT NULL::text, p_busca text DEFAULT ''::text, p_limite integer DEFAULT 24, p_offset integer DEFAULT 0, p_ordem text DEFAULT 'recentes'::text, p_degrau integer DEFAULT 3)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
 SET statement_timeout TO '10s'
 SET jit TO 'off'
 SET plan_cache_mode TO 'force_custom_plan'
 SET work_mem TO '16MB'
AS $function$
declare resultado jsonb;
begin
  if p_degrau is null or p_degrau not in (1,2,3) then
    raise exception 'Degrau invalido' using errcode='22023';
  end if;
  if p_limite is null or p_limite not between 1 and 60
     or p_offset is null or p_offset not between 0 and 100000
     or p_busca is null or length(p_busca)>100 or length(p_box)>500
     or p_ordem is null or p_ordem not in ('recentes','pontuacao') then
    raise exception 'Parametros invalidos' using errcode='22023';
  end if;

  if p_box is null and p_ordem='recentes' then
    with vinculos as materialized (
      select distinct on (x.box_nome,x.card_id)
        x.card_id,x.box_id,x.box_nome as box,x.data_oferta
      from clube_novo.carta_box_oferta_v1 x
      where x.estado_box in ('finalizada','cadastrada')
        and not exists(
          select 1 from clube_novo.carta_box_oferta_v1 a
          where a.estado_box='em_andamento' and a.box_nome=x.box_nome
        )
      order by x.box_nome,x.card_id,x.box_id desc
    ),
    catalogo as materialized (
      select v.box,count(*)::integer total_cards,max(v.data_oferta) data_oferta
      from vinculos v
      where btrim(p_busca)=''
        or clube_novo.site_novo_texto_corresponde_v1(v.box,p_busca)
        or exists(
          select 1 from vinculos vb
          join clube_novo.carta_jogo cb on cb.card_id=vb.card_id
          where vb.box=v.box
            and clube_novo.site_novo_texto_corresponde_v1(cb.nome,p_busca)
        )
      group by v.box
    ),
    ordenadas as (
      select *,row_number() over(order by data_oferta desc nulls last,box collate "C") ordem
      from catalogo
    ),
    pagina_boxes as materialized (
      select * from ordenadas order by ordem limit p_limite offset p_offset
    ),
    cards_pagina as materialized (
      select v.* from vinculos v join pagina_boxes p on p.box=v.box
    ),
    notas as materialized (
 select m.card_id,m.analises,(m.analises#>>'{0,pontuacao}')::numeric pontuacao_maxima,(m.analises#>>'{0,regua_vigente}')::boolean regua_vigente
 from clube_novo.site_novo_boxes_melhores_linhas_v1((select array_agg(distinct card_id) from cards_pagina),p_degrau) m
    ),
    base_pagina as materialized (
      select v.card_id,v.box_id,c.nome,v.box,c.overall,
        (select pj.codigo_pt
         from clube_novo.carta_posicao_principal_jogo cp
         join clube_novo.posicao_jogo pj on pj.id=cp.posicao_id
         where cp.card_id=c.card_id order by cp.posicao_id limit 1) as posicao,
        c.foto_url_cloudinary as foto_url,n.pontuacao_maxima,n.regua_vigente,coalesce(n.analises,'[]'::jsonb) analises
      from cards_pagina v
      join clube_novo.carta_jogo c on c.card_id=v.card_id
      left join notas n on n.card_id=v.card_id
    ),
    itens_boxes as (
      select p.box,p.total_cards,max(b.pontuacao_maxima) melhor_pontuacao,p.data_oferta,
        coalesce(to_char(p.data_oferta,'DD/MM/YYYY'),'Data não informada') data_rotulo,p.ordem,
        (select jsonb_agg(to_jsonb(t)-'ordem_card'-'box_id' order by t.ordem_card)
         from (
           select bp.card_id,bp.nome,bp.posicao,bp.overall,bp.foto_url,bp.pontuacao_maxima,bp.regua_vigente,
             bp.analises analises,
             row_number() over(order by
               clube_novo.contratacao_estrelas_v1(bp.analises#>>'{0,codigo}') desc nulls last,
               (bp.analises#>>'{0,pontuacao}')::numeric desc nulls last,bp.card_id collate "C") ordem_card
           from base_pagina bp where bp.box=p.box order by ordem_card limit 3
         ) t) cards
      from pagina_boxes p
      join base_pagina b on b.box=p.box
      group by p.box,p.total_cards,p.data_oferta,p.ordem
    )
    select jsonb_build_object(
      'contrato','site-novo-boxes-v1','versao',1,'degrau',p_degrau,'modo','boxes',
      'box',null,'busca',p_busca,'ordem',p_ordem,'limite',p_limite,'offset',p_offset,
      'total',(select count(*) from catalogo),
      'total_cards',(select coalesce(sum(total_cards),0) from catalogo),
      'itens',coalesce((select jsonb_agg(to_jsonb(i)-'ordem' order by i.ordem) from itens_boxes i),'[]'::jsonb)
    ) into resultado;

  elsif p_box is not null then
    with vinculos as materialized (
      select distinct on (x.box_nome,x.card_id)
        x.card_id,x.box_id,x.box_nome as box,x.data_oferta
      from clube_novo.carta_box_oferta_v1 x
      where x.box_nome=p_box
        and x.estado_box in ('finalizada','cadastrada')
        and not exists(
          select 1 from clube_novo.carta_box_oferta_v1 a
          where a.estado_box='em_andamento' and a.box_nome=x.box_nome
        )
      order by x.box_nome,x.card_id,x.box_id desc
    ),
    notas as materialized (
 select m.card_id,m.analises,(m.analises#>>'{0,pontuacao}')::numeric pontuacao_maxima,(m.analises#>>'{0,regua_vigente}')::boolean regua_vigente
 from clube_novo.site_novo_boxes_melhores_linhas_v1((select array_agg(distinct card_id) from vinculos),p_degrau) m
    ),
    cards_box as materialized (
      select v.card_id,v.box_id,c.nome,
        (select pj.codigo_pt
         from clube_novo.carta_posicao_principal_jogo cp
         join clube_novo.posicao_jogo pj on pj.id=cp.posicao_id
         where cp.card_id=c.card_id order by cp.posicao_id limit 1) as posicao,
        c.overall,c.foto_url_cloudinary as foto_url,n.pontuacao_maxima,n.regua_vigente,
        coalesce(n.analises,'[]'::jsonb) analises,
        row_number() over(order by clube_novo.contratacao_estrelas_v1(n.analises#>>'{0,codigo}') desc nulls last,(n.analises#>>'{0,pontuacao}')::numeric desc nulls last,v.card_id collate "C") ordem_card
      from vinculos v
      join clube_novo.carta_jogo c on c.card_id=v.card_id
      left join notas n on n.card_id=v.card_id
    ),
    pagina_cards as (
      select * from cards_box order by ordem_card limit p_limite offset p_offset
    )
    select jsonb_build_object(
      'contrato','site-novo-boxes-v1','versao',1,'degrau',p_degrau,'modo','cards',
      'box',p_box,'busca',p_busca,'ordem',p_ordem,'limite',p_limite,'offset',p_offset,
      'total',(select count(*) from cards_box),'total_cards',(select count(*) from cards_box),
      'itens',coalesce((select jsonb_agg(to_jsonb(i)-'ordem_card'-'box_id' order by i.ordem_card) from pagina_cards i),'[]'::jsonb)
    ) into resultado;

  else
    -- Ordenar todas as boxes por pontuacao exige ler as notas de todo o catalogo.
    with notas_fonte as materialized (
 select a.card_id,a.nota_final,a.impeto_condicional_codigo,a.impeto_condicional_nivel from clube_novo.build_publicacao_exibivel_v3 a
), notas as materialized (
 select a.card_id,max(a.nota_final) pontuacao_maxima from notas_fonte a
 where (a.impeto_condicional_codigo is null or a.impeto_condicional_nivel=p_degrau)
 and a.nota_final::text not in ('NaN','Infinity','-Infinity') group by a.card_id
    ),
    base as materialized (
      select distinct on (x.box_nome,c.card_id)
        c.card_id,x.box_id,c.nome,x.box_nome as box,c.overall,
        (select pj.codigo_pt
         from clube_novo.carta_posicao_principal_jogo cp
         join clube_novo.posicao_jogo pj on pj.id=cp.posicao_id
         where cp.card_id=c.card_id order by cp.posicao_id limit 1) as posicao,
        c.foto_url_cloudinary as foto_url,n.pontuacao_maxima,x.data_oferta
      from clube_novo.carta_box_oferta_v1 x
      join clube_novo.carta_jogo c using(card_id)
      left join notas n using(card_id)
      where x.estado_box in ('finalizada','cadastrada')
        and not exists(
          select 1 from clube_novo.carta_box_oferta_v1 a
          where a.estado_box='em_andamento' and a.box_nome=x.box_nome
        )
      order by x.box_nome,c.card_id,x.box_id desc
    ),
    catalogo as materialized (
      select box,count(*)::integer total_cards,max(pontuacao_maxima) melhor_pontuacao,max(data_oferta) data_oferta
      from base
      group by box
      having clube_novo.site_novo_texto_corresponde_v1(box,p_busca)
        or bool_or(clube_novo.site_novo_texto_corresponde_v1(nome,p_busca))
    ),
    ordenadas as (
      select *,row_number() over(order by melhor_pontuacao desc nulls last,data_oferta desc nulls last,box collate "C") ordem
      from catalogo
    ),
    pagina_boxes as materialized (
      select * from ordenadas order by ordem limit p_limite offset p_offset
    ),
    analises_pagina as materialized (
 select * from clube_novo.site_novo_boxes_melhores_linhas_v1(
 (select array_agg(distinct b.card_id) from base b join pagina_boxes p on p.box=b.box),p_degrau)
    ),
    itens_boxes as (
      select p.box,p.total_cards,p.melhor_pontuacao,p.data_oferta,
        coalesce(to_char(p.data_oferta,'DD/MM/YYYY'),'Data não informada') data_rotulo,p.ordem,
        (select jsonb_agg(to_jsonb(t)-'ordem_card'-'box_id' order by t.ordem_card)
         from (
           select b.card_id,b.box_id,b.nome,b.posicao,b.overall,b.foto_url,b.pontuacao_maxima,
             coalesce(ap.analises,'[]'::jsonb) analises,
             row_number() over(order by
               clube_novo.contratacao_estrelas_v1(coalesce(ap.analises,'[]'::jsonb)#>>'{0,codigo}') desc nulls last,
               (coalesce(ap.analises,'[]'::jsonb)#>>'{0,pontuacao}')::numeric desc nulls last,b.card_id collate "C") ordem_card
           from base b left join analises_pagina ap on ap.card_id=b.card_id where b.box=p.box order by ordem_card limit 3
         ) t) cards
      from pagina_boxes p
    )
    select jsonb_build_object(
      'contrato','site-novo-boxes-v1','versao',1,'degrau',p_degrau,'modo','boxes',
      'box',null,'busca',p_busca,'ordem',p_ordem,'limite',p_limite,'offset',p_offset,
      'total',(select count(*) from catalogo),
      'total_cards',(select coalesce(sum(total_cards),0) from catalogo),
      'itens',coalesce((select jsonb_agg(to_jsonb(i)-'ordem' order by i.ordem) from itens_boxes i),'[]'::jsonb)
    ) into resultado;
  end if;

  return resultado || jsonb_build_object(
    'regua',(
      select coalesce(jsonb_agg(jsonb_build_object(
        'codigo',f.codigo,'rotulo',f.rotulo,'percentual_minimo',f.percentual_minimo
      ) order by f.ordem),'[]'::jsonb)
      from clube_novo.regua_contratacao_faixa_v1 f
      join clube_novo.regua_contratacao_versao_v1 v
        on v.versao=f.regua_versao and v.estado='vigente'
    ),
    'tem_mais',(resultado->>'total')::bigint>p_offset+p_limite,
    'status',case when jsonb_array_length(resultado->'itens')=0 then 'vazio' else 'pronto' end
  );
end
$function$;
CREATE OR REPLACE FUNCTION clube_novo.site_novo_boxes_em_andamento_calculo_v1(p_box text DEFAULT NULL::text, p_busca text DEFAULT ''::text, p_limite integer DEFAULT 24, p_offset integer DEFAULT 0, p_degrau integer DEFAULT 3)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
 SET statement_timeout TO '10s'
 SET jit TO 'off'
 SET plan_cache_mode TO 'force_custom_plan'
 SET work_mem TO '16MB'
AS $function$
declare resultado jsonb;
begin
  if p_degrau is null or p_degrau not in (1,2,3) then
    raise exception 'Degrau invalido' using errcode='22023';
  end if;
  if p_limite is null or p_limite<1 or p_limite>60
     or p_offset is null or p_offset<0 or p_offset>100000
     or p_busca is null or length(p_busca)>100 or length(p_box)>500 then
    raise exception 'Parametros invalidos' using errcode='22023';
  end if;

  if p_box is null then
    with ofertas as materialized (
 select distinct m.card_id,x.box_nome from clube_novo.box_card_em_andamento_v1 m
 join clube_novo.box_contexto_contratacao_v1 x on x.box_id=m.box_id
 where x.estado_box='em_andamento' and x.oferta_fonte is not null and nullif(btrim(x.box_nome),'') is not null
 and (p_box is null or x.box_nome=p_box)
), notas as materialized (
 select * from clube_novo.site_novo_boxes_melhores_linhas_v1((select array_agg(distinct card_id) from ofertas),p_degrau)
), base as materialized (
 select c.card_id,c.nome,x.box_nome as box,c.overall,
 (select p.codigo_pt from clube_novo.carta_posicao_principal_jogo cp join clube_novo.posicao_jogo p on p.id=cp.posicao_id where cp.card_id=c.card_id order by cp.posicao_id limit 1) posicao,
 c.foto_url_cloudinary,(n.analises#>>'{0,pontuacao}')::numeric pontuacao_maxima,
 (n.analises#>>'{0,regua_vigente}')::boolean regua_vigente,coalesce(n.analises,'[]'::jsonb) analises
 from ofertas x join clube_novo.carta_jogo c on c.card_id=x.card_id left join notas n on n.card_id=x.card_id
),
    grupos as (
      select box,count(*)::integer total_cards,
        max((analises#>>'{0,percentual_topo}')::numeric) melhor_percentual
      from base
      group by box
      having strpos(lower(extensions.unaccent(box)),lower(extensions.unaccent(btrim(p_busca))))>0
        or bool_or(strpos(lower(extensions.unaccent(nome)),lower(extensions.unaccent(btrim(p_busca))))>0)
    ),
    pagina as (
      select * from grupos
      order by melhor_percentual desc nulls last,box collate "C"
      limit p_limite offset p_offset
    ),
    itens as (
      select p.box,p.total_cards,p.melhor_percentual,
        coalesce((select jsonb_agg(to_jsonb(t)-'ordem_preview' order by t.ordem_preview)
          from (
            select b.card_id,b.nome,b.posicao,b.overall,b.foto_url_cloudinary as foto_url,
              b.analises,b.pontuacao_maxima,
              row_number() over(order by
                clube_novo.contratacao_estrelas_v1(b.analises#>>'{0,codigo}') desc nulls last,
                (b.analises#>>'{0,pontuacao}')::numeric desc nulls last,b.card_id collate "C") ordem_preview
            from base b where b.box=p.box order by ordem_preview limit 3
          ) t
        ),'[]'::jsonb) cards
      from pagina p
    )
    select jsonb_build_object(
      'contrato','site-novo-boxes-v1','versao',1,'degrau',p_degrau,'modo','boxes',
      'box',null,'busca',p_busca,'total',(select count(*) from grupos),
      'total_cards',(select coalesce(sum(total_cards),0) from grupos),
      'limite',p_limite,'offset',p_offset,
      'itens',coalesce((select jsonb_agg(to_jsonb(i) order by i.melhor_percentual desc nulls last,i.box collate "C") from itens i),'[]'::jsonb)
    ) into resultado;
  else
    with ofertas as materialized (
 select distinct m.card_id,x.box_nome from clube_novo.box_card_em_andamento_v1 m
 join clube_novo.box_contexto_contratacao_v1 x on x.box_id=m.box_id
 where x.estado_box='em_andamento' and x.oferta_fonte is not null and nullif(btrim(x.box_nome),'') is not null
 and (p_box is null or x.box_nome=p_box)
), notas as materialized (
 select * from clube_novo.site_novo_boxes_melhores_linhas_v1((select array_agg(distinct card_id) from ofertas),p_degrau)
), base as materialized (
 select c.card_id,c.nome,x.box_nome as box,c.overall,
 (select p.codigo_pt from clube_novo.carta_posicao_principal_jogo cp join clube_novo.posicao_jogo p on p.id=cp.posicao_id where cp.card_id=c.card_id order by cp.posicao_id limit 1) posicao,
 c.foto_url_cloudinary,(n.analises#>>'{0,pontuacao}')::numeric pontuacao_maxima,
 (n.analises#>>'{0,regua_vigente}')::boolean regua_vigente,coalesce(n.analises,'[]'::jsonb) analises
 from ofertas x join clube_novo.carta_jogo c on c.card_id=x.card_id left join notas n on n.card_id=x.card_id
),
    selecionadas as (
      select card_id,nome,posicao,overall,foto_url_cloudinary as foto_url,analises,pontuacao_maxima
      from base where box=p_box
    ),
    pagina as (
      select * from selecionadas
      order by clube_novo.contratacao_estrelas_v1(analises#>>'{0,codigo}') desc nulls last,
        (analises#>>'{0,pontuacao}')::numeric desc nulls last,card_id collate "C"
      limit p_limite offset p_offset
    )
    select jsonb_build_object(
      'contrato','site-novo-boxes-v1','versao',1,'degrau',p_degrau,'modo','cards',
      'box',p_box,'busca',p_busca,'total',(select count(*) from selecionadas),
      'total_cards',(select count(*) from selecionadas),'limite',p_limite,'offset',p_offset,
      'itens',coalesce((select jsonb_agg(to_jsonb(p) order by
        clube_novo.contratacao_estrelas_v1(p.analises#>>'{0,codigo}') desc nulls last,
        (p.analises#>>'{0,pontuacao}')::numeric desc nulls last,p.card_id collate "C") from pagina p),'[]'::jsonb)
    ) into resultado;
  end if;

  return resultado || jsonb_build_object(
    'regua',(
      select coalesce(jsonb_agg(jsonb_build_object(
        'codigo',f.codigo,'rotulo',f.rotulo,'percentual_minimo',f.percentual_minimo
      ) order by f.ordem),'[]'::jsonb)
      from clube_novo.regua_contratacao_faixa_v1 f
      join clube_novo.regua_contratacao_versao_v1 v
        on v.versao=f.regua_versao and v.estado='vigente'
    ),
    'tem_mais',(resultado->>'total')::bigint>p_offset+p_limite,
    'status',case when jsonb_array_length(resultado->'itens')=0 then 'vazio' else 'pronto' end
  );
end
$function$;
CREATE OR REPLACE FUNCTION clube_novo.site_novo_box_card_identidade_v1(p_card jsonb)
 RETURNS jsonb
 LANGUAGE sql
 STABLE
 SET search_path TO ''
AS $function$
with pos as (
 select p.id,p.nome_pt from clube_novo.posicao_jogo p
 where p.codigo_pt=p_card->>'posicao'
)
select jsonb_build_object('posicao_nome',(select nome_pt from pos limit 1),
 'estilos',coalesce((select jsonb_agg(jsonb_build_object('id',s.playstyle_id,'nome',ps.nome_tela) order by s.slot_fisico)
 from clube_novo.carta_playstyle_jogo s join clube_novo.playstyle ps on ps.id_jogo=s.playstyle_id
 where s.card_id=p_card->>'card_id' and ps.nome_tela is not null and s.playstyle_id<>256), '[]'::jsonb));
$function$;
ALTER FUNCTION clube_novo.site_novo_boxes_melhores_linhas_v1(text[],integer) SET jit TO 'off'; ALTER FUNCTION clube_novo.site_novo_boxes_melhores_linhas_v1(text[],integer) SET plan_cache_mode TO 'force_custom_plan'; ALTER FUNCTION clube_novo.site_novo_boxes_melhores_linhas_v1(text[],integer) SET work_mem TO '32MB';
ALTER FUNCTION public.site_novo_boxes_em_andamento_v1(text,text,integer,integer,integer) SET jit TO 'off'; ALTER FUNCTION public.site_novo_boxes_em_andamento_v1(text,text,integer,integer,integer) SET plan_cache_mode TO 'force_custom_plan'; ALTER FUNCTION public.site_novo_boxes_v1(text,text,integer,integer,text,integer) SET jit TO 'off'; ALTER FUNCTION public.site_novo_boxes_v1(text,text,integer,integer,text,integer) SET plan_cache_mode TO 'force_custom_plan'; NOTIFY pgrst,'reload schema';