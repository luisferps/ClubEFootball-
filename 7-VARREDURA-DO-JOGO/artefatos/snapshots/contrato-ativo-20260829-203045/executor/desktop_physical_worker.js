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
const baselinePath = argument('--baseline');
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
function summary(diff) {
  return {
    igual: Number(diff.unchanged || 0),
    novo: Array.isArray(diff.new_cards) ? diff.new_cards.length : 0,
    alterado: Array.isArray(diff.changed_cards) ? diff.changed_cards.length : 0,
    ausente: Array.isArray(diff.possibly_inactive) ? diff.possibly_inactive.length : 0,
    duplicado: 0
  };
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
    artifacts: {}
  };
  emit('status', { database_write: false, message: 'Pedido canônico recebido; iniciando apenas leitura física.' });

  const updated = await readSource(sources, 'dt870_updated');
  await core.validateSourceByContract(updated, plan, 'dt870_updated');

  const cards = await family('Cartas', 18, async () => {
    const records = await core.extractCardsFromCpk(updated, plan, (message) => emit('log', { message }));
    const validation = core.validateCards(records);
    const csv = core.cardsToCsv(records);
    const csvPath = path.join(path.dirname(outputPath), 'cartas-fisicas.csv');
    fs.writeFileSync(csvPath, csv, 'utf8');
    result.artifacts.cards_csv = csvPath;
    result.card_validation = validation;
    const baseline = core.parseCsv(fs.readFileSync(baselinePath, 'utf8'));
    const current = core.parseCsv(csv);
    core.validateSchema(baseline.headers);
    core.validateSchema(current.headers);
    const diff = core.compareCardRows(current.rows, baseline.rows);
    result.card_comparison = summary(diff);
    result.artifacts.card_diff = writeJson('cartas-divergencias.json', diff);
    emit('log', { message: `Cartas: ${validation.records} físicas; ${result.card_comparison.alterado} alteradas.` });
    return records;
  }, result);

  // O worker nunca abre uma fonte que o contrato ativo não solicitou. Famílias
  // que exigem uma fonte ausente do pedido ficam explicitamente pendentes, sem
  // derrubar Cartas nem forçar um fallback de layout local.
  const requestedRoles = new Set((plan.arquivos || []).map((item) => item.papel_fonte).filter(Boolean));
  const requested = (role) => requestedRoles.has(role);
  const metadataSources = { dt870_updated: updated };
  for (const role of ['dt200', 'dt870_original', 'dt261_bra'].filter(requested)) {
    metadataSources[role] = await readSource(sources, role);
    await core.validateSourceByContract(metadataSources[role], plan, role);
  }
  const descriptors = Object.fromEntries(Object.entries(sources).map(([role, item]) => [role, {
    role, filename: item.filename, location: item.location, bytes: item.bytes, sha256: item.sha256 || null
  }]));

  const metadataRoles = ['dt870_updated', 'dt200', 'dt870_original', 'dt261_bra'];
  const missingForMetadata = metadataRoles.filter((role) => !requested(role));
  let dimensions = null;
  let metadata = null;
  if (missingForMetadata.length) {
    const message = `não solicitada pelo contrato ativo: faltam ${missingForMetadata.join(', ')}`;
    for (const name of ['Dimensões', 'Metadados', 'Técnicos', 'Ímpetos']) {
      result.families[name] = { state: 'not_requested_by_contract', message, database_write: false };
      emit('family', { family: name, state: 'not_requested_by_contract', message });
    }
  } else {
    dimensions = await family('Dimensões', 55, async () => {
      const snapshot = await core.extractCardDimensionsByFamily(metadataSources, descriptors, (message) => emit('log', { message }));
      result.artifacts.dimensions = writeJson('dimensoes-fisicas.json', snapshot);
      result.dimensions_counts = snapshot.counts;
      return snapshot;
    }, result);
    metadata = await family('Metadados', 76, async () => {
      const snapshot = await core.extractMetadataByFamily(metadataSources, descriptors, (message) => emit('log', { message }));
      result.artifacts.metadata = writeJson('metadados-fisicos.json', snapshot);
      result.metadata_catalogs = Object.fromEntries(Object.entries(snapshot.catalogs || {}).map(([name, catalog]) => [name, {
        supported: Boolean(catalog && catalog.supported), records: Array.isArray(catalog && catalog.records) ? catalog.records.length : 0
      }]));
      return snapshot;
    }, result);
  }

  if (requested('dt261_bra')) await family('Textos', 76, async () => {
    const catalog = await core.extractTextCatalogFromCpk(metadataSources.dt261_bra);
    result.artifacts.texts = writeJson('textos-fisicos.json', catalog);
    result.texts = { sections: catalog.section_count, keys: catalog.records.length, duplicate_ids: catalog.duplicate_ids.length };
    return catalog;
  }, result);

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
