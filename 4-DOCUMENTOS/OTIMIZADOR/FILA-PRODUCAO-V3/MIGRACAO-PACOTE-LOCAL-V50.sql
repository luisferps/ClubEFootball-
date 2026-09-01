-- Pacote local portátil V1 do Otimizador.
--
-- Não altera fórmula, pesos, ordem, moldes, ímpetos condicionais, publicação
-- ou a fila existente. Só cria contratos privados para: exportar a fotografia
-- integral pausada, reservar por identidade já baixada e concluir até 100
-- resultados que foram calculados localmente pelo mesmo roda_lote_v6.

begin;

create or replace function public.otimizador_producao_pacote_local_manifesto_v1(
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
    raise exception 'pacote local recusado: lote obrigatório';
  end if;

  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id;

  if not found or v_lote.tipo_lote <> 'integral' then
    raise exception 'pacote local recusado: lote integral inexistente';
  end if;
  if v_lote.estado <> 'pausado'
     or v_lote.preparo_concluido <> v_lote.preparo_total
     or v_lote.pode_publicar is distinct from false
     or v_lote.formula_fingerprint <> '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad'
     or not coalesce((v_lote.regua_snapshot -> 'gate' ->> 'pode_rodar')::boolean, false) then
    raise exception 'pacote local recusado: lote não está pausado e apto para fotografia selada';
  end if;
  if exists (
    select 1
    from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id
      and l.estado_otimizador = 'processando'
  ) then
    raise exception 'pacote local recusado: há reserva ativa no lote';
  end if;
  if exists (
    select 1
    from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id
      and l.estado_otimizador = 'pendente'
      and (l.impeto_condicional_codigo is not null or l.impeto_condicional_nivel is not null)
  ) then
    raise exception 'pacote local recusado: Ímpeto condicional pendente continua desligado';
  end if;

  select count(*)::integer into v_linhas
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id = q.linha_id
  where q.lote_id = p_lote_id
    and l.estado_otimizador = 'pendente'
    and l.impeto_condicional_codigo is null
    and l.impeto_condicional_nivel is null;

  select count(*)::integer into v_cartas
  from (
    select distinct q.card_id
    from clube_novo.otimizador_lote_producao_linha_v3 q
    join clube_novo.build_linha_card l on l.id = q.linha_id
    where q.lote_id = p_lote_id
      and l.estado_otimizador = 'pendente'
      and l.impeto_condicional_codigo is null
      and l.impeto_condicional_nivel is null
  ) s;

  return jsonb_build_object(
    'contrato', 'otimizador_pacote_local_v1',
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
    'fonte', 'clube_novo.otimizador_entrada_linha_v1'
  );
end
$function$;

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
    'carta_versao', s.carta_versao,
    'carta_fingerprint', s.carta_fingerprint
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

create or replace function public.otimizador_producao_pacote_local_linhas_v1(
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
    raise exception 'página de linhas local recusada: argumentos inválidos';
  end if;
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id;
  if not found or v_lote.tipo_lote <> 'integral'
     or v_lote.estado <> 'pausado'
     or v_lote.preparo_concluido <> v_lote.preparo_total
     or v_lote.pode_publicar is distinct from false
     or v_lote.formula_fingerprint <> '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad' then
    raise exception 'página de linhas local recusada: fotografia não está estável';
  end if;
  if exists (
    select 1 from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id and l.estado_otimizador = 'processando'
  ) then
    raise exception 'página de linhas local recusada: há reserva ativa';
  end if;

  select count(*)::integer into v_total
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id = q.linha_id
  where q.lote_id = p_lote_id
    and l.estado_otimizador = 'pendente'
    and l.impeto_condicional_codigo is null
    and l.impeto_condicional_nivel is null;

  with pagina as materialized (
    select q.linha_id, q.ordem_fila, q.card_id, q.entrada_fingerprint,
           l.card_id as linha_card_id, l.funcao_id, l.posicao_id,
           l.impeto_condicional_codigo, l.impeto_condicional_nivel,
           c.nome as carta_nome, f.rotulo as funcao_rotulo, p.nome_pt as posicao_rotulo
    from clube_novo.otimizador_lote_producao_linha_v3 q
    join clube_novo.build_linha_card l on l.id = q.linha_id
    left join clube_novo.carta_jogo c on c.card_id = l.card_id
    left join clube_novo.funcao_sistema f on f.id = l.funcao_id
    left join clube_novo.posicao_jogo p on p.id = l.posicao_id
    where q.lote_id = p_lote_id
      and l.estado_otimizador = 'pendente'
      and l.impeto_condicional_codigo is null
      and l.impeto_condicional_nivel is null
    order by q.ordem_fila
    offset p_offset limit p_limite
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'linha_id', linha_id,
    'ordem_fila', ordem_fila,
    'card_id', linha_card_id,
    'funcao_id', funcao_id,
    'posicao_id', posicao_id,
    'carta_entrada_fingerprint', entrada_fingerprint,
    'carta_nome', carta_nome,
    'funcao_rotulo', funcao_rotulo,
    'posicao_rotulo', posicao_rotulo,
    'impeto_condicional_codigo', impeto_condicional_codigo,
    'impeto_condicional_nivel', impeto_condicional_nivel
  ) order by ordem_fila), '[]'::jsonb)
  into v_itens
  from pagina;

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

