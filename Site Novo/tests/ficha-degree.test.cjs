const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../ficha.js'),'utf8');
const code=source.slice(source.indexOf('  function renderImpulses('),source.indexOf('  function renderAttributes('));
let nodes,selectedDegree;
const ctx={window:{SiteNovoDegrau:{set:n=>selectedDegree=n}},asArray:x=>Array.isArray(x)?x:[],create:(tag,cls,text)=>({tag,cls,text,children:[],appendChild(x){this.children.push(x)},setAttribute(){}}),formatSigned:x=>'+'+x,replaceChildren:(_,n)=>nodes=n};
vm.createContext(ctx);vm.runInContext(code,ctx);
for(const [level,next] of [[3,1],[1,2],[2,3]]){
ctx.renderImpulses([{tipo:'nativo',nome:'Física',condicao_nivel:level,delta_uniforme:3,efeitos:[]}],{card:{card_id:'card'},proximo_degrau:{nivel:next,linha_id:100+next}});
const button=nodes[0].children[0].children[1];assert.equal(button.tag,'button');assert.equal(button.text,'+'+level);button.onclick();assert.equal(selectedDegree,next);
}
ctx.renderImpulses([{tipo:'nativo',condicao_nivel:null,delta_uniforme:5,efeitos:[]}],{});assert.equal(nodes[0].children[0].children[1].tag,'span');
ctx.renderImpulses([{tipo:'nativo',condicao_nivel:3,delta_uniforme:3,efeitos:[]}],{});assert.equal(nodes[0].children[0].children[1].disabled,true);
assert.match(source,/SiteNovoDegrau\.subscribe\(selectConditionalDegree\)/);
assert.match(source,/degraus_condicionais/);
const html=fs.readFileSync(path.join(__dirname,'../ficha.html'),'utf8');
assert.doesNotMatch(html,/Ficha — visão do usuário|id="status-badge"|id="page-subtitle"/);
assert.match(html,/>COMPONENTES DA BUILD</);

const key='sb_publishable_XTKGboY9RyYiirPiIsWMhw_P8B51cHj';
(async()=>{
  const response=await fetch('https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/rpc/site_novo_ficha_v2',{method:'POST',headers:{'Content-Type':'application/json',apikey:key},body:JSON.stringify({p_card_id:'89138556575063',p_linha_id:363917})});
  const envelope=await response.json();assert.ok(response.ok,JSON.stringify(envelope));
  assert.deepEqual(envelope.dados.degraus_condicionais.map(x=>x.nivel),[1,2,3]);
  assert.equal(new Set(envelope.dados.degraus_condicionais.map(x=>String(x.linha_id))).size,3);
  console.log('Ficha: controles sincronizados, mapa público 1/2/3 e ímpetos fixos preservados.');
})().catch(e=>{console.error(e);process.exitCode=1;});
