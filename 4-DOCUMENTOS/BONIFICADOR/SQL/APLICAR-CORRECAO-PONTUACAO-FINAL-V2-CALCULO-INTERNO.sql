-- Corrige a materializacao V2 provisoria para que a conta oficial nasca no banco.
-- Nao muda a publicacao V1, nao inicia motores e mantem a RPC V2 fechada ate a
-- paridade banco x formula da tela ser comprovada.
begin;

lock table clube_novo.build_pontuacao_normalizada_v2 in access exclusive mode;

do $precondicao$
declare
  v_total integer;
  v_divergencias integer;
begin
  select count(*) into v_total
  from clube_novo.build_pontuacao_normalizada_v2;

  if v_total <> 613 then
    raise exception 'PARE: a correcao V2 esperava 613 linhas, encontrou %', v_total;
  end if;

  select count(*) into v_divergencias
  from clube_novo.build_pontuacao_normalizada_v2 n
  join clube_novo.build_pontuacao_final_v1 f on f.linha_id = n.linha_id
  join clube_novo.build_bonificador b on b.id = n.build_bonificador_id
  where not f.publicacao_liberada
     or f.estado_final <> 'publicada'
     or f.build_otimizador_id is distinct from n.build_otimizador_id
     or f.build_bonificador_id is distinct from n.build_bonificador_id
     or f.otimizador_resultado_fingerprint is distinct from n.otimizador_resultado_fingerprint
     or f.bonificador_resultado_fingerprint is distinct from n.bonificador_resultado_fingerprint
     or f.pontuacao_otimizador is distinct from n.pontuacao_otimizador_bruta_selada
     or f.bonus_total_bonificador is distinct from n.bonus_total_bonificador
     or b.resultado_fingerprint is distinct from n.bonificador_resultado_fingerprint;

  if v_divergencias <> 0 then
    raise exception 'PARE: % linhas V2 divergiram dos resultados selados atuais', v_divergencias;
  end if;
end
$precondicao$;

create or replace function clube_novo.calcular_numerador_normalizacao_v2(
  p_atributos_finais jsonb,
  p_arows_snapshot jsonb
)
returns numeric
language sql
immutable
strict
parallel safe
set search_path = ''
as $$
  select sum(
    (item->>1)::numeric
      * (p_atributos_finais->>((item->>0)::integer))::numeric
  )
  from jsonb_array_elements(p_arows_snapshot) item
  where (item->>1)::numeric <> 0
$$;

create or replace function clube_novo.calcular_denominador_normalizacao_v2(
  p_arows_snapshot jsonb
)
returns numeric
language sql
immutable
strict
parallel safe
set search_path = ''
as $$
  select sum((item->>1)::numeric * (item->>2)::numeric)
  from jsonb_array_elements(p_arows_snapshot) item
  where (item->>1)::numeric <> 0
$$;

create or replace function clube_novo.calcular_pontuacao_normalizada_v2(
  p_atributos_finais jsonb,
  p_arows_snapshot jsonb
)
returns numeric
language sql
immutable
strict
parallel safe
set search_path = ''
as $$
  select case when d > 0 then 100 * n / d else null::numeric end
  from (
    select
      clube_novo.calcular_numerador_normalizacao_v2(
        p_atributos_finais, p_arows_snapshot) as n,
      clube_novo.calcular_denominador_normalizacao_v2(
        p_arows_snapshot) as d
  ) calculo
$$;

create or replace function clube_novo.fingerprint_calculo_pontuacao_v2(
  p_linha_id bigint,
  p_atributos_finais jsonb,
  p_arows_snapshot jsonb,
  p_bonus_total numeric
)
returns text
language sql
immutable
strict
parallel safe
set search_path = ''
as $$
  select encode(extensions.digest(convert_to(jsonb_build_object(
    'contrato', 'clube-novo-calculo-pontuacao-v2-banco',
    'linha_id', p_linha_id,
    'atributos_finais', p_atributos_finais,
    'arows_snapshot', p_arows_snapshot,
    'pontuacao_normalizada',
      clube_novo.calcular_pontuacao_normalizada_v2(
        p_atributos_finais, p_arows_snapshot),
    'bonus_total', p_bonus_total,
    'overall_final',
      clube_novo.calcular_pontuacao_normalizada_v2(
        p_atributos_finais, p_arows_snapshot) + p_bonus_total
  )::text, 'UTF8'), 'sha256'), 'hex')
$$;

revoke all on function clube_novo.calcular_numerador_normalizacao_v2(jsonb, jsonb)
  from public, anon, authenticated;
revoke all on function clube_novo.calcular_denominador_normalizacao_v2(jsonb)
  from public, anon, authenticated;
revoke all on function clube_novo.calcular_pontuacao_normalizada_v2(jsonb, jsonb)
  from public, anon, authenticated;
