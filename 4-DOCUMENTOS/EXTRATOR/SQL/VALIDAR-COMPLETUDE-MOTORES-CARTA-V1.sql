-- Validação independente, somente leitura, para habilitar os motores.
-- Pode ser executada depois da migração e do seed físico inicial.
-- Não altera cartas, publicação, filas nem resultados.

begin transaction isolation level repeatable read read only;

select
  (select count(*) from clube_novo.carta_jogo) cartas_no_banco,
  (select count(*) from clube_novo.carta_completude_motor_versao where vigente) cartas_com_estado_vigente,
  (select count(*) from clube_novo.carta_completude_motor_versao where vigente and apto_motor) aptas_aos_motores,
  (select count(*) from clube_novo.carta_completude_motor_versao where vigente and not apto_motor) bloqueadas_nos_motores,
  (select count(*) from clube_novo.carta_completude_motor_versao where vigente and estado_coleta='incompleta') coleta_incompleta;

select c.estado_coleta,c.estado_resolucao,c.apto_motor,count(*) componentes
from clube_novo.carta_completude_motor_componente c
join clube_novo.carta_completude_motor_versao v using(versao_id)
where v.vigente
group by c.estado_coleta,c.estado_resolucao,c.apto_motor
order by c.estado_coleta,c.estado_resolucao,c.apto_motor;

select count(*) componentes_orfaos_catalogo_atual,
       count(distinct v.card_id) cartas_orfas_catalogo_atual
from clube_novo.carta_completude_motor_componente c
join clube_novo.carta_completude_motor_versao v using(versao_id)
where v.vigente and c.estado_resolucao='orfao_catalogo_atual';

select acao,motivo,count(*) cartas
from clube_novo.planejar_completude_motor_v1(
  array(select card_id from clube_novo.carta_jogo order by card_id)
)
group by acao,motivo
order by acao,motivo;

do $validacao$
declare
  v_n bigint;
  v_role record;
  v_can boolean;
