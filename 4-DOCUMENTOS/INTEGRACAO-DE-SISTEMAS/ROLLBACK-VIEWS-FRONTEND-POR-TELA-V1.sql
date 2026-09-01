begin;

drop view if exists public.frontend_ficha_v1;
drop view if exists public.frontend_busca_v1;
drop view if exists public.frontend_home_v1;
drop view if exists public.frontend_boxes_v1;
drop index if exists clube_novo.carta_jogo_frontend_busca_v1_fts_idx;
drop index if exists clube_novo.carta_jogo_frontend_box_v1_idx;
drop policy if exists frontend_view_owner_select_v1
  on clube_novo.atributo_ordem_otimizador;
drop policy if exists frontend_view_owner_select_v1
  on clube_novo.carta_posicao_principal_jogo;
drop policy if exists frontend_view_owner_select_v1
  on clube_novo.carta_pe_jogo;
drop policy if exists frontend_view_owner_select_v1
  on clube_novo.carta_playstyle_jogo;
drop function if exists clube_novo.frontend_normalizar_texto_v1(text);

do $rollback_owner$
begin
  if exists (
    select 1
    from pg_catalog.pg_roles
    where rolname = 'clube_frontend_view_owner'
  ) then
    execute 'drop owned by clube_frontend_view_owner';
  end if;
end
$rollback_owner$;

drop role if exists clube_frontend_view_owner;

notify pgrst, 'reload schema';

commit;
