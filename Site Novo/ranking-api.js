/* Porta publica do Ranking. Nao importa adaptadores ou motores legados. */
(() => {
 'use strict';
 const endpoint = 'https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/rpc/site_novo_ranking_v1';
 const key = 'sb_publishable_XTKGboY9RyYiirPiIsWMhw_P8B51cHj';
 const id = value => typeof value === 'string' && /^[1-9][0-9]*$/.test(value);
 const text = value => typeof value === 'string' && value.trim().length > 0;
 const integer = value => Number.isSafeInteger(value) && value >= 0;
 function validate(data, request) {
  const invalid = () => { throw new Error('Resposta do Ranking incompatível.'); };
  if (!data || data.contrato !== 'site-novo-ranking-v1' || data.versao !== 1 || !['pronto','vazio'].includes(data.status)) invalid();
  if (data.modo !== request.p_modo || data.setor !== request.p_setor || data.offset !== request.p_offset || data.limite !== request.p_limite || !integer(data.total) || typeof data.tem_mais !== 'boolean' || !Array.isArray(data.itens) || data.itens.length > data.limite) invalid();
  if ((data.status === 'vazio') !== (data.itens.length === 0)) invalid();
  if (data.tem_mais !== (data.total > data.offset + data.limite) || data.itens.length !== Math.min(data.limite, Math.max(0, data.total-data.offset))) invalid();
  const seen = new Set();
  data.itens.forEach((item, index) => {
   if (!item || !id(item.card_id) || !id(item.linha_id) || !id(item.jogador_id) || !id(item.funcao_id) || !text(item.nome) || !text(item.funcao) || !text(item.posicao) || !integer(item.posicao_id) || !['goleiro','defesa','meio','ataque'].includes(item.setor) || typeof item.nota_final !== 'number' || !Number.isFinite(item.nota_final) || !text(item.publicada_em) || !Number.isFinite(Date.parse(item.publicada_em)) || item.classificacao !== data.offset+index+1 || seen.has(item.linha_id)) invalid();
   if (item.foto_url !== null && typeof item.foto_url !== 'string') invalid();
   if (!Array.isArray(item.boxes) || item.boxes.some(b=>!b||!text(b.nome)||typeof b.em_andamento!=='boolean')) invalid();
   if (!Array.isArray(item.estilos) || item.estilos.some(s=>!s||!integer(s.id)||!text(s.nome))) invalid();
   seen.add(item.linha_id);
  });
  const catalog = data.catalogo;
  if (!catalog || !Array.isArray(catalog.funcoes) || !Array.isArray(catalog.posicoes) || !Array.isArray(catalog.estilos)) invalid();
  catalog.funcoes.forEach(f => { if (!id(f.id) || !text(f.nome) || !['goleiro','defesa','meio','ataque'].includes(f.setor)) invalid(); });
  for (const list of [catalog.posicoes,catalog.estilos]) list.forEach(v => { if (!integer(v.id) || !text(v.nome)) invalid(); });
  return data;
 }
 async function read(request, signal) {
  // O estado visual (por exemplo, eixo) não pertence à assinatura pública.
  const parameters = {};
  for (const name of ['p_modo','p_setor','p_funcao_id','p_busca','p_posicao_nativa_id','p_estilo_id','p_offset','p_limite','p_degrau']) {
   if (Object.prototype.hasOwnProperty.call(request,name)) parameters[name] = request[name];
  }
  const response = await fetch(endpoint, { method:'POST', headers:{ 'Content-Type':'application/json', apikey:key }, body:JSON.stringify(parameters), signal, cache:'no-store' });
  if (!response.ok) throw new Error(response.status === 400 ? 'Confira os filtros informados.' : 'Não foi possível consultar o Ranking. Tente novamente.');
  const data=validate(await response.json(), request);if(data.degrau!==(request.p_degrau??3))throw new Error('Degrau do Ranking incompatível.');return data;
 }
 window.SiteNovoRankingAPI = Object.freeze({ read, validate });
})();
