begin;

alter table clube_novo.build_linha_card
  add column execucao_tipo text not null default 'producao'
    check (execucao_tipo in ('producao','teste_isolado')),
  add column lote_teste_id uuid,
  add column lote_teste_semente text,
  add column lote_teste_fingerprint text,
  add column amostra_ordem smallint,
  add column sorteada_em timestamptz,
  add column estado_otimizador text not null default 'pendente'
    check (estado_otimizador in ('pendente','processando','concluido','bloqueado')),
  add column erro_otimizador text,
  add column otimizador_iniciado_em timestamptz,
  add column otimizador_finalizado_em timestamptz,
  add constraint build_linha_teste_campos_v1_check check (
    (execucao_tipo='producao' and lote_teste_id is null and amostra_ordem is null)
    or
    (execucao_tipo='teste_isolado' and lote_teste_id is not null
      and lote_teste_semente is not null and btrim(lote_teste_semente)<>''
      and lote_teste_fingerprint ~ '^[0-9a-f]{64}$'
      and amostra_ordem between 1 and 100 and sorteada_em is not null)
  );

create unique index build_linha_teste_contexto_v1_uidx
  on clube_novo.build_linha_card(lote_teste_id,card_id,funcao_id,posicao_id)
  where lote_teste_id is not null;
create index build_linha_teste_estado_v1_idx
  on clube_novo.build_linha_card(lote_teste_id,estado_otimizador)
  where lote_teste_id is not null;

create function clube_novo.bloquear_publicacao_linha_teste_v1()
returns trigger language plpgsql security invoker set search_path=''
as $$
begin
  if new.execucao_tipo='teste_isolado' and new.estado not in ('pendente','invalida') then
    raise exception 'linha de teste isolado nunca pode ser pronta ou publicada';
  end if;
  return new;
end $$;

create trigger build_linha_teste_nao_publica_v1
before insert or update on clube_novo.build_linha_card
for each row execute function clube_novo.bloquear_publicacao_linha_teste_v1();

create function public.otimizador_status_teste_v1(p_lote_id uuid)
returns jsonb language sql stable security definer set search_path=''
as $$
select jsonb_build_object(
 'contrato','otimizador_teste_100_v1','lote_id',p_lote_id,
 'fingerprint',max(lote_teste_fingerprint),'sorteada_em',min(sorteada_em),
 'cards',count(distinct card_id),'linhas',count(*),
 'pendentes',count(*) filter(where estado_otimizador='pendente'),
 'processando',count(*) filter(where estado_otimizador='processando'),
 'concluidas',count(*) filter(where estado_otimizador='concluido'),
 'bloqueadas',count(*) filter(where estado_otimizador='bloqueado'),
 'motivos',coalesce(jsonb_agg(jsonb_build_object('linha_id',id,'card_id',card_id,
             'funcao_id',funcao_id,'posicao_id',posicao_id,'motivo',erro_otimizador)
             order by id) filter(where estado_otimizador='bloqueado'),'[]'::jsonb),
 'pode_publicar',false,'modo','teste_nao_publicado')
from clube_novo.build_linha_card where lote_teste_id=p_lote_id;
$$;

