-- Contrato canônico final V1: somente leitura, sem publicar ou alterar linhas.
-- A equação publicada é a já aprovada: pontuação do Otimizador + bônus total.
begin;

create or replace view clube_novo.build_pontuacao_final_v1
with (security_barrier = true)
as
with base as (
  select
    l.id as linha_id,
    l.card_id,
    l.funcao_id,
    l.posicao_id,
    l.build_otimizador_id,
    l.build_bonificador_id,
    l.carta_versao,
    l.carta_fingerprint as linha_carta_fingerprint,
    l.estado as estado_linha,
    l.estado_otimizador,
    l.pendencias,
    l.execucao_tipo,
    l.lote_teste_id,
    l.lote_producao_id,
    l.publicada_em,
    l.publicacao_fingerprint,
    l.snapshot_otimizador_fingerprint,
    l.snapshot_bonificador_fingerprint,
    l.otimizador_motor_versao,
    l.otimizador_contrato_versao,
    l.otimizador_formula_fingerprint_esperado,
    l.otimizador_contrato_fingerprint_esperado,
    l.bonificador_motor_versao,
    l.bonificador_contrato_versao,
    o.pontuacao as pontuacao_otimizador,
    o.concluido_em as otimizador_concluido_em,
    o.motor_versao as otimizador_motor_versao_resultado,
    o.contrato_versao as otimizador_contrato_versao_resultado,
    o.contrato_fingerprint as otimizador_contrato_fingerprint_resultado,
    o.formula_fingerprint as otimizador_formula_fingerprint,
    o.carta_versao as otimizador_carta_versao,
    o.carta_fingerprint as otimizador_carta_fingerprint,
    o.resultado_fingerprint as otimizador_resultado_fingerprint,
    b.bonus_total as bonus_total_bonificador,
    b.concluido_em as bonificador_concluido_em,
    b.motor_versao as bonificador_motor_versao_resultado,
    b.contrato_versao as bonificador_contrato_versao_resultado,
    b.contrato_fingerprint as bonificador_contrato_fingerprint_resultado,
    b.formula_fingerprint as bonificador_formula_fingerprint,
    b.carta_versao as bonificador_carta_versao,
    b.carta_fingerprint as bonificador_carta_fingerprint,
    b.resultado_fingerprint as bonificador_resultado_fingerprint,
    b.faltou as bonificador_faltou
  from clube_novo.build_linha_card l
  left join clube_novo.build_otimizador o on o.id = l.build_otimizador_id
  left join clube_novo.build_bonificador b on b.id = l.build_bonificador_id
), selos as (
  select base.*,
    (
      build_otimizador_id is not null
      and estado_otimizador = 'concluido'
      and otimizador_concluido_em is not null
      and otimizador_carta_versao = carta_versao
      and otimizador_resultado_fingerprint = snapshot_otimizador_fingerprint
      and otimizador_motor_versao_resultado = otimizador_motor_versao
      and otimizador_contrato_versao_resultado = otimizador_contrato_versao
      and otimizador_formula_fingerprint = otimizador_formula_fingerprint_esperado
      and otimizador_contrato_fingerprint_resultado = otimizador_contrato_fingerprint_esperado
    ) as selo_otimizador_valido,
    (
      build_bonificador_id is not null
      and bonificador_concluido_em is not null
      and bonificador_carta_versao = carta_versao
      and bonificador_resultado_fingerprint = snapshot_bonificador_fingerprint
      and bonificador_motor_versao_resultado = bonificador_motor_versao
      and bonificador_contrato_versao_resultado = bonificador_contrato_versao
      and coalesce(bonificador_faltou, '{}'::text[]) = '{}'::text[]
    ) as selo_bonificador_valido,
    (lote_teste_id is not null or pendencias @> array['teste_nao_publicado']::text[]) as lote_de_teste
  from base
), classificacao as (
  select selos.*,
    case
      when build_otimizador_id is null then 'aguardando_otimizador'
      when estado_otimizador <> 'concluido' or otimizador_concluido_em is null then 'otimizador_nao_concluido'
      when build_bonificador_id is null then 'aguardando_bonificador'
      when bonificador_concluido_em is null then 'bonificador_nao_concluido'
      when not selo_otimizador_valido then 'selo_otimizador_incompativel'
      when not selo_bonificador_valido then 'selo_bonificador_incompativel'
      when lote_de_teste then 'bloqueada_lote_de_teste'
      when publicada_em is not null then 'publicada'
      else 'elegivel_para_publicacao'
    end as estado_final
  from selos
)
select
  linha_id, card_id, funcao_id, posicao_id,
  build_otimizador_id, build_bonificador_id,
  pontuacao_otimizador, bonus_total_bonificador,
  case when selo_otimizador_valido and selo_bonificador_valido
       then round(pontuacao_otimizador + bonus_total_bonificador, 4) end as pontuacao_final_candidata,
  case when estado_final = 'publicada'
       then round(pontuacao_otimizador + bonus_total_bonificador, 4) end as pontuacao_final_publicada,
  estado_final,
  case estado_final
    when 'aguardando_otimizador' then 'RESULTADO_OTIMIZADOR_AUSENTE'
    when 'otimizador_nao_concluido' then 'OTIMIZADOR_NAO_CONCLUIDO'
    when 'aguardando_bonificador' then 'RESULTADO_BONIFICADOR_AUSENTE'
    when 'bonificador_nao_concluido' then 'BONIFICADOR_NAO_CONCLUIDO'
    when 'selo_otimizador_incompativel' then 'SELO_OTIMIZADOR_INCOMPATIVEL'
    when 'selo_bonificador_incompativel' then 'SELO_BONIFICADOR_INCOMPATIVEL'
    when 'bloqueada_lote_de_teste' then 'LOTE_DE_TESTE_NAO_PUBLICAVEL'
    when 'publicada' then 'PUBLICADA'
    else 'ELEGIVEL_PARA_PUBLICACAO'
  end as motivo_final,
  estado_final in ('elegivel_para_publicacao', 'publicada') as elegivel_publicacao,
  estado_final = 'publicada' as publicacao_liberada,
  publicada_em, publicacao_fingerprint,
  carta_versao, linha_carta_fingerprint,
  otimizador_concluido_em, bonificador_concluido_em,
  otimizador_motor_versao_resultado, otimizador_contrato_versao_resultado,
  otimizador_contrato_fingerprint_resultado, otimizador_formula_fingerprint,
  otimizador_carta_fingerprint, otimizador_resultado_fingerprint,
  bonificador_motor_versao_resultado, bonificador_contrato_versao_resultado,
  bonificador_contrato_fingerprint_resultado, bonificador_formula_fingerprint,
  bonificador_carta_fingerprint, bonificador_resultado_fingerprint,
  case when selo_otimizador_valido and selo_bonificador_valido then
    encode(extensions.digest(convert_to(jsonb_build_object(
      'contrato', 'clube-novo-pontuacao-final-v1',
      'linha_id', linha_id, 'card_id', card_id, 'funcao_id', funcao_id, 'posicao_id', posicao_id,
      'build_otimizador_id', build_otimizador_id,
      'otimizador_resultado_fingerprint', otimizador_resultado_fingerprint,
      'build_bonificador_id', build_bonificador_id,
      'bonificador_resultado_fingerprint', bonificador_resultado_fingerprint,
      'pontuacao_final', round(pontuacao_otimizador + bonus_total_bonificador, 4)
    )::text, 'UTF8'), 'sha256'), 'hex')
  end as selo_final_fingerprint,
  jsonb_build_object(
    'contrato', 'clube-novo-pontuacao-final-v1',
    'linha', jsonb_build_object('id', linha_id, 'carta_versao', carta_versao,
      'fingerprint', linha_carta_fingerprint),
    'otimizador', jsonb_build_object('id', build_otimizador_id,
      'resultado_fingerprint', otimizador_resultado_fingerprint),
    'bonificador', jsonb_build_object('id', build_bonificador_id,
      'resultado_fingerprint', bonificador_resultado_fingerprint)
  ) as proveniencia
