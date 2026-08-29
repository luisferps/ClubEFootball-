'use strict';

/**
 * Núcleo novo do Extrator ClubEfootball.
 * Somente funções puras de leitura, decodificação, comparação e manifestação.
 * Não contém persistência, credencial, cliente Supabase ou efeito automático.
 */
(function installCore(global) {
  const { K, IMP, OVRW, STYLE_CAT, DEF_CAT } = global.CLUBEF_PHYSICAL_MAP;
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
  const CONTRACT_VERSION = 'clubef-extrator-v3';

  function u32(bytes, offset) {
    return (bytes[offset] | (bytes[offset + 1] << 8) | (bytes[offset + 2] << 16) | (bytes[offset + 3] << 24)) >>> 0;
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
    card.booster_primary = decodeBoosterSlot(readBits(bytes, base, 308, 8));
    card.booster_conditional = decodeBoosterSlot(readBits(bytes, base, 288, 8));
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
      const fields = CARD_COLUMNS.filter((column) => column !== 'card_id' && (before[column] || '') !== (row[column] || '')).map((column) => ({ field: column, before: before[column] || '', after: row[column] || '' }));
      if (fields.length) changedCards.push({ card_id: id, fields, row });
    }
    for (const [id, row] of baseline) if (!current.has(id)) inactiveCards.push({ card_id: id, name: row.nome || '', type: row.tipo || '', row });
    const sortById = (left, right) => BigInt(left.card_id) < BigInt(right.card_id) ? -1 : 1;
    newCards.sort(sortById); changedCards.sort(sortById); inactiveCards.sort(sortById);
    return { new_cards: newCards, changed_cards: changedCards, possibly_inactive: inactiveCards, unchanged: currentRows.length - newCards.length - changedCards.length };
  }

  function bytesToHex(bytes) { return [...bytes].map((value) => value.toString(16).padStart(2, '0')).join(''); }
  async function extractMetadataFromCpk(bytes, source, log = () => {}) {
    const cpk = extractCpk(bytes);
    const specs = {
      habilidades: { file: 'PlayerSkill.bin', record_size: 104, id: (buffer, offset) => u32(buffer, offset), id_contract: 'u32 little-endian no byte 0' },
      impetos: { file: 'PlayerBooster.bin', record_size: 40, id: (buffer, offset) => readBits(buffer, offset, 112, 10), id_contract: 'bit 112, largura 10' },
      playstyles: { file: 'Playstyle.bin', record_size: 168, id: (buffer, offset) => u32(buffer, offset), id_contract: 'u32 little-endian no byte 0' },
      tecnicos: { file: 'Coach.bin', record_size: 176, id: (buffer, offset) => u32(buffer, offset), id_contract: 'u32 little-endian no byte 0' }
    };
    const catalogs = {};
    for (const [name, spec] of Object.entries(specs)) {
      if (!cpk[spec.file]) { catalogs[name] = { file: spec.file, missing: true, records: [] }; continue; }
      const raw = await unpackWesys(cpk[spec.file]);
      if (raw.length % spec.record_size !== 0) throw new Error(`${spec.file} não é múltiplo de ${spec.record_size} bytes.`);
      const records = [];
      for (let offset = 0; offset < raw.length; offset += spec.record_size) records.push({ id: String(spec.id(raw, offset)), raw_hex: bytesToHex(raw.subarray(offset, offset + spec.record_size)) });
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
    extractMetadataFromCpk,
    compareMetadata,
    sealManifest,
    makeExecutionId,
    expirationFromNow,
    ensureCurrentManifest,
    selectionSummary
  });
})(globalThis);
