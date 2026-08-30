'use strict';

/*
 * Worker físico do aplicativo desktop.
 *
 * Não abre HTTP, navegador ou UI. Recebe um pedido de leitura já selado pelo
 * coordenador Python, lê somente os CPKs indicados e grava fotografias locais
 * para posterior comparação read-only. Cada mensagem stdout é JSONL para que
 * a janela Windows possa continuar responsiva mesmo se este processo falhar.
 */
const fs = require('fs');
const crypto = require('crypto');
const path = require('path');
const { webcrypto } = require('crypto');

if (!globalThis.crypto) globalThis.crypto = webcrypto;

function argument(name) {
  const index = process.argv.indexOf(name);
  if (index < 0 || !process.argv[index + 1]) throw new Error(`argumento obrigatório ausente: ${name}`);
  return process.argv[index + 1];
}

const root = argument('--root');
const planPath = argument('--plan');
const sourcesPath = argument('--sources');
const outputPath = argument('--output');
const cancelPath = argument('--cancel');

function emit(type, payload) {
  process.stdout.write(`${JSON.stringify({ type, at: new Date().toISOString(), ...payload })}\n`);
}
function cancelled() {
  if (!fs.existsSync(cancelPath)) return false;
  throw new Error('cancelled_by_user');
}
function load(relative) {
  require(path.join(root, relative));
}
function writeJson(name, value) {
  const target = path.join(path.dirname(outputPath), name);
  fs.writeFileSync(target, JSON.stringify(value));
  return target;
}
function familyPlan(plan, key) {
  const item = (plan.familias || []).find((family) => family.chave_familia === key);
  if (!item) throw new Error(`família ausente do pedido tipado: ${key}`);
  return item;
}

function catalogEntries(plan) {
  if (!Array.isArray(plan.catalogo_enderecos) || !plan.catalogo_enderecos.length) throw new Error('pedido sem catálogo único de endereços');
  return plan.catalogo_enderecos;
}

function familyRoles(plan, key) {
  familyPlan(plan, key); // confirma família canônica; endereços vêm somente da view.
  const roles = catalogEntries(plan).filter((item) => item && item.chave_familia === key).map((item) => item.papel_fonte).filter(Boolean);
  if (!roles.length) throw new Error(`família sem endereço no catálogo: ${key}`);
  return [...new Set(roles)];
}

async function familySeal(reader, plan, sources, key, payload) {
  const roles = familyRoles(plan, key);
  const source = [];
  for (const role of roles) {
    const descriptor = sources[role];
    if (!descriptor || !descriptor.found || !descriptor.location) {
      throw new Error(`fonte contratada indisponível para ${key}: ${role}`);
    }
    const bytes = new Uint8Array(fs.readFileSync(descriptor.location));
    source.push({
      papel_fonte: role,
      arquivo: descriptor.filename || null,
      sha256: descriptor.sha256 || await reader.sha256(bytes)
    });
  }
  const contract = {
    contrato_id: plan.contrato_id,
    versao_contrato: plan.versao_contrato,
    fingerprint_contrato: plan.fingerprint_contrato,
    chave_familia: key,
    leitor_id: familyPlan(plan, key).reader_id || null,
    versao_leitor: familyPlan(plan, key).reader_versao || null,
    fontes: source
  };
  const fingerprint_fontes = await reader.sha256(new TextEncoder().encode(JSON.stringify(source)));
  const fingerprint_payload = await reader.sha256(new TextEncoder().encode(globalThis.CLUBEF_CORE.stableJson(payload)));
  const fingerprint_familia = await reader.sha256(new TextEncoder().encode(globalThis.CLUBEF_CORE.stableJson({ contract, fingerprint_fontes, fingerprint_payload })));
  return { contract, fingerprint_fontes, fingerprint_payload, fingerprint_familia };
}

async function readSource(sources, role) {
  cancelled();
  const descriptor = sources[role];
  if (!descriptor || !descriptor.found || !descriptor.location) throw new Error(`fonte indisponível: ${role}`);
  emit('progress', { stage: `Lendo ${role}`, percent: 5 });
  return new Uint8Array(fs.readFileSync(descriptor.location));
}

async function family(name, percent, work, result) {
  cancelled();
  emit('family', { family: name, state: 'running', message: 'Leitura física em andamento.' });
  emit('progress', { stage: name, percent });
  try {
    const value = await work();
    result.families[name] = { state: 'ready', database_write: false };
    emit('family', { family: name, state: 'ready', message: 'Fotografia física concluída.' });
    return value;
  } catch (error) {
    const message = String(error && error.message ? error.message : error);
    result.families[name] = { state: message === 'cancelled_by_user' ? 'cancelled' : 'error', error: message, database_write: false };
    emit('family', { family: name, state: result.families[name].state, message });
    if (message === 'cancelled_by_user') throw error;
    return null;
  }
}

