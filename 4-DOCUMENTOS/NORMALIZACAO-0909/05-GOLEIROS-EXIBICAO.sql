-- Elegibilidade de exibição aprovada: não misturar os dois estilos de goleiro.
-- A ponte produtiva e as linhas dos motores permanecem intactas.
create view clube_novo.build_publicacao_exibivel_v3 as
 select a.* from clube_novo.build_publicacao_linha_ativa_v1 a
 where a.funcao_id not in (4,5) or exists(
   select 1 from clube_novo.carta_playstyle_jogo p where p.card_id=a.card_id
   and p.playstyle_id=case a.funcao_id when 4 then 337 when 5 then 336 end
 );
revoke all on clube_novo.build_publicacao_exibivel_v3 from public,anon,authenticated;
grant select on clube_novo.build_publicacao_exibivel_v3 to service_role;
comment on view clube_novo.build_publicacao_exibivel_v3 is
 'Leitura da vitrine: goleiro defensivo 337 na função 4; ofensivo 336 na 5. Não altera produção, finalização, fila ou editor pessoal.';
create view clube_novo.build_pontuacao_final_v3_exibivel as  WITH base AS (
         SELECT d.publicacao_v2_fingerprint,
            d.linha_id,
            d.card_id,
            d.funcao_id,
            d.posicao_id,
            d.build_otimizador_id,
            d.build_bonificador_id,
            d.tecnico_id,
            d.barras,
            d.impeto_adicional_codigo,
            d.habilidades_adicionais,
            d.atributos_finais,
            d.arows_snapshot,
            d.pontuacao_otimizador_bruta_evidencia,
            d.pontuacao_otimizador_normalizada,
            d.bonus_pe,
            d.bonus_fisico_total,
            d.bonus_posicao,
            d.bonus_playstyle_1,
            d.bonus_playstyle_2,
            d.bonus_ia,
            d.bonus_outros,
            d.bonus_total_bonificador,
            d.overall_final,
            d.normalizacao_fingerprint,
            d.calculo_banco_fingerprint,
            d.carta_fingerprint,
            d.formula_fingerprint,
            d.contrato_fingerprint,
            d.otimizador_resultado_fingerprint,
            d.bonificador_resultado_fingerprint,
            d.publicacao_fingerprint_v1,
            d.publicada_em,
            d.publicacao_linha_fingerprint_v2,
            max(d.overall_final) OVER (PARTITION BY d.funcao_id) AS topo_funcao,
            d.estado_final,
            d.motivo_final,
            d.proveniencia
           FROM clube_novo.build_pontuacao_final_v2_delta_v1 d
             JOIN clube_novo.build_publicacao_exibivel_v3 a ON a.linha_id = d.linha_id AND a.build_otimizador_id = d.build_otimizador_id AND a.build_bonificador_id = d.build_bonificador_id
        )
 SELECT b.publicacao_v2_fingerprint,
    b.linha_id,
    b.card_id,
    b.funcao_id,
    b.posicao_id,
    b.build_otimizador_id,
    b.build_bonificador_id,
    b.tecnico_id,
    b.barras,
    b.impeto_adicional_codigo,
    b.habilidades_adicionais,
    b.atributos_finais,
    b.arows_snapshot,
    b.pontuacao_otimizador_bruta_evidencia,
    b.pontuacao_otimizador_normalizada,
    b.bonus_pe,
    b.bonus_fisico_total,
    b.bonus_posicao,
    b.bonus_playstyle_1,
    b.bonus_playstyle_2,
    b.bonus_ia,
    b.bonus_outros,
    b.bonus_total_bonificador,
    b.overall_final,
    b.normalizacao_fingerprint,
    b.calculo_banco_fingerprint,
    b.carta_fingerprint,
    b.formula_fingerprint,
    b.contrato_fingerprint,
    b.otimizador_resultado_fingerprint,
    b.bonificador_resultado_fingerprint,
    b.publicacao_fingerprint_v1,
    b.publicada_em,
    b.publicacao_linha_fingerprint_v2,
    b.topo_funcao,
        CASE
            WHEN b.topo_funcao > 0::numeric THEN 100::numeric * b.overall_final / b.topo_funcao
            ELSE NULL::numeric
        END AS percentual_topo,
    b.estado_final,
    b.motivo_final,
    b.proveniencia,
    c.nome AS carta_nome,
    c.tipo AS carta_tipo,
        CASE
            WHEN c.box IS NOT NULL AND btrim(c.box) <> ''::text AND (lower(btrim(c.box)) <> ALL (ARRAY['0'::text, 'dummy'::text, '[[not use]]'::text])) THEN btrim(c.box)
            ELSE NULL::text
        END AS carta_box,
    c.overall AS carta_overall,
        CASE
            WHEN c.foto_url_cloudinary ~ '^https://res\\.cloudinary\\.com/[A-Za-z0-9_-]+/image/upload/'::text THEN c.foto_url_cloudinary
            ELSE NULL::text
        END AS foto_url_cloudinary,
    COALESCE(fs.sigla, ''::text) AS funcao_codigo,
    fs.rotulo AS funcao_nome,
    COALESCE(p.codigo_pt, ''::text) AS posicao_codigo,
    p.nome_pt AS posicao_nome,
    COALESCE(t.nome_en, b.tecnico_id::text) AS tecnico_nome,
        CASE
            WHEN b.impeto_adicional_codigo IS NOT NULL THEN jsonb_build_object('codigo', b.impeto_adicional_codigo, 'nome', clube_novo.impeto_nome_v1(b.impeto_adicional_codigo), 'de_goleiro', clube_novo.impeto_e_de_goleiro_v1(b.impeto_adicional_codigo), 'efeitos', clube_novo.impeto_efeitos_v1(b.impeto_adicional_codigo))
            ELSE NULL::jsonb
        END AS impeto_adicional,
        CASE
            WHEN bl.impeto_condicional_codigo IS NOT NULL THEN jsonb_build_object('codigo', bl.impeto_condicional_codigo, 'nome', clube_novo.impeto_nome_v1(bl.impeto_condicional_codigo), 'degrau', bl.impeto_condicional_nivel, 'degraus', jsonb_build_array(1, 2, 3), 'regra', 'degrau pela quantidade de jogadores da condicao em campo: 1 a 7 = +1, 8 a 10 = +2, 11 a 23 = +3', 'efeitos', clube_novo.impeto_efeitos_v1(bl.impeto_condicional_codigo))
            ELSE NULL::jsonb
        END AS impeto_condicional,
    row_number() OVER (ORDER BY b.overall_final DESC, b.card_id, b.funcao_id, b.posicao_id, b.linha_id) AS ordem_geral,
    row_number() OVER (PARTITION BY b.funcao_id ORDER BY b.overall_final DESC, b.card_id, b.posicao_id, b.linha_id) AS ordem_na_funcao
   FROM base b
     JOIN clube_novo.carta_jogo c ON c.card_id = b.card_id
     JOIN clube_novo.build_linha_card bl ON bl.id = b.linha_id
     JOIN clube_novo.funcao_sistema fs ON fs.id = b.funcao_id
     JOIN clube_novo.posicao_jogo p ON p.id = b.posicao_id
     LEFT JOIN clube_novo.tecnico_jogo t ON t.id = b.tecnico_id;
