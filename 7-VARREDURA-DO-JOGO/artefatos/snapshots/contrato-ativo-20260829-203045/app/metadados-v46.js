'use strict';

(function installMetadataReviewGate(global) {
  const PANEL_ID = 'clubef-metadata-v46-panel';
  const CONFIRMATION = 'APLICAR METADADOS PRIMEIRO';
  const state = {
    status: null,
    metadataScan: global.CLUBEF_LAST_METADATA_SCAN || null,
    cardScan: global.CLUBEF_LAST_CARD_SCAN || null,
    prepared: null,
    busy: false,
    expanded: false,
    applied: false
  };

  const escapeHtml = (value) => String(value == null ? '' : value).replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[character]));
  const fmt = (value) => Number(value || 0).toLocaleString('pt-BR');
  const $ = (id) => document.getElementById(id);

  function installStyles() {
    if ($('clubef-metadata-v46-style')) return;
    const style = document.createElement('style');
    style.id = 'clubef-metadata-v46-style';
    style.textContent = `
      #${PANEL_ID}{position:fixed;right:18px;bottom:18px;z-index:9999;width:min(500px,calc(100vw - 36px));max-height:calc(100vh - 36px);overflow:auto;padding:14px;border:1px solid rgba(127,127,127,.35);border-radius:14px;background:rgba(18,22,28,.97);color:#fff;box-shadow:0 12px 36px rgba(0,0,0,.35);font:14px/1.45 system-ui,sans-serif}
      #${PANEL_ID} button{font:inherit}
      #${PANEL_ID} .review-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
      #${PANEL_ID} .review-title{font-weight:850;font-size:15px}
      #${PANEL_ID} .review-subtitle{opacity:.76;font-size:12px;margin-top:2px}
      #${PANEL_ID} .review-collapse{border:1px solid rgba(255,255,255,.2);background:transparent;color:#fff;border-radius:8px;padding:4px 8px;cursor:pointer}
      #${PANEL_ID} .review-status{margin:10px 0;padding:9px 10px;border-radius:10px;background:rgba(255,255,255,.055);font-size:13px}
      #${PANEL_ID} .review-primary{width:100%;padding:10px 12px;border:0;border-radius:10px;font-weight:800;cursor:pointer;background:#53d9aa;color:#071510}
      #${PANEL_ID} .review-primary:disabled{opacity:.42;cursor:not-allowed}
      #${PANEL_ID} .review-details{margin-top:12px;border-top:1px solid rgba(255,255,255,.12);padding-top:12px}
      #${PANEL_ID} .review-note{padding:9px 10px;border-radius:10px;background:rgba(73,186,255,.11);border:1px solid rgba(73,186,255,.25);font-size:12px}
      #${PANEL_ID} .review-section{margin-top:12px}
      #${PANEL_ID} .review-section>h4{margin:0 0 7px;font-size:13px}
      #${PANEL_ID} .review-family{margin:6px 0;border:1px solid rgba(255,255,255,.12);border-radius:10px;padding:8px 9px;background:rgba(255,255,255,.035)}
      #${PANEL_ID} .review-family.ok{border-color:rgba(62,211,155,.28)}
      #${PANEL_ID} .review-family.warn{border-color:rgba(255,177,66,.38)}
      #${PANEL_ID} .review-family.error{border-color:rgba(255,95,95,.45)}
      #${PANEL_ID} .review-family summary{cursor:pointer}
      #${PANEL_ID} .review-meta{opacity:.78;font-size:12px;margin-top:4px}
      #${PANEL_ID} .review-ids{margin-top:6px;font-size:11px;word-break:break-word;opacity:.88}
      #${PANEL_ID} .review-confirm{margin-top:12px;padding:10px;border:1px solid rgba(255,190,70,.45);border-radius:10px;background:rgba(255,190,70,.07)}
      #${PANEL_ID} .review-confirm label{display:block;margin-top:8px;font-size:12px}
      #${PANEL_ID} .review-confirm input[type=text]{width:100%;box-sizing:border-box;margin-top:4px;padding:9px;border-radius:8px;border:1px solid rgba(255,255,255,.25);background:#0d141d;color:#fff}
      #${PANEL_ID} .review-apply{width:100%;margin-top:10px;padding:10px;border:0;border-radius:10px;font-weight:850;background:#f2b84b;color:#1b1303;cursor:pointer}
      #${PANEL_ID} .review-apply:disabled{opacity:.4;cursor:not-allowed}
      #${PANEL_ID} .review-result{margin-top:9px;font-size:12px;white-space:pre-wrap}
      @media(max-width:700px){#${PANEL_ID}{right:10px;bottom:10px;width:calc(100vw - 20px);max-height:72vh}}
    `;
    document.head.appendChild(style);
  }

  function createPanel() {
    installStyles();
    if ($(PANEL_ID)) return $(PANEL_ID);
    const panel = document.createElement('section');
    panel.id = PANEL_ID;
    panel.innerHTML = `
      <div class="review-head">
        <div>
          <div class="review-title">Conferência antes do banco</div>
          <div class="review-subtitle">Leitura → divergências → aprovação → aplicação</div>
        </div>
        <button id="clubef-review-collapse" class="review-collapse" type="button">abrir</button>
      </div>
      <div id="clubef-metadata-v46-status" class="review-status">Aguardando a leitura terminar. Nenhum dado será enviado automaticamente.</div>
      <button id="clubef-metadata-v46-review" class="review-primary" type="button" disabled>Abrir conferência</button>
      <div id="clubef-review-details" class="review-details" hidden>
        <div class="review-note"><b>Área intermediária.</b> Os dados ficam carregados apenas para conferência. Abrir esta área não grava nada no banco.</div>
        <div class="review-section"><h4>Metadados e catálogos</h4><div id="clubef-review-metadata">Aguardando o relatório de metadados…</div></div>
        <div class="review-section"><h4>Cartas e relações</h4><div id="clubef-review-cards">Aguardando o relatório de cartas…</div></div>
        <div class="review-section"><h4>Pacote que pode ser aplicado por este botão</h4><div id="clubef-review-dimensions">Abra a conferência para preparar o pacote.</div></div>
        <div id="clubef-review-confirm" class="review-confirm" hidden>
          <div id="clubef-review-scope"></div>
          <label><input id="clubef-review-ack" type="checkbox"> Conferi as divergências e entendi quais famílias ficarão fora desta aplicação.</label>
          <label>Digite <code id="clubef-review-phrase"></code><input id="clubef-review-input" type="text" autocomplete="off"></label>
          <button id="clubef-metadata-v46-apply" class="review-apply" type="button" disabled>Aplicar somente o pacote aprovado</button>
        </div>
        <div id="clubef-metadata-v46-result" class="review-result"></div>
      </div>`;
    document.body.appendChild(panel);

    $('clubef-review-collapse').addEventListener('click', toggleExpanded);
    $('clubef-metadata-v46-review').addEventListener('click', prepareReview);
    $('clubef-metadata-v46-apply').addEventListener('click', applyPrepared);
    $('clubef-review-ack').addEventListener('change', updateApplyAvailability);
    $('clubef-review-input').addEventListener('input', updateApplyAvailability);
    return panel;
  }

  function toggleExpanded() {
    state.expanded = !state.expanded;
    $('clubef-review-details').hidden = !state.expanded;
    $('clubef-review-collapse').textContent = state.expanded ? 'recolher' : 'abrir';
    if (state.expanded) renderAll();
  }

  function idsFrom(entries) {
    return (entries || []).map((entry) => String(entry && entry.id != null ? entry.id : entry)).filter(Boolean);
  }

  function idLine(label, entries, limit = 80) {
    const ids = idsFrom(entries);
    if (!ids.length) return '';
    const shown = ids.slice(0, limit);
    const remainder = ids.length - shown.length;
    return `<div class="review-ids"><b>${escapeHtml(label)}:</b> ${escapeHtml(shown.join(', '))}${remainder > 0 ? ` … +${fmt(remainder)}` : ''}</div>`;
  }

  function familyTone(status) {
    if (['validado_banco', 'comparado', 'aprovado'].includes(status)) return 'ok';
    if (['divergente', 'bloqueado_fonte_alterada'].includes(status)) return 'warn';
    if (['erro_leitura', 'bloqueado'].includes(status)) return 'error';
    return 'warn';
  }

  function renderMetadataScan() {
    const target = $('clubef-review-metadata');
    const scan = state.metadataScan;
    if (!scan || !scan.summary) {
      target.innerHTML = '<div class="review-meta">A leitura de metadados ainda não terminou.</div>';
      return;
    }
    const items = Object.entries(scan.summary).sort((a, b) => {
      const aw = familyTone(a[1].status) === 'ok' ? 1 : 0;
      const bw = familyTone(b[1].status) === 'ok' ? 1 : 0;
      return aw - bw || a[0].localeCompare(b[0]);
    });
    target.innerHTML = items.map(([name, item]) => {
      const diff = (scan.diff || {})[name] || {};
      const counts = `fonte ${fmt(item.current)} · banco ${fmt(item.baseline_active)} · novas ${fmt(item.new)} · alteradas ${fmt(item.changed)} · ausentes ${fmt(item.absent)}`;
      const details = [
        idLine('novas', diff.new_entries),
        idLine('alteradas', diff.changed_entries),
        idLine('ausentes', diff.absent_entries),
        idLine('duplicadas', diff.duplicate_ids)
      ].join('');
      return `<details class="review-family ${familyTone(item.status)}" ${familyTone(item.status) !== 'ok' ? 'open' : ''}><summary><b>${escapeHtml(name)}</b> · ${escapeHtml(item.status || 'sem estado')}</summary><div class="review-meta">${escapeHtml(counts)}${item.reason ? `<br>${escapeHtml(item.reason)}` : ''}</div>${details}</details>`;
    }).join('');
  }

  function renderCardScan() {
    const target = $('clubef-review-cards');
    const scan = state.cardScan;
    if (!scan) {
      target.innerHTML = '<div class="review-meta">A leitura de cartas ainda não terminou.</div>';
      return;
    }
    const counts = scan.counts || {};
    const intro = `<div class="review-family ${scan.relations_exact ? 'ok' : 'warn'}"><b>${scan.relations_exact ? 'Relações exatas' : 'Relações divergentes'}</b><div class="review-meta">${fmt(counts.current)} cartas · ${fmt(counts.new)} novas · ${fmt(counts.changed)} alteradas · ${fmt(counts.possibly_inactive)} possíveis inativas · ${fmt(counts.relation_mismatches)} divergências de relação.</div></div>`;
    const relations = (scan.relation_divergences || []).map((item) => {
      const samples = (item.samples || []).slice(0, 8).map((sample) => {
        const key = (sample.expected || sample.database || [])[0] || 'sem card';
        return `${key}: esperado ${JSON.stringify(sample.expected)} | banco ${JSON.stringify(sample.database)}`;
      });
      return `<details class="review-family warn"><summary><b>${escapeHtml(item.name)}</b> · ${fmt(item.mismatch_count)}</summary><div class="review-meta">fonte ${fmt(item.expected_rows)} · banco ${fmt(item.database_rows)}</div>${samples.length ? `<div class="review-ids">${escapeHtml(samples.join('\n')).replace(/\n/g, '<br>')}</div>` : ''}</details>`;
    }).join('');
    target.innerHTML = intro + relations;
  }

  function renderDimensionReview() {
    const target = $('clubef-review-dimensions');
    const prepared = state.prepared;
    if (!prepared || !prepared.review) {
      const validation = state.status && state.status.validation;
      if (validation) {
        target.innerHTML = `<div class="review-family ${validation.passed ? 'ok' : 'warn'}"><b>Fotografia disponível</b><div class="review-meta">${validation.passed ? 'Dimensões conferidas. Clique em “Abrir conferência” para gerar a etapa intermediária obrigatória.' : 'Dimensões possuem divergências. A conferência pode ser aberta, mas a aplicação ficará bloqueada.'}</div></div>`;
      } else {
        target.innerHTML = '<div class="review-meta">Aguardando a fotografia de Dimensões.</div>';
      }
      return;
    }
    const review = prepared.review;
    const families = Object.entries(review.families || {}).map(([name, item]) => {
      const samples = item.difference_samples || {};
      return `<details class="review-family ${item.passed ? 'ok' : 'warn'}" ${item.passed ? '' : 'open'}><summary><b>${escapeHtml(name)}</b> · ${item.passed ? 'igual' : 'divergente'}</summary><div class="review-meta">fonte ${fmt(item.source)} · banco ${fmt(item.database)} · faltando no banco ${fmt(item.missing_in_database)} · faltando na fonte ${fmt(item.missing_in_source)} · alterados ${fmt(item.changed)}</div>${idLine('faltando no banco', samples.missing_in_database)}${idLine('faltando na fonte', samples.missing_in_source)}${idLine('alterados', (samples.changed || []).map((entry) => entry.id))}</details>`;
    }).join('');
    const included = (review.included_tables || []).map((item) => `<li>${escapeHtml(item)}</li>`).join('');
    const excluded = (review.excluded_families || []).map((item) => `<li>${escapeHtml(item)}</li>`).join('');
    target.innerHTML = `<div class="review-family ${review.validation_passed ? 'ok' : 'warn'}"><b>${escapeHtml(review.title)}</b><div class="review-meta">Esta conferência não grava nada. Exclusões: nenhuma.</div></div>${families}<details class="review-family"><summary><b>Escopo exato do eventual envio</b></summary><div class="review-meta"><b>Inclui:</b><ul>${included}</ul><b>Não inclui:</b><ul>${excluded}</ul></div></details>`;
  }

  function renderAll() {
    if (!$(PANEL_ID)) return;
    renderMetadataScan();
    renderCardScan();
    renderDimensionReview();
    updateApplyAvailability();
  }

  function updateApplyAvailability() {
    const confirmBox = $('clubef-review-confirm');
    const applyButton = $('clubef-metadata-v46-apply');
    if (!confirmBox || !applyButton) return;
    const prepared = state.prepared;
    const allowed = Boolean(prepared && prepared.application_allowed && !state.applied);
    confirmBox.hidden = !prepared;
    $('clubef-review-phrase').textContent = prepared ? prepared.required_confirmation : CONFIRMATION;
    $('clubef-review-scope').innerHTML = prepared
      ? (allowed
        ? '<b>Etapa final:</b> somente o pacote de Dimensões aprovado acima poderá ser aplicado. Famílias divergentes continuam fora.'
        : '<b>Aplicação bloqueada:</b> a conferência está disponível, mas este pacote não foi aprovado ou a escrita local não está habilitada.')
      : '';
    const acknowledged = $('clubef-review-ack').checked;
    const phrase = $('clubef-review-input').value.trim();
    applyButton.disabled = !(allowed && acknowledged && phrase === prepared.required_confirmation && !state.busy);
  }

  async function currentSeal() {
    const response = await fetch('/api/reading-contract/current', { cache: 'no-store' });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    const keys = ['contrato_id', 'versao_jogo', 'versao_contrato', 'fingerprint_contrato_sha256', 'fingerprint_fontes_sha256', 'fingerprint_catalogos_sha256'];
    return Object.fromEntries(keys.map((key) => [key, payload[key]]));
  }

  async function refreshStatus() {
    createPanel();
    const statusBox = $('clubef-metadata-v46-status');
    const reviewButton = $('clubef-metadata-v46-review');
    try {
      const response = await fetch('/api/card-dimensions/cached-status', { cache: 'no-store' });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
      state.status = payload;
      if (!payload.ready) {
        statusBox.textContent = 'Aguardando a leitura terminar. Nenhum dado será enviado automaticamente.';
        reviewButton.disabled = true;
        renderAll();
        return;
      }
      const counts = payload.source_counts || {};
      statusBox.textContent = `Leitura pronta na área intermediária: ${fmt(counts.cards)} cartas · ${fmt(counts.clubs)} clubes · ${fmt(counts.leagues)} ligas. Banco ainda não alterado.`;
      reviewButton.disabled = state.busy;
      reviewButton.textContent = state.prepared ? 'Atualizar conferência' : 'Abrir conferência';
      if (state.prepared && payload.review_prepared === false) {
        state.prepared = null;
        state.applied = false;
        $('clubef-review-ack').checked = false;
        $('clubef-review-input').value = '';
      }
      renderAll();
    } catch (error) {
      statusBox.textContent = `Conferência ainda não disponível: ${error.message}`;
      reviewButton.disabled = true;
    }
  }

  async function prepareReview() {
    if (state.busy) return;
    state.busy = true;
    state.expanded = true;
    $('clubef-review-details').hidden = false;
    $('clubef-review-collapse').textContent = 'recolher';
    const button = $('clubef-metadata-v46-review');
    const resultBox = $('clubef-metadata-v46-result');
    button.disabled = true;
    button.textContent = 'Preparando conferência…';
    resultBox.textContent = 'Carregando a fotografia e o readback em modo somente leitura. Nenhuma escrita será feita.';
    try {
      const seal = await currentSeal();
      const response = await fetch('/api/card-dimensions/prepare-cached', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ leitura_contrato: seal })
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
      state.prepared = payload;
      state.applied = false;
      $('clubef-review-ack').checked = false;
      $('clubef-review-input').value = '';
      resultBox.textContent = payload.application_allowed
        ? 'Conferência pronta. Revise os itens acima; só depois a confirmação final será liberada.'
        : 'Conferência pronta, mas a aplicação deste pacote está bloqueada. As divergências continuam visíveis para análise.';
      renderAll();
    } catch (error) {
      state.prepared = null;
      resultBox.textContent = `CONFERÊNCIA BLOQUEADA: ${error.message}`;
    } finally {
      state.busy = false;
      button.disabled = !(state.status && state.status.ready);
      button.textContent = state.prepared ? 'Atualizar conferência' : 'Abrir conferência';
      updateApplyAvailability();
    }
  }

  async function applyPrepared() {
    if (state.busy || !state.prepared) return;
    state.busy = true;
    const button = $('clubef-metadata-v46-apply');
    const resultBox = $('clubef-metadata-v46-result');
    button.disabled = true;
    button.textContent = 'Aplicando pacote aprovado…';
    resultBox.textContent = 'Transação em andamento. Somente o escopo mostrado na conferência será enviado.';
    try {
      const seal = await currentSeal();
      const response = await fetch('/api/card-dimensions/apply-cached', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          review_id: state.prepared.review_id,
          acknowledged: true,
          confirmation: $('clubef-review-input').value.trim(),
          leitura_contrato: seal
        })
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
      const catalogs = payload.result && payload.result.catalogs ? payload.result.catalogs : {};
      const cards = payload.result && payload.result.cards ? payload.result.cards : {};
      state.applied = true;
      resultBox.textContent = `APLICAÇÃO CONCLUÍDA após conferência: ${fmt(catalogs.clubs)} clubes · ${fmt(catalogs.leagues)} ligas · ${fmt(cards.updated)} cartas vinculadas. Ímpetos, técnicos, textos e famílias divergentes não foram incluídos.`;
      button.textContent = 'Pacote conferido e aplicado';
      await refreshStatus();
    } catch (error) {
      resultBox.textContent = `APLICAÇÃO BLOQUEADA: ${error.message}`;
      button.textContent = 'Tentar aplicar o pacote aprovado';
    } finally {
      state.busy = false;
      updateApplyAvailability();
    }
  }

  global.addEventListener('clubef:metadata-scan-ready', (event) => {
    state.metadataScan = event.detail || null;
    renderAll();
  });
  global.addEventListener('clubef:card-scan-ready', (event) => {
    state.cardScan = event.detail || null;
    renderAll();
  });

  createPanel();
  renderAll();
  refreshStatus();
  global.setInterval(refreshStatus, 5000);
})(globalThis);
