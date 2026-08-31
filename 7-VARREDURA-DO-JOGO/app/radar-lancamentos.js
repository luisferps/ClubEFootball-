'use strict';

/**
 * Radar observacional de boxes físicas.
 *
 * PlayerVariationDetail.bin liga card_id ao nome físico da box, mas esse
 * dado ainda não pertence ao contrato de escrita de clube_novo. Por isso o
 * radar gera um artefato local separado: ele nunca entra na identidade da
 * carta, nunca entra no pacote de aplicação e não decide publicação nem uso
 * no motor.
 */
(function installLaunchRadar(global) {
  const core = global.CLUBEF_CORE;
  if (!core) throw new Error('radar-lancamentos.js requer extrator-core.js');

  const CONTRACT_VERSION = 'clubef-radar-lancamentos-fisicos-v2';
  const PARSER_VERSION = 'player-variation-detail-168-v2';
  const RECORD_SIZE = 168;
  const NAME_OFFSET = 12;
  const MAX_CARD_ID = 1n << 50n;
  const HASH_RE = /^[0-9a-f]{64}$/;
  const VALID_STATES = new Set(['nova', 'ja_conhecida', 'sem_historico']);
  const IGNORED_CLASSIFICATIONS = new Set(['card_without_box_name', 'empty_padding_record', 'box_relation_card_absent_from_current_player']);

  function assert(condition, message) {
    if (!condition) throw new Error(message);
  }
  function u32(bytes, offset) {
    return (bytes[offset] | (bytes[offset + 1] << 8) | (bytes[offset + 2] << 16) | (bytes[offset + 3] << 24)) >>> 0;
  }
  function u64String(bytes, offset) {
    return (BigInt(u32(bytes, offset)) | (BigInt(u32(bytes, offset + 4)) << 32n)).toString();
  }
  function normalizedBoxName(value) {
    return String(value || '').normalize('NFC').trim().replace(/\s+/g, ' ').toLocaleLowerCase('pt-BR');
  }
  function sortedCardIds(values) {
    return [...values].map(String).sort((left, right) => {
      const a = BigInt(left), b = BigInt(right);
      return a < b ? -1 : (a > b ? 1 : 0);
    });
  }
  function nonZeroOffsets(bytes) {
    const output = [];
    for (let index = 0; index < bytes.length; index += 1) if (bytes[index] !== 0) output.push(index);
    return output;
  }

  /**
   * Parser fail-closed do layout físico comprovado: u64 LE no offset 0 e
   * nome UTF-8 terminado em NUL a partir do offset 12, registro de 168 bytes.
   */
  function parsePlayerVariationDetail(raw) {
    assert(raw instanceof Uint8Array, 'PlayerVariationDetail.bin precisa ser fornecido como bytes.');
    assert(raw.length > 0, 'PlayerVariationDetail.bin está vazio.');
    assert(raw.length % RECORD_SIZE === 0, `PlayerVariationDetail.bin incompatível: ${raw.length} bytes não formam registros de ${RECORD_SIZE}.`);
    const decoder = new TextDecoder('utf-8', { fatal: true });
    const records = [];
    const ignoredRecords = [];
    const seenCardIds = new Set();
    for (let offset = 0, recordIndex = 0; offset < raw.length; offset += RECORD_SIZE, recordIndex += 1) {
      const cardId = u64String(raw, offset);
      const region = raw.subarray(offset + NAME_OFFSET, offset + RECORD_SIZE);
      const terminator = region.indexOf(0);
      assert(terminator >= 0, `PlayerVariationDetail.bin registro ${recordIndex}: nome sem terminador NUL.`);
      let boxName;
      try {
        boxName = decoder.decode(region.subarray(0, terminator)).normalize('NFC').trim().replace(/\s+/g, ' ');
      } catch (_) {
        throw new Error(`PlayerVariationDetail.bin registro ${recordIndex}: nome não é UTF-8 válido.`);
      }
      const emptyId = cardId === '0';
      const emptyName = boxName.length === 0;
      const recordBytes = raw.slice(offset, offset + RECORD_SIZE);
      const recordAllZero = recordBytes.every((value) => value === 0);
      const tailAfterIdAllZero = recordBytes.subarray(8).every((value) => value === 0);
      if (emptyId && emptyName) {
        assert(recordAllZero, `PlayerVariationDetail.bin registro ${recordIndex}: registro sem identidade contém dados residuais não comprovados.`);
        ignoredRecords.push({
          classification: 'empty_padding_record',
          card_id: null,
          record_index: recordIndex,
          byte_offset: offset,
          record_bytes: recordBytes,
          nonzero_offsets: [],
          name_region_all_zero: true,
          record_tail_after_id_all_zero: true,
          meaning: 'Registro físico inteiramente vazio; tratado somente como espaço sem relação card/box.',
          affects_today: 'Não. Ele não identifica card nem box e não entra nas contagens de lançamentos.',
          operator_action: 'Nenhuma ação. O Extrator guarda a evidência local e continua a leitura.',
          publication_eligible: false,
          radar_relation_eligible: false,
          package_eligible: false,
          database_write: false
        });
        continue;
      }
      assert(!(emptyId && !emptyName), `PlayerVariationDetail.bin registro ${recordIndex}: existe nome de box sem card_id; a relação física não pode ser comprovada.`);
      const numericId = BigInt(cardId);
      assert(numericId > 0n && numericId < MAX_CARD_ID, `PlayerVariationDetail.bin registro ${recordIndex}: card_id fora do domínio físico.`);
      assert(!seenCardIds.has(cardId), `PlayerVariationDetail.bin contém card_id duplicado: ${cardId}.`);
      seenCardIds.add(cardId);
      if (emptyName) {
        assert(tailAfterIdAllZero, `PlayerVariationDetail.bin registro ${recordIndex}: card_id sem nome de box contém dados residuais não comprovados.`);
        ignoredRecords.push({
          classification: 'card_without_box_name',
          card_id: cardId,
          record_index: recordIndex,
          byte_offset: offset,
          record_bytes: recordBytes,
          nonzero_offsets: nonZeroOffsets(recordBytes),
          name_region_all_zero: true,
          record_tail_after_id_all_zero: true,
          meaning: 'O arquivo físico identifica o card, mas não atribui nenhum nome de box a este registro.',
          affects_today: 'Somente este registro não pode ser usado para anunciar ou relacionar uma box. As relações card/box completas continuam válidas.',
          operator_action: 'Não invente uma box. Aguarde uma futura varredura; se a Konami preencher o nome, o card entrará normalmente no radar.',
          publication_eligible: false,
          radar_relation_eligible: false,
          package_eligible: false,
          database_write: false
        });
        continue;
      }
      assert(!/[\u0000-\u001f\u007f]/u.test(boxName), `PlayerVariationDetail.bin registro ${recordIndex}: nome da box contém caractere de controle.`);
      records.push({
        card_id: cardId,
        nome_box_fisico: boxName,
        record_index: recordIndex,
        byte_offset: offset,
        record_bytes: recordBytes
      });
    }
    assert(records.length > 0, 'PlayerVariationDetail.bin não contém relações card/box utilizáveis.');
    return { records, ignored_records: ignoredRecords };
  }

  function sanitizeSource(source) {
    assert(source && typeof source === 'object', 'Radar de boxes sem proveniência da fonte.');
    assert(typeof source.role === 'string' && source.role, 'Radar de boxes sem papel da fonte.');
    if (source.cpk_sha256 != null) assert(HASH_RE.test(String(source.cpk_sha256)), 'Fingerprint do CPK inválido no radar de boxes.');
    return {
      role: source.role,
      cpk_file: source.cpk_file || null,
      location: source.location || null,
      bytes: source.bytes != null && Number.isFinite(Number(source.bytes)) ? Number(source.bytes) : null,
      modified_at: source.modified_at || null,
      cpk_sha256: source.cpk_sha256 || null
    };
  }

  async function observeRaw(raw, metadata) {
    const parsed = parsePlayerVariationDetail(raw);
    const records = await Promise.all(parsed.records.map(async (record) => {
      const { record_bytes: recordBytes, ...evidence } = record;
      return { ...evidence, record_sha256: await core.sha256(recordBytes) };
    }));
    const ignoredRecords = await Promise.all(parsed.ignored_records.map(async (record) => {
      const { record_bytes: recordBytes, ...evidence } = record;
      return { ...evidence, record_sha256: await core.sha256(recordBytes) };
    }));
    const rawSha256 = await core.sha256(raw);
    if (metadata?.member?.raw_sha256) {
      assert(rawSha256 === metadata.member.raw_sha256, 'Fingerprint descompactado de PlayerVariationDetail.bin divergente.');
    }
    return {
      parser: { version: PARSER_VERSION, record_size: RECORD_SIZE, name_offset: NAME_OFFSET, encoding: 'utf-8-nul' },
      source: sanitizeSource(metadata?.source),
      member: {
        file: core.BOX_RADAR_MEMBER || 'PlayerVariationDetail.bin',
        packed_bytes: metadata?.member?.packed_bytes ?? null,
        packed_sha256: metadata?.member?.packed_sha256 || null,
        raw_bytes: raw.length,
        raw_sha256: rawSha256,
        records_total: raw.length / RECORD_SIZE,
        relations_valid: records.length,
        records_ignored: ignoredRecords.length,
        ignored_by_classification: ignoredRecords.reduce((counts, record) => {
          counts[record.classification] = (counts[record.classification] || 0) + 1;
          return counts;
        }, {})
      },
      contract_verification: metadata?.contract_verification || null,
      records,
      ignored_records: ignoredRecords
    };
  }

  async function observeCpk(bytes, metadata) {
    assert(bytes instanceof Uint8Array, 'CPK do radar precisa ser fornecido como bytes.');
    const cpkSha256 = await core.sha256(bytes);
    const declaredSha256 = metadata?.source?.cpk_sha256 || null;
    if (declaredSha256) assert(cpkSha256 === declaredSha256, 'Fingerprint do CPK divergente antes da leitura de boxes.');
    const member = await core.extractPlayerVariationDetailMember(bytes);
    return observeRaw(member.raw, {
      ...metadata,
      source: { ...(metadata?.source || {}), cpk_sha256: cpkSha256, bytes: bytes.length },
      member
    });
  }

  function validateRadarStructure(radar) {
    assert(radar && typeof radar === 'object', 'Artefato anterior do radar ausente ou inválido.');
    assert(radar.contract === CONTRACT_VERSION, 'Artefato anterior usa outro contrato de radar.');
    assert(radar.database_write === false && radar.read_only === true, 'Artefato anterior não comprova leitura somente local.');
    assert(radar.parser?.version === PARSER_VERSION && radar.parser?.record_size === RECORD_SIZE, 'Artefato anterior usa outro layout físico de boxes.');
    assert(Array.isArray(radar.boxes), 'Artefato anterior não contém lista de boxes.');
    assert(radar.provenance?.source?.role, 'Artefato anterior não informa o papel da fonte.');
    assert(radar.provenance?.member?.file === (core.BOX_RADAR_MEMBER || 'PlayerVariationDetail.bin'), 'Artefato anterior não veio de PlayerVariationDetail.bin.');
    assert(Array.isArray(radar.ignored_records), 'Artefato anterior não preserva os registros físicos ignorados.');
    const identities = new Set();
    const allCards = new Set();
    const counts = { nova: 0, ja_conhecida: 0, sem_historico: 0 };
    for (const box of radar.boxes) {
      assert(VALID_STATES.has(box.estado), `Estado de box inválido: ${box.estado}.`);
      assert(HASH_RE.test(String(box.fingerprint_identidade || '')), 'Box sem fingerprint de identidade válido.');
      assert(HASH_RE.test(String(box.fingerprint_box || '')), 'Box sem fingerprint de conteúdo válido.');
      assert(!identities.has(box.fingerprint_identidade), 'Artefato contém box duplicada por identidade.');
      identities.add(box.fingerprint_identidade);
      assert(Array.isArray(box.cartas) && box.cartas.length === box.quantidade_cartas, `Quantidade de cards inconsistente na box ${box.nome_box}.`);
      for (const card of box.cartas) {
        const key = String(card.card_id);
        assert(!allCards.has(key), `Artefato relaciona o card ${key} a mais de uma box.`);
        assert(HASH_RE.test(String(card.record_sha256 || '')), `Card ${key} ficou sem hash do registro físico da box.`);
        allCards.add(key);
      }
      counts[box.estado] += 1;
    }
    const ignoredKeys = new Set();
    const ignoredCounts = {};
    for (const record of radar.ignored_records) {
      assert(IGNORED_CLASSIFICATIONS.has(record.classification), `Classificação de registro ignorado inválida: ${record.classification}.`);
      assert(Number.isInteger(record.record_index) && record.record_index >= 0, 'Registro ignorado sem índice físico válido.');
      assert(Number.isInteger(record.byte_offset) && record.byte_offset === record.record_index * RECORD_SIZE, 'Registro ignorado com offset físico inconsistente.');
      assert(HASH_RE.test(String(record.record_sha256 || '')), 'Registro ignorado sem fingerprint físico válido.');
      assert(record.publication_eligible === false && record.radar_relation_eligible === false && record.package_eligible === false && record.database_write === false, 'Registro ignorado ganhou destino indevido.');
      if (record.classification === 'card_without_box_name') {
        assert(record.card_id != null && record.name_region_all_zero === true && record.record_tail_after_id_all_zero === true, 'Registro de card sem box não comprova a região física vazia.');
      } else if (record.classification === 'empty_padding_record') {
        assert(record.card_id == null && record.name_region_all_zero === true, 'Registro vazio contém identidade ou nome indevido.');
      } else if (record.classification === 'box_relation_card_absent_from_current_player') {
        assert(record.card_id != null && typeof record.nome_box_fisico === 'string' && record.nome_box_fisico.length > 0, 'Relação física antiga perdeu card ou nome de box.');
        assert(record.card_join_checked === true && record.card_present_in_current_player === false, 'Relação física antiga não comprova ausência no Player.bin atual.');
      }
      if (record.card_id != null && radar.provenance?.card_join_checked === true) {
        assert(typeof record.card_present_in_current_player === 'boolean', 'Registro ignorado não informa se o card existe no Player.bin atual.');
      }
      const ignoredKey = `${record.record_index}:${record.record_sha256}`;
      assert(!ignoredKeys.has(ignoredKey), 'Artefato contém evidência ignorada duplicada.');
      ignoredKeys.add(ignoredKey);
      if (record.card_id != null) assert(!allCards.has(String(record.card_id)), `Card ignorado ${record.card_id} entrou também em uma box.`);
      ignoredCounts[record.classification] = (ignoredCounts[record.classification] || 0) + 1;
    }
    assert(radar.counts?.boxes === radar.boxes.length, 'Contagem total de boxes inconsistente.');
    assert(radar.counts?.cards_mapped === allCards.size, 'Contagem total de cards do radar inconsistente.');
    assert(radar.counts?.records_ignored === radar.ignored_records.length, 'Contagem de registros ignorados inconsistente.');
    assert(radar.counts?.ignored_absent_from_current_player === radar.ignored_records.filter((record) => record.card_id != null && record.card_present_in_current_player === false).length, 'Contagem de registros sem card no Player.bin atual inconsistente.');
    for (const classification of IGNORED_CLASSIFICATIONS) {
      assert((radar.counts?.ignored_by_classification?.[classification] || 0) === (ignoredCounts[classification] || 0), `Contagem ignorada de ${classification} inconsistente.`);
    }
    assert(radar.provenance?.member?.records_total === radar.provenance?.member?.relations_valid + radar.provenance?.member?.records_ignored, 'Total físico não fecha entre relações de layout válido e registros ignorados pelo parser.');
    const absentBoxes = radar.comparison?.boxes_ausentes_desde_anterior;
    assert(Array.isArray(absentBoxes), 'Comparação não informa as boxes ausentes desde a rodada anterior.');
    assert(radar.counts?.boxes_ausentes_desde_anterior === absentBoxes.length, 'Contagem de boxes ausentes inconsistente.');
    assert(absentBoxes.every((box) => box.database_write === false), 'Uma box ausente acionou exclusão automática indevida.');
    for (const state of VALID_STATES) assert(radar.counts?.by_state?.[state] === counts[state], `Contagem do estado ${state} inconsistente.`);
    assert(radar.apply_scope?.radar_fields_included === false && radar.apply_scope?.ignored_records_included === false && radar.apply_scope?.destination === null, 'Dados observacionais de box entraram indevidamente no destino de aplicação.');
    assert(radar.publication_decision?.evaluated === false && radar.publication_decision?.blocked === false, 'Radar de boxes decidiu ou bloqueou publicação de card indevidamente.');
    assert(radar.publication_decision?.ignored_records_evaluated === true && radar.publication_decision?.ignored_records_publishable === false, 'Registros sem box ganharam permissão de publicação indevida.');
    assert(radar.integration_contract?.status === 'prepared_not_enabled', 'Envelope do radar não está preparado para integração futura.');
    assert(radar.integration_contract?.write_enabled === false && radar.integration_contract?.current_destination === null, 'Integração futura de boxes foi habilitada sem migração.');
    return true;
  }

  function comparability(previous, observation) {
    if (!previous) return { comparable: false, reason: 'Nenhuma rodada anterior do radar foi encontrada.' };
    try {
      validateRadarStructure(previous);
    } catch (error) {
      return { comparable: false, reason: String(error.message || error) };
    }
    if (previous.provenance.source.role !== observation.source.role) {
      return { comparable: false, reason: 'A rodada anterior usou outro papel de fonte.' };
    }
    if (previous.provenance.member.file !== observation.member.file) {
      return { comparable: false, reason: 'A rodada anterior usou outro membro físico.' };
    }
    return { comparable: true, reason: 'Mesmo papel de fonte, membro físico e versão de parser.' };
  }

  async function groupBoxes(observation, cards) {
    const cardMap = new Map();
    if (cards != null) {
      assert(Array.isArray(cards), 'Lista canônica de cards inválida para conferir o radar.');
      for (const card of cards) {
        const id = String(card.card_id);
        assert(!cardMap.has(id), `Lista canônica contém card_id duplicado: ${id}.`);
        cardMap.set(id, card);
      }
    }
    const groups = new Map();
    for (const record of observation.records) {
      if (cards != null) assert(cardMap.has(record.card_id), `A box física aponta para card_id ausente em Player.bin: ${record.card_id}.`);
      const key = normalizedBoxName(record.nome_box_fisico);
      assert(key, `Nome normalizado da box ficou vazio no registro ${record.record_index}.`);
      if (!groups.has(key)) groups.set(key, { key, display_names: new Set(), records: [] });
      const group = groups.get(key);
      group.display_names.add(record.nome_box_fisico);
      group.records.push(record);
    }
    const output = [];
    for (const group of groups.values()) {
      const names = [...group.display_names].sort((a, b) => a.localeCompare(b, 'pt-BR'));
      const cardIds = sortedCardIds(group.records.map((record) => record.card_id));
      const recordsById = new Map(group.records.map((record) => [record.card_id, record]));
      const identityFingerprint = await core.sha256(`box-identity-v1\u0000${group.key}`);
      const boxFingerprint = await core.sha256(core.stableJson({ normalized_name: group.key, card_ids: cardIds }));
      output.push({
        nome_box: names[0],
        nomes_fisicos_observados: names,
        nome_normalizado: group.key,
        fingerprint_identidade: identityFingerprint,
        fingerprint_box: boxFingerprint,
        quantidade_cartas: cardIds.length,
        cartas: cardIds.map((cardId) => {
          const source = recordsById.get(cardId);
          const card = cardMap.get(cardId);
          return {
            card_id: cardId,
            nome_card: card ? String(card.name || card.nome || '') || null : null,
            record_index: source.record_index,
            byte_offset: source.byte_offset,
            record_sha256: source.record_sha256
          };
        })
      });
    }
    return output.sort((a, b) => a.nome_normalizado.localeCompare(b.nome_normalizado, 'pt-BR'));
  }

  async function buildRadar(observation, previous, options = {}) {
    assert(observation && Array.isArray(observation.records) && Array.isArray(observation.ignored_records), 'Observação física de boxes inválida.');
    const canonicalCardIds = options.cards != null
      ? new Set(options.cards.map((card) => String(card.card_id)))
      : null;
    const parserIgnoredRecords = observation.ignored_records.map((record) => ({
      ...record,
      card_join_checked: canonicalCardIds != null,
      card_present_in_current_player: record.card_id == null || canonicalCardIds == null
        ? null
        : canonicalCardIds.has(String(record.card_id))
    }));
    const absentCurrentCardRecords = canonicalCardIds == null
      ? []
      : observation.records.filter((record) => !canonicalCardIds.has(String(record.card_id))).map((record) => ({
        classification: 'box_relation_card_absent_from_current_player',
        card_id: record.card_id,
        nome_box_fisico: record.nome_box_fisico,
        record_index: record.record_index,
        byte_offset: record.byte_offset,
        record_sha256: record.record_sha256,
        meaning: 'O arquivo de boxes contém uma relação completa, mas o card não existe no Player.bin atual da mesma rodada.',
        affects_today: 'Não entra no Radar atual porque não identifica um card disponível na base física atual do jogo.',
        operator_action: 'Nenhuma ação manual. Preserve como referência física histórica e não recrie o card por tentativa.',
        publication_eligible: false,
        radar_relation_eligible: false,
        package_eligible: false,
        database_write: false,
        card_join_checked: true,
        card_present_in_current_player: false
      }));
    const ignoredRecords = [...parserIgnoredRecords, ...absentCurrentCardRecords];
    const groupingObservation = canonicalCardIds == null
      ? observation
      : { ...observation, records: observation.records.filter((record) => canonicalCardIds.has(String(record.card_id))) };
    const currentBoxes = await groupBoxes(groupingObservation, options.cards);
    const comparable = comparability(previous, observation);
    const previousByIdentity = new Map(comparable.comparable ? previous.boxes.map((box) => [box.fingerprint_identidade, box]) : []);
    const boxes = currentBoxes.map((box) => {
      const old = previousByIdentity.get(box.fingerprint_identidade) || null;
      const previousIds = new Set(old ? old.cartas.map((card) => String(card.card_id)) : []);
      const currentIds = new Set(box.cartas.map((card) => String(card.card_id)));
      const added = sortedCardIds([...currentIds].filter((id) => !previousIds.has(id)));
      const absent = sortedCardIds([...previousIds].filter((id) => !currentIds.has(id)));
      const state = comparable.comparable ? (old ? 'ja_conhecida' : 'nova') : 'sem_historico';
      return {
        ...box,
        estado: state,
        explicacao_estado: state === 'nova'
          ? 'Este nome de box não existia na última rodada comparável.'
          : (state === 'ja_conhecida'
            ? 'Este nome de box já existia na última rodada comparável.'
            : 'Ainda não existe uma rodada anterior comparável; esta primeira leitura vira a referência local.'),
        conteudo_alterado: old ? old.fingerprint_box !== box.fingerprint_box : null,
        cards_adicionados_desde_anterior: old ? added : [],
        cards_ausentes_desde_anterior: old ? absent : [],
        database_write: false
      };
    });
    const currentIdentities = new Set(boxes.map((box) => box.fingerprint_identidade));
    const absentBoxes = comparable.comparable
      ? previous.boxes.filter((box) => !currentIdentities.has(box.fingerprint_identidade)).map((box) => ({
        nome_box: box.nome_box,
        fingerprint_identidade: box.fingerprint_identidade,
        fingerprint_box_anterior: box.fingerprint_box,
        quantidade_cartas_anterior: box.quantidade_cartas,
        meaning: 'A box existia na rodada anterior e não está no arquivo físico atual; o radar não executa exclusão automática.',
        database_write: false
      }))
      : [];
    const byState = { nova: 0, ja_conhecida: 0, sem_historico: 0 };
    for (const box of boxes) byState[box.estado] += 1;
    const radarFingerprint = await core.sha256(core.stableJson({
      contract: CONTRACT_VERSION,
      parser: observation.parser,
      source_role: observation.source.role,
      member_raw_sha256: observation.member.raw_sha256,
      boxes: boxes.map((box) => ({
        fingerprint_identidade: box.fingerprint_identidade,
        fingerprint_box: box.fingerprint_box,
        estado: box.estado
      })),
      boxes_ausentes_desde_anterior: absentBoxes.map((box) => box.fingerprint_identidade),
      ignored_records: ignoredRecords.map((record) => ({
        classification: record.classification,
        card_id: record.card_id,
        record_index: record.record_index,
        record_sha256: record.record_sha256,
        card_present_in_current_player: record.card_present_in_current_player
      }))
    }));
    const artifact = {
      contract: CONTRACT_VERSION,
      generated_at: options.generated_at || new Date().toISOString(),
      database_write: false,
      read_only: true,
      evidence_mode: observation.contract_verification?.evidence_mode || 'physical_runtime',
      radar_fingerprint: radarFingerprint,
      parser: observation.parser,
      meaning: 'Radar local de boxes pré-carregadas fisicamente; não confirma que a box já apareceu na tela do jogo.',
      publication_decision: {
        evaluated: false,
        blocked: false,
        reason: 'O radar informa a box física, mas não autoriza nem impede publicar ou selecionar o card no site.',
        ignored_records_evaluated: true,
        ignored_records_publishable: false,
        ignored_records_reason: 'Um registro sem relação card/box atual comprovada não comprova um lançamento e permanece fora do radar publicável.'
      },
      motor_decision: {
        evaluated: false,
        reason: 'Completude e elegibilidade para Motor/Otimizador/Bonificador são avaliadas por outra etapa.'
      },
      apply_scope: {
        radar_fields_included: false,
        ignored_records_included: false,
        destination: null,
        reason: 'Box é observação local fora da identidade canônica e fora do pacote de aplicação enquanto não houver contrato/migração próprios.'
      },
      integration_contract: {
        version: 'clubef-box-observation-envelope-v1',
        status: 'prepared_not_enabled',
        database_migration_required: true,
        write_enabled: false,
        current_destination: null,
        box_identity_fields: ['fingerprint_identidade'],
        card_box_relation_identity_fields: ['card_id', 'fingerprint_identidade'],
        payload_fields: ['nome_box', 'nome_normalizado', 'fingerprint_identidade', 'fingerprint_box', 'card_id', 'record_index', 'byte_offset'],
        required_provenance: ['source.role', 'source.cpk_sha256', 'member.raw_sha256', 'parser.version'],
        note: 'O envelope está estável para uma migração futura, mas nenhuma tabela, RPC, trigger ou escrita foi ativada por este radar.'
      },
      comparison: {
        status: comparable.comparable ? 'comparado' : 'sem_historico_comparavel',
        reason: comparable.reason,
        previous_artifact: comparable.comparable ? (options.previous_artifact || null) : null,
        previous_generated_at: comparable.comparable ? previous.generated_at : null,
        previous_radar_fingerprint: comparable.comparable ? previous.radar_fingerprint : null,
        boxes_ausentes_desde_anterior: absentBoxes
      },
      counts: {
        boxes: boxes.length,
        cards_mapped: boxes.reduce((sum, box) => sum + box.quantidade_cartas, 0),
        records_ignored: ignoredRecords.length,
        ignored_absent_from_current_player: ignoredRecords.filter((record) => record.card_id != null && record.card_present_in_current_player === false).length,
        ignored_by_classification: ignoredRecords.reduce((counts, record) => {
          counts[record.classification] = (counts[record.classification] || 0) + 1;
          return counts;
        }, {}),
        boxes_ausentes_desde_anterior: absentBoxes.length,
        by_state: byState
      },
      provenance: {
        source: observation.source,
        member: observation.member,
        contract_verification: observation.contract_verification,
        card_join_checked: options.cards != null,
        card_join_source: options.cards != null ? 'cartas-fisicas-canonicas.json / Player.bin da mesma rodada' : null
      },
      ignored_records: ignoredRecords,
      boxes
    };
    validateRadarStructure(artifact);
    return artifact;
  }

  global.CLUBEF_BOX_RADAR = Object.freeze({
    CONTRACT_VERSION,
    PARSER_VERSION,
    RECORD_SIZE,
    NAME_OFFSET,
    normalizedBoxName,
    parsePlayerVariationDetail,
    observeRaw,
    observeCpk,
    comparability,
    validateRadarStructure,
    buildRadar
  });
})(globalThis);
