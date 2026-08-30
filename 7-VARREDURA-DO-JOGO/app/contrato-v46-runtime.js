'use strict';

/**
 * Runtime V4.6.
 * Preserva a lógica do Extrator e troca somente a origem das referências
 * físicas: tabela/catálogo de clube_novo + contrato ativo.
 */
(function installV46ContractRuntime(global) {
  const core = global.CLUBEF_CORE;
  const reader = global.CLUBEF_CONTRACT_READER;
  if (!core || !reader) throw new Error('runtime V4.6 requer leitura-contrato.js e extrator-core.js');

  let activePlan = null;
  const precedenceBaseLabelCache = new WeakMap();
  const TD = new TextDecoder('utf-8');
  const u32 = (bytes, offset) => (bytes[offset] | (bytes[offset + 1] << 8) | (bytes[offset + 2] << 16) | (bytes[offset + 3] << 24)) >>> 0;
  const u32be = (bytes, offset) => ((bytes[offset] << 24) | (bytes[offset + 1] << 16) | (bytes[offset + 2] << 8) | bytes[offset + 3]) >>> 0;
  const u16be = (bytes, offset) => ((bytes[offset] << 8) | bytes[offset + 1]) >>> 0;

  function rememberPlan(plan) {
    reader.requirePlan(plan);
    activePlan = plan;
    return plan;
  }
  function planNow() {
    if (!activePlan) throw new Error('contrato de leitura ainda não foi recebido pelo runtime V4.6');
    return activePlan;
  }
  function catalogRows(plan, table) {
    return (plan.catalogos || []).find((item) => item.schema === 'clube_novo' && item.table === table)?.rows || [];
  }
  function requireCatalog(plan, table) {
    const rows = catalogRows(plan, table);
    if (!rows.length) throw new Error(`catálogo obrigatório ausente no pedido: clube_novo.${table}`);
    return rows;
  }
  function field(plan, key) {
    const found = reader.requirePlan(plan).fields.get(key);
    if (!found) throw new Error(`campo obrigatório ausente no contrato: ${key}`);
    return found;
  }
  function family(plan, key) {
    const item = (plan.familias || []).find((candidate) => candidate && candidate.chave_familia === key);
    if (!item) throw new Error(`família ausente do contrato: ${key}`);
    if (!Array.isArray(item.papeis_fonte) || !item.papeis_fonte.length) throw new Error(`família sem fontes no contrato: ${key}`);
    return item;
  }
  function familyRoles(plan, key) { return [...family(plan, key).papeis_fonte]; }
  function fileById(plan, arquivoId) {
    const found = (plan.arquivos || []).find((item) => item.arquivo_id === arquivoId);
    if (!found) throw new Error(`arquivo ${arquivoId} ausente no contrato`);
    return found;
  }
  function fixed(bytes, start, width) {
    let end = start;
    while (end < start + width && bytes[end] !== 0) end += 1;
    return TD.decode(bytes.subarray(start, end));
  }
  function template(rows, predicate, label) {
    const row = rows.find(predicate) || rows[0];
    if (!row) throw new Error(`sem referência física para ${label}`);
    return row;
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
      if (type === 0 || type === 1) return [bytes[offset], 1];
      if (type === 2 || type === 3) return [u16be(bytes, offset), 2];
      if (type === 4 || type === 5) return [u32be(bytes, offset), 4];
      if (type === 6 || type === 7) return [u32be(bytes, offset) * 4294967296 + u32be(bytes, offset + 4), 8];
      if (type === 8) return [0, 4];
      if (type === 0xA) return [readString(u32be(bytes, offset)), 4];
      if (type === 0xB) return [[u32be(bytes, offset), u32be(bytes, offset + 4)], 8];
      throw new Error(`tipo @UTF não suportado: ${type}`);
    };
    let pointer = 24;
    const columns = [];
    for (let index = 0; index < columnCount; index += 1) {
      const flag = block[pointer++];
      const nameOffset = u32be(block, pointer); pointer += 4;
      const storage = flag & 0xf0;
      const type = flag & 0x0f;
      let constant = null;
      if (storage === 0x30) {
        const result = readValue(type, block, pointer);
        constant = result[0]; pointer += result[1];
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
        const result = readValue(column.type, block, offset);
        row[column.name] = result[0]; offset += result[1];
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
      for (let i = 0; i < count; i += 1) {
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
        for (let i = 0; i < length; i += 1) {
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
  async function inflate(bytes) {
    const stream = new DecompressionStream('deflate');
    return new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(stream)).arrayBuffer());
  }
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
  async function unpackPhysical(cpks, plan, role, name, fallbackRecordSize) {
    const packed = cpks[role]?.[name];
    if (!packed) throw new Error(`${name} não encontrado em ${role}`);
    const raw = await unpackWesys(packed);
    const hash = await reader.sha256(raw);
    const spec = (plan.arquivos || []).find((item) => item.arquivo === name && item.papel_fonte === role) || null;
    const recordSize = Number(spec?.tamanho_registro ?? fallbackRecordSize);
    if (!Number.isInteger(recordSize) || recordSize <= 0 || raw.length % recordSize !== 0) throw new Error(`tamanho físico incompatível: ${role}/${name}`);
    if (spec && hash !== String(spec.sha256_arquivo).toLowerCase()) throw new Error(`fingerprint físico divergente: ${role}/${name}`);
    return { raw, hash, recordSize };
  }

  function declaredRange(fieldDefinition, raw, label) {
    const transform = fieldDefinition.transformacao || {};
    const domain = typeof transform.enum === 'string' ? transform.enum : transform.dominio;
    const match = /^(\d+)\.\.(\d+)$/.exec(String(domain || ''));
    if (!match) throw new Error(`normalização ausente no contrato para ${label}`);
    const value = Number(raw);
    const minimum = Number(match[1]), maximum = Number(match[2]);
    if (!Number.isInteger(value) || value < minimum || value > maximum) {
      throw new Error(`valor físico fora do domínio contratado para ${label}: ${raw}`);
    }
    return value;
  }
  function declaredEnum(plan, key, raw) {
    const definition = field(plan, key);
    const values = definition.transformacao?.enum;
    if (!values || Array.isArray(values) || typeof values !== 'object') {
      throw new Error(`enumeração ausente no contrato: ${key}`);
    }
    // decodeFile pode já ter aplicado o enum do próprio campo. Aceitamos esse
    // resultado apenas se ele pertencer à enumeração recebida no pedido; nunca
    // recorremos a um mapa local como segunda autoridade.
    if (typeof raw === 'string' && Object.values(values).includes(raw)) return raw;
    const normalized = values[String(raw)];
    if (typeof normalized !== 'string' || !normalized.length) {
      throw new Error(`valor físico sem enumeração contratada: ${key}=${raw}`);
    }
    return normalized;
  }
  function declaredPrecedence(plan, keys, values, label) {
    const active = keys.map((key) => {
      const definition = field(plan, key);
      const transform = definition.transformacao || {};
      if (transform.composicao !== 'precedencia' || typeof transform.grupo !== 'string' || !transform.grupo || typeof transform.rotulo !== 'string' || !transform.rotulo) {
        throw new Error(`composição por precedência ausente no contrato para ${label}: ${key}`);
      }
      return {
        key,
        active: Number(values[key]) !== 0,
        priority: Number(transform.prioridade),
        label: transform.rotulo,
        group: transform.grupo
      };
    });
    if (new Set(active.map((item) => item.group)).size !== 1) throw new Error(`grupo de precedência incompatível para ${label}`);
    const selected = active.filter((item) => item.active).sort((left, right) => right.priority - left.priority)[0];
    if (selected) return { value: selected.label, state: 'precedencia_declarada_no_contrato' };

    // O nível-base não recebe um nome local. Ele só é resolvido quando o
    // catálogo físico de textos contratado contém, na mesma seção e em IDs
    // consecutivos, a sequência [nível-base, prioridade 1, prioridade 2...].
    // As identidades continuam sendo os bits; os textos são apenas a saída de
    // apresentação. Se o vínculo não for unívoco, a leitura falha fechada.
    const ordered = [...active].sort((left, right) => left.priority - right.priority);
    if (!ordered.length || !ordered.every((item, index) => Number.isInteger(item.priority) && item.priority === index + 1)) {
      throw new Error(`prioridades de precedência não enumeráveis para ${label}`);
    }
    const cacheKey = ordered.map((item) => `${item.key}:${item.priority}:${item.label}`).join('|');
    let planCache = precedenceBaseLabelCache.get(plan);
    if (!planCache) {
      planCache = new Map();
      precedenceBaseLabelCache.set(plan, planCache);
    }
    const cached = planCache.get(cacheKey);
    if (cached) return { value: cached, state: 'nivel_base_catalogo_texto_contratado' };

    const textRows = requireCatalog(plan, 'texto_do_jogo');
    const rowsBySectionAndId = new Map();
    for (const row of textRows) {
      const section = typeof row.secao === 'string' ? row.secao : null;
      const id = Number(row.id_texto);
      if (!section || !Number.isInteger(id) || typeof row.texto !== 'string' || !row.texto) continue;
      rowsBySectionAndId.set(`${section}\u0000${id}`, row.texto);
    }
    const baseLabels = new Set();
    for (const row of textRows) {
      const section = typeof row.secao === 'string' ? row.secao : null;
      const baseId = Number(row.id_texto);
      if (!section || !Number.isInteger(baseId) || typeof row.texto !== 'string' || !row.texto) continue;
      const matches = ordered.every((item) => rowsBySectionAndId.get(`${section}\u0000${baseId + item.priority}`) === item.label);
      if (matches) baseLabels.add(row.texto);
    }
    if (baseLabels.size !== 1) {
      throw new Error(`nível-base de ${label} não pode ser derivado univocamente do catálogo de textos contratado`);
    }
    const baseLabel = [...baseLabels][0];
    planCache.set(cacheKey, baseLabel);
    return { value: baseLabel, state: 'nivel_base_catalogo_texto_contratado' };
  }
  function overallByContract(plan, attributes, position) {
    const definition = reader.requirePlan(plan).fields.get('carta.overall');
    if (!definition) return { value: null, state: 'nao_solicitado_pelo_contrato' };
    const weights = definition.transformacao?.pesos_por_posicao?.[position];
    if (!weights || !Number.isFinite(Number(weights.base)) || !Array.isArray(weights.pesos)) {
      throw new Error(`pesos de overall ausentes no contrato para posição ${position}`);
    }
    if (weights.pesos.length !== attributes.length) {
      throw new Error(`pesos de overall incompatíveis com atributos para posição ${position}`);
    }
    let score = Number(weights.base);
    for (let index = 0; index < weights.pesos.length; index += 1) {
      if (!Number.isFinite(Number(attributes[index])) || !Number.isFinite(Number(weights.pesos[index]))) {
        throw new Error(`atributo/peso inválido no overall contratado para posição ${position}`);
      }
      score += Number(attributes[index]) * Number(weights.pesos[index]);
    }
    return { value: Math.round(score), state: 'normalizado_pelo_contrato' };
  }
  async function decodeLeagueByTeam(bytes, plan, cpk) {
    const teamField = field(plan, 'carta.liga.team_id');
    const leagueField = field(plan, 'carta.liga.codigo');
    if (teamField.arquivo_id !== leagueField.arquivo_id) throw new Error('vínculo de liga não pertence ao mesmo arquivo contratado');
    const file = fileById(plan, teamField.arquivo_id);
    const packed = cpk[file.arquivo];
    if (!packed) throw new Error(`${file.arquivo} não encontrado`);
    const decoded = await reader.decodeFile(plan, file.arquivo, await unpackWesys(packed), ['carta.liga.team_id', 'carta.liga.codigo']);
    const result = new Map();
    for (const record of decoded.records) {
      const team = Number(record.values['carta.liga.team_id']);
      const league = Number(record.values['carta.liga.codigo']);
      if (team && league && !result.has(team)) result.set(team, league);
    }
    return result;
  }
  async function decodeBasicCards(bytes, plan) {
    rememberPlan(plan);
    const keys = ['carta.id','carta.altura','carta.peso','carta.idade','carta.posicao.principal','carta.playstyle.primario','carta.playstyle.secundario','carta.pe','carta.pe.ruim_uso','carta.pe.ruim_precisao','carta.forma','carta.resistencia_lesao.alta','carta.resistencia_lesao.media','carta.nacionalidade.raw','carta.clube.codigo','carta.nome.roman'];
    const idField = field(plan, 'carta.id');
    const file = fileById(plan, idField.arquivo_id);
    if (keys.some((key) => field(plan, key).arquivo_id !== file.arquivo_id)) throw new Error('dados básicos/vínculos da carta não pertencem ao mesmo arquivo contratado');
    const cpk = extractCpk(bytes);
    const packed = cpk[file.arquivo];
    if (!packed) throw new Error(`${file.arquivo} não encontrado no CPK atual`);
    const [decoded, leagueByTeam] = await Promise.all([
      reader.decodeFile(plan, file.arquivo, await unpackWesys(packed), keys),
      decodeLeagueByTeam(bytes, plan, cpk)
    ]);
    const positions = new Map(requireCatalog(plan, 'posicao_jogo').map((row) => [Number(row.id), row.codigo_en]));
    const playstyles = new Map(requireCatalog(plan, 'playstyle').map((row) => [Number(row.bit ?? row.id_jogo), row]));
    const clubs = new Map(requireCatalog(plan, 'clube_jogo').map((row) => [Number(row.codigo_jogo), row]));
    const leagues = new Map(requireCatalog(plan, 'liga_jogo').map((row) => [Number(row.codigo_jogo), row]));
    const nationalities = new Map(requireCatalog(plan, 'nacionalidade_jogo').map((row) => [Number(row.codigo_jogo), row]));
    return decoded.records.map((record) => {
      const v = record.values;
      const id = String(v['carta.id']);
      const position = positions.get(Number(v['carta.posicao.principal']));
      if (!position) throw new Error(`posição principal sem catálogo: ${id}`);
      const primaryId = Number(v['carta.playstyle.primario']);
      const secondaryId = Number(v['carta.playstyle.secundario']);
      const nationalityCode = Number(v['carta.nacionalidade.raw']);
      const clubCode = Number(v['carta.clube.codigo']);
      const leagueCode = leagueByTeam.get(clubCode) ?? null;
      if (nationalityCode && !nationalities.has(nationalityCode)) throw new Error(`nacionalidade sem catálogo: ${nationalityCode}`);
      if (clubCode && !clubs.has(clubCode)) throw new Error(`clube sem catálogo: ${clubCode}`);
      if (leagueCode != null && !leagues.has(leagueCode)) throw new Error(`liga sem catálogo: ${leagueCode}`);
      const nationality = nationalities.get(nationalityCode) || null;
      const nationalityLabel = nationality == null ? null : (nationality.nome_pt_br || nationality.nome_en || nationality.sigla || null);
      if (nationalityCode && !nationalityLabel) throw new Error(`nacionalidade sem rótulo derivado do catálogo contratado: ${nationalityCode}`);
      const injuryKeys = ['carta.resistencia_lesao.alta', 'carta.resistencia_lesao.media'];
      const injuryHigh = Number(v['carta.resistencia_lesao.alta']) !== 0;
      const injuryMedium = Number(v['carta.resistencia_lesao.media']) !== 0;
      const injury = declaredPrecedence(plan, injuryKeys, v, 'carta.resistencia_lesao');
      return {
        card_id:id, height:Number(v['carta.altura']), weight:Number(v['carta.peso']), age:Number(v['carta.idade']), position,
        primary_style_id:primaryId, primary_style_unknown:primaryId !== 0 && !playstyles.has(primaryId),
        defensive_style_id:secondaryId, defensive_style_confirmed:secondaryId === 0 || playstyles.has(secondaryId),
        weak_foot_usage:declaredRange(field(plan, 'carta.pe.ruim_uso'), v['carta.pe.ruim_uso'], 'carta.pe.ruim_uso'),
        weak_foot_accuracy:declaredRange(field(plan, 'carta.pe.ruim_precisao'), v['carta.pe.ruim_precisao'], 'carta.pe.ruim_precisao'),
        foot:declaredEnum(plan, 'carta.pe', v['carta.pe']),
        form:declaredRange(field(plan, 'carta.forma'), v['carta.forma'], 'carta.forma'),
        injury:injury.value, injury_raw:{ alta:injuryHigh, media:injuryMedium }, injury_normalization:injury.state,
        nationality:nationalityLabel, nacionalidade_codigo:nationalityCode,
        clube_codigo:clubCode, clube:clubs.get(clubCode) || null, liga_codigo:leagueCode, liga:leagueCode == null ? null : leagues.get(leagueCode) || null,
        name:String(v['carta.nome.roman'] || '')
      };
    }).filter((card) => {
      const id = BigInt(card.card_id);
      return id !== 0n && id < (1n << 50n) && card.height >= 145 && card.height <= 210 && card.age >= 14 && card.age <= 47;
    });
  }
  async function extractCardsFromCpkV46(bytes, plan, log = () => {}) {
    rememberPlan(plan);
    const cards = await decodeBasicCards(bytes, plan);
    const [slots, attributes, relations, bodies] = await Promise.all([
      core.extractCardSlotsByContract(bytes, plan), core.extractCardAttributesByContract(bytes, plan),
      core.extractCardRelationsByContract(bytes, plan), core.extractCardBodiesByContract(bytes, plan)
    ]);
    for (const card of cards) {
      card.box = null;
      const slot = slots.slots.get(card.card_id);
      if (!slot) throw new Error(`contrato não retornou slots para ${card.card_id}`);
      card.booster_primary = slot.slot1; card.booster_conditional = slot.slot2;
      card.attrs = attributes.get(card.card_id);
      if (!card.attrs) throw new Error(`contrato não retornou atributos para ${card.card_id}`);
      const test = card.attrs.every((value) => value === 99);
      const base = BigInt(card.card_id) < (1n << 18n);
      card.tipo = test ? 'teste' : (base ? 'base' : 'colecionavel');
      card.roda_motor = !test && !base;
      const overall = overallByContract(plan, card.attrs, card.position);
      card.overall = overall.value;
      card.overall_normalization = overall.state;
      const rel = relations.get(card.card_id);
      if (!rel) throw new Error(`contrato não retornou relações para ${card.card_id}`);
      if (!Array.isArray(rel.habilidades_fisicas)) {
        throw new Error(`contrato não retornou habilidades físicas para ${card.card_id}`);
      }
      card.skills = rel.skills;
      card.habilidades_fisicas = rel.habilidades_fisicas;
      card.ai_styles = rel.ai;
      if (!Array.isArray(rel.estilos_ia_fisicos)) {
        throw new Error(`contrato não retornou estilos IA físicos para ${card.card_id}`);
      }
      card.estilos_ia_fisicos = rel.estilos_ia_fisicos;
      card.aptitudes = rel.aptitudes;
      const body = bodies.get(card.card_id);
      if (!body) throw new Error(`contrato não retornou corpo para ${card.card_id}`);
      card.corpo = [card.height, ...body];
    }
    log(`V4.6 · cartas e vínculos lidos pelas referências canônicas do contrato ${plan.versao_contrato}`);
    return cards;
  }

  async function validateSourceByContractV46(bytes, plan, role) {
    rememberPlan(plan);
    return core.validateSourceByContract(bytes, plan, role);
  }

  async function extractCardDimensionsByFamilyV46(sourceBytes, sourceDescriptors = {}, log = () => {}) {
    const plan = planNow();
    const roles = familyRoles(plan, 'dimensoes');
    for (const role of roles) if (!sourceBytes[role]) throw new Error(`Fonte contratada ausente para Dimensões: ${role}`);
    const textRoles = familyRoles(plan, 'textos');
    const textRole = textRoles.find((role) => sourceBytes[role]);
    if (!textRole) throw new Error('Dimensões exige a família Textos contratada para resolver rótulos oficiais');
    const cpks = Object.fromEntries([...new Set([...roles, textRole])].map((role) => [role, extractCpk(sourceBytes[role])]));
    const fileHashes = {};

    const nationalityRefs = requireCatalog(plan, 'nacionalidade_jogo');
    const clubRefs = requireCatalog(plan, 'clube_jogo');
    const leagueRefs = requireCatalog(plan, 'liga_jogo');
    const typeRefs = requireCatalog(plan, 'tipo_carta_jogo');
    const countryRef = template(nationalityRefs, (row) => row.arquivo === 'Country.bin', 'nacionalidade');
    const clubRef = template(clubRefs, (row) => row.arquivo === 'Team.bin' && row.tamanho_registro, 'clube');
    const leagueRef = template(leagueRefs, (row) => row.arquivo === 'CompetitionUnit.bin' && row.tamanho_registro, 'liga');

    const countryByRole = {};
    for (const role of roles) {
      const item = await unpackPhysical(cpks, plan, role, countryRef.arquivo || 'Country.bin', Number(countryRef.tamanho_registro));
      countryByRole[role] = item.raw;
      fileHashes[`${role}:Country.bin`] = item.hash;
    }
    if (new Set(roles.map((role) => fileHashes[`${role}:Country.bin`])).size !== 1) throw new Error('Country.bin não é byte-idêntico nas três fontes');
    const countryRole = roles[0];
    const country = countryByRole[countryRole];
    const countrySize = Number(countryRef.tamanho_registro);
    const nationalities = [];
    const nationalityByCode = new Map();
    for (let offset = 0, recordIndex = 0; offset < country.length; offset += countrySize, recordIndex += 1) {
      const codigo = reader.readBitsLE(country, offset, Number(countryRef.bit_codigo), Number(countryRef.largura_codigo));
      const record = {
        id:String(codigo), codigo_jogo:codigo,
        nome_pt_br:fixed(country, offset + Number(countryRef.offset_nome_pt_br), Number(countryRef.largura_nome_pt_br)),
        sigla:fixed(country, offset + Number(countryRef.offset_sigla), Number(countryRef.largura_sigla)),
        source_role:countryRole, arquivo:countryRef.arquivo, record_index:recordIndex, record_size:countrySize,
        codigo_bit:Number(countryRef.bit_codigo), codigo_largura:Number(countryRef.largura_codigo),
        nome_offset:Number(countryRef.offset_nome_pt_br), nome_largura:Number(countryRef.largura_nome_pt_br),
        sigla_offset:Number(countryRef.offset_sigla), sigla_largura:Number(countryRef.largura_sigla),
        source_file_sha256:fileHashes[`${countryRole}:Country.bin`], presente_dt870_atualizacao:roles.includes('dt870_updated'), presente_dt200:roles.includes('dt200'), presente_dt870_original:roles.includes('dt870_original')
      };
      if (!record.nome_pt_br || !record.sigla || nationalityByCode.has(codigo)) throw new Error(`Country.bin inválido no registro ${recordIndex}`);
      record.fingerprint = core.stableJson(record);
      nationalities.push(record); nationalityByCode.set(codigo, record);
    }

    const teamSources = {};
    const teamPresence = new Map();
    const teamSize = Number(clubRef.tamanho_registro);
    for (const role of roles) {
      const item = await unpackPhysical(cpks, plan, role, clubRef.arquivo || 'Team.bin', teamSize);
      fileHashes[`${role}:Team.bin`] = item.hash;
      const records = new Map();
      for (let offset = 0, recordIndex = 0; offset < item.raw.length; offset += teamSize, recordIndex += 1) {
        const codigo = Number(reader.readByteLE(item.raw, offset + Number(clubRef.offset_codigo), Number(clubRef.largura_codigo)));
        if (records.has(codigo)) throw new Error(`Team.bin de ${role} duplicou o código ${codigo}`);
        records.set(codigo, {
          codigo_jogo:codigo,
          nome_pt_br:fixed(item.raw, offset + Number(clubRef.offset_nome_pt_br), Number(clubRef.largura_nome_pt_br)) || null,
          nome_en:fixed(item.raw, offset + Number(clubRef.offset_nome_en), Number(clubRef.largura_nome_en)) || null,
          sigla:fixed(item.raw, offset + Number(clubRef.offset_sigla), Number(clubRef.largura_sigla)) || null,
          source_role:role, record_index:recordIndex, source_file_sha256:item.hash
        });
        if (!teamPresence.has(codigo)) teamPresence.set(codigo, new Set());
        teamPresence.get(codigo).add(role);
      }
      teamSources[role] = records;
    }
    const actualTeamCodes = new Set(teamPresence.keys());

    const competitionUnitSources = {};
    const leaguePresence = new Map();
    const unitSize = Number(leagueRef.tamanho_registro);
    for (const role of roles) {
      const item = await unpackPhysical(cpks, plan, role, leagueRef.arquivo || 'CompetitionUnit.bin', unitSize);
      fileHashes[`${role}:CompetitionUnit.bin`] = item.hash;
      const records = new Map();
      for (let offset = 0, recordIndex = 0; offset < item.raw.length; offset += unitSize, recordIndex += 1) {
        const codigo = Number(reader.readByteLE(item.raw, offset + Number(leagueRef.offset_codigo), Number(leagueRef.largura_codigo)));
        if (records.has(codigo)) throw new Error(`CompetitionUnit.bin de ${role} duplicou o código ${codigo}`);
        const parent = Number(reader.readByteLE(item.raw, offset + Number(leagueRef.offset_codigo_pai), Number(leagueRef.largura_codigo_pai)));
        records.set(codigo, {
          codigo_jogo:codigo, codigo_pai:parent === 0xffff ? null : parent,
          nome_pt_br:fixed(item.raw, offset + Number(leagueRef.offset_nome_pt_br), Number(leagueRef.largura_nome_pt_br)) || null,
          nome_en:fixed(item.raw, offset + Number(leagueRef.offset_nome_en), Number(leagueRef.largura_nome_en)) || null,
          source_role:role, record_index:recordIndex, source_file_sha256:item.hash
        });
        if (!leaguePresence.has(codigo)) leaguePresence.set(codigo, new Set());
        leaguePresence.get(codigo).add(role);
      }
      competitionUnitSources[role] = records;
    }
    const leagues = [...leaguePresence.keys()].sort((a,b) => a-b).map((codigo) => {
      const sourceRole = roles.find((role) => competitionUnitSources[role].has(codigo));
      const source = competitionUnitSources[sourceRole].get(codigo);
      const presence = leaguePresence.get(codigo);
      const record = {
        id:String(codigo), codigo_jogo:codigo, codigo_pai:source.codigo_pai, nome_pt_br:source.nome_pt_br, nome_en:source.nome_en,
        source_role:sourceRole, arquivo:leagueRef.arquivo, record_index:source.record_index, record_size:unitSize,
        codigo_offset:Number(leagueRef.offset_codigo), codigo_largura:Number(leagueRef.largura_codigo),
        codigo_pai_offset:Number(leagueRef.offset_codigo_pai), codigo_pai_largura:Number(leagueRef.largura_codigo_pai),
        nome_pt_br_offset:Number(leagueRef.offset_nome_pt_br), nome_pt_br_largura:Number(leagueRef.largura_nome_pt_br),
        nome_en_offset:Number(leagueRef.offset_nome_en), nome_en_largura:Number(leagueRef.largura_nome_en),
        source_file_sha256:source.source_file_sha256,
        presente_dt870_atualizacao:presence.has('dt870_updated'), presente_dt200:presence.has('dt200'), presente_dt870_original:presence.has('dt870_original')
      };
      record.fingerprint = core.stableJson(record);
      return record;
    });
    const leagueCodes = new Set(leagues.map((row) => row.codigo_jogo));

    const teamField = field(plan, 'carta.liga.team_id');
    const leagueField = field(plan, 'carta.liga.codigo');
    if (teamField.arquivo_id !== leagueField.arquivo_id) throw new Error('contrato de CompetitionEntry incompleto');
    const entryFile = fileById(plan, teamField.arquivo_id);
    const leagueByTeam = new Map();
    const competitionEntryDetails = {};
    for (const role of roles) {
      const item = await unpackPhysical(cpks, plan, role, entryFile.arquivo, Number(entryFile.tamanho_registro));
      fileHashes[`${role}:${entryFile.arquivo}`] = item.hash;
      competitionEntryDetails[role] = { records:item.raw.length / item.recordSize, source_file_sha256:item.hash };
      for (let offset = 0, recordIndex = 0; offset < item.raw.length; offset += item.recordSize, recordIndex += 1) {
        const team = Number(reader.readByteLE(item.raw, offset + Number(teamField.byte_offset), Number(teamField.largura_bytes)));
        const rawLeague = Number(reader.readByteLE(item.raw, offset + Number(leagueField.byte_offset), Number(leagueField.largura_bytes)));
        const league = leagueField.transformacao?.operacao === 'high16' ? ((rawLeague >>> 16) & 0xffff) : rawLeague;
        if (team && leagueCodes.has(league) && !leagueByTeam.has(team)) leagueByTeam.set(team, { codigo_liga:league, source_role:role, record_index:recordIndex });
      }
    }

    const idField = field(plan, 'carta.id');
    const playerFile = fileById(plan, idField.arquivo_id);
    const cardRole = familyRoles(plan, 'cartas')[0];
    if (!sourceBytes[cardRole]) throw new Error(`Cartas sem fonte contratada para Dimensões: ${cardRole}`);
    const playerItem = await unpackPhysical(cpks, plan, cardRole, playerFile.arquivo, Number(playerFile.tamanho_registro));
    fileHashes[`${cardRole}:${playerFile.arquivo}`] = playerItem.hash;
    const validCards = new Set((await decodeBasicCards(sourceBytes[cardRole], plan)).map((card) => card.card_id));
    const natField = field(plan, 'carta.nacionalidade.raw');
    const clubField = field(plan, 'carta.clube.codigo');
    const subtypeField = field(plan, 'carta.tipo.subtipo');
    const typeField = field(plan, 'carta.tipo.codigo');
    const physicalCards = [];
    const firstCardByRawTeam = new Map();
    for (let offset = 0, recordIndex = 0; offset < playerItem.raw.length; offset += playerItem.recordSize, recordIndex += 1) {
      const id = String(reader.readByteLE(playerItem.raw, offset + Number(idField.byte_offset), Number(idField.largura_bytes)));
      if (!validCards.has(id)) continue;
      const rawNat = reader.readBitsLE(playerItem.raw, offset, Number(natField.bit_inicio), Number(natField.largura_bits));
      const rawTeam = Number(reader.readByteLE(playerItem.raw, offset + Number(clubField.byte_offset), Number(clubField.largura_bytes)));
      const subtype = reader.readBitsLE(playerItem.raw, offset, Number(subtypeField.bit_inicio), Number(subtypeField.largura_bits));
      const transform = typeField.transformacao || {};
      const typeCode = Number((BigInt(id) >> BigInt(transform.bit_inicio)) & ((1n << BigInt(transform.largura_bits)) - 1n));
      if (rawTeam && !firstCardByRawTeam.has(rawTeam)) firstCardByRawTeam.set(rawTeam, recordIndex);
      physicalCards.push({
        card_id:id, registro_vinculos_jogo:recordIndex, codigo_nacionalidade_player_raw:rawNat,
        codigo_clube_player_raw:rawTeam, codigo_tipo_carta_fisico:typeCode,
        marcador_subtipo_tipo_carta:subtype, jogador_indisponivel:false
      });
    }

    const unavailableField = field(plan, 'carta.tipo.indisponivel.id');
    const deleteFile = fileById(plan, unavailableField.arquivo_id);
    const deleteItem = await unpackPhysical(cpks, plan, cardRole, deleteFile.arquivo, Number(deleteFile.tamanho_registro));
    fileHashes[`${cardRole}:${deleteFile.arquivo}`] = deleteItem.hash;
    const deleted = new Set();
    for (let offset = 0; offset < deleteItem.raw.length; offset += deleteItem.recordSize) {
      deleted.add(String(reader.readByteLE(deleteItem.raw, offset + Number(unavailableField.byte_offset), Number(unavailableField.largura_bytes))));
    }
    for (const card of physicalCards) card.jogador_indisponivel = deleted.has(card.card_id);

    const clubs = [...actualTeamCodes].sort((a,b) => a-b).map((codigo) => {
      const sourceRole = roles.find((role) => teamSources[role].has(codigo));
      const source = teamSources[sourceRole].get(codigo);
      const presence = teamPresence.get(codigo);
      const record = {
        id:String(codigo), codigo_jogo:codigo, nome_pt_br:source.nome_pt_br, nome_en:source.nome_en, sigla:source.sigla,
        source_role:sourceRole, arquivo:clubRef.arquivo, record_index:source.record_index, registro_primeira_carta:null,
        record_size:teamSize, codigo_offset:Number(clubRef.offset_codigo), codigo_largura:Number(clubRef.largura_codigo),
        nome_pt_br_offset:Number(clubRef.offset_nome_pt_br), nome_pt_br_largura:Number(clubRef.largura_nome_pt_br),
        nome_en_offset:Number(clubRef.offset_nome_en), nome_en_largura:Number(clubRef.largura_nome_en),
        sigla_offset:Number(clubRef.offset_sigla), sigla_largura:Number(clubRef.largura_sigla), source_file_sha256:source.source_file_sha256,
        presente_dt870_atualizacao:presence.has('dt870_updated'), presente_dt200:presence.has('dt200'), presente_dt870_original:presence.has('dt870_original'),
        pode_rodar:Boolean(source.nome_pt_br || source.nome_en), falta_o_que:null
      };
      record.fingerprint = core.stableJson(record);
      return record;
    });
    for (const codigo of [...firstCardByRawTeam.keys()].filter((value) => !actualTeamCodes.has(value)).sort((a,b) => a-b)) {
      const record = {
        id:String(codigo), codigo_jogo:codigo, nome_pt_br:null, nome_en:null, sigla:null,
        source_role:'dt870_atualizacao:Player.bin_codigo_sem_catalogo', arquivo:playerFile.arquivo, record_index:null,
        registro_primeira_carta:firstCardByRawTeam.get(codigo), record_size:playerItem.recordSize,
        codigo_offset:Number(clubField.byte_offset), codigo_largura:Number(clubField.largura_bytes),
        nome_pt_br_offset:null, nome_pt_br_largura:null, nome_en_offset:null, nome_en_largura:null, sigla_offset:null, sigla_largura:null,
        source_file_sha256:playerItem.hash, presente_dt870_atualizacao:false, presente_dt200:false, presente_dt870_original:false,
        pode_rodar:false, falta_o_que:'código presente em Player.bin, mas ausente nos Team.bin DT870 atualização/original e DT200'
      };
      record.fingerprint = core.stableJson(record);
      clubs.push(record);
    }
    clubs.sort((a,b) => a.codigo_jogo - b.codigo_jogo);
    const clubByCode = new Map(clubs.map((row) => [row.codigo_jogo, row]));

    const textCatalog = await core.extractTextCatalogFromCpk(sourceBytes[textRole]);
    const textByKey = new Map(textCatalog.records.map((row) => [row.id, row]));
    const types = typeRefs.map((source) => {
      const record = { ...source, id:source.tipo_carta_id };
      const official = record.chave_texto ? textByKey.get(record.chave_texto) : null;
      if (record.chave_texto && (!official || official.texto !== record.nome_exibicao)) throw new Error(`rótulo oficial ${record.chave_texto} divergente`);
      if (official) {
        record.secao_texto = official.secao; record.id_texto = official.id_texto; record.nome_pt_br = official.texto;
        record.arquivo_texto = official.arquivo; record.cpk_texto = official.cpk; record.entrada_texto = official.entrada_idx;
        record.entrada_offset = official.entrada_offset; record.texto_offset = official.texto_offset;
        record.tamanho_armazenado = official.tamanho_armazenado; record.hash_all_str = official.fonte_arquivo_sha256;
      }
      record.fingerprint = core.stableJson(record);
      return record;
    });
    const typeByState = new Map(types.filter((row) => !row.usa_player_delete_list).map((row) => [`${row.codigo_tipo_fisico}/${row.marcador_subtipo}`, row]));
    const deleteType = types.find((row) => row.usa_player_delete_list);
    const cards = physicalCards.map((physical) => {
      const codigoNacionalidade = Math.floor(physical.codigo_nacionalidade_player_raw / 2);
      const club = physical.codigo_clube_player_raw ? clubByCode.get(physical.codigo_clube_player_raw) : null;
      const clubResolved = Boolean(club && club.pode_rodar);
      const league = club ? leagueByTeam.get(physical.codigo_clube_player_raw) : null;
      const type = physical.jogador_indisponivel ? deleteType : typeByState.get(`${physical.codigo_tipo_carta_fisico}/${physical.marcador_subtipo_tipo_carta}`);
      if (!nationalityByCode.has(codigoNacionalidade)) throw new Error(`Carta ${physical.card_id} referencia nacionalidade ausente: ${codigoNacionalidade}`);
      if (!type) throw new Error(`Carta ${physical.card_id} possui estado de tipo não mapeado`);
      return {
        ...physical, codigo_nacionalidade:codigoNacionalidade,
        codigo_clube:club ? physical.codigo_clube_player_raw : null,
        codigo_liga:league ? league.codigo_liga : null,
        tipo_carta_id:type.tipo_carta_id, chave_tipo_carta:type.chave_texto,
        tipo_provisorio:Boolean(type.tipo_provisorio),
        pode_rodar_vinculos:!physical.codigo_clube_player_raw || clubResolved,
        falta_o_que_vinculos:physical.codigo_clube_player_raw && !clubResolved ? 'codigo_clube sem definicao em Team.bin dos tres CPKs' : null
      };
    });
    const typeCounts = {};
    for (const card of cards) typeCounts[card.tipo_carta_id] = (typeCounts[card.tipo_carta_id] || 0) + 1;
    const snapshot = {
      contract:core.CARD_DIMENSIONS_CONTRACT_VERSION, database_write:false,
      source_policy:'mesma lógica V4; referências físicas fornecidas por clube_novo',
      sources:sourceDescriptors, source_files:fileHashes,
      physical_contract:{ source:'clube_novo + contrato ativo', versao_contrato:plan.versao_contrato },
      counts:{
        cards:cards.length, nationalities:nationalities.length, clubs:clubs.length, leagues:leagues.length, types:types.length,
        deleted_cards:cards.filter((c) => c.jogador_indisponivel).length,
        cards_with_club:cards.filter((c) => c.codigo_clube !== null).length,
        cards_with_league:cards.filter((c) => c.codigo_liga !== null).length,
        provisional_cards:cards.filter((c) => c.tipo_provisorio).length,
        blocked_cards:cards.filter((c) => !c.pode_rodar_vinculos).length,
        type_distribution:typeCounts
      },
      catalogs:{ nationalities, clubs, leagues, types }, cards, competition_entry_sources:competitionEntryDetails
    };
    log(`V4.6 · Dimensões por catálogo: ${cards.length} cartas · ${nationalities.length} países · ${clubs.length} clubes · ${leagues.length} ligas · ${types.length} tipos`);
    return snapshot;
  }

  global.CLUBEF_CORE = Object.freeze({
    ...core,
    validateSourceByContract:validateSourceByContractV46,
    extractCardsFromCpk:extractCardsFromCpkV46,
    extractCardDimensionsByFamily:extractCardDimensionsByFamilyV46,
    decodeBasicCardsByContract:decodeBasicCards
  });
})(globalThis);
