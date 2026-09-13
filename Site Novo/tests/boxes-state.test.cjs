const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../boxes.js'),'utf8');
const css=fs.readFileSync(path.join(__dirname,'../boxes.css'),'utf8');
assert.match(css,/--nb-card:#0f1512/);assert.match(css,/\.nb-box\{[^}]*border:1px solid var\(--nb-card-border\)[^}]*background:var\(--nb-card\)/);
const storage=new Map(),prefix='site-novo:boxes:navegacao:v1:';
function app(blocked=false){
 const handlers=new Map(),requests=[];
 const window={sessionStorage:{getItem:k=>{if(blocked)throw Error('blocked');return storage.get(k)||null;},setItem:(k,v)=>{if(blocked)throw Error('blocked');storage.set(k,v);}},SiteNovoBoxesAPI:{read:async(r,s,active)=>{requests.push({...r,active});return {status:'vazio',total:120,total_cards:120,itens:[],tem_mais:true,regua:[]};}}};
 const root={innerHTML:'',contains:()=>true,scrollIntoView(){},addEventListener:(k,f)=>handlers.set(k,f),removeEventListener:k=>handlers.delete(k)};
 vm.runInNewContext(source,{window,URL,AbortController,setTimeout,clearTimeout,document:{}});
 return {mount:(active,box)=>window.SiteNovoBoxes.mount(root,active,box),request:()=>requests.at(-1),click(attr,value=''){const key=attr.replace(/^data-/,'').replace(/-([a-z])/g,(_,c)=>c.toUpperCase());const t={dataset:{[key]:value},closest(){return this;},hasAttribute:k=>k===attr};handlers.get('click')({target:t});},search(value){handlers.get('submit')({preventDefault(){},target:{matches:()=>true,elements:{busca:{value}}}});},sort(value){handlers.get('change')({target:{matches:()=>true,value}});}};
}
const tick=()=>new Promise(r=>setImmediate(r));
(async()=>{
 const a=app();await a.mount(false);a.search('Legends');await tick();a.sort('pontuacao');await tick();a.click('data-nb-page','3');await tick();
 await a.mount(true);assert.equal(a.request().p_busca,'');a.search('POTW');await tick();a.click('data-nb-page','2');await tick();
 await a.mount(false);assert.equal(a.request().p_busca,'Legends');assert.equal(a.request().p_ordem,'pontuacao');assert.equal(a.request().p_offset,48);
 a.click('data-nb-box','Living Legends 2026');await tick();await a.mount(true);assert.equal(a.request().p_busca,'POTW');assert.equal(a.request().p_offset,24);
 const fresh=app();await fresh.mount(false);assert.equal(fresh.request().p_box,'Living Legends 2026');fresh.click('data-nb-back');await tick();assert.equal(fresh.request().p_offset,48);assert.equal(fresh.request().p_busca,'Legends');assert.equal(fresh.request().p_ordem,'pontuacao');
 await fresh.mount(false,'Outra box & teste');assert.equal(fresh.request().p_box,'Outra box & teste');assert.equal(fresh.request().p_busca,'');assert.equal(fresh.request().p_offset,0);fresh.click('data-nb-back');await tick();assert.equal(fresh.request().p_busca,'Legends');
 const bad=JSON.parse(storage.get(prefix+'cadastradas'));bad.state.p_offset=-24;storage.set(prefix+'cadastradas',JSON.stringify(bad));const invalid=app();await invalid.mount(false);assert.equal(invalid.request().p_offset,0);assert.equal(invalid.request().p_busca,'');
 const unavailable=app(true);await unavailable.mount(false);unavailable.search('Messi');await tick();await unavailable.mount(true);await unavailable.mount(false);assert.equal(unavailable.request().p_busca,'Messi');
 console.log('OK: estados independentes, busca, ordenacao, paginacao, detalhe e retorno, recarga, estado invalido e armazenamento bloqueado.');
})().catch(e=>{console.error(e);process.exitCode=1;});
