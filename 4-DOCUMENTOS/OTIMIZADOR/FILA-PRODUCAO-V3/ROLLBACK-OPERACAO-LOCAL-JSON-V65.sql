begin;

revoke all on function public.otimizador_producao_importar_json_local_v1(uuid,bigint,jsonb,timestamptz)
  from public, anon, authenticated, service_role;
drop function if exists public.otimizador_producao_importar_json_local_v1(uuid,bigint,jsonb,timestamptz);

notify pgrst, 'reload schema';

commit;
