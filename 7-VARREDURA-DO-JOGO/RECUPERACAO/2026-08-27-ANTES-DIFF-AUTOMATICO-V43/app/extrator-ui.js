'use strict';

(function installUi(global) {
  const core = global.CLUBEF_CORE;
  const state = {
    executor: { online: false, write_enabled: false, mode: 'offline' },
    sources: {},
    reference: { status: 'loading' },
    pendingSourceRole: null,
    incremental: null,
    metadata: null,
    full: null,
    cardPackage: null,
    approvals: {}
  };
  const $ = (id) => document.getElementById(id);
  const escapeHtml = (value) => String(value == null ? '' : value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));
  const SOURCE_SPECS = Object.freeze({
    dt870_updated: { label: 'DT870 da atualização', filename: 'dt870_console_win.cpk', purpose: 'Cartas atuais; habilidades; ímpetos atuais; overlay de playstyles.', operations: 'Cartas e catálogos' },
    dt200: { label: 'DT200 base', filename: 'dt200_console_all.cpk', purpose: 'Base semântica de playstyles e ímpetos legados.', operations: 'Somente catálogos' },
    dt870_original: { label: 'DT870 original', filename: 'dt870_console_win.cpk', purpose: 'Ímpetos legados exclusivos e conferência histórica.', operations: 'Somente catálogos' },
    dt261_bra: { label: 'Textos em português', filename: 'dt261_bra_console_win.cpk', purpose: 'all.str e catálogos textuais.', operations: 'Somente catálogos' }
  });
  const CARD_SOURCE_ROLES = Object.freeze(['dt870_updated']);
  const METADATA_SOURCE_ROLES = Object.freeze(['dt870_updated', 'dt200', 'dt870_original', 'dt261_bra']);

  function log(id, message, reset = false) {
    const element = $(id);
    element.hidden = false;
    if (reset) element.textContent = '';
    element.textContent += `${message}\n`;
    element.scrollTop = element.scrollHeight;
  }
  function setStats(id, items) {
    $(id).innerHTML = items.map(([label, value]) => `<div class="stat"><b>${escapeHtml(value)}</b><span>${escapeHtml(label)}</span></div>`).join('');
  }
  function download(name, content, type = 'application/octet-stream') {
    const url = URL.createObjectURL(new Blob([content], { type }));
    const anchor = document.createElement('a');
    anchor.href = url; anchor.download = name; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  }
  function setFileName(inputId, nameId) {
    const file = $(inputId).files[0];
    $(nameId).textContent = file ? `${file.name} · ${file.size.toLocaleString('pt-BR')} bytes` : 'Nenhum arquivo escolhido';
    return file;
  }
  function showPane(name) {
    document.querySelectorAll('.tab').forEach((tab) => tab.classList.toggle('active', tab.dataset.pane === name));
    document.querySelectorAll('.pane').forEach((pane) => pane.classList.toggle('active', pane.id === `pane-${name}`));
  }
  document.querySelectorAll('.tab').forEach((tab) => tab.addEventListener('click', () => showPane(tab.dataset.pane)));

  async function refreshExecutorStatus() {
    try {
      const response = await fetch('/api/status', { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      state.executor = await response.json();
      state.executor.online = true;
      $('executor-dot').className = `dot ${state.executor.manual_apply_available ? 'ok' : 'neutral'}`;
      $('executor-title').textContent = state.executor.manual_apply_available ? 'Banco conectado · envio manual' : 'Executor local · modo protegido';
      $('executor-detail').textContent = state.executor.manual_apply_available ? 'destino único: clube_novo; nenhuma escrita automática' : 'banco sem conexão; extração continua disponível';
    } catch (error) {
      state.executor = { online: false, write_enabled: false, mode: 'offline' };
      $('executor-dot').className = 'dot neutral';
      $('executor-title').textContent = 'Executor local desconectado';
      $('executor-detail').textContent = 'extração funciona; aplicação indisponível';
    }
  }

  function sourceIsReady(role) { return Boolean(state.sources[role] && state.sources[role].status === 'ready'); }
  function operationIsReady(roles) { return roles.every(sourceIsReady); }
  async function fetchReferenceStatus() {
    const response = await fetch('/api/card-reference/status', { cache: 'no-store' });
    const payload = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
    if (!response.ok || !payload.ready) throw new Error(payload.error || 'A referência interna não pôde ser validada.');
    return payload;
  }
  function renderReference() {
    const element = $('full-reference-name');
    if (!element) return;
    if (state.reference.status === 'ready') {
      const output = state.reference.output || {};
      element.textContent = `Referência validada · ${Number(output.records || 0).toLocaleString('pt-BR')} cartas · versões anteriores preservadas`;
    } else if (state.reference.status === 'blocked') {
      element.textContent = `Validação bloqueada: ${state.reference.error}`;
    } else {
      element.textContent = 'Verificando a referência versionada…';
    }
    enableFull();
  }
  async function refreshCardReference() {
    state.reference = { status: 'loading' };
    renderReference();
    try {
      state.reference = { ...(await fetchReferenceStatus()), status: 'ready' };
    } catch (error) {
      state.reference = { status: 'blocked', error: error.message };
    }
    renderReference();
  }
  function sourceDescriptor(role) {
    const source = state.sources[role];
    return {
      role,
      label: SOURCE_SPECS[role].label,
      file: source.name,
      bytes: source.bytes.length,
      sha256: source.sha256,
      origin: source.origin,
      modified_at: source.modifiedAt || null,
      validation: source.validation
    };
  }
  function renderSources() {
    $('source-list').innerHTML = Object.entries(SOURCE_SPECS).map(([role, spec]) => {
      const source = state.sources[role] || { status: 'missing', reason: 'Ainda não localizado.' };
      const status = source.status === 'ready' ? ['ok', 'Encontrado'] : (source.status === 'loading' ? ['loading', 'Validando'] : ['missing', 'Não encontrado']);
      const detail = source.status === 'ready'
        ? `${source.name} · ${source.bytes.length.toLocaleString('pt-BR')} bytes · ${source.origin === 'automatic' ? 'localizado automaticamente' : 'pasta escolhida'}`
        : (source.reason || `Escolha a pasta que contém ${spec.filename}.`);
      const choose = source.status === 'ready' ? '' : `<button class="secondary source-pick" type="button" data-source-role="${role}">Escolher somente esta pasta</button>`;
      return `<div class="source-item"><div><b>${escapeHtml(spec.label)}</b><small>${escapeHtml(spec.operations)}</small></div><span class="source-status ${status[0]}">${status[1]}</span><p>${escapeHtml(spec.purpose)}<br>${escapeHtml(detail)}</p>${choose}</div>`;
    }).join('');
    const cardsReady = operationIsReady(CARD_SOURCE_ROLES);
    const metadataMissing = METADATA_SOURCE_ROLES.filter((role) => !sourceIsReady(role));
    $('inc-source-name').textContent = cardsReady ? 'DT870 da atualização encontrado e validado' : 'Falta o DT870 da atualização';
    $('full-source-name').textContent = $('inc-source-name').textContent;
    $('meta-source-name').textContent = metadataMissing.length
      ? `Faltam ${metadataMissing.length} fonte(s): ${metadataMissing.map((role) => SOURCE_SPECS[role].label).join(', ')}`
      : 'As quatro fontes foram encontradas e validadas por papel';
    updateRunAvailability();
  }
  function updateRunAvailability() {
    $('run-incremental').disabled = !($('inc-base').files[0] && operationIsReady(CARD_SOURCE_ROLES));
    $('run-metadata').disabled = !($('meta-base').files[0] && operationIsReady(METADATA_SOURCE_ROLES));
    enableFull();
  }
  async function registerSource(role, bytes, details) {
    state.sources[role] = { status: 'loading' };
    renderSources();
    const validation = await core.validateSourceForRole(bytes, role);
    state.sources[role] = {
      status: 'ready',
      bytes,
      name: details.name || SOURCE_SPECS[role].filename,
      modifiedAt: details.modifiedAt || null,
      origin: details.origin,
      sha256: await core.sha256(bytes),
      validation
    };
    renderSources();
  }
  async function refreshSources() {
    for (const role of Object.keys(SOURCE_SPECS)) state.sources[role] = { status: 'loading' };
    renderSources();
    try {
      const response = await fetch('/api/sources/status', { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const discovery = await response.json();
      for (const role of Object.keys(SOURCE_SPECS)) {
        const found = discovery.sources && discovery.sources[role];
        if (!found || !found.found) {
          state.sources[role] = { status: 'missing', reason: found && found.reason ? found.reason : 'Fonte não encontrada nos locais conhecidos.' };
          renderSources();
          continue;
        }
        try {
          const fileResponse = await fetch(`/api/sources/file?role=${encodeURIComponent(role)}`, { cache: 'no-store' });
          if (!fileResponse.ok) throw new Error(`HTTP ${fileResponse.status}`);
          await registerSource(role, new Uint8Array(await fileResponse.arrayBuffer()), { name: found.filename, modifiedAt: found.modified_at, origin: 'automatic' });
        } catch (error) {
          state.sources[role] = { status: 'missing', reason: `Arquivo localizado, mas inválido para esta função: ${error.message}` };
          renderSources();
        }
      }
    } catch (error) {
      for (const role of Object.keys(SOURCE_SPECS)) state.sources[role] = { status: 'missing', reason: 'A busca automática não respondeu. Escolha apenas a pasta desta fonte.' };
      renderSources();
    }
    await refreshCardReference();
  }

  $('refresh-sources').addEventListener('click', refreshSources);
  $('source-list').addEventListener('click', (event) => {
    const button = event.target.closest('[data-source-role]');
    if (!button) return;
    state.pendingSourceRole = button.dataset.sourceRole;
    $('source-folder-picker').value = '';
    $('source-folder-picker').click();
  });
  $('source-folder-picker').addEventListener('change', async () => {
    const role = state.pendingSourceRole;
    state.pendingSourceRole = null;
    if (!role) return;
    const expected = SOURCE_SPECS[role].filename.toLowerCase();
    const candidates = [...$('source-folder-picker').files].filter((file) => file.name.toLowerCase() === expected);
    if (!candidates.length) {
      state.sources[role] = { status: 'missing', reason: `A pasta escolhida não contém ${SOURCE_SPECS[role].filename}.` };
      renderSources();
      return;
    }
    let lastError = null;
    for (const file of candidates) {
      try {
        await registerSource(role, new Uint8Array(await file.arrayBuffer()), { name: file.name, modifiedAt: new Date(file.lastModified).toISOString(), origin: 'manual' });
        return;
      } catch (error) { lastError = error; }
    }
    state.sources[role] = { status: 'missing', reason: `Nenhum ${SOURCE_SPECS[role].filename} válido foi encontrado nessa pasta: ${lastError ? lastError.message : 'formato incompatível'}` };
    renderSources();
  });

  async function fileSha(file) { return core.sha256(new Uint8Array(await file.arrayBuffer())); }
  function defaultCardSelection(diff) {
    return new Set([
      ...diff.new_cards.map((row) => `new:${row.card_id}`),
      ...diff.changed_cards.map((entry) => `change:${entry.card_id}`)
    ]);
  }
  function cardReviewRows(diff) {
    return [
      ...diff.new_cards.map((row) => ({ key: `new:${row.card_id}`, action: 'new', label: 'NOVA', id: row.card_id, name: row.nome, fields: 'registro completo' })),
      ...diff.changed_cards.map((entry) => ({ key: `change:${entry.card_id}`, action: 'change', label: 'ALTERADA', id: entry.card_id, name: entry.row.nome, fields: entry.fields.map((field) => field.field).join(', ') })),
      ...diff.possibly_inactive.map((entry) => ({ key: `inactive:${entry.card_id}`, action: 'inactive', label: 'POSSÍVEL INATIVA', id: entry.card_id, name: entry.name, fields: 'ausente na fonte física atual' }))
    ];
  }
  function renderCardReview() {
    const current = state.incremental;
    const rows = cardReviewRows(current.diff);
    $('table-incremental').innerHTML = `<table><thead><tr><th>usar</th><th>ação</th><th>card_id</th><th>nome</th><th>campos</th></tr></thead><tbody>${rows.map((row) => `<tr><td><input class="card-choice" type="checkbox" data-key="${escapeHtml(row.key)}" ${current.selection.has(row.key) ? 'checked' : ''}></td><td class="action-${row.action}">${row.label}</td><td><code>${escapeHtml(row.id)}</code></td><td>${escapeHtml(row.name)}</td><td class="fields">${escapeHtml(row.fields)}</td></tr>`).join('')}</tbody></table>`;
    document.querySelectorAll('.card-choice').forEach((checkbox) => checkbox.addEventListener('change', () => {
      if (checkbox.checked) current.selection.add(checkbox.dataset.key); else current.selection.delete(checkbox.dataset.key);
      updateCardApplySummary();
    }));
    updateCardApplySummary();
  }
  function updateCardApplySummary() {
    return state.incremental ? core.selectionSummary(state.incremental.diff, [...state.incremental.selection]) : null;
  }

  async function activateCardPackage(type, manifest, details) {
    let packageManifest = manifest;
    let packagePayload;
    if (type === 'incremental') {
      packagePayload = { type: 'incremental', items: details.items };
    } else {
      packageManifest = await core.sealManifest({
        contract: core.CONTRACT_VERSION,
        mode: 'card_full',
        execution_id: core.makeExecutionId(),
        generated_at: new Date().toISOString(),
        expires_at: core.expirationFromNow(60),
        database_write: false,
        source_validation_manifest_sha256: manifest.manifest_sha256,
        reference_id: details.reference.reference_id,
        reference_csv_sha256: details.reference.output.sha256,
        records: details.reference.output.records,
        target_policy: 'somente clube_novo.carta_jogo; clube preservado'
      });
      packagePayload = { type: 'full', reference_id: details.reference.reference_id, reference_csv_sha256: details.reference.output.sha256, records: details.reference.output.records };
    }
    state.cardPackage = { type, manifest: packageManifest, package: packagePayload, details, prepared: null };
    $('apply-card-package').hidden = false;
    $('approval-card-package').hidden = true;
    $('prepare-card-package').disabled = !state.executor.online;
    const label = type === 'full' ? 'recarga completa validada' : 'atualização incremental validada';
    $('card-package-description').textContent = `Pacote atual: ${label}. O aplicativo usará somente esta execução; não é possível escolher um CSV avulso.`;
    if (type === 'full') {
      $('card-package-summary').textContent = `${Number(details.reference.output.records).toLocaleString('pt-BR')} cartas validadas. Ao clicar em OK, o pré-voo de leitura calculará automaticamente inserções e alterações em clube_novo.carta_jogo. O schema clube não será mexido.`;
    } else {
      $('card-package-summary').textContent = `${details.counts.insert} para inserir · ${details.counts.update} para atualizar · ${details.counts.inactive} possíveis inativações. Destino: clube_novo.carta_jogo; clube não será mexido.`;
    }
  }

  $('inc-base').addEventListener('change', () => { setFileName('inc-base', 'inc-base-name'); updateRunAvailability(); });
  $('run-incremental').addEventListener('click', async () => {
    const button = $('run-incremental');
    button.disabled = true;
    $('result-incremental').hidden = true;
    log('log-incremental', 'Iniciando leitura controlada…', true);
    try {
      const baselineFile = $('inc-base').files[0];
      const source = state.sources.dt870_updated;
      const baselineText = await baselineFile.text();
      const baseline = core.parseCsv(baselineText);
      core.validateSchema(baseline.headers);
      log('log-incremental', `Base atual: ${baseline.rows.length} cartas.`);
      const cpkBytes = source.bytes;
      const cards = await core.extractCardsFromCpk(cpkBytes, (message) => log('log-incremental', message));
      const validation = core.validateCards(cards);
      if (validation.duplicate_card_ids.length) throw new Error('Fonte física contém card_id duplicado.');
      const currentRows = cards.map(core.cardToRow);
      const diff = core.compareCardRows(currentRows, baseline.rows);
      const executionId = core.makeExecutionId();
      const applicableItems = [
        ...diff.new_cards.map((row) => ({ action: 'insert', card_id: row.card_id, row })),
        ...diff.changed_cards.map((entry) => ({ action: 'update', card_id: entry.card_id, row: entry.row, fields: entry.fields })),
        ...diff.possibly_inactive.map((entry) => ({ action: 'inactive', card_id: entry.card_id, row: entry.row })),
      ];
      const selectionContract = { algorithm: 'sha256/canonical-json', items: await Promise.all(applicableItems.map(async (item) => ({ key: `${item.action}:${item.card_id}`, sha256: await core.sha256(core.stableJson(item)) }))) };
      const manifest = await core.sealManifest({
        contract: core.CONTRACT_VERSION,
        mode: 'card_diff',
        execution_id: executionId,
        generated_at: new Date().toISOString(),
        expires_at: core.expirationFromNow(60),
        database_write: false,
        source_authority: 'arquivos físicos atuais do jogo; base usada apenas para comparação',
        current_source: sourceDescriptor('dt870_updated'),
        baseline: { file: baselineFile.name, bytes: baselineFile.size, modified_at: new Date(baselineFile.lastModified).toISOString(), sha256: await core.sha256(baselineText), records: baseline.rows.length },
        counts: { current: currentRows.length, new: diff.new_cards.length, changed: diff.changed_cards.length, possibly_inactive: diff.possibly_inactive.length, unchanged: diff.unchanged },
        selection_contract: selectionContract,
        validation,
        changes: {
          new_card_ids: diff.new_cards.map((row) => row.card_id),
          changed: diff.changed_cards.map((entry) => ({ card_id: entry.card_id, fields: entry.fields })),
          possibly_inactive: diff.possibly_inactive.map((entry) => ({ card_id: entry.card_id, name: entry.name, type: entry.type }))
        }
      });
      state.incremental = { baseline, cards, currentRows, diff, manifest, selection: defaultCardSelection(diff), allItems: applicableItems };
      setStats('stats-incremental', [['atuais', currentRows.length], ['novas', diff.new_cards.length], ['alteradas', diff.changed_cards.length], ['possíveis inativas', diff.possibly_inactive.length], ['duplicadas', 0]]);
      renderCardReview();
      $('result-incremental').hidden = false;
      await activateCardPackage('incremental', manifest, { items: applicableItems, counts: { insert: diff.new_cards.length, update: diff.changed_cards.length, inactive: diff.possibly_inactive.length } });
      log('log-incremental', 'Concluído: somente o diff foi preparado; nenhum dado foi aplicado.');
    } catch (error) {
      log('log-incremental', `BLOQUEADO: ${error.message}`);
      alert(error.message);
    } finally {
      updateRunAvailability();
    }
  });
  document.querySelectorAll('[data-select]').forEach((button) => button.addEventListener('click', () => {
    if (!state.incremental) return;
    const requested = button.dataset.select;
    if (requested === 'none') state.incremental.selection.clear();
    else {
      const prefix = requested === 'new' ? 'new:' : 'change:';
      for (const row of cardReviewRows(state.incremental.diff)) if (row.key.startsWith(prefix)) state.incremental.selection.add(row.key);
    }
    renderCardReview();
  }));
  $('download-incremental').addEventListener('click', () => {
    const diff = state.incremental.diff;
    download('carta_jogo_INCREMENTAL.csv', core.rowsToCsv([...diff.new_cards, ...diff.changed_cards.map((entry) => entry.row)]), 'text/csv;charset=utf-8');
  });
  $('download-card-manifest').addEventListener('click', () => download('MANIFESTO-CARTAS-DIFF.json', `${JSON.stringify(state.incremental.manifest, null, 2)}\n`, 'application/json'));
  $('download-inactive').addEventListener('click', () => download('carta_jogo_POSSIVELMENTE_INATIVAS.csv', `\uFEFFcard_id,nome,tipo\n${state.incremental.diff.possibly_inactive.map((entry) => [entry.card_id, entry.name, entry.type].join(',')).join('\n')}`, 'text/csv;charset=utf-8'));

  function metadataReviewRows(diff) {
    const rows = [];
    for (const [catalog, catalogDiff] of Object.entries(diff)) {
      for (const record of catalogDiff.new_entries) rows.push({ key: `${catalog}:new:${record.id}`, catalog, action: 'new', label: 'NOVA', id: record.id, detail: record.origins ? `nova entrada física · fontes: ${record.origins.join(', ')}` : 'nova entrada física', record });
      for (const entry of catalogDiff.changed_entries) rows.push({ key: `${catalog}:change:${entry.id}`, catalog, action: 'change', label: 'ALTERADA', id: entry.id, detail: 'fingerprint físico mudou', record: entry.record, before: entry.before, after: entry.after });
      for (const entry of catalogDiff.absent_entries) rows.push({ key: `${catalog}:absent:${entry.id}`, catalog, action: 'absent', tone: 'inactive', label: 'AUSENTE', id: entry.id, detail: 'não aparece na fonte física atual', record: entry.record });
    }
    return rows;
  }
  function renderMetadataReview() {
    const rows = metadataReviewRows(state.metadata.diff);
    $('table-metadata').innerHTML = rows.length ? `<table><thead><tr><th>usar</th><th>catálogo</th><th>ação</th><th>id</th><th>evidência</th></tr></thead><tbody>${rows.map((row) => `<tr><td><input class="metadata-choice" type="checkbox" data-key="${escapeHtml(row.key)}"></td><td>${escapeHtml(row.catalog)}</td><td class="action-${row.tone || row.action}">${row.label}</td><td><code>${escapeHtml(row.id)}</code></td><td>${escapeHtml(row.detail)}</td></tr>`).join('')}</tbody></table>` : '<div class="callout">Nenhuma entrada nova, alterada ou ausente foi comprovada.</div>';
    document.querySelectorAll('.metadata-choice').forEach((checkbox) => checkbox.addEventListener('change', () => {
      if (checkbox.checked) state.metadata.selection.add(checkbox.dataset.key); else state.metadata.selection.delete(checkbox.dataset.key);
      updateMetadataApplySummary();
    }));
    updateMetadataApplySummary();
  }
  function updateMetadataApplySummary() {
    if (!state.metadata) return;
    const selected = metadataReviewRows(state.metadata.diff).filter((row) => state.metadata.selection.has(row.key));
    $('apply-summary-metadata').textContent = `${selected.length} item(ns) selecionado(s) manualmente`;
    $('prepare-metadata').disabled = !selected.length || !state.executor.online;
  }
  $('meta-base').addEventListener('change', () => { setFileName('meta-base', 'meta-base-name'); updateRunAvailability(); });
  $('run-metadata').addEventListener('click', async () => {
    const button = $('run-metadata'); button.disabled = true; $('result-metadata').hidden = true;
    log('log-metadata', 'Lendo catálogos físicos…', true);
    try {
      const baselineFile = $('meta-base').files[0];
      const baseline = JSON.parse(await baselineFile.text());
      if (!baseline.catalogs) throw new Error('Referência JSON sem objeto catalogs.');
      const sourceBytes = Object.fromEntries(METADATA_SOURCE_ROLES.map((role) => [role, state.sources[role].bytes]));
      const sourceDescriptors = Object.fromEntries(METADATA_SOURCE_ROLES.map((role) => [role, sourceDescriptor(role)]));
      const current = await core.extractMetadataByFamily(sourceBytes, sourceDescriptors, (message) => log('log-metadata', message));
      const diff = core.compareMetadata(current, baseline);
      const summary = Object.fromEntries(Object.entries(diff).map(([catalog, item]) => [catalog, { status: item.status, reason: item.reason || null, current: item.current, baseline_active: item.baseline_active, new: item.new_entries.length, changed: item.changed_entries.length, absent: item.absent_entries.length, without_previous_fingerprint: item.without_previous_fingerprint, duplicate_ids: item.duplicate_ids.length }]));
      if (Object.values(summary).some((item) => item.duplicate_ids)) throw new Error('Catálogo físico contém chave duplicada.');
      const totals = Object.values(summary).reduce((acc, item) => ({ new: acc.new + item.new, changed: acc.changed + item.changed, absent: acc.absent + item.absent }), { new: 0, changed: 0, absent: 0 });
      const applicableItems = metadataReviewRows(diff).map((item) => Object.fromEntries(['catalog', 'action', 'id', 'record', 'before', 'after'].filter((key) => key in item).map((key) => [key, item[key]])));
      const selectionContract = { algorithm: 'sha256/canonical-json', items: await Promise.all(applicableItems.map(async (item) => ({ key: `${item.catalog}:${item.action}:${item.id}`, sha256: await core.sha256(core.stableJson(item)) }))) };
      const manifest = await core.sealManifest({ contract: core.CONTRACT_VERSION, mode: 'metadata_diff', execution_id: core.makeExecutionId(), generated_at: new Date().toISOString(), expires_at: core.expirationFromNow(60), database_write: false, source_authority: 'fontes físicas separadas por família; referência usada apenas para comparação', source_policy: current.source_policy, current_sources: current.sources, baseline: { file: baselineFile.name, bytes: baselineFile.size, sha256: await fileSha(baselineFile) }, counts: { new: totals.new, changed: totals.changed, possibly_inactive: totals.absent }, selection_contract: selectionContract, summary });
      state.metadata = { baseline, current, diff, summary, manifest, selection: new Set() };
      const supportedCount = Object.values(summary).filter((item) => item.status !== 'nao_suportado_nesta_atualizacao').length;
      const unsupportedCount = Object.values(summary).filter((item) => item.status === 'nao_suportado_nesta_atualizacao').length;
      setStats('stats-metadata', [['famílias suportadas', supportedCount], ['não suportadas', unsupportedCount], ['novas', totals.new], ['alteradas', totals.changed], ['ausentes', totals.absent]]);
      $('metadata-support').innerHTML = Object.entries(summary).map(([name, item]) => item.status === 'nao_suportado_nesta_atualizacao'
        ? `<div class="support-item unsupported"><b>${escapeHtml(name)}</b> — Não suportada nesta atualização. ${escapeHtml(item.reason || '')}</div>`
        : `<div class="support-item"><b>${escapeHtml(name)}</b> — ${escapeHtml(item.status === 'comparado' ? 'Comparada pela fonte física definida para esta família.' : item.reason || item.status)}</div>`).join('');
      renderMetadataReview(); $('result-metadata').hidden = false;
      log('log-metadata', 'Concluído: diferenças revisáveis preparadas; nenhum catálogo foi aplicado.');
    } catch (error) {
      log('log-metadata', `BLOQUEADO: ${error.message}`); alert(error.message);
    } finally { updateRunAvailability(); }
  });
  $('download-metadata-diff').addEventListener('click', () => download('METADADOS-DIFF.json', `${JSON.stringify(Object.fromEntries(Object.entries(state.metadata.diff).map(([name, item]) => [name, { new_entries: item.new_entries, changed_entries: item.changed_entries, absent_entries: item.absent_entries }])), null, 2)}\n`, 'application/json'));
  $('download-metadata-manifest').addEventListener('click', () => download('MANIFESTO-METADADOS-DIFF.json', `${JSON.stringify(state.metadata.manifest, null, 2)}\n`, 'application/json'));

  function enableFull() {
    $('run-full').disabled = !(operationIsReady(CARD_SOURCE_ROLES) && state.reference.status === 'ready' && $('full-check').checked);
  }
  $('full-check').addEventListener('change', enableFull);
  $('run-full').addEventListener('click', async () => {
    const button = $('run-full'); button.disabled = true; $('result-full').hidden = true;
    log('log-full', 'Validando a fonte e a referência internas…', true);
    try {
      const source = state.sources.dt870_updated;
      const reference = await fetchReferenceStatus();
      const sourceUnchanged = source.sha256 === reference.source.sha256;
      if (sourceUnchanged) {
        const manifest = await core.sealManifest({
          contract: core.CONTRACT_VERSION,
          mode: 'full_reference_validation',
          execution_id: core.makeExecutionId(),
          generated_at: new Date().toISOString(),
          database_write: false,
          result: 'source_unchanged_reference_reused',
          source: sourceDescriptor('dt870_updated'),
          reference: { reference_id: reference.reference_id, source_sha256: reference.source.sha256, output: reference.output },
          validation: reference.validation
        });
        state.full = { cards: [], baseline: null, diff: null, manifest, fullCsv: null };
        setStats('stats-full', [['cartas validadas', reference.output.records], ['IDs únicos', reference.validation.unique_card_ids], ['duplicadas', 0], ['campos', core.CARD_COLUMNS.length], ['nova carga', 'não']]);
        $('full-golden-status').textContent = `VALIDAÇÃO CONCLUÍDA — a fonte do jogo é a mesma da referência interna vigente (${Number(reference.output.records).toLocaleString('pt-BR')} cartas).`;
        $('table-full').innerHTML = '<div class="callout">Nenhuma mudança física foi detectada. A referência interna foi reutilizada automaticamente.</div>';
        $('result-full').hidden = false;
        await activateCardPackage('full', manifest, { reference });
        log('log-full', 'Concluído: fonte igual; nenhuma extração repetida, nenhuma nova referência e nenhuma escrita no banco.');
        return;
      }
      log('log-full', 'Nova versão física detectada. Extraindo e validando a carga completa…');
      const baselineResponse = await fetch('/api/card-reference/current.csv', { cache: 'no-store' });
      if (!baselineResponse.ok) throw new Error('A referência anterior não pôde ser lida para comparação.');
      const baseline = core.parseCsv(await baselineResponse.text());
      core.validateSchema(baseline.headers);
      const cards = await core.extractCardsFromCpk(source.bytes, (message) => log('log-full', message));
      const validation = core.validateCards(cards);
      if (!validation.records) throw new Error('A extração não encontrou cartas válidas.');
      if (validation.unique_card_ids !== validation.records || validation.duplicate_card_ids.length) throw new Error('A extração contém card_id duplicado.');
      if (validation.schema.length !== core.CARD_COLUMNS.length || validation.schema.some((field, index) => field !== core.CARD_COLUMNS[index])) throw new Error('A estrutura extraída não possui os 29 campos esperados.');
      const fullCsv = core.cardsToCsv(cards);
      const fullCsvSha256 = await core.sha256(fullCsv);
      const currentRows = cards.map(core.cardToRow);
      const diff = core.compareCardRows(currentRows, baseline.rows);
      const comparison = { previous: baseline.rows.length, current: currentRows.length, new: diff.new_cards.length, changed: diff.changed_cards.length, possibly_inactive: diff.possibly_inactive.length, unchanged: diff.unchanged };
      const manifest = await core.sealManifest({
        contract: core.CONTRACT_VERSION,
        mode: 'full_reference_promotion',
        execution_id: core.makeExecutionId(),
        generated_at: new Date().toISOString(),
        database_write: false,
        source_policy: 'somente DT870 da atualização, obrigatório e autoritativo',
        source: sourceDescriptor('dt870_updated'),
        previous_reference_id: reference.reference_id,
        extracted_csv_sha256: fullCsvSha256,
        validation,
        comparison_to_previous: comparison
      });
      const promotion = await postJson('/api/card-reference/promote', { previous_reference_id: reference.reference_id, csv: fullCsv, manifest });
      if (!promotion.promoted && !promotion.reused) throw new Error('A nova referência não foi selada.');
      state.reference = { ...promotion.reference, status: 'ready' };
      state.full = { cards, baseline, diff, manifest: { ...manifest, reference_promotion: promotion.manifest || null }, fullCsv: null };
      setStats('stats-full', [['cartas', cards.length], ['novas', diff.new_cards.length], ['alteradas', diff.changed_cards.length], ['possíveis inativas', diff.possibly_inactive.length], ['duplicadas', 0]]);
      $('full-golden-status').textContent = `NOVA CARGA VALIDADA — ${diff.new_cards.length} cartas novas, ${diff.changed_cards.length} alteradas e ${diff.possibly_inactive.length} possíveis inativas. A referência interna foi versionada e selada automaticamente.`;
      const changedRows = [...diff.new_cards, ...diff.changed_cards.map((entry) => entry.row)].slice(0, 300);
      $('table-full').innerHTML = changedRows.length ? `<table><thead><tr><th>card_id</th><th>nome</th><th>tipo</th><th>posição</th><th>overall</th></tr></thead><tbody>${changedRows.map((row) => `<tr><td><code>${escapeHtml(row.card_id)}</code></td><td>${escapeHtml(row.nome)}</td><td>${escapeHtml(row.tipo)}</td><td>${escapeHtml(row.posicao)}</td><td>${escapeHtml(row.overall)}</td></tr>`).join('')}</tbody></table>` : '<div class="callout">A fonte mudou, mas nenhum valor de carta mudou.</div>';
      $('result-full').hidden = false;
      renderReference();
      await activateCardPackage('full', state.full.manifest, { reference: promotion.reference });
      log('log-full', 'Concluído: nova referência interna preservada; versões anteriores mantidas; nenhum banco foi alterado.');
    } catch (error) {
      state.full = { manifest: null };
      setStats('stats-full', [['estado', 'bloqueado']]);
      $('full-golden-status').textContent = `VALIDAÇÃO BLOQUEADA — ${error.message} A referência vigente foi preservada.`;
      $('table-full').innerHTML = '';
      $('result-full').hidden = false;
      log('log-full', `BLOQUEADO: ${error.message}. Nenhuma referência nova e nenhuma escrita no banco.`);
    }
    finally { enableFull(); }
  });
  $('download-full-manifest').addEventListener('click', () => {
    if (state.full && state.full.manifest) download('MANIFESTO-VALIDACAO-CARGA-COMPLETA.json', `${JSON.stringify(state.full.manifest, null, 2)}\n`, 'application/json');
  });

  async function postJson(url, body) {
    const response = await fetch(url, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
    const payload = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    return payload;
  }
  function configureApproval(kind, prepared) {
    state.approvals[kind] = prepared;
    $(`approval-${kind}`).hidden = false;
    $(`approval-preview-${kind}`).textContent = `${prepared.summary.insert || 0} inserções · ${prepared.summary.update || 0} alterações · ${prepared.summary.inactive || 0} inativações · modo ${prepared.mode}`;
    $(`approval-phrase-${kind}`).textContent = prepared.confirmation_phrase;
    $(`approval-text-${kind}`).value = '';
    $(`approval-check-${kind}`).checked = false;
    $(`apply-lock-${kind}`).textContent = prepared.write_enabled ? 'A escrita só ocorre após a frase exata e o clique final.' : 'Dry-run ativo: a escrita real está bloqueada no executor desta entrega.';
    const update = () => { $(`apply-button-${kind}`).disabled = !(prepared.write_enabled && $(`approval-check-${kind}`).checked && $(`approval-text-${kind}`).value.trim() === prepared.confirmation_phrase); };
    $(`approval-check-${kind}`).onchange = update;
    $(`approval-text-${kind}`).oninput = update;
    update();
    if (prepared.dry_run_manifest) download(`MANIFESTO-DRY-RUN-${kind.toUpperCase()}.json`, `${JSON.stringify(prepared.dry_run_manifest, null, 2)}\n`, 'application/json');
  }
  function configureCardPackageApproval(prepared) {
    state.cardPackage.prepared = prepared;
    $('approval-card-package').hidden = false;
    $('card-package-confirmation').hidden = false;
    const type = prepared.package_type === 'full' ? 'recarga completa' : 'atualização incremental';
    $('approval-preview-card-package').textContent = `Destino: clube_novo.carta_jogo · ${type} · ${prepared.summary.insert || 0} inserir · ${prepared.summary.update || 0} atualizar · ${prepared.summary.inactive || 0} inativar · clube não será alterado.`;
    if (prepared.no_changes) {
      $('approval-phrase-card-package').textContent = 'NENHUMA ALTERAÇÃO';
      $('approval-text-card-package').value = '';
      $('approval-check-card-package').checked = false;
      $('approval-check-card-package').disabled = true;
      $('approval-text-card-package').disabled = true;
      $('apply-button-card-package').disabled = true;
      $('apply-lock-card-package').textContent = 'O clube_novo já corresponde integralmente ao pacote validado; não há nada para enviar.';
      $('card-package-confirmation').hidden = true;
      return;
    }
    $('approval-phrase-card-package').textContent = prepared.confirmation_phrase;
    $('approval-text-card-package').value = '';
    $('approval-text-card-package').disabled = false;
    $('approval-check-card-package').checked = false;
    $('approval-check-card-package').disabled = false;
    $('apply-lock-card-package').textContent = prepared.write_enabled ? 'O envio só ocorre após esta confirmação final e vale apenas para o pacote atual.' : 'Teste seguro concluído: a escrita real está bloqueada nesta instalação.';
    const update = () => { $('apply-button-card-package').disabled = !(prepared.write_enabled && $('approval-check-card-package').checked && $('approval-text-card-package').value.trim() === prepared.confirmation_phrase); };
    $('approval-check-card-package').onchange = update;
    $('approval-text-card-package').oninput = update;
    update();
  }
  $('prepare-card-package').addEventListener('click', async () => {
    const button = $('prepare-card-package');
    button.disabled = true;
    try {
      if (!state.cardPackage) throw new Error('Execute e valide uma carga antes de continuar.');
      core.ensureCurrentManifest(state.cardPackage.manifest);
      const prepared = await postJson('/api/card-package/prepare', { manifest: state.cardPackage.manifest, package: state.cardPackage.package });
      configureCardPackageApproval(prepared);
    } catch (error) {
      $('approval-card-package').hidden = false;
      $('card-package-confirmation').hidden = true;
      $('approval-preview-card-package').textContent = `ENVIO BLOQUEADO — ${error.message}`;
      $('apply-lock-card-package').textContent = 'Nenhum dado foi enviado. O pacote validado permanece disponível para novo pré-voo.';
      $('apply-button-card-package').disabled = true;
    } finally { button.disabled = !state.cardPackage || !state.executor.online; }
  });
  $('prepare-metadata').addEventListener('click', async () => {
    try {
      core.ensureCurrentManifest(state.metadata.manifest);
      const items = metadataReviewRows(state.metadata.diff).filter((row) => state.metadata.selection.has(row.key));
      const prepared = await postJson('/api/prepare', { manifest: state.metadata.manifest, selection: { kind: 'metadata', items } });
      configureApproval('metadata', prepared);
    } catch (error) { alert(`Preparação bloqueada: ${error.message}`); }
  });
  for (const kind of ['metadata']) {
    $(`apply-button-${kind}`).addEventListener('click', async () => {
      try {
        const prepared = state.approvals[kind];
        const result = await postJson('/api/apply', { approval_token: prepared.approval_token, confirmation: $(`approval-text-${kind}`).value.trim() });
        download(`MANIFESTO-APLICACAO-${kind.toUpperCase()}.json`, `${JSON.stringify(result.application_manifest, null, 2)}\n`, 'application/json');
        alert('Aplicação concluída e validada por leitura posterior. O manifesto foi baixado.');
        await refreshExecutorStatus();
      } catch (error) { alert(`Aplicação bloqueada: ${error.message}`); }
    });
  }
  $('apply-button-card-package').addEventListener('click', async () => {
    try {
      const prepared = state.cardPackage && state.cardPackage.prepared;
      if (!prepared) throw new Error('Faça o pré-voo deste pacote novamente.');
      const result = await postJson('/api/apply', { approval_token: prepared.approval_token, confirmation: $('approval-text-card-package').value.trim() });
      alert(`Carga aplicada em clube_novo.carta_jogo e conferida por leitura posterior. O schema clube não foi alterado. Manifesto: ${result.application_manifest.execution_id}.`);
      await refreshExecutorStatus();
    } catch (error) { alert(`Aplicação bloqueada: ${error.message}`); }
  });

  refreshExecutorStatus().then(() => { updateCardApplySummary(); updateMetadataApplySummary(); });
  refreshSources();
})(globalThis);
