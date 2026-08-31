-- Rollback estrutural V5. Nunca apaga um lote integral nem um resultado.
-- Para reverter depois da criação de um lote integral, restaure primeiro um
-- snapshot aprovado; este arquivo falha fechado para proteger evidências.

begin;

do $$
begin
  if exists (
    select 1 from clube_novo.otimizador_lote_producao_v3 where tipo_lote='integral'
  ) then
    raise exception 'rollback V5 recusado: existe lote integral; use o snapshot recuperável, sem apagar evidência';
  end if;
end
$$;

drop function if exists public.otimizador_cartas_apresentacao_v2(text[]);
drop function if exists public.otimizador_producao_eventos_paginados_v5(uuid,integer,integer);
drop function if exists public.otimizador_producao_fila_paginada_v5(uuid,integer,integer,boolean);
drop function if exists public.otimizador_producao_controlar_preparo_v5(uuid,text);
drop function if exists public.otimizador_producao_preparar_fatia_v5(uuid,integer);
drop function if exists public.otimizador_producao_criar_lote_integral_v5(uuid,text,text);
drop function if exists public.otimizador_producao_prevoo_integral_v5();
drop function if exists public.otimizador_producao_status_v5(uuid);

alter table clube_novo.otimizador_evento_producao_v3
  drop constraint otimizador_evento_producao_v3_evento_check;
alter table clube_novo.otimizador_evento_producao_v3
  add constraint otimizador_evento_producao_v3_evento_check
  check (evento in (
    'lote_criado','lote_iniciado','lote_retomado','pausa_solicitada','lote_pausado',
    'encerramento_solicitado','lote_encerrado','linha_reservada','linha_concluida',
    'linha_bloqueada','lote_concluido','lote_falhou'
  ));

drop table if exists clube_novo.otimizador_lote_producao_candidata_v5;

drop index if exists clube_novo.build_linha_card_contexto_por_lote_v5_uidx;
drop index if exists clube_novo.build_linha_card_lote_producao_v5_idx;

alter table clube_novo.otimizador_lote_producao_linha_v3
  drop constraint if exists otimizador_lote_producao_linha_v5_linhagem_fk;
alter table clube_novo.build_linha_card
  drop constraint if exists build_linha_card_id_lote_producao_v5_key;
alter table clube_novo.build_linha_card
  drop constraint if exists build_linha_card_lote_producao_v5_fk;

alter table clube_novo.build_linha_card
  drop constraint build_linha_teste_campos_v1_check;
alter table clube_novo.build_linha_card
  add constraint build_linha_teste_campos_v1_check
  check (
    (
      execucao_tipo='producao' and lote_teste_id is null and amostra_ordem is null
    ) or (
      execucao_tipo='teste_isolado'
      and lote_teste_id is not null
      and lote_teste_semente is not null
      and btrim(lote_teste_semente)<>''
      and lote_teste_fingerprint ~ '^[0-9a-f]{64}$'
      and amostra_ordem between 1 and 100
      and sorteada_em is not null
    )
  );

alter table clube_novo.build_linha_card
  drop constraint build_linha_card_lote_estado_check;
alter table clube_novo.build_linha_card
  add constraint build_linha_card_lote_estado_check
  check (lote_estado is null or lote_estado in (
    'parado','rodando','pausando','pausado','encerrando','encerrado','concluido','falhou'
  ));

alter table clube_novo.build_linha_card drop column lote_producao_id;

create unique index build_linha_card_uma_ativa_por_contexto_uidx
  on clube_novo.build_linha_card(
    card_id,funcao_id,posicao_id,
    coalesce(impeto_condicional_codigo,-1),
    coalesce(impeto_condicional_nivel::integer,0)
  )
  where estado <> 'invalida' and execucao_tipo='producao';

alter table clube_novo.otimizador_lote_producao_v3
  drop constraint otimizador_lote_producao_v3_estado_check;
alter table clube_novo.otimizador_lote_producao_v3
  add constraint otimizador_lote_producao_v3_estado_check
  check (estado in (
    'parado','rodando','pausando','pausado','encerrando','encerrado','concluido','falhou'
  ));
alter table clube_novo.otimizador_lote_producao_v3
  drop constraint otimizador_lote_producao_v3_tipo_lote_v5_check,
  drop constraint otimizador_lote_producao_v3_preparo_v5_check,
  drop column tipo_lote,
  drop column preparo_total,
  drop column preparo_concluido;

grant execute on function public.otimizador_producao_criar_lote_v3(uuid,text,text,integer) to service_role;
grant execute on function public.otimizador_producao_fila_v3(uuid) to service_role;

commit;
