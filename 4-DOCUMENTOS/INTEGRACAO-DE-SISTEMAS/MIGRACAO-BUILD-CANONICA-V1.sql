begin;

create table clube_novo.build (
  id bigint generated always as identity primary key,
  funcao_id bigint not null references clube_novo.funcao_sistema(id),
  combinacao_fingerprint text not null unique,
  formula_fingerprint text not null,
  regua_fingerprint text not null,
  busca_fingerprint text not null,
  desempate_fingerprint text not null,
  estado text not null default 'rascunho'
    check (estado in ('rascunho','ativa','invalida')),
  configuracao_extra jsonb not null default '{}'::jsonb,
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);

create table clube_novo.build_barra (
  build_id bigint not null references clube_novo.build(id) on delete cascade,
  grupo_codigo text not null,
  nivel smallint not null check (nivel >= 0),
  ordem smallint not null check (ordem >= 0),
  primary key (build_id, grupo_codigo),
  unique (build_id, ordem)
);

create table clube_novo.build_tecnico (
  build_id bigint primary key references clube_novo.build(id) on delete cascade,
  tecnico_id bigint not null references clube_novo.tecnico_jogo(id),
  codigo_estilo text not null,
  proficiencia smallint not null check (proficiencia >= 0),
  boosts jsonb not null default '[]'::jsonb
);

create table clube_novo.build_habilidade (
  build_id bigint not null references clube_novo.build(id) on delete cascade,
  skill_id integer not null references clube_novo.habilidade_jogo(skill_id),
  ordem smallint not null check (ordem >= 0),
  origem text not null check (origem in ('nativa','adicionada','neutra')),
  primary key (build_id, skill_id, origem),
  unique (build_id, ordem, origem)
);

create table clube_novo.build_impeto (
  build_id bigint not null references clube_novo.build(id) on delete cascade,
  slot smallint not null check (slot in (1,2)),
  codigo_impeto integer references clube_novo.impeto_jogo(codigo_jogo),
  estado text not null check (estado in ('sem_impeto','vaga','ativo','condicional')),
  primary key (build_id, slot),
  check ((estado in ('ativo','condicional') and codigo_impeto is not null)
      or (estado in ('sem_impeto','vaga') and codigo_impeto is null))
);

create table clube_novo.build_carta (
  id bigint generated always as identity primary key,
  build_id bigint not null references clube_novo.build(id),
  card_id text not null references clube_novo.carta_jogo(card_id),
  carta_versao text not null,
  carta_fingerprint text not null,
  estado text not null default 'pendente'
    check (estado in ('pendente','pronto','nao_aplicavel','invalido')),
  pontuacao_vencedora numeric,
  rank_vencedor integer check (rank_vencedor is null or rank_vencedor = 1),
  criterio_desempate jsonb not null default '{}'::jsonb,
  combinacoes_avaliadas bigint check (combinacoes_avaliadas is null or combinacoes_avaliadas >= 0),
  combinacoes_podadas bigint check (combinacoes_podadas is null or combinacoes_podadas >= 0),
  tela_fingerprint text,
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now(),
  unique (build_id, card_id, carta_fingerprint)
);

create index build_carta_card_id_idx on clube_novo.build_carta(card_id);
create index build_carta_estado_idx on clube_novo.build_carta(estado);

create table clube_novo.build_carta_atributo_snapshot (
  build_carta_id bigint not null references clube_novo.build_carta(id) on delete cascade,
  codigo_atributo text not null references clube_novo.atributo_jogo(codigo),
  ordem smallint not null check (ordem >= 0),
  valor_base numeric not null,
  evolucao_aplicada numeric,
  valor_apos_evolucao numeric,
  efeito_tecnico numeric,
  boost_tecnico numeric,
  efeito_impeto numeric,
  efeito_habilidade numeric,
  valor_final_interno numeric,
  valor_final_exibido numeric not null,
  alvo numeric,
  peso numeric,
  pontos numeric,
  detalhes jsonb not null default '{}'::jsonb,
  primary key (build_carta_id, codigo_atributo),
  unique (build_carta_id, ordem)
);

