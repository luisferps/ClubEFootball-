/* Leitura publica cadastral, independente do legado. */
(() => {
'use strict';
const endpoint='https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/rpc/site_novo_boxes_v1';
const key='sb_publishable_XTKGboY9RyYiirPiIsWMhw_P8B51cHj';
function validate(d,r){
 const fail=()=>{throw new Error('Resposta de Boxes incompatível.');};
 const text=v=>typeof v==='string'&&v.trim().length>0;
 const integer=v=>Number.isSafeInteger(v)&&v>=0;
 if(!d||d.contrato!=='site-novo-boxes-v1'||d.versao!==1||d.modo!==(r.p_box===null?'boxes':'cards')||d.box!==r.p_box||d.busca!==r.p_busca||d.offset!==r.p_offset||d.limite!==r.p_limite||!integer(d.total)||!integer(d.total_cards)||!Array.isArray(d.itens)||d.itens.length!==Math.min(r.p_limite,Math.max(0,d.total-r.p_offset))||d.tem_mais!==(d.total>r.p_offset+r.p_limite)||d.status!==(d.itens.length?'pronto':'vazio'))fail();
 const card=c=>{if(!c||typeof c.card_id!=='string'||!/^[1-9][0-9]*$/.test(c.card_id)||!text(c.nome)||(c.posicao!==null&&typeof c.posicao!=='string')||(c.overall!==null&&!integer(c.overall))||(c.foto_url!==null&&typeof c.foto_url!=='string'))fail();};
 const seen=new Set();
 d.itens.forEach(i=>{
 const id=d.modo==='boxes'?i.box:i.card_id;if(seen.has(id))fail();seen.add(id);
 if(d.modo==='cards')card(i);
 else {if(!text(i.box)||!integer(i.total_cards)||i.total_cards<1||!Array.isArray(i.cards)||i.cards.length!==Math.min(3,i.total_cards))fail();i.cards.forEach(card);if(new Set(i.cards.map(c=>c.card_id)).size!==i.cards.length)fail();}
 });
 if(!Array.isArray(d.regua)||!d.regua.length||d.regua.some(f=>!f.codigo||!f.rotulo||!integer(f.estrelas)||f.estrelas>5||'percentual_minimo' in f))fail();
 const cards=d.modo==='cards'?d.itens:d.itens.flatMap(b=>b.cards);
 for(const c of cards)if(c.pontuacao_maxima!==null&&(typeof c.pontuacao_maxima!=='number'||!Number.isFinite(c.pontuacao_maxima)))fail();
 for(const c of cards)if(!Array.isArray(c.analises)||c.analises.some(a=>(a.linha_id!==null&&(typeof a.linha_id!=='string'||!/^\d+$/.test(a.linha_id)))||'percentual_topo' in a||typeof a.pontuacao!=='number'||!Number.isFinite(a.pontuacao)||!a.funcao||!a.etiqueta||!a.codigo||!integer(a.estrelas)||a.estrelas>5||!a.regua_versao))fail();
 return d;
}
async function read(r,signal,active=false){
 const request={...r};if(active)delete request.p_ordem;else request.p_ordem=r.p_ordem||'recentes';
 const url=active?endpoint.replace('site_novo_boxes_v1','site_novo_boxes_em_andamento_v1'):endpoint;
 let res;
 for(let attempt=0;attempt<2;attempt++){
  if(signal)signal.throwIfAborted();
  try{
   res=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json',apikey:key},body:JSON.stringify(request),signal,cache:'no-store'});
   if(attempt||![408,500,502,503,504].includes(res.status))break;
  }catch(e){if(attempt||signal?.aborted||e.name==='AbortError'||e.name!=='TypeError')throw e;}
  await new Promise(resolve=>setTimeout(resolve,400));
 }
 if(!res.ok)throw new Error('Não foi possível consultar as boxes.');
 const d=validate(await res.json(),r);if(d.degrau!==(r.p_degrau??3))throw new Error('Degrau de Boxes incompatível.');
 if(!active&&d.ordem!==request.p_ordem)throw new Error('Ordenação de boxes incompatível.');
 if(!active&&d.modo==='boxes')for(const b of d.itens)if(typeof b.data_rotulo!=='string'||(b.data_oferta!==null&&!/^\d{4}-\d{2}-\d{2}$/.test(b.data_oferta))||(b.melhor_pontuacao!==null&&(typeof b.melhor_pontuacao!=='number'||!Number.isFinite(b.melhor_pontuacao))))throw new Error('Dados de organização das boxes incompatíveis.');
 return d;
}
window.SiteNovoBoxesAPI=Object.freeze({read,validate});
})();
