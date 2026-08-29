'use strict';

/**
 * Auditoria somente leitura do contrato físico de ímpetos.
 *
 * Uso:
 *   node auditar-impetos-fisicos.js <pasta-saida> <dt200> <dt870-original>
 *        <dt870-atualizacao> <pasta-app-extrator>
 *
 * O script não acessa o banco e não altera CPKs. Ele reutiliza o leitor CPK/WESYS
 * já validado do Extrator, mas expõe suas funções privadas apenas nesta execução.
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const cryptoNode = require('crypto');

const [outputDir, dt200Path, dt870OriginalPath, dt870UpdatedPath, appDir] = process.argv.slice(2);
if (![outputDir, dt200Path, dt870OriginalPath, dt870UpdatedPath, appDir].every(Boolean)) {
  throw new Error('Informe pasta de saída, DT200, DT870 original, DT870 da atualização e pasta app.');
}

if (!global.crypto) global.crypto = cryptoNode.webcrypto;

function loadProjectCode() {
  const mapPath = path.join(appDir, 'mapeamento-fisico.js');
  const catalogMapPath = path.join(appDir, 'catalog-source-map.js');
  const corePath = path.join(appDir, 'extrator-core.js');

  const mapCode = fs.readFileSync(mapPath, 'utf8')
    + '\n;globalThis.CLUBEF_PHYSICAL_MAP={K,IMP,OVRW,STYLE_CAT,DEF_CAT};';
  vm.runInThisContext(mapCode, { filename: mapPath });
  vm.runInThisContext(fs.readFileSync(catalogMapPath, 'utf8'), { filename: catalogMapPath });

  const coreCode = fs.readFileSync(corePath, 'utf8').replace(
    'global.CLUBEF_CORE = Object.freeze({',
    'global.CLUBEF_CORE = Object.freeze({ extractCpk, unpackWesys, readBits, decodeCard, validCard,'
  );
  vm.runInThisContext(coreCode, { filename: corePath });
}

function sha256File(filePath) {
  return cryptoNode.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
}

function csvCell(value) {
  if (value == null) return '';
  const text = String(value);
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function toCsv(rows, columns) {
  return [columns.join(','), ...rows.map((row) => columns.map((column) => csvCell(row[column])).join(','))].join('\r\n') + '\r\n';
}

function writeJson(fileName, value) {
  fs.writeFileSync(path.join(outputDir, fileName), JSON.stringify(value, null, 2) + '\n', 'utf8');
}

function writeCsv(fileName, rows, columns) {
  fs.writeFileSync(path.join(outputDir, fileName), toCsv(rows, columns), 'utf8');
}

const ATTRIBUTE_FIELDS = Object.freeze([
  { legacy: 'low_pass', codigo: 'PB:524:6', bit: 122 },
  { legacy: 'attacking_prowess', codigo: 'PB:498:6', bit: 144 },
  { legacy: 'body_control', codigo: 'PB:504:6', bit: 149 },
  { legacy: 'place_kicking', codigo: 'PB:368:6', bit: 154 },
  { legacy: 'jump', codigo: 'PB:408:6', bit: 160 },
  { legacy: 'catching', codigo: 'PB:416:6', bit: 165 },
  { legacy: 'aggression', codigo: 'PB:512:6', bit: 170 },
  { legacy: 'physical_contact', codigo: 'PB:518:6', bit: 175 },
  { legacy: 'speed', codigo: 'PB:434:6', bit: 180 },
  { legacy: 'swerve', codigo: 'PB:428:6', bit: 185 },
  // Três campos de goleiro são fisicamente distintos, mas os 350 registros com
  // dicionário os ativam sempre juntos e com o mesmo delta. A permutação entre
  // Awareness/Parrying/Reflexes não é promovida como provada.
  { legacy: 'gk_field_a', codigo: null, bit: 192, grupo_ambiguo: 'gk_tripla' },
  { legacy: 'gk_field_b', codigo: null, bit: 197, grupo_ambiguo: 'gk_tripla' },
  { legacy: 'stamina', codigo: 'PB:480:6', bit: 202 },
  { legacy: 'explosive_power', codigo: 'PB:486:6', bit: 217 },
  { legacy: 'coverage', codigo: 'PB:422:6', bit: 224 },
  { legacy: 'lofted_pass', codigo: 'PB:448:6', bit: 229 },
  { legacy: 'tackling', codigo: 'PB:454:6', bit: 234 },
  { legacy: 'dribbling', codigo: 'PB:492:6', bit: 239 },
  { legacy: 'finishing', codigo: 'PB:530:6', bit: 244 },
  { legacy: 'kicking_power', codigo: 'PB:384:6', bit: 249 },
  { legacy: 'gk_field_c', codigo: null, bit: 256, grupo_ambiguo: 'gk_tripla' },
  { legacy: 'defensive_awareness', codigo: 'PB:390:6', bit: 261 },
  { legacy: 'defensive_engagement', codigo: 'PB:544:6', bit: 266 },
  { legacy: 'tight_possession', codigo: 'PB:550:6', bit: 271 },
  { legacy: 'ball_control', codigo: 'PB:396:6', bit: 276 },
  { legacy: 'header', codigo: 'PB:402:6', bit: 281 }
]);

const GK_LEGACY_NAMES = Object.freeze(['clearing', 'goalkeeping', 'reflexes']);
const SOURCE_ORDER = Object.freeze(['dt870_atualizacao', 'dt200', 'dt870_original']);

async function readBoosterSource(role, filePath) {
  const bytes = new Uint8Array(fs.readFileSync(filePath));
  const entries = CLUBEF_CORE.extractCpk(bytes);
  if (!entries['PlayerBooster.bin']) throw new Error(`${role}: PlayerBooster.bin ausente.`);
  const raw = await CLUBEF_CORE.unpackWesys(entries['PlayerBooster.bin']);
  const records = [];

  if (role === 'dt870_original') {
    const expected = CLUBEF_CATALOG_SOURCE_MAP.DT870_ORIGINAL_CPK_SHA256;
    const actual = sha256File(filePath);
    if (actual !== expected) throw new Error(`DT870 original fora do fingerprint selado: ${actual}`);
    for (const [idText, index] of Object.entries(CLUBEF_CATALOG_SOURCE_MAP.BOOSTER_DT870_ORIGINAL_INDEX)) {
      const id = Number(idText);
      const offset = index * 40;
      const physicalId = CLUBEF_CORE.readBits(raw, offset, 112, 10);
      if (physicalId !== id) throw new Error(`DT870 original: índice ${index} declara ${id}, leu ${physicalId}.`);
      records.push({ id, index, offset });
    }
  } else {
    if (raw.length % 40 !== 0) throw new Error(`${role}: tamanho ${raw.length} não é múltiplo de 40.`);
    for (let offset = 0; offset < raw.length; offset += 40) {
      records.push({ id: CLUBEF_CORE.readBits(raw, offset, 112, 10), index: offset / 40, offset });
    }
  }

  const seen = new Set();
  for (const record of records) {
    if (seen.has(record.id)) throw new Error(`${role}: codigo_jogo duplicado ${record.id}.`);
    seen.add(record.id);
  }

  return {
    role,
    filePath,
    cpk_sha256: sha256File(filePath),
    cpk_bytes: fs.statSync(filePath).size,
    player_booster_bytes: raw.length,
    raw,
    recipe_layout: role === 'dt870_original' ? 'legado_id_apenas' : 'registro_atual_40_bytes',
    records
  };
}

function decodeRecord(source, record) {
  const { raw } = source;
  const { offset } = record;
  const recipeAvailable = source.recipe_layout === 'registro_atual_40_bytes';
  const fields = recipeAvailable ? ATTRIBUTE_FIELDS.map((field) => ({
    ...field,
    delta: CLUBEF_CORE.readBits(raw, offset, field.bit, 5)
  })) : [];
  return {
    codigo_jogo: record.id,
    source: source.role,
    registro: record.index,
    byte_offset: record.offset,
    id_bit: 112,
    id_width: 10,
    recipe_layout: source.recipe_layout,
    recipe_available: recipeAvailable,
    tipo_efeito_fisico: recipeAvailable ? CLUBEF_CORE.readBits(raw, offset, 64, 8) : null,
    tipo_bit: 64,
    tipo_width: 8,
    nivel_fisico: recipeAvailable ? CLUBEF_CORE.readBits(raw, offset, 212, 3) : null,
    nivel_bit: 212,
    nivel_width: 3,
    fields,
    record_sha256: cryptoNode.createHash('sha256').update(Buffer.from(raw.slice(offset, offset + 40))).digest('hex')
  };
}

function semanticRecord(record) {
  return JSON.stringify({
    tipo_efeito_fisico: record.tipo_efeito_fisico,
    nivel_fisico: record.nivel_fisico,
    deltas: record.fields.map((field) => [field.bit, field.delta])
  });
}

function validateKnownMap(catalog) {
  const checks = [];
  for (const [idText, mapped] of Object.entries(CLUBEF_PHYSICAL_MAP.IMP)) {
    const id = Number(idText);
    const entry = catalog.get(id);
    if (!entry) {
      checks.push({ codigo_jogo: id, status: 'codigo_ausente_nas_fontes' });
      continue;
    }
    const decoded = entry.preferred;
    const direct = decoded.fields.filter((field) => field.codigo);
    const expectedDirect = new Set(mapped.a.filter((name) => !GK_LEGACY_NAMES.includes(name)));
    const actualDirect = new Set(direct.filter((field) => field.delta > 0).map((field) => field.legacy));
    const directMembershipOk = [...new Set([...expectedDirect, ...actualDirect])]
      .every((name) => expectedDirect.has(name) === actualDirect.has(name));
    const directDeltasOk = direct.every((field) => field.delta === (expectedDirect.has(field.legacy) ? mapped.u : 0));

    const expectedGk = GK_LEGACY_NAMES.filter((name) => mapped.a.includes(name));
    const actualGk = decoded.fields.filter((field) => field.grupo_ambiguo === 'gk_tripla').map((field) => field.delta);
    const gkCollectiveOk = expectedGk.length === 0
      ? actualGk.every((delta) => delta === 0)
      : expectedGk.length === 3 && actualGk.every((delta) => delta === mapped.u);

    const conditionClassOk = mapped.c
      ? decoded.tipo_efeito_fisico === 2
      : decoded.tipo_efeito_fisico !== 2;

    checks.push({
      codigo_jogo: id,
      source: decoded.source,
      registro: decoded.registro,
      nivel_esperado: mapped.u,
      nivel_fisico: decoded.nivel_fisico,
      condicional_dicionario: mapped.c,
      tipo_efeito_fisico: decoded.tipo_efeito_fisico,
      nivel_ok: decoded.nivel_fisico === mapped.u,
      atributos_diretos_ok: directMembershipOk && directDeltasOk,
      trio_gk_coletivo_ok: gkCollectiveOk,
      classe_condicao_ok: conditionClassOk,
      status: decoded.nivel_fisico === mapped.u && directMembershipOk && directDeltasOk && gkCollectiveOk && conditionClassOk
        ? 'confere'
        : 'diverge'
    });
  }
  return checks;
}

async function auditCards(updatedSource, catalog) {
  const cpk = CLUBEF_CORE.extractCpk(new Uint8Array(fs.readFileSync(updatedSource.filePath)));
  const players = await CLUBEF_CORE.unpackWesys(cpk['Player.bin']);
  if (players.length % 400 !== 0) throw new Error('Player.bin atual não usa registros de 400 bytes.');

  const samplesWanted = new Set(['88036360701097', '89138288270047', '89138556575063']);
  const samples = [];
  const counters = {
    registros_fisicos: players.length / 400,
    cartas_validas: 0,
    registros_descartados_pelo_contrato: 0,
    slot_primario_preenchido: 0,
    slot_condicional_preenchido: 0,
    slot_primario_acima_255: 0,
    slot_condicional_acima_255: 0,
    atribuicoes_acima_255: 0,
    atribuicoes_que_low8_confunde_com_sem_impeto: 0,
    atribuicoes_que_low8_confunde_com_vaga: 0,
    codigos_preenchidos_sem_catalogo: 0,
    codigos_distintos_sem_catalogo: 0
  };
  const missing = new Map();
  const fullCodes = new Set();
  const low8LossSamples = [];

  for (let offset = 0; offset < players.length; offset += 400) {
    const decodedCard = CLUBEF_CORE.decodeCard(players, offset);
    if (!CLUBEF_CORE.validCard(decodedCard)) {
      counters.registros_descartados_pelo_contrato += 1;
      continue;
    }
    counters.cartas_validas += 1;
    const cardId = (
      BigInt(CLUBEF_CORE.readBits(players, offset, 64, 32))
      | (BigInt(CLUBEF_CORE.readBits(players, offset, 96, 32)) << 32n)
    ).toString();
    const primary = CLUBEF_CORE.readBits(players, offset, 308, 10);
    const conditional = CLUBEF_CORE.readBits(players, offset, 288, 10);
    const row = {
      card_id: cardId,
      registro: offset / 400,
      byte_offset: offset,
      slot_primario_codigo_jogo: primary,
      slot_condicional_codigo_jogo: conditional,
      slot_primario_low8: primary & 255,
      slot_condicional_low8: conditional & 255,
      slot_primario_bit: 308,
      slot_condicional_bit: 288,
      largura: 10
    };
    if (samplesWanted.has(cardId)) samples.push(row);

    for (const [slot, code] of [['primario', primary], ['condicional', conditional]]) {
      if (code === 0 || code === 136) continue;
      counters[`slot_${slot}_preenchido`] += 1;
      if (code > 255) {
        counters[`slot_${slot}_acima_255`] += 1;
        counters.atribuicoes_acima_255 += 1;
        const low8 = code & 255;
        if (low8 === 0) counters.atribuicoes_que_low8_confunde_com_sem_impeto += 1;
        if (low8 === 136) counters.atribuicoes_que_low8_confunde_com_vaga += 1;
        if ((low8 === 0 || low8 === 136) && low8LossSamples.length < 20) {
          low8LossSamples.push({ card_id: cardId, slot, codigo_jogo: code, low8 });
        }
      }
      fullCodes.add(code);
      if (!catalog.has(code)) {
        counters.codigos_preenchidos_sem_catalogo += 1;
        missing.set(code, (missing.get(code) || 0) + 1);
      }
    }
  }
  counters.codigos_distintos_preenchidos = fullCodes.size;
  counters.codigos_distintos_sem_catalogo = missing.size;

  return {
    counters,
    sentinel_vaga: 136,
    sem_impeto: 0,
    samples,
    low8_loss_samples: low8LossSamples,
    missing_codes: [...missing.entries()].map(([codigo_jogo, ocorrencias]) => ({ codigo_jogo, ocorrencias }))
  };
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  loadProjectCode();

  const sources = {
    dt200: await readBoosterSource('dt200', dt200Path),
    dt870_original: await readBoosterSource('dt870_original', dt870OriginalPath),
    dt870_atualizacao: await readBoosterSource('dt870_atualizacao', dt870UpdatedPath)
  };

  const catalog = new Map();
  for (const source of Object.values(sources)) {
    for (const record of source.records) {
      if (!catalog.has(record.id)) catalog.set(record.id, { codigo_jogo: record.id, sources: {} });
      catalog.get(record.id).sources[source.role] = decodeRecord(source, record);
    }
  }
  for (const entry of catalog.values()) {
    const preferredRole = SOURCE_ORDER.find((role) => entry.sources[role]);
    entry.preferred = entry.sources[preferredRole];
  }

  const sourceDivergences = [];
  for (const entry of [...catalog.values()].sort((a, b) => a.codigo_jogo - b.codigo_jogo)) {
    if (!entry.preferred.recipe_available) continue;
    const preferredSignature = semanticRecord(entry.preferred);
    for (const [sourceRole, sourceRecord] of Object.entries(entry.sources)) {
      if (sourceRole === entry.preferred.source) continue;
      if (!sourceRecord.recipe_available) continue;
      if (semanticRecord(sourceRecord) !== preferredSignature) {
        sourceDivergences.push({
          codigo_jogo: entry.codigo_jogo,
          fonte_preferida: entry.preferred.source,
          registro_preferido: entry.preferred.registro,
          fonte_comparada: sourceRole,
          registro_comparado: sourceRecord.registro,
          tipo_preferido: entry.preferred.tipo_efeito_fisico,
          tipo_comparado: sourceRecord.tipo_efeito_fisico,
          nivel_preferido: entry.preferred.nivel_fisico,
          nivel_comparado: sourceRecord.nivel_fisico,
          record_sha256_preferido: entry.preferred.record_sha256,
          record_sha256_comparado: sourceRecord.record_sha256
        });
      }
    }
  }

  const knownChecks = validateKnownMap(catalog);
  const cards = await auditCards(sources.dt870_atualizacao, catalog);
  const relationCandidates = [];
  for (const entry of [...catalog.values()].sort((a, b) => a.codigo_jogo - b.codigo_jogo)) {
    const known = CLUBEF_PHYSICAL_MAP.IMP[String(entry.codigo_jogo)] || null;
    // Os 90 códigos sem dicionário não entram na relação: campos não nulos em
    // registros de tipo novo não são promovidos como atributos por semelhança.
    if (!known) continue;
    const decoded = entry.preferred;
    const conditionState = known.c ? 'presente_sem_semantica' : 'ausente_comprovada';
    const directByLegacy = new Map(decoded.fields.filter((field) => field.codigo).map((field) => [field.legacy, field]));
    const gkFields = decoded.fields.filter((field) => field.grupo_ambiguo === 'gk_tripla');
    const knownGk = GK_LEGACY_NAMES.filter((name) => known.a.includes(name));

    for (const [index, legacyName] of known.a.entries()) {
      if (GK_LEGACY_NAMES.includes(legacyName)) continue;
      const field = directByLegacy.get(legacyName);
      if (!field || field.delta !== known.u) {
        throw new Error(`Código ${entry.codigo_jogo}: atributo ${legacyName} não confirmado no campo físico.`);
      }
      relationCandidates.push({
        codigo_impeto: entry.codigo_jogo,
        codigo_atributo: field.codigo,
        ordem: index + 1,
        delta_fisico: field.delta,
        bit_delta: field.bit,
        largura_delta: 5,
        fonte_preferida: decoded.source,
        registro_origem: decoded.registro,
        endereco_origem: `${decoded.source} · PlayerBooster.bin · registro ${decoded.registro} · bit ${field.bit} · largura 5`,
        presente_dt200: Boolean(entry.sources.dt200),
        presente_dt870_original: Boolean(entry.sources.dt870_original),
        presente_dt870_atualizacao: Boolean(entry.sources.dt870_atualizacao),
        condicao_estado: conditionState,
        receita_confirmada: !known.c,
        aplicavel_agora: !known.c,
        falta_o_que: known.c ? 'semantica_e_parametros_da_condicao' : ''
      });
    }

    if (knownGk.length === 3 && gkFields.every((field) => field.delta === decoded.nivel_fisico)) {
      for (const [legacy, codigo] of [
        ['goalkeeping', 'PB:472:6'],
        ['clearing', 'PB:466:6'],
        ['reflexes', 'PB:460:6']
      ]) {
        const index = known.a.indexOf(legacy);
        relationCandidates.push({
          codigo_impeto: entry.codigo_jogo,
          codigo_atributo: codigo,
          ordem: index + 1,
          delta_fisico: decoded.nivel_fisico,
          bit_delta: '',
          largura_delta: 5,
          fonte_preferida: decoded.source,
          registro_origem: decoded.registro,
          endereco_origem: `${decoded.source} · PlayerBooster.bin · registro ${decoded.registro} · conjunto GK bits 192/197/256`,
          presente_dt200: Boolean(entry.sources.dt200),
          presente_dt870_original: Boolean(entry.sources.dt870_original),
          presente_dt870_atualizacao: Boolean(entry.sources.dt870_atualizacao),
          condicao_estado: conditionState,
          receita_confirmada: false,
          aplicavel_agora: false,
          falta_o_que: known && known.c
            ? 'permutacao_semantica_dos_tres_campos_gk; semantica_e_parametros_da_condicao'
            : 'permutacao_semantica_dos_tres_campos_gk',
          atributo_legado: legacy
        });
      }
    }
  }

  const catalogRows = [...catalog.values()].sort((a, b) => a.codigo_jogo - b.codigo_jogo).map((entry) => {
    const known = CLUBEF_PHYSICAL_MAP.IMP[String(entry.codigo_jogo)] || null;
    const preferred = entry.preferred;
    return {
      codigo_jogo: entry.codigo_jogo,
      fonte_preferida: preferred.source,
      registro_preferido: preferred.registro,
      tipo_efeito_fisico: preferred.tipo_efeito_fisico,
      nivel_fisico: preferred.nivel_fisico,
      presente_dt200: Boolean(entry.sources.dt200),
      presente_dt870_original: Boolean(entry.sources.dt870_original),
      presente_dt870_atualizacao: Boolean(entry.sources.dt870_atualizacao),
      dicionario_existente: Boolean(known),
      condicional_dicionario: known ? known.c : '',
      condicao_estado: known ? (known.c ? 'presente_sem_semantica' : 'ausente_comprovada') : 'nao_avaliada',
      nome_dicionario: known ? known.n : '',
      record_sha256: preferred.record_sha256,
      receita_fisica_disponivel: preferred.recipe_available
    };
  });

  const summary = {
    contract: 'clube_novo-impeto-fisico-audit-v1',
    generated_at: new Date().toISOString(),
    read_only: true,
    sources: Object.fromEntries(Object.entries(sources).map(([role, source]) => [role, {
      path: source.filePath,
      cpk_sha256: source.cpk_sha256,
      cpk_bytes: source.cpk_bytes,
      player_booster_bytes: source.player_booster_bytes,
      records: source.records.length,
      recipe_layout: source.recipe_layout
    }])),
    catalog: {
      union_codes: catalog.size,
      mapped_dictionary_codes: knownChecks.length,
      mapped_checks_ok: knownChecks.filter((row) => row.status === 'confere').length,
      mapped_checks_divergent: knownChecks.filter((row) => row.status !== 'confere').length,
      source_semantic_divergences: sourceDivergences.length,
      condition_states: Object.groupBy(catalogRows, (row) => row.condicao_estado)
    },
    relation_candidates: {
      rows: relationCandidates.length,
      applicable_now: relationCandidates.filter((row) => row.aplicavel_agora).length,
      blocked: relationCandidates.filter((row) => !row.aplicavel_agora).length,
      blocked_gk_permutation: relationCandidates.filter((row) => String(row.falta_o_que).includes('permutacao_semantica')).length,
      blocked_condition: relationCandidates.filter((row) => String(row.falta_o_que).includes('condicao')).length,
      observed_delta_min: Math.min(...relationCandidates.map((row) => row.delta_fisico)),
      observed_delta_max: Math.max(...relationCandidates.map((row) => row.delta_fisico))
    },
    cards
  };

  // Object.groupBy não é serializado de maneira útil aqui; substitui por contagem.
  summary.catalog.condition_states = Object.fromEntries(
    Object.entries(summary.catalog.condition_states).map(([key, rows]) => [key, rows.length])
  );

  writeJson('MANIFESTO-AUDITORIA-FISICA.json', summary);
  writeJson('AMOSTRAS-SLOTS-CARTA.json', cards);
  writeCsv('MATRIZ-CATALOGO-FISICO.csv', catalogRows, Object.keys(catalogRows[0]));
  writeCsv('VALIDACAO-DICIONARIO-X-FISICO.csv', knownChecks, Object.keys(knownChecks[0]));
  writeCsv('DIVERGENCIAS-SEMANTICAS-ENTRE-FONTES.csv', sourceDivergences, sourceDivergences.length
    ? Object.keys(sourceDivergences[0])
    : ['codigo_jogo', 'fonte_preferida', 'registro_preferido', 'fonte_comparada', 'registro_comparado']);
  writeCsv('MATRIZ-RECEITAS-CANDIDATAS.csv', relationCandidates, [
    'codigo_impeto', 'codigo_atributo', 'ordem', 'delta_fisico', 'bit_delta', 'largura_delta',
    'fonte_preferida', 'registro_origem', 'endereco_origem', 'presente_dt200',
    'presente_dt870_original', 'presente_dt870_atualizacao', 'condicao_estado',
    'receita_confirmada', 'aplicavel_agora', 'falta_o_que'
  ]);
  console.log(JSON.stringify(summary, null, 2));
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exitCode = 1;
});
