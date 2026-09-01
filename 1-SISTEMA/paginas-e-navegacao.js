/* bloco JavaScript 32 */

/* ROUTE_STATE_5 — dono único da rota, URL e histórico.
   A página desenha; esta porta decide a transição e registra uma única entrada. */
(function instalaRouteState(){
  if(window.RouteState) return;
  var CHAVE='clubefutebol_aba_atual', ESTAVEL='clubefutebol_aba_estavel';
  var ROTAS_BASE={inicio:1,meutime:1,ranking:1,boxatual:1,busca:1,ficha:1};
  var VALIDAS={inicio:1,meutime:1,ranking:1,boxatual:1,busca:1,ficha:1};
  /* Hierarquia visual canônica: estas análises são páginas próprias, mas
     continuam pertencendo à aba global Elenco. O mapa não registra nem abre
     rotas; apenas restaura a aba-pai quando alguma delas estiver disponível. */
  var FILHAS_ELENCO={melhorfuncao:1,timefraco:1,melhorformacao:1,tecnicotime:1,comparartime:1};
  var CHAVE_ESTADO_PAGINA='t6PageState', LIMITE_ESTADO_PAGINA=65536;
  var PAGINAS=Object.create(null);
  var NOMES={Inicio:'inicio',MeuTime:'meutime',Ranking:'ranking',BoxAtual:'boxatual',BoxAnt:'boxatual',Busca:'busca'};
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
    if(v==='boxant') v='boxatual';
    return VALIDAS[v]?v:null;
  }
  function le(k){try{return localStorage.getItem(k)||'';}catch(e){return '';}}
  function grava(k,v){try{localStorage.setItem(k,v);}catch(e){}}
  var inicial=normaliza(le(CHAVE))||'inicio';
  var estavel=normaliza(le(ESTAVEL));
  if(!estavel||estavel==='ficha') estavel=inicial!=='ficha'?inicial:'inicio';
  function painelDaRota(rota){return rota==='boxatual'||rota==='busca'?rota:(rota==='inicio'?'inicio':null);}
  var estado={atual:inicial,estavel:estavel,painel:painelDaRota(inicial)||'inicio',origem:null,transicoes:0,
    commits:0,restaurado:false,emTransicao:0,fichaPendente:null,fichaCard:null};
  var retornoFichaPendente=null,fichaCadastralDaRota=false;
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
  function restauraTermoBusca(termo){
    termo=String(termo||'').trim();
    window._t6BuscaGlobal=termo;
    var campo=document.getElementById('q');
    if(campo)campo.value=termo;
    return termo;
  }
  function urlFicha(key){
    var p=partes(key),u=new URL(location.href);
    u.searchParams.set('card',String(p[0]||'').split('@')[0]);
    u.searchParams.delete('funcao');u.searchParams.delete('modo');
    return u.pathname+u.search+u.hash;
  }
  function escreveHistorico(rota,key,modo,pageState){
    var st={t6Route:rota};
    if(rota==='busca')st.t6BuscaTermo=String(window._t6BuscaGlobal||'').trim();
    var privado=copiaEstadoPagina(pageState);
    if(PAGINAS[rota]&&privado)st[CHAVE_ESTADO_PAGINA]=privado;
    if(rota==='ficha'){
      st.ficha=1;st.paginaCard=1;st.key=String(key||'');
      if(estado.origem){
        st.fromRoute=estado.origem.rota;st.fromY=estado.origem.y;
        if(estado.origem.rota==='busca')st.fromBuscaTermo=String(window._t6BuscaGlobal||'').trim();
      }
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
    return {inicio:'Inicio',meutime:'MeuTime',ranking:'Ranking',boxatual:'BoxAtual'}[rota]||'';
  }
  function sincronizaAbaGlobal(rota){
    var alvo=nomeAbaGlobal(rota);
    try{document.querySelectorAll('#t6tabs .t6tab[data-aba]').forEach(function(aba){
      var ativa=!!alvo&&aba.getAttribute('data-aba')===alvo;
      aba.classList.toggle('on',ativa);
      if(ativa)aba.setAttribute('aria-current','page');else aba.removeAttribute('aria-current');
    });}catch(e){}
    try{
      var buscaTopo=document.getElementById('q');
      if(buscaTopo)buscaTopo.placeholder=rota==='ranking'
        ? 'buscar nesta posição':'buscar em todos os cards';
    }catch(e){}
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
    }else if(rota==='busca'&&typeof window.t6Painel==='function'){
      window.t6Painel('busca');resultado=true;
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
    if(fichaCadastralDaRota){
      fichaCadastralDaRota=false;
      try{if(typeof window.t6FechaFichaCadastral==='function')window.t6FechaFichaCadastral();}catch(e){}
    }
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
    var id=String(card||'').split('@')[0].trim();
    if(!/^\d+$/.test(id)||typeof window.t6AbreFichaCadastral!=='function')return false;
    estado.fichaPendente=modo||'none';
    var r=window.t6AbreFichaCadastral(id);
    estado.fichaPendente=null;
    fichaCadastralDaRota=r!==false;
    return r;
  }
  function agendaVoltaDaFichaCadastral(){
    if(!fichaCadastralDaRota||estado.atual!=='ficha')return;
    setTimeout(function(){
      if(!fichaCadastralDaRota||estado.atual!=='ficha'||document.querySelector('.t6fc-back'))return;
      fichaCadastralDaRota=false;aposFecharFicha(true,false);
    },0);
  }
  document.addEventListener('click',function(ev){
    var alvo=ev&&ev.target;
    if(alvo&&typeof alvo.closest==='function'&&alvo.closest('.t6fc-close'))agendaVoltaDaFichaCadastral();
  });
  document.addEventListener('pointerdown',function(ev){
    var alvo=ev&&ev.target;
    if(alvo&&alvo.classList&&alvo.classList.contains('t6fc-back'))agendaVoltaDaFichaCadastral();
  });
  document.addEventListener('keydown',function(ev){if(ev&&ev.key==='Escape')agendaVoltaDaFichaCadastral();});
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
        if(rota==='busca'){
          restauraTermoBusca(st.t6BuscaTermo);
          renderiza(rota,{boot:true,popstate:true});
        }
        try{window.scrollTo(0,retorno.y);}catch(e){}
        return true;
      }
    }
    if(rota==='ficha'){
      var card=st.key?partes(st.key)[0]:'';
      try{card=card||new URLSearchParams(location.search).get('card')||'';}catch(e){}
      estado.origem=st.fromRoute?{rota:normaliza(st.fromRoute)||estado.estavel,y:+st.fromY||0}:estado.origem;
      if(estado.origem&&estado.origem.rota==='busca')restauraTermoBusca(st.fromBuscaTermo);
      estado.atual='ficha';estado.fichaCard=String(card).split('@')[0];persiste('ficha');abreFichaDaRota(card,'none');return;
    }
    if(rota==='busca')restauraTermoBusca(st.t6BuscaTermo);
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
    if(card){
      var st=history.state||{};
      var rotaOrigem=rota==='ficha'?(estado.estavel||'inicio'):rota;
      estado.origem=st.fromRoute?{rota:normaliza(st.fromRoute)||rotaOrigem,y:+st.fromY||0}:{rota:rotaOrigem,y:0};
      if(estado.origem.rota==='busca')restauraTermoBusca(st.fromBuscaTermo);
      estado.atual='ficha';estado.fichaCard=String(card).split('@')[0];persiste('ficha');escreveHistorico('ficha',card,'replace');
      return concluiBoot(abreFichaDaRota(card,'none'),true);
    }
    if(rota==='ficha') rota=estado.estavel||'inicio';
    estado.atual=rota;estado.origem=null;estado.fichaCard=null;
    var atual=history.state||{},pageState=estadoPaginaDoHistorico(atual,rota);
    if(rota==='busca')restauraTermoBusca(atual.t6BuscaTermo||window._t6BuscaGlobal);
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
    if(painel==='boxant')painel='boxatual';
    if(painel!=='inicio'&&painel!=='boxatual'&&painel!=='busca')return false;
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
  /* Todos os cliques cadastrais entram primeiro na rota persistida. Quando a
     própria restauração da rota chama a Ficha, card/estado já coincidem e não
     há um segundo commit de histórico. */
  var abreFichaCadastralBase=window.t6AbreFichaCadastral;
  if(typeof abreFichaCadastralBase==='function'){
    window.t6AbreFichaCadastral=function(cardId){
      var id=String(cardId||'').split('@')[0].trim();
      if(!/^\d+$/.test(id))return false;
      var atual=inspeciona();
      if(atual.atual!=='ficha'||String(atual.fichaCard||'')!==id){
        if(entraFicha(id,{})===false)return false;
      }
      var resultado=abreFichaCadastralBase(id);
      fichaCadastralDaRota=resultado!==false;
      return resultado;
    };
  }
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
  var nome={inicio:'Inicio',meutime:'MeuTime',ranking:'Ranking',boxatual:'BoxAtual',boxant:'BoxAtual'}[qual];
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
 function attrH(v){return String(v==null?'':v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
 var estadoHomeH={codigo:'NAO_INICIADO',linhas:[],erro:null,pedido:0};
 function valorH(c){
  for(var i=1;i<arguments.length;i++)if(c&&c[arguments[i]]!=null)return c[arguments[i]];
  return null;
 }
 function cardIdH(c){var v=valorH(c,'id','card_id');return v==null?'':String(v).split('@')[0].trim();}
 function fotoH(c){
  var url=valorH(c,'fotoUrl','foto_url_cloudinary')||'';
  url=String(url||'').trim();
  if(!/^https:\/\/[^\s"'<>]+$/i.test(url)&&!/^data:image\/(?:gif|png|jpeg|webp);base64,[a-z0-9+/=]+$/i.test(url))return '';
  return attrH(url);
 }
 function imgH(c){var url=fotoH(c);return '<img'+(url?' src="'+url+'"':'')+' alt="">';}
 function overallH(c){var v=valorH(c,'overall'),n=Number(v);return v!=null&&isFinite(n)?n:null;}
 function posicaoH(c){return valorH(c,'posicaoSigla','posicao_principal_codigo')||'';}
 function nomeBoxH(c){return String(valorH(c,'box','box_nome')||'').trim();}
 function totalBoxH(c){var v=valorH(c,'boxTotalCards','box_total_cards'),n=Number(v);return v!=null&&isFinite(n)&&n>=0?n:0;}
 function repintaHomeH(){
  var atual='';try{atual=window.RouteState&&window.RouteState.inspect().atual||'';}catch(e){}
  if(atual==='inicio'&&typeof window.t6Painel==='function')window.t6Painel('inicio');
 }
 function falhaHomeH(pedido,erro){
  if(pedido!==estadoHomeH.pedido)return;
  estadoHomeH.codigo='ERRO';estadoHomeH.linhas=[];estadoHomeH.erro=erro||new Error('Home indisponível');repintaHomeH();
 }
 function carregaHomeH(){
  if(estadoHomeH.codigo==='CARREGANDO'||estadoHomeH.codigo==='PRONTO')return;
  estadoHomeH.codigo='CARREGANDO';estadoHomeH.erro=null;var pedido=++estadoHomeH.pedido,cn=window.ClubeNovoReadModel,retorno;
  if(!cn||typeof cn.home!=='function'){falhaHomeH(pedido,new Error('View frontend_home_v1 indisponível'));return;}
  try{retorno=cn.home();}catch(e){falhaHomeH(pedido,e);return;}
  Promise.resolve(retorno).then(function(linhas){
    if(pedido!==estadoHomeH.pedido)return;
    if(!Array.isArray(linhas))throw new Error('Resposta inválida de frontend_home_v1');
    estadoHomeH.codigo='PRONTO';estadoHomeH.linhas=linhas.slice(0,3);estadoHomeH.erro=null;repintaHomeH();
  }).catch(function(e){falhaHomeH(pedido,e);});
 }
 function modeloBoxH(){
  if(estadoHomeH.codigo==='NAO_INICIADO')carregaHomeH();
  if(estadoHomeH.codigo==='CARREGANDO')return {nome:'Carregando Box em destaque…',q:0,cards:[],pronto:false,mensagem:'Consultando a vitrine oficial da Home…'};
  if(estadoHomeH.codigo==='ERRO')return {nome:'Box indisponível',q:0,cards:[],pronto:false,erro:true,mensagem:'Não foi possível consultar a vitrine oficial da Home.'};
  var cards=estadoHomeH.linhas.filter(function(c){return !!cardIdH(c);}).slice(0,3),primeiro=cards[0]||null;
  return {nome:primeiro?nomeBoxH(primeiro):'Nenhuma Box em destaque',q:primeiro?totalBoxH(primeiro):0,cards:cards,pronto:true,mensagem:''};
 }
 function miniBoxH(c){
  var ov=overallH(c),pos=posicaoH(c),detalhe=[pos,ov===null?'':'Overall '+ov].filter(Boolean).join(' · ');
  return '<article class="t6h-boxcard" data-t6cadastro="'+attrH(cardIdH(c))+'" role="button" tabindex="0">'+imgH(c)+'<b>'+escH(c&&c.nome||('Card '+cardIdH(c)))+'</b><small>'+escH(detalhe||'Card cadastrado')+'</small><span>Cadastro oficial da Box</span><em>VER FICHA</em></article>';
 }
 window.t6TelaInicio=function(){
  var box=modeloBoxH(),imagem='linear-gradient(155deg,#25344a 0%,#141d2a 48%,#0b1119 100%)';
  var top='<span style="font-size:12px;color:var(--d13)">aguardando contrato de publicação das Builds</span>';
  var boxCards=(box.cards||[]).map(miniBoxH).join('');
  if(!boxCards)boxCards='<span style="font-size:12px;color:var(--d13)">'+escH(box.pronto?'A view da Home não retornou uma Box em destaque.':box.mensagem)+'</span>'
    +(box.erro?'<button type="button" data-t6home-retry="1" style="padding:7px 10px;border-radius:8px;border:1px solid var(--d18);background:var(--d32);color:var(--d30);cursor:pointer">Tentar novamente</button>':'');
  var textoBox=box.pronto?'Amostra oficial de '+box.q+' '+(box.q===1?'card cadastrado':'cards cadastrados')+' nesta Box.':box.mensagem;
  return '<section class="t6home2">'
    +'<article class="t6h-hero"><div><span class="t6h-kicker">BUILDS</span><h1>Descubra até onde seu card chega.</h1><p>Vê onde ele rende mais, o que vale ajustar e para de gastar ponto no escuro. São mais de 10,6 bilhões de cenários comparados com ajuda da IA.</p><span class="t6h-prova">Método de pontuação exclusivo, mais assertivo que a nota padrão da Konami.</span><span class="t6h-prova">+10 bilhões de cenários testados com IA</span><button class="t6h-maincta" data-t6home="ranking">Ver no ranking</button></div><div class="t6h-buildmock"><div class="t6h-cardpic" style="background-image:'+imagem+'"><div class="t6h-cardtop"><strong class="t6h-cardovr">—</strong></div><div class="t6h-cardbottom"><span class="t6h-cardstars">★★★★★</span><span class="t6h-cardimpetos"><i class="azul">⚡</i><i class="amarelo">⚡</i></span></div></div><div class="t6h-buildboard"><small>PUBLICAÇÃO DAS BUILDS</small><div class="t6h-pontos"><span>—</span><i>→</i><b>—</b></div><div class="t6h-bars"><i></i><i></i><i></i></div></div></div></article>'
   +'<article class="t6h-elenco"><div><span class="t6h-kicker" style="color:var(--d8)">ELENCO</span><h2>Seu elenco tá redondo?</h2><p>Vê o que tá faltando, compara quem você já tem e encontra quem encaixa melhor no seu time.</p><button class="t6h-maincta" style="background:linear-gradient(180deg,var(--d25),var(--d26));border-color:var(--d28)" data-t6home="meutime">Organizar elenco</button></div><div class="t6h-pitches" aria-hidden="true"><div class="t6h-pitch agora"><em>AGORA</em><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div><div class="t6h-pitch depois"><em>DEPOIS</em><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div></div></article>'
   +'<div class="t6h-free"><section class="t6h-freebox"><div class="t6h-freehead"><h2>Quem tá no topo?</h2><button data-t6home="ranking">Ver ranking →</button></div><div class="t6h-top3">'+top+'</div></section>'
   +'<section class="t6h-freebox"><div class="t6h-freehead"><h2>Boxes cadastradas</h2><button data-t6home="boxatual">Ver todas →</button></div><div class="t6h-boxsample"><div><div class="t6h-boxcopy"><b>'+escH(box.nome)+'</b><p>'+escH(textoBox)+'</p></div><div class="t6h-boxcards">'+boxCards+'</div></div></div></section></div>'
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
   rotaVisualInicial==='boxatual'||rotaVisualInicial==='busca'?rotaVisualInicial:'inicio');}catch(e){}
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
 function ligaCardsCadastraisH(raiz){
  if(!raiz||typeof raiz.querySelectorAll!=='function')return;
  raiz.querySelectorAll('[data-t6cadastro]').forEach(function(el){
   if(el.dataset.t6CadastroLigado)return;el.dataset.t6CadastroLigado='1';
   function abre(ev){
    if(ev&&ev.type==='keydown'&&ev.key!=='Enter'&&ev.key!==' ')return;
    if(ev){ev.preventDefault();ev.stopPropagation();}
    var id=el.getAttribute('data-t6cadastro');
    if(id&&typeof window.t6AbreFichaCadastral==='function')window.t6AbreFichaCadastral(id);
   }
   el.addEventListener('click',abre);el.addEventListener('keydown',abre);
  });
 }
 window.t6LigaCardsCadastrais=ligaCardsCadastraisH;
  var cliquesAntesDoCadastro=window.t6Cliques;
  window.t6Cliques=function(raiz){if(typeof cliquesAntesDoCadastro==='function')cliquesAntesDoCadastro(raiz);ligaCardsCadastraisH(raiz);};
 document.addEventListener('click',function(ev){
  var alvo=ev&&ev.target,botao=alvo&&typeof alvo.closest==='function'?alvo.closest('[data-t6home-retry]'):null;
  if(!botao||estadoHomeH.codigo!=='ERRO')return;
  ev.preventDefault();ev.stopPropagation();carregaHomeH();repintaHomeH();
 });
})();


/* bloco JavaScript 36 */

/* Busca global do cabeçalho: sugestões de versões enquanto digita e página
   completa ao confirmar. É independente da busca contextual do Ranking. */
(function(){
 function esc(v){var d=document.createElement('div');d.textContent=String(v||'');return d.innerHTML;}
 function attr(v){return String(v==null?'':v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
 var LIMITE_SUGESTOES=8,LIMITE_PAGINA=48,timerSugestoes=null,tokenSugestoes=0;
 var paginaBusca={termo:'',codigo:'NAO_INICIADO',linhas:[],erro:null,pedido:0};
 function valor(c){for(var i=1;i<arguments.length;i++)if(c&&c[arguments[i]]!=null)return c[arguments[i]];return null;}
 function cardId(c){var v=valor(c,'id','card_id');return v==null?'':String(v).split('@')[0].trim();}
 function imagem(c){
   var url=valor(c,'fotoUrl','foto_url_cloudinary')||'';
   url=String(url||'').trim();
   if(!/^https:\/\/[^\s"'<>]+$/i.test(url)&&!/^data:image\/(?:gif|png|jpeg|webp);base64,[a-z0-9+/=]+$/i.test(url))return '';
   return attr(url);
 }
 function tagImagem(c){var url=imagem(c);return '<img'+(url?' src="'+url+'"':'')+' alt="">';}
 function posicaoBusca(c){return valor(c,'posicaoSigla','posicao_principal_codigo','posicaoNome','posicao_principal_nome')||'';}
 function tipoBusca(c){return valor(c,'tipoCartaNome','tipo_carta_nome')||'';}
 function boxBusca(c){return valor(c,'box','box_nome')||'';}
 function overallBusca(c){var v=valor(c,'overall'),n=Number(v);return v!=null&&isFinite(n)?'Overall '+n:'';}
 function estilosBusca(c){
   var lista=valor(c,'playstyles');
   if(typeof lista==='string'){try{var json=JSON.parse(lista);if(Array.isArray(json))lista=json;}catch(e){return lista;}}
   if(!Array.isArray(lista))return '';
   return lista.map(function(item){return typeof item==='string'?item:(item&&String(item.nome||item.rotulo||item.codigo||''));}).filter(Boolean).slice(0,2).join(' · ');
 }
 function statusCadastro(c){
   var pendencias=valor(c,'pendencias'),integro=String(valor(c,'integridadeCadastro','integridade_cadastro')||'').toLowerCase();
   var texto=String(pendencias==null?'':pendencias).trim().toLowerCase();
   var temPendencia=Array.isArray(pendencias)?pendencias.length>0:(pendencias&&typeof pendencias==='object'?Object.keys(pendencias).length>0:!!texto&&texto!=='[]'&&texto!=='{}'&&texto!=='null');
   return temPendencia||integro==='incompleto'||integro==='pendente'?'Cadastro com pendências':'Card cadastrado';
 }
 function consultaBusca(termo,limite){
   var cn=window.ClubeNovoReadModel,retorno;
   if(!cn||typeof cn.busca!=='function')return Promise.reject(new Error('View frontend_busca_v1 indisponível'));
   try{retorno=cn.busca(termo,{limit:limite});}catch(e){return Promise.reject(e);}
   return Promise.resolve(retorno).then(function(linhas){if(!Array.isArray(linhas))throw new Error('Resposta inválida de frontend_busca_v1');return linhas.slice(0,limite);});
 }
 function detalheBusca(c){return [tipoBusca(c),posicaoBusca(c),overallBusca(c),boxBusca(c)].filter(Boolean).join(' · ');}
 function abreCadastro(c){
   var id=cardId(c);fecha();
   if(id&&typeof window.t6AbreFichaCadastral==='function')return window.t6AbreFichaCadastral(id);
   return false;
 }
 function fecha(){clearTimeout(timerSugestoes);tokenSugestoes++;var s=document.getElementById('t6GlobalSuggest');if(s)s.hidden=true;}
 function posiciona(s,q){var r=q.getBoundingClientRect();s.style.left=Math.max(8,r.left)+'px';s.style.top=(r.bottom+7)+'px';s.style.width=Math.min(r.width,Math.max(280,window.innerWidth-16))+'px';}
 function desenhaSugestoes(s,lista){
   if(!lista.length){s.innerHTML='<div class="t6gs-empty">Nenhum card encontrado.</div>';s.hidden=false;return;}
   s.innerHTML=lista.map(function(c){var id=cardId(c),estilos=estilosBusca(c),detalhe=[detalheBusca(c),estilos].filter(Boolean).join(' · ');return '<button type="button" class="t6gs-item" data-t6gs="'+attr(id)+'">'+tagImagem(c)+'<span><b>'+esc(c&&c.nome||('Card '+id))+'</b><small>'+esc(detalhe||'Cadastro do clube')+'</small></span><em>'+esc(statusCadastro(c))+'</em></button>';}).join('');
   s.hidden=false;s.querySelectorAll('[data-t6gs]').forEach(function(botao){botao.onclick=function(){var id=botao.getAttribute('data-t6gs'),card=lista.filter(function(c){return cardId(c)===id;})[0];if(card)abreCadastro(card);};});
 }
 function sugestoes(q){
   var s=document.getElementById('t6GlobalSuggest');if(!s)return;posiciona(s,q);
   clearTimeout(timerSugestoes);var termo=q.value.trim(),pedido=++tokenSugestoes;
   if(!termo){fecha();return;}
   if(termo.length<3){s.innerHTML='<div class="t6gs-empty">Digite pelo menos três letras.</div>';s.hidden=false;return;}
   s.innerHTML='<div class="t6gs-empty">Buscando cards…</div>';s.hidden=false;
   timerSugestoes=setTimeout(function(){
     consultaBusca(termo,LIMITE_SUGESTOES).then(function(lista){
       if(pedido!==tokenSugestoes||q.value.trim()!==termo)return;desenhaSugestoes(s,lista);
     },function(){
       if(pedido!==tokenSugestoes||q.value.trim()!==termo)return;
       s.innerHTML='<div class="t6gs-empty">Busca indisponível no momento.</div>';s.hidden=false;
     });
   },220);
 }
 function repintaPaginaBusca(){
   var atual='';try{atual=window.RouteState&&window.RouteState.inspect().atual||'';}catch(e){}
   if(atual==='busca'&&typeof window.t6Painel==='function')window.t6Painel('busca');
 }
 function iniciaPaginaBusca(termo,forcar){
   termo=String(termo||'').trim();
   if(termo.length<3)return;
   if(!forcar&&paginaBusca.termo===termo&&(paginaBusca.codigo==='CARREGANDO'||paginaBusca.codigo==='PRONTO'||paginaBusca.codigo==='ERRO'))return;
   var pedido=++paginaBusca.pedido;paginaBusca.termo=termo;paginaBusca.codigo='CARREGANDO';paginaBusca.linhas=[];paginaBusca.erro=null;
   consultaBusca(termo,LIMITE_PAGINA).then(function(linhas){
     if(pedido!==paginaBusca.pedido)return;paginaBusca.codigo='PRONTO';paginaBusca.linhas=linhas;repintaPaginaBusca();
   },function(e){
     if(pedido!==paginaBusca.pedido)return;paginaBusca.codigo='ERRO';paginaBusca.linhas=[];paginaBusca.erro=e;repintaPaginaBusca();
   });
 }
 window.t6TelaBusca=function(){
   var termo=String(window._t6BuscaGlobal||'').trim();
   if(termo.length<3)return '<section class="t6-resultados"><h1>Busca de cards</h1><p>Digite pelo menos três letras.</p></section>';
   iniciaPaginaBusca(termo,false);
   if(paginaBusca.termo!==termo||paginaBusca.codigo==='CARREGANDO')return '<section class="t6-resultados"><h1>Resultados para “'+esc(termo)+'”</h1><p>Buscando cards cadastrados…</p></section>';
   if(paginaBusca.codigo==='ERRO')return '<section class="t6-resultados"><h1>Resultados para “'+esc(termo)+'”</h1><p>Não foi possível consultar a busca oficial agora.</p></section>';
   var lista=paginaBusca.linhas;
   if(!lista.length)return '<section class="t6-resultados"><h1>Resultados para “'+esc(termo)+'”</h1><p>Nenhum card encontrado.</p></section>';
   var cards=lista.map(function(c){var id=cardId(c),estilos=estilosBusca(c),detalhe=[detalheBusca(c),estilos].filter(Boolean).join(' · ');return '<article class="t6-result-card" data-t6cadastro="'+attr(id)+'" role="button" tabindex="0">'+tagImagem(c)+'<div><b>'+esc(c&&c.nome||('Card '+id))+'</b><small>'+esc(detalhe||'Cadastro do clube')+'</small><strong>'+esc(statusCadastro(c))+'</strong></div></article>';}).join('');
   return '<section class="t6-resultados"><h1>Resultados para “'+esc(termo)+'”</h1><p>Mostrando '+lista.length+' '+(lista.length===1?'card cadastrado.':'cards cadastrados.')+'</p><div class="t6-result-grid">'+cards+'</div></section>';
 };
 function monta(){
   var q=document.getElementById('q');if(!q||q.dataset.t6BuscaGlobal)return false;
   q.dataset.t6BuscaGlobal='1';q.setAttribute('autocomplete','off');
   var s=document.createElement('div');s.id='t6GlobalSuggest';s.hidden=true;document.body.appendChild(s);
   q.addEventListener('input',function(){sugestoes(q);});
   q.addEventListener('keydown',function(ev){if(ev.key==='Escape'){fecha();return;}if(ev.key!=='Enter')return;ev.preventDefault();var termo=q.value.trim();if(termo.length<3)return;window._t6BuscaGlobal=termo;fecha();iniciaPaginaBusca(termo,true);try{if(window.RouteState&&typeof window.RouteState.navigate==='function')window.RouteState.navigate('busca');else{if(window.RouteState)window.RouteState.setPanel('busca');window.t6Painel('busca');}window.scrollTo(0,0);}catch(e){}});
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
