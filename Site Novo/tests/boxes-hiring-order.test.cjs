const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const window={};require('./common-harness.cjs').run(fs.readFileSync(path.join(__dirname,'../boxes-api.js'),'utf8'),{window,fetch,URL});
const read=(box,degrau,offset=0)=>window.SiteNovoBoxesAPI.read({p_box:box,p_busca:'',p_limite:24,p_offset:offset,p_degrau:degrau},undefined,true);
const rating=c=>c.analises?.[0]?.estrelas??-1;
const score=c=>c.pontuacao_maxima??c.analises?.[0]?.pontuacao??-Infinity;
function ordered(cards){for(let i=1;i<cards.length;i++){const a=cards[i-1],b=cards[i];assert.ok(rating(a)>rating(b)||rating(a)===rating(b)&&score(a)>=score(b),'estrelas e desempate por pontuação: '+a.nome+' / '+b.nome);}}
(async()=>{
 let checked=0;
 for(const degree of [1,2,3]){
  const list=await read(null,degree);
  for(const box of list.itens){
   ordered(box.cards);
   const detail=await read(box.box,degree);ordered(detail.itens);
   assert.deepEqual(box.cards.map(c=>c.card_id),detail.itens.slice(0,3).map(c=>c.card_id),'prévia deve ser o início da box: '+box.box);
   if(detail.tem_mais){const next=await read(box.box,degree,24);ordered(detail.itens.concat(next.itens));}
   checked++;
  }
 }
 console.log(JSON.stringify({ok:true,boxesConferidas:checked,degraus:3,regra:'estrelas desc, pontuação desc; prévia igual ao início do detalhe'}));
})().catch(e=>{console.error(e);process.exitCode=1;});
