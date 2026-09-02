-- Mantem os gates V2, mas parte das 613 linhas seladas em vez de recalcular
-- toda a classificacao V1 a cada pagina de Builds.
begin;

drop function if exists public.frontend_build_estado_v2(text);
drop function if exists public.frontend_build_publicada_v2(text, bigint, integer, integer);
drop view if exists clube_novo.build_pontuacao_final_v2;

create view clube_novo.build_pontuacao_final_v2
with (security_barrier = true)
as
with validas as materialized (
  select
    l.id as linha_id, l.card_id, l.funcao_id, l.posicao_id,
    l.build_otimizador_id, l.build_bonificador_id,
    o.tecnico_id, o.barras, o.impeto_adicional_codigo,
    o.habilidades_adicionais,
    n.atributos_finais, n.arows_snapshot,
    n.pontuacao_otimizador_bruta_selada as pontuacao_otimizador_bruta_evidencia,
    n.pontuacao_otimizador_normalizada,
    n.bonus_pe, n.bonus_fisico_total, n.bonus_posicao,
    n.bonus_playstyle_1, n.bonus_playstyle_2, n.bonus_ia, n.bonus_outros,
    n.bonus_total_bonificador,
    n.overall_final,
    n.normalizacao_fingerprint,
    n.calculo_banco_fingerprint,
    n.carta_fingerprint, n.formula_fingerprint, n.contrato_fingerprint,
    n.otimizador_resultado_fingerprint,
    n.bonificador_resultado_fingerprint,
    l.publicacao_fingerprint as publicacao_fingerprint_v1,
    l.publicada_em,
    encode(extensions.digest(convert_to(jsonb_build_object(
      'contrato', 'clube-novo-pontuacao-final-v2',
      'linha_id', l.id,
      'calculo_banco_fingerprint', n.calculo_banco_fingerprint,
      'bonificador_resultado_fingerprint', n.bonificador_resultado_fingerprint,
      'overall_final', n.overall_final,
      'publicacao_fingerprint_v1', l.publicacao_fingerprint
    )::text, 'UTF8'), 'sha256'), 'hex') as publicacao_linha_fingerprint_v2
  from clube_novo.build_pontuacao_normalizada_v2 n
  join clube_novo.build_linha_card l on l.id = n.linha_id
  join clube_novo.build_otimizador o on o.id = l.build_otimizador_id
  join clube_novo.build_bonificador b on b.id = l.build_bonificador_id
  where l.publicada_em is not null
    and l.lote_teste_id is null
    and not (l.pendencias @> array['teste_nao_publicado'])
    and l.estado_otimizador = 'concluido'
    and o.concluido_em is not null
    and o.carta_versao = l.carta_versao
    and o.resultado_fingerprint = l.snapshot_otimizador_fingerprint
    and o.motor_versao = l.otimizador_motor_versao
    and o.contrato_versao = l.otimizador_contrato_versao
    and o.formula_fingerprint = l.otimizador_formula_fingerprint_esperado
    and o.contrato_fingerprint = l.otimizador_contrato_fingerprint_esperado
    and b.concluido_em is not null
    and b.carta_versao = l.carta_versao
    and b.resultado_fingerprint = l.snapshot_bonificador_fingerprint
    and b.motor_versao = l.bonificador_motor_versao
    and b.contrato_versao = l.bonificador_contrato_versao
    and coalesce(b.faltou, '{}'::text[]) = '{}'::text[]
    and l.build_otimizador_id = n.build_otimizador_id
    and l.build_bonificador_id = n.build_bonificador_id
    and o.resultado_fingerprint = n.otimizador_resultado_fingerprint
    and b.resultado_fingerprint = n.bonificador_resultado_fingerprint
    and o.carta_fingerprint = n.carta_fingerprint
    and o.formula_fingerprint = n.formula_fingerprint
    and o.contrato_fingerprint = n.contrato_fingerprint
    and o.pontuacao = n.pontuacao_otimizador_bruta_selada
    and b.bonus_pe = n.bonus_pe
    and b.bonus_fisico_total = n.bonus_fisico_total
    and b.bonus_posicao = n.bonus_posicao
    and b.bonus_playstyle_1 = n.bonus_playstyle_1
    and b.bonus_playstyle_2 = n.bonus_playstyle_2
    and b.bonus_ia = n.bonus_ia
    and coalesce(b.bonus_outros, '{}'::jsonb) = n.bonus_outros
    and b.bonus_total = n.bonus_total_bonificador
    and l.publicacao_fingerprint = n.publicacao_fingerprint_v1
    and l.publicada_em = n.publicada_em_v1
), geracao as materialized (
  select encode(extensions.digest(convert_to(jsonb_build_object(
    'contrato', 'clube-novo-publicacao-build-v2',
    'linhas', jsonb_agg(
      validas.publicacao_linha_fingerprint_v2 order by validas.linha_id)
  )::text, 'UTF8'), 'sha256'), 'hex') as publicacao_v2_fingerprint
  from validas
), com_topo as (
  select v.*,
    max(v.overall_final) over (partition by v.funcao_id) as topo_funcao
  from validas v
)
select
  g.publicacao_v2_fingerprint,
  c.*,
  case when c.topo_funcao > 0
       then 100 * c.overall_final / c.topo_funcao end as percentual_topo,
  'publicada'::text as estado_final,
  'PUBLICADA_V2_NORMALIZADA_NO_BANCO'::text as motivo_final,
  jsonb_build_object(
    'contrato', 'clube-novo-pontuacao-final-v2',
    'linha_id', c.linha_id,
    'calculo_banco_fingerprint', c.calculo_banco_fingerprint,
    'otimizador', jsonb_build_object(
      'id', c.build_otimizador_id,
      'resultado_fingerprint', c.otimizador_resultado_fingerprint,
      'pontuacao_bruta_apenas_evidencia', c.pontuacao_otimizador_bruta_evidencia,
      'pontuacao_normalizada', c.pontuacao_otimizador_normalizada),
    'bonificador', jsonb_build_object(
      'id', c.build_bonificador_id,
      'resultado_fingerprint', c.bonificador_resultado_fingerprint,
      'componentes', jsonb_build_object(
        'pe', c.bonus_pe,
        'fisico', c.bonus_fisico_total,
        'posicao', c.bonus_posicao,
        'playstyle_1', c.bonus_playstyle_1,
        'playstyle_2', c.bonus_playstyle_2,
        'ia', c.bonus_ia,
        'outros', c.bonus_outros),
      'bonus_total', c.bonus_total_bonificador),
    'pontuacao_final_oficial', c.overall_final,
    'publicacao_v1', c.publicacao_fingerprint_v1,
    'publicacao_v2', c.publicacao_linha_fingerprint_v2
  ) as proveniencia
