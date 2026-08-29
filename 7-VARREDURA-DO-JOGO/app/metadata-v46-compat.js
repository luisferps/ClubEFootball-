'use strict';

/**
 * Compatibilidade transitória do runtime V4.6.
 *
 * Não conhece endereço físico. Fontes históricas que não fazem parte do selo
 * de arquivos do contrato ativo são aceitas apenas como contêineres descobertos;
 * a validação estrutural real acontece depois, dentro do leitor de metadados,
 * usando tamanhos/bits dos catálogos canônicos. O espelho de tipo de ímpeto é
 * projetado exclusivamente de tipo_impeto_jogo para uma dependência antiga do
 * runtime, sem criar uma segunda autoridade.
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

  async function validateSourceWithoutInventingAddress(bytes, plan, role) {
    reader.requirePlan(plan);
    currentPlan = plan;
    const requested = (plan.arquivos || []).filter((file) => file.papel_fonte === role && file.obrigatorio);
    if (requested.length) return previousValidate(bytes, plan, role);

    if (role !== 'dt200' && role !== 'dt870_original') {
      throw new Error(`fonte ${role} não é descrita pelo contrato ativo`);
    }

    // DT200 e DT870 original são fontes históricas auxiliares. O contrato atual
    // não publica fingerprint para elas; portanto este passo não tenta adivinhar
    // tamanho, bit, offset ou arquivo. A rotina canônica de metadados fará a
    // validação física pelos catálogos antes de consumir qualquer registro.
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

    const existing = catalog(currentPlan, 'impeto_condicao_jogo');
    let injected = null;
    if (!existing) {
      const typeCatalog = catalog(currentPlan, 'tipo_impeto_jogo');
      const source = typeCatalog && Array.isArray(typeCatalog.rows) ? typeCatalog.rows.find((row) =>
        Number.isInteger(row.bit_tipo_espelho) && Number.isInteger(row.largura_tipo_espelho)
      ) : null;
      if (!source) throw new Error('tipo_impeto_jogo não fornece o endereço do espelho da condição');

      // Projeção mínima para uma dependência interna da rotina já existente.
      // Os números continuam vindo da tabela tipo_impeto_jogo.
      injected = {
        schema: 'clube_novo',
        table: 'impeto_condicao_jogo',
        keys: ['codigo_impeto'],
        rows: [{
          bit_tipo_espelho: source.bit_tipo_espelho,
          largura_tipo_espelho: source.largura_tipo_espelho,
          origem_referencia: 'clube_novo.tipo_impeto_jogo'
        }]
      };
      currentPlan.catalogos.push(injected);
    }

    try {
      return await previousExtractMetadata(sourceBytes, sourceDescriptors, log);
    } finally {
      if (injected) {
        const index = currentPlan.catalogos.indexOf(injected);
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
