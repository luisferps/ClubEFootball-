-- V3.4 — `build_otimizador.id` é GENERATED ALWAYS AS IDENTITY.
-- O banco deve gerar a PK; nenhuma fórmula, peso, barra ou regra é alterada.

create or replace function public.otimizador_producao_concluir_linha_v3(
  p_lote_id uuid,
  p_linha_id bigint,
  p_reserva_token uuid,
  p_resultado jsonb
) returns jsonb
language plpgsql
security definer
set search_path=''
as $function$
declare v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_q clube_novo.otimizador_lote_producao_linha_v3%rowtype;
  v_l clube_novo.build_linha_card%rowtype; v_habilidades integer[];
  v_resultado_fp text; v_build_id bigint;
begin
  if jsonb_typeof(p_resultado)<>'object' then raise exception 'resultado do Otimizador deve ser objeto'; end if;
  select * into v_lote from clube_novo.otimizador_lote_producao_v3 where id=p_lote_id for update;
  select * into v_q from clube_novo.otimizador_lote_producao_linha_v3 where lote_id=p_lote_id and linha_id=p_linha_id for update;
  select * into v_l from clube_novo.build_linha_card where id=p_linha_id for update;
  if v_lote.id is null or v_q.linha_id is null or v_l.id is null then raise exception 'conclusão recusada: lote ou linha inexistente'; end if;
  if v_l.estado_otimizador<>'processando' or v_q.reserva_token is distinct from p_reserva_token then raise exception 'conclusão recusada: reserva não pertence ao worker'; end if;
  if p_resultado->>'card_id'<>v_l.card_id or (p_resultado->>'funcao_id')::bigint<>v_l.funcao_id or (p_resultado->>'posicao_id')::integer<>v_l.posicao_id then raise exception 'conclusão recusada: identidade da linha diverge'; end if;
  if p_resultado->>'formula_fingerprint'<>v_lote.formula_fingerprint or p_resultado->>'contrato_fingerprint'<>v_lote.contrato_fingerprint or p_resultado->>'motor_versao'<>v_lote.motor_versao or p_resultado->>'lote_fingerprint'<>v_lote.fingerprint or p_resultado->>'carta_entrada_fingerprint'<>v_q.entrada_fingerprint then raise exception 'conclusão recusada: selo divergente'; end if;
  if coalesce(p_resultado->>'impeto_condicional_codigo','')<>'' or coalesce(p_resultado->>'impeto_condicional_nivel','')<>'' then raise exception 'conclusão recusada: Ímpeto condicional continua desligado'; end if;
  if not (p_resultado ?& array['b1','barras','tecnico_id','habilidades','builds_comparadas','builds_possiveis']) then raise exception 'conclusão recusada: resultado incompleto'; end if;
  if jsonb_typeof(p_resultado->'barras')<>'object' or jsonb_typeof(p_resultado->'habilidades')<>'array' then raise exception 'conclusão recusada: build inválida'; end if;
  select coalesce(array_agg(x.valor::integer order by x.ordem),'{}'::integer[]) into v_habilidades from jsonb_array_elements_text(p_resultado->'habilidades') with ordinality x(valor,ordem);
  v_resultado_fp:=encode(extensions.digest(convert_to(p_resultado::text,'UTF8'),'sha256'),'hex');
  insert into clube_novo.build_otimizador(
    tecnico_id,barras,impeto_adicional_codigo,habilidades_adicionais,pontuacao,
    contrato_versao,contrato_fingerprint,carta_versao,carta_fingerprint,
    formula_fingerprint,resultado_fingerprint,motor_versao,builds_comparadas,builds_possiveis
  ) values (
    (p_resultado->>'tecnico_id')::bigint,p_resultado->'barras',
    nullif(p_resultado->>'impeto_adicional_codigo','')::integer,v_habilidades,(p_resultado->>'b1')::numeric,
    'otimizador_regua_v2',v_lote.contrato_fingerprint,v_l.carta_versao,v_l.carta_fingerprint,
    v_lote.formula_fingerprint,v_resultado_fp,v_lote.motor_versao,
    (p_resultado->>'builds_comparadas')::integer,(p_resultado->>'builds_possiveis')::numeric
  ) returning id into v_build_id;
  update clube_novo.build_linha_card set build_otimizador_id=v_build_id,estado_otimizador='concluido',erro_otimizador=null,otimizador_finalizado_em=clock_timestamp(),pendencias='{}'::text[],atualizado_em=clock_timestamp() where id=p_linha_id;
  update clube_novo.otimizador_lote_producao_linha_v3 set reserva_token=null,worker_id=null,finalizada_em=clock_timestamp(),resultado_fingerprint=v_resultado_fp where lote_id=p_lote_id and linha_id=p_linha_id;
  insert into clube_novo.otimizador_evento_producao_v3(lote_id,linha_id,evento,detalhe) values(p_lote_id,p_linha_id,'linha_concluida',jsonb_build_object('build_otimizador_id',v_build_id,'resultado_fingerprint',v_resultado_fp,'bonificador','pendente'));
  if v_lote.estado='rodando' and not exists(select 1 from clube_novo.otimizador_lote_producao_linha_v3 q join clube_novo.build_linha_card l on l.id=q.linha_id where q.lote_id=p_lote_id and l.estado_otimizador in ('pendente','processando')) then
    update clube_novo.otimizador_lote_producao_v3 set estado='concluido',finalizado_em=clock_timestamp(),atualizado_em=clock_timestamp() where id=p_lote_id;
    insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento) values(p_lote_id,'lote_concluido');
  end if;
  return jsonb_build_object('contrato','otimizador_fila_producao_v3','linha_id',p_linha_id,'build_otimizador_id',v_build_id,'bonificador','pendente','pode_publicar',false);
end
$function$;
