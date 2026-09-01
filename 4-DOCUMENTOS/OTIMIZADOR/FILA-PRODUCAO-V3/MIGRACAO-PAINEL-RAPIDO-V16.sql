-- V16: caminho rápido do painel e correção acumulada da página de resultados.
-- Não escreve linhas, não modifica estados, fórmula, pesos, moldes ou publicação.

begin;

do $$
begin
    if to_regprocedure('public.otimizador_producao_fila_operacional_v2(uuid,integer,integer,text)') is null
       or to_regprocedure('public.otimizador_portal_local_v1(text,jsonb)') is null then
        raise exception 'V16 recusada: contratos V12/V13 ausentes';
    end if;
end;
$$;

-- Corrige V14 sem depender de coluna de resumo inexistente. A contagem vem
-- das próprias linhas finais, pelo índice (lote_producao_id, estado_otimizador).
create or replace function public.otimizador_producao_fila_operacional_v3(
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
        raise exception 'leitura operacional V3 recusada: parâmetros fora da faixa';
    end if;
    if p_grupo = 'abertas' then
        return public.otimizador_producao_fila_operacional_v2(
            p_lote_id, p_offset, p_limite, 'abertas'
        );
    end if;

    select count(*)::integer into v_total
      from clube_novo.build_linha_card l
     where l.lote_producao_id = p_lote_id
       and l.estado_otimizador in ('concluido', 'bloqueado', 'interrompido', 'falhou');

    with pagina as materialized (
        select q.ordem_fila, q.overall_snapshot,
               l.id as linha_id, l.card_id, l.funcao_id, l.posicao_id,
               l.estado_otimizador as estado, l.erro_otimizador as motivo,
               l.otimizador_iniciado_em as iniciada_em,
               l.otimizador_finalizado_em as finalizada_em,
               l.build_otimizador_id, l.build_bonificador_id
          from clube_novo.build_linha_card l
          join clube_novo.otimizador_lote_producao_linha_v3 q
            on q.lote_id = p_lote_id and q.linha_id = l.id
         where l.lote_producao_id = p_lote_id
           and l.estado_otimizador in ('concluido', 'bloqueado', 'interrompido', 'falhou')
         order by q.ordem_fila
         offset p_offset limit p_limite
    )
    select coalesce(jsonb_agg(jsonb_build_object(
        'ordem_fila', p.ordem_fila, 'linha_id', p.linha_id, 'card_id', p.card_id,
        'funcao_id', p.funcao_id, 'posicao_id', p.posicao_id, 'estado', p.estado,
        'motivo', p.motivo, 'iniciada_em', p.iniciada_em, 'finalizada_em', p.finalizada_em,
        'overall_snapshot', p.overall_snapshot, 'tecnico_id', o.tecnico_id,
        'pontuacao_final', o.pontuacao, 'b1', o.pontuacao, 'barras', o.barras,
        'impeto_adicional_codigo', o.impeto_adicional_codigo,
        'habilidades_adicionais', coalesce(to_jsonb(o.habilidades_adicionais), '[]'::jsonb),
        'builds_comparadas', o.builds_comparadas::text,
        'builds_possiveis', o.builds_possiveis::text,
        'duracao_segundos', case when p.iniciada_em is not null and p.finalizada_em is not null
            then extract(epoch from p.finalizada_em - p.iniciada_em) end,
        'bonificador', case when p.build_bonificador_id is not null then 'concluido'
            when p.estado = 'concluido' then 'pendente' else 'aguardando_otimizador' end
    ) order by p.ordem_fila), '[]'::jsonb)
      into v_itens
      from pagina p
      left join clube_novo.build_otimizador o on o.id = p.build_otimizador_id;

    return jsonb_build_object(
        'contrato', 'otimizador_fila_producao_v6', 'lote_id', p_lote_id,
        'grupo', p_grupo, 'total', coalesce(v_total, 0),
        'offset', p_offset, 'limite', p_limite, 'itens', v_itens
    );
end;
$$;

-- Catálogo mínimo de apresentação da fila: nomes apenas por IDs canônicos.
-- Evita carregar a régua, técnicos e habilidades quando o usuário só quer
-- acompanhar a próxima linha. A aba de teste unitário continua carregando a
-- régua completa sob demanda.
create or replace function public.otimizador_rotulos_fila_v1()
returns jsonb
language sql
stable
security definer
set search_path to ''
as $$
select jsonb_build_object(
    'contrato', 'otimizador_rotulos_fila_v1',
    'funcoes', coalesce((select jsonb_agg(jsonb_build_object(
        'funcao_id', f.id, 'rotulo', f.rotulo
    ) order by f.ordem, f.id)
      from clube_novo.funcao_sistema f
     where f.ativa and f.pode_rodar), '[]'::jsonb),
    'posicoes', coalesce((select jsonb_agg(jsonb_build_object(
        'posicao_id', p.id, 'rotulo', p.nome_pt
    ) order by p.id)
      from clube_novo.posicao_jogo p
     where p.pode_rodar), '[]'::jsonb)
)
$$;

revoke all on function public.otimizador_producao_fila_operacional_v3(uuid, integer, integer, text)
  from public, anon, authenticated;
grant execute on function public.otimizador_producao_fila_operacional_v3(uuid, integer, integer, text)
  to service_role;
revoke all on function public.otimizador_rotulos_fila_v1() from public, anon, authenticated;
grant execute on function public.otimizador_rotulos_fila_v1() to service_role;

create or replace function public.otimizador_portal_local_v3(
    p_operacao text,
    p_corpo jsonb default '{}'::jsonb
)
returns jsonb
language plpgsql
security definer
set search_path to ''
as $$
begin
    if p_operacao = 'otimizador_producao_fila_operacional_v3' then
        return public.otimizador_producao_fila_operacional_v3(
            (p_corpo ->> 'p_lote_id')::uuid, (p_corpo ->> 'p_offset')::integer,
            (p_corpo ->> 'p_limite')::integer, p_corpo ->> 'p_grupo'
        );
    end if;
    if p_operacao = 'otimizador_rotulos_fila_v1' then
        return public.otimizador_rotulos_fila_v1();
    end if;
    return public.otimizador_portal_local_v1(p_operacao, p_corpo);
end;
$$;

revoke all on function public.otimizador_portal_local_v3(text, jsonb) from public;
grant execute on function public.otimizador_portal_local_v3(text, jsonb) to bonificador_runtime;

comment on function public.otimizador_rotulos_fila_v1() is
    'V16: rótulos mínimos da fila por IDs canônicos; apenas apresentação.';
comment on function public.otimizador_portal_local_v3(text, jsonb) is
    'V16: ponte local com fila rápida, rótulos mínimos e allowlist V13.';

notify pgrst, 'reload schema';

commit;
