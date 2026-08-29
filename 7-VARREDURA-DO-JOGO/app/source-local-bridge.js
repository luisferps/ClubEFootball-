'use strict';

// Ponte mínima: localizar/ler CPK no disco é uma operação LOCAL e não depende
// do Supabase. O contrato continua sendo exigido depois, na validação/extração.
(function installLocalSourceBridge(global) {
  const nativeFetch = global.fetch.bind(global);
  let contractSeal = null;
  let readQueue = Promise.resolve();

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

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
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers
    });
  }

  async function fetchGetWithRetry(input, init) {
    let lastError = null;
    for (let attempt = 0; attempt < 3; attempt += 1) {
      try {
        return await nativeFetch(input, init);
      } catch (error) {
        lastError = error;
        if (attempt < 2) await sleep(250 * (attempt + 1));
      }
    }
    throw lastError || new TypeError('Failed to fetch');
  }

  function enqueueRead(task) {
    const current = readQueue.then(task, task);
    readQueue = current.catch(() => undefined);
    return current;
  }

  global.fetch = async function sourceAwareFetch(input, init) {
    const url = typeof input === 'string' ? input : (input && input.url ? input.url : '');
    const method = String((init && init.method) || (input && input.method) || 'GET').toUpperCase();

    if (url === '/api/reading-contract/current') {
      const response = await fetchGetWithRetry(input, init);
      try {
        cacheSeal(await response.clone().json());
      } catch (_) {}
      return response;
    }

    if (url.startsWith('/api/sources/status')) {
      const localUrl = url.replace('/api/sources/status', '/local-sources/status');
      return withContractHeaders(await fetchGetWithRetry(localUrl, init));
    }

    if (url.startsWith('/api/sources/file')) {
      const localUrl = url.replace('/api/sources/file', '/local-sources/file');
      return withContractHeaders(await fetchGetWithRetry(localUrl, init));
    }

    // As consultas GET protegidas podem ser pesadas (baseline de cartas,
    // referência de metadados). Fazemos uma de cada vez e repetimos somente
    // falhas de transporte. POST nunca é repetido automaticamente.
    if (method === 'GET' && url.startsWith('/api/')) {
      return enqueueRead(() => fetchGetWithRetry(input, init));
    }

    return nativeFetch(input, init);
  };
})(globalThis);
