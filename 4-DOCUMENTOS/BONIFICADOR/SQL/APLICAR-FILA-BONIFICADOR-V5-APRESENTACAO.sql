-- Contrato privado V5 de apresentação humana da fila do Bonificador.
-- Não altera a seleção, os gates, o motor, a fórmula ou qualquer dado de jogo.
begin;

create function public.bonificador_contexto_fila_v5(
  p_limit integer default 1000,
  p_offset integer default 0
)
returns table(
  build_linha_card_id bigint,
  card_id text,
  carta_nome text,
  carta_tipo text,
  carta_box text,
  carta_overall integer,
  funcao_id bigint,
  funcao_codigo text,
  funcao_nome text,
  posicao_id integer,
  posicao_codigo text,
  posicao_nome text,
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
    order by l.id
    limit least(greatest(coalesce(p_limit,1000),1),5000)
    offset greatest(coalesce(p_offset,0),0)
  )
  select l.id,l.card_id,c.nome,c.tipo,c.box,c.overall,
         l.funcao_id,coalesce(f.sigla,'')::text,f.rotulo,
         l.posicao_id,coalesce(p.codigo_pt,'')::text,p.nome_pt,
         l.carta_versao,l.carta_fingerprint,'bonificador-regua-v2',
         'regua_lida_pelo_motor_antes_do_calculo',
         'ad8427acf268cf695bf69eca87704be95d8e1f13213d3ddec3d21955f705ce09'
  from candidatos l
  join clube_novo.carta_jogo c on c.card_id=l.card_id
  join clube_novo.funcao_sistema f on f.id=l.funcao_id
  join clube_novo.posicao_jogo p on p.id=l.posicao_id
  order by l.id
$function$;

revoke all on function public.bonificador_contexto_fila_v5(integer,integer)
  from public,anon,authenticated;
grant execute on function public.bonificador_contexto_fila_v5(integer,integer) to service_role;
grant execute on function public.bonificador_contexto_fila_v5(integer,integer) to bonificador_runtime;
commit;
