CREATE OR REPLACE FUNCTION clube_novo.sincronizar_boxes_jogo_v1(p jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_capture uuid;
  v_when timestamptz;
  v_hash text;
  v_box jsonb;
  v_card text;
  v_order bigint;
  v_box_id bigint;
  v_existing_title_id bigint;
  v_previous jsonb;
  v_result jsonb;
  v_boxes integer;
  v_links integer;
  v_new integer := 0;
  v_recognized integer := 0;
  v_updated integer := 0;
  v_closed integer := 0;
begin
  if p is null or p->>'schema' is distinct from 'clubef-boxes-jogo-runtime-v1'
     or p->>'leitor_versao' is distinct from 'boxes-cmd-get-myclub-agentlist-v1'
     or p->>'fonte' is distinct from 'jogo:CmdGetMyclubAgentlist'
     or p->>'cobertura' is distinct from 'lista_completa_retornada_por_CmdGetMyclubAgentlist'
     or p->>'executavel_sha256' is distinct from 'a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4'
     or jsonb_typeof(p->'boxes') is distinct from 'array'
     or jsonb_array_length(p->'boxes') not between 1 and 1000 then
    raise exception 'captura de boxes recusada: contrato fisico invalido' using errcode='22023';
  end if;

  begin
    v_capture := (p->>'captura_id')::uuid;
    v_when := (p->>'capturado_em')::timestamptz;
  exception when others then
    raise exception 'captura de boxes recusada: identidade ou horario invalido' using errcode='22023';
  end;
  if v_capture is null or v_when is null or v_when < now()-interval '30 minutes' or v_when > now()+interval '5 minutes' then
    raise exception 'captura de boxes recusada: leitura fora da janela operacional' using errcode='22023';
  end if;

  v_hash := encode(extensions.digest(convert_to(p::text,'UTF8'),'sha256'),'hex');
  select resultado into v_result
  from clube_novo.box_captura_jogo_v1
  where captura_id=v_capture;
  if found then
    return v_result || jsonb_build_object('idempotente',true);
  end if;
  if exists(select 1 from clube_novo.box_captura_jogo_v1 where payload_sha256=v_hash) then
    raise exception 'captura de boxes recusada: payload ja usado com outra identidade' using errcode='23505';
  end if;
  if exists(
    select 1 from jsonb_array_elements(p->'boxes') b
    where jsonb_typeof(b)<>'object'
       or coalesce(b->>'agente_id','') !~ '^[1-9][0-9]*$'
       or nullif(btrim(b->>'titulo'),'') is null
       or length(b->>'titulo')>2048
       or jsonb_typeof(b->'cartas')<>'array'
       or jsonb_array_length(b->'cartas')<1
  ) then
    raise exception 'captura de boxes recusada: agente, titulo ou cartas invalidos' using errcode='22023';
  end if;
  if exists(
    select 1 from (
      select b->>'agente_id' id,count(*)
      from jsonb_array_elements(p->'boxes') b
      group by 1 having count(*)>1
    ) q
  ) then
    raise exception 'captura de boxes recusada: agente duplicado' using errcode='22023';
  end if;
  if exists(
    select 1 from (
      select lower(regexp_replace(btrim(b->>'titulo'),'\s+',' ','g')) titulo,count(*)
      from jsonb_array_elements(p->'boxes') b
      group by 1 having count(*)>1
    ) q
  ) then
    raise exception 'captura de boxes recusada: titulo duplicado' using errcode='22023';
  end if;
  if exists(
    select 1 from jsonb_array_elements(p->'boxes') b
    cross join lateral jsonb_array_elements_text(b->'cartas') c(card_id)
    where c.card_id !~ '^[1-9][0-9]*$'
       or not exists(select 1 from clube_novo.carta_jogo j where j.card_id=c.card_id)
  ) then
    raise exception 'captura de boxes recusada: card ausente da tabela fisica' using errcode='23503';
  end if;
  if exists(
    select 1 from jsonb_array_elements(p->'boxes') b
    cross join lateral (
      select c.card_id,count(*)
      from jsonb_array_elements_text(b->'cartas') c(card_id)
      group by 1 having count(*)>1
    ) d
  ) then
    raise exception 'captura de boxes recusada: card duplicado no agente' using errcode='22023';
  end if;

  perform pg_advisory_xact_lock(hashtextextended('clube_novo.boxes.jogo',0));
  lock table clube_novo.box_contexto_contratacao_v1 in share row exclusive mode;
  if exists(select 1 from clube_novo.box_captura_jogo_v1 where capturado_em>v_when) then
    raise exception 'Existe captura de boxes mais recente';
  end if;
  select coalesce(jsonb_agg(to_jsonb(x) order by x.box_id),'[]'::jsonb)
  into v_previous
  from clube_novo.box_contexto_contratacao_v1 x
  where x.estado_box='em_andamento';

  v_boxes := jsonb_array_length(p->'boxes');
  select count(*) into v_links
  from jsonb_array_elements(p->'boxes') b
  cross join lateral jsonb_array_elements_text(b->'cartas');

  insert into clube_novo.box_captura_jogo_v1
    (captura_id,capturado_em,executavel_sha256,leitor_versao,payload_sha256,payload,estado_anterior,resultado)
  values
    (v_capture,v_when,p->>'executavel_sha256',p->>'leitor_versao',v_hash,p,v_previous,
     jsonb_build_object('estado','recebido','captura_id',v_capture));

  for v_box in select value from jsonb_array_elements(p->'boxes') loop
    insert into clube_novo.box_agente_captura_jogo_v1
      (captura_id,agente_jogo_id,titulo,inicio_epoch,fim_epoch)
    values
      (v_capture,(v_box->>'agente_id')::bigint,btrim(v_box->>'titulo'),
       nullif(v_box->>'inicio_epoch','')::bigint,nullif(v_box->>'fim_epoch','')::bigint);

    for v_card,v_order in
      select value,ordinality
      from jsonb_array_elements_text(v_box->'cartas') with ordinality
      order by ordinality
    loop
      insert into clube_novo.box_agente_card_captura_jogo_v1
        (captura_id,agente_jogo_id,card_id,ordem)
      values
        (v_capture,(v_box->>'agente_id')::bigint,v_card,v_order);
    end loop;

    v_box_id := null;
    v_existing_title_id := null;
    select x.box_id into v_box_id
    from clube_novo.box_contexto_contratacao_v1 x
    where x.agente_jogo_id=(v_box->>'agente_id')::bigint;

    if v_box_id is null then
      select x.box_id into v_existing_title_id
      from clube_novo.box_contexto_contratacao_v1 x
      where x.estado_box='em_andamento'
        and x.oferta_fonte is distinct from 'jogo:CmdGetMyclubAgentlist'
        and lower(regexp_replace(btrim(x.box_nome),'\s+',' ','g')) =
            lower(regexp_replace(btrim(v_box->>'titulo'),'\s+',' ','g'))
      order by x.box_id
      limit 1;
    end if;

    if v_box_id is null and v_existing_title_id is not null then
      -- A captura comercial atual assume o contexto reconhecido sem duplicar a box.
      v_box_id := v_existing_title_id;
      v_recognized := v_recognized + 1;
    end if;

    if v_box_id is null then
      select coalesce(max(box_id),0)+1 into v_box_id
      from clube_novo.box_contexto_contratacao_v1;
      insert into clube_novo.box_contexto_contratacao_v1
        (box_id,box_nome,estado_box,status_origem,origem_fingerprint,capturado_em,
         oferta_fonte,data_oferta,agente_jogo_id,fim_oferta)
      values
        (v_box_id,btrim(v_box->>'titulo'),'em_andamento','atual',v_hash,v_when,
         'jogo:CmdGetMyclubAgentlist',
         case when coalesce((v_box->>'inicio_epoch')::bigint,0)>0
              then (to_timestamp((v_box->>'inicio_epoch')::bigint) at time zone 'UTC')::date end,
         (v_box->>'agente_id')::bigint,
         case when coalesce((v_box->>'fim_epoch')::bigint,0)>0
              then to_timestamp((v_box->>'fim_epoch')::bigint) end);
      v_new := v_new + 1;
    else
      update clube_novo.box_contexto_contratacao_v1
      set box_nome=btrim(v_box->>'titulo'),estado_box='em_andamento',status_origem='atual',
          origem_fingerprint=v_hash,capturado_em=v_when,
          oferta_fonte='jogo:CmdGetMyclubAgentlist',
          agente_jogo_id=(v_box->>'agente_id')::bigint,
          data_oferta=case when coalesce((v_box->>'inicio_epoch')::bigint,0)>0
                           then (to_timestamp((v_box->>'inicio_epoch')::bigint) at time zone 'UTC')::date end,
          fim_oferta=case when coalesce((v_box->>'fim_epoch')::bigint,0)>0
                          then to_timestamp((v_box->>'fim_epoch')::bigint) end
      where box_id=v_box_id;
      delete from clube_novo.box_card_em_andamento_v1 where box_id=v_box_id;
      if v_existing_title_id is null then v_updated := v_updated + 1; end if;
    end if;

    insert into clube_novo.box_card_em_andamento_v1(box_id,card_id,capturado_em)
    select v_box_id,value,v_when
    from jsonb_array_elements_text(v_box->'cartas');
  end loop;

  -- Ausencia numa sessao nao comprova encerramento de outras fontes.
  -- Fim oficial comprovado encerra sem apagar participantes historicos.
  update clube_novo.box_contexto_contratacao_v1 x
  set estado_box='finalizada',status_origem='anterior'
  where x.estado_box='em_andamento' and x.fim_oferta is not null
    and x.fim_oferta<=now();
  get diagnostics v_closed = row_count;

  v_result := jsonb_build_object(
    'estado','aplicado',
    'captura_id',v_capture,
    'boxes_lidas',v_boxes,
    'vinculos_lidos',v_links,
    'boxes_novas',v_new,
    'boxes_reconhecidas',v_recognized,
    'boxes_atualizadas',v_updated,
    'boxes_encerradas',v_closed,
    'fonte','jogo:CmdGetMyclubAgentlist',
    'historico','vinculos_preservados'
  );
  update clube_novo.box_captura_jogo_v1
  set resultado=v_result
  where captura_id=v_capture;
  return v_result;
end
$function$;

CREATE OR REPLACE FUNCTION clube_novo.boxes_leitura_atualizar_v1()
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
 SET statement_timeout TO '50s'
 SET jit TO 'off'
AS $function$
DECLARE revisao bigint; BEGIN
 IF NOT pg_try_advisory_xact_lock(hashtext('clube_novo.boxes_leitura_pronta_v1')) THEN RETURN false; END IF;
 IF EXISTS(SELECT 1 FROM clube_novo.box_contexto_contratacao_v1 WHERE estado_box='em_andamento' AND fim_oferta<=now()) THEN
 UPDATE clube_novo.box_contexto_contratacao_v1 SET estado_box='finalizada',status_origem='anterior'
 WHERE estado_box='em_andamento' AND fim_oferta IS NOT NULL AND fim_oferta<=now();
 END IF;
 SELECT solicitada INTO revisao FROM clube_novo.boxes_leitura_revisao_v1 WHERE id AND solicitada>aplicada;
 IF revisao IS NULL THEN RETURN false; END IF;
 REFRESH MATERIALIZED VIEW CONCURRENTLY clube_novo.boxes_leitura_pronta_v1;
 UPDATE clube_novo.boxes_leitura_revisao_v1 SET aplicada=revisao,atualizada_em=clock_timestamp() WHERE id;
 RETURN true;
END $function$
;
