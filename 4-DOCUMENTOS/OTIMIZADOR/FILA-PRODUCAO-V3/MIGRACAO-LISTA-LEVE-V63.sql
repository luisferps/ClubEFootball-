-- V63: página da fila integral sem varrer todas as linhas a cada atualização.
--
-- A página e os totais continuam vindo do mesmo contrato privado. A diferença
-- é que a contagem não é mais refeita sobre 184 mil linhas: ela usa o resumo
-- canônico atualizado pela mesma transação que altera o estado da linha.
-- Não altera fila, fórmula, motor, resultados ou publicação.

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
  v_resumo clube_novo.otimizador_lote_producao_status_v1%rowtype;
begin
  if p_lote_id is null
     or coalesce(p_offset, 0) < 0
     or coalesce(p_limite, 0) not between 1 and 200
     or p_grupo not in ('abertas', 'finais') then
    raise exception 'leitura operacional V63 recusada: parâmetros fora da faixa';
  end if;

  -- Os contadores são mantidos junto da mudança de estado da linha. Sem esse
  -- resumo, a tela falha fechada em vez de recontar a fila inteira e expirar.
  select * into v_resumo
  from clube_novo.otimizador_lote_producao_status_v1
  where lote_id = p_lote_id;
  if not found then
    raise exception 'leitura operacional V63 recusada: resumo de estado ausente para lote %', p_lote_id;
  end if;

  v_total := case
    when p_grupo = 'abertas' then
      greatest(0, coalesce(v_resumo.pendentes, 0) + coalesce(v_resumo.processando, 0))
    else
      greatest(0, coalesce(v_resumo.concluidas, 0) + coalesce(v_resumo.bloqueadas, 0) + coalesce(v_resumo.interrompidas, 0))
  end;

  -- A página seleciona só as colunas apresentadas. Não use `e.*`: a view
  -- também possui fotografias pesadas que não são necessárias nesta tela.
  with pagina as materialized (
    select
      e.ordem_fila,
      e.linha_id,
      e.card_id,
      e.carta_nome,
      e.funcao_id,
      e.funcao_rotulo,
      e.posicao_id,
      e.posicao_rotulo,
      e.estado,
      e.motivo,
      e.iniciada_em,
      e.finalizada_em,
      e.overall_snapshot,
      e.tecnico_id,
      e.pontuacao_final,
      e.b1,
      e.barras,
      e.impeto_adicional_codigo,
      e.habilidades_adicionais,
      e.builds_comparadas,
      e.builds_possiveis,
      e.duracao_segundos,
      e.bonificador
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
    'total', v_total,
    'offset', p_offset,
    'limite', p_limite,
    'itens', v_itens
  );
end
$$;

-- Teto explícito: uma regressão futura falha fechada e não deixa a tela presa.
alter function public.otimizador_producao_fila_operacional_v4(uuid, integer, integer, text)
  set statement_timeout to '5s';
revoke all on function public.otimizador_producao_fila_operacional_v4(uuid, integer, integer, text)
  from public, anon, authenticated;
grant execute on function public.otimizador_producao_fila_operacional_v4(uuid, integer, integer, text)
  to service_role;

comment on function public.otimizador_producao_fila_operacional_v4(uuid, integer, integer, text) is
  'V63: página privada do Otimizador usa o resumo canônico para total e seleciona apenas as colunas exibidas; sem varredura da fila, fórmula ou publicação.';

notify pgrst, 'reload schema';

commit;
