CREATE OR REPLACE FUNCTION clube_novo.reaproveitar_bonificador_conforme_v1(p_linha_destino_id bigint, p_linha_fonte_id bigint, p_build_bonificador_id bigint, p_origem text DEFAULT 'desconhecida'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
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
  v_entrada_atual jsonb;
  v_antes clube_novo.recalculo_1209_entrada_antes_v1%rowtype;
  v_fonte_original jsonb;
  v_fp_atual text;
  v_versao_atual text;
  v_esperado jsonb;
begin
  if p_linha_destino_id is null
     or p_linha_fonte_id is null
     or p_build_bonificador_id is null then
    raise exception 'reaproveitamento Bonificador: linha destino, linha fonte e resultado sao obrigatorios';
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
    raise exception 'reaproveitamento Bonificador: linha ou resultado inexistente';
  end if;

  if v_destino.execucao_tipo <> 'producao'
     or v_destino.lote_teste_id is not null
     or v_destino.estado = 'invalida' then
    raise exception 'reaproveitamento Bonificador: linha destino nao e produtiva ativa';
  end if;

  if v_destino.card_id is distinct from v_fonte.card_id
     or v_destino.funcao_id is distinct from v_fonte.funcao_id
     or v_destino.posicao_id is distinct from v_fonte.posicao_id
     or v_destino.impeto_condicional_codigo is distinct from v_fonte.impeto_condicional_codigo
     or v_destino.impeto_condicional_nivel is distinct from v_fonte.impeto_condicional_nivel then
    raise exception 'reaproveitamento Bonificador: identidade da linha substituta diverge da origem';
  end if;

  if p_linha_destino_id = p_linha_fonte_id then
    raise exception 'Reaproveitamento exige linha nova; a origem histórica permanece preservada';
  end if;
  perform pg_advisory_xact_lock_shared(hashtextextended('bonificador-conferencia-regra',0));
  perform pg_advisory_xact_lock(hashtextextended('bonificador-conferencia-card:'||v_destino.card_id,0));
  v_entrada_atual := clube_novo.bonificador_carta_v1(v_destino.card_id);
  v_fp_atual := clube_novo.bonificador_carta_fingerprint_v1(v_destino.card_id);
  select extraido_em::text into v_versao_atual from clube_novo.carta_jogo
    where card_id=v_destino.card_id and roda_motor is true and coalesce(jogador_indisponivel,false)=false;
  if v_versao_atual is null or coalesce((v_entrada_atual->>'pode_rodar')::boolean,false)=false
     or v_destino.carta_fingerprint is distinct from v_fp_atual
     or v_destino.carta_versao is distinct from v_versao_atual then
    raise exception 'Destino não corresponde à entrada efetiva vigente';
  end if;
  if v_bonus.carta_fingerprint is distinct from v_fp_atual
     or v_bonus.carta_versao is distinct from v_versao_atual then
    select * into v_antes from clube_novo.recalculo_1209_entrada_antes_v1 where card_id=v_destino.card_id;
    if not found or v_bonus.carta_fingerprint is distinct from v_antes.carta_fingerprint
       or v_bonus.carta_versao is distinct from (v_antes.carta->>'extraido_em')::timestamptz::text
       or coalesce((v_antes.entrada_bonificador->>'pode_rodar')::boolean,false)=false
       or (v_antes.entrada_bonificador - array['nome','slot1_nome','slot2_nome','proveniencia'])
          is distinct from (v_entrada_atual - array['nome','slot1_nome','slot2_nome','proveniencia']) then
      raise exception 'Não há prova de igualdade das entradas antes/depois da extração';
    end if;
  end if;
  if v_bonus.carta_fingerprint is null or v_bonus.entrada_bonificador_fingerprint is distinct from v_bonus.carta_fingerprint then
    raise exception 'Origem sem selo de entrada íntegro';
  end if;

  if v_fonte.build_bonificador_id is distinct from v_bonus.id
     and not exists (
       select 1
       from clube_novo.bonificador_correcao_item_v1 i
       where i.build_linha_card_id = v_fonte.id
         and i.estado_item = 'preparado'
         and i.build_bonificador_id_novo = v_bonus.id
     )
     and not exists (
       select 1 from clube_novo.bonificador_altura_ia_sucessor_v13 s
       join clube_novo.build_bonificador anterior on anterior.id=s.antigo_id
       where s.linha_id=v_fonte.id and s.novo_id=v_bonus.id
         and anterior.carta_fingerprint=v_fonte.carta_fingerprint
         and anterior.carta_versao=v_fonte.carta_versao
     ) then
    raise exception 'reaproveitamento Bonificador: resultado nao pertence a linha fonte';
  end if;

  if v_fonte.execucao_tipo <> 'producao' or v_fonte.lote_teste_id is not null
     or v_bonus.carta_fingerprint is distinct from v_fonte.carta_fingerprint
     or v_bonus.carta_versao is distinct from v_fonte.carta_versao then
    raise exception 'Origem sem identidade produtiva e selos coerentes';
  end if;
  v_esperado := clube_novo.bonificador_componentes_vigentes_v1(v_destino.card_id,v_destino.funcao_id,v_destino.posicao_id);
  if not clube_novo.bonificador_resultado_conforme_componentes_v1(to_jsonb(v_bonus),v_esperado) then
    raise exception 'Bônus de origem não atende a todos os componentes vigentes';
  end if;
  v_fonte_original := to_jsonb(v_bonus);
  -- Nova certificação após prova completa. Não altera o registro de origem nem suas parcelas.
  v_bonus.carta_versao := v_versao_atual;
  v_bonus.carta_fingerprint := v_fp_atual;
  v_bonus.entrada_bonificador_fingerprint := v_fp_atual;
  v_bonus.motor_versao := 'v13-1009-altura-ia-v1';
  v_bonus.contrato_versao := 'bonificador-altura-ia-v13';
  v_bonus.contrato_fingerprint := 'afa495d927fe99730fa154e5d91c227e56c36c51bd048cd8881b688bc2aa126f';
  v_bonus.formula_fingerprint := v_bonus.contrato_fingerprint;

  if p_linha_destino_id = p_linha_fonte_id then
    v_bonus_destino_id := v_bonus.id;
    v_resultado_fingerprint := v_bonus.resultado_fingerprint;
  else
    v_resultado_fingerprint := pg_catalog.encode(
      extensions.digest(
        pg_catalog.convert_to(
          jsonb_build_object(
            'contrato', 'bonificador-revalidacao-componentes-1209-v1',
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
      raise exception 'reaproveitamento Bonificador: clone idempotente nao foi localizado';
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
      raise exception 'reaproveitamento Bonificador: linha destino ja possui resultado diferente';
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
      raise exception 'reaproveitamento Bonificador: resultado destino ja pertence a outra linha';
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
      raise exception 'reaproveitamento Bonificador: linha mudou durante a vinculacao';
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
        else 'bonificador_revalidado_sem_recalculo'
      end,
      jsonb_build_object(
        'origem', coalesce(nullif(p_origem, ''), 'desconhecida'),
        'linha_fonte_id', v_fonte.id,
        'build_bonificador_fonte_id', v_bonus.id,
        'build_bonificador_destino_id', v_bonus_destino_id,
        'clonado', v_clonado,
        'sem_recalculo', true,
        'revalidacao', 'bonificador-revalidacao-componentes-1209-v1',
        'selo_fonte_original', jsonb_build_object('motor',v_fonte_original->'motor_versao','formula',v_fonte_original->'formula_fingerprint','entrada',v_fonte_original->'entrada_bonificador_fingerprint'),
        'componentes_conferidos', v_esperado,
        'entrada_efetiva_sha256',encode(extensions.digest(v_entrada_atual::text,'sha256'),'hex')
      )
    );
  end if;

  insert into clube_novo.bonificador_conferencia_vigente_v1(linha_id,card_id,funcao_id,posicao_id,bonus_id,entrada_fingerprint,resultado_fingerprint,regra_fingerprint,conforme,conferido_em)
  values(v_destino.id,v_destino.card_id,v_destino.funcao_id,v_destino.posicao_id,v_bonus_destino_id,v_fp_atual,v_resultado_fingerprint,clube_novo.bonificador_conferencia_regra_fingerprint_v1(),true,clock_timestamp())
  on conflict(linha_id) do update set bonus_id=excluded.bonus_id,card_id=excluded.card_id,funcao_id=excluded.funcao_id,posicao_id=excluded.posicao_id,entrada_fingerprint=excluded.entrada_fingerprint,resultado_fingerprint=excluded.resultado_fingerprint,regra_fingerprint=excluded.regra_fingerprint,conforme=true,conferido_em=excluded.conferido_em;

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
revoke all on function clube_novo.reaproveitar_bonificador_conforme_v1(bigint,bigint,bigint,text) from public,anon,authenticated;
