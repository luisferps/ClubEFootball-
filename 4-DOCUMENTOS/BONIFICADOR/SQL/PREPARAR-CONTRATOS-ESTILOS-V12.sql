-- ETAPA 1: contratos V12 preparados. Nao ativa producao nem altera fila/resultados.
begin;
create or replace function clube_novo.carta_estilos_efetivos_v12(p_card_id text)
returns jsonb language sql stable security definer set search_path='' as $f$
with s as (
  select count(*) n,
    max(playstyle_id) filter(where slot_fisico=1) a,
    max(playstyle_id) filter(where slot_fisico=2) d
  from clube_novo.carta_playstyle_jogo where card_id=p_card_id
), g as (
  select *, n=2 and a is not null and d is not null and
    not(a<>256 and d<>256 and a<>d and ((a>>6)&3)=((d>>6)&3) and ((a>>6)&3) in(0,1)) as ok
  from s
), e as (
  select *,case when a<>256 and ((a>>6)&3) in(0,2) then a
    when d<>256 and ((d>>6)&3) in(0,2) then d else 256 end ataque,
    case when d<>256 and ((d>>6)&3) in(1,2) then d
    when a<>256 and ((a>>6)&3) in(1,2) then a else 256 end defesa
  from g
)
select jsonb_build_object('pode_rodar',ok,
  'falta_o_que',case when ok then '[]'::jsonb else '["estilos fisicos ausentes ou fases ambiguas"]'::jsonb end,
  'ataque_id',case when ok then ataque end,'defesa_id',case when ok then defesa end,
  'fisico_slot1_id',a,'fisico_slot2_id',d,
  'interpretacao','fase_playstyle_ataque_defesa_v1') from e;
$f$;
revoke all on function clube_novo.carta_estilos_efetivos_v12(text) from public,anon,authenticated;
grant execute on function clube_novo.carta_estilos_efetivos_v12(text) to service_role;

create or replace function public.bonificador_carta_v3(p_card_id text)
returns jsonb language sql stable security invoker set search_path='' as $f$
with b as(select public.bonificador_carta_v2(p_card_id) j),
 e as(select clube_novo.carta_estilos_efetivos_v12(p_card_id) j)
select b.j || jsonb_build_object(
  'contrato','bonificador-carta-v3',
  'pode_rodar',coalesce((b.j->>'pode_rodar')::boolean,false) and (e.j->>'pode_rodar')::boolean,
  'falta_o_que',coalesce(b.j->'falta_o_que','[]'::jsonb)||(e.j->'falta_o_que'),
  'slot1_id_jogo',e.j->'ataque_id','slot2_id_jogo',e.j->'defesa_id',
  'slot1_nome',(select p.nome_pt from clube_novo.playstyle p where p.id_jogo=(e.j->>'ataque_id')::integer),
  'slot2_nome',(select p.nome_pt from clube_novo.playstyle p where p.id_jogo=(e.j->>'defesa_id')::integer),
  'estilos_efetivos',e.j,
  'semantica_slots','1=ataque efetivo; 2=defesa efetiva; raw preservado em seus campos fisicos'
) from b cross join e;
$f$;
revoke all on function public.bonificador_carta_v3(text) from public,anon,authenticated;
grant execute on function public.bonificador_carta_v3(text) to service_role;

create or replace function public.bonificador_regua_v4()
returns jsonb language sql stable security definer set search_path='' as $f$
with p as(select * from clube_novo.bonificador_politica_estilo where versao='estilos-funcao-20260909-v1'),
b as(select public.bonificador_regua_v3()-'contrato_fingerprint' j),
e as(select b.j||jsonb_build_object(
  'contrato','bonificador-regua-v4','motor_versao','v12-0909-estilo-funcao-ativacao-v1','formula_fingerprint','4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8',
  'politica_estilo',p.politica,'politica_estilo_fingerprint',p.politica_fingerprint,
  'estado_implantacao',p.estado,
  'liberado_para_producao',p.estado='ativa',
  'pode_rodar',coalesce((b.j->>'pode_rodar')::boolean,false) and p.politica_fingerprint='7ed53bbab831180cde9d247782dd133fe072acadb69bd34871c3f83f28773dc5'
) j from b cross join p)
select e.j||jsonb_build_object('contrato_fingerprint',
  encode(extensions.digest(e.j::text,'sha256'),'hex')) from e;
$f$;
revoke all on function public.bonificador_regua_v4() from public,anon,authenticated;
grant execute on function public.bonificador_regua_v4() to service_role;