create or replace function public.otimizador_producao_reservar_linha_local_v1(
  p_lote_id uuid,
  p_worker_id uuid,
  p_linha_id bigint,
  p_card_id text,
  p_funcao_id bigint,
  p_posicao_id integer,
  p_carta_entrada_fingerprint text,
  p_formula_fingerprint text,
  p_contrato_fingerprint text,
  p_motor_versao text,
  p_lote_fingerprint text
) returns jsonb
language plpgsql
security definer
set search_path to ''
as $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_q clube_novo.otimizador_lote_producao_linha_v3%rowtype;
  v_l clube_novo.build_linha_card%rowtype;
  v_token uuid;
begin
  if p_lote_id is null or p_worker_id is null or p_linha_id is null
     or nullif(trim(coalesce(p_card_id, '')), '') is null
     or p_funcao_id is null or p_posicao_id is null
     or nullif(trim(coalesce(p_carta_entrada_fingerprint, '')), '') is null
     or nullif(trim(coalesce(p_formula_fingerprint, '')), '') is null
     or nullif(trim(coalesce(p_contrato_fingerprint, '')), '') is null
     or nullif(trim(coalesce(p_motor_versao, '')), '') is null
     or nullif(trim(coalesce(p_lote_fingerprint, '')), '') is null then
    raise exception 'reserva local recusada: identidade e selos são obrigatórios';
  end if;

  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id
  for update;
  if not found or v_lote.tipo_lote <> 'integral' then
    raise exception 'reserva local recusada: lote integral inexistente';
  end if;
  if v_lote.formula_fingerprint <> p_formula_fingerprint
     or v_lote.contrato_fingerprint <> p_contrato_fingerprint
     or v_lote.motor_versao <> p_motor_versao
     or v_lote.fingerprint <> p_lote_fingerprint
     or v_lote.formula_fingerprint <> '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad'
     or v_lote.pode_publicar is distinct from false then
    raise exception 'reserva local recusada: selo do pacote diverge do lote';
  end if;
  if v_lote.estado <> 'rodando' then
    return jsonb_build_object(
      'contrato', 'otimizador_pacote_local_v1', 'reservada', false,
      'estado_lote', v_lote.estado, 'pode_publicar', false
    );
  end if;

  select * into v_q
  from clube_novo.otimizador_lote_producao_linha_v3
  where lote_id = p_lote_id and linha_id = p_linha_id
  for update;
  select * into v_l
  from clube_novo.build_linha_card
  where id = p_linha_id
  for update;
  if v_q.linha_id is null or v_l.id is null then
    raise exception 'reserva local recusada: linha inexistente';
  end if;
  if v_l.lote_producao_id <> p_lote_id or v_q.card_id <> v_l.card_id then
    raise exception 'reserva local recusada: vínculo canônico da linha diverge';
  end if;
  if v_l.estado_otimizador <> 'pendente' then
    return jsonb_build_object(
      'contrato', 'otimizador_pacote_local_v1', 'reservada', false,
      'estado_lote', v_lote.estado, 'linha_estado', v_l.estado_otimizador,
      'pode_publicar', false
    );
  end if;
  if v_l.card_id <> p_card_id
     or v_l.funcao_id <> p_funcao_id
     or v_l.posicao_id <> p_posicao_id
     or v_q.entrada_fingerprint <> p_carta_entrada_fingerprint
     or v_l.impeto_condicional_codigo is not null
     or v_l.impeto_condicional_nivel is not null
     or not exists (
       select 1
       from clube_novo.otimizador_lote_producao_carta_v3 s
       where s.lote_id = p_lote_id and s.card_id = v_l.card_id
         and s.entrada_fingerprint = v_q.entrada_fingerprint
         and s.entrada_otimizador is not null
     )
     or not coalesce((v_lote.regua_snapshot -> 'gate' ->> 'pode_rodar')::boolean, false) then
    raise exception 'reserva local recusada: fotografia/gates canônicos divergentes';
  end if;

  v_token := extensions.gen_random_uuid();
  update clube_novo.otimizador_lote_producao_linha_v3
  set reserva_token = v_token,
      worker_id = p_worker_id,
      reservada_em = clock_timestamp(),
      tentativas = tentativas + 1
  where lote_id = p_lote_id and linha_id = p_linha_id;
  update clube_novo.build_linha_card
  set estado_otimizador = 'processando',
      erro_otimizador = null,
      otimizador_iniciado_em = clock_timestamp(),
      atualizado_em = clock_timestamp()
  where id = p_linha_id and estado_otimizador = 'pendente';
  insert into clube_novo.otimizador_evento_producao_v3(lote_id, linha_id, evento, detalhe)
  values(
    p_lote_id, p_linha_id, 'linha_reservada',
    jsonb_build_object(
      'worker_id', p_worker_id,
      'ordem_fila', v_q.ordem_fila,
      'pacote_local_v1', true,
      'origem', 'clube_novo.otimizador_entrada_linha_v1'
    )
  );
  return jsonb_build_object(
    'contrato', 'otimizador_pacote_local_v1',
    'reservada', true,
    'lote_id', p_lote_id,
    'linha_id', p_linha_id,
    'ordem_fila', v_q.ordem_fila,
    'reserva_token', v_token,
    'card_id', v_l.card_id,
    'funcao_id', v_l.funcao_id,
    'posicao_id', v_l.posicao_id,
    'carta_entrada_fingerprint', v_q.entrada_fingerprint,
    'pode_publicar', false,
    'impetos_condicionais', 'desligados'
  );
