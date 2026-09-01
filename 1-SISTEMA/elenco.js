/* bloco JavaScript 21 */

/* ===================================================================
   O VISUAL DO MODAL — 15/08/2026, 2a leva (ordens do Luis)
   ⛔ SO APARENCIA. Nao encosta em nota, motor, banco nem chave de funcao.
      Ordem dele: "isso ai e so o visual, so o que aparece na tela".

    1  o nome do card maior
    2  a coluna da nota em BLOQUINHOS: "pontuacao total" no lugar de
       "nota final", "% do topo" no lugar de "% top", "Pode Melhorar"
    3  a aba "DO MEU JEITO" vira "LIVRE"
    4  o titulo ATRIBUTOS centralizado
    5  o FISICO num bloco so, medidas em TRES COLUNAS, e o ESTILO DE
       JOGO DA IA na quarta coluna
    6  o titulo do campinho: o nome da posicao por extenso e sem negrito,
       so a sigla em negrito
    7  as tres colunas do painel com a MESMA largura (a distribuicao dos
       pontos ocupava o espaco das outras duas)
    8  IMPETO: quem nao tem vaga (sl 0/0) nao mostra mais o campo
       ADICIONADO — nao ha o que adicionar
    9  o botao do condicional vira hexagono + os tres degraus (+1/+2/+3),
       com o degrau atual aceso. Clicar vai DIRETO no degrau (antes o
       botao ciclava 1->2->3->1, e parecia que apagava coisa).
       ⚠️ o rotulo antigo dizia `degrau ${cmode||1}` e o cmode interno e
       0/1/2 — degrau 1 e 2 mostravam os DOIS o numero 1. Agora bate.
   10  o condicional passa a funcionar tambem na aba MAXIMO — e so ele
   11  TECNICO: a caixa fechada mostra so o NOME; a lista aberta continua
       com os atributos (senao os tres Koeman viram um so). O +1 vai
       para uma linha por atributo
   12  o efeito do impeto: um atributo por linha

   Feito por JS depois que a ficha monta (e nao por replace na casca)
   porque a ficha e REMONTADA a cada abrir / trocar de aba. Tudo dentro
   de try/catch: se algo aqui falhar, a ficha continua de pe.
   =================================================================== */
(function(){
 if(window.VISUAL_1508B) return; window.VISUAL_1508B = true;

 var st = document.createElement('style');
 st.textContent =
  '.fhdnome>div{font-size:27px!important}'
 +'.cbnv{font-weight:600!important}.cbnv b{font-weight:800!important}'
 +'.fhdnota{display:flex;flex-direction:column;gap:7px;align-items:stretch}'
 +'.pvbox{background:var(--surf2,#dae3de);border:1px solid var(--line,#bfcec7);'
 +'border-radius:10px;padding:8px 10px;text-align:center}'
 +'.pvbox .fhdl{display:block}'
 +'h3.pvcentro{text-align:center}'
 /* 15/08: as duas primeiras colunas sobravam espaco a direita e a
    distribuicao dos pontos ficava espremida, ruim de arrastar a barra.
    Agora elas ficam do tamanho do conteudo e o que sobra vai todo para
    a distribuicao. */
 +'@media(min-width:1101px){#box .bptrio,body .bptrio{'
 +'grid-template-columns:fit-content(250px) fit-content(235px) minmax(0,1fr)!important}}'
 +'.pvfis{grid-column:1/-1!important;display:grid!important;'
 +'grid-template-columns:1fr 1fr 1fr 0.85fr;gap:16px;align-items:start}'
 +'.pvfis .pvtopo{grid-column:1/-1}.pvfis .pvtotal{grid-column:1/4}'
 +'.pvcol{min-width:0}'
 +'.pvcol .fzh,.pvcol .fzr{grid-template-columns:1fr 32px 30px 34px 44px!important;'
 +'gap:5px!important;font-size:11px!important}'
 +'.pvcol .fzh{font-size:8.5px!important;letter-spacing:0!important;line-height:1.25}'
 +'.pvfis .sec{margin:0!important;padding:0!important;background:none!important;border:none!important}'
 +'.pvcond{margin-top:8px;padding-top:8px;border-top:1px dashed var(--line,#bfcec7)}'
 +'.pvcondtt{display:flex;align-items:center;gap:6px;font-size:10px;letter-spacing:.5px;'
 +'text-transform:uppercase;color:var(--txt2,#4a6159);margin-bottom:6px}'
 +'.pvhex{width:17px;height:19px;display:block;flex:none}'
 +'.pvdeg{display:flex;gap:5px}'
 +'.pvdeg button{flex:1;padding:5px 0;border-radius:7px;font-size:12px;font-weight:800;'
 +'background:var(--surf2,#dae3de);border:1px solid var(--line,#bfcec7);'
 +'color:var(--txt2,#4a6159);cursor:pointer;line-height:1.1}'
 +'.pvdeg button.on{background:#f0a531;border-color:#d38c1c;color:#3a2500}'
 +'[data-encmodo] #box .pvdeg button{pointer-events:auto!important;opacity:1!important}'
 +'.pvtec select{width:100%;font-weight:800}'
 +'.pvtecl{font-size:11px;color:var(--txt2,#4a6159);margin-top:4px;line-height:1.5}'
 +'.pvtecl b{color:var(--txt,#16302a)}'
 +'.impef .pvef{display:block}'
 +'#box.pvtrava .sec,#box.pvtrava .bpan{opacity:.28;pointer-events:none;filter:grayscale(.5)}'
 +'#box.pvtrava .fhdestbox .fhdbasico{display:none!important}'
 +'.pvpede{background:var(--surf2,#dae3de);border:1px solid var(--line,#bfcec7);'
 +'border-radius:12px;padding:14px 16px;margin:10px 0 14px;text-align:center}'
 +'.pvpedet{font-size:13.5px;font-weight:800;color:var(--txt,#16302a)}'
 +'.pvpedes{font-size:11.5px;color:var(--txt2,#4a6159);margin-top:3px}'
 +'.pvpedeb{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:11px}'
 +'.pvpedeb button{padding:9px 16px;border-radius:9px;font-size:13px;font-weight:800;'
 +'background:#17402f;color:#fff;border:1px solid #0f2c20;cursor:pointer}'
 +'.pvpedeb button b{font-weight:900;margin-left:8px}'
 +'.pvbas{display:inline-block;font-size:8.5px;font-weight:800;letter-spacing:.4px;'
 +'background:#0000002e;color:inherit;padding:1px 5px;border-radius:5px;margin-left:6px;'
 +'vertical-align:middle;opacity:.9}'
 /* 16/08 — a etiqueta vira COLUNA dentro do botao da funcao: largura fixa
    para as quatro colunas (nome · basico · posicao · nota) baterem em todas
    as linhas, e invisivel quando o estilo liga. */
 +'.cbfn .pvbas{flex:0 0 54px;margin-left:0;text-align:center;padding:1px 0}'
 +'.cbfn .pvbasvazio{background:transparent;opacity:0}'
 +'@media(max-width:1100px){.pvfis{grid-template-columns:1fr 1fr}.pvfis .pvtotal{grid-column:1/-1}}'
 /* ================= O CELULAR — 15/08 =========================
    Medido em 390x844: a 3a coluna do painel ficava com LARGURA ZERO
    (a regra do desktop matava o responsivo da casca), o campinho
    colapsava com as posicoes uma por cima da outra, e a coluna da
    nota gastava 158px de altura. Aqui vai o pacote do celular. */
 +'@media(max-width:820px){'
   /* o painel empilha, e a distribuicao dos pontos ocupa a largura toda */
 +'#box .bptrio,body .bptrio{grid-template-columns:minmax(0,1fr)!important;gap:12px}'
 +'.bptrio .bpc3{grid-column:auto!important}'
   /* o campinho para de colapsar: cada linha com altura minima */
 +'.fhdcampo{align-self:auto!important;max-width:none!important;width:100%}'
 +'.cbcampo{height:auto!important}'
 +'.cbcampo .cbl{flex:none!important;min-height:32px}'
 +'.cbcampo .cbp{height:32px!important;font-size:11px}'
   /* a nota vira uma faixa de tres, em vez de tres blocos empilhados */
 +'.fhdnota{flex-direction:row!important;align-items:stretch;gap:6px}'
 +'.fhdnota .pvbox{flex:1;padding:7px 4px}'
 +'.fhdnota .fhdn{font-size:26px}'
 +'.fhdnota .fhdl{font-size:8.5px}'
   /* a coluna do nome ocupa a largura toda e nao deixa buraco do lado */
 +'.fhdcol{width:100%!important;flex-direction:row;align-items:center;gap:10px;flex-wrap:wrap}'
 +'.fhdnome{text-align:left;flex:1 1 100%}'
 +'.fhdnome>div{font-size:22px!important}'
 +'.fhdcol>.mini{flex:1 1 auto}'
   /* o fisico em duas colunas e o resto respirando */
 +'.pvfis{grid-template-columns:1fr 1fr!important;gap:10px}'
 +'.pvfis .pvtotal{grid-column:1/-1!important}'
 +'.pvcol .fzh,.pvcol .fzr{grid-template-columns:1fr 26px 26px 30px 40px!important;font-size:10.5px!important}'
   /* as tres abas cabem sem quebrar */
 +'.encabas{display:grid!important;grid-template-columns:1fr 1fr 1fr;gap:5px}'
 +'.encaba{padding:8px 2px!important;font-size:10px!important;line-height:1.2}'
 +'.pvpedeb{flex-direction:column}'
 +'.pvpedeb button{width:100%}'
 +'}';
 document.head.appendChild(st);

 var HEX = '<svg class=pvhex viewBox="0 0 24 27" aria-hidden="true">'
         + '<polygon points="12,1 23,7.5 23,19.5 12,26 1,19.5 1,7.5" fill="#f0a531" '
         + 'stroke="#8a5a10" stroke-width="1.4"/></svg>';

 /* A CHAVE DA FICHA ABERTA.
    ⚠️ 15/08: o `CUR` da casca e um `let` no topo do script — ele NAO vira
    `window.CUR`, e ler dali devolvia undefined. Aqui se tenta o proprio
    `CUR` (visivel no escopo global) e, se falhar, tira a chave do onclick
    dos botoes das abas, que sempre a carregam. */
 function chave(){
  try{ if(typeof CUR !== 'undefined' && CUR) return CUR; }catch(e){}
  if(window.CUR) return window.CUR;
  var b = document.querySelector('.encaba[onclick]');
  if(b){
   var m = String(b.getAttribute('onclick') || '').match(/,\s*'([^']+)'\s*\)/);
   if(m) return m[1];
  }
  return null;
 }
 function cardAberto(){
  var k = chave();
  if(!k) return null;
  try{ return (typeof _card === 'function') ? _card(k) : null; }catch(e){ return null; }
 }

 /* ---- 3 · a aba ------------------------------------------------- */
 /* ⛔ 16/08 — ESTE RENOMEADOR FOI REMOVIDO. NAO REPOR.
    Ele reescrevia o texto dos botoes DEPOIS de desenhados, para trocar
    "COM O QUE EU TENHO" por "MEU CARD" e "DO MEU JEITO" por "LIVRE".
    Era o TERCEIRO lugar mexendo na mesma barra de abas — junto com a
    definicao do `_modoBar` no patch_edicao_viva (removida hoje) e a do
    CONTA-DO-MOTOR.js.

    Ordem do Luis, 16/08: *"por que que tem duas versoes? A gente nao pode
    trabalhar com coisa pela metade, so da problema."*

    Agora QUEM DECIDE O ROTULO DA ABA E UM LUGAR SO: o `window._modoBar`
    do `patch_modal_1608b`, que desenha as DUAS abas
    (⚡ MAXIMO POSSIVEL e ⚙ FAZER MINHA BUILD) ja com o nome certo. */
 function abas(){ /* sem efeito: o rotulo nasce certo no _modoBar */ }

 /* ---- 2 · a coluna da nota -------------------------------------- */
 function nota(){
  var nt = document.querySelector('.fhdnota');
  if(!nt || nt.dataset.pv === '1') return;
  var num = nt.querySelector('.fhdn'), lab = nt.querySelector('.fhdl'),
      top = nt.querySelector('.fhdtopo'), mel = nt.querySelector('.fhdmel');
  if(!num || !lab) return;
  lab.textContent = 'pontuação total';
  if(top) top.innerHTML = top.innerHTML.replace('% top', '% do topo');
  if(mel) mel.innerHTML = mel.innerHTML.replace('pode melhorar', 'Pode Melhorar');
  var cx = function(a, b2){ var d = document.createElement('div'); d.className = 'pvbox';
                            if(a) d.appendChild(a); if(b2) d.appendChild(b2); return d; };
  nt.appendChild(cx(num, lab));
  if(top) nt.appendChild(cx(top));
  if(mel) nt.appendChild(cx(mel));
  nt.dataset.pv = '1';
 }

 /* ---- 4 · o titulo ---------------------------------------------- */
 function titulos(){
  var h = document.querySelectorAll('.sec>h3'), i;
  for(i=0;i<h.length;i++)
   if(/^Atributos$/i.test(h[i].textContent.trim())) h[i].classList.add('pvcentro');
 }

 /* ---- 5 · o FISICO em tres colunas + o ESTILO DE JOGO DA IA ------
    A coluna DIRECAO sai: a "nota da medida" (+1 / -2 / 0) ja da o
    resultado, e sem ela cada medida cabe numa linha so. */
 function fisico(){
  var secs = document.querySelectorAll('.sec'), fis = null, ia = null, i, t;
  for(i=0;i<secs.length;i++){
   t = secs[i].querySelector('h3'); if(!t) continue;
   t = t.textContent.trim();
   if(/^F[ií]sico$/i.test(t)) fis = secs[i];
   if(/Estilo de jogo da IA/i.test(t)) ia = secs[i];
  }
  if(!fis || fis.dataset.pv === '1') return;
  var h3 = fis.querySelector('h3'),
      topo = fis.querySelectorAll('.corpotop,.corpopr'),
      head = fis.querySelector('.fzh'),
      rows = [].slice.call(fis.querySelectorAll('.fzr'));
  if(!h3 || !head || rows.length < 4) return;
  var total = rows.pop();
  var tira = function(el){ var c = el.children; if(c[1]) c[1].remove(); };
  tira(head); rows.forEach(tira);
  fis.dataset.pv = '1'; fis.classList.add('pvfis');
  var wt = document.createElement('div'); wt.className = 'pvtopo';
  wt.appendChild(h3);
  for(i=0;i<topo.length;i++) wt.appendChild(topo[i]);
  fis.innerHTML = ''; fis.appendChild(wt);
  var per = Math.ceil(rows.length / 3), j, col;
  for(i=0;i<3;i++){
   col = document.createElement('div'); col.className = 'pvcol';
   col.appendChild(head.cloneNode(true));
   for(j=i*per;j<(i+1)*per && j<rows.length;j++) col.appendChild(rows[j]);
   fis.appendChild(col);
  }
  if(ia){ col = document.createElement('div'); col.className = 'pvcol';
          col.appendChild(ia); fis.appendChild(col); }
  if(total){ total.classList.add('pvtotal'); fis.appendChild(total); }
 }

 /* ---- 9 e 10 · O DEGRAU DO CONDICIONAL --------------------------
    ⚠️ MEDIDO EM 15/08 — a tela aplicava a build ERRADA, deslocada de um.
    O motor grava as builds em `c.CD` nas chaves "2" e "3" (o degrau 1 e a
    propria build base). A tela procurava CD[cmode] com cmode 0/1/2:
        degrau 1 -> base        certo
        degrau 2 -> CD["1"] nao existe -> caia na base   ERRADO
        degrau 3 -> CD["2"]                              ERRADO
        CD["3"] nunca era usada
    Medido no Can Uzun / Meia ofensivo:  111,6 · 111,6 · 132,2
    quando o gravado e                   111,6 · 132,2 · 151,7

    E o motor esta CERTO: ele roda `build_completo2` de novo para cada
    degrau (roda_lote_v6.py, `for _grau in (2,3)`) — reotimiza barras,
    tecnico e habilidades. Medido nas 653 linhas com CD: 635 tem b1
    diferente por degrau, 81 mudam de barra, 69 de tecnico, 39 de
    habilidade. So 18 dao o mesmo b1 (o condicional nao pega atributo com
    peso naquela funcao) — e foi num desses que eu tropecei primeiro.

    ⛔ O RANKING continua no degrau 1, sempre. Isto so vale quando o Luis
    clica no degrau dentro da ficha. */
 function _cdBuild(c, degrau){
  if(degrau > 1 && c.CD && c.CD[String(degrau)]) return c.CD[String(degrau)];
  return c._cdBase || null;
 }
 function _fotoBuildBaseAntesDaSimulacao(c){
  var lvl={}, habs=[], imp=null, im;
  try{ lvl=_lvlDe(c)||{}; }catch(e){ lvl={}; }
  try{ habs=(c._habs!==undefined?c._habs:(c.HAB||[])).slice(); }catch(e){ habs=[]; }
  try{ if(typeof impAdicionado==='function') imp=impAdicionado(c)||null; }catch(e){}
  if(imp===null){
   try{ im=(c.imps||[]).filter(function(x){ return !!x.f; }); imp=im.length?im[0].n:null; }catch(e){}
  }
  return {func:c.tipo,lvl:Object.assign({},lvl),habs:habs,imp:imp,
          tec:(Array.isArray(c._tec)?c._tec.slice():null),
          tecNome:(c._tecNome!==undefined?c._tecNome:null),grau:1};
 }
 window.setCondCard = function(key, degrau){
  try{
   var c = (typeof _card === 'function') ? _card(key) : null;
   if(!c) return;
   if(typeof _marca === 'function') _marca(key);
   /* Ao sair do +1, fotografa novamente a base que estava realmente na
      Ficha. A simulacao +2/+3 troca barras e derivados pelo CD completo;
      essa fotografia separada e temporaria impede que o salvar misture
      grau 1 com as barras da simulacao. */
   var saindoDoBase = degrau>1 && (+c.cmode||0)===0;
   if(!c._cdBase || saindoDoBase) c._cdBase = { b1:c.b1, b1n:c.b1n, v:(c.sis||[]).slice(),
     bar:JSON.parse(JSON.stringify(c.sisBar||[])), TEC:c.TEC, TECB:c.TECB,
     HAB:(c.adds||[]).slice(), sobra:c.sobra };
   if(saindoDoBase) c._fotoBuildGrauBase=_fotoBuildBaseAntesDaSimulacao(c);
   var s = _cdBuild(c, degrau);
   if(s){
    if(s.v)   c.sis    = s.v.slice();
    if(s.bar) c.sisBar = JSON.parse(JSON.stringify(s.bar));
    if(s.HAB) c.adds   = s.HAB.slice();
    if(s.TEC !== undefined)  c.TEC  = s.TEC;
    if(s.TECB !== undefined) c.TECB = s.TECB;
    if(s.sobra !== undefined) c.sobra = s.sobra;
    if(s.b1  !== undefined) c.b1  = s.b1;
    if(s.b1n !== undefined) c.b1n = s.b1n;
    /* a nota e a tabela leem do arows. ⚠️ a linha e
       [indice, peso, alvo, valor, valor-alvo] — o 1o campo e o INDICE do
       atributo, NAO o nome (tentei pelo nome e nunca casava). */
    if(c.arows && s.v) c.arows.forEach(function(r){
      var at = r[0];
      if(typeof at === 'string' && typeof ATTRS !== 'undefined') at = ATTRS.indexOf(at);
      if(typeof at === 'number' && at >= 0 && s.v[at] !== undefined){
        r[3] = s.v[at]; r[4] = r[3] - r[2];
      }
    });
   }
   c.cmode = degrau - 1;              /* o campo antigo segue coerente */
   ['_n','_cp','_fb','_ia','_pr','_ESC','_notaMot'].forEach(function(k){ delete c[k]; });
   if(typeof traducaoViva === 'function') traducaoViva();
   if(typeof render === 'function') render();
   if(typeof reabrir === 'function') reabrir(key);
  }catch(e){ console.warn('setCondCard', e); }
 };

 /* ---- 8 · 9 · 12 · o bloco do IMPETO ----------------------------- */
 function impeto(){
  var K = chave(), c = null;
  c = cardAberto();

  /* 8 — sem vaga, sem campo "adicionado" */
  if(c && c.sl && c.sl[0] === 0 && c.sl[1] === 0){
   var subs = document.querySelectorAll('.iasub'), i, s;
   for(i=0;i<subs.length;i++){
    s = subs[i];
    if(/adicionado/i.test(s.textContent) && s.dataset.pv !== '1'){
     var ul = s.nextElementSibling;
     s.remove(); if(ul && ul.tagName === 'UL') ul.remove();
    }
   }
  }

  /* 12 — o efeito do impeto, um atributo por linha */
  var efs = document.querySelectorAll('.impef'), k, e, partes;
  for(k=0;k<efs.length;k++){
   e = efs[k];
   if(e.dataset.pv === '1') continue;
   e.dataset.pv = '1';
   partes = e.textContent.split(' · ');
   if(partes.length > 1)
    e.innerHTML = partes.map(function(x){
     return '<span class=pvef>' + x + '</span>'; }).join('');
  }

  /* 9 — o botao do condicional */
  var bts = document.querySelectorAll('button.bbt'), b, box, grau, j, h = '', K2;
  for(j=0;j<bts.length;j++){
   b = bts[j];
   if(!/condicional/i.test(b.textContent)) continue;
   box = b.parentElement;
   if(box.dataset.pv === '1') continue;
   box.dataset.pv = '1';
   /* a chave sai do onclick do proprio botao: o window.CUR ainda vem
      nulo quando a ficha esta sendo montada */
   K2 = (String(b.getAttribute('onclick')||'').match(/'([^']+)'/) || [])[1] || K;
   if(!c){ try{ c = _card(K2); }catch(e){} }
   grau = ((c && c.cmode) || 0) + 1;
   h = '<div class=pvcondtt>' + HEX + '<span>ímpeto condicional</span></div><div class=pvdeg>';
   for(var n=1;n<=3;n++)
    h += '<button class="' + (n === grau ? 'on' : '') + '" title="degrau ' + n
       + ' do ímpeto condicional" onclick="setCondCard(\'' + K2 + '\',' + n + ')">+'
       + n + '</button>';
   h += '</div>';
   box.className = 'hbgrp pvcond';
   box.innerHTML = h;
  }
 }

 /* ---- 11 · o TECNICO --------------------------------------------- */
 function tecnico(){
  var sel = null, ss = document.querySelectorAll('#box select'), i;
  for(i=0;i<ss.length;i++)
   if(/trocaTec/.test(ss[i].getAttribute('onchange') || '')){ sel = ss[i]; break; }
  if(!sel) return;
  var grp = sel.closest('.hbgrp');
  if(!grp || grp.dataset.pv === '1') return;
  grp.dataset.pv = '1'; grp.classList.add('pvtec');

  var op = sel.options[sel.selectedIndex];
  if(op && op.value !== ''){
   var cheio = op.text, corte = cheio.split(' · ');
   /* fechado mostra so o nome; ao abrir, a lista volta inteira —
      senao os tres Koeman viram um so */
   op.dataset.cheio = cheio;
   op.text = corte[0];
   var volta = function(){ if(op.dataset.cheio) op.text = op.dataset.cheio; };
   var corta = function(){ if(op.dataset.cheio) op.text = op.dataset.cheio.split(' · ')[0]; };
   sel.addEventListener('mousedown', volta);
   sel.addEventListener('focus', volta);
   sel.addEventListener('blur', corta);
   sel.addEventListener('change', corta);
  }

  /* o "+1 X · Y" vira uma linha por atributo */
  var kids = grp.querySelectorAll('div,span'), e, attrs = null, velha = null;
  for(i=0;i<kids.length;i++){
   e = kids[i];
   if(e.children.length === 0 && /^\+1\s+\S/.test(e.textContent.trim())){ velha = e; break; }
  }
  if(velha){
   attrs = velha.textContent.trim().replace(/^\+1\s*/, '').split(' · ');
   var alvo = velha.parentElement, html = '';
   for(i=0;i<attrs.length;i++)
    if(attrs[i].trim()) html += '<div class=pvtecl>+1 em <b>' + attrs[i].trim() + '</b></div>';
   velha.remove();
   if(html){ var d = document.createElement('div'); d.innerHTML = html; alvo.appendChild(d); }
  }
 }

 /* ---- 13 · CLICOU NUMA POSICAO: A FICHA TRAVA E PEDE A FUNCAO ----
    Ordem do Luis, 15/08: *"se ele clicar em MAT, ele pode ser Meia
    ofensivo ou Atacante infiltrador. O que nao pode e ele olhar la
    embaixo e achar que aquela ficha e a de MAT"*. Antes, clicar numa
    posicao acendia as funcoes mas deixava a ficha da funcao ANTERIOR
    montada embaixo — induzindo ao erro.
    Agora a ficha esmaece e aparece o aviso com as funcoes daquela
    posicao, cada uma com a sua nota. So volta quando ele escolher.
    ⛔ So apresentacao: nada de nota, nem de motor.
    As funcoes saem dos BOTOES JA ACESOS pelo campinho (classe cbfnq) —
    mesma fonte da tela, para o aviso nunca discordar do que esta ali. */
 /* escolheu a funcao: a marcacao da posicao sai e a ficha abre inteira */
 window._pvEscolhe = function(k){
  window._SELPOS = null;
  var b = document.querySelector('#box');
  if(b) b.classList.remove('pvtrava');
  var a = document.querySelector('.pvpede');
  if(a) a.remove();
  try{ abrir(k); }catch(e){}
 };

 function pedeFuncao(){
  var box = document.querySelector('#box') || document.body;
  var velho = document.querySelector('.pvpede');
  if(velho) velho.remove();
  box.classList.remove('pvtrava');
  var sel = window._SELPOS;
  if(!sel) return;
  var fhd = document.querySelector('.fhd');
  if(!fhd || !fhd.parentElement) return;
  var acesos = document.querySelectorAll('.cbfn.cbfnq'), i, b, nome, nota_, sig, out = [];
  for(i=0;i<acesos.length;i++){
   b = acesos[i];
   nome = (b.querySelector('i') || {}).textContent || '';
   nota_ = (b.querySelector('b') || {}).textContent || '';
   if(nome) out.push([nome.trim(), nota_.trim(), !!b.querySelector('.pvbas')]);
  }
  if(!out.length) return;
  /* uma funcao so nessa posicao: nao ha o que escolher — abre direto
     (Luis, 15/08: "quando o cara faz uma funcao so nao precisa escolher") */
  if(out.length === 1){
   var c1 = cardAberto();
   if(c1 && c1.tipo !== out[0][0]){ window._pvEscolhe(c1.id + '|' + out[0][0]); return; }
   window._SELPOS = null;
   return;
  }
  sig = (typeof SIGJ !== 'undefined' && SIGJ[sel]) || sel;
  var c = null;
  c = cardAberto();
  var id = c ? c.id : '';
  var d = document.createElement('div');
  d.className = 'pvpede';
  d.innerHTML = '<div class=pvpedet>' + sig + ' — '
    + (out.length > 1 ? ('aqui ele pode fazer ' + out.length + ' funções')
                      : 'aqui ele faz uma função')
    + '</div><div class=pvpedes>'
    + (out.length > 1 ? 'cada uma tem build e pontuação própria. Escolha qual você quer ver:'
                      : 'clique para ver a ficha dela:')
    + '</div><div class=pvpedeb>'
    + out.map(function(x){
        return '<button onclick="_pvEscolhe(\'' + id + '|' + x[0].replace(/'/g, "\\'")
             + '\')">' + x[0] + (x[1] ? '<b>' + x[1] + '</b>' : '')
             + (x[2] ? '<span class=pvbas>BÁSICO</span>' : '') + '</button>';
      }).join('')
    + '</div>';
  fhd.parentElement.insertBefore(d, fhd.nextSibling);
  box.classList.add('pvtrava');
 }

 /* ---- 14 · A MARCA "BASICO" NA LISTA DAS FUNCOES -----------------
    Luis, 15/08: para saber em quais funcoes o estilo nao liga ele tinha
    de abrir uma por uma, porque a tarja so fala da ficha aberta. Agora
    cada botao da lista leva a marca, e ele ve todas de uma vez.
    ⛔ So etiqueta: a nota nao muda (o +1 continua onde ja estava). */
 function basicoNaLista(){
  var bts = document.querySelectorAll('.cbfn'), i, b, nome, irm, c = null;
  if(!bts.length) return;
  c = cardAberto();
  if(!c || typeof D === 'undefined' || typeof estiloAtiva !== 'function') return;
  var base = String(c.id).split('@')[0];
  for(i=0;i<bts.length;i++){
   b = bts[i];
   if(b.querySelector('.pvbas')) continue;
   nome = (b.querySelector('i') || {}).textContent;
   if(!nome) continue;
   nome = nome.trim();
   irm = null;
   for(var j=0;j<D.length;j++)
    if(D[j].id !== 'MOLDE' && String(D[j].id).split('@')[0] === base && D[j].tipo === nome){
     irm = D[j]; break; }
   /* 16/08 — ORDEM DO LUIS: a etiqueta era ANEXADA no fim do botao, depois
      da nota, e desalinhava a lista inteira: o que era tres colunas virava
      quatro so nas linhas que tinham BASICO, e o nome quebrava em duas
      linhas. *"agora vai ficar o nome na primeira da esquerda, basico ou
      vazio na segunda, na terceira a posicao e na quarta a nota."*
      Entao a coluna existe SEMPRE — vazia quando o estilo liga — e entra
      ANTES da posicao, nao no fim. */
   var s = document.createElement('span');
   if(irm && !estiloAtiva(irm)){
    s.className = 'pvbas';
    s.textContent = 'BÁSICO';
    s.title = 'o estilo de jogo dele não liga nesta posição';
   } else {
    s.className = 'pvbas pvbasvazio';
   }
   var u = b.querySelector('u');
   if(u) b.insertBefore(s, u); else b.appendChild(s);
  }
 }

 /* ---- 15 · O NOME DO ESTILO POR EXTENSO --------------------------
    Luis, 15/08: *"tem espaco suficiente pra escrever Jogador de
    infiltracao e voce abreviou sem necessidade"*.
    A abreviacao vem do DADO (c.modelo). Aqui so o TEXTO NA TELA e
    trocado — o `c.modelo` continua igual, senao quebra o `funcDaPos`,
    o `SA_FAMILIA` e o `EST_POS`, que casam pelo nome do banco. */
 var ESTPT = { 'Jog. de infiltração': 'Jogador de infiltração',
               'Especialista em cruz.': 'Especialista em cruzamento' };
 function nomeEstilo(){
  var b = document.querySelector('.fhdestbox');
  if(!b) return;
  var no = b.firstChild;
  while(no){
   if(no.nodeType === 3 && ESTPT[no.nodeValue.trim()])
    no.nodeValue = ESTPT[no.nodeValue.trim()];
   no = no.nextSibling;
  }
 }

 function arruma(){
  try{ abas(); }catch(e){}
  try{ nota(); }catch(e){}
  try{ titulos(); }catch(e){}
  try{ fisico(); }catch(e){}
  try{ impeto(); }catch(e){}
  try{ tecnico(); }catch(e){}
  try{ pedeFuncao(); }catch(e){}
  try{ basicoNaLista(); }catch(e){}
  try{ nomeEstilo(); }catch(e){}
  try{ tiraBotaoBonus(); }catch(e){}
 }
 var arrumaAgendada=false;
 function agendaArruma(){
  if(arrumaAgendada) return;
  arrumaAgendada=true;
  requestAnimationFrame(function(){ arrumaAgendada=false; arruma(); });
 }
 /* ---- 16 · O CLIQUE NA POSICAO ESTAVA SENDO ENGOLIDO -------------
    ⚠️ Medido em 15/08: o `selPos` da casca marca a posicao e chama o
    `reabrir`; so que o `reabrir` foi envolvido para ZERAR o `_SELPOS`
    quando a chave muda — e na primeira vez o `_ULTK` ainda esta vazio,
    entao ele zerava a marcacao que acabara de ser feita. Resultado: o
    primeiro clique numa posicao nao fazia nada.
    Aqui o `_ULTK` e acertado ANTES, e a marcacao e reposta depois. */
 (function(){
  var orig = window.selPos;
  if(typeof orig !== 'function') return;
  window.selPos = function(p, key){
   var novo = (window._SELPOS === p) ? null : p;
   window._ULTK = key;
   window._SELPOS = novo;
   try{ if(typeof reabrir === 'function') reabrir(key); }catch(e){}
   window._SELPOS = novo;
   agendaArruma();
  };
 })();

 /* ---- 17 · OS BONUS ENTRAM NA NOTA, E O BOTAO SAI ----------------
    ORDEM DO LUIS, 15/08: *"e pra colocar direto na nota já esses valores.
    Físico ±1,5 · estilo de IA 0 a +1 · pé ruim 0 a +1 · estilo ativo +1.
    Já não tem nada de botão mais não."*

    ⚠️ O QUE ESTAVA ACONTECENDO: a casca tem `let ACH_BONUS=0` e envolve
    os tres bonus:
        prBonus  = function(c){ return ACH_BONUS ? _pr(c)  : 0; };
        fisBonus = function(c){ return ACH_BONUS ? _fis(c) : 0; };
        iaBonus  = function(c){ return ACH_BONUS ? _ia(c)  : 0; };
    Com a chave em 0, FISICO, PE RUIM e ESTILO DE IA ficavam TODOS zerados
    no ranking — era isso o "bonus +0.0" que o Luis viu no estilo de IA e o
    "bonus +0.00" do bloco Fisico. A conta por tras estava certa: medido,
    o _ia de um card com 2 COM devolve 0,4 certinho.

    Medido ao ligar, nas 12.161 linhas: 11.223 mudam de nota (92%),
    media +0,389, maior ganho +2,30, maior perda -1,50. No top 20 do
    Zagueiro de combate so 2 dos 20 ficam na mesma posicao.

    O estilo ativo (+1) nunca esteve na chave — esse ja entrava. */
 try{ ACH_BONUS = 1; }catch(e){}
 function tiraBotaoBonus(){
  var bs = document.querySelectorAll('button'), i;
  for(i=0;i<bs.length;i++)
   if(/nota = % do molde/.test(bs[i].textContent||'')) bs[i].remove();
 }
 try{ tiraBotaoBonus(); }catch(e){}
 try{ if(typeof _achGo === 'function') _achGo(); }catch(e){}

 window._visual1508B = arruma;

 function envolve(nome){
  var f = window[nome];
  if(typeof f !== 'function') return;
  window[nome] = function(){
   var r = f.apply(this, arguments);
   agendaArruma();
   return r;
  };
 }
 envolve('abrir'); envolve('encModo'); envolve('reabrir');
 if(document.readyState === 'loading')
  document.addEventListener('DOMContentLoaded', agendaArruma);
 else agendaArruma();
})();


/* bloco JavaScript 22 */

