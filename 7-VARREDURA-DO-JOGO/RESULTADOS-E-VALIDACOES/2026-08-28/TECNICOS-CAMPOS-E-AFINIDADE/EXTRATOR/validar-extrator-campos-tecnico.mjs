import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const task = 'C:/Users/Luis Fernando/Documents/Codex/2026-08-27/atualizar-extrator-carga-atual';
const app = process.env.CLUBEF_TEST_APP_DIR || `${task}/outputs/SISTEMA-EXTRATOR/app`;
const referenceRoot = 'C:/Users/Luis Fernando/Downloads/Clubefootball V4/7-VARREDURA-DO-JOGO/artefatos/referencias-metadados';
const output = `${task}/outputs/02-carga-atual/tecnicos-2026-08-28/campos-apresentacao-v1/VALIDACAO-EXTRATOR-CAMPOS-TECNICO.json`;
const sources = {
  dt870_updated: 'C:/ProgramData/KONAMI/eFootball/ST/Download/dt870_console_win.cpk',
  dt200: 'C:/Program Files (x86)/Steam/steamapps/common/eFootball/cpk/dt200_console_all.cpk',
  dt870_original: 'C:/Program Files (x86)/Steam/steamapps/common/eFootball/cpk/dt870_console_win.cpk',
  dt261_bra: 'C:/Program Files (x86)/Steam/steamapps/common/eFootball/cpk/dt261_bra_console_win.cpk',
};

for (const script of ['mapeamento-fisico.js', 'catalog-source-map.js', 'extrator-core.js']) {
  vm.runInThisContext(fs.readFileSync(`${app}/${script}`, 'utf8'), { filename: script });
}
const core = globalThis.CLUBEF_CORE;
const sourceBytes = {};
const descriptors = {};
for (const [role, file] of Object.entries(sources)) {
  const buffer = fs.readFileSync(file);
  sourceBytes[role] = new Uint8Array(buffer);
  descriptors[role] = {
    role,
    path: file,
    bytes: buffer.length,
    sha256: crypto.createHash('sha256').update(buffer).digest('hex'),
  };
}

const logs = [];
const current = await core.extractMetadataByFamily(sourceBytes, descriptors, (message) => logs.push(message));
const pointer = JSON.parse(fs.readFileSync(path.join(referenceRoot, 'referencia-vigente.json'), 'utf8'));
const snapshot = JSON.parse(fs.readFileSync(path.join(referenceRoot, 'versoes', pointer.reference_id, 'snapshot.json'), 'utf8'));
const diff = core.compareMetadata(current, snapshot);
const technicians = current.catalogs.tecnicos.records;
const nationalities = current.catalogs.nacionalidades.records;
const affinities = current.catalogs.afinidades_tecnico.records;
const capello = technicians.find((row) => row.id === '17601312850052');
const expected = {
  technicians: 1478,
  nationalities: 214,
  affinities: 8,
  capello: {
    idade: 44,
    nacionalidade_codigo: 215,
    nacionalidade_nome_pt_br: 'Itália',
    nacionalidade_sigla: 'ITA',
    afinidade_codigo: 5,
  },
};
const errors = [];
if (technicians.length !== expected.technicians || new Set(technicians.map((row) => row.id)).size !== expected.technicians) errors.push('técnicos não fecham 1.478 IDs únicos');
if (nationalities.length !== expected.nationalities || new Set(nationalities.map((row) => row.id)).size !== expected.nationalities) errors.push('nacionalidades não fecham 214 códigos únicos');
if (affinities.length !== expected.affinities || new Set(affinities.map((row) => row.id)).size !== expected.affinities) errors.push('afinidades não fecham códigos 0..7');
for (const [field, value] of Object.entries(expected.capello)) if (!capello || capello[field] !== value) errors.push(`Capello divergiu em ${field}`);
if (technicians.some((row) => !nationalities.some((country) => country.codigo_jogo === row.nacionalidade_codigo))) errors.push('há técnico com nacionalidade órfã');
for (const family of ['tecnicos', 'nacionalidades', 'afinidades_tecnico']) {
  const result = diff[family];
  if (!result || result.status !== 'comparado' || result.new_entries.length || result.changed_entries.length || result.absent_entries.length || result.without_previous_fingerprint) {
    errors.push(`${family} divergiu da referência interna selada`);
  }
}
const document = {
  contract: 'clubef-extractor-coach-display-validation-v1',
  generated_at: new Date().toISOString(),
  database_write: false,
  executable_used: false,
  app_source_directory: app,
  reference_id: pointer.reference_id,
  sources: descriptors,
  counts: {
    technicians: technicians.length,
    technician_unique_ids: new Set(technicians.map((row) => row.id)).size,
    nationalities: nationalities.length,
    affinities: affinities.length,
  },
  sample_capello: capello,
  comparison: Object.fromEntries(['tecnicos', 'nacionalidades', 'afinidades_tecnico'].map((family) => [family, {
    status: diff[family]?.status,
    new: diff[family]?.new_entries.length,
    changed: diff[family]?.changed_entries.length,
    absent: diff[family]?.absent_entries.length,
    without_previous_fingerprint: diff[family]?.without_previous_fingerprint,
  }])),
  logs,
  passed: errors.length === 0,
  errors,
};
fs.writeFileSync(output, `${JSON.stringify(document, null, 2)}\n`, 'utf8');
process.stdout.write(`${JSON.stringify({
  passed: document.passed,
  reference_id: document.reference_id,
  counts: document.counts,
  comparison: document.comparison,
  output,
  errors,
}, null, 2)}\n`);
if (errors.length) process.exitCode = 1;
