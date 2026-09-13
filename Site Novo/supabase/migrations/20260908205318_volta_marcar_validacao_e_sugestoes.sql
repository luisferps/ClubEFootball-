-- Decisao 08/09/2026: restricao adicional; nativas e historico preservados.
insert into clube_novo.habilidade_funcao_bloqueio_otimizador(skill_id,funcao_id,origem)
select 56,f,'Decisao Luis 2026-09-08: Volta para marcar adicional'
from unnest(array[1,2,6,7,10,11,16,17,18,19]::bigint[]) f
on conflict (skill_id,funcao_id) do nothing;
CREATE OR REPLACE FUNCTION public.otimizador_producao_importar_json_local_v1(p_lote_id uuid, p_linha_id bigint, p_resultado jsonb, p_calculado_em_utc timestamp with time zone)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_q clube_novo.otimizador_lote_producao_linha_v3%rowtype;
  v_l clube_novo.build_linha_card%rowtype;
  v_habilidades integer[];
  v_resultado_fp text;
  v_build_id bigint;
  v_enviado_em timestamptz;
  v_vals jsonb;
  v_vals_int jsonb;
  v_arows jsonb;
  v_impeto integer;
  v_cond_codigo integer;
  v_cond_nivel integer;
  v_completou boolean := false;
  v_lote_fingerprint_recebido text;
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
  if p_resultado->>'card_id' is distinct from v_l.card_id
     or (p_resultado->>'funcao_id')::bigint is distinct from v_l.funcao_id
     or (p_resultado->>'posicao_id')::integer is distinct from v_l.posicao_id then
    raise exception 'importação JSON recusada: identidade da linha diverge';
  end if;

  if v_l.otimizador_formula_fingerprint_esperado is null
     or v_l.otimizador_contrato_fingerprint_esperado is null
     or v_l.otimizador_motor_versao_esperada is null
     or v_q.entrada_fingerprint is null then
    raise exception 'importação JSON recusada: linha sem selos esperados completos';
  end if;

  if p_resultado->>'formula_fingerprint' is distinct from v_l.otimizador_formula_fingerprint_esperado
     or p_resultado->>'contrato_fingerprint' is distinct from v_l.otimizador_contrato_fingerprint_esperado
     or p_resultado->>'motor_versao' is distinct from v_l.otimizador_motor_versao_esperada
     or p_resultado->>'carta_entrada_fingerprint' is distinct from v_q.entrada_fingerprint then
    raise exception 'importação JSON recusada: selo da linha divergente';
  end if;

  v_lote_fingerprint_recebido := p_resultado->>'lote_fingerprint';
  if v_lote_fingerprint_recebido is null
     or v_lote_fingerprint_recebido !~ '^[0-9a-f]{64}$' then
    raise exception 'importação JSON recusada: fingerprint do lote ausente ou inválido';
  end if;

  -- O fingerprint acima registra a procedência declarada pelo pacote e fica no
  -- fingerprint integral do resultado. A integridade canônica é conferida pelos
  -- selos imutáveis da linha. O agregado do lote muda quando a fila recebe cartas
  -- novas e seus valores antigos não foram todos preservados no banco.

  v_cond_codigo := nullif(p_resultado->>'impeto_condicional_codigo', '')::integer;
  v_cond_nivel := nullif(p_resultado->>'impeto_condicional_nivel', '')::integer;

  if v_cond_codigo is distinct from v_l.impeto_condicional_codigo
     or v_cond_nivel is distinct from v_l.impeto_condicional_nivel then
    raise exception
      'importação JSON recusada: o degrau do Ímpeto condicional não é o desta linha (linha: % / %, resultado: % / %)',
      v_l.impeto_condicional_codigo, v_l.impeto_condicional_nivel,
      v_cond_codigo, v_cond_nivel;
  end if;
  if (v_cond_codigo is null) <> (v_cond_nivel is null) then
    raise exception 'importação JSON recusada: Ímpeto condicional pela metade (código sem nível, ou o contrário)';
  end if;
  if v_cond_nivel is not null and v_cond_nivel not between 1 and 3 then
    raise exception 'importação JSON recusada: degrau % fora de 1..3', v_cond_nivel;
  end if;

  if not (p_resultado ?& array[
    'b1', 'barras', 'tecnico_id', 'habilidades', 'builds_comparadas', 'builds_possiveis'
  ]) then
    raise exception 'importação JSON recusada: resultado incompleto';
  end if;
  if jsonb_typeof(p_resultado->'barras') <> 'object'
     or jsonb_typeof(p_resultado->'habilidades') <> 'array' then
    raise exception 'importação JSON recusada: build inválida';
  end if;

  v_impeto := nullif(p_resultado->>'impeto_adicional_codigo', '')::integer;
  perform clube_novo.conferir_impeto_x_posicao_v1(v_impeto, v_l.posicao_id);

  begin
    v_vals := case
      when jsonb_typeof(p_resultado->'vals_tela') = 'array'
       and jsonb_array_length(p_resultado->'vals_tela') = 26
      then p_resultado->'vals_tela'
    end;
  exception when others then
    v_vals := null;
  end;
  begin
    v_vals_int := case
      when jsonb_typeof(p_resultado->'vals') = 'array'
       and jsonb_array_length(p_resultado->'vals') = 26
      then p_resultado->'vals'
    end;
  exception when others then
    v_vals_int := null;
  end;
  begin
    v_arows := clube_novo.arows_da_cadeia_v1(p_resultado->'cadeia');
  exception when others then
    v_arows := null;
  end;

  select coalesce(array_agg(x.valor::integer order by x.ordem), '{}'::integer[])
    into v_habilidades
    from jsonb_array_elements_text(p_resultado->'habilidades')
      with ordinality x(valor, ordem);

  v_resultado_fp := encode(
    extensions.digest(convert_to(p_resultado::text, 'UTF8'), 'sha256'),
    'hex'
  );

  -- Uma resposta perdida depois do commit continua idempotente mesmo se o
  -- lote agregado tiver recebido outras cartas desde o primeiro envio.
  if v_l.estado_otimizador = 'concluido' then
    if v_l.build_otimizador_id is not null
       and v_q.resultado_fingerprint = v_resultado_fp then
      v_enviado_em := coalesce(v_q.finalizada_em, v_l.otimizador_finalizado_em);
      if v_enviado_em is null then
        raise exception 'importação JSON recusada: linha concluída sem carimbo de envio';
      end if;
      if v_vals is not null or v_vals_int is not null or v_arows is not null then
        update clube_novo.build_otimizador b
           set atributos_finais = coalesce(b.atributos_finais, v_vals),
               atributos_internos = coalesce(b.atributos_internos, v_vals_int),
               arows_snapshot = coalesce(b.arows_snapshot, v_arows)
         where b.id = v_l.build_otimizador_id
           and (
             b.atributos_finais is null
             or b.atributos_internos is null
             or b.arows_snapshot is null
           );
        v_completou := found;
      end if;
      return jsonb_build_object(
        'contrato', 'otimizador_importacao_json_local_v1',
        'linha_id', p_linha_id,
        'build_otimizador_id', v_l.build_otimizador_id,
        'resultado_fingerprint', v_resultado_fp,
        'lote_fingerprint_recebido', v_lote_fingerprint_recebido,
        'calculado_em_utc', p_calculado_em_utc,
        'enviado_em_utc', v_enviado_em,
        'idempotente', true,
        'numeros_completados', v_completou,
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

  -- Regra vigente para novas gravacoes; recibos historicos seguem idempotentes.
  if exists (
    select 1 from clube_novo.habilidade_funcao_bloqueio_otimizador bq
    where bq.funcao_id = v_l.funcao_id and bq.skill_id = any(v_habilidades)
  ) then
    raise exception 'importação JSON recusada: habilidade adicional proibida nesta especialidade; atualize o pacote e recalcule a linha';
  end if;

  v_enviado_em := clock_timestamp();

  insert into clube_novo.build_otimizador(
    tecnico_id,
    barras,
    impeto_adicional_codigo,
    habilidades_adicionais,
    pontuacao,
    contrato_versao,
    contrato_fingerprint,
    carta_versao,
    carta_fingerprint,
    formula_fingerprint,
    resultado_fingerprint,
    motor_versao,
    builds_comparadas,
    builds_possiveis,
    atributos_finais,
    atributos_internos,
    arows_snapshot
  ) values (
    (p_resultado->>'tecnico_id')::bigint,
    p_resultado->'barras',
    v_impeto,
    v_habilidades,
    (p_resultado->>'b1')::numeric,
    'otimizador_regua_v2',
    v_l.otimizador_contrato_fingerprint_esperado,
    v_l.carta_versao,
    v_l.carta_fingerprint,
    v_l.otimizador_formula_fingerprint_esperado,
    v_resultado_fp,
    v_l.otimizador_motor_versao_esperada,
    (p_resultado->>'builds_comparadas')::integer,
    (p_resultado->>'builds_possiveis')::numeric,
    v_vals,
    v_vals_int,
    v_arows
  ) returning id into v_build_id;

  update clube_novo.build_linha_card
     set build_otimizador_id = v_build_id,
         estado_otimizador = 'concluido',
         erro_otimizador = null,
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

  insert into clube_novo.otimizador_evento_producao_v3(
    lote_id,
    linha_id,
    evento,
    detalhe
  ) values (
    p_lote_id,
    p_linha_id,
    'linha_importada_json_local',
    jsonb_build_object(
      'contrato', 'otimizador_importacao_json_local_v1',
      'build_otimizador_id', v_build_id,
      'resultado_fingerprint', v_resultado_fp,
      'lote_fingerprint_recebido', v_lote_fingerprint_recebido,
      'calculado_em_utc', p_calculado_em_utc,
      'enviado_em_utc', v_enviado_em,
      'atributos_finais', v_vals is not null,
      'atributos_internos', v_vals_int is not null,
      'arows_snapshot', v_arows is not null,
      'impeto_x_posicao_conferido', true,
      'impeto_condicional_codigo', v_cond_codigo,
      'impeto_condicional_nivel', v_cond_nivel,
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
        jsonb_build_object(
          'origem', 'operacao_local_json_v1',
          'enviado_em_utc', v_enviado_em
        )
      );
    end if;
  end if;

  return jsonb_build_object(
    'contrato', 'otimizador_importacao_json_local_v1',
    'linha_id', p_linha_id,
    'build_otimizador_id', v_build_id,
    'resultado_fingerprint', v_resultado_fp,
    'lote_fingerprint_recebido', v_lote_fingerprint_recebido,
    'calculado_em_utc', p_calculado_em_utc,
    'enviado_em_utc', v_enviado_em,
    'idempotente', false,
    'numeros_completados', false,
    'impeto_condicional_nivel', v_cond_nivel,
    'bonificador', 'pendente',
    'pode_publicar', false
  );
end
$function$
;

CREATE OR REPLACE FUNCTION clube_novo.site_novo_ficha_sugestoes_v1(p_card_id text, p_linha_id bigint)
 RETURNS jsonb
 LANGUAGE sql
 STABLE
 SET search_path TO ''
AS $function$
with contexto as materialized (
  select a.linha_id, a.card_id, a.funcao_id, b.tecnico_id,
         b.habilidades_adicionais, b.arows_snapshot, l.regua_snapshot as regua
  from clube_novo.build_publicacao_linha_ativa_v1 a
  join clube_novo.build_otimizador b on b.id = a.build_otimizador_id
  join clube_novo.otimizador_lote_producao_linha_v3 pl
    on pl.linha_id = a.linha_id and pl.resultado_fingerprint = b.resultado_fingerprint
  join clube_novo.otimizador_lote_producao_v3 l on l.id = pl.lote_id
  where a.card_id = p_card_id and a.linha_id = p_linha_id
), multiplicadores as materialized (
  select regua->'multiplicadores' as valores from contexto
), habilidades as materialized (
  select (h.item->>'skill_id')::integer as id, h.item,
    (select jsonb_agg(e.item order by e.item->>'codigo_atributo')
     from jsonb_array_elements(h.item->'efeitos') e(item)) as efeitos
  from contexto c cross join lateral jsonb_array_elements(c.regua->'habilidades') h(item)
), bloqueios as materialized (
  select (b.item->>'skill_id')::integer as id
  from contexto c cross join lateral jsonb_array_elements(c.regua->'bloqueios') b(item)
  where (b.item->>'funcao_id')::bigint = c.funcao_id
  union
  select b.skill_id from contexto c
  join clube_novo.habilidade_funcao_bloqueio_otimizador b on b.funcao_id=c.funcao_id
), incidencias as materialized (
  select (i.item->>'skill_id')::integer as id, (i.item->>'incidencia_pct')::numeric as pct
  from contexto c cross join lateral jsonb_array_elements(c.regua->'incidencias') i(item)
  where (i.item->>'funcao_id')::bigint = c.funcao_id
), pares as (
  select distinta.id, hg.nome_pt as nome, hg.ordem,
         coalesce(i.pct, 0) as incidencia,
         escolhida.skill_id as substitui_id, origem.nome_pt as substitui_nome,
         escolhida.ordem as ordem_escolhida
  from contexto c
  cross join lateral unnest(c.habilidades_adicionais) with ordinality escolhida(skill_id, ordem)
  join clube_novo.habilidade_jogo origem on origem.skill_id = escolhida.skill_id
  join habilidades atual on atual.id = escolhida.skill_id
  join habilidades distinta on distinta.id = any(origem.gemeas)
    and distinta.efeitos = atual.efeitos
    and distinta.item->>'tipo' = atual.item->>'tipo'
  join clube_novo.habilidade_jogo hg on hg.skill_id = distinta.id
  left join incidencias i on i.id = distinta.id
  where atual.item->>'fabricavel' = 'true'
    and distinta.item->>'fabricavel' = 'true'
    and distinta.item->>'pode_rodar' = 'true'
    and distinta.item->>'vetada' = 'false'
    and not (distinta.id = any(c.habilidades_adicionais))
    and not exists (select 1 from clube_novo.carta_habilidade_jogo n where n.card_id=c.card_id and n.skill_id=distinta.id)
    and not exists (select 1 from bloqueios v where v.id=distinta.id)
), gemeas as (
  select id,nome,ordem,incidencia,
    jsonb_agg(jsonb_build_object('id',substitui_id,'nome',substitui_nome) order by ordem_escolhida) as substitui
  from pares group by id,nome,ordem,incidencia
), pesos as materialized (
  select (p.item->>0)::integer as indice
  from contexto c cross join lateral jsonb_array_elements(c.arows_snapshot) p(item)
  where jsonb_array_length(c.arows_snapshot)=26 and (p.item->>1)::numeric <> 0
), catalogo_tecnicos as materialized (
  select (t.item->>'tecnico_id')::bigint as id, t.item,
         m.valores->(t.item->>'proficiencia_maxima') as multiplicador
  from contexto c cross join multiplicadores m
  cross join lateral jsonb_array_elements(c.regua->'tecnicos') t(item)
), tecnicos as materialized (
  select t.id, t.item, t.multiplicador,
         (select coalesce(jsonb_agg(jsonb_build_object('indice', (b.item->>'indice_otimizador')::integer,
                    'delta', (b.item->>'delta')::numeric) order by (b.item->>'indice_otimizador')::integer), '[]'::jsonb)
          from jsonb_array_elements(t.item->'boosts') b(item)
          join pesos p on p.indice=(b.item->>'indice_otimizador')::integer) as efeitos
  from contexto c
  join catalogo_tecnicos escolhido on escolhido.id=c.tecnico_id
  join catalogo_tecnicos t on t.multiplicador=escolhido.multiplicador
  where exists (select 1 from pesos)
), equivalentes as (
  select t.id,j.nome_en as nome,
    (select jsonb_agg(jsonb_build_object('codigo',e.item->>'codigo_estilo','nome',ej.nome_pt,
                          'proficiencia',(e.item->>'valor')::integer) order by ej.ordem)
     from jsonb_array_elements(t.item->'estilos_principais') e(item)
     join clube_novo.estilo_jogo_tecnico ej on ej.codigo=e.item->>'codigo_estilo') as estilos,
    (select coalesce(jsonb_agg(jsonb_build_object(
       'codigo_atributo',ta.codigo_atributo,'nome',aj.nome_pt,'delta',ta.delta
     ) order by ta.ordem),'[]'::jsonb)
     from clube_novo.tecnico_atributo_jogo ta
     join clube_novo.atributo_jogo aj on aj.codigo=ta.codigo_atributo
     where ta.tecnico_id=t.id) as atributos
  from contexto c join tecnicos escolhido on escolhido.id=c.tecnico_id
  join tecnicos t on t.id <> escolhido.id and t.multiplicador=escolhido.multiplicador and t.efeitos=escolhido.efeitos
  join clube_novo.tecnico_jogo j on j.id=t.id
  where jsonb_typeof(t.multiplicador)='number'
)
select jsonb_build_object(
  'estado', case when exists (select 1 from contexto) then 'pronto' else 'nao_publicado' end,
  'habilidades', coalesce((select jsonb_agg(jsonb_build_object('id',id,'nome',nome,'substitui',substitui)
                         order by incidencia desc,ordem,id) from gemeas), '[]'::jsonb),
  'tecnicos', coalesce((select jsonb_agg(jsonb_build_object('id',id,'nome',nome,'estilos',estilos,'atributos',atributos) order by nome,id)
                      from equivalentes), '[]'::jsonb)
);
$function$
;