from classificacao;

comment on view clube_novo.build_pontuacao_final_v1 is
  'Projecao selada V1 da Build candidata e do Bonificador. Nao publica linhas, nao recalcula motores e so declara pontuacao final publicada quando a publicacao explicita ja existe.';

revoke all on clube_novo.build_pontuacao_final_v1 from public, anon, authenticated;
grant usage on schema clube_novo to service_role, bonificador_runtime;
grant select on clube_novo.build_pontuacao_final_v1 to service_role, bonificador_runtime;

create or replace function public.frontend_build_publicada_v1(
  p_card_id text default null,
  p_funcao_id bigint default null,
  p_limit integer default 100,
  p_offset integer default 0
)
returns table(
  schema_versao text,
  linha_id bigint,
  card_id text,
  carta_nome text,
  carta_tipo text,
  carta_box text,
  carta_overall integer,
  funcao_id bigint,
  funcao_codigo text,
  funcao_nome text,
  posicao_id integer,
  posicao_codigo text,
  posicao_nome text,
  build_otimizador_id bigint,
  build_bonificador_id bigint,
  pontuacao_final numeric,
  estado_final text,
  motivo_final text,
  selo_final_fingerprint text,
  publicada_em timestamp with time zone,
  proveniencia jsonb
)
language sql
stable
security definer
set search_path = ''
as $$
  select
    'clube-frontend-build-publicada-v1'::text,
    f.linha_id, f.card_id, c.nome, c.tipo, c.box, c.overall,
    f.funcao_id, coalesce(fs.sigla, '')::text, fs.rotulo,
    f.posicao_id, coalesce(p.codigo_pt, '')::text, p.nome_pt,
    f.build_otimizador_id, f.build_bonificador_id,
    f.pontuacao_final_publicada, f.estado_final, f.motivo_final,
    f.selo_final_fingerprint, f.publicada_em, f.proveniencia
  from clube_novo.build_pontuacao_final_v1 f
  join clube_novo.carta_jogo c on c.card_id = f.card_id
  join clube_novo.funcao_sistema fs on fs.id = f.funcao_id
  join clube_novo.posicao_jogo p on p.id = f.posicao_id
  where f.publicacao_liberada
    and (p_card_id is null or f.card_id = p_card_id)
    and (p_funcao_id is null or f.funcao_id = p_funcao_id)
  order by f.pontuacao_final_publicada desc, f.card_id, f.funcao_id, f.posicao_id, f.linha_id
  limit least(greatest(coalesce(p_limit, 100), 1), 500)
  offset greatest(coalesce(p_offset, 0), 0)
$$;

revoke all on function public.frontend_build_publicada_v1(text, bigint, integer, integer)
  from public, anon, authenticated;
grant execute on function public.frontend_build_publicada_v1(text, bigint, integer, integer)
  to anon, authenticated, service_role;

comment on function public.frontend_build_publicada_v1(text, bigint, integer, integer) is
  'RPC SELECT-only para Ranking, Elenco e Ficha. Retorna exclusivamente Builds explicitamente publicadas e seladas; candidatos e lotes de teste nunca vazam para o front-end.';

notify pgrst, 'reload schema';
commit;
