-- Fila operacional V4 do Bonificador.
-- A origem e o marcador são canônicos: clube_novo.build_linha_card.pendencias
-- contém bonificador_nao_executado e a linha ainda não possui build_bonificador_id.
-- Não lê clube/public legados, não executa o motor e não modifica fórmulas,
-- pesos, moldes, ordem ou regras de negócio.
begin;

create or replace function public.bonificador_contexto_fila_v4(
  p_limit integer default 1000,
  p_offset integer default 0
)
returns table(
  build_linha_card_id bigint,
  card_id text,
  funcao_id bigint,
  funcao_codigo text,
  posicao_id integer,
  carta_versao text,
  carta_fingerprint text,
  contrato_versao text,
  contrato_fingerprint text,
  formula_fingerprint text
)
language sql stable security definer set search_path=''
as $function$
  with candidatos as materialized (
    select l.id,l.card_id,l.funcao_id,l.posicao_id,l.carta_versao,l.carta_fingerprint
    from clube_novo.build_linha_card l
    where l.build_bonificador_id is null
      and l.lote_estado='concluido'
      and l.estado='pendente'
      and l.estado_otimizador='concluido'
      and l.pendencias @> array['bonificador_nao_executado']::text[]
    limit least(greatest(coalesce(p_limit,1000),1),5000)
    offset greatest(coalesce(p_offset,0),0)
  )
  select l.id,l.card_id,l.funcao_id,''::text,l.posicao_id,
         l.carta_versao,l.carta_fingerprint,'bonificador-regua-v2',
         'regua_lida_pelo_motor_antes_do_calculo',
         'ad8427acf268cf695bf69eca87704be95d8e1f13213d3ddec3d21955f705ce09'
  from candidatos l
  order by l.id
$function$;

revoke all on function public.bonificador_contexto_fila_v4(integer,integer)
  from public,anon,authenticated;
grant execute on function public.bonificador_contexto_fila_v4(integer,integer) to service_role;

commit;
