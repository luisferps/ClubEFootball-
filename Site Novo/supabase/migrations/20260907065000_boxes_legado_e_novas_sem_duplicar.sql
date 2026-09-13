-- O histórico de boxes é o acervo preservado do legado. A leitura física do
-- jogo cobre somente a lista atualmente carregada em CmdGetMyclubAgentlist.
-- Uma box atual já cadastrada por outra fonte é reconhecida pelo título e
-- permanece intacta; somente títulos inéditos são criados pela fonte do jogo.

create table if not exists clube_novo.box_acervo_legado_v1 (
  acervo_versao text primary key,
  origem_preservada text not null,
  arquivo text not null,
  sha256 text not null check (sha256 ~ '^[0-9a-f]{64}$'),
  boxes_esperadas integer not null check (boxes_esperadas > 0),
  vinculos_esperados integer not null check (vinculos_esperados > 0),
  conferido_em timestamptz not null default now()
);

comment on table clube_novo.box_acervo_legado_v1 is
  'Manifesto da base histórica fixa de boxes copiada do legado; não é reconstruída pelo jogo atual.';

do $seed$
declare
  v_source constant text := 'legado:SITE-ATUAL-EXATO-2026-08-24; sha256=ec5aaaef830ea03fbea3983037b4eaa9ab1014d25f6a7f082336d59d9255bbae';
  v_hash constant text := 'ec5aaaef830ea03fbea3983037b4eaa9ab1014d25f6a7f082336d59d9255bbae';
  v_base bigint;
  v_boxes integer;
  v_links integer;
begin
  perform pg_advisory_xact_lock(hashtextextended('clube_novo.boxes.legado',0));

  -- Estes três registros não pertencem ao acervo canônico copiado. Eles ficam
  -- preservados para auditoria, mas sem fonte pública.
  update clube_novo.box_contexto_contratacao_v1
  set oferta_fonte=null
  where estado_box='finalizada'
    and oferta_fonte like 'BOXHIST corrigido preservado%'
    and (
      box_nome like 'National Team Selection T%rkiye 23 Mar ''26'
      or box_nome like 'POTM Brasileir%o Betano 19 Mar ''26'
      or box_nome like 'POTM Trendyol S%per Lig 19 Mar ''26'
    );

  update clube_novo.box_contexto_contratacao_v1
  set oferta_fonte=v_source,origem_fingerprint=v_hash
  where estado_box='finalizada'
    and oferta_fonte like 'BOXHIST corrigido preservado%';

  select coalesce(max(box_id),0) into v_base
  from clube_novo.box_contexto_contratacao_v1;

  with seed(box_nome,data_oferta,ids) as (values
    ('Daily Bonus 2027'::text,null::date,array[
      '105867185797302','105867185851044','105867185858673','105867454305172',
      '105867454312689','105867454313810','105867454344792','106787114104779',
      '88045755827674','88045755866499','88045755964125']::text[]),
    ('English League Selection 13 Aug ''26'::text,'2026-08-13'::date,array[
      '105873896745385','105873896750438','105873896751326','105873896755947',
      '105873896760682','105873896763633','105873896766735','105873896771214',
      '105873896774572','105873896778628','105873896779262']::text[]),
    ('eFootball Webstore'::text,null::date,array[
      '88045755861057','88045755867302']::text[])
  ), missing as (
    select s.*,row_number() over(order by s.box_nome) rn
    from seed s
    where not exists (
      select 1 from clube_novo.box_contexto_contratacao_v1 x
      where x.box_nome=s.box_nome and x.estado_box='finalizada'
        and x.oferta_fonte=v_source
    )
  )
  insert into clube_novo.box_contexto_contratacao_v1
    (box_id,box_nome,estado_box,status_origem,origem_fingerprint,oferta_fonte,data_oferta)
  select v_base+rn,box_nome,'finalizada','anterior',v_hash,v_source,data_oferta
  from missing;

  with seed(box_nome,ids) as (values
    ('Daily Bonus 2027'::text,array[
      '105867185797302','105867185851044','105867185858673','105867454305172',
      '105867454312689','105867454313810','105867454344792','106787114104779',
      '88045755827674','88045755866499','88045755964125']::text[]),
    ('English League Selection 13 Aug ''26'::text,array[
      '105873896745385','105873896750438','105873896751326','105873896755947',
      '105873896760682','105873896763633','105873896766735','105873896771214',
      '105873896774572','105873896778628','105873896779262']::text[]),
    ('eFootball Webstore'::text,array['88045755861057','88045755867302']::text[])
  )
  insert into clube_novo.box_card_em_andamento_v1(box_id,card_id)
  select x.box_id,c.card_id
  from seed s
  join clube_novo.box_contexto_contratacao_v1 x
    on x.box_nome=s.box_nome and x.estado_box='finalizada' and x.oferta_fonte=v_source
  cross join lateral unnest(s.ids) c(card_id)
  on conflict do nothing;

  insert into clube_novo.box_acervo_legado_v1
    (acervo_versao,origem_preservada,arquivo,sha256,boxes_esperadas,vinculos_esperados,conferido_em)
  values
    ('boxes-historicas-legado-v1','SITE-ATUAL-EXATO-2026-08-24',
     '7-VARREDURA-DO-JOGO/dados/boxes-historicas-legado.json',v_hash,1023,6708,now())
  on conflict(acervo_versao) do update set
    origem_preservada=excluded.origem_preservada,
    arquivo=excluded.arquivo,
    sha256=excluded.sha256,
    boxes_esperadas=excluded.boxes_esperadas,
    vinculos_esperados=excluded.vinculos_esperados,
    conferido_em=excluded.conferido_em;

  select count(*) into v_boxes
  from clube_novo.box_contexto_contratacao_v1
  where estado_box='finalizada' and oferta_fonte=v_source;
  select count(*) into v_links
  from clube_novo.box_card_em_andamento_v1 m
  join clube_novo.box_contexto_contratacao_v1 x using(box_id)
  where x.estado_box='finalizada' and x.oferta_fonte=v_source;
  if v_boxes <> 1023 or v_links <> 6708 then
    raise exception 'acervo legado divergente: % boxes e % vinculos',v_boxes,v_links;
  end if;
