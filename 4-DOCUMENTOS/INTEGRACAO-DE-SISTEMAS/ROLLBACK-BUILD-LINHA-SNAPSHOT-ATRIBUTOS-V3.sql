begin;

create or replace function clube_novo.validar_build_linha_publicavel_v3()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_otim clube_novo.build_otimizador%rowtype;
  v_bonus clube_novo.build_bonificador%rowtype;
begin
  if new.estado not in ('pronta','publicada') then return new; end if;
  if new.build_otimizador_id is null or new.build_bonificador_id is null then
    raise exception 'linha recusada: resultados do Otimizador e do Bonificador sao obrigatorios';
  end if;
  select * into v_otim from clube_novo.build_otimizador where id = new.build_otimizador_id;
  select * into v_bonus from clube_novo.build_bonificador where id = new.build_bonificador_id;
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

alter table clube_novo.build_linha_card
  drop constraint if exists build_linha_card_atributos_snapshot_check,
  drop column if exists snapshot_bonificador_fingerprint,
  drop column if exists snapshot_otimizador_fingerprint,
  drop column if exists atributos_snapshot_fingerprint,
  drop column if exists atributos_snapshot;

commit;
