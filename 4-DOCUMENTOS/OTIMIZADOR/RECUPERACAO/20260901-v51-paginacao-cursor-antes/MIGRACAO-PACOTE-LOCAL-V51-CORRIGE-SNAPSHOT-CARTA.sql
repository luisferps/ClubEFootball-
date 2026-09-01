-- V51: corrige somente os aliases físicos do snapshot de carta do pacote local.
--
-- Não altera fórmula, pesos, ordem, fila, resultados, publicação ou gates.
-- A tabela física usa carta_versao_bonificador/carta_fingerprint_bonificador;
-- o contrato continua expondo os nomes neutros carta_versao/carta_fingerprint.

begin;

create or replace function public.otimizador_producao_pacote_local_cartas_v1(
  p_lote_id uuid,
  p_offset integer default 0,
  p_limite integer default 1000
) returns jsonb
language plpgsql
stable
security definer
set search_path to ''
as $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_total integer;
  v_itens jsonb := '[]'::jsonb;
begin
  if p_lote_id is null or coalesce(p_offset, -1) < 0 or coalesce(p_limite, 0) not between 1 and 1000 then
    raise exception 'página de cartas local recusada: argumentos inválidos';
  end if;
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id;
  if not found or v_lote.tipo_lote <> 'integral'
     or v_lote.estado <> 'pausado'
     or v_lote.preparo_concluido <> v_lote.preparo_total
     or v_lote.pode_publicar is distinct from false then
    raise exception 'página de cartas local recusada: fotografia não está estável';
  end if;
  if exists (
    select 1 from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id and l.estado_otimizador = 'processando'
  ) then
    raise exception 'página de cartas local recusada: há reserva ativa';
  end if;

  select count(*)::integer into v_total
  from (
    select distinct q.card_id
    from clube_novo.otimizador_lote_producao_linha_v3 q
    join clube_novo.build_linha_card l on l.id = q.linha_id
    where q.lote_id = p_lote_id
      and l.estado_otimizador = 'pendente'
      and l.impeto_condicional_codigo is null
      and l.impeto_condicional_nivel is null
  ) s;

  with ids as materialized (
    select distinct q.card_id
    from clube_novo.otimizador_lote_producao_linha_v3 q
    join clube_novo.build_linha_card l on l.id = q.linha_id
    where q.lote_id = p_lote_id
      and l.estado_otimizador = 'pendente'
      and l.impeto_condicional_codigo is null
      and l.impeto_condicional_nivel is null
    order by q.card_id
    offset p_offset limit p_limite
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'card_id', s.card_id,
    'carta_entrada_fingerprint', s.entrada_fingerprint,
    'carta', s.entrada_otimizador,
    'carta_nome', c.nome,
    'carta_versao', s.carta_versao_bonificador,
    'carta_fingerprint', s.carta_fingerprint_bonificador
  ) order by s.card_id), '[]'::jsonb)
  into v_itens
  from ids
  join clube_novo.otimizador_lote_producao_carta_v3 s
    on s.lote_id = p_lote_id and s.card_id = ids.card_id
  left join clube_novo.carta_jogo c on c.card_id = s.card_id;

  return jsonb_build_object(
    'contrato', 'otimizador_pacote_local_v1',
    'lote_id', p_lote_id,
    'offset', p_offset,
    'limite', p_limite,
    'total', coalesce(v_total, 0),
    'itens', v_itens,
    'pode_publicar', false,
    'impetos_condicionais', 'desligados'
  );
end
$function$;

revoke all on function public.otimizador_producao_pacote_local_cartas_v1(uuid, integer, integer)
  from public, anon, authenticated;
grant execute on function public.otimizador_producao_pacote_local_cartas_v1(uuid, integer, integer)
  to service_role;
comment on function public.otimizador_producao_pacote_local_cartas_v1(uuid, integer, integer) is
  'V51: fotografia privada do pacote local; aliases de versão/fingerprint apontam para as colunas físicas canônicas.';

notify pgrst, 'reload schema';
commit;
