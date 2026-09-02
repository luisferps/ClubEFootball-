-- Operação local em JSON V65.
--
-- O cálculo ocorre offline, usando a fotografia selada. Esta porta recebe
-- somente um resultado já calculado, confirma uma linha por chamada e deixa
-- explícitos os dois tempos: cálculo local e envio confirmado pelo banco.
--
-- Não reserva linha, não inicia esteira, não publica Build e não toca tabela
-- legada. Ela só aceita lote integral pausado e uma linha ainda pendente.

begin;

do $$
begin
  if to_regclass('clube_novo.otimizador_lote_producao_v3') is null
     or to_regclass('clube_novo.otimizador_lote_producao_linha_v3') is null
     or to_regclass('clube_novo.build_linha_card') is null
     or to_regclass('clube_novo.build_otimizador') is null
     or to_regclass('clube_novo.otimizador_evento_producao_v3') is null
     or to_regprocedure('clube_novo.aplicar_delta_status_lote_otimizador_v2(uuid,integer,integer,integer,integer,integer,integer)') is null then
    raise exception 'V65 recusada: contratos da fila produtiva V3/V19 ausentes';
  end if;
end
$$;

create or replace function public.otimizador_producao_importar_json_local_v1(
  p_lote_id uuid,
  p_linha_id bigint,
  p_resultado jsonb,
  p_calculado_em_utc timestamptz
) returns jsonb
language plpgsql
security definer
set search_path to ''
as $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_q clube_novo.otimizador_lote_producao_linha_v3%rowtype;
  v_l clube_novo.build_linha_card%rowtype;
  v_habilidades integer[];
  v_resultado_fp text;
  v_build_id bigint;
  v_enviado_em timestamptz;
