const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const base=path.resolve(__dirname,'..'),window={},sent=[];
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures/ranking-publico-33-20260906.json'),'utf8').replace(/^\uFEFF/,''));
data.degrau=3;
vm.runInNewContext(fs.readFileSync(path.join(base,'ranking-api.js'),'utf8'),{window,URL,Number,Set,fetch:async(url,options)=>{sent.push(JSON.parse(options.body));return {ok:true,json:async()=>data};}});
(async()=>{
 const parameters={p_modo:data.modo,p_setor:data.setor,p_offset:data.offset,p_limite:data.limite,p_funcao_id:null,p_busca:'',p_posicao_nativa_id:null,p_estilo_id:null,p_degrau:3};
 for(const eixo of ['posicao','estilo','funcao']){
  const request={...parameters,eixo};
  await window.SiteNovoRankingAPI.read(request);
  assert.deepEqual(sent.at(-1),parameters);
  assert.equal(request.eixo,eixo);
 }
 console.log('OK: tres eixos visuais nao entram no corpo RPC; parametros publicos preservados.');
})().catch(e=>{console.error(e);process.exitCode=1;});
