begin;

drop trigger if exists build_publicacao_gate_v2 on clube_novo.build_publicacao;
drop function if exists clube_novo.validar_publicacao_build_v2();
drop index if exists clube_novo.build_uma_campea_ativa_por_carta_uidx;
drop index if exists clube_novo.build_card_id_idx;

create table clube_novo.build_carta (
  id bigint generated always as identity primary key,
  build_id bigint not null references clube_novo.build(id),
  card_id text not null references clube_novo.carta_jogo(card_id),
  carta_versao text not null,
  carta_fingerprint text not null,
  estado text not null default 'pendente' check (estado in ('pendente','pronto','nao_aplicavel','invalido')),
  pontuacao_vencedora numeric,
  rank_vencedor integer check (rank_vencedor is null or rank_vencedor = 1),
  criterio_desempate jsonb not null default '{}'::jsonb,
  combinacoes_avaliadas bigint check (combinacoes_avaliadas is null or combinacoes_avaliadas >= 0),
  combinacoes_podadas bigint check (combinacoes_podadas is null or combinacoes_podadas >= 0),
  tela_fingerprint text,
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now(),
  unique (build_id,card_id,carta_fingerprint)
);
create index build_carta_card_id_idx on clube_novo.build_carta(card_id);
create index build_carta_estado_idx on clube_novo.build_carta(estado);
alter table clube_novo.build_carta enable row level security;
revoke all on table clube_novo.build_carta from anon, authenticated;

alter table clube_novo.build_resultado_otimizador
  drop constraint build_resultado_otimizador_build_id_fkey;
alter table clube_novo.build_resultado_otimizador
  rename column build_id to build_carta_id;
alter table clube_novo.build_resultado_otimizador
  add constraint build_resultado_otimizador_build_carta_id_fkey
  foreign key (build_carta_id) references clube_novo.build_carta(id) on delete cascade;

alter table clube_novo.build_resultado_bonificador
  drop constraint build_resultado_bonificador_build_id_fkey;
alter table clube_novo.build_resultado_bonificador
  rename column build_id to build_carta_id;
alter table clube_novo.build_resultado_bonificador
  add constraint build_resultado_bonificador_build_carta_id_fkey
  foreign key (build_carta_id) references clube_novo.build_carta(id) on delete cascade;

alter table clube_novo.build_publicacao
  drop constraint build_publicacao_build_id_fkey;
alter table clube_novo.build_publicacao
  rename column build_id to build_carta_id;
alter table clube_novo.build_publicacao
  add constraint build_publicacao_build_carta_id_fkey
  foreign key (build_carta_id) references clube_novo.build_carta(id) on delete cascade;

alter table clube_novo.build_atributo_snapshot
  drop constraint build_atributo_snapshot_build_id_fkey;
alter table clube_novo.build_atributo_snapshot
  rename column build_id to build_carta_id;
alter table clube_novo.build_atributo_snapshot rename to build_carta_atributo_snapshot;
alter table clube_novo.build_carta_atributo_snapshot
  add constraint build_carta_atributo_snapshot_build_carta_id_fkey
  foreign key (build_carta_id) references clube_novo.build_carta(id) on delete cascade;

alter table clube_novo.build
  drop column tela_fingerprint,
  drop column combinacoes_podadas,
  drop column combinacoes_avaliadas,
  drop column criterio_desempate,
  drop column rank_vencedor,
  drop column carta_fingerprint,
  drop column carta_versao,
  drop column card_id;

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
    raise exception 'publicacao recusada: resultado do Bonificador nao esta pronto/nao aplicavel';
  end if;
  if v_otim.carta_fingerprint <> v_carta_fp or v_bonus.carta_fingerprint <> v_carta_fp then
    raise exception 'publicacao recusada: versoes/fingerprints da carta divergem';
  end if;
  return new;
end $$;

create trigger build_publicacao_gate_v1
before insert or update on clube_novo.build_publicacao
for each row execute function clube_novo.validar_publicacao_build_v1();

revoke all on function clube_novo.validar_publicacao_build_v1() from public, anon, authenticated;
grant execute on function clube_novo.validar_publicacao_build_v1() to service_role;

commit;