end
$function$;

create or replace function public.otimizador_producao_concluir_lote_local_v1(
  p_lote_id uuid,
  p_resultados jsonb
) returns jsonb
language plpgsql
security definer
set search_path to ''
as $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_item jsonb;
  v_resultado jsonb;
  v_linha_id bigint;
  v_token uuid;
  v_resultado_fp text;
  v_resposta jsonb;
  v_itens jsonb := '[]'::jsonb;
  v_vistos bigint[] := '{}'::bigint[];
begin
  if p_lote_id is null or jsonb_typeof(p_resultados) <> 'array'
     or jsonb_array_length(p_resultados) not between 1 and 100 then
    raise exception 'conclusão local recusada: lote deve conter de 1 a 100 resultados';
  end if;
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id
  for update;
  if not found or v_lote.tipo_lote <> 'integral'
     or v_lote.pode_publicar is distinct from false
     or v_lote.formula_fingerprint <> '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad' then
    raise exception 'conclusão local recusada: lote/gate inválido';
  end if;

  for v_item in select value from jsonb_array_elements(p_resultados)
  loop
    if jsonb_typeof(v_item) <> 'object'
       or jsonb_typeof(v_item -> 'resultado') <> 'object'
       or nullif(v_item ->> 'linha_id', '') is null
       or nullif(v_item ->> 'reserva_token', '') is null then
      raise exception 'conclusão local recusada: item de lote inválido';
    end if;
    v_linha_id := (v_item ->> 'linha_id')::bigint;
    v_token := (v_item ->> 'reserva_token')::uuid;
    v_resultado := v_item -> 'resultado';
    if v_linha_id = any(v_vistos) then
      raise exception 'conclusão local recusada: linha repetida no mesmo lote';
    end if;
    v_vistos := array_append(v_vistos, v_linha_id);
    v_resultado_fp := encode(extensions.digest(convert_to(v_resultado::text, 'UTF8'), 'sha256'), 'hex');

    -- Repetir um POST depois de timeout é seguro apenas quando o banco prova
    -- que já gravou exatamente o mesmo resultado para a mesma linha.
    if exists (
      select 1
      from clube_novo.otimizador_lote_producao_linha_v3 q
      join clube_novo.build_linha_card l on l.id = q.linha_id
      where q.lote_id = p_lote_id and q.linha_id = v_linha_id
        and l.estado_otimizador = 'concluido'
        and q.resultado_fingerprint = v_resultado_fp
    ) then
      v_itens := v_itens || jsonb_build_array(jsonb_build_object(
        'linha_id', v_linha_id, 'confirmada', true, 'idempotente', true
      ));
      continue;
    end if;

    v_resposta := public.otimizador_producao_concluir_linha_v6(
      p_lote_id, v_linha_id, v_token, v_resultado
    );
    if v_resposta ->> 'contrato' is distinct from 'otimizador_fila_producao_v3'
       or (v_resposta ->> 'pode_publicar')::boolean is distinct from false then
      raise exception 'conclusão local recusada: subcontrato não confirmou a linha';
    end if;
    v_itens := v_itens || jsonb_build_array(jsonb_build_object(
      'linha_id', v_linha_id,
      'confirmada', true,
      'idempotente', false,
      'build_otimizador_id', v_resposta -> 'build_otimizador_id'
    ));
  end loop;

  return jsonb_build_object(
    'contrato', 'otimizador_pacote_local_v1',
    'lote_id', p_lote_id,
    'itens', v_itens,
    'pode_publicar', false,
    'impetos_condicionais', 'desligados'
  );
