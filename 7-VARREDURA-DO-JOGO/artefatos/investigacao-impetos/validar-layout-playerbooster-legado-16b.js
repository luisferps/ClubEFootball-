'use strict';

// Prova física somente leitura do formato PlayerBooster legado presente no
// DT870 da instalação Steam. Não usa o layout atual de 40 bytes e não promove
// o catálogo histórico à união canônica.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const vm = require('vm');

const root = path.resolve(__dirname, '..', '..');
for (const file of ['leitura-contrato.js', 'mapeamento-fisico.js']) {
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

const cpkPath = 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\eFootball\\cpk\\dt870_console_win.cpk';
const expectedTargets = [
  204, 209, 214, 219, 224, 229, 234, 239, 244, 249, 254,
  259, 269, 274, 279, 284, 289, 294, 299, 309, 334, 369
];
const sha256 = buffer => crypto.createHash('sha256').update(buffer).digest('hex');

function decodeRecord(bytes, index) {
  const ordinal = bytes[6];
  const code = ordinal === 0 ? null : (ordinal * 5) - 1;
  const attributeMask = bytes.readUInt32LE(12);
  return {
    record_index: index,
    record_number: index + 1,
    byte_offset: index * 16,
    raw_hex: bytes.toString('hex'),
    record_sha256: sha256(bytes),
    ordinal,
    codigo_jogo: code,
    codigo_regra: ordinal === 0 ? 'ausente' : '5 * ordinal - 1',
    tipo_efeito_raw: bytes[7],
    metadados_raw_hex: bytes.subarray(0, 12).toString('hex'),
    mascara_atributos_raw_u32: attributeMask,
    mascara_atributos_raw_hex: attributeMask.toString(16).padStart(8, '0'),
    bits_atributos_ativos: Array.from({ length: 32 }, (_, bit) => bit)
      .filter(bit => ((attributeMask >>> bit) & 1) === 1)
  };
}

(async () => {
  const cpkBytes = fs.readFileSync(cpkPath);
  const cpk = globalThis.CLUBEF_CORE.extractCpk(new Uint8Array(cpkBytes));
  const raw = Buffer.from(await globalThis.CLUBEF_CORE.unpackWesys(cpk['PlayerBooster.bin']));
  if (raw.length % 16 !== 0) throw new Error(`PlayerBooster legado não é divisível por 16: ${raw.length}`);
  const records = [];
  for (let offset = 0, index = 0; offset < raw.length; offset += 16, index += 1) {
    records.push(decodeRecord(raw.subarray(offset, offset + 16), index));
  }
  const byCode = new Map();
  for (const record of records) {
    if (record.codigo_jogo === null) continue;
    if (!byCode.has(record.codigo_jogo)) byCode.set(record.codigo_jogo, []);
    byCode.get(record.codigo_jogo).push(record);
  }
  const targetProof = expectedTargets.map(code => {
    const matches = byCode.get(code) || [];
    return {
      codigo_jogo: code,
      ocorrencias: matches.length,
      correspondencia_unica: matches.length === 1,
      registro: matches[0] || null
    };
  });
  const result = {
    schema: 'clubef-playerbooster-legado-layout-16b-v1',
    read_only: true,
    source: {
      role: 'dt870_original',
      historical_only: true,
      cpk_path: cpkPath,
      cpk_sha256: sha256(cpkBytes),
      arquivo: 'PlayerBooster.bin',
      arquivo_bytes: raw.length,
      arquivo_sha256: sha256(raw)
    },
    layout: {
      record_size: 16,
      prefix_bytes: 0,
      records: records.length,
      exact_division: raw.length === records.length * 16,
      canonical_merge_enabled: false
    },
    identity: {
      ordinal_byte_offset: 6,
      formula: 'codigo_jogo = 5 * ordinal - 1; ordinal 0 não declara identidade',
      unique_nonzero_codes: [...byCode.values()].filter(items => items.length === 1).length,
      duplicate_nonzero_codes: [...byCode.entries()]
        .filter(([, items]) => items.length > 1)
        .map(([code, items]) => ({ codigo_jogo: code, registros: items.map(item => item.record_number) }))
    },
    target_proof: targetProof,
    target_summary: {
      requested: expectedTargets.length,
      unique_matches: targetProof.filter(item => item.correspondencia_unica).length,
      missing: targetProof.filter(item => item.ocorrencias === 0).map(item => item.codigo_jogo),
      duplicated: targetProof.filter(item => item.ocorrencias > 1).map(item => item.codigo_jogo)
    },
    records
  };
  if (result.layout.records !== 414) throw new Error(`cardinalidade histórica inesperada: ${result.layout.records}`);
  if (result.target_summary.unique_matches !== expectedTargets.length) {
    throw new Error(`identidade dos alvos não é única: ${JSON.stringify(result.target_summary)}`);
  }
  const output = path.join(__dirname, 'validacao-layout-playerbooster-legado-16b.json');
  fs.writeFileSync(output, `${JSON.stringify(result, null, 2)}\n`, 'utf8');
  process.stdout.write(`${JSON.stringify({ output, source: result.source, layout: result.layout, identity: result.identity, target_summary: result.target_summary }, null, 2)}\n`);
})().catch(error => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});
