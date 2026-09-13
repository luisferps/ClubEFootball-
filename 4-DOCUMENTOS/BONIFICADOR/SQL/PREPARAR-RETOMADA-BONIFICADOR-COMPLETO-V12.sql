-- Prepara a retomada futura. Esta migracao nao inicia nem altera o lote atual.
create or replace function public.bonificador_preparar_retomada_v12(p_lote_id uuid)
returns jsonb language plpgsql security definer set search_path='' as $f$
declare l clube_novo.bonificador_correcao_lote_v1%rowtype; p clube_novo.bonificador_politica_estilo%rowtype;
begin
 if not exists(select 1 from clube_novo.correcao_estilos_execucao_v12 where concluida_em is not null)
  or exists(select 1 from clube_novo.correcao_estilos_item_v12 where estado<>'concluida') then
  return jsonb_build_object('liberada',false,'motivo','Aguarde a conclusao da correcao de estilos. Nenhuma linha foi reservada.');
 end if;
 perform pg_advisory_xact_lock(hashtextextended('correcao-estilos-v12-executor',0));
 select * into l from clube_novo.bonificador_correcao_lote_v1 where id=p_lote_id for update;
 if l.id is null or l.estado not in ('pausado','preparado') then raise exception 'lote inexistente ou nao esta pausado/preparado'; end if;
 if exists(select 1 from clube_novo.bonificador_correcao_item_v1 where lote_id=l.id and estado_item in ('processando','falha')) then
  raise exception 'o lote tem linha em processamento ou falha pendente'; end if;
 if l.motor_versao not in ('v11-0709-estilo-posicao-oficial-v1','v12-0909-estilo-funcao-ativacao-v1') then
  raise exception 'versao anterior do lote nao foi aprovada para esta retomada'; end if;
 select * into strict p from clube_novo.bonificador_politica_estilo where versao='estilos-funcao-20260909-v1' for update;
 if p.politica_fingerprint<>'7ed53bbab831180cde9d247782dd133fe072acadb69bd34871c3f83f28773dc5'
  or p.estado not in ('aprovada_implantacao_pendente','ativa') then raise exception 'politica de estilos mudou'; end if;
 if l.motor_versao<>'v12-0909-estilo-funcao-ativacao-v1' then
  update clube_novo.correcao_estilos_execucao_v12 set auditoria=auditoria||jsonb_build_object(
   'retomada_bonificador_completo',jsonb_build_object('solicitada_em',clock_timestamp(),'lote_antes',to_jsonb(l),'politica_estado_antes',p.estado))
  where id='estilos-funcao-20260909-v1';
  update clube_novo.bonificador_correcao_lote_v1 set
   motor_versao='v12-0909-estilo-funcao-ativacao-v1',
   contrato_regua='bonificador-regua-v4',
   formula_fingerprint='4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8',
   observacao=coalesce(observacao,'')||' | Retomada V12 apos conclusao seletiva; ordem, estados e resultados preservados.',
   atualizado_em=clock_timestamp()
  where id=l.id;
 end if;
 update clube_novo.bonificador_politica_estilo set estado='ativa' where versao=p.versao and estado<>'ativa';
 return jsonb_build_object('liberada',true,'lote_id',l.id,'estado',l.estado,
  'motor','v12-0909-estilo-funcao-ativacao-v1','nenhuma_linha_reservada',true);
