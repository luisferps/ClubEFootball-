'use strict';

// Reexecuta toda a cadeia cumulativa sem habilitar escrita no banco.
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.resolve(__dirname, '..', '..');
const reviewPort = process.env.CLUBEF_REVIEW_PORT || '8765';
const baseUrl = `http://127.0.0.1:${reviewPort}`;
for (const file of ['mapeamento-fisico.js', 'catalog-source-map.js', 'extrator-core.js']) {
  vm.runInThisContext(fs.readFileSync(path.join(root, 'app', file), 'utf8'), { filename: file });
}

const paths = {
  dt870_updated: path.join(process.env.ProgramData || 'C:\\ProgramData', 'KONAMI', 'eFootball', 'ST', 'Download', 'dt870_console_win.cpk'),
  dt200: path.join(process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)', 'Steam', 'steamapps', 'common', 'eFootball', 'cpk', 'dt200_console_all.cpk'),
  dt870_original: path.join(process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)', 'Steam', 'steamapps', 'common', 'eFootball', 'cpk', 'dt870_console_win.cpk'),
  dt261_bra: path.join(process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)', 'Steam', 'steamapps', 'common', 'eFootball', 'cpk', 'dt261_bra_console_win.cpk')
};

function assert(condition, message) { if (!condition) throw new Error(message); }
function stableEvidence(value) {
  if (Array.isArray(value)) return value.map(stableEvidence);
  if (!value || typeof value !== 'object') return value;
  return Object.fromEntries(Object.entries(value)
    .filter(([key]) => !['generated_at', 'extraido_em', 'carregado_em'].includes(key))
    .map(([key, item]) => [key, stableEvidence(item)]));
}
async function getJson(url) {
  const response = await fetch(url, { cache: 'no-store' });
  const payload = await response.json();
  if (!response.ok) throw new Error(`${url}: ${payload.error || `HTTP ${response.status}`}`);
  return payload;
}
async function postJson(url, body) {
  const response = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const payload = await response.json();
  if (!response.ok) throw new Error(`${url}: ${payload.error || payload.result || `HTTP ${response.status}`}\n${JSON.stringify(payload, null, 2)}`);
  return payload;
}

const bytes = Object.fromEntries(Object.entries(paths).map(([role, file]) => [role, new Uint8Array(fs.readFileSync(file))]));

async function runOnce(index) {
  const descriptors = {};
  for (const [role, data] of Object.entries(bytes)) descriptors[role] = { role, sha256: await CLUBEF_CORE.sha256(data) };
  const status = await getJson(`${baseUrl}/api/status`);
  assert(status.write_enabled === false, 'executor não permaneceu com escrita automática desligada');
  const physical = await CLUBEF_CORE.extractMetadataByFamily(bytes, descriptors);
  const cards = await CLUBEF_CORE.extractCardsFromCpk(bytes.dt870_updated);
  assert(cards.length === 43072, `cartas físicas: ${cards.length}`);
  const rows = cards.map(CLUBEF_CORE.cardToRow);
  const relations = await postJson(`${baseUrl}/api/card-relations/validate`, { card_csv: CLUBEF_CORE.rowsToCsv(rows) });
  const dimensionsSnapshot = await CLUBEF_CORE.extractCardDimensionsByFamily(bytes, descriptors);
  const dimensions = await postJson(`${baseUrl}/api/card-dimensions/validate`, { snapshot: dimensionsSnapshot });
  const text = await getJson(`${baseUrl}/api/text-baseline/current.json`);
  const techniciansSnapshot = {
    ...physical.catalogs.tecnicos,
    nationalities: physical.catalogs.nacionalidades.records,
    affinities: physical.catalogs.afinidades_tecnico.records
  };
  const technicians = await postJson(`${baseUrl}/api/tecnicos/validate`, { snapshot: techniciansSnapshot });
  const impetus = await postJson(`${baseUrl}/api/impetos/validate`, { snapshot: physical.catalogs.impetos });
  for (const [name, result] of Object.entries({ relations, dimensions, technicians, impetus })) {
    assert(result.passed && result.transaction_read_only && result.database_write === false, `${name} não aprovou o contrato read-only`);
  }
  assert(text.records === 11679 && text.catalog_references_checked === 166 && text.validated_foreign_keys === 8, 'Texto não preservou 11.679 chaves, 166 referências e 8 FKs');
  assert(text.transaction_read_only && text.database_write === false && text.unresolved_catalog_references === 0 && text.unvalidated_foreign_keys === 0, 'Texto não aprovou o contrato read-only integral');
  const evidence = stableEvidence({
    sources: descriptors,
    physical_counts: {
      technicians: physical.catalogs.tecnicos.records.length,
      nationalities: physical.catalogs.nacionalidades.records.length,
      affinities: physical.catalogs.afinidades_tecnico.records.length,
      texts: physical.catalogs.textos.records.length,
      impetus_union: physical.catalogs.impetos.records.length,
      impetus_effects: physical.catalogs.efeitos_de_impeto.records.length,
      cards: rows.length
    },
    relations, dimensions, technicians, impetus,
    text: {
      records: text.records, unique_official_keys: text.unique_official_keys,
      sha256: text.sha256, catalog_references_checked: text.catalog_references_checked,
      unresolved_catalog_references: text.unresolved_catalog_references,
      validated_foreign_keys: text.validated_foreign_keys,
      unvalidated_foreign_keys: text.unvalidated_foreign_keys,
      transaction_read_only: text.transaction_read_only, database_write: text.database_write
    }
  });
  const fingerprint = await CLUBEF_CORE.sha256(CLUBEF_CORE.stableJson(evidence));
  console.log(`execução ${index}: ${fingerprint}`);
  return { fingerprint, evidence };
}

(async () => {
  const first = await runOnce(1);
  const second = await runOnce(2);
  assert(first.fingerprint === second.fingerprint, 'as duas releituras produziram fingerprints diferentes');
  console.log(JSON.stringify({
    result: 'APROVADO', database_write: false, runs: 2, fingerprint: first.fingerprint,
    counts: first.evidence.physical_counts,
    relation_rows: Object.fromEntries(Object.entries(first.evidence.relations.relations).map(([name, item]) => [name, item.database_rows])),
    dimension_counts: Object.fromEntries(Object.entries(first.evidence.dimensions.comparisons).map(([name, item]) => [name, item.database])),
    impetus: {
      effects: first.evidence.impetus.checks.effects.database,
      conditions: first.evidence.impetus.checks.conditions.database,
      ranges: first.evidence.impetus.checks.ranges.database,
      league_members: first.evidence.impetus.checks.competition_unit_members.database,
      consumer_apt: first.evidence.impetus.checks.consumer_readiness.condicoes_aptas
    }
  }, null, 2));
})().catch((error) => { console.error(error.stack || error.message); process.exitCode = 1; });