from com_topo c
cross join geracao g;

create function public.frontend_build_publicada_v2(
  p_card_id text default null,
  p_funcao_id bigint default null,
  p_limit integer default 100,
  p_offset integer default 0
)
returns table(
  schema_versao text,
  publicacao_v2_fingerprint text,
  linha_id bigint,
  card_id text,
  carta_nome text,
  carta_tipo text,
  carta_box text,
  carta_overall integer,
  foto_url_cloudinary text,
  ficha jsonb,
  funcao_id bigint,
  funcao_codigo text,
  funcao_nome text,
  posicao_id integer,
  posicao_codigo text,
  posicao_nome text,
  build_otimizador_id bigint,
  build_bonificador_id bigint,
  tecnico_id bigint,
  tecnico_nome text,
  barras jsonb,
  impeto_adicional_codigo integer,
  habilidades_adicionais jsonb,
  atributos_finais jsonb,
  arows_snapshot jsonb,
  pontuacao_otimizador_bruta_evidencia numeric,
  pontuacao_otimizador_normalizada numeric,
  bonus_total_bonificador numeric,
  overall_final numeric,
  pontuacao_final numeric,
  topo_funcao numeric,
  percentual_topo numeric,
  estado_final text,
  motivo_final text,
  normalizacao_fingerprint text,
  publicacao_linha_fingerprint_v2 text,
  publicada_em timestamp with time zone,
  proveniencia jsonb
)
language sql
stable
security definer
set search_path = ''
as $$
  with pagina as materialized (
    select *
    from clube_novo.build_pontuacao_final_v2 base
    where (p_card_id is null or base.card_id = p_card_id)
      and (p_funcao_id is null or base.funcao_id = p_funcao_id)
    order by base.overall_final desc, base.card_id, base.funcao_id,
      base.posicao_id, base.linha_id
    limit least(greatest(coalesce(p_limit, 100), 1), 500)
    offset greatest(coalesce(p_offset, 0), 0)
  )
  select
    'clube-frontend-build-publicada-v2'::text,
    v.publicacao_v2_fingerprint,
    v.linha_id, v.card_id, c.nome, c.tipo,
    case when c.box is not null and btrim(c.box) <> ''
           and lower(btrim(c.box)) <> all(array['0','dummy','[[not use]]'])
         then btrim(c.box) end,
    c.overall,
    case when c.foto_url_cloudinary ~
      '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'
      then c.foto_url_cloudinary end,
    to_jsonb(fi),
    v.funcao_id, coalesce(fs.sigla, ''), fs.rotulo,
    v.posicao_id, coalesce(p.codigo_pt, ''), p.nome_pt,
    v.build_otimizador_id, v.build_bonificador_id,
    v.tecnico_id, coalesce(t.nome_en, v.tecnico_id::text),
    v.barras, v.impeto_adicional_codigo,
    coalesce(habs.itens, '[]'::jsonb),
    v.atributos_finais, v.arows_snapshot,
    v.pontuacao_otimizador_bruta_evidencia,
    v.pontuacao_otimizador_normalizada,
    v.bonus_total_bonificador,
    v.overall_final, v.overall_final,
    v.topo_funcao, v.percentual_topo,
    v.estado_final, v.motivo_final,
    v.normalizacao_fingerprint,
    v.publicacao_linha_fingerprint_v2,
    v.publicada_em, v.proveniencia
  from pagina v
  join clube_novo.carta_jogo c on c.card_id = v.card_id
  join public.frontend_ficha_v1 fi on fi.card_id = v.card_id
  join clube_novo.funcao_sistema fs on fs.id = v.funcao_id
  join clube_novo.posicao_jogo p on p.id = v.posicao_id
  left join clube_novo.tecnico_jogo t on t.id = v.tecnico_id
  left join lateral (
    select jsonb_agg(jsonb_build_object(
      'skill_id', h.skill_id,
      'nome', coalesce(h.nome_pt, h.nome_en, h.nome_no_motor, h.skill_id::text)
    ) order by u.ordem) as itens
    from unnest(coalesce(v.habilidades_adicionais, '{}'::integer[]))
      with ordinality as u(skill_id, ordem)
    join clube_novo.habilidade_jogo h on h.skill_id = u.skill_id
  ) habs on true
  order by v.overall_final desc, v.card_id, v.funcao_id,
    v.posicao_id, v.linha_id
