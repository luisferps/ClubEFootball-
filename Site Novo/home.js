/* Inicio conectada: le as mesmas portas publicas do Ranking e das Boxes. Nao calcula nota. */
(() => {
  'use strict';
  let root = null, seq = 0, rankController = null, boxController = null;

  const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
  const photo = value => { try { const url = new URL(value); return url.protocol === 'https:' ? url.href : null; } catch { return null; } };
  const score = value => Number(value).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const count = value => Number(value).toLocaleString('pt-BR');
  const degrau = () => window.SiteNovoDegrau?.get() ?? 3;
  const fichaHref = item => 'ficha.html?card=' + encodeURIComponent(item.card_id) + '&amp;linha=' + encodeURIComponent(item.linha_id);

  function heroCard(item) {
    if (!item) return '<div class="sn-card-slot"><span>Card em destaque</span><small>Indisponível agora</small></div>';
    const image = photo(item.foto_url);
    return '<a class="sn-card-slot sn-card-slot-live" href="' + fichaHref(item) + '" target="_blank" rel="noopener">'
      + (image ? '<img src="' + esc(image) + '" alt="Card de ' + esc(item.nome) + '" loading="lazy" referrerpolicy="no-referrer">' : '<span class="sn-card-slot-nophoto">Sem imagem</span>')
      + '<strong>' + esc(item.nome) + '</strong><small>' + esc(item.funcao) + ' · ' + esc(item.posicao) + '</small></a>';
  }

  function heroBoard(state, total) {
    if (state !== 'pronto') return '<div class="sn-build-board"><small>PUBLICAÇÃO DAS BUILDS</small><p>—</p><span>' + (state === 'carregando' ? 'Carregando…' : 'Indisponível agora.') + '</span></div>';
    return '<div class="sn-build-board"><small>CARDS COM BUILD PUBLICADA</small><p>' + count(total) + '</p><span>Cada card com a especialidade em que rende mais e a nota final já publicada.</span></div>';
  }

  function topList(state, items) {
    if (state !== 'pronto') return '<div class="sn-home-empty"><p>' + (state === 'carregando' ? 'Carregando o ranking…' : 'Ranking indisponível agora.') + '</p><span>Abra o Ranking para consultar os cards e suas notas finais.</span></div>';
    if (!items.length) return '<div class="sn-home-empty"><p>Nenhuma build publicada ainda.</p></div>';
    return '<ol class="sn-home-list">' + items.map(item => {
      const image = photo(item.foto_url);
      return '<li><a href="' + fichaHref(item) + '" target="_blank" rel="noopener">'
        + '<span class="sn-home-place">' + esc(item.classificacao) + 'º</span>'
        + (image ? '<img src="' + esc(image) + '" alt="" loading="lazy" referrerpolicy="no-referrer">' : '<span class="sn-home-nophoto" aria-hidden="true">CF</span>')
        + '<span class="sn-home-name"><strong>' + esc(item.nome) + '</strong><small>' + esc(item.funcao) + ' · ' + esc(item.posicao) + '</small></span>'
        + '<b>' + esc(score(item.nota_final)) + '</b></a></li>';
    }).join('') + '</ol>';
  }

  function boxList(state, items) {
    if (state !== 'pronto') return '<div class="sn-home-empty"><p>' + (state === 'carregando' ? 'Carregando as boxes…' : 'Catálogo indisponível agora.') + '</p><span>Explore as coleções cadastradas e abra os cards na Ficha.</span></div>';
    if (!items.length) return '<div class="sn-home-empty"><p>Nenhuma box cadastrada.</p></div>';
    return '<ul class="sn-home-list sn-home-boxes">' + items.map(box =>
      '<li><a href="#boxes?box=' + encodeURIComponent(box.box) + '">'
      + '<span class="sn-home-name"><strong>' + esc(box.box) + '</strong><small>' + esc(box.data_oferta ? 'Oferta de ' + box.data_rotulo : box.data_rotulo) + '</small></span>'
      + '<b>' + esc(box.total_cards) + (Number(box.total_cards) === 1 ? ' card' : ' cards') + '</b></a></li>'
    ).join('') + '</ul>';
  }

  function markup(rank, boxes) {
    return '<div class="sn-home">'
      + '<article class="sn-hero"><div><p class="sn-eyebrow">BUILDS</p><h1>Descubra até onde seu card chega.</h1>'
      + '<p>Veja onde ele rende mais e o que vale ajustar.</p>'
      + '<a class="sn-button sn-gold-button" href="#ranking">Ver no ranking</a></div>'
      + '<div class="sn-build-preview">' + heroCard(rank.items[0]) + heroBoard(rank.state, rank.total) + '</div></article>'
      + '<article class="sn-roster-home"><div><p class="sn-eyebrow">ELENCO</p><h2>Seu elenco tá redondo?</h2>'
      + '<p>Veja o que está faltando, compare quem você já tem e encontre quem encaixa melhor no seu time.</p>'
      + '<p class="sn-inline-state">Elenco e análises ainda não conectados.</p>'
      + '<a class="sn-button" href="#elenco">Organizar elenco</a></div>'
      + '<div class="sn-pitches"><div class="sn-pitch"><span>ELENCO</span><small>Não conectado</small></div><div class="sn-pitch"><span>ENCAIXE</span><small>Não conectado</small></div></div></article>'
      + '<div class="sn-home-lower">'
      + '<section class="sn-home-panel"><div class="sn-panel-title"><h2>Quem tá no topo?</h2><a href="#ranking">Ver ranking →</a></div>' + topList(rank.state, rank.items) + '</section>'
      + '<section class="sn-home-panel"><div class="sn-panel-title"><h2>Boxes cadastradas</h2><a href="#boxes">Ver todas →</a></div>' + boxList(boxes.state, boxes.items) + '</section>'
      + '</div></div>';
  }

  function paint(rank, boxes) { if (root) root.innerHTML = markup(rank, boxes); }

  async function load() {
    const ticket = ++seq;
    rankController?.abort(); boxController?.abort();
    rankController = new AbortController(); boxController = new AbortController();
    const rank = { state: 'carregando', items: [], total: 0 };
    const boxes = { state: 'carregando', items: [] };
    paint(rank, boxes);

    const rankRequest = { p_modo: 'card', p_setor: 'geral', p_funcao_id: null, p_busca: '', p_posicao_nativa_id: null, p_estilo_id: null, p_offset: 0, p_limite: 5, p_degrau: degrau() };
    const boxRequest = { p_box: null, p_busca: '', p_limite: 5, p_offset: 0, p_ordem: 'recentes', p_degrau: degrau() };

    const [rankResult, boxResult] = await Promise.allSettled([
      window.SiteNovoRankingAPI.read(rankRequest, rankController.signal),
      window.SiteNovoBoxesAPI.read(boxRequest, boxController.signal, false)
    ]);
    if (ticket !== seq || !root) return;

    if (rankResult.status === 'fulfilled') { rank.state = 'pronto'; rank.items = rankResult.value.itens; rank.total = rankResult.value.total; }
    else rank.state = 'erro';
    if (boxResult.status === 'fulfilled') { boxes.state = 'pronto'; boxes.items = boxResult.value.itens; }
    else boxes.state = 'erro';
    paint(rank, boxes);
  }

  let unsubscribe = null;
  function unmount() {
    unsubscribe?.(); unsubscribe = null;
    ++seq; rankController?.abort(); boxController?.abort(); root = null;
  }

  window.SiteNovoHome = Object.freeze({
    mount(node) { unmount(); root = node; unsubscribe = window.SiteNovoDegrau?.subscribe(() => { if (root) load(); }); return load(); },
    unmount
  });
})();
