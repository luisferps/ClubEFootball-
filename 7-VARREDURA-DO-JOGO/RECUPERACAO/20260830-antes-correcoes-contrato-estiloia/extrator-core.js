'use strict';

/**
 * Núcleo novo do Extrator eFootball.
 * Somente funções puras de leitura, decodificação, comparação e manifestação.
 * Não contém persistência, credencial, cliente Supabase ou efeito automático.
 */
(function installCore(global) {
  const CONTRACT_READER = global.CLUBEF_CONTRACT_READER;
  if (!CONTRACT_READER) throw new Error('leitura-contrato.js deve ser carregado antes do núcleo');
  const { K, OVRW, STYLE_CAT, DEF_CAT } = global.CLUBEF_PHYSICAL_MAP;
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
  const CARD_RELATIONS_CONTRACT_VERSION = 'clubef-card-relations-physical-v1';
  const CARD_DIMENSIONS_CONTRACT_VERSION = 'clubef-card-dimensions-physical-v2';
  const CARD_DIMENSION_TYPES = Object.freeze([
    { tipo_carta_id: 'player_type_0_subtype_0', codigo_tipo_fisico: 0, marcador_subtipo: 0, usa_player_delete_list: false, chave_texto: 'Any1W:980', nome_exibicao: 'Normal', status_associacao: 'rotulo_dicionario_ancora_tela_sem_ponte_fisica', tipo_provisorio: false },
    { tipo_carta_id: 'player_delete_list', codigo_tipo_fisico: 0, marcador_subtipo: 0, usa_player_delete_list: true, chave_texto: 'Any2W:923', nome_exibicao: 'Jogador indisponível', status_associacao: 'classificacao_operacional_usuario_sem_ponte_fisica', tipo_provisorio: false },
    { tipo_carta_id: 'player_type_1_subtype_0', codigo_tipo_fisico: 1, marcador_subtipo: 0, usa_player_delete_list: false, chave_texto: 'Any1W:981', nome_exibicao: 'Lendário', status_associacao: 'rotulo_dicionario_ancora_tela_sem_ponte_fisica', tipo_provisorio: false },
    { tipo_carta_id: 'player_type_3_subtype_0', codigo_tipo_fisico: 3, marcador_subtipo: 0, usa_player_delete_list: false, chave_texto: 'Any1W:982', nome_exibicao: 'Em destaque', status_associacao: 'rotulo_dicionario_ancora_tela_sem_ponte_fisica', tipo_provisorio: false },
    { tipo_carta_id: 'player_type_3_subtype_1', codigo_tipo_fisico: 3, marcador_subtipo: 1, usa_player_delete_list: false, chave_texto: 'Any1W:983', nome_exibicao: 'Em evidência', status_associacao: 'rotulo_dicionario_ancora_tela_sem_ponte_fisica', tipo_provisorio: false },
    { tipo_carta_id: 'player_type_4_subtype_0', codigo_tipo_fisico: 4, marcador_subtipo: 0, usa_player_delete_list: false, chave_texto: null, nome_exibicao: 'Desconhecido 1', status_associacao: 'provisorio_sem_prova_nominal', tipo_provisorio: true },
    { tipo_carta_id: 'player_type_5_subtype_0', codigo_tipo_fisico: 5, marcador_subtipo: 0, usa_player_delete_list: false, chave_texto: 'Any2W:360', nome_exibicao: 'Épico', status_associacao: 'rotulo_dicionario_ancora_tela_sem_ponte_fisica', tipo_provisorio: false },
    { tipo_carta_id: 'player_type_5_subtype_1', codigo_tipo_fisico: 5, marcador_subtipo: 1, usa_player_delete_list: false, chave_texto: 'Any3W:423', nome_exibicao: 'Épico - Big Time', status_associacao: 'rotulo_dicionario_ancora_tela_sem_ponte_fisica', tipo_provisorio: false },
    { tipo_carta_id: 'player_type_6_subtype_0', codigo_tipo_fisico: 6, marcador_subtipo: 0, usa_player_delete_list: false, chave_texto: 'Any2W:361', nome_exibicao: 'Distinguido', status_associacao: 'rotulo_dicionario_ancora_tela_sem_ponte_fisica', tipo_provisorio: false },
    { tipo_carta_id: 'player_type_6_subtype_1', codigo_tipo_fisico: 6, marcador_subtipo: 1, usa_player_delete_list: false, chave_texto: 'Any3W:422', nome_exibicao: 'Distinguido - Show Time', status_associacao: 'rotulo_dicionario_ancora_tela_sem_ponte_fisica', tipo_provisorio: false },
    { tipo_carta_id: 'player_type_7_subtype_0', codigo_tipo_fisico: 7, marcador_subtipo: 0, usa_player_delete_list: false, chave_texto: null, nome_exibicao: 'Desconhecido 2', status_associacao: 'provisorio_sem_prova_nominal', tipo_provisorio: true }
  ]);

  function u32(bytes, offset) {
    return (bytes[offset] | (bytes[offset + 1] << 8) | (bytes[offset + 2] << 16) | (bytes[offset + 3] << 24)) >>> 0;
  }
  function u16(bytes, offset) {
    return (bytes[offset] | (bytes[offset + 1] << 8)) >>> 0;
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

  async function validateSourceByContract(bytes, readingContract, role) {
    const index = CONTRACT_READER.requirePlan(readingContract);
    const requested = [...index.files.values()].filter((file) => file.papel_fonte === role && file.obrigatorio);
    const locator = (readingContract.localizadores_fontes || []).find((item) => item && item.papel_fonte === role && Number(item.ordem) === 1);
    if (!locator) throw new Error(`o contrato ativo não declara localizador para a fonte ${role}`);
    const cpkHash = await sha256(bytes);
    if (locator.sha256_cpk && cpkHash !== String(locator.sha256_cpk).toLowerCase()) throw new Error(`fingerprint do CPK divergente: ${role}`);
    if (!requested.length) {
      return {
        contract: Object.fromEntries(CONTRACT_READER.SEAL_KEYS.map((key) => [key, readingContract[key]])),
        role,
        cpk_sha256: cpkHash,
        files: [],
        database_write: false
      };
    }
    const cpk = extractCpk(bytes);
    const verified = [];
    for (const file of requested) {
      const packed = cpk[file.arquivo];
      if (!packed) throw new Error(`${file.arquivo} não foi encontrado na fonte solicitada pelo contrato`);
      const raw = await unpackWesys(packed);
      const result = await CONTRACT_READER.verifyFile(readingContract, file.arquivo, raw);
      verified.push({ arquivo: file.arquivo, sha256: result.actualHash, decodificador: file.decodificador, tamanho_registro: file.tamanho_registro });
    }
    return {
      contract: Object.fromEntries(CONTRACT_READER.SEAL_KEYS.map((key) => [key, readingContract[key]])),
      role,
      cpk_sha256: cpkHash,
      files: verified,
      database_write: false
    };
  }

  async function extractCardSlotsByContract(bytes, readingContract) {
    const index = CONTRACT_READER.requirePlan(readingContract);
    const required = ['carta.id', 'carta.impeto.slot1', 'carta.impeto.slot2'];
    const fields = required.map((key) => index.fields.get(key));
    if (fields.some((field) => !field)) throw new Error('o contrato não contém os três campos de slots de carta');
    const playerFile = index.files.get(fields[0].arquivo_id);
    if (!playerFile || fields.some((field) => field.arquivo_id !== playerFile.arquivo_id)) throw new Error('o contrato separa indevidamente identidade e slots de carta');
    const cpk = extractCpk(bytes);
    const packed = cpk[playerFile.arquivo];
    if (!packed) throw new Error(`${playerFile.arquivo} não foi encontrado na fonte do contrato`);
    const raw = await unpackWesys(packed);
    const decoded = await CONTRACT_READER.decodeFile(readingContract, playerFile.arquivo, raw, required);
    const slots = new Map();
    for (const record of decoded.records) {
      const cardId = String(record.values['carta.id']);
      const one = record.values['carta.impeto.slot1'];
      const two = record.values['carta.impeto.slot2'];
      const state = (field, rawCode) => {
        const transform = field.transformacao || {};
        const semantic = rawCode === 0 && transform.zero != null ? transform.zero : transform[String(rawCode)];
        if (semantic === 'sem') return { state: 'sem' };
        if (semantic === 'vaga') return { state: 'vaga' };
        return { state: 'preench', id: Number(rawCode) };
      };
      slots.set(cardId, { slot1: state(fields[1], one), slot2: state(fields[2], two), record_index: record.record_index });
    }
    return { selo: decoded.selo, arquivo: decoded.arquivo, sha256_arquivo: decoded.sha256_arquivo, slots };
  }

  async function extractCardAttributesByContract(bytes, readingContract) {
    const index = CONTRACT_READER.requirePlan(readingContract);
    const fields = [...index.fields.values()].filter((field) => field.chave_campo.startsWith('carta.atributo.'));
    const idField = index.fields.get('carta.id');
    if (!idField || fields.length !== 26) throw new Error('o contrato não contém os 26 atributos tipados');
    const file = index.files.get(idField.arquivo_id);
    if (!file || fields.some((field) => field.arquivo_id !== file.arquivo_id)) throw new Error('atributos e identidade não pertencem ao mesmo arquivo do contrato');
    const catalog = (readingContract.catalogos || []).find((item) => item.schema === 'clube_novo' && item.table === 'atributo_jogo');
    if (!catalog || !Array.isArray(catalog.rows)) throw new Error('o pedido não trouxe o catálogo atributo_jogo');
    const order = new Map(catalog.rows.map((row) => [row.codigo, row.idx_casa]));
    const ordered = fields.slice().sort((left, right) => Number(order.get(left.transformacao?.codigo_atributo)) - Number(order.get(right.transformacao?.codigo_atributo)));
    if (ordered.some((field, position) => order.get(field.transformacao?.codigo_atributo) !== position)) throw new Error('catálogo atributo_jogo não ordena os campos do contrato de 0 a 25');
    const cpk = extractCpk(bytes), packed = cpk[file.arquivo];
    if (!packed) throw new Error(`${file.arquivo} não foi encontrado na fonte do contrato`);
    const decoded = await CONTRACT_READER.decodeFile(readingContract, file.arquivo, await unpackWesys(packed), ['carta.id', ...ordered.map((field) => field.chave_campo)]);
    return new Map(decoded.records.map((record) => [String(record.values['carta.id']), ordered.map((field) => record.values[field.chave_campo])]));
  }

  async function extractCardRelationsByContract(bytes, readingContract) {
    const index = CONTRACT_READER.requirePlan(readingContract);
    const idField = index.fields.get('carta.id');
    const groups = { skills: 'carta.habilidade.', ai: 'carta.estilo_ia.', positions: 'carta.posicao.aptidao.' };
    const fields = Object.fromEntries(Object.entries(groups).map(([name, prefix]) => [name, [...index.fields.values()].filter((field) => field.chave_campo.startsWith(prefix))]));
    if (!idField || !fields.skills.length || !fields.ai.length || fields.positions.length !== 12) throw new Error('o contrato não contém todas as relações de carta');
    const file = index.files.get(idField.arquivo_id);
    if (!file || Object.values(fields).flat().some((field) => field.arquivo_id !== file.arquivo_id)) throw new Error('relações de carta em arquivo divergente do contrato');
    const catalog = (table) => (readingContract.catalogos || []).find((item) => item.schema === 'clube_novo' && item.table === table)?.rows;
    const skillNames = new Map((catalog('habilidade_jogo') || []).map((row) => [Number(row.skill_id), row.nome_en]));
    const aiNames = new Map((catalog('estilo_ia') || []).map((row) => [Number(row.bit), row.nome_en]));
    if (!skillNames.size || !aiNames.size) throw new Error('catálogos de habilidade/estilo IA ausentes do pedido');
    const skillMappings = (readingContract.mapeamentos_envelope || [])
      .filter((mapping) => mapping && mapping.status === 'comprovado' && mapping.grupo_repeticao === 'habilidades_player_bin');
    if (!skillMappings.length) throw new Error('pedido sem membros físicos comprovados de habilidades');
    const mappedSkillFields = skillMappings.map((mapping) => {
      const rule = mapping.regra_decomposicao || {};
      const match = /^skill_id=(\d+)$/.exec(String(rule.chave || ''));
      const skillId = match ? Number(match[1]) : NaN;
      const bit = Number(rule.bit);
      const width = Number(rule.largura);
      if (mapping.artefato_fisico !== 'cartas_fisicas' || mapping.coluna_fisica !== 'habilidades' ||
          rule.tipo !== 'lista_filtrada_bit' || !Number.isInteger(mapping.campo_id) ||
          !Number.isInteger(mapping.ordem_regra) || !Number.isInteger(skillId) ||
          !Number.isInteger(bit) || !Number.isInteger(width) || width <= 0) {
        throw new Error('membro de habilidade inválido no pedido de envelope');
      }
      const matches = fields.skills.filter((field) => Number(field.bit_inicio) === bit &&
        Number(field.largura_bits) === width && Number(field.transformacao?.skill_id) === skillId);
      if (matches.length !== 1) throw new Error(`mapeamento físico de habilidade sem campo único: campo_id ${mapping.campo_id}`);
      return { mapping, field: matches[0], skillId, bit, width };
    });
    if (mappedSkillFields.length !== fields.skills.length || new Set(mappedSkillFields.map((item) => item.field.chave_campo)).size !== fields.skills.length) {
      throw new Error('cobertura de membros físicos de habilidades incompleta ou duplicada');
    }
    const cpk = extractCpk(bytes), packed = cpk[file.arquivo];
    if (!packed) throw new Error(`${file.arquivo} não foi encontrado na fonte do contrato`);
    const selected = ['carta.id', ...Object.values(fields).flat().map((field) => field.chave_campo)];
    const decoded = await CONTRACT_READER.decodeFile(readingContract, file.arquivo, await unpackWesys(packed), selected);
    return new Map(decoded.records.map((record) => {
      const value = record.values;
      const skillFields = mappedSkillFields.filter((item) => value[item.field.chave_campo]);
      const aiFields = fields.ai.filter((field) => value[field.chave_campo]);
      const skills = skillFields.map((item) => skillNames.get(item.skillId));
      const habilidades_fisicas = skillFields.map((item) => ({
        campo_id: item.mapping.campo_id, skill_id: item.skillId,
        bit: item.bit, largura: item.width, ativo: true, ordem: item.mapping.ordem_regra,
        registro: record.record_index, arquivo: file.arquivo, hash: decoded.sha256_arquivo,
        procedencia: item.mapping.proveniencia
      }));
      const ai = aiFields.map((field) => aiNames.get(Number(field.transformacao?.bit_estilo_ia)));
      if (skills.some((name) => !name) || ai.some((name) => !name)) {
        throw new Error(`o catálogo do contrato não traduz todas as relações da carta ${value['carta.id']}`);
      }
      const aptitudes = Object.fromEntries(fields.positions.map((field) => [field.transformacao?.codigo_en, value[field.chave_campo]]));
      return [String(value['carta.id']), { skills, habilidades_fisicas, ai, aptitudes }];
    }));
  }

  async function extractCardBodiesByContract(bytes, readingContract) {
    const index = CONTRACT_READER.requirePlan(readingContract);
    const idField = index.fields.get('carta.corpo.card_id');
    const fields = [...index.fields.values()].filter((field) => field.chave_campo.startsWith('carta.corpo.pos.'));
    if (!idField || fields.length !== 11) throw new Error('o contrato não contém os 11 campos de aparência corporal');
    const file = index.files.get(idField.arquivo_id);
    if (!file || fields.some((field) => field.arquivo_id !== file.arquivo_id)) throw new Error('corpo em arquivo divergente do contrato');
    const ordered = fields.slice().sort((left, right) => Number(left.transformacao?.pos) - Number(right.transformacao?.pos));
    if (ordered.some((field, position) => Number(field.transformacao?.pos) !== position + 1)) throw new Error('o contrato não ordena o corpo de 1 a 11');
    const cpk = extractCpk(bytes), packed = cpk[file.arquivo];
    if (!packed) throw new Error(`${file.arquivo} não foi encontrado na fonte do contrato`);
    const decoded = await CONTRACT_READER.decodeFile(readingContract, file.arquivo, await unpackWesys(packed), ['carta.corpo.card_id', ...ordered.map((field) => field.chave_campo)]);
    return new Map(decoded.records.filter((record) => String(record.values['carta.corpo.card_id']) !== '0').map((record) => [
      String(record.values['carta.corpo.card_id']), ordered.map((field) => record.values[field.chave_campo])
    ]));
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
  function calculateOverall(attributes, position) {
    const weights = OVRW.weights[position];
    if (!weights) return null;
    let score = weights.b;
    for (let index = 0; index < weights.w.length; index += 1) {
      const value = attributes[index];
      if (value == null) return null;
      score += value * weights.w[index];
    }
    return Math.round(score);
  }
  function decodeCard(bytes, base) {
    const card = {};
    card.card_id = (BigInt(readBits(bytes, base, 64, 32)) | (BigInt(readBits(bytes, base, 96, 32)) << 32n)).toString();
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
    const nameStart = base + K.NAME_REGION_START + 3 * K.NAME_FIELD_STRIDE;
    let nameEnd = nameStart;
    while (nameEnd < nameStart + K.NAME_FIELD_STRIDE && bytes[nameEnd] !== 0) nameEnd += 1;
    card.name = TD.decode(bytes.slice(nameStart, nameEnd));
    return card;
  }
  function validCard(card) {
    const id = BigInt(card.card_id);
    return id !== 0n && id < (1n << 50n) && card.height >= 145 && card.height <= 210 && card.age >= 14 && card.age <= 47;
  }
  async function extractCardsFromCpk(bytes, readingContract, log = () => {}) {
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
    const rawPlayers = await unpackWesys(cpk['Player.bin']);
    if (rawPlayers.length % K.RECORD_SIZE !== 0) throw new Error(`Player.bin não é múltiplo do registro físico de ${K.RECORD_SIZE} bytes.`);
    const cards = [];
    for (let offset = 0; offset < rawPlayers.length; offset += K.RECORD_SIZE) {
      const card = decodeCard(rawPlayers, offset);
      if (!validCard(card)) continue;
      card.box = boxes[card.card_id] || null;
      cards.push(card);
    }
    const contractSlots = await extractCardSlotsByContract(bytes, readingContract);
    for (const card of cards) {
      const slot = contractSlots.slots.get(String(card.card_id));
      if (!slot) throw new Error(`o contrato não retornou slots para ${card.card_id}`);
      card.booster_primary = slot.slot1;
      card.booster_conditional = slot.slot2;
    }
    const [contractAttributes, contractRelations, contractBodies] = await Promise.all([
      extractCardAttributesByContract(bytes, readingContract),
      extractCardRelationsByContract(bytes, readingContract),
      extractCardBodiesByContract(bytes, readingContract)
    ]);
    for (const card of cards) {
      card.attrs = contractAttributes.get(String(card.card_id));
      if (!card.attrs) throw new Error(`o contrato não retornou atributos para ${card.card_id}`);
      const test = card.attrs.every((value) => value === 99);
      const base = BigInt(card.card_id) < (1n << 18n);
      card.tipo = test ? 'teste' : (base ? 'base' : 'colecionavel');
      card.roda_motor = !test && !base;
      card.overall = calculateOverall(card.attrs, card.position);
      const relations = contractRelations.get(String(card.card_id));
      if (!relations) throw new Error(`o contrato não retornou relações para ${card.card_id}`);
      card.skills = relations.skills;
      card.habilidades_fisicas = relations.habilidades_fisicas;
      card.ai_styles = relations.ai;
      card.aptitudes = relations.aptitudes;
      const body = contractBodies.get(String(card.card_id));
      if (!body) throw new Error(`o contrato não retornou corpo para ${card.card_id}`);
      card.corpo = [card.height, ...body];
    }
    log(`cartas válidas: ${cards.length}; slots lidos por ${contractSlots.selo.versao_contrato}`);
    return cards;
  }

  /**
   * Relê as quatro dimensões normalizadas das cartas sem alterar a carga
   * principal. A saída conserva o endereço físico e é comparada pelo executor
   * local, sempre em transação READ ONLY, com clube_novo.
   */
  async function extractCardDimensionsByFamily(sourceBytes, sourceDescriptors = {}, log = () => {}) {
    const required = ['dt870_updated', 'dt200', 'dt870_original', 'dt261_bra'];
    for (const role of required) if (!sourceBytes[role]) throw new Error(`Fonte obrigatória ausente para Dimensões: ${role}.`);
    const cpks = Object.fromEntries(required.map((role) => [role, extractCpk(sourceBytes[role])]));
    const unpackRequired = async (role, file) => {
      const entry = cpks[role][file];
      if (!entry) throw new Error(`${file} não foi encontrado em ${role}.`);
      return unpackWesys(entry);
    };
    const fileHashes = {};

    const countryByRole = {};
    for (const role of ['dt870_updated', 'dt200', 'dt870_original']) {
      const raw = await unpackRequired(role, 'Country.bin');
      if (raw.length % 1488 !== 0) throw new Error(`Country.bin de ${role} não usa registros de 1.488 bytes.`);
      countryByRole[role] = raw;
      fileHashes[`${role}:Country.bin`] = await sha256(raw);
    }
    if (new Set(Object.values(fileHashes).filter((_, index) => index < 3)).size !== 1) {
      throw new Error('Country.bin não é byte-idêntico nas três fontes; a compatibilidade compartilhada foi bloqueada.');
    }
    const country = countryByRole.dt870_updated;
    const nationalities = [];
    const nationalityByCode = new Map();
    for (let offset = 0, recordIndex = 0; offset < country.length; offset += 1488, recordIndex += 1) {
      const codigo = readBits(country, offset, 10, 9);
      const record = {
        id: String(codigo), codigo_jogo: codigo,
        nome_pt_br: fixedNullUtf8(country, offset + 788, 70),
        sigla: fixedNullUtf8(country, offset + 708, 10),
        source_role: 'dt870_updated', arquivo: 'Country.bin', record_index: recordIndex,
        record_size: 1488, codigo_bit: 10, codigo_largura: 9,
        nome_offset: 788, nome_largura: 70, sigla_offset: 708, sigla_largura: 10,
        source_file_sha256: fileHashes['dt870_updated:Country.bin'],
        presente_dt870_atualizacao: true, presente_dt200: true, presente_dt870_original: true
      };
      if (!record.nome_pt_br || !record.sigla || nationalityByCode.has(codigo)) throw new Error(`Country.bin inválido no registro ${recordIndex}.`);
      record.fingerprint = stableJson(record);
      nationalities.push(record);
      nationalityByCode.set(codigo, record);
    }

    const teamSources = {};
    const teamPresence = new Map();
    for (const role of ['dt870_updated', 'dt200', 'dt870_original']) {
      const raw = await unpackRequired(role, 'Team.bin');
      if (raw.length % 1600 !== 0) throw new Error(`Team.bin de ${role} não usa registros de 1.600 bytes.`);
      fileHashes[`${role}:Team.bin`] = await sha256(raw);
      const records = new Map();
      for (let offset = 0, recordIndex = 0; offset < raw.length; offset += 1600, recordIndex += 1) {
        const codigo = u32(raw, offset + 12);
        if (records.has(codigo)) throw new Error(`Team.bin de ${role} duplicou o código ${codigo}.`);
        records.set(codigo, {
          codigo_jogo: codigo,
          nome_pt_br: fixedNullUtf8(raw, offset + 746, 70) || null,
          nome_en: fixedNullUtf8(raw, offset + 396, 70) || null,
          sigla: fixedNullUtf8(raw, offset + 886, 10) || null,
          source_role: role, record_index: recordIndex,
          source_file_sha256: fileHashes[`${role}:Team.bin`]
        });
        if (!teamPresence.has(codigo)) teamPresence.set(codigo, new Set());
        teamPresence.get(codigo).add(role);
      }
      teamSources[role] = records;
    }
    const actualTeamCodes = new Set(teamPresence.keys());

    const competitionUnitSources = {};
    const leaguePresence = new Map();
    for (const role of ['dt870_updated', 'dt200', 'dt870_original']) {
      const raw = await unpackRequired(role, 'CompetitionUnit.bin');
      if (raw.length % 2472 !== 0) throw new Error(`CompetitionUnit.bin de ${role} não usa registros de 2.472 bytes.`);
      fileHashes[`${role}:CompetitionUnit.bin`] = await sha256(raw);
      const records = new Map();
      for (let offset = 0, recordIndex = 0; offset < raw.length; offset += 2472, recordIndex += 1) {
        const codigo = u16(raw, offset + 10);
        if (records.has(codigo)) throw new Error(`CompetitionUnit.bin de ${role} duplicou o código ${codigo}.`);
        const rawParent = u16(raw, offset + 2);
        records.set(codigo, {
          codigo_jogo: codigo, codigo_pai: rawParent === 0xffff ? null : rawParent,
          nome_pt_br: fixedNullUtf8(raw, offset + 1091, 115) || null,
          nome_en: fixedNullUtf8(raw, offset + 1781, 115) || null,
          source_role: role, record_index: recordIndex,
          source_file_sha256: fileHashes[`${role}:CompetitionUnit.bin`]
        });
        if (!leaguePresence.has(codigo)) leaguePresence.set(codigo, new Set());
        leaguePresence.get(codigo).add(role);
      }
      competitionUnitSources[role] = records;
    }
    const leagues = [...leaguePresence.keys()].sort((left, right) => left - right).map((codigo) => {
      const sourceRole = ['dt870_updated', 'dt200', 'dt870_original'].find((role) => competitionUnitSources[role].has(codigo));
      const source = competitionUnitSources[sourceRole].get(codigo);
      const presence = leaguePresence.get(codigo);
      const record = {
        id: String(codigo), codigo_jogo: codigo, codigo_pai: source.codigo_pai,
        nome_pt_br: source.nome_pt_br, nome_en: source.nome_en,
        source_role: sourceRole, arquivo: 'CompetitionUnit.bin', record_index: source.record_index,
        record_size: 2472, codigo_offset: 10, codigo_largura: 2,
        codigo_pai_offset: 2, codigo_pai_largura: 2,
        nome_pt_br_offset: 1091, nome_pt_br_largura: 115,
        nome_en_offset: 1781, nome_en_largura: 115,
        source_file_sha256: source.source_file_sha256,
        presente_dt870_atualizacao: presence.has('dt870_updated'),
        presente_dt200: presence.has('dt200'), presente_dt870_original: presence.has('dt870_original')
      };
      record.fingerprint = stableJson(record);
      return record;
    });
    const leagueCodes = new Set(leagues.map((record) => record.codigo_jogo));

    const leagueByTeam = new Map();
    const competitionEntryDetails = {};
    for (const role of ['dt870_updated', 'dt200', 'dt870_original']) {
      const raw = await unpackRequired(role, 'CompetitionEntry.bin');
      if (raw.length % 12 !== 0) throw new Error(`CompetitionEntry.bin de ${role} não usa registros de 12 bytes.`);
      fileHashes[`${role}:CompetitionEntry.bin`] = await sha256(raw);
      competitionEntryDetails[role] = { records: raw.length / 12, source_file_sha256: fileHashes[`${role}:CompetitionEntry.bin`] };
      for (let offset = 0, recordIndex = 0; offset < raw.length; offset += 12, recordIndex += 1) {
        const teamCode = u32(raw, offset);
        const leagueCode = u32(raw, offset + 4) >>> 16;
        if (!teamCode || !leagueCodes.has(leagueCode) || leagueByTeam.has(teamCode)) continue;
        leagueByTeam.set(teamCode, { codigo_liga: leagueCode, source_role: role, record_index: recordIndex });
      }
    }

    const rawPlayers = await unpackRequired('dt870_updated', 'Player.bin');
    if (rawPlayers.length % K.RECORD_SIZE !== 0) throw new Error(`Player.bin atual não usa registros de ${K.RECORD_SIZE} bytes.`);
    fileHashes['dt870_updated:Player.bin'] = await sha256(rawPlayers);
    const rawDeleteList = await unpackRequired('dt870_updated', 'PlayerDeleteList.bin');
    if (rawDeleteList.length % 8 !== 0) throw new Error('PlayerDeleteList.bin atual não usa registros de 8 bytes.');
    fileHashes['dt870_updated:PlayerDeleteList.bin'] = await sha256(rawDeleteList);
    const deletedCardIds = new Set();
    for (let offset = 0; offset < rawDeleteList.length; offset += 8) deletedCardIds.add(u64String(rawDeleteList, offset));

    const physicalCards = [];
    const firstCardByRawTeam = new Map();
    for (let offset = 0, recordIndex = 0; offset < rawPlayers.length; offset += K.RECORD_SIZE, recordIndex += 1) {
      const decoded = decodeCard(rawPlayers, offset);
      if (!validCard(decoded)) continue;
      const cardId = BigInt(decoded.card_id);
      const rawTeamCode = u32(rawPlayers, offset + 16);
      if (rawTeamCode && !firstCardByRawTeam.has(rawTeamCode)) firstCardByRawTeam.set(rawTeamCode, recordIndex);
      physicalCards.push({
        card_id: decoded.card_id, registro_vinculos_jogo: recordIndex,
        codigo_nacionalidade_player_raw: readBits(rawPlayers, offset, 328, 10),
        codigo_clube_player_raw: rawTeamCode,
        codigo_tipo_carta_fisico: Number((cardId >> 44n) & 0xfn),
        marcador_subtipo_tipo_carta: readBits(rawPlayers, offset, 104, 1),
        jogador_indisponivel: deletedCardIds.has(decoded.card_id)
      });
    }

    const clubs = [...actualTeamCodes].sort((left, right) => left - right).map((codigo) => {
      const sourceRole = ['dt870_updated', 'dt200', 'dt870_original'].find((role) => teamSources[role].has(codigo));
      const source = teamSources[sourceRole].get(codigo);
      const presence = teamPresence.get(codigo);
      const record = {
        id: String(codigo), codigo_jogo: codigo,
        nome_pt_br: source.nome_pt_br, nome_en: source.nome_en, sigla: source.sigla,
        source_role: sourceRole, arquivo: 'Team.bin', record_index: source.record_index,
        registro_primeira_carta: null, record_size: 1600,
        codigo_offset: 12, codigo_largura: 4,
        nome_pt_br_offset: 746, nome_pt_br_largura: 70,
        nome_en_offset: 396, nome_en_largura: 70,
        sigla_offset: 886, sigla_largura: 10,
        source_file_sha256: source.source_file_sha256,
        presente_dt870_atualizacao: presence.has('dt870_updated'),
        presente_dt200: presence.has('dt200'), presente_dt870_original: presence.has('dt870_original'),
        pode_rodar: Boolean(source.nome_pt_br || source.nome_en), falta_o_que: null
      };
      record.fingerprint = stableJson(record);
      return record;
    });
    for (const codigo of [...firstCardByRawTeam.keys()].filter((value) => !actualTeamCodes.has(value)).sort((left, right) => left - right)) {
      const record = {
        id: String(codigo), codigo_jogo: codigo, nome_pt_br: null, nome_en: null, sigla: null,
        source_role: 'dt870_atualizacao:Player.bin_codigo_sem_catalogo', arquivo: 'Player.bin', record_index: null,
        registro_primeira_carta: firstCardByRawTeam.get(codigo), record_size: K.RECORD_SIZE,
        codigo_offset: 16, codigo_largura: 4,
        nome_pt_br_offset: null, nome_pt_br_largura: null,
        nome_en_offset: null, nome_en_largura: null, sigla_offset: null, sigla_largura: null,
        source_file_sha256: fileHashes['dt870_updated:Player.bin'],
        presente_dt870_atualizacao: false, presente_dt200: false, presente_dt870_original: false,
        pode_rodar: false,
        falta_o_que: 'código presente em Player.bin, mas ausente nos Team.bin DT870 atualização/original e DT200'
      };
      record.fingerprint = stableJson(record);
      clubs.push(record);
    }
    clubs.sort((left, right) => left.codigo_jogo - right.codigo_jogo);
    const clubByCode = new Map(clubs.map((record) => [record.codigo_jogo, record]));

    const textCatalog = await extractTextCatalogFromCpk(sourceBytes.dt261_bra);
    const textByKey = new Map(textCatalog.records.map((record) => [record.id, record]));
    const types = CARD_DIMENSION_TYPES.map((definition) => {
      const official = definition.chave_texto ? textByKey.get(definition.chave_texto) : null;
      if (definition.chave_texto && (!official || official.texto !== definition.nome_exibicao)) {
        throw new Error(`O rótulo oficial ${definition.chave_texto} não confere com ${definition.nome_exibicao}.`);
      }
      const record = {
        id: definition.tipo_carta_id, ...definition,
        secao_texto: official ? official.secao : null,
        id_texto: official ? official.id_texto : null,
        nome_pt_br: official ? official.texto : null,
        arquivo_texto: official ? official.arquivo : null,
        cpk_texto: official ? official.cpk : null,
        entrada_texto: official ? official.entrada_idx : null,
        entrada_offset: official ? official.entrada_offset : null,
        texto_offset: official ? official.texto_offset : null,
        tamanho_armazenado: official ? official.tamanho_armazenado : null,
        hash_all_str: official ? official.fonte_arquivo_sha256 : null
      };
      record.fingerprint = stableJson(record);
      return record;
    });
    const typeByPhysicalState = new Map(types.filter((record) => !record.usa_player_delete_list).map((record) => [`${record.codigo_tipo_fisico}/${record.marcador_subtipo}`, record]));

    const cards = physicalCards.map((physical) => {
      const codigoNacionalidade = Math.floor(physical.codigo_nacionalidade_player_raw / 2);
      const club = physical.codigo_clube_player_raw ? clubByCode.get(physical.codigo_clube_player_raw) : null;
      const clubResolved = Boolean(club && club.pode_rodar);
      const league = club ? leagueByTeam.get(physical.codigo_clube_player_raw) : null;
      const type = physical.jogador_indisponivel
        ? types.find((record) => record.usa_player_delete_list)
        : typeByPhysicalState.get(`${physical.codigo_tipo_carta_fisico}/${physical.marcador_subtipo_tipo_carta}`);
      if (!nationalityByCode.has(codigoNacionalidade)) throw new Error(`Carta ${physical.card_id} referencia nacionalidade ausente: ${codigoNacionalidade}.`);
      if (!type) throw new Error(`Carta ${physical.card_id} possui estado de tipo não mapeado: ${physical.codigo_tipo_carta_fisico}/${physical.marcador_subtipo_tipo_carta}.`);
      return {
        card_id: physical.card_id,
        registro_vinculos_jogo: physical.registro_vinculos_jogo,
        codigo_nacionalidade_player_raw: physical.codigo_nacionalidade_player_raw,
        codigo_nacionalidade: codigoNacionalidade,
        codigo_clube_player_raw: physical.codigo_clube_player_raw,
        codigo_clube: club ? physical.codigo_clube_player_raw : null,
        codigo_liga: league ? league.codigo_liga : null,
        codigo_tipo_carta_fisico: physical.codigo_tipo_carta_fisico,
        marcador_subtipo_tipo_carta: physical.marcador_subtipo_tipo_carta,
        jogador_indisponivel: physical.jogador_indisponivel,
        tipo_carta_id: type.tipo_carta_id,
        chave_tipo_carta: type.chave_texto,
        pode_rodar_vinculos: !physical.codigo_clube_player_raw || clubResolved,
        falta_o_que_vinculos: physical.codigo_clube_player_raw && !clubResolved ? 'codigo_clube sem definicao em Team.bin dos tres CPKs' : null
      };
    });
    const typeCounts = {};
    for (const card of cards) typeCounts[card.tipo_carta_id] = (typeCounts[card.tipo_carta_id] || 0) + 1;

    const snapshot = {
      contract: CARD_DIMENSIONS_CONTRACT_VERSION,
      database_write: false,
      source_policy: 'DT870 atualizado por carta; catálogos em união DT870 atualizado > DT200 > DT870 original; textos somente all.str pt-BR',
      sources: sourceDescriptors,
      source_files: fileHashes,
      physical_contract: {
        player: { arquivo: 'Player.bin', record_size: K.RECORD_SIZE, card_id_offset: 8, clube_offset: 16, nacionalidade_bit: 328, nacionalidade_largura: 10, nacionalidade_transformacao: 'floor(raw/2)', tipo: 'card_id bits 44-47', subtipo_bit: 104, subtipo_largura: 1 },
        delete_list: { arquivo: 'PlayerDeleteList.bin', record_size: 8, card_id_offset: 0 },
        country: { arquivo: 'Country.bin', record_size: 1488 },
        club: { arquivo: 'Team.bin', record_size: 1600 },
        league: { arquivo: 'CompetitionUnit.bin + CompetitionEntry.bin', unit_record_size: 2472, entry_record_size: 12 }
      },
      counts: {
        cards: cards.length, nationalities: nationalities.length, clubs: clubs.length, leagues: leagues.length, types: types.length,
        deleted_cards: cards.filter((card) => card.jogador_indisponivel).length,
        cards_with_club: cards.filter((card) => card.codigo_clube !== null).length,
        cards_with_league: cards.filter((card) => card.codigo_liga !== null).length,
        provisional_cards: cards.filter((card) => card.tipo_carta_id === 'player_type_4_subtype_0' || card.tipo_carta_id === 'player_type_7_subtype_0').length,
        blocked_cards: cards.filter((card) => !card.pode_rodar_vinculos).length,
        type_distribution: typeCounts
      },
      catalogs: { nationalities, clubs, leagues, types },
      cards,
      competition_entry_sources: competitionEntryDetails
    };
    log(`Dimensões físicas: ${cards.length} cartas · ${nationalities.length} países · ${clubs.length} clubes · ${leagues.length} ligas · ${types.length} tipos`);
    return snapshot;
  }

  function validateCardDimensionsSnapshot(snapshot) {
    if (!snapshot || snapshot.contract !== CARD_DIMENSIONS_CONTRACT_VERSION) throw new Error('Contrato físico de Dimensões incompatível.');
    const cards = snapshot.cards;
    const catalogs = snapshot.catalogs || {};
    if (!Array.isArray(cards) || !cards.length) throw new Error('A fotografia de Dimensões não contém cartas.');
    for (const name of ['nationalities', 'clubs', 'leagues', 'types']) if (!Array.isArray(catalogs[name]) || !catalogs[name].length) throw new Error(`Catálogo físico ausente: ${name}.`);
    const ids = new Set(cards.map((card) => String(card.card_id)));
    if (ids.size !== cards.length) throw new Error('A fotografia de Dimensões contém card_id duplicado.');
    const nationalityIds = new Set(catalogs.nationalities.map((record) => Number(record.codigo_jogo)));
    const clubIds = new Set(catalogs.clubs.map((record) => Number(record.codigo_jogo)));
    const leagueIds = new Set(catalogs.leagues.map((record) => Number(record.codigo_jogo)));
    const typeIds = new Set(catalogs.types.map((record) => record.tipo_carta_id));
    const invalid = cards.filter((card) => !nationalityIds.has(card.codigo_nacionalidade)
      || (card.codigo_clube !== null && !clubIds.has(card.codigo_clube))
      || (card.codigo_liga !== null && !leagueIds.has(card.codigo_liga))
      || !typeIds.has(card.tipo_carta_id));
    if (invalid.length) throw new Error(`A fotografia de Dimensões contém ${invalid.length} vínculo(s) órfão(s).`);
    const provisional = cards.filter((card) => card.tipo_carta_id === 'player_type_4_subtype_0' || card.tipo_carta_id === 'player_type_7_subtype_0');
    if (provisional.some((card) => card.chave_tipo_carta !== null)) throw new Error('Tipo provisório recebeu chave oficial indevida.');
    return {
      contract: CARD_DIMENSIONS_CONTRACT_VERSION,
      passed: true,
      cards: cards.length,
      unique_card_ids: ids.size,
      counts: snapshot.counts,
      orphan_count: 0,
      database_write: false
    };
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
      atributos: JSON.stringify(card.attrs),
      habilidades: JSON.stringify(card.skills || []),
      aptidoes: JSON.stringify(card.aptitudes || {}),
      estilos_ia: JSON.stringify(card.ai_styles || []),
      corpo: card.corpo ? JSON.stringify(card.corpo) : ''
    };
    return row;
  }

  /**
   * Contrato físico das cinco relações normalizadas que pertencem a esta frente.
   *
   * As chaves canônicas finais (codigo_atributo, codigo_corpo, skill_id e os IDs
   * de catálogo) são resolvidas pelo executor local em leitura contra clube_novo.
   * O núcleo entrega somente evidência obtida do Player.bin/PlayerAppearance.bin;
   * não infere nomes, IDs de banco ou dados de outras famílias.
   */
  function cardRelationSource(card) {
    return {
      contract: CARD_RELATIONS_CONTRACT_VERSION,
      card_id: String(card.card_id),
      atributos: (card.attrs || []).map((value, index) => ({ index, value })),
      corpo: (card.corpo || []).map((value, index) => ({ index, value })),
      habilidades: (card.skills || []).map((nome_en, ordem) => ({ nome_en, ordem })),
      estilos_ia: (card.ai_styles || []).map((nome_en) => ({ nome_en })),
      posicoes: Object.entries(card.aptitudes || {}).map(([codigo_en, nivel_aptidao]) => ({ codigo_en, nivel_aptidao }))
    };
  }

  function validateCardRelationSources(cards) {
    const counts = { atributos: 0, corpo: 0, habilidades: 0, estilos_ia: 0, posicoes: 0 };
    const invalid = [];
    const seen = new Set();
    for (const card of cards) {
      const source = cardRelationSource(card);
      if (seen.has(source.card_id)) invalid.push({ card_id: source.card_id, reason: 'card_id duplicado' });
      seen.add(source.card_id);
      counts.atributos += source.atributos.length;
      counts.corpo += source.corpo.length;
      counts.habilidades += source.habilidades.length;
      counts.estilos_ia += source.estilos_ia.length;
      counts.posicoes += source.posicoes.length;
      if (source.atributos.length !== 26) invalid.push({ card_id: source.card_id, relation: 'atributos', found: source.atributos.length, expected: 26 });
      if (source.corpo.length !== 12) invalid.push({ card_id: source.card_id, relation: 'corpo', found: source.corpo.length, expected: 12 });
      if (source.posicoes.length !== 12) invalid.push({ card_id: source.card_id, relation: 'posicoes', found: source.posicoes.length, expected: 12 });
      if (source.atributos.some((item) => !Number.isInteger(item.value) || item.value < 40 || item.value > 99)) invalid.push({ card_id: source.card_id, relation: 'atributos', reason: 'valor fora de 40..99' });
      if (source.posicoes.some((item) => !Number.isInteger(item.nivel_aptidao) || item.nivel_aptidao < 0 || item.nivel_aptidao > 2)) invalid.push({ card_id: source.card_id, relation: 'posicoes', reason: 'nível fora de 0..2' });
      if (new Set(source.habilidades.map((item) => item.nome_en)).size !== source.habilidades.length) invalid.push({ card_id: source.card_id, relation: 'habilidades', reason: 'habilidade duplicada' });
      if (new Set(source.estilos_ia.map((item) => item.nome_en)).size !== source.estilos_ia.length) invalid.push({ card_id: source.card_id, relation: 'estilos_ia', reason: 'estilo duplicado' });
    }
    return {
      contract: CARD_RELATIONS_CONTRACT_VERSION,
      cards: cards.length,
      unique_card_ids: seen.size,
      counts,
      invalid_count: invalid.length,
      invalid: invalid.slice(0, 100),
      database_write: false,
      excluded_relations: ['carta_impeto_jogo', 'dimensoes_de_carta']
    };
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
      if (coach.length % 176 !== 0) {
        throw new Error('Coach.bin do DT870 atualizado não respeita o layout de registros declarado.');
      }
      if (country.length % 1488 !== 0) {
        throw new Error('Country.bin do DT870 atualizado não respeita o layout de registros declarado.');
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
      const recordBytes = raw.subarray(offset, offset + spec.record_size);
      records.push({
        id: String(spec.id(raw, offset)),
        raw_hex: bytesToHex(recordBytes),
        record_sha256: await sha256(recordBytes),
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
    if (coach.length % 176 !== 0) throw new Error('Coach.bin atual não respeita o layout declarado.');
    if (country.length % 1488 !== 0) throw new Error('Country.bin atual não respeita o layout declarado.');
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
      decode: (buffer, offset) => {
        const fieldMap = [
          [0,0,144,'PB:498:6'],[1,17,261,'PB:390:6'],[2,21,192,'PB:472:6'],[3,2,239,'PB:492:6'],
          [4,1,276,'PB:396:6'],[5,3,271,'PB:550:6'],[6,6,244,'PB:530:6'],[7,4,122,'PB:524:6'],
          [8,5,229,'PB:448:6'],[9,7,281,'PB:402:6'],[10,18,234,'PB:454:6'],[11,19,170,'PB:512:6'],
          [12,20,266,'PB:544:6'],[13,8,154,'PB:368:6'],[14,9,185,'PB:428:6'],[15,22,165,'PB:416:6'],
          [16,23,197,'PB:466:6'],[17,24,256,'PB:460:6'],[18,25,224,'PB:422:6'],[19,10,180,'PB:434:6'],
          [20,14,175,'PB:518:6'],[21,15,149,'PB:504:6'],[22,12,249,'PB:384:6'],[23,11,217,'PB:486:6'],
          [24,13,160,'PB:408:6'],[25,16,202,'PB:480:6']
        ];
        const typeRaw = readBits(buffer, offset, 296, 3);
        const classOwner = readBits(buffer, offset, 302, 3);
        const nationality = readBits(buffer, offset, 128, 9);
        const league = readBits(buffer, offset, 96, 16);
        const team = readBits(buffer, offset, 32, 18);
        let criterion = 'sempre_ativo';
        let targetKind = null;
        let targetCode = null;
        if (typeRaw === 1) criterion = 'avaliacao_ao_vivo';
        if (typeRaw === 2) {
          if (classOwner > 0) { criterion = 'quantidade_jogadores_classe_impeto'; targetKind = 'classe_impeto'; targetCode = classOwner; }
          else if (nationality > 0) { criterion = 'quantidade_jogadores_nacionalidade_regiao'; targetKind = 'nacionalidade_regiao'; targetCode = nationality; }
          else if (league !== 0 && league !== 0xffff) { criterion = 'quantidade_jogadores_liga_categoria'; targetKind = 'liga_categoria'; targetCode = league; }
          else { criterion = 'quantidade_jogadores_clube_equipe'; targetKind = 'clube_equipe'; targetCode = team || null; }
        }
        const cutoffRaw = readBits(buffer, offset, 207, 5);
        const level = readBits(buffer, offset, 212, 5);
        const cutoff = cutoffRaw + 2;
        const ranges = [];
        if (typeRaw === 2 && level > 0) {
          let start = 1, previous = null;
          for (let quantity = 1; quantity <= 23; quantity += 1) {
            const delta = Math.min(level, Math.max(1, Math.floor(level * quantity / cutoff)));
            if (previous !== null && delta !== previous) { ranges.push({ quantidade_minima: start, quantidade_maxima: quantity - 1, delta: previous }); start = quantity; }
            previous = delta;
          }
          ranges.push({ quantidade_minima: start, quantidade_maxima: 23, delta: previous });
        }
        return ({
        tipo_condicao_raw: typeRaw,
        tipo_condicao_espelho_u32: u32(buffer, offset + 8),
        tipo_bit: 296,
        tipo_largura: 3,
        tipo_espelho_bit: 64,
        tipo_espelho_largura: 32,
        criterio_codigo: criterion,
        alvo_tipo: targetKind,
        alvo_codigo: targetCode,
        alvo_nacionalidade_raw: nationality,
        alvo_liga_raw: league,
        alvo_clube_raw: team,
        classe_candidato: readBits(buffer, offset, 299, 3),
        classe_dono: classOwner,
        corte_raw: cutoffRaw,
        corte: cutoff,
        efeito_maximo: level,
        faixas: ranges,
        efeitos: fieldMap.map(([slotRuntime,parametroUi,bit,codigoAtributo]) => ({
          slot_runtime: slotRuntime, parametro_ui: parametroUi, codigo_atributo: codigoAtributo,
          bit_delta: bit, largura_delta: 5, delta: readBits(buffer, offset, bit, 5)
        })).filter((effect) => effect.delta > 0)
      }); }
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
          record_sha256: record.record_sha256 || null,
          tipo_condicao_raw: record.tipo_condicao_raw ?? null,
          tipo_condicao_espelho_u32: record.tipo_condicao_espelho_u32 ?? null,
          tipo_bit: record.tipo_bit ?? null,
          tipo_largura: record.tipo_largura ?? null,
          tipo_espelho_bit: record.tipo_espelho_bit ?? null,
          tipo_espelho_largura: record.tipo_espelho_largura ?? null
          ,criterio_codigo: record.criterio_codigo ?? null
          ,alvo_tipo: record.alvo_tipo ?? null
          ,alvo_codigo: record.alvo_codigo ?? null
          ,classe_candidato: record.classe_candidato ?? null
          ,classe_dono: record.classe_dono ?? null
          ,corte_raw: record.corte_raw ?? null
          ,corte: record.corte ?? null
          ,efeito_maximo: record.efeito_maximo ?? null
          ,faixas: record.faixas || []
          ,efeitos: record.efeitos || []
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
          criterio_codigo: preferred.criterio_codigo ?? null,
          alvo_tipo: preferred.alvo_tipo ?? null,
          alvo_codigo: preferred.alvo_codigo ?? null,
          classe_candidato: preferred.classe_candidato ?? null,
          classe_dono: preferred.classe_dono ?? null,
          corte_raw: preferred.corte_raw ?? null,
          corte: preferred.corte ?? null,
          efeito_maximo: preferred.efeito_maximo ?? null,
          faixas: preferred.faixas || [],
          efeitos: preferred.efeitos || [],
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
    const competitionUnitRaw = await unpackWesys(cpks.dt870_updated['CompetitionUnit.bin']);
    if (competitionUnitRaw.length % 2472 !== 0) throw new Error('CompetitionUnit.bin não é múltiplo de 2472 bytes.');
    const competitionUnitSha256 = await sha256(competitionUnitRaw);
    impetos.liga_membros = [];
    for (let index = 0; index < competitionUnitRaw.length / 2472; index += 1) {
      const offset = index * 2472;
      const competitionRecordSha256 = await sha256(competitionUnitRaw.subarray(offset, offset + 2472));
      const codigo = u16(competitionUnitRaw, offset + 10);
      const anterior = u16(competitionUnitRaw, offset + 4);
      const posterior = u16(competitionUnitRaw, offset + 6);
      const provenance = { source_file_sha256: competitionUnitSha256, record_sha256: competitionRecordSha256 };
      if (anterior && anterior !== 0xffff) impetos.liga_membros.push({ codigo_liga_alvo_base: codigo, codigo_liga_membro: anterior, ordem_fisica: 1, papel_fisico: 'vinculo_anterior', record_index: index, bit_inicial: 32, largura: 16, ...provenance });
      impetos.liga_membros.push({ codigo_liga_alvo_base: codigo, codigo_liga_membro: codigo, ordem_fisica: anterior && anterior !== 0xffff ? 2 : 1, papel_fisico: 'alvo_base', record_index: index, bit_inicial: 80, largura: 16, ...provenance });
      if (posterior && posterior !== 0xffff) impetos.liga_membros.push({ codigo_liga_alvo_base: codigo, codigo_liga_membro: posterior, ordem_fisica: (anterior && anterior !== 0xffff ? 3 : 2), papel_fisico: 'vinculo_posterior', record_index: index, bit_inicial: 48, largura: 16, ...provenance });
    }
    impetos.contract = 'clubef-impetos-physical-v1';
    impetos.field_contract = {
      codigo: { bit: 112, largura: 10 }, tipo: { bit: 296, largura: 3 }, nacionalidade: { bit: 128, largura: 9 },
      liga: { bit: 96, largura: 16 }, clube: { bit: 32, largura: 18 }, classe_candidato: { bit: 299, largura: 3 },
      classe_dono: { bit: 302, largura: 3 }, corte: { bit: 207, largura: 5, transformacao: 'raw + 2' },
      efeito_maximo: { bit: 212, largura: 5 }, faixas: { rotina: '0x144A47800', formula: 'min(nivel,max(1,floor(nivel*n/corte)))' },
      liga_membros: { arquivo: 'CompetitionUnit.bin', tamanho_registro: 2472, arquivo_sha256: competitionUnitSha256, anterior: 'bit32/w16', posterior: 'bit48/w16', rotina: '0x144A52D40' }
    };

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
      efeitos_de_impeto: { supported: true, file: 'PlayerBooster.bin', contract: 'clubef-impetos-physical-v1', records: impetos.records.flatMap((record) => (record.efeitos || []).map((effect) => ({ codigo_impeto: record.id, ...effect }))), duplicate_ids: [] },
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
    CARD_RELATIONS_CONTRACT_VERSION,
    CARD_DIMENSIONS_CONTRACT_VERSION,
    CARD_COLUMNS,
    STRUCTURED_COLUMNS,
    stableJson,
    sha256,
    parseCsv,
    validateSchema,
    cardToRow,
    cardRelationSource,
    validateCardRelationSources,
    extractCardDimensionsByFamily,
    validateCardDimensionsSnapshot,
    rowsToCsv,
    cardsToCsv,
    duplicateIds,
    missingCounts,
    validateCards,
    compareCardRows,
    extractCardsFromCpk,
    extractCardAttributesByContract,
    extractCardRelationsByContract,
    extractCardBodiesByContract,
    validateSourceForRole,
    validateSourceByContract,
    extractCardSlotsByContract,
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
