/* bloco JavaScript 32 */

/* ROUTE_STATE_5 — dono único da rota, URL e histórico.
   A página desenha; esta porta decide a transição e registra uma única entrada. */
(function instalaRouteState(){
  if(window.RouteState) return;
  var CHAVE='clubefutebol_aba_atual', ESTAVEL='clubefutebol_aba_estavel';
  var ROTAS_BASE={inicio:1,meutime:1,ranking:1,boxatual:1,boxant:1,ficha:1};
  var VALIDAS={inicio:1,meutime:1,ranking:1,boxatual:1,boxant:1,ficha:1};
  /* Hierarquia visual canônica: estas análises são páginas próprias, mas
     continuam pertencendo à aba global Elenco. O mapa não registra nem abre
     rotas; apenas restaura a aba-pai quando alguma delas estiver disponível. */
  var FILHAS_ELENCO={melhorfuncao:1,timefraco:1,melhorformacao:1,tecnicotime:1,comparartime:1};
  var CHAVE_ESTADO_PAGINA='t6PageState', LIMITE_ESTADO_PAGINA=65536;
  var PAGINAS=Object.create(null);
  var NOMES={Inicio:'inicio',MeuTime:'meutime',Ranking:'ranking',BoxAtual:'boxatual',BoxAnt:'boxant'};
  function slugPagina(v){
    var s=String(v||'').trim().toLowerCase();
    return /^[a-z][a-z0-9-]{2,39}$/.test(s)?s:'';
  }
  /* Extensão canônica para páginas próprias. O módulo declara sua página antes
     de restore() (ou em T6_ROUTE_DEFINITIONS antes deste arquivo carregar), e
     RouteState continua sendo o único dono de persistência/history/render. */
  function registraPagina(rota,def){
    rota=slugPagina(rota);def=def||{};
    if(!rota||ROTAS_BASE[rota]||PAGINAS[rota]||typeof def.render!=='function')return false;
    var retorno=String(def.returnRoute||'meutime').toLowerCase();
    if(!ROTAS_BASE[retorno]||retorno==='ficha')retorno='meutime';
    PAGINAS[rota]=Object.freeze({route:rota,returnRoute:retorno,render:def.render});
    VALIDAS[rota]=1;
    return true;
  }
  try{
    var declaradas=window.T6_ROUTE_DEFINITIONS;
    if(declaradas&&typeof declaradas==='object')Object.keys(declaradas).forEach(function(rota){
      registraPagina(rota,declaradas[rota]);
    });
  }catch(e){}
  function normaliza(v){
    v=NOMES[v]||String(v||'').toLowerCase();
    if(v==='elenco') v='meutime';
    if(v==='boxes-atuais') v='boxatual';
    if(v==='boxes-anteriores') v='boxant';
    return VALIDAS[v]?v:null;
  }
  function le(k){try{return localStorage.getItem(k)||'';}catch(e){return '';}}
  function grava(k,v){try{localStorage.setItem(k,v);}catch(e){}}
  var inicial=normaliza(le(CHAVE))||'inicio';
  var estavel=normaliza(le(ESTAVEL));
  if(!estavel||estavel==='ficha') estavel=inicial!=='ficha'?inicial:'inicio';
  function painelDaRota(rota){return rota==='boxatual'||rota==='boxant'?rota:(rota==='inicio'?'inicio':null);}
  var estado={atual:inicial,estavel:estavel,painel:painelDaRota(inicial)||'inicio',origem:null,transicoes:0,
    commits:0,restaurado:false,emTransicao:0,fichaPendente:null,fichaCard:null};
  var retornoFichaPendente=null;
  function persiste(rota){
    grava(CHAVE,rota);
    if(rota!=='ficha'){estado.estavel=rota;grava(ESTAVEL,rota);}
  }
  function urlPrincipal(){
    var u=new URL(location.href);
    ['card','funcao','modo'].forEach(function(p){u.searchParams.delete(p);});
    return u.pathname+u.search+u.hash;
  }
  function partes(key){var s=String(key||''),i=s.indexOf('|');return i<0?[s,'']:[s.slice(0,i),s.slice(i+1)];}
  function jsonPrivadoValido(valor,pilha,profundidade){
    if(valor===null)return true;
    var tipo=typeof valor;
    if(tipo==='string'||tipo==='boolean')return true;
    if(tipo==='number')return isFinite(valor);
    if(tipo!=='object'||profundidade>12)return false;
    if(pilha.indexOf(valor)>=0)return false;
    var lista=Array.isArray(valor);
    if(!lista){
      try{if(Object.prototype.toString.call(valor)!=='[object Object]')return false;}catch(e){return false;}
    }
    pilha.push(valor);
    var chaves=Object.keys(valor),ok=true;
    for(var i=0;i<chaves.length;i++){
      if(!jsonPrivadoValido(valor[chaves[i]],pilha,profundidade+1)){ok=false;break;}
    }
    pilha.pop();return ok;
  }
  function copiaEstadoPagina(valor){
    if(!valor||typeof valor!=='object'||Array.isArray(valor)||!jsonPrivadoValido(valor,[],0))return null;
    try{
      var texto=JSON.stringify(valor);
      if(!texto||texto.length>LIMITE_ESTADO_PAGINA)return null;
      return JSON.parse(texto);
    }catch(e){return null;}
  }
  function estadoPaginaDoHistorico(st,rota){
    if(!PAGINAS[rota]||normaliza(st&&st.t6Route)!==rota)return null;
    return copiaEstadoPagina(st&&st[CHAVE_ESTADO_PAGINA]);
  }
  function urlFicha(key){
    var p=partes(key),u=new URL(location.href);
    u.searchParams.set('card',String(p[0]||'').split('@')[0]);
    u.searchParams.delete('funcao');u.searchParams.delete('modo');
    return u.pathname+u.search+u.hash;
  }
  function escreveHistorico(rota,key,modo,pageState){
    var st={t6Route:rota};
    var privado=copiaEstadoPagina(pageState);
    if(PAGINAS[rota]&&privado)st[CHAVE_ESTADO_PAGINA]=privado;
    if(rota==='ficha'){
      st.ficha=1;st.paginaCard=1;st.key=String(key||'');
      if(estado.origem){st.fromRoute=estado.origem.rota;st.fromY=estado.origem.y;}
    }
    var url=rota==='ficha'?urlFicha(key):urlPrincipal();
    if(modo==='push') history.pushState(st,'',url);
    else history.replaceState(st,'',url);
    estado.commits++;
  }
  function salvaEstadoPagina(payload){
    if(payload===undefined||!PAGINAS[estado.atual])return false;
    var atual=history.state||{},rota=normaliza(atual.t6Route);
    if(rota!==estado.atual)return false;
    var privado=payload===null?null:copiaEstadoPagina(payload);
    if(payload!==null&&!privado)return false;
    var st={};
    try{Object.keys(atual).forEach(function(k){if(k!==CHAVE_ESTADO_PAGINA)st[k]=atual[k];});}catch(e){}
    st.t6Route=rota;
    if(privado)st[CHAVE_ESTADO_PAGINA]=privado;
    try{history.replaceState(st,'',urlPrincipal());estado.commits++;return true;}catch(e){return false;}
  }
  function capturaOrigem(){
    if(estado.origem) return estado.origem;
    var rota=estado.atual!=='ficha'?estado.atual:estado.estavel;
    estado.origem={rota:normaliza(rota)||'inicio',y:window.scrollY||window.pageYOffset||0};
    return estado.origem;
  }
  function nomeAbaGlobal(rota){
    if(FILHAS_ELENCO[rota])return 'MeuTime';
    return {inicio:'Inicio',meutime:'MeuTime',ranking:'Ranking',boxatual:'BoxAtual',boxant:'BoxAnt'}[rota]||'';
  }
  function sincronizaAbaGlobal(rota){
    var alvo=nomeAbaGlobal(rota);
    try{document.querySelectorAll('#t6tabs .t6tab[data-aba]').forEach(function(aba){
      var ativa=!!alvo&&aba.getAttribute('data-aba')===alvo;
      aba.classList.toggle('on',ativa);
      if(ativa)aba.setAttribute('aria-current','page');else aba.removeAttribute('aria-current');
    });}catch(e){}
    return alvo;
  }
  function renderiza(rota,opcoes){
    var pagina=PAGINAS[rota];
    var resultado;
    if(pagina){
      try{resultado=pagina.render(rota,opcoes||{},pagina)!==false;}catch(e){
        try{console.error('[RouteState] falha ao desenhar '+rota,e);}catch(_e){}
        return false;
      }
    }else{
      if(typeof window.t6RenderRota!=='function') return false;
      resultado=window.t6RenderRota(rota,opcoes||{});
    }
    if(resultado!==false)sincronizaAbaGlobal(rota);
    return resultado;
  }
  function liberaBoot(){
    try{document.documentElement.removeAttribute('data-t6boot');}catch(e){}
  }
  function fallbackBoot(){
    var rota='inicio';
    estado.atual=rota;estado.origem=null;estado.fichaCard=null;
    estado.painel='inicio';persiste(rota);escreveHistorico(rota,'','replace');
    return concluiBoot(renderiza(rota,{boot:true,fallback:true}),false);
  }
  function concluiBoot(resultado,permitirFallback){
    if(resultado&&typeof resultado.then==='function'){
      return resultado.then(function(ok){return concluiBoot(ok,permitirFallback);},
        function(){return permitirFallback?fallbackBoot():false;});
    }
    if(resultado===false) return permitirFallback?fallbackBoot():false;
    liberaBoot();
    return resultado;
  }
  function fechaFichaParaTransicao(){
    var c=window.FichaController;
    if(!c||typeof c.inspect!=='function'||!c.inspect().aberta) return true;
    return c.close(false)!==false;
  }
  function navega(destino,opcoes){
    opcoes=opcoes||{};var rota=normaliza(destino);
    if(!rota||rota==='ficha') return false;
    estado.emTransicao++;
    try{
      if(!fechaFichaParaTransicao()) return false;
      estado.atual=rota;estado.origem=null;estado.fichaCard=null;estado.transicoes++;
      var painel=painelDaRota(rota);if(painel)estado.painel=painel;persiste(rota);
      escreveHistorico(rota,'',opcoes.replace||opcoes.boot?'replace':'push');
      if(renderiza(rota,{boot:!!opcoes.boot,popstate:false})===false) return false;
      if(opcoes.scrollY!==undefined) try{window.scrollTo(0,+opcoes.scrollY||0);}catch(e){}
      return true;
    }finally{estado.emTransicao--;}
  }
  function entraFicha(key,opcoes){
    opcoes=opcoes||{};key=String(key||'');if(!key) return false;
    var card=partes(key)[0].split('@')[0],jaFicha=estado.atual==='ficha';
    if(jaFicha && estado.fichaCard===card && !estado.fichaPendente) return true;
    if(!jaFicha) capturaOrigem();
    estado.atual='ficha';estado.fichaCard=card;estado.transicoes++;persiste('ficha');
    var modo=estado.fichaPendente||opcoes.history||(jaFicha?'replace':'push');
    estado.fichaPendente=null;
    if(modo!=='none') escreveHistorico('ficha',key,modo);
    return true;
  }
  function desenhaOrigemAntesDoHistorico(origem){
    var rota=normaliza(origem&&origem.rota)||estado.estavel||'inicio';
    estado.emTransicao++;
    try{
      estado.atual=rota;estado.origem=null;estado.fichaCard=null;estado.transicoes++;
      var painel=painelDaRota(rota);if(painel)estado.painel=painel;persiste(rota);
      if(renderiza(rota,{boot:false,popstate:false,fromFicha:true})===false) return false;
      try{window.scrollTo(0,+origem.y||0);}catch(e){}
      retornoFichaPendente={rota:rota,y:+origem.y||0};
      return true;
    }finally{estado.emTransicao--;}
  }
  function aposFecharFicha(restaurar,popstate){
    if(popstate||estado.emTransicao) return true;
    var origem=estado.origem||{rota:estado.estavel||'inicio',y:0};
    if(restaurar && history.state && history.state.t6Route==='ficha' && history.length>1){
      if(desenhaOrigemAntesDoHistorico(origem)!==false){
        try{history.back();return true;}catch(e){retornoFichaPendente=null;}
      }
    }
    retornoFichaPendente=null;
    return navega(restaurar?origem.rota:(estado.estavel||'inicio'),
      {replace:true,scrollY:restaurar?origem.y:0});
  }
  function abreFichaDaRota(card,modo){
    var c=window.FichaController;if(!card||!c||typeof c.openFromRoute!=='function') return false;
    estado.fichaPendente=modo||'none';
    var r=c.openFromRoute(String(card).split('@')[0]);
    if(r&&typeof r.then==='function') r.then(function(ok){if(ok===false)estado.fichaPendente=null;});
    return r;
  }
  function rotaDoEvento(ev){
    var r=normaliza(ev&&ev.state&&ev.state.t6Route);
    if(r) return r;
    try{if(new URLSearchParams(location.search).get('card'))return 'ficha';}catch(e){}
    return estado.estavel||'inicio';
  }
  function aoPopstate(ev){
    var rota=rotaDoEvento(ev),st=ev&&ev.state||{};
    if(retornoFichaPendente){
      var retorno=retornoFichaPendente;retornoFichaPendente=null;
      if(rota===retorno.rota && estado.atual===rota){
        try{window.scrollTo(0,retorno.y);}catch(e){}
        return true;
      }
    }
    if(rota==='ficha'){
      var card=st.key?partes(st.key)[0]:'';
      try{card=card||new URLSearchParams(location.search).get('card')||'';}catch(e){}
      estado.origem=st.fromRoute?{rota:normaliza(st.fromRoute)||estado.estavel,y:+st.fromY||0}:estado.origem;
      estado.atual='ficha';estado.fichaCard=String(card).split('@')[0];persiste('ficha');abreFichaDaRota(card,'none');return;
    }
    estado.emTransicao++;
    try{
      fechaFichaParaTransicao();estado.atual=rota;estado.origem=null;estado.fichaCard=null;estado.transicoes++;
      var painel=painelDaRota(rota);if(painel)estado.painel=painel;persiste(rota);
      renderiza(rota,{boot:true,popstate:true,pageState:estadoPaginaDoHistorico(st,rota)});
    }finally{estado.emTransicao--;}
  }
  function restaura(){
    if(estado.restaurado) return false;estado.restaurado=true;
    try{if('scrollRestoration' in history)history.scrollRestoration='manual';}catch(e){}
    var rota=normaliza(le(CHAVE))||'inicio',card='';
    try{card=new URLSearchParams(location.search).get('card')||'';}catch(e){}
    if(rota==='ficha'&&card){
      var st=history.state||{};
      estado.origem=st.fromRoute?{rota:normaliza(st.fromRoute)||estado.estavel,y:+st.fromY||0}:{rota:estado.estavel,y:0};
      estado.atual='ficha';estado.fichaCard=String(card).split('@')[0];persiste('ficha');escreveHistorico('ficha',card,'replace');
      return concluiBoot(abreFichaDaRota(card,'none'),true);
    }
    if(rota==='ficha') rota=estado.estavel||'inicio';
    estado.atual=rota;estado.origem=null;estado.fichaCard=null;
    var atual=history.state||{},pageState=estadoPaginaDoHistorico(atual,rota);
    var painel=painelDaRota(rota);if(painel)estado.painel=painel;persiste(rota);escreveHistorico(rota,'','replace',pageState);
    return concluiBoot(renderiza(rota,{boot:true,popstate:false,pageState:pageState}),true);
  }
  function registraCompat(destino){
    var rota=normaliza(destino);if(!rota)return false;
    estado.atual=rota;var painel=painelDaRota(rota);if(painel)estado.painel=painel;persiste(rota);return true;
  }
  function voltaDaPagina(){
    var pagina=PAGINAS[estado.atual];if(!pagina)return false;
    return navega(pagina.returnRoute,{replace:true});
  }
  function definePainel(painel){
    painel=String(painel||'');
    if(painel!=='inicio'&&painel!=='boxatual'&&painel!=='boxant'&&painel!=='busca')return false;
    estado.painel=painel;return true;
  }
  function inspeciona(){return {atual:estado.atual,estavel:estado.estavel,
    origem:estado.origem?{rota:estado.origem.rota,y:estado.origem.y}:null,fichaCard:estado.fichaCard,painel:estado.painel,
    transicoes:estado.transicoes,commits:estado.commits,restaurado:estado.restaurado,
    emTransicao:estado.emTransicao};}
  var api=Object.freeze({navigate:navega,enterFicha:entraFicha,
    captureFichaOrigin:capturaOrigem,afterFichaClosed:aposFecharFicha,
    restore:restaura,handlePopState:aoPopstate,record:registraCompat,
    registerPage:registraPagina,leavePage:voltaDaPagina,
    savePageState:salvaEstadoPagina,
    setPanel:definePainel,panel:function(){return estado.painel;},
    normalize:normaliza,inspect:inspeciona});
  window.RouteState=api;
  window.t6RegistraRota=api.record;
  window.addEventListener('popstate',api.handlePopState);
})();