$$;

create function public.frontend_build_estado_v2(p_card_id text)
returns table(build_publicada boolean, build_indisponivel_codigo text)
language sql
stable
security definer
set search_path = ''
as $$
  select
    exists (
      select 1 from clube_novo.build_pontuacao_final_v2 v
      where v.card_id = p_card_id
    ) as build_publicada,
    case
      when exists (
        select 1 from clube_novo.build_pontuacao_final_v2 v
        where v.card_id = p_card_id
      ) then null::text
      when exists (
        select 1 from clube_novo.build_pontuacao_final_v1 f
        where f.card_id = p_card_id and f.estado_final = 'publicada'
      ) then 'AGUARDANDO_NORMALIZACAO_V2'
      when exists (
        select 1 from clube_novo.build_pontuacao_final_v1 f
        where f.card_id = p_card_id
          and f.estado_final in ('aguardando_bonificador',
            'bonificador_nao_concluido', 'selo_bonificador_incompativel')
      ) then 'AGUARDANDO_BONIFICADOR'
      when exists (
        select 1 from clube_novo.build_linha_card l
        where l.card_id = p_card_id
      ) then 'AGUARDANDO_OTIMIZADOR'
      else 'SEM_BUILD_PUBLICADA'
    end as build_indisponivel_codigo
  where exists (
    select 1 from clube_novo.carta_jogo c where c.card_id = p_card_id
  )
$$;

revoke all on clube_novo.build_pontuacao_final_v2
  from public, anon, authenticated;
grant select on clube_novo.build_pontuacao_final_v2 to service_role;
revoke all on function public.frontend_build_publicada_v2(text, bigint, integer, integer)
  from public, anon, authenticated;
revoke all on function public.frontend_build_estado_v2(text)
  from public, anon, authenticated;
grant execute on function public.frontend_build_publicada_v2(text, bigint, integer, integer),
  public.frontend_build_estado_v2(text)
  to service_role;

notify pgrst, 'reload schema';
commit;
