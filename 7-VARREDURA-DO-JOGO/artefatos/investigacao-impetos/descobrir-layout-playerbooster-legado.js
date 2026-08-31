'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const crypto = require('crypto');

const root = path.resolve(__dirname, '..', '..');
for (const file of ['leitura-contrato.js', 'mapeamento-fisico.js', 'catalog-source-map.js']) {
  const full = path.join(root, 'app', file);
  vm.runInThisContext(fs.readFileSync(full, 'utf8'), { filename: full });
}
const corePath = path.join(root, 'app', 'extrator-core.js');
let source = fs.readFileSync(corePath, 'utf8');
source = source.replace('global.CLUBEF_CORE = Object.freeze({', 'global.CLUBEF_CORE = Object.freeze({ extractCpk, unpackWesys,');
vm.runInThisContext(source, { filename: corePath });

const CPK = 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\eFootball\\cpk\\dt870_console_win.cpk';
const sha256 = buffer => crypto.createHash('sha256').update(buffer).digest('hex');
function readBits(buffer, absoluteBit, width) {
  let value = 0;
  for (let bit = 0; bit < width; bit++) {
    const current = absoluteBit + bit;
    value |= ((buffer[Math.floor(current / 8)] >> (current % 8)) & 1) << bit;
  }
  return value >>> 0;
}

(async () => {
  const cpk = globalThis.CLUBEF_CORE.extractCpk(new Uint8Array(fs.readFileSync(CPK)));
  const raw = Buffer.from(await globalThis.CLUBEF_CORE.unpackWesys(cpk['PlayerBooster.bin']));
  const index = globalThis.CLUBEF_CATALOG_SOURCE_MAP.BOOSTER_DT870_ORIGINAL_INDEX;
  const pairs = Object.entries(index).map(([code, locator]) => ({ code: Number(code), locator: Number(locator) }));
  const hypotheses = {
    locator_8_bytes_one_based: locator => (locator - 1) * 8,
    locator_8_bytes_zero_based: locator => locator * 8,
    locator_16_bytes_one_based: locator => (locator - 1) * 16,
    antigo_prefixo24_stride40: locator => 24 + (locator - 1) * 40
  };
  const scans = {};
  for (const [name, offsetOf] of Object.entries(hypotheses)) {
    const candidates = [];
    for (let relativeBit = 0; relativeBit < 128; relativeBit++) {
      for (let width = 8; width <= 16; width++) {
        let matches = 0;
        let available = 0;
        for (const pair of pairs) {
          const byteOffset = offsetOf(pair.locator);
          if (byteOffset < 0 || byteOffset + Math.ceil((relativeBit + width) / 8) > raw.length) continue;
          available++;
          if (readBits(raw, byteOffset * 8 + relativeBit, width) === pair.code) matches++;
        }
        if (matches) candidates.push({ relative_bit: relativeBit, width, matches, available });
      }
    }
    scans[name] = candidates.sort((a, b) => b.matches - a.matches || a.relative_bit - b.relative_bit || a.width - b.width).slice(0, 25);
  }
  const samples = pairs.slice().sort((a, b) => a.locator - b.locator).map(pair => {
    const offset = (pair.locator - 1) * 8;
    return {
      ...pair,
      byte_offset: offset,
      bytes_8: raw.subarray(offset, offset + 8).toString('hex'),
      bytes_16: raw.subarray(offset, offset + 16).toString('hex')
    };
  });
  const result = {
    schema: 'clubef-playerbooster-legado-layout-search-v1',
    read_only: true,
    source: { path: CPK, playerbooster_bytes: raw.length, playerbooster_sha256: sha256(raw) },
    mapped_pairs: pairs.length,
    scans,
    samples
  };
  const target = path.join(__dirname, 'descoberta-layout-playerbooster-legado.json');
  fs.writeFileSync(target, JSON.stringify(result, null, 2));
  process.stdout.write(JSON.stringify({ target, mapped_pairs: pairs.length, best: Object.fromEntries(Object.entries(scans).map(([key, value]) => [key, value.slice(0, 5)])) }, null, 2));
})().catch(error => { process.stderr.write(`${error.stack || error}\n`); process.exitCode = 1; });
