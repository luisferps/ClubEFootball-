/* Porta pública da busca do Site Novo. Não importa consultas ou adaptadores aposentados. */
(() => {
  'use strict';
  const endpoint = '/rest/v1/rpc/site_novo_busca_v1';
  const hasText = value => typeof value === 'string' && value.trim().length > 0;
  const integer = value => Number.isSafeInteger(value) && value >= 0;
  function validate(data, request) {
    const fail = () => { throw new Error('Resposta da busca incompatível.'); };
    if (!data || data.contrato !== 'site-novo-busca-v1' || data.versao !== 1 || !['pronto', 'vazio'].includes(data.status)) fail();
    if (data.busca !== request.p_busca.trim() || data.degrau !== request.p_degrau || data.limite !== request.p_limite || data.offset !== request.p_offset || !integer(data.total) || typeof data.tem_mais !== 'boolean' || !Array.isArray(data.itens)) fail();
    if (data.itens.length !== Math.min(data.limite, Math.max(0, data.total - data.offset)) || data.tem_mais !== (data.total > data.offset + data.limite) || (data.status === 'vazio') !== (data.itens.length === 0)) fail();
    const seen = new Set();
    data.itens.forEach(item => {
      if (!item || typeof item.card_id !== 'string' || !/^[1-9][0-9]*$/.test(item.card_id) || !hasText(item.nome) || seen.has(item.card_id)) fail();
      if (item.foto_url !== null && typeof item.foto_url !== 'string') fail();
      if (item.box !== null && typeof item.box !== 'string') fail();
      if (item.pontuacao_total !== null && (typeof item.pontuacao_total !== 'number' || !Number.isFinite(item.pontuacao_total))) fail();
      if (item.posicao !== null && typeof item.posicao !== 'string') fail();
      seen.add(item.card_id);
    });
    return data;
  }
  async function read(request, signal) {
    const data = await window.SiteNovoCommon.request(endpoint,request,{signal,retries:1,errorMessage:'Não foi possível fazer a busca. Tente novamente.'});
    return validate(data,request);
  }
  window.SiteNovoSearchAPI = Object.freeze({ read, validate });
})();
