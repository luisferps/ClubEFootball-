CREATE OR REPLACE FUNCTION clube_novo.gravar_build_bonificador_v6_antes_altura_ia(p_resultado jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  l clube_novo.build_linha_card%rowtype;
  r jsonb;
  c jsonb;
  resultado_id bigint;
  resultado_fp text;
  v_idempotente boolean:=false;
begin
  perform clube_novo.exigir_producao_bonificador_v12();
  perform clube_novo.validar_payload_bonificador_v12(p_resultado);
  select * into l from clube_novo.build_linha_card
  where id=(p_resultado->>'build_linha_card_id')::bigint for update;
  if l.id is null or l.card_id<>p_resultado->>'card_id'
     or l.funcao_id<>(p_resultado->>'funcao_id')::bigint
     or l.posicao_id<>(p_resultado->>'posicao_id')::integer then
    raise exception 'writer V5: identidade canonica divergente';
  end if;

  r:=public.bonificador_regua_v4();
  c:=public.bonificador_carta_v3(l.card_id);
  if not coalesce((r->>'pode_rodar')::boolean,false)
     or not coalesce((c->>'pode_rodar')::boolean,false)
     or c->>'carta_versao'<>l.carta_versao
     or c->>'carta_fingerprint'<>p_resultado->>'carta_fingerprint'
     or r->>'contrato'<>p_resultado->>'contrato_versao'
     or r->>'contrato_fingerprint'<>p_resultado->>'contrato_fingerprint' then
    raise exception 'writer V5: selo ou gate divergente';
  end if;

  resultado_fp:=encode(extensions.digest(convert_to(jsonb_build_object(
    'linha_id',l.id,'card_id',l.card_id,'funcao_id',l.funcao_id,
    'resultado',p_resultado,'regua',r->>'contrato_fingerprint',
    'carta',c->>'carta_fingerprint',
    'formula','4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8'
  )::text,'UTF8'),'sha256'),'hex');

  if l.build_bonificador_id is not null then
    if exists (
      select 1 from clube_novo.build_bonificador b
      where b.id=l.build_bonificador_id
        and b.motor_versao='v12-0909-estilo-funcao-ativacao-v1'
        and b.formula_fingerprint='4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8'
        and b.resultado_fingerprint=resultado_fp
    ) then
      resultado_id:=l.build_bonificador_id;
      v_idempotente:=true;
    else
      raise exception 'writer V5: linha ligada a resultado diferente';
    end if;
  end if;

  if not v_idempotente then
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
    end if;
    if resultado_id is null then
      raise exception 'writer V5: resultado nao localizado apos upsert';
    end if;

    update clube_novo.build_linha_card set
      build_bonificador_id=resultado_id,
      bonificador_motor_versao=p_resultado->>'motor_versao',
      bonificador_contrato_versao=r->>'contrato',
      snapshot_bonificador_fingerprint=resultado_fp,
      atualizado_em=clock_timestamp()
    where id=l.id;
  end if;

  return jsonb_build_object(
    'readback','ok','gravado',not v_idempotente,'idempotente',v_idempotente,
    'build_linha_card_id',l.id,'build_bonificador_id',resultado_id,
    'carta_versao',l.carta_versao,'carta_fingerprint',c->>'carta_fingerprint',
    'resultado_fingerprint',resultado_fp,'independente_do_otimizador',true
  );
end
$function$
;
revoke all on function clube_novo.gravar_build_bonificador_v6_antes_altura_ia(jsonb) from public,anon,authenticated;
create or replace function public.gravar_build_bonificador_v6(p_resultado jsonb) returns jsonb
language plpgsql security definer set search_path='' as $$
declare r jsonb;n bigint;b clube_novo.build_bonificador%rowtype;f jsonb;fp_base text;
begin
 fp_base:=encode(extensions.digest(jsonb_build_object('linha_id',(p_resultado->>'build_linha_card_id')::bigint,
 'card_id',p_resultado->>'card_id','funcao_id',(p_resultado->>'funcao_id')::bigint,
 'resultado',p_resultado,'regua',p_resultado->>'contrato_fingerprint','carta',p_resultado->>'carta_fingerprint',
 'formula',p_resultado->>'formula_fingerprint')::text,'sha256'),'hex');
 select x.* into b from clube_novo.bonificador_altura_ia_sucessor_v13 m
 join clube_novo.build_bonificador a on a.id=m.antigo_id join clube_novo.build_bonificador x on x.id=m.novo_id
 join clube_novo.build_linha_card l on l.id=m.linha_id
 where m.linha_id=(p_resultado->>'build_linha_card_id')::bigint and a.resultado_fingerprint=fp_base
 and (l.build_bonificador_id=x.id or exists(select 1 from clube_novo.bonificador_correcao_item_v1 i where i.build_linha_card_id=l.id and i.build_bonificador_id_novo=x.id)) limit 1;
 if b.id is not null then return jsonb_build_object('readback','ok','gravado',false,'idempotente',true,
 'build_linha_card_id',(p_resultado->>'build_linha_card_id')::bigint,'build_bonificador_id',b.id,
 'carta_versao',b.carta_versao,'carta_fingerprint',b.carta_fingerprint,'resultado_fingerprint',b.resultado_fingerprint,
 'politica_aplicada','altura-ia-v13','bonus_fisico_total',b.bonus_fisico_total,'bonus_ia',b.bonus_ia,'bonus_total',b.bonus_total);end if;
 r:=clube_novo.gravar_build_bonificador_v6_antes_altura_ia(p_resultado);
 n:=clube_novo.corrigir_altura_ia_resultado_v13((p_resultado->>'build_linha_card_id')::bigint,(r->>'build_bonificador_id')::bigint);
 select * into b from clube_novo.build_bonificador where id=n;
 update clube_novo.bonificador_correcao_item_v1 set build_bonificador_id_novo=n
  where build_linha_card_id=(p_resultado->>'build_linha_card_id')::bigint and build_bonificador_id_novo=(r->>'build_bonificador_id')::bigint and estado_item='preparado';
 update clube_novo.build_linha_card set build_bonificador_id=n,bonificador_motor_versao=b.motor_versao,
 bonificador_contrato_versao=b.contrato_versao,snapshot_bonificador_fingerprint=b.resultado_fingerprint
 where id=(p_resultado->>'build_linha_card_id')::bigint and build_bonificador_id=(r->>'build_bonificador_id')::bigint;
 if exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 where linha_id=(p_resultado->>'build_linha_card_id')::bigint) then
  f:=clube_novo.finalizar_publicar_linha_v1((p_resultado->>'build_linha_card_id')::bigint,'writer_altura_ia_v13');
  if f->>'estado' not in('publicada','ja_publicada') then raise exception 'Finalização V13 recusada: %',f;end if;
 end if;
 return r||jsonb_build_object('build_bonificador_id',n,'resultado_fingerprint',b.resultado_fingerprint,
 'politica_aplicada','altura-ia-v13','bonus_fisico_total',b.bonus_fisico_total,'bonus_ia',b.bonus_ia,'bonus_total',b.bonus_total);
