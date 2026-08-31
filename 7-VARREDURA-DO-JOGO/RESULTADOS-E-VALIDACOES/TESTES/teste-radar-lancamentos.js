'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { webcrypto } = require('crypto');

if (!globalThis.crypto) globalThis.crypto = webcrypto;
const root = path.resolve(__dirname, '..', '..');
for (const file of ['leitura-contrato.js', 'mapeamento-fisico.js', 'extrator-core.js', 'radar-lancamentos.js', 'contrato-v46-runtime.js']) {
  vm.runInThisContext(fs.readFileSync(path.join(root, 'app', file), 'utf8'), { filename: file });
}

const fixturePath = path.join(__dirname, 'fixtures', 'radar-boxes-salvas.json');
const fixture = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));
const radar = globalThis.CLUBEF_BOX_RADAR;

function assert(condition, message) {
  if (!condition) throw new Error(message);
}
function encodeRecords(entries) {
  const bytes = new Uint8Array(entries.length * radar.RECORD_SIZE);
  const encoder = new TextEncoder();
  for (let index = 0; index < entries.length; index += 1) {
    const entry = entries[index];
    const base = index * radar.RECORD_SIZE;
    new DataView(bytes.buffer).setBigUint64(base, BigInt(entry.card_id), true);
    const name = encoder.encode(entry.box);
    assert(name.length < radar.RECORD_SIZE - radar.NAME_OFFSET, 'nome grande demais para o fixture');
    bytes.set(name, base + radar.NAME_OFFSET);
    bytes[base + radar.NAME_OFFSET + name.length] = 0;
  }
  return bytes;
}
function cards(entries) {
  return entries.map((entry) => ({ card_id: entry.card_id, name: entry.card_name, box: null }));
}
async function observation(entries, suffix) {
  return radar.observeRaw(encodeRecords(entries), {
    source: {
      role: fixture.source_role,
      cpk_file: 'dt870_console_win.cpk',
      location: `fixture://${suffix}/dt870_console_win.cpk`,
      bytes: 123456,
      modified_at: suffix === 'anterior' ? fixture.previous_generated_at : fixture.current_generated_at,
      cpk_sha256: (suffix === 'anterior' ? '11' : '22').repeat(32)
    },
    contract_verification: {
      evidence_mode: 'fixture_salvo',
      container_contract_verified: true,
      member_declared_in_active_contract: false,
      member_contract_status: 'observacional_ate_migracao_do_contrato',
      identity_or_apply_destination_declared: false,
      database_write: false
    }
  });
}
function expectParserFailure(bytes, expected) {
  let message = null;
  try { radar.parsePlayerVariationDetail(bytes); } catch (error) { message = String(error.message || error); }
  assert(message && message.includes(expected), `parser deveria falhar com "${expected}", recebeu: ${message}`);
}

