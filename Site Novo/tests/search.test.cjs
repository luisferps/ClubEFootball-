const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const base=path.resolve(__dirname,'..'),window={};
vm.runInNewContext(fs.readFileSync(path.join(base,'search-api.js'),'utf8'),{window,fetch,URL,Number,Set,setTimeout});
const read=(term,limit=8,offset=0,degrau=3)=>window.SiteNovoSearchAPI.read({p_busca:term,p_limite:limit,p_offset:offset,p_degrau:degrau});
(async()=>{
 const names={Messi:'Lionel Messi',Cristiano:'Cristiano Ronaldo',Neymar:'Neymar Jr','Mbappé':'Kylian Mbappé'};
 for(const [term,name] of Object.entries(names)){
  const result=await read(term);assert.ok(result.total>0,term);assert.equal(result.itens[0].nome,name,term+' prioriza o jogador pesquisado');
  assert.ok(result.itens.every(item=>item.posicao===null||!['GK','CB','LB','RB','DMF','CMF','AMF','LMF','RMF','LWF','RWF','SS','CF'].includes(item.posicao)),'posição vem em português');
 }
 const messi=await read('Messi');assert.equal(messi.degrau,3);assert.equal(messi.itens[0].pontuacao_total.toFixed(2),'113.77','cards do mesmo jogador começam pela maior pontuação total');
 assert.ok(messi.itens.every(item=>!('tipo_carta' in item)&&!('posicao_nome' in item)&&!('overall' in item)),'campos antigos de exibição foram removidos do contrato');
 const notas=messi.itens.map(item=>item.pontuacao_total).filter(Number.isFinite);for(let i=1;i<notas.length;i++)assert.ok(notas[i-1]>=notas[i],'pontuações em ordem decrescente');
 for(const nivel of [1,2,3])assert.equal((await read('Messi',8,0,nivel)).degrau,nivel,'o contrato respeita o degrau global');
 const invalidBox=await read('105795245055319');assert.equal(invalidBox.itens[0].box,null,'rótulo cadastral inválido não chega à tela');
 const plain=await read('Alvaro Morata'),accented=await read('Álvaro Morata');
 assert.equal(plain.total,17);assert.equal(accented.total,17);assert.deepEqual(plain.itens.map(i=>i.card_id),accented.itens.map(i=>i.card_id));
 const page=await read('Messi',48,48);assert.equal(page.offset,48);assert.ok(page.itens.length>0);assert.equal(new Set(page.itens.map(i=>i.card_id)).size,page.itens.length);
 const api=fs.readFileSync(path.join(base,'search-api.js'),'utf8'),ui=fs.readFileSync(path.join(base,'search.js'),'utf8');
 assert.doesNotMatch(api+ui,/frontend_busca_v1|frontend_normalizar_texto_v1|1-SISTEMA|clube\.fila|clube\.build/);
 assert.match(ui,/setTimeout\(suggestions, 220\)/);assert.match(ui,/p_limite: 8/);assert.match(ui,/p_limite: 48/);assert.match(ui,/p_degrau: degrau\(\)/);assert.match(ui,/Pontuação total/);
 const css=fs.readFileSync(path.join(base,'site-shell.css'),'utf8');assert.match(css,/object-fit:contain/);assert.doesNotMatch(css,/sn-search-(?:suggestion|card)[^{]*[^}]*object-fit:cover/);
 console.log(JSON.stringify({ok:true,messi:messi.total,morata:plain.total,checks:'jogadores diversos, acentos, siglas portuguesas, ordem por pontuação total, degrau global, arte inteira, box válida, paginação e independência do legado'}));
})().catch(error=>{console.error(error);process.exitCode=1;});
