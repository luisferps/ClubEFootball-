'use strict';

// Diagnóstico físico somente leitura do contêiner legado. Não aplica o layout
// de 40 bytes atual nem promove a tabela local de índices como prova semântica.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const vm = require('vm');

const root = path.resolve(__dirname, '..', '..');
for (const file of ['leitura-contrato.js', 'mapeamento-fisico.js', 'catalog-source-map.js']) {
  const full = path.join(root, 'app', file);
  vm.runInThisContext(fs.readFileSync(full, 'utf8'), { filename: full });
}
const corePath = path.join(root, 'app', 'extrator-core.js');
let source = fs.readFileSync(corePath, 'utf8');
source = source.replace(
  'global.CLUBEF_CORE = Object.freeze({',
  'global.CLUBEF_CORE = Object.freeze({ extractCpk, unpackWesys,'
);
vm.runInThisContext(source, { filename: corePath });
const core = globalThis.CLUBEF_CORE;
const sources = {
  original: 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\eFootball\\cpk\\dt870_console_win.cpk',
  updated: 'C:\\ProgramData\\KONAMI\\eFootball\\ST\\Download\\dt870_console_win.cpk'
};
const sha256 = (buffer) => crypto.createHash('sha256').update(buffer).digest('hex');
const missingTargets = [204,209,214,219,224,229,234,239,244,249,254,259,269,274,279,284,289,294,299,309,334,369];

function readBits(buffer, bitOffset, width) {
  let value = 0;
  for (let index = 0; index < width; index += 1) {
    const absolute = bitOffset + index;
    value |= ((buffer[Math.floor(absolute / 8)] >> (absolute % 8)) & 1) << index;
  }
  return value;
}

(async () => {
  const result = {};
  let originalRaw = null;
  for (const [role, cpkPath] of Object.entries(sources)) {
    const cpk = core.extractCpk(new Uint8Array(fs.readFileSync(cpkPath)));
    const raw = Buffer.from(await core.unpackWesys(cpk['PlayerBooster.bin']));
    if (role === 'original') originalRaw = raw;
    result[role] = {
      cpk_path: cpkPath,
      cpk_sha256: sha256(fs.readFileSync(cpkPath)),
      player_booster_bytes: raw.length,
      player_booster_sha256: sha256(raw),
      first_128_hex: raw.subarray(0, 128).toString('hex'),
      divisibility: Object.fromEntries([8,16,20,24,32,40,48,64,80,96,104,120,128,160,168].map((size) => [size, {
        remainder: raw.length % size,
        records: Math.floor(raw.length / size)
      }]))
    };
  }
  const originalIndex = globalThis.CLUBEF_CATALOG_SOURCE_MAP.BOOSTER_DT870_ORIGINAL_INDEX;
  result.historical_displacement_candidates = missingTargets.map((databaseCode) => {
    const mappedRecordNumber = originalIndex[databaseCode];
    if (!Number.isInteger(mappedRecordNumber) || mappedRecordNumber < 1) throw new Error(`número de registro histórico ausente para ${databaseCode}`);
    const offset = 24 + (mappedRecordNumber - 1) * 40;
    const raw = originalRaw.subarray(offset, offset + 40);
    if (raw.length !== 40) throw new Error(`registro histórico fora do arquivo para ${databaseCode}`);
    return {
      database_code: databaseCode,
      mapped_record_index_zero_based: mappedRecordNumber - 1,
      mapped_record_number_one_based: mappedRecordNumber,
      byte_offset: offset,
      raw_code_bit112_w10: readBits(raw, 112, 10),
      record_sha256: sha256(raw),
      raw_hex: raw.toString('hex')
    };
  });
  result.conclusion = result.original.player_booster_bytes % 40 === 0
    ? 'tamanho_divisivel_por_40_nao_prova_layout'
    : 'layout_atual_40_inaplicavel_ao_original';
  const out = path.join(__dirname, 'diagnostico-layout-playerbooster-original.json');
  fs.writeFileSync(out, `${JSON.stringify(result, null, 2)}\n`, 'utf8');
  process.stdout.write(`${JSON.stringify({ output: out, ...result }, null, 2)}\n`);
})().catch((error) => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});
