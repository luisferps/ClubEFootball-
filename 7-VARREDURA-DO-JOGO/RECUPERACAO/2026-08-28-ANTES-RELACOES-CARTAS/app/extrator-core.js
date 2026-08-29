'use strict';

/**
 * Núcleo novo do Extrator eFootball.
 * Somente funções puras de leitura, decodificação, comparação e manifestação.
 * Não contém persistência, credencial, cliente Supabase ou efeito automático.
 */
(function installCore(global) {
  const { K, IMP, OVRW, STYLE_CAT, DEF_CAT } = global.CLUBEF_PHYSICAL_MAP;
  const CATALOG_SOURCE_MAP = global.CLUBEF_CATALOG_SOURCE_MAP || {};
  const TD = new TextDecoder('utf-8');
  const CARD_COLUMNS = Object.freeze([
    'card_id', 'tipo', 'overall', 'roda_motor', 'nome', 'posicao',
    'slot_ofensivo_id', 'slot_ofensivo_confirmado', 'slot_defensivo_id',
    'slot_defensivo_confirmado', 'pe', 'altura', 'peso', 'idade',
    'nacionalidade', 'pe_ruim_uso', 'pe_ruim_precisao', 'resistencia_lesao',
    'forma', 'impeto_s1', 'impeto_s2_cond', 'vaga_s1', 'vaga_s2', 'box',
    'atributos', 'habilidades', 'aptidoes', 'estilos_ia', 'corpo'
  ]);
  const STRUCTURED_COLUMNS = new Set(['atributos', 'habilidades', 'aptidoes', 'estilos_ia', 'corpo']);
  const CONTRACT_VERSION = 'clubef-extrator-v4';

  function u32(bytes, offset) {
    return (bytes[offset] | (bytes[offset + 1] << 8) | (bytes[offset + 2] << 16) | (bytes[offset + 3] << 24)) >>> 0;
  }
  function u64String(bytes, offset) {
    return (BigInt(u32(bytes, offset)) | (BigInt(u32(bytes, offset + 4)) << 32n)).toString();
  }
  function u32be(bytes, offset) {
    return ((bytes[offset] << 24) | (bytes[offset + 1] << 16) | (bytes[offset + 2] << 8) | bytes[offset + 3]) >>> 0;
  }
  function u16be(bytes, offset) {
    return ((bytes[offset] << 8) | bytes[offset + 1]) >>> 0;
  }
  function readBits(bytes, base, bit, width) {
    let value = 0;
    for (let index = 0; index < width; index += 1) {
      const absolute = bit + index;
      value |= ((bytes[base + (absolute >> 3)] >> (absolute & 7)) & 1) << index;
    }
    return value >>> 0;
  }
  async function inflate(bytes) {
    const stream = new DecompressionStream('deflate');
    const response = new Response(new Blob([bytes]).stream().pipeThrough(stream));
    return new Uint8Array(await response.arrayBuffer());
  }

  function utfDeobfuscate(data) {
    if (data[0] === 0x40 && data[1] === 0x55 && data[2] === 0x54 && data[3] === 0x46) return data;
    const output = Uint8Array.from(data);
    let mask = 0x655f >>> 0;
    for (let index = 0; index < output.length; index += 1) {
      output[index] ^= mask & 0xff;
      mask = Math.imul(mask, 0x4115) >>> 0;
    }
    return output;
  }
  function parseUtfTable(data) {
    const decoded = utfDeobfuscate(data);
    const size = u32be(decoded, 4);
    const block = decoded.subarray(8, 8 + size);
    const rowsOffset = u32be(block, 0);
    const stringsOffset = u32be(block, 4);
    const dataOffset = u32be(block, 8);
    const columnCount = u16be(block, 16);
    const rowLength = u16be(block, 18);
    const rowCount = u32be(block, 20);
    const strings = block.subarray(stringsOffset, dataOffset);
    const readString = (offset) => {
      let end = offset;
      while (end < strings.length && strings[end] !== 0) end += 1;
      return TD.decode(strings.subarray(offset, end));
    };
    const readValue = (type, bytes, offset) => {
      switch (type) {
        case 0: case 1: return [bytes[offset], 1];
        case 2: case 3: return [u16be(bytes, offset), 2];
        case 4: case 5: return [u32be(bytes, offset), 4];
        case 6: case 7: return [u32be(bytes, offset) * 4294967296 + u32be(bytes, offset + 4), 8];
        case 8: return [0, 4];
        case 0xA: return [readString(u32be(bytes, offset)), 4];
        case 0xB: return [[u32be(bytes, offset), u32be(bytes, offset + 4)], 8];
        default: throw new Error(`tipo @UTF não suportado: ${type}`);
      }
    };
    let pointer = 24;
    const columns = [];
    for (let index = 0; index < columnCount; index += 1) {
      const flag = block[pointer]; pointer += 1;
      const nameOffset = u32be(block, pointer); pointer += 4;
      const storage = flag & 0xf0;
      const type = flag & 0x0f;
      let constant = null;
      if (storage === 0x30) {
        const [value, consumed] = readValue(type, block, pointer);
        constant = value; pointer += consumed;
      }
      columns.push({ name: readString(nameOffset), storage, type, constant });
    }
    const rows = [];
    for (let rowIndex = 0; rowIndex < rowCount; rowIndex += 1) {
      let offset = rowsOffset + rowIndex * rowLength;
      const row = {};
      for (const column of columns) {
        if (column.storage === 0x30) { row[column.name] = column.constant; continue; }
        if (column.storage === 0x10) { row[column.name] = 0; continue; }
        const [value, consumed] = readValue(column.type, block, offset);
        row[column.name] = value; offset += consumed;
      }
      rows.push(row);
    }
    return rows;
  }
  function decompressCriLayla(source) {
    if (!(source[0] === 0x43 && source[1] === 0x52 && source[2] === 0x49)) return source;
    const uncompressedSize = u32(source, 8);
    const headerOffset = u32(source, 12);
    const output = new Uint8Array(uncompressedSize);
    const header = source.subarray(16 + headerOffset, 16 + headerOffset + 0x100);
    const data = source.subarray(16, 16 + headerOffset);
    let position = data.length * 8 - 1;
    const getBits = (count) => {
      let value = 0;
      for (let index = 0; index < count; index += 1) {
        const byteIndex = position >> 3;
        const bitIndex = position & 7;
        value = (value << 1) | ((data[byteIndex] >> (7 - bitIndex)) & 1);
        position -= 1;
      }
      return value;
    };
    let write = uncompressedSize - 1;
    while (write >= 0) {
      if (getBits(1)) {
        let reference = write + getBits(13) + 3;
        let length = 3;
        let done = false;
        for (const width of [2, 3, 5]) {
          const count = getBits(width); length += count;
          if (count !== (1 << width) - 1) { done = true; break; }
        }
        if (!done) {
          let count = getBits(8); length += count;
          while (count === 255) { count = getBits(8); length += count; }
        }
        for (let index = 0; index < length; index += 1) {
          output[write] = output[reference]; write -= 1; reference -= 1;
        }
      } else {
        output[write] = getBits(8); write -= 1;
      }
    }
    const result = new Uint8Array(header.length + output.length);
    result.set(header, 0); result.set(output, header.length);
    return result;
  }
  function extractCpk(data) {
    if (!(data[0] === 0x43 && data[1] === 0x50 && data[2] === 0x4b)) throw new Error('arquivo não é um CPK');
    const header = parseUtfTable(data.subarray(16))[0];
    const tocOffset = header.TocOffset;
    const contentOffset = header.ContentOffset;
    const files = {};
    if (tocOffset) {
      for (const row of parseUtfTable(data.subarray(tocOffset + 16))) {
        const base = contentOffset && contentOffset <= tocOffset ? contentOffset : tocOffset;
        const absolute = base + row.FileOffset;
        let chunk = data.subarray(absolute, absolute + row.FileSize);
        if (chunk[0] === 0x43 && chunk[1] === 0x52 && chunk[2] === 0x49) chunk = decompressCriLayla(chunk);
        files[row.FileName] = chunk;
      }
    }
    return files;
  }

  const WESYS_KEYS = { 1: [378445824, 774547186, 214490323], 2: [0xED5B2960, 1246903118, 0xF3A31BAD] };
  async function unpackWesys(data) {
    const nibble = data[1] & 15;
    const compressedSize = u32(data, 8);
    const originalSize = u32(data, 12);
    const buffer = Uint8Array.from(data.subarray(16, 16 + compressedSize));
    const initial = WESYS_KEYS[nibble] || [0, 0, 0];
    let x = initial[0] >>> 0, y = initial[1] >>> 0, z = initial[2] >>> 0;
    let w = (((originalSize << 16) >>> 0) | compressedSize) >>> 0;
    const aligned = (compressedSize >> 2) * 4;
    for (let offset = 0; offset < aligned; offset += 4) {
      const t = (x ^ ((x << 11) >>> 0)) >>> 0;
      const previous = w; x = y; y = z; z = w;
      w = (previous ^ (((previous >>> 11) ^ t) >>> 8) ^ t) >>> 0;
      const value = (u32(buffer, offset) ^ w) >>> 0;
      buffer[offset] = value & 0xff;
      buffer[offset + 1] = (value >>> 8) & 0xff;
      buffer[offset + 2] = (value >>> 16) & 0xff;
      buffer[offset + 3] = (value >>> 24) & 0xff;
    }
    return inflate(buffer);
  }

  const TEXT_SECTION_RELOCATION = Object.freeze({
    Amg1T: 'Amg1W', Any1T: 'Any1W', Any2T: 'Any2W', Any3T: 'Any3W',
    E13W: 'E15W', E5T: 'E5W', E6T: 'E6W', Lcm2W: 'Lcm4W',
    T2T: 'T2W', PlayC: 'Po1C'
  });
  function fixedUtf8(data, start, length) {
    let end = Math.min(data.length, start + length);
    while (end > start && data[end - 1] === 0) end -= 1;
    return TD.decode(data.subarray(start, end));
  }
  function fixedNullUtf8(data, start, length) {
    let end = start;
    const limit = Math.min(data.length, start + length);
    while (end < limit && data[end] !== 0) end += 1;
    return TD.decode(data.subarray(start, end));
  }
  function parseAllStr(data) {
    const sectionCount = u32(data, 0);
    const headerStart = u32(data, 4);
    if (sectionCount < 1 || sectionCount > 4096) throw new Error(`all.str declara uma quantidade de seções inválida: ${sectionCount}.`);
    if (headerStart < 8 || headerStart + sectionCount * 12 > data.length) throw new Error('A tabela de seções do all.str aponta para fora do arquivo.');
    const sections = [], records = [], seen = new Set(), duplicateIds = [];
    for (let physicalIndex = 0; physicalIndex < sectionCount; physicalIndex += 1) {
      const headerOffset = headerStart + physicalIndex * 12;
      const sectionOffset = u32(data, headerOffset);
      const sectionSize = u32(data, headerOffset + 4);
      const nameOffset = u32(data, headerOffset + 8);
      if (nameOffset >= data.length || sectionOffset + sectionSize > data.length) throw new Error(`A seção física ${physicalIndex} do all.str é inválida.`);
      let nameEnd = nameOffset;
      while (nameEnd < data.length && data[nameEnd] !== 0) nameEnd += 1;
      const secao = TD.decode(data.subarray(nameOffset, nameEnd));
      const count = sectionSize >= 8 ? u32(data, sectionOffset) : 0;
      if (count > 100000 || sectionOffset + 8 + count * 12 > sectionOffset + sectionSize) throw new Error(`A tabela de entradas da seção ${secao || physicalIndex} é inválida.`);
      sections.push({ secao, secao_idx: physicalIndex, nome_offset: nameOffset, secao_offset: sectionOffset, secao_tamanho: sectionSize, entradas: count });
      for (let entryIndex = 0; entryIndex < count; entryIndex += 1) {
        const entryOffset = sectionOffset + 8 + entryIndex * 12;
        const idTexto = u32(data, entryOffset);
        const storedLength = data[entryOffset + 4] | (data[entryOffset + 5] << 8);
        const visibleLength = data[entryOffset + 6] | (data[entryOffset + 7] << 8);
        const relativeOffset = u32(data, entryOffset + 8);
        const textOffset = sectionOffset + relativeOffset;
        if (relativeOffset + storedLength > sectionSize || textOffset + storedLength > data.length) throw new Error(`O texto ${secao}:${idTexto} aponta para fora da seção.`);
        const id = `${secao}:${idTexto}`;
        if (seen.has(id)) duplicateIds.push(id);
        seen.add(id);
        records.push({
          id,
          secao,
          secao_idx: physicalIndex,
          id_texto: idTexto,
          texto: fixedUtf8(data, textOffset, storedLength),
          idioma: 'pt-BR',
          origem: 'jogo_fisico',
          arquivo: 'all.str',
          cpk: 'dt261_bra_console_win.cpk',
          secao_offset: sectionOffset,
          entrada_idx: entryIndex,
          entrada_offset: entryOffset,
          texto_offset: textOffset,
          tamanho_armazenado: storedLength,
          tamanho_visivel: visibleLength,
          presente_na_fonte: true
        });
      }
    }
    if (duplicateIds.length) throw new Error(`O all.str contém ${duplicateIds.length} chave(s) oficial(is) duplicada(s).`);
    return { section_count: sectionCount, sections, records, duplicate_ids: duplicateIds };
  }
  async function extractTextCatalogFromCpk(bytes) {
    const cpk = extractCpk(bytes);
    if (!cpk['all.str']) throw new Error('all.str não foi encontrado no CPK de textos em português.');
    const raw = await unpackWesys(cpk['all.str']);
    const parsed = parseAllStr(raw);
    const sourceFingerprint = await sha256(raw);
    const cpkFingerprint = await sha256(bytes);
    const records = parsed.records.map((record) => ({
      ...record,
      fonte_cpk_sha256: cpkFingerprint,
      fonte_arquivo_sha256: sourceFingerprint,
      fingerprint: stableJson({
        secao: record.secao, secao_idx: record.secao_idx, id_texto: record.id_texto,
        texto: record.texto, idioma: record.idioma, origem: record.origem,
        arquivo: record.arquivo, cpk: record.cpk, secao_offset: record.secao_offset,
        entrada_idx: record.entrada_idx, entrada_offset: record.entrada_offset,
        texto_offset: record.texto_offset, tamanho_armazenado: record.tamanho_armazenado,
        tamanho_visivel: record.tamanho_visivel, presente_na_fonte: true,
        fonte_cpk_sha256: cpkFingerprint, fonte_arquivo_sha256: sourceFingerprint
      })
    }));
    return {
      supported: true,
      status: 'comparavel',
      file: 'all.str',
      source_policy: 'somente dt261_bra; chave oficial composta por secao + id_texto',
      source_fingerprint: sourceFingerprint,
      source_cpk_fingerprint: cpkFingerprint,
      section_count: parsed.section_count,
      records,
      duplicate_ids: parsed.duplicate_ids,
      empty_texts: records.filter((record) => record.texto === '').length
    };
  }
  function validateTextCatalogStructure(currentCatalog) {
    if (!currentCatalog || currentCatalog.supported !== true) throw new Error('A fonte física de textos não está validada.');
    const sectionCount = Number(currentCatalog.section_count);
    const records = currentCatalog.records;
    if (!Number.isInteger(sectionCount) || sectionCount < 1 || sectionCount > 4096) throw new Error('A quantidade de seções do all.str é inválida.');
    if (!Array.isArray(records) || records.length < 1) throw new Error('O all.str não contém nenhuma chave oficial de texto.');
    if ((currentCatalog.duplicate_ids || []).length) throw new Error('O all.str contém chaves oficiais duplicadas.');
    const keys = new Set(), cpkHashes = new Set(), fileHashes = new Set();
    const hashPattern = /^[0-9a-f]{64}$/i;
    for (const record of records) {
      if (!record || typeof record.secao !== 'string' || !record.secao || !Number.isInteger(record.id_texto) || record.id_texto < 0) throw new Error('O all.str contém uma chave oficial incompleta ou inválida.');
      const key = `${record.secao}:${record.id_texto}`;
      if (record.id !== key || keys.has(key)) throw new Error(`O all.str repete ou identifica incorretamente a chave ${key}.`);
      keys.add(key);
      if (typeof record.texto !== 'string' || record.idioma !== 'pt-BR' || record.origem !== 'jogo_fisico' || record.arquivo !== 'all.str' || record.cpk !== 'dt261_bra_console_win.cpk' || record.presente_na_fonte !== true) throw new Error(`A procedência física de ${key} é inválida.`);
      for (const field of ['secao_idx', 'secao_offset', 'entrada_idx', 'entrada_offset', 'texto_offset', 'tamanho_armazenado', 'tamanho_visivel']) {
        if (!Number.isInteger(record[field]) || record[field] < 0) throw new Error(`O endereço físico ${field} de ${key} é inválido.`);
      }
      if (!hashPattern.test(String(record.fonte_cpk_sha256 || '')) || !hashPattern.test(String(record.fonte_arquivo_sha256 || ''))) throw new Error(`O fingerprint físico de ${key} é inválido.`);
      cpkHashes.add(record.fonte_cpk_sha256.toLowerCase());
      fileHashes.add(record.fonte_arquivo_sha256.toLowerCase());
    }
    if (cpkHashes.size !== 1 || fileHashes.size !== 1) throw new Error('O catálogo mistura mais de uma versão física de all.str.');
    if (String(currentCatalog.source_cpk_fingerprint || '').toLowerCase() !== [...cpkHashes][0] || String(currentCatalog.source_fingerprint || '').toLowerCase() !== [...fileHashes][0]) throw new Error('O manifesto da fonte não corresponde aos fingerprints das entradas de all.str.');
    return { sections: sectionCount, official_keys: keys.size, duplicate_official_keys: 0, source_cpk_sha256: [...cpkHashes][0], source_file_sha256: [...fileHashes][0] };
  }
  function compareTextCatalog(currentCatalog, baselineRows) {
    const structuralValidation = validateTextCatalogStructure(currentCatalog);
    const current = new Map(), baseline = new Map();
    for (const record of currentCatalog.records || []) {
      if (current.has(record.id)) throw new Error(`A fonte física repete a chave ${record.id}.`);
      current.set(record.id, record);
    }
    for (const row of baselineRows || []) {
      const id = `${row.secao}:${row.id_texto}`;
      if (baseline.has(id)) throw new Error(`A base atual repete a chave ${id}.`);
      baseline.set(id, row);
    }
    const consumed = new Set(), changedEntries = [], blocked = [];
    const comparableFields = [
      'secao_idx', 'texto', 'idioma', 'origem', 'arquivo', 'cpk', 'secao_offset',
      'entrada_idx', 'entrada_offset', 'texto_offset', 'tamanho_armazenado',
      'tamanho_visivel', 'fonte_cpk_sha256', 'fonte_arquivo_sha256', 'presente_na_fonte'
    ];
    for (const [beforeId, before] of baseline) {
      const relocatedSection = TEXT_SECTION_RELOCATION[before.secao] || before.secao;
      const relocatedId = `${relocatedSection}:${before.id_texto}`;
      const afterId = current.has(beforeId) ? beforeId : relocatedId;
      const after = current.get(afterId);
      if (!after) {
        blocked.push({ id: beforeId, reason: `a chave oficial de destino ${afterId} não existe no all.str atual`, before });
        continue;
      }
      consumed.add(afterId);
      const keyChanged = beforeId !== afterId;
      const fields = comparableFields.filter((field) => {
        const oldValue = before[field] == null ? null : before[field];
        const newValue = after[field] == null ? null : after[field];
        return stableJson(oldValue) !== stableJson(newValue);
      }).map((field) => ({ field, before: before[field] == null ? null : before[field], after: after[field] == null ? null : after[field] }));
      if (keyChanged || fields.length) {
        const operation = keyChanged ? (before.texto === after.texto ? 'relocate' : 'relocate_and_replace_content') : 'update';
        changedEntries.push({ id: afterId, before_id: beforeId, before, after, record: after, fields, operation });
      }
    }
    if (blocked.length) throw new Error(`Comparação de textos bloqueada: ${blocked.length} chave(s) não possui(em) destino oficial.`);
    const newEntries = [...current].filter(([id]) => !consumed.has(id)).map(([, record]) => record);
    return {
      status: 'comparado',
      current: current.size,
      baseline_active: baseline.size,
      new_entries: newEntries,
      changed_entries: changedEntries,
      absent_entries: [],
      without_previous_fingerprint: 0,
      duplicate_ids: [],
      unchanged: baseline.size - changedEntries.length,
      validation: { ...structuralValidation, empty_texts: currentCatalog.empty_texts, delete_without_replacement: 0 }
    };
  }

  function decodePrimaryStyle(raw) {
    const id = raw - (raw % 4);
    const known = STYLE_CAT[String(id)];
    return known ? { name: known.nome, position: known.pos || null, id, unknown: false } : { name: 'Novo (2027)', position: null, id, unknown: true };
  }
  function decodeDefensiveStyle(id) {
    if (id === 0) return { name: 'Básico', id: 0, confirmed: true };
    const known = DEF_CAT[String(id)];
    return known ? { name: known.n, id, confirmed: known.c } : { name: `Defensivo #${id}`, id, confirmed: false };
  }
  function decodeBoosterSlot(value) {
    if (value === 0) return { state: 'sem' };
    if (value === 136) return { state: 'vaga' };
    const known = IMP[String(value)];
    return { state: 'preench', id: value, name: known ? known.n : null, known: Boolean(known) };
  }
  function calculateOverall(attributes, position) {
    const weights = OVRW.weights[position];
    if (!weights) return null;
    let score = weights.b;
    for (let index = 0; index < OVRW.names.length; index += 1) {
      const value = attributes[OVRW.names[index]];
      if (value == null) return null;
      score += value * weights.w[index];
    }
    return Math.round(score);
  }
  const BODY_FIELDS = [
    ['coxa', 12, 0, 4], ['panturrilha', 12, 4, 4], ['cintura', 8, 20, 4],
    ['peito', 8, 16, 4], ['tamBraco', 8, 24, 4], ['tamPescoco', 8, 4, 4],
    ['comprPerna', 12, 8, 4], ['comprBraco', 8, 28, 4], ['comprPescoco', 8, 0, 4],
    ['largOmbro', 8, 12, 4], ['altOmbro', 8, 8, 4]
  ];
  function decodeBody(bytes, base) {
    return BODY_FIELDS.map(([, byte, bit, width]) => readBits(bytes, base + byte, bit, width));
  }
  function decodeCard(bytes, base) {
    const card = {};
    card.card_id = (BigInt(readBits(bytes, base, 64, 32)) | (BigInt(readBits(bytes, base, 96, 32)) << 32n)).toString();
    card.attrs = {};
    for (const name of Object.keys(K.ABILITIES)) card.attrs[name] = 40 + readBits(bytes, base, K.ABILITIES[name], K.ABIL_WIDTH);
    const height = K.PROTECT['身高 Height(cm)'];
    const weight = K.PROTECT['体重 Weight(kg)'];
    const age = K.PROTECT['年龄 Age'];
    card.height = readBits(bytes, base, height[0], height[1]) + height[2];
    card.weight = readBits(bytes, base, weight[0], weight[1]) + weight[2];
    card.age = readBits(bytes, base, age[0], age[1]) + age[2];
    card.position = K.POSITION_NAMES[readBits(bytes, base, K.POSITION_BIT, K.POSITION_WIDTH)];
    const primary = decodePrimaryStyle(readBits(bytes, base, K.PLAYING_STYLE_BIT, K.PLAYING_STYLE_WIDTH));
    card.primary_style_id = primary.id;
    card.primary_style_unknown = primary.unknown;
    const defensive = decodeDefensiveStyle(readBits(bytes, base, K.SECONDARY_STYLE_BIT, K.SECONDARY_STYLE_WIDTH));
    card.defensive_style_id = defensive.id;
    card.defensive_style_confirmed = defensive.confirmed;
    card.weak_foot_usage = K.WFU_NAMES[readBits(bytes, base, K.WFU_BIT, K.WFU_WIDTH)];
    card.weak_foot_accuracy = K.WFA_NAMES[readBits(bytes, base, K.WFA_BIT, K.WFA_WIDTH)];
    card.foot = readBits(bytes, base, K.FOOT_BIT, 1) ? 'Esquerdo' : 'Direito';
    card.form = K.FORM_NAMES[readBits(bytes, base, K.FORM_BIT, K.FORM_WIDTH)];
    card.injury = readBits(bytes, base, K.INJURY_HIGH_BIT, 1) ? 'Alta' : (readBits(bytes, base, K.INJURY_MED_BIT, 1) ? 'Média' : 'Baixa');
    card.nationality = K.NATIONALITY_ID[readBits(bytes, base, K.NATIONALITY_BIT, K.NATIONALITY_WIDTH)];
    card.ai_styles = Object.keys(K.AI_PLAYING_STYLES).filter((name) => readBits(bytes, base, K.AI_PLAYING_STYLES[name], 1));
    card.skills = Object.keys(K.SKILL_BITS).filter((name) => readBits(bytes, base, K.SKILL_BITS[name], 1));
    card.aptitudes = {};
    for (const position of Object.keys(K.POSITION_APTITUDE_BITS)) card.aptitudes[position] = readBits(bytes, base, K.POSITION_APTITUDE_BITS[position], K.APTITUDE_WIDTH);
    const nameStart = base + K.NAME_REGION_START + 3 * K.NAME_FIELD_STRIDE;
    let nameEnd = nameStart;
    while (nameEnd < nameStart + K.NAME_FIELD_STRIDE && bytes[nameEnd] !== 0) nameEnd += 1;
    card.name = TD.decode(bytes.slice(nameStart, nameEnd));
    card.booster_primary = decodeBoosterSlot(readBits(bytes, base, 308, 10));
    card.booster_conditional = decodeBoosterSlot(readBits(bytes, base, 288, 10));
    card.overall = calculateOverall(card.attrs, card.position);
    return card;
  }
  function validCard(card) {
    const id = BigInt(card.card_id);
    return id !== 0n && id < (1n << 50n) && card.height >= 145 && card.height <= 210 && card.age >= 14 && card.age <= 47;
  }
  async function extractCardsFromCpk(bytes, log = () => {}) {
    const cpk = extractCpk(bytes);
    if (!cpk['Player.bin']) throw new Error('Player.bin não encontrado no CPK atual.');
    const boxes = {};
    if (cpk['PlayerVariationDetail.bin']) {
      const raw = await unpackWesys(cpk['PlayerVariationDetail.bin']);
      if (raw.length % 168 !== 0) throw new Error('PlayerVariationDetail.bin incompatível com registros de 168 bytes.');
      for (let offset = 0; offset < raw.length; offset += 168) {
        const id = (BigInt(u32(raw, offset)) | (BigInt(u32(raw, offset + 4)) << 32n)).toString();
        let end = offset + 12;
        while (end < offset + 168 && raw[end] !== 0) end += 1;
        const name = TD.decode(raw.slice(offset + 12, end));
        if (id !== '0' && name) boxes[id] = name;
      }
      log(`boxes físicos: ${Object.keys(boxes).length}`);
    }
    const bodies = {};
    if (cpk['PlayerAppearance.bin']) {
      const raw = await unpackWesys(cpk['PlayerAppearance.bin']);
      if (raw.length % 64 !== 0) throw new Error('PlayerAppearance.bin incompatível com registros de 64 bytes.');
      for (let offset = 0; offset < raw.length; offset += 64) {
        const id = (BigInt(u32(raw, offset)) | (BigInt(u32(raw, offset + 4)) << 32n)).toString();
        if (id !== '0') bodies[id] = decodeBody(raw, offset);
      }
      log(`corpos físicos: ${Object.keys(bodies).length}`);
    }
    const rawPlayers = await unpackWesys(cpk['Player.bin']);
    if (rawPlayers.length % K.RECORD_SIZE !== 0) throw new Error(`Player.bin não é múltiplo do registro físico de ${K.RECORD_SIZE} bytes.`);
    const cards = [];
    for (let offset = 0; offset < rawPlayers.length; offset += K.RECORD_SIZE) {
      const card = decodeCard(rawPlayers, offset);
      if (!validCard(card)) continue;
      const values = Object.values(card.attrs);
      const test = values.every((value) => value === 99);
      const base = BigInt(card.card_id) < (1n << 18n);
      card.tipo = test ? 'teste' : (base ? 'base' : 'colecionavel');
      card.roda_motor = !test && !base;
      card.box = boxes[card.card_id] || null;
      card.corpo = bodies[card.card_id] ? [card.height].concat(bodies[card.card_id]) : null;
      cards.push(card);
    }
    log(`cartas válidas: ${cards.length}`);
    return cards;
  }

  function quoteCsv(value) {
    if (value == null) return '';
    const text = String(value);
    return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
  }
  function stableJson(value) {
    if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`;
    if (value && typeof value === 'object') return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableJson(value[key])}`).join(',')}}`;
    return JSON.stringify(value);
  }
  async function sha256(bytesOrText) {
    const bytes = typeof bytesOrText === 'string' ? new TextEncoder().encode(bytesOrText) : bytesOrText;
    const digest = await crypto.subtle.digest('SHA-256', bytes);
    return [...new Uint8Array(digest)].map((value) => value.toString(16).padStart(2, '0')).join('');
  }
  function parseCsv(text) {
    const source = text.replace(/^\uFEFF/, '');
    const matrix = [];
    let row = [], cell = '', quoted = false;
    for (let index = 0; index < source.length; index += 1) {
      const character = source[index];
      if (quoted) {
        if (character === '"' && source[index + 1] === '"') { cell += '"'; index += 1; }
        else if (character === '"') quoted = false;
        else cell += character;
      } else if (character === '"') quoted = true;
      else if (character === ',') { row.push(cell); cell = ''; }
      else if (character === '\n') { row.push(cell); matrix.push(row); row = []; cell = ''; }
      else if (character !== '\r') cell += character;
    }
    if (quoted) throw new Error('CSV inválido: aspas não fechadas.');
    if (cell !== '' || row.length) { row.push(cell); matrix.push(row); }
    if (!matrix.length) throw new Error('CSV vazio.');
    const headers = matrix.shift().map((value, index) => index ? value : value.replace(/^\uFEFF/, ''));
    const rows = matrix.filter((values) => values.some((value) => value !== '')).map((values, index) => {
      if (values.length !== headers.length) throw new Error(`CSV inválido na linha ${index + 2}: ${values.length} campos; esperado ${headers.length}.`);
      return Object.fromEntries(headers.map((header, column) => [header, values[column]]));
    });
    return { headers, rows };
  }
  function validateSchema(headers) {
    const missing = CARD_COLUMNS.filter((column) => !headers.includes(column));
    const extra = headers.filter((column) => !CARD_COLUMNS.includes(column));
    if (missing.length || extra.length) throw new Error(`Schema incompatível. Ausentes: ${missing.join(', ') || 'nenhum'}; extras: ${extra.join(', ') || 'nenhum'}.`);
    return true;
  }
  function cardToRow(card) {
    const weakUsage = { 'Almost Never': 0, Rarely: 1, Occasionally: 2, Regularly: 3 };
    const weakAccuracy = { Low: 0, Medium: 1, High: 2, 'Very High': 3 };
    const form = { Inconsistent: 0, Standard: 1, Unwavering: 2 };
    const row = {
      card_id: card.card_id,
      tipo: card.tipo,
      overall: card.overall == null ? '' : String(card.overall),
      roda_motor: String(Boolean(card.roda_motor)),
      nome: card.name,
      posicao: card.position,
      slot_ofensivo_id: String(card.primary_style_id),
      slot_ofensivo_confirmado: String(card.primary_style_id === 0 || !card.primary_style_unknown),
      slot_defensivo_id: String(card.defensive_style_id),
      slot_defensivo_confirmado: String(Boolean(card.defensive_style_confirmed)),
      pe: card.foot,
      altura: String(card.height),
      peso: String(card.weight),
      idade: String(card.age),
      nacionalidade: card.nationality || '',
      pe_ruim_uso: weakUsage[card.weak_foot_usage] == null ? '' : String(weakUsage[card.weak_foot_usage]),
      pe_ruim_precisao: weakAccuracy[card.weak_foot_accuracy] == null ? '' : String(weakAccuracy[card.weak_foot_accuracy]),
      resistencia_lesao: card.injury,
      forma: form[card.form] == null ? '' : String(form[card.form]),
      impeto_s1: card.booster_primary.state === 'preench' ? String(card.booster_primary.id) : '',
      impeto_s2_cond: card.booster_conditional.state === 'preench' ? String(card.booster_conditional.id) : '',
      vaga_s1: String(card.booster_primary.state === 'vaga'),
      vaga_s2: String(card.booster_conditional.state === 'vaga'),
      box: card.box || '',
      atributos: JSON.stringify(Object.keys(K.ABILITIES).map((name) => card.attrs[name])),
      habilidades: JSON.stringify(card.skills || []),
      aptidoes: JSON.stringify(card.aptitudes || {}),
      estilos_ia: JSON.stringify(card.ai_styles || []),
      corpo: card.corpo ? JSON.stringify(card.corpo) : ''
    };
    return row;
  }
  function rowsToCsv(rows) {
    return `\uFEFF${CARD_COLUMNS.join(',')}\n${rows.map((row) => CARD_COLUMNS.map((column) => quoteCsv(row[column] || '')).join(',')).join('\n')}`;
  }
  function cardsToCsv(cards) { return rowsToCsv(cards.map(cardToRow)); }
  function duplicateIds(rows, key = 'card_id') {
    const seen = new Set(), duplicates = new Set();
    for (const row of rows) {
      const id = String(row[key]);
      if (seen.has(id)) duplicates.add(id); else seen.add(id);
    }
    return [...duplicates].sort((left, right) => BigInt(left) < BigInt(right) ? -1 : 1);
  }
  function missingCounts(rows) {
    return Object.fromEntries(CARD_COLUMNS.map((column) => [column, rows.reduce((count, row) => count + (row[column] === '' ? 1 : 0), 0)]));
  }
  function validateCards(cards) {
    const rows = cards.map(cardToRow);
    const duplicates = duplicateIds(rows);
    return {
      records: rows.length,
      unique_card_ids: new Set(rows.map((row) => row.card_id)).size,
      duplicate_card_ids: duplicates,
      schema: CARD_COLUMNS,
      missing_by_field: missingCounts(rows),
      types: Object.fromEntries(['base', 'colecionavel', 'teste'].map((type) => [type, rows.filter((row) => row.tipo === type).length])),
      positions: Object.fromEntries([...new Set(rows.map((row) => row.posicao))].sort().map((position) => [position, rows.filter((row) => row.posicao === position).length]))
    };
  }
  function comparableCardValue(column, value) {
    const text = value == null ? '' : String(value);
    if (!STRUCTURED_COLUMNS.has(column) || text === '') return text;
    try { return stableJson(JSON.parse(text)); }
    catch (error) { throw new Error(`Comparação bloqueada: JSON inválido no campo ${column}.`); }
  }
  function compareCardRows(currentRows, baselineRows) {
    const currentDuplicates = duplicateIds(currentRows);
    const baselineDuplicates = duplicateIds(baselineRows);
    if (currentDuplicates.length || baselineDuplicates.length) throw new Error(`Comparação bloqueada: card_id duplicado (atual ${currentDuplicates.length}, base ${baselineDuplicates.length}).`);
    const current = new Map(currentRows.map((row) => [row.card_id, row]));
    const baseline = new Map(baselineRows.map((row) => [row.card_id, row]));
    const newCards = [], changedCards = [], inactiveCards = [];
    for (const [id, row] of current) {
      const before = baseline.get(id);
      if (!before) { newCards.push(row); continue; }
      const fields = CARD_COLUMNS.filter((column) => column !== 'card_id' && comparableCardValue(column, before[column]) !== comparableCardValue(column, row[column])).map((column) => ({ field: column, before: before[column] || '', after: row[column] || '' }));
      if (fields.length) changedCards.push({ card_id: id, fields, row });
    }
    for (const [id, row] of baseline) if (!current.has(id)) inactiveCards.push({ card_id: id, name: row.nome || '', type: row.tipo || '', row });
    const sortById = (left, right) => BigInt(left.card_id) < BigInt(right.card_id) ? -1 : 1;
    newCards.sort(sortById); changedCards.sort(sortById); inactiveCards.sort(sortById);
    return { new_cards: newCards, changed_cards: changedCards, possibly_inactive: inactiveCards, unchanged: currentRows.length - newCards.length - changedCards.length };
  }

  function bytesToHex(bytes) { return [...bytes].map((value) => value.toString(16).padStart(2, '0')).join(''); }
  async function validateSourceForRole(bytes, role) {
    const cpk = extractCpk(bytes);
    const entries = Object.keys(cpk).sort();
    if (role === 'dt261_bra') {
      if (!cpk['all.str']) throw new Error('A pasta escolhida não contém o arquivo de textos em português esperado.');
      const raw = await unpackWesys(cpk['all.str']);
      if (raw.length < 16 || u32(raw, 0) < 1) throw new Error('O all.str encontrado é inválido.');
      return { role, entries, all_str_bytes: raw.length, text_sections: u32(raw, 0) };
    }
    if (!cpk['Player.bin']) throw new Error('O CPK escolhido não contém Player.bin.');
    const players = await unpackWesys(cpk['Player.bin']);
    if (role === 'dt870_updated' && players.length % K.RECORD_SIZE !== 0) {
      throw new Error(`Este não é o DT870 da atualização: Player.bin não usa registros de ${K.RECORD_SIZE} bytes.`);
    }
    if (role === 'dt870_updated') {
      if (!cpk['Coach.bin'] || !cpk['Country.bin']) {
        throw new Error('O DT870 da atualização não contém Coach.bin e Country.bin, necessários para técnicos.');
      }
      const coach = await unpackWesys(cpk['Coach.bin']);
      const country = await unpackWesys(cpk['Country.bin']);
      if (coach.length % 176 !== 0 || coach.length / 176 !== 1478) {
        throw new Error('Coach.bin do DT870 atualizado não respeita 1.478 registros de 176 bytes.');
      }
      if (country.length % 1488 !== 0 || country.length / 1488 !== 214) {
        throw new Error('Country.bin do DT870 atualizado não respeita 214 registros de 1.488 bytes.');
      }
    }
    if (role === 'dt870_original' && players.length % 392 !== 0) {
      throw new Error('Este não é o DT870 original: Player.bin não usa registros de 392 bytes.');
    }
    if (role === 'dt200') {
      if (players.length % K.RECORD_SIZE !== 0 || !cpk['PlayerBooster.bin'] || !cpk['Playstyle.bin']) {
        throw new Error('Este não é o DT200 base esperado.');
      }
    }
    return {
      role,
      entries,
      player_record_size: role === 'dt870_original' ? 392 : K.RECORD_SIZE,
      player_records: players.length / (role === 'dt870_original' ? 392 : K.RECORD_SIZE)
    };
  }

  async function readPhysicalCatalog(cpk, spec, sourceRole) {
    if (!cpk[spec.file]) throw new Error(`${spec.file} não foi encontrado em ${sourceRole}.`);
    const raw = await unpackWesys(cpk[spec.file]);
    const prefix = (spec.prefix_by_role && spec.prefix_by_role[sourceRole]) || 0;
    if ((raw.length - prefix) <= 0 || (raw.length - prefix) % spec.record_size !== 0) throw new Error(`${spec.file} de ${sourceRole} não respeita prefixo ${prefix} + registros de ${spec.record_size} bytes.`);
    const sourceFileSha256 = await sha256(raw);
    const records = [];
    for (let offset = prefix; offset < raw.length; offset += spec.record_size) {
      records.push({
        id: String(spec.id(raw, offset)),
        raw_hex: bytesToHex(raw.subarray(offset, offset + spec.record_size)),
        source_role: sourceRole,
        record_index: (offset - prefix) / spec.record_size,
        source_file_sha256: sourceFileSha256,
        ...(spec.decode ? spec.decode(raw, offset) : {})
      });
    }
    const duplicate_ids = duplicateIds(records, 'id');
    if (duplicate_ids.length && !spec.allow_duplicate_occurrences) throw new Error(`${spec.file} de ${sourceRole} contém IDs duplicados.`);
    return { records, duplicate_ids };
  }

  async function extractCoachDisplayCatalog(cpk, textCatalog) {
    if (!cpk['Coach.bin'] || !cpk['Country.bin']) throw new Error('Coach.bin ou Country.bin ausente no DT870 atualizado.');
    const coach = await unpackWesys(cpk['Coach.bin']);
    const country = await unpackWesys(cpk['Country.bin']);
    if (coach.length % 176 !== 0 || coach.length / 176 !== 1478) throw new Error('Coach.bin atual não contém 1.478 registros de 176 bytes.');
    if (country.length % 1488 !== 0 || country.length / 1488 !== 214) throw new Error('Country.bin atual não contém 214 registros de 1.488 bytes.');
    const coachHash = await sha256(coach);
    const countryHash = await sha256(country);
    const nationalities = [];
    const nationalityByCode = new Map();
    for (let offset = 0, recordIndex = 0; offset < country.length; offset += 1488, recordIndex += 1) {
      const code = readBits(country, offset, 10, 9);
      const record = {
        id: String(code),
        codigo_jogo: code,
        nome_pt_br: fixedNullUtf8(country, offset + 788, 70),
        sigla: fixedNullUtf8(country, offset + 708, 10),
        source_role: 'dt870_updated',
        arquivo: 'Country.bin',
        record_index: recordIndex,
        record_size: 1488,
        codigo_bit: 10,
        codigo_largura: 9,
        nome_offset: 788,
        nome_largura: 70,
        nome_codificacao: 'utf-8',
        sigla_offset: 708,
        sigla_largura: 10,
        source_file_sha256: countryHash,
        presente_dt200: true,
        presente_dt870_original: true,
        presente_dt870_atualizacao: true,
        ativo: true
      };
      if (!record.nome_pt_br || !record.sigla || nationalityByCode.has(code)) throw new Error(`Country.bin inválido no registro ${recordIndex}.`);
      record.fingerprint = stableJson(record);
      nationalities.push(record);
      nationalityByCode.set(code, record);
    }
    const affinityText = (textCatalog.records || []).find((record) => record.id === 'Any1W:495');
    if (!affinityText || affinityText.texto !== 'Jogadores de AT') throw new Error('Rótulo oficial comprovado da afinidade 5 não foi encontrado em Any1W:495.');
    const affinities = Array.from({ length: 8 }, (_, code) => {
      const record = {
        id: String(code),
        codigo_jogo: code,
        nome_pt: code === 5 ? affinityText.texto : null,
        nome_tela: code === 5 ? 'Atacantes' : null,
        ausencia_legitima: code === 0,
        rotulo_confirmado: code === 5,
        source_role: 'dt870_updated',
        arquivo: 'Coach.bin',
        bit: 187,
        largura: 3,
        source_file_sha256: coachHash,
        texto_source_role: code === 5 ? 'dt261_bra' : null,
        texto_arquivo: code === 5 ? 'all.str' : null,
        texto_secao: code === 5 ? 'Any1W' : null,
        texto_id: code === 5 ? 495 : null,
        pode_rodar: code === 0 || code === 5,
        falta_o_que: code === 0 || code === 5 ? null : 'vínculo físico código-rótulo ainda não comprovado',
        ativo: true
      };
      return { ...record, fingerprint: stableJson(record) };
    });
    const styleBits = [
      ['possessionGame', 206], ['longBallCounter', 238], ['quickCounter', 224],
      ['longBall', 199], ['outWide', 213]
    ];
    const technicians = [];
    for (let offset = 0, recordIndex = 0; offset < coach.length; offset += 176, recordIndex += 1) {
      const nationalityCode = readBits(coach, offset, 170, 8);
      const nationality = nationalityByCode.get(nationalityCode);
      if (!nationality) throw new Error(`Coach.bin referencia nacionalidade ausente: ${nationalityCode}.`);
      const boosts = [];
      for (const [order, bit] of [[1, 160], [2, 148]]) {
        const encoded = readBits(coach, offset, bit, 5);
        if (encoded) boosts.push({ ordem: order, atributo_idx_canonico: encoded - 1, delta: 1, bit, largura: 5 });
      }
      const ageRaw = readBits(coach, offset, 231, 7);
      const proficiencias = Object.fromEntries(styleBits.map(([code, bit]) => [code, readBits(coach, offset, bit, 7)]));
      const sobreposicao = readBits(coach, offset, 135, 7);
      if (sobreposicao) proficiencias.overload = sobreposicao;
      const record = {
        id: u64String(coach, offset),
        nome_jp: fixedNullUtf8(coach, offset + 32, 46),
        nome_en: fixedNullUtf8(coach, offset + 78, 46),
        nome_cn: fixedNullUtf8(coach, offset + 124, 52),
        proficiencias,
        boosts,
        idade: ageRaw + 14,
        idade_valor_fisico: ageRaw,
        nacionalidade_codigo: nationalityCode,
        nacionalidade_nome_pt_br: nationality.nome_pt_br,
        nacionalidade_sigla: nationality.sigla,
        afinidade_codigo: readBits(coach, offset, 187, 3),
        source_role: 'dt870_updated',
        arquivo: 'Coach.bin',
        record_index: recordIndex,
        record_size: 176,
        source_file_sha256: coachHash,
        field_contract: {
          idade: { bit: 231, largura: 7, transformacao: 'valor_fisico + 14' },
          nacionalidade: { bit: 170, largura: 8, resolve_em: 'Country.bin.codigo bit 10 largura 9' },
          afinidade: { bit: 187, largura: 3, zero: 'ausencia_legitima' },
          sobreposicao: { bit: 135, largura: 7, zero: 'ausencia_legitima; relação somente quando valor maior que zero' }
        },
        ativo: true
      };
      record.fingerprint = stableJson(record);
      technicians.push(record);
    }
    if (duplicateIds(technicians, 'id').length) throw new Error('Coach.bin atual contém IDs físicos duplicados.');
    return {
      technicians,
      nationalities,
      affinities,
      coach_hash: coachHash,
      country_hash: countryHash
    };
  }

  async function extractMetadataByFamily(sourceBytes, sourceDescriptors, log = () => {}) {
    const required = ['dt870_updated', 'dt200', 'dt870_original', 'dt261_bra'];
    for (const role of required) if (!sourceBytes[role]) throw new Error(`Fonte obrigatória ausente para metadados: ${role}.`);
    const cpks = Object.fromEntries(required.map((role) => [role, extractCpk(sourceBytes[role])]));
    const skillSpec = { file: 'PlayerSkill.bin', record_size: 104, id: (buffer, offset) => u32(buffer, offset) };
    const boosterSpec = {
      file: 'PlayerBooster.bin',
      record_size: 40,
      prefix_by_role: { dt870_original: 24 },
      allow_duplicate_occurrences: true,
      id: (buffer, offset) => readBits(buffer, offset, 112, 10),
      decode: (buffer, offset) => ({
        tipo_condicao_raw: readBits(buffer, offset, 296, 3),
        tipo_condicao_espelho_u32: u32(buffer, offset + 8),
        tipo_bit: 296,
        tipo_largura: 3,
        tipo_espelho_bit: 64,
        tipo_espelho_largura: 32
      })
    };
    const playstyleSpec = { file: 'Playstyle.bin', record_size: 168, id: (buffer, offset) => u32(buffer, offset) };

    const skillCatalog = await readPhysicalCatalog(cpks.dt870_updated, skillSpec, 'dt870_updated');
    const habilidades = {
      supported: true,
      file: 'PlayerSkill.bin',
      source_policy: 'DT870 da atualização',
      record_size: 104,
      id_contract: 'u32 little-endian no byte 0',
      records: skillCatalog.records,
      duplicate_ids: skillCatalog.duplicate_ids
    };
    log(`habilidades · DT870 da atualização: ${habilidades.records.length}`);

    const boosterSources = {};
    for (const role of ['dt200', 'dt870_updated']) {
      boosterSources[role] = await readPhysicalCatalog(cpks[role], boosterSpec, role);
      log(`ímpetos · ${role}: ${boosterSources[role].records.length}`);
    }
    const expectedOriginalHash = CATALOG_SOURCE_MAP.DT870_ORIGINAL_CPK_SHA256;
    const actualOriginalHash = sourceDescriptors.dt870_original && sourceDescriptors.dt870_original.sha256;
    if (!expectedOriginalHash || !actualOriginalHash || actualOriginalHash.toLowerCase() !== expectedOriginalHash.toLowerCase()) {
      throw new Error('DT870 original não corresponde ao fingerprint do mapa físico comprovado; ímpetos legados foram bloqueados.');
    }
    const originalIndex = CATALOG_SOURCE_MAP.BOOSTER_DT870_ORIGINAL_INDEX || {};
    if (Object.keys(originalIndex).length !== 102) throw new Error('Mapa físico do DT870 original está incompleto.');
    const originalBoosterRaw = await unpackWesys(cpks.dt870_original['PlayerBooster.bin']);
    const originalFileSha256 = await sha256(originalBoosterRaw);
    boosterSources.dt870_original = {
      records: Object.entries(originalIndex).map(([id, mappedRecordIndex]) => ({ id, source_role: 'dt870_original', mapped_record_index: mappedRecordIndex, source_file_sha256: originalFileSha256 })),
      duplicate_ids: []
    };
    log(`ímpetos · dt870_original pelo mapa físico selado: ${boosterSources.dt870_original.records.length}`);
    const boosterById = new Map();
    for (const role of ['dt200', 'dt870_original', 'dt870_updated']) {
      for (const record of boosterSources[role].records) {
        if (!boosterById.has(record.id)) boosterById.set(record.id, { id: record.id, source_records: {}, source_details: {} });
        const mergedRecord = boosterById.get(record.id);
        const sourceRecords = mergedRecord.source_records;
        if (!sourceRecords[role]) sourceRecords[role] = [];
        const evidence = record.raw_hex || stableJson({ mapped_record_index: record.mapped_record_index, source_file_sha256: record.source_file_sha256 });
        if (!sourceRecords[role].includes(evidence)) sourceRecords[role].push(evidence);
        if (!mergedRecord.source_details[role]) mergedRecord.source_details[role] = [];
        mergedRecord.source_details[role].push({
          record_index: record.record_index ?? record.mapped_record_index ?? null,
          source_file_sha256: record.source_file_sha256 || null,
          tipo_condicao_raw: record.tipo_condicao_raw ?? null,
          tipo_condicao_espelho_u32: record.tipo_condicao_espelho_u32 ?? null,
          tipo_bit: record.tipo_bit ?? null,
          tipo_largura: record.tipo_largura ?? null,
          tipo_espelho_bit: record.tipo_espelho_bit ?? null,
          tipo_espelho_largura: record.tipo_espelho_largura ?? null
        });
      }
    }
    const boosterPriority = ['dt870_updated', 'dt870_original', 'dt200'];
    const impetos = {
      supported: true,
      file: 'PlayerBooster.bin',
      source_policy: 'união por ID com procedência preservada; DT870 atualizado tem prioridade de conteúdo quando presente',
      record_size: 40,
      id_contract: 'bit 112, largura 10',
      records: [...boosterById.values()].map((record) => {
        const origins = ['dt200', 'dt870_original', 'dt870_updated'].filter((role) => role in record.source_records);
        const preferred_source = boosterPriority.find((role) => role in record.source_records);
        const preferred = (record.source_details[preferred_source] || [])[0] || {};
        const rawType = preferred.tipo_condicao_raw ?? null;
        const isVacancySlotMarker = record.id === '136' && rawType === 4;
        const isNonEffectRaw4 = rawType === 4;
        return {
          id: record.id,
          origins,
          preferred_source,
          source_fingerprints: record.source_records,
          source_details: record.source_details,
          tipo_condicao_raw: isNonEffectRaw4 ? null : rawType,
          tipo_condicao_status: isVacancySlotMarker ? 'vaga_de_slot' : (isNonEffectRaw4 ? 'registro_nao_impeto_raw4' : (rawType === null ? 'nao_coletado' : 'coletado')),
          vaga_de_slot: isVacancySlotMarker,
          fingerprint: stableJson({
            id: record.id,
            origins,
            source_fingerprints: record.source_records,
            tipo_condicao_raw: isNonEffectRaw4 ? null : rawType,
            tipo_condicao_status: isVacancySlotMarker ? 'vaga_de_slot' : (isNonEffectRaw4 ? 'registro_nao_impeto_raw4' : (rawType === null ? 'nao_coletado' : 'coletado'))
          })
        };
      }),
      duplicate_ids: []
    };
    log(`ímpetos · união com procedência: ${impetos.records.length}`);

    const baseStyles = await readPhysicalCatalog(cpks.dt200, playstyleSpec, 'dt200');
    const overlayStyles = await readPhysicalCatalog(cpks.dt870_updated, playstyleSpec, 'dt870_updated');
    const overlayById = new Map(overlayStyles.records.map((record) => [record.id, record]));
    const baseIds = new Set(baseStyles.records.map((record) => record.id));
    const overlayOnly = overlayStyles.records.filter((record) => !baseIds.has(record.id)).map((record) => ({
      id: record.id,
      source_role: 'dt870_updated',
      reason: 'overlay sem registro semântico correspondente no DT200'
    }));
    const playstyles = {
      supported: true,
      file: 'Playstyle.bin',
      source_policy: 'DT200 é a base semântica; DT870 atualizado é somente overlay',
      record_size: 168,
      id_contract: 'u32 little-endian no byte 0',
      records: baseStyles.records.map((base) => {
        const overlay = overlayById.get(base.id);
        const record = {
          id: base.id,
          semantic_source: 'dt200',
          base_raw_hex: base.raw_hex,
          overlay_present: Boolean(overlay),
          overlay_raw_hex: overlay ? overlay.raw_hex : null
        };
        return { ...record, fingerprint: stableJson(record) };
      }),
      unsupported_entries: overlayOnly,
      duplicate_ids: []
    };
    log(`playstyles · base DT200: ${playstyles.records.length}; overlay sem base: ${overlayOnly.length}`);

    const textos = await extractTextCatalogFromCpk(sourceBytes.dt261_bra);
    log(`textos · ${textos.records.length} chaves oficiais únicas em ${textos.section_count} seções`);
    const coachCatalog = await extractCoachDisplayCatalog(cpks.dt870_updated, textos);
    const tecnicos = {
      supported: true,
      file: 'Coach.bin + Country.bin',
      source_policy: 'DT870 da atualização; identificação por ID físico u64',
      record_size: 176,
      id_contract: 'u64 little-endian no byte 0',
      contract: 'clubef-tecnicos-carga-v4-sobreposicao',
      records: coachCatalog.technicians,
      duplicate_ids: []
    };
    const nacionalidades = {
      supported: true,
      file: 'Country.bin',
      source_policy: 'arquivo byte-idêntico em DT200, DT870 original e DT870 atualizado; leitura autoritativa no DT870 atualizado',
      record_size: 1488,
      id_contract: 'bit 10, largura 9',
      contract: 'clubef-nacionalidades-v1',
      records: coachCatalog.nationalities,
      duplicate_ids: []
    };
    const afinidadesTecnico = {
      supported: true,
      file: 'Coach.bin + all.str',
      source_policy: 'código físico do DT870 atualizado; rótulo somente quando comprovado no dicionário pt-BR',
      id_contract: 'Coach.bin bit 187, largura 3',
      contract: 'clubef-afinidades-tecnico-v1',
      records: coachCatalog.affinities,
      duplicate_ids: []
    };
    log(`técnicos · DT870 da atualização: ${tecnicos.records.length}; nacionalidades: ${nacionalidades.records.length}; afinidades: ${afinidadesTecnico.records.length}`);

    const unsupported = (file, reason, sourcePolicy = null) => ({
      supported: false,
      status: 'nao_suportado_nesta_atualizacao',
      file,
      reason,
      source_policy: sourcePolicy,
      records: [],
      duplicate_ids: []
    });
    const catalogs = {
      habilidades,
      impetos,
      playstyles,
      posicoes: {
        supported: true,
        file: 'Player.bin + mapeamento físico',
        source_policy: 'DT870 da atualização',
        records: Object.entries(K.POSITION_NAMES).map(([id, codigo_en]) => ({ id: String(id), codigo_en, fingerprint: stableJson({ id: String(id), codigo_en }) })),
        duplicate_ids: []
      },
      textos,
      tecnicos,
      nacionalidades,
      afinidades_tecnico: afinidadesTecnico,
      estilos_ia: unsupported('Player.bin', 'bits físicos conhecidos, mas catálogo de nomes não possui fonte física integral'),
      efeitos_de_impeto: unsupported('PlayerBooster.bin', 'endereçamento dos efeitos não é integral e três associações permanecem convencionais'),
      times_e_vinculos: unsupported('Team.bin + PlayerAssignment.bin', 'layout físico ainda não foi comprovado integralmente'),
      potw: unsupported('PlayerWeekly.bin', 'layout físico ainda não foi comprovado integralmente'),
      habilidade_extra_de_variacao: unsupported('PlayerVariationPrSkill.bin', 'layout físico ainda não foi comprovado integralmente')
    };
    return {
      contract: 'clubef-physical-metadata-v4',
      source_policy: 'por família; sem mistura genérica de CPKs',
      sources: sourceDescriptors,
      catalogs
    };
  }

  async function extractMetadataFromCpk(bytes, source, log = () => {}) {
    const cpk = extractCpk(bytes);
    const specs = {
      habilidades: { file: 'PlayerSkill.bin', record_size: 104, id: (buffer, offset) => u32(buffer, offset), id_contract: 'u32 little-endian no byte 0' },
      impetos: {
        file: 'PlayerBooster.bin',
        record_size: 40,
        id: (buffer, offset) => readBits(buffer, offset, 112, 10),
        id_contract: 'bit 112, largura 10',
        decode: (buffer, offset) => ({
          tipo_condicao_raw: readBits(buffer, offset, 296, 3),
          tipo_condicao_espelho_u32: u32(buffer, offset + 8),
          tipo_bit: 296,
          tipo_largura: 3
        })
      },
      playstyles: { file: 'Playstyle.bin', record_size: 168, id: (buffer, offset) => u32(buffer, offset), id_contract: 'u32 little-endian no byte 0' },
      tecnicos: { file: 'Coach.bin', record_size: 176, id: (buffer, offset) => u32(buffer, offset), id_contract: 'u32 little-endian no byte 0' }
    };
    const catalogs = {};
    for (const [name, spec] of Object.entries(specs)) {
      if (!cpk[spec.file]) { catalogs[name] = { file: spec.file, missing: true, records: [] }; continue; }
      const raw = await unpackWesys(cpk[spec.file]);
      if (raw.length % spec.record_size !== 0) throw new Error(`${spec.file} não é múltiplo de ${spec.record_size} bytes.`);
      const records = [];
      for (let offset = 0; offset < raw.length; offset += spec.record_size) records.push({
        id: String(spec.id(raw, offset)),
        raw_hex: bytesToHex(raw.subarray(offset, offset + spec.record_size)),
        record_index: offset / spec.record_size,
        ...(spec.decode ? spec.decode(raw, offset) : {})
      });
      catalogs[name] = { file: spec.file, record_size: spec.record_size, id_contract: spec.id_contract, records, duplicate_ids: duplicateIds(records, 'id') };
      log(`${name}: ${records.length}`);
    }
    catalogs.posicoes = { file: 'Player.bin + mapeamento físico', records: Object.entries(K.POSITION_NAMES).map(([id, codigo_en]) => ({ id: String(id), codigo_en, fingerprint: stableJson({ id: String(id), codigo_en }) })) };
    catalogs.estilos_ia = { file: 'Player.bin + mapeamento físico', records: Object.entries(K.AI_PLAYING_STYLES).map(([nome_en, id]) => ({ id: String(id), nome_en, fingerprint: stableJson({ id: String(id), nome_en }) })) };
    return { contract: 'clubef-physical-metadata-v3', source, catalogs };
  }
  function compareMetadata(current, baseline) {
    const output = {};
    const names = [...new Set([...Object.keys(current.catalogs || {}), ...Object.keys(baseline.catalogs || {})])].sort();
    for (const name of names) {
      const currentCatalog = current.catalogs[name] || { records: [] };
      const baselineCatalog = baseline.catalogs[name] || { records: [] };
      if (currentCatalog.supported === false) {
        output[name] = { status: 'nao_suportado_nesta_atualizacao', reason: currentCatalog.reason || 'família sem mapeamento físico integral', current: 0, baseline_active: (baselineCatalog.records || []).filter((record) => record.ativo !== false).length, new_entries: [], changed_entries: [], absent_entries: [], without_previous_fingerprint: 0, duplicate_ids: [], diagnostics: { file: currentCatalog.file || null, source_policy: currentCatalog.source_policy || null, source_fingerprint: currentCatalog.source_fingerprint || null } };
        continue;
      }
      if (baselineCatalog.comparavel === false) {
        output[name] = { status: 'sem_gabarito', reason: baselineCatalog.motivo || 'catálogo sem referência comparável', current: currentCatalog.records.length, baseline_active: 0, new_entries: [], changed_entries: [], absent_entries: [], without_previous_fingerprint: 0, duplicate_ids: currentCatalog.duplicate_ids || [] };
        continue;
      }
      const currentMap = new Map((currentCatalog.records || []).map((record) => [String(record.id), record]));
      const baselineMap = new Map((baselineCatalog.records || []).filter((record) => record.ativo !== false).map((record) => [String(record.id), record]));
      const newEntries = [], changedEntries = [], absentEntries = [];
      let withoutPreviousFingerprint = 0;
      for (const [id, record] of currentMap) {
        const old = baselineMap.get(id);
        if (!old) newEntries.push(record);
        else {
          const after = record.raw_hex || record.fingerprint;
          const before = old.raw_hex || old.fingerprint;
          if (after && before && after !== before) changedEntries.push({ id, before, after, record });
          else if (!(after && before)) withoutPreviousFingerprint += 1;
        }
      }
      for (const [id, record] of baselineMap) if (!currentMap.has(id)) absentEntries.push({ id, record });
      output[name] = { status: 'comparado', current: currentMap.size, baseline_active: baselineMap.size, new_entries: newEntries, changed_entries: changedEntries, absent_entries: absentEntries, without_previous_fingerprint: withoutPreviousFingerprint, duplicate_ids: currentCatalog.duplicate_ids || [] };
    }
    return output;
  }

  async function sealManifest(manifest) {
    const body = { ...manifest };
    delete body.manifest_sha256;
    return { ...body, manifest_sha256: await sha256(stableJson(body)) };
  }
  function makeExecutionId() { return crypto.randomUUID(); }
  function expirationFromNow(minutes = 60) { return new Date(Date.now() + minutes * 60 * 1000).toISOString(); }
  function ensureCurrentManifest(manifest) {
    if (!manifest || manifest.contract !== CONTRACT_VERSION) throw new Error('Manifesto incompatível com o extrator atual.');
    if (!manifest.execution_id || !manifest.manifest_sha256) throw new Error('Manifesto não selado.');
    if (Date.now() >= Date.parse(manifest.expires_at)) throw new Error('Diff obsoleto: faça nova extração e comparação.');
    return true;
  }
  function selectionSummary(diff, selection) {
    const selected = new Set(selection || []);
    const all = [
      ...diff.new_cards.map((row) => ({ key: `new:${row.card_id}`, action: 'insert', card_id: row.card_id, row })),
      ...diff.changed_cards.map((entry) => ({ key: `change:${entry.card_id}`, action: 'update', card_id: entry.card_id, row: entry.row, fields: entry.fields })),
      ...diff.possibly_inactive.map((entry) => ({ key: `inactive:${entry.card_id}`, action: 'inactive', card_id: entry.card_id, row: entry.row }))
    ];
    const items = all.filter((item) => selected.has(item.key));
    return { items, counts: { insert: items.filter((item) => item.action === 'insert').length, update: items.filter((item) => item.action === 'update').length, inactive: items.filter((item) => item.action === 'inactive').length } };
  }

  global.CLUBEF_CORE = Object.freeze({
    CONTRACT_VERSION,
    CARD_COLUMNS,
    STRUCTURED_COLUMNS,
    stableJson,
    sha256,
    parseCsv,
    validateSchema,
    cardToRow,
    rowsToCsv,
    cardsToCsv,
    duplicateIds,
    missingCounts,
    validateCards,
    compareCardRows,
    extractCardsFromCpk,
    validateSourceForRole,
    extractMetadataFromCpk,
    extractMetadataByFamily,
    compareMetadata,
    parseAllStr,
    extractTextCatalogFromCpk,
    validateTextCatalogStructure,
    compareTextCatalog,
    TEXT_SECTION_RELOCATION,
    sealManifest,
    makeExecutionId,
    expirationFromNow,
    ensureCurrentManifest,
    selectionSummary
  });
})(globalThis);
