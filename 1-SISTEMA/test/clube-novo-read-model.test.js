'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const modulo = require(path.join(__dirname, '..', 'clube-novo-read-model.js'));
const contratos = modulo.contratos;
const recursos = modulo.recursos;

const ATUALIZADO = '2026-09-01T12:00:00Z';
const FOTO = 'https://res.cloudinary.com/clubefootball/image/upload/c_fill,w_320/v1/card-500001.png';

function copia(valor) {
  return JSON.parse(JSON.stringify(valor));
}

function cadastro(cardId, contrato, alteracoes) {
  return Object.assign({
    schema_versao: contrato,
    card_id: String(cardId),
    nome: 'Carta ' + cardId,
    foto_url_cloudinary: 'https://res.cloudinary.com/clubefootball/image/upload/v1/card-' + cardId + '.png',
    box_nome: 'Epic Club 2026',
    overall: 99,
    tipo_carta_id: 'player_type_6_subtype_0',
    tipo_carta_nome: 'Epic',
    posicao_principal_id: 9,
    posicao_principal_codigo: 'CA',
    posicao_principal_nome: 'Centroavante',
    integridade_cadastro: true,
    pendencias: [],
    catalogo_atualizado_em: ATUALIZADO
  }, alteracoes || {});
}

function box(cardId, rank, alteracoes) {
  return Object.assign(cadastro(cardId, contratos.boxes), {
    box_total_cards: 5,
    rank_box_overall: rank,
    catalogo_atualizado_em: null
  }, alteracoes || {});
}

function destaque(cardId, rank, alteracoes) {
  const base = cadastro(cardId, contratos.home);
  delete base.integridade_cadastro;
  return Object.assign(base, {
    secao: 'box_destaque',
    box_total_cards: 5,
    rank_box_overall: rank,
    integridade_cadastro: true
  }, alteracoes || {});
}

function resultadoBusca(cardId, alteracoes) {
  return Object.assign(cadastro(cardId, contratos.busca), {
    playstyles: [{ id: '22', codigo: 'artilheiro', nome: 'Artilheiro' }],
    busca_texto: 'carta ' + cardId + ' epic club 2026'
  }, alteracoes || {});
}

function ficha(cardId, alteracoes) {
  return Object.assign({
    schema_versao: contratos.ficha,
    card_id: String(cardId),
    nome: 'Carta ' + cardId,
    foto_url_cloudinary: FOTO,
    box_nome: 'Epic Club 2026',
    overall: 99,
    tipo_carta_id: 'player_type_6_subtype_0',
    tipo_carta_nome: 'Epic',
    posicao_origem: 'CA',
    posicao_principal_id: 9,
    posicao_principal_codigo: 'CA',
    posicao_principal_nome: 'Centroavante',
    slot_ofensivo: 'Atacante',
    slot_ofensivo_id: '2',
    slot_defensivo: null,
    slot_defensivo_id: null,
    estilo_of_pos: 'Artilheiro',
    pe_dominante: 'Direito',
    altura: 188,
    peso: 84,
    idade: 25,
    codigo_nacionalidade: 'brasil',
    nacionalidade_nome: 'Brasil',
    codigo_clube: 'club-001',
    clube_nome: 'Clube Exemplo',
    codigo_liga: 'liga-001',
    liga_nome: 'Liga Exemplo',
    pe_ruim_uso: 2,
    pe_ruim_precisao: 3,
    resistencia_lesao: 2,
    forma: 2,
    level_cap: 30,
    orcamento: 12,
    cap_estimado: 12,
    roda_motor: true,
    atributos: [{ codigo: 'finalizacao', valor: 91 }],
    corpo: [{ codigo: 'altura', valor: 188 }],
    posicoes: [{ posicao_id: '9', codigo: 'CA', nivel_aptidao: 2 }],
    habilidades: [{ skill_id: '105', codigo: 'finalizacao_acrobatica' }],
    estilos_ia: [],
    pes: [{ campo: 'dominante', valor: 'direito' }],
    playstyles: [{ slot_fisico: 1, playstyle_id: '22', codigo: 'artilheiro' }],
    impetos: [],
    atributos_quantidade: 1,
    corpo_quantidade: 1,
    posicoes_quantidade: 1,
    habilidades_quantidade: 1,
    estilos_ia_quantidade: 0,
    pes_quantidade: 1,
    playstyles_quantidade: 1,
    impetos_quantidade: 0,
    integridade_ficha: true,
    pendencias: [],
    build_publicada: false,
    build_indisponivel_codigo: 'CONTRATO_PONTUACAO_FINAL_AUSENTE',
    catalogo_atualizado_em: ATUALIZADO
  }, alteracoes || {});
}

