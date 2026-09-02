/* Adaptador publico por tela do ClubeEfootball.
   Cada metodo consulta exclusivamente a view da tela correspondente.
   Nao existe leitura de tabela privada, ponteiro de geracao ou resultado de
   build fora do contrato proprio e seletivo de pontuacao final publicada. */
(function (root, criarAdaptador) {
  'use strict';

  var api = criarAdaptador(root || {});
  root.ClubeNovoReadModel = api;

  /* A fabrica CommonJS serve somente para testes com transporte injetado. */
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = Object.freeze({
      api: api,
      createForTests: function (ambiente) { return criarAdaptador(ambiente || {}); },
      contratos: api.contratos,
      recursos: api.recursos
    });
  }
})(typeof window !== 'undefined' ? window : globalThis, function criarAdaptador(env) {
  'use strict';

  var BASE_URL = 'https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/';
  var PUBLISHABLE_KEY = 'sb_publishable_XTKGboY9RyYiirPiIsWMhw_P8B51cHj';
  var PAGE_SIZE = 1000;
  var BUILD_PAGE_SIZE = 500;
  var MAX_SCREEN_ROWS = 5000;
  var MAX_TOTAL_ROWS = 100000;
  var MAX_SEARCH_ROWS = 100;
  var MAX_SEARCH_LENGTH = 120;
  var FOTO_VAZIA = 'data:image/gif;base64,R0lGODlhAQABAAAAACw=';
  var own = Object.prototype.hasOwnProperty;

  var CONTRATOS = Object.freeze({
    boxes: 'clube-frontend-boxes-v1',
    home: 'clube-frontend-home-v1',
    busca: 'clube-frontend-busca-v1',
    ficha: 'clube-frontend-ficha-v1',
    build: 'clube-frontend-build-publicada-v2'
  });

  var RECURSOS = Object.freeze({
    boxes: 'frontend_boxes_v1',
    home: 'frontend_home_v1',
    busca: 'frontend_busca_v1',
    ficha: 'frontend_ficha_v1',
    build: 'frontend_build_publicada_v2'
  });

  var RPCS = Object.freeze({
    build: 'frontend_build_publicada_v2'
  });

  var BOXES_FIELDS = Object.freeze([
    'schema_versao', 'card_id', 'box_nome', 'nome',
    'foto_url_cloudinary', 'overall', 'tipo_carta_id', 'tipo_carta_nome',
    'posicao_principal_id', 'posicao_principal_codigo',
    'posicao_principal_nome', 'box_total_cards', 'rank_box_overall',
    'integridade_cadastro', 'pendencias', 'catalogo_atualizado_em'
  ]);

  var HOME_FIELDS = Object.freeze([
    'schema_versao', 'secao', 'card_id', 'box_nome', 'nome',
    'foto_url_cloudinary', 'overall', 'tipo_carta_id', 'tipo_carta_nome',
    'posicao_principal_id', 'posicao_principal_codigo',
    'posicao_principal_nome', 'box_total_cards', 'rank_box_overall',
    'integridade_cadastro', 'pendencias', 'catalogo_atualizado_em'
  ]);

  var BUSCA_FIELDS = Object.freeze([
    'schema_versao', 'card_id', 'nome', 'foto_url_cloudinary', 'box_nome',
    'overall', 'tipo_carta_id', 'tipo_carta_nome', 'posicao_principal_id',
    'posicao_principal_codigo', 'posicao_principal_nome', 'playstyles',
    'busca_texto', 'integridade_cadastro', 'pendencias',
    'catalogo_atualizado_em'
  ]);

  var FICHA_FIELDS = Object.freeze([
    'schema_versao', 'card_id', 'nome', 'foto_url_cloudinary', 'box_nome',
    'overall', 'tipo_carta_id', 'tipo_carta_nome', 'posicao_origem',
    'posicao_principal_id', 'posicao_principal_codigo',
    'posicao_principal_nome', 'slot_ofensivo', 'slot_ofensivo_id',
    'slot_defensivo', 'slot_defensivo_id', 'estilo_of_pos', 'pe_dominante',
    'altura', 'peso', 'idade', 'codigo_nacionalidade', 'nacionalidade_nome',
    'codigo_clube', 'clube_nome', 'codigo_liga', 'liga_nome', 'pe_ruim_uso',
    'pe_ruim_precisao', 'resistencia_lesao', 'forma', 'level_cap',
    'orcamento', 'cap_estimado', 'roda_motor', 'atributos', 'corpo',
    'posicoes', 'habilidades', 'estilos_ia', 'pes', 'playstyles', 'impetos',
    'atributos_quantidade', 'corpo_quantidade', 'posicoes_quantidade',
    'habilidades_quantidade', 'estilos_ia_quantidade', 'pes_quantidade',
    'playstyles_quantidade', 'impetos_quantidade', 'integridade_ficha',
    'pendencias', 'build_publicada', 'build_indisponivel_codigo',
    'catalogo_atualizado_em'
  ]);

  /* O contrato de Build e deliberadamente independente da Ficha fisica:
     a lista nao carrega o agregado pesado de um card para cada linha. */
  var BUILD_FIELDS = Object.freeze([
    'schema_versao', 'publicacao_v2_fingerprint', 'linha_id', 'card_id',
    'carta_nome', 'carta_tipo', 'carta_box', 'carta_overall',
    'foto_url_cloudinary', 'funcao_id', 'funcao_codigo', 'funcao_nome',
    'posicao_id', 'posicao_codigo', 'posicao_nome', 'build_otimizador_id',
    'build_bonificador_id', 'tecnico_id', 'tecnico_nome', 'barras',
    'impeto_adicional_codigo', 'habilidades_adicionais', 'atributos_finais',
    'arows_snapshot', 'pontuacao_otimizador_bruta_evidencia',
    'pontuacao_otimizador_normalizada', 'bonus_pe', 'bonus_fisico_total',
    'bonus_posicao', 'bonus_playstyle_1', 'bonus_playstyle_2', 'bonus_ia',
    'bonus_outros', 'bonus_total_bonificador', 'overall_final',
    'pontuacao_final', 'topo_funcao', 'percentual_topo', 'estado_final',
    'motivo_final', 'normalizacao_fingerprint',
    'publicacao_linha_fingerprint_v2', 'publicada_em', 'proveniencia',
    'contratacoes_por_box'
  ]);

  /* O contrato V2 usa chaves estáveis do motor; a Ficha legada identifica
     cada barra pelo rótulo exibido. Esta ponte é só de formato: não recalcula
     nível, orçamento ou nota. */
  var BARRAS_V2_PARA_SISBAR = Object.freeze([
    ['shooting', 'Chute'],
    ['passing', 'Passe'],
    ['dribbling', 'Drible'],
    ['dexterity', 'Destreza'],
    ['lowerBodyStrength', 'Força pernas'],
    ['aerialStrength', 'Força aérea'],
    ['defending', 'Defesa'],
    ['gk1', 'GO reflexo/salto'],
    ['gk2', 'GO defesa/alcance'],
    ['gk3', 'GO encaixe/reflexos']
  ]);

  var SELECTS = Object.freeze({
    boxes: BOXES_FIELDS.join(','),
    home: HOME_FIELDS.join(','),
    busca: BUSCA_FIELDS.join(','),
    ficha: FICHA_FIELDS.join(',')
  });

  var fotosPorCard = Object.create(null);
  var ultimoEstado = Object.freeze({
    codigo: 'NAO_INICIADO',
    mensagem: 'Nenhuma tela consultou sua view publica.',
    detalhes: null
  });

  function ReadModelError(codigo, mensagem, detalhes) {
    this.name = 'ClubeNovoReadModelError';
    this.code = codigo;
    this.message = mensagem;
    this.detalhes = detalhes || null;
    if (Error.captureStackTrace) Error.captureStackTrace(this, ReadModelError);
  }
  ReadModelError.prototype = Object.create(Error.prototype);
  ReadModelError.prototype.constructor = ReadModelError;

  function falha(codigo, mensagem, detalhes) {
    throw new ReadModelError(codigo, mensagem, detalhes);
  }

  function mudaEstado(codigo, mensagem, detalhes) {
    ultimoEstado = Object.freeze({
      codigo: codigo,
      mensagem: mensagem,
      detalhes: detalhes || null
    });
    try {
      if (typeof env.dispatchEvent === 'function' && typeof env.CustomEvent === 'function') {
        env.dispatchEvent(new env.CustomEvent('clube-novo:read-model-estado', {
          detail: { codigo: codigo, mensagem: mensagem, detalhes: detalhes || null }
        }));
      }
    } catch (e) {}
  }

  function registraErro(e) {
    mudaEstado(e && e.code ? e.code : 'READ_MODEL_ERRO',
      e && e.message ? e.message : String(e), e && e.detalhes ? e.detalhes : null);
    return e;
  }

  function textoResposta(texto) {
    return String(texto || '')
      .replace(/[<>]/g, ' ')
      .replace(/[\u0000-\u001f\u007f]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .slice(0, 240);
  }

  function erroHTTP(status, corpo, recurso) {
    if (status === 404) {
      return new ReadModelError('READ_MODEL_INDISPONIVEL',
        'A view publica desta tela ainda nao foi disponibilizada.',
        { recurso: RECURSOS[recurso], status: status });
    }
    if (status === 401 || status === 403) {
      return new ReadModelError('READ_MODEL_NEGADO',
        'A leitura publica da tela foi negada pelo banco.',
        { recurso: RECURSOS[recurso], status: status });
    }
    return new ReadModelError('READ_MODEL_HTTP',
      'A view publica respondeu HTTP ' + status + '.',
      { recurso: RECURSOS[recurso], status: status, resposta: textoResposta(corpo) });
  }

  function endereco(recurso, parametros) {
    if (!own.call(RECURSOS, recurso)) {
      falha('RECURSO_DESCONHECIDO', 'View de tela desconhecida.', { recurso: recurso });
    }
    var partes = [];
    Object.keys(parametros || {}).forEach(function (chave) {
      var valor = parametros[chave];
      if (valor === undefined || valor === null || valor === '') return;
      partes.push(encodeURIComponent(chave) + '=' + encodeURIComponent(String(valor)));
    });
    return BASE_URL + RECURSOS[recurso] + (partes.length ? '?' + partes.join('&') : '');
  }

  function enderecoRpc(recurso, parametros) {
    if (!own.call(RPCS, recurso)) {
      falha('RECURSO_DESCONHECIDO', 'RPC de leitura desconhecida.', { recurso: recurso });
    }
    var partes = [];
    Object.keys(parametros || {}).forEach(function (chave) {
      var valor = parametros[chave];
      if (valor === undefined || valor === null || valor === '') return;
      partes.push(encodeURIComponent(chave) + '=' + encodeURIComponent(String(valor)));
    });
    return BASE_URL + 'rpc/' + RPCS[recurso] + (partes.length ? '?' + partes.join('&') : '');
  }

  function decodifica(corpo, recurso) {
    try {
      var dados = JSON.parse(corpo || '[]');
      if (!Array.isArray(dados)) throw new Error('resposta nao e lista');
      return dados;
    } catch (e) {
      falha('READ_MODEL_JSON', 'A view publica devolveu JSON invalido.', {
        recurso: RECURSOS[recurso]
      });
    }
  }

  function valorHeader(headers, nome) {
    if (!headers) return null;
    if (typeof headers.get === 'function') return headers.get(nome);
    return headers[nome] || headers[String(nome).toLowerCase()] || null;
  }

  function validaContentRange(header, offset, quantidade, limite, recurso) {
    var texto = String(Array.isArray(header) ? header[0] : (header || '')).trim();
    if (!texto) {
      falha('CONTENT_RANGE_AUSENTE', 'A view nao declarou Content-Range.', {
        recurso: RECURSOS[recurso], offset: offset
      });
    }
    if (quantidade === 0) {
      var vazio = /^\*\/(\*|\d+)$/.exec(texto);
      if (!vazio) {
        falha('CONTENT_RANGE_INVALIDO', 'Content-Range invalido para resposta vazia.', {
          recurso: RECURSOS[recurso], content_range: texto
        });
      }
      var totalVazio = vazio[1] === '*' ? null : Number(vazio[1]);
      if (totalVazio !== null && totalVazio > MAX_TOTAL_ROWS) {
        falha('TOTAL_EXCESSIVO', 'A view declarou linhas demais.', {
          recurso: RECURSOS[recurso], total: totalVazio
        });
      }
      return { total: totalVazio };
    }
    var m = /^(\d+)-(\d+)\/(\*|\d+)$/.exec(texto);
    if (!m) {
      falha('CONTENT_RANGE_INVALIDO', 'Content-Range invalido.', {
        recurso: RECURSOS[recurso], content_range: texto
      });
    }
    var inicio = Number(m[1]);
    var fim = Number(m[2]);
    var total = m[3] === '*' ? null : Number(m[3]);
    if (inicio !== offset || fim < inicio || fim - inicio + 1 !== quantidade || quantidade > limite) {
      falha('CONTENT_RANGE_DIVERGENTE', 'Content-Range nao corresponde a pagina solicitada.', {
        recurso: RECURSOS[recurso], content_range: texto,
        offset: offset, quantidade: quantidade, limite: limite
      });
    }
    if (total !== null && (fim >= total || total > MAX_TOTAL_ROWS)) {
      falha('CONTENT_RANGE_DIVERGENTE', 'Content-Range ultrapassa o total declarado.', {
        recurso: RECURSOS[recurso], content_range: texto
      });
    }
    return { total: total };
  }

  function lerPaginaSync(recurso, parametros, offset, limite) {
    if (typeof env.XMLHttpRequest !== 'function') {
      falha('XHR_INDISPONIVEL', 'Leitura sincrona indisponivel neste navegador.');
    }
    var x = new env.XMLHttpRequest();
    x.open('GET', endereco(recurso, parametros), false);
    x.setRequestHeader('apikey', PUBLISHABLE_KEY);
    x.send(null);
    if (x.status < 200 || x.status >= 300) throw erroHTTP(x.status, x.responseText, recurso);
    var rows = decodifica(x.responseText, recurso);
    var faixa = validaContentRange(
      typeof x.getResponseHeader === 'function' ? x.getResponseHeader('Content-Range') : null,
      offset, rows.length, limite, recurso
    );
    return { rows: rows, total: faixa.total };
  }

  function lerPagina(recurso, parametros, offset, limite) {
    if (typeof env.fetch !== 'function') {
      return Promise.reject(new ReadModelError(
        'FETCH_INDISPONIVEL', 'Leitura assincrona indisponivel neste navegador.'));
    }
    return env.fetch(endereco(recurso, parametros), {
      method: 'GET', headers: { apikey: PUBLISHABLE_KEY }, cache: 'no-store'
    }).then(function (r) {
      return r.text().then(function (corpo) {
        if (!r.ok) throw erroHTTP(r.status, corpo, recurso);
        var rows = decodifica(corpo, recurso);
        var faixa = validaContentRange(
          valorHeader(r.headers, 'Content-Range'), offset, rows.length, limite, recurso);
        return { rows: rows, total: faixa.total };
      });
    });
  }

  /* As RPCs V2 sao STABLE e devolvem uma pagina fechada; PostgREST nao envia
     Content-Range para elas. A pagina e limitada no banco a 500 linhas. */
  function lerRpcSync(recurso, parametros) {
    if (typeof env.XMLHttpRequest !== 'function') {
      falha('XHR_INDISPONIVEL', 'Leitura sincrona indisponivel neste navegador.');
    }
    var x = new env.XMLHttpRequest();
    x.open('GET', enderecoRpc(recurso, parametros), false);
    x.setRequestHeader('apikey', PUBLISHABLE_KEY);
    x.send(null);
    if (x.status < 200 || x.status >= 300) throw erroHTTP(x.status, x.responseText, recurso);
    return decodifica(x.responseText, recurso);
  }

  function lerRpc(recurso, parametros) {
    if (typeof env.fetch !== 'function') {
      return Promise.reject(new ReadModelError(
        'FETCH_INDISPONIVEL', 'Leitura assincrona indisponivel neste navegador.'));
    }
    return env.fetch(enderecoRpc(recurso, parametros), {
      method: 'GET', headers: { apikey: PUBLISHABLE_KEY }, cache: 'no-store'
    }).then(function (r) {
      return r.text().then(function (corpo) {
        if (!r.ok) throw erroHTTP(r.status, corpo, recurso);
        return decodifica(corpo, recurso);
      });
    });
  }

  function parametrosPagina(base, offset, limite) {
    var p = {};
    Object.keys(base).forEach(function (k) { p[k] = base[k]; });
    p.offset = offset;
    p.limit = limite;
    return p;
  }

  function lerIntervaloSync(recurso, base, offset, limite) {
    var rows = [];
    while (rows.length < limite) {
      var pedido = Math.min(PAGE_SIZE, limite - rows.length);
      var inicio = offset + rows.length;
      var pagina = lerPaginaSync(recurso, parametrosPagina(base, inicio, pedido), inicio, pedido);
      if (!pagina.rows.length) break;
      Array.prototype.push.apply(rows, pagina.rows);
      if (pagina.total !== null && offset + rows.length >= pagina.total) break;
      if (offset + rows.length > MAX_TOTAL_ROWS) {
        falha('TOTAL_EXCESSIVO', 'A paginacao ultrapassou o limite de seguranca.', {
          recurso: RECURSOS[recurso]
        });
      }
    }
    return rows;
  }

  function lerIntervalo(recurso, base, offset, limite) {
    var rows = [];
    function proxima() {
      if (rows.length >= limite) return Promise.resolve(rows);
      var pedido = Math.min(PAGE_SIZE, limite - rows.length);
      var inicio = offset + rows.length;
      return lerPagina(recurso, parametrosPagina(base, inicio, pedido), inicio, pedido)
        .then(function (pagina) {
          if (!pagina.rows.length) return rows;
          Array.prototype.push.apply(rows, pagina.rows);
          if (pagina.total !== null && offset + rows.length >= pagina.total) return rows;
          if (offset + rows.length > MAX_TOTAL_ROWS) {
            falha('TOTAL_EXCESSIVO', 'A paginacao ultrapassou o limite de seguranca.', {
              recurso: RECURSOS[recurso]
            });
          }
          return proxima();
        });
    }
    return proxima();
  }

  function copiaJson(valor, campo) {
    if (valor === null || typeof valor === 'string' || typeof valor === 'boolean') return valor;
    if (typeof valor === 'number') {
      if (!Number.isFinite(valor)) falha('DADO_INVALIDO', 'Numero invalido na view.', { campo: campo });
      return valor;
    }
    if (Array.isArray(valor)) {
      return valor.map(function (item, i) { return copiaJson(item, campo + '[' + i + ']'); });
    }
    if (valor && typeof valor === 'object') {
      var resultado = {};
      Object.keys(valor).forEach(function (chave) {
        resultado[chave] = copiaJson(valor[chave], campo + '.' + chave);
      });
      return resultado;
    }
    falha('DADO_INVALIDO', 'Tipo JSON invalido na view.', { campo: campo });
  }

  function congelaProfundo(valor) {
    if (!valor || typeof valor !== 'object' || Object.isFrozen(valor)) return valor;
    Object.keys(valor).forEach(function (chave) { congelaProfundo(valor[chave]); });
    return Object.freeze(valor);
  }

  function selecionaCampos(row, campos, recurso) {
    if (!row || typeof row !== 'object' || Array.isArray(row)) {
      falha('LINHA_INVALIDA', 'A view devolveu uma linha invalida.', {
        recurso: RECURSOS[recurso]
      });
    }
    var dto = {};
    campos.forEach(function (campo) {
      if (!own.call(row, campo)) {
        falha('CAMPO_AUSENTE', 'A view nao devolveu todos os campos do contrato.', {
          recurso: RECURSOS[recurso], campo: campo
        });
      }
      dto[campo] = copiaJson(row[campo], campo);
    });
    return dto;
  }

  function idDecimal(valor, campo, aceitaZero, aceitaNulo) {
    if ((valor === null || valor === '') && aceitaNulo) return null;
    var texto;
    if (typeof valor === 'number') {
      if (!Number.isSafeInteger(valor)) {
        falha('ID_INVALIDO', 'ID numerico fora da faixa segura.', { campo: campo });
      }
      texto = String(valor);
    } else if (typeof valor === 'string') texto = valor;
    else falha('ID_INVALIDO', 'ID deve ser decimal canonico.', { campo: campo });
    var padrao = aceitaZero ? /^(?:0|[1-9]\d*)$/ : /^[1-9]\d*$/;
    if (!padrao.test(texto)) {
      falha('ID_INVALIDO', 'ID deve ser decimal canonico.', {
        campo: campo, valor: texto.slice(0, 80)
      });
    }
    return texto;
  }

  function textoObrigatorio(valor, campo) {
    if (typeof valor !== 'string' || !valor.trim()) {
      falha('DADO_INVALIDO', 'Texto obrigatorio ausente na view.', { campo: campo });
    }
    return valor.trim();
  }

  function textoOpcional(valor, campo) {
    if (valor === null || valor === '') return null;
    if (typeof valor !== 'string') falha('DADO_INVALIDO', 'Texto invalido na view.', { campo: campo });
    return valor.trim() || null;
  }

  function identificadorTextoOpcional(valor, campo) {
    if (valor === null || valor === '') return null;
    if (typeof valor !== 'string' ||
        !/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(valor)) {
      falha('ID_INVALIDO', 'Identificador textual invalido na view.', {
        campo: campo,
        valor: typeof valor === 'string' ? valor.slice(0, 80) : typeof valor
      });
    }
    return valor;
  }

  function numeroOpcional(valor, campo) {
    if (valor === null) return null;
    if (typeof valor !== 'number' || !Number.isFinite(valor)) {
      falha('DADO_INVALIDO', 'Numero invalido na view.', { campo: campo });
    }
    return valor;
  }

  function inteiro(valor, campo, minimo) {
    if (typeof valor !== 'number' || !Number.isSafeInteger(valor) || valor < minimo) {
      falha('DADO_INVALIDO', 'Inteiro invalido na view.', { campo: campo });
    }
    return valor;
  }

  function dataIso(valor, campo) {
    if (valor === null || valor === '') return null;
    if (typeof valor !== 'string' || !valor.trim() || Number.isNaN(Date.parse(valor))) {
      falha('DADO_INVALIDO', 'Data invalida na view.', { campo: campo });
    }
    return valor;
  }

  function fotoCloudinary(valor) {
    if (valor === null || valor === '') return null;
    if (typeof valor !== 'string' || /[\s\"'<>\\]/.test(valor)) {
      falha('FOTO_INVALIDA', 'A foto nao e uma URL Cloudinary permitida.');
    }
    try {
      var url = new URL(valor);
      if (url.protocol !== 'https:' || url.hostname !== 'res.cloudinary.com' ||
          url.port || url.username || url.password || url.hash ||
          !/^\/[A-Za-z0-9_-]+\/image\/upload\/.+/.test(url.pathname)) {
        throw new Error('origem ou caminho invalido');
      }
    } catch (e) {
      falha('FOTO_INVALIDA', 'A foto nao e uma URL Cloudinary permitida.');
    }
    return valor;
  }

  function validaContrato(dto, recurso) {
    if (dto.schema_versao !== CONTRATOS[recurso]) {
      falha('CONTRATO_INVALIDO', 'A view respondeu uma versao de contrato diferente.', {
        recurso: RECURSOS[recurso], esperado: CONTRATOS[recurso], recebido: dto.schema_versao
      });
    }
  }

  function validaPendencias(dto, campoIntegridade, recurso) {
    if (!Array.isArray(dto.pendencias)) {
      falha('PENDENCIAS_INVALIDAS', 'Pendencias deve ser um array.', {
        recurso: RECURSOS[recurso]
      });
    }
    if (dto[campoIntegridade] !== true || dto.pendencias.length !== 0) {
      falha('TELA_NAO_INTEGRA', 'A linha da tela nao passou pela integridade canonica.', {
        recurso: RECURSOS[recurso], campo_integridade: campoIntegridade,
        pendencias: copiaJson(dto.pendencias, 'pendencias')
      });
    }
  }

  function normalizaBase(dto, recurso, integridade, boxObrigatoria) {
    validaContrato(dto, recurso);
    dto.card_id = idDecimal(dto.card_id, 'card_id', false, false);
    dto.nome = textoObrigatorio(dto.nome, 'nome');
    dto.foto_url_cloudinary = fotoCloudinary(dto.foto_url_cloudinary);
    dto.box_nome = boxObrigatoria ? textoObrigatorio(dto.box_nome, 'box_nome') :
      textoOpcional(dto.box_nome, 'box_nome');
    dto.overall = numeroOpcional(dto.overall, 'overall');
    /* `tipo_carta_id` e a chave textual estavel do cadastro (por exemplo,
       player_type_6_subtype_0), nao um inteiro do front antigo. */
    dto.tipo_carta_id = identificadorTextoOpcional(dto.tipo_carta_id, 'tipo_carta_id');
    dto.tipo_carta_nome = textoOpcional(dto.tipo_carta_nome, 'tipo_carta_nome');
    dto.posicao_principal_id = idDecimal(
      dto.posicao_principal_id, 'posicao_principal_id', true, true);
    dto.posicao_principal_codigo = textoOpcional(
      dto.posicao_principal_codigo, 'posicao_principal_codigo');
    dto.posicao_principal_nome = textoOpcional(
      dto.posicao_principal_nome, 'posicao_principal_nome');
    dto.catalogo_atualizado_em = dataIso(dto.catalogo_atualizado_em, 'catalogo_atualizado_em');
    validaPendencias(dto, integridade, recurso);
    if (dto.foto_url_cloudinary) fotosPorCard[dto.card_id] = dto.foto_url_cloudinary;
    /* Aliases de apresentacao sao copias 1:1; nao calculam nem reclassificam
       nenhum dado retornado pela view. */
    dto.id = dto.card_id;
    dto.box = dto.box_nome;
    dto.fotoUrl = dto.foto_url_cloudinary;
    dto.posicaoSigla = dto.posicao_principal_codigo;
    dto.posicaoNome = dto.posicao_principal_nome;
    dto.tipoCartaNome = dto.tipo_carta_nome;
    return dto;
  }

  function normalizaBoxesRow(row) {
    var dto = selecionaCampos(row, BOXES_FIELDS, 'boxes');
    normalizaBase(dto, 'boxes', 'integridade_cadastro', true);
    dto.box_total_cards = inteiro(dto.box_total_cards, 'box_total_cards', 1);
    dto.rank_box_overall = inteiro(dto.rank_box_overall, 'rank_box_overall', 1);
    if (dto.rank_box_overall > dto.box_total_cards) {
      falha('DADO_INVALIDO', 'O ranking da box ultrapassa o total de cards.', {
        card_id: dto.card_id
      });
    }
    dto.boxTotalCards = dto.box_total_cards;
    dto.rankBoxOverall = dto.rank_box_overall;
    return dto;
  }

  function normalizaHomeRow(row) {
    var dto = selecionaCampos(row, HOME_FIELDS, 'home');
    normalizaBase(dto, 'home', 'integridade_cadastro', true);
    if (dto.secao !== 'box_destaque') {
      falha('SECAO_INVALIDA', 'A home devolveu uma secao nao contratada.', { secao: dto.secao });
    }
    dto.box_total_cards = inteiro(dto.box_total_cards, 'box_total_cards', 1);
    dto.rank_box_overall = inteiro(dto.rank_box_overall, 'rank_box_overall', 1);
    if (dto.rank_box_overall > dto.box_total_cards) {
      falha('DADO_INVALIDO', 'O ranking da home ultrapassa o total da box.', {
        card_id: dto.card_id
      });
    }
    dto.boxTotalCards = dto.box_total_cards;
    dto.rankBoxOverall = dto.rank_box_overall;
    return dto;
  }

  function normalizaBuscaRow(row) {
    var dto = selecionaCampos(row, BUSCA_FIELDS, 'busca');
    normalizaBase(dto, 'busca', 'integridade_cadastro', false);
    if (!Array.isArray(dto.playstyles)) {
      falha('DADO_INVALIDO', 'playstyles deve ser um array.', { card_id: dto.card_id });
    }
    dto.busca_texto = textoObrigatorio(dto.busca_texto, 'busca_texto');
    return dto;
  }

  function validaGrupoFicha(dto, grupo) {
    var campoQuantidade = grupo + '_quantidade';
    if (!Array.isArray(dto[grupo])) {
      falha('FICHA_INVALIDA', 'O grupo JSON da ficha deve ser um array.', {
        card_id: dto.card_id, grupo: grupo
      });
    }
    dto[campoQuantidade] = inteiro(dto[campoQuantidade], campoQuantidade, 0);
    if (dto[campoQuantidade] !== dto[grupo].length) {
      falha('FICHA_INVALIDA', 'A contagem nao corresponde ao grupo JSON da ficha.', {
        card_id: dto.card_id, grupo: grupo,
        declarado: dto[campoQuantidade], recebido: dto[grupo].length
      });
    }
  }

  function normalizaFichaRow(row) {
    var dto = selecionaCampos(row, FICHA_FIELDS, 'ficha');
    normalizaBase(dto, 'ficha', 'integridade_ficha', false);
    dto.slot_ofensivo_id = idDecimal(dto.slot_ofensivo_id, 'slot_ofensivo_id', true, true);
    dto.slot_defensivo_id = idDecimal(dto.slot_defensivo_id, 'slot_defensivo_id', true, true);
    ['atributos', 'corpo', 'posicoes', 'habilidades', 'estilos_ia', 'pes',
      'playstyles', 'impetos'].forEach(function (grupo) { validaGrupoFicha(dto, grupo); });
    /* A Ficha V1 e deliberadamente cadastral. A Build V2 chega pelo contrato
       separado, nunca embutida aqui; o consumidor faz o overlay pelo card_id. */
    if (dto.build_publicada !== false ||
        dto.build_indisponivel_codigo !== 'CONTRATO_PONTUACAO_FINAL_AUSENTE') {
      falha('FICHA_INVALIDA',
        'A ficha fisica nao pode embutir uma Build fora do contrato V2.',
        { card_id: dto.card_id });
    }
    return dto;
  }

  function numeroObrigatorio(valor, campo) {
    if (typeof valor !== 'number' || !Number.isFinite(valor)) {
      falha('BUILD_INVALIDA', 'Numero obrigatorio invalido na Build publicada.', { campo: campo });
    }
    return valor;
  }

  function objetoJson(valor, campo) {
    if (!valor || typeof valor !== 'object' || Array.isArray(valor)) {
      falha('BUILD_INVALIDA', 'Objeto JSON invalido na Build publicada.', { campo: campo });
    }
    return valor;
  }

  function seloHex(valor, campo) {
    if (typeof valor !== 'string' || !/^[a-f0-9]{64}$/.test(valor)) {
      falha('BUILD_INVALIDA', 'Selo SHA-256 invalido na Build publicada.', { campo: campo });
    }
    return valor;
  }

  function normalizaArowsSnapshot(dto) {
    if (!Array.isArray(dto.atributos_finais) || dto.atributos_finais.length !== 26 ||
        !Array.isArray(dto.arows_snapshot) || dto.arows_snapshot.length !== 26) {
      falha('BUILD_INVALIDA', 'A Build deve declarar os 26 atributos e as 26 linhas de peso.', {
        card_id: dto.card_id
      });
    }
    dto.atributos_finais.forEach(function (valor, indice) {
      numeroObrigatorio(valor, 'atributos_finais[' + indice + ']');
    });
    dto.arows_snapshot.forEach(function (linha, indice) {
      if (!Array.isArray(linha) || linha.length !== 6 || linha[0] !== indice) {
        falha('BUILD_INVALIDA', 'Linha de atributo fora do formato canonicamente selado.', {
          card_id: dto.card_id, indice: indice
        });
      }
      for (var coluna = 0; coluna < linha.length; coluna++) {
        numeroObrigatorio(linha[coluna], 'arows_snapshot[' + indice + '][' + coluna + ']');
      }
      if (linha[1] < 0 || Math.abs(linha[3] - dto.atributos_finais[indice]) > 0.000000001) {
        falha('BUILD_INVALIDA', 'A Build tem peso negativo ou atributo final divergente.', {
          card_id: dto.card_id, indice: indice
        });
      }
    });
  }

  function barrasV2ParaSisBar(barras) {
    var resultado = [];
    BARRAS_V2_PARA_SISBAR.forEach(function (ponte) {
      var chave = ponte[0];
      if (!own.call(barras, chave)) return;
      resultado.push([ponte[1], inteiro(barras[chave], 'barras.' + chave, 0)]);
    });
    return resultado;
  }

  /* Percentual e etiqueta de contratação pertencem ao contexto da Box. O
     adaptador apenas valida e transporta o retrato vindo do banco: não contém
     faixas, thresholds, fallback ou escolha local de etiqueta. */
  function normalizaContratacoesPorBox(dto) {
    if (!Array.isArray(dto.contratacoes_por_box)) {
      falha('BUILD_INVALIDA', 'A Build deve declarar os contextos de contratação por Box.', {
        card_id: dto.card_id
      });
    }
    var vistos = Object.create(null);
    dto.contratacoes_por_box = dto.contratacoes_por_box.map(function (contexto, indice) {
      var prefixo = 'contratacoes_por_box[' + indice + ']';
      objetoJson(contexto, prefixo);
      var boxId = idDecimal(contexto.box_id, prefixo + '.box_id', false, false);
      var boxNome = textoObrigatorio(contexto.box_nome, prefixo + '.box_nome');
      var estado = textoObrigatorio(contexto.estado_box, prefixo + '.estado_box');
      var origem = textoObrigatorio(contexto.origem_percentual, prefixo + '.origem_percentual');
      var percentual = numeroObrigatorio(contexto.percentual_topo, prefixo + '.percentual_topo');
      var codigo = textoObrigatorio(contexto.etiqueta_codigo, prefixo + '.etiqueta_codigo');
      var rotulo = textoObrigatorio(contexto.etiqueta_rotulo, prefixo + '.etiqueta_rotulo');
      var reguaVersao = textoObrigatorio(contexto.regua_versao, prefixo + '.regua_versao');
      var congeladoEm = dataIso(contexto.congelado_em, prefixo + '.congelado_em');
      if ((estado !== 'em_andamento' && estado !== 'finalizada') ||
          (origem !== 'dinamica' && origem !== 'snapshot') ||
          (estado === 'em_andamento' && (origem !== 'dinamica' || congeladoEm !== null)) ||
          (estado === 'finalizada' && (origem !== 'snapshot' || congeladoEm === null)) ||
          percentual < 0 || percentual > 100 || !/^[a-z0-9_]+$/.test(codigo) ||
          !/^[A-Z0-9_]+$/.test(reguaVersao)) {
        falha('BUILD_INVALIDA', 'Contexto de contratação fora do contrato V2.', {
          card_id: dto.card_id, campo: prefixo
        });
      }
      var chave = boxId + '|' + estado;
      if (vistos[chave]) {
        falha('BUILD_INVALIDA', 'A Build repetiu o mesmo contexto de contratação.', {
          card_id: dto.card_id, box_id: boxId
        });
      }
      vistos[chave] = true;
      return {
        boxId: boxId,
        boxNome: boxNome,
        estadoBox: estado,
        origemPercentual: origem,
        percentualTopo: percentual,
        etiquetaCodigo: codigo,
        etiquetaRotulo: rotulo,
        reguaVersao: reguaVersao,
        congeladoEm: congeladoEm
      };
    });
  }

  function normalizaBuildRow(row) {
    var dto = selecionaCampos(row, BUILD_FIELDS, 'build');
    validaContrato(dto, 'build');
    dto.publicacao_v2_fingerprint = seloHex(dto.publicacao_v2_fingerprint,
      'publicacao_v2_fingerprint');
    dto.publicacao_linha_fingerprint_v2 = seloHex(dto.publicacao_linha_fingerprint_v2,
      'publicacao_linha_fingerprint_v2');
    dto.normalizacao_fingerprint = seloHex(dto.normalizacao_fingerprint,
      'normalizacao_fingerprint');
    dto.linha_id = idDecimal(dto.linha_id, 'linha_id', false, false);
    dto.card_id = idDecimal(dto.card_id, 'card_id', false, false);
    dto.funcao_id = idDecimal(dto.funcao_id, 'funcao_id', false, false);
    dto.posicao_id = idDecimal(dto.posicao_id, 'posicao_id', true, false);
    dto.build_otimizador_id = idDecimal(dto.build_otimizador_id, 'build_otimizador_id', false, false);
    dto.build_bonificador_id = idDecimal(dto.build_bonificador_id, 'build_bonificador_id', false, false);
    dto.tecnico_id = idDecimal(dto.tecnico_id, 'tecnico_id', false, false);
    dto.carta_nome = textoObrigatorio(dto.carta_nome, 'carta_nome');
    dto.carta_tipo = textoOpcional(dto.carta_tipo, 'carta_tipo');
    dto.carta_box = textoOpcional(dto.carta_box, 'carta_box');
    dto.carta_overall = numeroOpcional(dto.carta_overall, 'carta_overall');
    dto.foto_url_cloudinary = fotoCloudinary(dto.foto_url_cloudinary);
    dto.funcao_codigo = textoOpcional(dto.funcao_codigo, 'funcao_codigo') || '';
    dto.funcao_nome = textoObrigatorio(dto.funcao_nome, 'funcao_nome');
    dto.posicao_codigo = textoOpcional(dto.posicao_codigo, 'posicao_codigo') || '';
    dto.posicao_nome = textoObrigatorio(dto.posicao_nome, 'posicao_nome');
    dto.tecnico_nome = textoObrigatorio(dto.tecnico_nome, 'tecnico_nome');
    objetoJson(dto.barras, 'barras');
    if (dto.impeto_adicional_codigo !== null) {
      inteiro(dto.impeto_adicional_codigo, 'impeto_adicional_codigo', 0);
    }
    if (!Array.isArray(dto.habilidades_adicionais)) {
      falha('BUILD_INVALIDA', 'habilidades_adicionais deve ser array.', { card_id: dto.card_id });
    }
    dto.habilidades_adicionais.forEach(function (habilidade, indice) {
      objetoJson(habilidade, 'habilidades_adicionais[' + indice + ']');
      /* O catalogo fisico reserva `0` para a habilidade-base "Pedalada
         simples"; e um identificador valido do contrato, nao uma ausencia. */
      idDecimal(habilidade.skill_id, 'habilidades_adicionais[' + indice + '].skill_id', true, false);
      textoObrigatorio(habilidade.nome, 'habilidades_adicionais[' + indice + '].nome');
    });
    normalizaArowsSnapshot(dto);
    [
      'pontuacao_otimizador_bruta_evidencia', 'pontuacao_otimizador_normalizada',
      'bonus_pe', 'bonus_fisico_total', 'bonus_posicao', 'bonus_playstyle_1',
      'bonus_playstyle_2', 'bonus_ia', 'bonus_total_bonificador', 'overall_final',
      'pontuacao_final', 'topo_funcao', 'percentual_topo'
    ].forEach(function (campo) { numeroObrigatorio(dto[campo], campo); });
    objetoJson(dto.bonus_outros, 'bonus_outros');
    objetoJson(dto.proveniencia, 'proveniencia');
    normalizaContratacoesPorBox(dto);
    dto.publicada_em = dataIso(dto.publicada_em, 'publicada_em');
    if (!dto.publicada_em || dto.estado_final !== 'publicada' ||
        dto.motivo_final !== 'PUBLICADA_V2_NORMALIZADA_NO_BANCO') {
      falha('BUILD_INVALIDA', 'A linha nao esta publicada pelo contrato V2.', {
        card_id: dto.card_id, linha_id: dto.linha_id
      });
    }
    if (Math.abs(dto.pontuacao_final - dto.overall_final) > 0.000000001 ||
        Math.abs(dto.overall_final -
          (dto.pontuacao_otimizador_normalizada + dto.bonus_total_bonificador)) > 0.000000001 ||
        Math.abs(dto.bonus_total_bonificador - (dto.bonus_pe + dto.bonus_fisico_total +
          dto.bonus_posicao + dto.bonus_playstyle_1 + dto.bonus_playstyle_2 + dto.bonus_ia)) > 0.0001) {
      falha('BUILD_INVALIDA', 'A composicao da nota oficial diverge da evidencia V2.', {
        card_id: dto.card_id, linha_id: dto.linha_id
      });
    }
    if (dto.proveniencia.pontuacao_final_oficial !== dto.overall_final ||
        !dto.proveniencia.bonificador || !dto.proveniencia.bonificador.componentes) {
      falha('BUILD_INVALIDA', 'A proveniencia V2 nao confirma os componentes da nota.', {
        card_id: dto.card_id, linha_id: dto.linha_id
      });
    }
    if (dto.foto_url_cloudinary) fotosPorCard[dto.card_id] = dto.foto_url_cloudinary;

    /* Adaptadores de compatibilidade: nenhum deles recalcula ou apresenta a
       nota. `nota()` recebe prioridade para pontuacao_final abaixo. */
    dto.id = dto.card_id;
    dto.nome = dto.carta_nome;
    dto.box = dto.carta_box;
    dto.fotoUrl = dto.foto_url_cloudinary;
    dto.tipo = dto.funcao_nome;
    dto.modelo = dto.funcao_nome;
    dto.np = dto.posicao_codigo;
    dto.sp = [];
    dto.ovr = dto.carta_overall;
    dto.sis = dto.atributos_finais.slice();
    dto.arows = dto.arows_snapshot.map(function (linha) { return linha.slice(); });
    dto.falta = [];
    dto.b1 = dto.pontuacao_final;
    dto.b1n = dto.pontuacao_final;
    dto.b2 = 0; dto.b3 = 0; dto.b4 = 0; dto.b5 = 0;
    dto.HAB = dto.habilidades_adicionais.map(function (habilidade) { return habilidade.nome; });
    dto.TEC = dto.tecnico_nome;
    dto.TECB = [];
    /* O adicional não possui nome/efeito público neste contrato. Nunca se
       deduz um ímpeto por código, nem se cria um valor quando ele vem nulo. */
    dto.imp = '';
    dto.imps = [];
    dto.fab = []; dto.raras = []; dto.adds = []; dto.NEU = []; dto.com = [];
    dto.frows = []; dto.sisBar = barrasV2ParaSisBar(dto.barras);
    dto.base = null; dto.nm = []; dto.nx = [];
    dto.h = null; dto.w = null; dto.age = null; dto.foot = null; dto.inj = null;
    dto.orc = 0; dto.temMax = false; dto.sec = null; dto.MIG = false; dto.votos = 0;
    dto.__cn = {
      contrato: dto.schema_versao,
      generationId: dto.publicacao_v2_fingerprint,
      publicationLineFingerprint: dto.publicacao_linha_fingerprint_v2,
      lineId: dto.linha_id,
      cardId: dto.card_id,
      functionId: dto.funcao_id,
      positionId: dto.posicao_id,
      normalizacaoFingerprint: dto.normalizacao_fingerprint,
      pontuacaoNormalizada: dto.pontuacao_otimizador_normalizada,
      bonusTotal: dto.bonus_total_bonificador,
      bonusComponentes: {
        pe: dto.bonus_pe, fisico: dto.bonus_fisico_total, posicao: dto.bonus_posicao,
        playstyle1: dto.bonus_playstyle_1, playstyle2: dto.bonus_playstyle_2,
        ia: dto.bonus_ia, outros: dto.bonus_outros
      },
      pontuacao_final: dto.pontuacao_final,
      barras: dto.barras,
      impetoAdicionalCodigo: dto.impeto_adicional_codigo,
      contratacoesPorBox: dto.contratacoes_por_box,
      publicadaEm: dto.publicada_em
    };
    /* A bruta e o percentual global permanecem como evidência no banco. A UI
       recebe apenas a contratação contextual já resolvida por Box. */
    delete dto.pontuacao_otimizador_bruta_evidencia;
    delete dto.topo_funcao;
    delete dto.percentual_topo;
    return dto;
  }

  function normalizaBuildRows(rows) {
    var vistos = Object.create(null);
    return rows.map(function (row) {
      var dto = normalizaBuildRow(row);
      if (vistos[dto.linha_id]) {
        falha('BUILD_INVALIDA', 'A RPC devolveu a mesma linha de Build duas vezes.', {
          linha_id: dto.linha_id
        });
      }
      vistos[dto.linha_id] = true;
      return dto;
    });
  }

  function normalizaRows(rows, recurso) {
    var normalizador = {
      boxes: normalizaBoxesRow, home: normalizaHomeRow,
      busca: normalizaBuscaRow, ficha: normalizaFichaRow
    }[recurso];
    var vistos = Object.create(null);
    var resultado = rows.map(function (row) {
      var dto = normalizador(row);
      if (vistos[dto.card_id]) {
        falha('CARD_DUPLICADO', 'A view devolveu o mesmo card mais de uma vez.', {
          recurso: RECURSOS[recurso], card_id: dto.card_id
        });
      }
      vistos[dto.card_id] = true;
      return congelaProfundo(dto);
    });
    return congelaProfundo(resultado);
  }

  function opcoesPagina(opcoes) {
    opcoes = opcoes || {};
    if (!opcoes || typeof opcoes !== 'object' || Array.isArray(opcoes)) {
      falha('PAGINACAO_INVALIDA', 'As opcoes de paginacao sao invalidas.');
    }
    var offset = own.call(opcoes, 'offset') ? opcoes.offset : 0;
    var limite = own.call(opcoes, 'limit') ? opcoes.limit : PAGE_SIZE;
    if (!Number.isSafeInteger(offset) || offset < 0 || offset > MAX_TOTAL_ROWS ||
        !Number.isSafeInteger(limite) || limite < 1 || limite > MAX_SCREEN_ROWS) {
      falha('PAGINACAO_INVALIDA', 'offset ou limit fora do contrato.', {
        offset: offset, limit: limite
      });
    }
    return { offset: offset, limit: limite };
  }

  function boxesSync(opcoes) {
    try {
      var pagina = opcoesPagina(opcoes);
      var rows = lerIntervaloSync('boxes', {
        select: SELECTS.boxes,
        order: 'box_nome.asc,rank_box_overall.asc,card_id.asc'
      }, pagina.offset, pagina.limit);
      var resultado = normalizaRows(rows, 'boxes');
      mudaEstado('BOXES_PRONTAS', 'A pagina de boxes foi carregada.', {
        offset: pagina.offset, quantidade: resultado.length
      });
      return resultado;
    } catch (e) { registraErro(e); throw e; }
  }

  function boxes(opcoes) {
    var pagina;
    try { pagina = opcoesPagina(opcoes); }
    catch (e) { registraErro(e); return Promise.reject(e); }
    return lerIntervalo('boxes', {
      select: SELECTS.boxes,
      order: 'box_nome.asc,rank_box_overall.asc,card_id.asc'
    }, pagina.offset, pagina.limit).then(function (rows) {
      var resultado = normalizaRows(rows, 'boxes');
      mudaEstado('BOXES_PRONTAS', 'A pagina de boxes foi carregada.', {
        offset: pagina.offset, quantidade: resultado.length
      });
      return resultado;
    }).catch(function (e) { registraErro(e); throw e; });
  }

  function homeSync() {
    try {
      var rows = lerIntervaloSync('home', {
        select: SELECTS.home, secao: 'eq.box_destaque',
        order: 'box_nome.asc,rank_box_overall.asc,card_id.asc'
      }, 0, 3);
      var resultado = normalizaRows(rows, 'home');
      if (resultado.length > 3) falha('HOME_INVALIDA', 'A home ultrapassou tres destaques.');
      mudaEstado('HOME_PRONTA', 'Os destaques da home foram carregados.', {
        quantidade: resultado.length
      });
      return resultado;
    } catch (e) { registraErro(e); throw e; }
  }

  function home() {
    return lerIntervalo('home', {
      select: SELECTS.home, secao: 'eq.box_destaque',
      order: 'box_nome.asc,rank_box_overall.asc,card_id.asc'
    }, 0, 3).then(function (rows) {
      var resultado = normalizaRows(rows, 'home');
      if (resultado.length > 3) falha('HOME_INVALIDA', 'A home ultrapassou tres destaques.');
      mudaEstado('HOME_PRONTA', 'Os destaques da home foram carregados.', {
        quantidade: resultado.length
      });
      return resultado;
    }).catch(function (e) { registraErro(e); throw e; });
  }

  function termoBusca(termo) {
    if (typeof termo !== 'string') falha('TERMO_BUSCA_INVALIDO', 'O termo de busca deve ser texto.');
    var limpo = termo;
    if (typeof limpo.normalize === 'function') limpo = limpo.normalize('NFC');
    limpo = limpo.toLowerCase();
    var acentos = 'áàâãäåéèêëíìîïóòôõöúùûüçñýÿ';
    var simples = 'aaaaaaeeeeiiiiooooouuuucnyy';
    limpo = limpo.replace(/[áàâãäåéèêëíìîïóòôõöúùûüçñýÿ]/g, function (letra) {
      return simples.charAt(acentos.indexOf(letra));
    }).replace(/\s+/g, ' ').trim();
    if (limpo.length < 3 || limpo.length > MAX_SEARCH_LENGTH || /[\u0000-\u001f\u007f]/.test(limpo)) {
      falha('TERMO_BUSCA_INVALIDO', 'O termo de busca esta vazio ou fora do limite.');
    }
    /* A mesma traducao da funcao SQL frontend_normalizar_texto_v1 e aplicada
       antes do filtro. Somente lexemas viram tsquery; pontuacao e operadores
       recebidos do usuario nunca entram na gramatica do PostgREST. */
    var lexemas = limpo.match(/[\p{L}\p{N}]+/gu) || [];
    if (!lexemas.length || lexemas.length > 12) {
      falha('TERMO_BUSCA_INVALIDO', 'O termo de busca nao contem lexemas validos.');
    }
    return lexemas.map(function (lexema) { return lexema + ':*'; }).join(' & ');
  }

  function limiteBusca(opcoes) {
    opcoes = opcoes || {};
    if (!opcoes || typeof opcoes !== 'object' || Array.isArray(opcoes)) {
      falha('PAGINACAO_INVALIDA', 'As opcoes da busca sao invalidas.');
    }
    var limite = own.call(opcoes, 'limit') ? opcoes.limit : 30;
    if (!Number.isSafeInteger(limite) || limite < 1 || limite > MAX_SEARCH_ROWS) {
      falha('PAGINACAO_INVALIDA', 'O limite da busca deve ficar entre 1 e 100.');
    }
    return limite;
  }

  function buscaSync(termo, opcoes) {
    try {
      var filtro = termoBusca(termo), limite = limiteBusca(opcoes);
      var rows = lerIntervaloSync('busca', {
        select: SELECTS.busca, busca_documento: 'fts(simple).' + filtro,
        order: 'overall.desc.nullslast,nome.asc,card_id.asc'
      }, 0, limite);
      var resultado = normalizaRows(rows, 'busca');
      mudaEstado('BUSCA_PRONTA', 'A busca de cards foi carregada.', {
        quantidade: resultado.length
      });
      return resultado;
    } catch (e) { registraErro(e); throw e; }
  }

  function busca(termo, opcoes) {
    var filtro, limite;
    try { filtro = termoBusca(termo); limite = limiteBusca(opcoes); }
    catch (e) { registraErro(e); return Promise.reject(e); }
    return lerIntervalo('busca', {
      select: SELECTS.busca, busca_documento: 'fts(simple).' + filtro,
      order: 'overall.desc.nullslast,nome.asc,card_id.asc'
    }, 0, limite).then(function (rows) {
      var resultado = normalizaRows(rows, 'busca');
      mudaEstado('BUSCA_PRONTA', 'A busca de cards foi carregada.', {
        quantidade: resultado.length
      });
      return resultado;
    }).catch(function (e) { registraErro(e); throw e; });
  }

  function fichaSync(cardId) {
    try {
      var id = idDecimal(cardId, 'card_id', false, false);
      var rows = lerIntervaloSync('ficha', {
        select: SELECTS.ficha, card_id: 'eq.' + id, order: 'card_id.asc'
      }, 0, 2);
      if (!rows.length) falha('FICHA_NAO_ENCONTRADA',
        'O card nao existe na view da ficha.', { card_id: id });
      if (rows.length !== 1) falha('FICHA_DUPLICADA',
        'A view da ficha devolveu mais de uma linha.', { card_id: id });
      var resultado = normalizaRows(rows, 'ficha')[0];
      mudaEstado('FICHA_PRONTA', 'A ficha canonica foi carregada.', { card_id: id });
      return resultado;
    } catch (e) { registraErro(e); throw e; }
  }

  function ficha(cardId) {
    var id;
    try { id = idDecimal(cardId, 'card_id', false, false); }
    catch (e) { registraErro(e); return Promise.reject(e); }
    return lerIntervalo('ficha', {
      select: SELECTS.ficha, card_id: 'eq.' + id, order: 'card_id.asc'
    }, 0, 2).then(function (rows) {
      if (!rows.length) falha('FICHA_NAO_ENCONTRADA',
        'O card nao existe na view da ficha.', { card_id: id });
      if (rows.length !== 1) falha('FICHA_DUPLICADA',
        'A view da ficha devolveu mais de uma linha.', { card_id: id });
      var resultado = normalizaRows(rows, 'ficha')[0];
      mudaEstado('FICHA_PRONTA', 'A ficha canonica foi carregada.', { card_id: id });
      return resultado;
    }).catch(function (e) { registraErro(e); throw e; });
  }

  function opcoesPaginaBuild(opcoes) {
    opcoes = opcoes || {};
    if (!opcoes || typeof opcoes !== 'object' || Array.isArray(opcoes)) {
      falha('PAGINACAO_INVALIDA', 'As opcoes da Build sao invalidas.');
    }
    var offset = own.call(opcoes, 'offset') ? opcoes.offset : 0;
    var limite = own.call(opcoes, 'limit') ? opcoes.limit : 100;
    if (!Number.isSafeInteger(offset) || offset < 0 || offset > MAX_TOTAL_ROWS ||
        !Number.isSafeInteger(limite) || limite < 1 || limite > BUILD_PAGE_SIZE) {
      falha('PAGINACAO_INVALIDA', 'A RPC V2 aceita paginas de 1 a 500 linhas.', {
        offset: offset, limit: limite
      });
    }
    return { offset: offset, limit: limite };
  }

  function parametrosBuild(pagina, cardId) {
    var parametros = { p_limit: pagina.limit, p_offset: pagina.offset };
    if (cardId !== undefined && cardId !== null) parametros.p_card_id = cardId;
    return parametros;
  }

  function falhaSemBuild() {
    falha('SEM_BUILD_PUBLICADA',
      'Ainda nao ha Build completa e publicada no contrato V2.',
      { build_indisponivel_codigo: 'SEM_BUILD_PUBLICADA' });
  }

  function listarSync(opcoes) {
    try {
      var pagina = opcoesPaginaBuild(opcoes);
      var rows = lerRpcSync('build', parametrosBuild(pagina));
      var resultado = normalizaBuildRows(rows);
      if (!resultado.length && pagina.offset === 0) falhaSemBuild();
      mudaEstado('BUILDS_PRONTAS', 'A pagina de Builds V2 foi carregada.', {
        offset: pagina.offset, quantidade: resultado.length, limite: pagina.limit
      });
      return resultado;
    } catch (e) { registraErro(e); throw e; }
  }

  function listar(opcoes) {
    var pagina;
    try { pagina = opcoesPaginaBuild(opcoes); }
    catch (e) { registraErro(e); return Promise.reject(e); }
    return lerRpc('build', parametrosBuild(pagina)).then(function (rows) {
      var resultado = normalizaBuildRows(rows);
      if (!resultado.length && pagina.offset === 0) falhaSemBuild();
      mudaEstado('BUILDS_PRONTAS', 'A pagina de Builds V2 foi carregada.', {
        offset: pagina.offset, quantidade: resultado.length, limite: pagina.limit
      });
      return resultado;
    }).catch(function (e) { registraErro(e); throw e; });
  }

  function cardSync(cardId) {
    try {
      var id = idDecimal(cardId, 'card_id', false, false);
      var rows = lerRpcSync('build', parametrosBuild({ offset: 0, limit: BUILD_PAGE_SIZE }, id));
      var resultado = normalizaBuildRows(rows);
      mudaEstado('BUILD_CARD_PRONTA', 'As Builds V2 do card foram carregadas.', {
        card_id: id, quantidade: resultado.length
      });
      return resultado;
    } catch (e) { registraErro(e); throw e; }
  }

  function card(cardId) {
    var id;
    try { id = idDecimal(cardId, 'card_id', false, false); }
    catch (e) { registraErro(e); return Promise.reject(e); }
    return lerRpc('build', parametrosBuild({ offset: 0, limit: BUILD_PAGE_SIZE }, id))
      .then(function (rows) {
        var resultado = normalizaBuildRows(rows);
        mudaEstado('BUILD_CARD_PRONTA', 'As Builds V2 do card foram carregadas.', {
          card_id: id, quantidade: resultado.length
        });
        return resultado;
      }).catch(function (e) { registraErro(e); throw e; });
  }

  function foto(cardOuId) {
    var card = cardOuId && typeof cardOuId === 'object' ? cardOuId : null;
    var id = null;
    try {
      id = idDecimal(card ? (card.card_id !== undefined ? card.card_id : card.id) : cardOuId,
        'card_id', false, false);
    } catch (e) {}
    var candidata = card ? card.foto_url_cloudinary : null;
    if (candidata) {
      try { candidata = fotoCloudinary(candidata); }
      catch (eFoto) { candidata = null; }
    }
    if (!candidata && id) candidata = fotosPorCard[id] || null;
    return candidata || FOTO_VAZIA;
  }

  function diagnostico() {
    return congelaProfundo({
      estado: {
        codigo: ultimoEstado.codigo, mensagem: ultimoEstado.mensagem,
        detalhes: copiaJson(ultimoEstado.detalhes, 'diagnostico.detalhes')
      },
      contratos: {
        boxes: CONTRATOS.boxes, home: CONTRATOS.home,
        busca: CONTRATOS.busca, ficha: CONTRATOS.ficha, build: CONTRATOS.build
      },
      recursos: {
        boxes: RECURSOS.boxes, home: RECURSOS.home,
        busca: RECURSOS.busca, ficha: RECURSOS.ficha, build: RECURSOS.build
      },
      fotosIndexadas: Object.keys(fotosPorCard).length,
      transporte: 'GET + apikey', buildsDisponiveis: true,
      build_indisponivel_codigo: null,
      buildPaginaMaxima: BUILD_PAGE_SIZE
    });
  }

  return Object.freeze({
    boxesSync: boxesSync, boxes: boxes,
    homeSync: homeSync, home: home,
    buscaSync: buscaSync, busca: busca,
    fichaSync: fichaSync, ficha: ficha,
    cartaSync: fichaSync, carta: ficha,
    listarSync: listarSync, listar: listar,
    cardSync: cardSync, card: card,
    foto: foto, diagnostico: diagnostico,
    contratos: CONTRATOS, recursos: RECURSOS,
    ReadModelError: ReadModelError
  });
});
