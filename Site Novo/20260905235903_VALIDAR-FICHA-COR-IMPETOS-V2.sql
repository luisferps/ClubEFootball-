-- Validacao somente leitura da preparacao de cores dos Impetos.

select jsonb_build_object(
  'tabela', jsonb_build_object(
    'existe', to_regclass('clube_novo.tipo_impeto_cor_visual_jogo') is not null,
    'linhas', (select count(*) from clube_novo.tipo_impeto_cor_visual_jogo),
    'confirmadas', (
      select count(*)
      from clube_novo.tipo_impeto_cor_visual_jogo
      where estado_validacao = 'confirmada'
    )
  ),
  'funcao', (
    select jsonb_build_object(
      'assinatura', p.oid::regprocedure::text,
      'stable', p.provolatile = 's',
      'security_definer', p.prosecdef,
      'search_path', p.proconfig,
      'anon_executa', has_function_privilege('anon',p.oid,'EXECUTE'),
      'authenticated_executa', has_function_privilege('authenticated',p.oid,'EXECUTE'),
      'service_role_executa', has_function_privilege('service_role',p.oid,'EXECUTE')
    )
    from pg_proc p
    where p.oid = 'public.site_novo_ficha_v2(text,bigint)'::regprocedure::oid
  ),
  'amostra', (
    select jsonb_build_object(
      'contrato', resposta ->> 'contrato',
      'versao', resposta -> 'versao',
      'status', resposta ->> 'status'
    )
    from (
      select public.site_novo_ficha_v2('55068997045101',8475) as resposta
    ) x
  )
) as validacao;
