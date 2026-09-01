-- V17: nomes oficiais de carta para a página operacional, por card_id.
-- Não escreve cartas, linhas, estados, resultados, fórmula, pesos ou publicação.

begin;

do $$
begin
    if to_regprocedure('public.otimizador_portal_local_v3(text,jsonb)') is null then
        raise exception 'V17 recusada: ponte local V16 ausente';
    end if;
end;
$$;

-- A fila só precisa do rótulo da carta. Esta função não carrega posição,
-- atributos ou relações e não aceita busca textual: recebe exclusivamente IDs
-- físicos/canônicos já presentes nas linhas seladas.
create or replace function public.otimizador_rotulos_cartas_fila_v1(p_card_ids text[])
returns jsonb
language plpgsql
stable
security definer
set search_path to ''
as $$
declare
    v_itens jsonb := '[]'::jsonb;
begin
    if p_card_ids is null
       or cardinality(p_card_ids) not between 1 and 200 then
        raise exception 'rótulos de cartas V17 recusados: card_ids fora da faixa';
    end if;

    select coalesce(jsonb_agg(jsonb_build_object(
        'card_id', c.card_id,
        'nome', c.nome
    ) order by c.card_id), '[]'::jsonb)
      into v_itens
      from clube_novo.carta_jogo c
     where c.card_id = any(p_card_ids);

    return jsonb_build_object(
        'contrato', 'otimizador_rotulos_cartas_fila_v1',
        'itens', v_itens
    );
end;
$$;

revoke all on function public.otimizador_rotulos_cartas_fila_v1(text[])
  from public, anon, authenticated;
grant execute on function public.otimizador_rotulos_cartas_fila_v1(text[])
  to service_role;

-- V4 mantém toda a allowlist V13/V16 e acrescenta somente o contrato leve.
-- O browser não chama esta função: apenas o processo local com a credencial
-- privada de runtime possui EXECUTE.
create or replace function public.otimizador_portal_local_v4(
    p_operacao text,
    p_corpo jsonb default '{}'::jsonb
)
returns jsonb
language plpgsql
security definer
set search_path to ''
as $$
declare
    v_card_ids text[];
begin
    if p_operacao = 'otimizador_rotulos_cartas_fila_v1' then
        if jsonb_typeof(coalesce(p_corpo, '{}'::jsonb) -> 'p_card_ids') <> 'array' then
            raise exception 'ponte V17 recusou card_ids fora do contrato';
        end if;
        select coalesce(array_agg(x.card_id), '{}'::text[])
          into v_card_ids
          from jsonb_array_elements_text(p_corpo -> 'p_card_ids') as x(card_id);
        return public.otimizador_rotulos_cartas_fila_v1(v_card_ids);
    end if;
    return public.otimizador_portal_local_v3(p_operacao, p_corpo);
end;
$$;

revoke all on function public.otimizador_portal_local_v4(text, jsonb)
  from public, anon, authenticated;
grant execute on function public.otimizador_portal_local_v4(text, jsonb)
  to bonificador_runtime;

comment on function public.otimizador_rotulos_cartas_fila_v1(text[]) is
  'V17: nomes oficiais de carta por card_id para a página operacional; sem joins de relações.';
comment on function public.otimizador_portal_local_v4(text, jsonb) is
  'V17: allowlist privada local V13/V16 mais rótulos leves de carta por ID.';

notify pgrst, 'reload schema';

commit;