begin
  if p_lote_id is null or p_linha_id is null then
    raise exception 'importação JSON recusada: lote e linha são obrigatórios';
  end if;
  if p_calculado_em_utc is null then
    raise exception 'importação JSON recusada: data/hora de cálculo ausente';
  end if;
  if jsonb_typeof(p_resultado) <> 'object' then
    raise exception 'importação JSON recusada: resultado deve ser objeto';
  end if;

  -- A mesma ordem de lock da conclusão V6 evita inversão com qualquer rotina
  -- de recuperação que ainda esteja apenas preservada no legado.
  select * into v_lote
    from clube_novo.otimizador_lote_producao_v3
   where id = p_lote_id
   for update;
  select * into v_q
    from clube_novo.otimizador_lote_producao_linha_v3
   where lote_id = p_lote_id
     and linha_id = p_linha_id
   for update;
  select * into v_l
    from clube_novo.build_linha_card
   where id = p_linha_id
   for update;

  if v_lote.id is null
     or v_lote.tipo_lote <> 'integral'
     or v_lote.pode_publicar is not false
     or v_q.linha_id is null
     or v_l.id is null
     or v_l.lote_producao_id is distinct from p_lote_id then
    raise exception 'importação JSON recusada: lote ou linha não pertence à fila integral';
  end if;
  if p_resultado->>'card_id' <> v_l.card_id
     or (p_resultado->>'funcao_id')::bigint <> v_l.funcao_id
     or (p_resultado->>'posicao_id')::integer <> v_l.posicao_id then
    raise exception 'importação JSON recusada: identidade da linha diverge';
  end if;
  if p_resultado->>'formula_fingerprint' <> v_lote.formula_fingerprint
     or p_resultado->>'contrato_fingerprint' <> v_lote.contrato_fingerprint
     or p_resultado->>'motor_versao' <> v_lote.motor_versao
     or p_resultado->>'lote_fingerprint' <> v_lote.fingerprint
     or p_resultado->>'carta_entrada_fingerprint' <> v_q.entrada_fingerprint then
    raise exception 'importação JSON recusada: selo divergente';
  end if;
  if coalesce(p_resultado->>'impeto_condicional_codigo', '') <> ''
     or coalesce(p_resultado->>'impeto_condicional_nivel', '') <> '' then
    raise exception 'importação JSON recusada: Ímpeto condicional continua desligado';
  end if;
  if not (p_resultado ?& array['b1', 'barras', 'tecnico_id', 'habilidades', 'builds_comparadas', 'builds_possiveis']) then
    raise exception 'importação JSON recusada: resultado incompleto';
  end if;
  if jsonb_typeof(p_resultado->'barras') <> 'object'
     or jsonb_typeof(p_resultado->'habilidades') <> 'array' then
    raise exception 'importação JSON recusada: build inválida';
  end if;

  select coalesce(array_agg(x.valor::integer order by x.ordem), '{}'::integer[])
    into v_habilidades
    from jsonb_array_elements_text(p_resultado->'habilidades') with ordinality x(valor, ordem);

  v_resultado_fp := encode(
    extensions.digest(convert_to(p_resultado::text, 'UTF8'), 'sha256'),
    'hex'
  );

  -- Uma resposta perdida depois do commit não duplica Build: o segundo envio
  -- recebe a mesma confirmação, com a hora original do banco.
  if v_l.estado_otimizador = 'concluido' then
    if v_l.build_otimizador_id is not null
       and v_q.resultado_fingerprint = v_resultado_fp then
      v_enviado_em := coalesce(v_q.finalizada_em, v_l.otimizador_finalizado_em);
      if v_enviado_em is null then
        raise exception 'importação JSON recusada: linha concluída sem carimbo de envio';
      end if;
      return jsonb_build_object(
        'contrato', 'otimizador_importacao_json_local_v1',
        'linha_id', p_linha_id,
        'build_otimizador_id', v_l.build_otimizador_id,
        'resultado_fingerprint', v_resultado_fp,
        'calculado_em_utc', p_calculado_em_utc,
        'enviado_em_utc', v_enviado_em,
        'idempotente', true,
        'bonificador', 'pendente',
        'pode_publicar', false
      );
    end if;
    raise exception 'importação JSON recusada: linha concluída com resultado diferente';
  end if;

  if v_lote.estado <> 'pausado' then
    raise exception 'importação JSON recusada: o lote precisa estar pausado';
  end if;
  if v_l.estado_otimizador <> 'pendente'
     or v_q.reserva_token is not null
     or v_q.worker_id is not null then
    raise exception 'importação JSON recusada: a linha não está livre para envio local';
  end if;

  v_enviado_em := clock_timestamp();

  insert into clube_novo.build_otimizador(
    tecnico_id, barras, impeto_adicional_codigo, habilidades_adicionais, pontuacao,
    contrato_versao, contrato_fingerprint, carta_versao, carta_fingerprint,
    formula_fingerprint, resultado_fingerprint, motor_versao, builds_comparadas, builds_possiveis
  ) values (
    (p_resultado->>'tecnico_id')::bigint,
    p_resultado->'barras',
    nullif(p_resultado->>'impeto_adicional_codigo', '')::integer,
    v_habilidades,
    (p_resultado->>'b1')::numeric,
    'otimizador_regua_v2',
    v_lote.contrato_fingerprint,
    v_l.carta_versao,
    v_l.carta_fingerprint,
    v_lote.formula_fingerprint,
    v_resultado_fp,
    v_lote.motor_versao,
    (p_resultado->>'builds_comparadas')::integer,
    (p_resultado->>'builds_possiveis')::numeric
  ) returning id into v_build_id;

  update clube_novo.build_linha_card
     set build_otimizador_id = v_build_id,
         estado_otimizador = 'concluido',
         erro_otimizador = null,
         -- Esta é a hora de confirmação do envio, não uma estimativa local.
         otimizador_finalizado_em = v_enviado_em,
         pendencias = '{}'::text[],
         atualizado_em = v_enviado_em
   where id = p_linha_id
     and estado_otimizador = 'pendente';
  if not found then
    raise exception 'importação JSON recusada: a linha mudou durante o envio';
  end if;

  update clube_novo.otimizador_lote_producao_linha_v3
     set reserva_token = null,
         worker_id = null,
         reservada_em = null,
         finalizada_em = v_enviado_em,
         resultado_fingerprint = v_resultado_fp
   where lote_id = p_lote_id
     and linha_id = p_linha_id;

  insert into clube_novo.otimizador_evento_producao_v3(lote_id, linha_id, evento, detalhe)
  values (
    p_lote_id,
    p_linha_id,
    'linha_importada_json_local',
    jsonb_build_object(
      'contrato', 'otimizador_importacao_json_local_v1',
      'build_otimizador_id', v_build_id,
      'resultado_fingerprint', v_resultado_fp,
      'calculado_em_utc', p_calculado_em_utc,
      'enviado_em_utc', v_enviado_em,
      'bonificador', 'pendente',
      'pode_publicar', false
    )
  );

  if v_lote.preparo_concluido >= v_lote.preparo_total
     and not exists (
       select 1
         from clube_novo.otimizador_lote_producao_linha_v3 q2
         join clube_novo.build_linha_card l2 on l2.id = q2.linha_id
        where q2.lote_id = p_lote_id
          and l2.estado_otimizador in ('pendente', 'processando')
     ) then
    update clube_novo.otimizador_lote_producao_v3
       set estado = 'concluido',
           finalizado_em = v_enviado_em,
           atualizado_em = v_enviado_em
     where id = p_lote_id
       and estado = 'pausado';
    if found then
      insert into clube_novo.otimizador_evento_producao_v3(lote_id, evento, detalhe)
      values (
        p_lote_id,
        'lote_concluido',
        jsonb_build_object('origem', 'operacao_local_json_v1', 'enviado_em_utc', v_enviado_em)
      );
    end if;
  end if;

  return jsonb_build_object(
    'contrato', 'otimizador_importacao_json_local_v1',
    'linha_id', p_linha_id,
    'build_otimizador_id', v_build_id,
    'resultado_fingerprint', v_resultado_fp,
    'calculado_em_utc', p_calculado_em_utc,
    'enviado_em_utc', v_enviado_em,
    'idempotente', false,
    'bonificador', 'pendente',
    'pode_publicar', false
  );
end
$function$;

revoke all on function public.otimizador_producao_importar_json_local_v1(uuid,bigint,jsonb,timestamptz)
  from public, anon, authenticated;
grant execute on function public.otimizador_producao_importar_json_local_v1(uuid,bigint,jsonb,timestamptz)
  to service_role;

comment on function public.otimizador_producao_importar_json_local_v1(uuid,bigint,jsonb,timestamptz) is
  'V65: confirma uma saída local JSON por linha. Exige lote integral pausado, mantém idempotência por fingerprint e registra cálculo local + envio confirmado.';

notify pgrst, 'reload schema';

commit;