function build(cardId, linhaId, alteracoes) {
  const atributos = Array.from({ length: 26 }, (_, i) => 80 + (i % 5));
  const normalizada = 100;
  const bonus = 1.5;
  return Object.assign({
    schema_versao: contratos.build,
    publicacao_v2_fingerprint: 'a'.repeat(64),
    linha_id: String(linhaId), card_id: String(cardId),
    carta_nome: 'Carta ' + cardId, carta_tipo: 'Epic', carta_box: 'Epic Club 2026',
    carta_overall: 99, foto_url_cloudinary: FOTO,
    funcao_id: '10', funcao_codigo: 'MAT', funcao_nome: 'Meia armador',
    posicao_id: '9', posicao_codigo: 'CA', posicao_nome: 'Centroavante',
    build_otimizador_id: '901', build_bonificador_id: '902',
    tecnico_id: '7', tecnico_nome: 'Técnico Exemplo',
    barras: { shooting: 8 }, impeto_adicional_codigo: null,
    habilidades_adicionais: [{ skill_id: '105', nome: 'Finalização acrobática' }],
    atributos_finais: atributos,
    arows_snapshot: atributos.map((valor, i) => [i, 1, 80, valor, valor - 80, valor]),
    pontuacao_otimizador_bruta_evidencia: -580.7,
    pontuacao_otimizador_normalizada: normalizada,
    bonus_pe: 0.1, bonus_fisico_total: 0.2, bonus_posicao: 0.3,
    bonus_playstyle_1: 0.4, bonus_playstyle_2: 0.2, bonus_ia: 0.3,
    bonus_outros: {}, bonus_total_bonificador: bonus,
    overall_final: normalizada + bonus, pontuacao_final: normalizada + bonus,
    topo_funcao: normalizada + bonus, percentual_topo: 100,
    estado_final: 'publicada', motivo_final: 'PUBLICADA_V2_NORMALIZADA_NO_BANCO',
    normalizacao_fingerprint: 'b'.repeat(64),
    publicacao_linha_fingerprint_v2: 'c'.repeat(64), publicada_em: ATUALIZADO,
    contratacoes_por_box: [],
    proveniencia: {
      pontuacao_final_oficial: normalizada + bonus,
      bonificador: { componentes: { pe: 0.1, fisico: 0.2 } }
    }
  }, alteracoes || {});
}

