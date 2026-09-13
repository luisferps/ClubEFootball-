CREATE OR REPLACE FUNCTION clube_novo.site_novo_boxes_em_andamento_calculo_v1(p_box text DEFAULT NULL::text, p_busca text DEFAULT ''::text, p_limite integer DEFAULT 24, p_offset integer DEFAULT 0, p_degrau integer DEFAULT 3)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
 SET statement_timeout TO '5s'
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
      select m.card_id,x.box_id,x.box_nome,x.estado_box,x.data_oferta,x.origem_fingerprint
      from clube_novo.box_card_em_andamento_v1 m
      join clube_novo.box_contexto_contratacao_v1 x on x.box_id=m.box_id
      where x.estado_box='em_andamento'
        and x.oferta_fonte is not null
        and nullif(btrim(x.box_nome),'') is not null
    ),
    cards_oferta as materialized (select distinct card_id from ofertas),
    topos_fonte as materialized (
      select funcao_id,nota_final from clube_novo.build_publicacao_exibivel_v3
    ),
    topos as materialized (
      select funcao_id,max(nota_final) topo_funcao from topos_fonte group by funcao_id
    ),
    avaliadas_fonte as materialized (
      select a.card_id,a.linha_id,a.funcao_id,fs.rotulo funcao_nome,
        coalesce(p.codigo_pt,'') posicao_codigo,
        100::numeric*a.nota_final/t.topo_funcao percentual_topo,
        a.nota_final overall_final,(select bo.contrato_fingerprint=rv.contrato_fingerprint from clube_novo.build_otimizador bo cross join clube_novo.regua_vigente_v1 rv where bo.id=a.build_otimizador_id) regua_vigente
      from cards_oferta o
      join clube_novo.build_publicacao_exibivel_v3 a on a.card_id=o.card_id
      join topos t on t.funcao_id=a.funcao_id and t.topo_funcao>0
      join clube_novo.funcao_sistema fs on fs.id=a.funcao_id
      join clube_novo.posicao_jogo p on p.id=a.posicao_id
      where a.impeto_condicional_codigo is null or a.impeto_condicional_nivel=p_degrau
    ),
    avaliadas as materialized (
      select v.*,
        max(v.overall_final) over(partition by v.card_id) pontuacao_maxima,
        row_number() over(partition by v.card_id,v.funcao_id order by v.percentual_topo desc,v.overall_final desc,v.linha_id) rn
      from avaliadas_fonte v
      where v.percentual_topo is not null
        and v.percentual_topo::text not in ('NaN','Infinity','-Infinity')
    ),
    base as materialized (
      select c.card_id,c.nome,x.box_nome as box,c.overall,
        (select pj.codigo_pt
         from clube_novo.carta_posicao_principal_jogo cp
         join clube_novo.posicao_jogo pj on pj.id=cp.posicao_id
         where cp.card_id=c.card_id order by cp.posicao_id limit 1) as posicao,
        c.foto_url_cloudinary,
        (select max(v.pontuacao_maxima) from avaliadas v where v.card_id=c.card_id) pontuacao_maxima,
        (select (array_agg(v.regua_vigente order by v.overall_final desc))[1] from avaliadas v where v.card_id=c.card_id) regua_vigente,
        coalesce((
          select jsonb_agg(jsonb_build_object(
            'linha_id',v.linha_id::text,'funcao',v.funcao_nome,'posicao',v.posicao_codigo,
            'pontuacao',v.overall_final,'percentual_topo',v.percentual_topo,'regua_vigente',v.regua_vigente,
            'etiqueta',et.item->>'etiqueta_rotulo','codigo',et.item->>'etiqueta_codigo',
            'regua_versao',et.item->>'regua_versao'
          ) order by v.percentual_topo desc,v.overall_final desc,v.linha_id)
          from avaliadas v
          cross join lateral jsonb_array_elements(
            clube_novo.contratacoes_por_box_build_v1(v.card_id,v.funcao_nome,v.percentual_topo)
          ) et(item)
          where v.card_id=c.card_id and v.rn=1
            and et.item->>'box_id'=x.box_id::text
            and et.item->>'estado_box'='em_andamento'
        ),'[]'::jsonb) analises
      from ofertas x
      join clube_novo.carta_jogo c on c.card_id=x.card_id
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
                coalesce(b.pontuacao_maxima,(b.analises#>>'{0,pontuacao}')::numeric) desc nulls last,b.card_id collate "C") ordem_preview
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
      select m.card_id,x.box_id,x.box_nome,x.estado_box,x.data_oferta,x.origem_fingerprint
      from clube_novo.box_card_em_andamento_v1 m
      join clube_novo.box_contexto_contratacao_v1 x on x.box_id=m.box_id
      where x.estado_box='em_andamento'
        and x.oferta_fonte is not null
        and nullif(btrim(x.box_nome),'') is not null
    ),
    cards_oferta as materialized (select distinct card_id from ofertas),
    topos_fonte as materialized (
      select funcao_id,nota_final from clube_novo.build_publicacao_exibivel_v3
    ),
    topos as materialized (
      select funcao_id,max(nota_final) topo_funcao from topos_fonte group by funcao_id
    ),
    avaliadas_fonte as materialized (
      select a.card_id,a.linha_id,a.funcao_id,fs.rotulo funcao_nome,
        coalesce(p.codigo_pt,'') posicao_codigo,
        100::numeric*a.nota_final/t.topo_funcao percentual_topo,
        a.nota_final overall_final,(select bo.contrato_fingerprint=rv.contrato_fingerprint from clube_novo.build_otimizador bo cross join clube_novo.regua_vigente_v1 rv where bo.id=a.build_otimizador_id) regua_vigente
      from cards_oferta o
      join clube_novo.build_publicacao_exibivel_v3 a on a.card_id=o.card_id
      join topos t on t.funcao_id=a.funcao_id and t.topo_funcao>0
      join clube_novo.funcao_sistema fs on fs.id=a.funcao_id
      join clube_novo.posicao_jogo p on p.id=a.posicao_id
      where a.impeto_condicional_codigo is null or a.impeto_condicional_nivel=p_degrau
    ),
    avaliadas as materialized (
      select v.*,
        max(v.overall_final) over(partition by v.card_id) pontuacao_maxima,
        row_number() over(partition by v.card_id,v.funcao_id order by v.percentual_topo desc,v.overall_final desc,v.linha_id) rn
      from avaliadas_fonte v
      where v.percentual_topo is not null
        and v.percentual_topo::text not in ('NaN','Infinity','-Infinity')
    ),
    base as materialized (
      select c.card_id,c.nome,x.box_nome as box,c.overall,
        (select pj.codigo_pt
         from clube_novo.carta_posicao_principal_jogo cp
         join clube_novo.posicao_jogo pj on pj.id=cp.posicao_id
         where cp.card_id=c.card_id order by cp.posicao_id limit 1) as posicao,
        c.foto_url_cloudinary,
        (select max(v.pontuacao_maxima) from avaliadas v where v.card_id=c.card_id) pontuacao_maxima,
        (select (array_agg(v.regua_vigente order by v.overall_final desc))[1] from avaliadas v where v.card_id=c.card_id) regua_vigente,
        coalesce((
          select jsonb_agg(jsonb_build_object(
            'linha_id',v.linha_id::text,'funcao',v.funcao_nome,'posicao',v.posicao_codigo,
            'pontuacao',v.overall_final,'percentual_topo',v.percentual_topo,'regua_vigente',v.regua_vigente,
            'etiqueta',et.item->>'etiqueta_rotulo','codigo',et.item->>'etiqueta_codigo',
            'regua_versao',et.item->>'regua_versao'
          ) order by v.percentual_topo desc,v.overall_final desc,v.linha_id)
          from avaliadas v
          cross join lateral jsonb_array_elements(
            clube_novo.contratacoes_por_box_build_v1(v.card_id,v.funcao_nome,v.percentual_topo)
          ) et(item)
          where v.card_id=c.card_id and v.rn=1
            and et.item->>'box_id'=x.box_id::text
            and et.item->>'estado_box'='em_andamento'
        ),'[]'::jsonb) analises
      from ofertas x join clube_novo.carta_jogo c on c.card_id=x.card_id
    ),
    selecionadas as (
      select card_id,nome,posicao,overall,foto_url_cloudinary as foto_url,analises,pontuacao_maxima
      from base where box=p_box
    ),
    pagina as (
      select * from selecionadas
      order by clube_novo.contratacao_estrelas_v1(analises#>>'{0,codigo}') desc nulls last,
        coalesce(pontuacao_maxima,(analises#>>'{0,pontuacao}')::numeric) desc nulls last,card_id collate "C"
      limit p_limite offset p_offset
    )
    select jsonb_build_object(
      'contrato','site-novo-boxes-v1','versao',1,'degrau',p_degrau,'modo','cards',
      'box',p_box,'busca',p_busca,'total',(select count(*) from selecionadas),
      'total_cards',(select count(*) from selecionadas),'limite',p_limite,'offset',p_offset,
      'itens',coalesce((select jsonb_agg(to_jsonb(p) order by
        clube_novo.contratacao_estrelas_v1(p.analises#>>'{0,codigo}') desc nulls last,
        coalesce(p.pontuacao_maxima,(p.analises#>>'{0,pontuacao}')::numeric) desc nulls last,p.card_id collate "C") from pagina p),'[]'::jsonb)
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
