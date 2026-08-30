'use strict';

// Diagnóstico somente leitura: expõe em memória os decodificadores já
// carregados pelo Extrator e procura uma ponte de texto nos CPKs oficiais.
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const operationalRoot = path.resolve(__dirname, '..', '..');
const corePath = path.join(operationalRoot, 'app', 'extrator-core.js');
for (const dependency of ['leitura-contrato.js', 'mapeamento-fisico.js', 'catalog-source-map.js']) {
  const dependencyPath = path.join(operationalRoot, 'app', dependency);
  vm.runInThisContext(fs.readFileSync(dependencyPath, 'utf8'), { filename: dependencyPath });
}
let coreSource = fs.readFileSync(corePath, 'utf8');
const exportMarker = 'global.CLUBEF_CORE = Object.freeze({';
if (!coreSource.includes(exportMarker)) throw new Error('marcador de exportação do núcleo não encontrado');
coreSource = coreSource.replace(
  exportMarker,
  `${exportMarker} extractCpk, unpackWesys,`
);
vm.runInThisContext(coreSource, { filename: corePath });

const core = globalThis.CLUBEF_CORE;
const cpks = {
  dt200: 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\eFootball\\cpk\\dt200_console_all.cpk',
  dt261_bra: 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\eFootball\\cpk\\dt261_bra_console_win.cpk',
  dt870_original: 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\eFootball\\cpk\\dt870_console_win.cpk',
  dt870_updated: 'C:\\ProgramData\\KONAMI\\eFootball\\ST\\Download\\dt870_console_win.cpk'
};
const tokens = [
  'BoosterTextId', 'TextID_Name', 'Name_Hash', 'STR_BOOSTER',
  'Any3W', 'Defesaça', 'BoosterData', '.locres'
];
const bridgeSequence = [
  [26, 15, 62],
  [28, 15, 63],
  [30, 15, 64],
  [32, 15, 65],
  [34, 15, 66],
  [36, 15, 67]
];

function findAll(buffer, needle) {
  const hits = [];
  let offset = 0;
  while ((offset = buffer.indexOf(needle, offset)) !== -1) {
    hits.push(offset);
    offset += Math.max(1, needle.length);
    if (hits.length === 20) break;
  }
  return hits;
}

function tokenHits(buffer) {
  const result = [];
  for (const token of tokens) {
    const variants = [
      ['utf8', Buffer.from(token, 'utf8')],
      ['utf16le', Buffer.from(token, 'utf16le')]
    ];
    for (const [encoding, needle] of variants) {
      const offsets = findAll(buffer, needle);
      if (offsets.length) result.push({ token, encoding, offsets });
    }
  }
  return result;
}

function encodeTriple(width, values) {
  const encoded = Buffer.alloc(width * 3);
  values.forEach((value, index) => {
    const offset = index * width;
    if (width === 1) encoded.writeUInt8(value, offset);
    else if (width === 2) encoded.writeUInt16LE(value, offset);
    else encoded.writeUInt32LE(value, offset);
  });
  return encoded;
}

function structuredBridgeHits(buffer) {
  const result = [];
  for (const width of [1, 2, 4]) {
    const recordSize = width * 3;
    const first = encodeTriple(width, bridgeSequence[0]);
    let offset = 0;
    while ((offset = buffer.indexOf(first, offset)) !== -1) {
      for (let stride = recordSize; stride <= 32; stride += 1) {
        const valid = bridgeSequence.every((triple, index) => {
          const expected = encodeTriple(width, triple);
          const start = offset + index * stride;
          return start + recordSize <= buffer.length
            && buffer.subarray(start, start + recordSize).equals(expected);
        });
        if (valid) {
          const contextStart = Math.max(0, offset - 16);
          const contextEnd = Math.min(buffer.length, offset + bridgeSequence.length * stride + 16);
          result.push({
            offset,
            offset_hex: `0x${offset.toString(16)}`,
            format: `u${width * 8}le`,
            stride,
            context_offset: contextStart,
            context_hex: buffer.subarray(contextStart, contextEnd).toString('hex')
          });
        }
      }
      offset += 1;
    }
  }
  return result;
}

