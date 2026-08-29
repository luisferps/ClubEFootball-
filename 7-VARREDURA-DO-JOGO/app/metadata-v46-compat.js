'use strict';

/**
 * Compatibilidade transitória do runtime V4.6.
 *
 * Não contém endereço físico próprio. Quando uma dependência antiga do runtime
 * exige uma tabela que não faz parte da lista enviada pelo contrato atual, esta
 * camada cria somente uma projeção temporária a partir da referência canônica
 * já presente no pedido (catálogo ou campo contratado).
 */
(function installMetadataV46Compat(global) {
  const core = global.CLUBEF_CORE;
  const reader = global.CLUBEF_CONTRACT_READER;
  if (!core || !reader) throw new Error('metadata-v46-compat requer core e leitor');

  const previousValidate = core.validateSourceByContract;
  const previousExtractMetadata = core.extractMetadataByFamily;
  let currentPlan = null;

  function catalog(plan, table) {
    return (plan.catalogos || []).find((item) => item.schema === 'clube_novo' && item.table === table) || null;
  }
  function contractField(plan, key) {
    const found = reader.requirePlan(plan).fields.get(key);
    if (!found) throw new Error(`campo canônico ausente: ${key}`);
    return found;
  }
  function addProjection(table, row, source) {
    if (catalog(currentPlan, table)) return null;
    const projected = {
      schema: 'clube_novo',
      table,
      keys: ['compat_v46'],
      rows: [{ ...row, origem_referencia: source }]
    };
    currentPlan.catalogos.push(projected);
    return projected;
  }

  async function validateSourceWithoutInventingAddress(bytes, plan, role) {
    reader.requirePlan(plan);
    currentPlan = plan;
    const requested = (plan.arquivos || []).filter((file) => file.papel_fonte === role && file.obrigatorio);
    if (requested.length) return previousValidate(bytes, plan, role);

    if (role !== 'dt200' && role !== 'dt870_original') {
      throw new Error(`fonte ${role} não é descrita pelo contrato ativo`);
    }

    // O contrato atual não publica fingerprint autoritativo para as duas fontes
    // históricas. Nenhum tamanho/bit/offset é inventado aqui. A validação de cada
    // arquivo ocorre no consumo, pela rotina canônica de metadados.
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
    const injected = [];

    const typeCatalog = catalog(currentPlan, 'tipo_impeto_jogo');
    const typeSource = typeCatalog && Array.isArray(typeCatalog.rows)
      ? typeCatalog.rows.find((row) => Number.isInteger(row.bit_tipo_espelho) && Number.isInteger(row.largura_tipo_espelho))
      : null;
    if (!catalog(currentPlan, 'impeto_condicao_jogo')) {
      if (!typeSource) throw new Error('tipo_impeto_jogo não fornece o endereço do espelho da condição');
      const projection = addProjection('impeto_condicao_jogo', {
        bit_tipo_espelho: typeSource.bit_tipo_espelho,
        largura_tipo_espelho: typeSource.largura_tipo_espelho
      }, 'clube_novo.tipo_impeto_jogo');
      if (projection) injected.push(projection);
    }

    if (!catalog(currentPlan, 'impeto_condicao_nacionalidade_jogo')) {
      const source = contractField(currentPlan, 'impeto.condicao.nacionalidade');
      const projection = addProjection('impeto_condicao_nacionalidade_jogo', {
        bit_alvo: source.bit_inicio,
        largura_alvo: source.largura_bits
      }, 'contrato:impeto.condicao.nacionalidade');
      if (projection) injected.push(projection);
    }

    if (!catalog(currentPlan, 'impeto_condicao_liga_jogo')) {
      const source = contractField(currentPlan, 'impeto.condicao.liga');
      const projection = addProjection('impeto_condicao_liga_jogo', {
        bit_alvo: source.bit_inicio,
        largura_alvo: source.largura_bits
      }, 'contrato:impeto.condicao.liga');
      if (projection) injected.push(projection);
    }

    try {
      return await previousExtractMetadata(sourceBytes, sourceDescriptors, log);
    } finally {
      for (const projection of injected) {
        const index = currentPlan.catalogos.indexOf(projection);
        if (index >= 0) currentPlan.catalogos.splice(index, 1);
      }
    }
  }

  global.CLUBEF_CORE = Object.freeze({
    ...core,
    validateSourceByContract: validateSourceWithoutInventingAddress,
    extractMetadataByFamily: extractMetadataWithCanonicalDependencies
  });
})(globalThis);
