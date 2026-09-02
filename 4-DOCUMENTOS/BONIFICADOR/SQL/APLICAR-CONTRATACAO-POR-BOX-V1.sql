-- Contrato de contratação por Box, separado da pontuação final V2.
--
-- Regra de estado:
--   public.boxes.status = 'atual'    -> em_andamento: percentual + etiqueta
--                                      calculados dinamicamente no Clube Novo.
--   public.boxes.status = 'anterior' -> finalizada: somente snapshot histórico,
--                                      jamais recalculado pela leitura pública.
--
-- A migração importa o retrato histórico uma única vez, sem modificar a
-- origem. A versão da régua dos retratos antigos não existe na origem; por
-- isso ela fica explicitamente marcada como HISTORICO_SEM_REGUA_COMPROVADA,
-- sem inferir ou reproduzir a regra antiga.

begin;

create table if not exists clube_novo.regua_contratacao_versao_v1 (
  versao text primary key,
  estado text not null check (estado in ('vigente', 'historico_sem_regua_comprovada')),
  descricao text not null,
  criada_em timestamp with time zone not null default now()
);

create unique index if not exists regua_contratacao_versao_v1_uma_vigente
  on clube_novo.regua_contratacao_versao_v1 ((estado))
  where estado = 'vigente';

create table if not exists clube_novo.regua_contratacao_faixa_v1 (
  regua_versao text not null
    references clube_novo.regua_contratacao_versao_v1(versao),
  codigo text not null check (codigo ~ '^[a-z0-9_]+$'),
  ordem smallint not null check (ordem between 1 and 99),
  percentual_minimo numeric not null check (percentual_minimo >= 0 and percentual_minimo <= 100),
  rotulo text not null check (btrim(rotulo) <> ''),
  primary key (regua_versao, codigo),
  unique (regua_versao, ordem),
  unique (regua_versao, percentual_minimo)
);

create table if not exists clube_novo.box_contexto_contratacao_v1 (
  box_id bigint primary key,
  box_nome text not null check (btrim(box_nome) <> ''),
  estado_box text not null check (estado_box in ('em_andamento', 'finalizada')),
  status_origem text not null check (status_origem in ('atual', 'anterior')),
  origem_fingerprint text not null check (origem_fingerprint ~ '^[a-f0-9]{64}$'),
  capturado_em timestamp with time zone not null default now(),
  check (
    (estado_box = 'em_andamento' and status_origem = 'atual')
    or (estado_box = 'finalizada' and status_origem = 'anterior')
  )
);

create table if not exists clube_novo.box_card_em_andamento_v1 (
  box_id bigint not null
    references clube_novo.box_contexto_contratacao_v1(box_id) on delete restrict,
  card_id text not null check (card_id ~ '^[1-9][0-9]*$'),
  capturado_em timestamp with time zone not null default now(),
  primary key (box_id, card_id)
);

create table if not exists clube_novo.box_card_contratacao_snapshot_v1 (
  box_id bigint not null
    references clube_novo.box_contexto_contratacao_v1(box_id) on delete restrict,
  card_id text not null check (card_id ~ '^[1-9][0-9]*$'),
  funcao_rotulo text not null check (btrim(funcao_rotulo) <> ''),
  pontuacao_snapshot numeric not null,
  percentual_topo_snapshot numeric not null check (percentual_topo_snapshot >= 0 and percentual_topo_snapshot <= 100),
  etiqueta_codigo text not null check (etiqueta_codigo ~ '^[a-z0-9_]+$'),
  etiqueta_rotulo text not null check (btrim(etiqueta_rotulo) <> ''),
  regua_versao_snapshot text not null
    references clube_novo.regua_contratacao_versao_v1(versao),
  congelado_em timestamp with time zone not null,
  origem text not null check (btrim(origem) <> ''),
  origem_fingerprint text not null check (origem_fingerprint ~ '^[a-f0-9]{64}$'),
  primary key (box_id, card_id)
);

create index if not exists box_card_contratacao_snapshot_v1_card_funcao_idx
  on clube_novo.box_card_contratacao_snapshot_v1(card_id, lower(funcao_rotulo));

