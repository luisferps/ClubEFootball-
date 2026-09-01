-- V52: contrato V2 de fotografia local do Otimizador.
--
-- Corrige o gargalo de produto da exportação V1: V1 recontava toda a fila e
-- fazia paginação por deslocamento a cada página. V2 conta uma única vez no
-- manifesto e usa cursores canônicos (card_id/ordem_fila) para cada página.
--
-- Não altera fórmula, pesos, ordem de cálculo, moldes, estados de negócio,
-- publicação, resultados já gravados ou gates. O lote precisa continuar
-- pausado e sem reserva para ser fotografado.

begin;

create or replace function public.otimizador_producao_pacote_local_manifesto_v2(
  p_lote_id uuid
) returns jsonb
language plpgsql
stable
security definer
set search_path to ''
as $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_cartas integer;
  v_linhas integer;
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
     or v_lote.formula_fingerprint <> '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad'
     or not coalesce((v_lote.regua_snapshot -> 'gate' ->> 'pode_rodar')::boolean, false) then
    raise exception 'pacote local v2 recusado: lote não está pausado e apto para fotografia selada';
  end if;
  if exists (
    select 1
    from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id
      and l.estado_otimizador = 'processando'
  ) then
    raise exception 'pacote local v2 recusado: há reserva ativa no lote';
  end if;
  if exists (
    select 1
    from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id
      and l.estado_otimizador = 'pendente'
      and (l.impeto_condicional_codigo is not null or l.impeto_condicional_nivel is not null)
  ) then
    raise exception 'pacote local v2 recusado: Ímpeto condicional pendente continua desligado';
  end if;

  -- O catálogo de fotografias é imutável para este lote; cartas já concluídas
  -- permanecem no pacote, mas nenhuma delas é calculada sem linha pendente.
  select count(*)::integer into v_cartas
  from clube_novo.otimizador_lote_producao_carta_v3 s
  where s.lote_id = p_lote_id;

  -- O índice de lote/estado torna esta contagem independente do tamanho da
  -- tabela inteira e a contagem é conferida no fim do download local.
  select count(*)::integer into v_linhas
  from clube_novo.build_linha_card l
  where l.lote_producao_id = p_lote_id
    and l.estado_otimizador = 'pendente';

  return jsonb_build_object(
    'contrato', 'otimizador_pacote_local_v2',
    'lote_id', v_lote.id,
    'formula_fingerprint', v_lote.formula_fingerprint,
    'contrato_fingerprint', v_lote.contrato_fingerprint,
    'motor_versao', v_lote.motor_versao,
    'lote_fingerprint', v_lote.fingerprint,
    'regua', v_lote.regua_snapshot,
    'pode_publicar', false,
    'impetos_condicionais', 'desligados',
    'cartas_total', coalesce(v_cartas, 0),
    'linhas_total', coalesce(v_linhas, 0),
    'paginacao', 'cursor_canonico',
    'fonte', 'clube_novo.otimizador_entrada_linha_v1'
  );
end
$function$;

create or replace function public.otimizador_producao_pacote_local_cartas_v2(
  p_lote_id uuid,
  p_depois_de_card_id text default null,
  p_limite integer default 1000
) returns jsonb
language plpgsql
stable
security definer
set search_path to ''
as $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_itens jsonb := '[]'::jsonb;
  v_proximo_card_id text;
