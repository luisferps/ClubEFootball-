begin;
alter table clube_novo.build_linha_card
  add column lote_estado text check(lote_estado is null or lote_estado in
    ('parado','rodando','pausando','pausado','concluido','falhou')),
  add column lote_estado_atualizado_em timestamptz,
  add column lote_falha text;

create or replace function public.otimizador_status_teste_v1(p_lote_id uuid)
returns jsonb language sql stable security definer set search_path=''
as $$
select jsonb_build_object(
 'contrato','otimizador_teste_100_v1','lote_id',p_lote_id,
 'fingerprint',max(lote_teste_fingerprint),'sorteada_em',min(sorteada_em),
 'estado_lote',min(lote_estado),'estado_atualizado_em',max(lote_estado_atualizado_em),
 'falha_lote',max(lote_falha),'cards',count(distinct card_id),'linhas',count(*),
 'pendentes',count(*) filter(where estado_otimizador='pendente'),
 'processando',count(*) filter(where estado_otimizador='processando'),
 'concluidas',count(*) filter(where estado_otimizador='concluido'),
 'bloqueadas',count(*) filter(where estado_otimizador='bloqueado'),
 'corrente',coalesce(jsonb_agg(jsonb_build_object('linha_id',id,'card_id',card_id,
    'funcao_id',funcao_id,'posicao_id',posicao_id,'iniciada_em',otimizador_iniciado_em)
    order by otimizador_iniciado_em) filter(where estado_otimizador='processando'),'[]'::jsonb),
 'motivos',coalesce(jsonb_agg(jsonb_build_object('linha_id',id,'card_id',card_id,
    'funcao_id',funcao_id,'posicao_id',posicao_id,'motivo',erro_otimizador)
    order by id) filter(where estado_otimizador='bloqueado'),'[]'::jsonb),
 'pode_publicar',false,'modo','teste_nao_publicado')
from clube_novo.build_linha_card where lote_teste_id=p_lote_id;
$$;

create or replace function public.otimizador_criar_amostra_teste_v1(p_lote_id uuid,p_semente text)
returns jsonb language plpgsql security definer set search_path=''
as $$
declare v_cards int; v_fp text; v_quando timestamptz:=clock_timestamp();
begin
  if p_lote_id is null or p_semente is null or btrim(p_semente)='' then raise exception 'lote_id e semente sao obrigatorios'; end if;
  if exists(select 1 from clube_novo.build_linha_card where lote_teste_id=p_lote_id) then
    return public.otimizador_status_teste_v1(p_lote_id);
  end if;
  create temporary table _amostra_100 on commit drop as
  with universo as materialized (
    select c.card_id,c.extraido_em,c.extracao_id,public.otimizador_carta_v1(c.card_id) pacote
    from clube_novo.carta_jogo c
    order by encode(extensions.digest(p_semente||':'||c.card_id,'sha256'),'hex') limit 2000
  ), aptas as (
    select *,row_number() over(order by encode(extensions.digest(p_semente||':'||card_id,'sha256'),'hex')) ordem
    from universo where coalesce((pacote->'gate'->>'pode_rodar')::boolean,false)
  ) select * from aptas where ordem<=100;
  select count(*) into v_cards from _amostra_100;
  if v_cards<>100 then raise exception 'pre-voo recusado: somente % cartas aptas',v_cards; end if;
  select encode(extensions.digest(p_semente||':'||string_agg(card_id,',' order by ordem),'sha256'),'hex') into v_fp from _amostra_100;

  insert into clube_novo.build_linha_card(card_id,funcao_id,posicao_id,carta_versao,carta_fingerprint,
    estado,pendencias,execucao_tipo,lote_teste_id,lote_teste_semente,lote_teste_fingerprint,
    amostra_ordem,sorteada_em,estado_otimizador,lote_estado,lote_estado_atualizado_em)
  select distinct a.card_id,fs.id,px.posicao_id,
    coalesce(a.extracao_id::text,a.extraido_em::text,'sem_versao'),
    encode(extensions.digest(a.pacote::text,'sha256'),'hex'),'pendente',
    array['teste_nao_publicado','bonificador_nao_executado']::text[],
    'teste_isolado',p_lote_id,p_semente,v_fp,a.ordem,v_quando,'pendente','parado',v_quando
  from _amostra_100 a
  join lateral (
    select cpp.posicao_id from clube_novo.carta_posicao_principal_jogo cpp where cpp.card_id=a.card_id
    union
    select cp.posicao_id from clube_novo.carta_posicao_jogo cp where cp.card_id=a.card_id and cp.nivel_aptidao>0
  ) px on true
  join clube_novo.posicao_jogo p on p.id=px.posicao_id and p.pode_rodar
  join clube_novo.funcao_sistema fs on fs.ativa and fs.pode_rodar and p.codigo_pt=any(fs.posicoes)
  order by a.ordem,fs.id,px.posicao_id;
  if (select count(distinct card_id) from clube_novo.build_linha_card where lote_teste_id=p_lote_id)<>100 then
    raise exception 'fila recusada: nao preservou exatamente 100 cards unicos';
  end if;
  return public.otimizador_status_teste_v1(p_lote_id);
end $$;

create function public.otimizador_controlar_lote_teste_v1(p_lote_id uuid,p_acao text)
returns jsonb language plpgsql security definer set search_path=''
as $$
declare v_estado text;
begin
  select min(lote_estado) into v_estado from clube_novo.build_linha_card where lote_teste_id=p_lote_id for update;
  if v_estado is null then raise exception 'lote de teste inexistente'; end if;
  if p_acao in ('iniciar','retomar') then
    if v_estado='concluido' then return public.otimizador_status_teste_v1(p_lote_id); end if;
    update clube_novo.build_linha_card set lote_estado='rodando',lote_estado_atualizado_em=clock_timestamp(),lote_falha=null
      where lote_teste_id=p_lote_id;
  elsif p_acao='parar' then
    update clube_novo.build_linha_card set lote_estado=case when estado_otimizador='processando' then 'pausando' else 'pausado' end,
      lote_estado_atualizado_em=clock_timestamp() where lote_teste_id=p_lote_id;
  elsif p_acao='confirmar_pausa' then
    if exists(select 1 from clube_novo.build_linha_card where lote_teste_id=p_lote_id and estado_otimizador='processando') then
      raise exception 'pausa ainda aguarda linha atomica corrente';
    end if;
    update clube_novo.build_linha_card set lote_estado='pausado',lote_estado_atualizado_em=clock_timestamp()
      where lote_teste_id=p_lote_id;
  else raise exception 'acao invalida'; end if;
  return public.otimizador_status_teste_v1(p_lote_id);
end $$;

revoke all on function public.otimizador_controlar_lote_teste_v1(uuid,text) from public,anon,authenticated;
grant execute on function public.otimizador_controlar_lote_teste_v1(uuid,text) to service_role;
commit;
