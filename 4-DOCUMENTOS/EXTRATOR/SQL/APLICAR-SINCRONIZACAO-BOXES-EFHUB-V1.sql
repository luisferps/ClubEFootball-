create table clube_novo.box_sincronizacao_efhub_v1 (
  fingerprint text primary key,
  observado_em timestamptz not null,
  aplicado_em timestamptz not null default now(),
  payload jsonb not null,
  estado_anterior jsonb not null,
  resultado jsonb not null
);
alter table clube_novo.box_sincronizacao_efhub_v1 enable row level security;
revoke all on clube_novo.box_sincronizacao_efhub_v1 from public, anon, authenticated;

create or replace function clube_novo.sincronizar_boxes_efhub_v1(p jsonb)
returns jsonb language plpgsql security invoker set search_path='' set jit=off as $$
declare
  fp text; anterior jsonb; resposta jsonb; b jsonb; id_box bigint;
  ids bigint[] := '{}'; n integer; fechadas integer; momento timestamptz;
begin
  if p is null or p->>'source_url' is distinct from 'https://efhub.com/pt-BR'
     or coalesce(p->>'html_sha256','') !~ '^[a-f0-9]{64}$'
     or coalesce(p->>'radar_fingerprint','') !~ '^[a-f0-9]{64}$'
     or jsonb_typeof(p->'boxes') is distinct from 'array' then
    raise exception 'Fonte de boxes inválida';
  end if;
  momento := (p->>'observed_at')::timestamptz;
  if momento is null or momento < now()-interval '24 hours' or momento > now()+interval '5 minutes' then
    raise exception 'Home fora da validade de aplicação';
  end if;
  n := jsonb_array_length(p->'boxes');
  if n not between 1 and 100 then raise exception 'Lista vazia ou inválida'; end if;
  if exists(select 1 from jsonb_array_elements(p->'boxes') x where
    coalesce(btrim(x->>'nome'),'')='' or jsonb_typeof(x->'cards') is distinct from 'array') then
    raise exception 'Box inválida';
  end if;
  if (select count(distinct lower(btrim(x->>'nome'))) from jsonb_array_elements(p->'boxes') x) <> n then
    raise exception 'Nomes de boxes duplicados';
  end if;
  if exists(select 1 from jsonb_array_elements(p->'boxes') x where jsonb_array_length(x->'cards')=0
     or (select count(distinct c->>'card_id') from jsonb_array_elements(x->'cards') c) <> jsonb_array_length(x->'cards')) then
    raise exception 'Box vazia ou cards duplicados';
  end if;
  if exists(select 1 from jsonb_array_elements(p->'boxes') x cross join lateral jsonb_array_elements(x->'cards') c
    where coalesce(c->>'card_id','') !~ '^[1-9][0-9]*$' or coalesce(btrim(c->>'box_fisica'),'')=''
       or coalesce(c->>'record_sha256','') !~ '^[a-f0-9]{64}$') then
    raise exception 'Vínculo físico inválido';
  end if;
  if exists(select 1 from jsonb_array_elements(p->'boxes') x cross join lateral jsonb_array_elements(x->'cards') c
    where not exists(select 1 from clube_novo.carta_jogo j where j.card_id::text=c->>'card_id')) then
    raise exception 'Card da home ainda não cadastrado no banco';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('clube_novo.boxes.efhub',0));
  lock table clube_novo.box_contexto_contratacao_v1 in share row exclusive mode;
  fp := encode(extensions.digest(convert_to(p::text,'UTF8'),'sha256'),'hex');
  select resultado into resposta from clube_novo.box_sincronizacao_efhub_v1 where fingerprint=fp;
  if found then return resposta || '{"reaplicacao":true}'::jsonb; end if;
  if exists(select 1 from clube_novo.box_sincronizacao_efhub_v1 where observado_em > momento) then
    raise exception 'Existe fotografia mais recente das boxes';
  end if;
  select jsonb_build_object('contextos',coalesce((select jsonb_agg(to_jsonb(x)) from clube_novo.box_contexto_contratacao_v1 x where estado_box='em_andamento'),'[]'),
      'vinculos',coalesce((select jsonb_agg(to_jsonb(m)) from clube_novo.box_card_em_andamento_v1 m join clube_novo.box_contexto_contratacao_v1 x using(box_id) where x.estado_box='em_andamento'),'[]')) into anterior;
  -- Cada retorno de uma oferta encerrada abre novo contexto, preservando seu histórico.
  for b in select value from jsonb_array_elements(p->'boxes') loop
    select box_id into id_box from clube_novo.box_contexto_contratacao_v1
     where estado_box='em_andamento' and box_nome=b->>'nome' order by box_id limit 1;
    if id_box is null then
      select coalesce(max(box_id),0)+1 into id_box from clube_novo.box_contexto_contratacao_v1;
      insert into clube_novo.box_contexto_contratacao_v1 values(id_box,b->>'nome','em_andamento','atual',fp,momento);
    else
      update clube_novo.box_contexto_contratacao_v1 set origem_fingerprint=fp,capturado_em=momento where box_id=id_box;
    end if;
    ids := array_append(ids,id_box);
    delete from clube_novo.box_card_em_andamento_v1 m where m.box_id=id_box
      and not exists(select 1 from jsonb_array_elements(b->'cards') c where c->>'card_id'=m.card_id);
    insert into clube_novo.box_card_em_andamento_v1(box_id,card_id,capturado_em)
      select id_box,c->>'card_id',momento from jsonb_array_elements(b->'cards') c
      on conflict(box_id,card_id) do update set capturado_em=excluded.capturado_em;
  end loop;
  -- Usa a mesma pontuação/percentual publicados e a mesma régua canônica da tela.
  insert into clube_novo.box_card_contratacao_snapshot_v1
   (box_id,card_id,funcao_rotulo,pontuacao_snapshot,percentual_topo_snapshot,etiqueta_codigo,etiqueta_rotulo,regua_versao_snapshot,congelado_em,origem,origem_fingerprint)
  select distinct on (m.box_id,m.card_id) m.box_id,m.card_id,v.funcao_nome,v.overall_final,v.percentual_topo,
     faixa->>'etiqueta_codigo',faixa->>'etiqueta_rotulo',faixa->>'regua_versao',momento,'Encerramento observado na home eFHUB',fp
  from clube_novo.box_card_em_andamento_v1 m
  join clube_novo.box_contexto_contratacao_v1 ctx using(box_id)
  join clube_novo.build_pontuacao_final_v2_publica_v1 v on v.card_id::text=m.card_id
  cross join lateral jsonb_array_elements(clube_novo.contratacoes_por_box_build_v1(m.card_id,v.funcao_nome,v.percentual_topo)) faixa
  where ctx.estado_box='em_andamento' and not(ctx.box_id=any(ids)) and v.percentual_topo between 0 and 100
    and (faixa->>'box_id')::bigint=m.box_id and faixa->>'origem_percentual'='dinamica'
  order by m.box_id,m.card_id,v.percentual_topo desc,v.overall_final desc,v.linha_id
  on conflict(box_id,card_id) do nothing;
  update clube_novo.box_contexto_contratacao_v1 set estado_box='finalizada',status_origem='anterior',origem_fingerprint=fp,capturado_em=momento
    where estado_box='em_andamento' and not(box_id=any(ids));
  get diagnostics fechadas = row_count;
  resposta := jsonb_build_object('fingerprint',fp,'boxes',n,'vinculos',(select count(*) from clube_novo.box_card_em_andamento_v1 where box_id=any(ids)),'encerradas',fechadas,'database_write',true);
  insert into clube_novo.box_sincronizacao_efhub_v1 values(fp,momento,now(),p,anterior,resposta);
  return resposta;
end;
$$;
revoke all on function clube_novo.sincronizar_boxes_efhub_v1(jsonb) from public, anon, authenticated;
