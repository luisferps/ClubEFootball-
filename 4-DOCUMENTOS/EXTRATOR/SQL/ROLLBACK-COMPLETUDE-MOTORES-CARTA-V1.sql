-- Rollback seguro da completude dos motores V1.
--
-- Este rollback se recusa a apagar estado produzido depois da migração.
-- Se uma linha de build mudou ou nasceu após o snapshot, a reconciliação deve
-- ser decidida explicitamente; não há restauração silenciosa.

begin;

do $preflight$
declare
  v_n bigint;
begin
  if to_regclass('clube_novo.migracao_completude_motor_build_snapshot_v1') is null
     or to_regclass('clube_novo.migracao_gravar_bonus_grant_snapshot_v1') is null
     or to_regclass('clube_novo.carta_completude_motor_versao') is null
     or to_regclass('clube_novo.carta_completude_motor_componente') is null
     or to_regclass('clube_novo.carta_completude_motor_decisao') is null then
    raise exception 'rollback recusado: objetos V1/snapshot não foram encontrados';
  end if;

  if to_regprocedure('public.gravar_bonus(jsonb)') is null
     or to_regprocedure('public.gravar_bonus_sem_completude_v1(jsonb)') is null
     or pg_get_functiondef('public.gravar_bonus(jsonb)'::regprocedure)
        not like '%gravar_bonus bloqueada:%nenhuma linha foi gravada%' then
    raise exception 'rollback recusado: par bloqueador/preservado de gravar_bonus divergiu';
  end if;

  if to_regprocedure('public.otimizador_carta_sem_completude_v2(text)') is null
     or to_regprocedure('public.otimizador_proxima_fila_sem_completude_v1(integer)') is null
     or to_regprocedure('public.bonificador_carta_sem_completude_v1(text)') is null
     or to_regprocedure('public.bonificador_pares_sem_completude_v1(integer,integer)') is null then
    raise exception 'rollback recusado: contratos originais preservados estão ausentes';
  end if;

  select count(*) into v_n
  from (
    select id from clube_novo.build_linha_card
    except
    select id from clube_novo.migracao_completude_motor_build_snapshot_v1
  ) q;
  if v_n<>0 then
    raise exception 'rollback recusado: % linhas de build nasceram depois da migração',v_n;
  end if;

  select count(*) into v_n
  from (
    select id from clube_novo.migracao_completude_motor_build_snapshot_v1
    except
    select id from clube_novo.build_linha_card
  ) q;
  if v_n<>0 then
    raise exception 'rollback recusado: % linhas de build do snapshot deixaram de existir',v_n;
  end if;

  select count(*) into v_n
  from clube_novo.build_linha_card l
  join clube_novo.migracao_completude_motor_build_snapshot_v1 s using(id)
  where (l.estado,l.pendencias,l.estado_otimizador,l.erro_otimizador)
        is distinct from
        (s.estado,s.pendencias,s.estado_otimizador,s.erro_otimizador);
  if v_n<>0 then
    raise exception 'rollback recusado: % linhas de build mudaram; preservar e reconciliar manualmente',v_n;
  end if;
end
$preflight$;

-- Retira o bloqueador, devolve o nome à implementação original e restaura
-- exatamente os grantees + grant option capturados. Nenhum destino alternativo
-- é criado durante o rollback.
drop function public.gravar_bonus(jsonb);
alter function public.gravar_bonus_sem_completude_v1(jsonb)
  rename to gravar_bonus;

do $restaurar_grants_gravar_bonus$
declare
  v_role record;
  v_owner text;
begin
  select proprietario into v_owner
  from clube_novo.migracao_gravar_bonus_grant_snapshot_v1
  limit 1;
  if v_owner is null then
    raise exception 'rollback recusado: snapshot de grants gravar_bonus vazio';
  end if;

  for v_role in
    select distinct case when a.grantee=0 then 'PUBLIC'
                         else pg_get_userbyid(a.grantee) end grantee
    from pg_proc p
    cross join lateral aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
    where p.oid='public.gravar_bonus(jsonb)'::regprocedure
  loop
    execute format(
      'revoke all privileges on function public.gravar_bonus(jsonb) from %s',
      case when v_role.grantee='PUBLIC' then 'PUBLIC' else quote_ident(v_role.grantee) end
    );
  end loop;

  for v_role in
    select grantee,privilege_type,is_grantable
    from clube_novo.migracao_gravar_bonus_grant_snapshot_v1
    order by grantee,privilege_type
  loop
    execute format(
      'grant %s on function public.gravar_bonus(jsonb) to %s%s',
      v_role.privilege_type,
      case when v_role.grantee='PUBLIC' then 'PUBLIC' else quote_ident(v_role.grantee) end,
      case when v_role.is_grantable then ' with grant option' else '' end
    );
  end loop;

  if (select pg_get_userbyid(p.proowner)
      from pg_proc p where p.oid='public.gravar_bonus(jsonb)'::regprocedure)
     is distinct from v_owner then
    raise exception 'rollback readback: proprietário de gravar_bonus mudou';
  end if;
  if exists(
    select grantee,privilege_type,is_grantable
    from clube_novo.migracao_gravar_bonus_grant_snapshot_v1
    except
    select case when a.grantee=0 then 'PUBLIC' else pg_get_userbyid(a.grantee) end,
           a.privilege_type,a.is_grantable
    from pg_proc p
    cross join lateral aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
    where p.oid='public.gravar_bonus(jsonb)'::regprocedure
  ) or exists(
    select case when a.grantee=0 then 'PUBLIC' else pg_get_userbyid(a.grantee) end,
           a.privilege_type,a.is_grantable
    from pg_proc p
    cross join lateral aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
    where p.oid='public.gravar_bonus(jsonb)'::regprocedure
    except
    select grantee,privilege_type,is_grantable
    from clube_novo.migracao_gravar_bonus_grant_snapshot_v1
  ) then
    raise exception 'rollback readback: grants de gravar_bonus não voltaram exatamente';
  end if;