(function(){
  function fecha(){document.documentElement.classList.remove('t6filtrosaberto');}
  function monta(){
    var main=document.querySelector('main'), filtros=document.getElementById('filtros');
    if(!main||!filtros)return;
    var b=document.getElementById('t6rkfilterbtn');
    if(!b){b=document.createElement('button');b.id='t6rkfilterbtn';b.type='button';b.onclick=function(){document.documentElement.classList.toggle('t6filtrosaberto');};main.insertBefore(b,main.firstChild);}
    var fn='funções';try{fn=(window.S&&S.tipo)||fn;}catch(e){}
    b.textContent='☰ Filtros · '+fn;
    var mask=document.getElementById('t6rkmask');
    if(!mask){mask=document.createElement('div');mask.id='t6rkmask';mask.onclick=fecha;document.body.appendChild(mask);}
    if(document.documentElement.classList.contains('t6semlat'))fecha();
  }
  /* O botão é estático depois de montado. Recriá-lo a cada 1,2 s fazia a
     página mudar sozinha quando outra área atualizava o DOM. */
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',monta);else monta();
})();


/* bloco JavaScript 33 */

/* Uma única rotina, restrita ao Ranking: evita que regras de cada card
   decidam cores diferentes para Nativo e Básico no tema claro. */
(function(){
 var obsGrade=null,obsTema=null,montado=false,aguardaDom=false;
 function aplicarEtiquetasRanking(){
  var claro=document.documentElement.getAttribute('data-tema')==='claro';
  document.querySelectorAll('#out .grade .tg.rn,#out .grade .tg.se').forEach(function(el){
   if(!claro){['background','border-color','color','box-shadow','text-shadow'].forEach(function(p){el.style.removeProperty(p)});return;}
   var nativo=el.classList.contains('rn');
   el.style.setProperty('background',nativo?'#15558f':'#9d3025','important');
   el.style.setProperty('border-color',nativo?'#0d3d69':'#6e1d16','important');
   el.style.setProperty('color','#fff','important');
   el.style.setProperty('box-shadow','none','important');
   el.style.setProperty('text-shadow','none','important');
  });
 }
 function aoDom(){aguardaDom=false;mount();}
 function mount(){
  if(montado){aplicarEtiquetasRanking();return true;}
  if(document.readyState==='loading'&&!document.documentElement){
   if(!aguardaDom){aguardaDom=true;document.addEventListener('DOMContentLoaded',aoDom);}
   return false;
  }
  aplicarEtiquetasRanking();
  var out=document.getElementById('out');
  if(out){obsGrade=new MutationObserver(aplicarEtiquetasRanking);obsGrade.observe(out,{childList:true,subtree:true});}
  obsTema=new MutationObserver(aplicarEtiquetasRanking);
  obsTema.observe(document.documentElement,{attributes:true,attributeFilter:['data-tema']});
  montado=true;return true;
 }
 function dispose(){
  if(aguardaDom){document.removeEventListener('DOMContentLoaded',aoDom);aguardaDom=false;}
  if(obsGrade){obsGrade.disconnect();obsGrade=null;}
  if(obsTema){obsTema.disconnect();obsTema=null;}
  montado=false;return true;
 }
 window.T6RankingEtiquetasLifecycle=Object.freeze({mount:mount,dispose:dispose,refresh:aplicarEtiquetasRanking,
  inspect:function(){return{mounted:montado,gradeObserver:!!obsGrade,themeObserver:!!obsTema,waitingDom:aguardaDom};}});
 if(document.readyState==='loading'){
  aguardaDom=true;document.addEventListener('DOMContentLoaded',aoDom);
 }else mount();
})();