function criaTransporte(dados, opcoes) {
  dados = dados || {};
  opcoes = opcoes || {};
  const chamadas = [];
  const limiteServidor = opcoes.serverCap || 1000;

  function linhas(nome) {
    return copia(dados[nome] || []);
  }

  function filtra(rows, url) {
    const card = url.searchParams.get('card_id') || url.searchParams.get('p_card_id');
    if (card) {
      const id = card.startsWith('eq.') ? card.slice(3) : card;
      rows = rows.filter(row => String(row.card_id) === id);
    }
    const secao = url.searchParams.get('secao');
    if (secao && secao.startsWith('eq.')) {
      const valor = secao.slice(3);
      rows = rows.filter(row => row.secao === valor);
    }
    return rows;
  }

  function responde(textoUrl) {
    const url = new URL(textoUrl);
    const recurso = decodeURIComponent(url.pathname.split('/').pop());
    const status = opcoes.statusByResource && opcoes.statusByResource[recurso];
    if (status) {
      return {
        status,
        body: JSON.stringify({ message: 'erro simulado' }),
        contentRange: null
      };
    }
    const todas = filtra(linhas(recurso), url);
    const offset = Number(url.searchParams.get('offset') || url.searchParams.get('p_offset') || 0);
    const solicitado = Number(url.searchParams.get('limit') || url.searchParams.get('p_limit') || 1000);
    const limite = Math.min(solicitado, limiteServidor);
    const pagina = todas.slice(offset, offset + limite);
    let contentRange;
    if (opcoes.missingRangeFor === recurso) contentRange = null;
    else if (!pagina.length) contentRange = opcoes.exactCount ? '*/' + todas.length : '*/*';
    else {
      contentRange = offset + '-' + (offset + pagina.length - 1) + '/' +
        (opcoes.exactCount ? todas.length : '*');
    }
    return { status: 200, body: JSON.stringify(pagina), contentRange };
  }

  class XHR {
    constructor() {
      this._headers = {};
      this._responseHeaders = {};
    }
    open(method, url, async) {
      this._call = { transport: 'xhr', method, url, async, headers: this._headers, body: undefined };
      chamadas.push(this._call);
    }
    setRequestHeader(nome, valor) {
      this._headers[nome] = valor;
    }
    send(body) {
      this._call.body = body;
      const resposta = responde(this._call.url);
      this.status = resposta.status;
      this.responseText = resposta.body;
      this._responseHeaders['content-range'] = resposta.contentRange;
    }
    getResponseHeader(nome) {
      return this._responseHeaders[String(nome).toLowerCase()] || null;
    }
  }

  function fetchMock(url, options) {
    const chamada = {
      transport: 'fetch',
      method: options && options.method,
      url,
      async: true,
      headers: Object.assign({}, options && options.headers),
      body: options && options.body
    };
    chamadas.push(chamada);
    const resposta = responde(url);
    return Promise.resolve({
      ok: resposta.status >= 200 && resposta.status < 300,
      status: resposta.status,
      headers: {
        get(nome) {
          return String(nome).toLowerCase() === 'content-range' ? resposta.contentRange : null;
        }
      },
      text() { return Promise.resolve(resposta.body); }
    });
  }

  return {
    env: {
      XMLHttpRequest: XHR,
      fetch: fetchMock,
      CLUBE_NOVO_READ_MODEL_CONFIG: {
        baseUrl: 'https://host-injetado.invalid/',
        publishableKey: 'valor-injetado-nao-pode-ser-usado'
      }
    },
    chamadas
  };
}

function dadosBasicos(alteracoes) {
  return Object.assign({
    [recursos.boxes]: [box('500001', 1, { foto_url_cloudinary: FOTO })],
    [recursos.home]: [destaque('500001', 1, { foto_url_cloudinary: FOTO })],
    [recursos.busca]: [resultadoBusca('500001', { foto_url_cloudinary: FOTO })],
    [recursos.ficha]: [ficha('500001')],
    [recursos.build]: []
  }, alteracoes || {});
}

function novo(dados, opcoes) {
  const transporte = criaTransporte(dados, opcoes);
  return {
    api: modulo.createForTests(transporte.env),
    chamadas: transporte.chamadas
  };
}

function somenteGetApikey(chamadas) {
  assert.ok(chamadas.length > 0);
  chamadas.forEach(chamada => {
    assert.equal(chamada.method, 'GET');
    assert.equal(chamada.body == null, true);
    assert.deepEqual(Object.keys(chamada.headers), ['apikey']);
    assert.match(chamada.headers.apikey, /^sb_publishable_/);
    assert.equal(Object.prototype.hasOwnProperty.call(chamada.headers, 'Authorization'), false);
    assert.match(chamada.url,
      /^https:\/\/trqqpsnafpbudtvvicch\.supabase\.co\/rest\/v1\/(?:frontend_(?:boxes|home|busca|ficha)_v1|rpc\/frontend_build_publicada_v2)\?/);
  });
}

test('expoe contratos por tela e Build V2 sem declarar geracao mutavel', () => {
  assert.deepEqual(recursos, {
    boxes: 'frontend_boxes_v1',
    home: 'frontend_home_v1',
    busca: 'frontend_busca_v1',
    ficha: 'frontend_ficha_v1',
    build: 'frontend_build_publicada_v2'
  });
  assert.deepEqual(contratos, {
    boxes: 'clube-frontend-boxes-v1',
    home: 'clube-frontend-home-v1',
    busca: 'clube-frontend-busca-v1',
    ficha: 'clube-frontend-ficha-v1',
    build: 'clube-frontend-build-publicada-v2'
  });
  assert.deepEqual(Object.keys(modulo.api).sort(), [
    'ReadModelError', 'boxes', 'boxesSync', 'busca', 'buscaSync', 'card',
    'cardSync', 'carta', 'cartaSync', 'contratos', 'diagnostico', 'ficha',
    'fichaSync', 'foto', 'home', 'homeSync', 'listar', 'listarSync', 'recursos'
  ].sort());
  assert.equal(modulo.api.geracao, undefined);
  assert.equal(modulo.api.catalogo, undefined);
  const diagnostico = modulo.api.diagnostico();
  assert.equal(diagnostico.buildsDisponiveis, true);
  assert.equal(diagnostico.buildPaginaMaxima, 500);
  assert.equal(diagnostico.geracao, undefined);
  assert.equal(Object.isFrozen(diagnostico), true);
});

