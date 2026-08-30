'use strict';

// Investigação somente leitura. Os rótulos operacionais nunca são usados como
// identidade: as seis âncoras abaixo combinam código físico de PlayerBooster e
// seção/id físicos já lidos do all.str. Um hit só seria prova se o grupo inteiro
// compartilhasse arquivo, formato e layout; números isolados são descartados.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
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
coreSource = coreSource.replace(exportMarker, `${exportMarker} extractCpk, unpackWesys,`);
vm.runInThisContext(coreSource, { filename: corePath });
const core = globalThis.CLUBEF_CORE;

const cpkPath = 'C:\\ProgramData\\KONAMI\\eFootball\\ST\\Download\\dt870_console_win.cpk';
const outputPath = path.join(__dirname, 'investigacao-ponte-rotulos-especiais-categoria0.json');
const section = 43; // E5W no all.str físico atual.
const anchors = [
  { code: 250, text_id: 116, label: 'Controle de bola' },
  { code: 261, text_id: 152, label: 'Agressividade' },
  { code: 263, text_id: 94, label: 'Velocidade' },
  { code: 265, text_id: 150, label: 'Contato físico' },
  { code: 266, text_id: 149, label: 'Equilíbrio' },
  { code: 267, text_id: 40, label: 'Salto' }
];
const exclusiveLabels = [
  'Better of Fate', 'Son of God', 'King of Football', 'The Undisputed',
  'Le Petit Prince', 'Medical', 'Striking', 'Natural-Born'
];

function sha256(buffer) {
  return crypto.createHash('sha256').update(buffer).digest('hex');
}

function encoded(values, width) {
  const out = Buffer.alloc(values.length * width);
  values.forEach((value, index) => {
    const offset = index * width;
    if (width === 1) out.writeUInt8(value, offset);
    else if (width === 2) out.writeUInt16LE(value, offset);
    else out.writeUInt32LE(value, offset);
  });
  return out;
}

function positions(buffer, needle, limit = 20) {
  const found = [];
  let cursor = 0;
  while ((cursor = buffer.indexOf(needle, cursor)) !== -1) {
    found.push(cursor);
    cursor += Math.max(1, needle.length);
    if (found.length >= limit) break;
  }
  return found;
}

function structuredHits(buffer, anchor) {
  const result = [];
  const layouts = [
    ['code_section_text', [anchor.code, section, anchor.text_id]],
    ['section_text_code', [section, anchor.text_id, anchor.code]],
    ['code_text', [anchor.code, anchor.text_id]],
    ['text_code', [anchor.text_id, anchor.code]],
    ['section_text', [section, anchor.text_id]],
    ['text_section', [anchor.text_id, section]]
  ];
  for (const width of [1, 2, 4]) {
    for (const [layout, values] of layouts) {
      if (width === 1 && values.some((value) => value > 255)) continue;
      const needle = encoded(values, width);
      const offsets = positions(buffer, needle);
      if (offsets.length) result.push({ width, layout, offsets });
    }
  }
  return result;
}

function labelHits(buffer) {
  const found = [];
  for (const label of exclusiveLabels) {
    for (const encoding of ['utf8', 'utf16le']) {
      const offsets = positions(buffer, Buffer.from(label, encoding));
      if (offsets.length) found.push({ label, encoding, offsets });
    }
  }
  return found;
}

function getBits(buffer, bitOffset, width) {
  let value = 0;
  for (let index = 0; index < width; index += 1) {
    const absolute = bitOffset + index;
    value |= ((buffer[Math.floor(absolute / 8)] >> (absolute % 8)) & 1) << index;
  }
  return value;
}