/* bloco JavaScript 34 */

/* A vitrine entrega rotas, não conteúdo gratuito. As páginas próprias continuam
   responsáveis por revelar Ranking e Boxes. */
(function(){
 function abrirHome(qual){
  var nome={inicio:'Inicio',meutime:'MeuTime',ranking:'Ranking',boxatual:'BoxAtual',boxant:'BoxAnt'}[qual];
  if(nome&&typeof window.t6NavegaPara==='function') return window.t6NavegaPara(nome);
 if(qual==='meutime'){
   try{
    /* A Home final deixa um seletor no documento. Limpa-o antes de abrir o
       Elenco, para a regra visual da vitrine não esconder a tela de destino. */
    var home=document.getElementById('homewrap');
    if(home){home.innerHTML='';home.style.display='none';}
    if(typeof homeToggle==='function') homeToggle(0);
    var painel=document.getElementById('mtwrap');
    if(painel&&getComputedStyle(painel).display!=='block'&&typeof mtToggle==='function') mtToggle();
    window.scrollTo(0,0);
   }catch(e){}
   return;
  }
  if(typeof window.t6Painel==='function') window.t6Painel(qual);
 }
 var antigo=window.t6Cliques;
 window.t6Cliques=function(raiz){
  if(typeof antigo==='function') antigo(raiz);
  raiz.querySelectorAll('[data-t6home]').forEach(function(el){el.onclick=function(ev){ev.preventDefault();ev.stopPropagation();abrirHome(el.dataset.t6home);};});
 };
 /* A rota antiga não é chamada aqui. A Home final abaixo abre a tela nova
    diretamente, sem a pintura intermediária. */
})();


