-- Boxes comerciais extraidas da resposta que o proprio jogo mantem em memoria.
-- PlayerVariationDetail.bin continua sendo variacao da carta e nao participa
-- da identidade nem do agrupamento comercial de uma box.

alter table clube_novo.box_contexto_contratacao_v1
  add column if not exists agente_jogo_id bigint,
  add column if not exists fim_oferta timestamptz;

create unique index if not exists box_contexto_agente_jogo_uidx
  on clube_novo.box_contexto_contratacao_v1(agente_jogo_id)
  where agente_jogo_id is not null;

create table if not exists clube_novo.box_leitor_endereco_jogo_v1 (
  leitor_versao text not null,
  executavel_versao text not null,
  executavel_sha256 text not null check (executavel_sha256 ~ '^[0-9a-f]{64}$'),
  campo text not null,
  origem_objeto text not null,
  endereco_ou_offset text not null,
  largura_ou_layout text not null,
  derivacao text not null,
  validacao text not null,
  ativo boolean not null default true,
  primary key (leitor_versao,campo)
);

comment on table clube_novo.box_leitor_endereco_jogo_v1 is
  'Contrato fisico versionado usado pelo Extrator de boxes. Registra onde e como cada campo e lido no codigo/memoria do jogo.';

insert into clube_novo.box_leitor_endereco_jogo_v1
  (leitor_versao,executavel_versao,executavel_sha256,campo,origem_objeto,endereco_ou_offset,largura_ou_layout,derivacao,validacao)
values
  ('boxes-cmd-get-myclub-agentlist-v1','6.0.0.0','a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4','raiz','eFootball.exe','base+0x86c9fc0','ponteiro UInt64','G=[base+0x86c9fc0]; A=[G+0x28]; B=[A+0x20]','ponteiros de usuario e releitura estavel'),
  ('boxes-cmd-get-myclub-agentlist-v1','6.0.0.0','a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4','vetor_agentes','objeto B','B+0/B+8/B+0x10','vetor MSVC; stride 0x238','inicio, fim e capacidade da resposta convertida','limites alinhados, no maximo 1000 agentes e releitura estavel'),
  ('boxes-cmd-get-myclub-agentlist-v1','6.0.0.0','a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4','agente_id','agente convertido','+0x08','UInt64; 8 bytes','agent_id bruto +0x00 convertido por 0x1445d7d70 para +0x08','positivo e unico na captura'),
  ('boxes-cmd-get-myclub-agentlist-v1','6.0.0.0','a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4','titulo','agente convertido','+0x68','std::string MSVC x64; 32 bytes','title bruto +0x50 lido por 0x1457eb210 e convertido por 0x1445d7d70','UTF-8, nao vazio, ate 2048 bytes e releitura estavel'),
  ('boxes-cmd-get-myclub-agentlist-v1','6.0.0.0','a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4','inicio_epoch','agente convertido','+0x1c','UInt32; 4 bytes','start_date bruto +0xc8 convertido por 0x1445d7d70','zero vira NULL; demais valores viram timestamptz'),
  ('boxes-cmd-get-myclub-agentlist-v1','6.0.0.0','a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4','fim_epoch','agente convertido','+0x24','UInt32; 4 bytes','expiration_date bruto +0xcc convertido por 0x1445d7d70','zero vira NULL; demais valores viram timestamptz'),
  ('boxes-cmd-get-myclub-agentlist-v1','6.0.0.0','a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4','pickup_list','agente convertido','+0xe8','vetor MSVC; stride 0xf8; card_id +0x08 UInt64','pickup_list bruto +0x128; parser 0x1457eb210; conversor 0x1445d7d70','card_id existe em carta_jogo e cabecalho permanece estavel'),
  ('boxes-cmd-get-myclub-agentlist-v1','6.0.0.0','a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4','banner_a_pickup_list','agente convertido','+0x200','vetor MSVC; stride 0xf0; card_id +0x08 UInt64','banner_a_pickup_list bruto +0x250; parser 0x1457eb210; conversor 0x1445d7d70','card_id existe em carta_jogo e cabecalho permanece estavel'),
  ('boxes-cmd-get-myclub-agentlist-v1','6.0.0.0','a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4','banner_c_pickup_list','agente convertido','+0x218','vetor MSVC; stride 0xf0; card_id +0x08 UInt64','banner_c_pickup_list bruto +0x268; parser 0x1457eb210; conversor 0x1445d7d70','card_id existe em carta_jogo e cabecalho permanece estavel')
