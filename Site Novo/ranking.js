/* Apresentacao somente: filtros e classificacao sao resolvidos pela RPC. */
(() => {
 'use strict';
 const sectors = [['geral','Geral'],['goleiro','Goleiro'],['defesa','Defesa'],['meio','Meio'],['ataque','Ataque']];
 const modes = [['card','POR CARD'],['jogador','POR JOGADOR'],['mix','MIX']];
 const modeHelp = {card:'A melhor build de cada card.',jogador:'O melhor resultado de cada jogador, entre seus cards.',mix:'Uma entrada por card e build, no degrau selecionado.'};
 const firstPageSize = 33, pageSize = 30;
 const pageCount = total => 1 + Math.ceil(Math.max(0,total-firstPageSize)/pageSize);
 const pageNumber = offset => offset===0 ? 1 : 2+Math.floor((offset-firstPageSize)/pageSize);
 const pageRequest = page => ({p_offset:page===1 ? 0 : firstPageSize+(page-2)*pageSize,p_limite:page===1 ? firstPageSize : pageSize});
 const eixos = [['posicao','POSIÇÃO','Onde o card joga no campo'],['estilo','ESTILO DE JOGO','O comportamento do card'],['funcao','ESPECIALIDADE','O ofício que o card exerce no time']];
 let state = { eixo:'posicao',p_modo:'card',p_setor:'geral',p_funcao_id:null,p_busca:'',p_posicao_nativa_id:null,p_estilo_id:null,...pageRequest(1) };
 const storageKey='site-novo:ranking:filtros:v1';
 try {
  const saved=JSON.parse(window.sessionStorage.getItem(storageKey));
  if(saved&&modes.some(([id])=>id===saved.p_modo)&&(saved.eixo===undefined||eixos.some(([id])=>id===saved.eixo))&&sectors.some(([id])=>id===saved.p_setor)&&typeof saved.p_busca==='string'&&saved.p_busca.length<=100&&(saved.p_funcao_id===null||/^[1-9][0-9]*$/.test(saved.p_funcao_id))&&[saved.p_posicao_nativa_id,saved.p_estilo_id].every(v=>v===null||Number.isSafeInteger(v)&&v>=0)&&Number.isSafeInteger(saved.p_offset)&&saved.p_offset>=0&&saved.p_offset<=100000){
   for(const key of Object.keys(state))if(key in saved)state[key]=saved[key];
   // O setor deixou de ter controle na tela: um valor herdado filtraria sem o leitor ver.
   state.p_setor='geral';
   if(!eixos.some(([id])=>id===state.eixo))state.eixo='posicao';
   if(state.eixo!=='funcao')state.p_funcao_id=null;
   if(state.eixo!=='posicao')state.p_posicao_nativa_id=null;
   if(state.eixo!=='estilo')state.p_estilo_id=null;
   state={...state,...pageRequest(pageNumber(state.p_offset))};
  }
 }catch{}
 let root = null, response = null, catalog = null, busy = false, error = '', sequence = 0, controller = null;
 const esc = window.SiteNovoCommon.escapeHTML;
 const pressed = value => value ? 'true' : 'false';
 const score = new Intl.NumberFormat('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
 const photo = window.SiteNovoCommon.photo;
 function card(item) {
  const podium = item.classificacao <= 3;
  const medal = ({1:'nr-ouro',2:'nr-prata',3:'nr-bronze'})[item.classificacao] || '';
  const url = photo(item.foto_url);
  const picture = url ? `<img class="nr-photo nr-real-photo" src="${esc(url)}" alt="Card de ${esc(item.nome)}" loading="lazy" referrerpolicy="no-referrer">` : '<div class="nr-photo">Sem imagem</div>';
  const showSpecialty = state.eixo !== 'funcao' || state.p_funcao_id === null;
  const showStyle = state.eixo !== 'estilo' || state.p_estilo_id === null;
  const styles = [...new Set((item.estilos || []).map(s=>s.nome))].join(' / ');
  const details = (showSpecialty ? `<span class="nr-detail"><span class="nr-detail-label">Especialidade:</span><strong>${esc(item.funcao)}</strong></span>` : '')
   + (showStyle ? `<span class="nr-detail"><span class="nr-detail-label">Estilo de Jogo:</span><strong>${esc(styles || 'Não informado')}</strong></span>` : '');
  const selo = item.regua_vigente === false ? '<span class="nr-selo-antiga" title="Nota da regua anterior: esta linha ainda nao passou pelo Otimizador novo">Regua antiga</span>' : '';
  const content = `<div class="nr-scoreline"><span class="nr-score">${score.format(item.nota_final)}</span>${selo}</div><h3>${esc(item.nome)}</h3><p class="nr-role">${details}<span class="nr-position">${esc(item.posicao)}</span></p>`;

  return `<a href="ficha.html?card=${encodeURIComponent(item.card_id)}&amp;linha=${encodeURIComponent(item.linha_id)}" aria-label="Abrir Ficha de ${esc(item.nome)}" class="nr-card ${podium?'nr-podium':'nr-compact'} ${medal} nr-live-card"><span class="nr-place">${item.classificacao}º</span>${picture}${podium?`<div class="nr-card-copy">${content}</div>`:content}</a>`;
 }
 function pagination() {
  if (!response || busy || error) return '';
  const current=pageNumber(state.p_offset);
  const count=pageCount(response.total);
  const candidates=new Set([1,count]);
  const start=Math.max(1,Math.min(current-2,count-4));
  for(let p=start;p<=Math.min(count,start+4);p++)candidates.add(p);
  let previous=0;
  const buttons=[...candidates].sort((a,b)=>a-b).map(page=>{
   const gap=previous && page>previous+1 ? '<span class="nr-page-gap" aria-hidden="true">…</span>' : '';
   previous=page;
   return gap+`<button type="button" data-nr-page="${page}" aria-label="Página ${page}" ${page===current?'aria-current="page"':''}>${page}</button>`;
  }).join('');
  return `<div class="nr-pager nr-pager-bottom"><nav class="nr-pagination" aria-label="Páginas do Ranking — rodapé"><button type="button" data-nr-prev ${current===1?'disabled':''}>← Anterior</button><div class="nr-page-numbers">${buttons}</div><button type="button" data-nr-next ${response.tem_mais?'':'disabled'}>Próxima →</button></nav><p class="nr-page-summary">${response.total ? `Página ${current} de ${count} · ${state.p_offset+1}–${state.p_offset+response.itens.length} de ${response.total} resultados` : 'Nenhum resultado'}</p></div>`;
 }
 function markup() {
  const abas = eixos.map(([id,rot]) => `<button type="button" class="nr-axis" data-nr-axis="${id}" aria-pressed="${pressed(state.eixo===id)}">${rot}</button>`).join('');
  let escolha = '';
  if (!catalog) escolha = '<p class="nr-axis-loading">Carregando…</p>';
  else {
   // Ordem visual do campo; nomes e IDs continuam vindos do catalogo.
   const ordemCampo = ['4','5','18','19','6','7','17','16','10','11','12','13','8','9','14','15','3','2','1'];
   const lista = state.eixo === 'posicao' ? (catalog.posicoes||[]) : state.eixo === 'estilo'
    ? [...(catalog.estilos||[])].sort((a,b)=>a.nome.localeCompare(b.nome,'pt-BR'))
    : [...(catalog.funcoes||[])].sort((a,b)=>{
     const ia=ordemCampo.indexOf(String(a.id)),ib=ordemCampo.indexOf(String(b.id));
     return (ia<0?Infinity:ia)-(ib<0?Infinity:ib)||a.nome.localeCompare(b.nome,'pt-BR');
    });
   const atual = state.eixo === 'posicao' ? state.p_posicao_nativa_id : state.eixo === 'estilo' ? state.p_estilo_id : state.p_funcao_id;
   const attr = state.eixo === 'posicao' ? 'data-nr-position-chip' : state.eixo === 'estilo' ? 'data-nr-style-chip' : 'data-nr-function-chip';
   escolha = `<div class="nr-axis-chips nr-axis-chips-${state.eixo}" role="group" aria-label="${state.eixo==='posicao'?'Posições':state.eixo==='estilo'?'Estilos de jogo':'Especialidades'}">`
    + `<button type="button" class="nr-function" ${attr}="" aria-pressed="${pressed(atual===null)}">${state.eixo==='estilo'?'Todos os estilos':'Todas'}</button>`
    + lista.map(v => `<button type="button" class="nr-function" ${attr}="${esc(v.id)}" aria-pressed="${pressed(String(v.id)===String(atual))}">${esc(state.eixo==='posicao'?(v.codigo||v.nome):v.nome)}</button>`).join('')
    + '</div>';
  }
  const chips = modes.map(([id,name]) => `<button type="button" class="nr-function" data-nr-mode="${id}" aria-describedby="nr-help-${id}" aria-pressed="${pressed(state.p_modo===id)}">${name}<span class="nr-mode-help" id="nr-help-${id}" role="tooltip">${modeHelp[id]}</span></button>`).join('');
  let content = '';
  let status = busy ? 'Consultando Ranking…' : error || (response ? `${response.total.toLocaleString('pt-BR')} resultados · notas publicadas` : '');
  if (busy) content = '<div class="nr-message">Carregando os resultados publicados…</div>';
  else if (error) content = '<div class="nr-message"><p>O Ranking está indisponível neste momento.</p><button type="button" data-nr-retry>Tentar novamente</button></div>';
  else if (response?.status==='vazio') content = '<div class="nr-message">Nenhum resultado publicado para esta exibição.</div>';
  else if (response) content = `<div class="nr-results">${response.itens.map(card).join('')}</div>`;
  const classificar = `<div class="nr-classify">`
   + `<div class="nr-axis-tabs" role="group" aria-label="Critério de exibição do Ranking">${abas}</div>${escolha}</div>`;
  return `<section class="nr-ranking" aria-labelledby="nr-title"><h1 id="nr-title" class="nr-sr">Ranking</h1><div class="nr-band"><div class="nr-functions" role="group" aria-label="Modo de leitura">${chips}</div>${classificar}</div><p class="nr-state" role="status">${esc(status)}</p><form class="nr-tools" data-nr-search><input name="busca" type="search" maxlength="100" value="${esc(state.p_busca)}" aria-label="Buscar jogador no Ranking" placeholder="Buscar"><button type="submit" class="nr-filter-button">Buscar</button></form><div aria-busy="${pressed(busy)}">${content}</div>${pagination()}</section>`;
 }
 function paint(focus) { if (!root) return; root.innerHTML = markup(); if (focus) root.querySelector(focus)?.focus(); }
 async function load(focus, reason='consulta') {
  try{window.sessionStorage.setItem(storageKey,JSON.stringify(state));}catch{}
  const ticket = ++sequence;
  controller?.abort(); controller = new AbortController();
  const current = controller;
  const timeout = setTimeout(()=>current.abort(),12000);
  busy = true; error = ''; response = null; paint(focus);
  try {
   const result = await window.SiteNovoRankingAPI.read({...state,p_degrau:window.SiteNovoDegrau?.get()??3},current.signal);
   if (ticket !== sequence || !root) return;
   response = result; catalog = result.catalogo;
  } catch (e) {
   if (ticket !== sequence || !root) return;
   error = e.name==='AbortError' ? 'A consulta demorou mais que o esperado. Tente novamente.' : e.message;
  } finally {
   clearTimeout(timeout);
   if (ticket===sequence && root) {
    busy=false; paint(focus);
    if (response && !error) window.dispatchEvent?.(new CustomEvent('site-novo:ranking-pagina', {detail:{pagina:pageNumber(response.offset),limite:response.limite,total:response.total,modo:response.modo,setor:response.setor,motivo:reason}}));
   }
  }
 }
 function update(patch,focus) { state={...state,...patch,...pageRequest(1)}; return load(focus); }
 function goToPage(page,focus) {state={...state,...pageRequest(page)};load(focus,'pagina');root.scrollIntoView({block:'start'});}
 function click(event) {
  const target = event.target.closest('button'); if (!target || !root?.contains(target)) return;
  if (target.hasAttribute('data-nr-mode') && modes.some(([id])=>id===target.dataset.nrMode)) update({p_modo:target.dataset.nrMode},`[data-nr-mode="${target.dataset.nrMode}"]`);
  // Uma exibicao por vez: trocar de aba limpa a escolha das outras duas.
  else if (target.hasAttribute('data-nr-axis') && eixos.some(([id])=>id===target.dataset.nrAxis)) update({eixo:target.dataset.nrAxis,p_funcao_id:null,p_posicao_nativa_id:null,p_estilo_id:null},`[data-nr-axis="${target.dataset.nrAxis}"]`);
  else if (target.hasAttribute('data-nr-position-chip')) { const v=target.dataset.nrPositionChip; update({p_posicao_nativa_id:v===''?null:Number(v),p_funcao_id:null,p_estilo_id:null},`[data-nr-position-chip="${v}"]`); }
  else if (target.hasAttribute('data-nr-style-chip')) { const v=target.dataset.nrStyleChip; update({p_estilo_id:v===''?null:Number(v),p_funcao_id:null,p_posicao_nativa_id:null},`[data-nr-style-chip="${v}"]`); }
  else if (target.hasAttribute('data-nr-function-chip')) { const v=target.dataset.nrFunctionChip; update({p_funcao_id:v||null,p_posicao_nativa_id:null,p_estilo_id:null},`[data-nr-function-chip="${v}"]`); }
  else if (target.hasAttribute('data-nr-retry')) load();
  else if (target.hasAttribute('data-nr-page') && response && !busy) {
   const page=Number(target.dataset.nrPage),count=pageCount(response.total);
   if(Number.isInteger(page)&&page>=1&&page<=count&&page!==pageNumber(state.p_offset))goToPage(page,`[data-nr-page="${page}"]`);
  }
  else if (target.hasAttribute('data-nr-next') && response?.tem_mais && !busy) goToPage(pageNumber(state.p_offset)+1,'[data-nr-next]');
  else if (target.hasAttribute('data-nr-prev') && state.p_offset>0 && !busy) goToPage(pageNumber(state.p_offset)-1,'[data-nr-prev]');
 }
 function submit(event) { if (!event.target.matches('[data-nr-search]')) return;event.preventDefault();update({p_busca:event.target.elements.busca.value.trim()},'[name="busca"]'); }
 function imageError(event) {if(event.target.matches?.('.nr-real-photo')){const span=document.createElement('div');span.className='nr-photo';span.textContent='Sem imagem';event.target.replaceWith(span);}}
 let unsubscribe=null;
 function degreeChanged(){update({},undefined);}
 function unmount() {unsubscribe?.();unsubscribe=null;++sequence;controller?.abort();if(!root)return;for(const [type,fn] of [['click',click],['submit',submit]])root.removeEventListener(type,fn);root.removeEventListener('error',imageError,true);root=null;}
 window.SiteNovoRanking=Object.freeze({mount(node){unmount();root=node;unsubscribe=window.SiteNovoDegrau?.subscribe(degreeChanged);for(const [type,fn] of [['click',click],['submit',submit]])root.addEventListener(type,fn);root.addEventListener('error',imageError,true);return load();},unmount});
})();
