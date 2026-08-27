/* ============================================================
   COLETOR efHUB — level cap e o resto da ficha
   Cole ESTE bloco no Console (F12) de uma aba aberta em efhub.com

   POR QUE ELE NAO PERDE NADA:
     - grava CADA ficha no IndexedDB na hora que chega
     - se voce fechar o navegador, cair a energia ou o PC desligar,
       na proxima vez ele CONTINUA de onde parou
     - nada fica so na memoria esperando o fim
   ============================================================ */
(async () => {
  const DB='efhub_coleta', LOJA='fichas';
  let LOTE=1, PAUSA=600;   // devagar de proposito. Ele acelera/desacelera sozinho.

  // ---- IndexedDB: a memoria que sobrevive a queda ----
  // Blindado: se o banco estiver corrompido ou de uma versao velha, ele
  // apaga e refaz. Se o navegador nao deixar usar IndexedDB de jeito nenhum,
  // cai para localStorage e AVISA — nao morre em silencio.
  function abrirIDB(){
    return new Promise((ok,err)=>{
      let r;
      try{ r=indexedDB.open(DB,2); }catch(e){ return err(e); }
      r.onupgradeneeded=e=>{ const d=e.target.result;
        if(!d.objectStoreNames.contains(LOJA)) d.createObjectStore(LOJA);
        if(!d.objectStoreNames.contains('meta'))  d.createObjectStore('meta'); };
      r.onsuccess=e=>{
        const d=e.target.result;
        if(!d.objectStoreNames.contains(LOJA)||!d.objectStoreNames.contains('meta')){
          d.close(); return err(new Error('lojas faltando'));
        }
        d.onversionchange=()=>d.close();
        ok(d);
      };
      r.onerror=()=>err(r.error||new Error('open falhou'));
      r.onblocked=()=>err(new Error('banco travado por outra aba'));
    });
  }

  let db=null, MODO='idb';
  try{ db=await abrirIDB(); }
  catch(e1){
    console.log('%cIndexedDB reclamou: '+(e1&&e1.message||e1)+' — vou refazer o banco',
                'background:#e0a53a;color:#000;padding:2px 8px');
    try{
      await new Promise(ok=>{ const d=indexedDB.deleteDatabase(DB);
        d.onsuccess=ok; d.onerror=ok; d.onblocked=ok; setTimeout(ok,3000); });
      db=await abrirIDB();
      console.log('   banco refeito. (o que tinha antes foi perdido, daqui pra frente guarda)');
    }catch(e2){
      MODO='ls';
      console.log('%cIndexedDB indisponivel neste navegador ('+(e2&&e2.message||e2)+')',
                  'background:#e0a53a;color:#000;padding:2px 8px');
      console.log('   Vou usar o localStorage. Funciona igual, so guarda menos.');
      console.log('   Se o Chrome estiver em aba anonima, feche e abra normal — anonima apaga tudo.');
    }
  }

  // ---- as duas memorias, com a mesma cara ----
  let por, pega, chaves, tudo, limpar;
  if(MODO==='idb'){
    const tx=(loja,modo)=>db.transaction(loja,modo).objectStore(loja);
    por    =(loja,k,v)=>new Promise((ok,err)=>{const r=tx(loja,'readwrite').put(v,k);r.onsuccess=()=>ok();r.onerror=()=>err(r.error);});
    pega   =(loja,k)=>new Promise(ok=>{const r=tx(loja,'readonly').get(k);r.onsuccess=()=>ok(r.result);r.onerror=()=>ok(undefined);});
    chaves =(loja)=>new Promise(ok=>{const r=tx(loja,'readonly').getAllKeys();r.onsuccess=()=>ok(r.result||[]);r.onerror=()=>ok([]);});
    tudo   =(loja)=>new Promise(ok=>{const r=tx(loja,'readonly').getAll();r.onsuccess=()=>ok(r.result||[]);r.onerror=()=>ok([]);});
    limpar =()=>new Promise(ok=>{const r=db.transaction([LOJA,'meta'],'readwrite');
              r.objectStore(LOJA).clear(); r.objectStore('meta').clear(); r.oncomplete=ok; r.onerror=ok;});
  } else {
    const pfx=l=>'efhub_'+l+'_';
    por    =async(l,k,v)=>{ try{ localStorage.setItem(pfx(l)+k, JSON.stringify(v)); }catch(e){
              console.log('%cLOCALSTORAGE CHEIO — baixe o CSV agora com efhubBaixar()','background:#e0524a;color:#fff;padding:3px 8px'); throw e; } };
    pega   =async(l,k)=>{ const v=localStorage.getItem(pfx(l)+k); return v==null?undefined:JSON.parse(v); };
    chaves =async(l)=>Object.keys(localStorage).filter(x=>x.startsWith(pfx(l))).map(x=>x.slice(pfx(l).length));
    tudo   =async(l)=>(await chaves(l)).map(k=>JSON.parse(localStorage.getItem(pfx(l)+k)));
    limpar =async()=>{ for(const x of Object.keys(localStorage)) if(x.startsWith('efhub_')) localStorage.removeItem(x); };
  }

  // ---- a lista de ids ----
  let IDS = await pega('meta','ids');
  if(!IDS){
    if(!window.IDS_PARA_COLETAR){
      console.log('%cFALTA A LISTA','background:#e0524a;color:#fff;padding:3px 8px;font-weight:700');
      console.log('Cole o arquivo ids-para-coletar.js ANTES deste bloco.');
      return;
    }
    IDS = window.IDS_PARA_COLETAR.map(String);
    await por('meta','ids',IDS);
  }

  const feitas = new Set((await chaves(LOJA)).map(String));
  const faltam = IDS.filter(id=>!feitas.has(id));

  console.log('%cCOLETOR efHUB','background:#22c58b;color:#000;font-weight:700;padding:3px 10px');
  console.log('  na lista .......... '+IDS.length);
  console.log('  ja coletadas ...... '+feitas.size+'   (guardadas no navegador)');
  console.log('  faltam ............ '+faltam.length);
  if(!faltam.length){ console.log('%cJA ACABOU. Rode  efhubBaixar()  para pegar o CSV.','background:#22c58b;color:#000;padding:3px 8px'); }

  let feito=0, e429=0, seguidas=0, t0=Date.now(), parar=false;
  let freio=0;                       // ate quando TODO MUNDO fica parado (timestamp)
  window.efhubParar = ()=>{ parar=true; console.log('parando... (o que ja veio esta salvo)'); };

  const dorme=ms=>new Promise(r=>setTimeout(r,ms));
  const fila=[...faltam];
  const total0=fila.length;

  // ---- o freio comum: um 429 segura TODOS, nao so quem tomou ----
  async function esperarFreio(){
    while(Date.now()<freio && !parar) await dorme(250);
  }
  function bater429(retryAfter){
    e429++; seguidas++;
    // respeita o Retry-After se o site mandar; senao sobe sozinho
    const mandado = retryAfter ? Number(retryAfter)*1000 : 0;
    const meu = Math.min(3000*Math.pow(1.7,Math.min(seguidas,8)), 120000);
    const ate = Date.now() + Math.max(mandado, meu);
    if(ate>freio) freio=ate;
    // e deixa o ritmo normal mais lento pra nao bater de novo
    if(seguidas>=3 && PAUSA<4000){ PAUSA=Math.round(PAUSA*1.5); console.log('   ritmo mais lento: '+PAUSA+'ms entre cartas'); }
  }
  function deuCerto(){
    seguidas=0;
    if(PAUSA>600 && feito%200===0){ PAUSA=Math.max(600,Math.round(PAUSA*0.85)); }
  }

  const trabalhador = async () => {
    while(fila.length && !parar){
      await esperarFreio();
      if(parar) break;
      const id=fila.shift();
      try{
        const r=await fetch('/api/public/players/'+id,{credentials:'include'});
        if(r.status===429){
          bater429(r.headers.get('retry-after'));
          fila.push(id);                       // <<< VOLTA PRA FILA. Nao perde.
          const s=Math.ceil((freio-Date.now())/1000);
          if(seguidas===1||seguidas%5===0) console.log('   429 — esperando '+s+'s (a carta voltou pra fila)');
          continue;
        }
        if(r.ok){
          const j=await r.json();
          await por(LOJA,id,(j&&j.player)?j.player:j);
          deuCerto();
        } else if(r.status===404){
          await por(LOJA,id,{__erro:'HTTP404'});   // nao existe: registra e nao volta
        } else {
          fila.push(id); await dorme(2000);        // qualquer outro erro: tenta de novo depois
        }
      }catch(e){
        fila.push(id); await dorme(3000);          // rede caiu: volta pra fila
      }
      feito++;
      if(feito%25===0){
        const seg=(Date.now()-t0)/1000, resta=seg/feito*fila.length;
        await por('meta','ultimo',{feito,quando:new Date().toISOString()});
        console.log('   '+feito+' feitas · faltam '+fila.length+' · 429: '+e429+
                    ' · ritmo '+PAUSA+'ms · ~'+Math.ceil(resta/60)+' min');
      }
      await dorme(PAUSA);
    }
  };
  await Promise.all(Array.from({length:LOTE},trabalhador));

  const total=(await chaves(LOJA)).length;
  console.log('%cPAROU — '+total+' de '+IDS.length+' guardadas','background:#22c58b;color:#000;font-weight:700;padding:3px 10px');
  console.log('  efhubBaixar()   → baixa o CSV do que ja tem');
  console.log('  efhubRitmo(ms)  → forca o ritmo (ex: efhubRitmo(2000) = 2s entre cartas)');
  console.log('  efhubParar()    → interrompe (nao perde nada)');
  console.log('  cole o bloco de novo   → continua de onde parou');

  // ---- exportar ----
  window.efhubBaixar = async () => {
    const ks=await chaves(LOJA), vs=await tudo(LOJA);
    const linhas=['card_id,level_cap,orcamento,ovr,max_ovr,tier,votos'];
    let com=0;
    for(let i=0;i<ks.length;i++){
      const id=String(ks[i]), f=vs[i]||{};
      if(f.__erro) continue;
      const lc = f.levelCap ?? f.level_cap ?? f.maxLevel ?? '';
      if(lc!=='') com++;
      const orc = lc!=='' ? (2*Number(lc)-2) : '';
      linhas.push([id,lc,orc,f.overallRating??f.ovr??'',f.maxOverallRating??f.max_ovr??'',f.tier??'',f.votes??f.votos??''].join(','));
    }
    const b=new Blob(['﻿'+linhas.join('\n')],{type:'text/csv'});
    const a=document.createElement('a'); a.href=URL.createObjectURL(b);
    a.download='efhub-levelcap.csv'; a.click();
    console.log('CSV baixado: '+(linhas.length-1)+' linhas · '+com+' com level cap');
  };

  window.efhubRitmo = (ms)=>{ PAUSA=Math.max(200,Number(ms)||600); console.log('ritmo: '+PAUSA+'ms'); };

  window.efhubZerar = async () => {
    if(!confirm('Isso APAGA tudo que ja foi coletado. Confirma?')) return;
    await limpar();
    console.log('zerado.');
  };
})().catch(e=>{
  console.log('%cPAROU COM ERRO','background:#e0524a;color:#fff;font-weight:700;padding:3px 10px');
  console.log(e && (e.message||e));
  console.log('Nada do que ja foi coletado se perdeu. Cole o bloco de novo para continuar.');
});