create extension if not exists unaccent with schema extensions;
alter table clube_novo.box_contexto_contratacao_v1 add column oferta_fonte text, add column data_oferta date;
comment on column clube_novo.box_contexto_contratacao_v1.oferta_fonte is 'Proveniencia do vinculo comercial confirmado; NULL impede usar rotulos fisicos como ofertas.';
comment on table clube_novo.box_card_em_andamento_v1 is 'Vinculos card/oferta; nome preservado por compatibilidade. Relacoes sao mantidas apos encerramento para o catalogo historico.';
create or replace view clube_novo.carta_box_oferta_v1 with (security_invoker=true) as
select m.card_id,x.box_id,x.box_nome,x.estado_box,x.data_oferta,x.origem_fingerprint
from clube_novo.box_card_em_andamento_v1 m
join clube_novo.box_contexto_contratacao_v1 x on x.box_id=m.box_id
where x.oferta_fonte is not null and nullif(btrim(x.box_nome),'') is not null;
revoke all on clube_novo.carta_box_oferta_v1 from public,anon,authenticated;
comment on view clube_novo.carta_box_oferta_v1 is 'Leitura central das boxes comerciais comprovadas pela sincronizacao da oferta. Rotulos fisicos de variacao da carta nunca entram como box.';
CREATE OR REPLACE FUNCTION clube_novo.sincronizar_boxes_efhub_v1(p jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO ''
 SET jit TO 'off'
AS $function$
declare
  fp text; anterior jsonb; resposta jsonb; b jsonb; id_box bigint;
  ids bigint[] := '{}'; n integer; fechadas integer; momento timestamptz;
begin
  if p is null or p->>'source_url' is distinct from 'https://efhub.com/pt-BR'
     or coalesce(p->>'html_sha256','') !~ '^[a-f0-9]{64}$'
     or coalesce(p->>'radar_fingerprint','') !~ '^[a-f0-9]{64}$'
     or jsonb_typeof(p->'boxes') is distinct from 'array' then
    raise exception 'Fonte de boxes inválida';
  end if;
  momento := (p->>'observed_at')::timestamptz;
  if momento is null or momento < now()-interval '24 hours' or momento > now()+interval '5 minutes' then
    raise exception 'Home fora da validade de aplicação';
  end if;
  n := jsonb_array_length(p->'boxes');
  if n not between 1 and 100 then raise exception 'Lista vazia ou inválida'; end if;
  if exists(select 1 from jsonb_array_elements(p->'boxes') x where
    coalesce(btrim(x->>'nome'),'')='' or jsonb_typeof(x->'cards') is distinct from 'array') then
    raise exception 'Box inválida';
  end if;
  if (select count(distinct lower(btrim(x->>'nome'))) from jsonb_array_elements(p->'boxes') x) <> n then
    raise exception 'Nomes de boxes duplicados';
  end if;
  if exists(select 1 from jsonb_array_elements(p->'boxes') x where jsonb_array_length(x->'cards')=0
     or (select count(distinct c->>'card_id') from jsonb_array_elements(x->'cards') c) <> jsonb_array_length(x->'cards')) then
    raise exception 'Box vazia ou cards duplicados';
  end if;
  if exists(select 1 from jsonb_array_elements(p->'boxes') x cross join lateral jsonb_array_elements(x->'cards') c
    where coalesce(c->>'card_id','') !~ '^[1-9][0-9]*$' or coalesce(btrim(c->>'box_fisica'),'')=''
       or coalesce(c->>'record_sha256','') !~ '^[a-f0-9]{64}$') then
    raise exception 'Vínculo físico inválido';
  end if;
  if exists(select 1 from jsonb_array_elements(p->'boxes') x cross join lateral jsonb_array_elements(x->'cards') c
    where not exists(select 1 from clube_novo.carta_jogo j where j.card_id::text=c->>'card_id')) then
    raise exception 'Card da home ainda não cadastrado no banco';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('clube_novo.boxes.efhub',0));
  lock table clube_novo.box_contexto_contratacao_v1 in share row exclusive mode;
  fp := encode(extensions.digest(convert_to(p::text,'UTF8'),'sha256'),'hex');
  select resultado into resposta from clube_novo.box_sincronizacao_efhub_v1 where fingerprint=fp;
  if found then return resposta || '{"reaplicacao":true}'::jsonb; end if;
  if exists(select 1 from clube_novo.box_sincronizacao_efhub_v1 where observado_em > momento) then
    raise exception 'Existe fotografia mais recente das boxes';
  end if;
  select jsonb_build_object('contextos',coalesce((select jsonb_agg(to_jsonb(x)) from clube_novo.box_contexto_contratacao_v1 x where estado_box='em_andamento'),'[]'),
      'vinculos',coalesce((select jsonb_agg(to_jsonb(m)) from clube_novo.box_card_em_andamento_v1 m join clube_novo.box_contexto_contratacao_v1 x using(box_id) where x.estado_box='em_andamento'),'[]')) into anterior;
  -- Cada retorno de uma oferta encerrada abre novo contexto, preservando seu histórico.
  for b in select value from jsonb_array_elements(p->'boxes') loop
    select box_id into id_box from clube_novo.box_contexto_contratacao_v1
     where estado_box='em_andamento' and box_nome=b->>'nome' order by box_id limit 1;
    if id_box is null then
      select coalesce(max(box_id),0)+1 into id_box from clube_novo.box_contexto_contratacao_v1;
      insert into clube_novo.box_contexto_contratacao_v1(box_id,box_nome,estado_box,status_origem,origem_fingerprint,capturado_em,oferta_fonte,data_oferta) values(id_box,b->>'nome','em_andamento','atual',fp,momento,p->>'source_url',nullif(b->>'data_oferta','')::date);
    else
      update clube_novo.box_contexto_contratacao_v1 set origem_fingerprint=fp,capturado_em=momento,oferta_fonte=p->>'source_url',data_oferta=coalesce(nullif(b->>'data_oferta','')::date,data_oferta) where box_id=id_box;
    end if;
    ids := array_append(ids,id_box);
    delete from clube_novo.box_card_em_andamento_v1 m where m.box_id=id_box
      and not exists(select 1 from jsonb_array_elements(b->'cards') c where c->>'card_id'=m.card_id);
    insert into clube_novo.box_card_em_andamento_v1(box_id,card_id,capturado_em)
      select id_box,c->>'card_id',momento from jsonb_array_elements(b->'cards') c
      on conflict(box_id,card_id) do update set capturado_em=excluded.capturado_em;
  end loop;
  -- Usa a mesma pontuação/percentual publicados e a mesma régua canônica da tela.
  insert into clube_novo.box_card_contratacao_snapshot_v1
   (box_id,card_id,funcao_rotulo,pontuacao_snapshot,percentual_topo_snapshot,etiqueta_codigo,etiqueta_rotulo,regua_versao_snapshot,congelado_em,origem,origem_fingerprint)
  select distinct on (m.box_id,m.card_id) m.box_id,m.card_id,v.funcao_nome,v.overall_final,v.percentual_topo,
     faixa->>'etiqueta_codigo',faixa->>'etiqueta_rotulo',faixa->>'regua_versao',momento,'Encerramento observado na home eFHUB',fp
  from clube_novo.box_card_em_andamento_v1 m
  join clube_novo.box_contexto_contratacao_v1 ctx using(box_id)
  join clube_novo.build_pontuacao_final_v2_publica_v1 v on v.card_id::text=m.card_id
  cross join lateral jsonb_array_elements(clube_novo.contratacoes_por_box_build_v1(m.card_id,v.funcao_nome,v.percentual_topo)) faixa
  where ctx.estado_box='em_andamento' and not(ctx.box_id=any(ids)) and v.percentual_topo between 0 and 100
    and (faixa->>'box_id')::bigint=m.box_id and faixa->>'origem_percentual'='dinamica'
  order by m.box_id,m.card_id,v.percentual_topo desc,v.overall_final desc,v.linha_id
  on conflict(box_id,card_id) do nothing;
  update clube_novo.box_contexto_contratacao_v1 set estado_box='finalizada',status_origem='anterior',origem_fingerprint=fp,capturado_em=momento
    where estado_box='em_andamento' and not(box_id=any(ids));
  get diagnostics fechadas = row_count;
  resposta := jsonb_build_object('fingerprint',fp,'boxes',n,'vinculos',(select count(*) from clube_novo.box_card_em_andamento_v1 where box_id=any(ids)),'encerradas',fechadas,'database_write',true);
  insert into clube_novo.box_sincronizacao_efhub_v1 values(fp,momento,now(),p,anterior,resposta);
  return resposta;
