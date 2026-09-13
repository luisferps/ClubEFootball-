const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(__dirname+'/../ficha.js','utf8');
const piece=(a,b)=>source.slice(source.indexOf(a),source.indexOf(b));
let degree=1, pending=[],shown=[],messages=[],nodes={};
const envelope=n=>({status:'pronto',dados:{card:{card_id:'card'},build:{linha_id:n,impetos:[{condicao_nivel:n}]},degraus_condicionais:[1,2,3].map(n=>({nivel:n,linha_id:n}))}});
const ctx={Number,String,AbortController,window:{SiteNovoDegrau:{get:()=>degree},location:{href:'ficha'},history:{pushState(){},replaceState(){}}},viewState:{requestVersion:0,envelope:envelope(1)},personalState:{version:0,records:[]},CARD_STATUSES:new Set(['pronto','card_sem_build_publicada']),asArray:x=>Array.isArray(x)?x:[],lineIdText:x=>x==null?null:String(x),isPlainObject:x=>!!x,
 byId:id=>nodes[id]||(nodes[id]={hidden:false}),setLoading(){},fetchFicha:(params,signal)=>new Promise((resolve,reject)=>pending.push({params,signal,resolve,reject})),buildUrl:(_,n)=>'ficha?linha='+n,readParams:()=>({p_card_id:'card',p_linha_id:1}),
 renderBuildEnvelope:e=>shown.push(e.dados.build.linha_id),renderEnvelope:e=>{shown.push(e.dados.build&&e.dados.build.linha_id);messages.push(e.mensagem);},renderFailure:e=>messages.push(e.message),renderSwitchFailure:e=>messages.push(e.message),refreshPersonalBuilds(){},revealPopulatedFicha(){nodes['ficha-content'].hidden=false;},preparePhoto:async()=>null,readBuildExpansion:()=>false};
vm.createContext(ctx);
vm.runInContext(piece('  function conditionalDegree(', '  function selectPublishedBuild(')+piece('  function assertSwitchResponse(', '  function renderBuildEnvelope(')+piece('  async function loadFicha(', '  function start()'),ctx);
const tick=()=>new Promise(r=>setImmediate(r));
(async()=>{
 for(const [from,to] of [[1,2],[2,3],[3,1],[1,3],[3,2],[2,1]]){
   ctx.viewState.envelope=envelope(from);degree=to;ctx.selectConditionalDegree();assert.equal(nodes['ficha-content'].hidden,true);
   pending.shift().resolve(envelope(from));await tick();assert.equal(pending[0].params.p_linha_id,to);
   pending.shift().resolve(envelope(to));await tick();assert.equal(shown.at(-1),to);assert.equal(degree,to);
 }
 degree=2;ctx.viewState.envelope=envelope(1);ctx.selectConditionalDegree();const obsolete=pending.shift();
 degree=1;ctx.selectConditionalDegree();pending.shift().resolve(envelope(1));await tick();obsolete.resolve(envelope(2));await tick();assert.equal(shown.at(-1),1);assert.equal(pending.length,0);assert.equal(obsolete.signal.aborted,true);
 degree=2;ctx.selectConditionalDegree();const missing=envelope(1);missing.dados.degraus_condicionais=[];pending.shift().resolve(missing);await tick();assert.equal(nodes['ficha-content'].hidden,false);assert.equal(shown.at(-1),null);assert.equal(messages.at(-1),'Análise Ainda Não Publicada');
 ctx.selectConditionalDegree();pending.shift().reject(new Error('offline'));await tick();assert.equal(nodes['ficha-content'].hidden,true);
 degree=1;const initial=ctx.loadFicha({p_card_id:'card',p_linha_id:3},{mode:'initial'});pending.shift().resolve(envelope(3));await tick();pending.shift().resolve(envelope(1));await initial;assert.equal(shown.at(-1),1);
 const api=fs.readFileSync(__dirname+'/../ficha-editor-api.js','utf8');
 const record={id:'local-1',revisao:1,card_id:'card',entrada:{card_id:'card',condicoes:{2:3}},build:{impetos:[{slot:2,condicao_nivel:3}]}};
 const pctx={window:{SiteNovoDegrau:{get:()=>degree}},localData:()=>({records:[record]}),session:null,refreshedPersonal:new Map(),calculation:async(_,p)=>({nota_final:p.p_entrada.condicoes[2],ficha:{impetos:[{slot:2,condicao_nivel:p.p_entrada.condicoes[2]}]}})};
 vm.createContext(pctx);vm.runInContext(api.slice(api.indexOf('  async function listBuilds('),api.indexOf('  async function removeBuild(')),pctx);
 for(const n of [1,2,3,1]){const result=await pctx.listBuilds('card',n);assert.equal(result[0].resultado.nota_final,n);assert.equal(record.entrada.condicoes[2],3);}
 console.log('OK: seis trocas, resposta atrasada, linha ausente, erro, link divergente e builds pessoais sem alterar o salvo.');
})().catch(e=>{console.error(e);process.exitCode=1;});
