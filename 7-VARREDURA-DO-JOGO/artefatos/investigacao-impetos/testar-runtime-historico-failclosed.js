'use strict';

const fs = require('fs');
const path = require('path');
const { webcrypto } = require('crypto');

if (!globalThis.crypto) globalThis.crypto = webcrypto;

const root = path.resolve(__dirname, '..', '..');
const run = path.join(root, 'artefatos', 'desktop', 'run-20260830-005609');
const plan = JSON.parse(fs.readFileSync(path.join(run, 'pedido-leitura.json'), 'utf8'));
const descriptors = JSON.parse(fs.readFileSync(path.join(run, 'fontes.json'), 'utf8'));
const physicalConclusion = JSON.parse(fs.readFileSync(path.join(__dirname, 'conclusao-reconciliacao-codigos-historicos.json'), 'utf8'));

for (const relative of [
  'app/mapeamento-fisico.js',
  'app/leitura-contrato.js',
  'app/extrator-core.js',
  'app/contrato-v46-runtime.js',
  'app/metadata-v46-runtime.js'
]) require(path.join(root, relative));

async function main() {
  const roles = ['dt200', 'dt261_bra', 'dt870_original', 'dt870_updated'];
  const sources = {};
  for (const role of roles) {
    sources[role] = new Uint8Array(fs.readFileSync(descriptors[role].location));
    await globalThis.CLUBEF_CORE.validateSourceByContract(sources[role], plan, role);
  }
  const metadata = await globalThis.CLUBEF_CORE.extractMetadataByFamily(sources, descriptors);
  const impetus = metadata.catalogs.impetos;
  if (!impetus.supported) throw new Error(`Ímpetos não suportados: ${impetus.reason}`);
  const originalLeaked = impetus.records.filter(record => (record.origins || []).includes('dt870_original'));
  const historical = impetus.historical_source;
  if (originalLeaked.length) throw new Error('DT870 original vazou para a união canônica');
  if (!historical || historical.canonical_merge_enabled !== false) throw new Error('fonte histórica não está fail-closed');
  const byNumber = new Map(historical.records.map(record => [record.record_number, record]));
  const proof = physicalConclusion.evidence.map(expected => {
    const actual = byNumber.get(expected.record_number_one_based);
    return {
      database_code: expected.database_code,
      raw_code: actual && actual.raw_code,
      record_number: expected.record_number_one_based,
      record_sha256: actual && actual.record_sha256,
      exact: Boolean(actual && actual.raw_code === expected.raw_code && actual.record_sha256 === expected.record_sha256)
    };
  });
  if (!proof.every(item => item.exact)) throw new Error('readback físico histórico divergiu da prova anterior');
  const result = {
    test: 'runtime_historico_failclosed',
    passed: true,
    read_only: true,
    database_write: false,
    domain_write: false,
    canonical_records: impetus.records.length,
    canonical_records_with_dt870_original: originalLeaked.length,
    historical_records: historical.records.length,
    historical_prefix_bytes: historical.prefix_bytes,
    historical_source_sha256: historical.source_file_sha256,
    historical_semantic_status: historical.semantic_status,
    historical_canonical_merge_enabled: historical.canonical_merge_enabled,
    displacement_candidates_verified: proof.filter(item => item.exact).length,
    displacement_candidates_total: proof.length,
    samples: proof.slice(0, 3)
  };
  const target = path.join(__dirname, 'teste-runtime-historico-failclosed.json');
  fs.writeFileSync(target, JSON.stringify(result, null, 2));
  process.stdout.write(`${target}\n`);
}

main().catch(error => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});