begin
  if p_lote_id is null or coalesce(p_limite, 0) not between 1 and 1000 then
    raise exception 'página de cartas local v2 recusada: argumentos inválidos';
  end if;
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id;
  if not found or v_lote.tipo_lote <> 'integral'
     or v_lote.estado <> 'pausado'
     or v_lote.preparo_concluido <> v_lote.preparo_total
     or v_lote.pode_publicar is distinct from false then
    raise exception 'página de cartas local v2 recusada: fotografia não está estável';
  end if;
  if exists (
    select 1 from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id and l.estado_otimizador = 'processando'
  ) then
    raise exception 'página de cartas local v2 recusada: há reserva ativa';
  end if;

  with pagina as materialized (
    select s.card_id, s.entrada_fingerprint, s.entrada_otimizador,
           s.carta_versao_bonificador, s.carta_fingerprint_bonificador,
           c.nome as carta_nome
    from clube_novo.otimizador_lote_producao_carta_v3 s
    left join clube_novo.carta_jogo c on c.card_id = s.card_id
    where s.lote_id = p_lote_id
      and (nullif(trim(p_depois_de_card_id), '') is null or s.card_id > p_depois_de_card_id)
    order by s.card_id
    limit p_limite
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'card_id', card_id,
    'carta_entrada_fingerprint', entrada_fingerprint,
    'carta', entrada_otimizador,
    'carta_nome', carta_nome,
    'carta_versao', carta_versao_bonificador,
    'carta_fingerprint', carta_fingerprint_bonificador
  ) order by card_id), '[]'::jsonb), max(card_id)
  into v_itens, v_proximo_card_id
  from pagina;

  return jsonb_build_object(
    'contrato', 'otimizador_pacote_local_v2',
    'lote_id', p_lote_id,
    'depois_de_card_id', p_depois_de_card_id,
    'proximo_card_id', v_proximo_card_id,
    'limite', p_limite,
    'contagem_no_manifesto', true,
    'itens', v_itens,
    'pode_publicar', false,
    'impetos_condicionais', 'desligados'
  );
end
$function$;

create or replace function public.otimizador_producao_pacote_local_linhas_v2(
  p_lote_id uuid,
  p_depois_de_ordem bigint default null,
  p_limite integer default 1000
) returns jsonb
language plpgsql
stable
security definer
set search_path to ''
as $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_itens jsonb := '[]'::jsonb;
  v_proxima_ordem bigint;
begin
  if p_lote_id is null or coalesce(p_limite, 0) not between 1 and 1000
     or coalesce(p_depois_de_ordem, 0) < 0 then
    raise exception 'página de linhas local v2 recusada: argumentos inválidos';
  end if;
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id;
  if not found or v_lote.tipo_lote <> 'integral'
     or v_lote.estado <> 'pausado'
     or v_lote.preparo_concluido <> v_lote.preparo_total
     or v_lote.pode_publicar is distinct from false
     or v_lote.formula_fingerprint <> '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad' then
    raise exception 'página de linhas local v2 recusada: fotografia não está estável';
  end if;
  if exists (
    select 1 from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id and l.estado_otimizador = 'processando'
  ) then
    raise exception 'página de linhas local v2 recusada: há reserva ativa';
  end if;

  with pagina as materialized (
    select q.linha_id, q.ordem_fila, q.entrada_fingerprint,
           l.card_id, l.funcao_id, l.posicao_id,
           l.impeto_condicional_codigo, l.impeto_condicional_nivel,
           c.nome as carta_nome, f.rotulo as funcao_rotulo, p.nome_pt as posicao_rotulo
    from clube_novo.otimizador_lote_producao_linha_v3 q
    join clube_novo.build_linha_card l on l.id = q.linha_id
    left join clube_novo.carta_jogo c on c.card_id = l.card_id
    left join clube_novo.funcao_sistema f on f.id = l.funcao_id
    left join clube_novo.posicao_jogo p on p.id = l.posicao_id
    where q.lote_id = p_lote_id
      and (p_depois_de_ordem is null or q.ordem_fila > p_depois_de_ordem)
      and l.estado_otimizador = 'pendente'
      and l.impeto_condicional_codigo is null
      and l.impeto_condicional_nivel is null
    order by q.ordem_fila
    limit p_limite
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'linha_id', linha_id,
    'ordem_fila', ordem_fila,
    'card_id', card_id,
    'funcao_id', funcao_id,
    'posicao_id', posicao_id,
    'carta_entrada_fingerprint', entrada_fingerprint,
    'carta_nome', carta_nome,
    'funcao_rotulo', funcao_rotulo,
    'posicao_rotulo', posicao_rotulo,
    'impeto_condicional_codigo', impeto_condicional_codigo,
    'impeto_condicional_nivel', impeto_condicional_nivel
  ) order by ordem_fila), '[]'::jsonb), max(ordem_fila)
  into v_itens, v_proxima_ordem
  from pagina;

  return jsonb_build_object(
    'contrato', 'otimizador_pacote_local_v2',
    'lote_id', p_lote_id,
    'depois_de_ordem', p_depois_de_ordem,
    'proxima_ordem_fila', v_proxima_ordem,
    'limite', p_limite,
    'contagem_no_manifesto', true,
    'itens', v_itens,
    'pode_publicar', false,
    'impetos_condicionais', 'desligados'
  );
