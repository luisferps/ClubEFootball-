const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict');
const base=path.resolve(__dirname,'..'),storage=new Map();
function boot(){const buttons=[1,2,3].map(n=>({dataset:{snDegrau:String(n)},setAttribute(k,v){this[k]=v;},addEventListener(k,fn){this[k]=fn;}}));const handlers={};const window={localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)},addEventListener:(k,fn)=>handlers[k]=fn};vm.runInNewContext(fs.readFileSync(path.join(base,'degrau.js'),'utf8'),{window,document:{querySelectorAll:()=>buttons}});return {window,buttons,handlers};}
const first=boot();assert.equal(first.window.SiteNovoDegrau.get(),3);const events=[];const stop=first.window.SiteNovoDegrau.subscribe(n=>events.push(n));
first.window.SiteNovoDegrau.set(2);first.window.SiteNovoDegrau.set(2);assert.deepEqual(events,[2]);assert.equal(first.buttons[1]['aria-pressed'],'true');
first.window.SiteNovoDegrau.sync(1);assert.deepEqual(events,[2]);assert.equal(first.window.SiteNovoDegrau.get(),1);assert.equal(storage.get('clubefootball.degrau-condicional'),'1');
first.buttons[2].click();assert.deepEqual(events,[2,3]);stop();first.buttons[0].click();assert.deepEqual(events,[2,3]);assert.equal(first.window.SiteNovoDegrau.get(),1);assert.equal(boot().window.SiteNovoDegrau.get(),1);
const fichaHtml=fs.readFileSync(path.join(base,'ficha.html'),'utf8');assert.match(fichaHtml,/src="degrau\.js\?[^" ]+"/);assert.match(fichaHtml,/class="sn-header"/);
const key='sb_publishable_XTKGboY9RyYiirPiIsWMhw_P8B51cHj';
async function rpc(name,body){const r=await fetch('https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/rpc/'+name,{method:'POST',headers:{'Content-Type':'application/json',apikey:key},body:JSON.stringify(body)});const d=await r.json();assert.ok(r.ok,JSON.stringify(d));return d;}
(async()=>{
 const samples=[];
 for(const degree of [1,2,3]){
  const d=await rpc('site_novo_ranking_v1',{p_modo:'mix',p_busca:'Messi',p_limite:60,p_degrau:degree});assert.equal(d.degrau,degree);const keys=d.itens.map(c=>c.card_id+':'+c.funcao_id);assert.equal(new Set(keys).size,keys.length,'um bloco por card e build');const item=d.itens.find(c=>c.card_id==='89138556575063'&&c.funcao.toLowerCase()==='falso nove');assert.ok(item);assert.match(item.posicao,/SA/);assert.match(item.posicao,/CA/);samples.push(item);
  for(const name of ['site_novo_boxes_v1','site_novo_boxes_em_andamento_v1']){const b=await rpc(name,{p_box:null,p_busca:'',p_limite:1,p_degrau:degree});assert.equal(b.degrau,degree);assert.ok(b.itens.length);}
 }
 assert.equal(new Set(samples.map(x=>x.linha_id)).size,3,'cada degrau seleciona sua linha');assert.ok(samples[0].nota_final<samples[1].nota_final&&samples[1].nota_final<samples[2].nota_final);
 console.log(JSON.stringify({ok:true,linhas:samples.map(c=>({id:c.linha_id,nota:c.nota_final,posicoes:c.posicao})),checks:'padrao 3 sem preferencia, escolha persistente entre paginas, 3 RPCs nos 3 degraus, Mix agrupado e linhas distintas'}));
})().catch(e=>{console.error(e);process.exitCode=1;});
