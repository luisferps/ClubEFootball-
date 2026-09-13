with recursive destinos as (
 select distinct to_regclass(format('%I.%I',destino_schema,destino_tabela)) oid
 from clube_novo.contrato_leitura_escritor_destino where ativo
), arestas as (
 select distinct c.conrelid filho,c.confrelid pai from pg_constraint c
 join destinos a on a.oid=c.conrelid join destinos b on b.oid=c.confrelid
 where c.contype='f' and c.conrelid<>c.confrelid
), caminhos as (
 select oid,oid atual,array[oid] visitados,0 profundidade from destinos
 union all select c.oid,a.pai,c.visitados||a.pai,c.profundidade+1
 from caminhos c join arestas a on a.filho=c.atual where not a.pai=any(c.visitados)
), niveis as (select oid,max(profundidade) nivel from caminhos group by oid)
update clube_novo.contrato_leitura_escritor_destino d
 set ordem_lote=(n.nivel+1)*100+case when destino_tabela='carta_jogo' and escritor_id='extrator.envelope.dimensoes.v1' then -10 else 0 end
 from niveis n where d.ativo and n.oid=to_regclass(format('%I.%I',d.destino_schema,d.destino_tabela));
do $$ begin
 if exists(
 select 1 from pg_constraint c
 join clube_novo.contrato_leitura_escritor_destino filho on filho.ativo and c.conrelid=to_regclass(format('%I.%I',filho.destino_schema,filho.destino_tabela))
 join clube_novo.contrato_leitura_escritor_destino pai on pai.ativo and c.confrelid=to_regclass(format('%I.%I',pai.destino_schema,pai.destino_tabela))
 where c.contype='f' and c.conrelid<>c.confrelid and pai.ordem_lote>=filho.ordem_lote
 ) then raise exception 'ordem de dependências não resolvida'; end if;
end $$;
