/* ===========================================================================
   arows-sob-demanda.js  —  leitura canônica sob demanda
   ---------------------------------------------------------------------------
   POR QUE ESTE ARQUIVO EXISTE

   A `linha` gravada no banco pesa 32 MB no total. Medido chave por chave:

       arows .... 26,5%
       falta .... 20,6%
       o resto .. 52,9%

   (44 MB de JSON no total, medido com octet_length no texto que trafega —
    nao com pg_column_size, que conta o jsonb comprimido e engana.)

   E `arows` so e lido quando o card e ABERTO (a ficha, o otimizador, o
   recalculo). A lista nunca precisa dele. Ou seja: a tela baixava 30 MB para
   desenhar uma lista que nao usa nem um byte deles.

   O QUE ESTE ARQUIVO FAZ

   Instala em cada linha carregada as propriedades `arows` e `falta`, que só
   vão ao read-model publicado
   na PRIMEIRA vez que alguém lê. Quem lê não muda nada: continua escrevendo
   `c.arows` como sempre escreveu. Nenhuma das 193 funcoes da tela foi tocada.

   Quando a primeira leitura acontece, ele traz o card INTEIRO de uma vez
   (todas as funcoes daquele card) e ja preenche todas — porque quem abre a
   ficha de um card costuma ver mais de uma funcao dele.

   ⛔ POR QUE SINCRONO. `notaDe(vals, c.arows)` e sincrono, e esta escrito em
      dezenas de lugares. Um getter nao pode devolver promessa sem quebrar
      todos eles. A propria carga inicial da tela ja usa XHR sincrono pelo
      mesmo motivo (motor-e-ficha-base.js, funcao `pedeSync`). Aqui o pedido e
      de UM card (~5 KB, ~120 ms medidos) e acontece uma vez por card.

   A origem é exclusivamente ClubeNovoReadModel. Se a projeção não existir ou
   a build não estiver publicada, a linha não recebe dados substitutos.
   =========================================================================== */
(function () {
  'use strict';

  var cache   = {};   // card_id -> { funcao_codigo: arows }
  var pedidos = 0;
  var servidos = 0;

  function buscaCard(cardId) {
    if (cache[cardId]) return cache[cardId];
    var mapa = {};
    try {
      if (!window.ClubeNovoReadModel) throw new Error('read-model canônico indisponível');
      var linhas = window.ClubeNovoReadModel.cardSync(cardId);
      pedidos++;
      for (var i = 0; i < linhas.length; i++) {
        var linha=linhas[i], meta=linha.__cn||{};
        var par = { arows: linha.arows, falta: linha.falta };
        if (meta.functionId != null) mapa[String(meta.functionId)] = par;
        if (linha.funcao_codigo != null) mapa[String(linha.funcao_codigo)] = par;
        if (linha.tipo != null) mapa[String(linha.tipo)] = par;
      }
      servidos += linhas.length;
    } catch (e) {
      console.warn('[arows] falhou o card ' + cardId + ': ' + e);
    }
    cache[cardId] = mapa;
    return mapa;
  }

  /* Instala o getter numa linha. Idempotente: se ela ja tem `arows` de
     verdade (linha antiga, ou ja resolvida), nao faz nada. */
  function instala(L) {
    if (!L || typeof L !== 'object') return;
    if (L.__arowsPronto) return;
    var proprio = Object.getOwnPropertyDescriptor(L, 'arows');
    if (proprio && proprio.get) { L.__arowsPronto = 1; return; }
    var fal = Object.getOwnPropertyDescriptor(L, 'falta');
    if (proprio && Array.isArray(proprio.value)
        && fal && Array.isArray(fal.value)) {
      L.__arowsPronto = 1; return;      // veio inteira do contrato canônico
    }
    var cardId = L.id;
    /* ⛔ A `linha` gravada NAO tem `funcao_codigo`. O que ela tem e `tipo`,
       que e exatamente o `funcao.rotulo` (conferido: 19 de 19, 1 para 1).
       Por isso procuramos pelos dois — e a view devolve os dois. */
    var meta=L.__cn||{};
    var codigo = (meta.functionId !== undefined && meta.functionId !== null)
               ? String(meta.functionId)
               : ((L.funcao_codigo !== undefined && L.funcao_codigo !== null)
                 ? String(L.funcao_codigo)
                 : (L.tipo !== undefined && L.tipo !== null ? String(L.tipo) : null));
    if (cardId === undefined || cardId === null) { L.__arowsPronto = 1; return; }

    var guardado = { arows: null, falta: null };

    function traz(qual) {
      if (guardado[qual] !== null) return guardado[qual];
      var mapa = buscaCard(cardId), par = null;
      if (codigo !== null && mapa[codigo] !== undefined) {
        par = mapa[codigo];
      } else {
        /* sem chave de funcao na linha: cai para a unica que veio, ou vazio */
        var chaves = Object.keys(mapa);
        par = (chaves.length === 1) ? mapa[chaves[0]] : null;
      }
      if(!par)throw new Error('Build publicada sem detalhe canônico para a função.');
      var v = par[qual];
      if (!Array.isArray(v)) throw new Error('Build publicada sem ' + qual + ' declarado.');
      guardado[qual] = v;
      return v;
    }

    function poe(qual) {
      var jaTinha = Object.getOwnPropertyDescriptor(L, qual);
      if (jaTinha && Array.isArray(jaTinha.value)) return;
      Object.defineProperty(L, qual, {
        configurable: true,
        enumerable: true,
        get: function () { return traz(qual); },
        set: function (v) { guardado[qual] = v; }   // quem grava, grava
      });
    }

    try {
      poe('arows');
      poe('falta');
      L.__arowsPronto = 1;
    } catch (e) {
      L.__arowsPronto = 1;
    }
  }

  function varre() {
    var d = null;
    try { d = (typeof D !== 'undefined') ? D : (window.D || null); } catch (e) { d = window.D || null; }
    if (!Array.isArray(d)) return 0;
    var n = 0;
    for (var i = 0; i < d.length; i++) {
      if (d[i] && !d[i].__arowsPronto) { instala(d[i]); n++; }
    }
    return n;
  }

  /* Varre agora, a cada leva que chega, e quando o carregamento fecha. */
  varre();
  var timer = setInterval(varre, 400);
  try {
    window.addEventListener('encaixe:dados-completos', function () {
      varre();
      clearInterval(timer);
      setTimeout(varre, 1500);     // rede de seguranca
      console.log('[arows] sob demanda ligado — ' + pedidos + ' cards pedidos ate aqui');
    });
  } catch (e) {}
  document.addEventListener('DOMContentLoaded', varre);

  window.AROWS = {
    varre: varre,
    pedidos: function () { return pedidos; },
    linhasServidas: function () { return servidos; },
    cache: function () { return cache; },
    aquece: function (cardId) { return buscaCard(cardId); }
  };
})();
