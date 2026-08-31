-- Escritor exclusivo do Bonificador V3: aceita somente a fila de teste V3.
-- Não altera fórmula; confere identidade, selos e soma recebida do motor.
begin;
create or replace function public.gravar_build_bonificador_v3(p_resultado jsonb)
returns jsonb language plpgsql security definer set search_path=''
as $function$
declare
  l clube_novo.build_linha_card%rowtype;
  r jsonb; c jsonb; resultado_id bigint; resultado_fp text;
  esperado constant text := 'ad8427acf268cf695bf69eca87704be95d8e1f13213d3ddec3d21955f705ce09';
begin
  if jsonb_typeof(p_resultado) <> 'object' or not (p_resultado ?& array[
    'build_linha_card_id','card_id','funcao_id','posicao_id','carta_versao','carta_fingerprint',
    'contrato_versao','contrato_fingerprint','formula_fingerprint','motor_versao','bonus_pe',
    'bonus_fisico_total','bonus_fisico_detalhe','bonus_posicao','bonus_playstyle_1',
    'bonus_playstyle_2','bonus_ia','bonus_total']) then
    raise exception 'writer v3: payload incompleto';
  end if;
  select * into l from clube_novo.build_linha_card
   where id=(p_resultado->>'build_linha_card_id')::bigint for update;
  if l.id is null or l.card_id<>p_resultado->>'card_id'
     or l.funcao_id<>(p_resultado->>'funcao_id')::bigint
     or l.posicao_id<>(p_resultado->>'posicao_id')::integer then
    raise exception 'writer v3: identidade canônica divergente';
  end if;
  if l.execucao_tipo<>'teste_isolado' or l.lote_estado<>'concluido'
     or l.estado<>'pendente' or l.estado_otimizador<>'concluido'
     or l.build_bonificador_id is not null
     or not (l.pendencias @> array['teste_nao_publicado','bonificador_nao_executado']::text[])
     or cardinality(l.pendencias)<>2 then
    raise exception 'writer v3: linha fora da fila de teste do Bonificador';
  end if;
  r:=public.bonificador_regua_v2(); c:=public.bonificador_carta_v2(l.card_id);
  if not coalesce((r->>'pode_rodar')::boolean,false)
     or not coalesce((c->>'pode_rodar')::boolean,false)
     or c->>'carta_versao'<>l.carta_versao
     or c->>'carta_fingerprint'<>p_resultado->>'carta_fingerprint'
     or r->>'contrato'<>p_resultado->>'contrato_versao'
     or r->>'contrato_fingerprint'<>p_resultado->>'contrato_fingerprint'
     or p_resultado->>'formula_fingerprint'<>esperado then
    raise exception 'writer v3: selo ou gate divergente';
  end if;
  if round(((p_resultado->>'bonus_pe')::numeric + (p_resultado->>'bonus_fisico_total')::numeric
       + (p_resultado->>'bonus_posicao')::numeric + (p_resultado->>'bonus_playstyle_1')::numeric
       + (p_resultado->>'bonus_playstyle_2')::numeric + (p_resultado->>'bonus_ia')::numeric),4)
       <> (p_resultado->>'bonus_total')::numeric then
    raise exception 'writer v3: total diverge das parcelas';
  end if;
  resultado_fp:=encode(extensions.digest(convert_to(jsonb_build_object(
    'linha_id',l.id,'card_id',l.card_id,'funcao_id',l.funcao_id,'resultado',p_resultado,
    'regua',r->>'contrato_fingerprint','carta',c->>'carta_fingerprint','formula',esperado)::text,'UTF8'),'sha256'),'hex');
  insert into clube_novo.build_bonificador(
    id,bonus_pe,bonus_fisico_total,bonus_posicao,bonus_playstyle_1,bonus_playstyle_2,bonus_ia,
    bonus_outros,bonus_total,contrato_versao,contrato_fingerprint,carta_versao,carta_fingerprint,
    formula_fingerprint,resultado_fingerprint,bonus_fisico_detalhe,motor_versao,b_corpo,b_pe_ruim,
    b_estilo,b_total,faltou,entrada_bonificador_fingerprint)
  values(nextval('clube_novo.build_bonificador_id_seq'::regclass),
    (p_resultado->>'bonus_pe')::numeric,(p_resultado->>'bonus_fisico_total')::numeric,
    (p_resultado->>'bonus_posicao')::numeric,(p_resultado->>'bonus_playstyle_1')::numeric,
    (p_resultado->>'bonus_playstyle_2')::numeric,(p_resultado->>'bonus_ia')::numeric,
    coalesce(p_resultado->'bonus_outros','{}'::jsonb),(p_resultado->>'bonus_total')::numeric,
    r->>'contrato',r->>'contrato_fingerprint',l.carta_versao,l.carta_fingerprint,esperado,
    resultado_fp,p_resultado->'bonus_fisico_detalhe',p_resultado->>'motor_versao',
    (p_resultado->>'bonus_fisico_total')::numeric,(p_resultado->>'bonus_pe')::numeric,
    ((p_resultado->>'bonus_playstyle_1')::numeric+(p_resultado->>'bonus_playstyle_2')::numeric),
    (p_resultado->>'bonus_total')::numeric,'{}',c->>'carta_fingerprint') returning id into resultado_id;
  update clube_novo.build_linha_card set build_bonificador_id=resultado_id,
    bonificador_motor_versao=p_resultado->>'motor_versao',bonificador_contrato_versao=r->>'contrato',
    snapshot_bonificador_fingerprint=resultado_fp,atualizado_em=clock_timestamp() where id=l.id;
  return jsonb_build_object('readback','ok','gravado',true,'idempotente',false,
    'build_linha_card_id',l.id,'build_bonificador_id',resultado_id,
    'carta_versao',l.carta_versao,'carta_fingerprint',l.carta_fingerprint,'resultado_fingerprint',resultado_fp);
end $function$;
revoke all on function public.gravar_build_bonificador_v3(jsonb) from public,anon,authenticated;
grant execute on function public.gravar_build_bonificador_v3(jsonb) to service_role;
commit;