create or replace function clube_novo.exigir_producao_bonificador_v12()
returns void language plpgsql stable security definer set search_path='' as $f$
begin
  if not coalesce((public.bonificador_regua_v4()->>'liberado_para_producao')::boolean,false) then
    raise exception 'V12 preparada; ativacao produtiva e atualizacao da Maquina 2 pertencem a proxima etapa.';
  end if;
end;
$f$;
revoke all on function clube_novo.exigir_producao_bonificador_v12() from public,anon,authenticated;
grant execute on function clube_novo.exigir_producao_bonificador_v12() to service_role;

CREATE OR REPLACE FUNCTION clube_novo.validar_payload_bonificador_v12(p_resultado jsonb)
 RETURNS void
 LANGUAGE plpgsql
 STABLE
 SET search_path TO ''
AS $function$
declare
  v_soma_detalhe numeric;
  v_soma numeric;
  v_pct numeric;
  v_maximo numeric;
  v_c jsonb;
  v_bonus jsonb;
begin
  if jsonb_typeof(p_resultado)<>'object'
     or not (p_resultado ?& array[
       'build_linha_card_id','card_id','funcao_id','posicao_id','carta_versao',
       'carta_fingerprint','contrato_versao','contrato_fingerprint',
       'formula_fingerprint','motor_versao','bonus_pe','bonus_fisico_total',
       'bonus_fisico_detalhe','bonus_posicao','bonus_playstyle_1',
       'bonus_playstyle_2','bonus_ia','bonus_total','corpo_soma','corpo_pct','corpo_maximo'
     ]) then
    raise exception 'writer V10: payload incompleto';
  end if;
  if p_resultado->>'motor_versao'<>'v12-0909-estilo-funcao-ativacao-v1'
     or p_resultado->>'formula_fingerprint'<>'4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8'
     or p_resultado->>'contrato_versao'<>'bonificador-regua-v4' then
    raise exception 'writer V10: versão/fingerprint divergente';
  end if;
  if jsonb_typeof(p_resultado->'bonus_fisico_detalhe')<>'object'
     or exists (
       select 1 from jsonb_each(p_resultado->'bonus_fisico_detalhe') e
       where jsonb_typeof(e.value)<>'number'
     )
     or (select count(*) from jsonb_each(p_resultado->'bonus_fisico_detalhe'))<>12 then
    raise exception 'writer V10: detalhamento físico inválido';
  end if;
  select coalesce(sum((e.value::text)::numeric),0)
    into v_soma_detalhe
  from jsonb_each(p_resultado->'bonus_fisico_detalhe') e;
  if v_soma_detalhe<>(p_resultado->>'bonus_fisico_total')::numeric
     or (p_resultado->>'bonus_fisico_total')::numeric not between -1.5 and 1.5 then
    raise exception 'writer V10: detalhe não fecha ou físico fora da faixa';
  end if;
  v_soma:=(p_resultado->>'corpo_soma')::numeric;
  v_pct:=(p_resultado->>'corpo_pct')::numeric;
  v_maximo:=(p_resultado->>'corpo_maximo')::numeric;
  if v_maximo<=0 or v_pct not between -1 and 1
     or round(greatest(-1::numeric,least(1::numeric,v_soma/v_maximo)),4)<>v_pct then
    raise exception 'writer V10: soma, máximo e percentual físicos não fecham';
  end if;
  if round(
       (p_resultado->>'bonus_pe')::numeric+
       (p_resultado->>'bonus_fisico_total')::numeric+
       (p_resultado->>'bonus_posicao')::numeric+
       (p_resultado->>'bonus_playstyle_1')::numeric+
       (p_resultado->>'bonus_playstyle_2')::numeric+
       (p_resultado->>'bonus_ia')::numeric,4
     )<>(p_resultado->>'bonus_total')::numeric then
    raise exception 'writer V10: total diverge das parcelas';
  end if;
  v_c:=public.bonificador_carta_v3(p_resultado->>'card_id');
  if not coalesce((v_c->>'pode_rodar')::boolean,false) then raise exception 'V12: carta sem entrada apta'; end if;
  v_bonus:=clube_novo.conferir_bonus_estilo_0909_v1(
    (p_resultado->>'funcao_id')::bigint,(p_resultado->>'posicao_id')::integer,
    (v_c->>'slot1_id_jogo')::integer,(v_c->>'slot2_id_jogo')::integer);
  if not coalesce((v_bonus->>'pode_calcular')::boolean,false)
    or (p_resultado->>'bonus_playstyle_1')::numeric is distinct from (v_bonus->>'bonus_ataque')::numeric
    or (p_resultado->>'bonus_playstyle_2')::numeric is distinct from (v_bonus->>'bonus_defesa')::numeric then
    raise exception 'V12: parcelas de estilo divergem da politica aprovada';
  end if;
