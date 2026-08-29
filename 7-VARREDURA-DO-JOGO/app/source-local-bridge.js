'use strict';

// Ponte mínima: localizar/ler CPK no disco é uma operação LOCAL e não depende
// do Supabase. O contrato continua sendo exigido depois, na validação/extração.
(function installLocalSourceBridge(global) {
  const nativeFetch = global.fetch.bind(global);
  let contractSeal = null;

  function cacheSeal(payload) {
    if (!payload || typeof payload !== 'object') return;
    const keys = [
      'contrato_id',
      'versao_jogo',
      'versao_contrato',
      'fingerprint_contrato_sha256',
      'fingerprint_fontes_sha256',
      'fingerprint_catalogos_sha256'
    ];
    if (keys.every((key) => typeof payload[key] === 'string' && payload[key])) {
      contractSeal = Object.fromEntries(keys.map((key) => [key, payload[key]]));
    }
  }

  function withContractHeaders(response) {
    if (!contractSeal) return response;
    const headers = new Headers(response.headers);
    headers.set('X-Clubef-Contract-Id', contractSeal.contrato_id);
    headers.set('X-Clubef-Contract-Version', contractSeal.versao_contrato);
    headers.set('X-Clubef-Contract-Fingerprint', contractSeal.fingerprint_contrato_sha256);
    headers.set('X-Clubef-Sources-Fingerprint', contractSeal.fingerprint_fontes_sha256);
    headers.set('X-Clubef-Catalogs-Fingerprint', contractSeal.fingerprint_catalogos_sha256);
    return response.arrayBuffer().then((body) => new Response(body, {
      status: response.status,
      statusText: response.statusText,
      headers
    }));
  }

  global.fetch = async function sourceAwareFetch(input, init) {
    const url = typeof input === 'string' ? input : (input && input.url ? input.url : '');

    if (url === '/api/reading-contract/current') {
      const response = await nativeFetch(input, init);
      try {
        cacheSeal(await response.clone().json());
      } catch (_) {}
      return response;
    }

    if (url.startsWith('/api/sources/status')) {
      const response = await nativeFetch(url.replace('/api/sources/status', '/local-sources/status'), init);
      return withContractHeaders(response);
    }

    if (url.startsWith('/api/sources/file')) {
      const response = await nativeFetch(url.replace('/api/sources/file', '/local-sources/file'), init);
      return withContractHeaders(response);
    }

    return nativeFetch(input, init);
  };
})(globalThis);
