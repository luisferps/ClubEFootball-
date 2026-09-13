set local lock_timeout='1s'; set local statement_timeout='15s'; create index build_publicacao_card_leitura_v2_idx on clube_novo.build_publicacao_linha_ativa_v1(card_id,nota_final desc,linha_id) include(funcao_id,posicao_id,build_otimizador_id,publicada_em,impeto_condicional_codigo,impeto_condicional_nivel);
set local lock_timeout='1s';
drop index clube_novo.build_publicacao_linha_ativa_card_v1_idx;
alter index clube_novo.build_publicacao_card_leitura_v2_idx rename to build_publicacao_linha_ativa_card_v1_idx;
CREATE OR REPLACE FUNCTION public.site_novo_ranking_v1(p_modo text DEFAULT 'card'::text, p_setor text DEFAULT 'geral'::text, p_funcao_id text DEFAULT NULL::text, p_busca text DEFAULT ''::text, p_posicao_nativa_id integer DEFAULT NULL::integer, p_estilo_id integer DEFAULT NULL::integer, p_limite integer DEFAULT 30, p_offset integer DEFAULT 0, p_degrau integer DEFAULT 3)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
 SET jit TO 'off'
 SET statement_timeout TO '5s'
 SET work_mem TO '16MB'
 SET plan_cache_mode TO 'force_custom_plan'