test('boxes pagina internamente, consulta apenas sua view e congela aliases', async () => {
  const rows = [];
  for (let i = 0; i < 5; i++) {
    rows.push(box(String(510001 + i), i + 1, {
      foto_url_cloudinary: i === 0 ? FOTO : null
    }));
  }
  const { api, chamadas } = novo(dadosBasicos({ [recursos.boxes]: rows }), {
    serverCap: 2
  });
  const resultado = await api.boxes({ offset: 0, limit: 5 });
  assert.equal(resultado.length, 5);
  assert.equal(resultado[0].id, '510001');
  assert.equal(resultado[0].card_id, '510001');
  assert.equal(resultado[0].box, resultado[0].box_nome);
  assert.equal(resultado[0].fotoUrl, FOTO);
  assert.equal(resultado[0].posicaoSigla, 'CA');
  assert.equal(resultado[0].posicaoNome, 'Centroavante');
  assert.equal(resultado[0].tipoCartaNome, 'Epic');
  assert.equal(resultado[0].boxTotalCards, 5);
  assert.equal(resultado[0].rankBoxOverall, 1);
  assert.equal(Object.isFrozen(resultado), true);
  assert.equal(Object.isFrozen(resultado[0]), true);
  assert.equal(Object.isFrozen(resultado[0].pendencias), true);
  assert.throws(() => { resultado[0].nome = 'mutada'; }, TypeError);
  assert.throws(() => { resultado[0].pendencias.push('mutada'); }, TypeError);

  const paginas = chamadas.filter(c => c.url.includes('/' + recursos.boxes + '?'));
  assert.deepEqual(paginas.map(c => Number(new URL(c.url).searchParams.get('offset'))), [0, 2, 4]);
  paginas.forEach(c => {
    const url = new URL(c.url);
    assert.equal(url.searchParams.get('order'),
      'box_nome.asc,rank_box_overall.asc,card_id.asc');
    assert.notEqual(url.searchParams.get('select'), '*');
  });
  somenteGetApikey(chamadas);
});

test('home consulta somente três destaques da view própria', () => {
  const rows = [
    destaque('520001', 1), destaque('520002', 2), destaque('520003', 3)
  ];
  const { api, chamadas } = novo(dadosBasicos({ [recursos.home]: rows }), {
    exactCount: true
  });
  const resultado = api.homeSync();
  assert.equal(resultado.length, 3);
  assert.ok(resultado.every(row => row.secao === 'box_destaque'));
  assert.ok(chamadas.every(c => c.url.includes('/' + recursos.home + '?')));
  const url = new URL(chamadas[0].url);
  assert.equal(url.searchParams.get('secao'), 'eq.box_destaque');
  assert.equal(url.searchParams.get('limit'), '3');
  somenteGetApikey(chamadas);
});

test('busca escapa curingas e nao permite injetar parametros PostgREST', async () => {
  const { api, chamadas } = novo(dadosBasicos(), { exactCount: true });
  const resultado = await api.busca('  Nêymár%_*&select=segredo  ', { limit: 7 });
  assert.equal(resultado.length, 1);
  assert.equal(resultado[0].id, '500001');
  assert.equal(Object.isFrozen(resultado[0].playstyles), true);
  assert.ok(chamadas.every(c => c.url.includes('/' + recursos.busca + '?')));
  const url = new URL(chamadas[0].url);
  assert.equal(url.searchParams.getAll('select').length, 1);
  assert.match(url.searchParams.get('select'), /^schema_versao,card_id,/);
  assert.equal(url.searchParams.has('segredo'), false);
  assert.equal(url.searchParams.get('busca_documento'),
    'fts(simple).neymar:* & select:* & segredo:*');
  assert.equal(url.searchParams.get('limit'), '7');
  somenteGetApikey(chamadas);

  const vazio = novo(dadosBasicos());
  await assert.rejects(vazio.api.busca('   '), e => e && e.code === 'TERMO_BUSCA_INVALIDO');
  await assert.rejects(vazio.api.busca('ma'), e => e && e.code === 'TERMO_BUSCA_INVALIDO');
  assert.equal(vazio.chamadas.length, 0);
});