end
$seed$;

revoke all on clube_novo.box_acervo_legado_v1 from public,anon,authenticated;
grant select on clube_novo.box_acervo_legado_v1 to service_role;

create or replace function clube_novo.sincronizar_boxes_jogo_v1(p jsonb)
returns jsonb
language plpgsql
security definer
set search_path to ''
as $function$
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
  if p is null or p->>'schema' <> 'clubef-boxes-jogo-runtime-v1'
     or p->>'leitor_versao' <> 'boxes-cmd-get-myclub-agentlist-v1'
     or p->>'fonte' <> 'jogo:CmdGetMyclubAgentlist'
     or p->>'cobertura' <> 'lista_completa_retornada_por_CmdGetMyclubAgentlist'
     or p->>'executavel_sha256' <> 'a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4'
     or jsonb_typeof(p->'boxes') <> 'array'
     or jsonb_array_length(p->'boxes') not between 1 and 1000 then
    raise exception 'captura de boxes recusada: contrato fisico invalido' using errcode='22023';
  end if;

  begin
    v_capture := (p->>'captura_id')::uuid;
    v_when := (p->>'capturado_em')::timestamptz;
  exception when others then
    raise exception 'captura de boxes recusada: identidade ou horario invalido' using errcode='22023';
  end;
  if v_when < now()-interval '30 minutes' or v_when > now()+interval '5 minutes' then
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
      -- A box já existe entre as atuais. A captura fica registrada, mas não
      -- troca fonte, cards, estado, datas ou identidade do registro existente.
      v_recognized := v_recognized + 1;
      continue;
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
              then to_timestamp((v_box->>'inicio_epoch')::bigint)::date end,
         (v_box->>'agente_id')::bigint,
         case when coalesce((v_box->>'fim_epoch')::bigint,0)>0
              then to_timestamp((v_box->>'fim_epoch')::bigint) end);
      v_new := v_new + 1;
    else
      update clube_novo.box_contexto_contratacao_v1
      set box_nome=btrim(v_box->>'titulo'),estado_box='em_andamento',status_origem='atual',
          origem_fingerprint=v_hash,capturado_em=v_when,
          oferta_fonte='jogo:CmdGetMyclubAgentlist',
          data_oferta=case when coalesce((v_box->>'inicio_epoch')::bigint,0)>0
                           then to_timestamp((v_box->>'inicio_epoch')::bigint)::date end,
          fim_oferta=case when coalesce((v_box->>'fim_epoch')::bigint,0)>0
                          then to_timestamp((v_box->>'fim_epoch')::bigint) end
      where box_id=v_box_id;
      delete from clube_novo.box_card_em_andamento_v1 where box_id=v_box_id;
      v_updated := v_updated + 1;
    end if;

    insert into clube_novo.box_card_em_andamento_v1(box_id,card_id,capturado_em)
    select v_box_id,value,v_when
    from jsonb_array_elements_text(v_box->'cartas');
  end loop;

  delete from clube_novo.box_card_em_andamento_v1 m
  using clube_novo.box_contexto_contratacao_v1 x
  where x.box_id=m.box_id
    and x.estado_box='em_andamento'
    and x.oferta_fonte='jogo:CmdGetMyclubAgentlist'
    and not exists(
      select 1 from jsonb_array_elements(p->'boxes') b
      where (b->>'agente_id')::bigint=x.agente_jogo_id
    );
  update clube_novo.box_contexto_contratacao_v1 x
  set estado_box='finalizada',status_origem='anterior',capturado_em=v_when
  where x.estado_box='em_andamento'
    and x.oferta_fonte='jogo:CmdGetMyclubAgentlist'
    and not exists(
      select 1 from jsonb_array_elements(p->'boxes') b
      where (b->>'agente_id')::bigint=x.agente_jogo_id
    );
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
    'historico','legado'
  );
  update clube_novo.box_captura_jogo_v1
  set resultado=v_result
  where captura_id=v_capture;
  return v_result;
end
$function$;

revoke all on function clube_novo.sincronizar_boxes_jogo_v1(jsonb)
  from public,anon,authenticated;
grant execute on function clube_novo.sincronizar_boxes_jogo_v1(jsonb)
  to service_role;

comment on function clube_novo.sincronizar_boxes_jogo_v1(jsonb) is
  'Registra a captura atual de CmdGetMyclubAgentlist, reconhece boxes atuais já cadastradas sem alterá-las, cria somente títulos novos e atualiza/encerra apenas registros pertencentes à própria fonte do jogo. O histórico vem do legado.';
