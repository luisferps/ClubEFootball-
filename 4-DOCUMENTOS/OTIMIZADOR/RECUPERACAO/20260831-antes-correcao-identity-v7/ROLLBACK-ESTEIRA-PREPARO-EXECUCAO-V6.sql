-- Rollback da esteira V6.
-- Execute somente com a esteira V6 parada: nenhum lote integral pode estar em
-- estado "rodando" com preparo pendente, pois V5 deliberadamente não calcula
-- em paralelo ao preparo.

begin;

do $rollback$
begin
  if exists (
    select 1
    from clube_novo.otimizador_lote_producao_v3
    where tipo_lote = 'integral'
      and estado = 'rodando'
      and preparo_concluido < preparo_total
  ) then
    raise exception 'rollback V6 recusado: há esteira integral ativa; pause ou conclua primeiro';
  end if;
end
$rollback$;

revoke all on function public.otimizador_producao_iniciar_esteira_v6(uuid)
  from public, anon, authenticated, service_role;
revoke all on function public.otimizador_producao_preparar_fatia_v6(uuid, integer)
  from public, anon, authenticated, service_role;
revoke all on function public.otimizador_producao_reservar_linha_v6(uuid, uuid)
  from public, anon, authenticated, service_role;
revoke all on function public.otimizador_producao_concluir_linha_v6(uuid, bigint, uuid, jsonb)
  from public, anon, authenticated, service_role;

drop function if exists public.otimizador_producao_concluir_linha_v6(uuid, bigint, uuid, jsonb);
drop function if exists public.otimizador_producao_reservar_linha_v6(uuid, uuid);
drop function if exists public.otimizador_producao_preparar_fatia_v6(uuid, integer);
drop function if exists public.otimizador_producao_iniciar_esteira_v6(uuid);

alter table clube_novo.otimizador_lote_producao_v3
  drop constraint if exists otimizador_lote_producao_v3_preparo_fingerprint_final_check;

alter table clube_novo.otimizador_lote_producao_v3
  drop column if exists preparo_fingerprint_final;

commit;
