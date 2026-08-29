-- Origem única do pedido de leitura. Retorna um plano somente quando ele é seguro
-- para execução: versão, fingerprints, arquivos, campos, FKs e requisitos.

create or replace function clube_novo.obter_pedido_leitura_contrato_ativo()
returns jsonb
language plpgsql
security invoker
set search_path = clube_novo, pg_temp
as $$
declare
  contract_row clube_novo.contrato_leitura_jogo%rowtype;
  result jsonb;
begin
  select * into contract_row
  from clube_novo.contrato_leitura_jogo
  where estado='ativo' and cobertura_total
  order by ativado_em desc nulls last, criado_em desc
  limit 1;

  if not found then
    raise exception 'contrato de leitura ativo e integral não encontrado';
  end if;
  if exists (
    select 1 from clube_novo.contrato_leitura_campo f
    where f.contrato_id=contract_row.contrato_id and f.ativo and f.status_prova <> 'comprovado'
  ) then
    raise exception 'contrato ativo inválido: campo sem prova física individual';
  end if;
  if exists (
    select 1 from clube_novo.contrato_leitura_cadeia c
    where c.contrato_id=contract_row.contrato_id and c.requer_selo_contrato and c.estado <> 'conforme'
  ) then
    raise exception 'contrato ativo inválido: cadeia satélite não conforme';
  end if;

  select jsonb_build_object(
    'contrato_id', contract_row.contrato_id,
    'versao_jogo', contract_row.versao_jogo,
    'versao_contrato', contract_row.versao_contrato,
    'fingerprint_contrato_sha256', contract_row.fingerprint_contrato_sha256,
    'fingerprint_fontes_sha256', contract_row.fingerprint_fontes_sha256,
    'requisitos', coalesce((
      select jsonb_agg(jsonb_build_object('chave',r.chave_requisito,'expressao',r.expressao,'obrigatorio',r.obrigatorio) order by r.chave_requisito)
      from clube_novo.contrato_leitura_requisito r where r.contrato_id=contract_row.contrato_id
    ), '[]'::jsonb),
    'arquivos', coalesce((
      select jsonb_agg(jsonb_build_object(
        'arquivo_id',a.arquivo_id,'papel_fonte',a.papel_fonte,'arquivo',a.arquivo,'cpk',a.cpk,
        'versao_arquivo',a.versao_arquivo,'sha256_arquivo',a.sha256_arquivo,
        'tamanho_registro',a.tamanho_registro,'prefixo_bytes',a.prefixo_bytes,
        'decodificador',a.decodificador,'obrigatorio',a.obrigatorio
      ) order by a.papel_fonte,a.arquivo)
      from clube_novo.contrato_leitura_arquivo a where a.contrato_id=contract_row.contrato_id
    ), '[]'::jsonb),
    'campos', coalesce((
      select jsonb_agg(jsonb_build_object(
        'chave_campo',f.chave_campo,'arquivo_id',f.arquivo_id,'entidade_destino',f.entidade_destino,
        'tipo_leitura',f.tipo_leitura,'byte_offset',f.byte_offset,'bit_inicio',f.bit_inicio,
        'largura_bits',f.largura_bits,'largura_bytes',f.largura_bytes,'endianness',f.endianness,
        'codificacao',f.codificacao,'transformacao',f.transformacao,'catalogo_schema',f.catalogo_schema,
        'catalogo_tabela',f.catalogo_tabela,'catalogo_chave',f.catalogo_chave,'requisito',f.requisito,
        'proveniencia',f.proveniencia_mapa_assunto,'prova',f.prova
      ) order by f.chave_campo)
      from clube_novo.contrato_leitura_campo f
      where f.contrato_id=contract_row.contrato_id and f.ativo and f.status_prova='comprovado'
    ), '[]'::jsonb)
  ) into result;
  return result;
end;
$$;
