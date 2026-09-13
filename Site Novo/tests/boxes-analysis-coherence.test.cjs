const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../boxes.js'),'utf8');
const analysis={linha_id:'123',funcao:'Atacante Driblador',posicao:'PTE',pontuacao:110.63,estrelas:3,etiqueta:'PAGAR'};
const card={card_id:'99',nome:'Jogador',posicao:'SA',foto_url:null,pontuacao_maxima:113.25,analises:[analysis]};
(async()=>{
 for(const active of [false,true])for(const detail of [false,true]){
  const window={SiteNovoBoxesAPI:{read:async()=>({status:'pronto',total:1,total_cards:1,tem_mais:false,regua:[{estrelas:3,rotulo:'PAGAR'}],itens:detail?[card]:[{box:'Teste',total_cards:1,data_rotulo:'',melhor_pontuacao:null,cards:[card]}]})}};
  const root={innerHTML:'',addEventListener(){},removeEventListener(){}};
  require('./common-harness.cjs').run(source,{window});
  await window.SiteNovoBoxes.mount(root,active,detail?'Teste':null);
  assert.ok(root.innerHTML.includes('110,63'));
  assert.ok(!root.innerHTML.includes('113,25'));
  assert.ok(!root.innerHTML.includes('Atacante Driblador')); assert.ok(!root.innerHTML.includes('Especialidade')); assert.ok(root.innerHTML.includes('>SA</span>'));
  assert.ok(root.innerHTML.includes('linha=123'));
  assert.ok(root.innerHTML.includes('Contratação: 3 de 5 estrelas'));
  window.SiteNovoBoxes.unmount();
 }
 console.log('Coerência de função, nota, estrelas e link: quatro modos aprovados.');
})().catch(e=>{console.error(e);process.exitCode=1;});
