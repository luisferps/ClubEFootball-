-- Ranking publico: somente leitura de publicacoes ativas em clube_novo.
-- Nao calcula nota e nao altera publicacao, filas ou motores.
create function public.site_novo_ranking_v1(
 p_modo text default 'card', p_setor text default 'geral',
 p_funcao_id text default null, p_busca text default '',
 p_posicao_nativa_id integer default null, p_estilo_id integer default null,
 p_limite integer default 30, p_offset integer default 0
) returns jsonb
language plpgsql stable security definer
set search_path = '' set jit = off set statement_timeout = '5s'
as $$
declare resposta jsonb;
begin
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
   a.funcao_id,a.posicao_id,a.nota_final,a.publicada_em,c.nome,
   c.foto_url_cloudinary foto_url,c.box,f.rotulo funcao,p.codigo_pt posicao,
   f.setor,cp.posicao_id posicao_nativa_id
  from clube_novo.build_publicacao_linha_ativa_v1 a
  join clube_novo.build_linha_card l on l.id=a.linha_id and l.card_id=a.card_id
   and l.funcao_id=a.funcao_id and l.posicao_id=a.posicao_id
  join clube_novo.carta_jogo c on c.card_id=a.card_id
  join funcoes f on f.id=a.funcao_id
  join clube_novo.posicao_jogo p on p.id=a.posicao_id
  left join clube_novo.carta_posicao_principal_jogo cp on cp.card_id=c.card_id
  where l.execucao_tipo='producao' and l.lote_teste_id is null
   and not coalesce(l.pendencias @> array['teste_nao_publicado']::text[],false)
   and a.nota_final is not null and a.nota_final::text not in ('NaN','Infinity','-Infinity')
   and a.publicada_em is not null
   and nullif(btrim(c.nome),'') is not null
   and (c.card_id::bigint & 262143)>0
   and (p_setor='geral' or f.setor=p_setor)
   and (p_funcao_id is null or a.funcao_id::text=p_funcao_id)
   and (btrim(p_busca)='' or strpos(lower(c.nome),lower(btrim(p_busca)))>0)
   and (p_posicao_nativa_id is null or cp.posicao_id=p_posicao_nativa_id)
   and (p_estilo_id is null or exists(select 1 from clube_novo.carta_playstyle_jogo s where s.card_id=c.card_id and s.playstyle_id=p_estilo_id))
 ), escolhas as (
  select b.*, row_number() over (
   partition by case p_modo when 'card' then b.card_id when 'jogador' then b.jogador_id else b.linha_id::text end
   order by b.nota_final desc,b.card_id collate "C",b.funcao_id,b.posicao_id,b.linha_id
  ) escolha from base b
 ), ordenadas as materialized (
  select e.*,row_number() over(order by e.nota_final desc,e.card_id collate "C",e.funcao_id,e.posicao_id,e.linha_id) classificacao
  from escolhas e where escolha=1
 ), pagina as (
  select * from ordenadas order by classificacao limit p_limite offset p_offset
 )
 select jsonb_build_object(
  'contrato','site-novo-ranking-v1','versao',1,
  'status',case when exists(select 1 from pagina) then 'pronto' else 'vazio' end,
  'modo',p_modo,'setor',p_setor,'total',(select count(*) from ordenadas),
  'limite',p_limite,'offset',p_offset,'tem_mais',(select count(*) from ordenadas)>p_offset+p_limite,
  'itens',coalesce((select jsonb_agg(jsonb_build_object(
   'linha_id',linha_id::text,'card_id',card_id,'jogador_id',jogador_id,
   'classificacao',classificacao,'nota_final',nota_final,'publicada_em',publicada_em,
   'nome',nome,'foto_url',foto_url,'box',box,
   'funcao_id',funcao_id::text,'funcao',funcao,'posicao_id',posicao_id,'posicao',posicao,'setor',setor
  ) order by classificacao) from pagina),'[]'::jsonb),
  'catalogo',jsonb_build_object(
   'funcoes',(select jsonb_agg(jsonb_build_object('id',id::text,'nome',rotulo,'setor',setor) order by ordem,id) from funcoes),
   'posicoes',(select jsonb_agg(jsonb_build_object('id',id,'nome',nome_pt,'codigo',codigo_pt) order by id) from clube_novo.posicao_jogo),
   'estilos',(select jsonb_agg(jsonb_build_object('id',id_jogo,'nome',nome_tela) order by nome_tela,id_jogo) from clube_novo.playstyle where nome_tela is not null)
  )
 ) into resposta;
 return resposta;
end;
$$;
revoke all on function public.site_novo_ranking_v1(text,text,text,text,integer,integer,integer,integer) from public;
grant execute on function public.site_novo_ranking_v1(text,text,text,text,integer,integer,integer,integer) to anon,authenticated,service_role;
comment on function public.site_novo_ranking_v1(text,text,text,text,integer,integer,integer,integer)
is 'Contrato publico de leitura do Ranking. Notas prontas de build_publicacao_linha_ativa_v1; identidade fisica do jogador nos 18 bits baixos do card_id. Filtros precedem agrupamento; nenhuma nota recalculada.';
notify pgrst, 'reload schema';
