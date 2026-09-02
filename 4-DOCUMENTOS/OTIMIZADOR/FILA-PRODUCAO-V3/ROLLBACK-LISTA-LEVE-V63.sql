-- Rollback V63: restaura literalmente a leitura V19, sem alterar linhas,
-- resultados, fórmula, motor ou publicação.

begin;

create or replace function public.otimizador_producao_fila_operacional_v4(
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
     or p_grupo not in ('abertas', 'finais') then
    raise exception 'leitura operacional V4 recusada: parâmetros fora da faixa';
  end if;

  select count(*)::integer into v_total
  from clube_novo.otimizador_entrada_linha_v1 e
  where e.lote_id = p_lote_id
    and (
      (p_grupo = 'abertas' and e.estado in ('pendente', 'processando'))
      or
      (p_grupo = 'finais' and e.estado in ('concluido', 'bloqueado', 'interrompido', 'falhou'))
    );

  with pagina as materialized (
    select e.*
    from clube_novo.otimizador_entrada_linha_v1 e
    where e.lote_id = p_lote_id
      and (
        (p_grupo = 'abertas' and e.estado in ('pendente', 'processando'))
        or
        (p_grupo = 'finais' and e.estado in ('concluido', 'bloqueado', 'interrompido', 'falhou'))
      )
    order by e.ordem_fila
    offset p_offset limit p_limite
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'ordem_fila', p.ordem_fila,
    'linha_id', p.linha_id,
    'card_id', p.card_id,
    'carta_nome', p.carta_nome,
    'funcao_id', p.funcao_id,
    'funcao_rotulo', p.funcao_rotulo,
    'posicao_id', p.posicao_id,
    'posicao_rotulo', p.posicao_rotulo,
    'estado', p.estado,
    'motivo', p.motivo,
    'iniciada_em', p.iniciada_em,
    'finalizada_em', p.finalizada_em,
    'overall_snapshot', p.overall_snapshot,
    'tecnico_id', p.tecnico_id,
    'pontuacao_final', p.pontuacao_final,
    'b1', p.b1,
    'barras', p.barras,
    'impeto_adicional_codigo', p.impeto_adicional_codigo,
    'habilidades_adicionais', p.habilidades_adicionais,
    'builds_comparadas', p.builds_comparadas,
    'builds_possiveis', p.builds_possiveis,
    'duracao_segundos', p.duracao_segundos,
    'bonificador', p.bonificador
  ) order by p.ordem_fila), '[]'::jsonb)
  into v_itens
  from pagina p;

  return jsonb_build_object(
    'contrato', 'otimizador_fila_producao_v7',
    'fonte', 'clube_novo.otimizador_entrada_linha_v1',
    'lote_id', p_lote_id,
    'grupo', p_grupo,
    'total', coalesce(v_total, 0),
    'offset', p_offset,
    'limite', p_limite,
    'itens', v_itens
  );
end
$$;

alter function public.otimizador_producao_fila_operacional_v4(uuid, integer, integer, text)
  reset statement_timeout;
revoke all on function public.otimizador_producao_fila_operacional_v4(uuid, integer, integer, text)
  from public, anon, authenticated;
grant execute on function public.otimizador_producao_fila_operacional_v4(uuid, integer, integer, text)
  to service_role;

comment on function public.otimizador_producao_fila_operacional_v4(uuid, integer, integer, text) is
  'V19: página do painel derivada da mesma view privada da reserva; sem leitura de tabela pela UI.';

notify pgrst, 'reload schema';

commit;
