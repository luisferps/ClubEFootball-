/* Design de colecoes do legado, comportamento novo e dados cadastrais. */
(()=>{
'use strict';
let root=null,seq=0,controller=null,data=null,busy=false,error='',active=false;
const title=()=>active?'Boxes em andamento':'Boxes cadastradas';
const defaultState=()=>({p_box:null,p_busca:'',p_limite:24,p_offset:0,p_ordem:'recentes'});
const savedPages=new Map(),storageKey='site-novo:boxes:navegacao:v1:';
let state=defaultState(),catalogState=null;
function validState(s){return s&&(s.p_box===null||typeof s.p_box==='string'&&s.p_box.trim().length>0&&s.p_box.length<=300)&&typeof s.p_busca==='string'&&s.p_busca.length<=100&&s.p_limite===24&&Number.isSafeInteger(s.p_offset)&&s.p_offset>=0&&s.p_offset<=100000&&s.p_offset%24===0&&['recentes','pontuacao'].includes(s.p_ordem);}
function restoreState(){
 let saved=savedPages.get(active);
 if(!saved)try{saved=JSON.parse(window.sessionStorage.getItem(storageKey+(active?'andamento':'cadastradas')));}catch{}
 if(saved&&validState(saved.state)&&(saved.state.p_box===null?saved.catalog===null:validState(saved.catalog)&&saved.catalog.p_box===null)){
  state={...defaultState(),...saved.state};catalogState=saved.catalog?{...saved.catalog}:null;
 }else{state=defaultState();catalogState=null;}
}
function saveState(){
 const saved={state:{...state},catalog:catalogState?{...catalogState}:null};savedPages.set(active,saved);
 try{window.sessionStorage.setItem(storageKey+(active?'andamento':'cadastradas'),JSON.stringify(saved));}catch{}
}
const esc=window.SiteNovoCommon.escapeHTML;
const cardCount=n=>n+' '+(n===1?'card':'cards');
const registeredCards=n=>cardCount(n)+' '+(n===1?'cadastrado':'cadastrados');
const boxCount=n=>n+' '+(n===1?'box':'boxes');
const openCardsLabel=n=>n===1?'Ver o card →':'Ver todos os '+n+' cards →';
function picture(c){let url=null;try{const u=new URL(c.foto_url);if(u.protocol==='https:')url=u.href;}catch{}
 return url?'<img src="'+esc(url)+'" alt="Card de '+esc(c.nome)+'" loading="lazy" referrerpolicy="no-referrer">':'<span class="nb-no-photo">Sem imagem</span>';
}
const number=v=>v.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
// A quantidade vem do banco. O navegador apenas desenha os cinco ícones.
function stars(value){
 if(!Number.isInteger(value)||value<0||value>5)throw new Error('Estrelas de contratação inválidas.');
 const label='Contratação: '+value+' de 5 estrelas';
 return '<span class="nb-stars" role="img" aria-label="'+label+'" title="'+label+'" data-stars="'+value+'">'
  +Array.from({length:5},(_,i)=>'<svg class="nb-star '+(i<value?'nb-star-filled':'nb-star-empty')+'" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="m12 2.8 2.75 5.57 6.15.9-4.45 4.33 1.05 6.13L12 16.84l-5.5 2.89 1.05-6.13L3.1 9.27l6.15-.9Z"/></svg>').join('')+'</span>';
}
function legend(){
 return data&&!busy&&!error?'<section class="nb-legend" aria-label="Legenda das estrelas de contratação">'
  +'<div class="nb-legend-heading"><strong>Vale a pena contratar?</strong></div>'
  +'<div class="nb-legend-levels">'+data.regua.map(f=>'<div class="nb-legend-level" data-stars="'+f.estrelas+'">'+stars(f.estrelas)+'<span>'+esc(f.rotulo)+'</span></div>').join('')+'</div></section>':'';
}
function card(c,index){
 const analyses=c.analises||[];
 const best=analyses[0];
 const href='ficha.html?card='+encodeURIComponent(c.card_id)+(best?.linha_id?'&amp;linha='+encodeURIComponent(best.linha_id):'');
 const hiringLabel=best?data.regua.find(f=>f.estrelas===best.estrelas)?.rotulo||best.etiqueta:'';
 const score=best?'<b title="Pontuação da análise">'+number(best.pontuacao)+'</b>'+'<span class="nb-hiring" data-stars="'+best.estrelas+'"><span class="nb-hiring-label">Contratação</span>'+stars(best.estrelas)+'<span class="nb-hiring-verdict">'+esc(hiringLabel)+'</span></span>':'<small class="nb-pending">Análise ainda não publicada</small>';
 const details=[['Estilo de jogo',(c.estilos||[]).map(s=>s.nome).join(' / ')||'Sem estilo de jogo']].map(([label,value])=>'<span class="nb-identity-row"><span class="nb-identity-label">'+label+'</span><span class="nb-identity-value">'+esc(value)+'</span></span>').join('');
 const main='<a class="nb-rated-player" href="'+href+'" target="_blank" rel="noopener"><span class="nb-rank">'+(index+1+(state.p_box?state.p_offset:0))+'</span>'+picture(c)+'<span class="nb-player-info"><strong>'+esc(c.nome)+'</strong><span class="nb-position">'+esc(c.posicao||'—')+'</span><span class="nb-identity">'+details+'</span>'+(c.regua_vigente===false?'<span class="nb-regua-antiga" title="Nota da regua anterior: esta linha ainda nao passou pelo Otimizador novo">Regua antiga</span>':'')+'</span><span class="nb-rating">'+score+'</span></a>';
 return '<article class="nb-entry">'+main+'</article>';
}
function sortControl(){return !active&&!state.p_box?'<div class="nb-sort"><label>Ordenar por <select data-nb-sort aria-label="Ordenar boxes"><option value="recentes" '+(state.p_ordem==='recentes'?'selected':'')+'>Últimas</option><option value="pontuacao" '+(state.p_ordem==='pontuacao'?'selected':'')+'>Melhores</option></select></label><small>Esta lista não inclui as boxes em andamento.</small></div>':'';}
function boxMeta(b){return active?'':'<div class="nb-meta"><span>'+(b.data_oferta?'Data da oferta: ':'')+esc(b.data_rotulo)+'</span></div>';}
function change(e){if(e.target.matches?.('[data-nb-sort]')&&['recentes','pontuacao'].includes(e.target.value)){state.p_ordem=e.target.value;state.p_offset=0;load();}}
function pages(){
 if(!data||busy||error||!data.total)return '';
 const current=Math.floor(state.p_offset/24)+1,total=Math.ceil(data.total/24),numbers=new Set([1,total]);
 for(let p=Math.max(1,current-2);p<=Math.min(total,current+2);p++)numbers.add(p);
 let last=0;
 return '<nav class="nb-pages" aria-label="Páginas de Boxes"><button data-nb-page="'+(current-1)+'" '+(current===1?'disabled':'')+'>← Anterior</button>'+[...numbers].sort((a,b)=>a-b).map(p=>{const gap=last&&p>last+1?'<span>…</span>':'';last=p;return gap+'<button data-nb-page="'+p+'" '+(p===current?'aria-current="page"':'')+'>'+p+'</button>';}).join('')+'<button data-nb-page="'+(current+1)+'" '+(!data.tem_mais?'disabled':'')+'>Próxima →</button><span class="nb-page-summary">Página '+current+' de '+total+' · '+(state.p_offset+1)+'–'+(state.p_offset+data.itens.length)+' de '+data.total+'</span></nav>';
}
function paint(){
 if(!root)return;
 let body='';
 if(busy)body='<p class="nb-message" role="status">Carregando '+(state.p_box?'cards':'boxes')+'…</p>';
 else if(error)body='<div class="nb-message" role="alert"><p>'+esc(error)+'</p><button data-nb-retry>Tentar novamente</button></div>';
 else if(data?.status==='vazio')body='<p class="nb-message">Nenhum '+(state.p_box?'card cadastrado nesta box.':'resultado para esta busca.')+'</p>';
 else if(data)body=state.p_box?'<div class="nb-card-grid">'+data.itens.map(card).join('')+'</div>':'<div class="nb-grid">'+data.itens.map(b=>'<section class="nb-box"><header><h2 title="'+esc(b.box)+'">'+esc(b.box)+'</h2><span>'+cardCount(b.total_cards)+'</span></header>'+boxMeta(b)+'<div class="nb-preview">'+b.cards.map(card).join('')+'</div><button class="nb-open" data-nb-box="'+esc(b.box)+'">'+openCardsLabel(b.total_cards)+'</button></section>').join('')+'</div>';
 root.innerHTML='<section class="nb-boxes '+(active?'nb-active ':'')+(state.p_offset===0?'nb-firstpage':'')+'"><header class="nb-heading">'+(state.p_box?'<button data-nb-back>← '+esc(title())+'</button>':'')+'<div><h1>'+esc(state.p_box||title())+'</h1><p>'+(data&&!busy&&!error?(state.p_box?registeredCards(data.total):boxCount(data.total)+' · '+registeredCards(data.total_cards)):'Explore as coleções e seus cards.')+'</p></div>'+(!state.p_box?'<form data-nb-search><input name="busca" type="search" maxlength="100" placeholder="Box ou jogador" aria-label="Pesquisar por nome da box ou do jogador" value="'+esc(state.p_busca)+'"><button>Buscar</button>'+(state.p_busca?'<button type="button" data-nb-clear>Limpar</button>':'')+'</form>':'')+'</header>'+sortControl()+legend()+body+pages()+'</section>';
}
async function load(){
 saveState();
 const ticket=++seq;controller?.abort();controller=new AbortController();const ctrl=controller;
 const timer=setTimeout(()=>ctrl.abort(),12000);busy=true;error='';data=null;paint();
 try{const result=await window.SiteNovoBoxesAPI.read({...state,p_degrau:window.SiteNovoDegrau?.get()??3},ctrl.signal,active);if(ticket!==seq||!root)return;data=result;}
 catch(e){if(ticket!==seq||!root)return;error=e.name==='AbortError'?'A consulta demorou. Tente novamente.':e.message;}
 finally{clearTimeout(timer);if(ticket===seq&&root){busy=false;paint();}}
}
function click(e){
 const t=e.target.closest('button');if(!t||!root?.contains(t))return;
 if(t.hasAttribute('data-nb-box')){catalogState={...state};state={...state,p_box:t.dataset.nbBox,p_offset:0};load();root.scrollIntoView({block:'start'});}
 else if(t.hasAttribute('data-nb-back')){state=catalogState||defaultState();catalogState=null;load();}
 else if(t.hasAttribute('data-nb-page')&&data&&!busy){const p=Number(t.dataset.nbPage);if(Number.isInteger(p)&&p>=1&&p<=Math.ceil(data.total/24)&&(p-1)*24!==state.p_offset){state.p_offset=(p-1)*24;load();root.scrollIntoView({block:'start'});}}
 else if(t.hasAttribute('data-nb-clear')){state.p_busca='';state.p_offset=0;load();}
 else if(t.hasAttribute('data-nb-retry'))load();
}
function submit(e){if(!e.target.matches('[data-nb-search]'))return;e.preventDefault();state.p_busca=e.target.elements.busca.value.trim();state.p_offset=0;load();}
function imageError(e){if(e.target.matches?.('.nb-rated-player img')){const span=document.createElement('span');span.className='nb-no-photo';span.textContent='Sem imagem';e.target.replaceWith(span);}}
let unsubscribe=null;
function degreeChanged(){state.p_offset=0;if(catalogState)catalogState.p_offset=0;load();}
function unmount(){unsubscribe?.();unsubscribe=null;++seq;controller?.abort();if(root){root.removeEventListener('click',click);root.removeEventListener('submit',submit);root.removeEventListener('change',change);root.removeEventListener('error',imageError,true);}root=null;}
window.SiteNovoBoxes=Object.freeze({mount(node,ongoing=false,box=null){unmount();active=ongoing;restoreState();unsubscribe=window.SiteNovoDegrau?.subscribe(degreeChanged);if(typeof box==='string'&&box.trim()&&box.length<=300){catalogState=state.p_box?catalogState:{...state};state={...state,p_box:box,p_busca:'',p_offset:0};}root=node;root.addEventListener('click',click);root.addEventListener('submit',submit);root.addEventListener('change',change);root.addEventListener('error',imageError,true);return load();},unmount});
})();
