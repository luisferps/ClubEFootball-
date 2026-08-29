'use strict';

(function instalarDiagnostico(global) {
  const fetchAnterior = global.fetch.bind(global);
  const eventos = [];
  let botao = null;

  function limitarTexto(valor, maximo) {
    const texto = String(valor == null ? '' : valor);
    return texto.length > maximo ? texto.slice(0, maximo) + '…' : texto;
  }

  function urlDaEntrada(input) {
    if (typeof input === 'string') return input;
    if (input && typeof input.url === 'string') return input.url;
    return '<url-indisponivel>';
  }

  function metodoDaEntrada(input, init) {
    return String((init && init.method) || (input && input.method) || 'GET').toUpperCase();
  }

  function enviarAoServidor(evento) {
    try {
      const corpo = new Blob([JSON.stringify(evento)], { type: 'application/json' });
      if (navigator.sendBeacon && navigator.sendBeacon('/api/client-log', corpo)) return;
    } catch (_) {}
  }

  function registrar(tipo, detalhe) {
    const evento = {
      instante: new Date().toISOString(),
      tipo,
      pagina: location.href,
      detalhe
    };
    eventos.push(evento);
    if (eventos.length > 80) eventos.shift();
    enviarAoServidor(evento);
    if (botao) {
      botao.textContent = 'ERRO — VER DIAGNÓSTICO';
      botao.style.background = '#7f1d1d';
      botao.style.borderColor = '#ef4444';
    }
  }

  global.fetch = async function fetchComDiagnostico(input, init) {
    const url = urlDaEntrada(input);
    const metodo = metodoDaEntrada(input, init);
    const inicio = performance.now();
    try {
      const resposta = await fetchAnterior(input, init);
      if (!resposta.ok) {
        registrar('fetch-http', {
          url,
          metodo,
          status: resposta.status,
          statusText: resposta.statusText,
          duracao_ms: Math.round(performance.now() - inicio)
        });
      }
      return resposta;
    } catch (erro) {
      const mensagemOriginal = erro && erro.message ? erro.message : String(erro);
      const detalhe = {
        url,
        metodo,
        nome: erro && erro.name ? erro.name : 'Error',
        mensagem: limitarTexto(mensagemOriginal, 2000),
        stack: limitarTexto(erro && erro.stack ? erro.stack : '', 8000),
        duracao_ms: Math.round(performance.now() - inicio),
        online: navigator.onLine
      };
      registrar('fetch-transporte', detalhe);
      throw new TypeError('Falha de transporte em ' + url + ': ' + mensagemOriginal);
    }
  };

  global.addEventListener('error', function (evento) {
    registrar('javascript-error', {
      mensagem: limitarTexto(evento.message || 'erro sem mensagem', 2000),
      arquivo: evento.filename || '',
      linha: evento.lineno || 0,
      coluna: evento.colno || 0,
      stack: limitarTexto(evento.error && evento.error.stack ? evento.error.stack : '', 8000)
    });
  });

  global.addEventListener('unhandledrejection', function (evento) {
    const razao = evento.reason;
    registrar('promise-rejeitada', {
      mensagem: limitarTexto(razao && razao.message ? razao.message : razao, 2000),
      stack: limitarTexto(razao && razao.stack ? razao.stack : '', 8000)
    });
  });

  function criarModal() {
    const fundo = document.createElement('div');
    fundo.id = 'clubef-diagnostico-modal';
    fundo.style.cssText = [
      'position:fixed', 'inset:0', 'z-index:2147483647',
      'background:rgba(2,6,23,.88)', 'display:flex',
      'align-items:center', 'justify-content:center', 'padding:24px'
    ].join(';');

    const caixa = document.createElement('div');
    caixa.style.cssText = [
      'width:min(1100px,96vw)', 'max-height:90vh', 'overflow:auto',
      'background:#0b1220', 'color:#e5e7eb', 'border:1px solid #334155',
      'border-radius:14px', 'padding:18px', 'box-shadow:0 24px 80px rgba(0,0,0,.55)'
    ].join(';');

    const titulo = document.createElement('h2');
    titulo.textContent = 'Diagnóstico do Extrator';
    titulo.style.margin = '0 0 12px';

    const estado = document.createElement('div');
    estado.textContent = 'Carregando o diagnóstico…';
    estado.style.cssText = 'font:14px/1.5 ui-monospace,Consolas,monospace;white-space:pre-wrap;word-break:break-word;background:#020617;padding:14px;border-radius:10px;min-height:180px';

    const acoes = document.createElement('div');
    acoes.style.cssText = 'display:flex;gap:10px;justify-content:flex-end;margin-top:14px;flex-wrap:wrap';

    const copiar = document.createElement('button');
    copiar.type = 'button';
    copiar.textContent = 'Copiar diagnóstico';
    copiar.style.cssText = 'padding:10px 14px;border-radius:9px;border:1px solid #10b981;background:#064e3b;color:white;font-weight:700;cursor:pointer';
    copiar.onclick = async function () {
      try {
        await navigator.clipboard.writeText(estado.textContent || '');
        copiar.textContent = 'Copiado';
      } catch (_) {
        copiar.textContent = 'Não consegui copiar';
      }
    };

    const fechar = document.createElement('button');
    fechar.type = 'button';
    fechar.textContent = 'Fechar';
    fechar.style.cssText = 'padding:10px 14px;border-radius:9px;border:1px solid #64748b;background:#1e293b;color:white;font-weight:700;cursor:pointer';
    fechar.onclick = function () { fundo.remove(); };

    acoes.append(copiar, fechar);
    caixa.append(titulo, estado, acoes);
    fundo.append(caixa);
    fundo.addEventListener('click', function (evento) {
      if (evento.target === fundo) fundo.remove();
    });
    document.body.append(fundo);

    fetchAnterior('/api/diagnostico', { cache: 'no-store' })
      .then(async function (resposta) {
        const texto = await resposta.text();
        let servidor;
        try { servidor = JSON.parse(texto); }
        catch (_) { servidor = { erro: 'Resposta de diagnóstico inválida', resposta: texto }; }
        estado.textContent = JSON.stringify({ servidor, eventos_do_navegador: eventos }, null, 2);
      })
      .catch(function (erro) {
        estado.textContent = JSON.stringify({
          erro: 'Não foi possível consultar /api/diagnostico',
          mensagem: erro && erro.message ? erro.message : String(erro),
          eventos_do_navegador: eventos
        }, null, 2);
      });
  }

  function criarBotao() {
    if (document.getElementById('clubef-open-diagnostico')) return;
    botao = document.createElement('button');
    botao.id = 'clubef-open-diagnostico';
    botao.type = 'button';
    botao.textContent = 'VER DIAGNÓSTICO';
    botao.style.cssText = [
      'position:fixed', 'left:18px', 'bottom:18px', 'z-index:2147483646',
      'padding:11px 15px', 'border-radius:10px', 'border:1px solid #22d3ee',
      'background:#083344', 'color:#ecfeff', 'font-weight:800', 'cursor:pointer',
      'box-shadow:0 10px 30px rgba(0,0,0,.35)'
    ].join(';');
    botao.onclick = criarModal;
    document.body.append(botao);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', criarBotao, { once: true });
  } else {
    criarBotao();
  }
})(globalThis);
