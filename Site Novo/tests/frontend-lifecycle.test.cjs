const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const {run,homeNode}=require('./common-harness.cjs');
const source=name=>fs.readFileSync(path.join(__dirname,'..',name),'utf8');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 let resolveBoxes;const window={SiteNovoRankingAPI:{read:()=>Promise.resolve({total:23,itens:[]})},SiteNovoBoxesAPI:{read:()=>new Promise(r=>resolveBoxes=r)}};
 run(source('home.js'),{window});const node=homeNode(),loaded=window.SiteNovoHome.mount(node);await tick();
 assert.match(node.innerHTML,/Nenhuma build publicada ainda/,'ranking painted before boxes returns');
 resolveBoxes({itens:[]});await loaded;window.SiteNovoHome.unmount();

 const events={},input={value:'Messi',setAttribute(){},blur(){}},popup={hidden:true};
 const header={elements:{busca:input},querySelector:()=>popup,addEventListener:(n,fn)=>events[n]=fn,contains:()=>false};
 let resolveSearch,scheduled;const searchWindow={SiteNovoSearchAPI:{read:()=>new Promise(r=>resolveSearch=r)}};
 run(source('search.js'),{window:searchWindow,document:{querySelector:()=>header,addEventListener(){},activeElement:null},setTimeout:fn=>(scheduled=fn,1),clearTimeout(){}});
 events.input();const pending=scheduled();events.keydown({key:'Escape'});resolveSearch({itens:[],total:0});await pending;
 assert.equal(popup.hidden,true,'stale response cannot reopen dismissed suggestions');
 events.input();const second=scheduled();events.input();resolveSearch({itens:[],total:0});await second;
 assert.equal(popup.hidden,true,'typing invalidates previous generation before debounce');

 const twin=source('ficha-editor.js').match(/async function replaceTwin\(from,to\)\{[\s\S]*?\n  \}/)[0];
 const queue=[];const context={session:{serial:0,input:{choice:'old'},result:{},saving:false},api:{twin:()=>new Promise(r=>queue.push(r))},clone:structuredClone,AbortController,clearTimeout,id:()=>({}),status(){},renderSkills(){},applyResult(){},errorText:e=>e.message};
 vm.runInNewContext(twin,context);const first=context.replaceTwin(1,2),last=context.replaceTwin(1,3);
 queue[0]({entrada:{choice:'first'},resultado:{}});await first;queue[1]({entrada:{choice:'last'},resultado:{}});await last;
 assert.equal(context.session.input.choice,'last','latest twin selection wins');

 let calls=0;const transportWindow={};run(source('site-common.js'),{window:transportWindow,fetch:async()=>{calls++;return {ok:false,status:503,json:async()=>({})}}});
 await assert.rejects(transportWindow.SiteNovoCommon.request('/test',{},{}));assert.equal(calls,1,'writes never retry automatically');
 const ctrl=new AbortController();ctrl.abort();await assert.rejects(transportWindow.SiteNovoCommon.request('/test',{}, {signal:ctrl.signal}));assert.equal(calls,1,'pre-aborted request never reaches network');
 const timeoutWindow={};run(source('site-common.js'),{window:timeoutWindow,fetch:(_url,{signal})=>new Promise((_resolve,reject)=>signal.addEventListener('abort',()=>reject(Object.assign(new Error(),{name:'AbortError'}))))});
 await assert.rejects(timeoutWindow.SiteNovoCommon.request('/test',{}, {timeout:5}),{name:'TimeoutError'});
 console.log('OK: independent home, stale search, latest twin, safe retries, cancellation and timeout');
})().catch(error=>{console.error(error);process.exitCode=1});
