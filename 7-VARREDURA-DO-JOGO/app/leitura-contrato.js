'use strict';

/**
 * Decodificador neutro do pedido versionado de leitura.
 * Endereço, largura, tamanho de registro, transformação e fingerprint chegam
 * exclusivamente do contrato retornado por clube_novo.
 */
(function installContractReader(global) {
  const decoder = new TextDecoder('utf-8');
  const SEAL_KEYS = Object.freeze([
    'contrato_id', 'versao_jogo', 'versao_contrato',
    'fingerprint_contrato_sha256', 'fingerprint_fontes_sha256', 'fingerprint_catalogos_sha256'
  ]);
  const SUPPORTED_READERS = new Set(['bitfield_le', 'byte_le', 'fixed_utf8_nul', 'id_mask', 'membership', 'all_str_parser']);
  const SUPPORTED_FILE_DECODERS = new Set(['wesys_raw', 'all_str_v1']);

  function requirePlan(plan) {
    if (!plan || typeof plan !== 'object') throw new Error('pedido de leitura ausente');
    for (const key of SEAL_KEYS) if (typeof plan[key] !== 'string' || !plan[key]) throw new Error(`pedido de leitura sem ${key}`);
    if (!Array.isArray(plan.arquivos) || !Array.isArray(plan.campos)) throw new Error('pedido de leitura sem arquivos/campos');
    const files = new Map();
    for (const file of plan.arquivos) {
      if (!file || !Number.isInteger(file.arquivo_id) || typeof file.arquivo !== 'string' || !file.arquivo || !SUPPORTED_FILE_DECODERS.has(file.decodificador)) throw new Error('arquivo inválido no pedido de leitura');
      if (files.has(file.arquivo_id)) throw new Error(`arquivo duplicado no pedido: ${file.arquivo_id}`);
      if (typeof file.sha256_arquivo !== 'string' || !/^[a-f0-9]{64}$/i.test(file.sha256_arquivo)) throw new Error(`fingerprint inválido para ${file.arquivo}`);
      if (file.tamanho_registro != null && (!Number.isInteger(file.tamanho_registro) || file.tamanho_registro <= 0)) throw new Error(`registro inválido para ${file.arquivo}`);
      files.set(file.arquivo_id, file);
    }
    const fields = new Map();
    for (const field of plan.campos) {
      if (!field || typeof field.chave_campo !== 'string' || !field.chave_campo || !files.has(field.arquivo_id)) throw new Error('campo sem arquivo canônico no pedido');
      if (!SUPPORTED_READERS.has(field.tipo_leitura)) throw new Error(`tipo de leitura não suportado: ${field.tipo_leitura}`);
      if (field.status_base !== 'comprovado' && field.status_base !== 'convencao_aprovada') throw new Error(`campo sem base aceita: ${field.chave_campo}`);
      if (typeof field.chave_familia !== 'string' || !field.chave_familia || typeof field.expected_type !== 'string' || !field.expected_type || typeof field.normalizador_id !== 'string' || !field.normalizador_id || !field.schema_payload || typeof field.schema_payload !== 'object' || !field.identidade_estavel || typeof field.identidade_estavel !== 'object') throw new Error(`campo sem semântica tipada: ${field.chave_campo}`);
      if (fields.has(field.chave_campo)) throw new Error(`campo duplicado no pedido: ${field.chave_campo}`);
      fields.set(field.chave_campo, field);
    }
    return { files, fields };
  }

  function readBitsLE(bytes, base, bit, width) {
    if (!Number.isInteger(bit) || !Number.isInteger(width) || bit < 0 || width <= 0 || width > 53) throw new Error('bitfield não tipado');
    if (base < 0 || base + Math.ceil((bit + width) / 8) > bytes.length) throw new Error('bitfield ultrapassa o registro');
    let value = 0;
    for (let index = 0; index < width; index += 1) {
      const absolute = bit + index;
      value += ((bytes[base + (absolute >> 3)] >> (absolute & 7)) & 1) * (2 ** index);
    }
    return value;
  }
  function readByteLE(bytes, start, width) {
    if (!Number.isInteger(start) || !Number.isInteger(width) || start < 0 || width <= 0 || width > 8 || start + width > bytes.length) throw new Error('inteiro little-endian não tipado');
    let value = 0n;
    for (let index = 0; index < width; index += 1) value |= BigInt(bytes[start + index]) << BigInt(index * 8);
    return value <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(value) : value.toString();
  }
  function readFixedUtf8(bytes, start, width) {
    if (!Number.isInteger(start) || !Number.isInteger(width) || start < 0 || width <= 0 || start + width > bytes.length) throw new Error('texto fixo não tipado');
    let end = start;
    while (end < start + width && bytes[end] !== 0) end += 1;
    return decoder.decode(bytes.subarray(start, end));
  }
  function sourceValue(values, origin) {
    if (Object.prototype.hasOwnProperty.call(values, origin)) return values[origin];
    if (origin === 'card_id' && Object.prototype.hasOwnProperty.call(values, 'carta.id')) return values['carta.id'];
    return undefined;
  }
  function rawValue(bytes, base, field, values) {
    switch (field.tipo_leitura) {
      case 'bitfield_le': return readBitsLE(bytes, base, field.bit_inicio, field.largura_bits);
      case 'byte_le': return readByteLE(bytes, base + field.byte_offset, field.largura_bytes);
      case 'fixed_utf8_nul': return readFixedUtf8(bytes, base + field.byte_offset, field.largura_bytes);
      case 'id_mask': {
        const transform = field.transformacao || {};
        const source = sourceValue(values, transform.origem);
        if (source == null || !Number.isInteger(transform.bit_inicio) || !Number.isInteger(transform.largura_bits)) throw new Error(`máscara sem origem tipada: ${field.chave_campo}`);
        return Number((BigInt(source) >> BigInt(transform.bit_inicio)) & ((1n << BigInt(transform.largura_bits)) - 1n));
      }
      case 'membership': {
        if (Number.isInteger(field.byte_offset) && Number.isInteger(field.largura_bytes)) return readByteLE(bytes, base + field.byte_offset, field.largura_bytes);
        return readBitsLE(bytes, base, field.bit_inicio, field.largura_bits);
      }
      case 'all_str_parser': throw new Error(`campo textual exige parser all.str: ${field.chave_campo}`);
      default: throw new Error(`tipo de leitura não implementado: ${field.tipo_leitura}`);
    }
  }
  function transformed(raw, field) {
    const transform = field.transformacao || {};
    if (Object.prototype.hasOwnProperty.call(transform, 'base')) return Number(raw) + Number(transform.base);
    if (transform.operacao === 'raw+100') return Number(raw) + 100;
    if (transform.operacao === 'raw+30') return Number(raw) + 30;
    if (transform.operacao === 'raw+10') return Number(raw) + 10;
    if (transform.operacao === 'floor(raw/2)') return Math.floor(Number(raw) / 2);
    if (transform.operacao === 'floor(raw/4)*4') return Math.floor(Number(raw) / 4) * 4;
    if (transform.operacao === 'high16') return (Number(raw) >>> 16) & 0xffff;
    if (transform.enum && typeof transform.enum === 'object') return transform.enum[String(raw)] ?? raw;
    return raw;
  }
  function assertExpectedType(value, field) {
    if (value == null) return value;
    const type = field.expected_type;
    if (type === 'integer' && !Number.isInteger(value)) throw new Error(`normalização não produziu inteiro: ${field.chave_campo}`);
    if (type === 'boolean' && typeof value !== 'boolean' && !Number.isInteger(value)) throw new Error(`normalização não produziu booleano: ${field.chave_campo}`);
    if (type === 'string' && typeof value !== 'string') throw new Error(`normalização não produziu texto: ${field.chave_campo}`);
    if (type === 'foreign_key' && !(Number.isInteger(value) || typeof value === 'string')) throw new Error(`normalização não produziu FK estável: ${field.chave_campo}`);
    return value;
  }
  async function sha256(bytes) {
    const hash = await crypto.subtle.digest('SHA-256', bytes);
    return Array.from(new Uint8Array(hash), (item) => item.toString(16).padStart(2, '0')).join('');
  }
  async function verifyFile(plan, fileName, bytes) {
    const index = requirePlan(plan);
    const file = [...index.files.values()].find((item) => item.arquivo === fileName);
    if (!file) throw new Error(`arquivo não solicitado pelo contrato: ${fileName}`);
    const actualHash = await sha256(bytes);
    if (actualHash !== file.sha256_arquivo.toLowerCase()) throw new Error(`fingerprint físico divergente: ${fileName}`);
    if (file.tamanho_registro != null && bytes.length % file.tamanho_registro !== 0) throw new Error(`tamanho físico incompatível: ${fileName}`);
    return { index, file, actualHash };
  }
  async function decodeFile(plan, fileName, bytes, fieldKeys = null) {
    const { index, file, actualHash } = await verifyFile(plan, fileName, bytes);
    if (file.decodificador !== 'wesys_raw') throw new Error(`decodificador não genérico: ${file.decodificador}`);
    if (!Number.isInteger(file.tamanho_registro) || file.tamanho_registro <= 0) throw new Error(`tamanho de registro ausente no contrato: ${fileName}`);
    const selected = fieldKeys == null ? null : new Set(fieldKeys);
    const fields = [...index.fields.values()].filter((field) => field.arquivo_id === file.arquivo_id && field.tipo_leitura !== 'all_str_parser' && (selected == null || selected.has(field.chave_campo))).sort((left, right) => left.chave_campo.localeCompare(right.chave_campo));
    if (!fields.length) throw new Error(`nenhum campo binário solicitado para ${fileName}`);
    const records = [];
    for (let base = 0, recordIndex = 0; base < bytes.length; base += file.tamanho_registro, recordIndex += 1) {
      const values = {};
      const envelope = [];
      for (const field of fields) {
        if (field.tipo_leitura === 'id_mask') continue;
        const raw = rawValue(bytes, base, field, values);
        const normalized = assertExpectedType(transformed(raw, field), field);
        values[field.chave_campo] = normalized;
        envelope.push({ chave_campo:field.chave_campo, familia:field.chave_familia, bruto:raw, normalizado:normalized, tipo_esperado:field.expected_type, normalizador:{id:field.normalizador_id,versao:field.versao_normalizador}, identidade:field.identidade_estavel, fk_destino:field.fk_destino || null, proveniencia:{arquivo:fileName,sha256_arquivo:actualHash,registro:recordIndex,tipo_leitura:field.tipo_leitura,byte_offset:field.byte_offset ?? null,bit_inicio:field.bit_inicio ?? null,largura_bits:field.largura_bits ?? null,largura_bytes:field.largura_bytes ?? null} });
      }
      for (const field of fields.filter((item) => item.tipo_leitura === 'id_mask')) {
        const raw = rawValue(bytes, base, field, values);
        const normalized = assertExpectedType(transformed(raw, field), field);
        values[field.chave_campo] = normalized;
        envelope.push({ chave_campo:field.chave_campo, familia:field.chave_familia, bruto:raw, normalizado:normalized, tipo_esperado:field.expected_type, normalizador:{id:field.normalizador_id,versao:field.versao_normalizador}, identidade:field.identidade_estavel, fk_destino:field.fk_destino || null, proveniencia:{arquivo:fileName,sha256_arquivo:actualHash,registro:recordIndex,tipo_leitura:field.tipo_leitura,byte_offset:field.byte_offset ?? null,bit_inicio:field.bit_inicio ?? null,largura_bits:field.largura_bits ?? null,largura_bytes:field.largura_bytes ?? null} });
      }
      records.push({ record_index: recordIndex, values, envelope });
    }
    return { selo: Object.fromEntries(SEAL_KEYS.map((key) => [key, plan[key]])), arquivo: fileName, sha256_arquivo: actualHash, tamanho_registro: file.tamanho_registro, records };
  }

  global.CLUBEF_CONTRACT_READER = Object.freeze({ SEAL_KEYS, requirePlan, readBitsLE, readByteLE, readFixedUtf8, verifyFile, decodeFile, sha256 });
})(globalThis);
