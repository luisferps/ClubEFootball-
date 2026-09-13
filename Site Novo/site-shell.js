/* Shell local independente. Não importa código, adaptadores ou motores da Ficha. */
(() => {
  'use strict';
  const pages = Object.freeze({
    elenco: { title: 'Elenco', group: 'Seu time', description: 'Organize seus jogadores e confira as possibilidades do elenco.', empty: 'Seu elenco ainda não está conectado.', detail: 'Esta área ainda não carrega nem salva jogadores. O campo e as análises serão conectados em uma próxima etapa.', regions: [['Jogadores do elenco', 'Área reservada para os cards do usuário.'], ['Formação e posições', 'Área reservada para a organização do time.'], ['Encaixe e análises', 'Função, formação, técnico e comparação aguardam módulos próprios.']] }
  });
  const main = document.getElementById('conteudo');
  const heading = (group, title, description) => `<header class="sn-heading"><p class="sn-eyebrow">${group}</p><h1>${title}</h1><p>${description}</p></header>`;
  const back = '<a class="sn-return" href="#inicio">← Voltar ao início</a>';
  function home() {
    return '<div class="sn-home"><article class="sn-hero"><div><p class="sn-eyebrow">BUILDS</p><h1>Descubra até onde seu card chega.</h1><p>Veja onde ele rende mais e o que vale ajustar.</p><p class="sn-inline-state">Ranking conectado às builds publicadas.</p><a class="sn-button sn-gold-button" href="#ranking">Ver no ranking</a><a class="sn-ficha-link" href="#ficha">Abrir Ficha pelo ID →</a></div><div class="sn-build-preview"><div class="sn-card-slot">Card em destaque<br><small>Aguardando conexão</small></div><div class="sn-build-board"><small>PUBLICAÇÃO DAS BUILDS</small><p>Não conectada</p><span>Notas e distribuição serão exibidas com os dados publicados.</span></div></div></article>' +
      '<article class="sn-roster-home"><div><p class="sn-eyebrow">ELENCO</p><h2>Seu elenco tá redondo?</h2><p>Veja o que está faltando, compare quem você já tem e encontre quem encaixa melhor no seu time.</p><p class="sn-inline-state">Elenco e análises ainda não conectados.</p><a class="sn-button" href="#elenco">Organizar elenco</a></div><div class="sn-pitches"><div class="sn-pitch"><span>ELENCO</span><small>Não conectado</small></div><div class="sn-pitch"><span>ENCAIXE</span><small>Não conectado</small></div></div></article>' +
      '<div class="sn-home-lower"><section class="sn-home-panel"><div class="sn-panel-title"><h2>Quem tá no topo?</h2><a href="#ranking">Ver ranking →</a></div><div class="sn-home-empty"><p>Ranking de builds publicadas.</p><span>Abra o Ranking para consultar os cards e suas notas finais.</span></div></section><section class="sn-home-panel"><div class="sn-panel-title"><h2>Boxes cadastradas</h2><a href="#boxes">Ver todas →</a></div><div class="sn-home-empty"><p>Catálogo de boxes conectado.</p><span>Explore as coleções cadastradas e abra os cards na Ficha.</span></div></section></div></div>';
  }
  function modulePage(page) {
    return heading(page.group, page.title, page.description) + `<section class="sn-empty"><span class="sn-status">Ainda não conectado</span><h2>${page.empty}</h2><p>${page.detail}</p></section><div class="sn-outline">${page.regions.map(([title, detail]) => `<section><h3>${title}</h3><p>${detail}</p></section>`).join('')}</div>` + back;
  }
  function ficha() {
    return heading('Ficha do jogador', 'Abra um card', 'A Ficha atual abre em outra aba, mantendo a navegação do site aqui.') +
      '<section class="sn-empty"><h2>Acesso por identificação do card</h2><p>Use a busca do cabeçalho para encontrar pelo nome. Se você já tem o ID, também pode abrir o card diretamente aqui.</p><form class="sn-form" action="ficha.html" method="get" target="_blank" rel="noopener"><div class="sn-fields"><label>ID do card<input name="card" inputmode="numeric" pattern="[0-9]*[1-9][0-9]*" required autocomplete="off" aria-describedby="sn-card-help"></label><label>ID da linha (opcional)<input name="linha" inputmode="numeric" pattern="[0-9]*[1-9][0-9]*" autocomplete="off" aria-describedby="sn-line-help"></label></div><p class="sn-help" id="sn-card-help">Use somente números, sem espaços.</p><p class="sn-help" id="sn-line-help">Sem linha, a Ficha solicita a build pública padrão do card. Com linha, abre exatamente a build indicada.</p><button class="sn-button" type="submit">Abrir Ficha em outra aba ↗</button></form></section>' + back;
  }
  function about() {
    return heading('Entenda o site', 'Como funciona', 'O que é a nota, o que é especialidade e o que muda quando você troca o degrau do ímpeto.') +
      '<div class="sn-outline">' +
      '<section><h2>Especialidade não é posição</h2><p>Posição é onde o card entra em campo: ponta, meia, zagueiro. Especialidade é o ofício que ele exerce ali — Atacante criador, Meia armador, Zagueiro de saída. São 19 especialidades, e o mesmo card rende diferente em cada uma. Por isso um card aparece no ranking várias vezes, uma por especialidade.</p></section>' +
      '<section><h2>De onde vem a nota</h2><p>O Otimizador escolhe a distribuição, o técnico, os ímpetos e as habilidades. Sua pontuação é convertida por uma curva fixa da especialidade: o molde vale 100 e o teto teórico vale 110. Depois são somados os bônus integrais de físico, pé ruim, estilos de jogo e IA. A nota é calculada e publicada pelo banco; o site só mostra o resultado. Ela não é o overall do jogo.</p></section>' +
      '<section><h2>O degrau do ímpeto</h2><p>Alguns ímpetos são condicionais e crescem em três degraus. O seletor 1 · 2 · 3 no topo escolhe em qual degrau o site inteiro calcula: no 1 tudo aparece com o ímpeto no primeiro nível, no 3 no máximo. Trocar o degrau muda as notas de todas as telas ao mesmo tempo.</p></section>' +
      '<section><h2>Ranking</h2><p>Todos os cards com build publicada, do maior para o menor. A exibição é uma de cada vez: por posição, por estilo de jogo ou por especialidade. Por card mostra cada carta; por jogador junta as cartas do mesmo atleta.</p></section>' +
      '<section><h2>Boxes</h2><p>Os cards recebem de zero a cinco estrelas de contratação. Cinco estrelas vazias significam não pagar; cinco preenchidas, pagar qualquer preço. A legenda mostra os seis níveis. Essas estrelas representam a indicação de contratação, e são diferentes das estrelas impressas na imagem da carta. As boxes em andamento ficam separadas das já encerradas.</p></section>' +
      '<section><h2>Ficha do card</h2><p>Abre pelo Ranking, pelas Boxes ou pela busca. Mostra a build escolhida pelo sistema: distribuição dos pontos, técnico, ímpetos, habilidades e os atributos finais. Clicar em outra build troca tudo, sem recarregar a página.</p></section>' +
      '<section><h2>Elenco</h2><p>Ainda não está pronto. Vai guardar os cards que você tem e montar o time a partir deles.</p></section>' +
      '</div>' + back;
  }

  function render(focus) {
    const [routeName,query=''] = location.hash.slice(1).split('?');
    const route = routeName || 'inicio';
    const params = new URLSearchParams(query);
    const box = params.get('box');
    const term = (params.get('termo') || '').trim();
    window.SiteNovoRanking?.unmount();
    window.SiteNovoBoxes?.unmount();
    window.SiteNovoSearch?.unmount();
    window.SiteNovoHome?.unmount();
    let title;
    if (route === 'inicio') {
      title = 'Início';
      if (window.SiteNovoHome) window.SiteNovoHome.mount(main);
      else main.innerHTML = home();
    }
    else if (['ranking','boxes','boxes-em-andamento'].includes(route)) {
      title = route==='ranking'?'Ranking':route==='boxes'?'Boxes cadastradas':'Boxes em andamento';
      const module = route==='ranking'?window.SiteNovoRanking:window.SiteNovoBoxes;
      if(module)module.mount(main,route==='boxes-em-andamento',box);
      else main.innerHTML=heading('Falha de carregamento',title,'Não foi possível carregar este módulo. Recarregue a página para tentar novamente.')+back;
    }
    else if (route === 'busca') {
      title = 'Buscar Cards';
      if (term.length >= 3 && term.length <= 120 && window.SiteNovoSearch) window.SiteNovoSearch.mount(main, term);
      else {
        window.SiteNovoSearch?.sync(term);
        main.innerHTML = heading('Catálogo', 'Buscar Cards', 'Digite pelo menos 3 letras na busca do cabeçalho.');
      }
    }
    else if (Object.hasOwn(pages, route)) { title = pages[route].title; main.innerHTML = modulePage(pages[route]); }
    else if (route === 'ficha') { title = 'Ficha'; main.innerHTML = ficha(); }
    else if (route === 'como-funciona') { title = 'Como funciona'; main.innerHTML = about(); }
    else { title = 'Página não encontrada'; main.innerHTML = heading('Navegação', title, 'Este endereço não faz parte do Site Novo.') + back; }
    document.title = `${title} — ClubEfootball`;
    document.querySelectorAll('[data-route]').forEach(link => {
      if (link.dataset.route === route) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
    document.querySelector('[data-sn-global-search]')?.classList.toggle('sn-search-current', route === 'busca');
    if (focus) main.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  }
  // Omite a linha vazia sem converter IDs em Number (IDs grandes preservados).
  main.addEventListener('submit', event => {
    const form = event.target;
    if (!form.matches('.sn-form')) return;
    const line = form.elements.namedItem('linha');
    line.disabled = line.value === '';
    setTimeout(() => { line.disabled = false; }, 0);
  });
  window.addEventListener('hashchange', () => {
    // O link de acessibilidade não é uma rota de página.
    if (location.hash === '#conteudo') { main.focus(); return; }
    render(true);
  });
  render(false);
})();



