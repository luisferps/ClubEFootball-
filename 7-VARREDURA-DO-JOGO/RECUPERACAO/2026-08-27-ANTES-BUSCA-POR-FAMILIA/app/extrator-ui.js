'use strict';

(function installUi(global) {
  const core = global.CLUBEF_CORE;
  const state = {
    executor: { online: false, write_enabled: false, mode: 'offline' },
    incremental: null,
    metadata: null,
    full: null,
    approvals: {}
  };
  const $ = (id) => document.getElementById(id);
  const escapeHtml = (value) => String(value == null ? '' : value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));

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
      $('executor-dot').className = `dot ${state.executor.write_enabled ? 'warn' : 'ok'}`;
      $('executor-title').textContent = state.executor.write_enabled ? 'Executor local · escrita habilitada' : 'Executor local · dry-run';
      $('executor-detail').textContent = state.executor.write_enabled ? 'nenhuma ação sem confirmação' : 'banco protegido; sem escrita real';
    } catch (error) {
      state.executor = { online: false, write_enabled: false, mode: 'offline' };
      $('executor-dot').className = 'dot neutral';
      $('executor-title').textContent = 'Executor local desconectado';
      $('executor-detail').textContent = 'extração funciona; aplicação indisponível';
    }
  }

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
    if (!state.incremental) return;
    const summary = core.selectionSummary(state.incremental.diff, [...state.incremental.selection]);
    $('apply-summary-incremental').textContent = `${summary.counts.insert} inserções · ${summary.counts.update} alterações · ${summary.counts.inactive} possíveis inativações selecionadas`;
    $('prepare-incremental').disabled = !summary.items.length || !state.executor.online;
  }

  $('inc-base').addEventListener('change', () => { setFileName('inc-base', 'inc-base-name'); $('run-incremental').disabled = !($('inc-base').files[0] && $('inc-cpk').files[0]); });
  $('inc-cpk').addEventListener('change', () => { setFileName('inc-cpk', 'inc-cpk-name'); $('run-incremental').disabled = !($('inc-base').files[0] && $('inc-cpk').files[0]); });
  $('run-incremental').addEventListener('click', async () => {
    const button = $('run-incremental');
    button.disabled = true;
    $('result-incremental').hidden = true;
    log('log-incremental', 'Iniciando leitura controlada…', true);
    try {
      const baselineFile = $('inc-base').files[0];
      const cpkFile = $('inc-cpk').files[0];
      const baselineText = await baselineFile.text();
      const baseline = core.parseCsv(baselineText);
      core.validateSchema(baseline.headers);
      log('log-incremental', `Base atual: ${baseline.rows.length} cartas.`);
      const cpkBytes = new Uint8Array(await cpkFile.arrayBuffer());
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
        current_source: { file: cpkFile.name, bytes: cpkFile.size, modified_at: new Date(cpkFile.lastModified).toISOString(), sha256: await core.sha256(cpkBytes) },
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
      state.incremental = { baseline, cards, currentRows, diff, manifest, selection: defaultCardSelection(diff) };
      setStats('stats-incremental', [['atuais', currentRows.length], ['novas', diff.new_cards.length], ['alteradas', diff.changed_cards.length], ['possíveis inativas', diff.possibly_inactive.length], ['duplicadas', 0]]);
      renderCardReview();
      $('result-incremental').hidden = false;
      log('log-incremental', 'Concluído: somente o diff foi preparado; nenhum dado foi aplicado.');
    } catch (error) {
      log('log-incremental', `BLOQUEADO: ${error.message}`);
      alert(error.message);
    } finally {
      button.disabled = !($('inc-base').files[0] && $('inc-cpk').files[0]);
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
      for (const record of catalogDiff.new_entries) rows.push({ key: `${catalog}:new:${record.id}`, catalog, action: 'new', label: 'NOVA', id: record.id, detail: 'nova entrada física', record });
      for (const entry of catalogDiff.changed_entries) rows.push({ key: `${catalog}:change:${entry.id}`, catalog, action: 'change', label: 'ALTERADA', id: entry.id, detail: 'fingerprint físico mudou', record: entry.record, before: entry.before, after: entry.after });
      for (const entry of catalogDiff.absent_entries) rows.push({ key: `${catalog}:absent:${entry.id}`, catalog, action: 'inactive', label: 'AUSENTE', id: entry.id, detail: 'não aparece na fonte física atual', record: entry.record });
    }
    return rows;
  }
  function renderMetadataReview() {
    const rows = metadataReviewRows(state.metadata.diff);
    $('table-metadata').innerHTML = rows.length ? `<table><thead><tr><th>usar</th><th>catálogo</th><th>ação</th><th>id</th><th>evidência</th></tr></thead><tbody>${rows.map((row) => `<tr><td><input class="metadata-choice" type="checkbox" data-key="${escapeHtml(row.key)}"></td><td>${escapeHtml(row.catalog)}</td><td class="action-${row.action}">${row.label}</td><td><code>${escapeHtml(row.id)}</code></td><td>${escapeHtml(row.detail)}</td></tr>`).join('')}</tbody></table>` : '<div class="callout">Nenhuma entrada nova, alterada ou ausente foi comprovada.</div>';
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
  $('meta-base').addEventListener('change', () => { setFileName('meta-base', 'meta-base-name'); $('run-metadata').disabled = !($('meta-base').files[0] && $('meta-cpk').files[0]); });
  $('meta-cpk').addEventListener('change', () => { setFileName('meta-cpk', 'meta-cpk-name'); $('run-metadata').disabled = !($('meta-base').files[0] && $('meta-cpk').files[0]); });
  $('run-metadata').addEventListener('click', async () => {
    const button = $('run-metadata'); button.disabled = true; $('result-metadata').hidden = true;
    log('log-metadata', 'Lendo catálogos físicos…', true);
    try {
      const baselineFile = $('meta-base').files[0];
      const cpkFile = $('meta-cpk').files[0];
      const baseline = JSON.parse(await baselineFile.text());
      if (!baseline.catalogs) throw new Error('Referência JSON sem objeto catalogs.');
      const cpkBytes = new Uint8Array(await cpkFile.arrayBuffer());
      const current = await core.extractMetadataFromCpk(cpkBytes, { file: cpkFile.name, bytes: cpkFile.size, sha256: await core.sha256(cpkBytes) }, (message) => log('log-metadata', message));
      const diff = core.compareMetadata(current, baseline);
      const summary = Object.fromEntries(Object.entries(diff).map(([catalog, item]) => [catalog, { status: item.status, reason: item.reason || null, current: item.current, baseline_active: item.baseline_active, new: item.new_entries.length, changed: item.changed_entries.length, absent: item.absent_entries.length, without_previous_fingerprint: item.without_previous_fingerprint, duplicate_ids: item.duplicate_ids.length }]));
      if (Object.values(summary).some((item) => item.duplicate_ids)) throw new Error('Catálogo físico contém chave duplicada.');
      const totals = Object.values(summary).reduce((acc, item) => ({ new: acc.new + item.new, changed: acc.changed + item.changed, absent: acc.absent + item.absent }), { new: 0, changed: 0, absent: 0 });
      const applicableItems = metadataReviewRows(diff).map((item) => Object.fromEntries(['catalog', 'action', 'id', 'record', 'before', 'after'].filter((key) => key in item).map((key) => [key, item[key]])));
      const selectionContract = { algorithm: 'sha256/canonical-json', items: await Promise.all(applicableItems.map(async (item) => ({ key: `${item.catalog}:${item.action}:${item.id}`, sha256: await core.sha256(core.stableJson(item)) }))) };
      const manifest = await core.sealManifest({ contract: core.CONTRACT_VERSION, mode: 'metadata_diff', execution_id: core.makeExecutionId(), generated_at: new Date().toISOString(), expires_at: core.expirationFromNow(60), database_write: false, source_authority: 'catálogos físicos atuais; referência usada apenas para comparação', current_source: current.source, baseline: { file: baselineFile.name, bytes: baselineFile.size, sha256: await fileSha(baselineFile) }, counts: { new: totals.new, changed: totals.changed, possibly_inactive: totals.absent }, selection_contract: selectionContract, summary });
      state.metadata = { baseline, current, diff, summary, manifest, selection: new Set() };
      setStats('stats-metadata', [['catálogos', Object.keys(summary).length], ['novas', totals.new], ['alteradas', totals.changed], ['ausentes', totals.absent]]);
      renderMetadataReview(); $('result-metadata').hidden = false;
      log('log-metadata', 'Concluído: diferenças revisáveis preparadas; nenhum catálogo foi aplicado.');
    } catch (error) {
      log('log-metadata', `BLOQUEADO: ${error.message}`); alert(error.message);
    } finally { button.disabled = !($('meta-base').files[0] && $('meta-cpk').files[0]); }
  });
  $('download-metadata-diff').addEventListener('click', () => download('METADADOS-DIFF.json', `${JSON.stringify(Object.fromEntries(Object.entries(state.metadata.diff).map(([name, item]) => [name, { new_entries: item.new_entries, changed_entries: item.changed_entries, absent_entries: item.absent_entries }])), null, 2)}\n`, 'application/json'));
  $('download-metadata-manifest').addEventListener('click', () => download('MANIFESTO-METADADOS-DIFF.json', `${JSON.stringify(state.metadata.manifest, null, 2)}\n`, 'application/json'));

  function enableFull() {
    $('run-full').disabled = !($('full-cpk').files[0] && $('full-check').checked && $('full-text').value.trim() === 'RECARREGAR COMPLETO');
  }
  $('full-cpk').addEventListener('change', () => { setFileName('full-cpk', 'full-cpk-name'); enableFull(); });
  $('full-base').addEventListener('change', () => setFileName('full-base', 'full-base-name'));
  $('full-check').addEventListener('change', enableFull);
  $('full-text').addEventListener('input', enableFull);
  $('run-full').addEventListener('click', async () => {
    const button = $('run-full'); button.disabled = true; $('result-full').hidden = true;
    log('log-full', 'Executando contingência completa…', true);
    try {
      const cpkFile = $('full-cpk').files[0];
      const baselineFile = $('full-base').files[0];
      const cpkBytes = new Uint8Array(await cpkFile.arrayBuffer());
      const cards = await core.extractCardsFromCpk(cpkBytes, (message) => log('log-full', message));
      const validation = core.validateCards(cards);
      if (validation.duplicate_card_ids.length) throw new Error('Recarga bloqueada: card_id duplicado.');
      const fullCsv = core.cardsToCsv(cards);
      const fullCsvSha256 = await core.sha256(fullCsv);
      let baseline = null, diff = null;
      let golden = null;
      if (baselineFile) {
        baseline = core.parseCsv(await baselineFile.text()); core.validateSchema(baseline.headers);
        diff = core.compareCardRows(cards.map(core.cardToRow), baseline.rows);
        const baselineSha256 = await fileSha(baselineFile);
        golden = {
          file: baselineFile.name,
          records: baseline.rows.length,
          sha256: baselineSha256,
          extracted_sha256: fullCsvSha256,
          logical_exact: baseline.rows.length === cards.length && diff.new_cards.length === 0 && diff.changed_cards.length === 0 && diff.possibly_inactive.length === 0,
          byte_exact: baselineSha256 === fullCsvSha256,
        };
      }
      const manifest = await core.sealManifest({ contract: core.CONTRACT_VERSION, mode: 'full_reload_contingency', execution_id: core.makeExecutionId(), generated_at: new Date().toISOString(), expires_at: core.expirationFromNow(30), database_write: false, double_confirmation: true, source: { file: cpkFile.name, bytes: cpkFile.size, sha256: await core.sha256(cpkBytes) }, extracted_csv_sha256: fullCsvSha256, validation, golden_test: golden, optional_diff: diff ? { baseline: baseline.rows.length, current: cards.length, new: diff.new_cards.length, changed: diff.changed_cards.length, possibly_inactive: diff.possibly_inactive.length } : null });
      state.full = { cards, baseline, diff, manifest, fullCsv };
      setStats('stats-full', [['cartas', cards.length], ['IDs únicos', validation.unique_card_ids], ['duplicadas', validation.duplicate_card_ids.length], ['campos', core.CARD_COLUMNS.length], ['gabarito', golden ? (golden.logical_exact && golden.byte_exact ? 'EXATO' : 'DIVERGENTE') : 'não informado']]);
      $('full-golden-status').textContent = golden
        ? (golden.logical_exact && golden.byte_exact
          ? `GABARITO EXATO — ${golden.records} cartas e SHA-256 ${golden.sha256}.`
          : `GABARITO DIVERGENTE — lógico: ${golden.logical_exact ? 'igual' : 'diferente'}; fingerprint: ${golden.byte_exact ? 'igual' : 'diferente'}. Revise antes de qualquer aplicação.`)
        : `Carga integral gerada com SHA-256 ${fullCsvSha256}. Selecione o gabarito selado para a prova exata.`;
      $('table-full').innerHTML = `<table><thead><tr><th>card_id</th><th>nome</th><th>tipo</th><th>posição</th><th>overall</th></tr></thead><tbody>${cards.slice(0, 300).map((card) => `<tr><td><code>${escapeHtml(card.card_id)}</code></td><td>${escapeHtml(card.name)}</td><td>${escapeHtml(card.tipo)}</td><td>${escapeHtml(card.position)}</td><td>${escapeHtml(card.overall)}</td></tr>`).join('')}</tbody></table>`;
      $('result-full').hidden = false; log('log-full', golden && golden.logical_exact && golden.byte_exact ? 'Concluído: fotografia completa exatamente igual ao gabarito; nenhum banco foi alterado.' : 'Concluído: fotografia completa gerada localmente; nenhuma referência e nenhum banco foram alterados.');
    } catch (error) { log('log-full', `BLOQUEADO: ${error.message}`); alert(error.message); }
    finally { enableFull(); }
  });
  $('download-full').addEventListener('click', () => download('carta_jogo_COMPLETO-CONTINGENCIA.csv', state.full.fullCsv, 'text/csv;charset=utf-8'));
  $('download-full-manifest').addEventListener('click', () => download('MANIFESTO-RECARGA-COMPLETA.json', `${JSON.stringify(state.full.manifest, null, 2)}\n`, 'application/json'));

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
  $('prepare-incremental').addEventListener('click', async () => {
    try {
      core.ensureCurrentManifest(state.incremental.manifest);
      const selection = core.selectionSummary(state.incremental.diff, [...state.incremental.selection]);
      const prepared = await postJson('/api/prepare', { manifest: state.incremental.manifest, selection: { kind: 'cards', items: selection.items } });
      configureApproval('incremental', prepared);
    } catch (error) { alert(`Preparação bloqueada: ${error.message}`); }
  });
  $('prepare-metadata').addEventListener('click', async () => {
    try {
      core.ensureCurrentManifest(state.metadata.manifest);
      const items = metadataReviewRows(state.metadata.diff).filter((row) => state.metadata.selection.has(row.key));
      const prepared = await postJson('/api/prepare', { manifest: state.metadata.manifest, selection: { kind: 'metadata', items } });
      configureApproval('metadata', prepared);
    } catch (error) { alert(`Preparação bloqueada: ${error.message}`); }
  });
  for (const kind of ['incremental', 'metadata']) {
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

  refreshExecutorStatus().then(() => { updateCardApplySummary(); updateMetadataApplySummary(); });
})(globalThis);
