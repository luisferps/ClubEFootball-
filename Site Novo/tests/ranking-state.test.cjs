const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../ranking.js'),'utf8');
const fixture=JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures/ranking-publico-33-20260906.json'),'utf8'));
async function mount(saved){
 let request,persisted;
 const window={sessionStorage:{getItem:()=>JSON.stringify(saved),setItem:(k,v)=>persisted=JSON.parse(v)},SiteNovoRankingAPI:{read:async r=>{request=r;return {...fixture,modo:r.p_modo,setor:r.p_setor,offset:r.p_offset,limite:r.p_limite};}}};
 const root={innerHTML:'',addEventListener(){},removeEventListener(){}};
 vm.runInNewContext(source,{window,URL,Intl,AbortController,setTimeout,clearTimeout,document:{}});
 await window.SiteNovoRanking.mount(root);window.SiteNovoRanking.unmount();return {request,persisted,html:root.innerHTML};
}
(async()=>{
 const saved={p_modo:'mix',p_setor:'geral',p_busca:'Messi',p_funcao_id:null,p_posicao_nativa_id:1,p_estilo_id:2,p_offset:33,p_limite:30};
 const result=await mount(saved);
 assert.equal(JSON.stringify(result.request),JSON.stringify({...result.request,...saved,p_estilo_id:null}));
 for(const eixo of ['posicao','funcao','estilo']){
  const restored=await mount({...saved,eixo,p_funcao_id:'17',p_setor:'defesa'});
  assert.equal(restored.request.p_setor,'geral');
  assert.equal(restored.request.p_funcao_id,eixo==='funcao'?'17':null);
  assert.equal(restored.request.p_posicao_nativa_id,eixo==='posicao'?1:null);
  assert.equal(restored.request.p_estilo_id,eixo==='estilo'?2:null);
 }
 assert.equal(result.persisted.p_offset,33);assert.match(result.html,/aria-describedby="nr-help-mix"/);assert.match(result.html,/role="tooltip"/);assert.match(result.html,/Uma entrada por card e build/);
 const invalid=await mount({...saved,p_offset:-1});assert.equal(invalid.request.p_offset,0);assert.equal(invalid.request.p_modo,'card');
 console.log('OK: restaura filtros e pagina em nova instancia; descarta estado invalido; ajuda discreta acessivel.');
})().catch(e=>{console.error(e);process.exitCode=1;});