insert into clube_novo.regua_contratacao_versao_v1(versao, estado, descricao)
values
  ('CONTRATACAO_V1_2026_09_02', 'vigente',
   'Régua canônica dinâmica autorizada em 2026-09-02.'),
  ('HISTORICO_SEM_REGUA_COMPROVADA', 'historico_sem_regua_comprovada',
   'Marcador de proveniência: retrato histórico importado sem versão de régua comprovada na origem.')
on conflict (versao) do nothing;

insert into clube_novo.regua_contratacao_faixa_v1(
  regua_versao, codigo, ordem, percentual_minimo, rotulo
)
values
  ('CONTRATACAO_V1_2026_09_02', 'qualquer_preco', 1, 99.995, 'PAGAR QUALQUER PREÇO'),
  ('CONTRATACAO_V1_2026_09_02', 'caro',            2, 99,     'PAGAR CARO'),
  ('CONTRATACAO_V1_2026_09_02', 'pagar',           3, 98,     'PAGAR'),
  ('CONTRATACAO_V1_2026_09_02', 'pouco',           4, 97,     'PAGAR POUCO'),
  ('CONTRATACAO_V1_2026_09_02', 'muito_pouco',     5, 96,     'PAGAR MUITO POUCO'),
  ('CONTRATACAO_V1_2026_09_02', 'nao_pagar',       6, 0,      'NÃO PAGAR')
on conflict (regua_versao, codigo) do nothing;

-- Migração de metadados: a origem histórica só é lida nesta operação.
insert into clube_novo.box_contexto_contratacao_v1(
  box_id, box_nome, estado_box, status_origem, origem_fingerprint, capturado_em
)
select
  b.id,
  btrim(b.nome),
  case b.status when 'atual' then 'em_andamento' when 'anterior' then 'finalizada' end,
  b.status,
  encode(extensions.digest(convert_to(jsonb_build_object(
    'fonte', 'public.boxes', 'id', b.id, 'nome', b.nome, 'status', b.status,
    'card_ids', b.card_ids, 'atualizado_em', b.atualizado_em
  )::text, 'UTF8'), 'sha256'), 'hex'),
  now()
from public.boxes b
where b.status in ('atual', 'anterior')
  and btrim(coalesce(b.nome, '')) <> ''
on conflict (box_id) do nothing;

-- Membership das Boxes em andamento. A pontuação e a etiqueta NÃO são gravadas
-- aqui: a função pública as calcula da régua vigente e da pontuação V2 atual.
insert into clube_novo.box_card_em_andamento_v1(box_id, card_id, capturado_em)
select distinct
  b.id,
  btrim(e.card_id),
  now()
from public.boxes b
cross join lateral jsonb_array_elements_text(
  case when jsonb_typeof(b.card_ids) = 'array' then b.card_ids else '[]'::jsonb end
) as e(card_id)
join clube_novo.box_contexto_contratacao_v1 cb
  on cb.box_id = b.id and cb.estado_box = 'em_andamento'
where b.status = 'atual'
  and btrim(e.card_id) ~ '^[1-9][0-9]*$'
on conflict (box_id, card_id) do nothing;

-- Snapshot de Boxes finalizadas: cópia literal dos valores existentes, sem
-- recalcular percentual, trocar etiqueta ou inferir a versão antiga da régua.
insert into clube_novo.box_card_contratacao_snapshot_v1(
  box_id, card_id, funcao_rotulo, pontuacao_snapshot, percentual_topo_snapshot,
  etiqueta_codigo, etiqueta_rotulo, regua_versao_snapshot, congelado_em,
  origem, origem_fingerprint
)
select
  r.box_id,
  r.card_id,
  btrim(r.funcao),
  r.pontuacao,
  r.recomendacao,
  r.etiqueta_codigo,
  btrim(r.etiqueta),
  'HISTORICO_SEM_REGUA_COMPROVADA',
  r.congelado_em,
  btrim(r.origem),
  encode(extensions.digest(convert_to(jsonb_build_object(
    'fonte', 'public.box_card_retratos', 'box_id', r.box_id, 'card_id', r.card_id,
    'funcao', r.funcao, 'pontuacao', r.pontuacao, 'percentual', r.recomendacao,
    'etiqueta_codigo', r.etiqueta_codigo, 'etiqueta', r.etiqueta,
    'congelado_em', r.congelado_em, 'origem', r.origem
  )::text, 'UTF8'), 'sha256'), 'hex')
