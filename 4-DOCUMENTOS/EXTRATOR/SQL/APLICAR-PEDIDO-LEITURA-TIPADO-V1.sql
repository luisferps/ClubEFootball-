-- Expõe um pedido integralmente tipado sem substituir o pedido V1 ainda usado
-- pelo fluxo legado. Nenhum dado do jogo é inserido ou atualizado.
begin;

create or replace function clube_novo.obter_pedido_leitura_tipado_ativo()
returns jsonb
language plpgsql
set search_path to 'clube_novo','pg_temp'
as $$
declare base jsonb; cid text;
begin
  base := clube_novo.obter_pedido_leitura_contrato_ativo();
  cid := base->>'contrato_id';
  if cid is null then raise exception 'pedido V1 sem contrato_id'; end if;
  if exists (select 1 from clube_novo.contrato_leitura_campo where contrato_id=cid and ativo and (expected_type='' or normalizador_id='' or schema_payload='{}'::jsonb)) then
    raise exception 'pedido tipado recusado: campo sem tipo/normalizador/schema';
  end if;
  if exists (select 1 from clube_novo.contrato_leitura_familia where contrato_id=cid and obrigatoria and (papeis_fonte='[]'::jsonb or schema_payload='{}'::jsonb)) then
    raise exception 'pedido tipado recusado: família obrigatória incompleta';
  end if;
  return base || jsonb_build_object(
    'contrato_formato','pedido_leitura_tipado_v1',
    'familias',coalesce((select jsonb_agg(jsonb_build_object('chave_familia',f.chave_familia,'leitor_id',f.leitor_id,'versao_leitor',f.versao_leitor,'schema_payload',f.schema_payload,'tipo_saida',f.tipo_saida,'normalizador_id',f.normalizador_id,'versao_normalizador',f.versao_normalizador,'identidade',f.identidade,'papeis_fonte',f.papeis_fonte,'precedencia_fontes',f.precedencia_fontes,'catalogos_requeridos',f.catalogos_requeridos,'comparacao_ativa',f.comparacao_ativa,'obrigatoria',f.obrigatoria) order by f.chave_familia) from clube_novo.contrato_leitura_familia f where f.contrato_id=cid),'[]'::jsonb),
    'expectativas',coalesce((select jsonb_agg(jsonb_build_object('familia',e.chave_familia,'metrica',e.chave_metrica,'valor',e.valor_esperado,'comparador',e.comparador,'obrigatoria',e.obrigatoria) order by e.chave_familia,e.chave_metrica) from clube_novo.contrato_leitura_expectativa e where e.contrato_id=cid),'[]'::jsonb),
    'localizadores_fontes',coalesce((select jsonb_agg(jsonb_build_object('papel_fonte',l.papel_fonte,'ordem',l.ordem,'template_caminho',l.template_caminho,'plataforma',l.plataforma,'obrigatorio',l.obrigatorio,'sha256_cpk',l.sha256_cpk) order by l.papel_fonte,l.ordem) from clube_novo.contrato_leitura_fonte_localizador l where l.contrato_id=cid),'[]'::jsonb),
    'arquivos',coalesce((select jsonb_agg(jsonb_build_object('arquivo_id',a.arquivo_id,'papel_fonte',a.papel_fonte,'arquivo',a.arquivo,'cpk',a.cpk,'versao_arquivo',a.versao_arquivo,'sha256_arquivo',a.sha256_arquivo,'tamanho_registro',a.tamanho_registro,'prefixo_bytes',a.prefixo_bytes,'decodificador',a.decodificador,'leitor_id',a.leitor_id,'versao_leitor',a.versao_leitor,'formato_saida',a.formato_saida,'tipo_saida',a.tipo_saida,'serializacao_saida',a.serializacao_saida,'obrigatorio',a.obrigatorio) order by a.papel_fonte,a.arquivo) from clube_novo.contrato_leitura_arquivo a where a.contrato_id=cid),'[]'::jsonb),
    'campos',coalesce((select jsonb_agg(jsonb_build_object('chave_campo',f.chave_campo,'chave_familia',f.chave_familia,'arquivo_id',f.arquivo_id,'entidade_destino',f.entidade_destino,'tipo_leitura',f.tipo_leitura,'byte_offset',f.byte_offset,'bit_inicio',f.bit_inicio,'largura_bits',f.largura_bits,'largura_bytes',f.largura_bytes,'endianness',f.endianness,'codificacao',f.codificacao,'transformacao',f.transformacao,'catalogo_schema',f.catalogo_schema,'catalogo_tabela',f.catalogo_tabela,'catalogo_chave',f.catalogo_chave,'requisito',f.requisito,'proveniencia',f.proveniencia_mapa_assunto,'prova',f.prova,'status_base',f.status_prova,'expected_type',f.expected_type,'normalizador_id',f.normalizador_id,'versao_normalizador',f.versao_normalizador,'schema_payload',f.schema_payload,'identidade_estavel',f.identidade_estavel,'fk_destino',f.fk_destino,'nulidade',f.nulidade,'serializacao_saida',f.serializacao_saida) order by f.chave_campo) from clube_novo.contrato_leitura_campo f where f.contrato_id=cid and f.ativo and f.status_prova in ('comprovado','convencao_aprovada')),'[]'::jsonb)
  );
end;
$$;

commit;
