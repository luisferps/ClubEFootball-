const $ = (s) => document.querySelector(s);
const texto = (v) => Array.isArray(v) ? (v.length ? v.join(', ') : 'Nenhum') : (v === null || v === undefined || v === '' ? 'Não informado' : String(v));
const seguro = (v) => texto(v).replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(caminho) { const r = await fetch(caminho, {cache:'no-store'}); const d = await r.json(); if (!r.ok || d.ok === false) throw new Error(d.erro || 'Consulta local indisponível'); return d; }
async function acaoPipeline(caminho) { const r = await fetch(caminho, {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'}); const d = await r.json(); if (!r.ok || d.ok === false) throw new Error(d.erro || 'Ação local indisponível'); return d.pipeline; }
function preencher(id, pares) { const alvo = $(id); alvo.innerHTML = ''; for (const [nome, valor] of pares) { const d=document.importNode($('#linha').content,true); d.querySelector('dt').textContent=nome; d.querySelector('dd').innerHTML=seguro(valor); alvo.append(d); } }
function valorBonus(v) { return typeof v === 'number' ? v.toFixed(4) : 'Bloqueado'; }
function mostrarPipeline(p) { const ativo=!!p.ativo, aguardando=!!p.aguardando; const estado=p.estado || 'desconhecido'; const textoEstado=`${estado}${aguardando ? ' — aguardando novas linhas do Otimizador' : ''} · ${p.mensagem || 'Sem mensagem'}${typeof p.confirmados==='number' ? ` · ${p.confirmados} confirmado(s) na última rodada` : ''}`; $('#pipeline-estado').textContent=textoEstado; $('#iniciar-pipeline').disabled=ativo; $('#parar-pipeline').disabled=!ativo; $('#iniciar-pipeline').textContent=ativo ? 'Bonificador em execução' : 'Iniciar Bonificador'; }
async function atualizarPipeline() { try { mostrarPipeline((await api('/api/pipeline/estado')).pipeline); } catch(e) { $('#pipeline-estado').textContent=`Controle do pipeline indisponível: ${e.message}`; } }
async function iniciarPipeline() { try { mostrarPipeline(await acaoPipeline('/api/pipeline/iniciar')); } catch(e) { $('#pipeline-estado').textContent=`Não foi possível iniciar: ${e.message}`; } }
async function pararPipeline() { try { mostrarPipeline(await acaoPipeline('/api/pipeline/parar')); } catch(e) { $('#pipeline-estado').textContent=`Não foi possível parar: ${e.message}`; } }
async function carregar() {
  try {
    const [saude, funcoes] = await Promise.all([api('/api/saude'), api('/api/funcoes')]);
    $('#estado').textContent=`Contrato ${saude.contrato} · ${saude.pode_rodar ? 'apto' : 'bloqueado'}`; $('#estado').className=`selo ${saude.pode_rodar ? 'ok' : 'erro'}`;
    $('#funcao').innerHTML = funcoes.funcoes.map(f => `<option value="${f.id}">${seguro(f.nome)} (#${f.id})</option>`).join('') || '<option>Sem função apta</option>';
  } catch (e) { $('#estado').textContent='Contrato indisponível'; $('#estado').className='selo erro'; $('#resumo').innerHTML=`<h2>Resultado</h2><p class="falha">${seguro(e.message)}</p>`; }
}
async function simular() {
  const card = $('#card-id').value.trim(), funcao=$('#funcao').value;
  if (!card || !funcao) return;
  $('#simular').disabled=true; $('#simular').textContent='Consultando…';
  try {
    const r=await api(`/api/simular?card_id=${encodeURIComponent(card)}&funcao_id=${encodeURIComponent(funcao)}`), c=r.carta, b=r.bonus;
    $('#resumo').innerHTML=`<h2>Resultado — ${seguro(c.nome || c.card_id)}</h2><p class="${r.ok?'bonus':'aviso'}">Bônus total: ${seguro(valorBonus(b.total))}</p><p>Corpo ${seguro(valorBonus(b.corpo))} · pé ruim ${seguro(valorBonus(b.pe_ruim))} · playstyle ${seguro(valorBonus(b.estilo))} · IA ${seguro(valorBonus(b.ia))}</p>`;
    preencher('#carta', [['Carta', `${c.nome || 'Sem nome'} (${c.card_id || card})`],['Corpo',texto(c.corpo)],['Pé ruim — uso',texto(c.pe_ruim_uso)],['Pé ruim — precisão',texto(c.pe_ruim_precisao)],['Posição principal',`${c.posicao.codigo || 'Não informada'} (#${c.posicao.id || '—'})`],['Playstyle 1',`${c.playstyles[0].nome || 'Não informado'} (#${c.playstyles[0].id || '—'})`],['Playstyle 2',`${c.playstyles[1].nome || 'Não informado'} (#${c.playstyles[1].id || '—'})`],['Estilo de IA',texto(c.estilos_ia)],['Cardinalidades',JSON.stringify(c.cardinalidades)]]);
    const moldeResumo=Object.entries(r.molde).map(([medida,regra])=>`${medida}: peso ${regra.peso}; direção ${regra.direcao}; cortes ${texto(regra.cortes)}`).join(' · ');
    const parResumo=Object.entries(r.regua.parametros).map(([nome,valor])=>`${nome}: ${valor}`).join(' · ');
    preencher('#regra', [['Função',`${r.funcao.nome} (#${r.funcao.id})`],['Molde corporal',moldeResumo],['Slot que manda',r.regra_estilo.slot_que_manda],['Playstyle proprietário',`#${r.regra_estilo.playstyle_dono || '—'}`],['Playstyle complementar',`#${r.regra_estilo.playstyle_complementar || '—'}`],['Casa por função',`#${r.regra_estilo.funcao_casa_id || '—'}`],['Complementar ativo',r.regra_estilo.complementar_ativa_na_posicao ? 'Sim' : 'Não'],['Parâmetros da régua',parResumo]]);
    $('#gates').innerHTML=r.gates.map(g=>`<li class="${g.ok?'ok':'falha'}">${g.ok?'✓':'×'} <strong>${seguro(g.nome)}</strong> — ${seguro(texto(g.detalhe))}</li>`).join('');
    const a=await api('/api/auditoria'); preencher('#auditoria', [['Versão',a.auditoria.contrato],['Régua apta',a.auditoria.regua_apta?'Sim':'Não'],['Paridade',a.auditoria.paridade],['Acesso',a.auditoria.acesso],['Fingerprint do motor',a.auditoria.motor_sha256],['Proveniência',JSON.stringify(a.auditoria.proveniencia)],['Faltas',texto(a.auditoria.falta_o_que)]]);
    $('#detalhes').hidden=false;
  } catch(e) { $('#resumo').innerHTML=`<h2>Resultado</h2><p class="falha">${seguro(e.message)}</p>`; $('#detalhes').hidden=true; }
  finally { $('#simular').disabled=false; $('#simular').textContent='Simular bônus'; }
}
$('#simular').addEventListener('click',simular); $('#card-id').addEventListener('keydown',(e)=>{if(e.key==='Enter')simular()}); carregar();
$('#iniciar-pipeline').addEventListener('click',iniciarPipeline); $('#parar-pipeline').addEventListener('click',pararPipeline); atualizarPipeline(); setInterval(atualizarPipeline,1000);
