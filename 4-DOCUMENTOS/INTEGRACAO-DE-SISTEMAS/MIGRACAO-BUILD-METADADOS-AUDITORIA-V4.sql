begin;

alter table clube_novo.build_otimizador
  add column criado_em timestamptz not null default now(),
  add column motor_versao text not null;

alter table clube_novo.build_bonificador
  add column criado_em timestamptz not null default now(),
  add column motor_versao text not null;

alter table clube_novo.build_linha_card
  add column otimizador_motor_versao text,
  add column otimizador_contrato_versao text,
  add column bonificador_motor_versao text,
  add column bonificador_contrato_versao text,
  add column montada_em timestamptz;

create function clube_novo.proteger_build_resultado_imutavel_v4()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  raise exception 'resultado de motor imutavel: crie uma nova execucao';
end $$;

create trigger build_otimizador_imutavel_v4
before update on clube_novo.build_otimizador
for each row execute function clube_novo.proteger_build_resultado_imutavel_v4();

create trigger build_bonificador_imutavel_v4
before update on clube_novo.build_bonificador
for each row execute function clube_novo.proteger_build_resultado_imutavel_v4();

create function clube_novo.controlar_build_linha_auditoria_v4()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if new.criado_em is distinct from old.criado_em then
    raise exception 'linha recusada: criado_em e imutavel';
  end if;

  if old.estado in ('pronta','publicada','invalida') and (
       new.card_id is distinct from old.card_id
       or new.funcao_id is distinct from old.funcao_id
       or new.posicao_id is distinct from old.posicao_id
       or new.build_otimizador_id is distinct from old.build_otimizador_id
       or new.build_bonificador_id is distinct from old.build_bonificador_id
       or new.carta_versao is distinct from old.carta_versao
       or new.carta_fingerprint is distinct from old.carta_fingerprint
       or new.otimizador_motor_versao is distinct from old.otimizador_motor_versao
       or new.otimizador_contrato_versao is distinct from old.otimizador_contrato_versao
       or new.bonificador_motor_versao is distinct from old.bonificador_motor_versao
       or new.bonificador_contrato_versao is distinct from old.bonificador_contrato_versao
       or new.atributos_snapshot is distinct from old.atributos_snapshot
       or new.atributos_snapshot_fingerprint is distinct from old.atributos_snapshot_fingerprint
       or new.snapshot_otimizador_fingerprint is distinct from old.snapshot_otimizador_fingerprint
       or new.snapshot_bonificador_fingerprint is distinct from old.snapshot_bonificador_fingerprint
  ) then
    raise exception 'linha recusada: identidade e selos da linha montada sao imutaveis';
  end if;

  if old.montada_em is not null and new.montada_em is distinct from old.montada_em then
    raise exception 'linha recusada: montada_em e imutavel';
  end if;

  if old.montada_em is null and new.estado in ('pronta','publicada') then
    new.montada_em := now();
  end if;
  new.atualizado_em := now();
  return new;
end $$;

create trigger build_linha_auditoria_v4
before update on clube_novo.build_linha_card
for each row execute function clube_novo.controlar_build_linha_auditoria_v4();

create or replace function clube_novo.validar_build_linha_publicavel_v3()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_otim clube_novo.build_otimizador%rowtype;
  v_bonus clube_novo.build_bonificador%rowtype;
  v_item record;
begin
  if new.estado not in ('pronta','publicada') then return new; end if;
  if new.build_otimizador_id is null or new.build_bonificador_id is null then
    raise exception 'linha recusada: resultados do Otimizador e do Bonificador sao obrigatorios';
  end if;
  select * into v_otim from clube_novo.build_otimizador where id=new.build_otimizador_id;
  select * into v_bonus from clube_novo.build_bonificador where id=new.build_bonificador_id;
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
  if new.otimizador_motor_versao is distinct from v_otim.motor_versao
     or new.otimizador_contrato_versao is distinct from v_otim.contrato_versao
     or new.bonificador_motor_versao is distinct from v_bonus.motor_versao
     or new.bonificador_contrato_versao is distinct from v_bonus.contrato_versao then
    raise exception 'linha recusada: versoes dos resultados ligados divergem';
  end if;
  if cardinality(new.pendencias) <> 0 then
    raise exception 'linha recusada: ainda existem pendencias';
  end if;
  if new.atributos_snapshot is null
     or jsonb_typeof(new.atributos_snapshot) <> 'object'
     or new.atributos_snapshot = '{}'::jsonb
     or new.atributos_snapshot_fingerprint is null then
    raise exception 'linha recusada: snapshot de atributos ausente ou vazio';
  end if;
  if new.snapshot_otimizador_fingerprint is distinct from v_otim.resultado_fingerprint
     or new.snapshot_bonificador_fingerprint is distinct from v_bonus.resultado_fingerprint then
    raise exception 'linha recusada: snapshot nao esta selado pelos dois resultados';
  end if;
  for v_item in select key,value from jsonb_each(new.atributos_snapshot)
  loop
    if not exists(select 1 from clube_novo.atributo_jogo a where a.codigo=v_item.key) then
      raise exception 'linha recusada: atributo canonico inexistente: %',v_item.key;
    end if;
    if jsonb_typeof(v_item.value) <> 'object'
       or not (v_item.value ? 'valor_inicial')
       or not (v_item.value ? 'etapas')
       or not (v_item.value ? 'valor_final')
       or jsonb_typeof(v_item.value->'valor_inicial') <> 'number'
       or jsonb_typeof(v_item.value->'etapas') <> 'array'
       or jsonb_typeof(v_item.value->'valor_final') <> 'number' then
      raise exception 'linha recusada: estrutura invalida do atributo %',v_item.key;
    end if;
  end loop;
  if new.montada_em is null then new.montada_em:=now(); end if;
  return new;
end $$;

revoke all on function clube_novo.proteger_build_resultado_imutavel_v4()
from public,anon,authenticated;
revoke all on function clube_novo.controlar_build_linha_auditoria_v4()
from public,anon,authenticated;
grant execute on function clube_novo.proteger_build_resultado_imutavel_v4() to service_role;
grant execute on function clube_novo.controlar_build_linha_auditoria_v4() to service_role;

commit;
