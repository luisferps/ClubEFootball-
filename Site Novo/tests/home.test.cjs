const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'home.js'), 'utf8');

const foto = id => `https://res.cloudinary.com/demsusjwf/image/upload/${id}.png`;
const RANK = {
  total: 3668,
  itens: [
    { nome: 'Lionel Messi', funcao: 'Atacante criador', posicao: 'PTD / PTE', card_id: '89136409091415', linha_id: '30014', foto_url: foto('89136409091415'), nota_final: 113.7715519353258207, classificacao: 1 },
    { nome: '<script>x</script>', funcao: 'Meia armador', posicao: 'MLG', card_id: '17592723049952', linha_id: '32731', foto_url: 'http://inseguro/foto.png', nota_final: 113.7481920199501247, classificacao: 2 },
  ],
};
const BOXES = {
  itens: [
    { box: 'Catenaccio', total_cards: 11, data_rotulo: '24/08/2026', data_oferta: '2026-08-24' },
    { box: 'Box de um card só', total_cards: 1, data_rotulo: 'Sem data', data_oferta: null },
  ],
};

function makeWindow(rankResult, boxResult) {
  const calls = { rank: null, box: null };
  return {
    calls,
    window: {
      SiteNovoDegrau: { get: () => 2, subscribe: () => () => {} },
      SiteNovoRankingAPI: { read: req => { calls.rank = req; return rankResult(); } },
      SiteNovoBoxesAPI: { read: (req, signal, active) => { calls.box = { req, active }; return boxResult(); } },
    },
  };
}

function run(rankResult, boxResult) {
  const node = { innerHTML: '' };
  const made = makeWindow(rankResult, boxResult);
  vm.runInNewContext(source, { window: made.window, AbortController, URL, Promise, Number, String, encodeURIComponent });
  const promise = made.window.SiteNovoHome.mount(node);
  return { node, promise, calls: made.calls, api: made.window.SiteNovoHome };
}

(async () => {
  // 1) Estado de carregamento nao inventa numero.
  let hold;
  const pending = run(() => new Promise(r => { hold = r; }), () => new Promise(() => {}));
  assert.match(pending.node.innerHTML, /Carregando o ranking…/, 'mostra carregamento do ranking');
  assert.match(pending.node.innerHTML, /Carregando as boxes…/, 'mostra carregamento das boxes');
  assert.doesNotMatch(pending.node.innerHTML, /3\.668/, 'nao mostra total antes da resposta');
  pending.api.unmount();

  // 2) Estado pronto usa exatamente o que a porta publica entregou.
  const ready = run(() => Promise.resolve(RANK), () => Promise.resolve(BOXES));
  await ready.promise;
  const html = ready.node.innerHTML;

  assert.equal(ready.calls.rank.p_limite, 5, 'pede 5 do ranking');
  assert.equal(ready.calls.rank.p_modo, 'card');
  assert.equal(ready.calls.rank.p_degrau, 2, 'usa o degrau escolhido no site');
  assert.equal(ready.calls.box.req.p_limite, 5, 'pede 5 boxes');
  assert.equal(ready.calls.box.active, false, 'le o catalogo, nao as ofertas em andamento');

  assert.match(html, /3\.668/, 'mostra o total de cards publicados');
  assert.match(html, /113,77/, 'formata a nota com duas casas');
  assert.match(html, /113,75/, 'formata a segunda nota');
  assert.doesNotMatch(html, /113\.7715519353258207/, 'nao imprime a nota crua');
  assert.match(html, /ficha\.html\?card=89136409091415&amp;linha=30014/, 'link da ficha leva card e linha');
  assert.match(html, /Catenaccio/, 'lista a box');
  assert.match(html, /11 cards/, 'plural de cards');
  assert.match(html, /1 card</, 'singular de card');
  assert.match(html, /Oferta de 24\/08\/2026/, 'mostra a data da oferta');

  // 3) Nada de HTML injetado e nada de foto fora de https.
  assert.doesNotMatch(html, /<script>x<\/script>/, 'escapa o nome recebido');
  assert.match(html, /&lt;script&gt;/, 'nome escapado aparece como texto');
  assert.doesNotMatch(html, /http:\/\/inseguro/, 'descarta foto que nao e https');
  assert.match(html, /sn-home-nophoto/, 'usa o lugar da foto quando ela e recusada');

  // 4) Falha nao vira dado inventado.
  const broken = run(() => Promise.reject(new Error('500')), () => Promise.reject(new Error('500')));
  await broken.promise;
  assert.match(broken.node.innerHTML, /Ranking indisponível agora/, 'diz que o ranking falhou');
  assert.match(broken.node.innerHTML, /Catálogo indisponível agora/, 'diz que o catalogo falhou');
  assert.doesNotMatch(broken.node.innerHTML, /3\.668|113,77/, 'nao reaproveita numero de outra carga');

  // 5) Uma falha nao derruba a outra metade.
  const half = run(() => Promise.resolve(RANK), () => Promise.reject(new Error('500')));
  await half.promise;
  assert.match(half.node.innerHTML, /113,77/, 'ranking continua montado');
  assert.match(half.node.innerHTML, /Catálogo indisponível agora/, 'boxes falha sozinha');

  // 6) O Elenco continua declarado como nao conectado.
  assert.match(html, /Elenco e análises ainda não conectados/, 'nao promete elenco que nao existe');

  // 7) Uma chamada por porta publica, sem repeticao.
  let rankCount = 0, boxCount = 0;
  const counted = run(() => { rankCount++; return Promise.resolve(RANK); }, () => { boxCount++; return Promise.resolve(BOXES); });
  await counted.promise;
  assert.equal(rankCount, 1, 'uma leitura do ranking');
  assert.equal(boxCount, 1, 'uma leitura das boxes');
  counted.api.unmount();

  console.log('home.test.cjs: 7 blocos passaram');
})();
