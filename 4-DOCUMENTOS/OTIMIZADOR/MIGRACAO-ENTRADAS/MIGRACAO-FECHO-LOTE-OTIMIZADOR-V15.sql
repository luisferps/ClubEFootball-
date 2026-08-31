-- V15: fecha automaticamente uma rodada de teste quando não resta linha
-- pendente nem processando. Não altera resultados, fórmulas ou seleção da fila.

begin;

create or replace function clube_novo.otimizador_fechar_lote_apos_linha_v1()
returns trigger language plpgsql security definer set search_path='' as $$
begin
  if new.lote_teste_id is null
     or new.execucao_tipo <> 'teste_isolado'
     or new.estado_otimizador not in ('concluido','bloqueado')
     or new.lote_estado not in ('rodando','pausando','pausado') then
    return null;
  end if;

  if not exists (
    select 1
    from clube_novo.build_linha_card x
    where x.lote_teste_id=new.lote_teste_id
      and x.estado_otimizador in ('pendente','processando')
  ) then
    update clube_novo.build_linha_card
       set lote_estado='concluido',
           lote_estado_atualizado_em=clock_timestamp()
     where lote_teste_id=new.lote_teste_id
       and lote_estado in ('rodando','pausando','pausado');
  end if;
  return null;
end $$;

revoke all on function clube_novo.otimizador_fechar_lote_apos_linha_v1()
  from public,anon,authenticated;

drop trigger if exists build_linha_card_fechar_lote_otimizador_v15
  on clube_novo.build_linha_card;
create trigger build_linha_card_fechar_lote_otimizador_v15
after update of estado_otimizador on clube_novo.build_linha_card
for each row
when (old.estado_otimizador is distinct from new.estado_otimizador)
execute function clube_novo.otimizador_fechar_lote_apos_linha_v1();

create or replace function public.otimizador_status_teste_v2(p_lote_id uuid)
returns jsonb language sql stable security definer set search_path='' as $$
with base as (
  select max(lote_teste_fingerprint) fingerprint,min(sorteada_em) sorteada_em,
    min(lote_estado) estado_gravado,max(lote_estado_atualizado_em) estado_atualizado_em,
    max(lote_falha) falha_lote,count(distinct card_id) cards,count(*) linhas,
    count(*) filter(where estado_otimizador='pendente') pendentes,
    count(*) filter(where estado_otimizador='processando') processando,
    count(*) filter(where estado_otimizador='concluido') concluidas,
    count(*) filter(where estado_otimizador='bloqueado') bloqueadas,
    count(*) filter(where estado_otimizador='interrompido') interrompidas,
    coalesce(jsonb_agg(jsonb_build_object(
      'linha_id',id,'card_id',card_id,'funcao_id',funcao_id,'posicao_id',posicao_id,
      'impeto_condicional_codigo',impeto_condicional_codigo,
      'impeto_condicional_nivel',impeto_condicional_nivel,
      'estado',estado_otimizador,'motivo',erro_otimizador,
      'iniciada_em',otimizador_iniciado_em) order by otimizador_iniciado_em)
      filter(where estado_otimizador='processando'),'[]'::jsonb) corrente,
    coalesce(jsonb_agg(jsonb_build_object(
      'linha_id',id,'card_id',card_id,'funcao_id',funcao_id,'posicao_id',posicao_id,
      'impeto_condicional_codigo',impeto_condicional_codigo,
      'impeto_condicional_nivel',impeto_condicional_nivel,
      'estado',estado_otimizador,'motivo',erro_otimizador) order by id)
      filter(where estado_otimizador in ('bloqueado','interrompido')),'[]'::jsonb) motivos
  from clube_novo.build_linha_card where lote_teste_id=p_lote_id
), s as (
  select base.*,case
    when estado_gravado in ('rodando','pausando','pausado')
         and linhas>0 and pendentes=0 and processando=0 then 'concluido'
    else estado_gravado end estado_lote
  from base
)
select jsonb_build_object(
  'contrato','otimizador_teste_lote_v14','lote_id',p_lote_id,'fingerprint',fingerprint,
  'sorteada_em',sorteada_em,'estado',estado_lote,'estado_lote',estado_lote,
  'estado_atualizado_em',estado_atualizado_em,'falha_lote',falha_lote,
  'cards',cards,'linhas',linhas,'pendentes',pendentes,'processando',processando,
  'concluidas',concluidas,'bloqueadas',bloqueadas,'interrompidas',interrompidas,
  'corrente',case when estado_lote='concluido' then '[]'::jsonb else corrente end,
  'motivos',motivos,
  'acoes',jsonb_build_object(
    'criar',false,
    'iniciar',estado_lote in ('parado','pausado') and pendentes>0,
    'pausar',estado_lote='rodando' and (pendentes>0 or processando>0),
    'parar',estado_lote in ('parado','rodando','pausando','pausado','falhou') and pendentes>0,
    'retomar',estado_lote in ('pausado','falhou') and pendentes>0,
    'console',estado_lote is not null),
  'confirmacao',jsonb_build_object('parar_exige_confirmacao',true),
  'pode_publicar',false,'modo','teste_nao_publicado')
from s
$$;

revoke all on function public.otimizador_status_teste_v2(uuid)
  from public,anon,authenticated;
grant execute on function public.otimizador_status_teste_v2(uuid) to service_role;

commit;
