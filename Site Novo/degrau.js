/* Preferência de exibição; a seleção das linhas ocorre no banco. */
(()=>{
'use strict';
const listeners=new Set();
const storageKey='clubefootball.degrau-condicional';
let value=3;
try{const saved=Number(window.localStorage.getItem(storageKey));if([1,2,3].includes(saved))value=saved;}catch{}
function paint(){document.querySelectorAll('[data-sn-degrau]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.snDegrau)===value)));}
function set(next,persist=true,notify=true){if(![1,2,3].includes(next)||next===value)return false;value=next;if(persist)try{window.localStorage.setItem(storageKey,String(value));}catch{}paint();if(notify)listeners.forEach(fn=>fn(value));return true;}
window.SiteNovoDegrau=Object.freeze({get:()=>value,set:next=>set(Number(next)),sync:next=>set(Number(next),true,false),subscribe(fn){listeners.add(fn);return()=>listeners.delete(fn);}});
document.querySelectorAll('[data-sn-degrau]').forEach(b=>b.addEventListener('click',()=>set(Number(b.dataset.snDegrau))));
window.addEventListener('storage',event=>{if(event.key===storageKey)set(Number(event.newValue),false,true);});
paint();
})();