AS $function$
declare resposta jsonb;
begin
 if p_degrau is null or p_degrau not in (1,2,3) then raise exception 'Degrau invalido' using errcode='22023'; end if;
 if p_modo is null or p_modo not in ('card','jogador','mix')
 or p_setor is null or p_setor not in ('geral','goleiro','defesa','meio','ataque')
 or p_limite is null or p_limite not between 1 and 60
 or p_offset is null or p_offset not between 0 and 100000
 or p_busca is null or length(p_busca)>100
 or (p_funcao_id is not null and not exists(select 1 from clube_novo.funcao_sistema f where f.id::text=p_funcao_id and f.ativa))
 or (p_posicao_nativa_id is not null and not exists(select 1 from clube_novo.posicao_jogo p where p.id=p_posicao_nativa_id))
 or (p_estilo_id is not null and not exists(select 1 from clube_novo.playstyle s where s.id_jogo=p_estilo_id))
 then raise exception 'Parametros do Ranking invalidos' using errcode='22023'; end if;
 with funcoes as materialized (
  select f.id,f.rotulo,f.ordem,
   case when f.grupo='GOLEIRO' then 'goleiro'
    when f.grupo in ('ZAGUEIRO','LATERAL') or f.id=17 then 'defesa'
    when f.grupo in ('CENTROAVANTE','PONTA') then 'ataque' else 'meio' end setor
  from clube_novo.funcao_sistema f where f.ativa
 ), base as materialized (
  select a.linha_id,a.card_id,(c.card_id::bigint & 262143)::text jogador_id,
   a.funcao_id,a.posicao_id,a.nota_final,a.publicada_em,f.setor,a.build_otimizador_id
  from clube_novo.build_publicacao_exibivel_v3 a
  join clube_novo.carta_jogo c on c.card_id=a.card_id
  join funcoes f on f.id=a.funcao_id
  where (a.impeto_condicional_codigo is null or a.impeto_condicional_nivel=p_degrau)
   and a.nota_final is not null and a.nota_final::text not in ('NaN','Infinity','-Infinity')
   and a.publicada_em is not null
   and nullif(btrim(c.nome),'') is not null
   and (c.card_id::bigint & 262143)>0
   and (p_setor='geral' or f.setor=p_setor)
   and (p_funcao_id is null or a.funcao_id::text=p_funcao_id)
   and (btrim(p_busca)='' or strpos(clube_novo.site_novo_busca_normalizar_v1(c.nome),clube_novo.site_novo_busca_normalizar_v1(btrim(p_busca)))>0)
   and (p_posicao_nativa_id is null or a.posicao_id=p_posicao_nativa_id)
   and (p_estilo_id is null or (p_estilo_id<>256 and exists(select 1 from clube_novo.carta_playstyle_jogo s where s.card_id=c.card_id and s.playstyle_id=p_estilo_id) and exists(select 1 from clube_novo.bonificador_regra_playstyle r where r.playstyle_id=p_estilo_id and r.posicao_id=a.posicao_id and r.da_bonus)))
 ), escolhas as (
  select b.*, row_number() over (
   partition by case p_modo when 'card' then b.card_id when 'jogador' then b.jogador_id else b.card_id||':'||b.funcao_id::text end
   order by b.nota_final desc,b.card_id collate "C",b.funcao_id,b.posicao_id,b.linha_id
  ) escolha from base b
 ), ordenadas as materialized (
  select e.*,row_number() over(order by e.nota_final desc,e.card_id collate "C",e.funcao_id,e.posicao_id,e.linha_id) classificacao
  from escolhas e where escolha=1
 ), pagina_linhas as materialized (
  select * from ordenadas order by classificacao limit p_limite offset p_offset
 ), posicoes_pagina as materialized (
  select bb.card_id,bb.funcao_id,string_agg(distinct pp.codigo_pt,' / ' order by pp.codigo_pt) posicao
  from base bb join (select distinct card_id,funcao_id from pagina_linhas) ids using(card_id,funcao_id)
  join clube_novo.posicao_jogo pp on pp.id=bb.posicao_id group by bb.card_id,bb.funcao_id
 ), pagina as (
  select o.*,(select bo.contrato_fingerprint = rv.contrato_fingerprint from clube_novo.build_otimizador bo cross join clube_novo.regua_vigente_v1 rv where bo.id=o.build_otimizador_id) as regua_vigente,(select coalesce(jsonb_agg(jsonb_build_object('id',s.playstyle_id,'nome',ps.nome_tela) order by s.slot_fisico),'[]'::jsonb) from clube_novo.carta_playstyle_jogo s join clube_novo.playstyle ps on ps.id_jogo=s.playstyle_id where s.card_id=o.card_id and ps.nome_tela is not null) estilos,c.nome,c.foto_url_cloudinary foto_url,(select coalesce(jsonb_agg(jsonb_build_object('nome',b.box_nome,'em_andamento',b.em_andamento) order by b.box_nome),'[]'::jsonb) from (select x.box_nome,bool_or(x.estado_box='em_andamento') em_andamento from clube_novo.carta_box_oferta_v1 x where x.card_id=o.card_id group by x.box_nome)b) as boxes,f.rotulo funcao,pp.posicao
  from pagina_linhas o
  join posicoes_pagina pp on pp.card_id=o.card_id and pp.funcao_id=o.funcao_id
  join clube_novo.carta_jogo c on c.card_id=o.card_id
  join funcoes f on f.id=o.funcao_id
  join clube_novo.posicao_jogo p on p.id=o.posicao_id
 )
 select jsonb_build_object(
  'contrato','site-novo-ranking-v1','versao',1,'degrau',p_degrau,
  'status',case when exists(select 1 from pagina) then 'pronto' else 'vazio' end,
  'modo',p_modo,'setor',p_setor,'total',(select count(*) from ordenadas),
  'limite',p_limite,'offset',p_offset,'tem_mais',(select count(*) from ordenadas)>p_offset+p_limite,
  'itens',coalesce((select jsonb_agg(jsonb_build_object(
   'linha_id',linha_id::text,'card_id',card_id,'jogador_id',jogador_id,
   'classificacao',classificacao,'nota_final',nota_final,'publicada_em',publicada_em,
   'nome',nome,'foto_url',foto_url,'boxes',boxes,'estilos',estilos,
   'funcao_id',funcao_id::text,'funcao',funcao,'posicao_id',posicao_id,'posicao',posicao,'setor',setor,'regua_vigente',regua_vigente
  ) order by classificacao) from pagina),'[]'::jsonb),
  'catalogo',jsonb_build_object(
   'funcoes',(select jsonb_agg(jsonb_build_object('id',id::text,'nome',rotulo,'setor',setor) order by ordem,id) from funcoes),
   'posicoes',(select jsonb_agg(jsonb_build_object('id',id,'nome',nome_pt,'codigo',codigo_pt) order by id) from clube_novo.posicao_jogo),
   'estilos',(select jsonb_agg(jsonb_build_object('id',id_jogo,'nome',nome_tela) order by nome_tela,id_jogo) from clube_novo.playstyle where nome_tela is not null)
  )
 ) into resposta;
 return resposta;
end;
$function$
;
notify pgrst,'reload schema';