end
$function$
;
revoke all on function clube_novo.validar_payload_bonificador_v12(jsonb) from public,anon,authenticated;
grant execute on function clube_novo.validar_payload_bonificador_v12(jsonb) to service_role;

CREATE OR REPLACE FUNCTION public.gravar_build_bonificador_v6(p_resultado jsonb)
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
revoke all on function public.gravar_build_bonificador_v6(jsonb) from public,anon,authenticated;
grant execute on function public.gravar_build_bonificador_v6(jsonb) to service_role;

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
revoke all on function public.gravar_build_bonificador_correcao_v2(uuid,jsonb) from public,anon,authenticated;
grant execute on function public.gravar_build_bonificador_correcao_v2(uuid,jsonb) to service_role;

CREATE OR REPLACE FUNCTION public.bonificador_contexto_fila_v7(p_limit integer DEFAULT 1000, p_offset integer DEFAULT 0)
 RETURNS TABLE(build_linha_card_id bigint, card_id text, carta_nome text, carta_tipo text, carta_box text, carta_overall integer, funcao_id bigint, funcao_codigo text, funcao_nome text, posicao_id integer, posicao_codigo text, posicao_nome text, carta_versao text, carta_fingerprint text, contrato_versao text, contrato_fingerprint text, formula_fingerprint text)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
  with candidatos as materialized (
    select l.id,l.card_id,l.funcao_id,l.posicao_id,l.carta_versao,l.carta_fingerprint,
           c.nome,c.tipo,c.box,c.overall,
           case when l.criado_em>=timestamptz '2026-09-04 22:00:00+00'
                     and c.chave_tipo_carta in ('Any2W:360','Any2W:361')
                then 0 else 1 end as prioridade_grupo
    from clube_novo.build_linha_card l
    join clube_novo.carta_jogo c on c.card_id=l.card_id
    left join clube_novo.build_bonificador b on b.id=l.build_bonificador_id
    where coalesce((public.bonificador_regua_v4()->>'liberado_para_producao')::boolean,false)
      and l.execucao_tipo='producao'
      and l.lote_teste_id is null
      and not exists(select 1 from clube_novo.orcamento_revisao_linha_v1 r where r.linha_anterior_id=l.id)
      and not (l.pendencias @> array['teste_nao_publicado'::text])
      and c.roda_motor is true
      and coalesce(c.jogador_indisponivel,false)=false
      and l.carta_versao=c.extraido_em::text
      and (
        l.build_bonificador_id is null
        or b.motor_versao<>'v12-0909-estilo-funcao-ativacao-v1'
        or b.formula_fingerprint<>'4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8'
      )
    order by prioridade_grupo,c.overall desc nulls last,l.card_id,l.funcao_id,l.posicao_id,l.id
    limit least(greatest(coalesce(p_limit,1000),1),5000)
    offset greatest(coalesce(p_offset,0),0)
  ), regua as (select public.bonificador_regua_v4() valor)
  select l.id,l.card_id,l.nome,l.tipo,l.box,l.overall,l.funcao_id,
         coalesce(f.sigla,'')::text,f.rotulo,l.posicao_id,
         coalesce(p.codigo_pt,'')::text,p.nome_pt,l.carta_versao,l.carta_fingerprint,
         r.valor->>'contrato',r.valor->>'contrato_fingerprint',r.valor->>'formula_fingerprint'
  from candidatos l
  join clube_novo.funcao_sistema f on f.id=l.funcao_id
  join clube_novo.posicao_jogo p on p.id=l.posicao_id
  cross join regua r
  order by l.prioridade_grupo,l.overall desc nulls last,l.card_id,l.funcao_id,l.posicao_id,l.id
$function$
;
revoke all on function public.bonificador_contexto_fila_v7(integer,integer) from public,anon,authenticated;
grant execute on function public.bonificador_contexto_fila_v7(integer,integer) to service_role;

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
revoke all on function public.bonificador_correcao_proxima_linha_v2(uuid) from public,anon,authenticated;
grant execute on function public.bonificador_correcao_proxima_linha_v2(uuid) to service_role;

comment on function public.bonificador_regua_v4() is 'V12: regra preparada, com liberacao produtiva separada; nao substitui regua V3 nesta etapa.';
commit;

-- Contrato V3 permanece invoker e restrito a service_role.
grant select (id_jogo,nome_pt) on clube_novo.playstyle to service_role;
