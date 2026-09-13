-- As classificações de boxes encerradas são snapshots: permanecem iguais após
-- a finalização. O degrau serve somente para localizar a linha publicada que
-- a ficha deve abrir; percentual e etiqueta vêm do snapshot persistido.
create or replace function clube_novo.site_novo_box_card_analise_snapshot_v1(
  p_box_id bigint,
  p_card_id text,
  p_degrau smallint
)
returns jsonb
language sql
stable
security definer
set search_path to ''
as $function$
  select coalesce(jsonb_agg(jsonb_build_object(
    'linha_id',linha.linha_id::text,
    'funcao',s.funcao_rotulo,
    'posicao',coalesce(pos.codigo_pt,principal.codigo_pt,''),
    'pontuacao',s.pontuacao_snapshot,
    'percentual_topo',s.percentual_topo_snapshot,
    'etiqueta',s.etiqueta_rotulo,
    'codigo',s.etiqueta_codigo,
    'regua_versao',s.regua_versao_snapshot
  ) order by s.percentual_topo_snapshot desc,s.pontuacao_snapshot desc,s.funcao_rotulo collate "C"),'[]'::jsonb)
  from clube_novo.box_card_contratacao_snapshot_v1 s
  left join clube_novo.funcao_sistema fs
    on lower(btrim(fs.rotulo))=lower(btrim(s.funcao_rotulo))
  left join lateral (
    select a.linha_id,a.posicao_id
    from clube_novo.build_publicacao_linha_ativa_v1 a
    where a.card_id=s.card_id and a.funcao_id=fs.id
      and (a.impeto_condicional_codigo is null or a.impeto_condicional_nivel=p_degrau)
    order by abs(a.nota_final-s.pontuacao_snapshot),a.linha_id
    limit 1
  ) linha on true
  left join clube_novo.posicao_jogo pos on pos.id=linha.posicao_id
  left join lateral (
    select p.codigo_pt
    from clube_novo.carta_posicao_principal_jogo cp
    join clube_novo.posicao_jogo p on p.id=cp.posicao_id
    where cp.card_id=s.card_id
    order by cp.posicao_id
    limit 1
  ) principal on true
  where s.box_id=p_box_id and s.card_id=p_card_id;
$function$;

revoke all on function clube_novo.site_novo_box_card_analise_snapshot_v1(bigint,text,smallint) from public;
grant execute on function clube_novo.site_novo_box_card_analise_snapshot_v1(bigint,text,smallint) to service_role;
create or replace function public.site_novo_boxes_v1(
  p_box text default null,
  p_busca text default '',
  p_limite integer default 24,
  p_offset integer default 0,
  p_ordem text default 'recentes',
  p_degrau integer default 3
)
returns jsonb
language plpgsql
stable
security definer
set search_path to ''
set statement_timeout to '8s'
set jit to 'off'
set plan_cache_mode to 'force_custom_plan'
set work_mem to '16MB'
as $function$
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
        or strpos(lower(extensions.unaccent(v.box)),lower(extensions.unaccent(btrim(p_busca))))>0
        or exists(
          select 1 from vinculos vb
          join clube_novo.carta_jogo cb on cb.card_id=vb.card_id
          where vb.box=v.box
            and strpos(lower(extensions.unaccent(cb.nome)),lower(extensions.unaccent(btrim(p_busca))))>0
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
      select a.card_id,max(a.nota_final) pontuacao_maxima
      from (select distinct card_id from cards_pagina) cp
      join clube_novo.build_publicacao_linha_ativa_v1 a on a.card_id=cp.card_id
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
        c.foto_url_cloudinary as foto_url,n.pontuacao_maxima
      from cards_pagina v
      join clube_novo.carta_jogo c on c.card_id=v.card_id
      left join notas n on n.card_id=v.card_id
    ),
    itens_boxes as (
      select p.box,p.total_cards,max(b.pontuacao_maxima) melhor_pontuacao,p.data_oferta,
        coalesce(to_char(p.data_oferta,'DD/MM/YYYY'),'Data não informada') data_rotulo,p.ordem,
        (select jsonb_agg(to_jsonb(t)-'ordem_card'-'box_id' order by t.ordem_card)
         from (
           select bp.card_id,bp.nome,bp.posicao,bp.overall,bp.foto_url,bp.pontuacao_maxima,
             clube_novo.site_novo_box_card_analise_snapshot_v1(bp.box_id,bp.card_id,p_degrau::smallint) analises,
             row_number() over(order by
               case when btrim(p_busca)<>'' and strpos(lower(extensions.unaccent(bp.nome)),lower(extensions.unaccent(btrim(p_busca))))>0 then 0 else 1 end,
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
      select a.card_id,max(a.nota_final) pontuacao_maxima
      from (select distinct card_id from vinculos) v
      join clube_novo.build_publicacao_linha_ativa_v1 a on a.card_id=v.card_id
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
        c.overall,c.foto_url_cloudinary as foto_url,n.pontuacao_maxima,
        clube_novo.site_novo_box_card_analise_snapshot_v1(v.box_id,v.card_id,p_degrau::smallint) analises,
        row_number() over(order by n.pontuacao_maxima desc nulls last,v.card_id collate "C") ordem_card
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
    with notas as materialized (
      select a.card_id,max(a.nota_final) pontuacao_maxima
      from clube_novo.build_publicacao_linha_ativa_v1 a
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
      having strpos(lower(extensions.unaccent(box)),lower(extensions.unaccent(btrim(p_busca))))>0
        or bool_or(strpos(lower(extensions.unaccent(nome)),lower(extensions.unaccent(btrim(p_busca))))>0)
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
               case when btrim(p_busca)<>'' and strpos(lower(extensions.unaccent(b.nome)),lower(extensions.unaccent(btrim(p_busca))))>0 then 0 else 1 end,
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

comment on function public.site_novo_boxes_v1(text,text,integer,integer,text,integer)
is 'Catalogo cadastrado com pontuacao publicada e classificacao congelada por card e box.';

revoke all on function public.site_novo_boxes_v1(text,text,integer,integer,text,integer) from public;
grant execute on function public.site_novo_boxes_v1(text,text,integer,integer,text,integer) to anon,authenticated,service_role;
