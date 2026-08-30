-- Estado explícito de cobertura para catálogo cuja enumeração física ainda não
-- foi comprovada. Estrutural apenas: não grava dados de domínio, legado ou jogo.
begin;
set local lock_timeout = '5s';
set local statement_timeout = '30s';

alter table clube_novo.contrato_leitura_catalogo_fisico
  add column if not exists estado_cobertura text not null default 'nao_declarado',
  add column if not exists motivo_cobertura text,
  add column if not exists evidencia_enumeracao jsonb not null default '{}'::jsonb,
  add column if not exists aprovacao_aplicacao_habilitada boolean not null default true,
  add column if not exists familias_impactadas text[] not null default array[]::text[],
  add column if not exists chave_resultado_leitura text;

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname='contrato_leitura_catalogo_fisico_estado_cobertura_check'
      and conrelid='clube_novo.contrato_leitura_catalogo_fisico'::regclass
  ) then
    alter table clube_novo.contrato_leitura_catalogo_fisico
      add constraint contrato_leitura_catalogo_fisico_estado_cobertura_check
      check (estado_cobertura in ('nao_declarado','verificavel','coverage_nao_verificavel'));
  end if;
end $$;

comment on column clube_novo.contrato_leitura_catalogo_fisico.estado_cobertura is
  'Estado de verificabilidade da enumeração física do catálogo; não equivale a quantidade nem autoriza promoção.';
comment on column clube_novo.contrato_leitura_catalogo_fisico.aprovacao_aplicacao_habilitada is
  'Gate declarativo do contrato: false bloqueia somente as famílias declaradas em familias_impactadas.';
comment on column clube_novo.contrato_leitura_catalogo_fisico.chave_resultado_leitura is
  'Chave declarada do relatório físico/metadata; não é caminho, rótulo de domínio nem identificador de registro.';

do $$
declare rows_changed integer;
begin
  update clube_novo.contrato_leitura_catalogo_fisico
     set estado_cobertura='coverage_nao_verificavel',
         motivo_cobertura='A origem física enumarável do catálogo não foi comprovada. Bits observados em Player.bin são relações de carta e não enumeram o domínio completo.',
         evidencia_enumeracao=jsonb_build_object(
           'fonte_enumeravel_comprovada',false,
           'artefato_fisico_promovido',null,
           'metodo','eliminação por campos/arquivos com destino já comprovado; observações relacionais não promovidas a catálogo',
           'procedencia','MAPA-DO-CODIGO-DO-JOGO, pedido tipado e leitura física oficial auditados em 29/08/2026'
         ),
         aprovacao_aplicacao_habilitada=false,
         familias_impactadas=array['catalogos','relacoes']::text[],
         chave_resultado_leitura='estilos_ia'
   where contrato_id='clubef-dt870-2026-r1'
     and catalogo_schema='clube_novo'
     and catalogo_tabela='estilo_ia';
  get diagnostics rows_changed = row_count;
  if rows_changed <> 1 then
    raise exception 'esperava exatamente um contrato estilo_ia, obtive %', rows_changed;
  end if;
end $$;

-- Projeção read-only de cobertura. Ela complementa o único catálogo de
-- endereços sem duplicar nem alterar seus campos/ordem já consumidos.
create or replace view clube_novo.catalogo_cobertura_extrator_v1
with (security_invoker = true) as
select contrato_id,catalogo_schema,catalogo_tabela,modo_validacao,
       artefato_fisico,coluna_chave_fisica,colunas_chave_canonica,papel_fonte,
       familia_dependencia,check_dependencia,proveniencia,estado_cobertura,
       motivo_cobertura,evidencia_enumeracao,aprovacao_aplicacao_habilitada,
       familias_impactadas,chave_resultado_leitura
  from clube_novo.contrato_leitura_catalogo_fisico;

comment on view clube_novo.catalogo_cobertura_extrator_v1 is
  'Projeção read-only da cobertura de catálogos do contrato do Extrator; não é tabela espelho, fonte física nem destino de dados.';

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
  'catalogos_fisicos',(select coalesce(jsonb_agg(jsonb_build_object('schema',catalogo_schema,'table',catalogo_tabela,'modo_validacao',modo_validacao,'artefato_fisico',artefato_fisico,'coluna_chave_fisica',coluna_chave_fisica,'colunas_chave_canonica',colunas_chave_canonica,'papel_fonte',papel_fonte,'familia_dependencia',familia_dependencia,'check_dependencia',check_dependencia,'proveniencia',proveniencia,'estado_cobertura',estado_cobertura,'motivo_cobertura',motivo_cobertura,'evidencia_enumeracao',evidencia_enumeracao,'aprovacao_aplicacao_habilitada',aprovacao_aplicacao_habilitada,'familias_impactadas',familias_impactadas,'chave_resultado_leitura',chave_resultado_leitura) order by catalogo_tabela),'[]'::jsonb) from clube_novo.catalogo_cobertura_extrator_v1 where contrato_id=cid),
  'projecoes_cartas',(select coalesce(jsonb_agg(jsonb_build_object('chave_campo',chave_campo,'artefato_fisico',artefato_fisico,'coluna_fisica',coluna_fisica,'destino_schema',destino_schema,'destino_tabela',destino_tabela,'destino_coluna',destino_coluna,'tipo_valor',tipo_valor,'proveniencia',proveniencia) order by chave_campo),'[]'::jsonb) from clube_novo.contrato_leitura_projecao_cartas where contrato_id=cid),
  'escritores_dominio',(select coalesce(jsonb_agg(jsonb_build_object('escritor_id',e.escritor_id,'familia',e.chave_familia,'versao',e.versao_escritor,'schema_envelope',e.schema_envelope,'identidade_canonica',e.identidade_canonica,'operacao',e.operacao,'destinos',(select coalesce(jsonb_agg(jsonb_build_object('destino_id',d.destino_id,'schema',d.destino_schema,'tabela',d.destino_tabela,'operacao',d.operacao,'colunas_chave',d.colunas_chave,'colunas_escrita',d.colunas_escrita,'tipos_colunas',d.tipos_colunas,'exige_procedencia',d.exige_procedencia,'ordem_lote',d.ordem_lote,'proveniencia',d.proveniencia) order by d.ordem_lote,d.destino_tabela),'[]'::jsonb) from clube_novo.contrato_leitura_escritor_destino d where d.escritor_id=e.escritor_id and d.ativo),'proveniencia',e.proveniencia) order by e.chave_familia),'[]'::jsonb) from clube_novo.contrato_leitura_escritor_dominio e where e.contrato_id=cid and e.ativo)
 );
end; $$;

update clube_novo.contrato_leitura_jogo
   set versao_contrato='r3-estilo-ia-cobertura-failclosed-v1',
       fingerprint_contrato_sha256=clube_novo.fingerprint_material_contrato_leitura(contrato_id)
 where contrato_id='clubef-dt870-2026-r1';

commit;
