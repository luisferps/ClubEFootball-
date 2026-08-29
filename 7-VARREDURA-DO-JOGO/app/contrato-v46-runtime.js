'use strict';

/**
 * Runtime V4.6: preserva a lógica do Extrator e troca somente a origem das
 * referências físicas. Endereço/bit/offset vêm do pedido/catálogos de
 * clube_novo; esta camada não define endereço semântico próprio.
 */
(function installV46ContractRuntime(global) {
  const core = global.CLUBEF_CORE;
  const reader = global.CLUBEF_CONTRACT_READER;
  const physicalMap = global.CLUBEF_PHYSICAL_MAP || {};
  if (!core || !reader) throw new Error('contrato-v46-runtime.js requer leitura-contrato.js e extrator-core.js');

  const TD = new TextDecoder('utf-8');
  const u32 = (bytes, offset) => (bytes[offset] | (bytes[offset + 1] << 8) | (bytes[offset + 2] << 16) | (bytes[offset + 3] << 24)) >>> 0;
  const u32be = (bytes, offset) => ((bytes[offset] << 24) | (bytes[offset + 1] << 16) | (bytes[offset + 2] << 8) | bytes[offset + 3]) >>> 0;
  const u16be = (bytes, offset) => ((bytes[offset] << 8) | bytes[offset + 1]) >>> 0;

  function utfDeobfuscate(data) {
    if (data[0] === 0x40 && data[1] === 0x55 && data[2] === 0x54 && data[3] === 0x46) return data;
    const output = Uint8Array.from(data); let mask = 0x655f >>> 0;
    for (let index = 0; index < output.length; index += 1) { output[index] ^= mask & 0xff; mask = Math.imul(mask, 0x4115) >>> 0; }
    return output;
  }

  function parseUtfTable(data) {
    const decoded = utfDeobfuscate(data), size = u32be(decoded, 4), block = decoded.subarray(8, 8 + size);
    const rowsOffset = u32be(block, 0), stringsOffset = u32be(block, 4), dataOffset = u32be(block, 8);
    const columnCount = u16be(block, 16), rowLength = u16be(block, 18), rowCount = u32be(block, 20), strings = block.subarray(stringsOffset, dataOffset);
    const readString = (offset) => { let end = offset; while (end < strings.length && strings[end] !== 0) end += 1; return TD.decode(strings.subarray(offset, end)); };
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
    let pointer = 24; const columns = [];
    for (let index = 0; index < columnCount; index += 1) {
      const flag = block[pointer++], nameOffset = u32be(block, pointer); pointer += 4;
      const storage = flag & 0xf0, type = flag & 0x0f; let constant = null;
      if (storage === 0x30) { const result = readValue(type, block, pointer); constant = result[0]; pointer += result[1]; }
      columns.push({ name: readString(nameOffset), storage, type, constant });
    }
    const rows = [];
    for (let rowIndex = 0; rowIndex < rowCount; rowIndex += 1) {
      let offset = rowsOffset + rowIndex * rowLength; const row = {};
      for (const column of columns) {
        if (column.storage === 0x30) { row[column.name] = column.constant; continue; }
        if (column.storage === 0x10) { row[column.name] = 0; continue; }
        const result = readValue(column.type, block, offset); row[column.name] = result[0]; offset += result[1];
      }
      rows.push(row);
    }
    return rows;
  }

  function decompressCriLayla(source) {
    if (!(source[0] === 0x43 && source[1] === 0x52 && source[2] === 0x49)) return source;
    const uncompressedSize = u32(source, 8), headerOffset = u32(source, 12), output = new Uint8Array(uncompressedSize);
    const header = source.subarray(16 + headerOffset, 16 + headerOffset + 0x100), data = source.subarray(16, 16 + headerOffset);
    let position = data.length * 8 - 1;
    const getBits = (count) => { let value = 0; for (let i = 0; i < count; i += 1) { const byteIndex = position >> 3, bitIndex = position & 7; value = (value << 1) | ((data[byteIndex] >> (7 - bitIndex)) & 1); position -= 1; } return value; };
    let write = uncompressedSize - 1;
    while (write >= 0) {
      if (getBits(1)) {
        let reference = write + getBits(13) + 3, length = 3, done = false;
        for (const width of [2, 3, 5]) { const count = getBits(width); length += count; if (count !== (1 << width) - 1) { done = true; break; } }
        if (!done) { let count = getBits(8); length += count; while (count === 255) { count = getBits(8); length += count; } }
        for (let i = 0; i < length; i += 1) { output[write] = output[reference]; write -= 1; reference -= 1; }
      } else { output[write] = getBits(8); write -= 1; }
    }
    const result = new Uint8Array(header.length + output.length); result.set(header, 0); result.set(output, header.length); return result;
  }

  function extractCpk(data) {
    if (!(data[0] === 0x43 && data[1] === 0x50 && data[2] === 0x4b)) throw new Error('arquivo não é um CPK');
    const header = parseUtfTable(data.subarray(16))[0], tocOffset = header.TocOffset, contentOffset = header.ContentOffset, files = {};
    if (tocOffset) for (const row of parseUtfTable(data.subarray(tocOffset + 16))) {
      const base = contentOffset && contentOffset <= tocOffset ? contentOffset : tocOffset, absolute = base + row.FileOffset;
      let chunk = data.subarray(absolute, absolute + row.FileSize); if (chunk[0] === 0x43 && chunk[1] === 0x52 && chunk[2] === 0x49) chunk = decompressCriLayla(chunk); files[row.FileName] = chunk;
    }
    return files;
  }

  const WESYS_KEYS = { 1: [378445824, 774547186, 214490323], 2: [0xED5B2960, 1246903118, 0xF3A31BAD] };
  async function inflate(bytes) { const stream = new DecompressionStream('deflate'); return new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(stream)).arrayBuffer()); }
  async function unpackWesys(data) {
    const nibble = data[1] & 15, compressedSize = u32(data, 8), originalSize = u32(data, 12), buffer = Uint8Array.from(data.subarray(16, 16 + compressedSize));
    const initial = WESYS_KEYS[nibble] || [0, 0, 0]; let x = initial[0] >>> 0, y = initial[1] >>> 0, z = initial[2] >>> 0, w = (((originalSize << 16) >>> 0) | compressedSize) >>> 0;
    const aligned = (compressedSize >> 2) * 4;
    for (let offset = 0; offset < aligned; offset += 4) { const t = (x ^ ((x << 11) >>> 0)) >>> 0, previous = w; x = y; y = z; z = w; w = (previous ^ (((previous >>> 11) ^ t) >>> 8) ^ t) >>> 0; const value = (u32(buffer, offset) ^ w) >>> 0; buffer[offset] = value & 0xff; buffer[offset + 1] = (value >>> 8) & 0xff; buffer[offset + 2] = (value >>> 16) & 0xff; buffer[offset + 3] = (value >>> 24) & 0xff; }
    return inflate(buffer);
  }

  function catalogRows(plan, table) { return (plan.catalogos || []).find((item) => item.schema === 'clube_novo' && item.table === table)?.rows || []; }
  function overall(attributes, position) {
    const weights = physicalMap.OVRW?.weights?.[position]; if (!weights) return null;
    let score = weights.b; for (let i = 0; i < weights.w.length; i += 1) { if (attributes[i] == null) return null; score += attributes[i] * weights.w[i]; } return Math.round(score);
  }

  async function decodeLeagueByTeam(bytes, plan, cpk) {
    const index = reader.requirePlan(plan), teamField = index.fields.get('carta.liga.team_id'), leagueField = index.fields.get('carta.liga.codigo');
    if (!teamField || !leagueField) throw new Error('contrato ativo não contém vínculo físico de liga');
    if (teamField.arquivo_id !== leagueField.arquivo_id) throw new Error('team_id e liga não pertencem ao mesmo arquivo contratado');
    const file = index.files.get(teamField.arquivo_id), packed = cpk[file.arquivo]; if (!file || !packed) throw new Error('arquivo contratado de vínculo de liga não encontrado');
    const decoded = await reader.decodeFile(plan, file.arquivo, await unpackWesys(packed), ['carta.liga.team_id','carta.liga.codigo']);
    const result = new Map();
    for (const record of decoded.records) { const team = Number(record.values['carta.liga.team_id']), league = Number(record.values['carta.liga.codigo']); if (team && league && !result.has(team)) result.set(team, league); }
    return result;
  }

  async function decodeBasicCards(bytes, plan) {
    const index = reader.requirePlan(plan);
    const keys = ['carta.id','carta.altura','carta.peso','carta.idade','carta.posicao.principal','carta.playstyle.primario','carta.playstyle.secundario','carta.pe','carta.pe.ruim_uso','carta.pe.ruim_precisao','carta.forma','carta.resistencia_lesao.alta','carta.resistencia_lesao.media','carta.nacionalidade.raw','carta.clube.codigo','carta.nome.roman'];
    if (keys.some((key) => !index.fields.has(key))) throw new Error('contrato ativo não contém todos os dados básicos/vínculos da carta');
    const file = index.files.get(index.fields.get('carta.id').arquivo_id);
    if (!file || keys.some((key) => index.fields.get(key).arquivo_id !== file.arquivo_id)) throw new Error('dados básicos/vínculos da carta não pertencem ao mesmo Player.bin contratado');
    const cpk = extractCpk(bytes), packed = cpk[file.arquivo]; if (!packed) throw new Error(`${file.arquivo} não encontrado no CPK atual`);
    const [decoded, leagueByTeam] = await Promise.all([
      reader.decodeFile(plan, file.arquivo, await unpackWesys(packed), keys),
      decodeLeagueByTeam(bytes, plan, cpk)
    ]);
    const positions = new Map(catalogRows(plan, 'posicao_jogo').map((row) => [Number(row.id), row.codigo_en]));
    const playstyles = new Map(catalogRows(plan, 'playstyle').map((row) => [Number(row.bit), row]));
    const clubs = new Map(catalogRows(plan, 'clube_jogo').map((row) => [Number(row.codigo_jogo), row]));
    const leagues = new Map(catalogRows(plan, 'liga_jogo').map((row) => [Number(row.codigo_jogo), row]));
    const nationalities = new Map(catalogRows(plan, 'nacionalidade_jogo').map((row) => [Number(row.codigo_jogo), row]));
    const nationalityEnglish = physicalMap.K?.NATIONALITY_ID || {};
    const weakUsage = ['Almost Never','Rarely','Occasionally','Regularly'], weakAccuracy = ['Low','Medium','High','Very High'], forms = ['Inconsistent','Standard','Unwavering'];
    return decoded.records.map((record) => {
      const v = record.values, id = String(v['carta.id']), position = positions.get(Number(v['carta.posicao.principal'])); if (!position) throw new Error(`posição principal sem catálogo no contrato: ${id}`);
      const primaryId = Number(v['carta.playstyle.primario']), secondaryId = Number(v['carta.playstyle.secundario']);
      const nationalityCode = Number(v['carta.nacionalidade.raw']), clubCode = Number(v['carta.clube.codigo']), leagueCode = leagueByTeam.get(clubCode) ?? null;
      if (nationalityCode && !nationalities.has(nationalityCode)) throw new Error(`nacionalidade sem catálogo canônico: ${nationalityCode}`);
      if (clubCode && !clubs.has(clubCode)) throw new Error(`clube sem catálogo canônico: ${clubCode}`);
      if (leagueCode != null && !leagues.has(leagueCode)) throw new Error(`liga sem catálogo canônico: ${leagueCode}`);
      return {
        card_id:id,height:Number(v['carta.altura']),weight:Number(v['carta.peso']),age:Number(v['carta.idade']),position,
        primary_style_id:primaryId,primary_style_unknown:primaryId!==0&&!playstyles.has(primaryId),defensive_style_id:secondaryId,defensive_style_confirmed:secondaryId===0||playstyles.has(secondaryId),
        weak_foot_usage:weakUsage[Number(v['carta.pe.ruim_uso'])],weak_foot_accuracy:weakAccuracy[Number(v['carta.pe.ruim_precisao'])],foot:String(v['carta.pe']),form:forms[Number(v['carta.forma'])],
        injury:Number(v['carta.resistencia_lesao.alta'])?'Alta':(Number(v['carta.resistencia_lesao.media'])?'Média':'Baixa'),
        nationality:nationalityEnglish[nationalityCode]||String(nationalityCode),nacionalidade_codigo:nationalityCode,
        clube_codigo:clubCode,clube:clubs.get(clubCode)||null,liga_codigo:leagueCode,liga:leagueCode==null?null:(leagues.get(leagueCode)||null),name:String(v['carta.nome.roman']||'')
      };
    }).filter((card)=>{const id=BigInt(card.card_id);return id!==0n&&id<(1n<<50n)&&card.height>=145&&card.height<=210&&card.age>=14&&card.age<=47;});
  }

  async function extractCardsFromCpkV46(bytes, plan, log = () => {}) {
    const cards = await decodeBasicCards(bytes, plan);
    const [slots, attributes, relations, bodies] = await Promise.all([core.extractCardSlotsByContract(bytes,plan),core.extractCardAttributesByContract(bytes,plan),core.extractCardRelationsByContract(bytes,plan),core.extractCardBodiesByContract(bytes,plan)]);
    for (const card of cards) {
      card.box=null; const slot=slots.slots.get(card.card_id); if(!slot) throw new Error(`contrato não retornou slots para ${card.card_id}`); card.booster_primary=slot.slot1; card.booster_conditional=slot.slot2;
      card.attrs=attributes.get(card.card_id); if(!card.attrs) throw new Error(`contrato não retornou atributos para ${card.card_id}`);
      const test=card.attrs.every((value)=>value===99), base=BigInt(card.card_id)<(1n<<18n); card.tipo=test?'teste':(base?'base':'colecionavel'); card.roda_motor=!test&&!base; card.overall=overall(card.attrs,card.position);
      const rel=relations.get(card.card_id); if(!rel) throw new Error(`contrato não retornou relações para ${card.card_id}`); card.skills=rel.skills; card.ai_styles=rel.ai; card.aptitudes=rel.aptitudes;
      const body=bodies.get(card.card_id); if(!body) throw new Error(`contrato não retornou corpo para ${card.card_id}`); card.corpo=[card.height,...body];
    }
    log(`V4.6 · cards, nacionalidade, clube, liga, slots, atributos, relações e corpo lidos pelo contrato ${plan.versao_contrato}`);
    return cards;
  }

  global.CLUBEF_CORE = Object.freeze({ ...core, extractCardsFromCpk:extractCardsFromCpkV46, decodeBasicCardsByContract:decodeBasicCards });
})(globalThis);
