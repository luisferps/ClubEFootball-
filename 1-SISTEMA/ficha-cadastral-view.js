/* Ficha cadastral V1.
   Esta superficie consulta somente public.frontend_ficha_v1 por meio do
   adaptador. Ela nao consulta D, nao escolhe Build e nao calcula pontuacao. */
(function instalaFichaCadastral(root){
 'use strict';

 var tokenCarga=0,camada=null,overflowAnterior='';

 function esc(v){
  var d=document.createElement('div');d.textContent=v===null||v===undefined?'':String(v);return d.innerHTML;
 }
 function attr(v){
  return String(v===null||v===undefined?'':v).replace(/&/g,'&amp;').replace(/</g,'&lt;')
   .replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
 }
 function lista(v){return Array.isArray(v)?v:[];}
 function texto(v,fallback){var s=v===null||v===undefined?'':String(v).trim();return s||fallback||'';}
 function inteiro(v){var n=Number(v);return Number.isInteger(n)?String(n):'—';}
 function fotoSegura(v){
  var s=texto(v,'');
  return /^https:\/\/res\.cloudinary\.com\/[A-Za-z0-9_-]+\/image\/upload\//.test(s)?s:'';
 }
 function fecha(){
  tokenCarga++;
  if(camada&&camada.parentNode)camada.parentNode.removeChild(camada);
  camada=null;document.body.style.overflow=overflowAnterior;
 }
 function tecla(ev){if(ev.key==='Escape'&&camada)fecha();}
 document.addEventListener('keydown',tecla);

 function estilo(){
  if(document.getElementById('t6-ficha-cadastral-css'))return;
  var s=document.createElement('style');s.id='t6-ficha-cadastral-css';
  s.textContent=''
   +'.t6fc-back{position:fixed;inset:0;z-index:100080;background:rgba(2,7,5,.82);backdrop-filter:blur(7px);padding:18px;overflow:auto}'
   +'.t6fc-dialog{width:min(1080px,100%);margin:0 auto;background:#0b1510;color:#edf7f0;border:1px solid rgba(91,221,148,.28);border-radius:18px;box-shadow:0 30px 90px rgba(0,0,0,.58);overflow:hidden}'
   +'.t6fc-head{display:grid;grid-template-columns:104px minmax(0,1fr) auto;gap:18px;align-items:center;padding:22px;background:linear-gradient(135deg,#13291d,#0b1510);border-bottom:1px solid rgba(255,255,255,.08)}'
   +'.t6fc-photo{width:104px;height:139px;border-radius:13px;object-fit:cover;background:#17231d;border:1px solid rgba(255,255,255,.12)}'
   +'.t6fc-ph{display:flex;align-items:center;justify-content:center;font-size:34px;color:#688073}'
   +'.t6fc-title{margin:4px 0 5px;font:800 27px/1.05 system-ui}.t6fc-head p{margin:0;color:#9eb1a6;font:13px/1.5 system-ui}'
   +'.t6fc-k{font:800 10px/1 system-ui;letter-spacing:1.2px;color:#59dc94}.t6fc-close{align-self:start;border:1px solid rgba(255,255,255,.16);background:#14231b;color:#fff;border-radius:10px;width:38px;height:38px;cursor:pointer;font-size:21px}'
   +'.t6fc-alert{margin:18px 22px 0;padding:12px 14px;border-radius:11px;background:#201b0d;border:1px solid #725c22;color:#f3d98b;font:12.5px/1.5 system-ui}'
   +'.t6fc-warn{background:#231312;border-color:#703a35;color:#efb2ab}.t6fc-body{padding:20px 22px 28px;display:grid;gap:16px}'
   +'.t6fc-facts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}.t6fc-fact{padding:11px 12px;border-radius:10px;background:#111e17;border:1px solid rgba(255,255,255,.07)}'
   +'.t6fc-fact small{display:block;color:#7f9488;font:700 9px/1 system-ui;letter-spacing:.8px;text-transform:uppercase}.t6fc-fact b{display:block;margin-top:5px;font:700 13px/1.25 system-ui;overflow-wrap:anywhere}'
   +'.t6fc-sec{border:1px solid rgba(255,255,255,.08);background:#0e1a13;border-radius:12px;overflow:hidden}.t6fc-sec summary{cursor:pointer;padding:13px 15px;font:800 12px/1.2 system-ui;color:#d6e4db;list-style:none}.t6fc-sec summary::-webkit-details-marker{display:none}.t6fc-sec summary span{color:#57d892;margin-left:6px}'
   +'.t6fc-content{padding:0 14px 14px}.t6fc-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px}.t6fc-item{display:flex;justify-content:space-between;gap:10px;padding:8px 9px;border-radius:8px;background:#14221a;color:#b9c9bf;font:11.5px/1.3 system-ui}.t6fc-item b{color:#f0f7f2;text-align:right}.t6fc-tags{display:flex;flex-wrap:wrap;gap:7px}.t6fc-tag{padding:7px 9px;border-radius:8px;background:#14251b;border:1px solid rgba(82,216,142,.16);font:11.5px/1.2 system-ui}.t6fc-tag em{font-style:normal;color:#6fe1a3;margin-left:4px}'
   +'.t6fc-loading{min-height:360px;display:flex;align-items:center;justify-content:center;color:#9eb1a6;font:14px system-ui}'
   +'@media(max-width:760px){.t6fc-back{padding:0}.t6fc-dialog{border-radius:0;min-height:100vh}.t6fc-head{grid-template-columns:72px minmax(0,1fr) auto;padding:16px;gap:12px}.t6fc-photo{width:72px;height:96px}.t6fc-title{font-size:21px}.t6fc-facts{grid-template-columns:repeat(2,minmax(0,1fr))}.t6fc-grid{grid-template-columns:1fr}.t6fc-body{padding:16px}.t6fc-alert{margin:14px 16px 0}}';
  document.head.appendChild(s);
 }
 function abreCasca(){
  fecha();estilo();
  overflowAnterior=document.body.style.overflow;document.body.style.overflow='hidden';
  camada=document.createElement('div');camada.className='t6fc-back';
  camada.innerHTML='<section class="t6fc-dialog" role="dialog" aria-modal="true" aria-label="Ficha cadastral"><div class="t6fc-loading">Carregando a Ficha pelo contrato próprio…</div></section>';
  camada.addEventListener('pointerdown',function(ev){if(ev.target===camada)fecha();});
  document.body.appendChild(camada);
 }
 function fato(n,v){return '<div class="t6fc-fact"><small>'+esc(n)+'</small><b>'+esc(texto(v,'—'))+'</b></div>';}
 function item(n,v){return '<div class="t6fc-item"><span>'+esc(texto(n,'—'))+'</span><b>'+esc(texto(v,'—'))+'</b></div>';}
 function tag(n,v){return '<span class="t6fc-tag">'+esc(texto(n,'—'))+(v!==undefined&&v!==null&&String(v)!==''?'<em>'+esc(v)+'</em>':'')+'</span>';}
 function secao(titulo,itens,corpo,aberta){
  return '<details class="t6fc-sec"'+(aberta?' open':'')+'><summary>'+esc(titulo)+' <span>'+itens+'</span></summary><div class="t6fc-content">'+corpo+'</div></details>';
 }
 function desenha(f){
  if(!camada)return;
  var cardId=texto(f.card_id!==undefined?f.card_id:f.id,''),foto=fotoSegura(f.foto_url_cloudinary||f.fotoUrl);
  var atributos=lista(f.atributos),corpo=lista(f.corpo),posicoes=lista(f.posicoes),habilidades=lista(f.habilidades);
  var estilos=lista(f.estilos_ia),pes=lista(f.pes),playstyles=lista(f.playstyles),impetos=lista(f.impetos),pendencias=lista(f.pendencias);
  var posCodigo=f.posicao_principal_codigo||f.posicaoSigla,posNome=f.posicao_principal_nome||f.posicaoNome;
  var cabFoto=foto?'<img class="t6fc-photo" src="'+attr(foto)+'" alt="">':'<span class="t6fc-photo t6fc-ph" aria-hidden="true">◇</span>';
  var meta=[texto(f.tipo_carta_nome||f.tipoCartaNome,''),texto(posCodigo,''),texto(f.box_nome||f.box,'')].filter(Boolean).join(' · ');
  var fatos=''
   +fato('Card ID',cardId)+fato('Overall cadastral',f.overall)+fato('Posição principal',[posCodigo,posNome].filter(Boolean).join(' · '))
   +fato('Tipo de carta',f.tipo_carta_nome||f.tipoCartaNome)+fato('Box',f.box_nome||f.box)+fato('Pé dominante',f.pe_dominante)
   +fato('Altura / peso',(f.altura!=null?f.altura+' cm':'—')+' / '+(f.peso!=null?f.peso+' kg':'—'))+fato('Idade',f.idade)
   +fato('Nacionalidade',f.nacionalidade_nome)+fato('Clube',f.clube_nome)+fato('Liga',f.liga_nome)+fato('Orçamento',f.orcamento);
  var atrHtml='<div class="t6fc-grid">'+atributos.map(function(a){return item(a.nome||a.codigo,inteiro(a.valor));}).join('')+'</div>';
  var posHtml='<div class="t6fc-tags">'+posicoes.map(function(p){return tag((p.nativa?'★ ':'')+(p.codigo||p.nome),p.nivel_aptidao!=null?'aptidão '+p.nivel_aptidao:'');}).join('')+'</div>';
  var playHtml='<div class="t6fc-tags">'+playstyles.map(function(p){return tag(p.nome||p.codigo,'slot '+p.slot);}).join('')+'</div>';
  var habHtml='<div class="t6fc-tags">'+habilidades.map(function(h){return tag(h.nome||('Skill '+h.skill_id),h.tipo||'');}).join('')+'</div>';
  var iaHtml='<div class="t6fc-tags">'+estilos.map(function(e){return tag(e.nome||e.codigo,'');}).join('')+'</div>';
  var corpoHtml='<div class="t6fc-grid">'+corpo.map(function(c){return item(c.nome||c.codigo,inteiro(c.valor));}).join('')+'</div>';
  var peHtml='<div class="t6fc-grid">'+pes.map(function(p){return item(p.nome||p.campo,inteiro(p.valor));}).join('')+'</div>';
  var impHtml='<div class="t6fc-tags">'+impetos.map(function(i){var estado=i.vaga?'vaga':(i.condicional?'condicional':'nativo');return tag(i.nome||('Ímpeto '+i.codigo),estado);}).join('')+'</div>';
  var aviso='<div class="t6fc-alert"><b>Esta é a Ficha cadastral.</b> Ela mostra somente o cadastro oficial do card. A pontuação, a distribuição e a contratação dependem da função e aparecem na Build publicada aberta pelo Ranking.</div>';
  if(pendencias.length)aviso+='<div class="t6fc-alert t6fc-warn"><b>Cadastro com pendências explícitas:</b> '+esc(pendencias.join(', '))+'</div>';
  camada.innerHTML='<section class="t6fc-dialog" role="dialog" aria-modal="true" aria-labelledby="t6fc-titulo">'
   +'<div class="t6fc-head">'+cabFoto+'<div><span class="t6fc-k">FICHA CADASTRAL · CLUBE_NOVO</span><div class="t6fc-title" id="t6fc-titulo">'+esc(f.nome||('Card '+cardId))+'</div><p>'+esc(meta||'Dados canônicos do cadastro')+'</p></div><button class="t6fc-close" type="button" aria-label="Fechar">×</button></div>'
   +aviso+'<div class="t6fc-body"><div class="t6fc-facts">'+fatos+'</div>'
   +secao('Atributos',atributos.length,atrHtml,true)+secao('Posições',posicoes.length,posHtml,true)
   +secao('Playstyles',playstyles.length,playHtml,false)+secao('Habilidades',habilidades.length,habHtml,false)
   +secao('Estilos de IA',estilos.length,iaHtml,false)+secao('Medidas do corpo',corpo.length,corpoHtml,false)
   +secao('Pé e comportamento',pes.length,peHtml,false)+secao('Ímpetos',impetos.length,impHtml,false)
   +'</div></section>';
  var botao=camada.querySelector('.t6fc-close');if(botao){botao.onclick=fecha;botao.focus();}
 }
 function erro(e){
  if(!camada)return;
  var msg=texto(e&&e.message,'A Ficha cadastral não pôde ser carregada.');
  camada.innerHTML='<section class="t6fc-dialog" role="dialog" aria-modal="true"><div class="t6fc-head"><span class="t6fc-photo t6fc-ph">!</span><div><span class="t6fc-k">FICHA CADASTRAL</span><div class="t6fc-title">Dados indisponíveis</div><p>'+esc(msg)+'</p></div><button class="t6fc-close" type="button" aria-label="Fechar">×</button></div></section>';
  var b=camada.querySelector('.t6fc-close');if(b){b.onclick=fecha;b.focus();}
 }
 root.t6FechaFichaCadastral=fecha;
 root.t6AbreFichaCadastral=function(cardId){
  var id=texto(cardId,'').split('@')[0];
  if(!/^\d+$/.test(id))return false;
  abreCasca();var meuToken=++tokenCarga,CN=root.ClubeNovoReadModel;
  if(!CN||typeof CN.ficha!=='function'){erro(new Error('Contrato público da Ficha indisponível.'));return true;}
  Promise.resolve().then(function(){return CN.ficha(id);}).then(function(f){
   if(meuToken!==tokenCarga||!camada)return;
   if(!f)throw new Error('O card não existe na view da Ficha.');
   desenha(f);
  }).catch(function(e){if(meuToken===tokenCarga)erro(e);});
  return true;
 };
})(window);