revoke all on function clube_novo.fingerprint_calculo_pontuacao_v2(bigint, jsonb, jsonb, numeric)
  from public, anon, authenticated;
grant execute on function clube_novo.calcular_numerador_normalizacao_v2(jsonb, jsonb),
  clube_novo.calcular_denominador_normalizacao_v2(jsonb),
  clube_novo.calcular_pontuacao_normalizada_v2(jsonb, jsonb),
  clube_novo.fingerprint_calculo_pontuacao_v2(bigint, jsonb, jsonb, numeric)
  to service_role;

comment on function clube_novo.calcular_pontuacao_normalizada_v2(jsonb, jsonb) is
  'Formula imutavel da tela: 100 * soma(peso * atributo final) / soma(peso * alvo), ignorando peso zero e sem arredondamento, piso, teto, K ou populacao.';

-- A RPC e a view dependem das colunas que passam a ser geradas.
drop function if exists public.frontend_build_estado_v2(text);
drop function if exists public.frontend_build_publicada_v2(text, bigint, integer, integer);
drop view if exists clube_novo.build_pontuacao_final_v2;

alter table clube_novo.build_pontuacao_normalizada_v2
  add column pontuacao_normalizada_recomputada_evidencia numeric,
  add column overall_final_recomputado_evidencia numeric,
  add column bonus_pe numeric,
  add column bonus_fisico_total numeric,
  add column bonus_posicao numeric,
  add column bonus_playstyle_1 numeric,
  add column bonus_playstyle_2 numeric,
  add column bonus_ia numeric,
  add column bonus_outros jsonb;

update clube_novo.build_pontuacao_normalizada_v2 n
set
  pontuacao_normalizada_recomputada_evidencia = n.pontuacao_otimizador_normalizada,
  overall_final_recomputado_evidencia = n.overall_final,
  bonus_pe = b.bonus_pe,
  bonus_fisico_total = b.bonus_fisico_total,
  bonus_posicao = b.bonus_posicao,
  bonus_playstyle_1 = b.bonus_playstyle_1,
  bonus_playstyle_2 = b.bonus_playstyle_2,
  bonus_ia = b.bonus_ia,
  bonus_outros = coalesce(b.bonus_outros, '{}'::jsonb)
from clube_novo.build_bonificador b
where b.id = n.build_bonificador_id;

alter table clube_novo.build_pontuacao_normalizada_v2
  alter column pontuacao_normalizada_recomputada_evidencia set not null,
  alter column overall_final_recomputado_evidencia set not null,
  alter column bonus_pe set not null,
  alter column bonus_fisico_total set not null,
  alter column bonus_posicao set not null,
  alter column bonus_playstyle_1 set not null,
  alter column bonus_playstyle_2 set not null,
  alter column bonus_ia set not null,
  alter column bonus_outros set not null;

alter table clube_novo.build_pontuacao_normalizada_v2
  drop constraint if exists build_pontuacao_normalizada_v2_denominador_check,
  drop constraint if exists build_pontuacao_normalizada_v2_paridade_normalizada_check,
  drop constraint if exists build_pontuacao_normalizada_v2_paridade_overall_check,
  drop column numerador,
  drop column denominador,
  drop column pontuacao_otimizador_normalizada,
  drop column overall_final;

alter table clube_novo.build_pontuacao_normalizada_v2
  add column numerador numeric generated always as
    (clube_novo.calcular_numerador_normalizacao_v2(
      atributos_finais, arows_snapshot)) stored,
  add column denominador numeric generated always as
    (clube_novo.calcular_denominador_normalizacao_v2(
      arows_snapshot)) stored,
  add column pontuacao_otimizador_normalizada numeric generated always as
    (clube_novo.calcular_pontuacao_normalizada_v2(
      atributos_finais, arows_snapshot)) stored,
  add column overall_final numeric generated always as
    (clube_novo.calcular_pontuacao_normalizada_v2(
      atributos_finais, arows_snapshot) + bonus_total_bonificador) stored,
  add column calculo_banco_fingerprint text generated always as
    (clube_novo.fingerprint_calculo_pontuacao_v2(
      linha_id, atributos_finais, arows_snapshot,
      bonus_total_bonificador)) stored;

alter table clube_novo.build_pontuacao_normalizada_v2
  add constraint build_pontuacao_normalizada_v2_denominador_banco_check
    check (denominador > 0),
  add constraint build_pontuacao_normalizada_v2_paridade_tela_check
    check (abs(pontuacao_normalizada_recomputada_evidencia
      - pontuacao_otimizador_normalizada) <= 0.000000000001),
  add constraint build_pontuacao_normalizada_v2_paridade_final_check
    check (abs(overall_final_recomputado_evidencia
      - overall_final) <= 0.000000000001),
  add constraint build_pontuacao_normalizada_v2_bonus_componentes_check
    check (bonus_total_bonificador = round(
      bonus_pe + bonus_fisico_total + bonus_posicao
      + bonus_playstyle_1 + bonus_playstyle_2 + bonus_ia, 4)),
  add constraint build_pontuacao_normalizada_v2_calculo_banco_fingerprint_check
    check (calculo_banco_fingerprint ~ '^[0-9a-f]{64}$');