on conflict (leitor_versao,campo) do update set
  executavel_versao=excluded.executavel_versao,
  executavel_sha256=excluded.executavel_sha256,
  origem_objeto=excluded.origem_objeto,
  endereco_ou_offset=excluded.endereco_ou_offset,
  largura_ou_layout=excluded.largura_ou_layout,
  derivacao=excluded.derivacao,
  validacao=excluded.validacao,
  ativo=true;

create table if not exists clube_novo.box_captura_jogo_v1 (
  captura_id uuid primary key,
  capturado_em timestamptz not null,
  aplicado_em timestamptz not null default now(),
  executavel_sha256 text not null,
  leitor_versao text not null,
  payload_sha256 text not null unique,
  payload jsonb not null,
  estado_anterior jsonb not null,
  resultado jsonb not null
);

create table if not exists clube_novo.box_agente_captura_jogo_v1 (
  captura_id uuid not null references clube_novo.box_captura_jogo_v1(captura_id) on delete restrict,
  agente_jogo_id bigint not null,
  titulo text not null,
  inicio_epoch bigint,
  fim_epoch bigint,
  primary key (captura_id,agente_jogo_id)
);

create table if not exists clube_novo.box_agente_card_captura_jogo_v1 (
  captura_id uuid not null,
  agente_jogo_id bigint not null,
  card_id text not null references clube_novo.carta_jogo(card_id),
  ordem integer not null check (ordem > 0),
  primary key (captura_id,agente_jogo_id,card_id),
  unique (captura_id,agente_jogo_id,ordem),
  foreign key (captura_id,agente_jogo_id)
    references clube_novo.box_agente_captura_jogo_v1(captura_id,agente_jogo_id) on delete restrict
);

create or replace view clube_novo.box_sincronizacao_jogo_ordem_v1
with (security_invoker=true) as
select a.payload_sha256 as fingerprint,
  jsonb_build_object('boxes',coalesce((
    select jsonb_agg(jsonb_build_object(
      'nome',b.item->>'titulo',
      'cards',coalesce((select jsonb_agg(jsonb_build_object('card_id',c.card_id) order by c.ordem)
                        from clube_novo.box_agente_card_captura_jogo_v1 c
                        where c.captura_id=a.captura_id and c.agente_jogo_id=(b.item->>'agente_id')::bigint),'[]'::jsonb)
    ) order by b.ord)
    from jsonb_array_elements(a.payload->'boxes') with ordinality b(item,ord)
  ),'[]'::jsonb)) as payload
from clube_novo.box_captura_jogo_v1 a;

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
  v_box_id bigint;
  v_previous jsonb;
  v_result jsonb;
  v_boxes integer;
  v_links integer;
