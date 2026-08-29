'use strict';

(function installUi(global) {
  const core = global.CLUBEF_CORE;
  const state = {
    executor: { online: false, write_enabled: false, mode: 'offline' },
    sources: {},
    reference: { status: 'loading' },
    pendingSourceRole: null,
    sourcesRunning: false,
    incremental: null,
    incrementalRunning: false,
    metadata: null,
    metadataRunning: false,
    full: null,
    cardPackage: null,
    approvals: {},
    automatic: { cards: { state: 'loading' }, metadata: { state: 'loading' } },
    applying: false
  };
  const $ = (id) => document.getElementById(id);
  const escapeHtml = (value) => String(value == null ? '' : value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));
  const SOURCE_SPECS = Object.freeze({
    dt870_updated: { label: 'DT870 da atualização', filename: 'dt870_console_win.cpk', purpose: 'Cartas atuais; habilidades; ímpetos; técnicos, idade, nacionalidade e afinidade; overlay de playstyles.', operations: 'Cartas e catálogos' },
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
  function setOperationStatus(id, kind, title, detail) {
    const element = $(id);
    if (!element) return;
    element.hidden = false;
    element.className = `operation-status ${kind}`;
    element.innerHTML = `<span class="busy-spinner" aria-hidden="true"></span><div><b>${escapeHtml(title)}</b><small>${escapeHtml(detail || '')}</small></div>`;
  }
  function setNamedOperationStatus(prefix, kind, title, detail) {
    const element = $(`${prefix}-status`);
    if (!element) return;
    element.hidden = false;
    element.className = `operation-status ${kind}`;
    $(`${prefix}-title`).textContent = title;
    $(`${prefix}-detail`).textContent = detail || '';
  }
  function renderAutomaticSummary() {
    const cards = state.automatic.cards;
    const metadata = state.automatic.metadata;
    const renderOne = (name, item) => {
      const badge = $(`${name}-update-badge`);
      const summary = $(`${name}-auto-summary`);
      badge.className = `update-badge ${item.state === 'ready' ? (item.pending ? 'pending' : 'ok') : (item.state === 'error' ? 'error' : 'loading')}`;
      badge.textContent = item.state === 'loading' ? 'Verificando…' : (item.state === 'error' ? 'Verificação bloqueada' : (item.pending ? 'Atualização disponível' : 'Tudo atualizado'));
      summary.textContent = item.message || (item.state === 'loading' ? 'Verificando automaticamente…' : '');
    };
    renderOne('cards', cards);
    renderOne('metadata', metadata);
    const finished = cards.state !== 'loading' && metadata.state !== 'loading';
    const failed = cards.state === 'error' || metadata.state === 'error';
    const pending = Boolean(cards.pending || metadata.pending);
    const badge = $('overall-update-badge');
    badge.className = `update-badge ${!finished ? 'loading' : (failed || pending ? 'pending' : 'ok')}`;
    badge.textContent = !finished ? 'Verificando…' : (failed ? 'Atenção necessária' : (pending ? 'Atualização disponível' : 'Tudo atualizado'));
    if (!finished) setOperationStatus('automatic-summary-status', 'loading', 'Verificação automática em andamento', 'As fontes, cartas e famílias suportadas estão sendo conferidas.');
    else if (failed) setOperationStatus('automatic-summary-status', 'error', 'Uma verificação foi bloqueada', 'Veja o motivo em Cartas ou Metadados; nenhuma escrita foi feita.');
    else if (pending) setOperationStatus('automatic-summary-status', 'error', 'Atualização disponível', 'Revise as novidades abaixo. O envio continua manual e depende de confirmação.');
    else setOperationStatus('automatic-summary-status', 'success', 'Tudo atualizado', 'Não há itens pendentes de aplicação nesta abertura.');
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
    if (name === 'incremental') {
      if (state.incremental) $('result-incremental').scrollIntoView({ behavior: 'smooth', block: 'start' });
      else setTimeout(() => maybeStartIncrementalComparison('aba Atualização por diff'), 0);
    } else if (name === 'metadata' && !state.metadata && !state.metadataRunning) {
      setTimeout(() => refreshMetadataAutomatically('aba Metadados'), 0);
    }
  }
  document.querySelectorAll('.tab').forEach((tab) => tab.addEventListener('click', () => showPane(tab.dataset.pane)));
  $('open-card-details').addEventListener('click', () => { showPane('incremental'); $('pane-incremental').scrollIntoView({ behavior: 'smooth', block: 'start' }); });
  $('open-metadata-details').addEventListener('click', () => { showPane('metadata'); $('pane-metadata').scrollIntoView({ behavior: 'smooth', block: 'start' }); });

  async function refreshExecutorStatus() {
    try {
      const response = await fetch('/api/status', { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      state.executor = await response.json();
      state.executor.online = true;
      $('executor-dot').className = `dot ${state.executor.manual_apply_available ? 'ok' : 'neutral'}`;
      $('executor-title').textContent = state.executor.manual_apply_available ? 'Banco conectado · envio manual' : 'Executor local · modo protegido';
      $('executor-detail').textContent = state.executor.manual_apply_available ? 'destino único: clube_novo; nenhuma escrita automática' : 'banco sem conexão; extração continua disponível';
      $('inc-base-name').textContent = state.executor.database_configured
        ? 'clube_novo.carta_jogo conectado; a base será carregada automaticamente'
        : 'Base indisponível: conexão segura com clube_novo não encontrada';
    } catch (error) {
      state.executor = { online: false, write_enabled: false, mode: 'offline' };
      $('executor-dot').className = 'dot neutral';
      $('executor-title').textContent = 'Executor local desconectado';
      $('executor-detail').textContent = 'extração funciona; aplicação indisponível';
      $('inc-base-name').textContent = 'Base indisponível: o executor local não respondeu';
    }
    updateRunAvailability();
    if ($('pane-incremental').classList.contains('active')) setTimeout(() => maybeStartIncrementalComparison('conexão de leitura confirmada'), 0);
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
      bytes: source.byteLength == null ? (source.bytes ? source.bytes.length : 0) : source.byteLength,
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
        ? `${source.name} · ${Number(source.byteLength == null ? (source.bytes ? source.bytes.length : 0) : source.byteLength).toLocaleString('pt-BR')} bytes · ${source.origin === 'automatic' ? 'localizado automaticamente' : 'pasta escolhida'}`
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
    const incrementalReady = Boolean(state.executor.online && state.executor.database_configured && operationIsReady(CARD_SOURCE_ROLES));
    $('run-incremental').disabled = state.incrementalRunning || !incrementalReady;
    if (!state.incrementalRunning) $('run-incremental').textContent = state.incremental ? 'Comparar novamente' : 'Comparar agora';
    if (!state.executor.online || !state.executor.database_configured) {
      setOperationStatus('incremental-status', 'error', 'Comparação de cartas bloqueada', 'A conexão segura de leitura com clube_novo não respondeu.');
    } else if (!operationIsReady(CARD_SOURCE_ROLES)) {
      setOperationStatus('incremental-status', 'error', 'Comparação de cartas bloqueada', 'O DT870 da atualização não foi localizado ou validado.');
    } else if (!state.incremental && !state.incrementalRunning) {
      setOperationStatus('incremental-status', 'loading', 'Comparação de cartas pronta para iniciar', 'A execução automática começará em seguida.');
    }
    $('run-metadata').disabled = state.metadataRunning || !operationIsReady(METADATA_SOURCE_ROLES);
    if (!state.metadataRunning) $('run-metadata').textContent = state.metadata ? 'Comparar metadados novamente' : 'Comparar metadados agora';
    enableFull();
  }
  async function registerSource(role, bytes, details) {
    state.sources[role] = { status: 'loading' };
    renderSources();
    const validation = await core.validateSourceForRole(bytes, role);
    state.sources[role] = {
      status: 'ready',
      bytes,
      byteLength: bytes.length,
      name: details.name || SOURCE_SPECS[role].filename,
      modifiedAt: details.modifiedAt || null,
      origin: details.origin,
      sha256: await core.sha256(bytes),
      validation
    };
    renderSources();
  }
  async function refreshSources() {
    if (state.sourcesRunning || state.applying) return;
    state.sourcesRunning = true;
    $('refresh-sources').disabled = true;
    $('refresh-sources').textContent = 'Procurando…';
    state.incremental = null;
    state.metadata = null;
    state.cardPackage = null;
    $('result-incremental').hidden = true;
    $('apply-card-package').hidden = true;
    setOperationStatus('incremental-status', 'loading', 'Atualizando as fontes', 'Preparando uma nova comparação automática de cartas.');
    state.automatic.cards = { state: 'loading', pending: false, message: 'Localizando o DT870 atualizado e carregando clube_novo…' };
    state.automatic.metadata = { state: 'loading', pending: false, message: 'Conferindo automaticamente as fontes de catálogos…' };
    renderAutomaticSummary();
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
        if (role === 'dt870_updated' || role === 'dt261_bra') {
          try {
            const fileResponse = await fetch(`/api/sources/file?role=${encodeURIComponent(role)}`, { cache: 'no-store' });
            if (!fileResponse.ok) throw new Error(`HTTP ${fileResponse.status}`);
            await registerSource(role, new Uint8Array(await fileResponse.arrayBuffer()), { name: found.filename, modifiedAt: found.modified_at, origin: 'automatic' });
          } catch (error) {
            state.sources[role] = { status: 'missing', reason: `Arquivo localizado, mas inválido para esta função: ${error.message}` };
            renderSources();
          }
        } else {
          state.sources[role] = { status: 'ready', bytes: null, byteLength: found.bytes, name: found.filename, modifiedAt: found.modified_at, origin: 'automatic', sha256: null, validation: { valid_container: true, discovery_only: true } };
          renderSources();
        }
      }
    } catch (error) {
      for (const role of Object.keys(SOURCE_SPECS)) state.sources[role] = { status: 'missing', reason: 'A busca automática não respondeu. Escolha apenas a pasta desta fonte.' };
      renderSources();
    }
    await Promise.all([refreshCardReference(), refreshMetadataAutomatically('abertura automática')]);
    state.sourcesRunning = false;
    $('refresh-sources').disabled = false;
    $('refresh-sources').textContent = 'Procurar novamente';
    await maybeStartIncrementalComparison('localização automática concluída');
  }

  $('refresh-sources').addEventListener('click', () => {
    if (state.incrementalRunning) return;
    refreshSources();
  });
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
    const noIncrementalChanges = type === 'incremental' && (details.counts.insert + details.counts.update + details.counts.inactive === 0);
    state.cardPackage = { type, manifest: packageManifest, package: packagePayload, details, prepared: null, no_changes: noIncrementalChanges };
    $('apply-card-package').hidden = false;
    $('approval-card-package').hidden = true;
    $('card-package-preflight-status').hidden = true;
    $('card-package-apply-status').hidden = true;
    $('prepare-card-package').disabled = !state.executor.online || noIncrementalChanges;
    $('prepare-card-package').textContent = noIncrementalChanges ? 'Sem mudanças para enviar' : 'OK — preparar envio ao clube_novo';
    const label = type === 'full' ? 'recarga completa validada' : 'atualização incremental validada';
    $('card-package-description').textContent = `Pacote atual: ${label}. O aplicativo usará somente esta execução; não é possível escolher um CSV avulso.`;
    if (type === 'full') {
      $('card-package-summary').textContent = `${Number(details.reference.output.records).toLocaleString('pt-BR')} cartas validadas. Ao clicar em OK, o pré-voo de leitura calculará automaticamente inserções e alterações em clube_novo.carta_jogo. O schema clube não será mexido.`;
    } else {
      $('card-package-summary').textContent = noIncrementalChanges
        ? 'SEM MUDANÇAS — clube_novo já corresponde à fonte atual; não há pacote para enviar.'
        : `${details.counts.insert} para inserir · ${details.counts.update} para atualizar · ${details.counts.inactive} possíveis inativações. Destino: clube_novo.carta_jogo; clube não será mexido.`;
    }
  }

  async function fetchCurrentCardBaseline() {
    const response = await fetch('/api/card-baseline/current.csv', { cache: 'no-store' });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
      throw new Error(payload.error || 'A base atual do clube_novo não pôde ser lida.');
    }
    const text = await response.text();
    const parsed = core.parseCsv(text);
    core.validateSchema(parsed.headers);
    const records = Number(response.headers.get('X-Clubef-Records') || parsed.rows.length);
    if (records !== parsed.rows.length) throw new Error('A contagem recebida do clube_novo não confere.');
    return {
      ...parsed,
      text,
      records,
      sha256: response.headers.get('X-Clubef-Sha256') || await core.sha256(text),
      transaction_read_only: response.headers.get('X-Clubef-Read-Only') === 'true',
      source: 'clube_novo.carta_jogo'
    };
  }

  async function maybeStartIncrementalComparison(trigger) {
    if (state.incremental || state.incrementalRunning) return;
    if (state.sourcesRunning || CARD_SOURCE_ROLES.some((role) => state.sources[role] && state.sources[role].status === 'loading')) {
      setOperationStatus('incremental-status', 'loading', 'Localizando a fonte de cartas', 'A comparação começará automaticamente assim que o DT870 atualizado for validado.');
      state.automatic.cards = { state: 'loading', pending: false, message: 'Localizando e validando o DT870 atualizado…' };
      renderAutomaticSummary();
      return;
    }
    if (!(state.executor.online && state.executor.database_configured && operationIsReady(CARD_SOURCE_ROLES))) {
      updateRunAvailability();
      state.automatic.cards = { state: 'error', pending: false, message: 'Não foi possível iniciar a comparação automática de cartas.' };
      renderAutomaticSummary();
      return;
    }
    await runIncrementalComparison(trigger);
  }

  async function runIncrementalComparison(trigger) {
    if (state.incrementalRunning) return;
    if (!(state.executor.online && state.executor.database_configured)) {
      setOperationStatus('incremental-status', 'error', 'Comparação de cartas bloqueada', 'Não foi possível ler a base atual de clube_novo.');
      return;
    }
    if (!operationIsReady(CARD_SOURCE_ROLES)) {
      setOperationStatus('incremental-status', 'error', 'Comparação de cartas bloqueada', 'O DT870 da atualização ainda não está disponível.');
      return;
    }
    const button = $('run-incremental');
    state.incrementalRunning = true;
    state.incremental = null;
    state.cardPackage = null;
    button.disabled = true;
    button.textContent = 'Comparando…';
    setOperationStatus('incremental-status', 'loading', 'Comparando cartas', `Execução iniciada por ${trigger}. Aguarde o conjunto revisável.`);
    state.automatic.cards = { state: 'loading', pending: false, message: 'Extraindo o estado atual do jogo e comparando com clube_novo…' };
    renderAutomaticSummary();
    $('result-incremental').hidden = true;
    $('apply-card-package').hidden = true;
    log('log-incremental', 'Iniciando leitura controlada…', true);
    try {
      const source = state.sources.dt870_updated;
      const baseline = await fetchCurrentCardBaseline();
      if (!baseline.transaction_read_only) throw new Error('A leitura da base atual não foi confirmada como protegida.');
      $('inc-base-name').textContent = `${baseline.rows.length.toLocaleString('pt-BR')} cartas carregadas automaticamente de clube_novo`;
      log('log-incremental', `Base atual de clube_novo: ${baseline.rows.length} cartas; leitura protegida.`);
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
        baseline: { source: baseline.source, sha256: baseline.sha256, records: baseline.rows.length, transaction_read_only: true, preserved_schema: 'clube' },
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
      const changes = diff.new_cards.length + diff.changed_cards.length + diff.possibly_inactive.length;
      $('incremental-result-status').textContent = changes
        ? `NOVA CARGA IDENTIFICADA — ${diff.new_cards.length} novas, ${diff.changed_cards.length} atualizadas e ${diff.possibly_inactive.length} possíveis inativas.`
        : 'SEM MUDANÇAS — o estado atual do jogo já corresponde à base de clube_novo.';
      renderCardReview();
      $('result-incremental').hidden = false;
      await activateCardPackage('incremental', manifest, { items: applicableItems, counts: { insert: diff.new_cards.length, update: diff.changed_cards.length, inactive: diff.possibly_inactive.length } });
      setOperationStatus('incremental-status', 'success', changes ? 'Comparação concluída — atualização disponível' : 'Comparação concluída — nada para atualizar', changes ? 'Confira os números e use o botão de preparar envio quando desejar.' : 'clube_novo já corresponde ao estado atual do jogo.');
      state.automatic.cards = { state: 'ready', pending: Boolean(changes), message: changes ? `${diff.new_cards.length} novas · ${diff.changed_cards.length} alteradas · ${diff.possibly_inactive.length} possíveis inativas.` : `Nada para atualizar: ${currentRows.length.toLocaleString('pt-BR')} cartas conferidas e nenhuma diferença pendente.` };
      renderAutomaticSummary();
      log('log-incremental', 'Concluído: somente o diff foi preparado; nenhum dado foi aplicado.');
      if (trigger.startsWith('botão')) $('result-incremental').scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
      log('log-incremental', `BLOQUEADO: ${error.message}`);
      $('incremental-result-status').textContent = `COMPARAÇÃO BLOQUEADA — ${error.message}`;
      $('stats-incremental').innerHTML = '';
      $('table-incremental').innerHTML = '';
      $('result-incremental').hidden = false;
      setOperationStatus('incremental-status', 'error', 'Comparação de cartas bloqueada', `${error.message} Nenhum dado foi enviado.`);
      state.automatic.cards = { state: 'error', pending: false, message: `Cartas: ${error.message}` };
      renderAutomaticSummary();
      if (trigger.startsWith('botão')) $('result-incremental').scrollIntoView({ behavior: 'smooth', block: 'start' });
    } finally {
      state.incrementalRunning = false;
      updateRunAvailability();
    }
  }
  $('run-incremental').addEventListener('click', () => runIncrementalComparison('botão Comparar agora'));
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
    const visibleRows = rows.slice(0, 250);
    const remainder = Math.max(0, rows.length - visibleRows.length);
    $('table-metadata').innerHTML = rows.length ? `${remainder ? `<div class="callout">Exibindo 250 de ${rows.length.toLocaleString('pt-BR')} diferenças para manter o aplicativo responsivo. O manifesto contém o conjunto integral.</div>` : ''}<table><thead><tr><th>usar</th><th>catálogo</th><th>ação</th><th>id</th><th>evidência</th></tr></thead><tbody>${visibleRows.map((row) => `<tr><td><input class="metadata-choice" type="checkbox" data-key="${escapeHtml(row.key)}" ${state.metadata.selection.has(row.key) ? 'checked' : ''}></td><td>${escapeHtml(row.catalog)}</td><td class="action-${row.tone || row.action}">${row.label}</td><td><code>${escapeHtml(row.id)}</code></td><td>${escapeHtml(row.detail)}</td></tr>`).join('')}</tbody></table>` : '<div class="callout">Nenhuma entrada nova, alterada ou ausente foi comprovada.</div>';
    document.querySelectorAll('.metadata-choice').forEach((checkbox) => checkbox.addEventListener('change', () => {
      if (checkbox.checked) state.metadata.selection.add(checkbox.dataset.key); else state.metadata.selection.delete(checkbox.dataset.key);
      updateMetadataApplySummary();
    }));
    updateMetadataApplySummary();
  }
  function updateMetadataApplySummary() {
    if (!state.metadata) return;
    const selected = metadataReviewRows(state.metadata.diff).filter((row) => state.metadata.selection.has(row.key));
    const safeTextItems = state.metadata.textItems || [];
    const selectedTextItems = selected.filter((row) => row.catalog === 'textos');
    const complete = safeTextItems.length > 0 && selectedTextItems.length === safeTextItems.length && selected.length === safeTextItems.length;
    $('apply-summary-metadata').textContent = !safeTextItems.length
      ? 'Nenhum texto oficial está pendente de aplicação.'
      : complete
        ? `${safeTextItems.length.toLocaleString('pt-BR')} diferenças de texto compõem o pacote integral seguro; nenhuma outra família será enviada.`
        : 'O pacote de textos só pode ser preparado integralmente. Marque novamente todos os textos seguros ou refaça a comparação.';
    $('prepare-metadata').disabled = !(complete && state.executor.manual_text_apply_available && state.metadata.baseline && state.metadata.baseline.schema_ready && !state.metadataRunning && !state.applying);
    $('prepare-metadata').textContent = $('prepare-metadata').disabled
      ? (safeTextItems.length ? 'Pacote textual incompleto ou bloqueado' : 'Nada para aplicar')
      : 'OK — preparar textos para clube_novo';
  }

  async function refreshMetadataAutomatically(trigger = 'abertura automática') {
    if (state.metadataRunning) return;
    const button = $('run-metadata');
    state.metadataRunning = true;
    button.disabled = true;
    button.textContent = 'Comparando…';
    $('result-metadata').hidden = true;
    setOperationStatus('metadata-status', 'loading', 'Comparando metadados automaticamente', `Verificando a referência interna e as fontes por família (${trigger}).`);
    state.automatic.metadata = { state: 'loading', pending: false, message: 'Conferindo a referência interna e as fontes por família…' };
    renderAutomaticSummary();
    log('log-metadata', 'Verificando referência interna, all.str e dicionário canônico de clube_novo…', true);
    try {
      if (!operationIsReady(METADATA_SOURCE_ROLES)) throw new Error('Uma ou mais fontes de catálogos não foram localizadas automaticamente.');
      const response = await fetch('/api/metadata-reference/status', { cache: 'no-store' });
      const reference = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
      if (!response.ok || !reference.ready) throw new Error(reference.error || 'A referência interna de metadados não pôde ser validada.');
      const changedRoles = new Set(reference.changed_roles || []);
      const summary = Object.fromEntries(Object.entries(reference.summary || {}).map(([catalog, item]) => {
        const affected = catalog !== 'textos' && (item.source_roles || []).some((role) => changedRoles.has(role));
        return [catalog, affected ? { ...item, status: 'bloqueado_fonte_alterada', reason: `A fonte física desta família mudou (${(item.source_roles || []).filter((role) => changedRoles.has(role)).join(', ')}); a referência anterior foi preservada e nenhum item foi promovido.`, new: 0, changed: 0, absent: 0 } : item];
      }));
      const diff = Object.fromEntries(Object.entries(summary).map(([catalog, item]) => [catalog, { status: item.status, reason: item.reason || null, current: item.current || 0, baseline_active: item.baseline_active || 0, new_entries: [], changed_entries: [], absent_entries: [], without_previous_fingerprint: item.without_previous_fingerprint || 0, duplicate_ids: [] }]));
      const textSource = state.sources.dt261_bra;
      if (!textSource || !textSource.bytes) throw new Error('O CPK de textos foi localizado, mas seus bytes não ficaram disponíveis para a comparação.');
      log('log-metadata', 'Extraindo all.str e validando chaves oficiais…');
      const textCatalog = await core.extractTextCatalogFromCpk(textSource.bytes);
      const textStructure = core.validateTextCatalogStructure(textCatalog);
      log('log-metadata', `Estrutura válida: ${textStructure.official_keys.toLocaleString('pt-BR')} chaves oficiais em ${textStructure.sections.toLocaleString('pt-BR')} seções.`);
      const baselineResponse = await fetch('/api/text-baseline/current.json', { cache: 'no-store' });
      const baseline = await baselineResponse.json().catch(() => ({ error: `HTTP ${baselineResponse.status}` }));
      if (!baselineResponse.ok || !baseline.transaction_read_only) throw new Error(baseline.error || 'A fotografia atual de clube_novo.texto_do_jogo não pôde ser lida de modo protegido.');
      if (baseline.duplicate_official_keys) throw new Error('clube_novo.texto_do_jogo contém chave oficial duplicada.');
      const textDiff = core.compareTextCatalog(textCatalog, baseline.rows || []);
      diff.textos = textDiff;
      summary.textos = {
        status: 'comparado', reason: baseline.schema_ready ? null : 'contrato estrutural ainda não instalado; comparação disponível e aplicação bloqueada',
        current: textDiff.current, baseline_active: textDiff.baseline_active,
        new: textDiff.new_entries.length, changed: textDiff.changed_entries.length, absent: 0,
        without_previous_fingerprint: 0, duplicate_ids: 0, source_roles: ['dt261_bra']
      };
      const textItems = [
        ...textDiff.new_entries.map((record) => ({ key: `textos:new:${record.id}`, catalog: 'textos', action: 'new', id: record.id, record })),
        ...textDiff.changed_entries.map((entry) => ({ key: `textos:change:${entry.id}`, catalog: 'textos', action: 'change', id: entry.id, record: entry.record, before: entry.before, after: entry.after }))
      ];
      const selectionContract = {
        algorithm: 'sha256/canonical-json',
        items: await Promise.all(textItems.map(async (item) => {
          const normalized = { catalog: item.catalog, action: item.action, id: item.id, record: item.record };
          if (item.before) normalized.before = item.before;
          if (item.after) normalized.after = item.after;
          return { key: `${item.catalog}:${item.action}:${item.id}`, sha256: await core.sha256(core.stableJson(normalized)) };
        }))
      };
      const totals = Object.values(summary).reduce((acc, item) => ({ new: acc.new + Number(item.new || 0), changed: acc.changed + Number(item.changed || 0), absent: acc.absent + Number(item.absent || 0) }), { new: 0, changed: 0, absent: 0 });
      const textCounts = { new: textDiff.new_entries.length, changed: textDiff.changed_entries.length, possibly_inactive: 0 };
      const manifest = await core.sealManifest({
        contract: core.CONTRACT_VERSION, mode: 'metadata_diff', execution_id: core.makeExecutionId(), generated_at: new Date().toISOString(), expires_at: core.expirationFromNow(60), database_write: false,
        source_authority: 'dt261_bra_console_win.cpk/all.str; chave oficial secao + id_texto; banco somente como base de comparação',
        reference_id: reference.reference_id, source_matches_reference: reference.source_matches_current_reference, changed_roles: [...changedRoles],
        target: 'clube_novo.texto_do_jogo', preserved_schema: 'clube', counts: textCounts, selection_contract: selectionContract,
        text_validation: textDiff.validation, text_source: sourceDescriptor('dt261_bra'), text_baseline: { records: baseline.records, sha256: baseline.sha256, transaction_read_only: true, schema_ready: baseline.schema_ready }, summary
      });
      state.metadata = { reference, baseline, textCatalog, textItems, diff, summary, manifest, selection: new Set(textItems.map((item) => item.key)) };
      const supportedCount = Object.values(summary).filter((item) => item.status !== 'nao_suportado_nesta_atualizacao').length;
      const unsupportedCount = Object.values(summary).filter((item) => item.status === 'nao_suportado_nesta_atualizacao').length;
      setStats('stats-metadata', [['famílias suportadas', supportedCount], ['não suportadas', unsupportedCount], ['novas', totals.new], ['alteradas', totals.changed], ['ausentes', totals.absent]]);
      $('metadata-support').innerHTML = Object.entries(summary).map(([name, item]) => item.status === 'nao_suportado_nesta_atualizacao'
        ? `<div class="support-item unsupported"><b>${escapeHtml(name)}</b> — Não suportada nesta atualização. ${escapeHtml(item.reason || '')}</div>`
        : item.status === 'bloqueado_fonte_alterada'
          ? `<div class="support-item unsupported"><b>${escapeHtml(name)}</b> — Verificação bloqueada. ${escapeHtml(item.reason || '')}</div>`
          : `<div class="support-item"><b>${escapeHtml(name)}</b> — ${escapeHtml(name === 'textos' ? (item.new || item.changed ? `${item.new} novas chaves · ${item.changed} atualizadas · 0 remoções sem substituição` : `Tudo atualizado; ${Number(item.current || 0).toLocaleString('pt-BR')} chaves oficiais conferidas.`) : item.status === 'comparado' ? 'Tudo atualizado; fonte física igual à referência interna vigente.' : item.reason || item.status)}</div>`).join('');
      renderMetadataReview(); $('result-metadata').hidden = false;
      const blockedRoles = [...changedRoles].filter((role) => role !== 'dt261_bra');
      const blocked = blockedRoles.length > 0 || !baseline.schema_ready;
      const changes = totals.new + totals.changed + totals.absent;
      if (blocked) {
        const reason = !baseline.schema_ready ? 'O contrato estrutural de texto ainda não está instalado; o diff foi preservado, mas o envio ficou bloqueado.' : `Fonte alterada sem adaptador: ${blockedRoles.join(', ')}.`;
        setOperationStatus('metadata-status', 'error', 'Metadados comparados com bloqueio de aplicação', reason);
        state.automatic.metadata = { state: 'error', pending: Boolean(changes), message: reason };
      } else {
        setOperationStatus('metadata-status', 'success', changes ? 'Atualização de metadados disponível' : 'Metadados conferidos — nada para atualizar', changes ? `${totals.new} novas · ${totals.changed} alteradas · ${totals.absent} ausentes.` : 'As fontes são as mesmas da referência interna vigente.');
        state.automatic.metadata = { state: 'ready', pending: Boolean(changes), message: changes ? `${totals.new} novas · ${totals.changed} alteradas · ${totals.absent} ausentes.` : 'Nada para atualizar nas famílias suportadas; as demais continuam identificadas como não suportadas.' };
      }
      renderAutomaticSummary();
      log('log-metadata', `Concluído: ${textDiff.current} chaves oficiais conferidas; ${textDiff.new_entries.length} novas e ${textDiff.changed_entries.length} atualizadas; nenhuma escrita foi feita.`);
    } catch (error) {
      log('log-metadata', `BLOQUEADO: ${error.message}`);
      setOperationStatus('metadata-status', 'error', 'Comparação de metadados bloqueada', `${error.message} Nenhuma escrita foi feita.`);
      state.automatic.metadata = { state: 'error', pending: false, message: `Metadados: ${error.message}` };
      renderAutomaticSummary();
      $('metadata-support').innerHTML = `<div class="support-item unsupported"><b>Verificação bloqueada</b> — ${escapeHtml(error.message)}</div>`;
      $('table-metadata').innerHTML = '<div class="callout">Nenhum item foi promovido ou selecionado.</div>';
      $('result-metadata').hidden = false;
    } finally {
      state.metadataRunning = false;
      updateRunAvailability();
      updateMetadataApplySummary();
    }
  }
  $('run-metadata').addEventListener('click', () => refreshMetadataAutomatically('botão Comparar metadados novamente'));
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

  async function postJson(url, body, timeoutMs = 0) {
    const controller = timeoutMs ? new AbortController() : null;
    const timeout = controller ? setTimeout(() => controller.abort(), timeoutMs) : null;
    let response;
    try {
      response = await fetch(url, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body), signal: controller ? controller.signal : undefined });
    } catch (error) {
      if (error && error.name === 'AbortError') throw new Error('A conexão demorou além do limite seguro. O estado será conferido antes de permitir nova tentativa.');
      throw error;
    } finally { if (timeout) clearTimeout(timeout); }
    const payload = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    return payload;
  }
  const allowStatusPaint = () => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
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
    button.setAttribute('aria-busy', 'true');
    button.textContent = 'Preparando pré-voo…';
    $('approval-card-package').hidden = true;
    setNamedOperationStatus('card-package-preflight', 'loading', 'Preparando o envio com segurança', 'Lendo clube_novo e conferindo o pacote selado. Nenhum dado está sendo gravado.');
    let stageTimer = null;
    try {
      await allowStatusPaint();
      stageTimer = setTimeout(() => setNamedOperationStatus('card-package-preflight', 'loading', 'Pré-voo ainda em andamento', 'A leitura do banco pode levar alguns instantes; não clique novamente.'), 2500);
      if (!state.cardPackage) throw new Error('Execute e valide uma carga antes de continuar.');
      core.ensureCurrentManifest(state.cardPackage.manifest);
      const prepared = await postJson('/api/card-package/prepare', { manifest: state.cardPackage.manifest, package: state.cardPackage.package }, 120000);
      if (!prepared || !prepared.summary || !prepared.target || !prepared.execution_id) throw new Error('O pré-voo retornou vazio ou incompleto; nenhum envio foi liberado.');
      configureCardPackageApproval(prepared);
      if (prepared.no_changes) {
        setNamedOperationStatus('card-package-preflight', 'success', 'Sem mudanças para enviar', 'clube_novo já corresponde integralmente ao pacote validado.');
        button.textContent = 'Sem mudanças para enviar';
      } else {
        setNamedOperationStatus('card-package-preflight', 'success', 'Pré-voo concluído', `${prepared.summary.insert || 0} inserir · ${prepared.summary.update || 0} atualizar · ${prepared.summary.inactive || 0} inativar. Faça a confirmação final abaixo.`);
        button.textContent = 'Refazer pré-voo';
      }
    } catch (error) {
      $('approval-card-package').hidden = false;
      $('card-package-confirmation').hidden = true;
      $('approval-preview-card-package').textContent = `ENVIO BLOQUEADO — ${error.message}`;
      $('apply-lock-card-package').textContent = 'Nenhum dado foi enviado. O pacote validado permanece disponível para novo pré-voo.';
      $('apply-button-card-package').disabled = true;
      setNamedOperationStatus('card-package-preflight', 'error', 'Pré-voo bloqueado', `${error.message} Nenhum dado foi enviado.`);
      button.textContent = 'Tentar preparar novamente';
    } finally {
      if (stageTimer) clearTimeout(stageTimer);
      button.removeAttribute('aria-busy');
      button.disabled = !state.cardPackage || !state.executor.online || state.cardPackage.no_changes;
    }
  });
  $('prepare-metadata').addEventListener('click', async () => {
    if (state.metadataRunning || state.applying) return;
    const button = $('prepare-metadata');
    try {
      state.metadataRunning = true;
      button.disabled = true;
      button.textContent = 'Preparando textos…';
      button.setAttribute('aria-busy', 'true');
      setNamedOperationStatus('metadata-preflight', 'loading', 'Preparando textos — aguarde', 'Conferindo chaves, procedência e referências de catálogo em leitura protegida.');
      await allowStatusPaint();
      core.ensureCurrentManifest(state.metadata.manifest);
      const items = metadataReviewRows(state.metadata.diff).filter((row) => state.metadata.selection.has(row.key));
      const prepared = await postJson('/api/prepare', { manifest: state.metadata.manifest, selection: { kind: 'metadata', items } });
      if (!prepared || !prepared.execution_id || !prepared.summary || !prepared.preflight) throw new Error('O pré-voo retornou vazio ou incompleto; nenhum envio foi liberado.');
      configureApproval('metadata', prepared);
      setNamedOperationStatus('metadata-preflight', 'success', 'Pré-voo concluído', `${prepared.summary.insert || 0} inserir · ${prepared.summary.update || 0} atualizar · 0 excluir. Confirme o pacote abaixo.`);
    } catch (error) {
      setNamedOperationStatus('metadata-preflight', 'error', 'Preparação bloqueada', `${error.message} Nenhum dado foi enviado.`);
      button.textContent = 'Tentar preparar textos novamente';
    } finally {
      state.metadataRunning = false;
      button.removeAttribute('aria-busy');
      updateMetadataApplySummary();
    }
  });
  async function waitForMetadataApplyResult(executionId) {
    for (let attempt = 0; attempt < 90; attempt += 1) {
      const status = await fetchApplyStatus(executionId);
      if (status.state === 'completed' && status.application_manifest) return { application_manifest: status.application_manifest, idempotent_reuse: true };
      if (status.state === 'failed') throw new Error(status.error || 'A transação falhou e foi encerrada sem conclusão.');
      setNamedOperationStatus('metadata-apply', 'loading', 'Aplicando textos — não clique novamente', `Transação identificada e protegida contra repetição (${attempt + 1}).`);
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
    throw new Error('A confirmação está demorando. Não clique novamente; reabra o aplicativo para consultar esta execução.');
  }
  $('apply-button-metadata').addEventListener('click', async () => {
    if (state.applying) return;
    const button = $('apply-button-metadata');
    let executionId = '';
    try {
      const prepared = state.approvals.metadata;
      if (!prepared || !prepared.execution_id) throw new Error('Faça o pré-voo deste pacote novamente.');
      executionId = prepared.execution_id;
      state.applying = true;
      document.body.classList.add('busy-lock');
      button.disabled = true;
      button.setAttribute('aria-busy', 'true');
      button.textContent = 'Aplicando textos…';
      $('approval-check-metadata').disabled = true;
      $('approval-text-metadata').disabled = true;
      $('prepare-metadata').disabled = true;
      setNamedOperationStatus('metadata-apply', 'loading', 'Aplicando textos — não clique novamente', 'A transação está em andamento. O identificador único impede envio duplicado.');
      await allowStatusPaint();
      let result;
      try {
        result = await postJson('/api/apply', { approval_token: prepared.approval_token, confirmation: $('approval-text-metadata').value.trim(), request_id: executionId }, 180000);
        if (result.state === 'applying') result = await waitForMetadataApplyResult(executionId);
      } catch (requestError) {
        setNamedOperationStatus('metadata-apply', 'loading', 'Conferindo a execução antes de liberar nova tentativa', 'A resposta direta falhou; consultando o identificador único no executor.');
        try { result = await waitForMetadataApplyResult(executionId); }
        catch (statusError) { throw new Error(`${requestError.message} ${statusError.message}`.trim()); }
      }
      if (!result || !result.application_manifest) throw new Error('O executor não devolveu o manifesto final; nenhuma repetição foi liberada.');
      const readback = result.application_manifest.result || {};
      setNamedOperationStatus('metadata-apply', 'success', 'Textos aplicados e conferidos', `${readback.changed || 0} alterações · ${readback.already_applied || 0} já aplicadas · ${readback.readback_count || 0} chaves conferidas.`);
      button.textContent = 'Textos aplicados e conferidos';
      download('MANIFESTO-APLICACAO-TEXTOS.json', `${JSON.stringify(result.application_manifest, null, 2)}\n`, 'application/json');
      await refreshExecutorStatus();
    } catch (error) {
      setNamedOperationStatus('metadata-apply', 'error', 'Aplicação bloqueada ou não confirmada', `${error.message} Não repita o envio sem conferir este estado.`);
      button.textContent = 'Tentar novamente com esta execução';
      button.disabled = false;
      $('approval-check-metadata').disabled = false;
      $('approval-text-metadata').disabled = false;
    } finally {
      state.applying = false;
      document.body.classList.remove('busy-lock');
      button.removeAttribute('aria-busy');
    }
  });
  async function fetchApplyStatus(executionId) {
    const response = await fetch(`/api/apply/status?execution_id=${encodeURIComponent(executionId)}`, { cache: 'no-store' });
    const payload = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    return payload;
  }
  async function waitForApplyResult(executionId) {
    for (let attempt = 0; attempt < 90; attempt += 1) {
      const status = await fetchApplyStatus(executionId);
      if (status.state === 'completed' && status.application_manifest) return { application_manifest: status.application_manifest, idempotent_reuse: true };
      if (status.state === 'failed') throw new Error(status.error || 'A transação falhou e foi encerrada sem conclusão.');
      setNamedOperationStatus('card-package-apply', 'loading', 'Aplicando carga — aguarde', `Transação em andamento e protegida contra repetição (${attempt + 1}).`);
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
    throw new Error('A confirmação está demorando. Não clique novamente; feche e abra o aplicativo para verificar o estado da execução.');
  }
  function showApplySuccess(result) {
    const manifest = result.application_manifest;
    const readback = manifest.result || {};
    setNamedOperationStatus('card-package-apply', 'success', 'Carga aplicada e conferida', `${readback.changed || 0} alterações gravadas · ${readback.already_applied || 0} já estavam aplicadas · ${readback.readback_count || 0} registros conferidos. Execução ${manifest.execution_id}.`);
    $('apply-button-card-package').textContent = 'Carga aplicada e conferida';
    $('apply-button-card-package').disabled = true;
    $('approval-check-card-package').disabled = true;
    $('approval-text-card-package').disabled = true;
    $('prepare-card-package').disabled = true;
    $('apply-lock-card-package').textContent = 'Concluído com leitura posterior. Repetições desta mesma execução são reutilizadas com segurança e não geram nova carga.';
  }
  $('apply-button-card-package').addEventListener('click', async () => {
    if (state.applying) return;
    const button = $('apply-button-card-package');
    let executionId = '';
    try {
      const prepared = state.cardPackage && state.cardPackage.prepared;
      if (!prepared) throw new Error('Faça o pré-voo deste pacote novamente.');
      executionId = prepared.execution_id;
      if (!executionId) throw new Error('O identificador único do pacote não foi recebido; aplicação bloqueada.');
      state.applying = true;
      document.body.classList.add('busy-lock');
      button.disabled = true;
      button.setAttribute('aria-busy', 'true');
      button.textContent = 'Aplicando carga…';
      $('approval-check-card-package').disabled = true;
      $('approval-text-card-package').disabled = true;
      $('prepare-card-package').disabled = true;
      setNamedOperationStatus('card-package-apply', 'loading', 'Aplicando carga — não clique novamente', 'A transação está em andamento. O pacote possui um identificador único e repetições são bloqueadas pelo servidor.');
      await allowStatusPaint();
      let result;
      try {
        result = await postJson('/api/apply', { approval_token: prepared.approval_token, confirmation: $('approval-text-card-package').value.trim(), request_id: executionId });
        if (result.state === 'applying') result = await waitForApplyResult(executionId);
      } catch (requestError) {
        setNamedOperationStatus('card-package-apply', 'loading', 'Conferindo o resultado da execução', 'A resposta direta falhou; o aplicativo está consultando o identificador único antes de permitir qualquer nova ação.');
        try { result = await waitForApplyResult(executionId); }
        catch (statusError) { throw new Error(`${requestError.message} ${statusError.message}`.trim()); }
      }
      if (!result || !result.application_manifest) throw new Error('O servidor não devolveu o manifesto de aplicação; nenhuma repetição será liberada até nova conferência.');
      showApplySuccess(result);
      await refreshExecutorStatus();
    } catch (error) {
      setNamedOperationStatus('card-package-apply', 'error', 'Aplicação bloqueada ou não confirmada', `${error.message} Não repita o envio sem usar “Tentar novamente” após conferir este estado.`);
      button.textContent = 'Tentar novamente com este pacote';
      button.disabled = false;
      $('approval-check-card-package').disabled = false;
      $('approval-text-card-package').disabled = false;
      $('apply-lock-card-package').textContent = 'A nova tentativa é deliberada e reutiliza o mesmo identificador; o servidor impede aplicação duplicada.';
    } finally {
      state.applying = false;
      document.body.classList.remove('busy-lock');
      button.removeAttribute('aria-busy');
    }
  });

  refreshExecutorStatus().then(() => { updateCardApplySummary(); updateMetadataApplySummary(); });
  refreshSources();
})(globalThis);