create table clube_novo.build_resultado_otimizador (
  build_carta_id bigint primary key references clube_novo.build_carta(id) on delete cascade,
  estado text not null default 'pendente'
    check (estado in ('pendente','pronto','nao_aplicavel','invalido')),
  contrato_versao text not null,
  contrato_fingerprint text not null,
  carta_fingerprint text not null,
  formula_fingerprint text not null,
  pontuacao numeric,
  rank_vencedor integer check (rank_vencedor is null or rank_vencedor = 1),
  payload jsonb,
  payload_fingerprint text,
  concluido_em timestamptz,
  atualizado_em timestamptz not null default now(),
  check (estado <> 'pronto' or
    (pontuacao is not null and rank_vencedor = 1 and payload is not null and
     payload_fingerprint is not null and concluido_em is not null))
);

create table clube_novo.build_resultado_bonificador (
  build_carta_id bigint primary key references clube_novo.build_carta(id) on delete cascade,
  estado text not null default 'pendente'
    check (estado in ('pendente','pronto','nao_aplicavel','invalido')),
  contrato_versao text not null,
  contrato_fingerprint text not null,
  carta_fingerprint text not null,
  formula_fingerprint text not null,
  bonus_total numeric,
  payload jsonb,
  payload_fingerprint text,
  concluido_em timestamptz,
  atualizado_em timestamptz not null default now(),
  check (estado <> 'pronto' or
    (bonus_total is not null and payload is not null and payload_fingerprint is not null and concluido_em is not null)),
  check (estado <> 'nao_aplicavel' or concluido_em is not null)
);

create table clube_novo.build_publicacao (
  build_carta_id bigint primary key references clube_novo.build_carta(id) on delete cascade,
  estado text not null default 'pendente'
    check (estado in ('pendente','publicada','invalida')),
  payload_tela jsonb,
  payload_fingerprint text,
  publicada_em timestamptz,
  atualizado_em timestamptz not null default now(),
  check (estado <> 'publicada' or
    (payload_tela is not null and payload_fingerprint is not null and publicada_em is not null))
);

create function clube_novo.validar_publicacao_build_v1()
returns trigger language plpgsql security invoker set search_path = '' as $$
declare
  v_carta_fp text;
  v_otim clube_novo.build_resultado_otimizador%rowtype;
  v_bonus clube_novo.build_resultado_bonificador%rowtype;
begin
  if new.estado <> 'publicada' then return new; end if;
  select carta_fingerprint into v_carta_fp
    from clube_novo.build_carta where id = new.build_carta_id;
  select * into v_otim from clube_novo.build_resultado_otimizador
    where build_carta_id = new.build_carta_id;
  select * into v_bonus from clube_novo.build_resultado_bonificador
    where build_carta_id = new.build_carta_id;
  if v_otim.build_carta_id is null or v_otim.estado <> 'pronto' then
    raise exception 'publicacao recusada: resultado do Otimizador nao esta pronto';
  end if;
  if v_bonus.build_carta_id is null or v_bonus.estado not in ('pronto','nao_aplicavel') then
    raise exception 'publicacao recusada: resultado do Bonificador nao esta pronto/não aplicavel';
  end if;
  if v_otim.carta_fingerprint <> v_carta_fp or v_bonus.carta_fingerprint <> v_carta_fp then
    raise exception 'publicacao recusada: versoes/fingerprints da carta divergem';
  end if;
  return new;
end $$;

create trigger build_publicacao_gate_v1
before insert or update on clube_novo.build_publicacao
for each row execute function clube_novo.validar_publicacao_build_v1();

alter table clube_novo.build enable row level security;
alter table clube_novo.build_barra enable row level security;
alter table clube_novo.build_tecnico enable row level security;
alter table clube_novo.build_habilidade enable row level security;
alter table clube_novo.build_impeto enable row level security;
alter table clube_novo.build_carta enable row level security;
alter table clube_novo.build_carta_atributo_snapshot enable row level security;
alter table clube_novo.build_resultado_otimizador enable row level security;
alter table clube_novo.build_resultado_bonificador enable row level security;
alter table clube_novo.build_publicacao enable row level security;

revoke all on table
  clube_novo.build,
  clube_novo.build_barra,
  clube_novo.build_tecnico,
  clube_novo.build_habilidade,
  clube_novo.build_impeto,
  clube_novo.build_carta,
  clube_novo.build_carta_atributo_snapshot,
  clube_novo.build_resultado_otimizador,
  clube_novo.build_resultado_bonificador,
  clube_novo.build_publicacao
from anon, authenticated;
revoke all on function clube_novo.validar_publicacao_build_v1() from public, anon, authenticated;
grant execute on function clube_novo.validar_publicacao_build_v1() to service_role;

commit;