(async () => {
  const packedCpk = fs.readFileSync(cpkPath);
  const entries = core.extractCpk(new Uint8Array(packedCpk));
  const fileResults = [];
  let playerBooster = null;
  for (const name of Object.keys(entries).sort()) {
    const layers = [{ layer: 'packed', bytes: Buffer.from(entries[name]) }];
    try {
      layers.push({ layer: 'decoded', bytes: Buffer.from(await core.unpackWesys(entries[name])) });
    } catch (_) {
      // Entrada sem contêiner WESYS.
    }
    for (const { layer, bytes } of layers) {
      const anchorHits = anchors.map((anchor) => ({
        code: anchor.code,
        text_id: anchor.text_id,
        hits: structuredHits(bytes, anchor)
      })).filter((item) => item.hits.length);
      const names = labelHits(bytes);
      if (anchorHits.length || names.length) {
        fileResults.push({ file: name, layer, size: bytes.length, anchor_hits: anchorHits, label_hits: names });
      }
      if (name === 'PlayerBooster.bin' && layer === 'decoded') playerBooster = bytes;
    }
  }

  if (!playerBooster || playerBooster.length % 40 !== 0) {
    throw new Error('PlayerBooster.bin atualizado não possui layout esperado de 40 bytes');
  }
  const physicalRecords = [];
  for (let record = 0; record < playerBooster.length / 40; record += 1) {
    const raw = playerBooster.subarray(record * 40, record * 40 + 40);
    const code = getBits(raw, 112, 10);
    const anchor = anchors.find((item) => item.code === code);
    if (!anchor) continue;
    physicalRecords.push({
      code,
      record,
      category: getBits(raw, 137, 5),
      type_raw: getBits(raw, 142, 3),
      record_sha256: sha256(raw),
      raw_hex: raw.toString('hex'),
      text_anchor: { section: 'E5W', section_idx: section, text_id: anchor.text_id, label: anchor.label },
      exact_text_id_u8_offsets_in_record: positions(raw, encoded([anchor.text_id], 1)),
      exact_section_text_u8_offsets_in_record: positions(raw, encoded([section, anchor.text_id], 1)),
      exact_section_text_u16le_offsets_in_record: positions(raw, encoded([section, anchor.text_id], 2))
    });
  }

  const commonStructuredLayouts = [];
  for (const file of fileResults) {
    for (const width of [1, 2, 4]) {
      for (const layout of ['code_section_text', 'section_text_code', 'code_text', 'text_code']) {
        const covered = anchors.filter((anchor) => file.anchor_hits.some((item) =>
          item.code === anchor.code && item.hits.some((hit) => hit.width === width && hit.layout === layout)
        )).map((anchor) => anchor.code);
        if (covered.length === anchors.length) {
          commonStructuredLayouts.push({ file: file.file, layer: file.layer, width, layout, covered_codes: covered });
        }
      }
    }
  }

  const report = {
    schema: 'clubef-investigacao-ponte-rotulos-especiais-categoria0-v1',
    generated_at: new Date().toISOString(),
    read_only: true,
    executable_scanned: false,
    source: { path: cpkPath, sha256: sha256(packedCpk), entries: Object.keys(entries).length },
    dictionary_anchors: anchors,
    physical_player_booster_records: physicalRecords,
    files_with_numeric_or_label_candidates: fileResults,
    common_structured_layouts_covering_all_six: commonStructuredLayouts,
    conclusion: commonStructuredLayouts.length
      ? 'candidato_estrutural_requer_validacao_manual'
      : 'ponte_fisica_texto_codigo_nao_encontrada_no_dt870_atualizado',
    boundary: 'rótulos operacionais permanecem apresentação; secao_texto/id_texto continuam nulos e a pendência continua ativa'
  };
  fs.writeFileSync(outputPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  process.stdout.write(`${JSON.stringify({
    output_path: outputPath,
    source: report.source,
    physical_records: physicalRecords.length,
    files_with_candidates: fileResults.length,
    common_structured_layouts: commonStructuredLayouts,
    conclusion: report.conclusion
  }, null, 2)}\n`);
})().catch((error) => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});