end
$function$;

create or replace function public.otimizador_portal_local_v8(
  p_operacao text,
  p_corpo jsonb default '{}'::jsonb
) returns jsonb
language plpgsql
security definer
set search_path to ''
as $function$
begin
  if p_operacao = 'otimizador_producao_pacote_local_manifesto_v2' then
    return public.otimizador_producao_pacote_local_manifesto_v2((p_corpo ->> 'p_lote_id')::uuid);
  end if;
  if p_operacao = 'otimizador_producao_pacote_local_cartas_v2' then
    return public.otimizador_producao_pacote_local_cartas_v2(
      (p_corpo ->> 'p_lote_id')::uuid,
      nullif(p_corpo ->> 'p_depois_de_card_id', ''),
      coalesce((p_corpo ->> 'p_limite')::integer, 1000)
    );
  end if;
  if p_operacao = 'otimizador_producao_pacote_local_linhas_v2' then
    return public.otimizador_producao_pacote_local_linhas_v2(
      (p_corpo ->> 'p_lote_id')::uuid,
      nullif(p_corpo ->> 'p_depois_de_ordem', '')::bigint,
      coalesce((p_corpo ->> 'p_limite')::integer, 1000)
    );
  end if;
  return public.otimizador_portal_local_v7(p_operacao, p_corpo);
end
$function$;

revoke all on function public.otimizador_producao_pacote_local_manifesto_v2(uuid)
  from public, anon, authenticated;
revoke all on function public.otimizador_producao_pacote_local_cartas_v2(uuid, text, integer)
  from public, anon, authenticated;
revoke all on function public.otimizador_producao_pacote_local_linhas_v2(uuid, bigint, integer)
  from public, anon, authenticated;
revoke all on function public.otimizador_portal_local_v8(text, jsonb)
  from public, anon, authenticated;

grant execute on function public.otimizador_producao_pacote_local_manifesto_v2(uuid)
  to service_role;
grant execute on function public.otimizador_producao_pacote_local_cartas_v2(uuid, text, integer)
  to service_role;
grant execute on function public.otimizador_producao_pacote_local_linhas_v2(uuid, bigint, integer)
  to service_role;
grant execute on function public.otimizador_portal_local_v8(text, jsonb)
  to bonificador_runtime;

comment on function public.otimizador_producao_pacote_local_manifesto_v2(uuid) is
  'V52: manifesto privado de fotografia local, com contagens únicas e gates preservados.';
comment on function public.otimizador_producao_pacote_local_cartas_v2(uuid, text, integer) is
  'V52: página de snapshots por cursor card_id, sem recontar fila.';
comment on function public.otimizador_producao_pacote_local_linhas_v2(uuid, bigint, integer) is
  'V52: página de linhas pendentes por cursor ordem_fila, sem OFFSET nem recontagem.';
comment on function public.otimizador_portal_local_v8(text, jsonb) is
  'V52: allowlist privada do pacote local V2; delega operações anteriores ao portal V7.';

notify pgrst, 'reload schema';
commit;
