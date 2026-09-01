/* bloco JavaScript 8 */

/* v167 — a nota com duas casas: a inteira grande, a decimal miuda. */
function _nd(v){
 if(v===null||v===undefined||isNaN(v)) return '—';
 const s=(+v).toFixed(2).split('.');
 return s[0]+'<span class=ndec>.'+s[1]+'</span>';
}
function _fotoCN(c){
 var u=window.ClubeNovoReadModel?window.ClubeNovoReadModel.foto(c):'';
 return String(u||'').replace(/&/g,'&amp;').replace(/"/g,'&quot;')
   .replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

/* Renderizadores globais só podem atuar quando a rota canônica lhes pertence.
   Se o roteador ainda não existe ou não consegue informar a rota, falha fechado. */
function _t6RotaCanonicaEh(rota){
 try{
  var rs=window.RouteState;
  return !!(rs&&typeof rs.inspect==='function'&&rs.inspect().atual===rota);
 }catch(e){return false;}
}


/* bloco JavaScript 9 */

const ATTRS=["Ofensividade","Controle de bola","Drible","Posse de bola","Passe rasteiro","Passe alto","Finalização","Cabeceio","Cobrança de falta","Efeito","Velocidade","Aceleração","Potência de chute","Salto","Contato físico","Equilíbrio","Resistência","Talento defensivo","Desarme","Envolv. defensivo","Agressividade","Talento de goleiro","Encaixe","Defesa (GO)","Reflexos","Alcance"], SET=[["GOLEIRO",["GOLEIRO"]],["DEFESA",["ZAGUEIRO","LATERAL","VOLANTE"]],["MEIO",["MEIA DE LIGAÇÃO","MEIA LATERAL","MEIA ATACANTE"]],["ATAQUE",["SEGUNDO ATACANTE","PONTA","CENTROAVANTE"]]], SIG={"GOLEIRO":"GO","ZAGUEIRO":"ZC","LATERAL":"LE · LD","VOLANTE":"VOL","MEIA DE LIGAÇÃO":"MLG","MEIA LATERAL":"MLE · MLD","MEIA ATACANTE":"MAT","SEGUNDO ATACANTE":"SA","PONTA":"PTE · PTD","CENTROAVANTE":"CA","★":""}, ROT={"Goleiro defensivo":"defensivo","Goleiro ofensivo":"ofensivo","Zagueiro de combate":"de combate","Zagueiro de saída":"de saída","Lateral defensivo":"defensivo","Lateral ofensivo":"ofensivo","Volante de contenção":"de contenção","Volante de construção":"de construção","Meia armador":"armador","Meia de arranque":"de arranque","Ala finalizador":"finalizador","Ala cruzador":"cruzador","Meia ofensivo":"ofensivo","Atacante infiltrador":"infiltrador","Atacante criador":"criador","Atacante finalizador":"finalizador","Falso nove":"falso nove","Centroavante fixo":"fixo","Centroavante móvel":"móvel","★ GERAL":"★ GERAL"}, FAM=[["★",["★ GERAL"]],["GOLEIRO",["Goleiro defensivo","Goleiro ofensivo"]],["ZAGUEIRO",["Zagueiro de combate","Zagueiro de saída"]],["LATERAL",["Lateral defensivo","Lateral ofensivo"]],["VOLANTE",["Volante de contenção","Volante de construção"]],["MEIA DE LIGAÇÃO",["Meia armador","Meia de arranque"]],["MEIA LATERAL",["Ala finalizador","Ala cruzador"]],["MEIA ATACANTE",["Meia ofensivo","Atacante infiltrador"]],["PONTA",["Atacante criador","Atacante finalizador"]],["CENTROAVANTE",["Falso nove","Centroavante fixo","Centroavante móvel"]]], METAS=["A. Costacurta", "Alessandro Del Piero", "Alessandro Nesta", "Alisson Becker", "Andrea Pirlo", "Andres Iniesta", "Andriy Shevchenko", "Aurelien Tchouameni", "Bradley Barcola", "Cafu", "Carles Puyol", "Clarence Seedorf", "Claude Makelele", "Cristiano Ronaldo", "David Beckham", "Dida", "Didier Drogba", "Eden Hazard", "Edmilson", "Edwin van der Sar", "Erling Haaland", "Fabio Cannavaro", "Federico Valverde", "Fernando Torres", "Filippo Inzaghi", "Francesco Totti", "Franck Ribery", "Frank Lampard", "Frank Rijkaard", "Franz Beckenbauer", "Frenkie de Jong", "Gabriel Batistuta", "Gareth Bale", "Gerard Pique", "Gerd Muller", "Gianluigi Buffon", "Gianluigi Donnarumma", "Giorgio Chiellini", "Giuseppe Bergomi", "Iker Casillas", "Jaap Stam", "Jan Koller", "Javier Zanetti", "Johan Cruyff", "Jude Bellingham", "Jules Kounde", "K. Heinz Rummenigge", "Kaka", "Kevin De Bruyne", "Kylian Mbappe", "Lamine Yamal", "Leonardo Bonucci", "Lilian Thuram", "Lionel Messi", "Lothar Matthaus", "Luis Figo", "Luis Suarez", "Manuel Neuer", "Marco Reus", "Marco van Basten", "Michel Platini", "Neymar Jr", "Oliver Kahn", "Paolo Maldini", "Patrick Vieira", "Paul Scholes", "Pavel Nedved", "Pedri", "Pele", "Peter Schmeichel", "Petr Cech", "Philipp Lahm", "Rafael Leao", "Raphael Varane", "Rio Ferdinand", "Rivaldo", "Roberto Baggio", "Roberto Carlos", "Rodri", "Romario", "Ronaldinho Gaucho", "Ruben Dias", "Ruud Gullit", "Ruud van Nistelrooij", "Steven Gerrard", "T. Alexander-Arnold", "Takehiro Tomiyasu", "Thiago Silva", "Thibaut Courtois", "Toni Kroos", "Vinicius Junior", "Virgil van Dijk", "Wayne Rooney", "Wesley Sneijder", "William Saliba", "Xabi Alonso", "Zico", "Zlatan Ibrahimovic"], MED={"Falso nove":{"b1n":99.2,"b2":88.6,"b3":68.3,"b4":83.2,"b5":0,"n":709},"Goleiro ofensivo":{"b1n":99.7,"b2":95,"b3":0,"b4":81.9,"b5":0,"n":106},"Goleiro defensivo":{"b1n":99.8,"b2":98.1,"b3":0,"b4":82.1,"b5":0,"n":40},"Zagueiro de saída":{"b1n":99.4,"b2":92.9,"b3":62.6,"b4":83.1,"b5":0,"n":317},"Zagueiro de combate":{"b1n":99.1,"b2":98.1,"b3":74.5,"b4":86.3,"b5":0,"n":130},"Lateral ofensivo":{"b1n":99,"b2":86.1,"b3":67.6,"b4":84.3,"b5":0,"n":290},"Lateral defensivo":{"b1n":98.7,"b2":95.2,"b3":71.9,"b4":87.6,"b5":0,"n":84},"Volante de construção":{"b1n":99.4,"b2":92.3,"b3":69.4,"b4":83.2,"b5":0,"n":236},"Volante de contenção":{"b1n":98.8,"b2":93.2,"b3":63.7,"b4":79.6,"b5":0,"n":188},"Meia de arranque":{"b1n":100,"b2":90.4,"b3":68.8,"b4":86.4,"b5":0,"n":303},"Meia armador":{"b1n":98.5,"b2":90.4,"b3":65.2,"b4":80.8,"b5":0,"n":423},"Meia ofensivo":{"b1n":99.4,"b2":92,"b3":61.6,"b4":84.3,"b5":0,"n":574},"Ala finalizador":{"b1n":99.3,"b2":83.3,"b3":67.2,"b4":82.5,"b5":0,"n":797},"Ala cruzador":{"b1n":98.5,"b2":90.6,"b3":63.4,"b4":86,"b5":0,"n":113},"Atacante criador":{"b1n":99,"b2":92.4,"b3":63.9,"b4":84.4,"b5":0,"n":228},"Atacante finalizador":{"b1n":99.5,"b2":86.9,"b3":68.3,"b4":83.6,"b5":0,"n":717},"Centroavante fixo":{"b1n":99.1,"b2":94.9,"b3":61.8,"b4":83.8,"b5":0,"n":101},"Centroavante móvel":{"b1n":99.2,"b2":88.6,"b3":68.3,"b4":83.2,"b5":0,"n":709},"Atacante infiltrador":{"b1n":99.1,"b2":93,"b3":65.9,"b4":84,"b5":0,"n":261},"Meia central armador":{"b1n":98.5,"b2":90.4,"b3":65.2,"b4":80.8,"b5":0,"n":423},"Meia central de chegada":{"b1n":100,"b2":90.4,"b3":68.8,"b4":86.4,"b5":0,"n":303},"Meia de lado por dentro":{"b1n":99.3,"b2":83.3,"b3":67.2,"b4":82.5,"b5":0,"n":797},"Meia de lado por fora":{"b1n":98.5,"b2":90.6,"b3":63.4,"b4":86,"b5":0,"n":113},"Meia lateral atacante":{"b1n":99.3,"b2":83.3,"b3":67.2,"b4":82.5,"b5":0,"n":797},"Meia lateral cruzador":{"b1n":98.5,"b2":90.6,"b3":63.4,"b4":86,"b5":0,"n":113},"Meia ofensivo armador":{"b1n":99.4,"b2":92,"b3":61.6,"b4":84.3,"b5":0,"n":574},"Segundo atacante":{"b1n":99.1,"b2":93,"b3":65.9,"b4":84,"b5":0,"n":261},"Ponta criadora":{"b1n":99,"b2":92.4,"b3":63.9,"b4":84.4,"b5":0,"n":228},"Ponta finalizadora":{"b1n":99.5,"b2":86.9,"b3":68.3,"b4":83.6,"b5":0,"n":717}};
const D=(function(){
// ===========================================================================
//  AS LINHAS VEM DO BANCO — E NAO TODAS DE UMA VEZ
// ===========================================================================
//  ⛔ 18/08 — ORDEM DO LUIS:
//     "A pagina pros usuarios tem que ser dinamica, nao pode ficar esperando
//      dezessete segundos pra carregar tudo. E nem precisa carregar tudo:
//      precisa carregar o que esta dando na pagina. O resto pode carregar em
//      segundo plano."
//
//  O QUE ACONTECIA: as 17.023 linhas vinham em 18 requisicoes SINCRONAS antes
//  de qualquer coisa aparecer. Medido em 18/08, servindo de um servidor local
//  (o melhor caso possivel): 17,5 SEGUNDOS de tela branca. Pela internet, mais.
//  E o contador do cabecalho e escrito na geracao, entao ele mostrava
//  "17.187 de 18.598 linhas" com o painel vazio — parecia defeito, e nao era.
//
//  AGORA: a PRIMEIRA leva vem sincrona (a tela abre com ela, em ~1s) e o resto
//  vem em SEGUNDO PLANO, empurrando dentro do mesmo D e mandando a tela se
//  redesenhar a cada leva.
//
//  ⛔ POR QUE ISTO NAO OBRIGA A MEXER NAS 193 FUNCOES: `const D` continua sendo
//     o mesmo ARRAY desde o primeiro instante. `const` prende a referencia, nao
//     o conteudo — entao `D.push(...)` e legal e todo mundo que le o D ve o que
//     chegou. Quem redesenha ja existe e se chama render().
// ===========================================================================
  /* A lista recebe somente DTOs aprovados pelo contrato versionado do
     clube_novo. A camada de leitura rejeita teste, pendência e build sem os
     dois motores antes que qualquer cálculo ou desenho veja a linha. */
  var CN = window.ClubeNovoReadModel;
  var PAGINA = 1000;
  var PRIMEIRA = 2;   // levas que vem antes da tela abrir
  function erroNaTela(e){
    var codigo=e&&e.code||'ERRO';
    window.CLUBE_NOVO_FRONTEND_ESTADO={
      codigo:codigo,
      mensagem:String(e&&e.message||'O contrato público de leitura ainda não está disponível.')
    };
    /* A falha encerra esta carga. Marcar o estado como terminal impede que o
       Elenco espere para sempre um evento de conclusão que não será emitido. */
    window.ENC_DADOS_COMPLETOS=true;
    window.ENC_DADOS_INDISPONIVEIS=true;
    function montaErro(){
      var antigo=document.getElementById('_estado_builds_publicadas');
      if(antigo)antigo.remove();
      var caixa=document.createElement('section');
      caixa.id='_estado_builds_publicadas';
      caixa.setAttribute('role','status');
      caixa.style.cssText='margin:88px auto 24px;max-width:720px;padding:22px 24px;'
        +'border:1px solid #344054;border-radius:14px;background:#111827;color:#e6edf3;'
        +'font:15px/1.5 system-ui;text-align:center';
      var titulo=document.createElement('h2');
      titulo.style.cssText='margin:0 0 8px;color:#f0a531;font-size:19px';
      titulo.textContent='Builds publicadas ainda indisponíveis';
      var texto=document.createElement('p');
      texto.style.cssText='margin:0;color:#aab4c3';
      texto.textContent=(e&&e.code==='SEM_BUILD_PUBLICADA')
        ? 'O processamento ainda não produziu uma build completa e publicada.'
        : String(e&&e.message||'O contrato público de leitura ainda não está disponível.');
      var regra=document.createElement('p');
      regra.style.cssText='margin:9px 0 0;color:#7f8b9d;font-size:12px';
      regra.textContent='A tela não usa dados de teste, linhas parciais nem fontes legadas.';
      caixa.appendChild(titulo);caixa.appendChild(texto);caixa.appendChild(regra);
      var alvo=document.getElementById('out')||document.querySelector('main')||document.body;
      alvo.insertBefore(caixa,alvo.firstChild||null);
    }
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',montaErro,{once:true});
    else montaErro();
  }

  function paginaInicial(de){
    if(!CN)throw new Error('Camada de leitura do clube_novo não carregada.');
    return CN.listarSync({offset:de,limit:PAGINA});
  }

  var fora = [], de = 0, acabou = false;
  // ⛔ 18/08 — A MESMA FUNCAO APARECIA DUAS VEZES NA FICHA DO CARD.
  //    Sem `order`, o PostgREST nao garante ordem entre uma pagina e a
  //    seguinte: a mesma linha vem em duas levas e OUTRA nunca vem. O
  //    `order=card_id,funcao` no endereco resolve; este cadeado e a segunda
  //    rede — se a ordem falhar de novo, entra uma vez so.
  var _visto = {};
  function _entra(L){
    if (L && L.id !== undefined && L.tipo !== undefined){
      var cn=L.__cn||{};
      var ch = cn.generationId !== undefined
        ? [cn.generationId,cn.cardId,cn.functionId].join('|')
        : L.id + '|' + L.tipo;
      if (_visto[ch]) return;
      _visto[ch] = 1;
    }
    fora.push(L);
  }
  // ---------- a primeira leva, sincrona: e ela que faz a tela abrir ----------
  try {
    for (var v = 0; v < PRIMEIRA && !acabou; v++) {
      var p = paginaInicial(de);
      for (var k = 0; k < p.length; k++) _entra(p[k]);
      if (p.length < PAGINA) acabou = true;
      de += PAGINA;
    }
    if (!fora.length) {
      var vazio=new Error('Ainda não há builds completas e publicadas para exibir.');
      vazio.code='SEM_BUILD_PUBLICADA';
      throw vazio;
    }
    console.log('[encaixe] ' + fora.length + ' linhas na primeira leva — a tela ja pode abrir');
  } catch (e) {
    /* A âncora e as páginas iniciais formam uma única abertura atômica.
       Se qualquer uma falhar, nenhuma fração pode sobreviver como ranking. */
    fora.length=0;_visto={};erroNaTela(e);acabou=true;return fora;
  }

  // ---------- o resto, em segundo plano ----------
  //  ⛔ Cada leva que chega entra no MESMO array e manda redesenhar. A tela vai
  //     enchendo na frente do usuario em vez de ficar branca esperando.
  function aviso(txt){
    try{
      var d = document.getElementById('_carregando_banco');
      if (!d && txt){
        d = document.createElement('div');
        d.id = '_carregando_banco';
        d.style.cssText = 'position:fixed;right:12px;bottom:56px;z-index:99999;'
          + 'background:#132a1f;color:#9fe8c0;border:1px solid #1f7a4d;'
          + 'border-radius:8px;padding:6px 11px;font:12px system-ui;opacity:.93';
        document.body.appendChild(d);
      }
      if (d){ if (txt) d.textContent = txt; else d.remove(); }
    }catch(e){}
  }
  function redesenha(){
    // guarda onde a pagina estava: redesenhar nao pode jogar o leitor pro topo
    var _sy = window.pageYOffset || document.documentElement.scrollTop || 0;
    // ⛔ 18/08 — O TOPO DA FUNCAO E MEMORIZADO (_TOPO), e quem memoriza no meio
    //    do carregamento guarda um topo PROVISORIO: a primeira leva tinha 2.000
    //    linhas, o Goleiro ofensivo mais alto dela valia menos que o que chegou
    //    depois — e o card virou "110,21% do topo". Nao e conta errada, e conta
    //    feita cedo demais. A cada leva o topo se apaga e nasce de novo.
    try{ if(typeof _TOPO !== 'undefined') _TOPO = {}; }catch(e){}
    // Primeiro a passada que carimba pacote e refaz o fisico, DEPOIS desenha.
    // As superficies vigentes reagem ao carregamento pelos seus donos atuais;
    // a Home legada nao participa desta passada.
    try{ if (typeof window._pos_D === 'function') window._pos_D(); }catch(e){}
    try{ if (_t6RotaCanonicaEh('ranking')&&typeof render  === 'function') render(); }catch(e){}
    try{ if (_t6RotaCanonicaEh('meutime')&&typeof desenha === 'function') desenha(); }catch(e){}
    if (_sy > 0) { try{ window.scrollTo(0, _sy); }catch(e){} }
  }
  function proxima(){
    if (acabou) { aviso(''); redesenha();
                  /* O catálogo carrega em silêncio para não repintar a tela a
                     cada leva. Ao fim, porém, o Elenco precisa uma única
                     reavaliação: alguns moldes dos titulares podem ter
                     chegado depois da primeira pintura. */
                  try{
                    window.ENC_DADOS_COMPLETOS = true;
                    window.dispatchEvent(new Event('encaixe:dados-completos'));
                  }catch(e){}
                  console.log('[encaixe] ' + fora.length + ' linhas no total'); return; }
    CN.listar({offset:de,limit:PAGINA}).then(function(q){
      try{
        for (var k = 0; k < q.length; k++) _entra(q[k]);
        if (q.length < PAGINA) acabou = true;
        de += PAGINA;
        aviso('carregando o resto — ' + fora.length.toLocaleString('pt-BR') + ' linhas');
        // ⛔ 18/08 (noite) — NAO SE REDESENHA A CADA LEVA. Ordem do Luis:
        //    "carrega um pouco, a tela fica piscando, carrega outro pouco —
        //     esta horrivel." Cada redesenho refaz o painel inteiro e as fotos
        //    recarregam: sao 17 piscadas ate o fim. A tela ja abre com as levas
        //    sincronas (as 2.000 mais fortes + 2.000), que e o que aparece na
        //    primeira dobra; o resto entra no D em silencio e a tela se redesenha
        //    UMA vez, quando acaba. O aviso do canto mostra o progresso.
        setTimeout(proxima, 0);
      }catch(e){
        aviso('');fora.length=0;_visto={};acabou=true;erroNaTela(e);redesenha();
        console.warn('[encaixe] lote canônico rejeitado',e);
      }
    }).catch(function(e){
      aviso('');fora.length=0;_visto={};acabou=true;erroNaTela(e);redesenha();
      console.warn('[encaixe] leitura canônica interrompida',e);
    });
  }
  document.addEventListener('DOMContentLoaded', function(){
    aviso('carregando o resto — ' + fora.length.toLocaleString('pt-BR') + ' linhas');
    setTimeout(proxima, 60);
  });

  return fora;
})();

/* Gate único das superfícies que dependem de Builds. O catálogo cadastral de
   Home, Boxes, Busca e Ficha não passa por aqui e continua independente. */
function _t6BloqueioBuildsElenco(){
 var estado=window.CLUBE_NOVO_FRONTEND_ESTADO;
 if(!estado)return null;
 if(estado.codigo==='PUBLICACAO_BUILD_INDISPONIVEL'||estado.codigo==='SEM_BUILD_PUBLICADA')return estado;
 try{
  if(!(D||[]).some(function(c){return !!(c&&c.id!=='MOLDE');}))return estado;
 }catch(e){return estado;}
 return null;
}

function _t6LimpaEstadoBloqueadoElenco(w){
 if(!w||!w.dataset||w.dataset.t6BuildsBloqueadas!=='1')return;
 delete w.dataset.t6BuildsBloqueadas;
 w.removeAttribute('role');w.removeAttribute('aria-live');w.removeAttribute('aria-label');
 ['max-width','margin','padding','border','border-radius','background','color',
  'font','text-align','visibility','min-height'].forEach(function(p){w.style.removeProperty(p);});
}

function _t6RenderEstadoBloqueadoElenco(estado){
 var w=document.getElementById('mtwrap');if(!w)return true;
 var contrato=estado&&estado.codigo==='PUBLICACAO_BUILD_INDISPONIVEL';
 w.dataset.t6BuildsBloqueadas='1';w.setAttribute('role','status');
 w.setAttribute('aria-live','polite');w.setAttribute('aria-label','Elenco indisponível');
 /* O texto fica deliberadamente curto: o aprimorador legado considera apenas
    painéis extensos como campo montado e, assim, não o redesenha sobre o gate. */
 w.textContent=contrato
  ?'Builds publicadas indisponíveis. O Elenco está bloqueado: falta o contrato oficial de pontuação final. Nenhum campo, média, seleção ou otimização foi aberto.'
  :'Builds publicadas indisponíveis. O Elenco está bloqueado e não usa linhas parciais, dados de teste nem fontes legadas.';
 var estilo={'max-width':'720px','margin':'88px auto 24px','padding':'22px 24px',
  'border':'1px solid #344054','border-radius':'14px','background':'#111827',
  'color':'#e6edf3','font':'15px/1.5 system-ui','text-align':'center',
  'visibility':'visible','min-height':'0'};
 Object.keys(estilo).forEach(function(p){w.style.setProperty(p,estilo[p],'important');});
 return true;
}

/* Não existe mais um catálogo genérico baixado pelo navegador. Boxes, Home,
   Busca e Ficha possuem contratos públicos independentes e cada dona consulta
   somente a sua view. Além de evitar 43 mil cards em memória, isso impede que
   uma tela volte a juntar catálogo e Build por ordem de chegada. */

const CAT=[["Precisão +1",0,[[4,1],[5,1],[6,1],[12,1]]],["Precisão +2",0,[[4,2],[5,2],[6,2],[12,2]]],["Precisão +3",0,[[4,3],[5,3],[6,3],[12,3]]],["Disputa Aérea +1",0,[[6,1],[7,1],[13,1],[14,1]]],["Disputa Aérea +2",0,[[6,2],[7,2],[13,2],[14,2]]],["Disputa Aérea +3",0,[[6,3],[7,3],[13,3],[14,3]]],["Bloqueio Aéreo +1",0,[[7,1],[13,1],[14,1],[17,1]]],["Bloqueio Aéreo +2",0,[[7,2],[13,2],[14,2],[17,2]]],["Bloqueio Aéreo +3",0,[[7,3],[13,3],[14,3],[17,3]]],["Agilidade +1",0,[[10,1],[11,1],[15,1],[16,1]]],["Agilidade +2",0,[[10,2],[11,2],[15,2],[16,2]]],["Agilidade +3",0,[[10,3],[11,3],[15,3],[16,3]]],["Equilibrista +1",0,[[0,1],[11,1],[16,1],[17,1]]],["Equilibrista +2",0,[[0,2],[11,2],[16,2],[17,2]]],["Equilibrista +3",0,[[0,3],[11,3],[16,3],[17,3]]],["Física +1",0,[[1,1],[3,1],[14,1],[15,1]]],["Física +2",0,[[1,2],[3,2],[14,2],[15,2]]],["Física +3",0,[[1,3],[3,3],[14,3],[15,3]]],["Condução Técnica +1",0,[[2,1],[3,1],[10,1],[15,1]]],["Condução Técnica +2",0,[[2,2],[3,2],[10,2],[15,2]]],["Condução Técnica +3",0,[[2,3],[3,3],[10,3],[15,3]]],["Arrancada +1",0,[[2,1],[10,1],[12,1],[14,1]]],["Arrancada +2",0,[[2,2],[10,2],[12,2],[14,2]]],["Arrancada +3",0,[[2,3],[10,3],[12,3],[14,3]]],["Contra-ataque +1",0,[[4,1],[14,1],[18,1],[19,1]]],["Contra-ataque +2",0,[[4,2],[14,2],[18,2],[19,2]]],["Contra-ataque +3",0,[[4,3],[14,3],[18,3],[19,3]]],["Cruzamento +1",0,[[5,1],[9,1],[10,1],[16,1]]],["Cruzamento +2",0,[[5,2],[9,2],[10,2],[16,2]]],["Cruzamento +3",0,[[5,3],[9,3],[10,3],[16,3]]],["Defesa +1",0,[[11,1],[13,1],[17,1],[18,1]]],["Defesa +2",0,[[11,2],[13,2],[17,2],[18,2]]],["Defesa +3",0,[[11,3],[13,3],[17,3],[18,3]]],["Duelo (Divididas) +1",0,[[10,1],[16,1],[17,1],[18,1]]],["Duelo (Divididas) +2",0,[[10,2],[16,2],[17,2],[18,2]]],["Duelo (Divididas) +3",0,[[10,3],[16,3],[17,3],[18,3]]],["Fantasia +1",0,[[1,1],[2,1],[6,1],[15,1]]],["Fantasia +2",0,[[1,2],[2,2],[6,2],[15,2]]],["Fantasia +3",0,[[1,3],[2,3],[6,3],[15,3]]],["Cobrança de Falta +1",0,[[6,1],[8,1],[9,1],[12,1]]],["Cobrança de Falta +2",0,[[6,2],[8,2],[9,2],[12,2]]],["Cobrança de Falta +3",0,[[6,3],[8,3],[9,3],[12,3]]],["Qualidade Goleiro +1",0,[[21,1],[22,1],[23,1],[24,1]]],["Qualidade Goleiro +2",0,[[21,2],[22,2],[23,2],[24,2]]],["Qualidade Goleiro +3",0,[[21,3],[22,3],[23,3],[24,3]]],["Motor do Time +1",0,[[11,1],[14,1],[16,1],[20,1]]],["Motor do Time +2",0,[[11,2],[14,2],[16,2],[20,2]]],["Motor do Time +3",0,[[11,3],[14,3],[16,3],[20,3]]],["Sem Bola +1",0,[[0,1],[10,1],[11,1],[16,1]]],["Sem Bola +2",0,[[0,2],[10,2],[11,2],[16,2]]],["Sem Bola +3",0,[[0,3],[10,3],[11,3],[16,3]]],["Criador de Jogadas +1",0,[[0,1],[1,1],[4,1],[12,1]]],["Criador de Jogadas +2",0,[[0,2],[1,2],[4,2],[12,2]]],["Criador de Jogadas +3",0,[[0,3],[1,3],[4,3],[12,3]]],["Passe +1",0,[[4,1],[5,1],[9,1],[12,1]]],["Passe +2",0,[[4,2],[5,2],[9,2],[12,2]]],["Passe +3",0,[[4,3],[5,3],[9,3],[12,3]]],["Vigor Físico +1",0,[[13,1],[14,1],[15,1],[16,1]]],["Vigor Físico +2",0,[[13,2],[14,2],[15,2],[16,2]]],["Vigor Físico +3",0,[[13,3],[14,3],[15,3],[16,3]]],["Reconstrução +1",0,[[4,1],[17,1],[19,1],[20,1]]],["Reconstrução +2",0,[[4,2],[17,2],[19,2],[20,2]]],["Reconstrução +3",0,[[4,3],[17,3],[19,3],[20,3]]],["Regista +1",0,[[3,1],[4,1],[17,1],[18,1]]],["Regista +2",0,[[3,2],[4,2],[17,2],[18,2]]],["Regista +3",0,[[3,3],[4,3],[17,3],[18,3]]],["Defesaça +1",0,[[21,1],[23,1],[24,1],[25,1]]],["Defesaça +2",0,[[21,2],[23,2],[24,2],[25,2]]],["Defesaça +3",0,[[21,3],[23,3],[24,3],[25,3]]],["Chute +1",0,[[1,1],[6,1],[12,1],[14,1]]],["Chute +2",0,[[1,2],[6,2],[12,2],[14,2]]],["Chute +3",0,[[1,3],[6,3],[12,3],[14,3]]],["Duelo +1",0,[[10,1],[17,1],[18,1],[19,1]]],["Duelo +2",0,[[10,2],[17,2],[18,2],[19,2]]],["Duelo +3",0,[[10,3],[17,3],[18,3],[19,3]]],["Defesa (Roubo) +1",0,[[11,1],[14,1],[18,1],[20,1]]],["Defesa (Roubo) +2",0,[[11,2],[14,2],[18,2],[20,2]]],["Defesa (Roubo) +3",0,[[11,3],[14,3],[18,3],[20,3]]],["Força +1",0,[[10,1],[12,1],[13,1],[14,1]]],["Força +2",0,[[10,2],[12,2],[13,2],[14,2]]],["Força +3",0,[[10,3],[12,3],[13,3],[14,3]]],["Instinto Artilheiro +1",0,[[0,1],[1,1],[6,1],[11,1]]],["Instinto Artilheiro +2",0,[[0,2],[1,2],[6,2],[11,2]]],["Instinto Artilheiro +3",0,[[0,3],[1,3],[6,3],[11,3]]],["Técnica +1",0,[[1,1],[2,1],[3,1],[4,1]]],["Técnica +2",0,[[1,2],[2,2],[3,2],[4,2]]],["Técnica +3",0,[[1,3],[2,3],[3,3],[4,3]]],["Precisão +1",1,[[4,1],[5,1],[6,1],[12,1]]],["Disputa Aérea +1",1,[[6,1],[7,1],[13,1],[14,1]]],["Bloqueio Aéreo +1",1,[[7,1],[13,1],[14,1],[17,1]]],["Agilidade +1",1,[[10,1],[11,1],[15,1],[16,1]]],["Equilibrista +1",1,[[0,1],[11,1],[16,1],[17,1]]],["Física +1",1,[[1,1],[3,1],[14,1],[15,1]]],["Condução Técnica +1",1,[[2,1],[3,1],[10,1],[15,1]]],["Arrancada +1",1,[[2,1],[10,1],[12,1],[14,1]]],["Contra-ataque +1",1,[[4,1],[14,1],[18,1],[19,1]]],["Cruzamento +1",1,[[5,1],[9,1],[10,1],[16,1]]],["Defesa +1",1,[[11,1],[13,1],[17,1],[18,1]]],["Duelo (Divididas) +1",1,[[10,1],[16,1],[17,1],[18,1]]],["Fantasia +1",1,[[1,1],[2,1],[6,1],[15,1]]],["Cobrança de Falta +1",1,[[6,1],[8,1],[9,1],[12,1]]],["Qualidade Goleiro +1",1,[[21,1],[22,1],[23,1],[24,1]]],["Motor do Time +1",1,[[11,1],[14,1],[16,1],[20,1]]],["Sem Bola +1",1,[[0,1],[10,1],[11,1],[16,1]]],["Criador de Jogadas +1",1,[[0,1],[1,1],[4,1],[12,1]]],["Passe +1",1,[[4,1],[5,1],[9,1],[12,1]]],["Vigor Físico +1",1,[[13,1],[14,1],[15,1],[16,1]]],["Reconstrução +1",1,[[4,1],[17,1],[19,1],[20,1]]],["Regista +1",1,[[3,1],[4,1],[17,1],[18,1]]],["Defesaça +1",1,[[21,1],[23,1],[24,1],[25,1]]],["Chute +1",1,[[1,1],[6,1],[12,1],[14,1]]],["Duelo +1",1,[[10,1],[17,1],[18,1],[19,1]]],["Defesa (Roubo) +1",1,[[11,1],[14,1],[18,1],[20,1]]],["Força +1",1,[[10,1],[12,1],[13,1],[14,1]]],["Instinto Artilheiro +1",1,[[0,1],[1,1],[6,1],[11,1]]],["Técnica +1",1,[[1,1],[2,1],[3,1],[4,1]]]];
// ===== MOTOR DE BUILD — gravado no sistema (roda no navegador) =====
// Regra única: maximizar os pontos do Bloco 1 (barras + ímpeto fabricado).
const MB={shooting:[6,8,9],passing:[4,5],dribbling:[1,2,3],dexterity:[0,11,15],lowerBodyStrength:[10,12,16],aerialStrength:[7,13,14],defending:[17,18,20,19],gk1:[21,13],gk2:[23,25],gk3:[22,24]};
const MBN={shooting:"Chute",passing:"Passe",dribbling:"Drible",dexterity:"Destreza",lowerBodyStrength:"Força pernas",aerialStrength:"Força aérea",defending:"Defesa",gk1:"GO reflexo/salto",gk2:"GO defesa/alcance",gk3:"GO encaixe/reflexos"};
const MBK=Object.keys(MB);
const custoNivel=n=>Math.ceil(n/4);
const ACCU=(()=>{const a=[0];let t=0;for(let n=1;n<=25;n++){t+=custoNivel(n);a[n]=t;}return a;})();
function expand(pairs){const v=new Array(26).fill(0);(pairs||[]).forEach(([i,x])=>v[i]=x);return v;}
const INCP=p=>0.25*p/12;
function notaDe(vals,arows){let s=0;for(const r of arows){if(!r[1])continue;const d=vals[r[0]]-r[2];
 s+= d>=0 ? _bon(d,r[1]) : (r[1]===1?0:-_fal(-d,r[1]));}return Math.round(s*10)/10;}
function aplicar(start,lvl){const v=start.slice();for(const b of MBK){const n=lvl[b]||0;if(n)MB[b].forEach(i=>{v[i]=Math.min(99,v[i]+n);});}return v;}
function gastoDe(lvl){let t=0;for(const b of MBK)t+=ACCU[lvl[b]||0];return t;}
// distribuição ÓTIMA EXATA por programação dinâmica (barras separáveis; Impulsão é o par aéreo+gk1)
function distOtima(start,arows,orc,add,bf){
 const R={};arows.forEach(r=>{if(r[1])R[r[0]]={a:r[2],p:r[1]};});
 /* v131 · o buff da habilidade entra ANTES do DP decidir a barra — senao o motor
    gasta ponto onde a habilidade ja cobre (era a causa de 122 de 125 piorarem) */
 const nA=(i,n)=>{const r=R[i];if(!r)return 0;const A=(add&&add[i])||0;const B=bf&&bf[i];
  /* ⛔ 25/08 — A CONTA DO EFEITO, ESCRITA AQUI E NAO POR eval().
     Ate hoje esta linha era corrigida em tempo de execucao: um bloco la
     embaixo pegava distOtima.toString(), trocava este texto e refazia a
     funcao com eval(). Funcionava — e falhava CALADO: bastava um espaco
     mudar aqui para o indexOf nao achar, DIST_OTIMA_CERTA virar false e o
     motor voltar a gastar ponto onde a habilidade ja cobre, sem aviso.
     A troca e exatamente a mesma; agora e o proprio codigo.
     A regra (equacao.py): o efeito da habilidade e ceil(ref*pct/100+flat)
     sobre a REFERENCIA (base+barras), somado DEPOIS, e sem trava em 99. */
  const f=(v)=>{const pre=Math.min(99,v); let w=pre+A; if(B)w=w+Math.ceil(pre*B[0]/100+B[1]);
   const d=w-r.a;return d>=0?_bon(d,r.p):(r.p===1?0:-P.K*_fal(-d,r.p));};
  return f(start[i]+n)-f(start[i]);};
 const grupos=[];
 for(const b of MBK){if(b==="aerialStrength"||b==="gk1")continue;
  const ids=MB[b].filter(i=>R[i]);
  if(!ids.length){grupos.push({bar:[b],opts:[[0,0,[0]]]});continue;}
  const opts=[];for(let n=0;n<=25;n++){if(ACCU[n]>orc)break;let g=0;for(const i of ids)g+=nA(i,n);opts.push([ACCU[n],g,[n]]);}
  grupos.push({bar:[b],opts});}
 {const opts=[];for(let a=0;a<=25;a++){if(ACCU[a]>orc)break;for(let k=0;k<=25;k++){const c=ACCU[a]+ACCU[k];if(c>orc)break;
   opts.push([c,nA(7,a)+nA(14,a)+nA(21,k)+nA(13,a+k),[a,k]]);}}
  grupos.push({bar:["aerialStrength","gk1"],opts});}
 let dp=new Float64Array(orc+1).fill(-1e18);dp[0]=0;const tr=[];
 for(const g of grupos){const nd=new Float64Array(orc+1).fill(-1e18),ch=new Int32Array(orc+1).fill(-1),pc=new Int32Array(orc+1).fill(-1);
  for(let c=0;c<=orc;c++){if(dp[c]<-1e17)continue;for(let oi=0;oi<g.opts.length;oi++){const t=c+g.opts[oi][0];if(t>orc)continue;const v=dp[c]+g.opts[oi][1];if(v>nd[t]){nd[t]=v;ch[t]=oi;pc[t]=c;}}}
  tr.push({ch,pc});dp=nd;}
 let bc=0;for(let c=1;c<=orc;c++)if(dp[c]>dp[bc])bc=c;
 const lvl={};MBK.forEach(b=>lvl[b]=0);let cc=bc;
 for(let gi=grupos.length-1;gi>=0;gi--){const oi=tr[gi].ch[cc];if(oi>=0){grupos[gi].bar.forEach((b,j)=>lvl[b]=grupos[gi].opts[oi][2][j]);cc=tr[gi].pc[cc];}}
 return lvl;
}
// build ÓTIMO do card: escolhe ímpeto fabricável + distribuição
function buildOtimo(c){
 const nm=expand(c.nm), arows=c.arows, orc=c.orc||0;
 const pes=new Set(arows.filter(r=>r[1]).map(r=>r[0]));
 const base=c.base;
 let best=null;
 const bf=buffDe(habsDe(c));
 const tenta=(extra,nome)=>{
  const add=base.map((x,i)=>nm[i]+(extra?extra[i]:0)+tecVet(tecAtual(c))[i]);
  const lvl=distOtima(base,arows,orc,add,bf);
  const vals=aplicar(base,lvl).map((x,i)=>{let w=x+add[i];return bf[i]?aplicaBuff(w,bf[i][0],bf[i][1]):w;});
  const n=notaDe(vals,arows);
  if(!best||n>best.nota)best={nota:n,lvl,vals,fab:nome?[nome]:[],start:base,add};
 };
 tenta(null,null);
 const L=CAT.filter(x=>x[1]===0&&x[2].some(([i])=>pes.has(i)));
 const R=CAT.filter(x=>x[1]===1&&x[2].some(([i])=>pes.has(i)));
 if(c.sl&&c.sl[0])for(const x of L)tenta(expand(x[2]),x[0]);
 if(c.sl&&c.sl[1])for(const x of R)tenta(expand(x[2]),x[0]);
 if(c.sl&&c.sl[0]&&c.sl[1])for(const a of L)for(const b of R){const va=expand(a[2]),vb=expand(b[2]);tenta(va.map((x,i)=>x+vb[i]),a[0]+" + "+b[0]);}
 if(best){let g=orc-gastoDe(best.lvl);
  if(g>0){const ordem=MBK.slice().sort((a,b)=>Math.max(...MB[b].map(i=>{const r=arows.find(x=>x[0]===i);return r?r[1]:0}))-Math.max(...MB[a].map(i=>{const r=arows.find(x=>x[0]===i);return r?r[1]:0})));
   for(const b of ordem){while((best.lvl[b]||0)<25){const c2=ACCU[(best.lvl[b]||0)+1]-ACCU[best.lvl[b]||0];if(c2>g)break;best.lvl[b]=(best.lvl[b]||0)+1;g-=c2;}if(g<=0)break;}
   best.vals=aplicar(best.start,best.lvl).map((x,i)=>{let w=x+(best.add[i]||0);
    return bf[i]?aplicaBuff(w,bf[i][0],bf[i][1]):w;});}}
 return best;
}

const ESTV={"Falso nove":{"Atacante Pivô":22.5,"Artilheiro":100.0,"Lateral móvel":0.5,"Ala produtivo":2.9,"Puxa marcação":3.7,"Armador criativo":2.4,"Jog. de infiltração":3.0,"Clássica nº 10":0.4,"Zagueiro ofensivo":0.0,"Meia versátil":0.0},"Goleiro ofensivo":{"Goleiro ofensivo":100.0,"Pivô":1.0,"Goleiro defensivo":0.5},"Goleiro defensivo":{"Goleiro defensivo":100.0,"Goleiro ofensivo":5.1},"Zagueiro de saída":{"Zagueiro ofensivo":5.6,"Atacante surpresa":4.1,"Orquestrador":2.5,"Zagueiro defensivo":10.8,"Provocador":100.0,"Primeiro volante":4.1,"Lateral atacante":0.8,"Especialista em cruz.":0.7,"Meia versátil":1.3,"Homem de área":0.2,"Jog. de infiltração":0.2,"Zagueiro de saída":0.5,"O destruidor":0.5},"Zagueiro de combate":{"O destruidor":100.0,"Zagueiro de saída":1.0},"Lateral ofensivo":{"Atacante surpresa":1.3,"Provocador":5.4,"Zagueiro ofensivo":100.0,"Lateral atacante":11.6,"Meia versátil":2.7,"Especialista em cruz.":2.0,"Ala produtivo":1.1,"O destruidor":4.8,"Orquestrador":1.4,"Armador criativo":0.7,"Jog. de infiltração":0.7,"Primeiro volante":0.5,"Artilheiro":0.4,"Homem de área":0.2,"Lateral ofensivo":0.7},"Lateral defensivo":{"Zagueiro defensivo":100.0,"Lateral atacante":0.6,"Lateral ofensivo":2.5},"Volante de contenção":{"O destruidor":69.8,"Primeiro volante":100.0,"Provocador":10.0,"Zagueiro defensivo":2.3,"Zagueiro ofensivo":9.6,"Jog. de infiltração":4.6,"Armador criativo":2.7,"Artilheiro":0.5,"Especialista em cruz.":1.4,"Orquestrador":0.9,"Meia versátil":0.5},"Volante de construção":{"Meia versátil":72.3,"Orquestrador":100.0},"Meia armador":{"Orquestrador":100.0,"O destruidor":10.5,"Primeiro volante":12.1,"Armador criativo":22.1,"Zagueiro ofensivo":4.7,"Clássica nº 10":3.0,"Lateral atacante":0.9,"Zagueiro defensivo":0.6,"Lateral móvel":0.4,"Atacante Pivô":0.7,"Ala produtivo":0.7,"Especialista em cruz.":1.9,"Puxa marcação":0.2,"Provocador":1.3,"Artilheiro":0.4,"Homem de área":0.2,"Meia versátil":0.6},"Meia de arranque":{"Meia versátil":100.0,"Jog. de infiltração":36.7,"O destruidor":0.2,"Orquestrador":0.4},"Meia ofensivo":{"Armador criativo":100.0,"Meia versátil":8.1,"Ala produtivo":3.3,"Orquestrador":7.7,"Atacante Pivô":5.9,"Clássica nº 10":18.2,"Artilheiro":3.9,"Lateral móvel":1.2,"Zagueiro ofensivo":0.6,"Especialista em cruz.":0.6,"Homem de área":0.5,"Lateral atacante":0.2,"Primeiro volante":0.2,"Jog. de infiltração":0.5},"Ala finalizador":{"Jog. de infiltração":100.0,"Artilheiro":18.8,"Armador criativo":56.3,"Zagueiro ofensivo":17.3,"Puxa marcação":1.2,"Ala produtivo":24.7,"Clássica nº 10":2.4,"Lateral atacante":3.6,"Orquestrador":4.4,"Zagueiro defensivo":3.6,"Atacante Pivô":3.9,"Homem de área":0.7,"Provocador":0.3,"Primeiro volante":0.3,"O destruidor":1.0,"Especialista em cruz.":0.5},"Ala cruzador":{"Lateral móvel":42.0,"Meia versátil":98.4,"Especialista em cruz.":100.0,"Jog. de infiltração":2.7},"Atacante finalizador":{"Jog. de infiltração":14.6,"Artilheiro":13.8,"Ala produtivo":100.0,"Puxa marcação":0.7,"Clássica nº 10":1.1,"Zagueiro ofensivo":1.4,"Meia versátil":1.9,"Orquestrador":1.6,"Atacante Pivô":3.8,"Homem de área":0.4,"Zagueiro defensivo":0.1,"Primeiro volante":0.1,"Lateral atacante":0.1,"O destruidor":0.1,"Provocador":0.2,"Armador criativo":0.1},"Atacante criador":{"Armador criativo":100.0,"Lateral móvel":34.9,"Especialista em cruz.":10.5,"Provocador":1.0},"Centroavante móvel":{"Atacante Pivô":22.5,"Artilheiro":100.0,"Lateral móvel":0.5,"Ala produtivo":2.9,"Puxa marcação":3.7,"Armador criativo":2.4,"Jog. de infiltração":3.0,"Clássica nº 10":0.4,"Zagueiro ofensivo":0.0,"Meia versátil":0.0},"Centroavante fixo":{"Pivô":33.0,"Homem de área":100.0,"Artilheiro":4.3,"Puxa marcação":0.6},"Atacante infiltrador":{"Jog. de infiltração":100.0,"Puxa marcação":5.3,"Armador criativo":0.5,"Clássica nº 10":0.3},"Meia central armador":{"Orquestrador":100.0,"O destruidor":10.5,"Primeiro volante":12.1,"Armador criativo":22.1,"Zagueiro ofensivo":4.7,"Clássica nº 10":3.0,"Lateral atacante":0.9,"Zagueiro defensivo":0.6,"Lateral móvel":0.4,"Atacante Pivô":0.7,"Ala produtivo":0.7,"Especialista em cruz.":1.9,"Puxa marcação":0.2,"Provocador":1.3,"Artilheiro":0.4,"Homem de área":0.2,"Meia versátil":0.6},"Meia central de chegada":{"Meia versátil":100.0,"Jog. de infiltração":36.7,"O destruidor":0.2,"Orquestrador":0.4},"Meia de lado por dentro":{"Jog. de infiltração":100.0,"Artilheiro":18.8,"Armador criativo":56.3,"Zagueiro ofensivo":17.3,"Puxa marcação":1.2,"Ala produtivo":24.7,"Clássica nº 10":2.4,"Lateral atacante":3.6,"Orquestrador":4.4,"Zagueiro defensivo":3.6,"Atacante Pivô":3.9,"Homem de área":0.7,"Provocador":0.3,"Primeiro volante":0.3,"O destruidor":1.0,"Especialista em cruz.":0.5},"Meia de lado por fora":{"Lateral móvel":42.0,"Meia versátil":98.4,"Especialista em cruz.":100.0,"Jog. de infiltração":2.7},"Meia lateral atacante":{"Jog. de infiltração":100.0,"Artilheiro":18.8,"Armador criativo":56.3,"Zagueiro ofensivo":17.3,"Puxa marcação":1.2,"Ala produtivo":24.7,"Clássica nº 10":2.4,"Lateral atacante":3.6,"Orquestrador":4.4,"Zagueiro defensivo":3.6,"Atacante Pivô":3.9,"Homem de área":0.7,"Provocador":0.3,"Primeiro volante":0.3,"O destruidor":1.0,"Especialista em cruz.":0.5},"Meia lateral cruzador":{"Lateral móvel":42.0,"Meia versátil":98.4,"Especialista em cruz.":100.0,"Jog. de infiltração":2.7},"Meia ofensivo armador":{"Armador criativo":100.0,"Meia versátil":8.1,"Ala produtivo":3.3,"Orquestrador":7.7,"Atacante Pivô":5.9,"Clássica nº 10":18.2,"Artilheiro":3.9,"Lateral móvel":1.2,"Zagueiro ofensivo":0.6,"Especialista em cruz.":0.6,"Homem de área":0.5,"Lateral atacante":0.2,"Primeiro volante":0.2,"Jog. de infiltração":0.5},"Segundo atacante":{"Jog. de infiltração":100.0,"Puxa marcação":5.3,"Armador criativo":0.5,"Clássica nº 10":0.3},"Ponta criadora":{"Armador criativo":100.0,"Lateral móvel":34.9,"Especialista em cruz.":10.5,"Provocador":1.0},"Ponta finalizadora":{"Jog. de infiltração":14.6,"Artilheiro":13.8,"Ala produtivo":100.0,"Puxa marcação":0.7,"Clássica nº 10":1.1,"Zagueiro ofensivo":1.4,"Meia versátil":1.9,"Orquestrador":1.6,"Atacante Pivô":3.8,"Homem de área":0.4,"Zagueiro defensivo":0.1,"Primeiro volante":0.1,"Lateral atacante":0.1,"O destruidor":0.1,"Provocador":0.2,"Armador criativo":0.1}};
/* ===================================================================
   13/08/2026 — O ESTILO ATIVA OU O CARD E BASICO
   Fonte: a tela de filtro do PROPRIO jogo, fotografada pelo Luis, mais o
   guia da GGFoot que diz a regra por escrito:
     "Um jogador precisa ser atribuido a uma das posicoes compativeis para
      que o efeito do estilo de jogo seja ativado. Um jogador sem estilo ou
      escalado em posicao incompativel agira como BASICO."
   Basico = comportamento neutro. Nao existe molde de basico (basico e a
   AUSENCIA de estilo, nao um tipo), entao a nota NAO pune o basico:
   ela BONIFICA quem ativa. Ordem do Luis, 13/08.
   =================================================================== */
const FUNC_POS={
 'Goleiro defensivo':['GK'],'Goleiro ofensivo':['GK'],
 'Zagueiro de combate':['ZC'],'Zagueiro de saída':['ZC'],
 'Lateral defensivo':['LD','LE'],'Lateral ofensivo':['LD','LE'],
 'Volante de contenção':['VOL'],'Volante de construção':['VOL'],
 'Meia armador':['MC'],'Meia de arranque':['MC'],
 'Ala finalizador':['MLD','MLE'],'Ala cruzador':['MLD','MLE'],
 'Meia ofensivo':['MO'],'Atacante infiltrador':['MO','SA'],
 'Atacante criador':['PD','PE'],'Atacante finalizador':['PD','PE'],
 'Centroavante fixo':['CA'],'Centroavante móvel':['CA'],'Falso nove':['CA','SA'],"Meia central armador":['MC'],"Meia central de chegada":['MC'],"Meia de lado por dentro":['MLD','MLE'],"Meia de lado por fora":['MLD','MLE'],"Meia lateral atacante":['MLD','MLE'],"Meia lateral cruzador":['MLD','MLE'],"Meia ofensivo armador":['MO'],"Segundo atacante":['MO','SA'],"Ponta criadora":['PD','PE'],"Ponta finalizadora":['PD','PE']};
/* onde cada estilo LIGA. Aceita o nome novo e o que o nosso banco ainda usa. */
const EST_POS={
 'Artilheiro':['CA'],'Homem de área':['CA'],'Pivô':['CA'],
 'Atacante Pivô':['CA','SA'],'Atacante pivô':['CA','SA'],
 'Puxa marcação':['CA','SA','MO'],
 'Clássica nº 10':['SA','MO'],'Clássico nº 10':['SA','MO'],
 'Armador criativo':['SA','PD','PE','MO','MLD','MLE'],
 'Jog. de infiltração':['SA','MO','MLD','MLE','MC'],'Jogador de infiltração':['SA','MO','MLD','MLE','MC'],
 'Ala produtivo':['PD','PE'],
 'Lateral móvel':['PD','PE','MLD','MLE'],
 'Especialista em cruz.':['PD','PE','MLD','MLE'],'Perito em cruzamento':['PD','PE','MLD','MLE'],
 'Meia versátil':['MLD','MLE','MC','VOL'],
 'Orquestrador':['MC','VOL'],'Primeiro volante':['VOL'],
 'O destruidor':['MC','VOL','LD','LE','ZC'],
 'Defensor criativo':['ZC'],'Provocador':['ZC'],'Atacante surpresa':['ZC'],
 'Zagueiro ofensivo':['LD','LE'],'Lateral atacante':['LD','LE'],
 'Zagueiro defensivo':['LD','LE'],
 'Goleiro ofensivo':['GK'],'Goleiro defensivo':['GK'],'Goleiro adiantado':['GK']};
/* 14/08 · O BONUS DE ESTILO ATIVO E PONTO FIXO, NAO PERCENTUAL.
   Valor +3, ancorado pelo Luis na amplitude do molde do fisico: o fisico vai de
   -1,5 a +1,5, amplitude 3. O estilo nao tem lado negativo (quem nao ativa nao
   perde nada — a Konami que fez assim), entao ele usa a mesma amplitude 3 toda
   pra cima: 0 quando nao liga, +3 quando liga.
   POR QUE NAO PERCENTUAL: 3% de uma nota de 100 sao 3 pontos no Messi e 2,7 num
   card de 90 — premiaria mais quem ja e alto. Ativar o estilo e interruptor, nao
   escala: ou a IA obedece o estilo, ou joga como Basico. */
/* 14/08 · FECHADO PELO LUIS: +1 ponto, o mesmo que o grupo do estilo de IA inteiro.
   Medido antes de fechar: a distancia mediana entre dois vizinhos no top 30 e de
   0,07 ponto e 88% dos vizinhos estao a menos de 1,0 — entao 1 ponto ja vale ~14
   posicoes. Nas 7 funcoes completas, os cards SEM estilo no top 20 caem de 33 para
   18 com b=1; com b=2 sobram 6 e com b=3 sobra 1 (vira peneira, e o card sem estilo
   joga como Basico, que e pior, nao e zero).
   A escada continua para teste; abre no valor fechado. */
const BON_ESCALA=[1,1.5,2,0,0.5,2.5,3];
let BON_I=0, BON_ESTILO=1;
function estiloAtiva(c){
 if(!c||c.id==='MOLDE') return true;
 const ps=FUNC_POS[c.tipo], es=EST_POS[c.modelo];
 if(!ps||!es) return false;
 for(let i=0;i<ps.length;i++) if(es.indexOf(ps[i])>=0) return true;
 return false;
}
function bonEstilo(c){ return estiloAtiva(c)?BON_ESTILO:0; }
function toggleBonEstilo(){
 BON_I=(BON_I+1)%BON_ESCALA.length; BON_ESTILO=BON_ESCALA[BON_I];
 for(const c of D){ delete c._n; }
 _TOPO={};
 const b=document.getElementById('bonbt');
 if(b){ b.textContent=BON_ESTILO===0?'estilo ativo: sem bônus':('estilo ativo: +'+String(BON_ESTILO));
  const cor=BON_ESTILO===0?'#8b949e':'#22c58b'; b.style.borderColor=cor; b.style.color=cor; }
 try{ traducaoViva(); }catch(e){}
 render();
}
let PUN_ESTILO=0;  /* PONTOS — punição por jogar em função de outro estilo de jogo */
function comportamento(c){const t=ESTV[c.tipo];if(!t)return 100;const v=t[c.modelo];return v===undefined?0:v;}
function punEstilo(c){ return 0; }   /* 15/08: ABOLIDA. Sempre zero. */
const BK=[['b1n','Atributos','#4f8cff'],['b2','Habilidades','#22c58b'],['b3','Estilo IA','#9aa4b2'],['b4','Físico','#f0a531'],['b5','Player Skills','#e0533d']];
/* ===== BLOCO 3 (Estilo de jogo da IA) DESPLUGADO =====
   Para religar: troque B3ON para true. Volta o slider, a coluna da tabela,
   a linha na composição da nota, a seção na ficha e o peso 4%.
   Os dados (c.b3 de cada card e MED[tipo].b3) continuam gravados. */
const FILA={"Falso nove":[["Chute de primeira",87.7],["Efeito de longe",76.8],["Precisão à distância",62.7],["Toque duplo",57.6],["Finaliz. acrobática",51.1],["Curva para fora",49.4],["Passe em profundidade",44.7],["Espírito guerreiro",43.1],["Passe de primeira",40],["Puxada de letra",38.8],["Cabeceio",36.1],["Controle com a sola",35.4],["Especialista em pênalti",31.7],["Toque de calcanhar",24.9],["Chutes com decolagem",24.3],["Pedalada simples",24.3],["Controle da cavadinha",24.3],["Malícia",23.2],["Liderança",20.5],["Corte com virada",18],["Folha seca",17.9],["Finalizador nato",16.8],["Superioridade aérea",15.3],["Super substituto",14.1],["Cruzamento preciso",14],["Volta para marcar",12.2],["360 graus",10.9],["Elástico",10.6],["Chute com o peito do pé",8.4],["Curva descendente",6.2],["Drible astuto",5.8],["Drible explosivo",4.9],["Chapéu",4.8],["De letra",4.5],["Chute rasteiro forte",4.5],["Cabeçada matadora",4.1],["Passe na medida",2.8],["Força de vontade",2.6],["Passador nato",2.2],["Pés magnéticos",1.9],["Passe aéreo baixo",1.7],["Finta de letra",1.6],["Passe visionário",1.5],["Passe sem olhar",0.9],["Carrinho",0.7],["Arrem. lateral longo",0.2],["Interceptação",0.2],["Xerifão",0.1],["Marcação individual",0.1],["Bloqueador",0.1],["Cruzamento seco",0.1]],"Centroavante fixo":[["Chute de primeira",98.5],["Cabeceio",91.1],["Finaliz. acrobática",83.7],["Precisão à distância",74.1],["Superioridade aérea",66.7],["Espírito guerreiro",60.7],["Efeito de longe",60.7],["Chutes com decolagem",47.4],["Especialista em pênalti",38.5],["Passe de primeira",36.3],["Curva para fora",32.6],["Cabeçada matadora",28.9],["Finalizador nato",27.4],["Toque de calcanhar",25.9],["Controle da cavadinha",24.4],["Super substituto",16.3],["Puxada de letra",14.8],["Toque duplo",13.3],["Passe em profundidade",13.3],["Liderança",11.9],["Chute com o peito do pé",10.4],["Controle com a sola",10.4],["Malícia",8.9],["Folha seca",8.9],["Volta para marcar",8.1],["Elástico",7.4],["Força de vontade",7.4],["Pedalada simples",4.4],["360 graus",4.4],["Chute rasteiro forte",4.4],["Chapéu",3.7],["Cruzamento preciso",2.2],["Drible astuto",2.2],["Corte com virada",1.5],["Passe aéreo baixo",1.5],["Passe visionário",1.5],["Drible explosivo",1.5],["Curva descendente",1.5],["Passador nato",1.5],["Pés magnéticos",1.5],["Finta de letra",0.7],["Marcação individual",0.7],["Interceptação",0.7],["Bloqueador",0.7],["Carrinho",0.7]],"Centroavante móvel":[["Chute de primeira",87.7],["Efeito de longe",76.8],["Precisão à distância",62.7],["Toque duplo",57.6],["Finaliz. acrobática",51.1],["Curva para fora",49.4],["Passe em profundidade",44.7],["Espírito guerreiro",43.1],["Passe de primeira",40],["Puxada de letra",38.8],["Cabeceio",36.1],["Controle com a sola",35.4],["Especialista em pênalti",31.7],["Toque de calcanhar",24.9],["Chutes com decolagem",24.3],["Pedalada simples",24.3],["Controle da cavadinha",24.3],["Malícia",23.2],["Liderança",20.5],["Corte com virada",18],["Folha seca",17.9],["Finalizador nato",16.8],["Superioridade aérea",15.3],["Super substituto",14.1],["Cruzamento preciso",14],["Volta para marcar",12.2],["360 graus",10.9],["Elástico",10.6],["Chute com o peito do pé",8.4],["Curva descendente",6.2],["Drible astuto",5.8],["Drible explosivo",4.9],["Chapéu",4.8],["De letra",4.5],["Chute rasteiro forte",4.5],["Cabeçada matadora",4.1],["Passe na medida",2.8],["Força de vontade",2.6],["Passador nato",2.2],["Pés magnéticos",1.9],["Passe aéreo baixo",1.7],["Finta de letra",1.6],["Passe visionário",1.5],["Passe sem olhar",0.9],["Carrinho",0.7],["Arrem. lateral longo",0.2],["Interceptação",0.2],["Xerifão",0.1],["Marcação individual",0.1],["Bloqueador",0.1],["Cruzamento seco",0.1]],"Goleiro defensivo":[["Pegador de pênaltis",94.4],["Arrem. longo do GO",94.4],["Repos. baixa do GO",70.4],["Reposição alta do GO",53.7],["Liderança",46.3],["Espírito guerreiro",22.2],["Passe em profundidade",7.4],["Passe na medida",7.4],["Passe aéreo baixo",5.6],["Passe de primeira",1.9]],"Goleiro ofensivo":[["Arrem. longo do GO",92.9],["Repos. baixa do GO",88.7],["Pegador de pênaltis",83],["Reposição alta do GO",46.8],["Liderança",45.4],["Espírito guerreiro",12.1],["Passe na medida",9.2],["Passe aéreo baixo",8.5],["Passe de primeira",7.1],["Passe em profundidade",4.3],["Cabeceio",2.1],["Especialista em pênalti",2.1],["Superioridade aérea",2.1],["Carrinho",1.4],["Interceptação",1.4],["Chutes com decolagem",1.4],["Finaliz. acrobática",1.4],["Precisão à distância",1.4],["Super substituto",1.4],["Toque de calcanhar",1.4],["Chapéu",0.7],["Chute de primeira",0.7],["Controle com a sola",0.7],["Elástico",0.7],["Toque duplo",0.7]],"Lateral defensivo":[["Interceptação",94.6],["Marcação individual",92.9],["Carrinho",91.1],["Bloqueador",84.8],["Espírito guerreiro",82.1],["Afastamento acrobático",66.1],["Superioridade aérea",57.1],["Cabeceio",49.1],["Cruzamento preciso",33],["Passe na medida",25.9],["Passe de primeira",24.1],["Liderança",22.3],["Arrem. lateral longo",17],["Passe em profundidade",15.2],["Controle com a sola",15.2],["Puxada de letra",13.4],["Corte com virada",10.7],["Toque duplo",9.8],["Precisão à distância",7.1],["Chute de primeira",7.1],["Curva para fora",6.2],["Passe aéreo baixo",6.2],["Chutes com decolagem",4.5],["Especialista em pênalti",2.7],["Finaliz. acrobática",2.7],["Super substituto",2.7],["360 graus",1.8],["Malícia",1.8],["Pedalada simples",1.8],["Efeito de longe",0.9],["Toque de calcanhar",0.9]],"Lateral ofensivo":[["Interceptação",73.8],["Cruzamento preciso",71.2],["Espírito guerreiro",60.2],["Carrinho",59.4],["Passe de primeira",57.9],["Passe em profundidade",57.6],["Marcação individual",53.3],["Bloqueador",46.7],["Curva para fora",36.3],["Afastamento acrobático",33.7],["Passe na medida",28],["Precisão à distância",28],["Superioridade aérea",27.7],["Toque duplo",25.1],["Controle com a sola",21.3],["Liderança",21],["Cabeceio",19.9],["Chute de primeira",19.3],["Efeito de longe",17.6],["Puxada de letra",17],["Arrem. lateral longo",15.9],["Passe aéreo baixo",14.1],["Corte com virada",11.8],["Chutes com decolagem",11.2],["Pedalada simples",9.2],["Finaliz. acrobática",8.9],["Folha seca",8.6],["Elástico",8.4],["Especialista em pênalti",7.2],["360 graus",6.9],["Malícia",6.3],["Toque de calcanhar",5.5],["Volta para marcar",4.6],["Chute com o peito do pé",4.3],["Super substituto",2.9],["Controle da cavadinha",2.3],["Chapéu",2],["Finta de letra",1.2],["De letra",0.9]],"Meia armador":[["Passe de primeira",89],["Passe em profundidade",79.1],["Curva para fora",57.5],["Passe na medida",55.1],["Precisão à distância",54.2],["Interceptação",49.3],["Toque duplo",44.5],["Cruzamento preciso",43],["Controle com a sola",40.1],["Espírito guerreiro",39.6],["Puxada de letra",35.9],["Efeito de longe",33.5],["Passe aéreo baixo",30.8],["Liderança",27.5],["Bloqueador",26.7],["Marcação individual",26],["Carrinho",24.9],["Chute de primeira",22.2],["360 graus",19.4],["Chutes com decolagem",17.8],["Superioridade aérea",14.8],["Toque de calcanhar",14.3],["Folha seca",10.1],["Cabeceio",9.5],["Malícia",8.6],["Especialista em pênalti",7.5],["Chapéu",7],["Afastamento acrobático",7],["Volta para marcar",6.8],["Super substituto",5.9],["Chute com o peito do pé",4.8],["Finaliz. acrobática",4.8],["Passe sem olhar",4.6],["Elástico",4.6],["Controle da cavadinha",4],["Corte com virada",3.3],["Finta de letra",2.9],["Pedalada simples",2.4],["De letra",0.9]],"Meia de arranque":[["Passe de primeira",84.2],["Passe em profundidade",83.9],["Precisão à distância",62.7],["Curva para fora",61.6],["Espírito guerreiro",61],["Chute de primeira",54.8],["Toque duplo",53.4],["Efeito de longe",46.6],["Controle com a sola",46],["Interceptação",45.2],["Passe na medida",33.9],["Puxada de letra",30.2],["Cruzamento preciso",29.4],["Chutes com decolagem",25.4],["Passe aéreo baixo",23.7],["Bloqueador",21.2],["Carrinho",18.1],["Marcação individual",17.8],["Liderança",17.8],["360 graus",17.5],["Volta para marcar",14.7],["Folha seca",10.7],["Toque de calcanhar",9.6],["Finaliz. acrobática",9.3],["Elástico",8.5],["Malícia",8.2],["Cabeceio",7.9],["Especialista em pênalti",7.1],["Super substituto",5.6],["Chute com o peito do pé",4.5],["Superioridade aérea",4.2],["Pedalada simples",3.7],["Corte com virada",3.1],["Controle da cavadinha",2.3],["Passe sem olhar",2],["Afastamento acrobático",1.7],["Chapéu",1.7],["Arrem. lateral longo",1.1],["Finta de letra",0.8],["De letra",0.3]],"Ala finalizador":[["Toque duplo",71.3],["Efeito de longe",65.4],["Passe em profundidade",64],["Curva para fora",56],["Chute de primeira",54],["Controle com a sola",52.7],["Cruzamento preciso",50.7],["Passe de primeira",50.4],["Puxada de letra",49.1],["Precisão à distância",46.7],["Espírito guerreiro",33.9],["Pedalada simples",24.9],["Corte com virada",23.4],["Malícia",23.2],["Elástico",21.9],["360 graus",21.6],["Finaliz. acrobática",19.8],["Especialista em pênalti",16.3],["Liderança",15.8],["Interceptação",14.9],["Toque de calcanhar",14.5],["Folha seca",14.5],["Chutes com decolagem",13.2],["Passe na medida",12.5],["Super substituto",11.9],["Carrinho",10.5],["Controle da cavadinha",10.1],["Volta para marcar",9.8],["Marcação individual",9.2],["Cabeceio",7.9],["Bloqueador",7.5],["Passe aéreo baixo",7.2],["Afastamento acrobático",6.9],["Chapéu",6.7],["De letra",6.5],["Chute com o peito do pé",6.5],["Arrem. lateral longo",4.2],["Superioridade aérea",4.2],["Passe sem olhar",3.6],["Finta de letra",3.1]],"Ala cruzador":[["Passe em profundidade",82.3],["Efeito de longe",64.6],["Passe de primeira",64.6],["Cruzamento preciso",61.5],["Toque duplo",55.4],["Precisão à distância",50.8],["Curva para fora",50],["Chute de primeira",42.3],["Controle com a sola",41.5],["Espírito guerreiro",33.1],["Puxada de letra",32.3],["Interceptação",29.2],["Volta para marcar",25.4],["Passe na medida",23.1],["Chutes com decolagem",23.1],["Passe aéreo baixo",18.5],["Elástico",16.9],["Bloqueador",16.9],["Folha seca",16.2],["Pedalada simples",15.4],["360 graus",14.6],["Super substituto",13.8],["Finaliz. acrobática",13.8],["Malícia",13.8],["Liderança",12.3],["Toque de calcanhar",10.8],["Marcação individual",9.2],["Carrinho",9.2],["Especialista em pênalti",9.2],["Corte com virada",7.7],["Controle da cavadinha",7.7],["Chapéu",6.2],["Finta de letra",6.2],["Arrem. lateral longo",4.6],["Cabeceio",3.1],["Superioridade aérea",2.3],["Afastamento acrobático",2.3],["Chute com o peito do pé",2.3]],"Meia ofensivo":[["Passe em profundidade",81.5],["Passe de primeira",78.2],["Efeito de longe",71.3],["Toque duplo",69.1],["Curva para fora",68.2],["Precisão à distância",61.5],["Chute de primeira",55.1],["Controle com a sola",45.7],["Puxada de letra",45.5],["Cruzamento preciso",38.1],["Espírito guerreiro",28.5],["Passe na medida",26.6],["360 graus",26.3],["Liderança",21.3],["Toque de calcanhar",18.9],["Chutes com decolagem",18],["Finaliz. acrobática",16.1],["Malícia",16.1],["Folha seca",15.8],["Especialista em pênalti",14.5],["Interceptação",13.4],["Elástico",12.6],["Chapéu",12.4],["Controle da cavadinha",12.1],["Passe aéreo baixo",12.1],["Cabeceio",8.9],["Pedalada simples",8.1],["Super substituto",7.8],["Passe sem olhar",7],["Volta para marcar",6.5],["Corte com virada",5.1],["Chute com o peito do pé",4.9],["Bloqueador",4.3],["De letra",4.1],["Carrinho",4],["Superioridade aérea",2.4],["Marcação individual",2.2],["Finta de letra",2.1],["Arrem. lateral longo",1],["Afastamento acrobático",0.3]],"Meia ofensivo infiltrador":[["Passe em profundidade",84.3],["Toque duplo",76.7],["Passe de primeira",74.5],["Curva para fora",72.6],["Efeito de longe",71.1],["Chute de primeira",67.9],["Controle com a sola",61.3],["Precisão à distância",54.4],["Puxada de letra",49.7],["Cruzamento preciso",38.7],["Espírito guerreiro",37.7],["360 graus",22.6],["Toque de calcanhar",21.4],["Chutes com decolagem",17],["Finaliz. acrobática",16.4],["Malícia",15.7],["Elástico",15.4],["Volta para marcar",14.5],["Super substituto",14.2],["Liderança",12.3],["Especialista em pênalti",11.9],["Passe na medida",11.6],["Folha seca",11.3],["Cabeceio",10.4],["Passe aéreo baixo",9.1],["Pedalada simples",8.8],["Corte com virada",7.2],["Interceptação",6.9],["Controle da cavadinha",6.6],["Chapéu",5.7],["Chute com o peito do pé",3.1],["Superioridade aérea",1.9],["Passe sem olhar",1.6],["Carrinho",1.3],["Finta de letra",1.3],["Bloqueador",0.9],["De letra",0.9],["Marcação individual",0.3]],"Atacante criador":[["Efeito de longe",83.9],["Toque duplo",80.7],["Passe em profundidade",76.8],["Passe de primeira",62.6],["Puxada de letra",60.2],["Curva para fora",57.1],["Controle com a sola",56.3],["Precisão à distância",49.6],["Chute de primeira",47.2],["Cruzamento preciso",45.7],["360 graus",31.1],["Malícia",29.5],["Elástico",27.6],["Especialista em pênalti",24.8],["Folha seca",20.5],["Toque de calcanhar",18.9],["Controle da cavadinha",18.5],["Chapéu",17.3],["Espírito guerreiro",16.9],["Pedalada simples",14.6],["Liderança",12.6],["Passe na medida",12.6],["Super substituto",12.6],["Chutes com decolagem",10.2],["Corte com virada",9.4],["Passe sem olhar",9.1],["Passe aéreo baixo",8.7],["Finaliz. acrobática",8.7],["Volta para marcar",8.3],["De letra",6.3],["Finta de letra",5.5],["Cabeceio",3.1],["Chute com o peito do pé",2],["Arrem. lateral longo",1.2],["Interceptação",1.2],["Bloqueador",0.4]],"Atacante finalizador":[["Toque duplo",77.5],["Efeito de longe",73.9],["Chute de primeira",64.8],["Passe em profundidade",56.9],["Curva para fora",55.4],["Controle com a sola",54.7],["Puxada de letra",53.8],["Precisão à distância",51.1],["Passe de primeira",41.2],["Cruzamento preciso",38.3],["Espírito guerreiro",32.4],["Finaliz. acrobática",30.9],["Pedalada simples",30.2],["Malícia",26.4],["Elástico",23.8],["Corte com virada",23.8],["Toque de calcanhar",21.4],["Especialista em pênalti",20.9],["360 graus",20.1],["Folha seca",18.1],["Chutes com decolagem",16],["Super substituto",15.1],["Controle da cavadinha",15.1],["Liderança",14.7],["Volta para marcar",13.4],["Cabeceio",11.4],["Chute com o peito do pé",6.8],["Chapéu",6.5],["De letra",5.5],["Passe na medida",5.4],["Interceptação",4.9],["Superioridade aérea",3.7],["Passe sem olhar",3.3],["Finta de letra",3.1],["Passe aéreo baixo",2.2],["Carrinho",1.9],["Bloqueador",1.4],["Afastamento acrobático",1],["Marcação individual",0.8],["Arrem. lateral longo",0.5]],"Atacante infiltrador":[["Efeito de longe",79.1],["Chute de primeira",75],["Toque duplo",67.8],["Passe em profundidade",64.5],["Precisão à distância",62.5],["Curva para fora",57.7],["Passe de primeira",52.9],["Puxada de letra",47.6],["Controle com a sola",42.1],["Espírito guerreiro",33.7],["Finaliz. acrobática",33.2],["Malícia",24.7],["Cabeceio",24.2],["Toque de calcanhar",24.2],["Cruzamento preciso",22.7],["Especialista em pênalti",22.2],["Liderança",20.4],["360 graus",20.4],["Controle da cavadinha",18.6],["Pedalada simples",16.6],["Chutes com decolagem",16.3],["Elástico",15.9],["Folha seca",13.9],["Volta para marcar",12.3],["Super substituto",11.6],["Corte com virada",11.4],["Chapéu",10.9],["Passe na medida",7],["Chute com o peito do pé",5.6],["Superioridade aérea",5.5],["Passe sem olhar",5],["Passe aéreo baixo",3.8],["De letra",3.8],["Finta de letra",3.2],["Interceptação",1.7],["Carrinho",1.5],["Bloqueador",0.7],["Arrem. lateral longo",0.3],["Marcação individual",0.3]],"Volante de construção":[["Passe de primeira",88.7],["Passe em profundidade",88.3],["Interceptação",73.7],["Passe na medida",62.4],["Precisão à distância",59.5],["Curva para fora",56.9],["Espírito guerreiro",54],["Passe aéreo baixo",41.6],["Toque duplo",39.4],["Controle com a sola",38.3],["Bloqueador",33.6],["Carrinho",32.5],["Cruzamento preciso",29.2],["Chute de primeira",28.5],["Liderança",28.1],["Marcação individual",27.4],["Puxada de letra",25.5],["Efeito de longe",25.5],["Chutes com decolagem",15.7],["360 graus",10.2],["Especialista em pênalti",9.1],["Toque de calcanhar",8.8],["Volta para marcar",7.3],["Folha seca",6.9],["Superioridade aérea",5.8],["Malícia",5.8],["Cabeceio",4.4],["Chute com o peito do pé",4],["Controle da cavadinha",3.6],["Super substituto",3.3],["Chapéu",2.6],["Finaliz. acrobática",2.6],["Afastamento acrobático",2.2],["Passe sem olhar",2.2],["Finta de letra",2.2],["Pedalada simples",2.2],["Arrem. lateral longo",1.5],["Elástico",1.5],["Corte com virada",0.4]],"Volante de contenção":[["Interceptação",88.9],["Passe de primeira",81.4],["Espírito guerreiro",77.4],["Marcação individual",70.8],["Bloqueador",65.5],["Carrinho",58.8],["Passe em profundidade",54],["Superioridade aérea",46.5],["Passe na medida",45.6],["Precisão à distância",39.8],["Passe aéreo baixo",33.2],["Liderança",27.9],["Cabeceio",24.8],["Curva para fora",22.6],["Afastamento acrobático",22.1],["Chutes com decolagem",22.1],["Chute de primeira",18.1],["Cruzamento preciso",18.1],["Controle com a sola",15.5],["Puxada de letra",14.2],["Toque duplo",11.9],["Volta para marcar",11.1],["Efeito de longe",9.3],["360 graus",6.2],["Malícia",4.9],["Especialista em pênalti",4],["Chute com o peito do pé",2.7],["Toque de calcanhar",2.7],["Super substituto",2.2],["Finaliz. acrobática",2.2],["Folha seca",1.8],["Arrem. lateral longo",1.3],["Chapéu",1.3],["Finta de letra",1.3],["Pedalada simples",1.3],["Corte com virada",0.9],["Controle da cavadinha",0.4],["Elástico",0.4],["Passe sem olhar",0.4]],"Zagueiro de combate":[["Interceptação",98.8],["Marcação individual",98.8],["Carrinho",94.2],["Bloqueador",93.6],["Espírito guerreiro",92.4],["Superioridade aérea",91.8],["Afastamento acrobático",74.3],["Cabeceio",71.9],["Liderança",38.6],["Passe de primeira",28.1],["Passe na medida",24.6],["Passe aéreo baixo",20.5],["Arrem. lateral longo",11.7],["Passe em profundidade",8.8],["Chutes com decolagem",7.6],["Precisão à distância",4.7],["Cruzamento preciso",4.1],["Controle com a sola",2.9],["Chute de primeira",2.9],["360 graus",2.3],["Finaliz. acrobática",1.8],["Pedalada simples",1.2],["Puxada de letra",1.2],["Curva para fora",1.2],["Especialista em pênalti",1.2],["Toque de calcanhar",1.2],["Corte com virada",0.6],["Efeito de longe",0.6],["Folha seca",0.6],["Malícia",0.6],["Super substituto",0.6],["Toque duplo",0.6],["Volta para marcar",0.6]],"Zagueiro de saída":[["Interceptação",94.1],["Marcação individual",86.5],["Bloqueador",79.2],["Carrinho",76.5],["Superioridade aérea",72],["Espírito guerreiro",71.2],["Afastamento acrobático",58.8],["Cabeceio",56.6],["Passe na medida",49.3],["Passe de primeira",43.1],["Liderança",30.7],["Passe em profundidade",29.4],["Passe aéreo baixo",24.3],["Cruzamento preciso",17.3],["Precisão à distância",16.7],["Arrem. lateral longo",10.8],["Curva para fora",9.7],["Controle com a sola",9.4],["Chute de primeira",8.1],["Chutes com decolagem",7.8],["Toque duplo",6.7],["Puxada de letra",6.2],["Malícia",3.2],["Finaliz. acrobática",3],["Especialista em pênalti",2.4],["Toque de calcanhar",2.2],["Corte com virada",1.9],["Efeito de longe",1.9],["Super substituto",1.9],["Finta de letra",1.6],["360 graus",1.3],["Chute com o peito do pé",1.1],["Folha seca",1.1],["Chapéu",0.5],["Pedalada simples",0.5],["Volta para marcar",0.5]],"Meia central armador":[["Passe de primeira",89],["Passe em profundidade",79.1],["Curva para fora",57.5],["Passe na medida",55.1],["Precisão à distância",54.2],["Interceptação",49.3],["Toque duplo",44.5],["Cruzamento preciso",43],["Controle com a sola",40.1],["Espírito guerreiro",39.6],["Puxada de letra",35.9],["Efeito de longe",33.5],["Passe aéreo baixo",30.8],["Liderança",27.5],["Bloqueador",26.7],["Marcação individual",26],["Carrinho",24.9],["Chute de primeira",22.2],["360 graus",19.4],["Chutes com decolagem",17.8],["Superioridade aérea",14.8],["Toque de calcanhar",14.3],["Folha seca",10.1],["Cabeceio",9.5],["Malícia",8.6],["Especialista em pênalti",7.5],["Chapéu",7],["Afastamento acrobático",7],["Volta para marcar",6.8],["Super substituto",5.9],["Chute com o peito do pé",4.8],["Finaliz. acrobática",4.8],["Passe sem olhar",4.6],["Elástico",4.6],["Controle da cavadinha",4],["Corte com virada",3.3],["Finta de letra",2.9],["Pedalada simples",2.4],["De letra",0.9]],"Meia central de chegada":[["Passe de primeira",84.2],["Passe em profundidade",83.9],["Precisão à distância",62.7],["Curva para fora",61.6],["Espírito guerreiro",61],["Chute de primeira",54.8],["Toque duplo",53.4],["Efeito de longe",46.6],["Controle com a sola",46],["Interceptação",45.2],["Passe na medida",33.9],["Puxada de letra",30.2],["Cruzamento preciso",29.4],["Chutes com decolagem",25.4],["Passe aéreo baixo",23.7],["Bloqueador",21.2],["Carrinho",18.1],["Marcação individual",17.8],["Liderança",17.8],["360 graus",17.5],["Volta para marcar",14.7],["Folha seca",10.7],["Toque de calcanhar",9.6],["Finaliz. acrobática",9.3],["Elástico",8.5],["Malícia",8.2],["Cabeceio",7.9],["Especialista em pênalti",7.1],["Super substituto",5.6],["Chute com o peito do pé",4.5],["Superioridade aérea",4.2],["Pedalada simples",3.7],["Corte com virada",3.1],["Controle da cavadinha",2.3],["Passe sem olhar",2],["Afastamento acrobático",1.7],["Chapéu",1.7],["Arrem. lateral longo",1.1],["Finta de letra",0.8],["De letra",0.3]],"Meia de lado por dentro":[["Toque duplo",71.3],["Efeito de longe",65.4],["Passe em profundidade",64],["Curva para fora",56],["Chute de primeira",54],["Controle com a sola",52.7],["Cruzamento preciso",50.7],["Passe de primeira",50.4],["Puxada de letra",49.1],["Precisão à distância",46.7],["Espírito guerreiro",33.9],["Pedalada simples",24.9],["Corte com virada",23.4],["Malícia",23.2],["Elástico",21.9],["360 graus",21.6],["Finaliz. acrobática",19.8],["Especialista em pênalti",16.3],["Liderança",15.8],["Interceptação",14.9],["Toque de calcanhar",14.5],["Folha seca",14.5],["Chutes com decolagem",13.2],["Passe na medida",12.5],["Super substituto",11.9],["Carrinho",10.5],["Controle da cavadinha",10.1],["Volta para marcar",9.8],["Marcação individual",9.2],["Cabeceio",7.9],["Bloqueador",7.5],["Passe aéreo baixo",7.2],["Afastamento acrobático",6.9],["Chapéu",6.7],["De letra",6.5],["Chute com o peito do pé",6.5],["Arrem. lateral longo",4.2],["Superioridade aérea",4.2],["Passe sem olhar",3.6],["Finta de letra",3.1]],"Meia de lado por fora":[["Passe em profundidade",82.3],["Efeito de longe",64.6],["Passe de primeira",64.6],["Cruzamento preciso",61.5],["Toque duplo",55.4],["Precisão à distância",50.8],["Curva para fora",50],["Chute de primeira",42.3],["Controle com a sola",41.5],["Espírito guerreiro",33.1],["Puxada de letra",32.3],["Interceptação",29.2],["Volta para marcar",25.4],["Passe na medida",23.1],["Chutes com decolagem",23.1],["Passe aéreo baixo",18.5],["Elástico",16.9],["Bloqueador",16.9],["Folha seca",16.2],["Pedalada simples",15.4],["360 graus",14.6],["Super substituto",13.8],["Finaliz. acrobática",13.8],["Malícia",13.8],["Liderança",12.3],["Toque de calcanhar",10.8],["Marcação individual",9.2],["Carrinho",9.2],["Especialista em pênalti",9.2],["Corte com virada",7.7],["Controle da cavadinha",7.7],["Chapéu",6.2],["Finta de letra",6.2],["Arrem. lateral longo",4.6],["Cabeceio",3.1],["Superioridade aérea",2.3],["Afastamento acrobático",2.3],["Chute com o peito do pé",2.3]],"Meia lateral atacante":[["Toque duplo",71.3],["Efeito de longe",65.4],["Passe em profundidade",64],["Curva para fora",56],["Chute de primeira",54],["Controle com a sola",52.7],["Cruzamento preciso",50.7],["Passe de primeira",50.4],["Puxada de letra",49.1],["Precisão à distância",46.7],["Espírito guerreiro",33.9],["Pedalada simples",24.9],["Corte com virada",23.4],["Malícia",23.2],["Elástico",21.9],["360 graus",21.6],["Finaliz. acrobática",19.8],["Especialista em pênalti",16.3],["Liderança",15.8],["Interceptação",14.9],["Toque de calcanhar",14.5],["Folha seca",14.5],["Chutes com decolagem",13.2],["Passe na medida",12.5],["Super substituto",11.9],["Carrinho",10.5],["Controle da cavadinha",10.1],["Volta para marcar",9.8],["Marcação individual",9.2],["Cabeceio",7.9],["Bloqueador",7.5],["Passe aéreo baixo",7.2],["Afastamento acrobático",6.9],["Chapéu",6.7],["De letra",6.5],["Chute com o peito do pé",6.5],["Arrem. lateral longo",4.2],["Superioridade aérea",4.2],["Passe sem olhar",3.6],["Finta de letra",3.1]],"Meia lateral cruzador":[["Passe em profundidade",82.3],["Efeito de longe",64.6],["Passe de primeira",64.6],["Cruzamento preciso",61.5],["Toque duplo",55.4],["Precisão à distância",50.8],["Curva para fora",50],["Chute de primeira",42.3],["Controle com a sola",41.5],["Espírito guerreiro",33.1],["Puxada de letra",32.3],["Interceptação",29.2],["Volta para marcar",25.4],["Passe na medida",23.1],["Chutes com decolagem",23.1],["Passe aéreo baixo",18.5],["Elástico",16.9],["Bloqueador",16.9],["Folha seca",16.2],["Pedalada simples",15.4],["360 graus",14.6],["Super substituto",13.8],["Finaliz. acrobática",13.8],["Malícia",13.8],["Liderança",12.3],["Toque de calcanhar",10.8],["Marcação individual",9.2],["Carrinho",9.2],["Especialista em pênalti",9.2],["Corte com virada",7.7],["Controle da cavadinha",7.7],["Chapéu",6.2],["Finta de letra",6.2],["Arrem. lateral longo",4.6],["Cabeceio",3.1],["Superioridade aérea",2.3],["Afastamento acrobático",2.3],["Chute com o peito do pé",2.3]],"Meia ofensivo armador":[["Passe em profundidade",81.5],["Passe de primeira",78.2],["Efeito de longe",71.3],["Toque duplo",69.1],["Curva para fora",68.2],["Precisão à distância",61.5],["Chute de primeira",55.1],["Controle com a sola",45.7],["Puxada de letra",45.5],["Cruzamento preciso",38.1],["Espírito guerreiro",28.5],["Passe na medida",26.6],["360 graus",26.3],["Liderança",21.3],["Toque de calcanhar",18.9],["Chutes com decolagem",18],["Finaliz. acrobática",16.1],["Malícia",16.1],["Folha seca",15.8],["Especialista em pênalti",14.5],["Interceptação",13.4],["Elástico",12.6],["Chapéu",12.4],["Controle da cavadinha",12.1],["Passe aéreo baixo",12.1],["Cabeceio",8.9],["Pedalada simples",8.1],["Super substituto",7.8],["Passe sem olhar",7],["Volta para marcar",6.5],["Corte com virada",5.1],["Chute com o peito do pé",4.9],["Bloqueador",4.3],["De letra",4.1],["Carrinho",4],["Superioridade aérea",2.4],["Marcação individual",2.2],["Finta de letra",2.1],["Arrem. lateral longo",1],["Afastamento acrobático",0.3]],"Segundo atacante":[["Efeito de longe",79.1],["Chute de primeira",75],["Toque duplo",67.8],["Passe em profundidade",64.5],["Precisão à distância",62.5],["Curva para fora",57.7],["Passe de primeira",52.9],["Puxada de letra",47.6],["Controle com a sola",42.1],["Espírito guerreiro",33.7],["Finaliz. acrobática",33.2],["Malícia",24.7],["Cabeceio",24.2],["Toque de calcanhar",24.2],["Cruzamento preciso",22.7],["Especialista em pênalti",22.2],["Liderança",20.4],["360 graus",20.4],["Controle da cavadinha",18.6],["Pedalada simples",16.6],["Chutes com decolagem",16.3],["Elástico",15.9],["Folha seca",13.9],["Volta para marcar",12.3],["Super substituto",11.6],["Corte com virada",11.4],["Chapéu",10.9],["Passe na medida",7],["Chute com o peito do pé",5.6],["Superioridade aérea",5.5],["Passe sem olhar",5],["Passe aéreo baixo",3.8],["De letra",3.8],["Finta de letra",3.2],["Interceptação",1.7],["Carrinho",1.5],["Bloqueador",0.7],["Arrem. lateral longo",0.3],["Marcação individual",0.3]],"Ponta criadora":[["Efeito de longe",83.9],["Toque duplo",80.7],["Passe em profundidade",76.8],["Passe de primeira",62.6],["Puxada de letra",60.2],["Curva para fora",57.1],["Controle com a sola",56.3],["Precisão à distância",49.6],["Chute de primeira",47.2],["Cruzamento preciso",45.7],["360 graus",31.1],["Malícia",29.5],["Elástico",27.6],["Especialista em pênalti",24.8],["Folha seca",20.5],["Toque de calcanhar",18.9],["Controle da cavadinha",18.5],["Chapéu",17.3],["Espírito guerreiro",16.9],["Pedalada simples",14.6],["Liderança",12.6],["Passe na medida",12.6],["Super substituto",12.6],["Chutes com decolagem",10.2],["Corte com virada",9.4],["Passe sem olhar",9.1],["Passe aéreo baixo",8.7],["Finaliz. acrobática",8.7],["Volta para marcar",8.3],["De letra",6.3],["Finta de letra",5.5],["Cabeceio",3.1],["Chute com o peito do pé",2],["Arrem. lateral longo",1.2],["Interceptação",1.2],["Bloqueador",0.4]],"Ponta finalizadora":[["Toque duplo",77.5],["Efeito de longe",73.9],["Chute de primeira",64.8],["Passe em profundidade",56.9],["Curva para fora",55.4],["Controle com a sola",54.7],["Puxada de letra",53.8],["Precisão à distância",51.1],["Passe de primeira",41.2],["Cruzamento preciso",38.3],["Espírito guerreiro",32.4],["Finaliz. acrobática",30.9],["Pedalada simples",30.2],["Malícia",26.4],["Elástico",23.8],["Corte com virada",23.8],["Toque de calcanhar",21.4],["Especialista em pênalti",20.9],["360 graus",20.1],["Folha seca",18.1],["Chutes com decolagem",16],["Super substituto",15.1],["Controle da cavadinha",15.1],["Liderança",14.7],["Volta para marcar",13.4],["Cabeceio",11.4],["Chute com o peito do pé",6.8],["Chapéu",6.5],["De letra",5.5],["Passe na medida",5.4],["Interceptação",4.9],["Superioridade aérea",3.7],["Passe sem olhar",3.3],["Finta de letra",3.1],["Passe aéreo baixo",2.2],["Carrinho",1.9],["Bloqueador",1.4],["Afastamento acrobático",1],["Marcação individual",0.8],["Arrem. lateral longo",0.5]]};
const B5V={"Falso nove":{"Cabeçada matadora":16.3,"Chute rasteiro forte":18.6,"Cruzamento seco":0,"Curva descendente":21.3,"Drible astuto":13.7,"Drible explosivo":16.6,"Finalizador nato":60.1,"Força de vontade":10.5,"Passador nato":7.2,"Passe visionário":4.8,"Pés magnéticos":6,"Xerifão":0},"Goleiro ofensivo":{"Defesa direta (GO)":58.4,"Grito de garra (GO)":19.9,"Passe visionário":21.8},"Goleiro defensivo":{"Defesa direta (GO)":61.2,"Grito de garra (GO)":16.2,"Passe visionário":22.5},"Zagueiro de saída":{"Chute rasteiro forte":0.2,"Cruzamento seco":1,"Curva descendente":0.2,"Desarme de longo alcance":34.7,"Domínio aéreo":32.4,"Drible explosivo":0.2,"Passador nato":3.6,"Passe visionário":18.2,"Xerifão":32.9},"Zagueiro de combate":{"Cabeçada matadora":0.4,"Chute rasteiro forte":2.2,"Desarme de longo alcance":34,"Domínio aéreo":40.3,"Passe inspirador":0.4,"Passe visionário":2.6,"Xerifão":25.7},"Lateral ofensivo":{"Chute rasteiro forte":5.7,"Cruzamento seco":64.4,"Curva descendente":2.6,"Desarme de longo alcance":16.9,"Domínio aéreo":1.4,"Drible astuto":7.4,"Drible explosivo":12.5,"Passador nato":15.9,"Passe inspirador":0.2,"Passe visionário":3,"Pés magnéticos":0.2,"Xerifão":18.7},"Lateral defensivo":{"Cruzamento seco":5.5,"Desarme de longo alcance":28.8,"Domínio aéreo":5.5,"Passe visionário":6.8,"Xerifão":64.4},"Volante de construção":{"Chute rasteiro forte":2,"Curva descendente":0.3,"Desarme de longo alcance":14.3,"Passador nato":37,"Passe inspirador":4.2,"Passe visionário":37.7,"Pés magnéticos":3.3,"Xerifão":25.2},"Volante de contenção":{"Cabeçada matadora":3,"Chute rasteiro forte":4.4,"Cruzamento seco":3.2,"Desarme de longo alcance":52.7,"Domínio aéreo":0.4,"Passador nato":18.6,"Passe inspirador":0.7,"Passe visionário":17.5,"Pés magnéticos":3,"Xerifão":28.7},"Meia de arranque":{"Cabeçada matadora":0.2,"Chute rasteiro forte":27.1,"Cruzamento seco":0.5,"Curva descendente":6.9,"Desarme de longo alcance":14.5,"Drible astuto":4.4,"Finalizador nato":4.2,"Passador nato":48.3,"Passe inspirador":0.5,"Passe visionário":24.6,"Pés magnéticos":3.7,"Xerifão":11.6},"Meia armador":{"Cabeçada matadora":0.3,"Chute rasteiro forte":7.2,"Cruzamento seco":2.9,"Curva descendente":1.2,"Desarme de longo alcance":13,"Drible astuto":0.3,"Drible explosivo":0.6,"Finalizador nato":1.4,"Passador nato":45.8,"Passe inspirador":7.2,"Passe visionário":41.2,"Pés magnéticos":11.5,"Xerifão":9.8},"Meia ofensivo":{"Cabeçada matadora":0.2,"Chute rasteiro forte":7.5,"Cruzamento seco":4.1,"Curva descendente":31.2,"Desarme de longo alcance":0.5,"Drible astuto":32,"Drible explosivo":10.2,"Finalizador nato":14,"Força de vontade":0.2,"Passador nato":36.7,"Passe inspirador":3.3,"Passe visionário":26.4,"Pés magnéticos":4.2,"Xerifão":0.4},"Meia ofensivo infiltrador":{"Cabeçada matadora":5.5,"Chute rasteiro forte":25.1,"Cruzamento seco":2.8,"Curva descendente":7.4,"Drible astuto":33.9,"Drible explosivo":9.5,"Finalizador nato":10,"Passador nato":41,"Passe visionário":6.7,"Pés magnéticos":14.3,"Xerifão":2.8},"Ala finalizador":{"Cabeçada matadora":0.2,"Chute rasteiro forte":8.9,"Cruzamento seco":4,"Curva descendente":7,"Desarme de longo alcance":1.1,"Domínio aéreo":0.2,"Drible astuto":55.6,"Drible explosivo":28,"Finalizador nato":16.4,"Força de vontade":0.3,"Passador nato":10.4,"Passe inspirador":0.2,"Passe visionário":5.3,"Pés magnéticos":4.6,"Xerifão":1.2},"Ala cruzador":{"Chute rasteiro forte":13.9,"Cruzamento seco":54.2,"Curva descendente":4.6,"Desarme de longo alcance":3.7,"Drible astuto":22.2,"Drible explosivo":12,"Passador nato":23.6,"Passe inspirador":2.8,"Passe visionário":9.7,"Pés magnéticos":11.1,"Xerifão":6.9},"Atacante criador":{"Chute rasteiro forte":1.2,"Cruzamento seco":31.5,"Curva descendente":46.5,"Drible astuto":22,"Drible explosivo":11.3,"Finalizador nato":0.6,"Passador nato":9.5,"Passe inspirador":7.1,"Passe visionário":8.9,"Pés magnéticos":6.6},"Atacante finalizador":{"Cabeçada matadora":0.5,"Chute rasteiro forte":6.2,"Cruzamento seco":3.2,"Curva descendente":40.6,"Desarme de longo alcance":0.1,"Drible astuto":28.4,"Drible explosivo":31,"Finalizador nato":5.1,"Força de vontade":2.9,"Passador nato":6.5,"Passe inspirador":0.1,"Passe visionário":8.1,"Pés magnéticos":12.9,"Xerifão":0.2},"Atacante infiltrador":{"Cabeçada matadora":2,"Chute rasteiro forte":4.2,"Cruzamento seco":6.9,"Curva descendente":23.7,"Drible astuto":39.2,"Drible explosivo":6.6,"Finalizador nato":37.2,"Força de vontade":1.5,"Passador nato":11.9,"Passe visionário":12.2,"Pés magnéticos":13.5,"Xerifão":0.2},"Centroavante fixo":{"Cabeçada matadora":42.4,"Chute rasteiro forte":6.3,"Curva descendente":2.6,"Drible astuto":3.1,"Drible explosivo":2.6,"Finalizador nato":44.5,"Força de vontade":13.1,"Passador nato":2.6,"Passe visionário":2.6,"Pés magnéticos":2.6},"Centroavante móvel":{"Cabeçada matadora":16.3,"Chute rasteiro forte":18.6,"Cruzamento seco":0,"Curva descendente":21.3,"Drible astuto":13.7,"Drible explosivo":16.6,"Finalizador nato":60.1,"Força de vontade":10.5,"Passador nato":7.2,"Passe visionário":4.8,"Pés magnéticos":6,"Xerifão":0},"Meia central armador":{"Cabeçada matadora":0.3,"Chute rasteiro forte":7.2,"Cruzamento seco":2.9,"Curva descendente":1.2,"Desarme de longo alcance":13,"Drible astuto":0.3,"Drible explosivo":0.6,"Finalizador nato":1.4,"Passador nato":45.8,"Passe inspirador":7.2,"Passe visionário":41.2,"Pés magnéticos":11.5,"Xerifão":9.8},"Meia central de chegada":{"Cabeçada matadora":0.2,"Chute rasteiro forte":27.1,"Cruzamento seco":0.5,"Curva descendente":6.9,"Desarme de longo alcance":14.5,"Drible astuto":4.4,"Finalizador nato":4.2,"Passador nato":48.3,"Passe inspirador":0.5,"Passe visionário":24.6,"Pés magnéticos":3.7,"Xerifão":11.6},"Meia de lado por dentro":{"Cabeçada matadora":0.2,"Chute rasteiro forte":8.9,"Cruzamento seco":4,"Curva descendente":7,"Desarme de longo alcance":1.1,"Domínio aéreo":0.2,"Drible astuto":55.6,"Drible explosivo":28,"Finalizador nato":16.4,"Força de vontade":0.3,"Passador nato":10.4,"Passe inspirador":0.2,"Passe visionário":5.3,"Pés magnéticos":4.6,"Xerifão":1.2},"Meia de lado por fora":{"Chute rasteiro forte":13.9,"Cruzamento seco":54.2,"Curva descendente":4.6,"Desarme de longo alcance":3.7,"Drible astuto":22.2,"Drible explosivo":12,"Passador nato":23.6,"Passe inspirador":2.8,"Passe visionário":9.7,"Pés magnéticos":11.1,"Xerifão":6.9},"Meia lateral atacante":{"Cabeçada matadora":0.2,"Chute rasteiro forte":8.9,"Cruzamento seco":4,"Curva descendente":7,"Desarme de longo alcance":1.1,"Domínio aéreo":0.2,"Drible astuto":55.6,"Drible explosivo":28,"Finalizador nato":16.4,"Força de vontade":0.3,"Passador nato":10.4,"Passe inspirador":0.2,"Passe visionário":5.3,"Pés magnéticos":4.6,"Xerifão":1.2},"Meia lateral cruzador":{"Chute rasteiro forte":13.9,"Cruzamento seco":54.2,"Curva descendente":4.6,"Desarme de longo alcance":3.7,"Drible astuto":22.2,"Drible explosivo":12,"Passador nato":23.6,"Passe inspirador":2.8,"Passe visionário":9.7,"Pés magnéticos":11.1,"Xerifão":6.9},"Meia ofensivo armador":{"Cabeçada matadora":0.2,"Chute rasteiro forte":7.5,"Cruzamento seco":4.1,"Curva descendente":31.2,"Desarme de longo alcance":0.5,"Drible astuto":32,"Drible explosivo":10.2,"Finalizador nato":14,"Força de vontade":0.2,"Passador nato":36.7,"Passe inspirador":3.3,"Passe visionário":26.4,"Pés magnéticos":4.2,"Xerifão":0.4},"Segundo atacante":{"Cabeçada matadora":2,"Chute rasteiro forte":4.2,"Cruzamento seco":6.9,"Curva descendente":23.7,"Drible astuto":39.2,"Drible explosivo":6.6,"Finalizador nato":37.2,"Força de vontade":1.5,"Passador nato":11.9,"Passe visionário":12.2,"Pés magnéticos":13.5,"Xerifão":0.2},"Ponta criadora":{"Chute rasteiro forte":1.2,"Cruzamento seco":31.5,"Curva descendente":46.5,"Drible astuto":22,"Drible explosivo":11.3,"Finalizador nato":0.6,"Passador nato":9.5,"Passe inspirador":7.1,"Passe visionário":8.9,"Pés magnéticos":6.6},"Ponta finalizadora":{"Cabeçada matadora":0.5,"Chute rasteiro forte":6.2,"Cruzamento seco":3.2,"Curva descendente":40.6,"Desarme de longo alcance":0.1,"Drible astuto":28.4,"Drible explosivo":31,"Finalizador nato":5.1,"Força de vontade":2.9,"Passador nato":6.5,"Passe inspirador":0.1,"Passe visionário":8.1,"Pés magnéticos":12.9,"Xerifão":0.2}};
const B3ON=false;

/* ================= BLOCO 4 — ESPELHO FÍSICO =================
   CALIBRAGEM: mexa só nesta linha. Nada mais precisa ser tocado.
   FIS_K   multiplicador do peso da altura (proporção da Konami). 1=original, 2=dobrado
   FIS_HI  espelho a partir do qual o card ganha a faixa cheia (+2)
   FIS_MID espelho a partir do qual ganha meia faixa (+1)
   FIS_LO  espelho até o qual leva punição (-1)
   FIS_PT  quantos pontos da nota final vale cada faixa
   ============================================================ */
const FIS_K=2, FIS_HI=90, FIS_MID=70, FIS_LO=20, FIS_PT=2;
const FIS_KON={"Falso nove":5.89,"Goleiro ofensivo":11.08,"Goleiro defensivo":11.08,"Zagueiro de saída":8.09,"Zagueiro de combate":8.09,"Lateral ofensivo":2.92,"Lateral defensivo":2.92,"Volante de construção":3.64,"Volante de contenção":3.64,"Meia de arranque":2.21,"Meia armador":2.21,"Meia ofensivo":2.21,"Ala finalizador":0.72,"Ala cruzador":0.72,"Atacante criador":2.92,"Atacante finalizador":2.92,"Centroavante fixo":5.89,"Centroavante móvel":5.89,"Atacante infiltrador":2.21,"Meia central armador":2.21,"Meia central de chegada":2.21,"Meia de lado por dentro":0.72,"Meia de lado por fora":0.72,"Meia lateral atacante":0.72,"Meia lateral cruzador":0.72,"Meia ofensivo armador":2.21,"Segundo atacante":2.21,"Ponta criadora":2.92,"Ponta finalizadora":2.92};
const FIS_M={"116751":[8,12,7,4,9,6,6,7,5,6,6,175.1,167.2,261.8,52,181],"135067":[6,7,5,6,7,9,7,7,7,7,7,166,155.2,257.2,47.9,172],"105590697335088":[7,10,7,4,7,7,8,5,5,6,6,180,169.4,262.5,52.5,187],"105828799607548":[5,7,7,5,7,9,4,7,4,4,6,177.8,166.8,261.8,51.7,183],"105835241963937":[9,10,8,5,6,5,11,5,5,8,6,188.6,178,263.8,54.5,197],"105852237307683":[6,10,4,9,10,4,9,10,8,9,9,169.9,158.4,255.3,49.9,177],"106726447777829":[5,8,5,3,12,6,8,2,4,2,8,168.4,156.2,257.9,48.3,175],"106732084830367":[4,10,7,11,12,5,12,12,4,9,10,179.3,163.6,257.5,52.2,188],"106735037701276":[8,7,8,6,5,9,11,7,4,6,5,184.7,172.7,267.7,52.5,193],"106738258909413":[11,10,5,2,7,9,14,6,3,6,4,187.3,177.4,260,53.5,197],"106743896078681":[11,10,5,10,8,7,12,4,4,5,4,180.3,171.8,265.2,52.1,189],"106772350211068":[7,6,9,5,10,5,7,7,4,7,8,175.6,165.1,264.3,50.3,182],"106785503587053":[10,11,7,6,9,6,11,7,4,4,7,190.5,181.2,262.9,55.5,199],"106787651035597":[6,8,7,4,9,7,8,7,6,5,7,183.9,171.6,259.2,53.1,191],"106787651045215":[7,10,10,5,7,3,7,9,9,7,10,167.9,158.5,255.2,49.4,174],"106787651045391":[8,12,7,4,9,6,6,7,5,6,6,175.1,167.2,263.1,52,181],"52868094734462":[12,5,4,6,7,11,14,5,9,5,3,175.5,166.4,264.3,49,185],"52869705269665":[9,10,8,5,6,5,11,5,5,8,6,188.6,178,265.8,54.5,197],"52886616816720":[6,8,5,6,7,6,13,7,6,8,7,170.1,156.3,260.2,48.4,179],"52887690564960":[7,8,6,6,9,6,11,7,5,8,6,176.8,164.5,268.4,50.6,185],"52891717047292":[7,6,9,5,10,5,7,7,4,7,8,175.6,165.1,267.6,50.3,182],"52892790823620":[6,7,6,6,6,8,8,7,9,7,9,171.3,159.7,265.1,49.4,178],"52893059240129":[8,6,6,4,4,9,11,7,3,5,5,170,158.8,260.8,48,178],"52896548935008":[7,8,6,6,9,6,11,7,5,8,6,176.8,164.5,269.1,50.6,185],"52898696326240":[6,9,5,5,9,9,7,8,5,8,8,174.7,163.7,265.5,50.9,181],"56162334672709":[11,11,7,7,7,7,14,8,5,5,8,183.4,173.9,273,53,193],"56165555880124":[10,8,7,5,4,7,14,4,0,4,4,180.4,169.5,262.1,50.8,190],"56166629640005":[11,11,7,7,7,7,14,8,5,5,8,183.4,173.9,271.7,53,193],"56168240220884":[6,8,8,5,8,8,7,7,5,6,8,188.2,176.1,263.2,54.5,195],"87962272537319":[9,14,5,7,11,3,10,7,7,7,7,188,178.8,252.4,56,196],"87963346142036":[4,9,6,7,7,9,9,7,7,6,8,179.6,165.2,252.6,52.2,187],"88029649699741":[7,11,7,9,8,0,9,14,8,10,12,171.9,161.4,259.4,50.9,179],"88030723575245":[4,5,5,7,9,1,7,9,7,8,9,169.8,156.4,257.2,48.6,176],"88030723578594":[10,14,5,10,12,0,13,12,1,10,9,171,162.2,251.9,50.5,180],"88032334191333":[7,7,4,4,9,5,7,10,7,7,9,169.8,159.8,247.7,49.1,176],"88033139494363":[7,10,6,10,10,6,2,10,8,7,10,161.5,154.9,248.9,48.5,165],"88033407929799":[6,11,4,7,8,3,12,10,7,8,8,184.2,170.4,251.8,53.8,193],"88036360591553":[6,8,6,7,10,8,8,9,4,4,9,164.6,153.6,249.5,47.6,171],"88039581811496":[9,12,7,7,9,4,11,7,7,7,7,188.6,178.4,253.6,55.4,197],"88039581945292":[5,9,3,8,14,8,12,13,9,10,11,164.6,151,245.5,47.7,173],"88040387117922":[5,9,4,5,10,5,7,3,5,6,5,164.1,152.8,255,47.6,170],"88040387255015":[10,11,7,9,12,6,11,8,9,9,8,188.6,179.3,253.6,55.3,197],"88041460993512":[7,7,7,8,9,7,11,8,7,8,8,185.6,172.5,267.8,53.1,194],"88044145214260":[8,7,7,7,10,7,11,7,7,7,7,187.6,175.4,265.8,53.5,196],"88044145253792":[5,9,5,8,9,5,9,9,4,6,9,169.9,157.2,259.5,49.4,177],"88044145348029":[14,8,6,5,5,10,14,7,2,7,7,189.3,182.2,270.8,53.5,199],"88044145351392":[6,6,7,6,8,6,12,7,6,6,7,178.4,164,262.4,50.4,187],"88044950524330":[1,9,7,6,8,2,9,7,4,5,6,181.6,163.8,266.1,52.6,189],"89129966765504":[7,8,6,6,6,7,11,7,6,8,6,183.7,170.9,265.5,52.6,192],"89136409091415":[5,9,6,9,9,2,3,9,7,8,10,162,152.8,256.1,48.1,166],"89138019757152":[6,9,5,5,9,9,7,8,5,8,8,172.7,161.9,258.2,50.4,179],"89138288133079":[7,11,5,7,9,5,8,9,7,10,8,185.9,175.1,252.1,54.9,193],"89138288136169":[5,5,4,2,10,10,9,4,4,4,3,166,153,253.3,46.7,173],"89138288138433":[6,8,6,7,10,8,8,9,4,4,9,164.6,153.6,249.5,47.6,171],"89138288270047":[7,9,7,7,9,7,13,7,2,2,2,181.9,168.4,258.8,52,191],"89138556572074":[1,9,7,6,8,2,9,7,4,5,6,181.6,163.8,265.4,52.6,189],"89138556575063":[5,9,6,9,9,2,3,9,7,10,10,162,152.8,256.1,48.1,166],"89138556678367":[8,8,5,4,7,3,8,8,7,6,8,183.9,173.8,269.2,53.2,191]};
const FIS_P={"Falso nove":[[0,180,1,null],[10,6,1,20],[11,6,0,14.29],[3,9,1,12.5],[16,50.6,1,0.6],[17,184,1,0.55],[15,261.15,0,0.44],[14,163.8,1,0.24]],"Goleiro ofensivo":[[0,193,1,null],[3,10,1,11.11],[8,10,1,11.11],[1,88,1,3.53],[16,54.5,1,1.96],[14,177.1,1,1.9],[17,197,1,1.55],[13,188.6,1,1.4],[15,259.2,1,0.27]],"Goleiro defensivo":[[0,194,1,null],[5,7,1,40],[4,6.5,1,18.18],[6,8,1,14.29],[10,6,1,9.09],[7,6,0,7.69],[3,11,1,4.76],[1,92.5,1,2.78],[14,177.75,1,0.71],[15,255.3,0,0.43],[16,55,1,0.18]],"Zagueiro de saída":[[0,191,1,null],[5,5,0,16.67],[4,6.5,1,8.33],[1,85,1,7.59],[8,9.5,1,5.56],[13,186.2,1,3.67],[17,193,1,3.21],[16,53.5,1,3.08],[14,172.3,1,2.68],[15,264.15,1,0.71]],"Zagueiro de combate":[[0,186,1,null],[10,7,1,16.67],[2,6,0,14.29],[9,8,1,14.29],[11,6,0,14.29],[3,7,0,12.5],[6,7,0,12.5],[8,8,0,11.11],[14,168.4,0,1.06],[16,52.2,0,0.76],[13,180.7,0,0.47],[15,258.1,0,0.15]],"Lateral ofensivo":[[0,178,1,null],[4,5,0,16.67],[5,7,1,16.67],[9,8,1,14.29],[12,8,1,14.29],[6,9,1,12.5],[16,49.8,0,1.58],[17,181,0,1.09],[15,257.2,0,1.04],[14,162.6,0,0.91],[13,173.8,0,0.6]],"Lateral defensivo":[[0,183,1,null],[10,6,1,20],[4,7,1,16.67],[6,8,1,14.29],[7,6,0,14.29],[3,7.5,0,6.25],[8,10.5,1,5],[1,75,0,1.32],[16,50.849999999999994,0,0.88],[14,165.14999999999998,0,0.3],[13,178.4,0,0.28],[15,260.54999999999995,1,0.06]],"Volante de contenção":[[0,187,1,null],[8,11,1,22.22],[4,5,0,16.67],[7,7.5,1,7.14],[1,81,1,6.58],[17,191,1,4.37],[13,182.7,1,3.45],[14,170,1,2.66],[16,52.4,1,2.54],[15,264.65,1,0.97]],"Volante de construção":[[0,179.5,1,null],[4,7,1,16.67],[5,5,0,16.67],[7,6,0,14.29],[9,8,1,14.29],[12,8,1,14.29],[6,7,0,12.5],[1,75,1,1.35],[16,50.35,1,1.1],[14,161.2,0,0.25],[15,261.20000000000005,0,0.15],[13,173.5,0,0.12]],"Meia armador":[[0,174,1,null],[11,5,0,28.57],[4,5,0,16.67],[5,5,0,16.67],[2,6,0,14.29],[7,6,0,14.29],[12,8,1,14.29],[6,9,1,12.5],[1,69,0,5.48],[16,48.3,0,3.98],[14,156.2,0,3.94],[17,175,0,3.31],[13,168.4,0,3.16],[15,259.2,0,1.18]],"Meia de arranque":[[0,182,1,null],[2,5,0,16.67],[4,7,1,16.67],[6,8,1,14.29],[9,8,1,14.29],[1,75,1,2.74],[17,183,1,1.1],[16,50.9,1,0.99],[13,176.2,1,0.86],[15,262.4,1,0.11],[14,163,1,0.06]],"Meia ofensivo":[[0,179,1,null],[10,6,1,20],[6,7.5,0,6.25],[16,50.3,1,1.41],[1,73,1,1.39],[14,161.9,1,1.06],[13,172.75,1,0.64],[17,180,1,0.56],[15,260.95,0,0.1]],"Ala finalizador":[[0,179,1,null],[5,5,0,16.67],[12,6,0,14.29],[3,7.5,0,6.25],[1,70,0,2.78],[15,262.2,1,0.42],[16,49.45,0,0.3],[17,180.5,0,0.28],[14,162.25,0,0.09],[13,173.75,0,0.09]],"Ala cruzador":[[0,178,1,null],[8,7,0,12.5],[17,178,0,0.56],[14,162.1,1,0.43],[13,171.8,0,0.29],[15,261.2,1,0.11]],"Atacante finalizador":[[0,178,1,null],[12,6,0,14.29],[1,72,0,1.37],[17,183,1,1.1],[13,175,1,0.63],[16,49.5,0,0.6],[15,262.6,1,0.38],[14,163,1,0.12]],"Atacante criador":[[0,175,1,null],[9,8.5,1,21.43],[10,6,1,20],[5,7,1,16.67],[11,7,1,16.67],[7,6,0,14.29],[12,8,1,14.29],[3,9,1,12.5],[2,6.5,1,8.33],[6,8.5,1,6.25],[1,72,1,1.41],[16,48.9,0,1.01],[15,259,0,0.94],[13,169.9,0,0.73],[17,177,0,0.56],[14,159.65,0,0.34]],"Centroavante móvel":[[0,180,1,null],[10,6,1,20],[11,6,0,14.29],[3,9,1,12.5],[16,50.6,1,0.6],[17,184,1,0.55],[15,261.15,0,0.44],[14,163.8,1,0.24]],"Centroavante fixo":[[0,189,1,null],[7,5.5,1,10],[5,6.5,1,8.33],[15,271.25,1,0.61],[16,53.25,1,0.47],[14,172.7,0,0.29],[13,184.1,0,0.11]],"Atacante infiltrador":[[0,180,1,null],[2,7,1,16.67],[4,7,1,16.67],[9,8,1,14.29],[8,8,0,11.11],[1,74,1,2.78],[16,50.5,1,1.41],[13,174.9,1,1.27],[14,163.7,1,0.92],[17,181,1,0.56],[15,263.1,1,0.27]],"Meia central armador":[[0,174,1,null],[11,5,0,28.57],[4,5,0,16.67],[5,5,0,16.67],[2,6,0,14.29],[7,6,0,14.29],[12,8,1,14.29],[6,9,1,12.5],[1,69,0,5.48],[16,48.3,0,3.98],[14,156.2,0,3.94],[17,175,0,3.31],[13,168.4,0,3.16],[15,259.2,0,1.18]],"Meia central de chegada":[[0,182,1,null],[2,5,0,16.67],[4,7,1,16.67],[6,8,1,14.29],[9,8,1,14.29],[1,75,1,2.74],[17,183,1,1.1],[16,50.9,1,0.99],[13,176.2,1,0.86],[15,262.4,1,0.11],[14,163,1,0.06]],"Meia de lado por dentro":[[0,179,1,null],[5,5,0,16.67],[12,6,0,14.29],[3,7.5,0,6.25],[1,70,0,2.78],[15,262.2,1,0.42],[16,49.45,0,0.3],[17,180.5,0,0.28],[14,162.25,0,0.09],[13,173.75,0,0.09]],"Meia de lado por fora":[[0,178,1,null],[8,7,0,12.5],[17,178,0,0.56],[14,162.1,1,0.43],[13,171.8,0,0.29],[15,261.2,1,0.11]],"Meia lateral atacante":[[0,179,1,null],[5,5,0,16.67],[12,6,0,14.29],[3,7.5,0,6.25],[1,70,0,2.78],[15,262.2,1,0.42],[16,49.45,0,0.3],[17,180.5,0,0.28],[14,162.25,0,0.09],[13,173.75,0,0.09]],"Meia lateral cruzador":[[0,178,1,null],[8,7,0,12.5],[17,178,0,0.56],[14,162.1,1,0.43],[13,171.8,0,0.29],[15,261.2,1,0.11]],"Meia ofensivo armador":[[0,179,1,null],[10,6,1,20],[6,7.5,0,6.25],[16,50.3,1,1.41],[1,73,1,1.39],[14,161.9,1,1.06],[13,172.75,1,0.64],[17,180,1,0.56],[15,260.95,0,0.1]],"Segundo atacante":[[0,180,1,null],[2,7,1,16.67],[4,7,1,16.67],[9,8,1,14.29],[8,8,0,11.11],[1,74,1,2.78],[16,50.5,1,1.41],[13,174.9,1,1.27],[14,163.7,1,0.92],[17,181,1,0.56],[15,263.1,1,0.27]],"Ponta criadora":[[0,175,1,null],[9,8.5,1,21.43],[10,6,1,20],[5,7,1,16.67],[11,7,1,16.67],[7,6,0,14.29],[12,8,1,14.29],[3,9,1,12.5],[2,6.5,1,8.33],[6,8.5,1,6.25],[1,72,1,1.41],[16,48.9,0,1.01],[15,259,0,0.94],[13,169.9,0,0.73],[17,177,0,0.56],[14,159.65,0,0.34]],"Ponta finalizadora":[[0,178,1,null],[12,6,0,14.29],[1,72,0,1.37],[17,183,1,1.1],[13,175,1,0.63],[16,49.5,0,0.6],[15,262.6,1,0.38],[14,163,1,0.12]]};

/* ===== v134 · CORPO DAS 97 CARTAS DOS PACOTES (sessao do motor, 03/08) =====
   As 16 medidas vieram de /api/public/players/{id} -> playerModel.
   Sem elas o bonus de corpo ficava 0 e a nota saia errada NOS DOIS SENTIDOS. */
if(false){
const CORPO97={"52896280457223":[5,10,4,8,8,9,11,10,5,8,6,170,156.5,260.9,49.4,178],"105835292374467":[9,6,6,6,6,3,7,7,5,5,7,170.8,162.6,255.2,49,177],"105859401165777":[5,9,5,1,6,5,10,5,5,3,5,176.3,162.6,258.3,50.7,184],"105884634194916":[7,7,5,6,7,9,11,2,6,4,2,173.9,161.6,257.9,49.4,182],"106788724836718":[7,5,8,5,7,3,9,6,5,4,5,180.6,168.5,266.7,51.1,188],"105854300981393":[5,8,8,5,6,8,7,5,4,5,5,168.9,157.1,253,48.8,175],"105855106307448":[6,7,11,6,10,8,7,7,7,8,7,173.7,162.4,262.1,50.2,180],"105855106324436":[7,7,5,5,11,7,7,7,5,5,7,179.5,168.9,267.2,51.7,186],"105884634176665":[4,7,7,5,7,11,7,10,8,7,11,181.4,167.5,264.5,52.5,188],"105884634185427":[7,9,6,6,7,9,11,6,6,6,6,179.8,167.4,264.2,51.8,188],"52896280457526":[9,6,10,7,7,2,6,9,7,7,8,175.1,167.2,269.8,50.5,181],"88040387251729":[8,8,7,7,9,6,11,9,8,9,9,174.9,163.7,258.1,50.3,183],"52896280448144":[6,11,6,6,7,9,10,7,7,7,7,178.2,165.9,251.9,52.2,186],"105859401163965":[2,7,5,5,8,10,11,6,5,4,7,170,153,249.3,48.3,178],"105835241972925":[2,7,5,5,8,10,11,6,5,4,7,170,153,249.3,48.3,178],"106788456363289":[5,7,4,9,12,9,8,8,9,7,8,172.3,159.6,259.6,49.8,179],"105884634188207":[9,11,6,6,8,9,11,6,6,6,9,173.9,164.4,256.8,50.7,182],"52896012049652":[6,7,5,6,8,9,7,7,7,7,7,179.5,167.8,259.9,51.8,186],"105859401160231":[5,8,5,3,3,3,7,8,5,4,8,179.5,166.9,264.6,52,186],"52895743535509":[7,7,5,6,4,9,11,6,6,6,6,169,157.1,259.5,48.1,177],"105854300973679":[5,8,4,5,9,7,7,7,5,5,6,162.1,150.8,245.7,47,168],"105855106313816":[6,8,5,7,7,9,8,7,7,7,7,168.4,157.2,255.2,48.8,175],"105855106317534":[7,6,7,5,7,3,7,6,6,7,5,165,155.1,250.1,47.3,171],"106788456409199":[7,8,5,6,7,9,11,7,6,8,6,177.8,165.4,263.2,51,186],"105855106313897":[5,6,7,6,10,6,5,7,6,7,5,174.5,163,258.5,50.4,180],"52896011971406":[7,7,7,7,5,4,7,8,7,10,7,184.3,173.4,255.6,53.3,191],"89138556700485":[11,11,7,7,7,7,14,8,5,5,8,183.4,173.9,265.8,53,193],"105859485110629":[5,10,5,5,10,7,11,5,3,8,4,182.7,168.2,256.3,52.7,191],"88045219096844":[4,6,6,3,10,6,5,9,4,6,8,164,152.2,252.5,47.2,169],"89138556678270":[12,5,4,6,7,11,14,5,9,5,3,175.5,166.4,261.6,49,185],"52895743616652":[8,8,5,6,7,9,11,7,5,6,5,173.9,162.8,261.2,49.8,182],"105859401156605":[5,9,5,8,7,3,7,6,8,8,8,185.3,172.5,269.2,54.2,192],"105884634196567":[6,11,5,10,11,10,4,11,10,9,9,164.4,155.9,253.2,49.4,169],"105835242034156":[7,7,6,5,10,7,9,7,5,6,7,172.8,161.6,259.5,49.5,180],"52896280487327":[7,5,5,6,4,9,9,6,7,5,6,181.6,169.4,269.5,51.5,189],"106788724799833":[11,10,5,10,8,7,12,4,4,5,4,180.3,171.8,265.2,52.1,189],"105884634233598":[6,7,5,6,7,9,7,7,7,8,7,178.5,166.9,248.4,51.5,185],"105884634201900":[6,7,5,6,7,9,7,7,7,8,7,179.5,167.8,264.6,51.8,186],"105859401162517":[5,8,6,9,10,8,9,9,7,9,9,177.7,164.3,253.9,51.5,185],"52895743595540":[5,7,5,7,10,5,8,11,6,5,9,170.4,157.8,260.5,49.2,177],"105855106319035":[6,6,9,6,6,7,7,5,6,5,6,176.6,164.9,263.9,50.6,183],"105855106307706":[7,8,5,8,7,7,13,7,7,8,6,186.8,172.7,265.3,53.3,196],"52895743617950":[5,9,5,6,7,6,9,7,9,4,7,180.6,167.1,262.6,52.5,188],"105884634166456":[5,8,4,6,10,3,7,7,5,7,7,180.5,167.8,256.7,52.3,187],"88044145351389":[7,8,6,7,7,7,9,9,10,7,9,174.8,163.6,259.5,50.7,182],"52896012078905":[8,7,6,4,7,8,11,5,4,4,5,178.8,167.2,269.8,50.7,187],"88044145213492":[3,8,6,2,6,4,8,10,5,7,9,169.4,155.1,258.5,48.9,176],"105855106300661":[4,6,4,5,6,8,10,5,5,3,5,165.6,151.3,250.4,46.9,173],"105854300977016":[4,6,7,5,9,8,4,7,4,5,6,174,162,261.1,50.3,179],"105835242048365":[5,8,4,5,8,2,8,8,6,5,8,179.1,166.1,264,51.8,186],"105859401178925":[7,7,7,7,6,5,9,7,6,6,6,189.3,177.1,260.9,54.3,197],"89138556572074":[1,9,7,6,8,2,9,7,4,5,6,181.6,163.8,265.4,52.6,189],"89138556575063":[5,9,6,9,9,2,3,9,7,10,10,162,152.8,256.1,48.1,166],"106788187843931":[7,8,4,8,9,7,8,7,8,7,6,175.2,164.5,262.6,50.8,182],"106788187841133":[6,9,7,3,9,8,7,10,4,7,9,173.7,162.8,262.4,50.6,180],"106788187839904":[5,9,5,8,9,5,9,9,4,6,9,169.9,157.2,258.2,49.4,177],"106788187833650":[7,7,6,5,8,9,9,8,5,5,10,167,156.2,256.8,47.8,174],"106788187832737":[9,10,8,5,6,5,11,5,5,8,6,188.6,178,263.8,54.5,197],"105859401166632":[7,7,7,5,9,3,11,5,4,5,6,190.5,177.1,264.9,54.1,199],"105859401239571":[5,8,5,5,9,6,7,7,5,5,7,174.7,162.5,260.2,50.6,181],"105859485069597":[7,6,5,3,7,9,9,5,3,7,5,173.8,162.4,262.2,49.2,181],"88044682118054":[3,7,7,7,13,8,8,14,9,9,14,167.5,153.1,256.1,48.6,174],"88045218959416":[6,8,6,12,13,7,6,13,13,8,13,169.3,159,258.8,50,175],"88039581811496":[9,12,7,7,9,4,11,7,7,7,7,188.6,178.4,253.6,55.4,197],"88040387119176":[4,5,4,5,8,9,7,7,7,6,8,180.5,166.2,264,51.5,187],"88040387163000":[7,8,6,0,7,7,7,4,2,6,4,173.7,163.6,261.5,49.9,180],"88040387251634":[4,11,4,7,10,9,7,11,6,8,10,164.1,152.1,249,48.6,170],"88040387251674":[6,12,9,3,7,0,9,8,2,3,8,177.7,166,266.6,52.2,185],"88041460993512":[7,7,7,8,9,7,11,8,7,8,8,185.6,172.5,267.8,53.1,194],"88044145214260":[8,7,7,7,10,7,11,7,7,7,7,187.6,175.4,265.8,53.5,196],"88030991881014":[5,9,5,4,11,7,7,7,2,6,7,164.1,152.8,253.9,47.6,170],"88029918268857":[5,7,6,12,12,6,8,9,8,9,7,172.3,159.6,250.2,50,179],"88031797317097":[6,9,9,6,7,4,8,7,7,7,7,182,170,270.9,53,189],"88029649833482":[7,4,7,0,7,6,7,8,6,8,8,194.9,182.8,272.5,55,202],"52896280508738":[7,5,5,6,8,9,13,5,5,4,4,176.9,163.1,267.8,49.4,186],"52896012028215":[2,5,9,5,12,9,6,7,5,7,6,169.3,154.4,264.8,48.4,175],"52896280457250":[8,9,6,3,7,9,13,5,3,3,6,175,163,265.4,49.8,184],"52896012021812":[5,10,4,5,8,4,9,7,5,2,7,170.9,158.3,262.9,49.8,178],"52896012020127":[7,8,8,5,8,4,7,7,5,7,7,181.4,170.9,273.3,52.6,188],"52895743604432":[10,10,5,9,7,10,11,11,10,9,6,178.8,169.9,268.2,52.3,187],"52895743520095":[8,6,11,1,7,6,12,5,3,6,7,196,182.5,269,54.9,205],"52896280488202":[7,9,6,6,8,9,11,7,6,6,6,172,160.2,262.8,49.6,180],"52896280461130":[7,7,6,4,7,7,7,7,5,5,6,186.2,175.2,279.1,53.6,193],"52896280460029":[10,13,6,10,11,1,8,9,5,8,7,174.2,167.6,264.8,52,181],"52896280392617":[7,7,7,7,7,7,7,9,6,10,9,176.6,166.2,260.1,51.1,183],"52896012048168":[8,10,5,6,9,9,11,7,5,6,5,174.9,164.1,264.8,50.7,183],"52896012041487":[8,8,9,4,8,4,7,8,6,7,8,179.5,170.1,271.6,52,186],"52896012025128":[8,8,7,7,7,5,7,7,6,6,9,174.7,165.6,266,50.7,181],"52895743641408":[5,8,5,6,7,7,9,7,7,8,7,178.7,165.2,263.2,51.6,186],"52895743602336":[7,12,4,11,7,11,10,11,10,11,9,165.6,155.2,255,49.2,173],"52895743589623":[5,7,7,4,7,9,8,5,4,7,6,176.2,163.2,267,50.4,183],"52896012059063":[5,9,5,5,9,6,7,7,7,5,7,172.7,160.8,264.2,50.4,179],"105835241963937":[9,10,8,5,6,5,11,5,5,8,6,188.6,178,263.8,54.5,197],"105835242039414":[8,5,8,6,7,5,7,7,2,4,6,174.7,165,263,49.7,181],"105835242041536":[8,9,5,10,9,5,10,10,4,8,10,176.3,165.7,258.3,51.2,184],"105835242060713":[10,10,4,5,9,5,7,7,7,7,7,178.5,171.7,264,52.4,185],"106771813384691":[9,8,7,7,7,8,9,7,7,6,5,176.7,167.5,265.1,51,184]};
const PACOTE={"52896280457223": "POTW European Club Championship 23 Apr '26", "105835292374467": "National Team Icons vol.3", "105859401165777": "Living Legends 2026", "105884634194916": "Pressure-Proof 2026", "106788724836718": "Pressure-Proof 2026", "105854300981393": "Thailand Selection 27 Jul '26", "105855106307448": "Victory Drivers 2026", "105855106324436": "Victory Drivers 2026", "105884634176665": "Pressure-Proof 2026", "105884634185427": "Pressure-Proof 2026", "52896280457526": "POTW European Club Championship 23 Apr '26", "88040387251729": "Sem box confirmada", "52896280448144": "POTW European Club Championship 23 Apr '26", "105859401163965": "Living Legends 2026", "105835241972925": "National Team Icons vol.3", "106788456363289": "Victory Drivers 2026", "105884634188207": "Pressure-Proof 2026", "52896012049652": "POTW European Club Championship 26 Mar '26", "105859401160231": "Living Legends 2026", "52895743535509": "POTW European Club Championship 19 Mar '26", "105854300973679": "Thailand Selection 27 Jul '26", "105855106313816": "Victory Drivers 2026", "105855106317534": "Victory Drivers 2026", "106788456409199": "Victory Drivers 2026", "105855106313897": "Victory Drivers 2026", "52896011971406": "POTW European Club Championship 26 Mar '26", "89138556700485": "Sem box confirmada", "105859485110629": "Living Legends 2026", "88045219096844": "Sem box confirmada", "89138556678270": "Sem box confirmada", "52895743616652": "POTW European Club Championship 19 Mar '26", "105859401156605": "Living Legends 2026", "105884634196567": "Pressure-Proof 2026", "105835242034156": "National Team Icons vol.3", "52896280487327": "POTW European Club Championship 23 Apr '26", "106788724799833": "Pressure-Proof 2026", "105884634233598": "Pressure-Proof 2026", "105884634201900": "Pressure-Proof 2026", "105859401162517": "Living Legends 2026", "52895743595540": "POTW European Club Championship 19 Mar '26", "105855106319035": "Victory Drivers 2026", "105855106307706": "Victory Drivers 2026", "52895743617950": "POTW European Club Championship 19 Mar '26", "105884634166456": "Pressure-Proof 2026", "88044145351389": "Sem box confirmada", "52896012078905": "POTW European Club Championship 26 Mar '26", "88044145213492": "Sem box confirmada", "105855106300661": "Victory Drivers 2026", "105854300977016": "Thailand Selection 27 Jul '26", "105835242048365": "National Team Icons vol.3", "105859401178925": "Living Legends 2026", "89138556572074": "Big Time Portugal 23 Jun '26", "89138556575063": "Sem box confirmada", "106788187843931": "Living Legends 2026", "106788187841133": "Living Legends 2026", "106788187839904": "Living Legends 2026", "106788187833650": "Living Legends 2026", "106788187832737": "Living Legends 2026", "105859401166632": "Living Legends 2026", "105859401239571": "Living Legends 2026", "105859485069597": "Living Legends 2026", "88044682118054": "Sem box confirmada", "88045218959416": "Sem box confirmada", "88039581811496": "Sem box confirmada", "88040387119176": "Sem box confirmada", "88040387163000": "Sem box confirmada", "88040387251634": "Sem box confirmada", "88040387251674": "Sem box confirmada", "88041460993512": "Sem box confirmada", "88044145214260": "Sem box confirmada", "88030991881014": "Sem box confirmada", "88029918268857": "Sem box confirmada", "88031797317097": "Sem box confirmada", "88029649833482": "Sem box confirmada", "52896280508738": "POTW European Club Championship 23 Apr '26", "52896012028215": "POTW European Club Championship 26 Mar '26", "52896280457250": "POTW European Club Championship 23 Apr '26", "52896012021812": "POTW European Club Championship 26 Mar '26", "52896012020127": "POTW European Club Championship 26 Mar '26", "52895743604432": "POTW European Club Championship 19 Mar '26", "52895743520095": "POTW European Club Championship 19 Mar '26", "52896280488202": "POTW European Club Championship 23 Apr '26", "52896280461130": "POTW European Club Championship 23 Apr '26", "52896280460029": "POTW European Club Championship 23 Apr '26", "52896280392617": "POTW European Club Championship 23 Apr '26", "52896012048168": "POTW European Club Championship 26 Mar '26", "52896012041487": "POTW European Club Championship 26 Mar '26", "52896012025128": "POTW European Club Championship 26 Mar '26", "52895743641408": "POTW European Club Championship 19 Mar '26", "52895743602336": "POTW European Club Championship 19 Mar '26", "52895743589623": "POTW European Club Championship 19 Mar '26", "52896012059063": "POTW European Club Championship 26 Mar '26", "105835241963937": "National Team Icons vol.3", "105835242039414": "National Team Icons vol.3", "105835242041536": "National Team Icons vol.3", "105835242060713": "National Team Icons vol.3", "106771813384691": "eFootball™ League Rewards Phase 13", "105866112118910": "Welcome Login Bonus 2027", "105866112143259": "Welcome Login Bonus 2027", "105866380552607": "Skill Up 2027", "105866112053032": "Welcome Login Bonus 2027", "105866917436893": "New Season Campaign 2027", "105873628309622": "New Season Campaign 2027", "105873628311604": "New Season Campaign 2027", "105873628311744": "New Season Campaign 2027", "105866917459000": "New Season Campaign 2027", "105873628311862": "New Season Campaign 2027", "105873628348195": "New Season Campaign 2027", "105866917361630": "New Season Campaign 2027", "105866917432656": "New Season Campaign 2027", "105866917449491": "New Season Campaign 2027", "88045755863174": "Chelsea B Selection 14 Aug '26", "88045487427597": "Chelsea B Selection 14 Aug '26", "106785772007373": "Summer Transfer 17 Aug '26", "106785772021264": "Summer Transfer 17 Aug '26", "88045487423105": "Chelsea B Selection 14 Aug '26", "88045755964125": "Daily Bonus 2027", "105865038310751": "Leo Messi Edition 2027", "106785771992434": "Summer Transfer 17 Aug '26", "88046829575511": "Leo Messi Edition 2027", "88047098165570": "Lamine Yamal Edition 2027", "105864769947959": "Tactical Defence 13 Aug '26", "105865843704022": "Starter Set 2027", "105867454344792": "Daily Bonus 2027", "105873896766735": "English League Selection 13 Aug '26", "106784966581591": "Skill Up 2027", "106785235123572": "eFootball™ League 2027 Rewards Phase 1", "106787114104779": "Daily Bonus 2027", "88045755827674": "Daily Bonus 2027", "105863964635188": "Advertisement Reward 2027", "105865306857038": "Lamine Yamal Edition 2027", "105865306863987": "Lamine Yamal Edition 2027", "105865843676422": "Starter Set 2027", "105865843702105": "Starter Set 2027", "105866648987766": "Step-up 2027", "105867185858673": "Daily Bonus 2027", "105873091445023": "Summer Transfer 13 Aug '26", "105873091448219": "Summer Transfer 13 Aug '26", "105873896755947": "English League Selection 13 Aug '26", "105873896760682": "English League Selection 13 Aug '26", "105873896763633": "English League Selection 13 Aug '26", "105873896774572": "English League Selection 13 Aug '26", "105873896778628": "English League Selection 13 Aug '26", "105880691466019": "CAF Africa Cup of Nations Selection 13 Aug '26", "105880691550984": "CAF Africa Cup of Nations Selection 13 Aug '26", "88045755829674": "Advertisement Reward 2027", "88045755866499": "Daily Bonus 2027", "88045755960768": "Advertisement Reward 2027", "88045755960849": "Advertisement Reward 2027", "105863964584785": "Advertisement Reward 2027", "105863964636344": "Advertisement Reward 2027", "105863964686707": "Advertisement Reward 2027", "105864769948954": "Tactical Defence 13 Aug '26", "105864769962198": "Tactical Defence 13 Aug '26", "105865038308792": "Leo Messi Edition 2027", "105865038367702": "Leo Messi Edition 2027", "105865306838492": "Lamine Yamal Edition 2027", "105865306864830": "Lamine Yamal Edition 2027", "105865306872202": "Lamine Yamal Edition 2027", "105865306872490": "Lamine Yamal Edition 2027", "105865575254367": "Manager Pack 13 Aug '26", "105866649005150": "Step-up 2027", "105866649017104": "Step-up 2027", "105868528074316": "Chelsea B Selection 14 Aug '26", "105868528075260": "Chelsea B Selection 14 Aug '26", "105868528101388": "Chelsea B Selection 14 Aug '26", "105869333368702": "Summer Transfer 17 Aug '26", "105873091431106": "Summer Transfer 13 Aug '26", "105873091473615": "Summer Transfer 13 Aug '26", "105873896751326": "English League Selection 13 Aug '26", "105873896771214": "English League Selection 13 Aug '26", "105873896779262": "English League Selection 13 Aug '26", "105863964625602": "Advertisement Reward 2027", "105863964672716": "Advertisement Reward 2027", "105864769937869": "Tactical Defence 13 Aug '26", "105864769941508": "Tactical Defence 13 Aug '26", "105865038306663": "Leo Messi Edition 2027", "105865038307964": "Leo Messi Edition 2027", "105865038312124": "Leo Messi Edition 2027", "105865038313234": "Leo Messi Edition 2027", "105865038376671": "Leo Messi Edition 2027", "105865306842764": "Lamine Yamal Edition 2027", "105865306845091": "Lamine Yamal Edition 2027", "105865306855034": "Lamine Yamal Edition 2027", "105865306866884": "Lamine Yamal Edition 2027", "105865575300328": "Manager Pack 13 Aug '26", "105867185797302": "Daily Bonus 2027", "105867185851044": "Daily Bonus 2027", "105867454305172": "Daily Bonus 2027", "105867454312689": "Daily Bonus 2027", "105867454313810": "Daily Bonus 2027", "105868528086725": "Chelsea B Selection 14 Aug '26", "105873091468038": "Summer Transfer 13 Aug '26", "105873091489528": "Summer Transfer 13 Aug '26", "105873091492244": "Summer Transfer 13 Aug '26", "105873091504239": "Summer Transfer 13 Aug '26", "105873896745385": "English League Selection 13 Aug '26", "105873896750438": "English League Selection 13 Aug '26", "105861817154804": "Moroccan League Selection 13 Aug '26", "105861817157277": "Moroccan League Selection 13 Aug '26", "105861817219813": "Moroccan League Selection 13 Aug '26", "105861817219822": "Moroccan League Selection 13 Aug '26", "105861817219831": "Moroccan League Selection 13 Aug '26", "105863964635994": "Advertisement Reward 2027", "105863964642476": "Advertisement Reward 2027", "105864769951152": "Tactical Defence 13 Aug '26", "105865038307949": "Leo Messi Edition 2027", "105865038392713": "Leo Messi Edition 2027", "105868528054502": "Chelsea B Selection 14 Aug '26", "105868528071235": "Chelsea B Selection 14 Aug '26", "105869333361235": "Summer Transfer 17 Aug '26", "105869333393229": "Summer Transfer 17 Aug '26", "105869333394562": "Summer Transfer 17 Aug '26", "105880691466200": "CAF Africa Cup of Nations Selection 13 Aug '26", "105880691517588": "CAF Africa Cup of Nations Selection 13 Aug '26", "105880691523097": "CAF Africa Cup of Nations Selection 13 Aug '26", "105880691523462": "CAF Africa Cup of Nations Selection 13 Aug '26", "105880691532128": "CAF Africa Cup of Nations Selection 13 Aug '26", "105880691550364": "CAF Africa Cup of Nations Selection 13 Aug '26", "105861817160530": "Moroccan League Selection 13 Aug '26", "105861817180967": "Moroccan League Selection 13 Aug '26", "105861817187270": "Moroccan League Selection 13 Aug '26", "105861817205535": "Moroccan League Selection 13 Aug '26", "105861817208648": "Moroccan League Selection 13 Aug '26", "105861817219819": "Moroccan League Selection 13 Aug '26", "105864769945293": "Tactical Defence 13 Aug '26", "105868528055595": "Chelsea B Selection 14 Aug '26", "105868528068056": "Chelsea B Selection 14 Aug '26", "105869333415031": "Summer Transfer 17 Aug '26", "105864769871207": "Tactical Defence 13 Aug '26", "105869333357110": "Summer Transfer 17 Aug '26", "105869333381118": "Summer Transfer 17 Aug '26", "105869333401321": "Summer Transfer 17 Aug '26", "105553921606966": "Club Pack Club América Aug '22", "105561169438455": "National Team Selection Italy [Deluxe] Nov '22", "105561706240865": "Alltime Greats Nov '22", "105563853717921": "National Team Pack Germany '22", "105568685563515": "Derby Day Manchester 14 Jan '23", "105580765180136": "Club Selection FC Barcelona 22 May '23", "105586670755629": "Breakout Stars 6 Jul '23", "105590160392609": "Back in the Game 3 Aug '23", "105621835804904": "Leo Messi Edition '23", "105622909546728": "Startup Campaign 7 Sep '23", "105638478848461": "Spanish League Selection Guardians 27 Nov '23", "105648142451105": "FC Bayern München Selection 15 Jan '24", "105659953622088": "Spanish League Selection Guardians 25 Mar '24", "105661027358435": "The All-Rounders 11 Apr '24", "105705050796264": "Magical Dribbler 12 Sep '24", "105706124621334": "Spanish League Selection 19 Sep '24", "105723035943329": "Captain Tsubasa Collaboration Campaign 5 Dec '24", "105727867788923": "Mid-season MVPs 9 Jan '25", "105745047661640": "Spanish League Selection 6 Mar '25", "105757664212756": "National Teams Selection European 22 May '25", "105766522560972": "Epic Nostalgia 26 Jun '25", "105783165492859": "Italian League Selection 18 Sep '25", "105799271724566": "Liverpool R Selection 23 Mar '26", "105799540076776": "Winter Transfer 23 Feb '26", "105799808558839": "Manchester B Selection 26 Jan '26", "105800613898989": "National Team Selection Worldwide 30 Apr '26", "105801687639790": "Spanish League Selection 2 Apr '26", "105802224470740": "English League Selection 5 Feb '26", "105803029803070": "European Clubs Selection 13 Nov '25", "105804640430829": "Borussia Dortmund Pack 25-26", "105805714171630": "FC Barcelona Pack 25-26", "105826652141078": "European Clubs Selection Guardians 9 Feb '26", "105829336468960": "Elite Lineage 30 Apr '26", "105851968872237": "National Team Selection Morocco Jun '26", "105860290427681": "National Team Selection Senegal Jun '26", "106727789930231": "Show Time Ligue 1 Uber Eats 23-24", "106738795720031": "Standout Lefties 3 Feb '25", "106740406335670": "GK Directing Defence 29 May '25", "106740406401980": "GK Directing Defence 29 May '25", "106740406415422": "GK Directing Defence 29 May '25", "106741480063393": "FC Bayern München Selection 15 May '25", "106744164503008": "Italian League 24-25 Season's Best", "106744432941483": "Brazilian League Selection 26 Jun '25", "106750338463730": "Trusted Shields 22 Sep '25", "106758173464832": "National Team Selection Indonesia 2 Oct '25", "106759196878583": "Anticipated Standouts 13 Oct '25", "106762418131391": "Japanese Stars 10 Nov '25", "106763491781983": "Towering Giants 29 Dec '25", "106764917858093": "Best Players of CAF AFRICA CUP OF NATIONS 25", "106768860487291": "eFootball™ League Rewards Phase 7", "106771008035172": "Trendyol Süper Lig Monthly MVPs Feb '26", "106775839943506": "J.LEAGUE Monthly MVPs Apr '26", "106776645183223": "Standout Guardians 25-26 Season's Best", "106777987393262": "Spanish League 25-26 Season's Best", "106778524224656": "European Club Championship 25-26 Season's Best", "106783356096959": "Japan Selection 11 Jul '26", "106785503587053": "The Football Festival Campaign 2026", "106787651035597": "Spain 2026", "17592186045268": "Sem box confirmada", "17592454480724": "Sem box confirmada", "17592991488743": "Sem box confirmada", "52781658507988": "POTW International Cup 22 Dec '22", "52786758721147": "POTW 25 May '23", "52845546085217": "POTW National Teams 14 Sep '23", "52846888261347": "POTW 12 Oct '23", "52847156719848": "POTW European Club Championship 12 Oct '23", "52848498943735": "POTW European Club Championship 2 Nov '23", "52851988604663": "POTW 18 Jan '24", "52869705269665": "POTW European Club Championship 25 Apr '24", "52869973708663": "POTW 2 May '24", "52871047475432": "POTW 30 May '24", "52871315893320": "POTW National Teams 20 Jun '24", "52871852847166": "POTW National Teams 4 Jul '24", "52876953037896": "POTW European Club Championship 14 Nov '24", "52877489905275": "POTW 28 Nov '24", "52878026768801": "POTW European Club Championship 5 Dec '24", "52880174266079": "POTW 30 Jan '25", "52881248005192": "POTW 13 Feb '25", "52882858634271": "POTW National Teams 27 Mar '25", "52884737662953": "POTW European Club Championship 13 Mar '25", "52885006165751": "POTW European Club Championship 20 Mar '25", "52885811464916": "POTW 15 May '25", "52888227330230": "POTW 28 Aug '25", "52891448637204": "POTW National Teams 20 Nov '25", "52891717004319": "POTW 27 Nov '25", "52892790826734": "POTW 25 Dec '25", "52894401405389": "POTW European Club Championship 18 Dec '25", "52894938298132": "POTW European Club Championship 5 Feb '26", "52897354189524": "POTW 29 Jan '26", "52897622651925": "POTW 5 Feb '26", "52898427941722": "POTW 26 Feb '26", "52899501713134": "POTW 26 Mar '26", "52899770134230": "POTW National Teams 2 Apr '26", "52900038483579": "POTW 9 Apr '26", "52901380664392": "POTW 21 May '26", "53976464668196": "POTM Brazilian League 10 Jul '25", "55068460171804": "POTS English League 24-25", "55068728633070": "POTS Spanish League 24-25", "55069265399671": "POTS Trendyol Süper Lig 24-25", "55069802361877": "POTS Italian League 25-26", "55070339149151": "POTS Spanish League 25-26", "55070607676904": "POTS English League 25-26", "55070876122984": "POTS Trendyol Süper Lig 25-26", "56163190239491": "POTD International Cup Day 11", "56164482083871": "POTD International Cup Day 16", "56164750585918": "POTD International Cup Day 17", "56165019067344": "POTD International Cup Day 18-19", "56167166556926": "POTD International Cup Day 27", "56167434870573": "POTD International Cup Day 28-29", "56168240220884": "POTD International Cup Day 33-34", "87962272537319": "Sem box confirmada", "87963346142036": "Sem box confirmada", "87963346144375": "Sem box confirmada", "87963614581408": "Sem box confirmada", "88029918135124": "Sem box confirmada", "88029918137463": "Sem box confirmada", "88030455143143": "Sem box confirmada", "88031797183316": "Sem box confirmada", "88032065621111": "Sem box confirmada", "88032334187979": "Sem box confirmada", "88032334191335": "Sem box confirmada", "88033407796052": "Sem box confirmada", "88033407798391": "Sem box confirmada", "88033407929799": "Sem box confirmada", "88033944800711": "Germany 2002 feat. Captain Tsubasa", "88035823852263": "Sem box confirmada", "88036092150743": "Sem box confirmada", "88036360586068": "Sem box confirmada", "88036360588407": "Sem box confirmada", "88036360719819": "Sem box confirmada", "88038776505238": "Sem box confirmada", "88039045074401": "Sem box confirmada", "88039581948647": "Sem box confirmada", "88040387118039": "Sem box confirmada", "88040387120247": "Sem box confirmada", "88040387255015": "National Teams Selection Guardians 25 May '26", "89136946097691": "Big Time Kashima Antlers 20 Sep '25", "89138288133079": "Italy Selection 11 Jun '26", "105553384806629": "Transfer Aug '22", "105557948218809": "Club Pack FC Bayern München Oct '22", "105561169444838": "National Team Selection Italy [Deluxe] Nov '22", "105562243176752": "National Team Selection France 21 Nov '22", "105563048421444": "National Team Pack France [Premium] Nov '22", "105568954067359": "Club Icons Jan '23", "105572980533316": "Derby Day England 5 Mar '23", "105574322779320": "Club Selection Manchester B 3 Apr '23", "105575396416673": "European Club Championship Selection 16 Mar '23", "105576201761705": "Masterful Stars 13 Apr '23", "105576201779319": "Masterful Stars 13 Apr '23", "105578617670692": "Club Selection Chelsea B 8 May '23", "105579959944852": "End-season MVPs 11 May '23", "105580496794182": "League Selection Italian 15 May '23", "105582644280761": "Club Selection FC Bayern München 5 Jun '23", "105585328643029": "Fans' Choice Asia 22-23", "105585597067456": "Fans' Choice Young Stars 22-23", "105588281359016": "National Team Selection Colombia 31 Jul '23", "105589623605167": "National Team Selection France 24 Jul '23", "105590160485839": "Back in the Game 3 Aug '23", "105590697335088": "Summer Tour in Japan 14 Aug '23", "105590697338022": "Summer Tour in Japan 14 Aug '23", "105592844749860": "Summer Transfer 3 Aug '23", "105629351979076": "Manchester United FC Pack 5 Oct '23", "105629620493269": "Arsenal FC Pack 5 Oct '23", "105632841711033": "Halloween Campaign 26 Oct '23", "105655927053473": "Spanish League Selection 14 Mar '24", "105655927154806": "Spanish League Selection 14 Mar '24", "105656463961896": "English League Selection 14 Mar '24", "105659953691509": "Spanish League Selection Guardians 25 Mar '24", "105663174864633": "English League Selection Guardians 11 Apr '24", "105663174930145": "English League Selection Guardians 11 Apr '24", "105679817928417": "Speedsters 9 May '24", "105683039136529": "National Team Pack England '24", "105683844342701": "National Team Pack Portugal '24", "105684649687720": "National Teams Selection Worldwide 13 Jun '24", "105684649772480": "National Teams Selection Worldwide 13 Jun '24", "105692434376822": "Leo Messi Edition 2025", "105695387103016": "Welcome Login Bonus", "105701561184448": "Startup Campaign 12 Sep '24", "105705856155870": "English League Selection 19 Sep '24", "105706124602831": "Spanish League Selection 19 Sep '24", "105716056649465": "Earthmover 7 Nov '24", "105716056708070": "Earthmover 7 Nov '24", "105716056728354": "Earthmover 7 Nov '24", "105723036026799": "Captain Tsubasa Collaboration Campaign 5 Dec '24", "105723841328312": "National Teams Selection European 12 Dec '24", "105733773457753": "Ramadan Campaign 20 Feb '25", "105733773466384": "Ramadan Campaign 20 Feb '25", "105744779312437": "Italian League Selection 27 Mar '25", "105745047731917": "Spanish League Selection 6 Mar '25", "105745047765545": "Spanish League Selection 6 Mar '25", "105745047783232": "Spanish League Selection 6 Mar '25", "105745316167967": "English League Selection 6 Mar '25", "105747732088751": "International Cup Qualifiers Campaign 13 Mar '25", "105750684898296": "English League Selection 24 Apr '25", "105750684926988": "English League Selection 24 Apr '25", "105751221741686": "The Art of Passing 17 Apr '25", "105754979770527": "Winter Transfer 3 Mar '25", "105756053603387": "Elite Lineage 15 May '25", "105761422295232": "English League Selection Guardians 26 May '25", "105768133193441": "National Teams Selection 17 Jul '25", "105770817532096": "Champions Campaign 24-25 FC Barcelona", "105775380983650": "Lamine Yamal Edition 2026", "105776186238118": "Daily Bonus 2026", "105776186272669": "Daily Bonus 2026", "105779675904885": "Back in the Game 14 Aug '25", "105781018104141": "Italian League Selection Guardians 21 Aug '25", "105782628618516": "Italian League Selection Guardians 8 Sep '25", "105782897169290": "Anticipated Standouts 25-26", "105783165584350": "Italian League Selection 18 Sep '25", "105785849923497": "National Teams Selection Guardians 6 Oct '25", "105792023949025": "PFA Awards 2025", "105794171442168": "Speedsters 6 Nov '25", "105794171470860": "Speedsters 6 Nov '25", "105794439850769": "Clutch Players 4 Dec '25", "105799003257530": "AS Monaco Selection 20 Apr '26", "105799003270372": "AS Monaco Selection 20 Apr '26", "105799271624488": "Liverpool R Selection 23 Mar '26", "105799271742270": "Liverpool R Selection 23 Mar '26", "105800077021517": "Piemonte BN Selection 29 Dec '25", "105800882303664": "Tottenham WB Selection 3 Nov '25", "105801687534628": "Spanish League Selection 2 Apr '26", "105801687618534": "Spanish League Selection 2 Apr '26", "105801687636935": "Spanish League Selection 2 Apr '26", "105801956048801": "Italian League Selection 5 Mar '26", "105802224496079": "English League Selection 5 Feb '26", "105802492909797": "National Teams Selection 8 Jan '26", "105802492921775": "National Teams Selection 8 Jan '26", "105802492922090": "National Teams Selection 8 Jan '26", "105803298237825": "Spanish League Selection 16 Oct '25", "105803298257275": "Spanish League Selection 16 Oct '25", "105804103544545": "Arsenal FC Pack 25-26", "105804103550011": "Arsenal FC Pack 25-26", "105804103551534": "Arsenal FC Pack 25-26", "105804103565865": "Arsenal FC Pack 25-26", "105804640431005": "Borussia Dortmund Pack 25-26", "105804908838329": "Manchester United Pack 25-26", "105805714139254": "FC Barcelona Pack 25-26", "105805714141376": "FC Barcelona Pack 25-26", "105805714163136": "FC Barcelona Pack 25-26", "105817525312469": "Japanese Stars 6 Apr '26", "105820478091227": "European Clubs Selection 15 Jan '26", "105823967752880": "Daily Bonus 2026", "105827994319227": "Spanish League Selection Guardians 23 Feb '26", "105828799607548": "Role Changers 5 Mar '26", "105844905772864": "National Teams Campaign Mar '26", "105847053216618": "English League 25-26 Season's Best", "105849200705750": "National Team Pack England 2026", "105849469126575": "National Team Pack France 2026", "105849469129702": "National Team Pack France 2026", "105850005925672": "National Team Pack Netherlands 2026", "105850274440395": "National Team Selection Japan Jun '26", "105850542877475": "National Team Pack Türkiye 2026", "105850811233193": "National Team Selection Brazil Jun '26", "105850811298407": "National Team Selection Brazil Jun '26", "105851348171352": "National Team Selection Malaysia May '26", "105851348212928": "National Team Selection Malaysia May '26", "105851666965172": "National Team Selection Indonesia Jun '26", "105851666981523": "National Team Selection Indonesia Jun '26", "105851968934993": "National Team Selection Morocco Jun '26", "105852237353730": "National Team Selection Egypt Jun '26", "105852237362944": "National Team Selection Egypt Jun '26", "105852237395399": "National Team Selection Egypt Jun '26", "105852690346465": "The Football Festival Campaign 2026", "105854569331106": "Spain 2026", "105854569449280": "Spain 2026", "105855374705611": "Japan Selection 2 Jul '26", "105855374711765": "Japan Selection 2 Jul '26", "105855643177615": "Japan Selection 11 Jul '26", "105856716900910": "Italy Selection 11 Jun '26", "105857790613668": "National Teams Selection 29 Jun '26", "105858327501390": "National Teams Selection 6 Jul '26", "105860290416997": "National Team Selection Senegal Jun '26", "105860558796162": "National Team Selection Algeria Jun '26", "105860558858388": "National Team Selection Algeria Jun '26", "105867773075036": "National Team Selection Korea Republic Jun '26", "106654507064924": "Show Time Italian League 22-23", "106728595173160": "Show Time English League 23-24", "106730205873248": "Show Time Young Stars 23-24 Vol. 2", "106730205877240": "Show Time Young Stars 23-24 Vol. 2", "106732084830367": "Hard-working Players 3 Oct '24", "106734500753192": "Aerial Fort 9 Jan '25", "106734500820152": "Aerial Fort 9 Jan '25", "106734500820728": "Aerial Fort 9 Jan '25", "106738258909413": "National Teams Selection Guardians 20 Mar '25", "106738258937280": "National Teams Selection Guardians 20 Mar '25", "106739869539932": "Korea Republic Focus Campaign 13 Mar '25", "106740674763013": "Brazilian League Selection 29 May '25", "106741211655929": "Towering Giants 29 May '25", "106741748631921": "Trendyol Süper Lig Selection 15 May '25", "106742553882816": "Long-reach Tackle 1 May '25", "106742553898721": "Long-reach Tackle 1 May '25", "106743359189607": "English League 24-25 Season's Best", "106746899235852": "AFC Asian Qualifiers™ Selection 22 May '25", "106748459484820": "National Team Selection Portugal 4 Aug '25", "106749264802276": "Club International Cup Campaign 12 Jun '25", "106750338532448": "Trusted Shields 22 Sep '25", "106750338536440": "Trusted Shields 22 Sep '25", "106752485992566": "Squad Pillars 24-25 Season's Best", "106753828209219": "Show Time 9 Aug '25", "106755170349023": "Brazilian League Selection 28 Aug '25", "106755170353522": "Brazilian League Selection 28 Aug '25", "106755707155132": "Brazilian League Selection 30 Oct '25", "106756512520356": "Trendyol Süper Lig Monthly MVPs Aug '25", "106758173527305": "National Team Selection Indonesia 2 Oct '25", "106758928449823": "Earthmover 27 Oct '25", "106759465371456": "Rising Prodigies 15 Sep '25", "106759733774894": "Diagonal Long Pass B 6 Nov '25", "106761092659319": "AFC Champions League Elite™ Selection 20 Oct '25", "106761881238104": "National Teams Selection Southeast Asia 27 Nov '25", "106762149606313": "National Teams Selection 6 Nov '25", "106762955018895": "Japanese Stars 6 Apr '26", "106763491864289": "Towering Giants 29 Dec '25", "106763760292838": "Central Dominator 5 Jan '26", "106764917945800": "Best Players of CAF AFRICA CUP OF NATIONS 25", "106765454774629": "CAF AFRICA CUP OF NATIONS 25 vol.2", "106766176130728": "American League Selection 17 Nov '25", "106766981558114": "New Year's Gift 2026", "106768055185192": "Over-the-Top Pass C 5 Feb '26", "106768323680420": "Trendyol Süper Lig Monthly MVPs Jan '26", "106768592119926": "Attack Trigger 19 Feb '26", "106768592137310": "Attack Trigger 19 Feb '26", "106769665885243": "eFootball™ League Rewards Phase 10", "106769934330781": "eFootball™ League Rewards Phase 11", "106772350248490": "Trendyol Süper Lig Monthly MVPs Mar '26", "106772887089344": "FC Barcelona Selection 20 Apr '26", "106772887111104": "FC Barcelona Selection 20 Apr '26", "106776376791946": "Ligue 1 McDonald’s Selection 2 Mar '26", "106777718857892": "Starter Set 28 May '26", "106779329558490": "Trendyol Süper Lig Monthly MVPs May '26", "106780671715908": "Daily Bonus 2026", "106780940156345": "Mobile 9th Anniversary Celebration", "106782282337313": "International Cup vol.4", "106782819256128": "International Cup vol.6", "106783356085451": "Japan Selection 11 Jul '26", "106783356088205": "Japan Selection 11 Jul '26", "106785503556272": "The Football Festival Campaign 2026", "106787919475376": "Tournament Stars 2026", "17592186179010": "Sem box confirmada", "17592186179044": "Sem box confirmada", "17592186179052": "Sem box confirmada", "17592454614457": "Sem box confirmada", "17592454614466": "Sem box confirmada", "17592454614501": "Sem box confirmada", "17592454614504": "Sem box confirmada", "17592991485433": "Sem box confirmada", "52778168787119": "POTW European Club Championship 22 Sep '22", "52781121668192": "POTW International Cup 8 Dec '22", "52785953484992": "POTW 27 Apr '23", "52787295558817": "POTW 8 Jun '23", "52787564107184": "POTW National Teams 22 Jun '23", "52788637837430": "POTW 24 Aug '23", "52845277718943": "POTW 7 Sep '23", "52847156719353": "POTW European Club Championship 12 Oct '23", "52847693536417": "POTW 26 Oct '23", "52848767403456": "POTW 9 Nov '23", "52849304150957": "POTW European Club Championship 16 Nov '23", "52850109595212": "POTW 7 Dec '23", "52850378005461": "POTW European Club Championship 7 Dec '23", "52851720165605": "POTW 11 Jan '24", "52853062349460": "POTW 15 Feb '24", "52853330718504": "POTW 22 Feb '24", "52853330778381": "POTW 22 Feb '24", "52854404456607": "POTW 14 Mar '24", "52868094737849": "POTW European Club Championship 21 Mar '24", "52868631501985": "POTW 4 Apr '24", "52869168485350": "POTW 18 Apr '24", "52869705368672": "POTW European Club Championship 25 Apr '24", "52870779100117": "POTW 23 May '24", "52871852830912": "POTW National Teams 4 Jul '24", "52872121291768": "POTW National Teams 11 Jul '24", "52874537210872": "POTW 3 Oct '24", "52875073990890": "POTW European Club Championship 10 Oct '24", "52876684674991": "POTW 14 Nov '24", "52876953104576": "POTW European Club Championship 14 Nov '24", "52876953116252": "POTW European Club Championship 14 Nov '24", "52877221533925": "POTW National Teams 21 Nov '24", "52878026846823": "POTW European Club Championship 5 Dec '24", "52878026873799": "POTW European Club Championship 5 Dec '24", "52880174352942": "POTW 30 Jan '25", "52880979573417": "POTW European Club Championship 6 Feb '25", "52880979634637": "POTW European Club Championship 6 Feb '25", "52880979658176": "POTW European Club Championship 6 Feb '25", "52881248006378": "POTW 13 Feb '25", "52881248109097": "POTW 13 Feb '25", "52881516555945": "POTW 20 Feb '25", "52881784956107": "POTW 27 Feb '25", "52882590199545": "POTW 20 Mar '25", "52883127116966": "POTW 3 Apr '25", "52883663925032": "POTW 17 Apr '25", "52884200867759": "POTW European Club Championship 20 Feb '25", "52884737754171": "POTW European Club Championship 13 Mar '25", "52885274625684": "POTW European Club Championship 24 Apr '25", "52885543081851": "POTW 1 May '25", "52886616802964": "POTW National Teams 12 Jun '25", "52888227415099": "POTW 28 Aug '25", "52888764273638": "POTW National Teams 11 Sep '25", "52889301132454": "POTW 25 Sep '25", "52889301138293": "POTW 25 Sep '25", "52889569571431": "POTW 2 Oct '25", "52890374875561": "POTW 23 Oct '25", "52890374899136": "POTW 23 Oct '25", "52890643315573": "POTW 30 Oct '25", "52890643338232": "POTW 30 Oct '25", "52891448640608": "POTW National Teams 20 Nov '25", "52891985492393": "POTW 4 Dec '25", "52891985515372": "POTW 4 Dec '25", "52892253946070": "POTW 11 Dec '25", "52892790801832": "POTW 25 Dec '25", "52893059165992": "POTW European Club Championship 25 Sep '25", "52893864488697": "POTW European Club Championship 13 Nov '25", "52893864563704": "POTW European Club Championship 13 Nov '25", "52894132921815": "POTW European Club Championship 4 Dec '25", "52894401343272": "POTW European Club Championship 18 Dec '25", "52894401409216": "POTW European Club Championship 18 Dec '25", "52894669842550": "POTW European Club Championship 29 Jan '26", "52894669845168": "POTW European Club Championship 29 Jan '26", "52894938278468": "POTW European Club Championship 5 Feb '26", "52895206713492": "POTW European Club Championship 26 Feb '26", "52895475160038": "POTW European Club Championship 5 Mar '26", "52897354196134": "POTW 29 Jan '26", "52897622638879": "POTW 5 Feb '26", "52897891077153": "POTW 12 Feb '26", "52898427956609": "POTW 26 Feb '26", "52898696392417": "POTW 5 Mar '26", "52899770137909": "POTW National Teams 2 Apr '26", "52900307009750": "POTW 16 Apr '26", "52900575358760": "POTW 23 Apr '26", "52900575482481": "POTW 23 Apr '26", "52900843893220": "POTW 30 Apr '26", "53982370341557": "POTM Trendyol S�per Lig 19 Mar '26", "53984249311006": "POTM Brasileirão Betano 14 May '26", "55067118012404": "POTS Ligue 1 Uber Eats 23-24", "55067386331226": "POTS English League 23-24", "55067386425959": "POTS English League 23-24", "55067654854885": "POTS Spanish League 23-24", "55068460168376": "POTS English League 24-25", "55068460171551": "POTS English League 24-25", "55068460194657": "POTS English League 24-25", "55068728630326": "POTS Spanish League 24-25", "55068997041878": "POTS Italian League 24-25", "55069802386207": "POTS Italian League 25-26", "55070339270464": "POTS Spanish League 25-26", "55070607581343": "POTS English League 25-26", "55070607587294": "POTS English League 25-26", "55070607651018": "POTS English League 25-26", "55070607666913": "POTS English League 25-26", "55071144547234": "Champions Campaign 25-26 Paris Saint-Germain", "55072486740874": "Champions Campaign 25-26 Paris Saint-Germain", "56161529278248": "POTD International Cup Day 4", "56163408396319": "POTD International Cup Day 12", "56163676848342": "POTD International Cup Day 13", "56163945263719": "POTD International Cup Day 14", "56165287440437": "POTD International Cup Day 20", "56165287449574": "POTD International Cup Day 20", "56166092747440": "POTD International Cup Day 23", "56166092753953": "POTD International Cup Day 23", "56166361188271": "POTD International Cup Day 24", "56167434979136": "POTD International Cup Day 28-29", "56168508708296": "POTD International Cup Day 9", "70374381329569": "Premium Player Pack L. Messi Jun '22", "87962272515241": "Sem box confirmada", "87963346275820": "Sem box confirmada", "87964420017640": "Sem box confirmada", "88029649814697": "Sem box confirmada", "88029649833445": "Sem box confirmada", "88029649833457": "Sem box confirmada", "88029918136423": "Sem box confirmada", "88029918268901": "Sem box confirmada", "88029918268908": "Sem box confirmada", "88029918268912": "Sem box confirmada", "88029918268940": "Sem box confirmada", "88030455139778": "Sem box confirmada", "88030455139826": "Sem box confirmada", "88030723575272": "Sem box confirmada", "88030723578597": "Sem box confirmada", "88030991991977": "Sem box confirmada", "88031797317049": "Sem box confirmada", "88031797317058": "Sem box confirmada", "88031797320416": "Sem box confirmada", "88032334054195": "Sem box confirmada", "88032334055527": "Sem box confirmada", "88032334188018": "Sem box confirmada", "88032334191333": "Sem box confirmada", "88033139360721": "Sem box confirmada", "88033139475625": "Sem box confirmada", "88033139494363": "Sem box confirmada", "88033139494376": "Sem box confirmada", "88033139494412": "Sem box confirmada", "88033139497696": "Sem box confirmada", "88033407804051": "Sem box confirmada", "88033407929785": "Sem box confirmada", "88033407929794": "Sem box confirmada", "88033407929829": "Sem box confirmada", "88033407929836": "Sem box confirmada", "88033407929841": "Sem box confirmada", "88033407929875": "Sem box confirmada", "88033407933157": "Sem box confirmada", "88034213236197": "Germany 1990 feat. Captain Tsubasa", "88035555413480": "Sem box confirmada", "88035555413488": "Sem box confirmada", "88035555416800": "Sem box confirmada", "88035823751192": "Sem box confirmada", "88035823830185": "Sem box confirmada", "88035823848953": "Sem box confirmada", "88036092284396": "Sem box confirmada", "88036360587096": "Sem box confirmada", "88036360587367": "Sem box confirmada", "88036360594067": "Italy 2021", "88036360615426": "Sem box confirmada", "88036360701097": "Sem box confirmada", "88036360719801": "Sem box confirmada", "88036360719848": "Sem box confirmada", "88036360719858": "Sem box confirmada", "88036360719884": "Sem box confirmada", "88036360723168": "Sem box confirmada", "88036360723173": "Sem box confirmada", "88036629155304": "Sem box confirmada", "88036897464767": "Epic Nostalgia 26 Jun '25", "88038776504455": "Sem box confirmada", "88038776505140": "Sem box confirmada", "88038776506699": "Sem box confirmada", "88038776513453": "Sem box confirmada", "88038776537399": "Sem box confirmada", "88038776638902": "Sem box confirmada", "88039044941334": "Sem box confirmada", "88039044973419": "Sem box confirmada", "88039045074370": "Sem box confirmada", "88039045074405": "Sem box confirmada", "88039581810760": "Sem box confirmada", "88039581819327": "Sem box confirmada", "88039581926569": "Sem box confirmada", "88039581945324": "Sem box confirmada", "88039581945329": "Sem box confirmada", "88039581948640": "Sem box confirmada", "88039850247068": "Sem box confirmada", "88039850249642": "Sem box confirmada", "88039850289220": "Sem box confirmada", "88039850362027": "Sem box confirmada", "88039850384095": "Sem box confirmada", "88040387118614": "Sem box confirmada", "88040387119435": "National Teams Selection Guardians 25 May '26", "88040387120361": "Sem box confirmada", "88040387126189": "Sem box confirmada", "88040387150135": "National Teams Selection Guardians 25 May '26", "88040387251641": "Sem box confirmada", "88040387251675": "Sem box confirmada", "88040655558775": "Sem box confirmada", "88040655690467": "Sem box confirmada", "88041460862185": "Sem box confirmada", "88041460901956": "Sem box confirmada", "88041460993474": "Sem box confirmada", "88041460996837": "Sem box confirmada", "88042803041930": "Sem box confirmada", "88044145247083": "Sem box confirmada", "88044145348069": "National Teams Selection 15 Jun '26", "88044145351392": "Sem box confirmada", "89063126342373": "Sem box confirmada", "89063663209957": "Sem box confirmada", "89064736951784": "Sem box confirmada", "89067421306306": "Sem box confirmada", "89070374083541": "Sem box confirmada", "89129966741622": "Sem box confirmada", "89129966765504": "Sem box confirmada", "89131308923305": "Sem box confirmada", "89131577367509": "Sem box confirmada", "89132382592939": "Sem box confirmada", "89135066951464": "Squad Pillars 24-25 Season's Best", "89138019807847": "Sem box confirmada", "89138288270047": "Sem box confirmada", "105559290329771": "Club Selection Manchester B 17 Oct '22", "105585597086633": "Fans' Choice Young Stars 22-23", "105628009878609": "Startup Campaign 7 Sep '23", "105628009888681": "Startup Campaign 7 Sep '23", "105641700078228": "Festive Season Campaign AC Milan 14 Dec '23", "105681428544425": "Mobile 7th Anniversary Celebration", "105701829568955": "Startup Campaign 12 Sep '24", "105717130438001": "Spanish League Selection Guardians 18 Nov '24", "105727867862312": "Mid-season MVPs 9 Jan '25", "105736457823509": "European Clubs Selection Guardians 17 Feb '25", "105751221734082": "The Art of Passing 17 Apr '25", "105752832373838": "Madrid Chamartin B Selection 7 Apr '25", "105783165562137": "Italian League Selection 18 Sep '25", "105785044655466": "Spanish League Selection Guardians 29 Sep '25", "105797124228674": "Brazilian League 2025 Season's Best", "105804103545400": "Arsenal FC Pack 25-26", "105808129996766": "Manchester United Quiz 11 Sep '25", "105811351276226": "European Clubs Selection 1 Dec '25", "105823514770728": "CAF Africa Cup of Nations Selection 11 Dec '25", "105837926463063": "Standout Guardians 25-26 Season's Best", "105848932271764": "National Team Pack Portugal 2026", "105850542865832": "National Team Pack Türkiye 2026", "105851968929064": "National Team Selection Morocco Jun '26", "105852237380941": "National Team Selection Egypt Jun '26", "105868041554130": "National Team Selection Iraq Jun '26", "106653701683166": "Show Time 8 Jun '23", "106725105581480": "Trendyol Süper Lig Selection 7 Mar '24", "106728595255864": "Show Time English League 23-24", "106729132110484": "Show Time Italian League 23-24", "106730205869134": "Show Time Young Stars 23-24 Vol. 2", "106733963950845": "The All-Rounders 26 Dec '24", "106734785968811": "AFC Champions League Elite™ Selection 13 Jan '25", "106743896063272": "European League 24-25 Season's Best", "106759733768760": "Diagonal Long Pass B 6 Nov '25", "106762149661348": "National Teams Selection 6 Nov '25", "106763223418719": "English League Selection 22 Dec '25", "106765454795104": "CAF AFRICA CUP OF NATIONS 25 vol.2", "106766176132585": "American League Selection 17 Nov '25", "106771293270235": "AFC Champions League™ Selection 16 Feb '26", "106772887125793": "FC Barcelona Selection 20 Apr '26", "106774497726444": "Brasileirão Betano Selection 5 Mar '26", "106776645188904": "Standout Guardians 25-26 Season's Best", "106780940156328": "Mobile 9th Anniversary Celebration", "106780940205246": "Mobile 9th Anniversary Celebration", "106787651045215": "Spain 2026", "17592186174377": "Sem box confirmada", "17592186179020": "Sem box confirmada", "52778168793771": "POTW European Club Championship 22 Sep '22", "52783000624617": "POTW 9 Feb '23", "52783537568444": "POTW 23 Feb '23", "52784611254141": "POTW 23 Mar '23", "52787027217090": "POTW 1 Jun '23", "52787564025383": "POTW National Teams 22 Jun '23", "52788906294185": "POTW 31 Aug '23", "52845814528683": "POTW 21 Sep '23", "52851183322921": "POTW European Club Championship 21 Dec '23", "52869973799480": "POTW 2 May '24", "52872121283128": "POTW National Teams 11 Jul '24", "52872658154040": "POTW 22 Aug '24", "52874805637688": "POTW 10 Oct '24", "52875342494461": "POTW National Teams 17 Oct '24", "52877489992248": "POTW 28 Nov '24", "52879100607401": "POTW 26 Dec '24", "52883664008270": "POTW 17 Apr '25", "52884737729905": "POTW European Club Championship 13 Mar '25", "52885006189858": "POTW European Club Championship 20 Mar '25", "52885274606888": "POTW European Club Championship 24 Apr '25", "52887690525992": "POTW Club International Cup 10 Jul '25", "52889032690370": "POTW 18 Sep '25", "52890106442388": "POTW National Teams 16 Oct '25", "52890643316008": "POTW 30 Oct '25", "52891717095666": "POTW 27 Nov '25", "52893596124820": "POTW European Club Championship 30 Oct '25", "52897622656660": "POTW 5 Feb '26", "52898427993278": "POTW 26 Feb '26", "52899233184427": "POTW 19 Mar '26", "52900038544066": "POTW 9 Apr '26", "55068460171452": "POTS English League 24-25", "55068997045101": "POTS Italian League 24-25", "55069802385650": "POTS Italian League 25-26", "55070607703230": "POTS English League 25-26", "56163676849812": "POTD International Cup Day 13", "56163945266472": "POTD International Cup Day 14", "56167971811177": "POTD International Cup Day 31-32", "56168240247352": "POTD International Cup Day 33-34", "87963346275788": "Sem box confirmada", "88029649699702": "Sem box confirmada", "88029649700454": "Sem box confirmada", "88029649833420": "Sem box confirmada", "88029649833432": "Sem box confirmada", "88029918294849": "Sem box confirmada", "88030455139772": "Sem box confirmada", "88030723575244": "Sem box confirmada", "88031797188801": "Sem box confirmada", "88032334059713": "Sem box confirmada", "88033139494348": "Sem box confirmada", "88033139494357": "Sem box confirmada", "88033407796838": "Sem box confirmada", "88033407835625": "Sem box confirmada", "88033407929787": "Sem box confirmada", "88035555285185": "Sem box confirmada", "88035555413452": "Sem box confirmada", "88036360591553": "Sem box confirmada", "88036360719820": "Sem box confirmada", "88037702826110": "Sem box confirmada", "88038776520134": "Sem box confirmada", "88038776567939": "Sem box confirmada", "88039044975272": "Sem box confirmada", "88039045074389": "Sem box confirmada", "88039581945292": "Sem box confirmada", "88039581945304": "Sem box confirmada", "88040387180670": "Sem box confirmada", "88041997764700": "Sem box confirmada", "88042803071068": "Sem box confirmada", "88044145248348": "National Teams Selection 29 Jun '26", "88044145253865": "Sem box confirmada", "88044145277054": "National Teams Selection 13 Jul '26", "88044413760689": "Italy Selection 11 Jun '26", "89073595321804": "Sem box confirmada", "89130772069289": "Sem box confirmada", "89138019804326": "Big Time Internazionale Milano 23 Jan '26", "89138288138433": "Sem box confirmada", "105556337499280": "Liga MX x Day of the Dead 2022", "105627741438140": "Startup Campaign 7 Sep '23", "105629352050876": "Manchester United FC Pack 5 Oct '23", "105658343074253": "BLUE LOCK Collaboration Campaign 21 Mar '24", "105728689936874": "AFC Champions League Elite™ Selection 13 Jan '25", "105729746939740": "Role Changers 13 Feb '25", "105770549094861": "30th Anniversary Elites 10 Jul '25", "105794171419895": "Speedsters 6 Nov '25", "105794171439578": "Speedsters 6 Nov '25", "105799271726109": "Liverpool R Selection 23 Mar '26", "105801150753886": "Chelsea B Selection 18 May '26", "105807593193660": "European Clubs Selection 9 Oct '25", "105828799610127": "Role Changers 5 Mar '26", "105849737554381": "National Team Pack Germany 2026", "105859132806164": "Spain Selection 16 Jul '26", "105863159370023": "National Team Rising Stars 2 Jul '26", "105863159375515": "National Team Rising Stars 2 Jul '26", "106653701749501": "Show Time 8 Jun '23", "106741480139213": "FC Bayern München Selection 15 May '25", "106742553885943": "Long-reach Tackle 1 May '25", "106745775110909": "Summer Transfer 28 Jul '25", "106746580415858": "European Club Championship 24-25 Season's Best", "106758928448759": "Earthmover 27 Oct '25", "106763223432463": "English League Selection 22 Dec '25", "106768323746308": "Trendyol Süper Lig Monthly MVPs Jan '26", "106773423963383": "Standout Midfielders 25-26 Season's Best", "106780940151245": "Mobile 9th Anniversary Celebration", "106783356067329": "Japan Selection 11 Jul '26", "17592186179021": "Sem box confirmada", "52780047903181": "POTW 17 Nov '22", "52787564100349": "POTW National Teams 22 Jun '23", "52853330776672": "POTW 22 Feb '24", "52877489978615": "POTW 28 Nov '24", "52878026838624": "POTW European Club Championship 5 Dec '24", "52880442695351": "POTW European Club Championship 30 Jan '25", "52882858682829": "POTW National Teams 27 Mar '25", "52883932429053": "POTW 24 Apr '25", "52887422102622": "POTW Club International Cup 3 Jul '25", "52888495848719": "POTW 4 Sep '25", "52888764279902": "POTW National Teams 11 Sep '25", "52890106440141": "POTW National Teams 16 Oct '25", "52898159508221": "POTW 19 Feb '26", "52899501729435": "POTW 26 Mar '26", "53978343813402": "POTM Brazilian League 25 Sep '25", "55067386455692": "POTS English League 23-24", "55070339207776": "POTS Spanish League 25-26", "55070607660052": "POTS English League 25-26", "55070607670543": "POTS English League 25-26", "55070876122670": "POTS Trendyol Süper Lig 25-26", "56162871522674": "POTD International Cup Day 10", "56165555880124": "POTD International Cup Day 21", "56166092749498": "POTD International Cup Day 23", "88030455165763": "Sem box confirmada", "88030723575245": "Sem box confirmada", "88030991989501": "Sem box confirmada", "88033407799261": "Sem box confirmada", "88033407929805": "Sem box confirmada", "88033407929867": "Sem box confirmada", "88035555413453": "Sem box confirmada", "88035823874883": "Sem box confirmada", "88039044943837": "Sem box confirmada", "88039044946848": "Sem box confirmada", "88039581945293": "Sem box confirmada", "88040655555524": "Sem box confirmada", "88044145348045": "Sem box confirmada", "89129966675852": "Sem box confirmada", "89130772048333": "Sem box confirmada", "89132651102396": "Sem box confirmada", "105556605970093": "Transfer Oct '22", "105561706239656": "Alltime Greats Nov '22", "105578080877242": "Derby Day London 2 May '23", "105586670814750": "Breakout Stars 6 Jul '23", "105590160400550": "Back in the Game 3 Aug '23", "105625325514975": "English League Selection Midfielders 18 Sep '23", "105625325547356": "English League Selection Midfielders 18 Sep '23", "105628546742970": "New Chapter 5 Oct '23", "105629351978669": "Manchester United FC Pack 5 Oct '23", "105656464045337": "English League Selection 14 Mar '24", "105663711787706": "European Clubs Selection Guardians 22 Apr '24", "105665859194786": "Spanish League Selection Midfielders 27 May '24", "105682502284569": "National Team Pack Argentina '24", "105718204110504": "Miami's Spanish Stars 21 Nov '24", "105730552213727": "National Team Selection Spain 7 Nov '24", "105745316171163": "English League Selection 6 Mar '25", "105751221792344": "The Art of Passing 17 Apr '25", "105756322077129": "National Teams Selection Midfielders 2 Jun '25", "105757664216492": "National Teams Selection European 22 May '25", "105761153855711": "Manchester B Selection 2 Jun '25", "105764375118332": "Club International Cup Selection 12 Jun '25", "105768133195033": "National Teams Selection 17 Jul '25", "105768938500737": "Borussia Dortmund Selection 24 Jul '25", "105770817554469": "Champions Campaign 24-25 FC Barcelona", "105775380957221": "Lamine Yamal Edition 2026", "105779675902175": "Back in the Game 14 Aug '25", "105780481240924": "Chelsea B Selection 18 Aug '25", "105785849948268": "National Teams Selection Guardians 6 Oct '25", "105792023949405": "PFA Awards 2025", "105794708285855": "Mid-season MVPs 8 Jan '26", "105794708320092": "Mid-season MVPs 8 Jan '26", "105799271706717": "Liverpool R Selection 23 Mar '26", "105800077013402": "Piemonte BN Selection 29 Dec '25", "105800613910395": "National Team Selection Worldwide 30 Apr '26", "105801150771036": "Chelsea B Selection 18 May '26", "105802224521791": "English League Selection 5 Feb '26", "105802492952578": "National Teams Selection 8 Jan '26", "105803029789370": "European Clubs Selection 13 Nov '25", "105804103548058": "Arsenal FC Pack 25-26", "105804371954409": "Internazionale Milano Pack 25-26", "105804371956998": "Internazionale Milano Pack 25-26", "105805982613506": "Earthmover 27 Oct '25", "105806787889465": "European Clubs Selection Guardians 3 Nov '25", "105820478139412": "European Clubs Selection 15 Jan '26", "105829336478106": "Elite Lineage 30 Apr '26", "105829873332447": "National Team Icons vol.2", "105837658021466": "FC Barcelona Selection 20 Apr '26", "105848932274075": "National Team Pack Portugal 2026", "105848932298328": "National Team Pack Portugal 2026", "105849469111254": "National Team Pack France 2026", "105850006007901": "National Team Pack Netherlands 2026", "105850542852841": "National Team Pack Türkiye 2026", "105850811304249": "National Team Selection Brazil Jun '26", "105852237395400": "National Team Selection Egypt Jun '26", "105852237421001": "National Team Selection Egypt Jun '26", "105852690280748": "The Football Festival Campaign 2026", "105854569391823": "Spain 2026", "105854837836653": "Tournament Stars 2026", "105855374705614": "Japan Selection 2 Jul '26", "105856716875181": "Italy Selection 11 Jun '26", "105857522208638": "Brazil Selection 25 Jun '26", "105858059077036": "Germany Selection 2 Jul '26", "105858864355084": "National Teams Selection 13 Jul '26", "105860290356815": "National Team Selection Senegal Jun '26", "105860290430931": "National Team Selection Senegal Jun '26", "105860558860253": "National Team Selection Algeria Jun '26", "105860558880165": "National Team Selection Algeria Jun '26", "105867773082911": "National Team Selection Korea Republic Jun '26", "106653433237410": "Show Time 18 May '23", "106653433246643": "Show Time 18 May '23", "106654238617823": "Show Time European Club Championship 22-23", "106722421241113": "National Teams Selection Midfielders 16 Nov '23", "106727253055244": "Daily Bonus", "106727521423266": "Show Time European Club Tournaments 23-24", "106727789935290": "Show Time Ligue 1 Uber Eats 23-24", "106730474235970": "Show Time eFootball™ Festival 2024", "106732621770975": "World Player of the Year 2024", "106735843042971": "New Year's Gift 1 Jan '25", "106736916728790": "Daily Bonus", "106737722037510": "National Teams Selection Attackers 13 Mar '25", "106738258921279": "National Teams Selection Guardians 20 Mar '25", "106741211703711": "Towering Giants 29 May '25", "106743359205469": "English League 24-25 Season's Best", "106745775115778": "Summer Transfer 28 Jul '25", "106747922604897": "Daily Bonus 2026", "106748459487131": "National Team Selection Portugal 4 Aug '25", "106750070068486": "Over-the-Top Pass A 4 Sep '25", "106750875381983": "Over-the-Top Pass B 2 Oct '25", "106752754353458": "Show Time 7 Jun '25", "106758173423636": "National Team Selection Indonesia 2 Oct '25", "106758928478044": "Earthmover 27 Oct '25", "106759465365080": "Rising Prodigies 15 Sep '25", "106760002235412": "Manchester United Selection 16 Feb '26", "106761881282574": "National Teams Selection Southeast Asia 27 Nov '25", "106761881289891": "National Teams Selection Southeast Asia 27 Nov '25", "106762149600615": "National Teams Selection 6 Nov '25", "106762955019322": "Japanese Stars 6 Apr '26", "106763760282015": "Central Dominator 5 Jan '26", "106764565597595": "eFootball™ League Rewards Phase 5", "106765454779807": "CAF AFRICA CUP OF NATIONS 25 vol.2", "106765907789861": "Magnetic Feet 29 Jan '26", "106770739623193": "Breakthrough Pass B 12 Mar '26", "106771008054113": "Trendyol Süper Lig Monthly MVPs Feb '26", "106772618646508": "Arsenal FC Selection 21 May '26", "106773423990288": "Standout Midfielders 25-26 Season's Best", "106773960836927": "National Teams Campaign Mar '26", "106778524258203": "European Club Championship 25-26 Season's Best", "106779061095382": "Trendyol Süper Lig Monthly MVPs Apr '26", "106781477040769": "International Cup vol.1", "106782013927260": "International Cup vol.3", "106783087654662": "Japan Selection 2 Jul '26", "106784698181293": "Highlight May '26", "106785503488127": "The Football Festival Campaign 2026", "17592186045282": "Sem box confirmada", "17592186179005": "Sem box confirmada", "17592186179040": "Sem box confirmada", "17592186182370": "Sem box confirmada", "17592454614461": "Sem box confirmada", "17592454614496": "Sem box confirmada", "17592723049952": "Sem box confirmada", "52781658441010": "POTW International Cup 22 Dec '22", "52782463750050": "POTW 26 Jan '23", "52783269130463": "POTW 16 Feb '23", "52784611304863": "POTW 23 Mar '23", "52785148186011": "POTW 6 Apr '23", "52787564047456": "POTW National Teams 22 Jun '23", "52845814585122": "POTW 21 Sep '23", "52847693630185": "POTW 26 Oct '23", "52851720171743": "POTW 11 Jan '24", "52852525404066": "POTW 1 Feb '24", "52853062347167": "POTW 15 Feb '24", "52869436927989": "POTW 25 Apr '24", "52871047450530": "POTW 30 May '24", "52871315950550": "POTW National Teams 20 Jun '24", "52872121259197": "POTW National Teams 11 Jul '24", "52873463441823": "POTW 12 Sep '24", "52875074062143": "POTW European Club Championship 10 Oct '24", "52878026852159": "POTW European Club Championship 5 Dec '24", "52878832159597": "POTW European Club Championship 19 Dec '24", "52880174337435": "POTW 30 Jan '25", "52881784866098": "POTW 27 Feb '25", "52883663993530": "POTW 17 Apr '25", "52885274601887": "POTW European Club Championship 24 Apr '25", "52885543061541": "POTW 1 May '25", "52887422135896": "POTW Club International Cup 3 Jul '25", "52888227410013": "POTW 28 Aug '25", "52888227416101": "POTW 28 Aug '25", "52888495877720": "POTW 4 Sep '25", "52889032719514": "POTW 18 Sep '25", "52889301151837": "POTW 25 Sep '25", "52889838004639": "POTW 9 Oct '25", "52889838038876": "POTW 9 Oct '25", "52890374870278": "POTW 23 Oct '25", "52890911746463": "POTW 6 Nov '25", "52891180208027": "POTW 13 Nov '25", "52891448626690": "POTW National Teams 20 Nov '25", "52891448667736": "POTW National Teams 20 Nov '25", "52893059291530": "POTW European Club Championship 25 Sep '25", "52893596119681": "POTW European Club Championship 30 Oct '25", "52894132979581": "POTW European Club Championship 4 Dec '25", "52894132998043": "POTW European Club Championship 4 Dec '25", "52894669861274": "POTW European Club Championship 29 Jan '26", "52896280489452": "POTW European Club Championship 23 Apr '26", "52897622566573": "POTW 5 Feb '26", "52898159428914": "POTW 19 Feb '26", "52898964834341": "POTW 12 Mar '26", "52899233278218": "POTW 19 Mar '26", "52899770125723": "POTW National Teams 2 Apr '26", "52899770125826": "POTW National Teams 2 Apr '26", "52900038544105": "POTW 9 Apr '26", "52900306979798": "POTW 16 Apr '26", "52900575417606": "POTW 23 Apr '26", "52901649165284": "POTW 28 May '26", "55067386425567": "POTS English League 23-24", "55067923286761": "POTS Italian League 23-24", "55067923312181": "POTS Italian League 23-24", "55068460158191": "POTS English League 24-25", "55070607657273": "POTS English League 25-26", "55070607683713": "POTS English League 25-26", "56161797802021": "POTD International Cup Day 5", "56162334699096": "POTD International Cup Day 7", "56162603118247": "POTD International Cup Day 8", "56162955404703": "POTD International Cup Day 10", "56164213731164": "POTD International Cup Day 15", "56164750599696": "POTD International Cup Day 17", "56166361204716": "POTD International Cup Day 24", "56167434921679": "POTD International Cup Day 28-29", "56167971795167": "POTD International Cup Day 31-32", "56168240228767": "POTD International Cup Day 33-34", "87962272400283": "Sem box confirmada", "87962272533984": "Sem box confirmada", "87963077840381": "Sem box confirmada", "87963346275808": "Sem box confirmada", "87963614577617": "Sem box confirmada", "88029649699741": "Sem box confirmada", "88029649833464": "Sem box confirmada", "88029649836770": "Sem box confirmada", "88029918172866": "Sem box confirmada", "88029918268852": "Sem box confirmada", "88029918268861": "Sem box confirmada", "88029918268896": "Sem box confirmada", "88029918268922": "Sem box confirmada", "88030723575218": "Sem box confirmada", "88030723575220": "Sem box confirmada", "88030723578594": "Sem box confirmada", "88030992010749": "Sem box confirmada", "88031797183387": "Sem box confirmada", "88031797183431": "Sem box confirmada", "88032065619658": "Sem box confirmada", "88032065623324": "Sem box confirmada", "88032065752498": "Sem box confirmada", "88032065752544": "Sem box confirmada", "88032065752573": "Sem box confirmada", "88032065755874": "Sem box confirmada", "88032334187959": "Sem box confirmada", "88033139360610": "Sem box confirmada", "88033139360669": "Sem box confirmada", "88033139494333": "Sem box confirmada", "88033139494394": "Sem box confirmada", "88033139494397": "Sem box confirmada", "88033407796123": "Sem box confirmada", "88033407796167": "Sem box confirmada", "88033407796938": "Sem box confirmada", "88033407833768": "Sem box confirmada", "88033407833794": "Sem box confirmada", "88033407929780": "Sem box confirmada", "88033407929824": "Sem box confirmada", "88035555342464": "Sem box confirmada", "88035555413425": "Sem box confirmada", "88035555413426": "Sem box confirmada", "88035555413472": "Sem box confirmada", "88035555413477": "Sem box confirmada", "88035555413501": "Sem box confirmada", "88035823744514": "Sem box confirmada", "88036092150683": "Sem box confirmada", "88036092284349": "Sem box confirmada", "88036360586141": "Sem box confirmada", "88036360648832": "Sem box confirmada", "88036360719793": "Sem box confirmada", "88036360719796": "Sem box confirmada", "88036360723170": "Sem box confirmada", "88038776506440": "Sem box confirmada", "88039044941514": "Sem box confirmada", "88039044945180": "Sem box confirmada", "88039045074354": "Sem box confirmada", "88039045074359": "Sem box confirmada", "88039581811611": "Sem box confirmada", "88039581811655": "Sem box confirmada", "88039581811665": "Sem box confirmada", "88039581945277": "Sem box confirmada", "88039581945312": "Sem box confirmada", "88039581945332": "Sem box confirmada", "88039581948642": "Sem box confirmada", "88039850287270": "Sem box confirmada", "88040118816667": "World Player of the Year 2025", "88040387117922": "Sem box confirmada", "88040387147266": "Maestro 13 Apr '26", "88040387158182": "Maestro 13 Apr '26", "88040387180672": "Sem box confirmada", "88040387251639": "Sem box confirmada", "88040387251709": "Maestro 13 Apr '26", "88041460859805": "Sem box confirmada", "88042803039763": "Sem box confirmada", "88044145214363": "National Teams Selection 6 Jul '26", "88044145348017": "National Teams Selection 8 Jun '26", "88044145348020": "Sem box confirmada", "88044145348028": "National Teams Selection 6 Jul '26", "88044145348029": "Sem box confirmada", "88044145348064": "Italy Selection 11 Jun '26", "88044413653830": "National Teams Selection 13 Jul '26", "89064200084194": "Sem box confirmada", "89065005387197": "Sem box confirmada", "89065273822644": "Sem box confirmada", "89071447742146": "Sem box confirmada", "89071984709041": "Sem box confirmada", "89132651028391": "Sem box confirmada", "89132651030189": "Sem box confirmada", "89135067023229": "Big Time 14 Apr '25", "89135067039781": "Big Time 11 May '25", "89138019805599": "Big Time Arsenal FC 3 Jan '26", "89138019820385": "Big Time Beşiktaş JK 19 Mar '26", "89138556678367": "Big Time Spain 19 Jul '26", "105557679802405": "Club Pack FC Barcelona Oct '22", "105561169438272": "National Team Selection Italy [Deluxe] Nov '22", "105569222527013": "Mid-season MVPs Jan '23", "105574591216887": "Derby Day Classic 19 Mar '23", "105579959916322": "End-season MVPs 11 May '23", "105585060089833": "J.LEAGUE Monthly MVPs May '23", "105590428927813": "Club Selection Madrid Chamartin B 7 Aug '23", "105592844822968": "Summer Transfer 3 Aug '23", "105593113252860": "Summer Transfer 10 Aug '23", "105593113267536": "Summer Transfer 10 Aug '23", "105621835876389": "Leo Messi Edition '23", "105628009896720": "Startup Campaign 7 Sep '23", "105628546762565": "New Chapter 5 Oct '23", "105632304859173": "Spanish League Selection Midfielders 30 Oct '23", "105639552527707": "Club Icons 7 Dec '23", "105639552601681": "Club Icons 7 Dec '23", "105640626339188": "English League Selection 14 Dec '23", "105647874029000": "English League Selection Midfielders 15 Jan '24", "105653511161138": "Spanish League Selection Midfielders 22 Jan '24", "105655658655067": "National Teams Selection Attackers 18 Mar '24", "105655927160055": "Spanish League Selection 14 Mar '24", "105658074590304": "BLUE LOCK Collaboration Campaign 21 Mar '24", "105664248648684": "Classic No. 10 Players 21 Mar '24", "105666127707508": "European Clubs Selection Attackers 20 May '24", "105681428448562": "Mobile 7th Anniversary Celebration", "105683039142008": "National Team Pack England '24", "105683039160133": "National Team Pack England '24", "105684381248859": "National Teams Selection European 13 Jun '24", "105685186641167": "National Teams Selection Midfielders 17 Jun '24", "105695387172984": "Welcome Login Bonus", "105697803124515": "Back in the Game 8 Aug '24", "105702098082576": "FC Bayern München Selection 16 Sep '24", "105703440166235": "777 Million Downloads Campaign", "105705050869659": "Magical Dribbler 12 Sep '24", "105706124609573": "Spanish League Selection 19 Sep '24", "105708808891488": "Manchester United Pack 16 Jan '25", "105727867881509": "Mid-season MVPs 9 Jan '25", "105729478491407": "English League Selection Midfielders 27 Jan '25", "105738873636146": "Pride of the Club 20 Mar '25", "105744510893859": "Spanish League Selection Midfielders 10 Mar '25", "105745316097371": "English League Selection 6 Mar '25", "105750684877018": "English League Selection 24 Apr '25", "105752563913708": "National Team Pack Norway '25", "105752832378693": "Madrid Chamartin B Selection 7 Apr '25", "105756053604165": "Elite Lineage 15 May '25", "105763569793369": "Champions Campaign 24-25 FC Bayern München", "105763569802000": "Champions Campaign 24-25 FC Bayern München", "105768133204752": "National Teams Selection 17 Jul '25", "105779944357135": "English League Selection 21 Aug '25", "105788265861019": "Squad Pillars 24-25 Season's Best", "105789876442092": "Arsenal FC Partnership Campaign 7 Aug '25", "105799003189215": "AS Monaco Selection 20 Apr '26", "105801687651660": "Spanish League Selection 2 Apr '26", "105801956089422": "Italian League Selection 5 Mar '26", "105802224484472": "English League Selection 5 Feb '26", "105802492839218": "National Teams Selection 8 Jan '26", "105802761382154": "Young Stars 11 Dec '25", "105804103532762": "Arsenal FC Pack 25-26", "105804640349696": "Borussia Dortmund Pack 25-26", "105804908784736": "Manchester United Pack 25-26", "105805445742371": "900 Million Downloads Campaign", "105823514802387": "CAF Africa Cup of Nations Selection 11 Dec '25", "105829604830555": "National Team Icons vol.1", "105829873263213": "National Team Icons vol.2", "105833094568552": "National Teams Selection Midfielders 30 Mar '26", "105838194766453": "National Teams Selection Attackers 27 Apr '26", "105846784808268": "Spanish League 25-26 Season's Best", "105848932199520": "National Team Pack Portugal 2026", "105849200707397": "National Team Pack England 2026", "105850274443253": "National Team Selection Japan Jun '26", "105850542893322": "National Team Pack Türkiye 2026", "105851968956572": "National Team Selection Morocco Jun '26", "105852237358172": "National Team Selection Egypt Jun '26", "105852237410755": "National Team Selection Egypt Jun '26", "105852958832396": "The Football Festival Campaign 2026", "105854569418342": "Spain 2026", "105858059077471": "Germany Selection 2 Jul '26", "105859132833571": "Spain Selection 16 Jul '26", "105860558923477": "National Team Selection Algeria Jun '26", "105863159356176": "National Team Rising Stars 2 Jul '26", "105863159384430": "National Team Rising Stars 2 Jul '26", "106653433261152": "Show Time Rewards 18 May '23", "106653433333573": "Show Time 18 May '23", "106654507051839": "Show Time Italian League 22-23", "106655312282930": "Show Time 27 Jul '23", "106655312293211": "Show Time 27 Jul '23", "106722958116677": "Spanish League Selection Attackers 27 Nov '23", "106726447777829": "Show Time 13 Jun '24", "106728863677687": "Show Time Spanish League 23-24", "106728863696709": "Show Time Spanish League 23-24", "106729400572844": "Show Time Young Stars 23-24 Vol. 1", "106730474291018": "Show Time eFootball™ Festival 2024", "106731547959917": "Show Time Continental Tournaments '24", "106732084936483": "Hard-working Players 3 Oct '24", "106732621793093": "World Player of the Year 2024", "106733963948084": "The All-Rounders 26 Dec '24", "106741480168208": "FC Bayern München Selection 15 May '25", "106741748591999": "Trendyol Süper Lig Selection 15 May '25", "106742017012542": "Brazilian League Selection 1 May '25", "106743090687323": "Offensive Genius 24 Apr '25", "106743896078681": "European League 24-25 Season's Best", "106746580456800": "European Club Championship 24-25 Season's Best", "106747167662741": "National Team Selection Indonesia 22 May '25", "106747385740559": "Show Time [8 Anniv.]", "106749264818797": "Club International Cup Campaign 12 Jun '25", "106752486016837": "Squad Pillars 24-25 Season's Best", "106753291337609": "Borussia Dortmund Selection 26 Jul '25", "106753559668284": "eFootball™ League Rewards Phase 1", "106755438720293": "Brazilian League Selection 25 Sep '25", "106755975663185": "Brazilian League Selection 27 Nov '25", "106762149664546": "National Teams Selection 6 Nov '25", "106764028750090": "Breakthrough Pass A 8 Jan '26", "106765186342826": "CAF AFRICA CUP OF NATIONS 25 vol.1", "106765907771610": "Magnetic Feet 29 Jan '26", "106765907789637": "Magnetic Feet 29 Jan '26", "106766981442907": "New Year's Gift 2026", "106767518381244": "Battle for the Show Time", "106768592071776": "Attack Trigger 19 Feb '26", "106769129043724": "eFootball™ League Rewards Phase 8", "106772350211068": "Trendyol Süper Lig Monthly MVPs Mar '26", "106773155552016": "1-2 Cut-in A 23 Apr '26", "106777181979954": "Italian League 25-26 Season's Best", "106777182101070": "Italian League 25-26 Season's Best", "106778792700170": "National Team Selection T�rkiye 23 Mar '26", "106779597968380": "Trendyol Süper Lig 25-26 Season's Best", "106782550787909": "International Cup vol.5", "106783087652853": "Japan Selection 2 Jul '26", "17592186048489": "Sem box confirmada", "17592186178992": "Sem box confirmada", "17592186178993": "Sem box confirmada", "17592186179036": "Sem box confirmada", "17592186179050": "Sem box confirmada", "17592454483945": "Sem box confirmada", "17592454614449": "Sem box confirmada", "17592454614506": "Sem box confirmada", "52777095067617": "POTW 1 Sep '22", "52777631993516": "POTW 15 Sep '22", "52780316362565": "POTW International Cup 28 Nov '22", "52780584725600": "POTW International Cup 1 Dec '22", "52781658444018": "POTW International Cup 22 Dec '22", "52781658453914": "POTW International Cup 22 Dec '22", "52781926875605": "POTW 12 Jan '23", "52783000685289": "POTW 9 Feb '23", "52783269152805": "POTW 16 Feb '23", "52783537501640": "POTW 23 Feb '23", "52783806005368": "POTW 2 Mar '23", "52785416618202": "POTW 13 Apr '23", "52786490360026": "POTW 18 May '23", "52787027254032": "POTW 1 Jun '23", "52787295585287": "POTW 8 Jun '23", "52788369426245": "POTW 17 Aug '23", "52848230532933": "POTW 2 Nov '23", "52848498973456": "POTW European Club Championship 2 Nov '23", "52849304184140": "POTW European Club Championship 16 Nov '23", "52851451685713": "POTW 28 Dec '23", "52851988540763": "POTW 18 Jan '24", "52853062371141": "POTW 15 Feb '24", "52853330777068": "POTW 22 Feb '24", "52853867588955": "POTW European Club Championship 29 Feb '24", "52853867677733": "POTW European Club Championship 29 Feb '24", "52867826326288": "POTW 21 Mar '24", "52868899976648": "POTW 11 Apr '24", "52869436915930": "POTW 25 Apr '24", "52869705350391": "POTW European Club Championship 25 Apr '24", "52870779111461": "POTW 23 May '24", "52871047474272": "POTW 30 May '24", "52871315987216": "POTW National Teams 20 Jun '24", "52871584326253": "POTW National Teams 27 Jun '24", "52871584329051": "POTW National Teams 27 Jun '24", "52871852853061": "POTW National Teams 4 Jul '24", "52873463366962": "POTW 12 Sep '24", "52873463470864": "POTW 12 Sep '24", "52875610963747": "POTW 24 Oct '24", "52877221562181": "POTW National Teams 21 Nov '24", "52878295309072": "POTW 12 Dec '24", "52878295312650": "POTW 12 Dec '24", "52879100607759": "POTW 26 Dec '24", "52879369045829": "POTW 9 Jan '25", "52879905898616": "POTW 23 Jan '25", "52880442758124": "POTW European Club Championship 30 Jan '25", "52880711223333": "POTW 6 Feb '25", "52882858703193": "POTW National Teams 27 Mar '25", "52883395582736": "POTW 10 Apr '25", "52883663924571": "POTW 17 Apr '25", "52884200880473": "POTW European Club Championship 20 Feb '25", "52884200886171": "POTW European Club Championship 20 Feb '25", "52885543057753": "POTW 1 May '25", "52886885243664": "POTW Club International Cup 19 Jun '25", "52888495859978": "POTW 4 Sep '25", "52888764198235": "POTW National Teams 11 Sep '25", "52889032623410": "POTW 18 Sep '25", "52889032750860": "POTW 18 Sep '25", "52889301085280": "POTW 25 Sep '25", "52890374921806": "POTW 23 Oct '25", "52890643316954": "POTW 30 Oct '25", "52890643343516": "POTW 30 Oct '25", "52890911684878": "POTW 6 Nov '25", "52891180246741": "POTW 13 Nov '25", "52891716988895": "POTW 27 Nov '25", "52891717047292": "POTW 27 Nov '25", "52891717058778": "POTW 27 Nov '25", "52892790818629": "POTW 25 Dec '25", "52893059235960": "POTW European Club Championship 25 Sep '25", "52893596124997": "POTW European Club Championship 30 Oct '25", "52893596153612": "POTW European Club Championship 30 Oct '25", "52893864542328": "POTW European Club Championship 13 Nov '25", "52894938283850": "POTW European Club Championship 5 Feb '26", "52898427945178": "POTW 26 Feb '26", "52898696326240": "POTW 5 Mar '26", "52899501687031": "POTW 26 Mar '26", "52900575428855": "POTW 23 Apr '26", "52900843793755": "POTW 30 Apr '26", "52900843910924": "POTW 30 Apr '26", "52901380680800": "POTW 21 May '26", "52901649159970": "POTW 28 May '26", "53967337854719": "POTM Liga BBVA MX 11 Apr '24", "55068460117088": "POTS English League 24-25", "55068728534588": "POTS Spanish League 24-25", "55068728625084": "POTS Spanish League 24-25", "55070339215207": "POTS Spanish League 25-26", "55070607716019": "POTS English League 25-26", "55071949764878": "Champions Campaign 25-26 Internazionale Milano", "56161797829059": "POTD International Cup Day 5", "56162334672709": "POTD International Cup Day 7", "56162603149423": "POTD International Cup Day 8", "56163408385004": "POTD International Cup Day 12", "56164482158182": "POTD International Cup Day 16", "56164482165002": "POTD International Cup Day 16", "56164750503259": "POTD International Cup Day 17", "56166629640005": "POTD International Cup Day 25", "70377334146354": "European Club Championship 16 Jun '22", "87960930356724": "Sem box confirmada", "87962272533982": "Sem box confirmada", "87962272534003": "Sem box confirmada", "87962272534031": "Sem box confirmada", "87963077709801": "Sem box confirmada", "87963077840306": "Sem box confirmada", "87963346275818": "Sem box confirmada", "87963883146670": "Sem box confirmada", "87964151582174": "Sem box confirmada", "88029649703734": "Sem box confirmada", "88029649833393": "Sem box confirmada", "88029918135138": "Sem box confirmada", "88029918268869": "Sem box confirmada", "88029918268906": "Sem box confirmada", "88029918268927": "Sem box confirmada", "88029918268943": "Sem box confirmada", "88030455062283": "Sem box confirmada", "88030455139768": "Sem box confirmada", "88030992010693": "Sem box confirmada", "88031797186537": "Sem box confirmada", "88032065618786": "Sem box confirmada", "88032065752497": "Sem box confirmada", "88032334053428": "Sem box confirmada", "88032334187974": "Sem box confirmada", "88032334188031": "Sem box confirmada", "88032334191325": "Sem box confirmada", "88033139363817": "Sem box confirmada", "88033139494321": "Sem box confirmada", "88033139494364": "Sem box confirmada", "88033139494378": "Sem box confirmada", "88033407810520": "Sem box confirmada", "88033407929774": "Sem box confirmada", "88033407929797": "Sem box confirmada", "88033407929815": "Sem box confirmada", "88033407929871": "Sem box confirmada", "88033407955778": "Sem box confirmada", "88033407967737": "Sem box confirmada", "88035555279078": "Sem box confirmada", "88035555283766": "Sem box confirmada", "88035555285997": "Sem box confirmada", "88035555413482": "Sem box confirmada", "88035823718377": "Sem box confirmada", "88035823729624": "Sem box confirmada", "88035823848901": "Sem box confirmada", "88035823848926": "Sem box confirmada", "88035823852253": "Sem box confirmada", "88036360585379": "Sem box confirmada", "88036360589289": "Sem box confirmada", "88036360590134": "Sem box confirmada", "88036360719836": "Sem box confirmada", "88036360719887": "Sem box confirmada", "88039044970281": "Sem box confirmada", "88039045074350": "Sem box confirmada", "88039045074373": "Sem box confirmada", "88039045074374": "Sem box confirmada", "88039045074410": "Sem box confirmada", "88039045077725": "Sem box confirmada", "88039581945303": "Sem box confirmada", "88040387121129": "Sem box confirmada", "88040387121974": "Sem box confirmada", "88040387251676": "Sem box confirmada", "88040387251711": "Sem box confirmada", "88041460859043": "Sem box confirmada", "88041460915979": "Sem box confirmada", "88041460993477": "Sem box confirmada", "88041460993495": "Sem box confirmada", "88041460993514": "Sem box confirmada", "89066615870262": "Sem box confirmada", "89068763496227": "Sem box confirmada", "89071716139171": "Sem box confirmada", "89072790015452": "Sem box confirmada", "89130235068579": "Sem box confirmada", "89130503504035": "Sem box confirmada", "89130772077328": "Sem box confirmada", "89131845789248": "Sem box confirmada", "89132382653161": "Sem box confirmada", "89138019757152": "Big Time Manchester United 7 Feb '26", "89138288136169": "Sem box confirmada", "105556605974603": "Transfer Oct '22", "105561706241802": "Alltime Greats Nov '22", "105568417094999": "Shining Stars 26 Dec '22", "105570833043590": "eFootball™ Point Rewards Vol.5", "105571906874752": "Transfer Feb '23", "105630694238119": "European Clubs Selection Attackers 16 Oct '23", "105633915462473": "Golden Boys 2 Nov '23", "105639552543719": "Club Icons 7 Dec '23", "105642505315660": "Mid-season MVPs 4 Jan '24", "105657269264138": "BLUE LOCK Collaboration Campaign 21 Mar '24", "105679817923720": "Speedsters 9 May '24", "105684381342404": "National Teams Selection European 13 Jun '24", "105724109798480": "National Teams Selection Worldwide 12 Dec '24", "105727867886508": "Mid-season MVPs 9 Jan '25", "105729746908648": "Role Changers 13 Feb '25", "105737799900226": "European Clubs Selection 27 Feb '25", "105739158855570": "AFC Champions League™ Selection 20 Mar '25", "105749074287300": "Bayer 04 Leverkusen Selection 20 Feb '25", "105754979871496": "Winter Transfer 3 Mar '25", "105761959189420": "Chelsea B Selection 5 May '25", "105764375012684": "Club International Cup Selection 12 Jun '25", "105765985721028": "European League 24-25 Season's Best", "105779675838539": "Back in the Game 14 Aug '25", "105779944341322": "English League Selection 21 Aug '25", "105780749658023": "Summer Transfer 14 Aug '25", "105790681755700": "World Player of the Year 2025", "105793902985437": "Newly Licensed Italian Clubs 9 Oct '25", "105794439861140": "Clutch Players 4 Dec '25", "105799003292364": "AS Monaco Selection 20 Apr '26", "105799271717572": "Liverpool R Selection 23 Mar '26", "105799808584213": "Manchester B Selection 26 Jan '26", "105800345448096": "Madrid Rosas RB Selection 1 Dec '25", "105802492916022": "National Teams Selection 8 Jan '26", "105802761367501": "Young Stars 11 Dec '25", "105804640433206": "Borussia Dortmund Pack 25-26", "105804908843755": "Manchester United Pack 25-26", "105804908846557": "Manchester United Pack 25-26", "105804908857901": "Manchester United Pack 25-26", "105805714141236": "FC Barcelona Pack 25-26", "105826920468722": "Worldwide Clubs Selection 12 Feb '26", "105829068034795": "Magical Dribbler 2 Apr '26", "105829336503648": "Elite Lineage 30 Apr '26", "105830678654925": "Signature Goal Celebrations 5 Feb '26", "105830678666156": "Signature Goal Celebrations 5 Feb '26", "105833648221568": "AFC Champions League™ Selection 19 Feb '26", "105837121021260": "European Clubs Selection 16 Apr '26", "105840610761736": "NARUTO SHIPPUDEN Collaboration Campaign 2026", "105849469139289": "National Team Pack France 2026", "105849469143573": "National Team Pack France 2026", "105849737559882": "National Team Pack Germany 2026", "105849737583300": "National Team Pack Germany 2026", "105850542916637": "National Team Pack Türkiye 2026", "105850811297844": "National Team Selection Brazil Jun '26", "105851968929670": "National Team Selection Morocco Jun '26", "105855374711653": "Japan Selection 2 Jul '26", "105867773079001": "National Team Selection Korea Republic Jun '26", "106652627934624": "Show Time Rewards 2 Mar '23", "106731279490391": "Skill Up", "106735037705888": "Offensive Genius 17 Oct '24", "106735037717188": "Offensive Genius 17 Oct '24", "106735306076245": "Brazilian League 2024 Season's Best", "106738527300583": "Trendyol Süper Lig Selection 27 Mar '25", "106738795813804": "Standout Lefties 3 Feb '25", "106743627624500": "Spanish League 24-25 Season's Best", "106744432971741": "Brazilian League Selection 26 Jun '25", "106745238268680": "Breakout Stars 24-25 Season's Best", "106745506689835": "Club International Cup 2025", "106745775135428": "Summer Transfer 28 Jul '25", "106746043541825": "Brazilian League Selection 24 Jul '25", "106746899117047": "AFC Asian Qualifiers™ Selection 22 May '25", "106747167629241": "National Team Selection Indonesia 22 May '25", "106749264804803": "Club International Cup Campaign 12 Jun '25", "106749533208454": "Diagonal Long Pass A 15 Aug '25", "106749801654633": "J.LEAGUE Monthly MVPs Jul '25", "106755438714272": "Brazilian League Selection 25 Sep '25", "106756244131805": "Brazilian League 2025 Season's Best", "106756512476135": "Trendyol Süper Lig Monthly MVPs Aug '25", "106756780911591": "Trendyol Süper Lig Monthly MVPs Sep '25", "106757586221077": "Trendyol Süper Lig Monthly MVPs Dec '25", "106757586263695": "Trendyol Süper Lig Monthly MVPs Dec '25", "106759196889835": "Anticipated Standouts 13 Oct '25", "106759465339413": "Rising Prodigies 15 Sep '25", "106760002199005": "Manchester United Selection 16 Feb '26", "106761092722444": "AFC Champions League Elite™ Selection 20 Oct '25", "106762954972673": "Japanese Stars 6 Apr '26", "106763760299981": "Central Dominator 5 Jan '26", "106764917911559": "Best Players of CAF AFRICA CUP OF NATIONS 25", "106765186350982": "CAF AFRICA CUP OF NATIONS 25 vol.1", "106765639374176": "Daily Bonus 2026", "106766444574903": "Extraordinary One 4 Dec '25", "106766444664616": "Extraordinary One 4 Dec '25", "106767786806011": "eFootball™ League Rewards Phase 6", "106770471099808": "Campaign Rewards Feb '26", "106770471185881": "Campaign Rewards Feb '26", "106770739621536": "Breakthrough Pass B 12 Mar '26", "106773960831286": "National Teams Campaign Mar '26", "106774766072775": "Brasileirão Betano Selection 9 Apr '26", "106775303019476": "J.LEAGUE Monthly MVPs Feb '26", "106775571439108": "J.LEAGUE Monthly MVPs Mar '26", "106776376765788": "Ligue 1 McDonald’s Selection 2 Mar '26", "106778792723485": "National Team Selection T�rkiye 23 Mar '26", "106779061103582": "Trendyol Süper Lig Monthly MVPs Apr '26", "106779329535631": "Trendyol Süper Lig Monthly MVPs May '26", "106779866307927": "The Football Festival Campaign 2026", "106780403293192": "The Football Festival Campaign 2026", "106781476920663": "International Cup vol.1", "106781745473447": "International Cup vol.2", "106782013903764": "International Cup vol.3", "106782550788446": "International Cup vol.5", "106782819217056": "International Cup vol.6", "106783087647748": "Japan Selection 2 Jul '26", "106783356083208": "Japan Selection 11 Jul '26", "106784161310028": "Show Time 9 May '26", "106787651039542": "Spain 2026", "123236838841410": "Strike Arena", "17592186048174": "Sem box confirmada", "17592186051927": "Sem box confirmada", "17592186084768": "Sem box confirmada", "17592186178997": "Sem box confirmada", "17592186179013": "Sem box confirmada", "17592186179024": "Sem box confirmada", "17592186179051": "Sem box confirmada", "17592186179053": "Sem box confirmada", "17592186179054": "Sem box confirmada", "17592186179055": "Sem box confirmada", "17592454614469": "Sem box confirmada", "17592454614480": "Sem box confirmada", "17592454614507": "Sem box confirmada", "17592454614509": "Sem box confirmada", "17592722922839": "Sem box confirmada", "17592722955680": "Sem box confirmada", "17592723049936": "Sem box confirmada", "17593259920877": "FC Bayern München 79–80", "299067699633495": "Sem box confirmada", "299067699666336": "Sem box confirmada", "370536760778144": "Sem box confirmada", "370537029180759": "Sem box confirmada", "52777631915074": "POTW 15 Sep '22", "52779510963616": "POTW 3 Nov '22", "52781390011808": "POTW International Cup 15 Dec '22", "52782195325003": "POTW 19 Jan '23", "52783269157572": "POTW 16 Feb '23", "52783806009713": "POTW 2 Mar '23", "52784342881172": "POTW 16 Mar '23", "52785416510807": "POTW 13 Apr '23", "52787027123543": "POTW 1 Jun '23", "52788637736279": "POTW 24 Aug '23", "52788906209492": "POTW 31 Aug '23", "52845546085792": "POTW National Teams 14 Sep '23", "52849035817086": "POTW 16 Nov '23", "52851720174914": "POTW 11 Jan '24", "52851720182920": "POTW 11 Jan '24", "52852257053845": "POTW 25 Jan '24", "52852793922283": "POTW 8 Feb '24", "52853599156299": "POTW 29 Feb '24", "52868094750368": "POTW European Club Championship 21 Mar '24", "52868363197124": "POTW National Teams 28 Mar '24", "52868900044618": "POTW 11 Apr '24", "52869973711938": "POTW 2 May '24", "52872121266486": "POTW National Teams 11 Jul '24", "52872926590672": "POTW 29 Aug '24", "52873463459488": "POTW 12 Sep '24", "52874268681548": "POTW European Club Championship 26 Sep '24", "52874537212844": "POTW 3 Oct '24", "52875342527062": "POTW National Teams 17 Oct '24", "52875610824023": "POTW 24 Oct '24", "52876416233782": "POTW 7 Nov '24", "52878026869086": "POTW European Club Championship 5 Dec '24", "52878295213388": "POTW 12 Dec '24", "52878832156550": "POTW European Club Championship 19 Dec '24", "52878832168608": "POTW European Club Championship 19 Dec '24", "52879100524619": "POTW 26 Dec '24", "52879637458996": "POTW 16 Jan '25", "52880442781344": "POTW European Club Championship 30 Jan '25", "52883127174173": "POTW 3 Apr '25", "52885274603572": "POTW European Club Championship 24 Apr '25", "52885543047915": "POTW 1 May '25", "52885811474484": "POTW 15 May '25", "52886079860180": "POTW 22 May '25", "52886079925920": "POTW 22 May '25", "52886348361088": "POTW 29 May '25", "52886616816720": "POTW National Teams 12 Jun '25", "52887153548631": "POTW Club International Cup 26 Jun '25", "52887422094115": "POTW Club International Cup 3 Jul '25", "52887690550188": "POTW Club International Cup 10 Jul '25", "52887690564960": "POTW Club International Cup 10 Jul '25", "52887690579199": "POTW Club International Cup 10 Jul '25", "52888764161367": "POTW National Teams 11 Sep '25", "52889569586848": "POTW 2 Oct '25", "52889838022294": "POTW 9 Oct '25", "52890374892941": "POTW 23 Oct '25", "52890643249227": "POTW 30 Oct '25", "52890643324381": "POTW 30 Oct '25", "52890911771157": "POTW 6 Nov '25", "52891180115276": "POTW 13 Nov '25", "52891717070797": "POTW 27 Nov '25", "52891985419680": "POTW 4 Dec '25", "52891985490230": "POTW 4 Dec '25", "52891985519680": "POTW 4 Dec '25", "52891985544221": "POTW 4 Dec '25", "52892253948437": "POTW 11 Dec '25", "52892522360884": "POTW 18 Dec '25", "52892790823620": "POTW 25 Dec '25", "52893059265590": "POTW European Club Championship 25 Sep '25", "52893596129988": "POTW European Club Championship 30 Oct '25", "52894132973575": "POTW European Club Championship 4 Dec '25", "52894401431902": "POTW European Club Championship 18 Dec '25", "52895206727528": "POTW European Club Championship 26 Feb '26", "52895206757728": "POTW European Club Championship 26 Feb '26", "52895475188428": "POTW European Club Championship 5 Mar '26", "52895743518028": "POTW European Club Championship 19 Mar '26", "52896548935008": "POTW 8 Jan '26", "52896817328180": "POTW 15 Jan '26", "52897085700171": "POTW 22 Jan '26", "52897354207979": "POTW 29 Jan '26", "52897891097516": "POTW 12 Feb '26", "52899233256171": "POTW 19 Mar '26", "52899501686662": "POTW 26 Mar '26", "52899770145476": "POTW National Teams 2 Apr '26", "52900307004764": "POTW 16 Apr '26", "52900575447573": "POTW 23 Apr '26", "52901380747213": "POTW 21 May '26", "52901380766800": "POTW 21 May '26", "52901649095746": "POTW 28 May '26", "53962237674443": "POTM Brasileirão Assaí 7 Dec '23", "53968680110883": "POTM Brasileirão Benato 13 Jun '24", "53977270054668": "POTM J1 LEAGUE 14 Aug '25", "53981028177481": "POTM Trendyol Süper Lig 22 Jan '26", "53983980938001": "POTM Brasileirão Betano 16 Apr '26", "55066849484923": "POTS Liga BBVA MX 23-24", "55066849562859": "POTS Liga BBVA MX 23-24", "55068460171421": "POTS English League 24-25", "55068460176107": "POTS English League 24-25", "55068460183501": "POTS English League 24-25", "55068728532034": "POTS Spanish League 24-25", "55068728618656": "POTS Spanish League 24-25", "55068997039592": "POTS Italian League 24-25", "55069533838752": "POTS Brazilian League 2025", "55069533950196": "POTS Brazilian League 2025", "55069802348765": "POTS Italian League 25-26", "55069802398749": "POTS Italian League 25-26", "55070339215364": "POTS Spanish League 25-26", "55070607649352": "POTS English League 25-26", "55070607668011": "POTS English League 25-26", "55070876039189": "POTS Trendyol Süper Lig 25-26", "55070876081807": "POTS Trendyol Süper Lig 25-26", "55070876119403": "POTS Trendyol Süper Lig 25-26", "55071412966292": "Champions Campaign 25-26 Arsenal FC", "56162066111831": "POTD International Cup Day 6", "56162066233689": "POTD International Cup Day 6", "56162603100071": "POTD International Cup Day 8", "56163139903267": "POTD International Cup Day 11", "56163139956740": "POTD International Cup Day 11", "56163408392226": "POTD International Cup Day 12", "56164750578580": "POTD International Cup Day 17", "56165019008842": "POTD International Cup Day 18-19", "56165019026854": "POTD International Cup Day 18-19", "56165019032260": "POTD International Cup Day 18-19", "56165019040848": "POTD International Cup Day 18-19", "56165287461944": "POTD International Cup Day 20", "56166361224544": "POTD International Cup Day 24", "56166629547424": "POTD International Cup Day 25", "56167703375520": "POTD International Cup Day 30", "56167703392163": "POTD International Cup Day 30", "70373039184962": "Great Finishers 2 May '22", "70377334152258": "European Club Championship 16 Jun '22", "70379750074001": "Breakout Stars Jul '22", "70380286909783": "Ligue 1 Uber Eats Jul '22", "87960930356715": "Sem box confirmada", "87963346144942": "Sem box confirmada", "87963346275802": "Sem box confirmada", "87963346275821": "Sem box confirmada", "87963614711275": "Sem box confirmada", "87964419886766": "Sem box confirmada", "87964420017642": "Sem box confirmada", "88029649833411": "Sem box confirmada", "88029649833424": "Sem box confirmada", "88029918174624": "Sem box confirmada", "88029918268894": "Sem box confirmada", "88029918268910": "Sem box confirmada", "88029918268911": "Sem box confirmada", "88030186577239": "Argentina 2022", "88030455007969": "Sem box confirmada", "88030455139790": "Sem box confirmada", "88030455139819": "Sem box confirmada", "88030455139821": "Sem box confirmada", "88030455139822": "Sem box confirmada", "88030455139854": "Sem box confirmada", "88030455153209": "Sem box confirmada", "88030723480992": "Sem box confirmada", "88030723575271": "Sem box confirmada", "88030992010677": "Sem box confirmada", "88031797186222": "Sem box confirmada", "88031797317111": "Sem box confirmada", "88032065620703": "Sem box confirmada", "88032065752515": "Sem box confirmada", "88032065752551": "Sem box confirmada", "88032065752559": "Sem box confirmada", "88032065752590": "Sem box confirmada", "88032334056161": "Sem box confirmada", "88032334187984": "Sem box confirmada", "88032334188007": "Sem box confirmada", "88032334201401": "Sem box confirmada", "88032602496343": "Sem box confirmada", "88032870964640": "Sem box confirmada", "88033139363502": "Sem box confirmada", "88033139400096": "Sem box confirmada", "88033139494325": "Sem box confirmada", "88033139494339": "Sem box confirmada", "88033139494379": "Sem box confirmada", "88033407797983": "Sem box confirmada", "88033407797985": "Sem box confirmada", "88033407804329": "Sem box confirmada", "88033407832198": "Sem box confirmada", "88033407929808": "Sem box confirmada", "88033407929837": "Sem box confirmada", "88033407929847": "Sem box confirmada", "88033407929870": "Sem box confirmada", "88033676365293": "Germany 1980 feat. Captain Tsubasa", "88034481539809": "France 1993 feat. Captain Tsubasa", "88034750107127": "Uruguay 2010 feat. Captain Tsubasa", "88035018410719": "France 1984 feat. Captain Tsubasa", "88035555342710": "Sem box confirmada", "88035555400712": "Vasco Gipuzkoa AB 22-23", "88035555413429": "Sem box confirmada", "88035555413443": "Sem box confirmada", "88035555413454": "Sem box confirmada", "88035555413486": "Sem box confirmada", "88035823751302": "Sem box confirmada", "88035823760248": "Sem box confirmada", "88035823848941": "Sem box confirmada", "88035823862329": "Sem box confirmada", "88036092152543": "Sem box confirmada", "88036092153518": "Sem box confirmada", "88036092284395": "Sem box confirmada", "88036360588001": "Sem box confirmada", "88036360588974": "Sem box confirmada", "88036360594345": "Sem box confirmada", "88036360631160": "Sem box confirmada", "88036360649078": "Sem box confirmada", "88036360719797": "Sem box confirmada", "88036360719822": "Sem box confirmada", "88036360719824": "Sem box confirmada", "88036360719834": "Sem box confirmada", "88036360719854": "Sem box confirmada", "88036360719863": "Sem box confirmada", "88036360719886": "Sem box confirmada", "88037434461671": "Epic Nostalgia 26 Jun '25", "88037971205463": "Leo Messi Edition 2026", "88039044942559": "Sem box confirmada", "88039044955096": "Sem box confirmada", "88039044955099": "Sem box confirmada", "88039044976774": "Sem box confirmada", "88039044980128": "Sem box confirmada", "88039045003638": "Sem box confirmada", "88039045074371": "Sem box confirmada", "88039045074407": "Sem box confirmada", "88039045074413": "Sem box confirmada", "88039581932552": "Vasco Gipuzkoa AB 23-24", "88039581945296": "Sem box confirmada", "88039581945323": "Sem box confirmada", "88039581945358": "Sem box confirmada", "88040387117286": "Sem box confirmada", "88040387119839": "Sem box confirmada", "88040387126185": "Sem box confirmada", "88040655554414": "Sem box confirmada", "88041460874200": "Sem box confirmada", "88041460993461": "National Teams Selection Attackers 27 Apr '26", "88042803047215": "Sem box confirmada", "88044145217198": "Sem box confirmada", "88044145253792": "National Teams Selection 29 Jun '26", "88044145348046": "National Teams Selection 8 Jun '26", "88044145348071": "National Teams Selection 15 Jun '26", "88044145348075": "Sem box confirmada", "88044413691936": "Sem box confirmada", "89061247290863": "Sem box confirmada", "89061784067488": "Sem box confirmada", "89063394774510": "Sem box confirmada", "89067152870864": "Sem box confirmada", "89067958050135": "Sem box confirmada", "89069568702539": "Sem box confirmada", "89071179308448": "Sem box confirmada", "89072253144526": "Sem box confirmada", "89073863757293": "Sem box confirmada", "89129161334103": "Sem box confirmada", "89129429769559": "Sem box confirmada", "89129698205015": "Sem box confirmada", "89130771980042": "Sem box confirmada", "89132919465292": "Sem box confirmada", "89133187865943": "Sem box confirmada", "89133456301399": "Sem box confirmada", "89133993205152": "Sem box confirmada", "89135067044780": "Club International Cup 2025", "89136409091415": "Sem box confirmada", "89136946016341": "Big Time CR Flamengo 19 Oct '25", "89137214427270": "Sem box confirmada", "89138288266704": "Sem box confirmada", "105555263858377": "Premium Ambassador Pack Alexander-Arnold Sep '22", "105557142802858": "Premium Ambassador Pack Bruno Fernandes Oct '22", "105562243182718": "National Team Selection France 21 Nov '22", "105566538043818": "National Team Pack Portugal '22", "105569490872375": "Club Selection Tottenham WB 16 Jan '23", "105569759379003": "Club Selection Piemonte BN 23 Jan '23", "105573517421702": "League Selection English 2 Mar '23", "105575396517577": "European Club Championship Selection 16 Mar '23", "105576470271075": "Club Selection Liverpool R 17 Apr '23", "105582912724124": "Perfect Introduction 8 Jun '23", "105585328564279": "Fans' Choice Asia 22-23", "105587476115502": "Fans' Choice English League 22-23", "105589623599230": "National Team Selection France 24 Jul '23", "105589891928490": "National Team Selection Worldwide 31 Jul '23", "105592039515849": "Club Selection Liverpool R 21 Aug '23", "105593650153567": "Champions Campaign Rewards 22-23 FC Barcelona", "105594723822622": "Champions Campaign Rewards 22-23 FC Bayern München", "105629352046638": "Manchester United FC Pack 5 Oct '23", "105633915466074": "Golden Boys 2 Nov '23", "105639284052394": "Daily Bonus", "105644451473463": "AFC Asian Cup Selection Republic of Korea Jan '24", "105652974377878": "European Clubs Selection Attackers 4 Mar '24", "105656195595835": "Italian League Selection 14 Mar '24", "105658611511342": "BLUE LOCK Collaboration Campaign 21 Mar '24", "105659416861935": "BLUE LOCK Collaboration Campaign 21 Mar '24", "105663443355959": "Spanish League Selection Attackers 15 Apr '24", "105666127704098": "European Clubs Selection Attackers 20 May '24", "105680623218814": "National Team Selection France '24", "105681428525102": "Mobile 7th Anniversary Celebration", "105681965395975": "Champions Campaign Rewards 23-24 Atalanta BC", "105682770702370": "National Team Pack France '24", "105683844338090": "National Team Pack Portugal '24", "105691092199113": "National Stars 13 Jun '24", "105694044991614": "Summer Transfer 15 Aug '24", "105695387168894": "Welcome Login Bonus", "105702366490750": "Highlight Continental Tournaments '24", "105703171734409": "SC Corinthians Paulista Selection 29 Aug '24", "105709614251579": "Legacy of Legends 10 Oct '24", "105715788280154": "European Clubs Selection Attackers 4 Nov '24", "105720888529397": "Centre Piece 5 Dec '24", "105720888553818": "Centre Piece 5 Dec '24", "105723841358773": "National Teams Selection European 12 Dec '24", "105729746907170": "Role Changers 13 Feb '25", "105745047734583": "Spanish League Selection 6 Mar '25", "105749342693065": "Liverpool R Selection 6 Feb '25", "105752832356478": "Madrid Chamartin B Selection 7 Apr '25", "105754711432614": "Advertisement Reward 24 Apr '25", "105754979851158": "Winter Transfer 3 Mar '25", "105762227604762": "Offensive Genius 24 Apr '25", "105773233448649": "National Team Selection Portugal 29 May '25", "105776454608951": "Manager Edition 2026", "105778870595710": "Welcome Login Bonus 2026", "105783165571441": "Italian League Selection 18 Sep '25", "105783434009756": "European Clubs Selection Attackers 11 Sep '25", "105794439855675": "Clutch Players 4 Dec '25", "105799540139370": "Winter Transfer 23 Feb '26", "105801687641013": "Spanish League Selection 2 Apr '26", "105802492809642": "National Teams Selection 8 Jan '26", "105802492925027": "National Teams Selection 8 Jan '26", "105803835101553": "AC Milan Pack 25-26", "105807861636245": "National Teams Selection Attackers 16 Oct '25", "105821820296614": "Brazil & England National Team Campaign 6 Nov '25", "105828799598961": "Role Changers 5 Mar '26", "105829067975814": "Magical Dribbler 2 Apr '26", "105832826159749": "National Teams Selection Attackers 23 Mar '26", "105846516333406": "Starter Set 28 May '26", "105849200685102": "National Team Pack England 2026", "105849200694299": "National Team Pack England 2026", "105849469120546": "National Team Pack France 2026", "105849469120638": "National Team Pack France 2026", "105850274440406": "National Team Selection Japan Jun '26", "105851666980824": "National Team Selection Indonesia Jun '26", "105851968964074": "National Team Selection Morocco Jun '26", "105852237392648": "National Team Selection Egypt Jun '26", "105860558896107": "National Team Selection Algeria Jun '26", "106653970182270": "Show Time Ligue 1 Uber Eats 22-23", "106723494897719": "Show Time 7 Dec '23", "106723494968891": "Show Time 7 Dec '23", "106723780071850": "AFC Champions League Selection 25 Dec '23", "106726716084650": "Show Time 1 Aug '24", "106727521503543": "Show Time European Club Tournaments 23-24", "106727789932670": "Show Time Ligue 1 Uber Eats 23-24", "106729400576949": "Show Time Young Stars 23-24 Vol. 1", "106732621777207": "World Player of the Year 2024", "106734785925546": "AFC Champions League Elite™ Selection 13 Jan '25", "106735037701276": "Offensive Genius 17 Oct '24", "106737722036725": "National Teams Selection Attackers 13 Mar '25", "106737722044542": "National Teams Selection Attackers 13 Mar '25", "106738795814310": "Standout Lefties 3 Feb '25", "106741211713905": "Towering Giants 29 May '25", "106742822268038": "Trendyol Süper Lig Selection 17 Apr '25", "106743627624574": "Spanish League 24-25 Season's Best", "106746899114039": "AFC Asian Qualifiers™ Selection 22 May '25", "106749533210935": "Diagonal Long Pass A 15 Aug '25", "106750875398684": "Over-the-Top Pass B 2 Oct '25", "106754096599541": "Show Time 10 Aug '25", "106754901929868": "Offensive Genius 25 Aug '25", "106755438787299": "Brazilian League Selection 25 Sep '25", "106762418117636": "Japanese Stars 10 Nov '25", "106762686548319": "Aggressive Centring A 4 Dec '25", "106763223426410": "English League Selection 22 Dec '25", "106764028719230": "Breakthrough Pass A 8 Jan '26", "106765186378504": "CAF AFRICA CUP OF NATIONS 25 vol.1", "106766176135223": "American League Selection 17 Nov '25", "106766981509166": "New Year's Gift 2026", "106773692395554": "Standout Attackers 25-26 Season's Best", "106773692401975": "Standout Attackers 25-26 Season's Best", "106777987362942": "Spanish League 25-26 Season's Best", "106780671726691": "Daily Bonus 2026", "106781477023870": "International Cup vol.1", "106781745353130": "International Cup vol.2", "106781745470620": "International Cup vol.2", "106782013894690": "International Cup vol.3", "106783087650006": "Japan Selection 2 Jul '26", "106787651045391": "Spain 2026", "17592186048938": "Manchester United 21-22", "17592186179074": "Sem box confirmada", "52776826679422": "POTW 25 Aug '22", "52777363558769": "POTW 8 Sep '22", "52777900357362": "POTW 29 Sep '22", "52780584775806": "POTW International Cup 1 Dec '22", "52781121579063": "POTW International Cup 8 Dec '22", "52781658517630": "POTW International Cup 22 Dec '22", "52783537565822": "POTW 23 Feb '23", "52785416625046": "POTW 13 Apr '23", "52785685049470": "POTW 20 Apr '23", "52785953482441": "POTW 27 Apr '23", "52787295665723": "POTW 8 Jun '23", "52788906274942": "POTW 31 Aug '23", "52845277653047": "POTW 7 Sep '23", "52847156775223": "POTW European Club Championship 12 Oct '23", "52847425098154": "POTW National Teams 19 Oct '23", "52847425204350": "POTW National Teams 19 Oct '23", "52848230502901": "POTW 2 Nov '23", "52848230512334": "POTW 2 Nov '23", "52849304260977": "POTW European Club Championship 16 Nov '23", "52849572697187": "POTW National Teams 23 Nov '23", "52851451736190": "POTW 28 Dec '23", "52851988613431": "POTW 18 Jan '24", "52852257040073": "POTW 25 Jan '24", "52854404458551": "POTW 14 Mar '24", "52868094734462": "POTW European Club Championship 21 Mar '24", "52868631613809": "POTW 4 Apr '24", "52868900072373": "POTW 11 Apr '24", "52869168493084": "POTW 18 Apr '24", "52871852862389": "POTW National Teams 4 Jul '24", "52873463337386": "POTW 12 Sep '24", "52875074056199": "POTW European Club Championship 10 Oct '24", "52876684675383": "POTW 14 Nov '24", "52876953113699": "POTW European Club Championship 14 Nov '24", "52878295289079": "POTW 12 Dec '24", "52878563649591": "POTW 19 Dec '24", "52878832158735": "POTW European Club Championship 19 Dec '24", "52879100515879": "POTW 26 Dec '24", "52879100588158": "POTW 26 Dec '24", "52879637458978": "POTW 16 Jan '25", "52880174329982": "POTW 30 Jan '25", "52880442771767": "POTW European Club Championship 30 Jan '25", "52880442773873": "POTW European Club Championship 30 Jan '25", "52880979636258": "POTW European Club Championship 6 Feb '25", "52883663999345": "POTW 17 Apr '25", "52884469297278": "POTW European Club Championship 27 Feb '25", "52885274603566": "POTW European Club Championship 24 Apr '25", "52885811474558": "POTW 15 May '25", "52886616674730": "POTW National Teams 12 Jun '25", "52886616818309": "POTW National Teams 12 Jun '25", "52886885222751": "POTW Club International Cup 19 Jun '25", "52887422093623": "POTW Club International Cup 3 Jul '25", "52887690522658": "POTW Club International Cup 10 Jul '25", "52887690522750": "POTW Club International Cup 10 Jul '25", "52888227393662": "POTW 28 Aug '25", "52888764200735": "POTW National Teams 11 Sep '25", "52889838012727": "POTW 9 Oct '25", "52890374885745": "POTW 23 Oct '25", "52891717060623": "POTW 27 Nov '25", "52893059231790": "POTW European Club Championship 25 Sep '25", "52893059240129": "POTW European Club Championship 25 Sep '25", "52893059253670": "POTW European Club Championship 25 Sep '25", "52893327667326": "POTW European Club Championship 9 Oct '25", "52894132973694": "POTW European Club Championship 4 Dec '25", "52894669850935": "POTW European Club Championship 29 Jan '26", "52894938297131": "POTW European Club Championship 5 Feb '26", "52895206724635": "POTW European Club Championship 26 Feb '26", "52897085763618": "POTW 22 Jan '26", "52897354230536": "POTW 29 Jan '26", "52897891019910": "POTW 12 Feb '26", "52897891069986": "POTW 12 Feb '26", "52898964843272": "POTW 12 Mar '26", "52900038553634": "POTW 9 Apr '26", "52900306995215": "POTW 16 Apr '26", "52900306996396": "POTW 16 Apr '26", "52901112295470": "POTW 14 May '26", "52901112312348": "POTW 14 May '26", "52901380744554": "POTW 21 May '26", "52901380758278": "POTW 21 May '26", "53983980934636": "POTM Brasileirão Betano 16 Apr '26", "55067117989922": "POTS Ligue 1 Uber Eats 23-24", "55067386431839": "POTS English League 23-24", "55071681398799": "Champions Campaign 25-26 FC Barcelona", "56162066215038": "POTD International Cup Day 6", "56162066252275": "POTD International Cup Day 6", "56162871532700": "POTD International Cup Day 10", "56163676721578": "POTD International Cup Day 13", "56164482134050": "POTD International Cup Day 16", "56165287477893": "POTD International Cup Day 20", "56165824319857": "POTD International Cup Day 22", "56168240230526": "POTD International Cup Day 33-34", "56168240236559": "POTD International Cup Day 33-34", "56168240262069": "POTD International Cup Day 33-34", "56168508672311": "POTD International Cup Day 9", "70373039149482": "Great Finishers 2 May '22", "70373307691134": "Enchanting Dribblers 9 May '22", "70376260374954": "Premium Club Pack Manchester United Jun '22", "87963077840392": "Sem box confirmada", "88029649700314": "Sem box confirmada", "88029649701165": "Sem box confirmada", "88032065752589": "Sem box confirmada", "88035823760539": "Italy 2021", "88036360586714": "Sem box confirmada", "88036360631451": "Sem box confirmada", "88039045074440": "Sem box confirmada", "88039045116846": "Sem box confirmada", "88039313485858": "World Player of the Year 2025", "88039850246968": "Sem box confirmada", "88040387118554": "Sem box confirmada", "88041461035950": "Sem box confirmada", "88044950524330": "Portugal 2026", "89068226588798": "Sem box confirmada", "89069031903601": "Sem box confirmada", "89070105636910": "Sem box confirmada", "89131308929393": "Sem box confirmada", "89131577378214": "Sem box confirmada", "89135067017250": "Big Time 29 Apr '25", "89135067035344": "Big Time 17 May '25", "89138019820906": "Standout Midfielders 25-26 Season's Best", "105577812455608": "Club Selection eFootball™ Championship Vol.4", "105654584996024": "Manchester United FC Selection 8 Apr '24", "105679817862778": "Speedsters 9 May '24", "105702903413058": "Champions Campaign Rewards '24 Spain", "105709614280107": "Legacy of Legends 10 Oct '24", "105716056649338": "Earthmover 7 Nov '24", "105749342641955": "Liverpool R Selection 6 Feb '25", "105770817583426": "Champions Campaign 24-25 FC Barcelona", "105782897139165": "Anticipated Standouts 25-26", "105790413371714": "Tresure Link Campaign 28 Aug '25", "105792023879459": "PFA Awards 2025", "105794439801608": "Clutch Players 4 Dec '25", "105802761407743": "Young Stars 11 Dec '25", "105803029802332": "European Clubs Selection 13 Nov '25", "105805714192706": "FC Barcelona Pack 25-26", "105807593205944": "European Clubs Selection 9 Oct '25", "105816451581405": "Champions Campaign 2025 CR Flamengo", "105851348193896": "National Team Selection Malaysia May '26", "105852690382682": "The Football Festival Campaign 2026", "105860558811421": "National Team Selection Algeria Jun '26", "106653164826909": "Show Time 13 Apr '23", "106723494911779": "Show Time 7 Dec '23", "106728863725890": "Show Time Spanish League 23-24", "106737185105810": "Brazilian League Kick-off 27 Mar '25", "106754365099263": "Show Time 11 Aug '25", "106755707278436": "Brazilian League Selection 30 Oct '25", "106757854755138": "The Football Festival Campaign 2026", "106761092718202": "AFC Champions League Elite™ Selection 20 Oct '25", "106761092731496": "AFC Champions League Elite™ Selection 20 Oct '25", "106766713092441": "Daily Free Draw 4 Dec '25", "106768055197475": "Over-the-Top Pass C 5 Feb '26", "106771293204765": "AFC Champions League™ Selection 16 Feb '26", "106787651090754": "Spain 2026", "52782732190909": "POTW 2 Feb '23", "52848767392772": "POTW 9 Nov '23", "52873731930434": "POTW 19 Sep '24", "52877758357283": "POTW 5 Dec '24", "52884737740993": "POTW European Club Championship 13 Mar '25", "52885006219586": "POTW European Club Championship 20 Mar '25", "52885274655042": "POTW European Club Championship 24 Apr '25", "52885542985507": "POTW 1 May '25", "52887690567240": "POTW Club International Cup 10 Jul '25", "52887959009602": "POTW 21 Aug '25", "52889837932398": "POTW 9 Oct '25", "52890374892892": "POTW 23 Oct '25", "52890911764664": "POTW 6 Nov '25", "52891985493661": "POTW 4 Dec '25", "52894401424732": "POTW European Club Championship 18 Dec '25", "52897085775325": "POTW 22 Jan '26", "52897354250562": "POTW 29 Jan '26", "52897354255615": "POTW 29 Jan '26", "52897891086520": "POTW 12 Feb '26", "52898696427842": "POTW 5 Mar '26", "53976196313725": "POTM Trendyol Süper Lig 12 Jun '25", "53976464735047": "POTM Brazilian League 10 Jul '25", "55069533958391": "POTS Brazilian League 2025", "55070607654410": "POTS English League 25-26", "56163140008258": "POTD International Cup Day 11", "56163760664861": "POTD International Cup Day 13", "70373307641466": "Enchanting Dribblers 9 May '22", "88030455139858": "Sem box confirmada", "88032334187967": "Sem box confirmada", "88035555440962": "FC Barcelona 24-25", "88038239795522": "Lamine Yamal Edition 2026", "88039934308531": "Sem box confirmada", "88040118843714": "World Player of the Year 2025", "88040655687168": "Sem box confirmada", "89060441984433": "Sem box confirmada", "89135066963747": "Sem box confirmada", "89135067068738": "Big Time 15 May '25", "89138019858754": "Big Time FC Barcelona 28 Feb '26", "105569222502056": "Mid-season MVPs Jan '23", "105570564611459": "Club Selection Chelsea B 13 Feb '23", "105582644223960": "Club Selection FC Bayern München 5 Jun '23", "105593113271432": "Summer Transfer 10 Aug '23", "105747732120051": "International Cup Qualifiers Campaign 13 Mar '25", "105754711436040": "Advertisement Reward 24 Apr '25", "105757932636076": "European Clubs Selection 19 May '25", "105764375112456": "Club International Cup Selection 12 Jun '25", "105783702451920": "Paris Saint-Germain Selection 6 Oct '25", "105801956046312": "Italian League Selection 5 Mar '26", "105803298148206": "Spanish League Selection 16 Oct '25", "105840879187432": "NARUTO SHIPPUDEN Collaboration Campaign 2026", "105848663838948": "Trendyol Süper Lig 25-26 Season's Best", "105851968938280": "National Team Selection Morocco Jun '26", "105860290371544": "National Team Selection Senegal Jun '26", "106654507071184": "Show Time Italian League 22-23", "106735574598131": "Breakthrough Talents 9 Dec '24", "106735843018933": "New Year's Gift 1 Jan '25", "106737990526435": "National Team Selection Türkiye 20 Mar '25", "106744164492837": "Italian League 24-25 Season's Best", "106749264693909": "Club International Cup Campaign 12 Jun '25", "106749281580484": "Club International Cup Campaign 12 Jun '25", "106756244027167": "Brazilian League 2025 Season's Best", "106760270552451": "eFootball™ League Rewards Phase 2", "106777450514613": "Starter Set 28 May '26", "106785503491871": "The Football Festival Campaign 2026", "52780584775954": "POTW International Cup 1 Dec '22", "52784074448008": "POTW 9 Mar '23", "52849304260801": "POTW European Club Championship 16 Nov '23", "52849841131713": "POTW 30 Nov '23", "52877221544327": "POTW National Teams 21 Nov '24", "52879100592519": "POTW 26 Dec '24", "52880442802675": "POTW European Club Championship 30 Jan '25", "52881248089808": "POTW 13 Feb '25", "52883395573456": "POTW 10 Apr '25", "52885006165541": "POTW European Club Championship 20 Mar '25", "52886348382707": "POTW 29 May '25", "52889301136872": "POTW 25 Sep '25", "52892253943504": "POTW 11 Dec '25", "52898696413683": "POTW 5 Mar '26", "52900843908580": "POTW 30 Apr '26", "53876606760371": "POTM Cinch Premiership Apr '22", "55067923314384": "POTS Italian League 23-24", "55068460171655": "POTS English League 24-25", "55069533859022": "POTS Brazilian League 2025", "88029649706260": "Sem box confirmada", "88029918268949": "Sem box confirmada", "88032334054874": "Sem box confirmada", "88032334090141": "Sem box confirmada", "88033139362093": "Sem box confirmada", "88035555286292": "Sem box confirmada", "88036092185256": "Sem box confirmada", "88038776508032": "Sem box confirmada", "88040387120768": "Sem box confirmada", "88041460894376": "Sem box confirmada", "88041729329832": "Sem box confirmada", "88042534641027": "Sem box confirmada", "88042803076483": "Sem box confirmada", "88043608522886": "Master League Sprint 9 Apr '26", "88044145220884": "Sem box confirmada", "89065542187382": "Sem box confirmada", "89066347431386": "Sem box confirmada", "89133724764840": "Sem box confirmada", "89137029898200": "Big Time Senegal 14 Jan '26", "89138019825360": "Big Time Paris Saint-Germain 28 Apr '26", "105576738645383": "Gabriel Barbosa Campaign Reward 13 Apr '23", "105586670813575": "Breakout Stars 6 Jul '23", "105632841744383": "Halloween Campaign 26 Oct '23", "105691377312496": "AFC Champions League Selection 23 May '24", "105707735146275": "Daily Bonus", "105823967763933": "Daily Bonus 2026", "105833379764805": "AFC Champions League™ Selection 22 Jan '26", "105852237307683": "National Team Selection Egypt Jun '26", "106655043870499": "ShowTime English League 22-23", "106734786026053": "AFC Champions League Elite™ Selection 13 Jan '25", "106737185230079": "Brazilian League Kick-off 27 Mar '25", "106755975603591": "Brazilian League Selection 27 Nov '25", "106775034613725": "Brasileirão Betano Selection 7 May '26", "106776376796960": "Ligue 1 McDonald’s Selection 2 Mar '26", "106784429760291": "Highlight May '26", "52778974109475": "POTW 20 Oct '22", "52779779415843": "POTW 10 Nov '22", "52781926899717": "POTW 12 Jan '23", "52787295560432": "POTW 8 Jun '23", "52847693586211": "POTW 26 Oct '23", "52875342438179": "POTW National Teams 17 Oct '24", "53878485695166": "POTS Campeonato Brasileiro Série A 2022", "70373039202083": "Great Finishers 2 May '22", "88039044948961": "Sem box confirmada", "88040655728821": "Sem box confirmada", "89061515600624": "Sem box confirmada", "89136677522134": "Sem box confirmada", "105679281039473": "Champions Campaign Rewards 23-24 Inter", "105694044986846": "Summer Transfer 15 Aug '24", "105720888546027": "Centre Piece 5 Dec '24", "105734310370982": "Negrete - A Passada 20 Feb '25", "105765448820849": "National Teams Selection Worldwide 19 Jun '25", "106729132107889": "Show Time Italian League 23-24", "106732353288463": "J.LEAGUE Monthly MVPs Sep '24", "106750070073457": "Over-the-Top Pass A 4 Sep '25", "106751949120936": "2025 J.LEAGUE AWARDS", "106763491879812": "Towering Giants 29 Dec '25", "106769397419872": "eFootball™ League Rewards Phase 9", "106782282266807": "International Cup vol.4", "106787919411383": "Tournament Stars 2026", "17592186179049": "Sem box confirmada", "17592186179086": "Sem box confirmada", "17592454614505": "Sem box confirmada", "52871852828785": "POTW National Teams 4 Jul '24", "52873463367745": "POTW 12 Sep '24", "52885274601585": "POTW European Club Championship 24 Apr '25", "52887422011457": "POTW Club International Cup 3 Jul '25", "52893327691402": "POTW European Club Championship 9 Oct '25", "52896548890737": "POTW 8 Jan '26", "55069802342513": "POTS Italian League 25-26", "55070339239313": "POTS Spanish League 25-26", "56162334587063": "POTD International Cup Day 7", "56165555812535": "POTD International Cup Day 21", "87962272534030": "Sem box confirmada", "87963077840374": "Sem box confirmada", "87963614711285": "Manchester United FC 64-65", "87964419887216": "Sem box confirmada", "88029649836778": "Sem box confirmada", "88030455139831": "Sem box confirmada", "88030992010723": "Sem box confirmada", "88031797186672": "Sem box confirmada", "88031797189908": "Sem box confirmada", "88031797317109": "Manchester United FC 63-64", "88032334057584": "Sem box confirmada", "88032334188021": "Manchester United 68-69", "88032334188054": "Sem box confirmada", "88033139394625": "Sem box confirmada", "88033407929878": "Sem box confirmada", "88033407933162": "Sem box confirmada", "88035555283056": "Sem box confirmada", "88035555413494": "Sem box confirmada", "88036360589424": "Sem box confirmada", "88037702764935": "Sem box confirmada", "88039044941086": "Sem box confirmada", "88039044943928": "Sem box confirmada", "88039044974657": "Sem box confirmada", "88039581945366": "Sem box confirmada", "88040387119495": "Sem box confirmada", "88040387251683": "Sem box confirmada", "88040387251702": "Sem box confirmada", "88044145248321": "National Teams Selection 13 Jul '26", "88044145348118": "National Teams Selection 6 Jul '26", "89066079129079": "Sem box confirmada", "89069300328561": "Sem box confirmada", "89132382660721": "Sem box confirmada", "89134261635137": "Sem box confirmada", "105559290415527": "Club Selection Manchester B 17 Oct '22", "105567075021694": "Golden Boys Dec '22", "105567075052406": "Golden Boys Dec '22", "105590160400490": "Back in the Game 3 Aug '23", "105623983353775": "Italian League Selection Attackers 11 Sep '23", "105646800277946": "Süper Lig Selection 18 Jan '24", "105656464050599": "English League Selection 14 Mar '24", "105701829556407": "Startup Campaign 12 Sep '24", "105705856174503": "English League Selection 19 Sep '24", "105711493244994": "Halloween Campaign 24 Oct '24", "105715519844271": "Trendyol Süper Lig Selection 24 Oct '24", "105727867875270": "Mid-season MVPs 9 Jan '25", "105731625977951": "BLACK FRIDAY Campaign 21 Nov '24", "105738873702207": "Pride of the Club 20 Mar '25", "105752563921142": "National Team Pack Norway '25", "105752563943847": "National Team Pack Norway '25", "105761959192134": "Chelsea B Selection 5 May '25", "105763569711287": "Champions Campaign 24-25 FC Bayern München", "105770549096694": "30th Anniversary Elites 10 Jul '25", "105774038773679": "Champions Campaign 24-25 Galatasaray SK", "105782897156511": "Anticipated Standouts 25-26", "105794171431354": "Speedsters 6 Nov '25", "105799271719327": "Liverpool R Selection 23 Mar '26", "105799808584103": "Manchester B Selection 26 Jan '26", "105803298222326": "Spanish League Selection 16 Oct '25", "105803835101144": "AC Milan Pack 25-26", "105804908868664": "Manchester United Pack 25-26", "105807056340769": "European Clubs Selection Attackers 23 Oct '25", "105815914625207": "Brazil & England National Team Campaign 6 Nov '25", "105816988360530": "National Teams Selection 8 Dec '25", "105823514776462": "CAF Africa Cup of Nations Selection 11 Dec '25", "105823514783663": "CAF Africa Cup of Nations Selection 11 Dec '25", "105829068030343": "Magical Dribbler 2 Apr '26", "105851666948025": "National Team Selection Indonesia Jun '26", "105860290455110": "National Team Selection Senegal Jun '26", "106652628021167": "Show Time 2 Mar '23", "106652628027815": "Show Time 2 Mar '23", "106654238640551": "Show Time European Club Championship 22-23", "106724568715499": "Liga BBVA MX Selection 25 Jan '24", "106726716183270": "Show Time 1 Aug '24", "106726716190966": "Show Time 1 Aug '24", "106729400568231": "Show Time Young Stars 23-24 Vol. 1", "106733158578359": "Goal Machines 28 Nov '24", "106733158664615": "Goal Machines 28 Nov '24", "106735843043104": "New Year's Gift 1 Jan '25", "106737185182020": "Brazilian League Kick-off 27 Mar '25", "106738527354430": "Trendyol Süper Lig Selection 27 Mar '25", "106738527367087": "Trendyol Süper Lig Selection 27 Mar '25", "106739601095545": "First Half of the Season 10 Apr '25", "106742822333228": "Trendyol Süper Lig Selection 17 Apr '25", "106745238253510": "Breakout Stars 24-25 Season's Best", "106748996323135": "Show Time 15 May '25", "106754901843130": "Offensive Genius 25 Aug '25", "106754901936551": "Offensive Genius 25 Aug '25", "106756512542639": "Trendyol Süper Lig Monthly MVPs Aug '25", "106756780971655": "Trendyol Süper Lig Monthly MVPs Sep '25", "106756780978095": "Trendyol Süper Lig Monthly MVPs Sep '25", "106757317842567": "Trendyol Süper Lig Monthly MVPs Oct '25", "106758391503938": "900 Million Downloads Campaign", "106759196885383": "Anticipated Standouts 13 Oct '25", "106760002221112": "Manchester United Selection 16 Feb '26", "106762418128755": "Japanese Stars 10 Nov '25", "106762686570911": "Aggressive Centring A 4 Dec '25", "106770471216611": "Campaign Rewards Feb '26", "106772350228103": "Trendyol Süper Lig Monthly MVPs Mar '26", "106773155540934": "1-2 Cut-in A 23 Apr '26", "106778255821223": "English League 25-26 Season's Best", "106778255827359": "English League 25-26 Season's Best", "106779329476141": "Trendyol Süper Lig Monthly MVPs May '26", "106779597985415": "Trendyol Süper Lig 25-26 Season's Best", "106779597991855": "Trendyol Süper Lig 25-26 Season's Best", "106782550788519": "International Cup vol.5", "106783087658867": "Japan Selection 2 Jul '26", "106785503555830": "The Football Festival Campaign 2026", "123236570413239": "Strike Arena", "17592186044712": "Sem box confirmada", "17592186179023": "Sem box confirmada", "17592186179082": "Sem box confirmada", "17592186179094": "Sem box confirmada", "17592454614479": "Sem box confirmada", "17592454614538": "Sem box confirmada", "17592454614550": "Sem box confirmada", "52777095137703": "POTW 1 Sep '22", "52781121650238": "POTW International Cup 8 Dec '22", "52781926889005": "POTW 12 Jan '23", "52786221849786": "POTW 11 May '23", "52845277743527": "POTW 7 Sep '23", "52848230533543": "POTW 2 Nov '23", "52852525478134": "POTW 1 Feb '24", "52853062371751": "POTW 15 Feb '24", "52853867671471": "POTW European Club Championship 29 Feb '24", "52870242240935": "POTW 9 May '24", "52872926595495": "POTW 29 Aug '24", "52873731815607": "POTW 19 Sep '24", "52875074057086": "POTW European Club Championship 10 Oct '24", "52875610863799": "POTW 24 Oct '24", "52875610943407": "POTW 24 Oct '24", "52877221562791": "POTW National Teams 21 Nov '24", "52880711210631": "POTW 6 Feb '25", "52884200884647": "POTW European Club Championship 20 Feb '25", "52884737669303": "POTW European Club Championship 13 Mar '25", "52887958894125": "POTW 21 Aug '25", "52887958987167": "POTW 21 Aug '25", "52889032722855": "POTW 18 Sep '25", "52889569580679": "POTW 2 Oct '25", "52891448555703": "POTW National Teams 20 Nov '25", "52891448641959": "POTW National Teams 20 Nov '25", "52891985494407": "POTW 4 Dec '25", "52893059232638": "POTW European Club Championship 25 Sep '25", "52893864554415": "POTW European Club Championship 13 Nov '25", "52895475167151": "POTW European Club Championship 5 Mar '26", "52898696305850": "POTW 5 Mar '26", "52898696405407": "POTW 5 Mar '26", "52900038576551": "POTW 9 Apr '26", "53968143169652": "POTM Trendyol Süper Lig 9 May '24", "53978612219454": "POTM Trendyol Süper Lig 23 Oct '25", "53980759707972": "POTM Brazilian League 18 Dec '25", "53982101886599": "POTM Trendyol Süper Lig 19 Feb '26", "55068460197336": "POTS English League 24-25", "55068996967610": "POTS Italian League 24-25", "55069533925462": "POTS Brazilian League 2025", "55069802334015": "POTS Italian League 25-26", "55069802378853": "POTS Italian League 25-26", "56162066237863": "POTD International Cup Day 6", "56164213720125": "POTD International Cup Day 15", "56166629640615": "POTD International Cup Day 25", "70379750164903": "Breakout Stars Jul '22", "87963077840342": "Sem box confirmada", "87963346275817": "Sem box confirmada", "88029649833430": "Sem box confirmada", "88029918268889": "Sem box confirmada", "88029918268950": "Sem box confirmada", "88030455139794": "Sem box confirmada", "88030455139807": "Sem box confirmada", "88030723575247": "Sem box confirmada", "88030992010761": "Sem box confirmada", "88031260446148": "Sem box confirmada", "88031528881604": "Sem box confirmada", "88032065752527": "Sem box confirmada", "88032334055391": "Sem box confirmada", "88032334187990": "Sem box confirmada", "88033139494377": "Sem box confirmada", "88033139525920": "Sem box confirmada", "88033407796182": "Sem box confirmada", "88033407929779": "Sem box confirmada", "88033407929796": "Sem box confirmada", "88033407929807": "Sem box confirmada", "88033407929826": "Sem box confirmada", "88033407929857": "Sem box confirmada", "88033407929873": "Sem box confirmada", "88035555413514": "Sem box confirmada", "88035823752931": "Sem box confirmada", "88036360586198": "Sem box confirmada", "88036360719839": "Sem box confirmada", "88036360719849": "Sem box confirmada", "88036360719873": "Sem box confirmada", "88037166026249": "Epic Nostalgia 26 Jun '25", "88037702765700": "Sem box confirmada", "88038776539586": "Sem box confirmada", "88039044974638": "Türkiye 2021", "88039044986828": "India 2023", "88039045074362": "Sem box confirmada", "88039045074383": "Sem box confirmada", "88039045074390": "Sem box confirmada", "88039045077738": "Sem box confirmada", "88039045081356": "Sem box confirmada", "88039045116847": "Sem box confirmada", "88039581945284": "Sem box confirmada", "88039581945302": "Sem box confirmada", "88039581945354": "Sem box confirmada", "88040387118038": "Sem box confirmada", "88040387119642": "Sem box confirmada", "88040387120260": "Sem box confirmada", "88040387121264": "Sem box confirmada", "88040387251635": "Advertisement Reward 16 Apr '26", "88040387251679": "Sem box confirmada", "88040387251713": "Sem box confirmada", "88040387251721": "Sem box confirmada", "88040655554922": "Sem box confirmada", "88040655557091": "Sem box confirmada", "88040655732170": "Sem box confirmada", "88041460860895": "National Teams Selection Attackers 27 Apr '26", "88041460993546": "National Teams Selection Attackers 27 Apr '26", "88041461035951": "National Team Selection Malaysia 27 Apr '26", "88042803217588": "Sem box confirmada", "88043876825271": "England 2026", "88044145348036": "Sem box confirmada", "88044145348047": "National Teams Selection 15 Jun '26", "88044413651570": "Sem box confirmada", "89060978855375": "Sem box confirmada", "89063931645407": "Sem box confirmada", "89066884435465": "Sem box confirmada", "89073326886422": "Sem box confirmada", "89074132192745": "Sem box confirmada", "89074400628164": "Sem box confirmada", "89131308848867": "Sem box confirmada", "89131845794218": "Sem box confirmada", "89135066911146": "Big Time 8 Jun '25", "89135067033519": "Sem box confirmada", "89136140651034": "Sem box confirmada", "89138019757410": "Big Time Johor Darul Ta'zim FC 25 Oct '25", "89138556701095": "Big Time Norway 5 Jul '26", "105859669692115": "National Teams Selection 6 Aug '26", "105859669695690": "National Teams Selection 6 Aug '26", "105859669699875": "National Teams Selection 6 Aug '26", "105843563556275": "J1 LEAGUE Selection 28 May '26", "105842758169569": "J1 LEAGUE Selection 26 Mar '26", "105842758262122": "J1 LEAGUE Selection 26 Mar '26", "105843563590422": "J1 LEAGUE Selection 28 May '26", "105842758260365": "J1 LEAGUE Selection 26 Mar '26", "105843563604842": "J1 LEAGUE Selection 28 May '26", "105843295137604": "J1 LEAGUE Selection 23 Apr '26", "105843295011243": "J1 LEAGUE Selection 23 Apr '26", "106799462259226": "Show Time 6 Aug '26", "106776108311976": "J.LEAGUE Monthly MVPs May '26", "106775839900908": "J.LEAGUE Monthly MVPs Apr '26", "106776108361937": "J.LEAGUE Monthly MVPs May '26", "106776108339229": "J.LEAGUE Monthly MVPs May '26", "106775839936861": "J.LEAGUE Monthly MVPs Apr '26", "106775571455574": "J.LEAGUE Monthly MVPs Mar '26", "106775303024396": "J.LEAGUE Monthly MVPs Feb '26", "106775303013036": "J.LEAGUE Monthly MVPs Feb '26", "106775571493490": "J.LEAGUE Monthly MVPs Mar '26", "55067654796153": "POTS Spanish League 23-24", "70377065722745": "Club Pack Manchester B Jun '22", "105796318919671": "Brazilian League Selection 25 Sep '25", "53970559146077": "POTM Brazilian League 10 Oct '24", "105796318894173": "Brazilian League Selection 25 Sep '25", "55070339218528": "POTS Spanish League 25-26", "105796318903040": "Brazilian League Selection 25 Sep '25", "105554726993672": "Club Selection Sevilla Triana VB 5 Sep '22", "105639552527964": "Club Icons 7 Dec '23", "53974854120198": "POTM Brazilian League 15 May '25", "53968680104710": "POTM Brasileirão Benato 13 Jun '24", "70377602608450": "European Masters Cup 16 Jun '22", "105642505334082": "Mid-season MVPs 4 Jan '24", "105796318836246": "Brazilian League Selection 25 Sep '25", "105796318916611": "Brazilian League Selection 25 Sep '25", "55069533944959": "POTS Brazilian League 2025", "106755438820479": "Brazilian League Selection 25 Sep '25", "105724646566013": "Brazilian League Selection 12 Dec '24", "105796318835406": "Brazilian League Selection 25 Sep '25", "52851988616262": "POTW 18 Jan '24", "387113187136582": "Italian League Selection Midfielders 4 Dec '23", "53975927864176": "POTM J1 LEAGUE 12 Jun '25", "53975122505049": "POTM J1 LEAGUE 15 May '25", "52847693645299": "POTW 26 Oct '23", "105686797239795": "Highlight English League 23-24", "105553116301513": "New license Aug '22", "105577275492553": "Club Selection Tigres UANL 20 Apr '23", "105687065662081": "Highlight Spanish League 23-24", "52884200904241": "POTW European Club Championship 20 Feb '25", "52851988649521": "POTW 18 Jan '24", "52901380742826": "POTW 21 May '26", "105817525313194": "Japanese Stars 6 Apr '26", "105805714163749": "FC Barcelona Pack 25-26", "105653511172985": "Spanish League Selection Midfielders 22 Jan '24", "88032334062505": "Sem box confirmada", "105805714141494": "FC Barcelona Pack 25-26", "105805714196288": "FC Barcelona Pack 25-26", "88036360622214": "Sem box confirmada", "52888495823012": "POTW 4 Sep '25", "105644183117482": "AFC Asian Cup Selection Japan Jan '24", "56167971812633": "POTD International Cup Day 31-32", "56167971795254": "POTD International Cup Day 31-32", "105854569403412": "Spain 2026", "105854569387197": "Spain 2026", "105854837821566": "Tournament Stars 2026", "105854837865552": "Tournament Stars 2026", "105854837839159": "Tournament Stars 2026", "105854837866225": "Tournament Stars 2026", "105854837879235": "Tournament Stars 2026", "105854837882618": "Tournament Stars 2026", "105854837862087": "Tournament Stars 2026", "90138747134483": "Sem box confirmada", "90138210263571": "Sem box confirmada", "90138478699027": "Sem box confirmada", "90138747134885": "Sem box confirmada", "90138478699429": "Sem box confirmada", "90138210263973": "Sem box confirmada", "90138478698953": "Sem box confirmada", "90138210263497": "Sem box confirmada", "90138747134409": "Sem box confirmada", "90138210259184": "Sem box confirmada", "90138478694640": "Sem box confirmada", "90138747130096": "Sem box confirmada", "90138210258002": "Sem box confirmada", "90138478693458": "Sem box confirmada", "90138747128914": "Sem box confirmada", "90138478698908": "Sem box confirmada", "90138210263452": "Sem box confirmada", "90138747134364": "Sem box confirmada", "90138478694647": "Sem box confirmada", "90138747130092": "Sem box confirmada", "90138210259180": "Sem box confirmada", "56167434860491": "POTD International Cup Day 28-29", "105859132821094": "Spain Selection 16 Jul '26", "105859132827344": "Spain Selection 16 Jul '26", "105859132816538": "Spain Selection 16 Jul '26", "105859132787394": "Spain Selection 16 Jul '26", "105859132793293": "Spain Selection 16 Jul '26", "105859132802911": "Spain Selection 16 Jul '26", "56167703296681": "POTD International Cup Day 30", "56167703292363": "POTD International Cup Day 30", "106783356022615": "Japan Selection 11 Jul '26", "105855643149532": "Japan Selection 11 Jul '26", "105855643147250": "Japan Selection 11 Jul '26", "105855643149509": "Japan Selection 11 Jul '26", "105855643153148": "Japan Selection 11 Jul '26", "105855643160674": "Japan Selection 11 Jul '26", "105855643168283": "Japan Selection 11 Jul '26", "105855643182804": "Japan Selection 11 Jul '26", "56166629607205": "POTD International Cup Day 25", "105858595968352": "France Selection 9 Jul '26", "105858595862475": "France Selection 9 Jul '26", "105858595920141": "France Selection 9 Jul '26", "105858595923493": "France Selection 9 Jul '26", "105858595930001": "France Selection 9 Jul '26", "105858595943762": "France Selection 9 Jul '26", "105858595963596": "France Selection 9 Jul '26", "105858595860513": "France Selection 9 Jul '26", "105858864353622": "National Teams Selection 13 Jul '26", "105858864287607": "National Teams Selection 13 Jul '26", "56166361216452": "POTD International Cup Day 24", "56166898046141": "POTD International Cup Day 26", "56166898059279": "POTD International Cup Day 26", "56166898075998": "POTD International Cup Day 26", "56166898055772": "POTD International Cup Day 26", "56167166486641": "POTD International Cup Day 27", "56167166506265": "POTD International Cup Day 27", "56167166487110": "POTD International Cup Day 27", "105858059057795": "Germany Selection 2 Jul '26", "105858059080556": "Germany Selection 2 Jul '26", "105858059090518": "Germany Selection 2 Jul '26", "105858059072129": "Germany Selection 2 Jul '26", "105858059086575": "Germany Selection 2 Jul '26", "105858059118591": "Germany Selection 2 Jul '26", "56165019016286": "POTD International Cup Day 18-19", "56165371349549": "POTD International Cup Day 20", "56165287474663": "POTD International Cup Day 20", "56163945294573": "POTD International Cup Day 14", "56163945279536": "POTD International Cup Day 14", "56163945300998": "POTD International Cup Day 14", "56163945336685": "POTD International Cup Day 14", "56164213690869": "POTD International Cup Day 15", "56164213715185": "POTD International Cup Day 15", "56164213744966": "POTD International Cup Day 15", "56164297650152": "POTD International Cup Day 15", "106783087647510": "Japan Selection 2 Jul '26", "105855374758570": "Japan Selection 2 Jul '26", "105855374605766": "Japan Selection 2 Jul '26", "105863159388554": "National Team Rising Stars 2 Jul '26", "105863159362754": "National Team Rising Stars 2 Jul '26", "56162603159351": "POTD International Cup Day 8", "56163676818671": "POTD International Cup Day 13", "56163676827359": "POTD International Cup Day 13", "56162334653278": "POTD International Cup Day 7", "56162334681687": "POTD International Cup Day 7", "56162334681984": "POTD International Cup Day 7", "105857522137074": "Brazil Selection 25 Jun '26", "105857522208887": "Brazil Selection 25 Jun '26", "105857522233591": "Brazil Selection 25 Jun '26", "105857522184466": "Brazil Selection 25 Jun '26", "105857522225394": "Brazil Selection 25 Jun '26", "105857522226699": "Brazil Selection 25 Jun '26", "105857522134814": "Brazil Selection 25 Jun '26", "56168508667068": "POTD International Cup Day 9", "56168508675153": "POTD International Cup Day 9", "56168508688815": "POTD International Cup Day 9", "56168508668869": "POTD International Cup Day 9", "56163408399393": "POTD International Cup Day 12", "56163408409938": "POTD International Cup Day 12", "56163492281881": "POTD International Cup Day 12", "56163139890527": "POTD International Cup Day 11", "56163139999591": "POTD International Cup Day 11", "56162871543647": "POTD International Cup Day 10", "56162871550948": "POTD International Cup Day 10", "56162871554253": "POTD International Cup Day 10", "56162116559324": "POTD International Cup Day 6", "105829873349913": "National Team Icons vol.2", "105829873359623": "National Team Icons vol.2", "105829873383795": "National Team Icons vol.2", "105829873260071": "National Team Icons vol.2", "105868041434003": "National Team Selection Iraq Jun '26", "105868041524885": "National Team Selection Iraq Jun '26", "105868041555523": "National Team Selection Iraq Jun '26", "105851666929920": "National Team Selection Indonesia Jun '26", "105851666888706": "National Team Selection Indonesia Jun '26", "105851666928735": "National Team Selection Indonesia Jun '26", "105851666933156": "National Team Selection Indonesia Jun '26", "105851666944980": "National Team Selection Indonesia Jun '26", "105851666962720": "National Team Selection Indonesia Jun '26", "105851666981529": "National Team Selection Indonesia Jun '26", "56161797708986": "POTD International Cup Day 5", "56161797816759": "POTD International Cup Day 5", "56161848136240": "POTD International Cup Day 5", "56161797813920": "POTD International Cup Day 5", "106770202684241": "eFootball™ League Rewards Phase 12", "56161529379414": "POTD International Cup Day 4", "56161529361025": "POTD International Cup Day 4", "56161529393658": "POTD International Cup Day 4", "56161613253165": "POTD International Cup Day 4", "56161529398584": "POTD International Cup Day 4", "56161260915001": "POTD International Cup Day 3", "56161260912518": "POTD International Cup Day 3", "56161260899827": "POTD International Cup Day 3", "56161260910022": "POTD International Cup Day 3", "56161260939420": "POTD International Cup Day 3", "56161311254482": "POTD International Cup Day 3", "56160992488921": "POTD International Cup Day 1-2", "56160992492831": "POTD International Cup Day 1-2", "56160992494840": "POTD International Cup Day 1-2", "56160992464525": "POTD International Cup Day 1-2", "105850006008049": "National Team Pack Netherlands 2026", "105856985310927": "National Teams Selection 15 Jun '26", "105856985320467": "National Teams Selection 15 Jun '26", "105856985350860": "National Teams Selection 15 Jun '26", "105856985337620": "National Teams Selection 15 Jun '26", "105856985338073": "National Teams Selection 15 Jun '26", "105856985370362": "National Teams Selection 15 Jun '26", "105856985306005": "National Teams Selection 15 Jun '26", "105856985311141": "National Teams Selection 15 Jun '26", "105849737550053": "National Team Pack Germany 2026", "105849737587523": "National Team Pack Germany 2026", "105849737587588": "National Team Pack Germany 2026", "105849737505756": "National Team Pack Germany 2026", "105849737591393": "National Team Pack Germany 2026", "105849737548277": "National Team Pack Germany 2026", "105849737557752": "National Team Pack Germany 2026", "105849737587522": "National Team Pack Germany 2026", "105848663814726": "Trendyol Süper Lig 25-26 Season's Best", "105848663824640": "Trendyol Süper Lig 25-26 Season's Best", "105848663868227": "Trendyol Süper Lig 25-26 Season's Best", "105848663818205": "Trendyol Süper Lig 25-26 Season's Best", "105848663822029": "Trendyol Süper Lig 25-26 Season's Best", "105848663815533": "Trendyol Süper Lig 25-26 Season's Best", "105862353945906": "National Team Captains 11 Jun '26", "105862437905823": "National Team Captains 11 Jun '26", "105862353971609": "National Team Captains 11 Jun '26", "105862354012836": "National Team Captains 11 Jun '26", "105862354044152": "National Team Captains 11 Jun '26", "105862354020931": "National Team Captains 11 Jun '26", "105862353957564": "National Team Captains 11 Jun '26", "105848395383057": "Trendyol Süper Lig Monthly MVPs May '26", "105848395389102": "Trendyol Süper Lig Monthly MVPs May '26", "105848395386435": "Trendyol Süper Lig Monthly MVPs May '26", "105848395400674": "Trendyol Süper Lig Monthly MVPs May '26", "105848395438518": "Trendyol Süper Lig Monthly MVPs May '26", "105848395386758": "Trendyol Süper Lig Monthly MVPs May '26", "105849469070367": "National Team Pack France 2026", "105849469121172": "National Team Pack France 2026", "105849469124895": "National Team Pack France 2026", "105849469150860": "National Team Pack France 2026", "105847321641389": "European Club Championship 25-26 Season's Best", "105847321630498": "European Club Championship 25-26 Season's Best", "105847321652945": "European Club Championship 25-26 Season's Best", "105847321641526": "European Club Championship 25-26 Season's Best", "105847321651674": "European Club Championship 25-26 Season's Best", "105847321668510": "European Club Championship 25-26 Season's Best", "105847321659866": "European Club Championship 25-26 Season's Best", "105847321586510": "European Club Championship 25-26 Season's Best", "105861548740954": "Japan Selection 4 Jun '26", "105861548621914": "Japan Selection 4 Jun '26", "105861548620873": "Japan Selection 4 Jun '26", "105861548721102": "Japan Selection 4 Jun '26", "105861548622168": "Japan Selection 4 Jun '26", "105861548768451": "Japan Selection 4 Jun '26", "105861548727062": "Japan Selection 4 Jun '26", "105861548730730": "Japan Selection 4 Jun '26", "88044145348039": "National Teams Selection 8 Jun '26", "105856448463933": "National Teams Selection 8 Jun '26", "105856448474539": "National Teams Selection 8 Jun '26", "105856448472638": "National Teams Selection 8 Jun '26", "105848932256095": "National Team Pack Portugal 2026", "105848932186795": "National Team Pack Portugal 2026", "105848932292145": "National Team Pack Portugal 2026", "105848932292218": "National Team Pack Portugal 2026", "105848932186223": "National Team Pack Portugal 2026", "105849200712620": "National Team Pack England 2026", "105849200715280": "National Team Pack England 2026", "105849200621750": "National Team Pack England 2026", "105849200685258": "National Team Pack England 2026", "105849200635641": "National Team Pack England 2026", "105849200737470": "National Team Pack England 2026", "105847053225747": "English League 25-26 Season's Best", "105847053225988": "English League 25-26 Season's Best", "105847053224560": "English League 25-26 Season's Best", "105847053251793": "English League 25-26 Season's Best", "105847053218316": "English League 25-26 Season's Best", "105847053250386": "English League 25-26 Season's Best", "105847053209473": "English League 25-26 Season's Best", "105851079679755": "National Team Selection Thailand May '26", "105851079745145": "National Team Selection Thailand May '26", "105851079682634": "National Team Selection Thailand May '26", "105851079770803": "National Team Selection Thailand May '26", "105851079727645": "National Team Selection Thailand May '26", "105851079745151": "National Team Selection Thailand May '26", "105851079748206": "National Team Selection Thailand May '26", "105851079748211": "National Team Selection Thailand May '26", "105851079766660": "National Team Selection Thailand May '26", "105851079734328": "National Team Selection Thailand May '26", "105851079748256": "National Team Selection Thailand May '26", "105860558872928": "National Team Selection Algeria Jun '26", "105860558903021": "National Team Selection Algeria Jun '26", "90138747130103": "Sem box confirmada", "90138210259191": "Sem box confirmada", "90138210263302": "Sem box confirmada", "90138478698758": "Sem box confirmada", "90138747134214": "Sem box confirmada", "90138210263185": "Sem box confirmada", "90138478698641": "Sem box confirmada", "90138747134097": "Sem box confirmada", "90138478694636": "Sem box confirmada", "105858864369073": "National Teams Selection 13 Jul '26", "105858864383032": "National Teams Selection 13 Jul '26", "105858864360006": "National Teams Selection 13 Jul '26", "105858864359761": "National Teams Selection 13 Jul '26", "105858864421684": "National Teams Selection 13 Jul '26", "106782282354314": "International Cup vol.4", "56165555885083": "POTD International Cup Day 21", "56165555825049": "POTD International Cup Day 21", "56165555822578": "POTD International Cup Day 21", "56165555900116": "POTD International Cup Day 21", "56165824335498": "POTD International Cup Day 22", "56165824317279": "POTD International Cup Day 22", "56165824320532": "POTD International Cup Day 22", "56165824239143": "POTD International Cup Day 22", "56165824241828": "POTD International Cup Day 22", "56166092766931": "POTD International Cup Day 23", "56166092683577": "POTD International Cup Day 23", "56166092750624": "POTD International Cup Day 23", "105857790655076": "National Teams Selection 29 Jun '26", "105857790656951": "National Teams Selection 29 Jun '26", "105857790570068": "National Teams Selection 29 Jun '26", "105857790619868": "National Teams Selection 29 Jun '26", "105857790622767": "National Teams Selection 29 Jun '26", "105857790655590": "National Teams Selection 29 Jun '26", "56162603017656": "POTD International Cup Day 8", "56162603098399": "POTD International Cup Day 8", "105829873325056": "National Team Icons vol.2", "105829923659230": "National Team Icons vol.2", "105857253699669": "National Teams Selection 22 Jun '26", "105857253677921": "National Teams Selection 22 Jun '26", "105857253740019": "National Teams Selection 22 Jun '26", "105857253742893": "National Teams Selection 22 Jun '26", "105857253747473": "National Teams Selection 22 Jun '26", "105857253748091": "National Teams Selection 22 Jun '26", "105857253755853": "National Teams Selection 22 Jun '26", "105857253684791": "National Teams Selection 22 Jun '26", "105867772995639": "National Team Selection Korea Republic Jun '26", "105867773068870": "National Team Selection Korea Republic Jun '26", "105867773017511": "National Team Selection Korea Republic Jun '26", "105867773118895": "National Team Selection Korea Republic Jun '26", "105867773069145": "National Team Selection Korea Republic Jun '26", "105867773088320": "National Team Selection Korea Republic Jun '26", "105867773111889": "National Team Selection Korea Republic Jun '26", "105867773075969": "National Team Selection Korea Republic Jun '26", "105868041511388": "National Team Selection Iraq Jun '26", "105862353955202": "National Team Captains 11 Jun '26", "106776108377423": "J.LEAGUE Monthly MVPs May '26", "105844100317226": "J.LEAGUE Monthly MVPs May '26", "105844100446407": "J.LEAGUE Monthly MVPs May '26", "105844100464385": "J.LEAGUE Monthly MVPs May '26", "105844100476247": "J.LEAGUE Monthly MVPs May '26", "55070876085214": "POTS Trendyol Süper Lig 25-26", "55070876036641": "POTS Trendyol Süper Lig 25-26", "55070876087661": "POTS Trendyol Süper Lig 25-26", "55070876094096": "POTS Trendyol Süper Lig 25-26", "55070876094622": "POTS Trendyol Süper Lig 25-26", "55070876022532": "POTS Trendyol Süper Lig 25-26", "55070876096721": "POTS Trendyol Süper Lig 25-26", "55070876100065": "POTS Trendyol Süper Lig 25-26", "55070876118921": "POTS Trendyol Süper Lig 25-26", "55070876086138": "POTS Trendyol Süper Lig 25-26", "55070876084691": "POTS Trendyol Süper Lig 25-26", "55070876121649": "POTS Trendyol Süper Lig 25-26", "55070876083368": "POTS Trendyol Süper Lig 25-26", "105856716881894": "Italy Selection 11 Jun '26", "105856716870918": "Italy Selection 11 Jun '26", "105856716881856": "Italy Selection 11 Jun '26", "105856716914308": "Italy Selection 11 Jun '26", "105856716932292": "Italy Selection 11 Jun '26", "105856716927847": "Italy Selection 11 Jun '26", "106779329486937": "Trendyol Süper Lig Monthly MVPs May '26", "105847590083429": "Japan Selection 1 Jun '26", "105847590101443": "Japan Selection 1 Jun '26", "105847590072811": "Japan Selection 1 Jun '26", "105847590087017": "Japan Selection 1 Jun '26", "105847590096866": "Japan Selection 1 Jun '26", "105847590083368": "Japan Selection 1 Jun '26", "105847590126330": "Japan Selection 1 Jun '26", "105852237357787": "National Team Selection Egypt Jun '26", "106775839950376": "J.LEAGUE Monthly MVPs Apr '26", "105843832018243": "J.LEAGUE Monthly MVPs Apr '26", "105843831987163": "J.LEAGUE Monthly MVPs Apr '26", "105843831980149": "J.LEAGUE Monthly MVPs Apr '26", "105843832031923": "J.LEAGUE Monthly MVPs Apr '26", "105846516353374": "Starter Set 28 May '26", "105846516380154": "Starter Set 28 May '26", "88043608522885": "Master League Sprint 28 May '26", "105853495722117": "Master League Sprint 28 May '26", "55070607675511": "POTS English League 25-26", "55070607652807": "POTS English League 25-26", "55070607654887": "POTS English League 25-26", "55070607666523": "POTS English League 25-26", "55070607667189": "POTS English League 25-26", "55070607578576": "POTS English League 25-26", "106779061108686": "Trendyol Süper Lig Monthly MVPs Apr '26", "106779061141038": "Trendyol Süper Lig Monthly MVPs Apr '26", "105848126879277": "Trendyol Süper Lig Monthly MVPs Apr '26", "105848126937444": "Trendyol Süper Lig Monthly MVPs Apr '26", "105848126997315": "Trendyol Süper Lig Monthly MVPs Apr '26", "105851348229244": "National Team Selection Malaysia May '26", "105851348238214": "National Team Selection Malaysia May '26", "105851968940938": "National Team Selection Morocco Jun '26", "105851968962348": "National Team Selection Morocco Jun '26", "105851968968056": "National Team Selection Morocco Jun '26", "105851968918079": "National Team Selection Morocco Jun '26", "105862890900513": "Highlight May '26", "105862622460669": "Highlight May '26", "105862639181784": "Highlight May '26", "105862890947646": "Highlight May '26", "105862639229509": "Highlight May '26", "105862890829790": "Highlight May '26", "105860290457086": "National Team Selection Senegal Jun '26", "105860290487884": "National Team Selection Senegal Jun '26", "105860290475507": "National Team Selection Senegal Jun '26", "105860290435572": "National Team Selection Senegal Jun '26", "105860290422217": "National Team Selection Senegal Jun '26", "105861062202761": "National Team Selection Indonesia 21 May '26", "105861062222485": "National Team Selection Indonesia 21 May '26", "105861062232195": "National Team Selection Indonesia 21 May '26", "52901380730932": "POTW 21 May '26", "52901380679835": "POTW 21 May '26", "52901380726959": "POTW 21 May '26", "52901380730939": "POTW 21 May '26", "105859938144575": "National Teams Selection Guardians 25 May '26", "105845711053470": "European Clubs Selection Guardians 14 May '26", "105845711080004": "European Clubs Selection Guardians 14 May '26", "105845711022546": "European Clubs Selection Guardians 14 May '26", "105845711048063": "European Clubs Selection Guardians 14 May '26", "105845711054401": "European Clubs Selection Guardians 14 May '26", "106781208610214": "Starter Set 14 May '26", "105861280210106": "European Clubs Selection 14 May '26", "105861280309819": "European Clubs Selection 14 May '26", "105861280331812": "European Clubs Selection 14 May '26", "105801150744415": "Chelsea B Selection 18 May '26", "105801150744927": "Chelsea B Selection 18 May '26", "105801150782703": "Chelsea B Selection 18 May '26", "105801150756139": "Chelsea B Selection 18 May '26", "105801150771407": "Chelsea B Selection 18 May '26", "105801150768600": "Chelsea B Selection 18 May '26", "53982907202719": "POTM Trendyol Süper Lig 14 May '26", "53982907212742": "POTM Trendyol Süper Lig 14 May '26", "53982907213525": "POTM Trendyol Süper Lig 14 May '26", "53982907189183": "POTM Trendyol Süper Lig 14 May '26", "53982907190851": "POTM Trendyol Süper Lig 14 May '26", "53982907196589": "POTM Trendyol Süper Lig 14 May '26", "52901112298509": "POTW 14 May '26", "52901112304532": "POTW 14 May '26", "52901112311349": "POTW 14 May '26", "52901112285078": "POTW 14 May '26", "105845979470381": "Italian League 25-26 Season's Best", "105845979482252": "Italian League 25-26 Season's Best", "55070070849362": "POTS Liga Super Malaysia 25-26", "55070070840446": "POTS Liga Super Malaysia 25-26", "55070070841296": "POTS Liga Super Malaysia 25-26", "55070070799147": "POTS Liga Super Malaysia 25-26", "55070070775711": "POTS Liga Super Malaysia 25-26", "55070070799144": "POTS Liga Super Malaysia 25-26", "55070070814429": "POTS Liga Super Malaysia 25-26", "55070070730712": "POTS Liga Super Malaysia 25-26", "55070070799156": "POTS Liga Super Malaysia 25-26", "55070070810490": "POTS Liga Super Malaysia 25-26", "55070070840967": "POTS Liga Super Malaysia 25-26", "55070070825616": "POTS Liga Super Malaysia 25-26", "55070070849451": "POTS Liga Super Malaysia 25-26", "55069802280907": "POTS Italian League 25-26", "55069802375077": "POTS Italian League 25-26", "55069802354280": "POTS Italian League 25-26", "55069802359885": "POTS Italian League 25-26", "55069802401513": "POTS Italian League 25-26", "55069802348081": "POTS Italian League 25-26", "55069802351276": "POTS Italian League 25-26", "55069802352350": "POTS Italian League 25-26", "55069802353778": "POTS Italian League 25-26", "55069802390795": "POTS Italian League 25-26", "55069802396052": "POTS Italian League 25-26", "55069802357576": "POTS Italian League 25-26", "88040387251694": "J1 LEAGUE Selection 7 May '26", "88040387132864": "J1 LEAGUE Selection 7 May '26", "105845442630288": "J1 LEAGUE Selection 7 May '26", "105862085581069": "Highlight 9 May '26", "105862085519427": "Highlight 9 May '26", "105862085519640": "Highlight 9 May '26", "105837926394281": "Standout Guardians 25-26 Season's Best"};
}
const FROWNOME_N2I={"Altura":0,"Altura salto":15,"Compr. perna":8,"Coxa":9,"Panturrilha":12,"Cintura":10,"Peito":5,"Larg. ombro":3,"Alt. ombro":7,"Compr. braço":2,"Tam. braço":11,"Compr. pescoço":4,"Tam. pescoço":6};

/* o mapa vem como nome->indice; a reconstrucao precisa de indice->nome */
const FROWIDX=(()=>{const o={};for(const k in FROWNOME_N2I)o[FROWNOME_N2I[k]]=k;
 /* os 5 que nao apareciam no frows dos cards antigos.
    fisVals = [altura, peso] + as 16 do playerModel  ->  indice = posicao em MED + 2 */
 o[1]='Peso'; o[13]='Cobertura pernas'; o[14]='Cobertura braço';
 o[16]='Colisão do tronco'; o[17]='Altura no drible';
 return o;})();
/* Tabelas históricas permanecem inertes para comparação visual. Builds
   canônicas só usam corpo e resultados presentes no próprio DTO publicado. */
const FIS_F=(()=>{const R={};for(const f in FIS_P){const L=FIS_P[f];
 const fa=Math.min(85,(FIS_KON[f]||3.84)*FIS_K);
 const tot=L.slice(1).reduce((s,p)=>s+p[3],0)||1;
 R[f]=L.map((p,i)=>i===0?[p[0],p[1],p[2],fa]:[p[0],p[1],p[2],p[3]/tot*(100-fa)]);}
 return R;})();
function fisVals(c){
 const m=c&&(c.corpo_valores||c.corpoValores);
 if(Array.isArray(m)&&m.every(x=>typeof x==='number'))return m.slice();
 return null;
}
let MODO_ADM=1;   /* 1 = administrador (vê tudo) · 0 = usuário */
function toggleFicha(){const f=document.getElementById('fichasis');if(!f)return;
 f.style.display=f.style.display==='none'?'block':'none';}
function toggleModo(){MODO_ADM=MODO_ADM?0:1;
 try{localStorage.setItem('encaixe_adm',MODO_ADM?'1':'0')}catch(e){}
 document.documentElement.dataset.modo=MODO_ADM?'adm':'user';
 const b=document.getElementById('modobt');
 if(b){b.textContent=MODO_ADM?'⚙ administrador':'👤 usuário';
  b.style.borderColor=MODO_ADM?'#f0a531':'#22c58b';b.style.color=MODO_ADM?'#f0a531':'#22c58b';}
 render();}
let FIS_MODO=0;   /* 0 = corte seco (oficial) · 1 = proporcional · 2 = caudas por função */
let FIS_PROP=0;   /* a medida em si pontua proporcional nos modos 1 e 2 */
const FIS_TOL=0.15;      /* a que distância relativa do alvo o peso zera */
/* ALTURA CONTÍNUA — só nas funções onde ser alto é o ofício.
   Aqui não existe "passou/não passou": cada centímetro acima do alvo soma,
   cada centímetro abaixo TIRA. É a única medida que pode ficar negativa. */
const ALT_FUNC={"Goleiro ofensivo":1,"Goleiro defensivo":1,
                "Centroavante fixo":1};
let ALT_PASSO=6;   /* quantos cm valem uma faixa inteira do peso da altura */
let ALT_ON=1;
function fisEspelho(c){const L=FIS_F[c.tipo],v=fisVals(c);if(!L||!v)return null;
 let s=0;
 for(const p of L){const x=v[p[0]],a=p[1],maior=p[2];
  if(ALT_ON&&p[0]===0&&ALT_FUNC[c.tipo]){
   let f=(x-a)/ALT_PASSO; f=Math.max(-1.5,Math.min(1.5,f));
   s+=p[3]*(f>=0?1+f*0.5:f);      /* acima premia devagar, abaixo pune direto */
   continue;}
  if(maior? x>=a : x<=a){s+=p[3];continue;}
  if(!FIS_PROP||!a)continue;
  const d=Math.abs(maior?(a-x):(x-a))/Math.abs(a);
  const f=1-d/FIS_TOL;
  if(f>0)s+=p[3]*f;}
 return s;}
/* Apenas confere o payload publicado. O navegador não reconstrói nem completa
   um resultado oficial com catálogos locais. */
window._pos_D=function(){ let incompletas=0;
 for(const c of D){ if(c.id==='MOLDE')continue;
  if(!Array.isArray(c.frows))incompletas++;}
 if(incompletas)console.warn('[clube_novo] '+incompletas+' builds publicadas sem frows declarado');
};window._pos_D();
const FIS_NOMES=['corpo: corte seco (oficial)','corpo: proporcional','corpo: só as pontas'];
const FIS_CORES=['#8b949e','#f0a531','#22c58b'];
function toggleProp(){
 FIS_MODO=(FIS_MODO+1)%3;
 FIS_PROP=FIS_MODO===0?0:1;
 FIS_CORTES=null;
 for(const c of D){delete c._fb;delete c._n;}
 const b=document.getElementById('propbt');
 if(b){b.textContent=FIS_NOMES[FIS_MODO];
       b.style.borderColor=FIS_CORES[FIS_MODO];
       b.style.color=FIS_CORES[FIS_MODO];}
 traducaoViva();render();}
/* MODO 2 — caudas: prêmio/punição só nos extremos DA PRÓPRIA FUNÇÃO.
   Quem está no miolo (o meio 50%) não ganha nem perde. Cortes por percentil. */
let FIS_CORTES=null;
function fisCortes(){
 if(FIS_CORTES)return FIS_CORTES;
 const porF={};
 for(const c of D){if(c.id==='MOLDE')continue;const e=fisEspelho(c);
  if(e!==null)(porF[c.tipo]=porF[c.tipo]||[]).push(e);}
 FIS_CORTES={};
 for(const f in porF){const a=porF[f].sort((x,y)=>x-y),q=k=>a[Math.min(a.length-1,Math.floor(a.length*k))];
  FIS_CORTES[f]={p10:q(.10),p25:q(.25),p75:q(.75),p90:q(.90),n:a.length};}
 return FIS_CORTES;}

  /* ===== MOLDE DO FISICO - 10/08/2026 - injetado pelo gera_encaixe.py ===== */
  /* 10/08 · FECHADO PELO LUIS: de -1,5 a +1,5 (amplitude 3 pontos). */
  let CORPO_MAX = 1.5;
  const MF_BAN={"Altura":[171,178,184,191],"Coxa":[5,7,8,10],"Panturrilha":[4,6,8,10],
   "Cintura":[3,5,7,8],"Peito":[3,5,7,9],"Tam. bra\u00e7o":[4,6,7,9],"Tam. pesco\u00e7o":[5,7,9,11],
   "Compr. perna":[5,7,10,12],"Compr. bra\u00e7o":[3,5,7,9],"Compr. pesco\u00e7o":[4,5,7,8],
   "Larg. ombro":[5,7,9,11],"Alt. ombro":[3,6,8,11]};
  const MF_BAN_GK_ALT=[179,184,189,194];
  const MF_A=["Altura","Coxa","Panturrilha","Cintura","Peito","Tam. bra\u00e7o","Tam. pesco\u00e7o"];
  const MF_B=["Compr. perna","Compr. bra\u00e7o","Compr. pesco\u00e7o"];
  const MF_C={"Larg. ombro":-1,"Alt. ombro":1};
  const MF_ORD=MF_A.concat(MF_B).concat(Object.keys(MF_C));
  const MF_PESO=m=>m==="Altura"?5:1;
  const MF_TIPO={"Falso nove":["M","L"],"Zagueiro de sa\u00edda":["G","L"],"Zagueiro de combate":["G","L"],
   "Lateral defensivo":["G","L"],"Volante de conten\u00e7\u00e3o":["G","L"],"Centroavante fixo":["G","L"],
   "Centroavante m\u00f3vel":["M","L"],"Atacante finalizador":["M","L"],"Ala finalizador":["M","L"],
   "Atacante criador":["M","L"],"Atacante infiltrador":["M","L"],"Ala cruzador":["M","L"],
   "Lateral ofensivo":["M","L"],"Meia ofensivo":["M","C"],"Meia armador":["M","C"],
   "Meia de arranque":["M","C"],"Volante de constru\u00e7\u00e3o":["M","C"],
   "Goleiro ofensivo":["GK","GK"],"Goleiro defensivo":["GK","GK"],"Meia central armador":["M","C"],"Meia central de chegada":["M","C"],"Meia de lado por dentro":["M","L"],"Meia de lado por fora":["M","L"],"Meia lateral atacante":["M","L"],"Meia lateral cruzador":["M","L"],"Meia ofensivo armador":["M","C"],"Segundo atacante":["M","L"],"Ponta criadora":["M","L"],"Ponta finalizadora":["M","L"]};
  const MF_GK={"Altura":1,"Coxa":-1,"Panturrilha":-1,"Cintura":-1,"Peito":-1,"Tam. bra\u00e7o":-1,
   "Tam. pesco\u00e7o":-1,"Compr. perna":1,"Compr. bra\u00e7o":1,"Compr. pesco\u00e7o":1,
   "Larg. ombro":-1,"Alt. ombro":1};
  const MF_EXC={"Centroavante fixo|Larg. ombro":1,"Meia ofensivo|Alt. ombro":-1};
  /* 10/08 · DIRECAO POR FUNCAO — cada uma das 18 pontua conforme o tipo
     fisico que ELA exige. Medido nos 40 melhores cards de cada funcao do
     proprio motor: desvio da media global / desvio-padrao, corte em 0,20.
     +1 = maior e melhor · -1 = menor e melhor · 0 = nao pesa nessa funcao.
     Antes eram 4 moldes (G/L, M/L, M/C, GK) para 18 funcoes — por isso o
     percentual saia igual em funcoes diferentes. Agora sao 17 perfis. */
  const MF_DIRF={"Falso nove": {"Altura": -1, "Coxa": 1, "Panturrilha": 1, "Cintura": -1, "Peito": 1, "Tam. braço": 1, "Tam. pescoço": 1, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 1, "Alt. ombro": -1}, "Centroavante fixo": {"Altura": 1, "Coxa": 0, "Panturrilha": 1, "Cintura": -1, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": -1}, "Centroavante móvel": {"Altura": -1, "Coxa": 1, "Panturrilha": 1, "Cintura": 1, "Peito": 1, "Tam. braço": 1, "Tam. pescoço": 1, "Compr. perna": 0, "Compr. braço": 1, "Compr. pescoço": 0, "Larg. ombro": 1, "Alt. ombro": -1}, "Goleiro defensivo": {"Altura": -1, "Coxa": -1, "Panturrilha": -1, "Cintura": 0, "Peito": -1, "Tam. braço": 1, "Tam. pescoço": 1, "Compr. perna": 1, "Compr. braço": 1, "Compr. pescoço": 1, "Larg. ombro": 1, "Alt. ombro": -1}, "Goleiro ofensivo": {"Altura": 1, "Coxa": -1, "Panturrilha": 1, "Cintura": 0, "Peito": -1, "Tam. braço": 1, "Tam. pescoço": -1, "Compr. perna": 1, "Compr. braço": 1, "Compr. pescoço": 1, "Larg. ombro": 1, "Alt. ombro": -1}, "Lateral defensivo": {"Altura": -1, "Coxa": 1, "Panturrilha": 1, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 1, "Compr. perna": 0, "Compr. braço": 0, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": -1}, "Lateral ofensivo": {"Altura": -1, "Coxa": 0, "Panturrilha": 1, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": 0}, "Meia armador": {"Altura": -1, "Coxa": 0, "Panturrilha": 1, "Cintura": -1, "Peito": -1, "Tam. braço": -1, "Tam. pescoço": 1, "Compr. perna": -1, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": -1}, "Meia de arranque": {"Altura": -1, "Coxa": -1, "Panturrilha": 1, "Cintura": -1, "Peito": -1, "Tam. braço": -1, "Tam. pescoço": 1, "Compr. perna": -1, "Compr. braço": -1, "Compr. pescoço": -1, "Larg. ombro": 0, "Alt. ombro": 0}, "Ala finalizador": {"Altura": -1, "Coxa": 0, "Panturrilha": 0, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 1, "Compr. perna": 0, "Compr. braço": 0, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": 0}, "Ala cruzador": {"Altura": 1, "Coxa": 0, "Panturrilha": 1, "Cintura": 1, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": -1}, "Meia ofensivo": {"Altura": -1, "Coxa": 1, "Panturrilha": 1, "Cintura": 1, "Peito": 1, "Tam. braço": -1, "Tam. pescoço": 1, "Compr. perna": -1, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": -1}, "Atacante criador": {"Altura": -1, "Coxa": 0, "Panturrilha": 0, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 1, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 1, "Larg. ombro": -1, "Alt. ombro": -1}, "Atacante finalizador": {"Altura": -1, "Coxa": 0, "Panturrilha": 0, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": 0, "Compr. pescoço": 1, "Larg. ombro": 0, "Alt. ombro": -1}, "Atacante infiltrador": {"Altura": -1, "Coxa": 1, "Panturrilha": 1, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 1, "Alt. ombro": -1}, "Volante de construção": {"Altura": -1, "Coxa": 1, "Panturrilha": 1, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": 0, "Compr. pescoço": 1, "Larg. ombro": 0, "Alt. ombro": -1}, "Volante de contenção": {"Altura": 1, "Coxa": 1, "Panturrilha": 0, "Cintura": -1, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 1, "Compr. perna": 0, "Compr. braço": 0, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": -1}, "Zagueiro de combate": {"Altura": 1, "Coxa": 0, "Panturrilha": 0, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": 0}, "Zagueiro de saída": {"Altura": 1, "Coxa": 0, "Panturrilha": 0, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 1, "Larg. ombro": -1, "Alt. ombro": -1},"Meia central armador":{"Altura": -1, "Coxa": 0, "Panturrilha": 1, "Cintura": -1, "Peito": -1, "Tam. braço": -1, "Tam. pescoço": 1, "Compr. perna": -1, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": -1},"Meia central de chegada":{"Altura": -1, "Coxa": -1, "Panturrilha": 1, "Cintura": -1, "Peito": -1, "Tam. braço": -1, "Tam. pescoço": 1, "Compr. perna": -1, "Compr. braço": -1, "Compr. pescoço": -1, "Larg. ombro": 0, "Alt. ombro": 0},"Meia de lado por dentro":{"Altura": -1, "Coxa": 0, "Panturrilha": 0, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 1, "Compr. perna": 0, "Compr. braço": 0, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": 0},"Meia de lado por fora":{"Altura": 1, "Coxa": 0, "Panturrilha": 1, "Cintura": 1, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": -1},"Meia lateral atacante":{"Altura": -1, "Coxa": 0, "Panturrilha": 0, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 1, "Compr. perna": 0, "Compr. braço": 0, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": 0},"Meia lateral cruzador":{"Altura": 1, "Coxa": 0, "Panturrilha": 1, "Cintura": 1, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": -1},"Meia ofensivo armador":{"Altura": -1, "Coxa": 1, "Panturrilha": 1, "Cintura": 1, "Peito": 1, "Tam. braço": -1, "Tam. pescoço": 1, "Compr. perna": -1, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": -1},"Segundo atacante":{"Altura": -1, "Coxa": 1, "Panturrilha": 1, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 1, "Alt. ombro": -1},"Ponta criadora":{"Altura": -1, "Coxa": 0, "Panturrilha": 0, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 1, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 1, "Larg. ombro": -1, "Alt. ombro": -1},"Ponta finalizadora":{"Altura": -1, "Coxa": 0, "Panturrilha": 0, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": 0, "Compr. pescoço": 1, "Larg. ombro": 0, "Alt. ombro": -1}};
  const MF_FAIXA={"Falso nove":[-15,16],"Goleiro ofensivo":[-12,22],"Goleiro defensivo":[-12,22],
   "Zagueiro de sa\u00edda":[-11,16],"Zagueiro de combate":[-11,16],"Lateral defensivo":[-19,14],
   "Lateral ofensivo":[-16,15],"Volante de conten\u00e7\u00e3o":[-19,10],"Volante de constru\u00e7\u00e3o":[-12,20],
   "Meia armador":[-7,22],"Meia de arranque":[-7,22],
   "Meia ofensivo":[-8,20],"Ala finalizador":[-8,18],"Ala cruzador":[-8,18],
   "Atacante criador":[-8,19],"Atacante finalizador":[-8,19],"Atacante infiltrador":[-12,18],
   "Centroavante fixo":[-17,16],"Centroavante m\u00f3vel":[-15,16],"Meia central armador":[-7,22],"Meia central de chegada":[-7,22],"Meia de lado por dentro":[-8,18],"Meia de lado por fora":[-8,18],"Meia lateral atacante":[-8,18],"Meia lateral cruzador":[-8,18],"Meia ofensivo armador":[-8,20],"Segundo atacante":[-12,18],"Ponta criadora":[-8,19],"Ponta finalizadora":[-8,19]};
  const MF_ARQIDX={"Altura":0,"Coxa":1,"Panturrilha":2,"Cintura":3,"Peito":4,"Tam. bra\u00e7o":5,
   "Tam. pesco\u00e7o":6,"Compr. perna":7,"Compr. bra\u00e7o":8,"Compr. pesco\u00e7o":9,
   "Larg. ombro":10,"Alt. ombro":11};
  const MF_IDX={"Altura":0,"Coxa":9,"Panturrilha":12,"Cintura":10,"Peito":5,"Tam. bra\u00e7o":11,
   "Tam. pesco\u00e7o":6,"Compr. perna":8,"Compr. bra\u00e7o":2,"Compr. pesco\u00e7o":4,
   "Larg. ombro":3,"Alt. ombro":7};
  function mfMedidas(c){
   const bruto=c&&(c.corpo_medidas||c.corpoMedidas); if(!bruto)return null;
   const o={};
   if(Array.isArray(bruto)){
    for(const m in MF_ARQIDX){const x=bruto[MF_ARQIDX[m]];if(typeof x!=="number")return null;o[m]=x;}
    return o;
   }
   for(const m in MF_ARQIDX){const x=bruto[m];if(typeof x!=="number")return null;o[m]=x;}
   return o;
  }
  function mfDir(m,f){const dd=MF_DIRF[f]; if(dd&&dd[m]!==undefined)return dd[m];
   if(MF_EXC[f+"|"+m]!==undefined)return MF_EXC[f+"|"+m];
   const t=MF_TIPO[f]; if(!t)return 0;
   if(t[0]==="GK")return MF_GK[m];
   if(MF_A.indexOf(m)>=0)return t[0]==="G"?1:-1;
   if(MF_B.indexOf(m)>=0)return t[1]==="L"?1:-1;
   return MF_C[m];}
  function mfCortes(m,f){const t=MF_TIPO[f];
   return (t&&t[0]==="GK"&&m==="Altura")?MF_BAN_GK_ALT:MF_BAN[m];}
  function mfNota(v,c){return v<=c[0]?-2:v<=c[1]?-1:v<=c[2]?0:v<=c[3]?1:2;}
  function mfFaixaTxt(m,f,n){const c=mfCortes(m,f);
   return n===0?("\u2264"+c[0]):n===1?((c[0]+1)+"-"+c[1]):n===2?((c[1]+1)+"-"+c[2]):n===3?((c[2]+1)+"-"+c[3]):("\u2265"+(c[3]+1));}
  /* o ALVO da linha: com +1 o ideal e o topo, com -1 e o piso, com 0 nao pesa */
  function mfAlvoTxt(m,f){const d=mfDir(m,f); if(!d)return "\u2014";
   return mfFaixaTxt(m,f,d>0?4:0);}
  function mfSoma(card){const v=mfMedidas(card); if(!v||!MF_TIPO[card.tipo])return null;
   let s=0; for(const m of MF_ORD){const x=v[m]; if(typeof x!=="number")continue;
    s+=mfNota(x,mfCortes(m,card.tipo))*mfDir(m,card.tipo)*MF_PESO(m);}
   return s;}
  const MF_TETO=(f)=>{let t=0; for(const m of MF_ORD){if(mfDir(m,f))t+=MF_PESO(m)*2;} return t||1;};
  function mfPct(card){const s=mfSoma(card); if(s===null)return null;
   const te=MF_DIRF[card.tipo]?MF_TETO(card.tipo):null;
   if(te){return Math.max(-100,Math.min(100,s/te*100));}
   const fa=MF_FAIXA[card.tipo]; if(!fa)return null;
   const p=s>=0? s/fa[1]*100 : s/Math.abs(fa[0])*100;
   return Math.max(-100,Math.min(100,p));}
  function mfFrows(card){const v=mfMedidas(card); if(!v||!MF_TIPO[card.tipo])return [];
   return MF_ORD.map(m=>{const x=v[m],d=mfDir(m,card.tipo),pe=MF_PESO(m);
    const n=(typeof x==="number")?mfNota(x,mfCortes(m,card.tipo)):0;
    return [m,d?pe:0,mfAlvoTxt(m,card.tipo),x,n,d,n*d*pe];});}
  (function(){let n=0;
   for(const c of D){ if(c.id==="MOLDE")continue;
    if(mfMedidas(c))n++;}
   const sem=D.filter(c=>c.id!=="MOLDE"&&!mfMedidas(c)).length;
   console.log("%cMOLDE DO FISICO - "+n+" linhas com corpo canônico - "+sem+" sem corpo declarado"
    +" - CORPO_MAX="+CORPO_MAX,
    "color:"+(sem?"#f0a531":"#22c58b")+";font-weight:700");})();
  /* ===== FIM DO MOLDE DO FISICO ===== */
  function fisBonus(c){const p=mfPct(c); if(p===null)return 0;
   return p/100*CORPO_MAX;}
  /* regua ANTIGA do Bloco 4, desativada em 10/08/2026:
  function fisBonus(c){const e=fisEspelho(c);if(e===null)return 0;
 if(FIS_MODO===2){const k=fisCortes()[c.tipo];if(!k)return 0;
  if(e>=k.p90)return 2*FIS_PT;
  if(e>=k.p75)return 1*FIS_PT;
  if(e<=k.p10)return -2*FIS_PT;
  if(e<=k.p25)return -1*FIS_PT;
  return 0;}
 return e>=FIS_HI-1e-6?2*FIS_PT:(e>=FIS_MID?1*FIS_PT:(e<=FIS_LO?-1*FIS_PT:0));}
  fim da regua antiga */

const BKV=BK.map((b,i)=>[b,i]).filter(([b,i])=>B3ON||i!==2);
const SUG=[100,0,0,0,0];
const PRE={of:[50,25,0,15,10],ia:[50,25,4,15,10],c:[55,20,0,15,10],a2:[60,20,0,10,10],b2:[49,14,0,19,14],e2:[40,30,0,20,10],a:[40,15,5,25,15],b:[45,12.5,5,25,12.5],e:[32,16,5,32,16],sep:[22,13,0,31,34]};
let W=SUG.slice();
const S={tipo:'★ GERAL',sort:'nota',dir:-1,view:'cards',orig:''};
const isGeral=t=>t==='★ GERAL'||t==='★ GERAL · por jogador'||t==='★ GERAL · mix';
/* O banco conserva as chaves históricas; a tela mostra o vocabulário atual.
   Nunca alterar `c.tipo`: ele continua sendo a chave usada para buscar a
   linha correta. */
const NOME_FUNCAO_RANKING={
 "Meia central armador":"Meia armador","Meia central de chegada":"Meia de arranque",
 "Meia de ligação armador":"Meia armador","Meia de ligação avançado":"Meia de arranque",
 "Meia de lado por dentro":"Ala finalizador","Meia de lado por fora":"Ala cruzador",
 "Meia lateral atacante":"Ala finalizador","Meia lateral cruzador":"Ala cruzador",
 "Ala atacante":"Ala finalizador","Meia ofensivo armador":"Meia ofensivo",
 "Segundo atacante":"Atacante infiltrador","Ponta criadora":"Atacante criador",
 "Ponta finalizadora":"Atacante finalizador"
};
const nomeFuncaoRanking=t=>NOME_FUNCAO_RANKING[t]||t;
const nz=s=>(s||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase();
const MS=new Set(METAS.map(nz));
const isM=c=>MS.has(nz(c.nome));
let CMODE=0;
function recalcCard(c){
 if(!c.cdelta)return;
 const on=Math.max(CMODE,c.cmode||0);
 c.arows.forEach(r=>{
  if(r[5]===undefined)r[5]=r[3];
  const d=c.cdelta[r[0]]||0;
  const add=on===0?0:(on===1?Math.round(d/2):d);
  r[3]=Math.min(99,r[5]+add);
  r[4]=r[3]-r[2];
 });
 let s=0;c.arows.forEach(r=>{if(r[1])s+=ptsAttr(r);});
 c.b1=Math.round(s*10)/10;
}
function recalcB1(){for(const c of D)recalcCard(c);}
function toggleCondCard(key){
 const [id,tipo]=key.split("|");const c=D.find(x=>String(x.id)===id&&x.tipo===tipo);if(!c)return;_marca(key);
 c.cmode=((c.cmode||0)+1)%3;recalcCard(c);traducaoViva();render();reabrir(key);
}
function tetoB1(t){
 const c0=D.find(x=>x.tipo===t&&x.id!=="MOLDE");if(!c0)return 1;let te=0;
 for(const r of c0.arows){if(!r[1])continue;const d=P.DEG.length;
  for(let k=1;k<=d;k++)te+=P.DEG[k-1]*r[1];}
 return te||1;}
/* ===== v158 · FAIXAS ANCORADAS NO MOLDE OTIMIZADO DE CADA FUNCAO =====
   Ideia do Luis: "se a gente otimizar o molde com o nosso motor ele vai ter um
   numero, por que a gente nao usa esse numero como ancora de cada funcao?"

   Foi o que faltava. Ancorar no molde EXATO nao servia: ele da 92 em todas as 18
   funcoes por definicao (b1=0), e foi isso que apagou a diferenca entre elas na
   v155 e encheu o top 10 de goleiro. Ja o molde OTIMIZADO — o molde passado pelo
   nosso motor, com o orcamento mediano da funcao — separa: de 114,1 (Goleiro
   ofensivo) a 125,2 (Ala finalizador). 11,1 pontos de amplitude, medidos.

   Regra: de 92 pra cima nao se toca (topo identico ao de hoje). Abaixo, a nota
   cai ate 40 numa curva cuja VELOCIDADE sai da ancora daquela funcao — funcao
   que estica mais tem faixa mais larga. O k de cada uma e calibrado pra colar
   exatamente em 92, sem degrau.

   Medido: topo de cada funcao identico ao de hoje · mediana ~84 nas 18 ·
   pior card de hoje entre 41,8 e 58,8 · carta 40-em-tudo entre 40,2 e 46,5.
   Distribuicao: 42 cards em 40-50, 486 em 50-60, 1.429 em 60-70. */
let PISO_ON=1;
const FX_ANC={"Falso nove": 116.8,"Goleiro ofensivo": 114.1, "Goleiro defensivo": 117.1, "Zagueiro de saída": 117.2, "Zagueiro de combate": 120.1, "Lateral ofensivo": 125.1, "Lateral defensivo": 120.5, "Volante de contenção": 119.2, "Volante de construção": 119.9, "Meia armador": 115.2, "Meia de arranque": 119.7, "Meia ofensivo": 116.7, "Atacante infiltrador": 115.5, "Ala finalizador": 125.2, "Ala cruzador": 122.1, "Atacante finalizador": 115.6, "Atacante criador": 114.8, "Centroavante móvel": 116.8, "Centroavante fixo": 119,"Meia central armador":115.2,"Meia central de chegada":119.7,"Meia de lado por dentro":125.2,"Meia de lado por fora":122.1,"Meia lateral atacante":125.2,"Meia lateral cruzador":122.1,"Meia ofensivo armador":116.7,"Segundo atacante":115.5,"Ponta criadora":114.8,"Ponta finalizadora":115.6};
const FX_K={"Falso nove": 0.44521,"Goleiro ofensivo": 0.45574, "Goleiro defensivo": 0.44406, "Zagueiro de saída": 0.44369, "Zagueiro de combate": 0.43297, "Lateral ofensivo": 0.41567, "Lateral defensivo": 0.43154, "Volante de contenção": 0.43624, "Volante de construção": 0.43369, "Meia armador": 0.45139, "Meia de arranque": 0.43442, "Meia ofensivo": 0.44559, "Atacante infiltrador": 0.45022, "Ala finalizador": 0.41534, "Ala cruzador": 0.42588, "Atacante finalizador": 0.44983, "Atacante criador": 0.45296, "Centroavante móvel": 0.44521, "Centroavante fixo": 0.43697,"Meia central armador":0.45139,"Meia central de chegada":0.43442,"Meia de lado por dentro":0.41534,"Meia de lado por fora":0.42588,"Meia lateral atacante":0.41534,"Meia lateral cruzador":0.42588,"Meia ofensivo armador":0.44559,"Segundo atacante":0.45022,"Ponta criadora":0.45296,"Ponta finalizadora":0.44983};
function piso(x,tipo){
 if(!PISO_ON||x>=92) return x;
 const A=FX_ANC[tipo], k=FX_K[tipo];
 if(!A||!k) return x;
 const u=(A-x)/A;
 return Math.round((A-(A-40)*(u/(u+k)))*100)/100;
}
function togglePiso(){PISO_ON=PISO_ON?0:1;
 const b=document.getElementById('pisobt');
 if(b)b.textContent=PISO_ON?'escala: piso 40':'escala: crua (vai a \u22122040)';
 for(const c of D)delete c._n;
 traducaoViva();render();}
function traducaoViva(){
 /* ===== v154 · A REGUA CONGELOU =====
    Ela era recalculada da populacao (sa=20/topo, sb=14/-mediana). Medido: entrar
    7.000 cards piores deslocava a nota de quem JA estava no sistema em 7 a 9
    pontos na media e ate 34 no pior caso — inclusive no top 50. Um card parado
    mudaria de nota sozinho so porque chegou gente pior. Inaceitavel.
    Agora a regua e uma TABELA FIXA, medida em 03/08/2026 com 11.214 linhas.
    Card novo entra na regua que existe; ninguem se mexe. Medido depois de
    congelar: 33.642 cards novos, deslocamento maximo 0,0000.
    Se um dia entrar card MELHOR que o topo de hoje, ele passa de 117,2 — e esta
    certo, e o topo que subiu de verdade. Recalibrar so por decisao, nunca sozinho. */
 const REGUA={"Falso nove": [0.06535948, 0.07106599],"Goleiro ofensivo": [0.08267879, 0.37533512], "Goleiro defensivo": [0.10015023, 1], "Zagueiro de saída": [0.07624857, 0.15037594], "Zagueiro de combate": [0.09965122, 0.07739082], "Lateral ofensivo": [0.0805153, 0.03829322], "Lateral defensivo": [0.07369197, 0.02420052], "Volante de contenção": [0.08240626, 0.04539559], "Volante de construção": [0.07806401, 0.06238859], "Meia armador": [0.07130125, 0.0751073], "Meia de arranque": [0.07220217, 0.09414929], "Meia ofensivo": [0.0625, 0.07216495], "Atacante infiltrador": [0.0575374, 0.04186603], "Ala finalizador": [0.07407407, 0.01931567], "Ala cruzador": [0.07153076, 0.02556144], "Atacante finalizador": [0.05216484, 0.04229607], "Atacante criador": [0.05109862, 0.02908789], "Centroavante móvel": [0.06535948, 0.07106599], "Centroavante fixo": [0.07524454, 0.02060338],"Meia central armador":[0.07130125, 0.0751073],"Meia central de chegada":[0.07220217, 0.09414929],"Meia de lado por dentro":[0.07407407, 0.01931567],"Meia de lado por fora":[0.07153076, 0.02556144],"Meia lateral atacante":[0.07407407, 0.01931567],"Meia lateral cruzador":[0.07153076, 0.02556144],"Meia ofensivo armador":[0.0625, 0.07216495],"Segundo atacante":[0.0575374, 0.04186603],"Ponta criadora":[0.05109862, 0.02908789],"Ponta finalizadora":[0.05216484, 0.04229607]};
 for(const t of [...new Set(D.map(c=>c.tipo))]){
  const cs=D.filter(c=>c.tipo===t&&c.id!=="MOLDE");
  const r=REGUA[t];
  const sa=r?r[0]:(()=>{const v=cs.map(c=>c.b1).sort((a,b)=>a-b);return 20/Math.max(1,v[v.length-1]);})();
  const sb=r?r[1]:1;
  D.filter(c=>c.tipo===t).forEach(c=>{c.b1n=Math.round((92+(c.b1>=0?c.b1*sa:c.b1*sb))*10)/10;});
  /* 🔒 REGRA DO LUIS: quem NAO EVOLUI nao participa do molde.
     Ficam listados e personalizados, mas nao entram na referencia do tipo.
     Sem isso o Goleiro defensivo mostrava modelo 21,5 em vez de 93,8. */
  if(MED[t]){const ev=cs.filter(c=>c.orc);const fonte=(ev.length>=5?ev:cs);
   const w=fonte.map(c=>c.b1n).sort((a,b)=>a-b);
   MED[t].b1n=Math.round(w[Math.floor(w.length/2)]*10)/10;
   MED[t].nEvolui=ev.length;MED[t].nTotal=cs.length;}
 }
}
/* ===== v127 · BARRAS SEM MOTOR =====
   O buildOtimo do arquivo e a versao ANTIGA do motor: nao conhece as 5
   habilidades adicionais nem o tecnico, e a tabela de efeito das 61
   habilidades nunca foi embarcada aqui. Por isso reconstruir o card a
   partir da base dava valor errado.
   Mexer numa barra nao precisa de nada disso: e SOMA. Guardamos o estado
   gravado pelo motor (_ori) e aplicamos so a DIFERENCA de niveis.
   Nenhum ingrediente do motor entra nesta conta. */
/* ===== v130 · TROCA DE TECNICO =====
   Os 62 tecnicos com boost, do treinadores_com_boost.json do Luis. Cada um da
   +1 em 1 ou 2 atributos. Trocar tecnico e delta puro: tira +1 dos boosts do
   tecnico gravado, poe +1 nos do escolhido. Nao usa o motor. */
const TECS=[["Cesc Fabregas",["loftedPass","ballWinning"]],["Cristian Chivu",["speed","stamina"]],["D. Deschamps",["speed","ballControl"]],["D. Deschamps",["speed"]],["D. Stojkovic",["kickingPower"]],["Erik ten Hag",["speed"]],["F. Beckenbauer",["dribbling","defensiveAwareness"]],["F. Beckenbauer",["finishing","kickingPower"]],["Fabio Capello",["finishing","defensiveAwareness"]],["Frank Lampard",["balance"]],["Frank Rijkaard",["tightPossession","balance"]],["Frank Rijkaard",["lowPass"]],["G. P. Gasperini",["physicalContact"]],["G. Southgate",["acceleration"]],["Gennaro Gattuso",["trackingBack","loftedPass"]],["Hansi Flick",["lowPass","dribbling"]],["Hansi Flick",["lowPass","speed"]],["J. Nagelsmann",["dribbling","physicalContact"]],["Johan Cruyff",["acceleration","balance"]],["Johan Cruyff",["tightPossession","jump"]],["Jose Mourinho",["physicalContact","stamina"]],["Jose Mourinho",["trackingBack"]],["Jurgen Klopp",["speed","aggression"]],["L. Spalletti",["defensiveAwareness","stamina"]],["L. de la Fuente",["acceleration"]],["Lionel Scaloni",["lowPass"]],["M. Allegri",["offensiveAwareness","ballControl"]],["Mikel Arteta",["acceleration","setPieceTaking"]],["Mikel Arteta",["acceleration","tightPossession"]],["Mikel Arteta",["lowPass"]],["Niko Kovac",["kickingPower","tightPossession"]],["Okan Buruk",["balance","loftedPass"]],["Olympio H.",["kickingPower"]],["P. Kluivert",["lowPass","ballWinning"]],["Patrick Vieira",["trackingBack"]],["Paulo Fonseca",["physicalContact","kickingPower"]],["Pep Guardiola",["kickingPower","aggression"]],["Pep Guardiola",["tightPossession"]],["R. Martinez",["finishing","offensiveAwareness"]],["R. Martinez",["ballControl","aggression"]],["R. Martinez",["physicalContact"]],["Ronald Koeman",["kickingPower","jump"]],["Ronald Koeman",["lowPass","heading"]],["Ronald Koeman",["ballControl","stamina"]],["Ruben Amorim",["physicalContact","loftedPass"]],["Ruben Amorim",["speed","offensiveAwareness"]],["Rudi Garcia",["ballControl","offensiveAwareness"]],["Simone Inzaghi",["speed","finishing"]],["Simone Inzaghi",["stamina"]],["Stale Solbakken",["heading","physicalContact"]],["Stefano Pioli",["trackingBack"]],["Steven Gerrard",["dribbling"]],["Thomas Tuchel",["lowPass","stamina"]],["Thomas Tuchel",["physicalContact"]],["V. Montella",["acceleration","tightPossession"]],["V. Montella",["stamina"]],["Vincent Kompany",["acceleration","kickingPower"]],["Xabi Alonso",["ballControl","finishing"]],["Xabi Alonso",["acceleration"]],["Xabi Alonso",["acceleration"]],["Xavi Hernandez",["ballControl"]],["Zico",["dribbling"]]];
const TECIDX={offensiveAwareness:0,ballControl:1,dribbling:2,tightPossession:3,lowPass:4,loftedPass:5,
 finishing:6,heading:7,setPieceTaking:8,curl:9,speed:10,acceleration:11,kickingPower:12,jump:13,
 physicalContact:14,balance:15,stamina:16,defensiveAwareness:17,ballWinning:18,trackingBack:19,
 aggression:20,gkAwareness:21,gkCatching:22,gkClearing:23,gkReflexes:24,gkReach:25};
function tecVet(bs){const v=new Array(26).fill(0);
 (bs||[]).forEach(k=>{const i=TECIDX[k];if(i!==undefined)v[i]+=1;});return v;}
function tecAtual(c){return c._tec!==undefined?c._tec:(c.TECB||[]);}
function trocaTec(key,idx){const c=_card(key);if(!c)return;_marca(key);
 c._tecNome = idx==='' ? null : TECS[+idx][0];
 c._tec     = idx==='' ? [] : TECS[+idx][1];
 _grava(c,_lvlDe(c));reabrir(key);}
window.HABEF={"Cabeceio":[0,{"7":[5,0]}],"Liderança":[0,{"19":[2,0]}],"Chute de primeira":[0,{"6":[5,0]}],"Passe de primeira":[0,{"4":[5,0]}],"Arrem. longo do GO":[0,{"5":[3,0],"23":[2,0]}],"Repos. baixa do GO":[0,{"23":[3,0],"4":[2,0]}],"Pegador de pênaltis":[0,{"21":[2,0]}],"Toque de calcanhar":[0,{"4":[2,0]}],"Efeito de longe":[0,{"9":[3,0],"6":[2,0]}],"Espírito guerreiro":[0,{"16":[2,0],"7":[1,0]}],"Curva para fora":[0,{"9":[3,0]}],"Puxada de letra":[0,{"2":[5,0]}],"Finaliz. acrobática":[0,{"6":[5,0]}],"Malícia":[0,{"15":[3,0],"20":[2,0]}],"Chutes com decolagem":[0,{"12":[4,0],"9":[1,0]}],"Finta de letra":[0,{"2":[5,0]}],"Elástico":[0,{"2":[5,0]}],"360 graus":[0,{"2":[5,0]}],"Passe sem olhar":[0,{"4":[2,0]}],"Toque duplo":[0,{"2":[5,0]}],"Especialista em pênalti":[0,{"8":[2,0]}],"De letra":[0,{"5":[2,0]}],"Chapéu":[0,{"2":[5,0]}],"Cruzamento preciso":[0,{"4":[10,0],"5":[10,0]}],"Folha seca":[0,{"9":[4,0],"12":[1,0]}],"Interceptação":[0,{"20":[3,0],"17":[2,0]}],"Passe na medida":[0,{"5":[4,0],"9":[1,0]}],"Precisão à distância":[0,{"6":[10,0]}],"Passe aéreo baixo":[0,{"5":[5,0]}],"Pedalada simples":[0,{"2":[5,0]}],"Controle da cavadinha":[0,{"6":[2,0]}],"Carrinho":[0,{"18":[5,0]}],"Bloqueador":[0,{"17":[3,0],"14":[2,0]}],"Marcação individual":[0,{"20":[2,0],"14":[2,0],"17":[1,0]}],"Arrem. lateral longo":[0,{"5":[2,0]}],"Chute com o peito do pé":[0,{"12":[2,0]}],"Passe em profundidade":[0,{"4":[10,0],"5":[10,0]}],"Controle com a sola":[0,{"3":[3,0]}],"Corte com virada":[0,{"2":[5,0]}],"Superioridade aérea":[0,{"14":[3,0],"13":[2,0]}],"Afastamento acrobático":[0,{"17":[3,0],"18":[2,0]}],"Volta para marcar":[0,{"17":[1,0],"11":[1,0]}],"Super substituto":[0,{"0":[1,0],"6":[1,0]}],"Reposição alta do GO":[0,{"23":[3,0],"5":[2,0]}],"Cruzamento seco":[1,{"4":[2,0]}],"Drible explosivo":[1,{"2":[5,0]}],"Xerifão":[1,{"17":[5,0],"18":[5,0]}],"Passe visionário":[1,{"5":[3,0],"4":[2,0]}],"Desarme de longo alcance":[1,{"18":[5,0]}],"Finalizador nato":[1,{"6":[3,0],"12":[2,0]}],"Passador nato":[1,{"4":[3,0],"5":[2,0]}],"Drible astuto":[1,{"2":[5,0]}],"Cabeçada matadora":[1,{"7":[5,0]}],"Fortaleza aérea":[1,{"14":[3,0],"13":[2,0]}],"Curva descendente":[1,{"9":[5,0]}],"Chute rasteiro forte":[1,{"12":[5,0]}],"Defesa direta (GO)":[1,{"23":[5,0]}],"Força de vontade":[1,{"0":[3,0],"16":[2,0]}],"Grito de garra (GO)":[1,{"21":[3,0],"23":[2,0]}],"Pés magnéticos":[1,{"3":[5,0]}],"Passe inspirador":[1,{"4":[10,0],"5":[10,0]}],"Puxada e tapa":[0,{"2":[5,0]}]};
/* ===== v131 · A CADEIA REAL DO MOTOR (motor3.py, 03/08) =====
   1) v = min(99, base + nivel_da_barra)                 <- TETO 99 AQUI
   2) v = v + add            add = nm + impeto + tecnico <- SEM TETO
   3) v = v + max(0, min(99-v, ceil(v*pct/100) + flat))  <- HABILIDADE, trava em 99
   COMUNS: a maior vale INTEIRA, cada perdedora vale METADE (05/08) · RARAS somam por cima, inteiras. */
function buffDe(hs){const pcC={},pcR={},flC={},flR={};
 (hs||[]).forEach(h=>{const v=HABEF[h];if(!v)return;const rara=v[0]===1;
  for(const i in v[1]){const k=+i,[pct,flat]=v[1][i];
   if(pct){(rara?pcR:pcC)[k]=((rara?pcR:pcC)[k]||[]).concat(pct);}
   if(flat){(rara?flR:flC)[k]=((rara?flR:flC)[k]||[]).concat(flat);}}});
 const out={},ids=new Set([...Object.keys(pcC),...Object.keys(pcR),...Object.keys(flC),...Object.keys(flR)].map(Number));
 for(const i of ids){
  const _meia=a=>{if(!a||!a.length)return 0;const v=a.slice().sort((x,y)=>y-x);return v[0]+v.slice(1).reduce((s,x)=>s+x/2,0);};
  const pct=_meia(pcC[i])+(pcR[i]||[]).reduce((a,b)=>a+b,0);
  const flat=_meia(flC[i])+(flR[i]||[]).reduce((a,b)=>a+b,0);
  if(pct||flat)out[i]=[pct,flat];}
 return out;}
function aplicaBuff(v,pct,flat){return v+Math.max(0,Math.min(99-v,Math.ceil(v*pct/100)+flat));}
function habsAtual(c){return c._habs!==undefined?c._habs:(c.HAB||[]);}
function habsDe(c){return (c.fab||[]).concat(habsAtual(c));}
function _trocaHabs(key,novas){const c=_card(key);if(!c)return;_marca(key);_oriDe(c);
 const lvl=_lvlDe(c);
 const v0=cadeia(c,lvl);
 c._habs=novas;
 const v1=cadeia(c,lvl);
 const vals=(c.sis||v0).map((x,i)=>Math.max(0,Math.min(Math.max(99,x),Math.round(x+(v1[i]-v0[i])))));
 c.sis=vals;c.arows.forEach(r=>{r[3]=vals[r[0]];r[4]=r[3]-r[2];r[5]=r[3];});
 c.b1=notaDe(vals,c.arows);traducaoViva();render();reabrir(key);}
function remHab(key,ix){const c=_card(key);if(!c)return;
 const cur=habsAtual(c).slice();cur.splice(ix,1);_trocaHabs(key,cur);}
function addHab(key,s){const c=_card(key);if(!c||!s)return;
 const cur=habsAtual(c);if(cur.length>=5||cur.includes(s))return;
 _trocaHabs(key,cur.concat([s]));}
function cadeia(c,lvl,addExtra){
 const nm=expand(c.nm), tec=tecVet(tecAtual(c)), bf=buffDe(habsDe(c));
 /* o c.imps do banco esta desencontrado do c.imp; a STRING e a verdade do motor */
 const imp=new Array(26).fill(0);
 String(c.imp||'').split(' + ').map(x=>x.replace(' (cond.)','').replace(' \u2692','').trim()).filter(Boolean)
  .forEach(nome=>{const f=CAT.find(y=>y[0]===nome);if(f)expand(f[2]).forEach((v,i)=>imp[i]+=v);});
 const cb=_contrib(lvl), v=new Array(26).fill(0);
 for(let i=0;i<26;i++){
  let x=Math.min(99,(c.base?c.base[i]:0)+cb[i]);
  x+=nm[i]+imp[i]+tec[i]+((addExtra&&addExtra[i])||0);
  if(bf[i])x=aplicaBuff(x,bf[i][0],bf[i][1]);
  v[i]=x;}
 return v;}
/* ===== v133 · CASCATA POR ETAPA =====
   Devolve o valor do atributo depois de cada etapa da cadeia do motor.
   [0] base · [1] +barras (teto 99) · [2] +impeto · [3] +tecnico · [4] +habilidade */
function _e4nat(c,lvl){const E=etapas(c,lvl),bf=buffDe(c.fab||[]);
 return E.map((e,i)=>bf[i]?aplicaBuff(e[3],bf[i][0],bf[i][1]):e[3]);}
function etapas(c,lvl){
 const nm=expand(c.nm), im=impVet(c), tc=tecVet(tecAtual(c)), bf=buffDe(habsDe(c));
 const cb=_contrib(lvl||_lvlDe(c)), out=[];
 for(let i=0;i<26;i++){
  const e0=c.base?c.base[i]:0;
  const e1=Math.min(99,e0+cb[i]);
  const e2=e1+nm[i]+im[i];
  const e3=e2+tc[i];
  const e4=bf[i]?aplicaBuff(e3,bf[i][0],bf[i][1]):e3;
  out.push([e0,e1,e2,e3,e4]);}
 return out;}
function _oriDe(c){
 if(!c._ori)c._ori={v:c.arows.map(r=>r[3]),lvl:_lvlDe(c),tec:(c.TECB||[]).slice(),imp:c.imp,imps:(c.imps||[]).map(x=>({n:x.n,c:x.c,f:x.f})),
   sisBar:(c.sisBar||[]).map(r=>r.slice()),sobra:c.sobra,b1:c.b1,sis:(c.sis||[]).slice()};
 return c._ori;}
function _contrib(lvl){const v=new Array(26).fill(0);
 for(const b of MBK){const n=lvl[b]||0;if(n)MB[b].forEach(i=>{v[i]+=n;});}return v;}
function valsDeLvl(c,lvl){
 const o=_oriDe(c),cb=_contrib(o.lvl),cn=_contrib(lvl),v=new Array(26).fill(0);
 const tb=tecVet(o.tec),tn=tecVet(tecAtual(c));
 c.arows.forEach((r,k)=>{const i=r[0];
  v[i]=Math.max(0,Math.min(Math.max(99,o.v[k]),o.v[k]+(cn[i]-cb[i])+(tn[i]-tb[i])));});
 return v;}
function restaurarMotor(key){const c=_card(key);if(!c)return;const o=_oriDe(c);
 if(o.sis&&o.sis.length)c.sis=o.sis.slice();
 c.arows.forEach((r,k)=>{r[3]=o.v[k];r[4]=r[3]-r[2];r[5]=r[3];});
 c.sisBar=o.sisBar.map(r=>r.slice());c.sobra=o.sobra;c.imp=o.imp;c.imps=o.imps.map(x=>({n:x.n,c:x.c,f:x.f}));
 c.b1=o.b1;delete c._tec;delete c._tecNome;delete c._habs;traducaoViva();render();reabrir(key);}
function _card(key){const[id,tipo]=key.split("|");return D.find(x=>String(x.id)===id&&x.tipo===tipo);}
function _lvlDe(c){const l={};MBK.forEach(b=>l[b]=0);(c.sisBar||[]).forEach(([nm,n])=>{const b=MBK.find(k=>MBN[k]===nm);if(b)l[b]=n;});return l;}
function _startDe(c){const nm=expand(c.nm);const fab=(c.imps||[]).filter(x=>x.f).map(x=>CAT.find(y=>y[0]===x.n)).filter(Boolean);
 const ex=new Array(26).fill(0);fab.forEach(f=>expand(f[2]).forEach((v,i)=>ex[i]+=v));
 const cd=(CMODE||c.cmode)?expand(c.nx):new Array(26).fill(0);
 return c.base.map((x,i)=>Math.min(99,x+nm[i]+ex[i]+cd[i]));}
let SNAP=null;
function _snapshot(key){const c=_card(key);if(!c)return;
 SNAP={k:key,sis:c.sis?c.sis.slice():c.sis,sisBar:c.sisBar?c.sisBar.map(r=>r.slice()):c.sisBar,
  sobra:c.sobra,imp:c.imp,imps:(c.imps||[]).map(x=>({n:x.n,c:x.c,f:x.f})),b1:c.b1,cmode:c.cmode||0,
  arows:c.arows?c.arows.map(r=>r.slice()):null};}
function _marca(key){if(!SNAP||SNAP.k!==key)_snapshot(key);}
function _desfaz(){if(!SNAP)return;const c=_card(SNAP.k);
 if(c){c.sis=SNAP.sis;c.sisBar=SNAP.sisBar;c.sobra=SNAP.sobra;c.imp=SNAP.imp;c.imps=SNAP.imps;
  c.b1=SNAP.b1;c.cmode=SNAP.cmode;if(SNAP.arows)c.arows=SNAP.arows;}
 SNAP=null;traducaoViva();render();}
function _grava(c,lvl){
 const vals=valsDeLvl(c,lvl);
 c.sis=vals;c.sisBar=MBK.filter(b=>lvl[b]>0).map(b=>[MBN[b],lvl[b]]);
 c.sobra=(c.orc||0)-gastoDe(lvl);
 c.arows.forEach(r=>{r[3]=vals[r[0]];r[4]=r[3]-r[2];r[5]=r[3];});
 c.b1=notaDe(vals,c.arows);
 traducaoViva();render();
}
function editBar(key,bar,d){const c=_card(key);if(!c)return;_marca(key);const lvl=_lvlDe(c);
 const nv=Math.max(0,Math.min(25,lvl[bar]+d));const antes=lvl[bar];lvl[bar]=nv;
 if(gastoDe(lvl)>(c.orc||0)){lvl[bar]=antes;alert("Sem pontos suficientes: esse nível custa "+custoNivel(nv)+" pts e só sobram "+((c.orc||0)-gastoDe(lvl))+".");return;}
 _grava(c,lvl);reabrir(key);}
function editImp(key,nome){const c=_card(key);if(!c)return;_marca(key);
 c.imps=(c.imps||[]).filter(x=>!x.f);
 if(nome&&nome!=="(nenhum)")c.imps.push({n:nome,c:0,f:1});
 c.imp=c.imps.map(x=>x.n+(x.c?" (cond.)":"")+(x.f?" ⚒":"")).join(" · ");
 _grava(c,_lvlDe(c));reabrir(key);}
/* ===== v132 · OTIMIZAR AS BARRAS COM O QUE ESTA NA TELA =====
   Ordem do Luis: "a pessoa nao vai recalcular com o que nao esta na tela.
   Tem que ser o que esta selecionado la na tela."
   Entao NAO varre impeto nem troca tecnico: usa o impeto selecionado, o tecnico
   selecionado e as habilidades do card, e so distribui os pontos de barra.
   REGRA DE OURO do motor: nunca sobra ponto — o resto vai pro maior peso. */
function impVet(c){const v=new Array(26).fill(0);
 /* a STRING c.imp e a verdade do motor; o array c.imps esta desencontrado no banco */
 String(c.imp||'').split(' + ').map(x=>x.replace(' (cond.)','').replace(' \u2692','').trim()).filter(Boolean)
  .forEach(nome=>{const f=CAT.find(y=>y[0]===nome);if(f)expand(f[2]).forEach((q,i)=>v[i]+=q);});
 return v;}
function otimizarBarras(key){const c=_card(key);if(!c||!c.base)return;_marca(key);
 const nm=expand(c.nm), im=impVet(c), tc=tecVet(tecAtual(c)), bf=buffDe(habsDe(c));
 const add=new Array(26).fill(0);
 for(let i=0;i<26;i++)add[i]=nm[i]+im[i]+tc[i];
 const orc=c.orc||0;
 const lvl=distOtima(c.base,c.arows,orc,add,bf);
 let g=orc-gastoDe(lvl);
 if(g>0){const pw={};MBK.forEach(b=>{pw[b]=Math.max(0,...c.arows.filter(r=>MB[b].includes(r[0])).map(r=>r[1]));});
  for(const b of MBK.slice().sort((x,y)=>pw[y]-pw[x])){
   while((lvl[b]||0)<25){const cst=ACCU[(lvl[b]||0)+1]-ACCU[lvl[b]||0];if(cst>g)break;lvl[b]=(lvl[b]||0)+1;g-=cst;}
   if(g<=0)break;}}
 _grava(c,lvl);reabrir(key);}
const P={K:100,DEG:[1,0.88,0.76,0.64,0.52,0.40,0.28,0.16,0.04],AGR:0};
function _bon(d,p){let t=0;for(let k=1;k<=d;k++){const f=P.DEG[k-1];if(f===undefined)break;t+=f*p;}return t;}
function _fal(d,p){const inc=0.25*p/12;let t=0;for(let k=1;k<=d;k++)t+=(1+(k-1)*inc)*p;return t;}

function MOTOR_UI(){
 const d=document.createElement('div');
 d.id='motorpan';
 d.style.cssText='display:none;position:fixed;right:12px;bottom:52px;z-index:9999;background:#0e1116;border:1px solid #22c58b;border-radius:10px;padding:12px;font:12px system-ui;color:#cfd6e4;width:290px;box-shadow:0 6px 26px #000a';
 d.innerHTML=`<div style="font-weight:800;color:#22c58b;margin-bottom:8px">MOTOR — roda no seu navegador</div>
 <label>peso da falta (K) <input id=mK value="100" style="width:60px;background:#161b22;border:1px solid #30363d;color:#cfd6e4;border-radius:4px;padding:2px 4px"></label><br>
 <label style="display:block;margin-top:6px">degraus acima do molde<br><input id=mD value="1,0.75,0.5,0.25" style="width:100%;background:#161b22;border:1px solid #30363d;color:#cfd6e4;border-radius:4px;padding:2px 4px"></label>
 <label style="display:block;margin-top:6px">agravo da punição por ponto <input id=mA value="0" style="width:60px;background:#161b22;border:1px solid #30363d;color:#cfd6e4;border-radius:4px;padding:2px 4px"></label>
 <button onclick="MOTOR_RUN(false)" style="width:100%;margin-top:9px;background:#22c58b;border:none;color:#08120c;font-weight:800;border-radius:6px;padding:7px;cursor:pointer">RECALCULAR ESTA FUNÇÃO</button>
 <button onclick="MOTOR_RUN(true)" style="width:100%;margin-top:6px;background:#1a1206;border:1px solid #f0a531;color:#f0a531;font-weight:700;border-radius:6px;padding:7px;cursor:pointer">RECALCULAR AS 19 (demora)</button>
 <button onclick="MOTOR_EXP()" style="width:100%;margin-top:6px;background:#161b22;border:1px solid #30363d;color:#cfd6e4;border-radius:6px;padding:6px;cursor:pointer">baixar resultado (.json)</button>
 <label style="display:block;margin-top:6px;cursor:pointer;text-align:center;border:1px solid #30363d;border-radius:6px;padding:6px">carregar resultado (.json)<input type=file id=mF style="display:none"></label>
 <div id=mLog style="margin-top:8px;color:#8b949e"></div>`;
 document.body.appendChild(d);
 const t=document.createElement('div');
 t.style.cssText='position:fixed;right:12px;bottom:12px;z-index:9999;background:#0e1116;border:1px solid #22c58b;color:#22c58b;border-radius:8px;padding:6px 11px;font:11px system-ui;cursor:pointer;user-select:none';
 t.textContent='\u2699 motor';
 t.onclick=()=>{const p=document.getElementById('motorpan');p.style.display=p.style.display==='none'?'block':'none';};
 document.body.appendChild(t);
 document.getElementById('mF').onchange=e=>{const f=e.target.files[0];if(!f)return;const r=new FileReader();
  r.onload=()=>{MOTOR_IMP(JSON.parse(r.result));};r.readAsText(f);};
}
function _lerPar(){
 P.K=parseFloat(document.getElementById('mK').value)||100;
 P.DEG=document.getElementById('mD').value.split(',').map(x=>parseFloat(x)).filter(x=>!isNaN(x));
 P.AGR=parseFloat(document.getElementById('mA').value)||0;
}
function MOTOR_RUN(todas){
 _lerPar();
 const L=document.getElementById('mLog');
 const ts=todas?[...new Set(D.map(c=>c.tipo))]:[S.tipo];
 let i=0,n=0;const t0=Date.now();
 const passo=()=>{ if(i>=ts.length){L.textContent='pronto: '+n+' cards em '+Math.round((Date.now()-t0)/1000)+'s';render();return;}
  const t=ts[i];L.textContent='('+(i+1)+'/'+ts.length+') '+t+'...';
  setTimeout(()=>{_RE[t]=0;n+=reOtimizaTipo(t);i++;passo();},20);};
 passo();
}
function MOTOR_EXP(){
 const out=D.filter(c=>c.id!=='MOLDE'&&c.orc).map(c=>({id:c.id,tipo:c.tipo,sis:c.sis,sisBar:c.sisBar,sobra:c.sobra,b1:c.b1,imps:c.imps,imp:c.imp,arows:c.arows}));
 const b=new Blob([JSON.stringify({P,cards:out})],{type:'application/json'});
 const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='motor_resultado.json';a.click();
}
function MOTOR_IMP(j){
 if(j.P){P.K=j.P.K;P.DEG=j.P.DEG;P.AGR=j.P.AGR;
  document.getElementById('mK').value=P.K;document.getElementById('mD').value=P.DEG.join(',');document.getElementById('mA').value=P.AGR;}
 const M={};(j.cards||j).forEach(x=>M[x.id+'|'+x.tipo]=x);
 let n=0;for(const c of D){const x=M[c.id+'|'+c.tipo];if(!x)continue;
  c.sis=x.sis;c.sisBar=x.sisBar;c.sobra=x.sobra;c.b1=x.b1;c.imps=x.imps;c.imp=x.imp;c.arows=x.arows;n++;}
 traducaoViva();render();document.getElementById('mLog').textContent='carregados '+n+' cards';
}
const _RE={};
function RECALC_TUDO(){
 if(!confirm("Recalcular as 19 funções? Leva alguns minutos. Pode acompanhar no painel do motor."))return;
 if(!document.getElementById('motorpan'))MOTOR_UI();
 document.getElementById('motorpan').style.display='block';
 MOTOR_RUN(true);
}
function RECALC(){const t=S.tipo;_RE[t]=0;const t0=Date.now();const n=reOtimizaTipo(t);render();alert("Recalculados "+n+" cards de "+t+" em "+Math.round((Date.now()-t0)/1000)+"s");}
function reOtimizaTipo(t){
 if(_RE[t])return 0;_RE[t]=1;
 let m=0;
 for(const c of D){ if(c.tipo!==t||c.id==="MOLDE"||!c.orc) continue;
  const b=buildOtimo(c);
  c.imps=(c.imps||[]).filter(x=>!x.f);(b.fab||[]).forEach(n=>n.split(" + ").forEach(x=>c.imps.push({n:x,c:0,f:1})));
  c.imp=c.imps.map(x=>x.n+(x.c?" (cond.)":"")+(x.f?" \u2692":"")).join(" \u00b7 ");
  const start=_startDe(c);const vals=aplicar(start,b.lvl);
  c.sis=vals;c.sisBar=MBK.filter(k=>b.lvl[k]>0).map(k=>[MBN[k],b.lvl[k]]);c.sobra=(c.orc||0)-gastoDe(b.lvl);
  c.arows.forEach(r=>{r[3]=vals[r[0]];r[4]=r[3]-r[2];r[5]=r[3];});
  c.b1=notaDe(vals,c.arows);m++;}
 traducaoViva();
 return m;
}
function otimizarTodos(){
 const t=S.tipo;const cs=D.filter(x=>x.tipo===t&&x.orc);
 let m=0;
 for(const c of cs){const b=buildOtimo(c);
  c.imps=(c.imps||[]).filter(x=>!x.f);(b.fab||[]).forEach(n=>n.split(" + ").forEach(x=>c.imps.push({n:x,c:0,f:1})));
  c.imp=c.imps.map(x=>x.n+(x.c?" (cond.)":"")+(x.f?" ⚒":"")).join(" · ");
  const start=_startDe(c);const vals=aplicar(start,b.lvl);
  c.sis=vals;c.sisBar=MBK.filter(k=>b.lvl[k]>0).map(k=>[MBN[k],b.lvl[k]]);c.sobra=(c.orc||0)-gastoDe(b.lvl);
  c.arows.forEach(r=>{r[3]=vals[r[0]];r[4]=r[3]-r[2];r[5]=r[3];});
  c.b1=notaDe(vals,c.arows);m++;}
 traducaoViva();render();alert("Re-otimizados "+m+" cards de "+t+".");}
function toggleCondModal(key){toggleCond();reabrir(key);}
const CTXT=["⬡ condicionais · +1  (1 a 7 jogadores)","⬡ condicionais · +2  (8 a 10 jogadores)","⬡ condicionais · +3  (11 a 23 jogadores)"];
function toggleCond(){CMODE=(CMODE+1)%3;recalcB1();traducaoViva();const b=document.getElementById("condbt");
 if(b){b.textContent=CTXT[CMODE];b.style.background=CMODE?"#f0a531":"#1a1206";b.style.color=CMODE?"#0e1116":"#f0a531";}render();}

(function(){
 for(const t of Object.keys(MED)){
  const c0=D.find(x=>x.tipo===t);if(!c0)continue;
  const kit=(FILA[t]||[]).slice(0,15).map(x=>x[0]);
  const m=MED[t];
  D.push({tipo:t,fam:c0.fam,pos:c0.pos,id:"MOLDE",nome:"⬥ Molde — "+t,ovr:0,votos:m.n,tier:"—",sec:null,
   h:"—",w:"—",foot:"—",temMax:false,b1:0,b1n:m.b1n,b2:m.b2,b3:m.b3,b4:m.b4,b5:m.b5,
   imp:null,sobra:0,modelo:"referência do tipo",wfu:"—",wfa:"—",age:"—",inj:"—",
   arows:c0.arows.map(r=>[r[0],r[1],r[2],r[2],0]),
   frows:c0.frows.map(r=>[r[0],r[1],r[2],r[2],1,r[5],0]),
   fab:kit,falta:[],raras:[],com:[],sisOvr:0,estilo:c0.estilo,base:null,mx:null,sis:null,baseOvr:0,maxOvr:0,sisBar:null,mst:"molde"});
 }
})();


function fechaFiltrosRanking(){
 document.documentElement.classList.remove('t6filtrosaberto');
 const f=document.getElementById('filtros'),b=document.getElementById('fbt');
 if(f&&f.classList.contains('aberto')){f.classList.remove('aberto');if(b){b.classList.remove('on');b.textContent='filtros ▾';}}
}
function fechaFiltrosMobile(){if(window.innerWidth<=820)fechaFiltrosRanking();}
document.addEventListener('DOMContentLoaded',()=>{
 const F=document.getElementById('filtros'); if(!F)return;
 F.addEventListener('change',e=>{
  if(!e.target.matches('#mdl,#posfab,#funcaoGeral'))return;
  render();requestAnimationFrame(fechaFiltrosRanking);
 });
 F.addEventListener('click',e=>{const t=e.target;
  if(t.closest('.fam')||t.closest('.seg')||t.tagName==='BUTTON') setTimeout(fechaFiltrosMobile,60);});
});
function toggleNav(){const f=document.getElementById('fam'),b=document.getElementById('navbt');
 const fech=f.classList.toggle('fechado'); b.textContent=fech?'posi\u00e7\u00f5es \u25be':'posi\u00e7\u00f5es \u25b4';
 b.classList.toggle('on',fech);}
function toggleFiltros(){const f=document.getElementById('filtros'),b=document.getElementById('fbt');
 const ab=f.classList.toggle('aberto'); b.classList.toggle('on',ab); b.textContent=ab?'filtros ▴':'filtros ▾';}
function togglePesos(){const p=document.getElementById('pesos'),b=document.getElementById('pesosbt');
 const on=p.style.display==='none';p.style.display=on?'':'none';b.textContent=on?'ajustar pesos \u25b4':'ajustar pesos \u25be';}
function pizza(c){
 const tw=W.reduce((a,b)=>a+b,0)||1;
 const it=BKV.map(([b,i])=>({n:b[1],cor:b[2],nota:c[b[0]],peso:W[i],cont:c[b[0]]*W[i]/tw}));
 const soma=it.reduce((a,x)=>a+x.cont,0)||1;
 const R=64,r=39,cx=72,cy=72;let ang=-Math.PI/2,paths='';
 it.forEach(x=>{const f=x.cont/soma;const a2=ang+2*Math.PI*(f>=0.9999?0.9999:f);
  const P=(rr,a)=>[(cx+rr*Math.cos(a)).toFixed(2),(cy+rr*Math.sin(a)).toFixed(2)];
  const A=P(R,ang),B=P(R,a2),C=P(r,a2),E=P(r,ang),big=(a2-ang)>Math.PI?1:0;
  paths+='<path d="M'+A[0]+' '+A[1]+' A'+R+' '+R+' 0 '+big+' 1 '+B[0]+' '+B[1]+' L'+C[0]+' '+C[1]+' A'+r+' '+r+' 0 '+big+' 0 '+E[0]+' '+E[1]+' Z" fill="'+x.cor+'" stroke="#0e1116" stroke-width="1.5"/>';ang=a2;});
 const leg=it.map(x=>`<div class=pzr><i style="background:${x.cor}"></i><span style="color:#c7cedb">${x.n}</span><b style="font-size:15px;color:${x.cor}">${(x.nota/10).toFixed(1)}</b><span class=mini>peso ${Math.round(100*x.peso/tw)}% · entrega ${x.cont.toFixed(1)}</span></div>`).join('');
 return `<div class=pz><svg width=144 height=144 viewBox="0 0 144 144">${paths}<text x=72 y=70 text-anchor=middle style="font:800 24px sans-serif" fill="#fff">${(soma/10).toFixed(1)}</text><text x=72 y=86 text-anchor=middle style="font:600 8.5px sans-serif" fill="#5d6673">PONTUAÇÃO 0-10</text></svg><div class=pzl>${leg}</div></div>`;}
function setBar(key,bar,v){const c=_card(key);if(!c)return;_marca(key);const lvl=_lvlDe(c);const antes=lvl[bar];
 v=Math.max(0,Math.min(25,v));
 while(v>0){lvl[bar]=v;if(gastoDe(lvl)<=(c.orc||0))break;v--;}
 lvl[bar]=v;if(gastoDe(lvl)>(c.orc||0)){lvl[bar]=antes;return;}
 _grava(c,lvl);reabrir(key);}
function painelBuild(c){
 if(!c.orc)return '';
 const lvl=_lvlDe(c),K=c.id+'|'+c.tipo;
 const bars=MBK.slice();  /* 10 barras sempre (Luis 05/08) */
 const cst=n=>{let t=0;for(let k=1;k<=n;k++)t+=Math.ceil(k/4);return t;};
 const gasto=gastoDe(lvl),sobra=(c.orc||0)-gasto,lc=Math.round((c.orc||0)/2)+1;
 const barsO=MBK.filter(b=>!bars.includes(b));const _row=(b)=>{const n=lvl[b]||0;
  return `<div class=brow><span class=bn>${MBN[b]}</span><input type=range min=0 max=25 value="${n}" onchange="setBar('${K}','${b}',+this.value)"><span class=bp>${cst(n)} pts</span><span class=bc><button class=bbt onclick="editBar('${K}','${b}',-1)">\u2212</button><b class=bnum>${n}</b><button class=bbt onclick="editBar('${K}','${b}',1)">+</button></span></div>`;};const rows=bars.map(_row).join(''),rowsO=barsO.map(_row).join('');
 const tecNome=(c._tecNome!==undefined?c._tecNome:c.TEC)||'';
 const tecSel=`<div class=imp><label>\u26bd TÉCNICO</label><select onchange="trocaTec('${K}',this.value)">`
  +`<option value=""${tecNome?'':' selected'}>(nenhum)</option>`
  +(function(){const bs=(tecAtual(c)||[]).slice().sort().join();
    let sel=TECS.findIndex(t=>t[0]===tecNome&&t[1].slice().sort().join()===bs);
    if(sel<0)sel=TECS.findIndex(t=>t[0]===tecNome);
    return TECS.map((t,i)=>`<option value="${i}"${i===sel?' selected':''}>${t[0]}${_tecRep(t[0])?' · '+t[1].map(tecPT).join(' + '):''}</option>`).join('');})()
  +`</select></div>`;
 const imp=false?`<div class=imp><label>\u2692 FABRICAR ÍMPETO</label><select onchange="editImp('${K}',this.value)">${["(nenhum)"].concat(CAT.filter(x=>c.sl[x[1]]).map(x=>x[0])).map(n=>`<option${(c.imps||[]).some(y=>y.f&&y.n===n)?" selected":""}>${n}</option>`).join("")}</select></div>`:'';
 const _hab=habsAtual(c);
 const _nat=(c.fab||[]).concat(c.raras||[]);
 const _pool=Object.keys(HABEF).filter(function(s){return _hab.indexOf(s)<0&&_nat.indexOf(s)<0&&!(typeof HABRARAS!=='undefined'&&HABRARAS[s]);}).sort(function(x,y){return x.localeCompare(y,'pt');});
 const _cond=!!(c.CD&&(c.CD["2"]||c.CD["3"]));
 const _recHab=`<div class=receita><b class=receitatt>Habilidades</b>`
  +`<div class=hbgrp><b>Nativas</b><ul class=hblist>${(_nat.length?_nat:['—']).map(s=>`<li>${s}</li>`).join('')}</ul></div>`
  +`<div class=hbgrp><b>Adicionadas</b><ul class=hblist>${_hab.length?_hab.map((s,ix)=>`<li><span class=chip style="border-color:#f0a531;color:#f0a531">${s} <b style="cursor:pointer" onclick="remHab('${K}',${ix})">×</b></span></li>`).join(''):'<li>nenhuma</li>'}</ul>`
  +(_hab.length<5&&_pool.length?`<select style="max-width:170px" onchange="addHab('${K}',this.value);this.value=''"><option value="">+ adicionar…</option>${_pool.map(s=>`<option>${s}</option>`).join('')}</select>`:'')
  +`</div>`
  +((c.NEU&&c.NEU.length)?`<div class=hbgrp><b>Boas opções</b><ul class=hblist>${c.NEU.map(x=>`<li><span class=chip style="border-color:#5d6673;color:#8d97a3">${x}</span></li>`).join('')}</ul></div>`:'')
  +`</div>`;
 const _recMot=`<div class=receita>`
  +((c.raras&&c.raras.length)?`<div class=hbgrp><b>Habilidades especiais</b><div class=chips>${c.raras.map(s=>`<span class="chip rr">${s}</span>`).join('')}</div></div>`:'')
  +`<div class=hbgrp><b>Técnico utilizado${(c._tecNome!==undefined&&((window.FichaState&&window.FichaState.uiMode())||'motor')!=='insumos')?' <b class=receitadim>· trocado</b>':''}</b>${tecSel}<div class=tecmais>+1 ${(tecAtual(c)||[]).map(tecPT).join(' · ')||'—'}</div></div>`
  +((tecIguais(c).length)?`<div class=hbgrp><b>Sugestões de técnico</b><ul class=hblist>${tecIguais(c).slice(0,5).map(x=>`<li>${x}</li>`).join('')}</ul></div>`:'')
  +`<div class=hbgrp><b>Ímpeto</b><div class=iasub>nativo</div><ul class=hblist>${(function(){const L=(typeof pimpNativos==='function')?pimpNativos(c):null;if(L&&L.length>1) return L.map(x=>{const ef=pimpEfeito(x.efeito);return `<li><b>${pimpPT(x.nome,x.efeito)}</b>${ef?`<div class=impef>${ef}</div>`:''}</li>`;}).join('');const P=(typeof pimpDoCard==='function')?pimpDoCard(c):null;const f=(c.nmn&&c.nmn.length)?c.nmn:(c.imps||[]).filter(x=>x&&x.f).map(x=>x.n).filter(Boolean);if(P){const ef=pimpEfeito(P.efeito);return `<li><b>${pimpPT(P.nome,P.efeito)}</b>${ef?`<div class=impef>${ef}</div>`:''}</li>`;}if(L&&L.length===1){const ef=pimpEfeito(L[0].efeito);return `<li><b>${pimpPT(L[0].nome,L[0].efeito)}</b>${ef?`<div class=impef>${ef}</div>`:''}</li>`;}return f.length?f.map(n=>`<li><b>${n}</b></li>`).join(''):((typeof _natDoVetor==='function')?_natDoVetor(c):'<li>não tem</li>');})()}</ul><div class=iasub>adicionado</div><ul class=hblist>${(function(){var _p=String(c.imp||'').split('o motor pos:');if(_p.length>1){var nm=_p[1].trim();var ef='';try{var h=(typeof CAT!=='undefined')?CAT.filter(function(x){return x[0]===nm;})[0]:null;if(h)ef=pimpEfeito(h[2]);}catch(e){}return `<li><b>${nm}</b> <b style="cursor:pointer;color:#e46a6a;margin-left:4px" title="tirar este ímpeto" onclick="editImp('${K}','')">×</b>${ef?`<div class=impef>${ef}</div>`:''}${(typeof _impSel==='function')?_impSel(c,K,nm):''}</li>`;}if(c.slot===0) return '<li style="color:#8fa4c4">não tem vaga</li>';if(c.slot) return `<li><span style="color:#8fa4c4">vaga livre</span>${(typeof _impSel==='function')?_impSel(c,K,''):''}</li>`;return '<li style="color:#8fa4c4">vaga ainda não conferida</li>';})()}</ul></div>`
  +((c.slot===0&&String(c.imp||'').trim())?`<div class=hbgrp><b style="color:#e46a6a">⚠ carta SEM VAGA — o ímpeto escolhido não existe no jogo</b></div>`:'')
  +(_cond?`<div class=hbgrp><button class=bbt style="width:auto;padding:0 8px" onclick="toggleCondCard('${K}')" title="ímpeto condicional deste card">⚒ condicional · degrau ${c.cmode||1}</button></div>`:'')
  +`</div>`;
 return `${(typeof _modoBar==='function')?_modoBar(K):''}<div class="bpan bptrio"><div class=bpc1>${_recHab}</div><div class=bpc2>${_recMot}</div><div class=bpc3><div class=bhd><span>Distribuição dos pontos <span class="bhdnote admonly">· teste temporário, fechar a ficha desfaz</span></span><span class=bhdnum>Nível <b>${lc}</b> · <b class=ptsbig>${gasto}/${c.orc}</b>${sobra?` · <b style="color:#e0533d">sobram ${sobra}</b>`:` · <b style="color:#22c58b">tudo gasto</b>`}</span></div><div class=bp2><div>${rows}</div><div class=bpocul>${rowsO}</div></div><button onclick="restaurarMotor('${K}')" style="width:100%;margin-top:10px;cursor:pointer;background:#22c58b;border:none;color:#08120c;font-weight:800;border-radius:7px;padding:7px;font-size:12px">\u26a1 OTIMIZAR — a build do motor</button></div></div>`;}
function VP(){return (document.getElementById('verpor')||{}).value||'';}
const ORG={1:['1ª · nativa','#22c58b'],2:['2ª · comprada','#f0a531'],3:['3ª · exercida','#c4a5ff']};
const POSN={GK:"Goleiro",ZC:"Zagueiro",LE:"Lateral esquerdo",LD:"Lateral direito",VOL:"Volante",MC:"Meia de ligação",MLE:"Meia lateral esquerda",MLD:"Meia lateral direita",MO:"Meia atacante",PE:"Ponta esquerda",PD:"Ponta direita",SA:"Segundo atacante",CA:"Centroavante"};
const SIGJ={GK:"GO",ZC:"ZC",LE:"LE",LD:"LD",VOL:"VOL",MC:"MLG",MLE:"MLE",MLD:"MLD",MO:"MAT",PE:"PTE",PD:"PTD",SA:"SA",CA:"CA"};
/* v129 · VOCABULARIO — o usuario fala a lingua do jogo (LD, MLE, CA);
   o administrador continua vendo o nome por extenso. */
function posLabel(p){if(!p)return '—';return (POSN[p]||p)+' ('+(SIGJ[p]||p)+')';}
function tarjaSE(c){return estiloAtiva(c)?'':'<span style="background:#2a1210;color:#e0533d;padding:1px 6px;border-radius:4px;font-size:10.5px;font-weight:700;margin-left:6px" title="o estilo de jogo dele não liga nesta posição — aqui ele joga como BÁSICO">BÁSICO</span>';}
function tarjaMig(c){return c.MIG?'<span style="background:#3a2a12;color:#f0a531;padding:1px 6px;border-radius:4px;font-size:10.5px;font-weight:700;margin-left:6px">MIGRADO</span>':'';}
const TECPT={lowPass:'Passe rasteiro',loftedPass:'Passe alto',finishing:'Finalização',heading:'Cabeceio',
 ballControl:'Controle de bola',tightPossession:'Posse de bola',dribbling:'Drible',curl:'Efeito',
 offensiveAwareness:'Ofensividade',defensiveAwareness:'Talento defensivo',ballWinning:'Desarme',
 trackingBack:'Envolv. defensivo',aggression:'Agressividade',speed:'Velocidade',stamina:'Resistência',
 gkAwareness:'Talento de goleiro',gkClearing:'Defesa (GO)',gkReflexes:'Reflexos',gkReach:'Alcance',
 acceleration:'Aceleração',kickingPower:'Potência de chute',jump:'Salto',physicalContact:'Contato físico',
 balance:'Equilíbrio',setPieceTaking:'Cobrança de falta',gkCatching:'Encaixe'};
const tecPT=k=>TECPT[k]||k;
function boxMotor(c){if(!c.TEC&&!c.HAB)return '';
 return '<div class=receita>'+
 '<b class=receitatt>Receita do motor</b><br>'+
 ((c.TEC||c._tecNome)?('<b>Técnico:</b> '+(c._tecNome!==undefined?(c._tecNome||'nenhum'):c.TEC)+' <span class=receitadim>(+1 em '+(tecAtual(c).map(tecPT).join(' · ')||'—')+')</span>'+(c._tecNome!==undefined?' <b class=receitadim>· trocado</b>':'')+'<br>'):'')+
 (c.imp?('<b>Ímpeto:</b> '+c.imp+'<br>'):'')+
 ((c.HAB&&c.HAB.length)?('<b>Habilidades adicionadas:</b> '+c.HAB.join(' · ')):'')+'</div>';}
function posLinha(c){
 const nv=posLabel(c.np);
 const sp=(c.sp||[]).filter(x=>x[0]!==c.np);
 const sec=sp.map(x=>{const f=funcDaPos(x[0],c.modelo);const alvo=f?irmAll(c).find(y=>y.tipo===f):null;const est=x[1]>=2?'\u2605\u2605':'\u2605';if(alvo)return `<span class=ps2 style="cursor:pointer;border-color:#22c58b" title="abre ${f}" onclick="reabrir('${alvo.id}|${alvo.tipo}')">${posLabel(x[0])}<b>${est}</b></span>`;return `<span class=ps2 style="opacity:.45;cursor:not-allowed" title="${f?('a funcao '+f+' ainda nao foi calculada para este card'):('nao ha regra de funcao para a posicao '+x[0])}">${posLabel(x[0])}<b>${est}</b></span>`;}).join('');function irmAll(c){const b=String(c.id).split('@')[0];return D.filter(x=>x.id!=='MOLDE'&&String(x.id).split('@')[0]===b);}
 const base=String(c.id).split('@')[0];
 const irm=D.filter(x=>x.id!=='MOLDE'&&String(x.id).split('@')[0]===base);
 irm.forEach(x=>{if(x._n===undefined)x._n=nota(x);});
 irm.sort((a,b)=>b._n-a._n);
 const fn=irm.length>1?`<div class=posl style="margin-top:6px"><span class=pslb>ESTE CARD NAS ${irm.length} FUNÇÕES</span>`+
  irm.map(x=>`<span class=ps2 style="cursor:pointer;${x.tipo===c.tipo?'border-color:#22c58b;color:#22c58b':''}" onclick="reabrir('${x.id}|${x.tipo}')">${x.tipo} (${sigDe(x.tipo)}) <b>${x._n.toFixed(1)}</b></span>`).join('')+`</div>`:'';
 return `<div class=posl><span class=pslb>POSIÇÃO NATIVA</span><span class=psnv>${nv}</span>${sp.length?`<span class=pslb style="margin-left:12px">TAMBÉM JOGA</span>${sec}`:''}</div>${fn}`;}
function notaBase(c){let s=0,t=0;for(let i=0;i<5;i++){s+=c[BK[i][0]]*W[i];t+=W[i];}return t?s/t:0;}
const MIG_ESCALA=[0];
let MIG_I=0;                 /* PUNIÇÃO ABOLIDA (Luis 05/08) */
let MIG_PUN=0;
/* ===== BLOCO 3 · ESTILO DE JOGO DA IA — BONUS POR QUANTIDADE (03/08) =====
   Decisao do Luis: e bonus, nao composicao de nota. Logo nao tem teto de
   pertinencia — cada COM que o card carrega vale ponto, nada se desperdiça.
   O jogo permite no maximo 5 COM por card; 4 cards no banco tem os 5
   (Marcos Llorente x3, Pedro Porro).
     bonus = IA_PT * (nCOM / 5)      ->  5=+2,0  4=+1,6  3=+1,2  2=+0,8  1=+0,4  0=0
   GOLEIRO ENTRA NA MESMA REGRA. Conferido em 03/08: 18 dos 19 goleiros com COM
   sao goleiros de verdade (Emiliano Martinez, Maignan, Diogo Costa, Szczesny,
   Pickford, Unai Simon, Zion Suzuki, Trubin, Buffon, Kahn, Abbiati) e todos com
   o MESMO COM, "Cruzamento antecipado" — coerente demais para ser erro de base,
   e combina com a funcao Goleiro ofensivo. Nao se zera ninguem.
   (O unico fora do lugar e o Olivier Giroud, que nem goleiro e.)
   IA_PT = escala. IA_ON = liga/desliga. IA_MAX = teto de COM do jogo. */
let IA_ON=1;
let IA_PT=1;
let IA_MAX=4;
const IA_ESCALA=[0,0.5,1,1.5,2,2.5,3];
let IA_I=2;
function iaBonus(c){
 if(!IA_ON)return 0;
 const n=(c.com||[]).length;
 if(!n)return 0;
 return IA_PT*Math.min(n,IA_MAX)/IA_MAX;}
function toggleIA(){
 IA_I=(IA_I+1)%IA_ESCALA.length;
 IA_PT=IA_ESCALA[IA_I];
 IA_ON=IA_PT>0?1:0;
 const b=document.getElementById('iabt');
 if(b)b.textContent='estilo IA: '+(IA_ON?'+'+IA_PT:'desligado');
 CARDS.forEach(c=>{c._ia=undefined;});
 render();}
  /* ===== PE RUIM - 11/08/2026 - injetado pelo gera_encaixe.py ===== */
  /* 11/08 FECHADO PELO LUIS: bonus = f x q, teto 1,00, igual pra toda funcao. */
  const PR_RAW="8823:6 33185:6 34881:a 35017:1 35207:a 40352:b 40571:6 43133:2 43387:e 44636:a 45774:f 46536:5 46614:a 57123:5 57309:5 60391:0 60738:6 60789:5 61050:9 61181:5 100995:a 101334:5 103041:5 104717:0 108140:5 108662:a 110626:f 110644:6 110718:a 110784:5 111366:5 111407:5 111909:6 112932:5 113338:5 113408:1 113502:6 113760:5 114440:5 114876:5 116691:1 116751:a 117047:1 118157:9 121750:a 123101:5 125050:5 125370:a 126689:5 126979:6 127038:5 127617:1 128513:5 129369:1 130039:a 132933:b 133100:6 133543:2 135067:5 136184:6 137924:6 138000:2 138183:5 140066:5 140127:5 140284:6 141008:a 142061:6 142198:b 143196:5 144438:5 147458:a 152691:9 157472:5 159320:a 162114:a 170711:5 170946:4 177751:f 179676:5 16781738:b 16812405:f 16887496:5 16925209:1 84006535:9 17592186044712:b 17592186045268:1 17592186045282:1 17592186048174:a 17592186048489:5 17592186048938:a 17592186051927:2 17592186084768:b 17592186174377:a 17592186178992:1 17592186178993:1 17592186178997:6 17592186179005:6 17592186179010:a 17592186179013:f 17592186179020:1 17592186179021:6 17592186179023:6 17592186179024:6 17592186179036:6 17592186179040:a 17592186179044:5 17592186179049:a 17592186179050:b 17592186179051:f 17592186179052:6 17592186179053:b 17592186179054:7 17592186179055:6 17592186179074:a 17592186179082:6 17592186179086:e 17592186179094:2 17592186182370:5 17592454480724:1 17592454483945:5 17592454614449:1 17592454614457:6 17592454614461:6 17592454614466:a 17592454614469:f 17592454614479:6 17592454614480:6 17592454614496:a 17592454614501:7 17592454614504:6 17592454614505:a 17592454614506:b 17592454614507:f 17592454614509:b 17592454614538:6 17592454614550:2 17592722922839:2 17592722955680:b 17592723049936:6 17592723049952:a 17592991485433:5 17592991488743:5 17593259920877:b 52776826679422:a 52777095067617:a 52777095137703:2 52777363558769:1 52777631915074:a 52777631993516:a 52777900357362:5 52778168787119:1 52778168793771:6 52778974109475:5 52779510963616:b 52779779415843:5 52780047903181:6 52780316362565:b 52780584725600:a 52780584775806:a 52780584775954:b 52781121579063:f 52781121650238:5 52781121668192:6 52781390011808:b 52781658441010:6 52781658444018:1 52781658453914:5 52781658507988:5 52781658517630:a 52781926875605:1 52781926889005:a 52781926899717:a 52782195325003:1 52782463750050:a 52782732190909:5 52783000624617:1 52783000685289:9 52783269130463:6 52783269152805:f 52783269157572:6 52783537501640:5 52783537565822:a 52783537568444:1 52783806005368:1 52783806009713:a 52784074448008:a 52784342881172:a 52784611254141:b 52784611304863:9 52785148186011:a 52785416510807:2 52785416618202:9 52785416625046:a 52785685049470:a 52785953482441:b 52785953484992:5 52786221849786:a 52786490360026:9 52786758721147:6 52787027123543:2 52787027217090:5 52787027254032:2 52787295558817:6 52787295560432:a 52787295585287:7 52787295665723:e 52787564025383:f 52787564047456:a 52787564100349:a 52787564107184:5 52788369426245:b 52788637736279:2 52788637837430:a 52788906209492:6 52788906274942:a 52788906294185:a 52845277653047:f 52845277718943:6 52845277743527:2 52845546085217:5 52845546085792:b 52845814528683:6 52845814585122:1 52846888261347:5 52847156719353:1 52847156719848:6 52847156775223:1 52847425098154:b 52847425204350:a 52847693536417:6 52847693586211:5 52847693630185:9 52847693645299:0 52848230502901:1 52848230512334:a 52848230532933:b 52848230533543:2 52848498943735:5 52848498973456:2 52848767392772:7 52848767403456:5 52849035817086:b 52849304150957:5 52849304184140:5 52849304260801:7 52849304260977:a 52849572697187:a 52849841131713:6 52850109595212:9 52850378005461:f 52851183322921:e 52851451685713:a 52851451736190:a 52851720165605:a 52851720171743:6 52851720174914:6 52851720182920:b 52851988540763:b 52851988604663:5 52851988613431:1 52851988616262:b 52851988649521:a 52852257040073:b 52852257053845:6 52852525404066:a 52852525478134:3 52852793922283:2 52853062347167:6 52853062349460:0 52853062371141:b 52853062371751:3 52853330718504:a 52853330776672:a 52853330777068:1 52853330778381:0 52853599156299:1 52853867588955:b 52853867671471:1 52853867677733:f 52854404456607:1 52854404458551:f 52867826326288:3 52868094734462:a 52868094737849:a 52868094750368:a 52868363197124:6 52868631501985:6 52868631613809:a 52868899976648:5 52868900044618:6 52868900072373:f 52869168485350:6 52869168493084:9 52869436915930:9 52869436927989:b 52869705269665:6 52869705350391:6 52869705368672:7 52869973708663:5 52869973711938:a 52869973799480:a 52870242240935:2 52870779100117:f 52870779111461:f 52871047450530:a 52871047474272:a 52871047475432:6 52871315893320:0 52871315950550:5 52871315987216:2 52871584326253:1 52871584329051:b 52871852828785:e 52871852830912:5 52871852847166:5 52871852853061:b 52871852862389:f 52872121259197:5 52872121266486:7 52872121283128:a 52872121291768:6 52872658154040:a 52872926590672:b 52872926595495:2 52873463337386:b 52873463366962:6 52873463367745:a 52873463441823:6 52873463459488:b 52873463470864:2 52873731815607:a 52873731930434:a 52874268681548:7 52874537210872:6 52874537212844:1 52874805637688:b 52875073990890:5 52875074056199:a 52875074057086:a 52875074062143:6 52875342438179:6 52875342494461:a 52875342527062:a 52875610824023:2 52875610863799:a 52875610943407:1 52875610963747:e 52876416233782:7 52876684674991:5 52876684675383:5 52876953037896:0 52876953104576:5 52876953113699:a 52876953116252:5 52877221533925:a 52877221544327:7 52877221562181:b 52877221562791:2 52877489905275:6 52877489978615:6 52877489992248:a 52877758357283:5 52878026768801:6 52878026838624:a 52878026846823:1 52878026852159:6 52878026869086:6 52878026873799:5 52878295213388:6 52878295289079:1 52878295309072:2 52878295312650:5 52878563649591:f 52878832156550:f 52878832158735:a 52878832159597:6 52878832168608:a 52879100515879:f 52879100524619:1 52879100588158:a 52879100592519:6 52879100607401:a 52879100607759:b 52879369045829:b 52879637458978:f 52879637458996:6 52879905898616:1 52880174266079:5 52880174329982:a 52880174337435:a 52880174352942:6 52880442695351:5 52880442758124:5 52880442771767:1 52880442773873:b 52880442781344:a 52880442802675:9 52880711210631:9 52880711223333:f 52880979573417:a 52880979634637:6 52880979636258:f 52880979658176:5 52881248005192:0 52881248006378:5 52881248089808:b 52881248109097:6 52881516555945:6 52881784866098:6 52881784956107:6 52882590199545:1 52882858634271:a 52882858682829:6 52882858703193:2 52883127116966:5 52883127174173:6 52883395573456:b 52883395582736:2 52883663924571:b 52883663925032:a 52883663993530:5 52883663999345:a 52883664008270:5 52883932429053:b 52884200867759:5 52884200880473:1 52884200884647:2 52884200886171:1 52884200904241:a 52884469297278:a 52884737662953:5 52884737669303:a 52884737729905:5 52884737740993:7 52884737754171:a 52885006165541:6 52885006165751:5 52885006189858:1 52885006219586:a 52885274601585:e 52885274601887:6 52885274603566:6 52885274603572:6 52885274606888:a 52885274625684:6 52885274655042:a 52885542985507:5 52885543047915:6 52885543057753:1 52885543061541:f 52885543081851:1 52885811464916:5 52885811474484:6 52885811474558:a 52886079860180:b 52886079925920:a 52886348361088:e 52886348382707:9 52886616674730:b 52886616802964:5 52886616816720:a 52886616818309:a 52886885222751:6 52886885243664:2 52887153548631:2 52887422011457:b 52887422093623:2 52887422094115:b 52887422102622:5 52887422135896:a 52887690522658:f 52887690522750:a 52887690525992:a 52887690550188:1 52887690564960:a 52887690567240:5 52887690579199:6 52887958894125:a 52887958987167:a 52887959009602:a 52888227330230:6 52888227393662:a 52888227410013:a 52888227415099:a 52888227416101:f 52888495823012:6 52888495848719:a 52888495859978:5 52888495877720:a 52888764161367:2 52888764198235:b 52888764200735:6 52888764273638:6 52888764279902:5 52889032623410:6 52889032690370:1 52889032719514:a 52889032722855:2 52889032750860:b 52889301085280:a 52889301132454:5 52889301136872:e 52889301138293:5 52889301151837:a 52889569571431:1 52889569580679:9 52889569586848:a 52889837932398:9 52889838004639:6 52889838012727:1 52889838022294:a 52889838038876:5 52890106440141:a 52890106442388:0 52890374870278:5 52890374875561:5 52890374885745:a 52890374892892:f 52890374892941:b 52890374899136:5 52890374921806:a 52890643249227:2 52890643315573:5 52890643316008:a 52890643316954:9 52890643324381:6 52890643338232:6 52890643343516:f 52890911684878:b 52890911746463:6 52890911764664:2 52890911771157:f 52891180115276:5 52891180208027:5 52891180246741:5 52891448555703:a 52891448626690:f 52891448637204:a 52891448640608:a 52891448641959:2 52891448667736:a 52891716988895:6 52891717004319:a 52891717047292:0 52891717058778:a 52891717060623:b 52891717070797:b 52891717095666:5 52891985419680:b 52891985490230:b 52891985492393:a 52891985493661:5 52891985494407:6 52891985515372:a 52891985519680:5 52891985544221:7 52892253943504:6 52892253946070:a 52892253948437:f 52892522360884:6 52892790801832:5 52892790818629:b 52892790823620:6 52892790826734:5 52893059165992:a 52893059231790:6 52893059232638:b 52893059235960:1 52893059240129:6 52893059253670:6 52893059265590:5 52893059291530:6 52893327667326:a 52893327691402:b 52893596119681:5 52893596124820:5 52893596124997:b 52893596129988:6 52893596153612:f 52893864488697:1 52893864542328:5 52893864554415:1 52893864563704:6 52894132921815:1 52894132973575:f 52894132973694:a 52894132979581:5 52894132998043:2 52894401343272:a 52894401405389:0 52894401409216:5 52894401424732:f 52894401431902:a 52894669842550:a 52894669845168:5 52894669850935:1 52894669861274:6 52894938278468:6 52894938283850:a 52894938297131:b 52894938298132:a 52895206713492:1 52895206724635:a 52895206727528:e 52895206757728:e 52895475160038:6 52895475167151:9 52895475188428:5 52895743518028:5 52895743520095:5 52895743535509:6 52895743589623:7 52895743595540:a 52895743602336:a 52895743604432:6 52895743616652:5 52895743617950:6 52895743641408:f 52896011971406:5 52896012020127:6 52896012021812:7 52896012025128:a 52896012028215:2 52896012041487:b 52896012048168:6 52896012049652:6 52896012059063:5 52896012078905:f 52896280392617:5 52896280448144:5 52896280457223:e 52896280457250:f 52896280457526:7 52896280460029:a 52896280461130:6 52896280487327:0 52896280488202:5 52896280489452:5 52896280508738:a 52896548890737:e 52896548935008:9 52896817328180:a 52897085700171:1 52897085763618:f 52897085775325:6 52897354189524:5 52897354196134:5 52897354207979:6 52897354230536:5 52897354250562:a 52897354255615:5 52897622566573:5 52897622638879:5 52897622651925:5 52897622656660:5 52897891019910:6 52897891069986:f 52897891077153:5 52897891086520:1 52897891097516:5 52898159428914:6 52898159508221:a 52898427941722:5 52898427945178:9 52898427956609:b 52898427993278:5 52898696305850:a 52898696326240:a 52898696392417:5 52898696405407:a 52898696413683:9 52898696427842:a 52898964834341:f 52898964843272:5 52899233184427:7 52899233256171:6 52899233278218:5 52899501686662:f 52899501687031:5 52899501713134:5 52899501729435:6 52899770125723:a 52899770125826:f 52899770134230:5 52899770137909:5 52899770145476:6 52900038483579:6 52900038544066:1 52900038544105:a 52900038553634:f 52900038576551:2 52900306979798:5 52900306995215:a 52900306996396:7 52900307004764:f 52900307009750:a 52900575358760:a 52900575417606:5 52900575428855:1 52900575447573:f 52900575482481:5 52900843793755:b 52900843893220:5 52900843908580:6 52900843910924:b 52901112295470:6 52901112312348:9 52901380664392:0 52901380680800:a 52901380742826:9 52901380744554:f 52901380747213:a 52901380758278:a 52901380766800:b 52901649095746:b 52901649159970:1 52901649165284:b 53876606760371:f 53878485695166:5 53962237674443:6 53967337854719:2 53968143169652:a 53968680104710:5 53968680110883:a 53970559146077:a 53974854120198:5 53975122505049:6 53975927864176:a 53976196313725:e 53976464668196:4 53976464735047:1 53977270054668:6 53978343813402:5 53978612219454:5 53980759707972:b 53981028177481:9 53982101886599:9 53982370341557:1 53983980934636:b 53983980938001:5 53984249311006:5 55066849484923:b 55066849562859:5 55067117989922:f 55067118012404:5 55067386331226:a 55067386425567:6 55067386425959:1 55067386431839:6 55067386455692:5 55067654796153:a 55067654854885:a 55067923286761:b 55067923312181:5 55067923314384:b 55068460117088:a 55068460158191:6 55068460168376:a 55068460171421:b 55068460171452:5 55068460171551:5 55068460171655:a 55068460171804:5 55068460176107:a 55068460183501:b 55068460194657:e 55068460197336:6 55068728532034:b 55068728534588:a 55068728618656:a 55068728625084:a 55068728630326:0 55068728633070:5 55068996967610:b 55068997039592:e 55068997041878:5 55068997045101:6 55069265399671:5 55069533838752:b 55069533859022:a 55069533925462:a 55069533944959:5 55069533950196:a 55069533958391:5 55069802334015:a 55069802342513:f 55069802348765:a 55069802361877:5 55069802378853:6 55069802385650:6 55069802386207:6 55069802398749:a 55070339149151:5 55070339207776:a 55070339215207:6 55070339215364:6 55070339218528:6 55070339239313:b 55070339270464:f 55070607581343:5 55070607587294:1 55070607649352:6 55070607651018:5 55070607654410:6 55070607657273:a 55070607660052:a 55070607666913:5 55070607668011:b 55070607670543:a 55070607676904:a 55070607683713:6 55070607703230:5 55070607716019:5 55070876039189:6 55070876081807:a 55070876119403:5 55070876122670:6 55070876122984:5 55071144547234:5 55071412966292:b 55071681398799:a 55071949764878:b 55072486740874:5 56161529278248:a 56161797802021:f 56161797829059:a 56162066111831:6 56162066215038:a 56162066233689:1 56162066237863:2 56162066252275:9 56162334587063:a 56162334672709:b 56162334699096:a 56162603100071:b 56162603118247:a 56162603149423:6 56162871522674:a 56162871532700:b 56162955404703:a 56163139903267:5 56163139956740:2 56163140008258:a 56163190239491:5 56163408385004:1 56163408392226:f 56163408396319:5 56163676721578:b 56163676848342:a 56163676849812:5 56163760664861:2 56163945263719:1 56163945266472:a 56164213720125:a 56164213731164:5 56164482083871:a 56164482134050:f 56164482158182:6 56164482165002:5 56164750503259:f 56164750578580:b 56164750585918:5 56164750599696:a 56165019008842:6 56165019026854:6 56165019032260:6 56165019040848:a 56165019067344:5 56165287440437:5 56165287449574:6 56165287461944:5 56165287477893:a 56165555812535:a 56165555880124:5 56165824319857:a 56166092747440:5 56166092749498:5 56166092753953:5 56166361188271:5 56166361204716:6 56166361224544:a 56166629547424:b 56166629640005:b 56166629640615:2 56167166556926:5 56167434870573:0 56167434921679:2 56167434979136:f 56167703375520:a 56167703392163:7 56167971795167:6 56167971811177:9 56168240220884:5 56168240228767:6 56168240230526:b 56168240236559:b 56168240247352:a 56168240262069:f 56168508672311:1 56168508708296:a 70373039149482:b 70373039184962:a 70373039202083:5 70373307641466:9 70373307691134:a 70374381329569:6 70376260374954:b 70377065722745:a 70377334146354:6 70377334152258:a 70377602608450:6 70379750074001:6 70379750164903:2 70380286909783:2 87960930356715:7 87960930356724:9 87962272400283:6 87962272515241:2 87962272533982:6 87962272533984:b 87962272534003:a 87962272534030:a 87962272534031:b 87962272537319:5 87963077709801:b 87963077840306:6 87963077840342:a 87963077840374:a 87963077840381:6 87963077840392:6 87963346142036:1 87963346144375:1 87963346144942:6 87963346275788:1 87963346275802:2 87963346275808:b 87963346275817:b 87963346275818:b 87963346275820:6 87963346275821:b 87963614577617:0 87963614581408:5 87963614711275:7 87963614711285:f 87963883146670:6 87964151582174:b 87964419886766:a 87964419887216:9 87964420017640:7 87964420017642:7 88029649699702:f 88029649699741:f 88029649700314:6 88029649700454:9 88029649701165:6 88029649703734:f 88029649706260:1 88029649814697:2 88029649833393:1 88029649833411:a 88029649833420:1 88029649833424:6 88029649833430:a 88029649833432:e 88029649833445:7 88029649833457:6 88029649833464:a 88029649833482:6 88029649836770:6 88029649836778:7 88029918135124:1 88029918135138:1 88029918136423:f 88029918137463:1 88029918172866:1 88029918174624:6 88029918268852:6 88029918268857:6 88029918268861:6 88029918268869:b 88029918268889:9 88029918268894:b 88029918268896:b 88029918268901:7 88029918268906:b 88029918268908:6 88029918268910:7 88029918268911:6 88029918268912:5 88029918268922:5 88029918268927:6 88029918268940:5 88029918268943:b 88029918268949:1 88029918268950:b 88029918294849:1 88030186577239:2 88030455007969:a 88030455062283:a 88030455139768:f 88030455139772:5 88030455139778:f 88030455139790:6 88030455139794:6 88030455139807:b 88030455139819:7 88030455139821:b 88030455139822:7 88030455139826:1 88030455139831:b 88030455139854:a 88030455139858:6 88030455143143:5 88030455153209:6 88030455165763:5 88030723480992:b 88030723575218:6 88030723575220:6 88030723575244:1 88030723575245:6 88030723575247:6 88030723575271:6 88030723575272:7 88030723578594:6 88030723578597:6 88030991881014:f 88030991989501:a 88030991991977:2 88030992010677:6 88030992010693:f 88030992010723:9 88030992010749:6 88030992010761:0 88031260446148:e 88031528881604:e 88031797183316:1 88031797183387:6 88031797183431:6 88031797186222:a 88031797186537:b 88031797186672:9 88031797188801:6 88031797189908:1 88031797317049:6 88031797317058:f 88031797317097:b 88031797317109:f 88031797317111:b 88031797320416:6 88032065618786:1 88032065619658:5 88032065620703:f 88032065621111:1 88032065623324:5 88032065752497:1 88032065752498:6 88032065752515:a 88032065752527:6 88032065752544:b 88032065752551:b 88032065752559:6 88032065752573:6 88032065752589:6 88032065752590:a 88032065755874:5 88032334053428:f 88032334054195:e 88032334054874:6 88032334055391:f 88032334055527:f 88032334056161:6 88032334057584:9 88032334059713:b 88032334062505:a 88032334090141:6 88032334187959:a 88032334187967:6 88032334187974:5 88032334187979:5 88032334187984:6 88032334187990:a 88032334188007:b 88032334188018:5 88032334188021:f 88032334188031:6 88032334188054:b 88032334191325:6 88032334191333:6 88032334191335:5 88032334201401:a 88032602496343:2 88032870964640:b 88033139360610:1 88033139360669:f 88033139360721:0 88033139362093:6 88033139363502:a 88033139363817:b 88033139394625:a 88033139400096:f 88033139475625:6 88033139494321:1 88033139494325:6 88033139494333:6 88033139494339:a 88033139494348:1 88033139494357:b 88033139494363:1 88033139494364:6 88033139494376:7 88033139494377:b 88033139494378:b 88033139494379:7 88033139494394:5 88033139494397:6 88033139494412:5 88033139497696:6 88033139525920:f 88033407796052:1 88033407796123:6 88033407796167:6 88033407796182:5 88033407796838:9 88033407796938:5 88033407797983:f 88033407797985:a 88033407798391:1 88033407799261:f 88033407804051:5 88033407804329:b 88033407810520:b 88033407832198:b 88033407833768:a 88033407833794:1 88033407835625:1 88033407929774:b 88033407929779:f 88033407929780:6 88033407929785:6 88033407929787:1 88033407929794:f 88033407929796:e 88033407929797:f 88033407929799:1 88033407929805:6 88033407929807:6 88033407929808:6 88033407929815:6 88033407929824:b 88033407929826:f 88033407929829:7 88033407929836:a 88033407929837:b 88033407929841:6 88033407929847:b 88033407929857:a 88033407929867:9 88033407929870:a 88033407929871:b 88033407929873:b 88033407929875:5 88033407929878:b 88033407933157:6 88033407933162:b 88033407955778:6 88033407967737:f 88033676365293:b 88033944800711:1 88034213236197:7 88034481539809:a 88034750107127:b 88035018410719:f 88035555279078:f 88035555283056:9 88035555283766:f 88035555285185:b 88035555285997:a 88035555286292:7 88035555342464:5 88035555342710:6 88035555400712:1 88035555413425:1 88035555413426:6 88035555413429:6 88035555413443:a 88035555413452:1 88035555413453:6 88035555413454:6 88035555413472:b 88035555413477:7 88035555413480:7 88035555413482:b 88035555413486:7 88035555413488:5 88035555413494:f 88035555413501:6 88035555413514:6 88035555416800:6 88035555440962:a 88035823718377:b 88035823729624:b 88035823744514:a 88035823751192:9 88035823751302:b 88035823752931:5 88035823760248:a 88035823760539:5 88035823830185:6 88035823848901:f 88035823848926:6 88035823848941:b 88035823848953:5 88035823852253:6 88035823852263:5 88035823862329:a 88035823874883:5 88036092150683:6 88036092150743:5 88036092152543:f 88036092153518:a 88036092185256:5 88036092284349:6 88036092284395:7 88036092284396:a 88036360585379:2 88036360586068:1 88036360586141:f 88036360586198:5 88036360586714:6 88036360587096:5 88036360587367:f 88036360588001:a 88036360588407:1 88036360588974:a 88036360589289:b 88036360589424:9 88036360590134:f 88036360591553:b 88036360594067:5 88036360594345:b 88036360615426:a 88036360622214:b 88036360631160:a 88036360631451:5 88036360648832:5 88036360649078:6 88036360701097:6 88036360719793:1 88036360719796:6 88036360719797:6 88036360719801:6 88036360719819:5 88036360719820:1 88036360719822:6 88036360719824:a 88036360719834:6 88036360719836:6 88036360719839:b 88036360719848:7 88036360719849:b 88036360719854:7 88036360719858:5 88036360719863:b 88036360719873:a 88036360719884:5 88036360719886:b 88036360719887:b 88036360723168:6 88036360723170:6 88036360723173:6 88036629155304:7 88036897464767:a 88037166026249:5 88037434461671:b 88037702764935:f 88037702765700:6 88037702826110:5 88037971205463:2 88038239795522:a 88038776504455:5 88038776505140:5 88038776505238:5 88038776506440:a 88038776506699:6 88038776508032:a 88038776513453:5 88038776520134:b 88038776537399:a 88038776539586:a 88038776567939:a 88038776638902:7 88039044941086:6 88039044941334:a 88039044941514:5 88039044942559:f 88039044943837:b 88039044943928:a 88039044945180:5 88039044946848:1 88039044948961:5 88039044955096:b 88039044955099:a 88039044970281:5 88039044973419:5 88039044974638:e 88039044974657:b 88039044975272:6 88039044976774:b 88039044980128:f 88039044986828:a 88039045003638:a 88039045074350:a 88039045074354:6 88039045074359:a 88039045074362:7 88039045074370:f 88039045074371:a 88039045074373:f 88039045074374:a 88039045074383:6 88039045074389:b 88039045074390:a 88039045074401:5 88039045074405:7 88039045074407:b 88039045074410:b 88039045074413:b 88039045074440:6 88039045077725:6 88039045077738:b 88039045081356:a 88039045116846:f 88039045116847:a 88039313485858:f 88039581810760:a 88039581811496:6 88039581811611:6 88039581811655:6 88039581811665:5 88039581819327:a 88039581926569:6 88039581932552:1 88039581945277:6 88039581945284:e 88039581945292:1 88039581945293:6 88039581945296:6 88039581945302:a 88039581945303:6 88039581945304:e 88039581945312:b 88039581945323:7 88039581945324:a 88039581945329:6 88039581945332:f 88039581945354:6 88039581945358:a 88039581945366:b 88039581948640:6 88039581948642:6 88039581948647:5 88039850246968:a 88039850247068:6 88039850249642:a 88039850287270:a 88039850289220:5 88039850362027:a 88039850384095:6 88039934308531:a 88040118816667:6 88040118843714:a 88040387117286:b 88040387117922:1 88040387118038:5 88040387118039:5 88040387118554:6 88040387118614:a 88040387119176:a 88040387119435:6 88040387119495:f 88040387119642:a 88040387119839:f 88040387120247:1 88040387120260:6 88040387120361:a 88040387120768:a 88040387121129:b 88040387121264:9 88040387121974:f 88040387126185:b 88040387126189:5 88040387147266:a 88040387150135:a 88040387158182:a 88040387163000:a 88040387180670:5 88040387180672:5 88040387251634:6 88040387251635:f 88040387251639:a 88040387251641:6 88040387251674:6 88040387251675:1 88040387251676:6 88040387251679:b 88040387251683:a 88040387251702:f 88040387251709:6 88040387251711:6 88040387251713:a 88040387251721:5 88040387251729:b 88040387255015:5 88040655554414:6 88040655554922:a 88040655555524:5 88040655557091:6 88040655558775:5 88040655687168:5 88040655690467:5 88040655728821:f 88040655732170:a 88041460859043:2 88041460859805:f 88041460860895:f 88041460862185:a 88041460874200:b 88041460894376:6 88041460901956:5 88041460915979:b 88041460993461:6 88041460993474:f 88041460993477:f 88041460993495:6 88041460993512:7 88041460993514:b 88041460993546:6 88041460996837:6 88041461035950:f 88041461035951:a 88041729329832:6 88041997764700:5 88042534641027:6 88042803039763:a 88042803041930:5 88042803047215:5 88042803071068:5 88042803076483:6 88042803217588:6 88043608522886:5 88043876825271:a 88044145213492:f 88044145214260:5 88044145214363:6 88044145217198:a 88044145220884:7 88044145247083:5 88044145248321:b 88044145248348:5 88044145253792:f 88044145253865:1 88044145277054:5 88044145348017:1 88044145348020:6 88044145348028:5 88044145348029:6 88044145348036:e 88044145348045:6 88044145348046:6 88044145348047:6 88044145348064:b 88044145348069:7 88044145348071:b 88044145348075:7 88044145348118:b 88044145351389:6 88044145351392:a 88044413651570:a 88044413653830:a 88044413691936:6 88044413760689:f 88044682118054:a 88044950524330:b 88045218959416:a 88045219096844:a 89060441984433:1 89060978855375:6 89061247290863:6 89061515600624:a 89061784067488:b 89063126342373:6 89063394774510:b 89063663209957:7 89063931645407:a 89064200084194:6 89064736951784:6 89065005387197:6 89065273822644:6 89065542187382:6 89066079129079:b 89066347431386:6 89066615870262:f 89066884435465:0 89067152870864:6 89067421306306:f 89067958050135:2 89068226588798:a 89068763496227:e 89069031903601:b 89069300328561:e 89069568702539:1 89070105636910:a 89070374083541:f 89071179308448:f 89071447742146:1 89071716139171:2 89071984709041:1 89072253144526:a 89072790015452:6 89073326886422:b 89073595321804:1 89073863757293:b 89074132192745:b 89074400628164:e 89129161334103:2 89129429769559:7 89129698205015:2 89129966675852:5 89129966741622:a 89129966765504:5 89130235068579:2 89130503504035:2 89130771980042:a 89130772048333:6 89130772069289:a 89130772077328:2 89131308848867:5 89131308923305:a 89131308929393:a 89131577367509:f 89131577378214:6 89131845789248:b 89131845794218:5 89132382592939:a 89132382653161:9 89132382660721:e 89132651028391:b 89132651030189:1 89132651102396:5 89132919465292:5 89133187865943:2 89133456301399:6 89133724764840:6 89133993205152:f 89134261635137:f 89135066911146:b 89135066951464:a 89135066963747:6 89135067017250:f 89135067023229:a 89135067033519:6 89135067035344:f 89135067039781:f 89135067044780:5 89135067068738:a 89136140651034:a 89136409091415:6 89136677522134:b 89136946016341:a 89136946097691:5 89137029898200:b 89137214427270:b 89138019757152:b 89138019757410:a 89138019804326:6 89138019805599:a 89138019807847:1 89138019820385:a 89138019820906:f 89138019825360:f 89138019858754:a 89138288133079:5 89138288136169:b 89138288138433:b 89138288266704:6 89138288270047:6 89138556572074:b 89138556575063:7 89138556678270:a 89138556678367:a 89138556700485:b 89138556701095:6 105553116301513:1 105553384806629:a 105553921606966:5 105554726993672:5 105555263858377:b 105556337499280:6 105556605970093:1 105556605974603:1 105557142802858:b 105557679802405:f 105557948218809:a 105559290329771:6 105559290415527:2 105561169438272:b 105561169438455:5 105561169444838:5 105561706239656:5 105561706240865:5 105561706241802:a 105562243176752:1 105562243182718:a 105563048421444:1 105563853717921:6 105566538043818:b 105567075021694:0 105567075052406:b 105568417094999:2 105568685563515:6 105568954067359:6 105569222502056:6 105569222527013:f 105569490872375:f 105569759379003:e 105570564611459:6 105570833043590:b 105571906874752:e 105572980533316:1 105573517421702:6 105574322779320:a 105574591216887:6 105575396416673:6 105575396517577:b 105576201761705:5 105576201779319:6 105576470271075:a 105576738645383:1 105577275492553:1 105577812455608:1 105578080877242:a 105578617670692:6 105579959916322:1 105579959944852:5 105580496794182:5 105580765180136:6 105582644223960:b 105582644280761:a 105582912724124:a 105585060089833:b 105585328564279:f 105585328643029:f 105585597067456:5 105585597086633:a 105586670755629:0 105586670813575:6 105586670814750:b 105587476115502:6 105588281359016:5 105589623599230:a 105589623605167:5 105589891928490:b 105590160392609:6 105590160400490:6 105590160400550:6 105590160485839:1 105590428927813:b 105590697335088:1 105590697338022:9 105592039515849:b 105592844749860:6 105592844822968:6 105593113252860:0 105593113267536:b 105593113271432:a 105593650153567:6 105594723822622:a 105621835804904:6 105621835876389:f 105622909546728:6 105623983353775:1 105625325514975:6 105625325547356:5 105627741438140:5 105628009878609:a 105628009888681:a 105628009896720:2 105628546742970:a 105628546762565:b 105629351978669:1 105629351979076:1 105629352046638:6 105629352050876:5 105629620493269:f 105630694238119:a 105632304859173:f 105632841711033:a 105632841744383:1 105633915462473:6 105633915466074:a 105638478848461:0 105639284052394:b 105639552527707:b 105639552527964:a 105639552543719:5 105639552601681:a 105640626339188:6 105641700078228:0 105642505315660:5 105642505334082:6 105644183117482:9 105644451473463:f 105646800277946:a 105647874029000:5 105648142451105:6 105652974377878:a 105653511161138:6 105653511172985:a 105654584996024:1 105655658655067:b 105655927053473:6 105655927154806:a 105655927160055:6 105656195595835:e 105656463961896:a 105656464045337:6 105656464050599:2 105657269264138:a 105658074590304:a 105658343074253:6 105658611511342:6 105659416861935:a 105659953622088:0 105659953691509:5 105661027358435:5 105663174864633:1 105663174930145:5 105663443355959:1 105663711787706:a 105664248648684:1 105665859194786:a 105666127704098:f 105666127707508:6 105679281039473:e 105679817862778:9 105679817923720:a 105679817928417:5 105680623218814:a 105681428448562:6 105681428525102:5 105681428544425:a 105681965395975:a 105682502284569:6 105682770702370:f 105683039136529:6 105683039142008:1 105683039160133:b 105683844338090:b 105683844342701:5 105684381248859:b 105684381342404:6 105684649687720:5 105684649772480:5 105685186641167:a 105686797239795:0 105687065662081:5 105691092199113:b 105691377312496:a 105692434376822:a 105694044986846:a 105694044991614:a 105695387103016:a 105695387168894:a 105695387172984:1 105697803124515:e 105701561184448:5 105701829556407:a 105701829568955:1 105702098082576:2 105702366490750:a 105702903413058:a 105703171734409:a 105703440166235:b 105705050796264:6 105705050869659:1 105705856155870:1 105705856174503:2 105706124602831:1 105706124609573:f 105706124621334:5 105707735146275:5 105708808891488:a 105709614251579:e 105709614280107:5 105711493244994:6 105715519844271:1 105715788280154:a 105716056649338:9 105716056649465:1 105716056708070:6 105716056728354:5 105717130438001:5 105718204110504:5 105720888529397:1 105720888546027:6 105720888553818:a 105723035943329:6 105723036026799:5 105723841328312:a 105723841358773:f 105724109798480:a 105724646566013:2 105727867788923:6 105727867862312:a 105727867875270:a 105727867881509:f 105727867886508:1 105728689936874:5 105729478491407:a 105729746907170:f 105729746908648:a 105729746939740:5 105730552213727:6 105731625977951:6 105733773457753:1 105733773466384:2 105734310370982:1 105736457823509:0 105737799900226:a 105738873636146:6 105738873702207:a 105739158855570:1 105744510893859:e 105744779312437:5 105745047661640:0 105745047731917:5 105745047734583:1 105745047765545:5 105745047783232:f 105745316097371:b 105745316167967:5 105745316171163:a 105747732088751:5 105747732120051:9 105749074287300:6 105749342641955:5 105749342693065:b 105750684877018:9 105750684898296:6 105750684926988:5 105751221734082:1 105751221741686:a 105751221792344:a 105752563913708:5 105752563921142:2 105752563943847:2 105752832356478:a 105752832373838:5 105752832378693:b 105754711432614:4 105754711436040:5 105754979770527:1 105754979851158:a 105754979871496:5 105756053603387:a 105756053604165:b 105756322077129:5 105757664212756:a 105757664216492:1 105757932636076:6 105761153855711:6 105761422295232:6 105761959189420:1 105761959192134:a 105762227604762:6 105763569711287:a 105763569793369:1 105763569802000:2 105764375012684:5 105764375112456:5 105764375118332:a 105765448820849:e 105765985721028:6 105766522560972:0 105768133193441:5 105768133195033:6 105768133204752:2 105768938500737:1 105770549094861:6 105770549096694:2 105770817532096:5 105770817554469:f 105770817583426:a 105773233448649:b 105774038773679:1 105775380957221:f 105775380983650:f 105776186238118:5 105776186272669:1 105776454608951:f 105778870595710:a 105779675838539:1 105779675902175:6 105779675904885:5 105779944341322:6 105779944357135:a 105780481240924:5 105780749658023:a 105781018104141:5 105782628618516:f 105782897139165:6 105782897156511:a 105782897169290:5 105783165492859:6 105783165562137:0 105783165571441:a 105783165584350:5 105783434009756:a 105783702451920:a 105785044655466:6 105785849923497:5 105785849948268:6 105788265861019:1 105789876442092:1 105790413371714:a 105790681755700:6 105792023879459:5 105792023949025:5 105792023949405:a 105793902985437:a 105794171419895:6 105794171431354:a 105794171439578:4 105794171442168:6 105794171470860:5 105794439801608:b 105794439850769:6 105794439855675:e 105794439861140:b 105794708285855:6 105794708320092:5 105796318835406:f 105796318836246:a 105796318894173:a 105796318903040:1 105796318916611:6 105796318919671:a 105797124228674:5 105799003189215:a 105799003257530:5 105799003270372:5 105799003292364:5 105799271624488:a 105799271706717:a 105799271717572:a 105799271719327:a 105799271724566:5 105799271726109:5 105799271742270:5 105799540076776:6 105799540139370:f 105799808558839:5 105799808584103:6 105799808584213:f 105800077013402:6 105800077021517:5 105800345448096:a 105800613898989:6 105800613910395:1 105800882303664:5 105801150753886:5 105801150771036:5 105801687534628:6 105801687618534:6 105801687636935:5 105801687639790:5 105801687641013:f 105801687651660:9 105801956046312:e 105801956048801:9 105801956089422:a 105802224470740:5 105802224484472:5 105802224496079:1 105802224521791:5 105802492809642:b 105802492839218:6 105802492909797:a 105802492916022:7 105802492921775:5 105802492922090:a 105802492925027:a 105802492952578:a 105802761367501:a 105802761382154:5 105802761407743:5 105803029789370:5 105803029802332:f 105803029803070:5 105803298148206:9 105803298222326:2 105803298237825:a 105803298257275:5 105803835101144:a 105803835101553:a 105804103532762:9 105804103544545:5 105804103545400:a 105804103548058:a 105804103550011:a 105804103551534:6 105804103565865:5 105804371954409:a 105804371956998:5 105804640349696:a 105804640430829:6 105804640431005:1 105804640433206:5 105804908784736:a 105804908838329:a 105804908843755:6 105804908846557:6 105804908857901:0 105804908868664:b 105805445742371:e 105805714139254:a 105805714141236:6 105805714141376:5 105805714141494:7 105805714163136:5 105805714163749:f 105805714171630:5 105805714192706:a 105805714196288:f 105805982613506:a 105806787889465:a 105807056340769:5 105807593193660:5 105807593205944:1 105807861636245:6 105808129996766:1 105811351276226:1 105815914625207:a 105816451581405:a 105816988360530:6 105817525312469:f 105817525313194:9 105820478091227:5 105820478139412:a 105821820296614:4 105823514770728:a 105823514776462:6 105823514783663:1 105823514802387:a 105823967752880:5 105823967763933:6 105826652141078:5 105826920468722:1 105827994319227:5 105828799598961:a 105828799607548:f 105828799610127:a 105829067975814:6 105829068030343:6 105829068034795:6 105829336468960:0 105829336478106:6 105829336503648:9 105829604830555:b 105829873263213:1 105829873332447:6 105830678654925:a 105830678666156:1 105832826159749:a 105833094568552:a 105833379764805:6 105833648221568:e 105835241963937:6 105835241972925:5 105835242034156:1 105835242039414:a 105835242041536:5 105835242048365:6 105835242060713:a 105835292374467:a 105837121021260:5 105837658021466:a 105837926463063:f 105838194766453:6 105840610761736:1 105840879187432:e 105842758169569:9 105842758260365:5 105842758262122:5 105843295011243:f 105843295137604:5 105843563556275:a 105843563590422:5 105843563604842:5 105844905772864:f 105846516333406:6 105846784808268:9 105847053216618:a 105848663838948:a 105848932199520:a 105848932271764:5 105848932274075:5 105848932298328:a 105849200685102:6 105849200694299:a 105849200705750:a 105849200707397:b 105849469111254:5 105849469120546:f 105849469120638:a 105849469126575:5 105849469129702:6 105849469139289:5 105849469143573:f 105849737554381:6 105849737559882:6 105849737583300:6 105850005925672:a 105850006007901:a 105850274440395:5 105850274440406:a 105850274443253:b 105850542852841:a 105850542865832:a 105850542877475:5 105850542893322:5 105850542916637:6 105850811233193:5 105850811297844:6 105850811298407:1 105850811304249:a 105851348171352:6 105851348193896:6 105851348212928:5 105851666948025:a 105851666965172:5 105851666980824:5 105851666981523:5 105851968872237:0 105851968929064:a 105851968929670:f 105851968934993:a 105851968938280:5 105851968956572:e 105851968964074:a 105852237307683:6 105852237353730:5 105852237358172:6 105852237362944:5 105852237380941:1 105852237392648:6 105852237395399:5 105852237395400:5 105852237410755:a 105852237421001:5 105852690280748:a 105852690346465:5 105852690382682:5 105852958832396:b 105854300973679:5 105854300977016:a 105854300981393:5 105854569331106:1 105854569391823:2 105854569418342:6 105854569449280:f 105854837836653:6 105855106300661:5 105855106307448:5 105855106307706:5 105855106313816:a 105855106313897:6 105855106317534:e 105855106319035:5 105855106324436:5 105855374705611:a 105855374705614:5 105855374711653:a 105855374711765:f 105855643177615:f 105856716875181:5 105856716900910:6 105857522208638:5 105857790613668:5 105858059077036:1 105858059077471:a 105858327501390:4 105858864355084:a 105859132806164:a 105859132833571:e 105859401156605:6 105859401160231:f 105859401162517:5 105859401163965:5 105859401165777:5 105859401166632:a 105859401178925:0 105859401239571:b 105859485069597:2 105859485110629:a 105859669692115:5 105859669695690:9 105859669699875:a 105860290356815:5 105860290371544:b 105860290416997:a 105860290427681:1 105860290430931:1 105860290455110:a 105860558796162:5 105860558811421:6 105860558858388:1 105860558860253:5 105860558880165:a 105860558896107:5 105860558923477:6 105863159356176:2 105863159370023:5 105863159375515:6 105863159384430:5 105867773075036:5 105867773079001:5 105867773082911:b 105868041554130:5 105884634166456:a 105884634176665:a 105884634185427:6 105884634188207:6 105884634194916:f 105884634196567:a 105884634201900:6 105884634233598:5 106652627934624:b 106652628021167:1 106652628027815:2 106653164826909:2 106653433237410:a 106653433246643:6 106653433261152:a 106653433333573:b 106653701683166:1 106653701749501:a 106653970182270:a 106654238617823:6 106654238640551:2 106654507051839:a 106654507064924:5 106654507071184:b 106655043870499:5 106655312282930:6 106655312293211:b 106722421241113:6 106722958116677:b 106723494897719:f 106723494911779:5 106723494968891:e 106723780071850:f 106724568715499:9 106725105581480:5 106726447777829:f 106726716084650:b 106726716183270:a 106726716190966:2 106727253055244:a 106727521423266:a 106727521503543:1 106727789930231:5 106727789932670:a 106727789935290:a 106728595173160:a 106728595255864:a 106728863677687:6 106728863696709:b 106728863725890:a 106729132107889:f 106729132110484:0 106729400568231:2 106729400572844:1 106729400576949:f 106730205869134:5 106730205873248:7 106730205877240:6 106730474235970:6 106730474291018:6 106731279490391:2 106731547959917:1 106732084830367:1 106732084936483:e 106732353288463:6 106732621770975:a 106732621777207:1 106732621793093:b 106733158578359:b 106733158664615:2 106733963948084:6 106733963950845:a 106734500753192:a 106734500820152:a 106734500820728:a 106734785925546:b 106734785968811:6 106734786026053:7 106735037701276:a 106735037705888:a 106735037717188:6 106735306076245:a 106735574598131:9 106735843018933:6 106735843042971:6 106735843043104:5 106736916728790:5 106737185105810:6 106737185182020:a 106737185230079:5 106737722036725:5 106737722037510:a 106737722044542:a 106737990526435:b 106738258909413:a 106738258921279:a 106738258937280:5 106738527300583:a 106738527354430:6 106738527367087:6 106738795720031:5 106738795813804:1 106738795814310:5 106739601095545:6 106739869539932:5 106740406335670:6 106740406401980:1 106740406415422:5 106740674763013:6 106741211655929:1 106741211703711:6 106741211713905:a 106741480063393:6 106741480139213:6 106741480168208:6 106741748591999:6 106741748631921:0 106742017012542:1 106742553882816:5 106742553885943:6 106742553898721:5 106742822268038:7 106742822333228:b 106743090687323:b 106743359189607:1 106743359205469:a 106743627624500:6 106743627624574:a 106743896063272:a 106743896078681:6 106744164492837:6 106744164503008:0 106744432941483:5 106744432971741:6 106745238253510:a 106745238268680:6 106745506689835:a 106745775110909:a 106745775115778:6 106745775135428:a 106746043541825:a 106746580415858:a 106746580456800:9 106746899114039:f 106746899117047:6 106746899235852:5 106747167629241:a 106747167662741:9 106747385740559:a 106747922604897:a 106748459484820:5 106748459487131:6 106748996323135:a 106749264693909:a 106749264802276:5 106749264804803:5 106749264818797:a 106749281580484:6 106749533208454:f 106749533210935:6 106749801654633:b 106750070068486:a 106750070073457:f 106750338463730:5 106750338532448:b 106750338536440:6 106750875381983:a 106750875398684:9 106751949120936:b 106752485992566:a 106752486016837:b 106752754353458:6 106753291337609:6 106753559668284:6 106753828209219:6 106754096599541:5 106754365099263:6 106754901843130:a 106754901929868:6 106754901936551:6 106755170349023:5 106755170353522:5 106755438714272:b 106755438720293:6 106755438787299:6 106755438820479:5 106755707155132:5 106755707278436:5 106755975603591:6 106755975663185:a 106756244027167:a 106756244131805:a 106756512476135:a 106756512520356:6 106756512542639:6 106756780911591:a 106756780971655:9 106756780978095:5 106757317842567:9 106757586221077:5 106757586263695:a 106757854755138:a 106758173423636:5 106758173464832:5 106758173527305:5 106758391503938:a 106758928448759:6 106758928449823:5 106758928478044:5 106759196878583:5 106759196885383:a 106759196889835:7 106759465339413:f 106759465365080:a 106759465371456:f 106759733768760:a 106759733774894:6 106760002199005:6 106760002221112:b 106760002235412:a 106760270552451:6 106761092659319:6 106761092718202:6 106761092722444:a 106761092731496:6 106761881238104:6 106761881282574:5 106761881289891:5 106762149600615:6 106762149606313:5 106762149661348:1 106762149664546:1 106762418117636:a 106762418128755:a 106762418131391:5 106762686548319:6 106762686570911:a 106762954972673:6 106762955018895:b 106762955019322:6 106763223418719:1 106763223426410:f 106763223432463:a 106763491781983:5 106763491864289:5 106763491879812:a 106763760282015:6 106763760292838:6 106763760299981:a 106764028719230:a 106764028750090:5 106764565597595:a 106764917858093:0 106764917911559:e 106764917945800:5 106765186342826:6 106765186350982:f 106765186378504:6 106765454774629:a 106765454779807:a 106765454795104:5 106765639374176:9 106765907771610:a 106765907789637:b 106765907789861:f 106766176130728:5 106766176132585:1 106766176135223:f 106766444574903:a 106766444664616:6 106766713092441:1 106766981442907:b 106766981509166:6 106766981558114:f 106767518381244:5 106767786806011:6 106768055185192:a 106768055197475:5 106768323680420:5 106768323746308:6 106768592071776:b 106768592119926:a 106768592137310:5 106768860487291:6 106769129043724:b 106769397419872:6 106769665885243:a 106769934330781:1 106770471099808:b 106770471185881:5 106770471216611:b 106770739621536:b 106770739623193:6 106771008035172:5 106771008054113:a 106771293204765:6 106771293270235:6 106771813384691:9 106772350211068:5 106772350228103:9 106772350248490:5 106772618646508:1 106772887089344:5 106772887111104:5 106772887125793:9 106773155540934:a 106773155552016:2 106773423963383:6 106773423990288:a 106773692395554:f 106773692401975:1 106773960831286:7 106773960836927:6 106774497726444:5 106774766072775:a 106775034613725:6 106775303013036:9 106775303019476:f 106775303024396:a 106775571439108:a 106775571455574:6 106775571493490:5 106775839900908:a 106775839936861:b 106775839943506:5 106776108311976:a 106776108339229:a 106776108361937:a 106776376765788:f 106776376791946:5 106776376796960:5 106776645183223:5 106776645188904:a 106777181979954:6 106777182101070:a 106777450514613:6 106777718857892:6 106777987362942:a 106777987393262:5 106778255821223:6 106778255827359:a 106778524224656:5 106778524258203:a 106778792700170:5 106778792723485:6 106779061095382:5 106779061103582:6 106779329476141:a 106779329535631:a 106779329558490:5 106779597968380:5 106779597985415:9 106779597991855:a 106779866307927:2 106780403293192:1 106780671715908:6 106780671726691:a 106780940151245:6 106780940156328:a 106780940156345:a 106780940205246:1 106781476920663:6 106781477023870:a 106781477040769:5 106781745353130:b 106781745470620:b 106781745473447:b 106782013894690:f 106782013903764:b 106782013927260:5 106782282266807:a 106782282337313:5 106782550787909:b 106782550788446:6 106782550788519:2 106782819217056:a 106782819256128:f 106783087647748:a 106783087650006:a 106783087652853:b 106783087654662:6 106783087658867:a 106783356067329:6 106783356083208:1 106783356085451:5 106783356088205:5 106783356096959:6 106784161310028:5 106784429760291:5 106784698181293:1 106785503488127:a 106785503491871:6 106785503555830:6 106785503556272:5 106785503587053:6 106787651035597:0 106787651039542:7 106787651045215:5 106787651045391:b 106787651090754:a 106787919411383:a 106787919475376:5 106788187832737:6 106788187833650:a 106788187839904:b 106788187841133:5 106788187843931:b 106788456363289:6 106788456409199:6 106788724799833:5 106788724836718:9 106799462259226:5 123236570413239:a 123236838841410:a 299067699633495:2 299067699666336:b 370536760778144:b 370537029180759:2 387113187136582:9 105869333357110:6 105868528055595:a 105865306838492:6 105865306855034:5 105865038310751:5 105865038312124:5 88045755829674:a 105867185797302:6 105863964635994:5 105864769937869:0 105873896750438:5 105861817208648:5 105866917449491:5 105861817219819:5 106785771992434:a 106785772007373:a 106785772021264:a 105869333368702:5 105869333361235:0 105869333393229:a 105869333381118:5 105869333394562:6 105869333401321:5 105869333415031:6 88045487427597:a 105868528054502:5 105868528068056:5 105868528071235:5 105868528074316:9 105868528075260:a 105868528086725:5 105868528101388:5 88047098165570:a 105865306842764:5 105865306845091:2 105865306857038:a 105865306863987:b 105865306864830:5 105865306866884:a 105865306872202:6 105865306872490:5 88046829575511:2 105865038306663:6 105865038307949:5 105865038308792:5 105865038307964:5 105865038313234:5 105865038367702:5 105865038376671:6 105865038392713:5 88045755964125:6 88045755866499:6 106787114104779:5 88045755827674:6 105867454305172:f 105867454312689:6 105867454313810:1 105867454344792:a 105867185851044:1 105867185858673:e 88045755960768:a 88045755960849:b 105863964625602:1 105863964584785:a 105863964636344:a 105863964635188:a 105863964642476:6 105863964672716:5 106785235123572:a 105863964686707:b 105880691466019:5 105880691466200:b 105880691517588:1 105880691523097:5 105880691523462:f 105880691532128:5 105880691550364:e 105864769871207:6 105880691550984:5 105864769941508:2 105864769945293:5 105864769947959:1 105864769948954:6 105864769951152:a 105873091445023:5 105873091448219:a 105873091473615:5 105873091468038:a 105873091489528:5 105873091492244:e 105873091504239:a 105873896745385:5 105873896755947:6 105873896751326:1 105873896760682:f 105873896763633:6 105873896766735:a 105873896771214:1 105873896774572:5 105873896778628:6 105873896779262:a 105866917361630:1 105866917432656:b 105866917436893:6 105866917459000:b 105873628309622:a 105873628311744:5 105873628311604:a 105873628311862:7 105873628348195:e 105861817154804:6 105861817160530:6 105861817205535:5 105861817219813:b 105861817157277:5 105861817219822:5 105861817219831:6 105866112053032:a 105866112118910:a 105866112143259:5 105866648987766:a 105866649005150:5 105866649017104:2 105865575254367:6 105865575300328:5 105865843676422:5 105865843702105:1 105865843704022:a 106784966581591:5 105866380552607:6 56167971812633:6 56167971795254:7 105854569403412:a 105854569387197:5 105854837821566:6 105854837865552:a 105854837839159:6 105854837866225:0 105854837879235:a 105854837882618:5 105854837862087:e 90138747134483:a 90138210263571:a 90138478699027:a 90138747134885:a 90138478699429:a 90138210263973:a 90138478698953:a 90138210263497:a 90138747134409:a 90138210259184:a 90138478694640:a 90138747130096:a 90138210258002:a 90138478693458:a 90138747128914:a 90138478698908:a 90138210263452:a 90138747134364:a 90138478694647:a 90138747130092:a 90138210259180:a 56167434860491:5 105859132821094:6 105859132827344:a 105859132816538:a 105859132787394:1 105859132793293:0 105859132802911:1 56167703296681:a 56167703292363:1 106783356022615:5 105855643149532:6 105855643147250:a 105855643149509:a 105855643153148:f 105855643160674:5 105855643168283:5 105855643182804:6 56166629607205:6 105858595968352:a 105858595862475:1 105858595920141:0 105858595923493:6 105858595930001:a 105858595943762:5 105858595963596:5 105858595860513:1 105858864353622:5 105858864287607:5 56166361216452:6 56166898046141:5 56166898059279:a 56166898075998:6 56166898055772:f 56167166486641:e 56167166506265:6 56167166487110:4 105858059057795:6 105858059080556:a 105858059090518:a 105858059072129:1 105858059086575:5 105858059118591:5 56165019016286:6 56165371349549:5 56165287474663:6 56163945294573:6 56163945279536:a 56163945300998:6 56163945336685:6 56164213690869:1 56164213715185:6 56164213744966:a 56164297650152:5 106783087647510:a 105855374758570:a 105855374605766:f 105863159388554:6 105863159362754:a 56162603159351:a 56163676818671:6 56163676827359:6 56162334653278:6 56162334681687:a 56162334681984:5 105857522137074:5 105857522208887:a 105857522233591:5 105857522184466:b 105857522225394:1 105857522226699:d 105857522134814:5 56168508667068:5 56168508675153:a 56168508688815:6 56168508668869:5 56163408399393:5 56163408409938:5 56163492281881:5 56163139890527:5 56163139999591:6 56162871543647:a 56162871550948:e 56162871554253:b 56162116559324:6 105829873349913:6 105829873359623:6 105829873383795:b 105829873260071:f 105868041434003:5 105868041524885:5 105868041555523:5 105851666929920:5 105851666888706:a 105851666928735:1 105851666933156:6 105851666944980:5 105851666962720:5 105851666981529:9 56161797708986:a 56161797816759:5 56161848136240:a 56161797813920:f 106770202684241:a 56161529379414:a 56161529361025:1 56161529393658:6 56161613253165:5 56161529398584:5 56161260915001:a 56161260912518:f 56161260899827:6 56161260910022:a 56161260939420:e 56161311254482:5 56160992488921:5 56160992492831:b 56160992494840:4 56160992464525:5 105850006008049:6 105856985310927:1 105856985320467:b 105856985350860:5 105856985337620:6 105856985338073:1 105856985370362:e 105856985306005:a 105856985311141:5 105849737550053:a 105849737587523:5 105849737587588:6 105849737505756:5 105849737591393:1 105849737548277:1 105849737557752:a 105849737587522:a 105848663814726:5 105848663824640:5 105848663868227:1 105848663818205:1 105848663822029:1 105848663815533:5 105862353945906:6 105862437905823:a 105862353971609:b 105862354012836:1 105862354044152:4 105862354020931:5 105862353957564:5 105848395383057:5 105848395389102:2 105848395386435:5 105848395400674:0 105848395438518:0 105848395386758:6 105849469070367:a 105849469121172:0 105849469124895:5 105849469150860:5 105847321641389:5 105847321630498:1 105847321652945:a 105847321641526:9 105847321651674:5 105847321668510:6 105847321659866:4 105847321586510:5 105861548740954:a 105861548621914:a 105861548620873:6 105861548721102:5 105861548622168:5 105861548768451:1 105861548727062:a 105861548730730:5 88044145348039:1 105856448463933:a 105856448474539:5 105856448472638:1 105848932256095:6 105848932186795:6 105848932292145:a 105848932292218:5 105848932186223:5 105849200712620:1 105849200715280:a 105849200621750:6 105849200685258:5 105849200635641:1 105849200737470:1 105847053225747:5 105847053225988:1 105847053224560:a 105847053251793:5 105847053218316:a 105847053250386:6 105847053209473:5 105851079679755:a 105851079745145:5 105851079682634:9 105851079770803:a 105851079727645:5 105851079745151:5 105851079748206:4 105851079748211:5 105851079766660:b 105851079734328:9 105851079748256:5 105860558872928:5 105860558903021:1 90138747130103:a 90138210259191:a 90138210263302:a 90138478698758:a 90138747134214:a 90138210263185:a 90138478698641:a 90138747134097:a 90138478694636:a 105858864369073:6 105858864383032:5 105858864360006:4 105858864359761:9 105858864421684:5 106782282354314:b 56165555885083:a 56165555825049:b 56165555822578:6 56165555900116:a 56165824335498:b 56165824317279:1 56165824320532:a 56165824239143:f 56165824241828:2 56166092766931:6 56166092683577:a 56166092750624:5 105857790655076:f 105857790656951:5 105857790570068:1 105857790619868:a 105857790622767:6 105857790655590:5 56162603017656:1 56162603098399:5 105829873325056:1 105829923659230:a 105857253699669:a 105857253677921:5 105857253740019:6 105857253742893:b 105857253747473:6 105857253748091:9 105857253755853:5 105857253684791:5 105867772995639:f 105867773068870:f 105867773017511:a 105867773118895:9 105867773069145:a 105867773088320:a 105867773111889:5 105867773075969:5 105868041511388:6 105862353955202:6 106776108377423:5 105844100317226:a 105844100446407:5 105844100464385:5 105844100476247:5 55070876085214:6 55070876036641:5 55070876087661:5 55070876094096:5 55070876094622:a 55070876022532:6 55070876096721:6 55070876100065:1 55070876118921:5 55070876086138:5 55070876084691:5 55070876121649:a 55070876083368:a 105856716881894:5 105856716870918:5 105856716881856:6 105856716914308:5 105856716932292:a 105856716927847:5 106779329486937:e 105847590083429:a 105847590101443:f 105847590072811:a 105847590087017:a 105847590096866:5 105847590083368:a 105847590126330:5 105852237357787:4 106775839950376:5 105843832018243:5 105843831987163:b 105843831980149:5 105843832031923:5 105846516353374:5 105846516380154:6 88043608522885:5 105853495722117:5 55070607675511:a 55070607652807:5 55070607654887:6 55070607666523:6 55070607667189:b 55070607578576:a 106779061108686:6 106779061141038:6 105848126879277:a 105848126937444:5 105848126997315:1 105851348229244:5 105851348238214:5 105851968940938:1 105851968962348:6 105851968968056:5 105851968918079:0 105862890900513:5 105862622460669:a 105862639181784:b 105862890947646:a 105862639229509:6 105862890829790:1 105860290457086:a 105860290487884:5 105860290475507:5 105860290435572:a 105860290422217:5 105861062202761:1 105861062222485:9 105861062232195:5 52901380730932:6 52901380679835:6 52901380726959:5 52901380730939:a 105859938144575:5 105845711053470:1 105845711080004:5 105845711022546:a 105845711048063:1 105845711054401:a 106781208610214:6 105861280210106:a 105861280309819:e 105861280331812:5 105801150744415:5 105801150744927:6 105801150782703:a 105801150756139:a 105801150771407:6 105801150768600:6 53982907202719:5 53982907212742:9 53982907213525:a 53982907189183:6 53982907190851:5 53982907196589:6 52901112298509:5 52901112304532:b 52901112311349:5 52901112285078:5 105845979470381:6 105845979482252:b 55070070849362:5 55070070840446:5 55070070841296:6 55070070799147:a 55070070775711:a 55070070799144:5 55070070814429:1 55070070730712:6 55070070799156:6 55070070810490:4 55070070840967:5 55070070825616:5 55070070849451:5 55069802280907:5 55069802375077:a 55069802354280:5 55069802359885:6 55069802401513:5 55069802348081:0 55069802351276:6 55069802352350:6 55069802353778:6 55069802390795:5 55069802396052:a 55069802357576:9 88040387251694:7 88040387132864:a 105845442630288:5 105862085581069:0 105862085519427:0 105862085519640:9 105837926394281:5 105873091431106:1 105861817180967:5 105861817187270:9 105864769962198:a";
  let PR_MAX = 1.0;
  const PR_F=[0,0.35,0.70,1.00], PR_Q=[0,0.40,0.75,1.00];
  const PR_ROT_F=["Quase nunca","Raramente","Ocasionalmente","Regularmente"];
  const PR_ROT_Q=["Baixa","Média","Alta","Muito alta"];
  const PR_TAB=(()=>{const R={};
   for(const p of PR_RAW.split(" ")){const a=p.split(":");if(a.length!==2)continue;
    const v=parseInt(a[1],16);R[a[0]]=[v>>2,v&3];}
   return R;})();
  function prPar(c){return PR_TAB[String(c.id).split("@")[0]]||null;}
  function prBonus(c){const v=prPar(c); if(!v)return 0;
   return PR_F[v[0]]*PR_Q[v[1]]*PR_MAX;}
  (function(){let n=0,s=0;
   for(const c of D){if(c.id==="MOLDE")continue; if(prPar(c)){n++;s+=prBonus(c);}}
   const sem=D.filter(c=>c.id!=="MOLDE"&&!prPar(c)).length;
   console.log("%cPE RUIM - "+n+" linhas com dado - "+sem+" sem dado - media +"
    +(n?(s/n).toFixed(3):0)+" - PR_MAX="+PR_MAX,
    "color:"+(sem?"#f0a531":"#22c58b")+";font-weight:700");})();
  /* ===== FIM DO PE RUIM ===== */
  function nota(c){const b=notaBase(c);if(c.id==="MOLDE")return b;if(c._fb===undefined)c._fb=bonusPronto(c,0,fisBonus);
 if(c._ia===undefined)c._ia=bonusPronto(c,3,iaBonus);
 if(c._pr===undefined)c._pr=bonusPronto(c,1,prBonus);
 /* 14/08: a punicao de migracao virou PONTO FIXO, como o fisico (±1,5), o estilo
    de IA (+1) e o condicional (+1). Era o unico ajuste do sistema em percentual —
    e percentual pune mais quem ja e alto, o que nao faz sentido aqui. */
 /* 15/08: punEstilo APAGADO. Nao existe mais punicao de migracao —
    o que vale e o bonus de quem E da funcao. */
 /* 13/08: bonus de ESTILO ATIVO. Mesma forma da punicao — % sobre a base
    positiva — mas somando para quem ativa, em vez de descontar de quem nao. */
 const bo=bonusPronto(c,2,bonEstilo);
 /* o piso e a ULTIMA coisa: os bonus de corpo e de IA entram depois do Bloco 1
    e podiam jogar o card de volta pra baixo de zero */
 return piso(b+c._fb+c._ia+c._pr+bo,c.tipo);}   /* 15/08: o -p (punicao de migracao) SAIU. Abolida em 05/08. */
function toggleMigPun(){ return; }   /* 15/08: o botao da punicao nao faz mais nada */
function _toggleMigPun_morto(){
 MIG_I=(MIG_I+1)%MIG_ESCALA.length;
 PUN_ESTILO=MIG_ESCALA[MIG_I];
 MIG_PUN=PUN_ESTILO>0?1:0;
 for(const c of D){delete c._n;}
 const b=document.getElementById('migbt');
 if(b){b.textContent=PUN_ESTILO===0?'migração: sem punição':('migração: −'+String(PUN_ESTILO));
  const cor=PUN_ESTILO===0?'#8b949e':'#c4a5ff';b.style.borderColor=cor;b.style.color=cor;}
 traducaoViva();render();}
function notaMed(t){const m=MED[t];if(!m)return 0;let s=0,tt=0;for(let i=0;i<5;i++){s+=m[BK[i][0]]*W[i];tt+=W[i];}return tt?s/tt:0;}
function _mel(b,j){if(!b||b<=0)return '—';const p=(j-b)/b*100;return (p>0?'+':'')+p.toFixed(1)+'%';}
function _melTot(c,ET,ST){let sb=0,sj=0;(c.arows||[]).forEach(r=>{const b=ET&&ET[r[0]]?ET[r[0]][0]:(ST?(ST[r[0]]||0):0);if(b>0){sb+=b;sj+=r[3];}});return sb>0?(sj-sb)/sb*100:null;}
function sigDe(t){for(const[f,ts]of FAM)if(ts.includes(t))return (SIG[f]||'').replace(/ · /g,'/');return '';}
function nomeRanking(nome){
 const p=String(nome||'').trim().split(/\s+/);const primeiro=p.shift()||'';
 return '<span class="rn1">'+primeiro+'</span><span class="rn2">'+(p.join(' ')||'&nbsp;')+'</span>';
}
function estiloRanking(c){
 const md=(c.modelo&&c.modelo!==c.tipo)?c.modelo:'';
 const porExtenso={
  'Jog. de infiltração':'Jogador de infiltração',
  'Jog. de Infiltração':'Jogador de infiltração',
  'Especialista em cruz.':'Especialista em cruzamento',
  'Finaliz. acrobática':'Finalização acrobática',
  'Arrem. lateral longo':'Arremesso lateral longo',
  'Arrem. longo do GO':'Arremesso longo do goleiro',
  'Repos. baixa do GO':'Reposição baixa do goleiro',
  'Defesa direta (GO)':'Defesa direta do goleiro',
  'Grito de garra (GO)':'Grito de garra do goleiro'
 };
 return md?'<span class=cdmdl>'+(porExtenso[md]||md)+'</span>':'';
}
function etiquetaRanking(c){
 /* No Ranking, nativo é a função que nasce da posição nativa da carta com
    o estilo ativo. Não é o campo de segunda posição: ele só descreve as
    posições que também podem ser compradas. */
 if(funcDaPos(c.np,c.modelo)===c.tipo)return '<span class="tg rn">NATIVO</span>';
 if(!estiloAtiva(c))return '<span class="tg se" title="o estilo de jogo nao atua nesta funcao">BÁSICO</span>';
 return '';
}
function cor(n,ref){
 var _c = document.documentElement.getAttribute('data-tema')==='claro'
   ? ['#0a7d4f','#2f7d55','#8a5a00','#b3361f']
   : ['#22c58b','#8fd694','#f0a531','#e0533d'];
 return n>=ref+12?_c[0]:n>=ref?_c[1]:n>=ref-12?_c[2]:_c[3];}

const _bloco=f=>{const ts=(FAM.find(z=>z[0]===f)||[0,[]])[1];
 return `<div class=famg><div class="famt fambt" data-g="${f}"><b>${f}</b>${SIG[f]?`<i>${SIG[f]}</i>`:``}</div><div class=tabs>${ts.map(t=>`<div class=tab data-t="${t}">${ROT[t]||t}</div>`).join('')}</div></div>`;};
document.getElementById('fam').innerHTML=
 `<div class=setor><div class=setl>★</div><div class=setg><div class=famg><div class=tabs><div class=tab data-t="★ GERAL">por card</div><div class=tab data-t="★ GERAL · por jogador">por jogador</div><div class=tab data-t="★ GERAL · mix">Mix</div></div></div></div></div>`+
 SET.map(([nome,gs])=>`<div class=setor><div class=setl>${nome}</div><div class=setg>${gs.map(_bloco).join('')}</div></div>`).join('');
document.querySelectorAll('.fambt').forEach(el=>el.onclick=()=>{const g=el.dataset.g;if(g==='★')return;S.tipo='grp:'+g;document.querySelectorAll('.tab,.fambt').forEach(x=>x.classList.remove('on'));el.classList.add('on');render();});
document.querySelectorAll('.tab').forEach(el=>el.onclick=()=>{S.tipo=el.dataset.t;document.querySelectorAll('.tab,.fambt').forEach(x=>x.classList.remove('on'));el.classList.add('on');render();});
document.querySelector('.tab').classList.add('on');
document.querySelectorAll('#view div').forEach(el=>el.onclick=()=>{S.view=el.dataset.v;document.querySelectorAll('#view div').forEach(x=>x.classList.remove('on'));el.classList.add('on');render();});
document.querySelectorAll('#orig div').forEach(el=>el.onclick=()=>{S.orig=el.dataset.o;document.querySelectorAll('#orig div').forEach(x=>x.classList.remove('on'));el.classList.add('on');render();});
['mk','hnat','hsp','hs'].forEach(id=>{const e=document.getElementById(id);if(e)e.onchange=render;});

function pesosUI(){
 document.getElementById('pesos').innerHTML=BKV.map(([b,i])=>
  `<div class=pw><label style="color:${b[2]}">${b[1]}</label><input type=range min=0 max=60 step=0.5 value=${W[i]} data-i=${i}><div class=v id=pv${i}></div></div>`
 ).join('')+`<b style="font-size:10px;color:#5d6673;align-self:center">PRESETS</b><button class=btn data-p=of>D · 50/25/15/10</button><button class=btn data-p=c>C · 55/20/15/10</button><button class=btn data-p=a2>A · 60/20/10/10</button><button class=btn data-p=b2>B · 49/14/19/14</button><button class=btn data-p=e2>E · 40/30/20/10</button>`;
 document.querySelectorAll('#pesos input').forEach(el=>el.oninput=e=>{W[+e.target.dataset.i]=+e.target.value;render();});
 document.querySelectorAll('#pesos button').forEach(b=>{if(b.id==='condbt'){b.onclick=toggleCond;return;}b.onclick=()=>{W=PRE[b.dataset.p].slice();if(!B3ON)W[2]=0;traducaoViva();pesosUI();render();};});
}
function syncP(){const t=W.reduce((a,b)=>a+b,0);BK.forEach((b,i)=>{const e=document.getElementById('pv'+i);if(e)e.textContent=t?Math.round(100*W[i]/t)+'%':'0%';});
 const pt=document.getElementById('pesotxt');
 if(pt&&t){const f=i=>Math.round(100*W[i]/t);pt.textContent=[f(0),f(1),f(3),f(4)].filter((v,k)=>k!==2||v>0).join(' / ');}}

/* Setores do Ranking: o primeiro clique mostra todas as funções daquele setor.
   Os chips continuam disponíveis para quem quiser recortar por função. */
function funcoesSetorRanking(setor){
 const pega=n=>(FAM.find(x=>x[0]===n)||['',[]])[1];
 const volantes=pega('VOLANTE');
 const mapa={
  Goleiro:pega('GOLEIRO'),
  Defesa:[...pega('ZAGUEIRO'),...pega('LATERAL'),...volantes.filter(f=>f!=='Volante de construção')],
  Meio:[...volantes.filter(f=>f==='Volante de construção'),...pega('MEIA DE LIGAÇÃO'),...pega('MEIA LATERAL'),...pega('MEIA ATACANTE')],
  Ataque:[...pega('PONTA'),...pega('CENTROAVANTE')]
 };
 return mapa[setor]||[];
}
function grupoRankingAtual(){
 if(!S.tipo.startsWith('grp:'))return null;
 const chave=S.tipo.slice(4);
 if(chave.startsWith('setor:')){const setor=chave.slice(6);return [setor,funcoesSetorRanking(setor)];}
 return FAM.find(z=>z[0]===chave)||null;
}
function posfabUI(){
 const sel=document.getElementById('posfab');if(!sel)return;
 const GRP=grupoRankingAtual();
 const GERAL=isGeral(S.tipo)||!!GRP;const c={};
 for(const x of D){if(x.id==='MOLDE')continue;if(!GERAL&&x.tipo!==S.tipo)continue;
  if(x.MIG||x.sec!==null)continue;c[x.np]=(c[x.np]||0)+1;}
 const ord=Object.entries(c).sort((a,b)=>b[1]-a[1]);const atual=sel.value;
 sel.innerHTML='<option value="">todas</option>'+ord.map(([p])=>`<option value="${p}"${p===atual?' selected':''}>${POSN[p]||p}</option>`).join('');
 if(atual&&!ord.some(([p])=>p===atual))sel.value='';}
/* 13/08 (Luis): quantos por cento da nota do PRIMEIRO da funcao.
   O topo de cada funcao vale 100%. Serve para comparar entre funcoes, porque
   funcao de molde mais duro da nota menor para todo mundo. NAO e percentil:
   e a razao entre a nota do card e a nota do lider da MESMA funcao. */
var _TOPO={};
function pctTopo(c,n){
 var p=(c&&c.__cn&&typeof c.percentual_topo==='number'&&isFinite(c.percentual_topo))
  ? c.percentual_topo : null;
 if(p===null)return '';
 var cr=p>=99.5?'#8fd694':(p>=90?'#f0a531':'var(--txt3)');
 return '<span class=pcttopo style="color:'+cr+'" title="percentual oficial publicado para esta função">'+p.toFixed(2)+'%</span>';}
function topoDoTipo(t){
 if(_TOPO[t]!==undefined)return _TOPO[t];
 for(var i=0;i<D.length;i++){var c=D[i];if(!c||!c.__cn||c.tipo!==t)continue;
  if(typeof c.topo_funcao==='number'&&isFinite(c.topo_funcao)&&c.topo_funcao>=0)
   return _TOPO[t]=c.topo_funcao;}
 return _TOPO[t]=0;
}
function lista(){
 const q=nz(window._rkBusca||''),vm=+document.getElementById('vm').value||0;
 const GRP=grupoRankingAtual();
 const tr=document.getElementById('tier').value,og=S.orig;
 const pf=(document.getElementById('posfab')||{}).value||'';
 const fg=(document.getElementById('funcaoGeral')||{}).value||'';
 const mx=document.getElementById('mx').value,ps=document.getElementById('ps').value;
 const md=(document.getElementById('mdl')||{}).value||'';
 const mg=(document.getElementById('mig')||{}).value||'';
 const nv=(document.getElementById('nova')||{}).value||'';
 const GER=isGeral(S.tipo)||!!GRP;
 const chaveCalculo=(typeof CMODE!=='undefined'?CMODE:0)+'|'+(typeof PISO_ON!=='undefined'?PISO_ON:0)+'|'+W.join(',');
 if(window._rkChaveCalculo!==chaveCalculo){window._rkChaveCalculo=chaveCalculo;_TOPO={};D.forEach(c=>{if(c&&c.id!=='MOLDE')delete c._n;});}
 let L=D.filter(c=>c.id!=='MOLDE'&&(GER?(GRP?GRP[1].includes(c.tipo):true):c.tipo===S.tipo)&&c.votos>=vm&&(!q||nz(c.nome).includes(q)));
 /* Ranking Geral: antes de desenhar, compara todas as funções disponíveis.
    A aba "por card" conserva a melhor função de cada carta; a aba "por
    jogador" conserva a melhor entre todas as versões e funções do jogador. */
 
 if(tr==='S+ e S')L=L.filter(c=>c.tier==='S+'||c.tier==='S');else if(tr)L=L.filter(c=>c.tier===tr);
 if(og==='nat')L=L.filter(c=>!c.sec);else if(og==='sec')L=L.filter(c=>c.sec);
 if(pf)L=L.filter(c=>c.np===pf);
 if(isGeral(S.tipo)&&fg)L=L.filter(c=>nomeFuncaoRanking(c.tipo)===fg);
 if(GRP)L=L.filter(c=>GRP[1].includes(c.tipo));
 if(mx==='1')L=L.filter(c=>c.temMax);else if(mx==='0')L=L.filter(c=>!c.temMax);
 if(ps==='1')L=L.filter(c=>c.raras.length);else if(ps==='0')L=L.filter(c=>!c.raras.length);
 if(md)L=L.filter(c=>(c.modelo||'')===md);
 if(mg==='nat')L=L.filter(c=>!c.MIG);else if(mg==='mig')L=L.filter(c=>c.MIG);
 if(nv)L=L.filter(c=>c.NOVO);
 /* No Geral, a nota precisa ser exatamente a mesma nota fixa exibida na
    Ficha. `nota(c)` usa a leitura bruta da grade e podia expor a b1n sem os
    ajustes que a Ficha recebe do retrato salvo pelo motor. */
  L.forEach(c=>{
   if(c.__cn&&typeof c.pontuacao_final==='number'){
    c._n=c.pontuacao_final;
   }else if(isGeral(S.tipo)&&typeof window.t6NotaDoMotor==='function'){
   /* Substitui tambem uma nota antiga que tenha ficado em memoria apos a
      navegacao por outra funcao. */
   c._n=window.t6NotaDoMotor(c);
  }else if(c._n===undefined)c._n=nota(c);
 });
 L.forEach(c=>{c._pct=(c.__cn&&typeof c.percentual_topo==='number'&&isFinite(c.percentual_topo))?c.percentual_topo:0;});
 L.forEach(c=>{c._org = c.MIG ? 3 : (c.sec!==null && c.sec!==undefined ? 2 : 1);});
 /* ARQUITETURA DO GERAL
    1. A Mix é a lista-base: todas as linhas, ordenadas pela nota.
    2. Por card só mantém a primeira linha de cada ID de carta da Mix.
    3. Por jogador só mantém a primeira linha de cada nome da Mix.
    Assim, as três vistas sempre partem exatamente da mesma classificação. */
 if(isGeral(S.tipo)){
  L.sort((a,b)=>b._n-a._n || String(a.id).localeCompare(String(b.id)) || String(a.tipo).localeCompare(String(b.tipo)));
  if(S.tipo==='★ GERAL' || S.tipo==='★ GERAL · por jogador'){
   const vistos=new Set(),porJogador=S.tipo==='★ GERAL · por jogador';
   L=L.filter(c=>{const chave=porJogador?nz(c.nome):String(c.id).split('@')[0];if(vistos.has(chave))return false;vistos.add(chave);return true;});
   L.forEach(c=>c._cmp=1);
  }
 }else{
  L.forEach(c=>c._dups=0);
  if(document.getElementById('uniq').checked){const seen={};L.sort((a,b)=>b._n-a._n);L=L.filter(c=>{const k=nz(c.nome);if(seen[k]){seen[k]._dups++;return false;}seen[k]=c;return true;});}
  const k=S.sort;
  if(k==='nome')L.sort((a,b)=>S.dir*a.nome.localeCompare(b.nome));
  else L.sort((a,b)=>S.dir*((k==='nota'?a._n:a[k])-(k==='nota'?b._n:b[k])));
 }
 return L;
}
function mdlUI(){
 const el=document.getElementById('mdl');if(!el||el.dataset.t===S.tipo)return;
 el.dataset.t=S.tipo;
 const GRP=grupoRankingAtual();
 const GERAL=isGeral(S.tipo)||!!GRP;
 const cs=D.filter(c=>c.id!=='MOLDE'&&(GERAL?(GRP?GRP[1].includes(c.tipo):true):c.tipo===S.tipo)),cnt={};
 cs.forEach(c=>{const m=c.modelo||'—';cnt[m]=(cnt[m]||0)+1;});
 el.innerHTML='<option value="">Todos</option>'+Object.keys(cnt).sort().map(m=>`<option value="${m}">${m}</option>`).join('');}
function funcaoGeralUI(){
 const campo=document.getElementById('funcaoGeralFld'),sel=document.getElementById('funcaoGeral');if(!campo||!sel)return;
 const geral=isGeral(S.tipo);campo.style.display=geral?'':'none';
 if(!geral){sel.value='';return;}
 const atual=sel.value;
 const funcoes=[...new Set(D.filter(c=>c.id!=='MOLDE').map(c=>nomeFuncaoRanking(c.tipo)))].sort((a,b)=>a.localeCompare(b,'pt-BR'));
 sel.innerHTML='<option value="">todas</option>'+funcoes.map(f=>`<option value="${f}"${f===atual?' selected':''}>${f}</option>`).join('');
}
/* ===== v141 · CARREGAR AOS POUCOS =====
   Antes o corte era seco em 240 (cards) e 500 (tabela) e o resto nao existia.
   Agora abre com 100 e carrega mais conforme o usuario desce, com botao no fim. */
let VIS=100, VIS_MANTER=false;
const VIS_PASSO=100;
function maisCards(){ VIS+=VIS_PASSO; VIS_MANTER=true; render(); }
function todosCards(){ VIS=1e9; VIS_MANTER=true; render(); }
/* O cabeçalho é redesenhado quando chegam novos lotes. Um único clique
   delegado mantém os setores e as funções responsivos mesmo nessa troca. */
if(!window._rkMenuLigado){
 window._rkMenuLigado=true;
 document.addEventListener('click',e=>{
  const setor=e.target.closest('#mline [data-rksetor]');
  const fn=e.target.closest('#mline [data-rkfn]');
  if(!setor&&!fn)return;
  e.preventDefault();e.stopImmediatePropagation();
  if(setor){
   const nome=setor.dataset.rksetor;window._rkSetorAberto=nome;
   S.tipo=nome==='Geral'?'★ GERAL':'grp:setor:'+nome;
   document.querySelectorAll('.tab,.fambt').forEach(x=>x.classList.remove('on'));
   render();return;
  }
  S.tipo=fn.dataset.rkfn;
  document.querySelectorAll('.tab,.fambt').forEach(x=>x.classList.remove('on'));
  const o=[...document.querySelectorAll('.tab')].find(x=>x.dataset.t===S.tipo);if(o)o.classList.add('on');
  render();
 },true);
}
function render(){
 /* O renderizador legado abaixo pertence exclusivamente ao Ranking. Vários
    recálculos e a carga tardia ainda o chamam, mas nenhuma outra rota pode
    reconstruir #mline nem #out. Sem autoridade canônica, falha fechado. */
 if(!_t6RotaCanonicaEh('ranking'))return false;
 if(!VIS_MANTER)VIS=100; VIS_MANTER=false;
 mdlUI();
 posfabUI();
 funcaoGeralUI();
 syncP();
 const GRP=grupoRankingAtual();
 const GERAL=isGeral(S.tipo)||!!GRP;
 const L=lista(),ref=GERAL?0:notaMed(S.tipo),mk=document.getElementById('mk').checked;
 const HN=document.getElementById('hnat').checked,HP=document.getElementById('hsp').checked,HS=document.getElementById('hs').checked;
 const cls=c=>(c.MIG?' mig':'');
 const _ok=c=>GRP?GRP[1].includes(c.tipo):(GERAL||c.tipo===S.tipo);
 const _nat=D.filter(c=>c.id!=='MOLDE'&&_ok(c)&&!c.sec).length,_tot=D.filter(c=>c.id!=='MOLDE'&&_ok(c)).length;
 document.getElementById('cnt').textContent=L.length+' cards'+(L.length>VIS?' ('+Math.min(VIS,L.length)+' na tela)':'')+' · '+_nat+' nativos de '+_tot+' na função';
 {
  const grupos=(typeof FAM!=='undefined'?FAM:[]), pega=n=>(grupos.find(x=>x[0]===n)||['',[]])[1];
  const volantes=pega('VOLANTE');
  const setores=[['Geral',['★ GERAL','★ GERAL · por jogador','★ GERAL · mix']],['Goleiro',pega('GOLEIRO')],['Defesa',[...pega('ZAGUEIRO'),...pega('LATERAL'),...volantes.filter(f=>f!=='Volante de construção')]],['Meio',[...volantes.filter(f=>f==='Volante de construção'),...pega('MEIA DE LIGAÇÃO'),...pega('MEIA LATERAL'),...pega('MEIA ATACANTE')]],['Ataque',[...pega('PONTA'),...pega('CENTROAVANTE')]]];
  const setorAtivo=GRP?GRP[0]:(GERAL?'Geral':(setores.find(x=>x[1].includes(S.tipo))||setores[1])[0]);
  const aberto=window._rkSetorAberto||setorAtivo, atual=(setores.find(x=>x[0]===aberto)||setores[1]);
  const botoesSetor=setores.map(x=>`<button type="button" class="rksetor${x[0]==='Geral'?' geral':''}${x[0]===aberto?' open':''}" data-rksetor="${x[0]}">${x[0]}</button>`).join('');
  const chips=atual[1].map(f=>`<button type="button" class="rkfunc${f===S.tipo?' on':''}" data-rkfn="${f}">${f==='★ GERAL'?'por card':f==='★ GERAL · por jogador'?'por jogador':f==='★ GERAL · mix'?'Mix':f}</button>`).join('');
  document.getElementById('mline').innerHTML=`<div class="rksetores">${botoesSetor}</div><div class="rktools"><input id=rklineq type=search placeholder="buscar nesta função" value="${String(window._rkBusca||'').replace(/&/g,'&amp;').replace(/"/g,'&quot;')}"><button type="button" id="rkbandfilters">Filtros</button></div><div class="rkfuncoes">${chips}</div>`;
  const rq=document.getElementById('rklineq');rq.oninput=()=>{window._rkBusca=rq.value;render();requestAnimationFrame(()=>{const x=document.getElementById('rklineq');if(x){x.focus();x.setSelectionRange(x.value.length,x.value.length);}});};
  document.getElementById('rkbandfilters').onclick=()=>document.documentElement.classList.toggle('t6filtrosaberto');
  }
  const out=document.getElementById('out');
  if(!D.some(c=>c&&c.id!=='MOLDE')){
   out.textContent='';
   const caixa=document.createElement('section');
   caixa.id='_estado_builds_publicadas';caixa.setAttribute('role','status');
   caixa.style.cssText='margin:34px auto;max-width:720px;padding:22px 24px;border:1px solid #344054;border-radius:14px;background:#111827;color:#e6edf3;font:15px/1.5 system-ui;text-align:center';
   const titulo=document.createElement('h2');titulo.style.cssText='margin:0 0 8px;color:#f0a531;font-size:19px';titulo.textContent='Builds publicadas ainda indisponíveis';
   const texto=document.createElement('p');texto.style.cssText='margin:0;color:#aab4c3';texto.textContent=(window.CLUBE_NOVO_FRONTEND_ESTADO&&window.CLUBE_NOVO_FRONTEND_ESTADO.mensagem)||'Ainda não há builds completas e publicadas para exibir.';
   const regra=document.createElement('p');regra.style.cssText='margin:9px 0 0;color:#7f8b9d;font-size:12px';regra.textContent='A tela não usa dados de teste, linhas parciais nem fontes legadas.';
   caixa.append(titulo,texto,regra);out.appendChild(caixa);
   return true;
  }
  if(S.view==='cards'){
  const _M=MED[S.tipo]||{};const mSegs=BKV.map(([b,j])=>`<div style="flex:${W[j]*Math.max(0,_M[b[0]]||0)||0.001};background:${b[2]}"></div>`).join('');
  const moldeCard=GERAL?'<div id=moldecd class="rksentinel" aria-hidden="true"></div>':(!MODO_ADM?"":`<div class=cd id=moldecd style="border:1.5px dashed #8fa4c4;background:#10161f"><div class=ovx>MOLDE</div>
   <div style="width:66px;height:88px;margin:4px auto;display:flex;align-items:center;justify-content:center;font-size:34px;background:#151d29;border-radius:8px">⬥</div>
   <div class=nm>Molde do tipo</div>
   <div class=mi>mediana dos ${(MED[S.tipo]||{}).n||0} cards</div>
   <div class=nt style="color:#8fa4c4">${ref.toFixed(1)}</div>
   <div class=mb>${mSegs}</div>
   <div class=tags><span class=tg>referência</span></div></div>`);
  out.innerHTML='<div class=grade>'+moldeCard+L.slice(0,VIS).map((c,i)=>{
   const m=mk&&isM(c);
   const segs=BKV.map(([b,j])=>`<div style="flex:${W[j]*Math.max(0,c[b[0]])||0.001};background:${b[2]}"></div>`).join('');
    return `<div class="cd${cls(c)}" data-k="${c.id}|${c.tipo}" data-rknome="${nz(c.nome)}"><div class=rk>${i+1}º</div>   <img src="${_fotoCN(c)}" loading=lazy onerror="this.outerHTML='<div style=&quot;width:66px;height:88px;margin:4px auto;display:flex;align-items:center;justify-content:center;font-size:26px;background:#151d29;border-radius:8px;color:#3a4350&quot;>👤</div>'">
   <div class=nm>${nomeRanking(c.nome)}${c.velha?' <span class="tg vl" title="o motor está recalculando esta linha — esta é a pontuação anterior">↻ refazendo</span>':''}</div>
   <div class=mi><b style="color:${c.tipo!==S.tipo?'#f0a531':'#8fd694'}">${nomeFuncaoRanking(c.tipo)}</b> <span style="color:#4f8cff;font-weight:700">${(typeof SIGJ!=='undefined'&&SIGJ[c.np])||c.np||''}</span><span class=admonly> · ${c.tier} · ${c.votos} votos</span>${estiloRanking(c)}</div>
   <div class=nt style="color:${cor(c._n,ref)}">${_nd(c._n)}<span class=ntsub><b style="color:${c._pct>=99.5?'#8fd694':(c._pct>=90?'#f0a531':'var(--txt3)')}">${(c._pct||0).toFixed(2)}%</b> do topo</span></div><div class=rktag>${etiquetaRanking(c)}</div>
   <div class=mb>${segs}</div>
   <div class=tags></div>
   </div>`;}).join('')+'</div>';
 }else{
  out.innerHTML='<table><tr><th>#</th><th data-s=nome>Card</th><th data-s=nota>Pontuação</th><th data-s=_pct title="percentual da nota do 1o colocado desta funcao">% topo</th>'+
   BKV.map(([b])=>`<th data-s=${b[0]} style="color:${b[2]}">${b[1]}</th>`).join('')+
   '<th data-s=sisOvr>MÁX</th><th data-s=votos>Votos</th><th data-s=h>Alt</th></tr>'+
   L.slice(0,VIS).map((c,i)=>{const m=mk&&isM(c);
    return `<tr class="r${cls(c)}${c.NOVO?' nova':''}" data-k="${c.id}|${c.tipo}"><td class=mini>${i+1}</td>
    <td><span class=nm2>${c.nome}</span>${c.NOVO?' <span class="tg nv">NOVA</span>':''}${c.MIG?' <span class="tg mg">MIG</span>':''}${estiloAtiva(c)?'':' <span class="tg se" title="o estilo de jogo dele não liga nesta posição — aqui ele joga como BÁSICO">BÁSICO</span>'}${m?' <span class="tg m">meta</span>':''}${c.sec?' <span class="tg s2">2ª</span>':''}${c.raras.length?` <span class="tg r">${c.raras.length}★</span>`:''}<br><span class=mini>${c.tier} · ${c.foot} · ${c.h}cm/${c.w}kg${c.temMax?'':' · sem MÁX'}</span></td>
    <td style="font-weight:800;font-size:14px;color:${cor(c._n,ref)}">${c._n.toFixed(1)}</td>
    <td style="font-weight:800;font-size:13px;color:${c._pct>=99.5?'#8fd694':(c._pct>=90?'#f0a531':'var(--txt3)')}">${(c._pct||0).toFixed(2)}%</td>`+
    BKV.map(([b])=>`<td style="color:${b[2]}">${c[b[0]].toFixed(0)}</td>`).join('')+
    `<td>${c.sisOvr.toFixed(1)}</td><td class=mini>${c.votos}</td><td class=mini>${c.h}</td></tr>`;}).join('')+'</table>';
  out.querySelectorAll('th[data-s]').forEach(th=>th.onclick=()=>{const s=th.dataset.s;if(S.sort===s)S.dir*=-1;else{S.sort=s;S.dir=-1;}render();});
 }
 out.querySelectorAll('[data-k]').forEach(el=>el.onclick=()=>abrir(el.dataset.k));
 const mc=document.getElementById('moldecd');if(mc)mc.onclick=()=>abrir("MOLDE|"+S.tipo);
 montaMais(L.length);
}
/* o rodapé que carrega mais: sentinela invisível + botão.
   A sentinela dispara sozinha quando o usuário chega perto do fim;
   o botão fica para quem prefere clicar (ou se o observer não pegar). */
let VIS_OBS=null;
function montaMais(total){
 const out=document.getElementById('out');
 const velho=document.getElementById('maiswrap'); if(velho)velho.remove();
 if(VIS_OBS){VIS_OBS.disconnect();VIS_OBS=null;}
 if(total<=VIS) return;
 const faltam=total-VIS;
 const d=document.createElement('div');
 d.id='maiswrap'; d.className='maiswrap';
 d.innerHTML='<div id=sentinela></div>'+
  '<button class=maisbt onclick="maisCards()">ver mais '+Math.min(VIS_PASSO,faltam)+
  ' <span class=mini>· faltam '+faltam+'</span></button>'+
  (faltam>VIS_PASSO?'<button class="maisbt maisbt2" onclick="todosCards()">ver todos os '+total+'</button>':'');
 out.appendChild(d);
 const alvo=document.getElementById('sentinela');
 if(alvo&&'IntersectionObserver' in window){
  VIS_OBS=new IntersectionObserver(es=>{ if(es.some(e=>e.isIntersecting)) maisCards(); },{rootMargin:'600px'});
  VIS_OBS.observe(alvo);
 }
}
function ptsAttr(r){const d=r[4],p=r[1];if(!p)return 0;if(d>=0)return _bon(d,p);if(p===1)return 0;return -_fal(-d,p);}
function reabrir(key){const ov=document.getElementById('ov');const sc=ov?ov.scrollTop:0;abrir(key);if(ov)ov.scrollTop=sc;}
let CUR=null, FICHA_ORIGEM=null, FICHA_FECHANDO=false, FICHA_RESTAURAR=false;
function _visivelFicha(id){const el=document.getElementById(id);return !!(el&&el.offsetParent!==null);}
function _guardaOrigemFicha(){
  if(FICHA_ORIGEM)return;
  FICHA_ORIGEM={
    tela: _visivelFicha('mtwrap')?'meutime':(_visivelFicha('homewrap')?((window.RouteState&&window.RouteState.panel())||'inicio'):'ranking'),
    y: window.scrollY||window.pageYOffset||0
  };
}
function _registraRetornoAoElenco(){
  /* `card`, `funcao` e `modo` pertencem exclusivamente à rota da Ficha.
     Ao voltar ao Elenco eles não podem sobreviver e reabrir o detalhe no F5. */
  try{
    const u=new URL(location.href);
    ['card','funcao','modo'].forEach(p=>u.searchParams.delete(p));
    const st=(history.state&&!(history.state.ficha||history.state.paginaCard))?history.state:{};
    history.replaceState(st,'',u.pathname+u.search+u.hash);
  }catch(e){}
  try{ sessionStorage.setItem('t6-rota-atual','elenco'); }catch(e){}
  try{ if(typeof window.t6RegistraRota==='function') window.t6RegistraRota('meutime'); }catch(e){}
}
function _restauraOrigemFicha(){
  const origem=FICHA_ORIGEM; FICHA_ORIGEM=null;
  if(!origem)return;
  if(origem.tela==='meutime'){
    try{homeToggle(0);if(!_visivelFicha('mtwrap'))mtToggle();}catch(e){}
    _registraRetornoAoElenco();
  }else if(origem.tela==='ranking'){
    try{if(_visivelFicha('mtwrap'))mtToggle();homeToggle(0);}catch(e){}
  }else if(typeof window.t6Painel==='function'){
    try{window.t6Painel(origem.tela);}catch(e){}
  }else{
    try{homeToggle(1);if(window.boxModo)boxModo(origem.tela==='boxant'?1:0);}catch(e){}
  }
  requestAnimationFrame(()=>{
    window.scrollTo(0,origem.y);
    /* O retorno da Ficha não passa por mtToggle quando o Elenco já estava
       visível sob o detalhe. Recalcula só a geometria depois de ele voltar
       ao layout, sem segundo render, save ou temporizador. */
    if(origem.tela==='meutime' && typeof window.elRecalculaGeometriaAoVoltarFicha==='function'){
      window.elRecalculaGeometriaAoVoltarFicha();
    }
  });
}
function _fechaFichaUI(){
  const ov=document.getElementById('ov');if(ov)ov.style.display='none';
  const vb=document.getElementById('voltar');if(vb)vb.style.display='none';
  document.body.classList.remove('naficha');
  if(SNAP){_desfaz();}
  else if(CUR){const c=_card(CUR);if(c&&c.cmode){c.cmode=0;recalcCard(c);traducaoViva();render();}}
 CUR=null;
}
/* Portas de lifecycle: expõem somente operações de UI/origem já existentes.
   O FichaController decide a transição; este bloco não desenha a Ficha. */
window.FichaLifecyclePorts=Object.freeze({
 captureOrigin:_guardaOrigemFicha,
 closeUI:_fechaFichaUI,
 restoreOrigin:_restauraOrigemFicha,
 clearOrigin:function(){FICHA_ORIGEM=null;},
 origin:function(){return FICHA_ORIGEM?{tela:FICHA_ORIGEM.tela,y:FICHA_ORIGEM.y}:null;},
 isOpen:function(){const ov=document.getElementById('ov');return !!(ov&&ov.style.display!=='none');}
});
window.addEventListener('keydown',e=>{
  if(e.key==='Escape'){const ov=document.getElementById('ov');
   if(ov&&ov.style.display!=='none') fechar();}
});
function fechar(restaurar=true){
 const temHistorico=!!(history.state&&history.state.ficha);
 _fechaFichaUI();
 if(temHistorico){FICHA_FECHANDO=true;FICHA_RESTAURAR=!!restaurar;try{history.back();}catch(e){FICHA_FECHANDO=false;if(restaurar)_restauraOrigemFicha();}}
 else if(restaurar)_restauraOrigemFicha();else FICHA_ORIGEM=null;
}
function abrir(key){
 _guardaOrigemFicha();
 document.body.classList.add('naficha');
 CUR=key;
 const vb=document.getElementById('voltar'); if(vb) vb.style.display='block';
 if(!(history.state&&history.state.ficha)) history.pushState({ficha:1},'');
 const [id,tipo]=key.split('|');const c=D.find(x=>x.id===id&&x.tipo===tipo);if(!c)return;
 if(c._notaMot===undefined&&c.id!=='MOLDE')c._notaMot=nota(c);
 const t=W.reduce((a,b)=>a+b,0)||1,ref=notaMed(tipo),m=MED[tipo];
 const CL={12:['Indispensável','#e0533d'],7:['Desejável','#f0a531'],6:['Desejável','#f0a531'],3:['Útil','#22c58b'],1:['Acessório','#4f8cff'],0:['—','#3a4350']};
 const GRP=[['ATAQUE',[0,1,2,3,4,5,6,7,8,9]],['ATLETISMO',[10,11,12,13,14,15,16]],['DEFESA',[17,18,19,20]],['GOLEIRO',[21,22,23,24,25]]];
 const ST=(c.base?_startDe(c):null);
 const rowHtml=r=>{const p=r[1],cl=CL[p]||CL[0];
  const jogo=r[3];
  const gb=ST?Math.round((jogo-(ST[r[0]]||0))*10)/10:0;
  if(!MODO_ADM){
   if(ET){const e=ET[r[0]],d=(a,b)=>b>a?`<span class=up>${b}</span>`:`<span class=mini>${b}</span>`;
    return `<div class="at atgu5"><span>${ATTRS[r[0]]}</span><span class=mini>${e[0]}</span>${d(e[0],e[1])}${d(e[1],e[2])}${d(e[2],e[3])}<b>${jogo}</b></div>`;}
   const bs=ST?(ST[r[0]]||0):jogo;
   return `<div class="at atgu"><span>${ATTRS[r[0]]}</span><span class=mini>${bs}</span><b style="color:${jogo>bs?'#22c58b':'inherit'}">${jogo}</b></div>`;}
  if(ET){const e=ET[r[0]],dd=(a,b)=>b>a?`<span class=up>${b}</span>`:`<span class=mini>${b}</span>`;
  return `<div class="at atgc"><span class="${p===0?'w0':''}" style="${p>=6?'font-weight:700':''}">${ATTRS[r[0]]}</span><span><span style="font-size:10px;padding:1px 6px;border-radius:4px;background:${cl[1]}22;color:${cl[1]};border:1px solid ${cl[1]}55">${cl[0]}</span></span><span class=mini>${e[0]}</span>${dd(e[0],e[1])}${dd(e[1],e[2])}${dd(e[2],e[3])}<b>${e[3]}</b>${dd(e[3],(ETN?ETN[r[0]]:e[3]))}${dd((ETN?ETN[r[0]]:e[3]),e[4])}<b>${jogo}</b><span class=mini>${r[2]}</span><span class="${p?(r[4]>=0?'up':'dn'):'mini'}">${r[4]>=0?'+':''}${r[4]}</span><b style="color:${p?(ptsAttr(r)>=0?'#22c58b':'#e0533d'):'#5d6673'}">${p?(ptsAttr(r)>=0?'+':'')+ptsAttr(r).toFixed(1):'0.0'}</b></div>`;}
  return `<div class="at atg"><span class="${p===0?'w0':''}" style="${p>=6?'font-weight:700':''}">${ATTRS[r[0]]}</span><span><span style="font-size:10px;padding:1px 6px;border-radius:4px;background:${cl[1]}22;color:${cl[1]};border:1px solid ${cl[1]}55">${cl[0]}</span></span><span class=mini>${r[2]}</span><b>${jogo}${gb>0?`<sup style="color:#22c58b;font-size:9px;font-weight:700">+${gb}</sup>`:''}</b><span class="${p?(r[4]>=0?'up':'dn'):'mini'}">${r[4]>=0?'+':''}${r[4]}</span><b style="color:${p?(ptsAttr(r)>=0?'#22c58b':'#e0533d'):'#5d6673'}">${p?(ptsAttr(r)>=0?'+':'')+ptsAttr(r).toFixed(1):'0.0'}</b></div>`;};
 const ET=c.base?etapas(c,_lvlDe(c)):null;
 const ETN=c.base?_e4nat(c,_lvlDe(c)):null;
 const AH=MODO_ADM?(ET?'<div class="athead atgc"><span>Atributo</span><span>Classe</span><span>Base</span><span>+barras</span><span>+\u00edmpeto</span><span>+t\u00e9cnico</span><span>Na tela</span><span>+hab. nativas</span><span>+hab. adicionadas</span><span>Total</span><span>Alvo</span><span>vs alvo</span><span>Pontos</span></div>':'<div class=athead><span>Atributo</span><span>Classe</span><span>Alvo</span><span>No jogo</span><span>vs alvo</span><span>Pontos</span></div>')
  :(ET?'<div class="athead athequ5"><span>Atributo</span><span>base</span><span>barras</span><span>ímpeto</span><span>técnico</span><span>no jogo</span></div>'
     :'<div class="athead athequ"><span>Atributo</span><span>Base</span><span>Otimizado</span></div>');
 const secao=f=>GRP.map(([g,idxs])=>{const rows=c.arows.filter(r=>idxs.includes(r[0])&&f(r));
  return rows.length?`<div class=grptt>${g}</div>`+rows.map(rowHtml).join(''):'';}).join('');
 const nz0=c.arows.filter(r=>!r[1]).length;
 const at=MODO_ADM
  ?AH+secao(r=>r[1]>0)+(nz0?`<details class=zr><summary>+ ${nz0} atributos indiferentes nesta função</summary>${AH+secao(r=>!r[1])}</details>`:'')
  :AH+secao(r=>true);
 const FH=MODO_ADM?'<div class=fzh><span>Medida</span><span>Direção</span><span>Nota da medida</span><span>No card</span><span>Pontos</span></div>'
  :'<div class="fzh fzhu"><span>Medida</span><span>No card</span></div>';
 const fz=MODO_ADM?(FH+c.frows.slice().sort((a,b)=>(a[6]||0)-(b[6]||0)).map(r=>`<div class=fzr><span>${r[0]} <span class=mini>p${r[1]}</span></span><span class=mini>${!r[5]?'—':(r[5]>0?'maior melhor':'menor melhor')}</span><span class=mini><b style="color:${r[4]>0?'#22c58b':(r[4]<0?'#e0533d':'inherit')}">${r[4]>0?'+':''}${r[4]}</b></span><b>${r[3]}</b><span class=mini>${r[2]}</span><b style="color:${(r[6]||0)>=0?'#22c58b':'#e0533d'}">${(r[6]||0)>=0?'+':''}${(r[6]||0).toFixed(2)}</b></div>`).join('')+`<div class=fzr style="border-top:2px solid #2b3543;margin-top:5px;padding-top:7px;border-bottom:none"><span style="font-weight:800">TOTAL</span><span class=mini>soma ${(c.b4r||0).toFixed(0)}</span><span class=mini>peso ${c.frows.reduce((a,r)=>a+r[1],0)}</span><span class=mini>bônus ${((c._fb!==undefined?c._fb:0)>=0?"+":"")+(c._fb!==undefined?c._fb:0).toFixed(2)}</span><b style="font-size:15px;color:${c.b4>=0?'#22c58b':'#e0533d'}">${c.b4>=0?'+':''}${c.b4.toFixed(0)}%</b></div>`)
 :(FH+c.frows.slice().map(r=>`<div class="fzr fzru"><span>${r[0].replace(/ p\d+$/,'')}</span><b>${r[3]}</b></div>`).join(''));
 const bar=(c.sisBar||[]).map(b=>`${b[0]} <b>+${b[1]}</b>`).join(' · ');
  const notaPublicada=(c.__cn&&typeof c.pontuacao_final==='number'&&isFinite(c.pontuacao_final))?c.pontuacao_final:nota(c);
  const pctPublicado=(c.__cn&&typeof c.percentual_topo==='number'&&isFinite(c.percentual_topo))?c.percentual_topo:0;
  document.getElementById('box').innerHTML=`
 <span class=close onclick="fechar()">×</span>
 <div class=fhd>
  <div class=fhdcol><div class=fhdnome><div style="font-size:21px;font-weight:800">${c.nome}</div></div><img class=fhdimg src="${_fotoCN(c)}" onerror="this.style.display='none'">
 <div class="mini fhdnat"><span class=pslb>POSIÇÃO NATIVA</span><div class=fhdsig>${(typeof SIGJ!=='undefined'&&SIGJ[npFixo(c)])||npFixo(c)||'—'}</div><div class=fhdpos>${(POSN[npFixo(c)]||npFixo(c)||'—')}</div>${c.dt?`<div class=fhddt>${c.dt.split('-').reverse().join('/')}</div>`:''}</div>
 <div class=mini>${c.ovr?`<div class=fhdovr>Base Konami: <b>${c.ovr}</b></div><div class=fhdovr>Máximo Konami: <b>${(c.maxOvr||c.sisOvr||0)}</b></div>`:'card de referência — os valores SÃO os alvos do tipo'}${c.temMax?'':(c.capdesc?' <b style=color:#f0a531>(progressão ainda não publicada pelo efHub — MÁX desconhecido, a pontuação sai só com o que já é certo)</b>':' <b style=color:#f0a531>(card sem progressão — MÁX = base)</b>')}</div>
  </div><div class=fhdmeio><div class=fhdestbox>${(c.modelo||c.tipo||'')}${estiloAtiva(c)?'':'<div class=fhdbasico title="o estilo de jogo dele não liga nesta posição">BÁSICO — este estilo não liga nesta posição</div>'}</div><div class=fhdbts><div class=fhdbtstt>FUNÇÕES QUE ELE PODE EXERCER EM CAMPO<span>clique para ver o build</span></div>${cbFuncoes(c)}</div></div><div class=fhdcampo>${cbCampo(c)}</div><div class=fhdnota><span class=fhdn style="color:${cor(notaPublicada,ref)}">${_nd(notaPublicada)}</span><span class=fhdl>pontuação final publicada</span><span class=fhdtopo><b style="color:${pctPublicado>=99.5?'#22c58b':(pctPublicado>=90?'#c98a1f':'inherit')}">${pctPublicado.toFixed(2)}% top</b></span>${(function(){if(c._notaMot===undefined)return '';const na=nota(c);const p=na>0?(c._notaMot-na)/na*100:0;return '<span class=fhdmel>pode melhorar <b>'+(p>0.05?'+'+p.toFixed(1):'0')+'%</b></span>';})()}</div></div>
 <div class=duo>

</div>
 <div class=grid2>
  <div class=sec style=margin:0><h3 class=h3big>Atributos</h3>${painelBuild(c)}${at}<div class="at admonly" style="border-top:2px solid #2b3543;margin-top:6px;padding-top:7px;border-bottom:none"><span style="font-weight:800">TOTAL</span><span><b style="font-size:15px;color:${c.b1>=0?'#22c58b':'#e0533d'}">${c.b1>=0?'+':''}${c.b1.toFixed(1)} pts</b></span></div></div>
  <div>
   <div class=sec><h3>${MODO_ADM?'Físico':'Físico'}</h3><div class=corpotop><span>${c.h}cm</span><span>${c.w}kg</span><span>${c.age||'—'} anos</span><span>lesão ${c.inj||'—'}</span></div><div class=corpopr><span>pé <b>${c.foot||'—'}</b></span>${prPar(c)?`<span>pé ruim <b>${PR_ROT_F[prPar(c)[0]]}</b></span><span>precisão <b>${PR_ROT_Q[prPar(c)[1]]}</b></span><span>bônus <b style=color:#4f8cff>+${prBonus(c).toFixed(2)}</b></span>`:'<span>pé ruim sem dado</span>'}</div>${fz}</div>
   <div class="sec secdup"><h3>${MODO_ADM?'Habilidades':'Habilidades'}</h3>
     <div class=mini>${c.id==="MOLDE"?'as 15 mais aferidas na comunidade (teto comum da função)':'nativas'}</div><div class=chips>${c.fab.map(s=>{const f=(FILA[c.tipo]||[]).find(x=>x[0]===s);return `<span class="chip ok">${s}${(c.id==="MOLDE"&&f)?` <b style="opacity:.75">${f[1]}%</b>`:''}</span>`;}).join('')}${(c.raras||[]).map(s=>`<span class="chip rr">${s}</span>`).join('')||(c.fab.length?'':'<span class=mini>—</span>')}</div>
     <div class=mini style="margin-top:7px">habilidades adicionais sugeridas</div>${c.naFila?'<div class=avisobox style="margin:4px 0 6px"><b>Na fila do motor.</b> Carta nova: a comunidade ainda não montou builds dela, então o pool de adicionáveis não existe. Ela entra na próxima rodada do motor, junto com as outras. Até lá a nota está <b>subestimada</b>.</div>':''}<div class=chips>${(c.adds||[]).map(s=>`<span class="chip" style="border-color:#f0a531;color:#f0a531">${s}</span>`).join('')||(c.orc>0?'<span class=mini>pool de habilidades adicionáveis ainda não coletado neste card</span>':'<span class=mini>card sem progressão — não adiciona habilidade</span>')}</div><div class="mini admonly" style="margin-top:7px">de fora — dá pra selecionar e a pontuação NÃO muda</div><div class="chips admonly">${(c.NEU||[]).map(s=>`<span class="chip" style="border-color:#5d6673;color:#8d97a3">${s}</span>`).join()||'<span class=mini>nenhuma troca neutra</span>'}</div><details class=admonly style="margin-top:6px"><summary class=mini>o pool inteiro que o motor pode escolher (${(c.falta||[]).length})</summary><div class=chips>${(c.falta||[]).map(s=>`<span class="chip no">${s}</span>`).join('')}</div></details></div>
   <div class="sec secdup"><h3>${MODO_ADM?'Habilidades especiais':'Habilidades especiais'}</h3><div class=chips>${c.raras.map(s=>`<span class="chip rr">${s}${(B5V[c.tipo]||{})[s]!==undefined?` <b>${(B5V[c.tipo]||{})[s]}</b>`:''}</span>`).join('')||'<span class=mini>nenhuma</span>'}</div><div class="mini admonly" style="margin-top:6px">as mais valiosas nesta função</div><div class="chips admonly">${Object.entries(B5V[c.tipo]||{}).sort((a,b)=>b[1]-a[1]).slice(0,5).map(([n,v])=>`<span class="chip" style="border-color:#e0533d55;color:#c98">${n} <b>${v}</b></span>`).join('')||'<span class=mini>—</span>'}</div>${c.raras.length&&MODO_ADM?`<div class=mini style=margin-top:5px>ocupam ${c.raras.length} dos 15 slots do card — o teto do o quadro de habilidades NÃO é reescalado por isso (é sempre as 15 maiores da função)</div>`:''}</div>
   <div class=sec style=margin-bottom:0><h3>${MODO_ADM?'Estilo de jogo da IA':'Estilo de jogo da IA'}</h3><div class=chips>${(c.com||[]).map(s=>`<span class=chip style="border-color:#4f8cff55;color:#8fb8ff">${s}</span>`).join('')||'<span class=mini>nenhum</span>'}</div><div class=mini style="margin-top:6px">${(c.com||[]).length?`${(c.com||[]).length} de 5 · bônus <b style=color:#4f8cff>+${iaBonus(c).toFixed(1)}</b> na nota`:'este card não tem estilo de jogo da IA'}</div></div><div class="sec secoff" style=margin-bottom:0><h3>Pé ruim</h3><div class=mini>${prPar(c)?`frequência <b style=color:#8fb8ff>${PR_ROT_F[prPar(c)[0]]}</b> · precisão <b style=color:#8fb8ff>${PR_ROT_Q[prPar(c)[1]]}</b> · bônus <b style=color:#4f8cff>+${prBonus(c).toFixed(2)}</b> na nota`:'sem dado de pé ruim'}</div></div></div>
  </div>
 </div>`;
 document.getElementById('ov').style.display='block';document.getElementById('ov').scrollTop=0;
}
document.getElementById('ov').onclick=e=>{if(e.target.id==='ov')fechar();};
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&document.getElementById('ov').style.display==='block')fechar();});
['q','vm','mk','uniq','tier','mx','ps','mdl','hnat','hsp','hs'].forEach(id=>{const e=document.getElementById(id);e.oninput=render;e.onchange=render;});
/* ===== v140 · FILA DA PRÓXIMA RODADA DO MOTOR =====
   Decisao do Luis (03/08): carta nova NAO recebe habilidade provisoria.
   "Deixa eles aí pra rodada de motor. A gente junta com os outros que tem que rodar."
   Aqui a gente so CLASSIFICA e MARCA. Nao escolhe habilidade, nao mexe em nota.

   O que ainda e feito, porque e correcao de dado e nao invencao:
   - separar as RARAS que a coleta jogou dentro do fab (comum COMPETE, rara SOMA:
     classificar errado muda a conta) */
(function(){
 const RARAS=new Set(); D.forEach(c=>(c.raras||[]).forEach(h=>RARAS.add(h)));
 let sep=0, fila=0;
 for(const c of D){
  if(c.id==='MOLDE'||!c.pacote) continue;
  const r=(c.fab||[]).filter(h=>RARAS.has(h));
  if(r.length){ c.raras=[...new Set([...(c.raras||[]),...r])];
   c.fab=(c.fab||[]).filter(h=>!RARAS.has(h)); sep++; }
  /* sem pool de adicionaveis (a comunidade ainda nao montou build dela) e com
     orcamento pra gastar => esta esperando a proxima rodada do motor */
  if(c.orc>0 && !(c.HAB||[]).length){ c.naFila=1; fila++; }
 }
 if(sep)console.log('%craras separadas do fab em '+sep+' linhas','color:#f0a531');
 if(fila)console.log('%c'+fila+' linhas na fila da proxima rodada do motor','color:#4f8cff');
})();

/* A rota atual decide qual tela desenhar. Não renderizar o Ranking legado na
   inicialização: ele aparecia por instantes e era substituído depois pela tela atual. */
traducaoViva();pesosUI();MOTOR_UI();

/* ===================== MÓDULO MEU TIME ===================== */
const MT_FUNCS={
 GK:["Goleiro defensivo","Goleiro ofensivo"],
 ZC:["Zagueiro de combate","Zagueiro de saída"],
 LE:["Lateral defensivo","Lateral ofensivo"],
 LD:["Lateral defensivo","Lateral ofensivo"],
 VOL:["Volante de contenção","Volante de construção"],
 MC:["Meia armador","Meia de arranque"],
 MLE:["Ala finalizador","Ala cruzador"],
 MLD:["Ala finalizador","Ala cruzador"],
 MO:["Meia ofensivo","Atacante infiltrador"],
 PE:["Atacante criador","Atacante finalizador"],
 PD:["Atacante criador","Atacante finalizador"],
 SA:["Atacante infiltrador","Falso nove"],
 CA:["Falso nove","Centroavante fixo","Centroavante móvel"]};
const MT_FORM={
 "4-3-3":[["GK",50,94],["LE",12,76],["ZC",36,80],["ZC",64,80],["LD",88,76],["VOL",50,58],["MC",26,50],["MC",74,50],["PE",14,22],["CA",50,14],["PD",86,22]],
 "4-2-3-1":[["GK",50,94],["LE",12,76],["ZC",36,80],["ZC",64,80],["LD",88,76],["VOL",36,60],["VOL",64,60],["MLE",14,38],["MO",50,36],["MLD",86,38],["CA",50,12]],
 "4-4-2":[["GK",50,94],["LE",12,76],["ZC",36,80],["ZC",64,80],["LD",88,76],["MLE",14,52],["MC",36,54],["MC",64,54],["MLD",86,52],["SA",38,18],["CA",62,16]],
 "4-3-2-1":[["GK",50,94],["LE",12,76],["ZC",36,80],["ZC",64,80],["LD",88,76],["VOL",50,60],["MC",26,52],["MC",74,52],["MO",32,30],["MO",68,30],["CA",50,12]],
 "4-3-1-2":[["GK",50,94],["LE",12,76],["ZC",36,80],["ZC",64,80],["LD",88,76],["VOL",50,60],["MC",26,52],["MC",74,52],["MO",50,34],["SA",38,18],["CA",62,16]],
 "3-4-3":[["GK",50,94],["ZC",26,80],["ZC",50,84],["ZC",74,80],["MLE",14,54],["MC",38,54],["MC",62,54],["MLD",86,54],["PE",16,20],["CA",50,14],["PD",84,20]],
 "3-2-3-2":[["GK",50,94],["ZC",26,80],["ZC",50,84],["ZC",74,80],["VOL",36,62],["VOL",64,62],["MLE",20,42],["MC",50,42],["MLD",80,42],["SA",38,18],["CA",62,16]],
 "3-2-4-1":[["GK",50,94],["ZC",26,80],["ZC",50,84],["ZC",74,80],["VOL",36,62],["VOL",64,62],["MLE",14,42],["MC",38,42],["MC",62,42],["MLD",86,42],["CA",50,14]],
 "3-1-4-2":[["GK",50,94],["ZC",26,80],["ZC",50,84],["ZC",74,80],["VOL",50,62],["MLE",14,42],["MC",38,42],["MC",62,42],["MLD",86,42],["SA",38,18],["CA",62,16]],
 "4-1-2-3":[["GK",50,94],["LE",12,76],["ZC",36,80],["ZC",64,80],["LD",88,76],["VOL",50,64],["MC",30,46],["MC",70,46],["PE",14,20],["CA",50,12],["PD",86,20]],
 "4-1-4-1":[["GK",50,94],["LE",12,76],["ZC",36,80],["ZC",64,80],["LD",88,76],["VOL",50,62],["MLE",14,42],["MC",38,42],["MC",62,42],["MLD",86,42],["CA",50,14]],
 "4-2-1-3":[["GK",50,94],["LE",12,76],["ZC",36,80],["ZC",64,80],["LD",88,76],["VOL",36,62],["VOL",64,62],["MO",50,42],["PE",14,18],["CA",50,14],["PD",86,18]],
 "4-2-4":[["GK",50,94],["LE",12,76],["ZC",36,80],["ZC",64,80],["LD",88,76],["VOL",36,58],["VOL",64,58],["PE",12,18],["SA",38,16],["CA",62,16],["PD",88,18]],
 "3-3-4":[["GK",50,94],["ZC",26,80],["ZC",50,84],["ZC",74,80],["MLE",14,54],["MC",50,54],["MLD",86,54],["PE",12,18],["SA",38,16],["CA",62,16],["PD",88,18]],
 "5-3-2":[["GK",50,94],["LE",10,82],["ZC",30,82],["ZC",50,86],["ZC",70,82],["LD",90,82],["VOL",50,58],["MC",28,46],["MC",72,46],["SA",38,18],["CA",62,16]],
 "5-2-2-1":[["GK",50,94],["LE",10,80],["ZC",30,80],["ZC",50,84],["ZC",70,80],["LD",90,80],["VOL",36,60],["VOL",64,60],["MO",32,38],["MO",68,38],["CA",50,14]],
 "5-2-1-2":[["GK",50,94],["LE",10,80],["ZC",30,80],["ZC",50,84],["ZC",70,80],["LD",90,80],["VOL",36,60],["VOL",64,60],["MO",50,38],["SA",38,18],["CA",62,16]],
};

let MT={form:"4-3-3",slots:[],banco:[],elenco:[],nome:"Meu time"};
let MT_ON=false, MT_SEL=null, PRO=false;

/* persistência do usuário — único acesso pelo repositório/adaptador */
function userStateRepository(){
 if(!window.UserStateRepository) throw new Error("UserStateRepository não carregado");
 return window.UserStateRepository;
}
function userStateSave(){
 return userStateRepository().saveLegacy(MT);
}
function userStateLoad(){
 var carregado=userStateRepository().loadLegacy(MT);
 MT=Object.assign({form:"4-3-3",slots:[],banco:[],elenco:[],nome:"Meu time"},carregado||{});
 return MT;
}
window.UserStateRuntime=Object.freeze({save:userStateSave,load:userStateLoad});

function mtSlots(){const f=MT_FORM[MT.form]||MT_FORM["4-3-3"];
 var mudou=!!window._MT_FORM_ATUAL&&window._MT_FORM_ATUAL!==MT.form;
 if(!MT.slots||MT.slots.length!==f.length)MT.slots=f.map(x=>({pos:x[0],func:MT_FUNCS[x[0]][0],key:null}));
 f.forEach((x,i)=>{
  /* Uma troca de formação restaura as vagas-base. No render normal, mantém
     a posição escolhida pelo usuário nos botões do cabeçalho. */
  if(mudou||!MT.slots[i].pos)MT.slots[i].pos=x[0];
  if(!MT.slots[i].mv){MT.slots[i].x=x[1];MT.slots[i].y=x[2];}
  if(!(MT_FUNCS[MT.slots[i].pos]||[]).includes(MT.slots[i].func))MT.slots[i].func=(MT_FUNCS[MT.slots[i].pos]||[])[0]||MT.slots[i].func;
 });
 window._MT_FORM_ATUAL=MT.form;
 return MT.slots;}
function mtCard(k){return k?_card(k):null;}
function mtNota(k){return mtNotaReal(k);}
function mtN(c,k){return k?mtNotaReal(k):(c?notaComTec(c,mtTecBs()):0);}
function mtTopo(func,n){return D.filter(c=>c.id!=="MOLDE"&&c.tipo===func).map(c=>({c,n:nota(c)})).sort((a,b)=>b.n-a.n).slice(0,n*4);}
function _bid(k){return String(String(k).split("|")[0]).split("@")[0];}
function _jog(k){const c=_card(k);return c?nz(c.nome):_bid(k);}
function _b(k){return _jog(k);}
function mtUsados(){const s=new Set();MT.slots.forEach(x=>{if(x.key)s.add(_jog(x.key))});(MT.banco||[]).forEach(k=>s.add(_jog(k)));(MT.elenco||[]).forEach(k=>s.add(_jog(k)));return s;}
function mtPool(){const m=new Map();
 MT.slots.forEach(x=>{if(x.key&&!m.has(_jog(x.key)))m.set(_jog(x.key),x.key)});
 (MT.banco||[]).forEach(k=>{if(!m.has(_jog(k)))m.set(_jog(k),k)});
 (MT.elenco||[]).forEach(k=>{if(!m.has(_jog(k)))m.set(_jog(k),k)});
 return [...m.values()];}

/* ===== v142 · MEU TIME — resumo por setor e sugestão por vaga ===== */
const MT_SETOR={GK:'DEFESA',ZC:'DEFESA',LE:'DEFESA',LD:'DEFESA',
 VOL:'MEIO',MC:'MEIO',MLE:'MEIO',MLD:'MEIO',MO:'MEIO',
 SA:'ATAQUE',PE:'ATAQUE',PD:'ATAQUE',CA:'ATAQUE'};
/* forca de um slot = nota do card / nota do melhor do banco naquela funcao */
/* v152 · a forca do setor virou "quanto voce ja tirou das SUAS cartas".
   Comparar a build crua do usuario com o TETO do melhor card da funcao dava
   0% em todo mundo e nao dizia nada acionavel. */
function mtForca(sl){
 const c=mtCard(sl.key); if(!c)return null;
 return mtPct(sl.key);
}
function mtTetoDaFuncao(sl){
 const c=mtCard(sl.key); if(!c)return null;
 const ref=mtTopo(sl.func,1)[0];
 return ref? Math.max(0,Math.min(100,100*mtRef(sl.key).ideal/ref.n)) : null;
}
function mtResumo(S1){
 const st={DEFESA:[],MEIO:[],ATAQUE:[]};
 S1.forEach(sl=>{const f=mtForca(sl); const s=MT_SETOR[sl.pos]||'MEIO';
  st[s].push({sl,f,c:mtCard(sl.key)});});
 const out={};
 for(const k in st){const v=st[k], ok=v.filter(x=>x.f!==null);
  out[k]={total:v.length, escalados:ok.length,
   media: ok.length? ok.reduce((a,x)=>a+x.f,0)/ok.length : 0,
   nota: ok.length? ok.reduce((a,x)=>a+mtNotaReal(x.sl.key),0)/ok.length : 0,
   pior: ok.length? ok.slice().sort((a,b)=>a.f-b.f)[0] : null,
   vazios: v.filter(x=>x.f===null).length};}
 return out;
}
/* os 3 melhores DO ELENCO para uma vaga; se o elenco nao cobre, os 3 do banco inteiro */
function mtSugestao(sl){
 const usados=mtUsados();
 const meus=(MT.elenco||[]).concat(MT.banco||[])
   .map(k=>_card(k)).filter(Boolean)
   .map(c=>D.find(x=>String(x.id)===String(c.id)&&x.tipo===sl.func))
   .filter(Boolean).map(c=>({c,n:nota(c),meu:1}))
   .sort((a,b)=>b.n-a.n).slice(0,3);
 if(meus.length>=3) return {lista:meus, doElenco:true};
 const fora=D.filter(c=>c.id!=='MOLDE'&&c.tipo===sl.func&&!usados.has(_jog(c.id+'|'+c.tipo)))
   .map(c=>({c,n:nota(c),meu:0})).sort((a,b)=>b.n-a.n).slice(0,3-meus.length);
 return {lista:meus.concat(fora), doElenco:meus.length>0};
}

let MT_ED=0;
function mtEdit(){MT_ED=MT_ED?0:1;mtRender();}
function mtResetPos(){const f=MT_FORM[MT.form]||MT_FORM["4-3-3"];
 MT.slots=(MT.slots||[]).map((s,i)=>f[i]?Object.assign({},s,{x:f[i][1],y:f[i][2],mv:0}):s);
 userStateSave();mtRender();}

/* ===== v151 · CAMPO INTERATIVO =====
   Dois arrastos diferentes, de proposito:
   - normal: arrasta o JOGADOR. Vaga->vaga troca os dois. Banco->vaga entra e
     o que sai vai pro banco. Vaga->banco tira de campo.
   - "mover posicoes" ligado: arrasta a VAGA pelo campo (o marcador). */
let MT_DRAG=null;
function mtTiraDaLista(k){
 MT.banco=(MT.banco||[]).filter(x=>x!==k);
 MT.elenco=(MT.elenco||[]).filter(x=>x!==k);
}
function mtSolta(destTipo,destI){
 const d=MT_DRAG; MT_DRAG=null;
 if(!d)return;
 if(destTipo==='slot'){
  const alvo=MT.slots[destI]; if(!alvo)return;
  const saiu=alvo.key;
  if(d.de==='slot'){
   if(d.i===destI)return;
   MT.slots[d.i].key=saiu; alvo.key=d.k;
  }else{
   mtTiraDaLista(d.k);
   alvo.key=d.k;
   if(saiu){ if(d.de==='banco'){MT.banco.push(saiu);} else {MT.elenco=MT.elenco||[];MT.elenco.push(saiu);} }
  }
 }else if(destTipo==='banco'){
  if(d.de==='slot'){MT.slots[d.i].key=null;}
  mtTiraDaLista(d.k); MT.banco=MT.banco||[]; MT.banco.push(d.k);
 }else if(destTipo==='elenco'){
  if(d.de==='slot'){MT.slots[d.i].key=null;}
  mtTiraDaLista(d.k); MT.elenco=MT.elenco||[]; MT.elenco.push(d.k);
 }
 userStateSave(); mtRender();
}
function mtDndInit(){
 const w=document.getElementById('mtwrap'); if(!w)return;
 w.querySelectorAll('.mtsl[draggable=true]').forEach(el=>{
  el.addEventListener('dragstart',e=>{ if(MT_ED){e.preventDefault();return;}
   MT_DRAG={de:'slot',i:+el.dataset.i,k:el.dataset.key};
   e.dataTransfer.effectAllowed='move'; try{e.dataTransfer.setData('text/plain',el.dataset.key);}catch(x){}
   el.classList.add('arrastando'); });
  el.addEventListener('dragend',()=>{el.classList.remove('arrastando');document.querySelectorAll('.pousa').forEach(x=>x.classList.remove('pousa'));});
 });
 w.querySelectorAll('.mtbc[draggable=true]').forEach(el=>{
  el.addEventListener('dragstart',e=>{
   MT_DRAG={de:el.dataset.de,i:+el.dataset.i,k:el.dataset.key};
   e.dataTransfer.effectAllowed='move'; try{e.dataTransfer.setData('text/plain',el.dataset.key);}catch(x){}
   el.classList.add('arrastando'); });
  el.addEventListener('dragend',()=>{el.classList.remove('arrastando');document.querySelectorAll('.pousa').forEach(x=>x.classList.remove('pousa'));});
 });
 w.querySelectorAll('.mtsl').forEach(el=>{
  el.addEventListener('dragover',e=>{if(!MT_DRAG||MT_ED)return;e.preventDefault();e.dataTransfer.dropEffect='move';el.classList.add('pousa');});
  el.addEventListener('dragleave',()=>el.classList.remove('pousa'));
  el.addEventListener('drop',e=>{e.preventDefault();e.stopPropagation();el.classList.remove('pousa');mtSolta('slot',+el.dataset.i);});
 });
 const cx=(sel,tipo)=>{const box=w.querySelector(sel); if(!box)return;
  box.addEventListener('dragover',e=>{if(!MT_DRAG)return;e.preventDefault();e.dataTransfer.dropEffect='move';box.classList.add('pousa');});
  box.addEventListener('dragleave',()=>box.classList.remove('pousa'));
  box.addEventListener('drop',e=>{e.preventDefault();box.classList.remove('pousa');mtSolta(tipo,null);});};
 cx('.alvobanco','banco'); cx('.alvoelenco','elenco');
}
function mtDragInit(){
 const camp=document.querySelector('.mtcampo'); if(!camp)return;
 camp.querySelectorAll('.mtsl').forEach(el=>{
  el.addEventListener('pointerdown',ev=>{
   if(!MT_ED)return; ev.preventDefault();
   const i=+el.dataset.i, r=camp.getBoundingClientRect();
   let moveu=0; el.classList.add('arr'); el.setPointerCapture(ev.pointerId);
   const mv=e=>{moveu=1;
    let x=(e.clientX-r.left)/r.width*100, y=(e.clientY-r.top)/r.height*100;
    x=Math.max(3,Math.min(97,x)); y=Math.max(3,Math.min(97,y));
    el.style.left=x+'%'; el.style.top=y+'%';
    const S=mtSlots(); if(S[i]){S[i].x=Math.round(x*10)/10;S[i].y=Math.round(y*10)/10;S[i].mv=1;}};
   const up=e=>{el.classList.remove('arr');
    el.removeEventListener('pointermove',mv); el.removeEventListener('pointerup',up);
    if(moveu){userStateSave();}};
   el.addEventListener('pointermove',mv); el.addEventListener('pointerup',up);
  });
 });
}
function mtRender(){ _MTMAX=null;
 var bloqueioBuilds=_t6BloqueioBuildsElenco();
 if(bloqueioBuilds)return _t6RenderEstadoBloqueadoElenco(bloqueioBuilds);
 _t6LimpaEstadoBloqueadoElenco(document.getElementById('mtwrap'));
 const S1=mtSlots();
 /* Render e restauracao nunca saneiam ocorrencias. A porta canônica do
    Elenco bloqueia novas duplicatas por card_id; legado e apenas auditado. */
 const tit=S1.filter(x=>x.key),med=tit.length?tit.reduce((a,x)=>{const cc=mtCard(x.key);return a+(cc?mtMaiorNota(cc):0);},0)/tit.length:0;
 const campo=S1.map((sl,i)=>{
  const c=mtCard(sl.key);const n=mtN(c,sl.key);const ref=mtTopo(sl.func,1)[0];
  const pc=ref&&c?Math.max(0,Math.min(100,Math.round(100*n/ref.n))):0;
  const pu=c?mtPct(sl.key):0;
  const cl=!c?"vaz":(pu>=90?"ok":pu>=50?"md":"fr");
  return `<div class="mtsl ${cl}" data-i="${i}" data-key="${sl.key||''}" draggable="${sl.key?'true':'false'}" style="left:${sl.x}%;top:${sl.y}%" onclick="if(!MT_ED)mtAbreSel(${i})">
   <div class=mtpos>${sl.pos}</div>
    ${c?`<img src="${_fotoCN(c)}" onerror="this.style.visibility='hidden'">
      <div class=mtnm>${c.nome.split(" ").slice(-1)[0]}${estiloAtiva(c)?'':' <span style="color:#e0533d;font-weight:800">•</span>'}</div><div class=mtnt>${n.toFixed(1)}<span style="display:block;font-size:10px;font-weight:800">${pctTopo(c,n)}</span></div>
      <button class=mtcfgbt title="ajustar as barras deste jogador" onclick="event.stopPropagation();mtAbreCfg('${sl.key}')">⚙</button>`
     :`<div class=mtmais>+</div><div class=mtnm style="color:#5d6673">vazio</div>`}
   <div class=mtfn>${(typeof ROT!=="undefined"&&ROT[sl.func])||sl.func}</div>
  </div>`}).join("");
 const banco=MT.banco.map((k,i)=>{const c=mtCard(k);if(!c)return"";
   return `<div class=mtbc draggable=true data-key="${k}" data-de="banco" data-i="${i}" onclick="abrir('${k}')"><img src="${_fotoCN(c)}" onerror="this.style.visibility='hidden'">
   <div style=flex:1><b>${c.nome}</b><div class=mini>${c.tipo}</div></div><b title="nota da carta otimizada (a mesma do ranking)" style="color:${cor(mtMaiorNota(c),0)}">${mtMaiorNota(c).toFixed(1)}</b>
   <button class=bbt title="ajustar barras" onclick="event.stopPropagation();mtAbreCfg('${k}')">⚙</button>
   <button class=bbt onclick="event.stopPropagation();mtTiraBanco(${i})">×</button></div>`}).join("")+(MT.banco.length?'<div style="padding:7px 0 2px"><button class=btn onclick="mtAddBanco()">+ adicionar outra reserva</button></div>':'')||'<div class=mini style="padding:6px 0">Nenhum reserva ainda. <button class=btn style="margin-left:6px" onclick="mtAddBanco()">+ reserva</button></div>';

 const _foraL=mtForaLista();
 const elenco=_foraL.map(({k,i,c})=>{
   return `<div class=mtbc draggable=true data-key="${k}" data-de="elenco" data-i="${i}" onclick="abrir('${k}')"><img src="${_fotoCN(c)}" onerror="this.style.visibility='hidden'">
   <div style=flex:1><b>${c.nome}</b><div class=mini>${c.tipo}</div></div><b title="nota da carta otimizada (a mesma do ranking)" style="color:${cor(mtMaiorNota(c),0)}">${mtMaiorNota(c).toFixed(1)}</b>
   <button class=bbt title="ajustar barras" onclick="event.stopPropagation();mtAbreCfg('${k}')">⚙</button>
   <button class=bbt title="mandar pro banco" onclick="event.stopPropagation();mtProBanco(${i})">\u2191</button>
   <button class=bbt onclick="event.stopPropagation();mtTiraElenco(${i})">\u00d7</button></div>`}).join("")
  ||'<div class=mini style="padding:6px 0">'+((MT.elenco||[]).length?'Nenhum jogador com esse filtro.':'Ninguém fora do banco ainda. <button class=btn style="margin-left:6px" onclick="mtAddElenco()">+ elenco</button>')+'</div>';
 document.getElementById("mtwrap").innerHTML=`
 <div class=mthd>
  <div><b style="font-size:17px">★ ELENCO</b> <span class=mini>· ${tit.length}/11 escalados · média <b style="color:${cor(med,0)}">${med.toFixed(1)}</b></span></div>
  <div style="display:flex;gap:7px;flex-wrap:wrap;align-items:center">
   <select onchange="MT.form=this.value;MT.slots=[];userStateSave();mtRender()">${Object.keys(MT_FORM).map(f=>`<option${f===MT.form?" selected":""}>${f}</option>`).join("")}</select>
   <button class=btn onclick="mtAddBanco()">+ reserva</button>
   <button class=btn onclick="mtAddElenco()">+ elenco</button>
   <button class=btn onclick="mtExporta()" title="baixa o time num arquivo, para levar para a próxima versão">↓ salvar arquivo</button>
   <button class=btn onclick="mtImporta()" title="carrega um time salvo">↑ carregar</button>
   <button class=btn onclick="mtEdit()">${MT_ED?"✓ pronto":"✥ mover posições"}</button>
   ${MT_ED?'<button class=btn onclick="mtResetPos()">restaurar posições</button>':""}
   <button class=btn onclick="mtLimpa()">limpar</button>
  </div>
 </div>
 <div class=mtacts>
  <button class="mtbt pro" onclick="mtOtimizaTudo()">⚡ DEIXAR O TIME NO IDEAL ${(MODO_ADM||PRO)?"":"🔒"}</button>
  <button class="mtbt pro" onclick="mtMelhorFuncao()">🎯 MELHOR FUNÇÃO DE CADA UM</button>
  <button class="mtbt pro" onclick="mtBuracos()">🔍 ONDE MEU TIME ESTÁ FRACO</button>
  <button class="mtbt pro" onclick="mtMelhorFormacao()">🧩 MELHOR FORMAÇÃO PRO MEU ELENCO</button>
  <button class="mtbt pro" onclick="mtTecnicoTime()">🎓 TÉCNICO DO TIME INTEIRO</button>
  <button class="mtbt pro" onclick="mtCompara()">⚖️ COMPARAR COM OUTRO TIME</button>
 </div>
 <div class=mtgrid>
  <div class=mtlado id=mtesq>
   ${mtPainelTec()}
   <div class="mtbanco alvobanco"><div class=bhd><span>Reservas (banco)</span><span style="display:flex;gap:6px;align-items:center"><span class=mini>${(MT.banco||[]).length}</span><button class=btn onclick="mtAddBanco()">+ reserva</button></span></div>${banco}</div>
   ${mtPainelResumo(S1)}
  </div>
  <div class="mtcampo${MT_ED?' edit':''}">${campo}</div>
  </div>
 <div class="mtfora alvoelenco"><div class=bhd><span>Elenco — fora do banco</span><span style="display:flex;gap:6px;align-items:center"><button class=btn onclick="mtAddElenco()">+ elenco</button></span></div>${mtForaBarra(_foraL.length,(MT.elenco||[]).length)}<div class=mtforagrid>${elenco}</div></div>
 <div id=mtsaida></div>
 ${MT_ED?'<div class=mtdicaed>Modo mover posições: arraste para reposicionar as <b>vagas</b> no campo. Clique em "pronto" para voltar a trocar jogadores.</div>'
   :'<div class=mtdicadnd>Arraste um jogador de uma vaga para outra para trocar os dois · do banco para o campo para escalar · do campo para o banco para tirar.</div>'}`;
 /* A troca de jogadores pertence ao renderer aprimorado do Elenco, que
    preserva buildId e aplica a invariável por card_id. Aqui permanece só o
    arraste das coordenadas das vagas; dois DnDs concorrentes não são ligados. */
 mtDragInit();
}
function mtPainelResumo(S1){
 const R=mtResumo(S1);
 const barra=(p)=>`<div class=mtbar><div class=mtbarf style="width:${Math.round(p)}%;background:${p>=92?'#22c58b':p>=80?'#f0a531':'#e0533d'}"></div></div>`;
 const setor=(k)=>{const r=R[k];
  if(!r.escalados)return `<div class=mtset><div class=mtsetn>${k}</div><div class=mini>${r.total} vagas · nenhuma preenchida</div></div>`;
  const pr=r.pior;
  return `<div class=mtset>
   <div class=mtsetn>${k} <b style="color:${cor(r.nota,0)}">${r.nota.toFixed(1)}</b> <span class=mini>· ${Math.round(r.media)}% do teto</span></div>
   ${barra(r.media)}
   <div class=mini>${r.escalados}/${r.total} escalados${r.vazios?` · <b style="color:#f0a531">${r.vazios} vaga${r.vazios>1?'s':''} vazia${r.vazios>1?'s':''}</b>`:''}
   ${pr?` · elo fraco: <b>${pr.c.nome.split(' ').slice(-1)[0]}</b> (${Math.round(pr.f)}% do teto)`:''}</div>
  </div>`;};
 const vagas=S1.map((sl,i)=>({sl,i})).filter(x=>!x.sl.key);
 let sug='';
 if(vagas.length){
  const v=vagas[0]; const s=mtSugestao(v.sl);
  sug=`<div class=mtset><div class=mtsetn>PARA A VAGA DE ${v.sl.pos}</div>
   <div class=mini style="margin-bottom:5px">${s.doElenco?'do seu elenco':'⚠️ seu elenco não cobre — estes são os melhores do banco'}</div>
   ${s.lista.map(x=>`<div class=mtsug onclick="mtPoeDireto(${v.i},'${x.c.id}|${x.c.tipo}')">
     <span style="flex:1">${x.c.nome}</span>
     ${x.meu?'<span class=mtmeu>meu</span>':''}
     <b style="color:${cor(x.n,0)}">${x.n.toFixed(1)}</b> <span style="font-size:10px;font-weight:800">${pctTopo(x.c,x.n)}</span></div>`).join('')||'<div class=mini>sem candidato</div>'}
  </div>`;
 }
 return `<div class=mtresumo>${['DEFESA','MEIO','ATAQUE'].map(setor).join('')}${sug}</div>`;
}
function mtPoeDireto(i,k){
 const inv=window.ElencoCardInvariant,sl=MT.slots[i];if(!inv||!sl)return false;
 const p=inv.planMove(k,'campo',i);if(!p.ok){inv.notify(k,true);return false;}if(p.noOp)return true;
 inv.detach(p);sl.key=k;sl.buildId=p.buildId||'base';userStateSave();mtRender();return true;
}

/* ===== v143 · LEVAR O TIME DE UMA VERSÃO PARA OUTRA =====
   O time é gravado sozinho, mas no localStorage — e arquivo aberto como file://
   tem armazenamento POR ARQUIVO. Como cada versão vem com nome novo, o time
   sumiria a cada atualização. Estes dois botões resolvem. */
function mtExporta(){
 const pacote={_o:'encaixe-meu-time', _v:1, quando:new Date().toISOString(), time:MT};
 const b=new Blob([JSON.stringify(pacote,null,1)],{type:'application/json'});
 const a=document.createElement('a');
 a.href=URL.createObjectURL(b);
 a.download='meu-time-'+new Date().toISOString().slice(0,10)+'.json';
 a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),2000);
}
function mtImporta(){
 const inp=document.createElement('input');
 inp.type='file'; inp.accept='.json,application/json';
 inp.onchange=()=>{const f=inp.files[0]; if(!f)return;
  const r=new FileReader();
  r.onload=()=>{ try{
    const p=JSON.parse(r.result);
    const t=p&&p.time?p.time:p;
    if(!t||!Array.isArray(t.slots))throw new Error('arquivo não parece um time');
    /* só entra card que existe neste banco — carta que saiu do jogo não quebra a tela */
    const vale=k=>!!(k&&_card(k));
    t.slots=t.slots.map(sl=>Object.assign({},sl,{key:vale(sl.key)?sl.key:null}));
    t.banco=(t.banco||[]).filter(vale);
    t.elenco=(t.elenco||[]).filter(vale);
    const perdidos=(p.time||p).slots.filter(sl=>sl.key&&!vale(sl.key)).length;
    MT=Object.assign({form:'4-3-3',slots:[],banco:[],elenco:[],nome:'Meu time'},t);
    userStateSave(); mtRender();
    alert('Time carregado.'+(perdidos?'\n\n'+perdidos+' jogador(es) não existem mais neste banco e ficaram de fora.':''));
   }catch(e){ alert('Não consegui ler: '+e.message); } };
  r.readAsText(f);};
 inp.click();
}
function mtLimpa(){if(!confirm("Apagar o time todo?"))return;MT.slots=[];MT.banco=[];userStateSave();mtRender();}
function mtTiraBanco(i){MT.banco.splice(i,1);userStateSave();mtRender();}
function mtTiraElenco(i){MT.elenco.splice(i,1);userStateSave();mtRender();}
function mtProBanco(i){
 const k=(MT.elenco||[])[i],inv=window.ElencoCardInvariant;if(!k||!inv)return false;
 const p=inv.planMove(k,'banco',null);if(!p.ok){inv.notify(k,true);return false;}if(p.noOp)return true;
 inv.detach(p);MT.banco=MT.banco||[];MT.banco.push(k);
 try{if(window.elPreservaBuildMovida)window.elPreservaBuildMovida('banco',k,p.buildId);}catch(e){}
 userStateSave();mtRender();return true;
}
function mtAddElenco(){MT_SEL={elenco:1};mtListaSel("");}

/* ---- seletor de card ---- */
function mtAbreSel(i){MT_SEL={slot:i};mtListaSel("");}
function mtAddBanco(){MT_SEL={banco:1};mtListaSel("");}
/* v143 · TODAS as 18 funções ficam disponíveis para qualquer vaga.
   O Luis: "está como armador, e não é armador, ele é um volante que eu estou
   colocando. A gente tem que poder personalizar isso aqui." */
const MT_TODAS=(()=>{const v=[];FAM.forEach(([f,ts])=>{if(f!=='★')ts.forEach(t=>v.push(t));});return v;})();
function mtListaSel(q){
 if(_t6BloqueioBuildsElenco()){mtRender();return false;}
 const sl=MT_SEL.slot!==undefined?MT.slots[MT_SEL.slot]:null;
 const sugeridas=sl?MT_FUNCS[sl.pos]:[];
 const funcs=sl?sugeridas.concat(MT_TODAS.filter(f=>!sugeridas.includes(f))):MT_TODAS;
 const fsel=sl?sl.func:(MT_SEL.func||funcs[0]);
 const nq=nz(q||"");
 const livre=!sl;
 const L=(livre
  ? D.filter(c=>c.id!=="MOLDE"&&(!nq||nz(c.nome).includes(nq)))
  : D.filter(c=>c.id!=="MOLDE"&&c.tipo===fsel&&(!nq||nz(c.nome).includes(nq))))
  .map(c=>({c,n:nota(c)})).sort((a,b)=>b.n-a.n).slice(0,120);
 /* achou nada nesta função? procura o nome nas OUTRAS e diz onde está.
    Era o caso do Neuer: existe, mas só como Goleiro ofensivo. */
 let noutra='';
 if(nq&&!L.length&&!livre){
  const o=D.filter(c=>c.id!=="MOLDE"&&nz(c.nome).includes(nq))
   .map(c=>({c,n:nota(c)})).sort((a,b)=>b.n-a.n).slice(0,8);
  noutra=o.length?`<div class=mtnoutra><b>Não joga de ${fsel}.</b> Mas está em:</div>`+
   o.map(x=>`<div class=mtli onclick="mtVaiPara('${x.c.tipo}','${(q||'').replace(/'/g,"")}')">
      <img src="${_fotoCN(x.c)}" onerror="this.style.visibility='hidden'">
     <div style=flex:1><b>${x.c.nome}</b><div class=mini>${x.c.tipo}</div></div>
     <b style="color:${cor(x.n,0)};font-size:15px">${x.n.toFixed(1)}</b> <span style="font-size:10px;font-weight:800">${pctTopo(x.c,x.n)}</span></div>`).join('')
   :'<div class=mini>Nenhum jogador com esse nome no banco.</div>';
 }
 document.getElementById("box").innerHTML=`
 <span class=close onclick="fechar()">×</span>
 <div style="font-size:18px;font-weight:800;margin-bottom:6px">${sl?"Quem joga de "+sl.pos:(MT_SEL.elenco?"Adicionar ao elenco":"Adicionar reserva")}</div>
 ${livre?'':`<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:9px">${funcs.map((f,i)=>`<div class="tab${f===fsel?" on":""}" onclick="mtTrocaFunc('${f}')" ${sl&&i===sugeridas.length?'style="margin-left:10px;opacity:.7"':(sl&&i>sugeridas.length?'style="opacity:.7"':'')}>${f}</div>`).join("")}</div>`}
 ${sl?'<div class=mini style="margin:-4px 0 9px">as duas primeiras são as da posição; as outras são livres, escolha a que você vai usar de verdade</div>':'<div class=mini style="margin:-2px 0 9px">busque pelo nome — entra qualquer carta, a função você define depois</div>'}
 <input type=search id=mtq placeholder="buscar pelo nome" style="width:100%;margin-bottom:9px" oninput="mtBusca(this.value)" value="${(q||"").replace(/"/g,"&quot;")}">
 ${sl&&sl.key?`<button class=btn style="margin-bottom:9px" onclick="mtPoe(null)">✕ tirar este jogador da vaga</button>`:""}
 <div class=mtlist id=mtlist>${noutra}${L.map(x=>`<div class=mtli onclick="mtPoe('${x.c.id}|${x.c.tipo}')">
    <img src="${_fotoCN(x.c)}" onerror="this.style.visibility='hidden'">
   <div style=flex:1><b>${x.c.nome}</b><div class=mini>${livre?x.c.tipo+" · ":""}${x.c.tier} · ${x.c.votos} votos · ${x.c.modelo||""}${x.c.MIG?' · <span style="color:#c4a5ff">migrado</span>':""}</div></div>
   <b style="color:${cor(x.n,0)};font-size:16px">${x.n.toFixed(1)}</b> <span style="font-size:10px;font-weight:800">${pctTopo(x.c,x.n)}</span></div>`).join("")||(noutra?"":'<div class=mini>Nada encontrado.</div>')}</div>`;
 const ov=document.getElementById("ov");ov.style.display="block";
 const vb=document.getElementById("voltar");if(vb)vb.style.display="block";
 if(!(history.state&&history.state.ficha))history.pushState({ficha:1},"");
}
function mtTrocaFunc(f){if(MT_SEL.slot!==undefined){MT.slots[MT_SEL.slot].func=f;userStateSave();}else MT_SEL.func=f;
 mtListaSel(document.getElementById("mtq")?document.getElementById("mtq").value:"");}
/* v143 · o campo de busca perdia o foco a cada letra porque a caixa inteira era
   redesenhada. Agora só a LISTA é redesenhada, e o cursor fica onde estava. */
let MT_BUSCA_T=null;
function mtBusca(q){
 clearTimeout(MT_BUSCA_T);
 MT_BUSCA_T=setTimeout(()=>{
  const el=document.getElementById('mtq');
  const pos=el?el.selectionStart:null;
  mtListaSel(q);
  const n=document.getElementById('mtq');
  if(n){ n.focus(); if(pos!==null){ try{n.setSelectionRange(pos,pos);}catch(e){} } }
 },120);
}
function mtVaiPara(func,q){
 if(MT_SEL.slot!==undefined){ MT.slots[MT_SEL.slot].func=func; userStateSave(); }
 else MT_SEL.func=func;
 mtListaSel(q);
}
function mtPoe(k){
 const inv=window.ElencoCardInvariant;
 if(k){
  if(!inv)return false;
  const grupo=MT_SEL.slot!==undefined?'campo':(MT_SEL.elenco?'fora':'banco');
  const indice=MT_SEL.slot!==undefined?MT_SEL.slot:null,p=inv.planMove(k,grupo,indice);
  if(!p.ok){inv.notify(k,true);return false;}if(p.noOp)return true;
  inv.detach(p);
  if(MT_SEL.slot!==undefined){MT.slots[MT_SEL.slot].key=k;MT.slots[MT_SEL.slot].buildId=p.buildId||'base';}
  else if(MT_SEL.elenco){MT.elenco=MT.elenco||[];MT.elenco.push(k);
   try{if(window.elPreservaBuildMovida)window.elPreservaBuildMovida('fora',k,p.buildId);}catch(e){}}
  else{MT.banco=MT.banco||[];MT.banco.push(k);
   try{if(window.elPreservaBuildMovida)window.elPreservaBuildMovida('banco',k,p.buildId);}catch(e){}}
 }
 userStateSave();
 if(MT_SEL.slot!==undefined){fechar();mtRender();}
 else{mtRender();mtListaSel(document.getElementById('mtq')?document.getElementById('mtq').value:'');}}

/* ---- gate da função paga ---- */
function _proImpressao(s){var x=5381;for(var i=0;i<s.length;i++)x=((x*33)^s.charCodeAt(i))>>>0;return x;}
function mtPro(){
 if(MODO_ADM||PRO)return true;
 const ch=prompt("Recurso PRO. Digite a chave de acesso:");
 /* ⛔ 25/08 — A CHAVE SAIU DO TEXTO CLARO.
    Ate hoje a comparacao era com a palavra escrita: bastava abrir o F12 e ler
    a senha do plano pago no proprio arquivo. Agora comparamos a impressao
    (djb2 de 32 bits) e a palavra nao esta escrita em lugar nenhum. Mesma senha,
    mesmo comportamento — conferido: 3821596949, e nao colide com "encaixe",
    "pro" nem com a palavra com espaco.
    ⚠️ ISTO NAO E SEGURANCA, e higiene. Cadeado que roda no navegador do
    visitante nao protege nada: quem quiser burla em dois minutos. A protecao de
    verdade e o login com sessao no servidor — etapa 11. */
 if(ch&&_proImpressao(nz(ch))===3821596949){PRO=true;try{localStorage.setItem("MT_PRO","1")}catch(e){};mtRender();return true;}
 alert("Chave inválida. Este recurso faz parte do plano pago.");return false;}
try{if(localStorage.getItem("MT_PRO")==="1")PRO=true}catch(e){}
try{const m=localStorage.getItem('encaixe_adm');if(m==='0'){MODO_ADM=0;}}catch(e){}
document.documentElement.dataset.modo=MODO_ADM?'adm':'user';
window.addEventListener('DOMContentLoaded',()=>{const b=document.getElementById('modobt');
 if(b&&!MODO_ADM){b.textContent='👤 usuário';b.style.borderColor='#22c58b';b.style.color='#22c58b';}});

/* ---- ações ---- */
function mtTitulares(){return MT.slots.filter(x=>x.key).map(x=>({sl:x,c:mtCard(x.key)})).filter(x=>x.c);}
function mtSaida(h){document.getElementById("mtsaida").innerHTML=h;document.getElementById("mtsaida").scrollIntoView({behavior:"smooth",block:"start"});}


/* ===== v147 · TÉCNICO DO TIME INTEIRO =====
   No jogo o técnico dá +1 nos atributos dele para TODO MUNDO. Então a escolha
   não é por card, é por time: qual técnico soma mais nota nos 11 juntos. */
/* a nota lê b1n (tradução viva), não b1 — sem reescalar, trocar o técnico não
   mexia em nada. Aqui a escala do tipo é medida uma vez e reaproveitada. */
const _ESC={};
function escalaDe(tipo){
 if(_ESC[tipo])return _ESC[tipo];
 const v=D.filter(c=>c.tipo===tipo&&c.id!=="MOLDE").map(c=>c.b1).sort((a,b)=>a-b);
 const med=v[Math.floor(v.length/2)]||-1, top=Math.max(1,v[v.length-1]);
 return _ESC[tipo]={sa:20/top, sb:med<0?14/(0-med):1};
}
function b1nDe(tipo,b1){const e=escalaDe(tipo);
 return Math.round((92+(b1>=0?b1*e.sa:b1*e.sb))*10)/10;}
function notaComTec(c,bs){
 const salvo=c._tec, b1s=c.b1, b1ns=c.b1n, ar=c.arows.map(r=>r.slice());
 c._tec=bs||[];
 const vals=valsDeLvl(c,_lvlDe(c));
 c.arows.forEach((r,k)=>{r[3]=vals[r[0]];r[4]=r[3]-r[2];r[5]=r[3];});
 c.b1=notaDe(vals,c.arows); c.b1n=(function(A){var n=0,d=0,i,w;A=A||[];for(i=0;i<A.length;i++){w=A[i][1];if(!w)continue;n+=w*A[i][3];d+=w*A[i][2];}return d?100*n/d:b1nDe(c.tipo,c.b1);})(c.arows); delete c._n;
 const n=nota(c);
 c.arows=ar; c.b1=b1s; c.b1n=b1ns; delete c._n;
 if(salvo===undefined)delete c._tec; else c._tec=salvo;
 return n;
}

/* ===== v148 · TÉCNICO DO TIME (principal + reservas) =====
   O jogo tem UM técnico em campo e um plantel de técnicos guardados. Enquanto
   o Luis não escolher, o time aparece SEM técnico nenhum — a nota com "o
   técnico ideal de cada um" é impossível no jogo e enganava. */

/* ===== v149 · O TIME É O DELE, NÃO O IDEAL =====
   Decisão do Luis: "o time que ele vai colocar lá é o time dele, do jeito que
   está no videogame dele. Aí depois a gente cobra pra otimizar."
   Então cada jogador entra CRU (nenhum ponto distribuído) e ele digita as
   barras que tem de verdade. O botão que preenche a build ótima é o produto. */

/* ===== v149 · % DO IDEAL =====
   A regua de falta e acelerada e sem teto: card cru marca -1114. Numero
   impossivel de mostrar. No Meu Time o que aparece e o quanto ele ja tirou
   daquela carta: 0% = nada distribuido, 100% = build do motor.
   A nota crua fica intacta e continua visivel no modo admin. */
const _MTREF={};
function mtRef(k){
 if(_MTREF[k])return _MTREF[k];
 const c=mtCard(k); if(!c)return {cru:0,ideal:1};
 const z={}; MBK.forEach(b=>z[b]=0);
 return _MTREF[k]={cru:notaCfg(c,z,[]), ideal:notaCfg(c,_oriDe(c).lvl,[])};
}
function mtPct(k){
 const r=mtRef(k), c=mtCard(k); if(!c)return 0;
 const at=notaCfg(c,mtCfg(k).lvl,[]);
 const d=r.ideal-r.cru; if(d<=0)return at>=r.ideal?100:0;
 return Math.max(0,Math.min(100,Math.round(100*(at-r.cru)/d)));
}
function mtIdealDe(k){ const c=mtCard(k); if(!c)return; const cfg=mtCfg(k);
 const o=_oriDe(c); MBK.forEach(b=>cfg.lvl[b]=o.lvl[b]||0); }
function mtTodosDoTime(){
 return MT.slots.filter(s=>s.key).map(s=>s.key)
  .concat(MT.banco||[]).concat(MT.elenco||[]);
}
/* ===== O PRODUTO PAGO =====
   Ordem do Luis: roda o motor em TODOS os que ele pos (os 22), SEM tecnico,
   e so no fim descobre qual tecnico e o ideal pro time ja otimizado. */
function mtOtimizaTudo(){
 if(_t6BloqueioBuildsElenco()){mtRender();return false;}
 if(!MODO_ADM&&!PRO){ mtVendaIdeal(); return; }
 const ks=mtTodosDoTime(); if(!ks.length){alert('Ponha alguém no time primeiro.');return;}
 const antes=ks.map(k=>({k,pct:mtPct(k),n:notaCfg(mtCard(k),mtCfg(k).lvl,[])}));
 ks.forEach(mtIdealDe);
 userStateSave();
 const depois=ks.map(k=>notaCfg(mtCard(k),mtCfg(k).lvl,[]));
 const linhas=ks.map((k,i)=>{const c=mtCard(k);
  return `<div class=mtrl><span style=flex:1>${c.nome} <span class=mini>· ${c.tipo}</span></span>
   <span style="width:70px;text-align:right" class=mini>${antes[i].pct}%</span>
   <span style="width:30px;text-align:center" class=mini>→</span>
   <b style="width:60px;text-align:right;color:#22c58b">100%</b>
   <b style="width:80px;text-align:right">+${(depois[i]-antes[i].n).toFixed(1)}</b></div>`;}).join('');
 mtRender();
 mtSaida(`<div class=mtcx>
  <div class=mtcxt>⚡ TIME OTIMIZADO — ${ks.length} JOGADORES</div>
  <div class=mini style="margin-bottom:8px">Motor rodado em cada um, sem técnico. O técnico é a última decisão — está logo abaixo.</div>
  ${linhas}
  <div style="margin-top:11px"><button class="mtbt pro" onclick="mtTecnicoTime()">🎓 AGORA SIM: QUAL TÉCNICO PRA ESTE TIME</button></div>
 </div>`);
}
function mtVendaIdeal(){
 mtSaida(`<div class=mtcx>
  <div class=mtcxt>⚡ DEIXAR O TIME NO IDEAL</div>
  <div style="font-size:13px;line-height:1.6">O time acima é <b>o seu</b>, do jeito que está no seu jogo.
  O que a gente faz é descobrir, carta por carta, <b>onde gastar cada ponto</b> pra tirar o máximo dela —
  e só no fim qual técnico casa com o time já ajustado.</div>
  <div class=mtdet style="margin-top:9px">${mtTodosDoTime().slice(0,22).map(k=>{const c=mtCard(k);
    return `<span class=mtchip>${c?c.nome.split(' ').slice(-1)[0]:''} <b>${mtPct(k)}%</b></span>`;}).join('')}</div>
  <div class=mini style="margin-top:8px">Cada número é o quanto você já tirou daquela carta. 100% é o teto dela.</div>
 </div>`);
}
function mtCfg(k){ MT.cfg=MT.cfg||{}; if(!MT.cfg[k]){const l={};MBK.forEach(b=>l[b]=0);MT.cfg[k]={lvl:l};} 
 MBK.forEach(b=>{if(MT.cfg[k].lvl[b]===undefined)MT.cfg[k].lvl[b]=0;}); return MT.cfg[k]; }
function notaCfg(c,lvl,bs){
 const salvo=c._tec,b1s=c.b1,b1ns=c.b1n,ar=c.arows.map(r=>r.slice());
 c._tec=bs||[];
 const vals=valsDeLvl(c,lvl);
 c.arows.forEach((r,j)=>{r[3]=vals[r[0]];r[4]=r[3]-r[2];r[5]=r[3];});
 c.b1=notaDe(vals,c.arows); c.b1n=(function(A){var n=0,d=0,i,w;A=A||[];for(i=0;i<A.length;i++){w=A[i][1];if(!w)continue;n+=w*A[i][3];d+=w*A[i][2];}return d?100*n/d:b1nDe(c.tipo,c.b1);})(c.arows); delete c._n;
 const n=nota(c);
 c.arows=ar;c.b1=b1s;c.b1n=b1ns;delete c._n;
 if(salvo===undefined)delete c._tec;else c._tec=salvo;
 return n;
}
function mtNotaReal(k){const c=mtCard(k);if(!c)return 0;return notaCfg(c,mtCfg(k).lvl,mtTecBs());}
function mtGasto(k){return gastoDe(mtCfg(k).lvl);}

let MT_CFG_K=null;
function mtAbreCfg(k){ MT_CFG_K=k; mtDesenhaCfg(); }
function mtBarra(b,d){ const cfg=mtCfg(MT_CFG_K), c=mtCard(MT_CFG_K);
 const nv=Math.max(0,Math.min(25,(cfg.lvl[b]||0)+d)), antes=cfg.lvl[b];
 cfg.lvl[b]=nv;
 if(gastoDe(cfg.lvl)>(c.orc||0)){cfg.lvl[b]=antes;alert('Sem pontos: esse nível custa '+Math.ceil(nv/4)+' e só sobram '+((c.orc||0)-gastoDe(cfg.lvl))+'.');return;}
 userStateSave(); mtDesenhaCfg(); mtRender();
}
function mtZeraCfg(){ const cfg=mtCfg(MT_CFG_K); MBK.forEach(b=>cfg.lvl[b]=0); userStateSave(); mtDesenhaCfg(); mtRender(); }
function mtIdeal(){
 if(!MODO_ADM&&!PRO){ fechar(); mtVendaIdeal(); return; }
 mtIdealDe(MT_CFG_K); userStateSave(); mtDesenhaCfg(); mtRender();
}
function mtDesenhaCfg(){
 const k=MT_CFG_K, c=mtCard(k); if(!c)return;
 const cfg=mtCfg(k), gasto=gastoDe(cfg.lvl), orc=c.orc||0;
 const agora=notaCfg(c,cfg.lvl,mtTecBs());
 const cru=(()=>{const l={};MBK.forEach(b=>l[b]=0);return notaCfg(c,l,mtTecBs());})();
 const teto=notaCfg(c,_oriDe(c).lvl,mtTecBs());
 const linhas=MBK.filter(b=>!(c.pos==='GK')===b.startsWith('gk')?true:true).map(b=>{
  const n=cfg.lvl[b]||0;
  return `<div class=mtbl><span style=flex:1>${MBN[b]}</span>
   <span class=mtblb><i style="width:${n*4}%"></i></span>
   <button class=bbt onclick="mtBarra('${b}',-1)">−</button><b class=bnum>${n}</b><button class=bbt onclick="mtBarra('${b}',1)">+</button></div>`;}).join('');
 document.getElementById('box').innerHTML=`
 <span class=close onclick="fechar()">×</span>
 <div style="font-size:18px;font-weight:800">${c.nome}</div>
 <div class=mini style="margin-bottom:9px">${c.tipo} · ${c.tier} · o que está aqui é a <b>sua</b> configuração no jogo</div>
 <div class=mtcx style="margin:0 0 10px">
  <div class=mtrl><span style=flex:1><b>Como você tem hoje</b></span><b style="font-size:22px;color:${cor(agora,0)}">${agora.toFixed(1)}</b></div>
  <div class=mtrl><span style=flex:1 class=mini>sem gastar nada <b>${cru.toFixed(1)}</b> · no teto desta carta <b>${teto.toFixed(1)}</b></span><b style="color:${mtPct(k)>=90?'#22c58b':mtPct(k)>=50?'#f0a531':'#8b949e'}">${mtPct(k)}%</b></div>
  <div class=mtblb style="flex:none;width:100%;height:9px;margin:4px 0 2px"><i style="width:${mtPct(k)}%"></i></div>
  <div class=mini>0% = nenhum ponto distribuído · 100% = o máximo que esta carta dá</div>

 </div>
 <div class=bhd><span>Barras</span><span class=bhdnum>Pontos <b>${gasto}</b>/<b>${orc}</b>${orc-gasto?` · sobram <b style="color:#f0a531">${orc-gasto}</b>`:' · <b style="color:#22c58b">tudo gasto</b>'}</span></div>
 ${linhas}
 <div style="display:flex;gap:7px;margin-top:11px;flex-wrap:wrap">
  <button class=btn onclick="mtZeraCfg()">zerar</button>
  <button class="mtbt pro" style="flex:1" onclick="mtIdeal()">⚡ DEIXAR A BUILD IDEAL ${(MODO_ADM||PRO)?'':'🔒'}</button>
 </div>
 <div class=mini style="margin-top:8px">Ponha aqui exatamente o que está no seu jogo. O técnico não entra por jogador — é um só, do time todo, no painel do lado.</div>`;
 const ov=document.getElementById('ov');ov.style.display='block';
 const vb=document.getElementById('voltar');if(vb)vb.style.display='block';
 if(!(history.state&&history.state.ficha))history.pushState({ficha:1},'');
}
function mtTecBs(){ return (MT.tec===undefined||MT.tec===null)?[]:(TECS[MT.tec]?TECS[MT.tec][1]:[]); }
function mtTecNome(){ return (MT.tec===undefined||MT.tec===null)?null:(TECS[MT.tec]?TECS[MT.tec][0]:null); }
function mtPoeTec(v){
 MT.tec = v===''?null:+v;
 if(MT.tec!==null){MT.tecRes=(MT.tecRes||[]).filter(i=>i!==MT.tec);}
 userStateSave(); mtRender();
}
function mtAddTecRes(v){
 if(v==='')return; const i=+v;
 MT.tecRes=MT.tecRes||[];
 if(i!==MT.tec&&!MT.tecRes.includes(i))MT.tecRes.push(i);
 userStateSave(); mtRender();
}
function mtTiraTecRes(i){ MT.tecRes.splice(i,1); userStateSave(); mtRender(); }
function mtSobeTecRes(i){
 const novo=MT.tecRes[i]; MT.tecRes.splice(i,1);
 if(MT.tec!==null&&MT.tec!==undefined)MT.tecRes.push(MT.tec);
 MT.tec=novo; userStateSave(); mtRender();
}
const _TECOP=(()=>{const v=[],vis={};TECS.forEach((t,i)=>{const k=t[0]+'|'+t[1].join(',');if(vis[k])return;vis[k]=1;v.push([i,t[0]+' · +1 '+t[1].map(tecPT).join(' · ')]);});return v;})();
function mtPainelTec(){
 const res=(MT.tecRes||[]);
 return `<div class=mttec>
  <div class=bhd><span>⚽ Técnico do time</span><span class=mini>${res.length} reserva${res.length===1?'':'s'}</span></div>
  <select onchange="mtPoeTec(this.value)" style="width:100%">
   <option value=""${MT.tec===null||MT.tec===undefined?' selected':''}>— sem técnico —</option>
   ${_TECOP.map(([i,r])=>`<option value="${i}"${MT.tec===i?' selected':''}>${r}</option>`).join('')}
  </select>
  ${MT.tec===null||MT.tec===undefined
   ?'<div class=mtavtec>Sem técnico escolhido — as pontuações do campo estão <b>sem o bônus do técnico</b>. Escolha um e o time inteiro se recalcula.</div>'
   :`<div class=mtoktec>Aplicado nos 11: <b>+1</b> em ${mtTecBs().map(tecPT).join(' · ')}</div>`}
  <div class=bhd style="margin-top:9px"><span>Técnicos reservas</span></div>
  ${res.map((i,k)=>`<div class=mtrl2><span style=flex:1>${TECS[i][0]} <span class=mini>· ${TECS[i][1].map(tecPT).join(' · ')}</span></span>
    <button class=bbt title="por em campo" onclick="mtSobeTecRes(${k})">↑</button>
    <button class=bbt onclick="mtTiraTecRes(${k})">×</button></div>`).join('')||'<div class=mini style="padding:4px 0">Nenhum guardado.</div>'}
  <select onchange="mtAddTecRes(this.value);this.value=''" style="width:100%;margin-top:6px">
   <option value="">+ guardar um técnico reserva…</option>
   ${_TECOP.filter(([i])=>i!==MT.tec&&!res.includes(i)).map(([i,r])=>`<option value="${i}">${r}</option>`).join('')}
  </select>
 </div>`;
}
function mtTecnicoTime(){
 if(!window.RouteState||typeof window.RouteState.navigate!=='function')return false;
 return window.RouteState.navigate('tecnicotime');
 /* Fluxo legado preservado abaixo apenas como referência histórica. */
 if(!mtPro())return;
 const T=mtTitulares(); if(T.length<2){alert("Escale pelo menos 2 jogadores.");return;}
 const base=T.reduce((a,x)=>a+nota(x.c),0);
 const semTec=T.reduce((a,x)=>a+notaComTec(x.c,[]),0);
 const vistos={}, res=[];
 TECS.forEach((t,idx)=>{
  const ch=t[0]+'|'+t[1].join(','); if(vistos[ch])return; vistos[ch]=1;
  let s=0; const porJog=T.map(x=>{const n=notaComTec(x.c,t[1]);s+=n;return {c:x.c,n,d:n-nota(x.c)};});
  res.push({nome:t[0],bs:t[1],idx,soma:s,ganho:s-semTec,porJog:porJog.map(j=>({c:j.c,n:j.n,d:j.n-notaComTec(j.c,[])}))});
 });
 res.sort((a,b)=>b.soma-a.soma);
 const top=res.slice(0,8);
 mtSaida(`<div class=mtcx>
  <div class=mtcxt>🎓 TÉCNICO DO TIME INTEIRO</div>
  <div class=mini style="margin-bottom:9px">O jogo só deixa ter <b>um</b> técnico. Comparação feita contra o time <b>sem técnico nenhum</b> — é a única base honesta. A pontuação que aparece na tela hoje dá a cada card o técnico ideal <i>dele</i>, o que o jogo não permite.</div>
  <div class=mtrl style="font-weight:700;opacity:.7"><span style=flex:1>Técnico</span><span style="width:180px">Reforça</span><span style="width:70px;text-align:right">Ganho</span><span style="width:80px;text-align:right">Time</span></div>
  ${top.map((r,i)=>`<div class=mtrl>
    <span style=flex:1><b>${i===0?'🥇 ':''}${r.nome}</b></span>
    <span style="width:180px" class=mini>${r.bs.map(tecPT).join(' · ')}</span>
    <b style="width:70px;text-align:right;color:${r.ganho>0?'#22c58b':'#8b949e'}">${r.ganho>0?'+':''}${r.ganho.toFixed(1)}</b>
    <b style="width:80px;text-align:right">${(r.soma/T.length).toFixed(1)}</b></div>
   ${i===0?`<div class=mtdet>${r.porJog.slice().sort((a,b)=>b.d-a.d).map(j=>`<span class=mtchip>${j.c.nome.split(' ').slice(-1)[0]} <b style="color:${j.d>0?'#22c58b':'#8b949e'}">${j.d>0?'+':''}${j.d.toFixed(1)}</b></span>`).join('')}</div>`:''}`).join('')}
  <div class=mini style="margin-top:8px">Sem técnico: <b>${(semTec/T.length).toFixed(1)}</b> · com o melhor técnico: <b style="color:#22c58b">${(top[0].soma/T.length).toFixed(1)}</b> · na tela hoje (cada um com o ideal dele, impossível no jogo): <b>${(base/T.length).toFixed(1)}</b></div>
 </div>`);
}

/* ===== v147 · COMPARAR DOIS TIMES =====
   Carrega um time salvo em arquivo e põe lado a lado com o que está na tela. */
function mtCompara(){
 if(!window.RouteState||typeof window.RouteState.navigate!=='function')return false;
 return window.RouteState.navigate('comparartime');
 /* Fluxo legado preservado abaixo apenas como referência histórica. */
 if(!mtPro())return;
 const inp=document.createElement('input'); inp.type='file'; inp.accept='.json,application/json';
 inp.onchange=()=>{const f=inp.files[0]; if(!f)return; const r=new FileReader();
  r.onload=()=>{try{
    const p=JSON.parse(r.result), t=p&&p.time?p.time:p;
    if(!t||!Array.isArray(t.slots))throw new Error('não parece um time salvo');
    mtDesenhaComp(t, f.name.replace(/\.json$/i,''));
   }catch(e){alert('Não consegui ler: '+e.message);}};
  r.readAsText(f);};
 inp.click();
}
function mtLadoDe(slots){
 const L=slots.filter(s=>s&&s.key).map(s=>{const c=_card(s.key);return c?{pos:s.pos,func:s.func,c,n:nota(c)}:null;}).filter(Boolean);
 const set={DEFESA:[],MEIO:[],ATAQUE:[]};
 L.forEach(x=>{const s=MT_SETOR[x.pos]||'MEIO';(set[s]=set[s]||[]).push(x);});
 const md=a=>a.length?a.reduce((s,x)=>s+x.n,0)/a.length:0;
 return {L, n:L.length, media:md(L), DEFESA:md(set.DEFESA), MEIO:md(set.MEIO), ATAQUE:md(set.ATAQUE),
  set, pior:L.slice().sort((a,b)=>a.n-b.n)[0], melhor:L.slice().sort((a,b)=>b.n-a.n)[0]};
}
function mtDesenhaComp(outro,nomeArq){
 const A=mtLadoDe(MT.slots), B=mtLadoDe(outro.slots);
 const dif=(a,b)=>{const d=a-b;return `<b style="color:${d>0.05?'#22c58b':d<-0.05?'#e0533d':'#8b949e'}">${d>0?'+':''}${d.toFixed(1)}</b>`;};
 const linha=(rot,a,b)=>`<div class=mtrl><span style=flex:1>${rot}</span>
   <b style="width:70px;text-align:right;color:${cor(a,0)}">${a?a.toFixed(1):'—'}</b>
   <span style="width:70px;text-align:right">${dif(a,b)}</span>
   <b style="width:70px;text-align:right;color:${cor(b,0)}">${b?b.toFixed(1):'—'}</b></div>`;
 const nomes=(x)=>x.L.slice().sort((p,q)=>q.n-p.n).map(j=>`<div class=mtrl2><span style=flex:1>${j.c.nome}</span><b style="color:${cor(j.n,0)}">${j.n.toFixed(1)}</b></div>`).join('')||'<div class=mini>vazio</div>';
 mtSaida(`<div class=mtcx>
  <div class=mtcxt>⚖️ MEU TIME × ${(nomeArq||'time carregado').toUpperCase()}</div>
  <div class=mtrl style="font-weight:700;opacity:.7"><span style=flex:1></span>
   <span style="width:70px;text-align:right">este</span><span style="width:70px;text-align:right">dif.</span><span style="width:70px;text-align:right">outro</span></div>
  ${linha('<b>MÉDIA GERAL</b>',A.media,B.media)}
  ${linha('Escalados',A.n,B.n)}
  ${linha('Defesa',A.DEFESA,B.DEFESA)}
  ${linha('Meio',A.MEIO,B.MEIO)}
  ${linha('Ataque',A.ATAQUE,B.ATAQUE)}
  ${linha('Melhor jogador',A.melhor?A.melhor.n:0,B.melhor?B.melhor.n:0)}
  ${linha('Elo mais fraco',A.pior?A.pior.n:0,B.pior?B.pior.n:0)}
  <div class=mtdet style="margin-top:9px">
   ${A.pior?`Seu elo fraco: <b>${A.pior.c.nome}</b> (${A.pior.n.toFixed(1)}) · `:''}
   ${B.pior?`Elo fraco do outro: <b>${B.pior.c.nome}</b> (${B.pior.n.toFixed(1)})`:''}</div>
  <div class=mtcomp2>
   <div><div class=mtcxt2>ESTE TIME</div>${nomes(A)}</div>
   <div><div class=mtcxt2>${(nomeArq||'OUTRO').toUpperCase()}</div>${nomes(B)}</div>
  </div>
 </div>`);
}
function mtOtimizaTime(){
 if(!mtPro())return;
 const T=mtTitulares().concat(MT.banco.map(k=>({sl:null,c:mtCard(k)})).filter(x=>x.c));
 if(!T.length){alert("Escale alguém primeiro.");return;}
 const res=[];
 T.forEach(({c})=>{
  const antes=nota(c);
  if(c.orc){const b=buildOtimo(c);
   c.imps=(c.imps||[]).filter(x=>!x.f);
   (b.fab||[]).forEach(n=>n.split(" + ").forEach(x=>c.imps.push({n:x,c:0,f:1})));
   c.imp=c.imps.map(x=>x.n+(x.f?" ⚒":"")).join(" · ");
   const start=_startDe(c),vals=aplicar(start,b.lvl);
   c.sis=vals;c.sisBar=MBK.filter(x=>b.lvl[x]>0).map(x=>[MBN[x],b.lvl[x]]);
   c.sobra=(c.orc||0)-gastoDe(b.lvl);
   c.arows.forEach(r=>{r[3]=vals[r[0]];r[4]=r[3]-r[2];r[5]=r[3];});
   c.b1=notaDe(vals,c.arows);}
  res.push({c,antes,depois:nota(c)});});
 res.sort((a,b)=>(b.depois-b.antes)-(a.depois-a.antes));
 mtRender();
 mtSaida(`<div class=mtres><div class=bhd><span>⚡ Builds otimizadas</span><span class=mini>barras · ímpeto · habilidades</span></div>
 ${res.map(r=>`<div class=mtrl><div style=flex:1><b>${r.c.nome}</b> <span class=mini>${r.c.tipo}</span>
   <div class=mini>${(r.c.sisBar||[]).map(b=>b[0]+" +"+b[1]).join(" · ")||"sem barras"}${r.c.imp?" · ímpeto "+r.c.imp:""}</div></div>
   <span class=mini>${r.antes.toFixed(1)} →</span> <b style="color:${cor(r.depois,0)}">${r.depois.toFixed(1)}</b>
   <b style="color:${r.depois>r.antes?"#22c58b":"#5d6673"};width:52px;text-align:right">${r.depois>r.antes?"+":""}${(r.depois-r.antes).toFixed(1)}</b></div>`).join("")}</div>`);
}

/* ===== MELHOR FUNCAO DE CADA UM · V1 SEGURA =====
   Esta primeira versao nunca usa MODO_ADM, PRO ou localStorage como prova de
   acesso. Ate existir autenticacao + entitlements server-side, o universo
   acessivel e: Basica compativel, build aplicada e builds salvas neste estado.
   A projecao global atual serve somente para devolver um booleano comercial;
   nenhum detalhe bloqueado entra no estado ou no HTML do resultado.

   Adaptador futuro (nao ativo): o backend autenticado devera devolver apenas
   candidatos globais autorizados ao usuario; para usuario comum, a comparacao
   com bloqueadas deve voltar como `has_better_locked`, sem payload da build.
   A fonte paralela da Tarefa 4 nao e consultada por este modulo. */
let MT_MF_ESTADO=null;
const MT_MF_EPS=0.05;

function mtMfEsc(v){return String(v==null?'':v).replace(/&/g,'&amp;').replace(/</g,'&lt;')
 .replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
function mtMfIdCard(k){return String(k||'').split('|')[0].split('@')[0];}
function mtMfFuncChave(k){return String(k||'').split('|').slice(1).join('|')||null;}
function mtMfNomeFunc(f){
 try{if(typeof window.elFuncaoVisivel==='function')return window.elFuncaoVisivel(f)||f||'—';}catch(e){}
 try{return (typeof ROT!=='undefined'&&ROT[f])||f||'—';}catch(e){return f||'—';}
}
function mtMfCanonica(f){
 try{if(typeof window.elFuncaoCanonica==='function')return window.elFuncaoCanonica(mtMfNomeFunc(f));}catch(e){}
 return nz(f||'');
}
function mtMfMesmoFunc(a,b){return !!mtMfCanonica(a)&&mtMfCanonica(a)===mtMfCanonica(b);}
function mtMfEntrada(campo,i,k){
 var L=[];try{L=MT.listEntries&&Array.isArray(MT.listEntries[campo])?MT.listEntries[campo]:[];}catch(e){}
 var e=L[i]&&String(L[i].cardKey||'')===String(k||'')?Object.assign({},L[i]):null;
 return e||{entryId:campo+':'+i,collection:campo,cardId:mtMfIdCard(k),cardKey:k,
  functionId:mtMfFuncChave(k),buildId:'base'};
}
function mtMfOcorrencias(){
 var out=[];
 (MT.slots||[]).forEach((sl,i)=>{if(!sl||!sl.key)return;var c=mtCard(sl.key);
  out.push({id:'titular:'+i,grupo:'titulares',grupoNome:'Titular',ordem:i,key:sl.key,
   cardId:mtMfIdCard(sl.key),c,funcAtual:sl.func||mtMfFuncChave(sl.key),buildId:sl.buildId||'base',
   detalhe:sl.pos||'',sl:Object.assign({},sl),entrada:null});});
 (MT.banco||[]).forEach((k,i)=>{var c=mtCard(k),e=mtMfEntrada('banco',i,k);
  out.push({id:'reserva:'+i,grupo:'reservas',grupoNome:'Reserva',ordem:i,key:k,
   cardId:mtMfIdCard(k),c,funcAtual:e.functionId||mtMfFuncChave(k)||(c&&c.tipo),
   buildId:e.buildId||'base',detalhe:'Banco',sl:null,entrada:e});});
 (MT.elenco||[]).forEach((k,i)=>{var c=mtCard(k),e=mtMfEntrada('fora',i,k);
  out.push({id:'elenco:'+i,grupo:'elenco',grupoNome:'Fora do banco',ordem:i,key:k,
   cardId:mtMfIdCard(k),c,funcAtual:e.functionId||mtMfFuncChave(k)||(c&&c.tipo),
   buildId:e.buildId||'base',detalhe:'Elenco',sl:null,entrada:e});});
 return out;
}
function mtMfSelecionadas(){
 if(!MT_MF_ESTADO)return [];
 return MT_MF_ESTADO.itens.filter(x=>!!MT_MF_ESTADO.selecionadas[x.id]);
}
function mtMfBotaoGrupo(id,rot,qtd){
 var on=MT_MF_ESTADO&&MT_MF_ESTADO.grupo===id;
 return `<button class=mtbt type=button onclick="mtMelhorFuncaoSelecionaGrupo('${id}')"`
  +(qtd?'': ' disabled')+` style="${on?'background:#22c58b!important;color:#061b10!important;':''}${qtd?'':'opacity:.4;'}">${rot} · ${qtd}</button>`;
}
function mtMfDesenhaSelecao(){
 if(!MT_MF_ESTADO)return;
 var E=MT_MF_ESTADO,qt={titulares:0,reservas:0,elenco:0};
 E.itens.forEach(x=>qt[x.grupo]=(qt[x.grupo]||0)+1);
 var escolhidas=mtMfSelecionadas(),lista=E.grupo?E.itens.filter(x=>E.grupo==='todos'||x.grupo===E.grupo):[];
 var checks=lista.length?`<div style="margin-top:12px;max-height:360px;overflow:auto;border:1px solid var(--line);border-radius:10px;padding:4px 11px">
  ${lista.map(x=>`<label style="display:flex;align-items:center;gap:10px;padding:9px 2px;border-bottom:1px solid var(--line2);cursor:pointer">
   <input type=checkbox ${E.selecionadas[x.id]?'checked':''} onchange="mtMelhorFuncaoAlterna('${x.id}',this.checked)">
   <span style="flex:1;min-width:0"><b>${mtMfEsc(x.c&&x.c.nome||('Card '+x.cardId))}</b>
    <span class=mini style="display:block">${mtMfEsc(x.grupoNome)}${x.detalhe?' · '+mtMfEsc(x.detalhe):''} · função atual: ${mtMfEsc(mtMfNomeFunc(x.funcAtual))}</span></span>
  </label>`).join('')}</div>`
  :`<div class=mini style="margin-top:12px">Escolha primeiro Titulares, Reservas ou Elenco inteiro.</div>`;
 var total=escolhidas.length;
 mtSaida(`<div class=mtcx style="max-width:900px;margin-left:auto;margin-right:auto">
  <div class=mtcxt>🎯 MELHOR FUNÇÃO DE CADA UM</div>
  <div style="font-size:13px;line-height:1.55">Escolha um grupo inicial e revise jogador por jogador. Só os marcados entram no cálculo e na futura cobrança.</div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px">
   ${mtMfBotaoGrupo('titulares','Titulares',qt.titulares)}
   ${mtMfBotaoGrupo('reservas','Reservas',qt.reservas)}
   ${mtMfBotaoGrupo('todos','Elenco inteiro',E.itens.length)}
  </div>${checks}
  <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:12px">
   <div style="flex:1;min-width:220px"><b id=mt-mf-contagem>${total} ocorrência${total===1?'':'s'} selecionada${total===1?'':'s'}</b>
    <div class=mini>Modo seguro pré-autenticação · Básica e builds aplicadas/salvas.</div></div>
   <button class=mtbt id=mt-mf-calcular type=button onclick="mtMelhorFuncaoCalcula()"${total?'':' disabled'} style="${total?'':'opacity:.4;'}">CALCULAR SELECIONADOS</button>
  </div>
 </div>`);
}
function mtMelhorFuncaoSelecionaGrupo(grupo){
 if(!MT_MF_ESTADO)return;
 MT_MF_ESTADO.grupo=grupo;MT_MF_ESTADO.selecionadas={};
 MT_MF_ESTADO.itens.forEach(x=>{if(grupo==='todos'||x.grupo===grupo)MT_MF_ESTADO.selecionadas[x.id]=true;});
 mtMfDesenhaSelecao();
}
function mtMelhorFuncaoAlterna(id,on){
 if(!MT_MF_ESTADO)return;MT_MF_ESTADO.selecionadas[id]=!!on;
 var total=mtMfSelecionadas().length,cont=null,bt=null;
 try{cont=document.getElementById('mt-mf-contagem');bt=document.getElementById('mt-mf-calcular');}catch(e){}
 if(cont&&bt){
  cont.textContent=total+' ocorrência'+(total===1?'':'s')+' selecionada'+(total===1?'':'s');
  bt.disabled=!total;bt.style.opacity=total?'':'0.4';return;
 }
 mtMfDesenhaSelecao();
}
function mtMfLinhasCard(idb){
 var unicos={},L=[];
 (D||[]).forEach(c=>{if(!c||c.id==='MOLDE'||mtMfIdCard(c.id)!==String(idb))return;
  var k=mtMfCanonica(c.tipo)||String(c.tipo||'');if(!unicos[k]){unicos[k]=1;L.push(c);}});
 return L;
}
function mtMfAvaliaFoto(idb,func,b,origem){
 if(!func||!b||typeof window.elNotaDaBuild!=='function')return null;
 var catalogo=func;try{if(typeof window.elFuncaoDoCatalogo==='function')catalogo=window.elFuncaoDoCatalogo(idb+'|'+func,func)||func;}catch(e){}
 var alvo=idb+'|'+catalogo,c=null;try{c=mtCard(alvo);}catch(e){}if(!c)return null;
 var n=0;try{n=window.elNotaDaBuild(alvo,b,true)||0;}catch(e){n=0;}
 return isFinite(+n)&&+n>0?{func:func,n:+n,origem:origem}:null;
}
function mtMfPontuacaoAtual(o){
 try{
  if(typeof window.elPontuacao!=='function')return null;
  return o.sl?window.elPontuacao(o.key,o.funcAtual,true,o.sl,null)
   :window.elPontuacao(o.key,o.funcAtual,false,null,o.entrada);
 }catch(e){return null;}
}
function mtMfCandidatosAcessiveis(o){
 var C=[],atual=mtMfPontuacaoAtual(o);
 if(atual&&atual.compativel!==false&&isFinite(+atual.n)&&+atual.n>0)
  C.push({func:atual.func||o.funcAtual,n:+atual.n,origem:'aplicada'});
 mtMfLinhasCard(o.cardId).forEach(c=>{
  var b=null;try{b=window.elBuildBase(o.cardId+'|'+c.tipo);}catch(e){}
  var r=mtMfAvaliaFoto(o.cardId,c.tipo,b,'basica');if(r)C.push(r);
 });
 var salvas=[];try{salvas=MT.builds&&Array.isArray(MT.builds[o.cardId])?MT.builds[o.cardId]:[];}catch(e){}
 salvas.forEach(b=>{var r=mtMfAvaliaFoto(o.cardId,b&&b.func,b,'salva');if(r)C.push(r);});
 C.sort((a,b)=>b.n-a.n);return {atual:atual,candidatos:C};
}
function mtMfTemGlobalSuperior(o,melhorAcessivel){
 /* Somente booleano. Nao retornar nem guardar funcao, nota ou fotografia. */
 var superior=false;
 mtMfLinhasCard(o.cardId).some(c=>{var n=0;try{n=nota(c)||0;}catch(e){}
  if(isFinite(+n)&&+n>melhorAcessivel+MT_MF_EPS){superior=true;return true;}return false;});
 return superior;
}
function mtMfCalculaOcorrencia(o){
 var a=mtMfCandidatosAcessiveis(o),atual=a.atual,top=a.candidatos[0]||null;
 var nAtual=atual&&isFinite(+atual.n)?+atual.n:0;
 if(!top)return {o:o,atual:nAtual,melhor:null,ganho:0,estado:'sem função compatível',globalMelhor:false};
 var ganho=Math.max(0,top.n-nAtual),ja=mtMfMesmoFunc(top.func,(atual&&atual.func)||o.funcAtual)&&ganho<=MT_MF_EPS;
 return {o:o,atual:nAtual,melhor:top,ganho:ganho,
  estado:ja?'já está na melhor função':'melhor função encontrada',
  globalMelhor:mtMfTemGlobalSuperior(o,top.n)};
}
function mtMfDesenhaResultados(resultados){
 var linhas=resultados.map(r=>{var o=r.o,sem=!r.melhor,melhor=sem?'—':mtMfNomeFunc(r.melhor.func);
  var corEstado=sem?'#e0533d':(r.estado==='já está na melhor função'?'#22c58b':'#f0a531');
  return `<div style="padding:12px 0;border-bottom:1px solid var(--line2)">
   <div style="display:flex;align-items:flex-start;gap:10px"><div style="flex:1;min-width:0">
    <b>${mtMfEsc(o.c&&o.c.nome||('Card '+o.cardId))}</b>
    <div class=mini>${mtMfEsc(o.grupoNome)}${o.detalhe?' · '+mtMfEsc(o.detalhe):''}</div>
   </div><b style="color:${r.ganho>MT_MF_EPS?'#f0a531':'#8fa4c4'}">${r.ganho>MT_MF_EPS?'+'+r.ganho.toFixed(1):'—'}</b></div>
   <div style="display:grid;grid-template-columns:repeat(4,minmax(90px,1fr));gap:7px;margin-top:8px;font-size:12px">
    <span>Função atual<br><b>${mtMfEsc(mtMfNomeFunc(o.funcAtual))}</b></span>
    <span>Melhor acessível<br><b>${mtMfEsc(melhor)}</b></span>
    <span>Pontuação atual<br><b>${r.atual>0?r.atual.toFixed(1):'—'}</b></span>
    <span>Pontuação possível<br><b>${r.melhor?r.melhor.n.toFixed(1):'—'}</b></span>
   </div>
   <div style="margin-top:7px;font-size:11.5px;font-weight:800;color:${corEstado}">${mtMfEsc(r.estado)}</div>
   ${r.globalMelhor?'<div style="margin-top:7px;padding:7px 9px;border-radius:7px;background:rgba(240,165,49,.12);border:1px solid rgba(240,165,49,.35);font-size:11.5px;font-weight:800">🔒 Existe uma opção melhor disponível</div>':''}
  </div>`;}).join('');
 mtSaida(`<div class=mtcx style="max-width:900px;margin-left:auto;margin-right:auto">
  <div class=mtcxt>🎯 MELHOR FUNÇÃO DE CADA UM · ${resultados.length} SELECIONADO${resultados.length===1?'':'S'}</div>
  <div class=mini style="margin-bottom:7px">Resultado calculado somente com opções acessíveis nesta sessão. Nenhuma build foi alterada.</div>
  ${linhas}
  <div style="margin-top:12px"><button class=mtbt type=button onclick="mtMfDesenhaSelecao()">REVISAR SELEÇÃO</button></div>
 </div>`);
}
function mtMelhorFuncaoCalcula(){
 var L=mtMfSelecionadas();if(!L.length){mtMfDesenhaSelecao();return;}
 mtMfDesenhaResultados(L.map(mtMfCalculaOcorrencia));
}
function mtMelhorFuncao(){
 if(!window.RouteState||typeof window.RouteState.navigate!=='function')return false;
 return window.RouteState.navigate('melhorfuncao');
}

function mtBuracos(){
 if(!window.RouteState||typeof window.RouteState.navigate!=='function')return false;
 return window.RouteState.navigate('timefraco');
 /* Fluxo legado preservado abaixo apenas como referência histórica. */
 if(!mtPro())return;
 const S1=mtSlots(),us=mtUsados();
 const linhas=S1.map(sl=>{
  const c=mtCard(sl.key),n=c?mtNotaReal(sl.key):0;
  const topo=mtTopo(sl.func,14);
  const ref=topo[0]?topo[0].n:0;
  const pc=c?mtPct(sl.key):0;
  const vi=new Set();
  const sug=topo.filter(t=>{const b=nz(t.c.nome);
   if(us.has(b)||vi.has(b)||t.n<=n+0.3)return false;vi.add(b);return true;}).slice(0,3);
  return {sl,c,n,ref,pc,sug};}).sort((a,b)=>a.pc-b.pc);
 mtSaida(`<div class=mtres><div class=bhd><span>🔍 Onde o time está fraco</span><span class=mini>o % é quanto você já tirou da carta que tem</span></div>
 ${linhas.map(l=>`<div class=mtrl style="align-items:flex-start"><div style=flex:1>
   <b>${l.sl.pos}</b> <span class=mini>${l.sl.func}</span><br>
   <span style="color:${l.c?cor(l.n,0):'#e0533d'}">${l.c?l.c.nome+' '+l.n.toFixed(1):"VAGA VAZIA"}</span>
   <span class=mini>${l.c?` · você tira <b>${Math.round(l.pc)}%</b> dela · no teto ela dá <b>${mtRef(l.sl.key).ideal.toFixed(1)}</b> · melhor da função ${l.ref.toFixed(1)}`:''}</span>
   <div class=mtbar><div style="width:${Math.max(2,Math.min(100,l.pc))}%;background:${l.pc>=92?"#22c58b":l.pc>=80?"#f0a531":"#e0533d"}"></div></div>
   ${l.sug.length?`<div class=mini style="margin-top:4px">quem resolveria: ${l.sug.map(t=>`<span class=ps2 style="cursor:pointer" onclick="abrir('${t.c.id}|${t.c.tipo}')">${t.c.nome} <b>${t.n.toFixed(1)}</b></span>`).join(" ")}</div>`:'<div class=mini style="margin-top:4px;color:#22c58b">nada melhor disponível</div>'}
   </div><b style="color:${l.pc>=92?"#22c58b":l.pc>=80?"#f0a531":"#e0533d"};width:46px;text-align:right">${Math.round(l.pc)}%</b></div>`).join("")}</div>`);
}


/* ---- melhor formação para o elenco ---- */
function mtMelhorFormacao(){
 if(!window.RouteState||typeof window.RouteState.navigate!=='function')return false;
 return window.RouteState.navigate('melhorformacao');
 /* Fluxo legado preservado abaixo apenas como referência histórica. */
 if(!mtPro())return;
 const pool=mtPool();
 if(pool.length<5){alert("Adicione pelo menos 5 jogadores ao elenco/banco/time.");return;}
 const linhas=[];
 const nomes=new Set(pool.map(k=>_jog(k)));
 D.forEach(c=>{if(c.id!=="MOLDE"&&nomes.has(nz(c.nome)))linhas.push({b:nz(c.nome),c,n:nota(c)});});
 const porFunc={};
 linhas.forEach(x=>{(porFunc[x.c.tipo]=porFunc[x.c.tipo]||[]).push(x);});
 Object.values(porFunc).forEach(a=>a.sort((p,q)=>q.n-p.n));

 const monta=form=>{
  const vagas=MT_FORM[form].map((v,i)=>({i,pos:v[0]}));
  const cand=[];
  vagas.forEach(v=>{MT_FUNCS[v.pos].forEach(f=>{(porFunc[f]||[]).forEach(x=>cand.push({v:v.i,pos:v.pos,f,b:x.b,c:x.c,n:x.n}))});});
  cand.sort((a,b)=>b.n-a.n);
  const usados=new Set(),ocup={},esc=[];
  for(const k of cand){if(ocup[k.v]!==undefined||usados.has(k.b))continue;
   ocup[k.v]=k;usados.add(k.b);esc.push(k);
   if(esc.length===vagas.length)break;}
  const soma=esc.reduce((a,x)=>a+x.n,0);
  return {form,esc,ocup,cheias:esc.length,media:esc.length?soma/esc.length:0,soma};};

 const rs=Object.keys(MT_FORM).map(monta).sort((a,b)=>(b.cheias-a.cheias)||(b.soma-a.soma));
 const top=rs[0];
 mtRender();
 mtSaida(`<div class=mtres><div class=bhd><span>🧩 Melhor formação pro seu elenco</span><span class=mini>${pool.length} jogadores no elenco</span></div>
 ${rs.map((r,i)=>`<div class=mtrl><b style="width:66px;color:${i?"#8fa4c4":"#22c58b"}">${r.form}</b>
   <span class=mini style=flex:1>${r.cheias}/11 vagas preenchidas</span>
   <b style="color:${cor(r.media,0)}">${r.media.toFixed(1)}</b>
   <span class=mini style="width:74px;text-align:right">média</span></div>`).join("")}
 <div style="margin-top:10px"><button class=mtbt onclick="mtAplicaFormacao('${top.form}')">✔ escalar assim: ${top.form} (média ${top.media.toFixed(1)})</button></div>
 <div class=bhd style="margin-top:12px"><span>Escalação sugerida · ${top.form}</span></div>
 ${MT_FORM[top.form].map((v,i)=>{const k=top.ocup[i];
   return `<div class=mtrl><b style="width:44px">${v[0]}</b><span class=mini style="width:150px">${k?k.f:"—"}</span>
   <span style=flex:1>${k?k.c.nome:'<span style="color:#e0533d">sem jogador</span>'}</span>
   <b style="color:${k?cor(k.n,0):"#5d6673"}">${k?k.n.toFixed(1):"—"}</b></div>`}).join("")}</div>`);
}
function mtAplicaFormacao(form){
 if(!window.ElencoCardInvariant)return false;
 const auditoria=window.ElencoCardInvariant.audit(MT);
 if(!auditoria.ok){window.ElencoCardInvariant.notify(auditoria.duplicates[0].cardId,true);return false;}
 const pool=mtPool();
 const linhas=[];const ids=new Set(pool.map(k=>String(k).split('|')[0].split('@')[0]));
 const buildPorCard={};
 if(window.ElencoCardInvariant)pool.forEach(k=>{const os=window.ElencoCardInvariant.occurrences(k);if(os.length===1)buildPorCard[String(k).split('|')[0].split('@')[0]]=os[0].buildId||'base';});
 D.forEach(c=>{const id=String(c&&c.id||'').split('@')[0];if(c.id!=="MOLDE"&&ids.has(id))linhas.push({b:id,c,n:nota(c)});});
 const porFunc={};linhas.forEach(x=>{(porFunc[x.c.tipo]=porFunc[x.c.tipo]||[]).push(x);});
 Object.values(porFunc).forEach(a=>a.sort((p,q)=>q.n-p.n));
 const vagas=MT_FORM[form].map((v,i)=>({i,pos:v[0]}));
 const cand=[];vagas.forEach(v=>{MT_FUNCS[v.pos].forEach(f=>{(porFunc[f]||[]).forEach(x=>cand.push({v:v.i,f,b:x.b,c:x.c,n:x.n}));});});
 cand.sort((a,b)=>b.n-a.n);
 const usados=new Set(),ocup={};
 for(const k of cand){if(ocup[k.v]!==undefined||usados.has(k.b))continue;ocup[k.v]=k;usados.add(k.b);}
 MT.form=form;MT.slots=[];mtSlots();
 MT.slots.forEach((sl,i)=>{const k=ocup[i];if(k){sl.func=k.f;sl.key=k.c.id+"|"+k.c.tipo;sl.buildId=buildPorCard[k.b]||'base';}else{sl.key=null;sl.buildId='base';}});
 const tit=new Set(MT.slots.filter(x=>x.key).map(x=>String(x.key).split('|')[0].split('@')[0]));
 const vistos=new Set();
 MT.elenco=(MT.elenco||[]).concat(MT.banco||[]).filter(k=>{const id=String(k).split('|')[0].split('@')[0];if(tit.has(id)||vistos.has(id))return false;vistos.add(id);return true;});
 MT.banco=[];
 try{if(window.elPreservaBuildMovida)MT.elenco.forEach(k=>window.elPreservaBuildMovida('fora',k,buildPorCard[String(k).split('|')[0].split('@')[0]]||'base'));}catch(e){}
 userStateSave();mtRender();
}

/* ---- alternância de aba ---- */
function mtToggle(){
 MT_ON=!MT_ON;
 document.getElementById("mtwrap").style.display=MT_ON?"block":"none";
 document.getElementById("out").style.display=MT_ON?"none":"";
 document.getElementById("mline").style.display=MT_ON?"none":"";
 /* A barra atual substitui os antigos #filtros e #mtbt. Quando eles não
    existem, a entrada no Elenco não pode abortar antes de mtRender(). */
 var _filtros=document.getElementById("filtros"),_mtbt=document.getElementById("mtbt");
 if(_filtros)_filtros.classList.toggle("mtoff",MT_ON);
 if(_mtbt)_mtbt.classList.toggle("on",MT_ON);
 if(MT_ON){
  /* Entrada única do Elenco: nenhum atalho pode herdar faixa, cards ou estado
     do Ranking. A limpeza acontece antes do renderizador nativo do campo. */
  try{
   var _ml=document.getElementById('mline'),_out=document.getElementById('out'),_sp=document.getElementById('rkspacer');
   document.documentElement.classList.remove('t6ranking');
   document.documentElement.classList.add('t6elenco');
   if(_ml){_ml.innerHTML='';_ml.style.display='none';}
   if(_sp)_sp.style.display='none';
   if(_out){_out.innerHTML='';_out.style.display='none';}
  }catch(_limpaErro){}
  /* Entrar no Elenco sempre encerra a rota da ficha. Assim F5 não pode
     reconstruir uma ficha antiga por cima do campo. */
  try{
   var _u=new URL(location.href);
   ['card','funcao','modo'].forEach(function(_p){_u.searchParams.delete(_p);});
   history.replaceState({},'',_u.pathname+_u.search+_u.hash);
   document.documentElement.removeAttribute('data-t6pagina');
   document.body.removeAttribute('data-t6pagina');
   sessionStorage.setItem('t6-rota-atual','elenco');
  }catch(e){}
  mtRender();
 }else{
  try{document.documentElement.classList.remove('t6elenco');}catch(_fechaErro){}
 }
}
userStateLoad();
try{if(window.innerWidth<=820){var _f=document.getElementById('fam');if(_f)_f.classList.add('fechado');
var _b=document.getElementById('navbt');if(_b){_b.textContent='posi\u00e7\u00f5es \u25be';_b.classList.add('on');}}}catch(e){}


/* ===== v168 · PÁGINA INICIAL =====
   O desenho vigente pertence a t6TelaInicio/t6Painel. Este módulo conserva
   somente a visibilidade da área para as rotas que ainda chamam homeToggle. */
let HOME=1;
function homeToggle(v){
 HOME=v===undefined?(HOME?0:1):(v?1:0);
 const w=document.getElementById('homewrap');if(w)w.style.display=HOME?'block':'none';
 ['mline','out','mtwrap'].forEach(id=>{const e=document.getElementById(id);if(e&&HOME)e.style.display='none';else if(e&&id!=='mtwrap')e.style.display='';});
 const b=document.getElementById('homebt');if(b)b.classList.toggle('on',!!HOME);
 if(HOME){
  /* A Home antiga não pode aparecer por um instante antes da vitrine atual.
     Quando a tela nova estiver pronta, ela é a única que desenha. */
  if(!window.T6HOME_FINAL_PRONTA){
   w.innerHTML='';
  }else if(typeof window.t6TelaInicio==='function'){
   w.innerHTML='<div class="t6tela">'+window.t6TelaInicio()+'</div>';
   try{if(typeof window.t6Cliques==='function')window.t6Cliques(w);}catch(e){}
  }else w.innerHTML='';
  window.scrollTo(0,0);
 }}
document.addEventListener('click',e=>{if(HOME&&e.target.closest&&e.target.closest('#filtros .tab,#filtros .fambt,#mtbt'))homeToggle(0);},true);
/* A abertura inicial agora é responsabilidade exclusiva da Home nova, no
   fim do arquivo. O listener antigo chamava a rota estática junto dela. */

/* v169 · a barra começa exatamente onde o header termina */
function _hh(){const h=document.querySelector('header');if(!h)return;
 document.documentElement.style.setProperty('--hh',h.offsetHeight+'px');}
window.addEventListener('resize',_hh);
window.addEventListener('DOMContentLoaded',()=>{_hh();setTimeout(_hh,120);});
document.addEventListener('click',()=>setTimeout(_hh,60),true);


/* bloco JavaScript 10 */

(function(){
 const T=[["claro","Claro"],["escuro","Escuro"]];
 const salvo=(function(){try{return localStorage.getItem("encaixe_tema")}catch(e){return null}})();
 document.documentElement.dataset.tema=salvo&&T.some(t=>t[0]===salvo)?salvo:"escuro";
 function aplica(v){document.documentElement.dataset.tema=v;try{localStorage.setItem("encaixe_tema",v)}catch(e){}
  if(typeof render==="function")render();}
 window.addEventListener("DOMContentLoaded",function(){
  const h=document.getElementById("subtxt");if(!h)return;
  const b=document.createElement("button");b.id="temabt";b.className="fbt";b.style.display="inline-block";
  const rot=v=>"◐ "+(T.find(t=>t[0]===v)||T[0])[1];
  b.textContent=rot(document.documentElement.dataset.tema);
  b.onclick=function(){const a=document.documentElement.dataset.tema;const i=T.findIndex(t=>t[0]===a);
   const n=T[(i+1)%T.length][0];aplica(n);b.textContent=rot(n);};
  h.appendChild(b);
 });
})();


/* bloco JavaScript 11 */

/* ================= A NOTA É O PERCENTUAL DE CUMPRIMENTO — 06/08/2026 =================
   Ordem do Luis: "colocar o que está sobrando ou faltando como percentual, acima ou abaixo
   de cem, e considerar o molde como cem. Ela própria pode ser o ranking."

       nota = Σ(peso × valor do card) ÷ Σ(peso × alvo do molde) × 100

   100  = o card entrega EXATAMENTE o que o molde da função pede
   107  = entrega 7% a mais        ·        92 = entrega 8% a menos

   ⛔ SEM ARREDONDAR NADA por dentro. Quem arredonda é a tela.
   ⛔ SEM PISO e SEM TETO — a conta é proporção pura, não precisa de nenhum dos dois.
   ⛔ SEM K — não existe número escolhido nesta régua. Nada foi inventado.
   ⛔ SEM POPULAÇÃO — card novo entra e não move a nota de ninguém.
   ⛔ Os bônus de corpo e de IA ficam FORA do ranking (botão religa só para comparar).

   O motor continua intacto e continua escolhendo pela régua com degraus: os degraus servem
   para ESCOLHER (impedir que ele empilhe tudo no peso 12), não para MEDIR o card pronto. */
let ACH_BONUS=1;
PISO_ON=0;
function achPct(c){
 if(!c||!c.arows) return null;
 if(c._cp!==undefined) return c._cp;
 let num=0,den=0;
 for(const r of c.arows){const w=r[1]; if(!w) continue; num+=w*r[3]; den+=w*r[2];}
 return c._cp = den? 100*num/den : null;
}
traducaoViva=function(){
 for(const t of [...new Set(D.map(c=>c.tipo))]){
  const cs=D.filter(c=>c.tipo===t&&c.id!=="MOLDE");
  D.filter(c=>c.tipo===t).forEach(c=>{const v=achPct(c); c.b1n = (v===null?0:v);});
  if(MED[t]&&cs.length){const ev=cs.filter(c=>c.orc);const fonte=(ev.length>=5?ev:cs);
   const w=fonte.map(c=>c.b1n).sort((a,b)=>a-b);
   MED[t].b1n=w[Math.floor(w.length/2)];
   MED[t].nEvolui=ev.length;MED[t].nTotal=cs.length;}
 }
};
const _fis=fisBonus,_ia=iaBonus,_pr=prBonus;
prBonus=function(c){return ACH_BONUS?_pr(c):0;};
fisBonus=function(c){return ACH_BONUS?_fis(c):0;};
iaBonus =function(c){return ACH_BONUS?_ia(c):0;};
function _achGo(){for(const c of D){delete c._n;c._fb=undefined;c._ia=undefined;c._pr=undefined;c._cp=undefined;}
 traducaoViva(); if(typeof render==='function')render();
 if(window._achPinta)setTimeout(window._achPinta,80);}
/* o bruto continua na tela, ao lado, como referência do que o motor pagou */
(function(){
 const RX=/^\s*bruto\s+(-?[\d.,]+)/;
 const idx=new Map();
 let tt=null,mo=null,montado=false,aguardaDom=false;
 function mapa(){ idx.clear();
  for(const c of D){ if(c.id==='MOLDE') continue;
   const k=(c.b1||0).toFixed(1); if(!idx.has(k)) idx.set(k,c); } }
 function pinta(){
  if(!idx.size) mapa();
  const raiz=document.getElementById('box'); if(!raiz) return;
  for(const el of raiz.querySelectorAll('span,div')){
   if(el.dataset && el.dataset.enc) continue;
   if(el.children.length) continue;
   const t=el.textContent||''; const m=RX.exec(t); if(!m) continue;
   const c=idx.get(parseFloat(m[1].replace(',','.')).toFixed(1)); if(!c) continue;
   const v=achPct(c); if(v===null) continue;
   el.dataset.enc='1';
   const d=v-100, cor=d>=0?'#22c58b':'#e0533d';
   el.innerHTML=t;
  }
 }
 window._achPinta=pinta;
 function aoMutar(){if(tt!==null)clearTimeout(tt);tt=setTimeout(function(){tt=null;pinta();},60);}
 function aoDom(){aguardaDom=false;mount();}
 function mount(){
  if(montado){pinta();return true;}
  const raiz=document.getElementById('box');
  if(!raiz){
   if(document.readyState==='loading'&&!aguardaDom){
    aguardaDom=true;document.addEventListener('DOMContentLoaded',aoDom);
   }
   return false;
  }
  if(!mo)mo=new MutationObserver(aoMutar);
  mo.observe(raiz,{childList:true,subtree:true});montado=true;pinta();return true;
 }
 function dispose(){
  if(aguardaDom){document.removeEventListener('DOMContentLoaded',aoDom);aguardaDom=false;}
  if(tt!==null){clearTimeout(tt);tt=null;}
  if(mo)mo.disconnect();montado=false;return true;
 }
 window.T6AchPintaLifecycle=Object.freeze({mount:mount,dispose:dispose,refresh:pinta,
  inspect:function(){return{mounted:montado,pending:tt!==null,waitingDom:aguardaDom};}});
 mount();
})();
(function(){
 const b=document.createElement('button');
 b.style.cssText='position:fixed;right:14px;bottom:52px;z-index:9999;padding:6px 11px;border-radius:8px;border:1px solid #17402f;background:#17402f;color:#fff;font:600 11.5px system-ui;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.25)';
 const rot=()=>b.textContent='nota = % do molde'+(ACH_BONUS?'  + bônus':'');
 rot(); b.title='100 = o card entrega exatamente o que a função pede. Clique para ligar/desligar os bônus de corpo e IA.';
 b.onclick=function(){ACH_BONUS=ACH_BONUS?0:1;rot();
  b.style.background=b.style.borderColor=ACH_BONUS?'#8a5a00':'#17402f';_achGo();};
 document.body.appendChild(b);
 const pb=document.getElementById('pisobt');
 if(pb){pb.textContent='escala: 100 = o molde';pb.onclick=null;pb.style.opacity=.7;}
 const h=document.querySelector('.sub');
 if(h)h.textContent=(h.textContent||'')+' · NOTA = % DE CUMPRIMENTO DO MOLDE · 100 = o molde';
 _achGo();
})();

/* A busca global vigente pertence a paginas-e-navegacao.js. A busca antiga
   gbBt/gbWrap foi removida na origem para não exigir remoção corretiva. */



/* bloco JavaScript 12 */

(function(){
 var botao=null,espera=null,montado=false,tentativas=0;
 var MAX_TENTATIVAS=20,T=["\u2b21 condicional +1","\u2b21 condicional +2","\u2b21 condicional +3"];
 function cancelaEspera(){if(espera!==null){clearTimeout(espera);espera=null;}}
 function pinta(){
  if(!botao)return false;
  var m=(typeof CMODE!=="undefined")?(CMODE||0):0;
  botao.textContent=T[m]||T[0];
  botao.style.background=m?"#f0a531":"transparent";
  botao.style.color=m?"#0e1116":"#f0a531";
  return true;
 }
 function aoClicar(){try{toggleCond();}catch(e){}pinta();}
 function tentaMontar(){
  cancelaEspera();
  if(!montado)return false;
  var existente=document.getElementById("condflut");
  if(existente){botao=existente;return pinta();}
  var alvo=document.getElementById("fbt");
  if(!alvo){
   if(tentativas++<MAX_TENTATIVAS)espera=setTimeout(tentaMontar,200);
   return false;
  }
  var b=document.createElement("button");b.id="condflut";b.dataset.t6Owner="bloco12";
  b.className=alvo.className;
  b.style.cssText="display:inline-block;margin-left:8px;border-color:#f0a531;color:#f0a531;font-weight:700";
  b.title="troca TODOS os impetos condicionais e reordena o ranking";
  b.addEventListener("click",aoClicar);
  alvo.parentNode.insertBefore(b,alvo.nextSibling);botao=b;return pinta();
 }
 function mount(){
  if(montado)return tentaMontar();
  montado=true;tentativas=0;return tentaMontar();
 }
 function refresh(){return montado?tentaMontar():false;}
 function dispose(){
  montado=false;cancelaEspera();tentativas=0;
  if(botao&&botao.dataset&&botao.dataset.t6Owner==="bloco12"){
   botao.removeEventListener("click",aoClicar);
   if(botao.parentNode)botao.parentNode.removeChild(botao);
  }
  botao=null;return true;
 }
 window.T6Bloco12=Object.freeze({mount:mount,refresh:refresh,dispose:dispose,
  inspect:function(){return{mounted:montado,pending:espera!==null,attempts:tentativas,hasButton:!!botao};}});
 mount();
})();


/* bloco JavaScript 13 */

(function(){
 var ORIG=null;
 function guarda(){
  if(ORIG) return;
  ORIG=D.map(function(c){
   return {b1:c.b1,b1n:c.b1n,v:c.arows.map(function(r){return r[3];}),
           bar:c.sisBar,TEC:c.TEC,TECB:c.TECB,HAB:c.HAB,adds:c.adds,sobra:c.sobra};
  });
 }
 function aplica(m){
  guarda();
  var g=String(m+1),i,a,c,o,f;
  for(i=0;i<D.length;i++){
   c=D[i]; o=ORIG[i]; if(!o) continue;
   f=(m>0 && c.CD && c.CD[g]) ? c.CD[g] : null;
   c.b1   = f? f.b1   : o.b1;
   c.b1n  = f? f.b1n  : o.b1n;
   c.sisBar = f? f.bar : o.bar;
   c.TEC  = f? f.TEC  : o.TEC;
   c.TECB = f? f.TECB : o.TECB;
   c.HAB  = f? f.HAB  : o.HAB;
   c.adds = f? f.HAB  : o.adds;
   c.sobra= f? f.sobra: o.sobra;
   delete c._n;
   var vv = f? f.v : o.v;
   if(c.arows && vv){
    for(a=0;a<c.arows.length;a++){
     if(vv[a]===undefined) continue;
     c.arows[a][3]=vv[a];
     c.arows[a][4]=Math.round((vv[a]-c.arows[a][2])*100)/100;
    }
   }
  }
 }
 function pinta(){
  var b=document.getElementById("condbt");
  if(b && typeof CTXT!=="undefined"){
   b.textContent=CTXT[CMODE];
   b.style.background=CMODE?"#f0a531":"#1a1206";
   b.style.color=CMODE?"#0e1116":"#f0a531";
  }
 }
 window.toggleCond=function(){
  CMODE=(CMODE+1)%3;
  aplica(CMODE);
  try{ traducaoViva(); }catch(e){}
  pinta();
  try{ render(); }catch(e){}
 };
 window.condQuantas=function(){
  var n=0; for(var i=0;i<D.length;i++){ if(D[i].CD && D[i].CD["2"]) n++; }
  return n;
 };
})();


/* bloco JavaScript 14 */

/* Catálogo antigo de Boxes mantido apenas como evidência inativa nesta etapa.
   A interface canônica usa exclusivamente carta_jogo.box via read-model. */
if(false){
const BOXDT={"Welcome Login Bonus 2027": "2026-08-13", "Skill Up 2027": "2026-08-13", "New Season Campaign 2027": "2026-08-13", "Chelsea B Selection 14 Aug '26": "2026-08-13", "Summer Transfer 17 Aug '26": "2026-08-13", "Daily Bonus 2027": "2026-08-13", "Leo Messi Edition 2027": "2026-08-13", "Lamine Yamal Edition 2027": "2026-08-13", "Tactical Defence 13 Aug '26": "2026-08-13", "Starter Set 2027": "2026-08-13", "English League Selection 13 Aug '26": "2026-08-13", "eFootball™ League 2027 Rewards Phase 1": "2026-08-13", "Advertisement Reward 2027": "2026-08-13", "Step-up 2027": "2026-08-13", "Summer Transfer 13 Aug '26": "2026-08-13", "CAF Africa Cup of Nations Selection 13 Aug '26": "2026-08-13", "Manager Pack 13 Aug '26": "2026-08-13", "Moroccan League Selection 13 Aug '26": "2026-08-13"};
const BOXATIVA=["Summer Transfer 17 Aug '26", "Chelsea B Selection 14 Aug '26", "Lamine Yamal Edition 2027", "Leo Messi Edition 2027", "Daily Bonus 2027", "Advertisement Reward 2027", "eFootball™ League 2027 Rewards Phase 1", "CAF Africa Cup of Nations Selection 13 Aug '26", "Tactical Defence 13 Aug '26", "Summer Transfer 13 Aug '26", "English League Selection 13 Aug '26", "New Season Campaign 2027", "Moroccan League Selection 13 Aug '26", "Welcome Login Bonus 2027", "Step-up 2027", "Manager Pack 13 Aug '26", "Starter Set 2027", "Skill Up 2027"];
const BOXHIST={"Encored AC Milan": {"visto": "2026-08-10", "ids": ["88036360648832", "88039044943837", "88039045074401", "88039045074410", "88039045077725", "89136140651034"]}, "Pressure-Proof 2026": {"visto": "2026-08-18", "ids": ["105884634166456", "105884634176665", "105884634185427", "105884634188207", "105884634194916", "105884634196567", "105884634201900", "105884634233598", "106788724799833", "106788724836718", "89138556700485"]}, "Victory Drivers 2026": {"visto": "2026-08-18", "ids": ["105855106300661", "105855106307448", "105855106307706", "105855106313816", "105855106313897", "105855106317534", "105855106319035", "105855106324436", "106788456363289", "106788456409199", "89138556678270"]}, "Living Legends 2026": {"visto": "2026-08-18", "ids": ["105859401156605", "105859401160231", "105859401162517", "105859401163965", "105859401165777", "105859401166632", "105859401178925", "105859401239571", "105859485069597", "105859485110629", "106788187832737", "106788187833650", "106788187839904", "106788187841133", "106788187843931", "89138556572074", "89138556575063"]}, "Legends Assemble": {"visto": "2026-08-15", "ids": ["88039581811496", "88040387119176", "88040387163000", "88040387251634", "88040387251674", "88040387251729", "88041460993512", "88044145213492", "88044145351389", "88044682118054", "88045218959416"]}, "Treasure Link": {"visto": "2026-08-15", "ids": ["88029649833482", "88029918268857", "88030991881014", "88031797317097", "88044145214260"]}, "National Team Icons vol.3": {"visto": "2026-08-18", "ids": ["105835241963937", "105835241972925", "105835242034156", "105835242039414", "105835242041536", "105835242048365", "105835242060713", "105835292374467"]}, "eFootball™ League Rewards Phase 13": {"visto": "2026-08-18", "ids": ["106771813384691"]}, "Thailand Selection 27 Jul '26": {"visto": "2026-08-18", "ids": ["105854300973679", "105854300977016", "105854300981393", "88045219096844"]}, "Club Pack Club América Aug '22": {"visto": "2026-07-09", "ids": ["105553921606966"]}, "National Team Selection Italy [Deluxe] Nov '22": {"visto": "2026-07-09", "ids": ["105561169438272", "105561169438455", "105561169444838"]}, "Alltime Greats Nov '22": {"visto": "2026-07-09", "ids": ["105561706239656", "105561706240865", "105561706241802"]}, "National Team Pack Germany '22": {"visto": "2026-07-09", "ids": ["105563853717921"]}, "Derby Day Manchester 14 Jan '23": {"visto": "2026-07-09", "ids": ["105568685563515"]}, "Club Selection FC Barcelona 22 May '23": {"visto": "2026-07-09", "ids": ["105580765180136"]}, "Breakout Stars 6 Jul '23": {"visto": "2026-07-09", "ids": ["105586670755629", "105586670813575", "105586670814750"]}, "Back in the Game 3 Aug '23": {"visto": "2026-07-09", "ids": ["105590160392609", "105590160400490", "105590160400550", "105590160485839"]}, "Leo Messi Edition '23": {"visto": "2026-07-09", "ids": ["105621835804904", "105621835876389"]}, "Startup Campaign 7 Sep '23": {"visto": "2026-07-09", "ids": ["105622909546728", "105627741438140", "105628009878609", "105628009888681", "105628009896720"]}, "Spanish League Selection Guardians 27 Nov '23": {"visto": "2026-07-09", "ids": ["105638478848461"]}, "FC Bayern München Selection 15 Jan '24": {"visto": "2026-07-09", "ids": ["105648142451105"]}, "Spanish League Selection Guardians 25 Mar '24": {"visto": "2026-07-09", "ids": ["105659953622088", "105659953691509"]}, "The All-Rounders 11 Apr '24": {"visto": "2026-07-09", "ids": ["105661027358435"]}, "Magical Dribbler 12 Sep '24": {"visto": "2026-07-09", "ids": ["105705050796264", "105705050869659"]}, "Spanish League Selection 19 Sep '24": {"visto": "2026-07-09", "ids": ["105706124602831", "105706124609573", "105706124621334"]}, "Captain Tsubasa Collaboration Campaign 5 Dec '24": {"visto": "2026-08-18", "ids": ["105722230611287", "105722230638657", "105722499161096", "105723035943329", "105723036019149", "105723036026799"]}, "Mid-season MVPs 9 Jan '25": {"visto": "2026-08-18", "ids": ["105727867788923", "105727867862312", "105727867863450", "105727867875270", "105727867875421", "105727867881509", "105727867886508", "105727867901819"]}, "Spanish League Selection 6 Mar '25": {"visto": "2026-08-18", "ids": ["105745047661640", "105745047681033", "105745047725477", "105745047731917", "105745047734583", "105745047742532", "105745047744696", "105745047747738", "105745047750510", "105745047765545", "105745047783232"]}, "National Teams Selection European 22 May '25": {"visto": "2026-08-18", "ids": ["105757664130847", "105757664143769", "105757664192037", "105757664198776", "105757664207689", "105757664207713", "105757664212756", "105757664214492", "105757664216160", "105757664216492", "105757664216724"]}, "Italian League Selection 18 Sep '25": {"visto": "2026-08-18", "ids": ["105783165492224", "105783165492859", "105783165493354", "105783165495382", "105783165511769", "105783165562137", "105783165566926", "105783165571441", "105783165584350", "105783165604082", "105783165617181"]}, "Liverpool R Selection 23 Mar '26": {"visto": "2026-08-18", "ids": ["105799271624488", "105799271706717", "105799271717572", "105799271719327", "105799271724566", "105799271726109", "105799271726298", "105799271742270"]}, "Winter Transfer 23 Feb '26": {"visto": "2026-08-18", "ids": ["105799540062891", "105799540076776", "105799540125703", "105799540132883", "105799540139370", "105799540146832", "105799540147260", "105799540157315"]}, "Manchester B Selection 26 Jan '26": {"visto": "2026-08-18", "ids": ["105799808558839", "105799808562360", "105799808568834", "105799808584103", "105799808584213", "105799808588551", "105799808597794", "105799808602683"]}, "National Team Selection Worldwide 30 Apr '26": {"visto": "2026-08-18", "ids": ["105800613796930", "105800613868997", "105800613871552", "105800613872994", "105800613877367", "105800613879388", "105800613884444", "105800613893026", "105800613898989", "105800613901030", "105800613910395"]}, "Spanish League Selection 2 Apr '26": {"visto": "2026-08-18", "ids": ["105801687534628", "105801687599561", "105801687606426", "105801687618534", "105801687636935", "105801687639335", "105801687639688", "105801687639790", "105801687641013", "105801687650950", "105801687651660"]}, "English League Selection 5 Feb '26": {"visto": "2026-08-18", "ids": ["105802224470740", "105802224484472", "105802224484918", "105802224487760", "105802224492889", "105802224496079", "105802224507828", "105802224509715", "105802224510604", "105802224521791", "105802224527648"]}, "European Clubs Selection 13 Nov '25": {"visto": "2026-08-18", "ids": ["105803029714659", "105803029779174", "105803029789370", "105803029798570", "105803029802332", "105803029803070", "105803029822915", "105803029823369", "105803029827845", "105803029829169", "105803029835352"]}, "Borussia Dortmund Pack 25-26": {"visto": "2026-08-18", "ids": ["105804640335593", "105804640349696", "105804640391008", "105804640391294", "105804640416385", "105804640427210", "105804640430829", "105804640430831", "105804640431004", "105804640431005", "105804640433206"]}, "FC Barcelona Pack 25-26": {"visto": "2026-08-18", "ids": ["105805714139254", "105805714141230", "105805714141236", "105805714141376", "105805714141494", "105805714163136", "105805714163749", "105805714171630", "105805714177825", "105805714192706", "105805714196288"]}, "European Clubs Selection Guardians 9 Feb '26": {"visto": "2026-08-18", "ids": ["105826652105091", "105826652106157", "105826652114181", "105826652118866", "105826652119880", "105826652128984", "105826652141078", "105826652154737"]}, "Elite Lineage 30 Apr '26": {"visto": "2026-08-18", "ids": ["105829336458789", "105829336468960", "105829336478106", "105829336491941", "105829336503648", "105829336508397", "105829336515385", "105829353237311"]}, "National Team Selection Morocco Jun '26": {"visto": "2026-08-18", "ids": ["105851968872237", "105851968918079", "105851968929064", "105851968929670", "105851968934993", "105851968938280", "105851968940938", "105851968956572", "105851968962348", "105851968964074", "105851968968056"]}, "National Team Selection Senegal Jun '26": {"visto": "2026-08-18", "ids": ["105860290356815", "105860290371544", "105860290416997", "105860290422217", "105860290427681", "105860290430931", "105860290435572", "105860290455110", "105860290457086", "105860290475507", "105860290487884"]}, "Show Time Ligue 1 Uber Eats 23-24": {"visto": "2026-07-09", "ids": ["106727789930231", "106727789932670", "106727789935290"]}, "Standout Lefties 3 Feb '25": {"visto": "2026-08-18", "ids": ["105748000511970", "105748000515791", "105748000519038", "105748000523818", "105748000526283", "105748000540516", "105748000550288", "105748000554572", "106738795720031", "106738795813804", "106738795814310"]}, "GK Directing Defence 29 May '25": {"visto": "2026-08-18", "ids": ["106740406335670", "106740406401980", "106740406415422", "106740456734704"]}, "FC Bayern München Selection 15 May '25": {"visto": "2026-08-18", "ids": ["105758201002311", "105758201015326", "105758201063882", "105758201064420", "105758201072646", "105758201084841", "105758201085087", "105758201117043", "106741480063393", "106741480139213", "106741480168208"]}, "Italian League 24-25 Season's Best": {"visto": "2026-08-18", "ids": ["105766254059131", "105766254063916", "105766254126509", "105766254129159", "105766254129812", "105766254133736", "105766254149247", "105766254151524", "106744164492837", "106744164503008"]}, "Brazilian League Selection 26 Jun '25": {"visto": "2026-08-18", "ids": ["105766790997250", "105766791000942", "105766791020542", "105766791023955", "105766791026405", "105766791033680", "105766791042129", "105766791052172", "106744432885358", "106744432941483", "106744432947286", "106744432971741"]}, "Trusted Shields 22 Sep '25": {"visto": "2026-08-18", "ids": ["105783970803800", "105783970818142", "105783970867583", "105783970877003", "105783970877313", "105783970885873", "105783970886253", "105783970913545", "106750338463730", "106750338532448", "106750338536440"]}, "National Team Selection Indonesia 2 Oct '25": {"visto": "2026-08-18", "ids": ["106758173423636", "106758173464832", "106758173516441", "106758173527305"]}, "Anticipated Standouts 13 Oct '25": {"visto": "2026-08-18", "ids": ["105806250946031", "105806251027853", "105806251028182", "105806251032533", "105806251039829", "105806251046082", "105806251048967", "105806251053627", "106759196878583", "106759196885383", "106759196889835"]}, "Japanese Stars 10 Nov '25": {"visto": "2026-08-18", "ids": ["105815377822667", "105815377832342", "105815377833867", "105815377833869", "105815377833973", "105815377834748", "105815377847809", "105815377859180", "106762418117636", "106762418128755", "106762418131391"]}, "Towering Giants 29 Dec '25": {"visto": "2026-08-18", "ids": ["105819135906943", "105819135913695", "105819135917598", "105819135925663", "105819135931009", "105819135933749", "105819135938679", "105819135947688", "106763491781983", "106763491864289", "106763491879812"]}, "Best Players of CAF AFRICA CUP OF NATIONS 25": {"visto": "2026-08-18", "ids": ["105822440974750", "105822440976669", "105822441022657", "105822441037263", "105822441058657", "105822441068411", "105822441072621", "105822441082750", "106764917858093", "106764917911559", "106764917945800"]}, "eFootball™ League Rewards Phase 7": {"visto": "2026-08-18", "ids": ["106768860487291"]}, "Trendyol Süper Lig Monthly MVPs Feb '26": {"visto": "2026-08-18", "ids": ["105832289200445", "105832289261742", "105832289269722", "105832289278364", "105832289286705", "105832289287907", "105832289295702", "106771008035172", "106771008054113", "106771008057263", "106771008066245"]}, "J.LEAGUE Monthly MVPs Apr '26": {"visto": "2026-08-18", "ids": ["105843831980149", "105843831987163", "105843832018243", "105843832031923", "106775839900908", "106775839936861", "106775839943506", "106775839950376"]}, "Standout Guardians 25-26 Season's Best": {"visto": "2026-08-18", "ids": ["105837926385942", "105837926394004", "105837926394281", "105837926400192", "105837926405008", "105837926433018", "105837926442563", "105837926463063", "106776645183223", "106776645188904"]}, "Spanish League 25-26 Season's Best": {"visto": "2026-08-18", "ids": ["105846784698228", "105846784755556", "105846784763076", "105846784763261", "105846784767375", "105846784783510", "105846784799975", "105846784808268", "106777987362942", "106777987393262"]}, "European Club Championship 25-26 Season's Best": {"visto": "2026-08-18", "ids": ["105847321586510", "105847321630498", "105847321641389", "105847321641526", "105847321651674", "105847321652945", "105847321659866", "105847321668510", "106778524224656", "106778524258203"]}, "Japan Selection 11 Jul '26": {"visto": "2026-08-18", "ids": ["105855643147250", "105855643149509", "105855643149532", "105855643153148", "105855643160674", "105855643168283", "105855643177615", "105855643182804", "106783356022615", "106783356067329", "106783356083208", "106783356085451", "106783356088205", "106783356096959"]}, "The Football Festival Campaign 2026": {"visto": "2026-07-09", "ids": ["105852690280748", "105852690346465", "105852690382682", "105852958832396", "106757854755138", "106779866307927", "106780403293192", "106785503488127", "106785503491871", "106785503555830", "106785503556272", "106785503587053"]}, "Spain 2026": {"visto": "2026-08-18", "ids": ["105854569331106", "105854569387197", "105854569391823", "105854569403412", "105854569418342", "105854569449280", "106787651035597", "106787651039542", "106787651045215", "106787651045391", "106787651090754"]}, "POTW International Cup 22 Dec '22": {"visto": "2026-07-09", "ids": ["52781658441010", "52781658444018", "52781658453914", "52781658507988", "52781658517630"]}, "POTW 25 May '23": {"visto": "2026-07-09", "ids": ["52786758721147"]}, "POTW National Teams 14 Sep '23": {"visto": "2026-07-09", "ids": ["52845546085217", "52845546085792"]}, "POTW 12 Oct '23": {"visto": "2026-07-09", "ids": ["52846888261347"]}, "POTW European Club Championship 12 Oct '23": {"visto": "2026-07-09", "ids": ["52847156719353", "52847156719848", "52847156775223"]}, "POTW European Club Championship 2 Nov '23": {"visto": "2026-07-09", "ids": ["52848498943735", "52848498973456"]}, "POTW 18 Jan '24": {"visto": "2026-07-09", "ids": ["52851988540763", "52851988604663", "52851988613431", "52851988616262", "52851988649521"]}, "POTW European Club Championship 25 Apr '24": {"visto": "2026-07-09", "ids": ["52869705269665", "52869705350391", "52869705368672"]}, "POTW 2 May '24": {"visto": "2026-07-09", "ids": ["52869973708663", "52869973711938", "52869973799480"]}, "POTW 30 May '24": {"visto": "2026-07-09", "ids": ["52871047450530", "52871047474272", "52871047475432"]}, "POTW National Teams 20 Jun '24": {"visto": "2026-07-09", "ids": ["52871315893320", "52871315950550", "52871315987216"]}, "POTW National Teams 4 Jul '24": {"visto": "2026-07-09", "ids": ["52871852828785", "52871852830912", "52871852847166", "52871852853061", "52871852862389"]}, "POTW European Club Championship 14 Nov '24": {"visto": "2026-08-18", "ids": ["52876953037896", "52876953104442", "52876953104576", "52876953107036", "52876953111864", "52876953112945", "52876953113699", "52876953116252", "52876953120710", "52876953128660", "52876953131558"]}, "POTW 28 Nov '24": {"visto": "2026-08-18", "ids": ["52877489905275", "52877489924772", "52877489925084", "52877489978615", "52877489978740", "52877489992248", "52877489992985", "52877489998454", "52877490008548", "52877490012876", "52877490021910"]}, "POTW European Club Championship 5 Dec '24": {"visto": "2026-08-18", "ids": ["52878026768801", "52878026772722", "52878026776491", "52878026838624", "52878026846823", "52878026848682", "52878026852159", "52878026857317", "52878026869086", "52878026873799", "52878026895125"]}, "POTW 30 Jan '25": {"visto": "2026-08-18", "ids": ["52880174266079", "52880174327921", "52880174328269", "52880174329982", "52880174333374", "52880174337435", "52880174352942", "52880174357656", "52880174362977", "52880174367436", "52880174380812"]}, "POTW 13 Feb '25": {"visto": "2026-08-18", "ids": ["52881247999655", "52881248005192", "52881248006378", "52881248065798", "52881248079832", "52881248080899", "52881248089808", "52881248094140", "52881248094741", "52881248109097", "52881248123251"]}, "POTW National Teams 27 Mar '25": {"visto": "2026-08-18", "ids": ["52882858634271", "52882858682829", "52882858684420", "52882858688448", "52882858700173", "52882858700497", "52882858703193", "52882858710824", "52882858715706", "52882858716060", "52882858720048"]}, "POTW European Club Championship 13 Mar '25": {"visto": "2026-08-18", "ids": ["52884737662953", "52884737666692", "52884737669303", "52884737722416", "52884737729905", "52884737730975", "52884737740993", "52884737749130", "52884737754171", "52884737754772", "52884737766665"]}, "POTW European Club Championship 20 Mar '25": {"visto": "2026-08-18", "ids": ["52885006097408", "52885006098197", "52885006102740", "52885006165541", "52885006165751", "52885006187433", "52885006189200", "52885006189858", "52885006209930", "52885006219586", "52885006222001"]}, "POTW 15 May '25": {"visto": "2026-08-18", "ids": ["52885811404554", "52885811464916", "52885811474484", "52885811474558", "52885811474678", "52885811475014", "52885811478746", "52885811482011", "52885811486568", "52885811498634", "52885811504380"]}, "POTW 28 Aug '25": {"visto": "2026-08-18", "ids": ["52888227321571", "52888227323267", "52888227330230", "52888227392484", "52888227393662", "52888227397606", "52888227410013", "52888227410731", "52888227415099", "52888227416101", "52888227425571"]}, "POTW National Teams 20 Nov '25": {"visto": "2026-08-18", "ids": ["52891448555703", "52891448626690", "52891448637204", "52891448638618", "52891448639187", "52891448640608", "52891448641040", "52891448641959", "52891448649356", "52891448650628", "52891448667736"]}, "POTW 27 Nov '25": {"visto": "2026-08-18", "ids": ["52891716988895", "52891717004319", "52891717047292", "52891717054551", "52891717058306", "52891717058727", "52891717058778", "52891717060623", "52891717070797", "52891717095666", "52891717098089"]}, "POTW 25 Dec '25": {"visto": "2026-08-18", "ids": ["52892790726778", "52892790799712", "52892790800320", "52892790800359", "52892790801832", "52892790803970", "52892790818629", "52892790823620", "52892790826734", "52892790828459", "52892790843639"]}, "POTW European Club Championship 18 Dec '25": {"visto": "2026-08-18", "ids": ["52894401343272", "52894401405389", "52894401409216", "52894401409270", "52894401416045", "52894401424732", "52894401430950", "52894401431902", "52894401433471", "52894401461438", "52894401467324"]}, "POTW European Club Championship 5 Feb '26": {"visto": "2026-08-18", "ids": ["52894938274024", "52894938278468", "52894938279982", "52894938283850", "52894938285887", "52894938292576", "52894938297131", "52894938298132", "52894938304212", "52894938313655", "52894938327972"]}, "POTW European Club Championship 19 Mar '26": {"visto": "2026-08-18", "ids": ["52895743518028", "52895743520095", "52895743523498", "52895743535509", "52895743589623", "52895743595540", "52895743602336", "52895743604432", "52895743616652", "52895743617950", "52895743641408"]}, "POTW 29 Jan '26": {"visto": "2026-08-18", "ids": ["52897354189524", "52897354196134", "52897354196397", "52897354207979", "52897354230359", "52897354230536", "52897354235364", "52897354245920", "52897354247016", "52897354250562", "52897354255615"]}, "POTW 5 Feb '26": {"visto": "2026-08-18", "ids": ["52897622566573", "52897622571278", "52897622626144", "52897622638497", "52897622638879", "52897622642517", "52897622651925", "52897622652185", "52897622656660", "52897622657203", "52897622667074"]}, "POTW 26 Feb '26": {"visto": "2026-08-18", "ids": ["52898427835154", "52898427889753", "52898427941722", "52898427945178", "52898427956609", "52898427963487", "52898427963735", "52898427970975", "52898427974712", "52898427993278", "52898427995175"]}, "POTW 26 Mar '26": {"visto": "2026-08-18", "ids": ["52899501610448", "52899501682093", "52899501686662", "52899501687031", "52899501698816", "52899501704886", "52899501704993", "52899501713134", "52899501729435", "52899501735102", "52899501737962"]}, "POTW National Teams 2 Apr '26": {"visto": "2026-08-18", "ids": ["52899770115621", "52899770121640", "52899770125723", "52899770125826", "52899770127980", "52899770134230", "52899770134470", "52899770137909", "52899770139611", "52899770145476", "52899770150952"]}, "POTW 9 Apr '26": {"visto": "2026-08-18", "ids": ["52900038483579", "52900038503936", "52900038544066", "52900038544105", "52900038553634", "52900038553646", "52900038558670", "52900038564120", "52900038576551", "52900038603503", "52900038624677"]}, "POTW 21 May '26": {"visto": "2026-08-18", "ids": ["52901380664392", "52901380679835", "52901380680800", "52901380726959", "52901380730932", "52901380730939", "52901380742826", "52901380744554", "52901380747213", "52901380758278", "52901380766800"]}, "POTM Brazilian League 10 Jul '25": {"visto": "2026-08-18", "ids": ["53976464668196", "53976464732182", "53976464735047", "53976464736629", "53976464773364", "53976464790817"]}, "POTS English League 24-25": {"visto": "2026-08-18", "ids": ["55068460097362", "55068460117088", "55068460158191", "55068460162986", "55068460168376", "55068460171421", "55068460171452", "55068460171551", "55068460171655", "55068460171804", "55068460173151", "55068460176107", "55068460176816", "55068460178909", "55068460183501", "55068460184363", "55068460189519", "55068460194657", "55068460197336", "55068460209528"]}, "POTS Spanish League 24-25": {"visto": "2026-08-18", "ids": ["55068728532034", "55068728534588", "55068728539556", "55068728553559", "55068728592228", "55068728602335", "55068728603871", "55068728604535", "55068728606318", "55068728606489", "55068728608166", "55068728613896", "55068728618458", "55068728618656", "55068728625084", "55068728626790", "55068728630326", "55068728633070", "55068728644230", "55068728663652"]}, "POTS Trendyol Süper Lig 24-25": {"visto": "2026-08-18", "ids": ["55069265399671", "55069265400582", "55069265423335", "55069265463209", "55069265465611", "55069265466549", "55069265472476", "55069265472498", "55069265472524", "55069265474925", "55069265481360", "55069265483966", "55069265488684", "55069265489941", "55069265490485", "55069265498063", "55069265500175", "55069265515116", "55069265527317"]}, "POTS Italian League 25-26": {"visto": "2026-08-18", "ids": ["55069802280907", "55069802334015", "55069802342513", "55069802348081", "55069802348765", "55069802351276", "55069802352350", "55069802353778", "55069802354280", "55069802357576", "55069802359885", "55069802361877", "55069802375077", "55069802378853", "55069802385650", "55069802386207", "55069802390795", "55069802396052", "55069802398749", "55069802401513"]}, "POTS Spanish League 25-26": {"visto": "2026-08-18", "ids": ["55070339147925", "55070339149151", "55070339165826", "55070339165913", "55070339204992", "55070339207776", "55070339208350", "55070339215207", "55070339215364", "55070339218528", "55070339220817", "55070339221612", "55070339223299", "55070339225880", "55070339231952", "55070339239313", "55070339239525", "55070339265706", "55070339270464", "55070339278757"]}, "POTS English League 25-26": {"visto": "2026-08-18", "ids": ["55070607578576", "55070607581343", "55070607587294", "55070607649352", "55070607651018", "55070607652807", "55070607654410", "55070607654887", "55070607657273", "55070607660052", "55070607666523", "55070607666913", "55070607667189", "55070607668011", "55070607670543", "55070607675511", "55070607676904", "55070607683713", "55070607703230", "55070607716019"]}, "POTS Trendyol Süper Lig 25-26": {"visto": "2026-08-18", "ids": ["55070876022532", "55070876036641", "55070876039189", "55070876081807", "55070876083368", "55070876084691", "55070876085214", "55070876086138", "55070876087661", "55070876094096", "55070876094622", "55070876096721", "55070876100065", "55070876118921", "55070876119403", "55070876121649", "55070876122670", "55070876122984"]}, "POTD International Cup Day 11": {"visto": "2026-08-18", "ids": ["56163139890527", "56163139903267", "56163139956740", "56163139999591", "56163140008258", "56163190239491"]}, "POTD International Cup Day 16": {"visto": "2026-08-18", "ids": ["56164482082972", "56164482083871", "56164482134050", "56164482158182", "56164482165002", "56164566026195"]}, "POTD International Cup Day 17": {"visto": "2026-08-18", "ids": ["56164750503259", "56164750578580", "56164750585918", "56164750599696", "56164750623419", "56164750632696"]}, "POTD International Cup Day 18-19": {"visto": "2026-08-18", "ids": ["56165019008842", "56165019016286", "56165019026854", "56165019032260", "56165019040848", "56165019067344"]}, "POTD International Cup Day 27": {"visto": "2026-08-18", "ids": ["56167166486641", "56167166487110", "56167166506265", "56167166556926"]}, "POTD International Cup Day 28-29": {"visto": "2026-08-18", "ids": ["56167434860491", "56167434870573", "56167434921679", "56167434979136"]}, "POTD International Cup Day 33-34": {"visto": "2026-08-18", "ids": ["56168240220884", "56168240228767", "56168240230526", "56168240236559", "56168240247352", "56168240262069"]}, "Germany 2002 feat. Captain Tsubasa": {"visto": "2026-08-18", "ids": ["88033944800711"]}, "Transfer Aug '22": {"visto": "2026-07-09", "ids": ["105553384806629"]}, "Club Pack FC Bayern München Oct '22": {"visto": "2026-07-09", "ids": ["105557948218809"]}, "National Team Selection France 21 Nov '22": {"visto": "2026-07-09", "ids": ["105562243176752", "105562243182718"]}, "National Team Pack France [Premium] Nov '22": {"visto": "2026-07-09", "ids": ["105563048421444"]}, "Club Icons Jan '23": {"visto": "2026-07-09", "ids": ["105568954067359"]}, "Derby Day England 5 Mar '23": {"visto": "2026-07-09", "ids": ["105572980533316"]}, "Club Selection Manchester B 3 Apr '23": {"visto": "2026-07-09", "ids": ["105574322779320"]}, "European Club Championship Selection 16 Mar '23": {"visto": "2026-07-09", "ids": ["105575396416673", "105575396517577"]}, "Masterful Stars 13 Apr '23": {"visto": "2026-07-09", "ids": ["105576201761705", "105576201779319"]}, "Club Selection Chelsea B 8 May '23": {"visto": "2026-07-09", "ids": ["105578617670692"]}, "End-season MVPs 11 May '23": {"visto": "2026-07-09", "ids": ["105579959916322", "105579959944852"]}, "League Selection Italian 15 May '23": {"visto": "2026-07-09", "ids": ["105580496794182"]}, "Club Selection FC Bayern München 5 Jun '23": {"visto": "2026-07-09", "ids": ["105582644223960", "105582644280761"]}, "Fans' Choice Asia 22-23": {"visto": "2026-07-09", "ids": ["105585328564279", "105585328643029"]}, "Fans' Choice Young Stars 22-23": {"visto": "2026-07-09", "ids": ["105585597067456", "105585597086633"]}, "National Team Selection Colombia 31 Jul '23": {"visto": "2026-07-09", "ids": ["105588281359016"]}, "National Team Selection France 24 Jul '23": {"visto": "2026-07-09", "ids": ["105589623599230", "105589623605167"]}, "Summer Tour in Japan 14 Aug '23": {"visto": "2026-07-09", "ids": ["105590697335088", "105590697338022"]}, "Summer Transfer 3 Aug '23": {"visto": "2026-07-09", "ids": ["105592844749860", "105592844822968"]}, "Manchester United FC Pack 5 Oct '23": {"visto": "2026-07-09", "ids": ["105629351978669", "105629351979076", "105629352046638", "105629352050876"]}, "Arsenal FC Pack 5 Oct '23": {"visto": "2026-07-09", "ids": ["105629620493269"]}, "Halloween Campaign 26 Oct '23": {"visto": "2026-07-09", "ids": ["105632841711033", "105632841744383"]}, "Spanish League Selection 14 Mar '24": {"visto": "2026-07-09", "ids": ["105655927053473", "105655927154806", "105655927160055"]}, "English League Selection 14 Mar '24": {"visto": "2026-07-09", "ids": ["105656463961896", "105656464045337", "105656464050599"]}, "English League Selection Guardians 11 Apr '24": {"visto": "2026-07-09", "ids": ["105663174864633", "105663174930145"]}, "Speedsters 9 May '24": {"visto": "2026-07-09", "ids": ["105679817862778", "105679817923720", "105679817928417"]}, "National Team Pack England '24": {"visto": "2026-07-09", "ids": ["105683039136529", "105683039142008", "105683039160133"]}, "National Team Pack Portugal '24": {"visto": "2026-07-09", "ids": ["105683844338090", "105683844342701"]}, "National Teams Selection Worldwide 13 Jun '24": {"visto": "2026-07-09", "ids": ["105684649687720", "105684649772480"]}, "Leo Messi Edition 2025": {"visto": "2026-07-09", "ids": ["105692434376822"]}, "Welcome Login Bonus": {"visto": "2026-07-09", "ids": ["105695387103016", "105695387168894", "105695387172984"]}, "Startup Campaign 12 Sep '24": {"visto": "2026-07-09", "ids": ["105701561184448", "105701829556407", "105701829568955"]}, "English League Selection 19 Sep '24": {"visto": "2026-07-09", "ids": ["105705856155870", "105705856174503"]}, "Earthmover 7 Nov '24": {"visto": "2026-08-18", "ids": ["105716056630957", "105716056649338", "105716056649465", "105716056702865", "105716056708070", "105716056712317", "105716056728354", "105716056735746"]}, "National Teams Selection European 12 Dec '24": {"visto": "2026-08-18", "ids": ["105723841278232", "105723841280289", "105723841325471", "105723841328312", "105723841331136", "105723841339672", "105723841349620", "105723841358689", "105723841358773", "105723841364613", "105723841373851"]}, "Ramadan Campaign 20 Feb '25": {"visto": "2026-08-18", "ids": ["105733773437389", "105733773450844", "105733773457753", "105733773466384"]}, "Italian League Selection 27 Mar '25": {"visto": "2026-08-18", "ids": ["105744779222202", "105744779229223", "105744779229454", "105744779289721", "105744779296470", "105744779297017", "105744779300574", "105744779301958", "105744779308416", "105744779311573", "105744779312437"]}, "English League Selection 6 Mar '25": {"visto": "2026-08-18", "ids": ["105745316097371", "105745316156412", "105745316157177", "105745316159746", "105745316167967", "105745316170079", "105745316171163", "105745316172820", "105745316173420", "105745316178794", "105745316179814"]}, "International Cup Qualifiers Campaign 13 Mar '25": {"visto": "2026-08-18", "ids": ["105747732088751", "105747732089740", "105747732098816", "105747732100434", "105747732120051", "105753906105363", "105753906129647", "105753906129731", "105753906133590", "105753906133604", "105754174542191", "105754174542851", "105754174549069", "105754174549610", "105754174563778", "106737453559252", "106737453603113", "106737453613030", "106737453613622", "106737453614662"]}, "English League Selection 24 Apr '25": {"visto": "2026-08-18", "ids": ["105750684825586", "105750684869966", "105750684871984", "105750684872750", "105750684877018", "105750684879161", "105750684880119", "105750684886236", "105750684898296", "105750684920680", "105750684926988"]}, "The Art of Passing 17 Apr '25": {"visto": "2026-08-18", "ids": ["105751221679839", "105751221680311", "105751221734082", "105751221734121", "105751221741686", "105751221754884", "105751221760241", "105751221792344"]}, "Winter Transfer 3 Mar '25": {"visto": "2026-08-18", "ids": ["105754979770527", "105754979844662", "105754979847340", "105754979851158", "105754979851679", "105754979858128", "105754979871496", "105754979882618"]}, "Elite Lineage 15 May '25": {"visto": "2026-08-18", "ids": ["105756053575949", "105756053582484", "105756053582519", "105756053582688", "105756053587775", "105756053603387", "105756053603388", "105756053604165", "105756053618569"]}, "English League Selection Guardians 26 May '25": {"visto": "2026-08-18", "ids": ["105761422291802", "105761422292364", "105761422292421", "105761422295232", "105761422300662", "105761422316450", "105761422326813", "105761422345278"]}, "National Teams Selection 17 Jul '25": {"visto": "2026-08-18", "ids": ["105768133185903", "105768133193441", "105768133195033", "105768133198038", "105768133203420", "105768133204752", "105768133207292", "105768133207973", "105768133208663", "105768133209515", "105768133223907"]}, "Champions Campaign 24-25 FC Barcelona": {"visto": "2026-08-18", "ids": ["105770817461314", "105770817531956", "105770817532096", "105770817554469", "105770817583426"]}, "Lamine Yamal Edition 2026": {"visto": "2026-08-18", "ids": ["105775380952852", "105775380957221", "105775380966325", "105775380968166", "105775380968504", "105775380970714", "105775380977201", "105775380981403", "105775380983650", "105775380986227", "88038239795522"]}, "Daily Bonus 2026": {"visto": "2026-08-18", "ids": ["105775917811551", "105775917822492", "105775917831976", "105776186238118", "105776186242502", "105776186249585", "105776186272669", "105823967684663", "105823967752880", "105823967763933", "105824236193711", "105824236196867", "105824236213724", "106747922604897", "106765639374176", "106780671715908", "106780671726691"]}, "Back in the Game 14 Aug '25": {"visto": "2026-08-18", "ids": ["105779675838539", "105779675902175", "105779675904885", "105779675905448", "105779675905953", "105779675962970"]}, "Italian League Selection Guardians 21 Aug '25": {"visto": "2026-08-18", "ids": ["105781018013316", "105781018077872", "105781018081705", "105781018085610", "105781018086013", "105781018101256", "105781018104141", "105781018109852"]}, "Italian League Selection Guardians 8 Sep '25": {"visto": "2026-08-18", "ids": ["105782628618516", "105782628691248", "105782628694647", "105782628696313", "105782628696474", "105782628708241", "105782628709854", "105782628739319"]}, "Anticipated Standouts 25-26": {"visto": "2026-08-18", "ids": ["105782897139165", "105782897143750", "105782897156511", "105782897156794", "105782897164122", "105782897169290", "105782897172040", "105782897187543"]}, "National Teams Selection Guardians 6 Oct '25": {"visto": "2026-08-18", "ids": ["105785849850014", "105785849917642", "105785849920877", "105785849923497", "105785849926543", "105785849948268", "105785849948969", "105785849949086"]}, "PFA Awards 2025": {"visto": "2026-08-18", "ids": ["105792023863122", "105792023867176", "105792023879459", "105792023929090", "105792023931295", "105792023933543", "105792023937415", "105792023938879", "105792023949025", "105792023949405", "105792023968986"]}, "Speedsters 6 Nov '25": {"visto": "2026-08-18", "ids": ["105794171419895", "105794171427685", "105794171431354", "105794171439578", "105794171442168", "105794171450422", "105794171452929", "105794171470860"]}, "Clutch Players 4 Dec '25": {"visto": "2026-08-18", "ids": ["105794439746322", "105794439801608", "105794439850769", "105794439855675", "105794439856275", "105794439861140", "105794439876234", "105794439893044"]}, "AS Monaco Selection 20 Apr '26": {"visto": "2026-08-18", "ids": ["105799003160992", "105799003189215", "105799003257530", "105799003270372", "105799003277407", "105799003277743", "105799003292364", "105799003305459"]}, "Piemonte BN Selection 29 Dec '25": {"visto": "2026-08-18", "ids": ["105800076997502", "105800076999693", "105800077005709", "105800077013402", "105800077021517", "105800077026754", "105800077033092", "105800077050909"]}, "Tottenham WB Selection 3 Nov '25": {"visto": "2026-08-18", "ids": ["105800882301924", "105800882303250", "105800882303664", "105800882308866", "105800882319209", "105800882325492", "105800882329384", "105800882362762"]}, "Italian League Selection 5 Mar '26": {"visto": "2026-08-18", "ids": ["105801956038912", "105801956044205", "105801956045692", "105801956046016", "105801956046312", "105801956048801", "105801956050813", "105801956060725", "105801956066824", "105801956089422", "105801956099268"]}, "National Teams Selection 8 Jan '26": {"visto": "2026-08-18", "ids": ["105802492809642", "105802492839218", "105802492865361", "105802492909797", "105802492916022", "105802492919142", "105802492921775", "105802492922090", "105802492925027", "105802492943562", "105802492952578"]}, "Spanish League Selection 16 Oct '25": {"visto": "2026-08-18", "ids": ["105803298128216", "105803298148206", "105803298155871", "105803298215100", "105803298216233", "105803298222326", "105803298223503", "105803298237825", "105803298257275", "105803298272426", "105803298279485"]}, "Arsenal FC Pack 25-26": {"visto": "2026-08-18", "ids": ["105804103519376", "105804103521260", "105804103521469", "105804103532762", "105804103544545", "105804103545400", "105804103548058", "105804103550011", "105804103551155", "105804103551534", "105804103565865"]}, "Manchester United Pack 25-26": {"visto": "2026-08-18", "ids": ["105804908766893", "105804908784736", "105804908833553", "105804908838329", "105804908842360", "105804908843755", "105804908846557", "105804908857901", "105804908859155", "105804908868664", "105804908879113"]}, "Japanese Stars 6 Apr '26": {"visto": "2026-08-18", "ids": ["105817525312469", "105817525313194", "105817525319426", "105817525319488", "105817525325846", "105817525333826", "105817525348052", "105817525350394", "106762954972673", "106762955018895", "106762955019322"]}, "European Clubs Selection 15 Jan '26": {"visto": "2026-08-18", "ids": ["105820478019024", "105820478087097", "105820478091227", "105820478097277", "105820478102634", "105820478115146", "105820478135535", "105820478139412"]}, "Spanish League Selection Guardians 23 Feb '26": {"visto": "2026-08-18", "ids": ["105827994220228", "105827994281341", "105827994282549", "105827994285898", "105827994300983", "105827994319227", "105827994325287", "105827994326194"]}, "Role Changers 5 Mar '26": {"visto": "2026-08-18", "ids": ["105828799598124", "105828799598961", "105828799606481", "105828799607548", "105828799610127", "105828799612352", "105828799639282", "105828799644734"]}, "National Teams Campaign Mar '26": {"visto": "2026-08-18", "ids": ["105831752277335", "105831752384205", "105831752386365", "105831752396173", "105844905716269", "105844905748176", "105844905769282", "105844905772864", "106773960831286", "106773960836927"]}, "English League 25-26 Season's Best": {"visto": "2026-08-18", "ids": ["105847053209473", "105847053216618", "105847053218316", "105847053224560", "105847053225747", "105847053225988", "105847053250386", "105847053251793", "106778255821223", "106778255827359"]}, "National Team Pack England 2026": {"visto": "2026-08-18", "ids": ["105849200621750", "105849200635641", "105849200685102", "105849200685258", "105849200694299", "105849200705750", "105849200707397", "105849200712620", "105849200715280", "105849200737470"]}, "National Team Pack France 2026": {"visto": "2026-08-18", "ids": ["105849469070367", "105849469111254", "105849469120546", "105849469120638", "105849469121172", "105849469124895", "105849469126575", "105849469129702", "105849469139289", "105849469143573", "105849469150860"]}, "National Team Pack Netherlands 2026": {"visto": "2026-08-18", "ids": ["105850005925672", "105850005983974", "105850005992818", "105850005998764", "105850005999106", "105850005999148", "105850006002844", "105850006007901", "105850006008049", "105850006017016", "105850006017500"]}, "National Team Selection Japan Jun '26": {"visto": "2026-08-18", "ids": ["105850274377559", "105850274422273", "105850274438148", "105850274440395", "105850274440406", "105850274443149", "105850274443253", "105850274445062", "105850274449267", "105850274451554", "105850274451903"]}, "National Team Pack Türkiye 2026": {"visto": "2026-08-18", "ids": ["105850542852841", "105850542865832", "105850542872832", "105850542874904", "105850542877475", "105850542889372", "105850542891713", "105850542891974", "105850542893322", "105850542898734", "105850542916637"]}, "National Team Selection Brazil Jun '26": {"visto": "2026-08-18", "ids": ["105850811231189", "105850811233193", "105850811293836", "105850811297844", "105850811298407", "105850811304249", "105850811314987", "105850811316710", "105850811317244", "105850811319718", "105850811325688"]}, "National Team Selection Malaysia May '26": {"visto": "2026-08-18", "ids": ["105851348169412", "105851348171352", "105851348187940", "105851348187947", "105851348193896", "105851348212928", "105851348214410", "105851348214413", "105851348225662", "105851348229244", "105851348238214"]}, "National Team Selection Indonesia Jun '26": {"visto": "2026-08-18", "ids": ["105851666888706", "105851666928735", "105851666929920", "105851666933156", "105851666944980", "105851666948025", "105851666962720", "105851666965172", "105851666980824", "105851666981523", "105851666981529"]}, "National Team Selection Egypt Jun '26": {"visto": "2026-08-18", "ids": ["105852237307683", "105852237353730", "105852237357787", "105852237358172", "105852237362944", "105852237380941", "105852237392648", "105852237395399", "105852237395400", "105852237410755", "105852237421001"]}, "Japan Selection 2 Jul '26": {"visto": "2026-08-18", "ids": ["105855374605766", "105855374705611", "105855374705614", "105855374711653", "105855374711765", "105855374758570", "106783087647510", "106783087647748", "106783087650006", "106783087652853", "106783087654662", "106783087658867"]}, "Italy Selection 11 Jun '26": {"visto": "2026-08-18", "ids": ["105856716870918", "105856716875181", "105856716881856", "105856716881894", "105856716900910", "105856716914308", "105856716927847", "105856716932292", "88044145348064", "88044413760689", "89138288133079"]}, "National Teams Selection 29 Jun '26": {"visto": "2026-08-18", "ids": ["105857790570068", "105857790613668", "105857790619868", "105857790622767", "105857790626942", "105857790655076", "105857790655590", "105857790656951", "88044145222014", "88044145248348", "88044145253792"]}, "National Teams Selection 6 Jul '26": {"visto": "2026-08-18", "ids": ["105858327483934", "105858327493990", "105858327499431", "105858327501390", "105858327505878", "105858327506775", "105858327507990", "105858327513076", "88044145214363", "88044145348028", "88044145348118"]}, "National Team Selection Algeria Jun '26": {"visto": "2026-08-18", "ids": ["105860558796162", "105860558811421", "105860558858388", "105860558860253", "105860558863655", "105860558872928", "105860558880165", "105860558896107", "105860558903021", "105860558913969", "105860558923477"]}, "National Team Selection Korea Republic Jun '26": {"visto": "2026-08-18", "ids": ["105867772995639", "105867773017511", "105867773068870", "105867773069145", "105867773075036", "105867773075969", "105867773079001", "105867773082911", "105867773088320", "105867773111889", "105867773118895"]}, "Show Time Italian League 22-23": {"visto": "2026-07-09", "ids": ["106654507051839", "106654507064924", "106654507071184"]}, "Show Time English League 23-24": {"visto": "2026-07-09", "ids": ["106728595173160", "106728595255864"]}, "Show Time Young Stars 23-24 Vol. 2": {"visto": "2026-07-09", "ids": ["106730205869134", "106730205873248", "106730205877240"]}, "Hard-working Players 3 Oct '24": {"visto": "2026-07-09", "ids": ["106732084830367", "106732084936483"]}, "Aerial Fort 9 Jan '25": {"visto": "2026-08-18", "ids": ["106734500753192", "106734500820152", "106734500820728"]}, "National Teams Selection Guardians 20 Mar '25": {"visto": "2026-08-18", "ids": ["105746926709717", "105746926769932", "105746926773953", "105746926779011", "105746926779439", "105746926782304", "105746926786152", "105746926813434", "106738258909413", "106738258921279", "106738258937280"]}, "Korea Republic Focus Campaign 13 Mar '25": {"visto": "2026-08-18", "ids": ["105753637595191", "105753637675521", "105753637678553", "105753637682463", "105753637717848", "106739869539932"]}, "Brazilian League Selection 29 May '25": {"visto": "2026-08-18", "ids": ["105756590452157", "105756590469105", "105756590469796", "105756590473215", "105756590477159", "105756590480742", "105756590488534", "105756590513006", "106740674763013", "106740674765072", "106740674828340", "106740674853884"]}, "Towering Giants 29 May '25": {"visto": "2026-08-18", "ids": ["105757395686773", "105757395709980", "105757395760945", "105757395766533", "105757395766587", "105757395780728", "105757395792952", "105757395822240", "106741211655929", "106741211703711", "106741211713905"]}, "Trendyol Süper Lig Selection 15 May '25": {"visto": "2026-08-18", "ids": ["105758737935178", "105758737939278", "105758737960515", "105758737970591", "105758737972126", "105758737982833", "105758737994236", "105758737995370", "106741748512301", "106741748586752", "106741748591999", "106741748631921"]}, "Long-reach Tackle 1 May '25": {"visto": "2026-08-18", "ids": ["106742553882816", "106742553885943", "106742553898721"]}, "English League 24-25 Season's Best": {"visto": "2026-08-18", "ids": ["105764643519326", "105764643520025", "105764643523866", "105764643525731", "105764643538016", "105764643557695", "105764643560041", "105764643563808", "106743359189607", "106743359205469"]}, "AFC Asian Qualifiers™ Selection 22 May '25": {"visto": "2026-08-18", "ids": ["105772209988743", "105772209990763", "105772209991942", "105772209993947", "105772210042305", "105772210042425", "105772210046506", "105772210053762", "106746899114039", "106746899117047", "106746899194332", "106746899235852"]}, "National Team Selection Portugal 4 Aug '25": {"visto": "2026-08-18", "ids": ["105778065282828", "105778065282850", "105778065287320", "105778065290424", "105778065295711", "105778065296760", "105778065317108", "105778065331834", "106748459484820", "106748459487131"]}, "Club International Cup Campaign 12 Jun '25": {"visto": "2026-08-18", "ids": ["106749264693909", "106749264802276", "106749264804803", "106749264818797", "106749281580484"]}, "Squad Pillars 24-25 Season's Best": {"visto": "2026-08-18", "ids": ["105788265766247", "105788265768376", "105788265844024", "105788265852062", "105788265852625", "105788265860820", "105788265861019", "105788265874124", "106752485992566", "106752486016837", "89135066951464"]}, "Show Time 9 Aug '25": {"visto": "2026-08-18", "ids": ["106753828209219"]}, "Brazilian League Selection 28 Aug '25": {"visto": "2026-08-18", "ids": ["105796050414335", "105796050458655", "105796050459339", "105796050476454", "105796050487433", "105796050498225", "105796050514486", "105796050521906", "106755170302024", "106755170349023", "106755170353522", "106755170362129"]}, "Brazilian League Selection 30 Oct '25": {"visto": "2026-08-18", "ids": ["105796587268756", "105796587270439", "105796587271113", "105796587327320", "105796587353479", "105796587378141", "105796587379404", "105796587385079", "106755707155132", "106755707216005", "106755707220784", "106755707278436"]}, "Trendyol Süper Lig Monthly MVPs Aug '25": {"visto": "2026-08-18", "ids": ["105797392568681", "105797392588889", "105797392634357", "105797392639585", "105797392640152", "105797392655201", "105797392678465", "106756512476135", "106756512520356", "106756512526918", "106756512542639"]}, "Earthmover 27 Oct '25": {"visto": "2026-08-18", "ids": ["105805982503686", "105805982513238", "105805982568338", "105805982581165", "105805982607697", "105805982608572", "105805982613506", "105805982632234", "106758928448759", "106758928449823", "106758928478044"]}, "Rising Prodigies 15 Sep '25": {"visto": "2026-08-18", "ids": ["105808935382574", "105808935390994", "105808935391102", "105808935397072", "105808935413079", "105808935413697", "105808935417892", "105808935430156", "106759465339413", "106759465365080", "106759465371456"]}, "Diagonal Long Pass B 6 Nov '25": {"visto": "2026-08-18", "ids": ["105809472188034", "105809472227880", "105809472229984", "105809472245420", "105809472246676", "105809472253542", "105809472260720", "105809472284346", "105809472287911", "105809472290023", "106759733768760", "106759733774894"]}, "AFC Champions League Elite™ Selection 20 Oct '25": {"visto": "2026-08-18", "ids": ["105813247039602", "105813247060772", "105813247061757", "105813247105507", "105813247111128", "105813247123929", "105813247128063", "105813247163827", "106761092659319", "106761092718202", "106761092722444", "106761092731496"]}, "National Teams Selection Southeast Asia 27 Nov '25": {"visto": "2026-08-18", "ids": ["105814840894614", "105814840965924", "105814840969361", "105814840984243", "105814840991704", "105814840992405", "105814841002180", "105814841002183", "105814841003566", "106761881238104", "106761881277010", "106761881282574", "106761881287983", "106761881289891", "106761881292414"]}, "National Teams Selection 6 Nov '25": {"visto": "2026-08-18", "ids": ["106762149600615", "106762149606313", "106762149661348", "106762149664546"]}, "Central Dominator 5 Jan '26": {"visto": "2026-08-18", "ids": ["105819672713083", "105819672776029", "105819672777144", "105819672789184", "105819672796254", "105819672800821", "105819672832288", "105819672843196", "106763760282015", "106763760292838", "106763760299981"]}, "CAF AFRICA CUP OF NATIONS 25 vol.2": {"visto": "2026-08-18", "ids": ["105823246328958", "105823246339422", "105823246354989", "105823246362182", "105823246364158", "105823246367723", "106765454774629", "106765454779807", "106765454795104"]}, "American League Selection 17 Nov '25": {"visto": "2026-08-18", "ids": ["105825041391998", "105825041443184", "105825041485296", "105825041492424", "105825041502529", "105825041506730", "105825041526486", "105825041526735", "106766176130728", "106766176132585", "106766176132874", "106766176135223"]}, "New Year's Gift 2026": {"visto": "2026-08-18", "ids": ["106766981442907", "106766981509166", "106766981558114"]}, "Over-the-Top Pass C 5 Feb '26": {"visto": "2026-08-18", "ids": ["105826383608135", "105826383608226", "105826383668783", "105826383675161", "105826383689129", "105826383700918", "106768055185192", "106768055197475"]}, "Trendyol Süper Lig Monthly MVPs Jan '26": {"visto": "2026-08-18", "ids": ["105827457419202", "105827457421470", "105827457423522", "105827457423616", "105827457423644", "105827457437924", "105827457442497", "106768323680420", "106768323686982", "106768323710975", "106768323746308"]}, "Attack Trigger 19 Feb '26": {"visto": "2026-08-18", "ids": ["106768592071776", "106768592119926", "106768592137310"]}, "eFootball™ League Rewards Phase 10": {"visto": "2026-08-18", "ids": ["106769665885243"]}, "eFootball™ League Rewards Phase 11": {"visto": "2026-08-18", "ids": ["106769934330781"]}, "Trendyol Süper Lig Monthly MVPs Mar '26": {"visto": "2026-08-18", "ids": ["105836852586776", "105836852657280", "105836852658126", "105836852664608", "105836852666216", "105836852670082", "105836852670483", "106772350211068", "106772350228103", "106772350228736", "106772350248490"]}, "FC Barcelona Selection 20 Apr '26": {"visto": "2026-08-18", "ids": ["105837657890793", "105837657960494", "105837657966607", "105837657976193", "105837657997091", "105837658001460", "105837658005316", "105837658021466", "106772887089344", "106772887111104", "106772887125793"]}, "Ligue 1 McDonald’s Selection 2 Mar '26": {"visto": "2026-08-18", "ids": ["105844637275989", "105844637281791", "105844637297892", "105844637311784", "105844637319176", "105844637319345", "105844637331186", "105844637349732", "106776376765788", "106776376791946", "106776376796960"]}, "Starter Set 28 May '26": {"visto": "2026-08-18", "ids": ["105846516333406", "105846516353374", "105846516380154", "106777450514613", "106777718857892"]}, "Trendyol Süper Lig Monthly MVPs May '26": {"visto": "2026-08-18", "ids": ["105848395383057", "105848395386435", "105848395386758", "105848395389102", "105848395400674", "105848395408053", "105848395438518", "106779329476141", "106779329486937", "106779329535631", "106779329558490"]}, "Mobile 9th Anniversary Celebration": {"visto": "2026-08-18", "ids": ["106780940151245", "106780940156328", "106780940156345", "106780940205246"]}, "International Cup vol.4": {"visto": "2026-08-18", "ids": ["106782282266807", "106782282337313", "106782282354314"]}, "International Cup vol.6": {"visto": "2026-08-18", "ids": ["106782819217056", "106782819256128"]}, "Tournament Stars 2026": {"visto": "2026-08-18", "ids": ["105854837821566", "105854837836653", "105854837839159", "105854837862087", "105854837865552", "105854837866225", "105854837879235", "105854837882618", "106787919411383", "106787919475376"]}, "POTW European Club Championship 22 Sep '22": {"visto": "2026-07-09", "ids": ["52778168787119", "52778168793771"]}, "POTW International Cup 8 Dec '22": {"visto": "2026-07-09", "ids": ["52781121579063", "52781121650238", "52781121668192"]}, "POTW 27 Apr '23": {"visto": "2026-07-09", "ids": ["52785953482441", "52785953484992"]}, "POTW 8 Jun '23": {"visto": "2026-07-09", "ids": ["52787295558817", "52787295560432", "52787295585287", "52787295665723"]}, "POTW National Teams 22 Jun '23": {"visto": "2026-07-09", "ids": ["52787564025383", "52787564047456", "52787564100349", "52787564107184"]}, "POTW 24 Aug '23": {"visto": "2026-07-09", "ids": ["52788637736279", "52788637837430"]}, "POTW 7 Sep '23": {"visto": "2026-07-09", "ids": ["52845277653047", "52845277718943", "52845277743527"]}, "POTW 26 Oct '23": {"visto": "2026-07-09", "ids": ["52847693536417", "52847693586211", "52847693630185", "52847693645299"]}, "POTW 9 Nov '23": {"visto": "2026-07-09", "ids": ["52848767392772", "52848767403456"]}, "POTW European Club Championship 16 Nov '23": {"visto": "2026-07-09", "ids": ["52849304150957", "52849304184140", "52849304260801", "52849304260977"]}, "POTW 7 Dec '23": {"visto": "2026-07-09", "ids": ["52850109595212"]}, "POTW European Club Championship 7 Dec '23": {"visto": "2026-07-09", "ids": ["52850378005461"]}, "POTW 11 Jan '24": {"visto": "2026-07-09", "ids": ["52851720165605", "52851720171743", "52851720174914", "52851720182920"]}, "POTW 15 Feb '24": {"visto": "2026-07-09", "ids": ["52853062347167", "52853062349460", "52853062371141", "52853062371751"]}, "POTW 22 Feb '24": {"visto": "2026-07-09", "ids": ["52853330718504", "52853330776672", "52853330777068", "52853330778381"]}, "POTW 14 Mar '24": {"visto": "2026-07-09", "ids": ["52854404456607", "52854404458551"]}, "POTW European Club Championship 21 Mar '24": {"visto": "2026-07-09", "ids": ["52868094734462", "52868094737849", "52868094750368"]}, "POTW 4 Apr '24": {"visto": "2026-07-09", "ids": ["52868631501985", "52868631613809"]}, "POTW 18 Apr '24": {"visto": "2026-07-09", "ids": ["52869168485350", "52869168493084"]}, "POTW 23 May '24": {"visto": "2026-07-09", "ids": ["52870779100117", "52870779111461"]}, "POTW National Teams 11 Jul '24": {"visto": "2026-07-09", "ids": ["52872121259197", "52872121266486", "52872121283128", "52872121291768"]}, "POTW 3 Oct '24": {"visto": "2026-07-09", "ids": ["52874537210872", "52874537212844"]}, "POTW European Club Championship 10 Oct '24": {"visto": "2026-08-18", "ids": ["52875073990890", "52875074046697", "52875074056199", "52875074057086", "52875074060106", "52875074062143", "52875074070263", "52875074074063", "52875074085498", "52875074086361", "52875074102991"]}, "POTW 14 Nov '24": {"visto": "2026-08-18", "ids": ["52876684618848", "52876684663144", "52876684672960", "52876684674991", "52876684675383", "52876684676342", "52876684677867", "52876684684761", "52876684686123", "52876684699074", "52876684721326"]}, "POTW National Teams 21 Nov '24": {"visto": "2026-08-18", "ids": ["52877221433770", "52877221474337", "52877221530057", "52877221533925", "52877221541234", "52877221541318", "52877221544327", "52877221562181", "52877221562791", "52877221575748", "52877221594912"]}, "POTW European Club Championship 6 Feb '25": {"visto": "2026-08-18", "ids": ["52880979573417", "52880979585090", "52880979633701", "52880979634637", "52880979636258", "52880979652557", "52880979654420", "52880979658176", "52880979672922", "52880979677139", "52880979685903"]}, "POTW 20 Feb '25": {"visto": "2026-08-18", "ids": ["52881516413344", "52881516500157", "52881516513026", "52881516514654", "52881516516336", "52881516519704", "52881516523404", "52881516523704", "52881516538632", "52881516539307", "52881516555945"]}, "POTW 27 Feb '25": {"visto": "2026-08-18", "ids": ["52881784866098", "52881784890757", "52881784935420", "52881784942599", "52881784942902", "52881784943486", "52881784950240", "52881784954333", "52881784956107", "52881784962319", "52881784974261"]}, "POTW 20 Mar '25": {"visto": "2026-08-18", "ids": ["52882590155096", "52882590182751", "52882590198880", "52882590199545", "52882590250951", "52882590255119", "52882590260674", "52882590261075", "52882590268411", "52882590271962", "52882590272913"]}, "POTW 3 Apr '25": {"visto": "2026-08-18", "ids": ["52883127049282", "52883127056822", "52883127109900", "52883127112181", "52883127112344", "52883127116966", "52883127133398", "52883127136851", "52883127149331", "52883127168600", "52883127174173"]}, "POTW 17 Apr '25": {"visto": "2026-08-18", "ids": ["52883663915005", "52883663924571", "52883663925032", "52883663993530", "52883663994191", "52883663995047", "52883663998508", "52883663999345", "52883664000003", "52883664003424", "52883664008270"]}, "POTW European Club Championship 20 Feb '25": {"visto": "2026-08-18", "ids": ["52884200789543", "52884200853996", "52884200865670", "52884200867759", "52884200871604", "52884200880473", "52884200881147", "52884200884647", "52884200886171", "52884200898180", "52884200904241"]}, "POTW European Club Championship 24 Apr '25": {"visto": "2026-08-18", "ids": ["52885274537311", "52885274540359", "52885274596541", "52885274597680", "52885274601585", "52885274601887", "52885274603566", "52885274603572", "52885274606888", "52885274625684", "52885274655042"]}, "POTW 1 May '25": {"visto": "2026-08-18", "ids": ["52885542971478", "52885542985507", "52885543028683", "52885543046459", "52885543047915", "52885543055302", "52885543057753", "52885543061541", "52885543076333", "52885543081594", "52885543081851"]}, "POTW National Teams 12 Jun '25": {"visto": "2026-08-18", "ids": ["52886616674730", "52886616730655", "52886616774957", "52886616780804", "52886616781488", "52886616793433", "52886616802964", "52886616811786", "52886616816720", "52886616818309", "52886616830458"]}, "POTW National Teams 11 Sep '25": {"visto": "2026-08-18", "ids": ["52888764161367", "52888764198235", "52888764200735", "52888764214237", "52888764257469", "52888764262980", "52888764270905", "52888764273638", "52888764273667", "52888764279902", "52888764299873"]}, "POTW 25 Sep '25": {"visto": "2026-08-18", "ids": ["52889301065493", "52889301085280", "52889301131178", "52889301132454", "52889301132864", "52889301136872", "52889301138293", "52889301141519", "52889301151837", "52889301152789", "52889301157983"]}, "POTW 2 Oct '25": {"visto": "2026-08-18", "ids": ["52889569476952", "52889569498576", "52889569520671", "52889569571431", "52889569578140", "52889569580679", "52889569586848", "52889569588649", "52889569596322", "52889569598215", "52889569608229"]}, "POTW 23 Oct '25": {"visto": "2026-08-18", "ids": ["52890374870278", "52890374875561", "52890374875921", "52890374885745", "52890374892892", "52890374892941", "52890374899136", "52890374899571", "52890374902207", "52890374921806", "52890374935405"]}, "POTW 30 Oct '25": {"visto": "2026-08-18", "ids": ["52890643249227", "52890643265557", "52890643305168", "52890643310450", "52890643315573", "52890643316008", "52890643316077", "52890643316954", "52890643324381", "52890643338232", "52890643343516"]}, "POTW 4 Dec '25": {"visto": "2026-08-18", "ids": ["52891985396128", "52891985419680", "52891985490230", "52891985492393", "52891985493661", "52891985494407", "52891985503887", "52891985511544", "52891985515372", "52891985519680", "52891985544221"]}, "POTW 11 Dec '25": {"visto": "2026-08-18", "ids": ["52892253923997", "52892253928813", "52892253930446", "52892253943504", "52892253946070", "52892253947763", "52892253948437", "52892253951784", "52892253956005", "52892253957045", "52892253966388"]}, "POTW European Club Championship 25 Sep '25": {"visto": "2026-08-18", "ids": ["52893059165992", "52893059167145", "52893059181211", "52893059229221", "52893059231790", "52893059232638", "52893059235960", "52893059240129", "52893059253670", "52893059265590", "52893059291530"]}, "POTW European Club Championship 13 Nov '25": {"visto": "2026-08-18", "ids": ["52893864488697", "52893864531133", "52893864542328", "52893864544063", "52893864545285", "52893864554415", "52893864559248", "52893864561932", "52893864563704", "52893864569735", "52893864592457"]}, "POTW European Club Championship 4 Dec '25": {"visto": "2026-08-18", "ids": ["52894132921815", "52894132973575", "52894132973694", "52894132979581", "52894132980811", "52894132996275", "52894132998043", "52894133002669", "52894133005104", "52894133005213", "52894133030143"]}, "POTW European Club Championship 29 Jan '26": {"visto": "2026-08-18", "ids": ["52894669797362", "52894669842088", "52894669842550", "52894669845168", "52894669847390", "52894669850935", "52894669855261", "52894669857637", "52894669861274", "52894669861465", "52894669879940"]}, "POTW European Club Championship 26 Feb '26": {"visto": "2026-08-18", "ids": ["52895206648904", "52895206705099", "52895206707519", "52895206713492", "52895206723941", "52895206724635", "52895206727528", "52895206738351", "52895206743499", "52895206757728", "52895206764386"]}, "POTW European Club Championship 5 Mar '26": {"visto": "2026-08-18", "ids": ["52895475086249", "52895475140684", "52895475147060", "52895475148205", "52895475151094", "52895475160038", "52895475165658", "52895475167151", "52895475173080", "52895475182471", "52895475188428"]}, "POTW European Club Championship 23 Apr '26": {"visto": "2026-08-18", "ids": ["52896280392617", "52896280448144", "52896280457223", "52896280457250", "52896280457526", "52896280460029", "52896280461130", "52896280487327", "52896280488202", "52896280489452", "52896280508738"]}, "POTW 12 Feb '26": {"visto": "2026-08-18", "ids": ["52897891019910", "52897891062252", "52897891063586", "52897891069986", "52897891077153", "52897891086278", "52897891086520", "52897891088344", "52897891097516", "52897891114346", "52897891130970"]}, "POTW 5 Mar '26": {"visto": "2026-08-18", "ids": ["52898696305850", "52898696326240", "52898696372138", "52898696383734", "52898696392417", "52898696395771", "52898696404120", "52898696405407", "52898696413683", "52898696423330", "52898696427842"]}, "POTW 16 Apr '26": {"visto": "2026-08-18", "ids": ["52900306923313", "52900306979798", "52900306990450", "52900306995215", "52900306996396", "52900307004764", "52900307009750", "52900307012876", "52900307021291", "52900307021953", "52900307032396"]}, "POTW 23 Apr '26": {"visto": "2026-08-18", "ids": ["52900575358760", "52900575360971", "52900575374311", "52900575417606", "52900575428855", "52900575431962", "52900575443614", "52900575447573", "52900575455863", "52900575474818", "52900575482481"]}, "POTW 30 Apr '26": {"visto": "2026-08-18", "ids": ["52900843793755", "52900843850404", "52900843852277", "52900843858068", "52900843858916", "52900843860214", "52900843877675", "52900843893220", "52900843896610", "52900843908580", "52900843910924"]}, "POTM Brasileirão Betano 14 May '26": {"visto": "2026-08-18", "ids": ["53984249311006", "53984249354285", "53984249358379", "53984249371055", "53984249373209", "53984249397183"]}, "POTS Ligue 1 Uber Eats 23-24": {"visto": "2026-07-09", "ids": ["55067117989922", "55067118012404"]}, "POTS English League 23-24": {"visto": "2026-07-09", "ids": ["55067386331226", "55067386425567", "55067386425959", "55067386431839", "55067386455692"]}, "POTS Spanish League 23-24": {"visto": "2026-07-09", "ids": ["55067654796153", "55067654854885"]}, "POTS Italian League 24-25": {"visto": "2026-08-18", "ids": ["55068996967610", "55068997031174", "55068997036751", "55068997037051", "55068997037395", "55068997038972", "55068997039522", "55068997039592", "55068997041713", "55068997041878", "55068997042112", "55068997045101", "55068997047299", "55068997053618", "55068997063103", "55068997064992", "55068997069057", "55068997074433", "55068997075060", "55068997082702"]}, "Champions Campaign 25-26 Paris Saint-Germain": {"visto": "2026-08-18", "ids": ["55071144547234", "55072486740874"]}, "POTD International Cup Day 4": {"visto": "2026-08-18", "ids": ["56161529278248", "56161529361025", "56161529379414", "56161529393658", "56161529398584", "56161613253165"]}, "POTD International Cup Day 12": {"visto": "2026-08-18", "ids": ["56163408385004", "56163408392226", "56163408396319", "56163408399393", "56163408409938", "56163492281881"]}, "POTD International Cup Day 13": {"visto": "2026-08-18", "ids": ["56163676721578", "56163676818671", "56163676827359", "56163676848342", "56163676849812", "56163760664861"]}, "POTD International Cup Day 14": {"visto": "2026-08-18", "ids": ["56163945263719", "56163945266472", "56163945279536", "56163945294573", "56163945300998", "56163945336685"]}, "POTD International Cup Day 20": {"visto": "2026-08-18", "ids": ["56165287440437", "56165287449574", "56165287461944", "56165287474663", "56165287477893", "56165371349549"]}, "POTD International Cup Day 23": {"visto": "2026-08-18", "ids": ["56166092683577", "56166092747440", "56166092749498", "56166092750624", "56166092753953", "56166092766931"]}, "POTD International Cup Day 24": {"visto": "2026-08-18", "ids": ["56166361188271", "56166361204716", "56166361216452", "56166361224544"]}, "POTD International Cup Day 9": {"visto": "2026-08-18", "ids": ["56168508667068", "56168508668869", "56168508672311", "56168508675153", "56168508688815", "56168508708296"]}, "Premium Player Pack L. Messi Jun '22": {"visto": "2026-07-09", "ids": ["70374381329569"]}, "Germany 1990 feat. Captain Tsubasa": {"visto": "2026-08-18", "ids": ["88034213236197"]}, "Italy 2021": {"visto": "2026-07-09", "ids": ["88035823760539", "88036360594067", "88040387150135"]}, "Club Selection Manchester B 17 Oct '22": {"visto": "2026-07-09", "ids": ["105559290329771", "105559290415527"]}, "Festive Season Campaign AC Milan 14 Dec '23": {"visto": "2026-07-09", "ids": ["105641700078228"]}, "Mobile 7th Anniversary Celebration": {"visto": "2026-07-09", "ids": ["105681428448562", "105681428525102", "105681428544425"]}, "Spanish League Selection Guardians 18 Nov '24": {"visto": "2026-08-18", "ids": ["105717130367939", "105717130434362", "105717130438001", "105717130444409", "105717130455108", "105717130455946", "105717130462936", "105717130471048"]}, "European Clubs Selection Guardians 17 Feb '25": {"visto": "2026-08-18", "ids": ["105736457743446", "105736457790717", "105736457804894", "105736457805651", "105736457809805", "105736457823509", "105736457834716", "105736457835402"]}, "Madrid Chamartin B Selection 7 Apr '25": {"visto": "2026-08-18", "ids": ["105752832350470", "105752832353649", "105752832356478", "105752832359285", "105752832368884", "105752832373838", "105752832378693", "105752832417380"]}, "Spanish League Selection Guardians 29 Sep '25": {"visto": "2026-08-18", "ids": ["105785044600704", "105785044612489", "105785044617171", "105785044638799", "105785044642116", "105785044644909", "105785044655466", "105785044655780"]}, "Brazilian League 2025 Season's Best": {"visto": "2026-08-18", "ids": ["105797124207809", "105797124209342", "105797124222961", "105797124228535", "105797124228674", "105797124247145", "105797124249447", "105797124263414", "106756244017231", "106756244027167", "106756244131805"]}, "Manchester United Quiz 11 Sep '25": {"visto": "2026-08-18", "ids": ["105808129996766"]}, "European Clubs Selection 1 Dec '25": {"visto": "2026-08-18", "ids": ["105811351222601", "105811351275678", "105811351276226", "105811351279586", "105811351301841", "105811351313194", "105811351313466", "105811351328977"]}, "CAF Africa Cup of Nations Selection 11 Dec '25": {"visto": "2026-08-18", "ids": ["105823514713891", "105823514714072", "105823514718493", "105823514768986", "105823514770728", "105823514776462", "105823514783663", "105823514786276", "105823514800034", "105823514802387"]}, "National Team Pack Portugal 2026": {"visto": "2026-08-18", "ids": ["105848932186223", "105848932186795", "105848932199520", "105848932256095", "105848932265344", "105848932271764", "105848932274075", "105848932292145", "105848932292218", "105848932298328"]}, "National Team Selection Iraq Jun '26": {"visto": "2026-08-18", "ids": ["105868041434003", "105868041511388", "105868041524885", "105868041536035", "105868041542152", "105868041543644", "105868041545401", "105868041546540", "105868041554130", "105868041555522", "105868041555523"]}, "Show Time 8 Jun '23": {"visto": "2026-07-09", "ids": ["106653701683166", "106653701749501"]}, "Trendyol Süper Lig Selection 7 Mar '24": {"visto": "2026-07-09", "ids": ["106725105581480"]}, "Show Time Italian League 23-24": {"visto": "2026-07-09", "ids": ["106729132107889", "106729132110484"]}, "The All-Rounders 26 Dec '24": {"visto": "2026-08-18", "ids": ["105726525587573", "105726525608386", "105726525677708", "105726525679287", "105726525680013", "105726525703977", "105726525713474", "105726525717468", "106733963948084", "106733963950845", "106733963951528"]}, "AFC Champions League Elite™ Selection 13 Jan '25": {"visto": "2026-08-18", "ids": ["105728689889024", "105728689936874", "105728689941012", "105728689942502", "105728689945176", "105728689954557", "105728689984834", "105728689998329", "106734785925546", "106734785968811", "106734786026053"]}, "European League 24-25 Season's Best": {"visto": "2026-08-18", "ids": ["105765985630155", "105765985630391", "105765985694050", "105765985697401", "105765985716757", "105765985721028", "105765985725932", "105765985740481", "106743896063272", "106743896078681"]}, "English League Selection 22 Dec '25": {"visto": "2026-08-18", "ids": ["105818598975615", "105818599041603", "105818599042427", "105818599045286", "105818599064637", "105818599080444", "105818599089759", "105818599092798", "106763223418719", "106763223426410", "106763223432463"]}, "AFC Champions League™ Selection 16 Feb '26": {"visto": "2026-08-18", "ids": ["105833916575978", "105833916652530", "105833916653820", "105833916656238", "105833916656428", "105833916663989", "105833916674592", "105833916678346", "106771293203810", "106771293204765", "106771293270235", "106771293316203"]}, "Brasileirão Betano Selection 5 Mar '26": {"visto": "2026-08-18", "ids": ["105841684442353", "105841684443147", "105841684445096", "105841684487329", "105841684496942", "105841684513562", "105841684539050", "105841684542534", "106774497720318", "106774497723869", "106774497726444", "106774497745510"]}, "POTW 9 Feb '23": {"visto": "2026-07-09", "ids": ["52783000624617", "52783000685289"]}, "POTW 23 Feb '23": {"visto": "2026-07-09", "ids": ["52783537501640", "52783537565822", "52783537568444"]}, "POTW 23 Mar '23": {"visto": "2026-07-09", "ids": ["52784611254141", "52784611304863"]}, "POTW 1 Jun '23": {"visto": "2026-07-09", "ids": ["52787027123543", "52787027217090", "52787027254032"]}, "POTW 31 Aug '23": {"visto": "2026-07-09", "ids": ["52788906209492", "52788906274942", "52788906294185"]}, "POTW 21 Sep '23": {"visto": "2026-07-09", "ids": ["52845814528683", "52845814585122"]}, "POTW European Club Championship 21 Dec '23": {"visto": "2026-07-09", "ids": ["52851183322921"]}, "POTW 22 Aug '24": {"visto": "2026-07-09", "ids": ["52872658154040"]}, "POTW 10 Oct '24": {"visto": "2026-07-09", "ids": ["52874805637688"]}, "POTW National Teams 17 Oct '24": {"visto": "2026-08-18", "ids": ["52875342426844", "52875342438179", "52875342440713", "52875342491586", "52875342494461", "52875342498026", "52875342502062", "52875342509844", "52875342511258", "52875342511375", "52875342527062"]}, "POTW 26 Dec '24": {"visto": "2026-08-18", "ids": ["52879100515879", "52879100524619", "52879100585640", "52879100588158", "52879100588278", "52879100592519", "52879100604323", "52879100604365", "52879100607401", "52879100607759", "52879100637026"]}, "POTW Club International Cup 10 Jul '25": {"visto": "2026-08-18", "ids": ["52887690416071", "52887690522658", "52887690522750", "52887690525992", "52887690534303", "52887690550188", "52887690552649", "52887690553610", "52887690564960", "52887690567240", "52887690579199"]}, "POTW 18 Sep '25": {"visto": "2026-08-18", "ids": ["52889032606112", "52889032623410", "52889032690370", "52889032694064", "52889032706053", "52889032719514", "52889032722782", "52889032722855", "52889032737267", "52889032750860", "52889032760040"]}, "POTW National Teams 16 Oct '25": {"visto": "2026-08-18", "ids": ["52890106371459", "52890106373560", "52890106392014", "52890106435340", "52890106440141", "52890106442388", "52890106443145", "52890106453148", "52890106462422", "52890106463195", "52890106496029"]}, "POTW European Club Championship 30 Oct '25": {"visto": "2026-08-18", "ids": ["52893596106919", "52893596108546", "52893596109460", "52893596113437", "52893596118982", "52893596119681", "52893596124820", "52893596124997", "52893596129988", "52893596153612", "52893596157124"]}, "POTW European Club Championship 26 Mar '26": {"visto": "2026-08-18", "ids": ["52896011951170", "52896011971406", "52896012020127", "52896012021812", "52896012025128", "52896012028215", "52896012041487", "52896012048168", "52896012049652", "52896012059063", "52896012078905"]}, "POTW 19 Mar '26": {"visto": "2026-08-18", "ids": ["52899233179044", "52899233183877", "52899233184427", "52899233244286", "52899233247736", "52899233256171", "52899233265626", "52899233278218", "52899233278356", "52899233294624", "52899233319051"]}, "POTD International Cup Day 31-32": {"visto": "2026-08-18", "ids": ["56167971795167", "56167971795254", "56167971811177", "56167971812633"]}, "Liga MX x Day of the Dead 2022": {"visto": "2026-07-09", "ids": ["105556337499280"]}, "BLUE LOCK Collaboration Campaign 21 Mar '24": {"visto": "2026-07-09", "ids": ["105657269264138", "105658074590304", "105658343074253", "105658611511342", "105659416861935"]}, "Role Changers 13 Feb '25": {"visto": "2026-08-18", "ids": ["105729746813018", "105729746843595", "105729746907170", "105729746907188", "105729746908648", "105729746939740", "105729746948374", "105729746955981"]}, "30th Anniversary Elites 10 Jul '25": {"visto": "2026-08-18", "ids": ["105770549044695", "105770549046303", "105770549087376", "105770549094258", "105770549094861", "105770549094980", "105770549095396", "105770549096694"]}, "Chelsea B Selection 18 May '26": {"visto": "2026-08-18", "ids": ["105801150744415", "105801150744927", "105801150753886", "105801150756139", "105801150768600", "105801150771036", "105801150771407", "105801150782703"]}, "European Clubs Selection 9 Oct '25": {"visto": "2026-08-18", "ids": ["105807593181310", "105807593181926", "105807593190234", "105807593193660", "105807593205083", "105807593205944", "105807593219044", "105807593224403"]}, "National Team Pack Germany 2026": {"visto": "2026-08-18", "ids": ["105849737505756", "105849737548277", "105849737550053", "105849737554381", "105849737557752", "105849737559882", "105849737583300", "105849737587522", "105849737587523", "105849737587588", "105849737591393"]}, "Spain Selection 16 Jul '26": {"visto": "2026-08-18", "ids": ["105859132787394", "105859132793293", "105859132802911", "105859132806164", "105859132816538", "105859132821094", "105859132827344", "105859132833571"]}, "National Team Rising Stars 2 Jul '26": {"visto": "2026-08-18", "ids": ["105863159356176", "105863159362754", "105863159370023", "105863159370166", "105863159375515", "105863159384430", "105863159388554", "105863159388842", "105863159392367", "105863243280360"]}, "Summer Transfer 28 Jul '25": {"visto": "2026-08-18", "ids": ["105769206922598", "105769206931808", "105769206937560", "105769206942170", "105769206948909", "105769206948928", "105769206952515", "105769206970178", "106745775110909", "106745775115778", "106745775135428"]}, "European Club Championship 24-25 Season's Best": {"visto": "2026-08-18", "ids": ["105765180324167", "105765180378256", "105765180380144", "105765180388806", "105765180403850", "105765180404758", "105765180406779", "105765180414919", "106746580415858", "106746580456800"]}, "Standout Midfielders 25-26 Season's Best": {"visto": "2026-08-18", "ids": ["105839536957595", "105839537026386", "105839537038913", "105839537039516", "105839537039959", "105839537044213", "105839537046053", "105839537070790", "106773423963383", "106773423990288", "89138019820906"]}, "POTW 17 Nov '22": {"visto": "2026-07-09", "ids": ["52780047903181"]}, "POTW European Club Championship 30 Jan '25": {"visto": "2026-08-18", "ids": ["52880442695351", "52880442758124", "52880442765850", "52880442769382", "52880442771767", "52880442773873", "52880442781057", "52880442781344", "52880442781579", "52880442781834", "52880442802675"]}, "POTW 24 Apr '25": {"visto": "2026-08-18", "ids": ["52883932419146", "52883932426550", "52883932427132", "52883932429053", "52883932431872", "52883932433690", "52883932435348", "52883932437981", "52883932442165", "52883932455582", "52883932485023"]}, "POTW Club International Cup 3 Jul '25": {"visto": "2026-08-18", "ids": ["52887422011457", "52887422013682", "52887422015749", "52887422080994", "52887422089918", "52887422093623", "52887422094115", "52887422099969", "52887422102622", "52887422115238", "52887422135896"]}, "POTW 4 Sep '25": {"visto": "2026-08-18", "ids": ["52888495818533", "52888495819515", "52888495820640", "52888495823012", "52888495829473", "52888495833576", "52888495848719", "52888495851379", "52888495859978", "52888495877720", "52888495890666"]}, "POTW 19 Feb '26": {"visto": "2026-08-18", "ids": ["52898159428914", "52898159441453", "52898159442345", "52898159451939", "52898159455277", "52898159508221", "52898159511903", "52898159512987", "52898159537052", "52898159546629", "52898159559876"]}, "POTM Brazilian League 25 Sep '25": {"visto": "2026-08-18", "ids": ["53978343780960", "53978343785952", "53978343812520", "53978343813402", "53978343814403", "53978343823207"]}, "POTD International Cup Day 10": {"visto": "2026-08-18", "ids": ["56162871522674", "56162871532700", "56162871543647", "56162871550948", "56162871554253", "56162955404703"]}, "POTD International Cup Day 21": {"visto": "2026-08-18", "ids": ["56165555812535", "56165555822578", "56165555825049", "56165555880124", "56165555885083", "56165555900116"]}, "Transfer Oct '22": {"visto": "2026-07-09", "ids": ["105556605970093", "105556605974603"]}, "Derby Day London 2 May '23": {"visto": "2026-07-09", "ids": ["105578080877242"]}, "English League Selection Midfielders 18 Sep '23": {"visto": "2026-07-09", "ids": ["105625325514975", "105625325547356"]}, "New Chapter 5 Oct '23": {"visto": "2026-07-09", "ids": ["105628546742970", "105628546762565"]}, "European Clubs Selection Guardians 22 Apr '24": {"visto": "2026-07-09", "ids": ["105663711787706"]}, "Spanish League Selection Midfielders 27 May '24": {"visto": "2026-07-09", "ids": ["105665859194786"]}, "National Team Pack Argentina '24": {"visto": "2026-07-09", "ids": ["105682502284569"]}, "Miami's Spanish Stars 21 Nov '24": {"visto": "2026-08-18", "ids": ["105718204110504", "105718204112361"]}, "National Team Selection Spain 7 Nov '24": {"visto": "2026-08-18", "ids": ["105730552145786", "105730552206525", "105730552213508", "105730552213727", "105730552214921"]}, "National Teams Selection Midfielders 2 Jun '25": {"visto": "2026-08-18", "ids": ["105756321968408", "105756321970183", "105756322009214", "105756322028136", "105756322039356", "105756322044614", "105756322077129", "105756322079050"]}, "Manchester B Selection 2 Jun '25": {"visto": "2026-08-18", "ids": ["105761153790841", "105761153854020", "105761153855711", "105761153878439", "105761153883558", "105761153886985", "105761153892130", "105761153907902"]}, "Club International Cup Selection 12 Jun '25": {"visto": "2026-08-18", "ids": ["105764375012684", "105764375016361", "105764375018095", "105764375080888", "105764375110675", "105764375112456", "105764375118332", "105764391856959"]}, "Borussia Dortmund Selection 24 Jul '25": {"visto": "2026-08-18", "ids": ["105768938434048", "105768938475360", "105768938489256", "105768938490899", "105768938500737", "105768938515181", "105768938515356", "105768938517558"]}, "Chelsea B Selection 18 Aug '25": {"visto": "2026-08-18", "ids": ["105780481208407", "105780481219999", "105780481232900", "105780481238668", "105780481239149", "105780481240924", "105780481266541", "105780481267103"]}, "Mid-season MVPs 8 Jan '26": {"visto": "2026-08-18", "ids": ["105794708219320", "105794708285855", "105794708294269", "105794708309875", "105794708312183", "105794708319133", "105794708320092", "105794708331882"]}, "Internazionale Milano Pack 25-26": {"visto": "2026-08-18", "ids": ["105804371889939", "105804371897988", "105804371900686", "105804371954409", "105804371956998", "105804371960998", "105804371961381", "105804371961969", "105804371962436", "105804371965298", "105804371967974"]}, "European Clubs Selection Guardians 3 Nov '25": {"visto": "2026-08-18", "ids": ["105806787875975", "105806787884428", "105806787884999", "105806787886438", "105806787889465", "105806787891147", "105806787897412", "105806787912381"]}, "National Team Icons vol.2": {"visto": "2026-08-18", "ids": ["105829873260071", "105829873263213", "105829873325056", "105829873332447", "105829873349913", "105829873359623", "105829873383795", "105829923659230"]}, "Brazil Selection 25 Jun '26": {"visto": "2026-08-18", "ids": ["105857522134814", "105857522137074", "105857522184466", "105857522208638", "105857522208887", "105857522225394", "105857522226699", "105857522233591"]}, "Germany Selection 2 Jul '26": {"visto": "2026-08-18", "ids": ["105858059057795", "105858059072129", "105858059077036", "105858059077471", "105858059080556", "105858059086575", "105858059090518", "105858059118591"]}, "National Teams Selection 13 Jul '26": {"visto": "2026-08-18", "ids": ["105858864287607", "105858864353622", "105858864355084", "105858864359761", "105858864360006", "105858864369073", "105858864383032", "105858864421684", "88044145248321", "88044145277054", "88044413653830"]}, "Show Time 18 May '23": {"visto": "2026-07-09", "ids": ["106653433237410", "106653433246643", "106653433333573"]}, "Show Time European Club Championship 22-23": {"visto": "2026-07-09", "ids": ["106654238617823", "106654238640551"]}, "National Teams Selection Midfielders 16 Nov '23": {"visto": "2026-07-09", "ids": ["106722421241113"]}, "Daily Bonus": {"visto": "2026-08-18", "ids": ["105639284052394", "105639284091160", "105639284148969", "105639284189933", "105707735133256", "105707735146275", "105707735146505", "105707735227308", "105708003627134", "105708003639583", "105708003639687", "105708003641090", "105742631802658", "105742631825056", "105742631830624", "105772965019795", "105772965026972", "106727253055244", "106736916728790"]}, "Show Time European Club Tournaments 23-24": {"visto": "2026-07-09", "ids": ["106727521423266", "106727521503543"]}, "Show Time eFootball™ Festival 2024": {"visto": "2026-07-09", "ids": ["106730474235970", "106730474291018"]}, "World Player of the Year 2024": {"visto": "2026-08-18", "ids": ["105715251324344", "105715251329207", "105715251339273", "105715251382996", "105715251383017", "105715251393720", "105715251395831", "105715251405949", "106732621770975", "106732621777207", "106732621793093"]}, "New Year's Gift 1 Jan '25": {"visto": "2026-08-18", "ids": ["106735843018933", "106735843042971", "106735843043104"]}, "National Teams Selection Attackers 13 Mar '25": {"visto": "2026-08-18", "ids": ["105745852965329", "105745852965485", "105745853028653", "105745853036287", "105745853040259", "105745853047933", "105745853050577", "105745853057203", "106737722036725", "106737722037510", "106737722044542"]}, "Over-the-Top Pass A 4 Sep '25": {"visto": "2026-08-18", "ids": ["105782091748816", "105782091770993", "105782091819730", "105782091824611", "105782091827174", "105782091848390", "105782091852623", "105782091862591", "105782091875153", "105782091877685", "106750070068486", "106750070073457"]}, "Over-the-Top Pass B 2 Oct '25": {"visto": "2026-08-18", "ids": ["105785312982423", "105785313036556", "105785313036963", "105785313045037", "105785313053499", "105785313063436", "105785313074015", "105785313076752", "105785313078082", "105785313091676", "106750875381983", "106750875398684"]}, "Show Time 7 Jun '25": {"visto": "2026-08-18", "ids": ["106752754353458"]}, "Manchester United Selection 16 Feb '26": {"visto": "2026-08-18", "ids": ["106760002199005", "106760002221112", "106760002235412"]}, "eFootball™ League Rewards Phase 5": {"visto": "2026-08-18", "ids": ["106764565597595"]}, "Magnetic Feet 29 Jan '26": {"visto": "2026-08-18", "ids": ["105824772957106", "105824772986765", "105824772991008", "105824773053265", "105824773062266", "105824773082985", "105824773088273", "105824773090183", "106765907771610", "106765907789637", "106765907789861"]}, "Breakthrough Pass B 12 Mar '26": {"visto": "2026-08-18", "ids": ["105831215458713", "105831215510050", "105831215513059", "105831215516678", "105831215522088", "105831215527250", "105831215527375", "105831215532019", "105831215550985", "105831215559072", "106770739621536", "106770739623193"]}, "Arsenal FC Selection 21 May '26": {"visto": "2026-08-18", "ids": ["105837389528906", "105837389534839", "105837389541944", "106772618646508"]}, "Trendyol Süper Lig Monthly MVPs Apr '26": {"visto": "2026-08-18", "ids": ["105848126879277", "105848126937444", "105848126943804", "105848126950684", "105848126953182", "105848126973482", "105848126997315", "106779061095382", "106779061103582", "106779061108686", "106779061141038"]}, "International Cup vol.1": {"visto": "2026-08-18", "ids": ["106781476920663", "106781477023870", "106781477040769"]}, "International Cup vol.3": {"visto": "2026-08-18", "ids": ["106782013894690", "106782013903764", "106782013927260"]}, "POTW 26 Jan '23": {"visto": "2026-07-09", "ids": ["52782463750050"]}, "POTW 16 Feb '23": {"visto": "2026-07-09", "ids": ["52783269130463", "52783269152805", "52783269157572"]}, "POTW 6 Apr '23": {"visto": "2026-07-09", "ids": ["52785148186011"]}, "POTW 1 Feb '24": {"visto": "2026-07-09", "ids": ["52852525404066", "52852525478134"]}, "POTW 25 Apr '24": {"visto": "2026-07-09", "ids": ["52869436915930", "52869436927989"]}, "POTW 12 Sep '24": {"visto": "2026-07-09", "ids": ["52873463337386", "52873463366962", "52873463367745", "52873463441823", "52873463459488", "52873463470864"]}, "POTW European Club Championship 19 Dec '24": {"visto": "2026-08-18", "ids": ["52878832087977", "52878832105458", "52878832156550", "52878832158735", "52878832159597", "52878832168608", "52878832168704", "52878832171353", "52878832186804", "52878832187974", "52878832201421"]}, "POTW 9 Oct '25": {"visto": "2026-08-18", "ids": ["52889837932398", "52889837997461", "52889837999088", "52889838004639", "52889838012727", "52889838019946", "52889838022294", "52889838030611", "52889838036812", "52889838038876", "52889838043629"]}, "POTW 6 Nov '25": {"visto": "2026-08-18", "ids": ["52890911684368", "52890911684878", "52890911694627", "52890911697563", "52890911746463", "52890911764664", "52890911765291", "52890911765967", "52890911771157", "52890911775896", "52890911792490"]}, "POTW 13 Nov '25": {"visto": "2026-08-18", "ids": ["52891180112962", "52891180115276", "52891180178945", "52891180180646", "52891180187070", "52891180190333", "52891180192882", "52891180200476", "52891180208027", "52891180227823", "52891180246741"]}, "POTW 12 Mar '26": {"visto": "2026-08-18", "ids": ["52898964747671", "52898964802212", "52898964811056", "52898964815095", "52898964817725", "52898964822272", "52898964834341", "52898964843272", "52898964843421", "52898964845123", "52898964866077"]}, "POTW 28 May '26": {"visto": "2026-08-18", "ids": ["52901649095746", "52901649102231", "52901649113097", "52901649159970", "52901649163645", "52901649165284", "52901649166389", "52901649169926", "52901649173786", "52901649188708", "52901649220670"]}, "POTS Italian League 23-24": {"visto": "2026-07-09", "ids": ["55067923286761", "55067923312181", "55067923314384"]}, "POTD International Cup Day 5": {"visto": "2026-08-18", "ids": ["56161797708986", "56161797802021", "56161797813920", "56161797816759", "56161797829059", "56161848136240"]}, "POTD International Cup Day 7": {"visto": "2026-08-18", "ids": ["56162334587063", "56162334653278", "56162334672709", "56162334681687", "56162334681984", "56162334699096"]}, "POTD International Cup Day 8": {"visto": "2026-08-18", "ids": ["56162603017656", "56162603098399", "56162603100071", "56162603118247", "56162603149423", "56162603159351"]}, "POTD International Cup Day 15": {"visto": "2026-08-18", "ids": ["56164213690869", "56164213715185", "56164213720125", "56164213731164", "56164213744966", "56164297650152"]}, "World Player of the Year 2025": {"visto": "2026-08-18", "ids": ["105790681689896", "105790681702179", "105790681754015", "105790681755700", "105790681757042", "105790681761599", "105790681782980", "105790681783212", "88039313485858", "88040118816667", "88040118843714"]}, "Club Pack FC Barcelona Oct '22": {"visto": "2026-07-09", "ids": ["105557679802405"]}, "Mid-season MVPs Jan '23": {"visto": "2026-07-09", "ids": ["105569222502056", "105569222527013"]}, "Derby Day Classic 19 Mar '23": {"visto": "2026-07-09", "ids": ["105574591216887"]}, "J.LEAGUE Monthly MVPs May '23": {"visto": "2026-07-09", "ids": ["105585060089833"]}, "Club Selection Madrid Chamartin B 7 Aug '23": {"visto": "2026-07-09", "ids": ["105590428927813"]}, "Summer Transfer 10 Aug '23": {"visto": "2026-07-09", "ids": ["105593113252860", "105593113267536", "105593113271432"]}, "Spanish League Selection Midfielders 30 Oct '23": {"visto": "2026-07-09", "ids": ["105632304859173"]}, "Club Icons 7 Dec '23": {"visto": "2026-07-09", "ids": ["105639552527707", "105639552527964", "105639552543719", "105639552601681"]}, "English League Selection 14 Dec '23": {"visto": "2026-07-09", "ids": ["105640626339188"]}, "English League Selection Midfielders 15 Jan '24": {"visto": "2026-07-09", "ids": ["105647874029000"]}, "Spanish League Selection Midfielders 22 Jan '24": {"visto": "2026-07-09", "ids": ["105653511161138", "105653511172985"]}, "National Teams Selection Attackers 18 Mar '24": {"visto": "2026-07-09", "ids": ["105655658655067"]}, "Classic No. 10 Players 21 Mar '24": {"visto": "2026-07-09", "ids": ["105664248648684"]}, "European Clubs Selection Attackers 20 May '24": {"visto": "2026-07-09", "ids": ["105666127704098", "105666127707508"]}, "National Teams Selection European 13 Jun '24": {"visto": "2026-07-09", "ids": ["105684381248859", "105684381342404"]}, "National Teams Selection Midfielders 17 Jun '24": {"visto": "2026-07-09", "ids": ["105685186641167"]}, "Back in the Game 8 Aug '24": {"visto": "2026-07-09", "ids": ["105697803124515"]}, "FC Bayern München Selection 16 Sep '24": {"visto": "2026-07-09", "ids": ["105702098082576"]}, "777 Million Downloads Campaign": {"visto": "2026-07-09", "ids": ["105703440166235"]}, "Manchester United Pack 16 Jan '25": {"visto": "2026-08-18", "ids": ["105708808871847", "105708808891488", "105708808935780", "105708808941614", "105708808945081", "105708808949072", "105708808949112", "105708808950865", "105708808972197", "105708808985839", "105708808985865"]}, "English League Selection Midfielders 27 Jan '25": {"visto": "2026-08-18", "ids": ["105729478473306", "105729478475274", "105729478476206", "105729478479330", "105729478487993", "105729478491407", "105729478499079", "105729478509052"]}, "Pride of the Club 20 Mar '25": {"visto": "2026-08-18", "ids": ["105738873636146", "105738873642762", "105738873643130", "105738873702207", "105738873702309", "105738873704338", "105738873706796", "105738873715453"]}, "Spanish League Selection Midfielders 10 Mar '25": {"visto": "2026-08-18", "ids": ["105744510794030", "105744510857063", "105744510863095", "105744510874681", "105744510874702", "105744510877958", "105744510882009", "105744510893859"]}, "National Team Pack Norway '25": {"visto": "2026-08-18", "ids": ["105752563910437", "105752563913437", "105752563913708", "105752563921142", "105752563926370", "105752563939044", "105752563943847", "105752563952540", "105752563957209", "105752563958405", "105752563962427"]}, "Champions Campaign 24-25 FC Bayern München": {"visto": "2026-08-18", "ids": ["105763569711287", "105763569773005", "105763569780655", "105763569793369", "105763569802000"]}, "English League Selection 21 Aug '25": {"visto": "2026-08-18", "ids": ["105779944267935", "105779944330646", "105779944335747", "105779944341322", "105779944342478", "105779944353430", "105779944353540", "105779944357135", "105779944364807", "105779944373836", "105779944385556"]}, "Arsenal FC Partnership Campaign 7 Aug '25": {"visto": "2026-08-18", "ids": ["105789876442092"]}, "Young Stars 11 Dec '25": {"visto": "2026-08-18", "ids": ["105802761367501", "105802761377256", "105802761381392", "105802761382154", "105802761392783", "105802761393504", "105802761397591", "105802761399144", "105802761403582", "105802761405828", "105802761407743"]}, "900 Million Downloads Campaign": {"visto": "2026-08-18", "ids": ["105805445698981", "105805445711887", "105805445742371", "105805445756684", "106758391503938"]}, "National Team Icons vol.1": {"visto": "2026-08-18", "ids": ["105829604826962", "105829604828600", "105829604830555", "105829604888702", "105829604902781", "105829604910442", "105829655176327", "105829688801764"]}, "National Teams Selection Midfielders 30 Mar '26": {"visto": "2026-08-18", "ids": ["105833094551698", "105833094555200", "105833094557712", "105833094567530", "105833094568552", "105833094587644", "105833094589312", "105833094591541"]}, "National Teams Selection Attackers 27 Apr '26": {"visto": "2026-08-18", "ids": ["105838194766453", "105838194780425", "105838194780732", "105838194831606", "105838194850913", "105838194851539", "105838194867139", "105838194875764", "88041460860895", "88041460993461", "88041460993546"]}, "Show Time Rewards 18 May '23": {"visto": "2026-07-09", "ids": ["106653433261152"]}, "Show Time 27 Jul '23": {"visto": "2026-07-09", "ids": ["106655312282930", "106655312293211"]}, "Spanish League Selection Attackers 27 Nov '23": {"visto": "2026-07-09", "ids": ["106722958116677"]}, "Show Time 13 Jun '24": {"visto": "2026-07-09", "ids": ["106726447777829"]}, "Show Time Spanish League 23-24": {"visto": "2026-07-09", "ids": ["106728863677687", "106728863696709", "106728863725890"]}, "Show Time Young Stars 23-24 Vol. 1": {"visto": "2026-07-09", "ids": ["106729400568231", "106729400572844", "106729400576949"]}, "Show Time Continental Tournaments '24": {"visto": "2026-07-09", "ids": ["106731547959917"]}, "Brazilian League Selection 1 May '25": {"visto": "2026-08-18", "ids": ["105759811614541", "105759811672914", "105759811681092", "105759811699640", "105759811708233", "105759811714175", "105759811727766", "105759811736992", "106742016943293", "106742016948576", "106742017012542", "106742017042984"]}, "Offensive Genius 24 Apr '25": {"visto": "2026-08-18", "ids": ["105762227531988", "105762227604762", "105762227610986", "105762227630860", "105762227633334", "105762227634175", "105762227634336", "105762227656095", "106743090687323", "106743090758023", "106743090769804"]}, "National Team Selection Indonesia 22 May '25": {"visto": "2026-08-18", "ids": ["105772478429204", "105772478469215", "105772478473636", "105772478496944", "105772478502281", "105772478505652", "105772478519269", "105772478532873", "106747167629241", "106747167643936", "106747167662739", "106747167662741"]}, "Show Time [8 Anniv.]": {"visto": "2026-08-18", "ids": ["106747385740559"]}, "Borussia Dortmund Selection 26 Jul '25": {"visto": "2026-08-18", "ids": ["105790950183038", "105790950215529", "105790950222575", "106753291337609"]}, "eFootball™ League Rewards Phase 1": {"visto": "2026-08-18", "ids": ["106753559668284"]}, "Brazilian League Selection 25 Sep '25": {"visto": "2026-08-18", "ids": ["105796318833363", "105796318835273", "105796318835406", "105796318836246", "105796318894173", "105796318903040", "105796318916611", "105796318919671", "106755438714272", "106755438720293", "106755438787299", "106755438820479"]}, "Brazilian League Selection 27 Nov '25": {"visto": "2026-08-18", "ids": ["105796855702061", "105796855765043", "105796855765313", "105796855773908", "105796855784332", "105796855792581", "105796855803259", "105796855813029", "106755975587287", "106755975603591", "106755975663185", "106755975686702"]}, "Breakthrough Pass A 8 Jan '26": {"visto": "2026-08-18", "ids": ["105819941218745", "105819941228728", "105819941231769", "105819941236874", "105819941244305", "105819941245714", "105819941248253", "105819941250622", "105819941261863", "105819941263085", "106764028719230", "106764028750090"]}, "CAF AFRICA CUP OF NATIONS 25 vol.1": {"visto": "2026-08-18", "ids": ["105822977893468", "105822977894783", "105822977896455", "105822977911690", "105822977938808", "105822977959609", "106765186342826", "106765186350982", "106765186378504"]}, "Battle for the Show Time": {"visto": "2026-08-18", "ids": ["106767518381244"]}, "eFootball™ League Rewards Phase 8": {"visto": "2026-08-18", "ids": ["106769129043724"]}, "1-2 Cut-in A 23 Apr '26": {"visto": "2026-08-18", "ids": ["105839268507966", "105839268572895", "105839268576670", "105839268582403", "105839268585739", "105839268586621", "105839268602522", "105839268605859", "105839268615214", "105839268623814", "106773155540934", "106773155552016"]}, "Italian League 25-26 Season's Best": {"visto": "2026-08-18", "ids": ["105845979395858", "105845979462263", "105845979463585", "105845979465597", "105845979470381", "105845979475502", "105845979482252", "105845979496941", "106777181979954", "106777182101070"]}, "Trendyol Süper Lig 25-26 Season's Best": {"visto": "2026-08-18", "ids": ["105848663814726", "105848663815533", "105848663818205", "105848663822029", "105848663824640", "105848663838948", "105848663868227", "106779597968380", "106779597985415", "106779597991855"]}, "International Cup vol.5": {"visto": "2026-08-18", "ids": ["106782550787909", "106782550788446", "106782550788519"]}, "POTW 1 Sep '22": {"visto": "2026-07-09", "ids": ["52777095067617", "52777095137703"]}, "POTW 15 Sep '22": {"visto": "2026-07-09", "ids": ["52777631915074", "52777631993516"]}, "POTW International Cup 28 Nov '22": {"visto": "2026-07-09", "ids": ["52780316362565"]}, "POTW International Cup 1 Dec '22": {"visto": "2026-07-09", "ids": ["52780584725600", "52780584775806", "52780584775954"]}, "POTW 12 Jan '23": {"visto": "2026-07-09", "ids": ["52781926875605", "52781926889005", "52781926899717"]}, "POTW 2 Mar '23": {"visto": "2026-07-09", "ids": ["52783806005368", "52783806009713"]}, "POTW 13 Apr '23": {"visto": "2026-07-09", "ids": ["52785416510807", "52785416618202", "52785416625046"]}, "POTW 18 May '23": {"visto": "2026-07-09", "ids": ["52786490360026"]}, "POTW 17 Aug '23": {"visto": "2026-07-09", "ids": ["52788369426245"]}, "POTW 2 Nov '23": {"visto": "2026-07-09", "ids": ["52848230502901", "52848230512334", "52848230532933", "52848230533543"]}, "POTW 28 Dec '23": {"visto": "2026-07-09", "ids": ["52851451685713", "52851451736190"]}, "POTW European Club Championship 29 Feb '24": {"visto": "2026-07-09", "ids": ["52853867588955", "52853867671471", "52853867677733"]}, "POTW 21 Mar '24": {"visto": "2026-07-09", "ids": ["52867826326288"]}, "POTW 11 Apr '24": {"visto": "2026-07-09", "ids": ["52868899976648", "52868900044618", "52868900072373"]}, "POTW National Teams 27 Jun '24": {"visto": "2026-07-09", "ids": ["52871584326253", "52871584329051"]}, "POTW 24 Oct '24": {"visto": "2026-08-18", "ids": ["52875610824023", "52875610850610", "52875610863799", "52875610864297", "52875610916624", "52875610939737", "52875610943407", "52875610952013", "52875610953180", "52875610957077", "52875610963747"]}, "POTW 12 Dec '24": {"visto": "2026-08-18", "ids": ["52878295186505", "52878295209930", "52878295211008", "52878295213388", "52878295216150", "52878295217938", "52878295283655", "52878295289079", "52878295304332", "52878295309072", "52878295312650"]}, "POTW 9 Jan '25": {"visto": "2026-08-18", "ids": ["52879368957598", "52879369023290", "52879369025962", "52879369029120", "52879369030689", "52879369032731", "52879369034908", "52879369035160", "52879369035229", "52879369045829", "52879369051558"]}, "POTW 23 Jan '25": {"visto": "2026-08-18", "ids": ["52879905826629", "52879905828584", "52879905891748", "52879905898616", "52879905898653", "52879905900413", "52879905902785", "52879905912902", "52879905917109", "52879905941792", "52879905943393"]}, "POTW 6 Feb '25": {"visto": "2026-08-18", "ids": ["52880711131051", "52880711153650", "52880711205430", "52880711208450", "52880711210631", "52880711222966", "52880711223333", "52880711230436", "52880711242249", "52880711247900", "52880711249613"]}, "POTW 10 Apr '25": {"visto": "2026-08-18", "ids": ["52883395508245", "52883395548046", "52883395551146", "52883395571701", "52883395572758", "52883395573456", "52883395577679", "52883395582736", "52883395584701", "52883395589654", "52883395597644"]}, "POTW Club International Cup 19 Jun '25": {"visto": "2026-08-18", "ids": ["52886885140094", "52886885146389", "52886885169382", "52886885213903", "52886885222751", "52886885223821", "52886885235871", "52886885243664", "52886885252223", "52886885259096", "52886885273401"]}, "POTM Liga BBVA MX 11 Apr '24": {"visto": "2026-07-09", "ids": ["53967337854719"]}, "Champions Campaign 25-26 Internazionale Milano": {"visto": "2026-08-18", "ids": ["55071949764878"]}, "POTD International Cup Day 25": {"visto": "2026-08-18", "ids": ["56166629547424", "56166629607205", "56166629640005", "56166629640615"]}, "European Club Championship 16 Jun '22": {"visto": "2026-07-09", "ids": ["70377334146354", "70377334152258"]}, "Shining Stars 26 Dec '22": {"visto": "2026-07-09", "ids": ["105568417094999"]}, "eFootball™ Point Rewards Vol.5": {"visto": "2026-07-09", "ids": ["105570833043590"]}, "Transfer Feb '23": {"visto": "2026-07-09", "ids": ["105571906874752"]}, "European Clubs Selection Attackers 16 Oct '23": {"visto": "2026-07-09", "ids": ["105630694238119"]}, "Golden Boys 2 Nov '23": {"visto": "2026-07-09", "ids": ["105633915462473", "105633915466074"]}, "Mid-season MVPs 4 Jan '24": {"visto": "2026-07-09", "ids": ["105642505315660", "105642505334082"]}, "National Teams Selection Worldwide 12 Dec '24": {"visto": "2026-08-18", "ids": ["105724109693056", "105724109753044", "105724109761915", "105724109763175", "105724109765879", "105724109766534", "105724109768102", "105724109778582", "105724109794056", "105724109798480", "105724109813206"]}, "European Clubs Selection 27 Feb '25": {"visto": "2026-08-18", "ids": ["105737799896993", "105737799898663", "105737799900226", "105737799921130", "105737799964941", "105737799970802", "105737799995092", "105737800011916"]}, "AFC Champions League™ Selection 20 Mar '25": {"visto": "2026-08-18", "ids": ["105739158829753", "105739158855570", "105739158921714", "105739158928249", "105739158938073", "105739158941527", "105739158974033", "105739158974706", "105739158980806", "105739158980827"]}, "Bayer 04 Leverkusen Selection 20 Feb '25": {"visto": "2026-08-18", "ids": ["105749074191800", "105749074192791", "105749074252095", "105749074261752", "105749074277801", "105749074282970", "105749074287300", "105749074291614"]}, "Chelsea B Selection 5 May '25": {"visto": "2026-08-18", "ids": ["105761959160248", "105761959172637", "105761959177310", "105761959179545", "105761959179563", "105761959189420", "105761959192134", "105761959198284"]}, "Summer Transfer 14 Aug '25": {"visto": "2026-08-18", "ids": ["105780749577563", "105780749658023", "105780749666837", "105780749667942", "105780749673944", "105780749679834", "105780749692770", "105780749697723"]}, "Newly Licensed Italian Clubs 9 Oct '25": {"visto": "2026-08-18", "ids": ["105793902913420", "105793902973503", "105793902984370", "105793902985437", "105793903006143", "105793903011541", "105793903024013", "105793903025742"]}, "Madrid Rosas RB Selection 1 Dec '25": {"visto": "2026-08-18", "ids": ["105800345365576", "105800345424480", "105800345433481", "105800345438013", "105800345447582", "105800345448096", "105800345456230", "105800345468762"]}, "Worldwide Clubs Selection 12 Feb '26": {"visto": "2026-08-18", "ids": ["105824504680979", "105826920468722", "105826920478404", "105826920536368", "105826920566484", "105826920567572", "105826920588803", "105826920591404"]}, "Magical Dribbler 2 Apr '26": {"visto": "2026-08-18", "ids": ["105829067975814", "105829068019974", "105829068030343", "105829068034795", "105829068038496", "105829068061878", "105829068082431", "105829068087309"]}, "Signature Goal Celebrations 5 Feb '26": {"visto": "2026-08-18", "ids": ["105830678575179", "105830678636657", "105830678643662", "105830678644751", "105830678654925", "105830678660216", "105830678666156", "105830678669468"]}, "AFC Champions League™ Selection 19 Feb '26": {"visto": "2026-08-18", "ids": ["105833648110449", "105833648158722", "105833648206484", "105833648217722", "105833648221568", "105833648248115", "105833648251530", "105833648251533"]}, "European Clubs Selection 16 Apr '26": {"visto": "2026-08-18", "ids": ["105837121017579", "105837121021260", "105837121090286", "105837121095519", "105837121100258", "105837121105370", "105837121105668", "105837121157081"]}, "NARUTO SHIPPUDEN Collaboration Campaign 2026": {"visto": "2026-08-18", "ids": ["105838463196576", "105840610761736", "105840879109426", "105840879187432", "105840879194481", "105840879197592", "105841147550786", "105841416049644"]}, "Show Time Rewards 2 Mar '23": {"visto": "2026-07-09", "ids": ["106652627934624"]}, "Skill Up": {"visto": "2026-07-09", "ids": ["106731279490391"]}, "Offensive Genius 17 Oct '24": {"visto": "2026-08-18", "ids": ["105730820599244", "105730820653352", "105730820663738", "105730820673126", "105730820679428", "105730820685984", "105730820695344", "105730820707257", "106735037701276", "106735037705888", "106735037717188"]}, "Brazilian League 2024 Season's Best": {"visto": "2026-08-18", "ids": ["105731357453900", "105731357455305", "105731357456736", "105731357467972", "105731357470056", "105731357522659", "105731357540004", "105731357566621", "106735306076245", "106735306121991", "106735306130248", "106735306181887"]}, "Trendyol Süper Lig Selection 27 Mar '25": {"visto": "2026-08-18", "ids": ["105747463572886", "105747463639934", "105747463641213", "105747463656524", "105747463664360", "105747463684015", "105747463684185", "105747463702509", "106738527300583", "106738527354430", "106738527367026", "106738527367087"]}, "Spanish League 24-25 Season's Best": {"visto": "2026-08-18", "ids": ["105765717190805", "105765717208073", "105765717248457", "105765717251898", "105765717256399", "105765717266779", "105765717272644", "105765717294938", "106743627624500", "106743627624574"]}, "Breakout Stars 24-25 Season's Best": {"visto": "2026-08-18", "ids": ["105767864777946", "105767864783151", "105767864783369", "105767864786337", "105767864789213", "105767864790616", "105767864790733", "105767864802007", "106745238253510", "106745238268680"]}, "Club International Cup 2025": {"visto": "2026-08-18", "ids": ["105768670051123", "105768670051341", "105768670057783", "105768670065180", "105768670065235", "105768670070237", "105768670072703", "105768670090055", "106745506608041", "106745506689835", "89135067044780"]}, "Brazilian League Selection 24 Jul '25": {"visto": "2026-08-18", "ids": ["105769475302712", "105769475352688", "105769475367454", "105769475369333", "105769475376022", "105769475387756", "105769475390587", "105769475418752", "106746043475495", "106746043477580", "106746043534334", "106746043541825"]}, "Diagonal Long Pass A 15 Aug '25": {"visto": "2026-08-18", "ids": ["105780212719622", "105780212763239", "105780212771400", "105780212774076", "105780212776308", "105780212782594", "105780212790966", "105780212803712", "105780212819265", "105780212834538", "106749533208454", "106749533210935"]}, "J.LEAGUE Monthly MVPs Jul '25": {"visto": "2026-08-18", "ids": ["105781554856409", "105781554963663", "105781554992497", "105781555000164", "106749801637288", "106749801654633", "106749801697545", "106749801697703"]}, "Trendyol Süper Lig Monthly MVPs Sep '25": {"visto": "2026-08-18", "ids": ["105797661070332", "105797661071716", "105797661081565", "105797661087953", "105797661090657", "105797661095898", "105797661109248", "106756780911591", "106756780962374", "106756780971655", "106756780978095"]}, "Trendyol Süper Lig Monthly MVPs Dec '25": {"visto": "2026-08-18", "ids": ["105798466319225", "105798466377892", "105798466396856", "105798466420096", "105798466437955", "105798466441724", "105798466441733", "106757586204383", "106757586221077", "106757586263695", "106757586267102"]}, "Extraordinary One 4 Dec '25": {"visto": "2026-08-18", "ids": ["106766444571720", "106766444574903", "106766444664616"]}, "eFootball™ League Rewards Phase 6": {"visto": "2026-08-18", "ids": ["106767786806011"]}, "Campaign Rewards Feb '26": {"visto": "2026-08-18", "ids": ["106770471099808", "106770471185881", "106770471216611"]}, "Brasileirão Betano Selection 9 Apr '26": {"visto": "2026-08-18", "ids": ["105841952859185", "105841952860846", "105841952864281", "105841952921118", "105841952921646", "105841952932210", "105841952940112", "105841952959867", "106774766072775", "106774766138222", "106774766141772", "106774766159287"]}, "J.LEAGUE Monthly MVPs Feb '26": {"visto": "2026-08-18", "ids": ["105842489821699", "105842489823577", "105842489846883", "105842489858046", "106775303005608", "106775303013036", "106775303019476", "106775303024396"]}, "J.LEAGUE Monthly MVPs Mar '26": {"visto": "2026-08-18", "ids": ["105843026680178", "105843026683167", "105843026686721", "105843026732388", "106775571379169", "106775571439108", "106775571455574", "106775571493490"]}, "International Cup vol.2": {"visto": "2026-08-18", "ids": ["106781745353130", "106781745470620", "106781745473447"]}, "Show Time 9 May '26": {"visto": "2026-08-18", "ids": ["106784161310028"]}, "Strike Arena": {"visto": "2026-07-09", "ids": ["123236570413239", "123236838841410"]}, "FC Bayern München 79–80": {"visto": "2026-07-09", "ids": ["17593259920877"]}, "POTW 3 Nov '22": {"visto": "2026-07-09", "ids": ["52779510963616"]}, "POTW International Cup 15 Dec '22": {"visto": "2026-07-09", "ids": ["52781390011808"]}, "POTW 19 Jan '23": {"visto": "2026-07-09", "ids": ["52782195325003"]}, "POTW 16 Mar '23": {"visto": "2026-07-09", "ids": ["52784342881172"]}, "POTW 16 Nov '23": {"visto": "2026-07-09", "ids": ["52849035817086"]}, "POTW 25 Jan '24": {"visto": "2026-07-09", "ids": ["52852257040073", "52852257053845"]}, "POTW 8 Feb '24": {"visto": "2026-07-09", "ids": ["52852793922283"]}, "POTW 29 Feb '24": {"visto": "2026-07-09", "ids": ["52853599156299"]}, "POTW National Teams 28 Mar '24": {"visto": "2026-07-09", "ids": ["52868363197124"]}, "POTW 29 Aug '24": {"visto": "2026-07-09", "ids": ["52872926590672", "52872926595495"]}, "POTW European Club Championship 26 Sep '24": {"visto": "2026-07-09", "ids": ["52874268681548"]}, "POTW 7 Nov '24": {"visto": "2026-08-18", "ids": ["52876416223875", "52876416227560", "52876416233479", "52876416233782", "52876416240955", "52876416244502", "52876416244744", "52876416263816", "52876416269530", "52876416270170", "52876416293856"]}, "POTW 16 Jan '25": {"visto": "2026-08-18", "ids": ["52879637388647", "52879637408411", "52879637452770", "52879637456754", "52879637458978", "52879637458996", "52879637466118", "52879637469974", "52879637470216", "52879637495342", "52879637495670"]}, "POTW 22 May '25": {"visto": "2026-08-18", "ids": ["52886079836023", "52886079837787", "52886079844652", "52886079860180", "52886079910746", "52886079915871", "52886079917740", "52886079925920", "52886079926156", "52886079947002", "52886079964189"]}, "POTW 29 May '25": {"visto": "2026-08-18", "ids": ["52886348280697", "52886348281895", "52886348342701", "52886348346821", "52886348351357", "52886348361088", "52886348368429", "52886348381772", "52886348382707", "52886348394344", "52886348394442"]}, "POTW Club International Cup 26 Jun '25": {"visto": "2026-08-18", "ids": ["52887153548631", "52887153585503", "52887153600476", "52887153668404", "52887153670214", "52887153671164", "52887153682990", "52887153694028", "52887153698299", "52887153701956", "52887153706013"]}, "POTW 18 Dec '25": {"visto": "2026-08-18", "ids": ["52892522295633", "52892522310299", "52892522358440", "52892522359368", "52892522360884", "52892522364446", "52892522365357", "52892522369217", "52892522388231", "52892522389919", "52892522392478"]}, "POTW 8 Jan '26": {"visto": "2026-08-18", "ids": ["52896548823676", "52896548840583", "52896548890737", "52896548894150", "52896548910102", "52896548917367", "52896548923572", "52896548935008", "52896548937288", "52896548943628", "52896548957875"]}, "POTW 15 Jan '26": {"visto": "2026-08-18", "ids": ["52896817255888", "52896817328180", "52896817332174", "52896817332391", "52896817339400", "52896817361459", "52896817365485", "52896817365486", "52896817369887", "52896817375008", "52896817383722"]}, "POTW 22 Jan '26": {"visto": "2026-08-18", "ids": ["52897085700171", "52897085714050", "52897085760666", "52897085763618", "52897085767188", "52897085769246", "52897085775325", "52897085781291", "52897085795203", "52897085805626", "52897085824612"]}, "POTM Brasileirão Assaí 7 Dec '23": {"visto": "2026-07-09", "ids": ["53962237674443"]}, "POTM Brasileirão Benato 13 Jun '24": {"visto": "2026-07-09", "ids": ["53968680104710", "53968680110883"]}, "POTM Trendyol Süper Lig 22 Jan '26": {"visto": "2026-08-18", "ids": ["53981028140994", "53981028143070", "53981028150051", "53981028170498", "53981028177481", "53981028188611"]}, "POTM Brasileirão Betano 16 Apr '26": {"visto": "2026-08-18", "ids": ["53983980861792", "53983980934636", "53983980938001", "53983980941082", "53983980947241", "53983980954943"]}, "POTS Liga BBVA MX 23-24": {"visto": "2026-07-09", "ids": ["55066849484923", "55066849562859"]}, "POTS Brazilian League 2025": {"visto": "2026-08-18", "ids": ["55069533838752", "55069533844362", "55069533844425", "55069533845856", "55069533855818", "55069533857156", "55069533859022", "55069533859360", "55069533859614", "55069533905029", "55069533909601", "55069533918197", "55069533921087", "55069533925462", "55069533939017", "55069533944959", "55069533950196", "55069533952614", "55069533958391"]}, "Champions Campaign 25-26 Arsenal FC": {"visto": "2026-08-18", "ids": ["55071412966292"]}, "POTD International Cup Day 6": {"visto": "2026-08-18", "ids": ["56162066111831", "56162066215038", "56162066233689", "56162066237863", "56162066252275", "56162116559324"]}, "POTD International Cup Day 30": {"visto": "2026-08-18", "ids": ["56167703292363", "56167703296681", "56167703375520", "56167703392163"]}, "Great Finishers 2 May '22": {"visto": "2026-07-09", "ids": ["70373039149482", "70373039184962", "70373039202083"]}, "Breakout Stars Jul '22": {"visto": "2026-07-09", "ids": ["70379750074001", "70379750164903"]}, "Ligue 1 Uber Eats Jul '22": {"visto": "2026-07-09", "ids": ["70380286909783"]}, "Argentina 2022": {"visto": "2026-07-09", "ids": ["88030186577239"]}, "Germany 1980 feat. Captain Tsubasa": {"visto": "2026-08-18", "ids": ["88033676365293"]}, "France 1993 feat. Captain Tsubasa": {"visto": "2026-08-18", "ids": ["88034481539809"]}, "Uruguay 2010 feat. Captain Tsubasa": {"visto": "2026-08-18", "ids": ["88034750107127"]}, "France 1984 feat. Captain Tsubasa": {"visto": "2026-08-18", "ids": ["88035018410719"]}, "Vasco Gipuzkoa AB 22-23": {"visto": "2026-07-09", "ids": ["88035555400712"]}, "Vasco Gipuzkoa AB 23-24": {"visto": "2026-07-09", "ids": ["88039581932552"]}, "Premium Ambassador Pack Alexander-Arnold Sep '22": {"visto": "2026-07-09", "ids": ["105555263858377"]}, "Premium Ambassador Pack Bruno Fernandes Oct '22": {"visto": "2026-07-09", "ids": ["105557142802858"]}, "National Team Pack Portugal '22": {"visto": "2026-07-09", "ids": ["105566538043818"]}, "Club Selection Tottenham WB 16 Jan '23": {"visto": "2026-07-09", "ids": ["105569490872375"]}, "Club Selection Piemonte BN 23 Jan '23": {"visto": "2026-07-09", "ids": ["105569759379003"]}, "League Selection English 2 Mar '23": {"visto": "2026-07-09", "ids": ["105573517421702"]}, "Club Selection Liverpool R 17 Apr '23": {"visto": "2026-07-09", "ids": ["105576470271075"]}, "Perfect Introduction 8 Jun '23": {"visto": "2026-07-09", "ids": ["105582912724124"]}, "Fans' Choice English League 22-23": {"visto": "2026-07-09", "ids": ["105587476115502"]}, "National Team Selection Worldwide 31 Jul '23": {"visto": "2026-07-09", "ids": ["105589891928490"]}, "Club Selection Liverpool R 21 Aug '23": {"visto": "2026-07-09", "ids": ["105592039515849"]}, "Champions Campaign Rewards 22-23 FC Barcelona": {"visto": "2026-07-09", "ids": ["105593650153567"]}, "Champions Campaign Rewards 22-23 FC Bayern München": {"visto": "2026-07-09", "ids": ["105594723822622"]}, "AFC Asian Cup Selection Republic of Korea Jan '24": {"visto": "2026-07-09", "ids": ["105644451473463"]}, "European Clubs Selection Attackers 4 Mar '24": {"visto": "2026-07-09", "ids": ["105652974377878"]}, "Italian League Selection 14 Mar '24": {"visto": "2026-07-09", "ids": ["105656195595835"]}, "Spanish League Selection Attackers 15 Apr '24": {"visto": "2026-07-09", "ids": ["105663443355959"]}, "National Team Selection France '24": {"visto": "2026-07-09", "ids": ["105680623218814"]}, "Champions Campaign Rewards 23-24 Atalanta BC": {"visto": "2026-07-09", "ids": ["105681965395975"]}, "National Team Pack France '24": {"visto": "2026-07-09", "ids": ["105682770702370"]}, "National Stars 13 Jun '24": {"visto": "2026-07-09", "ids": ["105691092199113"]}, "Summer Transfer 15 Aug '24": {"visto": "2026-07-09", "ids": ["105694044986846", "105694044991614"]}, "Highlight Continental Tournaments '24": {"visto": "2026-07-09", "ids": ["105702366490750"]}, "SC Corinthians Paulista Selection 29 Aug '24": {"visto": "2026-07-09", "ids": ["105703171734409"]}, "Legacy of Legends 10 Oct '24": {"visto": "2026-08-18", "ids": ["105709614146386", "105709614198038", "105709614245413", "105709614251579", "105709614252189", "105709614255179", "105709614270028", "105709614280107"]}, "European Clubs Selection Attackers 4 Nov '24": {"visto": "2026-08-18", "ids": ["105715788266818", "105715788268008", "105715788280154", "105715788281816", "105715788284630", "105715788286383", "105715788304339", "105715788318084"]}, "Centre Piece 5 Dec '24": {"visto": "2026-08-18", "ids": ["105720888465275", "105720888527611", "105720888529397", "105720888535759", "105720888541431", "105720888546027", "105720888550241", "105720888553818"]}, "Liverpool R Selection 6 Feb '25": {"visto": "2026-08-18", "ids": ["105749342629672", "105749342641955", "105749342685860", "105749342693065", "105749342699067", "105749342701375", "105749342708057", "105749342711946"]}, "Advertisement Reward 24 Apr '25": {"visto": "2026-08-18", "ids": ["105754711351085", "105754711427191", "105754711432614", "105754711433908", "105754711436040", "105754711446096", "105754711451783", "105754711455091"]}, "National Team Selection Portugal 29 May '25": {"visto": "2026-08-18", "ids": ["105773233344938", "105773233444642", "105773233448649", "105773233452216", "105773233475483"]}, "Manager Edition 2026": {"visto": "2026-08-18", "ids": ["105776454608951", "105776454612767"]}, "Welcome Login Bonus 2026": {"visto": "2026-08-18", "ids": ["105778870529832", "105778870595710", "105778870613273"]}, "European Clubs Selection Attackers 11 Sep '25": {"visto": "2026-08-18", "ids": ["105783433945093", "105783433947541", "105783434009756", "105783434011773", "105783434020767", "105783434025734", "105783434029212", "105783434052996"]}, "AC Milan Pack 25-26": {"visto": "2026-08-18", "ids": ["105803835016498", "105803835029451", "105803835042847", "105803835091384", "105803835092272", "105803835094504", "105803835099111", "105803835101144", "105803835101553", "105803835120792", "105803835123870"]}, "National Teams Selection Attackers 16 Oct '25": {"visto": "2026-08-18", "ids": ["105807861574805", "105807861621018", "105807861630781", "105807861632172", "105807861636245", "105807861639980", "105807861647500", "105807861655108"]}, "Brazil & England National Team Campaign 6 Nov '25": {"visto": "2026-08-18", "ids": ["105815914625207", "105815914697755", "105815914703966", "105815914704845", "105815914709206", "105821820262479", "105821820268596", "105821820285739", "105821820290470", "105821820296614"]}, "National Teams Selection Attackers 23 Mar '26": {"visto": "2026-08-18", "ids": ["105832826046461", "105832826072532", "105832826116397", "105832826120399", "105832826122087", "105832826126493", "105832826133683", "105832826159749"]}, "Show Time Ligue 1 Uber Eats 22-23": {"visto": "2026-07-09", "ids": ["106653970182270"]}, "Show Time 7 Dec '23": {"visto": "2026-07-09", "ids": ["106723494897719", "106723494911779", "106723494968891"]}, "AFC Champions League Selection 25 Dec '23": {"visto": "2026-07-09", "ids": ["106723780071850"]}, "Show Time 1 Aug '24": {"visto": "2026-07-09", "ids": ["106726716084650", "106726716183270", "106726716190966"]}, "Trendyol Süper Lig Selection 17 Apr '25": {"visto": "2026-08-18", "ids": ["105751490128175", "105751490181819", "105751490185154", "105751490189479", "105751490189596", "105751490192058", "105751490222471", "105751490223900", "106742822244713", "106742822268038", "106742822333228", "106742822333706"]}, "Show Time 10 Aug '25": {"visto": "2026-08-18", "ids": ["106754096599541"]}, "Offensive Genius 25 Aug '25": {"visto": "2026-08-18", "ids": ["105794976723838", "105794976726538", "105794976727207", "105794976734658", "105794976738777", "105794976739551", "105794976741730", "105794976756065", "106754901843130", "106754901929868", "106754901936551"]}, "Aggressive Centring A 4 Dec '25": {"visto": "2026-08-18", "ids": ["105816719924919", "105816719931694", "105816719944982", "105816720007345", "105816720015622", "105816720019329", "105816720030046", "105816720032005", "105816720032183", "105816720046620", "106762686548319", "106762686570911"]}, "Standout Attackers 25-26 Season's Best": {"visto": "2026-08-18", "ids": ["105839805390853", "105839805450900", "105839805457253", "105839805463547", "105839805466974", "105839805472004", "105839805475630", "105839805501844", "106773692395554", "106773692401975"]}, "Manchester United 21-22": {"visto": "2026-07-09", "ids": ["17592186048938"]}, "POTW 25 Aug '22": {"visto": "2026-07-09", "ids": ["52776826679422"]}, "POTW 8 Sep '22": {"visto": "2026-07-09", "ids": ["52777363558769"]}, "POTW 29 Sep '22": {"visto": "2026-07-09", "ids": ["52777900357362"]}, "POTW 20 Apr '23": {"visto": "2026-07-09", "ids": ["52785685049470"]}, "POTW National Teams 19 Oct '23": {"visto": "2026-07-09", "ids": ["52847425098154", "52847425204350"]}, "POTW National Teams 23 Nov '23": {"visto": "2026-07-09", "ids": ["52849572697187"]}, "POTW 19 Dec '24": {"visto": "2026-08-18", "ids": ["52878563649591", "52878563710214", "52878563714930", "52878563717154", "52878563720729", "52878563724321", "52878563725272", "52878563732746", "52878563734549", "52878563737873", "52878563758399"]}, "POTW European Club Championship 27 Feb '25": {"visto": "2026-08-18", "ids": ["52884469229224", "52884469294799", "52884469297278", "52884469304395", "52884469304632", "52884469304961", "52884469310305", "52884469316521", "52884469322604", "52884469343937", "52884469344193"]}, "POTW European Club Championship 9 Oct '25": {"visto": "2026-08-18", "ids": ["52893327601284", "52893327660012", "52893327667326", "52893327677696", "52893327678879", "52893327679324", "52893327686651", "52893327691402", "52893327696868", "52893327697829", "52893327700026"]}, "POTW 14 May '26": {"visto": "2026-08-18", "ids": ["52901112285078", "52901112295470", "52901112298509", "52901112304532", "52901112306533", "52901112311349", "52901112312348", "52901112326991", "52901112344823", "52901112349371", "52901112352569"]}, "Champions Campaign 25-26 FC Barcelona": {"visto": "2026-08-18", "ids": ["55071681398799"]}, "POTD International Cup Day 22": {"visto": "2026-08-18", "ids": ["56165824239143", "56165824241828", "56165824317279", "56165824319857", "56165824320532", "56165824335498"]}, "Enchanting Dribblers 9 May '22": {"visto": "2026-07-09", "ids": ["70373307641466", "70373307691134"]}, "Premium Club Pack Manchester United Jun '22": {"visto": "2026-07-09", "ids": ["70376260374954"]}, "Portugal 2026": {"visto": "2026-07-09", "ids": ["88044950524330"]}, "Club Selection eFootball™ Championship Vol.4": {"visto": "2026-07-09", "ids": ["105577812455608"]}, "Manchester United FC Selection 8 Apr '24": {"visto": "2026-07-09", "ids": ["105654584996024"]}, "Champions Campaign Rewards '24 Spain": {"visto": "2026-07-09", "ids": ["105702903413058"]}, "Tresure Link Campaign 28 Aug '25": {"visto": "2026-08-18", "ids": ["105790144781655", "105790413371714"]}, "Champions Campaign 2025 CR Flamengo": {"visto": "2026-08-18", "ids": ["105816451510357", "105816451554136", "105816451555441", "105816451563890", "105816451581405", "105817256803120", "105817256814658", "105817256816414", "105817256866608", "105817256868579"]}, "Show Time 13 Apr '23": {"visto": "2026-07-09", "ids": ["106653164826909"]}, "Brazilian League Kick-off 27 Mar '25": {"visto": "2026-08-18", "ids": ["105742900181017", "105742900181897", "105742900194545", "105742900197448", "105742900199022", "105742900251609", "105742900257553", "105742900268927", "106737185105810", "106737185182020", "106737185189658", "106737185230079"]}, "Show Time 11 Aug '25": {"visto": "2026-08-18", "ids": ["106754365099263"]}, "Daily Free Draw 4 Dec '25": {"visto": "2026-08-18", "ids": ["106766713092441"]}, "POTW 2 Feb '23": {"visto": "2026-07-09", "ids": ["52782732190909"]}, "POTW 19 Sep '24": {"visto": "2026-07-09", "ids": ["52873731815607", "52873731930434"]}, "POTW 5 Dec '24": {"visto": "2026-08-18", "ids": ["52877758338795", "52877758340667", "52877758357283", "52877758403470", "52877758409562", "52877758410811", "52877758415005", "52877758416735", "52877758433212", "52877758433837", "52877758442306"]}, "POTW 21 Aug '25": {"visto": "2026-08-18", "ids": ["52887958894125", "52887958894919", "52887958949008", "52887958958354", "52887958965762", "52887958973146", "52887958974122", "52887958977850", "52887958987167", "52887958989749", "52887959009602"]}, "POTM Trendyol Süper Lig 12 Jun '25": {"visto": "2026-08-18", "ids": ["53976196289380", "53976196304589", "53976196310189", "53976196313725", "53976196351791", "53976196351817"]}, "FC Barcelona 24-25": {"visto": "2026-07-09", "ids": ["88035555440962"]}, "Club Selection Chelsea B 13 Feb '23": {"visto": "2026-07-09", "ids": ["105570564611459"]}, "European Clubs Selection 19 May '25": {"visto": "2026-08-18", "ids": ["105757932564600", "105757932621299", "105757932630251", "105757932630326", "105757932633881", "105757932634542", "105757932636076", "105757932648518"]}, "Paris Saint-Germain Selection 6 Oct '25": {"visto": "2026-08-18", "ids": ["105783702437160", "105783702451920", "105783702455956", "105783702463098", "105783702467044", "105783702476128", "105783702480539", "105783702490937"]}, "Breakthrough Talents 9 Dec '24": {"visto": "2026-08-18", "ids": ["105733505012739", "105733505019562", "105733505021391", "105733505027796", "105733505033688", "105733505040218", "105733505047969", "105733505050561", "106735574574294", "106735574597166", "106735574598131"]}, "National Team Selection Türkiye 20 Mar '25": {"visto": "2026-08-18", "ids": ["105746658331369", "105746658344360", "105746658351278", "105746658351360", "105746658353848", "105746658356003", "105746658356490", "105746658377262", "106737990509510", "106737990510858", "106737990526435"]}, "eFootball™ League Rewards Phase 2": {"visto": "2026-08-18", "ids": ["105812156521859", "106760270552451"]}, "POTW 9 Mar '23": {"visto": "2026-07-09", "ids": ["52784074448008"]}, "POTW 30 Nov '23": {"visto": "2026-07-09", "ids": ["52849841131713"]}, "POTM Cinch Premiership Apr '22": {"visto": "2026-07-09", "ids": ["53876606760371"]}, "Master League Sprint 9 Apr '26": {"visto": "2026-07-09", "ids": ["88043608522886"]}, "Gabriel Barbosa Campaign Reward 13 Apr '23": {"visto": "2026-07-09", "ids": ["105576738645383"]}, "AFC Champions League Selection 23 May '24": {"visto": "2026-07-09", "ids": ["105691377312496"]}, "AFC Champions League™ Selection 22 Jan '26": {"visto": "2026-08-18", "ids": ["105833379676352", "105833379764805", "105833379773217", "105833379782265", "105833379789611", "105833379803761", "105833379827241", "105833379827941"]}, "ShowTime English League 22-23": {"visto": "2026-07-09", "ids": ["106655043870499"]}, "Brasileirão Betano Selection 7 May '26": {"visto": "2026-08-18", "ids": ["105842221295506", "105842221312066", "105842221361262", "105842221366198", "105842221377909", "105842221380311", "105842221394472", "105842221416250", "106775034509133", "106775034589169", "106775034613725", "106775034629622"]}, "POTW 20 Oct '22": {"visto": "2026-07-09", "ids": ["52778974109475"]}, "POTW 10 Nov '22": {"visto": "2026-07-09", "ids": ["52779779415843"]}, "POTS Campeonato Brasileiro Série A 2022": {"visto": "2026-07-09", "ids": ["53878485695166"]}, "Champions Campaign Rewards 23-24 Inter": {"visto": "2026-07-09", "ids": ["105679281039473"]}, "Negrete - A Passada 20 Feb '25": {"visto": "2026-08-18", "ids": ["105734310370982"]}, "National Teams Selection Worldwide 19 Jun '25": {"visto": "2026-08-18", "ids": ["105765448748906", "105765448813308", "105765448819419", "105765448820849", "105765448825694", "105765448838026", "105765448847231", "105765448854602", "105765448873424", "105765448874797", "105765499170265"]}, "J.LEAGUE Monthly MVPs Sep '24": {"visto": "2026-08-18", "ids": ["105711224890877", "106732353241291", "106732353288463", "106732353376912", "106732353383210"]}, "2025 J.LEAGUE AWARDS": {"visto": "2026-08-18", "ids": ["105787728871863", "105787728916317", "105787728976898", "105787728977751", "105787728981772", "105787728982769", "105787728982781", "105787728983860", "105787728985581", "106751949120936", "106751949126357", "106751949173604"]}, "eFootball™ League Rewards Phase 9": {"visto": "2026-08-18", "ids": ["106769397419872"]}, "Manchester United FC 64-65": {"visto": "2026-07-09", "ids": ["87963614711285"]}, "Manchester United FC 63-64": {"visto": "2026-07-09", "ids": ["88031797317109"]}, "Manchester United 68-69": {"visto": "2026-07-09", "ids": ["88032334188021"]}, "Golden Boys Dec '22": {"visto": "2026-07-09", "ids": ["105567075021694", "105567075052406"]}, "Italian League Selection Attackers 11 Sep '23": {"visto": "2026-07-09", "ids": ["105623983353775"]}, "Süper Lig Selection 18 Jan '24": {"visto": "2026-07-09", "ids": ["105646800277946"]}, "Halloween Campaign 24 Oct '24": {"visto": "2026-08-18", "ids": ["105711493244994", "105711493293736", "105711493300042"]}, "Trendyol Süper Lig Selection 24 Oct '24": {"visto": "2026-08-18", "ids": ["105715519826930", "105715519830786", "105715519835792", "105715519843711", "105715519844271", "105715519857345", "105715519864694", "105715519883055"]}, "BLACK FRIDAY Campaign 21 Nov '24": {"visto": "2026-08-18", "ids": ["105731625971073", "105731625977951", "105731625982762", "105731626000196", "105731894392296", "105731894393257", "105731894393258", "105731894406912"]}, "Champions Campaign 24-25 Galatasaray SK": {"visto": "2026-08-18", "ids": ["105774038683511", "105774038751396", "105774038765925", "105774038773679", "105774038793774"]}, "European Clubs Selection Attackers 23 Oct '25": {"visto": "2026-08-18", "ids": ["105807056252721", "105807056253277", "105807056340769", "105807056341174", "105807056351139", "105807056356842", "105807056365515", "105807056368708"]}, "National Teams Selection 8 Dec '25": {"visto": "2026-08-18", "ids": ["105816988360469", "105816988360530", "105816988366391", "105816988367030", "105816988428868", "105816988466256", "105816988478950", "105816988479994"]}, "Show Time 2 Mar '23": {"visto": "2026-07-09", "ids": ["106652628021167", "106652628027815"]}, "Liga BBVA MX Selection 25 Jan '24": {"visto": "2026-07-09", "ids": ["106724568715499"]}, "Goal Machines 28 Nov '24": {"visto": "2026-08-18", "ids": ["105719009416931", "105719009478421", "105719009480594", "105719009494845", "105719009496748", "105719009501032", "105719009513242", "105719009520144", "106733158578359", "106733158650049", "106733158664615"]}, "First Half of the Season 10 Apr '25": {"visto": "2026-08-18", "ids": ["105752295477672", "105752295488335", "105752295498230", "105752295500116", "105752295500736", "105752295505290", "105752295526994", "106739601022272", "106739601041994", "106739601095545", "106739601099092"]}, "Show Time 15 May '25": {"visto": "2026-08-18", "ids": ["106748996323135"]}, "Trendyol Süper Lig Monthly MVPs Oct '25": {"visto": "2026-08-18", "ids": ["105798197898215", "105798197942628", "105798197948998", "105798197949805", "105798197958865", "105798197964719", "105798197980160", "106757317825013", "106757317825532", "106757317842567", "106757317845857"]}, "POTW 11 May '23": {"visto": "2026-07-09", "ids": ["52786221849786"]}, "POTW 9 May '24": {"visto": "2026-07-09", "ids": ["52870242240935"]}, "POTM Trendyol Süper Lig 9 May '24": {"visto": "2026-07-09", "ids": ["53968143169652"]}, "POTM Trendyol Süper Lig 23 Oct '25": {"visto": "2026-08-18", "ids": ["53978612219454", "53978612221581", "53978612221854", "53978612231434", "53978612240612", "53978612252252"]}, "POTM Brazilian League 18 Dec '25": {"visto": "2026-08-18", "ids": ["53980759634885", "53980759652361", "53980759695475", "53980759707972", "53980759714165", "53980759758251"]}, "POTM Trendyol Süper Lig 19 Feb '26": {"visto": "2026-08-18", "ids": ["53982101885285", "53982101886599", "53982101887127", "53982101887178", "53982101893141", "53982101897415"]}, "Türkiye 2021": {"visto": "2026-07-09", "ids": ["88039044974638"]}, "India 2023": {"visto": "2026-07-09", "ids": ["88039044986828"]}, "England 2026": {"visto": "2026-07-09", "ids": ["88043876825271"]}, "National Teams Selection 6 Aug '26": {"visto": "2026-08-18", "ids": ["105859669692115", "105859669695690", "105859669699875"]}, "J1 LEAGUE Selection 28 May '26": {"visto": "2026-08-18", "ids": ["105843563556275", "105843563565426", "105843563582172", "105843563590422", "105843563597542", "105843563600460", "105843563600489", "105843563604842"]}, "J1 LEAGUE Selection 26 Mar '26": {"visto": "2026-08-18", "ids": ["105842758140294", "105842758169569", "105842758245206", "105842758247624", "105842758247738", "105842758260365", "105842758262122", "105842758266289"]}, "J1 LEAGUE Selection 23 Apr '26": {"visto": "2026-08-18", "ids": ["105843295011243", "105843295055693", "105843295128029", "105843295129693", "105843295131354", "105843295136299", "105843295137603", "105843295137604"]}, "Show Time 6 Aug '26": {"visto": "2026-08-18", "ids": ["106799462259226"]}, "J.LEAGUE Monthly MVPs May '26": {"visto": "2026-08-18", "ids": ["105844100317226", "105844100446407", "105844100464385", "105844100476247", "106776108311976", "106776108339229", "106776108361937", "106776108377423"]}, "Summer Transfer 17 Aug '26": {"visto": "2026-08-19", "ids": ["105869333357110", "105869333361235", "105869333368702", "105869333381118", "105869333393229", "105869333394562", "105869333401321", "105869333415031", "106785771992434", "106785772007373", "106785772021264"]}, "Chelsea B Selection 14 Aug '26": {"visto": "2026-08-19", "ids": ["105868528054502", "105868528055595", "105868528068056", "105868528071235", "105868528074316", "105868528075260", "105868528086725", "105868528101388", "88045487423105", "88045487427597", "88045755863174"]}, "Lamine Yamal Edition 2027": {"visto": "2026-08-19", "ids": ["105865306838492", "105865306842764", "105865306845091", "105865306855034", "105865306857038", "105865306863987", "105865306864830", "105865306866884", "105865306872202", "105865306872490", "88047098165570"]}, "Leo Messi Edition 2027": {"visto": "2026-08-19", "ids": ["105865038306663", "105865038307949", "105865038307964", "105865038308792", "105865038310751", "105865038312124", "105865038313234", "105865038367702", "105865038376671", "105865038392713", "88046829575511"]}, "Daily Bonus 2027": {"visto": "2026-08-19", "ids": ["105867185797302", "105867185851044", "105867185858673", "105867454305172", "105867454312689", "105867454313810", "105867454344792", "106787114104779", "88045755827674", "88045755866499", "88045755964125"]}, "Advertisement Reward 2027": {"visto": "2026-08-19", "ids": ["105863964584785", "105863964625602", "105863964635188", "105863964635994", "105863964636344", "105863964642476", "105863964672716", "105863964686707", "88045755829674", "88045755960768", "88045755960849"]}, "eFootball™ League 2027 Rewards Phase 1": {"visto": "2026-08-19", "ids": ["106785235123572"]}, "CAF Africa Cup of Nations Selection 13 Aug '26": {"visto": "2026-08-19", "ids": ["105880691466019", "105880691466200", "105880691517588", "105880691523097", "105880691523462", "105880691532128", "105880691550364", "105880691550984"]}, "Tactical Defence 13 Aug '26": {"visto": "2026-08-19", "ids": ["105864769871207", "105864769937869", "105864769941508", "105864769945293", "105864769947959", "105864769948954", "105864769951152", "105864769962198"]}, "Summer Transfer 13 Aug '26": {"visto": "2026-08-19", "ids": ["105873091431106", "105873091445023", "105873091448219", "105873091468038", "105873091473615", "105873091489528", "105873091492244", "105873091504239"]}, "English League Selection 13 Aug '26": {"visto": "2026-08-19", "ids": ["105873896745385", "105873896750438", "105873896751326", "105873896755947", "105873896760682", "105873896763633", "105873896766735", "105873896771214", "105873896774572", "105873896778628", "105873896779262"]}, "New Season Campaign 2027": {"visto": "2026-08-19", "ids": ["105866917361630", "105866917432656", "105866917436893", "105866917449491", "105866917459000", "105873628309622", "105873628311604", "105873628311744", "105873628311862", "105873628348195"]}, "Moroccan League Selection 13 Aug '26": {"visto": "2026-08-19", "ids": ["105861817154804", "105861817157277", "105861817160530", "105861817180967", "105861817187270", "105861817205535", "105861817208648", "105861817219813", "105861817219819", "105861817219822", "105861817219831"]}, "Welcome Login Bonus 2027": {"visto": "2026-08-19", "ids": ["105866112053032", "105866112118910", "105866112143259"]}, "Step-up 2027": {"visto": "2026-08-19", "ids": ["105866648987766", "105866649005150", "105866649017104"]}, "Manager Pack 13 Aug '26": {"visto": "2026-08-19", "ids": ["105865575254367", "105865575300328"]}, "Starter Set 2027": {"visto": "2026-08-19", "ids": ["105865843676422", "105865843702105", "105865843704022"]}, "Skill Up 2027": {"visto": "2026-08-19", "ids": ["105866380552607", "106784966581591"]}, "Club Pack Manchester B Jun '22": {"visto": "2026-07-09", "ids": ["70377065722745"]}, "POTM Brazilian League 10 Oct '24": {"visto": "2026-08-18", "ids": ["53970559106670", "53970559146035", "53970559146077", "53970559151515", "53970559157692", "53970559176575"]}, "Club Selection Sevilla Triana VB 5 Sep '22": {"visto": "2026-07-09", "ids": ["105554726993672"]}, "POTM Brazilian League 15 May '25": {"visto": "2026-08-18", "ids": ["53974854069608", "53974854118811", "53974854120198", "53974854133681", "53974854170076", "53974854173733"]}, "European Masters Cup 16 Jun '22": {"visto": "2026-07-09", "ids": ["70377602608450"]}, "Brazilian League Selection 12 Dec '24": {"visto": "2026-08-18", "ids": ["105724646566013", "105724646584330", "105724646623998", "105724646625775", "105724646629160", "105724646655557", "105724646666434", "105724646683818"]}, "Italian League Selection Midfielders 4 Dec '23": {"visto": "2026-07-09", "ids": ["387113187136582"]}, "POTM J1 LEAGUE 12 Jun '25": {"visto": "2026-08-18", "ids": ["53975927864176", "53975927885913", "53975927890323", "53975927891442", "53975927902935", "53975927909615"]}, "POTM J1 LEAGUE 15 May '25": {"visto": "2026-08-18", "ids": ["53975122505049", "53975122566116", "53975122570675", "53975122585088", "53975122587057", "53975122612573"]}, "Highlight English League 23-24": {"visto": "2026-07-09", "ids": ["105686797239795"]}, "New license Aug '22": {"visto": "2026-07-09", "ids": ["105553116301513"]}, "Club Selection Tigres UANL 20 Apr '23": {"visto": "2026-07-09", "ids": ["105577275492553"]}, "Highlight Spanish League 23-24": {"visto": "2026-07-09", "ids": ["105687065662081"]}, "AFC Asian Cup Selection Japan Jan '24": {"visto": "2026-07-09", "ids": ["105644183117482"]}, "eFootball Webstore": {"visto": "2026-08-19", "ids": ["88045755861057", "88045755867302"]}, "France Selection 9 Jul '26": {"visto": "2026-08-18", "ids": ["105858595860513", "105858595862475", "105858595920141", "105858595923493", "105858595930001", "105858595943762", "105858595963596", "105858595968352"]}, "POTD International Cup Day 26": {"visto": "2026-08-18", "ids": ["56166898046141", "56166898055772", "56166898059279", "56166898075998"]}, "eFootball™ League Rewards Phase 12": {"visto": "2026-08-18", "ids": ["106770202684241"]}, "POTD International Cup Day 3": {"visto": "2026-08-18", "ids": ["56161260899827", "56161260910022", "56161260912518", "56161260915001", "56161260939420", "56161311254482"]}, "POTD International Cup Day 1-2": {"visto": "2026-08-18", "ids": ["56160992464525", "56160992488841", "56160992488921", "56160992492831", "56160992494840", "56160992498373"]}, "National Teams Selection 15 Jun '26": {"visto": "2026-08-18", "ids": ["105856985306005", "105856985310927", "105856985311141", "105856985320467", "105856985337620", "105856985338073", "105856985350860", "105856985370362", "88044145348047", "88044145348069", "88044145348071"]}, "National Team Captains 11 Jun '26": {"visto": "2026-08-18", "ids": ["105862353945906", "105862353954386", "105862353955202", "105862353957564", "105862353971609", "105862354012836", "105862354020931", "105862354044152", "105862404289527", "105862437905823"]}, "Japan Selection 4 Jun '26": {"visto": "2026-08-18", "ids": ["105861548620873", "105861548621914", "105861548622168", "105861548721102", "105861548727062", "105861548730730", "105861548740954", "105861548768451"]}, "National Teams Selection 8 Jun '26": {"visto": "2026-08-18", "ids": ["105856448463933", "105856448472638", "105856448472836", "105856448473246", "105856448473567", "105856448474539", "105856448475211", "105856532388822", "88044145348017", "88044145348039", "88044145348046"]}, "National Team Selection Thailand May '26": {"visto": "2026-08-18", "ids": ["105851079679755", "105851079682634", "105851079727645", "105851079734328", "105851079745145", "105851079745151", "105851079748206", "105851079748211", "105851079748256", "105851079766660", "105851079770803"]}, "National Teams Selection 22 Jun '26": {"visto": "2026-08-18", "ids": ["105857253677921", "105857253684791", "105857253699669", "105857253740019", "105857253742893", "105857253747473", "105857253748091", "105857253755853"]}, "J1 LEAGUE Selection 11 Jun '26": {"visto": "2026-08-18", "ids": ["105844368851653", "105844368857887", "105844368863425", "105844368865006", "105844368883338", "105844368883527", "105844368888695", "105844368889201"]}, "National Teams Selection 4 Jun '26": {"visto": "2026-08-18", "ids": ["105855911579211", "105855911580932", "105855911581292", "105855911601124", "105855911603010", "105855911607376", "105855911630795", "105855995501867"]}, "Japan Selection 1 Jun '26": {"visto": "2026-08-18", "ids": ["105847590072811", "105847590077387", "105847590083368", "105847590083429", "105847590087017", "105847590096866", "105847590101443", "105847590126330"]}, "Master League Sprint 28 May '26": {"visto": "2026-08-18", "ids": ["105853495722117", "88043608522885"]}, "Highlight May '26": {"visto": "2026-08-18", "ids": ["105862622460669", "105862639181784", "105862639229509", "105862890829790", "105862890900513", "105862890947646", "106784429760291", "106784698181293"]}, "National Team Selection Indonesia 21 May '26": {"visto": "2026-08-18", "ids": ["105861062202761", "105861062222485", "105861062232195"]}, "National Teams Selection Guardians 25 May '26": {"visto": "2026-08-18", "ids": ["105859938030531", "105859938040233", "105859938051543", "105859938096255", "105859938099375", "105859938122905", "105859938125048", "105859938144575", "88040387119435", "88040387150135", "88040387255015"]}, "European Clubs Selection Guardians 14 May '26": {"visto": "2026-08-18", "ids": ["105845711020494", "105845711022546", "105845711046290", "105845711047948", "105845711048063", "105845711053470", "105845711054401", "105845711080004"]}, "Starter Set 14 May '26": {"visto": "2026-08-18", "ids": ["106781208610214"]}, "European Clubs Selection 14 May '26": {"visto": "2026-08-18", "ids": ["105861280210106", "105861280309819", "105861280331812"]}, "POTM Trendyol Süper Lig 14 May '26": {"visto": "2026-08-18", "ids": ["53982907189183", "53982907190851", "53982907196589", "53982907202719", "53982907212742", "53982907213525"]}, "POTM J1 LEAGUE 14 May '26": {"visto": "2026-08-18", "ids": ["53985054572591", "53985054572972", "53985054667678", "53985054688492", "53985054724445", "53985054734640"]}, "Liga Super Malaysia 25-26 Season's Best": {"visto": "2026-08-18", "ids": ["105846247920232", "105846247921592", "105846247940746", "105846247940749", "105846247950532", "105846247950537", "105846247951998", "105846247964550", "106783624511587", "106783624532586", "106783624536797"]}, "POTS Liga Super Malaysia 25-26": {"visto": "2026-08-18", "ids": ["55070070730712", "55070070775711", "55070070799144", "55070070799147", "55070070799156", "55070070810490", "55070070814429", "55070070825616", "55070070840446", "55070070840967", "55070070841296", "55070070849362", "55070070849451"]}, "J1 LEAGUE Selection 7 May '26": {"visto": "2026-08-18", "ids": ["105845442494916", "105845442599762", "105845442600530", "105845442602255", "105845442604811", "105845442613344", "105845442624182", "105845442630288", "105845442635414", "105845442637208", "105845442647323", "105845442654377", "88040387132864", "88040387251694"]}, "Highlight 9 May '26": {"visto": "2026-08-18", "ids": ["105862085519427", "105862085519640", "105862085581069"]}, "Worldwide Clubs Selection 30 Apr '26": {"visto": "2026-08-18", "ids": ["105838731630853", "105838731634236", "105838731701031", "105838731702507", "105838731705977", "105838731713986", "105838731734947", "105838731735524"]}, "Manager Pack 23 Apr '26": {"visto": "2026-08-18", "ids": ["105835778916220", "105835778954746"]}, "National Team Selection Malaysia 27 Apr '26": {"visto": "2026-08-18", "ids": ["105860743434856", "105860743465158", "105860743465159", "88041461035951"]}, "Advertisement Reward 16 Apr '26": {"visto": "2026-08-18", "ids": ["105854032456661", "105854032517417", "105854032532912", "105854032555082", "105854032557112", "105854032559662", "105854082874014", "105854082875568", "88040387153821", "88040387251635", "88040387251658"]}, "POTM Trendyol Süper Lig 16 Apr '26": {"visto": "2026-08-18", "ids": ["53982638744918", "53982638747672", "53982638751694", "53982638779278", "53982638789669", "53982638801361"]}, "POTM J1 LEAGUE 16 Apr '26": {"visto": "2026-08-18", "ids": ["53981565010897", "53981565017042", "53981565017060", "53981565023052", "53981565025775", "53981565054351"]}, "Liga Super Malaysia Selection 9 Apr '26": {"visto": "2026-08-18", "ids": ["105834168310666", "105834168318750", "105834168318757", "105834168318760", "105834168318772", "105834168324712", "105834168334059", "105834168345226", "105834168345232", "105834168356471", "105834168360602", "105834168369070", "105834168369115"]}, "J1 LEAGUE Selection 9 Apr '26": {"visto": "2026-08-18", "ids": ["105836315689028", "105836315784048", "105836315794419", "105836315799825", "105836315800336", "105836315807835", "105836315812292", "105836315815992", "105836315825077", "105836315830319", "105836315840884", "105836315841049"]}, "Maestro 13 Apr '26": {"visto": "2026-08-18", "ids": ["105836584149114", "105836584149152", "105836584155078", "105836584168960", "105836584216557", "105836584224050", "105836584235216", "105836584248032", "88040387147266", "88040387158182", "88040387251709"]}, "National Teams Selection 9 Apr '26": {"visto": "2026-08-18", "ids": ["105836047277293", "105836047277991", "105836047278701", "105836047279544", "105836047283999", "105836047346104", "105836047349723", "105836047350912", "105836047351928", "105836047352252", "105836047353477", "105836047354972", "105836047355375", "105836047356820", "105836047359836", "105836047363456", "105836047369179", "105836047369187", "105836047370079", "105836047375110"]}, "Italian League Selection Guardians 2 Apr '26": {"visto": "2026-08-18", "ids": ["105835510470693", "105835510481111", "105835510484557", "105835510492338", "105835510494019", "105835510498270", "105835510498741", "105835510506038"]}, "National Team Selection T�rkiye 23 Mar '26": {"visto": "2026-08-18", "ids": ["105847858509268", "105847858511487", "105847858515661", "105847858520344", "105847858520776", "105847858539410", "105847858563441", "105847858569547", "106778792685399", "106778792700170", "106778792723485"]}, "POTM J1 LEAGUE 19 Mar '26": {"visto": "2026-08-18", "ids": ["53981296520537", "53981296568459", "53981296573141", "53981296581450", "53981296581644", "53981296602518"]}, "POTM Brasileir�o Betano 19 Mar '26": {"visto": "2026-08-18", "ids": ["53983712444014", "53983712500139", "53983712502302", "53983712538549", "53983712538612", "53983712553600"]}, "European Clubs Selection 19 Mar '26": {"visto": "2026-08-18", "ids": ["105832557728022", "105832557731233", "105832557733531", "105832557735629", "105832557742446", "105832557744485", "105832557746903", "105832557753974"]}, "POTM Trendyol S�per Lig 19 Mar '26": {"visto": "2026-08-18", "ids": ["53982370249386", "53982370337477", "53982370341557", "53982370347569", "53982370348904", "53982370383269"]}, "Italian League Selection Midfielders 16 Mar '26": {"visto": "2026-08-18", "ids": ["105832020767000", "105832020805392", "105832020826014", "105832020826694", "105832020827544", "105832020831847", "105832020840182", "105832020841952"]}, "Manager Pack 12 Mar '26": {"visto": "2026-08-18", "ids": ["105831483894748", "105831483976527"]}, "Italian League Selection Attackers 5 Mar '26": {"visto": "2026-08-18", "ids": ["105830947077135", "105830947081528", "105830947083813", "105830947084378", "105830947091715", "105830947092949", "105830947099413", "105830947115064"]}, "J1 LEAGUE Selection 5 Mar '26": {"visto": "2026-08-18", "ids": ["105826115140775", "105826115186562", "105826115246898", "105826115246976", "105826115249476", "105826115252484", "105826115253518", "105826115260441", "105826115260505", "105826115277469", "105826115286209", "105826115287933"]}, "English League Selection Guardians 9 Mar '26": {"visto": "2026-08-18", "ids": ["105827188981116", "105827188994387", "105827188994791", "105827189000180", "105827189003116", "105827189013094", "105827189021013", "105827189026473"]}, "J.LEAGUE Selection 26 Feb '26": {"visto": "2026-08-18", "ids": ["105834436641042", "105834436746008", "105834436748512", "105834436751480", "105834436753090", "105834436753159", "105834436753870", "105834436758275", "105834436759517", "105834436759646", "105834436767590", "105834436767660", "105834436768051", "105834436768369", "105834436776827", "105834436777024", "105834436782128", "105834436783497", "105834436784007", "105834436784146", "105834436784625", "105834436784996", "105834436785038", "105834436788877", "105834436792549", "105834436792611", "105834436797857", "105834436799140", "105834436799163", "105834436799768"]}, "European Clubs Selection 26 Feb '26": {"visto": "2026-08-18", "ids": ["105828531147044", "105828531149032", "105828531159015"]}, "American League Selection 19 Feb '26": {"visto": "2026-08-18", "ids": ["105825309827454", "105825309859594", "105825309861943", "105825309864824", "105825309879121"]}, "European Clubs Selection 19 Feb '26": {"visto": "2026-08-18", "ids": ["105827725856300", "105827725857812", "105827725864013", "105827725870371", "105827725878291", "105827725878992", "105827725890182", "105827725908400"]}, "European Clubs Selection 16 Feb '26": {"visto": "2026-08-18", "ids": ["105810009037824", "105810009038128", "105810009058422", "105810009102535", "105810009102633", "105810009115451", "105810009139109", "105810009166449"]}, "Show Time 12 Feb '26": {"visto": "2026-08-18", "ids": ["106771544911876"]}, "Brazil Selection 5 Feb '26": {"visto": "2026-08-18", "ids": ["105834973611507", "105834973638863", "105834973648395"]}, "Manager Pack 5 Feb '26": {"visto": "2026-08-18", "ids": ["105822088636276", "105822088706705"]}, "Italian League Selection Guardians 2 Feb '26": {"visto": "2026-08-18", "ids": ["105824504573524", "105824504574520", "105824504612940", "105824504626467", "105824504626902", "105824504643190", "105824504650536", "105824504650664"]}, "European Clubs Selection 26 Jan '26": {"visto": "2026-08-18", "ids": ["105821014954992", "105821014959810", "105821014970552", "105821014984476", "105821015003489", "105821015003935", "105821015006794", "105821015020051"]}, "European Clubs Selection Guardians 19 Jan '26": {"visto": "2026-08-18", "ids": ["105820746456278", "105820746458783", "105820746463343", "105820746534776", "105820746538825", "105820746548514", "105820746554827", "105820746563834"]}, "J1 LEAGUE Selection 8 Jan '26": {"visto": "2026-08-18", "ids": ["105825578270698", "105825578360904", "105825578365422", "105825578375995", "105825578376033", "105825578376099", "105825578382437", "105825578388227", "105825578389533", "105825578390263", "105825578395114", "105825578397543"]}, "European Clubs Selection Midfielders 12 Jan '26": {"visto": "2026-08-18", "ids": ["105820209653455", "105820209663133", "105820209671893", "105820209677372", "105820209683232", "105820209693388", "105820209702530", "105820209709755"]}, "Manager Pack 8 Jan '26": {"visto": "2026-08-18", "ids": ["105821283329596", "105821283398383"]}, "Trendyol Süper Lig Monthly MVPs Nov '25": {"visto": "2026-08-18", "ids": ["105797929505269", "105797929508495", "105797929510497", "105797929511902", "105797929523484", "105797929549672", "105797929574320", "106757049390076", "106757049395352", "106757049398637", "106757049455109"]}, "BYD SEALION 6 LEAGUE 1 Selection 8 Jan '26": {"visto": "2026-08-18", "ids": ["105812961846697", "105812961896944", "105812961899882", "105812961913458", "105812961943456", "105812961959414", "105812961965831", "106760807496569", "106760807508156", "106760807508595", "106760807527044"]}, "Spanish League Selection Midfielders 25 Dec '25": {"visto": "2026-08-18", "ids": ["105818867472646", "105818867478698", "105818867484407", "105818867487399", "105818867495993", "105818867499548", "105818867499664", "105818867523396"]}, "European Clubs Selection 1 Jan '26": {"visto": "2026-08-18", "ids": ["105819404279972", "105819404297484", "105819404298395", "105819404300031", "105819404342362", "105819404350776", "105819404350917", "105819404352559", "105819404353783", "105819404356221", "105819404356890", "105819404357987", "105819404365482", "105819404366870", "105819404371638", "105819404379784", "105819404381676", "105819404382561", "105819404390379", "105819404393844"]}, "J1 LEAGUE Selection 25 Dec '25": {"visto": "2026-08-18", "ids": ["105787191996791", "105787192000920", "105787192000979", "105787192043852", "105787192095213", "105787192104927", "105787192105742", "105787192105909"]}, "J.LEAGUE Monthly MVPs Nov & Dec '25": {"visto": "2026-08-18", "ids": ["105787460541296", "105787460562459", "105787460575263", "105787460579207", "106751680593884", "106751680685480", "106751680707727", "106751680752920"]}, "POTM Trendyol Süper Lig 18 Dec '25": {"visto": "2026-08-18", "ids": ["53980222827486", "53980222831744", "53980222837429", "53980222864942", "53980222875468", "53980222889904"]}, "European Clubs Selection Guardians 18 Dec '25": {"visto": "2026-08-18", "ids": ["105818330540099", "105818330556620", "105818330558492", "105818330603981", "105818330631822", "105818330638516", "105818330638643", "105818330652062"]}, "POTM J1 LEAGUE 18 Dec '25": {"visto": "2026-08-18", "ids": ["53980491168854", "53980491214674", "53980491275220", "53980491282228", "53980491305577", "53980491305616"]}, "Italian League Selection Attackers 15 Dec '25": {"visto": "2026-08-18", "ids": ["105818062169611", "105818062170821", "105818062180062", "105818062184295", "105818062194532", "105818062202555", "105818062215786", "105818062222700"]}, "J1 LEAGUE Selection 11 Dec '25": {"visto": "2026-08-18", "ids": ["105817793641408", "105817793687434", "105817793730915", "105817793747720", "105817793750254", "105817793751397", "105817793757187", "105817793758444", "105817793759295", "105817793763035", "105817793772214", "105817793804507"]}, "Manager Pack 4 Dec '25": {"visto": "2026-08-18", "ids": ["105821551760987", "105821551783546"]}, "J.LEAGUE Monthly MVPs Oct '25": {"visto": "2026-08-18", "ids": ["105786923565102", "105786923693191", "105786923709284", "106751412248068", "106751412275715", "106751412275975", "106751412284955"]}, "J1 LEAGUE Selection 27 Nov '25": {"visto": "2026-08-18", "ids": ["105786655174492", "105786655174630", "105786655215946", "105786655227900", "105786655248475", "105786655248689", "105786655250471", "105786655272920"]}, "POTM Trendyol Süper Lig 20 Nov '25": {"visto": "2026-08-18", "ids": ["53979417472149", "53979417516018", "53979417525662", "53979417527814", "53979417551553", "53979417555307"]}, "European Clubs Selection 20 Nov '25": {"visto": "2026-08-18", "ids": ["105810814347350", "105810814347723", "105810814405353", "105810814412205", "105810814413599", "105810814416060", "105810814418690", "105810814418822", "105810814422392", "105810814422427", "105810814422530", "105810814423407", "105810814430497", "105810814436409", "105810814436940", "105810814437726", "105810814439757", "105810814440300", "105810814442261", "105810814443914"]}, "POTM Brazilian League 20 Nov '25": {"visto": "2026-08-18", "ids": ["53979954319439", "53979954389105", "53979954390946", "53979954391083", "53979954411455", "53979954429677"]}, "English League Selection Midfielders 24 Nov '25": {"visto": "2026-08-18", "ids": ["105811082786248", "105811082853913", "105811082862937", "105811082864552", "105811082880361", "105811082880558", "105811082882144", "105811082893179"]}, "POTM J1 LEAGUE 20 Nov '25": {"visto": "2026-08-18", "ids": ["53979685863464", "53979685886060", "53979685951824", "53979685961466", "53979685962438", "53979685982303"]}, "National Teams Selection Midfielders 17 Nov '25": {"visto": "2026-08-18", "ids": ["105810545910381", "105810545914156", "105810545984866", "105810545989228", "105810546002239", "105810546011563", "105810546021708", "105810546041162"]}, "European Clubs Selection Guardians 13 Nov '25": {"visto": "2026-08-18", "ids": ["105809740607521", "105809740622198", "105809740669388", "105809740676520", "105809740683858", "105809740688234", "105809740702397", "105809740719809"]}, "J1 LEAGUE Selection 13 Nov '25": {"visto": "2026-08-18", "ids": ["105810277449226", "105810277449444", "105810277497101", "105810277554976", "105810277555062", "105810277557470", "105810277557508", "105810277562046", "105810277574593", "105810277577329", "105810277584211", "105810277597837"]}, "eFootball™ League Rewards Phase 4": {"visto": "2026-08-18", "ids": ["106764297101321"]}, "Windah Basudara Cup 2025": {"visto": "2026-08-18", "ids": ["105815646315111"]}, "Manager Pack 6 Nov '25": {"visto": "2026-08-18", "ids": ["105808666859047", "105808666925325"]}, "J1 LEAGUE Selection 30 Oct '25": {"visto": "2026-08-18", "ids": ["105786118300813", "105786118300976", "105786118366410", "105786118366418", "105786118368886", "105786118371015", "105786118377514", "105786118420784"]}, "J.LEAGUE Monthly MVPs Sep '25": {"visto": "2026-08-18", "ids": ["105786386817394", "105786386820635", "105786386845985", "105786386853230", "106751143834353", "106751143836110", "106751143847877", "106751143874825"]}, "Halloween Campaign 23 Oct '25": {"visto": "2026-08-18", "ids": ["105813767207337", "105813767216536", "105813767220842", "105813767251446"]}, "POTM J1 LEAGUE 23 Oct '25": {"visto": "2026-08-18", "ids": ["53978880557495", "53978880662530", "53978880671213", "53978880672730", "53978880679274", "53978880682230"]}, "Ay Yýldýz Kampanyasý 2025": {"visto": "2026-08-18", "ids": ["105805177223189", "105805177267809", "105805177272746", "105805177274641", "105805177280135", "105805177283757", "105805177290497", "105805177317196"]}, "POTM Brazilian League 23 Oct '25": {"visto": "2026-08-18", "ids": ["53979149037622", "53979149078372", "53979149081432", "53979149098815", "53979149103831", "53979149108805"]}, "Spanish League Selection Midfielders 20 Oct '25": {"visto": "2026-08-18", "ids": ["105807324704855", "105807324750779", "105807324753767", "105807324759377", "105807324770869", "105807324785955", "105807324796469", "105807324798719"]}, "Manchester United Challenge 16 Oct '25": {"visto": "2026-08-18", "ids": ["105815109314221"]}, "Eintracht Frankfurt Selection 9 Oct '25": {"visto": "2026-08-18", "ids": ["105811888089120", "105811888152065", "105811888180123", "105811888184681", "105811888187920", "105811888188206", "105811888216020", "105811888216496"]}, "Diwali Campaign 9 Oct '25": {"visto": "2026-08-18", "ids": ["105814304012236"]}, "eFootball™ League Rewards Phase 3": {"visto": "2026-08-18", "ids": ["106760539047830"]}, "J1 LEAGUE Selection 9 Oct '25": {"visto": "2026-08-18", "ids": ["105814572525970", "105814572528455", "105814572528460", "105814572531716", "105814572539061", "105814572541715", "105814572546854", "105814572553523", "105814572553537", "105814572558560", "105814572559753", "105814572560480"]}, "AFC Asian Qualifiers™ Selection 2 Oct '25": {"visto": "2026-08-18", "ids": ["105803616982111", "105803616990659", "105803617001401", "105803617001948", "105803617008511", "105803617018548", "105803617023877", "105803617049591"]}, "Manager Pack 2 Oct '25": {"visto": "2026-08-18", "ids": ["105785581409959", "105785581518626"]}, "Show Time 2 Oct '25": {"visto": "2026-08-18", "ids": ["106761612796044"]}, "Yu-Gi-Oh! Collaboration Campaign 25 Sep '25": {"visto": "2026-08-18", "ids": ["105795513523616", "105795513593982", "105795513640603", "105795781979167", "105795782029504", "105795782045409"]}, "J1 LEAGUE Selection 25 Sep '25": {"visto": "2026-08-18", "ids": ["105784507646140", "105784507751283", "105784507751454", "105784507753751", "105784507756430", "105784507764830", "105784507765038", "105784507770645"]}, "POTM Trendyol Süper Lig 25 Sep '25": {"visto": "2026-08-18", "ids": ["53977806911914", "53977806912067", "53977806915077", "53977806945857", "53977806958631", "53977806974331"]}, "J.LEAGUE Monthly MVPs Aug '25": {"visto": "2026-08-18", "ids": ["105784776167452", "105784776186866", "105784776238182", "105784776239780", "106750606941701", "106750606949077", "106750606958423", "106750607003913"]}, "POTM J1 LEAGUE 25 Sep '25": {"visto": "2026-08-18", "ids": ["53978075250776", "53978075295443", "53978075356629", "53978075359630", "53978075362033", "53978075392810"]}, "Low Screamer 18 Sep '25": {"visto": "2026-08-18", "ids": ["105784239234541", "105784239236536", "105784239240976", "105784239253913", "105784239255018", "105784239257632", "105784239301610", "105784239336323"]}, "J1 LEAGUE Selection 11 Sep '25": {"visto": "2026-08-18", "ids": ["105792560710057", "105792560710110", "105792560710125", "105792560750453", "105792560799226", "105792560799979", "105792560814975", "105792560815124", "105792560817368", "105792560823374", "105792560851703", "105792560861383"]}, "Manager Pack 4 Sep '25": {"visto": "2026-08-18", "ids": ["105782360264664", "105782360272490"]}, "Napoli A Selection 8 Sep '25": {"visto": "2026-08-18", "ids": ["105801419163926", "105801419173947", "105801419177629", "105801419179550", "105801419179901", "105801419181536", "105801419186024", "105801419193983"]}, "J1 LEAGUE Selection 28 Aug '25": {"visto": "2026-08-18", "ids": ["105781286465377", "105781286510085", "105781286525891", "105781286525892", "105781286532194", "105781286536393", "105781286539570", "105781286561840"]}, "National Team Selection Italy 1 Sep '25": {"visto": "2026-08-18", "ids": ["105781823382694", "105781823389843", "105781823393179", "105781823394819", "105781823397724", "105781823407692", "105781823415746", "105781823422580"]}, "Skill Up 2026": {"visto": "2026-08-18", "ids": ["105779139033853", "106747654053207"]}, "J1 LEAGUE Selection 15 Aug '25": {"visto": "2026-08-18", "ids": ["105792292274134", "105792292274369", "105792292274627", "105792292274647", "105792292274650", "105792292380148", "105792292380899", "105792292381889", "105792292386498", "105792292386505", "105792292401125", "105792292409156"]}, "POTM J1 LEAGUE 14 Aug '25 ": {"visto": "2026-08-18", "ids": ["53977269973985", "53977270049807", "53977270052064", "53977270054668", "53977270068715", "53977270087018"]}, "POTM Brazilian League 14 Aug '25": {"visto": "2026-08-18", "ids": ["53977538426792", "53977538476771", "53977538483722", "53977538486110", "53977538498333", "53977538498540"]}, "Starter Set 2026 ": {"visto": "2026-08-18", "ids": ["105775649319286", "105775649362662", "105775649371506"]}, "Startup Campaign 14 Aug '25": {"visto": "2026-08-18", "ids": ["105792829232390", "105792829240690", "105792829243366", "105792829246840", "105792829260920", "105792829271114"]}, "Step-up 2026": {"visto": "2026-08-18", "ids": ["105779407403191", "105779407483982", "105779407488096"]}, "National Team Selection India 14 Aug '25": {"visto": "2026-08-18", "ids": ["105791218663624", "105791218663639", "105791218670413", "105791218670415", "105791218681972"]}, "Leo Messi Edition 2026": {"visto": "2026-08-18", "ids": ["105775112422706", "105775112428610", "105775112429333", "105775112429394", "105775112429483", "105775112430189", "105775112432987", "105775112445731", "105775112445741", "105775112506252", "88037971205463"]}, "Highlight 9 Aug '25": {"visto": "2026-08-18", "ids": ["105793097669457", "105793097678196", "105793097690985"]}, "Highlight 11 Aug '25": {"visto": "2026-08-18", "ids": ["105793634561118", "105793634563371", "105793634575942"]}, "Highlight 10 Aug '25": {"visto": "2026-08-18", "ids": ["105793366107745", "105793366125347", "105793366130433"]}, "Japan Selection 4 Aug '25": {"visto": "2026-08-18", "ids": ["105787997307296", "105787997351767", "105787997414620", "105787997417357", "105787997423475", "105787997433666", "105787997442229", "105787997443130"]}, "J.LEAGUE Monthly MVPs Jun '25": {"visto": "2026-08-18", "ids": ["105770012150817", "105770012262215", "105770012262979", "105770012283302", "106746311998959", "106746312023283", "106746312026321", "106746312027375"]}, "J1 LEAGUE Selection 24 Jul '25": {"visto": "2026-08-18", "ids": ["105769743694749", "105769743790577", "105769743791177", "105769743807631", "105769743807763", "105769743844002", "105769743847622", "105769743847855"]}, "Summer Tour Campaign 24 Jul '25": {"visto": "2026-08-18", "ids": ["105791487063528", "105791487068135", "105791487089816", "105791487112890", "105791755495839", "105791755514424", "105791755534586", "105791755546317"]}, "European Clubs Selection Midfielders 21 Jul '25": {"visto": "2026-08-18", "ids": ["105768401564216", "105768401606485", "105768401610447", "105768401615452", "105768401618226", "105768401620633", "105768401626568", "105768401628928"]}, "National Teams Selection Guardians 14 Jul '25": {"visto": "2026-08-18", "ids": ["105762764401047", "105762764405552", "105762764465273", "105762764470008", "105762764475425", "105762764475689", "105762764475825", "105762764484202"]}, "eFootball Festival 30th Campaign 10 Jul '25": {"visto": "2026-08-18", "ids": ["105774575525207", "105774844115266"]}, "POTM J1 LEAGUE 10 Jul '25": {"visto": "2026-08-18", "ids": ["53976733118301", "53976733168543", "53976733171240", "53976733184765", "53976733185916", "53976733186799"]}, "National Teams Selection Attackers 10 Jul '25": {"visto": "2026-08-18", "ids": ["105763032835666", "105763032908342", "105763032925245", "105763032926389", "105763032928671", "105763032936523", "105763032936842", "105763032961977"]}, "J1 LEAGUE Selection 10 Jul '25": {"visto": "2026-08-18", "ids": ["105763301289712", "105763301336087", "105763301350238", "105763301350374", "105763301350471", "105763301362314", "105763301363735", "105763301368176", "105763301371787", "105763301387236", "105763301389505", "105763301391565"]}, "Epic Nostalgia 26 Jun '25": {"visto": "2026-08-18", "ids": ["105766522558696", "105766522560972", "105766522568126", "105766522570270", "105766522581222", "105766522601249", "105766522615283", "105766522620586", "88036897464767", "88037166026249", "88037434461671"]}, "J.LEAGUE Monthly MVPs May '25": {"visto": "2026-08-18", "ids": ["105767327776814", "105767327882311", "105767327901181", "105767327928611", "106744701366892", "106744701377557", "106744701380969", "106744701423881"]}, "J1 LEAGUE Selection 26 Jun '25": {"visto": "2026-08-18", "ids": ["105767059450220", "105767059452657", "105767059460191", "105767059466259", "105767059467804", "105767059477209", "105767059477367", "105767059477630"]}, "Trendyol Süper Lig 24-25 Season's Best": {"visto": "2026-08-18", "ids": ["105767596253180", "105767596256801", "105767596297711", "105767596310505", "105767596319410", "105767596322377", "105767596343215", "105767596366481", "106744969732202", "106744969733514", "106744969838454"]}, "POTM Brazilian League 12 Jun '25": {"visto": "2026-08-18", "ids": ["53975659423854", "53975659427009", "53975659430005", "53975659436466", "53975659476038", "53975659483693"]}, "J1 LEAGUE Selection 12 Jun '25": {"visto": "2026-08-18", "ids": ["105764911880245", "105764911952371", "105764911962944", "105764911962990", "105764911963196", "105764911965508", "105764911970058", "105764911976844", "105764911979077", "105764911984696", "105764911993500", "105764912016013"]}, "Show Time 13 Jun '25": {"visto": "2026-08-18", "ids": ["106748727910680"]}, "National Teams Selection Attackers 9 Jun '25": {"visto": "2026-08-18", "ids": ["105763838219867", "105763838231672", "105763838239241", "105763838240516", "105763838241664", "105763838245476", "105763838251148", "105763838251446"]}, "Japanese Stars 5 Jun '25": {"visto": "2026-08-18", "ids": ["105764106657450", "105764106659019", "105764106661812", "105764106663682", "105764106668322", "105764106670178", "105764106670426", "105764106674627", "106752217464922", "106752217564110", "106752217570149"]}, "Highlight 7 Jun '25": {"visto": "2026-08-18", "ids": ["105789607945901", "105789607960585", "105789608006652"]}, "National Team Selection Indonesia 29 May '25": {"visto": "2026-08-18", "ids": ["105771941558274", "105771941650392", "105771941659811"]}, "J.LEAGUE Monthly MVPs Apr '25": {"visto": "2026-08-18", "ids": ["105757127355931", "105757127365557", "105757127372679", "105757127373668", "106740943280920", "106740943281173", "106740943282007", "106740943305465"]}, "National Team Selection England 29 May '25": {"visto": "2026-08-18", "ids": ["105773501823159", "105773501889277", "105773501903416", "105773501914028", "105773501935309"]}, "J1 LEAGUE Selection 29 May '25": {"visto": "2026-08-18", "ids": ["105756858793946", "105756858885131", "105756858899323", "105756858899468", "105756858904836", "105756858909717", "105756858910853", "105756858913050"]}, "National Team Pack Belgium '25": {"visto": "2026-08-18", "ids": ["105749879495866", "105749879500123", "105749879500127", "105749879575444", "105749879581114", "105749879583260", "105749879589214", "105749879590676", "105749879594345", "105749879599144", "105749879603202"]}, "National Team Pack Italy '25": {"visto": "2026-08-18", "ids": ["105750147998886", "105750147999296", "105750147999479", "105750148005824", "105750148006298", "105750148008170", "105750148009371", "105750148013916", "105750148024878", "105750148031765", "105750148038772"]}, "European Clubs Selection [8 Anniv.]": {"visto": "2026-08-18", "ids": ["105773770314732", "105773770327933", "105773770339609"]}, "J1 LEAGUE Selection 15 May '25": {"visto": "2026-08-18", "ids": ["105758469451650", "105758469512061", "105758469512064", "105758469512195", "105758469518153", "105758469519067", "105758469519864", "105758469531589", "105758469533612", "105758469542597", "105758469555558", "105758469561173"]}, "POTM Trendyol Süper Lig 15 May '25": {"visto": "2026-08-18", "ids": ["53975390924870", "53975390926608", "53975390990647", "53975390998101", "53975391002891", "53975391014911"]}, "Highlight 15 May '25": {"visto": "2026-08-18", "ids": ["105778602058578", "105778602150870", "105778618888477"]}, "European Clubs Selection 1 May '25": {"visto": "2026-08-18", "ids": ["105760348479253", "105760348479465", "105760348483884", "105760348547455", "105760348551866", "105760348579468", "105760348590341", "105760348591436"]}, "J1 LEAGUE Selection 1 May '25": {"visto": "2026-08-18", "ids": ["105760080109641", "105760080124677", "105760080131173", "105760080136854", "105760080138205", "105760080144318", "105760080162719", "105760080163070"]}, "Italian League Selection Midfielders 12 May '25": {"visto": "2026-08-18", "ids": ["105759006364195", "105759006372386", "105759006383512", "105759006400906", "105759006402460", "105759006404011", "105759006405197", "105759006418866"]}, "European Clubs Selection Midfielders 5 May '25": {"visto": "2026-08-18", "ids": ["105759543233775", "105759543239641", "105759543242768", "105759543250476", "105759543258774", "105759543270155", "105759543272809", "105759543287156"]}, "European Clubs Selection Attackers 8 May '25": {"visto": "2026-08-18", "ids": ["105759274757626", "105759274760620", "105759274810720", "105759274813455", "105759274822868", "105759274830255", "105759274831498", "105759274844653"]}, "J.LEAGUE Monthly MVPs Feb & Mar '25": {"visto": "2026-08-18", "ids": ["105760885437790", "105760885449152", "105760885462322", "105760885474042", "106742285444520", "106742285461861", "106742285461863", "106742285470471"]}, "Coppa eFootball™ Italia 2025": {"visto": "2026-08-18", "ids": ["105754442973134", "105754442977240", "105754442991180", "105754442999509"]}, "Brazil Selection 28 Apr '25": {"visto": "2026-08-18", "ids": ["105750416370761", "105750416431149", "105750416442707", "105750416442867", "105750416452753", "105750416455640", "105750416470223", "105750416480873"]}, "AFC Champions League Elite™ Selection 17 Apr '25": {"visto": "2026-08-18", "ids": ["105760633690164", "105760633752320", "105760633769191", "105760633770699", "105760633773690", "105760633779663", "105760633817586", "105760633821825"]}, "Spanish League Selection Attackers 17 Apr '25": {"visto": "2026-08-18", "ids": ["105751758610714", "105751758614994", "105751758641952", "105751758641962", "105751758651168", "105751758651661", "105751758661408", "105751758670154"]}, "POTM Trendyol Süper Lig 17 Apr '25": {"visto": "2026-08-18", "ids": ["53974585681674", "53974585694478", "53974585704193", "53974585707888", "53974585713534", "53974585717149"]}, "POTM J1 LEAGUE 17 Apr '25": {"visto": "2026-08-18", "ids": ["53974317154351", "53974317245864", "53974317246406", "53974317259616", "53974317259841", "53974317269209"]}, "National Teams Selection Guardians 21 Apr '25": {"visto": "2026-08-18", "ids": ["105750953242657", "105750953244854", "105750953306692", "105750953308848", "105750953310849", "105750953323994", "105750953329955", "105750953331318"]}, "European Clubs Selection Guardians 14 Apr '25": {"visto": "2026-08-18", "ids": ["105752026984536", "105752027048515", "105752027073919", "105752027082220", "105752027086308", "105752027091247", "105752027091662", "105752027102403"]}, "Songkran Campaign 10 Apr '25": {"visto": "2026-08-18", "ids": ["105755516657419"]}, "European Clubs Selection 7 Apr '25": {"visto": "2026-08-18", "ids": ["105753100715857", "105753100716145", "105753100717934", "105753100722087", "105753100724291", "105753100727039", "105753100794895", "105753100808400"]}, "J1 LEAGUE Selection 3 Apr '25": {"visto": "2026-08-18", "ids": ["105753369133124", "105753369178009", "105753369218783", "105753369238321", "105753369238356", "105753369238363", "105753369245386", "105753369251865", "105753369268893", "105753369279357"]}, "European Clubs Selection 31 Mar '25": {"visto": "2026-08-18", "ids": ["105747195160642", "105747195201804", "105747195203943", "105747195204304", "105747195228811", "105747195239189", "105747195242676", "105747195254071"]}, "POTM J1 LEAGUE 20 Mar '25": {"visto": "2026-08-18", "ids": ["53974048718964", "53974048824398", "53974048843800", "53974048855346", "53974048862998", "53974048863741"]}, "American League International Stars 20 Mar '25": {"visto": "2026-08-18", "ids": ["105741289529726", "105741289558040", "105741289559779", "105741289567096", "105741289567387", "105741289643137"]}, "POTM Trendyol Süper Lig 20 Mar '25": {"visto": "2026-08-18", "ids": ["53973780328056", "53973780330517", "53973780369918", "53973780373772", "53973780390584", "53973780394621"]}, "National Teams Selection Attackers 24 Mar '25": {"visto": "2026-08-18", "ids": ["105745584596060", "105745584608148", "105745584608283", "105745584614797", "105745584616470", "105745584620557", "105745584625448", "105745584629049"]}, "National Team Selection Japan 20 Mar '25": {"visto": "2026-08-18", "ids": ["105746389903303", "105746389910475", "105746389910478", "105746389916676", "105746389916680", "105746389921676", "105746389921781", "105746389930431"]}, "National Teams Selection Midfielders 17 Mar '25": {"visto": "2026-08-18", "ids": ["105746121407146", "105746121420288", "105746121462275", "105746121468461", "105746121476923", "105746121499900", "105746121518680", "105746121529738"]}, "POTW 13 Mar '25": {"visto": "2026-08-18", "ids": ["52882321743034", "52882321749778", "52882321761415", "52882321764439", "52882321804009", "52882321815016", "52882321819487", "52882321822819", "52882321823221", "52882321829830", "52882321830129"]}, "Internazionale Milano Pack 6 Mar '25": {"visto": "2026-08-18", "ids": ["105738605203219", "105738605207467", "105738605267689", "105738605270278", "105738605271344", "105738605274661", "105738605275249", "105738605278578", "105738605281254", "105738605281427", "105738605289299"]}, "Guess the Winner Campaign 6 Mar '25": {"visto": "2026-08-18", "ids": ["105742363366380", "105742363389665", "105742363390520", "105749611125092", "105749611140177", "105749611161509"]}, "Holi Campaign 6 Mar '25": {"visto": "2026-08-18", "ids": ["106740138000583"]}, "POTW 6 Mar '25": {"visto": "2026-08-18", "ids": ["52882053310012", "52882053314985", "52882053327902", "52882053376425", "52882053376440", "52882053381425", "52882053391485", "52882053394972", "52882053420384", "52882053422916", "52882053432338"]}, "Internazionale Milano Selection 6 Mar '25": {"visto": "2026-08-18", "ids": ["105738605206528"]}, "J.LEAGUE Selection 6 Mar '25": {"visto": "2026-08-18", "ids": ["105748268859461", "105748268902730", "105748268954098", "105748268964820", "105748268965458", "105748268967209", "105748268969739", "105748268971839", "105748268973207", "105748268973551", "105748268978204", "105748268978261", "105748268978269", "105748268978272", "105748268978385", "105748268978523", "105748268986213", "105748268987526", "105748268987635", "105748268989109", "105748268989110", "105748268989866", "105748268991043", "105748268994524", "105748268995905", "105748269002122", "105748269011173", "105748269011389", "105748269016166", "105748269016399"]}, "Windah Basudara Campaign Vol. 2": {"visto": "2026-08-18", "ids": ["105734578807399", "105755785208423"]}, "European Clubs Selection Guardians 3 Mar '25": {"visto": "2026-08-18", "ids": ["105738336839085", "105738336841133", "105738336849792", "105738336851870", "105738336854856", "105738336862405", "105738336866520", "105738336869455"]}, "J1 LEAGUE Selection 27 Feb '25": {"visto": "2026-08-18", "ids": ["105738068312055", "105738068356992", "105738068417346", "105738068417523", "105738068417538", "105738068429061", "105738068431296", "105738068452502", "105738068455385", "105738068455418"]}, "Özel Başlangıç Paketi: Türkiye 27 Feb '25": {"visto": "2026-08-18", "ids": ["105748537381030", "105748537401624", "105748537402056", "106739064275997"]}, "FC Bayern München Selection 20 Feb '25": {"visto": "2026-08-18", "ids": ["105736994684063"]}, "Brazil Selection 24 Feb '25": {"visto": "2026-08-18", "ids": ["105737531536576", "105737531542949", "105737531545090", "105737531546044", "105737531551285", "105737531559809", "105737531568612", "105737531576285"]}, "European Clubs Selection 20 Feb '25": {"visto": "2026-08-18", "ids": ["105737263103645", "105737263116828", "105737263121905", "105737263121928", "105737263122965", "105737263126457", "105737263135777", "105737263154155"]}, "Trendyol Süper Lig Selection 20 Feb '25": {"visto": "2026-08-18", "ids": ["105721962205545", "105721962277852", "105721962286893", "105721962289303", "105721962289399", "105721962310542", "105721962320492", "105721962325526"]}, "FC Bayern München Pack 20 Feb '25": {"visto": "2026-08-18", "ids": ["105736994587041", "105736994601143", "105736994613691", "105736994614236", "105736994614740", "105736994663396", "105736994670511", "105736994677963", "105736994683225", "105736994683817", "105736994716019"]}, "AFC Champions League™ Selection 13 Feb '25": {"visto": "2026-08-18", "ids": ["105735669215105", "105735669215506", "105735669215517", "105735669256549", "105735669257297", "105735669276285", "105735669310103", "105735669316955", "105735669317278", "105735669323830"]}, "POTM Trendyol Süper Lig 13 Feb '25": {"visto": "2026-08-18", "ids": ["53973511891100", "53973511931817", "53973511943636", "53973511948223", "53973511984697", "53973512003504"]}, "European Clubs Selection Attackers 10 Feb '25": {"visto": "2026-08-18", "ids": ["105736726178197", "105736726179721", "105736726222012", "105736726226004", "105736726232192", "105736726235110", "105736726271328", "105736726277604"]}, "Captain Tsubasa Collaboration Campaign 30 Jan '25": {"visto": "2026-08-18", "ids": ["105739410513312", "105739678968863", "105739679019668", "105739679020520", "105739679021481", "105739947454516", "105739947505420"]}, "National Teams Selection Attackers 30 Jan '25": {"visto": "2026-08-18", "ids": ["105743973923017", "105743973936277", "105743973983324", "105743973983808", "105743974006483", "105743974008735", "105743974017867", "105743974020152"]}, "Trendyol Süper Lig Selection 23 Jan '25": {"visto": "2026-08-18", "ids": ["105741557993335", "105741557995889", "105741557998986", "105741558015299", "105741558064470", "105741558066188", "105741558067303", "105741558077648"]}, "European Clubs Selection Midfielders 16 Jan '25": {"visto": "2026-08-18", "ids": ["105728941549723", "105728941601980", "105728941604229", "105728941609782", "105728941616686", "105728941616746", "105728941624934", "105728941642810"]}, "Italian League Selection Attackers 20 Jan '25": {"visto": "2026-08-18", "ids": ["105729209960445", "105729209968726", "105729210039779", "105729210043028", "105729210043865", "105729210049868", "105729210067847", "105729210085217"]}, "Lunar New Year Campaign 16 Jan '25": {"visto": "2026-08-18", "ids": ["105735115623457", "105735115639341", "105735115664404"]}, "Manchester United Selection 16 Jan '25": {"visto": "2026-08-18", "ids": ["105708808940305"]}, "POTM Trendyol Süper Lig 9 Jan '25": {"visto": "2026-08-18", "ids": ["53972975019285", "53972975021091", "53972975064245", "53972975068319", "53972975068769", "53972975106864"]}, "National Teams Selection Guardians 9 Jan '25": {"visto": "2026-08-18", "ids": ["105728136231330", "105728136284107", "105728136287359", "105728136293437", "105728136293657", "105728136301452", "105728136325869", "105728136341122"]}, "AFC Asian Qualifiers™ Selection 9 Jan '25": {"visto": "2026-08-18", "ids": ["105735434332357", "105735434384023", "105735434384407", "105735434387440", "105735434396886", "105735434402489", "105735434403103", "105735434418350"]}, "J.LEAGUE Monthly MVPs Nov & Dec '24": {"visto": "2026-08-18", "ids": ["105725720404657", "105725720410946", "106733427027795", "106733427072516", "106733427081931", "106733427090746"]}, "Trendyol Süper Lig Selection 26 Dec '24": {"visto": "2026-08-18", "ids": ["105726794046638", "105726794047594", "105726794053688", "105726794063553", "105726794120606", "105726794127611", "105726794133122", "105726794137947"]}, "European Clubs Selection Guardians 30 Dec '24": {"visto": "2026-08-18", "ids": ["105727062545543", "105727062546308", "105727062576396", "105727062577498", "105727062580468", "105727062581882", "105727062597441", "105727062607271"]}, "European Clubs Selection 1 Jan '25": {"visto": "2026-08-18", "ids": ["105727599346994", "105727599353018", "105727599373137", "105727599426149", "105727599426573", "105727599426865", "105727599427006", "105727599428124", "105727599428150", "105727599432047", "105727599432589", "105727599436617", "105727599439965", "105727599442939", "105727599446574", "105727599453203", "105727599453766", "105727599453904", "105727599456219", "105727599460905"]}, "National Team Pack Netherlands '24": {"visto": "2026-08-18", "ids": ["105730283712296", "105730283727222", "105730283781167", "105730283785388", "105730283786104", "105730283789468", "105730283794525", "105730283799612", "105730283799613", "105730283803640", "105730283804124"]}, "2024 J.LEAGUE AWARDS": {"visto": "2026-08-18", "ids": ["105725988716738", "105725988739180", "105725988757567", "105725988761426", "105725988808972", "105725988815821", "105725988818659", "105725988822002", "105725988868384", "106733695463251", "106733695508536", "106733695550019", "106733695560490"]}, "J1 LEAGUE Selection 26 Dec '24": {"visto": "2026-08-18", "ids": ["105725451845963", "105725451846047", "105725451886642", "105725451933714", "105725451950958", "105725451951129", "105725451954578", "105725451963756", "105725451982130", "105725451989088"]}, "Spanish League Selection Guardians 6 Jan '25": {"visto": "2026-08-18", "ids": ["105728404657899", "105728404726222", "105728404730026", "105728404730360", "105728404738397", "105728404746835", "105728404781151", "105728404781869"]}, "English League Selection Attackers 19 Dec '24": {"visto": "2026-08-18", "ids": ["105726257176402", "105726257246482", "105726257257603", "105726257262730", "105726257263335", "105726257268883", "105726257298622", "105726257307882"]}, "POTS Brazilian League 2024": {"visto": "2026-08-18", "ids": ["55068191664018", "55068191664814", "55068191678538", "55068191681321", "55068191681716", "55068191723347", "55068191726418", "55068191727749", "55068191728391", "55068191729570", "55068191731679", "55068191732528", "55068191732542", "55068191740228", "55068191741239", "55068191742314", "55068191748994", "55068191749188", "55068191772970", "55068191781270"]}, "AC Milan Selection 12 Dec '24": {"visto": "2026-08-18", "ids": ["105724915068893", "105724915070440", "105724915071401", "105724915071402", "105724915085056", "105724915096383", "105724915123072", "105724915127782"]}, "Spanish League Selection Midfielders 16 Dec '24": {"visto": "2026-08-18", "ids": ["105725183498087", "105725183498502", "105725183512165", "105725183521369", "105725183532121", "105725183538229", "105725183546700", "105725183555340"]}, "POTM Trendyol Süper Lig 5 Dec '24": {"visto": "2026-08-18", "ids": ["53972169700651", "53972169701927", "53972169711612", "53972169759017", "53972169780490", "53972169822725"]}, "National Team Selection Germany 5 Dec '24": {"visto": "2026-08-18", "ids": ["105721156975233", "105721156976458", "105721156979731", "105721157004099", "105721157004163", "105721157004189", "105721157004190", "105721157007958"]}, "National Team Selection Malaysia Dec '24": {"visto": "2026-08-18", "ids": ["105720620104280", "105720620120868", "105720620120869", "105720620120872", "105720620120882", "105720620126824", "105720620136481", "105720620147338", "105720620147341", "105720620157122", "105720620157124"]}, "National Team Selection Thailand Dec '24": {"visto": "2026-08-18", "ids": ["105720083177227", "105720083180106", "105720083231800", "105720083242617", "105720083242618", "105720083245678", "105720083245679", "105720083245683", "105720083245759", "105720083249016", "105720083268275"]}, "National Team Selection Indonesia Dec '24": {"visto": "2026-08-18", "ids": ["105720401995172", "105720402006996", "105720402018480", "105720402023668", "105720402042840", "105720402043539", "105720402043541", "105720402043556", "105720402052259", "105720402053251", "105720402054654"]}, "China PR 2001": {"visto": "2026-08-18", "ids": ["88035287009271"]}, "POTM J1 LEAGUE 5 Dec '24": {"visto": "2026-08-18", "ids": ["53971901233913", "53971901341353", "53971901347606", "53971901354012", "53971901354080", "53971901365058"]}, "POTM Brazilian League 5 Dec '24": {"visto": "2026-08-18", "ids": ["53972438150385", "53972438196341", "53972438199796", "53972438208372", "53972438241522", "53972438250651"]}, "J1 LEAGUE Selection 5 Dec '24": {"visto": "2026-08-18", "ids": ["105721693738090", "105721693749721", "105721693792588", "105721693794032", "105721693794200", "105721693848529", "105721693854548", "105721693857028", "105721693857045", "105721693872497"]}, "Trendyol Süper Lig Selection 28 Nov '24": {"visto": "2026-08-18", "ids": ["105719277861302", "105719277918372", "105719277923082", "105719277939500", "105719277946310", "105719277946966", "105719277946999", "105719277986304"]}, "AC Milan Selection 28 Nov '24": {"visto": "2026-08-18", "ids": ["105719546371221"]}, "Italian League Selection Guardians 2 Dec '24": {"visto": "2026-08-18", "ids": ["105712030093217", "105712030167098", "105712030173053", "105712030184926", "105712030194214", "105712030203524", "105712030213622", "105712030218363"]}, "AC Milan Pack 28 Nov '24": {"visto": "2026-08-18", "ids": ["105719546292310", "105719546309663", "105719546353938", "105719546360468", "105719546363808", "105719546365927", "105719546367490", "105719546368369", "105719546376274", "105719546387608", "105719546389548"]}, "J1 LEAGUE Selection 21 Nov '24": {"visto": "2026-08-18", "ids": ["105717398781682", "105717398782020", "105717398872915", "105717398879994", "105717398888019", "105717398889678", "105717398889789", "105717398894460", "105717398900945", "105717398906899"]}, "English League Selection Midfielders 25 Nov '24": {"visto": "2026-08-18", "ids": ["105718741060765", "105718741061273", "105718741069357", "105718741071542", "105718741083497", "105718741086114", "105718741090861", "105718741096058"]}, "Collaboration Campaign FC Tokyo 2024": {"visto": "2026-08-18", "ids": ["105703977146082", "105703977147634", "105703977149001", "105703977149002", "105703977153380", "105703977154871"]}, "J.LEAGUE Monthly MVPs Oct '24": {"visto": "2026-08-18", "ids": ["105717667369301", "106732890153023", "106732890208981", "106732890224447", "106732890247823"]}, "FC Barcelona Selection 21 Nov '24": {"visto": "2026-08-18", "ids": ["105718472670439"]}, "FC Barcelona Pack 21 Nov '24": {"visto": "2026-08-18", "ids": ["105718472547394", "105718472552682", "105718472618036", "105718472618176", "105718472618294", "105718472623970", "105718472624143", "105718472633729", "105718472640549", "105718472654625", "105718472661201"]}, "FC Barcelona MSN 21 Nov '24": {"visto": "2026-08-18", "ids": ["105717935675047", "105717935675048", "105717935676905", "105717935679348", "105717935679372", "105717935698152", "105717935737551", "105717935738896"]}, "National Team Selection Uzbekistan Nov '24": {"visto": "2026-08-18", "ids": ["105714496366255", "105714496367612", "105714496412193", "105714496413325", "105714496413327", "105714496413366", "105714496418839", "105714496429679", "105714496451999", "105714496452558", "105714496461675"]}, "National Team Selection Iraq Nov '24": {"visto": "2026-08-18", "ids": ["105714227917715", "105714227988030", "105714227995100", "105714228008597", "105714228017326", "105714228019747", "105714228029113", "105714228037842", "105714228039231", "105714228039234", "105714228039235"]}, "Brazilian League Selection 14 Nov '24": {"visto": "2026-08-18", "ids": ["105716861898695", "105716861935063", "105716861942112", "105716862024716", "105716862026680", "105716862038298", "105716862045797", "105716862046805"]}, "National Team Selection Japan Nov '24": {"visto": "2026-08-18", "ids": ["105713959452762", "105713959453088", "105713959497559", "105713959542273", "105713959544775", "105713959551947", "105713959558152", "105713959558826", "105713959563148", "105713959569267", "105713959571903"]}, "J1 LEAGUE Selection 7 Nov '24": {"visto": "2026-08-18", "ids": ["105716325040216", "105716325040274", "105716325062700", "105716325069988", "105716325085066", "105716325139145", "105716325145525", "105716325149072", "105716325150476", "105716325175913"]}, "POTM J1 LEAGUE 7 Nov '24": {"visto": "2026-08-18", "ids": ["53971095928989", "53971095929026", "53971095969855", "53971096021260", "53971096027421", "53971096047645"]}, "Collaboration Campaign Kashima Antlers 2024": {"visto": "2026-08-18", "ids": ["105704513925005", "105704513999219", "105704514006555", "105704514023385"]}, "POTM Brazilian League 7 Nov '24": {"visto": "2026-08-18", "ids": ["53971632830285", "53971632842115", "53971632912319", "53971632929535", "53971632950441", "53971632951325"]}, "POTM Trendyol Süper Lig 7 Nov '24": {"visto": "2026-08-18", "ids": ["53971364450150", "53971364456870", "53971364465320", "53971364467045", "53971364490069", "53971364494601"]}, "National Team Selection Netherlands 11 Nov '24": {"visto": "2026-08-18", "ids": ["105716593495488", "105716593506079", "105716593562342", "105716593571186", "105716593575218", "105716593577848", "105716593591357", "105716593601328"]}, "POTW European Club Championship 31 Oct '24": {"visto": "2026-08-18", "ids": ["52876147704224", "52876147790832", "52876147798068", "52876147801446", "52876147805698", "52876147807117", "52876147814349", "52876147819942", "52876147820316", "52876147820403", "52876147825415"]}, "POTW 31 Oct '24": {"visto": "2026-08-18", "ids": ["52875879291970", "52875879299183", "52875879363954", "52875879365928", "52875879369055", "52875879371109", "52875879383254", "52875879385438", "52875879392198", "52875879394494", "52875879416861"]}, "National Team Selection India 24 Oct '24": {"visto": "2026-08-18", "ids": ["105731089121479", "105731089121480", "105731089121489", "105731089121491", "105731089128271"]}, "English League Selection Attackers 28 Oct '24": {"visto": "2026-08-18", "ids": ["105710151112749", "105710151112936", "105710151123064", "105710151126172", "105710151126263", "105710151135181", "105710151136043", "105710151140408"]}, "Arsenal FC Selection 24 Oct '24": {"visto": "2026-08-18", "ids": ["105711761753510"]}, "Arsenal FC Pack 24 Oct '24": {"visto": "2026-08-18", "ids": ["105711761722512", "105711761722607", "105711761724396", "105711761729951", "105711761735036", "105711761735498", "105711761740692", "105711761747681", "105711761748536", "105711761753147", "105711761754670"]}, "J1 LEAGUE Selection 24 Oct '24": {"visto": "2026-08-18", "ids": ["105710956331162", "105710956331425", "105710956353650", "105710956374346", "105710956435415", "105710956436233", "105710956441855", "105710956445153", "105710956454291", "105710956485276"]}, "AFC Champions League Elite™ Selection 17 Oct '24": {"visto": "2026-08-18", "ids": ["105714731229456", "105714731245528", "105714731247249", "105714731249491", "105714731293253", "105714731300291", "105714731310713", "105714731315275", "105714731324008", "105714731354319", "105714731354543"]}, "Brazilian League Selection 17 Oct '24": {"visto": "2026-08-18", "ids": ["105710419486167", "105710419486610", "105710419488332", "105710419502477", "105710419548206", "105710419576386", "105710419588573", "105710419603862"]}, "National Teams Selection Guardians 21 Oct '24": {"visto": "2026-08-18", "ids": ["105719814785730", "105719814801029", "105719814807796", "105719814826202", "105719814826849", "105719814826908", "105719814827500", "105719814837809"]}, "National Team Selection Korea Republic Oct '24": {"visto": "2026-08-18", "ids": ["105713691016803", "105713691043895", "105713691065767", "105713691110251", "105713691117126", "105713691123286", "105713691123292", "105713691124225", "105713691127257", "105713691131167", "105713691136576"]}};
(function(){
 var ATIVA=new Set(BOXATIVA),ORDEM={},modo=0;
 var botao=null,espera=null,montado=false,tentativas=0,aposRenderPendente=false;
 var MAX_TENTATIVAS=20;
 for(var i=0;i<BOXATIVA.length;i++) ORDEM[BOXATIVA[i]]=i;
 function nome(el){var n=el.querySelector(".hboxn");return n?n.textContent.trim():"";}
 function dt(n){ var H=(typeof BOXHIST!=="undefined")?BOXHIST:{};
   return (H[n]&&H[n].visto)||(typeof BOXDT!=="undefined"&&BOXDT[n])||""; }
 function pinta(){
  var b=document.getElementById("boxbt");
  if(!b) return;
  b.textContent = modo ? "← voltar às ativas" : "▦ boxes anteriores";
  b.style.borderColor = modo ? "#f0a531" : "";
  b.style.color = modo ? "#f0a531" : "";
 }
 function aplica(){
  window._t6box=!!modo;
  var w=document.getElementById("homewrap"); if(!w) return;
  var sec=w.querySelector(".hbloco"); if(!sec) return;
  var bx=Array.prototype.slice.call(sec.getElementsByClassName("hbox"));
  if(!bx.length) return;
  var mostra=[], n=0;
  for(var i=0;i<bx.length;i++){
   var nm=nome(bx[i]), a=ATIVA.has(nm);
   var ver=(modo===0)?a:!a;
   var _d=ver?"":"none";
   if(bx[i].style.display!==_d) bx[i].style.display=_d;
   if(ver){ mostra.push([bx[i],nm]); n++; }
  }
  // ordem: ativas na ordem do efHub · anteriores da mais nova para a mais velha
  mostra.sort(function(x,y){
   if(modo===0) return (ORDEM[x[1]]===undefined?999:ORDEM[x[1]])-(ORDEM[y[1]]===undefined?999:ORDEM[y[1]]);
   return (dt(y[1])||"").localeCompare(dt(x[1])||"");
  });
  var pai=mostra.length?mostra[0][0].parentNode:null;
  var _ord=mostra.map(function(x){return x[1];}).join("|");
  if(pai && _ord!==window._t6ordBox){ window._t6ordBox=_ord;
   for(var k=0;k<mostra.length;k++) pai.appendChild(mostra[k][0]); }
  var sb=sec.querySelector(".hsub");
  var _tx = modo
   ? (n+" box"+(n===1?"":"es")+" encerrada"+(n===1?"":"s")+" · top 3 de cada uma")
   : (n+" box"+(n===1?"":"es")+" ativa"+(n===1?"":"s")+" · top 3 de cada uma");
  if(sb && sb.textContent!==_tx) sb.textContent=_tx;
  var h2=sec.querySelector(".htt h2");
  var _h2 = modo ? "Boxes anteriores" : "Lançamentos";
  if(h2 && !window._t6abaBox && h2.textContent!==_h2) h2.textContent=_h2;
  pinta();
 }
 function cancelaEspera(){if(espera!==null){clearTimeout(espera);espera=null;}}
 function aoClicar(){
  modo=modo?0:1;aplica();
  var w=document.getElementById("homewrap");
  if(w)w.scrollIntoView({behavior:"smooth",block:"start"});
 }
 function tentaMontar(){
  cancelaEspera();
  if(!montado)return false;
  var existente=document.getElementById("boxbt");
  if(existente){botao=existente;pinta();aplica();return true;}
  var alvo=document.getElementById("fbt");
  if(!alvo){
   if(tentativas++<MAX_TENTATIVAS)espera=setTimeout(tentaMontar,250);
   return false;
  }
  var b=document.createElement("button");b.id="boxbt";b.dataset.t6Owner="bloco14";b.className=alvo.className;
  b.style.cssText="display:inline-block;margin-left:8px";
  b.title="alterna entre as campanhas no ar e as ja encerradas";
  b.addEventListener("click",aoClicar);
  var ref=document.getElementById("condflut")||alvo;
  ref.parentNode.insertBefore(b, ref.nextSibling);
  botao=b;pinta();aplica();return true;
 }
 function mount(){
  if(montado)return tentaMontar();
  montado=true;tentativas=0;return tentaMontar();
 }
 function refresh(){return montado?tentaMontar():false;}
 function dispose(){
  montado=false;cancelaEspera();tentativas=0;aposRenderPendente=false;
  if(botao&&botao.dataset&&botao.dataset.t6Owner==="bloco14"){
   botao.removeEventListener("click",aoClicar);
   if(botao.parentNode)botao.parentNode.removeChild(botao);
  }
  botao=null;return true;
 }
 function atualizaDepoisDoRender(){
  if(aposRenderPendente)return;
  aposRenderPendente=true;
  Promise.resolve().then(function(){
   aposRenderPendente=false;
   if(montado)refresh();
  });
 }
 window.boxModo=function(m){
  modo=m?1:0;window._t6box=!!modo;aplica();atualizaDepoisDoRender();
 };
 window.T6Bloco14=Object.freeze({mount:mount,refresh:refresh,dispose:dispose,
  inspect:function(){return{mounted:montado,pending:espera!==null,attempts:tentativas,mode:modo,hasButton:!!botao};}});
 mount();
})();
}


/* bloco JavaScript 15 */

(function(){
 var barra=null,espera=null,relogio=null,montado=false,tentativas=0;
 var MAX_TENTATIVAS=20;
 function buildsPublicadas(){
  try{return (D||[]).filter(function(c){return !!(c&&c.__cn&&c.__cn.generationId
    &&c.__cn.cardId!=null&&c.__cn.functionId!=null);}).length;}
  catch(e){return 0;}
 }
 function numeroCards(){
  try{
   var vistos={};(D||[]).forEach(function(c){
    if(c&&c.__cn&&c.__cn.cardId)vistos[String(c.__cn.cardId)]=1;
   });
   return Object.keys(vistos).length;
  }catch(e){return 0;}
 }
 function conteudo(){
  var bloqueio=_t6BloqueioBuildsElenco();
  if(bloqueio)return '<span style="color:#d99a45">Builds indisponíveis'
   +(bloqueio.codigo==='PUBLICACAO_BUILD_INDISPONIVEL'?' · contrato final ausente':'')+'</span>';
  var builds=buildsPublicadas(),cards=numeroCards();
  if(!builds)return '<span style="color:#d99a45">Aguardando builds publicadas</span>';
  return '<span id="buildtxt" style="color:#22c58b">'+builds.toLocaleString('pt-BR')+'</span> builds publicadas'
   +' &nbsp;·&nbsp; <span id="cardtxt" style="color:#22c58b">'+cards.toLocaleString('pt-BR')+'</span> cards';
 }
 function cancelaEspera(){if(espera!==null){clearTimeout(espera);espera=null;}}
 function iniciaRelogio(){
  if(_t6BloqueioBuildsElenco())return;
  if(relogio===null)relogio=setInterval(atualiza,1000);
 }
 function tentaMontar(){
  cancelaEspera();
  if(!montado)return false;
  var existente=document.getElementById("contbar");
  if(existente){barra=existente;atualiza();iniciaRelogio();return true;}
  var h=document.querySelector("header h1");
  if(!h){
   if(tentativas++<MAX_TENTATIVAS)espera=setTimeout(tentaMontar,300);
   return false;
  }
  var s=document.createElement("span");s.id="contbar";s.dataset.t6Owner="bloco15";
  s.style.cssText="margin-left:14px;font-size:11.5px;font-weight:600;color:#8fa4c4;"+
   "vertical-align:middle;letter-spacing:.2px;white-space:nowrap";
  s.innerHTML=conteudo();
  s.title='Contagem exclusiva da projeção canônica de builds publicadas';
  h.appendChild(s);barra=s;iniciaRelogio();return true;
 }
 function atualiza(){
  if(barra)barra.innerHTML=conteudo();
  if(_t6BloqueioBuildsElenco()&&relogio!==null){clearInterval(relogio);relogio=null;}
 }
 function mount(){
  if(montado)return tentaMontar();
  montado=true;tentativas=0;return tentaMontar();
 }
 function refresh(){return montado?tentaMontar():false;}
 function dispose(){
  montado=false;cancelaEspera();tentativas=0;
  if(relogio!==null){clearInterval(relogio);relogio=null;}
  if(barra&&barra.dataset&&barra.dataset.t6Owner==="bloco15"&&barra.parentNode)
   barra.parentNode.removeChild(barra);
  barra=null;return true;
 }
 window.T6Bloco15=Object.freeze({mount:mount,refresh:refresh,dispose:dispose,
  inspect:function(){return{mounted:montado,pending:espera!==null,ticking:relogio!==null,attempts:tentativas,hasBar:!!barra};}});
 mount();
})();


/* bloco JavaScript 16 */

const MEU_TIME={"ids": ["103041", "105644183117482", "105653511172985", "105796318835406", "105796318836246", "105796318894173", "105796318903040", "105796318916611", "105796318919671", "105805714139254", "105805714141236", "105805714141376", "105805714141494", "105805714163136", "105805714163749", "105805714192706", "105805714196288", "105848932271764", "105848932274075", "105848932298328", "105859401165777", "105859401166632", "105859485069597", "106731279490391", "106746580456800", "106750338536440", "106755438714272", "106755438720293", "106755438787299", "106755438820479", "106757854755138", "106758391503938", "106772887125793", "106781477023870", "106781477040769", "106782550787909", "106782550788446", "106782550788519", "106784429760291", "106785503491871", "106787919411383", "106787919475376", "106788187832737", "106788187833650", "106788187839904", "106788187841133", "106788187843931", "106799462259226", "111366", "111407", "113760", "123101", "125370", "128513", "140127", "35017", "35207", "40352", "43133", "43387", "44636", "52851720165605", "52851988616262", "52851988649521", "52880442695351", "52888495823012", "52889569580679", "53975122505049", "53975927864176", "56162066233689", "56163408392226", "56163760664861", "56164750585918", "56165555880124", "56166361188271", "56166629640615", "60738", "60789", "88029918174624", "88030455139822", "88030991881014", "88032334062505", "88033139494397", "88033407933162", "88036360587096", "88036360622214", "88036360631451", "88036360649078", "88036360701097", "88036360719796", "88036360719797", "88036360719819", "88036360719820", "88036360719839", "88036360719858", "88038776508032", "88039045074440", "88041460901956", "88041997764700", "88044145214260", "88044145217198", "88044145248321", "88044145277054", "88044145348029", "88044145348045", "88044145351392", "88044682118054", "88044950524330", "88045218959416", "89138288266704", "89138288270047", "89138556572074", "89138556575063", "89138556701095"]};
(function(){
 var IDS = new Set((typeof MEU_TIME!=="undefined" && MEU_TIME.ids)||[]);
 if(!IDS.size) return;
 var montado=false,aguardandoDados=false;
 function removeEspera(){
  if(!aguardandoDados)return;
  window.removeEventListener("encaixe:dados-completos",aoDados);aguardandoDados=false;
 }
 function aoDados(){semeia();}
 function semeia(){
  if(_t6BloqueioBuildsElenco()){removeEspera();return true;}
  if(typeof MT==="undefined" || typeof D==="undefined") return false;
  removeEspera();
  try{ userStateLoad(); }catch(e){}
  MT.elenco = MT.elenco || [];
  MT.banco  = MT.banco  || [];
  var ja = new Set();
  (MT.slots||[]).forEach(function(x){ if(x && x.key) ja.add(String(x.key).split("|")[0]); });
  MT.banco.forEach(function(k){ ja.add(String(k).split("|")[0]); });
  MT.elenco.forEach(function(k){ ja.add(String(k).split("|")[0]); });
  var melhor = {};
  for (var i=0;i<D.length;i++){
   var c=D[i];
   if(!c || c.id==="MOLDE") continue;
   var id=String(c.id);
   if(!IDS.has(id) || ja.has(id)) continue;
   var n = (typeof nota==="function") ? nota(c) : (c.b1n||0);
   if(!melhor[id] || n > melhor[id].n) melhor[id] = {n:n, k:id+"|"+c.tipo};
  }
  var novos = Object.keys(melhor);
  if(!novos.length) return true;
  novos.forEach(function(id){ MT.elenco.push(melhor[id].k); });
  try{ userStateSave(); }catch(e){}
  try{ if(typeof mtRender==="function") mtRender(); }catch(e){}
  console.log("%cMEU TIME · "+novos.length+" cards novos entraram no elenco ("+
    MT.elenco.length+" no total; "+IDS.size+" cards do elenco reconhecidos nas fotos)",
    "background:#22c58b;color:#08120c;font-weight:700;padding:2px 7px");
  return true;
 }
 function mount(){
  if(montado)return semeia();
  montado=true;
  if(semeia())return true;
  if(!aguardandoDados){
   aguardandoDados=true;window.addEventListener("encaixe:dados-completos",aoDados);
  }
  return false;
 }
 function dispose(){montado=false;removeEspera();return true;}
 window.meuTimeSemeia = semeia;
 window.T6MeuTimeSemeiaLifecycle=Object.freeze({mount:mount,dispose:dispose,
  inspect:function(){return{mounted:montado,waitingData:aguardandoDados};}});
 mount();
})();


/* bloco JavaScript 17 */

/* SUGESTAO DE TECNICO - 14/08/2026 - injetado pelo gera_encaixe.py */
window.TECS=[["Erik ten Hag",1.03275,[10]],["Mikel Arteta",1.03275,[4]],["Xavi Hernandez",1.03275,[1]],["Stefano Pioli",1.03275,[19]],["Simone Inzaghi",1.03275,[16]],["Thomas Tuchel",1.03275,[14]],["Zico",1.03,[2]],["Pep Guardiola",1.0355,[3]],["Xabi Alonso",1.0355,[11]],["R. Martinez",1.0355,[14]],["V. Montella",1.0355,[16]],["D. Deschamps",1.0355,[10]],["G. Southgate",1.034091,[11]],["Lionel Scaloni",1.034091,[4]],["Olympio H.",1.034091,[12]],["D. Stojkovic",1.0355,[12]],["L. de la Fuente",1.0355,[11]],["Mikel Arteta",1.0355,[3,11]],["Steven Gerrard",1.0355,[2]],["Patrick Vieira",1.0355,[19]],["Paulo Fonseca",1.0355,[12,14]],["Frank Lampard",1.0355,[15]],["Frank Rijkaard",1.0355,[4]],["Ronald Koeman",1.0355,[1,16]],["Ruben Amorim",1.0355,[0,10]],["Jose Mourinho",1.0355,[19]],["Vincent Kompany",1.0355,[11,12]],["Hansi Flick",1.0355,[4,10]],["G. P. Gasperini",1.0355,[14]],["Simone Inzaghi",1.0355,[6,10]],["Johan Cruyff",1.036,[3,13]],["Xabi Alonso",1.0355,[11]],["Stale Solbakken",1.036,[7,14]],["Rudi Garcia",1.036,[0,1]],["L. Spalletti",1.036,[16,17]],["F. Beckenbauer",1.036,[6,12]],["Okan Buruk",1.036,[5,15]],["R. Martinez",1.036,[1,20]],["P. Kluivert",1.036,[4,18]],["Jose Mourinho",1.036,[14,16]],["Fabio Capello",1.036,[6,17]],["Frank Rijkaard",1.036,[3,15]],["Pep Guardiola",1.036,[12,20]],["Ruben Amorim",1.036,[5,14]],["Hansi Flick",1.036,[2,4]],["M. Allegri",1.036,[0,1]],["Mikel Arteta",1.036,[8,11]],["Cristian Chivu",1.036,[10,16]],["Niko Kovac",1.036,[3,12]],["Cesc Fabregas",1.036,[5,18]],["Ronald Koeman",1.036,[4,7]],["Gennaro Gattuso",1.036,[5,19]],["Jurgen Klopp",1.036,[10,20]],["Xabi Alonso",1.036,[1,6]],["F. Beckenbauer",1.036,[2,17]],["Johan Cruyff",1.036,[11,15]],["R. Martinez",1.0365,[0,6]],["Thomas Tuchel",1.0365,[4,16]],["D. Deschamps",1.036,[1,10]],["J. Nagelsmann",1.036,[2,14]],["Ronald Koeman",1.036,[12,13]],["V. Montella",1.036,[3,11]],["Frank Lampard",1.036,[4,18]],["Antonio Conte",1.0365,[12,17]]];
window.tecIguais=function(c){
 try{
  var nm=(c._tecNome!==undefined?c._tecNome:c.TEC);
  if(!nm||!window.TECS) return c.TECIG||[];
  var t0=null,i;
  for(i=0;i<TECS.length;i++) if(TECS[i][0]===nm){t0=TECS[i];break;}
  if(!t0) return c.TECIG||[];
  var pes={};
  for(i=0;i<(c.arows||[]).length;i++) if(c.arows[i][1]) pes[c.arows[i][0]]=1;
  var a={},j; for(j=0;j<t0[2].length;j++) a[t0[2][j]]=1;
  var out=[];
  for(i=0;i<TECS.length;i++){ var t=TECS[i];
   if(t[0]===nm||t[1]!==t0[1]) continue;
   var b={},k,bate=true; for(j=0;j<t[2].length;j++) b[t[2][j]]=1;
   for(k in a) if(!b[k]&&pes[k]){bate=false;break;}
   if(bate) for(k in b) if(!a[k]&&pes[k]){bate=false;break;}
   if(bate) out.push(t[0]);
  }
  out.sort();
  return out.length?out.slice(0,5):(c.TECIG||[]);
 }catch(e){ return c.TECIG||[]; }
};


/* bloco JavaScript 18 */

/* ===== EDICAO_VIVA_1408 ===== */
(function(){
 /* A nota de hoje NAO vem mais do b1 pela regua: vem da % DO MOLDE
    (patch ACH, funcao achPct), que tem cache proprio em c._cp e reescreve
    o c.b1n de todos os cards a cada traducaoViva(). Medido em 14/08 no
    Chromium: apos editar, _renota punha o b1n certo e o traducaoViva
    seguinte devolvia o valor antigo, porque o _cp continuava no cache.
    Entao apaga-se o _cp ANTES — e o traducaoViva faz o resto.
    O b1nDe fica de reserva, para quando o ACH estiver desligado. */
 function _renota(c){
  if(!c||c.id==="MOLDE")return;
  delete c._cp;
  delete c._n;
  try{
   var A=c.arows||[], n2=0, d2=0, q, w2;
   for(q=0;q<A.length;q++){ w2=A[q][1]; if(!w2) continue;
    n2+=w2*A[q][3]; d2+=w2*A[q][2]; }
   if(d2){ c.b1n=100*n2/d2; return; }
  }catch(e){}
  try{ c.b1n=(function(A){var n=0,d=0,i,w;A=A||[];for(i=0;i<A.length;i++){w=A[i][1];if(!w)continue;n+=w*A[i][3];d+=w*A[i][2];}return d?100*n/d:b1nDe(c.tipo,c.b1);})(c.arows); }catch(e){}
 }
 function _pinta(){ try{traducaoViva();}catch(e){} try{render();}catch(e){} }
 window._renota=_renota;

 var _g=window._grava;
 if(_g) window._grava=function(c,lvl){ _g(c,lvl); _renota(c); _pinta(); };

 var _th=window._trocaHabs;
 if(_th) window._trocaHabs=function(key,novas){ _th(key,novas); _renota(_card(key)); _pinta(); };

 var _rm=window.restaurarMotor;
 if(_rm) window.restaurarMotor=function(key){
  var c=_card(key); if(c){ delete c._cdOrig; c.cmode=1; }
  _rm(key); _renota(_card(key)); _pinta();
 };

 var _df=window._desfaz;
 if(_df) window._desfaz=function(){
  _df();
  try{ for(var i=0;i<D.length;i++) _renota(D[i]); }catch(e){}
  _pinta();
 };

 /* ---- IMPETO CONDICIONAL NA FICHA DO CARD ----------------------------
    Degraus lidos do videogame em 31/07 e refeitos INTEIROS pelo motor:
      1 a 7 jogadores da condicao -> degrau 1 (o padrao, e o do ranking)
      8 a 10                      -> degrau 2
      11 a 23                     -> degrau 3
    Nao existe degrau 4 nem 5: o motor so calcula 2 e 3. */
 function _tem(c){ return !!(c&&c.CD&&(c.CD["2"]||c.CD["3"])); }
 function _guarda(c){
  if(c._cdOrig)return;
  c._cdOrig={b1:c.b1,b1n:c.b1n,bar:c.sisBar,TEC:c.TEC,TECB:c.TECB,
             HAB:c.HAB,adds:c.adds,sobra:c.sobra,
             v:(c.arows||[]).map(function(r){return r[3];})};
 }
 function _aplica(c){
  if(!_tem(c))return;
  _guarda(c);
  var n=c.cmode||1, o=c._cdOrig, a,
      f=(n>1&&c.CD[String(n)])?c.CD[String(n)]:null;
  c.b1    = f? f.b1    : o.b1;
  c.b1n   = f? f.b1n   : o.b1n;
  c.sisBar= f? f.bar   : o.bar;
  c.TEC   = f? f.TEC   : o.TEC;
  c.TECB  = f? f.TECB  : o.TECB;
  c.HAB   = f? f.HAB   : o.HAB;
  c.adds  = f? f.HAB   : o.adds;
  c.sobra = f? f.sobra : o.sobra;
  var vv = f? f.v : o.v;
  if(c.arows&&vv) for(a=0;a<c.arows.length;a++){
   if(vv[a]===undefined)continue;
   c.arows[a][3]=vv[a];
   c.arows[a][4]=Math.round((vv[a]-c.arows[a][2])*100)/100;
   c.arows[a][5]=vv[a];
  }
  delete c._cp;
  delete c._n;
 }
 window.recalcCard=function(c){ if(_tem(c)) _aplica(c); };

 /* ---- IMPETO ADICIONADO: editavel no proprio quadro -------------------
    A verdade do impeto e a STRING `c.imp` — o proprio codigo da casca diz
    isso num comentario, e a lista `c.imps` do banco esta desencontrada dela
    desde 05/08 (caderninho, item 24: "seletor pleno dos impetos fica pro
    pacotao real"). O formato real e:

       "de fabrica: Conducao Tecnica +3 · o motor pos: Sem Bola +1"

    O `editImp` da casca reescrevia a string INTEIRA ("Precisao +3 ⚒"),
    APAGANDO o impeto de fabrica junto. Aqui so a parte depois de
    "o motor pos:" e trocada; o nativo nunca e tocado.

    E o `valsDeLvl` nao conhecia impeto — so barra e tecnico. Entao trocar
    o impeto nao mexia em atributo nenhum. Agora entra pelo mesmo caminho
    do tecnico: delta entre o impeto original e o de agora. */
 /* Reotimizar as barras depois de trocar habilidade ou impeto (ordem do
    Luis, 14/08). Com uma trava: se a escolha voltou a ser EXATAMENTE a que o
    motor tinha posto, devolve a build do motor em vez de reotimizar — o
    otimizador que roda no navegador e mais fraco que o motor de verdade, e
    sem isso desfazer uma troca nunca voltava a nota de origem. */
 function _igualAoMotor(c){
  var o=_oriDe(c);
  if(String(c.imp||'')!==String(o.imp||'')) return false;
  var h=(c._habs!==undefined)?c._habs:(c.HAB||[]), h0=(c.HAB||[]), i;
  if(h.length!==h0.length) return false;
  for(i=0;i<h.length;i++) if(h0.indexOf(h[i])<0) return false;
  return true;
 }
 /* Se a composicao voltou a ser EXATAMENTE a que o motor escolheu, o card
    volta a ser o do motor — pelo mesmo caminho do botao verde, que ja devolve
    o numero exato. Nao se reotimiza no navegador nesse caso: o otimizador
    daqui e mais fraco que o motor e devolveria nota menor.
    (A primeira tentativa montava a restauracao na mao e devolvia 110,5 no
    lugar de 108,57 — por isso agora chama o `restaurarMotor` de verdade.) */
 function _igualAoMotor(c){
  var o=_oriDe(c);
  if(String(c.imp||'')!==String(o.imp||'')) return false;
  var h=(c._habs!==undefined)?c._habs:(c.HAB||[]), h0=(c.HAB||[]), i;
  if(h.length!==h0.length) return false;
  for(i=0;i<h.length;i++) if(h0.indexOf(h[i])<0) return false;
  var t=(c._tec!==undefined)?c._tec:(c.TECB||[]), t0=(o.tec||[]);
  if(t.length!==t0.length) return false;
  for(i=0;i<t.length;i++) if(t0.indexOf(t[i])<0) return false;
  return true;
 }
 function _reOtim(c,key){
  if(window.FichaState&&window.FichaState.uiMode()==='livre') return;
  if(_igualAoMotor(c)){
   if(typeof restaurarMotor==='function') restaurarMotor(key);
   return;
  }
  if(typeof otimizarBarras==='function') otimizarBarras(key);
 }
 /* trocar o TECNICO tambem redistribui as barras (ordem do Luis, 14/08:
    o usuario poe os insumos que ELE tem — habilidade, tecnico, impeto — e
    as barrinhas se acertam sozinhas para a maior nota com aquilo). */
 var _tc=window.trocaTec;
 if(_tc) window.trocaTec=function(key,idx){
  var c=_card(key); try{ _oriDe(c); }catch(e){}
  _tc(key,idx);
  try{ _reOtim(_card(key),key); }catch(e){}
  _pinta(); try{ reabrir(key); }catch(e){}
 };
 /* ===== AS ABAS DO BLOCO ATRIBUTOS — REMOVIDAS DAQUI EM 16/08/2026 =====
    ⛔ NAO REPOR. Este bloco definia `window.encModo` e `window._modoBar` — e o
    CONTA-DO-MOTOR.js define OS DOIS DE NOVO. Duas versoes da mesma coisa no
    mesmo HTML, e quem mandava era a que carregasse por ultimo.

    O que isso custou, medido em 16/08: na tela gerada as 02h25 venceu ESTA
    versao, que chamava `otimizarBarras` ao entrar na aba em vez de `zeraInsumos`.
    Resultado: a aba abria com tecnico, impeto fabricado e habilidades
    adicionadas ja preenchidos com a build do motor. E os nomes das abas que o
    Luis fechou em 15/08 (MAXIMO POSSIVEL / MEU CARD / LIVRE) nunca chegaram a
    aparecer — esta versao os sobrescrevia com os nomes de 14/08.

    Ordem do Luis, 16/08: *"por que que tem duas versoes? A gente nao pode
    trabalhar com coisa pela metade, so da problema. Voce tem que colocar o que
    a gente vai usar mesmo."*

    Fica UMA versao so, a do CONTA-DO-MOTOR.js. O gancho que insere a barra de
    abas (`_modoBar(K)` antes do `<div class="bpan bptrio">`) CONTINUA aqui em
    cima — ele so chama quem existir. */
 /* ---- "IMPETO NATIVO: nao tem" em card que TEM (14/08) ----------------
    O nome do impeto nativo vem do `nmn` / do efscout. Quando nenhum dos dois
    tem o nome, a tela escrevia "nao tem" — mas o EFEITO esta no vetor `nm`,
    que o motor usa e que nunca esta vazio nesses cards (Hazard e o exemplo
    do Luis). Aqui o nome e DEDUZIDO do proprio vetor: procura-se no catalogo
    o impeto cujos atributos e valores batem exatamente com o que sobrou.
    Se nenhum bate, mostra-se o efeito por extenso — nunca mais "nao tem"
    num card que tem. */
 window._natDoVetor=function(c){
  var v, i, j, k, sobra=[], usados=[], f, ok2, achou;
  var _AVISO='<li><b>TEM ímpeto — efeito por conferir</b>'
      +'<div class=impef>o card veio com ímpeto de fábrica, mas o catálogo não '
      +'conhece esse código'+((c.boostIds&&c.boostIds.length)?' ('+c.boostIds.join(' e ')+')':'')
      +'. O motor calculou SEM ele: a pontuação está por baixo. '
      +'Conferir a ficha no jogo resolve todos os cards que usam o mesmo.</div></li>';
  try{ v=expand(c.nm).slice(); }catch(e){ return c.impDesc?_AVISO:'<li>não tem</li>'; }
  var soma=0; for(i=0;i<26;i++) soma+=v[i];
  if(!soma) return c.impDesc?_AVISO:'<li>não tem</li>';
  /* tira do vetor o que ja foi identificado como fabricado (a string) */
  try{ var im=_impVetStr(c.imp); for(i=0;i<26;i++) v[i]=Math.max(0,v[i]-im[i]); }catch(e){}
  soma=0; for(i=0;i<26;i++) soma+=v[i];
  if(!soma) return c.impDesc?_AVISO:'<li>não tem</li>';
  for(k=0;k<3;k++){
   achou=null;
   for(j=0;j<CAT.length;j++){
    f=expand(CAT[j][2]); ok2=false;
    for(i=0;i<26;i++){ if(f[i]>v[i]){ ok2=false; break; } if(f[i]) ok2=true; }
    if(ok2){ if(!achou || _peso(f)>_peso(expand(achou[2]))) achou=CAT[j]; }
   }
   if(!achou) break;
   usados.push(achou[0]);
   f=expand(achou[2]); for(i=0;i<26;i++) v[i]-=f[i];
   soma=0; for(i=0;i<26;i++) soma+=v[i];
   if(!soma) break;
  }
  if(usados.length){
   return usados.map(function(n){
    var h=null,z; for(z=0;z<CAT.length;z++) if(CAT[z][0]===n){h=CAT[z];break;}
    var ef=''; try{ if(h) ef=pimpEfeito(h[2]); }catch(e){}
    return '<li><b>'+n+'</b>'+(ef?'<div class=impef>'+ef+'</div>':'')+'</li>';
   }).join('');
  }
  var txt=[]; try{ v=expand(c.nm);
   for(i=0;i<26;i++) if(v[i]) txt.push(ATTRS[i]+' +'+v[i]);
  }catch(e){}
  return txt.length? '<li><b>ímpeto nativo</b><div class=impef>'+txt.join(' · ')+'</div></li>'
                   : (c.impDesc?_AVISO:'<li>não tem</li>');
 };
 function _peso(f){ var t=0,i; for(i=0;i<26;i++) t+=f[i]; return t; }
 var MARCA='o motor pos:';
 function _impPartes(c){
  var s=String(c.imp||''), i=s.indexOf(MARCA);
  if(i<0) return {fab:s.replace(/\s*⚒\s*$/,'').trim(), add:''};
  return {fab:s.slice(0,i).replace(/[·\s]+$/,'').trim(),
          add:s.slice(i+MARCA.length).replace(/\s*⚒\s*$/,'').trim()};
 }
 function _impMonta(fab,add){
  var a=[]; if(fab)a.push(fab); if(add)a.push(MARCA+' '+add);
  return a.join(' · ');
 }
 function _impNome(n){
  if(!n)return null;
  for(var i=0;i<CAT.length;i++) if(CAT[i][0]===n) return CAT[i];
  return null;
 }
 function _impVetStr(s){
  var v=new Array(26); for(var i=0;i<26;i++)v[i]=0;
  var P=_impPartes({imp:s});
  [P.fab.replace(/^de f[aá]brica:\s*/i,''), P.add].forEach(function(bloco){
   String(bloco||'').split(/\s+[·+]\s+/).forEach(function(n){
    var f=_impNome(n.trim()); if(f) expand(f[2]).forEach(function(q,j){v[j]+=q;});
   });
  });
  return v;
 }
 window.impVet=function(c){ return _impVetStr(c&&c.imp); };

 var _vl=window.valsDeLvl;
 if(_vl) window.valsDeLvl=function(c,lvl){
  var v=_vl(c,lvl);
  try{
   var o=_oriDe(c), ib=_impVetStr(o.imp), inn=_impVetStr(c.imp);
   c.arows.forEach(function(r,k){ var i=r[0], d=inn[i]-ib[i];
    if(d) v[i]=Math.max(0,Math.min(Math.max(99,o.v[k]),v[i]+d)); });
  }catch(e){}
  return v;
 };

 window.editImp=function(key,nome){
  var c=_card(key); if(!c)return;
  /* o retrato do original TEM de ser tirado antes de mexer na string:
     o _oriDe guarda na primeira chamada, e quem chamava primeiro era o
     _grava — ja com o impeto novo, o que zerava o delta. */
  try{ _oriDe(c); _marca(key); }catch(e){}
  var P=_impPartes(c), add=(!nome||nome==='(nenhum)')?'':nome;
  c.imp=_impMonta(P.fab,add);
  c.imps=(c.imps||[]).filter(function(x){return !x.f;});
  if(add)c.imps.push({n:add,c:0,f:1});
  _grava(c,_lvlDe(c));
  try{ _reOtim(c,key); }catch(e){}
  _pinta();
  try{ reabrir(key); }catch(e){}
 };
/* ---- HABILIDADE: o efeito parava de aparecer por saturacao ------------
    O `_trocaHabs` mede o efeito da habilidade pela `cadeia()`, que trava em
    99. O Messi tem Drible 113 e Finalizacao 107 no motor; na cadeia os dois
    viram 99, e ai as habilidades de drible dele "nao tem onde subir" —
    tirar as CINCO adicionadas mexia 0,5% na nota. Medido em 14/08.
    Aqui o efeito e medido SEM a trava, sobre o valor pre-habilidade, e o
    delta e aplicado em cima do numero do motor. */
 function _preHab(c,lvl){
  var nm=expand(c.nm), tec=tecVet(tecAtual(c)), im=_impVetStr(c.imp);
  var cb=_contrib(lvl), v=new Array(26), i;
  for(i=0;i<26;i++){ v[i]=Math.min(99,(c.base?c.base[i]:0)+cb[i]) + nm[i]+im[i]+tec[i]; }
  return v;
 }
 function _buffSemTeto(v,b){
  if(!b) return v;
  return v + Math.max(0, Math.ceil(v*b[0]/100) + b[1]);
 }
 window._trocaHabs=function(key,novas){
  var c=_card(key); if(!c)return;
  try{ _oriDe(c); _marca(key); }catch(e){}
  var lvl=_lvlDe(c), pre=_preHab(c,lvl);
  var b0=buffDe(habsDe(c));
  c._habs=novas;
  var b1=buffDe(habsDe(c));
  var o=_oriDe(c), sis=(c.sis&&c.sis.length)?c.sis.slice():c.arows.map(function(r){return r[3];});
  c.arows.forEach(function(r,k){
   var i=r[0], d=_buffSemTeto(pre[i],b1[i])-_buffSemTeto(pre[i],b0[i]);
   var teto=Math.max(99,o.v[k]);
   var x=Math.max(0,Math.min(teto,Math.round(sis[i]+d)));
   sis[i]=x; r[3]=x; r[4]=Math.round((x-r[2])*100)/100; r[5]=x;
  });
  c.sis=sis;
  c.b1=notaDe(sis,c.arows);
  _renota(c);
  _pinta();
  try{ reabrir(key); }catch(e){}
 };
 window.impAdicionado=function(c){ return _impPartes(c).add; };
 window._impSel=function(c,K,atual){
  var ops=window.impOpcoes(c), h="", i, q=String.fromCharCode(39);
  h+="<select style=\"max-width:200px;margin-top:5px;font-size:11px\" onchange=\"editImp("+q+K+q+",this.value)\">";
  h+="<option value=\"\""+(atual?"":" selected")+">(nenhum)</option>";
  for(i=0;i<ops.length;i++) h+="<option"+(ops[i]===atual?" selected":"")+">"+ops[i]+"</option>";
  return h+"</select>";
 };
 window.impOpcoes=function(c){
  var fora={}, P=_impPartes(c);
  String(P.fab).split(/\s+[·+]\s+/).forEach(function(n){fora[n.trim()]=1;});
  return CAT.filter(function(x){ return !fora[x[0]]; }).map(function(x){return x[0];});
 };
 window.toggleCondCard=function(key){
  var c=_card(key); if(!c||!_tem(c))return;
  try{ _marca(key); }catch(e){}
  var d=(c.cmode||1)+1;
  while(d<=3 && !c.CD[String(d)]) d++;
  c.cmode = (d>3)?1:d;
  _aplica(c);
  _pinta();
  try{ reabrir(key); }catch(e){}
 };
})();


/* bloco JavaScript 19 */

/* ===================================================================
   A CONTA DO MOTOR NA TELA — 15/08/2026
   Ordem do Luis: "tem que calcular de acordo com o que mexe, da mesma
   forma que o motor calcula". E o desenho, na palavra dele:
     "o motor e essa equacao com alteracao a exaustao das variaveis para
      achar a soma maxima; a tela e a aplicacao dela pontualmente."
   Uma equacao so, dois usos.

   A Equacao 1 vigente, reconfirmada no Messi em 28/08/2026:
     pre = min(99, base + niveis das barras)      <- referencia da habilidade
     x   = min(99, pre + trunc(pre*(m-1)))         <- proficiencia
     x  += boost do tecnico                        passa de 99
     x  += impetos nativos/equipados               passa de 99
     x  += ceil(pre*pct/100 + flat)               habilidade, SEM TRAVA

   Hipotese posterior REVOGADA: impetos antes da proficiencia e sem teto superior.
   Messi com pre=99, Capello 89/+1 e Precisao +4 exibiu 104; a hipotese previa
   107 ou mais. Nao reintroduzir sem nova autorizacao e prova discriminante.
   =================================================================== */
(function(){
  if (window.CONTA_DO_MOTOR_1508) return;
  window.CONTA_DO_MOTOR_1508 = true;

  var HABM = {"Drible explosivo": [1, {"2": [5.0, 0.0]}], "Afastamento acrobático": [0, {"17": [3.0, 0.0], "18": [2.0, 0.0]}], "Finaliz. acrobática": [0, {"6": [5.0, 0.0]}], "Fortaleza aérea": [1, {"13": [2.0, 0.0], "14": [3.0, 0.0]}], "Superioridade aérea": [0, {"13": [2.0, 0.0], "14": [3.0, 0.0]}], "Ímpeto de Ataque": [1, {"10": [2.0, 0.0], "11": [3.0, 0.0]}], "Desencadeador de ataques": [1, {"4": [1.0, 0.0], "5": [2.0, 0.0]}], "Curva descendente": [1, {"9": [5.0, 0.0]}], "Bloqueador": [0, {"14": [2.0, 0.0], "17": [3.0, 0.0]}], "Cabeçada matadora": [1, {"7": [5.0, 0.0]}], "Liderança": [0, {"19": [2.0, 0.0]}], "Controle da cavadinha": [0, {"6": [2.0, 0.0]}], "Corte com virada": [0, {"2": [5.0, 0.0]}], "Puxada de letra": [0, {"2": [5.0, 0.0]}], "Folha seca": [0, {"9": [4.0, 0.0], "12": [1.0, 0.0]}], "Toque duplo": [0, {"2": [5.0, 0.0]}], "Cruzamento seco": [1, {"4": [2.0, 0.0]}], "Espírito guerreiro": [0, {"7": [1.0, 0.0], "16": [2.0, 0.0]}], "Chute de primeira": [0, {"6": [5.0, 0.0]}], "Elástico": [0, {"2": [5.0, 0.0]}], "Xerifão": [1, {"17": [5.0, 0.0], "18": [5.0, 0.0]}], "Passe inspirador": [1, {"4": [10.0, 0.0], "5": [10.0, 0.0]}], "Malícia": [0, {"15": [3.0, 0.0], "20": [2.0, 0.0]}], "Defesa direta (GO)": [1, {"23": [5.0, 0.0]}], "Reposição alta do GO": [0, {"5": [2.0, 0.0], "23": [3.0, 0.0]}], "Arrem. longo do GO": [0, {"5": [3.0, 0.0], "23": [2.0, 0.0]}], "Repos. baixa do GO": [0, {"4": [2.0, 0.0], "23": [3.0, 0.0]}], "Pegador de pênaltis": [0, {"21": [2.0, 0.0]}], "Grito de garra (GO)": [1, {"21": [3.0, 0.0], "23": [2.0, 0.0]}], "Cabeceio": [0, {"7": [5.0, 0.0]}], "Toque de calcanhar": [0, {"4": [2.0, 0.0]}], "Interceptação": [0, {"17": [2.0, 0.0], "20": [3.0, 0.0]}], "Chute com o peito do pé": [0, {"12": [2.0, 0.0]}], "Efeito de longe": [0, {"6": [2.0, 0.0], "9": [3.0, 0.0]}], "Precisão à distância": [0, {"6": [10.0, 0.0]}], "Desarme de longo alcance": [1, {"18": [5.0, 0.0]}], "Arrem. lateral longo": [0, {"5": [2.0, 0.0]}], "Passe aéreo baixo": [0, {"5": [5.0, 0.0]}], "Chute rasteiro forte": [1, {"12": [5.0, 0.0]}], "Pés magnéticos": [1, {"3": [5.0, 0.0]}], "Marcação individual": [0, {"14": [2.0, 0.0], "17": [1.0, 0.0], "20": [2.0, 0.0]}], "360 graus": [0, {"2": [5.0, 0.0]}], "Drible astuto": [1, {"2": [5.0, 0.0]}], "Passe sem olhar": [0, {"4": [2.0, 0.0]}], "Passe de primeira": [0, {"4": [5.0, 0.0]}], "Curva para fora": [0, {"9": [3.0, 0.0]}], "Especialista em pênalti": [0, {"8": [2.0, 0.0]}], "Finalizador nato": [1, {"6": [3.0, 0.0], "12": [2.0, 0.0]}], "Passador nato": [1, {"4": [3.0, 0.0], "5": [2.0, 0.0]}], "Cruzamento preciso": [0, {"4": [10.0, 0.0], "5": [10.0, 0.0]}], "De letra": [0, {"5": [2.0, 0.0]}], "Chutes com decolagem": [0, {"9": [1.0, 0.0], "12": [4.0, 0.0]}], "Pedalada simples": [0, {"2": [5.0, 0.0]}], "Finta de letra": [0, {"2": [5.0, 0.0]}], "Sombra veloz": [1, {"10": [2.0, 0.0], "11": [3.0, 0.0]}], "Carrinho": [0, {"18": [5.0, 0.0]}], "Chapéu": [0, {"2": [5.0, 0.0]}], "Controle com a sola": [0, {"3": [3.0, 0.0]}], "Super substituto": [0, {"0": [1.0, 0.0], "6": [1.0, 0.0]}], "Puxada e tapa": [1, {"2": [5.0, 0.0]}], "Passe em profundidade": [0, {"4": [10.0, 0.0], "5": [10.0, 0.0]}], "Volta para marcar": [0, {"11": [1.0, 0.0], "17": [1.0, 0.0]}], "Passe visionário": [1, {"4": [2.0, 0.0], "5": [3.0, 0.0]}], "Passe na medida": [0, {"5": [4.0, 0.0], "9": [1.0, 0.0]}], "Força de vontade": [1, {"0": [3.0, 0.0], "16": [2.0, 0.0]}]};      /* nome PT -> [rara?1:0, {idx:[pct,flat]}]  (65) */
  var TECM = {"Erik ten Hag": [1.03275], "Mikel Arteta": [1.03275, 1.0355, 1.036], "Xavi Hernandez": [1.03275], "Stefano Pioli": [1.03275], "Simone Inzaghi": [1.03275, 1.0355], "Thomas Tuchel": [1.03275, 1.0365], "Zico": [1.03], "Pep Guardiola": [1.0355, 1.036], "Xabi Alonso": [1.0355, 1.036], "R. Martinez": [1.0355, 1.036, 1.0365], "V. Montella": [1.0355, 1.036], "D. Deschamps": [1.0355, 1.036], "G. Southgate": [1.034091], "Lionel Scaloni": [1.034091], "Olympio H.": [1.034091], "D. Stojkovic": [1.0355], "L. de la Fuente": [1.0355], "Steven Gerrard": [1.0355], "Patrick Vieira": [1.0355], "Paulo Fonseca": [1.0355], "Frank Lampard": [1.0355, 1.036], "Frank Rijkaard": [1.0355, 1.036], "Ronald Koeman": [1.0355, 1.036], "Ruben Amorim": [1.0355, 1.036], "Jose Mourinho": [1.0355, 1.036], "Vincent Kompany": [1.0355], "Hansi Flick": [1.0355, 1.036], "G. P. Gasperini": [1.0355], "Johan Cruyff": [1.036], "Stale Solbakken": [1.036], "Rudi Garcia": [1.036], "L. Spalletti": [1.036], "F. Beckenbauer": [1.036], "Okan Buruk": [1.036], "P. Kluivert": [1.036], "Fabio Capello": [1.036], "M. Allegri": [1.036], "Cristian Chivu": [1.036], "Niko Kovac": [1.036], "Cesc Fabregas": [1.036], "Gennaro Gattuso": [1.036], "Jurgen Klopp": [1.036], "J. Nagelsmann": [1.036], "Antonio Conte": [1.0365]};      /* nome do tecnico -> [multiplicadores possiveis] */
  var MS   = [1.036,1.0365,1.0355,1.034091,1.03275,1.03];

  function mult(x,m){ if(!m||m===1) return x;
    return Math.min(99, Math.max(40, x + Math.trunc(x*(m-1)))); }

  /* a regra da metade: comum vencedora inteira, cada perdedora metade;
     RARA soma por cima, inteira. (equacao.py buff_de) */
  function buff(hs){
    var pcC={},pcR={},flC={},flR={},i,h,v,k,d;
    for(i=0;i<(hs||[]).length;i++){ h=hs[i]; v=HABM[h]; if(!v) continue;
      var rara=v[0]===1, ef=v[1];
      for(k in ef){ d=ef[k];
        if(d[0]){ var A=rara?pcR:pcC; A[k]=(A[k]||[]).concat(d[0]); }
        if(d[1]){ var B=rara?flR:flC; B[k]=(B[k]||[]).concat(d[1]); } } }
    var meia=function(a){ if(!a||!a.length) return 0;
      var v2=a.slice().sort(function(x,y){return y-x;});
      return v2[0]+v2.slice(1).reduce(function(s,x){return s+x/2;},0); };
    var out={}, ids={}, o;
    [pcC,pcR,flC,flR].forEach(function(O){ for(o in O) ids[o]=1; });
    for(o in ids){
      var pct = meia(pcC[o]) + (pcR[o]||[]).reduce(function(a,b){return a+b;},0);
      var flat= meia(flC[o]) + (flR[o]||[]).reduce(function(a,b){return a+b;},0);
      if(pct||flat) out[+o]=[pct,flat];
    }
    return out;
  }

  /* SO o que o motor pos entra pela string. O NATIVO ja vem pelo c.nm —
     ler a string inteira conta o de fabrica DUAS VEZES (erro pego em 15/08). */
  function impDoMotor(s){
    var v=new Array(26).fill(0), dep=String(s||'').split('o motor pos:');
    if(dep.length<2) return v;
    dep.slice(1).join(' ').split('·').forEach(function(p){
      var t=p.replace(' (cond.)','').replace(' ⚒','').trim(); if(!t) return;
      var f=(typeof CAT!=='undefined') ? CAT.find(function(y){return y[0]===t;}) : null;
      if(f) expand(f[2]).forEach(function(x,i){ v[i]+=x; });
    });
    return v;
  }

  /* TODAS as habilidades que contam: fabrica + RARAS + as escolhidas.
     A tela esquecia as raras. */
  function todasHabs(c, escolhidas){
    return (c.fab||[]).concat(c.raras||[], escolhidas||[]);
  }

  /* a Equacao 1, uma vez, com o estado que vier */
  function conta(c, st){
    var base=c.base||[], cb=_contrib(st.lvl), tec=tecVet(st.tecb||[]),
        nm=expand(c.nm), imp=impDoMotor(st.imp), bf=buff(todasHabs(c, st.habs)),
        out=[], i, pre, x;
    for(i=0;i<26;i++){
      pre = Math.min(99,(base[i]||0)+cb[i]);
      x   = mult(pre, st.m);
      x  += tec[i] + nm[i] + imp[i];
      if(bf[i]) x += Math.ceil(pre*bf[i][0]/100 + bf[i][1]);
      out[i]=x;
    }
    return out;
  }

  /* o multiplicador do card: o que REPRODUZ o que o motor gravou.
     Sem chute — e a propria prova que escolhe. */
  function achaM(c, b){
    if(c._m!==undefined) return c._m;
    /* compara sempre contra o RETRATO do que o motor gravou, nunca contra um
       estado que ja foi mexido na tela */
    b = b || c._anc0 || {lvl:_lvlDe(c), tecb:(c.TECB||[]), imp:c.imp,
                         habs:(c._habs0||c.HAB||[]), v:(c.sis||[])};
    var st0={lvl:b.lvl, tecb:b.tecb, imp:b.imp, habs:b.habs}, i, k, v, ok;
    for(k=0;k<MS.length;k++){
      st0.m=MS[k]; v=conta(c,st0); ok=true;
      for(i=0;i<26;i++) if(Math.round(v[i])!==Math.round(b.v[i])){ ok=false; break; }
      if(ok){ c._m=MS[k]; return c._m; }
    }
    var L=TECM[c.TEC]; c._m = (L&&L.length)? L[L.length-1] : 1.036; c._mAprox=true;
    return c._m;
  }
  function mDoNome(nome, atual){
    var L=TECM[nome]; if(!L||!L.length) return atual;
    if(L.length===1) return L[0];
    var melhor=L[0], i;                 /* nome repetido: fica o mais perto do atual */
    for(i=1;i<L.length;i++) if(Math.abs(L[i]-atual)<Math.abs(melhor-atual)) melhor=L[i];
    return melhor;
  }

  /* ---- a ANCORA: o retrato do que o motor gravou ---- */
  function anc(c){
    if(!c._anc){
      var b = c._anc0 || { v:(c.sis||[]).slice(), lvl:_lvlDe(c), tecb:(c.TECB||[]).slice(),
                           imp:c.imp, habs:(c._habs0||c.HAB||[]).slice(),
                           sisBar:(c.sisBar||[]).map(function(r){return r.slice();}), sobra:c.sobra };
      c._anc = { v:b.v.slice(), lvl:b.lvl, tecb:b.tecb.slice(), imp:b.imp, habs:b.habs.slice(),
                 sisBar:b.sisBar.map(function(r){return r.slice();}), sobra:b.sobra, m:0 };
      c._anc.m = achaM(c, b);
    }
    return c._anc;
  }

  /* ---- o estado que esta na tela agora ---- */
  function agora(c, lvl){
    var a=anc(c), tecb = (c._tec!==undefined? c._tec : a.tecb);
    var nomeTec = (c._tecNome!==undefined? c._tecNome : c.TEC);
    return { lvl: lvl||_lvlDe(c), tecb: tecb, imp: c.imp,
             habs: (c._habs!==undefined? c._habs : a.habs),
             m: (nomeTec ? mDoNome(nomeTec, a.m) : 1) };
  }

  /* =========== o valor final: gravado + o delta da EQUACAO ===========
     Ancorar no gravado faz o card nunca escorregar do que o motor calculou,
     e o delta e a conta do motor. */
  function valores(c, lvl){
    var a=anc(c), v0=conta(c,{lvl:a.lvl,tecb:a.tecb,imp:a.imp,habs:a.habs,m:a.m}),
        v1=conta(c, agora(c,lvl)), out=[], i;
    for(i=0;i<26;i++) out[i] = Math.max(0, a.v[i] + (v1[i]-v0[i]));
    return out;
  }

  window.valsDeLvl = function(c,lvl){ try{ return valores(c,lvl); }catch(e){ return (c.sis||[]).slice(); } };

  window._trocaHabs = function(key,novas){
    var c=_card(key); if(!c) return;
    try{ _marca(key); }catch(e){}
    try{ _oriDe(c); }catch(e){}
    anc(c);
    c._habs = novas;
    var vals = valores(c, _lvlDe(c));
    c.sis = vals;
    c.arows.forEach(function(r){ r[3]=vals[r[0]]; r[4]=r[3]-r[2]; r[5]=r[3]; });
    c.b1 = notaDe(vals, c.arows);
    try{ c.b1n=(function(A){var n=0,d=0,i,w;A=A||[];for(i=0;i<A.length;i++){w=A[i][1];if(!w)continue;n+=w*A[i][3];d+=w*A[i][2];}return d?100*n/d:b1nDe(c.tipo,c.b1);})(c.arows); }catch(e){}
    delete c._cp; delete c._n;
    traducaoViva(); render();
    try{ reabrir(key); }catch(e){}
  };


  /* guarda o retrato das habilidades ANTES de qualquer edicao */
  try{ for(var q=0;q<D.length;q++){ var _c=D[q]; if(!_c) continue;
    if(_c.HAB) _c._habs0 = _c.HAB.slice();
    if(_c.sis && _c.arows) _c._anc0 = { v:_c.sis.slice(), lvl:_lvlDe(_c), tecb:(_c.TECB||[]).slice(),
      imp:_c.imp, habs:(_c.HAB||[]).slice(),
      sisBar:(_c.sisBar||[]).map(function(r){return r.slice();}), sobra:_c.sobra };
  } }catch(e){}



  /* ===== RECALCULAR AS BARRAS — com a conta do motor ======================
     O botao "recalcular as barras" (o admin) chama a distOtima da casca, que
     decide onde por cada ponto JA CONTANDO o efeito da habilidade. Duas coisas
     estavam erradas ali, medidas em 15/08:
       1. o `bf` vinha do buffDe da casca — 62 habilidades e SEM as raras
       2. dentro da distOtima o efeito e aplicado pela aplicaBuff VELHA
          (% sobre o valor ja somado com impeto/tecnico, e travando em 99)
     Resultado: ele gastava ponto onde a habilidade ja cobria, e deixava de
     gastar onde ela nao chegava.

     Conserto: a mesma distOtima, com UMA linha trocada — a do efeito — e o
     buff certo (65 habilidades, com as raras). Se o trecho nao for encontrado,
     nada e alterado: fica como estava. */
  /* ⛔ 25/08 — O eval() SAIU DAQUI.
     O que este bloco fazia (reescrever a distOtima trocando uma linha de
     texto) esta feito no proprio fonte, la em cima, na definicao da
     distOtima. Mesma troca, mesmo resultado, sem eval e sem o modo de
     falha silencioso: nao existe mais o caso 'nao achei o trecho'.
     window.distOtima continua exposta porque ha quem a chame por ali. */
  try{
    if (typeof distOtima === 'function') window.distOtima = distOtima;
    window.DIST_OTIMA_CERTA = true;
  }catch(e){ window.DIST_OTIMA_CERTA = true; }

  function distBarras(c, key){
    if(!c||!c.base) return;
    try{ _marca(key); }catch(e){}
    var a=anc(c), st=agora(c, _lvlDe(c)), i;
    var nm=expand(c.nm), imp=impDoMotor(st.imp), tc=tecVet(st.tecb||[]);
    var add=new Array(26).fill(0);
    for(i=0;i<26;i++) add[i]=nm[i]+imp[i]+tc[i];
    var bf=buff(todasHabs(c, st.habs));           /* 65 habilidades, COM as raras */
    var orc=c.orc||0;
    var lvl=distOtima(c.base, c.arows, orc, add, bf);
    /* a regra de ouro do motor: nunca sobra ponto — o resto vai pro maior peso */
    var g=orc-gastoDe(lvl);
    if(g>0){
      var pw={}; MBK.forEach(function(b){
        pw[b]=Math.max.apply(null,[0].concat(c.arows.filter(function(r){return MB[b].indexOf(r[0])>=0;})
                                                    .map(function(r){return r[1];})));});
      var ordem=MBK.slice().sort(function(x,y){return pw[y]-pw[x];});
      for(var z=0;z<ordem.length;z++){
        var b=ordem[z];
        while((lvl[b]||0)<25){ var cst=ACCU[(lvl[b]||0)+1]-ACCU[lvl[b]||0];
          if(cst>g) break; lvl[b]=(lvl[b]||0)+1; g-=cst; }
        if(g<=0) break;
      }
    }
    _grava(c,lvl);
  }

  window.otimizarBarras = function(key){
    distBarras(_card(key), key);
    try{ reabrir(key); }catch(e){}
  };


  /* =======================================================================
     O MODAL DO CARD — 15/08/2026 (ordem do Luis, na sequencia)

       1  o botao verde "⚡ OTIMIZAR — a build do motor" NAO FUNCIONAVA.
         Medido na ficha do Pepe: 110,13 -> 108,44 e "sobram 15" pontos —
         o motor NUNCA deixa sobrar ponto. Causa: o botao chama
         `restaurarMotor`, da casca, que restaura de um retrato parcial
         (`_oriDe`). A porta canônica `restaurarMotor` abaixo devolve a ANCORA
         inteira e é chamada diretamente pelo botão.

     2  as TRES ABAS, na palavra dele:

          ⚡ MAXIMO ............ SO LEITURA. E o teto desta carta: a build
                                que o motor achou. Nao se mexe em nada.

          ⚙ COM O QUE EU TENHO  vem ZERADA — sem habilidade adicionada,
                                sem impeto fabricado, sem tecnico. O cara
                                olha o jogo dele e vai PONDO o que tem:
                                "tenho Lideranca" -> clica; "tenho o impeto
                                Chute +1" -> clica; "meu tecnico e o Fabio
                                Capello" -> clica. A CADA insumo as
                                barrinhas se redistribuem sozinhas para a
                                melhor nota possivel com aquilo.
                                Na barra ele NAO poe a mao.

          ✎ DO MEU JEITO ...... mexe em tudo na mao; nada se reajusta
                                sozinho.

     3  o seletor de IMPETO oferecia +1, +2 e +3. So da pra ESCOLHER
        impeto de efeito +1 — os +2 e +3 sao NATIVOS, vem de fabrica.
        (Confere com a propria fonte: no `CAT` da casca, as entradas de
        vaga tipo 1 sao todas "+1".) Agora o seletor respeita as duas
        coisas: a vaga da carta (c.sl) e o teto de +1.

     4  SEM TECNICO nao ha multiplicador. O `agora()` usava o multiplicador
        do motor mesmo com o tecnico em "(nenhum)" — na aba zerada isso
        daria nota alta sem insumo nenhum.
     ======================================================================= */

  var MARCA = 'o motor pos:';

  function impPartes(s){
    s = String(s||''); var i = s.indexOf(MARCA);
    if(i < 0) return { fab: s.replace(/\s*⚒\s*$/,'').trim(), add: '' };
    return { fab: s.slice(0,i).replace(/[·\s]+$/,'').trim(),
             add: s.slice(i+MARCA.length).replace(/\s*⚒\s*$/,'').trim() };
  }
  function impMonta(fab,add){
    var a=[]; if(fab)a.push(fab); if(add)a.push(MARCA+' '+add);
    return a.join(' · ');
  }

  /* refaz o card a partir da EQUACAO, sem encostar nas barras */
  function reAplica(c){
    var vals = valores(c, _lvlDe(c));
    c.sis = vals;
    if(c.arows) c.arows.forEach(function(r){
      r[3]=vals[r[0]]; r[4]=Math.round((r[3]-r[2])*100)/100; r[5]=r[3]; });
    c.b1 = notaDe(vals, c.arows);
    try{ c.b1n=(function(A){var n=0,d=0,i,w;A=A||[];for(i=0;i<A.length;i++){w=A[i][1];if(!w)continue;n+=w*A[i][3];d+=w*A[i][2];}return d?100*n/d:b1nDe(c.tipo,c.b1);})(c.arows); }catch(e){}
    delete c._cp; delete c._n;
    try{ traducaoViva(); }catch(e){}
    try{ render(); }catch(e){}
  }

  /* ===== A PUNICAO DA TELA NAO TINHA TETO — 15/08 ========================
     O Luis viu na ficha do Hazard: trocando o impeto na mao a nota passava do
     "maximo" do motor (110,52 -> 110,58, "100,06% top"). Medido depois em
     1.500 linhas, com a conta provada contra o que o motor gravou:

       regua do MOTOR (regua.py, TETO_PUN = 9: a punicao para no 9o ponto)
          existe impeto melhor em ....... 0 de 1.500
       regua da TELA (casca, `_fal` somando ate o fim, sem teto)
          existe impeto melhor em ....... 236 de 1.500  (16%)

     Ou seja: o motor escolheu certo; quem mentia era a tela. A `_fal` da casca
     e a copia da punicao do regua.py SEM o `min(-d, TETO_PUN)`, entao ela pune
     sem limite quem esta muito abaixo do alvo — e ai qualquer edicao (impeto,
     habilidade, tecnico ou barra) reordenava tudo pelo criterio errado, com
     notas absurdas no meio do caminho (Chanathip: -3.776 na tela, -886 no motor).

     Aqui a punicao ganha o mesmo teto do motor. Uma regua so nas duas pontas. */
  try{
    if (typeof _fal === 'function' && typeof P !== 'undefined') {
      window.TETO_PUN = 9;
      window._fal = function(d, p){
        var inc = 0.25 * p / 12, t = 0, lim = Math.min(d, window.TETO_PUN), k;
        for (k = 1; k <= lim; k++) t += (1 + (k - 1) * inc) * p;
        return t;
      };
      window.PUNICAO_COM_TETO = true;
    }
  }catch(e){ window.PUNICAO_COM_TETO = false; }

  /* ===== A CADEIA DA FICHA NAO FECHAVA COM O TOTAL — 15/08 =============
     O Luis: *"entre habilidades adicionais e o total tem um gap. Que gap e
     esse? De 90 na ofensividade o cara vai pra 93 do nada."*

     A `etapas()` da casca e a cadeia VELHA: ela nao tem o MULTIPLICADOR do
     tecnico (o degrau 2 da Equacao 1) e aplica a habilidade pela formula
     antiga (% sobre o valor ja somado, travando em 99):

        e1 = min(99, base+barras) · e2 = e1+impeto · e3 = e2+tecnico
        e4 = aplicaBuff(e3)                      <- velha

     Por isso o ultimo degrau nao batia com o TOTAL: faltava o multiplicador
     (o +3 que ele viu) e sobrava/faltava a diferenca da habilidade (o 101
     que virava 99). Aqui a cadeia passa a ser a MESMA Equacao 1 do motor, e
     o multiplicador aparece onde ele nasce: no degrau do TECNICO. */
  window.etapas = function(c, lvl){
    var st, cb, nm, imp, tec, bf, out = [], i, e0, pre, e2, e3, e4;
    try{
      anc(c);
      st = agora(c, lvl || _lvlDe(c));
      cb = _contrib(lvl || _lvlDe(c));
      nm = expand(c.nm); imp = impDoMotor(st.imp);
      tec = tecVet(st.tecb || []); bf = buff(todasHabs(c, st.habs));
    }catch(e){ return []; }
    for(i = 0; i < 26; i++){
      e0  = c.base ? c.base[i] : 0;
      pre = Math.min(99, e0 + (cb[i] || 0));
      e2  = pre + nm[i] + imp[i];                       /* + impeto  */
      e3  = mult(pre, st.m) + tec[i] + (e2 - pre);      /* proficiencia, boost, impetos */
      e4  = e3 + (bf[i] ? Math.ceil(pre * bf[i][0] / 100 + bf[i][1]) : 0);
      out.push([e0, pre, e2, e3, e4]);
    }
    return out;
  };

  /* a mesma correcao para o degrau das habilidades NATIVAS */
  window._e4nat = function(c, lvl){
    var E = window.etapas(c, lvl), bf, out = [], i;
    try{ bf = buff((c.fab || []).concat(c.raras || [])); }catch(e){ bf = {}; }
    for(i = 0; i < 26; i++){
      var pre = E[i] ? E[i][1] : 0, e3 = E[i] ? E[i][3] : 0;
      out.push(e3 + (bf[i] ? Math.ceil(pre * bf[i][0] / 100 + bf[i][1]) : 0));
    }
    return out;
  };

  /* ===== O "MEU TIME" SALVO ANTES DO RENOMEIO — 15/08 ===================
     O time é lido pelo UserStateRepository e cada peça é guardada pela chave
     `id|funcao`. Como a TELA passou a chamar as funções de outro jeito
     (Atacante infiltrador -> Atacante infiltrador, Atacante finalizador -> Atacante
     finalizador, Atacante criador -> Atacante criador), o time que já estava
     salvo apontaria para funções que não existem mais NA TELA — e as peças
     sumiriam sem erro nenhum.

     ⛔ Isto NÃO toca no banco: lá as chaves continuam as antigas. Aqui só se
     traduz o que já estava guardado no navegador, uma vez. */
  try{
    var _DPV = ['Segundo'+' atacante','Ponta'+' finalizadora','Ponta'+' criadora','Ponta'+' de lança','Meia'+' lateral atacante','Meia'+' lateral cruzador','Meia'+' de ligação armador','Meia'+' de ligação avançado','Meia'+' ofensivo armador','Meia'+' central armador','Meia'+' central de chegada','Ala'+' atacante'];
    var _DPN = ['Atacante infiltrador','Atacante finalizador','Atacante criador','Atacante infiltrador','Ala finalizador','Ala cruzador','Meia armador','Meia de arranque','Meia ofensivo','Meia armador','Meia de arranque','Ala finalizador'];
    var DEPARA = {};
    for (var _di = 0; _di < _DPV.length; _di++) DEPARA[_DPV[_di]] = _DPN[_di];
    var bruto = JSON.stringify(MT || {});
    if (bruto && _DPV.some(function(_x){return bruto.indexOf('|' + _x) >= 0;})) {
      var novo = bruto;
      for (var k in DEPARA) novo = novo.split('|' + k).join('|' + DEPARA[k]);
      if (novo !== bruto) {
        MT = Object.assign({form:'4-3-3',slots:[],banco:[],elenco:[],nome:'Meu time'}, JSON.parse(novo));
        try{ userStateSave(); }catch(e){}
        console.log('%cMEU TIME: chaves antigas traduzidas para os nomes novos '
                    + 'das funcoes (so na tela; o banco nao mudou)',
                    'color:#22c58b;font-weight:700');
      }
    }
  }catch(e){}

  /* ---- 1 · o ⚡ OTIMIZAR devolve a ANCORA inteira --------------------- */
  window.restaurarMotor = function(key){
    var c=_card(key); if(!c) return;
    var a=anc(c);
    delete c._habs; delete c._tec; delete c._tecNome; delete c._ori;
    c.imp = a.imp;
    c.imps = (c.imps||[]).filter(function(x){ return !x.f; });
    impPartes(a.imp).add.split(/\s+[·+]\s+/).forEach(function(n){
      n=n.trim(); if(n) c.imps.push({n:n, c:0, f:1}); });
    c.sisBar = a.sisBar.map(function(r){ return r.slice(); });
    if(a.sobra!==undefined) c.sobra = a.sobra;
    c.sis = a.v.slice();
    if(c.arows) c.arows.forEach(function(r){
      r[3]=c.sis[r[0]]; r[4]=Math.round((r[3]-r[2])*100)/100; r[5]=r[3]; });
    c.b1 = notaDe(c.sis, c.arows);
    try{ c.b1n=(function(A){var n=0,d=0,i,w;A=A||[];for(i=0;i<A.length;i++){w=A[i][1];if(!w)continue;n+=w*A[i][3];d+=w*A[i][2];}return d?100*n/d:b1nDe(c.tipo,c.b1);})(c.arows); }catch(e){}
    delete c._cp; delete c._n;
    try{ traducaoViva(); }catch(e){}
    try{ render(); }catch(e){}
    try{ reabrir(key); }catch(e){}
  };
  /* ---- 2 · as abas ----------------------------------------------------- */
  function modo(){ return window.FichaState?window.FichaState.uiMode():'motor'; }
  function _pintaModo(){
    /* no <html> tambem: o <body> pode nao existir quando isto roda, e o CSS
       das travas depende deste atributo para desligar barra e botao. */
    try{ document.documentElement.setAttribute('data-encmodo', modo()); }catch(e){}
    try{ if(document.body) document.body.setAttribute('data-encmodo', modo()); }catch(e){}
  }
  try{ document.addEventListener('DOMContentLoaded', _pintaModo); }catch(e){}

  /* a barra so aceita mao humana na aba DO MEU JEITO */
  function travaBarra(){ return modo() !== 'livre'; }
  /* na aba MAXIMO nada se mexe */
  function travaInsumo(){ return modo() === 'motor'; }

  function guarda(nome, fn){
    var f = window[nome]; if(typeof f !== 'function') return;
    window[nome] = function(){
      if(fn()) return;
      return f.apply(this, arguments);
    };
  }
  guarda('editBar', travaBarra);
  guarda('setBar',  travaBarra);
  guarda('addHab',  travaInsumo);
  guarda('remHab',  travaInsumo);
  guarda('toggleCondCard', travaInsumo);

  /* depois de POR um insumo na aba "com o que eu tenho", as barrinhas se
     acertam sozinhas para a maior nota possivel com o que esta la */
  function reBarras(key){
    if(modo() !== 'insumos') return;
    try{ distBarras(_card(key), key); }catch(e){}
  }
  function porInsumo(nome){
    var f = window[nome]; if(typeof f !== 'function') return;
    window[nome] = function(key){
      if(travaInsumo()) return;
      var r = f.apply(this, arguments);
      reBarras(key);
      try{ reabrir(key); }catch(e){}
      return r;
    };
  }

  porInsumo('_trocaHabs');
  porInsumo('trocaTec');

  /* ZERA a aba "com o que eu tenho": nenhuma habilidade adicionada,
     nenhum impeto fabricado, nenhum tecnico. O nativo do card fica —
     ele veio de fabrica, o cara nao escolheu. */
  function zeraInsumos(key){
    var c=_card(key); if(!c) return;
    var a=anc(c);
    c._habs = [];
    c._tec  = [];
    c._tecNome = '';
    c.imp = impMonta(impPartes(a.imp).fab, '');
    c.imps = (c.imps||[]).filter(function(x){ return !x.f; });
    delete c._cp; delete c._n;
    try{ distBarras(c, key); }catch(e){ reAplica(c); }
  }

  window.encModo = function(m, key){
    if(!window.FichaState)return;
    window.FichaState.setMode(m,key);
    _pintaModo();
    try{
      if(m === 'insumos') zeraInsumos(key);       /* vem zerada  */
      else window.restaurarMotor(key);            /* maximo e do meu jeito */
    }catch(e){}
    try{ reabrir(key); }catch(e){}
  };
  _pintaModo();

  /* ---- 3 · o IMPETO ---------------------------------------------------- */
  window.editImp = function(key, nome){
    var c=_card(key); if(!c) return;
    if(travaInsumo()) return;
    try{ _marca(key); }catch(e){}
    anc(c);
    var P = impPartes(c.imp), add = (!nome || nome === '(nenhum)') ? '' : nome;
    c.imp = impMonta(P.fab, add);
    c.imps = (c.imps||[]).filter(function(x){ return !x.f; });
    if(add) c.imps.push({ n:add, c:0, f:1 });
    if(modo() === 'insumos'){ try{ distBarras(c, key); }catch(e){ reAplica(c); } }
    else reAplica(c);
    try{ reabrir(key); }catch(e){}
  };

  /* SO efeito +1 pode ser escolhido. Os +2 e +3 sao nativos, de fabrica.
     Alem disso respeita a VAGA da carta (c.sl), que a versao anterior
     tinha perdido ao montar a lista pelo catalogo inteiro. */
  window.impOpcoes = function(c){
    var fora={}, P=impPartes(c && c.imp), vaga=null, vis={}, out=[], i, n;
    String(P.fab).replace(/^de f[aá]brica:\s*/i,'')
      .split(/\s+[·+]\s+/).forEach(function(x){ x=x.trim(); if(x) fora[x]=1; });
    if(c && c.sl && (c.sl[0] || c.sl[1])) vaga = c.sl;
    for(i=0;i<CAT.length;i++){
      n = CAT[i][0];
      if(!/\+\s*1$/.test(n)) continue;              /* a regra do Luis */
      if(vaga && !vaga[CAT[i][1]]) continue;        /* a vaga da carta */
      if(fora[n] || vis[n]) continue;
      vis[n]=1; out.push(n);
    }
    out.sort(function(a,b){ return a.localeCompare(b,'pt'); });
    return out;
  };

  /* ---- 5 · as abas explicadas no balaozinho (ordem do Luis, 15/08) ------
     "passa o mouse em cima e aparece uma caixinha de dialogo explicando" */
  /* Os textos falam com QUEM USA a tela, nao com quem a fez (ordem do Luis,
     15/08: "essa explicacao e pro publico geral, nao e pra mim"). */
  var ABAS = [
    ['motor', '\u26a1 M\u00c1XIMO',
     'A maior pontua\u00e7\u00e3o que esta carta consegue alcan\u00e7ar: todos os ' +
     'insumos no melhor arranjo poss\u00edvel. \u00c9 a refer\u00eancia da carta \u2014 ' +
     'nesta aba nada \u00e9 alterado.'],
    ['insumos', '\u2699 COM O QUE EU TENHO',
     'Monte a carta com o que voc\u00ea realmente tem no seu jogo. Ela come\u00e7a ' +
     'vazia: v\u00e1 pondo as habilidades, o \u00edmpeto e o t\u00e9cnico que est\u00e3o ' +
     'na sua m\u00e3o e, a cada um deles, a distribui\u00e7\u00e3o dos pontos se ' +
     'ajusta sozinha para a melhor nota poss\u00edvel com aquilo.'],
    ['livre', '\u270e DO MEU JEITO',
     'Espa\u00e7o livre para planejar. Altere o que quiser \u2014 pontos, ' +
     'habilidades, \u00edmpeto e t\u00e9cnico \u2014 e veja no que d\u00e1. ' +
     'Aqui nada se reajusta sozinho.']
  ];
  window._modoBar = function(K){
    var M = modo(), h = '<div class=encabas>', i, on, q = String.fromCharCode(39);
    for(i=0;i<ABAS.length;i++){
      on = (ABAS[i][0] === M);
      h += '<button class="encaba' + (on?' encabaon':'') + '"' +
           ' data-tip="' + ABAS[i][2].replace(/"/g,'&quot;') + '"' +
           ' onclick="encModo(' + q + ABAS[i][0] + q + ',' + q + K + q + ')">' +
           ABAS[i][1] + '</button>';
    }
    return h + '</div>';
  };

  /* ===== A PROVA — as duas contas ainda dao o mesmo resultado? =============
     Os casos abaixo foram calculados pelo PROPRIO equacao.py na hora de gerar
     esta tela. A conta daqui roda nos mesmos casos e compara.
     Mudou a formula do motor -> o esperado muda junto -> a tela acusa sozinha.
     (ordem do Luis, 15/08: "deixa pronto pra atualizar juntos") */
  var PROVA = [{"base": [80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80], "lvl": {"shooting": 5}, "m": 1.036, "tecb": ["finishing"], "nm": [], "habs": [], "esperado": [82, 82, 82, 82, 82, 82, 89, 82, 88, 88, 82, 82, 82, 82, 82, 82, 82, 82, 82, 82, 82, 82, 82, 82, 82, 82]}, {"base": [95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95, 95], "lvl": {"dribbling": 10}, "m": 1.0365, "tecb": ["dribbling"], "nm": [[2, 3]], "habs": ["Elástico"], "esperado": [98, 99, 108, 99, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98]}, {"base": [70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70], "lvl": {"passing": 20, "dribbling": 3}, "m": 1.0355, "tecb": ["lowPass", "stamina"], "nm": [[4, 4]], "habs": ["Passe na medida"], "esperado": [72, 75, 75, 75, 98, 97, 72, 72, 72, 73, 72, 72, 72, 72, 72, 72, 73, 72, 72, 72, 72, 72, 72, 72, 72, 72]}, {"base": [99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99], "lvl": {}, "m": 1.036, "tecb": ["speed"], "nm": [[15, 5]], "habs": ["Chutes com decolagem"], "esperado": [99, 99, 99, 99, 99, 99, 99, 99, 99, 100, 100, 99, 103, 99, 99, 104, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99]}, {"base": [88, 88, 88, 88, 88, 88, 88, 88, 88, 88, 88, 88, 88, 88, 88, 88, 88, 88, 88, 88, 88, 88, 88, 88, 88, 88], "lvl": {"defending": 12}, "m": 1.03, "tecb": ["ballWinning"], "nm": [], "habs": ["Interceptação", "Carrinho"], "esperado": [90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 101, 105, 99, 102, 90, 90, 90, 90, 90]}, {"base": [60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60], "lvl": {"lowerBodyStrength": 25}, "m": 1.0341, "tecb": [], "nm": [[17, 2]], "habs": [], "esperado": [62, 62, 62, 62, 62, 62, 62, 62, 62, 62, 87, 62, 87, 62, 62, 62, 87, 64, 62, 62, 62, 62, 62, 62, 62, 62]}, {"base": [97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97], "lvl": {"shooting": 8, "passing": 8}, "m": 1.0365, "tecb": ["finishing", "curl"], "nm": [[6, 4]], "habs": ["Folha seca", "Malícia"], "esperado": [99, 99, 99, 99, 99, 99, 104, 99, 99, 104, 99, 99, 100, 99, 99, 102, 99, 99, 99, 99, 101, 99, 99, 99, 99, 99]}, {"base": [40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40], "lvl": {}, "m": 1.03, "tecb": [], "nm": [], "habs": [], "esperado": [41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41]}];
  try{
    var falhou=[];
    (PROVA||[]).forEach(function(p,ix){
      var cf={ base:p.base, nm:p.nm, fab:[], raras:[], TECB:p.tecb };
      var v=conta(cf, {lvl:p.lvl, tecb:p.tecb, imp:'', habs:p.habs, m:p.m});
      for(var i=0;i<26;i++){
        if(Math.round(v[i])!==Math.round(p.esperado[i])){
          falhou.push({caso:ix, atributo:i, tela:Math.round(v[i]), motor:p.esperado[i]});
          break; }
      }
    });
    window.CONTA_DESALINHADA = falhou.length;
    window.CONTA_PROVAS = (PROVA||[]).length;
    if(falhou.length){
      console.warn('A CONTA DA TELA ESTA DESALINHADA DO MOTOR — '+falhou.length+
                   ' de '+PROVA.length+' casos de prova falharam', falhou);
      var aviso=document.createElement('div');
      aviso.style.cssText='position:fixed;left:8px;bottom:8px;z-index:99999;background:#a00;'+
        'color:#fff;font:12px system-ui;padding:6px 10px;border-radius:4px;max-width:320px';
      aviso.textContent='A conta da tela está desalinhada do motor ('+falhou.length+' de '+
        PROVA.length+' provas). O que você editar aqui pode não bater com a pontuação. '+
        'Detalhe no Console (F12).';
      if(document.body) document.body.appendChild(aviso);
      else document.addEventListener('DOMContentLoaded',function(){document.body.appendChild(aviso);});
    }
  }catch(e){ }

  window._contaDoMotor = { conta:conta, valores:valores, buff:buff, achaM:achaM,
                           impDoMotor:impDoMotor, anc:anc, agora:agora, mDoNome:mDoNome };
})();



/* bloco JavaScript 20 */

/* O CAMPINHO NO CABECALHO — 15/08. So apresentacao: nao encosta em nota. */
(function(){
 if(window.CAMPINHO_1508) return; window.CAMPINHO_1508 = true;
 /* o mesmo desenho da ficha do jogo, de cima (ataque) para baixo */
 var CAMPO=[["PE","CA","PD"],["","SA",""],["MLE","MO","MLD"],["","MC",""],
            ["","VOL",""],["LE","ZC","LD"],["","GK",""]];
 function irmAll(c){var b=String(c.id).split("@")[0];
  return D.filter(function(x){return x.id!=="MOLDE"&&String(x.id).split("@")[0]===b;});}
 function sig(p){ return (typeof SIGJ!=="undefined"&&SIGJ[p])?SIGJ[p]:p; }
 function nomeP(p){ return (typeof POSN!=="undefined"&&POSN[p])?POSN[p]:p; }
 /* A COR E O TAMANHO saem da PROFICIENCIA (ordem do Luis, 15/08):
    o de mais pontos vem maior e no verde mais forte; os outros vao clareando.
    *"nao e porque tem zagueiro de saida que o outro vai ser preto — pode ser
    um verde mais claro"* — a escala vai do verde medio ao verde CLARO, nunca
    ao escuro. E eles ficam um EMBAIXO do outro, nao lado a lado. */
 function cores(p){
  /* 15/08, 2o ajuste: a escala ia a um verde tao claro que o ultimo botao
     sumia no fundo. Agora vai do verde forte ao verde MEDIO, texto branco
     em todos e borda mais escura — nenhum se confunde com o fundo. */
  var l=Math.round(80-56*p), sat=Math.round(30+45*p);
  return {bg:"hsl(152 "+sat+"% "+l+"%)",
          bd:"hsl(152 "+(sat+16)+"% "+Math.round(l-15)+"%)",
          tx:"#ffffff",
          pad:(5+4*p).toFixed(1)+"px "+(9+4*p).toFixed(1)+"px",
          fn:(11+2.5*p).toFixed(1)+"px",
          fb:(13.5+4.5*p).toFixed(1)+"px"};
 }
 /* O NOME DO IMPETO NATIVO EM PORTUGUES (Luis, 15/08: "ele esta puxando o
    nome em ingles, tem que puxar o nome em portugues"). O efscout devolve
    "Stealing +3"; o `const CAT` da casca fala portugues. Casando o EFEITO
    atributo a atributo sai o nome certo — sem tabela de traducao a manter. */
 /* 15/08: a POSICAO NATIVA e do CARD, nao da linha. Em linha migrada ou
    de 2a posicao o `np` vem diferente, e o bloquinho mudava quando o
    Luis trocava de funcao. Aqui ela sai do irmao nativo — e nunca muda. */
 window.npFixo=function(c){
  try{
   var b=String(c.id).split("@")[0];
   var irm=D.filter(function(x){return x.id!=="MOLDE"&&String(x.id).split("@")[0]===b;});
   var nat=irm.find(function(x){return !x.MIG && !x.sec;});
   return (nat&&nat.np)||c.np;
  }catch(e){ return c.np; }
 };
 window.pimpPT=function(n,ef){
  try{
   if(!n) return n;
   if(CAT.some(function(x){return x[0]===n;})) return n;
   var v=expand(ef), i, j, f, ok, idx=[], nivel=0;
   /* 1) o nome exato, quando o efeito bate atributo a atributo */
   for(j=0;j<CAT.length;j++){ f=expand(CAT[j][2]); ok=true;
    for(i=0;i<26;i++) if(f[i]!==v[i]){ ok=false; break; }
    if(ok) return CAT[j][0]; }
   /* 2) o impeto nativo pode vir em nivel que nao existe no catalogo
         (o catalogo so tem +1/+2/+3 e o nativo chega a +5). Ai casa-se pelo
         CONJUNTO DE ATRIBUTOS e leva-se o nivel junto:
         "Technique +5" -> Tecnica (mesmos 4 atributos) -> "Tecnica +5". */
   for(i=0;i<26;i++) if(v[i]){ idx.push(i); if(v[i]>nivel) nivel=v[i]; }
   if(idx.length){
    for(j=0;j<CAT.length;j++){
     f=expand(CAT[j][2]); ok=true;
     for(i=0;i<26;i++) if((f[i]>0)!==(v[i]>0)){ ok=false; break; }
     if(ok) return String(CAT[j][0]).replace(/\s*\+\d+\s*$/,'')+' +'+nivel;
    }
   }
  }catch(e){}
  return n;
 };
 /* as duas pecas do cabecalho, cada uma na sua coluna (Luis, 15/08) */
 window.selPos=function(p,key){
  window._SELPOS=(window._SELPOS===p)?null:p;   /* clicar de novo desmarca */
  try{ reabrir(key); }catch(e){}
 };
 window.cbFuncoes=function(c){ posLinha(c); return window._cbFuncoes; };
 window.cbCampo  =function(c){ posLinha(c); return window._cbCampo;   };
 window.posLinha=function(c){
  var np=c.np, est={}, i;
  /* 15/08: o campinho segue a FUNCAO ABERTA, nao a nativa. Ordem do Luis:
     "quando eu clicar em Atacante infiltrador ele vai pro SA; quando eu clicar
      em Ala finalizador, la no campinho muda pra MLE ou MLD".
     As estrelinhas sairam. */
  var np=c.np, est={}, i, daFuncao={};
  (c.sp||[]).forEach(function(x){ if(x[0]!==np) est[x[0]]=x[1]; });
  /* 15/08: a posicao acesa. O `funcDaPos` depende do ESTILO do card, e por
     isso deixava o campinho apagado em card cujo estilo remapeia a posicao
     (o Luis pegou no Ruud Gullit "Armador criativo", em Atacante infiltrador).
     CONFERIDO no regra.json: cada posicao tem DUAS funcoes possiveis —
     REGRA["MO"] = [estilos, "Atacante infiltrador", "Meia ofensivo"].
     Entao a posicao desta ficha e: a que o estilo aponta OU, se nenhuma,
     qualquer posicao que tenha esta funcao entre as duas dela. */
  ["PE","CA","PD","SA","MLE","MO","MLD","MC","VOL","LE","ZC","LD","GK"]
   .forEach(function(p){ var f=null;
    try{ f=(typeof funcDaPos==="function")?funcDaPos(p,c.modelo):null; }catch(e){}
    /* 15/08 — CONFERIDO na base: o Hazard 88035823751302 tem np=MO e
       sec="MC/MLE/PD/PE/SA". MLD NAO esta la. O campinho acendia MLD ao abrir
       "Ala finalizador" so porque a REGRA diz que MLD gera essa funcao —
       mas a regra e da posicao, nao do card. So acende o que o card exerce. */
    if(!(p===np || est[p]!==undefined)) return;
    if(f && f===c.tipo){ daFuncao[p]=1; return; }
    try{ var r=(typeof TJ_REGRA!=="undefined")?TJ_REGRA[p]:null;
     if(r && (r[1]===c.tipo || r[2]===c.tipo)) daFuncao[p]=1;
     if(!daFuncao[p] && p==="SA" && typeof TJ_SA!=="undefined"){
      var q=TJ_SA[c.modelo]||"MO", r2=(typeof TJ_REGRA!=="undefined")?TJ_REGRA[q]:null;
      if(r2 && (r2[1]===c.tipo || r2[2]===c.tipo)) daFuncao[p]=1; }
    }catch(e){}
   });
  if(!Object.keys(daFuncao).length){
   ["PE","CA","PD","SA","MLE","MO","MLD","MC","VOL","LE","ZC","LD","GK"]
    .forEach(function(p){ var f=null;
     try{ f=(typeof funcDaPos==="function")?funcDaPos(p,c.modelo):null; }catch(e){}
     if(f && f===c.tipo) daFuncao[p]=1;
     try{ var r=(typeof TJ_REGRA!=="undefined")?TJ_REGRA[p]:null;
      if(r && (r[1]===c.tipo||r[2]===c.tipo)) daFuncao[p]=1; }catch(e){}
    });
  }
  var _minhas=[np].concat(Object.keys(est));
  /* ===== A REGRA SIMETRICA DO CAMPINHO (Luis, 15/08) ====================
       clicou na FUNCAO  ->  acende as POSICOES onde ela pode ser exercida
       clicou na POSICAO ->  acende as FUNCOES que ela pode exercer
     O azul quer dizer sempre "isto corresponde ao que voce clicou". Um lado
     e a pergunta, o outro e a resposta.
       clica em Atacante infiltrador -> acendem SA e MAT no campo
       clica em SA -> acendem Atacante infiltrador e Meia ofensivo na lista
     Clicar numa POSICAO nao abre ficha: so mostra as opcoes. Quem abre e o
     clique na FUNCAO — assim quem entra pela posicao escolhe qual quer ver. */
  function funcsDaPos(p){
   var out=[], f=null, r=null;
   try{ f=(typeof funcDaPos==="function")?funcDaPos(p,c.modelo):null; }catch(e){}
   try{ r=(typeof TJ_REGRA!=="undefined")?TJ_REGRA[p]:null; }catch(e){}
   irmAll(c).forEach(function(y){
    if(y.tipo===f || (r && (r[1]===y.tipo || r[2]===y.tipo))){
     if(out.indexOf(y.tipo)<0) out.push(y.tipo); }
   });
   return out;
  }
  var _sel = (window._SELPOS && _minhas.indexOf(window._SELPOS)>=0) ? window._SELPOS : null;
  var _funcsSel = _sel ? funcsDaPos(_sel) : null;
  if(_sel){ daFuncao={}; daFuncao[_sel]=1; }
  var cel=function(p){
   if(!p) return "<i class=cbv></i>";
   var aqui=(daFuncao[p]===1), nat=(p===np), sec=(est[p]!==undefined), f=null, alvo=null;
   try{ f=(typeof funcDaPos==="function")?funcDaPos(p,c.modelo):null; }catch(e){}
   if(f) alvo=irmAll(c).find(function(y){return y.tipo===f;});
   var cls="cbp "+(aqui?"cbnat":((nat||sec)?"cbsec":"cboff"))+(nat?" cbfab":"");
   var t=aqui?("esta ficha: "+c.tipo):(nat?("posicao de fabrica: "+nomeP(p)):
        (sec?("tambem joga: "+nomeP(p)+(f?" — "+f:"")):nomeP(p)));
   var cl=(_minhas.indexOf(p)>=0)?(" onclick=\"selPos('"+p+"','"+c.id+"|"+c.tipo+"')\""
           +" style=\"cursor:pointer\""):"";
   return "<span class=\""+cls+"\""+cl+" title=\""+t+"\">"+sig(p)+"</span>";
  };
  var campo=CAMPO.map(function(l){return "<div class=cbl>"+l.map(cel).join("")+"</div>";}).join("");
  var irm=irmAll(c);
  irm.forEach(function(x){ if(x._n===undefined) x._n=nota(x); });
  irm.sort(function(a,b){ return b._n-a._n; });
  var mx=irm.length?irm[0]._n:0, mn=irm.length?irm[irm.length-1]._n:0;
  /* 15/08 — a sigla do botao e a POSICAO QUE ESTE CARD EXERCE, nao a da
     funcao. Luis: "ele so pode ser MLE, entao nao poe MLE/MLD". */
  function sigsDoCard(tipo){
   var out=[];
   _minhas.forEach(function(p){
    var f=null, r=null;
    try{ f=(typeof funcDaPos==="function")?funcDaPos(p,c.modelo):null; }catch(e){}
    try{ r=(typeof TJ_REGRA!=="undefined")?TJ_REGRA[p]:null; }catch(e){}
    if((f===tipo)||(r&&(r[1]===tipo||r[2]===tipo))){
     if(out.indexOf(sig(p))<0) out.push(sig(p)); }
   });
   if(!out.length) return (typeof sigDe==="function")?sigDe(tipo):"";
   return out.join("/");
  }
  var bts=irm.map(function(x,ix){
   /* o tom vem da POSICAO NA LISTA, nao da diferenca de nota: com oito
      funcoes, oito tons — a 1a no verde escuro e a ultima bem clara. */
   var p=(irm.length>1)?(1-(ix/(irm.length-1))):1, k=cores(p),
       aq=_funcsSel?(_funcsSel.indexOf(x.tipo)>=0):(x.tipo===c.tipo);
   return "<span class=\"cbfn"+(aq?" cbfnq":"")+"\" style=\"background:"+k.bg+
    ";border-color:"+(aq?"#ffffff":k.bd)+";color:"+k.tx+";padding:"+k.pad+
    "\" onclick=\"reabrir('"+x.id+"|"+x.tipo+"')\" title=\""+x.tipo+
    (aq?" — e esta ficha":"")+"\"><i style=\"font-size:"+k.fn+"\">"+x.tipo+
    "</i><u>"+sigsDoCard(x.tipo)+"</u><b style=\"font-size:"+
    k.fb+"\">"+x._n.toFixed(1)+"</b></span>";
  }).join("");
  var titulo=irm.length>1?("ESTE CARD NAS "+irm.length+" FUN\u00c7\u00d5ES"):"A FUN\u00c7\u00c3O DESTE CARD";
  /* 15/08: primeiro as FUNCOES, e o campinho ao lado delas — ordem do
     Luis: "em vez de voce colocar o campo, voce coloca as funcoes; ai
     depois do lado das funcoes voce coloca o campo". */
  window._cbFuncoes="<div class=cbfnl>"+bts+"</div>";
  window._cbCampo="<div class=cbcampo><div class=cbnv>"+
   (_sel ? (nomeP(_sel)+" <b>"+sig(_sel)+"</b>")
         : (function(){var k=Object.keys(daFuncao);
            if(!k.length) return nomeP(np)+" <b>"+sig(np)+"</b>";
            return nomeP(k[0])+" <b>"+k.map(sig).join(" · ")+"</b>";})())+
   "</div>"+campo+"</div>";
  return "<div class=cbwrap><div class=cbfns>"+
   "<div class=cbfnl>"+bts+"</div></div>"+
   "<div class=cbcampo><div class=cbnv>"+
   (function(){var k=Object.keys(daFuncao);
    if(!k.length) return nomeP(np)+" <b>"+sig(np)+"</b>";
    return nomeP(k[0])+" <b>"+k.map(sig).join(" · ")+"</b>";})()+
   "</div>"+campo+"</div></div>";
 };
})();
