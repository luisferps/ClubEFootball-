begin;

drop trigger if exists build_publicacao_gate_v2 on clube_novo.build_publicacao;
drop function if exists clube_novo.validar_publicacao_build_v2();

drop table if exists clube_novo.build_publicacao;
drop table if exists clube_novo.build_resultado_bonificador;
drop table if exists clube_novo.build_resultado_otimizador;
drop table if exists clube_novo.build_atributo_snapshot;
drop table if exists clube_novo.build_impeto;
drop table if exists clube_novo.build_habilidade;
drop table if exists clube_novo.build_tecnico;
drop table if exists clube_novo.build_barra;
drop table if exists clube_novo.build;

create table clube_novo.build_otimizador (
  id bigint generated always as identity primary key,
  tecnico_id bigint not null references clube_novo.tecnico_jogo(id),
  barras jsonb not null,
  impeto_adicional_codigo integer references clube_novo.impeto_jogo(codigo_jogo),
  habilidades_adicionais integer[] not null default '{}'::integer[],
  pontuacao numeric not null,
  contrato_versao text not null,
  contrato_fingerprint text not null,
  carta_versao text not null,
  carta_fingerprint text not null,
  formula_fingerprint text not null,
  resultado_fingerprint text not null unique,
  concluido_em timestamptz not null default now(),
  check (jsonb_typeof(barras) = 'object'),
  check (cardinality(habilidades_adicionais) <= 5),
  check (array_position(habilidades_adicionais, null) is null)
);

create table clube_novo.build_bonificador (
  id bigint generated always as identity primary key,
  bonus_pe numeric not null,
  bonus_corpo_fisico numeric not null,
  bonus_posicao numeric not null,
  bonus_playstyle_1 numeric not null,
  bonus_playstyle_2 numeric not null,
  bonus_ia numeric not null,
  bonus_outros jsonb not null default '{}'::jsonb,
  bonus_total numeric not null,
  contrato_versao text not null,
  contrato_fingerprint text not null,
  carta_versao text not null,
  carta_fingerprint text not null,
  formula_fingerprint text not null,
  resultado_fingerprint text not null unique,
  concluido_em timestamptz not null default now(),
  check (jsonb_typeof(bonus_outros) = 'object')
);

create table clube_novo.build_linha_card (
  id bigint generated always as identity primary key,
  card_id text not null references clube_novo.carta_jogo(card_id),
  funcao_id bigint not null references clube_novo.funcao_sistema(id),
  posicao_id integer not null references clube_novo.posicao_jogo(id),
  build_otimizador_id bigint references clube_novo.build_otimizador(id),
  build_bonificador_id bigint references clube_novo.build_bonificador(id),
  carta_versao text not null,
  carta_fingerprint text not null,
  estado text not null default 'pendente'
    check (estado in ('pendente','pronta','publicada','invalida')),
  pendencias text[] not null default '{}'::text[],
  publicacao_fingerprint text,
  publicada_em timestamptz,
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now(),
  unique (build_otimizador_id),
  unique (build_bonificador_id),
  check (array_position(pendencias, null) is null),
  check (
    estado <> 'publicada' or
    (publicacao_fingerprint is not null and publicada_em is not null)
  )
);

create unique index build_linha_card_uma_ativa_por_contexto_uidx
  on clube_novo.build_linha_card(card_id, funcao_id, posicao_id)
  where estado <> 'invalida';

create index build_linha_card_card_id_idx
  on clube_novo.build_linha_card(card_id);
create index build_linha_card_estado_idx
  on clube_novo.build_linha_card(estado);

create function clube_novo.validar_build_linha_publicavel_v3()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_otim clube_novo.build_otimizador%rowtype;
  v_bonus clube_novo.build_bonificador%rowtype;
begin
  if new.estado not in ('pronta','publicada') then
    return new;
  end if;

  if new.build_otimizador_id is null or new.build_bonificador_id is null then
    raise exception 'linha recusada: resultados do Otimizador e do Bonificador sao obrigatorios';
  end if;

  select * into v_otim
    from clube_novo.build_otimizador where id = new.build_otimizador_id;
  select * into v_bonus
    from clube_novo.build_bonificador where id = new.build_bonificador_id;

  if v_otim.id is null or v_bonus.id is null then
    raise exception 'linha recusada: resultado de motor inexistente';
  end if;

  if v_otim.carta_versao <> new.carta_versao
     or v_bonus.carta_versao <> new.carta_versao
     or v_otim.carta_versao <> v_bonus.carta_versao then
    raise exception 'linha recusada: versoes da carta divergem';
  end if;

  if v_otim.carta_fingerprint <> new.carta_fingerprint
     or v_bonus.carta_fingerprint <> new.carta_fingerprint
     or v_otim.carta_fingerprint <> v_bonus.carta_fingerprint then
    raise exception 'linha recusada: fingerprints da carta divergem';
  end if;

  if cardinality(new.pendencias) <> 0 then
    raise exception 'linha recusada: ainda existem pendencias';
  end if;

  return new;
end $$;

create trigger build_linha_publicavel_gate_v3
before insert or update on clube_novo.build_linha_card
for each row execute function clube_novo.validar_build_linha_publicavel_v3();

alter table clube_novo.build_otimizador enable row level security;
alter table clube_novo.build_bonificador enable row level security;
alter table clube_novo.build_linha_card enable row level security;

revoke all on table
  clube_novo.build_otimizador,
  clube_novo.build_bonificador,
  clube_novo.build_linha_card
from anon, authenticated;
revoke all on function clube_novo.validar_build_linha_publicavel_v3()
from public, anon, authenticated;
grant execute on function clube_novo.validar_build_linha_publicavel_v3()
to service_role;

commit;
