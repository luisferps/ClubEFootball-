/* Preferencia compartilhada entre o shell e a Ficha. */
(()=>{
'use strict';
const storageKey='clubefootball.tema';
const button=document.getElementById('sn-theme');
if(!button)return;
let theme='escuro';
try{if(window.localStorage.getItem(storageKey)==='claro')theme='claro';}catch{}
function paint(){
 document.documentElement.dataset.theme=theme;
 const light=theme==='claro';
 button.textContent=light?'☾ Escuro':'☀ Claro';
 button.setAttribute('aria-label',light?'Ativar tema escuro':'Ativar tema claro');
}
function set(next,persist=true){
 if(next!=='claro'&&next!=='escuro')return;
 theme=next;
 if(persist)try{window.localStorage.setItem(storageKey,theme);}catch{}
 paint();
}
button.addEventListener('click',()=>set(theme==='claro'?'escuro':'claro'));
window.addEventListener('storage',event=>{if(event.key===storageKey)set(event.newValue,false);});
paint();
})();