end $f$;
revoke all on function public.bonificador_preparar_retomada_v12(uuid) from public,anon,authenticated;
grant execute on function public.bonificador_preparar_retomada_v12(uuid) to service_role;
CREATE OR REPLACE FUNCTION clube_novo.vincular_bonificador_v10_independente_v1(p_linha_destino_id bigint, p_linha_fonte_id bigint, p_build_bonificador_id bigint, p_origem text DEFAULT 'desconhecida'::text)
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

  if not clube_novo.bonus_estilo_conforme_v12(v_bonus.id,v_destino.card_id,v_destino.funcao_id,v_destino.posicao_id)
     or v_bonus.carta_versao is distinct from v_destino.carta_versao
     or v_bonus.carta_fingerprint is distinct from v_destino.carta_fingerprint
     or v_bonus.entrada_bonificador_fingerprint is distinct from v_destino.carta_fingerprint
     or coalesce(cardinality(v_bonus.faltou), -1) <> 0 then
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
$function$
;
CREATE OR REPLACE FUNCTION clube_novo.reaproveitar_bonificador_revisao_orcamento_v1(p_linha_anterior_id bigint, p_build_bonificador_id bigint DEFAULT NULL::bigint, p_origem text DEFAULT 'revisao_orcamento'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
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
      and (b.motor_versao,b.formula_fingerprint,b.contrato_versao) in (('v11-0709-estilo-posicao-oficial-v1','2e80a07d51f2bc8f456f9710c82717d38e3142cb3d52fd325b7b587c58ed2879','bonificador-regua-v3'),('v12-0909-estilo-funcao-ativacao-v1','4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8','bonificador-regua-v4'))
    order by i.preparado_em desc nulls last, i.lote_id desc
    limit 1;
  end if;

  if v_bonus_id is null then
    select l.build_bonificador_id into v_bonus_id
    from clube_novo.build_linha_card l
    join clube_novo.build_bonificador b on b.id = l.build_bonificador_id
    where l.id = v_revisao.linha_anterior_id
      and (b.motor_versao,b.formula_fingerprint,b.contrato_versao) in (('v11-0709-estilo-posicao-oficial-v1','2e80a07d51f2bc8f456f9710c82717d38e3142cb3d52fd325b7b587c58ed2879','bonificador-regua-v3'),('v12-0909-estilo-funcao-ativacao-v1','4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8','bonificador-regua-v4'));
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
$function$
;
CREATE OR REPLACE FUNCTION public.bonificador_correcao_controle_v1(p_lote_id uuid, p_acao text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_lote clube_novo.bonificador_correcao_lote_v1%rowtype;
  v_falhas bigint;
  v_processando bigint;
begin
  select * into v_lote
  from clube_novo.bonificador_correcao_lote_v1
  where id=p_lote_id
  for update;

  if v_lote.id is null then
    raise exception 'correção V10: lote inexistente';
  end if;

  select falha,processando
  into v_falhas,v_processando
  from clube_novo.bonificador_correcao_status_cache_v1
  where lote_id=p_lote_id;

  if v_falhas is null or v_processando is null then
    raise exception 'correção V10: cache de status ausente';
  end if;

  if p_acao in ('iniciar','retomar') then
    perform clube_novo.exigir_producao_bonificador_v12();
    if v_lote.motor_versao<>'v12-0909-estilo-funcao-ativacao-v1' then
      raise exception 'Atualize os arquivos e use a retomada V12 do Bonificador completo.';
    end if;

    if v_lote.estado not in ('preparado','pausado')
       or v_falhas<>0
       or v_processando<>0 then
      raise exception 'correção V10: lote não pode iniciar/retomar nesse estado';
    end if;

    update clube_novo.bonificador_correcao_lote_v1
    set estado='rodando',
        iniciado_em=coalesce(iniciado_em,clock_timestamp()),
        atualizado_em=clock_timestamp()
    where id=p_lote_id;

  elsif p_acao='pausar' then
    if v_lote.estado not in ('rodando','pausando') then
      raise exception 'correção V10: somente lote rodando pode pausar';
    end if;

    update clube_novo.bonificador_correcao_lote_v1
    set estado=case when v_processando=0 then 'pausado' else 'pausando' end,
        pausado_em=case when v_processando=0 then clock_timestamp() else pausado_em end,
        atualizado_em=clock_timestamp()
    where id=p_lote_id;

  elsif p_acao='repetir-falhas' then
    if v_lote.estado not in ('bloqueado','pausado')
       or v_processando<>0 then
      raise exception 'correção V10: falhas só podem ser reabertas com o lote parado';
    end if;

    update clube_novo.bonificador_correcao_item_v1
    set estado_item='pendente',
        erro=null,
        iniciado_em=null,
        atualizado_em=clock_timestamp()
    where lote_id=p_lote_id
      and estado_item='falha';

    update clube_novo.bonificador_correcao_lote_v1
    set estado='pausado',
        atualizado_em=clock_timestamp()
    where id=p_lote_id;

  elsif p_acao='cancelar' then
    if v_lote.estado not in ('preparado','pausado','bloqueado')
       or exists(
         select 1
         from clube_novo.bonificador_correcao_item_v1
         where lote_id=p_lote_id
           and build_bonificador_id_novo is not null
       ) then
      raise exception 'correção V10: lote com staging não pode ser cancelado';
    end if;

    update clube_novo.bonificador_correcao_lote_v1
    set estado='cancelado',
        atualizado_em=clock_timestamp()
    where id=p_lote_id;

  else
    raise exception 'correção V10: ação desconhecida';
  end if;

  return public.bonificador_correcao_status_v1(p_lote_id);
end
$function$
;
CREATE OR REPLACE FUNCTION public.bonificador_correcao_proxima_linha_v2(p_lote_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_lote clube_novo.bonificador_correcao_lote_v1%rowtype;
  v_linha_id bigint;
  v_regua jsonb;
  v_resposta jsonb;
begin
  perform clube_novo.exigir_producao_bonificador_v12();
  select * into v_lote from clube_novo.bonificador_correcao_lote_v1
  where id=p_lote_id for update;
  if v_lote.id is not null and (v_lote.motor_versao<>'v12-0909-estilo-funcao-ativacao-v1'
   or v_lote.formula_fingerprint<>'4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8') then
    raise exception 'lote ainda nao preparado para a retomada V12';
  end if;

  if v_lote.id is null then raise exception 'V10 paralelo: lote inexistente'; end if;
  if v_lote.estado<>'rodando' then
    if v_lote.estado='processado' then return null; end if;
    raise exception 'V10 paralelo: lote nao esta rodando';
  end if;

  select i.build_linha_card_id into v_linha_id
  from clube_novo.bonificador_correcao_item_v1 i
  where i.lote_id=p_lote_id and i.estado_item='pendente'
  order by i.prioridade_grupo,i.prioridade_overall desc nulls last,
           i.prioridade_card_id,i.prioridade_funcao_id,i.prioridade_posicao_id,
           i.build_linha_card_id
  for update skip locked limit 1;

  if v_linha_id is null then
    if not exists (
      select 1 from clube_novo.bonificador_correcao_item_v1
      where lote_id=p_lote_id and estado_item in ('pendente','processando','falha')
    ) then
      update clube_novo.bonificador_correcao_lote_v1 set
        estado='processado',processado_em=clock_timestamp(),atualizado_em=clock_timestamp()
      where id=p_lote_id;
    end if;
    return null;
  end if;

  update clube_novo.bonificador_correcao_item_v1 set
    estado_item='processando',tentativas=tentativas+1,iniciado_em=clock_timestamp(),
    atualizado_em=clock_timestamp()
  where lote_id=p_lote_id and build_linha_card_id=v_linha_id;

  v_regua:=public.bonificador_regua_v4();
  select jsonb_build_object(
    'build_linha_card_id',l.id,'card_id',l.card_id,'carta_nome',c.nome,
    'carta_tipo',c.tipo,'carta_box',c.box,'carta_overall',c.overall,
    'funcao_id',l.funcao_id,'funcao_codigo',coalesce(f.sigla,''),'funcao_nome',f.rotulo,
    'posicao_id',l.posicao_id,'posicao_codigo',coalesce(p.codigo_pt,''),'posicao_nome',p.nome_pt,
    'carta_versao',l.carta_versao,'carta_fingerprint',l.carta_fingerprint,
    'contrato_versao',v_regua->>'contrato',
    'contrato_fingerprint',v_regua->>'contrato_fingerprint',
    'formula_fingerprint',v_regua->>'formula_fingerprint'
  ) into v_resposta
  from clube_novo.build_linha_card l
  join clube_novo.carta_jogo c on c.card_id=l.card_id
  join clube_novo.funcao_sistema f on f.id=l.funcao_id
  join clube_novo.posicao_jogo p on p.id=l.posicao_id
  where l.id=v_linha_id;
  return v_resposta;
end
$function$
;
CREATE OR REPLACE FUNCTION public.gravar_build_bonificador_correcao_v2(p_lote_id uuid, p_resultado jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_lote clube_novo.bonificador_correcao_lote_v1%rowtype;
  v_item clube_novo.bonificador_correcao_item_v1%rowtype;
  l clube_novo.build_linha_card%rowtype;
  r jsonb;
  c jsonb;
  resultado_id bigint;
  resultado_fp text;
  v_gravado boolean:=false;
begin
  perform clube_novo.exigir_producao_bonificador_v12();
  perform clube_novo.validar_payload_bonificador_v12(p_resultado);
  select * into v_lote from clube_novo.bonificador_correcao_lote_v1
  where id=p_lote_id for update;
  if v_lote.id is not null and (v_lote.motor_versao<>'v12-0909-estilo-funcao-ativacao-v1'
   or v_lote.formula_fingerprint<>'4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8') then
    raise exception 'lote ainda nao preparado para a retomada V12';
  end if;

  if v_lote.id is null or v_lote.estado not in ('rodando','pausando') then
    raise exception 'writer corretivo V1: lote nao aceita gravacao';
  end if;
  select * into v_item from clube_novo.bonificador_correcao_item_v1
  where lote_id=p_lote_id
    and build_linha_card_id=(p_resultado->>'build_linha_card_id')::bigint
  for update;
  if v_item.lote_id is null or v_item.estado_item<>'processando' then
    raise exception 'writer corretivo V1: item nao esta reservado';
  end if;

  select * into l from clube_novo.build_linha_card where id=v_item.build_linha_card_id;
  if l.id is null or l.card_id<>p_resultado->>'card_id'
     or l.funcao_id<>(p_resultado->>'funcao_id')::bigint
     or l.posicao_id<>(p_resultado->>'posicao_id')::integer then
    raise exception 'writer corretivo V1: identidade canonica divergente';
  end if;

  r:=public.bonificador_regua_v4();
  c:=public.bonificador_carta_v3(l.card_id);
  if not coalesce((r->>'pode_rodar')::boolean,false)
     or not coalesce((c->>'pode_rodar')::boolean,false)
     or c->>'carta_versao'<>l.carta_versao
     or c->>'carta_fingerprint'<>p_resultado->>'carta_fingerprint'
     or r->>'contrato'<>p_resultado->>'contrato_versao'
     or r->>'contrato_fingerprint'<>p_resultado->>'contrato_fingerprint' then
    raise exception 'writer corretivo V1: selo ou gate divergente';
  end if;

  resultado_fp:=encode(extensions.digest(convert_to(jsonb_build_object(
    'linha_id',l.id,'card_id',l.card_id,'funcao_id',l.funcao_id,
    'resultado',p_resultado,'regua',r->>'contrato_fingerprint',
    'carta',c->>'carta_fingerprint',
    'formula','4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8'
  )::text,'UTF8'),'sha256'),'hex');

  insert into clube_novo.build_bonificador(
    bonus_pe,bonus_fisico_total,bonus_posicao,bonus_playstyle_1,
    bonus_playstyle_2,bonus_ia,bonus_outros,bonus_total,contrato_versao,
    contrato_fingerprint,carta_versao,carta_fingerprint,formula_fingerprint,
    resultado_fingerprint,bonus_fisico_detalhe,motor_versao,b_corpo,b_pe_ruim,
    b_estilo,b_total,faltou,entrada_bonificador_fingerprint,corpo_soma,corpo_pct
  ) values (
    (p_resultado->>'bonus_pe')::numeric,(p_resultado->>'bonus_fisico_total')::numeric,
    (p_resultado->>'bonus_posicao')::numeric,(p_resultado->>'bonus_playstyle_1')::numeric,
    (p_resultado->>'bonus_playstyle_2')::numeric,(p_resultado->>'bonus_ia')::numeric,
    coalesce(p_resultado->'bonus_outros','{}'::jsonb),(p_resultado->>'bonus_total')::numeric,
    r->>'contrato',r->>'contrato_fingerprint',l.carta_versao,c->>'carta_fingerprint',
    p_resultado->>'formula_fingerprint',resultado_fp,p_resultado->'bonus_fisico_detalhe',
    p_resultado->>'motor_versao',(p_resultado->>'bonus_fisico_total')::numeric,
    (p_resultado->>'bonus_pe')::numeric,
    (p_resultado->>'bonus_playstyle_1')::numeric+(p_resultado->>'bonus_playstyle_2')::numeric,
    (p_resultado->>'bonus_total')::numeric,'{}',c->>'carta_fingerprint',
    (p_resultado->>'corpo_soma')::numeric,(p_resultado->>'corpo_pct')::numeric
  ) on conflict (resultado_fingerprint) do nothing returning id into resultado_id;
  if resultado_id is null then
    select id into resultado_id from clube_novo.build_bonificador
    where resultado_fingerprint=resultado_fp;
  else
    v_gravado:=true;
  end if;
  if resultado_id is null then
    raise exception 'writer corretivo V1: resultado nao localizado apos upsert';
  end if;

  update clube_novo.bonificador_correcao_item_v1 set
    build_bonificador_id_novo=resultado_id,estado_item='preparado',erro=null,
    prova_fisico=jsonb_build_object(
      'bonus_fisico_total',(p_resultado->>'bonus_fisico_total')::numeric,
      'corpo_soma',(p_resultado->>'corpo_soma')::numeric,
      'corpo_maximo',(p_resultado->>'corpo_maximo')::numeric,
      'corpo_pct',(p_resultado->>'corpo_pct')::numeric,
      'detalhe',p_resultado->'bonus_fisico_detalhe'
    ),preparado_em=clock_timestamp(),atualizado_em=clock_timestamp()
  where lote_id=p_lote_id and build_linha_card_id=l.id;

  if v_lote.estado='pausando' and not exists (
    select 1 from clube_novo.bonificador_correcao_item_v1
    where lote_id=p_lote_id and estado_item='processando'
  ) then
    update clube_novo.bonificador_correcao_lote_v1 set
      estado='pausado',pausado_em=clock_timestamp(),atualizado_em=clock_timestamp()
    where id=p_lote_id;
  elsif v_lote.estado='rodando' and not exists (
    select 1 from clube_novo.bonificador_correcao_item_v1
    where lote_id=p_lote_id and estado_item in ('pendente','processando','falha')
  ) then
    update clube_novo.bonificador_correcao_lote_v1 set
      estado='processado',processado_em=clock_timestamp(),atualizado_em=clock_timestamp()
    where id=p_lote_id;
  end if;

  return jsonb_build_object(
    'readback','ok','gravado',v_gravado,'idempotente',not v_gravado,
    'build_linha_card_id',l.id,'build_bonificador_id',resultado_id,
    'carta_versao',l.carta_versao,'carta_fingerprint',c->>'carta_fingerprint',
    'resultado_fingerprint',resultado_fp,'staging',true,
    'linha_operacional_alterada',false,'independente_do_otimizador',true
  );
end
$function$
;

-- Compatibilidade estrita V11/V12 aplicada em 09/09/2026.
alter table clube_novo.bonificador_correcao_lote_v1
 drop constraint bonificador_correcao_lote_v1_contrato_regua_check,
 drop constraint bonificador_correcao_lote_v1_formula_fingerprint_check,
 drop constraint bonificador_correcao_lote_v1_motor_versao_check,
 add constraint bonificador_correcao_lote_v1_motor_contrato_formula_check check (
 (motor_versao='v11-0709-estilo-posicao-oficial-v1'
  and contrato_regua='bonificador-regua-v3'
  and formula_fingerprint='2e80a07d51f2bc8f456f9710c82717d38e3142cb3d52fd325b7b587c58ed2879')
 or
 (motor_versao='v12-0909-estilo-funcao-ativacao-v1'
  and contrato_regua='bonificador-regua-v4'
  and formula_fingerprint='4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8')
);