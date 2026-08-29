'use strict';

/**
 * Camada visual de revisão entre a extração e qualquer preparação de envio.
 *
 * Esta camada não possui endpoint de escrita. Ela apenas captura o diff puro
 * produzido pelo núcleo, mantém a fotografia na memória desta execução e
 * mostra os valores atuais do banco e os valores extraídos do jogo.
 */
(function installIntermediateReview(global) {
  const originalCore = global.CLUBEF_CORE;
  if (!originalCore || typeof originalCore.compareCardRows !== 'function') return;

  const review = {
    generation: 0,
    generatedAt: null,
    cardDiff: null,
    currentById: new Map(),
    baselineById: new Map(),
    textDiff: null
  };

  const originalCompareCardRows = originalCore.compareCardRows.bind(originalCore);
  const originalCompareTextCatalog = typeof originalCore.compareTextCatalog === 'function'
    ? originalCore.compareTextCatalog.bind(originalCore)
    : null;

  function scheduleRender() {
    global.queueMicrotask(() => {
      enhanceCardReview();
      enhanceMetadataReview();
      refreshStaticLabels();
    });
  }

  function compareCardRowsWithReview(currentRows, baselineRows) {
    const diff = originalCompareCardRows(currentRows, baselineRows);
    review.generation += 1;
    review.generatedAt = new Date().toISOString();
    review.cardDiff = diff;
    review.currentById = new Map(currentRows.map((row) => [String(row.card_id), row]));
    review.baselineById = new Map(baselineRows.map((row) => [String(row.card_id), row]));
    global.CLUBEF_INTERMEDIATE_REVIEW = review;
    scheduleRender();
    return diff;
  }

  function compareTextCatalogWithReview(currentCatalog, baselineRows) {
    const diff = originalCompareTextCatalog(currentCatalog, baselineRows);
    review.textDiff = diff;
    global.CLUBEF_INTERMEDIATE_REVIEW = review;
    scheduleRender();
    return diff;
  }

  global.CLUBEF_CORE = Object.freeze({
    ...originalCore,
    compareCardRows: compareCardRowsWithReview,
    ...(originalCompareTextCatalog ? { compareTextCatalog: compareTextCatalogWithReview } : {})
  });
  global.CLUBEF_INTERMEDIATE_REVIEW = review;

  const escapeHtml = (value) => String(value == null ? '' : value).replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[character]));

  function printable(value) {
    if (value == null || value === '') return '—';
    if (typeof value === 'object') return JSON.stringify(value, null, 2);
    const text = String(value);
    const trimmed = text.trim();
    if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
      try { return JSON.stringify(JSON.parse(trimmed), null, 2); }
      catch (_) { return text; }
    }
    return text;
  }

  function valueHtml(value, tone = '') {
    const text = printable(value);
    const className = tone ? ` review-value ${tone}` : 'review-value';
    if (text.length <= 120 && !text.includes('\n')) return `<code class="${className.trim()}">${escapeHtml(text)}</code>`;
    const preview = text.replace(/\s+/g, ' ').slice(0, 110);
    return `<details class="review-value-details"><summary>${escapeHtml(preview)}${text.length > 110 ? '…' : ''}</summary><pre class="${className.trim()}">${escapeHtml(text)}</pre></details>`;
  }

  function cardItemForKey(key) {
    if (!review.cardDiff || !key) return null;
    const separator = key.indexOf(':');
    if (separator < 0) return null;
    const action = key.slice(0, separator);
    const id = key.slice(separator + 1);
    if (action === 'new') {
      const row = review.currentById.get(id);
      return row ? { action, id, row } : null;
    }
    if (action === 'change') {
      const entry = review.cardDiff.changed_cards.find((item) => String(item.card_id) === id);
      return entry ? { action, id, entry } : null;
    }
    if (action === 'inactive') {
      const entry = review.cardDiff.possibly_inactive.find((item) => String(item.card_id) === id);
      return entry ? { action, id, entry } : null;
    }
    return null;
  }

  function cardDetailHtml(key) {
    const item = cardItemForKey(key);
    if (!item) return '<div class="review-empty">Detalhes desta divergência não foram localizados na fotografia temporária.</div>';

    let title = '';
    let rows = [];
    if (item.action === 'change') {
      title = 'Campos divergentes: banco atual × extração do jogo';
      rows = item.entry.fields.map((field) => ({ field: field.field, before: field.before, after: field.after }));
    } else if (item.action === 'new') {
      title = 'Carta nova: ainda não existe em clube_novo';
      rows = originalCore.CARD_COLUMNS
        .filter((field) => field !== 'card_id')
        .map((field) => ({ field, before: '', after: item.row[field] }));
    } else {
      title = 'Possível inativa: existe no banco, mas não apareceu na fonte física atual';
      rows = originalCore.CARD_COLUMNS
        .filter((field) => field !== 'card_id')
        .map((field) => ({ field, before: item.entry.row[field], after: 'AUSENTE NA FONTE ATUAL' }));
    }

    return `<div class="review-detail-card"><div class="review-detail-title"><b>${escapeHtml(title)}</b><small>card_id ${escapeHtml(item.id)} · somente leitura</small></div><div class="review-detail-scroll"><table class="review-detail-table"><thead><tr><th>campo</th><th>no banco agora</th><th>extraído do jogo</th></tr></thead><tbody>${rows.map((row) => `<tr><td><code>${escapeHtml(row.field)}</code></td><td>${valueHtml(row.before, 'before')}</td><td>${valueHtml(row.after, 'after')}</td></tr>`).join('')}</tbody></table></div></div>`;
  }

  function detailedCardPayload() {
    const diff = review.cardDiff;
    return {
      contract: 'clubef-intermediate-review-v1',
      generated_at: review.generatedAt,
      database_write: false,
      persistence: 'memoria_temporaria_da_execucao',
      baseline: 'clube_novo.carta_jogo',
      counts: {
        new: diff.new_cards.length,
        changed: diff.changed_cards.length,
        possibly_inactive: diff.possibly_inactive.length,
        unchanged: diff.unchanged
      },
      new_cards: diff.new_cards,
      changed_cards: diff.changed_cards.map((entry) => ({
        card_id: entry.card_id,
        nome: entry.row && entry.row.nome,
        fields: entry.fields
      })),
      possibly_inactive: diff.possibly_inactive
    };
  }

  function downloadDetailedCardDiff() {
    if (!review.cardDiff) return;
    const content = `${JSON.stringify(detailedCardPayload(), null, 2)}\n`;
    const url = URL.createObjectURL(new Blob([content], { type: 'application/json;charset=utf-8' }));
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `DIVERGENCIAS-ANTES-DO-BANCO-${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
    anchor.click();
    global.setTimeout(() => URL.revokeObjectURL(url), 1500);
  }

  function ensureCardReviewChrome() {
    const result = document.getElementById('result-incremental');
    const tableWrap = document.getElementById('table-incremental');
    if (!result || !tableWrap) return;

    if (!document.getElementById('intermediate-review-banner')) {
      const banner = document.createElement('div');
      banner.id = 'intermediate-review-banner';
      banner.className = 'intermediate-review-banner';
      banner.innerHTML = '<span>ETAPA INTERMEDIÁRIA</span><div><b>Prévia carregada em memória — nenhuma escrita no banco</b><p>Veja cada divergência abaixo. O pacote só chega à preparação de envio depois desta revisão e ainda exige a confirmação final. Fechar o aplicativo descarta esta prévia temporária.</p></div>';
      const status = document.getElementById('incremental-result-status');
      if (status && status.parentNode) status.insertAdjacentElement('afterend', banner);
      else result.prepend(banner);
    }

    if (!document.getElementById('intermediate-review-controls')) {
      const controls = document.createElement('div');
      controls.id = 'intermediate-review-controls';
      controls.className = 'intermediate-review-controls';
      controls.innerHTML = '<label>Filtrar divergências<input id="intermediate-review-search" type="search" placeholder="card_id, nome ou campo"></label><label>Tipo<select id="intermediate-review-type"><option value="all">Todas</option><option value="new">Novas</option><option value="change">Alteradas</option><option value="inactive">Possíveis inativas</option></select></label><span id="intermediate-review-visible"></span>';
      tableWrap.insertAdjacentElement('beforebegin', controls);
      document.getElementById('intermediate-review-search').addEventListener('input', applyCardFilters);
      document.getElementById('intermediate-review-type').addEventListener('change', applyCardFilters);
    }

    const toolbar = result.querySelector('.toolbar');
    if (toolbar && !document.getElementById('download-detailed-card-diff')) {
      const button = document.createElement('button');
      button.id = 'download-detailed-card-diff';
      button.className = 'secondary';
      button.type = 'button';
      button.textContent = 'Baixar divergências detalhadas';
      button.addEventListener('click', downloadDetailedCardDiff);
      toolbar.appendChild(button);
    }
  }

  function applyCardFilters() {
    const search = (document.getElementById('intermediate-review-search')?.value || '').trim().toLowerCase();
    const type = document.getElementById('intermediate-review-type')?.value || 'all';
    const rows = [...document.querySelectorAll('#table-incremental tbody tr[data-review-key]')];
    let visible = 0;
    rows.forEach((row) => {
      const typeMatches = type === 'all' || row.dataset.reviewAction === type;
      const textMatches = !search || (row.dataset.reviewSearch || '').includes(search);
      const show = typeMatches && textMatches;
      row.hidden = !show;
      const details = row.nextElementSibling;
      if (details && details.classList.contains('intermediate-detail-row')) {
        if (!show) details.hidden = true;
        else if (details.dataset.open === 'true') details.hidden = false;
      }
      if (show) visible += 1;
    });
    const counter = document.getElementById('intermediate-review-visible');
    if (counter) counter.textContent = `${visible.toLocaleString('pt-BR')} divergência(s) visível(is)`;
  }

  function enhanceCardReview() {
    if (!review.cardDiff) return;
    ensureCardReviewChrome();
    const table = document.querySelector('#table-incremental table');
    if (!table || table.dataset.intermediateGeneration === String(review.generation)) return;
    table.dataset.intermediateGeneration = String(review.generation);

    const header = table.querySelector('thead tr');
    if (header) {
      const first = header.querySelector('th');
      if (first) first.textContent = 'pacote';
      const detailsHeader = document.createElement('th');
      detailsHeader.textContent = 'valores';
      header.appendChild(detailsHeader);
    }

    [...table.querySelectorAll('tbody > tr')].forEach((row) => {
      const checkbox = row.querySelector('.card-choice');
      const key = checkbox?.dataset.key;
      const item = cardItemForKey(key);
      if (!key || !item) return;
      checkbox.checked = true;
      checkbox.disabled = true;
      checkbox.title = 'O pacote incremental validado é integral. Use a revisão para decidir se continua ou interrompe o envio.';
      row.dataset.reviewKey = key;
      row.dataset.reviewAction = item.action;
      row.dataset.reviewSearch = row.textContent.toLowerCase();

      const cell = document.createElement('td');
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'review-detail-button';
      button.textContent = 'Ver antes/depois';
      button.setAttribute('aria-expanded', 'false');
      cell.appendChild(button);
      row.appendChild(cell);

      const detailRow = document.createElement('tr');
      detailRow.className = 'intermediate-detail-row';
      detailRow.hidden = true;
      detailRow.dataset.open = 'false';
      const detailCell = document.createElement('td');
      detailCell.colSpan = 6;
      detailCell.innerHTML = '<div class="review-detail-loading">Abra para carregar os valores desta divergência.</div>';
      detailRow.appendChild(detailCell);
      row.insertAdjacentElement('afterend', detailRow);

      button.addEventListener('click', () => {
        const open = detailRow.dataset.open !== 'true';
        if (open && detailCell.dataset.loaded !== 'true') {
          detailCell.innerHTML = cardDetailHtml(key);
          detailCell.dataset.loaded = 'true';
        }
        detailRow.dataset.open = String(open);
        detailRow.hidden = !open;
        button.textContent = open ? 'Ocultar valores' : 'Ver antes/depois';
        button.setAttribute('aria-expanded', String(open));
      });
    });

    applyCardFilters();
    refreshStaticLabels();
  }

  function metadataItemForKey(key) {
    if (!review.textDiff || !key || !key.startsWith('textos:')) return null;
    const parts = key.split(':');
    const action = parts[1];
    const id = parts.slice(2).join(':');
    if (action === 'new') {
      const record = review.textDiff.new_entries.find((item) => String(item.id) === id);
      return record ? { action, id, record } : null;
    }
    if (action === 'change') {
      const entry = review.textDiff.changed_entries.find((item) => String(item.id) === id);
      return entry ? { action, id, entry } : null;
    }
    if (action === 'absent') {
      const entry = review.textDiff.absent_entries.find((item) => String(item.id) === id);
      return entry ? { action, id, entry } : null;
    }
    return null;
  }

  function metadataDetailHtml(key) {
    const item = metadataItemForKey(key);
    if (!item) return '<div class="review-empty">Detalhe disponível apenas no manifesto integral desta família.</div>';
    const before = item.action === 'new' ? '' : (item.entry.before || item.entry.record || '');
    const after = item.action === 'absent' ? 'AUSENTE NA FONTE ATUAL' : (item.record || item.entry.after || item.entry.record || '');
    return `<div class="review-detail-card"><div class="review-detail-title"><b>Metadado: banco atual × fonte física</b><small>${escapeHtml(item.id)} · somente leitura</small></div><div class="metadata-before-after"><div><span>NO BANCO AGORA</span>${valueHtml(before, 'before')}</div><div><span>EXTRAÍDO DO JOGO</span>${valueHtml(after, 'after')}</div></div></div>`;
  }

  function enhanceMetadataReview() {
    if (!review.textDiff) return;
    const table = document.querySelector('#table-metadata table');
    if (!table || table.dataset.intermediateMetadata === 'true') return;
    table.dataset.intermediateMetadata = 'true';
    const header = table.querySelector('thead tr');
    if (header) {
      const detailsHeader = document.createElement('th');
      detailsHeader.textContent = 'valores';
      header.appendChild(detailsHeader);
    }
    [...table.querySelectorAll('tbody > tr')].forEach((row) => {
      const checkbox = row.querySelector('.metadata-choice');
      const key = checkbox?.dataset.key;
      if (!key) return;
      const cell = document.createElement('td');
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'review-detail-button';
      button.textContent = 'Ver antes/depois';
      cell.appendChild(button);
      row.appendChild(cell);
      const detailRow = document.createElement('tr');
      detailRow.className = 'intermediate-detail-row';
      detailRow.hidden = true;
      const detailCell = document.createElement('td');
      detailCell.colSpan = 6;
      detailRow.appendChild(detailCell);
      row.insertAdjacentElement('afterend', detailRow);
      button.addEventListener('click', () => {
        const open = detailRow.hidden;
        if (open && !detailCell.innerHTML) detailCell.innerHTML = metadataDetailHtml(key);
        detailRow.hidden = !open;
        button.textContent = open ? 'Ocultar valores' : 'Ver antes/depois';
      });
    });
  }

  function refreshStaticLabels() {
    const reviewHead = document.querySelector('#result-incremental .review-head');
    if (reviewHead) {
      const title = reviewHead.querySelector('h3');
      const paragraph = reviewHead.querySelector('p');
      if (title) title.textContent = 'Divergências antes do banco';
      if (paragraph) paragraph.textContent = 'A lista abaixo é uma prévia temporária. Abra cada item para comparar o valor atual do banco com o valor extraído do jogo.';
      const quickSelect = reviewHead.querySelector('.quick-select');
      if (quickSelect) quickSelect.hidden = true;
    }

    const applyTitleStep = document.querySelector('#apply-card-package .apply-title > span');
    const applyTitle = document.getElementById('apply-card-package-title');
    if (applyTitleStep && applyTitleStep.textContent !== 'ETAPA 3 · APÓS A REVISÃO') applyTitleStep.textContent = 'ETAPA 3 · APÓS A REVISÃO';
    if (applyTitle && applyTitle.textContent !== 'Preparar o pacote revisado para envio') applyTitle.textContent = 'Preparar o pacote revisado para envio';

    const prepareButton = document.getElementById('prepare-card-package');
    if (prepareButton && prepareButton.textContent === 'OK — preparar envio ao clube_novo') {
      prepareButton.textContent = 'Revisão concluída — preparar envio ao clube_novo';
    }

    const confirmationLabel = document.querySelector('#card-package-confirmation label.check');
    if (confirmationLabel && !confirmationLabel.dataset.intermediateLabel) {
      confirmationLabel.dataset.intermediateLabel = 'true';
      const input = confirmationLabel.querySelector('input');
      confirmationLabel.textContent = '';
      if (input) confirmationLabel.appendChild(input);
      confirmationLabel.append(' Conferi todas as divergências exibidas, inclusive possíveis inativas.');
    }

    const applyBox = document.getElementById('apply-card-package');
    if (applyBox && !document.getElementById('integral-package-note')) {
      const note = document.createElement('div');
      note.id = 'integral-package-note';
      note.className = 'integral-package-note';
      note.innerHTML = '<b>Pacote integral:</b> esta etapa é para revisar e decidir se continua. Se uma divergência estiver errada, não prepare o envio; corrija a extração e compare novamente.';
      const summary = document.getElementById('card-package-summary');
      if (summary) summary.insertAdjacentElement('afterend', note);
    }
  }

  function installStyles() {
    if (document.getElementById('intermediate-review-styles')) return;
    const style = document.createElement('style');
    style.id = 'intermediate-review-styles';
    style.textContent = `
      .intermediate-review-banner{display:flex;gap:14px;align-items:flex-start;margin:16px 0;padding:16px;border:1px solid rgba(82,222,174,.38);border-radius:14px;background:rgba(26,78,67,.20)}
      .intermediate-review-banner>span{flex:0 0 auto;padding:5px 8px;border-radius:999px;background:rgba(82,222,174,.14);color:#64e6ba;font-size:11px;font-weight:800;letter-spacing:.08em}
      .intermediate-review-banner b{display:block;margin-bottom:4px;color:#effbf7}.intermediate-review-banner p{margin:0;color:#9fb3c7;line-height:1.5}
      .intermediate-review-controls{display:flex;gap:12px;align-items:end;flex-wrap:wrap;margin:14px 0;padding:12px;border:1px solid #25394e;border-radius:12px;background:#0c1723}
      .intermediate-review-controls label{display:grid;gap:6px;color:#9fb3c7;font-size:12px}.intermediate-review-controls input,.intermediate-review-controls select{min-width:220px;padding:9px 10px;border:1px solid #31475d;border-radius:9px;background:#09131e;color:#eef6ff}
      .intermediate-review-controls span{margin-left:auto;padding:9px 0;color:#9fb3c7;font-size:12px}
      .review-detail-button{white-space:nowrap;padding:7px 9px;border:1px solid #35516a;border-radius:8px;background:#102235;color:#dcecff;cursor:pointer}.review-detail-button:hover{border-color:#55dcb0;color:#fff}
      .intermediate-detail-row>td{padding:0!important;border-top:0!important}.review-detail-card{margin:0 8px 12px;padding:14px;border:1px solid #2a4055;border-radius:12px;background:#09131e}
      .review-detail-title{display:flex;justify-content:space-between;gap:12px;align-items:center;margin-bottom:12px}.review-detail-title b{color:#f4f8fc}.review-detail-title small{color:#8298ad}
      .review-detail-scroll{overflow:auto;max-height:480px}.review-detail-table{width:100%;border-collapse:collapse}.review-detail-table th,.review-detail-table td{vertical-align:top;padding:9px;border-bottom:1px solid #1e3144;text-align:left}.review-detail-table th{position:sticky;top:0;background:#0c1a28;color:#9fb3c7;z-index:1}
      .review-value{display:inline-block;max-width:520px;white-space:pre-wrap;overflow-wrap:anywhere;color:#dce7f1}.review-value.before{color:#ffb6af}.review-value.after{color:#7ee6bd}.review-value-details summary{max-width:520px;cursor:pointer;color:#b9c9d8;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.review-value-details pre{margin:8px 0 0;padding:10px;border-radius:8px;background:#050c13;max-width:620px;max-height:300px;overflow:auto}
      .integral-package-note{margin:12px 0;padding:12px;border-left:3px solid #f3b54a;background:rgba(243,181,74,.08);color:#c9d5df;line-height:1.45}.integral-package-note b{color:#ffd27a}
      .metadata-before-after{display:grid;grid-template-columns:1fr 1fr;gap:12px}.metadata-before-after>div{min-width:0;padding:10px;border:1px solid #24394e;border-radius:10px}.metadata-before-after span{display:block;margin-bottom:8px;color:#8298ad;font-size:11px;font-weight:800;letter-spacing:.06em}
      @media (max-width:760px){.intermediate-review-banner{display:block}.intermediate-review-banner>span{display:inline-block;margin-bottom:10px}.intermediate-review-controls{display:grid}.intermediate-review-controls input,.intermediate-review-controls select{width:100%;min-width:0}.intermediate-review-controls span{margin-left:0}.review-detail-title{display:block}.review-detail-title small{display:block;margin-top:4px}.metadata-before-after{grid-template-columns:1fr}}
    `;
    document.head.appendChild(style);
  }

  function installObservers() {
    installStyles();
    const observer = new MutationObserver(() => scheduleRender());
    const incremental = document.getElementById('result-incremental');
    const metadata = document.getElementById('result-metadata');
    const applyBox = document.getElementById('apply-card-package');
    if (incremental) observer.observe(incremental, { childList: true, subtree: true });
    if (metadata) observer.observe(metadata, { childList: true, subtree: true });
    if (applyBox) observer.observe(applyBox, { childList: true, subtree: true, characterData: true });
    refreshStaticLabels();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', installObservers, { once: true });
  else installObservers();
})(globalThis);
