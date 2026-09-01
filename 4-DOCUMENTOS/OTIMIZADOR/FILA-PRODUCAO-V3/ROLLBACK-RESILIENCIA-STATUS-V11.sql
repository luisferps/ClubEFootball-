-- Rollback V11. Não toca cartas, resultados, estados de fila, fórmula,
-- publicação ou dados do Otimizador; remove somente a leitura-resumo V11.
-- Use apenas se a validação pós-migração falhar antes de reempacotar a UI.

begin;

revoke all on function public.otimizador_producao_fila_operacional_v1(uuid,integer,integer,text)
  from public,anon,authenticated,service_role;
revoke all on function public.otimizador_producao_controle_lote_v1(uuid)
  from public,anon,authenticated,service_role;
revoke all on function public.otimizador_producao_status_v6(uuid)
  from public,anon,authenticated,service_role;

drop function if exists public.otimizador_producao_fila_operacional_v1(uuid,integer,integer,text);
drop function if exists public.otimizador_producao_controle_lote_v1(uuid);
drop function if exists public.otimizador_producao_status_v6(uuid);

drop trigger if exists build_linha_status_otimizador_v11_delete
  on clube_novo.build_linha_card;
drop trigger if exists build_linha_status_otimizador_v11_update
  on clube_novo.build_linha_card;
drop trigger if exists build_linha_status_otimizador_v11_insert
  on clube_novo.build_linha_card;
drop function if exists clube_novo.atualizar_status_lote_otimizador_v1();
drop table if exists clube_novo.otimizador_lote_producao_status_v1;

notify pgrst, 'reload schema';

commit;
