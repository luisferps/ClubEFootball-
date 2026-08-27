/* bloco JavaScript 29 */

/* A CASCA DO TURNO 6 — abas no lugar dos botoes soltos.
   Nada e recriado: o botao velho continua no DOM e a aba chama a MESMA
   funcao dele (homeToggle, mtToggle, boxModo). */
(function(){
  function ver(id){ var e=document.getElementById(id); return !!(e && e.offsetParent!==null); }
  function painel(){try{return window.RouteState?window.RouteState.panel():'inicio';}catch(e){return 'inicio';}}
  /* A ficha e uma pagina de detalhe, nao pertence a nenhuma aba principal.
     Antes ela satisfazia por acidente a regra do Ranking (home e elenco
     escondidos), deixando Ranking marcado mesmo quando vinha de uma box. */
  function emFicha(){
    try{ if(new URLSearchParams(location.search).has('card')) return true; }catch(e){}
    return !!document.querySelector('.pvwrap,.pvcard,[data-pv-ficha],#pvmodal');
  }
  function saiDaFicha(){
    if(!emFicha()) return;
    /* Compatibilidade de boot. Depois de RouteState instalado, ele fecha a
       Ficha antes de chamar este renderizador e esta porta não escreve rota. */
    if(window.RouteState) return;
    try{ if(typeof fechar==='function') fechar(false); }catch(e){}
  }
  var ABAS=[
    {n:'Inicio',   t:'In\u00edcio',
     f:function(){ saiDaFicha(); try{document.documentElement.classList.remove('t6elenco');}catch(e){} window._t6abaBox=false; window._t6cc=false;
                   /* A Home esconde o Elenco, mas não pode deixar o estado do
                      alternador ligado: isso fazia o próximo clique em Elenco
                      desligá-lo em vez de abri-lo. */
                   try{ if(typeof MT_ON!=='undefined' && MT_ON && !ver('mtwrap')) MT_ON=false;
                        if(ver('mtwrap')) mtToggle(); }catch(e){}
                   if(window.t6Painel){ window.t6Painel('inicio'); return; }
                   homeToggle(1); if(window.boxModo) boxModo(0);
                   window.scrollTo(0,0); },
     on:function(){ if(window.T6TELAS) return ver('homewrap') && painel()==='inicio';
                     return ver('homewrap') && !ver('mtwrap')
                      && !window._t6box && !window._t6abaBox && !window._t6cc; }},
    {n:'MeuTime',  t:'Elenco',
     f:function(){ saiDaFicha(); try{ document.documentElement.classList.remove('t6ranking'); document.documentElement.classList.add('t6elenco'); homeToggle(0); var h=document.getElementById('homewrap'),ml=document.getElementById('mline'),sp=document.getElementById('rkspacer'),out=document.getElementById('out');if(h)h.innerHTML='';if(ml){ml.innerHTML='';ml.style.display='none';}if(sp)sp.style.display='none';if(out){out.innerHTML='';out.style.display='none';} }catch(e){}
                   try{ if(typeof MT_ON!=='undefined' && MT_ON && !ver('mtwrap')) MT_ON=false; }catch(e){}
                   if(!ver('mtwrap')) mtToggle();
                   /* O clique abre o Elenco uma única vez. Não há uma segunda
                      renderização atrasada que possa sobrescrever a ação atual. */
                   window.scrollTo(0,0); },
     on:function(){ return ver('mtwrap'); }},
    {n:'Ranking',  t:'Ranking',
     f:function(){ saiDaFicha(); try{document.documentElement.classList.remove('t6elenco');}catch(e){}
                   try{ if(ver('mtwrap')) mtToggle(); else if(typeof MT_ON!=='undefined' && MT_ON) MT_ON=false; }catch(e){}
                   /* Ranking mantém o renderizador visual aprovado ontem. A
                      tela canônica é usada só por Home e Boxes. */
                   homeToggle(0);
                   try{var home=document.getElementById('homewrap');if(home)home.innerHTML='';}catch(e){}
                   try{var ml=document.getElementById('mline'),out=document.getElementById('out');
                       if(ml)ml.style.display='grid'; if(out)out.style.display='block';
                       if(typeof render==='function')render();}catch(e){}
                   window.scrollTo(0,0); },
     on:function(){ return !emFicha() && !ver('homewrap') && !ver('mtwrap'); }},
    {n:'BoxAtual', t:'Boxes atuais',
     f:function(){ saiDaFicha(); try{document.documentElement.classList.remove('t6elenco');}catch(e){} window._t6abaBox=true; window._t6cc=false;
                   if(window.t6Painel){ window.t6Painel('boxatual'); return; }
                   homeToggle(1); if(window.boxModo) boxModo(0);
                   window.scrollTo(0,0); },
     on:function(){ if(window.T6TELAS) return ver('homewrap') && painel()==='boxatual';
                     return ver('homewrap') && !!window._t6abaBox
                      && !window._t6box && !window._t6cc; }},
    {n:'BoxAnt',   t:'Boxes anteriores',
     f:function(){ saiDaFicha(); try{document.documentElement.classList.remove('t6elenco');}catch(e){} window._t6abaBox=false; window._t6cc=false;
                   if(window.t6Painel){ window.t6Painel('boxant'); return; }
                   homeToggle(1); if(window.boxModo) boxModo(1); window.scrollTo(0,0); },
     on:function(){ if(window.T6TELAS) return ver('homewrap') && painel()==='boxant';
                      return ver('homewrap') && !!window._t6box && !window._t6cc; }}
  ];
  /* Esta é a única porta para as páginas principais. Cliques e restauração
     usam a mesma rotina, sem reproduzir eventos de mouse nem criar outra rota. */
  function ativaAba(a,boot){
    if(!a) return false;
    try{var p=a.n==='BoxAtual'?'boxatual':(a.n==='BoxAnt'?'boxant':(a.n==='Inicio'?'inicio':null));if(p&&window.RouteState)window.RouteState.setPanel(p);}catch(e){}
    try{var q=document.getElementById('q'),s=document.getElementById('t6GlobalSuggest');if(q)q.value='';if(s)s.hidden=true;window._t6BuscaGlobal='';}catch(e){}
    try{ a.f(); }catch(e){}
    pinta();
    if(boot){
      /* A restauração direta pode encontrar o Elenco já aberto por uma
         camada anterior. Ainda assim, ele deve passar pela mesma guarda que
         a entrada normal e só aparecer quando as cartas salvas resolverem. */
      try{ if(a.n==='MeuTime' && typeof window.elAguardaCampoCompleto==='function') window.elAguardaCampoCompleto(); }catch(e){}
      requestAnimationFrame(function(){ try{ window.scrollTo(0,0); }catch(e){} });
    }else{
      setTimeout(function(){ window.dispatchEvent(new Event('resize')); },50);
    }
    return true;
  }
  var ROTA_POR_NOME={Inicio:'inicio',MeuTime:'meutime',Ranking:'ranking',BoxAtual:'boxatual',BoxAnt:'boxant'};
  var NOME_POR_ROTA={inicio:'Inicio',meutime:'MeuTime',ranking:'Ranking',boxatual:'BoxAtual',boxant:'BoxAnt'};
  window.t6RenderRota=function(rota,opcoes){
    var nome=NOME_POR_ROTA[rota]||rota;
    for(var i=0;i<ABAS.length;i++) if(ABAS[i].n===nome) return ativaAba(ABAS[i],!!(opcoes&&opcoes.boot));
    return false;
  };
  window.t6NavegaPara=function(nome,opcoes){
    var rota=ROTA_POR_NOME[nome]||nome;
    if(window.RouteState&&typeof window.RouteState.navigate==='function') return window.RouteState.navigate(rota,opcoes||{});
    return window.t6RenderRota(rota,opcoes||{});
  };
  function monta(){
    var h=document.querySelector('header');
    if(!h || document.getElementById('t6bar')) return;
    var bar=document.createElement('div'); bar.id='t6bar';
    var lg=document.createElement('div'); lg.id='t6logo'; lg.setAttribute('aria-label','ClubEfootball'); lg.innerHTML='<span class="t6logo-base">CLUB</span><span class="t6logo-elo">e</span><span class="t6logo-base">FOOTBALL</span>';
    lg.onclick=function(){ window.t6NavegaPara('Inicio'); };
    var nav=document.createElement('div'); nav.id='t6tabs';
    ABAS.forEach(function(a){
      var d=document.createElement('div'); d.className='t6tab'; d.textContent=a.t;
      d.dataset.aba=a.n; d.onclick=function(){ window.t6NavegaPara(a.n); };
      nav.appendChild(d); a.el=d;
    });
    var dir=document.createElement('div'); dir.id='t6dir';
    /* Ordem aprovada do cabeçalho: marca, abas e só então a busca. */
    bar.appendChild(lg);
    bar.appendChild(nav);
    var busca=document.getElementById('qtopo')||document.getElementById('q');
    if(busca) bar.appendChild(busca);
    bar.appendChild(dir);
    h.insertBefore(bar,h.firstChild);
    recolhe();
    /* a casca calcula a altura do cabecalho num --hh; a barra nova mudou essa
       altura DEPOIS do DOMContentLoaded, e sem avisar o conteudo passa por
       baixo dela. O resize e o proprio aviso que a casca ja escuta. */
    setTimeout(function(){ window.dispatchEvent(new Event('resize')); },60);
    /* o titulo velho sai do caminho — os botoes dele continuam ali */
    var h1=h.querySelector('h1');
    if(h1) for(var k=0;k<h1.childNodes.length;k++){
      var n=h1.childNodes[k];
      if(n.nodeType===3 && n.textContent.indexOf('Encaixe')>=0) n.textContent='';
    }
    pinta();
  }
  /* ⛔ 25 · os botoes que viraram aba nao ficam escondidos: saem do DOM.
     Estavam so com display:none, e o documento do design pede que nao existam
     mais. Os outros patches nao dependem deles (dependem de #fbt). */
  function tiraOsVelhos(){
    ['homebt','mtbt'].forEach(function(id){
      var e=document.getElementById(id);
      if(e && e.parentNode) e.parentNode.removeChild(e);
    });
  }
  /* o contador, o tema e o #cnt sobem para a barra assim que existirem —
     eles sao criados por outros patches, em outra hora. E os tres botoes que
     viraram aba somem da fila de baixo: ⌂ inicio, ★ elenco e boxes anteriores. */
  function recolhe(){
    var dir=document.getElementById('t6dir'); if(!dir) return;
    tiraOsVelhos();
    ['contbar','temabt'].forEach(function(id){
      var e=document.getElementById(id);
      if(e && e.parentNode!==dir) dir.appendChild(e);
    });
    /* nao adianta so mexer no style: outro patch reacende esses tres.
       Quem apaga de verdade e o CSS com !important la de cima. */
  }
  function pinta(){
    var rankingLigado=false;
    for(var i=0;i<ABAS.length;i++){
      if(!ABAS[i].el) return;
      var lig=false; try{ lig=!!ABAS[i].on(); }catch(e){}
      ABAS[i].el.className='t6tab'+(lig?' on':'');
      if(ABAS[i].n==='Ranking' && lig) rankingLigado=true;
    }
    /* A coluna de filtros pertence exclusivamente ao Ranking. Ela ficava no
       DOM quando a tela central mudava para Boxes e roubava largura da pagina. */
    var filtros=document.getElementById('filtros');
    if(filtros) filtros.style.display=rankingLigado?'':'none';
    document.documentElement.classList.toggle('t6semlat', !rankingLigado);
    document.documentElement.classList.toggle('t6ranking', rankingLigado);
  }
  function liga(){ monta(); pinta(); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',liga);
  else liga();
  /* A barra é montada por `liga` e as abas são pintadas no próprio clique.
     O antigo relógio de 1,4 s reaplicava estado de navegação sem ação. */
})();


/* bloco JavaScript 31 */

/* O MOTOR DO MOLDE — o minimo para dar vida ao HTML da designer.
   Ela ja entregou o desenho como template: <sc-for list="{{ x }}" as="y"> e
   {{ y.campo }}. Entao aqui nao ha marcacao escrita a mao: so preenchimento. */
(function(){
  var M = {"inicio": {"abre": "<div style=\"width:1280px;border-radius:18px;overflow:hidden;font-family:inherit;color:var(--d1);box-shadow:0 24px 60px var(--d2);background:radial-gradient(1100px 380px at 18% -10%,var(--d3),transparent 62%),linear-gradient(180deg,var(--d4),var(--d5))\">", "header": "<div style=\"display:flex;align-items:center;gap:18px;padding:0 22px;height:56px;background:var(--d6);border-bottom:1px solid var(--d7)\">\n<div style=\"font-weight:700;font-size:14.5px;letter-spacing:.4px;background:linear-gradient(96deg,var(--d1),var(--d8));-webkit-background-clip:text;background-clip:text;color:transparent\">ClubEfootball</div>\n<div style=\"display:flex;gap:3px;background:var(--d9);padding:3px;border-radius:10px;border:1px solid var(--d10)\">\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;background:linear-gradient(180deg,var(--d11),var(--d12));color:var(--d1);font-weight:600\">Início</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Meu time</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Ranking</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Boxes atuais</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Boxes anteriores</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Como calculamos</div>\n</div>\n<div style=\"flex:1;display:flex;align-items:center;gap:9px;background:var(--d14);border:1px solid var(--d15);border-radius:10px;height:34px;padding:0 12px;max-width:300px\">\n<span style=\"color:var(--d16);font-size:13px\">⌕</span>\n<span style=\"font-size:12.5px;color:var(--d16)\">buscar em todos os cards</span>\n</div>\n<div style=\"margin-left:auto;display:flex;align-items:center;gap:12px;font-family:inherit;font-size:11px;color:var(--d17)\">\n<span><b style=\"color:var(--d8)\">12.368</b> linhas</span>\n<span><b style=\"color:var(--d8)\">2.785</b> completos</span>\n<span style=\"padding:5px 10px;border:1px solid var(--d18);border-radius:8px;color:var(--d8)\">◐</span>\n</div>\n</div>", "corpo": "\n\n<div style=\"padding:22px;display:flex;flex-direction:column;gap:26px\">\n\n<div style=\"position:relative;border-radius:18px;overflow:hidden;padding:30px 32px;background:radial-gradient(700px 300px at 88% 20%,var(--d19),transparent 66%),linear-gradient(120deg,var(--d20),var(--d21));border:1px solid var(--d22);display:flex;align-items:center;gap:32px;cursor:pointer;transition:all .2s ease\" style-hover=\"border-color:var(--d23);transform:translateY(-2px)\">\n<div style=\"display:flex;flex-direction:column;gap:13px;max-width:560px\">\n<span style=\"font-family:inherit;font-size:9.5px;letter-spacing:1.8px;color:var(--d8)\">ANTES DE CONTRATAR</span>\n<b style=\"font-size:34px;font-weight:800;letter-spacing:-1px;line-height:1.1\">Quer saber se vale a pena gastar seus pontos?</b>\n<span style=\"font-size:14px;color:var(--d24);line-height:1.5;text-wrap:pretty\">A melhor build de cada card, testada em milhões de combinações por IA. 2.785 cards medidos em 19 funções: você sabe quanto rende antes de gastar GP.</span>\n<span style=\"display:flex;align-items:center;gap:11px;margin-top:5px\">\n<b style=\"font-size:14px;font-weight:700;padding:12px 22px;border-radius:12px;background:linear-gradient(180deg,var(--d25),var(--d26));color:var(--d27);box-shadow:0 8px 24px var(--d28)\">Abrir o elenco →</b>\n<b style=\"font-size:13px;font-weight:600;padding:12px 18px;border-radius:12px;background:var(--d12);border:1px solid var(--d29);color:var(--d30)\">Ver o ranking geral</b>\n</span>\n</div>\n<div style=\"margin-left:auto;display:flex;gap:11px;align-items:flex-end\">\n<span style=\"width:74px;height:98px;border-radius:11px;background:linear-gradient(160deg,var(--d31),var(--d32));border:1px solid var(--d33);display:block\"></span>\n<span style=\"width:88px;height:118px;border-radius:12px;background:linear-gradient(160deg,var(--d34),var(--d35));border:1px solid var(--d36);display:block\"></span>\n<span style=\"width:74px;height:98px;border-radius:11px;background:linear-gradient(160deg,var(--d31),var(--d32));border:1px solid var(--d33);display:block\"></span>\n</div>\n</div>\n\n<div style=\"display:flex;flex-direction:column;gap:13px\">\n<div style=\"display:flex;align-items:baseline;gap:11px\">\n<h2 style=\"margin:0;font-size:19px;font-weight:700;letter-spacing:-.3px\">Lançamentos</h2>\n<span style=\"font-size:12px;color:var(--d13)\">3 de 9 boxes atuais · top 3 de cada uma</span>\n<span style=\"position:relative;width:19px;height:19px;border-radius:50%;border:1px solid var(--d37);display:flex;align-items:center;justify-content:center;font-size:10px;font-style:italic;color:var(--d13);transition:all .18s ease;flex:none\" style-hover=\"border-color:var(--d23);color:var(--d8)\">i\n<b style=\"position:absolute;top:25px;left:0;width:262px;padding:11px 12px;border-radius:11px;background:var(--d38);backdrop-filter:blur(18px);border:1px solid var(--d37);box-shadow:0 14px 34px var(--d39);font-size:11.5px;font-weight:400;font-style:normal;color:var(--d30);line-height:1.5;text-align:left;opacity:0;pointer-events:none;transition:opacity .18s ease;z-index:9\" style-hover=\"opacity:1\">CONTRATAR: 99% ou mais do topo da função. SE SOBRAR: entre 96% e 99%. DEIXA PASSAR: abaixo de 96% — há card melhor pela mesma moeda.</b>\n</span>\n<span style=\"margin-left:auto;font-size:12.5px;font-weight:600;padding:8px 15px;border-radius:10px;border:1px solid var(--d28);background:var(--d40);color:var(--d25);transition:all .18s ease\" style-hover=\"background:var(--d41)\">Todas as boxes atuais →</span>\n</div>\n<div style=\"display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px\">\n<sc-for list=\"{{ boxes }}\" as=\"bx\" hint-placeholder-count=\"3\">\n<div style=\"border-radius:15px;background:linear-gradient(158deg,var(--d42),var(--d43));border:1px solid var(--d20);overflow:hidden;cursor:pointer;transition:transform .2s ease,border-color .2s ease\" style-hover=\"transform:translateY(-3px);border-color:var(--d44)\">\n<div style=\"display:flex;align-items:center;gap:10px;padding:11px 14px;background:var(--d32);border-bottom:1px solid var(--d10)\">\n<b style=\"font-size:12.5px;font-weight:600;line-height:1.25\">{{ bx.n }}</b>\n<em style=\"font-style:normal;font-family:inherit;font-size:10.5px;color:var(--d13);margin-left:auto;white-space:nowrap\">{{ bx.q }}</em>\n</div>\n<div style=\"padding:12px 14px;display:flex;flex-direction:column;gap:10px\">\n<sc-for list=\"{{ bx.cards }}\" as=\"c\" hint-placeholder-count=\"3\">\n<div style=\"display:flex;align-items:center;gap:11px\">\n<span style=\"font-family:inherit;font-size:11px;color:var(--d16);width:16px\">{{ c.r }}</span>\n<span style=\"width:38px;height:50px;border-radius:8px;background:linear-gradient(160deg,var(--d33),var(--d32));border:1px solid var(--d7);flex:none;display:block\"></span>\n<span style=\"display:flex;flex-direction:column;gap:2px;min-width:0;flex:1\">\n<b style=\"font-size:13px;font-weight:600;line-height:1.2\">{{ c.nome }}</b>\n<em style=\"font-style:normal;font-size:10.5px;color:var(--d13);line-height:1.25\">{{ c.est }}</em>\n<em style=\"font-style:normal;display:flex;align-items:baseline;gap:6px\">\n<span style=\"font-size:10.5px;color:var(--d30)\">{{ c.fn }}</span>\n<span style=\"font-family:inherit;font-size:10px;font-weight:700;color:var(--d45)\">{{ c.pos }}</span>\n</em>\n</span>\n<span style=\"display:flex;flex-direction:column;align-items:flex-end;gap:4px\">\n<b style=\"{{ c.pctSt }}\">{{ c.pct }}%</b>\n<em style=\"font-style:normal;font-family:inherit;font-size:10px;color:var(--d13)\">{{ c.pts }} pts</em>\n<em style=\"{{ c.vSt }}\">{{ c.v }}</em>\n</span>\n</div>\n</sc-for>\n</div>\n</div>\n</sc-for>\n</div>\n</div>\n\n<div style=\"display:flex;align-items:center;gap:26px;padding:22px 26px;border-radius:16px;background:radial-gradient(600px 260px at 92% 30%,var(--d46),transparent 64%),linear-gradient(120deg,var(--d10),var(--d47));border:1px solid var(--d48);cursor:pointer;transition:all .2s ease\" style-hover=\"border-color:var(--d49);transform:translateY(-2px)\">\n<div style=\"display:flex;flex-direction:column;gap:9px;max-width:470px\">\n<span style=\"font-family:inherit;font-size:9.5px;letter-spacing:1.8px;color:var(--d50)\">BUILD PRONTA</span>\n<b style=\"font-size:22px;font-weight:800;letter-spacing:-.6px;line-height:1.15\">Você não precisa mais ficar indeciso</b>\n<span style=\"font-size:13px;color:var(--d24);line-height:1.5;text-wrap:pretty\">A melhor build de cada card, testada em milhões de combinações por IA. Barras, ímpeto, técnico e habilidades já resolvidos.</span>\n</div>\n<div style=\"display:flex;gap:10px;margin-left:auto;align-items:center\">\n<div style=\"display:flex;flex-direction:column;gap:3px;padding:12px 15px;border-radius:12px;background:var(--d12);border:1px solid var(--d15)\">\n<span style=\"font-family:inherit;font-size:9px;letter-spacing:1.3px;color:var(--d17)\">SEM O MOTOR</span>\n<b style=\"font-family:inherit;font-size:22px;font-weight:700;color:var(--d13)\">108.41</b>\n</div>\n<span style=\"font-size:19px;color:var(--d50)\">→</span>\n<div style=\"display:flex;flex-direction:column;gap:3px;padding:12px 15px;border-radius:12px;background:linear-gradient(150deg,var(--d51),var(--d52));border:1px solid var(--d53)\">\n<span style=\"font-family:inherit;font-size:9px;letter-spacing:1.3px;color:var(--d50)\">OTIMIZADA</span>\n<b style=\"font-family:inherit;font-size:22px;font-weight:700;background:linear-gradient(180deg,var(--d54),var(--d55));-webkit-background-clip:text;background-clip:text;color:transparent\">112.26</b>\n</div>\n<b style=\"font-size:13px;font-weight:700;padding:12px 20px;border-radius:12px;background:linear-gradient(180deg,var(--d54),var(--d55));color:var(--d56);white-space:nowrap\">⚡ Otimizar meus cards</b>\n</div>\n</div>\n\n<div style=\"display:flex;flex-direction:column;gap:13px\">\n<div style=\"display:flex;align-items:baseline;gap:11px\">\n<h2 style=\"margin:0;font-size:19px;font-weight:700;letter-spacing:-.3px\">Top 3 do jogo</h2>\n<span style=\"font-size:12px;color:var(--d13)\">as três maiores pontuações entre todas as funções</span>\n<span style=\"margin-left:auto;font-size:12.5px;font-weight:600;padding:8px 15px;border-radius:10px;border:1px solid var(--d29);background:var(--d14);color:var(--d30);transition:all .18s ease\" style-hover=\"border-color:var(--d57)\">Ranking geral →</span>\n</div>\n<div style=\"display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px\">\n<sc-for list=\"{{ top3Jogo }}\" as=\"t\" hint-placeholder-count=\"3\">\n<div style=\"display:flex;gap:16px;padding:18px;border-radius:16px;background:linear-gradient(158deg,var(--d20),var(--d58));border:1px solid var(--d59);cursor:pointer;transition:all .2s ease\" style-hover=\"transform:translateY(-3px);border-color:var(--d57)\">\n<span style=\"{{ t.medSt }}\"></span>\n<span style=\"display:flex;flex-direction:column;gap:5px;min-width:0;flex:1\">\n<em style=\"{{ t.rSt }}\">{{ t.r }}</em>\n<b style=\"font-size:18px;font-weight:800;letter-spacing:-.4px;line-height:1.15\">{{ t.nome }}</b>\n<em style=\"font-style:normal;font-family:inherit;font-size:9px;letter-spacing:1.1px;font-weight:700;color:var(--d30);line-height:1.3\">{{ t.fn }}</em>\n<em style=\"font-style:normal;font-size:11.5px;color:var(--d13)\">{{ t.est }}</em>\n<em style=\"font-style:normal;display:flex;align-items:baseline;gap:8px;margin-top:auto\">\n<b style=\"font-family:inherit;font-size:29px;font-weight:700;line-height:1;letter-spacing:-.8px;color:var(--d25)\">{{ t.ptsInt }}<i style=\"font-style:normal;font-size:17px\">{{ t.ptsDec }}</i></b>\n<span style=\"font-family:inherit;font-size:9.5px;font-weight:700;color:var(--d45);padding:2px 6px;border-radius:5px;background:var(--d60);border:1px solid var(--d61)\">{{ t.pos }}</span>\n</em>\n<em style=\"font-style:normal;font-size:10.5px;color:var(--d16)\">{{ t.box }}</em>\n</span>\n</div>\n</sc-for>\n</div>\n</div>\n\n<div style=\"display:flex;flex-direction:column;gap:15px\">\n<div style=\"display:flex;align-items:baseline;gap:11px\">\n<h2 style=\"margin:0;font-size:19px;font-weight:700;letter-spacing:-.3px\">Top 3 de cada função</h2>\n<span style=\"font-size:12px;color:var(--d13)\">19 funções · clique para abrir o ranking da função</span>\n</div>\n<sc-for list=\"{{ topFns }}\" as=\"s\" hint-placeholder-count=\"4\">\n<div style=\"display:flex;flex-direction:column;gap:11px\">\n<div style=\"font-family:inherit;font-size:9.5px;letter-spacing:1.6px;color:var(--d62)\">{{ s.s }}</div>\n<div style=\"display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px\">\n<sc-for list=\"{{ s.fns }}\" as=\"fn\" hint-placeholder-count=\"4\">\n<div style=\"border-radius:15px;padding:14px 16px;background:linear-gradient(158deg,var(--d42),var(--d43));border:1px solid var(--d20);display:flex;flex-direction:column;gap:11px;cursor:pointer;transition:all .2s ease\" style-hover=\"border-color:var(--d63);transform:translateY(-2px)\">\n<div style=\"display:flex;align-items:baseline;gap:9px\">\n<b style=\"font-size:14px;font-weight:700\">{{ fn.n }}</b>\n<em style=\"font-style:normal;font-family:inherit;font-size:11px;font-weight:700;color:var(--d45)\">{{ fn.sig }}</em>\n<em style=\"font-style:normal;font-size:11px;color:var(--d16);margin-left:auto\">ranking →</em>\n</div>\n<div style=\"display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px\">\n<sc-for list=\"{{ fn.podio }}\" as=\"p\" hint-placeholder-count=\"3\">\n<div style=\"display:flex;flex-direction:column;gap:7px;min-width:0\">\n<span style=\"display:flex;align-items:flex-start;gap:8px\">\n<span style=\"{{ p.medSt }}\"></span>\n<em style=\"{{ p.rSt }}\">{{ p.r }}</em>\n</span>\n<span style=\"display:flex;flex-direction:column;gap:1px;min-width:0\">\n<b style=\"font-size:12px;font-weight:600;line-height:1.25\">{{ p.nome }}</b>\n<b style=\"{{ p.ptsSt }}\">{{ p.pts }}</b>\n<b style=\"{{ p.pctSt }}\">{{ p.pct }}%</b>\n</span>\n</div>\n</sc-for>\n</div>\n</div>\n</sc-for>\n</div>\n</div>\n</sc-for>\n</div>\n\n</div>\n"}, "meutime": {"abre": "<div style=\"width:1280px;border-radius:18px;overflow:hidden;font-family:inherit;color:var(--d1);box-shadow:0 24px 60px var(--d2);background:radial-gradient(1100px 380px at 18% -10%,var(--d3),transparent 62%),linear-gradient(180deg,var(--d4),var(--d5))\">", "header": "<div style=\"display:flex;align-items:center;gap:18px;padding:0 22px;height:56px;background:var(--d6);border-bottom:1px solid var(--d7)\">\n<div style=\"font-weight:700;font-size:14.5px;letter-spacing:.4px;background:linear-gradient(96deg,var(--d1),var(--d8));-webkit-background-clip:text;background-clip:text;color:transparent\">ClubEfootball</div>\n<div style=\"display:flex;gap:3px;background:var(--d9);padding:3px;border-radius:10px;border:1px solid var(--d10)\">\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Início</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;background:linear-gradient(180deg,var(--d11),var(--d12));color:var(--d1);font-weight:600\">Meu time</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Ranking</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Boxes atuais</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Boxes anteriores</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Como calculamos</div>\n</div>\n<div style=\"flex:1;display:flex;align-items:center;gap:9px;background:var(--d14);border:1px solid var(--d15);border-radius:10px;height:34px;padding:0 12px;max-width:300px\">\n<span style=\"color:var(--d16);font-size:13px\">⌕</span>\n<span style=\"font-size:12.5px;color:var(--d16)\">buscar em todos os cards</span>\n</div>\n<div style=\"margin-left:auto;display:flex;align-items:center;gap:12px;font-family:inherit;font-size:11px;color:var(--d17)\">\n<span style=\"padding:5px 10px;border:1px solid var(--d18);border-radius:8px;color:var(--d30)\">↓ salvar arquivo</span>\n<span style=\"padding:5px 10px;border:1px solid var(--d18);border-radius:8px;color:var(--d30)\">↑ carregar</span>\n<span style=\"padding:5px 10px;border:1px solid var(--d18);border-radius:8px;color:var(--d8)\">◐</span>\n</div>\n</div>", "corpo": "\n\n<div style=\"display:flex;align-items:center;gap:20px;padding:18px 22px;border-bottom:1px solid var(--d10);background:var(--d64)\">\n<div style=\"display:flex;flex-direction:column;gap:3px\">\n<span style=\"font-family:inherit;font-size:9px;letter-spacing:1.4px;color:var(--d17)\">ELENCO</span>\n<div style=\"display:flex;align-items:center;gap:8px\">\n<b style=\"font-size:24px;font-weight:800;letter-spacing:-.5px\">Meu time</b>\n<span style=\"position:relative;width:19px;height:19px;border-radius:50%;border:1px solid var(--d37);display:flex;align-items:center;justify-content:center;font-size:10px;font-style:italic;color:var(--d13);transition:all .18s ease;flex:none\" style-hover=\"border-color:var(--d23);color:var(--d8)\">i\n<b style=\"position:absolute;top:25px;left:0;width:210px;padding:11px 12px;border-radius:11px;background:var(--d38);backdrop-filter:blur(18px);border:1px solid var(--d37);box-shadow:0 14px 34px var(--d39);font-size:11.5px;font-weight:400;font-style:normal;color:var(--d30);line-height:1.5;text-align:left;opacity:0;pointer-events:none;transition:opacity .18s ease;z-index:9\" style-hover=\"opacity:1\">Clique no nome para renomear o time. Ele fica salvo neste navegador — entre na sua conta para levá-lo entre aparelhos.</b>\n</span>\n</div>\n</div>\n<div style=\"margin-left:auto;display:flex;gap:11px\">\n<div style=\"min-width:104px;display:flex;flex-direction:column;gap:4px;padding:11px 14px;border-radius:12px;background:var(--d12);border:1px solid var(--d20)\">\n<span style=\"font-family:inherit;font-size:9px;letter-spacing:1.3px;color:var(--d17)\">FORMAÇÃO</span>\n<b style=\"font-family:inherit;font-size:20px;font-weight:700\">5-3-2</b>\n</div>\n<div style=\"min-width:104px;display:flex;flex-direction:column;gap:4px;padding:11px 14px;border-radius:12px;background:var(--d12);border:1px solid var(--d20)\">\n<span style=\"font-family:inherit;font-size:9px;letter-spacing:1.3px;color:var(--d17)\">EM CAMPO</span>\n<b style=\"font-family:inherit;font-size:20px;font-weight:700\">10/11</b>\n</div>\n<div style=\"min-width:126px;display:flex;flex-direction:column;gap:4px;padding:11px 14px;border-radius:12px;background:linear-gradient(150deg,var(--d51),var(--d52));border:1px solid var(--d65)\">\n<span style=\"font-family:inherit;font-size:9px;letter-spacing:1.3px;color:var(--d50)\">PONTUAÇÃO MÉDIA</span>\n<b style=\"font-family:inherit;font-size:20px;font-weight:700;background:linear-gradient(180deg,var(--d54),var(--d55));-webkit-background-clip:text;background-clip:text;color:transparent\">110.87</b>\n</div>\n<div style=\"min-width:150px;display:flex;flex-direction:column;gap:4px;padding:11px 14px;border-radius:12px;background:var(--d12);border:1px solid var(--d20)\">\n<span style=\"font-family:inherit;font-size:9px;letter-spacing:1.3px;color:var(--d17)\">TÉCNICO</span>\n<b style=\"font-size:15px;font-weight:700\">Pep Guardiola</b>\n</div>\n</div>\n</div>\n\n<div style=\"display:flex;flex-wrap:wrap;gap:8px;padding:14px 22px;border-bottom:1px solid var(--d10)\">\n<sc-for list=\"{{ acoes }}\" as=\"ac\" hint-placeholder-count=\"6\">\n<span style=\"{{ ac.st }}\">{{ ac.n }}</span>\n</sc-for>\n<span style=\"margin-left:auto;display:flex;align-items:center;gap:8px;font-size:11.5px;color:var(--d66)\">\n<span>jogador modelo do tipo · pontuação <b style=\"color:var(--d30)\">106.4</b></span>\n<span style=\"position:relative;width:19px;height:19px;border-radius:50%;border:1px solid var(--d37);display:flex;align-items:center;justify-content:center;font-size:10px;font-style:italic;color:var(--d13);transition:all .18s ease\" style-hover=\"border-color:var(--d23);color:var(--d8)\">i\n<b style=\"position:absolute;top:25px;right:0;width:250px;padding:11px 12px;border-radius:11px;background:var(--d38);backdrop-filter:blur(18px);border:1px solid var(--d37);box-shadow:0 14px 34px var(--d39);font-size:11.5px;font-weight:400;font-style:normal;color:var(--d30);line-height:1.5;text-align:left;opacity:0;pointer-events:none;transition:opacity .18s ease;z-index:9\" style-hover=\"opacity:1\">Mediana dos cards que evoluem. Atributos 106.4 · Habilidades 95 · Físico 81.9 · Player Skills 0. Quem está acima supera o modelo.</b>\n</span>\n</span>\n</div>\n\n<div style=\"display:grid;grid-template-columns:404px minmax(0,1fr);gap:0\">\n<div style=\"border-right:1px solid var(--d10);padding:18px;display:flex;flex-direction:column;gap:16px\">\n<div style=\"display:flex;align-items:center;gap:12px;padding:13px 15px;border-radius:13px;background:linear-gradient(158deg,var(--d20),var(--d58));border:1px solid var(--d59)\">\n<div style=\"display:flex;flex-direction:column;gap:2px\">\n<span style=\"font-family:inherit;font-size:9px;letter-spacing:1.3px;color:var(--d17)\">FORMAÇÃO</span>\n<b style=\"font-family:inherit;font-size:22px;font-weight:700\">5-3-2</b>\n</div>\n<div style=\"margin-left:auto;display:flex;align-items:flex-end;gap:3px\">\n<i style=\"width:5px;height:20px;border-radius:2px;background:var(--d67);display:block\"></i>\n<i style=\"width:5px;height:15px;border-radius:2px;background:var(--d57);display:block\"></i>\n<i style=\"width:5px;height:25px;border-radius:2px;background:var(--d68);display:block\"></i>\n</div>\n<span style=\"font-size:11px;color:var(--d66)\">trocar ▾</span>\n</div>\n\n<div style=\"display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:13px;background:var(--d9);border:1px solid var(--d20)\">\n<span style=\"width:38px;height:38px;border-radius:50%;background:linear-gradient(160deg,var(--d29),var(--d14));border:1px solid var(--d33);display:block;flex:none\"></span>\n<span style=\"display:flex;flex-direction:column;gap:1px;min-width:0\">\n<em style=\"font-style:normal;font-family:inherit;font-size:9px;letter-spacing:1.3px;color:var(--d17)\">TÉCNICO</em>\n<b style=\"font-size:13.5px;font-weight:700\">Pep Guardiola</b>\n</span>\n<span style=\"margin-left:auto;color:var(--d16)\">▾</span>\n</div>\n\n<div style=\"display:flex;flex-direction:column;gap:9px\">\n<div style=\"display:flex;align-items:baseline;gap:8px\">\n<span style=\"font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d17)\">RESERVAS</span>\n<span style=\"font-family:inherit;font-size:10.5px;color:var(--d66)\">5 de 12</span>\n</div>\n<div style=\"display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;padding:9px;border-radius:12px;border:1px dashed var(--d31);background:var(--d64)\">\n<sc-for list=\"{{ reservas }}\" as=\"rv\" hint-placeholder-count=\"5\">\n<div style=\"position:relative;display:flex;flex-direction:column;gap:7px;padding:10px;border-radius:11px;background:var(--d12);border:1px solid var(--d7);cursor:grab;transition:all .18s ease\" style-hover=\"background:var(--d69);border-color:var(--d28)\">\n<span style=\"position:absolute;top:9px;right:10px;width:17px;height:17px;border-radius:5px;background:var(--d10);border:1px solid var(--d18);display:flex;align-items:center;justify-content:center;font-size:10px;color:var(--d13);transition:all .18s ease\" style-hover=\"color:var(--d1);border-color:var(--d70)\">×</span>\n<span style=\"display:flex;align-items:baseline;gap:7px\">\n<b style=\"font-family:inherit;font-size:19px;font-weight:700;line-height:1;letter-spacing:-.5px;color:var(--d25)\">{{ rv.ptsInt }}<i style=\"font-style:normal;font-size:12px\">{{ rv.ptsDec }}</i></b>\n<em style=\"font-style:normal;font-family:inherit;font-size:9px;font-weight:700;color:var(--d45);padding:1px 5px;border-radius:5px;background:var(--d60);border:1px solid var(--d61)\">{{ rv.pos }}</em>\n</span>\n<span style=\"display:flex;align-items:flex-start;gap:9px\">\n<span style=\"width:30px;height:40px;border-radius:7px;background:linear-gradient(160deg,var(--d29),var(--d32));border:1px solid var(--d7);flex:none;display:block\"></span>\n<span style=\"display:flex;flex-direction:column;gap:2px;min-width:0;flex:1\">\n<b style=\"font-size:11.5px;font-weight:700;line-height:1.2\">{{ rv.nome }}</b>\n<em style=\"font-style:normal;font-family:inherit;font-size:8.5px;letter-spacing:1px;font-weight:700;color:var(--d30);line-height:1.3\">{{ rv.FN }}</em>\n<em style=\"font-style:normal;font-size:10px;color:var(--d13);line-height:1.2\">{{ rv.est }}</em>\n</span>\n</span>\n<span style=\"display:grid;grid-template-columns:1fr 1fr;gap:5px\">\n<i style=\"font-style:normal;text-align:center;font-size:10.5px;font-weight:600;padding:5px 0;border-radius:7px;background:var(--d12);border:1px solid var(--d18);color:var(--d30);transition:all .18s ease\" style-hover=\"border-color:var(--d71);color:var(--d25)\">↑ campo</i>\n<i style=\"font-style:normal;text-align:center;font-size:10.5px;font-weight:600;padding:5px 0;border-radius:7px;background:var(--d12);border:1px solid var(--d18);color:var(--d30);transition:all .18s ease\" style-hover=\"border-color:var(--d71);color:var(--d25)\">↓ fora</i>\n</span>\n</div>\n</sc-for>\n<div style=\"grid-column:1/-1;display:flex;align-items:center;justify-content:center;gap:8px;padding:4px 0 1px\">\n<span style=\"font-size:11.5px;color:var(--d30);padding:6px 12px;border-radius:9px;background:var(--d14);border:1px solid var(--d18);transition:all .18s ease\" style-hover=\"border-color:var(--d57)\">+ adicionar reserva</span>\n<span style=\"position:relative;width:19px;height:19px;border-radius:50%;border:1px solid var(--d37);display:flex;align-items:center;justify-content:center;font-size:10px;font-style:italic;color:var(--d13);transition:all .18s ease;flex:none\" style-hover=\"border-color:var(--d23);color:var(--d8)\">i\n<b style=\"position:absolute;bottom:25px;left:0;width:200px;padding:11px 12px;border-radius:11px;background:var(--d38);backdrop-filter:blur(18px);border:1px solid var(--d37);box-shadow:0 14px 34px var(--d39);font-size:11.5px;font-weight:400;font-style:normal;color:var(--d30);line-height:1.5;text-align:left;opacity:0;pointer-events:none;transition:opacity .18s ease;z-index:9\" style-hover=\"opacity:1\">Arraste um card de \"fora do banco\" para cá, ou use o botão para escolher da lista.</b>\n</span>\n</div>\n</div>\n</div>\n</div>\n\n<div style=\"padding:18px 22px;display:flex;justify-content:center\">\n<div style=\"display:flex;flex-direction:column;gap:12px\">\n<div style=\"display:flex;align-items:baseline;gap:9px\">\n<span style=\"font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d17)\">CAMPO</span>\n<span style=\"position:relative;width:19px;height:19px;border-radius:50%;border:1px solid var(--d37);display:flex;align-items:center;justify-content:center;font-size:10px;font-style:italic;color:var(--d13);transition:all .18s ease;flex:none\" style-hover=\"border-color:var(--d23);color:var(--d8)\">i\n<b style=\"position:absolute;top:25px;left:0;width:250px;padding:11px 12px;border-radius:11px;background:var(--d38);backdrop-filter:blur(18px);border:1px solid var(--d37);box-shadow:0 14px 34px var(--d39);font-size:11.5px;font-weight:400;font-style:normal;color:var(--d30);line-height:1.5;text-align:left;opacity:0;pointer-events:none;transition:opacity .18s ease;z-index:9\" style-hover=\"opacity:1\">Arraste o card de uma vaga para outra para trocar. Ligue \"mover posições\" e arraste a alça ✥ para reposicionar a vaga no gramado.</b>\n</span>\n<span style=\"margin-left:auto;display:flex;gap:7px\">\n<span style=\"font-size:11.5px;color:var(--d30);padding:6px 12px;border-radius:9px;background:var(--d14);border:1px solid var(--d18);transition:all .18s ease\" style-hover=\"border-color:var(--d57)\">✥ mover posições</span>\n<span style=\"font-size:11.5px;color:var(--d72);padding:6px 12px;border-radius:9px;background:var(--d32);border:1px solid var(--d73);transition:all .18s ease\" style-hover=\"border-color:var(--d74)\">limpar</span>\n</span>\n</div>\n<div style=\"position:relative;width:660px;height:990px;border-radius:16px;overflow:hidden;background:repeating-linear-gradient(180deg,var(--d75) 0 82px,var(--d76) 82px 164px)\">\n<div style=\"position:absolute;inset:14px;border:2px solid var(--d77);border-radius:4px\"></div>\n<div style=\"position:absolute;left:14px;right:14px;top:50%;height:2px;background:var(--d77)\"></div>\n<div style=\"position:absolute;left:50%;top:50%;width:172px;height:172px;margin:-86px 0 0 -86px;border:2px solid var(--d77);border-radius:50%\"></div>\n<div style=\"position:absolute;left:50%;top:50%;width:8px;height:8px;margin:-4px 0 0 -4px;border-radius:50%;background:var(--d78)\"></div>\n<div style=\"position:absolute;left:50%;top:14px;width:340px;height:128px;margin-left:-170px;border:2px solid var(--d77);border-top:none;border-radius:0 0 5px 5px\"></div>\n<div style=\"position:absolute;left:50%;top:14px;width:158px;height:52px;margin-left:-79px;border:2px solid var(--d79);border-top:none;border-radius:0 0 4px 4px\"></div>\n<div style=\"position:absolute;left:50%;bottom:14px;width:340px;height:128px;margin-left:-170px;border:2px solid var(--d77);border-bottom:none;border-radius:5px 5px 0 0\"></div>\n<div style=\"position:absolute;left:50%;bottom:14px;width:158px;height:52px;margin-left:-79px;border:2px solid var(--d79);border-bottom:none;border-radius:4px 4px 0 0\"></div>\n<sc-for list=\"{{ XI }}\" as=\"s\" hint-placeholder-count=\"11\">\n<div style=\"{{ s.wrap }}\">\n<sc-if value=\"{{ s.vaga }}\" hint-placeholder-val=\"{{ false }}\">\n<div style=\"width:100%;height:100%;box-sizing:border-box;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;padding:8px;border-radius:13px;border:1.5px dashed var(--d78);background:var(--d80);transition:all .18s ease\" style-hover=\"border-color:var(--d25);background:var(--d3)\">\n<span style=\"display:flex;align-items:center;gap:3px;font-family:inherit;font-size:11px;font-weight:700;color:var(--d81);padding:2px 7px;border-radius:6px;background:var(--d18);cursor:pointer\">{{ s.pos }} <i style=\"font-style:normal;font-size:8px;opacity:.7\">▾</i></span>\n<span style=\"font-size:26px;font-weight:300;line-height:.8;color:var(--d81)\">+</span>\n<span style=\"font-size:10.5px;color:var(--d82);text-align:center;line-height:1.2\">vaga aberta</span>\n</div>\n</sc-if>\n<sc-if value=\"{{ s.nome }}\" hint-placeholder-val=\"{{ true }}\">\n<div style=\"position:relative;width:100%;height:100%;box-sizing:border-box;display:flex;flex-direction:column;align-items:center;gap:3px;padding:8px 6px 10px;border-radius:13px;background:var(--d83);backdrop-filter:blur(10px);border:1px solid var(--d37);box-shadow:0 8px 22px var(--d84);cursor:grab;transition:all .18s ease\" style-hover=\"border-color:var(--d25);transform:translateY(-2px)\">\n<span style=\"position:absolute;top:6px;left:7px;width:17px;height:17px;border-radius:6px;background:var(--d15);border:1px solid var(--d31);display:flex;align-items:center;justify-content:center;font-size:8.5px;color:var(--d85);cursor:grab\" title=\"mover esta vaga\">✥</span>\n<span style=\"position:absolute;top:6px;right:7px;display:flex;align-items:center;gap:2px;font-family:inherit;font-size:9px;font-weight:700;color:var(--d45);padding:2px 5px;border-radius:5px;background:var(--d86);border:1px solid var(--d87);cursor:pointer\">{{ s.pos }} <i style=\"font-style:normal;font-size:7px;opacity:.7\">▾</i></span>\n<span style=\"width:30px;height:30px;border-radius:8px;background:linear-gradient(160deg,var(--d37),var(--d12));flex:none;display:block;margin-top:14px\"></span>\n<b style=\"font-size:10.5px;font-weight:700;line-height:1.12;text-align:center;width:100%\">{{ s.nome }}</b>\n<em style=\"font-style:normal;font-family:inherit;font-size:7.5px;letter-spacing:.6px;font-weight:700;color:var(--d30);line-height:1.12;text-align:center;width:100%\">{{ s.FN }}</em>\n<em style=\"font-style:normal;font-size:8px;color:var(--d85);line-height:1.12;text-align:center;width:100%\">{{ s.est }}</em>\n<b style=\"font-family:inherit;font-size:14px;font-weight:700;color:var(--d25);margin-top:auto\">{{ s.pts }}</b>\n</div>\n</sc-if>\n</div>\n</sc-for>\n</div>\n</div>\n\n</div>\n</div>\n<div style=\"padding:0 22px 20px\">\n<div style=\"display:flex;flex-direction:column;gap:11px\">\n<div style=\"display:flex;align-items:baseline;gap:9px;flex-wrap:wrap\">\n<span style=\"font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d17)\">FORA DO BANCO</span>\n<span style=\"font-family:inherit;font-size:10.5px;color:var(--d66)\">8 cards</span>\n<span style=\"display:flex;gap:6px;flex-wrap:wrap;width:100%;margin-top:2px\">\n<span style=\"display:flex;align-items:center;gap:7px;font-size:11.5px;color:var(--d16);padding:6px 11px;border-radius:9px;background:var(--d14);border:1px solid var(--d15);flex:1;min-width:150px\">⌕ buscar pelo nome</span>\n<span style=\"font-size:11.5px;color:var(--d30);padding:6px 11px;border-radius:9px;background:var(--d32);border:1px solid var(--d18)\">maior pontuação ▾</span>\n<span style=\"font-size:11.5px;color:var(--d30);padding:6px 11px;border-radius:9px;background:var(--d32);border:1px solid var(--d18)\">todos os setores ▾</span>\n<span style=\"font-size:11.5px;color:var(--d30);padding:6px 11px;border-radius:9px;background:var(--d32);border:1px solid var(--d18)\">todas as posições ▾</span>\n<span style=\"font-size:11.5px;color:var(--d30);padding:6px 11px;border-radius:9px;background:var(--d14);border:1px solid var(--d18);transition:all .18s ease\" style-hover=\"border-color:var(--d57)\">+ adicionar card</span>\n</span>\n</div>\n<div style=\"display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px\">\n<sc-for list=\"{{ fora }}\" as=\"fc\" hint-placeholder-count=\"8\">\n<div style=\"position:relative;display:flex;flex-direction:column;gap:9px;padding:13px;border-radius:14px;background:linear-gradient(158deg,var(--d42),var(--d43));border:1px solid var(--d20);cursor:grab;transition:all .18s ease\" style-hover=\"transform:translateY(-3px);border-color:var(--d57)\">\n<span style=\"position:absolute;top:11px;right:12px;width:19px;height:19px;border-radius:6px;background:var(--d10);border:1px solid var(--d18);display:flex;align-items:center;justify-content:center;font-size:11px;color:var(--d13);transition:all .18s ease\" style-hover=\"color:var(--d1);border-color:var(--d70)\">×</span>\n<span style=\"display:flex;align-items:baseline;gap:8px\">\n<b style=\"font-family:inherit;font-size:25px;font-weight:700;line-height:1;letter-spacing:-.6px;color:var(--d25)\">{{ fc.ptsInt }}<i style=\"font-style:normal;font-size:15px\">{{ fc.ptsDec }}</i></b>\n<em style=\"font-style:normal;font-family:inherit;font-size:9.5px;font-weight:700;color:var(--d45);padding:2px 6px;border-radius:5px;background:var(--d60);border:1px solid var(--d61)\">{{ fc.pos }}</em>\n</span>\n<span style=\"display:flex;align-items:flex-start;gap:10px\">\n<span style=\"width:44px;height:58px;border-radius:8px;background:linear-gradient(160deg,var(--d29),var(--d32));border:1px solid var(--d7);flex:none;display:block\"></span>\n<span style=\"display:flex;flex-direction:column;gap:3px;min-width:0;flex:1\">\n<b style=\"font-size:13px;font-weight:700;line-height:1.2\">{{ fc.nome }}</b>\n<em style=\"font-style:normal;font-family:inherit;font-size:9px;letter-spacing:1.1px;font-weight:700;color:var(--d30);line-height:1.3\">{{ fc.FN }}</em>\n<em style=\"font-style:normal;font-size:10.5px;color:var(--d13);line-height:1.25\">{{ fc.est }}</em>\n</span>\n</span>\n<span style=\"display:grid;grid-template-columns:1fr 1fr;gap:6px\">\n<i style=\"font-style:normal;text-align:center;font-size:11px;font-weight:600;padding:6px 0;border-radius:8px;background:var(--d12);border:1px solid var(--d18);color:var(--d30);transition:all .18s ease\" style-hover=\"border-color:var(--d71);color:var(--d25)\">↓ reserva</i>\n<i style=\"font-style:normal;text-align:center;font-size:11px;font-weight:600;padding:6px 0;border-radius:8px;background:var(--d12);border:1px solid var(--d18);color:var(--d30);transition:all .18s ease\" style-hover=\"border-color:var(--d71);color:var(--d25)\">↑ campo</i>\n</span>\n</div>\n</sc-for>\n</div>\n</div>\n</div>\n"}, "boxes": {"abre": "<div style=\"width:1280px;border-radius:18px;overflow:hidden;font-family:inherit;color:var(--d1);box-shadow:0 24px 60px var(--d2);background:radial-gradient(1100px 380px at 18% -10%,var(--d3),transparent 62%),linear-gradient(180deg,var(--d4),var(--d5))\">", "header": "<div style=\"display:flex;align-items:center;gap:18px;padding:0 22px;height:56px;background:var(--d6);border-bottom:1px solid var(--d7)\">\n<div style=\"font-weight:700;font-size:14.5px;letter-spacing:.4px;background:linear-gradient(96deg,var(--d1),var(--d8));-webkit-background-clip:text;background-clip:text;color:transparent\">ClubEfootball</div>\n<div style=\"display:flex;gap:3px;background:var(--d9);padding:3px;border-radius:10px;border:1px solid var(--d10)\">\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Início</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Meu time</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Ranking</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Boxes atuais</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;background:linear-gradient(180deg,var(--d11),var(--d12));color:var(--d1);font-weight:600\">Boxes anteriores</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Como calculamos</div>\n</div>\n<div style=\"flex:1;display:flex;align-items:center;gap:9px;background:var(--d14);border:1px solid var(--d15);border-radius:10px;height:34px;padding:0 12px;max-width:300px\">\n<span style=\"color:var(--d16);font-size:13px\">⌕</span>\n<span style=\"font-size:12.5px;color:var(--d16)\">buscar box ou card</span>\n</div>\n<div style=\"margin-left:auto;display:flex;align-items:center;gap:12px;font-family:inherit;font-size:11px;color:var(--d17)\">\n<span><b style=\"color:var(--d8)\">12.368</b> linhas</span>\n<span style=\"padding:5px 10px;border:1px solid var(--d18);border-radius:8px;color:var(--d8)\">◐</span>\n</div>\n</div>", "corpo": "\n\n<div style=\"padding:22px;display:flex;flex-direction:column;gap:15px\">\n<div style=\"display:flex;align-items:baseline;gap:11px\">\n<h2 style=\"margin:0;font-size:19px;font-weight:700;letter-spacing:-.3px\">Boxes anteriores</h2>\n<span style=\"font-size:12px;color:var(--d13)\">72 boxes encerradas · top 3 de cada uma · mostrando as 6 mais recentes</span>\n<span style=\"margin-left:auto;display:flex;gap:7px\">\n<span style=\"font-size:12px;padding:6px 12px;border-radius:9px;border:1px solid var(--d18);background:var(--d32);color:var(--d30)\">mais recentes ▾</span>\n<span style=\"font-size:12px;padding:6px 12px;border-radius:9px;border:1px solid var(--d18);background:var(--d32);color:var(--d30)\">todas as funções ▾</span>\n<span style=\"font-size:12px;padding:6px 12px;border-radius:9px;background:linear-gradient(180deg,var(--d25),var(--d26));color:var(--d27);font-weight:600\">voltar aos lançamentos</span>\n</span>\n</div>\n<div style=\"display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px\">\n<sc-for list=\"{{ boxesAnt }}\" as=\"bx\" hint-placeholder-count=\"6\">\n<div style=\"border-radius:15px;background:linear-gradient(158deg,var(--d42),var(--d43));border:1px solid var(--d20);overflow:hidden;transition:transform .2s ease,border-color .2s ease\" style-hover=\"transform:translateY(-3px);border-color:var(--d44)\">\n<div style=\"display:flex;align-items:center;gap:10px;padding:11px 14px;background:var(--d32);border-bottom:1px solid var(--d10)\">\n<b style=\"font-size:12.5px;font-weight:600;line-height:1.25\">{{ bx.n }}</b>\n<em style=\"font-style:normal;font-family:inherit;font-size:10.5px;color:var(--d13);margin-left:auto;white-space:nowrap\">{{ bx.q }}</em>\n</div>\n<div style=\"padding:12px 14px;display:flex;flex-direction:column;gap:10px\">\n<sc-for list=\"{{ bx.cards }}\" as=\"c\" hint-placeholder-count=\"3\">\n<div style=\"display:flex;align-items:center;gap:11px\">\n<span style=\"font-family:inherit;font-size:11px;color:var(--d16);width:16px\">{{ c.r }}</span>\n<span style=\"width:38px;height:50px;border-radius:8px;background:linear-gradient(160deg,var(--d33),var(--d32));border:1px solid var(--d7);flex:none;display:block\"></span>\n<span style=\"display:flex;flex-direction:column;gap:2px;min-width:0;flex:1\">\n<b style=\"font-size:13px;font-weight:600;line-height:1.2\">{{ c.nome }}</b>\n<em style=\"font-style:normal;font-size:10.5px;color:var(--d13);line-height:1.25\">{{ c.est }}</em>\n<em style=\"font-style:normal;display:flex;align-items:baseline;gap:6px\">\n<span style=\"font-size:10.5px;color:var(--d30)\">{{ c.fn }}</span>\n<span style=\"font-family:inherit;font-size:10px;font-weight:700;color:var(--d45)\">{{ c.pos }}</span>\n</em>\n</span>\n<span style=\"display:flex;flex-direction:column;align-items:flex-end;gap:3px\">\n<b style=\"{{ c.pctSt }}\">{{ c.pct }}%</b>\n<em style=\"font-style:normal;font-family:inherit;font-size:10px;color:var(--d13)\">{{ c.pts }} pts</em>\n</span>\n</div>\n</sc-for>\n</div>\n</div>\n</sc-for>\n</div>\n</div>\n"}, "como": {"abre": "<div style=\"width:1280px;border-radius:18px;overflow:hidden;font-family:inherit;color:var(--d1);box-shadow:0 24px 60px var(--d2);background:radial-gradient(1100px 380px at 18% -10%,var(--d3),transparent 62%),linear-gradient(180deg,var(--d4),var(--d5))\">", "header": "<div style=\"display:flex;align-items:center;gap:18px;padding:0 22px;height:56px;background:var(--d6);border-bottom:1px solid var(--d7)\">\n<div style=\"font-weight:700;font-size:14.5px;letter-spacing:.4px;background:linear-gradient(96deg,var(--d1),var(--d8));-webkit-background-clip:text;background-clip:text;color:transparent\">ClubEfootball</div>\n<div style=\"display:flex;gap:3px;background:var(--d9);padding:3px;border-radius:10px;border:1px solid var(--d10)\">\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Início</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Meu time</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Ranking</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Boxes atuais</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Boxes anteriores</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;background:linear-gradient(180deg,var(--d11),var(--d12));color:var(--d1);font-weight:600\">Como calculamos</div>\n</div>\n<div style=\"flex:1;display:flex;align-items:center;gap:9px;background:var(--d14);border:1px solid var(--d15);border-radius:10px;height:34px;padding:0 12px;max-width:300px\">\n<span style=\"color:var(--d16);font-size:13px\">⌕</span>\n<span style=\"font-size:12.5px;color:var(--d16)\">buscar em todos os cards</span>\n</div>\n<div style=\"margin-left:auto;display:flex;align-items:center;gap:12px;font-family:inherit;font-size:11px;color:var(--d17)\">\n<span><b style=\"color:var(--d8)\">12.368</b> linhas</span>\n<span><b style=\"color:var(--d8)\">2.785</b> completos</span>\n<span style=\"padding:5px 10px;border:1px solid var(--d18);border-radius:8px;color:var(--d8)\">◐</span>\n</div>\n</div>", "corpo": "\n\n<div style=\"padding:26px 22px;display:flex;flex-direction:column;gap:26px\">\n\n<div style=\"display:flex;align-items:flex-end;gap:30px\">\n<div style=\"display:flex;flex-direction:column;gap:10px;max-width:620px\">\n<span style=\"font-family:inherit;font-size:9.5px;letter-spacing:1.8px;color:var(--d8)\">METODOLOGIA</span>\n<b style=\"font-size:30px;font-weight:800;letter-spacing:-.9px;line-height:1.12\">A nota não é opinião, é medição</b>\n<span style=\"font-size:13.5px;color:var(--d24);line-height:1.55;text-wrap:pretty\">Cada card recebe uma nota por função. A nota compara o card com o molde daquela função — o que a elite dela realmente tem — e não com um ideal inventado.</span>\n</div>\n<div style=\"margin-left:auto;display:flex;gap:11px\">\n<div style=\"min-width:112px;display:flex;flex-direction:column;gap:4px;padding:13px 16px;border-radius:13px;background:var(--d12);border:1px solid var(--d15)\">\n<span style=\"font-family:inherit;font-size:9px;letter-spacing:1.3px;color:var(--d17)\">CARDS MEDIDOS</span>\n<b style=\"font-family:inherit;font-size:21px;font-weight:700\">2.785</b>\n</div>\n<div style=\"min-width:112px;display:flex;flex-direction:column;gap:4px;padding:13px 16px;border-radius:13px;background:var(--d12);border:1px solid var(--d15)\">\n<span style=\"font-family:inherit;font-size:9px;letter-spacing:1.3px;color:var(--d17)\">FUNÇÕES</span>\n<b style=\"font-family:inherit;font-size:21px;font-weight:700\">19</b>\n</div>\n<div style=\"min-width:132px;display:flex;flex-direction:column;gap:4px;padding:13px 16px;border-radius:13px;background:linear-gradient(150deg,var(--d51),var(--d52));border:1px solid var(--d65)\">\n<span style=\"font-family:inherit;font-size:9px;letter-spacing:1.3px;color:var(--d50)\">COMBINAÇÕES TESTADAS</span>\n<b style=\"font-family:inherit;font-size:21px;font-weight:700;background:linear-gradient(180deg,var(--d54),var(--d55));-webkit-background-clip:text;background-clip:text;color:transparent\">1.4 bi</b>\n</div>\n</div>\n</div>\n\n<div style=\"display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px\">\n<div style=\"display:flex;flex-direction:column;gap:9px;padding:17px 18px;border-radius:15px;background:linear-gradient(158deg,var(--d10),var(--d47));border:1px solid var(--d15)\">\n<span style=\"font-family:inherit;font-size:22px;font-weight:700;color:var(--d25);line-height:1\">01</span>\n<b style=\"font-size:15px;font-weight:700\">O molde da função</b>\n<span style=\"font-size:12.5px;color:var(--d24);line-height:1.5;text-wrap:pretty\">Reunimos os cards que a comunidade usa naquela função e medimos o que eles têm de fato. Sai um alvo por atributo — o retrato da elite da função.</span>\n</div>\n<div style=\"display:flex;flex-direction:column;gap:9px;padding:17px 18px;border-radius:15px;background:linear-gradient(158deg,var(--d10),var(--d47));border:1px solid var(--d15)\">\n<span style=\"font-family:inherit;font-size:22px;font-weight:700;color:var(--d25);line-height:1\">02</span>\n<b style=\"font-size:15px;font-weight:700\">O peso de cada atributo</b>\n<span style=\"font-size:12.5px;color:var(--d24);line-height:1.5;text-wrap:pretty\">O alvo define o peso. Atributo que a elite tem alto pesa muito; o que ela não usa pesa zero. Nada de peso escolhido no chute.</span>\n</div>\n<div style=\"display:flex;flex-direction:column;gap:9px;padding:17px 18px;border-radius:15px;background:linear-gradient(158deg,var(--d10),var(--d47));border:1px solid var(--d15)\">\n<span style=\"font-family:inherit;font-size:22px;font-weight:700;color:var(--d25);line-height:1\">03</span>\n<b style=\"font-size:15px;font-weight:700\">A régua da nota</b>\n<span style=\"font-size:12.5px;color:var(--d24);line-height:1.5;text-wrap:pretty\">Cada atributo do card é comparado ao alvo em nove degraus. Ficar acima rende bônus, ficar abaixo do piso é punido — não existe compensar defeito com sobra.</span>\n</div>\n<div style=\"display:flex;flex-direction:column;gap:9px;padding:17px 18px;border-radius:15px;background:linear-gradient(158deg,var(--d88),var(--d89));border:1px solid var(--d90)\">\n<span style=\"font-family:inherit;font-size:22px;font-weight:700;color:var(--d55);line-height:1\">04</span>\n<b style=\"font-size:15px;font-weight:700\">O motor da build</b>\n<span style=\"font-size:12.5px;color:var(--d24);line-height:1.5;text-wrap:pretty\">Com a nota pronta, varremos as combinações de barras, ímpeto, técnico e habilidades e devolvemos a que dá a maior nota naquela função.</span>\n</div>\n</div>\n\n<div style=\"display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:14px\">\n<div style=\"display:flex;flex-direction:column;gap:13px;padding:19px 20px;border-radius:16px;background:linear-gradient(158deg,var(--d42),var(--d43));border:1px solid var(--d20)\">\n<div style=\"display:flex;align-items:baseline;gap:10px\">\n<b style=\"font-size:15px;font-weight:700\">O que entra na nota</b>\n<span style=\"font-family:inherit;font-size:10.5px;color:var(--d13);margin-left:auto\">peso na função Ala finalizador</span>\n</div>\n<div style=\"display:flex;flex-direction:column;gap:8px\">\n<div style=\"display:flex;align-items:center;gap:12px\">\n<span style=\"font-size:12.5px;width:132px;flex:none\">Atributos</span>\n<span style=\"flex:1;height:9px;border-radius:5px;background:var(--d10);overflow:hidden;display:block\"><i style=\"display:block;height:100%;width:62%;border-radius:5px;background:linear-gradient(90deg,var(--d26),var(--d25))\"></i></span>\n<b style=\"font-family:inherit;font-size:12.5px;width:44px;text-align:right\">62%</b>\n</div>\n<div style=\"display:flex;align-items:center;gap:12px\">\n<span style=\"font-size:12.5px;width:132px;flex:none\">Habilidades</span>\n<span style=\"flex:1;height:9px;border-radius:5px;background:var(--d10);overflow:hidden;display:block\"><i style=\"display:block;height:100%;width:21%;border-radius:5px;background:linear-gradient(90deg,var(--d26),var(--d25))\"></i></span>\n<b style=\"font-family:inherit;font-size:12.5px;width:44px;text-align:right\">21%</b>\n</div>\n<div style=\"display:flex;align-items:center;gap:12px\">\n<span style=\"font-size:12.5px;width:132px;flex:none\">Físico e pé</span>\n<span style=\"flex:1;height:9px;border-radius:5px;background:var(--d10);overflow:hidden;display:block\"><i style=\"display:block;height:100%;width:11%;border-radius:5px;background:linear-gradient(90deg,var(--d26),var(--d25))\"></i></span>\n<b style=\"font-family:inherit;font-size:12.5px;width:44px;text-align:right\">11%</b>\n</div>\n<div style=\"display:flex;align-items:center;gap:12px\">\n<span style=\"font-size:12.5px;width:132px;flex:none\">Estilo de jogo da IA</span>\n<span style=\"flex:1;height:9px;border-radius:5px;background:var(--d10);overflow:hidden;display:block\"><i style=\"display:block;height:100%;width:6%;border-radius:5px;background:linear-gradient(90deg,var(--d26),var(--d25))\"></i></span>\n<b style=\"font-family:inherit;font-size:12.5px;width:44px;text-align:right\">6%</b>\n</div>\n</div>\n<span style=\"font-size:11.5px;color:var(--d17);line-height:1.5\">O peso muda de função para função: para um goleiro o físico pesa mais, para um ala cruzador as habilidades de cruzamento sobem.</span>\n</div>\n\n<div style=\"display:flex;flex-direction:column;gap:12px;padding:19px 20px;border-radius:16px;background:linear-gradient(158deg,var(--d42),var(--d43));border:1px solid var(--d20)\">\n<b style=\"font-size:15px;font-weight:700\">De onde vêm os dados</b>\n<div style=\"display:flex;flex-direction:column;gap:9px\">\n<div style=\"display:flex;align-items:baseline;gap:9px\">\n<span style=\"font-family:inherit;font-size:11px;color:var(--d25);flex:none\">→</span>\n<span style=\"font-size:12.5px;color:var(--d30);line-height:1.45\">Atributos lidos do próprio jogo, card por card, no nível máximo de treino.</span>\n</div>\n<div style=\"display:flex;align-items:baseline;gap:9px\">\n<span style=\"font-family:inherit;font-size:11px;color:var(--d25);flex:none\">→</span>\n<span style=\"font-size:12.5px;color:var(--d30);line-height:1.45\">Efeito de habilidade e ímpeto medido dentro do jogo, não estimado.</span>\n</div>\n<div style=\"display:flex;align-items:baseline;gap:9px\">\n<span style=\"font-family:inherit;font-size:11px;color:var(--d25);flex:none\">→</span>\n<span style=\"font-size:12.5px;color:var(--d30);line-height:1.45\">Molde de cada função construído a partir dos cards que a comunidade competitiva usa nela.</span>\n</div>\n<div style=\"display:flex;align-items:baseline;gap:9px\">\n<span style=\"font-family:inherit;font-size:11px;color:var(--d50);flex:none\">×</span>\n<span style=\"font-size:12.5px;color:var(--d24);line-height:1.45\">Não usamos nota de site, voto de usuário nem opinião de streamer.</span>\n</div>\n</div>\n<div style=\"margin-top:auto;display:flex;align-items:center;gap:10px;padding-top:4px\">\n<b style=\"font-size:12.5px;font-weight:700;padding:10px 16px;border-radius:11px;background:linear-gradient(180deg,var(--d25),var(--d26));color:var(--d27)\">Ver o método completo</b>\n<span style=\"font-size:11.5px;color:var(--d17)\">atualizado a cada box nova</span>\n</div>\n</div>\n</div>\n\n</div>\n"}, "ranking": {"abre": "<div style=\"width:1280px;border-radius:18px;overflow:hidden;font-family:inherit;color:var(--d1);box-shadow:0 24px 60px var(--d2);background:radial-gradient(1100px 380px at 18% -10%,var(--d3),transparent 62%),linear-gradient(180deg,var(--d4),var(--d5))\">", "header": "<div style=\"display:flex;align-items:center;gap:18px;padding:0 22px;height:56px;background:var(--d6);border-bottom:1px solid var(--d7)\">\n<div style=\"font-weight:700;font-size:14.5px;letter-spacing:.4px;background:linear-gradient(96deg,var(--d1),var(--d8));-webkit-background-clip:text;background-clip:text;color:transparent\">ClubEfootball</div>\n<div style=\"display:flex;gap:3px;background:var(--d9);padding:3px;border-radius:10px;border:1px solid var(--d10)\">\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Início</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Meu time</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;background:linear-gradient(180deg,var(--d11),var(--d12));color:var(--d1);font-weight:600\">Ranking</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Boxes atuais</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Boxes anteriores</div>\n<div style=\"font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--d13)\">Como calculamos</div>\n</div>\n<div style=\"flex:1;display:flex;align-items:center;gap:9px;background:var(--d14);border:1px solid var(--d15);border-radius:10px;height:34px;padding:0 12px;max-width:320px;transition:all .18s ease\" style-hover=\"border-color:var(--d71);background:var(--d91)\">\n<span style=\"color:var(--d16);font-size:13px\">⌕</span>\n<span style=\"font-size:12.5px;color:var(--d16)\">buscar em todos os cards</span>\n</div>\n<div style=\"margin-left:auto;display:flex;align-items:center;gap:12px;font-family:inherit;font-size:11px;color:var(--d17)\">\n<span><b style=\"color:var(--d8)\">12.368</b> linhas</span>\n<span><b style=\"color:var(--d8)\">2.785</b> completos</span>\n<span style=\"position:relative;width:20px;height:20px;border-radius:50%;border:1px solid var(--d37);display:flex;align-items:center;justify-content:center;font-size:10px;color:var(--d13);font-style:italic;transition:all .18s ease\" style-hover=\"border-color:var(--d23);color:var(--d8)\">i\n<b style=\"position:absolute;top:26px;right:0;width:230px;padding:10px 12px;border-radius:11px;background:var(--d38);backdrop-filter:blur(18px);border:1px solid var(--d37);box-shadow:0 14px 34px var(--d39);font-family:inherit;font-size:11.5px;font-weight:400;font-style:normal;color:var(--d30);line-height:1.45;text-align:left;opacity:0;pointer-events:none;transition:opacity .18s ease;z-index:9\" style-hover=\"opacity:1\">Card completo é aquele em que todas as funções que ele exerce já foram otimizadas pelo motor.</b>\n</span>\n<span style=\"padding:5px 10px;border:1px solid var(--d18);border-radius:8px;color:var(--d8);transition:all .18s ease\" style-hover=\"background:var(--d92);border-color:var(--d57)\">◐</span>\n</div>\n</div>", "corpo": "\n\n<div style=\"display:flex;align-items:center;gap:10px;padding:0 22px;height:42px;background:var(--d64);border-bottom:1px solid var(--d10)\">\n<span style=\"font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d62)\">MEIO</span>\n<span style=\"font-size:12.5px;padding:6px 13px;border-radius:9px;background:linear-gradient(180deg,var(--d25),var(--d26));color:var(--d27);font-weight:700;box-shadow:0 4px 14px var(--d93)\">Ala finalizador</span>\n<span style=\"font-size:12.5px;padding:6px 12px;border-radius:9px;border:1px solid var(--d18);color:var(--d85);background:var(--d32);transition:all .18s ease\" style-hover=\"border-color:var(--d71);color:var(--d94);background:var(--d40)\">19 funções ▾</span>\n<div style=\"margin-left:auto;display:flex;align-items:center;gap:8px\">\n<span style=\"font-family:inherit;font-size:11px;color:var(--d8);border:1px solid var(--d95);background:var(--d40);border-radius:9px;padding:5px 10px\">pontuação ≥ 100 <span style=\"color:var(--d16)\">×</span></span>\n<span style=\"font-size:12.5px;padding:5px 12px;border-radius:9px;border:1px solid var(--d18);color:var(--d30);background:var(--d32);transition:all .18s ease\" style-hover=\"background:var(--d15)\">filtros <b style=\"color:var(--d8)\">2</b></span>\n</div>\n</div>\n\n<div style=\"padding:20px 22px 26px;display:flex;flex-direction:column;gap:18px\">\n<div style=\"display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px\">\n<sc-for list=\"{{ podio }}\" as=\"g\" hint-placeholder-count=\"3\">\n<div style=\"position:relative;border-radius:16px;padding:18px;display:flex;flex-direction:column;gap:14px;background:linear-gradient(158deg,var(--d20),var(--d58));border:1px solid var(--d59);box-shadow:0 2px 20px var(--d96);transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease\" style-hover=\"transform:translateY(-3px);border-color:var(--d97);box-shadow:0 16px 40px var(--d98)\">\n<span style=\"position:absolute;top:12px;right:14px;font-family:inherit;font-size:11.5px;font-weight:700;padding:3px 8px;border-radius:7px;background:var(--d86);border:1px solid var(--d99);color:var(--d45)\">{{ g.pos }}</span>\n<div style=\"display:flex;align-items:flex-start;gap:14px\">\n<span style=\"width:84px;height:84px;border-radius:13px;background:linear-gradient(160deg,var(--d33),var(--d32));border:1px solid var(--d7);display:flex;align-items:center;justify-content:center;font-size:10px;color:var(--d16);flex:none\">foto</span>\n<span style=\"display:flex;flex-direction:column;gap:6px;min-width:0;flex:1\">\n<em style=\"font-style:normal;font-family:inherit;font-size:10px;letter-spacing:1.5px;color:var(--d8);align-self:flex-start\">{{ g.r }}º LUGAR</em>\n<b style=\"font-size:20px;font-weight:700;letter-spacing:-.3px;line-height:1.18\">{{ g.nome }}</b>\n<i style=\"font-style:normal;display:flex;align-items:center;gap:7px;flex-wrap:wrap\">\n<span style=\"font-size:12px;color:var(--d13)\">{{ g.est }}</span>\n</i>\n</span>\n</div>\n<div style=\"display:flex;align-items:center;gap:8px;padding:8px 11px;border-radius:10px;background:var(--d9);border:1px solid var(--d7)\">\n<span style=\"font-size:12.5px;font-weight:600;color:var(--d30)\">{{ g.fn }}</span>\n</div>\n<div style=\"display:flex;align-items:flex-end;justify-content:space-between\">\n<span style=\"display:flex;flex-direction:column;gap:5px\">\n<b style=\"font-family:inherit;font-size:34px;font-weight:600;line-height:1;background:linear-gradient(180deg,var(--d100),var(--d26));-webkit-background-clip:text;background-clip:text;color:transparent\">{{ g.pts }}</b>\n<em style=\"font-style:normal;font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d17)\">PONTUAÇÃO</em>\n</span>\n<span style=\"display:flex;flex-direction:column;align-items:flex-end;gap:5px\">\n<b style=\"font-family:inherit;font-size:20px;font-weight:600;line-height:1\">{{ g.pct }}%</b>\n<em style=\"font-style:normal;font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d17)\">% DO TOPO</em>\n</span>\n</div>\n<div style=\"height:7px;border-radius:5px;background:var(--d10);overflow:hidden\">\n<i style=\"display:block;height:100%;border-radius:5px;background:linear-gradient(90deg,var(--d101),var(--d25));box-shadow:0 0 14px var(--d23);width:{{ g.w }}\"></i>\n</div>\n</div>\n</sc-for>\n</div>\n\n<div style=\"display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px\">\n<sc-for list=\"{{ resto }}\" as=\"g\" hint-placeholder-count=\"14\">\n<div style=\"position:relative;border-radius:14px;padding:13px;display:flex;flex-direction:column;gap:10px;background:linear-gradient(158deg,var(--d42),var(--d43));border:1px solid var(--d102);transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease\" style-hover=\"transform:translateY(-3px);border-color:var(--d57);box-shadow:0 14px 32px var(--d84)\">\n<span style=\"position:absolute;top:12px;right:14px;font-family:inherit;font-size:11.5px;font-weight:700;padding:3px 8px;border-radius:7px;background:var(--d86);border:1px solid var(--d99);color:var(--d45)\">{{ g.pos }}</span>\n<div style=\"display:flex;align-items:center;gap:9px\">\n<span style=\"width:34px;height:34px;border-radius:9px;background:linear-gradient(160deg,var(--d33),var(--d32));border:1px solid var(--d10);flex:none;display:block\"></span>\n<span style=\"font-family:inherit;font-size:10.5px;color:var(--d16)\">{{ g.r }}º</span>\n</div>\n<div style=\"display:flex;flex-direction:column;gap:3px\">\n<b style=\"font-size:12.5px;font-weight:600;line-height:1.25\">{{ g.nome }}</b>\n<em style=\"font-style:normal;font-size:10.5px;color:var(--d13);line-height:1.25\">{{ g.est }}</em>\n<em style=\"font-style:normal;font-size:11px;color:var(--d30);margin-top:2px;display:block\">{{ g.fn }}</em>\n</div>\n<div style=\"display:flex;align-items:baseline;justify-content:space-between;gap:4px;margin-top:auto\">\n<span style=\"font-family:inherit;font-size:18px;font-weight:600\">{{ g.pts }}</span>\n<span style=\"font-family:inherit;font-size:10px;color:var(--d8)\">{{ g.pct }}</span>\n</div>\n<div style=\"height:5px;border-radius:4px;background:var(--d10);overflow:hidden\">\n<i style=\"display:block;height:100%;border-radius:4px;background:linear-gradient(90deg,var(--d101),var(--d25));width:{{ g.w }}\"></i>\n</div>\n</div>\n</sc-for>\n</div>\n</div>\n"}, "ficha": {"abre": "<div style=\"width:1280px;border-radius:18px;overflow:hidden;font-family:inherit;color:var(--d1);box-shadow:0 24px 60px var(--d2);display:grid;grid-template-columns:340px minmax(0,1fr);background:radial-gradient(900px 340px at 12% -8%,var(--d103),transparent 60%),linear-gradient(180deg,var(--d4),var(--d5))\">", "header": "", "corpo": "\n<div style=\"background:linear-gradient(180deg,var(--d42),var(--d43));border-right:1px solid var(--d7);padding:22px;display:flex;flex-direction:column;gap:16px\">\n<div style=\"display:flex;gap:16px;align-items:flex-start\">\n<div style=\"width:112px;height:148px;border-radius:13px;background:linear-gradient(165deg,var(--d11),var(--d32));border:1px solid var(--d18);box-shadow:0 12px 28px var(--d104);display:flex;align-items:center;justify-content:center;font-size:11px;color:var(--d16);flex:none\">foto</div>\n<div style=\"display:flex;flex-direction:column;gap:11px;min-width:0;min-height:148px\">\n<div style=\"font-size:26px;font-weight:800;letter-spacing:-.7px;line-height:1.08\">Lionel Messi</div>\n<div style=\"display:flex;align-items:center;gap:7px\">\n<span style=\"font-family:inherit;font-size:13px;font-weight:800;padding:3px 9px;border-radius:7px;background:linear-gradient(180deg,var(--d105),var(--d106));border:1px solid var(--d107);color:var(--d45)\">PD</span>\n<span style=\"font-size:12.5px;color:var(--d30)\">Ponta direita</span>\n</div>\n<div style=\"display:flex;flex-direction:column;gap:2px\">\n<span style=\"font-family:inherit;font-size:9px;letter-spacing:1.3px;color:var(--d16)\">ESTILO DE JOGO</span>\n<span style=\"font-size:17px;font-weight:700;letter-spacing:-.2px;color:var(--d108)\">Armador criativo</span>\n</div>\n<div style=\"margin-top:auto;font-family:inherit;font-size:11.5px;color:var(--d17)\">24/06/2026</div>\n</div>\n</div>\n\n<div style=\"display:flex;flex-direction:column;gap:5px;border-radius:11px;padding:10px 13px;background:var(--d14);border:1px solid var(--d7)\">\n<div style=\"display:flex;align-items:baseline;justify-content:space-between\">\n<span style=\"font-size:11.5px;color:var(--d85)\">Base Konami</span>\n<b style=\"font-family:inherit;font-size:14px;color:var(--d1)\">92</b>\n</div>\n<div style=\"display:flex;align-items:baseline;justify-content:space-between\">\n<span style=\"font-size:11.5px;color:var(--d85)\">Máximo Konami</span>\n<b style=\"font-family:inherit;font-size:14px;color:var(--d1)\">104.20</b>\n</div>\n</div>\n\n<div style=\"border-radius:14px;padding:16px;background:linear-gradient(150deg,var(--d51),var(--d52));border:1px solid var(--d65);display:flex;flex-direction:column;gap:12px\">\n<div style=\"display:flex;flex-direction:column;gap:7px\">\n<div style=\"font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d50)\">PONTUAÇÃO TOTAL</div>\n<div style=\"font-family:inherit;font-size:44px;font-weight:700;line-height:1;letter-spacing:-1.5px;background:linear-gradient(180deg,var(--d54),var(--d55));-webkit-background-clip:text;background-clip:text;color:transparent\">112.26</div>\n</div>\n<div style=\"display:flex;align-items:baseline;gap:7px\">\n<span style=\"font-family:inherit;font-size:15px;font-weight:700;line-height:1;color:var(--d25)\">100.00%</span>\n<span style=\"font-family:inherit;font-size:9px;letter-spacing:1.3px;color:var(--d109)\">DO TOPO</span>\n</div>\n<div style=\"height:6px;border-radius:4px;background:var(--d110);overflow:hidden\">\n<i style=\"display:block;height:100%;width:100%;border-radius:4px;background:linear-gradient(90deg,var(--d101),var(--d25));box-shadow:0 0 16px var(--d67)\"></i>\n</div>\n</div>\n\n<div style=\"border:1px solid var(--d41);border-radius:16px;overflow:hidden\">\n<div style=\"display:flex;align-items:center;justify-content:space-between;padding:10px 13px;background:linear-gradient(180deg,var(--d103),var(--d35));border-bottom:1px solid var(--d3)\">\n<span style=\"display:flex;align-items:baseline;gap:9px;font-size:12.5px;font-weight:600;color:var(--d30)\">ATACANTE <b style=\"font-family:inherit;font-size:13.5px;color:var(--d8)\">PD</b></span>\n<span style=\"display:flex;align-items:center;gap:8px\">\n<span style=\"position:relative;width:19px;height:19px;border-radius:50%;border:1px solid var(--d79);display:flex;align-items:center;justify-content:center;font-size:10px;font-style:italic;color:var(--d111);transition:all .18s ease\" style-hover=\"border-color:var(--d67);color:var(--d8)\">i\n<b style=\"position:absolute;top:25px;right:0;width:206px;padding:11px 12px;border-radius:11px;background:var(--d38);backdrop-filter:blur(18px);border:1px solid var(--d37);box-shadow:0 14px 34px var(--d39);font-size:11.5px;font-weight:400;font-style:normal;color:var(--d30);line-height:1.5;text-align:left;display:flex;flex-direction:column;gap:6px;opacity:0;pointer-events:none;transition:opacity .18s ease;z-index:9\" style-hover=\"opacity:1\">\n<i style=\"font-style:normal;display:flex;align-items:center;gap:7px\"><u style=\"width:10px;height:10px;border-radius:3px;background:linear-gradient(180deg,var(--d25),var(--d26));display:block\"></u>a posição desta ficha</i>\n<i style=\"font-style:normal;display:flex;align-items:center;gap:7px\"><u style=\"width:10px;height:10px;border-radius:3px;border:1.5px solid var(--d55);display:block\"></u>posição de fábrica</i>\n<i style=\"font-style:normal;display:flex;align-items:center;gap:7px\"><u style=\"width:10px;height:10px;border-radius:3px;background:var(--d112);display:block\"></u>segunda posição</i>\n</b>\n</span>\n</span>\n</div>\n<div style=\"padding:12px;background:linear-gradient(180deg,var(--d75),var(--d113));display:flex;flex-direction:column;gap:5px\">\n<sc-for list=\"{{ campo }}\" as=\"r\" hint-placeholder-count=\"7\">\n<div style=\"display:grid;grid-template-columns:repeat(3,1fr);gap:5px\">\n<sc-for list=\"{{ r.cells }}\" as=\"c\" hint-placeholder-count=\"3\">\n<span style=\"{{ c.st }}\">{{ c.n }}</span>\n</sc-for>\n</div>\n</sc-for>\n</div>\n</div>\n\n<div style=\"display:flex;flex-direction:column;gap:7px\">\n<div style=\"display:flex;align-items:center;gap:7px\">\n<span style=\"font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d17)\">FUNÇÕES QUE EXERCE · 8</span>\n<span style=\"position:relative;width:19px;height:19px;border-radius:50%;border:1px solid var(--d37);display:flex;align-items:center;justify-content:center;font-size:10px;font-style:italic;color:var(--d13);transition:all .18s ease\" style-hover=\"border-color:var(--d23);color:var(--d8)\">i\n<b style=\"position:absolute;top:25px;left:0;width:224px;padding:11px 12px;border-radius:11px;background:var(--d38);backdrop-filter:blur(18px);border:1px solid var(--d37);box-shadow:0 14px 34px var(--d39);font-size:11.5px;font-weight:400;font-style:normal;color:var(--d30);line-height:1.5;text-align:left;opacity:0;pointer-events:none;transition:opacity .18s ease;z-index:9\" style-hover=\"opacity:1\">Clique para abrir o build da função. Quanto maior a nota, maior e mais forte a cor do botão.</b>\n</span>\n</div>\n<sc-for list=\"{{ fnsW }}\" as=\"f\" hint-placeholder-count=\"8\">\n<div style=\"{{ f.row }}\" style-hover=\"filter:brightness(1.4);transform:translateX(3px)\">\n<span>{{ f.n }}</span>\n<span style=\"{{ f.basSt }}\">{{ f.bas }}</span>\n<span style=\"{{ f.posSt }}\">{{ f.pos }}</span>\n<b style=\"{{ f.num }}\">{{ f.pts }}</b>\n</div>\n</sc-for>\n</div>\n</div>\n\n<div style=\"padding:22px 24px;display:flex;flex-direction:column;gap:18px\">\n<div style=\"display:flex;align-items:center;gap:9px\">\n<span style=\"font-size:12px;font-weight:700;padding:9px 15px;border-radius:11px;background:linear-gradient(180deg,var(--d25),var(--d26));color:var(--d27);box-shadow:0 6px 18px var(--d28);transition:all .18s ease\" style-hover=\"transform:translateY(-2px);box-shadow:0 12px 26px var(--d97)\">⚡ MÁXIMO POSSÍVEL</span>\n<span style=\"font-size:12px;padding:9px 15px;border-radius:11px;border:1px solid var(--d29);background:var(--d14);color:var(--d85);transition:all .18s ease\" style-hover=\"background:var(--d33);color:var(--d1);transform:translateY(-2px)\">⚙ FAZER MINHA BUILD</span>\n<span style=\"position:relative;width:20px;height:20px;border-radius:50%;border:1px solid var(--d37);display:flex;align-items:center;justify-content:center;font-size:10px;font-style:italic;color:var(--d13);transition:all .18s ease\" style-hover=\"border-color:var(--d23);color:var(--d8)\">i\n<b style=\"position:absolute;top:26px;left:0;width:250px;padding:11px 12px;border-radius:11px;background:var(--d38);backdrop-filter:blur(18px);border:1px solid var(--d37);box-shadow:0 14px 34px var(--d39);font-size:11.5px;font-weight:400;font-style:normal;color:var(--d30);line-height:1.5;text-align:left;opacity:0;pointer-events:none;transition:opacity .18s ease;z-index:9\" style-hover=\"opacity:1\">Máximo possível é o teto da carta, a build que o motor escolheu. Minha build monta o card como ele está no seu jogo, na mão.</b>\n</span>\n<span style=\"display:flex;align-items:baseline;gap:8px;padding:7px 13px;border-radius:10px;background:var(--d9);border:1px solid var(--d15)\">\n<b style=\"font-family:inherit;font-size:9px;letter-spacing:1.3px;color:var(--d17);font-weight:600\">PODE MELHORAR</b>\n<b style=\"font-family:inherit;font-size:16px;font-weight:700;color:var(--d25)\">0%</b>\n</span>\n<span style=\"margin-left:auto;display:flex;align-items:center;gap:7px\">\n<span style=\"display:flex;align-items:baseline;gap:9px;font-size:13px;font-weight:700;padding:8px 15px;border-radius:10px;background:linear-gradient(180deg,var(--d114),var(--d115));border:1px solid var(--d116);color:var(--d117)\">Ala finalizador <b style=\"font-family:inherit;font-size:14px\">112.3</b></span>\n</span>\n</div>\n\n<div style=\"display:flex;flex-direction:column;gap:9px;border-radius:16px;padding:16px 18px;background:linear-gradient(158deg,var(--d42),var(--d43));border:1px solid var(--d20)\">\n<div style=\"display:flex;align-items:center;gap:8px\">\n<span style=\"font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d17)\">DISTRIBUIÇÃO DOS PONTOS</span>\n<span style=\"margin-left:auto;font-family:inherit;font-size:11px;color:var(--d85)\">Nível <b style=\"color:var(--d1)\">30</b> · <b style=\"color:var(--d1)\">58/58</b> · <b style=\"color:var(--d25)\">tudo gasto</b></span>\n</div>\n<sc-for list=\"{{ barsFull }}\" as=\"b\" hint-placeholder-count=\"7\">\n<div style=\"display:grid;grid-template-columns:112px minmax(0,1fr) 52px 84px;gap:12px;align-items:center;border-radius:8px;padding:3px 5px;transition:background .18s ease\" style-hover=\"background:var(--d69)\">\n<span style=\"font-size:12.5px;color:var(--d30)\">{{ b.n }}</span>\n<span style=\"height:8px;border-radius:5px;background:var(--d10);display:block;overflow:hidden;position:relative\">\n<i style=\"display:block;height:100%;border-radius:5px;background:linear-gradient(90deg,var(--d101),var(--d25));box-shadow:0 0 12px var(--d57);width:{{ b.w }}\"></i>\n</span>\n<span style=\"font-family:inherit;font-size:11px;color:var(--d17);text-align:right\">{{ b.pts }} pts</span>\n<span style=\"display:flex;align-items:center;justify-content:flex-end;gap:6px\">\n<i style=\"font-style:normal;width:22px;height:22px;border-radius:7px;background:var(--d10);border:1px solid var(--d33);display:flex;align-items:center;justify-content:center;font-size:13px;color:var(--d85);transition:all .16s ease\" style-hover=\"background:var(--d41);color:var(--d25);border-color:var(--d57)\">−</i>\n<b style=\"font-family:inherit;font-size:13.5px;font-weight:600;width:20px;text-align:center\">{{ b.v }}</b>\n<i style=\"font-style:normal;width:22px;height:22px;border-radius:7px;background:var(--d10);border:1px solid var(--d33);display:flex;align-items:center;justify-content:center;font-size:13px;color:var(--d85);transition:all .16s ease\" style-hover=\"background:var(--d41);color:var(--d25);border-color:var(--d57)\">+</i>\n</span>\n</div>\n</sc-for>\n<div style=\"margin-top:6px;text-align:center;font-size:12px;font-weight:700;padding:9px;border-radius:10px;background:linear-gradient(180deg,var(--d25),var(--d26));color:var(--d27);box-shadow:0 6px 18px var(--d36);transition:all .18s ease\" style-hover=\"transform:translateY(-2px);box-shadow:0 12px 26px var(--d57)\">⚡ OTIMIZAR</div>\n</div>\n\n<div style=\"display:grid;grid-template-columns:1fr 1fr;gap:16px\">\n<div style=\"display:flex;flex-direction:column;gap:14px;border-radius:16px;padding:16px 18px;background:linear-gradient(158deg,var(--d42),var(--d43));border:1px solid var(--d20)\">\n<div style=\"font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d17)\">HABILIDADES</div>\n\n<div style=\"display:flex;flex-direction:column;gap:6px\">\n<div style=\"font-size:11px;color:var(--d17)\">especiais</div>\n<div style=\"display:flex;flex-wrap:wrap;gap:6px\">\n<span style=\"font-size:12.5px;font-weight:600;padding:5px 11px;border-radius:8px;background:var(--d118);border:1px solid var(--d116);color:var(--d117)\">Passe visionário</span>\n</div>\n</div>\n\n<div style=\"display:flex;flex-direction:column;gap:6px\">\n<div style=\"font-size:11px;color:var(--d17)\">nativas</div>\n<div style=\"display:flex;flex-wrap:wrap;gap:6px\">\n<span style=\"font-size:12px;padding:5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d12);color:var(--d30);transition:all .18s ease\" style-hover=\"background:var(--d29)\">Finta dupla</span>\n<span style=\"font-size:12px;padding:5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d12);color:var(--d30);transition:all .18s ease\" style-hover=\"background:var(--d29)\">Elástico</span>\n<span style=\"font-size:12px;padding:5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d12);color:var(--d30);transition:all .18s ease\" style-hover=\"background:var(--d29)\">Chute colocado</span>\n<span style=\"font-size:12px;padding:5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d12);color:var(--d30);transition:all .18s ease\" style-hover=\"background:var(--d29)\">Cobrança de falta</span>\n<span style=\"font-size:12px;padding:5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d12);color:var(--d30);transition:all .18s ease\" style-hover=\"background:var(--d29)\">Sem olhar</span>\n</div>\n</div>\n<div style=\"display:flex;flex-direction:column;gap:7px\">\n<div style=\"display:flex;align-items:baseline;gap:8px\">\n<span style=\"font-size:11px;color:var(--d17)\">adicionadas</span>\n<span style=\"font-family:inherit;font-size:10.5px;font-weight:700;color:var(--d85)\">5 de 5</span>\n<span style=\"position:relative;width:19px;height:19px;border-radius:50%;border:1px solid var(--d37);display:flex;align-items:center;justify-content:center;font-size:10px;font-style:italic;color:var(--d13);transition:all .18s ease;flex:none\" style-hover=\"border-color:var(--d23);color:var(--d8)\">i\n<b style=\"position:absolute;top:25px;left:0;width:214px;padding:11px 12px;border-radius:11px;background:var(--d38);backdrop-filter:blur(18px);border:1px solid var(--d37);box-shadow:0 14px 34px var(--d119);font-size:11.5px;font-weight:400;font-style:normal;color:var(--d30);line-height:1.5;text-align:left;opacity:0;pointer-events:none;transition:opacity .18s ease;z-index:9\" style-hover=\"opacity:1\">Arraste uma sugestão para cá. O teto é de 5 habilidades adicionadas.</b>\n</span>\n</div>\n<div style=\"display:flex;flex-wrap:wrap;gap:6px;padding:9px;border-radius:11px;border:1px dashed var(--d31);background:var(--d64)\">\n<span style=\"display:flex;align-items:center;gap:8px;font-size:12px;padding:5px 8px 5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d18);color:var(--d30);cursor:grab;transition:all .18s ease\" style-hover=\"filter:brightness(1.3);transform:translateY(-1px)\">Drible de primeira <b style=\"font-size:13px;color:var(--d13);line-height:1\">×</b></span>\n<span style=\"display:flex;align-items:center;gap:8px;font-size:12px;padding:5px 8px 5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d18);color:var(--d30);cursor:grab;transition:all .18s ease\" style-hover=\"filter:brightness(1.3);transform:translateY(-1px)\">Chute de fora da área <b style=\"font-size:13px;color:var(--d13);line-height:1\">×</b></span>\n<span style=\"display:flex;align-items:center;gap:8px;font-size:12px;padding:5px 8px 5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d18);color:var(--d30);cursor:grab;transition:all .18s ease\" style-hover=\"filter:brightness(1.3);transform:translateY(-1px)\">Passe rasteiro cortante <b style=\"font-size:13px;color:var(--d13);line-height:1\">×</b></span>\n<span style=\"display:flex;align-items:center;gap:8px;font-size:12px;padding:5px 8px 5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d18);color:var(--d30);cursor:grab;transition:all .18s ease\" style-hover=\"filter:brightness(1.3);transform:translateY(-1px)\">Malabarismo <b style=\"font-size:13px;color:var(--d13);line-height:1\">×</b></span>\n<span style=\"display:flex;align-items:center;gap:8px;font-size:12px;padding:5px 8px 5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d18);color:var(--d30);cursor:grab;transition:all .18s ease\" style-hover=\"filter:brightness(1.3);transform:translateY(-1px)\">Espírito guerreiro <b style=\"font-size:13px;color:var(--d13);line-height:1\">×</b></span>\n</div>\n</div>\n<div style=\"display:flex;flex-direction:column;gap:6px\">\n<div style=\"font-size:11px;color:var(--d17)\">sugestões · o pool inteiro que o motor pode escolher · 8</div>\n<div style=\"display:flex;flex-wrap:wrap;gap:6px\">\n<span style=\"font-size:12px;padding:5px 10px;border-radius:8px;border:1px dashed var(--d31);color:var(--d17)\">Drible de primeira</span>\n<span style=\"font-size:12px;padding:5px 10px;border-radius:8px;border:1px dashed var(--d31);color:var(--d17)\">Chute de fora da área</span>\n<span style=\"font-size:12px;padding:5px 10px;border-radius:8px;border:1px dashed var(--d31);color:var(--d17)\">Passe rasteiro cortante</span>\n<span style=\"font-size:12px;padding:5px 10px;border-radius:8px;border:1px dashed var(--d31);color:var(--d17)\">Malabarismo</span>\n<span style=\"font-size:12px;padding:5px 10px;border-radius:8px;border:1px dashed var(--d31);color:var(--d17)\">Espírito guerreiro</span>\n<span style=\"font-size:12px;padding:5px 10px;border-radius:8px;border:1px dashed var(--d31);color:var(--d17)\">Passe em profundidade</span>\n<span style=\"font-size:12px;padding:5px 10px;border-radius:8px;border:1px dashed var(--d31);color:var(--d17)\">Finta dupla</span>\n<span style=\"font-size:12px;padding:5px 10px;border-radius:8px;border:1px dashed var(--d31);color:var(--d17)\">Passe na medida</span>\n</div>\n</div>\n</div>\n<div style=\"display:flex;flex-direction:column;gap:12px;border-radius:16px;padding:16px 18px;background:linear-gradient(158deg,var(--d42),var(--d43));border:1px solid var(--d20)\">\n<div style=\"font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d17)\">TÉCNICO</div>\n<div style=\"display:flex;align-items:center;justify-content:space-between;background:var(--d12);border:1px solid var(--d15);border-radius:10px;padding:10px 12px;font-size:13px;transition:all .18s ease\" style-hover=\"border-color:var(--d57);background:var(--d69)\">Pep Guardiola <span style=\"color:var(--d16)\">▾</span></div>\n<div style=\"font-size:12px;color:var(--d85)\">+1 Posse de bola · +1 Drible</div>\n<div style=\"font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d17);border-top:1px solid var(--d33);padding-top:13px;margin-top:3px\">ÍMPETO</div>\n<div style=\"background:var(--d12);border:1px solid var(--d7);border-radius:12px;padding:11px 13px;display:flex;flex-direction:column;gap:7px\">\n<div style=\"display:flex;align-items:center;gap:9px\">\n<b style=\"font-size:13.5px\">Fantasia</b>\n<span style=\"font-weight:400;font-size:11px;color:var(--d17)\">nativo</span>\n<b style=\"margin-left:auto;font-family:inherit;font-size:14px;font-weight:700;padding:2px 9px;border-radius:7px;background:var(--d33);border:1px solid var(--d11);color:var(--d1)\">+2</b>\n</div>\n<div style=\"display:flex;flex-wrap:wrap;gap:5px\">\n<span style=\"font-size:11px;color:var(--d85);background:var(--d10);padding:4px 8px;border-radius:6px\">Drible</span>\n<span style=\"font-size:11px;color:var(--d85);background:var(--d10);padding:4px 8px;border-radius:6px\">Controle de bola</span>\n<span style=\"font-size:11px;color:var(--d85);background:var(--d10);padding:4px 8px;border-radius:6px\">Finalização</span>\n<span style=\"font-size:11px;color:var(--d85);background:var(--d10);padding:4px 8px;border-radius:6px\">Agilidade</span>\n</div>\n<div style=\"display:flex;align-items:center;gap:9px;border-top:1px solid var(--d15);padding-top:9px;margin-top:2px\">\n<span style=\"display:flex;align-items:center;gap:6px;font-family:inherit;font-size:9px;letter-spacing:1.2px;color:var(--d120)\"><i style=\"width:10px;height:10px;background:var(--d120);display:block;clip-path:polygon(50% 0,100% 25%,100% 75%,50% 100%,0 75%,0 25%)\"></i>ÍMPETO CONDICIONAL</span>\n<span style=\"display:flex;gap:5px;margin-left:auto\">\n<b style=\"font-family:inherit;font-size:12px;font-weight:700;padding:4px 12px;border-radius:7px;background:linear-gradient(180deg,var(--d121),var(--d122));color:var(--d123);box-shadow:0 3px 10px var(--d124)\">+1</b>\n<b style=\"font-family:inherit;font-size:12px;font-weight:500;padding:4px 12px;border-radius:7px;background:var(--d12);border:1px solid var(--d18);color:var(--d85);transition:all .16s ease\" style-hover=\"border-color:var(--d125);color:var(--d120)\">+2</b>\n<b style=\"font-family:inherit;font-size:12px;font-weight:500;padding:4px 12px;border-radius:7px;background:var(--d12);border:1px solid var(--d18);color:var(--d85);transition:all .16s ease\" style-hover=\"border-color:var(--d125);color:var(--d120)\">+3</b>\n</span>\n</div>\n</div>\n<div style=\"background:var(--d12);border:1px solid var(--d7);border-radius:12px;padding:11px 13px;display:flex;flex-direction:column;gap:7px\">\n<div style=\"display:flex;align-items:center;gap:9px\">\n<b style=\"font-size:13.5px\">Instinto Artilheiro</b>\n<span style=\"font-weight:400;font-size:11px;color:var(--d17)\">adicionado</span>\n<b style=\"margin-left:auto;font-family:inherit;font-size:14px;font-weight:700;padding:2px 9px;border-radius:7px;background:var(--d33);border:1px solid var(--d11);color:var(--d1)\">+1</b>\n</div>\n<div style=\"display:flex;flex-wrap:wrap;gap:5px\">\n<span style=\"font-size:11px;color:var(--d85);background:var(--d10);padding:4px 8px;border-radius:6px\">Drible</span>\n<span style=\"font-size:11px;color:var(--d85);background:var(--d10);padding:4px 8px;border-radius:6px\">Reação</span>\n<span style=\"font-size:11px;color:var(--d85);background:var(--d10);padding:4px 8px;border-radius:6px\">Chute</span>\n</div>\n</div>\n</div>\n</div>\n\n<div style=\"display:flex;flex-direction:column;gap:10px;border-radius:16px;padding:16px 18px;background:linear-gradient(158deg,var(--d42),var(--d43));border:1px solid var(--d20)\">\n<div style=\"display:flex;align-items:center;gap:8px\">\n<span style=\"font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d17)\">ATRIBUTOS</span>\n<span style=\"position:relative;width:19px;height:19px;border-radius:50%;border:1px solid var(--d37);display:flex;align-items:center;justify-content:center;font-size:10px;font-style:italic;color:var(--d13);transition:all .18s ease\" style-hover=\"border-color:var(--d23);color:var(--d8)\">i\n<b style=\"position:absolute;top:25px;left:0;width:270px;padding:11px 12px;border-radius:11px;background:var(--d38);backdrop-filter:blur(18px);border:1px solid var(--d37);box-shadow:0 14px 34px var(--d39);font-size:11.5px;font-weight:400;font-style:normal;color:var(--d30);line-height:1.5;text-align:left;opacity:0;pointer-events:none;transition:opacity .18s ease;z-index:9\" style-hover=\"opacity:1\">Cada coluna mostra de onde veio o ganho: barras, ímpeto, técnico, habilidades. Alvo é o valor do molde da função; vs alvo é quanto o card passa ou falta.</b>\n</span>\n<span style=\"margin-left:auto;font-family:inherit;font-size:12px;color:var(--d85)\">TOTAL <b style=\"color:var(--d25);font-size:14px\">+305.9 pts</b></span>\n</div>\n\n<div style=\"display:grid;grid-template-columns:130px 88px repeat(11,minmax(0,1fr));gap:6px;align-items:end;padding:0 6px 7px;border-bottom:1px solid var(--d33)\">\n<sc-for list=\"{{ colsAttr }}\" as=\"c\" hint-placeholder-count=\"13\">\n<span style=\"font-family:inherit;font-size:8.5px;letter-spacing:.6px;color:var(--d16);line-height:1.25;text-align:right\">{{ c }}</span>\n</sc-for>\n</div>\n\n<sc-for list=\"{{ atributos }}\" as=\"gr\" hint-placeholder-count=\"2\">\n<div style=\"display:flex;flex-direction:column;gap:1px\">\n<div style=\"font-family:inherit;font-size:9px;letter-spacing:1.4px;color:var(--d62);padding:9px 6px 4px\">{{ gr.g }}</div>\n<sc-for list=\"{{ gr.rows }}\" as=\"a\" hint-placeholder-count=\"8\">\n<div style=\"display:grid;grid-template-columns:130px 88px repeat(11,minmax(0,1fr));gap:6px;align-items:center;padding:5px 6px;border-radius:7px;transition:background .16s ease\" style-hover=\"background:var(--d69)\">\n<span style=\"{{ a.nSt }}\">{{ a.n }}</span>\n<span style=\"{{ a.clsSt }}\">{{ a.cls }}</span>\n<span style=\"font-family:inherit;font-size:11px;color:var(--d17);text-align:right\">{{ a.base }}</span>\n<span style=\"{{ a.barSt }}\">{{ a.bar }}</span>\n<span style=\"{{ a.impSt }}\">{{ a.imp }}</span>\n<span style=\"{{ a.tecSt }}\">{{ a.tec }}</span>\n<b style=\"font-family:inherit;font-size:11.5px;text-align:right\">{{ a.tela }}</b>\n<span style=\"{{ a.hnSt }}\">{{ a.hn }}</span>\n<span style=\"{{ a.haSt }}\">{{ a.ha }}</span>\n<b style=\"font-family:inherit;font-size:11.5px;text-align:right\">{{ a.total }}</b>\n<span style=\"font-family:inherit;font-size:11px;color:var(--d17);text-align:right\">{{ a.alvo }}</span>\n<span style=\"{{ a.vsSt }}\">{{ a.vs }}</span>\n<span style=\"{{ a.ptsSt }}\">{{ a.pts }}</span>\n</div>\n</sc-for>\n</div>\n</sc-for>\n\n<details style=\"margin-top:4px;border-radius:11px;background:var(--d32);border:1px solid var(--d7);padding:9px 12px\">\n<summary style=\"font-size:11.5px;color:var(--d85);cursor:pointer;list-style:none\">+ 9 atributos indiferentes nesta função</summary>\n<div style=\"display:flex;flex-direction:column;gap:1px;margin-top:8px\">\n<sc-for list=\"{{ indiferentes }}\" as=\"gr\" hint-placeholder-count=\"2\">\n<div style=\"display:flex;flex-direction:column;gap:1px\">\n<div style=\"font-family:inherit;font-size:9px;letter-spacing:1.4px;color:var(--d62);padding:8px 0 4px\">{{ gr.g }}</div>\n<sc-for list=\"{{ gr.rows }}\" as=\"a\" hint-placeholder-count=\"5\">\n<div style=\"display:grid;grid-template-columns:130px 88px repeat(11,minmax(0,1fr));gap:6px;align-items:center;padding:4px 0\">\n<span style=\"{{ a.nSt }}\">{{ a.n }}</span>\n<span style=\"{{ a.clsSt }}\">{{ a.cls }}</span>\n<span style=\"font-family:inherit;font-size:11px;color:var(--d17);text-align:right\">{{ a.base }}</span>\n<span style=\"{{ a.barSt }}\">{{ a.bar }}</span>\n<span style=\"{{ a.impSt }}\">{{ a.imp }}</span>\n<span style=\"{{ a.tecSt }}\">{{ a.tec }}</span>\n<b style=\"font-family:inherit;font-size:11.5px;text-align:right;color:var(--d85)\">{{ a.tela }}</b>\n<span style=\"{{ a.hnSt }}\">{{ a.hn }}</span>\n<span style=\"{{ a.haSt }}\">{{ a.ha }}</span>\n<b style=\"font-family:inherit;font-size:11.5px;text-align:right;color:var(--d85)\">{{ a.total }}</b>\n<span style=\"font-family:inherit;font-size:11px;color:var(--d17);text-align:right\">{{ a.alvo }}</span>\n<span style=\"{{ a.vsSt }}\">{{ a.vs }}</span>\n<span style=\"{{ a.ptsSt }}\">{{ a.pts }}</span>\n</div>\n</sc-for>\n</div>\n</sc-for>\n</div>\n</details>\n</div>\n\n<div style=\"display:flex;flex-direction:column;gap:12px;border-radius:16px;padding:16px 18px;background:linear-gradient(158deg,var(--d42),var(--d43));border:1px solid var(--d20)\">\n<div style=\"display:grid;grid-template-columns:1fr 1fr;gap:14px\">\n<div style=\"display:flex;flex-direction:column;gap:8px\">\n<span style=\"font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d17)\">FÍSICO</span>\n<div style=\"display:flex;gap:7px;flex-wrap:wrap\">\n<span style=\"font-size:11.5px;padding:5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d10);color:var(--d30)\">170 cm</span>\n<span style=\"font-size:11.5px;padding:5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d10);color:var(--d30)\">72 kg</span>\n<span style=\"font-size:11.5px;padding:5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d10);color:var(--d30)\">38 anos</span>\n<span style=\"font-size:11.5px;padding:5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d10);color:var(--d30)\">tendência a lesão Baixa</span>\n</div>\n</div>\n<div style=\"display:flex;flex-direction:column;gap:8px\">\n<span style=\"font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d17)\">PÉ</span>\n<div style=\"display:flex;gap:7px;flex-wrap:wrap\">\n<span style=\"font-size:11.5px;padding:5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d10);color:var(--d30)\">pé bom <b style=\"color:var(--d1)\">Esquerdo</b></span>\n<span style=\"font-size:11.5px;padding:5px 10px;border-radius:8px;background:var(--d126);border:1px solid var(--d105);color:var(--d45)\">pé ruim <b>Raramente</b></span>\n<span style=\"font-size:11.5px;padding:5px 10px;border-radius:8px;background:var(--d126);border:1px solid var(--d105);color:var(--d45)\">precisão <b>Média</b></span>\n<span style=\"font-size:11.5px;padding:5px 10px;border-radius:8px;background:var(--d126);border:1px solid var(--d105);color:var(--d45)\">bônus <b>+0.14</b> na nota</span>\n</div>\n</div>\n</div>\n\n<div style=\"font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d17);border-top:1px solid var(--d33);padding-top:13px\">MEDIDAS DO CORPO</div>\n\n<div style=\"display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px\">\n<sc-for list=\"{{ medidas }}\" as=\"col\" hint-placeholder-count=\"3\">\n<div style=\"display:flex;flex-direction:column;gap:2px\">\n<div style=\"display:grid;grid-template-columns:minmax(0,1fr) 54px 38px 44px 48px;gap:6px;padding:0 4px 5px;border-bottom:1px solid var(--d33)\">\n<span style=\"font-family:inherit;font-size:8.5px;letter-spacing:.6px;color:var(--d16)\">Medida</span>\n<span style=\"font-family:inherit;font-size:8.5px;letter-spacing:.6px;color:var(--d16);text-align:center;line-height:1.25\">Nota da medida</span>\n<span style=\"font-family:inherit;font-size:8.5px;letter-spacing:.6px;color:var(--d16);text-align:right\">No card</span>\n<span style=\"font-family:inherit;font-size:8.5px;letter-spacing:.6px;color:var(--d16);text-align:right\">Alvo</span>\n<span style=\"font-family:inherit;font-size:8.5px;letter-spacing:.6px;color:var(--d16);text-align:right\">Pontos</span>\n</div>\n<sc-for list=\"{{ col }}\" as=\"m\" hint-placeholder-count=\"4\">\n<div style=\"display:grid;grid-template-columns:minmax(0,1fr) 54px 38px 44px 48px;gap:6px;align-items:center;padding:4px;border-radius:6px;transition:background .16s ease\" style-hover=\"background:var(--d69)\">\n<span style=\"font-size:11.5px;color:var(--d30)\">{{ m.n }} <em style=\"font-style:normal;font-family:inherit;font-size:9.5px;color:var(--d16)\">{{ m.p }}</em></span>\n<span style=\"{{ m.notaSt }}\">{{ m.nota }}</span>\n<b style=\"font-family:inherit;font-size:11.5px;text-align:right\">{{ m.card }}</b>\n<span style=\"font-family:inherit;font-size:10.5px;color:var(--d17);text-align:right\">{{ m.ref }}</span>\n<span style=\"{{ m.pontosSt }}\">{{ m.pontos }}</span>\n</div>\n</sc-for>\n</div>\n</sc-for>\n</div>\n\n<div style=\"display:flex;align-items:center;gap:16px;border-top:1px solid var(--d29);padding-top:10px;font-family:inherit;font-size:11px;color:var(--d17)\">\n<span style=\"font-weight:700;color:var(--d30);letter-spacing:1.2px\">TOTAL</span>\n<span>soma <b style=\"color:var(--d25)\">-3</b></span>\n<span>peso <b style=\"color:var(--d30)\">15</b></span>\n<span>bônus <b style=\"color:var(--d127)\">-0.15</b></span>\n<span style=\"margin-left:auto;font-size:14px;font-weight:700;color:var(--d127)\">-1%</span>\n</div>\n</div>\n\n<div style=\"display:grid;grid-template-columns:1fr 1fr;gap:16px\">\n<div style=\"display:flex;flex-direction:column;gap:11px;border-radius:16px;padding:16px 18px;background:linear-gradient(158deg,var(--d42),var(--d43));border:1px solid var(--d20)\">\n<div style=\"font-family:inherit;font-size:9.5px;letter-spacing:1.4px;color:var(--d17)\">ESTILO DE JOGO DA IA</div>\n<div style=\"display:flex;flex-wrap:wrap;gap:6px\">\n<span style=\"font-size:12px;padding:5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d18);color:var(--d30)\">Passe cortante</span>\n<span style=\"font-size:12px;padding:5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d18);color:var(--d30)\">Driblador incisivo</span>\n<span style=\"font-size:12px;padding:5px 10px;border-radius:8px;background:var(--d10);border:1px solid var(--d18);color:var(--d30)\">Jogo de infiltração</span>\n</div>\n<div style=\"font-size:11.5px;color:var(--d85)\">3 de 5 · bônus <b style=\"color:var(--d1)\">+0.9</b> na nota</div>\n</div>\n</div>\n</div>\n"}};
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
    if(c && c._t6Congelado && isFinite(Number(c._t6Congelado.recomendacao)))
      return Number(c._t6Congelado.recomendacao);
    try{ var t = topoDoTipo(c.tipo); return t > 0 ? (100 * nota(c) / t) : 0; }
    catch(e){ return 0; }
  }
  var FONTE_PCT = 'font-family:inherit;font-size:19px;font-weight:700;letter-spacing:-.4px;color:';
  function estiloPct(p){
    return FONTE_PCT + (p >= 99.5 ? 'var(--d8)' : (p >= 95 ? 'var(--d55)' : 'var(--d13)'));
  }
  function siglaTela(p){
    var mapa = {GK:'GO', MC:'MLG', MO:'MAT', PE:'PTE', PD:'PTD'};
    p = String(p || '').toUpperCase();
    return mapa[p] || p;
  }
  function estiloTela(n){
    var mapa = {
      'Jog. de infiltração':'Jogador de infiltração',
      'Jog. de Infiltração':'Jogador de infiltração'
    };
    n = String(n || '');
    return mapa[n] || n;
  }
  function destacaPontosBox(molde){
    return molde.replace(
      '<b style="{{ c.pctSt }}">{{ c.pct }}%</b>\n<em style="font-style:normal;font-family:inherit;font-size:10px;color:var(--d13)">{{ c.pts }} pts</em>',
      '<b style="font-family:inherit;font-size:19px;font-weight:700;letter-spacing:-.4px;color:var(--d25)">{{ c.pts }}</b>\n<em style="font-style:normal;font-family:inherit;font-size:10px;color:var(--d13);white-space:nowrap">Recomendação: {{ c.pct }}%</em>'
    );
  }
  window.t6card = function(c, i){
    var p = pct(c);
    return {r: (i + 1) + 'º', nome: esc(c.nome), est: esc(estiloTela(c.modelo || '')),
            fn: esc(c.tipo), pos: esc(siglaTela(c.np || c.pos || '')),
            pct: n2(p), pctSt: estiloPct(p),
            pts: n2(c && isFinite(Number(c._t6PtsExibida)) ? Number(c._t6PtsExibida) : nota(c)),
            k: esc(c.id + '|' + c.tipo)};
  };
  window.t6PorBox = function(){
    var cx = {};
    var central = window._t6BoxNomePorCard || {};
    var histPorId = {};
    try{ Object.keys(BOXHIST||{}).forEach(function(nome){
      (BOXHIST[nome].ids||[]).forEach(function(id){ histPorId[String(id)] = nome; });
    }); }catch(e){}
    for (var i = 0; i < D.length; i++){
      var c = D[i];
      if (!c || c.id === 'MOLDE') continue;
      var cid = String(c.id).split('@')[0];
      var historico = histPorId[cid], pacotes = central[cid] || [];
      if (!Array.isArray(pacotes)) pacotes=[pacotes];
      if (!pacotes.length && (historico || c.pacote)) pacotes=[historico || c.pacote];
      if (!pacotes.length) continue;
      /* A associação histórica corrigida prevalece sobre um pacote antigo ou
         duplicado. Assim o Cristiano fica somente em Living Legends. */
      pacotes.forEach(function(pacote){(cx[pacote] = cx[pacote] || []).push(c);});
    }
    return cx;
  };
  window.t6MesclaCadastroBoxes = function(boxes){
    var meta=window._t6BoxMeta=window._t6BoxMeta||{};
    var nomePorCard=window._t6BoxNomePorCard=window._t6BoxNomePorCard||{};
    (boxes||[]).forEach(function(b){
      meta[b.nome]=b;
      (b.card_ids||[]).forEach(function(cid){
        var k=String(cid), lista=nomePorCard[k]=nomePorCard[k]||[];
        if(lista.indexOf(b.nome)<0)lista.push(b.nome);
      });
    });
  };
  window.t6MesclaRetratosBoxes = function(linhas){
    var mapa=window._t6BoxRetratos=window._t6BoxRetratos||{};
    (linhas||[]).forEach(function(r){mapa[String(r.box_id)+'|'+String(r.card_id)]=r;});
  };
  window.t6CarregaRetratosBoxes = function(boxes){
    var ids=(boxes||[]).filter(function(b){return b&&b.status==='anterior';})
      .map(function(b){return String(b.id);});
    if(!ids.length)return Promise.resolve();
    var raiz='https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/';
    var chave='sb_publishable_XTKGboY9RyYiirPiIsWMhw_P8B51cHj';
    var cab={apikey:chave,Authorization:'Bearer '+chave};
    var u=raiz+'box_card_retratos?select=box_id,card_id,funcao,pontuacao,recomendacao,etiqueta_codigo,etiqueta'
      +'&box_id=in.('+ids.join(',')+')&limit=5000';
    return fetch(u,{headers:cab,cache:'no-store'}).then(function(r){
      if(!r.ok)throw new Error('retratos '+r.status);return r.json();
    }).then(window.t6MesclaRetratosBoxes);
  };
  window.t6CarregaNomesEtiquetas = function(){
    if(window._t6EtiquetasPromessa)return window._t6EtiquetasPromessa;
    var raiz='https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/';
    var chave='sb_publishable_XTKGboY9RyYiirPiIsWMhw_P8B51cHj';
    var cab={apikey:chave,Authorization:'Bearer '+chave};
    window._t6EtiquetasPromessa=fetch(raiz+'box_etiquetas?select=codigo,nome&order=ordem.asc',{
      headers:cab,cache:'no-store'
    }).then(function(r){if(!r.ok)throw new Error('etiquetas '+r.status);return r.json();})
      .then(function(rows){
        var mapa=window._t6EtiquetasNomes={};
        (rows||[]).forEach(function(x){mapa[x.codigo]=x.nome;});
      }).catch(function(){window._t6EtiquetasNomes=window._t6EtiquetasNomes||{};});
    return window._t6EtiquetasPromessa;
  };
  function painelAtual(){try{return window.RouteState?window.RouteState.panel():'inicio';}catch(e){return 'inicio';}}
  window.t6CarregaCadastroBoxes = function(status){
    status=status||(painelAtual()==='boxatual'?'atual':'anterior');
    window._t6BoxStatusPronto=window._t6BoxStatusPronto||{};
    window._t6BoxStatusCarregando=window._t6BoxStatusCarregando||{};
    if(window._t6BoxStatusPronto[status]||window._t6BoxStatusCarregando[status])return;
    window._t6BoxStatusCarregando[status]=true;
    var raiz='https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/';
    var chave='sb_publishable_XTKGboY9RyYiirPiIsWMhw_P8B51cHj';
    var cab={apikey:chave,Authorization:'Bearer '+chave};
    var base=raiz+'boxes?select=id,nome,status,data_lancamento,data_coleta,card_ids'
      +'&status=eq.'+status+'&order=data_lancamento.desc.nullslast,nome.asc';
    fetch(base+'&limit=24',{headers:cab,cache:'no-store'})
    .then(function(r){if(!r.ok)throw new Error('boxes '+r.status);return r.json();})
    .then(function(boxes){
      window.t6MesclaCadastroBoxes(boxes);
      return Promise.all([
        window.t6CarregaRetratosBoxes(boxes),
        window.t6CarregaNomesEtiquetas()
      ]).then(function(){return boxes;});
    }).then(function(boxes){
      window._t6boxesCargaRapida=0;
      function carregaRestante(){
        /* O primeiro quadro ja esta na tela. O cadastro restante chega depois,
           em lotes, sem bloquear a navegacao nem voltar ao "Carregando boxes". */
        setTimeout(function carregaLote(offset){
        fetch(base+'&limit=200&offset='+offset,{headers:cab,cache:'no-store'})
        .then(function(r){if(!r.ok)throw new Error('boxes '+r.status);return r.json();})
        .then(function(lote){
          window.t6MesclaCadastroBoxes(lote);
          return window.t6CarregaRetratosBoxes(lote).then(function(){return lote;});
        }).then(function(lote){
          if((lote||[]).length===200)setTimeout(function(){carregaLote(offset+200);},0);
          else if(painelAtual()==='boxatual'||painelAtual()==='boxant')window.t6Painel(painelAtual());
        }).catch(function(){});
        },0,24);
      }
      window.t6CarregaBoxesPrimeiro(function(){
        window._t6BoxStatusPronto[status]=true;
        window._t6BoxStatusCarregando[status]=false;
        if(painelAtual()==='boxatual'||painelAtual()==='boxant')window.t6Painel(painelAtual());
        carregaRestante();
      });
    }).catch(function(){window._t6BoxStatusCarregando[status]=false;});
  };
  /* As duas abas usam a mesma carga progressiva. A relacao PACOTE informa os
     cards de cada campanha; a aba aberta escolhe atuais ou historicas, pinta
     essa primeira leva e deixa o restante seguir em segundo plano. */
  window.t6CarregaBoxesPrimeiro = function(aoTerminar){
    if(window._t6boxesCargaRapida) return;
    var ativas={}, ids=[], historicas=(painelAtual()==='boxant');
    try{
      var statusDesejado=historicas?'anterior':'atual', meta=window._t6BoxMeta||{};
      Object.keys(meta).forEach(function(nome){
        if(meta[nome].status!==statusDesejado)return;
        /* Big Time é categoria comemorativa do card, não nome de box. Um
           histórico antigo gravou essa coluna como associação e duplicou
           jogadores em boxes fictícias. Ela nunca participa da montagem. */
        if(/^Big Time(?:\s|$)/i.test(nome))return;
        (meta[nome].card_ids||[]).forEach(function(id){ids.push(String(id));});
      });
      /* Compatibilidade somente durante o primeiro instante, antes de o
         cadastro central responder. Depois dele, nenhuma fonte paralela
         decide quais cards pertencem a uma box. */
      if(!ids.length){
        (BOXATIVA||[]).forEach(function(n){ativas[n]=1;});
        Object.keys(PACOTE||{}).forEach(function(id){
          var ehAtiva=!!ativas[PACOTE[id]];
          if(historicas ? !ehAtiva : ehAtiva) ids.push(String(id));
        });
      }
      /* O histórico é a fonte completa da box. Alguns cards antigos não têm
         vínculo em PACOTE; sem esta união eles desaparecem (Living Legends é
         o caso de teste). */
      if (historicas && typeof BOXHIST !== 'undefined'){
        Object.keys(BOXHIST||{}).forEach(function(nome){
          if (ativas[nome]) return;
          if (nome !== 'Living Legends 2026') return;
          var h=BOXHIST[nome]||{};
          (h.ids||[]).forEach(function(id){ ids.push(String(id)); });
        });
      }
    }catch(e){ if(aoTerminar)aoTerminar(); return; }
    if(!ids.length){if(aoTerminar)aoTerminar();return;}
    window._t6boxesCargaRapida=1;
    var lista='("'+ids.join('","')+'")';
    /* ⛔ 25/08 — lista de boxes e ancora do topo: view enxuta (sem arows
       e sem falta). Quem abre a ficha recebe os dois sob demanda. */
    var baseUrl='https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/casa_lista';
    var url=baseUrl
      +'?select=linha&card_id=in.'+encodeURIComponent(lista)
      +(historicas ? '' : '&forca=not.is.null')
      +'&limit=5000';
    /* A recomendacao precisa do lider oficial de cada funcao. Buscar somente
       os cards visiveis transforma o melhor DA TELA em 100%. As linhas com
       maior `forca` sao a ancora persistida pelo banco para conter todos os
       lideres; chegam junto com as boxes e nunca dependem da ordem da tela. */
    var urlTop=baseUrl+'?select=linha&order=forca.desc.nullslast&limit=2000';
    var chave='sb_publishable_XTKGboY9RyYiirPiIsWMhw_P8B51cHj';
    var cab={apikey:chave,Authorization:'Bearer '+chave};
    Promise.all([urlTop,url].map(function(u){
      return fetch(u,{headers:cab}).then(function(r){
        if(!r.ok)throw new Error('HTTP '+r.status);return r.json();
      });
    })).then(function(partes){
       var rows=(partes[0]||[]).concat(partes[1]||[]);
       var tem={};
       (D||[]).forEach(function(c){if(c&&c.id!=='MOLDE')tem[String(c.id).split('@')[0]+'|'+c.tipo]=1;});
       (rows||[]).forEach(function(r){
         var c=r&&r.linha;if(!c||c.id===undefined||c.tipo===undefined)return;
         var k=String(c.id).split('@')[0]+'|'+c.tipo;if(!tem[k]){tem[k]=1;D.push(c);}
       });
       try{if(typeof window._pos_D==='function')window._pos_D();}catch(e){}
       /* Qualquer topo memorizado antes da ancora chegar e provisório. */
       try{if(typeof _TOPO!=='undefined')_TOPO={};}catch(e){}
       if(aoTerminar)aoTerminar();
       else try{if(painelAtual()==='boxatual'||painelAtual()==='boxant')window.t6Painel(painelAtual());}catch(e){}
     }).catch(function(){window._t6boxesCargaRapida=0;if(aoTerminar)aoTerminar();});
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
    if(qual==='boxatual'||qual==='boxant'||qual==='busca'){
      var linhaRanking=document.getElementById('mline');
      if(linhaRanking) linhaRanking.innerHTML='';
    }
    try{if(window.RouteState)window.RouteState.setPanel(qual);}catch(e){}
    if (window._t6pintando) return;      /* nao se chama de dentro de si */
    window._t6pintando = true;
    var h = '';
    try{
    if(qual === 'inicio' && !window.T6HOME_FINAL_PRONTA){
      w.innerHTML = '';
      return;
    }
    try{ homeToggle(1); }catch(e){}
      if (qual === 'boxant')        h = window.t6TelaBoxes(true);
      else if (qual === 'boxatual') h = window.t6TelaBoxes(false);
      else if (qual === 'como')     h = window.t6TelaComo();
      else if (qual === 'ranking')  h = window.t6TelaRanking();
      else if (qual === 'busca')    h = typeof window.t6TelaBusca === 'function' ? window.t6TelaBusca() : '';
      else                          h = window.t6TelaInicio();
    }catch(e){
      h = '';
      if (window.console) console.warn('TELAS_1808: ' + qual + ' falhou —', e);
    }finally{
      window._t6pintando = false;       /* SOLTA SEMPRE */
    }
    /* Se a fonte das Boxes ainda não chegou, a tela anterior não pode ficar
       exposta. Mostra o carregamento da própria aba até a próxima atualização. */
    if (!h || String(h).replace(/<[^>]*>/g,'').trim().length < 3){
      if(qual==='boxatual'||qual==='boxant'){
        h='<div style="min-height:360px;display:flex;align-items:center;justify-content:center;font-size:13px;color:var(--d13)">Carregando '+(qual==='boxatual'?'boxes atuais':'boxes anteriores')+'…</div>';
      }else return;
    }
    w.innerHTML = '<div class="t6tela">' + h + '</div>';
    try{ window.t6Cliques(w); }catch(e){}
    /* Libera o primeiro quadro somente depois que a camada oficial terminou.
       Assim nenhuma estrutura antiga aparece durante a inicializacao. */
    document.documentElement.removeAttribute('data-t6boot');
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
    var troca = raiz.querySelector('[data-t6boxalternar]');
    if (troca) troca.onclick = function(){
      var proxima = painelAtual() === 'boxant' ? 'boxatual' : 'boxant';
      try{if(window.RouteState)window.RouteState.setPanel(proxima);}catch(e){}
      window._t6boxesCargaRapida = 0;
      window.t6Painel(proxima);
      setTimeout(function(){ if(window.t6CarregaBoxesPrimeiro) window.t6CarregaBoxesPrimeiro(); }, 0);
      try{ window.scrollTo(0, 0); }catch(e){}
    };
    raiz.querySelectorAll('[data-t6abrirbox]').forEach(function(el){
      el.onclick=function(ev){ ev.stopPropagation(); window.t6AbreBox(el.dataset.t6abrirbox, el.dataset.t6origem || painelAtual()); };
    });
    var maisBoxes = raiz.querySelector('[data-t6maisboxes]');
    if (maisBoxes){
      var mostrarMais = function(){
        var chave = maisBoxes.getAttribute('data-t6maisboxes');
        var posicaoY = window.pageYOffset || document.documentElement.scrollTop || 0;
        window._t6BoxesVisiveis = window._t6BoxesVisiveis || {atual:24,anterior:24};
        window._t6BoxesVisiveis[chave] = (window._t6BoxesVisiveis[chave] || 24) + 24;
        if (window._t6ObservadorBoxes) window._t6ObservadorBoxes.disconnect();
        window.t6Painel(chave === 'anterior' ? 'boxant' : 'boxatual');
        requestAnimationFrame(function(){
          window.scrollTo(0, posicaoY);
          requestAnimationFrame(function(){ window.scrollTo(0, posicaoY); });
        });
      };
      if ('IntersectionObserver' in window){
        if (window._t6ObservadorBoxes) window._t6ObservadorBoxes.disconnect();
        window._t6ObservadorBoxes = new IntersectionObserver(function(itens){
          if (itens.some(function(item){ return item.isIntersecting; })) mostrarMais();
        }, {rootMargin:'500px 0px'});
        window._t6ObservadorBoxes.observe(maisBoxes);
      } else maisBoxes.onclick = mostrarMais;
    }
    var filtro = raiz.querySelector('[data-t6boxfiltro]');
    if (filtro){
      filtro.value = window._t6FiltroBoxes || '';
      filtro.oninput = function(){
        var valor = filtro.value || '';
        var posicao = typeof filtro.selectionStart === 'number'
          ? filtro.selectionStart : valor.length;
        window._t6FiltroBoxes = valor;
        clearTimeout(window._t6FiltroBoxesTimer);
        window._t6FiltroBoxesTimer = setTimeout(function(){
          window.t6Painel(painelAtual() || 'boxant');
          setTimeout(function(){
            var novoFiltro = document.querySelector('[data-t6boxfiltro]');
            if (!novoFiltro) return;
            novoFiltro.focus();
            try{ novoFiltro.setSelectionRange(posicao, posicao); }catch(e){}
          }, 0);
        }, 180);
      };
    }
    raiz.querySelectorAll('[data-t6boxdata]').forEach(function(el){
      el.value = window[el.getAttribute('data-t6boxdata')] || '';
      /* Campo de data nativo emite eventos antes do ano estar completo em
         alguns navegadores. Redesenhar naquele instante desmontava o input e
         fazia o cursor sair no primeiro dígito. Só aplica uma data completa,
         depois de uma breve pausa — ou quando o campo perde o foco. */
      var aplicaData = function(){
        var chave=el.getAttribute('data-t6boxdata'), valor=el.value || '';
        /* Enquanto o usuário ainda está trocando o ano, Chrome pode expor
           valores como 0002-08-06 e até disparar `change`. Não são uma busca
           válida: só datas completas a partir de 2000 podem redesenhar a tela. */
        if(valor && (!/^\d{4}-\d{2}-\d{2}$/.test(valor) || +valor.slice(0,4)<2000)) return;
        if((window[chave] || '') === valor) return;
        window[chave]=valor;
        window.t6Painel(painelAtual() || 'boxant');
      };
      el.oninput = function(){
        clearTimeout(el._t6dataTimer);
        el._t6dataTimer=setTimeout(aplicaData,900);
      };
      /* Nem `change` nem perda de foco redesenham: o seletor nativo pode
         dispará-los entre os dígitos do ano. O único gatilho é a pausa após
         uma data válida. */
      el.onchange = function(){};
      el.onblur = function(){};
    });
    var voltaBox=raiz.querySelector('[data-t6voltabox]');
    if(voltaBox) voltaBox.onclick=function(){
      var retorno = window._t6BoxRetorno || 'boxatual';
      window.t6Painel(retorno); window.scrollTo(0,0);
    };
  };

  /* ⛔ A TELA JA ABRE NO DESENHO NOVO. Sem esta linha o primeiro desenho era o
     antigo e so trocava depois do primeiro clique numa aba — que foi
     exatamente o "boa parte do site ta operando com design antigo". */
  if(painelAtual()==='boxatual'||painelAtual()==='boxant') setTimeout(window.t6CarregaBoxesPrimeiro,0);

  /* O painel só é desenhado pela navegação ou por carregamento explícito.
     O vigia periódico podia redesenhar uma aba já pronta no meio de outra ação. */

  /* ---------------- BOXES (atuais e anteriores) ---------------- */
  /* O molde e o mesmo da foto 3; o que muda entre as duas abas e o titulo,
     a linha de baixo e quais boxes entram. */
  window.t6TelaBoxes = function(anteriores){
    var statusDesejado=anteriores?'anterior':'atual';
    if (!M || !M['boxes'] || !M['boxes'].corpo){
      try{ if(window.t6CarregaCadastroBoxes) window.t6CarregaCadastroBoxes(statusDesejado); }catch(e){}
      return '<div style="min-height:360px;display:flex;align-items:center;justify-content:center;font-size:13px;color:var(--d13)">Carregando '+(anteriores?'boxes anteriores':'boxes atuais')+'…</div>';
    }
    if (!window._t6BoxStatusPronto || !window._t6BoxStatusPronto[statusDesejado]){
      window.t6CarregaCadastroBoxes(statusDesejado);
      return '<div style="min-height:360px;display:flex;align-items:center;justify-content:center;font-size:13px;color:var(--d13)">Carregando boxes…</div>';
    }
    var cx = window.t6PorBox(), ativas = {}, meta = window._t6BoxMeta || {};
    Object.keys(meta).forEach(function(n){if(meta[n].status==='atual')ativas[n]=1;});
    var nomes = Object.keys(cx).filter(function(n){
      if (n === 'Sem box confirmada') return false;
      if (/^Big Time(?:\s|$)/i.test(n)) return false;
      return !!meta[n] && meta[n].status===statusDesejado;
    });
    /* Nunca apresenta uma lista parcial como se estivesse pronta. A primeira
       leva do banco pode conhecer apenas duas boxes; a tela aguarda a leva
       completa e o redesenho final libera todas de uma vez. */
    var esperadas = 0;
    esperadas = Object.keys(ativas).length;
    /* Não bloqueia a tela aguardando todas as associações. A primeira leva
       aparece imediatamente e o carregamento progressivo completa o restante. */
    /* anteriores: da mais nova para a mais velha, pela data que o historico guarda */
    function quando(n){
      try{
        return (meta[n] && meta[n].data_lancamento) || '';
      }
      catch(e){ return ''; }
    }
    function melhorPct(n){
      var cs = cx[n] || [], melhor = -Infinity;
      for (var i = 0; i < cs.length; i++){
        var p = pct(cs[i]);
        if (isFinite(p) && p > melhor) melhor = p;
      }
      return melhor;
    }
    if (anteriores) nomes.sort(function(a, b){ return (quando(b) || '').localeCompare(quando(a) || ''); });
    else nomes.sort(function(a, b){
      return melhorPct(b) - melhorPct(a) || a.localeCompare(b, 'pt-BR');
    });
    var termo = String(window._t6FiltroBoxes || '').trim().toLocaleLowerCase();
    if (anteriores && termo){
      nomes = nomes.filter(function(n){
        return String(n).toLocaleLowerCase().indexOf(termo) >= 0
          || String(quando(n) || '').toLocaleLowerCase().indexOf(termo) >= 0;
      });
    }
    if (anteriores && (window._t6BoxDataDe || window._t6BoxDataAte)){
      var de = window._t6BoxDataDe ? Date.parse(window._t6BoxDataDe) : -Infinity;
      var ate = window._t6BoxDataAte ? Date.parse(window._t6BoxDataAte + 'T23:59:59') : Infinity;
      nomes = nomes.filter(function(n){
        var t = Date.parse(quando(n));
        return !isNaN(t) && t >= de && t <= ate;
      });
    }
    /* Os dados podem chegar todos em segundo plano, mas o navegador só desenha
       um grupo por vez. Isso evita criar mais de mil boxes no HTML de uma vez. */
    window._t6BoxesVisiveis = window._t6BoxesVisiveis || {atual:24,anterior:24};
    var chaveVisivel = anteriores ? 'anterior' : 'atual';
    var quantas = Math.min(window._t6BoxesVisiveis[chaveVisivel] || 24, nomes.length);
    var dados = {boxesAnt: nomes.slice(0, quantas).map(function(n, idx){
      var cs = cx[n] || [];
      var destaque = !anteriores && idx < 2
        && !(window.matchMedia && window.matchMedia('(max-width:820px)').matches);
      var todos = window.t6Melhores(cs, 9999, n);
      var cards = todos.slice(0, 3).map(window.t6cardBox);
      cards.forEach(function(c){
        c.fotoTam = destaque ? 'width:58px;height:76px;' : (anteriores ? 'width:46px;height:62px;' : 'width:38px;height:50px;');
        c.fotoCol = destaque ? '58px' : (anteriores ? '46px' : '38px');
        c.rowSt = destaque
          ? 'display:flex;align-items:center;gap:11px;'
          : 'display:grid;grid-template-columns:16px ' + c.fotoCol + ' minmax(0,1fr);gap:8px;align-items:center;';
        c.scoreSt = destaque
          ? 'display:flex;flex-direction:column;align-items:flex-end;gap:3px;'
          : 'grid-column:2 / 4;display:grid;grid-template-columns:auto minmax(0,1fr);gap:4px 8px;align-items:center;margin-top:-3px;';
        if (!destaque){
          c.vSt += ';grid-column:1 / 3;justify-self:end';
        }
      });
      return {n: esc(n), data: esc(quando(n)), nomeCru:n, total:todos.length,
              q: todos.length + ' card' + (todos.length === 1 ? '' : 's'),
              colSt: !anteriores ? ('grid-column:span ' + (destaque ? 6 : 4) + ';') : '',
              cards: cards};
    })};
    /* Esta pagina nao passa mais pelo molde antigo. As substituicoes de texto
       eram frageis: pequenas diferencas no molde faziam pontos e recomendacao
       sumirem apenas nas caixas compactas. Uma unica montagem agora entrega o
       HTML final e conserva os mesmos dados, cliques, cores e hierarquia. */
    function cardHtml(c, destaque){
      var foto = '<span data-t6boxfoto="1" style="' + c.fotoTam
        + 'border-radius:8px;background:' + c.foto + ' center/cover no-repeat,'
        + 'linear-gradient(160deg,var(--d33),var(--d32));border:1px solid var(--d7);flex:none;display:block"></span>';
      var info = '<span data-t6boxinfo="1" style="min-width:0;display:flex;flex-direction:column;gap:3px">'
        + '<b style="font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + c.nome + '</b>'
        + '<em style="font-style:normal;font-size:10.5px;color:var(--d13);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + c.est
        + (c.pos ? ' <b style="margin-left:5px;color:var(--d45)">· ' + c.pos + '</b>' : '') + '</em></span>';
      var nota = '<span data-t6score="1" style="display:flex;flex-direction:column;align-items:flex-end;gap:3px;min-width:0">'
        + '<b style="font-family:inherit;font-size:19px;font-weight:700;letter-spacing:-.4px;color:var(--d25);white-space:nowrap">' + c.pts + '</b>'
        + '<em data-t6rec="1" style="font-style:normal;font-family:inherit;font-size:10px;color:var(--d13);white-space:nowrap">Recomendação: ' + c.pct + '%</em>'
        + '<em data-t6veredito="1" style="' + c.vSt + '">' + c.v + '</em></span>';
      if (destaque){
        return '<div data-t6boxlinha="1" data-k="' + c.k + '" style="display:grid;grid-template-columns:18px 58px minmax(0,1fr) auto;gap:11px;align-items:center">'
          + '<span style="font-size:10px;color:var(--d13)">' + c.r + '</span>' + foto + info + nota + '</div>';
      }
      return '<div data-t6boxlinha="1" data-k="' + c.k + '" style="display:grid;grid-template-columns:18px ' + (c.fotoCol || '38px') + ' minmax(0,1fr) auto;gap:8px;align-items:center">'
        + '<span style="font-size:10px;color:var(--d13)">' + c.r + '</span>' + foto + info + nota + '</div>';
    }
    function boxHtml(bx, idx){
      var destaque = !anteriores && idx < 2
        && !(window.matchMedia && window.matchMedia('(max-width:820px)').matches);
      var cards = bx.cards.map(function(c){ return cardHtml(c, destaque); }).join('');
      return '<section data-t6boxcard="1" style="' + bx.colSt
        + 'border-radius:15px;background:linear-gradient(158deg,var(--d42),var(--d43));border:1px solid var(--d20);overflow:hidden">'
        + '<div data-t6boxcab="1" style="display:flex;align-items:center;width:100%;box-sizing:border-box;gap:16px;padding:12px 16px;background:var(--d12);border-bottom:1px solid var(--d7)">'
        + '<b style="font-size:15px;line-height:1.25;min-width:0;flex:1 1 auto;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + bx.n + (bx.data ? '<small style="display:block;margin-top:3px;font-size:11px;color:var(--d13);font-weight:600">' + bx.data + '</small>' : '') + '</b>'
        + '<span style="font-size:10px;line-height:1.25;color:var(--d13);white-space:nowrap;text-align:right;margin-left:auto;flex:0 0 auto">' + bx.q + '</span></div>'
        + '<div style="padding:' + (destaque ? '14px 17px' : '12px 13px') + ';display:flex;flex-direction:column;gap:' + (destaque ? '12px' : '10px') + '">' + cards
        + (bx.total>3?'<button data-t6abrirbox="'+bx.nomeCru.replace(/&/g,'&amp;').replace(/"/g,'&quot;')+'" data-t6origem="'+(anteriores?'boxant':'boxatual')+'" style="margin-top:2px;padding:7px 10px;border-radius:8px;border:1px solid var(--d18);background:var(--d32);color:var(--d30);font:inherit;font-size:11px;cursor:pointer">ver todos os '+bx.total+' cards</button>':'')
        + '</div></section>';
    }
    var titulo = anteriores ? 'BOXES ANTERIORES' : 'BOXES ATUAIS';
    var acao = anteriores ? 'voltar às atuais' : 'ver as anteriores';
    var grade = anteriores ? 'repeat(3,minmax(0,1fr))' : 'repeat(12,minmax(0,1fr))';
    /* Régua de decisão: os mesmos veredictos dos cards, apenas como leitura rápida. */
    var referenciaEtiquetas = '<div data-t6reguaetiquetas="1" aria-label="Etiquetas de contratação" style="display:flex;align-items:center;justify-content:center;gap:6px;flex-wrap:wrap">'
        + '<span style="padding:4px 8px;border-radius:999px;font-size:9px;font-weight:800;white-space:nowrap;color:#eef7ff;background:#1961b5;border:1px solid #73b6ff;box-shadow:0 0 10px rgba(115,182,255,.18)">PAGAR QUALQUER PREÇO</span>'
        + '<span style="padding:4px 8px;border-radius:999px;font-size:9px;font-weight:800;white-space:nowrap;color:#f0fff6;background:#177741;border:1px solid #6ee7a0;box-shadow:0 0 10px rgba(110,231,160,.18)">PAGAR CARO</span>'
        + '<span style="padding:4px 8px;border-radius:999px;font-size:9px;font-weight:900;white-space:nowrap;color:#e8fff0;background:linear-gradient(135deg,rgba(28,158,78,.32),rgba(98,235,141,.48));border:1px solid #98f5bd;box-shadow:0 0 12px rgba(98,235,141,.28)">PAGAR</span>'
        + '<span style="padding:4px 8px;border-radius:999px;font-size:9px;font-weight:800;white-space:nowrap;color:var(--t6-hire-worth-fg);background:var(--t6-hire-worth-bg);border:1px solid var(--t6-hire-worth-bd)">PAGAR POUCO</span>'
        + '<span style="padding:4px 8px;border-radius:999px;font-size:9px;font-weight:800;white-space:nowrap;color:var(--t6-hire-cheap-fg);background:var(--t6-hire-cheap-bg);border:1px solid var(--t6-hire-cheap-bd)">PAGAR MUITO POUCO</span>'
        + '<span style="padding:4px 8px;border-radius:999px;font-size:9px;font-weight:800;white-space:nowrap;color:var(--t6-hire-free-fg);background:var(--t6-hire-free-bg);border:1px solid var(--t6-hire-free-bd)">NÃO PAGAR</span>'
        + '</div>';
    var filtroHtml = anteriores
      ? '<input data-t6boxfiltro placeholder="pesquisar por nome" style="width:125px;padding:8px 9px;border-radius:9px;border:1px solid var(--d18);background:var(--d10);color:var(--d8);font:inherit;font-size:12px">'
        + '<span style="display:flex;flex-direction:column;gap:4px"><input type="date" data-t6boxdata="_t6BoxDataDe" title="data inicial" style="width:110px;padding:5px 7px;border-radius:7px;border:1px solid var(--d18);background:var(--d10);color:var(--d8);font:inherit;font-size:11px"><input type="date" data-t6boxdata="_t6BoxDataAte" title="data final" style="width:110px;padding:5px 7px;border-radius:7px;border:1px solid var(--d18);background:var(--d10);color:var(--d8);font:inherit;font-size:11px"></span>'
      : '';
    var cabecalhoHtml = anteriores
      ? '<div data-t6boxfiltros="1" style="display:grid;grid-template-columns:minmax(130px,1fr) auto minmax(360px,1fr);align-items:center;gap:10px"><h2 style="margin:0;font-size:19px;font-weight:700">' + titulo + '</h2>' + referenciaEtiquetas
        + '<div style="display:flex;justify-content:flex-end;align-items:center;gap:8px;min-width:0">' + filtroHtml + '<button data-t6boxalternar="1" style="border:1px solid var(--d18);background:var(--d32);color:var(--d30);padding:7px 11px;border-radius:9px;cursor:pointer;white-space:nowrap">' + acao + '</button></div></div>'
      : '<div data-t6boxfiltros="1" style="display:grid;grid-template-columns:minmax(150px,1fr) auto minmax(150px,1fr);align-items:center;gap:12px"><h2 style="margin:0;font-size:19px;font-weight:700">' + titulo + '</h2>' + referenciaEtiquetas
        + '<div style="display:flex;justify-content:flex-end;align-items:center;gap:12px;min-width:0">' + filtroHtml + '<button data-t6boxalternar="1" style="border:1px solid var(--d18);background:var(--d32);color:var(--d30);padding:7px 11px;border-radius:9px;cursor:pointer;white-space:nowrap">' + acao + '</button></div></div>';
    var h = '<div style="padding:22px;display:flex;flex-direction:column;gap:16px">'
      + cabecalhoHtml
      + '<div style="display:grid;grid-template-columns:' + grade + ';gap:13px">'
      + dados.boxesAnt.map(boxHtml).join('') + '</div>'
      + (quantas < nomes.length ? '<div data-t6maisboxes="'+chaveVisivel+'" style="height:2px" aria-hidden="true"></div>' : '')
      + '</div>';
    var sub = anteriores
      ? (nomes.length + ' boxes encerradas · top 3 de cada uma · mostrando as '
         + Math.min(quantas, nomes.length) + ' mais recentes')
      : (nomes.length + ' boxes no ar');
    return h;
  };

  window.t6AbreBox = function(nome, origem){
    var w=document.getElementById('homewrap'); if(!w) return;
    window._t6BoxRetorno = origem === 'boxant' ? 'boxant' : 'boxatual';
    var lista=(window.t6PorBox()[nome]||[]), todos=window.t6Melhores(lista,9999,nome);
    function item(c,i,destaque){
      var x=window.t6cardBox(c,i), v=destaque?'width:92px;height:124px':'width:64px;height:86px';
      return '<article data-t6boxitem="1" data-k="'+x.k+'" style="display:grid;grid-template-columns:'+v.split(';')[0].split(':')[1]+' minmax(0,1fr);gap:11px;padding:'+(destaque?'15px':'11px')+';border-radius:13px;border:1px solid var(--d20);background:linear-gradient(158deg,var(--d42),var(--d43));cursor:pointer">'
       +'<span style="'+v+';border-radius:8px;background:'+x.foto+' center/cover no-repeat;border:1px solid var(--d7)"></span>'
       +'<span data-t6boxinfo="1" style="min-width:0;display:flex;flex-direction:column;gap:4px"><b style="font-size:'+(destaque?'15px':'13px')+';white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'+x.nome+'</b><em style="font-style:normal;font-size:11px;color:var(--d13);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'+x.est+' <b style="color:var(--d45)">· '+x.pos+'</b></em><b style="margin-top:auto;font-size:'+(destaque?'20px':'16px')+';color:var(--d25)">'+x.pts+'</b><em style="font-style:normal;font-size:10px;color:var(--d13)">Recomendação: '+x.pct+'%</em><em data-t6veredito="1" style="'+x.vSt+';align-self:flex-start">'+x.v+'</em></span></article>';
    }
    var top=todos.slice(0,3).map(function(c,i){return item(c,i,true)}).join('');
    var resto=todos.slice(3).map(function(c,i){return item(c,i+3,false)}).join('');
    var rotuloVolta = window._t6BoxRetorno === 'boxant' ? '← Boxes anteriores' : '← Boxes atuais';
    var h='<div style="padding:22px;display:flex;flex-direction:column;gap:16px"><div data-t6boxdetcab="1" style="display:flex;align-items:center;gap:12px"><button data-t6voltabox="1" style="padding:7px 11px;border-radius:9px;border:1px solid var(--d18);background:var(--d32);color:var(--d30);cursor:pointer">'+rotuloVolta+'</button><h2 style="margin:0;font-size:19px">'+esc(nome)+'</h2><span data-t6boxq="1" style="margin-left:auto;color:var(--d13);font-size:11px">'+todos.length+' cards</span></div><div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px">'+top+'</div>'+(resto?'<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:11px">'+resto+'</div>':'')+'</div>';
    /* Mantém a aba de origem enquanto o detalhe está aberto. O estado
       `boxdetalhe` fazia o renderizador geral interpretar o primeiro clique
       como uma volta para a página inicial. */
    try{if(window.RouteState)window.RouteState.setPanel(window._t6BoxRetorno || 'boxatual');}catch(e){}
    window._t6BoxDetalhe = true;
    w.innerHTML='<div class="t6tela">'+h+'</div>'; window.t6Cliques(w); window.scrollTo(0,0);
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
  function veredicto(p, congelado, codigoCongelado){
    var C = window.T6_CORTES || [99, 98, 97, 96];
    if (C.length < 4) C = [99, 98, 97, 96];
    var fixo=String(congelado||'').toUpperCase();
    var nomes=window._t6EtiquetasNomes||{};
    function nome(codigo,padrao){return nomes[codigo]||padrao;}
    var codigo=String(codigoCongelado||'');
    if (codigo==='qualquer_preco' || fixo==='PAGAR QUALQUER PREÇO' || fixo==='MELHOR DA FUNÇÃO' || fixo==='TOPO DA FUNÇÃO' || (!codigo && p >= 99.995)) return [nome('qualquer_preco','PAGAR QUALQUER PREÇO'), 'var(--t6-hire-top-fg)', 'var(--t6-hire-top-bg)', 'var(--t6-hire-top-bd)', 'var(--t6-hire-top-sh)'];
    if (codigo==='caro' || fixo==='PAGAR CARO' || fixo==='CONTRATAR A QUALQUER CUSTO') return [nome('caro','PAGAR CARO'), 'var(--t6-hire-any-fg)', 'var(--t6-hire-any-bg)', 'var(--t6-hire-any-bd)'];
    if (codigo==='pagar' || fixo==='PAGAR') return [nome('pagar','PAGAR'), 'var(--t6-hire-pay-fg)', 'var(--t6-hire-pay-bg)', 'var(--t6-hire-pay-bd)', '0 0 12px rgba(98,235,141,.28)'];
    if (codigo==='pouco' || fixo==='PAGAR POUCO' || fixo==='COMPENSA CONTRATAR') return [nome('pouco','PAGAR POUCO'), 'var(--t6-hire-worth-fg)', 'var(--t6-hire-worth-bg)', 'var(--t6-hire-worth-bd)'];
    if (codigo==='muito_pouco' || fixo==='PAGAR MUITO POUCO' || fixo==='CONTRATAR SE FOR BARATO') return [nome('muito_pouco','PAGAR MUITO POUCO'), 'var(--t6-hire-cheap-fg)', 'var(--t6-hire-cheap-bg)', 'var(--t6-hire-cheap-bd)'];
    if (codigo==='nao_pagar' || fixo==='NÃO PAGAR' || fixo==='CONTRATAR SE FOR GRÁTIS') return [nome('nao_pagar','NÃO PAGAR'), 'var(--t6-hire-free-fg)', 'var(--t6-hire-free-bg)', 'var(--t6-hire-free-bd)'];
    if (p >= 99.995) return [nome('qualquer_preco','PAGAR QUALQUER PREÇO'), 'var(--t6-hire-top-fg)', 'var(--t6-hire-top-bg)', 'var(--t6-hire-top-bd)', 'var(--t6-hire-top-sh)'];
    if (p >= C[0]) return [nome('caro','PAGAR CARO'), 'var(--t6-hire-any-fg)', 'var(--t6-hire-any-bg)', 'var(--t6-hire-any-bd)'];
    if (p >= C[1]) return [nome('pagar','PAGAR'), 'var(--t6-hire-pay-fg)', 'var(--t6-hire-pay-bg)', 'var(--t6-hire-pay-bd)', '0 0 12px rgba(98,235,141,.28)'];
    if (p >= C[2]) return [nome('pouco','PAGAR POUCO'), 'var(--t6-hire-worth-fg)', 'var(--t6-hire-worth-bg)', 'var(--t6-hire-worth-bd)'];
    if (p >= C[3]) return [nome('muito_pouco','PAGAR MUITO POUCO'), 'var(--t6-hire-cheap-fg)', 'var(--t6-hire-cheap-bg)', 'var(--t6-hire-cheap-bd)'];
    return [nome('nao_pagar','NÃO PAGAR'), 'var(--t6-hire-free-fg)', 'var(--t6-hire-free-bg)', 'var(--t6-hire-free-bd)'];
  }
  window.t6cardBox = function(c, i){
    var d = window.t6card(c, i), p = parseFloat(d.pct),
        v = veredicto(p, c&&c._t6Congelado&&c._t6Congelado.etiqueta,
                      c&&c._t6Congelado&&c._t6Congelado.etiqueta_codigo);
    d.foto = 'url(' + url(c) + ')';
    d.v = v[0];
    d.vSt = 'font-style:normal;font-family:inherit;font-size:8.5px;font-weight:700;'
          + 'letter-spacing:.7px;padding:3px 7px;border-radius:999px;white-space:nowrap;'
          + 'color:' + v[1] + ';background:' + v[2] + ';border:1px solid ' + v[3]
          + (v[4] ? ';box-shadow:' + v[4] : '');
    return d;
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

  /* FICHA_STATE_5 — domínio separado da rota. É o único dono de card,
     função, modo da Ficha e sessão transitória de Editar. */
  (function instalaFichaState(){
    if(window.FichaState) return;
    function partes(key){var s=String(key||''),i=s.indexOf('|');return i<0?[s,'']:[s.slice(0,i),s.slice(i+1)];}
    function normalizaModo(m){m=String(m||'motor').toLowerCase();if(m==='insumos')m='livre';return m==='editar'?'editar':(m==='livre'?'livre':'motor');}
    var estado={aberta:false,key:null,cardId:null,funcao:null,modo:'motor',
      edicao:null,buildExibida:null,contextoBuild:'max',transicoes:0};
    function modoUI(){return estado.modo==='editar'?'livre':estado.modo;}
    function espelha(){
      try{document.documentElement.setAttribute('data-encmodo',modoUI());}catch(e){}
      try{if(document.body)document.body.setAttribute('data-encmodo',modoUI());}catch(e){}
    }
    function usaChave(key){
      if(!key)return;var p=partes(key);estado.key=String(key);estado.cardId=String(p[0]||'').split('@')[0];estado.funcao=p[1]||null;
    }
    function defineModo(m,key){
      m=normalizaModo(m);var mudou=estado.modo!==m;
      if(key&&estado.key!==String(key))mudou=true;
      estado.modo=m;usaChave(key);if(m!=='editar')estado.edicao=null;
      if(m==='motor'){estado.buildExibida=null;estado.contextoBuild='max';}
      else if(m==='livre')estado.contextoBuild='draft';
      if(mudou)estado.transicoes++;espelha();return true;
    }
    function abre(key){var mudou=!estado.aberta||estado.key!==String(key||'');estado.aberta=true;usaChave(key);if(mudou)estado.transicoes++;espelha();return true;}
    function fecha(){var mudou=estado.aberta||estado.key||estado.modo!=='motor'||estado.edicao||estado.buildExibida;estado.aberta=false;estado.key=null;estado.cardId=null;estado.funcao=null;estado.modo='motor';estado.edicao=null;estado.buildExibida=null;estado.contextoBuild='max';if(mudou)estado.transicoes++;espelha();return true;}
    function iniciaNova(key,opcoes){var mudou=estado.modo!=='livre'||estado.edicao||estado.buildExibida||estado.key!==String(key||'');estado.modo='livre';estado.edicao=null;estado.buildExibida=null;estado.contextoBuild=opcoes&&opcoes.kind==='base'?'base':'draft';usaChave(key);if(mudou)estado.transicoes++;espelha();return true;}
    function iniciaEdicao(meta,key){if(!meta)return false;estado.modo='editar';estado.edicao={};Object.keys(meta).forEach(function(k){estado.edicao[k]=meta[k];});estado.buildExibida=meta.buildId?{buildId:String(meta.buildId),cardId:String(meta.idb||''),functionId:meta.func||null}:null;estado.contextoBuild='saved';usaChave(key||((meta.idb||'')+'|'+(meta.func||'')));estado.transicoes++;espelha();return true;}
    function encerraEdicao(){var tinha=!!estado.edicao||estado.modo==='editar';estado.edicao=null;if(estado.modo==='editar')estado.modo='livre';estado.contextoBuild=estado.buildExibida?'saved':'draft';if(tinha)estado.transicoes++;espelha();return tinha;}
    function edicao(){return estado.edicao;}
    function mostraBuild(meta,key){if(!meta||!meta.buildId)return false;estado.buildExibida={buildId:String(meta.buildId),cardId:String(meta.cardId||meta.idb||estado.cardId||''),functionId:meta.functionId||meta.func||estado.funcao||null};estado.contextoBuild='saved';usaChave(key);return true;}
    function buildMostrada(){return estado.buildExibida?Object.assign({},estado.buildExibida):null;}
    function inspeciona(){return {aberta:estado.aberta,key:estado.key,cardId:estado.cardId,
      funcao:estado.funcao,modo:estado.modo,modoUI:modoUI(),edicao:estado.edicao,
      buildExibida:buildMostrada(),contextoBuild:estado.contextoBuild,
      transicoes:estado.transicoes};}
    var api=Object.freeze({setMode:defineModo,open:abre,close:fecha,
      beginNew:iniciaNova,startEdit:iniciaEdicao,finishEdit:encerraEdicao,
      editSession:edicao,showSavedBuild:mostraBuild,displayedBuild:buildMostrada,
      mode:function(){return estado.modo;},uiMode:modoUI,
      inspect:inspeciona});
    window.FichaState=api;espelha();
  })();

  /* QUAL ABA DO CARD ESTA ABERTA — leitura canônica da Ficha. */
  window.t6Modo = function(){
    try{return window.FichaState?window.FichaState.uiMode():'motor';}
    catch(e){return 'motor';}
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
  function agrupaFerramentasBuild(raiz){
    if(!raiz)return false;
    var maximo=raiz.querySelector('.t6modo-max');
    var atual=raiz.querySelector('[data-t6-builds-salvas]');
    var nova=raiz.querySelector('.t6modo-build');
    var elenco=raiz.querySelector('[data-t6-add-elenco]');
    var melhora=raiz.querySelector('.t6modo-melhora');
    var funcao=raiz.querySelector('.t6modo-funcao');
    var host=maximo&&maximo.parentElement;
    if(!maximo||!atual||!nova||!host
       ||atual.parentElement!==host||nova.parentElement!==host)return false;
    if(host.querySelector('[data-t6-build-ferramentas]'))return true;

    /* O estado do card e da build vem primeiro. Os tres dados pertencem a uma
       unica faixa; nenhum deles fica solto na borda direita do painel. */
    if(elenco&&melhora&&funcao&&elenco.parentElement===host
       &&melhora.parentElement===host&&funcao.parentElement===host){
      var status=document.createElement('div');
      status.className='t6build-status';
      status.setAttribute('data-t6-build-status','1');
      host.insertBefore(status,maximo);
      status.appendChild(elenco);status.appendChild(melhora);status.appendChild(funcao);
    }

    var grupo=document.createElement('div');
    grupo.className='t6build-ferramentas';
    grupo.setAttribute('data-t6-build-ferramentas','1');
    var titulo=document.createElement('span');
    titulo.className='t6build-ferramentas-titulo';
    titulo.setAttribute('data-t6-build-ferramentas-titulo','1');
    titulo.textContent='FERRAMENTAS DE BUILD';
    grupo.appendChild(titulo);
    host.insertBefore(grupo,maximo);
    host.classList.add('t6build-tools-host');

    function rotula(controle,classe,rotulo,principal){
      controle.classList.add('t6build-ferramenta',classe);
      while(controle.firstChild)controle.removeChild(controle.firstChild);
      var contexto=document.createElement('span');
      contexto.className='t6build-ferramenta-rotulo';
      contexto.textContent=rotulo;
      var nome=document.createElement('span');
      nome.className='t6build-ferramenta-principal';
      nome.textContent=principal;
      controle.appendChild(contexto);controle.appendChild(nome);
      controle.setAttribute('aria-label',rotulo+'. '+principal);
    }
    rotula(maximo,'t6build-ferramenta-premium','REFERÊNCIA IDEAL','MELHOR BUILD POSSÍVEL');
    atual.classList.add('t6build-ferramenta','t6build-ferramenta-atual');
    rotula(nova,'t6build-ferramenta-nova','COMEÇAR DO ZERO','CRIAR NOVA BUILD');
    grupo.appendChild(maximo);grupo.appendChild(atual);grupo.appendChild(nova);
    return true;
  }

  function desenhaFichaView(key){
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
        /* Este terceiro controle era apenas o "i" informativo. Marca-o
           já na montagem para que a ficha sempre o converta no acesso às
           builds salvas, independente da estrutura interna do template. */
        modos.children[2].classList.remove('t6modo-info');
        modos.children[2].classList.add('t6modo-builds');
        modos.children[2].setAttribute('data-t6-builds-salvas', '1');
        modos.children[2].textContent = 'BUILDS SALVAS';
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
    try{
      if(window.ElencoAddController&&typeof window.ElencoAddController.mountFichaButton==='function')
        window.ElencoAddController.mountFichaButton(box,key);
    }catch(e){}
    try{ agrupaFerramentasBuild(box); }catch(e){}
    var ov = document.getElementById('ov');
    if (ov) ov.style.display = 'block';
    var vb = document.getElementById('voltar');
    if (vb) vb.style.display = 'block';
    document.body.classList.add('naficha');
    try{
      if (typeof window.t6PaginaAtiva === 'function') window.t6PaginaAtiva(key);
    }catch(e){}
    return true;
  }

  /* FICHA_CONTROLLER_4 — dono estável do lifecycle aprovado. */
  function criaFichaController(desenhar){
    var estado={key:null,aberta:false,ocupado:false,transicoes:0,desenhos:0,
      fechamentos:0,pedidos:0,ultimoMotivo:null};
    function transita(motivo,key,preparar){
      key=String(key||'');
      if(!key || estado.ocupado) return false;
      var sx=0,sy=0;
      try{ sx=window.scrollX||0; sy=window.scrollY||0; }catch(e){}
      estado.ocupado=true;
      try{
        var portas=window.FichaLifecyclePorts,rotas=window.RouteState;
        if(!estado.aberta && rotas && typeof rotas.captureFichaOrigin==='function'){
          rotas.captureFichaOrigin();
        }else if(!estado.aberta && portas && typeof portas.captureOrigin==='function'){
          portas.captureOrigin();
        }
        if(preparar && preparar(key)===false) return false;
        estado.transicoes++;
        if(desenhar(key)!==true) return false;
        estado.key=key; estado.aberta=true; estado.desenhos++;
        try{if(window.FichaState)window.FichaState.open(key);}catch(e){}
        estado.ultimoMotivo=motivo;
        try{ window.scrollTo(sx,sy); }catch(e){}
        return true;
      }catch(e){
        window._T6_ERRO_DESENHO=key+' :: '+(e&&e.message||e);
        return false;
      }finally{
        estado.ocupado=false;
      }
    }
    function preparaMaximo(key){
      try{
        if(String(window._CHAVE_ABERTA||'')!==key){
          window._CHAVE_ABERTA=key; window._GRAU_COND=1;
        }
        if(String(window._ULTK||'')!==key){
          window._SELPOS=null; window._ULTK=key;
        }
      }catch(e){}
      try{if(window.FichaState)window.FichaState.setMode('motor');}catch(e){}
      window._BLD_FOTO=null; window.BLD_SEM_LACO=1;
      try{
        if(typeof window.t6RestauraMotor==='function'
           && window.t6RestauraMotor(key)===false) return false;
      }catch(e){ return false; }
      finally{ window.BLD_SEM_LACO=0; }
      return true;
    }
    function abreFuncao(key){ return transita('funcao',key,preparaMaximo); }
    function reabre(key){ return transita('redesenho',key,null); }
    function abreBuildSalva(key){ return transita('build-salva',key,null); }
    function chaveInicialDoCard(base,keySugerida){
      var primeira=null, inicial=null;
      try{
        primeira=(typeof D!=='undefined'?D:[]).find(function(x){
          return x && x.id!=='MOLDE' && String(x.id).split('@')[0]===base;
        });
        if(primeira && typeof window.t6InicialDaPosicaoNativa==='function'){
          inicial=window.t6InicialDaPosicaoNativa(primeira);
        }
      }catch(e){}
      if(inicial) return inicial.id+'|'+inicial.tipo;
      if(primeira) return primeira.id+'|'+primeira.tipo;
      return String(keySugerida||'');
    }
    /* Um unico resolvedor decide o estado inicial de TODO clique em card.
       A fonte do usuario e uma porta somente leitura; Auth/Supabase futuros
       substituem essa porta, nao esta regra. Builds legadas sem timestamp
       usam a ordem persistida: criacao anexa ao fim e edicao preserva lugar. */
    function resolveEntradaCard(base,keySugerida,referenciaOcorrencia){
      var maxKey=chaveInicialDoCard(base,keySugerida),port=window.FichaUserStatePort;
      var foto=null,builds=[],ocorrencias=[];
      try{foto=port&&typeof port.snapshotCard==='function'
        ?port.snapshotCard(base,referenciaOcorrencia||null):null;}catch(e){foto=null;}
      if(foto){builds=Array.isArray(foto.builds)?foto.builds:[];
        ocorrencias=Array.isArray(foto.occurrences)?foto.occurrences:[];}
      function achaBuild(id){
        id=String(id||'').trim(); if(!id)return null;
        for(var i=0;i<builds.length;i++)if(String(builds[i]&&builds[i].buildId||'').trim()===id)return builds[i];
        return null;
      }
      function planoBuild(b,source){
        if(!b||!b.buildId||!String(b.functionId||'').trim())return null;
        return {kind:'saved',source:source,cardId:String(base),buildId:String(b.buildId),
          key:String(base)+'|'+String(b.functionId)};
      }
      if(referenciaOcorrencia){
        var exata=foto&&foto.requestedOccurrence;
        if(!exata)return {kind:'invalid-occurrence',source:'team',cardId:String(base),key:maxKey};
        var idLinhaExata=String(exata.cardKey||'').split('|')[0]||String(base);
        if(String(exata.buildId||'').trim()==='base'&&String(exata.functionId||'').trim())
          return {kind:'base',source:'team-occurrence',cardId:String(base),buildId:'base',
            occurrence:exata,key:idLinhaExata+'|'+String(exata.functionId)};
        var buildExata=achaBuild(exata.buildId),planoExato=planoBuild(buildExata,'team-occurrence');
        if(planoExato){planoExato.occurrence=exata;
          planoExato.key=idLinhaExata+'|'+String(buildExata.functionId||buildExata.func);return planoExato;}
        return {kind:'invalid-occurrence',source:'team',cardId:String(base),key:maxKey};
      }
      if(ocorrencias.length===1){
        var o=ocorrencias[0];
        if(String(o.buildId||'')==='base' && String(o.functionId||'').trim())
          return {kind:'base',source:'team',cardId:String(base),buildId:'base',
            key:String(base)+'|'+String(o.functionId)};
        var aplicada=achaBuild(o.buildId),pa=planoBuild(aplicada,'team');
        if(pa)return pa;
      }else if(ocorrencias.length>1){
        /* Estado legado ambiguo nao e apagado nem arbitrado durante abertura. */
        try{console.error('Ficha: card duplicado no Elenco; build aplicada ignorada',base,ocorrencias);}catch(e){}
      }
      /* Sem timestamp escrito pelo fluxo vigente, a ordem do array e o
         contrato estavel. Entradas invalidas sao ignoradas de tras para frente. */
      for(var i=builds.length-1;i>=0;i--){var p=planoBuild(builds[i],'latest-saved');if(p)return p;}
      return {kind:'max',source:'native',cardId:String(base),buildId:null,key:maxKey};
    }
    function preparaEntradaCard(key){
      var base=String(key||'').split('|')[0].split('@')[0];
      if(base && base!==String(window._CARTA_ABERTA||'')){
        window._CARTA_ABERTA=base; window._BLD_ZERADA=null; window._BLD_FOTO=null;
      }
      return true;
    }
    function carregaEAbre(base,keySugerida,motivo,resolverClique,referenciaOcorrencia){
      base=String(base||'').split('@')[0];
      if(!base) return false;
      var pedido=++estado.pedidos;
      function conclui(){
        if(pedido!==estado.pedidos) return false;
        var plano=resolverClique?resolveEntradaCard(base,keySugerida,referenciaOcorrencia||null):null;
        if(plano&&plano.kind==='invalid-occurrence')return false;
        var key=plano&&plano.key?plano.key:chaveInicialDoCard(base,keySugerida);
        if(!key) return false;
        preparaEntradaCard(key);
        if(plano&&plano.kind!=='max'){
          var port=window.FichaUserStatePort;
          return transita(motivo,key,function(){
            return !!(port&&typeof port.prepareInitial==='function'&&port.prepareInitial(plano)===true);
          });
        }
        return transita(motivo,key,preparaMaximo);
      }
      var carga;
      try{ carga=_t6CompletaFuncoesDoCard(base); }
      catch(e){ window._T6_ERRO_CARGA_CARD=base+' :: '+(e&&e.message||e); return false; }
      if(carga && typeof carga.then==='function'){
        return carga.then(conclui,function(e){
          window._T6_ERRO_CARGA_CARD=base+' :: '+(e&&e.message||e); return false;
        });
      }
      return conclui();
    }
    function abreCard(key){
      var s=String(key||''), base=s.split('|')[0].split('@')[0];
      return carregaEAbre(base,s,'abrir-card',true);
    }
    function abreOcorrencia(key,referencia){
      var s=String(key||''),base=s.split('|')[0].split('@')[0];
      if(!referencia||String(referencia.cardKey||'')!==s)return false;
      return carregaEAbre(base,s,'abrir-ocorrencia',true,referencia);
    }
    function reabreDaRota(id){ return carregaEAbre(id,'','f5',false); }
    function limpaEstadoEfemero(){
      window.BLD_SUJO=0;try{if(window.FichaState)window.FichaState.close();}catch(e){}
      try{ delete window.BLD_EDICAO_CANCELADA; }catch(e){ window.BLD_EDICAO_CANCELADA=null; }
      window._CHAVE_ABERTA=null; window._GRAU_COND=1;
      window._CARTA_ABERTA=null; window._BLD_ZERADA=null; window._BLD_FOTO=null;
    }
    function limpaRotaFicha(){
      try{
        var u=new URL(location.href);
        ['card','funcao','modo'].forEach(function(p){ u.searchParams.delete(p); });
        var atual=history.state||{}, st={};
        Object.keys(atual).forEach(function(k){
          if(k!=='ficha' && k!=='paginaCard' && k!=='key') st[k]=atual[k];
        });
        history.replaceState(st,'',u.pathname+u.search+u.hash);
      }catch(e){}
    }
    function finalizaFechamento(restaurar,popstate){
      var portas=window.FichaLifecyclePorts,rotas=window.RouteState;
      var visivel=portas&&typeof portas.isOpen==='function' ? portas.isOpen() : estado.aberta;
      if((!estado.aberta && !visivel) || estado.ocupado || !portas
         || typeof portas.closeUI!=='function') return false;
      estado.ocupado=true;
      try{
        var origem=typeof portas.origin==='function' ? portas.origin() : null;
        estado.transicoes++; estado.fechamentos++; estado.ultimoMotivo='fechar';
        limpaEstadoEfemero();
        portas.closeUI();
        try{ if(typeof window.t6PaginaDesativa==='function') window.t6PaginaDesativa(); }catch(e){}
        estado.key=null; estado.aberta=false;
        if(rotas && typeof rotas.afterFichaClosed==='function'){
          if(typeof portas.clearOrigin==='function') portas.clearOrigin();
          rotas.afterFichaClosed(restaurar!==false,!!popstate);
        }else{
          if(!popstate) limpaRotaFicha();
          if(restaurar && typeof portas.restoreOrigin==='function') portas.restoreOrigin();
          else if(typeof portas.clearOrigin==='function') portas.clearOrigin();
          if(restaurar && origem && origem.tela && origem.tela!=='meutime'){
            try{ if(typeof window.t6RegistraRota==='function') window.t6RegistraRota(origem.tela); }catch(e){}
          }
        }
        return true;
      }finally{
        estado.ocupado=false;
      }
    }
    function fecha(restaurar){
      if(window.BLD_SUJO){
        try{
          if(!window.confirm("Voc\u00ea mexeu na carta e n\u00e3o salvou.\n\n"
            +"Fechar assim descarta o que voc\u00ea montou.")) return false;
        }catch(e){}
      }
      return finalizaFechamento(restaurar!==false,false);
    }
    function trataPopstate(){ return finalizaFechamento(true,true); }
    function inspeciona(){ return {
      key:estado.key,aberta:estado.aberta,ocupado:estado.ocupado,
      transicoes:estado.transicoes,desenhos:estado.desenhos,
      fechamentos:estado.fechamentos,pedidos:estado.pedidos,
      ultimoMotivo:estado.ultimoMotivo
    }; }
    return Object.freeze({openFunction:abreFuncao,reopen:reabre,
      openCard:abreCard,openOccurrence:abreOcorrencia,openFromRoute:reabreDaRota,
      openSavedBuild:abreBuildSalva,close:fecha,resolveInitial:resolveEntradaCard,
      handlePopState:trataPopstate,inspect:inspeciona});
  }
  function instalaFichaController(){
    if(window.FichaController) return window.FichaController;
    var controller=criaFichaController(desenhaFichaView);
    window.FichaController=controller;
    /* Compatibilidade sem segundo dono: os dois nomes apontam para a mesma
       função estável do controlador e não oferecem fallback legado. */
    window.t6DesenhaFicha=controller.reopen;
    window.t6ReabreFicha=controller.reopen;
    window.abrir=controller.openCard;
    window.reabrir=controller.reopen;
    window.fechar=controller.close;
    return controller;
  }
  instalaFichaController();

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

  /* A Ficha não nasce pela metade. O controller aguarda esta carga pontual,
     deduplicada por card, antes do único desenho. Esta rotina só prepara os
     dados; nunca abre, reabre ou agenda outra tentativa. */
  function _t6CompletaFuncoesDoCard(entrada){
    if (typeof D === 'undefined') return false;
    var base = String(entrada && typeof entrada==='object' ? entrada.id : entrada || '').split('@')[0];
    if (!base || !/^\d+$/.test(base)) return false;
    window._T6_CARGA_CARD = window._T6_CARGA_CARD || {};
    window._T6_CARGA_CARD_PROMESSA = window._T6_CARGA_CARD_PROMESSA || {};
    if (window._T6_CARGA_CARD[base] === 'pronto') return true;
    if (window._T6_CARGA_CARD_PROMESSA[base]) return window._T6_CARGA_CARD_PROMESSA[base];
    window._T6_CARGA_CARD[base] = 'carregando';
    window._T6_BONUS_POS = window._T6_BONUS_POS || {};
    window._T6_BONUS_POS_CARGA = window._T6_BONUS_POS_CARGA || {};
    window._T6_BONUS_POS_PROMESSA = window._T6_BONUS_POS_PROMESSA || {};
    var cargaBonus;
    if(window._T6_BONUS_POS_CARGA[base]==='pronto') cargaBonus=Promise.resolve(true);
    else if(window._T6_BONUS_POS_PROMESSA[base]) cargaBonus=window._T6_BONUS_POS_PROMESSA[base];
    else{
      window._T6_BONUS_POS_CARGA[base] = 'carregando';
      var ubp = 'https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/bonus_posicao'
        + '?select=card_id,funcao,posicao,estilo_ativo,b_estilo,b_total,nota&card_id=eq.'
        + encodeURIComponent(base);
      var kbp = 'sb_publishable_XTKGboY9RyYiirPiIsWMhw_P8B51cHj';
      cargaBonus=window._T6_BONUS_POS_PROMESSA[base]=fetch(ubp,{headers:{apikey:kbp,Authorization:'Bearer '+kbp}})
       .then(function(r){ if(!r.ok) throw new Error('HTTP '+r.status); return r.json(); })
       .then(function(rows){
         (rows||[]).forEach(function(z){
           window._T6_BONUS_POS[z.card_id+'|'+z.funcao+'|'+z.posicao]=z;
         });
         window._T6_BONUS_POS_CARGA[base]='pronto';
         delete window._T6_BONUS_POS_PROMESSA[base]; return true;
       },function(e){
         window._T6_BONUS_POS_CARGA[base]='erro';
         delete window._T6_BONUS_POS_PROMESSA[base]; throw e;
       });
    }
    /* ⛔ ESTA CONTINUA NA `casa_tela` (a linha inteira): e UM card so,
       custa poucos KB, e assim o card aberto por aqui ja chega com
       `arows` e `falta` dentro — sem depender do sob demanda. */
    var url = 'https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/casa_tela'
      + '?select=linha&card_id=eq.' + encodeURIComponent(base) + '&order=funcao.asc';
    var chave = 'sb_publishable_XTKGboY9RyYiirPiIsWMhw_P8B51cHj';
    var cargaLinhas=fetch(url, {headers:{apikey:chave, Authorization:'Bearer ' + chave}})
      .then(function(r){ if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function(rows){
        (rows || []).forEach(function(r){
          var x = r && r.linha;
          if (!x || x.id === undefined || x.tipo === undefined) return;
          var xb = String(x.id).split('@')[0], repetida = false;
          for (var di = 0; di < D.length; di++){
            var ja = D[di];
            if (ja && ja.id !== 'MOLDE' && String(ja.id).split('@')[0] === xb
                && _mesmaFn(ja.tipo, x.tipo)){
              try{
                if(_notaDoMotor(x)>_notaDoMotor(ja)) D[di]=x;
              }catch(e){}
              repetida = true; break;
            }
          }
          if (!repetida) D.push(x);
        });
        return true;
      });
    var carga=Promise.all([cargaLinhas,cargaBonus]).then(function(){
      try{ if (typeof _pos_D === 'function') _pos_D(); }catch(e){}
      window._T6_CARGA_CARD[base] = 'pronto';
      delete window._T6_CARGA_CARD_PROMESSA[base];
      return true;
    },function(e){
        window._T6_CARGA_CARD[base] = 'erro';
        delete window._T6_CARGA_CARD_PROMESSA[base];
        throw e;
      });
    window._T6_CARGA_CARD_PROMESSA[base]=carga;
    return carga;
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

    /* Quando a Ficha nasce de uma ocorrência do Elenco, a fotografia da
       build já foi aplicada antes deste único desenho. A linha destacada da
       função precisa mostrar essa mesma nota; usar _notaDoMotor aqui fazia o
       total dizer Teste 2/110,50 e a própria função continuar em 110,69.
       As outras funções (e toda abertura comum) preservam a referência fixa. */
    var projetaNotaDaOcorrencia=false;
    try{
      var estadoFichaAplicada=window.FichaState&&window.FichaState.inspect
        ?window.FichaState.inspect():null;
      var buildFichaAplicada=window.FichaState&&window.FichaState.displayedBuild
        ?window.FichaState.displayedBuild():null;
      projetaNotaDaOcorrencia=!!(estadoFichaAplicada
        &&estadoFichaAplicada.contextoBuild==='saved'&&buildFichaAplicada
        &&String(buildFichaAplicada.cardId||'')===base
        &&(_mesmaFn(buildFichaAplicada.functionId,c.tipo)
          ||_nomeFn(buildFichaAplicada.functionId)===_nomeFn(c.tipo)));
    }catch(e){projetaNotaDaOcorrencia=false;}
    function notaVisivelDaFuncao(x,pos){
      var mesma=projetaNotaDaOcorrencia&&x
        &&(_mesmaFn(x.tipo,c.tipo)||_nomeFn(x.tipo)===_nomeFn(c.tipo));
      if(mesma){
        try{
          var aplicada=nota(c);
          if(pos)aplicada=_ajustaNotaNaPos(c,pos,aplicada);
          if(typeof aplicada==='number'&&isFinite(aplicada))return aplicada;
        }catch(e){}
      }
      return pos?_notaDoMotorPos(x,pos):_notaDoMotor(x);
    }

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
                ? notaVisivelDaFuncao(x,window._T6SELPOS_FORCADA) : notaVisivelDaFuncao(x,null)),
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

    /* Falso Nove e Atacante Infiltrador só se dividem quando a mesma função
       muda de resultado conforme a posição. Uma linha única esconderia essa
       diferença e mostraria uma nota indevida para as duas posições. */
    var fnsSeparadas = [];
    fnsW.forEach(function(r, i){
      var x = irm[i], ps = _posDaFuncao(x.tipo, c);
      if (!ps.length) ps = _posFn(x);
      var mistas = ps.length > 1
        && ps.some(function(p){ return _estiloLigaNaPos(x,p) === false; })
        && ps.some(function(p){ return _estiloLigaNaPos(x,p) === true; });
      var nomeVariante = _nomeFn(x.tipo);
      var podeSeparar = nomeVariante === 'Falso Nove'
        || nomeVariante === 'Atacante Infiltrador';
      if (!podeSeparar || !mistas){
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
        /* A posição já aparece na etiqueta própria; o nome continua sendo o
           da função real, sem juntar duas variantes em uma mesma linha. */
        nr.n = esc(nomeVariante);
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
        nr.pts = n2(notaVisivelDaFuncao(x,p));
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
    /* As variantes por posição entram depois da ordenação original. Reordena
       as linhas finais para a nota maior continuar sempre acima. */
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
      function nomeImpetoNoGrau(nome){
        return /^Motor do Time(?:\s*\+\s*[123])?$/i.test(String(nome||'').trim())
          ? 'Motor do Time +' + grauAtual : nome;
      }
      function ehMotorDoTime(nome){
        return /^Motor do Time(?:\s*\+\s*[123])?$/i.test(String(nome||'').trim());
      }

      var E_CARD = 'background:var(--d12);border:1px solid var(--d7);border-radius:12px;'
                 + 'padding:11px 13px;display:flex;flex-direction:column;gap:7px';
      var E_LINHA = 'display:flex;align-items:center;gap:9px';
      var E_BADGE = 'margin-left:auto;font-family:inherit;font-size:14px;font-weight:700;'
                  + 'padding:2px 9px;border-radius:7px;background:var(--d33);'
                  + 'border:1px solid var(--d11);color:var(--d1)';
      var E_FILA = 'display:flex;flex-wrap:wrap;gap:5px';

      function cartao(nome, rotulo, ef, extra, semSeloDeGrau, acoesCabecalho){
        return '<div style="' + E_CARD + '">'
          + '<div style="' + E_LINHA + '">'
          +   '<b style="font-size:13.5px">' + esc(_extenso(nome)) + '</b>'
          +   '<span style="font-weight:400;font-size:11px;color:var(--d17)">' + rotulo + '</span>'
          +   (acoesCabecalho || '')
          +   (!semSeloDeGrau && _grau(ef) ? '<b style="' + E_BADGE + '">' + _grau(ef) + '</b>' : '')
          + '</div>'
          + (ef && ef.length ? '<div style="' + E_FILA + '">' + _chips(ef) + '</div>' : '')
          + (extra || '')
          + '</div>';
      }

      var condHtml = '';
      var condBotoesCabecalho = '';
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
        condBotoesCabecalho = '<span style="display:flex;gap:5px;margin-left:auto">' + bts + '</span>';
        condHtml = '<div style="display:flex;align-items:center;gap:9px;'
          + 'border-top:1px solid var(--d15);padding-top:9px;margin-top:2px">'
          + '<span style="display:flex;align-items:center;gap:6px;font-family:inherit;font-size:9px;'
          +   'letter-spacing:1.2px;color:var(--d120)">'
          +   '<i style="width:10px;height:10px;background:var(--d120);display:block;'
          +   'clip-path:polygon(50% 0,100% 25%,100% 75%,50% 100%,0 75%,0 25%)"></i>ÍMPETO CONDICIONAL</span>'
          + condBotoesCabecalho + '</div>';
      }

      var novo = h.slice(abCab, fim1);   /* o rotulo ÍMPETO fica como ela desenhou */
      if (nativos.length){
        nativos.forEach(function(x, ix){
          var _motorDoTime = ehMotorDoTime(x.nome);
          novo += cartao(_motorDoTime ? 'Motor do Time' : nomeImpetoNoGrau(x.nome), 'nativo', x.ef,
            '', true, _motorDoTime ? condBotoesCabecalho : '');
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
      } else if (nativos.length < 2) {
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
  window.t6PedeNomeBuild = function(sugestao, conclui, opcoes){
    opcoes = opcoes || {};
    var antiga = document.getElementById('t6nomebuild');
    if (antiga) antiga.remove();
    var fundo = document.createElement('div');
    fundo.id = 't6nomebuild';
    fundo.setAttribute('role', 'dialog');
    fundo.setAttribute('aria-modal', 'true');
    fundo.setAttribute('aria-label', opcoes.edicao ? 'Salvar alterações da build' : 'Salvar build');
    fundo.style.cssText = 'position:fixed;inset:0;z-index:100000;display:grid;place-items:center;'
      + 'background:rgba(0,0,0,.62);padding:18px';
    fundo.innerHTML = '<div data-build-caixa style="width:min(390px,100%);background:var(--d4);color:var(--d1);'
      + 'border:1px solid var(--d31);border-radius:14px;padding:18px;box-shadow:0 18px 60px #0008">'
      + '<div style="font-size:13px;font-weight:900;margin-bottom:10px">NOME DA BUILD</div>'
      + (opcoes.mensagem ? '<div style="margin:-2px 0 11px;font-size:11.5px;line-height:1.45;color:var(--d17)">' + String(opcoes.mensagem).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') + '</div>' : '')
      + '<input data-nome-build maxlength="60" style="box-sizing:border-box;width:100%;padding:11px 12px;'
      + 'border-radius:9px;border:1px solid var(--d31);background:var(--d5);color:var(--d1);font:inherit;outline-color:var(--d25)">'
      + '<div data-erro-build role="alert" style="display:none;margin-top:8px;font-size:11.5px;line-height:1.4;color:#ffb5a5"></div>'
      + '<div style="display:flex;justify-content:flex-end;gap:8px;margin-top:14px">'
      + '<button type="button" data-cancela style="padding:9px 14px;border-radius:8px;border:1px solid var(--d31);'
      + 'background:transparent;color:var(--d30);font-weight:800;cursor:pointer">CANCELAR</button>'
      + '<button type="button" data-confirma style="padding:9px 14px;border-radius:8px;border:1px solid var(--d25);'
      + 'background:var(--d25);color:#06200f;font-weight:900;cursor:pointer">'
      + (opcoes.edicao ? 'SALVAR ALTERAÇÕES' : 'SALVAR') + '</button></div></div>';
    document.body.appendChild(fundo);
    var inp = fundo.querySelector('[data-nome-build]');
    var erro = fundo.querySelector('[data-erro-build]');
    inp.value = sugestao || '';
    var estado = 'formulario';
    function limpaErro(){ erro.textContent = ''; erro.style.display = 'none'; }
    function mostraErro(txt){
      erro.textContent = txt;
      erro.style.display = 'block';
      inp.focus();
      inp.select();
    }
    function cancela(){
      if (estado !== 'formulario') return;
      estado = 'fechado';
      fundo.remove();
      if (typeof conclui === 'function') conclui(null);
      if (typeof opcoes.aoCancelar === 'function') opcoes.aoCancelar();
    }
    function mostraSucesso(){
      estado = 'sucesso';
      var caixa = fundo.querySelector('[data-build-caixa]');
      caixa.setAttribute('aria-live', 'polite');
      caixa.innerHTML = '<div data-build-sucesso style="display:flex;flex-direction:column;gap:8px">'
        + '<strong style="font-size:15px;color:var(--d25)">Build salva e disponível no Elenco.</strong>'
        + '<span style="font-size:12px;line-height:1.5;color:var(--d30)">No Elenco, a pontuação total pode ser diferente se o técnico do time não for o mesmo usado nesta build. Seus insumos serão preservados.</span>'
        + '<div style="display:flex;justify-content:flex-end;margin-top:8px">'
        + '<button type="button" data-conclui style="padding:9px 16px;border-radius:8px;border:1px solid var(--d25);'
        + 'background:var(--d25);color:#06200f;font-weight:900;cursor:pointer">CONCLUIR</button></div></div>';
      var concluir = caixa.querySelector('[data-conclui]');
      concluir.onclick = function(){
        if (estado !== 'sucesso') return;
        estado = 'fechado'; fundo.remove();
        if (typeof opcoes.aoConcluirSucesso === 'function') opcoes.aoConcluirSucesso();
      };
      setTimeout(function(){ concluir.focus(); }, 0);
    }
    function salva(){
      if (estado !== 'formulario' || typeof conclui !== 'function') return;
      var resposta = false;
      limpaErro();
      try{ resposta = conclui(inp.value); }catch(e){ resposta = false; }
      if (resposta === true) mostraSucesso();
      else if (resposta && resposta.erro) mostraErro(String(resposta.erro));
    }
    fundo.querySelector('[data-cancela]').onclick = cancela;
    fundo.querySelector('[data-confirma]').onclick = salva;
    fundo.onclick = function(e){ if (e.target === fundo) cancela(); };
    fundo.onkeydown = function(e){ if (e.key === 'Escape') cancela(); };
    inp.oninput = limpaErro;
    inp.onkeydown = function(e){
      if (e.key === 'Enter') salva();
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

  /* O select da ficha aplica o vetor canônico uma única vez. Não passa por
     wrappers legados de `trocaTec`, que podiam atualizar só o nome exibido. */
  window.t6Tec = function(key, idx){
    var c = null;
    try{ c = _card(key); }catch(e){}
    if (!c) return;
    try{ _marca(key); }catch(e){}
    var _t = (idx === '' || idx === null || idx === undefined || typeof TECS === 'undefined')
      ? null : (TECS[+idx] || null);
    var alvo = _t ? _t[0] : '';
    c._tecNome = alvo;
    c._tec = (_t && _t[1]) ? _t[1].slice() : [];
    try{ c.TECB = c._tec.slice(); }catch(e){ c.TECB = []; }
    try{ delete c._cp; delete c._n; }catch(e){}
    try{ _grava(c, _lvlDe(c)); }catch(e){}
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
    if(window.FichaState&&window.FichaState.mode()==='editar'){
      alert('Nesta edição, a função da build fica travada. Para mudar a função, crie uma nova build.');
      return;
    }
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
    if(!destino || !window.FichaController) return false;
    return window.FichaController.openFunction(destino);
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
    /* Entrada explícita em "Fazer minha build" inicia uma build nova.
       Se havia uma sessão de edição, ela é descartada sem alterar a build
       persistida; assim o salvar normal jamais sobrescreve a entrada antiga. */
    if(window.FichaState)window.FichaState.beginNew(destino);
    delete window.BLD_EDICAO_CANCELADA;
    window._BLD_FOTO = null;
    window._T6_COPIOU_MAX = window._T6_COPIOU_MAX || {};
    delete window._T6_COPIOU_MAX[String(destino).split('|')[0].split('@')[0]];
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

  /* Qualquer escolha explícita de função abre o Máximo possível dela. A aba
     Fazer minha build só inicia a carta-base quando a própria aba é clicada. */
  window.t6AbreFuncao = function(destino){
    /* Só durante uma edição salva: não deixa trocar a identidade da build
       por engano. Fora dessa sessão, o fluxo normal continua livre. */
    var ed = window.FichaState?window.FichaState.editSession():null, partes = String(destino || '').split('|');
    if(ed && String(ed.idb) === String(partes[0]).split('@')[0] && String(ed.func) !== String(partes[1])){
      alert('Nesta edição, a função da build fica travada. Para mudar a função, crie uma nova build.');
      try{ window.t6ReabreFicha(String(ed.idb)+'|'+ed.func); }catch(e){}
      return;
    }
    window.t6AbreMaximo(destino);
  };

  /* ⛔ A VIDA DOS BOTOES — cada um chama a MESMA funcao da casca. */
  window.t6FichaCliques = function(raiz, key){
    if (!raiz) return;
    function todos(sel){ return [].slice.call(raiz.querySelectorAll(sel)); }
    function buildCarregadaDaFicha(idb){
      var exibida=null, lista=[];
      try{ exibida=window.FichaState&&window.FichaState.displayedBuild?window.FichaState.displayedBuild():null; }catch(e){}
      if(!exibida||!exibida.buildId||String(exibida.cardId||'')!==String(idb||''))return null;
      try{ lista=(MT&&MT.builds&&Array.isArray(MT.builds[idb]))?MT.builds[idb]:[]; }catch(e){ lista=[]; }
      for(var bi=0;bi<lista.length;bi++){
        if(lista[bi]&&String(lista[bi].buildId||'')===String(exibida.buildId))
          return {build:lista[bi],buildId:String(exibida.buildId),indice:bi};
      }
      return null;
    }
    function estadoDoControleDeBuild(ativa){
      var contexto='max';
      try{
        var ficha=window.FichaState&&window.FichaState.inspect?window.FichaState.inspect():null;
        contexto=ficha&&ficha.contextoBuild?String(ficha.contextoBuild):contexto;
      }catch(e){}
      if(window.BLD_SUJO||contexto==='draft')
        return {tipo:'draft',rotulo:'BUILD ATUAL',principal:'NÃO SALVA',secundario:null};
      if(ativa)
        return {tipo:'saved',rotulo:'BUILD ATUAL',principal:String(ativa.build.nome||'build'),secundario:null};
      if(contexto==='base')
        return {tipo:'base',rotulo:'BUILD ATUAL',principal:'BÁSICA',secundario:null};
      if(contexto==='max')
        return {tipo:'max',rotulo:'BUILD ATUAL',principal:'MELHOR BUILD POSSÍVEL',secundario:null};
      return {tipo:'invalid',rotulo:'BUILD ATUAL',principal:'BUILD NÃO IDENTIFICADA',secundario:null};
    }
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
      try{ if(window.FichaState)window.FichaState.setMode(m,key); }catch(e){}
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
    /* No lugar do "i" sem ação fica o acesso às builds desta carta. */
    try{
      var _maxModo = [].slice.call(raiz.querySelectorAll('button')).filter(function(bt){
        return (bt.textContent || '').trim() === '⚡ MÁXIMO POSSÍVEL';
      })[0] || porTexto('⚡ MÁXIMO POSSÍVEL')[0], _linhaModo = _maxModo;
      for (var _mi=0; _mi<4 && _linhaModo; _mi++){
        var _temManual = [].slice.call(_linhaModo.children || []).some(function(filho){
          return (filho.textContent || '').indexOf('FAZER MINHA BUILD') >= 0;
        });
        if (_temManual) break;
        _linhaModo = _linhaModo.parentNode;
      }
      var _alvosBuilds = [].slice.call(raiz.querySelectorAll('[data-t6-builds-salvas]'));
      if (!_alvosBuilds.length && _linhaModo) _alvosBuilds = [].slice.call(_linhaModo.children || []).filter(function(filho){
        return (filho.textContent || '').trim() === 'i';
      });
      todos('[data-t6-build-ativa-nome]').forEach(function(indicador){ indicador.remove(); });
      _alvosBuilds.forEach(function(filho){
        filho.classList.remove('t6modo-info');
        filho.classList.add('t6modo-builds','t6build-controle');
        filho.setAttribute('data-t6-builds-salvas', '1');
        var idbFicha=String(key).split('|')[0].split('@')[0], ativaFicha=buildCarregadaDaFicha(idbFicha);
        var estadoControle=estadoDoControleDeBuild(ativaFicha);
        filho.setAttribute('data-t6-build-estado',estadoControle.tipo);
        if(ativaFicha&&estadoControle.tipo==='saved')filho.setAttribute('data-build-id',ativaFicha.buildId);
        else filho.removeAttribute('data-build-id');
        while(filho.firstChild)filho.removeChild(filho.firstChild);
        if(estadoControle.rotulo){
          var rotulo=document.createElement('span');
          rotulo.setAttribute('data-t6-build-controle-rotulo','1');
          rotulo.textContent=estadoControle.rotulo;
          filho.appendChild(rotulo);
        }
        var principal=document.createElement('span');
        principal.setAttribute('data-t6-build-controle-principal','1');
        principal.textContent=estadoControle.principal;
        filho.appendChild(principal);
        if(estadoControle.secundario){
          var secundario=document.createElement('span');
          secundario.setAttribute('data-t6-build-controle-secundario','1');
          secundario.textContent=estadoControle.secundario;
          filho.appendChild(secundario);
        }
        filho.title=estadoControle.tipo==='draft'?'salve a build antes de escolher outra':'ver e escolher as builds salvas desta carta';
        filho.setAttribute('aria-label',(estadoControle.rotulo?estadoControle.rotulo+'. ':'')
          +estadoControle.principal+(estadoControle.secundario?'. '+estadoControle.secundario:''));
        filho.setAttribute('role','button');filho.tabIndex=0;
        filho.style.cssText='cursor:pointer;font-family:inherit;padding:9px 13px;border-radius:8px;'
          +'border:1px solid var(--d31);background:var(--d14);color:var(--d8)';
        filho.onclick = function(ev){
          if (ev){ ev.preventDefault(); ev.stopPropagation(); }
          if(window.BLD_SUJO){
            try{ alert('Você mexeu na carta e não salvou.\n\nSalve antes de escolher outra build.'); }catch(e){}
            return false;
          }
          var idb = String(key).split('|')[0].split('@')[0], lista = [];
          try{ lista = (MT && MT.builds && Array.isArray(MT.builds[idb])) ? MT.builds[idb] : []; }catch(e){}
          var ativaNoModal=buildCarregadaDaFicha(idb);
          var anterior = document.querySelector('[data-t6modal-builds]');
          if (anterior) anterior.remove();
          var fundo = document.createElement('div');
          fundo.setAttribute('data-t6modal-builds', '1');
          fundo.style.cssText = 'position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;'
            + 'padding:20px;background:rgba(0,0,0,.68);backdrop-filter:blur(4px)';
          var painel = document.createElement('div');
          painel.style.cssText = 'width:min(480px,100%);max-height:min(70vh,620px);overflow:auto;box-sizing:border-box;'
            + 'padding:18px;border-radius:14px;background:#101713;border:1px solid rgba(177,255,204,.34);'
            + 'box-shadow:0 22px 60px rgba(0,0,0,.5);color:var(--d1);font-family:inherit';
          var cab = document.createElement('div');
          cab.style.cssText = 'display:flex;align-items:center;gap:12px;margin-bottom:12px';
          cab.innerHTML = '<b style="font-size:14px">BUILDS SALVAS</b><span style="font-size:11px;color:var(--d17)">'
            + lista.length + '/30</span>';
          var fecharModal = document.createElement('button');
          fecharModal.type = 'button'; fecharModal.textContent = '×'; fecharModal.title = 'fechar';
          fecharModal.style.cssText = 'margin-left:auto;width:30px;height:30px;border-radius:8px;cursor:pointer;'
            + 'border:1px solid var(--d31);background:var(--d14);color:var(--d1);font:800 18px/1 inherit';
          fecharModal.onclick = function(){ fundo.remove(); };
          cab.appendChild(fecharModal); painel.appendChild(cab);
          if (!lista.length){
            var vazio = document.createElement('p');
            vazio.textContent = 'Ainda não há builds salvas para esta carta.';
            vazio.style.cssText = 'margin:0;color:var(--d17);font-size:12px';
            painel.appendChild(vazio);
          } else {
            /* A apresentação é sempre por pontuação decrescente. O índice
               original é mantido para ativar exatamente a build escolhida. */
            lista.map(function(build, indice){ return { build: build, indice: indice }; })
              .sort(function(a, b){ return (+b.build.n || 0) - (+a.build.n || 0); })
              .forEach(function(item){
              var build = item.build, indice = item.indice;
              var opcao = document.createElement('div');
              opcao.setAttribute('role', 'button'); opcao.tabIndex = 0;
              opcao.style.cssText = 'display:flex;align-items:center;gap:8px;width:100%;margin-top:7px;padding:10px 11px;box-sizing:border-box;'
                + 'text-align:left;cursor:pointer;border-radius:9px;border:1px solid var(--d31);'
                + 'background:var(--d14);color:var(--d1);font-family:inherit';
              var estaAtiva=!!(ativaNoModal&&String(build.buildId||'')===ativaNoModal.buildId);
              if(estaAtiva){
                opcao.setAttribute('data-t6-build-ativa','1');
                opcao.setAttribute('aria-current','true');
                opcao.style.borderColor='rgba(177,255,204,.72)';
                opcao.style.background='rgba(33,72,48,.42)';
              }
              var texto = document.createElement('b');
              texto.style.cssText = 'flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap';
              texto.textContent = String(build.nome || ('build ' + (indice + 1)));
              var nota = document.createElement('span');
              nota.style.cssText = 'font-weight:800;color:var(--d25)'; nota.textContent = n2(+build.n || 0);
              var seloAtiva=null;
              if(estaAtiva){
                seloAtiva=document.createElement('span');
                seloAtiva.textContent='ATIVA';
                seloAtiva.style.cssText='flex:0 0 auto;padding:3px 6px;border-radius:999px;background:var(--d25);'
                  + 'color:#06200f;font:900 9px/1 inherit;letter-spacing:.35px';
              }
              var acoes = document.createElement('span');
              acoes.style.cssText = 'display:flex;gap:5px;flex:0 0 auto';
              function acao(txt, titulo){
                var bt = document.createElement('button'); bt.type = 'button'; bt.textContent = txt; bt.title = titulo;
                bt.style.cssText = 'padding:5px 7px;border-radius:6px;cursor:pointer;font:800 10px/1 inherit;'
                  + 'border:1px solid var(--d31);background:#101713;color:var(--d8)';
                bt.onclick = function(ev){ ev.preventDefault(); ev.stopPropagation(); };
                return bt;
              }
              var editar = acao('EDITAR', 'editar esta build');
              editar.onclick = function(ev){
                ev.preventDefault(); ev.stopPropagation();
                var ok=false; try{ ok=(typeof window.bldEdita === 'function') && window.bldEdita(idb, indice, key); }catch(e){}
                if(ok) fundo.remove();
              };
              var excluir = acao('EXCLUIR', 'excluir esta build');
              excluir.style.color = '#ffb5a5';
              excluir.onclick = function(ev){
                ev.preventDefault(); ev.stopPropagation();
                var ok=false; try{ ok=(typeof window.bldApaga === 'function') && window.bldApaga(idb, indice); }catch(e){}
                if(ok){ fundo.remove(); try{ window.FichaController.reopen(key); }catch(e){} }
              };
              acoes.appendChild(editar); acoes.appendChild(excluir);
              opcao.appendChild(texto); opcao.appendChild(nota); if(seloAtiva)opcao.appendChild(seloAtiva); opcao.appendChild(acoes);
              function usarBuild(){
                try{ if (typeof window.bldUsa === 'function') window.bldUsa(idb, indice); }catch(e){}
                fundo.remove();
              }
              opcao.onclick = usarBuild;
              opcao.onkeydown = function(ev){ if(ev.key === 'Enter' || ev.key === ' '){ ev.preventDefault(); usarBuild(); } };
              painel.appendChild(opcao);
            });
          }
          fundo.onclick = function(ev){ if (ev.target === fundo) fundo.remove(); };
          fundo.appendChild(painel); document.body.appendChild(fundo);
        };
        filho.onkeydown=function(ev){
          if(ev&&(ev.key==='Enter'||ev.key===' ')){ev.preventDefault();filho.onclick(ev);}
        };
      });
    }catch(e){}
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
      linha.setAttribute('data-t6controles-funcao', '1');
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
      var salvas = [], ativa = -1, TETO = 30;
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
      var _edAtual=window.FichaState&&window.FichaState.editSession();
      var emEdicao = !!(_edAtual && String(_edAtual.idb) === idb);
      bSalvar.textContent = emEdicao ? '✔ SALVAR ALTERAÇÕES' : '✔ SALVAR MINHA BUILD';
      bSalvar.title = emEdicao ? 'atualiza esta mesma build' : 'guarda esta build no seu elenco';
      bSalvar.style.cssText = E_BT + 'background:var(--d25);border-color:var(--d25);color:#06200f';
      bSalvar.onclick = function(){
        try{
          if (emEdicao && typeof window.bldSalva === 'function') return window.bldSalva();
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
        try{ if(typeof window.bldCopiaDoMaximo==='function' && window.bldCopiaDoMaximo(key)!==false) return; }catch(e){}
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

      /* Linha única de ações da aba manual. Ela é o único lugar que recebe
         Otimizar, Salvar, Copiar e Limpar: não há lista, resumo ou rodapé de
         builds abaixo dela. */
      if (botaoOti && botaoOti.parentNode){
        var linhaAcoes = document.createElement('div');
        linhaAcoes.setAttribute('data-t6bld', '1');
        linhaAcoes.setAttribute('data-t6controles-build', '1');
        linhaAcoes.style.cssText = 'display:flex;gap:8px;align-items:stretch;flex-wrap:wrap;margin-top:10px';
        botaoOti.parentNode.insertBefore(linhaAcoes, botaoOti);
        botaoOti.style.width = 'auto';
        botaoOti.style.flex = '1 1 200px';
        botaoOti.style.margin = '0';
        linhaAcoes.appendChild(botaoOti);
        [bSalvar,bCopiar,bLimpar].forEach(function(bt){ bt.style.flex = '0 0 auto'; linhaAcoes.appendChild(bt); });
        return;
      }

      /* ⛔ o OTIMIZAR nao se repete aqui: ele e o botao grande do fim do
         bloco das barras, e ja usa os insumos que estao na tela. */
      linha.appendChild(bSalvar); linha.appendChild(bCopiar); linha.appendChild(bLimpar);
      bar.appendChild(linha);

      var txt = document.createElement('div');
      txt.style.cssText = 'font-size:11.5px;line-height:1.35;color:var(--d30);padding:1px 2px';
      txt.setAttribute('data-t6bld-resumo', '1');
      bar.appendChild(txt);

      /* Esta lista precisa ser refeita depois de salvar: a build fica gravada
         imediatamente, mas a ficha aberta nao pode continuar mostrando a
         colecao antiga. A atualizacao abaixo so troca resumo e etiquetas. */
      var chips = document.createElement('div');
      chips.setAttribute('data-t6bld-lista', '1');
      chips.style.cssText = 'display:flex;gap:7px;align-items:center;flex-wrap:nowrap;min-width:0;overflow:hidden';
      bar.appendChild(chips);
      function atualizaListaBuildsDaFicha(){
        var estado = null, lista = [], indice = -1;
        try{
          estado = (typeof MT !== 'undefined') ? MT : null;
          lista = (estado && estado.builds && Array.isArray(estado.builds[idb]))
            ? estado.builds[idb] : [];
          indice = (estado && estado.buildOn && estado.buildOn[idb] !== undefined)
            ? estado.buildOn[idb] : -1;
        }catch(e){}
        txt.innerHTML = 'vai salvar como <b style="color:var(--d1)">'
          + esc(_nomeFn(c ? c.tipo : '')) + '</b> · '
          + lista.length + ' de ' + TETO + ' builds guardadas desta carta';
        chips.innerHTML = '';
        function poeEtiqueta(b, i){
          var ch = document.createElement('span');
          var on = (i === indice);
          ch.style.cssText = 'display:flex;align-items:center;gap:7px;font-size:11px;font-weight:700;'
            + (lista.length > 3 ? 'flex:1 1 0;width:0;' : '')
            + 'min-width:0;max-width:180px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'
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
        }
        /* Uma linha so: mantem a ativa sempre visivel e envia o restante
           para o seletor, sem alargar nem empurrar a ficha. */
        var visiveis = lista.map(function(item, i){ return { item:item, i:i }; }).slice(0, 3);
        if (indice >= 3){
          visiveis = lista.slice(0, 2).map(function(item, i){ return { item:item, i:i }; });
          visiveis.push({ item:lista[indice], i:indice });
        }
        visiveis.forEach(function(reg){ poeEtiqueta(reg.item, reg.i); });
        var vistos = {};
        visiveis.forEach(function(reg){ vistos[reg.i] = 1; });
        var demais = lista.map(function(item, i){ return { item:item, i:i }; })
          .filter(function(reg){ return !vistos[reg.i]; });
        if (demais.length){
          var verMais = document.createElement('select');
          verMais.title = 'ver e selecionar as demais builds';
          verMais.style.cssText = 'flex:0 0 auto;min-width:0;max-width:190px;font-family:inherit;font-size:11px;font-weight:800;padding:5px 9px;'
            + 'border-radius:8px;cursor:pointer;background:var(--d14);border:1px solid var(--d31);color:var(--d25)';
          verMais.innerHTML = '<option value="">ver mais builds (' + demais.length + ')</option>'
            + demais.map(function(reg){
              return '<option value="' + reg.i + '">' + esc(String(reg.item.nome || ('build ' + (reg.i + 1))))
                + ' · ' + n2(+reg.item.n || 0) + '</option>';
            }).join('');
          verMais.onchange = function(){
            if (verMais.value === '') return;
            try{ if (typeof window.bldUsa === 'function') window.bldUsa(idb, +verMais.value); }catch(e){}
          };
          chips.appendChild(verMais);
        }
      }
      window.t6AtualizaListaBuilds = function(cardId){
        if (String(cardId) !== idb || !bar.isConnected) return;
        atualizaListaBuildsDaFicha();
      };
      atualizaListaBuildsDaFicha();

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

  window.t6Melhores = function(lista, quantos, nomeBox){
    var meta=(window._t6BoxMeta||{})[nomeBox], retratos=window._t6BoxRetratos||{};
    if(meta && meta.status==='anterior'){
      var vistos={};
      (lista||[]).forEach(function(c){
        var cid=String(c.id).split('@')[0], s=retratos[String(meta.id)+'|'+cid];
        if(!s)return;
        var atual=vistos[cid];
        if(!atual || String(c.tipo)===String(s.funcao)){
          var copia=Object.assign({},c);
          copia._t6Congelado=s;
          copia._t6PtsExibida=Number(s.pontuacao);
          vistos[cid]=copia;
        }
      });
      return Object.keys(vistos).map(function(k){return vistos[k];}).sort(function(a,b){
        return Number(b._t6Congelado.recomendacao)-Number(a._t6Congelado.recomendacao)
          || Number(b._t6Congelado.pontuacao)-Number(a._t6Congelado.pontuacao);
      }).slice(0,quantos||3);
    }
    var por = {};
    lista.forEach(function(c){
      var k = c.nome, v = nota(c), r = pct(c);
      /* Cada função tem uma âncora diferente. Portanto, a maior nota absoluta
         não é necessariamente o melhor desempenho relativo. A recomendação
         vem do maior percentual entre as funções, enquanto o número grande
         mostra a maior nota real que existe na ficha daquele card. */
      if(!por[k])por[k]=[c,v,r,v];
      else{
        if(v>por[k][3])por[k][3]=v;
        if(r>por[k][2] || (r===por[k][2] && v>por[k][1])){por[k][0]=c;por[k][1]=v;por[k][2]=r;}
      }
    });
    return Object.keys(por).map(function(k){ return por[k]; })
      .sort(function(a, b){
        return b[2] - a[2] || b[1] - a[1];
      })
      .slice(0, quantos || 3).map(function(x){
        var copia=Object.assign({},x[0]);copia._t6PtsExibida=x[3];return copia;
      });
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
  var marcaExternaDaFicha = null;

  var css = document.createElement('style');
  css.textContent = [
    'html[data-t6pagina="card"],html[data-t6pagina="card"] body{min-height:100%;background:var(--d3,#07100b)}',
    'html[data-t6pagina="card"] body{overflow:auto!important}',
    'html[data-t6pagina="card"] #filtros,html[data-t6pagina="card"] body>main{display:none!important}',
    'html[data-t6pagina="card"] #ov{position:relative!important;inset:auto!important;display:block!important;',
      'z-index:1!important;overflow:visible!important;min-height:calc(100vh - 72px);padding:20px 18px 92px!important;',
      'background:var(--d3,#07100b)!important}',
    'html[data-t6pagina="card"] #box{max-width:1240px;margin:0 auto}',
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
    /* A URL é rota da Ficha, não memória do editor: F5 mantém o card, mas
       sempre reinicia na função nativa e no Máximo possível. */
    u.searchParams.delete('funcao');
    u.searchParams.delete('modo');
    return u.pathname+u.search+u.hash;
  }
  function ativa(key){
    if(!key) return;
    var jaEstavaNaFicha=document.documentElement.getAttribute('data-t6pagina')==='card';
    /* A ficha já traz a marca dentro da própria moldura. A cópia da barra
       global não entra na página de detalhe. */
    var marca=document.getElementById('t6logo');
    if(marca && marca.parentNode){
      marcaExternaDaFicha=marca;
      marca.parentNode.removeChild(marca);
    }
    document.documentElement.setAttribute('data-t6pagina','card');
    try{ document.body.setAttribute('data-t6pagina','card'); }catch(e){}
    if(window.RouteState&&typeof window.RouteState.enterFicha==='function'){
      window.RouteState.enterFicha(String(key));
    }
    /* So a entrada vinda da home comeca no topo. Trocar funcao, posicao ou
       aba dentro da ficha conserva exatamente o ponto de leitura. */
    if(!jaEstavaNaFicha) try{ window.scrollTo(0,0); }catch(e){}
  }
  function desativa(){
    document.documentElement.removeAttribute('data-t6pagina');
    try{ document.body.removeAttribute('data-t6pagina'); }catch(e){}
    /* Ao voltar para as páginas principais, a mesma marca retorna à barra. */
    if(marcaExternaDaFicha){
      var barra=document.getElementById('t6bar'), abas=document.getElementById('t6tabs');
      if(barra) barra.insertBefore(marcaExternaDaFicha, abas||barra.firstChild);
      marcaExternaDaFicha=null;
    }
  }
  window.t6PaginaAtiva=ativa;
  window.t6PaginaDesativa=desativa;

  function abreDaUrl(){
    var q=new URLSearchParams(location.search), id=q.get('card');
    try{
      var rotaNoBoot=localStorage.getItem('clubefutebol_aba_atual')||'';
      if(rotaNoBoot && rotaNoBoot!=='ficha') return;
    }catch(e){}
    if(!id) return;
    var controller=window.FichaController;
    if(!controller || typeof controller.openFromRoute!=='function') return;
    controller.openFromRoute(String(id).split('@')[0]);
  }

  /* O boot pertence ao RouteState. Esta função fica disponível somente como
     adaptação de leitura; não há uma segunda restauração durante o load. */
  window.t6AbreFichaDaUrl=abreDaUrl;
})();
