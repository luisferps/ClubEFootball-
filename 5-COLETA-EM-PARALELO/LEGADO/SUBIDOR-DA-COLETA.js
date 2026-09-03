/* =========================================================================
   SUBIDOR DA COLETA — leva os lotes da pasta para dentro do banco.

   É o caminho de volta do coletor: ele grava na pasta, este lê a pasta e
   entrega na CAIXA DE ENTRADA do banco (clube.recebimento), pela porta
   public.receber_lote — que só ACEITA. Ninguém lê nada por ela.

   COMO USAR
     1. abra https://efhub.com/pt-BR/players  (qualquer página serve; é só
        para ter um Console — o subidor não toca no eFHUB)
     2. F12 → Console → cole este arquivo inteiro → Enter
     3. quando ele pedir, escolha a pasta "Resultado da Coleta"

   Pode rodar com o coletor rodando: ele só LÊ os lotes já fechados, e o
   banco ignora o que já recebeu (confere card_id + sha256). Rodar duas
   vezes não duplica nada.
   ========================================================================= */
(async function () {
  'use strict';

  var URL_BANCO = 'https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/rpc/receber_lote';
  var CHAVE = 'sb_publishable_XTKGboY9RyYiirPiIsWMhw_P8B51cHj';
  var POR_VEZ = 400;          // o banco aceita até 500 por chamada
  var FONTE = 'efhub';

  function log(t, cor) {
    console.log('%c' + t, 'font-weight:600;color:' + (cor || '#22c58b'));
  }

  async function manda(lote, itens) {
    var r = await fetch(URL_BANCO, {
      method: 'POST',
      headers: { 'apikey': CHAVE, 'Authorization': 'Bearer ' + CHAVE,
                 'Content-Type': 'application/json' },
      body: JSON.stringify({ p_lote: lote, p_fonte: FONTE, p_itens: itens })
    });
    var t = await r.text();
    if (!r.ok) throw new Error('HTTP ' + r.status + ' - ' + t.slice(0, 200));
    return JSON.parse(t);
  }

  log('SUBIDOR DA COLETA — escolha a pasta "Resultado da Coleta".', '#f59e0b');
  var raiz = await window.showDirectoryPicker({ mode: 'read' });

  var lotes = [];
  for await (var e of raiz.values()) {
    if (e.kind === 'directory' && /^LOTE-\d+/.test(e.name)) lotes.push(e);
  }
  lotes.sort(function (a, b) { return a.name.localeCompare(b.name); });
  log(lotes.length + ' lotes na pasta.');

  var totalLido = 0, totalGravado = 0, totalRepetido = 0;

  for (var i = 0; i < lotes.length; i++) {
    var pasta = lotes[i];
    var arq;
    try {
      var dados = await pasta.getDirectoryHandle('dados');
      arq = await dados.getFileHandle('05-dados-estruturados.jsonl');
    } catch (err) {
      console.warn(pasta.name + ': sem o arquivo de dados ainda — pulei.');
      continue;
    }
    var texto = await (await arq.getFile()).text();
    var linhas = texto.split('\n').filter(function (l) { return l.trim(); });
    if (!linhas.length) { console.warn(pasta.name + ': vazio.'); continue; }

    var itens = [];
    for (var k = 0; k < linhas.length; k++) {
      try { itens.push(JSON.parse(linhas[k])); } catch (e2) {}
    }
    totalLido += itens.length;

    var gravados = 0, repetidos = 0;
    for (var j = 0; j < itens.length; j += POR_VEZ) {
      var parte = itens.slice(j, j + POR_VEZ);
      var res = await manda(pasta.name, parte);
      gravados += res.gravados; repetidos += res.ja_tinha;
      console.log('  ' + pasta.name + '  ' + Math.min(j + POR_VEZ, itens.length) +
                  '/' + itens.length + '  (+' + res.gravados + ')');
    }
    totalGravado += gravados; totalRepetido += repetidos;
    log(pasta.name + ' — ' + itens.length + ' lidos · ' + gravados + ' novos · ' +
        repetidos + ' o banco ja tinha');
  }

  log('PRONTO. ' + totalLido + ' lidos · ' + totalGravado + ' entraram · ' +
      totalRepetido + ' ja estavam la.', '#22c58b');
  console.info('Pode rodar de novo quando fechar mais lotes: o que ja entrou nao duplica.');
})();
