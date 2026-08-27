# -*- coding: utf-8 -*-
"""TELAS_1808 — as telas do arquivo da designer, montadas com o dado de verdade.

  ⛔ ESTA CAMADA SUBSTITUI, NAO SOBREPOE. O que ela escreve (o painel do Inicio,
     a aba de Boxes, o Como calculamos, o Ranking) e o molde da designer
     preenchido; o desenho antigo daquele bloco deixa de ser montado.

  ⛔ O MOLDE E O DELA, LETRA POR LETRA. Vem do ClubEfootball-Telas.dc.html pelo
     extrai_design.py; aqui nao se reescreve marcacao, so se preenche
     {{ campo }} e <sc-for>. Se a tela sair diferente da foto, o conserto e no
     dado ou no extrator — nunca "na mao, parecido".

  ⛔ COR SO POR VARIAVEL. As cores dela viraram --d1..--d131, com tabela para o
     escuro e para o claro. Nenhum valor fica preso no elemento.
"""
# ⛔ 19/08 — ESTE MODULO ACHA O VIZINHO SOZINHO.
#    Ele mora em ClubEfootball\programas junto com o moldes_design.py. Quando
#    alguem importa o telas de outro lugar (ou quando a pasta vai sozinha para
#    o GitHub, sem a raiz da v6), o `import moldes_design` so acha o vizinho
#    se a propria pasta estiver no caminho de busca. Uma linha, e o modulo
#    para de depender de quem o chamou.
import os as _os, sys as _sys
_AQUI = _os.path.dirname(_os.path.abspath(__file__))
if _AQUI not in _sys.path:
    _sys.path.insert(0, _AQUI)

from moldes_design import MOLDES, TOK_ESCURO, TOK_CLARO


def _vars(tab):
    return '\n'.join(' %s:%s;' % (k, v) for k, v in tab.items())


CSS_TELAS = ("""
<style id=TELAS_1808>
/* ⛔ 19/08 — OS TOKENS TAMBEM NO :root.
   Se por qualquer motivo o `data-tema` nao estiver no <html> (o script do tema
   estourar, o localStorage barrar no file://, um patch rodar antes), as cores
   sumiam TODAS e a tela saia sem nada. O escuro passa a ser o piso. */
:root{
""" + _vars(TOK_ESCURO) + """
}
html[data-tema=escuro]{
""" + _vars(TOK_ESCURO) + """
}
html[data-tema=claro]{
""" + _vars(TOK_CLARO) + """
}
/* Contraste funcional no tema claro. Os controles continuam discretos, mas
   nao podem desaparecer sobre o fundo claro. */
html[data-tema=claro] .t6ficha [data-bar]{
 background:#dcefe4!important;border-color:#358a60!important;color:#0b4d30!important;
 font-weight:900!important;box-shadow:0 1px 2px rgba(11,77,48,.12)!important}
html[data-tema=claro] .t6ficha .t6posnativa{
 background:#edf8f1!important;border-color:#69aa86!important;color:#07482c!important;
 font-weight:900!important}
html[data-tema=claro] .t6ficha [data-t6pede]{
 background:#f5fbf7!important;border-color:#25855b!important;box-shadow:0 10px 26px #163f2b22!important}
html[data-tema=claro] .t6ficha [data-t6pede]>span{color:#49665a!important}
html[data-tema=claro] .t6ficha [data-t6pede] button{
 background:#fff!important;border-color:#8db8a2!important;color:#123c2a!important}
html[data-tema=claro] .t6ficha [data-t6pede] button small{
 background:#e4f1e9!important;border-color:#76a88e!important;color:#294f3e!important}
html[data-tema=claro] .t6ficha [data-campo=pode]{
 background:rgba(255,255,255,.32)!important;border-color:rgba(255,255,255,.72)!important;color:#fff!important}
html[data-tema=claro] .t6ficha [data-campo=fora]{
 background:rgba(0,0,0,.22)!important;border-color:rgba(255,255,255,.16)!important;color:#9bb0a4!important}
/* a tela da designer ocupa a largura do app; a fonte e a do sistema */
.t6tela{width:100%;max-width:1280px;margin:0 auto;font-family:inherit}
.t6tela *{box-sizing:border-box}
.t6tela img{max-width:100%}

/* ⛔ O CELULAR (fotos 14 a 17). O molde dela e de 1280; as grades dele sao
   todas `repeat(N,minmax(0,1fr))`, entao da para dobra-las por seletor de
   atributo, sem tocar numa virgula da marcacao. Nada de segunda versao da
   tela: e a MESMA, dobrada. */
@media(max-width:820px){
 .t6ficha>div:first-child,
 .t6ficha>div[style*="width:1280px"]{
  width:100%!important;max-width:100%!important;
  grid-template-columns:minmax(0,1fr)!important}
 .t6ficha>div:first-child>div,
 .t6ficha>div[style*="width:1280px"]>div{min-width:0!important}
 .t6ficha [data-fn]{width:100%!important;min-width:0!important}
 .t6tela [style*="grid-template-columns:repeat(2,minmax(0,1fr))"],
 .t6tela [style*="grid-template-columns:repeat(3,minmax(0,1fr))"],
 .t6tela [style*="grid-template-columns:repeat(4,minmax(0,1fr))"],
 .t6tela [style*="grid-template-columns:1fr 1fr"],
 .t6tela [style*="grid-template-columns:minmax(0,1.25fr) minmax(0,1fr)"],
 .t6tela [style*="grid-template-columns:404px minmax(0,1fr)"]{
  grid-template-columns:1fr!important}
 .t6tela [style*="grid-template-columns:repeat(6,minmax(0,1fr))"]{
  grid-template-columns:repeat(2,minmax(0,1fr))!important}
 .t6tela [style*="padding:22px"]{padding:14px!important}
 .t6tela [style*="padding:30px 32px"]{padding:18px!important}
 .t6tela [style*="padding:26px 22px"]{padding:16px 14px!important}
 .t6tela [style*="padding:20px 22px 26px"]{padding:14px!important}
 .t6tela [style*="padding:0 22px"]{padding:0 14px!important}
 .t6tela [style*="padding:14px 22px"]{padding:12px 14px!important}
 .t6tela [style*="padding:18px 22px"]{padding:14px!important}
 .t6tela [style*="font-size:34px"]{font-size:26px!important}
 .t6tela [style*="font-size:30px"]{font-size:23px!important}
 .t6tela [style*="font-size:26px"]{font-size:20px!important}
 .t6tela [style*="width:660px"]{width:100%!important;max-width:360px!important}
 .t6tela [style*="flex-wrap:wrap"]{row-gap:8px}
 .t6tela{overflow-x:hidden}
 /* No celular, a tabela tecnica mostra somente o que ajuda a decidir:
    atributo, classe, total, alvo e pontos. Os insumos detalhados continuam no
    desktop e nos blocos acima. */
 .t6ficha .t6attrgrid{
  grid-template-columns:130px 88px repeat(11,50px)!important;
  gap:6px!important;min-width:840px!important;width:840px!important}
 .t6ficha [data-t6controles-build]{
  display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;
  gap:8px!important}
 .t6ficha [data-t6controles-build]>*{width:100%!important;min-width:0!important;margin:0!important}
 .t6ficha [data-t6controles-build]>:first-child{grid-column:1/-1}
 .t6ficha [data-t6controles-build]>:nth-child(2){grid-column:1;grid-row:2}
 .t6ficha [data-t6controles-build]>:nth-child(4){grid-column:2;grid-row:2}
 .t6ficha [data-t6controles-build]>:nth-child(3){grid-column:1/-1;grid-row:3}
 /* A segunda barra pertence ao modal antigo. No celular ela so repete as
    acoes e alonga a ficha. */
 .t6ficha [data-t6bld]:not([data-t6controles-build]){display:none!important}
 #box>.bldbar{display:none!important}
 #voltar,#gbBt,#t6ver,#_carregando_banco,.t6mobilelegacy{display:none!important}
 .t6ficha div:has(>.t6attrgrid){
  overflow-x:auto!important;overflow-y:hidden!important;max-width:100%!important;
  padding-bottom:8px!important;scrollbar-width:thin}
 .t6ficha select{max-width:100%!important}
 .t6ficha [style*="display:flex;flex-wrap:wrap;gap:8px"]{gap:6px!important}
 .t6ficha .t6habsnativas{
  display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;
  gap:6px!important;width:100%!important}
 .t6ficha .t6habsnativas>span{
  width:100%!important;min-width:0!important;min-height:34px!important;
  justify-content:center!important;text-align:center!important;white-space:normal!important;
  line-height:1.15!important;padding:6px 7px!important;font-size:11px!important}
 .t6ficha .t6modosmobile{
  display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;
  gap:7px!important;align-items:stretch!important;width:100%!important}
 .t6ficha .t6modo-funcao{
  grid-column:1/-1!important;grid-row:1!important;width:100%!important;
  min-width:0!important;margin:0!important}
 .t6ficha .t6modo-funcao>span{
  width:100%!important;min-width:0!important;min-height:44px!important;
  display:flex!important;align-items:center!important;justify-content:space-between!important}
 .t6ficha .t6modo-max,.t6ficha .t6modo-build,.t6ficha .t6modo-melhora{
  min-width:0!important;width:100%!important;min-height:72px!important;margin:0!important;
  padding:8px 6px!important;border-radius:12px!important;display:flex!important;
  align-items:center!important;justify-content:center!important;text-align:center!important;
  white-space:normal!important;line-height:1.25!important}
 .t6ficha .t6modo-max{grid-column:1!important;grid-row:2!important;box-shadow:0 6px 18px #31db7950!important}
 .t6ficha .t6modo-build{grid-column:2!important;grid-row:2!important}
 .t6ficha .t6modo-melhora{grid-column:3!important;grid-row:2!important;flex-direction:column!important;gap:4px!important}
 .t6ficha .t6modo-info{display:none!important}
}
@media(max-width:520px){
 .t6tela [style*="grid-template-columns:repeat(6,minmax(0,1fr))"]{
  grid-template-columns:repeat(2,minmax(0,1fr))!important}
}
</style>
""")