end
$function$;

-- O portal V7 é uma camada estreita adicional. Ele não aceita SQL, nomes de
-- tabela ou qualquer operação fora da allowlist; o V6 continua intacto para
-- quem ainda não tem este pacote instalado.
create or replace function public.otimizador_portal_local_v7(
  p_operacao text,
  p_corpo jsonb default '{}'::jsonb
) returns jsonb
language plpgsql
security definer
set search_path to ''
as $function$
begin
  if p_operacao = 'otimizador_producao_pacote_local_manifesto_v1' then
    return public.otimizador_producao_pacote_local_manifesto_v1((p_corpo ->> 'p_lote_id')::uuid);
  end if;
  if p_operacao = 'otimizador_producao_pacote_local_cartas_v1' then
    return public.otimizador_producao_pacote_local_cartas_v1(
      (p_corpo ->> 'p_lote_id')::uuid,
      (p_corpo ->> 'p_offset')::integer,
      (p_corpo ->> 'p_limite')::integer
    );
  end if;
  if p_operacao = 'otimizador_producao_pacote_local_linhas_v1' then
    return public.otimizador_producao_pacote_local_linhas_v1(
      (p_corpo ->> 'p_lote_id')::uuid,
      (p_corpo ->> 'p_offset')::integer,
      (p_corpo ->> 'p_limite')::integer
    );
  end if;
  if p_operacao = 'otimizador_producao_reservar_linha_local_v1' then
    return public.otimizador_producao_reservar_linha_local_v1(
      (p_corpo ->> 'p_lote_id')::uuid,
      (p_corpo ->> 'p_worker_id')::uuid,
      (p_corpo ->> 'p_linha_id')::bigint,
      p_corpo ->> 'p_card_id',
      (p_corpo ->> 'p_funcao_id')::bigint,
      (p_corpo ->> 'p_posicao_id')::integer,
      p_corpo ->> 'p_carta_entrada_fingerprint',
      p_corpo ->> 'p_formula_fingerprint',
      p_corpo ->> 'p_contrato_fingerprint',
      p_corpo ->> 'p_motor_versao',
      p_corpo ->> 'p_lote_fingerprint'
    );
  end if;
  if p_operacao = 'otimizador_producao_concluir_lote_local_v1' then
    return public.otimizador_producao_concluir_lote_local_v1(
      (p_corpo ->> 'p_lote_id')::uuid,
      p_corpo -> 'p_resultados'
    );
  end if;
  return public.otimizador_portal_local_v6(p_operacao, p_corpo);
