#!/usr/bin/env node
'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

function fail(message) {
  throw new Error(message);
}

function sha256File(filePath) {
  return crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function rowsFor(request, table) {
  const catalog = (request.catalogos || []).find((item) => item && item.table === table);
  if (!catalog || !Array.isArray(catalog.rows)) fail(`catálogo ausente no pedido: ${table}`);
  return catalog.rows;
}

function currentDetail(record) {
  const details = record && record.source_details && record.source_details.dt870_updated;
  return Array.isArray(details) && details.length ? details[0] : null;
}

function categoryFromRawHex(rawHex) {
  if (typeof rawHex !== 'string' || rawHex.length !== 80) fail('registro PlayerBooster inválido');
  const raw = Buffer.from(rawHex, 'hex');
  const byte17 = raw[17];
  return {
    byte17,
    reservedBit136: byte17 & 1,
    categoryBit137W5: (byte17 >>> 1) & 0x1f,
    upperBits142W2: (byte17 >>> 6) & 0x03,
  };
}

function declaredSequentialTextKey(category) {
  if (category >= 1 && category <= 11) {
    return { section: 'Any2W', textId: 841 + category, evidenceRange: 'categoria 1..11 -> Any2W:842..852' };
  }
  if (category >= 13 && category <= 18) {
    return { section: 'Any3W', textId: 49 + category, evidenceRange: 'categoria 13..18 -> Any3W:62..67' };
  }
  if (category >= 19 && category <= 30) {
    return { section: 'Any3W', textId: 596 + category, evidenceRange: 'categoria 19..30 -> Any3W:615..626' };
  }
  return null;
}

function main() {
  const runDir = path.resolve(process.argv[2] || '');
  const outputPath = path.resolve(process.argv[3] || path.join(__dirname, 'prova-categoria-texto-impeto.json'));
  const metadataPath = path.join(runDir, 'metadados-fisicos.json');
  const requestPath = path.join(runDir, 'pedido-leitura.json');
  if (!fs.existsSync(metadataPath) || !fs.existsSync(requestPath)) {
    fail('informe um run-dir que contenha metadados-fisicos.json e pedido-leitura.json');
  }

  const metadata = readJson(metadataPath);
  const request = readJson(requestPath);
  const impulses = rowsFor(request, 'impeto_jogo');
  const texts = rowsFor(request, 'texto_do_jogo');
  const impulseByCode = new Map(impulses.map((row) => [Number(row.codigo_jogo), row]));
  const textByKey = new Map(texts.map((row) => [`${row.secao}:${row.id_texto}`, row]));
  const physicalRecords = metadata.catalogs && metadata.catalogs.impetos && metadata.catalogs.impetos.records;
  if (!Array.isArray(physicalRecords)) fail('metadados físicos não contêm catálogo de Ímpetos');

  const groups = new Map();
  const mappedRecords = [];
  const unresolvedRecords = [];
  let currentRecords = 0;
  let reservedBitViolations = 0;
  let upperBitViolations = 0;

  for (const record of physicalRecords) {
    const detail = currentDetail(record);
    if (!detail) continue;
    currentRecords += 1;
    const code = Number(record.id);
    const physical = categoryFromRawHex(detail.raw_hex);
    if (physical.reservedBit136 !== 0) reservedBitViolations += 1;
    if (physical.upperBits142W2 !== 0) upperBitViolations += 1;
    const group = groups.get(physical.categoryBit137W5) || [];
    group.push(code);
    groups.set(physical.categoryBit137W5, group);

    const target = declaredSequentialTextKey(physical.categoryBit137W5);
    const base = {
      codigo_jogo: code,
      categoria_raw_bit137_w5: physical.categoryBit137W5,
      byte17: physical.byte17,
      arquivo: 'PlayerBooster.bin',
      fonte: 'dt870_updated',
      registro: Number(detail.record_index),
      registro_sha256: detail.record_sha256,
      arquivo_sha256: detail.source_file_sha256,
      rotulo_historico_apenas_diagnostico: impulseByCode.get(code)?.nome_pt || null,
    };
    if (!target) {
      unresolvedRecords.push({
        ...base,
        motivo: physical.categoryBit137W5 === 0
          ? 'categoria 0 reúne rótulos distintos; não existe ponte uniforme comprovada'
          : 'categoria 12 tem somente correspondência nominal isolada com Any2W:928; insuficiente como prova estrutural',
      });
      continue;
    }
    const key = `${target.section}:${target.textId}`;
    const text = textByKey.get(key);
    if (!text) fail(`texto físico ausente: ${key}`);
    mappedRecords.push({
      ...base,
      secao_texto: target.section,
      id_texto: target.textId,
      texto_fisico: text.texto,
      regra_candidata: target.evidenceRange,
      texto_proveniencia: {
        arquivo: text.arquivo,
        cpk: text.cpk,
        secao_idx: text.secao_idx,
        entrada_idx: text.entrada_idx,
        entrada_offset: text.entrada_offset,
        texto_offset: text.texto_offset,
        fonte_cpk_sha256: text.fonte_cpk_sha256,
        fonte_arquivo_sha256: text.fonte_arquivo_sha256,
      },
    });
  }

  const groupSummary = [...groups.entries()]
    .sort((left, right) => left[0] - right[0])
    .map(([category, codes]) => ({
      categoria_raw_bit137_w5: category,
      total_codigos: codes.length,
      codigos: [...codes].sort((left, right) => left - right),
      chave_texto_candidata: declaredSequentialTextKey(category),
    }));

  const code79 = mappedRecords.find((record) => record.codigo_jogo === 79) || null;
  const variants = [38, 49].map((code) => {
    const record = physicalRecords.find((item) => Number(item.id) === code);
    const detail = currentDetail(record);
    return {
      codigo_jogo: code,
      categoria_raw_bit137_w5: detail ? categoryFromRawHex(detail.raw_hex).categoryBit137W5 : null,
      efeitos: (record?.efeitos || []).map((effect) => ({
        codigo_atributo: effect.codigo_atributo,
        delta: effect.delta,
        bit_delta: effect.bit_delta,
      })),
    };
  });

  const result = {
    schema: 'clubef-prova-categoria-texto-impeto-v1',
    generated_at: new Date().toISOString(),
    read_only: true,
    database_write: false,
    game_write: false,
    source: {
      run_dir: runDir,
      metadata_file: metadataPath,
      metadata_sha256: sha256File(metadataPath),
      request_file: requestPath,
      request_sha256: sha256File(requestPath),
    },
    physical_field: {
      arquivo: 'PlayerBooster.bin',
      registro_bytes: 40,
      categoria: { bit_inicio: 137, largura_bits: 5 },
      comprovacao_layout: {
        registros_atualizados: currentRecords,
        bit_136_nao_zero: reservedBitViolations,
        bits_142_143_nao_zero: upperBitViolations,
      },
    },
    coverage: {
      registros_atualizados: currentRecords,
      registros_com_chave_sequencial_candidata: mappedRecords.length,
      registros_sem_ponte_estrutural_suficiente: unresolvedRecords.length,
      categorias_fisicas: groupSummary.length,
      status: 'evidencia_estrutural_forte_sem_referencia_binaria_direta',
      limite: 'as três sequências são determinísticas e cobrem grupos inteiros, mas nenhum arquivo legível contém o ponteiro categoria -> seção/id; promover como contrato exige decisão explícita de convenção rastreável',
    },
    anchor_code_79: code79,
    variant_guard_38_49: variants,
    groups: groupSummary,
    mapped_records: mappedRecords,
    unresolved_records: unresolvedRecords,
  };

  fs.writeFileSync(outputPath, JSON.stringify(result, null, 2) + '\n', 'utf8');
  process.stdout.write(JSON.stringify({
    output: outputPath,
    coverage: result.coverage,
    code_79: code79 && {
      categoria: code79.categoria_raw_bit137_w5,
      secao_texto: code79.secao_texto,
      id_texto: code79.id_texto,
      texto: code79.texto_fisico,
      registro_sha256: code79.registro_sha256,
    },
    variants_38_49: variants,
  }, null, 2) + '\n');
}

main();
