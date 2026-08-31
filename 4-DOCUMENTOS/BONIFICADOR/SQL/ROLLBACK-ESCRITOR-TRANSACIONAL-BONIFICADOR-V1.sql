-- Remove somente a porta V1. Resultados que ja tenham sido gravados por ela
-- nao sao apagados: sao fatos auditaveis e podem estar ligados a uma Build.

begin;

do $preflight$
declare
  v_def text;
begin
  if to_regprocedure('public.gravar_build_bonificador_v1(jsonb)') is null then
    raise exception 'rollback recusado: gravar_build_bonificador_v1(jsonb) nao existe';
  end if;
  select pg_get_functiondef('public.gravar_build_bonificador_v1(jsonb)'::regprocedure)
    into v_def;
  if v_def not ilike '%bonificador-writer-v1%'
     or v_def not ilike '%SECURITY DEFINER%' then
    raise exception 'rollback recusado: a funcao existente nao corresponde ao pacote V1';
  end if;
end
$preflight$;

revoke all on function public.gravar_build_bonificador_v1(jsonb)
  from public, anon, authenticated, service_role;
drop function public.gravar_build_bonificador_v1(jsonb);
revoke all on function public.bonificador_contexto_escrita_v2(integer,integer)
  from public, anon, authenticated, service_role;
drop function public.bonificador_contexto_escrita_v2(integer,integer);

do $readback$
begin
  if to_regprocedure('public.gravar_build_bonificador_v1(jsonb)') is not null then
    raise exception 'rollback falhou: a funcao ainda existe';
  end if;
  if to_regprocedure('public.bonificador_contexto_escrita_v2(integer,integer)') is not null then
    raise exception 'rollback falhou: o contexto ainda existe';
  end if;
  if to_regprocedure('public.gravar_bonus(jsonb)') is null then
    raise exception 'rollback falhou: o bloqueador legado nao foi preservado';
  end if;
end
$readback$;

commit;
