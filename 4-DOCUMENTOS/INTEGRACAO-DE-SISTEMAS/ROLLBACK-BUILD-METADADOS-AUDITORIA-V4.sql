begin;

drop trigger if exists build_linha_publicavel_gate_v3 on clube_novo.build_linha_card;
drop function if exists clube_novo.validar_build_linha_publicavel_v3();
drop trigger if exists build_linha_auditoria_v4 on clube_novo.build_linha_card;
drop trigger if exists build_bonificador_imutavel_v4 on clube_novo.build_bonificador;
drop trigger if exists build_otimizador_imutavel_v4 on clube_novo.build_otimizador;
drop function if exists clube_novo.controlar_build_linha_auditoria_v4();
drop function if exists clube_novo.proteger_build_resultado_imutavel_v4();

alter table clube_novo.build_linha_card
  drop column if exists montada_em,
  drop column if exists bonificador_contrato_versao,
  drop column if exists bonificador_motor_versao,
  drop column if exists otimizador_contrato_versao,
  drop column if exists otimizador_motor_versao;

alter table clube_novo.build_bonificador
  drop column if exists motor_versao,
  drop column if exists criado_em;

alter table clube_novo.build_otimizador
  drop column if exists motor_versao,
  drop column if exists criado_em;

create function clube_novo.validar_build_linha_publicavel_v3()
returns trigger language plpgsql security invoker set search_path='' as $$
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
  if cardinality(new.pendencias) <> 0 then
    raise exception 'linha recusada: ainda existem pendencias';
  end if;
  if new.atributos_snapshot is null or new.atributos_snapshot='{}'::jsonb
     or new.atributos_snapshot_fingerprint is null then
    raise exception 'linha recusada: snapshot de atributos ausente ou vazio';
  end if;
  if new.snapshot_otimizador_fingerprint is distinct from v_otim.resultado_fingerprint
     or new.snapshot_bonificador_fingerprint is distinct from v_bonus.resultado_fingerprint then
    raise exception 'linha recusada: snapshot nao esta selado pelos dois resultados';
  end if;
  for v_item in select key,value from jsonb_each(new.atributos_snapshot)
  loop
    if not exists(select 1 from clube_novo.atributo_jogo a where a.codigo=v_item.key)
       or jsonb_typeof(v_item.value)<>'object'
       or not(v_item.value?'valor_inicial') or not(v_item.value?'etapas')
       or not(v_item.value?'valor_final')
       or jsonb_typeof(v_item.value->'valor_inicial')<>'number'
       or jsonb_typeof(v_item.value->'etapas')<>'array'
       or jsonb_typeof(v_item.value->'valor_final')<>'number' then
      raise exception 'linha recusada: atributo ou estrutura invalida: %',v_item.key;
    end if;
  end loop;
  return new;
end $$;

create trigger build_linha_publicavel_gate_v3
before insert or update on clube_novo.build_linha_card
for each row execute function clube_novo.validar_build_linha_publicavel_v3();

revoke all on function clube_novo.validar_build_linha_publicavel_v3()
from public,anon,authenticated;
grant execute on function clube_novo.validar_build_linha_publicavel_v3() to service_role;

commit;