/* bloco JavaScript 35 */

(function(){
 function escH(v){var d=document.createElement('div');d.textContent=String(v||'');return d.innerHTML;}
 function fotoH(c){return 'https://efimg.com/efootballhub22/images/player_cards/'+encodeURIComponent(String(c.id).split('@')[0])+'_l.png';}
 function notaH(c){try{return Number(nota(c))||0;}catch(e){return 0;}}
 function melhoresH(){var a=[],vistos={};try{(D||[]).forEach(function(c){if(!c||c.id==='MOLDE'||!c.id)return;var n=notaH(c);if(!n)return;a.push({c:c,n:n});});}catch(e){}a.sort(function(x,y){return y.n-x.n;});return a.filter(function(x){var k=String(x.c.nome||x.c.id);if(vistos[k])return false;vistos[k]=1;return true;}).slice(0,3);}
 function amostraBoxH(){try{var mapa=window.t6PorBox?window.t6PorBox():{},ativas=(typeof BOXATIVA!=='undefined'?BOXATIVA:[]),nome=ativas.filter(function(n){return /chelsea\s*b\s*selection/i.test(String(n));})[0]||ativas[2]||ativas[ativas.length-1]||Object.keys(mapa)[0],lista=mapa[nome]||[],vistos={},cartas=lista.filter(function(c){var id=String(c&&c.id||'').split('@')[0];if(!id||vistos[id])return false;vistos[id]=1;return true;}).slice(0,3);return {nome:nome||'Boxes atuais',q:lista.length||0,cards:cartas};}catch(e){return {nome:'Boxes atuais',q:0,cards:[]};}}
 function miniBoxH(c,i){try{var d=window.t6cardBox?window.t6cardBox(c,i):null,label=d&&d.v?d.v:'VER NA BOX',st=d&&d.vSt?d.vSt:'color:var(--d30);background:var(--d14);border:1px solid var(--d18)',fn=d&&d.fn?d.fn:'',pos=d&&d.pos?d.pos:'',pc=d&&d.pct?d.pct:'';return '<article class="t6h-boxcard"><img src="'+fotoH(c)+'" alt=""><b>'+escH(c.nome)+'</b><small>'+escH(fn)+' '+escH(pos)+'</small><span>Recomendação: '+escH(pc)+'%</span><em style="'+st+'">'+escH(label)+'</em></article>';}catch(e){return '';}}
 window.t6TelaInicio=function(){
  var lista=melhoresH(),box=amostraBoxH(),imagem='assets/castolo-card-art-v2.png';
  var top=lista.map(function(x,i){return '<article class="t6h-topcard t6h-podio p'+(i+1)+'"><img src="'+fotoH(x.c)+'" alt=""><span><b>'+escH(x.c.nome)+'</b><small>PONTUAÇÃO <strong>'+notaH(x.c).toFixed(2)+'</strong></small></span><i>'+(i+1)+'º</i></article>';}).join('');
  var boxCards=(box.cards||[]).map(miniBoxH).join('');
  if(!top)top='<span style="font-size:12px;color:var(--d13)">O ranking completo está disponível na aba Ranking.</span>';
  return '<section class="t6home2">'
   +'<article class="t6h-hero"><div><span class="t6h-kicker">BUILDS</span><h1>Descubra até onde seu card chega.</h1><p>Vê onde ele rende mais, o que vale ajustar e para de gastar ponto no escuro. São mais de 10,6 bilhões de cenários comparados com ajuda da IA.</p><span class="t6h-prova">Método de pontuação exclusivo, mais assertivo que a nota padrão da Konami.</span><span class="t6h-prova">+10 bilhões de cenários testados com IA</span><button class="t6h-maincta" data-t6home="ranking">Ver no ranking</button></div><div class="t6h-buildmock"><div class="t6h-cardpic" style="background-image:url('+imagem+')"><div class="t6h-cardtop"><strong class="t6h-cardovr">104</strong></div><div class="t6h-cardbottom"><span class="t6h-cardstars">★★★★★</span><span class="t6h-cardimpetos"><i class="azul">⚡</i><i class="amarelo">⚡</i></span></div></div><div class="t6h-buildboard"><small>ANTES / DEPOIS</small><div class="t6h-pontos"><span>99.4</span><i>→</i><b>104.8</b></div><div class="t6h-bars"><i></i><i></i><i></i></div></div></div></article>'
   +'<article class="t6h-elenco"><div><span class="t6h-kicker" style="color:var(--d8)">ELENCO</span><h2>Seu elenco tá redondo?</h2><p>Vê o que tá faltando, compara quem você já tem e encontra quem encaixa melhor no seu time.</p><button class="t6h-maincta" style="background:linear-gradient(180deg,var(--d25),var(--d26));border-color:var(--d28)" data-t6home="meutime">Organizar elenco</button></div><div class="t6h-pitches" aria-hidden="true"><div class="t6h-pitch agora"><em>AGORA</em><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div><div class="t6h-pitch depois"><em>DEPOIS</em><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div></div></article>'
   +'<div class="t6h-free"><section class="t6h-freebox"><div class="t6h-freehead"><h2>Quem tá no topo?</h2><button data-t6home="ranking">Ver ranking →</button></div><div class="t6h-top3">'+top+'</div></section>'
   +'<section class="t6h-freebox"><div class="t6h-freehead"><h2>Boxes atuais</h2><button data-t6home="boxatual">Ver todas →</button></div><div class="t6h-boxsample"><div><div class="t6h-boxcopy"><b>'+escH(box.nome)+'</b><p>Uma amostra. As indicações e todos os cards estão dentro da Box.</p></div><div class="t6h-boxcards">'+boxCards+'</div></div></div></section></div>'
  +'</section>';
 };
 /* A primeira pintura fica invisível até a Home final estar montada no mesmo
    painel usado por Ranking, Boxes e Elenco. Assim o F5 não cria uma segunda
    rota nem expõe nenhum desenho legado antes da tela atual. */
 window.T6HOME_FINAL_PRONTA=true;
 /* Só evita pintar a Home como quadro provisório quando o boot já conhece
    outra rota. A decisão e a abertura continuam pertencendo ao roteador final. */
 var rotaVisualInicial='inicio';
 try{rotaVisualInicial=(window.RouteState&&window.RouteState.inspect().atual)||'inicio';}catch(e){}
 try{if(window.RouteState)window.RouteState.setPanel(
   rotaVisualInicial==='boxatual'||rotaVisualInicial==='boxant'?rotaVisualInicial:'inicio');}catch(e){}
 document.documentElement.classList.remove('t6ranking');
 var home=document.getElementById('homewrap');
 if(home){
  if(rotaVisualInicial==='inicio'){
   home.style.display='block';
   home.innerHTML='<div class="t6tela">'+window.t6TelaInicio()+'</div>';
   try{if(typeof window.t6Cliques==='function')window.t6Cliques(home);}catch(e){}
  }else{
   home.innerHTML='';
   home.style.display='none';
  }
 }
})();