test('ficha usa select explícito, valida grupos e carta é alias compatível', async () => {
  const { api, chamadas } = novo(dadosBasicos(), { exactCount: true });
  const primeira = await api.ficha('500001');
  assert.equal(primeira.id, '500001');
  assert.equal(primeira.card_id, '500001');
  assert.equal(primeira.build_publicada, false);
  assert.equal(primeira.build_indisponivel_codigo,
    'CONTRATO_PONTUACAO_FINAL_AUSENTE');
  assert.equal(primeira.atributos_quantidade, primeira.atributos.length);
  assert.equal(Object.isFrozen(primeira), true);
  assert.equal(Object.isFrozen(primeira.atributos), true);
  assert.equal(Object.isFrozen(primeira.atributos[0]), true);
  assert.equal(api.foto(primeira), FOTO);
  assert.equal(api.foto('500001'), FOTO);
  assert.throws(() => { primeira.atributos[0].valor = 1; }, TypeError);

  const segunda = await api.carta('500001');
  assert.deepEqual(segunda, primeira);
  assert.notEqual(segunda, primeira);
  assert.ok(chamadas.every(c => c.url.includes('/' + recursos.ficha + '?')));
  chamadas.forEach(c => {
    const url = new URL(c.url);
    assert.equal(url.searchParams.get('card_id'), 'eq.500001');
    assert.notEqual(url.searchParams.get('select'), '*');
    assert.match(url.searchParams.get('select'), /atributos,corpo,posicoes,habilidades/);
    assert.match(url.searchParams.get('select'), /build_publicada,build_indisponivel_codigo/);
  });
  somenteGetApikey(chamadas);
});

test('contrato, pendências e contagens divergentes falham fechado', () => {
  const contratoErrado = novo(dadosBasicos({
    [recursos.boxes]: [box('530001', 1, { schema_versao: 'contrato-antigo' })]
  }));
  assert.throws(() => contratoErrado.api.boxesSync({ limit: 1 }),
    e => e && e.code === 'CONTRATO_INVALIDO');

  const pendenciasTipo = novo(dadosBasicos({
    [recursos.busca]: [resultadoBusca('530002', { pendencias: null })]
  }));
  assert.throws(() => pendenciasTipo.api.buscaSync('carta', { limit: 1 }),
    e => e && e.code === 'PENDENCIAS_INVALIDAS');

  const incompleta = novo(dadosBasicos({
    [recursos.home]: [destaque('530003', 1, { pendencias: ['foto_ausente'] })]
  }));
  assert.throws(() => incompleta.api.homeSync(),
    e => e && e.code === 'TELA_NAO_INTEGRA');

  const contagem = novo(dadosBasicos({
    [recursos.ficha]: [ficha('530004', { atributos_quantidade: 2 })]
  }));
  assert.throws(() => contagem.api.fichaSync('530004'),
    e => e && e.code === 'FICHA_INVALIDA');
});

