const fs=require('fs'),assert=require('node:assert/strict');
const timers=new Map(),requests=[];let id=0,degree=1,listener;
const handlers={};const root={innerHTML:'',contains:()=>true,scrollIntoView(){},addEventListener:(k,f)=>handlers[k]=f,removeEventListener(){}};
const window={navigator:{},sessionStorage:{getItem:()=>null,setItem(){}},SiteNovoDegrau:{get:()=>degree,subscribe:f=>{listener=f;return()=>{};}},SiteNovoBoxesAPI:{read:async(r,signal)=>{requests.push({r,signal});return{status:'vazio',total:100,total_cards:100,itens:[],tem_mais:true,regua:[]};}}};
require('./common-harness.cjs').run(fs.readFileSync(__dirname+'/../boxes.js','utf8'),{window,URL,AbortController,document:{},setTimeout:(f,ms)=>{timers.set(++id,{f,ms});return id;},clearTimeout:i=>timers.delete(i)});
const tick=()=>new Promise(r=>setImmediate(r));
function page(n){handlers.click({target:{closest(){return this;},hasAttribute:k=>k==='data-nb-page',dataset:{nbPage:String(n)}}});}
async function preload(){const timer=[...timers.values()].find(t=>t.ms===1500);assert.ok(timer);await timer.f();}
(async()=>{
 await window.SiteNovoBoxes.mount(root);assert.equal(requests.length,1);
 await preload();assert.equal(requests.length,2);assert.equal(requests[1].r.p_offset,24);
 page(2);await tick();assert.equal(requests.length,2,'próxima página pronta não repete consulta');
 await preload();assert.equal(requests[2].r.p_offset,48);
 degree=2;listener();await tick();assert.equal(requests.at(-1).r.p_degrau,2);assert.equal(requests.at(-1).r.p_offset,0);
 page(2);await tick();assert.equal(requests.at(-1).r.p_degrau,2);assert.equal(requests.at(-1).r.p_offset,24);
 window.SiteNovoBoxes.unmount();assert.equal([...timers.values()].filter(t=>t.ms===1500).length,0);
 console.log('OK: uma página antecipada, reuso sem chamada duplicada, separação por grau e cancelamento ao sair.');
})().catch(e=>{console.error(e);process.exitCode=1;});
