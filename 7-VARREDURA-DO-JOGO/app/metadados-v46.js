'use strict';

(function installMetadataV46(global) {
  const PANEL_ID = 'clubef-metadata-v46-panel';
  const CONFIRMATION = 'APLICAR METADADOS PRIMEIRO';

  function createPanel() {
    if (document.getElementById(PANEL_ID)) return document.getElementById(PANEL_ID);
    const panel = document.createElement('section');
    panel.id = PANEL_ID;
    panel.style.cssText = [
      'position:fixed', 'right:18px', 'bottom:18px', 'z-index:9999',
      'width:min(390px,calc(100vw - 36px))', 'padding:14px',
      'border:1px solid rgba(127,127,127,.35)', 'border-radius:14px',
      'background:rgba(18,22,28,.96)', 'color:#fff',
      'box-shadow:0 12px 36px rgba(0,0,0,.35)', 'font:14px/1.4 system-ui,sans-serif'
    ].join(';');
    panel.innerHTML = `
      <div style="font-weight:800;margin-bottom:6px">Etapa 1 · Metadados antes dos cards</div>
      <div id="clubef-metadata-v46-status" style="opacity:.85;margin-bottom:10px">Aguardando a comparação física de clube, liga, nacionalidade e tipo…</div>
      <button id="clubef-metadata-v46-apply" type="button" disabled style="width:100%;padding:10px 12px;border:0;border-radius:10px;font-weight:800;cursor:pointer">Aplicar metadados e vínculos</button>
      <div id="clubef-metadata-v46-result" style="margin-top:8px;font-size:12px;opacity:.85"></div>`;
    document.body.appendChild(panel);
    document.getElementById('clubef-metadata-v46-apply').addEventListener('click', applyCached);
    return panel;
  }

  async function currentSeal() {
    const response = await fetch('/api/reading-contract/current', { cache: 'no-store' });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    const keys = ['contrato_id', 'versao_jogo', 'versao_contrato', 'fingerprint_contrato_sha256', 'fingerprint_fontes_sha256', 'fingerprint_catalogos_sha256'];
    return Object.fromEntries(keys.map((key) => [key, payload[key]]));
  }

  async function refreshStatus() {
    createPanel();
    const status = document.getElementById('clubef-metadata-v46-status');
    const button = document.getElementById('clubef-metadata-v46-apply');
    try {
      const response = await fetch('/api/card-dimensions/cached-status', { cache: 'no-store' });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
      if (!payload.ready) {
        status.textContent = 'Aguardando a aba Metadados terminar a leitura física de clube, liga, nacionalidade e tipo.';
        button.disabled = true;
        return;
      }
      const counts = payload.source_counts || {};
      status.textContent = `Fotografia pronta: ${Number(counts.cards || 0).toLocaleString('pt-BR')} cards · ${Number(counts.clubs || 0).toLocaleString('pt-BR')} clubes · ${Number(counts.leagues || 0).toLocaleString('pt-BR')} ligas.`;
      button.disabled = !payload.apply_available;
      if (!payload.apply_available) document.getElementById('clubef-metadata-v46-result').textContent = 'A conexão de escrita local ainda não está disponível.';
    } catch (error) {
      status.textContent = `Metadados ainda não prontos: ${error.message}`;
      button.disabled = true;
    }
  }

  async function applyCached() {
    const button = document.getElementById('clubef-metadata-v46-apply');
    const resultBox = document.getElementById('clubef-metadata-v46-result');
    if (!global.confirm('Aplicar primeiro os catálogos de nacionalidade, clube, liga e tipo e depois os vínculos físicos dos cards? Nenhum registro será apagado.')) return;
    button.disabled = true;
    button.textContent = 'Aplicando metadados…';
    resultBox.textContent = 'Transação em andamento. Não feche o extrator.';
    try {
      const seal = await currentSeal();
      const response = await fetch('/api/card-dimensions/apply-cached', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ confirmation: CONFIRMATION, leitura_contrato: seal })
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
      const catalogs = payload.result && payload.result.catalogs ? payload.result.catalogs : {};
      const cards = payload.result && payload.result.cards ? payload.result.cards : {};
      resultBox.textContent = `Concluído: ${Number(catalogs.clubs || 0).toLocaleString('pt-BR')} clubes · ${Number(catalogs.leagues || 0).toLocaleString('pt-BR')} ligas · ${Number(cards.updated || 0).toLocaleString('pt-BR')} cards vinculados. ${cards.pending_card_insert ? `${cards.pending_card_insert} cards ainda não existem na tabela e serão reconciliados após a carga de cards.` : 'Readback disponível.'}`;
      button.textContent = 'Metadados aplicados · comparar novamente';
      setTimeout(refreshStatus, 1200);
    } catch (error) {
      resultBox.textContent = `BLOQUEADO: ${error.message}`;
      button.disabled = false;
      button.textContent = 'Tentar aplicar metadados novamente';
    }
  }

  createPanel();
  refreshStatus();
  global.setInterval(refreshStatus, 2500);
})(globalThis);