begin
  if p is null or p->>'schema' <> 'clubef-boxes-jogo-runtime-v1'
     or p->>'leitor_versao' <> 'boxes-cmd-get-myclub-agentlist-v1'
     or p->>'fonte' <> 'jogo:CmdGetMyclubAgentlist'
     or p->>'cobertura' <> 'lista_completa_retornada_por_CmdGetMyclubAgentlist'
     or p->>'executavel_sha256' <> 'a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4'
     or jsonb_typeof(p->'boxes') <> 'array' or jsonb_array_length(p->'boxes') not between 1 and 1000 then
    raise exception 'captura de boxes recusada: contrato fisico invalido' using errcode='22023';
  end if;
  begin v_capture := (p->>'captura_id')::uuid; v_when := (p->>'capturado_em')::timestamptz;
  exception when others then raise exception 'captura de boxes recusada: identidade ou horario invalido' using errcode='22023'; end;
  if v_when < now()-interval '30 minutes' or v_when > now()+interval '5 minutes' then
    raise exception 'captura de boxes recusada: leitura fora da janela operacional' using errcode='22023';
  end if;
  v_hash := encode(extensions.digest(convert_to(p::text,'UTF8'),'sha256'),'hex');
  select resultado into v_result from clube_novo.box_captura_jogo_v1 where captura_id=v_capture;
  if found then return v_result || jsonb_build_object('idempotente',true); end if;
  if exists(select 1 from clube_novo.box_captura_jogo_v1 where payload_sha256=v_hash) then
    raise exception 'captura de boxes recusada: payload ja usado com outra identidade' using errcode='23505';
  end if;
  if exists(select 1 from jsonb_array_elements(p->'boxes') b
            where jsonb_typeof(b)<>'object' or coalesce(b->>'agente_id','') !~ '^[1-9][0-9]*$'
               or nullif(btrim(b->>'titulo'),'') is null or length(b->>'titulo')>2048
               or jsonb_typeof(b->'cartas')<>'array' or jsonb_array_length(b->'cartas')<1) then
    raise exception 'captura de boxes recusada: agente, titulo ou cartas invalidos' using errcode='22023';
  end if;
  if exists(select 1 from (select b->>'agente_id' id,count(*) from jsonb_array_elements(p->'boxes') b group by 1 having count(*)>1) q) then
    raise exception 'captura de boxes recusada: agente duplicado' using errcode='22023';
  end if;
  if exists(select 1 from jsonb_array_elements(p->'boxes') b
            cross join lateral jsonb_array_elements_text(b->'cartas') c(card_id)
            where c.card_id !~ '^[1-9][0-9]*$' or not exists(select 1 from clube_novo.carta_jogo j where j.card_id=c.card_id)) then
    raise exception 'captura de boxes recusada: card ausente da tabela fisica' using errcode='23503';
  end if;
  if exists(select 1 from jsonb_array_elements(p->'boxes') b
            cross join lateral (select c.card_id,count(*) from jsonb_array_elements_text(b->'cartas') c(card_id) group by 1 having count(*)>1) d) then
    raise exception 'captura de boxes recusada: card duplicado no agente' using errcode='22023';
  end if;

  perform pg_advisory_xact_lock(hashtextextended('clube_novo.boxes.jogo',0));
  select coalesce(jsonb_agg(to_jsonb(x) order by x.box_id),'[]'::jsonb) into v_previous
  from clube_novo.box_contexto_contratacao_v1 x where x.estado_box='em_andamento';
  v_boxes := jsonb_array_length(p->'boxes');
  select count(*) into v_links from jsonb_array_elements(p->'boxes') b cross join lateral jsonb_array_elements_text(b->'cartas');
  v_result := jsonb_build_object('estado','aplicado','captura_id',v_capture,'boxes',v_boxes,'vinculos',v_links,'fonte','jogo:CmdGetMyclubAgentlist');
  insert into clube_novo.box_captura_jogo_v1(captura_id,capturado_em,executavel_sha256,leitor_versao,payload_sha256,payload,estado_anterior,resultado)
  values(v_capture,v_when,p->>'executavel_sha256',p->>'leitor_versao',v_hash,p,v_previous,v_result);

  for v_box in select value from jsonb_array_elements(p->'boxes') loop
    insert into clube_novo.box_agente_captura_jogo_v1(captura_id,agente_jogo_id,titulo,inicio_epoch,fim_epoch)
    values(v_capture,(v_box->>'agente_id')::bigint,btrim(v_box->>'titulo'),nullif(v_box->>'inicio_epoch','')::bigint,nullif(v_box->>'fim_epoch','')::bigint);
    select box_id into v_box_id from clube_novo.box_contexto_contratacao_v1 where agente_jogo_id=(v_box->>'agente_id')::bigint;
    if v_box_id is null then
      select coalesce(max(box_id),0)+1 into v_box_id from clube_novo.box_contexto_contratacao_v1;
      insert into clube_novo.box_contexto_contratacao_v1(box_id,box_nome,estado_box,status_origem,origem_fingerprint,capturado_em,oferta_fonte,data_oferta,agente_jogo_id,fim_oferta)
      values(v_box_id,btrim(v_box->>'titulo'),'em_andamento','atual',v_hash,v_when,'jogo:CmdGetMyclubAgentlist',case when coalesce((v_box->>'inicio_epoch')::bigint,0)>0 then to_timestamp((v_box->>'inicio_epoch')::bigint)::date end,(v_box->>'agente_id')::bigint,case when coalesce((v_box->>'fim_epoch')::bigint,0)>0 then to_timestamp((v_box->>'fim_epoch')::bigint) end);
    else
      update clube_novo.box_contexto_contratacao_v1 set box_nome=btrim(v_box->>'titulo'),estado_box='em_andamento',status_origem='atual',origem_fingerprint=v_hash,capturado_em=v_when,oferta_fonte='jogo:CmdGetMyclubAgentlist',data_oferta=case when coalesce((v_box->>'inicio_epoch')::bigint,0)>0 then to_timestamp((v_box->>'inicio_epoch')::bigint)::date end,fim_oferta=case when coalesce((v_box->>'fim_epoch')::bigint,0)>0 then to_timestamp((v_box->>'fim_epoch')::bigint) end where box_id=v_box_id;
      delete from clube_novo.box_card_em_andamento_v1 where box_id=v_box_id;
    end if;
    for v_card in select value from jsonb_array_elements_text(v_box->'cartas') with ordinality order by ordinality loop
      insert into clube_novo.box_agente_card_captura_jogo_v1(captura_id,agente_jogo_id,card_id,ordem)
      select v_capture,(v_box->>'agente_id')::bigint,v_card,ordinality from jsonb_array_elements_text(v_box->'cartas') with ordinality where value=v_card;
      insert into clube_novo.box_card_em_andamento_v1(box_id,card_id,capturado_em) values(v_box_id,v_card,v_when);
    end loop;
  end loop;

  delete from clube_novo.box_card_em_andamento_v1 m using clube_novo.box_contexto_contratacao_v1 x
  where x.box_id=m.box_id and x.estado_box='em_andamento'
    and (x.oferta_fonte='https://efhub.com/pt-BR' or (x.oferta_fonte='jogo:CmdGetMyclubAgentlist' and not exists(select 1 from jsonb_array_elements(p->'boxes') b where (b->>'agente_id')::bigint=x.agente_jogo_id)));
  update clube_novo.box_contexto_contratacao_v1 x set estado_box='finalizada',status_origem='anterior',capturado_em=v_when
  where x.estado_box='em_andamento' and (x.oferta_fonte='https://efhub.com/pt-BR' or (x.oferta_fonte='jogo:CmdGetMyclubAgentlist' and not exists(select 1 from jsonb_array_elements(p->'boxes') b where (b->>'agente_id')::bigint=x.agente_jogo_id)));
  return v_result;
