-- V12: a página visível percorre a ordem canônica da fila e só junta os
-- detalhes da página. Não altera fórmula, seleção, reserva, resultado,
-- estados, publicação ou Bonificador.

begin;

do $$
begin
  if to_regclass('clube_novo.otimizador_lote_producao_status_v1') is null
     or to_regprocedure('public.otimizador_producao_status_v6(uuid)') is null then
    raise exception 'V12 recusada: resumo de estado V11 ausente';
  end if;
end
$$;

create or replace function public.otimizador_producao_fila_operacional_v2(
  p_lote_id uuid,
  p_offset integer default 0,
  p_limite integer default 100,
  p_grupo text default 'abertas'
)
returns jsonb
language plpgsql
stable
security definer
set search_path to ''
as $$
declare
  v_total integer := 0;
  v_itens jsonb := '[]'::jsonb;
begin
  if p_lote_id is null
     or coalesce(p_offset, 0) < 0
     or coalesce(p_limite, 0) not between 1 and 200
     or p_grupo not in ('abertas','finais') then
    raise exception 'leitura operacional V2 recusada: parâmetros fora da faixa';
  end if;

  select case when p_grupo = 'abertas'
              then s.pendentes + s.processando
              else s.concluidas + s.bloqueadas + s.interrompidas end
  into v_total
  from clube_novo.otimizador_lote_producao_status_v1 s
  where s.lote_id = p_lote_id;

  if not found then
    raise exception 'leitura operacional V2 recusada: resumo do lote ausente';
  end if;

  if p_grupo = 'abertas' then
    with pagina as materialized (
      select
        q.ordem_fila, q.overall_snapshot,
        l.id as linha_id, l.card_id, l.funcao_id, l.posicao_id,
        l.estado_otimizador as estado, l.erro_otimizador as motivo,
        l.otimizador_iniciado_em as iniciada_em,
        l.otimizador_finalizado_em as finalizada_em,
        l.build_otimizador_id, l.build_bonificador_id
      from clube_novo.otimizador_lote_producao_linha_v3 q
      join lateral (
        select *
        from clube_novo.build_linha_card l
        where l.id = q.linha_id
          and l.estado_otimizador in ('processando','pendente')
      ) l on true
      where q.lote_id = p_lote_id
      order by q.ordem_fila
      offset p_offset limit p_limite
    )
    select coalesce(jsonb_agg(jsonb_build_object(
      'ordem_fila',p.ordem_fila,'linha_id',p.linha_id,'card_id',p.card_id,
      'funcao_id',p.funcao_id,'posicao_id',p.posicao_id,'estado',p.estado,
      'motivo',p.motivo,'iniciada_em',p.iniciada_em,'finalizada_em',p.finalizada_em,
      'overall_snapshot',p.overall_snapshot,'tecnico_id',o.tecnico_id,
      'pontuacao_final',o.pontuacao,'b1',o.pontuacao,'barras',o.barras,
      'impeto_adicional_codigo',o.impeto_adicional_codigo,
      'habilidades_adicionais',coalesce(to_jsonb(o.habilidades_adicionais),'[]'::jsonb),
      'builds_comparadas',o.builds_comparadas::text,
      'builds_possiveis',o.builds_possiveis::text,
      'duracao_segundos',case
        when p.iniciada_em is not null and p.finalizada_em is not null
        then extract(epoch from p.finalizada_em - p.iniciada_em) end,
      'bonificador',case
        when p.build_bonificador_id is not null then 'concluido'
        when p.estado = 'concluido' then 'pendente'
        else 'aguardando_otimizador' end
    ) order by p.ordem_fila),'[]'::jsonb)
    into v_itens
    from pagina p
    left join clube_novo.build_otimizador o on o.id = p.build_otimizador_id;
  else
    with pagina as materialized (
      select
        q.ordem_fila, q.overall_snapshot,
        l.id as linha_id, l.card_id, l.funcao_id, l.posicao_id,
        l.estado_otimizador as estado, l.erro_otimizador as motivo,
        l.otimizador_iniciado_em as iniciada_em,
        l.otimizador_finalizado_em as finalizada_em,
        l.build_otimizador_id, l.build_bonificador_id
      from clube_novo.otimizador_lote_producao_linha_v3 q
      join lateral (
        select *
        from clube_novo.build_linha_card l
        where l.id = q.linha_id
          and l.estado_otimizador in ('concluido','bloqueado','interrompido')
      ) l on true
      where q.lote_id = p_lote_id
      order by q.ordem_fila
      offset p_offset limit p_limite
    )
    select coalesce(jsonb_agg(jsonb_build_object(
      'ordem_fila',p.ordem_fila,'linha_id',p.linha_id,'card_id',p.card_id,
      'funcao_id',p.funcao_id,'posicao_id',p.posicao_id,'estado',p.estado,
      'motivo',p.motivo,'iniciada_em',p.iniciada_em,'finalizada_em',p.finalizada_em,
      'overall_snapshot',p.overall_snapshot,'tecnico_id',o.tecnico_id,
      'pontuacao_final',o.pontuacao,'b1',o.pontuacao,'barras',o.barras,
      'impeto_adicional_codigo',o.impeto_adicional_codigo,
      'habilidades_adicionais',coalesce(to_jsonb(o.habilidades_adicionais),'[]'::jsonb),
      'builds_comparadas',o.builds_comparadas::text,
      'builds_possiveis',o.builds_possiveis::text,
      'duracao_segundos',case
        when p.iniciada_em is not null and p.finalizada_em is not null
        then extract(epoch from p.finalizada_em - p.iniciada_em) end,
      'bonificador',case
        when p.build_bonificador_id is not null then 'concluido'
        when p.estado = 'concluido' then 'pendente'
        else 'aguardando_otimizador' end
    ) order by p.ordem_fila),'[]'::jsonb)
    into v_itens
    from pagina p
    left join clube_novo.build_otimizador o on o.id = p.build_otimizador_id;
  end if;

  return jsonb_build_object(
    'contrato','otimizador_fila_producao_v6','lote_id',p_lote_id,
    'grupo',p_grupo,'total',coalesce(v_total, 0),
    'offset',p_offset,'limite',p_limite,'itens',v_itens
  );
end
$$;

revoke all on function public.otimizador_producao_fila_operacional_v2(uuid,integer,integer,text)
  from public,anon,authenticated;
grant execute on function public.otimizador_producao_fila_operacional_v2(uuid,integer,integer,text)
  to service_role;

notify pgrst, 'reload schema';

commit;
