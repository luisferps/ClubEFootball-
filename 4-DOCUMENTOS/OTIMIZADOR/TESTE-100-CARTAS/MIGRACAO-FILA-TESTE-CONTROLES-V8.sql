begin;

alter table clube_novo.build_linha_card drop constraint build_linha_card_estado_otimizador_check;
alter table clube_novo.build_linha_card add constraint build_linha_card_estado_otimizador_check
 check(estado_otimizador in ('pendente','processando','concluido','bloqueado','interrompido'));
alter table clube_novo.build_linha_card drop constraint build_linha_card_lote_estado_check;
alter table clube_novo.build_linha_card add constraint build_linha_card_lote_estado_check
 check(lote_estado is null or lote_estado in
 ('parado','rodando','pausando','pausado','encerrando','encerrado','concluido','falhou'));

create or replace function public.otimizador_controlar_lote_teste_v2(
 p_lote_id uuid,p_acao text,p_confirmado boolean default false)
returns jsonb language plpgsql security definer set search_path=''
as $$
declare v_estado text; v_corrente boolean;
begin
 perform 1 from clube_novo.build_linha_card where lote_teste_id=p_lote_id for update;
 select min(lote_estado),bool_or(estado_otimizador='processando')
 into v_estado,v_corrente from clube_novo.build_linha_card where lote_teste_id=p_lote_id;
 if v_estado is null then raise exception 'lote de teste inexistente'; end if;

 if p_acao in ('iniciar','retomar') then
   if v_estado in ('encerrando','encerrado','concluido') then
     raise exception 'lote encerrado/concluido nao pode ser retomado';
   end if;
   update clube_novo.build_linha_card set lote_estado='rodando',
    lote_estado_atualizado_em=clock_timestamp(),lote_falha=null
   where lote_teste_id=p_lote_id and estado_otimizador<>'interrompido';

 elsif p_acao='pausar' then
   update clube_novo.build_linha_card set lote_estado=case when v_corrente then 'pausando' else 'pausado' end,
    lote_estado_atualizado_em=clock_timestamp() where lote_teste_id=p_lote_id;

 elsif p_acao='confirmar_pausa' then
   if v_corrente then raise exception 'pausa ainda aguarda linha atomica corrente'; end if;
   update clube_novo.build_linha_card set lote_estado='pausado',
    lote_estado_atualizado_em=clock_timestamp() where lote_teste_id=p_lote_id;

 elsif p_acao='parar' then
   if not p_confirmado then raise exception 'parar exige confirmacao explicita da interface local'; end if;
   if v_estado in ('encerrado','concluido') then return public.otimizador_status_teste_v1(p_lote_id); end if;
   update clube_novo.build_linha_card set lote_estado=case when v_corrente then 'encerrando' else 'encerrado' end,
    lote_estado_atualizado_em=clock_timestamp() where lote_teste_id=p_lote_id;
   if not v_corrente then
     update clube_novo.build_linha_card set estado_otimizador='interrompido',
      erro_otimizador='lote encerrado pelo usuario',
      otimizador_finalizado_em=clock_timestamp(),
      pendencias=array(select distinct x from unnest(pendencias||array['teste_interrompido']) x)
     where lote_teste_id=p_lote_id and estado_otimizador='pendente';
   end if;

 elsif p_acao='confirmar_encerramento' then
   if not p_confirmado then raise exception 'confirmar encerramento exige selo local'; end if;
   if v_corrente then raise exception 'encerramento ainda aguarda linha atomica corrente'; end if;
   update clube_novo.build_linha_card set estado_otimizador='interrompido',
    erro_otimizador='lote encerrado pelo usuario',
    otimizador_finalizado_em=clock_timestamp(),
    pendencias=array(select distinct x from unnest(pendencias||array['teste_interrompido']) x)
   where lote_teste_id=p_lote_id and estado_otimizador='pendente';
   update clube_novo.build_linha_card set lote_estado='encerrado',
    lote_estado_atualizado_em=clock_timestamp() where lote_teste_id=p_lote_id;
 else raise exception 'acao invalida'; end if;
 return public.otimizador_status_teste_v1(p_lote_id);
end $$;

revoke all on function public.otimizador_controlar_lote_teste_v2(uuid,text,boolean)
 from public,anon,authenticated;
grant execute on function public.otimizador_controlar_lote_teste_v2(uuid,text,boolean) to service_role;

create or replace function public.otimizador_controlar_lote_teste_v1(p_lote_id uuid,p_acao text)
returns jsonb language plpgsql security definer set search_path=''
as $$
begin
 if p_acao='parar' then
   raise exception 'acao parar exige contrato v2 e confirmacao explicita';
 end if;
 return public.otimizador_controlar_lote_teste_v2(
   p_lote_id,case when p_acao='confirmar_pausa' then p_acao
                  when p_acao in ('iniciar','retomar') then p_acao
                  else 'pausar' end,false);
end $$;

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
  count(*) filter(where estado_otimizador='interrompido') interrompidas,
  coalesce(jsonb_agg(jsonb_build_object('linha_id',id,'card_id',card_id,'funcao_id',funcao_id,
   'posicao_id',posicao_id,'estado',estado_otimizador,'motivo',erro_otimizador,
   'iniciada_em',otimizador_iniciado_em) order by otimizador_iniciado_em)
   filter(where estado_otimizador='processando'),'[]'::jsonb) corrente,
  coalesce(jsonb_agg(jsonb_build_object('linha_id',id,'card_id',card_id,'funcao_id',funcao_id,
   'posicao_id',posicao_id,'estado',estado_otimizador,'motivo',erro_otimizador)
   order by id) filter(where estado_otimizador in ('bloqueado','interrompido')),'[]'::jsonb) motivos
 from clube_novo.build_linha_card where lote_teste_id=p_lote_id
)
select jsonb_build_object(
 'contrato','otimizador_teste_100_v8','lote_id',p_lote_id,'fingerprint',fingerprint,
 'sorteada_em',sorteada_em,'estado',estado_lote,'estado_lote',estado_lote,
 'estado_atualizado_em',estado_atualizado_em,'falha_lote',falha_lote,
 'cards',cards,'linhas',linhas,'pendentes',pendentes,'processando',processando,
 'concluidas',concluidas,'bloqueadas',bloqueadas,'interrompidas',interrompidas,
 'corrente',corrente,'motivos',motivos,
 'acoes',jsonb_build_object(
  'criar',false,
  'iniciar',estado_lote in ('parado','pausado') and pendentes>0,
  'pausar',estado_lote='rodando',
  'parar',estado_lote in ('parado','rodando','pausando','pausado','falhou') and pendentes>0,
  'retomar',estado_lote in ('pausado','falhou') and pendentes>0,
  'console',estado_lote is not null),
 'confirmacao',jsonb_build_object('parar_exige_confirmacao',true),
 'pode_publicar',false,'modo','teste_nao_publicado') from s;
$$;

commit;
