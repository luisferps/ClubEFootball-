'use strict';

// Regressão permanente do contrato físico de técnicos. Somente leitura.
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.resolve(__dirname, '..', '..');
for (const file of ['mapeamento-fisico.js', 'catalog-source-map.js', 'extrator-core.js']) {
  vm.runInThisContext(fs.readFileSync(path.join(root, 'app', file), 'utf8'), { filename: file });
}

const paths = {
  dt870_updated: path.join(process.env.ProgramData || 'C:\\ProgramData', 'KONAMI', 'eFootball', 'ST', 'Download', 'dt870_console_win.cpk'),
  dt200: path.join(process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)', 'Steam', 'steamapps', 'common', 'eFootball', 'cpk', 'dt200_console_all.cpk'),
  dt870_original: path.join(process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)', 'Steam', 'steamapps', 'common', 'eFootball', 'cpk', 'dt870_console_win.cpk'),
  dt261_bra: path.join(process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)', 'Steam', 'steamapps', 'common', 'eFootball', 'cpk', 'dt261_bra_console_win.cpk')
};

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

(async () => {
  const bytes = Object.fromEntries(Object.entries(paths).map(([role, file]) => [role, new Uint8Array(fs.readFileSync(file))]));
  const descriptors = {};
  for (const [role, data] of Object.entries(bytes)) descriptors[role] = { sha256: await CLUBEF_CORE.sha256(data) };
  const result = await CLUBEF_CORE.extractMetadataByFamily(bytes, descriptors);
  const tecnicos = result.catalogs.tecnicos;
  assert(tecnicos.supported === true, 'técnicos não foram marcados como suportados');
  assert(tecnicos.records.length === 1478, `esperados 1478 técnicos, vieram ${tecnicos.records.length}`);
  assert(tecnicos.duplicate_ids.length === 0, 'há IDs de técnico duplicados');
  const capello = tecnicos.records.find((record) => record.id === '17601312850052');
  assert(capello, 'Fabio Capello não foi extraído pelo ID físico u64');
  assert(capello.idade === 44 && capello.nacionalidade_codigo === 215 && capello.afinidade_codigo === 5, 'campos compartilhados de Capello divergiram');
  assert(JSON.stringify(capello.proficiencias) === JSON.stringify({ possessionGame: 46, longBallCounter: 89, quickCounter: 57, longBall: 89, outWide: 64 }), 'proficiências de Capello divergiram');
  assert(JSON.stringify(capello.boosts.map(({ ordem, atributo_idx_canonico, delta }) => ({ ordem, atributo_idx_canonico, delta }))) === JSON.stringify([{ ordem: 1, atributo_idx_canonico: 6, delta: 1 }, { ordem: 2, atributo_idx_canonico: 10, delta: 1 }]), 'boosts de Capello divergiram');
  const conte = tecnicos.records.find((record) => record.id === '17609097478250');
  assert(conte && conte.proficiencias.overload === 96, 'Sobreposição de Conte não foi relida no bit físico comprovado');
  assert(result.catalogs.nacionalidades.records.length === 214, 'catálogo compartilhado de nacionalidades divergente');
  assert(result.catalogs.afinidades_tecnico.records.length === 8, 'catálogo de afinidades divergente');
  assert(tecnicos.records.reduce((count, record) => count + Object.keys(record.proficiencias).length, 0) === 7391, 'relações de proficiência/Sobreposição divergentes');
  assert(tecnicos.records.reduce((count, record) => count + record.boosts.length, 0) === 104, 'relações de boosts divergentes');
  assert(result.catalogs.textos.records.length === 11679, 'frente Textos deixou de ser preservada');
  assert(result.catalogs.efeitos_de_impeto.records.length === 2072, 'frente Ímpetos deixou de ser preservada');
  console.log('OK: 1478 técnicos; 214 nacionalidades; 8 afinidades; 7391 proficiências/Sobreposição; 104 boosts; Textos e Ímpetos preservados');
})().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});
