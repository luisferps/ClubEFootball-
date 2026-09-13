create or replace function public.site_novo_busca_v1(
  p_busca text,
  p_limite integer default 48,
  p_offset integer default 0,
  p_degrau integer default 3
)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
set jit = 'off'
set statement_timeout = '5s'
as $function$
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
    join clube_novo.build_publicacao_linha_ativa_v1 a on a.card_id = b.card_id
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

comment on function public.site_novo_busca_v1(text, integer, integer, integer) is
  'Busca pública do Site Novo; ordena cards pela maior pontuação total publicada no degrau condicional selecionado.';

revoke all on function public.site_novo_busca_v1(text, integer, integer, integer) from public;
grant execute on function public.site_novo_busca_v1(text, integer, integer, integer) to anon, authenticated;

notify pgrst, 'reload schema';