async function main() {
  load('app/mapeamento-fisico.js');
  load('app/catalog-source-map.js');
  load('app/leitura-contrato.js');
  load('app/extrator-core.js');
  const corePath = path.resolve(root, 'app', 'extrator-core.js');
  emit('runtime', { core_path: corePath, core_sha256: crypto.createHash('sha256').update(fs.readFileSync(corePath)).digest('hex') });
  load('app/contrato-v46-runtime.js');
  load('app/metadata-v46-runtime.js');

  const plan = JSON.parse(fs.readFileSync(planPath, 'utf8'));
  const sources = JSON.parse(fs.readFileSync(sourcesPath, 'utf8'));
  const core = globalThis.CLUBEF_CORE;
  const reader = globalThis.CLUBEF_CONTRACT_READER;
  reader.requirePlan(plan);

  const result = {
    contract_seal: Object.fromEntries(reader.SEAL_KEYS.map((key) => [key, plan[key]])),
    database_write: false,
    physical_reader: 'node-desktop-worker',
    families: {},
    contract_families: Object.fromEntries((plan.familias || []).map((family) => [family.chave_familia, {
      physical_state: 'not_started',
      comparison_checks: {},
      database_write: false
    }])),
    artifacts: {},
    family_seals: {}
  };
  function markContractFamily(key, state, artifact) {
    if (!Object.prototype.hasOwnProperty.call(result.contract_families, key)) return;
    result.contract_families[key] = {
      ...result.contract_families[key],
      physical_state: state,
      artifact: artifact || null,
      database_write: false
    };
  }
  emit('status', { database_write: false, message: 'Pedido canônico recebido; iniciando apenas leitura física.' });

  const requestedRoles = new Set(catalogEntries(plan).map((item) => item.papel_fonte).filter(Boolean));
  const loadedSources = {};
  async function loadRole(role) {
    if (!requestedRoles.has(role)) throw new Error(`fonte não solicitada pelo contrato ativo: ${role}`);
    if (!loadedSources[role]) {
      loadedSources[role] = await readSource(sources, role);
      await core.validateSourceByContract(loadedSources[role], plan, role);
    }
    return loadedSources[role];
  }
  async function loadFamilySources(key) {
    const result = {};
    for (const role of familyRoles(plan, key)) result[role] = await loadRole(role);
    return result;
  }

  const cardRoles = familyRoles(plan, 'cartas');
  if (cardRoles.length !== 1) throw new Error('família cartas deve declarar exatamente uma fonte física');
  const updated = await loadRole(cardRoles[0]);

  const cards = await family('Cartas', 18, async () => {
    const records = await core.extractCardsFromCpk(updated, plan, (message) => emit('log', { message }));
    result.diagnostico_records_pos_extract = {
      array: Array.isArray(records), tipo: typeof records,
      tamanho: Array.isArray(records) ? records.length : null,
      chaves_primeiro: records && records[0] ? Object.keys(records[0]).sort() : [],
      primeiro_tem_habilidades_fisicas: Boolean(records && records[0] && Object.prototype.hasOwnProperty.call(records[0], 'habilidades_fisicas')),
      primeiro_habilidades_fisicas_tipo: records && records[0] ? typeof records[0].habilidades_fisicas : null
    };
    const validation = core.validateCards(records);
    const csv = core.cardsToCsv(records);
    const csvPath = path.join(path.dirname(outputPath), 'cartas-fisicas.csv');
    fs.writeFileSync(csvPath, csv, 'utf8');
    result.artifacts.cards_csv = csvPath;
    // Artefato canônico para estágio: conserva bits/FKs/procedência; o CSV
    // continua sendo exclusivamente apresentação.
    result.artifacts.cards_canonical = writeJson('cartas-fisicas-canonicas.json', records);
    result.diagnostico_habilidades_fisicas = records.diagnostico_habilidades_fisicas || null;
    result.card_validation = validation;
    // A comparação é feita pelo worker Python após Dimensões, usando somente
    // `projecoes_cartas` do pedido e a baseline canônica. CSV é apresentação,
    // nunca fonte de identidade, comparação ou decisão de carga.
    emit('log', { message: `Cartas: ${validation.records} físicas; aguardando comparação canônica por card_id/FKs.` });
    result.family_seals.cartas = await familySeal(reader, plan, sources, 'cartas', records);
    return records;
  }, result);
  if (cards) {
    markContractFamily('cartas', 'ready', result.artifacts.cards_csv);
    markContractFamily('relacoes', 'ready', result.artifacts.cards_csv);
  }

  // O worker nunca abre uma fonte que o contrato ativo não solicitou. Famílias
  // que exigem uma fonte ausente do pedido ficam explicitamente pendentes, sem
  // derrubar Cartas nem forçar um fallback de layout local.
  const requested = (role) => requestedRoles.has(role);
  const metadataSources = { ...loadedSources };
  for (const key of ['dimensoes', 'catalogos', 'tecnicos', 'impetos', 'textos']) {
    Object.assign(metadataSources, await loadFamilySources(key));
  }
  const descriptors = Object.fromEntries(Object.entries(sources).map(([role, item]) => [role, {
    role, filename: item.filename, location: item.location, bytes: item.bytes, sha256: item.sha256 || null
  }]));

  let dimensions = null;
  let metadata = null;
  dimensions = await family('Dimensões', 55, async () => {
    const snapshot = await core.extractCardDimensionsByFamily(metadataSources, descriptors, (message) => emit('log', { message }));
    result.artifacts.dimensions = writeJson('dimensoes-fisicas.json', snapshot);
    result.dimensions_counts = snapshot.counts;
    result.family_seals.dimensoes = await familySeal(reader, plan, sources, 'dimensoes', snapshot);
    return snapshot;
  }, result);
  if (dimensions) markContractFamily('dimensoes', 'ready', result.artifacts.dimensions);
  metadata = await family('Metadados', 76, async () => {
    const snapshot = await core.extractMetadataByFamily(metadataSources, descriptors, (message) => emit('log', { message }));
    result.artifacts.metadata = writeJson('metadados-fisicos.json', snapshot);
    result.metadata_catalogs = Object.fromEntries(Object.entries(snapshot.catalogs || {}).map(([name, catalog]) => [name, {
      supported: Boolean(catalog && catalog.supported), records: Array.isArray(catalog && catalog.records) ? catalog.records.length : 0
    }]));
    result.family_seals.catalogos = await familySeal(reader, plan, sources, 'catalogos', snapshot.catalogs || {});
    result.family_seals.tecnicos = await familySeal(reader, plan, sources, 'tecnicos', snapshot.catalogs?.tecnicos || {});
    result.family_seals.impetos = await familySeal(reader, plan, sources, 'impetos', snapshot.catalogs?.impetos || {});
    return snapshot;
  }, result);
  if (metadata) {
    markContractFamily('catalogos', 'ready', result.artifacts.metadata);
    markContractFamily('tecnicos', 'ready', result.artifacts.metadata);
    markContractFamily('impetos', 'ready', result.artifacts.metadata);
  }

  if (familyRoles(plan, 'textos').length === 1) await family('Textos', 76, async () => {
    const textRole = familyRoles(plan, 'textos')[0];
    const catalog = await core.extractTextCatalogFromCpk(metadataSources[textRole]);
    result.artifacts.texts = writeJson('textos-fisicos.json', catalog);
    result.texts = { sections: catalog.section_count, keys: catalog.records.length, duplicate_ids: catalog.duplicate_ids.length };
    result.family_seals.textos = await familySeal(reader, plan, sources, 'textos', catalog);
    return catalog;
  }, result);
  if (result.artifacts.texts) markContractFamily('textos', 'ready', result.artifacts.texts);

  if (cards) result.families['Relações'] = { state: 'pending_database_comparison', database_write: false };
  if (cards) result.families['Ímpetos'] = { state: 'pending_database_comparison', database_write: false };
  if (metadata) {
    result.families['Técnicos'] = { state: 'pending_database_comparison', database_write: false };
    result.families['Textos'] = { state: 'pending_database_comparison', database_write: false };
  }
  if (dimensions) result.families['Dimensões'] = { state: 'pending_database_comparison', database_write: false };
  fs.writeFileSync(outputPath, JSON.stringify(result, null, 2));
  emit('progress', { stage: 'Fotografias concluídas; conferindo com o banco.', percent: 88 });
  emit('physical_complete', { result_path: outputPath, database_write: false });
}

main().catch((error) => {
  const message = String(error && error.message ? error.message : error);
  emit('fatal', { message, database_write: false });
  process.exitCode = message === 'cancelled_by_user' ? 130 : 1;
});