begin
  if to_regclass('clube_novo.carta_completude_motor_versao') is null
     or to_regclass('clube_novo.carta_completude_motor_componente') is null
     or to_regclass('clube_novo.carta_completude_motor_decisao') is null
     or to_regclass('clube_novo.migracao_gravar_bonus_grant_snapshot_v1') is null
     or to_regclass('clube_novo.carta_completude_motor_atual') is null
     or to_regprocedure('clube_novo.registrar_completude_motor_v1(text,bigint,jsonb)') is null
     or to_regprocedure('clube_novo.planejar_completude_motor_v1(text[])') is null then
    raise exception 'validação: objetos V1 incompletos';
  end if;

  if to_regprocedure('public.gravar_bonus(jsonb)') is null
     or to_regprocedure('public.gravar_bonus_sem_completude_v1(jsonb)') is null
     or pg_get_functiondef('public.gravar_bonus(jsonb)'::regprocedure)
        not like '%gravar_bonus bloqueada:%nenhuma linha foi gravada%'
     or pg_get_functiondef('public.gravar_bonus(jsonb)'::regprocedure)
        like '%gravar_bonus_sem_completude_v1%' then
    raise exception 'NÃO HABILITAR BONIFICADOR: gravar_bonus não é um bloqueador explícito';
  end if;
  if has_function_privilege('service_role','public.gravar_bonus(jsonb)','EXECUTE')
     or has_function_privilege('service_role','public.gravar_bonus_sem_completude_v1(jsonb)','EXECUTE')
     or has_function_privilege('anon','public.gravar_bonus(jsonb)','EXECUTE')
     or has_function_privilege('authenticated','public.gravar_bonus(jsonb)','EXECUTE') then
    raise exception 'NÃO HABILITAR BONIFICADOR: role de runtime ainda executa gravar_bonus';
  end if;
  select count(*) into v_n
  from pg_proc p
  cross join lateral aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
  where p.oid in (
    'public.gravar_bonus(jsonb)'::regprocedure,
    'public.gravar_bonus_sem_completude_v1(jsonb)'::regprocedure
  ) and a.privilege_type='EXECUTE';
  if v_n<>0 then
    raise exception 'NÃO HABILITAR BONIFICADOR: ainda existem % grants EXECUTE declarados',v_n;
  end if;
  for v_role in
    select distinct grantee
    from clube_novo.migracao_gravar_bonus_grant_snapshot_v1
    where grantee<>'PUBLIC' and grantee<>
      (select proprietario from clube_novo.migracao_gravar_bonus_grant_snapshot_v1 limit 1)
  loop
    if exists(select 1 from pg_roles where rolname=v_role.grantee) then
      select has_function_privilege(v_role.grantee,'public.gravar_bonus(jsonb)','EXECUTE')
          or has_function_privilege(v_role.grantee,'public.gravar_bonus_sem_completude_v1(jsonb)','EXECUTE')
        into v_can;
      if v_can then
        raise exception 'NÃO HABILITAR BONIFICADOR: grant capturado de % ainda alcança bypass',v_role.grantee;
      end if;
    end if;
  end loop;

  select count(*) into v_n
  from clube_novo.carta_jogo j
  left join clube_novo.carta_completude_motor_versao v
    on v.card_id=j.card_id and v.vigente
  where v.versao_id is null;
  if v_n<>0 then
    raise exception 'NÃO HABILITAR MOTORES: % cartas ainda não têm estado de completude vigente',v_n;
  end if;

  select count(*) into v_n
  from clube_novo.carta_completude_motor_versao v
  left join lateral (
    select count(*) n
    from clube_novo.carta_completude_motor_componente c
    where c.versao_id=v.versao_id
  ) q on true
  where v.vigente and q.n<>11;
  if v_n<>0 then
    raise exception 'validação: % cartas vigentes não possuem os 11 componentes',v_n;
  end if;

  select count(*) into v_n
  from clube_novo.carta_completude_motor_versao v
  cross join lateral (
    select clube_novo.carta_input_motor_canonico_v1(v.card_id) j
  ) i
  where v.vigente and v.input_fingerprint_sha256 is distinct from
    encode(extensions.digest(i.j::text,'sha256'),'hex');
  if v_n<>0 then
    raise exception 'NÃO HABILITAR MOTORES: % fingerprints vigentes divergem do input atual',v_n;
  end if;

  select count(*) into v_n
  from clube_novo.carta_completude_motor_versao v
  where v.vigente and (
    (v.apto_motor and (
      v.estado_coleta<>'completa' or cardinality(v.missing_inputs)<>0
      or cardinality(v.motivos_bloqueio_motor)<>0
    ))
    or (not v.apto_motor and cardinality(v.motivos_bloqueio_motor)=0)
    or exists (
      select 1 from unnest(v.missing_inputs) m
      where m not like 'coleta:%'
    )
  );
  if v_n<>0 then
    raise exception 'validação: % estados misturam coleta, resolução ou bloqueio',v_n;
  end if;

  select count(*) into v_n
  from clube_novo.carta_completude_motor_componente c
  join clube_novo.carta_completude_motor_versao v using(versao_id)
  left join clube_novo.carta_completude_motor_decisao d
    on (d.versao_id,d.componente)=(c.versao_id,c.componente)
  where v.vigente and c.estado_resolucao='orfao_catalogo_atual' and (
    c.componente<>'dimensoes'
    or c.estado_coleta not in ('conferido_com_valor','conferido_sem_valor')
    or not c.apto_motor
    or jsonb_typeof(c.evidencia#>'{decisao_motor}') is distinct from 'object'
    or coalesce(c.evidencia#>'{decisao_motor}','{}'::jsonb)='{}'::jsonb
    or d.decisao_id is null
  );
  if v_n<>0 then
    raise exception 'validação: % órfãos de catálogo atual não preservam coleta/decisão não bloqueante',v_n;
  end if;

  select count(*) into v_n
  from clube_novo.carta_completude_motor_versao v
  cross join lateral (select public.otimizador_carta_v2(v.card_id) j) o
  cross join lateral (select public.bonificador_carta_v1(v.card_id) j) b
  where v.vigente and (
    (v.apto_motor and (
      not coalesce((o.j#>>'{gate,pode_rodar}')::boolean,false)
      or not coalesce((b.j->>'pode_rodar')::boolean,false)
    ))
    or (not v.apto_motor and (
      coalesce((o.j#>>'{gate,pode_rodar}')::boolean,false)
      or coalesce((b.j->>'pode_rodar')::boolean,false)
    ))
  );
  if v_n<>0 then
    raise exception 'NÃO HABILITAR MOTORES: % cartas divergem entre selo e gates de consumo',v_n;
  end if;

  select count(*) into v_n
  from clube_novo.build_linha_card l
  join clube_novo.carta_completude_motor_versao v
    on v.card_id=l.card_id and v.vigente
  where l.estado<>'invalida'
    and not (
      (l.carta_versao,l.carta_fingerprint)=
        (v.regra_versao,v.completude_fingerprint_sha256)
      or (
        l.estado in ('pronta','publicada')
        and l.carta_fingerprint=v.fingerprint_entrada_legado_sha256
      )
    );
  if v_n<>0 then
    raise exception 'NÃO HABILITAR MOTORES: % linhas ativas parecem calculadas com input obsoleto',v_n;
  end if;

  select count(*) into v_n
  from pg_trigger t
  join pg_class c on c.oid=t.tgrelid
  join pg_namespace n on n.oid=c.relnamespace
  where n.nspname='clube_novo' and c.relname='carta_jogo'
    and t.tgname='carta_jogo_invalidar_completude_motor_v1'
    and not t.tgisinternal and (t.tgtype & 2)=0;
  if v_n<>1 then
    raise exception 'validação: trigger de carta deve existir e ser AFTER (não bloqueia inserção/publicação)';
  end if;

  if not has_function_privilege(
       'service_role','clube_novo.registrar_completude_motor_v1(text,bigint,jsonb)','EXECUTE'
     )
     or has_function_privilege(
       'anon','clube_novo.registrar_completude_motor_v1(text,bigint,jsonb)','EXECUTE'
     )
     or has_function_privilege(
       'authenticated','clube_novo.registrar_completude_motor_v1(text,bigint,jsonb)','EXECUTE'
     ) then
    raise exception 'validação: privilégios do registrador incorretos';
  end if;
end
$validacao$;

rollback;