/* bloco JavaScript 36 */

/* Busca global do cabeçalho: sugestões de versões enquanto digita e página
   completa ao confirmar. É independente da busca contextual do Ranking. */
(function(){
 function esc(v){var d=document.createElement('div');d.textContent=String(v||'');return d.innerHTML;}
 function normal(v){return String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();}
 function imagem(c){return 'https://efimg.com/efootballhub22/images/player_cards/'+encodeURIComponent(String(c.id).split('@')[0])+'_l.png';}
 function notaBusca(c){try{return Number(nota(c))||0;}catch(e){return 0;}}
 function estiloBusca(c){
   var e=String(c&&c.modelo||'');
   var nomes={'Jog. de infiltração':'Jogador de infiltração','Jog. de Infiltração':'Jogador de infiltração','Especialista em cruz.':'Especialista em cruzamento'};
   return nomes[e]||e||'Sem estilo';
 }
 function encontra(texto){
   var termo=normal(texto).trim(), vistos={}, saida=[];
   if(termo.length<2)return saida;
   try{(D||[]).forEach(function(c){
     if(!c||c.id==='MOLDE'||!c.id||!normal(c.nome).includes(termo))return;
     var id=String(c.id).split('@')[0], atual=vistos[id], valor=notaBusca(c);
     if(!atual||valor>atual.n)vistos[id]={c:c,n:valor};
   });}catch(e){}
   Object.keys(vistos).forEach(function(k){saida.push(vistos[k]);});
   return saida.sort(function(a,b){return b.n-a.n;});
 }
 function fecha(){var s=document.getElementById('t6GlobalSuggest');if(s)s.hidden=true;}
 function abreFicha(c){
   fecha();
   var k=String(c.id)+'|'+c.tipo;
   try{ if(typeof window.elAbreCard==='function') return window.elAbreCard(k); }catch(e){}
   try{ if(typeof window.t6AbreMaximo==='function') return window.t6AbreMaximo(k); }catch(e){}
   try{ if(typeof abrir==='function') return abrir(k); }catch(e){}
 }
 function posiciona(s,q){var r=q.getBoundingClientRect();s.style.left=Math.max(8,r.left)+'px';s.style.top=(r.bottom+7)+'px';s.style.width=Math.min(r.width,Math.max(280,window.innerWidth-16))+'px';}
 function sugestoes(q){
   var s=document.getElementById('t6GlobalSuggest');if(!s)return;var lista=encontra(q.value);posiciona(s,q);
   if(!q.value.trim()){fecha();return;}
   if(q.value.trim().length<2){s.innerHTML='<div class="t6gs-empty">Digite pelo menos duas letras.</div>';s.hidden=false;return;}
   if(!lista.length){s.innerHTML='<div class="t6gs-empty">Nenhum card encontrado.</div>';s.hidden=false;return;}
   s.innerHTML=lista.map(function(x){var c=x.c, estilo=estiloBusca(c), pos=(typeof SIGJ!=='undefined'&&SIGJ[c.np])||c.np||'';return '<button type="button" class="t6gs-item" data-t6gs="'+esc(c.id)+'|'+esc(c.tipo)+'"><img src="'+imagem(c)+'" alt=""><span><b>'+esc(c.nome)+'</b><small>'+esc(estilo)+' · '+esc(pos)+'</small></span><em>'+x.n.toFixed(2)+'</em></button>';}).join('');
   s.hidden=false;s.querySelectorAll('[data-t6gs]').forEach(function(b){b.onclick=function(){var p=b.getAttribute('data-t6gs').split('|'),x=lista.filter(function(z){return String(z.c.id)===p[0]&&z.c.tipo===p[1];})[0];if(x)abreFicha(x.c);};});
 }
 window.t6TelaBusca=function(){
   var termo=window._t6BuscaGlobal||'', lista=encontra(termo);
   var cards=lista.map(function(x){var c=x.c,estilo=estiloBusca(c),pos=(typeof SIGJ!=='undefined'&&SIGJ[c.np])||c.np||'';return '<article class="t6-result-card" data-k="'+esc(c.id)+'|'+esc(c.tipo)+'"><img src="'+imagem(c)+'" alt=""><div><b>'+esc(c.nome)+'</b><small>'+esc(estilo)+' · '+esc(pos)+'</small><strong>'+x.n.toFixed(2)+'</strong></div></article>';}).join('');
   return '<section class="t6-resultados"><h1>Resultados para “'+esc(termo)+'”</h1><p>'+lista.length+' '+(lista.length===1?'versão encontrada.':'versões encontradas.')+' Clique em uma carta para abrir os detalhes.</p>'+(cards?'<div class="t6-result-grid">'+cards+'</div>':'<p>Nenhum card encontrado.</p>')+'</section>';
 };
 function monta(){
   var q=document.getElementById('q');if(!q||q.dataset.t6BuscaGlobal)return false;
   q.dataset.t6BuscaGlobal='1';q.setAttribute('autocomplete','off');
   var s=document.createElement('div');s.id='t6GlobalSuggest';s.hidden=true;document.body.appendChild(s);
   q.addEventListener('input',function(){sugestoes(q);});
   q.addEventListener('keydown',function(ev){if(ev.key==='Escape'){fecha();return;}if(ev.key!=='Enter')return;ev.preventDefault();var termo=q.value.trim();if(termo.length<2)return;window._t6BuscaGlobal=termo;fecha();try{if(window.RouteState)window.RouteState.setPanel('busca');window.t6Painel('busca');window.scrollTo(0,0);}catch(e){}});
   document.addEventListener('pointerdown',function(ev){if(ev.target!==q&&!s.contains(ev.target))fecha();});
   window.addEventListener('resize',function(){if(!s.hidden)posiciona(s,q);});
   return true;
 }
 if(!monta())setTimeout(monta,450);
})();


/* bloco JavaScript 38 */

(function(){
  function restaura(){
    if(window.RouteState&&typeof window.RouteState.restore==='function') window.RouteState.restore();
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',restaura,{once:true});
  else restaura();
})();