create function public.otimizador_criar_amostra_teste_v1(p_lote_id uuid,p_semente text)
returns jsonb language plpgsql security definer set search_path=''
as $$
declare v_cards int; v_fp text; v_quando timestamptz:=clock_timestamp();
begin
  if p_lote_id is null or p_semente is null or btrim(p_semente)='' then
    raise exception 'lote_id e semente sao obrigatorios';
  end if;
  if exists(select 1 from clube_novo.build_linha_card where lote_teste_id=p_lote_id) then
    return public.otimizador_status_teste_v1(p_lote_id);
  end if;

  create temporary table _amostra_100 on commit drop as
  with universo as materialized (
    select c.card_id,c.extraido_em,c.extracao_id,
           public.otimizador_carta_v1(c.card_id) pacote
    from clube_novo.carta_jogo c
    order by encode(extensions.digest(p_semente||':'||c.card_id,'sha256'),'hex')
    limit 2000
  ), aptas as (
    select *,row_number() over(order by encode(extensions.digest(p_semente||':'||card_id,'sha256'),'hex')) ordem
    from universo where coalesce((pacote->'gate'->>'pode_rodar')::boolean,false)
  ) select * from aptas where ordem<=100;

  select count(*) into v_cards from _amostra_100;
  if v_cards<>100 then raise exception 'pre-voo recusado: somente % cartas aptas no universo deterministico',v_cards; end if;
  select encode(extensions.digest(p_semente||':'||string_agg(card_id,',' order by ordem),'sha256'),'hex')
    into v_fp from _amostra_100;

  insert into clube_novo.build_linha_card(
    card_id,funcao_id,posicao_id,carta_versao,carta_fingerprint,estado,pendencias,
    execucao_tipo,lote_teste_id,lote_teste_semente,lote_teste_fingerprint,
    amostra_ordem,sorteada_em,estado_otimizador)
  select a.card_id,fs.id,cp.posicao_id,
         coalesce(a.extracao_id::text,a.extraido_em::text,'sem_versao'),
         encode(extensions.digest(a.pacote::text,'sha256'),'hex'),
         'pendente',array['teste_nao_publicado','bonificador_nao_executado']::text[],
         'teste_isolado',p_lote_id,p_semente,v_fp,a.ordem,v_quando,'pendente'
  from _amostra_100 a
  join clube_novo.carta_posicao_jogo cp on cp.card_id=a.card_id and cp.nivel_aptidao>0
  join clube_novo.posicao_jogo p on p.id=cp.posicao_id and p.pode_rodar
  join clube_novo.funcao_sistema fs on fs.ativa and fs.pode_rodar
       and p.codigo_pt=any(fs.posicoes)
  order by a.ordem,fs.ordem,cp.posicao_id;

  if (select count(distinct card_id) from clube_novo.build_linha_card where lote_teste_id=p_lote_id)<>100 then
    raise exception 'fila recusada: nao preservou exatamente 100 cards unicos';
  end if;
  return public.otimizador_status_teste_v1(p_lote_id);
end $$;

create function public.otimizador_fila_teste_v1(p_lote_id uuid)
returns jsonb language sql stable security definer set search_path=''
as $$
select coalesce(jsonb_agg(jsonb_build_object(
 'linha_id',l.id,'card_id',l.card_id,'funcao_id',l.funcao_id,
 'funcao_codigo_compat',f.codigo_legado,'funcao_nome',f.rotulo,
 'posicao_id',l.posicao_id,'posicao_codigo',p.codigo_pt,'posicao_nome',p.nome_pt,
 'ordem_card',l.amostra_ordem,'estado',l.estado_otimizador,
 'carta_versao',l.carta_versao,'carta_fingerprint',l.carta_fingerprint,
 'lote_fingerprint',l.lote_teste_fingerprint,'erro',l.erro_otimizador)
 order by l.amostra_ordem,f.ordem,l.posicao_id),'[]'::jsonb)
from clube_novo.build_linha_card l
join clube_novo.funcao_sistema f on f.id=l.funcao_id
join clube_novo.posicao_jogo p on p.id=l.posicao_id
where l.lote_teste_id=p_lote_id and l.execucao_tipo='teste_isolado';
$$;

create function public.otimizador_iniciar_linha_teste_v1(p_linha_id bigint,p_lote_id uuid)
returns boolean language plpgsql security definer set search_path=''
as $$
begin
  update clube_novo.build_linha_card set estado_otimizador='processando',
    otimizador_iniciado_em=coalesce(otimizador_iniciado_em,clock_timestamp()),
    erro_otimizador=null
  where id=p_linha_id and lote_teste_id=p_lote_id and execucao_tipo='teste_isolado'
    and estado='pendente' and estado_otimizador in ('pendente','processando');
  return found;
end $$;

