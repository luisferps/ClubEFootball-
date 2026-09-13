CREATE OR REPLACE FUNCTION clube_novo.site_novo_boxes_calculo_v1(p_box text DEFAULT NULL::text, p_busca text DEFAULT ''::text, p_limite integer DEFAULT 24, p_offset integer DEFAULT 0, p_ordem text DEFAULT 'recentes'::text, p_degrau integer DEFAULT 3)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
 SET statement_timeout TO '8s'
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
      select a.card_id,max(a.nota_final) pontuacao_maxima,(array_agg(a.regua_vigente order by a.nota_final desc))[1] regua_vigente
      from (select distinct card_id from cards_pagina) cp
      join clube_novo.build_publicacao_exibivel_v3 a on a.card_id=cp.card_id
      where (a.impeto_condicional_codigo is null or a.impeto_condicional_nivel=p_degrau)
        and a.nota_final::text not in ('NaN','Infinity','-Infinity')
      group by a.card_id
    ),
    base_pagina as materialized (
      select v.card_id,v.box_id,c.nome,v.box,c.overall,
        (select pj.codigo_pt
         from clube_novo.carta_posicao_principal_jogo cp
         join clube_novo.posicao_jogo pj on pj.id=cp.posicao_id
         where cp.card_id=c.card_id order by cp.posicao_id limit 1) as posicao,
        c.foto_url_cloudinary as foto_url,n.pontuacao_maxima,n.regua_vigente
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
             clube_novo.site_novo_box_card_analise_snapshot_v1(bp.box_id,bp.card_id,p_degrau::smallint) analises,
             row_number() over(order by
               clube_novo.contratacao_estrelas_v1(clube_novo.site_novo_box_card_analise_snapshot_v1(bp.box_id,bp.card_id,p_degrau::smallint)#>>'{0,codigo}') desc nulls last,
               bp.pontuacao_maxima desc nulls last,bp.card_id collate "C") ordem_card
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
      select a.card_id,max(a.nota_final) pontuacao_maxima,(array_agg(a.regua_vigente order by a.nota_final desc))[1] regua_vigente
      from (select distinct card_id from vinculos) v
      join clube_novo.build_publicacao_exibivel_v3 a on a.card_id=v.card_id
      where (a.impeto_condicional_codigo is null or a.impeto_condicional_nivel=p_degrau)
        and a.nota_final::text not in ('NaN','Infinity','-Infinity')
      group by a.card_id
    ),
    cards_box as materialized (
      select v.card_id,v.box_id,c.nome,
        (select pj.codigo_pt
         from clube_novo.carta_posicao_principal_jogo cp
         join clube_novo.posicao_jogo pj on pj.id=cp.posicao_id
         where cp.card_id=c.card_id order by cp.posicao_id limit 1) as posicao,
        c.overall,c.foto_url_cloudinary as foto_url,n.pontuacao_maxima,n.regua_vigente,
        clube_novo.site_novo_box_card_analise_snapshot_v1(v.box_id,v.card_id,p_degrau::smallint) analises,
        row_number() over(order by clube_novo.contratacao_estrelas_v1(clube_novo.site_novo_box_card_analise_snapshot_v1(v.box_id,v.card_id,p_degrau::smallint)#>>'{0,codigo}') desc nulls last,n.pontuacao_maxima desc nulls last,v.card_id collate "C") ordem_card
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
      select a.card_id,a.nota_final,a.impeto_condicional_codigo,a.impeto_condicional_nivel
      from clube_novo.build_publicacao_exibivel_v3 a
    ), notas as materialized (
      select a.card_id,max(a.nota_final) pontuacao_maxima
      from notas_fonte a
      where (a.impeto_condicional_codigo is null or a.impeto_condicional_nivel=p_degrau)
        and a.nota_final::text not in ('NaN','Infinity','-Infinity')
      group by a.card_id
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
    pagina_boxes as (
      select * from ordenadas order by ordem limit p_limite offset p_offset
    ),
    itens_boxes as (
      select p.box,p.total_cards,p.melhor_pontuacao,p.data_oferta,
        coalesce(to_char(p.data_oferta,'DD/MM/YYYY'),'Data não informada') data_rotulo,p.ordem,
        (select jsonb_agg(to_jsonb(t)-'ordem_card'-'box_id' order by t.ordem_card)
         from (
           select b.card_id,b.box_id,b.nome,b.posicao,b.overall,b.foto_url,b.pontuacao_maxima,
             clube_novo.site_novo_box_card_analise_snapshot_v1(b.box_id,b.card_id,p_degrau::smallint) analises,
             row_number() over(order by
               clube_novo.contratacao_estrelas_v1(clube_novo.site_novo_box_card_analise_snapshot_v1(b.box_id,b.card_id,p_degrau::smallint)#>>'{0,codigo}') desc nulls last,
               b.pontuacao_maxima desc nulls last,b.card_id collate "C") ordem_card
           from base b where b.box=p.box order by ordem_card limit 3
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
