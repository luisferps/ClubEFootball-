'use strict';

(function installReviewLayer(global) {
  const VERSION = '4.6.11';
  const PHRASE = 'REVISEI AS DIVERGENCIAS';
  const reviews = new Map();
  let activeKind = null;

  const escapeHtml = (value) => String(value == null ? '' : value).replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[character]));

  function kindLabel(kind) {
    return ({ metadata: 'Metadados', cards: 'Cartas', full: 'Recarga completa', family: 'Família' })[kind] || kind;
  }

  function ensurePanel() {
    let panel = document.getElementById('clubef-review-v4611');
    if (panel) return panel;
    panel = document.createElement('section');
    panel.id = 'clubef-review-v4611';
    panel.style.cssText = [
      'position:fixed', 'left:18px', 'bottom:76px', 'z-index:9998',
      'width:min(460px,calc(100vw - 36px))', 'max-height:62vh',
      'padding:14px', 'overflow:auto',
      'border:1px solid rgba(84,219,167,.45)', 'border-radius:14px',
      'background:rgba(10,18,29,.97)', 'color:#eef7ff',
      'box-shadow:0 14px 42px rgba(0,0,0,.42)',
      'font:14px/1.42 system-ui,sans-serif'
    ].join(';');
    panel.innerHTML = `
      <div style="display:flex;gap:12px;align-items:flex-start;justify-content:space-between">
        <div>
          <div style="font-size:11px;font-weight:900;letter-spacing:.12em;text-transform:uppercase;color:#54dba7">Etapa intermediária local</div>
          <div style="font-size:18px;font-weight:900;margin-top:2px">Revisão antes do banco</div>
        </div>
        <button id="clubef-review-collapse" type="button" style="border:1px solid rgba(255,255,255,.18);background:transparent;color:#fff;border-radius:9px;padding:5px 9px;cursor:pointer">−</button>
      </div>
      <div id="clubef-review-body">
        <p id="clubef-review-status" style="margin:9px 0;color:#a9bfd3">Aguardando a primeira fotografia.</p>
        <div id="clubef-review-tabs" style="display:flex;gap:6px;flex-wrap:wrap;margin:8px 0"></div>
        <div id="clubef-review-summary"></div>
        <div id="clubef-review-actions" style="display:none;gap:7px;flex-wrap:wrap;margin-top:10px">
          <button id="clubef-review-details" type="button">Ver divergências</button>
          <button id="clubef-review-download" type="button">Baixar revisão</button>
        </div>
        <div id="clubef-review-confirm" style="display:none;margin-top:11px;padding-top:11px;border-top:1px solid rgba(255,255,255,.13)">
          <div style="font-weight:800">Nada será enviado sem esta confirmação.</div>
          <label style="display:block;margin-top:7px">Digite <code>${PHRASE}</code></label>
          <input id="clubef-review-phrase" type="text" autocomplete="off" style="width:100%;box-sizing:border-box;margin-top:5px;padding:9px;border-radius:8px;border:1px solid rgba(255,255,255,.2);background:#08111d;color:#fff">
          <button id="clubef-review-ack" type="button" disabled style="width:100%;margin-top:7px;padding:10px;font-weight:900">Confirmar que revisei</button>
        </div>
      </div>`;
    document.body.appendChild(panel);

    const buttonStyle = 'border:1px solid rgba(255,255,255,.18);background:#13243a;color:#fff;border-radius:9px;padding:8px 10px;cursor:pointer;font-weight:750';
    panel.querySelectorAll('button').forEach((button) => {
      if (button.id !== 'clubef-review-collapse') button.style.cssText += `;${buttonStyle}`;
    });
    document.getElementById('clubef-review-collapse').addEventListener('click', () => {
      const body = document.getElementById('clubef-review-body');
      const collapsed = body.style.display === 'none';
      body.style.display = collapsed ? '' : 'none';
      document.getElementById('clubef-review-collapse').textContent = collapsed ? '−' : '+';
    });
    document.getElementById('clubef-review-details').addEventListener('click', showDetails);
    document.getElementById('clubef-review-download').addEventListener('click', downloadActive);
    document.getElementById('clubef-review-phrase').addEventListener('input', (event) => {
      document.getElementById('clubef-review-ack').disabled = event.target.value.trim() !== PHRASE;
    });
    document.getElementById('clubef-review-ack').addEventListener('click', acknowledgeActive);
    return panel;
  }

  function renderTabs() {
    ensurePanel();
    const tabs = document.getElementById('clubef-review-tabs');
    tabs.innerHTML = [...reviews.keys()].map((kind) => {
      const item = reviews.get(kind);
      const selected = kind === activeKind;
      const tone = item.status === 'reviewed' ? '#1f9d70' : '#7a5220';
      return `<button type="button" data-review-kind="${escapeHtml(kind)}" style="border:1px solid ${tone};background:${selected ? 'rgba(84,219,167,.16)' : 'transparent'};color:#fff;border-radius:999px;padding:6px 9px;cursor:pointer">${escapeHtml(kindLabel(kind))}${item.status === 'reviewed' ? ' ✓' : ''}</button>`;
    }).join('');
    tabs.querySelectorAll('[data-review-kind]').forEach((button) => button.addEventListener('click', () => {
      activeKind = button.dataset.reviewKind;
      render();
    }));
  }

  function issueSummary(record) {
    const payload = record.payload || {};
    const application = payload.application || {};
    const blocked = application.blocked_families || [];
    const allowed = application.allowed_families || [];
    const summary = payload.summary || {};
    const totals = Object.values(summary).reduce((acc, item) => ({
      new: acc.new + Number(item && item.new || 0),
      changed: acc.changed + Number(item && item.changed || 0),
      absent: acc.absent + Number(item && item.absent || 0)
    }), { new: 0, changed: 0, absent: 0 });
    return { blocked, allowed, totals };
  }

  function render() {
    ensurePanel();
    renderTabs();
    const status = document.getElementById('clubef-review-status');
    const summaryBox = document.getElementById('clubef-review-summary');
    const actions = document.getElementById('clubef-review-actions');
    const confirm = document.getElementById('clubef-review-confirm');
    const record = activeKind ? reviews.get(activeKind) : null;
    if (!record) {
      status.textContent = 'Aguardando a primeira fotografia.';
      summaryBox.innerHTML = '';
      actions.style.display = 'none';
      confirm.style.display = 'none';
      return;
    }

    const info = issueSummary(record);
    const reviewed = record.status === 'reviewed' && Boolean(record.review_token);
    status.textContent = reviewed
      ? `${kindLabel(activeKind)} revisado. Somente famílias sem divergência podem seguir para a confirmação final.`
      : `${kindLabel(activeKind)} salvo localmente. Confira as divergências antes de liberar qualquer escrita.`;
    const blockedText = info.blocked.length ? info.blocked.join(', ') : 'nenhuma';
    const allowedText = info.allowed.length ? info.allowed.join(', ') : 'nenhuma';
    summaryBox.innerHTML = `
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-top:8px">
        <div style="padding:8px;border:1px solid rgba(255,255,255,.12);border-radius:9px"><b>${info.totals.new}</b><br><small>novos</small></div>
        <div style="padding:8px;border:1px solid rgba(255,255,255,.12);border-radius:9px"><b>${info.totals.changed}</b><br><small>alterados</small></div>
        <div style="padding:8px;border:1px solid rgba(255,255,255,.12);border-radius:9px"><b>${info.totals.absent}</b><br><small>ausentes</small></div>
      </div>
      <div style="margin-top:8px;padding:9px;border-radius:9px;background:rgba(255,170,70,.09)"><b>Bloqueadas:</b> ${escapeHtml(blockedText)}</div>
      <div style="margin-top:6px;padding:9px;border-radius:9px;background:rgba(84,219,167,.08)"><b>Aptas após revisão:</b> ${escapeHtml(allowedText)}</div>
      <div style="margin-top:6px;font-size:12px;color:#9fb4c8;word-break:break-all">Arquivo local: ${escapeHtml(record.review_file || '')}</div>`;
    actions.style.display = 'flex';
    confirm.style.display = reviewed ? 'none' : 'block';
    if (!reviewed) {
      document.getElementById('clubef-review-phrase').value = '';
      document.getElementById('clubef-review-ack').disabled = true;
    }
  }

  function openJsonDialog(title, record) {
    let overlay = document.getElementById('clubef-review-overlay');
    if (overlay) overlay.remove();
    overlay = document.createElement('div');
    overlay.id = 'clubef-review-overlay';
    overlay.style.cssText = 'position:fixed;inset:0;z-index:10020;background:rgba(0,0,0,.78);display:grid;place-items:center;padding:20px';
    overlay.innerHTML = `<section style="width:min(1100px,96vw);max-height:92vh;overflow:auto;background:#08111d;color:#eaf4ff;border:1px solid rgba(255,255,255,.2);border-radius:14px;padding:16px;box-shadow:0 18px 70px rgba(0,0,0,.6)">
      <div style="display:flex;justify-content:space-between;gap:12px;align-items:center"><h2 style="margin:0">${escapeHtml(title)}</h2><button id="clubef-review-close" type="button" style="padding:8px 11px">Fechar</button></div>
      <p style="color:#a9bfd3">Esta é a fotografia intermediária local. Nenhuma escrita no banco ocorre nesta tela.</p>
      <pre style="white-space:pre-wrap;word-break:break-word;background:#050b13;padding:13px;border-radius:10px;max-height:72vh;overflow:auto">${escapeHtml(JSON.stringify(record, null, 2))}</pre>
    </section>`;
    document.body.appendChild(overlay);
    document.getElementById('clubef-review-close').addEventListener('click', () => overlay.remove());
    overlay.addEventListener('click', (event) => { if (event.target === overlay) overlay.remove(); });
  }

  function showDetails() {
    const record = activeKind ? reviews.get(activeKind) : null;
    if (record) openJsonDialog(`Divergências — ${kindLabel(activeKind)}`, record);
  }

  function downloadActive() {
    const record = activeKind ? reviews.get(activeKind) : null;
    if (!record) return;
    const url = URL.createObjectURL(new Blob([`${JSON.stringify(record, null, 2)}\n`], { type: 'application/json' }));
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `REVISAO-${activeKind}-${record.execution_id || record.review_id}.json`;
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  }

  async function currentSeal() {
    const response = await fetch('/api/reading-contract/current', { cache: 'no-store' });
    const payload = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    const keys = ['contrato_id', 'versao_jogo', 'versao_contrato', 'fingerprint_contrato_sha256', 'fingerprint_fontes_sha256', 'fingerprint_catalogos_sha256'];
    return Object.fromEntries(keys.map((key) => [key, payload[key]]));
  }

  async function post(url, body) {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ ...body, leitura_contrato: await currentSeal() })
    });
    const payload = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    return payload;
  }

  async function stage(payload) {
    ensurePanel();
    const record = await post('/api/review/stage', { ...payload, database_write: false });
    const previous = reviews.get(record.kind);
    reviews.set(record.kind, {
      ...record,
      review_token: previous && previous.review_id === record.review_id ? previous.review_token : null
    });
    activeKind = record.kind;
    render();
    return record;
  }

  async function acknowledgeActive() {
    const record = activeKind ? reviews.get(activeKind) : null;
    if (!record) return;
    const button = document.getElementById('clubef-review-ack');
    button.disabled = true;
    button.textContent = 'Confirmando…';
    try {
      const acknowledged = await post('/api/review/acknowledge', {
        review_id: record.review_id,
        phrase: document.getElementById('clubef-review-phrase').value.trim()
      });
      reviews.set(activeKind, acknowledged);
      render();
    } catch (error) {
      button.disabled = false;
      button.textContent = 'Confirmar que revisei';
      global.alert(`Não foi possível confirmar a revisão: ${error.message}`);
    }
  }

  function credentials(kind) {
    const record = reviews.get(kind);
    if (!record || record.status !== 'reviewed' || !record.review_token) return null;
    return { review_id: record.review_id, review_token: record.review_token };
  }

  function requireCredentials(kind) {
    const value = credentials(kind);
    if (!value) {
      activeKind = kind;
      render();
      throw new Error(`Antes de enviar ${kindLabel(kind)}, abra “Revisão antes do banco”, confira as divergências e confirme a leitura.`);
    }
    return value;
  }

  async function restoreLatest(kind) {
    try {
      const response = await fetch(`/api/review/latest?kind=${encodeURIComponent(kind)}`, { cache: 'no-store' });
      if (response.status === 404) return;
      const payload = await response.json();
      if (!response.ok) return;
      reviews.set(kind, payload);
      if (!activeKind) activeKind = kind;
      render();
    } catch (_) {
      // A restauração é conveniência; nunca interfere na extração.
    }
  }

  ensurePanel();
  ['metadata', 'cards', 'full'].forEach(restoreLatest);
  global.CLUBEF_REVIEW = Object.freeze({
    version: VERSION,
    phrase: PHRASE,
    stage,
    credentials,
    requireCredentials,
    show: (kind) => { activeKind = kind; render(); }
  });
})(globalThis);