create function public.otimizador_concluir_linha_teste_v1(p_linha_id bigint,p_lote_id uuid,p_resultado jsonb)
returns bigint language plpgsql security definer set search_path=''
as $$
declare v_linha clube_novo.build_linha_card%rowtype; v_id bigint; v_habs integer[];
begin
  select * into v_linha from clube_novo.build_linha_card
   where id=p_linha_id and lote_teste_id=p_lote_id and execucao_tipo='teste_isolado' for update;
  if v_linha.id is null then raise exception 'linha de teste inexistente'; end if;
  if v_linha.build_otimizador_id is not null and v_linha.estado_otimizador='concluido' then
    return v_linha.build_otimizador_id;
  end if;
  select coalesce(array_agg(x::integer),'{}'::integer[]) into v_habs
    from (select jsonb_array_elements_text(coalesce(p_resultado->'habilidades','[]'::jsonb)) x limit 5) q;
  insert into clube_novo.build_otimizador(
    tecnico_id,barras,impeto_adicional_codigo,habilidades_adicionais,pontuacao,
    contrato_versao,contrato_fingerprint,carta_versao,carta_fingerprint,
    formula_fingerprint,resultado_fingerprint,motor_versao)
  values((p_resultado->>'tecnico_id')::bigint,p_resultado->'barras',null,v_habs,
    (p_resultado->>'b1')::numeric,coalesce(p_resultado#>>'{insumos,fonte}','otimizador_regua_v1'),
    p_resultado#>>'{insumos,fingerprint_ids}',v_linha.carta_versao,v_linha.carta_fingerprint,
    p_resultado->>'formula_fingerprint',encode(extensions.digest(p_resultado::text,'sha256'),'hex'),
    coalesce(p_resultado->>'motor_versao','v6')) returning id into v_id;
  update clube_novo.build_linha_card set build_otimizador_id=v_id,
    estado_otimizador='concluido',otimizador_finalizado_em=clock_timestamp(),
    otimizador_motor_versao=coalesce(p_resultado->>'motor_versao','v6'),
    otimizador_contrato_versao=coalesce(p_resultado#>>'{insumos,fonte}','otimizador_regua_v1'),
    snapshot_otimizador_fingerprint=(select resultado_fingerprint from clube_novo.build_otimizador where id=v_id),
    erro_otimizador=null
  where id=v_linha.id;
  return v_id;
end $$;

create function public.otimizador_bloquear_linha_teste_v1(p_linha_id bigint,p_lote_id uuid,p_motivo text)
returns boolean language plpgsql security definer set search_path=''
as $$
begin
  update clube_novo.build_linha_card set estado_otimizador='bloqueado',
    erro_otimizador=left(coalesce(p_motivo,'falha sem detalhe'),2000),
    otimizador_finalizado_em=clock_timestamp()
  where id=p_linha_id and lote_teste_id=p_lote_id and execucao_tipo='teste_isolado'
    and estado='pendente' and build_otimizador_id is null;
  return found;
end $$;

revoke all on function clube_novo.bloquear_publicacao_linha_teste_v1() from public,anon,authenticated;
revoke all on function public.otimizador_status_teste_v1(uuid) from public,anon,authenticated;
revoke all on function public.otimizador_criar_amostra_teste_v1(uuid,text) from public,anon,authenticated;
revoke all on function public.otimizador_fila_teste_v1(uuid) from public,anon,authenticated;
revoke all on function public.otimizador_iniciar_linha_teste_v1(bigint,uuid) from public,anon,authenticated;
revoke all on function public.otimizador_concluir_linha_teste_v1(bigint,uuid,jsonb) from public,anon,authenticated;
revoke all on function public.otimizador_bloquear_linha_teste_v1(bigint,uuid,text) from public,anon,authenticated;
grant execute on function public.otimizador_status_teste_v1(uuid),
 public.otimizador_criar_amostra_teste_v1(uuid,text),public.otimizador_fila_teste_v1(uuid),
 public.otimizador_iniciar_linha_teste_v1(bigint,uuid),
 public.otimizador_concluir_linha_teste_v1(bigint,uuid,jsonb),
 public.otimizador_bloquear_linha_teste_v1(bigint,uuid,text) to service_role;

commit;
