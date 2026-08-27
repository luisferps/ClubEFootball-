/* SÓ BAIXA o que já foi coletado. Não coleta nada. Cole no Console do efhub.com */
(async () => {
  const d = await new Promise((ok,err)=>{const r=indexedDB.open('efhub_coleta',2);
    r.onupgradeneeded=e=>{const b=e.target.result;
      if(!b.objectStoreNames.contains('fichas')) b.createObjectStore('fichas');
      if(!b.objectStoreNames.contains('meta'))   b.createObjectStore('meta');};
    r.onsuccess=e=>ok(e.target.result); r.onerror=()=>err(r.error);});
  const st = d.transaction('fichas','readonly').objectStore('fichas');
  const ks = await new Promise(ok=>{const r=st.getAllKeys();r.onsuccess=()=>ok(r.result||[]);r.onerror=()=>ok([]);});
  const st2= d.transaction('fichas','readonly').objectStore('fichas');
  const vs = await new Promise(ok=>{const r=st2.getAll();r.onsuccess=()=>ok(r.result||[]);r.onerror=()=>ok([]);});
  console.log('guardadas no navegador: '+ks.length);
  if(!ks.length){ console.log('%cVAZIO — nada foi coletado ainda nesta máquina','background:#e0524a;color:#fff;padding:3px 8px'); return; }
  const cap=f=>f&&(f.levelCap??f.level_cap??f.maxLevel??f.maxLv??null);
  const L=['card_id,level_cap,orcamento,player_type,ovr,max_ovr,tier,votos']; let com=0;
  for(let i=0;i<ks.length;i++){
    const id=String(ks[i]), f=vs[i]||{}; if(f.__erro) continue;
    const lc=cap(f); if(lc!=null) com++;
    L.push([id, lc??'', lc!=null?(2*Number(lc)-2):'', f.playerType??'',
            f.overallRating??f.ovr??'', f.maxOverallRating??f.max_ovr??'',
            f.tier??'', f.votes??f.votos??''].join(','));
  }
  const b=new Blob(['﻿'+L.join('\n')],{type:'text/csv'});
  const a=document.createElement('a'); a.href=URL.createObjectURL(b);
  a.download='efhub-levelcap.csv'; document.body.appendChild(a); a.click(); a.remove();
  console.log('%c✔ baixado: '+(L.length-1)+' linhas · '+com+' com level cap',
              'background:#22c58b;color:#000;font-weight:700;padding:3px 10px');
  // mostra tambem os campos da primeira ficha, pra eu ver o que o efHub manda
  const pri = vs.find(x=>x&&!x.__erro);
  if(pri) console.log('campos da ficha:', Object.keys(pri).join(', '));
})();
