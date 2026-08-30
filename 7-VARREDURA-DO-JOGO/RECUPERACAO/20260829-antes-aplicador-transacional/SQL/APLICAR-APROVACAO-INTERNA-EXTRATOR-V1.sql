-- Aprovação pertence ao próprio fluxo do Extrator: relatório → aceite na UI → aplicação em clube_novo.
-- O pedido continua a determinar toda a leitura; a aprovação jamais limita a varredura.
begin;
create table if not exists clube_novo.contrato_leitura_politica_revisao (
 contrato_id text primary key references clube_novo.contrato_leitura_jogo(contrato_id) on delete restrict,
 revisao_humana_obrigatoria boolean not null default true,
 cobertura_aprovada boolean not null default false,
 carga_autorizada boolean not null default false,
 promocao_snapshot_autorizada boolean not null default false,
 decisao jsonb not null default '{}'::jsonb, proveniencia text not null, atualizado_em timestamptz not null default now(), check(jsonb_typeof(decisao)='object')
);
insert into clube_novo.contrato_leitura_politica_revisao (contrato_id,revisao_humana_obrigatoria,cobertura_aprovada,carga_autorizada,promocao_snapshot_autorizada,decisao,proveniencia)
select contrato_id,true,false,false,false,jsonb_build_object('estado','aguarda_aprovacao_no_extrator','regra','a UI do Extrator apresenta o pacote de revisão; aceite interno autoriza somente o pacote selado'),'fluxo interno do Extrator'
from clube_novo.contrato_leitura_jogo where estado='ativo'
on conflict (contrato_id) do update set decisao=jsonb_build_object('estado','aguarda_aprovacao_no_extrator','regra','a UI do Extrator apresenta o pacote de revisão; aceite interno autoriza somente o pacote selado'),proveniencia='fluxo interno do Extrator',atualizado_em=now();
create or replace function clube_novo.obter_pedido_leitura_tipado_ativo()
returns jsonb language plpgsql security invoker set search_path = clube_novo, pg_temp as $$
declare pedido jsonb; cid text;
begin
 pedido:=clube_novo.obter_pedido_leitura_tipado_sem_revisao_v1(); cid:=pedido->>'contrato_id';
 if cid is null or cid='' then raise exception 'pedido tipado sem contrato_id'; end if;
 if not exists(select 1 from clube_novo.contrato_leitura_politica_revisao where contrato_id=cid) then raise exception 'pedido tipado sem política de aprovação interna'; end if;
 if not exists(select 1 from clube_novo.contrato_leitura_catalogo_fisico where contrato_id=cid) then raise exception 'pedido tipado sem cobertura de catálogo'; end if;
 if not exists(select 1 from clube_novo.contrato_leitura_projecao_cartas where contrato_id=cid) then raise exception 'pedido tipado sem projeção canônica de cartas'; end if;
 return pedido || jsonb_build_object(
  'politica_revisao',(select jsonb_build_object('revisao_humana_obrigatoria',p.revisao_humana_obrigatoria,'cobertura_aprovada',p.cobertura_aprovada,'carga_autorizada',p.carga_autorizada,'promocao_snapshot_autorizada',p.promocao_snapshot_autorizada,'decisao',p.decisao,'proveniencia',p.proveniencia,'atualizado_em',p.atualizado_em) from clube_novo.contrato_leitura_politica_revisao p where p.contrato_id=cid),
  'catalogos_fisicos',(select coalesce(jsonb_agg(jsonb_build_object('schema',catalogo_schema,'table',catalogo_tabela,'modo_validacao',modo_validacao,'artefato_fisico',artefato_fisico,'coluna_chave_fisica',coluna_chave_fisica,'colunas_chave_canonica',colunas_chave_canonica,'papel_fonte',papel_fonte,'familia_dependencia',familia_dependencia,'check_dependencia',check_dependencia,'proveniencia',proveniencia) order by catalogo_tabela),'[]'::jsonb) from clube_novo.contrato_leitura_catalogo_fisico where contrato_id=cid),
  'projecoes_cartas',(select coalesce(jsonb_agg(jsonb_build_object('chave_campo',chave_campo,'artefato_fisico',artefato_fisico,'coluna_fisica',coluna_fisica,'destino_schema',destino_schema,'destino_tabela',destino_tabela,'destino_coluna',destino_coluna,'tipo_valor',tipo_valor,'proveniencia',proveniencia) order by chave_campo),'[]'::jsonb) from clube_novo.contrato_leitura_projecao_cartas where contrato_id=cid)
 );
end; $$;
commit;
