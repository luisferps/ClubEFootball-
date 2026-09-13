-- Carta com overall NULL e carta nova cujo overall ainda nao foi coletado.
-- Dentro de cada bloco, ela vem antes dos overalls conhecidos. Nenhum lote
-- ativo e reordenado por esta migracao; a regra vale para novos preparos,
-- novas fotografias e para reordenacao explicitamente solicitada depois.
begin;

do $$
declare
  r record;
  v_def text;
  v_nova text;
  v_alteradas integer := 0;
begin
  for r in
    select p.oid,p.proname
    from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public'
      and p.prokind='f'
      and p.proname in (
        'extrator_efhub_planejar_lote_v1',
        'otimizador_producao_criar_lote_integral_v5',
        'otimizador_producao_preparar_fatia_v5',
        'otimizador_reordenar_prioridade_v1'
      )
  loop
    v_def := pg_get_functiondef(r.oid);
    v_nova := regexp_replace(
      v_def,
      '(overall_snapshot|overall)[[:space:]]+DESC[[:space:]]+NULLS[[:space:]]+LAST',
      '\1 DESC NULLS FIRST',
      'gi'
    );
    if v_nova = v_def then
      raise exception 'Funcao % nao contem a ordem antiga esperada',r.proname;
    end if;
    execute v_nova;
    v_alteradas := v_alteradas + 1;
  end loop;
  if v_alteradas <> 4 then
    raise exception 'Esperadas 4 funcoes; encontradas %',v_alteradas;
  end if;
end $$;

commit;