/* ===== MODAL - 2a LEVA 16/08/2026 ===== */
(function(){
 if(window.MODAL_1608B) return; window.MODAL_1608B=1;
 var GKSO=["Arrem. longo do GO", "Defesa direta (GO)", "Grito de garra (GO)", "Pegador de p\u00eanaltis", "Repos. baixa do GO", "Reposi\u00e7\u00e3o alta do GO"];
 var CSS="#box .at.atgc>*:nth-child(11),#box .at.atgc>*:nth-child(12),#box .at.atgc>*:nth-child(13),#box .athead.atgc>*:nth-child(11),#box .athead.atgc>*:nth-child(12),#box .athead.atgc>*:nth-child(13){opacity:.5}"
  +"#box .at.atgc>*:nth-child(10),#box .athead.atgc>*:nth-child(10){background:#8b98a826;border-radius:4px}"
  +"#box .at.atgc>*:nth-child(10){font-weight:800}"
  +"#box .btotbar{display:flex;flex-direction:column;align-items:flex-start;gap:1px;cursor:pointer;background:#22c58b;border:none;color:#08120c;font-weight:800;border-radius:8px;padding:7px 14px;font-size:12px;line-height:1.2;white-space:nowrap}"
  +"#box .btotbar:hover{filter:brightness(1.08)}"
  +"#box .btotbar small{font-weight:600;opacity:.85;font-size:10px}"
  +"#box .habesp1608{border-color:#22c58b!important;color:#0e6b45!important;background:#22c58b1f!important;font-weight:700}"
  +"#box .maxtrava{pointer-events:none!important;opacity:.4!important;cursor:default!important}"
  +"#box .semorc{margin:8px 0 2px;padding:9px 12px;border-radius:9px;background:#f0a5311f;border:1px solid #f0a53155;color:#8a5c12;font-size:11.5px;font-weight:700}"
  +"#box .degduv{pointer-events:none!important;opacity:.35!important;text-decoration:line-through!important;cursor:default!important}";
 var st=document.createElement("style"); st.textContent=CSS;
 document.head.appendChild(st);
 function chave(){
  try{ if(typeof CUR!=="undefined" && CUR) return CUR; }catch(e){}try{ if(window._T6_CHAVE_ATUAL) return window._T6_CHAVE_ATUAL; }catch(e){}try{ if(window._T6_CHAVE_ATUAL) return window._T6_CHAVE_ATUAL; }catch(e){}try{ if(window._T6_CHAVE_ATUAL) return window._T6_CHAVE_ATUAL; }catch(e){}
  var bx=document.getElementById("box"); if(!bx) return null;
  var bt=bx.querySelector(".encaba[onclick]"); if(!bt) return null;
  var m=String(bt.getAttribute("onclick")||"").match(/'([^']+\|[^']+)'/);
  return m?m[1]:null;
 }
  function modoAtual(){
   return window.FichaState?window.FichaState.uiMode():"motor"; }
 function ehInsumos(){ return modoAtual()==="livre"; }
 window._modoBar=function(K){
  var M=modoAtual(), q=String.fromCharCode(39),
      AB=[["motor","\u26a1 M\u00c1XIMO POSS\u00cdVEL",
           "o teto desta carta: a build que o motor escolheu"],
          ["livre","\u2699 FAZER MINHA BUILD",
           "monte o card do jeito que ele est\u00e1 no seu jogo: habilidades, t\u00e9cnico, \u00edmpeto e as barras na m\u00e3o. Nada se ajusta sozinho \u2014 quem otimiza as barras \u00e9 o bot\u00e3o."]],
      h='<div style="display:flex;align-items:center;gap:6px;flex-wrap:nowrap;margin-bottom:10px">', i, on;
  for(i=0;i<AB.length;i++){
   on=(AB[i][0]===M);
     h+='<button class="encaba'+(on?" encabaon":"")+'"'
     +' data-tip="'+AB[i][2].replace(/"/g,"&quot;")+'"'
     +' onclick="encModo('+q+AB[i][0]+q+","+q+K+q+')">'
     +AB[i][1]+"</button>";
  }
  return h+"</div>";
 };
 function bldFoto(key){
  var c=null; try{ c=_card(key); }catch(e){}
  if(!c) return null;
  var lvl={}; try{ lvl=_lvlDe(c); }catch(e){}
  var add=null;
  try{ add=(typeof impAdicionado==="function")?impAdicionado(c):null; }catch(e){}
  return { lvl:lvl,
           habs:(c._habs!==undefined?c._habs.slice():null),
           tec:(c._tec!==undefined?c._tec.slice():null),
           tecNome:(c._tecNome!==undefined?c._tecNome:null),
           semTec:(c._tec===undefined),
           imp:add };
 }
 function bldPoe(key, f){
  if(!f) return;
  var c=null; try{ c=_card(key); }catch(e){}
  if(!c) return;
  try{ _marca(key); }catch(e){}
  try{ delete c._cp; delete c._n; }catch(e){}
  try{ if(typeof editImp==="function") editImp(key, f.imp||"(nenhum)"); }catch(e){}
  try{ c=_card(key)||c; }catch(e){}
  if(f.habs===null) delete c._habs; else c._habs=f.habs.slice();
  if(f.tec ===null) delete c._tec;  else c._tec =f.tec.slice();
  if(f.tecNome===null) delete c._tecNome; else c._tecNome=f.tecNome;
  try{ _grava(c, f.lvl||{}); }catch(e){}
  if(f.habs && f.habs.length){ try{ _trocaHabs(key, f.habs.slice()); }catch(e){} }
 }
 window.elBldFoto=bldFoto; window.elBldPoe=bldPoe;
 function zeraBarras(key){
  var c=null; try{ c=_card(key); }catch(e){}
  if(!c) return;
  try{ _marca(key); }catch(e){}
  var _tb=[], _tn=null;
  try{ if(typeof mtTecBs==="function") _tb=mtTecBs()||[]; }catch(e){ _tb=[]; }
  try{ if(typeof mtTecNome==="function") _tn=mtTecNome()||null; }catch(e){ _tn=null; }
  c._habs=[]; c._tec=_tb.slice(); c._tecNome=_tn;
  try{ delete c._cp; delete c._n; }catch(e){}
  try{ if(typeof editImp==="function") editImp(key,"(nenhum)"); }catch(e){}
  try{ c=_card(key)||c; }catch(e){}
  var z={}; try{ MBK.forEach(function(b){ z[b]=0; }); }catch(e){ return; }
  try{ c._habs=[]; c._tec=_tb.slice(); c._tecNome=_tn; }catch(e){}
  try{ _grava(c,z); }catch(e){}
 }
 var _enc = window.encModo;
 window.encModo=function(m,key){
  if(m==="insumos") m="livre";
 try{
   if(modoAtual()==="livre" && m!=="livre" && key)
    window._BLD_FOTO=bldFoto(key);
  }catch(e){}
  try{if(window.FichaState)window.FichaState.setMode(m,key);}catch(e){}
  if(typeof _enc==="function"){ try{ _enc.call(this,m,key); }catch(e){} }
  else if(m==="motor"){ try{ restaurarMotor(key); }catch(e){} }
  if(m==="livre"){
   var _ib=String(key||"").split("|")[0].split("@")[0];
   if(window._BLD_ZERADA!==_ib){
    window._BLD_ZERADA=_ib; window._BLD_FOTO=null;
    try{ zeraBarras(key); }catch(e){}
   } else if(window._BLD_FOTO){
    try{ bldPoe(key, window._BLD_FOTO); }catch(e){}
   }
  }
  try{ reabrir(key); }catch(e){}
 };
 function poeBotao(){
  var bx=document.getElementById("box"); if(!bx) return;
  var v=bx.querySelector(".btotbar");
  if(!ehInsumos()){ if(v) v.remove(); return; }
  if(v) return;
  var hd=null, todos=bx.querySelectorAll(".bhd"), i;
  for(i=0;i<todos.length;i++) if(/Distribui/i.test(todos[i].textContent)) hd=todos[i];
  if(!hd) return;
  if(!chave()) return;
  var b=document.createElement("button"); b.className="btotbar";
  b.title="distribui os pontos das barras buscando a maior pontuação, usando o impeto, o tecnico e as habilidades que estao na tela";
  b.innerHTML="\u26a1 OTIMIZAR AS BARRAS<small>com os insumos que voc\u00ea p\u00f4s</small>";
  b.onclick=function(){
   var kk=chave(); if(!kk) return;
   if(typeof window.otimizarBarras!=="function") return;
   try{ _marca(kk); }catch(e){}
   try{ window.otimizarBarras(kk); }catch(e){}
  };
  if(hd.children.length>1) hd.insertBefore(b, hd.children[hd.children.length-1]);
  else hd.appendChild(b);
 }
 function arrumaPool(){
  var bx=document.getElementById("box"); if(!bx || !ehInsumos()) return;
  var sel=bx.querySelector('select[onchange*="addHab"]'); if(!sel) return;
  var k=chave(); if(!k) return;
  var c=null; try{ c=_card(k); }catch(e){}  if(!c) return;
  var ehGK = /^Goleiro/.test(String(c.tipo||""))
          || String(c.np||"")==="GK" || String(c.pos||"")==="GK";
  var jaTem=[]; try{ jaTem=habsAtual(c)||[]; }catch(e){}
  var nat=(c.fab||[]).concat(c.raras||[]);
  var todas=[]; try{ todas=Object.keys(HABEF); }catch(e){ return; }
  var lista=todas.filter(function(s){
   if(jaTem.indexOf(s)>=0 || nat.indexOf(s)>=0) return false;
   if(GKSO.indexOf(s)>=0) return ehGK;
   return true;
  }).sort(function(x,y){ return x.localeCompare(y,"pt"); });
  if(sel.options.length-1===lista.length) return;
  var h='<option value="">+ adicionar\u2026</option>', i;
  for(i=0;i<lista.length;i++)
   h+="<option>"+lista[i].replace(/&/g,"&amp;").replace(/</g,"&lt;")+"</option>";
  sel.innerHTML=h; sel.value="";
 }
 function nomeDaEtiqueta(el){
  var t="", n;
  for(n=el.firstChild; n; n=n.nextSibling)
   if(n.nodeType===3) t+=n.textContent;
  return t.replace(/\s+/g," ").trim();
 }
 function especiais(){
  var bx=document.getElementById("box"); if(!bx) return;
  var chips=bx.querySelectorAll(".chip.rr"), nomes=[], j, nm;
  for(j=0;j<chips.length;j++){
   chips[j].classList.add("habesp1608");
   nm=nomeDaEtiqueta(chips[j]); if(nm) nomes.push(nm);
  }
  if(!nomes.length) return;
  var grupos=bx.querySelectorAll(".hbgrp"), g, cab, lis, x, txt, i;
  for(i=0;i<grupos.length;i++){
   g=grupos[i]; cab=g.querySelector("b");
   if(!cab || !/^Nativas$/i.test(cab.textContent.trim())) continue;
   lis=g.querySelectorAll("li");
   for(j=lis.length-1;j>=0;j--){
    txt=lis[j].textContent.replace(/\s+/g," ").trim();
    for(x=0;x<nomes.length;x++) if(txt===nomes[x]){ lis[j].remove(); break; }
   }
   if(!g.querySelectorAll("li").length){
    var ul=g.querySelector("ul"); if(ul) ul.innerHTML="<li>nenhuma</li>";
   }
  }
 }
 function boasOpcoes(){
  var bx=document.getElementById("box"); if(!bx) return;
  var gs=bx.querySelectorAll(".hbgrp"), i, cab;
  for(i=0;i<gs.length;i++){
   cab=gs[i].querySelector("b");
   if(cab && /^Boas\s+op/i.test(cab.textContent.trim()))
    gs[i].style.display = ehInsumos() ? "none" : "";
  }
 }
 document.addEventListener("click", function(ev){
  try{
   var t=ev.target;
   if(!t||!t.closest){ window._ULT_CLIQUE=null; return; }
   var dg=t.closest('[onclick*="setCondCard"]');
   if(dg){ var mm=String(dg.textContent||"").replace(/[^0-9]/g,"");
           if(mm) window._GRAU_COND=+mm;
           window._ULT_CLIQUE="grau"; return; }
   if(t.closest(".cbfn")){ window._ULT_CLIQUE="func";
                           window._ULT_POS=null; return; }
   var ps=t.closest(".cbcampo .cbp");
   if(ps){ window._ULT_CLIQUE="pos";
           window._ULT_POS=String(ps.textContent||"").trim(); return; }
   window._ULT_CLIQUE=null; window._ULT_POS=null;
  }catch(e){}
 }, true);
 function acendeCampo(){
  var bx=document.getElementById("box"); if(!bx) return;
  var campo=bx.querySelector(".cbcampo"); if(!campo) return;
  var cels=campo.querySelectorAll(".cbp"), i, t;
  if(window._ULT_CLIQUE==="pos" && window._ULT_POS){
   for(i=0;i<cels.length;i++){
    t=String(cels[i].textContent||"").trim();
    if(t===window._ULT_POS){
     cels[i].classList.remove("cboff"); cels[i].classList.remove("cbsec");
     cels[i].classList.add("cbnat");
    } else if(cels[i].classList.contains("cbnat")){
     cels[i].classList.remove("cbnat"); cels[i].classList.add("cbsec");
    }
   }
   return;
  }
  if(campo.querySelector(".cbnat")) return;
  var bt=bx.querySelector(".cbfn.cbfnq"); if(!bt) return;
  var u=bt.querySelector("u"); if(!u) return;
  var sigs=String(u.textContent||"").split("/")
   .map(function(s){return s.trim();}).filter(function(s){return !!s;});
  if(!sigs.length) return;
  var cels=campo.querySelectorAll(".cbp"), i, t;
  for(i=0;i<cels.length;i++){
   t=String(cels[i].textContent||"").trim();
   if(sigs.indexOf(t)>=0){
    cels[i].classList.remove("cboff"); cels[i].classList.remove("cbsec");
    cels[i].classList.add("cbnat");
   }
  }
 }
 function botaoDoMotor(){
  var bx=document.getElementById("box"); if(!bx) return;
  var bts=bx.querySelectorAll("[onclick]"), i, oc;
  for(i=0;i<bts.length;i++){
   oc=String(bts[i].getAttribute("onclick")||"");
   if(oc.indexOf("restaurarMotor(")<0) continue;
   bts[i].style.display = ehInsumos() ? "none" : "";
  }
 }
 (function(){
  if(typeof _fal!=="function") return;
  var TETO=9;
  var novo=function(d,p){ var inc=0.25*p/12, t=0, k,
   lim=Math.min(d,TETO);
   for(k=1;k<=lim;k++) t+=(1+(k-1)*inc)*p;
   return t; };
  try{ _fal=novo; }catch(e){}
  try{ window._fal=novo; }catch(e){}
  window.PUNICAO_COM_TETO=TETO;
 })();
 function nivelDe(c){
  var o={}; try{ var l=_lvlDe(c); for(var k in l) o[k]=l[k]; }catch(e){}
  return o;
 }
 function semMexerNasBarras(nome){
  var f=window[nome]; if(typeof f!=="function") return;
  window[nome]=function(){
   var a0=arguments[0],
       k=(typeof a0==="string"&&a0.indexOf("|")>0)?a0:chave();
   var antes=null, c=null;
   if(ehInsumos()&&k){ try{ c=_card(k); if(c) antes=nivelDe(c); }catch(e){} }
   var r=f.apply(this,arguments);
   if(antes&&k){
    try{ var cc=_card(k)||c;
     if(cc){ _grava(cc,antes);
             if(typeof _renota==="function") _renota(cc); }
    }catch(e){}
    try{ reabrir(k); }catch(e){}
   }
   return r;
  };
 }
 ["editImp","trocaTec","_trocaHabs","addHab","remHab"]
  .forEach(semMexerNasBarras);
 var _ordemFunc={}, _baseFunc={};
 if(!window._GRAU_COND) window._GRAU_COND=1;
 function baseDaCarta(){
  var k=chave(); if(!k) return null;
  return String(k).split("|")[0].split("@")[0];
 }
 function irmaosDa(base){
  try{ return D.filter(function(x){ return x && x.id!=="MOLDE"
   && String(x.id).split("@")[0]===base; }); }catch(e){ return []; }
 }
 function congelaBase(base){
  if(_baseFunc[base]) return;
  var m={}, irm=irmaosDa(base), i, x;
  for(i=0;i<irm.length;i++){ x=irm[i];
   try{ m[x.tipo]={ nota:nota(x), b1n:(x.b1n!==undefined?x.b1n:null),
                    CD:x.CD||null }; }catch(e){}
  }
  _baseFunc[base]=m;
 }
 function notaNoDegrau(base, funcao, grau){
  var m=_baseFunc[base]; if(!m||!m[funcao]) return null;
  var b=m[funcao];
  if(grau<=1 || !b.CD || !b.CD[String(grau)]) return b.nota;
  if(b.b1n===null) return b.nota;
  var d=b.CD[String(grau)];
  if(d.b1n===undefined || d.b1n===null) return b.nota;
  return d.b1n + (b.nota - b.b1n);
 }
 function pintaNotas(){
  var bx=document.getElementById("box"); if(!bx) return;
  var base=baseDaCarta(); if(!base) return;
  congelaBase(base);
  var bts=bx.querySelectorAll(".cbfn"), i, nm, b, v;
  for(i=0;i<bts.length;i++){
   nm=bts[i].querySelector("i"); b=bts[i].querySelector("b");
   if(!nm||!b) continue;
   v=notaNoDegrau(base, String(nm.textContent||"").trim(), window._GRAU_COND);
   if(v===null||isNaN(v)) continue;
   b.textContent=v.toFixed(1);
  }
 }
 function ordemEstavel(){
  var bx=document.getElementById("box"); if(!bx) return;
  var lista=bx.querySelector(".cbfnl"); if(!lista) return;
  var bts=[].slice.call(lista.querySelectorAll(".cbfn"));
  if(bts.length<2) return;
  var k=chave(); if(!k) return;
  var base=String(k).split("|")[0].split("@")[0];
  function nomeDe(e){ var q=e.querySelector("i");
   return q?String(q.textContent||"").trim():""; }
  var agora=bts.map(nomeDe);
  if(!_ordemFunc[base]){ _ordemFunc[base]=agora; return; }
  var alvo=_ordemFunc[base], i, mudou=false;
  if(alvo.length!==agora.length) return;
  for(i=0;i<agora.length;i++) if(agora[i]!==alvo[i]){ mudou=true; break; }
  if(!mudou) return;
  for(i=0;i<alvo.length;i++){
   var achou=null, j;
   for(j=0;j<bts.length;j++) if(nomeDe(bts[j])===alvo[i]){ achou=bts[j]; break; }
   if(achou) lista.appendChild(achou);
  }
 }
 function travaMaximo(){
  var bx=document.getElementById("box"); if(!bx) return;
  var trava=!ehInsumos();
  var sel='[onclick*="editBar"],[onclick*="setBar"],[onclick*="remHab"],'
   +'select[onchange*="addHab"],select[onchange*="trocaTec"],'
   +'select[onchange*="editImp"]';
  var a=bx.querySelectorAll(sel), i;
  for(i=0;i<a.length;i++){
   if(trava) a[i].classList.add("maxtrava");
   else a[i].classList.remove("maxtrava");
  }
 }
 function condicionalDuvidoso(c){
  try{
   var a=[], i;
   (c.nm||[]).forEach(function(p){ if(p && +p[1]===1) a.push(+p[0]); });
   if(!a.length) return false;
   var ch=a.sort(function(x,y){return x-y;}).join(",");
   for(i=0;i<CAT.length;i++){
    var pr=CAT[i][2].map(function(x){ return +x[0]; })
                    .sort(function(x,y){ return x-y; }).join(",");
    if(pr===ch) return false;
   }
   return true;
  }catch(e){ return false; }
 }
 window.condicionalDuvidoso=condicionalDuvidoso;
 function travaDegrauDuvidoso(){
  var bx=document.getElementById("box"); if(!bx) return;
  var c=null; try{ c=_card(chave()); }catch(e){}
  if(!c) return;
  var duv = !!(c.CD && (c.CD["2"]||c.CD["3"])) && condicionalDuvidoso(c);
  var a=bx.querySelectorAll('[onclick*="setCondCard"]'), i;
  for(i=0;i<a.length;i++){
   if(duv){ a[i].classList.add("degduv");
    a[i].setAttribute("title","nesta carta dois ímpetos somam no mesmo atributo, e o motor calculou o degrau sem enxergar um deles. O número sairia errado — por isso o botão está desligado.");
   } else { a[i].classList.remove("degduv"); }
  }
  if(duv) window._GRAU_COND=1;
 }
 function arrumaFisico(){
  var bx=document.getElementById("box"); if(!bx) return;
  var pr=bx.querySelector(".corpopr"), sp, i, t;
  if(pr){ sp=pr.querySelectorAll("b");
   for(i=0;i<sp.length;i++){ t=String(sp[i].textContent||"").trim();
    if(t==="Left")  sp[i].textContent="Esquerdo";
    if(t==="Right") sp[i].textContent="Direito";
   } }
  var tp=bx.querySelector(".corpotop"); if(!tp) return;
  sp=tp.querySelectorAll("span");
  for(i=0;i<sp.length;i++){ t=String(sp[i].textContent||"").trim();
   if(/^lesão\s+\d+$/.test(t)){
    sp[i].setAttribute("title","o dado veio em ingles, como numero ("
     +t.replace(/[^0-9]/g,"")+"). Baixa/Media/Alta ainda nao foi medido.");
    sp[i].textContent="lesão —";
   } }
 }
 function avisaSemOrcamento(){
  var bx=document.getElementById("box"); if(!bx) return;
  var velho=bx.querySelector(".semorc"); if(velho) velho.remove();
  if(bx.querySelector(".bpan")) return;
  var c=null; try{ c=_card(chave()); }catch(e){}
  if(!c || c.id==="MOLDE" || c.orc) return;
  var anc=bx.querySelector(".fhdcampo") || bx.querySelector(".cbwrap");
  if(anc && anc.parentNode && anc.parentNode.parentNode) anc=anc.parentNode;
  if(!anc || !anc.parentNode) return;
  var d=document.createElement("div");
  d.className="semorc";
  d.textContent="esta carta já está no teto — não há progressão para distribuir";
  anc.parentNode.insertBefore(d, anc.nextSibling);
 }
 (function(){ var _pn=window.pimpNativos;
  if(typeof _pn!=="function" || typeof CAT==="undefined") return;
  function sg(e){ var o={},k; for(k=0;k<e.length;k++)
   o[e[k][0]]=(o[e[k][0]]||0)+e[k][1]; return o; }
  function ig(a,b){ var x=Object.keys(a), y=Object.keys(b), k;
   if(x.length!==y.length) return false;
   for(k=0;k<x.length;k++) if(b[x[k]]!==a[x[k]]) return false;
   return true; }
  var PN=null, PS=null;
  window.pimpNativos=function(c){
   var r=_pn(c); if(!r) return r;
   var temFake=false, i, j;
   for(i=0;i<r.length;i++) if(/\+[45]$/.test(r[i].nome)) temFake=true;
   if(!temFake) return r;
   try{
    if(!PN){ PN=[]; PS=[];
     for(i=0;i<CAT.length;i++){ PN.push(CAT[i]); PS.push(sg(CAT[i][2])); } }
    var nm=(c&&c.nm)||[], d={};
    for(i=0;i<nm.length;i++) d[nm[i][0]]=(d[nm[i][0]]||0)+nm[i][1];
    var achou=[];
    for(i=0;i<PN.length;i++) for(j=i;j<PN.length;j++){
     var t={}, x;
     for(x in PS[i]) t[x]=PS[i][x];
     for(x in PS[j]) t[x]=(t[x]||0)+PS[j][x];
     if(ig(t,d)) achou.push([i,j]);
    }
    if(achou.length===1){ var a=achou[0];
     return [{nome:PN[a[0]][0], efeito:PN[a[0]][2]},
             {nome:PN[a[1]][0], efeito:PN[a[1]][2]}]; }
   }catch(e){}
   return r;
  };
 })();
 function tudo(){ try{ poeBotao(); }catch(e){}
                  try{ ordemEstavel(); }catch(e){}
                  try{ pintaNotas(); }catch(e){}
                  try{ travaMaximo(); }catch(e){}
                  try{ botaoDoMotor(); }catch(e){}
                  try{ acendeCampo(); }catch(e){}
                  try{ boasOpcoes(); }catch(e){}
                  try{ arrumaPool(); }catch(e){}
                  try{ arrumaFisico(); }catch(e){}
                  try{ travaDegrauDuvidoso(); }catch(e){}
                  try{ avisaSemOrcamento(); }catch(e){}
                  try{ especiais(); }catch(e){} }
 var tudoAgendado=false;
 function agendaTudo(){
  if(tudoAgendado) return;
  tudoAgendado=true;
  requestAnimationFrame(function(){ tudoAgendado=false; tudo(); });
 }
 ["abrir","reabrir","encModo"].forEach(function(n){
  var o=window[n]; if(typeof o!=="function") return;
  window[n]=function(){ var r=o.apply(this,arguments);
   agendaTudo(); return r; };
 });
 agendaTudo();
})();


/* bloco JavaScript 25 */

/* ===== CABECALHO_E_FILTROS_1608 ===== */
(function(){
 function achou(){ return document.getElementById("q")
   && document.querySelector("header h1")
   && document.querySelector("#filtros .ctl"); }

 function monta(){
  if(document.getElementById("qtopo")) return true;
  if(!achou()) return false;
  var h1=document.querySelector("header h1");
  var q=document.getElementById("q");
  var ctl=document.querySelector("#filtros .ctl");

  /* --- 8c · a busca sobe. Mover o proprio elemento preserva os
         ouvintes que a casca ja pendurou nele. --- */
  var cx=document.createElement("span"); cx.id="qtopo";
  var velhoPai=q.parentNode;
  cx.appendChild(q);
  var esc=document.createElement("span"); esc.className="qesc"; esc.textContent="\u00d7";
  esc.title="limpar a busca";
  cx.appendChild(esc);
  if(velhoPai && velhoPai.className==="fld") velhoPai.style.display="none";
  var ref=document.getElementById("boxbt")||document.getElementById("condflut")
        ||document.getElementById("fbt");
  if(ref&&ref.parentNode===h1) h1.insertBefore(cx, ref.nextSibling);
  else h1.appendChild(cx);

  /* --- 11 · o alcance da busca muda com a pagina --- */
  /* ⚠️ o HOME da casca e `let`, e `let` no topo de um script NAO vira
     propriedade de window. Tem de ler pelo escopo lexico. */
  function naHome(){ try{ return !!HOME; }catch(e){ return false; } }
  function ajustaPlaceholder(){
   q.placeholder = naHome() ? "buscar em todos os cards"
                            : "buscar nesta posição";
  }
  ajustaPlaceholder();
  /* O texto acompanha somente uma troca explícita de aba, não um relógio. */
  document.addEventListener("click", function(ev){
   if(ev.target.closest && ev.target.closest(".t6tab,[data-t6home]")) ajustaPlaceholder();
  }, true);
  esc.onclick=function(){ q.value=""; cx.classList.remove("tem");
   try{ if(!naHome()) render(); }catch(e){} };
  q.addEventListener("input", function(){
   cx.classList.toggle("tem", !!q.value);
  });

  /* --- a barra lateral: esconde grupo sem nenhuma funcao dentro --- */
  function limpaGrupos(){
   var n=0;
   Array.prototype.slice.call(document.querySelectorAll("#fam .famg"))
    .forEach(function(g){
      var tem=g.querySelectorAll(".tabs .tab").length;
      if(!tem){ g.classList.add("vazio"); n++; }
      else g.classList.remove("vazio");
    });
   /* e o setor que ficou sem nenhum grupo visivel some junto */
   Array.prototype.slice.call(document.querySelectorAll("#fam .setor"))
    .forEach(function(st){
      var vis=Array.prototype.slice.call(st.querySelectorAll(".famg"))
        .filter(function(g){ return !g.classList.contains("vazio"); }).length;
      st.style.display = vis ? "" : "none";
    });
   window._GRUPOS_VAZIOS = n;
  }
  limpaGrupos();
  setTimeout(limpaGrupos, 1200);

  /* --- os nomes de GRUPO que o Luis trocou, 16/08 15h35 ---
     Ordem dele, com estas palavras: "meia lateral nao e mais meia
     lateral, e ALA. Ponta nao e mais ponta, e ATACANTE."
     Acompanha o rotulo longo, que ja era Ala finalizador / Ala cruzador
     e Atacante criador / Atacante finalizador.
     ⚠️ So o que aparece na tela. O data-g continua o nome antigo, porque
        e ele que o FAM e o resto do codigo usam para achar o grupo. */
  var NOMEGRUPO = { "MEIA LATERAL":"ALA", "PONTA":"ATACANTE" };
  function renomeiaGrupos(){
   var n=0;
   Array.prototype.slice.call(document.querySelectorAll("#fam .famt[data-g]"))
    .forEach(function(t){
      var g=t.getAttribute("data-g"), novo=NOMEGRUPO[g];
      if(!novo) return;
      var b=t.querySelector("b");
      if(b && b.textContent!==novo){ b.textContent=novo; n++; }
    });
   window._GRUPOS_RENOMEADOS = n;
  }
  renomeiaGrupos();
  setTimeout(renomeiaGrupos, 1200);

  /* --- 9 · os filtros que saem, escondidos um a um pelo id --- */
  ["tier","posfab","orig","vm","mx","ps"].forEach(function(id){
   var e=document.getElementById(id); if(!e) return;
   var f=e.closest(".fld"); if(f) f.classList.add("saiu");
  });

  /* --- 9 · a faixa de pontuacao e a de percentual --- */
  function faixa(id,rot,ph1,ph2){
   var d=document.createElement("div"); d.className="fld";
   d.innerHTML="<span>"+rot+"</span><div class=faixa>"
    +"<input type=number id="+id+"min placeholder=\""+ph1+"\">"
    +"<em>até</em>"
    +"<input type=number id="+id+"max placeholder=\""+ph2+"\"></div>";
   return d;
  }
  var alvo=document.getElementById("mdl");
  var dep=alvo?alvo.closest(".fld"):ctl.firstChild;
  var f1=faixa("pnt","pontuação","mín","máx");
  var f2=faixa("pct","% do topo","mín","máx");
  if(dep&&dep.nextSibling) { ctl.insertBefore(f1,dep.nextSibling);
                             ctl.insertBefore(f2,f1.nextSibling); }
  else { ctl.appendChild(f1); ctl.appendChild(f2); }

  /* --- 9 · o que nao e filtro desce para um bloco proprio --- */
  var g=document.createElement("div"); g.id="ferrag";
  g.innerHTML="<div class=ftit>FERRAMENTAS</div>";
  ctl.appendChild(g);
  ["verpor","view"].forEach(function(id){
   var e=document.getElementById(id); if(!e) return;
   var f=e.closest(".fld"); if(f) g.appendChild(f);
  });
  var dst=ctl.querySelector(".dst"); if(dst) g.appendChild(dst);
  Array.prototype.slice.call(ctl.querySelectorAll("button.hb"))
   .forEach(function(b){ g.appendChild(b); });
  var cnt=document.getElementById("cnt"); if(cnt) g.appendChild(cnt);

  /* --- 9 · a faixa filtra depois do render, sem tocar no render --- */
  var IDX=null;
  function indice(){
   if(IDX) return IDX;
   IDX={};
   D.forEach(function(c){ IDX[c.id+"|"+c.tipo]=c; });
   return IDX;
  }
  function num(id){ var e=document.getElementById(id);
   if(!e||e.value==="") return null; var v=parseFloat(e.value.replace(",","."));
   return isNaN(v)?null:v; }
  function aplicaFaixa(){
   var pmin=num("pntmin"), pmax=num("pntmax"),
       cmin=num("pctmin"), cmax=num("pctmax");
   var out=document.getElementById("out"); if(!out) return;
   var lig=(pmin!==null||pmax!==null||cmin!==null||cmax!==null);
   var I=indice(), fora=0, dentro=0;
   Array.prototype.slice.call(out.querySelectorAll("[data-k]")).forEach(function(el){
    /* ⚠️ o tema poe display:grid!important no .cd — um display:none
       inline SEM important perde para ele e o card continua na tela.
       Tem de ser setProperty com a prioridade. */
    if(!lig){ el.style.removeProperty("display"); return; }
    var c=I[el.getAttribute("data-k")]; if(!c) return;
    var n=(c.__cn&&typeof c.pontuacao_final==='number')?c.pontuacao_final:nota(c),
        p=(c.__cn&&typeof c.percentual_topo==='number')?c.percentual_topo:0, ok=true;
    if(pmin!==null&&n<pmin) ok=false;
    if(pmax!==null&&n>pmax) ok=false;
    if(cmin!==null&&p<cmin) ok=false;
    if(cmax!==null&&p>cmax) ok=false;
    if(ok) el.style.removeProperty("display");
    else   el.style.setProperty("display","none","important");
    if(ok) dentro++; else fora++;
   });
   var av=document.getElementById("faixaav");
   if(!av){ av=document.createElement("div"); av.id="faixaav";
    av.style.cssText="font-size:10.5px;font-weight:700;margin-top:7px;opacity:.8";
    var p2=document.getElementById("pctmax");
    if(p2) p2.closest(".fld").appendChild(av); }
   av.textContent = lig ? (dentro+" na faixa · "+fora+" escondidos") : "";
  }
  window.aplicaFaixa=aplicaFaixa;
  ["pntmin","pntmax","pctmin","pctmax"].forEach(function(id){
   var e=document.getElementById(id); if(e) e.addEventListener("input",aplicaFaixa);
  });
  if(typeof window.render==="function"){
   var _r=window.render;
   window.render=function(){ var v=_r.apply(this,arguments);
    try{ aplicaFaixa(); }catch(e){} return v; };
  }
  return true;
 }

 /* Bootstrap limitado: os controles hoje têm lifecycle próprio. Esta camada
    tenta ligar a faixa até eles existirem, mas nunca mantém polling. */
 var esperaFaixa=null,tentativasFaixa=0,concluidoFaixa=false,MAX_TENTATIVAS_FAIXA=20;
 function cancelaEsperaFaixa(){if(esperaFaixa!==null){clearTimeout(esperaFaixa);esperaFaixa=null;}}
 function iniciaFaixa(){
  cancelaEsperaFaixa();
  if(concluidoFaixa)return true;
  if(monta()){concluidoFaixa=true;return true;}
  if(tentativasFaixa++<MAX_TENTATIVAS_FAIXA)
   esperaFaixa=setTimeout(iniciaFaixa,300);
  return false;
 }
 function disposeFaixa(){cancelaEsperaFaixa();return true;}
 window.T6FaixaBootstrap=Object.freeze({mount:iniciaFaixa,dispose:disposeFaixa,
  inspect:function(){return{completed:concluidoFaixa,pending:esperaFaixa!==null,attempts:tentativasFaixa};}});
 iniciaFaixa();
})();


/* bloco JavaScript 26 */

/* ===== ELENCO_1608 — o layout e o card unico ===== */
(function(){
 if(typeof mtRender!=="function") return;
 var TETO_TIT=11, TETO_BANCO=12;
 window.EL_TETO={titulares:TETO_TIT, banco:TETO_BANCO};

 /* ---------- 1 · A PONTUACAO QUE O CARD MOSTRA ----------
    Ordem do Luis, 16/08: *"descarta a pontuacao da posicao original.
    Ele vai aparecer com a pontuacao que esta no MEU CARD do modal."*
    O `mtNotaReal` ja e exatamente isso: a nota com as barras que o
    usuario pos (`mtCfg`) e o tecnico do time. Quando a FAZER MINHA BUILD
    entrar, ela substitui esta funcao por cima — por isso ela esta no
    window e num lugar so. */
 if(typeof window.elPontuacao!=="function")
  window.elPontuacao=function(k, funcDaVaga){
   var c=null; try{ c=mtCard(k); }catch(e){}
   if(!c) return null;
   var n=0; try{ n=mtNotaReal(k); }catch(e){ try{ n=nota(c); }catch(e2){ n=0; } }
   return {n:n, func:funcDaVaga||c.tipo, nome:null};
  };

 function doisDec(v){
  var s=(+v||0).toFixed(2).split(".");
  return s[0]+"<i>."+s[1]+"</i>";
 }
 function esc(t){ return String(t==null?"":t)
  .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
  .replace(/"/g,"&quot;"); }
 function escJs(t){return String(t==null?'':t).replace(/\\/g,'\\\\').replace(/'/g,"\\'")
  .replace(/\r/g,'\\r').replace(/\n/g,'\\n');}
 function funcaoBuildEmDuasLinhas(t){
  var w=String(t==null?"\u2014":t).trim().split(/\s+/), corte=1, melhor=Infinity;
  if(w.length<2) return '<span>'+esc(w[0]||"\u2014")+'</span>';
  for(var i=1;i<w.length;i++){
   var d=Math.abs(w.slice(0,i).join(' ').length-w.slice(i).join(' ').length);
   if(d<melhor){ melhor=d; corte=i; }
  }
 return '<span>'+esc(w.slice(0,corte).join(' '))+'</span>'
   +'<span>'+esc(w.slice(corte).join(' '))+'</span>';
 }
 /* Etiqueta, aviso e lookup de molde compartilham a mesma identidade da
    função; grafias que diferem só por caixa ou acento não podem separar uma
    build da função que ela representa. */
 function chaveFuncaoCanonica(t){
  return String(t==null?'':t).normalize('NFD').replace(/[\u0300-\u036f]/g,'')
   .toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
 }
 /* O dono da tradução técnico -> função vigente é a Ficha. Aqui só
    reaproveitamos a API exposta por ela; se o módulo ainda não carregou,
    conservamos o dado cru e nunca inventamos uma segunda tabela. */
 function funcaoVisivelVigente(t){
  var bruto=String(t==null?'':t).trim();
  try{
   if(typeof window.t6NomeFuncao==='function') return String(window.t6NomeFuncao(bruto)||bruto).trim();
  }catch(e){}
  return bruto;
 }
 function funcaoDoCatalogo(k,t){
  var alvo=chaveFuncaoCanonica(funcaoVisivelVigente(t)), idb=String(k||'').split('|')[0].split('@')[0], lista=[];
  try{ lista=(typeof D!=='undefined'&&Array.isArray(D))?D:[]; }catch(e){}
  for(var i=0;i<lista.length;i++){
   var c=lista[i];
   if(!c || String(c.id).split('@')[0]!==idb) continue;
   if(chaveFuncaoCanonica(funcaoVisivelVigente(c.tipo))===alvo) return c.tipo;
  }
  return null;
 }
 function mesmaFuncaoTecnica(a,b){
  var ca=chaveFuncaoCanonica(funcaoVisivelVigente(a));
  var cb=chaveFuncaoCanonica(funcaoVisivelVigente(b));
  return !!ca && ca===cb;
 }
 window.elFuncaoCanonica=chaveFuncaoCanonica;
 window.elFuncaoVisivel=funcaoVisivelVigente;
 window.elFuncaoDoCatalogo=funcaoDoCatalogo;
 window.elMesmaFuncaoTecnica=mesmaFuncaoTecnica;

 /* O seletor precisa existir antes do primeiro desenho das Reservas. Antes,
    ele só era instalado no IIFE de builds, depois de `desenha()`: o card
    Básica-only nascia sem o bloco e os botões absolutos ocupavam seu lugar.
    Esta é a única fábrica do seletor; os handlers continuam resolvidos pelas
    portas públicas depois que todo o arquivo termina de carregar. */
 function buildCompativelComEntradaNoDesenho(b,entrada){
  try{
   if(typeof window.elBuildCompativelComEntrada==='function')
    return !!window.elBuildCompativelComEntrada(b,entrada);
  }catch(e){}
  if(!b||!entrada)return false;
  var alvo=chaveFuncaoCanonica(funcaoVisivelVigente(entrada.functionId));
  return !!alvo&&chaveFuncaoCanonica(funcaoVisivelVigente(b.func))===alvo;
 }
 function seletorBuildDoCard(k,de,sl,entrada){
  var idb=String(k||'').split('|')[0].split('@')[0],m=null,L=[];
  try{m=(typeof MT!=='undefined')?MT:null;L=(m&&m.builds&&Array.isArray(m.builds[idb]))?m.builds[idb]:[];}catch(e){}
  var ativa=(de==='campo'&&sl)?String(sl.buildId||'base')
   :String(entrada&&entrada.buildId||'base');
  var indiceSlot=(de==='campo'&&sl&&m&&Array.isArray(m.slots))?m.slots.indexOf(sl):-1;
  if(de==='campo'&&indiceSlot<0)return '';
  if(de!=='campo'&&(!entrada||!entrada.entryId))
   return '<select class=elbsel disabled title="entrada indisponivel"><option>BÁSICA</option></select>';
  var acao=de==='campo'
   ?'elSelecionaBuild('+indiceSlot+',\''+escJs(k)+'\',this.value)'
   :'elSelecionaBuildLista(\''+escJs(de)+'\',\''+escJs(entrada.entryId)+'\',\''+escJs(k)+'\',this.value)';
  var h='<select class=elbsel onclick="event.stopPropagation()" '
   +'onchange="event.stopPropagation();'+acao+'" title="qual build está valendo">'
   +'<option value="base"'+(ativa==='base'?' selected':'')+'>BÁSICA</option>';
  for(var i=0;i<L.length;i++){
   var valor=String(L[i]&&L[i].buildId||'');if(!valor)continue;
   /* A build já aplicada é sempre exibida. As demais falham fechado enquanto
      a identidade canônica da função ainda não estiver disponível. */
   if(de!=='campo'&&valor!==ativa&&!buildCompativelComEntradaNoDesenho(L[i],entrada))continue;
   h+='<option value="'+esc(valor)+'"'+(valor===ativa?' selected':'')+'>'
    +esc(String(L[i].nome||('build '+(i+1))))+'</option>';
  }
  return h+'<option value="nova">CRIAR NOVA BUILD</option></select>';
 }
 window.elBotoesExtra=seletorBuildDoCard;

 /* ---------- 2 · UNICIDADE DA OCORRENCIA ----------
    Builds sao muitas; a ocorrencia do mesmo card_id no Elenco e uma so,
    somando campo, Reservas e Fora do banco. Campo + Reservas tambem aceitam
    uma unica VERSAO do mesmo jogador. O identificador nao vem do nome: no
    eFootballDB, base_pes_id sao os 23 bits inferiores do card_id. A relacao
    foi conferida nos 29.807 perfis brutos locais sem uma divergencia.
    Este servico apenas audita e fecha portas novas: nunca apaga nem escolhe
    silenciosamente entre duplicatas legadas durante render. */
 function quantosTit(){
  var n=0, s=MT.slots||[];
  for(var i=0;i<s.length;i++) if(s[i]&&s[i].key) n++;
  return n;
 }
 function cardIdCanonico(k){ return String(k||'').split('|')[0].split('@')[0]; }
 function playerIdCanonico(k){
  var id=cardIdCanonico(k);
  if(!/^\d+$/.test(id)) return null;
  var n=Number(id);
  if(!Number.isSafeInteger(n)||n<0) return null;
  return String(n%8388608);
 }
 function ocorrenciasDoCard(k,m){
  m=m||MT; var id=cardIdCanonico(k),out=[];
  (m.slots||[]).forEach(function(sl,i){if(sl&&sl.key&&cardIdCanonico(sl.key)===id)
   out.push({group:'campo',index:i,cardId:id,cardKey:sl.key,buildId:String(sl.buildId||'base'),slot:sl});});
  [['banco',m.banco],['fora',m.elenco]].forEach(function(par){
   var grupo=par[0],lista=par[1]||[],meta=m.listEntries&&Array.isArray(m.listEntries[grupo])?m.listEntries[grupo]:[];
   lista.forEach(function(chave,i){if(cardIdCanonico(chave)!==id)return;var e=meta[i];
    out.push({group:grupo,index:i,cardId:id,cardKey:chave,buildId:String(e&&e.buildId||'base'),entry:e||null});});
  });
  return out;
 }
 function ocorrenciasAtivasDoJogador(k,m){
  m=m||MT;var pid=playerIdCanonico(k),out=[];
  if(pid===null)return out;
  (m.slots||[]).forEach(function(sl,i){if(sl&&sl.key&&playerIdCanonico(sl.key)===pid)
   out.push({group:'campo',index:i,cardKey:sl.key,cardId:cardIdCanonico(sl.key),
    playerId:pid,buildId:String(sl.buildId||'base'),slot:sl});});
  var meta=m.listEntries&&Array.isArray(m.listEntries.banco)?m.listEntries.banco:[];
  (m.banco||[]).forEach(function(chave,i){if(playerIdCanonico(chave)!==pid)return;var e=meta[i];
   out.push({group:'banco',index:i,cardKey:chave,cardId:cardIdCanonico(chave),
    playerId:pid,buildId:String(e&&e.buildId||'base'),entry:e||null});});
  return out;
 }
 function auditoriaUnicidade(m){
  m=m||MT;var mapa={},duplicadas=[],jogadores={},jogadoresDuplicados=[];
  (m.slots||[]).forEach(function(sl){if(sl&&sl.key)(mapa[cardIdCanonico(sl.key)]||(mapa[cardIdCanonico(sl.key)]=[])).push('campo');});
  [['banco',m.banco],['fora',m.elenco]].forEach(function(par){(par[1]||[]).forEach(function(k){
   (mapa[cardIdCanonico(k)]||(mapa[cardIdCanonico(k)]=[])).push(par[0]);});});
  Object.keys(mapa).forEach(function(id){if(mapa[id].length>1)duplicadas.push({cardId:id,groups:mapa[id].slice(),count:mapa[id].length});});
  (m.slots||[]).forEach(function(sl,i){if(!sl||!sl.key)return;var pid=playerIdCanonico(sl.key);if(pid===null)return;
   (jogadores[pid]||(jogadores[pid]=[])).push({group:'campo',index:i,cardId:cardIdCanonico(sl.key)});});
  (m.banco||[]).forEach(function(k,i){var pid=playerIdCanonico(k);if(pid===null)return;
   (jogadores[pid]||(jogadores[pid]=[])).push({group:'banco',index:i,cardId:cardIdCanonico(k)});});
  Object.keys(jogadores).forEach(function(pid){var os=jogadores[pid];if(os.length>1)
   jogadoresDuplicados.push({playerId:pid,occurrences:os.slice(),count:os.length});});
  return {ok:duplicadas.length===0&&jogadoresDuplicados.length===0,duplicates:duplicadas,
   activePlayerDuplicates:jogadoresDuplicados};
 }
 function avisaDuplicata(k,legado){
  var c=null;try{c=mtCard(k);}catch(e){}
  alert(legado
   ?'Este card aparece mais de uma vez no estado salvo. Nada foi alterado. Remova uma das ocorrências antes de continuar.'
   :'Este card já está no Elenco. Mova a ocorrência existente em vez de adicioná-la novamente.');
  return false;
 }
 function avisaJogadorDuplicado(k,legado){
  alert(legado
   ?'Há mais de uma versão deste jogador entre Titulares e Reservas. Nada foi alterado. Escolha qual versão manter e mova a outra para Fora do banco.'
   :'Outra versão deste jogador já está entre Titulares ou Reservas. Mova a ocorrência existente ou escolha Fora do banco.');
  return false;
 }
 function mesmaOcorrencia(a,b){return !!(a&&b&&a.group===b.group&&a.index===b.index&&a.cardId===b.cardId);}
 function planoMovimento(k,group,index){
  var os=ocorrenciasDoCard(k),mesma=os.filter(function(o){return o.group===group&&(index==null||o.index===index);});
  if(os.length>1)return {ok:false,legacyDuplicate:true,occurrences:os};
  var source=os[0]||null,cardId=cardIdCanonico(k),playerId=playerIdCanonico(k),targetActive=group==='campo'||group==='banco';
  if(targetActive&&playerId!==null){
   var ativas=ocorrenciasAtivasDoJogador(k),outras=ativas.filter(function(o){return !mesmaOcorrencia(o,source);});
   /* Campo -> Reservas e a primeira etapa segura para resolver uma duplicata
      legada. O caminho inverso nao pode recolocar a segunda versao no Campo:
      enquanto houver outra versao ativa, Reservas -> Campo falha fechado. */
   var sourceAtiva=source&&(source.group==='campo'||source.group==='banco');
   var reabreDuplicata=sourceAtiva&&source.group==='banco'&&group==='campo';
   if(outras.length&&(!sourceAtiva||reabreDuplicata))return {ok:false,playerConflict:true,
    legacyPlayerDuplicate:ativas.length>1,playerId:playerId,occurrences:ativas,
    source:source,cardId:cardId,target:{group:group,index:index}};
  }
  return {ok:true,noOp:mesma.length===1,source:source,buildId:source?source.buildId:'base',
   cardId:cardId,playerId:playerId,target:{group:group,index:index}};
 }
 function soltaOcorrencia(plano){
  var o=plano&&plano.source;if(!o||plano.noOp)return true;
  if(o.group==='campo'){var sl=(MT.slots||[])[o.index];if(sl&&cardIdCanonico(sl.key)===plano.cardId){sl.key=null;sl.buildId='base';}}
  else{var lista=o.group==='banco'?MT.banco:MT.elenco;if(Array.isArray(lista)&&cardIdCanonico(lista[o.index])===plano.cardId)lista.splice(o.index,1);}
  return true;
 }
 function avisaPlano(k,p){
  if(p&&p.playerConflict)return avisaJogadorDuplicado(k,!!p.legacyPlayerDuplicate);
  return avisaDuplicata(k,!!(p&&p.legacyDuplicate));
 }
 window.ElencoCardInvariant=Object.freeze({cardId:cardIdCanonico,playerId:playerIdCanonico,
  occurrences:ocorrenciasDoCard,activePlayerOccurrences:ocorrenciasAtivasDoJogador,
  audit:auditoriaUnicidade,planMove:planoMovimento,detach:soltaOcorrencia,
  notify:function(k,legacy){return avisaDuplicata(k,legacy);},notifyPlan:avisaPlano});
 function podeMover(k,group,index){var p=planoMovimento(k,group,index);if(!p.ok){avisaPlano(k,p);return null;}return p;}
 function cabeNoBanco(){
  if((MT.banco||[]).length < TETO_BANCO) return true;
  alert("O banco de reservas j\u00e1 est\u00e1 cheio \u2014 s\u00e3o "+TETO_BANCO
   +" vagas.\n\nTire algu\u00e9m do banco antes de p\u00f4r mais um.");
  return false;
 }
 function cabeNoCampo(){
  if(quantosTit() < TETO_TIT) return true;
  alert("O time j\u00e1 est\u00e1 com os "+TETO_TIT+" titulares.\n\n"
   +"Tire algu\u00e9m do campo antes de p\u00f4r mais um.");
  return false;
 }

 /* ---------- 3 · MOVER DE UM LUGAR PARA O OUTRO ----------
    ⚠️ CORRIGIDO no teste de 16/08: a primeira versao caia no "primeiro
    slot livre qualquer" e mandou o Messi para o GOLEIRO. Escalar no lugar
    errado e pior que nao escalar. */
 function achaVaga(c){
  var s=MT.slots||[], pos=c?(c.np||c.pos):null, i, j;
  for(i=0;i<s.length;i++) if(s[i]&&!s[i].key&&s[i].pos===pos) return i;
  var fd=[]; try{ fd=MT_FUNCS[pos]||[]; }catch(e){}
  for(i=0;i<s.length;i++){
   if(!s[i]||s[i].key) continue;
   var fv=[]; try{ fv=MT_FUNCS[s[i].pos]||[]; }catch(e){}
   for(j=0;j<fd.length;j++) if(fv.indexOf(fd[j])>=0) return i;
  }
  return -1;
 }
 function buildSalvaDaOcorrencia(m,cardId,buildId){
  if(!buildId||buildId==='base')return null;
  var L=m&&m.builds&&Array.isArray(m.builds[cardId])?m.builds[cardId]:[];
  for(var i=0;i<L.length;i++)if(String(L[i]&&L[i].buildId||'')===String(buildId))return L[i];
  return null;
 }
 function idsDeEntradaUsados(m){var usados={};['banco','fora'].forEach(function(g){
  var L=m&&m.listEntries&&Array.isArray(m.listEntries[g])?m.listEntries[g]:[];
  L.forEach(function(e){if(e&&e.entryId)usados[e.entryId]=1;});});
  (m&&m.slots||[]).forEach(function(sl){if(sl&&sl.entryId)usados[sl.entryId]=1;});return usados;}
 var _entryMovSeq=0;
 function novoEntryIdMovimento(usados){var id='';try{if(window.crypto&&window.crypto.randomUUID)
  id='entry_'+window.crypto.randomUUID().toLowerCase();}catch(e){}
  if(!id)id='entry_move_'+Date.now().toString(36)+'_'+(++_entryMovSeq).toString(36);
  while(usados[id])id=id+'_'+(++_entryMovSeq);usados[id]=1;return id;}
 function funcaoDaFotoOcorrencia(m,k,buildId,corrente){
  var id=cardIdCanonico(k),b=buildSalvaDaOcorrencia(m,id,buildId);
  if(buildId&&buildId!=='base')return b&&b.func?String(b.func):null;
  return String(corrente||String(k||'').split('|').slice(1).join('|')||'').trim()||null;
 }
 function fotoCompletaDaOcorrencia(plano){
  var o=plano&&plano.source;if(!o)return null;var m=MT,e={},k='';
  if(o.group==='campo'){var sl=(m.slots||[])[o.index];if(!sl||!sl.key)return null;
   k=String(sl.key);e={entryId:sl.entryId||null,cardKey:k,buildId:String(sl.buildId||'base'),functionId:sl.func||null};}
  else{var lista=o.group==='banco'?m.banco:m.elenco,meta=m.listEntries&&Array.isArray(m.listEntries[o.group])?m.listEntries[o.group]:[];
   k=String(lista&&lista[o.index]||o.cardKey||'');e=Object.assign({},meta[o.index]||o.entry||{});}
  if(!k)return null;e.cardId=cardIdCanonico(k);e.cardKey=k;e.buildId=String(e.buildId||o.buildId||'base');
  e.functionId=funcaoDaFotoOcorrencia(m,k,e.buildId,e.functionId||(o.slot&&o.slot.func));
  if(!e.functionId)return null;if(!e.entryId)e.entryId=novoEntryIdMovimento(idsDeEntradaUsados(m));return e;
 }
 function passoPermitido(origem,destino){return origem==='campo'&&destino==='banco'
  ||origem==='banco'&&(destino==='campo'||destino==='fora')
  ||origem==='fora'&&destino==='banco';}
 function funcaoCabeNoSlot(sl,func){var fs=[];try{fs=MT_FUNCS[sl&&sl.pos]||[];}catch(e){}
  for(var i=0;i<fs.length;i++)if(mesmaFuncaoTecnica(fs[i],func))return true;return false;}
 var POSICAO_ESTRUTURAL_ALIAS={GO:'GK',GK:'GK',GOLEIRO:'GK',CB:'ZC',ZAG:'ZC',ZAGUEIRO:'ZC',
  RB:'LD','LATERAL DIREITO':'LD',LB:'LE','LATERAL ESQUERDO':'LE',DMF:'VOL',RMF:'MLD',LMF:'MLE',
  AMF:'MO',MAT:'MO',CMF:'MC',MLG:'MC',SS:'SA',CF:'CA',RWF:'PD',PTD:'PD',LWF:'PE',PTE:'PE'};
 function normalizaPosicaoEstrutural(pos){var p=String(pos||'').normalize('NFD')
  .replace(/[\u0300-\u036f]/g,'').toUpperCase().replace(/\s+/g,' ').trim();
  return POSICAO_ESTRUTURAL_ALIAS[p]||p;}
 function posicaoEstruturalDaVaga(sl){var p=normalizaPosicaoEstrutural(sl&&sl.pos);if(p)return p;
  var opcoes=[];try{opcoes=opcoesDaVaga(sl)||[];}catch(e){}return normalizaPosicaoEstrutural(opcoes[0]);}
 function funcaoEstruturalDaVaga(sl,k){var pos=posicaoEstruturalDaVaga(sl),prova=Object.assign({},sl,{pos:pos}),f=null;
  try{f=funcaoDaVaga(prova,k);}catch(e){}if(f)return String(f);var fs=[];try{fs=MT_FUNCS[pos]||[];}catch(e){}
  return String(fs[0]||(sl&&sl.func)||String(k||'').split('|').slice(1).join('|')||'').trim()||null;}
 function fotoEstruturalMovimento(){return {slots:JSON.parse(JSON.stringify(MT.slots||[])),
  banco:(MT.banco||[]).slice(),elenco:(MT.elenco||[]).slice(),
  listEntries:JSON.parse(JSON.stringify(MT.listEntries||{})),selo:window.EL_SELO||0};}
 function restauraEstruturalMovimento(f){MT.slots=f.slots;MT.banco=f.banco;MT.elenco=f.elenco;
  MT.listEntries=f.listEntries;window.EL_SELO=f.selo;}
 function retiraFonteAtomica(plano){var o=plano.source;if(o.group==='campo'){
   var sl=(MT.slots||[])[o.index];if(!sl||cardIdCanonico(sl.key)!==plano.cardId)return false;
   sl.key=null;sl.buildId='base';sl.entryId=null;return true;}
  var lista=o.group==='banco'?MT.banco:MT.elenco,meta=MT.listEntries&&MT.listEntries[o.group];
  if(!Array.isArray(lista)||!Array.isArray(meta)||cardIdCanonico(lista[o.index])!==plano.cardId)return false;
  lista.splice(o.index,1);meta.splice(o.index,1);return true;}
 function colocaDestinoAtomico(destino,indice,foto){
  if(destino==='campo'){var sl=(MT.slots||[])[indice];if(!sl||sl.key||!funcaoCabeNoSlot(sl,foto.functionId))return false;
   sl.key=foto.cardKey;sl.buildId=foto.buildId;sl.func=foto.functionId;sl.entryId=foto.entryId;return true;}
  var campo=destino==='banco'?'banco':'elenco',colecao=destino==='banco'?'banco':'fora';
  MT[campo]=MT[campo]||[];MT.listEntries=MT.listEntries||{};MT.listEntries[colecao]=MT.listEntries[colecao]||[];
  var e=Object.assign({},foto,{collection:colecao});
  if(destino==='banco'){MT[campo].push(foto.cardKey);MT.listEntries[colecao].push(e);}
  else{MT[campo].unshift(foto.cardKey);MT.listEntries[colecao].unshift(e);}return true;
 }
 function transfereOcorrenciaAtomica(k,destino,indice){
  try{if(typeof window.elSincronizaEntradasDasListas==='function')window.elSincronizaEntradasDasListas(MT);}catch(e){}
  var plano=podeMover(k,destino,indice);if(!plano||plano.noOp||!plano.source)return {ok:false,motivo:'origem-ausente'};
  if(!passoPermitido(plano.source.group,destino))return {ok:false,motivo:'salto-proibido'};
  if(destino==='banco'&&(MT.banco||[]).length>=TETO_BANCO){cabeNoBanco();return {ok:false,motivo:'reservas-cheias'};}
  if(destino==='campo'&&(!Number.isInteger(+indice)||!(MT.slots||[])[+indice]))return {ok:false,motivo:'vaga-ausente'};
  var foto=fotoCompletaDaOcorrencia(plano);if(!foto)return {ok:false,motivo:'fotografia-invalida'};
  if(foto.buildId!=='base'&&!buildSalvaDaOcorrencia(MT,foto.cardId,foto.buildId))return {ok:false,motivo:'build-ausente'};
  var antes=fotoEstruturalMovimento();
  try{
   if(!retiraFonteAtomica(plano)||!colocaDestinoAtomico(destino,+indice,foto))throw new Error('destino-invalido');
   window.EL_SELO=(window.EL_SELO||0)+1;
   try{if(window.elLimpaCachePontuacao)window.elLimpaCachePontuacao();}catch(e){}
   userStateSave();mtRender();return {ok:true,source:plano.source.group,target:destino,entry:Object.assign({},foto)};
  }catch(e){restauraEstruturalMovimento(antes);return {ok:false,motivo:e&&e.message||'falha'};}
 }
 function aplicaFotoNaVagaEstrutural(sl,foto,resolverFuncao){
  if(!sl||!foto||!foto.cardKey)throw new Error('foto-de-vaga-invalida');
  sl.key=String(foto.cardKey);sl.buildId=String(foto.buildId||'base');
  sl.entryId=foto.entryId||null;sl.func=foto.functionId||null;
  var resolvida=typeof resolverFuncao==='function'?resolverFuncao(sl,sl.key):sl.func;
  if(resolvida)sl.func=String(resolvida);
  if(!sl.func)throw new Error('funcao-da-vaga-ausente');
  return sl;
 }
 /* Serviço estrutural puro: troca somente os ocupantes. A geometria e a
    posição da vaga, assim como o índice da Reserva, permanecem no lugar. */
 function trocaPayloadsNoModelo(m,origem,alvo,fotoOrigem,fotoAlvo,resolverFuncao){
  if(!m||!origem||!alvo||!fotoOrigem||!fotoAlvo)throw new Error('permuta-invalida');
  var campoOrigem=origem.group==='campo',campoAlvo=alvo.group==='campo';
  if(campoOrigem&&campoAlvo){
   if(origem.index===alvo.index)throw new Error('mesma-ocorrencia');
   aplicaFotoNaVagaEstrutural(m.slots&&m.slots[origem.index],fotoAlvo,resolverFuncao);
   aplicaFotoNaVagaEstrutural(m.slots&&m.slots[alvo.index],fotoOrigem,resolverFuncao);
   return true;
  }
  if(campoOrigem===campoAlvo)throw new Error('grupos-sem-permuta');
  var campo=campoOrigem?origem:alvo,banco=campoOrigem?alvo:origem;
  var fotoCampo=campoOrigem?fotoOrigem:fotoAlvo,fotoBanco=campoOrigem?fotoAlvo:fotoOrigem;
  if(banco.group!=='banco'||!Array.isArray(m.banco)||!m.listEntries
     ||!Array.isArray(m.listEntries.banco)||banco.index<0||banco.index>=m.banco.length
     ||banco.index>=m.listEntries.banco.length)throw new Error('reserva-invalida');
  aplicaFotoNaVagaEstrutural(m.slots&&m.slots[campo.index],fotoBanco,resolverFuncao);
  m.banco[banco.index]=String(fotoCampo.cardKey);
  m.listEntries.banco[banco.index]=Object.assign({},fotoCampo,{collection:'banco'});
  return true;
 }
 function movePayloadCampoParaVagaVaziaNoModelo(m,origem,indiceAlvo,foto,resolverFuncao){
  var fonte=m&&m.slots&&m.slots[origem&&origem.index],alvo=m&&m.slots&&m.slots[indiceAlvo];
  if(!origem||origem.group!=='campo'||!fonte||!fonte.key||!alvo||alvo.key
     ||origem.index===indiceAlvo||String(fonte.key)!==String(foto&&foto.cardKey||''))
   throw new Error('movimento-campo-invalido');
  aplicaFotoNaVagaEstrutural(alvo,foto,resolverFuncao);
  fonte.key=null;fonte.buildId='base';fonte.entryId=null;
  return true;
 }
 function seloEstruturalDaVaga(sl,indice){
  if(!sl)return '';
  return [String(indice),String(sl.pos||''),String(sl.func||''),String(sl.x),String(sl.y),
   sl.posFixa?'1':'0',sl.mv?'1':'0',String(sl.key||'')].join('\u001f');
 }
 function moveReservaParaVagaVaziaNoModelo(m,origem,foto,pedido){
  var alvo=m&&m.slots&&m.slots[pedido&&pedido.index],meta=m&&m.listEntries&&m.listEntries.banco;
  if(!origem||origem.group!=='banco'||!Array.isArray(m&&m.banco)||!Array.isArray(meta)
     ||origem.index<0||origem.index>=m.banco.length||origem.index>=meta.length
     ||!alvo||alvo.key||!foto||!foto.cardKey)throw new Error('movimento-reserva-invalido');
  alvo.pos=String(pedido.pos);
  aplicaFotoNaVagaEstrutural(alvo,Object.assign({},foto,{cardKey:String(pedido.cardKey),
   functionId:String(pedido.func)}),function(){return pedido.func;});
  m.banco.splice(origem.index,1);meta.splice(origem.index,1);
  return true;
 }
 function localizaOcorrenciaDnD(d){
  if(!d||!d.k)return null;var grupo=d.group||d.de;
  if(grupo!=='campo'&&grupo!=='banco')return null;
  var os=ocorrenciasDoCard(d.k);if(os.length!==1)return null;var o=os[0];
  if(o.group!==grupo)return null;
  if(grupo==='campo'&&Number.isInteger(+d.index)&&+o.index!==+d.index)return null;
  if(grupo==='banco'&&d.entryId
     &&String(o.entry&&o.entry.entryId||'')!==String(d.entryId))return null;
  return o;
 }
 function trocaOcorrenciasAtomica(origemDesc,alvoDesc){
  var antes=fotoEstruturalMovimento(),tentouSalvar=false,tentouRender=false;
  try{
   if(typeof window.elSincronizaEntradasDasListas==='function')window.elSincronizaEntradasDasListas(MT);
   var origem=localizaOcorrenciaDnD(origemDesc),alvo=localizaOcorrenciaDnD(alvoDesc);
   if(!origem||!alvo||mesmaOcorrencia(origem,alvo))throw new Error('ocorrencia-invalida');
   var grupos=(origem.group==='campo'&&alvo.group==='campo')
    ||(origem.group==='campo'&&alvo.group==='banco')
    ||(origem.group==='banco'&&alvo.group==='campo');
   if(!grupos)throw new Error('grupos-sem-permuta');
   var fotoOrigem=fotoCompletaDaOcorrencia({source:origem,cardId:origem.cardId,buildId:origem.buildId});
   var fotoAlvo=fotoCompletaDaOcorrencia({source:alvo,cardId:alvo.cardId,buildId:alvo.buildId});
   if(!fotoOrigem||!fotoAlvo)throw new Error('fotografia-invalida');
   if((fotoOrigem.buildId!=='base'&&!buildSalvaDaOcorrencia(MT,fotoOrigem.cardId,fotoOrigem.buildId))
      ||(fotoAlvo.buildId!=='base'&&!buildSalvaDaOcorrencia(MT,fotoAlvo.cardId,fotoAlvo.buildId)))
    throw new Error('build-ausente');
   trocaPayloadsNoModelo(MT,origem,alvo,fotoOrigem,fotoAlvo,function(sl,k){return funcaoDaVaga(sl,k);});
   window.EL_SELO=(window.EL_SELO||0)+1;
   try{if(window.elLimpaCachePontuacao)window.elLimpaCachePontuacao();}catch(e){}
   tentouSalvar=true;var salvo=userStateSave();if(salvo===false)throw new Error('save-rejeitado');
   tentouRender=true;
   mtRender();
   return {ok:true,source:origem.group,target:alvo.group};
  }catch(e){
   restauraEstruturalMovimento(antes);
   if(tentouSalvar)try{userStateSave();}catch(rollbackSave){}
   if(tentouRender)try{mtRender();}catch(rollbackRender){}
   return {ok:false,motivo:e&&e.message||'falha'};
  }
 }
 function moveCampoParaVagaVaziaAtomica(origemDesc,indiceAlvo){
  var antes=fotoEstruturalMovimento(),tentouSalvar=false,tentouRender=false;
  try{
   if(typeof window.elSincronizaEntradasDasListas==='function')window.elSincronizaEntradasDasListas(MT);
   var origem=localizaOcorrenciaDnD(origemDesc),ix=+indiceAlvo,alvo=MT.slots&&MT.slots[ix];
   if(!origem||origem.group!=='campo'||!Number.isInteger(ix)||!alvo||alvo.key)
    throw new Error('vaga-vazia-invalida');
   var foto=fotoCompletaDaOcorrencia({source:origem,cardId:origem.cardId,buildId:origem.buildId});
   if(!foto)throw new Error('fotografia-invalida');
   if(foto.buildId!=='base'&&!buildSalvaDaOcorrencia(MT,foto.cardId,foto.buildId))
    throw new Error('build-ausente');
   movePayloadCampoParaVagaVaziaNoModelo(MT,origem,ix,foto,function(sl,k){return funcaoDaVaga(sl,k);});
   window.EL_SELO=(window.EL_SELO||0)+1;
   try{if(window.elLimpaCachePontuacao)window.elLimpaCachePontuacao();}catch(e){}
   tentouSalvar=true;var salvo=userStateSave();if(salvo===false)throw new Error('save-rejeitado');
   tentouRender=true;
   mtRender();
   return {ok:true,source:'campo',target:'campo'};
  }catch(e){
   restauraEstruturalMovimento(antes);
   if(tentouSalvar)try{userStateSave();}catch(rollbackSave){}
   if(tentouRender)try{mtRender();}catch(rollbackRender){}
   return {ok:false,motivo:e&&e.message||'falha'};
  }
 }
 function moveReservaParaCampoAtomica(pedido){
  var antes=fotoEstruturalMovimento(),tentouSalvar=false,tentouRender=false;
  try{
   if(typeof window.elSincronizaEntradasDasListas==='function')window.elSincronizaEntradasDasListas(MT);
   if(!pedido||!pedido.entryId)throw new Error('origem-sem-identidade');
   var origem=localizaOcorrenciaDnD({group:'banco',entryId:pedido.entryId,k:pedido.sourceKey});
   if(!origem||origem.group!=='banco')throw new Error('origem-alterada');
   var ix=+pedido.index,alvo=MT.slots&&MT.slots[ix];
   if(!Number.isInteger(ix)||!alvo)throw new Error('vaga-ausente');
   if(alvo.key)throw new Error('vaga-ocupada');
   if(String(pedido.slotToken||'')!==seloEstruturalDaVaga(alvo,ix))throw new Error('vaga-alterada');
   var pos=posicaoEstruturalDaVaga(alvo),posPedida=normalizaPosicaoEstrutural(pedido.pos),key=String(origem.cardKey||'');
   if(!pos||posPedida!==pos)throw new Error('posicao-da-vaga-alterada');
   if(!key||String(pedido.cardKey||'')!==key||cardIdCanonico(key)!==origem.cardId)
    throw new Error('card-indisponivel');
   var foto=fotoCompletaDaOcorrencia({source:origem,cardId:origem.cardId,buildId:origem.buildId});
   if(!foto)throw new Error('fotografia-invalida');
   if(foto.buildId!=='base'&&!buildSalvaDaOcorrencia(MT,foto.cardId,foto.buildId))
    throw new Error('build-ausente');
   var func=funcaoEstruturalDaVaga(alvo,key)||foto.functionId;
   if(!func)throw new Error('funcao-da-vaga-ausente');
   moveReservaParaVagaVaziaNoModelo(MT,origem,foto,{index:ix,pos:pos,func:func,cardKey:key});
   window.EL_SELO=(window.EL_SELO||0)+1;
   try{if(window.elLimpaCachePontuacao)window.elLimpaCachePontuacao();}catch(e){}
   tentouSalvar=true;var salvo=userStateSave();if(salvo===false)throw new Error('save-rejeitado');
   tentouRender=true;
   mtRender();
   return {ok:true,source:'banco',target:'campo',entry:Object.assign({},foto)};
  }catch(e){
   restauraEstruturalMovimento(antes);
   if(tentouSalvar)try{userStateSave();}catch(rollbackSave){}
   if(tentouRender)try{mtRender();}catch(rollbackRender){}
   return {ok:false,motivo:e&&e.message||'falha'};
  }
 }
 function removeOcorrenciaAtomica(pedido){
  var antes=fotoEstruturalMovimento(),tentouSalvar=false,tentouRender=false;
  try{
   if(typeof window.elSincronizaEntradasDasListas==='function')window.elSincronizaEntradasDasListas(MT);
   if(!pedido||!pedido.cardKey)throw new Error('ocorrencia-invalida');
   var grupo=pedido.group,os=ocorrenciasDoCard(pedido.cardKey),origem=os.length===1?os[0]:null;
   if(!origem||origem.group!==grupo)throw new Error('ocorrencia-alterada');
   if(grupo==='campo'){
    if(!Number.isInteger(+pedido.index)||+origem.index!==+pedido.index)
     throw new Error('ocorrencia-alterada');
    if(pedido.entryId&&String(origem.slot&&origem.slot.entryId||'')!==String(pedido.entryId))
     throw new Error('ocorrencia-alterada');
   }else if(grupo==='banco'||grupo==='fora'){
    if(!pedido.entryId||String(origem.entry&&origem.entry.entryId||'')!==String(pedido.entryId))
     throw new Error('ocorrencia-alterada');
   }else throw new Error('origem-invalida');
   var plano=planoMovimento(origem.cardKey,origem.group,origem.index);
   if(!plano||!plano.ok||!plano.source||!mesmaOcorrencia(plano.source,origem)
      ||!retiraFonteAtomica(plano))throw new Error('ocorrencia-alterada');
   window.EL_SELO=(window.EL_SELO||0)+1;
   try{if(window.elLimpaCachePontuacao)window.elLimpaCachePontuacao();}catch(e){}
   tentouSalvar=true;var salvo=userStateSave();if(salvo===false)throw new Error('save-rejeitado');
   tentouRender=true;mtRender();
   return {ok:true,source:origem.group,cardId:origem.cardId,entryId:pedido.entryId||null};
  }catch(e){
   restauraEstruturalMovimento(antes);
   if(tentouSalvar)try{userStateSave();}catch(rollbackSave){}
   if(tentouRender)try{mtRender();}catch(rollbackRender){}
   return {ok:false,motivo:e&&e.message||'falha'};
  }
 }
 window.ElencoOccurrenceSwap=Object.freeze({commit:trocaOcorrenciasAtomica});
 window.ElencoOccurrenceRemoval=Object.freeze({commit:removeOcorrenciaAtomica});
 function paraOCampo(k){
  var os=ocorrenciasDoCard(k),o=os.length===1?os[0]:null;if(!o||o.group!=='banco')return false;
  if(window.ElencoAddController&&typeof window.ElencoAddController.openMoveToField==='function')
   return window.ElencoAddController.openMoveToField(k);
  return false;
 }
 function paraOBanco(k){
  var r=transfereOcorrenciaAtomica(k,'banco',-1);return !!r.ok;
 }
 function paraForaDoBanco(k){
  var r=transfereOcorrenciaAtomica(k,'fora',-1);return !!r.ok;
 }
 function tiraDoElenco(k){
  try{if(typeof window.elSincronizaEntradasDasListas==='function')window.elSincronizaEntradasDasListas(MT);}catch(e){}var os=ocorrenciasDoCard(k),o=os.length===1?os[0]:null;
  if(!o||o.group!=='fora')return false;var c=null;try{c=mtCard(k);}catch(e){}
  if(!confirm("Tirar "+((c&&c.nome)||"este card")+" do seu elenco?\n\nIsso n\u00e3o apaga nada do seu jogo, s\u00f3 daqui."))return false;
  var plano=planoMovimento(k,'fora',o.index),antes=fotoEstruturalMovimento();
  try{if(!plano.ok||!retiraFonteAtomica(plano))return false;window.EL_SELO=(window.EL_SELO||0)+1;
   userStateSave();mtRender();return true;}catch(e){restauraEstruturalMovimento(antes);return false;}
 }
 window.ElencoOccurrenceTransfer=Object.freeze({snapshot:function(k){var os=ocorrenciasDoCard(k),o=os.length===1?os[0]:null;
  if(!o)return null;return fotoCompletaDaOcorrencia({source:o,cardId:cardIdCanonico(k),buildId:o.buildId});},
  slotToken:seloEstruturalDaVaga,canStep:passoPermitido,commit:transfereOcorrenciaAtomica,
  commitReserveToField:moveReservaParaCampoAtomica});
 window.elNormalizaPosicaoEstrutural=normalizaPosicaoEstrutural;
 window.elPosicaoEstruturalDaVaga=posicaoEstruturalDaVaga;
 window.elFuncaoEstruturalDaVaga=funcaoEstruturalDaVaga;
 window.elFuncaoCabeNoSlot=funcaoCabeNoSlot;
 window.elParaCampo=paraOCampo; window.elParaBanco=paraOBanco;
 window.elParaFora=paraForaDoBanco; window.elExclui=tiraDoElenco;

 (function(){
  var _ms=window.mtSlots; if(typeof _ms!=="function") return;
  window.mtSlots=function(){
    var g=(MT.slots||[]).map(function(x){
     return x?{pos:x.pos, func:x.func, posFixa:!!x.posFixa, mv:!!x.mv,
               x:x.x, y:x.y, buildId:x.buildId}:null; });
   var r=_ms.apply(this,arguments);
   var s=MT.slots||[], i;
   for(i=0;i<s.length;i++){
    if(!s[i]||!g[i]) continue;
    if(g[i].mv){ s[i].x=g[i].x; s[i].y=g[i].y; s[i].mv=1; }
     if(g[i].posFixa || g[i].mv){
      if(g[i].pos){ s[i].pos=g[i].pos; }
      if(g[i].func){ s[i].func=g[i].func; }
      if(g[i].posFixa) s[i].posFixa=1;
     }
     if(g[i].buildId!==undefined) s[i].buildId=g[i].buildId;
   }
   return r;
  };
 })();

 /* ---------- 5 · O CARD UNICO ---------- */
 function botao(fn,k,tit,rot,cls){
  return '<button class="elbt '+(cls||"")+'" title="'+esc(tit)+'" '
   +'onclick="event.stopPropagation();'+fn+'(\''+k+'\')">'+rot+'</button>';
 }
 var FAIXA={
  ata:["CA","SA","PE","PD"],
  mei:["MO","MC","VOL","MLE","MLD"],
  def:["ZC","LE","LD"],
  gol:["GK"]
 };
 function faixaDe(pos){
  for(var f in FAIXA) if(FAIXA[f].indexOf(pos)>=0) return f;
  return "mei";
 }
 function siglaVisivel(pos){
  if(pos==="GK") return "GO";
  if(pos==="MO") return "MAT";
  if(pos==="MC") return "MLG";
  if(pos==="PE") return "PTE";
  if(pos==="PD") return "PTD";
  return pos||"";
 }
 function seletorDePosicao(sl){
  if(!sl) return "";
  if(sl.pos==="GK") return '<b class=elvagafixa>GO</b>';
  var ix=(MT.slots||[]).indexOf(sl);
  var ops=FAIXA[faixaDe(sl.pos)]||[], h, i;
  if(ops.indexOf(sl.pos)<0) ops=ops.concat([sl.pos]);
  h='<select class=elpsel onclick="event.stopPropagation()" '
   +'onchange="event.stopPropagation();elTrocaPos('+ix+',this.value)" '
   +'title="a posi\u00e7\u00e3o desta vaga \u2014 a pontua\u00e7\u00e3o '
   +'\u00e9 medida contra o molde dela">';
  for(i=0;i<ops.length;i++)
   h+='<option value="'+esc(ops[i])+'"'+(ops[i]===sl.pos?" selected":"")+'>'+esc(siglaVisivel(ops[i]))+'</option>';
  return h+"</select>";
 }
window.elTrocaPos=function(ix, pos){
 var sl=(MT.slots||[])[ix]; if(!sl) return;
 sl.pos=pos; sl.posFixa=1;
 sl.func=funcaoDaVaga(sl, sl.key);
 window.EL_SELO=(window.EL_SELO||0)+1;
 /* Um unico caminho atualiza a vaga. A nota e calculada com a build ativa,
    a funcao escolhida nesta vaga e o tecnico atual; nenhum insumo da build
    e reescrito e o render abaixo apenas consome o resultado em cache. */
 if(sl.key && typeof window.elPontuacao==='function'){
   try{ window.elPontuacao(sl.key,sl.func,true,sl); }
  catch(e){ if(window.console) console.warn('nao calculei a nova funcao da vaga',e); }
 }
 try{ userStateSave(); }catch(e){}
 try{ mtRender(); }catch(e){}
};

 function posDoCard(c){
  var out=[];
  if(!c) return out;
  if(c.np) out.push(c.np);
  try{ (c.sp||[]).forEach(function(x){
   if(x && x[0] && out.indexOf(x[0])<0) out.push(x[0]); }); }catch(e){}
  if(!out.length && c.pos) out.push(c.pos);
  return out;
 }
 function jogaNaPos(c, pos){
  if(!c || !pos) return true;
  var L=posDoCard(c);
  if(!L.length) return true;
  return L.indexOf(pos)>=0;
 }
 /* Camada de acesso do Elenco. O arrasto segue livre; só a leitura da build
    muda conforme a vaga é compatível, automática ou impossível. */
 var POSICOES_ACEITAS_NA_VAGA={SA:["SA","CA"],CA:["CA","SA"]};
 window.EL_ACESSO="admin"; /* o produto poderá trocar para "cliente" depois */
 function posicoesDaFuncao(func){
  var L=[], p;
  try{ for(p in MT_FUNCS) if((MT_FUNCS[p]||[]).indexOf(func)>=0) L.push(p); }catch(e){}
  return L;
 }
 function vagaAceitaPosicao(posDaVaga,posDoCard){
  var L=POSICOES_ACEITAS_NA_VAGA[posDaVaga]||[posDaVaga];
  return L.indexOf(posDoCard)>=0;
 }
 function estadoDeEncaixe(c,k,sl){
  if(!sl) return {tipo:"livre",pos:(c.np||c.pos||""),func:null};
   var b=null; try{ b=window.elBuildDaVaga&&window.elBuildDaVaga(sl,String(k).split("|")[0].split("@")[0]); }catch(e){}
  var bp=b&&b.func?posicoesDaFuncao(b.func):[];
  for(var i=0;i<bp.length;i++) if(vagaAceitaPosicao(sl.pos,bp[i]))
   return {tipo:"build",pos:bp[i],func:b.func,build:b};
  if(jogaNaPos(c,sl.pos)){
   var fa=funcaoDaVaga({pos:sl.pos,func:null},k);
   return {tipo:(window.EL_ACESSO==="admin"?"automatica":"bloqueada"),pos:sl.pos,func:fa,build:null};
  }
  return {tipo:"incompativel",pos:sl.pos,func:b&&b.func?b.func:null,build:b};
 }
 function pontuacaoAutomatica(k,func){
  var alvo=String(k).split("|")[0]+"|"+func, c=null, b=null, n=0;
  try{ c=mtCard(alvo); if(c && typeof buildOtimo==="function") b=buildOtimo(c); }catch(e){}
  try{ if(b){ b.func=func; n=window.elNotaDaBuild(alvo,b,true)||0; } }catch(e){ n=0; }
  return {n:n,func:func,auto:1};
 }
 window.elPosDoCard=posDoCard; window.elJogaNaPos=jogaNaPos;

 /* Posições possíveis são definidas pela matriz do campo, não pela formação:
    faixa (ataque, dois meios, defesa) + coluna (esquerda, centro, direita). */
 function faixaDaVaga(sl){
  var y=Number(sl&&sl.y);
  if(y>=90) return 'go';
  if(y>=70) return 'defesa';
  if(y<=25) return 'ataque';
  if(y<=45) return 'meio3';
  return 'meio2';
 }
 function ladoDaVaga(sl){
  var faixa=faixaDaVaga(sl), lista=(MT.slots||[]).filter(function(x){return faixaDaVaga(x)===faixa;});
  if(lista.length<2) return 'centro';
  var xs=lista.map(function(x){return Number(x.x);}), mn=Math.min.apply(null,xs), mx=Math.max.apply(null,xs), x=Number(sl.x);
  if(x===mn) return 'esquerda';
  if(x===mx) return 'direita';
  return 'centro';
 }
 function opcoesDaVaga(sl){
  if(sl&&(sl.pos==='GK'||sl.pos==='GO')) return ['GK'];
  var faixa=faixaDaVaga(sl), lado=ladoDaVaga(sl);
  if(faixa==='go') return ['GK'];
  if(faixa==='ataque') return lado==='esquerda'?['SA','PE','CA']:lado==='direita'?['SA','PD','CA']:['CA','SA'];
  /* As duas faixas do meio são intercambiáveis dentro do setor. */
  if(faixa==='meio3'||faixa==='meio2') return lado==='esquerda'?['MLE','VOL','MC','MO']:lado==='direita'?['MLD','VOL','MC','MO']:['VOL','MC','MO'];
  return lado==='esquerda'?['LE','ZC']:lado==='direita'?['LD','ZC']:['ZC'];
 }
 function zcsNaDefesa(ignorar){
  return (MT.slots||[]).filter(function(s){return s!==ignorar&&faixaDaVaga(s)==='defesa'&&s.pos==='ZC';}).length;
 }
 function lateraisNoMeio(pos,ignorar){
  return (MT.slots||[]).filter(function(s){return s!==ignorar&&(faixaDaVaga(s)==='meio2'||faixaDaVaga(s)==='meio3')&&s.pos===pos;}).length;
 }
 function casNoAtaque(ignorar){
  return (MT.slots||[]).filter(function(s){return s!==ignorar&&faixaDaVaga(s)==='ataque'&&s.pos==='CA';}).length;
 }
 function pontasNoAtaque(pos,ignorar){
  return (MT.slots||[]).filter(function(s){return s!==ignorar&&faixaDaVaga(s)==='ataque'&&s.pos===pos;}).length;
 }
 window.elOpcoesDaVaga=opcoesDaVaga;
window.elMudaPosicao=function(indice,pos){
 mtSlots(); var sl=(MT.slots||[])[+indice]; if(!sl) return;
 var opcoes=opcoesDaVaga(sl); if(opcoes.indexOf(pos)<0) return;
 if(pos==='ZC'&&sl.pos!=='ZC'&&zcsNaDefesa(sl)>=3) return;
 if((pos==='MLE'||pos==='MLD')&&sl.pos!==pos&&lateraisNoMeio(pos,sl)>=1) return;
 if(pos==='CA'&&sl.pos!=='CA'&&casNoAtaque(sl)>=2) return;
 if((pos==='PE'||pos==='PD')&&sl.pos!==pos&&pontasNoAtaque(pos,sl)>=1) return;
 /* As travas ficam aqui; a mutacao, o calculo, o save e o unico render
    pertencem todos a elTrocaPos. */
 return window.elTrocaPos(+indice,pos);
};

 function falhaFotoCard(img){
  if(!img)return false;
  img.onerror=null;
  try{img.style.visibility="hidden";}catch(e){}
  try{if(img.parentNode&&img.parentNode.classList)img.parentNode.classList.add("elfoto-fallback");}catch(e2){}
  return true;
 }
 window.elFalhaFotoCard=falhaFotoCard;

 function montaCard(k, de, sl, entrada){
  var c=null; try{ c=mtCard(k); }catch(e){}
  if(!c) return "";
  var encaixe=estadoDeEncaixe(c,k,sl), fv=(sl&&sl.func)?sl.func:null;
  var foraDePosicao=encaixe.tipo==="incompativel";
 var p=foraDePosicao
  ?{n:0,func:fv||c.tipo,nome:null,zero:1,compativel:false}
   :(window.elPontuacao(k,fv,de==='campo',sl,entrada)||{n:0,func:fv||c.tipo,compativel:false});
  var estadoBuild=null;
  try{ if(de==='campo') estadoBuild=estadoDaBuildNaPosicao(k,sl,p,foraDePosicao); }catch(e){}
  var estadoVermelho=!!(estadoBuild&&estadoBuild.id==='vermelho');
  var posMostra=siglaVisivel(encaixe.pos||((sl&&sl.pos)?sl.pos:(c.np||c.pos||"")));
  var idb=String(c.id).split("@")[0];
  /* As fotos dos titulares pertencem ao primeiro quadro visivel do campo:
     todas iniciam juntas. Listas extensas continuam usando carga tardia. */
  var cargaFoto=de==="campo"
   ?' loading="eager" fetchpriority="high" decoding="async"'
   :' loading="lazy" decoding="async"';
  var est=c.modelo||c.tipo||"\u2014";
  var cr="inherit";
  try{ cr=cor(p.n, notaMed(p.func)); }catch(e){}
  var pt = estadoVermelho
   ?('<div class="elpt elzero" title="joga de '
     +esc(posDoCard(c).join(", "))+'">0<i>,00</i></div>')
   :((p.n>0)
     ?('<div class=elpt style="color:'+cr+'">'+doisDec(p.n)+'</div>')
     :('<div class=elpt style="opacity:.45" title="o motor n\u00e3o mede '
       +esc(c.nome)+' como '+esc(p.func)+' \u2014 esta carta n\u00e3o existe '
       +'nessa fun\u00e7\u00e3o no banco">\u2014</div>'));
  var tag = '<span class=elpos>'+esc(posMostra||"\u2014")+'</span>';
  if(de==='campo'&&sl){
   var indice=(MT.slots||[]).indexOf(sl), opcoes=opcoesDaVaga(sl);
   tag='<div class=elposopts>'+opcoes.map(function(pos){
    var ativa=sl.pos===pos, travada=(pos==='ZC'&&!ativa&&zcsNaDefesa(sl)>=3)||((pos==='MLE'||pos==='MLD')&&!ativa&&lateraisNoMeio(pos,sl)>=1)||(pos==='CA'&&!ativa&&casNoAtaque(sl)>=2)||((pos==='PE'||pos==='PD')&&!ativa&&pontasNoAtaque(pos,sl)>=1);
    return '<button type=button class="elpos elposbt'+(ativa?' ativa':'')+(travada?' travada':'')+'"'
      +(travada?' disabled':'')+' onclick="event.stopPropagation();elMudaPosicao('+indice+',\''+pos+'\')">'
      +esc(siglaVisivel(pos))+'</button>';
   }).join('')+'</div>';
  }
  var seletorBuild='';
   try{ if(typeof window.elBotoesExtra==='function') seletorBuild=window.elBotoesExtra(k,de,sl,entrada)||''; }catch(e){}
  /* No campo, a escolha de build sempre é um seletor. Nunca cai no botão
     alternativo: mesmo se a rotina principal ainda não estiver disponível,
     mantém Básica, as salvas e Criar nova build no mesmo controle. */
  if(de==='campo'&&!seletorBuild){
    var mb=bd(), ab=(sl&&sl.buildId)?sl.buildId:'base', lb=buildsDe(idb), sb='';
    var islot=(MT.slots||[]).indexOf(sl);
    sb='<select class=elbsel onclick="event.stopPropagation()" onchange="event.stopPropagation();elSelecionaBuild('+islot+',\''+k+'\',this.value)" title="qual build está valendo">';
    sb+='<option value="base"'+(ab==='base'?' selected':'')+'>BÁSICA</option>';
    for(var ib=0;ib<lb.length;ib++) sb+='<option value="'+esc(lb[ib].buildId||'')+'"'+(lb[ib].buildId===ab?' selected':'')+'>'+esc(String(lb[ib].nome||('build '+(ib+1))))+'</option>';
   seletorBuild=sb+'<option value="nova">CRIAR NOVA BUILD</option></select>';
  }
  var funcEtiqueta=p.func||'—';
  try{
    var ativaEtiqueta=(de==='campo'&&sl)
     ?(window.elBuildDaVaga&&window.elBuildDaVaga(sl,idb))
     :(entrada&&window.elBuildDaEntrada?window.elBuildDaEntrada(entrada,idb)
       :(window.elBuildAtiva&&window.elBuildAtiva(idb)));
   /* A Ficha é a autoridade do nome visível da função da build. */
   if(ativaEtiqueta&&ativaEtiqueta.func) funcEtiqueta=funcaoVisivelVigente(ativaEtiqueta.func);
   else funcEtiqueta=funcaoVisivelVigente(funcEtiqueta);
  }catch(e){}
  var avisoAlternativa=estadoBuild?avisoDoEstadoDaBuild(estadoBuild):'';
  var painelDetalhe='';
  if(de==='campo'){
   painelDetalhe='<div class=elbuildinfo>INFORMAÇÕES DA BUILD</div>'
    +'<div class=elbuilddivider></div>'
    +'<div class="elfn elbuildfunc" title="'+esc(funcEtiqueta||"\u2014")+'">'+funcaoBuildEmDuasLinhas(funcEtiqueta||"\u2014")+'</div>'
    +'<div class=elbuildrecados>'+avisoAlternativa+'</div>'
    +'<div class="elbuildselecionada elbuildrodape">'+seletorBuild+'</div>';
  } else {
   painelDetalhe='<div class=elfn title="'+esc(p.func||"\u2014")+'">'+esc(p.func||"\u2014")+'</div>'
    +(seletorBuild?'<div class=elbuildtroca>'+seletorBuild+'</div>':'')
    +avisoAlternativa;
  }
  var bts="";
  if(de==="fora")       bts = botao("elParaBanco",k,"subir para Reservas","\u2191","elico");
  else if(de==="banco") bts = botao("elParaCampo",k,"subir para Titular","\u2191","elico")
                            + botao("elParaFora",k,"tirar do banco","\u21e9","elico");
  else                  bts = botao("elParaBanco",k,"descer para Reservas","\u2193","elico");
  var identidadeFicha=de==='campo'?String((MT.slots||[]).indexOf(sl))
   :String(entrada&&entrada.entryId||'');
  var abre='onclick="event.stopPropagation();'
   +'(window.elAbreOcorrencia?window.elAbreOcorrencia(\''+escJs(k)+'\',\''+escJs(de)
   +'\',\''+escJs(identidadeFicha)+'\'):(window.elAbreCard||abrir)(\''+escJs(k)+'\'))"';
  var classeEstado=estadoBuild?(' elestado-'+estadoBuild.id):'';
  var atributosEstado=estadoBuild
   ?(' data-el-estado="'+estadoBuild.id+'" style="border-color:'+estadoBuild.cor
     +'!important;box-shadow:0 0 0 1px '+estadoBuild.moldura
     +',0 10px 26px -14px rgba(0,0,0,.95)!important"'):'';
  return '<div class="elcard elquadrado'+classeEstado+'" data-k="'+esc(k)+'"'
   +atributosEstado
   +(entrada&&entrada.entryId?' data-entry-id="'+esc(entrada.entryId)+'"':'')+' '+abre+'>'
   +'<div class=eltop>'+tag+pt+'</div>'
   +'<div class=elcorpo>'
     +'<div class=elident>'
       +'<div class=elfoto><img'+cargaFoto+' src="'+esc(window.ClubeNovoReadModel?window.ClubeNovoReadModel.foto(c):'')+'" '
      +'onerror="elFalhaFotoCard(this)"></div>'
     +'<div class=elnm title="'+esc(c.nome)+'">'+esc(c.nome)+'</div>'
     +'<div class=eles title="'+esc(est)+'">'+esc(est)+'</div>'
    +'</div>'
    +'<div class=eldet>'+painelDetalhe+'</div>'
    +'<div class="elacts'+(de==='campo'?'':' elactslista')+'" '+abre+'>'+bts
     +(de==="fora"?botao("elExclui",k,"tirar do elenco","\u00d7","elx"):"")+'</div>'
   +'</div>'
   +'</div>';
 }
 window.elMontaCard=montaCard;

 var MALHA={
  colE:18, colD:82,
  centro:[ {ate:17,pos:"CA"}, {ate:29,pos:"SA"}, {ate:41,pos:"MO"},
           {ate:55,pos:"MC"}, {ate:68,pos:"VOL"}, {ate:88,pos:"ZC"},
           {ate:101,pos:"GK"} ],
  lados:[ {ate:29,e:"PE",d:"PD"}, {ate:60,e:"MLE",d:"MLD"},
          {ate:101,e:"LE",d:"LD"} ]
 };
 function posDaRegiao(x,y){
  var i;
  if(x<MALHA.colE || x>MALHA.colD){
   for(i=0;i<MALHA.lados.length;i++) if(y<=MALHA.lados[i].ate)
    return (x<MALHA.colE)?MALHA.lados[i].e:MALHA.lados[i].d;
   return (x<MALHA.colE)?"LE":"LD";
  }
  for(i=0;i<MALHA.centro.length;i++) if(y<=MALHA.centro[i].ate)
   return MALHA.centro[i].pos;
  return "GK";
 }
 window.elPosDaRegiao=posDaRegiao;

 function formacaoLida(){
  var s=MT.slots||[], f={def:0,mei:0,ata:0}, i, y, p;
  for(i=0;i<s.length;i++){
   if(!s[i]) continue;
   p=s[i].pos; if(p==="GK") continue;
   y=+s[i].y||0;
   if(y>=62) f.def++; else if(y>=30) f.mei++; else f.ata++;
  }
  if(!f.def && !f.mei && !f.ata) return MT.form||"";
  return f.def+"-"+f.mei+"-"+f.ata;
 }
 window.elFormacaoLida=formacaoLida;

 function funcaoDaVaga(sl, k){
  var fs=[]; try{ fs=MT_FUNCS[sl.pos]||[]; }catch(e){}
  if(!fs.length) return sl.func||null;
   if(k && typeof window.elBuildDaVaga==="function"){
   var b=window.elBuildDaVaga(sl,String(k).split("|")[0].split("@")[0]);
   if(b && b.func){for(var ib=0;ib<fs.length;ib++)if(mesmaFuncaoTecnica(fs[ib],b.func))return b.func;}
  }
  if(k){
   var base=String(k).split("|")[0].split("@")[0], melhor=null;
   try{
    D.forEach(function(x){
     if(!x || x.id==="MOLDE") return;
     if(String(x.id).split("@")[0]!==base) return;
     if(fs.indexOf(x.tipo)<0) return;
     var n=nota(x); if(!melhor||n>melhor.n) melhor={n:n,tipo:x.tipo};
    });
   }catch(e){}
   if(melhor) return melhor.tipo;
  }
  if(fs.indexOf(sl.func)>=0) return sl.func;
   return fs[0];
  }
  window.elFuncaoDaVaga=funcaoDaVaga;

 function religaVaga(ix){
  var sl=(MT.slots||[])[ix]; if(!sl) return;
  if(sl.pos==="GK") return;  /* o goleiro nao sai do gol — ordem do Luis */
  var p=posDaRegiao(+sl.x||50, +sl.y||50);
  if(sl.posFixa && faixaDe(p)===faixaDe(sl.pos)){
   sl.func=funcaoDaVaga(sl, sl.key);
   var nv=formacaoLida(); if(nv) MT.form_lida=nv;
   return;
  }
  sl.posFixa=0;
  if(p==="GK") p="ZC";       /* nenhuma outra vaga vira goleiro */
  sl.pos=p;
  sl.func=funcaoDaVaga(sl, sl.key);
  var nova=formacaoLida();
  if(nova) MT.form_lida=nova;
 }
 window.elReligaVaga=religaVaga;

 function arrumaCampo(){
  var campo=document.querySelector("#mtwrap .mtcampo"); if(!campo) return;
  /* No zoom, o campo precisa encolher como uma única peça. Antes o gramado
     ficava responsivo, mas cards, fotos e controles mantinham pixels fixos.
     A escala abaixo preserva a proporção de todos eles e não muda nada em
     tela larga (escala 1). */
  var caixa=campo.parentElement, disponivel=0;
  try{ disponivel=caixa?caixa.clientWidth:0; }catch(e){}
  if(!disponivel) disponivel=campo.clientWidth||0;
  /* Ao voltar da ficha a casca do Elenco existe antes de receber a largura
     final. Não aplica a escala mínima nesse instante: ela deixava o campo
     gravado em miniatura até um zoom manual disparar novo resize. */
  if(disponivel<160){
   campo.style.removeProperty("zoom");
   campo.style.removeProperty("width");
   return;
  }
  var campoEstreito=disponivel<820;
  var baseEscala=campoEstreito?1240:1180;
  /* No celular, 236px x 68% mantém o card perto do tamanho histórico de
     leitura. O campo continua inteiro e o viewport navega lateralmente. */
  var escala=campoEstreito?Math.max(.68,Math.min(1,disponivel/baseEscala))
   :Math.min(1,Math.max(.05,disponivel/baseEscala));
  campo.style.zoom=String(escala);
  campo.style.setProperty("width",campoEstreito?(baseEscala+"px")
   :((100/escala)+"%"),"important");
  if(caixa&&campoEstreito){
   caixa.setAttribute('data-elcampo-navegavel','1');
   if(!caixa.getAttribute('data-elcampo-centralizado')){
    caixa.setAttribute('data-elcampo-centralizado','1');
    requestAnimationFrame(function(){try{caixa.scrollLeft=Math.max(0,(caixa.scrollWidth-caixa.clientWidth)/2);}catch(e){}});
   }
  }else if(caixa){
   caixa.removeAttribute('data-elcampo-navegavel');
   caixa.removeAttribute('data-elcampo-centralizado');
   try{caixa.scrollLeft=0;}catch(e){}
  }
  var W=campo.clientWidth; if(!W) return;
  /* O formato do campo é fixo; formação nenhuma pode esticá-lo. */
  campo.style.removeProperty("height");
  campo.style.removeProperty("max-height");
  var H=campo.clientHeight||W;
  var sls=[].slice.call(campo.querySelectorAll(".mtsl"));
  if(!sls.length) return;
  var slots=MT.slots||[], pts=[], i, j;
  for(i=0;i<sls.length;i++){
   var ix=+sls[i].getAttribute("data-i"); var sl=slots[ix]; if(!sl) continue;
   pts.push({el:sls[i], x:+sl.x||50, y:+sl.y||50, ix:ix});
  }
  if(!pts.length) return;
  pts.sort(function(a,b){ return a.y-b.y; });
  var linhas=[], atual=null;
  for(i=0;i<pts.length;i++){
   if(!atual || (pts[i].y-atual.y0)>10){ atual={y0:pts[i].y, itens:[]}; linhas.push(atual); }
   atual.itens.push(pts[i]);
  }
  var n=linhas.length, maior=1;
  for(i=0;i<n;i++) if(linhas[i].itens.length>maior) maior=linhas[i].itens.length;
  /* Padrão aprovado da cópia alinhada: uma única dimensão para todos os
     cards do campo, independente da formação ou da ordem de renderização. */
  var larg=236, altMax=239.4;
  campo.style.setProperty("--elcw", "236px");
  campo.style.setProperty("--elch", "239.4px");
  for(i=0;i<pts.length;i++){
   pts[i].el.style.left=pts[i].x.toFixed(2)+"%";
   pts[i].el.style.top =pts[i].y.toFixed(2)+"%";
  }
  var ph=100*altMax/H, pw=100*larg/W;
  /* Reserva uma faixa interna: card nenhum atravessa as linhas laterais do campo. */
  var mgy=ph/2+2.8;
  var ys=[];
  for(i=0;i<n;i++){
   var soma=0;
   for(j=0;j<linhas[i].itens.length;j++) soma+=linhas[i].itens[j].y;
   ys.push(soma/linhas[i].itens.length);
  }
  var serveY=(ys[0]>=mgy) && (ys[n-1]<=100-mgy);
  for(i=1;i<n && serveY;i++) if(ys[i]-ys[i-1] < ph) serveY=false;
  if(!serveY){
   var passo=(n>1)?((100-2*mgy)/(n-1)):0;
   for(i=0;i<n;i++){
    var yy=(n>1)?(mgy+i*passo):50;
    for(j=0;j<linhas[i].itens.length;j++){
     linhas[i].itens[j].y=yy;
     if(slots[linhas[i].itens[j].ix]) slots[linhas[i].itens[j].ix].y=Math.round(yy*10)/10;
    }
   }
  }
  var mgx=pw/2+(maior>=5?.8:2.8);
  for(i=0;i<n;i++){
   var L=linhas[i].itens;
   L.sort(function(a,b){ return a.x-b.x; });
   var serve=(L[0].x>=mgx) && (L[L.length-1].x<=100-mgx);
   for(j=1;j<L.length && serve;j++) if(L[j].x-L[j-1].x < pw+0.4) serve=false;
  if(!serve){
    for(j=0;j<L.length;j++){
     L[j].x=(L.length>1)?(mgx+j*((100-2*mgx)/(L.length-1))):50;
     if(slots[L[j].ix]) slots[L[j].ix].x=Math.round(L[j].x*10)/10;
    }
   }
  }
  for(i=0;i<pts.length;i++){
   pts[i].el.style.left=pts[i].x.toFixed(2)+"%";
   pts[i].el.style.top =pts[i].y.toFixed(2)+"%";
  }
  for(i=0;i<pts.length;i++){
   var e=pts[i].el;
   var mh=50*(e.offsetHeight||0)/H, mw=50*(e.offsetWidth||0)/W;
   /* Ajuste somente visual: a posição salva não é regravada aqui. */
   var margem=(maior>=5?.8:3.4);
   var y2=Math.max(mh+margem, Math.min(100-mh-margem, pts[i].y));
   var x2=Math.max(mw+margem, Math.min(100-mw-margem, pts[i].x));
   if(Math.abs(y2-pts[i].y)>0.05) e.style.top =y2.toFixed(2)+"%";
   if(Math.abs(x2-pts[i].x)>0.05) e.style.left=x2.toFixed(2)+"%";
  }
 }

 function ligaArrastoDaVaga(sl){
  var al=sl.querySelector(".elalca"); if(!al) return;
  if(al.getAttribute("data-arr")) return;
  al.setAttribute("data-arr","1");
  al.addEventListener("pointerdown", function(ev){
   if(ev.button!==0) return;
   ev.preventDefault(); ev.stopPropagation();
   var campo=document.querySelector("#mtwrap .mtcampo"); if(!campo) return;
   var ix=+sl.getAttribute("data-i");
   var st=(MT.slots||[])[ix]; if(!st) return;
   var r=campo.getBoundingClientRect(), moveu=0;
   sl.classList.add("arr");
   function mv(e){
    moveu=1; e.preventDefault();
    var x=(e.clientX-r.left)/r.width*100, y=(e.clientY-r.top)/r.height*100;
    x=Math.max(5,Math.min(95,x)); y=Math.max(4,Math.min(96,y));
    sl.style.left=x.toFixed(2)+"%"; sl.style.top=y.toFixed(2)+"%";
    st.x=Math.round(x*10)/10; st.y=Math.round(y*10)/10; st.mv=1;
   }
   function up(){
    document.removeEventListener("pointermove",mv);
    document.removeEventListener("pointerup",up);
    sl.classList.remove("arr");
    if(moveu){
     religaVaga(ix);
     try{ userStateSave(); }catch(e){}
     window.EL_SELO=(window.EL_SELO||0)+1;
     try{ mtRender(); }catch(e){}
    }
   }
   document.addEventListener("pointermove",mv);
   document.addEventListener("pointerup",up);
  });
 }

 window.elAbreBuildMelhor=function(k, func){
  var alvo=String(k).split('|')[0]+'|'+func;
  try{ if(typeof window.t6AbreMaximo==='function') return window.t6AbreMaximo(alvo); }catch(e){}
  try{ if(typeof window.elAbreCard==='function') return window.elAbreCard(alvo); }catch(e){}
 };
/* Um único estado alimenta a mensagem e a moldura. A função continua sendo
   comparada internamente, mas a interface explica o resultado pela posição. */
 function classificaEstadoDaBuild(fatos){
  var vermelhoDaBuild=!!(fatos&&fatos.cardServePosicao!==false&&fatos.temBuildAplicada
   &&fatos.buildAdequada!==false&&fatos.temNota===false);
  var id=!fatos||fatos.cardServePosicao===false?'vermelho'
   :(fatos.temBuildAplicada&&fatos.buildAdequada===false?'laranja'
    :(fatos.temNota===false?'vermelho':(fatos.haBuildMelhor?'amarelo':'verde')));
 var estados={
  vermelho:{id:'vermelho',cor:'#f85149',moldura:'rgba(248,81,73,.72)',
   fundo:'rgba(248,81,73,.12)',borda:'rgba(248,81,73,.45)',texto:'#ff8b86',
   mensagem:'Este card n\u00e3o serve para esta posi\u00e7\u00e3o.'},
  laranja:{id:'laranja',cor:'#f97316',moldura:'rgba(249,115,22,.76)',
   fundo:'rgba(249,115,22,.13)',borda:'rgba(249,115,22,.50)',texto:'#ffad73',
   mensagem:'O card serve para esta posi\u00e7\u00e3o, mas a build est\u00e1 adaptada.'},
  amarelo:{id:'amarelo',cor:'#f5c74d',moldura:'rgba(245,199,77,.76)',
   fundo:'rgba(245,199,77,.12)',borda:'rgba(245,199,77,.46)',texto:'#f7d979',
   mensagem:'H\u00e1 uma build melhor para esta posi\u00e7\u00e3o.'},
  verde:{id:'verde',cor:'#2eff97',moldura:'rgba(46,255,151,.68)',
   fundo:'rgba(46,255,151,.10)',borda:'rgba(46,255,151,.34)',texto:'#8df3ae',
   mensagem:'Esta \u00e9 sua melhor op\u00e7\u00e3o para esta posi\u00e7\u00e3o.'}
  };
  if(id==='vermelho'&&vermelhoDaBuild)
   estados.vermelho.mensagem='Esta build n\u00e3o serve para esta posi\u00e7\u00e3o.';
  return estados[id];
 }
window.elClassificaEstadoDaBuild=classificaEstadoDaBuild;
function avisoDoEstadoDaBuild(estado){
 if(!estado) return '';
 return '<div class="elaviso elaviso-'+estado.id+'" data-el-estado="'+estado.id
  +'" style="background:'+estado.fundo+';border-color:'+estado.borda+';color:'
  +estado.texto+'">'+estado.mensagem+'</div>';
}
function estadoDaBuildNaPosicao(k, sl, atual, foraDePosicao){
 if(!k || !sl) return null;
 var idb=String(k).split('|')[0].split('@')[0], L=[], ativa=null;
 try{ L=(window.elBuildsDe&&window.elBuildsDe(idb))||[]; }catch(e){ L=[]; }
 try{ ativa=window.elBuildDaVaga&&window.elBuildDaVaga(sl,idb); }catch(e){ ativa=null; }
 /* A origem persistida da build e a FUNCAO. A vaga pode mudar de posicao,
    mas o aviso so chama uma build de especifica quando ela foi salva para
    a mesma funcao que esta sendo avaliada agora. A Basica nunca entra em L. */
 var funcAtualBruta=String((sl&&sl.func)||atual.func||'').trim(),
     funcAtual=funcaoVisivelVigente(funcAtualBruta),
     chaveAtual=chaveFuncaoCanonica(funcAtual),
     funcAtiva=ativa&&ativa.func?funcaoVisivelVigente(ativa.func):'',
     ativaDaFuncao=!!(ativa&&chaveFuncaoCanonica(funcAtiva)===chaveAtual);
 var notaAtual=Number(atual&&atual.n), tecnico=null, melhorEspecifica=null;
 var fatos={cardServePosicao:!foraDePosicao,temNota:!!(atual&&notaAtual>0),
  temBuildAplicada:!!ativa,buildAdequada:ativaDaFuncao,haBuildMelhor:false};
 /* Adaptação vem antes da comparação de qualidade: não é erro e também não
    pode aparecer como amarela só porque existe outra build mais forte. */
 if(fatos.cardServePosicao===false || (fatos.temBuildAplicada&&!fatos.buildAdequada)
    || fatos.temNota===false) return classificaEstadoDaBuild(fatos);
 /* No Elenco, aplicada e candidatas são comparadas no MESMO contexto: a
    fotografia salva de cada build permanece intacta e somente o técnico do
    time é substituído durante a avaliação isolada. O resultado é derivado e
    memoizado; nunca volta para MT nem para a build persistida. */
 if(typeof window.elTecnicoDoTime!=='function'
    || typeof window.elMelhorBuildContextual!=='function') return "";
 try{
  tecnico=window.elTecnicoDoTime();
  melhorEspecifica=window.elMelhorBuildContextual(
   k,idb,L,funcAtualBruta,chaveAtual,tecnico);
 }catch(e){ return ""; }
 fatos.haBuildMelhor=!!(melhorEspecifica&&melhorEspecifica.n>notaAtual);
 return classificaEstadoDaBuild(fatos);
}

function refazVaga(sl, semSalvar){
  var ix=+sl.getAttribute("data-i");
  var s=(MT.slots||[])[ix];
  /* A fonte da vaga é o elenco salvo; o atributo visual pode ficar antigo após redesenhar. */
  var k=(s&&s.key)||sl.getAttribute("data-key")||"";
  if(k) sl.setAttribute("data-key",k);
  /* O desenho consome a funcao persistida; nao escolhe outra funcao durante
     render. Apenas estados legados sem funcao recebem uma inicializacao. */
  if(s && k && !s.func){
   var fnova=funcaoDaVaga(s, k);
   if(fnova && fnova!==s.func){
    s.func=fnova;
    if(!semSalvar) try{ userStateSave(); }catch(e){}
   }
  }
  /* A disponibilidade da linha faz parte da assinatura visual. Assim uma
     vaga que nasceu como placeholder durante a carga é refeita quando a
     mesma chave passa a resolver no catálogo, sem exceção por card/índice. */
  var cardVivo=null; try{ cardVivo=k?mtCard(k):null; }catch(e){}
  var assin=k+"|"+(s?s.func:"")+"|"+(s?s.pos:"")+"|"+(s?s.buildId||'base':"base")
   +"|"+(k?(cardVivo?"card":"pendente"):"vazia")+"|"+(window.EL_SELO||0);
  if(sl.getAttribute("data-el")!==assin){
   /* A posição já é escolhida pelos botões do cabeçalho do card. */
   var rot="";
   var alca=(s && s.pos!=="GK")
    ?'<button type=button class=elalca title="arraste para mover esta vaga">'
      +'\u2725</button>':"";
   if(k && cardVivo){ sl.innerHTML=montaCard(k,"campo",s)+rot+alca; }
   else if(k){
    sl.innerHTML='<div class="elvazio elvazio-indisponivel" title="Esta vaga continua ocupada no time salvo">'
     +'<div class=elvpos>'+esc(siglaVisivel(s?s.pos:""))+'</div>'
     +'<div class=elvmais>!</div><div class=elvfn>card indispon\u00edvel</div></div>'+rot+alca;
   } else {
    var posicoes=s?opcoesDaVaga(s).map(siglaVisivel):[];
    sl.innerHTML='<div class=elvazio onclick="event.stopPropagation();mtAbreSel('+ix+')">'
     +'<div class=elvpos>'+esc(posicoes.join(', ')||siglaVisivel(s?s.pos:""))+'</div>'
     +'<div class=elvmais>+</div>'
     +'<div class=elvfn>vaga livre</div></div>'+rot+alca;
   }
   sl.setAttribute("data-el",assin);
   sl.removeAttribute("data-arr");
  }
  ligaArrastoDaVaga(sl);
 }
 window.elRefazVaga=refazVaga;

 /* ---------- 7 · O ESQUELETO DA PAGINA ---------- */
 function nomeDoUsuario(){
  try{ if(window.EF_USUARIO) return window.EF_USUARIO; }catch(e){}
  return null;
 }
 function cabecalho(){
  var tit=(MT.slots||[]).filter(function(x){return x&&x.key;});
  var soma=0;
  tit.forEach(function(x){ var p=window.elPontuacao(x.key,x.func,true,x); if(p) soma+=p.n; });
  var med=tit.length?(soma/tit.length):0;
  var dono=nomeDoUsuario();
  var cr="inherit"; try{ cr=cor(med,0); }catch(e){}
  var lida=""; try{ lida=formacaoLida()||""; }catch(e){}
  var tec=null; try{ tec=mtTecNome(); }catch(e){}
  function st(r,v,est){ return '<div class=elstat><p>'+esc(r)+'</p>'
   +'<p'+(est?(' style="'+est+'"'):"")+'>'+v+'</p></div>'; }
  return '<div><p class=eleyebrow>Elenco</p>'
   +'<div class=eltime contenteditable=true spellcheck=false '
    +'onblur="elGravaNome(this)" onkeydown="if(event.key===\'Enter\'){event.preventDefault();this.blur();}" '
    +'title="clique para trocar o nome do seu time">'+esc(MT.nome||"Meu time")+'</div>'
   +'<div class=eldono>'+(dono?('time de <b>'+esc(dono)+'</b>')
     :'<span title="entre na sua conta para o time ficar salvo">time salvo neste navegador</span>')
   +'</div></div>'
   +'<div class=elstats>'
    +st("Forma\u00e7\u00e3o", esc(lida||MT.form||"\u2014"))
    +st("Em campo", tit.length+"/"+TETO_TIT)
    +st("Pontua\u00e7\u00e3o m\u00e9dia",
        tit.length?med.toFixed(2):"\u2014", "color:"+cr)
    +st("T\u00e9cnico", esc(tec||"\u2014"))
   +'</div>';
 }
 window.elGravaNome=function(el){
  var v=String(el.textContent||"").replace(/\s+/g," ").trim();
  MT.nome = v || "Meu time";
  el.textContent=MT.nome;
  try{ userStateSave(); }catch(e){}
 };

 function selFormacao(){
  var h='<select onchange="elTrocaFormacao(this.value)" '
   +'onclick="event.stopPropagation()" title="trocar a forma\u00e7\u00e3o">';
  var ks=[]; try{ ks=Object.keys(MT_FORM); }catch(e){}
  for(var i=0;i<ks.length;i++)
   h+='<option'+(ks[i]===MT.form?" selected":"")+'>'+esc(ks[i])+'</option>';
  return h+"</select>";
 }
window.elTrocaFormacao=function(v){
  var f=null; try{ f=MT_FORM[v]; }catch(e){}
  if(!f) return;
  /* A escalação é do usuário. Trocar o desenho tático nunca pode apagá-la. */
  var velhos=(MT.slots||[]).map(function(x){
   return x&&x.key?{key:x.key,func:x.func,buildId:x.buildId||'base'}:null;
  });
  MT.form=v;
  MT.slots=[];
  try{ mtSlots(); }catch(e){}
  var s2=MT.slots||[], i;
  for(i=0;i<s2.length;i++){
   if(!s2[i]) continue;
   s2[i].mv=0;
   var anterior=velhos[i];
   s2[i].key=anterior?anterior.key:null;
   s2[i].buildId=anterior?(anterior.buildId||'base'):'base';
   if(anterior&&anterior.key){
    try{ s2[i].func=funcaoDaVaga(s2[i],anterior.key)||s2[i].func; }catch(e){}
   }
  }
  MT.form_lida=null;
  window.EL_SELO=(window.EL_SELO||0)+1;
  try{ userStateSave(); }catch(e){}
  try{ mtRender(); }catch(e){}
 };
 function blocoFormacao(){
  var lida="";
  try{ lida=formacaoLida(); }catch(e){}
  var dif=(lida && lida!==MT.form);
  var mostra=String(lida||MT.form||"");
  var ns=mostra.split("-").map(function(x){ return parseInt(x,10)||0; });
  var dots="";
  for(var i=ns.length-1;i>=0;i--)
   dots+='<i style="height:'+Math.min(28,6+ns[i]*5)+'px"></i>';
  return '<div class=elbadge><div><p class=ellbl>Forma\u00e7\u00e3o</p>'
   +'<p class=elnum>'+esc(mostra||"\u2014")+'</p></div>'
   +'<div class=eldots>'+dots+'</div>'
   +'<span class=elseta>trocar \u25be</span>'
   +selFormacao()+'</div>'
   +(dif?('<div class=elnota2>voc\u00ea moveu as vagas \u2014 partiu de '
     +esc(MT.form)+'</div>'):"");
 }
 function blocoTecnico(){
  var nome=null, bs=[];
  try{ nome=mtTecNome(); }catch(e){}
  try{ bs=mtTecBs()||[]; }catch(e){}
  var ini=String(nome||"?").trim().charAt(0).toUpperCase();
  var sel='<select class=elsel onchange="elPoeTecnico(this.value)">'
   +'<option value=""'+((MT.tec===null||MT.tec===undefined)?" selected":"")
   +'>\u2014 sem t\u00e9cnico \u2014</option>';
  try{
   for(var i=0;i<_TECOP.length;i++)
    sel+='<option value="'+_TECOP[i][0]+'"'+((MT.tec===_TECOP[i][0])?" selected":"")
     +'>'+esc(_TECOP[i][1])+'</option>';
  }catch(e){}
  sel+="</select>";
  var efeito="";
  if(bs&&bs.length){
   var t=[], j;
   for(j=0;j<bs.length;j++){
    try{ t.push("+1 em "+((typeof tecPT==="function")?tecPT(bs[j]):bs[j])); }catch(e){}
   }
   if(t.length) efeito='<div class=elnota2>'+esc(t.join(" \u00b7 "))
    +'<br>vale para o time inteiro</div>';
  } else {
   efeito='<div class=elnota2>sem t\u00e9cnico \u2014 as pontua\u00e7\u00f5es '
    +'do campo est\u00e3o sem o b\u00f4nus dele</div>';
  }
 return '<div class=elcoach><div class=elavatar>'+esc(nome?ini:"\u2014")+'</div>'
   +'<div class=elcinfo><p class=elrole>T\u00e9cnico</p>'
   +'<p class=elcname title="'+esc(nome||"")+'">'
   +esc(nome||"\u2014 sem t\u00e9cnico \u2014")+'</p></div></div>'
   +sel+efeito;
 }

 function faixaDoElenco(){
  function forca(lista){
   var soma=0,qtd=0,vistos={};
   lista.forEach(function(item){
    var k=typeof item==="string"?item:(item&&item.key);
    if(!k||vistos[k]) return; vistos[k]=1;
     var p=null; try{p=window.elPontuacao(k,(item&&item.func)||null,!!(item&&item.key),item&&item.key?item:null);}catch(e){}
    if(p&&isFinite(+p.n)){soma+=+p.n;qtd++;}
   });
   return qtd?(soma/qtd).toFixed(2):"\u2014";
  }
  var tit=(MT.slots||[]).filter(function(s){return s&&s.key;});
  var elenco=tit.concat(MT.banco||[]);
  var selTec='<select class="eltopo-select" onchange="elPoeTecnico(this.value)">'
   +'<option value=""'+((MT.tec===null||MT.tec===undefined)?" selected":"")+'>T\u00e9cnico</option>';
  try{for(var i=0;i<_TECOP.length;i++) selTec+='<option value="'+_TECOP[i][0]+'"'+(MT.tec===_TECOP[i][0]?" selected":"")+'>'+esc(_TECOP[i][1])+'</option>';}catch(e){}
  selTec+='</select>';
  return '<div class="eltopo">'
   +'<label class="eltopo-ctrl"><small>Forma\u00e7\u00e3o</small>'+selFormacao()+'</label>'
   +'<label class="eltopo-ctrl"><small>T\u00e9cnico</small>'+selTec+'</label>'
   +'<div class="eltopo-forcas">'
    +'<span><small>For\u00e7a do time titular</small><b>'+forca(tit)+'</b></span>'
    +'<span><small>For\u00e7a do elenco</small><b>'+forca(elenco)+'</b></span>'
   +'</div></div>';
 }
 window.elPoeTecnico=function(v){
  var antes=(MT.tec===null||MT.tec===undefined)?'':String(MT.tec);
  var depois=(v===null||v===undefined||v==='')?'':String(+v);
  if(typeof mtPoeTec!=='function') return false;
  if(antes===depois) return true;
  /* A troca é o único evento que invalida simultaneamente campo, banco e
     fora do banco. O mtRender original desenha uma vez os cards visíveis;
     os demais continuam preguiçosos e serão calculados quando aparecerem. */
  if(typeof window.elLimpaCachePontuacao==='function')
   window.elLimpaCachePontuacao();
  mtPoeTec(v);
  if(typeof window.t6Notifica==='function')
   window.t6Notifica('T\u00e9cnico alterado. As builds de todos os cards foram recalculadas, mas n\u00e3o reotimizadas.');
  return true;
 };

 window.EL_RISCOS='<div class="risco r-borda"></div>'
  +'<div class="risco r-meio"></div><div class="risco r-circulo"></div>'
  +'<div class="risco r-areaG r-cima"></div><div class="risco r-areaP r-cima"></div>'
  +'<div class="risco r-meialua r-cima"></div>'
  +'<div class="risco r-areaG r-baixo"></div><div class="risco r-areaP r-baixo"></div>'
  +'<div class="risco r-meialua r-baixo"></div>'
  +'<div class="risco r-pena" style="top:11%"></div>'
  +'<div class="risco r-pena" style="bottom:11%"></div>';
 function esqueleto(){
  var w=document.getElementById("mtwrap"); if(!w) return null;
  var campo=w.querySelector(".mtcampo"); if(!campo) return null;
  var grid=w.querySelector(".mtgrid"); if(!grid) return null;
  var caixas=[].slice.call(w.querySelectorAll(".mtbanco"));
  var cxBanco=null, cxFora=null;
  caixas.forEach(function(x){
   if(x.className.indexOf("alvobanco")>=0) cxBanco=x;
   if(x.className.indexOf("alvoelenco")>=0) cxFora=x;
  });
  var wrap=document.createElement("div"); wrap.id="elwrap";
  try{
   if(!campo.querySelector(".risco")){
    campo.insertAdjacentHTML("afterbegin", window.EL_RISCOS);
   }
  }catch(e){}
  wrap.innerHTML='<div id=elfaixa></div>'
   +'<div id=elgrid>'
   +'<div id=elfmt class=elpane></div>'
   +'<div id=elesq class=elpane>'
    +'<div class=elhd>Campo <em>arraste o card para trocar \u00b7 '
    +'arraste a al\u00e7a para mover a vaga</em></div>'
    +'<div class=elcampodica>Deslize o campo para os lados</div>'
    +'<div id=elcampo-viewport tabindex=0 aria-label="Campo navegável horizontalmente"></div>'
   +'</div>'
   +'<div id=elreservas class=elpane><div id=elban></div></div>'
   +'</div>'
   +'<div id=elfora class=elpane style="margin-top:20px"></div>';
  grid.parentNode.insertBefore(wrap, grid);
  grid.style.display="none";
  wrap.querySelector("#elcampo-viewport").appendChild(campo);
  wrap._cxBanco=cxBanco; wrap._cxFora=cxFora;
  return wrap;
 }

 var VER={ord:"recente", setor:"", pos:"", func:"", est:"", q:""};
 window.EL_VER=VER;
 var SETOR={GK:"goleiro", ZC:"defesa", LE:"defesa", LD:"defesa",
            VOL:"meio", MC:"meio", MLE:"meio", MLD:"meio", MO:"meio",
            PE:"ataque", PD:"ataque", SA:"ataque", CA:"ataque"};
 function entradasDaColecaoVisual(c){
  /* O dono das builds vive no IIFE posterior. Identificadores lexicais não
     atravessam IIFEs: o desenho fala apenas pela porta pública e, durante o
     boot anterior a ela, lê a ponte já migrada sem criar nem salvar estado. */
  try{
   if(typeof window.elEntradasDaColecao==='function')
    return window.elEntradasDaColecao(c)||[];
   var m=(typeof MT!=='undefined')?MT:null;
   return m&&m.listEntries&&Array.isArray(m.listEntries[c])?m.listEntries[c]:[];
  }catch(e){ return []; }
 }
 function listaFora(){
  var L=(MT.elenco||[]).slice(), i;
  var entradas=entradasDaColecaoVisual('fora');
  var info=L.map(function(k,ix){
   var c=null; try{ c=mtCard(k); }catch(e){}
   var entrada=entradas[ix]||null;
   var p=null; try{ p=window.elPontuacao(k,null,false,null,entrada); }catch(e){}
   return {k:k, c:c, ix:ix, n:(p?p.n:0), func:(p&&p.func)||(c?c.tipo:""),
           pos:c?(c.np||c.pos||""):"", nome:c?String(c.nome||""):"",
           est:c?String(c.modelo||""):"",entry:entrada};
  }).filter(function(x){ return !!x.c; });
  var q=VER.q.toLowerCase().trim();
  info=info.filter(function(x){
   if(q && x.nome.toLowerCase().indexOf(q)<0) return false;
   if(VER.setor && SETOR[x.pos]!==VER.setor) return false;
   if(VER.pos && x.pos!==VER.pos) return false;
   if(VER.func && x.func!==VER.func) return false;
   if(VER.est && x.est!==VER.est) return false;
   return true;
  });
  if(VER.ord==="maior") info.sort(function(a,b){ return b.n-a.n; });
  else if(VER.ord==="menor") info.sort(function(a,b){ return a.n-b.n; });
  else if(VER.ord==="nome") info.sort(function(a,b){
   return a.nome.localeCompare(b.nome,"pt"); });
  else if(VER.ord==="pos") info.sort(function(a,b){
   return String(a.pos).localeCompare(String(b.pos))||(b.n-a.n); });
  return info;
 }
 window.elVer=function(campo, valor){
  VER[campo]=valor; desenhaFora();
 };
 window.elLimpaVer=function(){
  VER.setor=""; VER.pos=""; VER.func=""; VER.est=""; VER.q=""; VER.ord="recente";
  desenhaFora();
 };
 function opcoes(lista, sel, vazio){
  var h='<option value="">'+esc(vazio)+'</option>', i;
  for(i=0;i<lista.length;i++)
   h+='<option value="'+esc(lista[i])+'"'+(lista[i]===sel?" selected":"")
    +'>'+esc(lista[i])+'</option>';
  return h;
 }
 function barraDeVer(mostrando, total){
  var poss={}, funs={}, ests={};
  var entradas=entradasDaColecaoVisual('fora');
  (MT.elenco||[]).forEach(function(k,ix){
   var c=null; try{ c=mtCard(k); }catch(e){}  if(!c) return;
   if(c.np||c.pos) poss[c.np||c.pos]=1;
   var p=null; try{ p=window.elPontuacao(k,null,false,null,entradas[ix]||null); }catch(e){}
   if(p&&p.func) funs[p.func]=1;
   if(c.modelo) ests[c.modelo]=1;
  });
  function ord(o){ return Object.keys(o).sort(function(a,b){
   return a.localeCompare(b,"pt"); }); }
  var limpou=(VER.setor||VER.pos||VER.func||VER.est||VER.q||VER.ord!=="recente");
  return '<div id=elbarra>'
   +'<input id=elbusca placeholder="buscar pelo nome\u2026" value="'+esc(VER.q)+'" '
    +'oninput="elVer(\'q\',this.value)">'
   +'<select class=elsel2 onchange="elVer(\'ord\',this.value)">'
    +'<option value="recente"'+(VER.ord==="recente"?" selected":"")+'>adicionado por \u00faltimo</option>'
    +'<option value="maior"'+(VER.ord==="maior"?" selected":"")+'>maior pontua\u00e7\u00e3o</option>'
    +'<option value="menor"'+(VER.ord==="menor"?" selected":"")+'>menor pontua\u00e7\u00e3o</option>'
    +'<option value="nome"'+(VER.ord==="nome"?" selected":"")+'>nome A-Z</option>'
    +'<option value="pos"'+(VER.ord==="pos"?" selected":"")+'>posi\u00e7\u00e3o</option>'
   +'</select>'
   +'<select class=elsel2 onchange="elVer(\'setor\',this.value)">'
    +opcoes(["goleiro","defesa","meio","ataque"], VER.setor, "todos os setores")+'</select>'
   +'<select class=elsel2 onchange="elVer(\'pos\',this.value)">'
    +opcoes(ord(poss), VER.pos, "todas as posi\u00e7\u00f5es")+'</select>'
   +'<select class=elsel2 onchange="elVer(\'func\',this.value)">'
    +opcoes(ord(funs), VER.func, "todas as fun\u00e7\u00f5es")+'</select>'
   +'<select class=elsel2 onchange="elVer(\'est\',this.value)">'
    +opcoes(ord(ests), VER.est, "todos os estilos")+'</select>'
   +(limpou?'<button class="elbt ellimpa" onclick="elLimpaVer()">limpar</button>':"")
   +'<span class=elcont>'+(mostrando===total?(total+" cards")
     :(mostrando+" de "+total))+'</span>'
   +'</div>';
 }
 function desenhaFora(){
  var alvo=document.getElementById("elfora"); if(!alvo) return;
  var foco=(document.activeElement && document.activeElement.id==="elbusca");
  var pos=foco?document.activeElement.selectionStart:0;
  var L=listaFora(), total=(MT.elenco||[]).length;
  alvo.innerHTML=
   '<div class=elhd>Fora do banco '
   +'<em>'+total+' cards'
   +'<button class=elbt style="margin-left:6px" onclick="mtAddElenco()">'
   +'+ adicionar card</button></em></div>'
   +barraDeVer(L.length, total)
   +(L.length?('<div class=elgrid>'
     +L.map(function(x){ return montaCard(x.k,"fora",null,x.entry); }).join("")+'</div>')
    :('<div class=elvazia>'
     +(total?"Nenhum card com esse filtro.":"Ningu\u00e9m fora do banco ainda.")
     +'</div>'));
  if(foco){ var b=document.getElementById("elbusca");
   if(b){ b.focus(); try{ b.setSelectionRange(pos,pos); }catch(e){} } }
  ligaArrasta();
 }

 (function(){
  if(typeof window.mtDndInit==="function") window.mtDndInit=function(){};
  if(typeof window.mtDragInit==="function") window.mtDragInit=function(){};
 })();

 var ARR=null;
 function ligaArrasta(){
  var w=document.getElementById("mtwrap"); if(!w) return;
  [].slice.call(w.querySelectorAll("#elreservas .elcard,#elfora .elcard"))
   .forEach(function(el){
    if(el.getAttribute("data-dnd")) return;
    el.setAttribute("data-dnd","1");
    var caixa=el.closest("#elreservas")?"banco":"fora";
    var entryId=el.getAttribute("data-entry-id")||null;
    el.setAttribute("draggable","true");
    el.addEventListener("dragstart", function(e){
     var k=el.getAttribute("data-k")||"";
     ARR={de:caixa, k:k, entryId:entryId};
     e.dataTransfer.effectAllowed="move";
     try{ e.dataTransfer.setData("text/plain",k); }catch(x){}
     el.style.opacity=".45";
    });
    el.addEventListener("dragend", function(){
     el.style.opacity="";
     [].slice.call(document.querySelectorAll(".pousa"))
       .forEach(function(x){ x.classList.remove("pousa"); });
    });
    if(caixa==='banco'&&entryId){
     el.addEventListener("dragover",function(e){
      if(!ARR||ARR.de!=='campo')return;e.preventDefault();e.stopPropagation();
      e.dataTransfer.dropEffect="move";el.classList.add("pousa");
     });
     el.addEventListener("dragleave",function(){el.classList.remove("pousa");});
     el.addEventListener("drop",function(e){
      if(!ARR||ARR.de!=='campo')return;e.preventDefault();e.stopPropagation();
      el.classList.remove("pousa");
      soltaSobreCard({group:'banco',entryId:entryId,k:el.getAttribute('data-k')||''});
     });
    }
   });
  [].slice.call(w.querySelectorAll("#mtwrap .mtsl")).forEach(function(sl){
   if(sl.getAttribute("data-dnd")) return;
   sl.setAttribute("data-dnd","1");
   sl.setAttribute("draggable","true");
   sl.addEventListener("dragstart", function(e){
    var ed=false; try{ ed=!!MT_ED; }catch(x){}
    if(ed){ e.preventDefault(); return; }
    var k=sl.getAttribute("data-key")||"";
    if(!k){ e.preventDefault(); return; }
    ARR={de:"campo", k:k, i:+sl.getAttribute("data-i")};
    e.dataTransfer.effectAllowed="move";
    try{ e.dataTransfer.setData("text/plain",k); }catch(x){}
    sl.style.opacity=".45";
   });
   sl.addEventListener("dragend", function(){ sl.style.opacity=""; });
   sl.addEventListener("dragover", function(e){
    var ocupada=!!(sl.getAttribute("data-key")||"");
    var permuta=!!(ocupada&&ARR&&(ARR.de==='campo'||ARR.de==='banco'));
    var campoVazio=!!(!ocupada&&ARR&&ARR.de==='campo');
    if(!permuta&&!campoVazio&&(!ARR || !passoPermitido(ARR.de,'campo'))) return; e.preventDefault(); e.dataTransfer.dropEffect="move";
    sl.classList.add("pousa"); });
   sl.addEventListener("dragleave", function(){ sl.classList.remove("pousa"); });
   sl.addEventListener("drop", function(e){
    e.preventDefault(); e.stopPropagation(); sl.classList.remove("pousa");
    var alvo=sl.getAttribute("data-key")||"";
    if(alvo&&ARR&&(ARR.de==='campo'||ARR.de==='banco'))
     soltaSobreCard({group:'campo',index:+sl.getAttribute("data-i"),k:alvo});
    else solta("campo", +sl.getAttribute("data-i")); });
  });
  [["#elreservas","banco"],["#elfora","fora"]].forEach(function(par){
   var cx=document.querySelector(par[0]); if(!cx) return;
   if(cx.getAttribute("data-dnd")) return;
   cx.setAttribute("data-dnd","1");
   cx.addEventListener("dragover", function(e){
    if(!ARR || !passoPermitido(ARR.de,par[1])) return; e.preventDefault(); e.dataTransfer.dropEffect="move";
    cx.classList.add("pousa"); });
   cx.addEventListener("dragleave", function(){ cx.classList.remove("pousa"); });
   cx.addEventListener("drop", function(e){
    e.preventDefault(); cx.classList.remove("pousa"); solta(par[1], -1); });
  });
 }
 function solta(destino, ix){
  var d=ARR; ARR=null; if(!d || !d.k) return;
  if(d.de==='campo'&&destino==='campo'){
   var mov=moveCampoParaVagaVaziaAtomica({group:'campo',index:d.i,k:d.k},ix);return !!mov.ok;
  }
  if(!passoPermitido(d.de,destino))return false;
  var r=transfereOcorrenciaAtomica(d.k,destino,ix);return !!r.ok;
 }
 function soltaSobreCard(alvo){
  var d=ARR;ARR=null;if(!d||!d.k||!alvo||!alvo.k)return false;
  var r=trocaOcorrenciasAtomica({group:d.de,index:d.i,entryId:d.entryId,k:d.k},alvo);
  return !!(r&&r.ok);
 }

 function saneiaSlots(){
  var f=null;
  try{ f=MT_FORM[MT.form]||MT_FORM["4-3-3"]; }catch(e){ return; }
  if(!f) return;
  var s=MT.slots||[], mexeu=false, i;
  /* A ficha pode ter mudado o nome da função desde que o time foi salvo.
     Mantém o mesmo card pelo id e recompõe uma chave atual antes de desenhar. */
  function chaveAtual(k, preferida){
   if(!k) return null;
   try{ if(mtCard(k)) return k; }catch(e){}
   var bruto=String(k).split("|")[0], base=bruto.split("@")[0], cand=[], j;
   try{
    for(j=0;j<D.length;j++){
     var c=D[j]; if(!c||c.id==="MOLDE") continue;
     if(String(c.id).split("@")[0]===base) cand.push(c);
    }
   }catch(e){}
   /* Catálogo ainda não reconhecer uma chave não é autorização para apagar
      o jogador salvo. Mantém a chave até uma ação explícita do usuário ou
      até haver uma versão atual da mesma carta para normalizar. */
   if(!cand.length) return k;
   var achou=null;
   for(j=0;j<cand.length;j++) if(cand[j].tipo===preferida){ achou=cand[j]; break; }
   achou=achou||cand[0];
   return String(achou.id)+"|"+achou.tipo;
  }
  function normalizaLista(lista){
   var out=[];
   (lista||[]).forEach(function(k){
    var nk=chaveAtual(k,null); if(nk)out.push(nk);
   });
   return out;
  }
  var bancoNovo=normalizaLista(MT.banco), foraNovo=normalizaLista(MT.elenco);
  if(String(bancoNovo)!==String(MT.banco||[])){MT.banco=bancoNovo;mexeu=true;}
  if(String(foraNovo)!==String(MT.elenco||[])){MT.elenco=foraNovo;mexeu=true;}
  if(s.length!==f.length){
    var guarda=s.map(function(x){ return x?{key:x.key,buildId:x.buildId||'base'}:null; });
   MT.slots=[]; try{ mtSlots(); }catch(e){ return; }
   s=MT.slots||[];
    for(i=0;i<s.length;i++) if(s[i]){
     s[i].key=guarda[i]?guarda[i].key:null;
     s[i].buildId=guarda[i]?(guarda[i].buildId||'base'):'base';
    }
   mexeu=true;
  }
  var vistos={};
  for(i=0;i<s.length;i++){
   if(!s[i]){ s[i]={pos:f[i][0], func:null, key:null, x:f[i][1], y:f[i][2], buildId:'base'};
              mexeu=true; }
   var sl=s[i], fs=null;
   var nk=chaveAtual(sl.key,sl.func);
   if(nk!==sl.key){ sl.key=nk; mexeu=true; }
   try{ fs=MT_FUNCS[sl.pos]; }catch(e){}
   if(!sl.pos || !fs || !fs.length){ sl.pos=f[i][0]; sl.mv=0; sl.posFixa=0;
    try{ fs=MT_FUNCS[sl.pos]; }catch(e){} mexeu=true; }
   if(!fs || !fs.length) continue;
   if(!sl.func || fs.indexOf(sl.func)<0){ sl.func=fs[0]; mexeu=true; }
   var x=+sl.x, y=+sl.y;
   if(!isFinite(x)||!isFinite(y)||x<0||x>100||y<0||y>100){
    sl.x=f[i][1]; sl.y=f[i][2]; sl.mv=0; mexeu=true;
   }
   var ch=Math.round((+sl.x||0))+"x"+Math.round((+sl.y||0));
   if(vistos[ch]){ sl.x=f[i][1]; sl.y=f[i][2]; sl.mv=0; mexeu=true; }
   else vistos[ch]=1;
   if(sl.posFixa && sl.pos!==f[i][0]) { /* legitimo, nao mexe */ }
  }
  if(mexeu){ try{ userStateSave(); }catch(e){}
   window.EL_SELO=(window.EL_SELO||0)+1;
   if(window.console) console.info("ELENCO_1608: as vagas do campo "
    +"estavam quebradas no time salvo e foram refeitas."); }
 }
 window.elSaneia=saneiaSlots;

function desenha(){
  var w=document.getElementById("mtwrap"); if(!w) return;
  /* O desenho não pode normalizar nem salvar x/y: o alinhamento do campo
     é uma escolha manual do usuário e só muda por arraste explícito. */
  /* Remove a barra antiga: ela tinha outro onchange que zerava as vagas. */
  var barraAntiga=w.querySelector(".mthd"); if(barraAntiga) barraAntiga.remove();
  var wrap=document.getElementById("elwrap");
  if(!wrap || !wrap.isConnected || !w.contains(wrap)) wrap=esqueleto();
  if(!wrap) return;
  var esq=document.getElementById("elesq");
  var campo=w.querySelector(".mtcampo");
  var viewport=document.getElementById("elcampo-viewport")||esq;
  if(campo && campo.parentNode!==viewport) viewport.appendChild(campo);
  try{ if(campo && !campo.querySelector(".risco"))
   campo.insertAdjacentHTML("afterbegin", window.EL_RISCOS); }catch(e){}
  var fx=document.getElementById("elfaixa");
  if(fx) fx.remove();
  var fm=document.getElementById("elfmt");
  if(fm && (document.activeElement===null || !fm.contains(document.activeElement)))
   fm.innerHTML=faixaDoElenco();

  var tit=(MT.slots||[]).filter(function(x){return x&&x.key;}).length;
  var nb=(MT.banco||[]).length;
  var entradasBanco=entradasDaColecaoVisual('banco');
  document.getElementById("elban").innerHTML=
   '<div class=elhd>Reservas <em>'+nb+' de '+TETO_BANCO+'</em></div>'
   +(nb?('<div class=elgrid>'
     +(MT.banco||[]).map(function(k,i){ return montaCard(k,"banco",null,entradasBanco[i]||null); }).join("")
     +'</div>')
    :'<div class=elvazia>Arraste cards para c\u00e1</div>')
   +(nb<TETO_BANCO
     ?'<div style="padding:10px 0 2px"><button class=elbt onclick="mtAddBanco()">'
      +'+ adicionar reserva</button></div>':"");
  desenhaFora();
  [].slice.call(w.querySelectorAll(".mtsl")).forEach(refazVaga);
  arrumaCampo();
  ligaArrasta();
  var cmp=w.querySelector(".mtcampo"), ed=false;
  try{ ed=!!MT_ED; }catch(e){}
  if(cmp){
   cmp.classList.toggle("movendo", ed);
   var av=cmp.querySelector(".elmove");
   if(ed && !av){ av=document.createElement("div"); av.className="elmove";
    av.textContent="\u2725 arraste as vagas para mover as posi\u00e7\u00f5es";
    cmp.appendChild(av); }
   else if(!ed && av) av.remove();
  }
  if(tit>TETO_TIT){ /* nunca deveria acontecer; so nao quebra */ }
 }

 function naAba(){
  var w=document.getElementById("mtwrap");
  return !!(w && w.style.display!=="none" && (w.innerHTML||"").length>200);
 }
 /* A Ficha pode salvar uma build enquanto o campo está oculto. Ao voltar
    para o Elenco, a navegação chama esta porta única no quadro já visível;
    ela só recompõe a geometria existente, sem renderizar nem salvar nada. */
 window.elRecalculaGeometriaAoVoltarFicha=function(){
  try{ if(!naAba()) return false; arrumaCampo(); return true; }
  catch(e){ return false; }
 };
 var ajusteInicialAgendado=false, revelacaoPendente=false, revelacaoFotosSeq=0;
 function vagasDoCampoResolvidas(){
  try{
   /* MT é lexical no motor; não existe window.MT. Consultar window.MT fazia
      uma escalação ocupada parecer vazia e liberava o quadro cedo demais. */
   var vagas=(typeof MT!=="undefined"&&Array.isArray(MT.slots))?MT.slots:[];
   for(var i=0;i<vagas.length;i++){
    var vaga=vagas[i];
    if(vaga&&vaga.key&&typeof mtCard==="function"&&!mtCard(vaga.key)) return false;
   }
   return true;
  }catch(e){ return false; }
 }
 function campoProntoParaFotos(revelar){
  try{
   var vagas=(typeof MT!=="undefined"&&Array.isArray(MT.slots))?MT.slots:[];
   var campo=revelar&&revelar.querySelector(".mtcampo");
   if(!campo) return false;
   var fotosEsperadas=0;
   for(var i=0;i<vagas.length;i++){
    var vaga=vagas[i]; if(!vaga||!vaga.key) continue;
    var el=campo.querySelector('.mtsl[data-i="'+i+'"]');
    if(!el) return false;
    var card=null; try{card=typeof mtCard==="function"?mtCard(vaga.key):null;}catch(e){}
    if(card){
     fotosEsperadas++;
     if(!el.querySelector(".elcard img")) return false;
    }else{
     /* Depois da última leva, uma chave realmente órfã permanece ocupada e
        indisponível, mas não pode prender para sempre a revelação do campo. */
     if(!window.ENC_DADOS_COMPLETOS||!el.querySelector(".elvazio-indisponivel")) return false;
    }
   }
   return campo.querySelectorAll(".elcard img").length===fotosEsperadas;
  }catch(e){ return false; }
 }
 function aguardaFotosDoCampo(revelar){
  if(!revelar) return false;
  var seq=++revelacaoFotosSeq,imgs=[];
  try{imgs=[].slice.call(revelar.querySelectorAll(".mtcampo .elcard img"));}catch(e){imgs=[];}
  try{revelar.style.visibility="hidden";}catch(e2){}
  function revela(){requestAnimationFrame(function(){
   if(seq!==revelacaoFotosSeq||revelar.isConnected===false)return;
   try{revelar.style.removeProperty("visibility");}catch(e){}
  });}
  if(!imgs.length){revela();return true;}
  var encerrado=false,limite=null;
  function termina(){if(encerrado)return;encerrado=true;
   if(limite!==null)clearTimeout(limite);revela();}
  var esperas=imgs.map(function(img){return new Promise(function(resolve){
   function decodifica(){var p=null;try{if(typeof img.decode==='function')p=img.decode();}catch(e){}
    Promise.resolve(p).catch(function(){}).then(resolve);}
   if(img.complete){decodifica();return;}
   function pronta(){try{img.removeEventListener('load',pronta);img.removeEventListener('error',pronta);}catch(e){}
    decodifica();}
   try{img.addEventListener('load',pronta,{once:true});img.addEventListener('error',pronta,{once:true});}
   catch(e){decodifica();}
  });});
  Promise.all(esperas).then(termina);
  /* Uma origem que não conclui não pode prender o Elenco. Nesse caso o
     próprio fallback já aprovado ocupa a foto e o quadro é revelado inteiro. */
  limite=setTimeout(function(){imgs.forEach(function(img){
   try{if(!img.complete)falhaFotoCard(img);}catch(e){}
  });termina();},6000);
  return true;
 }
 window.elAguardaFotosDoCampo=aguardaFotosDoCampo;
 function concluiAjusteInicial(revelar){
  if(ajusteInicialAgendado) return;
  ajusteInicialAgendado=true;
  requestAnimationFrame(function(){
   ajusteInicialAgendado=false;
   try{ if(naAba()) arrumaCampo(); }catch(e){}
   if(!revelar) return;
   /* Uma vaga com chave salva não pode ser exibida como placeholder enquanto
      a leva assíncrona do catálogo ainda não tornou aquela carta consultável. */
   if(campoProntoParaFotos(revelar)){
    revelacaoPendente=false;
    aguardaFotosDoCampo(revelar);
    return;
   }
   /* Enquanto ainda pode chegar uma linha de titular, não fotografa o DOM
      parcial. O evento final redesenha primeiro e só então volta à barreira. */
   if(window.ENC_DADOS_COMPLETOS){
    requestAnimationFrame(function(){
     try{ if(naAba()) desenha(); }catch(e){}
     if(campoProntoParaFotos(revelar)){
      revelacaoPendente=false; aguardaFotosDoCampo(revelar);
     }
    });
    return;
   }
   if(revelacaoPendente) return;
   revelacaoPendente=true;
   window.addEventListener("encaixe:dados-completos", function(){
    revelacaoPendente=false;
    requestAnimationFrame(function(){ concluiAjusteInicial(revelar); });
   }, {once:true});
  });
 }
 /* A entrada pelo cabeçalho e a restauração de rota usam a mesma guarda.
    Isso só controla visibilidade: não renderiza, não salva e não altera vagas. */
 window.elAguardaCampoCompleto=function(){
  var campo=document.getElementById("mtwrap");
  if(!campo || !naAba()) return false;
  campo.style.visibility="hidden";
  concluiAjusteInicial(campo);
  return true;
 };
 function depois(){
  try{
   document.body.classList.toggle("naelenco", naAba());
   if(!naAba()) return;
   desenha();
   arrumaCampo();
  }catch(e){ if(window.console) console.warn("ELENCO_1608:", e); }
 }
 window.elRedesenha=depois;
 /* As portas de adicionar jogador pertencem ao ElencoAddController. O antigo
    wrapper de 60 ms foi removido: ele redesenhava a mesma seleção depois do
    dono base e criava uma segunda ordem de execução. */
 var _mr2=window.mtRender;
 window.mtRender=function(){
  /* Antes do único render do campo, normaliza apenas chaves antigas que a
     base atual ainda reconhece pelo mesmo ID. Sem isso, a vaga mantém a
     função, mas mtCard(key) falha e ela aparece como placeholder vazio. */
  try{ saneiaSlots(); }catch(e){}
  var v=_mr2.apply(this,arguments); depois(); return v;
 };
 window.addEventListener("resize", function(){ try{ arrumaCampo(); }catch(e){} });
 var _mtToggleEstado=window.mtToggle;
 if(typeof _mtToggleEstado==="function") window.mtToggle=function(){
  var entrando=false, campo=document.getElementById("mtwrap");
  try{ entrando=typeof MT_ON!=="undefined" && !MT_ON; }catch(e){}
  /* O render base cria as 11 vagas de uma vez, mas no primeiro quadro o
     campo ainda pode não ter a largura final. Só revela o mesmo DOM após a
     geometria das vagas estar calculada; não dispara outro mtRender. */
  if(entrando && campo) campo.style.visibility="hidden";
  /* Se o catálogo já terminou enquanto o Elenco estava fechado, descarta
     somente respostas provisórias de molde antes da renderização nativa de
     entrada. Assim não há uma segunda renderização nessa mesma navegação. */
  try{ if(entrando && window.ENC_DADOS_COMPLETOS && typeof window.elLimpaCachePontuacao==='function') window.elLimpaCachePontuacao(); }catch(e){}
  var v=_mtToggleEstado.apply(this,arguments);
  try{ document.body.classList.toggle("naelenco", naAba()); }catch(e){}
  if(entrando) concluiAjusteInicial(campo);
  return v;
 };
 if(document.readyState==="loading") document.addEventListener("DOMContentLoaded", depois);
 else depois();
})();


/* bloco JavaScript 27 */

/* ===== BUILD_DO_USUARIO_1608 ===== */
(function(){
 if(window.BUILD_DO_USUARIO_1608) return; window.BUILD_DO_USUARIO_1608=1;
 var TETO_BUILDS=30;
 window.EL_SELO=0;

 function base(k){ return String(k).split("|")[0].split("@")[0]; }
 function chaveAberta(){
  try{ if(typeof CUR!=="undefined" && CUR) return CUR; }catch(e){}
  return null;
 }
 var BUILD_ID_SEQ=0;
 function buildIdDaBuild(b){
  return b && typeof b.buildId==='string' && b.buildId.trim()
   ? b.buildId.trim() : null;
 }
 function criaBuildId(usados){
  usados=usados||{};
  for(var tentativa=0;tentativa<20;tentativa++){
   var token='';
   try{
    if(window.crypto && typeof window.crypto.randomUUID==='function')
     token=window.crypto.randomUUID();
   }catch(e){}
   if(!token){
    try{
     var bytes=new Uint32Array(4); window.crypto.getRandomValues(bytes);
     token=Array.prototype.map.call(bytes,function(n){ return ('00000000'+n.toString(16)).slice(-8); }).join('-');
    }catch(e){}
   }
   if(!token) token=Date.now().toString(36)+'-'+(++BUILD_ID_SEQ).toString(36)+'-'+Math.random().toString(36).slice(2,10);
   var id='bld_'+String(token).toLowerCase();
   if(!usados[id]){ usados[id]=1; return id; }
  }
  var fallback;
  do{ fallback='bld_'+Date.now().toString(36)+'-'+(++BUILD_ID_SEQ).toString(36); }
  while(usados[fallback]);
  usados[fallback]=1; return fallback;
 }
 function idsEmUso(m){
  var usados={};
  Object.keys((m&&m.builds)||{}).forEach(function(idb){
   var L=Array.isArray(m.builds[idb])?m.builds[idb]:[];
   L.forEach(function(b){ var id=buildIdDaBuild(b); if(id) usados[id]=1; });
  });
  return usados;
 }
 function novoBuildId(m){ return criaBuildId(idsEmUso(m)); }
 function migraBuildIds(m){
  if(!m || !m.builds || typeof m.builds!=='object') return false;
  var usados={}, mudou=false;
  Object.keys(m.builds).forEach(function(idb){
   var L=Array.isArray(m.builds[idb])?m.builds[idb]:[];
   L.forEach(function(b){
    if(!b || typeof b!=='object') return;
    var id=buildIdDaBuild(b);
    if(!id || usados[id]){
     b.buildId=criaBuildId(usados); mudou=true;
    } else usados[id]=1;
   });
  });
  return mudou;
 }
 function buildIdInicialDaVaga(m,sl){
  if(!sl || !sl.key) return 'base';
  var idb=base(sl.key), L=Array.isArray(m.builds[idb])?m.builds[idb]:[];
  var pref=m.buildOn&&m.buildOn[idb], id=buildIdDaReferencia(L,pref);
  return id||'base';
 }
 function migraBuildIdsDasVagas(m){
  if(!m || !Array.isArray(m.slots)) return false;
  var mudou=false;
  m.slots.forEach(function(sl){
   if(!sl || typeof sl!=='object') return;
   var idb=sl.key?base(sl.key):null;
   var L=idb&&Array.isArray(m.builds[idb])?m.builds[idb]:[];
   var atual=String(sl.buildId||'');
   /* Ausência legado pode ser migrada uma vez; identidade explícita inválida
      permanece inválida para falhar fechado, nunca vira Básica silenciosa. */
   var destino=!atual?buildIdInicialDaVaga(m,sl):atual;
   if(sl.buildId!==destino){ sl.buildId=destino; mudou=true; }
  });
  return mudou;
 }
 function indiceDaBuildId(L,buildId){
  var id=String(buildId||'');
  for(var i=0;i<(L||[]).length;i++) if(buildIdDaBuild(L[i])===id) return i;
  return -1;
 }
 function buildIdDaReferencia(L,ref){
  if(ref===undefined || ref===null || ref==='') return null;
  if(typeof ref==='string' && indiceDaBuildId(L,ref)>=0) return ref;
  var indice=Number(ref);
  return Number.isInteger(indice) && L[indice] ? buildIdDaBuild(L[indice]) : null;
 }
 function substituiBuildPorId(L,buildId,nova){
  var indice=indiceDaBuildId(L,buildId); if(indice<0) return -1;
  nova.buildId=buildId; L[indice]=nova; return indice;
 }
 function removeBuildPorId(L,buildId){
  var indice=indiceDaBuildId(L,buildId); if(indice<0) return null;
  return {indice:indice,build:L.splice(indice,1)[0]};
 }
 var _entrySeq=0;
 function novoEntryId(usados){
  var id='';try{if(window.crypto&&window.crypto.randomUUID)id='entry_'+window.crypto.randomUUID().toLowerCase();}catch(e){}
  if(!id){
   var s=String(Date.now())+'|'+String(++_entrySeq),h=2166136261;
   for(var i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619);}
   id='entry_runtime_'+('00000000'+(h>>>0).toString(16)).slice(-8);
  }
  while(usados[id])id=id+'_'+(++_entrySeq);usados[id]=1;return id;
 }
 function sincronizaEntradasDasListas(m){
  m.listEntries=(m.listEntries&&typeof m.listEntries==='object')?m.listEntries:{};
  var metaBanco=Array.isArray(m.listEntries.banco)?m.listEntries.banco:[];
  var metaFora=Array.isArray(m.listEntries.fora)?m.listEntries.fora:[];
  var pool=[],usados={},atribuidos={},mudou=false;
  metaBanco.forEach(function(e,i){pool.push({e:e,c:'banco',i:i,u:false});});
  metaFora.forEach(function(e,i){pool.push({e:e,c:'fora',i:i,u:false});});
  function key(e){return String(e&&e.cardKey||'');}
  function acha(k,c,i){
   var q,p;
   for(q=0;q<pool.length;q++){p=pool[q];if(!p.u&&p.c===c&&p.i===i&&key(p.e)===k){p.u=true;return p.e;}}
   for(q=0;q<pool.length;q++){p=pool[q];if(!p.u&&p.c===c&&key(p.e)===k){p.u=true;return p.e;}}
   for(q=0;q<pool.length;q++){p=pool[q];if(!p.u&&key(p.e)===k){p.u=true;return p.e;}}
   return null;
  }
  pool.forEach(function(p){var id=p.e&&p.e.entryId;if(id&&!usados[id])usados[id]=1;});
  function monta(lista,c){
   return (lista||[]).map(function(k,i){
    k=String(k);var antiga=acha(k,c,i),e=antiga?Object.assign({},antiga):{};
    if(!e.entryId||atribuidos[e.entryId])e.entryId=novoEntryId(usados);
    atribuidos[e.entryId]=1;
    var idb=base(k),L=Array.isArray(m.builds&&m.builds[idb])?m.builds[idb]:[];
    if(!e.buildId)e.buildId='base';
    var ib=e.buildId==='base'?-1:indiceDaBuildId(L,e.buildId),bAplicada=ib>=0?L[ib]:null;
    /* A build aplicada é a autoridade funcional. Uma referência ausente fica
       inválida e visível; nunca é rebaixada silenciosamente para Básica. */
    e.collection=c;e.cardId=idb;e.cardKey=k;
    e.functionId=(bAplicada&&bAplicada.func)?String(bAplicada.func)
     :(e.functionId||String(k).split('|').slice(1).join('|')||null);
    if(!antiga||JSON.stringify(antiga)!==JSON.stringify(e))mudou=true;
    return e;
   });
  }
  var banco=monta(m.banco||[],'banco'),fora=monta(m.elenco||[],'fora');
  if(JSON.stringify(metaBanco)!==JSON.stringify(banco)||JSON.stringify(metaFora)!==JSON.stringify(fora))mudou=true;
  m.listEntries.banco=banco;m.listEntries.fora=fora;return mudou;
 }
 window.elSincronizaEntradasDasListas=sincronizaEntradasDasListas;
 function entradasDaColecao(c){var m=bd();return m&&m.listEntries&&Array.isArray(m.listEntries[c])?m.listEntries[c]:[];}
 function buildDaEntrada(entrada,idb){
  if(!entrada||String(entrada.buildId||'base')==='base')return null;
  idb=idb||entrada.cardId||base(entrada.cardKey||'');var L=buildsDe(idb),i=indiceDaBuildId(L,entrada.buildId);
  return i>=0?L[i]:null;
 }
 function bd(){ if(typeof MT==="undefined") return null;
  MT.builds=MT.builds||{}; MT.buildOn=MT.buildOn||{};
  var mudou=migraBuildIds(MT);
  if(migraBuildIdsDasVagas(MT)) mudou=true;
  if(sincronizaEntradasDasListas(MT)) mudou=true;
  if(mudou) try{ userStateSave(); }catch(e){}
  return MT; }
 function buildsDe(idb){ var m=bd(); if(!m) return []; return m.builds[idb]||[]; }
function buildAtiva(idb){
  /* Preferência provisória da Ficha. O Elenco usa exclusivamente buildDaVaga. */
  var L=buildsDe(idb); if(!L.length) return null;
  var m=bd(), i=m.buildOn[idb];
  if(i==='base') return null;
  if(i===undefined||i===null||!L[i]) i=0;
  return L[i];
 }
 function buildDaVaga(sl,idb){
  var m=bd(); if(!m || !sl) return null;
  idb=idb||base(sl.key||'');
  var L=Array.isArray(m.builds[idb])?m.builds[idb]:[];
  var buildId=String(sl.buildId||'base');
  if(buildId==='base') return null;
  var indice=indiceDaBuildId(L,buildId);
  return indice>=0?L[indice]:null;
 }
 window.elBuildsDe=buildsDe; window.elBuildAtiva=buildAtiva;
 window.elBuildDaVaga=buildDaVaga;
 window.elBuildDaEntrada=buildDaEntrada;
 window.elEntradasDaColecao=entradasDaColecao;
 window.elMigraBuildIdsDasVagas=migraBuildIdsDasVagas;
 try{ bd(); }catch(e){}

 /* ---------- 2 · LER E APLICAR UMA BUILD ---------- */
 function impetoFabricado(c){
  try{ if(typeof impAdicionado==="function") return impAdicionado(c)||null; }catch(e){}
  var im=(c.imps||[]).filter(function(x){ return !!x.f; });
  return im.length?im[0].n:null;
 }
 function leDaTela(key){
  var c=null; try{ c=_card(key); }catch(e){}
  if(!c) return null;
  /* +2/+3 sao apenas simulacoes. O save recebe a fotografia completa do +1
     capturada antes da entrada na simulacao, sem alterar nem redesenhar a
     Ficha que o usuario esta vendo. */
  if((+c.cmode||0)>0 && c._fotoBuildGrauBase){
   var base1=fotoDaBuild(c._fotoBuildGrauBase);
   base1.func=c.tipo; base1.grau=1;
   return base1;
  }
  var habs=[]; try{ habs=(c._habs!==undefined?c._habs:(c.HAB||[])).slice(); }catch(e){}
  var lvl={}; try{ lvl=_lvlDe(c); }catch(e){}
  return {func:c.tipo, lvl:lvl, habs:habs, imp:impetoFabricado(c),
          /* O técnico escolhido na Ficha também é um insumo da build. A
             fotografia precisa preservá-lo na criação normal, não só ao
             editar uma build existente. */
          tec:(Array.isArray(c._tec)?c._tec.slice():null),
          tecNome:(c._tecNome!==undefined?c._tecNome:null),
          /* Grau do condicional pertence ao contexto do elenco; builds salvam a base. */
          grau:1};
 }

 /* A NOTA DE UMA BUILD.
    Mesma receita do `notaCfg` da casca (guarda, mexe, le, devolve), mais
    a diferenca das habilidades pela mesma conta do `_trocaHabs`. Nada
    aqui e formula nova: `valsDeLvl`, `cadeia`, `notaDe`, `b1nDe` e `nota`
    sao os do motor. */
 var HREF={};
 function habsDoOri(c,key){
  if(HREF[key]===undefined){
   try{ HREF[key]=(c._habs!==undefined?c._habs:(c.HAB||[])).slice(); }
   catch(e){ HREF[key]=[]; }
  }
  return HREF[key];
 }
 function impSoDeFabrica(t){
  t=String(t==null?"":t);
  var i=t.indexOf("o motor p");
  if(i>0) t=t.slice(0,i).replace(/\s*[\u00b7+]\s*$/,"");
  t=t.replace(/\s*[\u00b7+]\s*[^\u00b7]*\u2692\s*$/,"");
  return t;
 }
 function pctDoMolde(A){
  var n=0,d=0,i,w; A=A||[];
  for(i=0;i<A.length;i++){ w=A[i][1]; if(!w) continue;
   n+=w*A[i][3]; d+=w*A[i][2]; }
  return d?100*n/d:0;
 }
 function notaDaBuild(key, b, comTecnicoDoTime, tecnicoExplicito){
  var c=null; try{ c=_card(key); }catch(e){}
  if(!c) return 0;
  var g={ b1:c.b1, b1n:c.b1n, imp:c.imp,
          habs:c._habs, tec:c._tec, tecNome:c._tecNome,
          sis:(c.sis||[]).slice(),
          arows:c.arows.map(function(r){ return r.slice(); }) };
  var v=0;
  try{
   c._habs=(b.habs||[]).slice();
   if(tecnicoExplicito){
    c._tec=(tecnicoExplicito.bonus||[]).slice();
    c._tecNome=tecnicoExplicito.nome||null;
   } else if(comTecnicoDoTime){
    try{ c._tec=mtTecBs()||[]; }catch(e){ c._tec=[]; }
    try{ c._tecNome=mtTecNome()||null; }catch(e){ c._tecNome=null; }
   } else { c._tec=[]; c._tecNome=null; }
   c.imp=impSoDeFabrica(g.imp);
   if(b.imp) c.imp = c.imp + " \u00b7 o motor pos: " + b.imp;
   try{ delete c._cp; delete c._n; }catch(e){}
   var vals=valsDeLvl(c, b.lvl||{});
   c.arows.forEach(function(r){ r[3]=vals[r[0]]; r[4]=r[3]-r[2]; r[5]=r[3]; });
   c.sis=vals.slice();
   c.b1=notaDe(vals,c.arows);
   c.b1n=pctDoMolde(c.arows);
   delete c._n;
   v=nota(c);
  }catch(e){ v=0; }
  c.b1=g.b1; c.b1n=g.b1n; c.imp=g.imp; c.arows=g.arows; c.sis=g.sis;
  if(g.habs===undefined) delete c._habs; else c._habs=g.habs;
  if(g.tec===undefined) delete c._tec; else c._tec=g.tec;
  if(g.tecNome===undefined) delete c._tecNome; else c._tecNome=g.tecNome;
  try{ delete c._cp; delete c._n; }catch(e){}
  return v;
 }
 window.elNotaDaBuild=notaDaBuild;
 function tecnicoDoTime(){
  var t={id:null,nome:null,bonus:[]};
  try{ t.id=(typeof MT!=='undefined')?MT.tec:null; }catch(e){}
  try{ t.nome=mtTecNome()||null; }catch(e){}
  try{ t.bonus=(mtTecBs()||[]).slice(); }catch(e){ t.bonus=[]; }
  return t;
 }
 function fotoDaBuild(b){
  var f={}, k;
  b=b||{};
  for(k in b) if(Object.prototype.hasOwnProperty.call(b,k)){
   if(k==='lvl'){
    f.lvl={}; for(var barra in (b.lvl||{})) f.lvl[barra]=+b.lvl[barra]||0;
   } else if(k==='habs') f.habs=(b.habs||[]).slice();
   else if(Array.isArray(b[k])) f[k]=b[k].slice();
   else f[k]=b[k];
  }
  if(!f.lvl) f.lvl={};
  if(!f.habs) f.habs=[];
  return f;
 }
 /* Servico unico e reutilizavel. Recebe uma fotografia da build, o molde da
    funcao e o tecnico; devolve apenas o resultado e nunca troca a build ativa. */
 function calculaNotaBuildFuncao(k,b,func,tecnico){
  try{ if(typeof window.elFuncaoDoCatalogo==='function') func=window.elFuncaoDoCatalogo(k,func); }catch(e){}
  if(!func)return {n:0,func:null,compativel:false,motivo:'funcao-ausente'};
  var idb=base(k), alvo=idb+'|'+String(func||''), c=null;
  try{ c=_card(alvo); }catch(e){ c=null; }
  if(!c) return {n:0,func:func||null,compativel:false,motivo:'molde-ausente'};
  var t=tecnico||tecnicoDoTime(), foto=fotoDaBuild(b), n=0;
  n=notaDaBuild(alvo,foto,true,t);
  if(typeof n!=='number'||!isFinite(n))
   return {n:0,func:func,compativel:false,motivo:'nota-invalida'};
  return {n:n,func:func,compativel:true,motivo:null};
 }
 window.elTecnicoDoTime=tecnicoDoTime;
 window.elCalculaNotaBuildFuncao=calculaNotaBuildFuncao;
 window.EF_PONTO=function(key, opts){
  opts=opts||{};
  var b=opts.build;
  if(!b){ try{ b=buildAtiva(base(key)); }catch(e){} }
  if(!b) b=buildBase(key);
  var comTec=(opts.comTecnicoDoTime!==false);
  return notaDaBuild(key, b, comTec);
 };
 window.EF_PORQUE=function(key){
  var c=null; try{ c=_card(key); }catch(e){}
  if(!c){ console.warn("nao achei o card", key); return null; }
  var idb=base(key), b=buildAtiva(idb), qual=b?("build \u201c"+b.nome+"\u201d"):"carta base";
  if(!b) b=buildBase(key);
  var r={ carta:c.nome, funcao:String(key).split("|")[1], vem_de:qual,
          pontos_nas_barras:(function(){ var t=0,k; for(k in (b.lvl||{})) t+=(+b.lvl[k]||0); return t; })(),
          habilidades_adicionadas:(b.habs||[]).length,
          impeto_escolhido:(b.imp||"\u2014"),
          tecnico_do_time:(function(){ try{ return mtTecNome()||"\u2014"; }catch(e){ return "?"; } })(),
          SEM_o_tecnico:+notaDaBuild(key,b,false).toFixed(2),
          COM_o_tecnico:+notaDaBuild(key,b,true).toFixed(2),
          maximo_do_motor:+(function(){ try{ delete c._n; return nota(c); }catch(e){ return 0; } })().toFixed(2) };
  console.table(r); return r;
 };

 /* A CARTA BASE: nenhum ponto gasto, nenhuma habilidade adicionada,
    nenhum tecnico, so o impeto nativo. */
 function buildBase(key){
  var z={}; try{ MBK.forEach(function(b){ z[b]=0; }); }catch(e){}
  var c=null; try{ c=_card(key); }catch(e){}
  return {func:c?c.tipo:null, lvl:z, habs:[], imp:null, grau:1, base:1};
 }
 window.elBuildBase=buildBase;

 function aplicaImpetoDaFotoSemRender(c,nome){
  var marca='o motor pos:', atual=String(c&&c.imp||''), p=atual.indexOf(marca);
  var fabrica=(p>=0?atual.slice(0,p):atual).replace(/[·\s]+$/,'').replace(/\s*⚒\s*$/,'').trim();
  var adicional=(!nome||nome==='(nenhum)')?'':String(nome).trim();
  c.imp=[fabrica,adicional?(marca+' '+adicional):''].filter(Boolean).join(' · ');
  c.imps=(c.imps||[]).filter(function(x){ return !x.f; });
  if(adicional)c.imps.push({n:adicional,c:0,f:1});
 }
 function aplicaNaTela(key, b, opcoes){
  var c=null; try{ c=_card(key); }catch(e){}  if(!c) return false;
  b=fotoDaBuild(b);
  try{ _marca(key); }catch(e){}
  var anterior={cmode:c.cmode,grau:window._GRAU_COND,
   habs:c._habs,tec:c._tec,tecNome:c._tecNome,TECB:c.TECB,
   imp:c.imp,imps:c.imps,sis:c.sis,sisBar:c.sisBar,sobra:c.sobra,
   arows:(c.arows||[]).map(function(r){return r.slice();}),
   b1:c.b1,b1n:c.b1n,cp:c._cp,n:c._n};
  function restauraAnterior(){
   c.cmode=anterior.cmode; window._GRAU_COND=anterior.grau;
   if(anterior.habs===undefined)delete c._habs;else c._habs=anterior.habs;
   if(anterior.tec===undefined)delete c._tec;else c._tec=anterior.tec;
   if(anterior.tecNome===undefined)delete c._tecNome;else c._tecNome=anterior.tecNome;
   c.TECB=anterior.TECB; c.imp=anterior.imp; c.imps=anterior.imps;
   c.sis=anterior.sis; c.sisBar=anterior.sisBar; c.sobra=anterior.sobra;
   c.arows=anterior.arows; c.b1=anterior.b1; c.b1n=anterior.b1n;
   if(anterior.cp===undefined)delete c._cp;else c._cp=anterior.cp;
   if(anterior.n===undefined)delete c._n;else c._n=anterior.n;
  }
  /* Reidratação atômica: todos os insumos chegam ao card antes da única
     avaliação. Não chama editImp, _grava nem _trocaHabs, pois esses caminhos
     desenham estados parciais. A build salva sempre reabre na base +1. */
  c.cmode=0; window._GRAU_COND=1;
  c._habs=(b.habs||[]).slice();
  var estadoTec={tec:[],tecNome:null};
  try{ estadoTec=restauraTecnicoDaBuildNoEditor(key,b); }catch(e){}
  c._tec=(estadoTec.tec||[]).slice(); c._tecNome=estadoTec.tecNome||null;
  c.TECB=c._tec.slice();
  aplicaImpetoDaFotoSemRender(c,b.imp);
  var lvl={}; try{ MBK.forEach(function(x){ lvl[x]=+(b.lvl&&b.lvl[x])||0; }); }catch(e){}
  var vals=null;
  try{ vals=valsDeLvl(c,lvl); }catch(e){ vals=null; }
  if(!vals || !vals.length){ restauraAnterior(); return false; }
  c.sis=vals.slice();
  try{ c.sisBar=MBK.filter(function(x){ return lvl[x]>0; }).map(function(x){ return [MBN[x],lvl[x]]; }); }catch(e){}
  try{ c.sobra=(c.orc||0)-gastoDe(lvl); }catch(e){}
  (c.arows||[]).forEach(function(r){ r[3]=vals[r[0]]; r[4]=r[3]-r[2]; r[5]=r[3]; });
  try{ c.b1=notaDe(vals,c.arows); }catch(e){}
  try{ if(typeof window._renota==='function') window._renota(c); else { delete c._cp; delete c._n; } }catch(e){}
  /* O resolvedor inicial da Ficha prepara a fotografia dentro da mesma
     transicao do FichaController. Nesse caminho o controlador faz o unico
     desenho; os chamadores historicos continuam desenhando como antes. */
  if(opcoes && opcoes.somentePreparar===true) return true;
  try{
   if(window.FichaController
      && typeof window.FichaController.openSavedBuild==='function'
      && window.FichaController.openSavedBuild(key)===true) return true;
  }catch(e){}
  restauraAnterior();
  return false;
 }

 /* Porta somente leitura do estado do usuario para a abertura da Ficha.
    Ela nao migra, nao salva e nao usa MT.buildOn. A identidade autenticada
    futura entra por esta porta sem mudar a regra do FichaController. */
 function fotografiaUsuarioParaFicha(cardId,referencia){
  cardId=base(cardId); var m=null, builds=[], ocorrencias=[];
  try{ m=(typeof MT!=='undefined')?MT:null; }catch(e){ m=null; }
  if(!m) return {ownerId:null,cardId:cardId,builds:[],occurrences:[]};
  var lista=Array.isArray(m.builds&&m.builds[cardId])?m.builds[cardId]:[];
  lista.forEach(function(b,ordem){
   var id=buildIdDaBuild(b);
   if(!b || !id || !String(b.func||'').trim()) return;
   builds.push({buildId:id,functionId:String(b.func),order:ordem,photo:fotoDaBuild(b)});
  });
  function inclui(origem,cardKey,functionId,buildId,entryId,slotId,index,pos){
   if(base(cardKey)!==cardId) return;
   ocorrencias.push({origin:origem,cardKey:String(cardKey),functionId:functionId||null,
    buildId:buildId==null?null:String(buildId).trim(),entryId:entryId||null,
    slotId:slotId||null,index:index,pos:pos||null});
  }
  (m.slots||[]).forEach(function(sl,i){
   if(sl&&sl.key) inclui('campo',sl.key,sl.func,sl.buildId,sl.entryId||null,
    sl.slotId||('slot_'+(i+1)),i,sl.pos||null);
  });
  [['banco',m.banco],['fora',m.elenco]].forEach(function(par){
   var colecao=par[0],cards=Array.isArray(par[1])?par[1]:[];
   var meta=m.listEntries&&Array.isArray(m.listEntries[colecao])?m.listEntries[colecao]:[];
   cards.forEach(function(k,i){
    var e=meta[i],valida=e&&base(e.cardKey||e.cardId)===base(k);
    inclui(colecao,k,valida&&e.functionId,valida&&e.buildId,valida&&e.entryId,null,i,null);
   });
  });
  var solicitada=null;
  if(referencia){
   for(var oi=0;oi<ocorrencias.length;oi++){
    var o=ocorrencias[oi];if(o.origin!==referencia.origin)continue;
    if(referencia.cardKey&&String(o.cardKey)!==String(referencia.cardKey))continue;
    if(o.origin==='campo'){
     if(!Number.isInteger(+referencia.index)||+o.index!==+referencia.index)continue;
     if(referencia.entryId&&String(o.entryId||'')!==String(referencia.entryId))continue;
    }else if(!referencia.entryId||String(o.entryId||'')!==String(referencia.entryId))continue;
    solicitada=Object.assign({},o);break;
   }
  }
  return {ownerId:null,cardId:cardId,builds:builds,occurrences:ocorrencias,
   requested:!!referencia,requestedOccurrence:solicitada};
 }
 function buildDaFotoUsuario(cardId,buildId){
  var m=null; try{m=(typeof MT!=='undefined')?MT:null;}catch(e){}
  var L=m&&m.builds&&Array.isArray(m.builds[base(cardId)])?m.builds[base(cardId)]:[];
  var i=indiceDaBuildId(L,buildId); return i>=0?L[i]:null;
 }
 function preparaPlanoInicialDaFicha(plano){
  if(!plano||!plano.key) return false;
  var key=String(plano.key),idb=base(key),foto=null;
  if(plano.kind==='saved'){
   var b=buildDaFotoUsuario(idb,plano.buildId); if(!b) return false;
   var sessao={idb:String(idb),buildId:String(plano.buildId),func:b.func,
    nome:b.nome||'build'};
   if(!window.FichaState) return false;
   window.FichaState.startEdit(sessao,key);
   foto=fotoDaBuild(b);
  }else if(plano.kind==='base'){
   if(!window.FichaState) return false;
   window.FichaState.beginNew(key,{kind:'base'}); foto=buildBase(key);
  }else return false;
  window.BLD_SUJO=0;
  return aplicaNaTela(key,foto,{somentePreparar:true})===true;
 }
 window.FichaUserStatePort=Object.freeze({snapshotCard:fotografiaUsuarioParaFicha,
  prepareInitial:preparaPlanoInicialDaFicha});

 /* ---------- 3 · O MODAL ABRE NO MAXIMO POSSIVEL ----------
    Ordem do Luis: *"quando ele clicar, ele vai abrir o modal que abre pra
    todo mundo, que e o que esta no maximo possivel."* E a aba FAZER MINHA
    BUILD tem de comecar na CARTA BASE, nao na build do motor — que era o
    defeito que ele viu no Messi (112,03 e 62/62 nas duas abas). */
 /* ---------- 4 · A MELHOR FUNCAO JA ESCOLHIDA ----------
    *"o modal ja vai aparecer por padrao com a melhor funcao escolhida."* */
 function melhorFuncao(idb){
  var melhor=null;
  try{
   D.forEach(function(x){
    if(!x || x.id==="MOLDE") return;
    if(String(x.id).split("@")[0]!==idb) return;
    var n=nota(x);
    if(!melhor||n>melhor.n) melhor={n:n, tipo:x.tipo, id:x.id};
   });
  }catch(e){}
  return melhor;
 }
 window.elMelhorFuncao=melhorFuncao;
 window.elAbreNaMelhor=function(k){
  var m=melhorFuncao(base(k));
  try{ abrir(m?(m.id+"|"+m.tipo):k); }catch(e){}
 };
 window.elAbreCard=function(k){
  /* Todas as origens entram no mesmo resolvedor do FichaController. */
  try{ return window.FichaController&&window.FichaController.openCard(k); }catch(e){}
  return false;
 };
 window.elAbreOcorrencia=function(k,origem,identidade){
  var ref={origin:String(origem||''),cardKey:String(k||'')};
  if(ref.origin==='campo')ref.index=+identidade;
  else ref.entryId=String(identidade||'');
  try{return window.FichaController&&typeof window.FichaController.openOccurrence==='function'
   &&window.FichaController.openOccurrence(k,ref);}catch(e){}
  return false;
 };

 /* ---------- 5 · A LISTA DE FUNCOES PARA DE SE MEXER ----------
    Ordem do Luis, 16/08: *"a funcao de falso nove deveria estar verde
    maior e mais escura, e ficou menor. Cada vez que a gente mexe ela
    altera. Ela nao tem que alterar nao, essas coisas aqui sao fixas."*

    MEDIDO, e a causa nao e a ordem nem o numero (esses ja estavam
    congelados): e o ESTILO. O gerador desenha cada faixa assim —
        irm.sort(function(a,b){ return b._n-a._n; });
        var p=1-(ix/(irm.length-1)), k=cores(p);
    ou seja, a cor, o padding e o tamanho da letra saem da POSICAO NA
    LISTA. O `_n` da funcao aberta e recalculado quando o Luis mexe nas
    barras e as outras ficam com o valor velho: a ordem vira, o Falso nove
    cai para 2o e ganha a roupa do 2o — e o congelador de ordem devolve
    ele ao topo ja vestido errado.
    Aqui a roupa e guardada por NOME DE FUNCAO na primeira abertura da
    carta e reposta em toda renderizacao. ⛔ Nenhum numero e tocado. */
 var _roupa={};
 function congelaEstiloDaLista(){
  var bx=document.getElementById("box"); if(!bx) return;
  var k=chaveAberta(); if(!k) return;
  var idb=base(k);
  var bts=[].slice.call(bx.querySelectorAll(".cbfn"));
  if(bts.length<2) return;
  function nomeDe(e){ var q=e.querySelector("i");
   return q?String(q.textContent||"").trim():""; }
  if(!_roupa[idb]){
   var m={};
   bts.forEach(function(e){
    var nm=nomeDe(e); if(!nm) return;
    var i=e.querySelector("i"), b=e.querySelector("b");
    m[nm]={bg:e.style.background, bd:e.style.borderColor, tx:e.style.color,
           pad:e.style.padding,
           fi:i?i.style.fontSize:"", fb:b?b.style.fontSize:""};
   });
   _roupa[idb]=m;
   return;
  }
  var m2=_roupa[idb];
  bts.forEach(function(e){
   var nm=nomeDe(e), r=m2[nm]; if(!r) return;
   var aberta=e.classList.contains("cbfnq");
   e.style.background=r.bg;
   e.style.borderColor=aberta?"#ffffff":r.bd;
   e.style.color=r.tx;
   e.style.padding=r.pad;
   var i=e.querySelector("i"), b=e.querySelector("b");
   if(i&&r.fi) i.style.fontSize=r.fi;
   if(b&&r.fb) b.style.fontSize=r.fb;
  });
 }

 /* ---------- 6 · A BARRA DE SALVAR ---------- */
function ehFazerMinha(){
   try{ return !!window.FichaState&&window.FichaState.uiMode()==="livre"; }catch(e){ return false; }
 }
 function funcaoSelecionada(){
  var bx=document.getElementById("box"); if(!bx) return null;
  var b=bx.querySelector(".cbfn.cbfnq"); if(!b) return null;
  var i=b.querySelector("i");
  return i?String(i.textContent||"").trim():null;
 }
function nomePadrao(idb, func, rotulo){
 var L=buildsDe(idb), n=1, i;
 for(i=0;i<L.length;i++) if(L[i].func===func) n++;
 return (rotulo||func)+" "+n;
}
function normalizaNomeBuild(nome){
 var limpo=String(nome==null?"":nome).trim().replace(/\s+/g," ");
 try{return limpo.toLocaleLowerCase("pt-BR");}catch(e){return limpo.toLowerCase();}
}
function conflitoNomeBuild(L,nome,ignoraBuildId,ignoraIndice){
 var alvo=normalizaNomeBuild(nome), i, b;
 if(!alvo) return false;
 for(i=0;i<(L||[]).length;i++){
  b=L[i]; if(!b || i===ignoraIndice) continue;
  if(ignoraBuildId && String(b.buildId||"")===String(ignoraBuildId)) continue;
  if(normalizaNomeBuild(b.nome)===alvo) return true;
 }
 return false;
}
function erroNomeBuildDuplicado(){
 return {ok:false,erro:"Já existe uma build com esse nome neste card."};
}
 function rotuloAtualDaFuncao(func){
  /* O texto selecionado na ficha é a autoridade para o nome que o usuário verá. */
  try{
   var bx=document.getElementById("box"), b=bx&&bx.querySelector(".cbfn.cbfnq i");
   var visivel=b&&String(b.textContent||"").trim();
   if(visivel) return visivel;
  }catch(e){}
  try{ if(typeof window.t6NomeFuncao==='function') return window.t6NomeFuncao(func)||func; }catch(e){}
  return func;
 }

 /* Sessão transitória: só existe quando a pessoa entrou pelo botão EDITAR
    das builds salvas. Ela nunca é persistida e, portanto, não interfere no
    fluxo normal de criar uma build nova. */
 function cancelaEdicaoBuild(motivo){
   var ed=window.FichaState&&window.FichaState.editSession();
  if(!ed) return;
   if(window.FichaState){
    window.FichaState.finishEdit();
    if(window.FichaState.showSavedBuild)
     window.FichaState.showSavedBuild({buildId:buildId,cardId:idb,functionId:b.func},String(idb)+'|'+b.func);
   }
  window.BLD_EDICAO_CANCELADA=motivo||"A build em edição não existe mais.";
 }
 function renderBuildPreservandoCampo(){
  var alinhamentoCampo=null;
  try{ alinhamentoCampo=(MT.slots||[]).map(function(sl,i){
   return sl?{i:i,x:sl.x,y:sl.y}:null;
  }); }catch(e){}
  try{ if(typeof mtRender==="function") mtRender(); }catch(e){}
  if(!alinhamentoCampo) return;
  try{
   alinhamentoCampo.forEach(function(p){
    if(!p || !(MT.slots||[])[p.i]) return;
    MT.slots[p.i].x=p.x; MT.slots[p.i].y=p.y;
   });
   var campo=document.querySelector("#mtwrap .mtcampo");
   if(campo) campo.querySelectorAll(".mtsl").forEach(function(vaga){
    var p=alinhamentoCampo[+vaga.getAttribute("data-i")];
    if(!p) return;
    vaga.style.left=Number(p.x).toFixed(2)+"%";
    vaga.style.top=Number(p.y).toFixed(2)+"%";
   });
  }catch(e){}
 }
function salvaEdicaoDaBuild(k,idb,L,ed,nomeForcado){
  var buildId=ed&&ed.buildId, indice=indiceDaBuildId(L,buildId), anterior=L[indice];
  if(!anterior || String(ed.idb)!==String(idb)){
   cancelaEdicaoBuild("A build em edição não existe mais.");
   alert(window.BLD_EDICAO_CANCELADA); delete window.BLD_EDICAO_CANCELADA;
   return false;
  }
  var nomeEditado=String(nomeForcado==null?anterior.nome:nomeForcado).replace(/\s+/g," ").trim()||anterior.nome;
  if(conflitoNomeBuild(L,nomeEditado,buildId,indice)) return erroNomeBuildDuplicado();
  var b=leDaTela(k); if(!b) return false;
  /* A função e o buildId continuam sendo a identidade técnica da entrada.
     O nome pode ser ajustado, desde que permaneça único neste card. */
  b.func=anterior.func; b.nome=nomeEditado; b.tec=null;
  /* A criação normal continua zerando técnico por regra própria. Já uma
     edição precisa fotografar de volta todo insumo que o editor recebeu. */
  var estadoTec=estadoTecnicoDoEditor(k);
  b.tec=estadoTec.tec; b.tecNome=estadoTec.tecNome;
  b.grau=1;
  b.n=notaDaBuild(String(k).split("|")[0]+"|"+b.func,b,false,
                  {bonus:(b.tec||[]).slice(),nome:b.tecNome||null});
  if(substituiBuildPorId(L,buildId,b)<0){
   cancelaEdicaoBuild("A build em edição não existe mais.");
   return false;
  }
   if(window.FichaState)window.FichaState.finishEdit();
  window.BLD_EDICAO_CANCELADA=null;
  window.BLD_SUJO=0; window.EL_SELO=(window.EL_SELO||0)+1;
  try{ if(typeof window.elLimpaCachePontuacao==='function') window.elLimpaCachePontuacao(); }catch(e){}
  try{ userStateSave(); }catch(e){}
  renderBuildPreservandoCampo();
  try{ if(typeof window.t6AtualizaListaBuilds==='function') window.t6AtualizaListaBuilds(idb); }catch(e){}
  barra();
  return true;
 }

 function opcoesDoModalDeBuild(k,edicao){
  var op={edicao:!!edicao},extra=null;
  try{
   if(window.ElencoAddController&&typeof window.ElencoAddController.saveModalOptions==='function')
    extra=window.ElencoAddController.saveModalOptions(k);
  }catch(e){}
  if(extra)Object.keys(extra).forEach(function(ch){op[ch]=extra[ch];});
  return op;
 }

 function salvaBuildDireta(k,func,nomeForcado){
  if(!k) return;if(!func){try{var cf=_card(k);func=cf&&cf.tipo;}catch(e){}}if(!func){try{var cf=_card(k);func=cf&&cf.tipo;}catch(e){}}if(!func){try{var cf=_card(k);func=cf&&cf.tipo;}catch(e){}}if(!func){try{var cf=_card(k);func=cf&&cf.tipo;}catch(e){}}
  if(!func){ alert("Escolha a fun\u00e7\u00e3o l\u00e1 em cima antes de salvar.\n\n"
   +"A build guarda a fun\u00e7\u00e3o junto \u2014 sem ela n\u00e3o d\u00e1 "
   +"pra saber em que posi\u00e7\u00e3o ele joga."); return; }
  var m=bd(); if(!m) return;
  var idb=base(k), L=buildsDe(idb);
  if(window.BLD_EDICAO_CANCELADA){
   alert(window.BLD_EDICAO_CANCELADA); delete window.BLD_EDICAO_CANCELADA;
   return false;
  }
   var ed=window.FichaState&&window.FichaState.editSession();
  if(ed && String(ed.idb)===String(idb)){
   if(nomeForcado===undefined && typeof window.t6PedeNomeBuild==="function"){
    var indiceEd=indiceDaBuildId(L,ed.buildId), buildEd=L[indiceEd];
    if(!buildEd) return false;
    window.t6PedeNomeBuild(buildEd.nome||"",function(v){
     if(v===null) return false;
     return salvaBuildDireta(k,func,v);
     },opcoesDoModalDeBuild(k,true));
    return;
   }
   return salvaEdicaoDaBuild(k,idb,L,ed,nomeForcado);
  }
  if(L.length>=TETO_BUILDS){
   alert("Voc\u00ea j\u00e1 tem "+TETO_BUILDS+" builds guardadas deste card.\n\n"
    +"Apague uma antes de salvar outra \u2014 o x fica na etiqueta dela, "
    +"aqui embaixo."); return;
  }
  var b=leDaTela(k); if(!b) return;
  b.func=func;
  /* A chave da função permanece a do banco; o nome sugerido usa o rótulo atual da ficha. */
  var rotulo=rotuloAtualDaFuncao(func);
  var sug=nomePadrao(idb, func, rotulo);
  if(nomeForcado===undefined && typeof window.t6PedeNomeBuild==="function"){
    window.t6PedeNomeBuild(sug,function(v){
     if(v===null) return false;
     return salvaBuildDireta(k,func,v);
    },opcoesDoModalDeBuild(k,false));
   return;
  }
  var nome=(nomeForcado!==undefined)?nomeForcado:prompt("Nome desta build:", sug);
  if(nome===null) return;
  nome=String(nome).replace(/\s+/g," ").trim() || sug;
  if(conflitoNomeBuild(L,nome,null,-1)) return erroNomeBuildDuplicado();
  /* Técnico é insumo da build criada na Ficha. Salva a mesma fotografia que
     estava visível antes do clique e usa exatamente ela na nota persistida. */
  var estadoTec=estadoTecnicoDoEditor(k);
  b.nome=nome; b.tec=estadoTec.tec; b.tecNome=estadoTec.tecNome;
  b.n=notaDaBuild(String(k).split("|")[0]+"|"+func, b, false,
                  {bonus:(b.tec||[]).slice(),nome:b.tecNome||null});
  b.buildId=novoBuildId(m);
  /* Salvar uma build só muda a build ativa. O mtRender abaixo também passa
     pelo arrumaCampo legado, que tentava redistribuir as vagas e desfazia o
     alinhamento que a pessoa já tinha no gramado. Guarda a geometria atual e
     a repõe depois do render; nota, técnico, função e dados da build seguem
     exatamente pelo fluxo original. */
  var alinhamentoCampo=null;
  try{
   alinhamentoCampo=(MT.slots||[]).map(function(sl,i){
    return sl?{i:i,x:sl.x,y:sl.y}:null;
   });
  }catch(e){}
  m.builds[idb]=L.concat([b]);
  m.buildOn[idb]=m.builds[idb].length-1;
  try{
   if(window.FichaState&&window.FichaState.showSavedBuild)
    window.FichaState.showSavedBuild({buildId:b.buildId,cardId:idb,functionId:b.func},String(idb)+'|'+b.func);
  }catch(e){}
  window.BLD_SUJO=0; window.EL_SELO=(window.EL_SELO||0)+1;
  try{ userStateSave(); }catch(e){}
  try{ if(typeof mtRender==="function") mtRender(); }catch(e){}
  if(alinhamentoCampo){
   try{
    alinhamentoCampo.forEach(function(p){
     if(!p || !(MT.slots||[])[p.i]) return;
     MT.slots[p.i].x=p.x; MT.slots[p.i].y=p.y;
    });
    var campo=document.querySelector("#mtwrap .mtcampo");
    if(campo) campo.querySelectorAll(".mtsl").forEach(function(vaga){
     var p=alinhamentoCampo[+vaga.getAttribute("data-i")];
     if(!p) return;
     vaga.style.left=Number(p.x).toFixed(2)+"%";
     vaga.style.top=Number(p.y).toFixed(2)+"%";
    });
   }catch(e){}
  }
  try{ if(typeof window.t6AtualizaListaBuilds==="function") window.t6AtualizaListaBuilds(idb); }catch(e){}
  barra();
  return true;
 }
window.bldSalvaDireto=function(k,func){return salvaBuildDireta(k,func);};
window.bldSalva=function(){
 var k=chaveAberta(); if(!k) return;
  var ed=window.FichaState&&window.FichaState.editSession();
 return salvaBuildDireta(k,ed&&String(ed.idb)===String(base(k))?ed.func:funcaoSelecionada());
};
window.bldUsa=function(idb, i){
  var m=bd(); if(!m) return;
 m.buildOn[idb]=+i; window.EL_SELO=(window.EL_SELO||0)+1;
 try{ userStateSave(); }catch(e){}
  try{ if(typeof window.t6AtualizaListaBuilds==="function") window.t6AtualizaListaBuilds(idb); }catch(e){}
 var L=buildsDe(idb);
  if(L[+i]){ var k=chaveAberta();
   if(k && base(k)===idb){
     try{if(window.FichaState)window.FichaState.setMode('livre',String(k).split("|")[0]+"|"+L[+i].func);}catch(e){}
     try{if(window.FichaState&&window.FichaState.showSavedBuild)
      window.FichaState.showSavedBuild({buildId:L[+i].buildId,cardId:idb,functionId:L[+i].func},String(idb)+'|'+L[+i].func);}catch(e){}
     aplicaNaTela(String(k).split("|")[0]+"|"+L[+i].func, fotoDaBuild(L[+i]));
  } }
 try{ if(typeof mtRender==="function") mtRender(); }catch(e){}
 barra();
 };
function estadoTecnicoDoEditor(key){
 var c=null, tec=null, tecNome=null;
 try{ c=_card(key); }catch(e){}
 try{ tec=(c&&Array.isArray(c._tec))?c._tec.slice():null; }catch(e){ tec=null; }
 try{ tecNome=(c&&c._tecNome!==undefined)?c._tecNome:null; }catch(e){ tecNome=null; }
 return {tec:tec,tecNome:tecNome};
}
function restauraTecnicoDaBuildNoEditor(key,b){
 var bruto=b&&b.tec, nome=b&&b.tecNome, bonus=null, reg=null;
 function porNome(n){
  try{ return (typeof TECS!=='undefined'?TECS:[]).filter(function(t){ return String(t&&t[0]||'')===String(n||''); })[0]||null; }catch(e){ return null; }
 }
 if(Array.isArray(bruto)) bonus=bruto.slice();
 else if(bruto && typeof bruto==='object'){
  try{ bonus=Array.isArray(bruto.bonus)?bruto.bonus.slice():null; }catch(e){}
  try{ nome=nome||bruto.nome||null; }catch(e){}
 } else if(bruto!==undefined && bruto!==null && bruto!==''){
  if((typeof bruto==='number'||/^\d+$/.test(String(bruto))) && typeof TECS!=='undefined') reg=TECS[+bruto]||null;
  if(reg){ nome=nome||reg[0]||null; bonus=Array.isArray(reg[1])?reg[1].slice():[]; }
  else nome=nome||String(bruto);
 }
 if(!bonus && nome){ reg=porNome(nome); if(reg) bonus=Array.isArray(reg[1])?reg[1].slice():[]; }
 if(!nome && bonus){
  try{ reg=(typeof TECS!=='undefined'?TECS:[]).filter(function(t){ return JSON.stringify(t&&t[1]||[])===JSON.stringify(bonus); })[0]||null; }catch(e){}
  if(reg) nome=reg[0]||null;
 }
 return {tec:Array.isArray(bonus)?bonus:[],tecNome:nome||null};
}
window.bldEdita=function(idb, i, chave){
 var m=bd(), L=buildsDe(idb), buildId=buildIdDaReferencia(L,i), indice=indiceDaBuildId(L,buildId), b=L[indice];
 if(!m || !b) return false;
 var k=chave||chaveAberta();
 if(!k || String(base(k))!==String(idb)) return false;
 /* A fotografia evita que o editor compartilhe arrays/objetos com a build
    persistida antes do clique em salvar. */
 var sessao={idb:String(idb),buildId:buildId,func:b.func,nome:b.nome||("build "+(indice+1))};
 delete window.BLD_EDICAO_CANCELADA;
 var destino=String(idb)+'|'+b.func;
  if(!window.FichaState)return false;
  window.FichaState.startEdit(sessao,destino);
 window.BLD_SUJO=0;
 return aplicaNaTela(destino,fotoDaBuild(b));
};
function selecionaBuildNaVaga(m,indice,k,escolha){
  indice=Number(indice);
  if(!m || !Number.isInteger(indice) || indice<0 || !Array.isArray(m.slots)) return null;
  var sl=m.slots[indice], idb=base(k);
  if(!sl || !sl.key || base(sl.key)!==idb) return null;
  if(escolha==='base'){
   sl.buildId='base'; return {slot:sl,indice:indice,idb:idb,build:null};
  }
  var L=Array.isArray(m.builds&&m.builds[idb])?m.builds[idb]:[];
  var buildId=String(escolha||''), pos=indiceDaBuildId(L,buildId);
  if(pos<0 || !L[pos].func || typeof window.elFuncaoCabeNoSlot!=='function'
     || !window.elFuncaoCabeNoSlot(sl,L[pos].func)) return null;
  sl.buildId=buildId;sl.func=String(L[pos].func);
  return {slot:sl,indice:indice,idb:idb,build:L[pos]};
 }
 window.elSelecionaBuildNaVaga=selecionaBuildNaVaga;
 function selecionaBuildNoElenco(indice,k,escolha){
  var idb=base(k), m=bd(); if(!m) return false;
  if(escolha==='nova'){
   try{ if(typeof window.t6AbreLivreZerado==='function') return window.t6AbreLivreZerado(k); }catch(e){}
   try{ return (window.elAbreCard||abrir)(k); }catch(e2){}
   return false;
  }
  indice=Number(indice);
  var sl=Number.isInteger(indice)&&indice>=0&&Array.isArray(m.slots)?m.slots[indice]:null;
  if(!sl || !sl.key || base(sl.key)!==idb) return false;
  var elemento=null;
  try{ elemento=document.querySelector('#mtwrap .mtsl[data-i="'+indice+'"]'); }catch(e3){}
  /* Sem o DOM exato não há mutação, save nem fallback global. */
  if(!elemento || +elemento.getAttribute('data-i')!==indice) return false;
  var buildAntes=sl.buildId, funcAntes=sl.func, seloAntes=window.EL_SELO||0;
  var mudou=selecionaBuildNaVaga(m,indice,k,escolha);
  if(!mudou) return false;
  try{
   if(typeof window.elFuncaoDaVaga==='function'){
    var fn=window.elFuncaoDaVaga(mudou.slot,k);
    if(fn) mudou.slot.func=fn;
   }
  }catch(e4){}
  window.EL_SELO=seloAntes+1;
  try{
   if(typeof window.elRefazVaga!=='function') throw new Error('desenhista da vaga indisponível');
   /* semSalvar impede um segundo commit interno; o único save vem abaixo. */
   window.elRefazVaga(elemento,true);
  }catch(e6){
   sl.buildId=buildAntes; sl.func=funcAntes; window.EL_SELO=seloAntes;
   return false;
  }
  try{ userStateSave(); }catch(e8){ return false; }
  return true;
 }
 window.elSelecionaBuild=selecionaBuildNoElenco;
 function entradaDaLista(m,colecao,entryId){
  var campo=colecao==='banco'?'banco':(colecao==='fora'?'fora':null);
  if(!m||!campo||!m.listEntries||!Array.isArray(m.listEntries[campo]))return null;
  for(var i=0;i<m.listEntries[campo].length;i++)
   if(String(m.listEntries[campo][i].entryId||'')===String(entryId||''))return m.listEntries[campo][i];
  return null;
 }
 function buildCompativelComEntrada(b,entrada){
  var alvo=chaveFuncaoCanonicaContextual(entrada&&entrada.functionId);
  return alvo!==null && !!b && chaveFuncaoCanonicaContextual(b.func)===alvo;
 }
 window.elBuildCompativelComEntrada=buildCompativelComEntrada;
 function elementoDaEntrada(colecao,entryId){
  var raiz=colecao==='banco'?'#elreservas #elban':'#elfora',lista=[];
  try{lista=[].slice.call(document.querySelectorAll(raiz+' .elcard[data-entry-id]'));}catch(e){return null;}
  for(var i=0;i<lista.length;i++)if(String(lista[i].getAttribute('data-entry-id')||'')===String(entryId||''))return lista[i];
  return null;
 }
 function selecionaBuildNaLista(colecao,entryId,k,escolha){
  var m=bd(),entrada=entradaDaLista(m,colecao,entryId);if(!entrada)return false;
  if(String(entrada.cardKey)!==String(k)||String(entrada.cardId)!==String(base(k)))return false;
  var elemento=elementoDaEntrada(colecao,entryId);if(!elemento)return false;
  if(escolha==='nova'){
   var destino=String(entrada.cardId)+'|'+String(entrada.functionId||'');
   if(!entrada.functionId||typeof window.t6AbreLivreZerado!=='function')return false;
   try{return window.t6AbreLivreZerado(destino)!==false;}catch(e){return false;}
  }
  var buildId=String(escolha||'base');
  if(buildId!=='base'){
   var L=Array.isArray(m.builds&&m.builds[entrada.cardId])?m.builds[entrada.cardId]:[],i=indiceDaBuildId(L,buildId);
   if(i<0||!buildCompativelComEntrada(L[i],entrada))return false;
  }
  if(String(entrada.buildId||'base')===buildId)return true;
  var anterior=entrada.buildId||'base',funcAnterior=entrada.functionId;
  var listaBuilds=Array.isArray(m.builds&&m.builds[entrada.cardId])?m.builds[entrada.cardId]:[];
  var indiceNova=buildId==='base'?-1:indiceDaBuildId(listaBuilds,buildId);
  var buildNova=indiceNova>=0?listaBuilds[indiceNova]:null;
  var funcNova=buildNova&&buildNova.func?String(buildNova.func):entrada.functionId;
  var projetada=Object.assign({},entrada,{buildId:buildId,functionId:funcNova}),html='';
  try{html=montaCard(k,colecao==='banco'?'banco':'fora',null,projetada);}catch(e2){return false;}
  var caixa=null,novo=null;
  try{caixa=document.createElement('div');caixa.innerHTML=html;novo=caixa.firstElementChild;}catch(e3){return false;}
  if(!novo||String(novo.getAttribute('data-entry-id')||'')!==String(entryId))return false;
  entrada.buildId=buildId;entrada.functionId=funcNova;
  try{elemento.replaceWith(novo);}catch(e4){entrada.buildId=anterior;entrada.functionId=funcAnterior;return false;}
  try{userStateSave();}catch(e5){entrada.buildId=anterior;entrada.functionId=funcAnterior;try{novo.replaceWith(elemento);}catch(e6){}return false;}
  try{ligaArrasta();}catch(e7){}
  return true;
 }
 window.elSelecionaBuildLista=selecionaBuildNaLista;

/* O campo nasce com a primeira leva do catálogo. Se alguma função dos seus
   titulares só chegou nas levas seguintes, esta é a única recomposição
   autorizada ao término da carga — nunca um timer, clique sintético ou
   restauração de estado. */
(function(){
 if(window.EL_REAVALIA_DADOS_COMPLETOS_2308) return;
 window.EL_REAVALIA_DADOS_COMPLETOS_2308=1;
 var feita=false;
 function elencoCanonicoVisivel(){
  try{
   var rs=window.RouteState,campo=document.getElementById('mtwrap');
   if(!rs||typeof rs.inspect!=='function'||rs.inspect().atual!=='meutime'||!campo)return false;
   if(campo.style.display==='none')return false;
   if(typeof window.getComputedStyle==='function'&&window.getComputedStyle(campo).display==='none')return false;
   return true;
  }catch(e){return false;}
 }
 function reavalia(){
  /* O evento pode chegar antes de a rota abrir o Elenco. Nesse caso ele
     permanece pendente; concluí-lo cedo exigiria um clique posterior. */
  if(feita || !window.ENC_DADOS_COMPLETOS) return false;
  try{ if(typeof MT_ON==="undefined" || !MT_ON) return false; }catch(e){ return false; }
  if(!elencoCanonicoVisivel()) return false;
  feita=true;
  try{ if(typeof window.elLimpaCachePontuacao==='function') window.elLimpaCachePontuacao(); }catch(e){}
  try{ if(typeof mtRender==="function") mtRender(); }catch(e){}
  return true;
 }
 window.elReavaliaCampoComDadosCompletos=reavalia;
 window.addEventListener('encaixe:dados-completos',reavalia);
 if(window.ENC_DADOS_COMPLETOS) reavalia();
})();
window.bldApaga=function(idb, referencia){
  var m=bd(); if(!m) return;
  var L=buildsDe(idb), buildId=buildIdDaReferencia(L,referencia), indice=indiceDaBuildId(L,buildId); if(indice<0) return;
  if(!confirm("Apagar a build \u201c"+L[indice].nome+"\u201d?")) return false;
  var ativa=m.buildOn[idb], ativaIndice=(ativa==='base'||ativa===undefined||ativa===null)?null:+ativa,
      ed=window.FichaState&&window.FichaState.editSession();
   var removida=removeBuildPorId(L,buildId); if(!removida) return false;
   indice=removida.indice; m.builds[idb]=L;
   /* Uma referência removida falha fechado para Básica apenas nas vagas que
      realmente usavam esta identidade. Nenhuma outra vaga é reindexada. */
   (m.slots||[]).forEach(function(sl){
    if(sl && sl.key && base(sl.key)===String(idb) && sl.buildId===buildId)
     sl.buildId='base';
   });
   ['banco','fora'].forEach(function(campo){
    (((m.listEntries||{})[campo])||[]).forEach(function(e){
     if(e&&String(e.cardId)===String(idb)&&e.buildId===buildId)e.buildId='base';
    });
   });
  /* A Básica é o único fallback sem surpresa: apagar a ativa nunca troca a
     pessoa silenciosamente para outra build personalizada. */
  if(ativaIndice===indice) m.buildOn[idb]='base';
  else if(isFinite(ativaIndice) && ativaIndice>indice) m.buildOn[idb]=ativaIndice-1;
  else if(ativaIndice!==null && (!L[ativaIndice])) m.buildOn[idb]='base';
  if(ed && String(ed.idb)===String(idb)){
   if(String(ed.buildId)===String(buildId)) cancelaEdicaoBuild("A build que estava em edição foi excluída.");
  }
  window.EL_SELO=(window.EL_SELO||0)+1;
  try{ if(typeof window.elLimpaCachePontuacao==='function') window.elLimpaCachePontuacao(); }catch(e){}
  try{ userStateSave(); }catch(e){}
 renderBuildPreservandoCampo();
  try{ if(typeof window.t6AtualizaListaBuilds==="function") window.t6AtualizaListaBuilds(idb); }catch(e){}
  barra();
  return true;
 };
 /* *"poe um outro botaozinho pra ele copiar o que esta no maximo possivel,
    ai ele vai so tirando o que ele nao tem."* */
 window.bldCopiaDoMaximo=function(chaveForcada){
  /* A cópia vem da fotografia oficial da FUNÇÃO aberta, e não do card-base.
     Não passa pelo renderizador histórico: ele desmontava os cliques da
     ficha depois de funções como Falso nove. */
  var k=chaveForcada||chaveAberta(); if(!k) return false;
  var restaura=(typeof window.t6RestauraMotor==='function')
    ? window.t6RestauraMotor : window.restaurarMotor;
  if(typeof restaura!=="function") return false;
  var ok=false;
  window.BLD_SEM_LACO=1;
  try{
   try{ _marca(k); }catch(e){}
   if(restaura(k)===false) return false;
   try{if(window.FichaState)window.FichaState.setMode('livre',k);}catch(e){}
   window._T6_COPIOU_MAX=window._T6_COPIOU_MAX||{};
   try{ window._T6_COPIOU_MAX[base(k)]=1; }catch(e){}
   window.BLD_SUJO=1; ok=true;
  }catch(e){ ok=false; }
  finally{ window.BLD_SEM_LACO=0; }
  if(!ok) return false;
  try{ if(typeof window.t6ReabreFicha==='function') window.t6ReabreFicha(k); else reabrir(k); }catch(e){}
  setTimeout(barra,60);
  return true;
 };

 function barra(){
  var bx=document.getElementById("box"); if(!bx) return;
  var velha=bx.querySelector(".bldbar");
  if(!ehFazerMinha()){ if(velha) velha.remove(); return; }
  var k=chaveAberta(); if(!k){ if(velha) velha.remove(); return; }
  var idb=base(k), L=buildsDe(idb), m=bd();
  var func=funcaoSelecionada();
  var ativa=(m&&m.buildOn[idb]!==undefined)?m.buildOn[idb]:0;
  var h='<button class="bldbt ok" onclick="bldSalva()"'
   +(func?"":" disabled")+'>\u2714 SALVAR MINHA BUILD</button>'
   +'<button class="bldbt" onclick="bldCopiaDoMaximo()" '
   +'title="traz tudo do M\u00c1XIMO POSS\u00cdVEL pra c\u00e1; daqui voc\u00ea '
   +'vai tirando o que n\u00e3o tem">\u29c9 copiar do m\u00e1ximo poss\u00edvel</button>'
   +'<div class=bldtx>'
   +(func?("vai salvar como <b>"+func+"</b> \u00b7 "+L.length+" de "+TETO_BUILDS+" builds")
        :"<b>escolha a fun\u00e7\u00e3o l\u00e1 em cima</b> \u2014 sem ela n\u00e3o d\u00e1 pra salvar")
   +'</div>';
  if(L.length){
   h+='<div class=bldlista>';
   for(var i=0;i<L.length;i++){
    h+='<span class="bldch'+(i===ativa?" on":"")+'" '
     +'onclick="bldUsa(\''+idb+'\','+i+')" '
     +'title="usar esta build no seu elenco">'
     +'<b>'+String(L[i].nome||("build "+(i+1))).replace(/</g,"&lt;")+'</b>'
     +'<u>'+(+L[i].n||0).toFixed(2)+'</u>'
     +'<i onclick="event.stopPropagation();bldApaga(\''+idb+'\','+i+')" '
     +'title="apagar esta build">\u00d7</i></span>';
   }
   h+="</div>";
  }
  if(!velha){
   velha=document.createElement("div"); velha.className="bldbar";
   var alvo=null, hd=bx.querySelectorAll(".bhd"), j;
   for(j=0;j<hd.length;j++) if(/Distribui/i.test(hd[j].textContent)) alvo=hd[j];
   if(alvo && alvo.parentNode) alvo.parentNode.insertBefore(velha, alvo);
   else bx.appendChild(velha);
  }
  if(velha.innerHTML!==h) velha.innerHTML=h;
 }

 /* qualquer mexida na aba FAZER MINHA BUILD marca a carta como suja */
 document.addEventListener("click", function(ev){
  try{
   if(!ehFazerMinha()) return;
   var t=ev.target; if(!t||!t.closest) return;
   if(t.closest(".bldbar")) return;
   if(t.closest('[onclick*="editBar"],[onclick*="setBar"],[onclick*="remHab"],'
    +'.btotbar')) window.BLD_SUJO=1;
  }catch(e){}
 }, true);
 document.addEventListener("change", function(ev){
  try{
   if(!ehFazerMinha()) return;
   var t=ev.target; if(!t||!t.matches) return;
   if(t.matches('select[onchange*="addHab"],select[onchange*="trocaTec"],'
    +'select[onchange*="editImp"]')) window.BLD_SUJO=1;
  }catch(e){}
 }, true);

 /* ---------- 7 · A PONTUACAO DO CARD NO ELENCO ----------
    *"descarta a pontuacao da posicao original. Ele vai aparecer com a
    pontuacao que esta na build dele."* Sem build salva, vale a CARTA
    BASE — *"ele vai vir zerado, como carta base."* */
 var _cache=Object.create(null), _cacheOrdem=[];
 var _melhorCache=Object.create(null), _melhorOrdem=[];
 var _tecnicoCacheSig=null;
 var _cacheStats={scoreHits:0,scoreMisses:0,bestHits:0,bestMisses:0,clears:0};
 var LIMITE_SCORE_CACHE=2048, LIMITE_MELHOR_CACHE=512;
 function cacheTem(obj,k){ return Object.prototype.hasOwnProperty.call(obj,k); }
 function cachePoe(obj,ordem,limite,k,v){
  if(!cacheTem(obj,k)) ordem.push(k);
  obj[k]=v;
  while(ordem.length>limite){ var antiga=ordem.shift(); delete obj[antiga]; }
  return v;
 }
 function assinaturaTecnico(t){
  t=t||{};
  return JSON.stringify([t.id==null?'':String(t.id),String(t.nome||''),
   (t.bonus||[]).slice().map(String).sort()]);
 }
 function assinaturaFotoBuild(b){
  b=b||{};
  var lvl=[], ks=Object.keys(b.lvl||{}).sort();
  for(var i=0;i<ks.length;i++) lvl.push([ks[i],+b.lvl[ks[i]]||0]);
  return JSON.stringify([String(b.buildId||(b.base?'base':'')),String(b.func||''),
   lvl,(b.habs||[]).slice().map(String).sort(),String(b.imp||''),+b.grau||1,b.base?1:0]);
 }
 function chaveFuncaoCanonicaContextual(func){
  if(typeof window.elFuncaoVisivel!=='function'
     || typeof window.elFuncaoCanonica!=='function') return null;
  try{ return window.elFuncaoCanonica(window.elFuncaoVisivel(func)); }
  catch(e){ return null; }
 }
 function chaveFuncaoContextual(func){
  var chave=chaveFuncaoCanonicaContextual(func);
  return (chave===null?'@indisponivel':chave)+'::'+String(func||'');
 }
 function notaContextualComCache(k,idb,b,func,tecnico){
  var tecnicoSig=assinaturaTecnico(tecnico);
  if(_tecnicoCacheSig!==null && _tecnicoCacheSig!==tecnicoSig){
   _cache=Object.create(null); _cacheOrdem=[];
   _melhorCache=Object.create(null); _melhorOrdem=[];
   _cacheStats.clears++;
  }
  _tecnicoCacheSig=tecnicoSig;
  var chave=String(idb)+'|'+chaveFuncaoContextual(func)+'|'
   +tecnicoSig+'|'+assinaturaFotoBuild(b);
  if(cacheTem(_cache,chave)){ _cacheStats.scoreHits++; return _cache[chave]; }
  _cacheStats.scoreMisses++;
  return cachePoe(_cache,_cacheOrdem,LIMITE_SCORE_CACHE,chave,
   calculaNotaBuildFuncao(k,b,func,tecnico));
 }
 function melhorBuildContextual(k,idb,L,funcAtualBruta,chaveAtual,tecnico){
  var candidatas=[], assinaturas=[];
  for(var i=0;i<L.length;i++){
   var b=L[i];
   if(!b || chaveFuncaoCanonicaContextual(b.func)!==chaveAtual) continue;
   /* Registro sem nota histórica válida não é uma build salva confiável. */
   if(!isFinite(Number(b.n)) || !(Number(b.n)>0)) continue;
   candidatas.push({build:b,indice:i});
   assinaturas.push(assinaturaFotoBuild(b));
  }
  var chave=String(idb)+'|'+chaveFuncaoContextual(funcAtualBruta)+'|'
   +assinaturaTecnico(tecnico)+'|'+JSON.stringify(assinaturas);
  if(cacheTem(_melhorCache,chave)){ _cacheStats.bestHits++; return _melhorCache[chave]; }
  _cacheStats.bestMisses++;
  var melhor=null;
  for(var j=0;j<candidatas.length;j++){
   var item=candidatas[j];
   var r=notaContextualComCache(k,idb,item.build,funcAtualBruta,tecnico);
   if(!r || !r.compativel || !isFinite(Number(r.n)) || !(Number(r.n)>0)) continue;
   if(!melhor || Number(r.n)>melhor.n)
    melhor={n:Number(r.n),i:item.indice,buildId:item.build.buildId||null};
  }
  return cachePoe(_melhorCache,_melhorOrdem,LIMITE_MELHOR_CACHE,chave,melhor);
 }
 window.elMelhorBuildContextual=melhorBuildContextual;
 /* Cache exclusivamente derivada, em memória. Dados completos ou troca real
    de técnico limpam todos os grupos; mudanças de fotografia/função geram
    chaves novas sem apagar resultados não relacionados. */
 window.elLimpaCachePontuacao=function(){
  _cache=Object.create(null); _cacheOrdem=[];
  _melhorCache=Object.create(null); _melhorOrdem=[];
  _tecnicoCacheSig=null;
  _cacheStats.clears++;
 };
 window.elCacheContextualStats=function(){
  return {scoreHits:_cacheStats.scoreHits,scoreMisses:_cacheStats.scoreMisses,
   bestHits:_cacheStats.bestHits,bestMisses:_cacheStats.bestMisses,
   clears:_cacheStats.clears,scoreEntries:_cacheOrdem.length,bestEntries:_melhorOrdem.length};
 };
 window.elPontuacao=function(k, funcDaVaga, usarMoldeDaVaga, sl, entrada){
   var c=null; try{ c=mtCard(k); }catch(e){}
   if(!c) return null;
   var idb=base(k), referencia=(usarMoldeDaVaga&&sl)?String(sl.buildId||'base')
    :(entrada?String(entrada.buildId||'base'):'base');
   var b=(usarMoldeDaVaga&&sl)?buildDaVaga(sl,idb)
    :(entrada?buildDaEntrada(entrada,idb):buildAtiva(idb)), nomeB=null;
   if(!b&&referencia!=='base')return {n:0,func:(entrada&&entrada.functionId)||funcDaVaga||c.tipo,
    nome:null,compativel:false,motivo:'build-ausente'};
   var temBuildSalva=!!b;
   if(!b){ b=buildBase(k); }
   else nomeB=b.nome;
  /* Somente uma vaga titular passa `usarMoldeDaVaga=true`. Banco e fora do
     banco continuam fora desta integracao e usam a funcao propria da build. */
   var func=usarMoldeDaVaga
    ?(funcDaVaga||(b&&b.func)||c.tipo)
    :(temBuildSalva?((b&&b.func)||c.tipo)
      :((entrada&&entrada.functionId)||funcDaVaga||(b&&b.func)||c.tipo));
   /* Campo, banco e fora do banco usam a mesma avaliação contextual. A build
      é clonada pelo serviço e só o técnico corrente do time entra no cálculo;
      nenhuma barra, habilidade, ímpeto ou nota histórica é alterada. */
   var r=notaContextualComCache(k,idb,b,func,tecnicoDoTime());
   var out={n:r.n,func:func,nome:nomeB,compativel:r.compativel,motivo:r.motivo};
   return out;
  };

 /* ---------- 8 · o laco ---------- */
 function passo(){
  try{
   var bx=document.getElementById("box");
   var ov=document.getElementById("ov");
   if(!bx || !ov || ov.style.display==="none") return;
   congelaEstiloDaLista();
   barra();
  }catch(e){ if(window.console) console.warn("BUILD_1608:", e); }
 }
 var passoAgendado=false;
 function agendaPasso(){
  if(passoAgendado) return;
  passoAgendado=true;
  requestAnimationFrame(function(){ passoAgendado=false; passo(); });
 }
 ["abrir","reabrir"].forEach(function(nome){
  var anterior=window[nome]; if(typeof anterior!=="function") return;
  window[nome]=function(){ var r=anterior.apply(this,arguments); agendaPasso(); return r; };
 });
 agendaPasso();
})();


/* bloco JavaScript 28 */

/* ===== SELETOR_1608 ===== */
(function(){
 if(window.SELETOR_1608) return; window.SELETOR_1608=1;
 /* Substituído pelo ElencoAddController, instalado ao final deste arquivo.
    Mantemos o bloco abaixo inalcançável apenas até a limpeza medida: nenhum
    listener, wrapper ou requestAnimationFrame legado é montado. */
 return;

 function esc(t){ return String(t==null?"":t)
  .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
  .replace(/"/g,"&quot;"); }
 function enxuga(){
  var bx=document.getElementById("box"); if(!bx) return;
  var lista=bx.querySelector("#mtlist"); if(!lista) return;
  var linhas=[].slice.call(lista.querySelectorAll(".mtli")), i;
  for(i=0;i<linhas.length;i++){
   var li=linhas[i];
   if(li.getAttribute("data-enx")) continue;
   var oc=String(li.getAttribute("onclick")||"");
   var m=oc.match(/[\x27"]([^\x27"]+\|[^\x27"]+)[\x27"]/);
   if(!m){ li.setAttribute("data-enx","1"); continue; }
   var c=null; try{ c=_card(m[1]); }catch(e){}
   if(!c){ li.setAttribute("data-enx","1"); continue; }
   var idb=String(c.id).split("@")[0];
   var est=(c.modelo&&c.modelo!==c.tipo)?c.modelo:"";
   li.innerHTML=
     '<img src="'+esc(window.ClubeNovoReadModel?window.ClubeNovoReadModel.foto(c):'')
     +'" onerror="this.style.visibility=&quot;hidden&quot;">'
    +'<div style="flex:1;min-width:0">'
     +'<b>'+esc(c.nome)+'</b>'
     +'<div class=mini><b style="opacity:.75;letter-spacing:.5px">'
      +esc(c.np||c.pos||"")+'</b> \u00b7 '+esc(c.tipo)+'</div>'
     +(est?('<div class=mini style="opacity:.55">'+esc(est)+'</div>'):"")
    +'</div>';
   li.setAttribute("data-enx","1");
  }
 }

 var VER_TUDO=false;
 function souVaga(){
  try{ return !!(MT_SEL && MT_SEL.slot!==undefined); }catch(e){ return false; }
 }
 function meuElenco(){
  var m={}, s=MT.slots||[], i;
  (MT.banco||[]).forEach(function(k){ m[k]=1; });
  (MT.elenco||[]).forEach(function(k){ m[k]=1; });
  for(i=0;i<s.length;i++) if(s[i]&&s[i].key) m[s[i].key]=1;
  return m;
 }
 function montaListaDoElenco(){
  var bx=document.getElementById("box"); if(!bx) return false;
  var lista=bx.querySelector("#mtlist"); if(!lista) return false;
  var sl=null; try{ sl=MT.slots[MT_SEL.slot]; }catch(e){}
  var mm=meuElenco(), vistos={}, itens=[], k;
  for(k in mm){
   var idb=String(k).split("|")[0].split("@")[0];
   if(vistos[idb]) continue; vistos[idb]=1;
   var c=null; try{ c=_card(k); }catch(e){}
   if(!c) continue;
   var pode=true;
   try{ pode=(typeof window.elJogaNaPos==="function" && sl)
         ? window.elJogaNaPos(c, sl.pos) : true; }catch(e){}
   var n=0;
   try{ var pp=window.elPontuacao(k, sl?sl.func:null); n=pp?pp.n:0; }catch(e){}
   itens.push({k:k, c:c, idb:idb, pode:pode, n:(pode?n:0)});
  }
  itens.sort(function(a,b){
   if(a.pode!==b.pode) return a.pode?-1:1;
   return b.n-a.n;
  });
  var h="", i;
  for(i=0;i<itens.length;i++){
   var it=itens[i], est=(it.c.modelo&&it.c.modelo!==it.c.tipo)?it.c.modelo:"";
   h+='<div class=mtli style="'+(it.pode?"":"opacity:.5")+'" '
    +'onclick="mtPoe(\''+it.k+'\')">'
     +'<img src="'+esc(window.ClubeNovoReadModel?window.ClubeNovoReadModel.foto(it.c):'')
     +'" onerror="this.style.visibility=&quot;hidden&quot;">'
    +'<div style="flex:1;min-width:0"><b>'+esc(it.c.nome)+'</b>'
    +'<div class=mini><b style="opacity:.75;letter-spacing:.5px">'
    +esc(it.c.np||it.c.pos||"")+'</b> \u00b7 '+esc(it.c.tipo)+'</div>'
    +(est?('<div class=mini style="opacity:.55">'+esc(est)+'</div>'):"")
    +'</div>'
    +(it.pode
      ?('<b style="font-size:15px">'+(+it.n).toFixed(2)+'</b>')
      :'<b style="font-size:10px;color:#e0533d;text-align:right;line-height:1.2">'
       +'n\u00e3o joga<br>de '+esc(sl?sl.pos:"")+'</b>')
    +'</div>';
  }
  if(!itens.length)
   h='<div class=mini style="padding:10px 2px">Voc\u00ea ainda n\u00e3o tem '
    +'ningu\u00e9m no elenco. Use o cat\u00e1logo inteiro abaixo.</div>';
  if(lista.getAttribute("data-meu")!==String(itens.length)+"|"+(sl?sl.pos:"")){
   lista.innerHTML=h;
   lista.setAttribute("data-meu",String(itens.length)+"|"+(sl?sl.pos:""));
  }
  return true;
 }
 function soDoElenco(){
  var bx=document.getElementById("box"); if(!bx) return;
  var lista=bx.querySelector("#mtlist"); if(!lista) return;
  if(!souVaga()){ var b0=bx.querySelector(".elsofiltro"); if(b0) b0.remove();
   lista.removeAttribute("data-meu"); return; }
  if(!VER_TUDO){ if(montaListaDoElenco()) { barraDoFiltro(); return; } }
  lista.removeAttribute("data-meu");
  barraDoFiltro();
 }
 function barraDoFiltro(){
  var bx=document.getElementById("box"); if(!bx) return;
  var lista=bx.querySelector("#mtlist"); if(!lista) return;
  var mostrei=[].slice.call(lista.querySelectorAll(".mtli"))
   .filter(function(x){ return x.style.display!=="none"; }).length;
  var barra=bx.querySelector(".elsofiltro");
  if(!barra){
   barra=document.createElement("div"); barra.className="elsofiltro";
   barra.style.cssText="margin:-2px 0 9px;font-size:11.5px;display:flex;"
    +"gap:9px;align-items:center;flex-wrap:wrap";
   lista.parentNode.insertBefore(barra, lista);
  }
  var h = VER_TUDO
   ? ('<b>o cat\u00e1logo inteiro</b> \u2014 '+mostrei+' cartas'
      +'<button class=elbt onclick="elSoMeus()">\u2190 s\u00f3 o meu elenco</button>')
   : ('<b>'+mostrei+' do seu elenco</b> podem jogar aqui'
      +(mostrei?"":' \u2014 nenhum, por enquanto')
      +' <button class=elbt onclick="elVerTudo()">ver o cat\u00e1logo inteiro</button>');
  if(barra.innerHTML!==h) barra.innerHTML=h;
 }
 window.elVerTudo=function(){ VER_TUDO=true; soDoElenco(); };
 window.elSoMeus=function(){ VER_TUDO=false; soDoElenco(); };
 (function(){
  var _ls=window.mtListaSel;
  if(typeof _ls==="function"){
   window.mtListaSel=function(){ var r=_ls.apply(this,arguments);
    agendaLista();
    return r; };
  }
  var _as=window.mtAbreSel;
  if(typeof _as==="function"){
   window.mtAbreSel=function(){ VER_TUDO=false; return _as.apply(this,arguments); };
  }
 })();
 var listaAgendada=false;
 function agendaLista(){
  if(listaAgendada) return;
  listaAgendada=true;
  requestAnimationFrame(function(){
   listaAgendada=false;
   try{ enxuga(); soDoElenco(); }catch(e){}
  });
 }
document.addEventListener("input", agendaLista, true);
})();

/* ===== CONTROLADOR_UNICO_DE_ADICAO_2408 =====
   Uma janela, uma transação e um conjunto de listeners para todas as portas
   de entrada do Elenco. O contexto informa apenas de onde veio a ação. */
(function(){
 if(window.ElencoAddController) return;
 var estado={aberto:false,fase:null,contexto:null,selecionado:null,consulta:'',
  filtroPos:'',itens:[],opcoesSlots:[],pendenteSalvar:null,limite:100,
  transacoes:0,desenhos:0};

 function esc(t){return String(t==null?'':t).replace(/&/g,'&amp;').replace(/</g,'&lt;')
  .replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
 function clone(v){return v==null?v:JSON.parse(JSON.stringify(v));}
 function idCard(k){return String(k||'').split('|')[0].split('@')[0];}
 function funcDaChave(k){return String(k||'').split('|').slice(1).join('|')||null;}
 function sigla(p){return p==='GK'?'GO':(p==='MO'?'MAT':(p==='MC'?'MLG':(p==='PE'?'PTE':(p==='PD'?'PTD':p||''))));}
 function normaliza(t){return String(t||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'')
  .toLowerCase().replace(/\s+/g,' ').trim();}
 function modelo(){try{return typeof MT!=='undefined'?MT:null;}catch(e){return null;}}
 function catalogo(){try{return Array.isArray(D)?D:[];}catch(e){return [];}}
 function registro(k){try{return mtCard(k);}catch(e){return null;}}
 function builds(cardId){var m=modelo();return m&&m.builds&&Array.isArray(m.builds[cardId])?m.builds[cardId]:[];}
 function buildPorId(cardId,buildId){var L=builds(cardId);for(var i=0;i<L.length;i++)
  if(String(L[i]&&L[i].buildId||'')===String(buildId||''))return L[i];return null;}
 function ocorrencias(k){try{return window.ElencoCardInvariant.occurrences(k,modelo())||[];}catch(e){return [];}}
 function jaNoElenco(k){return ocorrencias(k).length>0;}
 function nomeDoSelecionado(){var c=estado.selecionado&&registro(estado.selecionado.key);
  return c&&c.nome?c.nome:'este card';}
 function entradaMeta(grupo,indice){var m=modelo(),L=m&&m.listEntries&&Array.isArray(m.listEntries[grupo])?m.listEntries[grupo]:[];
  return L[indice]||null;}
 function criaEntryId(){var id='';try{if(window.crypto&&window.crypto.randomUUID)id='entry_'+window.crypto.randomUUID().toLowerCase();}catch(e){}
  if(!id)id='entry_runtime_'+Date.now().toString(36)+'_'+Math.random().toString(36).slice(2,10);return id;}
 function fotoEstrutural(){var m=modelo();return m?{slots:clone(m.slots||[]),banco:clone(m.banco||[]),
  elenco:clone(m.elenco||[]),listEntries:clone(m.listEntries||{})}:null;}
 function restauraFoto(f){var m=modelo();if(!m||!f)return;m.slots=f.slots;m.banco=f.banco;m.elenco=f.elenco;m.listEntries=f.listEntries;}
 function garanteMeta(m){m.listEntries=m.listEntries&&typeof m.listEntries==='object'?m.listEntries:{};
  if(!Array.isArray(m.listEntries.banco))m.listEntries.banco=[];
  if(!Array.isArray(m.listEntries.fora))m.listEntries.fora=[];}

 function todasOcorrencias(){var m=modelo(),ids={},out=[],inv=window.ElencoCardInvariant;if(!m||!inv)return out;
  try{if(typeof window.elSincronizaEntradasDasListas==='function')window.elSincronizaEntradasDasListas(m);}catch(e){}
  (m.slots||[]).forEach(function(sl){if(sl&&sl.key)ids[idCard(sl.key)]=sl.key;});
  (m.banco||[]).forEach(function(k){ids[idCard(k)]=k;});(m.elenco||[]).forEach(function(k){ids[idCard(k)]=k;});
  Object.keys(ids).forEach(function(id){var os=inv.occurrences(ids[id],m)||[];
   if(os.length===1){var o=os[0],fn=o.group==='campo'?(o.slot&&o.slot.func):
      (o.entry&&o.entry.functionId)||funcDaChave(o.cardKey);
    o.functionId=fn||funcDaChave(o.cardKey);o.entryId=(o.entry&&o.entry.entryId)||(o.slot&&o.slot.entryId)||null;out.push(o);}
  });return out;}

 function funcoesDaPos(pos){try{return (MT_FUNCS[pos]||[]).slice();}catch(e){return [];}}
 function linhasDoCard(cardId){return catalogo().filter(function(c){return c&&c.id!=='MOLDE'&&idCard(c.id)===idCard(cardId);});}
 function avaliaEmPosicao(sel,sl,pos){
  var fs=funcoesDaPos(pos),candidatos=[];
  if(!fs.length||typeof window.elMesmaFuncaoTecnica!=='function'
     ||typeof window.elJogaNaPos!=='function')return null;
  linhasDoCard(sel.cardId).forEach(function(linha){
   var func=null;
   for(var i=0;i<fs.length;i++)if(window.elMesmaFuncaoTecnica(fs[i],linha.tipo)){func=fs[i];break;}
   if(!func||!window.elJogaNaPos(linha,pos))return;
   var k=String(linha.id)+'|'+linha.tipo,c=registro(k);if(!c)return;
   if(candidatos.some(function(x){return x.key===k&&x.func===func;}))return;
   var probe=Object.assign({},sl,{pos:pos,func:func,key:null,buildId:sel.buildId||'base'}),p=null;
   try{p=window.elPontuacao(k,func,true,probe,sel.entry||null);}catch(e){p=null;}
   candidatos.push({pos:pos,func:func,key:k,score:p&&isFinite(+p.n)?+p.n:0,
    preferida:!!(sel.functionId&&window.elMesmaFuncaoTecnica(sel.functionId,func)),ordem:i});
  });
  candidatos.sort(function(a,b){return (b.preferida?1:0)-(a.preferida?1:0)
   ||b.score-a.score||a.ordem-b.ordem||a.key.localeCompare(b.key);});
  return candidatos[0]||null;
 }
 function melhorNaVaga(sel,sl,filtro){var poss=[];try{poss=window.elOpcoesDaVaga(sl)||[];}catch(e){}
  if(filtro)poss=poss.filter(function(p){return p===filtro;});var melhor=null;
  poss.forEach(function(pos){var a=avaliaEmPosicao(sel,sl,pos);if(a&&(!melhor||a.score>melhor.score))melhor=a;});return melhor;}
 function slotsCompativeis(sel,apenas){var m=modelo(),out=[];(m&&m.slots||[]).forEach(function(sl,i){
  if((apenas!==undefined&&apenas!==null&&i!==+apenas)||!sl||sl.key)return;
  var a=melhorNaVaga(sel,sl,'');if(a)out.push({index:i,slot:sl,pos:a.pos,func:a.func,key:a.key,score:a.score,
   slotToken:window.ElencoOccurrenceTransfer&&window.ElencoOccurrenceTransfer.slotToken
    ?window.ElencoOccurrenceTransfer.slotToken(sl,i):null});
  });return out;}

 function opcaoEstruturalDaVaga(sel,sl,index){if(!sl||sl.key)return null;var key=String(sel&&sel.key
   ||sel&&sel.source&&sel.source.cardKey||''),pos='';
  try{pos=window.elPosicaoEstruturalDaVaga(sl)||'';}catch(e){}if(!key||!pos)return null;
  var func=null;try{func=window.elFuncaoEstruturalDaVaga(sl,key);}catch(e){}func=func||funcDaChave(key);
  var score=0,probe=Object.assign({},sl,{pos:pos,func:func,key:null,buildId:sel&&sel.buildId||'base'}),p=null;
  try{p=window.elPontuacao(key,func,true,probe,sel&&sel.entry||null);}catch(e){}if(p&&isFinite(+p.n))score=+p.n;
  return {index:index,slot:sl,pos:pos,func:func||'',key:key,score:score,
   slotToken:window.ElencoOccurrenceTransfer&&window.ElencoOccurrenceTransfer.slotToken
    ?window.ElencoOccurrenceTransfer.slotToken(sl,index):null};}
 function slotsLivresReserva(sel,apenas){var m=modelo(),out=[];(m&&m.slots||[]).forEach(function(sl,i){
  if(apenas!==undefined&&apenas!==null&&i!==+apenas)return;var o=opcaoEstruturalDaVaga(sel,sl,i);if(o)out.push(o);
  });return out;}

 function candidatoDaOcorrencia(o,sl,filtro){var sel={cardId:o.cardId||idCard(o.cardKey),key:o.cardKey,
   buildId:o.buildId||'base',functionId:o.functionId||funcDaChave(o.cardKey),entry:o.entry||null,source:o};
  var m=modelo(),index=m&&m.slots?(m.slots||[]).indexOf(sl):-1,a=opcaoEstruturalDaVaga(sel,sl,index);if(!a)return null;
  sel.functionId=a.func;sel.targetPos=a.pos;sel.score=a.score;var c=registro(o.cardKey),e=o.entry||{};
  sel.nome=c&&c.nome||e.nome||sel.cardId;sel.modelo=c&&c.modelo||e.modelo||'';return sel;}
 function candidatosDaVaga(){var m=modelo(),ix=+(estado.contexto&&estado.contexto.slotIndex),sl=m&&m.slots&&m.slots[ix];if(!sl||sl.key)return [];
  var q=normaliza(estado.consulta),L=[];todasOcorrencias().forEach(function(o){
   /* Uma vaga titular recebe somente uma ocorrência vinda de Reservas. Fora
      do banco precisa subir um degrau antes; não há atalho escondido no modal. */
   if(o.group!=='banco')return;var x=candidatoDaOcorrencia(o,sl,estado.filtroPos);
   if(!x||q&&normaliza(x.nome).indexOf(q)<0)return;L.push(x);});
  return L.sort(function(a,b){return b.score-a.score;});}
 function resultadosCatalogo(){var q=normaliza(estado.consulta);if(!q)return [];
  var porId={};catalogo().forEach(function(c){if(!c||c.id==='MOLDE'||normaliza(c.nome).indexOf(q)<0)return;
   var id=idCard(c.id),n=0;try{n=+nota(c)||0;}catch(e){}if(!porId[id]||n>porId[id].score)porId[id]={cardId:id,key:String(c.id)+'|'+c.tipo,
    buildId:'base',functionId:c.tipo,nome:c.nome||'',modelo:c.modelo||'',posNativa:c.np||c.pos||'',score:n,
    playerId:window.ElencoCardInvariant&&window.ElencoCardInvariant.playerId?window.ElencoCardInvariant.playerId(id):null,
    presente:jaNoElenco(id)};});
  /* Cada card_id é uma versão distinta, mesmo quando nome/player_id coincidem.
     A ordem visual não usa pontuação e nenhum resultado é cortado aqui. */
  return Object.keys(porId).map(function(id){return porId[id];}).sort(function(a,b){
   var an=normaliza(a.nome),bn=normaliza(b.nome);return an<bn?-1:(an>bn?1:String(a.cardId).localeCompare(String(b.cardId)));});}

 function estilo(){if(document.getElementById('el-add-style'))return;var s=document.createElement('style');s.id='el-add-style';
  s.textContent='body:not(.naelenco) #el-add-fab{display:none!important}#el-add-fab{position:fixed;right:12px;bottom:94px;z-index:9998;width:50px;height:50px;border-radius:15px;border:1px solid var(--d25);background:var(--d25);color:#06200f;font:900 25px/1 system-ui;cursor:pointer;box-shadow:0 10px 28px #0008}#el-add-fab:hover{filter:brightness(1.08)}.eladd-op{width:100%;text-align:left;border:1px solid var(--d31);background:var(--d12);color:var(--d1);border-radius:10px;padding:11px 12px;cursor:pointer}.eladd-op:hover{border-color:var(--d25);background:var(--d14)}.eladd-op:disabled{opacity:.38;cursor:not-allowed;filter:grayscale(.4)}';
  document.head.appendChild(s);}
 function raiz(){return document.getElementById('el-add-modal');}
 function fecha(){var r=raiz();if(r)r.remove();estado.aberto=false;estado.fase=null;estado.contexto=null;estado.selecionado=null;
  estado.consulta='';estado.filtroPos='';estado.itens=[];estado.opcoesSlots=[];return true;}
 function caixaBase(titulo,corpo){return '<div data-el-add-caixa style="width:min(620px,100%);max-height:min(760px,90vh);overflow:auto;background:var(--d4);color:var(--d1);border:1px solid var(--d31);border-radius:15px;padding:18px;box-shadow:0 22px 70px #000a">'
  +'<div style="display:flex;align-items:center;gap:12px;margin-bottom:13px"><strong style="font-size:17px">'+esc(titulo)+'</strong><button type="button" data-el-add="fechar" aria-label="Fechar" style="margin-left:auto;border:0;background:transparent;color:var(--d17);font-size:22px;cursor:pointer">×</button></div>'+corpo+'</div>';}
 function linhaCard(x,i,bloqueado,vaga){var detalhe=vaga?(x.functionId||x.modelo||''):
  [sigla(x.posNativa),x.modelo].filter(Boolean).join(' · ');
  return '<button type="button" class="eladd-op" data-el-add="candidato" data-i="'+i+'"'+(bloqueado?' disabled title="já está no Elenco"':'')+' style="display:flex;align-items:center;gap:11px">'
  +'<img alt="" src="'+esc(window.ClubeNovoReadModel?window.ClubeNovoReadModel.foto(x.cardId):'')+'" style="width:46px;height:61px;object-fit:cover;border-radius:7px" onerror="this.style.visibility=&quot;hidden&quot;">'
  +'<span style="display:flex;flex-direction:column;gap:3px;min-width:0;flex:1"><b>'+esc(x.nome)+'</b><small style="color:var(--d17)">'+esc(detalhe)+'</small></span>'
  +(vaga?'<b style="color:var(--d25);font-size:14px">'+(+x.score||0).toFixed(2)+'</b>':'')+'</button>';}
 function corpoBusca(){var vaga=estado.contexto.origin==='slot',m=modelo(),sl=vaga&&m&&m.slots[+estado.contexto.slotIndex],pos=[];
  if(vaga)estado.filtroPos='';
  estado.itens=vaga?candidatosDaVaga():resultadosCatalogo();
  var filtros=vaga&&pos.length?'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">'
   +[''].concat(pos).map(function(p){var on=estado.filtroPos===p;return '<button type="button" data-el-add="filtro" data-pos="'+esc(p)+'" style="padding:6px 10px;border-radius:8px;border:1px solid '+(on?'var(--d25)':'var(--d31)')+';background:'+(on?'var(--d25)':'var(--d12)')+';color:'+(on?'#06200f':'var(--d30)')+';font-weight:800;cursor:pointer">'+(p?esc(sigla(p)):'TODOS')+'</button>';}).join('')+'</div>':'';
  var vazio=vaga?'Nenhum card disponível nas Reservas.':(estado.consulta?'Nada encontrado.':'Digite o nome do jogador para pesquisar.');
  var visiveis=estado.itens.slice(0,estado.limite),mais=estado.itens.length>visiveis.length;
  return filtros+'<input data-el-add-busca type="search" autocomplete="off" placeholder="buscar pelo nome" value="'+esc(estado.consulta)+'" style="box-sizing:border-box;width:100%;padding:11px 12px;border-radius:9px;border:1px solid var(--d31);background:var(--d5);color:var(--d1);font:inherit;outline-color:var(--d25);margin-bottom:10px">'
   +'<div style="display:flex;flex-direction:column;gap:7px">'+(visiveis.length?visiveis.map(function(x,i){return linhaCard(x,i,!vaga&&x.presente,vaga);}).join(''):'<div style="padding:14px 3px;color:var(--d17);font-size:12px">'+esc(vazio)+'</div>')
   +(mais?'<button type="button" class="eladd-op" data-el-add="mais" style="text-align:center;font-weight:900">MOSTRAR MAIS RESULTADOS</button>':'')+'</div>';}
 function disponibilidade(){var sel=estado.selecionado,m=modelo(),inv=window.ElencoCardInvariant,
   campo=slotsCompativeis(sel),banco=(m&&m.banco||[]).length<12,conflitoCampo=false,conflitoBanco=false;
  if(inv&&typeof inv.planMove==='function'){
   campo=campo.filter(function(o){var p=inv.planMove(sel.key,'campo',o.index);if(!p.ok&&p.playerConflict)conflitoCampo=true;return !!p.ok;});
   if(banco){var pb=inv.planMove(sel.key,'banco',null);if(!pb.ok){conflitoBanco=!!pb.playerConflict;banco=false;}}
  }
  return {campo:campo,banco:banco,fora:true,conflitoCampo:conflitoCampo,conflitoBanco:conflitoBanco};}
 function corpoDestinos(){var d=disponibilidade(),c=registro(estado.selecionado.key),nm=c&&c.nome||nomeDoSelecionado();
  var bSalva=estado.selecionado.buildId!=='base'&&buildPorId(estado.selecionado.cardId,estado.selecionado.buildId);
  var rotBuild=bSalva?'<span style="margin-left:auto;color:var(--d17);font-size:11px">'+esc(bSalva.nome||'build salva')+'</span>':'';
  return '<div style="display:flex;align-items:center;gap:10px;padding:10px;border-radius:10px;background:var(--d12);margin-bottom:12px"><b>'+esc(nm)+'</b>'+rotBuild+'</div>'
   +'<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px">'
   +'<button class="eladd-op" data-el-add="destino" data-destino="campo"'+(d.campo.length?'':' disabled')+'><b>Titular</b><small style="display:block;margin-top:4px;color:var(--d17)">'+(d.campo.length?(d.campo.length+' vaga(s) compatível(is)'):(d.conflitoCampo?'outra versão já está ativa':'sem vaga compatível'))+'</small></button>'
   +'<button class="eladd-op" data-el-add="destino" data-destino="banco"'+(d.banco?'':' disabled')+'><b>Reservas</b><small style="display:block;margin-top:4px;color:var(--d17)">'+(d.banco?'adicionar no final':(d.conflitoBanco?'outra versão já está ativa':'Reservas lotadas'))+'</small></button>'
   +'<button class="eladd-op" data-el-add="destino" data-destino="fora"><b>Fora do banco</b><small style="display:block;margin-top:4px;color:var(--d17)">adicionar no final</small></button></div>';}
  function rotuloDestinoAmigavel(pos){var bruto=String(pos||'').toUpperCase(),
   aliases={GO:'GK',GOL:'GK',MAT:'MO',MLG:'MC',PTE:'PE',PTD:'PD'},p=aliases[bruto]||bruto,
   nomes={GK:'Goleiro',ZC:'Zagueiro',LD:'Lateral direito',LE:'Lateral esquerdo',VOL:'Volante',
    MC:'Meio-campista',MO:'Meia-atacante',MLE:'Meia pela esquerda',MLD:'Meia pela direita',
    SA:'Segundo atacante',CA:'Centroavante',PE:'Ponta esquerda',PD:'Ponta direita'};
   return nomes[p]?(sigla(p)+' — '+nomes[p]):'Posição disponível';}
  function corpoSlots(){var movimento=estado.contexto&&estado.contexto.origin==='movement';
   estado.opcoesSlots=movimento?slotsLivresReserva(estado.selecionado):slotsCompativeis(estado.selecionado);
   var carregando=!estado.opcoesSlots.length&&!window.ENC_DADOS_COMPLETOS;return '<div style="display:flex;flex-direction:column;gap:8px">'
   +(estado.opcoesSlots.length?estado.opcoesSlots.map(function(o,i){return '<button class="eladd-op" data-el-add="slot" data-i="'+i+'" style="display:flex;align-items:center;gap:11px"><span aria-hidden="true" style="color:var(--d25);font-size:18px">↗</span><span style="display:flex;flex-direction:column;gap:3px;min-width:0;flex:1"><b>'+esc(rotuloDestinoAmigavel(o.pos))+'</b><small style="color:var(--d17)">Colocar neste lugar</small></span><b style="margin-left:auto;color:var(--d25);font-size:12px">Selecionar</b></button>';}).join(''):'<div style="color:var(--d17)">'+(carregando?'Carregando vagas do campo…':(movimento?'Nenhuma vaga vazia disponível.':'Nenhuma vaga vazia e compatível.'))+'</div>')+'</div>';}
 function desenha(focar){var r=raiz();if(!r)return;var titulo='Adicionar ao Elenco.',corpo='';
  if(estado.fase==='busca'){titulo=estado.contexto.origin==='slot'?'Escolher jogador para esta vaga.':'Adicionar ao Elenco.';corpo=corpoBusca();}
  else if(estado.fase==='destinos'){titulo='Adicionar ao Elenco.';corpo=corpoDestinos();}
  else{titulo='Escolher vaga titular.';corpo=corpoSlots();}
  r.innerHTML=caixaBase(titulo,corpo);estado.desenhos++;
  if(focar){var q=r.querySelector('[data-el-add-busca]');if(q){q.focus();try{q.setSelectionRange(q.value.length,q.value.length);}catch(e){}}}}

 function removeFonte(plano){var m=modelo(),fonte=plano&&plano.source,meta=null;if(!fonte)return null;garanteMeta(m);
  if(fonte.group==='banco'||fonte.group==='fora'){var ml=m.listEntries[fonte.group];meta=clone(ml[fonte.index]||fonte.entry||{});
   window.ElencoCardInvariant.detach(plano);if(fonte.index>=0&&fonte.index<ml.length)ml.splice(fonte.index,1);}
  else{meta={entryId:fonte.slot&&fonte.slot.entryId||null};window.ElencoCardInvariant.detach(plano);if(fonte.slot)fonte.slot.entryId=null;}
  return meta;}
 function avisaFalhaMovimento(motivo){var mensagens={
  'origem-sem-identidade':'N\u00e3o foi poss\u00edvel confirmar este card nas Reservas. Reabra a sele\u00e7\u00e3o.',
  'origem-alterada':'Este card mudou de lugar. Reabra a sele\u00e7\u00e3o.',
  'vaga-ausente':'Esta vaga n\u00e3o existe mais. Escolha outra vaga.',
  'vaga-ocupada':'Esta vaga foi ocupada. Escolha outra vaga.',
  'vaga-alterada':'Esta vaga mudou desde que a lista foi aberta. Escolha novamente.',
  'posicao-da-vaga-alterada':'A posi\u00e7\u00e3o desta vaga mudou. Escolha novamente.',
  'card-indisponivel':'Os dados deste card n\u00e3o est\u00e3o dispon\u00edveis para concluir o movimento.',
  'card-incompativel':'Este card n\u00e3o serve para a posi\u00e7\u00e3o escolhida.',
  'funcao-invalida':'A compatibilidade desta vaga mudou. Escolha novamente.',
  'build-ausente':'A build aplicada n\u00e3o est\u00e1 mais dispon\u00edvel.'};
  var msg=mensagens[motivo]||'N\u00e3o foi poss\u00edvel concluir o movimento. Reabra a sele\u00e7\u00e3o.';
  try{if(typeof window.t6Notifica==='function'){window.t6Notifica(msg);return false;}}catch(e){}
  try{alert(msg);}catch(e){}return false;
 }
 function confirmaMutacao(destino,opcao){var m=modelo(),sel=estado.selecionado,inv=window.ElencoCardInvariant;if(!m||!sel||!inv)return false;
  var indice=destino==='campo'&&opcao?opcao.index:null,plano=inv.planMove(sel.key,destino,indice);
  if(!plano.ok){if(inv.notifyPlan)inv.notifyPlan(sel.key,plano);else inv.notify(sel.key,true);return false;}
  if(estado.contexto&&(estado.contexto.origin==='movement'
     ||(estado.contexto.origin==='slot'&&plano.source))){
   var tr=window.ElencoOccurrenceTransfer,fonte=sel.source||plano.source;
   if(destino!=='campo'||!opcao||!tr||typeof tr.commitReserveToField!=='function')
    return avisaFalhaMovimento('porta-indisponivel');
   var entryId=sel.entry&&sel.entry.entryId||fonte&&fonte.entry&&fonte.entry.entryId
    ||fonte&&fonte.entryId||null;
   var mov=tr.commitReserveToField({entryId:entryId,
    sourceKey:fonte&&fonte.cardKey||sel.entry&&sel.entry.cardKey||sel.key,
    index:opcao.index,slotToken:opcao.slotToken,pos:opcao.pos,func:opcao.func,cardKey:opcao.key});
   if(!mov||!mov.ok){avisaFalhaMovimento(mov&&mov.motivo);desenha(false);return false;}
   estado.transacoes++;fecha();return true;
  }
  if(estado.contexto.origin!=='slot'&&plano.source){inv.notify(sel.key,false);return false;}
  if(plano.noOp)return true;
  if(destino==='campo'){var sl=m.slots&&m.slots[indice];if(!sl||sl.key)return false;
   var atual=melhorNaVaga(sel,sl,opcao&&opcao.pos||'');if(!atual)return false;opcao=Object.assign({},opcao,atual);}
  if(destino==='banco'&&(m.banco||[]).length>=12)return false;
  var antes=fotoEstrutural();
  try{
   garanteMeta(m);var meta=removeFonte(plano)||{},entryId=meta.entryId||plano.source&&plano.source.entryId||criaEntryId();
   var keyFinal=opcao&&opcao.key?opcao.key:sel.key,funcFinal=opcao&&opcao.func?opcao.func:(sel.functionId||funcDaChave(keyFinal));
   if(destino==='campo'){var alvo=m.slots[indice];alvo.key=keyFinal;alvo.buildId=sel.buildId||plano.buildId||'base';alvo.func=funcFinal;alvo.pos=opcao.pos;alvo.entryId=entryId;}
   else{var campo=destino==='banco'?'banco':'elenco',colecao=destino==='banco'?'banco':'fora';m[campo]=m[campo]||[];m[campo].push(keyFinal);
    meta=Object.assign({},meta,{entryId:entryId,collection:colecao,cardId:sel.cardId,cardKey:keyFinal,
     functionId:funcFinal,buildId:sel.buildId||plano.buildId||'base'});m.listEntries[colecao].push(meta);}
   window.EL_SELO=(window.EL_SELO||0)+1;try{if(window.elLimpaCachePontuacao)window.elLimpaCachePontuacao();}catch(e){}
   userStateSave();mtRender();estado.transacoes++;fecha();atualizaBotaoFicha();
   try{if(window.t6Notifica)window.t6Notifica('Card adicionado ao Elenco.');}catch(e){}return true;
  }catch(e){restauraFoto(antes);try{console.error('[adicionar ao elenco]',e);}catch(_e){}return false;}
 }
 function selecionaCandidato(i){var x=estado.itens[+i];if(!x)return false;if(estado.contexto.origin==='slot'){
   estado.selecionado=x;var m=modelo(),index=+estado.contexto.slotIndex,sl=m&&m.slots&&m.slots[index],a=sl&&opcaoEstruturalDaVaga(x,sl,index);
   return !!(a&&confirmaMutacao('campo',Object.assign({index:+estado.contexto.slotIndex},a)));
  }
  if(x.presente){try{window.ElencoCardInvariant.notify(x.key,false);}catch(e){}return false;}
  estado.selecionado=x;estado.fase='destinos';desenha(false);return true;}
 function escolheDestino(d){if(d==='campo'){estado.fase='slots';desenha(false);return true;}
  return confirmaMutacao(d,null);}

 function instalaEventos(r){r.onclick=function(e){var a=e.target.closest&&e.target.closest('[data-el-add]');
   if(!a){if(e.target===r)fecha();return;}var ac=a.getAttribute('data-el-add');
   if(ac==='fechar'){fecha();return;}if(ac==='filtro'){estado.filtroPos=a.getAttribute('data-pos')||'';desenha(false);return;}
   if(ac==='candidato'){selecionaCandidato(a.getAttribute('data-i'));return;}if(ac==='mais'){estado.limite+=100;desenha(false);return;}if(ac==='destino'){escolheDestino(a.getAttribute('data-destino'));return;}
   if(ac==='slot'){var o=estado.opcoesSlots[+a.getAttribute('data-i')];if(o)confirmaMutacao('campo',o);}};
  r.oninput=function(e){if(!e.target.matches('[data-el-add-busca]'))return;estado.consulta=e.target.value||'';estado.limite=100;desenha(true);};
  r.onkeydown=function(e){if(e.key==='Escape'){e.preventDefault();fecha();}};}
 function abre(contexto){contexto=contexto||{};fecha();var m=modelo();if(!m)return false;
  if(contexto.origin==='slot'){var sl=m.slots&&m.slots[+contexto.slotIndex];if(!sl||sl.key)return false;}
  estilo();var r=document.createElement('div');r.id='el-add-modal';r.setAttribute('role','dialog');r.setAttribute('aria-modal','true');
  r.style.cssText='position:fixed;inset:0;z-index:100002;display:grid;place-items:center;background:rgba(0,0,0,.68);padding:18px';document.body.appendChild(r);instalaEventos(r);
  estado.aberto=true;estado.contexto=contexto;estado.fase=contexto.origin==='movement'?'slots':(contexto.card?'destinos':'busca');estado.selecionado=contexto.card||null;
  estado.consulta='';estado.filtroPos='';estado.limite=100;desenha(estado.fase==='busca'&&contexto.origin!=='slot');return true;}

 function abreMovimentoCampo(k){var tr=window.ElencoOccurrenceTransfer,inv=window.ElencoCardInvariant;
  if(!tr||!inv)return false;try{if(typeof window.elSincronizaEntradasDasListas==='function')
   window.elSincronizaEntradasDasListas(modelo());}catch(e){}
  var os=ocorrencias(k),o=os.length===1?os[0]:null;if(!o||o.group!=='banco')return false;
  var f=tr.snapshot(k);if(!f)return false;var sel={cardId:f.cardId,key:f.cardKey,buildId:f.buildId,
   functionId:f.functionId,entry:Object.assign({},f),source:o};return abre({origin:'movement',card:sel});}

 function selecionadoDaFicha(key){var st=window.FichaState&&window.FichaState.inspect?window.FichaState.inspect():{},cardId=idCard(key),modo=st.modoUI||st.modo||'motor';
  if(modo==='motor')return {cardId:cardId,key:String(key),functionId:funcDaChave(key),buildId:'base'};
  var exibida=window.FichaState&&window.FichaState.displayedBuild?window.FichaState.displayedBuild():null;
  if(exibida&&exibida.buildId&&!window.BLD_SUJO){var b=buildPorId(cardId,exibida.buildId);if(b)return {cardId:cardId,key:cardId+'|'+b.func,functionId:b.func,buildId:b.buildId};}
  return null;}
 function abreDaFicha(key){var cardId=idCard(key),os=ocorrencias(cardId);if(os.length){try{window.ElencoCardInvariant.notify(key,os.length>1);}catch(e){}return false;}
  var sel=selecionadoDaFicha(key);if(sel)return abre({origin:'ficha',card:sel});
  estado.pendenteSalvar={cardId:cardId,key:String(key)};
  try{if(typeof window.bldSalva==='function'){window.bldSalva();return true;}}catch(e){}
  estado.pendenteSalvar=null;return false;}
 function opcoesSalvar(key){var p=estado.pendenteSalvar;if(!p||p.cardId!==idCard(key))return null;
  return {mensagem:'Salve esta build antes de adicionar o card ao Elenco.',
   aoConcluirSucesso:function(){retomaDepoisDeSalvar(key);},aoCancelar:function(){estado.pendenteSalvar=null;}};}
 function retomaDepoisDeSalvar(key){var p=estado.pendenteSalvar;if(!p||p.cardId!==idCard(key))return false;estado.pendenteSalvar=null;
  var sel=selecionadoDaFicha(key);return !!(sel&&abre({origin:'ficha',card:sel}));}
 function cancelaSalvar(){estado.pendenteSalvar=null;return true;}

 function removeDaFicha(key,pedirConfirmacao){var cardId=idCard(key),os=ocorrencias(cardId),o=os.length===1?os[0]:null;
  if(!o){try{window.ElencoCardInvariant.notify(key,os.length>1);}catch(e){}return false;}
  var c=null;try{c=registro(o.cardKey||key);}catch(e){}
  if(pedirConfirmacao!==false&&!confirm('Remover '+((c&&c.nome)||'este card')+' do seu Elenco?\n\nO card será retirado do campo, das Reservas ou de Fora do banco, sem apagar a build salva.'))return false;
  var porta=window.ElencoOccurrenceRemoval,entryId=o.entry&&o.entry.entryId
   ||o.slot&&o.slot.entryId||null;
  if(!porta||typeof porta.commit!=='function')return false;
  var removida=porta.commit({group:o.group,index:o.index,entryId:entryId,
   cardKey:o.cardKey||key});
  if(!removida||!removida.ok){
   try{if(window.t6Notifica)window.t6Notifica('Não foi possível confirmar a ocorrência deste card. Nada foi alterado.');}catch(e){}
   return false;
  }
  atualizaBotaoFicha(null,key);
  try{if(window.t6Notifica)window.t6Notifica('Card removido do Elenco.');}catch(e){}
  return true;}
 function alternaFicha(key){return jaNoElenco(idCard(key))?removeDaFicha(key,true):abreDaFicha(key);}
 function atualizaBotaoFicha(raizFicha,key){var raizLocal=raizFicha||document.getElementById('box'),bt=raizLocal&&raizLocal.querySelector('[data-t6-add-elenco]');
  if(!bt)return false;var dentro=jaNoElenco(idCard(key||bt.getAttribute('data-card-key')));bt.disabled=false;
  bt.setAttribute('data-elenco-estado',dentro?'present':'absent');
  bt.setAttribute('aria-label',dentro?'Remover este card do Elenco':'Adicionar este card ao Elenco');
  bt.textContent=dentro?'✓ NO ELENCO · REMOVER':'＋ ADICIONAR AO ELENCO';
  bt.style.opacity='1';bt.style.cursor='pointer';return true;}
 function montaBotaoFicha(raizFicha,key){if(!raizFicha)return false;var velho=raizFicha.querySelector('[data-t6-add-elenco]');if(velho)velho.remove();
  var buildsBt=raizFicha.querySelector('[data-t6-builds-salvas]');if(!buildsBt||!buildsBt.parentNode)return false;
  var bt=document.createElement('button');bt.type='button';bt.setAttribute('data-t6-add-elenco','1');bt.setAttribute('data-card-key',String(key));
  bt.style.cssText='font-family:inherit;font-size:10px;font-weight:900;letter-spacing:.35px;padding:10px 13px;border-radius:9px;border:1px solid var(--d31);background:var(--d14);color:var(--d25);white-space:nowrap';
  bt.onclick=function(e){e.preventDefault();e.stopPropagation();alternaFicha(key);};buildsBt.parentNode.insertBefore(bt,buildsBt.nextSibling);atualizaBotaoFicha(raizFicha,key);return true;}
 function montaFlutuante(){estilo();var b=document.getElementById('el-add-fab');if(!b){b=document.createElement('button');b.id='el-add-fab';b.type='button';b.textContent='＋';b.title='Adicionar ao Elenco';b.setAttribute('aria-label','Adicionar ao Elenco');
   b.onclick=function(){abre({origin:'general'});};document.body.appendChild(b);}return true;}
 function inspeciona(){return {open:estado.aberto,phase:estado.fase,origin:estado.contexto&&estado.contexto.origin,
  transactions:estado.transacoes,draws:estado.desenhos,pendingSave:!!estado.pendenteSalvar};}

 var api=Object.freeze({open:abre,openMoveToField:abreMovimentoCampo,openFromFicha:abreDaFicha,saveModalOptions:opcoesSalvar,
  resumeAfterSave:retomaDepoisDeSalvar,cancelPendingSave:cancelaSalvar,mountFichaButton:montaBotaoFicha,
   updateFichaButton:atualizaBotaoFicha,toggleFromFicha:alternaFicha,mountLauncher:montaFlutuante,close:fecha,inspect:inspeciona,
  _test:Object.freeze({slotOptions:slotsLivresReserva,compatibleSlotOptions:slotsCompativeis,teamOccurrences:todasOcorrencias,
   candidates:candidatosDaVaga,generalSearch:function(q){estado.consulta=q||'';return resultadosCatalogo();},
    renderLine:linhaCard,renderDestinations:corpoDestinos,removeFromFicha:function(key){return removeDaFicha(key,false);},
   prepare:function(contexto,selecionado){estado.contexto=contexto;estado.selecionado=selecionado;return true;},
   commit:confirmaMutacao})});
 window.ElencoAddController=api;
 /* Compatibilidade sem segundo dono: todo ponto legado termina no controlador. */
 window.mtAbreSel=function(i){return api.open({origin:'slot',slotIndex:+i});};
 window.mtAddBanco=function(){return api.open({origin:'general',preferredDestination:'banco'});};
 window.mtAddElenco=function(){return api.open({origin:'general',preferredDestination:'fora'});};
 window.mtPoeDireto=function(i){return api.open({origin:'slot',slotIndex:+i});};
 window.mtListaSel=function(){return false;};window.mtBusca=function(){return false;};
 window.mtTrocaFunc=function(){return false;};window.mtVaiPara=function(){return false;};window.mtPoe=function(){return false;};
 window.addEventListener('encaixe:dados-completos',function(){
  if(estado.aberto&&estado.fase==='busca'&&estado.contexto&&estado.contexto.origin==='general'&&estado.consulta)
   desenha(true);
  else if(estado.aberto&&estado.fase==='slots'&&estado.contexto
    &&(estado.contexto.origin==='movement'||estado.contexto.origin==='slot'))
   desenha(false);
 });
 montaFlutuante();
})();