revoke all on clube_novo.build_pontuacao_final_v3_exibivel from public,anon,authenticated;
grant select on clube_novo.build_pontuacao_final_v3_exibivel to service_role;
CREATE OR REPLACE FUNCTION public.site_novo_ranking_v1(p_modo text DEFAULT 'card'::text, p_setor text DEFAULT 'geral'::text, p_funcao_id text DEFAULT NULL::text, p_busca text DEFAULT ''::text, p_posicao_nativa_id integer DEFAULT NULL::integer, p_estilo_id integer DEFAULT NULL::integer, p_limite integer DEFAULT 30, p_offset integer DEFAULT 0, p_degrau integer DEFAULT 3)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
 SET jit TO 'off'
 SET statement_timeout TO '5s'
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
   a.funcao_id,a.posicao_id,a.nota_final,a.publicada_em,f.setor
  from clube_novo.build_publicacao_exibivel_v3 a
  join clube_novo.carta_jogo c on c.card_id=a.card_id
  join funcoes f on f.id=a.funcao_id
  left join clube_novo.carta_posicao_principal_jogo cp on cp.card_id=c.card_id
  where (a.impeto_condicional_codigo is null or a.impeto_condicional_nivel=p_degrau)
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
   partition by case p_modo when 'card' then b.card_id when 'jogador' then b.jogador_id else b.card_id||':'||b.funcao_id::text end
   order by b.nota_final desc,b.card_id collate "C",b.funcao_id,b.posicao_id,b.linha_id
  ) escolha from base b
 ), ordenadas as materialized (
  select e.*,row_number() over(order by e.nota_final desc,e.card_id collate "C",e.funcao_id,e.posicao_id,e.linha_id) classificacao
  from escolhas e where escolha=1
 ), pagina as (
  select o.*,c.nome,c.foto_url_cloudinary foto_url,(select coalesce(jsonb_agg(jsonb_build_object('nome',b.box_nome,'em_andamento',b.em_andamento) order by b.box_nome),'[]'::jsonb) from (select x.box_nome,bool_or(x.estado_box='em_andamento') em_andamento from clube_novo.carta_box_oferta_v1 x where x.card_id=o.card_id group by x.box_nome)b) as boxes,f.rotulo funcao,(select string_agg(distinct pp.codigo_pt,' / ' order by pp.codigo_pt) from base bb join clube_novo.posicao_jogo pp on pp.id=bb.posicao_id where bb.card_id=o.card_id and bb.funcao_id=o.funcao_id) posicao
  from (select * from ordenadas order by classificacao limit p_limite offset p_offset) o
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
   'nome',nome,'foto_url',foto_url,'boxes',boxes,
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
$function$;
CREATE OR REPLACE FUNCTION public.site_novo_busca_v1(p_busca text, p_limite integer DEFAULT 48, p_offset integer DEFAULT 0, p_degrau integer DEFAULT 3)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
 SET jit TO 'off'
 SET statement_timeout TO '5s'
AS $function$
declare
  v_termo text;
  v_limpo text;
  v_tokens text[];
  v_consulta tsquery;
  v_resposta jsonb;
begin
  if p_busca is null
     or length(btrim(p_busca)) not between 3 and 120
     or p_busca ~ '[[:cntrl:]]'
     or p_limite is null or p_limite not between 1 and 48
     or p_offset is null or p_offset not between 0 and 100000
     or p_degrau is null or p_degrau not between 1 and 3 then
    raise exception 'Parametros da busca invalidos' using errcode = '22023';
  end if;

  v_termo := btrim(p_busca);
  v_limpo := btrim(regexp_replace(
    clube_novo.site_novo_busca_normalizar_v1(v_termo),
    '[^a-z0-9]+', ' ', 'g'
  ));
  v_tokens := regexp_split_to_array(v_limpo, ' +');

  if v_limpo = '' or coalesce(array_length(v_tokens, 1), 0) not between 1 and 12 then
    raise exception 'Parametros da busca invalidos' using errcode = '22023';
  end if;

  select to_tsquery('simple', string_agg(token || ':*', ' & ' order by ordem))
  into v_consulta
  from unnest(v_tokens) with ordinality as t(token, ordem);

  with base as materialized (
    select
      c.card_id,
      c.nome,
      c.foto_url_cloudinary as foto_url,
      case when lower(btrim(coalesce(c.box, ''))) in ('', '0', 'dummy', '[[not use]]') then null else btrim(c.box) end as box,
      c.overall,
      coalesce(p.codigo_pt, nullif(btrim(c.posicao), '')) as posicao,
      ts_rank_cd(
        to_tsvector(
          'simple',
          clube_novo.site_novo_busca_normalizar_v1(
            coalesce(c.card_id, '') || ' ' || coalesce(c.nome, '') || ' ' ||
            coalesce(c.box, '') || ' ' || coalesce(c.posicao, '') || ' ' ||
            coalesce(c.estilo_of_pos, '') || ' ' || coalesce(c.nacionalidade, '') || ' ' ||
            coalesce(c.tipo, '')
          )
        ),
        v_consulta
      ) as relevancia,
      case
        when clube_novo.site_novo_busca_normalizar_v1(c.nome) = v_limpo then 0
        when ' ' || clube_novo.site_novo_busca_normalizar_v1(c.nome) || ' ' like '% ' || v_limpo || ' %' then 1
        when clube_novo.site_novo_busca_normalizar_v1(c.nome) like v_limpo || '%' then 2
        else 3
      end as prioridade
    from clube_novo.carta_jogo c
    left join clube_novo.carta_posicao_principal_jogo cp on cp.card_id = c.card_id
    left join clube_novo.posicao_jogo p on p.id = cp.posicao_id
    where c.card_id ~ '^[1-9][0-9]*$'
      and nullif(btrim(c.nome), '') is not null
      and to_tsvector(
        'simple',
        clube_novo.site_novo_busca_normalizar_v1(
          coalesce(c.card_id, '') || ' ' || coalesce(c.nome, '') || ' ' ||
          coalesce(c.box, '') || ' ' || coalesce(c.posicao, '') || ' ' ||
          coalesce(c.estilo_of_pos, '') || ' ' || coalesce(c.nacionalidade, '') || ' ' ||
          coalesce(c.tipo, '')
        )
      ) @@ v_consulta
  ),
  pontuacoes as materialized (
    select a.card_id, max(a.nota_final) as pontuacao_total
    from base b
    join clube_novo.build_publicacao_exibivel_v3 a on a.card_id = b.card_id
    join clube_novo.build_linha_card l on l.id = a.linha_id
    where (l.impeto_condicional_codigo is null or l.impeto_condicional_nivel = p_degrau)
      and l.execucao_tipo = 'producao'
      and l.lote_teste_id is null
      and not coalesce(l.pendencias @> array['teste_nao_publicado']::text[], false)
      and a.nota_final is not null
      and a.nota_final not in ('Infinity'::numeric, '-Infinity'::numeric, 'NaN'::numeric)
      and a.publicada_em is not null
    group by a.card_id
  ),
  ordenada as materialized (
    select b.*, p.pontuacao_total, row_number() over (
      order by b.prioridade, p.pontuacao_total desc nulls last,
               b.relevancia desc, b.overall desc nulls last,
               b.nome collate "C", b.card_id collate "C"
    ) as ordem
    from base b
    left join pontuacoes p on p.card_id = b.card_id
  ),
  pagina as (
    select * from ordenada order by ordem limit p_limite offset p_offset
  )
  select jsonb_build_object(
    'contrato', 'site-novo-busca-v1', 'versao', 1,
    'status', case when exists(select 1 from pagina) then 'pronto' else 'vazio' end,
    'busca', v_termo, 'degrau', p_degrau,
    'total', (select count(*) from ordenada),
    'limite', p_limite, 'offset', p_offset,
    'tem_mais', (select count(*) from ordenada) > p_offset + p_limite,
    'itens', coalesce((select jsonb_agg(jsonb_build_object(
      'card_id', card_id, 'nome', nome, 'foto_url', foto_url, 'box', box,
      'pontuacao_total', pontuacao_total,
      'posicao', posicao
    ) order by ordem) from pagina), '[]'::jsonb)
  ) into v_resposta;

  return v_resposta;
end;
$function$;
CREATE OR REPLACE FUNCTION public.site_novo_ficha_base_publicada_v1(p_card_id text DEFAULT NULL::text, p_linha_id bigint DEFAULT NULL::bigint)
 RETURNS jsonb
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
with
entrada as (
  select nullif(btrim(p_card_id), '') as card_id
),
carta as (
  select
    c.card_id,
    c.nome,
    c.foto_url_cloudinary,
    (select string_agg(distinct bx.box_nome,' · ' order by bx.box_nome) from clube_novo.carta_box_oferta_v1 bx where bx.card_id=c.card_id) as box,
    c.level_cap,
    c.orcamento,
    c.altura,
    c.peso,
    c.idade,
    c.resistencia_lesao,
    (c.level_cap = 1 and c.orcamento = 0) as sem_evolucao,
    tc.nome_exibicao as tipo_carta
  from entrada e
  join clube_novo.carta_jogo c
    on c.card_id = e.card_id
  left join clube_novo.tipo_carta_jogo tc
    on tc.tipo_carta_id = c.tipo_carta_id
),
publicadas as (
  select
    l.id,
    l.card_id,
    l.funcao_id,
    l.posicao_id,
    a.build_otimizador_id,
    a.build_bonificador_id,
    a.nota_final,
    a.publicada_em as nota_publicada_em_v1,
    l.impeto_condicional_codigo,
    l.impeto_condicional_nivel,
    bo.tecnico_id,
    bo.barras,
    bo.impeto_adicional_codigo,
    bo.habilidades_adicionais,
    bo.atributos_finais,
    bo.atributos_internos,
    bb.bonus_pe,
    bb.bonus_fisico_total,
    bb.bonus_posicao,
    bb.bonus_playstyle_1,
    bb.bonus_playstyle_2,
    bb.bonus_ia,
    bb.bonus_outros,
    bb.bonus_total,
    bb.bonus_fisico_detalhe
  from entrada e
  join clube_novo.build_linha_card l
    on l.card_id = e.card_id
  join clube_novo.build_publicacao_exibivel_v3 a
    on a.linha_id = l.id
  join clube_novo.build_otimizador bo
    on bo.id = a.build_otimizador_id
  join clube_novo.build_bonificador bb
    on bb.id = a.build_bonificador_id
  where l.execucao_tipo = 'producao'
    and l.lote_teste_id is null
    and not (l.pendencias @> array['teste_nao_publicado'::text])
),
selecionada as (
  select p.*
  from publicadas p
  where (p_linha_id is null and (p.impeto_condicional_codigo is null or p.impeto_condicional_nivel = 3)) or p.id = p_linha_id
  order by
    p.nota_final desc nulls last,
    case
      when jsonb_typeof(p.atributos_finais) = 'array'
        then jsonb_array_length(p.atributos_finais) = 26
      else false
    end desc,
    p.nota_publicada_em_v1 desc,
    p.id asc
  limit 1
),
visiveis as (
 select p.* from publicadas p cross join selecionada s
 where p.impeto_condicional_codigo is null
    or p.impeto_condicional_nivel = coalesce(s.impeto_condicional_nivel,3)
),
contexto as (
  select
    e.card_id as card_id_pedido,
    c.*,
    s.id as linha_id,
    s.funcao_id,
    s.posicao_id,
    s.build_otimizador_id,
    s.build_bonificador_id,
    s.nota_final,
    s.nota_publicada_em_v1,
    s.impeto_condicional_codigo,
    s.impeto_condicional_nivel,
    s.tecnico_id,
    s.barras,
    s.impeto_adicional_codigo,
    s.habilidades_adicionais,
    s.atributos_finais,
    s.atributos_internos,
    s.bonus_pe,
    s.bonus_fisico_total,
    s.bonus_posicao,
    s.bonus_playstyle_1,
    s.bonus_playstyle_2,
    s.bonus_ia,
    s.bonus_outros,
    s.bonus_total,
    s.bonus_fisico_detalhe,
    clube_novo.site_novo_fila_atributos_confirmada_v1(e.card_id)
      as fila_atributos_confirmada,
    case
      when jsonb_typeof(s.atributos_finais) = 'array'
        then jsonb_array_length(s.atributos_finais) = 26
      else false
    end as atributos_completos
  from entrada e
  left join carta c on true
  left join selecionada s on true
)
select jsonb_build_object(
  'contrato', 'site-novo-ficha-v1',
  'versao', 1,
  'status',
    case
      when x.card_id_pedido is null then 'parametro_ausente'
      when x.card_id is null then 'card_nao_encontrado'
      when x.linha_id is null and p_linha_id is not null then 'linha_nao_encontrada_ou_nao_publicada'
      when x.linha_id is null then 'card_sem_build_publicada'
      when not x.atributos_completos and x.fila_atributos_confirmada
        then 'atributos_em_atualizacao'
      when not x.atributos_completos then 'atributos_aguardando_publicacao'
      else 'pronto'
    end,
  'mensagem',
    case
      when x.card_id_pedido is null then 'Informe o card_id na URL para abrir a Ficha.'
      when x.card_id is null then 'Card não encontrado.'
      when x.linha_id is null and p_linha_id is not null then 'A linha pedida não pertence ao card ou não está publicada.'
      when x.linha_id is null then 'Este card ainda não tem build publicada.'
      when not x.atributos_completos and x.fila_atributos_confirmada
        then 'A nota está publicada e há registro vivo de atualização dos 26 atributos.'
      when not x.atributos_completos
        then 'A nota está publicada; os 26 atributos ainda aguardam publicação.'
      else 'Ficha pronta.'
    end,
  'card_id', x.card_id_pedido,
  'dados',
    case
      when x.card_id is null then null
      else jsonb_build_object(
        'card', jsonb_build_object(
          'card_id', x.card_id,
          'nome', x.nome,
          'foto_url', x.foto_url_cloudinary,
          'box', x.box,
          'tipo_carta', x.tipo_carta,
          'no_elenco', null,
          'estilo_jogo', (
            select ps.nome_tela
            from clube_novo.carta_playstyle_jogo cp
            join clube_novo.playstyle ps
              on ps.id_jogo = cp.playstyle_id
            where cp.card_id = x.card_id
              and cp.slot_fisico = 1
            order by cp.slot_fisico, ps.id_jogo
            limit 1
          ),
          'posicao_nativa', (
            select jsonb_build_object(
              'id', pj.id,
              'codigo', pj.codigo_pt,
              'nome', pj.nome_pt
            )
            from clube_novo.carta_posicao_principal_jogo cpp
            join clube_novo.posicao_jogo pj
              on pj.id = cpp.posicao_id
            where cpp.card_id = x.card_id
            order by cpp.posicao_id
            limit 1
          ),
          'posicoes', (
            select coalesce(
              jsonb_agg(
                jsonb_build_object(
                  'id', pj.id,
                  'codigo', pj.codigo_pt,
                  'nome', pj.nome_pt,
                  'nivel', cp.nivel_aptidao,
                  'principal', cpp.posicao_id is not null,
                  'selecionada', pj.id = x.posicao_id
                )
                order by case pj.codigo_pt
                  when 'PTE' then 1
                  when 'CA' then 2
                  when 'PTD' then 3
                  when 'SA' then 4
                  when 'MLE' then 5
                  when 'MAT' then 6
                  when 'MLD' then 7
                  when 'MLG' then 8
                  when 'VOL' then 9
                  when 'LE' then 10
                  when 'ZC' then 11
                  when 'LD' then 12
                  when 'GO' then 13
                  else 99
                end
              ),
              '[]'::jsonb
            )
            from clube_novo.posicao_jogo pj
            left join clube_novo.carta_posicao_jogo cp
              on cp.card_id = x.card_id
             and cp.posicao_id = pj.id
            left join clube_novo.carta_posicao_principal_jogo cpp
              on cpp.card_id = x.card_id
             and cpp.posicao_id = pj.id
            where pj.codigo_pt in (
              'PTE','CA','PTD','SA','MLE','MAT','MLD','MLG','VOL','LE','ZC','LD','GO'
            )
          ),
          'habilidades_especiais', (
            select coalesce(
              jsonb_agg(
                jsonb_build_object(
                  'id', h.skill_id,
                  'nome', h.nome_pt
                )
                order by ch.ordem nulls last, h.ordem, h.skill_id
              ),
              '[]'::jsonb
            )
            from clube_novo.carta_habilidade_jogo ch
            join clube_novo.habilidade_jogo h
              on h.skill_id = ch.skill_id
            where ch.card_id = x.card_id
              and h.tipo = 'especial'
          ),
          'habilidades_nativas', (
            select coalesce(
              jsonb_agg(
                jsonb_build_object(
                  'id', h.skill_id,
                  'nome', h.nome_pt
                )
                order by ch.ordem nulls last, h.ordem, h.skill_id
              ),
              '[]'::jsonb
            )
            from clube_novo.carta_habilidade_jogo ch
            join clube_novo.habilidade_jogo h
              on h.skill_id = ch.skill_id
            where ch.card_id = x.card_id
              and h.tipo is distinct from 'especial'
          ),
          'estilos_ia', (
            select coalesce(
              jsonb_agg(
                jsonb_build_object(
                  'codigo', ei.codigo,
                  'nome', ei.nome_tela
                )
                order by ei.bit
              ),
              '[]'::jsonb
            )
            from clube_novo.carta_estilo_ia_jogo cei
            join clube_novo.estilo_ia ei
              on ei.bit = cei.bit_estilo_ia
            where cei.card_id = x.card_id
          ),
          'altura_cm', x.altura,
          'peso_kg', x.peso,
          'idade_anos', x.idade,
          'resistencia_lesao', x.resistencia_lesao,
          'pe', (
            select coalesce(
              jsonb_agg(
                jsonb_build_object(
                  'campo', cp.campo,
                  'valor', cp.valor,
                  'codigo', p.codigo,
                  'nome', p.nome_pt
                )
                order by case cp.campo
                  when 'pe_dominante' then 1
                  when 'pe_ruim_uso' then 2
                  when 'pe_ruim_precisao' then 3
                  else 99
                end
              ),
              '[]'::jsonb
            )
            from clube_novo.carta_pe_jogo cp
            join clube_novo.pe p
              on p.campo = cp.campo
             and p.valor = cp.valor
            where cp.card_id = x.card_id
          ),
          'corpo', (
            select coalesce(
              jsonb_agg(
                jsonb_build_object(
                  'codigo', co.codigo,
                  'chave_bonus', co.nosso,
                  'nome', co.nome_pt,
                  'ordem', co.pos,
                  'valor', cc.valor,
                  'bonus', case
                    when x.bonus_fisico_detalhe ? co.nosso
                      then x.bonus_fisico_detalhe -> co.nosso
                    else null
                  end
                )
                order by co.pos
              ),
              '[]'::jsonb
            )
            from clube_novo.carta_corpo_jogo cc
            join clube_novo.corpo_ordem co
              on co.codigo = cc.codigo_corpo
            where cc.card_id = x.card_id
              and co.usado_pelo_motor is true
          )
        ),
        'build', case
          when x.linha_id is null then null
          else jsonb_build_object(
            'linha_id', x.linha_id,
            'nota_final', x.nota_final,
            'nota_publicada_em', x.nota_publicada_em_v1,
            'funcao', (
              select jsonb_build_object(
                'id', fs.id,
                'rotulo', fs.rotulo,
                'sigla', fs.sigla,
                'grupo', fs.grupo,
                'familia', fs.familia
              )
              from clube_novo.funcao_sistema fs
              where fs.id = x.funcao_id
            ),
            'posicao', (
              select jsonb_build_object(
                'id', pj.id,
                'codigo', pj.codigo_pt,
                'nome', pj.nome_pt
              )
              from clube_novo.posicao_jogo pj
              where pj.id = x.posicao_id
            ),
            'nivel_maximo', x.level_cap,
            'orcamento_total', x.orcamento,
            'orcamento_gasto', null,
            'evolucao', jsonb_build_object(
              'estado', case
                when x.sem_evolucao then 'nivel_1_sem_evolucao'
                else 'com_evolucao'
              end,
              'sem_evolucao', x.sem_evolucao
            ),
            'barras', (
              select jsonb_agg(
                jsonb_build_object(
                  'chave', b.chave,
                  'rotulo', b.rotulo,
                  'valor', case
                    when x.barras ? b.chave then x.barras -> b.chave
                    else null
                  end
                )
                order by b.ordem
              )
              from (
                values
                  (1, 'shooting', 'Chute'),
                  (2, 'passing', 'Passe'),
                  (3, 'dribbling', 'Drible'),
                  (4, 'dexterity', 'Destreza'),
                  (5, 'lowerBodyStrength', 'Força pernas'),
                  (6, 'aerialStrength', 'Força aérea'),
                  (7, 'defending', 'Defesa'),
                  (8, 'gk1', 'GO reflexo/salto'),
                  (9, 'gk2', 'GO defesa/alcance'),
                  (10, 'gk3', 'GO encaixe/reflexos')
              ) as b(ordem, chave, rotulo)
            ),
            'tecnico', (
              select jsonb_build_object(
                'id', tj.id,
                'nome', tj.nome_en,
                'atributos', (
                  select coalesce(
                    jsonb_agg(
                      jsonb_build_object(
                        'codigo_atributo', ta.codigo_atributo,
                        'nome', aj.nome_pt,
                        'delta', ta.delta
                      )
                      order by ta.ordem
                    ),
                    '[]'::jsonb
                  )
                  from clube_novo.tecnico_atributo_jogo ta
                  join clube_novo.atributo_jogo aj
                    on aj.codigo = ta.codigo_atributo
                  where ta.tecnico_id = tj.id
                ),
                'estilos', (
                  select coalesce(
                    jsonb_agg(
                      jsonb_build_object(
                        'codigo', te.codigo_estilo,
                        'proficiencia', te.proficiencia
                      )
                      order by te.proficiencia desc, te.codigo_estilo
                    ),
                    '[]'::jsonb
                  )
                  from clube_novo.tecnico_estilo_jogo te
                  where te.tecnico_id = tj.id
                ),
                'alternativo', null,
                'sugeridos', '[]'::jsonb
              )
              from clube_novo.tecnico_jogo tj
              where tj.id = x.tecnico_id
            ),
            'habilidades_adicionadas', (
              select coalesce(
                jsonb_agg(
                  jsonb_build_object(
                    'id', hids.skill_id,
                    'nome', hj.nome_pt
                  )
                  order by hids.ordem
                ),
                '[]'::jsonb
              )
              from unnest(x.habilidades_adicionais) with ordinality
                as hids(skill_id, ordem)
              left join clube_novo.habilidade_jogo hj
                on hj.skill_id = hids.skill_id
            ),
            'habilidades_sugeridas', '[]'::jsonb,
            'impetos', (
              select coalesce(
                jsonb_agg(
                  jsonb_build_object(
                    'slot', ci.slot,
                    'tipo', case when ci.vaga then 'adicional' else 'nativo' end,
                    'vaga_original', ci.vaga,
                    'codigo', fin.codigo,
                    'nome', ij.nome_pt,
                    'condicional', ij.condicional,
                    'condicao_estado', ij.condicao_estado,
                    'condicao_nivel', case
                      when x.impeto_condicional_codigo = fin.codigo
                        then x.impeto_condicional_nivel
                      else null
                    end,
                    'delta_uniforme', (
                      select case
                        when count(*) > 0 and min(ia.delta) = max(ia.delta)
                          then min(ia.delta)
                        else null
                      end
                      from clube_novo.impeto_atributo_jogo ia
                      where ia.codigo_impeto = fin.codigo
                    ),
                    'efeitos', (
                      select coalesce(
                        jsonb_agg(
                          jsonb_build_object(
                            'codigo_atributo', ia.codigo_atributo,
                            'nome', aj.nome_pt,
                            'delta', ia.delta
                          )
                          order by ia.ordem
                        ),
                        '[]'::jsonb
                      )
                      from clube_novo.impeto_atributo_jogo ia
                      join clube_novo.atributo_jogo aj
                        on aj.codigo = ia.codigo_atributo
                      where ia.codigo_impeto = fin.codigo
                    )
                  )
                  order by ci.ordem
                ),
                '[]'::jsonb
              )
              from clube_novo.carta_impeto_jogo ci
              cross join lateral (
                select case
                  when ci.vaga then x.impeto_adicional_codigo
                  else ci.codigo_impeto
                end as codigo
              ) fin
              left join clube_novo.impeto_jogo ij
                on ij.codigo_jogo = fin.codigo
              where ci.card_id = x.card_id
            ),
            'atributos_completos', x.atributos_completos,
            'atualizacao_atributos', jsonb_build_object(
              'estado', case
                when x.atributos_completos then 'completa'
                when x.fila_atributos_confirmada then 'fila_confirmada'
                else 'sem_evidencia_de_fila'
              end,
              'fila_confirmada', x.fila_atributos_confirmada
            ),
            'atributos', (
              select coalesce(
                jsonb_agg(
                  jsonb_build_object(
                    'indice', ao.indice_otimizador,
                    'codigo', ao.codigo_atributo,
                    'nome', aj.nome_pt,
                    'grupo_origem', aj.grupo,
                    'grupo_tela', case
                      when ao.indice_otimizador between 0 and 6
                        or ao.indice_otimizador in (8, 9) then 'ataque'
                      when ao.indice_otimizador in (10, 11, 12, 15, 16) then 'atletismo'
                      when ao.indice_otimizador in (7, 13, 14) then 'fisico'
                      when ao.indice_otimizador between 17 and 20 then 'defesa'
                      when ao.indice_otimizador between 21 and 25 then 'goleiro'
                      else 'outro'
                    end,
                    'valor_base', ca.valor,
                    'valor_pos_evolucao', case
                      when x.sem_evolucao then ca.valor
                      else null
                    end,
                    'valor_final', case
                      when x.atributos_completos
                        then x.atributos_finais -> ao.indice_otimizador
                      else null
                    end,
                    'valor_jogo', case when x.atributos_completos then x.atributos_finais -> ao.indice_otimizador else null end,
                    'valor_sistema', case when jsonb_typeof(x.atributos_internos)='array' then
                      case when jsonb_array_length(x.atributos_internos)=26 then x.atributos_internos -> ao.indice_otimizador else null end
                      else null end,
                    'pontos', null
                  )
                  order by ao.indice_otimizador
                ),
                '[]'::jsonb
              )
              from clube_novo.atributo_ordem_otimizador ao
              join clube_novo.atributo_jogo aj
                on aj.codigo = ao.codigo_atributo
              left join clube_novo.carta_atributo_jogo ca
                on ca.card_id = x.card_id
               and ca.codigo_atributo = ao.codigo_atributo
            ),
            'atributos_total_pontos', null,
            'bonus_ia', x.bonus_ia,
            'bonus_pe', x.bonus_pe,
            'bonus_fisico_total', x.bonus_fisico_total
          )
        end,
        'proximo_degrau', (
 select jsonb_build_object('linha_id',p.id,'nivel',p.impeto_condicional_nivel)
 from publicadas p
 where x.impeto_condicional_codigo is not null
 and p.funcao_id=x.funcao_id and p.posicao_id=x.posicao_id
 and p.impeto_condicional_codigo=x.impeto_condicional_codigo
 and p.impeto_condicional_nivel=case x.impeto_condicional_nivel when 3 then 1 when 1 then 2 else 3 end
 order by p.nota_final desc nulls last,p.id limit 1
),
'builds_publicadas', (
          select coalesce(
            jsonb_agg(
              jsonb_build_object(
                'linha_id', p.id,
                'funcao', jsonb_build_object(
                  'id', fs.id,
                  'rotulo', fs.rotulo,
                  'sigla', fs.sigla
                ),
                'posicao', jsonb_build_object(
                  'id', pj.id,
                  'codigo', pj.codigo_pt,
                  'nome', pj.nome_pt
                ),
                'nota_final', p.nota_final,
                'selecionada', p.id = x.linha_id
              )
              order by
                p.nota_final desc nulls last,
                case
                  when jsonb_typeof(p.atributos_finais) = 'array'
                    then jsonb_array_length(p.atributos_finais) = 26
                  else false
                end desc,
                p.nota_publicada_em_v1 desc,
                p.id asc
            ),
            '[]'::jsonb
          )
          from visiveis p
          left join clube_novo.funcao_sistema fs
            on fs.id = p.funcao_id
          left join clube_novo.posicao_jogo pj
            on pj.id = p.posicao_id
        ),
        'builds_publicadas_total', (select count(distinct funcao_id) from visiveis),
        'builds_salvas_total', 0,
        'interacoes', jsonb_build_object(
          'referencia_ideal', false,
          'build_atual', false,
          'criar_build', false,
          'ver_mais', false,
          'editar_distribuicao', false,
          'trocar_tecnico', false,
          'editar_habilidades', false,
          'salvar_build', false,
          'alterar_elenco', false
        )
      )
    end
)
from contexto x;
$function$;
CREATE OR REPLACE FUNCTION public.site_novo_ficha_v2(p_card_id text DEFAULT NULL::text, p_linha_id bigint DEFAULT NULL::bigint)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
 SET jit TO 'off'
AS $function$
declare
  ficha jsonb;
  impetos jsonb;
  sugestoes jsonb;
  estilos jsonb;
  pe_rotulado jsonb;
  build jsonb;
  tecnico jsonb;
  degraus jsonb;
begin
  ficha := public.site_novo_ficha_v1(p_card_id,p_linha_id)
    || jsonb_build_object('contrato','site-novo-ficha-v2','versao',2);
  if jsonb_typeof(ficha #> '{dados,card}') = 'object' then
    select coalesce(jsonb_agg(jsonb_build_object(
      'id',p.id_jogo,'slot',cp.slot_fisico,
      'tipo',case cp.slot_fisico when 1 then 'ofensivo' when 2 then 'defensivo' end,
      'nome',coalesce(p.nome_tela,p.nome_pt,p.nome_en)
    ) order by cp.slot_fisico,p.id_jogo),'[]'::jsonb)
    into estilos
    from lateral(select clube_novo.carta_estilos_efetivos_v12(ficha #>> '{dados,card,card_id}') j) s
    cross join lateral(values (1,(s.j->>'ataque_id')::integer),(2,(s.j->>'defesa_id')::integer)) cp(slot_fisico,playstyle_id)
    join clube_novo.playstyle p on p.id_jogo=cp.playstyle_id
    where coalesce((s.j->>'pode_rodar')::boolean,false);
    ficha := jsonb_set(ficha,'{dados,card,estilos_jogo}',estilos);
    if jsonb_typeof(ficha #> '{dados,card,pe}')='array' then
      select coalesce(jsonb_agg(e.item || jsonb_build_object(
        'rotulo_valor',case when p.campo='pe_dominante' then p.nome_pt else nullif(p.nome_antigo,'') end
      ) order by e.ordem),'[]'::jsonb)
      into pe_rotulado
      from jsonb_array_elements(ficha #> '{dados,card,pe}') with ordinality e(item,ordem)
      left join clube_novo.pe p on p.campo=e.item->>'campo'
        and p.valor=(e.item->>'valor')::integer;
      ficha := jsonb_set(ficha,'{dados,card,pe}',pe_rotulado);
    end if;
  end if;
  build := ficha #> '{dados,build}';
  if jsonb_typeof(build) <> 'object' or build is null then
    return ficha;
  end if;

  select coalesce(jsonb_agg(jsonb_build_object(
    'nivel',d.impeto_condicional_nivel,
    'linha_id',d.linha_id
  ) order by d.impeto_condicional_nivel),'[]'::jsonb)
  into degraus
  from (
    select distinct on (alvo.impeto_condicional_nivel)
      alvo.impeto_condicional_nivel,
      alvo.linha_id
    from clube_novo.build_publicacao_exibivel_v3 atual
    join clube_novo.build_publicacao_exibivel_v3 alvo
      on alvo.card_id=atual.card_id
     and alvo.funcao_id=atual.funcao_id
     and alvo.posicao_id=atual.posicao_id
     and alvo.impeto_condicional_codigo=atual.impeto_condicional_codigo
    where atual.linha_id=(build->>'linha_id')::bigint
      and atual.impeto_condicional_codigo is not null
      and alvo.impeto_condicional_nivel between 1 and 3
    order by alvo.impeto_condicional_nivel,alvo.nota_final desc nulls last,alvo.linha_id
  ) d;
  ficha := jsonb_set(ficha,'{dados,degraus_condicionais}',degraus,true);

  if jsonb_typeof(build->'impetos') = 'array' then
    select coalesce(jsonb_agg(elemento.item || jsonb_build_object(
      'cor_visual',cor.cor_visual,
      'cor_visual_estado',coalesce(cor.estado_validacao,'aguardando_mapeamento')
    ) order by elemento.ordem),'[]'::jsonb)
    into impetos
    from jsonb_array_elements(build->'impetos') with ordinality elemento(item,ordem)
    left join clube_novo.impeto_jogo ij on ij.codigo_jogo=case
      when coalesce(elemento.item->>'codigo','') ~ '^[0-9]+$'
      then (elemento.item->>'codigo')::integer else null end
    left join clube_novo.tipo_impeto_cor_visual_jogo cor
      on cor.tipo_raw=ij.tipo_condicao_raw and cor.estado_validacao='confirmada';
    build := jsonb_set(build,'{impetos}',impetos);
  end if;
  sugestoes := clube_novo.site_novo_ficha_sugestoes_v1(
    ficha #>> '{dados,card,card_id}',(build->>'linha_id')::bigint);
  build := build || jsonb_build_object(
    'habilidades_sugeridas',sugestoes->'habilidades',
    'habilidades_sugeridas_estado',sugestoes->>'estado');
  tecnico := build->'tecnico';
  if jsonb_typeof(tecnico)='object' then
    build := jsonb_set(build,'{tecnico}',tecnico || jsonb_build_object(
      'sugeridos',sugestoes->'tecnicos','sugeridos_estado',sugestoes->>'estado'));
  end if;
  build := build || jsonb_build_object('pontos_distribuicao',
    clube_novo.site_novo_contador_pontos_v1(build->'barras',(build->>'orcamento_total')::integer));
  return jsonb_set(ficha,'{dados,build}',build);
end;
$function$;
CREATE OR REPLACE FUNCTION public.frontend_build_publicada_v1(p_card_id text DEFAULT NULL::text, p_funcao_id bigint DEFAULT NULL::bigint, p_limit integer DEFAULT 100, p_offset integer DEFAULT 0)
 RETURNS TABLE(schema_versao text, linha_id bigint, card_id text, carta_nome text, carta_tipo text, carta_box text, carta_overall integer, funcao_id bigint, funcao_codigo text, funcao_nome text, posicao_id integer, posicao_codigo text, posicao_nome text, build_otimizador_id bigint, build_bonificador_id bigint, pontuacao_final numeric, estado_final text, motivo_final text, selo_final_fingerprint text, publicada_em timestamp with time zone, proveniencia jsonb)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
  select 'clube-frontend-build-publicada-v1'::text,
    a.linha_id,a.card_id,c.nome,c.tipo,c.box,c.overall,
    a.funcao_id,coalesce(f.sigla,'')::text,f.rotulo,
    a.posicao_id,coalesce(p.codigo_pt,'')::text,p.nome_pt,
    a.build_otimizador_id,a.build_bonificador_id,a.nota_final,
    'publicada'::text,null::text,a.selo_final_fingerprint,a.publicada_em,a.proveniencia
  from clube_novo.build_publicacao_exibivel_v3 a
  join clube_novo.carta_jogo c on c.card_id=a.card_id
  join clube_novo.funcao_sistema f on f.id=a.funcao_id
  join clube_novo.posicao_jogo p on p.id=a.posicao_id
  where (p_card_id is null or a.card_id=p_card_id)
    and (p_funcao_id is null or a.funcao_id=p_funcao_id)
  order by a.nota_final desc,a.card_id,a.funcao_id,a.posicao_id,a.linha_id
  limit least(greatest(coalesce(p_limit,100),1),500)
  offset greatest(coalesce(p_offset,0),0)
$function$;
CREATE OR REPLACE FUNCTION public.frontend_build_publicada_v2(p_card_id text DEFAULT NULL::text, p_funcao_id bigint DEFAULT NULL::bigint, p_limit integer DEFAULT 100, p_offset integer DEFAULT 0)
 RETURNS TABLE(schema_versao text, publicacao_v2_fingerprint text, linha_id bigint, card_id text, carta_nome text, carta_tipo text, carta_box text, carta_overall integer, foto_url_cloudinary text, funcao_id bigint, funcao_codigo text, funcao_nome text, posicao_id integer, posicao_codigo text, posicao_nome text, build_otimizador_id bigint, build_bonificador_id bigint, tecnico_id bigint, tecnico_nome text, tecnico_bonus jsonb, tecnicos_sugeridos jsonb, barras jsonb, impeto_adicional_codigo integer, impeto_adicional jsonb, impeto_condicional jsonb, impetos jsonb, impetos_adicionaveis jsonb, degraus_publicados jsonb, habilidades_do_card jsonb, habilidades_adicionais jsonb, habilidades_sugeridas jsonb, atributos_finais jsonb, arows_snapshot jsonb, pontuacao_otimizador_bruta_evidencia numeric, pontuacao_otimizador_normalizada numeric, bonus_pe numeric, bonus_fisico_total numeric, bonus_posicao numeric, bonus_playstyle_1 numeric, bonus_playstyle_2 numeric, bonus_ia numeric, bonus_outros jsonb, bonus_total_bonificador numeric, overall_final numeric, pontuacao_final numeric, topo_funcao numeric, percentual_topo numeric, estado_final text, motivo_final text, normalizacao_fingerprint text, publicacao_linha_fingerprint_v2 text, publicada_em timestamp with time zone, proveniencia jsonb, contratacoes_por_box jsonb)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
  /* PORTA UNICA DA TELA. A fila publicada e lida da lista pronta
     clube_novo.build_pontuacao_final_v3_exibivel, que ja vem com nome, foto, funcao,
     posicao, tecnico e impetos gravados e numerada em ordem. Ler direto da conta
     custava 53 segundos com 55 mil linhas e a tela so tem 3. */
  with pagina as materialized (
    /* TRES CAMINHOS SEPARADOS DE PROPOSITO. Num unico SELECT com "ou" o banco
       nao consegue escolher o atalho certo e varre a lista inteira (6 segundos
       para abrir uma ficha). Separados, cada chamada usa o seu atalho. */

    /* 1) FICHA: um card. */
    (select * from clube_novo.build_pontuacao_final_v3_exibivel base
      where p_card_id is not null and base.card_id = p_card_id
        and (p_funcao_id is null or base.funcao_id = p_funcao_id)
      order by base.overall_final desc, base.card_id, base.funcao_id,
        base.posicao_id, base.linha_id
      limit least(greatest(coalesce(p_limit, 100), 1), 500)
      offset greatest(coalesce(p_offset, 0), 0))
    union all
    /* 2) LISTA GERAL: faixa de numeros na fila. Mandar o banco pular N linhas
          o obriga a ler as N primeiras; a fila ja vem numerada. */
    (select * from clube_novo.build_pontuacao_final_v3_exibivel base
      where p_card_id is null and p_funcao_id is null
        and base.ordem_geral > greatest(coalesce(p_offset, 0), 0)
        and base.ordem_geral <= greatest(coalesce(p_offset, 0), 0)
            + least(greatest(coalesce(p_limit, 100), 1), 500)
      order by base.overall_final desc, base.card_id, base.funcao_id,
        base.posicao_id, base.linha_id
      limit least(greatest(coalesce(p_limit, 100), 1), 500))
    union all
    /* 3) LISTA DE UMA FUNCAO: mesma faixa, contada dentro da funcao. */
    (select * from clube_novo.build_pontuacao_final_v3_exibivel base
      where p_card_id is null and p_funcao_id is not null
        and base.funcao_id = p_funcao_id
        and base.ordem_na_funcao > greatest(coalesce(p_offset, 0), 0)
        and base.ordem_na_funcao <= greatest(coalesce(p_offset, 0), 0)
            + least(greatest(coalesce(p_limit, 100), 1), 500)
      order by base.overall_final desc, base.card_id, base.funcao_id,
        base.posicao_id, base.linha_id
      limit least(greatest(coalesce(p_limit, 100), 1), 500))
  ),
  /* CONSTANTES DA FICHA: valem para o card inteiro, nao mudam de linha para
     linha. Calculadas UMA vez -- por linha derrubavam a leitura por tempo. */
  fixos as materialized (
    select
      case when p_card_id is null then '[]'::jsonb
           else coalesce(public.frontend_impetos_adicionaveis_v1(), '[]'::jsonb) end as adicionaveis,
      case when p_card_id is null then '[]'::jsonb
           else coalesce(public.frontend_habilidades_do_card_v1(p_card_id), '[]'::jsonb) end as habs_card
  )
  select
    'clube-frontend-build-publicada-v2'::text,
    v.publicacao_v2_fingerprint, v.linha_id, v.card_id,
    v.carta_nome, v.carta_tipo, v.carta_box, v.carta_overall, v.foto_url_cloudinary,
    v.funcao_id, v.funcao_codigo, v.funcao_nome,
    v.posicao_id, v.posicao_codigo, v.posicao_nome,
    v.build_otimizador_id, v.build_bonificador_id,
    v.tecnico_id, v.tecnico_nome,
    /* DETALHE DA FICHA: so quando a leitura e de UM card. As telas de lista leem
       500 linhas por vez e nao usam nada disto -- calcular por linha ali derruba
       a leitura inteira por tempo (aconteceu em 04/09). */
    case when p_card_id is null then '[]'::jsonb else coalesce(tbon.itens, '[]'::jsonb) end,
    case when p_card_id is null then '[]'::jsonb else coalesce(tsug.itens, '[]'::jsonb) end,
    v.barras,
    v.impeto_adicional_codigo,
    v.impeto_adicional,
    v.impeto_condicional,
    case when p_card_id is null then '[]'::jsonb
         else coalesce(public.frontend_impetos_do_card_v1(v.card_id, v.linha_id), '[]'::jsonb) end,
    fx.adicionaveis,
    case when p_card_id is null then '[]'::jsonb
         else coalesce(public.frontend_degraus_da_linha_v1(v.card_id, v.funcao_id, v.posicao_id), '[]'::jsonb) end,
    clube_novo.filtrar_gemeas_funcao_v12(fx.habs_card,v.funcao_id),
    case when p_card_id is null then '[]'::jsonb
         else clube_novo.filtrar_gemeas_funcao_v12(public.frontend_habilidades_adicionais_v1(v.habilidades_adicionais),v.funcao_id) end,
    case when p_card_id is null then '[]'::jsonb else coalesce(hsug.itens, '[]'::jsonb) end,
    v.atributos_finais, v.arows_snapshot,
    v.pontuacao_otimizador_bruta_evidencia, v.pontuacao_otimizador_normalizada,
    v.bonus_pe, v.bonus_fisico_total, v.bonus_posicao,
    v.bonus_playstyle_1, v.bonus_playstyle_2, v.bonus_ia, v.bonus_outros,
    v.bonus_total_bonificador, v.overall_final, v.overall_final,
    v.topo_funcao, v.percentual_topo, v.estado_final, v.motivo_final,
    v.normalizacao_fingerprint, v.publicacao_linha_fingerprint_v2,
    v.publicada_em, v.proveniencia,
    case when p_card_id is null then '[]'::jsonb else coalesce(cx.itens, '[]'::jsonb) end
  from pagina v
  cross join fixos fx
  left join lateral (
    select jsonb_agg(jsonb_build_object('codigo', ta.codigo_atributo,
      'nome', a.nome_pt, 'delta', ta.delta) order by ta.ordem) as itens
    from clube_novo.tecnico_atributo_jogo ta
    left join clube_novo.atributo_jogo a on a.codigo = ta.codigo_atributo
    where p_card_id is not null and ta.tecnico_id = v.tecnico_id) tbon on true
  left join lateral (
    select jsonb_agg(distinct jsonb_build_object('skill_id', g.skill_id,
      'nome', coalesce(g.nome_pt, g.nome_en, g.nome_no_motor, g.skill_id::text))) as itens
    from unnest(case when p_card_id is null then '{}'::integer[]
                     else coalesce(v.habilidades_adicionais, '{}'::integer[]) end) as a(skill_id)
    join clube_novo.habilidade_jogo hb on hb.skill_id = a.skill_id
    join clube_novo.habilidade_jogo g on g.skill_id = any(hb.gemeas)
      and g.fabricavel and g.pode_rodar and g.tipo=hb.tipo and g.efeito_por_codigo=hb.efeito_por_codigo
    where not (g.skill_id = any(coalesce(v.habilidades_adicionais, '{}'::integer[])))
      and not exists (select 1 from clube_novo.carta_habilidade_jogo ch
                       where ch.card_id = v.card_id and ch.skill_id = g.skill_id)
      and coalesce(g.vetada, false) = false
      and (v.posicao_id = 0 or coalesce(g.so_goleiro, false) = false)
      and (v.posicao_id <> 0 or coalesce(g.so_de_linha, false) = false)
      and not exists (select 1 from clube_novo.habilidade_funcao_bloqueio_otimizador bq
                       where bq.skill_id = g.skill_id and bq.funcao_id = v.funcao_id)) hsug on true
  left join lateral (
    select jsonb_agg(jsonb_build_object('tecnico_id', o.tecnico_id, 'nome', o.nome)
                     order by o.nome) as itens
    from (select ta2.tecnico_id, t2.nome_en as nome
          from clube_novo.tecnico_atributo_jogo ta2
          join clube_novo.tecnico_jogo t2 on t2.id = ta2.tecnico_id
          where p_card_id is not null and ta2.tecnico_id <> v.tecnico_id
            and t2.nome_en is distinct from (select t0.nome_en
                                             from clube_novo.tecnico_jogo t0
                                             where t0.id = v.tecnico_id)
          group by ta2.tecnico_id, t2.nome_en
          having string_agg(ta2.codigo_atributo || ':' || ta2.delta, '|'
                            order by ta2.codigo_atributo) = (
            select string_agg(ta1.codigo_atributo || ':' || ta1.delta, '|'
                              order by ta1.codigo_atributo)
            from clube_novo.tecnico_atributo_jogo ta1
            where ta1.tecnico_id = v.tecnico_id)) o) tsug on true
  left join lateral (
    select case when p_card_id is null then null
                else clube_novo.contratacoes_por_box_build_v1(
                       v.card_id, v.funcao_nome, v.percentual_topo) end as itens) cx on true
  order by v.overall_final desc, v.card_id, v.funcao_id, v.posicao_id, v.linha_id
$function$;
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
      select a.card_id,max(a.nota_final) pontuacao_maxima
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
               case when btrim(p_busca)<>'' and clube_novo.site_novo_texto_corresponde_v1(bp.nome,p_busca) then 0 else 1 end,
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
      from clube_novo.build_publicacao_exibivel_v3 a
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
               case when btrim(p_busca)<>'' and clube_novo.site_novo_texto_corresponde_v1(b.nome,p_busca) then 0 else 1 end,
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
    topos as materialized (
      select funcao_id,max(nota_final) topo_funcao
      from clube_novo.build_publicacao_exibivel_v3
      group by funcao_id
    ),
    ordem_home as materialized (
      select box->>'nome' box_nome,card->>'card_id' card_id,pos ordem
      from clube_novo.box_sincronizacao_efhub_v1 a
      cross join lateral jsonb_array_elements(a.payload->'boxes') box
      cross join lateral jsonb_array_elements(box->'cards') with ordinality as c(card,pos)
      where a.fingerprint in (select distinct origem_fingerprint from ofertas)
    ),
    avaliadas_fonte as materialized (
      select a.card_id,a.linha_id,a.funcao_id,fs.rotulo funcao_nome,
        coalesce(p.codigo_pt,'') posicao_codigo,
        100::numeric*a.nota_final/t.topo_funcao percentual_topo,
        a.nota_final overall_final
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
      select c.card_id,c.nome,x.box_nome as box,h.ordem as ordem_home,c.overall,
        (select pj.codigo_pt
         from clube_novo.carta_posicao_principal_jogo cp
         join clube_novo.posicao_jogo pj on pj.id=cp.posicao_id
         where cp.card_id=c.card_id order by cp.posicao_id limit 1) as posicao,
        c.foto_url_cloudinary,
        (select max(v.pontuacao_maxima) from avaliadas v where v.card_id=c.card_id) pontuacao_maxima,
        coalesce((
          select jsonb_agg(jsonb_build_object(
            'linha_id',v.linha_id::text,'funcao',v.funcao_nome,'posicao',v.posicao_codigo,
            'pontuacao',v.overall_final,'percentual_topo',v.percentual_topo,
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
      left join ordem_home h on h.box_nome=x.box_nome and h.card_id=c.card_id
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
                case when btrim(p_busca)<>'' and strpos(lower(extensions.unaccent(b.nome)),lower(extensions.unaccent(btrim(p_busca))))>0 then 0 else 1 end,
                b.ordem_home nulls last,b.card_id collate "C") ordem_preview
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
    topos as materialized (
      select funcao_id,max(nota_final) topo_funcao
      from clube_novo.build_publicacao_exibivel_v3
      group by funcao_id
    ),
    avaliadas_fonte as materialized (
      select a.card_id,a.linha_id,a.funcao_id,fs.rotulo funcao_nome,
        coalesce(p.codigo_pt,'') posicao_codigo,
        100::numeric*a.nota_final/t.topo_funcao percentual_topo,
        a.nota_final overall_final
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
        coalesce((
          select jsonb_agg(jsonb_build_object(
            'linha_id',v.linha_id::text,'funcao',v.funcao_nome,'posicao',v.posicao_codigo,
            'pontuacao',v.overall_final,'percentual_topo',v.percentual_topo,
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
      order by (analises#>>'{0,percentual_topo}')::numeric desc nulls last,
        (analises#>>'{0,pontuacao}')::numeric desc nulls last,card_id collate "C"
      limit p_limite offset p_offset
    )
    select jsonb_build_object(
      'contrato','site-novo-boxes-v1','versao',1,'degrau',p_degrau,'modo','cards',
      'box',p_box,'busca',p_busca,'total',(select count(*) from selecionadas),
      'total_cards',(select count(*) from selecionadas),'limite',p_limite,'offset',p_offset,
      'itens',coalesce((select jsonb_agg(to_jsonb(p) order by
        (p.analises#>>'{0,percentual_topo}')::numeric desc nulls last,
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
