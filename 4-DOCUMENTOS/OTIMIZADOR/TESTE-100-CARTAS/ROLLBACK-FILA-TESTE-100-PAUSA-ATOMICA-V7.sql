begin;
create or replace function public.otimizador_iniciar_linha_teste_v1(
  p_linha_id bigint,p_lote_id uuid)
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
commit;
