-- O banco declara o pedido; o Extrator lê integralmente e devolve diagnóstico normalizado.
-- Não há política de aprovação manual, carga candidata ou promoção de baseline neste fluxo.
begin;

create or replace function clube_novo.obter_pedido_leitura_tipado_ativo()
returns jsonb language plpgsql security invoker set search_path = clube_novo, pg_temp as $$
declare pedido jsonb; cid text;
begin
 pedido := clube_novo.obter_pedido_leitura_tipado_sem_revisao_v1();
 cid := pedido->>'contrato_id';
 if cid is null or cid='' then raise exception 'pedido tipado sem contrato_id'; end if;
 if not exists(select 1 from clube_novo.contrato_leitura_catalogo_fisico where contrato_id=cid) then raise exception 'pedido tipado sem cobertura de catálogo'; end if;
 if not exists(select 1 from clube_novo.contrato_leitura_projecao_cartas where contrato_id=cid) then raise exception 'pedido tipado sem projeção canônica de cartas'; end if;
 return pedido || jsonb_build_object(
  'catalogos_fisicos',(select coalesce(jsonb_agg(jsonb_build_object('schema',catalogo_schema,'table',catalogo_tabela,'modo_validacao',modo_validacao,'artefato_fisico',artefato_fisico,'coluna_chave_fisica',coluna_chave_fisica,'colunas_chave_canonica',colunas_chave_canonica,'papel_fonte',papel_fonte,'familia_dependencia',familia_dependencia,'check_dependencia',check_dependencia,'proveniencia',proveniencia) order by catalogo_tabela),'[]'::jsonb) from clube_novo.contrato_leitura_catalogo_fisico where contrato_id=cid),
  'projecoes_cartas',(select coalesce(jsonb_agg(jsonb_build_object('chave_campo',chave_campo,'artefato_fisico',artefato_fisico,'coluna_fisica',coluna_fisica,'destino_schema',destino_schema,'destino_tabela',destino_tabela,'destino_coluna',destino_coluna,'tipo_valor',tipo_valor,'proveniencia',proveniencia) order by chave_campo),'[]'::jsonb) from clube_novo.contrato_leitura_projecao_cartas where contrato_id=cid)
 );
end; $$;

drop table if exists clube_novo.contrato_leitura_politica_revisao;
commit;