(async () => {
  const savedPlanPath = path.join(root, 'artefatos', 'desktop', 'run-20260830-132440', 'pedido-leitura.json');
  const savedPlan = JSON.parse(fs.readFileSync(savedPlanPath, 'utf8'));
  const contractCheck = globalThis.CLUBEF_CORE.inspectLaunchRadarContract(savedPlan, { role: fixture.source_role });
  assert(contractCheck.container_contract_verified === true, 'âncora contratual do CPK não foi comprovada');
  assert(contractCheck.member_declared_in_active_contract === false, 'fixture deveria refletir PlayerVariationDetail ainda não migrado no contrato');
  assert(contractCheck.member_contract_status === 'observacional_ate_migracao_do_contrato', 'limite contratual do membro físico não ficou explícito');
  assert(contractCheck.identity_or_apply_destination_declared === false && contractCheck.database_write === false, 'radar ganhou identidade/destino de aplicação indevido');
  assert(typeof globalThis.CLUBEF_CORE.extractLaunchRadarFromCpk === 'function', 'runtime ativo não expôs o radar de lançamentos');

  const previousObservation = await observation(fixture.previous, 'anterior');
  const previous = await radar.buildRadar(previousObservation, null, {
    cards: cards(fixture.previous),
    generated_at: fixture.previous_generated_at
  });
  assert(previous.boxes.every((box) => box.estado === 'sem_historico'), 'primeira fotografia não ficou como sem histórico');

  const currentObservation = await observation(fixture.current, 'atual');
  const current = await radar.buildRadar(currentObservation, previous, {
    cards: cards(fixture.current),
    previous_artifact: 'fixture://anterior/radar-lancamentos.json',
    generated_at: fixture.current_generated_at
  });
  radar.validateRadarStructure(current);
  assert(current.database_write === false && current.read_only === true, 'radar não permaneceu somente leitura');
  assert(current.publication_decision.evaluated === false && current.publication_decision.blocked === false, 'radar decidiu publicação indevidamente');
  assert(current.apply_scope.radar_fields_included === false && current.apply_scope.destination === null, 'box observacional entrou no apply');
  assert(current.integration_contract.status === 'prepared_not_enabled' && current.integration_contract.database_migration_required === true, 'envelope não ficou preparado para integração futura');
  assert(current.integration_contract.write_enabled === false && current.integration_contract.current_destination === null, 'integração futura foi ligada sem migração');
  assert(current.comparison.status === 'comparado', 'fixture anterior não foi reconhecido como comparável');
  assert(current.counts.boxes === 2 && current.counts.cards_mapped === 5, 'contagens do radar divergiram');
  assert(current.counts.boxes_ausentes_desde_anterior === 1, 'box ausente desde a rodada anterior não foi contada');
  assert(current.comparison.boxes_ausentes_desde_anterior[0].nome_box === 'Box Fixture Ausente', 'proveniência da box ausente não foi preservada');
  assert(current.comparison.boxes_ausentes_desde_anterior[0].database_write === false, 'box ausente acionou exclusão indevida');
  assert(current.counts.by_state.nova === 1 && current.counts.by_state.ja_conhecida === 1 && current.counts.by_state.sem_historico === 0, 'estados comparados divergiram');
  const known = current.boxes.find((box) => box.nome_box === 'Box Fixture Conhecida');
  const fresh = current.boxes.find((box) => box.nome_box === 'Box Fixture Nova');
  assert(known && known.estado === 'ja_conhecida' && known.conteudo_alterado === true, 'box conhecida alterada não foi classificada');
  assert(known.cards_adicionados_desde_anterior.length === 1 && known.cards_adicionados_desde_anterior[0] === '100000000000004', 'card adicionado à box conhecida não foi apontado');
  assert(fresh && fresh.estado === 'nova' && /^[0-9a-f]{64}$/.test(fresh.fingerprint_box), 'box nova ou fingerprint não foram produzidos');
  assert(current.boxes.every((box) => box.cartas.every((card) => Number.isInteger(card.record_index) && Number.isInteger(card.byte_offset))), 'proveniência por registro não foi preservada');

  expectParserFailure(new Uint8Array(radar.RECORD_SIZE + 1), 'não formam registros');
  expectParserFailure(encodeRecords([
    { card_id: '123', box: 'Duplicada' },
    { card_id: '123', box: 'Duplicada' }
  ]), 'card_id duplicado');
  expectParserFailure(encodeRecords([{ card_id: '123', box: '' }]), 'estão incompletos');
  const invalidUtf8 = encodeRecords([{ card_id: '123', box: 'A' }]);
  invalidUtf8[radar.NAME_OFFSET] = 0xff;
  invalidUtf8[radar.NAME_OFFSET + 1] = 0;
  expectParserFailure(invalidUtf8, 'UTF-8 válido');
  const unterminated = encodeRecords([{ card_id: '123', box: 'A' }]);
  unterminated.fill(0x41, radar.NAME_OFFSET, radar.RECORD_SIZE);
  expectParserFailure(unterminated, 'sem terminador NUL');

  let orphanFailure = null;
  try {
    await radar.buildRadar(currentObservation, previous, { cards: cards(fixture.current).slice(1) });
  } catch (error) { orphanFailure = String(error.message || error); }
  assert(orphanFailure && orphanFailure.includes('ausente em Player.bin'), 'junção card/box órfã não falhou fechada');

  const incompatible = JSON.parse(JSON.stringify(previous));
  incompatible.parser.version = 'outro-layout';
  const withoutComparableHistory = await radar.buildRadar(currentObservation, incompatible, { cards: cards(fixture.current) });
  assert(withoutComparableHistory.comparison.status === 'sem_historico_comparavel', 'histórico incompatível foi comparado indevidamente');
  assert(withoutComparableHistory.boxes.every((box) => box.estado === 'sem_historico'), 'histórico incompatível contaminou os estados');

  const outputDirectory = path.join(root, 'artefatos', 'investigacao-boxes', 'fixture-radar');
  fs.mkdirSync(outputDirectory, { recursive: true });
  const outputPath = path.join(outputDirectory, 'radar-lancamentos.json');
  fs.writeFileSync(outputPath, `${JSON.stringify(current, null, 2)}\n`, 'utf8');
  process.stdout.write(`${JSON.stringify({ passed: true, database_write: false, output: outputPath, counts: current.counts })}\n`);
})().catch((error) => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});
