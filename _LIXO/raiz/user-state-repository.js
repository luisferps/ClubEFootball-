/* USER_STATE_REPOSITORY_V2
   Contrato único do estado do usuário. Nesta fase o adapter padrão continua
   local e nenhum código conecta, autentica ou escreve no Supabase. */
(function instalaUserStateRepository(global){
 'use strict';
 if(global.UserStateRepository && global.LocalStorageAdapter) return;

 var STATE_VERSION=2;
 var SCHEMA_REVISION=2;
 var KEY_V1='MT_v1';
 var KEY_V2='CLUBEFOOTBALL_USER_STATE_V2';
 var KEY_TXN='CLUBEFOOTBALL_USER_STATE_TXN_V2';

 function clone(v){
  if(v===undefined) return undefined;
  return JSON.parse(JSON.stringify(v));
 }
 function objeto(v){ return !!v && typeof v==='object' && !Array.isArray(v); }
 function canonico(v){
  if(Array.isArray(v)) return '['+v.map(canonico).join(',')+']';
  if(objeto(v)) return '{'+Object.keys(v).sort().map(function(k){
   return JSON.stringify(k)+':'+canonico(v[k]);
  }).join(',')+'}';
  return JSON.stringify(v);
 }
 function hashCurto(v){
  var s=typeof v==='string'?v:canonico(v),h=2166136261;
  for(var i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619);}
  return ('00000000'+(h>>>0).toString(16)).slice(-8);
 }
 function cardBase(k){ return String(k||'').split('|')[0].split('@')[0]; }
 function funcaoDaChave(k){
  var p=String(k||'').split('|');return p.length>1?p.slice(1).join('|'):null;
 }
 function idMigrado(prefix,semente,usados){
  var base=prefix+'_migrated_'+hashCurto(semente),id=base,n=1;
  while(usados[id]) id=base+'_'+(++n);
  usados[id]=1; return id;
 }
 function notaValida(v){v=Number(v);return isFinite(v)?v:null;}
 function registroBuild(cardId,b,indice,usados){
  b=clone(b||{});var id=typeof b.buildId==='string'&&b.buildId.trim()?b.buildId.trim():null;
  if(!id||usados[id])id=idMigrado('bld',cardId+'|'+indice+'|'+canonico(b),usados);
  else usados[id]=1;
  b.buildId=id;
  return {buildId:id,cardId:String(cardId),functionId:b.func==null?null:String(b.func),
   name:b.nome==null?null:String(b.nome),photo:b,finalScore:notaValida(b.n),
   createdAt:b.createdAt||null,updatedAt:b.updatedAt||null};
 }
 function prefereBuildId(lista,raw){
  if(raw==='base')return 'base';
  if(typeof raw==='string'){
   for(var i=0;i<lista.length;i++)if(lista[i].buildId===raw)return raw;
  }
  var n=Number(raw);return Number.isInteger(n)&&lista[n]?lista[n].buildId:'base';
 }
 function entradaColecao(bruto,cardKey,colecao,teamId,ocorrencia,usados,buildsById){
  var e=objeto(bruto)?clone(bruto):{},id=typeof e.entryId==='string'&&e.entryId.trim()?e.entryId.trim():null;
  cardKey=String(cardKey==null?(e.cardKey||''):cardKey);
  if(!id||usados[id])id=idMigrado('entry',teamId+'|'+colecao+'|'+cardKey+'|'+ocorrencia,usados);
  else usados[id]=1;
  var buildId=typeof e.buildId==='string'&&e.buildId.trim()?e.buildId.trim():'base';
  if(buildId!=='base'&&!buildsById[buildId])buildId='base';
  e.entryId=id;e.collection=colecao;e.cardId=cardBase(cardKey)||null;e.cardKey=cardKey;
  e.functionId=e.functionId==null?funcaoDaChave(cardKey):String(e.functionId);
  e.buildId=buildId;
  return e;
 }
 function normalizaColecoes(teamId,banco,fora,meta,buildsById,usadosGlobais){
  banco=Array.isArray(banco)?banco:[];fora=Array.isArray(fora)?fora:[];meta=objeto(meta)?meta:{};
  var pool=[],usadosLocais={},ocorrencias={};
  ['banco','fora'].forEach(function(c){
   var a=Array.isArray(meta[c])?meta[c]:[];
   a.forEach(function(e,i){pool.push({raw:e,collection:c,index:i,used:false});});
  });
  function chaveDe(v){return objeto(v)?String(v.cardKey||''):String(v||'');}
  function acha(cardKey,colecao,indice){
   var i,p;
   for(i=0;i<pool.length;i++){p=pool[i];if(!p.used&&p.collection===colecao&&p.index===indice&&chaveDe(p.raw)===cardKey){p.used=true;return p.raw;}}
   for(i=0;i<pool.length;i++){p=pool[i];if(!p.used&&p.collection===colecao&&chaveDe(p.raw)===cardKey){p.used=true;return p.raw;}}
   for(i=0;i<pool.length;i++){p=pool[i];if(!p.used&&chaveDe(p.raw)===cardKey){p.used=true;return p.raw;}}
   return null;
  }
  function monta(lista,colecao){
   return lista.map(function(item,i){
    var cardKey=chaveDe(item),raw=objeto(item)?item:acha(cardKey,colecao,i);
    var chave=colecao+'|'+cardKey,oc=ocorrencias[chave]||0;ocorrencias[chave]=oc+1;
    var e=entradaColecao(raw,cardKey,colecao,teamId,oc,usadosGlobais,buildsById);
    usadosLocais[e.entryId]=1;return e;
   });
  }
  return {banco:monta(banco,'banco'),fora:monta(fora,'fora')};
 }
 function normalizaV2(v2){
  v2=clone(v2||{});v2.stateVersion=STATE_VERSION;v2.schemaRevision=SCHEMA_REVISION;
  v2.builds=objeto(v2.builds)?v2.builds:{byId:{},orderByCard:{}};
  v2.builds.byId=objeto(v2.builds.byId)?v2.builds.byId:{};
  v2.teams=objeto(v2.teams)?v2.teams:{byId:{},order:[]};
  v2.teams.byId=objeto(v2.teams.byId)?v2.teams.byId:{};
  var usados={};
  Object.keys(v2.teams.byId).forEach(function(teamId){
   var t=v2.teams.byId[teamId]||{},c=normalizaColecoes(teamId,t.bench,t.reserves,
    {banco:t.bench,fora:t.reserves},v2.builds.byId,usados);
   t.bench=c.banco;t.reserves=c.fora;v2.teams.byId[teamId]=t;
  });
  return v2;
 }
 function migraV1(v1,ownerId){
  v1=clone(v1||{});var byId={},orderByCard={},usados={},buildOnRaw=clone(v1.buildOn||{});
  Object.keys(v1.builds||{}).forEach(function(cardId){
   var lista=Array.isArray(v1.builds[cardId])?v1.builds[cardId]:[];
   orderByCard[cardId]=[];
   lista.forEach(function(b,i){var r=registroBuild(cardId,b,i,usados);byId[r.buildId]=r;orderByCard[cardId].push(r.buildId);});
  });
  var pref={};Object.keys(buildOnRaw).forEach(function(cardId){
   pref[cardId]=prefereBuildId((orderByCard[cardId]||[]).map(function(id){return byId[id];}),buildOnRaw[cardId]);
  });
  var slotsById={},slotOrder=[],slotsUsados={},inventario=[],vistos={};
  function inventaria(k){var id=cardBase(k);if(!id||vistos[id])return;vistos[id]=1;inventario.push({cardId:id,cardKey:String(k)});}
  (v1.slots||[]).forEach(function(sl,i){
   sl=clone(sl||{});var slotId=typeof sl.slotId==='string'&&sl.slotId.trim()?sl.slotId.trim():null;
   if(!slotId||slotsUsados[slotId]){
    slotId='slot_'+(i+1);var sufixo=1,baseSlot=slotId;
    while(slotsUsados[slotId])slotId=baseSlot+'_'+(++sufixo);
    slotsUsados[slotId]=1;
   }else slotsUsados[slotId]=1;
   var cardId=cardBase(sl.key),buildId=sl.buildId||pref[cardId]||'base';
   if(buildId!=='base'&&!byId[buildId])buildId='base';
   sl.buildId=buildId;
   slotsById[slotId]={slotId:slotId,cardId:cardId||null,cardKey:sl.key==null?null:String(sl.key),
    pos:sl.pos==null?null:String(sl.pos),x:sl.x==null?null:Number(sl.x),y:sl.y==null?null:Number(sl.y),
    functionId:sl.func==null?null:String(sl.func),buildId:buildId,photo:sl};
   slotOrder.push(slotId);inventaria(sl.key);
  });
  (v1.banco||[]).forEach(inventaria);(v1.elenco||[]).forEach(inventaria);
  var conhecidos={form:1,slots:1,banco:1,elenco:1,listEntries:1,nome:1,builds:1,buildOn:1},extras={};
  Object.keys(v1).forEach(function(k){if(!conhecidos[k])extras[k]=clone(v1[k]);});
  var teamId='team_default',entradas=normalizaColecoes(teamId,v1.banco,v1.elenco,v1.listEntries,byId,{});
  return {stateVersion:STATE_VERSION,schemaRevision:SCHEMA_REVISION,ownerId:ownerId==null?null:String(ownerId),
   inventory:{cards:inventario},builds:{byId:byId,orderByCard:orderByCard},
   teams:{byId:(function(){var o={};o[teamId]={teamId:teamId,name:v1.nome||'Meu time',
    formation:v1.form||'4-3-3',slots:{byId:slotsById,order:slotOrder},
    bench:entradas.banco,reserves:entradas.fora};return o;})(),order:[teamId]},
   activeTeamId:teamId,preferences:{fichaBuildByCard:pref},
   compatibility:{rootExtras:extras,buildOnRaw:buildOnRaw}};
 }
 function paraV1(v2){
  validaV2(v2);var comp=v2.compatibility||{},out=clone(comp.rootExtras||{}),
   teamId=v2.activeTeamId||(v2.teams.order||[])[0],team=(v2.teams.byId||{})[teamId]||{},
   byId=v2.builds.byId||{},ord=v2.builds.orderByCard||{};
  out.form=team.formation||'4-3-3';out.nome=team.name||'Meu time';out.slots=[];
  ((team.slots&&team.slots.order)||[]).forEach(function(slotId){
   var s=team.slots.byId[slotId];if(!s)return;var x=clone(s.photo||{});
   if(s.cardKey!=null)x.key=s.cardKey;if(s.pos!=null)x.pos=s.pos;
   if(s.x!=null)x.x=s.x;if(s.y!=null)x.y=s.y;if(s.functionId!=null)x.func=s.functionId;
   x.buildId=s.buildId||'base';out.slots.push(x);
  });
  out.banco=(team.bench||[]).map(function(e){return String(e&&e.cardKey||'');});
  out.elenco=(team.reserves||[]).map(function(e){return String(e&&e.cardKey||'');});
  out.listEntries={banco:clone(team.bench||[]),fora:clone(team.reserves||[])};
  out.builds={};out.buildOn={};
  Object.keys(ord).forEach(function(cardId){
   out.builds[cardId]=ord[cardId].map(function(id){
    var r=byId[id],b=clone(r&&r.photo||{});if(!r)return b;
    b.buildId=r.buildId;if(r.functionId!=null)b.func=r.functionId;if(r.name!=null)b.nome=r.name;
    if(r.finalScore!=null)b.n=r.finalScore;
    if(r.createdAt!=null)b.createdAt=r.createdAt;if(r.updatedAt!=null)b.updatedAt=r.updatedAt;
    return b;
   });
   var p=v2.preferences&&v2.preferences.fichaBuildByCard&&v2.preferences.fichaBuildByCard[cardId];
   out.buildOn[cardId]=p==='base'?'base':Math.max(0,ord[cardId].indexOf(p));
  });
  Object.keys(comp.buildOnRaw||{}).forEach(function(cardId){
   if(!Object.prototype.hasOwnProperty.call(out.buildOn,cardId))out.buildOn[cardId]=clone(comp.buildOnRaw[cardId]);
  });
  return out;
 }
 function validaV2(v){
  if(!objeto(v) || +v.stateVersion!==STATE_VERSION || +v.schemaRevision!==SCHEMA_REVISION)
   throw new Error('UserStateV2 invalido');
  if(!objeto(v.inventory) || !objeto(v.builds) || !objeto(v.teams))
   throw new Error('UserStateV2 incompleto');
  var vistos={};Object.keys(v.builds.byId||{}).forEach(function(id){
   if(vistos[id])throw new Error('buildId duplicado');vistos[id]=1;
   if((v.builds.byId[id]||{}).buildId!==id)throw new Error('buildId inconsistente');
  });
  Object.keys(v.builds.orderByCard||{}).forEach(function(cardId){
   (v.builds.orderByCard[cardId]||[]).forEach(function(id){if(!vistos[id])throw new Error('ordem aponta build ausente');});
  });
  var entradas={};Object.keys(v.teams.byId||{}).forEach(function(teamId){
   var t=v.teams.byId[teamId]||{};
   ['bench','reserves'].forEach(function(campo){
    if(!Array.isArray(t[campo]))throw new Error('colecao de elenco invalida');
    t[campo].forEach(function(e){
     if(!objeto(e)||!e.entryId||!e.cardKey)throw new Error('entrada de elenco invalida');
     if(entradas[e.entryId])throw new Error('entryId duplicado');entradas[e.entryId]=1;
     if(e.buildId!=='base'&&!vistos[e.buildId])throw new Error('entrada aponta build ausente');
    });
   });
  });
  return true;
 }

 function MemoryStateAdapter(semente){
  this._raw=semente?clone(semente):{v1:null,v2:null};
  this.kind='memory';
 }
 MemoryStateAdapter.prototype.load=function(){ return clone(this._raw); };
 MemoryStateAdapter.prototype.commit=function(par){
  this._raw={v1:clone(par.v1),v2:clone(par.v2)}; return true;
 };
 MemoryStateAdapter.prototype.inspect=function(){ return clone(this._raw); };

function LocalStorageAdapter(storage,opcoes){
  if(!storage || typeof storage.getItem!=='function' || typeof storage.setItem!=='function' ||
     typeof storage.removeItem!=='function')
   throw new Error('storage local indisponivel');
  opcoes=opcoes||{};
  this.storage=storage;
  this.keyV1=opcoes.keyV1||KEY_V1;
  this.keyV2=opcoes.keyV2||KEY_V2;
  this.keyTxn=opcoes.keyTxn||KEY_TXN;
  this.kind='localStorage';
 }
 LocalStorageAdapter.prototype._le=function(k){
  var r=this.storage.getItem(k); if(!r) return null;
  try{return JSON.parse(r);}catch(e){throw new Error('JSON local invalido em '+k);}
 };
 LocalStorageAdapter.prototype._aplicaRaw=function(par){
  var self=this;
  [{key:this.keyV2,valor:par.v2},{key:this.keyV1,valor:par.v1}].forEach(function(x){
   if(x.valor==null)self.storage.removeItem(x.key);else self.storage.setItem(x.key,String(x.valor));
  });
 };
 LocalStorageAdapter.prototype.recover=function(){
  var bruto=this.storage.getItem(this.keyTxn);if(!bruto)return false;
  var txn;try{txn=JSON.parse(bruto);}catch(e){throw new Error('diario local invalido');}
  this._aplicaRaw(txn.phase==='committed'?txn.next:txn.previous);
  this.storage.removeItem(this.keyTxn);return true;
 };
 LocalStorageAdapter.prototype.load=function(){
  this.recover();
  return {v1:this._le(this.keyV1),v2:this._le(this.keyV2)};
 };
 LocalStorageAdapter.prototype.commit=function(par){
  this.recover();
  var anterior={v1:this.storage.getItem(this.keyV1),v2:this.storage.getItem(this.keyV2)};
  var proximo={v1:JSON.stringify(par.v1),v2:JSON.stringify(par.v2)};
  var txn={version:1,phase:'prepared',previous:anterior,next:proximo};
  this.storage.setItem(this.keyTxn,JSON.stringify(txn));
  try{
   this._aplicaRaw(proximo);
   txn.phase='committed';this.storage.setItem(this.keyTxn,JSON.stringify(txn));
   this.storage.removeItem(this.keyTxn);return true;
  }catch(e){
   try{this._aplicaRaw(anterior);this.storage.removeItem(this.keyTxn);}catch(rollbackErro){}
   throw e;
  }
 };

 function UserStateRepository(adapter,opcoes){
  if(!adapter || typeof adapter.load!=='function' || typeof adapter.commit!=='function')
   throw new Error('adapter do UserStateRepository invalido');
  this.adapter=adapter;
  this.ownerId=opcoes&&opcoes.ownerId!=null?String(opcoes.ownerId):null;
  this._state=null;
 }
 UserStateRepository.prototype.migrate=function(entrada){
  if(objeto(entrada) && +entrada.stateVersion===STATE_VERSION){
   var atualizado=normalizaV2(entrada);validaV2(atualizado);return atualizado;
  }
  var v2=migraV1(entrada,this.ownerId);validaV2(v2);return v2;
 };
 UserStateRepository.prototype.toLegacy=function(estado){ return paraV1(estado||this._state); };
 UserStateRepository.prototype.load=function(padraoV1){
  var raw=this.adapter.load(), origem=raw&&(raw.v2||raw.v1);
  if(!origem && padraoV1!==undefined)origem=padraoV1;
  if(!origem) return null;
  this._state=this.migrate(origem); return clone(this._state);
 };
 UserStateRepository.prototype.loadLegacy=function(padraoV1){
  var v2=this.load(padraoV1);return v2?paraV1(v2):clone(padraoV1||{});
 };
 UserStateRepository.prototype.save=function(estado){
  var v2=this.migrate(estado);
  this.adapter.commit({v2:v2,v1:paraV1(v2)});
  this._state=v2; return clone(v2);
 };
 UserStateRepository.prototype.saveLegacy=function(v1){ return this.save(this.migrate(v1)); };
 UserStateRepository.prototype.getState=function(){ return clone(this._state); };
 UserStateRepository.prototype.adapterKind=function(){ return this.adapter.kind||'custom'; };
 UserStateRepository.prototype.export=function(estado){
  var v2=this.migrate(estado||this._state);return JSON.stringify(v2);
 };
 UserStateRepository.prototype.import=function(payload,opcoes){
  var valor=typeof payload==='string'?JSON.parse(payload):clone(payload),v2=this.migrate(valor);
  if(!opcoes||opcoes.persist!==false)this.save(v2);else this._state=clone(v2);
  return clone(v2);
 };
 UserStateRepository.prototype.roundTrip=function(entrada){
  var v2=this.migrate(entrada),texto=JSON.stringify(v2),importado=this.migrate(JSON.parse(texto));
  return {v2:v2,exported:texto,imported:importado,legacy:paraV1(importado)};
 };
 UserStateRepository.prototype.transaction=function(mutador){
  var atual=this._state||this.load();if(!atual)throw new Error('estado nao carregado');
  var draft=clone(atual),resultado=mutador(draft);this.save(draft);return resultado;
 };
 UserStateRepository.prototype._edita=function(mutador){ return this.transaction(mutador); };
 UserStateRepository.prototype.createBuild=function(cardId,foto){
  var self=this;return this._edita(function(s){
   cardId=String(cardId);foto=clone(foto||{});var usados={};Object.keys(s.builds.byId).forEach(function(id){usados[id]=1;});
   var id=typeof foto.buildId==='string'&&foto.buildId.trim()?foto.buildId.trim():null;
   if(!id||usados[id]){
    var token='';try{if(global.crypto&&global.crypto.randomUUID)token=global.crypto.randomUUID();}catch(e){}
    id=token?'bld_'+token.toLowerCase():idMigrado('bld_runtime',cardId+'|'+Date.now()+'|'+canonico(foto),usados);
   }
   foto.buildId=id;var r=registroBuild(cardId,foto,(s.builds.orderByCard[cardId]||[]).length,{});
   r.buildId=id;r.photo.buildId=id;s.builds.byId[id]=r;(s.builds.orderByCard[cardId]||(s.builds.orderByCard[cardId]=[])).push(id);
   return id;
  });
 };
 UserStateRepository.prototype.updateBuild=function(buildId,mudancas){
  return this._edita(function(s){var r=s.builds.byId[buildId];if(!r)throw new Error('build ausente');
   var foto=clone(r.photo||{}),m=clone(mudancas||{});Object.keys(m).forEach(function(k){foto[k]=m[k];});
   foto.buildId=buildId;r.photo=foto;r.functionId=foto.func==null?r.functionId:String(foto.func);
   r.name=foto.nome==null?r.name:String(foto.nome);r.finalScore=notaValida(foto.n);r.updatedAt=foto.updatedAt||r.updatedAt;
   return buildId;});
 };
 UserStateRepository.prototype.deleteBuild=function(buildId){
  return this._edita(function(s){var r=s.builds.byId[buildId];if(!r)return false;
   delete s.builds.byId[buildId];var o=s.builds.orderByCard[r.cardId]||[],i=o.indexOf(buildId);if(i>=0)o.splice(i,1);
   Object.keys(s.teams.byId).forEach(function(tid){var slots=s.teams.byId[tid].slots;
    (slots.order||[]).forEach(function(sid){if(slots.byId[sid].buildId===buildId)slots.byId[sid].buildId='base';});
    ['bench','reserves'].forEach(function(campo){(s.teams.byId[tid][campo]||[]).forEach(function(e){
     if(e.buildId===buildId)e.buildId='base';
    });});});
   if(s.preferences.fichaBuildByCard[r.cardId]===buildId)s.preferences.fichaBuildByCard[r.cardId]='base';return true;});
 };
 UserStateRepository.prototype.assignBuildToSlot=function(teamId,slotId,buildId){
  return this._edita(function(s){var t=s.teams.byId[teamId],sl=t&&t.slots.byId[slotId];if(!sl)throw new Error('slot ausente');
   if(buildId!=='base'&&!s.builds.byId[buildId])throw new Error('build ausente');sl.buildId=buildId;return true;});
 };
 UserStateRepository.prototype.assignBuildToCollectionEntry=function(teamId,collection,entryId,buildId){
  return this._edita(function(s){
   var t=s.teams.byId[teamId],campo=collection==='banco'?'bench':(collection==='fora'?'reserves':null);
   if(!t||!campo)throw new Error('colecao ausente');
   var e=(t[campo]||[]).filter(function(x){return x.entryId===entryId;})[0];
   if(!e)throw new Error('entrada ausente');
   if(buildId!=='base'&&!s.builds.byId[buildId])throw new Error('build ausente');
   e.buildId=buildId;return true;
  });
 };

 global.UserStateRepositoryClass=UserStateRepository;
 global.LocalStorageAdapter=LocalStorageAdapter;
 global.MemoryStateAdapter=MemoryStateAdapter;
 global.UserStateContract=Object.freeze({stateVersion:STATE_VERSION,schemaRevision:SCHEMA_REVISION,
  keyV1:KEY_V1,keyV2:KEY_V2,keyTxn:KEY_TXN});

 /* Instalação sem leitura: carregar este arquivo não toca o navegador. */
 if(global.localStorage){
  global.UserStateRepository=new UserStateRepository(new LocalStorageAdapter(global.localStorage),{ownerId:null});
 }
})(typeof window!=='undefined'?window:this);
