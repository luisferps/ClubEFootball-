(function () {
  "use strict";
  // Um rascunho, uma avaliação privada. O cliente não contém a fórmula da nota.
  var api=window.FichaEditorAPI, session=null, pendingAction=null;
  var dialog=document.getElementById("build-editor"), content=document.getElementById("editor-content");
  var bars=[["shooting","Chute"],["passing","Passe"],["dribbling","Drible"],["dexterity","Destreza"],["lowerBodyStrength","Força nas pernas"],["aerialStrength","Força aérea"],["defending","Defesa"],["gk1","GO reflexo/salto"],["gk2","GO defesa/alcance"],["gk3","GO encaixe/reflexos"]];
  var colors={0:"azul",1:"verde",2:"amarelo",3:"roxo",5:"dourado"};
  function id(s){return document.getElementById(s);}
  function field(s){return dialog.querySelector("#draft-"+s);}
  function el(tag,css,text){var n=document.createElement(tag);n.className=css||"";if(text!==undefined)n.textContent=text;return n;}
  function button(text,fn,css){var b=el("button",css||"action",text);b.type="button";b.onclick=fn;return b;}
  function clone(v){return JSON.parse(JSON.stringify(v));}
  function fmt(v){return Number(v).toLocaleString("pt-BR",{minimumFractionDigits:2,maximumFractionDigits:2});}
  function status(v){id("editor-status").textContent=v;}
  function errorText(e){return e.name==="AbortError"?"A avaliação demorou. Tente novamente; seu rascunho foi mantido.":e.message;}
  function pick(options,value,label,fn){
    var s=el("select","editor-select");s.setAttribute("aria-label",label);
    options.forEach(function(o){var n=el("option","",o.name);n.value=String(o.id);s.append(n);});
    s.value=String(value===undefined||value===null?"":value);s.onchange=function(){if(!session.saving)fn(s.value);};return s;
  }
  function account(){
    var logged=api.signedIn();id("editor-account-name").textContent=logged?(api.displayName?api.displayName():api.email()):"";
    id("editor-account-name").hidden=!logged;
    id("editor-account-name").parentElement.hidden=false;
    id("editor-account-name").title=logged?id("editor-account-name").textContent+" · "+api.email():"";
    id("editor-save-notice").textContent=logged?"Salvamento na conta":"Salvamento neste navegador · sem login";
    if(logged)id("editor-auth").hidden=true;
    id("editor-login-show").hidden=logged||!id("editor-auth").hidden;id("editor-logout").hidden=!logged;
    id("editor-login-show").setAttribute("aria-expanded",String(!id("editor-auth").hidden));
    dialog.querySelector(".editor-footer").classList.toggle("auth-open",!id("editor-auth").hidden);
  }
  function showAccountForm(open){id("editor-auth").hidden=!open;account();if(open)id("editor-email").focus();else if(!api.signedIn())id("editor-login-show").focus();}
  function ask(text,label,fn){pendingAction=fn;id("editor-confirm-message").textContent=text;id("editor-discard").textContent=label;id("editor-confirm").hidden=false;id("editor-keep").focus();}
  function close(){
    var s=session;if(!s)return;clearTimeout(s.timer);if(s.request)s.request.abort();if(s.catalogRequest)s.catalogRequest.abort();session=null;pendingAction=null;
    dialog.close();content.replaceChildren();var score=dialog.querySelector(".editor-score");if(score)score.remove();id("editor-confirm").hidden=true;document.body.style.overflow=s.overflow;
    if(s.opener)s.opener.focus({preventScroll:true});window.scrollTo({left:s.x,top:s.y,behavior:"instant"});
  }
  function requestClose(){
    if(!session)return;if(session.saving){status("Aguarde a confirmação do envio antes de fechar.");return;}
    if(session.dirty)ask("Há alterações não salvas. Deseja descartá-las e fechar?","Descartar e fechar",close);else close();
  }
  function invalidate(){
    session.result=null;session.serial++;id("editor-save").disabled=true;id("editor-save-copy").disabled=true;
    if(!session.attributeRows){
      field("score-main").textContent="—";field("improve-main").textContent="—";
      content.querySelectorAll(".attr-final").forEach(function(n){n.textContent="—";});field("budget-summary").textContent="Avaliando…";
    }
    field("attribute-columns").setAttribute("aria-busy","true");
    dialog.querySelector(".score-wide .total small").textContent="AVALIANDO BUILD";
  }
  function schedule(){
    clearTimeout(session.timer);if(session.request)session.request.abort();
    session.timer=setTimeout(evaluate,220);
  }
  function changed(){session.dirty=true;session.saveRequest=null;invalidate();status("Alterações não salvas · avaliando");schedule();}
  function updateAttribute(row,a){
    var current=a.sistema,previous=row.displayedFinal;
    var delta=typeof previous==="number"&&typeof current==="number"?current-previous:0;
    row.querySelector(".attr-final-value").textContent=current==null?"—":current;
    var change=row.querySelector(".attr-change");
    change.textContent=delta>0?"↑":delta<0?"↓":"";
    change.className="attr-change"+(delta>0?" is-up":delta<0?" is-down":"");
    change.setAttribute("aria-label",delta?(delta>0?"Subiu":"Desceu")+" em relação à avaliação anterior":"Sem alteração");
    row.displayedFinal=current;
    row.title="Base: "+a.base+" · Após distribuição: "+a.referencia+" · No jogo: sem valoração das habilidades. No sistema: inclui os efeitos usados na avaliação.";
  }
  function renderAttributes(result){
    var columns=field("attribute-columns"),rows=session.attributeRows;
    if(rows&&result.atributos.length===Object.keys(rows).length&&result.atributos.every(function(a){return rows[a.codigo];})){
      result.atributos.forEach(function(a){
        updateAttribute(rows[a.codigo],a);
      });return;
    }
    columns.replaceChildren();session.attributeRows={};
    var groups=[["ATAQUE",[0,1,2,3,4,5,6,8,9]],["ATLETISMO",[10,11,12,15,16]],["FÍSICO",[7,13,14]],["DEFESA",[17,18,19,20]],["GOLEIRO",[21,22,23,24,25]]];
    groups.forEach(function(g){
      var box=el("div","attribute-group"),title=el("div","group-title");
      title.append(el("span","group-name",g[0]),el("b","group-base","BASE"),el("b","group-final","FINAL"));box.append(title);
      g[1].forEach(function(index){var a=result.atributos.find(function(x){return x.indice===index;});if(!a)return;
        var row=el("div","attribute");row.dataset.attributeCode=a.codigo;
        session.attributeRows[a.codigo]=row;
        var final=el("span","attr-final");final.append(el("span","attr-final-value"),el("span","attr-change"));
        row.append(el("span","attr-name",a.nome),el("span","attr-base",a.base==null?"—":a.base),final);updateAttribute(row,a);box.append(row);
      });columns.append(box);
    });
  }
  function applyResult(result){
    session.result=result;session.limits=result.limites_barras;session.total=result.pontos.total;
    field("score-main").textContent=fmt(result.nota_final);dialog.querySelector(".score-wide .total small").textContent="PONTUAÇÃO TOTAL";
    field("improve-main").closest(".gain").hidden=false;
    window.FichaView.renderComparison(field("improve-main"),session.source,session.input.funcao_id,result.nota_final);
    field("budget-summary").textContent=result.pontos.restantes+"/"+result.pontos.total;
    field("budget-summary").title="Pontos restantes / pontos totais";renderAttributes(result);
    field("attribute-columns").setAttribute("aria-busy","false");
    var retry=content.querySelector(".editor-retry");if(retry)retry.remove();
    id("editor-save").disabled=session.saving;id("editor-save-copy").disabled=session.saving;updateBarLimits();
    status(session.dirty?"Alterações não salvas · avaliação concluída":"Build avaliada no servidor");
  }
  async function evaluate(){
    var s=session;if(!s)return;var serial=s.serial;s.request=new AbortController();
    try{var result=await api.evaluate(clone(s.input),s.request.signal);if(session!==s||serial!==s.serial)return;applyResult(result);}
    catch(e){if(session!==s||serial!==s.serial)return;status(errorText(e)+" Valores exibidos são da última avaliação concluída.");id("editor-save").disabled=true;
      field("attribute-columns").setAttribute("aria-busy","false");dialog.querySelector(".score-wide .total small").textContent="AVALIAÇÃO PENDENTE";
      if(!content.querySelector(".editor-retry"))content.prepend(button("Tentar avaliar novamente",evaluate,"action editor-retry"));
      account();
    }
  }
  function updateBarLimits(){
    content.querySelectorAll(".editor-bar").forEach(function(row){
      var key=row.dataset.bar,level=session.input.barras[key],limit=session.limits?session.limits[key]:25;
      var used=session.catalog?bars.reduce(function(sum,b){var v=session.input.barras[b[0]];return sum+(v?Number(session.catalog.custos[v]):0);},0):0;
      var next=session.catalog?Number(session.catalog.custos[level+1])-Number(level?session.catalog.custos[level]:0):0;
      row.querySelector(".minus").disabled=session.saving||level<=0;
      row.querySelector(".plus").disabled=session.saving||!session.catalog||level>=limit||(session.total!==undefined&&used+next>session.total);
    });
  }
  function renderBars(){
    field("distribution").replaceChildren();bars.forEach(function(b){
      var row=el("div","bar editor-bar");row.dataset.bar=b[0];var value=el("output","bar-value",session.input.barras[b[0]]);
      function adjust(delta){if(session.saving)return;session.input.barras[b[0]]+=delta;value.textContent=session.input.barras[b[0]];changed();updateBarLimits();}
      var minus=button("−",function(){adjust(-1);},"adjust minus"),plus=button("+",function(){adjust(1);},"adjust plus");
      minus.setAttribute("aria-label","Diminuir "+b[1]);plus.setAttribute("aria-label","Aumentar "+b[1]);
      row.append(el("span","bar-name",b[1]),minus,value,plus);field("distribution").append(row);
    });updateBarLimits();
  }
  function skillName(code){var h=session.catalog.habilidades.find(function(x){return x.id===code;});return h?h.nome:String(code);}
  function twinsFor(code){
    var h=session.catalog.habilidades.find(function(x){return x.id===code;});
    var blocks=session.catalog.bloqueios_sugestao;
    if(!h||!Array.isArray(blocks))return [];
    return (h.gemeas_cadastradas||[]).filter(function(x){
      return !session.input.habilidades.includes(x)&&
        !blocks.some(function(b){return Number(b.skill_id)===Number(x)&&Number(b.funcao_id)===Number(session.input.funcao_id);})&&
        session.catalog.habilidades.some(function(t){return t.id===x&&t.fabricavel===true&&t.vetada===false;});
    });
  }
  function renderSkills(){
    var target=field("added-skills");target.replaceChildren();
    session.input.habilidades.forEach(function(code,index){
      var row=el("div","editor-skill-row");
      var opts=session.catalog.habilidades.filter(function(h){return h.id===code||!session.input.habilidades.includes(h.id);}).map(function(h){return{id:h.id,name:h.nome};});
      if(!opts.some(function(o){return o.id===code;}))opts.unshift({id:code,name:skillName(code)+" · não permitida nesta posição"});
      var select=pick(opts,code,"Habilidade adicionada "+(index+1),function(value){session.input.habilidades[index]=Number(value);changed();renderSkills();});
      var twins=twinsFor(code);select.title=twins.length?"Pode ser trocada por uma de: "+twins.map(skillName).join(", ")+" (sem alterar a nota).":"Sem gêmeas disponíveis.";
      row.append(select,button("×",function(){if(session.saving)return;session.input.habilidades.splice(index,1);changed();renderSkills();},"action editor-remove"));target.append(row);
    });
    field("added-skills-label").textContent="HABILIDADES ADICIONADAS · "+session.input.habilidades.length+" DE 5";
    if(session.input.habilidades.length<5)target.append(pick([{id:"",name:"+ Adicionar habilidade"}].concat(session.catalog.habilidades.filter(function(h){return !session.input.habilidades.includes(h.id);}).map(function(h){return{id:h.id,name:h.nome};})),"","Adicionar habilidade",function(v){if(!v)return;session.input.habilidades.push(Number(v));changed();renderSkills();}));
    var suggestions=field("suggested-skills");suggestions.replaceChildren();var map=new Map();
    session.input.habilidades.forEach(function(code){twinsFor(code).forEach(function(t){if(!map.has(t))map.set(t,[]);map.get(t).push(code);});});
    map.forEach(function(targets,twin){
      var b=button(skillName(twin),function(){
        if(session.saving)return;var old=suggestions.querySelector(".editor-twin-picker");if(old)old.remove();
        var chooser=el("div","editor-twin-picker");chooser.append(el("span","",skillName(twin)+" entra no lugar de uma habilidade:"));
        targets.forEach(function(from){chooser.append(button(skillName(from),function(){replaceTwin(from,twin);}));});suggestions.append(chooser);
      },"suggestion");
      b.title="Pode substituir uma de: "+targets.map(skillName).join(", ")+". Troca conferida pelo servidor.";suggestions.append(b);
    });
    if(!map.size)suggestions.append(el("span","empty","Nenhuma gêmea disponível para estas habilidades."));
  }
  async function replaceTwin(from,to){
    var s=session;if(!s||s.saving)return;
    var previous=s.result;clearTimeout(s.timer);if(s.request)s.request.abort();
    var serial=++s.serial;s.request=new AbortController();
    s.result=null;id("editor-save").disabled=true;id("editor-save-copy").disabled=true;status("Conferindo troca equivalente…");
    try{var r=await api.twin(clone(s.input),from,to,s.request.signal);if(session!==s||serial!==s.serial)return;s.input=r.entrada;s.dirty=true;s.serial++;s.saveRequest=null;renderSkills();applyResult(r.resultado);}
    catch(e){if(session===s&&serial===s.serial){if(previous)applyResult(previous);status(errorText(e));}}
  }
  function renderImpulses(){
    var target=field("impulses");target.replaceChildren();
    session.catalog.slots.forEach(function(slot){
      var current=slot.codigo?slot:session.catalog.adicionais.find(function(i){return i.codigo===session.input.impetos[slot.slot];});
      var box=el("div","impulse impulse-color-"+(current?(colors[current.cor]||"cinza"):"cinza"));
      var title=el("div","impulse-title"),name=el("b","");
      if(slot.vaga&&!slot.codigo)name.append(pick([{id:"",name:"Sem ímpeto adicional"}].concat(session.catalog.adicionais.map(function(i){return{id:i.codigo,name:i.nome};})),session.input.impetos[slot.slot],"Ímpeto adicional",function(v){if(v)session.input.impetos[slot.slot]=Number(v);else delete session.input.impetos[slot.slot];changed();renderImpulses();}));
      else {name.textContent=slot.nome;box.classList.add("is-fixed");}
      title.append(name);
      var deltas=(current&&current.efeitos||[]).map(function(e){return e.delta;});
      if(slot.condicional){
        var maximum=Math.max(1,Number(slot.maximo)||1);
        var selected=Number(session.input.condicoes[slot.slot]);
        if(!Number.isInteger(selected)||selected<1||selected>maximum)selected=maximum;
        session.input.condicoes[slot.slot]=selected;
        var level=button("+"+selected,function(){
          if(session.saving)return;
          session.input.condicoes[slot.slot]=selected>=maximum?1:selected+1;
          changed();renderImpulses();
        },"boost");
        level.setAttribute("aria-label","Ímpeto condicional +"+selected+". Clique para mostrar +"+(selected>=maximum?1:selected+1));
        level.title="Clique para alternar o degrau do ímpeto condicional";
        title.append(level);
      }else if(deltas.length&&deltas.every(function(v){return v===deltas[0];}))title.append(el("span","boost",(deltas[0]>=0?"+":"")+deltas[0]));
      box.append(title);
      var effects=el("div","mini-chips impulse-effects");(current&&current.efeitos||[]).forEach(function(e){
        var delta=slot.condicional?session.input.condicoes[slot.slot]:e.delta;
        effects.append(el("span","impulse-effect",e.nome+" +"+delta));
      });box.append(effects);target.append(box);
    });
  }
  function technicianOptionLabel(technician){
    var attributes=(technician.atributos||[]).map(function(attribute){
      return attribute.nome+" "+(attribute.delta>=0?"+":"")+attribute.delta;
    }).join(" · ");
    return technician.nome+" · "+technician.proficiencia+(attributes?" · "+attributes:"");
  }
  function technicianSelectedLabel(technician){
    return technician?technician.nome+" · "+technician.proficiencia:"Sem técnico";
  }
  function renderControls(){
    var slot=id("editor-function-slot");slot.replaceChildren();
    var funcs=session.catalog.funcoes.map(function(f){var p=session.source.card.posicoes.find(function(x){return x.id===f.posicao;});return{id:f.id+":"+f.posicao,name:f.nome+" · "+(p?p.codigo:f.posicao)};});
    var select=pick(funcs,session.input.funcao_id+":"+session.input.posicao_id,"Função e posição",function(v){var parts=v.split(":");session.input.funcao_id=Number(parts[0]);session.input.posicao_id=Number(parts[1]);changed();loadCatalog();});
    select.classList.add("editor-function");slot.append(select);
    var technicianChoices=[{id:"",name:"Sem técnico"}].concat(session.catalog.tecnicos.map(function(t){
      return{id:t.id,name:technicianOptionLabel(t)};
    }));
    var selectedTechnician=el("span","technician-selected-label",technicianSelectedLabel(session.catalog.tecnicos.find(function(t){return t.id===session.input.tecnico_id;})));
    selectedTechnician.setAttribute("aria-hidden","true");
    var technicianPicker=pick(technicianChoices,session.input.tecnico_id,"Técnico",function(v){
      session.input.tecnico_id=v||null;
      selectedTechnician.textContent=technicianSelectedLabel(session.catalog.tecnicos.find(function(t){return t.id===session.input.tecnico_id;}));
      changed();renderTechnicianDetails();
    });
    field("technician").replaceChildren(technicianPicker,selectedTechnician);
    renderTechnicianDetails();
    renderBars();renderSkills();renderImpulses();
  }
  async function loadCatalog(){
    var s=session;if(!s)return;var pos=s.input.posicao_id,version=(s.catalogVersion||0)+1;s.catalogVersion=version;if(s.catalogRequest)s.catalogRequest.abort();s.catalogRequest=new AbortController();status("Carregando opções permitidas…");
    try{var cat=await api.catalog(s.input.card_id,pos,s.catalogRequest.signal);if(session!==s||version!==s.catalogVersion||pos!==s.input.posicao_id)return;
      s.catalog=cat;if(!s.input.funcao_id&&cat.funcoes.length){s.input.funcao_id=cat.funcoes[0].id;s.input.posicao_id=cat.funcoes[0].posicao;}
      renderControls();schedule();
    }catch(e){if(session===s&&version===s.catalogVersion&&e.name!=="AbortError"){status(errorText(e));account();}}
  }
  function renderTechnicianDetails(){
    var chosen=session.catalog.tecnicos.find(function(t){return t.id===session.input.tecnico_id;});
    var boosts=chosen?(chosen.atributos||[]):[];
    field("technician-boosts").textContent=boosts.map(function(a){return a.nome+" +"+a.delta;}).join(" · ")||"—";
    field("technician-boosts").hidden=!boosts.length;
    field("technician-boosts").title=field("technician-boosts").textContent;
    var suggestions=field("suggested-technicians");suggestions.replaceChildren();
    var signature=function(t){return JSON.stringify((t.atributos||[]).map(function(a){return[a.codigo,a.delta];}));};
    var twins=chosen?session.catalog.tecnicos.filter(function(t){return t.id!==chosen.id&&t.proficiencia===chosen.proficiencia&&signature(t)===signature(chosen);}):[];
    twins.forEach(function(t){
      var b=button("",function(){if(session.saving)return;session.input.tecnico_id=t.id;changed();renderControls();},"suggestion technician-substitute");
      b.dataset.technicianId=String(t.id);
      var row=el("span","technician-substitute-row");row.append(el("span","suggestion-name",t.nome));
      var text=Array.isArray(t.atributos)?t.atributos.map(function(a){return a.nome+" "+(a.delta>=0?"+":"")+a.delta;}).join(" · ")||"Sem bônus de atributos":"Atributos não publicados";
      var effects=el("span","suggestion-boosts",text);effects.title=text;row.append(effects);b.append(row);
      b.title=t.nome+" · "+text+". Mesma proficiência máxima e mesmos atributos de técnico. Não altera a nota.";suggestions.append(b);
    });
    if(!twins.length)suggestions.append(el("span","empty","Nenhum técnico equivalente disponível."));
  }
  function mount(){
    id("editor-function-slot").replaceChildren();
    var previous=dialog.querySelector(".editor-score");if(previous)previous.remove();
    var block=document.querySelector("main .b3").cloneNode(true);block.classList.add("editor-block");
    block.querySelectorAll("[id]").forEach(function(n){n.id="draft-"+n.id;});
    block.querySelectorAll("[title]").forEach(function(n){n.removeAttribute("title");});content.replaceChildren(block);
    var score=block.querySelector(".score-wide");score.classList.add("editor-score");dialog.querySelector(".editor-header").insertBefore(score,id("editor-close"));
    field("improve-main").closest(".gain").hidden=false;
  }
  function beginDraft(mode,data,owned){
    var b=data.build||{},initial=mode==="edit";
    Object.assign(session,{mode:mode,source:clone(data),owned:owned||null,catalog:null,result:null,attributeRows:null,serial:0,dirty:false,saving:false,limits:null,total:b.orcamento_total,saveRequest:null});
    session.input=owned?clone(owned.entrada):{
      card_id:data.card.card_id,funcao_id:b.funcao&&b.funcao.id||null,posicao_id:b.posicao?b.posicao.id:(data.card.posicoes.find(function(p){return p.principal;})||{}).id,
      tecnico_id:initial&&b.tecnico?String(b.tecnico.id):null,
      barras:Object.fromEntries(bars.map(function(pair){var row=(b.barras||[]).find(function(x){return x.chave===pair[0];});return[pair[0],initial&&row?row.valor:0];})),
      habilidades:initial?(b.habilidades_adicionadas||[]).map(function(h){return h.id;}):[],impetos:{},condicoes:{}
    };
    if(initial&&!owned)(b.impetos||[]).forEach(function(i){if(i.tipo==="adicional")session.input.impetos[i.slot]=i.codigo;if(i.condicional&&i.condicao_nivel!==null)session.input.condicoes[i.slot]=i.condicao_nivel;});
    id("editor-title").textContent=mode==="new"?"Criar Nova Build":"Editar Build";id("editor-context").textContent=data.card.nome;
    id("editor-name").value=owned?owned.nome:initial?"Minha "+(b.funcao&&b.funcao.rotulo||"Build"):"";
    id("editor-origin").textContent=owned?"Esta build é sua. Salve as alterações ou crie uma cópia.":"A build do sistema não será alterada. O salvamento cria uma cópia pessoal.";
    id("editor-save").textContent=owned?"Salvar Alterações":"Salvar Minha Build";
    id("editor-delete").hidden=!owned;id("editor-delete").disabled=false;
    id("editor-save-copy").hidden=!owned;id("editor-save").hidden=false;id("editor-clear").hidden=false;id("editor-name").closest(".editor-meta").hidden=false;
    id("editor-auth").hidden=true;mount();renderBars();invalidate();account();loadCatalog();
  }
  function open(mode,data,owned){
    if(session||!api||!data||!data.card||(mode==="edit"&&!data.build&&!owned))return;
    session={opener:document.activeElement,overflow:document.body.style.overflow,x:window.scrollX,y:window.scrollY};
    document.body.style.overflow="hidden";id("editor-confirm").hidden=true;dialog.showModal();
    beginDraft(mode,data,owned);
    id("editor-close").focus();
  }
  function requestDelete(){
    var s=session;if(!s||!s.owned||s.saving)return;
    var r=s.owned;
    ask("Excluir "+(r.rotulo||r.nome)+"? Alterações não salvas serão descartadas. O número não será reutilizado.","Excluir build",async function(){
      if(session!==s||s.saving)return;
      s.saving=true;s.serial++;clearTimeout(s.timer);if(s.request)s.request.abort();
      id("editor-delete").disabled=true;id("editor-save").disabled=true;id("editor-save-copy").disabled=true;id("editor-name").disabled=true;
      dialog.querySelectorAll("#editor-content button,#editor-content select,.editor-function").forEach(function(n){n.disabled=true;});status("Excluindo sua build…");
      try{
        var result=await api.remove(r.id,r.revisao);
        if(!result||result.id!==r.id||result.excluida!==true)throw new Error("Não foi possível confirmar a exclusão.");
        if(session!==s)return;
        s.dirty=false;s.saving=false;close();
        window.dispatchEvent(new CustomEvent("ficha-builds-changed",{detail:{cardId:s.input.card_id}}));
      }catch(e){if(session===s)status(errorText(e));}
      finally{if(session===s){s.saving=false;id("editor-delete").disabled=false;id("editor-name").disabled=false;if(s.catalog)renderControls();id("editor-save").disabled=!s.result;id("editor-save-copy").disabled=!s.result;if(!s.result&&s.catalog)schedule();}}
    });
  }
  async function save(copy){
    var s=session;if(!s||s.saving||!s.result)return;var name=id("editor-name").value.trim();
    if(!name){status("Dê um nome à sua build.");id("editor-name").focus();return;}
    s.saving=true;id("editor-save").disabled=true;id("editor-save-copy").disabled=true;id("editor-name").disabled=true;
    dialog.querySelectorAll("#editor-content button,#editor-content select,.editor-function").forEach(function(n){n.disabled=true;});status("Salvando e conferindo…");
    var input=clone(s.input),target=copy?null:s.owned,identity=JSON.stringify([input,name,target&&target.id,target&&target.revisao]);
    if(!s.saveRequest||s.saveRequest.identity!==identity)s.saveRequest={identity:identity,id:crypto.randomUUID()};
    try{var saved=await api.save(input,name,s.saveRequest.id,target&&target.id,target&&target.revisao);if(session!==s)return;
      if(!saved.id||saved.nome!==name||!saved.resultado)throw new Error("Não foi possível conferir a gravação.");
      s.owned=saved;s.dirty=false;s.saveRequest=null;s.result=saved.resultado;
      id("editor-save").textContent="Salvar Alterações";id("editor-save-copy").hidden=false;
      id("editor-delete").hidden=false;
      id("editor-origin").textContent="Build pessoal salva. Atualize esta versão ou salve uma cópia.";
      status("Build salva e confirmada "+(saved.origem==="navegador"?"neste navegador":"na conta")+" · revisão "+saved.revisao);
      window.dispatchEvent(new CustomEvent("ficha-builds-changed",{detail:{cardId:s.input.card_id}}));
    }catch(e){if(session===s){status(errorText(e));account();if(!api.signedIn())showAccountForm(true);}}
    finally{if(session===s){s.saving=false;id("editor-name").disabled=false;renderControls();id("editor-save").disabled=!s.result;id("editor-save-copy").disabled=!s.result;}}
  }
  async function authenticate(createAccount){
    if(!session)return;var s=session,form=id("editor-auth");if(!form.reportValidity())return;
    var email=id("editor-email").value,password=id("editor-password").value;form.querySelectorAll("button").forEach(function(b){b.disabled=true;});id("editor-auth-status").textContent="Conectando…";
    try{
      if(createAccount){var ready=await api.signup(email,password);if(!ready){id("editor-auth-status").textContent="Confira o e-mail de confirmação e depois entre na conta.";return;}}
      else await api.login(email,password);
      id("editor-password").value="";if(session!==s)return;account();loadCatalog();
    }catch(e){id("editor-auth-status").textContent=errorText(e);}
    finally{form.querySelectorAll("button").forEach(function(b){b.disabled=false;});}
  }
  id("editor-auth").onsubmit=function(e){e.preventDefault();authenticate(false);};id("editor-signup").onclick=function(){authenticate(true);};
  id("editor-login-show").onclick=function(){showAccountForm(true);};
  id("editor-auth-close").onclick=function(){showAccountForm(false);};
  id("editor-logout").onclick=function(){if(!session||session.saving)return;ask("Sair fecha este rascunho. Alterações não salvas serão descartadas.","Sair da conta",async function(){try{await api.logout();}finally{close();}});};
  id("editor-close").onclick=requestClose;dialog.addEventListener("cancel",function(e){e.preventDefault();if(!id("editor-auth").hidden)showAccountForm(false);else requestClose();});
  id("editor-name").oninput=function(){if(session&&!session.saving){session.dirty=true;session.saveRequest=null;status("Alterações não salvas");}};
  id("editor-save").onclick=function(){save(false);};id("editor-save-copy").onclick=function(){save(true);};
  id("editor-delete").onclick=requestDelete;
  id("editor-clear").onclick=function(){if(!session||session.saving)return;ask("Limpar todos os pontos distribuídos? Habilidades, técnico e ímpetos serão mantidos.","Limpar Pontos",function(){bars.forEach(function(b){session.input.barras[b[0]]=0;});changed();renderBars();});};
  id("editor-keep").onclick=function(){id("editor-confirm").hidden=true;pendingAction=null;id("editor-close").focus();};
  id("editor-discard").onclick=function(){var fn=pendingAction;pendingAction=null;id("editor-confirm").hidden=true;if(fn)fn();};
  window.addEventListener("beforeunload",function(e){if(session&&(session.dirty||session.saving)){e.preventDefault();e.returnValue="";}});
  window.FichaEditor=Object.freeze({open:open});
}());