end $$;
revoke all on function public.gravar_build_bonificador_v6(jsonb) from public,anon,authenticated;
grant execute on function public.gravar_build_bonificador_v6(jsonb) to service_role;
CREATE OR REPLACE FUNCTION clube_novo.gravar_build_bonificador_correcao_v2_antes_altura_ia(p_lote_id uuid, p_resultado jsonb)
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
revoke all on function clube_novo.gravar_build_bonificador_correcao_v2_antes_altura_ia(uuid,jsonb) from public,anon,authenticated;
create or replace function public.gravar_build_bonificador_correcao_v2(p_lote_id uuid,p_resultado jsonb) returns jsonb
language plpgsql security definer set search_path='' as $$
declare r jsonb;n bigint;b clube_novo.build_bonificador%rowtype;f jsonb;fp_base text;
begin
 fp_base:=encode(extensions.digest(jsonb_build_object('linha_id',(p_resultado->>'build_linha_card_id')::bigint,
 'card_id',p_resultado->>'card_id','funcao_id',(p_resultado->>'funcao_id')::bigint,
 'resultado',p_resultado,'regua',p_resultado->>'contrato_fingerprint','carta',p_resultado->>'carta_fingerprint',
 'formula',p_resultado->>'formula_fingerprint')::text,'sha256'),'hex');
 select x.* into b from clube_novo.bonificador_altura_ia_sucessor_v13 m
 join clube_novo.build_bonificador a on a.id=m.antigo_id join clube_novo.build_bonificador x on x.id=m.novo_id
 join clube_novo.build_linha_card l on l.id=m.linha_id
 where m.linha_id=(p_resultado->>'build_linha_card_id')::bigint and a.resultado_fingerprint=fp_base
 and (l.build_bonificador_id=x.id or exists(select 1 from clube_novo.bonificador_correcao_item_v1 i where i.build_linha_card_id=l.id and i.build_bonificador_id_novo=x.id)) limit 1;
 if b.id is not null then return jsonb_build_object('readback','ok','gravado',false,'idempotente',true,
 'build_linha_card_id',(p_resultado->>'build_linha_card_id')::bigint,'build_bonificador_id',b.id,
 'carta_versao',b.carta_versao,'carta_fingerprint',b.carta_fingerprint,'resultado_fingerprint',b.resultado_fingerprint,
 'politica_aplicada','altura-ia-v13','bonus_fisico_total',b.bonus_fisico_total,'bonus_ia',b.bonus_ia,'bonus_total',b.bonus_total);end if;
 r:=clube_novo.gravar_build_bonificador_correcao_v2_antes_altura_ia(p_lote_id,p_resultado);
 n:=clube_novo.corrigir_altura_ia_resultado_v13((p_resultado->>'build_linha_card_id')::bigint,(r->>'build_bonificador_id')::bigint);
 select * into b from clube_novo.build_bonificador where id=n;
 update clube_novo.bonificador_correcao_item_v1 set build_bonificador_id_novo=n
  where build_linha_card_id=(p_resultado->>'build_linha_card_id')::bigint and build_bonificador_id_novo=(r->>'build_bonificador_id')::bigint and estado_item='preparado';
 update clube_novo.build_linha_card set build_bonificador_id=n,bonificador_motor_versao=b.motor_versao,
 bonificador_contrato_versao=b.contrato_versao,snapshot_bonificador_fingerprint=b.resultado_fingerprint
 where id=(p_resultado->>'build_linha_card_id')::bigint and build_bonificador_id=(r->>'build_bonificador_id')::bigint;
 if exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 where linha_id=(p_resultado->>'build_linha_card_id')::bigint) then
  f:=clube_novo.finalizar_publicar_linha_v1((p_resultado->>'build_linha_card_id')::bigint,'writer_altura_ia_v13');
  if f->>'estado' not in('publicada','ja_publicada') then raise exception 'Finalização V13 recusada: %',f;end if;
 end if;
 return r||jsonb_build_object('build_bonificador_id',n,'resultado_fingerprint',b.resultado_fingerprint,
 'politica_aplicada','altura-ia-v13','bonus_fisico_total',b.bonus_fisico_total,'bonus_ia',b.bonus_ia,'bonus_total',b.bonus_total);
end $$;
revoke all on function public.gravar_build_bonificador_correcao_v2(uuid,jsonb) from public,anon,authenticated;
grant execute on function public.gravar_build_bonificador_correcao_v2(uuid,jsonb) to service_role;
