-- Bonificador e Otimizador persistem de forma independente.
-- A normalizacao/publicacao acontece somente quando os dois resultados compativeis existem.
-- Revisao de orcamento troca apenas a entrada do Otimizador: o Bonificador V10 e reaproveitado
-- quando card, funcao, posicao, versao, fingerprint e formula permanecem identicos.

begin;

set local lock_timeout = '5s';
set local statement_timeout = '120s';

create or replace function clube_novo.vincular_bonificador_v10_independente_v1(
  p_linha_destino_id bigint,
  p_linha_fonte_id bigint,
  p_build_bonificador_id bigint,
  p_origem text default 'desconhecida'
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_destino clube_novo.build_linha_card%rowtype;
  v_fonte clube_novo.build_linha_card%rowtype;
  v_bonus clube_novo.build_bonificador%rowtype;
  v_bonus_atual clube_novo.build_bonificador%rowtype;
  v_bonus_destino_id bigint;
  v_resultado_fingerprint text;
  v_anterior_guard text;
  v_clonado boolean := false;
  v_vinculado boolean := false;
  v_finalizacao jsonb;
begin
  if p_linha_destino_id is null
     or p_linha_fonte_id is null
     or p_build_bonificador_id is null then
    raise exception 'vinculo Bonificador V10: linha destino, linha fonte e resultado sao obrigatorios';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('bonificador-v10-linha:' || p_linha_destino_id::text, 0)
  );

  -- Ordem deterministica evita deadlock se duas revisoes forem tratadas simultaneamente.
  perform 1
  from clube_novo.build_linha_card l
  where l.id in (p_linha_destino_id, p_linha_fonte_id)
  order by l.id
  for update;

  select * into v_destino
  from clube_novo.build_linha_card
  where id = p_linha_destino_id;

  select * into v_fonte
  from clube_novo.build_linha_card
  where id = p_linha_fonte_id;

  select * into v_bonus
  from clube_novo.build_bonificador
  where id = p_build_bonificador_id;

  if v_destino.id is null or v_fonte.id is null or v_bonus.id is null then
    raise exception 'vinculo Bonificador V10: linha ou resultado inexistente';
  end if;

  if v_destino.execucao_tipo <> 'producao'
     or v_destino.lote_teste_id is not null
     or v_destino.estado = 'invalida' then
    raise exception 'vinculo Bonificador V10: linha destino nao e produtiva ativa';
  end if;

  if v_destino.card_id is distinct from v_fonte.card_id
     or v_destino.funcao_id is distinct from v_fonte.funcao_id
     or v_destino.posicao_id is distinct from v_fonte.posicao_id
     or v_destino.impeto_condicional_codigo is distinct from v_fonte.impeto_condicional_codigo
     or v_destino.impeto_condicional_nivel is distinct from v_fonte.impeto_condicional_nivel then
    raise exception 'vinculo Bonificador V10: identidade da linha substituta diverge da origem';
  end if;

  if v_destino.carta_versao is distinct from v_fonte.carta_versao
     or v_destino.carta_fingerprint is distinct from v_fonte.carta_fingerprint then
    raise exception 'vinculo Bonificador V10: versao ou fingerprint mudou; recalculo e obrigatorio';
  end if;

  if v_fonte.build_bonificador_id is distinct from v_bonus.id
     and not exists (
       select 1
       from clube_novo.bonificador_correcao_item_v1 i
       where i.build_linha_card_id = v_fonte.id
         and i.estado_item = 'preparado'
         and i.build_bonificador_id_novo = v_bonus.id
     ) then
    raise exception 'vinculo Bonificador V10: resultado nao pertence a linha fonte';
  end if;

  if v_bonus.motor_versao <> 'v10-0409-fisico-regra-aprovada-v1'
     or v_bonus.formula_fingerprint <> '756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
     or v_bonus.contrato_versao <> 'bonificador-regua-v3'
     or v_bonus.carta_versao is distinct from v_destino.carta_versao
     or v_bonus.carta_fingerprint is distinct from v_destino.carta_fingerprint
     or v_bonus.entrada_bonificador_fingerprint is distinct from v_destino.carta_fingerprint
     or cardinality(v_bonus.faltou) <> 0 then
    raise exception 'vinculo Bonificador V10: resultado sem selo ou entrada compativel';
  end if;

  if p_linha_destino_id = p_linha_fonte_id then
    v_bonus_destino_id := v_bonus.id;
    v_resultado_fingerprint := v_bonus.resultado_fingerprint;
  else
    v_resultado_fingerprint := pg_catalog.encode(
      extensions.digest(
        pg_catalog.convert_to(
          jsonb_build_object(
            'contrato', 'bonificador-reaproveitamento-orcamento-v1',
            'linha_destino_id', v_destino.id,
            'linha_fonte_id', v_fonte.id,
            'resultado_fonte_fingerprint', v_bonus.resultado_fingerprint,
            'entrada_bonificador_fingerprint', v_bonus.entrada_bonificador_fingerprint,
            'formula_fingerprint', v_bonus.formula_fingerprint
          )::text,
          'UTF8'::name
        ),
        'sha256'
      ),
      'hex'
    );

    insert into clube_novo.build_bonificador(
      bonus_pe,
      bonus_fisico_total,
      bonus_posicao,
      bonus_playstyle_1,
      bonus_playstyle_2,
      bonus_ia,
      bonus_outros,
      bonus_total,
      contrato_versao,
      contrato_fingerprint,
      carta_versao,
      carta_fingerprint,
      formula_fingerprint,
      resultado_fingerprint,
      concluido_em,
      bonus_fisico_detalhe,
      criado_em,
      motor_versao,
      b_corpo,
      b_pe_ruim,
      b_estilo,
      b_total,
      faltou,
      corpo_soma,
      corpo_pct,
      entrada_bonificador_fingerprint
    ) values (
      v_bonus.bonus_pe,
      v_bonus.bonus_fisico_total,
      v_bonus.bonus_posicao,
      v_bonus.bonus_playstyle_1,
      v_bonus.bonus_playstyle_2,
      v_bonus.bonus_ia,
      v_bonus.bonus_outros,
      v_bonus.bonus_total,
      v_bonus.contrato_versao,
      v_bonus.contrato_fingerprint,
      v_bonus.carta_versao,
      v_bonus.carta_fingerprint,
      v_bonus.formula_fingerprint,
      v_resultado_fingerprint,
      v_bonus.concluido_em,
      v_bonus.bonus_fisico_detalhe,
      pg_catalog.clock_timestamp(),
      v_bonus.motor_versao,
      v_bonus.b_corpo,
      v_bonus.b_pe_ruim,
      v_bonus.b_estilo,
      v_bonus.b_total,
      v_bonus.faltou,
      v_bonus.corpo_soma,
      v_bonus.corpo_pct,
      v_bonus.entrada_bonificador_fingerprint
    )
    on conflict (resultado_fingerprint) do nothing
    returning id into v_bonus_destino_id;

    if v_bonus_destino_id is null then
      select id into v_bonus_destino_id
      from clube_novo.build_bonificador
      where resultado_fingerprint = v_resultado_fingerprint;
    else
      v_clonado := true;
    end if;

    if v_bonus_destino_id is null then
      raise exception 'vinculo Bonificador V10: clone idempotente nao foi localizado';
    end if;
  end if;

  if v_destino.build_bonificador_id is not null then
    select * into v_bonus_atual
    from clube_novo.build_bonificador
    where id = v_destino.build_bonificador_id;

    if v_bonus_atual.id is null
       or v_bonus_atual.motor_versao is distinct from v_bonus.motor_versao
       or v_bonus_atual.formula_fingerprint is distinct from v_bonus.formula_fingerprint
       or v_bonus_atual.contrato_versao is distinct from v_bonus.contrato_versao
       or v_bonus_atual.carta_versao is distinct from v_bonus.carta_versao
       or v_bonus_atual.carta_fingerprint is distinct from v_bonus.carta_fingerprint
       or v_bonus_atual.entrada_bonificador_fingerprint is distinct from v_bonus.entrada_bonificador_fingerprint
       or v_bonus_atual.bonus_pe is distinct from v_bonus.bonus_pe
       or v_bonus_atual.bonus_fisico_total is distinct from v_bonus.bonus_fisico_total
       or v_bonus_atual.bonus_posicao is distinct from v_bonus.bonus_posicao
       or v_bonus_atual.bonus_playstyle_1 is distinct from v_bonus.bonus_playstyle_1
       or v_bonus_atual.bonus_playstyle_2 is distinct from v_bonus.bonus_playstyle_2
       or v_bonus_atual.bonus_ia is distinct from v_bonus.bonus_ia
       or v_bonus_atual.bonus_outros is distinct from v_bonus.bonus_outros
       or v_bonus_atual.bonus_total is distinct from v_bonus.bonus_total
       or v_bonus_atual.bonus_fisico_detalhe is distinct from v_bonus.bonus_fisico_detalhe
       or v_bonus_atual.faltou is distinct from v_bonus.faltou
       or v_bonus_atual.corpo_soma is distinct from v_bonus.corpo_soma
       or v_bonus_atual.corpo_pct is distinct from v_bonus.corpo_pct then
      raise exception 'vinculo Bonificador V10: linha destino ja possui resultado diferente';
    end if;

    v_bonus_destino_id := v_bonus_atual.id;
    v_resultado_fingerprint := v_bonus_atual.resultado_fingerprint;
  else
    if exists (
      select 1
      from clube_novo.build_linha_card x
      where x.build_bonificador_id = v_bonus_destino_id
        and x.id <> v_destino.id
    ) then
      raise exception 'vinculo Bonificador V10: resultado destino ja pertence a outra linha';
    end if;

    v_anterior_guard := pg_catalog.current_setting(
      'clube_novo.finalizacao_linha_em_curso', true
    );
    perform pg_catalog.set_config(
      'clube_novo.finalizacao_linha_em_curso', v_destino.id::text, true
    );

    update clube_novo.build_linha_card
    set build_bonificador_id = v_bonus_destino_id,
        bonificador_motor_versao = v_bonus.motor_versao,
        bonificador_contrato_versao = v_bonus.contrato_versao,
        snapshot_bonificador_fingerprint = v_resultado_fingerprint,
        atualizado_em = pg_catalog.clock_timestamp()
    where id = v_destino.id
      and build_bonificador_id is null;

    if not found then
      raise exception 'vinculo Bonificador V10: linha mudou durante a vinculacao';
    end if;

    perform pg_catalog.set_config(
      'clube_novo.finalizacao_linha_em_curso', coalesce(v_anterior_guard, ''), true
    );
    v_vinculado := true;

    insert into clube_novo.build_finalizacao_evento_v1(linha_id, evento, detalhe)
    values (
      v_destino.id,
      case when p_linha_destino_id = p_linha_fonte_id
        then 'bonificador_v10_vinculado_independente'
        else 'bonificador_v10_reaproveitado_orcamento'
      end,
      jsonb_build_object(
        'origem', coalesce(nullif(p_origem, ''), 'desconhecida'),
        'linha_fonte_id', v_fonte.id,
        'build_bonificador_fonte_id', v_bonus.id,
        'build_bonificador_destino_id', v_bonus_destino_id,
        'clonado', v_clonado,
        'sem_recalculo', true
      )
    );
  end if;

  if v_destino.build_otimizador_id is not null
     and v_destino.estado_otimizador = 'concluido' then
    v_finalizacao := clube_novo.finalizar_publicar_linha_v1(
      v_destino.id,
      coalesce(nullif(p_origem, ''), 'bonificador_v10_independente')
    );
  else
    v_finalizacao := jsonb_build_object(
      'ok', true,
      'linha_id', v_destino.id,
      'estado', 'aguardando_otimizador'
    );
  end if;

  return jsonb_build_object(
    'ok', true,
    'linha_destino_id', v_destino.id,
    'linha_fonte_id', v_fonte.id,
    'build_bonificador_id', v_bonus_destino_id,
    'vinculado', v_vinculado,
    'clonado', v_clonado,
    'sem_recalculo', true,
    'finalizacao', v_finalizacao
  );
