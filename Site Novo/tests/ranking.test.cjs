const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const base=path.resolve(__dirname,'..');
const fixturePath=process.argv[2] || path.join(__dirname,'fixtures','ranking-publico-33-20260906.json');
assert.ok(fixturePath,'Informe o JSON de readback publico para testar o contrato real');
const rankingSql=fs.readFileSync(path.join(base,'APLICAR-RANKING-LEITURA-OTIMIZADA.sql'),'utf8');
assert.match(rankingSql,/from clube_novo\.build_publicacao_linha_ativa_v1 a/,'Ranking deve ler a fronteira publica finalizada');
assert.doesNotMatch(rankingSql,/join clube_novo\.build_linha_card\b/,'Ranking nao deve reabrir linhas operacionais publicadas');
assert.match(rankingSql,/a\.impeto_condicional_codigo is null or a\.impeto_condicional_nivel=p_degrau/,'degrau deve vir da publicacao ativa');
const live=JSON.parse(fs.readFileSync(fixturePath,'utf8').replace(/^\uFEFF/,''));
const events=[]; const window={dispatchEvent:event=>events.push(event)};
vm.runInNewContext(fs.readFileSync(path.join(base,'ranking-api.js'),'utf8'),{window,fetch,URL,AbortController,Date,Number,Set});
const request={p_modo:'card',p_setor:'geral',p_offset:0,p_limite:33};
assert.equal(window.SiteNovoRankingAPI.validate(live,request),live);
for(const mutate of [d=>d.versao=2,d=>d.itens[0].nota_final=null,d=>d.itens[0].linha_id=123,d=>d.itens[0].publicada_em=null,d=>d.itens[0].classificacao=2,d=>d.itens.push(d.itens[0]),d=>d.total=0]){
 const bad=structuredClone(live);mutate(bad);assert.throws(()=>window.SiteNovoRankingAPI.validate(bad,request));
}
const handlers=new Map(),pending=[];
const root={innerHTML:'',focused:null,contains:()=>true,scrollIntoView(){},querySelector:s=>({focus(){root.focused=s;}}),addEventListener(k,fn){assert.ok(!handlers.has(k),'evento duplicado');handlers.set(k,fn);},removeEventListener(k,fn){if(handlers.get(k)===fn)handlers.delete(k);}};
window.SiteNovoRankingAPI={read:(r,signal)=>new Promise((resolve,reject)=>pending.push({request:r,signal,resolve,reject}))};
vm.runInNewContext(fs.readFileSync(path.join(base,'ranking.js'),'utf8'),{window,URL,Intl,AbortController,setTimeout,clearTimeout,CustomEvent:class {constructor(type,options){this.type=type;this.detail=options.detail;}},document:{createElement:()=>({})}});
function click(attr,value=''){
 const key=attr.replace(/^data-/,'').replace(/-([a-z])/g,(_,c)=>c.toUpperCase());
 const target={dataset:{[key]:value},closest(){return this;},hasAttribute:k=>k===attr};handlers.get('click')({target});
}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 const initial=window.SiteNovoRanking.mount(root);assert.equal(pending.length,1);assert.match(root.innerHTML,/Consultando/);
 assert.equal(pending[0].request.p_limite,33);assert.equal(pending[0].request.p_offset,0);
 pending[0].resolve(live);await initial;
 assert.doesNotMatch(root.innerHTML,/class="nr-box"/,'Ranking nao mostra boxes');
 assert.doesNotMatch(root.innerHTML,/Ver Ficha|<article/,'card inteiro e link sem botao');
 assert.equal((root.innerHTML.match(/aria-label="Abrir Ficha de /g)||[]).length,33);
 assert.equal((root.innerHTML.match(/class="nr-card nr-compact/g)||[]).length,30,'cinco fileiras completas abaixo do podio');
 assert.equal((root.innerHTML.match(/<nav class="nr-pagination"/g)||[]).length,1,'paginacao somente no rodape');
 assert.match(root.innerHTML,/<div class="nr-scoreline"><span class="nr-score">/);
 assert.match(root.innerHTML,/<span class="nr-place">1º<\/span><img/);
 assert.equal((root.innerHTML.match(/class="nr-role"/g)||[]).length,33);
 assert.equal((root.innerHTML.match(/class="nr-position"/g)||[]).length,33);
 assert.match(fs.readFileSync(path.join(base,'ranking.css'),'utf8'),/\.nr-card \.nr-role \{[^}]*flex-direction:column[^}]*align-items:flex-start/);
 assert.match(fs.readFileSync(path.join(base,'ranking.css'),'utf8'),/\.nr-card \.nr-role strong \{[^}]*text-transform:capitalize/);
 assert.equal(events.length,1);assert.equal(events[0].type,'site-novo:ranking-pagina');
 assert.match(root.innerHTML,/data-nr-page="4"/);
 const beforeSame=pending.length;click('data-nr-page','1');assert.equal(pending.length,beforeSame);
 click('data-nr-page','2');assert.equal(pending.at(-1).request.p_offset,33);assert.equal(pending.at(-1).request.p_limite,30);
 const page2=structuredClone(live);page2.offset=33;page2.limite=30;page2.itens=page2.itens.slice(0,30);page2.itens.forEach((item,index)=>item.classificacao=34+index);
 pending.at(-1).resolve(page2);await tick();assert.equal(events.at(-1).detail.pagina,2);assert.equal(events.at(-1).detail.motivo,'pagina');assert.match(root.innerHTML,/Página 2 de/);
 assert.equal((root.innerHTML.match(/class="nr-card nr-podium/g)||[]).length,0);
 click('data-nr-next');assert.equal(pending.at(-1).request.p_offset,63);
 const page3=structuredClone(page2);page3.offset=63;page3.itens.forEach((item,index)=>item.classificacao=64+index);pending.at(-1).resolve(page3);await tick();
 assert.equal(events.at(-1).detail.pagina,3);
 click('data-nr-prev');assert.equal(pending.at(-1).request.p_offset,33);pending.at(-1).resolve(page2);await tick();
 click('data-nr-prev');assert.equal(pending.at(-1).request.p_offset,0);assert.equal(pending.at(-1).request.p_limite,33);pending.at(-1).resolve(live);await tick();
 assert.match(root.innerHTML,new RegExp(live.itens[0].nome));
 assert.match(root.innerHTML,new RegExp('card='+live.itens[0].card_id+'&amp;linha='+live.itens[0].linha_id));
 assert.equal((root.innerHTML.match(/class="nr-card nr-podium/g)||[]).length,3);
 // Limiares: nao criar pagina vazia quando o total termina exatamente em 33 ou 63.
 for(const [total,pages] of [[33,1],[34,2],[63,2],[64,3]]){
  click('data-nr-mode','card');const data=structuredClone(live);data.total=total;data.tem_mais=total>33;
  pending.at(-1).resolve(data);await tick();assert.match(root.innerHTML,new RegExp('Página 1 de '+pages+' ·'));
 }
 click('data-nr-mode','card');pending.at(-1).resolve(live);await tick();
 assert.doesNotMatch(root.innerHTML,/EXIBIR RANKING POR/);
 assert.doesNotMatch(root.innerHTML,/data-nr-filters|Filtros ativos/);
 click('data-nr-position-chip','0');
 assert.equal(pending.at(-1).request.p_posicao_nativa_id,0);
 pending.at(-1).resolve(live);await tick();assert.match(root.innerHTML,/data-nr-position-chip="0" aria-pressed="true"/);
 click('data-nr-axis','estilo');assert.equal(pending.at(-1).request.p_posicao_nativa_id,null);assert.equal(pending.at(-1).request.p_limite,33);
 pending.at(-1).resolve(live);await tick();assert.doesNotMatch(root.innerHTML,/aria-label="Filtros ativos"/);
 click('data-nr-mode','mix');const older=pending.at(-1);assert.equal(older.request.p_modo,'mix');
 click('data-nr-mode','jogador');const newer=pending.at(-1);assert.equal(older.signal.aborted,true);
 const newest=structuredClone(live);newest.itens[0].nome='<img src=x onerror=alert(1)>';newer.resolve(newest);await tick();
 assert.match(root.innerHTML,/&lt;img/);assert.doesNotMatch(root.innerHTML,/<img src=x/);
 const html=root.innerHTML;older.resolve(live);await tick();assert.equal(root.innerHTML,html,'resposta antiga nao pode sobrescrever');
 click('data-nr-axis','funcao');assert.equal(pending.at(-1).request.p_funcao_id,null);assert.equal(pending.at(-1).request.p_setor,'geral');
 const late=pending.at(-1);window.SiteNovoRanking.unmount();assert.equal(handlers.size,0);assert.ok(late.signal.aborted);
 const before=root.innerHTML;late.resolve(live);await tick();assert.equal(root.innerHTML,before);
 const again=window.SiteNovoRanking.mount(root);pending.at(-1).reject(new Error('Falha de teste'));await again;assert.match(root.innerHTML,/Tentar novamente/);assert.doesNotMatch(root.innerHTML,/nr-live-card/);
 window.SiteNovoRanking.unmount();assert.equal(handlers.size,0);
 console.log('OK: contrato real, rejeicoes, cards e links, filtros, cancelamento, resposta fora de ordem, escape HTML e erros sem notas antigas.');
})().catch(e=>{console.error(e);process.exitCode=1;});


