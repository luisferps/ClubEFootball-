/* Busca global compartilhada pelo cabeçalho e pela página de resultados. */
(() => {
  'use strict';
  const header = document.querySelector('[data-sn-global-search]');
  const input = header?.elements.busca;
  const popup = header?.querySelector('[data-sn-search-popup]');
  let timer = 0, request = 0, controller = null, resultsRoot = null, pageController = null, pageRequest = 0;
  const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
  const safePhoto = value => { try { const url = new URL(value); return url.protocol === 'https:' ? url.href : null; } catch { return null; } };
  const meta = item => [item.posicao, item.box].filter(Boolean).join(' · ');
  const degrau = () => window.SiteNovoDegrau?.get() ?? 3;
  const score = item => item.pontuacao_total === null ? 'Sem pontuação publicada' : `Pontuação total · ${item.pontuacao_total.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  function close() { if (!popup) return; popup.hidden = true; input?.setAttribute('aria-expanded', 'false'); }
  function show(html) { if (!popup) return; popup.innerHTML = html; popup.hidden = false; input?.setAttribute('aria-expanded', 'true'); }
  function resultLink(item, compact = false) {
    const photo = safePhoto(item.foto_url);
    const image = photo ? `<img src="${esc(photo)}" alt="" loading="lazy" referrerpolicy="no-referrer">` : '<span class="sn-search-no-photo" aria-hidden="true">CF</span>';
    return `<a class="${compact ? 'sn-search-suggestion' : 'sn-search-card'}" href="ficha.html?card=${encodeURIComponent(item.card_id)}" target="_blank" rel="noopener">${image}<span><strong>${esc(item.nome)}</strong><small>${esc(meta(item) || 'Dados cadastrais')}</small><em${item.pontuacao_total === null ? ' class="sn-no-score"' : ''}>${esc(score(item))}</em>${item.regua_vigente === false ? '<em class="sn-regua-antiga">Regua antiga</em>' : ''}</span></a>`;
  }
  async function suggestions() {
    const term = input.value.trim();
    clearTimeout(timer); controller?.abort();
    if (!term) { close(); return; }
    if (term.length < 3) { show('<p class="sn-search-message">Digite pelo menos 3 letras.</p>'); return; }
    const ticket = ++request;
    controller = new AbortController();
    show('<p class="sn-search-message">Buscando jogadores…</p>');
    try {
      const data = await window.SiteNovoSearchAPI.read({ p_busca: term, p_limite: 8, p_offset: 0, p_degrau: degrau() }, controller.signal);
      if (ticket !== request) return;
      show(data.itens.length ? data.itens.map(item => resultLink(item, true)).join('') + `<button type="button" class="sn-search-all" data-sn-search-all>Ver todos os ${data.total.toLocaleString('pt-BR')} resultados</button>` : '<p class="sn-search-message">Nenhum card encontrado.</p>');
    } catch (error) {
      if (error.name !== 'AbortError' && ticket === request) show(`<p class="sn-search-message">${esc(error.message)}</p>`);
    }
  }
  function schedule() { clearTimeout(timer); timer = setTimeout(suggestions, 220); }
  function go(term = input?.value.trim()) {
    if (!term || term.length < 3) { input?.focus(); suggestions(); return; }
    close();
    const hash = `busca?termo=${encodeURIComponent(term)}`;
    if (/index\.html$/i.test(location.pathname) || /\/$/.test(location.pathname)) location.hash = hash;
    else location.href = `index.html#${hash}`;
  }
  header?.addEventListener('submit', event => { event.preventDefault(); go(); });
  header?.addEventListener('input', schedule);
  header?.addEventListener('keydown', event => { if (event.key === 'Escape') { close(); input.blur(); } });
  header?.addEventListener('click', event => { if (event.target.closest('[data-sn-search-all]')) go(); });
  document.addEventListener('click', event => { if (header && !header.contains(event.target)) close(); });

  function pageMarkup(data, busy, error, term, offset) {
    const heading = `<header class="sn-heading"><p class="sn-eyebrow">CATÁLOGO</p><h1>Buscar Cards</h1><p>Resultados para “${esc(term)}”.</p></header>`;
    if (busy) return heading + '<div class="sn-search-page-message">Buscando em todos os cards…</div>';
    if (error) return heading + `<div class="sn-search-page-message" role="alert"><p>${esc(error)}</p><button class="sn-button" data-sn-search-retry>Tentar novamente</button></div>`;
    if (!data?.itens.length) return heading + '<div class="sn-search-page-message">Nenhum card encontrado.</div>';
    const start = offset + 1, end = offset + data.itens.length;
    return heading + `<p class="sn-search-summary">${start}–${end} de ${data.total.toLocaleString('pt-BR')} resultados</p><div class="sn-search-grid">${data.itens.map(item => resultLink(item)).join('')}</div><nav class="sn-search-pages" aria-label="Páginas da busca"><button type="button" data-sn-search-prev ${offset === 0 ? 'disabled' : ''}>← Anterior</button><button type="button" data-sn-search-next ${data.tem_mais ? '' : 'disabled'}>Próxima →</button></nav>`;
  }
  async function loadPage(term, offset = 0) {
    if (!resultsRoot) return;
    const ticket = ++pageRequest;
    pageController?.abort(); pageController = new AbortController();
    resultsRoot.innerHTML = pageMarkup(null, true, '', term, offset);
    try {
      const data = await window.SiteNovoSearchAPI.read({ p_busca: term, p_limite: 48, p_offset: offset, p_degrau: degrau() }, pageController.signal);
      if (ticket !== pageRequest || !resultsRoot) return;
      resultsRoot.dataset.term = term; resultsRoot.dataset.offset = String(offset); resultsRoot.innerHTML = pageMarkup(data, false, '', term, offset);
    } catch (error) {
      if (ticket !== pageRequest || !resultsRoot || error.name === 'AbortError') return;
      resultsRoot.dataset.term = term; resultsRoot.dataset.offset = String(offset); resultsRoot.innerHTML = pageMarkup(null, false, error.message, term, offset);
    }
  }
  function pageClick(event) {
    const button = event.target.closest('button'); if (!button || !resultsRoot?.contains(button)) return;
    const term = resultsRoot.dataset.term, offset = Number(resultsRoot.dataset.offset || 0);
    if (button.hasAttribute('data-sn-search-retry')) loadPage(term, offset);
    else if (button.hasAttribute('data-sn-search-prev')) loadPage(term, Math.max(0, offset - 48));
    else if (button.hasAttribute('data-sn-search-next')) loadPage(term, offset + 48);
  }
  function unmount() { ++pageRequest; pageController?.abort(); if (resultsRoot) resultsRoot.removeEventListener('click', pageClick); resultsRoot = null; }
  function sync(term = '') { if (input && document.activeElement !== input) input.value = term; }
  window.SiteNovoSearch = Object.freeze({
    mount(node, term) { unmount(); resultsRoot = node; resultsRoot.addEventListener('click', pageClick); sync(term); return loadPage(term, 0); },
    unmount,
    sync
  });
  window.SiteNovoDegrau?.subscribe(() => {
    if (input?.value.trim().length >= 3 && popup && !popup.hidden) suggestions();
    if (resultsRoot) loadPage(resultsRoot.dataset.term, Number(resultsRoot.dataset.offset || 0));
  });
})();
