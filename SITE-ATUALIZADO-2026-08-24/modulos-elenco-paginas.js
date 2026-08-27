/* MODULOS_ELENCO_PAGINAS_V1
   Shell e paginas proprias dos seis modulos internos do Elenco.

   POLITICA GLOBAL DE EXECUCAO — REGRA ORIGINAL, SUPERADA PELA EMENDA ABAIXO:
   - motores principal, de bonus e de otimizacao nunca sao executados pelo
     Codex, Supabase da tarefa, runner remoto ou servico que consuma creditos;
   - resultados reais sao produzidos exclusivamente pelo sistema externo do
     usuario, na maquina dele, e aqui apenas importados/validados;
   - testes no ambiente Codex devem usar somente fixtures sinteticas e mocks,
     sem criar build ou score novo para qualquer card real.
   - enquanto o importador de resultados externos nao estiver conectado, a
     interface falha fechada e nao chama nenhuma equacao existente do produto.

   EMENDA VIGENTE DE TESTE CONTROLADO:
   - quando estritamente necessario para validar um contrato, o Codex pode
     executar um teste real pequeno com no maximo 20 linhas/entradas;
   - a contagem deve ser declarada antes, validada por `controlaTesteReal` e
     registrada no handoff; acima de 20 a execucao falha fechada;
   - lotes, cargas amplas, producao e qualquer processamento acima de 20
     continuam sendo execucao externa pelo usuario, na maquina dele;
   - e proibido fracionar producao em varias execucoes de ate 20 para contornar
     o limite. Contagem ausente ou universo de execucao indeterminado bloqueia
     o teste antes de qualquer chamada de motor;
   - a pagina normal continua consumindo resultados existentes. A permissao
     de teste nao transforma esta interface em runner de motor.
   Referencia: POLITICA-EXECUCAO-EXTERNA-MOTORES-2026-08-24.md.

   CHECKPOINT DE CONVIVENCIA:
   - este arquivo e carregado antes do RouteState e declara somente paginas
     filhas do Elenco pelo contrato `T6_ROUTE_DEFINITIONS`;
   - abrir ou analisar nao altera o Elenco; formacao e tecnico exigem previa,
     confirmacao explicita, validacao e uma unica persistencia canonica;
   - `timeideal` permanece interno e sem rota publica;
   - nao consulta public.cards_completos nem a fonte paralela da Tarefa 4;
   - MODO_ADM, MT_PRO e qualquer flag local nunca autorizam conteudo pago.
*/
(function instalaElencoModulePages(global){
 'use strict';
 if(global.ElencoModulePages) return;

 var ROUTES=Object.freeze({
  melhorfuncao:'melhorfuncao',
  timefraco:'timefraco',
  tecnico:'tecnicotime',
  formacao:'melhorformacao',
  ideal:'timeideal',
  comparar:'comparartime'
 });
 var TITULOS={};
 TITULOS[ROUTES.melhorfuncao]='🎯 MELHOR FUNÇÃO DE CADA UM';
 TITULOS[ROUTES.timefraco]='🔍 ONDE MEU TIME ESTÁ FRACO';
 TITULOS[ROUTES.tecnico]='🎓 TÉCNICO DO TIME INTEIRO';
 TITULOS[ROUTES.formacao]='🧩 MELHOR FORMAÇÃO PRO MEU ELENCO';
 TITULOS[ROUTES.ideal]='⚡ DEIXAR O TIME NO IDEAL';
 TITULOS[ROUTES.comparar]='⚖️ COMPARAR COM OUTRO TIME';

 /* A memoria das paginas pertence ao modulo, nao ao no temporario usado pelo
    renderer. O Symbol mantem a mesma instancia mesmo se o arquivo for
    reinstalado no mesmo documento, sem gravar localStorage/sessionStorage. */
 var MEMORIA=typeof Symbol==='function'&&Symbol.for?Symbol.for('clubefutebol.modulos-elenco-paginas.v1'):'__T6_EMP_MEMORIA_V1__';
 var memoria=global[MEMORIA];
 if(!memoria||!memoria.states){memoria={states:Object.create(null),entradas:Object.create(null)};global[MEMORIA]=memoria;}
 if(!memoria.entradas)memoria.entradas=Object.create(null);
 var runtime={root:null,route:null,states:memoria.states,renders:0,actions:0,lastError:null,lastControlledTest:null,externalUserAction:0,lastExternalUserExecution:null,waitingData:false};
 var indiceCatalogo={lista:null,tamanho:-1,porCard:Object.create(null)};
 var EPS=0.05;

 function proximoCiclo(fn){if(typeof global.setTimeout==='function')return global.setTimeout(fn,0);fn();return 0;}

 function controlaTesteReal(qtd,rotulo){
  var n=Number(qtd),r=String(rotulo||'').trim();
  if(!r||!isFinite(n)||n<1||n>20||Math.floor(n)!==n){runtime.lastControlledTest={ok:false,linhas:isFinite(n)?n:null,rotulo:r,limite:20};throw new Error('Teste real bloqueado: informe finalidade e contagem exata entre 1 e 20 linhas/entradas.');}
  runtime.lastControlledTest={ok:true,linhas:n,rotulo:r,limite:20};return clone(runtime.lastControlledTest);
 }

 function fixtureSintetica(){return global.T6_EMP_FIXTURE_SINTETICA===true;}
 function exigeFixtureSintetica(){
  if(!fixtureSintetica()&&!runtime.externalUserAction)throw new Error('Execução externa pelo usuário; o Codex somente prepara insumos e valida/importa resultados.');
 }
 function esperaResultadoExterno(){return '<div class="emp-panel"><b>AGUARDANDO RESULTADO EXTERNO</b><p class="emp-sub">Execução externa pelo usuário; o Codex somente prepara insumos e valida/importa resultados. Nenhum motor, bônus, otimizador, build ou score será calculado nesta página.</p></div>';}

 function esc(v){return String(v==null?'':v).replace(/&/g,'&amp;').replace(/</g,'&lt;')
  .replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
 function clone(v){return v==null?v:JSON.parse(JSON.stringify(v));}
 function numero(v){v=Number(v);return isFinite(v)?v:0;}
 function idCard(k){return String(k||'').split('|')[0].split('@')[0];}
 function funcChave(k){return String(k||'').split('|').slice(1).join('|')||null;}
 function modelo(){try{return typeof MT!=='undefined'?MT:null;}catch(e){return null;}}
 function catalogo(){try{return Array.isArray(D)?D:[];}catch(e){return [];}}
 function chaveCatalogo(k){var id=idCard(k),f=funcChave(k);return id+(f?'|'+f:'');}
 function registro(k){
  var c=null,limpa=chaveCatalogo(k);
  try{if(typeof mtCard==='function'){c=mtCard(k);if(!c&&limpa&&limpa!==String(k||''))c=mtCard(limpa);}}catch(e){c=null;}
  if(c)return c;
  var id=idCard(k),f=funcChave(k),L=linhasCard(id);
  for(var i=0;i<L.length;i++)if(!f||String(L[i].tipo||'')===String(f))return L[i];
  return null;
 }
 function nomeFunc(f){
  try{if(typeof global.elFuncaoVisivel==='function')return global.elFuncaoVisivel(f)||f||'—';}catch(e){}
  try{return (typeof ROT!=='undefined'&&ROT[f])||f||'—';}catch(e){return f||'—';}
 }
 function canonFunc(f){
  try{if(typeof global.elFuncaoCanonica==='function')return global.elFuncaoCanonica(nomeFunc(f));}catch(e){}
  return String(f||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
 }
 function mesmaFunc(a,b){var x=canonFunc(a);return !!x&&x===canonFunc(b);}
 function corNota(n){try{return typeof cor==='function'?cor(n,0):'#22c58b';}catch(e){return '#22c58b';}}
 function tecnicoAtual(){
  var m=modelo(),t={id:m&&m.tec!=null?m.tec:null,nome:null,bonus:[]};
  try{t.nome=typeof mtTecNome==='function'?mtTecNome()||null:null;}catch(e){}
  try{t.bonus=typeof mtTecBs==='function'?(mtTecBs()||[]).slice():[];}catch(e){t.bonus=[];}
  return t;
 }
 function entradaLista(campo,i,k){
  var m=modelo(),L=m&&m.listEntries&&Array.isArray(m.listEntries[campo])?m.listEntries[campo]:[];
  var e=L[i]&&String(L[i].cardKey||'')===String(k||'')?clone(L[i]):null;
  return e||{entryId:campo+':'+i,collection:campo,cardId:idCard(k),cardKey:k,
   functionId:funcChave(k),buildId:'base'};
 }
 function ocorrencias(){
  var m=modelo(),out=[];if(!m)return out;
  (m.slots||[]).forEach(function(sl,i){if(!sl||!sl.key)return;var c=registro(sl.key);
   out.push({id:'titular:'+i,grupo:'titulares',grupoNome:'Titular',ordem:i,key:sl.key,
    cardId:idCard(sl.key),c:c,funcAtual:sl.func||funcChave(sl.key),buildId:sl.buildId||'base',
    detalhe:sl.pos||'',sl:clone(sl),entrada:null});});
  (m.banco||[]).forEach(function(k,i){var c=registro(k),e=entradaLista('banco',i,k);
   out.push({id:'reserva:'+i,grupo:'reservas',grupoNome:'Reserva',ordem:i,key:k,
    cardId:idCard(k),c:c,funcAtual:e.functionId||funcChave(k)||(c&&c.tipo),buildId:e.buildId||'base',
    detalhe:'Banco',sl:null,entrada:e});});
  (m.elenco||[]).forEach(function(k,i){var c=registro(k),e=entradaLista('fora',i,k);
   out.push({id:'elenco:'+i,grupo:'elenco',grupoNome:'Fora do banco',ordem:i,key:k,
    cardId:idCard(k),c:c,funcAtual:e.functionId||funcChave(k)||(c&&c.tipo),buildId:e.buildId||'base',
    detalhe:'Elenco',sl:null,entrada:e});});
  return out;
 }
 function atualizaRegistros(itens){
  var mudou=false;(itens||[]).forEach(function(o){if(!o||!o.key)return;var c=registro(o.key);if(c&&c!==o.c){o.c=c;mudou=true;}});return mudou;
 }
 function invalidaIndiceCatalogo(){indiceCatalogo={lista:null,tamanho:-1,porCard:Object.create(null)};}
 function garanteIndiceCatalogo(){
  var L=catalogo();if(indiceCatalogo.lista===L&&indiceCatalogo.tamanho===L.length)return indiceCatalogo.porCard;
  var porCard=Object.create(null),vistos=Object.create(null);
  L.forEach(function(c){if(!c||c.id==='MOLDE')return;var id=idCard(c.id),func=canonFunc(c.tipo)||String(c.tipo||''),ch=id+'\u0000'+func;
   if(vistos[ch])return;vistos[ch]=1;(porCard[id]||(porCard[id]=[])).push(c);});
  indiceCatalogo={lista:L,tamanho:L.length,porCard:porCard};return porCard;
 }
 function linhasCard(cardId){
  var L=garanteIndiceCatalogo()[String(cardId)]||[];return L;
 }
 function buildSalva(cardId,buildId){
  if(!buildId||String(buildId)==='base')return null;
  var m=modelo(),L=m&&m.builds&&Array.isArray(m.builds[cardId])?m.builds[cardId]:[];
  for(var i=0;i<L.length;i++)if(String(L[i].buildId||'')===String(buildId))return L[i];
  return null;
 }
 function buildsSalvas(cardId){var m=modelo();return m&&m.builds&&Array.isArray(m.builds[cardId])?m.builds[cardId]:[];}
 function funcCatalogo(cardId,func){
  try{if(typeof global.elFuncaoDoCatalogo==='function')return global.elFuncaoDoCatalogo(cardId+'|'+func,func)||func;}catch(e){}
  return func;
 }
 function fotoBasica(key){try{return typeof global.elBuildBase==='function'?global.elBuildBase(key):null;}catch(e){return null;}}
 function avaliaFoto(cardId,func,b,origem,tec){
  exigeFixtureSintetica();
  if(!func||!b||typeof global.elNotaDaBuild!=='function')return null;
  var fcat=funcCatalogo(cardId,func),row=null;
  linhasCard(cardId).some(function(c){if(c.tipo===fcat){row=c;return true;}return false;});
  if(!row)return null;
  var key=String(row.id)+'|'+row.tipo,n=0;
  try{n=global.elNotaDaBuild(key,b,true,tec||tecnicoAtual())||0;}catch(e){n=0;}
  return isFinite(+n)&&+n>0?{func:func,catalogo:row.tipo,key:key,n:+n,origem:origem,
   buildId:origem==='basica'?'base':String(b.buildId||'base'),build:b,card:row}:null;
 }
 function pontuacaoAtual(o){
  exigeFixtureSintetica();
  try{if(typeof global.elPontuacao!=='function')return null;
   return o.sl?global.elPontuacao(o.key,o.funcAtual,true,o.sl,null)
    :global.elPontuacao(o.key,o.funcAtual,false,null,o.entrada);
  }catch(e){return null;}
 }
 function fotoAplicada(o){
  var b=buildSalva(o.cardId,o.buildId);
  if(b)return b;
  var f=funcCatalogo(o.cardId,o.funcAtual),row=linhasCard(o.cardId).find(function(c){return c.tipo===f;});
  return row?fotoBasica(String(row.id)+'|'+row.tipo):null;
 }
 function notaAplicadaComTecnico(o,tec){
  var b=fotoAplicada(o),r=avaliaFoto(o.cardId,o.funcAtual,b,o.buildId==='base'?'basica':'aplicada',tec);
  return r?r.n:0;
 }
 function candidatosAcessiveis(o,tec){
  var out=[],atual=tec?null:pontuacaoAtual(o);
  if(atual&&atual.compativel!==false&&numero(atual.n)>0){
   var ba=fotoAplicada(o);out.push({func:atual.func||o.funcAtual,catalogo:funcCatalogo(o.cardId,atual.func||o.funcAtual),
    key:o.key,n:numero(atual.n),origem:'aplicada',buildId:o.buildId||'base',build:ba,card:o.c});
  }else if(tec){var na=notaAplicadaComTecnico(o,tec),ba2=fotoAplicada(o);if(na>0)out.push({func:o.funcAtual,
   catalogo:funcCatalogo(o.cardId,o.funcAtual),key:o.key,n:na,origem:'aplicada',buildId:o.buildId||'base',build:ba2});}
  linhasCard(o.cardId).forEach(function(c){var b=fotoBasica(String(c.id)+'|'+c.tipo),r=avaliaFoto(o.cardId,c.tipo,b,'basica',tec);if(r)out.push(r);});
  buildsSalvas(o.cardId).forEach(function(b){var r=avaliaFoto(o.cardId,b&&b.func,b,'salva',tec);if(r)out.push(r);});
  out.sort(function(a,b){return b.n-a.n;});return out;
 }
 function globalSuperior(o,melhor){
  exigeFixtureSintetica();
  var superior=false;linhasCard(o.cardId).some(function(c){var n=0;try{n=typeof nota==='function'?nota(c)||0:0;}catch(e){}
   if(numero(n)>numero(melhor)+EPS){superior=true;return true;}return false;});return superior;
 }
 function funcoesSlot(sl){
  var L=[];try{L=(typeof MT_FUNCS!=='undefined'&&MT_FUNCS[sl.pos])?(MT_FUNCS[sl.pos]||[]).slice():[];}catch(e){}
  if(sl.func&&!L.some(function(f){return mesmaFunc(f,sl.func);}))L.push(sl.func);
  return L;
 }
 function candidatoCabeNoSlot(cand,o,sl){
  if(!cand||!sl)return false;
  var fs=funcoesSlot(sl);if(fs.length&&!fs.some(function(f){return mesmaFunc(f,cand.func);}))return false;
  var c=cand.card||o&&o.c||registro(cand.key);try{if(c&&typeof global.elJogaNaPos==='function'&&!global.elJogaNaPos(c,sl.pos))return false;}catch(e){return false;}
  return true;
 }
 function melhorNaVaga(o,sl,tec){
  var C=candidatosAcessiveis(o,tec).filter(function(c){return candidatoCabeNoSlot(c,o,sl);});return C[0]||null;
 }
 function grupos(itens){var q={titulares:0,reservas:0,elenco:0};itens.forEach(function(x){q[x.grupo]=(q[x.grupo]||0)+1;});return q;}
 function escolhidas(st){return (st.itens||[]).filter(function(x){return !!st.selecionadas[x.id];});}
 function selecionaGrupo(st,g){st.grupo=g;st.selecionadas={};(st.itens||[]).forEach(function(x){if(g==='todos'||x.grupo===g)st.selecionadas[x.id]=true;});st.resultados=null;}
 function grupoSelecaoValido(g){return g==='titulares'||g==='reservas'||g==='todos';}
 function valorResultadoSeguro(v){v=Number(v);return isFinite(v)&&v>=0&&v<=10000?v:null;}
 function idsUnicos(lista){var vistos=Object.create(null),out=[];(lista||[]).forEach(function(v){v=String(v||'');if(v&&!vistos[v]){vistos[v]=1;out.push(v);}});return out;}
 function serializaEstadoMelhorFuncao(st){
  var selecionadas=idsUnicos(escolhidas(st).map(function(o){return o.id;}));
  var payload={versao:1,fase:st.resultados?'resultados':'selecao',grupo:grupoSelecaoValido(st.grupo)?st.grupo:null,selecionadas:selecionadas};
  if(!st.resultados)return payload;
  payload.resultados=[];var vistos=Object.create(null);
  (st.resultados||[]).forEach(function(r){var o=r&&r.o,atual=valorResultadoSeguro(r&&r.atual),melhor=r&&r.melhor,n=melhor&&valorResultadoSeguro(melhor.n);
   if(!o||!o.id||vistos[o.id]||selecionadas.indexOf(String(o.id))<0||atual==null)return;vistos[o.id]=1;
   var linha={ocorrenciaId:String(o.id),cardId:String(o.cardId||''),pontuacaoAtual:atual,
    melhorAcessivel:melhor&&n!=null&&String(melhor.func||'')?{funcao:String(melhor.func),pontuacao:n}:null,
    estado:r.estado==='já está na melhor função'?'ja-melhor':(r.estado==='sem função compatível'?'sem-funcao':'melhor-encontrada'),
    opcaoBloqueadaSuperior:!!r.globalMelhor};
   payload.resultados.push(linha);
  });
  return payload;
 }
 function restauraEstadoMelhorFuncao(payload){
  var st=initMelhorFuncao();if(!payload||payload.versao!==1||!grupoSelecaoValido(payload.grupo)||!Array.isArray(payload.selecionadas))return st;
  st.grupo=payload.grupo;var porId=Object.create(null);st.itens.forEach(function(o){porId[o.id]=o;});
  idsUnicos(payload.selecionadas).forEach(function(id){if(porId[id]&&(st.grupo==='todos'||porId[id].grupo===st.grupo))st.selecionadas[id]=true;});
  if(payload.fase!=='resultados'||!Array.isArray(payload.resultados))return st;
  var selecionadas=escolhidas(st),esperadas=Object.create(null),vistos=Object.create(null),out=[];selecionadas.forEach(function(o){esperadas[o.id]=o;});
  payload.resultados.forEach(function(linha){var id=String(linha&&linha.ocorrenciaId||''),o=esperadas[id],atual=valorResultadoSeguro(linha&&linha.pontuacaoAtual),m=linha&&linha.melhorAcessivel,n=m&&valorResultadoSeguro(m.pontuacao);
   if(!o||vistos[id]||String(linha.cardId||'')!==String(o.cardId||'')||atual==null)return;vistos[id]=1;
   var melhor=m&&n!=null&&String(m.funcao||'')?{func:String(m.funcao),n:n}:null;
   var estado=linha.estado==='ja-melhor'?'já está na melhor função':(linha.estado==='sem-funcao'?'sem função compatível':'melhor função encontrada');
   out.push({o:o,atual:atual,melhor:melhor,ganho:melhor?Math.max(0,melhor.n-atual):0,estado:estado,globalMelhor:!!linha.opcaoBloqueadaSuperior});
  });
  if(out.length===selecionadas.length&&out.length)st.resultados=out;
  return st;
 }
 function salvaEstadoMelhorFuncao(st){
  try{var rs=global.RouteState;if(!rs||typeof rs.savePageState!=='function'||!rotaCanonicaEh(ROUTES.melhorfuncao))return false;var payload=serializaEstadoMelhorFuncao(st),ok=rs.savePageState(payload);if(ok)memoria.entradas[ROUTES.melhorfuncao]={assinatura:JSON.stringify(payload),estado:st};return ok;}catch(e){return false;}
 }
 function aplicaEstadoDaEntrada(route,pageState){
  var assinatura='';try{assinatura=JSON.stringify(pageState||null);}catch(e){assinatura='null';pageState=null;}
  var anterior=memoria.entradas[route];
  if(anterior&&anterior.assinatura===assinatura&&anterior.estado){runtime.states[route]=anterior.estado;return anterior.estado;}
  var st=restauraEstadoMelhorFuncao(pageState);runtime.states[route]=st;memoria.entradas[route]={assinatura:assinatura,estado:st};return st;
 }

 function garanteEstilo(){
  if(typeof document==='undefined'||document.getElementById('emp-style-v1'))return;
  var s=document.createElement('style');s.id='emp-style-v1';s.textContent=
   '.emp-page{min-height:calc(100vh - 90px);padding:22px;color:var(--d1,var(--txt,#eef3f7));background:linear-gradient(180deg,var(--d4,#0b1015),var(--d5,#0d131a));box-sizing:border-box}'
  +'.emp-shell{max-width:1180px;margin:0 auto}.emp-top{display:flex;align-items:center;gap:12px;margin-bottom:18px}.emp-back{flex:0 0 auto}.emp-title{margin:0;font-size:22px;line-height:1.2}.emp-sub{color:var(--d17,var(--txt2,#8fa4c4));font-size:12.5px;line-height:1.55;margin:5px 0 0}'
  +'.emp-panel{background:linear-gradient(158deg,var(--d20,#111820),var(--d58,#0e141b));border:1px solid var(--d59,var(--line,#26313d));border-radius:14px;padding:16px;margin-bottom:14px}.emp-actions{display:flex;gap:8px;flex-wrap:wrap}.emp-timefraco-controls{align-items:center;margin-top:12px}.emp-btn{cursor:pointer;background:var(--d14,#142019);border:1px solid var(--d18,#365746);color:var(--d30,#a8e8c3);border-radius:10px;padding:9px 14px;font:inherit;font-size:12px;font-weight:800}.emp-btn.on{background:var(--d25,#22c58b);color:#06200f}.emp-btn:disabled{opacity:.4;cursor:not-allowed}.emp-btn[data-emp-action="calcular"]:not(:disabled){background:#22d983;border-color:#72f0b0;color:#04150b;box-shadow:0 0 0 1px rgba(114,240,176,.2),0 6px 18px rgba(34,217,131,.28)}.emp-btn[data-emp-action="calcular"]:not(:disabled):hover{background:#37e492;border-color:#a0f7ca;box-shadow:0 0 0 1px rgba(160,247,202,.28),0 7px 21px rgba(34,217,131,.4)}.emp-btn[data-emp-action="calcular"]:focus-visible{outline:3px solid #9affc9;outline-offset:3px}.emp-btn[data-emp-action="calcular"]:disabled{background:#18211d;border-color:#303b35;color:#65736c;box-shadow:none;opacity:.55;filter:saturate(.35)}.emp-list{max-height:52vh;overflow:auto;border:1px solid var(--d10,var(--line,#26313d));border-radius:10px;margin-top:12px;padding:4px 11px;overscroll-behavior:contain}.emp-check{display:flex;align-items:center;gap:10px;padding:9px 2px;border-bottom:1px solid var(--d10,var(--line2,#18202a));cursor:pointer}.emp-check:last-child{border-bottom:0}.emp-thumb{width:46px;height:61px;object-fit:cover;border-radius:7px;flex:0 0 46px;background:var(--d5,#0d131a)}.emp-check span{flex:1;min-width:0}.emp-check small,.emp-muted{display:block;color:var(--d17,var(--txt2,#8fa4c4));font-size:11px}.emp-count{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:12px}.emp-count>div{flex:1;min-width:220px}.emp-card{padding:12px 0;border-bottom:1px solid var(--d10,var(--line2,#18202a))}.emp-card:last-child{border-bottom:0}.emp-row{display:flex;gap:10px;align-items:flex-start}.emp-row>*:first-child{flex:1;min-width:0}.emp-result-player{display:flex;align-items:center;gap:10px;min-width:0}.emp-result-player>div{min-width:0}.emp-grid4{display:grid;grid-template-columns:repeat(4,minmax(100px,1fr));gap:8px;margin-top:8px;font-size:12px}.emp-grid2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.emp-status{margin-top:7px;font-size:11.5px;font-weight:800}.emp-upsell{margin-top:7px;padding:7px 9px;border-radius:7px;background:rgba(240,165,49,.12);border:1px solid rgba(240,165,49,.35);font-size:11.5px;font-weight:800}.emp-upsell small{display:block;color:#d9a74f;font-size:9px;letter-spacing:.08em;margin-bottom:2px}.emp-error{padding:10px 12px;border:1px solid rgba(224,83,61,.5);background:rgba(224,83,61,.12);border-radius:9px;color:#ff9b8f}.emp-table{width:100%;border-collapse:collapse}.emp-table th,.emp-table td{text-align:left;padding:8px 7px;border-bottom:1px solid var(--d10,var(--line2,#18202a));white-space:normal}.emp-preview{border-color:rgba(240,165,49,.45);background:rgba(240,165,49,.07)}'
  +'.emp-weak-list{display:grid;gap:10px}.emp-weak-box{border:1px solid var(--d59,var(--line,#26313d));border-radius:12px;padding:14px;background:linear-gradient(150deg,rgba(14,22,29,.92),rgba(9,15,21,.92))}.emp-weak-head{display:flex;align-items:center;justify-content:space-between;gap:12px;padding-bottom:10px;border-bottom:1px solid var(--d10,var(--line2,#26313d))}.emp-weak-kicker,.emp-weak-side-title{display:block;font-size:9px;font-weight:900;letter-spacing:.09em;text-transform:uppercase;color:var(--d17,var(--txt2,#8fa4c4))}.emp-weak-title{display:block;font-size:16px;line-height:1.3;margin-top:2px}.emp-weak-context{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}.emp-weak-chip{border-radius:999px;padding:4px 8px;background:rgba(255,255,255,.045);color:var(--d17,var(--txt2,#8fa4c4));font-size:10px}.emp-weak-lock{border-radius:999px;padding:4px 8px;background:rgba(240,165,49,.12);color:#e9bc70;font-size:10px;font-weight:800}.emp-weak-compare{display:grid;grid-template-columns:minmax(0,1fr) 34px minmax(0,1fr);align-items:stretch;gap:8px;margin-top:10px}.emp-weak-side{min-width:0;padding:9px 10px;border-radius:9px;background:rgba(255,255,255,.026)}.emp-weak-player{display:grid;grid-template-columns:46px minmax(0,1fr) auto;align-items:center;gap:10px;margin-top:7px}.emp-weak-player-info{min-width:0}.emp-weak-player-info>b{display:block;font-size:14px;line-height:1.25;overflow-wrap:anywhere}.emp-weak-meta{display:block;color:var(--d17,var(--txt2,#8fa4c4));font-size:10.5px;line-height:1.4;margin-top:3px}.emp-weak-meta b{color:var(--d1,var(--txt,#eef3f7));font-weight:700}.emp-weak-score{text-align:right;padding-left:6px}.emp-weak-score small{display:block;color:var(--d17,var(--txt2,#8fa4c4));font-size:8px;font-weight:900;letter-spacing:.08em}.emp-weak-score b{display:block;font-size:22px;line-height:1;color:var(--d1,var(--txt,#eef3f7));margin-top:3px}.emp-weak-vs{align-self:center;justify-self:center;width:28px;height:28px;border-radius:50%;display:grid;place-items:center;background:rgba(255,255,255,.055);color:var(--d17,var(--txt2,#8fa4c4));font-size:13px;font-weight:900}.emp-weak-verdict{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-top:10px;padding:9px 10px;border-radius:8px;background:rgba(255,255,255,.035);font-size:11.5px;font-weight:800}.emp-weak-delta{font-size:13px}.emp-weak-facts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin-top:9px}.emp-weak-facts span{min-width:0;padding:7px;border-radius:7px;background:rgba(255,255,255,.035);color:var(--d17,var(--txt2,#8fa4c4));font-size:10px;line-height:1.3}.emp-weak-facts b{display:block;color:var(--d1,var(--txt,#eef3f7));font-size:11.5px;overflow-wrap:anywhere;margin-top:2px}.emp-weak-modebar,.emp-mode-bbar{margin:0 0 10px;padding:8px 10px;border-radius:9px;font-size:11px}.emp-weak-modebar{border:1px solid rgba(34,197,139,.28);background:rgba(34,197,139,.07);color:#a8e8c3}.emp-mode-bbar{border:1px solid rgba(240,165,49,.3);background:rgba(240,165,49,.07);color:#d9b77a}.emp-mode-bbar b{display:block;font-size:9.5px;letter-spacing:.07em;margin-bottom:2px}.emp-mode-compact{display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin-bottom:10px;color:var(--d17,var(--txt2,#8fa4c4));font-size:10.5px}.emp-mode-tag{border-radius:999px;padding:5px 9px;font-weight:800}.emp-mode-tag.a{background:rgba(34,197,139,.11);color:#9fe1bd}.emp-mode-tag.b{background:rgba(240,165,49,.11);color:#dfb36b}'
  +'@media(max-width:760px){.emp-page{padding:12px}.emp-title{font-size:18px}.emp-grid4{grid-template-columns:repeat(2,minmax(0,1fr))}.emp-grid2{grid-template-columns:1fr}.emp-weak-compare{grid-template-columns:1fr}.emp-weak-vs{transform:rotate(90deg);margin:-3px 0}.emp-list{max-height:46vh}.emp-panel{padding:12px}.emp-weak-head{align-items:flex-start}.emp-weak-context{justify-content:flex-start}}@media(max-width:480px){.emp-weak-head{display:block}.emp-weak-context{margin-top:7px}.emp-weak-player{grid-template-columns:46px minmax(0,1fr)}.emp-weak-score{grid-column:2;text-align:left;padding:4px 0 0}.emp-weak-score small,.emp-weak-score b{display:inline}.emp-weak-score b{font-size:17px;margin-left:5px}}@media(max-width:420px){.emp-grid4,.emp-weak-facts{grid-template-columns:1fr}.emp-top{align-items:flex-start}}';
  document.head.appendChild(s);
 }
 function miniaturaCard(cardId,ocorrenciaId){return '<img class="emp-thumb" data-emp-thumb="'+esc(ocorrenciaId||idCard(cardId))+'" alt="" aria-hidden="true" loading="lazy" src="https://efimg.com/efootballhub22/images/player_cards/'+esc(idCard(cardId))+'_l.png" onerror="this.style.visibility=&quot;hidden&quot;">';}
 function removeMiniaturasDuplicadas(root){
  if(!root||typeof root.querySelectorAll!=='function')return 0;
  var vistos=Object.create(null),removidas=0,nos=root.querySelectorAll('.emp-thumb[data-emp-thumb]');
  Array.prototype.forEach.call(nos,function(img){var k=String(img.getAttribute('data-emp-thumb')||'');if(!k||!vistos[k]){if(k)vistos[k]=1;return;}if(typeof img.remove==='function')img.remove();else if(img.parentNode)img.parentNode.removeChild(img);removidas++;});
  return removidas;
 }
 function botaoGrupo(id,rot,q,st){return '<button class="emp-btn'+(st.grupo===id?' on':'')+'" data-emp-action="grupo" data-group="'+id+'"'+(q?'':' disabled')+'>'+rot+' · '+q+'</button>';}
 function listaSelecao(st){
  var L=st.grupo?(st.itens||[]).filter(function(x){return st.grupo==='todos'||x.grupo===st.grupo;}):[];
  if(!L.length)return '<div class="emp-muted" style="margin-top:12px">Escolha primeiro um grupo.</div>';
  return '<div class="emp-list">'+L.map(function(x){return '<label class="emp-check"><input type="checkbox" data-emp-change="ocorrencia" data-id="'+esc(x.id)+'" '+(st.selecionadas[x.id]?'checked':'')+'>'+miniaturaCard(x.cardId,x.id)+'<span><b>'+esc(x.c&&x.c.nome||('Card '+x.cardId))+'</b><small>'+esc(x.grupoNome)+(x.detalhe?' · '+esc(x.detalhe):'')+' · função atual: '+esc(nomeFunc(x.funcAtual))+'</small></span></label>';}).join('')+'</div>';
 }
 function seletorOcorrencias(st,explicacao){
  var q=grupos(st.itens||[]),n=escolhidas(st).length;
  return '<div class="emp-panel"><p class="emp-sub">'+esc(explicacao)+'</p><div class="emp-actions">'
   +botaoGrupo('titulares','Titulares',q.titulares,st)+botaoGrupo('reservas','Reservas',q.reservas,st)
   +botaoGrupo('todos','Elenco inteiro',(st.itens||[]).length,st)+'</div>'+listaSelecao(st)
   +'<div class="emp-count"><div><b data-emp-count>'+n+' ocorrência'+(n===1?'':'s')+' selecionada'+(n===1?'':'s')+'</b><small class="emp-muted">Só esta seleção entra no cálculo e em qualquer aplicação futura.</small></div>'
   +'<button class="emp-btn" data-emp-action="calcular" '+(n?'':'disabled')+'>CALCULAR SELECIONADOS</button></div></div>';
 }
function avisoComercial(){return '<div class="emp-upsell"><small>MODO B · MELHOR ABSOLUTA DO SISTEMA</small>🔒 Existe uma opção melhor disponível</div>';}
function explicaModoB(){return '<div class="emp-mode-bbar"><b>MODO B · MELHOR ABSOLUTA DO SISTEMA</b>A comparação é feita privadamente. Se uma build bloqueada superar as suas, aparece somente um aviso genérico, sem nota, função, nome ou receita.</div>';}
function modosBuildCompactos(){return '<div class="emp-mode-compact"><span class="emp-mode-tag a">MODO A · SUAS BUILDS — resultado exibido</span><span class="emp-mode-tag b">MODO B · MELHOR ABSOLUTA DO SISTEMA — privado</span></div>';}
function avisoComercialCompacto(){return '<span class="emp-weak-lock">🔒 Existe uma opção melhor disponível</span>';}
 function estadoVazio(txt){return '<div class="emp-panel"><div class="emp-muted">'+esc(txt)+'</div></div>';}
 function paginaShell(route,corpo){return '<section class="emp-page" data-emp-route="'+esc(route)+'"><div class="emp-shell">'
  +'<div class="emp-top"><button class="emp-btn emp-back" data-emp-action="voltar">← VOLTAR AO ELENCO</button><div><h1 class="emp-title">'+esc(TITULOS[route]||route)+'</h1></div></div>'+corpo+'</div></section>';}

 function estadoDaRota(route,init){if(!runtime.states[route])runtime.states[route]=init();return runtime.states[route];}
 function atualizaContador(root,st){
  var n=escolhidas(st).length,c=root&&root.querySelector('[data-emp-count]'),b=root&&root.querySelector('[data-emp-action="calcular"]');
  if(c)c.textContent=n+' ocorrência'+(n===1?'':'s')+' selecionada'+(n===1?'':'s');if(b)b.disabled=!n;
 }
 function acaoSelecao(st,acao,dados){
  if(acao==='grupo'){selecionaGrupo(st,dados.group);return true;}
  if(acao==='revisar'){st.resultados=null;return true;}
  return false;
 }

 /* 1 · MELHOR FUNCAO DE CADA UM — somente leitura. */
 function initMelhorFuncao(){return {itens:ocorrencias(),grupo:null,selecionadas:{},resultados:null};}
 function calculaMelhorFuncao(st){
  st.resultados=escolhidas(st).map(function(o){var atual=pontuacaoAtual(o),C=candidatosAcessiveis(o),top=C[0]||null;
   var na=atual&&isFinite(+atual.n)?+atual.n:0;if(!top)return {o:o,atual:na,melhor:null,ganho:0,estado:'sem função compatível',globalMelhor:false};
   var ganho=Math.max(0,top.n-na),ja=mesmaFunc(top.func,(atual&&atual.func)||o.funcAtual)&&ganho<=EPS;
   return {o:o,atual:na,melhor:top,ganho:ganho,estado:ja?'já está na melhor função':'melhor função encontrada',
    globalMelhor:globalSuperior(o,top.n)};});
 }
 function renderMelhorFuncao(st){
  if(!st.resultados)return seletorOcorrencias(st,'Escolha um grupo inicial e revise jogador por jogador. Builds bloqueadas nunca participam do resultado acessível.');
  var vistos=Object.create(null),resultados=st.resultados.filter(function(r){var id=r&&r.o&&r.o.id;if(!id||vistos[id])return false;vistos[id]=1;return true;});
  var L=resultados.map(function(r){var o=r.o,sem=!r.melhor,cor=sem?'#e0533d':(r.estado==='já está na melhor função'?'#22c58b':'#f0a531');
   return '<div class="emp-card"><div class="emp-row"><div class="emp-result-player">'+miniaturaCard(o.cardId,o.id)+'<div><b>'+esc(o.c&&o.c.nome||('Card '+o.cardId))+'</b><small class="emp-muted">'+esc(o.grupoNome)+(o.detalhe?' · '+esc(o.detalhe):'')+'</small></div></div><b style="color:'+(r.ganho>EPS?'#f0a531':'#8fa4c4')+'">'+(r.ganho>EPS?'+'+r.ganho.toFixed(1):'—')+'</b></div>'
    +'<div class="emp-grid4"><span>Função atual<br><b>'+esc(nomeFunc(o.funcAtual))+'</b></span><span>Melhor acessível<br><b>'+esc(sem?'—':nomeFunc(r.melhor.func))+'</b></span><span>Pontuação atual<br><b>'+(r.atual>0?r.atual.toFixed(1):'—')+'</b></span><span>Pontuação possível<br><b>'+(r.melhor?r.melhor.n.toFixed(1):'—')+'</b></span></div>'
    +'<div class="emp-status" style="color:'+cor+'">'+esc(r.estado)+'</div>'+(r.globalMelhor?avisoComercial():'')+'</div>';}).join('');
 return '<div class="emp-panel"><div class="emp-weak-modebar"><b>MODO A · SUAS BUILDS</b> — resultado calculado somente com builds Básica, aplicadas ou salvas acessíveis.</div>'+explicaModoB()+'<p class="emp-sub">Nenhuma build foi alterada.</p>'+L+'<div class="emp-actions" style="margin-top:12px"><button class="emp-btn" data-emp-action="revisar">REVISAR SELEÇÃO</button></div></div>';
}

 /* 2 · ONDE MEU TIME ESTA FRACO — duas visoes independentes. */
 function initTimeFraco(){return {itens:ocorrencias(),visao:'titulares',resultados:null,processando:false,erro:null};}
 function candidatosAcessiveisPreparados(o,ctx){
  var id=String(o&&o.id||o&&o.key||'');if(!ctx.acessiveis[id])ctx.acessiveis[id]=candidatosAcessiveis(o);return ctx.acessiveis[id];
 }
 function candidatosGlobaisPreparados(o,ctx){
  exigeFixtureSintetica();var id=String(o&&o.id||o&&o.key||'');if(ctx.globais[id])return ctx.globais[id];
  var out=[];linhasCard(o.cardId).forEach(function(c){var n=0;try{n=typeof nota==='function'?nota(c)||0:0;}catch(e){n=0;}
   if(numero(n)>0)out.push({func:c.tipo,key:String(c.id)+'|'+c.tipo,n:numero(n),card:c});});
  out.sort(function(a,b){return b.n-a.n;});ctx.globais[id]=out;return out;
 }
 function melhorNaVagaPreparado(o,sl,ctx){
  var C=candidatosAcessiveisPreparados(o,ctx);for(var i=0;i<C.length;i++)if(candidatoCabeNoSlot(C[i],o,sl))return C[i];return null;
 }
 function candidatoAtualComparavel(o,p){
  if(!o||!p||p.compativel===false||numero(p.n)<=0)return null;
  return {func:p.func||o.funcAtual,catalogo:funcCatalogo(o.cardId,p.func||o.funcAtual),key:o.key,n:numero(p.n),
   origem:String(o.buildId||'base')==='base'?'basica':'aplicada',buildId:o.buildId||'base',build:fotoAplicada(o),card:o.c};
 }
 function rotuloBuild(cand,o){
  if(!cand)return '—';var id=String(cand.buildId||o&&o.buildId||'base');
  if(cand.origem==='basica'||id==='base')return 'Básica';
  var b=cand.build||o&&buildSalva(o.cardId,id);if(b&&String(b.nome||'').trim())return String(b.nome).trim();
  return cand.origem==='salva'?'Build salva':'Build aplicada';
 }
 function tecnicoDaAnalise(t){return t&&t.nome?String(t.nome):'Sem técnico';}
 function ladoComparacao(o,cand,titulo,id){
  if(!o||!cand)return '<section class="emp-weak-side"><small class="emp-weak-side-title">'+esc(titulo)+'</small><b style="display:block;margin-top:12px;color:#e0533d">Sem opção compatível</b></section>';
  return '<section class="emp-weak-side"><small class="emp-weak-side-title">'+esc(titulo)+'</small><div class="emp-weak-player">'+miniaturaCard(o.cardId,id)+'<div class="emp-weak-player-info"><b>'+esc(o.c&&o.c.nome||o.cardId)+'</b><span class="emp-weak-meta">Build: <b>'+esc(rotuloBuild(cand,o))+'</b><br>Função: <b>'+esc(nomeFunc(cand.func))+'</b></span></div><div class="emp-weak-score"><small>NOTA</small><b>'+numero(cand.n).toFixed(1)+'</b></div></div></section>';
 }
 function globalSuperiorNaVaga(opcoes,sl,melhorAcessivel,ctx){
  var limite=melhorAcessivel&&melhorAcessivel.c?numero(melhorAcessivel.c.n):0;
  return (opcoes||[]).some(function(o){return candidatosGlobaisPreparados(o,ctx).some(function(c){return c.n>limite+EPS&&candidatoCabeNoSlot(c,o,sl);});});
 }
 function analisaTimeFraco(){
  var m=modelo(),todos=ocorrencias(),slots=m&&Array.isArray(m.slots)?m.slots:[],alts=[],titularesPorSlot=Object.create(null);
  todos.forEach(function(o){if(o.grupo==='titulares')titularesPorSlot[o.ordem]=o;else if(o.grupo==='reservas'||o.grupo==='elenco')alts.push(o);});
  var ctx={acessiveis:Object.create(null),globais:Object.create(null)},titulares=[],profundidade=[],tec=tecnicoAtual();
  slots.forEach(function(sl,i){
   var atual=titularesPorSlot[i]||null,p=atual?pontuacaoAtual(atual):null,atualComparavel=candidatoAtualComparavel(atual,p),notaAtual=atualComparavel?atualComparavel.n:0;
   var subs=alts.map(function(o){return {o:o,c:melhorNaVagaPreparado(o,sl,ctx)};}).filter(function(x){return x.c;}).sort(function(a,b){return b.c.n-a.c.n;});
   var melhor=subs[0]||null,diferenca=melhor?melhor.c.n-notaAtual:null,recomendada=!!(melhor&&(!atual||diferenca>EPS)),ganho=melhor?Math.max(0,diferenca):0,globalMelhor=globalSuperiorNaVaga(alts,sl,melhor,ctx);
   titulares.push({sl:sl,atual:atual,atualComparavel:atualComparavel,notaAtual:notaAtual,alternativa:melhor,diferenca:diferenca,recomendada:recomendada,ganho:atual?ganho:(melhor?melhor.c.n:0),
     estado:atual?(ganho>EPS?'há troca melhor no seu elenco':'sem troca melhor no seu elenco'):'vaga vazia',critica:!atual,globalMelhor:globalMelhor});
   profundidade.push({sl:sl,titular:atual,titularComparavel:atualComparavel,notaTitular:notaAtual,substitutos:subs,melhor:melhor,
     queda:melhor&&notaAtual>0?Math.max(0,notaAtual-melhor.c.n):null,
     estado:subs.length===0?'sem cobertura':(subs.length===1?'cobertura curta':'cobertura disponível'),globalMelhor:globalMelhor});
  });
  return {tecnico:{id:tec.id,nome:tec.nome||null},titulares:titulares,profundidade:profundidade};
 }
 function analiseTitulares(){return analisaTimeFraco().titulares;}
 function analiseProfundidade(){return analisaTimeFraco().profundidade;}
 function renderTimeFraco(st){
  var tabs='<button class="emp-btn'+(st.visao==='titulares'?' on':'')+'" data-emp-action="visao" data-view="titulares">TITULARES</button><button class="emp-btn'+(st.visao==='profundidade'?' on':'')+'" data-emp-action="visao" data-view="profundidade">PROFUNDIDADE DO ELENCO</button>';
  if(!st.resultados){var esperando=(st.itens||[]).some(function(o){return !o.c;}),bloqueado=esperando||st.processando;
   var botao='<button class="emp-btn" data-emp-action="analisartimefraco"'+(bloqueado?' disabled':'')+'>'+(esperando?'AGUARDANDO CARDS':(st.processando?'ANALISANDO…':'ANALISAR O TIME'))+'</button>';
   return '<div class="emp-panel"><p class="emp-sub">As duas visões são independentes. Titulares compara cada vaga com Reservas e Fora do banco; Profundidade mede cobertura e queda dos substitutos. A análise é somente leitura.</p><div class="emp-actions emp-timefraco-controls">'+tabs+botao+'</div>'+(st.erro?'<div class="emp-error" style="margin-top:12px">'+esc(st.erro)+'</div>':'')+'</div>';}
  if(st.visao==='titulares'){
   var A=st.resultados.titulares||[],tec=tecnicoDaAnalise(st.resultados.tecnico),h=A.map(function(x,ix){var a=x.atual,c=x.alternativa,d=x.diferenca;
    var tituloAlt=!c?'MELHOR ALTERNATIVA DISPONÍVEL':(x.recomendada?'TROCA QUE MELHORA':'MELHOR ALTERNATIVA DISPONÍVEL');
    var delta=x.critica?(c?'Preenchimento disponível':'Vaga sem opção'):(x.recomendada?'Ganho +'+x.ganho.toFixed(1):(c?(Math.abs(numero(d))<=EPS?'Não melhora · mesma nota':'Não melhora · '+numero(d).toFixed(1)):'Sem alternativa'));
    var cor=x.critica?'#e0533d':(x.recomendada?'#22c58b':'#8fa4c4');
    return '<article class="emp-weak-box"><div class="emp-weak-head"><div><small class="emp-weak-kicker">Vaga e função avaliadas</small><b class="emp-weak-title">'+esc(x.sl.pos||'Vaga')+' · '+esc(nomeFunc(x.sl.func))+'</b></div><div class="emp-weak-context"><span class="emp-weak-chip">Técnico: '+esc(tec)+'</span>'+(x.globalMelhor?avisoComercialCompacto():'')+'</div></div>'
     +'<div class="emp-weak-compare">'+ladoComparacao(a,x.atualComparavel,'TITULAR','timefraco-titular-'+ix)+'<span class="emp-weak-vs" aria-hidden="true">→</span>'+ladoComparacao(c&&c.o,c&&c.c,tituloAlt,'timefraco-alternativa-'+ix)+'</div>'
     +'<div class="emp-weak-verdict"><span style="color:'+cor+'">'+esc(x.estado)+'</span><b class="emp-weak-delta" style="color:'+cor+'">'+esc(delta)+'</b></div></article>';}).join('');
   return '<div class="emp-panel"><p class="emp-sub">Cada vaga usa o técnico indicado e compara a build do titular com a melhor build acessível de Reservas ou Fora do banco. “Melhor alternativa disponível” só vira “troca que melhora” quando sua nota comparável é realmente maior.</p><div class="emp-actions emp-timefraco-controls">'+tabs+'</div></div><div class="emp-panel">'+modosBuildCompactos()+'<div class="emp-weak-list">'+(h||'<div class="emp-muted">Nenhuma vaga disponível.</div>')+'</div></div>';
  }
  var P=st.resultados.profundidade||[],tecP=tecnicoDaAnalise(st.resultados.tecnico),hp=P.map(function(x,ix){var m=x.melhor,cor=x.substitutos.length===0?'#e0533d':(x.substitutos.length===1?'#f0a531':'#22c58b');
   var delta=x.queda==null?'Queda indisponível':'Queda '+x.queda.toFixed(1);
   return '<article class="emp-weak-box"><div class="emp-weak-head"><div><small class="emp-weak-kicker">Vaga e função avaliadas</small><b class="emp-weak-title">'+esc(x.sl.pos||'Vaga')+' · '+esc(nomeFunc(x.sl.func))+'</b></div><div class="emp-weak-context"><span class="emp-weak-chip">Técnico: '+esc(tecP)+'</span><span class="emp-weak-chip">'+x.substitutos.length+' opção'+(x.substitutos.length===1?'':'ões')+'</span>'+(x.globalMelhor?avisoComercialCompacto():'')+'</div></div>'
    +'<div class="emp-weak-compare">'+ladoComparacao(x.titular,x.titularComparavel,'TITULAR','timefraco-profundidade-titular-'+ix)+'<span class="emp-weak-vs" aria-hidden="true">→</span>'+ladoComparacao(m&&m.o,m&&m.c,'MELHOR SUBSTITUTO','timefraco-substituto-'+ix)+'</div>'
    +'<div class="emp-weak-verdict"><span style="color:'+cor+'">'+esc(x.estado)+'</span><b class="emp-weak-delta" style="color:'+cor+'">'+esc(delta)+'</b></div></article>';}).join('');
  return '<div class="emp-panel"><p class="emp-sub">Profundidade mede quantas builds acessíveis cobrem a mesma vaga e a queda entre a build do titular e a melhor build substituta, sempre com o técnico indicado.</p><div class="emp-actions emp-timefraco-controls">'+tabs+'</div></div><div class="emp-panel">'+modosBuildCompactos()+'<div class="emp-weak-list">'+(hp||'<div class="emp-muted">Nenhuma vaga disponível.</div>')+'</div></div>';
 }

 /* Autoridades mutantes compartilhadas. A abertura e os calculos nunca passam
    por estas funcoes; somente a confirmacao explicita pode persistir. */
 function restauraModelo(m,foto){
  Object.keys(m).forEach(function(k){delete m[k];});Object.keys(foto||{}).forEach(function(k){m[k]=clone(foto[k]);});
 }
function transacao(mutador){
  var m=modelo();if(!m)return {ok:false,erro:'Estado do Elenco indisponível.'};
  var antes=clone(m);
  try{
   mutador(m);
   if(typeof userStateSave!=='function')throw new Error('Persistência canônica indisponível.');
   if(userStateSave()===false)throw new Error('A persistência canônica recusou a alteração.');
   return {ok:true};
  }catch(e){
   restauraModelo(m,antes);runtime.lastError=e;
   return {ok:false,erro:'Nada foi alterado. Não foi possível salvar a aplicação.'};
  }
 }
 function catalogoTecnicos(){try{return typeof TECS!=='undefined'&&Array.isArray(TECS)?TECS:[];}catch(e){return [];}}
 function tecnicoIndice(i){
  if(i===null||i===undefined||i==='')return {id:null,nome:'Sem técnico',bonus:[]};
  var L=catalogoTecnicos(),t=L[+i];return t?{id:+i,nome:t[0],bonus:(t[1]||[]).slice()}:null;
 }
 function tecnicosDisponiveis(){
  var m=modelo(),ids=[null],vistos={'sem':1};
  function add(v){if(v===null||v===undefined||v==='')return;var k=String(+v);if(!vistos[k]){vistos[k]=1;ids.push(+v);}}
  if(m){add(m.tec);(m.tecRes||[]).forEach(add);}
  return ids.map(tecnicoIndice).filter(Boolean);
 }
 function aplicaTecnico(m,id){
  var antigo=m.tec,novos=(m.tecRes||[]).filter(function(x){return String(x)!==String(id);});
  if(antigo!==null&&antigo!==undefined&&String(antigo)!==String(id)&&!novos.some(function(x){return String(x)===String(antigo);}))novos.push(antigo);
  m.tec=id===null?null:+id;m.tecRes=novos;
 }

 /* 3 · TECNICO DO TIME INTEIRO. Pré-auth: somente atual + reservas locais. */
 function initTecnico(){return {itens:ocorrencias(),grupo:null,selecionadas:{},resultados:null,globalMelhor:false,escolhida:0,preview:null,feito:null};}
 function calculaTecnicos(st){
   var itens=escolhidas(st),atual=tecnicoAtual(),base=itens.reduce(function(s,o){return s+notaAplicadaComTecnico(o,atual);},0);
   st.resultados=tecnicosDisponiveis().map(function(t){var por=itens.map(function(o){var n=notaAplicadaComTecnico(o,t),a=notaAplicadaComTecnico(o,atual);return {o:o,a:a,n:n,d:n-a};});
    var soma=por.reduce(function(s,x){return s+x.n;},0);return {tec:t,soma:soma,media:itens.length?soma/itens.length:0,ganho:soma-base,por:por};
   }).sort(function(a,b){return b.soma-a.soma;});
   st.globalMelhor=itens.some(function(o){var limite=0;st.resultados.forEach(function(r){var x=(r.por||[]).find(function(y){return y.o.id===o.id;});if(x)limite=Math.max(limite,numero(x.n),numero(x.a));});return globalSuperior(o,limite);});
   st.escolhida=0;st.preview=null;st.feito=null;
  }
 function renderTecnico(st){
  if(!st.resultados)return seletorOcorrencias(st,'Compare o técnico atual e os técnicos reservas presentes no seu estado local. As builds aplicadas são preservadas.');
  if(!st.resultados.length)return estadoVazio('Nenhum técnico local disponível para comparar.');
  var escolhida=Math.max(0,Math.min(st.resultados.length-1,numero(st.escolhida))),top=st.resultados[escolhida]||st.resultados[0],m=modelo(),atual=m&&m.tec!=null?+m.tec:null;
  var cards=st.resultados.map(function(r,i){return '<div class="emp-card"><div class="emp-row"><div><b>'+(i===0?'🥇 ':'')+esc(r.tec.nome)+'</b><small class="emp-muted">'+esc((r.tec.bonus||[]).join(' · ')||'sem bônus')+'</small></div><b style="color:'+(r.ganho>EPS?'#22c58b':'#8fa4c4')+'">'+(r.ganho>EPS?'+':'')+r.ganho.toFixed(1)+'</b></div>'
   +'<div class="emp-grid4"><span>Média do grupo<br><b>'+r.media.toFixed(1)+'</b></span><span>Jogadores analisados<br><b>'+r.por.length+'</b></span><span>Builds<br><b>preservadas</b></span><span>Estado<br><b>'+(String(r.tec.id)===String(atual)?'atual':'disponível')+'</b></span></div>'
   +'<div class="emp-actions" style="margin-top:8px"><button class="emp-btn'+(i===escolhida?' on':'')+'" data-emp-action="escolhertecnico" data-index="'+i+'">'+(i===escolhida?'SELECIONADO':'SELECIONAR')+'</button></div></div>';}).join('');
  var porJogador=top.por.slice().sort(function(a,b){return b.d-a.d;}).map(function(x,i){var cand={func:x.o.funcAtual,n:x.n,origem:String(x.o.buildId||'base')==='base'?'basica':'aplicada',buildId:x.o.buildId||'base',build:fotoAplicada(x.o)};return '<article class="emp-weak-box"><div class="emp-row"><div class="emp-result-player">'+miniaturaCard(x.o.cardId,'tecnico-jogador-'+i)+'<div><b>'+esc(x.o.c&&x.o.c.nome||x.o.cardId)+'</b><small class="emp-muted">Build comparada: '+esc(rotuloBuild(cand,x.o))+'</small></div></div><b style="color:'+(x.d>EPS?'#22c58b':(x.d<-EPS?'#e0533d':'#8fa4c4'))+'">'+(x.d>=0?'+':'')+x.d.toFixed(1)+'</b></div><div class="emp-weak-facts"><span>Função calculada<b>'+esc(nomeFunc(x.o.funcAtual))+'</b></span><span>'+esc(tecnicoAtual().nome||'Sem técnico')+'<b>'+numero(x.a).toFixed(1)+'</b></span><span>'+esc(top.tec.nome)+'<b>'+numero(x.n).toFixed(1)+'</b></span></div></article>';}).join('');
  var a='<div class="emp-actions" style="margin-top:12px"><button class="emp-btn" data-emp-action="revisar">REVISAR SELEÇÃO</button>';
  if(String(top.tec.id)!==String(atual))a+='<button class="emp-btn" data-emp-action="prevertecnico">VER PRÉVIA DE APLICAÇÃO</button>';a+='</div>';
  var p='';if(st.preview){p='<div class="emp-panel emp-preview"><b>Prévia — nenhuma alteração feita</b><p class="emp-sub">Técnico atual: '+esc(tecnicoAtual().nome||'Sem técnico')+' → '+esc(st.preview.tec.nome)+'. Builds e escalação permanecem iguais.</p><div class="emp-actions"><button class="emp-btn" data-emp-action="confirmartecnico">CONFIRMAR APLICAÇÃO</button><button class="emp-btn" data-emp-action="cancelarpreview">CANCELAR</button></div></div>';}
  if(st.feito)p='<div class="emp-panel"><div class="emp-status" style="color:#22c58b">'+esc(st.feito)+'</div></div>';
  return '<div class="emp-panel"><div class="emp-weak-modebar"><b>MODO A · SUAS BUILDS</b> — compara técnicos mantendo exatamente a build aplicada de cada ocorrência selecionada.</div>'+explicaModoB()+(st.globalMelhor?avisoComercial():'')+'<p class="emp-sub">Ranking agregado somente das ocorrências selecionadas. Nenhuma build é substituída.</p>'+cards+a+'</div><div class="emp-panel"><b>Impacto por build e jogador · '+esc(top.tec.nome)+'</b><div class="emp-weak-list" style="margin-top:10px">'+porJogador+'</div></div>'+p;
 }

 /* Otimizador de formação. Um grupo por nome de jogador impede que o mesmo
    jogador ocupe duas vagas, inclusive quando há mais de um card dele. */
 function slotsDaFormacao(nome){
  var f=[];try{f=(typeof MT_FORM!=='undefined'&&MT_FORM[nome])?MT_FORM[nome]:[];}catch(e){}
  return f.map(function(x){var fs=[];try{fs=(typeof MT_FUNCS!=='undefined'&&MT_FUNCS[x[0]])||[];}catch(e){}
   return {pos:x[0],func:fs[0]||'',x:x[1],y:x[2]};});
 }
 function nomesFormacoes(){try{return typeof MT_FORM!=='undefined'?Object.keys(MT_FORM):[];}catch(e){return [];}}
 function uidJogador(o){try{var inv=global.ElencoCardInvariant,p=inv&&typeof inv.playerId==='function'?inv.playerId(o&&o.key):null;if(p!==null&&p!==undefined&&String(p)!=='')return 'player:'+String(p);}catch(e){}var n=o&&o.c&&o.c.nome;return canonFunc(n||o.cardId||o.id);}
 function jogadoresUnicos(itens){var mapa=Object.create(null),out=[];(itens||[]).forEach(function(o){var k=uidJogador(o);if(!mapa[k]){mapa[k]={uid:k,ocorrencias:[]};out.push(mapa[k]);}mapa[k].ocorrencias.push(o);});return out;}
 function popcount(n){var c=0;while(n){n&=n-1;c++;}return c;}
 function resolveFormacao(nome,tec){
  var slots=slotsDaFormacao(nome),jogs=jogadoresUnicos(ocorrencias()),dp={0:{score:0,assign:[]}};
  jogs.forEach(function(j){
   var porSlot=slots.map(function(sl){var melhor=null;j.ocorrencias.forEach(function(o){var c=melhorNaVaga(o,sl,tec);if(c&&(!melhor||c.n>melhor.c.n))melhor={o:o,c:c};});return melhor;});
   var next=Object.assign({},dp),ks=Object.keys(dp);
   ks.forEach(function(k){var mask=+k,base=dp[k];porSlot.forEach(function(cand,i){if(!cand||(mask&(1<<i)))return;var nm=mask|(1<<i),ns=base.score+cand.c.n,old=next[nm];if(!old||ns>old.score)next[nm]={score:ns,assign:base.assign.concat([{slot:i,o:cand.o,c:cand.c}])};});});
   dp=next;
  });
  var best=null;Object.keys(dp).forEach(function(k){var x=dp[k],fill=popcount(+k);if(!best||fill>best.preenchidos||(fill===best.preenchidos&&x.score>best.score))best={mask:+k,score:x.score,preenchidos:fill,assign:x.assign};});
  best=best||{mask:0,score:0,preenchidos:0,assign:[]};best.formacao=nome;best.slots=slots;best.lacunas=slots.length-best.preenchidos;best.media=best.preenchidos?best.score/best.preenchidos:0;best.tec=tec||tecnicoAtual();return best;
 }
 function somaAtual(){return ocorrencias().filter(function(o){return o.grupo==='titulares';}).reduce(function(s,o){return s+numero((pontuacaoAtual(o)||{}).n);},0);}
 function analisaFormacoes(tec){
  var atual=somaAtual(),todos=ocorrencias(),ctx={acessiveis:Object.create(null),globais:Object.create(null)};
  return nomesFormacoes().map(function(n){var p=resolveFormacao(n,tec),por=Object.create(null);p.ganho=p.score-atual;(p.assign||[]).forEach(function(a){por[a.slot]=a;});
   p.globalMelhor=(p.slots||[]).some(function(sl,i){return globalSuperiorNaVaga(todos,sl,por[i]||null,ctx);});return p;
  }).sort(function(a,b){return a.lacunas-b.lacunas||b.score-a.score;});
 }
 function nomeOcorrencia(o){return o&&o.c&&o.c.nome||('Card '+(o&&o.cardId||'—'));}
function resumoPlano(p){
  var por=Object.create(null);(p.assign||[]).forEach(function(a){por[a.slot]=a;});
  return (p.slots||[]).map(function(sl,i){var a=por[i],jogador=a?'<div class="emp-result-player">'+miniaturaCard(a.o.cardId,'formacao-'+p.formacao+'-'+i)+'<div><b>'+esc(nomeOcorrencia(a.o))+'</b><small class="emp-muted">'+esc(nomeFunc(a.c.func))+'</small></div></div>':'<b style="color:#e0533d">VAGA NÃO PREENCHIDA</b>';
   return '<div class="emp-card"><div class="emp-row"><div><b>'+esc(sl.pos)+' · '+esc(a?nomeFunc(a.c.func):nomeFunc(sl.func))+'</b>'+jogador+'</div><b>'+(a?a.c.n.toFixed(1):'—')+'</b></div>'+(a?'<div class="emp-status">Modo A · '+esc(rotuloBuild(a.c,a.o))+' · build acessível; nenhuma receita é exibida.</div>':'')+'</div>';}).join('');
 }
 function validaUnicidadePlano(m){
  var inv=global.ElencoCardInvariant;if(!inv||typeof inv.audit!=='function')throw new Error('Invariante canônico do Elenco indisponível.');
  var a=inv.audit(m);if(!a||a.ok!==true)throw new Error('A proposta repetiria um card no Elenco.');
 }
 function metaLista(o,c,campo,i){var e=clone(o.entrada||{});e.entryId=e.entryId||campo+':planejado:'+i;e.collection=campo;e.cardId=o.cardId;e.cardKey=o.key;e.functionId=c&&c.func||o.funcAtual;e.buildId=c&&c.buildId||o.buildId||'base';return e;}
function aplicaPlano(m,p,tecId){
  validaPlanoAplicavel(p);
  var por=Object.create(null),usados=Object.create(null);(p.assign||[]).forEach(function(a){por[a.slot]=a;usados[a.o.id]=1;});
  m.form=p.formacao;m.slots=(p.slots||[]).map(function(sl,i){var a=por[i];return {pos:sl.pos,func:a?a.c.func:sl.func,key:a?a.o.key:null,buildId:a?a.c.buildId:'base',x:sl.x,y:sl.y};});
  var banco=[],fora=[],mb=[],mf=[];ocorrencias().forEach(function(o){if(usados[o.id])return;var destino=o.grupo==='elenco'?'fora':'banco',L=destino==='fora'?fora:banco,M=destino==='fora'?mf:mb;L.push(o.key);M.push(metaLista(o,null,destino,L.length-1));});
  m.banco=banco;m.elenco=fora;m.listEntries=m.listEntries&&typeof m.listEntries==='object'?m.listEntries:{};m.listEntries.banco=mb;m.listEntries.fora=mf;delete m.form_lida;
  if(tecId!==undefined)aplicaTecnico(m,tecId);
  validaUnicidadePlano(m);
 }
 function validaPlanoAplicavel(p){
  if(!p||nomesFormacoes().indexOf(String(p.formacao||''))<0)throw new Error('Formação proposta não está mais disponível.');
  var mapa=mapaOcorrencias(),vistosOcorrencia=Object.create(null),vistosJogador=Object.create(null),slots=slotsDaFormacao(p.formacao);
  (p.assign||[]).forEach(function(a){var o=a&&a.o,c=a&&a.c,slot=slots[a&&a.slot],atual=o&&mapa[o.id];if(!o||!atual||String(atual.key)!==String(o.key)||!c||!slot)throw new Error('A proposta ficou desatualizada.');a.o=o=atual;
   if(vistosOcorrencia[o.id]||vistosJogador[uidJogador(o)])throw new Error('A proposta repetiria um jogador.');vistosOcorrencia[o.id]=1;vistosJogador[uidJogador(o)]=1;
   var cand={func:c.func,key:o.key,n:c.n};if(!candidatoCabeNoSlot(cand,o,slot))throw new Error('Uma opção deixou de ser compatível com a vaga.');
   if(String(c.buildId||'base')!=='base'&&!buildSalva(o.cardId,c.buildId))throw new Error('Uma build acessível deixou de existir.');
  });return true;
 }

 /* 4 · MELHOR FORMACAO PRO MEU ELENCO. */
 function initFormacao(){return {resultados:null,escolhida:0,preview:null,feito:null};}
function renderFormacao(st){
  if(!st.resultados)return '<div class="emp-panel"><div class="emp-weak-modebar"><b>MODO A · SUAS BUILDS</b> — testa formações somente com builds Básica, aplicadas ou salvas acessíveis no seu Elenco.</div>'+explicaModoB()+'<p class="emp-sub">Cards são únicos e o cálculo não altera nada.</p><button class="emp-btn" data-emp-action="calcularformacoes">ANALISAR FORMAÇÕES</button></div>';
  if(!st.resultados.length)return estadoVazio('Nenhuma formação disponível.');
  var top=st.resultados.slice(0,6),sel=st.resultados[st.escolhida]||top[0];
  var tabs='<div class="emp-actions">'+top.map(function(p,i){var idx=st.resultados.indexOf(p);return '<button class="emp-btn'+(idx===st.escolhida?' on':'')+'" data-emp-action="escolherformacao" data-index="'+idx+'">'+esc(p.formacao)+' · '+p.preenchidos+'/11</button>';}).join('')+'</div>';
  var p='<div class="emp-panel"><div class="emp-weak-modebar"><b>MODO A · SUAS BUILDS</b> — ordena primeiro por cobertura das 11 vagas e depois pela soma das builds acessíveis.</div>'+explicaModoB()+(sel.globalMelhor?avisoComercial():'')+tabs+'</div><div class="emp-panel"><div class="emp-row"><div><b>'+esc(sel.formacao)+'</b><small class="emp-muted">'+sel.preenchidos+' preenchidas · '+sel.lacunas+' lacuna(s) · ganho '+(sel.ganho>=0?'+':'')+sel.ganho.toFixed(1)+'</small></div><b>'+sel.media.toFixed(1)+'</b></div>'+resumoPlano(sel)+'<div class="emp-actions"><button class="emp-btn" data-emp-action="preverformacao">VER DIFF ANTES DE APLICAR</button></div></div>';
  if(st.preview)p+='<div class="emp-panel emp-preview"><b>Prévia — nenhuma alteração feita</b><p class="emp-sub">Formação: '+esc((modelo()||{}).form||'—')+' → '+esc(st.preview.formacao)+'. A escalação proposta acima é o diff completo; jogadores restantes continuam no Elenco e nenhuma opção bloqueada será usada.</p><div class="emp-actions"><button class="emp-btn" data-emp-action="confirmarformacao">CONFIRMAR APLICAÇÃO</button><button class="emp-btn" data-emp-action="cancelarpreview">CANCELAR</button></div></div>';
  if(st.feito)p+='<div class="emp-panel"><div class="emp-status" style="color:#22c58b">'+esc(st.feito)+'</div></div>';return p;
 }

 /* 5 · DEIXAR O TIME NO IDEAL. Formação, técnico local e builds acessíveis. */
 function initIdeal(){return {resultado:null,preview:null,feito:null};}
 function calculaIdeal(){
  var tecs=tecnicosDisponiveis(),melhor=null;tecs.forEach(function(t){analisaFormacoes(t).forEach(function(p){if(!melhor||p.lacunas<melhor.lacunas||(p.lacunas===melhor.lacunas&&p.score>melhor.score)){melhor=p;melhor.tec=t;}});});return melhor;
 }
 function diffIdeal(p){
  var m=modelo()||{},atual=(m.slots||[]),por=Object.create(null);(p.assign||[]).forEach(function(a){por[a.slot]=a;});
  var linhas=(p.slots||[]).map(function(sl,i){var a=por[i],ant=atual[i]||{},mudou=!a||String(ant.key||'')!==String(a.o.key||'')||!mesmaFunc(ant.func,a.c.func)||String(ant.buildId||'base')!==String(a.c.buildId||'base');
   return '<div class="emp-card"><div class="emp-row"><div><b>'+esc(sl.pos)+' · '+esc(a?nomeOcorrencia(a.o):'vaga')+'</b><small class="emp-muted">'+esc(ant.key?(registro(ant.key)||{}).nome||ant.key:'vazia')+' → '+esc(a?nomeOcorrencia(a.o):'vazia')+'</small></div><b style="color:'+(mudou?'#f0a531':'#8fa4c4')+'">'+(mudou?'ALTERA':'MANTÉM')+'</b></div>'+(a?'<div class="emp-status">'+esc(nomeFunc(a.c.func))+' · build '+esc(a.c.buildId||'base')+' acessível</div>':'')+'</div>';}).join('');
  return '<div class="emp-grid4"><span>Formação<br><b>'+esc(m.form||'—')+' → '+esc(p.formacao)+'</b></span><span>Técnico<br><b>'+esc(tecnicoAtual().nome||'Sem técnico')+' → '+esc(p.tec&&p.tec.nome||'Sem técnico')+'</b></span><span>Vagas preenchidas<br><b>'+p.preenchidos+'/11</b></span><span>Média proposta<br><b>'+p.media.toFixed(1)+'</b></span></div>'+linhas;
 }
 function renderIdeal(st){
  if(!st.resultado)return '<div class="emp-panel"><p class="emp-sub">Síntese segura de formação, titulares, funções, builds acessíveis e técnicos presentes no estado local. Primeiro gera uma proposta; aplicar exige outra confirmação.</p><button class="emp-btn" data-emp-action="calcularideal">GERAR PROPOSTA COMPLETA</button></div>';
  var p=st.resultado,h='<div class="emp-panel"><p class="emp-sub">Default V1 ajustável: maximiza cobertura e depois pontuação acessível, sem consultar builds pagas bloqueadas.</p>'+diffIdeal(p)+'<div class="emp-actions"><button class="emp-btn" data-emp-action="preverideal">VER PRÉVIA FINAL</button></div></div>';
  if(st.preview)h+='<div class="emp-panel emp-preview"><b>Confirmação final — ainda sem mutação</b><p class="emp-sub">Esta aplicação troca formação, escalação, funções/builds acessíveis e técnico em uma única persistência. Cancelar não altera nada.</p><div class="emp-actions"><button class="emp-btn" data-emp-action="confirmarideal">CONFIRMAR TODAS AS ALTERAÇÕES</button><button class="emp-btn" data-emp-action="cancelarpreview">CANCELAR</button></div></div>';
  if(st.feito)h+='<div class="emp-panel"><div class="emp-status" style="color:#22c58b">'+esc(st.feito)+'</div></div>';return h;
 }

 /* 6 · COMPARAR COM OUTRO TIME. V1 sem auth: somente JSON/código local
    sanitizado. Nunca busca time privado nem recebe distribuições de build. */
 var SHARE_SCHEMA='clubefutebol-team-share',SHARE_VERSION=2,SHARE_BASIS='applied-build';
 function initComparar(){return {texto:'',adversario:null,resultado:null,erro:null,codigoLocal:null};}
 function base64Codifica(s){try{return global.btoa(unescape(encodeURIComponent(s)));}catch(e){return '';}}
 function base64Decodifica(s){try{return decodeURIComponent(escape(global.atob(s)));}catch(e){return '';}}
 function exportaTime(){var m=modelo()||{},tit=ocorrencias().filter(function(o){return o.grupo==='titulares';});return {schema:SHARE_SCHEMA,version:SHARE_VERSION,basis:SHARE_BASIS,name:String(m.nome||'Time'),formation:String(m.form||''),slots:tit.slice(0,11).map(function(o){var p=pontuacaoAtual(o);return {position:String(o.sl&&o.sl.pos||''),cardId:String(idCard(o.cardId)),player:String(nomeOcorrencia(o)),score:+numero(p&&p.n).toFixed(1)};})};}
 function codificaTime(obj){return 'CF1.'+base64Codifica(JSON.stringify(obj));}
 function validaTime(obj){
  if(!obj||obj.schema!==SHARE_SCHEMA||+obj.version!==SHARE_VERSION||!Array.isArray(obj.slots))throw new Error('Código/arquivo não segue o formato compartilhável ClubEfootball V1.');
  if(obj.slots.length>11)throw new Error('O time importado tem mais de 11 vagas.');
  var limpos=obj.slots.map(function(x){if(!x||typeof x!=='object')throw new Error('Vaga inválida no arquivo.');var n=x.score,cardId=String(x.cardId||'');if(typeof n!=='number'||!isFinite(n)||n<0||n>999)throw new Error('Pontuação agregada inválida.');if(!/^\d{1,32}$/.test(cardId))throw new Error('card_id ausente ou inválido.');return {position:String(x.position||'').slice(0,12),cardId:cardId,player:String(x.player||'Jogador').slice(0,100),score:+n.toFixed(1)};});
  if(obj.basis!==undefined&&obj.basis!==SHARE_BASIS)throw new Error('A comparação exige resultados de builds aplicadas.');
  return {schema:SHARE_SCHEMA,version:SHARE_VERSION,basis:SHARE_BASIS,name:String(obj.name||'Outro time').slice(0,100),formation:String(obj.formation||'').slice(0,20),slots:limpos};
 }
 function leTime(txt){txt=String(txt||'').trim();if(txt.indexOf('CF1.')===0)txt=base64Decodifica(txt.slice(4));if(!txt)throw new Error('Cole um código ou selecione um arquivo.');return validaTime(JSON.parse(txt));}
 function chavePosicao(v){return String(v||'SEM POSIÇÃO').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase().trim()||'SEM POSIÇÃO';}
 function comparaObjetosTimes(loc,adv){
  var ordem=[],vistos=Object.create(null),aPor=Object.create(null),bPor=Object.create(null);
  function distribui(slots,dest){(slots||[]).forEach(function(x){var k=chavePosicao(x.position);if(!vistos[k]){vistos[k]=1;ordem.push(k);}if(!dest[k])dest[k]=[];dest[k].push(x);});}
  distribui(loc.slots,aPor);distribui(adv.slots,bPor);(adv.slots||[]).forEach(function(x){var k=chavePosicao(x.position);if(!vistos[k]){vistos[k]=1;ordem.push(k);}});
  var v=[],indice=0;ordem.forEach(function(k){var A=aPor[k]||[],B=bPor[k]||[],n=Math.max(A.length,B.length);for(var i=0;i<n;i++){var a=A[i]||null,b=B[i]||null;v.push({i:indice++,position:k,ordinal:i+1,a:a,b:b,d:numero(a&&a.score)-numero(b&&b.score)});}});
  var sa=loc.slots.reduce(function(s,x){return s+x.score;},0),sb=adv.slots.reduce(function(s,x){return s+x.score;},0);return {local:loc,adv:adv,vagas:v,mediaLocal:loc.slots.length?sa/loc.slots.length:0,mediaAdv:adv.slots.length?sb/adv.slots.length:0};
 }
 function globalSuperiorNoTimeLocal(){var ctx={acessiveis:Object.create(null),globais:Object.create(null)};return ocorrencias().filter(function(o){return o.grupo==='titulares';}).some(function(o){var p=pontuacaoAtual(o),limite={c:{n:numero(p&&p.n)}};return globalSuperiorNaVaga([o],o.sl,limite,ctx);});}
 function comparaTimes(adv){var r=comparaObjetosTimes(exportaTime(),adv);r.globalMelhorLocal=globalSuperiorNoTimeLocal();return r;}
function renderComparar(st){
  var entrada='<div class="emp-panel"><div class="emp-weak-modebar"><b>MODO A · BUILDS APLICADAS</b> — compara somente o resultado da build aplicada em cada ocorrência. IDs, nomes ou distribuições das builds não são compartilhados.</div>'+explicaModoB()+'<p class="emp-sub">Sem autenticação, a V1 aceita somente código ou arquivo local no schema sanitizado. Não há busca de times privados.</p><textarea data-emp-input="compare" rows="6" style="width:100%;box-sizing:border-box;margin-top:10px;background:#091018;color:#eef3f7;border:1px solid #26313d;border-radius:9px;padding:10px" placeholder="Cole aqui um código CF1 ou JSON">'+esc(st.texto)+'</textarea><div class="emp-actions" style="margin-top:10px"><label class="emp-btn">IMPORTAR ARQUIVO <input hidden type="file" accept="application/json,.json,.txt" data-emp-change="arquivo"></label><button class="emp-btn" data-emp-action="comparar">VALIDAR E COMPARAR</button><button class="emp-btn" data-emp-action="gerarcodigo">GERAR CÓDIGO DESTE TIME</button></div>'+(st.erro?'<div class="emp-error" style="margin-top:10px">'+esc(st.erro)+'</div>':'')+'</div>';
  if(st.codigoLocal)entrada+='<div class="emp-panel"><b>Código local sanitizado</b><textarea readonly rows="5" style="width:100%;box-sizing:border-box;margin-top:8px;background:#091018;color:#eef3f7;border:1px solid #26313d;border-radius:9px;padding:10px">'+esc(st.codigoLocal)+'</textarea></div>';
  if(!st.resultado)return entrada;
  var r=st.resultado,lin=r.vagas.map(function(x){var a=x.a?'<div class="emp-result-player">'+miniaturaCard(x.a.cardId,'comparar-local-'+x.i)+'<div><b>'+esc(x.a.player)+'</b><small class="emp-muted">Build aplicada · '+x.a.score.toFixed(1)+'</small></div></div>':'vazia';var b=x.b?'<div class="emp-result-player">'+miniaturaCard(x.b.cardId,'comparar-adversario-'+x.i)+'<div><b>'+esc(x.b.player)+'</b><small class="emp-muted">Build aplicada · '+x.b.score.toFixed(1)+'</small></div></div>':'vazia';return '<div class="emp-card"><div class="emp-grid4"><span>Posição<br><b>'+esc(x.position)+(x.ordinal>1?' · '+x.ordinal:'')+'</b></span><span>Seu time<br>'+a+'</span><span>'+esc(r.adv.name)+'<br>'+b+'</span><span>Diferença entre builds<br><b style="color:'+(x.d>=0?'#22c58b':'#e0533d')+'">'+(x.d>=0?'+':'')+x.d.toFixed(1)+'</b></span></div></div>';}).join('');
  return entrada+'<div class="emp-panel">'+(r.globalMelhorLocal?avisoComercial():'')+'<div class="emp-grid4"><span>Seu time<br><b>'+r.mediaLocal.toFixed(1)+'</b></span><span>'+esc(r.adv.name)+'<br><b>'+r.mediaAdv.toFixed(1)+'</b></span><span>Formação local<br><b>'+esc(r.local.formation||'—')+'</b></span><span>Formação importada<br><b>'+esc(r.adv.formation||'—')+'</b></span></div>'+lin+'<div class="emp-status">Comparação somente dos resultados das builds aplicadas, por vaga. Nenhum dado do Elenco foi alterado.</div></div>';
 }
 function serializaEstadoComparar(st){
  var p={versao:SHARE_VERSION,texto:String(st.texto||'').slice(0,24000),erro:st.erro?String(st.erro).slice(0,240):null,codigoLocal:st.codigoLocal?String(st.codigoLocal).slice(0,12000):null};
  if(st.resultado){p.local=clone(st.resultado.local);p.adversario=clone(st.resultado.adv);p.globalMelhorLocal=!!st.resultado.globalMelhorLocal;}return p;
 }
 function restauraEstadoComparar(payload){
  var st=initComparar();if(!payload||payload.versao!==SHARE_VERSION)return st;
  st.texto=String(payload.texto||'').slice(0,24000);st.erro=payload.erro?String(payload.erro).slice(0,240):null;st.codigoLocal=payload.codigoLocal?String(payload.codigoLocal).slice(0,12000):null;
  try{if(payload.local&&payload.adversario){var loc=validaTime(payload.local),adv=validaTime(payload.adversario);st.adversario=adv;st.resultado=comparaObjetosTimes(loc,adv);st.resultado.globalMelhorLocal=!!payload.globalMelhorLocal;}}catch(e){st.adversario=null;st.resultado=null;st.erro='O estado anterior da comparação não era válido.';}return st;
 }
 function salvaEstadoComparar(st){
  try{return !!(global.RouteState&&typeof global.RouteState.savePageState==='function'&&rotaCanonicaEh(ROUTES.comparar)&&global.RouteState.savePageState(serializaEstadoComparar(st)));}catch(e){return false;}
 }
function aplicaEstadoCompararDaEntrada(payload){var st=restauraEstadoComparar(payload);runtime.states[ROUTES.comparar]=st;return st;}
 function mapaOcorrencias(){var m=Object.create(null);ocorrencias().forEach(function(o){m[o.id]=o;});return m;}
 function numeroSeguro(v,max){v=Number(v);return isFinite(v)&&v>=-max&&v<=max?v:null;}
 function empacotaCandidato(x){return x&&x.o&&x.c?{ocorrenciaId:String(x.o.id),func:String(x.c.func||''),n:numero(x.c.n),origem:String(x.c.origem||'acessível').slice(0,20),buildId:String(x.c.buildId||'base').slice(0,100)}:null;}
 function restauraCandidato(x,mapa){if(!x||!mapa[x.ocorrenciaId]||numeroSeguro(x.n,10000)===null)return null;var o=mapa[x.ocorrenciaId];return {o:o,c:{func:String(x.func||''),key:o.key,n:Number(x.n),origem:String(x.origem||'acessível'),buildId:String(x.buildId||'base')}};}
 function empacotaTimeFraco(st){
  var r=st.resultados;if(!r)return {versao:1,visao:st.visao,analisado:false};
  return {versao:1,visao:st.visao,analisado:true,tecnicoId:r.tecnico&&r.tecnico.id,tecnicoNome:r.tecnico&&r.tecnico.nome?String(r.tecnico.nome).slice(0,120):null,
   titulares:(r.titulares||[]).map(function(x,i){return {slot:i,atualId:x.atual&&x.atual.id||null,atualComparavel:empacotaCandidato(x.atual&&x.atualComparavel?{o:x.atual,c:x.atualComparavel}:null),notaAtual:numero(x.notaAtual),alternativa:empacotaCandidato(x.alternativa),diferenca:x.diferenca==null?null:numero(x.diferenca),recomendada:!!x.recomendada,ganho:numero(x.ganho),estado:String(x.estado||''),critica:!!x.critica,globalMelhor:!!x.globalMelhor};}),
   profundidade:(r.profundidade||[]).map(function(x,i){return {slot:i,titularId:x.titular&&x.titular.id||null,titularComparavel:empacotaCandidato(x.titular&&x.titularComparavel?{o:x.titular,c:x.titularComparavel}:null),notaTitular:numero(x.notaTitular),melhor:empacotaCandidato(x.melhor),queda:x.queda==null?null:numero(x.queda),qtdSubstitutos:(x.substitutos||[]).length,estado:String(x.estado||''),globalMelhor:!!x.globalMelhor};})};
 }
 function restauraTimeFraco(payload){
  var st=initTimeFraco();if(!payload||payload.versao!==1)return st;st.visao=payload.visao==='profundidade'?'profundidade':'titulares';if(!payload.analisado)return st;
  var mapa=mapaOcorrencias(),m=modelo(),slots=m&&Array.isArray(m.slots)?m.slots:[];
  st.resultados={tecnico:{id:payload.tecnicoId,nome:payload.tecnicoNome?String(payload.tecnicoNome).slice(0,120):null},
   titulares:(payload.titulares||[]).slice(0,slots.length).map(function(x,i){var atual=x.atualId&&mapa[x.atualId]||null,atualComparavel=restauraCandidato(x.atualComparavel,mapa);return {sl:slots[i]||{},atual:atual,atualComparavel:atualComparavel&&atualComparavel.c||candidatoAtualComparavel(atual,{n:x.notaAtual,func:atual&&atual.funcAtual,compativel:numero(x.notaAtual)>0}),notaAtual:numero(x.notaAtual),alternativa:restauraCandidato(x.alternativa,mapa),diferenca:x.diferenca==null?null:numero(x.diferenca),recomendada:!!x.recomendada,ganho:numero(x.ganho),estado:String(x.estado||''),critica:!!x.critica,globalMelhor:!!x.globalMelhor};}),
   profundidade:(payload.profundidade||[]).slice(0,slots.length).map(function(x,i){var titular=x.titularId&&mapa[x.titularId]||null,titularComparavel=restauraCandidato(x.titularComparavel,mapa),melhor=restauraCandidato(x.melhor,mapa),q=Math.max(0,Math.min(999,Math.floor(numero(x.qtdSubstitutos))));return {sl:slots[i]||{},titular:titular,titularComparavel:titularComparavel&&titularComparavel.c||candidatoAtualComparavel(titular,{n:x.notaTitular,func:titular&&titular.funcAtual,compativel:numero(x.notaTitular)>0}),notaTitular:numero(x.notaTitular),substitutos:new Array(q),melhor:melhor,queda:x.queda==null?null:numero(x.queda),estado:String(x.estado||''),globalMelhor:!!x.globalMelhor};})};return st;
 }
 function empacotaPlano(p){return {formacao:String(p.formacao||''),score:numero(p.score),preenchidos:numero(p.preenchidos),lacunas:numero(p.lacunas),media:numero(p.media),ganho:numero(p.ganho),globalMelhor:!!p.globalMelhor,slots:(p.slots||[]).slice(0,11).map(function(s){return {pos:String(s.pos||''),func:String(s.func||''),x:numero(s.x),y:numero(s.y)};}),assign:(p.assign||[]).slice(0,11).map(function(a){return {slot:numero(a.slot),candidato:empacotaCandidato({o:a.o,c:a.c})};})};}
 function restauraPlano(p,mapa){if(!p||!Array.isArray(p.assign))return null;var formacao=String(p.formacao||''),slots=slotsDaFormacao(formacao);if(!slots.length)return null;var plano={formacao:formacao,score:numero(p.score),preenchidos:numero(p.preenchidos),lacunas:numero(p.lacunas),media:numero(p.media),ganho:numero(p.ganho),globalMelhor:!!p.globalMelhor,slots:slots,assign:[]};p.assign.slice(0,11).forEach(function(a){var c=restauraCandidato(a.candidato,mapa),slot=Math.floor(numero(a.slot));if(c&&slot>=0&&slot<plano.slots.length)plano.assign.push({slot:slot,o:c.o,c:c.c});});return plano;}
 function empacotaFormacao(st){return {versao:1,escolhida:numero(st.escolhida),feito:st.feito?String(st.feito).slice(0,240):null,resultados:st.resultados?(st.resultados||[]).slice(0,6).map(empacotaPlano):null,preview:st.preview?String(st.preview.formacao||''):null};}
 function restauraFormacao(payload){var st=initFormacao();if(!payload||payload.versao!==1)return st;var mapa=mapaOcorrencias();if(Array.isArray(payload.resultados)){st.resultados=payload.resultados.map(function(p){return restauraPlano(p,mapa);}).filter(Boolean);st.escolhida=Math.max(0,Math.min(st.resultados.length-1,Math.floor(numero(payload.escolhida))));if(payload.preview)st.preview=st.resultados.find(function(p){return p.formacao===String(payload.preview);})||null;}st.feito=payload.feito?String(payload.feito).slice(0,240):null;return st;}
 function empacotaTecnico(st){return {versao:1,grupo:st.grupo,selecionadas:idsUnicos(Object.keys(st.selecionadas||{}).filter(function(id){return st.selecionadas[id];})),globalMelhor:!!st.globalMelhor,escolhida:numero(st.escolhida),feito:st.feito?String(st.feito).slice(0,240):null,previewAtivo:!!st.preview,previewId:st.preview&&st.preview.tec?st.preview.tec.id:null,resultados:st.resultados?(st.resultados||[]).map(function(r){return {tecId:r.tec.id,soma:numero(r.soma),media:numero(r.media),ganho:numero(r.ganho),por:(r.por||[]).map(function(x){return {ocorrenciaId:x.o.id,a:numero(x.a),n:numero(x.n),d:numero(x.d)};})};}):null};}
 function restauraTecnico(payload){var st=initTecnico();if(!payload||payload.versao!==1)return st;var mapa=mapaOcorrencias(),permitidos=Object.create(null);tecnicosDisponiveis().forEach(function(t){permitidos[String(t.id)]=t;});st.grupo=grupoSelecaoValido(payload.grupo)?payload.grupo:null;st.globalMelhor=!!payload.globalMelhor;(payload.selecionadas||[]).forEach(function(id){if(mapa[id])st.selecionadas[id]=true;});if(Array.isArray(payload.resultados)){st.resultados=payload.resultados.map(function(r){var t=permitidos[String(r.tecId)];if(!t)return null;return {tec:t,soma:numero(r.soma),media:numero(r.media),ganho:numero(r.ganho),por:(r.por||[]).map(function(x){return mapa[x.ocorrenciaId]?{o:mapa[x.ocorrenciaId],a:numero(x.a),n:numero(x.n),d:numero(x.d)}:null;}).filter(Boolean)};}).filter(Boolean);st.escolhida=Math.max(0,Math.min(st.resultados.length-1,Math.floor(numero(payload.escolhida))));if(payload.previewAtivo)st.preview=st.resultados.find(function(r){return String(r.tec.id)===String(payload.previewId);})||null;}st.feito=payload.feito?String(payload.feito).slice(0,240):null;return st;}
 function salvaEstadoAnalise(route,st){
  var payload=route===ROUTES.timefraco?empacotaTimeFraco(st):(route===ROUTES.formacao?empacotaFormacao(st):(route===ROUTES.tecnico?empacotaTecnico(st):null));
  try{return !!(payload&&global.RouteState&&typeof global.RouteState.savePageState==='function'&&rotaCanonicaEh(route)&&global.RouteState.savePageState(payload));}catch(e){return false;}
 }
 function aplicaEstadoAnaliseDaEntrada(route,payload){var st=route===ROUTES.timefraco?restauraTimeFraco(payload):(route===ROUTES.formacao?restauraFormacao(payload):restauraTecnico(payload));runtime.states[route]=st;return st;}

 var PAGINAS={};
 PAGINAS[ROUTES.melhorfuncao]={init:initMelhorFuncao,render:renderMelhorFuncao};
 PAGINAS[ROUTES.timefraco]={init:initTimeFraco,render:renderTimeFraco};
 PAGINAS[ROUTES.tecnico]={init:initTecnico,render:renderTecnico};
 PAGINAS[ROUTES.formacao]={init:initFormacao,render:renderFormacao};
 PAGINAS[ROUTES.ideal]={init:initIdeal,render:renderIdeal};
 PAGINAS[ROUTES.comparar]={init:initComparar,render:renderComparar};

 function rotaCanonicaEh(route){
  try{return !!(global.RouteState&&typeof global.RouteState.inspect==='function'&&global.RouteState.inspect().atual===route);}catch(e){return false;}
 }
function aoDadosCompletos(){
  runtime.waitingData=false;invalidaIndiceCatalogo();var route=runtime.route,st=runtime.states[route];if(!st||!runtime.root||!rotaCanonicaEh(route))return false;
  var mudou=atualizaRegistros(st.itens);if(route===ROUTES.melhorfuncao&&!mudou)return false;
  return renderAtual();
 }
 function aguardaDadosCompletos(st){
  if(!st||global.ENC_DADOS_COMPLETOS||runtime.waitingData||!(st.itens||[]).some(function(o){return !o.c;})||typeof global.addEventListener!=='function')return false;
  runtime.waitingData=true;global.addEventListener('encaixe:dados-completos',aoDadosCompletos,{once:true});return true;
 }

 function renderAtual(){
  if(!runtime.root||!runtime.route||!PAGINAS[runtime.route])return false;
  try{var p=PAGINAS[runtime.route],st=estadoDaRota(runtime.route,p.init);if(runtime.route===ROUTES.melhorfuncao||runtime.route===ROUTES.timefraco||runtime.route===ROUTES.tecnico)atualizaRegistros(st.itens);var liberada=fixtureSintetica()||runtime.route===ROUTES.melhorfuncao||runtime.route===ROUTES.timefraco||runtime.route===ROUTES.formacao||runtime.route===ROUTES.tecnico||runtime.route===ROUTES.comparar,corpo=liberada?p.render(st):esperaResultadoExterno();runtime.root.innerHTML=paginaShell(runtime.route,corpo);removeMiniaturasDuplicadas(runtime.root);runtime.renders++;return true;}
  catch(e){runtime.lastError=e;runtime.root.innerHTML=paginaShell(runtime.route,'<div class="emp-error">Não foi possível desenhar esta análise. Nenhum dado foi alterado.</div>');return false;}
 }
 function dadosBotao(el){return {group:el&&el.getAttribute('data-group'),view:el&&el.getAttribute('data-view'),index:numero(el&&el.getAttribute('data-index'))};}
 function acaoComum(st,acao,d){if(acaoSelecao(st,acao,d)){renderAtual();return true;}return false;}
 function despachaAcao(acao,d){
  var route=runtime.route,p=PAGINAS[route],st=p&&estadoDaRota(route,p.init);if(!st)return false;runtime.actions++;
  if(acao==='voltar'){if(global.RouteState&&typeof global.RouteState.leavePage==='function')return global.RouteState.leavePage();return false;}
  if(!fixtureSintetica()&&route!==ROUTES.melhorfuncao&&route!==ROUTES.timefraco&&route!==ROUTES.formacao&&route!==ROUTES.tecnico&&route!==ROUTES.comparar)return false;
  if(acaoComum(st,acao,d)){if(route===ROUTES.melhorfuncao)salvaEstadoMelhorFuncao(st);else salvaEstadoAnalise(route,st);return true;}
  if(acao==='cancelarpreview'){st.preview=null;salvaEstadoAnalise(route,st);renderAtual();return true;}
  if(route===ROUTES.melhorfuncao&&acao==='calcular'){
   var qtd=escolhidas(st).length;if(!qtd)return false;
   runtime.externalUserAction++;try{calculaMelhorFuncao(st);runtime.lastExternalUserExecution={origem:'clique-do-usuario-na-maquina-externa',ocorrencias:qtd};}finally{runtime.externalUserAction--;}
   salvaEstadoMelhorFuncao(st);renderAtual();return true;
  }
  if(route===ROUTES.timefraco){
   if(acao==='analisartimefraco'){
    if(st.processando)return false;st.processando=true;st.erro=null;renderAtual();
    proximoCiclo(function(){
     if(runtime.states[route]!==st||!rotaCanonicaEh(route)){st.processando=false;return;}
     runtime.externalUserAction++;try{st.resultados=analisaTimeFraco();runtime.lastExternalUserExecution={origem:'clique-do-usuario-na-maquina-externa',acao:'analisar-time-fraco',ocorrencias:(st.itens||[]).length};}
     catch(e){runtime.lastError=e;st.resultados=null;st.erro='Não foi possível concluir a análise. Nenhum dado foi alterado.';}
     finally{runtime.externalUserAction--;st.processando=false;}
     salvaEstadoAnalise(route,st);if(runtime.states[route]===st&&rotaCanonicaEh(route))renderAtual();
    },0);return true;
   }
   if(acao==='visao'){st.visao=d.view==='profundidade'?'profundidade':'titulares';salvaEstadoAnalise(route,st);renderAtual();return true;}
  }
  if(route===ROUTES.tecnico){
   if(acao==='calcular'){runtime.externalUserAction++;try{calculaTecnicos(st);runtime.lastExternalUserExecution={origem:'clique-do-usuario-na-maquina-externa',acao:'comparar-tecnicos',ocorrencias:escolhidas(st).length};}finally{runtime.externalUserAction--;}salvaEstadoAnalise(route,st);renderAtual();return true;}
   if(acao==='escolhertecnico'){st.escolhida=Math.max(0,Math.min(st.resultados.length-1,d.index));st.preview=null;salvaEstadoAnalise(route,st);renderAtual();return true;}
   if(acao==='prevertecnico'){st.preview=st.resultados&&st.resultados[st.escolhida]||null;salvaEstadoAnalise(route,st);renderAtual();return true;}
   if(acao==='confirmartecnico'&&st.preview){var idTec=st.preview.tec.id,disponivel=tecnicosDisponiveis().some(function(t){return String(t.id)===String(idTec);});var rt=disponivel?transacao(function(m){aplicaTecnico(m,idTec);}):{ok:false,erro:'Nada foi alterado. Esse técnico não está mais disponível no seu estado local.'};st.preview=null;st.feito=rt.ok?'Técnico aplicado em uma única persistência.':rt.erro;salvaEstadoAnalise(route,st);renderAtual();return rt.ok;}
  }
  if(route===ROUTES.formacao){
   if(acao==='calcularformacoes'){runtime.externalUserAction++;try{st.resultados=analisaFormacoes(tecnicoAtual()).slice(0,6);runtime.lastExternalUserExecution={origem:'clique-do-usuario-na-maquina-externa',acao:'analisar-formacoes',ocorrencias:ocorrencias().length};}finally{runtime.externalUserAction--;}st.escolhida=0;st.preview=null;salvaEstadoAnalise(route,st);renderAtual();return true;}
   if(acao==='escolherformacao'){st.escolhida=Math.max(0,Math.min(st.resultados.length-1,d.index));st.preview=null;salvaEstadoAnalise(route,st);renderAtual();return true;}
   if(acao==='preverformacao'){st.preview=st.resultados[st.escolhida]||null;salvaEstadoAnalise(route,st);renderAtual();return true;}
   if(acao==='confirmarformacao'&&st.preview){var rf=transacao(function(m){aplicaPlano(m,st.preview);});st.preview=null;st.feito=rf.ok?'Formação e escalação aplicadas em uma única persistência.':rf.erro;salvaEstadoAnalise(route,st);renderAtual();return rf.ok;}
  }
  if(route===ROUTES.ideal){
   if(acao==='calcularideal'){st.resultado=calculaIdeal();st.preview=null;renderAtual();return true;}
   if(acao==='preverideal'&&st.resultado){st.preview=st.resultado;renderAtual();return true;}
   if(acao==='confirmarideal'&&st.preview){var ri=transacao(function(m){aplicaPlano(m,st.preview,st.preview.tec&&st.preview.tec.id);});st.preview=null;st.feito=ri.ok?'Proposta completa aplicada em uma única persistência.':ri.erro;renderAtual();return ri.ok;}
  }
  if(route===ROUTES.comparar){
   if(acao==='comparar'){runtime.externalUserAction++;try{st.adversario=leTime(st.texto);st.resultado=comparaTimes(st.adversario);st.erro=null;runtime.lastExternalUserExecution={origem:'clique-do-usuario-na-maquina-externa',acao:'comparar-times',ocorrencias:(st.resultado.local.slots||[]).length};}catch(e){st.resultado=null;st.erro=e&&e.message||'Arquivo inválido.';}finally{runtime.externalUserAction--;}salvaEstadoComparar(st);renderAtual();return !st.erro;}
   if(acao==='gerarcodigo'){runtime.externalUserAction++;try{st.codigoLocal=codificaTime(exportaTime());runtime.lastExternalUserExecution={origem:'clique-do-usuario-na-maquina-externa',acao:'gerar-codigo-time',ocorrencias:ocorrencias().filter(function(o){return o.grupo==='titulares';}).length};}finally{runtime.externalUserAction--;}st.erro=st.codigoLocal?null:'Não foi possível gerar o código local.';salvaEstadoComparar(st);renderAtual();return !!st.codigoLocal;}
  }
  return false;
 }
 function aoClique(ev){var el=ev.target&&ev.target.closest?ev.target.closest('[data-emp-action]'):null;if(!el||!runtime.root.contains(el))return;ev.preventDefault();despachaAcao(el.getAttribute('data-emp-action'),dadosBotao(el));}
 function aoInput(ev){var el=ev.target;if(!el||el.getAttribute('data-emp-input')!=='compare'||runtime.route!==ROUTES.comparar)return;var st=estadoDaRota(runtime.route,initComparar);st.texto=el.value||'';salvaEstadoComparar(st);}
 function aoMudanca(ev){
  var el=ev.target;if(!el)return;
  if(el.getAttribute('data-emp-change')==='ocorrencia'){var p=PAGINAS[runtime.route],st=estadoDaRota(runtime.route,p.init);st.selecionadas[el.getAttribute('data-id')]=!!el.checked;st.resultados=null;if(runtime.route===ROUTES.melhorfuncao)salvaEstadoMelhorFuncao(st);else salvaEstadoAnalise(runtime.route,st);atualizaContador(runtime.root,st);return;}
  if(el.getAttribute('data-emp-change')==='arquivo'&&runtime.route===ROUTES.comparar){var f=el.files&&el.files[0],sc=estadoDaRota(runtime.route,initComparar);if(!f)return;if(f.size>262144){sc.erro='Arquivo maior que 256 KB.';salvaEstadoComparar(sc);renderAtual();return;}var leitor=new FileReader();leitor.onload=function(){sc.texto=String(leitor.result||'');sc.erro=null;salvaEstadoComparar(sc);renderAtual();};leitor.onerror=function(){sc.erro='Não foi possível ler o arquivo local.';salvaEstadoComparar(sc);renderAtual();};leitor.readAsText(f);}
 }
 function mount(route,root){
  route=String(route||'');if(!PAGINAS[route]||!root)return false;garanteEstilo();
  if(runtime.root)unmount(runtime.root);runtime.root=root;runtime.route=route;
  root.onclick=aoClique;root.oninput=aoInput;root.onchange=aoMudanca;var ok=renderAtual();if(route===ROUTES.melhorfuncao||route===ROUTES.timefraco||route===ROUTES.tecnico)aguardaDadosCompletos(runtime.states[route]);return ok;
 }
 function unmount(root){root=root||runtime.root;if(!root)return false;root.onclick=null;root.oninput=null;root.onchange=null;if(root===runtime.root){runtime.root=null;runtime.route=null;}return true;}
 function montaPaginaCanonica(route,options){
  if(typeof document==='undefined')return false;var base=document.getElementById('homewrap'),elenco=document.getElementById('mtwrap');if(!base||!elenco)return false;
  if(route===ROUTES.melhorfuncao&&options&&typeof options==='object')aplicaEstadoDaEntrada(route,options.pageState||null);
  if((route===ROUTES.timefraco||route===ROUTES.formacao||route===ROUTES.tecnico)&&options&&typeof options==='object')aplicaEstadoAnaliseDaEntrada(route,options.pageState||null);
  if(route===ROUTES.comparar&&options&&typeof options==='object')aplicaEstadoCompararDaEntrada(options.pageState||null);
  try{document.documentElement.classList.remove('t6ranking');document.documentElement.classList.add('t6elenco');}catch(e){}
  if(runtime.root)unmount(runtime.root);
  elenco.style.display='none';['mline','out'].forEach(function(id){var el=document.getElementById(id);if(el)el.style.display='none';});
  base.style.display='block';base.innerHTML='<div id="t6ModuloElencoPage"></div>';var host=document.getElementById('t6ModuloElencoPage');return mount(route,host);
 }
 function inspect(){return {route:runtime.route,renders:runtime.renders,actions:runtime.actions,waitingData:runtime.waitingData,fixtureSintetica:fixtureSintetica(),maxRealTestRows:20,lastControlledTest:clone(runtime.lastControlledTest),lastExternalUserExecution:clone(runtime.lastExternalUserExecution),execucaoProducao:'externa-pelo-usuario',lastError:runtime.lastError?String(runtime.lastError.message||runtime.lastError):null,registeredRoutes:Object.keys(PAGINAS),stateRoutes:Object.keys(runtime.states)};}
 var api=Object.freeze({routes:ROUTES,titles:Object.freeze(TITULOS),mount:mount,unmount:unmount,render:renderAtual,inspect:inspect,
  _test:Object.freeze({ocorrencias:ocorrencias,candidatosAcessiveis:candidatosAcessiveis,analisaTimeFraco:analisaTimeFraco,analiseTitulares:analiseTitulares,analiseProfundidade:analiseProfundidade,
   tecnicosDisponiveis:tecnicosDisponiveis,resolveFormacao:resolveFormacao,analisaFormacoes:analisaFormacoes,validaPlanoAplicavel:validaPlanoAplicavel,aplicaPlano:aplicaPlano,calculaIdeal:calculaIdeal,validaTime:validaTime,exportaTime:exportaTime,comparaTimes:comparaTimes,transacao:transacao,controlaTesteReal:controlaTesteReal})});
 global.ElencoModulePages=api;

 /* Rotas expostas somente após a respectiva especificação e validação. */
 global.T6_ROUTE_DEFINITIONS=global.T6_ROUTE_DEFINITIONS||{};
 global.T6_ROUTE_DEFINITIONS.melhorfuncao={returnRoute:'meutime',render:function(route,options){return montaPaginaCanonica(ROUTES.melhorfuncao,options||{});}};
 global.T6_ROUTE_DEFINITIONS.timefraco={returnRoute:'meutime',render:function(route,options){return montaPaginaCanonica(ROUTES.timefraco,options||{});}};
 global.T6_ROUTE_DEFINITIONS.melhorformacao={returnRoute:'meutime',render:function(route,options){return montaPaginaCanonica(ROUTES.formacao,options||{});}};
 global.T6_ROUTE_DEFINITIONS.tecnicotime={returnRoute:'meutime',render:function(route,options){return montaPaginaCanonica(ROUTES.tecnico,options||{});}};
 global.T6_ROUTE_DEFINITIONS.comparartime={returnRoute:'meutime',render:function(route,options){return montaPaginaCanonica(ROUTES.comparar,options||{});}};
})(window);
