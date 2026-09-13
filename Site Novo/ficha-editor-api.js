(function () {
  "use strict";
  // Só transporte e autenticação. Nenhuma fórmula ou régua é enviada ao cliente.
  var storageKey = "clubefut.editor.session.v1";
  var session = null, refreshing = null;
  try { session = JSON.parse(sessionStorage.getItem(storageKey) || "null"); } catch (_) {}
  function remember(value) {
    var previousUser=session&&session.user&&session.user.id;
    session = value;
    try { if (value) sessionStorage.setItem(storageKey, JSON.stringify(value)); else sessionStorage.removeItem(storageKey); } catch (_) {}
    if(previousUser!==(value&&value.user&&value.user.id))window.dispatchEvent(new CustomEvent("ficha-account-changed"));
  }
  function request(path,body,token,signal) {
    return window.SiteNovoCommon.request(path,body,{token,signal,timeout:15000});
  }
  async function access() {
    if (!session || !session.access_token) throw new Error("Entre na sua conta para continuar. O rascunho será mantido.");
    if (session.expires_at * 1000 > Date.now() + 45000) return session.access_token;
    if (!refreshing) refreshing = request("/auth/v1/token?grant_type=refresh_token", { refresh_token: session.refresh_token })
      .then(function (data) { remember(data); return data.access_token; })
      .catch(function (error) { if (error.status === 400 || error.status === 401) remember(null); throw error; })
      .finally(function () { refreshing = null; });
    return refreshing;
  }
  async function rpc(name, body, signal) {
    try { return await request("/rest/v1/rpc/" + name, body, await access(), signal); }
    catch (error) { if (error.status === 401) remember(null); throw error; }
  }
  async function calculation(name,body,signal){
    return request("/rest/v1/rpc/"+name,body,null,signal);
  }
  var localKey="clubefut.personal-builds.v1";
  var refreshedPersonal=new Map();
  function localData(){
    var raw=localStorage.getItem(localKey);
    if(!raw)return {records:[],counters:{},receipts:{}};
    var data=JSON.parse(raw);
    if(!data||!Array.isArray(data.records)||!data.counters||!data.receipts)throw new Error("Não foi possível ler as builds deste navegador. Os dados foram preservados.");
    return data;
  }
  async function localChange(fn){
    var run=function(){var data=localData(),result=fn(data);localStorage.setItem(localKey,JSON.stringify(data));return result;};
    try{return navigator.locks?await navigator.locks.request(localKey,run):run();}
    catch(e){throw new Error("Não foi possível salvar neste navegador: "+e.message);}
  }
  async function saveBuild(input,name,requestId,id,revision){
    if(session&&(!id||!id.startsWith("local-")))return rpc("site_novo_editor_salvar_v1",{p_entrada:input,p_nome:name,p_pedido_id:requestId,p_id:id||null,p_revisao:revision||null});
    if(id&&!id.startsWith("local-"))throw new Error("Entre na conta para atualizar essa build. Ou salve uma cópia no navegador.");
    var result=await calculation("site_novo_editor_avaliar_v1",{p_entrada:input});
    return localChange(function(data){
      var identity=JSON.stringify([input,name,id||null,revision||null]);
      if(data.receipts[requestId]){if(data.receipts[requestId].identity!==identity)throw new Error("Envio reutilizado para outro conteúdo.");var receipt=data.receipts[requestId].record;if(data.records.some(function(r){return r.id===receipt.id&&r.excluida;}))throw new Error("Build excluída. Salve uma nova cópia.");return receipt;}
      var previous=id?data.records.find(function(r){return r.id===id&&!r.excluida;}):null;
      if(id&&(!previous||previous.revisao!==revision))throw new Error("A build mudou ou foi excluída. Reabra a atual ou salve uma cópia.");
      if(previous&&previous.funcao_base_id!==input.funcao_id)throw new Error("Para mudar a função, use Salvar Uma Cópia.");
      var key=input.card_id+":"+input.funcao_id,number=previous?previous.numero:(data.counters[key]||0)+1;
      if(!previous)data.counters[key]=number;
      var record={id:id||"local-"+crypto.randomUUID(),origem:"navegador",card_id:input.card_id,funcao_base_id:input.funcao_id,numero:number,rotulo:result.ficha.funcao.rotulo+" "+number,nome:name,revisao:previous?previous.revisao+1:1,entrada:input,resultado:result,build:result.ficha,atualizado_em:new Date().toISOString()};
      record.build.pessoal_id=record.id;
      data.records= data.records.filter(function(r){return r.id!==record.id;}).concat(record);
      data.receipts[requestId]={identity:identity,record:record};return record;
    });
  }
  async function listBuilds(card){
    var local=localData().records.filter(function(r){return r.card_id===card&&!r.excluida;});
    // Reavaliar escolhas antigas no servidor para apresentar a régua vigente.
    // O registro salvo e o histórico continuam preservados até o usuário salvar.
    var next=0;
    async function worker(){
      while(next<local.length){
        var i=next++,record=local[i],cacheKey=record.id+':'+record.revisao;
        var result=refreshedPersonal.get(cacheKey);
        if(!result){
          result=calculation("site_novo_editor_avaliar_v1",{p_entrada:record.entrada});
          refreshedPersonal.set(cacheKey,result);
          result.catch(function(){});
        }
        try{result=await result;}catch(error){refreshedPersonal.delete(cacheKey);throw error;}
        local[i]=Object.assign({},record,{resultado:result,build:Object.assign({},result.ficha,{pessoal_id:record.id})});
      }
    }
    var remotePromise=session?rpc("site_novo_editor_listar_v1",{p_card_id:card}):Promise.resolve([]);
    var results=await Promise.all([remotePromise,Promise.all(Array.from({length:Math.min(3,local.length)},worker))]);
    var remote=results[0];
    return remote.map(function(r){r.origem="conta";return r;}).concat(local).sort(function(a,b){return a.funcao_base_id-b.funcao_base_id||a.numero-b.numero||a.id.localeCompare(b.id);});
  }
  async function removeBuild(id,revision){
    if(!id.startsWith("local-"))return rpc("site_novo_editor_excluir_v1",{p_id:id,p_revisao:revision});
    return localChange(function(data){var r=data.records.find(function(x){return x.id===id;});if(!r)throw new Error("Build não encontrada.");if(!r.excluida&&r.revisao!==revision)throw new Error("A build mudou. Reabra antes de excluir.");r.excluida=true;return {id:id,excluida:true};});
  }
  async function login(email, password) {
    var data = await request("/auth/v1/token?grant_type=password", { email: email.trim(), password: password });
    remember(data);
  }
  async function signup(email, password) {
    var data = await request("/auth/v1/signup", { email: email.trim(), password: password });
    if (data.access_token) remember(data);
    return Boolean(data.access_token);
  }
  async function logout() {
    try { if (session) await request("/auth/v1/logout?scope=local", {}, await access()); }
    finally { remember(null); }
  }
  window.FichaEditorAPI = Object.freeze({
    login: login, signup: signup, logout: logout,
    signedIn: function () { return Boolean(session && session.access_token); },
    email: function () { return session && session.user && session.user.email || ""; },
    // Identificação visual apenas; permissões continuam vinculadas ao ID autenticado.
    displayName: function () {
      var user=session&&session.user,meta=user&&user.user_metadata||{};
      return [meta.full_name,meta.name,meta.display_name,user&&user.email].find(function(v){return typeof v==="string"&&v.trim();})||"";
    },
    catalog: function (card, position, signal) { return calculation("site_novo_editor_catalogo_v1", { p_card_id: card, p_posicao_id: position }, signal); },
    evaluate: function (input, signal) { return calculation("site_novo_editor_avaliar_v1", { p_entrada: input }, signal); },
    save:saveBuild, list:listBuilds, remove:removeBuild,
    twin: function (input, from, to, signal) { return calculation("site_novo_editor_gemea_v1", { p_entrada: input, p_sai: from, p_entra: to }, signal); }
  });
}());
