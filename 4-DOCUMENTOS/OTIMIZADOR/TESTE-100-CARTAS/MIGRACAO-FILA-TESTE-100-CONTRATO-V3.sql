begin;

alter table clube_novo.build_linha_card
  add column otimizador_formula_fingerprint_esperado text,
  add column otimizador_contrato_fingerprint_esperado text,
  add column otimizador_motor_versao_esperada text;

create or replace function public.otimizador_status_teste_v1(p_lote_id uuid)
returns jsonb language sql stable security definer set search_path=''
as $$
with s as (
 select max(lote_teste_fingerprint) fingerprint,min(sorteada_em) sorteada_em,
  min(lote_estado) estado_lote,max(lote_estado_atualizado_em) estado_atualizado_em,
  max(lote_falha) falha_lote,count(distinct card_id) cards,count(*) linhas,
  count(*) filter(where estado_otimizador='pendente') pendentes,
  count(*) filter(where estado_otimizador='processando') processando,
  count(*) filter(where estado_otimizador='concluido') concluidas,
  count(*) filter(where estado_otimizador='bloqueado') bloqueadas,
  count(*) filter(where estado_otimizador='falhou') falhas,
  coalesce(jsonb_agg(jsonb_build_object('linha_id',id,'card_id',card_id,'funcao_id',funcao_id,
    'posicao_id',posicao_id,'estado',estado_otimizador,'motivo',erro_otimizador,
    'iniciada_em',otimizador_iniciado_em) order by otimizador_iniciado_em)
    filter(where estado_otimizador='processando'),'[]'::jsonb) corrente,
  coalesce(jsonb_agg(jsonb_build_object('linha_id',id,'card_id',card_id,'funcao_id',funcao_id,
    'posicao_id',posicao_id,'estado',estado_otimizador,'motivo',erro_otimizador)
    order by id) filter(where estado_otimizador in ('bloqueado','falhou')),'[]'::jsonb) motivos
 from clube_novo.build_linha_card where lote_teste_id=p_lote_id
)
select jsonb_build_object(
 'contrato','otimizador_teste_100_v3','lote_id',p_lote_id,'fingerprint',fingerprint,
 'sorteada_em',sorteada_em,'estado',estado_lote,'estado_lote',estado_lote,
 'estado_atualizado_em',estado_atualizado_em,'falha_lote',falha_lote,'cards',cards,'linhas',linhas,
 'pendentes',pendentes,'processando',processando,'concluidas',concluidas,'bloqueadas',bloqueadas,
 'falhas',falhas,'corrente',corrente,'motivos',motivos,
 'acoes',jsonb_build_object(
   'criar',false,
   'iniciar',estado_lote in ('parado','pausado') and pendentes>0,
   'parar',estado_lote='rodando',
   'retomar',estado_lote in ('pausado','falhou') and pendentes>0,
   'console',estado_lote is not null),
 'pode_publicar',false,'modo','teste_nao_publicado') from s;
$$;

create or replace function public.otimizador_criar_amostra_teste_v2(
 p_lote_id uuid,p_semente text,p_formula_fingerprint text,
 p_contrato_fingerprint text,p_motor_versao text)