function isolatedSequenceHits(buffer, values) {
  const result = [];
  for (const width of [1, 2, 4]) {
    const encode = (value) => {
      const encoded = Buffer.alloc(width);
      if (width === 1) encoded.writeUInt8(value);
      else if (width === 2) encoded.writeUInt16LE(value);
      else encoded.writeUInt32LE(value);
      return encoded;
    };
    const first = encode(values[0]);
    let offset = 0;
    while ((offset = buffer.indexOf(first, offset)) !== -1) {
      for (let stride = width; stride <= 128; stride += 1) {
        const valid = values.every((value, index) => {
          const start = offset + index * stride;
          return start + width <= buffer.length
            && buffer.subarray(start, start + width).equals(encode(value));
        });
        if (valid) {
          const contextStart = Math.max(0, offset - 32);
          const contextEnd = Math.min(buffer.length, offset + values.length * stride + 32);
          result.push({
            offset,
            offset_hex: `0x${offset.toString(16)}`,
            format: `u${width * 8}le`,
            stride,
            context_offset: contextStart,
            context_hex: buffer.subarray(contextStart, contextEnd).toString('hex')
          });
          if (result.length >= 100) return result;
        }
      }
      offset += 1;
    }
  }
  return result;
}

(async () => {
  const report = {
    generated_at: new Date().toISOString(),
    read_only: true,
    executable_scanned: false,
    sources: []
  };
  for (const [role, cpkPath] of Object.entries(cpks)) {
    if (!fs.existsSync(cpkPath)) {
      report.sources.push({ role, cpk_path: cpkPath, status: 'ausente' });
      continue;
    }
    const cpkBytes = new Uint8Array(fs.readFileSync(cpkPath));
    const entries = core.extractCpk(cpkBytes);
    const names = Object.keys(entries).sort();
    const interestingNames = names.filter((name) =>
      /booster|text|string|loc|language|message|game.?define|ui/i.test(name)
    );
    const hits = [];
    const structuredHits = [];
    const isolatedTextSequenceHits = [];
    const isolatedCategorySequenceHits = [];
    for (const name of names) {
      const packed = entries[name];
      const packedHits = tokenHits(Buffer.from(packed));
      if (packedHits.length) hits.push({ file: name, layer: 'packed', hits: packedHits });
      const packedBridgeHits = structuredBridgeHits(Buffer.from(packed));
      if (packedBridgeHits.length) structuredHits.push({ file: name, layer: 'packed', hits: packedBridgeHits });
      const packedTextSequence = isolatedSequenceHits(Buffer.from(packed), [62, 63, 64, 65, 66, 67]);
      if (packedTextSequence.length) isolatedTextSequenceHits.push({ file: name, layer: 'packed', hits: packedTextSequence });
      const packedCategorySequence = isolatedSequenceHits(Buffer.from(packed), [26, 28, 30, 32, 34, 36]);
      if (packedCategorySequence.length) isolatedCategorySequenceHits.push({ file: name, layer: 'packed', hits: packedCategorySequence });
      try {
        const raw = await core.unpackWesys(packed);
        const decodedHits = tokenHits(Buffer.from(raw));
        if (decodedHits.length) hits.push({ file: name, layer: 'decoded', hits: decodedHits });
        const decodedBridgeHits = structuredBridgeHits(Buffer.from(raw));
        if (decodedBridgeHits.length) structuredHits.push({ file: name, layer: 'decoded', hits: decodedBridgeHits });
        const decodedTextSequence = isolatedSequenceHits(Buffer.from(raw), [62, 63, 64, 65, 66, 67]);
        if (decodedTextSequence.length) isolatedTextSequenceHits.push({ file: name, layer: 'decoded', hits: decodedTextSequence });
        const decodedCategorySequence = isolatedSequenceHits(Buffer.from(raw), [26, 28, 30, 32, 34, 36]);
        if (decodedCategorySequence.length) isolatedCategorySequenceHits.push({ file: name, layer: 'decoded', hits: decodedCategorySequence });
      } catch (_) {
        // Nem toda entrada do CPK usa o contêiner WESYS.
      }
    }
    report.sources.push({
      role,
      cpk_path: cpkPath,
      entry_count: names.length,
      interesting_names: interestingNames,
      locres_entries: names.filter((name) => /\.locres$/i.test(name)),
      token_hits: hits,
      structured_bridge_hits: structuredHits,
      isolated_text_sequence_hits: isolatedTextSequenceHits,
      isolated_category_sequence_hits: isolatedCategorySequenceHits
    });
  }
  const outputPath = path.join(__dirname, 'scan-booster-text-bridge-result.json');
  fs.writeFileSync(outputPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  const summary = report.sources.map((source) => ({
    role: source.role,
    entry_count: source.entry_count ?? 0,
    token_hit_files: source.token_hits?.map((item) => item.file) ?? [],
    structured_bridge_hit_files: source.structured_bridge_hits?.map((item) => item.file) ?? [],
    isolated_text_sequence_hit_files: source.isolated_text_sequence_hits?.map((item) => item.file) ?? [],
    isolated_category_sequence_hit_files: source.isolated_category_sequence_hits?.map((item) => item.file) ?? []
  }));
  process.stdout.write(`${JSON.stringify({ output_path: outputPath, summary }, null, 2)}\n`);
})().catch((error) => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});
