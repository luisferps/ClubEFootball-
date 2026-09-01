-- Contrato privado da aba Fila de resultados. Lê somente resultados já gravados.
-- Não recalcula, não grava e não altera fórmula, gates ou fila de pendências.
begin;
create function public.bonificador_resultados_v1(p_limit integer default 1000, p_offset integer default 0)
returns table(
  build_linha_card_id bigint, card_id text, carta_nome text, carta_tipo text,
  carta_box text, carta_overall integer, funcao_id bigint, funcao_codigo text,
  funcao_nome text, posicao_id integer, posicao_codigo text, posicao_nome text,
  estado text, b_corpo numeric, b_pe_ruim numeric, b_estilo numeric, b_ia numeric,
  b_total numeric, faltou text[], concluido_em timestamptz
)
language sql stable security definer set search_path=''
as $function$
  select l.id,l.card_id,c.nome,c.tipo,c.box,c.overall,l.funcao_id,
         coalesce(f.sigla,'')::text,f.rotulo,l.posicao_id,coalesce(p.codigo_pt,'')::text,p.nome_pt,
         'confirmado'::text,b.b_corpo,b.b_pe_ruim,b.b_estilo,b.bonus_ia,b.b_total,
         coalesce(b.faltou,'{}'::text[]),b.concluido_em
  from clube_novo.build_linha_card l
  join clube_novo.build_bonificador b on b.id=l.build_bonificador_id
  join clube_novo.carta_jogo c on c.card_id=l.card_id
  join clube_novo.funcao_sistema f on f.id=l.funcao_id
  join clube_novo.posicao_jogo p on p.id=l.posicao_id
  order by b.concluido_em desc nulls last,b.id desc
  limit least(greatest(coalesce(p_limit,1000),1),5000)
  offset greatest(coalesce(p_offset,0),0)
$function$;
revoke all on function public.bonificador_resultados_v1(integer,integer) from public,anon,authenticated;
grant execute on function public.bonificador_resultados_v1(integer,integer) to service_role;
grant execute on function public.bonificador_resultados_v1(integer,integer) to bonificador_runtime;
commit;