end
$function$;

revoke all on function clube_novo.vincular_bonificador_v10_independente_v1(
  bigint, bigint, bigint, text
) from public, anon, authenticated;

create or replace function clube_novo.reaproveitar_bonificador_revisao_orcamento_v1(
  p_linha_anterior_id bigint,
  p_build_bonificador_id bigint default null,
  p_origem text default 'revisao_orcamento'
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_revisao clube_novo.orcamento_revisao_linha_v1%rowtype;
  v_bonus_id bigint := p_build_bonificador_id;
begin
  select * into v_revisao
  from clube_novo.orcamento_revisao_linha_v1
  where linha_anterior_id = p_linha_anterior_id
  for update;

  if v_revisao.linha_anterior_id is null then
    return jsonb_build_object(
      'ok', false,
      'estado', 'sem_revisao',
      'linha_anterior_id', p_linha_anterior_id
    );
  end if;

  if v_revisao.linha_nova_id is null then
    return jsonb_build_object(
      'ok', true,
      'estado', 'aguardando_linha_nova',
      'linha_anterior_id', p_linha_anterior_id
    );
  end if;

  if v_bonus_id is null then
    select i.build_bonificador_id_novo into v_bonus_id
    from clube_novo.bonificador_correcao_item_v1 i
    join clube_novo.build_bonificador b on b.id = i.build_bonificador_id_novo
    where i.build_linha_card_id = v_revisao.linha_anterior_id
      and i.estado_item = 'preparado'
      and b.motor_versao = 'v10-0409-fisico-regra-aprovada-v1'
      and b.formula_fingerprint = '756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
      and b.contrato_versao = 'bonificador-regua-v3'
    order by i.preparado_em desc nulls last, i.lote_id desc
    limit 1;
  end if;

  if v_bonus_id is null then
    select l.build_bonificador_id into v_bonus_id
    from clube_novo.build_linha_card l
    join clube_novo.build_bonificador b on b.id = l.build_bonificador_id
    where l.id = v_revisao.linha_anterior_id
      and b.motor_versao = 'v10-0409-fisico-regra-aprovada-v1'
      and b.formula_fingerprint = '756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
      and b.contrato_versao = 'bonificador-regua-v3';
  end if;

  if v_bonus_id is null then
    return jsonb_build_object(
      'ok', true,
      'estado', 'aguardando_bonificador',
      'linha_anterior_id', v_revisao.linha_anterior_id,
      'linha_nova_id', v_revisao.linha_nova_id
    );
  end if;

  return clube_novo.vincular_bonificador_v10_independente_v1(
    v_revisao.linha_nova_id,
    v_revisao.linha_anterior_id,
    v_bonus_id,
    coalesce(nullif(p_origem, ''), 'revisao_orcamento')
  );
end
$function$;

revoke all on function clube_novo.reaproveitar_bonificador_revisao_orcamento_v1(
  bigint, bigint, text
) from public, anon, authenticated;

create or replace function clube_novo.disparar_finalizacao_correcao_v1()
returns trigger
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_linha_nova_id bigint;
  v_erro text;
begin
  if new.estado_item = 'preparado'
     and new.build_bonificador_id_novo is not null
     and (
       tg_op = 'INSERT'
       or old.estado_item is distinct from new.estado_item
       or old.build_bonificador_id_novo is distinct from new.build_bonificador_id_novo
     ) then
    begin
      select r.linha_nova_id into v_linha_nova_id
      from clube_novo.orcamento_revisao_linha_v1 r
      where r.linha_anterior_id = new.build_linha_card_id;

      if v_linha_nova_id is not null then
        perform clube_novo.reaproveitar_bonificador_revisao_orcamento_v1(
          new.build_linha_card_id,
          new.build_bonificador_id_novo,
          'bonificador_correcao:' || tg_op
        );
      else
        perform clube_novo.vincular_bonificador_v10_independente_v1(
          new.build_linha_card_id,
          new.build_linha_card_id,
          new.build_bonificador_id_novo,
          'bonificador_correcao:' || tg_op
        );
      end if;
    exception when others then
      get stacked diagnostics v_erro = message_text;
      insert into clube_novo.build_finalizacao_evento_v1(linha_id, evento, detalhe)
      values (
        coalesce(v_linha_nova_id, new.build_linha_card_id),
        'bonificador_v10_vinculo_falhou',
        jsonb_build_object(
          'origem', 'bonificador_correcao:' || tg_op,
          'linha_fonte_id', new.build_linha_card_id,
          'build_bonificador_id', new.build_bonificador_id_novo,
          'erro', v_erro
        )
      );
    end;
  end if;
  return new;
end
$function$;

revoke all on function clube_novo.disparar_finalizacao_correcao_v1()
from public, anon, authenticated;

create or replace function clube_novo.disparar_reaproveitamento_bonificador_orcamento_v1()
returns trigger
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_erro text;
begin
  if new.linha_nova_id is not null
     and (tg_op = 'INSERT' or old.linha_nova_id is distinct from new.linha_nova_id) then
    begin
      perform clube_novo.reaproveitar_bonificador_revisao_orcamento_v1(
        new.linha_anterior_id,
        null,
        'revisao_orcamento:' || tg_op
      );
    exception when others then
      get stacked diagnostics v_erro = message_text;
      insert into clube_novo.build_finalizacao_evento_v1(linha_id, evento, detalhe)
      values (
        new.linha_nova_id,
        'bonificador_v10_reaproveitamento_falhou',
        jsonb_build_object(
          'origem', 'revisao_orcamento:' || tg_op,
          'linha_fonte_id', new.linha_anterior_id,
          'erro', v_erro
        )
      );
    end;
  end if;
  return new;
end
$function$;

revoke all on function clube_novo.disparar_reaproveitamento_bonificador_orcamento_v1()
from public, anon, authenticated;

drop trigger if exists orcamento_revisao_bonificador_inserir_v1
on clube_novo.orcamento_revisao_linha_v1;
create trigger orcamento_revisao_bonificador_inserir_v1
after insert on clube_novo.orcamento_revisao_linha_v1
for each row
execute function clube_novo.disparar_reaproveitamento_bonificador_orcamento_v1();

drop trigger if exists orcamento_revisao_bonificador_atualizar_v1
on clube_novo.orcamento_revisao_linha_v1;
create trigger orcamento_revisao_bonificador_atualizar_v1
after update of linha_nova_id on clube_novo.orcamento_revisao_linha_v1
for each row
when (old.linha_nova_id is distinct from new.linha_nova_id)
execute function clube_novo.disparar_reaproveitamento_bonificador_orcamento_v1();

create or replace function public.bonificador_vincular_preparados_tick_v1(
  p_lote_id uuid,
  p_limite integer default 500
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  r record;
  v jsonb;
  v_processadas integer := 0;
  v_vinculadas integer := 0;
  v_clonadas integer := 0;
  v_publicadas integer := 0;
  v_erros integer := 0;
begin
  if p_lote_id is null or coalesce(p_limite, 0) not between 1 and 1000 then
    raise exception 'tick de vinculo: lote obrigatorio e limite entre 1 e 1000';
  end if;

  if not exists (
    select 1 from clube_novo.bonificador_correcao_lote_v1 where id = p_lote_id
  ) then
    raise exception 'tick de vinculo: lote inexistente';
  end if;

  for r in
    select
      i.build_linha_card_id as linha_fonte_id,
      coalesce(rv.linha_nova_id, i.build_linha_card_id) as linha_destino_id,
      i.build_bonificador_id_novo as bonus_id
    from clube_novo.bonificador_correcao_item_v1 i
    join clube_novo.build_bonificador b on b.id = i.build_bonificador_id_novo
    left join clube_novo.orcamento_revisao_linha_v1 rv
      on rv.linha_anterior_id = i.build_linha_card_id
    join clube_novo.build_linha_card destino
      on destino.id = coalesce(rv.linha_nova_id, i.build_linha_card_id)
    left join clube_novo.build_otimizador otim
      on otim.id = destino.build_otimizador_id
    where i.lote_id = p_lote_id
      and i.estado_item = 'preparado'
      and i.build_bonificador_id_novo is not null
      and destino.build_bonificador_id is null
      and destino.estado <> 'invalida'
      and destino.execucao_tipo = 'producao'
      and destino.lote_teste_id is null
      and b.motor_versao = 'v10-0409-fisico-regra-aprovada-v1'
      and b.formula_fingerprint = '756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
      and b.contrato_versao = 'bonificador-regua-v3'
      and b.carta_versao = destino.carta_versao
      and b.carta_fingerprint = destino.carta_fingerprint
      and b.entrada_bonificador_fingerprint = destino.carta_fingerprint
      and cardinality(b.faltou) = 0
    order by
      case when destino.build_otimizador_id is not null
                  and destino.estado_otimizador = 'concluido'
                  and otim.resultado_fingerprint is not distinct from destino.snapshot_otimizador_fingerprint
                  and jsonb_typeof(otim.atributos_finais) = 'array'
                  and jsonb_array_length(otim.atributos_finais) = 26
                  and jsonb_typeof(coalesce(otim.atributos_internos, otim.atributos_finais)) = 'array'
                  and jsonb_array_length(coalesce(otim.atributos_internos, otim.atributos_finais)) = 26
                  and otim.arows_snapshot is not null
             then 0 else 1 end,
      i.prioridade_grupo,
      i.prioridade_overall desc nulls last,
      i.prioridade_card_id,
      i.prioridade_funcao_id,
      i.prioridade_posicao_id,
      i.build_linha_card_id
    limit p_limite
    for update of i skip locked
  loop
    begin
      v := clube_novo.vincular_bonificador_v10_independente_v1(
        r.linha_destino_id,
        r.linha_fonte_id,
        r.bonus_id,
        'backfill_bonificador_independente'
      );
      v_processadas := v_processadas + 1;
      if coalesce((v->>'vinculado')::boolean, false) then
        v_vinculadas := v_vinculadas + 1;
      end if;
      if coalesce((v->>'clonado')::boolean, false) then
        v_clonadas := v_clonadas + 1;
      end if;
      if v#>>'{finalizacao,estado}' in ('publicada', 'ja_publicada') then
        v_publicadas := v_publicadas + 1;
      end if;
    exception when others then
      v_processadas := v_processadas + 1;
      v_erros := v_erros + 1;
      insert into clube_novo.build_finalizacao_evento_v1(linha_id, evento, detalhe)
      values (
        r.linha_destino_id,
        'bonificador_v10_backfill_falhou',
        jsonb_build_object(
          'linha_fonte_id', r.linha_fonte_id,
          'build_bonificador_id', r.bonus_id,
          'erro', sqlerrm
        )
      );
    end;
  end loop;

  return jsonb_build_object(
    'ok', v_erros = 0,
    'lote_id', p_lote_id,
    'processadas', v_processadas,
    'vinculadas', v_vinculadas,
    'clonadas', v_clonadas,
    'publicadas', v_publicadas,
    'erros', v_erros
  );
end
$function$;

revoke all on function public.bonificador_vincular_preparados_tick_v1(uuid, integer)
from public, anon, authenticated;
grant execute on function public.bonificador_vincular_preparados_tick_v1(uuid, integer)
to service_role, bonificador_runtime;

notify pgrst, 'reload schema';

commit;