from public.box_card_retratos r
join public.boxes b on b.id = r.box_id and b.status = 'anterior'
join clube_novo.box_contexto_contratacao_v1 cb
  on cb.box_id = r.box_id and cb.estado_box = 'finalizada'
where btrim(coalesce(r.card_id, '')) ~ '^[1-9][0-9]*$'
  and btrim(coalesce(r.funcao, '')) <> ''
  and r.pontuacao is not null
  and r.recomendacao is not null
  and btrim(coalesce(r.etiqueta_codigo, '')) <> ''
  and btrim(coalesce(r.etiqueta, '')) <> ''
  and r.congelado_em is not null
  and btrim(coalesce(r.origem, '')) <> ''
on conflict (box_id, card_id) do nothing;

create or replace function clube_novo.bloquear_mutacao_snapshot_contratacao_v1()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  raise exception 'snapshot histórico imutável: reprocessamento explícito é obrigatório';
end;
$$;

drop trigger if exists bloquear_mutacao_snapshot_contratacao_v1
  on clube_novo.box_card_contratacao_snapshot_v1;
create trigger bloquear_mutacao_snapshot_contratacao_v1
  before update or delete on clube_novo.box_card_contratacao_snapshot_v1
  for each row execute function clube_novo.bloquear_mutacao_snapshot_contratacao_v1();

do $guard$
begin
  if (select count(*) from clube_novo.regua_contratacao_faixa_v1
      where regua_versao = 'CONTRATACAO_V1_2026_09_02') <> 6 then
    raise exception 'régua V1 incompleta';
  end if;
  if exists (
    select 1
    from (values
      ('qualquer_preco'::text, 1::smallint, 99.995::numeric, 'PAGAR QUALQUER PREÇO'::text),
      ('caro',            2::smallint, 99::numeric,     'PAGAR CARO'),
      ('pagar',           3::smallint, 98::numeric,     'PAGAR'),
      ('pouco',           4::smallint, 97::numeric,     'PAGAR POUCO'),
      ('muito_pouco',     5::smallint, 96::numeric,     'PAGAR MUITO POUCO'),
      ('nao_pagar',       6::smallint, 0::numeric,      'NÃO PAGAR')
    ) esperado(codigo, ordem, percentual_minimo, rotulo)
    left join clube_novo.regua_contratacao_faixa_v1 f
      on f.regua_versao = 'CONTRATACAO_V1_2026_09_02'
     and f.codigo = esperado.codigo
     and f.ordem = esperado.ordem
     and f.percentual_minimo = esperado.percentual_minimo
     and f.rotulo = esperado.rotulo
    where f.codigo is null
  ) then
    raise exception 'régua V1 diverge da autorização';
  end if;
  if exists (
    select 1
    from public.box_card_retratos r
    join public.boxes b on b.id = r.box_id and b.status = 'anterior'
    left join clube_novo.box_card_contratacao_snapshot_v1 s
      on s.box_id = r.box_id and s.card_id = r.card_id
    where s.box_id is null
  ) then
    raise exception 'snapshot histórico não foi importado integralmente';
  end if;
  if exists (
    select 1
    from public.boxes b
    cross join lateral jsonb_array_elements_text(
      case when jsonb_typeof(b.card_ids) = 'array' then b.card_ids else '[]'::jsonb end
    ) e(card_id)
    left join clube_novo.box_card_em_andamento_v1 a
      on a.box_id = b.id and a.card_id = btrim(e.card_id)
    where b.status = 'atual'
      and btrim(e.card_id) ~ '^[1-9][0-9]*$'
      and a.box_id is null
  ) then
    raise exception 'membership de Box em andamento não foi importada integralmente';
  end if;
end;
$guard$;

