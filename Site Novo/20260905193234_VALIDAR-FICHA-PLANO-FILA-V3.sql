-- Validacao da Ficha V3. Somente leitura.

select jsonb_build_object(
  'base',(
    select jsonb_build_object(
      'md5',md5(pg_get_functiondef(p.oid)),
      'stable',p.provolatile='s',
      'security_definer',p.prosecdef,
      'search_path',p.proconfig,
      'usa_helper',strpos(
        pg_get_functiondef(p.oid),
        'clube_novo.site_novo_fila_atributos_confirmada_v1(e.card_id)'
      )>0,
      'anon_executa',has_function_privilege('anon',p.oid,'EXECUTE'),
      'authenticated_executa',has_function_privilege('authenticated',p.oid,'EXECUTE'),
      'service_role_executa',has_function_privilege('service_role',p.oid,'EXECUTE')
    )
    from pg_proc p
    where p.oid='public.site_novo_ficha_base_publicada_v1(text,bigint)'::regprocedure::oid
  ),
  'helper',(
    select jsonb_build_object(
      'assinatura',p.oid::regprocedure::text,
      'stable',p.provolatile='s',
      'security_invoker',not p.prosecdef,
      'search_path',p.proconfig,
      'anon_executa',has_function_privilege('anon',p.oid,'EXECUTE'),
      'authenticated_executa',has_function_privilege('authenticated',p.oid,'EXECUTE'),
      'service_role_executa',has_function_privilege('service_role',p.oid,'EXECUTE')
    )
    from pg_proc p
    where p.oid='clube_novo.site_novo_fila_atributos_confirmada_v1(text)'::regprocedure::oid
  ),
  'mckennie_default',public.site_novo_ficha_v1('55068997045101',null),
  'mckennie_8477',public.site_novo_ficha_v1('55068997045101',8477),
  'mckennie_8475',public.site_novo_ficha_v1('55068997045101',8475)
) as validacao;

explain (analyze,buffers,format json)
select public.site_novo_ficha_v1('55068997045101',8477);