end
$restaurar_grants_gravar_bonus$;

drop trigger if exists build_linha_completude_motor_v1
  on clube_novo.build_linha_card;
drop trigger if exists carta_jogo_invalidar_completude_motor_v1
  on clube_novo.carta_jogo;
drop trigger if exists carta_atributo_invalidar_completude_motor_v1
  on clube_novo.carta_atributo_jogo;
drop trigger if exists carta_corpo_invalidar_completude_motor_v1
  on clube_novo.carta_corpo_jogo;
drop trigger if exists carta_habilidade_invalidar_completude_motor_v1
  on clube_novo.carta_habilidade_jogo;
drop trigger if exists carta_estilo_ia_invalidar_completude_motor_v1
  on clube_novo.carta_estilo_ia_jogo;
drop trigger if exists carta_posicao_invalidar_completude_motor_v1
  on clube_novo.carta_posicao_jogo;
drop trigger if exists carta_posicao_principal_invalidar_completude_motor_v1
  on clube_novo.carta_posicao_principal_jogo;
drop trigger if exists carta_pe_invalidar_completude_motor_v1
  on clube_novo.carta_pe_jogo;
drop trigger if exists carta_playstyle_invalidar_completude_motor_v1
  on clube_novo.carta_playstyle_jogo;
drop trigger if exists carta_impeto_invalidar_completude_motor_v1
  on clube_novo.carta_impeto_jogo;

drop function clube_novo.validar_build_linha_completude_motor_v1();
drop function clube_novo.invalidar_completude_motor_por_insumo_v1();

drop function public.otimizador_carta_v2(text);
drop function public.otimizador_proxima_fila_v1(integer);
drop function public.bonificador_carta_v1(text);
drop function public.bonificador_pares_v1(integer,integer);

alter function public.otimizador_carta_sem_completude_v2(text)
  rename to otimizador_carta_v2;
alter function public.otimizador_proxima_fila_sem_completude_v1(integer)
  rename to otimizador_proxima_fila_v1;
alter function public.bonificador_carta_sem_completude_v1(text)
  rename to bonificador_carta_v1;
alter function public.bonificador_pares_sem_completude_v1(integer,integer)
  rename to bonificador_pares_v1;

grant execute on function public.otimizador_carta_v2(text) to service_role;
grant execute on function public.otimizador_proxima_fila_v1(integer) to service_role;
grant execute on function public.bonificador_carta_v1(text) to service_role;
grant execute on function public.bonificador_pares_v1(integer,integer) to service_role;

drop function clube_novo.planejar_completude_motor_v1(text[]);
drop function clube_novo.registrar_completude_motor_v1(text,bigint,jsonb);
drop function clube_novo.carta_input_motor_canonico_v1(text);
drop view clube_novo.carta_completude_motor_atual;
drop table clube_novo.carta_completude_motor_decisao;
drop table clube_novo.carta_completude_motor_componente;
drop table clube_novo.carta_completude_motor_versao;
drop table clube_novo.migracao_completude_motor_build_snapshot_v1;
drop table clube_novo.migracao_gravar_bonus_grant_snapshot_v1;

do $readback$
begin
  if to_regprocedure('public.otimizador_carta_v2(text)') is null
     or to_regprocedure('public.otimizador_proxima_fila_v1(integer)') is null
     or to_regprocedure('public.bonificador_carta_v1(text)') is null
     or to_regprocedure('public.bonificador_pares_v1(integer,integer)') is null
     or to_regprocedure('public.gravar_bonus(jsonb)') is null then
    raise exception 'rollback readback: contratos originais não voltaram';
  end if;
  if to_regprocedure('public.otimizador_carta_sem_completude_v2(text)') is not null
     or to_regprocedure('public.gravar_bonus_sem_completude_v1(jsonb)') is not null
     or to_regclass('clube_novo.carta_completude_motor_versao') is not null
     or to_regclass('clube_novo.migracao_completude_motor_build_snapshot_v1') is not null
     or to_regclass('clube_novo.migracao_gravar_bonus_grant_snapshot_v1') is not null then
    raise exception 'rollback readback: sobrou objeto da completude V1';
  end if;
end
$readback$;

commit;
