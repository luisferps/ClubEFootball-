const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const window={};vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../boxes-api.js'),'utf8'),{window,fetch,URL,Number,Set,setTimeout});
const request={p_box:null,p_busca:'',p_limite:24,p_offset:0};
const read=(changes,active)=>window.SiteNovoBoxesAPI.read({...request,...changes},undefined,active);
(async()=>{
 const living=await read({p_box:'Living Legends 2026'},false);
 const france=await read({p_box:'Big Time & Epic: France 1998',p_limite:60},false);assert.equal(france.total,3,'detalhe recebe somente o trio comercial confirmado');
 assert.deepEqual(france.itens.map(c=>c.nome).sort(),['Lilian Thuram','Marcel Desailly','Patrick Vieira']);
 const desailly=await read({p_busca:'Desailly',p_limite:60},false);assert.ok(desailly.itens.some(b=>b.box==='Big Time & Epic: France 1998'),'jogador encontra a relacao comercial oficial');
 const typo=await read({p_busca:'desaily',p_limite:60},false);assert.deepEqual(typo.itens.map(b=>b.box),desailly.itens.map(b=>b.box),'erro curto de digitacao preserva o resultado');
 for(const name of ['Neymar','Cristiano','Haaland','Mbappe']){const results=await read({p_busca:name,p_limite:60},false);assert.ok(results.total>0,name+' encontra boxes');console.log(name+': '+results.total+' boxes');}
 const plain=await read({p_busca:'Mbappe',p_limite:60},false),accented=await read({p_busca:'Mbappé',p_limite:60},false);assert.deepEqual(plain.itens.map(b=>b.box),accented.itens.map(b=>b.box),'acentos nao alteram resultados');
 const czech=await read({p_busca:'Cech'},true),czechAccent=await read({p_busca:'Čech'},true);assert.ok(czech.total>0);assert.deepEqual(czech.itens.map(b=>b.box),czechAccent.itens.map(b=>b.box));
 const found=await read({p_busca:'  mEsSi  ',p_limite:60},false);
 const box=found.itens.find(b=>b.box==='Living Legends 2026');assert.ok(box,'jogador encontra box cujo nome nao contem seu nome');assert.equal(box.total_cards,living.total,'contagem inclui todos os cards');
 assert.ok(box.cards[0].nome.toLowerCase().includes('messi'),'jogador pesquisado aparece primeiro na previa');
 const detail=await read({p_busca:'Messi',p_box:box.box},false);assert.equal(detail.total,living.total);assert.ok(detail.itens.some(c=>!c.nome.toLowerCase().includes('messi')),'detalhe mantem os demais jogadores');
 const page1=await read({p_busca:'Messi',p_limite:1},false),page2=await read({p_busca:'Messi',p_limite:1,p_offset:1},false);assert.equal(page1.total,page2.total);assert.notEqual(page1.itens[0].box,page2.itens[0].box);
 const active=await read({},true);const chosen=active.itens.find(b=>b.total_cards>3&&b.total_cards<=24);assert.ok(chosen);const full=await read({p_box:chosen.box},true);const outside=full.itens.find(c=>!chosen.cards.some(p=>p.card_id===c.card_id));assert.ok(outside);const player=outside.nome;
 const current=await read({p_busca:player},true);assert.ok(current.itens.some(b=>b.box===chosen.box&&b.total_cards===chosen.total_cards),'busca de jogador funciona nas ofertas atuais');
 assert.equal(current.itens.find(b=>b.box===chosen.box).cards[0].nome,player,'jogador fora da previa original passa a aparecer primeiro');
 const byBox=await read({p_busca:chosen.box},true);assert.deepEqual(byBox.itens.find(b=>b.box===chosen.box).cards.map(c=>c.card_id),chosen.cards.map(c=>c.card_id),'busca so pelo nome da box preserva ordem usual');
 for(const mode of [false,true]){const empty=await read({p_busca:'__jogador_inexistente_894312__'},mode);assert.equal(empty.total,0);const literal=await read({p_busca:'%'},mode);assert.equal(literal.total,0,'percentual nao vira curinga');}
 console.log(JSON.stringify({ok:true,boxesComMessi:found.total,exemploAtual:player,checks:'busca por jogador, caixa e espacos, total integral, detalhe, paginacao, andamento, vazio e curinga literal'}));
})().catch(e=>{console.error(e);process.exitCode=1;});