comment on column clube_novo.build_pontuacao_normalizada_v2.pontuacao_otimizador_bruta_selada is
  'Pontuacao nao linear usada pelo Otimizador para escolher a Build; somente evidencia, nunca OVR.';
comment on column clube_novo.build_pontuacao_normalizada_v2.pontuacao_otimizador_normalizada is
  'Coluna gerada e armazenada no banco pela formula percentual do molde da tela.';
comment on column clube_novo.build_pontuacao_normalizada_v2.overall_final is
  'Unica nota oficial: pontuacao normalizada gerada + bonus total selado.';

create view clube_novo.build_pontuacao_final_v2
with (security_barrier = true)
as
with validas as (
  select
    f.linha_id, f.card_id, f.funcao_id, f.posicao_id,
    f.build_otimizador_id, f.build_bonificador_id,
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
    f.publicacao_fingerprint as publicacao_fingerprint_v1,
    f.publicada_em,
    encode(extensions.digest(convert_to(jsonb_build_object(
      'contrato', 'clube-novo-pontuacao-final-v2',
      'linha_id', f.linha_id,
      'calculo_banco_fingerprint', n.calculo_banco_fingerprint,
      'bonificador_resultado_fingerprint', n.bonificador_resultado_fingerprint,
      'overall_final', n.overall_final,
      'publicacao_fingerprint_v1', f.publicacao_fingerprint
    )::text, 'UTF8'), 'sha256'), 'hex') as publicacao_linha_fingerprint_v2
  from clube_novo.build_pontuacao_final_v1 f
  join clube_novo.build_pontuacao_normalizada_v2 n on n.linha_id = f.linha_id
  join clube_novo.build_otimizador o on o.id = f.build_otimizador_id
  join clube_novo.build_bonificador b on b.id = f.build_bonificador_id
  where f.publicacao_liberada
    and f.estado_final = 'publicada'
    and f.build_otimizador_id = n.build_otimizador_id
    and f.build_bonificador_id = n.build_bonificador_id
    and f.otimizador_resultado_fingerprint = n.otimizador_resultado_fingerprint
    and f.bonificador_resultado_fingerprint = n.bonificador_resultado_fingerprint
    and f.otimizador_carta_fingerprint = n.carta_fingerprint
    and f.otimizador_formula_fingerprint = n.formula_fingerprint
    and f.otimizador_contrato_fingerprint_resultado = n.contrato_fingerprint
    and f.pontuacao_otimizador = n.pontuacao_otimizador_bruta_selada
    and f.bonus_total_bonificador = n.bonus_total_bonificador
    and b.bonus_pe = n.bonus_pe
    and b.bonus_fisico_total = n.bonus_fisico_total
    and b.bonus_posicao = n.bonus_posicao
    and b.bonus_playstyle_1 = n.bonus_playstyle_1
    and b.bonus_playstyle_2 = n.bonus_playstyle_2
    and b.bonus_ia = n.bonus_ia
    and coalesce(b.bonus_outros, '{}'::jsonb) = n.bonus_outros
    and b.bonus_total = n.bonus_total_bonificador
    and f.publicacao_fingerprint = n.publicacao_fingerprint_v1
    and f.publicada_em = n.publicada_em_v1
), geracao as (
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

revoke all on clube_novo.build_pontuacao_final_v2
  from public, anon, authenticated;
grant select on clube_novo.build_pontuacao_final_v2 to service_role;

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
  from (
    select *
    from clube_novo.build_pontuacao_final_v2 base
    where (p_card_id is null or base.card_id = p_card_id)
      and (p_funcao_id is null or base.funcao_id = p_funcao_id)
    order by base.overall_final desc, base.card_id, base.funcao_id,
      base.posicao_id, base.linha_id
    limit least(greatest(coalesce(p_limit, 100), 1), 500)
    offset greatest(coalesce(p_offset, 0), 0)
  ) v
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

revoke all on function public.frontend_build_publicada_v2(text, bigint, integer, integer)
  from public, anon, authenticated;
revoke all on function public.frontend_build_estado_v2(text)
  from public, anon, authenticated;
grant execute on function public.frontend_build_publicada_v2(text, bigint, integer, integer),
  public.frontend_build_estado_v2(text)
  to service_role;

notify pgrst, 'reload schema';
commit;
