'use strict';
const $=s=>document.querySelector(s);
const texto=v=>Array.isArray(v)?(v.length?v.join(', '):'Nenhum'):(v===null||v===undefined||v===''?'Não informado':String(v));
const seguro=v=>texto(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(c){const r=await fetch(c,{cache:'no-store'}),d=await r.json();if(!r.ok)throw new Error(d.erro||'Consulta local indisponível');return d;}
function preencher(id,pares){const alvo=$(id);alvo.innerHTML='';for(const [n,v] of pares){const t=document.importNode($('#linha').content,true);t.querySelector('dt').textContent=n;t.querySelector('dd').innerHTML=seguro(v);alvo.append(t);}}
function trocarAba(nome){document.querySelectorAll('.aba').forEach(x=>x.hidden=x.id!=='aba-'+nome);document.querySelectorAll('[data-aba]').forEach(x=>x.classList.toggle('aba-ativa',x.dataset.aba===nome));}
function parametros(){return {card:$('#card-id').value.trim(),funcao:$('#funcao').value,tecnico:$('#tecnico').value,impetoNivel:$('#impeto-nivel').value};}
function caminho(rota){const p=parametros();return rota+'?card_id='+encodeURIComponent(p.card)+'&funcao_id='+encodeURIComponent(p.funcao)+'&tecnico_id='+encodeURIComponent(p.tecnico)+'&impeto_nivel='+encodeURIComponent(p.impetoNivel);}
function linhaVazia(id,msg,colunas){$(id).innerHTML='<tr><td colspan="'+(colunas||5)+'">'+seguro(msg)+'</td></tr>';}
const ESTADOS_FILA={sem_lote:'Pronto para criar a fila V3',parado:'Parado',rodando:'Rodando',pausando:'Pausando',pausado:'Pausado',encerrando:'Encerrando',encerrado:'Encerrado',interrompido:'Interrompido','concluído':'Concluído',concluido:'Concluído',falhou:'Falhou',aguardando_contrato_de_integracao:'Aguardando contrato da Integração',aguardando_fila_v3:'Fila V3 não autorizada',aguardando_aplicacao_fila_v3:'Aguardando aplicação da fila V3'};
function rotuloEstado(estado){return ESTADOS_FILA[estado]||texto(estado);}
let temporizadorLinhaAtual=null;
let temporizadorFila=null;
let atualizandoFila=false;
let ultimoEstadoFila=null;
const buildsCampeasPorLinha=new Map();
const TAMANHO_PAGINA=200;
let linhasFilaAtuais=[];
let paginaFila=0;
let linhaFocoId=null;
let resultadosAtuais=[];
let paginaResultados=0;
function timestampInicio(x){return x&&((x.iniciada_em)||(x.otimizador_iniciado_em));}
function timestampFim(x){return x&&((x.finalizada_em)||(x.otimizador_finalizado_em));}
function duracaoLegivel(ms){const total=Math.max(0,Math.floor(ms/1000)),h=Math.floor(total/3600),m=Math.floor((total%3600)/60),s=total%60;if(total<60)return s+' s';return (h?h+' h ':'')+(m?m+' min ':'')+s+' s';}
function duracaoFinal(x){const segundos=x.duracao_segundos??x.segundos;if(segundos!==null&&segundos!==undefined&&segundos!==''&&Number.isFinite(Number(segundos)))return duracaoLegivel(Number(segundos)*1000);const inicio=timestampInicio(x),fim=timestampFim(x);if(!inicio&&!fim&&x.estado==='pendente')return 'Aguardando processamento';const a=Date.parse(inicio),b=Date.parse(fim);return Number.isFinite(a)&&Number.isFinite(b)&&b>=a?duracaoLegivel(b-a):'Duração não disponível';}
function duracaoCompacta(ms){const total=Math.max(0,Math.round(Number(ms)/10)/100),h=Math.floor(total/3600),resto=total-(h*3600),m=Math.floor(resto/60),s=resto-(m*60),segundos=(valor,doisDigitos)=>{const inteiro=Math.floor(valor),cent=Math.round((valor-inteiro)*100),base=(doisDigitos?String(inteiro).padStart(2,'0'):String(inteiro));return cent?base+'.'+String(cent).padStart(2,'0').replace(/0+$/,''):base;};if(total<60)return segundos(total,false)+'s';return (h?h+'h':'')+m+'m'+segundos(s,true)+'s';}
function duracaoFinalCompacta(x){const segundos=x.duracao_segundos??x.segundos;if(segundos!==null&&segundos!==undefined&&segundos!==''&&Number.isFinite(Number(segundos)))return duracaoCompacta(Number(segundos)*1000);const inicio=timestampInicio(x),fim=timestampFim(x);if(!inicio&&!fim&&x.estado==='pendente')return 'Aguardando processamento';const a=Date.parse(inicio),b=Date.parse(fim);return Number.isFinite(a)&&Number.isFinite(b)&&b>=a?duracaoCompacta(b-a):'Duração não disponível';}
function atualizarTemposEmProcessamento(){document.querySelectorAll('[data-inicio-processamento]').forEach(alvo=>{const inicio=Date.parse(alvo.dataset.inicioProcessamento);if(Number.isFinite(inicio))alvo.textContent='Em processamento há '+duracaoLegivel(Date.now()-inicio);});}
function limparContadorLinhaAtual(){if(temporizadorLinhaAtual!==null){window.clearInterval(temporizadorLinhaAtual);temporizadorLinhaAtual=null;}const destaque=$('#progresso-ao-vivo');destaque.hidden=true;destaque.textContent='';}
function pintarContadorLinhaAtual(linha){limparContadorLinhaAtual();const inicio=Date.parse(timestampInicio(linha));if(!linha||linha.estado!=='processando'||!Number.isFinite(inicio))return;const campo=document.createElement('div');campo.id='tempo-linha-atual';campo.innerHTML='<dt>Em processamento há</dt><dd id="contador-linha-atual"></dd>';$('#linha-atual').append(campo);const atualizar=()=>{const tempo=duracaoLegivel(Date.now()-inicio),alvo=$('#contador-linha-atual'),destaque=$('#progresso-ao-vivo');if(alvo)alvo.textContent=tempo;destaque.hidden=false;destaque.textContent='Processando agora: linha '+linha.linha_id+' · '+(linha.carta_rotulo||linha.card_id)+' · há '+tempo;atualizarTemposEmProcessamento();};atualizar();temporizadorLinhaAtual=window.setInterval(atualizar,1000);}
function aplicarAcoes(acoes,confirmacao){const a=acoes||{},c=confirmacao||{};$('#iniciar-fila').disabled=!(a.iniciar===true||a.retomar===true||a.criar===true);$('#iniciar-fila').textContent=a.iniciar===true?'Iniciar':a.retomar===true?'Retomar':a.criar===true?'Criar e iniciar':'Iniciar';$('#pausar-fila').disabled=a.pausar!==true;$('#parar-fila').disabled=!(a.parar===true&&c.parar_exige_confirmacao===true);}
function agendarAtualizacaoFila(estado){if(temporizadorFila!==null){window.clearTimeout(temporizadorFila);temporizadorFila=null;}if(['rodando','pausando','encerrando'].includes(estado))temporizadorFila=window.setTimeout(atualizarFila,3000);}
function classeLinhaFila(estado){return 'linha-'+String(estado||'desconhecido').replace(/[^a-z0-9_-]/gi,'-');}
function tempoNaFila(x){const inicio=timestampInicio(x);if(x.estado==='processando'&&inicio&&Number.isFinite(Date.parse(inicio)))return '<span class="tempo-em-processamento" data-inicio-processamento="'+seguro(inicio)+'"></span>';return seguro(duracaoFinal(x));}
function inteiroBuilds(v){if(v===null||v===undefined||v==='')return null;const s=String(v).trim();return /^\d+$/.test(s)?s.replace(/^0+(?=\d)/,''):null;}
const UNIDADES_BUILDS=['','mil','mi','bi','tri','quadr.','quint.','sext.'];
function abreviarInteiroBuilds(v){const s=inteiroBuilds(v);if(s===null)return null;if(s.length<=3)return s;const grupo=Math.floor((s.length-1)/3),expo=grupo*3,casas=s.length-expo;if(grupo>=UNIDADES_BUILDS.length){const decimal=s.slice(casas,casas+1);return s.slice(0,casas)+(decimal&&decimal!=='0'?','+decimal:'')+'e'+expo;}const divisor=10n**BigInt(expo),numero=BigInt(s),inteiro=numero/divisor,decimo=(numero%divisor)*10n/divisor;return String(inteiro)+(decimo?','+String(decimo):'')+' '+UNIDADES_BUILDS[grupo];}
function inteiroBuildsExato(v){const s=inteiroBuilds(v);return s===null?null:BigInt(s).toLocaleString('pt-BR');}
function buildsComparadas(x){const n=inteiroBuilds(x.builds_comparadas);if(n!==null)return n;if(x.estado==='pendente')return 'Aguardando processamento';if(x.estado==='processando')return 'Calculando…';return 'Não registrada';}
function buildsPossiveis(x){const n=inteiroBuilds(x.builds_possiveis);if(n!==null)return n;if(x.estado==='pendente')return 'Aguardando processamento';if(x.estado==='processando')return 'Contando…';return 'Não registrada';}
function contadorBuildsCompacto(x,campo,rotulo,valorAusente){const exato=inteiroBuilds(x[campo]);if(exato===null)return seguro(valorAusente(x));const titulo=rotulo+': '+inteiroBuildsExato(exato);return '<span class="contador-builds" title="'+seguro(titulo)+'" aria-label="'+seguro(titulo)+'">'+seguro(abreviarInteiroBuilds(exato))+'</span>';}
function buildsComparadasCompactas(x){return contadorBuildsCompacto(x,'builds_comparadas','Builds comparadas',buildsComparadas);}
function buildsPossiveisCompactas(x){return contadorBuildsCompacto(x,'builds_possiveis','Builds possíveis',buildsPossiveis);}
function numero(v){const n=Number(v);return Number.isFinite(n)?n:0;}
function normalizarBusca(v){return String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();}
function linhaBateBusca(x,busca){if(!busca)return true;return normalizarBusca([x.card_id,x.carta_rotulo,x.funcao_rotulo,x.posicao_rotulo,x.impeto_condicional_rotulo].join(' ')).includes(busca);}
function linhaBateEstado(x,estado){if(estado==='todos')return true;if(estado==='problemas')return ['bloqueado','falhou','interrompido'].includes(x.estado);return x.estado===estado;}
function linhasFiltradas(){const busca=normalizarBusca($('#filtro-fila').value),estado=$('#filtro-estado-fila').value;return linhasFilaAtuais.filter(x=>linhaBateBusca(x,busca)&&linhaBateEstado(x,estado));}
function renderizarLinhasFila(){
  const linhas=linhasFiltradas(),paginas=Math.max(1,Math.ceil(linhas.length/TAMANHO_PAGINA));
  paginaFila=Math.max(0,Math.min(paginaFila,paginas-1));
  const inicio=paginaFila*TAMANHO_PAGINA,fim=Math.min(inicio+TAMANHO_PAGINA,linhas.length),visiveis=linhas.slice(inicio,fim);
  $('#resumo-linhas').textContent=linhas.length?`${inicio+1}–${fim} de ${linhas.length} linhas`:'Nenhuma linha encontrada';
  $('#pagina-anterior-fila').disabled=paginaFila===0;
  $('#proxima-pagina-fila').disabled=paginaFila>=paginas-1;
  $('#linhas-fila').innerHTML=visiveis.map(x=>{
    const alvo=String(x.linha_id)===String(linhaFocoId)?' linha-alvo':'';
    return '<tr data-linha-id="'+seguro(x.linha_id)+'" class="'+classeLinhaFila(x.estado)+alvo+'"><td class="indice-fila" title="Linha técnica '+seguro(x.linha_id)+'">'+seguro(x._ordem_visual)+'</td><td>'+seguro(x.carta_rotulo||x.card_id)+'</td><td>'+seguro(x.funcao_rotulo||'ID '+x.funcao_id+' · catálogo ausente')+'</td><td>'+seguro(x.posicao_rotulo||'ID '+x.posicao_id+' · catálogo ausente')+'</td><td>'+seguro(x.impeto_condicional_rotulo)+'</td><td>'+seguro(rotuloEstado(x.estado))+'</td><td>'+tempoNaFila(x)+'</td><td>'+buildsComparadasCompactas(x)+'</td><td>'+buildsPossiveisCompactas(x)+'</td><td>'+seguro(texto(x.motivo||x.erro))+'</td></tr>';
  }).join('')||'<tr><td colspan="10">Nenhuma linha encontrada com estes filtros.</td></tr>';
  atualizarTemposEmProcessamento();
}
function irParaAndamento(){
  const alvo=linhasFilaAtuais.find(x=>String(x.linha_id)===String(linhaFocoId))||linhasFilaAtuais.find(x=>x.estado==='pendente');
  if(!alvo)return;
  $('#filtro-fila').value='';$('#filtro-estado-fila').value='todos';
  const indice=linhasFilaAtuais.indexOf(alvo);paginaFila=Math.floor(indice/TAMANHO_PAGINA);linhaFocoId=alvo.linha_id;renderizarLinhasFila();
  window.requestAnimationFrame(()=>{const caixa=$('#rolagem-fila'),linha=caixa.querySelector('[data-linha-id="'+CSS.escape(String(alvo.linha_id))+'"]');if(linha)caixa.scrollTo({top:Math.max(0,linha.offsetTop-(caixa.clientHeight/2)),behavior:'smooth'});});
}
function mensagemDaRodada(estado,t){
  if(estado==='aguardando_aplicacao_fila_v3')return 'A fila produtiva V3 ainda depende da aplicação explícita da migração no banco.';
  if(estado==='sem_lote')return 'Nenhuma fila produtiva V3 existe. Clique em Criar e iniciar para montar a fila completa.';
  if(estado==='parado')return 'Rodada pronta para iniciar.';
  if(estado==='rodando')return 'Motor trabalhando. A tela acompanha automaticamente.';
  if(estado==='pausado')return 'Rodada pausada com as linhas restantes preservadas.';
  if(estado==='concluido')return 'Todas as linhas da rodada foram finalizadas.';
  if(estado==='falhou')return 'A rodada parou por falha. Consulte os detalhes.';
  return numero(t.linhas_geradas)?'Acompanhando a rodada ativa.':'Nenhuma rodada disponível.';
}
function pintarFila(d){
  const t=d.totais||{},execucao=d.execucao||{},estado=execucao.estado||d.estado;
  ultimoEstadoFila=estado;
  const problemas=numero(t.bloqueadas)+numero(t.falhas),finalizadas=numero(t.concluidas)+numero(t.bloqueadas)+numero(t.interrompidas)+numero(t.falhas),total=numero(t.linhas_geradas),percentual=total?Math.min(100,(finalizadas/total)*100):0;
  const itens=[['Cartas',t.cartas_selecionadas,''],['Linhas',t.linhas_geradas,''],['Concluídas',t.concluidas,'total-destaque'],['Em andamento',t.em_processamento,''],['Pendentes',t.pendentes,''],['Para Bonificador',t.bonificador_pendentes,''],['Problemas',problemas,'total-problema']];
  $('#totais-fila').innerHTML=itens.map(x=>'<div class="total '+x[2]+'"><span>'+seguro(x[0])+'</span><strong>'+seguro(x[1]||0)+'</strong></div>').join('');
  $('#estado-execucao').textContent=rotuloEstado(estado);
  $('#resumo-andamento').textContent=total?`${finalizadas} de ${total} linhas finalizadas · ${numero(t.pendentes)} aguardando`:'Nenhuma linha carregada.';
  $('#barra-progresso-preenchida').style.width=percentual.toFixed(2)+'%';
  $('.barra-progresso').setAttribute('aria-valuenow',String(Math.round(percentual)));
  $('#fila-aviso').textContent=d.mensagem||mensagemDaRodada(estado,t);
  $('#modo-rodada').textContent=d.pode_publicar===false?'PRODUÇÃO V3 · SEM PUBLICAÇÃO':'PUBLICAÇÃO AUTORIZADA';
  aplicarAcoes(d.acoes,d.confirmacao);
  const atual=d.linha_atual;
  preencher('#linha-atual',atual?[['Linha',atual.linha_id],['Carta',atual.carta_rotulo||atual.card_id],['Função',atual.funcao_rotulo||atual.funcao_id],['Posição',atual.posicao_rotulo||atual.posicao_id],['Ímpeto / nível',atual.impeto_condicional_rotulo],['Estado',rotuloEstado(atual.estado)],['Motivo',texto(atual.motivo)]]:[['Estado','Nenhuma linha em processamento.'],['Próximo passo',estado==='aguardando_aplicacao_fila_v3'?'Aplique explicitamente a migração da fila V3 antes de criar qualquer lote.':estado==='sem_lote'?'Clique em Criar e iniciar para formar a fila completa por força da carta.':estado==='parado'?'Clique em Iniciar quando quiser começar.':estado==='concluido'?'Otimizador concluído; o Bonificador só poderá iniciar pelo fluxo separado.':'Aguardando a próxima atualização.']]);
  pintarContadorLinhaAtual(atual);
  if(!d.disponivel){linhasFilaAtuais=[];linhaFocoId=null;$('#ir-linha-atual').disabled=true;renderizarLinhasFila();$('#eventos-fila').textContent='Fila indisponível: '+texto(d.origem);return;}
  linhasFilaAtuais=(d.itens||[]).map((x,indice)=>({...x,_ordem_visual:indice+1}));
  linhaFocoId=atual&&atual.linha_id||((linhasFilaAtuais.find(x=>x.estado==='pendente')||{}).linha_id??null);
  $('#ir-linha-atual').disabled=linhaFocoId===null;
  preencher('#detalhes-lote',[['Identificador da rodada',d.lote_id],['Contrato',d.contrato],['Modo',d.modo],['Publicação',d.pode_publicar===false?'Desligada':'Autorizada'],['Linhas interrompidas',numero(t.interrompidas)],['Impressão digital',d.fingerprint]]);
  renderizarLinhasFila();
}
function pontuacaoFinal(x){const nota=x.pontuacao_final??x.b1;if(nota!==null&&nota!==undefined&&nota!=='')return nota;return x.estado==='pendente'?'Aguardando processamento':'Pontuação não informada';}
function barrasCompactas(x){const barras=x.barras;if(!barras||typeof barras!=='object'||Array.isArray(barras))return {texto:'Barras não informadas',detalhe:''};const pares=Object.entries(barras);return {texto:pares.map(([,v])=>v).join(' · '),detalhe:pares.map(([k,v])=>k+': '+v).join(' · ')};}
function resultadoOuMotivo(x){if(x.estado!=='concluido')return {texto:x.motivo||x.erro||'Motivo não informado',detalhe:''};const partes=['Build calculada'];const detalhes=[];if(x.tecnico_rotulo)partes.push('técnico '+x.tecnico_rotulo);const barras=barrasCompactas(x);if(barras.texto!=='Barras não informadas'){partes.push(barras.texto);if(barras.detalhe)detalhes.push('Barras: '+barras.detalhe);}const habilidades=x.habilidades_adicionais_rotulo||[];if(habilidades.length){partes.push('habilidades: '+habilidades.join(', '));detalhes.push('Habilidades adicionadas: '+habilidades.join(', '));}return {texto:partes.join(' · '),detalhe:detalhes.join(' | ')};}
function botaoBuildCampea(x){if(x.estado!=='concluido')return '—';const chave=String(x.linha_id);buildsCampeasPorLinha.set(chave,x);return '<button type="button" class="ver-build-campea" data-linha-id="'+seguro(chave)+'">Ver build campeã</button>';}
function abrirBuildCampea(linhaId){const x=buildsCampeasPorLinha.get(String(linhaId));if(!x)return;const barras=barrasCompactas(x),habilidades=(x.habilidades_adicionais_rotulo||[]);$('#build-campea-aviso').textContent=(x.carta_rotulo||x.card_id)+' · '+(x.funcao_rotulo||('ID '+x.funcao_id))+' · '+(x.posicao_rotulo||('ID '+x.posicao_id));preencher('#build-campea-detalhe',[['Ímpeto condicional / nível',x.impeto_condicional_rotulo],['Barras vencedoras',barras.detalhe||'Não registradas'],['Técnico vencedor',x.tecnico_rotulo||'Não registrado'],['Habilidades adicionais vencedoras',habilidades.length?habilidades.join(' · '):'Nenhuma registrada'],['Ímpeto adicional',x.impeto_adicional_codigo===null||x.impeto_adicional_codigo===undefined?'Não registrado na saída persistida deste lote':x.impeto_adicional_codigo],['Pontuação final',pontuacaoFinal(x)],['Builds comparadas',buildsComparadas(x)],['Builds possíveis na linha',buildsPossiveis(x)]]);const dialog=$('#dialog-build-campea');if(typeof dialog.showModal==='function')dialog.showModal();else dialog.setAttribute('open','');}
function resultadosFiltrados(){const busca=normalizarBusca($('#filtro-resultados').value);return resultadosAtuais.filter(x=>linhaBateBusca(x,busca));}
function renderizarResultados(){
  const linhas=resultadosFiltrados(),paginas=Math.max(1,Math.ceil(linhas.length/TAMANHO_PAGINA));
  paginaResultados=Math.max(0,Math.min(paginaResultados,paginas-1));
  const inicio=paginaResultados*TAMANHO_PAGINA,fim=Math.min(inicio+TAMANHO_PAGINA,linhas.length),visiveis=linhas.slice(inicio,fim);
  $('#resumo-resultados').textContent=linhas.length?`${inicio+1}–${fim} de ${linhas.length} resultados`:'Nenhum resultado';
  $('#pagina-anterior-resultados').disabled=paginaResultados===0;
  $('#proxima-pagina-resultados').disabled=paginaResultados>=paginas-1;
  buildsCampeasPorLinha.clear();
  $('#linhas-resultados').innerHTML=visiveis.map(x=>{const resumo=resultadoOuMotivo(x);return '<tr><td>'+seguro(x.carta_rotulo||x.card_id)+'</td><td>'+seguro(x.funcao_rotulo||'ID '+x.funcao_id+' · catálogo ausente')+'</td><td>'+seguro(x.posicao_rotulo||'ID '+x.posicao_id+' · catálogo ausente')+'</td><td>'+seguro(x.impeto_condicional_rotulo)+'</td><td>'+seguro(rotuloEstado(x.estado))+'</td><td>'+seguro(pontuacaoFinal(x))+'</td><td class="tempo-resultado">'+seguro(duracaoFinalCompacta(x))+'</td><td>'+botaoBuildCampea(x)+'</td><td>'+buildsComparadasCompactas(x)+'</td><td>'+buildsPossiveisCompactas(x)+'</td><td><span class="resultado-resumo" title="'+seguro(resumo.detalhe)+'">'+seguro(resumo.texto)+'</span></td></tr>';}).join('')||'<tr><td colspan="11">Nenhum resultado final.</td></tr>';
}
function pintarResultados(d){$('#resultados-aviso').textContent=d.mensagem||'Nenhum resultado disponível.';resultadosAtuais=d.disponivel?(d.itens||[]):[];renderizarResultados();}
function pintarEventos(eventos){
  const ultimos=(eventos||[]).slice(-30).reverse();
  if(!ultimos.length){$('#eventos-fila').textContent='Nenhum evento registrado nesta rodada.';return;}
  $('#eventos-fila').textContent=ultimos.map(x=>{const quando=x.instante?new Date(x.instante).toLocaleString('pt-BR'):'horário não informado';return `${quando} · linha ${texto(x.linha_id)} · carta ${texto(x.card_id)} · ${rotuloEstado(x.estado)}`;}).join('\n');
}
async function atualizarFila(){if(atualizandoFila)return;atualizandoFila=true;const botao=$('#atualizar-fila'),textoOriginal=botao.textContent;botao.disabled=true;botao.textContent='Atualizando…';try{const s=await api('/api/fila/status');pintarFila(s);const [e,r]=await Promise.all([api('/api/fila/eventos'),api('/api/resultados')]);pintarResultados(r);pintarEventos(e.itens||[]);}catch(e){$('#fila-aviso').textContent=e.message;}finally{atualizandoFila=false;botao.disabled=false;botao.textContent=textoOriginal;agendarAtualizacaoFila(ultimoEstadoFila);}}
async function acaoFila(acao,corpo){const botao=acao==='iniciar'?$('#iniciar-fila'):acao==='pausar'?$('#pausar-fila'):acao==='parar'?$('#parar-fila'):null;const original=botao&&botao.textContent;if(botao){botao.disabled=true;botao.textContent=acao==='iniciar'?'Iniciando…':acao==='pausar'?'Pausando…':'Parando…';}$('#fila-aviso').textContent='Enviando comando de '+acao+' à fila produtiva V3…';try{const r=await fetch('/api/fila/'+acao,{method:'POST',cache:'no-store',headers:{'Content-Type':'application/json'},body:JSON.stringify(corpo||{})}),d=await r.json();if(!r.ok)throw new Error(d.erro||'Ação de fila indisponível');await atualizarFila();}catch(e){$('#fila-aviso').textContent=e.message;}finally{if(botao){botao.disabled=false;botao.textContent=original;}}}
function confirmarParar(){if(window.confirm('Parar esta fila produtiva V3? As linhas já concluídas serão preservadas como não publicadas; as pendentes serão marcadas como interrompidas. O Bonificador não será acionado automaticamente.'))acaoFila('parar',{confirmado:true});}
function apresentar(r,paridade){const c=r.carta,out=r.resultado||{};$('#resumo').innerHTML=r.ok?'<h3>Resultado — '+seguro(c.nome||c.card_id)+'</h3><p class="nota">Nota: '+seguro(out.nota)+'</p><p>Função '+seguro(r.funcao.nome)+' · Técnico '+seguro(r.tecnico.nome)+' · multiplicador '+seguro(r.tecnico.multiplicador)+'</p>':'<h3>Simulação bloqueada</h3><p class="aviso">'+seguro(texto(r.falhas||['gate recusou a avaliação']))+'</p>';preencher('#carta',[['Carta',(c.nome||'Sem nome')+' (#'+(c.card_id||'—')+')'],['Posição',c.posicao],['Overall',c.overall],['Orçamento',c.orcamento],['Dimensões por ID',JSON.stringify(c.dimensoes)],['Atributos',(c.atributos||[]).map(x=>(x.codigo||x.indice_otimizador)+': '+x.valor).join(' · ')],['Habilidades por ID',(c.habilidades||[]).map(h=>'#'+h.skill_id).join(', ')||'Nenhuma'],['Cardinalidades',JSON.stringify(c.cardinalidades)]]);preencher('#resultado',r.ok?[['Ímpeto condicional (ID)',texto(out.impeto_condicional_codigo)],['Nível do ímpeto',texto(out.impeto_condicional_nivel)],['Barras',JSON.stringify(out.barras)],['Gasto',out.gasto],['Sobra',out.sobra],['Boosts (índices)',texto(out.boost_indices)],['Habilidades escolhidas (IDs)',texto(out.habilidades)],['Ímpetos fabricados',texto(out.impetos_fabricados)],['Atributos em campo',texto(out.atributos_em_campo)]]:[['Contrato',r.regua.contrato],['Motivos',texto(r.falhas)]]);$('#gates').innerHTML=(r.gates||[]).map(g=>'<li class="'+(g.ok?'ok':'falha')+'">'+(g.ok?'✓':'×')+' <strong>'+seguro(g.nome)+'</strong> — '+seguro(JSON.stringify(g.detalhe))+'</li>').join('');preencher('#validacao',paridade?[['Paridade',paridade.ok?'Aprovada':'Reprovada'],['Tipo',paridade.tipo],['Vetor esperado',paridade.vetor_esperado_sha256],['Vetor calculado',paridade.vetor_calculado_sha256],['Rótulos',paridade.renomear_texto_nao_muda_calculo?'Não influenciam o cálculo':'Falha']]:[['Modo','Clique em Validar paridade para comparar a equação aprovada com o cálculo inline.'],['Contrato',r.regua.contrato],['Proveniência',r.proveniencia]]);$('#detalhes').hidden=false;}
async function executar(validar){const p=parametros();if(!p.card||!p.funcao||!p.tecnico)return;const b=validar?$('#validar'):$('#simular');b.disabled=true;b.textContent='Consultando…';try{const d=await api(caminho(validar?'/api/validar':'/api/simular'));apresentar(validar?d.simulacao:d,validar?d.paridade:null);}catch(e){$('#resumo').innerHTML='<h3>Resultado</h3><p class="falha">'+seguro(e.message)+'</p>';$('#detalhes').hidden=true;}finally{b.disabled=false;b.textContent=validar?'Validar paridade':'Simular';}}
async function carregar(){try{const x=await Promise.all([api('/api/saude'),api('/api/catalogos')]),s=x[0],c=x[1];$('#estado').textContent=s.pode_rodar?'Motor pronto':'Motor precisa de atenção';$('#estado').title=(s.contrato||'')+(s.versao_interface?' · interface '+s.versao_interface:'');$('#estado').className='selo '+(s.pode_rodar?'ok':'erro');$('#funcao').innerHTML=c.funcoes.map(x=>'<option value="'+x.funcao_id+'">'+seguro(x.nome)+' (#'+x.funcao_id+')</option>').join('');$('#tecnico').innerHTML=c.tecnicos.map(x=>'<option value="'+x.tecnico_id+'">'+seguro(x.nome)+' (#'+x.tecnico_id+' · '+seguro(x.proficiencia)+')</option>').join('');await atualizarFila();}catch(e){$('#estado').textContent='Motor indisponível';$('#estado').className='selo erro';$('#fila-aviso').textContent=e.message;}}
document.querySelectorAll('[data-aba]').forEach(x=>x.addEventListener('click',()=>trocarAba(x.dataset.aba)));
$('#simular').addEventListener('click',()=>executar(false));
$('#validar').addEventListener('click',()=>executar(true));
$('#iniciar-fila').addEventListener('click',()=>acaoFila('iniciar'));
$('#pausar-fila').addEventListener('click',()=>acaoFila('pausar'));
$('#parar-fila').addEventListener('click',confirmarParar);
$('#atualizar-fila').addEventListener('click',atualizarFila);
$('#ir-linha-atual').addEventListener('click',irParaAndamento);
$('#filtro-fila').addEventListener('input',()=>{paginaFila=0;renderizarLinhasFila();});
$('#filtro-estado-fila').addEventListener('change',()=>{paginaFila=0;renderizarLinhasFila();});
$('#pagina-anterior-fila').addEventListener('click',()=>{paginaFila--;renderizarLinhasFila();$('#rolagem-fila').scrollTop=0;});
$('#proxima-pagina-fila').addEventListener('click',()=>{paginaFila++;renderizarLinhasFila();$('#rolagem-fila').scrollTop=0;});
$('#filtro-resultados').addEventListener('input',()=>{paginaResultados=0;renderizarResultados();});
$('#pagina-anterior-resultados').addEventListener('click',()=>{paginaResultados--;renderizarResultados();});
$('#proxima-pagina-resultados').addEventListener('click',()=>{paginaResultados++;renderizarResultados();});
$('#card-id').addEventListener('keydown',e=>{if(e.key==='Enter')executar(false)});
$('#linhas-resultados').addEventListener('click',e=>{const botao=e.target.closest('.ver-build-campea');if(botao)abrirBuildCampea(botao.dataset.linhaId)});
$('#fechar-build-campea').addEventListener('click',()=>$('#dialog-build-campea').close());
carregar();
