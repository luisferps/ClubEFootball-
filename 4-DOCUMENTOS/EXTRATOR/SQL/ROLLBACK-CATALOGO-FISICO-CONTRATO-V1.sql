-- Rollback cirúrgico: restaura a função anterior e remove somente os metadados V1.
begin;
drop table if exists clube_novo.contrato_leitura_projecao_cartas;
drop table if exists clube_novo.contrato_leitura_catalogo_fisico;
create or replace function clube_novo.obter_pedido_leitura_tipado_ativo()
returns jsonb language plpgsql security invoker set search_path = clube_novo, pg_temp as $$
declare pedido jsonb; cid text;
begin
 pedido := clube_novo.obter_pedido_leitura_tipado_sem_revisao_v1(); cid := pedido->>'contrato_id';
 if cid is null or cid='' then raise exception 'pedido tipado sem contrato_id'; end if;
 return pedido;
end; $$;
commit;
