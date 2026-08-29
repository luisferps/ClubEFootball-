begin;

drop trigger if exists build_publicacao_gate_v1 on clube_novo.build_publicacao;
drop function if exists clube_novo.validar_publicacao_build_v1();

alter table clube_novo.build_resultado_otimizador
  drop constraint build_resultado_otimizador_build_carta_id_fkey;
alter table clube_novo.build_resultado_otimizador
  rename column build_carta_id to build_id;
alter table clube_novo.build_resultado_bonificador
  drop constraint build_resultado_bonificador_build_carta_id_fkey;
alter table clube_novo.build_resultado_bonificador
  rename column build_carta_id to build_id;
alter table clube_novo.build_publicacao
  drop constraint build_publicacao_build_carta_id_fkey;
alter table clube_novo.build_publicacao
  rename column build_carta_id to build_id;
alter table clube_novo.build_carta_atributo_snapshot
  drop constraint build_carta_atributo_snapshot_build_carta_id_fkey;
alter table clube_novo.build_carta_atributo_snapshot
  rename column build_carta_id to build_id;
alter table clube_novo.build_carta_atributo_snapshot rename to build_atributo_snapshot;

alter table clube_novo.build
  add column card_id text not null references clube_novo.carta_jogo(card_id),
  add column carta_versao text not null,
  add column carta_fingerprint text not null,
  add column rank_vencedor integer not null default 1 check (rank_vencedor = 1),
  add column criterio_desempate jsonb not null default '{}'::jsonb,
  add column combinacoes_avaliadas bigint check (combinacoes_avaliadas is null or combinacoes_avaliadas >= 0),
  add column combinacoes_podadas bigint check (combinacoes_podadas is null or combinacoes_podadas >= 0),
  add column tela_fingerprint text;

create unique index build_uma_campea_ativa_por_carta_uidx
  on clube_novo.build(card_id) where estado = 'ativa';
create index build_card_id_idx on clube_novo.build(card_id);

alter table clube_novo.build_resultado_otimizador
  add constraint build_resultado_otimizador_build_id_fkey
  foreign key (build_id) references clube_novo.build(id) on delete cascade;
alter table clube_novo.build_resultado_bonificador
  add constraint build_resultado_bonificador_build_id_fkey
  foreign key (build_id) references clube_novo.build(id) on delete cascade;
alter table clube_novo.build_publicacao
  add constraint build_publicacao_build_id_fkey
  foreign key (build_id) references clube_novo.build(id) on delete cascade;
alter table clube_novo.build_atributo_snapshot
  add constraint build_atributo_snapshot_build_id_fkey
  foreign key (build_id) references clube_novo.build(id) on delete cascade;

drop table clube_novo.build_carta;

create function clube_novo.validar_publicacao_build_v2()
returns trigger language plpgsql security invoker set search_path = '' as $$
declare
  v_carta_fp text;
  v_otim clube_novo.build_resultado_otimizador%rowtype;
  v_bonus clube_novo.build_resultado_bonificador%rowtype;
begin
  if new.estado <> 'publicada' then return new; end if;
  select carta_fingerprint into v_carta_fp
    from clube_novo.build where id = new.build_id;
  select * into v_otim from clube_novo.build_resultado_otimizador
    where build_id = new.build_id;
  select * into v_bonus from clube_novo.build_resultado_bonificador
    where build_id = new.build_id;
  if v_otim.build_id is null or v_otim.estado <> 'pronto' then
    raise exception 'publicacao recusada: resultado do Otimizador nao esta pronto';
  end if;
  if v_bonus.build_id is null or v_bonus.estado not in ('pronto','nao_aplicavel') then
    raise exception 'publicacao recusada: resultado do Bonificador nao esta pronto/nao aplicavel';
  end if;
  if v_otim.carta_fingerprint <> v_carta_fp or v_bonus.carta_fingerprint <> v_carta_fp then
    raise exception 'publicacao recusada: versoes/fingerprints da carta divergem';
  end if;
  return new;
end $$;

create trigger build_publicacao_gate_v2
before insert or update on clube_novo.build_publicacao
for each row execute function clube_novo.validar_publicacao_build_v2();

revoke all on function clube_novo.validar_publicacao_build_v2() from public, anon, authenticated;
grant execute on function clube_novo.validar_publicacao_build_v2() to service_role;

commit;
