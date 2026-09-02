-- A Ficha fisica continua no contrato public.frontend_ficha_v1. Esta RPC
-- devolve somente a Build V2 publicada; assim a pagina de Ranking nao executa
-- uma Ficha completa para cada linha e a Ficha so busca seu card quando aberta.
-- Nao libera anon/authenticated: a liberacao continua no gate separado.
begin;

drop function if exists public.frontend_build_publicada_v2(text, bigint, integer, integer);

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
  bonus_pe numeric,
  bonus_fisico_total numeric,
  bonus_posicao numeric,
  bonus_playstyle_1 numeric,
  bonus_playstyle_2 numeric,
  bonus_ia numeric,
  bonus_outros jsonb,
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
      '^https://res\\.cloudinary\\.com/[A-Za-z0-9_-]+/image/upload/'
      then c.foto_url_cloudinary end,
    v.funcao_id, coalesce(fs.sigla, ''), fs.rotulo,
    v.posicao_id, coalesce(p.codigo_pt, ''), p.nome_pt,
    v.build_otimizador_id, v.build_bonificador_id,
    v.tecnico_id, coalesce(t.nome_en, v.tecnico_id::text),
    v.barras, v.impeto_adicional_codigo,
    coalesce(habs.itens, '[]'::jsonb),
    v.atributos_finais, v.arows_snapshot,
    v.pontuacao_otimizador_bruta_evidencia,
    v.pontuacao_otimizador_normalizada,
    v.bonus_pe, v.bonus_fisico_total, v.bonus_posicao,
    v.bonus_playstyle_1, v.bonus_playstyle_2, v.bonus_ia, v.bonus_outros,
    v.bonus_total_bonificador,
    v.overall_final, v.overall_final,
    v.topo_funcao, v.percentual_topo,
    v.estado_final, v.motivo_final,
    v.normalizacao_fingerprint,
    v.publicacao_linha_fingerprint_v2,
    v.publicada_em, v.proveniencia
  from pagina v
  join clube_novo.carta_jogo c on c.card_id = v.card_id
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

revoke all on function public.frontend_build_publicada_v2(text, bigint, integer, integer)
  from public, anon, authenticated;
grant execute on function public.frontend_build_publicada_v2(text, bigint, integer, integer)
  to service_role;

comment on function public.frontend_build_publicada_v2(text, bigint, integer, integer) is
  'Contrato V2 somente-leitura para Ranking, Elenco e overlay da Ficha. A nota oficial e overall_final = normalizada calculada no banco + bonus auditavel; a pontuacao bruta do Otimizador e evidencia, nunca OVR. Ficha fisica fica no contrato proprio frontend_ficha_v1.';

notify pgrst, 'reload schema';
commit;