end;
$function$;

-- O catalogo recente primeiro pagina os vinculos leves. Fotos, posicoes e notas
-- sao consultadas somente para os cards que realmente vao para a resposta.
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
        x.card_id,x.box_nome as box,x.data_oferta
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
      select v.card_id,c.nome,v.box,c.overall,
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
        (select jsonb_agg(to_jsonb(t)-'ordem_card' order by t.ordem_card)
         from (
           select bp.card_id,bp.nome,bp.posicao,bp.overall,bp.foto_url,bp.pontuacao_maxima,
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
        x.card_id,x.box_nome as box,x.data_oferta
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
      select v.card_id,c.nome,
        (select pj.codigo_pt
         from clube_novo.carta_posicao_principal_jogo cp
         join clube_novo.posicao_jogo pj on pj.id=cp.posicao_id
         where cp.card_id=c.card_id order by cp.posicao_id limit 1) as posicao,
        c.overall,c.foto_url_cloudinary as foto_url,n.pontuacao_maxima,
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
      'itens',coalesce((select jsonb_agg(to_jsonb(i)-'ordem_card' order by i.ordem_card) from pagina_cards i),'[]'::jsonb)
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
        c.card_id,c.nome,x.box_nome as box,c.overall,
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
        (select jsonb_agg(to_jsonb(t)-'ordem_card' order by t.ordem_card)
         from (
           select b.card_id,b.nome,b.posicao,b.overall,b.foto_url,b.pontuacao_maxima,
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
    'tem_mais',(resultado->>'total')::bigint>p_offset+p_limite,
    'status',case when jsonb_array_length(resultado->'itens')=0 then 'vazio' else 'pronto' end
  );
end
$function$;

comment on function public.site_novo_boxes_v1(text,text,integer,integer,text,integer)
is 'Catalogo por vinculo comercial confirmado; pagina antes de carregar os campos largos dos cards.';

revoke all on function public.site_novo_boxes_v1(text,text,integer,integer,text,integer) from public;
grant execute on function public.site_novo_boxes_v1(text,text,integer,integer,text,integer) to anon,authenticated,service_role;
