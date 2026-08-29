'use strict';

/**
 * Compatibilidade transitória do runtime V4.6.
 *
 * Não contém endereço físico e não fabrica catálogos. O servidor V4.6 entrega
 * diretamente as linhas das tabelas canônicas do clube_novo. Esta camada só
 * mantém a compatibilidade de descoberta das duas fontes históricas que ainda
 * não possuem fingerprint próprio no contrato ativo.
 */
(function installMetadataV46Compat(global) {
  const core = global.CLUBEF_CORE;
  const reader = global.CLUBEF_CONTRACT_READER;
  if (!core || !reader) throw new Error('metadata-v46-compat requer core e leitor');

  const previousValidate = core.validateSourceByContract;
  const previousExtractMetadata = core.extractMetadataByFamily;
  let currentPlan = null;

  function requireCatalog(plan, table) {
    const catalog = (plan.catalogos || []).find((item) => item.schema === 'clube_novo' && item.table === table);
    if (!catalog || !Array.isArray(catalog.rows) || !catalog.rows.length) {
      throw new Error(`catálogo canônico ausente no pedido: clube_novo.${table}`);
    }
    return catalog.rows;
  }

  function requireColumns(plan, table, columns) {
    const rows = requireCatalog(plan, table);
    for (const [index, row] of rows.entries()) {
      for (const column of columns) {
        if (row[column] === null || row[column] === undefined || row[column] === '') {
          throw new Error(`${table}[${index}] sem referência canônica ${column}`);
        }
      }
    }
    return rows;
  }

  function validateCanonicalPayload(plan) {
    requireColumns(plan, 'impeto_jogo', ['arquivo_catalogo', 'tamanho_registro', 'bit_codigo', 'largura_codigo']);
    requireColumns(plan, 'impeto_atributo_jogo', ['arquivo_origem', 'fonte_origem', 'bit_delta', 'largura_delta']);
    requireColumns(plan, 'estilo_jogo_tecnico', ['bit', 'largura']);
    requireColumns(plan, 'afinidade_tecnico_jogo', ['bit', 'largura']);
    requireColumns(plan, 'atributo_ordem_otimizador', ['codigo_atributo', 'indice_otimizador']);
    requireColumns(plan, 'impeto_condicao_nacionalidade_jogo', ['bit_alvo', 'largura_alvo']);
    requireColumns(plan, 'impeto_condicao_liga_jogo', ['bit_alvo', 'largura_alvo']);
    requireColumns(plan, 'impeto_condicao_liga_membro_jogo', ['arquivo_origem', 'tamanho_registro', 'bit_inicial', 'largura']);
    requireCatalog(plan, 'impeto_condicao_jogo');
    requireCatalog(plan, 'impeto_condicao_classe_jogo');
    requireCatalog(plan, 'impeto_condicao_parametro_faixa_jogo');
    requireCatalog(plan, 'posicao_jogo');

    const typeRows = requireCatalog(plan, 'tipo_impeto_jogo');
    if (!typeRows.some((row) => Number.isInteger(row.bit_tipo_espelho) && Number.isInteger(row.largura_tipo_espelho))) {
      throw new Error('tipo_impeto_jogo não fornece o endereço físico do espelho de condição');
    }
  }

  async function validateSourceWithoutInventingAddress(bytes, plan, role) {
    reader.requirePlan(plan);
    validateCanonicalPayload(plan);
    currentPlan = plan;
    const requested = (plan.arquivos || []).filter((file) => file.papel_fonte === role && file.obrigatorio);
    if (requested.length) return previousValidate(bytes, plan, role);

    if (role !== 'dt200' && role !== 'dt870_original') {
      throw new Error(`fonte ${role} não é descrita pelo contrato ativo`);
    }

    return {
      contract: Object.fromEntries(reader.SEAL_KEYS.map((key) => [key, plan[key]])),
      role,
      cpk_sha256: await core.sha256(bytes),
      files: [],
      database_write: false,
      validation: 'deferred_to_canonical_metadata_reader'
    };
  }

  async function extractMetadataWithCanonicalDependencies(sourceBytes, sourceDescriptors, log) {
    if (!currentPlan) throw new Error('contrato ativo não foi recebido antes dos metadados');
    validateCanonicalPayload(currentPlan);
    return previousExtractMetadata(sourceBytes, sourceDescriptors, log);
  }

  global.CLUBEF_CORE = Object.freeze({
    ...core,
    validateSourceByContract: validateSourceWithoutInventingAddress,
    extractMetadataByFamily: extractMetadataWithCanonicalDependencies
  });
})(globalThis);