test('rejeita IDs frouxos e aceita somente Cloudinary image/upload', async () => {
  const invalido = novo(dadosBasicos());
  await assert.rejects(invalido.api.ficha('500001@copia'),
    e => e && e.code === 'ID_INVALIDO');
  assert.equal(invalido.chamadas.length, 0);

  const fotosInvalidas = [
    'http://res.cloudinary.com/clubefootball/image/upload/v1/card.png',
    'https://res.cloudinary.com.evil.example/clubefootball/image/upload/v1/card.png',
    'https://res.cloudinary.com/clubefootball/raw/upload/v1/card.png',
    'https://res.cloudinary.com/clubefootball/image/upload/v1/card.png\"onerror=alert(1)'
  ];
  fotosInvalidas.forEach((url, i) => {
    const caso = novo(dadosBasicos({
      [recursos.boxes]: [box(String(540001 + i), 1, { foto_url_cloudinary: url })]
    }));
    assert.throws(() => caso.api.boxesSync({ limit: 1 }),
      e => e && e.code === 'FOTO_INVALIDA');
  });
  assert.match(invalido.api.foto({ card_id: '500001', foto_url_cloudinary: fotosInvalidas[0] }),
    /^data:image\//);
});

test('listar e card usam a RPC V2, limitam pagina a 500 e nunca usam a bruta como OVR', async () => {
  const { api, chamadas } = novo(dadosBasicos({
    [recursos.build]: [build('500001', '7001'), build('500001', '7002', {
      linha_id: '7002', funcao_id: '11', funcao_nome: 'Meia de arranque',
      impeto_adicional_codigo: 321,
      /* O catalogo fisico usa skill_id 0 para "Pedalada simples". */
      habilidades_adicionais: [{ skill_id: '0', nome: 'Pedalada simples' }],
      contratacoes_por_box: [{
        box_id: '37', box_nome: 'Box em andamento', estado_box: 'em_andamento',
        origem_percentual: 'dinamica', percentual_topo: 96.5,
        etiqueta_codigo: 'muito_pouco', etiqueta_rotulo: 'PAGAR MUITO POUCO',
        regua_versao: 'CONTRATACAO_V1_2026_09_02', congelado_em: null
      }, {
        box_id: '165', box_nome: 'Box finalizada', estado_box: 'finalizada',
        origem_percentual: 'snapshot', percentual_topo: 92.2,
        etiqueta_codigo: 'nao_pagar', etiqueta_rotulo: 'NÃO PAGAR',
        regua_versao: 'HISTORICO_SEM_REGUA_COMPROVADA', congelado_em: ATUALIZADO
      }]
    })]
  }));
  const lista = api.listarSync({ limit: 2 });
  assert.equal(lista.length, 2);
  assert.equal(lista[0].pontuacao_final, 101.5);
  assert.equal(lista[0].b1, 101.5);
  assert.equal(lista[0].pontuacao_otimizador_bruta_evidencia, undefined);
  assert.equal(lista[0].percentual_topo, undefined);
  assert.equal(lista[0].__cn.percentual_topo, undefined);
  assert.deepEqual(lista[0].sisBar, [['Chute', 8]]);
  assert.deepEqual(lista[0].imps, []);
  assert.equal(lista[0].imp, '');
  assert.equal(lista[0].__cn.impetoAdicionalCodigo, null);
  assert.equal(lista[1].habilidades_adicionais[0].skill_id, '0');
  assert.equal(lista[1].__cn.impetoAdicionalCodigo, 321);
  assert.deepEqual(lista[1].__cn.contratacoesPorBox.map(x => [
    x.estadoBox, x.origemPercentual, x.percentualTopo, x.etiquetaRotulo
  ]), [
    ['em_andamento', 'dinamica', 96.5, 'PAGAR MUITO POUCO'],
    ['finalizada', 'snapshot', 92.2, 'NÃO PAGAR']
  ]);
  assert.equal(lista[0].__cn.pontuacaoNormalizada, 100);
  assert.equal(lista[0].__cn.bonusTotal, 1.5);
  assert.equal(Object.isFrozen(lista[0]), false);
  assert.throws(() => api.listarSync({ limit: 501 }),
    e => e && e.code === 'PAGINACAO_INVALIDA');

  const card = await api.card('500001');
  assert.equal(card.length, 2);
  assert.ok(chamadas.every(c => c.url.includes('/rpc/' + recursos.build + '?')));
  chamadas.forEach(c => {
    const url = new URL(c.url);
    assert.equal(url.searchParams.has('select'), false);
    assert.ok(Number(url.searchParams.get('p_limit')) <= 500);
  });
  somenteGetApikey(chamadas);

  const vazio = novo(dadosBasicos());
  assert.throws(() => vazio.api.listarSync(), e => e && e.code === 'SEM_BUILD_PUBLICADA');
  assert.deepEqual(vazio.api.cardSync('500001'), []);
});

test('Content-Range ausente e view inexistente atualizam diagnóstico', async () => {
  const semFaixa = novo(dadosBasicos(), { missingRangeFor: recursos.boxes });
  await assert.rejects(semFaixa.api.boxes({ limit: 1 }),
    e => e && e.code === 'CONTENT_RANGE_AUSENTE');
  assert.equal(semFaixa.api.diagnostico().estado.codigo, 'CONTENT_RANGE_AUSENTE');

  const ausente = novo(dadosBasicos(), {
    statusByResource: { [recursos.home]: 404 }
  });
  await assert.rejects(ausente.api.home(),
    e => e && e.code === 'READ_MODEL_INDISPONIVEL');
  assert.equal(ausente.api.diagnostico().estado.codigo, 'READ_MODEL_INDISPONIVEL');
});
