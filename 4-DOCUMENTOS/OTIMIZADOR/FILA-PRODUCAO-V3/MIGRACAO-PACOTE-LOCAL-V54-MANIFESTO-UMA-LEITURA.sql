begin;

create or replace function public.otimizador_producao_pacote_local_manifesto_v2(p_lote_id uuid)
returns jsonb
language plpgsql
stable security definer
set search_path to ''
set statement_timeout to '90s'
as $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_cartas integer;
  v_linhas integer;
  v_condicionais integer;
  v_prioridade_fingerprint text;
begin
  if p_lote_id is null then
    raise exception 'pacote local v2 recusado: lote obrigatório';
  end if;

  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id;

  if not found or v_lote.tipo_lote <> 'integral' then
    raise exception 'pacote local v2 recusado: lote integral inexistente';
  end if;
  if v_lote.estado <> 'pausado'
     or v_lote.preparo_concluido <> v_lote.preparo_total
     or v_lote.pode_publicar is distinct from false
     or v_lote.formula_fingerprint not in (
       '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad',
       'bf6040b6fdbbb4a6b8cf97fe66cb441507ee637ec7edb300cf2ebabb5814f070',
       '5a7446b3dfa7b6b45ece1f611b1751fc1221f06e76c53cbd0827a83962c76e89'
     )
     or not coalesce((v_lote.regua_snapshot -> 'gate' ->> 'pode_rodar')::boolean, false) then
    raise exception 'pacote local v2 recusado: lote não está pausado e apto para fotografia selada';
  end if;
  if exists (
    select 1 from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id and l.estado_otimizador = 'processando'
  ) then
    raise exception 'pacote local v2 recusado: há reserva ativa no lote';
  end if;
  if exists (
    select 1 from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id
      and l.estado_otimizador = 'pendente'
      and ((l.impeto_condicional_codigo is null) <> (l.impeto_condicional_nivel is null))
  ) then
    raise exception 'pacote local v2 recusado: há linha com Ímpeto condicional pela metade (código sem nível, ou o contrário)';
  end if;

  -- A fotografia de prioridade é cara nos lotes grandes. Materializar uma vez
  -- evita as quatro leituras integrais que faziam o RPC estourar 30 segundos.
  with pendentes as materialized (
    select p.*
    from clube_novo.otimizador_fila_prioridade_v1 p
    where p.lote_id = p_lote_id
  )
  select count(distinct card_id)::integer,
         count(*)::integer,
         count(*) filter(where impeto_condicional_codigo is not null)::integer,
         encode(extensions.digest(convert_to(coalesce(
           string_agg(linha_id::text||':'||ordem_fila::text||':'||prioridade_grupo::text||':'||
             coalesce(overall_prioridade::text,'null')||':'||nivel_maximo::text||':'||captura_id::text||':'||entrada_fingerprint,
             ',' order by ordem_fila),''),'UTF8'),'sha256'),'hex')
  into v_cartas,v_linhas,v_condicionais,v_prioridade_fingerprint
  from pendentes;

  return jsonb_build_object(
    'contrato','otimizador_pacote_local_v2',
    'lote_id',v_lote.id,
    'formula_fingerprint',v_lote.formula_fingerprint,
    'contrato_fingerprint',v_lote.contrato_fingerprint,
    'motor_versao',v_lote.motor_versao,
    'lote_fingerprint',v_lote.fingerprint,
    'regua',v_lote.regua_snapshot,
    'pode_publicar',false,
    'impetos_condicionais',case when v_condicionais>0 then 'por_degrau' else 'nenhum_no_lote' end,
    'linhas_condicionais',coalesce(v_condicionais,0),
    'cartas_total',coalesce(v_cartas,0),
    'linhas_total',coalesce(v_linhas,0),
    'paginacao','cursor_canonico',
    'prioridade_contrato','prioridade_orcamento_v1',
    'prioridade_fingerprint',v_prioridade_fingerprint,
    'fonte','clube_novo.otimizador_entrada_linha_v1'
  );
end
$function$;

comment on function public.otimizador_producao_pacote_local_manifesto_v2(uuid) is
  'Manifesto selado V54. Calcula contagens e selo da prioridade em uma única leitura materializada.';

commit;