create or replace function clube_novo.contratacoes_por_box_build_v1(
  p_card_id text,
  p_funcao_rotulo text,
  p_percentual_topo_dinamico numeric
)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
  with faixa_vigente as (
    select f.regua_versao, f.codigo, f.percentual_minimo, f.rotulo
    from clube_novo.regua_contratacao_faixa_v1 f
    join clube_novo.regua_contratacao_versao_v1 v
      on v.versao = f.regua_versao and v.estado = 'vigente'
  ), dinamicas as (
    select
      c.box_id, c.box_nome, c.estado_box,
      'dinamica'::text as origem_percentual,
      p_percentual_topo_dinamico as percentual_topo,
      faixa.codigo as etiqueta_codigo,
      faixa.rotulo as etiqueta_rotulo,
      faixa.regua_versao,
      null::timestamptz as congelado_em
    from clube_novo.box_card_em_andamento_v1 m
    join clube_novo.box_contexto_contratacao_v1 c
      on c.box_id = m.box_id and c.estado_box = 'em_andamento'
    join lateral (
      select f.*
      from faixa_vigente f
      where p_percentual_topo_dinamico >= f.percentual_minimo
      order by f.percentual_minimo desc
      limit 1
    ) faixa on true
    where m.card_id = p_card_id
  ), historicas as (
    select
      c.box_id, c.box_nome, c.estado_box,
      'snapshot'::text as origem_percentual,
      s.percentual_topo_snapshot as percentual_topo,
      s.etiqueta_codigo,
      s.etiqueta_rotulo,
      s.regua_versao_snapshot as regua_versao,
      s.congelado_em
    from clube_novo.box_card_contratacao_snapshot_v1 s
    join clube_novo.box_contexto_contratacao_v1 c
      on c.box_id = s.box_id and c.estado_box = 'finalizada'
    where s.card_id = p_card_id
      and lower(btrim(s.funcao_rotulo)) = lower(btrim(p_funcao_rotulo))
  ), contextos as (
    select * from dinamicas
    union all
    select * from historicas
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'box_id', box_id,
    'box_nome', box_nome,
    'estado_box', estado_box,
    'origem_percentual', origem_percentual,
    'percentual_topo', percentual_topo,
    'etiqueta_codigo', etiqueta_codigo,
    'etiqueta_rotulo', etiqueta_rotulo,
    'regua_versao', regua_versao,
    'congelado_em', congelado_em
  ) order by estado_box, box_nome, box_id), '[]'::jsonb)
  from contextos;
$$;

-- A RPC já liberada continua com paginação máxima de 500. Ela só recebe uma
-- coluna contextual nova; não publica, não recalcula builds e não altera linhas.
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
  proveniencia jsonb,
  contratacoes_por_box jsonb
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
    v.publicada_em, v.proveniencia,
    coalesce(cx.itens, '[]'::jsonb)
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
  left join lateral (
    select clube_novo.contratacoes_por_box_build_v1(
      v.card_id, fs.rotulo, v.percentual_topo
    ) as itens
  ) cx on true
  order by v.overall_final desc, v.card_id, v.funcao_id,
    v.posicao_id, v.linha_id
$$;

revoke all on table
  clube_novo.regua_contratacao_versao_v1,
  clube_novo.regua_contratacao_faixa_v1,
  clube_novo.box_contexto_contratacao_v1,
  clube_novo.box_card_em_andamento_v1,
  clube_novo.box_card_contratacao_snapshot_v1
  from public, anon, authenticated;
grant select on table
  clube_novo.regua_contratacao_versao_v1,
  clube_novo.regua_contratacao_faixa_v1,
  clube_novo.box_contexto_contratacao_v1,
  clube_novo.box_card_em_andamento_v1,
  clube_novo.box_card_contratacao_snapshot_v1
  to service_role;
revoke all on function clube_novo.contratacoes_por_box_build_v1(text, text, numeric)
  from public, anon, authenticated;
grant execute on function clube_novo.contratacoes_por_box_build_v1(text, text, numeric)
  to service_role;

revoke all on function public.frontend_build_publicada_v2(text, bigint, integer, integer)
  from public;
grant execute on function public.frontend_build_publicada_v2(text, bigint, integer, integer)
  to anon, authenticated, service_role;

comment on function public.frontend_build_publicada_v2(text, bigint, integer, integer) is
  'Contrato V2 somente-leitura. Nota oficial: normalizada calculada no banco + bônus auditável. contratacoes_por_box é contextual: em_andamento usa a régua vigente; finalizada lê somente snapshot histórico importado, sem recalcular.';

notify pgrst, 'reload schema';
commit;
