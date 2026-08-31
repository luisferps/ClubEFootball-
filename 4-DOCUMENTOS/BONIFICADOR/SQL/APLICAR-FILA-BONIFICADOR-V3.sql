-- Fila de teste exclusiva do Bonificador. Não altera fórmulas, pesos, moldes
-- nem o produtor canônico de linhas. Não executa o motor nem publica resultados.
begin;

do $preflight$
declare n_par bigint; n_linhas bigint; n_cartas bigint; n_pares bigint;
begin
  select count(*) into n_par from clube_novo.bonificador_par;
  if n_par <> 0 then
    raise exception 'preflight: bonificador_par deveria estar vazia, encontrou %', n_par;
  end if;

  select count(*), count(distinct l.card_id), count(distinct (l.card_id,l.funcao_id))
    into n_linhas, n_cartas, n_pares
  from clube_novo.build_linha_card l
  join clube_novo.funcao_sistema f on f.id=l.funcao_id and f.ativa and f.pode_rodar
  cross join lateral public.bonificador_carta_v2(l.card_id) c
  where l.execucao_tipo='teste_isolado'
    and l.lote_estado='concluido'
    and l.estado='pendente'
    and l.estado_otimizador='concluido'
    and l.build_bonificador_id is null
    and l.pendencias @> array['teste_nao_publicado','bonificador_nao_executado']::text[]
    and cardinality(l.pendencias)=2
    and coalesce((c->>'pode_rodar')::boolean,false);
  if n_linhas <> 613 or n_cartas <> 50 or n_pares <> 345 then
    raise exception 'preflight: universo de teste divergente (% linhas, % cartas, % pares; esperado 613/50/345)', n_linhas, n_cartas, n_pares;
  end if;
end $preflight$;

insert into clube_novo.bonificador_par(card_id,funcao_id)
select distinct l.card_id,l.funcao_id
from clube_novo.build_linha_card l
join clube_novo.funcao_sistema f on f.id=l.funcao_id and f.ativa and f.pode_rodar
cross join lateral public.bonificador_carta_v2(l.card_id) c
where l.execucao_tipo='teste_isolado'
  and l.lote_estado='concluido'
  and l.estado='pendente'
  and l.estado_otimizador='concluido'
  and l.build_bonificador_id is null
  and l.pendencias @> array['teste_nao_publicado','bonificador_nao_executado']::text[]
  and cardinality(l.pendencias)=2
  and coalesce((c->>'pode_rodar')::boolean,false);

create or replace function public.bonificador_contexto_fila_v3(
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
  select l.id,l.card_id,l.funcao_id,f.codigo_legado,l.posicao_id,
         l.carta_versao,c->>'carta_fingerprint',r->>'contrato',
         r->>'contrato_fingerprint',
         'ad8427acf268cf695bf69eca87704be95d8e1f13213d3ddec3d21955f705ce09'
  from clube_novo.build_linha_card l
  join clube_novo.bonificador_par p on p.card_id=l.card_id and p.funcao_id=l.funcao_id
  join clube_novo.funcao_sistema f on f.id=l.funcao_id and f.ativa and f.pode_rodar
  cross join lateral public.bonificador_regua_v2() r
  cross join lateral public.bonificador_carta_v2(l.card_id) c
  where l.execucao_tipo='teste_isolado'
    and l.lote_estado='concluido'
    and l.estado='pendente'
    and l.estado_otimizador='concluido'
    and l.build_bonificador_id is null
    and l.pendencias @> array['teste_nao_publicado','bonificador_nao_executado']::text[]
    and cardinality(l.pendencias)=2
    and coalesce((r->>'pode_rodar')::boolean,false)
    and coalesce((c->>'pode_rodar')::boolean,false)
    and c->>'carta_versao'=l.carta_versao
  order by l.id
  limit least(greatest(coalesce(p_limit,1000),1),5000)
  offset greatest(coalesce(p_offset,0),0)
$function$;

revoke all on function public.bonificador_contexto_fila_v3(integer,integer)
  from public,anon,authenticated;
grant execute on function public.bonificador_contexto_fila_v3(integer,integer) to service_role;

do $readback$
declare n bigint; nc bigint;
begin
  select count(*),count(distinct card_id) into n,nc
    from public.bonificador_contexto_fila_v3(5000,0);
  if n<>613 or nc<>50 then
    raise exception 'readback: fila v3 divergente (% linhas, % cartas)',n,nc;
  end if;
  if not has_function_privilege('service_role','public.bonificador_contexto_fila_v3(integer,integer)','EXECUTE')
     or has_function_privilege('anon','public.bonificador_contexto_fila_v3(integer,integer)','EXECUTE')
     or has_function_privilege('authenticated','public.bonificador_contexto_fila_v3(integer,integer)','EXECUTE') then
    raise exception 'readback: grants incorretos na fila v3';
  end if;
end $readback$;

commit;