end
$function$;

revoke all on function clube_novo.sincronizar_boxes_jogo_v1(jsonb) from public,anon,authenticated;
grant execute on function clube_novo.sincronizar_boxes_jogo_v1(jsonb) to service_role;
revoke all on clube_novo.box_leitor_endereco_jogo_v1,clube_novo.box_captura_jogo_v1,clube_novo.box_agente_captura_jogo_v1,clube_novo.box_agente_card_captura_jogo_v1,clube_novo.box_sincronizacao_jogo_ordem_v1 from public,anon,authenticated;

create or replace view clube_novo.carta_box_oferta_v1
with (security_invoker=true) as
select m.card_id,x.box_id,x.box_nome,x.estado_box,x.data_oferta,x.origem_fingerprint
from clube_novo.box_card_em_andamento_v1 m
join clube_novo.box_contexto_contratacao_v1 x on x.box_id=m.box_id
where x.oferta_fonte is not null
  and x.oferta_fonte<>'https://efhub.com/pt-BR'
  and nullif(btrim(x.box_nome),'') is not null;

do $block$
declare v_sql text;
begin
  v_sql := pg_get_functiondef('clube_novo.site_novo_boxes_em_andamento_calculo_v1(text,text,integer,integer,integer)'::regprocedure);
  if strpos(v_sql,'clube_novo.box_sincronizacao_efhub_v1')=0 then
    raise exception 'funcao publica de boxes sem a origem antiga esperada';
  end if;
  v_sql := replace(v_sql,'clube_novo.box_sincronizacao_efhub_v1','clube_novo.box_sincronizacao_jogo_ordem_v1');
  v_sql := replace(v_sql,'and x.oferta_fonte is not null','and x.oferta_fonte=''jogo:CmdGetMyclubAgentlist''');
  execute v_sql;
end
$block$;

comment on view clube_novo.carta_box_oferta_v1 is
  'Leitura de boxes comerciais comprovadas; exclui a antiga fonte externa e os rotulos fisicos de variacao.';
comment on function clube_novo.sincronizar_boxes_jogo_v1(jsonb) is
  'Aplica atomica e idempotentemente a lista completa de boxes lida do jogo conforme box_leitor_endereco_jogo_v1.';
