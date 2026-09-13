/* Transporte e utilidades compartilhados. Sem fórmulas de cálculo. */
(() => {
 'use strict';
 const base = 'https://trqqpsnafpbudtvvicch.supabase.co';
 const key = 'sb_publishable_XTKGboY9RyYiirPiIsWMhw_P8B51cHj';
 const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const photo = value => { try { const url = new URL(value); return url.protocol === 'https:' ? url.href : null; } catch { return null; } };
 async function request(path, body, options = {}) {
  const controller = new AbortController();
  let expired = false;
  const abort = () => controller.abort();
  if (options.signal?.aborted) abort();
  else options.signal?.addEventListener('abort', abort, {once:true});
  const timer = setTimeout(() => { expired = true; abort(); }, options.timeout ?? 12000);
  try {
   for (let attempt = 0; ; attempt++) {
    try {
     controller.signal.throwIfAborted();
     const headers = {'Content-Type':'application/json',apikey:key};
     if (options.token) headers.Authorization = 'Bearer ' + options.token;
     const response = await fetch(base + path, {method:'POST',headers,body:JSON.stringify(body),signal:controller.signal,cache:'no-store'});
     if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      const error = new Error(options.errorMessage || data.msg || data.message || data.error_description || 'Não foi possível concluir a consulta. Tente novamente.');
      error.status = response.status; error.code = data.code;
      throw error;
     }
     return response.status === 204 ? null : await response.json();
    } catch (error) {
     if (controller.signal.aborted || attempt >= (options.retries ?? 0) || !(error.name === 'TypeError' || [408,500,502,503,504].includes(error.status))) throw error;
     await new Promise(resolve => setTimeout(resolve,300));
    }
   }
  } catch (error) {
   if (expired) { const timeout = new Error('A consulta demorou. Tente novamente.'); timeout.name = 'TimeoutError'; throw timeout; }
   throw error;
  } finally { clearTimeout(timer); options.signal?.removeEventListener('abort',abort); }
 }
 window.SiteNovoCommon = Object.freeze({request,escapeHTML,photo});
 // Apresentação compartilhada: não altera dados, valores de formulário ou nomes salvos.
 if (typeof document !== 'undefined' && typeof MutationObserver !== 'undefined') {
  const minor = new Set(['a','as','o','os','e','de','da','das','do','dos','em','na','nas','no','nos','por','pelo','pelos','pela','pelas','para','com','sem','entre','ao','aos','à','às']);
  const title = value => value.replace(/\p{L}[\p{L}\p{M}]*/gu,(word,offset) => {
   if (word===word.toUpperCase() && word.length>1) return word;
   if (offset>0 && minor.has(word.toLowerCase())) return word.toLowerCase();
   return word[0].toLocaleUpperCase('pt-BR')+word.slice(1);
  });
  const excluded = element => !element || element.closest('script,style,code,pre,textarea,[contenteditable="true"],option:not([value])');
  function format(node) {
   if(node.nodeType===3){if(!excluded(node.parentElement)){const next=title(node.data);if(next!==node.data)node.data=next;}return;}
   if(node.nodeType!==1||excluded(node))return;
   for(const attr of ['title','aria-label','placeholder','alt'])if(node.hasAttribute(attr)){const old=node.getAttribute(attr),next=title(old);if(next!==old)node.setAttribute(attr,next);}
   for(const child of node.childNodes)format(child);
  }
  function start(){
   format(document.body);
   new MutationObserver(records=>{for(const record of records){if(record.type==='childList'){for(const node of record.addedNodes)format(node);}else format(record.target);}})
    .observe(document.body,{subtree:true,childList:true,characterData:true});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 }
})();