returns jsonb language plpgsql security definer set search_path=''
as $$
declare v_cards int; v_fp text; v_quando timestamptz:=clock_timestamp();
begin
 if p_lote_id is null or nullif(btrim(p_semente),'') is null or
    nullif(btrim(p_formula_fingerprint),'') is null or nullif(btrim(p_contrato_fingerprint),'') is null or
    nullif(btrim(p_motor_versao),'') is null then raise exception 'lote, semente e selos sao obrigatorios'; end if;
 if exists(select 1 from clube_novo.build_linha_card where lote_teste_id=p_lote_id) then
   return public.otimizador_status_teste_v1(p_lote_id); end if;
 create temporary table _amostra_100 on commit drop as
 with base as materialized (
   select c.card_id,c.extraido_em,c.extracao_id
   from clube_novo.carta_jogo c
   where c.roda_motor and c.pode_rodar_vinculos
     and not exists(select 1 from clube_novo.carta_impeto_jogo ci
                    where ci.card_id=c.card_id and ci.codigo_impeto is not null)
   order by encode(extensions.digest(p_semente||':'||c.card_id,'sha256'),'hex') limit 180
 ), candidatos as materialized (
   select b.*,public.otimizador_carta_v1(b.card_id) pacote from base b
 ), aptas as (
   select *,row_number() over(order by encode(extensions.digest(p_semente||':'||card_id,'sha256'),'hex')) ordem
   from candidatos where coalesce((pacote->'gate'->>'pode_rodar')::boolean,false)
 ) select * from aptas where ordem<=100;
 select count(*) into v_cards from _amostra_100;
 if v_cards<>100 then raise exception 'pre-voo recusado: somente % cartas aptas entre 180 candidatos prefiltrados',v_cards; end if;
 select encode(extensions.digest(p_semente||':'||string_agg(card_id,',' order by ordem),'sha256'),'hex') into v_fp from _amostra_100;
 insert into clube_novo.build_linha_card(card_id,funcao_id,posicao_id,carta_versao,carta_fingerprint,
   estado,pendencias,execucao_tipo,lote_teste_id,lote_teste_semente,lote_teste_fingerprint,
   amostra_ordem,sorteada_em,estado_otimizador,lote_estado,lote_estado_atualizado_em,
   otimizador_formula_fingerprint_esperado,otimizador_contrato_fingerprint_esperado,
   otimizador_motor_versao_esperada)
 select distinct a.card_id,fs.id,px.posicao_id,coalesce(a.extracao_id::text,a.extraido_em::text,'sem_versao'),
   encode(extensions.digest(a.pacote::text,'sha256'),'hex'),'pendente',
   array['teste_nao_publicado','bonificador_nao_executado']::text[],
   'teste_isolado',p_lote_id,p_semente,v_fp,a.ordem,v_quando,'pendente','parado',v_quando,
   p_formula_fingerprint,p_contrato_fingerprint,p_motor_versao
 from _amostra_100 a
 join lateral (
   select cpp.posicao_id from clube_novo.carta_posicao_principal_jogo cpp where cpp.card_id=a.card_id
   union select cp.posicao_id from clube_novo.carta_posicao_jogo cp where cp.card_id=a.card_id and cp.nivel_aptidao>0
 ) px on true
 join clube_novo.posicao_jogo p on p.id=px.posicao_id and p.pode_rodar
 join clube_novo.funcao_sistema fs on fs.ativa and fs.pode_rodar and p.codigo_pt=any(fs.posicoes)
 order by a.ordem,fs.id,px.posicao_id;
 if (select count(distinct card_id) from clube_novo.build_linha_card where lote_teste_id=p_lote_id)<>100 then
   raise exception 'fila recusada: nao preservou exatamente 100 cards unicos'; end if;
 return public.otimizador_status_teste_v1(p_lote_id);
end $$;

revoke all on function public.otimizador_criar_amostra_teste_v2(uuid,text,text,text,text) from public,anon,authenticated;
grant execute on function public.otimizador_criar_amostra_teste_v2(uuid,text,text,text,text) to service_role;

create or replace function public.otimizador_eventos_teste_v1(p_lote_id uuid)
returns jsonb language sql stable security definer set search_path=''
as $$
select coalesce(jsonb_agg(jsonb_build_object('ordem',ordem,
 'instante',instante,'linha_id',id,'card_id',card_id,'funcao_id',funcao_id,'posicao_id',posicao_id,
 'estado',estado_otimizador,'motivo',erro_otimizador) order by instante,id),'[]'::jsonb)
from (select x.*,row_number() over(order by instante,id) ordem from
 (select *,coalesce(otimizador_finalizado_em,otimizador_iniciado_em,sorteada_em) instante
  from clube_novo.build_linha_card where lote_teste_id=p_lote_id) x) e;
$$;
revoke all on function public.otimizador_eventos_teste_v1(uuid) from public,anon,authenticated;
grant execute on function public.otimizador_eventos_teste_v1(uuid) to service_role;

commit;