end
$function$;

revoke all on function public.otimizador_producao_pacote_local_manifesto_v1(uuid)
  from public, anon, authenticated;
revoke all on function public.otimizador_producao_pacote_local_cartas_v1(uuid, integer, integer)
  from public, anon, authenticated;
revoke all on function public.otimizador_producao_pacote_local_linhas_v1(uuid, integer, integer)
  from public, anon, authenticated;
revoke all on function public.otimizador_producao_reservar_linha_local_v1(uuid, uuid, bigint, text, bigint, integer, text, text, text, text, text)
  from public, anon, authenticated;
revoke all on function public.otimizador_producao_concluir_lote_local_v1(uuid, jsonb)
  from public, anon, authenticated;
revoke all on function public.otimizador_portal_local_v7(text, jsonb)
  from public, anon, authenticated;

grant execute on function public.otimizador_producao_pacote_local_manifesto_v1(uuid)
  to service_role;
grant execute on function public.otimizador_producao_pacote_local_cartas_v1(uuid, integer, integer)
  to service_role;
grant execute on function public.otimizador_producao_pacote_local_linhas_v1(uuid, integer, integer)
  to service_role;
grant execute on function public.otimizador_producao_reservar_linha_local_v1(uuid, uuid, bigint, text, bigint, integer, text, text, text, text, text)
  to service_role;
grant execute on function public.otimizador_producao_concluir_lote_local_v1(uuid, jsonb)
  to service_role;
grant execute on function public.otimizador_portal_local_v7(text, jsonb)
  to bonificador_runtime;

comment on function public.otimizador_producao_pacote_local_manifesto_v1(uuid) is
  'V50: manifesto privado de pacote local portátil, selado e sem publicação.';
comment on function public.otimizador_producao_reservar_linha_local_v1(uuid, uuid, bigint, text, bigint, integer, text, text, text, text, text) is
  'V50: reserva atômica de linha já fotografada no pacote local por IDs e fingerprints canônicos.';
comment on function public.otimizador_producao_concluir_lote_local_v1(uuid, jsonb) is
  'V50: confirma de 1 a 100 resultados locais por chamada, idempotente pelo fingerprint persistido.';
comment on function public.otimizador_portal_local_v7(text, jsonb) is
  'V50: allowlist privada do pacote local; encaminha os demais contratos ao portal V6.';

notify pgrst, 'reload schema';

commit;
