-- Catálogo único de descoberta física. É uma VIEW: não duplica estado,
-- não possui gatilho e reflete diretamente as tabelas canônicas do contrato.
create or replace view clube_novo.catalogo_endereco_leitura_extrator_v1
with (security_invoker = true) as
select
  f.contrato_id,
  fam.familia_id,
  f.chave_familia,
  f.campo_id,
  f.chave_campo,
  f.entidade_destino,
  f.identidade_estavel,
  f.fk_destino,
  f.catalogo_schema,
  f.catalogo_tabela,
  f.catalogo_chave,
  f.expected_type,
  f.nulidade,
  f.serializacao_saida,
  f.tipo_leitura,
  f.byte_offset,
  f.bit_inicio,
  f.largura_bits,
  f.largura_bytes,
  f.endianness,
  f.codificacao,
  f.transformacao,
  f.requisito,
  f.normalizador_id,
  f.versao_normalizador,
  f.schema_payload,
  f.status_prova,
  f.prova,
  f.proveniencia_mapa_assunto as proveniencia_campo,
  a.arquivo_id,
  fonte.papel_fonte,
  a.arquivo,
  a.cpk,
  a.versao_arquivo,
  a.sha256_arquivo,
  a.tamanho_registro,
  a.prefixo_bytes,
  a.decodificador,
  a.leitor_id,
  a.versao_leitor,
  a.formato_saida,
  a.tipo_saida,
  a.serializacao_saida as serializacao_arquivo,
  a.obrigatorio as arquivo_obrigatorio,
  l.localizador_id,
  l.ordem as precedencia_localizador,
  l.template_caminho,
  l.plataforma,
  l.obrigatorio as localizador_obrigatorio,
  l.sha256_cpk,
  l.proveniencia as proveniencia_localizador,
  fam.precedencia_fontes,
  fam.papeis_fonte,
  fam.leitor_id as leitor_familia,
  fam.versao_leitor as versao_leitor_familia,
  a.papel_fonte as papel_fonte_arquivo_canonico
from clube_novo.contrato_leitura_campo f
join clube_novo.contrato_leitura_familia fam
  on fam.contrato_id=f.contrato_id and fam.chave_familia=f.chave_familia
join clube_novo.contrato_leitura_arquivo a
  on a.contrato_id=f.contrato_id and a.arquivo_id=f.arquivo_id
cross join lateral jsonb_array_elements_text(fam.papeis_fonte) as fonte(papel_fonte)
left join clube_novo.contrato_leitura_fonte_localizador l
  on l.contrato_id=a.contrato_id and l.papel_fonte=fonte.papel_fonte
where f.ativo and fam.obrigatoria;

comment on view clube_novo.catalogo_endereco_leitura_extrator_v1 is
  'Índice read-only único do Extrator: espelha por FK o campo canônico e acrescenta localização/fonte/versão/procedência; não é cópia nem autoridade paralela.';

