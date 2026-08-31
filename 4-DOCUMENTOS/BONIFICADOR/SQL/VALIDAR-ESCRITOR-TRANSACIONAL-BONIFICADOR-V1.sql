begin transaction read only;

-- 1. Porta instalada, invoker, search_path fechado e somente service_role.
select
  p.oid::regprocedure::text as funcao,
  pg_get_userbyid(p.proowner) as owner_deve_ser_postgres,
  p.prosecdef as security_definer_deve_ser_true,
  p.provolatile as volatilidade_deve_ser_v,
  p.proconfig,
  has_function_privilege('service_role',p.oid,'EXECUTE') as service_role_executa,
  exists (
    select 1
    from aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
    where a.grantee=0 and a.privilege_type='EXECUTE'
  ) as public_executa_deve_ser_false,
  has_function_privilege('anon',p.oid,'EXECUTE') as anon_nao_executa,
  has_function_privilege('authenticated',p.oid,'EXECUTE') as authenticated_nao_executa,
  md5(pg_get_functiondef(p.oid)) as definicao_md5
from pg_proc p
join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public'
  and p.proname in ('gravar_build_bonificador_v1','bonificador_contexto_escrita_v2')
order by p.proname;

do $validar$
declare
  v_def text;
begin
  if to_regprocedure('public.gravar_build_bonificador_v1(jsonb)') is null then
    raise exception 'validacao: writer V1 ausente';
  end if;
  select pg_get_functiondef('public.gravar_build_bonificador_v1(jsonb)'::regprocedure)
    into v_def;
  if v_def not ilike '%SECURITY DEFINER%'
     or v_def not ilike '%SET search_path TO%'
     or v_def ilike '%clube.build%'
     or v_def ilike '%clube.fila%'
     or v_def not ilike '%for update%'
     or v_def not ilike '%for share%' then
    raise exception 'validacao: isolamento, lock ou seguranca divergentes';
  end if;
  if (select pg_get_userbyid(p.proowner)
      from pg_proc p
      where p.oid='public.gravar_build_bonificador_v1(jsonb)'::regprocedure)
     <> 'postgres' then
    raise exception 'validacao: owner do writer nao e postgres';
  end if;
  if to_regprocedure('public.bonificador_contexto_escrita_v2(integer,integer)') is null
     or (select pg_get_userbyid(p.proowner)
         from pg_proc p
         where p.oid='public.bonificador_contexto_escrita_v2(integer,integer)'::regprocedure)
        <> 'postgres' then
    raise exception 'validacao: contexto privado ausente ou com owner incorreto';
  end if;
  if not has_function_privilege('service_role',
       'public.gravar_build_bonificador_v1(jsonb)','EXECUTE')
     or has_function_privilege('anon',
       'public.gravar_build_bonificador_v1(jsonb)','EXECUTE')
     or has_function_privilege('authenticated',
       'public.gravar_build_bonificador_v1(jsonb)','EXECUTE') then
    raise exception 'validacao: grants divergentes';
  end if;
  if not has_function_privilege('service_role',
       'public.bonificador_contexto_escrita_v2(integer,integer)','EXECUTE')
     or has_function_privilege('anon',
       'public.bonificador_contexto_escrita_v2(integer,integer)','EXECUTE')
     or has_function_privilege('authenticated',
       'public.bonificador_contexto_escrita_v2(integer,integer)','EXECUTE') then
    raise exception 'validacao: grants do contexto divergentes';
  end if;
end
$validar$;

-- 2. Readback independente das ligacoes atuais. Deve retornar zero linhas.
select
  l.id as build_linha_card_id,
  l.card_id,
  b.id as build_bonificador_id,
  b.resultado_fingerprint,
  case
    when c.versao_id is null then 'sem_completude_vigente_apta'
    when l.carta_versao is distinct from c.regra_versao
      or l.carta_fingerprint is distinct from c.completude_fingerprint_sha256
      then 'linha_obsoleta'
    when b.carta_versao is distinct from c.regra_versao
      or b.carta_fingerprint is distinct from c.completude_fingerprint_sha256
      then 'resultado_obsoleto'
    when l.snapshot_bonificador_fingerprint is distinct from b.resultado_fingerprint
      then 'ligacao_sem_readback'
  end as problema
from clube_novo.build_linha_card l
join clube_novo.build_bonificador b on b.id=l.build_bonificador_id
left join clube_novo.carta_completude_motor_versao c
  on c.card_id=l.card_id and c.vigente and c.apto_motor
where c.versao_id is null
   or l.carta_versao is distinct from c.regra_versao
   or l.carta_fingerprint is distinct from c.completude_fingerprint_sha256
   or b.carta_versao is distinct from c.regra_versao
   or b.carta_fingerprint is distinct from c.completude_fingerprint_sha256
   or l.snapshot_bonificador_fingerprint is distinct from b.resultado_fingerprint
order by l.id;

-- 3. Detalhe fisico precisa reconstruir exatamente o total. Zero linhas.
select
  b.id as build_bonificador_id,
  b.resultado_fingerprint,
  d.itens,
  d.numericos,
  d.soma_detalhe,
  b.bonus_fisico_total
from clube_novo.build_bonificador b
cross join lateral (
  select
    count(*) as itens,
    count(*) filter (where jsonb_typeof(x.value)='number') as numericos,
    (select sum((n.value #>> '{}')::numeric)
     from jsonb_each(b.bonus_fisico_detalhe) n
     where jsonb_typeof(n.value)='number') as soma_detalhe
  from jsonb_each(b.bonus_fisico_detalhe) x
) d
where d.itens=0
   or d.numericos<>d.itens
   or d.soma_detalhe is distinct from b.bonus_fisico_total
order by b.id;

-- 4. Para conferir uma gravacao em outra conexao, substitua o valor abaixo
-- pelo resultado_fingerprint devolvido pelo writer. Uma linha deve voltar.
select
  b.id as build_bonificador_id,
  l.id as build_linha_card_id,
  l.card_id,l.funcao_id,l.posicao_id,
  b.carta_versao,b.carta_fingerprint,
  b.resultado_fingerprint,
  l.snapshot_bonificador_fingerprint,
  b.motor_versao,b.contrato_versao,b.concluido_em
from clube_novo.build_bonificador b
join clube_novo.build_linha_card l on l.build_bonificador_id=b.id
where b.resultado_fingerprint='<COLE_O_RESULTADO_FINGERPRINT_AQUI>';

rollback;