JS_TELAS = r"""
<script id=TELAS_1808_JS>
/* O MOTOR DO MOLDE — o minimo para dar vida ao HTML da designer.
   Ela ja entregou o desenho como template: <sc-for list="{{ x }}" as="y"> e
   {{ y.campo }}. Entao aqui nao ha marcacao escrita a mao: so preenchimento. */
(function(){
  var M = __MOLDES__;
  window.T6M = M;

  function pega(ctx, cam){
    var p = String(cam).split('.'), v = ctx;
    for (var i = 0; i < p.length; i++){
      if (v === null || v === undefined) return undefined;
      v = v[p[i]];
    }
    return v;
  }
  function bloco(h, tag){
    var ini = h.indexOf('<' + tag);
    if (ini < 0) return null;
    var fim = h.indexOf('>', ini) + 1, n = 1, k = fim;
    while (k < h.length && n > 0){
      var a = h.indexOf('<' + tag, k), b = h.indexOf('</' + tag + '>', k);
      if (b < 0) break;
      if (a >= 0 && a < b){ n++; k = h.indexOf('>', a) + 1; }
      else { n--; k = b + tag.length + 3; }
    }
    return {ini:ini, abre:h.slice(ini, fim), corpo:h.slice(fim, k - (tag.length + 3)), fim:k};
  }
  function tpl(h, ctx){
    var b;
    while ((b = bloco(h, 'sc-for'))){
      var m = /list="\{\{\s*([^}]+?)\s*\}\}"\s+as="([^"]+)"/.exec(b.abre);
      var lista = m ? pega(ctx, m[1].trim()) : [];
      var alias = m ? m[2] : 'x', saida = '';
      (lista || []).forEach(function(item, i){
        var c = Object.create(ctx); c[alias] = item; c['_i'] = i;
        saida += tpl(b.corpo, c);
      });
      h = h.slice(0, b.ini) + saida + h.slice(b.fim);
    }
    while ((b = bloco(h, 'sc-if'))){
      var mv = /value="\{\{\s*([^}]+?)\s*\}\}"/.exec(b.abre);
      var v = mv ? pega(ctx, mv[1].trim()) : false;
      h = h.slice(0, b.ini) + (v ? tpl(b.corpo, ctx) : '') + h.slice(b.fim);
    }
    return h.replace(/\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}/g, function(_, k){
      var v = pega(ctx, k);
      return (v === undefined || v === null) ? '' : String(v);
    });
  }
  window.t6tpl = tpl;

  /* ---------------- o dado ---------------- */
  function esc(s){ return String(s == null ? '' : s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'); }
  function n2(v){ return (Math.round(v * 100) / 100).toFixed(2); }
  function pct(c){
    try{ var t = topoDoTipo(c.tipo); return t > 0 ? (100 * nota(c) / t) : 0; }
    catch(e){ return 0; }
  }
  var FONTE_PCT = 'font-family:inherit;font-size:19px;font-weight:700;letter-spacing:-.4px;color:';
  function estiloPct(p){
    return FONTE_PCT + (p >= 99.5 ? 'var(--d8)' : (p >= 95 ? 'var(--d55)' : 'var(--d13)'));
  }
  window.t6card = function(c, i){
    var p = pct(c);
    return {r: (i + 1) + 'º', nome: esc(c.nome), est: esc(c.modelo || ''),
            fn: esc(c.tipo), pos: esc(c.np || c.pos || ''),
            pct: n2(p), pctSt: estiloPct(p), pts: n2(nota(c)),
            k: esc(c.id + '|' + c.tipo)};
  };
  window.t6PorBox = function(){
    var cx = {};
    for (var i = 0; i < D.length; i++){
      var c = D[i];
      if (!c || c.id === 'MOLDE' || !c.pacote) continue;
      (cx[c.pacote] = cx[c.pacote] || []).push(c);
    }
    return cx;
  };
  /* ---------------- quem manda no painel ----------------
     ⛔ A CAMADA VELHA SAI DE CENA. Assim que este arquivo existe, o desenho
        antigo do painel para de ser montado (ele testa window.T6TELAS). Duas
        camadas montando o mesmo bloco foi o que fez a tela piscar. */
  window.T6TELAS = true;
  /* ⛔ 19/08 — A TRAVA TEM QUE SOLTAR SEMPRE.
     Defeito medido na maquina do Luis: durante o carregamento progressivo a
     primeira pintura estourou, `_t6pintando` ficou LIGADA para sempre e a
     tela nunca mais foi desenhada — pagina em branco permanente, mesmo depois
     das linhas todas chegarem. Duas regras nasceram daqui:
       1. a trava solta no `finally`, aconteca o que acontecer;
       2. se a tela nova falhar ou vier vazia, quem desenha e o DESENHO ANTIGO.
          Tela feia e melhor que tela branca. */
  window.t6Painel = function(qual){
    var w = document.getElementById('homewrap');
    if (!w) return;
    window._t6aba = qual;
    if (window._t6pintando) return;      /* nao se chama de dentro de si */
    window._t6pintando = true;
    var h = '';
    try{
      try{ homeToggle(1); }catch(e){}
      if (qual === 'boxant')        h = window.t6TelaBoxes(true);
      else if (qual === 'boxatual') h = window.t6TelaBoxes(false);
      else if (qual === 'como')     h = window.t6TelaComo();
      else if (qual === 'ranking')  h = window.t6TelaRanking();
      else                          h = window.t6TelaInicio();
    }catch(e){
      h = '';
      if (window.console) console.warn('TELAS_1808: ' + qual + ' falhou —', e);
    }finally{
      window._t6pintando = false;       /* SOLTA SEMPRE */
    }
    if (!h || String(h).replace(/<[^>]*>/g,'').trim().length < 3){
      /* a tela nova nao tinha o que mostrar (ainda carregando, ou erro):
         devolve o desenho antigo em vez de deixar o painel vazio */
      if (typeof window._t6homeAntigo === 'function'){
        try{ window._t6homeAntigo.call(window); return; }catch(e){}
      }
      return;                            /* nao apaga o que ja esta na tela */
    }
    w.innerHTML = '<div class="t6tela">' + h + '</div>';
    try{ window.t6Cliques(w); }catch(e){}
  };
  /* os cliques entram DEPOIS, sem mexer na marcacao dela: as linhas de card
     aparecem na mesma ordem em que foram montadas, entao basta caminhar. */
  window.t6Cliques = function(raiz){
    var alvos = raiz.querySelectorAll('[data-k]');
    alvos.forEach(function(el){
      el.style.cursor = 'pointer';
      el.onclick = function(ev){ ev.stopPropagation();
        try{ abrir(el.dataset.k); }catch(e){} };
    });
  };

  /* ⛔ QUEM ESCREVE O PAINEL PASSA A SER ESTA CAMADA. O homeRender da casca
     continua existindo (o Meu time e o modal ainda dependem dele), mas quando
     uma aba nova esta aberta ele devolve a tela da designer em vez de remontar
     o desenho velho. Sem isto, os dois escrevem no mesmo #homewrap e o ultimo
     a rodar ganha — foi o que fez a tela piscar antes. */
  if (typeof window.homeRender === 'function'){
    var _hr = window.homeRender;
    window._t6homeAntigo = _hr;          /* a rede de seguranca do t6Painel */
    window.homeRender = function(){
      if (window._t6aba && window.t6Painel){ window.t6Painel(window._t6aba); return; }
      return _hr.apply(this, arguments);
    };
  }
  /* ⛔ A TELA JA ABRE NO DESENHO NOVO. Sem esta linha o primeiro desenho era o
     antigo e so trocava depois do primeiro clique numa aba — que foi
     exatamente o "boa parte do site ta operando com design antigo". */
  if (!window._t6aba) window._t6aba = 'inicio';

  /* ⛔ 19/08 — O VIGIA DA TELA EM BRANCO.
     Na maquina do Luis o painel ficou vazio e nunca mais voltou. A causa foi
     a trava presa, mas a licao e outra: NENHUM defeito futuro pode deixar a
     tela branca. Este relogio olha o painel; se ele esta a vista e vazio,
     manda desenhar — primeiro a tela nova, e se ela nao der, a antiga. */
  setInterval(function(){
    try{
      var w = document.getElementById('homewrap');
      if (!w || !w.offsetParent) return;                 /* nao esta a vista */
      if ((w.innerText || '').trim().length > 2) return; /* tem conteudo */
      if (window._t6pintando){ window._t6pintando = false; }  /* destrava */
      if (window.t6Painel) window.t6Painel(window._t6aba || 'inicio');
      if ((w.innerText || '').trim().length > 2) return;
      if (typeof window._t6homeAntigo === 'function') window._t6homeAntigo.call(window);
    }catch(e){}
  }, 1500);

  /* ---------------- BOXES (atuais e anteriores) ---------------- */
  /* O molde e o mesmo da foto 3; o que muda entre as duas abas e o titulo,
     a linha de baixo e quais boxes entram. */
  window.t6TelaBoxes = function(anteriores){
    if (!M || !M['boxes'] || !M['boxes'].corpo) return '';
    var cx = window.t6PorBox(), ativas = {};
    try{ (BOXATIVA || []).forEach(function(n){ ativas[n] = 1; }); }catch(e){}
    var nomes = Object.keys(cx).filter(function(n){
      return anteriores ? !ativas[n] : !!ativas[n];
    });
    /* anteriores: da mais nova para a mais velha, pela data que o historico guarda */
    function quando(n){
      try{ return (BOXHIST[n] && BOXHIST[n].visto) || (BOXDT && BOXDT[n]) || ''; }
      catch(e){ return ''; }
    }
    if (anteriores) nomes.sort(function(a, b){ return (quando(b) || '').localeCompare(quando(a) || ''); });
    else nomes.sort(function(a, b){ return (cx[b] || []).length - (cx[a] || []).length; });
    var quantas = window._t6todasBoxes ? nomes.length : (anteriores ? 6 : 4);
    var dados = {boxesAnt: nomes.slice(0, quantas).map(function(n){
      var cs = cx[n] || [];
      return {n: esc(n), q: cs.length + ' card' + (cs.length === 1 ? '' : 's'),
              cards: window.t6Melhores(cs, 3).map(window.t6card)};
    })};
    /* ⛔ o data-k entra no molde ANTES de preencher, na linha do card. E o
       unico acrescimo a marcacao dela — sem ele nao da para abrir a ficha. */
    var molde = M.boxes.corpo.replace(
      '<div style="display:flex;align-items:center;gap:11px">',
      '<div data-k="{{ c.k }}" style="display:flex;align-items:center;gap:11px">');
    var h = tpl(molde, dados);
    var sub = anteriores
      ? (nomes.length + ' boxes encerradas · top 3 de cada uma · mostrando as '
         + Math.min(quantas, nomes.length) + ' mais recentes')
      : (nomes.length + ' boxes no ar · top 3 de cada uma · mostrando as '
         + Math.min(quantas, nomes.length) + ' maiores');
    h = h.replace('72 boxes encerradas · top 3 de cada uma · mostrando as 6 mais recentes', sub);
    if (!anteriores) h = h.replace('>Boxes anteriores<', '>Boxes atuais<')
                          .replace('voltar aos lançamentos', 'ver as anteriores');
    return h;
  };

  /* ---------------- INICIO ---------------- */
  var FOTO = 'https://efimg.com/efootballhub22/images/player_cards/';
  function url(c){ return FOTO + String(c.id).split('@')[0] + '_l.png'; }
  function medSt(c, w, h, r){
    /* o quadrado da foto: o molde deixa o estilo por nossa conta, entao a foto
       entra por aqui — sem mexer na marcacao dela. */
    return 'width:' + w + 'px;height:' + h + 'px;border-radius:' + r + 'px;flex:none;'
         + 'display:block;border:1px solid var(--d7);'
         + 'background:url(' + url(c) + ') center/cover no-repeat,'
         + 'linear-gradient(160deg,var(--d33),var(--d32))';
  }
  function veredicto(p){
    var C = window.T6_CORTES || [99, 95];
    if (p >= C[0]) return ['CONTRATAR A QUALQUER CUSTO', 'var(--d8)', 'var(--d94)', 'var(--d96)'];
    if (p >= C[1]) return ['CONTRATAR SE FOR BARATO', 'var(--d55)', 'var(--d89)', 'var(--d90)'];
    return ['CONTRATAR SE FOR GRÁTIS', 'var(--d13)', 'var(--d14)', 'var(--d29)'];
  }
  window.t6cardBox = function(c, i){
    var d = window.t6card(c, i), p = parseFloat(d.pct), v = veredicto(p);
    d.foto = 'url(' + url(c) + ')';
    d.v = v[0];
    d.vSt = 'font-style:normal;font-family:inherit;font-size:8.5px;font-weight:700;'
          + 'letter-spacing:.7px;padding:3px 7px;border-radius:999px;white-space:nowrap;'
          + 'color:' + v[1] + ';background:' + v[2] + ';border:1px solid ' + v[3];
    return d;
  };
  window.t6TelaInicio = function(){
    if (!M || !M.inicio || !M.inicio.corpo) return '';   /* sem molde, sem tela */
    var cx = window.t6PorBox(), ativas = {};
    try{ (BOXATIVA || []).forEach(function(n){ ativas[n] = 1; }); }catch(e){}
    var nomes = Object.keys(cx).filter(function(n){ return !!ativas[n]; })
      .sort(function(a, b){ return (cx[b] || []).length - (cx[a] || []).length; });

    /* Top 3 do jogo — as tres maiores pontuacoes entre todas as funcoes */
    var todos = [];
    for (var i = 0; i < D.length; i++){
      var c = D[i]; if (!c || c.id === 'MOLDE' || !c.tipo) continue;
      var v; try{ v = nota(c); }catch(e){ continue; }
      if (v > 0) todos.push([c, v]);
    }
    todos.sort(function(a, b){ return b[1] - a[1]; });
    var vistos = {}, top3 = [];
    for (var j = 0; j < todos.length && top3.length < 3; j++){
      var k = todos[j][0].nome;
      if (vistos[k]) continue;
      vistos[k] = 1; top3.push(todos[j]);
    }

    /* Top 3 de cada funcao, por setor e na ordem que o Luis ditou */
    var porFn = {};
    for (var x = 0; x < D.length; x++){
      var cc = D[x]; if (!cc || cc.id === 'MOLDE' || !cc.tipo) continue;
      (porFn[cc.tipo] = porFn[cc.tipo] || []).push(cc);
    }
    var SET = {}; try{ SET = window.t6Setor ? window.t6Setor() : {}; }catch(e){}
    var ORD = window.t6Ordem || Object.keys(porFn);
    var pref = ['GOLEIRO', 'DEFESA', 'MEIO', 'ATAQUE'], grupos = {};
    ORD.forEach(function(f){
      if (!porFn[f]) return;
      var s = SET[f] || 'OUTRAS';
      (grupos[s] = grupos[s] || []).push(f);
    });
    var SIG = {};
    try{
      document.querySelectorAll('#fam .famg').forEach(function(g){
        var i2 = g.querySelector('.famt i'), ts = g.querySelectorAll('.tab[data-t]');
        ts.forEach(function(tb){ SIG[tb.dataset.t] = i2 ? i2.textContent.trim() : ''; });
      });
    }catch(e){}

    var dados = {
      boxes: nomes.slice(0, 3).map(function(n){
        var cs = cx[n] || [];
        return {n: esc(n), q: cs.length + ' card' + (cs.length === 1 ? '' : 's'),
                cards: window.t6Melhores(cs, 3).map(window.t6cardBox)};
      }),
      top3Jogo: top3.map(function(par, i){
        var c = par[0], s = n2(par[1]).split('.');
        return {r: (i + 1) + 'º', rSt: 'font-style:normal;font-family:inherit;font-size:10px;'
                  + 'letter-spacing:1.2px;font-weight:700;color:'
                  + (i === 0 ? 'var(--d8)' : (i === 1 ? 'var(--d30)' : 'var(--d13)')),
                medSt: medSt(c, 86, 114, 12),
                nome: esc(c.nome), fn: esc((c.tipo || '').toUpperCase()),
                est: esc(c.modelo || ''), ptsInt: s[0], ptsDec: '.' + s[1],
                pos: esc(c.np || c.pos || ''), box: esc(c.pacote || ''),
                k: esc(c.id + '|' + c.tipo)};
      }),
      topFns: pref.concat(Object.keys(grupos).filter(function(s){ return pref.indexOf(s) < 0; }))
        .filter(function(s){ return grupos[s]; })
        .map(function(s){
          return {s: s, fns: grupos[s].map(function(f){
            var lst = window.t6Melhores(porFn[f], 3);
            return {n: esc(f), sig: esc(SIG[f] || ''), fn: esc(f),
              podio: lst.map(function(c, i){
                var p = pct(c);
                return {r: (i + 1) + 'º',
                  rSt: 'font-style:normal;font-family:inherit;font-size:9px;font-weight:700;'
                     + 'padding:2px 6px;border-radius:999px;color:'
                     + (i === 0 ? 'var(--d8)' : (i === 1 ? 'var(--d30)' : 'var(--d13)'))
                     + ';background:' + (i === 0 ? 'var(--d94)' : 'var(--d14)')
                     + ';border:1px solid ' + (i === 0 ? 'var(--d96)' : 'var(--d29)'),
                  medSt: medSt(c, 44, 58, 8),
                  nome: esc(c.nome),
                  pts: n2(nota(c)),
                  ptsSt: 'font-family:inherit;font-size:15px;font-weight:700;letter-spacing:-.4px;color:var(--d1)',
                  pct: n2(p), pctSt: estiloPct(p),
                  k: esc(c.id + '|' + c.tipo)};
              })};
          })};
        })
    };

    var molde = M.inicio.corpo
      .replace('<div style="display:flex;align-items:center;gap:11px">',
               '<div data-k="{{ c.k }}" style="display:flex;align-items:center;gap:11px">')
      .replace('<span style="{{ t.medSt }}"></span>',
               '<span data-k="{{ t.k }}" style="{{ t.medSt }}"></span>');
    var h = tpl(molde, dados);
    var q = (typeof CONT !== 'undefined') ? CONT : {};
    h = h.replace('2.785 cards medidos em 19 funções',
                  (q.cards_total || 0).toLocaleString('pt-BR') + ' cards medidos em 19 funções');
    h = h.replace('3 de 9 boxes atuais · top 3 de cada uma',
                  Math.min(3, nomes.length) + ' de ' + nomes.length
                  + ' boxes atuais · top 3 de cada uma');
    return h;
  };

  /* o seletor de funcao da barra dela abre o mesmo menu que a casca ja tem */
  window.t6FnMenu = function(raiz){
    var m = document.getElementById('t6fnmenu');
    var bf = raiz.querySelector('#t6rkFiltros');
    if (bf){ bf.style.cursor = 'pointer';
      bf.onclick = function(ev){ ev.stopPropagation(); try{ toggleFiltros(); }catch(e){} }; }
    var bc = raiz.querySelector('#t6rkCond');
    if (bc){ bc.style.cursor = 'pointer';
      bc.onclick = function(ev){ ev.stopPropagation(); try{ toggleCond(); }catch(e){} }; }
    ['t6rkFn', 't6rkTodas'].forEach(function(id){
      var el = raiz.querySelector('#' + id);
      if (!el) return;
      el.style.cursor = 'pointer';
      el.onclick = function(ev){
        ev.stopPropagation();
        if (!m) return;
        m.classList.toggle('on');
        if (m.classList.contains('on')){
          var r = el.getBoundingClientRect();
          m.style.position = 'fixed';
          m.style.left = Math.max(8, r.left) + 'px';
          m.style.top  = (r.bottom + 6) + 'px';
          try{ if(window.t6EncheMenu) window.t6EncheMenu(m); }catch(e){}
        }
      };
    });
  };

  /* ---------------- RANKING ----------------
     A tela e a da foto 5: podio de 3 + grade de 6 por linha. O molde e o dela;
     a casca continua dona do filtro e da ordem (lista()). */
  window.t6TelaRanking = function(){
    if (!M || !M['ranking'] || !M['ranking'].corpo) return '';
    var L; try{ L = lista(); }catch(e){ L = []; }
    if (!L || !L.length) return '';
    var lim; try{ lim = VIS; }catch(e){ lim = 120; }
    var mostra = L.slice(0, Math.max(3, lim || 120));
    function g(c, i){
      var v = nota(c), p = pct(c);
      return {r: (i + 1), pos: esc(c.np || c.pos || ''), nome: esc(c.nome),
              est: esc(c.modelo || ''), fn: esc(c.tipo),
              pts: n2(v), pct: n2(p),
              w: Math.max(2, Math.min(100, p)).toFixed(1) + '%',
              medSt: medSt(c, 84, 84, 13), medSt2: medSt(c, 34, 34, 9),
              k: esc(c.id + '|' + c.tipo)};
    }
    var dados = {podio: mostra.slice(0, 3).map(g),
                 resto: mostra.slice(3).map(function(c, i){ return g(c, i + 3); })};
    var molde = M.ranking.corpo
      /* a foto entra no lugar do quadrado dela, sem mexer na marcacao */
      .replace('<span style="width:84px;height:84px;border-radius:13px;background:linear-gradient(160deg,var(--d33),var(--d32));border:1px solid var(--d7);display:flex;align-items:center;justify-content:center;font-size:10px;color:var(--d16);flex:none">foto</span>',
               '<span style="{{ g.medSt }}"></span>')
      .replace('<span style="width:34px;height:34px;border-radius:9px;background:linear-gradient(160deg,var(--d33),var(--d32));border:1px solid var(--d10);flex:none;display:block"></span>',
               '<span style="{{ g.medSt2 }}"></span>')
      /* o data-k e o unico acrescimo: sem ele nao da para abrir a ficha */
      .split('<div style="position:relative;border-radius:16px;padding:18px;')
        .join('<div data-k="{{ g.k }}" style="position:relative;border-radius:16px;padding:18px;')
      .split('<div style="position:relative;border-radius:14px;padding:13px;')
        .join('<div data-k="{{ g.k }}" style="position:relative;border-radius:14px;padding:13px;')
      /* os tres controles da barra de funcao ganham identidade para o clique */
      .replace('>Ala finalizador<', ' id="t6rkFn">Ala finalizador<')
      .replace('>19 funções ▾<', ' id="t6rkTodas">19 funções ▾<')
      .replace('>MEIO<', ' id="t6rkSet">MEIO<');
    var h = tpl(molde, dados);
    var fn = '', st = '';
    try{ fn = S.tipo || ''; }catch(e){}
    try{ var mm = window.t6Setor ? window.t6Setor() : {}; st = mm[fn] || ''; }catch(e){}
    h = h.replace('>Ala finalizador<', '>' + esc(fn) + '<').replace('>MEIO<', '>' + esc(st) + '<');
    var qf = (window.t6Ordem || []).length || 19;
    h = h.replace('>19 funções ▾<', '>' + qf + ' funções ▾<');
    /* os dois chips da direita contam o que a casca esta filtrando de verdade */
    h = h.replace('pontuação ≥ 100 <span style="color:var(--d16)">×</span>',
                  esc(L.length.toLocaleString('pt-BR')) + ' cards nesta função');
    /* ⛔ OS CONTROLES QUE MORAVAM NA SEGUNDA FILA VOLTAM AQUI, no lugar que ela
       desenhou para eles. Nao e enfeite: sao os mesmos botoes da casca. */
    var cond = '';
    try{ cond = (typeof CTXT !== 'undefined') ? CTXT[CMODE] : ''; }catch(e){}
    h = h.replace('filtros <b style="color:var(--d8)">2</b>',
                  '<span id="t6rkCond">' + esc(cond || 'condicional') + '</span>'
                  + ' &nbsp;·&nbsp; <span id="t6rkFiltros">filtros</span>');
    return h;
  };
  /* ---------------- COMO CALCULAMOS ---------------- */
  window.t6TelaComo = function(){
    if (!M || !M['como'] || !M['como'].corpo) return '';
    var h = tpl(M.como.corpo, {});
    var q = (typeof CONT !== 'undefined') ? CONT : {};
    function pt(v){ return (v || 0).toLocaleString('pt-BR'); }
    /* os tres numeros do alto sao dado nosso, nao enfeite */
    h = h.replace('2.785', pt(q.cards_total || 0));
    var n = 0;
    try{ n = window.t6Contas ? window.t6Contas() : 0; }catch(e){}
    if (n > 0){
      var txt = (n >= 1e9) ? ((n / 1e9).toFixed(1).replace('.', ',') + ' bi')
                           : (Math.round(n / 1e6) + ' mi');
      h = h.replace('1.4 bi', txt);
    }
    return h;
  };

  /* ================= FICHA DO CARD (fotos 6, 8 e 9) =================
     O molde e o dela — estava escondido DENTRO do bloco 5a do arquivo, junto
     com a grade do Elenco, e por isso ficou de fora do primeiro extrator.

     ⛔ NENHUM BOTAO E REESCRITO. Os `-`/`+`, o Otimizar, o tecnico e as
        habilidades continuam chamando as MESMAS funcoes da casca (editBar,
        trocaTec, addHab, remHab, toggleCondCard, restaurarMotor). O molde so
        ganha um `data-` em cada um, e o t6FichaCliques amarra. Se a ficha nova
        falhar, a ficha antiga volta — a mesma rede do painel. */

  /* a grade do campinho — a mesma da casca, aqui em cima porque la ela e local */
  window.T6_CAMPO = [['PE','CA','PD'], ['','SA',''], ['MLE','MO','MLD'], ['','MC',''],
                     ['','VOL',''], ['LE','ZC','LD'], ['','GK','']];
  function _n1(v){ return (Math.round(v * 10) / 10).toFixed(1); }
  function _sn(v, casas){
    var x = (+v) || 0, s = x.toFixed(casas === undefined ? 0 : casas);
    return (x > 0 ? '+' : '') + s;
  }
  var C_MAIS = 'var(--d8)', C_MENOS = 'var(--d72)', C_ZERO = 'var(--d17)';
  function _stNum(v){
    var x = (+v) || 0;
    return 'font-family:inherit;font-size:11px;text-align:right;color:'
         + (x > 0 ? C_MAIS : (x < 0 ? C_MENOS : C_ZERO));
  }
  /* ⛔ 19/08 — AS CLASSES SAO UMA ESCALA, ENTAO A COR TAMBEM E.
     Ordem do Luis: *"faz indispensavel em verde forte, depois desejavel mais
     fraca, util mais fraca que desejavel e acessorio mais fraca ainda"*.
     Antes cada classe tinha uma cor propria — cinza, laranja, verde, azul.
     Quatro cores diferentes nao dizem qual vale mais: o olho tinha que ler a
     palavra. Agora e UM verde so, perdendo forca degrau a degrau, e a ordem
     se le sem ler. O numero e o PESO do atributo naquela funcao. */
  var CLS_F = {12: ['Indispensável', 1.00], 7: ['Desejável', 0.66],
               6: ['Desejável', 0.66], 3: ['Útil', 0.40],
               1: ['Acessório', 0.22], 0: ['—', 0.10]};
  function _stCls(p){
    var f = (CLS_F[p] || CLS_F[0])[1];
    var claro = false;
    try{ claro = document.documentElement.getAttribute('data-tema') === 'claro'; }catch(e){}
    /* o mesmo verde, so mudando quanto dele entra */
    var letra  = 'rgba(' + Math.round(214 - 74 * f) + ',' + Math.round(240 - 12 * f) + ','
                         + Math.round(222 - 44 * f) + ',' + (0.45 + 0.55 * f).toFixed(2) + ')';
    var fundo  = 'rgba(34,197,139,' + (0.05 + 0.24 * f).toFixed(3) + ')';
    var borda  = 'rgba(34,197,139,' + (0.12 + 0.62 * f).toFixed(3) + ')';
    /* ⛔ e o DESENHO muda junto, nao so o tom: contraste que depende so de cor
       morre no primeiro tema novo. A escada se le ate em preto e branco.
         cheio · fraco+contorno · so contorno · contorno tracejado */
    var desenho;
    if (f >= 0.9)      desenho = 'background:linear-gradient(180deg,#8df3ae,#22c58b);'
                              + 'border:1px solid #22c58b;color:#06200f;font-weight:800;'
                              + 'letter-spacing:.04em';
    else if (claro && f >= 0.6) desenho = 'background:rgba(34,197,139,.17);border:1px solid #3d966c;'
                              + 'color:#0d5f3e;font-weight:800';
    else if (claro && f >= 0.35) desenho = 'background:#eef7f2;border:1px solid #579474;'
                              + 'color:#205c42;font-weight:700';
    else if (claro && f >= 0.15) desenho = 'background:#f5f8f6;border:1px dashed #718f7f;'
                              + 'color:#42584d;font-weight:600';
    else if (claro) desenho = 'background:transparent;border:1px solid #a7b8ae;'
                              + 'color:#5d6d64;font-weight:600';
    else if (f >= 0.6) desenho = 'background:' + fundo + ';border:1px solid ' + borda
                              + ';color:' + letra + ';font-weight:700';
    else if (f >= 0.35) desenho = 'background:transparent;border:1px solid ' + borda
                              + ';color:' + letra + ';font-weight:600';
    else if (f >= 0.15) desenho = 'background:transparent;border:1px dashed ' + borda
                              + ';color:' + letra + ';font-weight:400';
    else                desenho = 'background:transparent;border:1px solid transparent;'
                              + 'color:rgba(255,255,255,.28);font-weight:400';
    return 'font-family:inherit;font-size:9.5px;text-align:center;padding:2px 6px;'
         + 'border-radius:5px;white-space:nowrap;' + desenho;
  }
  /* Habilidades especiais sao inerentes ao card: nunca entram pelo seletor.
     A lista completa e a uniao de `raras` de todas as cartas carregadas. */
  function _ehEspecial(nome){
    if (!nome) return false;
    try{ if (typeof HABRARAS !== 'undefined' && HABRARAS[nome]) return true; }catch(e){}
    try{
      for (var i = 0; i < D.length; i++)
        if (D[i] && (D[i].raras || []).indexOf(nome) >= 0) return true;
    }catch(e){}
    return false;
  }
  window.t6EhEspecial = _ehEspecial;
  /* o fim do <div> que comeca em `i` — contando abre e fecha. */
  function _fimDiv(h, i){
    var n = 0, q = i;
    while (q < h.length){
      var a = h.indexOf('<div', q), b = h.indexOf('</div>', q);
      if (b < 0) return h.length;
      if (a >= 0 && a < b){ n++; q = a + 4; }
      else { n--; q = b + 6; if (n <= 0) return q; }
    }
    return h.length;
  }
  /* apaga o pedaco de texto que comeca em `marca` e vai ate o fim do
     elemento — sem mexer no resto da linha */
  function _tiraTexto(h, marca){
    var i = h.indexOf(marca);
    while (i >= 0){
      var ab = h.lastIndexOf('<', i);
      var fecha = h.indexOf('</', i);
      if (ab < 0 || fecha < 0){ break; }
      var abreFim = h.indexOf('>', ab);
      if (abreFim < 0 || abreFim > i){ break; }
      h = h.slice(0, ab) + h.slice(h.indexOf('>', fecha) + 1);
      i = h.indexOf(marca);
    }
    return h;
  }

  /* tira do HTML o <div> que contem `marca`, subindo `acima` niveis antes */
  function _tiraBloco(h, marca, acima){
    var i = h.indexOf(marca);
    if (i < 0) return h;
    var ab = h.lastIndexOf('<div', i);
    for (var k = 0; k < (acima || 0) && ab > 0; k++) ab = h.lastIndexOf('<div', ab - 1);
    if (ab < 0) return h;
    return h.slice(0, ab) + h.slice(_fimDiv(h, ab));
  }

  /* troca o MIOLO de um bloco dela, achado por um pedaco unico do estilo.
     Nao reescreve a casca do bloco: so o que esta dentro. */
  function _miolo(h, marca, novo){
    var i = h.indexOf(marca);
    if (i < 0) return h;
    var ab = h.lastIndexOf('<div', i), f = h.indexOf('>', ab) + 1;
    if (ab < 0 || f <= 0) return h;
    var n = 1, q = f;
    while (q < h.length && n > 0){
      var a = h.indexOf('<div', q), b = h.indexOf('</div>', q);
      if (b < 0) break;
      if (a >= 0 && a < b){ n++; q = h.indexOf('>', a) + 1; }
      else { n--; q = b + 6; }
    }
    return h.slice(0, f) + novo + h.slice(q - 6);
  }

  /* ⛔ 19/08 — O NOME DA FUNCAO MUDOU E O `FUNC_POS` DA CASCA NAO MUDOU JUNTO.
     A casca guarda as posicoes de cada funcao pelos nomes ANTIGOS (19 chaves).
     O dado de hoje usa os nomes novos. Resultado medido na ficha do Gullit:
     `FUNC_POS['Meia ofensivo armador']` era `undefined`, o `estiloAtiva`
     devolvia false por falta de dado, e TODA funcao renomeada saia marcada
     como BÁSICO — inclusive as que o estilo ativa. A sigla da posicao sumia
     pelo mesmo motivo (o `sigDe` procura na familia, que tambem usa o nome
     velho).
     A ponte mora aqui, num lugar so. Quando a casca for atualizada, apagar. */
  /* ⛔ 19/08 — ORDEM DO LUIS: NUNCA, JAMAIS, ABREVIAR. EM LUGAR NENHUM.
     A abreviacao vem da Konami e do efHub, entao ela chega no dado. Ela para
     AQUI, num lugar so, e some de todas as telas de uma vez. Quem acrescentar
     nome novo abreviado, acrescenta a linha aqui junto. */
  var _POR_EXTENSO = {
    'Jog. de infiltração'   : 'Jogador de infiltração',
    'Especialista em cruz.' : 'Especialista em cruzamento',
    'Finaliz. acrobática'   : 'Finalização acrobática',
    'Arrem. lateral longo'  : 'Arremesso lateral longo',
    'Arrem. longo do GO'    : 'Arremesso longo do goleiro',
    'Repos. baixa do GO'    : 'Reposição baixa do goleiro',
    'Defesa direta (GO)'    : 'Defesa direta do goleiro',
    'Grito de garra (GO)'   : 'Grito de garra do goleiro',
    'Clássica nº 10'        : 'Clássico número 10',
    'Clássico nº 10'        : 'Clássico número 10'
  };
  /* ⛔ 19/08 — MAIUSCULA NO COMECO DE TODA PALAVRA COM MAIS DE DUAS LETRAS.
     Ordem do Luis, e vale para o site inteiro. As de duas letras ou menos
     ficam minusculas ("de", "do", "da", "e"), que e como se escreve nome
     proprio em portugues. Sigla ja maiuscula nao e tocada: "GO" continua
     "GO", nao vira "Go". */
  function _maiusc(t){
    if (!t) return t;
    return String(t).split(' ').map(function(w, i){
      if (!w) return w;
      if (w.length > 1 && w === w.toUpperCase()) return w;      /* sigla */
      var letras = w.replace(/[^0-9A-Za-zÀ-ÿ]/g, '');
      if (i > 0 && letras.length <= 2) return w.toLowerCase();
      var k = w.search(/[0-9A-Za-zÀ-ÿ]/);
      if (k < 0) return w;
      return w.slice(0, k) + w.charAt(k).toUpperCase() + w.slice(k + 1);
    }).join(' ');
  }
  function _extenso(t){
    if (!t) return t;
    var v = _POR_EXTENSO[String(t).trim()];
    return _maiusc(v || t);
  }
  window.t6Extenso = _extenso;
  window.t6Maiusc = _maiusc;

  /* ⛔ 19/08 — O NOME DA FUNCAO NA TELA vs A CHAVE DO BANCO.
     Fechado pelo Luis em 15/08 e registrado na VERDADE-VIGENTE: o nome da
     funcao NUNCA repete o nome de uma posicao, e diz o que o jogador FAZ.
     O banco, o linhas.jsonl e a tabela `funcoes` continuam com a chave velha —
     o motor nao sabe que o nome mudou, e nao precisa saber.
       ⛔ A TRADUCAO E SO DE EXIBICAO. Nenhuma chave e reescrita: a `key`
          continua sendo `id|chave-do-banco`, senao o clique nao acha a linha. */
  var _NOME_NA_TELA = {
    'Meia central armador'   : 'Meia armador',
    'Meia central de chegada': 'Meia de arranque',
    'Meia de ligação armador': 'Meia armador',
    'Meia de ligação avançado':'Meia de arranque',
    'Meia de lado por dentro': 'Ala finalizador',
    'Meia de lado por fora'  : 'Ala cruzador',
    'Meia lateral atacante'  : 'Ala finalizador',
    'Meia lateral cruzador'  : 'Ala cruzador',
    'Ala atacante'           : 'Ala finalizador',
    'Meia ofensivo armador'  : 'Meia ofensivo',
    'Segundo atacante'       : 'Atacante infiltrador',
    'Ponta de lança'         : 'Atacante infiltrador',
    'Ponta criadora'         : 'Atacante criador',
    'Ponta finalizadora'     : 'Atacante finalizador'
  };
  function _nomeFn(t){ return _maiusc(_extenso(_NOME_NA_TELA[t] || t)); }

  /* ⛔ 19/08 — DUAS GRAFIAS, A MESMA FUNCAO.
     O `TJ_REGRA` e o `funcDaPos` da casca respondem com o nome NOVO
     ("Ala cruzador", "Atacante infiltrador"); o `tipo` de cada linha vem com
     a chave do banco ("Meia de lado por fora", "Segundo atacante").
     Comparar as duas com `===` so acertava nas seis funcoes cujo nome nao
     mudou — e era por isso que clicar no campinho so funcionava em CA, ZC,
     GK, LD e VOL. Toda comparacao de nome de funcao passa por aqui. */
  function _mesmaFn(a, b){
    if (!a || !b) return false;
    if (a === b) return true;
    return (_NOME_NA_TELA[a] || a) === (_NOME_NA_TELA[b] || b);
  }
  window.t6NomeFuncao = _nomeFn;

  var _FUNC_ALIAS = {
    'Meia central armador'   : 'Meia armador',
    'Meia central de chegada': 'Meia de arranque',
    'Meia de lado por dentro': 'Ala finalizador',
    'Meia de lado por fora'  : 'Ala cruzador',
    'Meia ofensivo armador'  : 'Meia ofensivo',
    'Segundo atacante'       : 'Atacante infiltrador',
    'Ponta criadora'         : 'Atacante criador',
    'Ponta finalizadora'     : 'Atacante finalizador'
  };
  /* a posicao guardada no dado e uma so; o par do outro lado entra aqui */
  var _PARES = {MLD: ['MLD','MLE'], MLE: ['MLE','MLD'],
                LD:  ['LD','LE'],   LE:  ['LE','LD'],
                PD:  ['PD','PE'],   PE:  ['PE','PD']};

  /* AS POSICOES DE UMA FUNCAO — pela casca quando ela conhece o nome,
     pelo proprio dado (`x.pos`, que o gerador sempre preenche) quando nao. */
  function _posFn(x){
    var t = x && x.tipo, ps = null;
    try{ ps = FUNC_POS[t] || FUNC_POS[_NOME_NA_TELA[t]] || FUNC_POS[_FUNC_ALIAS[t]]; }catch(e){}
    if (ps && ps.length) return ps;
    var p = x && x.pos;
    if (!p) return [];
    return _PARES[p] || [p];
  }

  /* O ESTILO LIGA NESTA FUNCAO?  true / false / null quando nao da pra saber.
     ⛔ `null` NAO vira BÁSICO. Nao se afirma o que nao se mediu. */
  function _estiloLiga(x){
    var ps = _posFn(x), es = null, m = x && x.modelo;
    try{ es = EST_POS[m] || (typeof ESTPT !== 'undefined' ? EST_POS[ESTPT[m]] : null); }catch(e){}
    if (!ps.length || !es) return null;
    for (var i = 0; i < ps.length; i++) if (es.indexOf(ps[i]) >= 0) return true;
    return false;
  }
  function _estiloLigaNaPos(x, pos){
    var es = null, m = x && x.modelo;
    try{ es = EST_POS[m] || (typeof ESTPT !== 'undefined' ? EST_POS[ESTPT[m]] : null); }catch(e){}
    if (!pos || !es) return null;
    return es.indexOf(pos) >= 0;
  }

  function _sigla(p){
    try{ if (typeof SIGJ !== 'undefined' && SIGJ[p]) return SIGJ[p]; }catch(e){}
    return p;
  }

  /* AS POSICOES DE UM CARD — a nativa mais as compradas. */
  function _minhasDe(c){
    var np = c.np, out = [np];
    try{ if (typeof npFixo === 'function') { np = npFixo(c) || np; out = [np]; } }catch(e){}
    try{ (c.sp || []).forEach(function(x){
      if (x && x[0] !== np && out.indexOf(x[0]) < 0) out.push(x[0]); }); }catch(e){}
    return out.filter(Boolean);
  }

  /* ⛔ 19/08 — A SIGLA E A POSICAO QUE **ESTE CARD** EXERCE NESTA FUNCAO.
     Ordem do Luis, repetida em 15/08 e de novo em 19/08: *"se ele pode comprar
     so MLD, nao interessa que MLE tambem seja Ala — poe so o que ele pode"*.
     Entao cruza-se `_minhas` (nativa + compradas) com a regra da funcao, em vez
     de mostrar as duas pontas da familia. Mesma conta da `sigsDoCard` da casca
     antiga; ela morreu junto com o desenho velho e voltou aqui. */
  function _sigFn(x, dono){
    var out = [], minhas = _minhasDe(dono || x), oficiais = _posFn(x);
    /* A relacao funcao × posicao vem SOMENTE de FUNC_POS, cuja origem e
       `funcao_nativa.py`. O estilo decide a funcao NATIVA; ele nao autoriza
       inventar outra posicao para uma funcao ja definida. */
    oficiais.forEach(function(p){
      if (minhas.indexOf(p) < 0) return;
      var g = _sigla(p);
      if (out.indexOf(g) < 0) out.push(g);
    });
    if (out.length) return out.join('/');
    /* nenhuma posicao dele bate: cai para as posicoes da propria funcao */
    var ps = _posFn(x), i;
    for (i = 0; i < ps.length && i < 2; i++){
      var v = _sigla(ps[i]);
      if (out.indexOf(v) < 0) out.push(v);
    }
    return out.join('/');
  }

  /* AS FUNCOES QUE UMA POSICAO PODE EXERCER, dentro das que ESTE card tem. */
  function _funcsDaPos(pos, dono, irmaos){
    var out = [];
    (irmaos || []).forEach(function(y){
      if (_posDaFuncao(y.tipo, dono).indexOf(pos) >= 0){
        var repetida = false;
        for (var i = 0; i < out.length; i++){
          if (_mesmaFn(out[i], y.tipo) || _nomeFn(out[i]) === _nomeFn(y.tipo)){
            repetida = true; break;
          }
        }
        if (!repetida) out.push(y.tipo);
      }
    });
    return out;
  }
  /* AS POSICOES ONDE ESTA FUNCAO PODE SER EXERCIDA POR ESTE CARD */
  function _posDaFuncao(tipo, dono){
    var out = [], minhas = _minhasDe(dono);
    _posFn({tipo:tipo}).forEach(function(p){
      if (minhas.indexOf(p) >= 0 && out.indexOf(p) < 0) out.push(p);
    });
    return out;
  }

  /* ⛔ 19/08 — A NOTA DA LISTA DE FUNCOES E A DO MOTOR, E NAO SE MEXE.
     Ordem do Luis: *"a pontuacao que tem aqui e fixa, ela e de acordo com o que
     a gente tem no banco de dados; ela nao pode mudar quando a gente altera as
     habilidades ou as barras"*.
     E ela mudava: a lista chamava `nota(x)`, que le o estado VIVO da tela.
     Mexer numa barra rebaixava a nota de funcoes que o cara nem abriu — o
     Centroavante fixo caiu de 108,93 para 106,09 sem ninguem tocar nele.
     Aqui a conta e refeita a partir da ANCORA (`anc`), que e o retrato do que
     o motor gravou. O estado da tela e guardado e devolvido intacto: medir nao
     pode alterar o que se mede. E o resultado fica no proprio card (`_nMot`),
     entao a conta roda uma vez por funcao, nao a cada desenho. */
  function _notaDoMotor(x){
    if (x._nMot !== undefined) return x._nMot;
    var v = null;
    try{
      var a = anc(x);
      var h0 = x._habs, t0 = x._tec, tn0 = x._tecNome, im0 = x.imp;
      x._habs = (a.habs || []).slice();
      x.imp = a.imp;
      delete x._tecNome;
      v = notaCfg(x, a.lvl, (a.tecb || []).slice());
      if (h0 === undefined) delete x._habs; else x._habs = h0;
      if (t0 === undefined) delete x._tec; else x._tec = t0;
      if (tn0 === undefined) delete x._tecNome; else x._tecNome = tn0;
      x.imp = im0;
      delete x._cp; delete x._n;
    }catch(e){ v = null; }
    if (v === null || isNaN(v)){
      try{ v = nota(x); }catch(e2){ v = 0; }
    }
    x._nMot = v;
    return v;
  }
  window.t6NotaDoMotor = _notaDoMotor;

  function _fnBonusPos(tipo){
    var n = _nomeFn(tipo);
    if (n === 'Atacante Infiltrador' || n === 'Atacante infiltrador') return 'Segundo atacante';
    return tipo;
  }
  function _bonusPos(x, p){
    if(!x||!p) return null;
    if(x.bonus_posicoes && x.bonus_posicoes[p]) return x.bonus_posicoes[p];
    var base=String(x.id).split('@')[0], tab=window._T6_BONUS_POS||{};
    return tab[base+'|'+_fnBonusPos(x.tipo)+'|'+p] || tab[base+'|'+x.tipo+'|'+p] || null;
  }
  function _notaDoMotorPos(x,p){
    var z=_bonusPos(x,p);
    if(z && typeof z.nota==='number') return z.nota;
    var v=_notaDoMotor(x);
    if(z && typeof z.b_total==='number') return _ajustaNotaNaPos(x,p,v);
    return v;
  }
  function _ajustaNotaNaPos(x,p,valor){
    var z=_bonusPos(x,p); if(!z||typeof z.b_total!=='number') return valor;
    var ps=_posDaFuncao(x.tipo,x), maior=null;
    ps.forEach(function(q){ var a=_bonusPos(x,q); if(a&&typeof a.b_total==='number')
      maior=maior===null?a.b_total:Math.max(maior,a.b_total); });
    return maior===null ? valor : valor + z.b_total - maior;
  }

  /* QUAL ABA DO CARD ESTA ABERTA — 'motor' (maximo), 'insumos' ou 'livre' */
  window.t6Modo = function(){
    try{
      if (window._T6ABA === 'livre' || window._T6ABA === 'motor') return window._T6ABA;
      var m = window.ENC_MODO || 'motor';
      /* Duas geracoes da casca usam nomes diferentes para a mesma aba. */
      return m === 'insumos' ? 'livre' : m;
    }catch(e){ return 'motor'; }
  };

  /* DUAS ABAS, DOIS ESTADOS. Esta fotografia nasce quando a camada atual e
     carregada, antes de qualquer edicao humana, e nunca e sobrescrita. As
     camadas antigas reutilizam `_ori`, `_anc` e fotos da build livre; essa
     sobreposicao era a origem da tela hibrida (rotulo MAXIMO + barras zero). */
  function _t6FotoMotor(c){
    if (!c) return null;
    if (!c._t6MotorOriginal){
      /* `_anc0` e criada pela camada da equacao a partir da linha gravada
         pelo motor, antes de qualquer aba/localStorage mexer no card. */
      var a0 = c._anc0;
      var sis0 = (a0 && a0.v && a0.v.length) ? a0.v : (c.sis || []);
      var sb0 = (a0 && a0.sisBar) ? a0.sisBar : (c.sisBar || []);
      var imp0 = (a0 && a0.imp !== undefined) ? a0.imp : c.imp;
      var tec0 = (a0 && a0.tecb) ? a0.tecb : (c.TECB || []);
      c._t6MotorOriginal = {
        sis:sis0.slice(),
        sisBar:sb0.map(function(r){ return r.slice(); }),
        sobra:(a0 && a0.sobra !== undefined) ? a0.sobra : c.sobra,
        imp:imp0,
        imps:(c.imps || []).map(function(x){ return {n:x.n,c:x.c,f:x.f}; }),
        tecb:tec0.slice(), b1:c.b1, b1n:c.b1n,
        rows:(c.arows || []).map(function(r){
          var v = sis0[r[0]];
          return [v, v - r[2], v];
        })
      };
    }
    return c._t6MotorOriginal;
  }
  try{ (typeof D !== 'undefined' ? D : []).forEach(function(c){
    if (c && c.id !== 'MOLDE') _t6FotoMotor(c);
  }); }catch(e){}

  window.t6RestauraMotor = function(destino){
    var c = null; try{ c = _card(destino); }catch(e){}
    var f = _t6FotoMotor(c); if (!c || !f) return false;
    c.sis = f.sis.slice();
    c.sisBar = f.sisBar.map(function(r){ return r.slice(); });
    c.sobra = f.sobra; c.imp = f.imp;
    c.imps = f.imps.map(function(x){ return {n:x.n,c:x.c,f:x.f}; });
    c.TECB = f.tecb.slice(); c.b1 = f.b1; c.b1n = f.b1n;
    (c.arows || []).forEach(function(r,i){
      if (!f.rows[i]) return;
      r[3] = f.rows[i][0]; r[4] = f.rows[i][1]; r[5] = f.rows[i][2];
    });
    try{ c.b1 = notaDe(c.sis, c.arows); }catch(e){}
    try{
      c.b1n = (function(A){ var n=0,d=0,i,w; A=A||[];
        for(i=0;i<A.length;i++){ w=A[i][1]; if(!w) continue; n+=w*A[i][3]; d+=w*A[i][2]; }
        return d ? 100*n/d : c.b1n;
      })(c.arows);
    }catch(e){}
    delete c._habs; delete c._tec; delete c._tecNome;
    delete c._cp; delete c._n; delete c._ori;
    return true;
  };

  /* 19/08 — UMA UNICA ROTA DE DESENHO DA FICHA.
     A casca historica ainda tem mais de um `abrir`/`reabrir`, pois eles
     cuidam da entrada antiga, do historico e do retorno de seguranca. Eles nao
     podem, porem, participar de cada clique interno: isso fazia uma camada
     restaurar estado que outra acabara de trocar. Daqui para baixo, barras,
     tecnico, habilidades, posicao, funcao e abas redesenham diretamente pelo
     mesmo molde e pelo mesmo ligador de eventos. */
  function t6OcultaCromoMobile(){
    if ((window.innerWidth || 9999) > 820 || !document.body) return;
    ['voltar','gbBt','t6ver','_carregando_banco'].forEach(function(id){
      var el=document.getElementById(id);
      if(el && (el.style.getPropertyValue('display')!=='none' || el.style.getPropertyPriority('display')!=='important'))
        el.style.setProperty('display','none','important');
    });
    [].slice.call(document.body.children).forEach(function(el){
      if ((el.textContent || '').trim() === '⚙ motor' &&
          (el.style.getPropertyValue('display')!=='none' || el.style.getPropertyPriority('display')!=='important'))
        el.style.setProperty('display','none','important');
    });
  }
  if (!window._T6_CROMO_OBS && typeof MutationObserver !== 'undefined'){
    window._T6_CROMO_OBS = new MutationObserver(function(){ t6OcultaCromoMobile(); });
    try{ window._T6_CROMO_OBS.observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['style']}); }catch(e){}
  }
  window.t6DesenhaFicha = function(key){
    if (!key || typeof window.t6TelaFicha !== 'function'
        || typeof window.t6FichaCliques !== 'function') return false;
    var box = document.getElementById('box');
    if (!box) return false;
    var h = window.t6TelaFicha(key);
    if (!h || String(h).replace(/<[^>]*>/g, '').trim().length < 40) return false;
    try{ if (typeof CUR !== 'undefined') CUR = key; }catch(e){}
    window._T6_CHAVE_ATUAL = String(key);
    box.innerHTML = '<div class="t6tela t6ficha">' + h + '</div>';
    try{
      [].slice.call(box.querySelectorAll('div')).forEach(function(el){
        if ((el.textContent || '').trim() !== 'HABILIDADES NATIVAS') return;
        var linha = el.nextElementSibling;
        if (linha && linha.firstElementChild) linha.firstElementChild.classList.add('t6habsnativas');
      });
    }catch(e){}
    try{
      var maximo = [].slice.call(box.querySelectorAll('span')).find(function(el){
        return (el.textContent || '').trim().indexOf('MÁXIMO POSSÍVEL') >= 0;
      });
      var modos = maximo && maximo.parentElement;
      if (modos && modos.children.length >= 5){
        modos.classList.add('t6modosmobile');
        modos.children[0].classList.add('t6modo-max');
        modos.children[1].classList.add('t6modo-build');
        modos.children[2].classList.add('t6modo-info');
        modos.children[3].classList.add('t6modo-melhora');
        modos.children[4].classList.add('t6modo-funcao');
      }
    }catch(e){}
    try{
      [].slice.call(document.body.children).forEach(function(el){
        if ((el.textContent || '').trim() === '⚙ motor') el.classList.add('t6mobilelegacy');
      });
    }catch(e){}
    window.t6FichaCliques(box, key);
    var ov = document.getElementById('ov');
    if (ov) ov.style.display = 'block';
    var vb = document.getElementById('voltar');
    if (vb) vb.style.display = 'block';
    t6OcultaCromoMobile();
    try{
      if (typeof window.t6PaginaAtiva === 'function') window.t6PaginaAtiva(key);
    }catch(e){}
    return true;
  };

  window.t6ReabreFicha = function(key){
    var sx = 0, sy = 0;
    try{ sx = window.scrollX || 0; sy = window.scrollY || 0; }catch(e){}
    try{
      if (window.t6DesenhaFicha(key)){
        /* A troca e interna a pagina. O ponto de leitura pertence ao usuario,
           nao ao componente que acabou de ser redesenhado. */
        try{ window.scrollTo(sx, sy); }catch(e){}
        try{ requestAnimationFrame(function(){ window.scrollTo(sx, sy); }); }catch(e){}
        return true;
      }
    }catch(e){
      window._T6_ERRO_DESENHO = String(key) + ' :: ' + (e && e.message || e);
    }
    /* Retorno de seguranca para uma previa antiga que ainda nao tenha todos os
       componentes da ficha nova. Nao e mais o caminho normal. */
    try{ reabrir(key); return true; }catch(e2){}
    try{ abrir(key); return true; }catch(e3){}
    return false;
  };

  /* ⛔ 19/08 — O `style-hover` DA DESIGNER NAO EXISTE NO NAVEGADOR.
     O arquivo dela usa `style-hover="..."` em 72 lugares — e a ferramenta
     dela que traduz isso para `:hover`. O navegador ignora atributo que nao
     conhece. Por isso NENHUM dos balõezinhos dos botoes `i` aparecia: o texto
     ja estava escrito, preso em `opacity:0` para sempre.
     Aqui o atributo vira comportamento de verdade, para a tela inteira —
     nao so para os `i`. Um lugar so, e todo `style-hover` dela passa a valer. */
  window.t6Hover = function(raiz){
    if (!raiz) return;
    var els = [].slice.call(raiz.querySelectorAll('[style-hover]'));
    els.forEach(function(el){
      if (el._t6hv) return;
      el._t6hv = true;
      var extra = el.getAttribute('style-hover') || '';
      var antes = el.getAttribute('style') || '';
      function entra(){ el.setAttribute('style', antes + ';' + extra); }
      function sai(){ el.setAttribute('style', antes); }
      el.addEventListener('mouseenter', entra);
      el.addEventListener('mouseleave', sai);
      /* ⛔ 19/08 — O CLIQUE E DO BOTAO, NUNCA DO BALAO.
         A primeira versao amarrava um clique em TODO elemento com
         `style-hover` — e os botoes das abas tem `style-hover`. O clique
         era engolido pelo balao (com stopPropagation) e nao chegava no
         botao: o Luis tinha que clicar duas, tres, trinta vezes.
         Agora o toque so vale para o `i` de ajuda: elemento que TEM um
         balao filho escondido e que NAO e clicavel por si. E sem
         stopPropagation nunca mais. */
      var balao = null;
      try{ balao = el.querySelector('b[style*="opacity:0"]'); }catch(e){}
      var proprio = (el.textContent || '').trim();
      if (!balao || proprio.length > 3) return;
      el.addEventListener('click', function(){
        if (el._t6on){ sai(); el._t6on = false; }
        else { entra(); el._t6on = true; }
      });
    });
  };

  /* A pagina recebe `tela_encaixe` em levas. Isso e bom para a home, mas uma
     ficha nao pode nascer pela metade: se o card foi aberto quando apenas uma
     de suas funcoes estava em D, a lateral dizia "FUNCOES QUE EXERCE - 1".
     Ao abrir a ficha, buscamos somente as linhas daquele card e incorporamos
     as que ainda faltam no MESMO array D. A chamada e deduplicada por card e,
     quando termina, a ficha aberta e redesenhada uma unica vez. */
  function _t6CompletaFuncoesDoCard(c, key){
    if (!c || typeof D === 'undefined') return;
    var base = String(c.id || '').split('@')[0];
    if (!base || !/^\d+$/.test(base)) return;
    window._T6_CARGA_CARD = window._T6_CARGA_CARD || {};
    /* `erro` nao e estado final. Antes, uma unica falha de rede deixava a
       ficha presa para sempre na unica linha que chegou pela home. */
    if (window._T6_CARGA_CARD[base] === 'carregando'
        || window._T6_CARGA_CARD[base] === 'pronto') return;
    window._T6_CARGA_CARD[base] = 'carregando';
    window._T6_BONUS_POS = window._T6_BONUS_POS || {};
    window._T6_BONUS_POS_CARGA = window._T6_BONUS_POS_CARGA || {};
    if (!window._T6_BONUS_POS_CARGA[base]){
      window._T6_BONUS_POS_CARGA[base] = 'carregando';
      var ubp = 'https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/bonus_posicao'
        + '?select=card_id,funcao,posicao,estilo_ativo,b_estilo,b_total,nota&card_id=eq.'
        + encodeURIComponent(base);
      var kbp = 'sb_publishable_XTKGboY9RyYiirPiIsWMhw_P8B51cHj';
      fetch(ubp,{headers:{apikey:kbp,Authorization:'Bearer '+kbp}})
       .then(function(r){ if(!r.ok) throw new Error('HTTP '+r.status); return r.json(); })
       .then(function(rows){
         (rows||[]).forEach(function(z){
           window._T6_BONUS_POS[z.card_id+'|'+z.funcao+'|'+z.posicao]=z;
         });
         window._T6_BONUS_POS_CARGA[base]='pronto';
         /* Nao redesenha ainda se as funcoes continuam chegando. Esse redraw
            antecipado era exatamente o flash que voltava a mostrar apenas 1. */
         if(window._T6_CARGA_CARD[base]==='pronto') try{ window.t6ReabreFicha(key); }catch(e){}
       }).catch(function(){ window._T6_BONUS_POS_CARGA[base]='erro'; });
    }
    var url = 'https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/tela_encaixe'
      + '?select=linha&card_id=eq.' + encodeURIComponent(base) + '&order=funcao.asc';
    var chave = 'sb_publishable_XTKGboY9RyYiirPiIsWMhw_P8B51cHj';
    fetch(url, {headers:{apikey:chave, Authorization:'Bearer ' + chave}})
      .then(function(r){ if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function(rows){
        var entrou = 0;
        (rows || []).forEach(function(r){
          var x = r && r.linha;
          if (!x || x.id === undefined || x.tipo === undefined) return;
          var xb = String(x.id).split('@')[0], repetida = false;
          for (var di = 0; di < D.length; di++){
            var ja = D[di];
            if (ja && ja.id !== 'MOLDE' && String(ja.id).split('@')[0] === xb
                && _mesmaFn(ja.tipo, x.tipo)){
              try{
                if(_notaDoMotor(x)>_notaDoMotor(ja)){ D[di]=x; entrou++; }
              }catch(e){}
              repetida = true; break;
            }
          }
          if (!repetida){ D.push(x); entrou++; }
        });
        window._T6_CARGA_CARD[base] = 'pronto';
        /* Redesenha mesmo quando as linhas ja estavam em D. A pagina pode ter
           sido montada durante a corrida entre as duas requisicoes. */
        if ((rows || []).length){
          try{ if (typeof _pos_D === 'function') _pos_D(); }catch(e){}
          var destinoCarga = key, abriuInicial = false;
          try{
            if (window._T6_INICIAL_CARD && window._T6_INICIAL_CARD[base]){
              var ini = _t6InicialDaPosicaoNativa(c);
              if (ini) destinoCarga = ini.id + '|' + ini.tipo;
              delete window._T6_INICIAL_CARD[base];
              abriuInicial = !!ini;
            }
          }catch(e){}
          try{
            if(abriuInicial && typeof window.t6AbreFuncao==='function') window.t6AbreFuncao(destinoCarga);
            else window.t6ReabreFicha(destinoCarga);
          }catch(e){ try{ abrir(destinoCarga); }catch(e2){} }
        }
      })
      .catch(function(){
        window._T6_CARGA_CARD[base] = 'erro';
        window._T6_CARGA_TENTATIVA = window._T6_CARGA_TENTATIVA || {};
        var n=(window._T6_CARGA_TENTATIVA[base]||0)+1;
        window._T6_CARGA_TENTATIVA[base]=n;
        if(n<3) setTimeout(function(){ _t6CompletaFuncoesDoCard(c,key); },350*n);
      });
  }

  /* Uma mesma linha pode chegar pela leva inicial, pela carga em segundo plano
     e pela busca pontual da ficha. O identificador pode ganhar um sufixo `@`,
     portanto a identidade real aqui e card-base + funcao equivalente. */
  function _t6IrmasUnicas(c){
    var base = String(c.id).split('@')[0], out = [];
    for (var i = 0; i < D.length; i++){
      var x = D[i];
      if (!x || x.id === 'MOLDE' || String(x.id).split('@')[0] !== base) continue;
      var existe = false;
      for (var j = 0; j < out.length; j++){
        if (_mesmaFn(out[j].tipo, x.tipo) || _nomeFn(out[j].tipo) === _nomeFn(x.tipo)){
          /* Linha antiga e linha renomeada podem coexistir no banco. Para a
             mesma funcao exibida, conserva deterministicamente a de maior
             nota do motor — nunca a que chegou primeiro pela paginacao. */
          try{ if(_notaDoMotor(x)>_notaDoMotor(out[j])) out[j]=x; }catch(e){}
          existe = true; break;
        }
      }
      if (!existe) out.push(x);
    }
    return out.length ? out : [c];
  }

  /* A primeira funcao da pagina e a MAIS FORTE entre as que correspondem a
     posicao nativa do card. A busca pode ter sido aberta por qualquer linha;
     ela nao decide a funcao inicial. */
  function _t6InicialDaPosicaoNativa(c){
    if(!c) return null;
    var nat=c.np||'';
    try{ if(typeof npFixo==='function') nat=npFixo(c)||nat; }catch(e){}
    var irm=_t6IrmasUnicas(c), candidatas=[];
    for(var i=0;i<irm.length;i++){
      var ps=_posDaFuncao(irm[i].tipo,c);
      if(!ps.length) ps=_posFn(irm[i]);
      if(ps.indexOf(nat)>=0) candidatas.push(irm[i]);
    }
    if(!candidatas.length) return null;
    candidatas.sort(function(a,b){ return _notaDoMotor(b)-_notaDoMotor(a); });
    return candidatas[0];
  }
  window.t6InicialDaPosicaoNativa=_t6InicialDaPosicaoNativa;

  window.t6TelaFicha = function(key){
    if (!M || !M.ficha || !M.ficha.corpo) return '';
    var c = null;
    try{ c = _card(key); }catch(e){}
    if (!c || !c.arows) return '';
    var lvl = {}, ET = null, ETN = null, ST = null;
    try{ lvl = _lvlDe(c) || {}; }catch(e){}
    try{ ET  = c.base ? etapas(c, lvl) : null; }catch(e){}
    try{ ETN = c.base ? _e4nat(c, lvl) : null; }catch(e){}
    try{ ST  = c.base ? _startDe(c) : null; }catch(e){}
    try{ _t6CompletaFuncoesDoCard(c, key); }catch(e){}

    /* ---------- o campinho (3 por linha, como ela desenhou) ---------- */
    var np = c.np || '', minhas = [];
    try{ if (typeof npFixo === 'function') np = npFixo(c) || np; }catch(e){}
    try{ (c.sp || []).forEach(function(x){ if (minhas.indexOf(x[0]) < 0) minhas.push(x[0]); }); }catch(e){}
    if (np && minhas.indexOf(np) < 0) minhas.unshift(np);
    /* ⛔ `sig`, `nomeP` e `CAMPO` moram dentro de um IIFE da casca — nao sao
       globais. Entao o campinho sai das tabelas que SAO globais (SIGJ/POSN), e
       a grade de posicoes fica aqui, escrita uma vez so. */
    function _sig(p){
      try{ if (typeof SIGJ !== 'undefined' && SIGJ[p]) return SIGJ[p]; }catch(e){}
      return p;
    }
    function _nomeP(p){
      try{ if (typeof POSN !== 'undefined' && POSN[p]) return POSN[p]; }catch(e){}
      return p;
    }
    /* ⛔ 19/08 — OS QUATRO ESTADOS, COM CONTRASTE DE VERDADE.
       A legenda do proprio `i` do bloco ja dizia tres coisas diferentes, mas o
       desenho so distinguia duas — e mal. Ordem do Luis, 19/08: "o contraste
       das posicoes que ele pode ocupar com as que nao pode esta muito pouco".
         1. A POSICAO DESTA FICHA .. preenchida, verde forte, com brilho
         2. POSICAO DE FABRICA .... contorno verde grosso, fundo apagado
         3. SEGUNDA POSICAO ....... fundo azulado, contorno visivel
         4. NAO PODE OCUPAR ....... quase apagada, sem contorno
       Sao quatro degraus de brilho, nao dois de 1px. */
    /* a posicao selecionada no campinho — o `_SELPOS` da casca antiga */
    var _sel = null, _funcsSel = null;
    try{
      var _baseFicha = String(c.id).split('@')[0];
      var _selGuardada = (window._T6SELPOS_CARD === _baseFicha)
        ? (window._T6PENDENTE_POS || window._T6SELPOS_FORCADA || window._SELPOS)
        : window._SELPOS;
      if (_selGuardada && _minhasDe(c).indexOf(_selGuardada) >= 0) _sel = _selGuardada;
    }catch(e){}

    /* ⛔ 19/08 — OS ESTADOS DO CAMPINHO, E A LEITURA ANTES DA COR.
       Ordem do Luis: as cores estavam certas mas o TEXTO ficou ilegivel —
       claro sobre claro na acesa, apagado demais na que ele nao ocupa.
       Cada estado agora tem cor de letra escolhida contra o proprio fundo.
         ACESA ...... a posicao desta funcao (ou a que ele clicou)
         NATIVA ..... de fabrica
         COMPRADA ... segunda posicao
         FORA ....... ele nao ocupa: legivel, so sem destaque */
    var CX = (typeof CAMPO !== 'undefined') ? CAMPO : window.T6_CAMPO;
    var _acesas = _sel ? [_sel] : _posDaFuncao(c.tipo, c);
    var _segundas = [];
    try{ (c.sp || []).forEach(function(x){ if (x && x[0] !== np) _segundas.push(x[0]); }); }catch(e){}
    var campo = CX.map(function(linha){
      return {cells: linha.map(function(p){
        if (!p) return {n: '', p: '', st: 'display:block;height:32px'};
        var acesa = (_acesas.indexOf(p) >= 0),
            eNat  = (p === np),
            eSeg  = (_segundas.indexOf(p) >= 0),
            pode  = eNat || eSeg || (minhas.indexOf(p) >= 0);
        var fundo, borda, cor, extra = '';
        if (acesa){
          fundo = 'linear-gradient(180deg,#8df3ae,#4fd98a)';
          borda = '2px solid #ffffff';
          cor   = '#06200f';
          extra = ';box-shadow:0 0 0 3px rgba(255,255,255,.28),0 6px 14px rgba(0,0,0,.35);font-size:11.5px';
        /* Ao clicar numa POSICAO, somente ela fica acesa. A nativa e as
           compradas continuam clicaveis, mas perdem todo destaque enquanto
           a escolha por posicao estiver ativa. Clique em FUNCAO limpa `_sel`
           e volta a acender todas as posicoes relacionadas aquela funcao. */
        } else if (_sel){
          fundo = 'rgba(0,0,0,.20)';
          borda = '1px solid rgba(255,255,255,.20)';
          cor   = pode ? '#c7d8cd' : '#819187';
        } else if (eNat){
          fundo = 'rgba(255,255,255,.10)';
          borda = '2px solid #ffd75e';
          cor   = '#ffeaa8';
        } else if (eSeg || pode){
          fundo = 'rgba(255,255,255,.16)';
          borda = '1px solid rgba(255,255,255,.42)';
          cor   = '#ffffff';
        } else {
          fundo = 'rgba(0,0,0,.16)';
          borda = '1px solid rgba(255,255,255,.13)';
          cor   = '#b9cfc0';
        }
        if (pode) extra += ';cursor:pointer';
        return {n: esc(_sig(p)), p: esc(pode ? p : ''),
          e: acesa ? 'acesa' : (eNat ? 'nativa' : ((eSeg || pode) ? 'pode' : 'fora')),
          st: 'display:flex;align-items:center;justify-content:center;height:32px;'
            + 'font-family:inherit;font-size:10.5px;font-weight:800;letter-spacing:.3px;'
            + 'border-radius:7px;background:' + fundo
            + ';border:' + borda + ';color:' + cor + extra};
      })};
    });

    /* ---------- as funcoes que ele exerce ---------- */
    var base = String(c.id).split('@')[0], irm = [];
    try{
      irm = _t6IrmasUnicas(c);
      irm.forEach(function(x){ _notaDoMotor(x); });
      irm.sort(function(a, b){ return b._nMot - a._nMot; });
    }catch(e){ irm = [c]; }
    if (_sel) _funcsSel = _funcsDaPos(_sel, c, irm);

    var fnsW = irm.map(function(x, i){
      var g = (irm.length > 1) ? (1 - i / (irm.length - 1)) : 1;
      /* Enquanto uma posicao com varias funcoes aguarda escolha, nenhuma
         funcao fica marcada. A build antiga continua apenas como fundo; ela
         nao pode parecer a resposta da nova posicao. */
      var aqui = (x.tipo === c.tipo && !window._T6PENDENTE_POS);
      /* Clicar numa posicao com varias funcoes NAO seleciona todas elas.
         A build que esta por tras continua sendo a funcao anteriormente
         aberta ate a escolha obrigatoria na tampa. */
      /* BÁSICO so quando se MEDIU que o estilo nao liga. `null` = nao sei,
         e nao sei nao vira etiqueta. (Antes, todo nome renomeado caia aqui.) */
      var posicoesFn = _posDaFuncao(x.tipo, c);
      if (!posicoesFn.length) posicoesFn = _posFn(x);
      var estadosEstilo = posicoesFn.map(function(p){ return _estiloLigaNaPos(x, p); });
      var conhecidos = estadosEstilo.filter(function(v){ return v !== null; });
      /* BÁSICO e uma ETIQUETA da funcao, nunca um texto dentro do botao da
         posicao. Se ao menos uma das posicoes nao ativa o estilo, a etiqueta
         aparece uma vez na coluna propria. "COM ESTILO" nao existe na ficha. */
      var bas = conhecidos.length > 0 && conhecidos.every(function(v){ return v === false; });
      /* a sigla e a posicao que ESTE card exerce nesta funcao */
      var sg = _sigFn(x, c);
      return {n: esc(_nomeFn(x.tipo)),
        /* ⛔ 19/08 — QUATRO COLUNAS DE LARGURA FIXA.
           Sem isso o nome comprido quebra em duas linhas e a lista inteira
           desalinha — foi o que aconteceu com "Centroavante fixo". O nome
           ocupa o que sobra e corta com reticencias; as outras tres nao
           encolhem nunca. */
        /* ⛔ 19/08 — O NOME NAO SE CORTA. Ordem do Luis: "voce escondeu a
           informacao mais importante, que e o nome da funcao". Cortar com
           reticencias resolvia o desalinho e criava um pior: "Zagueiro ..."
           nao diz se e de saida ou de combate. Agora o nome quebra em duas
           linhas quando precisar, e as outras tres colunas e que nao mexem. */
        nSt: 'flex:1 1 auto;min-width:0;text-align:left;line-height:1.2;'
           + 'white-space:normal;overflow-wrap:normal;word-break:normal;hyphens:none',
        bas: bas ? 'BÁSICO' : '',
        basSt: bas ? 'font-family:inherit;font-size:8px;font-weight:800;letter-spacing:.6px;padding:2px 6px;border-radius:4px;background:var(--d14);border:1px solid var(--d31);color:var(--d17);flex:0 0 auto' : 'display:none',
        /* ⛔ a coluna da posicao fica NO MEIO da linha, centralizada — nao
           colada na nota. Ordem do Luis, 19/08. */
        /* ⛔ 19/08 — UMA SIGLA POR BOTAO, EMPILHADOS.
           Ordem do Luis: "coloca CA/SA em dois botoes, um embaixo do outro".
           O `pos` deixa de ser texto e vira marcacao — por isso o molde
           precisa imprimir sem escapar (o `tpl` ja aceita, e o conteudo e
           gerado aqui, nao vem de fora). */
        pos: posicoesFn.map(function(p){
          var g = _sigla(p);
          return '<button type="button" data-fnpos="' + esc(p)
               + '" data-fnkey="' + esc(x.id+'|'+x.tipo)
               + '" style="display:block;width:100%;font-family:inherit;font-size:9px;'
               + 'font-weight:800;letter-spacing:.4px;padding:2px 0;border-radius:5px;'
               + 'text-align:center;border:0;background:'
               + (aqui ? 'rgba(255,255,255,.14)' : 'var(--d14)')
               + ';color:' + (aqui ? 'var(--d117)' : 'var(--d45)') + '">'
               + esc(g) + '</button>';
        }).join(''),
        /* A posicao e somente uma etiqueta curta. A nota pertence a funcao e
           aparece uma unica vez na ultima coluna; BÁSICO tem coluna propria. */
        posSt: 'display:flex;flex-direction:column;gap:3px;flex:0 0 52px',
        /* ⛔ TODA pontuacao do site tem DUAS casas. Ordem do Luis, 19/08. */
        pts: n2((window._T6SELPOS_FORCADA && posicoesFn.indexOf(window._T6SELPOS_FORCADA)>=0)
                ? _notaDoMotorPos(x,window._T6SELPOS_FORCADA) : _notaDoMotor(x)),
        num: 'font-family:inherit;font-size:14px;font-weight:800;flex:0 0 58px;text-align:right;color:'
           + (aqui ? 'var(--d117)' : 'var(--d1)'),
        /* ⛔ o contraste era 1px de borda e um fundo que so contava o ranking.
           Agora a selecionada usa a MESMA cor da etiqueta do topo direito
           (ordem do Luis, 19/08), e as outras escurecem pelo ranking. */
        /* ⛔ a funcao ABERTA usa a MESMA ROUPA da etiqueta do topo direito —
           o mesmo roxo, a mesma borda, a mesma letra. Ordem do Luis, 19/08:
           "pra ela estar na cor roxa igual o outro". Os tokens sao os mesmos
           que o molde da designer usa naquela etiqueta: d114/d115/d116/d117. */
        row: 'display:flex;align-items:center;gap:6px;font-size:12.5px;font-weight:700;'
           + 'height:54px;min-height:54px;max-height:54px;box-sizing:border-box;'
           + 'padding:6px 10px;border-radius:9px;cursor:pointer;transition:all .16s ease;'
           + (aqui
              ? 'background:linear-gradient(180deg,var(--d114),var(--d115));'
                 + 'border:1px solid var(--d116);color:var(--d117)'
              : 'background:rgba(38,184,112,' + (0.10 + 0.34 * g).toFixed(3) + ');'
                + 'border:1px solid rgba(90,226,153,' + (0.20 + 0.48 * g).toFixed(3) + ');'
                + 'color:var(--d8)'),
        k: esc(x.id + '|' + x.tipo)};
    });

    /* Falso Nove e a excecao em que a MESMA funcao muda de resultado conforme
       a posicao: em CA o estilo nao liga (BASICO), em SA ele liga. Uma linha
       unica escondia essa diferenca e ainda mostrava a nota maior nas duas.
       A ficha passa a ter duas escolhas independentes, cada uma com sua nota. */
    var fnsSeparadas = [];
    fnsW.forEach(function(r, i){
      var x = irm[i], ps = _posDaFuncao(x.tipo, c);
      if (!ps.length) ps = _posFn(x);
      var mistas = ps.length > 1
        && ps.some(function(p){ return _estiloLigaNaPos(x,p) === false; })
        && ps.some(function(p){ return _estiloLigaNaPos(x,p) === true; });
      if (_nomeFn(x.tipo) !== 'Falso Nove' || !mistas){
        r.fp = '';
        fnsSeparadas.push(r);
        return;
      }
      ps.forEach(function(p){
        var z = _bonusPos(x,p);
        if (!z) return;
        var nr = {};
        Object.keys(r).forEach(function(k){ nr[k] = r[k]; });
        var basPos = z.estilo_ativo === false;
        var escolhida = window._T6PENDENTE_POS ? null : (window._T6SELPOS_FORCADA
          || x.posicao_da_nota || (x.bonus_posicoes && x.bonus_posicoes.SA ? 'SA' : p));
        var ativaVar = (x.tipo === c.tipo && escolhida === p);
        var gi = (irm.length > 1) ? (1 - i / (irm.length - 1)) : 1;
        /* A posicao ja aparece na etiqueta propria; repeti-la no nome deixa
           "Falso Nove CA · CA" e nao acrescenta informacao. */
        nr.n = esc('Falso Nove');
        nr.bas = basPos ? 'BÁSICO' : '';
        /* A excecao CA/SA usa exatamente a mesma etiqueta BÁSICO das demais
           funcoes. Antes ela herdava `display:none` da linha mista e acabava
           aparecendo como texto solto, parecendo outra categoria. */
        nr.basSt = basPos
          ? 'font-family:inherit;font-size:8px;font-weight:800;letter-spacing:.6px;padding:2px 6px;border-radius:4px;background:var(--d14);border:1px solid var(--d31);color:var(--d17);flex:0 0 auto'
          : 'display:none';
        nr.pos = '<span style="display:block;width:100%;font-family:inherit;font-size:9px;'
          + 'font-weight:800;letter-spacing:.4px;padding:2px 0;border-radius:5px;text-align:center;'
          + 'background:' + (ativaVar ? 'rgba(255,255,255,.14)' : 'var(--d14)')
          + ';color:' + (ativaVar ? 'var(--d117)' : 'var(--d45)') + '">'
          + esc(_sigla(p)) + '</span>';
        nr.pts = n2(_notaDoMotorPos(x,p));
        nr.num = 'font-family:inherit;font-size:14px;font-weight:800;flex:0 0 58px;text-align:right;color:'
          + (ativaVar ? 'var(--d117)' : 'var(--d1)');
        nr.row = 'display:flex;align-items:center;gap:6px;font-size:12.5px;font-weight:700;'
          + 'height:54px;min-height:54px;max-height:54px;box-sizing:border-box;'
          + 'padding:6px 10px;border-radius:9px;cursor:pointer;transition:all .16s ease;'
          + (ativaVar
            ? 'background:linear-gradient(180deg,var(--d114),var(--d115));border:1px solid var(--d116);color:var(--d117)'
            : 'background:rgba(38,184,112,' + (0.10 + 0.34 * gi).toFixed(3) + ');border:1px solid rgba(90,226,153,' + (0.20 + 0.48 * gi).toFixed(3) + ');color:var(--d8)');
        nr.fp = esc(p);
        fnsSeparadas.push(nr);
      });
    });
    fnsW = fnsSeparadas;
    /* A divisao CA/SA acontece depois da ordenacao das funcoes originais.
       Reordena as linhas finais para a nota maior continuar sempre acima. */
    fnsW.sort(function(a,b){ return parseFloat(b.pts)-parseFloat(a.pts); });

    /* O seletor de uma posicao com varias funcoes nasce junto com o HTML.
       Assim ele nao depende de uma insercao tardia que o molde possa apagar. */
    var escolhaPosHtml = '';
    /* O seletor existe somente enquanto a posicao aguarda escolha. Depois de
       escolher Ala Cruzador/Finalizador, a posicao continua acesa, mas a
       tampa precisa sumir para liberar os demais botoes. */
    if (window._T6PENDENTE_POS && _sel && _funcsSel && _funcsSel.length > 1){
      var opHtml = '';
      _funcsSel.forEach(function(f){
        var al = null;
        for (var ei = 0; ei < irm.length; ei++) if (_mesmaFn(irm[ei].tipo, f)){ al = irm[ei]; break; }
        if (!al) return;
        var psEscolha = _posDaFuncao(al.tipo, c);
        if (!psEscolha.length) psEscolha = _posFn(al);
        var basEscolhaTem = _sel
          ? (_estiloLigaNaPos(al,_sel) === false)
          : psEscolha.some(function(p){ return _estiloLigaNaPos(al,p) === false; });
        var basEscolha = basEscolhaTem
          ? '<small style="font-family:inherit;font-size:8px;font-weight:800;letter-spacing:.6px;'
            + 'padding:2px 6px;border-radius:4px;background:var(--d14);border:1px solid var(--d31);'
            + 'color:var(--d17)">BÁSICO</small>' : '';
        opHtml += '<button data-t6pickfn="' + esc(al.id + '|' + al.tipo) + '" style="'
          + 'display:flex;align-items:center;justify-content:space-between;gap:10px;'
          + 'font-family:inherit;font-size:12px;font-weight:700;padding:10px 12px;'
          + 'border-radius:9px;cursor:pointer;background:var(--d14);'
          + 'border:1px solid var(--d31);color:var(--d1)">'
          + '<span style="display:flex;align-items:center;gap:7px">'
          + '<span>' + esc(_nomeFn(al.tipo)) + '</span>' + basEscolha
          + '</span><b style="color:var(--d25)">'
          + n2(_sel ? _notaDoMotorPos(al,_sel) : _notaDoMotor(al)) + '</b></button>';
      });
      escolhaPosHtml = '<div data-t6pede="1" style="position:relative;z-index:9;width:100%;'
        + 'padding:15px;margin:0 0 10px;border-radius:12px;display:flex;flex-direction:column;gap:9px;'
        + 'background:#08120d;border:1.5px solid var(--d25);box-shadow:0 10px 26px var(--d104)">'
        + '<b style="font-size:12px;letter-spacing:.5px;color:var(--d25)">ESCOLHA A FUNÇÃO PARA '
        + esc(_sig(_sel)) + '</b><span style="font-size:12px;color:var(--d30)">'
        + 'Cada função tem uma build diferente. Selecione qual você quer abrir:</span>'
        + '<div style="display:flex;flex-direction:column;gap:7px">' + opHtml + '</div></div>';
    }

    /* ---------- as barras ---------- */
    function custo(n){ var t = 0; for (var k = 1; k <= n; k++) t += Math.ceil(k / 4); return t; }
    var chaves = []; try{ chaves = MBK.slice(); }catch(e){}
    var barsFull = chaves.map(function(b){
      var v = lvl[b] || 0;
      return {n: esc((typeof MBN !== 'undefined' && MBN[b]) || b), v: v,
              pts: custo(v), w: Math.round(v * 100 / 25) + '%', b: esc(b)};
    });
    var gasto = 0; try{ gasto = gastoDe(lvl); }catch(e){}
    var orc = c.orc || 0, niv = 0;
    for (var kk in lvl) niv += (lvl[kk] || 0);

    /* ---------- atributos ---------- */
    var GRUPOS = [['ATAQUE', [0,1,2,3,4,5,6,7,8,9]], ['ATLETISMO', [10,11,12,13,14,15,16]],
                  ['DEFESA', [17,18,19,20]], ['GOLEIRO', [21,22,23,24,25]]];
    function linhaAttr(r){
      var i = r[0], p = r[1], cl = CLS_F[p] || CLS_F[0];
      var e = ET ? ET[i] : null, nv = ETN ? ETN[i] : null, jogo = r[3];
      var pt = 0; try{ pt = ptsAttr(r); }catch(e2){}
      return {n: esc(ATTRS[i]),
        nSt: 'font-size:11.5px;color:' + (p ? 'var(--d1)' : 'var(--d16)') + (p >= 6 ? ';font-weight:700' : ''),
        cls: cl[0], clsSt: _stCls(p),
        base: e ? e[0] : (ST ? (ST[i] || 0) : jogo),
        bar: e ? _sn(e[1] - e[0]) : '—', barSt: e ? _stNum(e[1] - e[0]) : _stNum(0),
        imp: e ? _sn(e[2] - e[1]) : '—', impSt: e ? _stNum(e[2] - e[1]) : _stNum(0),
        tec: e ? _sn(e[3] - e[2]) : '—', tecSt: e ? _stNum(e[3] - e[2]) : _stNum(0),
        tela: e ? e[3] : jogo,
        hn: (e && nv !== null && nv !== undefined) ? _sn(nv - e[3]) : '—',
        hnSt: (e && nv !== null && nv !== undefined) ? _stNum(nv - e[3]) : _stNum(0),
        ha: (e && nv !== null && nv !== undefined) ? _sn(e[4] - nv) : '—',
        haSt: (e && nv !== null && nv !== undefined) ? _stNum(e[4] - nv) : _stNum(0),
        total: jogo, alvo: r[2],
        vs: _sn(r[4]), vsSt: _stNum(r[4]),
        pts: p ? _sn(pt, 1) : '0.0',
        ptsSt: 'font-family:inherit;font-size:11.5px;font-weight:700;text-align:right;color:'
             + (p ? (pt >= 0 ? C_MAIS : C_MENOS) : 'var(--d16)')};
    }
    function secao(f){
      return GRUPOS.map(function(g){
        var rows = (c.arows || []).filter(function(r){
          return g[1].indexOf(r[0]) >= 0 && f(r); }).map(linhaAttr);
        return rows.length ? {g: g[0], rows: rows} : null;
      }).filter(Boolean);
    }
    var atributos = secao(function(r){ return r[1] > 0; });
    var indiferentes = secao(function(r){ return !r[1]; });
    var nInd = (c.arows || []).filter(function(r){ return !r[1]; }).length;

    /* ---------- medidas do corpo, em duas colunas legiveis ---------- */
    /* ⛔ 19/08 — AS MEDIDAS DO CORPO VINHAM VAZIAS.
       O gerador manda `frows: []` sempre — e por isso o bloco mostrava
       `soma 0 · peso 0 · 0%`. Ordem do Luis: *"as medidas do corpo saem do
       motor de bonus e sao gravadas no supabase"*. Estavam: o `CORPO_MOTOR`
       traz os numeros medidos de cada carta e o `CORPO_MOLDE` (novo) traz o
       molde de cada funcao. A conta e a MESMA do motor_bonus. Se por algum
       motivo isso faltar, cai no `frows` e depois no `_pos_D` da casca —
       nunca fica em branco sem dizer por que. */
    var _fr0 = (c.frows && c.frows.length) ? c.frows : null;
    if (!_fr0){ try{ _fr0 = corpoLinhas(c); }catch(e){ _fr0 = null; } }
    if (!_fr0 || !_fr0.length){
      try{ if (typeof _pos_D === 'function' && !window._t6posD){ window._t6posD = 1; _pos_D(); } }catch(e){}
      _fr0 = c.frows || [];
    }
    /* Ordem anatomica: leitura de cima para baixo, mantendo pares juntos. */
    var ordemCorpo = {
      'Altura':0, 'Compr. pescoço':1, 'Tam. pescoço':2,
      'Alt. ombro':3, 'Larg. ombro':4, 'Peito':5,
      'Compr. braço':6, 'Tam. braço':7, 'Cintura':8,
      'Coxa':9, 'Compr. perna':10, 'Panturrilha':11
    };
    var fr = _fr0.slice().sort(function(a, b){
      var an = String(a[0]).replace(/ p\d+$/, '');
      var bn = String(b[0]).replace(/ p\d+$/, '');
      return (ordemCorpo[an] === undefined ? 99 : ordemCorpo[an])
           - (ordemCorpo[bn] === undefined ? 99 : ordemCorpo[bn]);
    });
    var corpoSoma = fr.reduce(function(a, r){ return a + (+r[6] || 0); }, 0);
    var corpoTeto = fr.reduce(function(a, r){
      return a + ((+r[5] || 0) ? ((+r[1] || 0) * 2) : 0); }, 0) || 1;
    var corpoPct = Math.max(-100, Math.min(100, corpoSoma / corpoTeto * 100));
    var corpoImpacto = corpoPct / 100 * 1.5;
    var nomesCorpo = {
      'Tam. braço':'Tamanho do braço',
      'Tam. pescoço':'Tamanho do pescoço',
      'Compr. perna':'Comprimento da perna',
      'Compr. braço':'Comprimento do braço',
      'Compr. pescoço':'Comprimento do pescoço',
      'Larg. ombro':'Largura dos ombros',
      'Alt. ombro':'Altura dos ombros'
    };
    var porCol = Math.ceil(fr.length / 2) || 1, medidas = [];
    for (var q = 0; q < fr.length; q += porCol){
      medidas.push(fr.slice(q, q + porCol).map(function(r){
        var pts = r[6] || 0, nt = r[4] || 0;
        var nomeCorpo = String(r[0]).replace(/ p\d+$/, '');
        return {n: esc(nomesCorpo[nomeCorpo] || nomeCorpo), p: '',
          nota: nt ? _sn(nt) : '0',
          notaSt: 'font-family:inherit;font-size:10.5px;text-align:center;color:'
                + (nt > 0 ? C_MAIS : (nt < 0 ? C_MENOS : C_ZERO)),
          card: r[3], ref: r[2], pontos: _sn(pts, 2),
          pontosSt: 'font-family:inherit;font-size:10.5px;font-weight:700;text-align:right;color:'
                  + (pts > 0 ? C_MAIS : (pts < 0 ? C_MENOS : C_ZERO))};
      }));
    }

    var dados = {campo: campo, fnsW: fnsW, barsFull: barsFull, atributos: atributos,
      indiferentes: indiferentes, medidas: medidas,
      colsAttr: ['Atributo','Classe','Base','+barras','+ímpeto','+técnico','Na tela',
                 '+hab. nativas','+hab. adicionadas','Total','Alvo','vs alvo','Pontos']};

    /* os data- entram ANTES de preencher — unico acrescimo a marcacao dela */
    var molde = M.ficha.corpo
      .replace('<div style="{{ f.row }}"', '<div data-fn="{{ f.k }}" data-fnvariant="{{ f.fp }}" style="{{ f.row }}"')
      .replace('<span>{{ f.n }}</span>', '<span style="{{ f.nSt }}">{{ f.n }}</span>')
      .replace('<span style="{{ c.st }}">{{ c.n }}</span>',
               '<span data-pos="{{ c.p }}" data-campo="{{ c.e }}" style="{{ c.st }}">{{ c.n }}</span>')
      .replace('<span style="font-family:inherit;font-size:13px;font-weight:800;padding:3px 9px;border-radius:7px;background:linear-gradient(180deg,var(--d105),var(--d106));border:1px solid var(--d107);color:var(--d45)">PD</span>',
               '<span class="t6posnativa" style="font-family:inherit;font-size:13px;font-weight:800;padding:3px 9px;border-radius:7px;background:linear-gradient(180deg,var(--d105),var(--d106));border:1px solid var(--d107);color:var(--d45)">PD</span>')
      .replace('<span style="font-size:11.5px;color:var(--d30)">{{ m.n }} ',
               '<span style="font-size:11.5px;color:var(--d30);white-space:nowrap">{{ m.n }} ')
      .replace('<div style="display:grid;grid-template-columns:minmax(0,1fr) 54px 38px 44px 48px;gap:6px;padding:0 4px 5px;border-bottom:1px solid var(--d33)">',
               '<div class="t6medhead" style="display:grid;grid-template-columns:minmax(150px,1fr) 52px 62px;gap:8px;padding:0 6px 7px;border-bottom:1px solid var(--d33)">')
      .replace('<div style="display:grid;grid-template-columns:minmax(0,1fr) 54px 38px 44px 48px;gap:6px;align-items:center;padding:4px;border-radius:6px;transition:background .16s ease"',
               '<div class="t6medrow" style="display:grid;grid-template-columns:minmax(150px,1fr) 52px 62px;gap:8px;align-items:center;padding:7px 6px;border-radius:6px;transition:background .16s ease"')
      .replace('<span style="height:8px;border-radius:5px;background:var(--d10);display:block;overflow:hidden;position:relative">',
               '<span data-trilha="{{ b.b }}" style="height:8px;border-radius:5px;background:var(--d10);display:block;overflow:hidden;position:relative">')
      .replace('">−</i>', '" data-bar="{{ b.b }}" data-d="-1">−</i>')
      .replace('">+</i>', '" data-bar="{{ b.b }}" data-d="1">+</i>');
    var h = tpl(molde, dados);
    h = h.replace(/<div style="display:grid;grid-template-columns:130px 88px repeat\(11,minmax\(0,1fr\)\);/g,
                  '<div class="t6attrgrid" style="display:grid;grid-template-columns:130px 88px repeat(11,minmax(0,1fr));');
    if (escolhaPosHtml){
      var priFn = h.indexOf('<div data-fn=');
      if (priFn >= 0) h = h.slice(0, priFn) + escolhaPosHtml + h.slice(priFn);
    }

    /* ---------- os textos que sao dado nosso ---------- */
    var nt = 0, tp = 0, pc = 0;
    try{
      nt = nota(c);
      /* So uma variante JA ESCOLHIDA altera a nota. `_SELPOS` tambem e usada
         enquanto o seletor esta aberto; usa-la aqui misturava MLD pendente
         com a build anterior de Atacante Infiltrador. */
      var posNota=window._T6PENDENTE_POS ? null : window._T6SELPOS_FORCADA;
      if(posNota) nt=_ajustaNotaNaPos(c,posNota,nt);
      tp = topoDoTipo(c.tipo); pc = tp > 0 ? 100 * nt / tp : 0;
    }catch(e){}
    function sub(de, para){ h = h.split(de).join(para); }
    /* O bloco de corpo mostrava nomes de implementacao (`p0`, `p1`, `p5`) e
       cabecalhos curtos demais para explicar a conta. Esses pesos continuam na
       matematica do motor, mas nao sao informacao util para o leitor. */
    sub('>Nota da medida<', '>Avaliação<');
    sub('>No card<', '>No card<');
    sub('>Alvo<', '>Ideal<');
    sub('>Pontos<', '>Na nota<');
    /* O molde tinha tres tabelas estreitas. Os nomes completos quebravam em
       duas ou tres linhas e pareciam dados diferentes. Duas colunas deixam a
       leitura horizontal e mantêm cada medida inteira. */
    sub('grid-template-columns:repeat(3,minmax(0,1fr));gap:14px',
        'grid-template-columns:repeat(2,minmax(0,1fr));gap:16px');
    h += '<style>'
      + '.t6medhead>:nth-child(2),.t6medhead>:nth-child(4),'
      + '.t6medrow>:nth-child(2),.t6medrow>:nth-child(4){display:none!important}'
      + '.t6medhead>:nth-child(3),.t6medrow>:nth-child(3){grid-column:2}'
      + '.t6medhead>:nth-child(5),.t6medrow>:nth-child(5){grid-column:3}'
      + '</style>';
    sub('>Lionel Messi<', '>' + esc(c.nome) + '<');
    sub('>PD<', '>' + esc(_sig(np) || '—') + '<');
    sub('>Ponta direita<', '>' + esc(_nomeP(np) || '—') + '<');
    sub('>Armador criativo<', '>' + esc(_extenso(c.modelo) || _nomeFn(c.tipo) || '') + '<');
    /* ⛔ 19/08 — A DATA NAO E DE LANCAMENTO. Ela sai do `c.dt`, que o
       unificar_base enche a partir do box_por_card.json: e a data da BOX em
       que a carta apareceu. A coluna do banco se chama `data_lancamento`, o
       que enganou por semanas. Enquanto nao houver a data real da Konami, a
       tela diz o que o numero E, em vez de mentir o que ele nao e. */
    sub('>24/06/2026<', '>' + (c.dt
        ? 'box · ' + esc(c.dt.split('-').reverse().join('/'))
        : 'sem data de box') + '<');
    /* ⛔ o MAXIMO KONAMI vem do `max_ovr` do efHub. O `maxOvr` que estava aqui
       e a pontuacao que a TELA ANTIGA mostrava (por isso saia quebrado, tipo
       100.18, quando OVR da Konami e sempre inteiro). O gerador ja foi
       corrigido para preferir o max_ovr; aqui fica a rede: numero quebrado
       nao e OVR, entao nao se mostra como se fosse. */
    sub('>92<', '>' + (c.ovr || '—') + '<');
    var _mx = c.maxOvr || c.sisOvr || 0;
    sub('>104.20<', '>' + ((_mx && Math.abs(_mx - Math.round(_mx)) < 0.001)
        ? Math.round(_mx) : (c.ovr || '—')) + '<');
    sub('>112.26<', '>' + n2(nt) + '<');
    sub('>100.00%<', '>' + n2(pc) + '%<');
    /* ⛔ 19/08 — o rotulo era o SETOR ("ATAQUE"), que a coluna da esquerda ja
       diz. Ordem do Luis: aqui vai a posicao nativa, com o nome escrito. */
    sub('ATACANTE <b', 'POSIÇÃO NATIVA: <b');
    sub('FUNÇÕES QUE EXERCE · 8', 'FUNÇÕES QUE EXERCE · ' + fnsW.length);
    sub('Ala finalizador <b', esc(_nomeFn(c.tipo)) + ' <b');
    sub('>112.3<', '>' + n2(nt) + '<');
    sub('>30</b>', '>' + niv + '</b>');
    sub('>58/58<', '>' + gasto + '/' + orc + '<');
    sub('>tudo gasto<', '>' + ((orc - gasto) > 0 ? (orc - gasto) + ' sobrando' : 'tudo gasto') + '<');
    var mel = 0;
    try{
      /* A referencia e o retrato imutavel do motor para ESTA funcao (e para
         a variante de posicao, quando houver). `_notaMot` pertencia a uma
         camada antiga; a fonte unica grava em `_nMot`, por meio de
         `_notaDoMotor`. Ler o nome antigo deixava o indicador sempre em 0%. */
      var maxFuncao = posNota ? _notaDoMotorPos(c, posNota) : _notaDoMotor(c);
      if (nt > 0 && maxFuncao > nt) mel = (maxFuncao - nt) / nt * 100;
    }catch(e){}
    sub('>0%<', '>' + (mel > 0.05 ? '+' + mel.toFixed(1) : '0') + '%<');
    sub('+ 9 atributos indiferentes nesta função', '+ ' + nInd + ' atributos indiferentes nesta função');
    sub('>170 cm<', '>' + (c.h || '—') + ' cm<');
    h = h.replace(
      '<span style="font-size:11.5px;padding:5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d10);color:var(--d30)">'
        + (c.h || '—') + ' cm</span>',
      '<span style="font-size:11.5px;padding:5px 10px;border-radius:8px;background:var(--d126);border:1px solid var(--d105);color:var(--d45);font-weight:700">'
        + (c.h || '—') + ' cm</span>');
    sub('>72 kg<', '>' + (c.w || '—') + ' kg<');
    sub('>38 anos<', '>' + (c.age || '—') + ' anos<');
    sub('tendência a lesão Baixa', 'Tendência a Lesão: ' + esc(c.inj || '—'));
    sub('>Esquerdo<', '>' + esc(c.foot || '—') + '<');
    var pr = null; try{ pr = prPar(c); }catch(e){}
    sub('>Raramente<', '>' + esc(pr ? ((typeof PR_ROT_F !== 'undefined' && PR_ROT_F[pr[0]]) || '—') : 'sem dado') + '<');
    sub('>Média<', '>' + esc(pr ? ((typeof PR_ROT_Q !== 'undefined' && PR_ROT_Q[pr[1]]) || '—') : '—') + '<');
    sub('>pé bom <b', '>Pé Bom: <b');
    sub('>pé ruim <b', '>Pé Ruim: <b');
    sub('>precisão <b', '>Precisão: <b');
    var pb = 0; try{ pb = prBonus(c); }catch(e){}
    var iaTotal = 0;
    try{
      iaTotal = (c._ia !== undefined && c._ia !== null)
        ? +c._ia : +bonusPronto(c, 3, iaBonus);
      if (!isFinite(iaTotal)) iaTotal = 0;
    }catch(e){ iaTotal = 0; }
    sub('>ESTILO DE JOGO DA IA</div>',
        '>ESTILO DE JOGO DA IA</span><span style="margin-left:auto;font-size:11px;color:var(--d17)">'
      + 'TOTAL <b style="font-size:13px;color:'
      + (iaTotal > 0 ? C_MAIS : (iaTotal < 0 ? C_MENOS : C_ZERO)) + '">'
      + _sn(iaTotal, 2) + '</b></span></div>');
    h = h.replace(
      '<div style="font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d17)">ESTILO DE JOGO DA IA</span>',
      '<div style="display:flex;align-items:center;font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d17)"><span>ESTILO DE JOGO DA IA</span>');
    /* ⛔ 19/08 — OS DOIS "bônus na nota" SAIRAM. Ordem do Luis, e ele tem
       razao: eles vinham de DOIS enderecos. A nota usa `bonusPronto(c,i,...)`
       (o numero do banco) e a linha de texto chamava a funcao de calculo
       direto (`iaBonus`, `fisBonus`). Medido pela sessao do encaixe: 1.567
       linhas divergem no estilo da IA e 250 no corpo. Enquanto vierem de dois
       lugares, mostrar e pior que nao mostrar. */
    h = _tiraTexto(h, 'bônus');
    h = h.replace(/\s*na nota/gi, '');
    sub('>+0.14<', '>' + _sn(pb, 2) + '<');
    /* Centraliza somente o titulo e o numero da pontuacao, sem alterar o
       restante do cartao nem os estilos da designer. */
    h = h.replace(
      '<div style="display:flex;flex-direction:column;gap:7px">\n'
      + '<div style="font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d50)">PONTUAÇÃO TOTAL</div>',
      '<div style="display:flex;flex-direction:column;gap:7px;align-items:center;text-align:center">\n'
      + '<div style="font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d50)">PONTUAÇÃO TOTAL</div>');
    sub('>+305.9 pts<', '>' + _sn(c.b1 || 0, 1) + ' pts<');
    sub('>-1%<', '>' + _sn(corpoImpacto, 2) + '<');
    sub('>-3</b>', '>' + _sn(corpoSoma, 2) + '</b>');
    sub('>15</b>', '>' + fr.reduce(function(a, r){ return a + (+r[1] || 0); }, 0) + '</b>');
    sub('>-0.15</b>', '>' + _sn(corpoImpacto, 2) + '</b>');
    sub('>soma <b', '>Pontos somados: <b');
    h = h.replace(/<span>peso <b[^>]*>.*?<\/b><\/span>/, '');
    h = h.replace(/(<span style="margin-left:auto;font-size:14px;font-weight:700;color:var\(--d127\)">)/,
                  '$1Impacto na nota: ');
    /* A soma bruta e o impacto final sao proporcionais; mostrar os dois
       obrigava o leitor a interpretar uma etapa interna da formula. Fica
       somente o numero que realmente entra na pontuacao geral. */
    (function(){
      var iFis = h.indexOf('Pontos somados:');
      if (iFis < 0) return;
      var abFis = h.lastIndexOf('<div', iFis);
      if (abFis < 0) return;
      var fimFis = _fimDiv(h, abFis);
      var rodapeFis = '<div style="display:flex;align-items:center;justify-content:flex-end;gap:10px;'
        + 'border-top:1px solid var(--d29);padding-top:11px">'
        + '<span style="font-family:inherit;font-size:10px;letter-spacing:1px;color:var(--d17)">'
        + 'TOTAL</span>'
        + '<b style="font-family:inherit;font-size:14px;color:'
        + (corpoImpacto > 0 ? C_MAIS : (corpoImpacto < 0 ? C_MENOS : C_ZERO)) + '">'
        + _sn(corpoImpacto, 2) + '</b></div>';
      h = h.slice(0, abFis) + rodapeFis + h.slice(fimFis);
    })();

    /* ⛔ 19/08 — A FOTO DA FICHA.
       O molde da designer traz um quadrado com a palavra "foto" dentro, e a
       ficha nunca o preenchia — por isso ela era o unico lugar do sistema sem
       imagem. Nao existe campo de imagem no card: a URL sai do proprio `id`,
       pela mesma `url()` que a lista e a home ja usam. Uma funcao so, tres
       telas. E o quadrado cresceu (112x148 -> 152x201), ordem do Luis. */
    (function(){
      var alvo = '>foto</div>', i = h.indexOf(alvo);
      if (i < 0) return;
      var ab = h.lastIndexOf('<div', i);
      if (ab < 0) return;
      /* ⛔ 19/08 — A ORDEM DO CABECALHO E A DO LUIS:
         foto grande · nome · posicao · estilo de jogo. Em coluna, centrado.
         A moldura do card ja vem desenhada na propria imagem da Konami, entao
         a foto entra inteira, sem borda nossa por cima. */
      var novo =
        '<div style="display:flex;flex-direction:column;align-items:center;gap:10px;width:100%">'
        + '<div style="' + medSt(c, 208, 275, 14) + ';border:none"></div>'
        + '<div style="font-size:25px;font-weight:800;letter-spacing:-.4px;color:var(--d1);text-align:center;line-height:1.15">'
        + esc(c.nome || '') + '</div>'
        + '<div style="display:flex;align-items:center;gap:8px">'
        +   '<span style="font-family:inherit;font-size:11px;font-weight:800;letter-spacing:.6px;'
        +   'padding:4px 9px;border-radius:7px;background:var(--d112);color:var(--d8)">'
        +   esc(_sig(np) || '—') + '</span>'
        +   '<span style="font-size:13px;color:var(--d30)">' + esc(_nomeP(np) || '—') + '</span>'
        + '</div>'
        + '<div style="display:flex;align-items:center;gap:8px">'
        +   '<span style="width:26px;height:26px;border-radius:50%;flex:none;display:flex;'
        +   'align-items:center;justify-content:center;background:var(--d14);'
        +   'border:1px solid var(--d31);font-size:13px;color:var(--d108)">◎</span>'
        +   '<span style="font-size:17px;font-weight:700;letter-spacing:-.2px;color:var(--d108);text-transform:uppercase">'
        +   esc(_extenso(c.modelo) || '—') + '</span>'
        + '</div>'
        + '</div>';
      /* sobe um nivel: sai a linha inteira (foto + coluna do nome), nao so a foto */
      var linha = h.lastIndexOf('<div', ab - 1);
      if (linha < 0) linha = ab;
      h = h.slice(0, linha) + novo + h.slice(_fimDiv(h, linha));
    })();

    /* ⛔ 19/08 — OS BLOCOS QUE O LUIS MANDOU TIRAR.
       `Base Konami` / `Máximo Konami`: o `max_ovr` vem vazio para parte das
       cartas e o Maximo caia no mesmo numero da Base. Numero que nao se sabe
       nao fica na tela.
       A data: ela e do BOX, nunca foi de lancamento. Sai ate existir a de
       verdade.
       `POSIÇÃO NATIVA:`: a posicao ja esta escrita no cabecalho novo. */
    h = _tiraBloco(h, '>Base Konami<', 1);
    h = _tiraBloco(h, 'box · ', 0);
    h = _tiraBloco(h, 'sem data de box', 0);
    (function(){
      var i = h.indexOf('POSIÇÃO NATIVA:');
      if (i < 0) return;
      var ab = h.lastIndexOf('<div', i);
      if (ab < 0) return;
      h = h.slice(0, ab) + h.slice(_fimDiv(h, ab));
    })();

    /* ⛔ 19/08 — O CAMPO E UM GRAMADO, E GRAMADO E VERDE.
       Ordem do Luis: "onde voce ocupa o campo preto na sua vida?". Sai a
       moldura de caixa que ele mandou tirar, entra o gramado: verde, listrado
       como campo cortado, com a linha do meio e o circulo central. O desenho
       nao e enfeite — e o que faz a leitura ser imediata. */
    sub('padding:12px;background:linear-gradient(180deg,var(--d75),var(--d113));display:flex;flex-direction:column;gap:5px',
        'position:relative;padding:12px 10px;border-radius:12px;display:flex;flex-direction:column;gap:5px;'
      + 'max-width:210px;margin:0 auto;width:100%;'
      + 'background:'
      +   'repeating-linear-gradient(180deg,rgba(255,255,255,.045) 0 26px,transparent 26px 52px),'
      +   'radial-gradient(120px 90px at 50% 50%,rgba(255,255,255,.10),transparent 70%),'
      +   'linear-gradient(180deg,#1d6b41,#0f4a2c);'
      + 'box-shadow:inset 0 0 0 2px rgba(255,255,255,.22)');

    /* ---------- habilidades: os quatro blocos ---------- */
    var hab = [], nat = (c.fab || []).concat(c.raras || []), pool = [];
    var podeRemoverHab = false;
    try{ podeRemoverHab = (window.t6Modo() === 'livre'); }catch(e){}
    try{ hab = habsAtual(c) || []; }catch(e){}
    /* ⛔ 19/08 — SUGESTAO NAO E O POOL INTEIRO.
       Ordem do Luis, e ele ja tinha dito antes: *"sugestoes sao aquelas
       habilidades que o cara pode adicionar e que NAO vao alterar a nota dele.
       As que ficavam de fora, mas que se trocasse alguma das adicionadas por
       ela, a nota nao mudava. Sempre foi isso."*
       O dado ja existe e vem do motor: o campo `NEU` de cada linha — o proprio
       gerador escreve "NEU = da pra selecionar e a nota NAO muda". Eu estava
       jogando na tela o `Object.keys(HABEF)` inteiro, 62 habilidades, e
       chamando aquilo de sugestao. Nao era sugestao, era catalogo.
       Sem `NEU` na linha, nao se inventa lista: mostra-se nada e diz-se por que. */
    var poolEhNeutro = true;
    try{
      var _neu = c.NEU;
      if (!_neu || !_neu.length){
        poolEhNeutro = false;
        _neu = [];
      }
      pool = _neu.filter(function(s){
        return hab.indexOf(s) < 0 && nat.indexOf(s) < 0 && !_ehEspecial(s); })
        .sort(function(x, y){ return x.localeCompare(y, 'pt'); });
    }catch(e){ pool = []; poolEhNeutro = false; }
    /* Na montagem manual a secao existe, mas nasce vazia. Ela so recebe as
       sugestoes do motor quando o usuario copia o maximo possivel. */
    var poolOcultoMinha = false;
    try{
      var _idPool = String(c.id).split('@')[0];
      poolOcultoMinha = (window.t6Modo() !== 'motor')
        && !(window._T6_COPIOU_MAX && window._T6_COPIOU_MAX[_idPool]);
      if (poolOcultoMinha) pool = [];
    }catch(e){}
    /* ⛔ 19/08 — AS ETIQUETAS DE HABILIDADE SE ATROPELAVAM.
       Mesmo defeito do nome da funcao na lista: a etiqueta nao tinha largura
       propria, entao um nome de duas palavras ("Chute de primeira", "Curva
       para fora") quebrava DENTRO da etiqueta e a segunda linha subia por
       cima da fileira de baixo. Duas coisas resolvem, e as duas ficam aqui:
         1. a etiqueta nunca quebra por dentro (`white-space:nowrap`)
         2. as etiquetas moram num flex meu, com quebra e respiro proprios —
            nao no que sobrou do bloco do molde. */
    var _NOQ = 'white-space:nowrap;display:inline-flex;align-items:center;flex:0 0 auto;';
    /* ⛔ sem moldura nas especiais — ordem do Luis, 19/08 */
    var E_ESP = _NOQ + 'font-size:12.5px;font-weight:600;padding:5px 11px;border-radius:8px;background:var(--d118);border:none;color:var(--d117)';
    var E_NAT = _NOQ + 'font-size:12px;padding:5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d12);color:var(--d30)';
    var E_ADD = _NOQ + 'gap:8px;font-size:12px;padding:5px 8px 5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d18);color:var(--d30)';
    var E_SUG = _NOQ + 'font-size:11.5px;padding:4px 9px;border-radius:7px;background:var(--d14);border:1px solid var(--d18);color:var(--d85);cursor:pointer';
    /* a fileira: quebra onde tem que quebrar, com espaco entre linha e linha */
    function fila(conteudo){
      return '<div style="display:flex;flex-wrap:wrap;align-items:flex-start;'
           + 'align-content:flex-start;gap:7px;width:100%">' + conteudo + '</div>';
    }
    function vazio(txt){ return '<span style="font-size:12px;color:var(--d17)">' + txt + '</span>'; }
    h = _miolo(h, 'background:var(--d118);border:',
      fila((c.raras || []).length
        ? (c.raras || []).map(function(s){ return '<span style="' + E_ESP + '">' + esc(_extenso(s)) + '</span>'; }).join('')
        : vazio('nenhuma')));
    h = _miolo(h, '>Finta dupla<',
      fila((c.fab || []).length
        ? (c.fab || []).map(function(s){ return '<span style="' + E_NAT + '">' + esc(_extenso(s)) + '</span>'; }).join('')
        : vazio('—')));
    h = _miolo(h, 'border:1px dashed var(--d31)',
      fila(hab.length
        ? hab.map(function(s, i){
            return '<span style="' + E_ADD + '">' + esc(_extenso(s))
                 + (podeRemoverHab
                    ? '<b data-hx="' + i + '" style="font-size:13px;color:var(--d13);line-height:1;cursor:pointer">×</b>'
                    : '')
                 + '</span>'; }).join('')
        : vazio('nenhuma')));
    h = _miolo(h, '>Drible de primeira<',
      fila(pool.length
        ? pool.map(function(s){ return '<span data-add="' + esc(s) + '" style="' + E_SUG + '">' + esc(_extenso(s)) + '</span>'; }).join('')
        : vazio('—')));
    sub('>5 de 5<', '>' + hab.length + ' de 5<');
    /* ⛔ 19/08 — OS TITULOS DO BLOCO, UM POR LINHA E EM MAIUSCULAS.
       Ordem do Luis: `HABILIDADES` + `especiais` viravam duas linhas para
       dizer uma coisa so. Agora cada grupo tem o nome inteiro, e o rotulo
       solto `HABILIDADES` sai. */
    var T_TIT = 'font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d17)';
    h = h.replace('<div style="font-family:inherit;font-size:9.5px;letter-spacing:1.4px;'
                + 'color:var(--d17)">HABILIDADES</div>', '');
    sub('<div style="font-size:11px;color:var(--d17)">especiais</div>',
        '<div style="' + T_TIT + '">HABILIDADES ESPECIAIS</div>');
    sub('<div style="font-size:11px;color:var(--d17)">nativas</div>',
        '<div style="' + T_TIT + '">HABILIDADES NATIVAS</div>');
    sub('<span style="font-size:11px;color:var(--d17)">adicionadas</span>',
        '<span style="' + T_TIT + '">HABILIDADES ADICIONADAS</span>');
    sub('<div style="font-size:11px;color:var(--d17)">sugestões · o pool inteiro que o motor pode escolher · 8</div>',
        '<div style="' + T_TIT + '">HABILIDADES SUGERIDAS</div>'
      + '<div style="font-size:11px;color:var(--d17);margin-top:-2px">'
      + (poolOcultoMinha ? '' : (pool.length
          ? 'trocar por qualquer uma destas não muda a nota'
          : (poolEhNeutro
              ? 'nenhuma troca mantém a nota nesta build'
              : 'o motor ainda não mediu as trocas desta função')))
      + '</div>');

    /* ⛔ 19/08 — O BLOCO DE ÍMPETO NUNCA FOI PREENCHIDO.
       O que estava na tela era o EXEMPLO DA DESIGNER: "Fantasia +2", "Instinto
       Artilheiro +1". Nao era o card. Por isso o Luis viu impeto condicional
       numa carta que nao tem, e um nativo que nao e o dela.
       Agora sai do dado, com a mesma cadeia da casca antiga:
         1. `pimpNativos(c)`  — decompoe o vetor `c.nm` contra o catalogo CAT
         2. `pimpDoCard(c)`   — a tabela PIMP, por boostId
         3. decomposicao gulosa do proprio `c.nm`
         4. o efeito cru, atributo a atributo — nunca "nao tem" em quem tem
       ⛔ O CONDICIONAL SO APARECE QUANDO EXISTE: `c.CD` com degrau 2 ou 3.
          A regra e da casca (`_cond` do painelBuild) e vale igual aqui. */
    (function(){
      var iCab = h.indexOf('>ÍMPETO<');
      if (iCab < 0) return;
      var abCab = h.lastIndexOf('<div', iCab);
      if (abCab < 0) return;
      var fim1 = _fimDiv(h, abCab);              /* o rotulo ÍMPETO */
      var ab2 = h.indexOf('<div', fim1);
      if (ab2 < 0) return;
      var fim2 = _fimDiv(h, ab2);                /* o cartao do nativo */
      var ab3 = h.indexOf('<div', fim2);
      var fim3 = (ab3 >= 0) ? _fimDiv(h, ab3) : fim2;   /* o cartao do adicionado */

      function _attrNome(i){
        try{ if (typeof ATTRS !== 'undefined' && ATTRS[i]) return ATTRS[i]; }catch(e){}
        return 'atributo ' + i;
      }
      function _chips(pares){
        var por = {}, out = [];
        (pares || []).forEach(function(x){ (por[x[1]] = por[x[1]] || []).push(_attrNome(x[0])); });
        Object.keys(por).sort(function(a, b){ return b - a; }).forEach(function(v){
          por[v].forEach(function(nm){
            out.push('<span style="font-size:11px;color:var(--d85);background:var(--d10);'
                   + 'padding:4px 8px;border-radius:6px;white-space:nowrap">' + esc(nm) + '</span>');
          });
        });
        return out.join('');
      }
      function _grau(pares){
        var m = 0;
        (pares || []).forEach(function(x){ if (+x[1] > m) m = +x[1]; });
        return m ? ('+' + m) : '';
      }
      function _doCat(nome){
        try{ for (var i = 0; i < CAT.length; i++) if (CAT[i][0] === nome) return CAT[i][2]; }catch(e){}
        return null;
      }

      /* ---- o NATIVO ----
         ⛔ 19/08 — A ORDEM DAS FONTES E A QUE A SESSAO DO ENCAIXE MEDIU:
           1. `c.imp`   — a string que o `impeto_da_carta()` ja montou. E o que
                          o resto do sistema inteiro le. ESTA e a fonte.
           2. `pimpNativos(c)` — quando se precisa do nome e do efeito separados
           3. `c.nmn`   — a lista crua de nomes de fabrica
           4. `_natDoVetor(c)` — ultimo recurso; com o `c.imp` ja declarado ele
                          devolve "nao tem", e isso esta CERTO, nao e defeito
           ⛔ `pimpDoCard` NUNCA para o nome: o PIMP guarda o nome do efscout,
              em ingles ("Shooting +3"). So serve para o efeito.
         Medido no Ruud Gullit `88039045074410`: as quatro concordam em
         `Chute +3`. */
      var nativos = [];
      try{
        var _fab = String(c.imp || '').split('o motor pos:')[0]
                     .replace(/^\s*de f[aá]brica:\s*/i, '')
                     .replace(/\s*⚒\s*$/, '').trim();
        if (_fab && _fab.indexOf('efeito somado') < 0){
          _fab.split(/\s+[·+]\s+/).forEach(function(n){
            n = n.trim();
            if (n) nativos.push({nome: n, ef: _doCat(n)});
          });
        }
      }catch(e){}
      if (!nativos.length){
        try{
          var L = (typeof pimpNativos === 'function') ? pimpNativos(c) : null;
          if (L && L.length) nativos = L.map(function(x){ return {nome: x.nome, ef: x.efeito}; });
        }catch(e){}
      }
      if (!nativos.length && c.nmn && c.nmn.length){
        nativos = c.nmn.map(function(n){ return {nome: n, ef: _doCat(n)}; });
      }
      /* O nome exibido vem de `c.imp`, mas algumas linhas trazem apenas esse
         rotulo e nao carregam o efeito junto. Complete o efeito pelas fontes
         estruturadas sem trocar o nome em portugues que ja foi confirmado. */
      try{
        var _ln = (typeof pimpNativos === 'function') ? pimpNativos(c) : null;
        if (_ln && _ln.length){
          nativos.forEach(function(x, i){
            if ((!x.ef || !x.ef.length) && _ln[i] && _ln[i].efeito) x.ef = _ln[i].efeito;
          });
        }
        if (nativos.length === 1 && (!nativos[0].ef || !nativos[0].ef.length)
            && typeof pimpDoCard === 'function'){
          var _pc = pimpDoCard(c);
          if (_pc && _pc.efeito) nativos[0].ef = _pc.efeito;
        }
      }catch(e){}
      if (!nativos.length){
        /* o efeito cru: melhor mostrar o que se sabe do que dizer "nao tem" */
        var cru = [];
        try{
          var v = expand(c.nm);
          for (var q = 0; q < 26; q++) if (v[q]) cru.push([q, v[q]]);
        }catch(e){}
        if (cru.length) nativos = [{nome: 'ímpeto nativo', ef: cru}];
      }

      /* ---- o ADICIONADO ---- */
      var addNome = '';
      try{
        if (typeof impAdicionado === 'function') addNome = impAdicionado(c) || '';
        else {
          var pp = String(c.imp || '').split('o motor pos:');
          addNome = (pp.length > 1) ? pp[1].trim() : '';
        }
      }catch(e){}

      /* ---- o CONDICIONAL: so quando o card tem ---- */
      var temCond = false;
      try{ temCond = !!(c.CD && (c.CD['2'] || c.CD['3'])); }catch(e){}
      /* ⛔ 19/08 — `cmode` NAO E O DEGRAU: e degrau-1.
         O `setCondCard(key, degrau)` grava `c.cmode = degrau - 1` (0,1,2) e o
         degrau que se chama e absoluto (1,2,3). Ler `cmode` como degrau e o
         leitor velho, e foi ele o `111,6 · 111,6 · 132,2` do Can Uzun. */
      var grauAtual = 1;
      try{ grauAtual = (+c.cmode || 0) + 1; }catch(e){}
      if (!(grauAtual >= 1 && grauAtual <= 3)) grauAtual = 1;

      var E_CARD = 'background:var(--d12);border:1px solid var(--d7);border-radius:12px;'
                 + 'padding:11px 13px;display:flex;flex-direction:column;gap:7px';
      var E_LINHA = 'display:flex;align-items:center;gap:9px';
      var E_BADGE = 'margin-left:auto;font-family:inherit;font-size:14px;font-weight:700;'
                  + 'padding:2px 9px;border-radius:7px;background:var(--d33);'
                  + 'border:1px solid var(--d11);color:var(--d1)';
      var E_FILA = 'display:flex;flex-wrap:wrap;gap:5px';

      function cartao(nome, rotulo, ef, extra){
        return '<div style="' + E_CARD + '">'
          + '<div style="' + E_LINHA + '">'
          +   '<b style="font-size:13.5px">' + esc(_extenso(nome)) + '</b>'
          +   '<span style="font-weight:400;font-size:11px;color:var(--d17)">' + rotulo + '</span>'
          +   (_grau(ef) ? '<b style="' + E_BADGE + '">' + _grau(ef) + '</b>' : '')
          + '</div>'
          + (ef && ef.length ? '<div style="' + E_FILA + '">' + _chips(ef) + '</div>' : '')
          + (extra || '')
          + '</div>';
      }

      var condHtml = '';
      if (temCond){
        var bts = '';
        [1, 2, 3].forEach(function(gg){
          var existe = (gg === 1) || !!(c.CD && c.CD[String(gg)]);
          var on = (gg === grauAtual);
          bts += '<b data-cond="' + gg + '" style="font-family:inherit;font-size:12px;'
              + 'font-weight:' + (on ? '700' : '500') + ';padding:4px 12px;border-radius:7px;'
              + (on ? 'background:linear-gradient(180deg,var(--d121),var(--d122));color:var(--d123);'
                    + 'box-shadow:0 3px 10px var(--d124)'
                    : 'background:var(--d12);border:1px solid var(--d18);color:var(--d85)')
              + (existe ? ';cursor:pointer' : ';opacity:.3')
              + '">+' + gg + '</b>';
        });
        condHtml = '<div style="display:flex;align-items:center;gap:9px;'
          + 'border-top:1px solid var(--d15);padding-top:9px;margin-top:2px">'
          + '<span style="display:flex;align-items:center;gap:6px;font-family:inherit;font-size:9px;'
          +   'letter-spacing:1.2px;color:var(--d120)">'
          +   '<i style="width:10px;height:10px;background:var(--d120);display:block;'
          +   'clip-path:polygon(50% 0,100% 25%,100% 75%,50% 100%,0 75%,0 25%)"></i>ÍMPETO CONDICIONAL</span>'
          + '<span style="display:flex;gap:5px;margin-left:auto">' + bts + '</span></div>';
      }

      var novo = h.slice(abCab, fim1);   /* o rotulo ÍMPETO fica como ela desenhou */
      if (nativos.length){
        nativos.forEach(function(x, ix){
          novo += cartao(x.nome, 'nativo', x.ef, (ix === 0 ? condHtml : ''));
        });
      } else {
        /* ⛔ 19/08 — TRES ESTADOS, MEDIDOS NO BANCO (6.902 cards):
             3.214 dizem que NAO tem ....... "não tem ímpeto nativo"
               191 tem o codigo e o catalogo nao conhece o efeito
               433 nunca foram conferidos
           Escrever "nao tem" nos 624 ultimos e mentir com cara de certeza.
           E a mesma regra do Luis de 15/08: nao se poe zero no lugar de
           nao sei — aqui, nao se poe "nao tem" no lugar de "nao perguntei". */
        var _txt, _sub, _cor;
        if (c.impDesc){
          _txt = 'TEM ímpeto — efeito por conferir';
          _sub = 'a carta veio com ímpeto de fábrica, mas o catálogo não conhece esse código'
               + ((c.boostIds && c.boostIds.length) ? ' (' + c.boostIds.join(' e ') + ')' : '')
               + '. O motor calculou SEM ele: a pontuação está por baixo.';
          _cor = 'var(--d55)';
        } else if (c.temImp === 0){
          _txt = 'não tem ímpeto nativo';
          _sub = '';
          _cor = 'var(--d17)';
        } else {
          _txt = 'ímpeto ainda não conferido';
          _sub = 'ninguém perguntou esta carta ainda — não é o mesmo que não ter.';
          _cor = 'var(--d55)';
        }
        novo += '<div style="' + E_CARD + '"><div style="' + E_LINHA + '">'
             + '<b style="font-size:13px;color:' + _cor + '">' + _txt + '</b></div>'
             + (_sub ? '<div style="font-size:11px;color:var(--d17);line-height:1.45">'
                     + _sub + '</div>' : '')
             + condHtml + '</div>';
      }
      if (addNome){
        novo += cartao(addNome, 'adicionado', _doCat(addNome),
          '<div data-impsel="1" style="display:flex;align-items:center;gap:8px;'
          + 'border-top:1px solid var(--d15);padding-top:9px;margin-top:2px"></div>');
      } else {
        novo += '<div style="' + E_CARD + '"><div style="' + E_LINHA + '">'
             + '<b style="font-size:12.5px;font-weight:600;color:var(--d17)">'
             + (c.slot === 0 ? 'não tem vaga para ímpeto adicionado'
                             : (c.slot ? 'vaga livre' : 'vaga ainda não conferida'))
             + '</b></div>'
             + '<div data-impsel="1" style="display:flex;align-items:center;gap:8px"></div></div>';
      }

      h = h.slice(0, abCab) + novo + h.slice(fim3);
    })();

    /* ---------- tecnico ---------- */
    var tecNome = (c._tecNome !== undefined ? c._tecNome : c.TEC) || '';
    sub('>Pep Guardiola <span', '>' + esc(tecNome || '(nenhum)') + ' <span');
    var tb = [];
    try{ tb = (tecAtual(c) || []).map(function(x){ return (typeof tecPT === 'function') ? tecPT(x) : x; }); }catch(e){}
    sub('+1 Posse de bola · +1 Drible',
        tb.length ? tb.map(function(x){ return '+1 ' + esc(x); }).join(' · ') : 'sem técnico');
    /* ⛔ A MOLDURA E A DELA. O corpo da ficha ja e a grade de duas colunas —
       sem o `abre` dela o modal fica sem fundo e a home aparece por tras. */
    return M.ficha.abre + h + '</div>';
  };

  /* ⛔ 19/08 — POR QUE ESTE `t6Bar` EXISTE, e nao um `editBar(...)` direto.
     Medido: chamar `editBar` NAO mexe no card. Ele fechou sobre uma versao
     antiga de `_grava` (a casca tem tres, empilhadas por patches diferentes) e
     grava num lugar que ninguem mais le. A prova: os mesmos passos, chamados
     com as funcoes de hoje, mudam o nivel de 4 para 3 na hora.
     ⛔ A REGRA NAO E MINHA: e a mesma do editBar, linha por linha. So as pecas
        sao as vigentes. Se um dia `editBar` for consertado, esta funcao pode
        virar uma chamada a ele — e nada mais muda. */
  window.t6Bar = function(key, bar, d, raiz){
    var c = null;
    try{ c = _card(key); }catch(e){}
    if (!c) return;
    /* ⛔ 19/08 — A TRAVA DA ABA, PELA DECIMA VEZ PEDIDA.
       Regra da casca: barra so se mexe na aba "DO MEU JEITO" (`livre`). Na aba
       do MAXIMO a carta ja esta no teto — nao ha o que subir. A casca tinha a
       trava (`guarda('editBar', travaBarra)`), mas o `t6Bar` grava direto e
       passava por fora dela. Agora a mesma regra vale aqui. */
    if (window.t6Modo() !== 'livre'){
      window.t6AvisoBar(raiz, window.t6Modo() === 'motor'
        ? 'no máximo não se edita'
        : 'edite na aba DO MEU JEITO');
      return;
    }
    try{ _marca(key); }catch(e){}
    var lvl = _lvlDe(c), antes = lvl[bar] || 0;
    var nv = Math.max(0, Math.min(25, antes + d));
    if (nv === antes) return;
    lvl[bar] = nv;
    if (gastoDe(lvl) > (c.orc || 0)){
      lvl[bar] = antes;
      window.t6AvisoBar(raiz, 'não cabe: só sobram ' + ((c.orc || 0) - gastoDe(lvl)) + ' pts');
      return;
    }
    try{ _grava(c, lvl); }catch(e){ return; }
    try{ window.t6ReabreFicha(key); }catch(e){}
  };
  /* o aviso mora no proprio rotulo do orcamento, por dois segundos —
     nada de alert(), que trava a pagina inteira. */
  window.t6AvisoBar = function(raiz, txt){
    try{
      var alvos = [].slice.call((raiz || document).querySelectorAll('b'));
      for (var i = 0; i < alvos.length; i++){
        var t = (alvos[i].textContent || '').trim();
        if (t === 'tudo gasto' || /sobrando$/.test(t) || /^não cabe/.test(t)){
          if (alvos[i]._t6volta === undefined) alvos[i]._t6volta = t;
          alvos[i].textContent = txt;
          alvos[i].style.color = 'var(--d55)';
          (function(el){ setTimeout(function(){
            el.textContent = el._t6volta; el.style.color = ''; }, 2200); })(alvos[i]);
          return;
        }
      }
    }catch(e){}
  };

  /* Caixa propria para nomear a build. `prompt()` e bloqueado em alguns
     navegadores/embutidos e fazia o botao parecer morto. */
  window.t6PedeNomeBuild = function(sugestao, conclui){
    var antiga = document.getElementById('t6nomebuild');
    if (antiga) antiga.remove();
    var fundo = document.createElement('div');
    fundo.id = 't6nomebuild';
    fundo.style.cssText = 'position:fixed;inset:0;z-index:100000;display:grid;place-items:center;'
      + 'background:rgba(0,0,0,.62);padding:18px';
    fundo.innerHTML = '<div style="width:min(390px,100%);background:var(--d13);color:var(--d8);'
      + 'border:1px solid var(--d31);border-radius:14px;padding:18px;box-shadow:0 18px 60px #0008">'
      + '<div style="font-size:13px;font-weight:900;margin-bottom:10px">NOME DA BUILD</div>'
      + '<input data-nome-build maxlength="60" style="box-sizing:border-box;width:100%;padding:11px 12px;'
      + 'border-radius:9px;border:1px solid var(--d31);background:var(--d11);color:var(--d8);font:inherit">'
      + '<div style="display:flex;justify-content:flex-end;gap:8px;margin-top:14px">'
      + '<button data-cancela style="padding:9px 14px;border-radius:8px;border:1px solid var(--d31);'
      + 'background:transparent;color:var(--d8);font-weight:800">CANCELAR</button>'
      + '<button data-confirma style="padding:9px 14px;border-radius:8px;border:1px solid var(--d25);'
      + 'background:var(--d25);color:#06200f;font-weight:900">SALVAR</button></div></div>';
    document.body.appendChild(fundo);
    var inp = fundo.querySelector('[data-nome-build]');
    inp.value = sugestao || '';
    function fecha(v){ fundo.remove(); if (typeof conclui === 'function') conclui(v); }
    fundo.querySelector('[data-cancela]').onclick = function(){ fecha(null); };
    fundo.querySelector('[data-confirma]').onclick = function(){ fecha(inp.value); };
    fundo.onclick = function(e){ if (e.target === fundo) fecha(null); };
    inp.onkeydown = function(e){
      if (e.key === 'Enter') fecha(inp.value);
      else if (e.key === 'Escape') fecha(null);
    };
    setTimeout(function(){ inp.focus(); inp.select(); }, 0);
  };
  window.t6Notifica = function(txt){
    var velha = document.getElementById('t6notifica');
    if (velha) velha.remove();
    var n = document.createElement('div');
    n.id = 't6notifica'; n.textContent = txt;
    n.style.cssText = 'position:fixed;z-index:100001;right:20px;bottom:20px;max-width:420px;'
      + 'padding:12px 15px;border-radius:10px;background:var(--d25);color:#06200f;'
      + 'font-size:12px;font-weight:900;box-shadow:0 12px 35px #0007';
    document.body.appendChild(n);
    setTimeout(function(){ if(n.parentNode) n.remove(); }, 3200);
  };

  /* ⛔ 19/08 — MESMO REMEDIO DO `t6Bar`, agora para HABILIDADE e TECNICO.
     Medido: `addHab` / `remHab` da casca fecham sobre um `_trocaHabs` LOCAL
     do IIFE dela — nao sobre o `window._trocaHabs` vigente. Clicar mexia num
     objeto que ninguem mais le. Aqui a lista e montada e entregue ao
     `window._trocaHabs`, que e o unico que refaz sis/arows/b1 e redesenha. */
  window.t6Hab = function(key, acao, val, raiz){
    var c = null;
    try{ c = _card(key); }catch(e){}
    if (!c) return;
    var atuais = [];
    try{ atuais = (habsAtual(c) || []).slice(); }catch(e){}
    if (acao === 'rem'){
      var ix = +val;
      if (!(ix >= 0 && ix < atuais.length)) return;
      atuais.splice(ix, 1);
    } else {
      if (!val) return;
      if (_ehEspecial(val)){
        window.t6AvisoBar(raiz, 'habilidade especial só vem de fábrica');
        return;
      }
      if (atuais.indexOf(val) >= 0) return;
      var teto = 5;
      try{ if (c.vagas !== undefined && c.vagas !== null) teto = +c.vagas; }catch(e){}
      if (atuais.length >= teto){
        window.t6AvisoBar(raiz, 'sem vaga: o card tem ' + teto);
        return;
      }
      atuais.push(val);
    }
    try{ _marca(key); }catch(e){}
    try{ window._trocaHabs(key, atuais); }catch(e){ return; }
    /* `_trocaHabs` ja recalcula e redesenha a ficha. Reabrir outra vez aqui
       duplicava todo o trabalho e fazia a habilidade parecer travada. */
  };

  /* o tecnico: chama o `trocaTec` vigente e CONFERE. Se o card nao mudou,
     escreve na mao e regrava — sem depender de qual versao venceu. */
  window.t6Tec = function(key, idx){
    var c = null;
    try{ c = _card(key); }catch(e){}
    if (!c) return;
    var antes = (c._tecNome !== undefined ? c._tecNome : c.TEC) || '';
    try{ _marca(key); }catch(e){}
    try{ trocaTec(key, idx); }catch(e){}
    var c2 = null;
    try{ c2 = _card(key); }catch(e){}
    if (!c2) return;
    var depois = (c2._tecNome !== undefined ? c2._tecNome : c2.TEC) || '';
    var alvo = (idx === '' || idx === null || idx === undefined) ? '' 
             : ((typeof TECS !== 'undefined' && TECS[+idx]) ? TECS[+idx][0] : '');
    if (depois !== alvo){
      /* ⛔ 19/08 — ERRO MEU, DE ONTEM. Eu guardava em `_tec` o PAR inteiro
         `[nome, [chaves]]` em vez das chaves. Ai o rodape lia o par como se
         fosse lista de atributos e escrevia
             "+1 Mikel Arteta · +1 acceleration,tightPossession"
         — o nome do tecnico virava atributo e as chaves saiam cruas, em
         ingles, grudadas por virgula. `_tec` guarda SO as chaves. */
      var _t = (alvo && typeof TECS !== 'undefined') ? TECS[+idx] : null;
      c2._tecNome = alvo;
      c2._tec = (_t && _t[1]) ? _t[1].slice() : [];
      try{ c2.TECB = c2._tec.slice(); }catch(e){ c2.TECB = []; }
      try{ _grava(c2, _lvlDe(c2)); }catch(e){}
    }
    try{ window.t6ReabreFicha(key); }catch(e){}
  };

  /* ⛔ 19/08 — A REGRA SIMETRICA DO CAMPINHO, DE VOLTA.
     Ela existia na casca antiga (`selPos` + `pedeFuncao`, 15/08) e morreu junto
     com o desenho velho, porque aquilo casava por classe CSS (`.cbp`, `.cbfn`) e
     o molde da designer nao tem classe nenhuma.
         clicou na POSICAO -> acende as FUNCOES que ela exerce
         clicou na FUNCAO  -> acende as POSICOES onde ele a exerce
     E a regra do Luis de 15/08, que ele repetiu em 19/08: clicar na posicao NAO
     abre ficha quando ha mais de uma funcao — ele escolhe qual quer ver. Quando
     ha uma so, abre direto ("quando o cara faz uma funcao so nao precisa
     escolher"). */
  window.t6Pos = function(pos, key){
    if (!pos) return;
    var c = null;
    try{ c = _card(key); }catch(e){}
    if (!c) return;
    var irm = [];
    try{
      var b = String(c.id).split('@')[0];
      irm = _t6IrmasUnicas(c);
    }catch(e){ irm = [c]; }
    var fs = _funcsDaPos(pos, c, irm);
    if (!fs.length) return;
    if (fs.length === 1){
      var unico = null;
      for (var u = 0; u < irm.length; u++) if (_mesmaFn(irm[u].tipo, fs[0])){ unico = irm[u]; break; }
      window._SELPOS = pos;
      window._T6PENDENTE_POS = null;
      window._T6SELPOS_FORCADA = pos;
      window._T6SELPOS_CARD = String(c.id).split('@')[0];
      var destinoUnico = (unico ? unico.id : c.id) + '|' + (unico ? unico.tipo : fs[0]);
      try{ window.t6AbreFuncao(destinoUnico); }catch(e){}
      return;
    }
    var nova = (window._T6PENDENTE_POS === pos) ? null : pos;
    window._SELPOS = nova;
    /* Outras camadas antigas de `reabrir` limpam `_SELPOS`. Esta chave e da
       ficha atual e sobrevive somente ate o usuario escolher uma funcao. */
    /* Posicao ainda nao e variante escolhida. Guardar em FORCADA fazia a
       nota da funcao antiga ser recalculada como se ela tivesse sido eleita. */
    window._T6PENDENTE_POS = nova;
    window._T6SELPOS_FORCADA = null;
    window._T6SELPOS_CARD = nova ? String(c.id).split('@')[0] : null;
    try{ window.t6ReabreFicha(key); }catch(e){}
  };

  /* Toda navegacao para outra FUNCAO comeca no retrato oficial do motor.
     A edicao de "fazer minha build" nao vaza para a funcao seguinte. */
  window.t6AbreMaximo = function(destino){
    if (!destino) return;
    /* Nao passa por `encModo`: a casca tem mais de uma camada dessa funcao e
       uma delas reaplica a foto da build livre depois de marcar "motor". O
       resultado era uma tela dizendo MAXIMO, mas com barras zeradas e botao
       OTIMIZAR. A fonte de verdade e `restaurarMotor`. */
    window.ENC_MODO = 'motor';
    window._T6ABA = 'motor';
    window._BLD_FOTO = null;
    window.BLD_SEM_LACO = 1;
    try{ document.documentElement.setAttribute('data-encmodo', 'motor'); }catch(e){}
    try{ if (document.body) document.body.setAttribute('data-encmodo', 'motor'); }catch(e){}
    try{ window.t6RestauraMotor(destino); }catch(e){}
    window.BLD_SEM_LACO = 0;
    /* `reabrir` ja redesenha a ficha inteira. Renderizar antes a home e todas
       as listagens fazia o clique trabalhar duas vezes sem mudar o resultado. */
    window.t6ReabreFicha(destino);
  };

  function _t6ImpetoSoDeFabrica(txt){
    txt = String(txt == null ? '' : txt);
    var i = txt.indexOf('o motor p');
    if (i > 0) txt = txt.slice(0, i).replace(/\s*[\u00b7+]\s*$/, '');
    return txt.replace(/\s*[\u00b7+]\s*[^\u00b7]*\u2692\s*$/, '').trim();
  }

  /* Reconstroi a CARTA DE FABRICA pela equacao, em vez de aproveitar `sis`,
     `arows` ou `b1n` da build maxima. Os atributos de fabrica sao os mesmos,
     mas cada funcao tem seus proprios pesos e alvos; por isso a nota base
     precisa nascer outra vez no molde do card de destino. */
  function _t6AplicaCartaBase(destino){
    var c = null; try{ c = _card(destino); }catch(e){}
    if (!c) return false;
    var foto = _t6FotoMotor(c), z = {};
    try{ MBK.forEach(function(x){ z[x] = 0; }); }catch(e){}

    c._habs = [];
    c._tec = [];
    c._tecNome = null;
    c.TECB = [];
    c.imp = _t6ImpetoSoDeFabrica(foto ? foto.imp : c.imp);
    /* `imps` alimenta somente a apresentacao dos impetos nativos. O calculo
       usa a string `imp`, que e a fonte de verdade documentada pela equacao. */
    if (foto && foto.imps) c.imps = foto.imps.map(function(x){
      return {n:x.n,c:x.c,f:x.f};
    });

    var vals = null;
    try{ vals = cadeia(c, z); }catch(e){}
    if (!vals || !vals.length) return false;
    c.sis = vals.slice();
    try{ c.sisBar = MBK.map(function(x){ return [x, 0]; }); }catch(e){ c.sisBar = []; }
    try{ c.sobra = +c.orc || +c.pts || 0; }catch(e){}
    (c.arows || []).forEach(function(r){
      r[3] = vals[r[0]];
      r[4] = r[3] - r[2];
      r[5] = r[3];
    });
    try{ c.b1 = notaDe(vals, c.arows); }catch(e){}
    try{
      var n=0,d=0;
      (c.arows||[]).forEach(function(r){
        var w=+r[1]||0; if(!w) return;
        n += w*r[3]; d += w*r[2];
      });
      if(d) c.b1n = 100*n/d;
    }catch(e){}
    delete c._cp; delete c._n; delete c._ori;
    return true;
  }

  window.t6AplicaCartaBase = _t6AplicaCartaBase;

  /* A build manual e descartavel por definicao: cada entrada nessa aba e cada
     troca de funcao enquanto ela esta aberta recomeca somente com os itens de
     fabrica. `elBuildBase` conserva nativos/especiais/impeto nativo e zera
     barras, tecnico, habilidades e impeto adicionados. A nota e recalculada
     pelo card da NOVA funcao, portanto nao reaproveita a nota anterior. */
  window.t6AbreLivreZerado = function(destino){
    if (!destino) return;
    window._T6ABA = 'livre';
    window.ENC_MODO = 'livre';
    window._BLD_FOTO = null;
    window._T6_COPIOU_MAX = window._T6_COPIOU_MAX || {};
    delete window._T6_COPIOU_MAX[String(destino).split('|')[0].split('@')[0]];
    try{ document.documentElement.setAttribute('data-encmodo', 'livre'); }catch(e){}
    try{ if (document.body) document.body.setAttribute('data-encmodo', 'livre'); }catch(e){}
    var aplicouBase = false;
    try{
      window.BLD_SEM_LACO = 1;
      aplicouBase = _t6AplicaCartaBase(destino);
      if (!aplicouBase) {
        window.BLD_SEM_LACO = 1;
        var cc = _card(destino), z = {};
        try{ MBK.forEach(function(x){ z[x] = 0; }); }catch(e){}
        try{ _grava(cc, z); }catch(e){}
        try{ window._trocaHabs(destino, []); }catch(e){}
        if (cc){ cc._tec = []; cc._tecNome = ''; try{ cc.TECB = []; }catch(e){} }
        try{ if (typeof editImp === 'function') editImp(destino, ''); }catch(e){}
      }
    }catch(e){}
    window.BLD_SEM_LACO = 0;
    /* A abertura da ficha ja refaz o que esta visivel; a home escondida nao
       precisa ser recalculada a cada troca de funcao. */
    window.t6ReabreFicha(destino);
  };

  /* A funcao e a chave da ficha. Trocar funcao preserva a ABA: maximo chama o
     maximo da nova funcao; montagem manual chama a base zerada da nova funcao. */
  window.t6AbreFuncao = function(destino){
    if (window.t6Modo() === 'livre') window.t6AbreLivreZerado(destino);
    else window.t6AbreMaximo(destino);
  };

  /* ⛔ A VIDA DOS BOTOES — cada um chama a MESMA funcao da casca. */
  window.t6FichaCliques = function(raiz, key){
    if (!raiz) return;
    function todos(sel){ return [].slice.call(raiz.querySelectorAll(sel)); }
    todos('[data-fn]').forEach(function(el){
      el.onclick = function(){
        window._T6PENDENTE_POS = null;
        window._SELPOS = null;              /* clicou na funcao: solta a posicao */
        window._T6SELPOS_FORCADA = null;
        window._T6SELPOS_CARD = null;
        var destino = el.getAttribute('data-fn');
        if (!destino) return;
        window.t6AbreFuncao(destino);
      };
    });
    todos('[data-fnvariant]').forEach(function(el){
      var variante = el.getAttribute('data-fnvariant');
      if (!variante) return;
      el.onclick = function(ev){
        if(ev){ ev.preventDefault(); ev.stopPropagation(); }
        window._T6PENDENTE_POS = null;
        window._SELPOS = variante;
        window._T6SELPOS_FORCADA = variante;
        var destino = el.getAttribute('data-fn');
        try{ window._T6SELPOS_CARD=String(_card(destino).id).split('@')[0]; }catch(e){}
        if(destino) window.t6AbreFuncao(destino);
      };
    });
    todos('[data-fnpos]').forEach(function(el){
      el.onclick=function(ev){
        if(ev){ ev.preventDefault(); ev.stopPropagation(); }
        var p=el.getAttribute('data-fnpos'), destino=el.getAttribute('data-fnkey');
        window._SELPOS=p; window._T6SELPOS_FORCADA=p;
        try{ window._T6SELPOS_CARD=String(_card(destino).id).split('@')[0]; }catch(e){}
        if(destino) window.t6AbreFuncao(destino);
      };
    });
    todos('[data-pos]').forEach(function(el){
      var p = el.getAttribute('data-pos');
      if (!p) return;
      el.style.cursor = 'pointer';
      el.onclick = function(){ window.t6Pos(p, key); };
    });
    var _modo = window.t6Modo(), _travado = (_modo !== 'livre');
    var _cardAqui = null; try{ _cardAqui = _card(key); }catch(e){}

    /* Na pagina, a FUNCAO manda na build. A ordem aprovada da coluna e:
       identificacao, pontuacao, funcoes e somente depois o campinho. Nao se
       recria nenhum bloco nem se muda seu desenho; apenas inverte os dois
       blocos ja existentes. */
    try{
      var primeiraFnOrdem = raiz.querySelector('[data-fn]');
      var primeiraPosOrdem = raiz.querySelector('[data-pos]');
      if (primeiraFnOrdem && primeiraPosOrdem){
        /* A lista e o campo tem profundidades diferentes no molde. A versao
           anterior comparava apenas os pais imediatos e, por isso, nao movia
           nada. Primeiro acha o ancestral comum; depois sobe cada elemento
           ate o filho direto desse ancestral. */
        var comum=primeiraFnOrdem.parentNode;
        while(comum && !comum.contains(primeiraPosOrdem)) comum=comum.parentNode;
        if(comum && comum!==raiz){
          var blocoFnOrdem=primeiraFnOrdem, blocoCampoOrdem=primeiraPosOrdem;
          while(blocoFnOrdem.parentNode && blocoFnOrdem.parentNode!==comum)
            blocoFnOrdem=blocoFnOrdem.parentNode;
          while(blocoCampoOrdem.parentNode && blocoCampoOrdem.parentNode!==comum)
            blocoCampoOrdem=blocoCampoOrdem.parentNode;
          if(blocoFnOrdem.parentNode===comum && blocoCampoOrdem.parentNode===comum
             && blocoFnOrdem!==blocoCampoOrdem)
            comum.insertBefore(blocoFnOrdem,blocoCampoOrdem);
        }
      }
    }catch(e){}

    /* ⛔ 19/08 — A BARRA VOLTA A SER ARRASTAVEL.
       Na casca antiga a trilha era um `<input type=range>` ligado no `setBar`.
       O molde da designer desenha a trilha como dois elementos, entao o arrasto
       morreu e sobrou o `-`/`+`. Aqui a propria trilha vira o controle.
       ⛔ Usa o `setBar` da casca, que DEGRADA sozinho ate caber no orcamento —
          nao o `editBar`, que recusa e avisa. Arrastar tem que responder. */
    todos('[data-trilha]').forEach(function(el){
      var b = el.getAttribute('data-trilha');
      if (!b) return;
      el.style.cursor = _travado ? 'default' : 'ew-resize';
      el.style.opacity = _travado ? '.35' : '';
      if (_travado) return;
      var pendente = null;
      function valorDe(ev){
        var r = el.getBoundingClientRect();
        var x = (ev.touches ? ev.touches[0].clientX : ev.clientX) - r.left;
        return Math.round(Math.max(0, Math.min(1, x / (r.width || 1))) * 25);
      }
      function poeVisual(ev){
        pendente = valorDe(ev);
        var fill = el.firstElementChild;
        if (fill) fill.style.width = Math.round(pendente * 100 / 25) + '%';
      }
      function confirma(){
        if (pendente === null) return;
        var v = pendente; pendente = null;
        try{ _marca(key); }catch(e){}
        try{ setBar(key, b, v); }catch(e){}
      }
      var arrastando = false;
      function moveDoc(ev){ if (arrastando){ poeVisual(ev); ev.preventDefault(); } }
      function soltaDoc(){
        if (!arrastando) return;
        arrastando = false;
        document.removeEventListener('mousemove', moveDoc);
        document.removeEventListener('mouseup', soltaDoc);
        confirma();
      }
      el.onmousedown = function(ev){
        arrastando = true; poeVisual(ev); ev.preventDefault();
        document.addEventListener('mousemove', moveDoc);
        document.addEventListener('mouseup', soltaDoc);
      };
      el.ontouchstart = function(ev){ arrastando = true; poeVisual(ev); ev.preventDefault(); };
      el.ontouchmove = function(ev){ if (arrastando) poeVisual(ev); };
      el.ontouchend = function(){ arrastando = false; confirma(); };
    });
    todos('[data-bar]').forEach(function(el){
      el.style.cursor = _travado ? 'default' : 'pointer';
      el.style.opacity = _travado ? '.28' : '';
      el.onclick = function(){ window.t6Bar(key, el.dataset.bar, +el.dataset.d, raiz); };
    });
    todos('[data-hx]').forEach(function(el){
      el.style.cursor = 'pointer';
      el.onclick = function(){ window.t6Hab(key, 'rem', el.dataset.hx, raiz); };
    });
    todos('[data-add]').forEach(function(el){
      el.style.cursor = 'pointer';
      el.onclick = function(){ window.t6Hab(key, 'add', el.dataset.add, raiz); };
    });
    /* ⛔ 19/08 — SO O ELEMENTO MAIS INTERNO.
       Quando um `<div>` tem so um `<span>` dentro, os DOIS tem o mesmo
       textContent — e os dois recebiam o mesmo `onclick`. Clicar disparava
       duas vezes (filho + bolha no pai), e a aba ia e voltava no mesmo
       clique. Era isso que fazia "clicar trinta vezes". */
    function porTexto(txt){
      var achados = todos('span,div,b,i').filter(function(e){
        return (e.textContent || '').trim() === txt; });
      return achados.filter(function(e){
        for (var i = 0; i < achados.length; i++){
          if (achados[i] !== e && e.contains(achados[i])) return false;
        }
        return true;
      });
    }
    /* ⛔ 19/08 — AS TRES ABAS DO CARD, LIGADAS NO `encModo` DA CASCA.
       O "FAZER MINHA BUILD" chamava `minhaBuild` e `abrirAntigo`: NENHUMA DAS
       DUAS EXISTE na tela (medido). Os dois `try` caiam em silencio e o botao
       so tinha cursor de mao. Quem troca de aba de verdade e o
       `encModo(m, key)`, que a casca ja define e que pinta o `data-encmodo`. */
    /* ⛔ 19/08 — A ABA "FAZER MINHA BUILD" COMECA VAZIA.
       Ordem do Luis: *"esse impeto e adicional; na aba fazer minha build ele
       nem sequer deveria estar preenchido, assim como o tecnico tambem nao"*.
       O `zeraBarras` da casca zera as habilidades e as barras, mas puxa o
       tecnico do MEU TIME e nao mexe no impeto adicionado. Aqui os dois saem
       tambem — a aba e para ele montar com o que TEM, e ele nao tem nada
       antes de escolher. O nativo fica: veio de fabrica, nao foi escolha. */
    function _aba(m){
      if (m === 'motor'){
        window._T6ABA = 'motor';
        window._SELPOS = null;
        window._T6SELPOS_FORCADA = null;
        window._T6SELPOS_CARD = null;
        window.t6AbreMaximo(key);
        return;
      }
      if (m === 'insumos'){
        window.t6AbreLivreZerado(key);
        return;
      }
      try{ if (typeof encModo === 'function') encModo(m, key); }
      catch(e){ try{ window.ENC_MODO = m; }catch(e2){} }
      if (m !== 'motor'){
        try{
          var cc = _card(key);
          if (cc){
            cc._tec = []; cc._tecNome = '';
            try{ cc.TECB = []; }catch(e){}
          }
        }catch(e){}
        try{ if (typeof editImp === 'function') editImp(key, ''); }catch(e){}
      }
      try{ window.t6ReabreFicha(key); }catch(e){}
    }
    function ligaAba(txt, modo){
      porTexto(txt).forEach(function(el){
        /* O texto ocupa so o miolo da pilula. O clique no padding caia no pai
           sem handler e parecia exigir duas tentativas. Sobe ate o elemento
           inteiro cujo conteudo ainda e apenas o nome desta aba. */
        var bt = el;
        while (bt.parentNode && (bt.parentNode.textContent || '').trim() === txt) bt = bt.parentNode;
        bt.style.cursor = 'pointer';
        bt.onclick = function(ev){
          if (ev){ ev.preventDefault(); ev.stopPropagation(); }
          _aba(modo);
        };
      });
    }
    /* Máximo possível já estava correto e permanece com o comportamento
       original. O aumento da área clicável vale somente para a aba manual. */
    porTexto('⚡ MÁXIMO POSSÍVEL').forEach(function(el){
      el.style.cursor = 'pointer';
      el.onclick = function(){ _aba('motor'); };
    });
    ligaAba('⚙ FAZER MINHA BUILD', 'insumos');
    /* ⛔ O OTIMIZAR SO EXISTE NA ABA LIVRE.
       Na aba do MAXIMO a carta ja esta no teto: um botao "otimizar" ali nao
       tem o que fazer, e so confunde. Ordem do Luis, repetida dez vezes. */
    porTexto('⚡ OTIMIZAR').forEach(function(el){
      var alvo = el, pai = el.parentNode;
      /* sobe somente enquanto o pai inteiro ainda for o mesmo botao; assim
         some o controle completo, e nao apenas o span que contem o texto */
      while (pai && (pai.textContent || '').trim() === '⚡ OTIMIZAR'){
        alvo = pai; pai = pai.parentNode;
      }
      if (_travado){ alvo.style.display = 'none'; return; }
      alvo.style.display = '';
      alvo.style.cursor = 'pointer';
      alvo.onclick = function(){
        try{ if (typeof otimizarBarras === 'function') return otimizarBarras(key); }catch(e){}
        try{ restaurarMotor(key); }catch(e){}
      };
    });
    /* o × de fechar */
    porTexto('×').forEach(function(el){
      if (el.dataset.hx !== undefined) return;
      el.style.cursor = 'pointer';
      el.onclick = function(){
        window._T6ABA = 'motor'; window.ENC_MODO = 'motor';
        try{ fechar(); }catch(e){}
      };
    });
    /* o tecnico vira um select de verdade */
    var c = null; try{ c = _card(key); }catch(e){}
    if (c && typeof TECS !== 'undefined'){
      var atual = (c._tecNome !== undefined ? c._tecNome : c.TEC) || '';
      var alvo = porTexto((atual || '(nenhum)') + ' ▾')[0];
      if (alvo){
        var sel = document.createElement('select');
        sel.style.cssText = 'width:100%;background:transparent;border:none;color:inherit;font:inherit;cursor:pointer;outline:none';
        /* ⛔ 19/08 — O SELETOR DE TECNICO SO TINHA O NOME.
           Ordem do Luis: *"olha o tanto de R. Martinez. Como que o cara vai
           saber qual e qual? Se voce nao colocar o que ele aumenta, o cara
           nunca vai saber."*
           O nome se repete porque o MESMO tecnico aparece com combinacoes de
           bonus diferentes — o que distingue e o bonus, e ele estava fora da
           tela. Agora cada linha diz o que ela faz, em portugues, e duas
           linhas identicas (mesmo nome E mesmo bonus) viram uma so. */
        function _oQueAumenta(t){
          var bs = (t && t[1]) || [], out = [];
          for (var q = 0; q < bs.length; q++){
            var nm = bs[q];
            try{ if (typeof tecPT === 'function') nm = tecPT(bs[q]) || bs[q]; }catch(e){}
            out.push('+1 ' + nm);
          }
          return out.join(' · ');
        }
        /* Nome nao identifica tecnico: existem nomes repetidos com bonus
           diferentes. A identidade visual precisa casar nome + conjunto de
           atributos, que e exatamente o `TECB` usado no calculo da nota. */
        function _assinaturaTec(bs){
          return (bs || []).slice().sort().join('|');
        }
        var _bonusAtual = [];
        try{ _bonusAtual = (tecAtual(c) || []).slice(); }catch(e){}
        var _sigAtual = _assinaturaTec(_bonusAtual), _chSelecionada = '';
        for (var _j = 0; _j < TECS.length; _j++){
          if (TECS[_j][0] !== atual) continue;
          var _cj = TECS[_j][0] + '|' + ((TECS[_j][1] || []).join(','));
          if (!_chSelecionada) _chSelecionada = _cj;
          if (_sigAtual && _assinaturaTec(TECS[_j][1]) === _sigAtual){
            _chSelecionada = _cj; break;
          }
        }
        var _vistos = {}, _ops = ['<option value="">(nenhum)</option>'];
        for (var _i = 0; _i < TECS.length; _i++){
          var _t = TECS[_i];
          var _ch = _t[0] + '|' + ((_t[1] || []).join(','));
          if (_vistos[_ch]) continue;
          _vistos[_ch] = 1;
          var _bo = _oQueAumenta(_t);
          _ops.push('<option value="' + _i + '"' + (_ch === _chSelecionada ? ' selected' : '') + '>'
                  + esc(_t[0]) + (_bo ? '  —  ' + esc(_bo) : '') + '</option>');
        }
        sel.innerHTML = _ops.join('');
        /* Fechado, o campo mostra somente o nome. Os bonus ja aparecem na
           linha imediatamente abaixo e repeti-los aqui deixava o bloco
           redundante. Ao abrir a lista na aba editavel, a opcao selecionada
           recupera a descricao completa, igual as demais, para distinguir
           tecnicos homonimos. */
        function _compactaTec(){
          var op = sel.options[sel.selectedIndex];
          if (!op) return;
          if (!op.getAttribute('data-t6full'))
            op.setAttribute('data-t6full', op.textContent || '');
          op.textContent = atual || '(nenhum)';
        }
        function _expandeTec(){
          var op = sel.options[sel.selectedIndex];
          if (!op) return;
          var full = op.getAttribute('data-t6full');
          if (full) op.textContent = full;
        }
        _compactaTec();
        sel.onmousedown = function(){ if (!_travado) _expandeTec(); };
        sel.onkeydown = function(){ if (!_travado) _expandeTec(); };
        sel.onblur = function(){ _compactaTec(); };
        sel.onchange = function(){ window.t6Tec(key, sel.value); };
        if (_travado){
          sel.disabled = true;
          sel.style.cursor = 'default';
          sel.style.opacity = '.55';
          sel.title = 'no MÁXIMO POSSÍVEL o técnico é o que o motor escolheu — '
                    + 'para trocar, vá em FAZER MINHA BUILD';
        }
        alvo.innerHTML = '';
        alvo.style.display = 'flex';
        alvo.style.alignItems = 'center';
        alvo.style.gap = '8px';
        alvo.appendChild(sel);
        /* ⛔ 19/08 — O `×` EM TUDO QUE FOI ADICIONADO.
           Ordem do Luis: habilidade, tecnico e impeto adicional tem que ter
           como tirar. O nativo NAO leva `×` — ele veio de fabrica, nao foi
           escolha de ninguem. */
        if (!_travado && atual){
          var xt = document.createElement('b');
          xt.textContent = '×';
          xt.title = 'tirar o técnico';
          xt.style.cssText = 'cursor:pointer;color:var(--d13);font-size:15px;line-height:1;flex:none';
          xt.onclick = function(){ window.t6Tec(key, ''); };
          alvo.appendChild(xt);
        }
        /* Tecnicos equivalentes: usa somente a lista medida pelo motor/tela.
           Linhas antigas sem essa informacao permanecem sem sugestao. */
        try{
          var iguais = (typeof tecIguais === 'function') ? (tecIguais(c) || []) : (c.TECIG || []);
          if (alvo.parentNode){
            var sgTec = document.createElement('div');
            sgTec.setAttribute('data-t6tecsug', '1');
            sgTec.style.cssText = 'display:flex;flex-direction:column;gap:6px;margin-top:8px';
            sgTec.innerHTML = '<span style="font-family:inherit;font-size:9.5px;letter-spacing:1.2px;color:var(--d17)">TÉCNICOS SUGERIDOS · MESMA NOTA</span>'
              + '<div style="display:flex;gap:6px;flex-wrap:wrap;min-height:28px">'
              + (iguais.length
                ? iguais.slice(0,5).map(function(n){ return '<span style="font-size:11.5px;padding:5px 9px;border-radius:7px;background:var(--d14);border:1px solid var(--d18);color:var(--d85)">' + esc(n) + '</span>'; }).join('')
                : '<span style="font-size:11px;color:var(--d17);padding:4px 0">nenhum técnico equivalente para esta build</span>')
              + '</div>';
            /* Fica dentro da secao TECNICO, antes da linha que inicia IMPETO.
               `alvo.parentNode` e a coluna inteira; anexar no fim jogava as
               sugestoes para baixo de todo o bloco de impeto. */
            /* Limita a procura ao cartao que contem o titulo TECNICO. Antes,
               `porTexto('IMPETO')[0]` podia achar outro bloco da ficha e a
               sugestao sumia ou aparecia no lugar errado. */
            var titTec = porTexto('TÉCNICO').filter(function(x){
              return x && x.parentNode && x.parentNode.contains(alvo);
            })[0];
            var caixaTec = titTec ? titTec.parentNode : alvo.parentNode;
            var titImp = null;
            try{
              titImp = Array.prototype.slice.call(caixaTec.children || []).filter(function(x){
                return (x.textContent || '').trim() === 'ÍMPETO';
              })[0] || null;
            }catch(e){}
            if (titImp && titImp.parentNode === caixaTec){
              var ponto = titImp;
              var ant = titImp.previousElementSibling;
              if (ant && ((ant.getAttribute('style') || '').indexOf('border-top') >= 0)) ponto = ant;
              caixaTec.insertBefore(sgTec, ponto);
            } else {
              caixaTec.appendChild(sgTec);
            }
          }
        }catch(e){}
      }
    }
    /* ⛔ 19/08 — ARRASTAR A SUGESTAO PARA DENTRO DAS ADICIONADAS.
       Ordem do Luis: *"teria que dar um jeito de arrastar as sugestoes de
       habilidade e colocar elas dentro do grupo de adicionadas. Se ja tivesse
       cinco ela nao fica — mas se arrastar pra cima de alguma outra, TROCA."*
       Duas regras, e as duas estao aqui:
         soltar no VAZIO do grupo .... entra, se houver vaga
         soltar EM CIMA de uma ....... troca as duas, mesmo com o grupo cheio
       ⛔ `<button>` nao inicia arrasto nativo no Chrome — por isso os chips
          sao `<span>` com `draggable`, e o `×` leva `pointer-events` proprio. */
    (function(){
      if (_travado) return;
      var sugs = todos('[data-add]');
      var adds = todos('[data-hx]').map(function(x){ return x.parentNode; });

      sugs.forEach(function(el){
        el.setAttribute('draggable', 'true');
        el.style.cursor = 'grab';
        el.addEventListener('dragstart', function(ev){
          try{ ev.dataTransfer.setData('text/plain', el.getAttribute('data-add')); }catch(e){}
          try{ ev.dataTransfer.effectAllowed = 'copy'; }catch(e){}
          el.style.opacity = '.45';
        });
        el.addEventListener('dragend', function(){ el.style.opacity = ''; });
      });

      function solta(nome, trocaCom){
        if (!nome) return;
        var c2 = null; try{ c2 = _card(key); }catch(e){}
        if (!c2) return;
        var atuais = [];
        try{ atuais = (habsAtual(c2) || []).slice(); }catch(e){}
        if (atuais.indexOf(nome) >= 0) return;
        if (trocaCom !== null && trocaCom !== undefined && atuais[trocaCom] !== undefined){
          atuais[trocaCom] = nome;
        } else {
          var teto = 5;
          try{ if (c2.vagas !== undefined && c2.vagas !== null) teto = +c2.vagas; }catch(e){}
          if (atuais.length >= teto){
            window.t6AvisoBar(raiz, 'já tem ' + teto + ': solte em cima de uma para trocar');
            return;
          }
          atuais.push(nome);
        }
        try{ _marca(key); }catch(e){}
        try{ window._trocaHabs(key, atuais); }catch(e){ return; }
        /* a troca acima ja redesenha; nao repetir a ficha inteira */
      }

      /* soltar EM CIMA de uma adicionada = troca */
      adds.forEach(function(chip){
        if (!chip) return;
        var ix = +chip.querySelector('[data-hx]').getAttribute('data-hx');
        chip.addEventListener('dragover', function(ev){
          ev.preventDefault();
          chip.style.outline = '2px solid var(--d25)';
        });
        chip.addEventListener('dragleave', function(){ chip.style.outline = ''; });
        chip.addEventListener('drop', function(ev){
          ev.preventDefault(); ev.stopPropagation();
          chip.style.outline = '';
          var nome = '';
          try{ nome = ev.dataTransfer.getData('text/plain'); }catch(e){}
          solta(nome, ix);
        });
      });

      /* soltar no grupo = entra, se couber */
      var grupo = adds.length ? adds[0].parentNode : null;
      if (!grupo){
        var vazio = porTexto('nenhuma')[0];
        grupo = vazio ? vazio.parentNode : null;
      }
      if (grupo){
        grupo.addEventListener('dragover', function(ev){
          ev.preventDefault();
          grupo.style.background = 'rgba(125,242,168,.08)';
          grupo.style.borderRadius = '9px';
        });
        grupo.addEventListener('dragleave', function(){ grupo.style.background = ''; });
        grupo.addEventListener('drop', function(ev){
          ev.preventDefault();
          grupo.style.background = '';
          var nome = '';
          try{ nome = ev.dataTransfer.getData('text/plain'); }catch(e){}
          solta(nome, null);
        });
      }

      /* ⛔ E O CATALOGO INTEIRO, para o que nao esta nas sugeridas.
         As sugeridas sao so as NEUTRAS (as que nao mudam a nota). O Luis quer
         poder pôr uma que muda — e a nota muda junto, que e o certo. */
      var alvoCat = porTexto('HABILIDADES SUGERIDAS')[0];
      if (alvoCat && alvoCat.parentNode && !raiz.querySelector('[data-t6cat]')){
        var todasHab = [];
        try{
          var jaTem = [];
          try{ jaTem = (habsAtual(_cardAqui) || []); }catch(e){}
          var nat = ((_cardAqui && _cardAqui.fab) || []).concat((_cardAqui && _cardAqui.raras) || []);
          var _catalogoHab = window.HABEF;
          if (!_catalogoHab && typeof HABEF !== 'undefined') _catalogoHab = HABEF;
          todasHab = Object.keys(_catalogoHab || {}).filter(function(n){
            return jaTem.indexOf(n) < 0 && nat.indexOf(n) < 0 && !_ehEspecial(n); })
            .sort(function(x, y){ return x.localeCompare(y, 'pt'); });
        }catch(e){}
        if (todasHab.length){
          var cx = document.createElement('div');
          cx.setAttribute('data-t6cat', '1');
          cx.style.cssText = 'display:flex;align-items:center;gap:8px;margin-top:8px';
          var selc = document.createElement('select');
          selc.style.cssText = 'flex:1 1 auto;min-width:0;background:var(--d10);'
            + 'border:1px solid var(--d18);color:var(--d8);font:inherit;font-size:11.5px;'
            + 'padding:5px 8px;border-radius:7px;cursor:pointer';
          selc.innerHTML = '<option value="">Selecionar habilidade</option>'
            + todasHab.map(function(n){
                return '<option>' + esc(_extenso(n)) + '</option>'; }).join('');
          selc.onchange = function(){
            var v = selc.selectedIndex > 0 ? todasHab[selc.selectedIndex - 1] : '';
            selc.selectedIndex = 0;
            if (v) window.t6Hab(key, 'add', v, raiz);
          };
          cx.appendChild(selc);
          alvoCat.parentNode.appendChild(cx);
        }
      }
    })();

    /* ⛔ 19/08 — O PAINEL DE ESCOLHA DA POSICAO, DE VOLTA.
       Regra do Luis, de 15/08 e repetida em 19/08: clicar numa posicao NAO abre
       ficha quando ela faz mais de uma funcao — ele escolhe qual quer ver.
       Quando faz uma so, abre direto. Era o `pedeFuncao` da casca antiga; ele
       casava por classe CSS (`.cbfn.cbfnq`) e o molde da designer nao tem
       classe nenhuma, entao morreu junto com o desenho velho. */
    (function(){
      var velho = raiz.querySelector('[data-t6pede]');
      var pos = window._T6PENDENTE_POS;
      if (!pos){ if (velho) velho.remove(); return; }
      var c = null;
      try{ c = _card(key); }catch(e){}
      if (!c) return;
      var irm = [];
      try{
        var bb = String(c.id).split('@')[0];
        irm = _t6IrmasUnicas(c);
      }catch(e){ irm = [c]; }
      var fs = _funcsDaPos(pos, c, irm);
      if (fs.length < 2){ if (velho) velho.remove(); return; }
      var botoesFn = todos('[data-fn]');
      if (!botoesFn.length) return;
      var listaFn = botoesFn[0].parentNode;
      if (!listaFn) return;
      listaFn.style.position = 'relative';
      listaFn.style.isolation = 'isolate';
      botoesFn.forEach(function(bt){
        bt.style.pointerEvents = 'none';
        bt.style.filter = 'brightness(.42) saturate(.55)';
        bt.style.opacity = '.48';
      });
      /* Na ficha atual o painel ja veio no HTML. Basta ligar as escolhas. */
      if (velho){
        /* A decisao fica no fim da lista, imediatamente antes do campinho.
           No topo ela podia ficar fora da area visivel depois do clique. */
        listaFn.appendChild(velho);
        todos('[data-t6pickfn]').forEach(function(bt){
          bt.onclick = function(ev){
            if (ev){ ev.preventDefault(); ev.stopPropagation(); }
            window._T6PENDENTE_POS = null;
            window._SELPOS = pos; window._T6SELPOS_FORCADA = pos;
            window._T6SELPOS_CARD = String(c.id).split('@')[0];
            window.t6AbreFuncao(bt.getAttribute('data-t6pickfn'));
          };
        });
        return;
      }
      var caixa = document.createElement('div');
      caixa.setAttribute('data-t6pede', '1');
      caixa.style.cssText = 'position:relative!important;z-index:999!important;width:100%;padding:16px 15px;'
        + 'margin:0 0 10px;border-radius:12px;display:flex!important;flex-direction:column;'
        + 'justify-content:flex-start;align-items:stretch;flex:0 0 auto;'
        + 'background:rgba(8,18,13,.985);border:1.5px solid var(--d25);box-shadow:0 10px 26px var(--d104)';
      var tit = document.createElement('div');
      tit.style.cssText = 'font-family:inherit;font-size:12px;font-weight:800;letter-spacing:.5px;color:var(--d25);margin-bottom:3px';
      tit.textContent = 'ESCOLHA A FUNÇÃO PARA ' + _sig(pos);
      var sub2 = document.createElement('div');
      sub2.style.cssText = 'font-size:12px;color:var(--d30);margin-bottom:11px';
      sub2.textContent = 'Cada função tem uma build diferente. Selecione qual você quer abrir:';
      var linha = document.createElement('div');
      linha.setAttribute('data-t6controles-build', '1');
      linha.style.cssText = 'display:flex;gap:8px;flex-wrap:wrap';
      fs.forEach(function(f){
        var alvo = null;
        for (var i = 0; i < irm.length; i++) if (irm[i].tipo === f){ alvo = irm[i]; break; }
        var b = document.createElement('button');
        var nt = 0;
        try{ nt = alvo ? _notaDoMotorPos(alvo,pos) : 0; }catch(e){}
        b.style.cssText = 'display:flex;align-items:center;gap:9px;font-family:inherit;font-size:12px;'
          + 'font-weight:700;padding:9px 13px;border-radius:9px;cursor:pointer;'
          + 'background:var(--d14);border:1px solid var(--d31);color:var(--d1)';
        var psFallback = alvo ? _posDaFuncao(alvo.tipo, c) : [];
        if (alvo && !psFallback.length) psFallback = _posFn(alvo);
        var basFallbackTem = alvo && pos
          ? (_estiloLigaNaPos(alvo, pos) === false)
          : alvo && psFallback.some(function(pp){ return _estiloLigaNaPos(alvo, pp) === false; });
        var basFallback = basFallbackTem
          ? '<small style="font-family:inherit;font-size:8px;font-weight:800;letter-spacing:.6px;'
            + 'padding:2px 6px;border-radius:4px;background:var(--d14);border:1px solid var(--d31);'
            + 'color:var(--d17)">BÁSICO</small>' : '';
        b.innerHTML = '<span style="display:flex;align-items:center;gap:7px">'
          + '<span>' + esc(_nomeFn(f)) + '</span>' + basFallback + '</span>'
          + '<b style="font-family:inherit;font-weight:800;color:var(--d25)">' + n2(nt) + '</b>';
        b.onclick = function(ev){
          if (ev){ ev.preventDefault(); ev.stopPropagation(); }
          window._T6PENDENTE_POS = null;
          window._SELPOS = pos;
          window._T6SELPOS_FORCADA = pos;
          window._T6SELPOS_CARD = String(c.id).split('@')[0];
          var destino = (alvo ? alvo.id : c.id) + '|' + (alvo ? alvo.tipo : f);
          window.t6AbreFuncao(destino);
        };
        linha.appendChild(b);
      });
      caixa.appendChild(tit); caixa.appendChild(sub2); caixa.appendChild(linha);
      /* Depois da ultima funcao: como a coluna foi invertida, este e o ponto
         imediatamente acima do campinho. */
      listaFn.appendChild(caixa);
    })();

    /* qual aba esta aberta — a pilula acesa */
    [['⚡ MÁXIMO POSSÍVEL', 'motor'], ['⚙ FAZER MINHA BUILD', 'livre']]
      .forEach(function(par){
        porTexto(par[0]).forEach(function(el){
          var on = (_modo === par[1]);
          el.style.opacity = on ? '1' : '.55';
          el.style.filter  = on ? '' : 'grayscale(1)';
        });
      });

    /* ⛔ 19/08 — A BARRA DA BUILD, INTEIRA, DE VOLTA.
       Ordem do Luis: *"a gente tinha no encaixe anterior alguns botoes perto
       dessas barras, como salvar a build, que era onde o cara salvava a build
       no time dele, la na aba MEU TIME. Voce sumiu com eles."*
       Ele esta certo: os botoes existem na casca desde 16/08 (`bldSalva`,
       `bldCopiaDoMaximo`, `bldUsa`, `bldApaga`) e ficaram ORFAOS — a barra
       deles era encaixada ao lado de um `.bhd`, e o molde da designer nao tem
       classe nenhuma. As funcoes continuam sendo as da casca; o que muda e
       so onde a barra e pendurada.
       ⛔ So na aba FAZER MINHA BUILD: na aba do MAXIMO nao ha build do
          usuario para salvar — a build de la e a do motor. */
    (function(){
      var velha = raiz.querySelector('[data-t6bld]');
      if (velha) velha.remove();
      if (_travado) return;
      /* ⛔ 19/08 — A BARRA MORA NA MESMA LINHA DO OTIMIZAR.
         Ordem do Luis: *"isso aqui ficaria melhor ao lado do botao otimizar,
         caso ele fosse menor"*. Entao o OTIMIZAR deixa de ocupar a largura
         toda e divide a linha com o SALVAR e o COPIAR. */
      var oti = porTexto('⚡ OTIMIZAR')[0];
      var botaoOti = null;
      if (oti){
        botaoOti = oti;
        for (var t0 = 0; t0 < 3 && botaoOti.parentNode; t0++){
          if ((botaoOti.parentNode.textContent || '').trim() !== '⚡ OTIMIZAR') break;
          botaoOti = botaoOti.parentNode;
        }
      }
      var caixa = null;
      if (!botaoOti){
        var alvo = porTexto('DISTRIBUIÇÃO DOS PONTOS')[0];
        if (!alvo) return;
        caixa = alvo.parentNode;
        for (var t = 0; t < 3 && caixa && caixa.parentNode; t++) caixa = caixa.parentNode;
        if (!caixa || !caixa.parentNode) return;
      }

      var c = null; try{ c = _card(key); }catch(e){}
      var idb = String(key).split('|')[0].split('@')[0];
      var salvas = [], ativa = -1, TETO = 5;
      try{
        salvas = (MT.builds && MT.builds[idb]) || [];
        ativa = (MT.buildOn && MT.buildOn[idb] !== undefined) ? MT.buildOn[idb] : -1;
      }catch(e){ salvas = []; }

      var bar = document.createElement('div');
      bar.setAttribute('data-t6bld', '1');
      /* O aviso de salvamento e apenas uma legenda. O bloco nao recebe fundo,
         borda nem moldura: somente os controles continuam parecendo botoes. */
      bar.style.cssText = 'display:flex;flex-direction:column;gap:8px;margin:0 0 12px;'
        + 'padding:0;background:transparent;border:0';

      var linha = document.createElement('div');
      linha.style.cssText = 'display:flex;gap:8px;align-items:center;flex-wrap:wrap';
      var E_BT = 'font-family:inherit;font-size:11.5px;font-weight:800;letter-spacing:.3px;'
               + 'padding:9px 15px;border-radius:8px;cursor:pointer;border:1px solid var(--d31);';

      var bSalvar = document.createElement('button');
      bSalvar.textContent = '✔ SALVAR MINHA BUILD';
      bSalvar.title = 'guarda esta build no seu elenco';
      bSalvar.style.cssText = E_BT + 'background:var(--d25);border-color:var(--d25);color:#06200f';
      bSalvar.onclick = function(){
        try{
          if (typeof window.bldSalvaDireto === 'function') return window.bldSalvaDireto(key, c.tipo);
          if (typeof window.bldSalva === 'function') return window.bldSalva();
        }catch(e){
          try{ console.error('[salvar build]', e); }catch(_e){}
        }
        window.t6AvisoBar(raiz, 'não consegui salvar');
      };

      var bCopiar = document.createElement('button');
      bCopiar.textContent = '⧉ COPIAR DO MÁXIMO POSSÍVEL';
      bCopiar.title = 'traz tudo do MÁXIMO POSSÍVEL pra cá; daqui você vai tirando o que não tem';
      bCopiar.style.cssText = E_BT + 'background:var(--d14);color:var(--d8)';
      bCopiar.onclick = function(){
        window._T6_COPIOU_MAX = window._T6_COPIOU_MAX || {};
        window._T6_COPIOU_MAX[idb] = 1;
        try{ if (typeof window.bldCopiaDoMaximo === 'function') return window.bldCopiaDoMaximo(); }catch(e){}
        window.t6AvisoBar(raiz, 'não consegui copiar');
      };

      var bLimpar = document.createElement('button');
      bLimpar.textContent = 'LIMPAR TUDO';
      bLimpar.title = 'limpa barras, técnico, ímpeto e habilidades preenchidos por você';
      bLimpar.style.cssText = E_BT + 'background:transparent;color:var(--d17)';
      bLimpar.onclick = function(){
        try{
          /* Usa exatamente a mesma porta de entrada da aba manual. O caminho
             antigo chamava `aplicaNaTela`, que reaproveitava caches e podia
             deixar barras/nota/insumos do maximo na tela. */
          if (typeof window.t6AbreLivreZerado === 'function'){
            window.t6AbreLivreZerado(key);
            return;
          }
          throw new Error('reset da carta-base indisponivel');
        }catch(e){ window.t6AvisoBar(raiz, 'não consegui limpar'); }
      };

      /* ⛔ o OTIMIZAR nao se repete aqui: ele e o botao grande do fim do
         bloco das barras, e ja usa os insumos que estao na tela. */
      linha.appendChild(bSalvar); linha.appendChild(bCopiar); linha.appendChild(bLimpar);
      bar.appendChild(linha);

      var txt = document.createElement('div');
      txt.style.cssText = 'font-size:11.5px;line-height:1.35;color:var(--d30);padding:1px 2px';
      txt.innerHTML = 'vai salvar como <b style="color:var(--d1)">'
        + esc(_nomeFn(c ? c.tipo : '')) + '</b> · '
        + salvas.length + ' de ' + TETO + ' builds guardadas desta carta';
      bar.appendChild(txt);

      if (salvas.length){
        var chips = document.createElement('div');
        chips.style.cssText = 'display:flex;gap:7px;flex-wrap:wrap';
        salvas.forEach(function(b, i){
          var ch = document.createElement('span');
          var on = (i === ativa);
          ch.style.cssText = 'display:flex;align-items:center;gap:7px;font-size:11px;font-weight:700;'
            + 'padding:5px 8px 5px 11px;border-radius:8px;cursor:pointer;'
            + (on ? 'background:linear-gradient(180deg,var(--d114),var(--d115));'
                    + 'border:1px solid var(--d116);color:var(--d117)'
                  : 'background:var(--d14);border:1px solid var(--d31);color:var(--d8)');
          ch.innerHTML = '<b style="font-weight:700">' + esc(String(b.nome || ('build ' + (i + 1))))
            + '</b><u style="text-decoration:none;font-family:inherit;font-weight:800;opacity:.85">'
            + n2(+b.n || 0) + '</u>';
          ch.title = 'usar esta build no seu elenco';
          ch.onclick = function(){
            try{ if (typeof window.bldUsa === 'function') window.bldUsa(idb, i); }catch(e){}
          };
          var x = document.createElement('i');
          x.textContent = '×';
          x.title = 'apagar esta build';
          x.style.cssText = 'font-style:normal;font-size:13px;line-height:1;opacity:.7;padding:0 2px';
          x.onclick = function(ev){
            ev.stopPropagation();
            try{ if (typeof window.bldApaga === 'function') window.bldApaga(idb, i); }catch(e){}
          };
          ch.appendChild(x);
          chips.appendChild(ch);
        });
        bar.appendChild(chips);
      }

      if (botaoOti && botaoOti.parentNode){
        /* o OTIMIZAR encolhe e a linha recebe todos os controles da build. */
        var linhaOti = document.createElement('div');
        linhaOti.setAttribute('data-t6bld', '1');
        linhaOti.setAttribute('data-t6controles-build', '1');
        linhaOti.style.cssText = 'display:flex;gap:8px;align-items:stretch;flex-wrap:wrap;margin-top:10px';
        botaoOti.parentNode.insertBefore(linhaOti, botaoOti);
        botaoOti.style.width = 'auto';
        botaoOti.style.flex = '1 1 200px';
        botaoOti.style.margin = '0';
        linhaOti.appendChild(botaoOti);
        bSalvar.style.flex = '0 0 auto';
        bCopiar.style.flex = '0 0 auto';
        bLimpar.style.flex = '0 0 auto';
        linhaOti.appendChild(bSalvar);
        linhaOti.appendChild(bCopiar);
        linhaOti.appendChild(bLimpar);
        /* o texto e as builds guardadas ficam logo abaixo da linha */
        bar.removeChild(linha);
        bar.style.marginTop = '9px';
        bar.style.marginBottom = '0';
        linhaOti.parentNode.insertBefore(bar, linhaOti.nextSibling);
      } else {
        caixa.parentNode.insertBefore(bar, caixa);
      }
    })();

    /* os balõezinhos dos `i` — a designer escreveu o texto, faltava fazer valer */
    try{ window.t6Hover(raiz); }catch(e){}

    /* ⛔ 19/08 — OS BOTOES DO CONDICIONAL, AGORA PELO DADO.
       Antes eles eram achados por TEXTO: `porTexto('+1')` casava com qualquer
       elemento cujo texto fosse "+1" — inclusive as CELULAS DA TABELA DE
       ATRIBUTOS, que estao cheias de "+1". Metade dos cliques ia parar num
       atributo, e o botao de verdade chamava `toggleCondCard`, que so cicla e
       ainda estava travado fora da aba livre.
       Agora cada botao carrega o proprio degrau (`data-cond`) e chama o
       `setCondCard(key, degrau)` da casca, que troca a build inteira que o
       motor gravou para aquele degrau. Degrau que o motor nao calculou fica
       apagado e nao responde. */
    todos('[data-cond]').forEach(function(el){
      var g = +el.getAttribute('data-cond');
      var existe = (g === 1);
      try{ existe = existe || !!(_cardAqui && _cardAqui.CD && _cardAqui.CD[String(g)]); }catch(e){}
      if (!existe) return;
      el.style.cursor = 'pointer';
      el.onclick = function(){
        try{ if (typeof setCondCard === 'function') return setCondCard(key, g); }catch(e){}
        try{ toggleCondCard(key); }catch(e){}
      };
    });

    /* o seletor do impeto ADICIONADO — so na aba FAZER MINHA BUILD.
       Algumas variantes do molde eliminam o `data-impsel` vazio ao montar o
       cartao. Nesse caso, recria-se a ancora dentro do proprio cartao de
       "vaga livre"; o usuario nunca fica apenas com a legenda sem controle. */
    if (!_travado && !todos('[data-impsel]').length){
      var vagaImp = porTexto('vaga livre')[0];
      if (vagaImp){
        var cardImp = vagaImp;
        for (var vi=0; vi<4 && cardImp.parentNode; vi++){
          if ((cardImp.getAttribute && (cardImp.getAttribute('style')||'').indexOf('border-radius:12px') >= 0)) break;
          cardImp = cardImp.parentNode;
        }
        if (cardImp && cardImp.appendChild){
          var ancoraImp = document.createElement('div');
          ancoraImp.setAttribute('data-impsel','1');
          ancoraImp.style.cssText = 'display:flex;align-items:center;gap:8px;margin-top:7px;width:100%';
          cardImp.appendChild(ancoraImp);
        }
      }
    }
    todos('[data-impsel]').forEach(function(el){
      el.innerHTML = '';
      if (_travado){
        el.style.display = 'none';
        return;
      }
      var ops = [];
      try{ ops = (typeof impOpcoes === 'function') ? (impOpcoes(_cardAqui) || []) : []; }catch(e){}
      var atual = '';
      try{ atual = (typeof impAdicionado === 'function') ? (impAdicionado(_cardAqui) || '') : ''; }catch(e){}
      var sel = document.createElement('select');
      sel.style.cssText = 'flex:1 1 auto;min-width:0;background:var(--d10);border:1px solid var(--d18);'
        + 'color:var(--d8);font:inherit;font-size:11.5px;padding:5px 8px;border-radius:7px;cursor:pointer';
      var html = '<option value="">(nenhum)</option>';
      for (var q = 0; q < ops.length; q++){
        html += '<option' + (ops[q] === atual ? ' selected' : '') + '>' + esc(ops[q]) + '</option>';
      }
      sel.innerHTML = html;
      sel.onchange = function(){
        try{ editImp(key, sel.value); }catch(e){}
      };
      el.appendChild(sel);
      if (atual){
        var x = document.createElement('b');
        x.textContent = '×';
        x.title = 'tirar este ímpeto';
        x.style.cssText = 'cursor:pointer;color:var(--d13);font-size:14px;line-height:1;flex:none';
        x.onclick = function(){ try{ editImp(key, ''); }catch(e){} };
        el.appendChild(x);
      }
    });
  };

  window.t6Melhores = function(lista, quantos){
    var por = {};
    lista.forEach(function(c){
      var k = c.nome, v = pct(c);
      if (!por[k] || v > por[k][1]) por[k] = [c, v];
    });
    return Object.keys(por).map(function(k){ return por[k]; })
      .sort(function(a, b){ return b[1] - a[1]; })
      .slice(0, quantos || 3).map(function(x){ return x[0]; });
  };
})();

/* ========================================================================
   PAGINA DINAMICA DO CARD — 19/08/2026

   Uma unica pagina atende todos os cards. O identificador e a funcao ficam
   na URL; a ficha aprovada continua sendo desenhada pelo mesmo `t6TelaFicha`.
   O modal nao foi apagado: o commit 2865f5c e o arquivo de checkpoint guardam
   exatamente o estado anterior a esta mudanca.
   ======================================================================== */
(function(){
  if (window.T6_PAGINA_CARD) return;
  window.T6_PAGINA_CARD = 1;

  var css = document.createElement('style');
  css.textContent = [
    'html[data-t6pagina="card"],html[data-t6pagina="card"] body{min-height:100%;background:var(--d3,#07100b)}',
    'html[data-t6pagina="card"] body{overflow:auto!important}',
    'html[data-t6pagina="card"] #filtros,html[data-t6pagina="card"] body>main{display:none!important}',
    'html[data-t6pagina="card"] #ov{position:relative!important;inset:auto!important;display:block!important;',
      'z-index:1!important;overflow:visible!important;min-height:calc(100vh - 72px);padding:20px 18px 92px!important;',
      'background:var(--d3,#07100b)!important}',
    'html[data-t6pagina="card"] #box{max-width:1440px;margin:0 auto}',
    'html[data-t6pagina="card"] #voltar{display:block!important;position:fixed!important;z-index:80!important}',
    '@media(max-width:700px){html[data-t6pagina="card"] #ov{padding:8px 0 82px!important}}'
  ].join('');
  (document.head || document.documentElement).appendChild(css);

  function partes(key){
    var s=String(key||''), i=s.indexOf('|');
    return i<0 ? [s,''] : [s.slice(0,i),s.slice(i+1)];
  }
  function urlDaFicha(key){
    var p=partes(key), u=new URL(location.href);
    u.searchParams.set('card',String(p[0]).split('@')[0]);
    u.searchParams.set('funcao',p[1]);
    u.searchParams.set('modo',(typeof window.t6Modo==='function'&&window.t6Modo()==='livre')?'minha-build':'maximo');
    return u.pathname+u.search+u.hash;
  }
  function ativa(key){
    if(!key) return;
    var jaEstavaNaFicha=document.documentElement.getAttribute('data-t6pagina')==='card';
    document.documentElement.setAttribute('data-t6pagina','card');
    try{ document.body.setAttribute('data-t6pagina','card'); }catch(e){}
    try{
      var st={ficha:1,paginaCard:1,key:String(key)};
      history.replaceState(st,'',urlDaFicha(key));
    }catch(e){}
    /* So a entrada vinda da home comeca no topo. Trocar funcao, posicao ou
       aba dentro da ficha conserva exatamente o ponto de leitura. */
    if(!jaEstavaNaFicha) try{ window.scrollTo(0,0); }catch(e){}
  }
  function desativa(){
    document.documentElement.removeAttribute('data-t6pagina');
    try{ document.body.removeAttribute('data-t6pagina'); }catch(e){}
  }
  window.t6PaginaAtiva=ativa;
  window.t6PaginaDesativa=desativa;

  function liga(){
    if(typeof window.abrir!=='function') return setTimeout(liga,250);
    if(window._t6AbrirPagina) return;
    window._t6AbrirPagina=window.abrir;
    window.abrir=function(key){
      /* Ao sair da home, a linha clicada serve para identificar o CARD, nao
         para escolher sua funcao inicial. A pagina comeca na melhor funcao
         ligada a posicao nativa. URL direta/F5 conserva a funcao da URL. */
      try{
        var qp=new URLSearchParams(location.search);
        var entrando=!document.documentElement.getAttribute('data-t6pagina') && !qp.get('card');
        if(entrando){
          var pc=partes(key), base=String(pc[0]).split('@')[0], cc=_card(key);
          window._T6_INICIAL_CARD=window._T6_INICIAL_CARD||{};
          window._T6_INICIAL_CARD[base]=1;
          var inicial=(typeof window.t6InicialDaPosicaoNativa==='function')
            ? window.t6InicialDaPosicaoNativa(cc) : null;
          if(inicial) key=inicial.id+'|'+inicial.tipo;
        }
      }catch(e){}
      var r=window._t6AbrirPagina.call(this,key);
      ativa(key);
      return r;
    };
    /* `reabrir` usa o `abrir` global e, portanto, mantem a pagina e atualiza
       funcao/modo na URL sem criar outra ficha nem outra pagina fisica. */
    var fecharAnterior=window.fechar;
    if(typeof fecharAnterior==='function'){
      window.fechar=function(){
        desativa();
        return fecharAnterior.apply(this,arguments);
      };
    }
    abreDaUrl();
  }

  function abreDaUrl(){
    var q=new URLSearchParams(location.search), id=q.get('card'), fn=q.get('funcao');
    if(!id) return;
    var base=String(id).split('@')[0], abriu=false, cargaCompleta=!!fn;
    function abreQuandoDisponivel(){
      if(abriu) return true;
      /* Sem funcao na URL, espera todas as linhas do card e aplica a regra de
         entrada: posicao nativa primeiro, maior funcao dela depois. */
      if(!fn && !cargaCompleta) return false;
      var c=null, primeira=null;
      try{
        primeira=(typeof D!=='undefined'?D:[]).find(function(x){
          return String(x.id).split('@')[0]===base;
        });
        c=fn ? (typeof D!=='undefined'?D:[]).find(function(x){
          return String(x.id).split('@')[0]===base && x.tipo===fn;
        }) : ((typeof window.t6InicialDaPosicaoNativa==='function' && primeira)
          ? window.t6InicialDaPosicaoNativa(primeira) : primeira);
      }catch(e){}
      if(!c) return false;
      abriu=true;
      var key=c.id+'|'+c.tipo;
      try{ window._T6ABA=q.get('modo')==='minha-build'?'livre':'motor'; }catch(e){}
      try{ window.ENC_MODO=window._T6ABA; }catch(e){}
      window.abrir(key);
      if(q.get('modo')==='minha-build' && typeof window.t6AbreLivreZerado==='function')
        window.t6AbreLivreZerado(key);
      return true;
    }
    /* No F5 a home ainda nao carregou a linha do card. Busca diretamente as
       linhas desse card antes de abrir a ficha; assim a URL e uma rota real,
       e nao depende da busca/listagem da pagina inicial ter sido montada. */
    var tentativas=0;
    (function esperaD(){
      if(typeof D==='undefined' && ++tentativas<80) return setTimeout(esperaD,100);
      if(abreQuandoDisponivel()) return;
      var url='https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/tela_encaixe'
        +'?select=linha&card_id=eq.'+encodeURIComponent(base)+'&order=funcao.asc';
      var chave='sb_publishable_XTKGboY9RyYiirPiIsWMhw_P8B51cHj';
      fetch(url,{headers:{apikey:chave,Authorization:'Bearer '+chave}})
       .then(function(r){ if(!r.ok) throw new Error('HTTP '+r.status); return r.json(); })
       .then(function(rows){
         (rows||[]).forEach(function(r){
           var x=r&&r.linha;
           if(!x||x.id===undefined||x.tipo===undefined) return;
           var repetida=false;
           for(var i=0;i<D.length;i++){
             var ja=D[i];
             if(ja&&ja.id!=='MOLDE'&&String(ja.id).split('@')[0]===base
                && (typeof _mesmaFn==='function'?_mesmaFn(ja.tipo,x.tipo):ja.tipo===x.tipo)){
               repetida=true; break;
             }
           }
           if(!repetida) D.push(x);
         });
         try{ if(typeof _pos_D==='function') _pos_D(); }catch(e){}
         cargaCompleta=true;
         abreQuandoDisponivel();
       })
       .catch(function(){
         /* Uma falha temporaria nao transforma a rota em home: conserva o
            estado de pagina e tenta de novo por alguns segundos. */
         var n=0;(function tenta(){
           if(abreQuandoDisponivel()||++n>40)return;
           setTimeout(tenta,250);
         })();
       });
    })();
  }

  window.addEventListener('popstate',function(){
    var q=new URLSearchParams(location.search);
    if(!q.get('card')) desativa();
  });
  liga();
})();
</script>
"""


def js_telas():
    """O bloco pronto: o motor + os moldes da designer embutidos."""
    import json
    return JS_TELAS.replace('__MOLDES__', json.dumps(MOLDES, ensure_ascii=False))