create or replace function clube_novo.obter_pedido_leitura_tipado_sem_revisao_v1()
returns jsonb language plpgsql set search_path = clube_novo, pg_temp as $$
declare base jsonb; cid text;
begin
  base := clube_novo.obter_pedido_leitura_contrato_ativo();
  cid := base->>'contrato_id';
  if cid is null then raise exception 'pedido V1 sem contrato_id'; end if;
  if exists (select 1 from clube_novo.catalogo_endereco_leitura_extrator_v1 where contrato_id=cid and (expected_type='' or normalizador_id='' or schema_payload='{}'::jsonb)) then
    raise exception 'pedido tipado recusado: campo sem tipo/normalizador/schema';
  end if;
  if exists (select 1 from clube_novo.contrato_leitura_familia where contrato_id=cid and obrigatoria and (papeis_fonte='[]'::jsonb or schema_payload='{}'::jsonb)) then
    raise exception 'pedido tipado recusado: família obrigatória incompleta';
  end if;
  if not exists (select 1 from clube_novo.catalogo_endereco_leitura_extrator_v1 where contrato_id=cid) then raise exception 'pedido tipado sem catálogo de endereços'; end if;
  return base || jsonb_build_object(
    'contrato_formato','pedido_leitura_tipado_v1',
    'familias',coalesce((select jsonb_agg(jsonb_build_object('chave_familia',f.chave_familia,'leitor_id',f.leitor_id,'versao_leitor',f.versao_leitor,'schema_payload',f.schema_payload,'tipo_saida',f.tipo_saida,'normalizador_id',f.normalizador_id,'versao_normalizador',f.versao_normalizador,'identidade',f.identidade,'papeis_fonte',f.papeis_fonte,'precedencia_fontes',f.precedencia_fontes,'catalogos_requeridos',f.catalogos_requeridos,'comparacao_ativa',f.comparacao_ativa,'obrigatoria',f.obrigatoria) order by f.chave_familia) from clube_novo.contrato_leitura_familia f where f.contrato_id=cid),'[]'::jsonb),
    'expectativas',coalesce((select jsonb_agg(jsonb_build_object('familia',e.chave_familia,'metrica',e.chave_metrica,'valor',e.valor_esperado,'comparador',e.comparador,'obrigatoria',e.obrigatoria) order by e.chave_familia,e.chave_metrica) from clube_novo.contrato_leitura_expectativa e where e.contrato_id=cid),'[]'::jsonb),
    'catalogo_enderecos',coalesce((select jsonb_agg(to_jsonb(v) order by v.chave_familia,v.chave_campo,v.localizador_id) from clube_novo.catalogo_endereco_leitura_extrator_v1 v where v.contrato_id=cid),'[]'::jsonb),
    'localizadores_fontes',coalesce((select jsonb_agg(jsonb_build_object('localizador_id',localizador_id,'papel_fonte',papel_fonte,'ordem',precedencia_localizador,'template_caminho',template_caminho,'plataforma',plataforma,'obrigatorio',localizador_obrigatorio,'sha256_cpk',sha256_cpk) order by papel_fonte,precedencia_localizador) from (select distinct on (localizador_id) * from clube_novo.catalogo_endereco_leitura_extrator_v1 where contrato_id=cid and localizador_id is not null order by localizador_id) v),'[]'::jsonb),
    'arquivos',coalesce((select jsonb_agg(jsonb_build_object('arquivo_id',arquivo_id,'papel_fonte',papel_fonte_arquivo_canonico,'arquivo',arquivo,'cpk',cpk,'versao_arquivo',versao_arquivo,'sha256_arquivo',sha256_arquivo,'tamanho_registro',tamanho_registro,'prefixo_bytes',prefixo_bytes,'decodificador',decodificador,'leitor_id',leitor_id,'versao_leitor',versao_leitor,'formato_saida',formato_saida,'tipo_saida',tipo_saida,'serializacao_saida',serializacao_arquivo,'obrigatorio',arquivo_obrigatorio) order by papel_fonte_arquivo_canonico,arquivo) from (select distinct on (arquivo_id) * from clube_novo.catalogo_endereco_leitura_extrator_v1 where contrato_id=cid order by arquivo_id) v),'[]'::jsonb),
    'campos',coalesce((select jsonb_agg(jsonb_build_object('chave_campo',v.chave_campo,'chave_familia',v.chave_familia,'arquivo_id',v.arquivo_id,'entidade_destino',v.entidade_destino,'tipo_leitura',v.tipo_leitura,'byte_offset',v.byte_offset,'bit_inicio',v.bit_inicio,'largura_bits',v.largura_bits,'largura_bytes',v.largura_bytes,'endianness',v.endianness,'codificacao',v.codificacao,'transformacao',v.transformacao,'catalogo_schema',v.catalogo_schema,'catalogo_tabela',v.catalogo_tabela,'catalogo_chave',v.catalogo_chave,'requisito',v.requisito,'proveniencia',v.proveniencia_campo,'prova',v.prova,'status_base',v.status_prova,'expected_type',v.expected_type,'normalizador_id',v.normalizador_id,'versao_normalizador',v.versao_normalizador,'schema_payload',v.schema_payload,'identidade_estavel',v.identidade_estavel,'fk_destino',v.fk_destino,'nulidade',v.nulidade,'serializacao_saida',v.serializacao_saida) order by v.chave_campo) from (select distinct on (campo_id) * from clube_novo.catalogo_endereco_leitura_extrator_v1 where contrato_id=cid and status_prova in ('comprovado','convencao_aprovada') order by campo_id,precedencia_localizador) v),'[]'::jsonb)
  );
end; $$;

-- A mudança de arquitetura é estrutural; o novo selo invalida planos emitidos
-- antes da view, mesmo que os dados de origem sejam idênticos.
update clube_novo.contrato_leitura_jogo
set versao_contrato = 'r2-fontes-catalogo-v1',
    fingerprint_contrato_sha256 = clube_novo.fingerprint_material_contrato_leitura(contrato_id)
where contrato_id='clubef-dt870-2026-r1';
