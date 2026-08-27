/* COMO_FUNCIONA_V1
   Página pública, somente de leitura, registrada pela porta canônica de rotas.
   Não consulta dados, não executa cálculos e não altera o estado do usuário. */
(function instalaComoFunciona(global){
  'use strict';
  if(global.ComoFuncionaPage) return;

  var ROUTE='como-funciona';
  var PAGE_ID='t6ComoFunciona';
  var TAB_ID='t6ComoFuncionaTab';

  function marcaAba(ativa){
    var aba=document.getElementById(TAB_ID);
    if(!aba) return;
    aba.classList.toggle('on',!!ativa);
    if(ativa) aba.setAttribute('aria-current','page');
    else aba.removeAttribute('aria-current');
  }

  function sincronizaAba(){
    var ativa=false;
    try{ativa=!!(global.RouteState&&global.RouteState.inspect().atual===ROUTE);}catch(e){}
    marcaAba(ativa);
  }

  function montaAba(){
    var nav=document.getElementById('t6tabs');
    if(!nav) return false;
    if(document.getElementById(TAB_ID)){sincronizaAba();return true;}

    var aba=document.createElement('button');
    aba.type='button';
    aba.id=TAB_ID;
    aba.className='t6tab t6cf-tab';
    aba.textContent='Como funciona';
    aba.setAttribute('aria-label','Entenda como funciona a avaliação');
    aba.addEventListener('click',function(){
      if(global.RouteState&&typeof global.RouteState.navigate==='function'){
        global.RouteState.navigate(ROUTE);
      }
    });
    nav.appendChild(aba);

    nav.addEventListener('click',function(ev){
      var destino=ev.target&&ev.target.closest?ev.target.closest('.t6tab'):null;
      if(destino&&destino!==aba) marcaAba(false);
    });
    var logo=document.getElementById('t6logo');
    if(logo) logo.addEventListener('click',function(){marcaAba(false);});
    sincronizaAba();
    return true;
  }

  function pagina(){
    return ''
      +'<section id="'+PAGE_ID+'" class="t6cf" aria-labelledby="t6cfTitulo">'
      +  '<div class="t6cf-hero">'
      +    '<div class="t6cf-hero-copy">'
      +      '<span class="t6cf-kicker">POR QUE NOSSA PONTUAÇÃO PODE SER DIFERENTE?</span>'
      +      '<h1 id="t6cfTitulo">Uma leitura de encaixe, não uma cópia da nota oficial.</h1>'
      +      '<p>A lógica parte de uma pergunta: nesta função, com esta build e este técnico, o quanto esta versão do card atende ao papel escolhido? O resultado resume essa resposta para o cenário montado.</p>'
      +    '</div>'
      +    '<div class="t6cf-score" aria-label="Card, função e contexto formando uma pontuação de encaixe">'
      +      '<span>PERGUNTA ANALISADA</span><strong>quanto encaixa?</strong><small>card + função + contexto</small>'
      +    '</div>'
      +  '</div>'

      +  '<div class="t6cf-legend" aria-label="Tipos de informação usados na avaliação">'
      +    '<span class="t6cf-chip card"><i aria-hidden="true"></i>O que o card traz</span>'
      +    '<span class="t6cf-chip escolha"><i aria-hidden="true"></i>Função, build e técnico</span>'
      +    '<span class="t6cf-chip analise"><i aria-hidden="true"></i>Leitura ClubEfootball</span>'
      +  '</div>'

      +  '<section class="t6cf-processo" aria-labelledby="t6cfProcessoTitulo">'
      +    '<div class="t6cf-section-head">'
      +      '<span>A LÓGICA GERAL</span><h2 id="t6cfProcessoTitulo">O que entra na leitura</h2>'
      +      '<p>Uma visão geral dos grupos considerados.</p>'
      +    '</div>'
      +    '<ol class="t6cf-flow">'
      +      '<li class="t6cf-step card"><span class="t6cf-icon" aria-hidden="true">▣</span><div><small>DADOS DO CARD</small><h3>1. O card oferece</h3><p>Consideramos as características que esta versão realmente traz.</p></div></li>'
      +      '<li class="t6cf-step escolha"><span class="t6cf-icon" aria-hidden="true">⌖</span><div><small>PAPEL AVALIADO</small><h3>2. A função pede</h3><p>Cada posição e função têm necessidades próprias, e o card precisa ser compatível.</p></div></li>'
      +      '<li class="t6cf-step escolha"><span class="t6cf-icon" aria-hidden="true">⌁</span><div><small>CONFIGURAÇÃO EM USO</small><h3>3. A build entra</h3><p>Consideramos a configuração realmente aplicada ao card naquele papel.</p></div></li>'
      +      '<li class="t6cf-step escolha"><span class="t6cf-icon" aria-hidden="true">◆</span><div><small>CONTEXTO</small><h3>4. O técnico completa</h3><p>O técnico e o cenário mudam o contexto em que o card é avaliado.</p></div></li>'
      +      '<li class="t6cf-step analise"><span class="t6cf-icon" aria-hidden="true">✓</span><div><small>COMPATIBILIDADE</small><h3>5. O conjunto precisa fazer sentido</h3><p>Card, função, build e contexto só entram juntos quando são compatíveis.</p></div></li>'
      +      '<li class="t6cf-step resultado"><span class="t6cf-icon" aria-hidden="true">★</span><div><small>ANÁLISE CLUBEFOOTBALL</small><h3>6. O número resume o encaixe</h3><p>A pontuação representa este cenário e pode mudar quando suas escolhas mudam.</p></div></li>'
      +    '</ol>'
      +  '</section>'

      +  '<section class="t6cf-contexto" aria-labelledby="t6cfContextoTitulo">'
      +    '<div><span class="t6cf-context-icon" aria-hidden="true">↔</span><div><small>DUAS NOTAS, DUAS PERGUNTAS</small><h2 id="t6cfContextoTitulo">Objetivos diferentes podem produzir números diferentes.</h2></div></div>'
      +    '<p>A Konami mostra a nota oficial do videogame dentro dos próprios critérios. O ClubEfootball analisa o encaixe desta versão na função e no cenário escolhidos. Não tentamos reproduzir nem substituir a nota oficial.</p>'
      +  '</section>'

      +  '<section class="t6cf-nota" aria-labelledby="t6cfNotaTitulo">'
      +    '<span class="t6cf-shield" aria-hidden="true">◇</span>'
      +    '<div><h2 id="t6cfNotaTitulo">O que este número representa — e o que não representa</h2><p>Representa: o encaixe desta versão do card naquele papel e uma referência para comparar cenários compatíveis. Não representa: a nota oficial da Konami, um valor universal para qualquer posição, uma cópia do cálculo do jogo ou uma promessa de desempenho em partidas.</p></div>'
      +  '</section>'

      +  '<div class="t6cf-actions"><button type="button" class="t6cf-back" data-t6cf-back>← Voltar ao início</button></div>'
      +'</section>';
  }

  function renderiza(){
    var home=document.getElementById('homewrap');
    var elenco=document.getElementById('mtwrap');
    if(!home||!elenco) return false;

    montaAba();
    try{
      document.documentElement.classList.remove('t6ranking','t6elenco','t6filtrosaberto');
      document.documentElement.classList.add('t6semlat');
    }catch(e){}
    elenco.style.display='none';
    ['mline','rkspacer','out','filtros'].forEach(function(id){
      var el=document.getElementById(id);if(el)el.style.display='none';
    });
    home.style.display='block';
    home.innerHTML=pagina();
    marcaAba(true);

    var voltar=home.querySelector('[data-t6cf-back]');
    if(voltar) voltar.addEventListener('click',function(){
      marcaAba(false);
      if(global.RouteState&&typeof global.RouteState.leavePage==='function') global.RouteState.leavePage();
    });
    try{global.scrollTo(0,0);}catch(e){}
    return true;
  }

  global.addEventListener('popstate',function(){global.setTimeout(sincronizaAba,0);});
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',montaAba,{once:true});
  else montaAba();

  global.T6_ROUTE_DEFINITIONS=global.T6_ROUTE_DEFINITIONS||{};
  if(!global.T6_ROUTE_DEFINITIONS[ROUTE]){
    global.T6_ROUTE_DEFINITIONS[ROUTE]={returnRoute:'inicio',render:renderiza};
  }

  global.ComoFuncionaPage=Object.freeze({
    route:ROUTE,
    render:renderiza,
    mountHeaderTab:montaAba,
    inspect:function(){
      return {route:ROUTE,mounted:!!document.getElementById(PAGE_ID),tabMounted:!!document.getElementById(TAB_ID),active:!!document.querySelector('#'+TAB_ID+'.on'),readsOnly:true,motorCalls:0,userStateWrites:0};
    }
  });
})(window);
