-- Rollback cirúrgico da cobertura de estilo_ia. Não toca em tabelas de domínio,
-- dados extraídos, legado, motor, UI ou arquivos do jogo.
begin;
set local lock_timeout = '5s';
set local statement_timeout = '30s';

create or replace function clube_novo.obter_pedido_leitura_tipado_ativo()
returns jsonb language plpgsql security invoker set search_path = clube_novo, pg_temp as $$
declare pedido jsonb; cid text;
begin
 pedido:=clube_novo.obter_pedido_leitura_tipado_sem_revisao_v1(); cid:=pedido->>'contrato_id';
 if cid is null or cid='' then raise exception 'pedido tipado sem contrato_id'; end if;
 if not exists(select 1 from clube_novo.contrato_leitura_politica_revisao where contrato_id=cid) then raise exception 'pedido tipado sem política de aprovação interna'; end if;
 if not exists(select 1 from clube_novo.contrato_leitura_catalogo_fisico where contrato_id=cid) then raise exception 'pedido tipado sem cobertura de catálogo'; end if;
 if not exists(select 1 from clube_novo.contrato_leitura_projecao_cartas where contrato_id=cid) then raise exception 'pedido tipado sem projeção canônica de cartas'; end if;
 if exists (
   select 1 from clube_novo.contrato_leitura_familia f left join clube_novo.contrato_leitura_escritor_dominio e
     on e.contrato_id=f.contrato_id and e.chave_familia=f.chave_familia and e.ativo
   where f.contrato_id=cid and f.obrigatoria and e.escritor_id is null
 ) then raise exception 'pedido tipado sem escritor declarativo para família obrigatória'; end if;
 if exists (
   select 1 from clube_novo.contrato_leitura_escritor_dominio e
   where e.contrato_id=cid and e.ativo and not exists (select 1 from clube_novo.contrato_leitura_escritor_destino d where d.escritor_id=e.escritor_id and d.ativo)
 ) then raise exception 'pedido tipado com escritor sem destino declarado'; end if;
 return pedido || jsonb_build_object(
  'politica_revisao',(select jsonb_build_object('revisao_humana_obrigatoria',p.revisao_humana_obrigatoria,'cobertura_aprovada',p.cobertura_aprovada,'carga_autorizada',p.carga_autorizada,'promocao_snapshot_autorizada',p.promocao_snapshot_autorizada,'decisao',p.decisao,'proveniencia',p.proveniencia,'atualizado_em',p.atualizado_em) from clube_novo.contrato_leitura_politica_revisao p where p.contrato_id=cid),
  'catalogos_fisicos',(select coalesce(jsonb_agg(jsonb_build_object('schema',catalogo_schema,'table',catalogo_tabela,'modo_validacao',modo_validacao,'artefato_fisico',artefato_fisico,'coluna_chave_fisica',coluna_chave_fisica,'colunas_chave_canonica',colunas_chave_canonica,'papel_fonte',papel_fonte,'familia_dependencia',familia_dependencia,'check_dependencia',check_dependencia,'proveniencia',proveniencia) order by catalogo_tabela),'[]'::jsonb) from clube_novo.contrato_leitura_catalogo_fisico where contrato_id=cid),
  'projecoes_cartas',(select coalesce(jsonb_agg(jsonb_build_object('chave_campo',chave_campo,'artefato_fisico',artefato_fisico,'coluna_fisica',coluna_fisica,'destino_schema',destino_schema,'destino_tabela',destino_tabela,'destino_coluna',destino_coluna,'tipo_valor',tipo_valor,'proveniencia',proveniencia) order by chave_campo),'[]'::jsonb) from clube_novo.contrato_leitura_projecao_cartas where contrato_id=cid),
  'escritores_dominio',(select coalesce(jsonb_agg(jsonb_build_object('escritor_id',e.escritor_id,'familia',e.chave_familia,'versao',e.versao_escritor,'schema_envelope',e.schema_envelope,'identidade_canonica',e.identidade_canonica,'operacao',e.operacao,'destinos',(select coalesce(jsonb_agg(jsonb_build_object('destino_id',d.destino_id,'schema',d.destino_schema,'tabela',d.destino_tabela,'operacao',d.operacao,'colunas_chave',d.colunas_chave,'colunas_escrita',d.colunas_escrita,'tipos_colunas',d.tipos_colunas,'exige_procedencia',d.exige_procedencia,'ordem_lote',d.ordem_lote,'proveniencia',d.proveniencia) order by d.ordem_lote,d.destino_tabela),'[]'::jsonb) from clube_novo.contrato_leitura_escritor_destino d where d.escritor_id=e.escritor_id and d.ativo),'proveniencia',e.proveniencia) order by e.chave_familia),'[]'::jsonb) from clube_novo.contrato_leitura_escritor_dominio e where e.contrato_id=cid and e.ativo)
 );
end; $$;

drop view if exists clube_novo.catalogo_cobertura_extrator_v1;

update clube_novo.contrato_leitura_jogo
   set versao_contrato='r2-fontes-catalogo-v1',
       fingerprint_contrato_sha256=clube_novo.fingerprint_material_contrato_leitura(contrato_id)
 where contrato_id='clubef-dt870-2026-r1';

alter table clube_novo.contrato_leitura_catalogo_fisico
  drop constraint if exists contrato_leitura_catalogo_fisico_estado_cobertura_check;
alter table clube_novo.contrato_leitura_catalogo_fisico
  drop column if exists chave_resultado_leitura,
  drop column if exists familias_impactadas,
  drop column if exists aprovacao_aplicacao_habilitada,
  drop column if exists evidencia_enumeracao,
  drop column if exists motivo_cobertura,
  drop column if exists estado_cobertura;

commit;
