/* =========================================================================
   MOTOR NO SERVIDOR — a tela para de fazer a conta e passa a perguntar.

   Ordem do Luis, 25/08:
     "A nota que sai lá, quando ele mexer no jogador dele, tem que ser
      exatamente a nota que o nosso motor daria."
     "Se o motor fica disponível na internet de um jeito que alguém possa
      copiar, a gente cria os próprios concorrentes."

   ESTE ARQUIVO ENTRA POR ÚLTIMO, depois de todos os outros. Ele não apaga
   nada: guarda a função antiga e põe a nova por cima. Para voltar atrás,
   basta tirar a linha do index.html.

   COMEÇA EM MODO CONFERÊNCIA (MODO='conferir'): a tela continua fazendo a
   conta dela e, em paralelo, pergunta ao servidor e ESCREVE NO CONSOLE quando
   os dois discordarem. Nada muda na tela. Só depois de a conferência dar
   zero divergência é que se vira a chave para 'servidor'.
   ========================================================================= */
(function () {
  'use strict';

  var URL_MOTOR = 'https://web-production-8c01c.up.railway.app';
  var MODO = 'conferir';          // 'conferir' | 'servidor' | 'desligado'

  window.MOTOR = window.MOTOR || {};
  window.MOTOR.url = URL_MOTOR;
  window.MOTOR.modo = MODO;
  window.MOTOR.divergencias = [];

  /* ---------------------------------------------------------------- estado
     O que a tela tem, traduzido para o que o servidor entende.
     ⚠️ A tela NÃO guarda tecnico_id nem id de ímpeto — guarda os boosts, o
     nome do técnico (de onde sai o multiplicador) e o NOME do ímpeto. */
  /* rotulo da funcao -> CODIGO. A tela guarda o rotulo (c.tipo); o servidor so
     entende codigo. Etiqueta muda, codigo nao — por isso o mapa mora aqui e a
     conversa com o servidor nunca depende do nome que aparece na tela. */
  var CODIGO = {
    'Centroavante fixo':'centroavante_fixo', 'Centroavante movel':'centroavante_movel',
    'Centroavante m\u00f3vel':'centroavante_movel', 'Falso nove':'falso_nove',
    'Goleiro defensivo':'goleiro_defensivo', 'Goleiro ofensivo':'goleiro_ofensivo',
    'Lateral defensivo':'lateral_defensivo', 'Lateral ofensivo':'lateral_ofensivo',
    'Meia ofensivo':'meia_ofensivo_armador', 'Atacante infiltrador':'segundo_atacante',
    'Meia armador':'meia_central_armador', 'Meia de arranque':'meia_central_de_chegada',
    'Ala finalizador':'meia_de_lado_por_dentro', 'Ala cruzador':'meia_de_lado_por_fora',
    'Atacante criador':'ponta_criadora', 'Atacante finalizador':'ponta_finalizadora',
    'Volante de constru\u00e7\u00e3o':'volante_de_construcao',
    'Volante de conten\u00e7\u00e3o':'volante_de_contencao',
    'Zagueiro de combate':'zagueiro_de_combate', 'Zagueiro de sa\u00edda':'zagueiro_de_saida'
  };

  function estadoDe(c, lvl) {
    if (!c) return null;
    /* c.id E o card_id: conferido no banco, 17.504 de 17.504 */
    var cid = c.id;
    var fcod = c.fcod || CODIGO[c.tipo];
    if (!cid || !fcod) return null;

    var boosts = [];
    try {
      var bs = (typeof tecAtual === 'function') ? tecAtual(c) : (c.TECB || []);
      (bs || []).forEach(function (k) {
        var i = (typeof TECIDX !== 'undefined') ? TECIDX[k] : undefined;
        if (i !== undefined) boosts.push(i);
      });
    } catch (e) {}

    var m = 1;
    try {
      var nome = (c._tecNome !== undefined ? c._tecNome : c.TEC);
      if (nome && typeof mDoNome === 'function') m = mDoNome(nome, 1);
      else if (nome && typeof TECM !== 'undefined' && TECM[nome]) m = TECM[nome][0];
    } catch (e) {}

    var impNome = null;
    try {
      var p = String(c.imp || '').split('o motor pos:');
      if (p.length > 1) impNome = p[1].split('·')[0].replace(' (cond.)', '').trim();
    } catch (e) {}

    var habs = [];
    try { habs = (c._habs !== undefined ? c._habs : (c.adds || [])) || []; } catch (e) {}

    var barras = {};
    try {
      var L = lvl || (typeof _lvlDe === 'function' ? _lvlDe(c) : {});
      Object.keys(L).forEach(function (b) { if (L[b]) barras[b] = L[b]; });
    } catch (e) {}

    var est = { card_id: String(cid), funcao: String(fcod), barras: barras,
                boosts_attr: boosts, multiplicador: m,
                habilidades_escolhidas: habs };
    if (impNome) est.impeto_nome = impNome;
    return est;
  }

  function pede(rota, corpo) {
    return fetch(URL_MOTOR + rota, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(corpo)
    }).then(function (r) { return r.json(); });
  }

  /* ------------------------------------------------------------- a nota */
  window.MOTOR.nota = function (c, lvl) {
    var est = estadoDe(c, lvl);
    if (!est) return Promise.resolve(null);
    return pede('/nota', est);
  };

  /* --------------------------------------------------------- o otimizador */
  window.MOTOR.otimizar = function (c) {
    var est = estadoDe(c, null);
    if (!est) return Promise.resolve(null);
    delete est.barras;
    return pede('/otimizar', est);
  };

  /* ------------------------------------------------- conferência silenciosa
     Toda vez que a tela grava uma build nova, pergunta ao servidor e compara.
     Não muda nada — só registra. É a prova de que dá para virar a chave. */
  function confere(c, lvl, notaLocal) {
    window.MOTOR.nota(c, lvl).then(function (r) {
      if (!r || !r.ok) return;
      var d = Math.abs((r.nota || 0) - (notaLocal || 0));
      if (d > 0.05) {
        var reg = { card: c.cid || c.id, funcao: c.fcod, local: notaLocal,
                    servidor: r.nota, diferenca: +d.toFixed(2) };
        window.MOTOR.divergencias.push(reg);
        console.warn('%cMOTOR ≠ TELA', 'color:#e0533d;font-weight:700', reg);
      } else {
        console.log('%cmotor = tela  ' + r.nota, 'color:#22c58b');
      }
    }).catch(function () { /* servidor fora: a conferência simplesmente não acontece */ });
  }

  /* ---------------------------------------------------------- os ganchos */
  var _gravaVelho = window._grava;
  if (typeof _gravaVelho === 'function') {
    window._grava = function (c, lvl) {
      var r = _gravaVelho.apply(this, arguments);
      if (MODO === 'conferir') { try { confere(c, lvl, c.b1); } catch (e) {} }
      return r;
    };
  }

  var _otimizarVelho = window.otimizarBarras;
  if (typeof _otimizarVelho === 'function') {
    window.otimizarBarras = function (key) {
      if (MODO !== 'servidor') return _otimizarVelho.apply(this, arguments);
      var c = (typeof _card === 'function') ? _card(key) : null;
      if (!c) return;
      if (typeof _marca === 'function') _marca(key);
      window.MOTOR.otimizar(c).then(function (r) {
        if (!r || !r.ok) {
          console.warn('o servidor não respondeu; nada foi mudado. ' + (r && r.erro || ''));
          return;
        }
        var lvl = {};
        (typeof MBK !== 'undefined' ? MBK : Object.keys(r.barras)).forEach(function (b) {
          lvl[b] = r.barras[b] || 0;
        });
        if (typeof _grava === 'function') _grava(c, lvl);
        if (typeof reabrir === 'function') reabrir(key);
      });
    };
  }

  console.info('%cMOTOR NO SERVIDOR — modo ' + MODO + ' · ' + URL_MOTOR,
               'font-weight:bold;color:#22c58b');
  console.info('Para ver as divergências: MOTOR.divergencias');
})();
