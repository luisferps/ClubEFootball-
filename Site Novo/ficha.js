(function () {
  "use strict";

  // Mesmos PNGs da referência eFHUB (CmnIconOffense/Defense_Small.png).
  // Bytes incorporados sem redesenho nem requisição externa durante a carga.
  var PLAYSTYLE_ICONS = Object.freeze({
    ofensivo: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEgAAABICAYAAABV7bNHAAAABHNCSVQICAgIfAhkiAAAA8pJREFUeJztnEuLFFcYht9X8wM6hCwCYgiJjgR0M5c/ILhIFoZ4CVkbo2OWiYI/QBjjWpgZyA9wQIgrQfAPyAwhKxeZIRcILtx01uo8WVS107eqM9196uLMeaCgu7rqq1MPX5069VVVm8XvlCjmSNMNaDtJUIAkKMB7o7Ps+pvRJqD/W8qgAGMyaCzXgCuSPpXUqbA9ddCVtGP7F0lroYU9eprfO8SAjyQ9kjQftYntYUvSedsv9mYNHmKhDHpkeyF+u1rDgqRfgaXejOEeuKwPuqaDmzn9zCvb17EUCsr7nEOB7cJ9Lcugw5A9PQr3db9nsT54x8dJZmhG6VAnjYMCJEEBkqAASVCAJChAEhQgCQowxThoVmatNzE8jqmUBgQV0pH0ff55XVlZonHaIKgD3FQmp1druilp3fY9NSyqyT7oOHAfeCnplgYLcR1Jt4CXwH1JxxtpoSoRZJdPOgM8AP6UdN320cC0LOkvSQ+A0/uIH5U6M+gs8AT4TdLFKda/ZPt34Imks5HbVkgdgi4AzyLuWE/0M0kXIsQrpUpBV4HnwIaqqS3NAxvAc0lXK4gvKYqggT7gfUk/AX8Dq5JOOsDkWxthTtndiX+AH7M2xOuTYmVQB7gD/AHclXQsUtxJOGb7Xt6GO4p0eyqGoK8LTtVN8XaIoL2B59TEEPRZhBiVAHw8a4wYI+kj6hM9Tb8SE9tHe5+JcNmWruYDJEEBkqAASVCAJChAEhQgCQqQBAVIggK0RVBX0gpwAjghaUUtKdo3KiivOd8GPgFuS9qWtN0/L7/obIw6BO0OTVImYVnSSVsrtrpjqsvd7DfPSVrOyxgUxKuMujNoG1jOD6NV7e8w6kpasz1n+4ayLKuNugRtYV8my4bVGeKsYc9hX1b2CG/lVCoIeIx9DntJ0sOIoR9iL2GfAx5HjDtCDEHDfcJrSRvAgqQvzO5Ts6u308R3saB/GojF7lPbX0pazO+1vepvS4zSVOwMWgdOAd+opkMgZ8v2t7Y/1z5eL5iEGIK6kn62/aHtHyTtRIg5LTvADeADSXeB/2YNWPiuBvAm+zacp8OPAQ/+zlCds/oC7KTbH3kMuLeexy0foSZdt5B6t9+WS43WkgQFSIICJEEBkqAASVCAJCjAFOOg8QOtd5zCsktZBtV5LdU0hTWmQkH5e+WHAqBwX8syaE2HI4s2VVLEC3XS5/MAB5VNSV+VLVAqyPYLYDEvsG+qJbdiZqQraTOvjS8C/5YtXPrXFNJo+eCgM8k/LyQ0dhzUdH2nXaQMCpAEBUiCAvwPny+OJxEjzrcAAAAASUVORK5CYII=",
    defensivo: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEgAAABICAYAAABV7bNHAAAABHNCSVQICAgIfAhkiAAAA0lJREFUeJztnEFr1EAUx3+RnmUpPXqRFunZlvoBiuDRUqwfQNj24E1Q+gUUD97E4op3pS3evJR+gNoteCuUKgo9Fln6ARoPM9F0SfLSzZsk274fDCW7kzfz/vsy8/Yl3Yh+HyOfG01PoO2YQAImkMBEiT7DIp6HmEiNXMofiyCBsgJ1gT3gFKf4OLdT70u3jOORsM3fAr4Ac2WMjSEHwBJwktchS6B0VO0B8/rzahV94F7q+MKaVHSJdbm6kZNmjoLLrUigJ/pzaS25vhYJdB2iJyHX16w8SMpzompzaZw45/VMvy0PEjCBBEwgARNIwAQSMIEETCCBMvUgiatWL7qARgR1gZdAR8GWFh3gFfCiqiENgTrAc1yd5R0wrWBzVKaBDeAPTpzKH5r2GtQFDoFP1Ptdbs6PeQisahoOsUhPACvAPvAVWAwwRsKiH2PfjzkBUZRqlQcIvYs9AHaAb8Cyot1lb3PHjxGMurb5eWATOKLaJbDqbWxSU6Wz7jxoBreIJkKVWUQ7/Bdmw9uojRACRUKDi0Ll7TYd/96wMGXsq9F0Jj2Fy1d++r8zvqVfm2psduhk0hok0VI5sdOm6QhqPU1E0FjVtC2CBEwgARNIwAQSMIEETCABE0hAIw8avtc9fBw674kLDyuiEUHHCjZC8auqAQ2BtoFJ4DUwULBXlQFuLpPA+6rGip5RPP/XZ/icfDq4uvRT3PONUn8NkmvqBHgL9Cj+oPKWhMxg0RYo4SbwGHgG3BH6SvakReUIeAN8Bs5KzO1SAoXaxc6AD8As8Aj3oKQ2fW971o9VRpxLU8c2vw0sAPeBXQV7u97WgrcdlDrzoMSxu8DWCOdv+XO1hC5FE4nid9w9rNu4BTUWWs/3XfHn1kqTmfRvYI3sFCG9Va/5vo0QahcbheT2Drj8JVRO1Yptvs20Ypu/MphAAiaQgAkkYAIJmEACJpCACSSQVZOWRNMt+jZMFEURMIjjOPG79P+sHgSbVfv4kfdGkUAfA0yklcRxnOtrkUA9rkcUHVBQ3M8SKP0rBUu4Z5Clms24tv04jh8O+SwKlOYEV9pcx9WA23BbpyoDnC/rON9yf3UB5J+muPZYHiRgAgmYQAImkIAJJPAXvKwLclhbZ4gAAAAASUVORK5CYII="
  });

  var CONFIG = Object.freeze({
    contract: "site-novo-ficha-v2",
    version: 2
  });

  var CARD_STATUSES = new Set([
    "card_sem_build_publicada",
    "builds_em_atualizacao",
    "linha_nao_encontrada_ou_nao_publicada",
    "atributos_em_atualizacao",
    "atributos_aguardando_publicacao",
    "pronto"
  ]);
  var ALL_STATUSES = new Set([
    "parametro_ausente",
    "card_nao_encontrado"
  ].concat(Array.from(CARD_STATUSES)));
  var linkedSelection = {
    source: null,
    positionCodes: [],
    buildKey: null
  };
  var viewState = {
    envelope: null,
    successfulUrl: window.location.href,
    requestVersion: 0,
    requestController: null
  };
  var scrollState = { pending: null, ready: false, timer: null };
  var personalState = { cardId:null, records:[], selected:null, version:0, expanded:false };
  function rememberBuildExpansion(){
    try{window.sessionStorage.setItem("clubefootball:ficha:expanded:"+personalState.cardId,String(personalState.expanded));}catch(_){}
  }
  function readBuildExpansion(cardId){
    try{return window.sessionStorage.getItem("clubefootball:ficha:expanded:"+cardId)==="true";}catch(_){return false;}
  }

  function scrollStorageKey() {
    return "clubefootball:ficha:scroll:" + window.location.href;
  }

  function readSavedScroll() {
    var saved = null;
    try { saved = window.history.state && window.history.state.fichaScroll; } catch (_) {}
    if (!saved || saved.url !== window.location.href) {
      try { saved = JSON.parse(window.sessionStorage.getItem(scrollStorageKey())); } catch (_) { saved = null; }
    }
    return saved && saved.url === window.location.href &&
      Number.isFinite(saved.x) && saved.x >= 0 && Number.isFinite(saved.y) && saved.y >= 0
      ? saved : null;
  }

  function saveScrollPosition() {
    // A página fica curta durante a consulta: não sobrescrever a altura anterior com zero.
    if (!scrollState.ready || byId("ficha-content").hidden) return;
    var saved = { url: window.location.href, x: window.scrollX || 0, y: window.scrollY || 0 };
    try { window.sessionStorage.setItem(scrollStorageKey(), JSON.stringify(saved)); } catch (_) {}
    try {
      var previous = window.history.state;
      var state = isPlainObject(previous) ? Object.assign({}, previous) : {};
      state.fichaScroll = saved;
      window.history.replaceState(state, "", window.location.href);
    } catch (_) {}
  }

  function restoreInitialScroll() {
    if (scrollState.ready) return;
    var saved = scrollState.pending;
    scrollState.pending = null;
    // Dados e foto já foram montados: a altura de destino agora existe.
    if (saved && typeof window.scrollTo === "function") {
      window.scrollTo({ left: saved.x, top: saved.y, behavior: "instant" });
    }
    scrollState.ready = true;
  }
  var PITCH_POSITION_ROWS = [
    ["PTE", "CA", "PTD"],
    ["SA"],
    ["MLE", "MAT", "MLD"],
    ["MLG"],
    ["VOL"],
    ["LE", "ZC", "LD"],
    ["GO"]
  ];

  function byId(id) {
    return document.getElementById(id);
  }

  function setText(id, value, fallback) {
    var node = byId(id);
    if (node) {
      node.textContent = value === null || value === undefined || value === ""
        ? (fallback || "—")
        : String(value);
    }
  }

  function asArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function isPlainObject(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
  }

  function formatNumber(value, digits) {
    if (value === null || value === undefined || value === "") return "—";
    var number = Number(value);
    if (!Number.isFinite(number)) return "—";
    return number.toLocaleString("pt-BR", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits
    });
  }

  function formatSigned(value, digits) {
    if (value === null || value === undefined || value === "") return "—";
    var number = Number(value);
    if (!Number.isFinite(number)) return "—";
    var prefix = number > 0 ? "+" : "";
    return prefix + formatNumber(number, digits);
  }

  function renderImprove(id, value) {
    var node = typeof id === "string" ? byId(id) : id;
    if (!node) return;
    node.classList.remove("ok", "unavailable");
    if (value === null || value === undefined || value === "") {
      node.textContent = "não publicado";
      node.classList.add("unavailable");
      return;
    }
    var percentage = Number(value);
    if (!Number.isFinite(percentage) || percentage < 0) {
      node.textContent = "não publicado";
      node.classList.add("unavailable");
      return;
    }
    node.textContent = percentage > 0.05
      ? "+" + formatNumber(percentage, 1) + "%"
      : "0%";
    node.classList.add("ok");
  }

  function sameFunction(left, right) {
    if (!isPlainObject(left) || !isPlainObject(right)) return false;
    if (left.id !== null && left.id !== undefined && right.id !== null && right.id !== undefined) {
      return String(left.id) === String(right.id);
    }
    return Boolean(left.rotulo && right.rotulo && left.rotulo === right.rotulo);
  }

  function bestReadyScoreForFunction(data, currentBuild) {
    if (!isPlainObject(currentBuild) || !isPlainObject(currentBuild.funcao)) return null;
    var scores = asArray(data && data.builds_publicadas)
      .filter(function (item) {
        return isPlainObject(item) && sameFunction(item.funcao, currentBuild.funcao);
      })
      .filter(function(item){return item.nota_final!==null&&item.nota_final!==undefined&&item.nota_final!=="";})
      .map(function (item) { return Number(item.nota_final); })
      .filter(Number.isFinite);
    return scores.length ? Math.max.apply(Math, scores) : null;
  }

  function improvementAgainstReadyBuilds(data, currentBuild, currentScore) {
    var score = Number(currentScore);
    var best = bestReadyScoreForFunction(data, currentBuild);
    if (!Number.isFinite(score) || score <= 0 || !Number.isFinite(best)) return null;
    return best > score ? (best - score) / score * 100 : 0;
  }

  function create(tag, className, textValue) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (textValue !== undefined && textValue !== null) {
      node.textContent = String(textValue);
    }
    return node;
  }

  function replaceChildren(id, children) {
    var target = byId(id);
    if (!target) return;
    target.replaceChildren.apply(target, children);
  }

  function positionCode(value) {
    var raw = isPlainObject(value) ? value.codigo : value;
    if (typeof raw !== "string") return null;
    var normalized = raw.trim().toUpperCase();
    return normalized || null;
  }

  function positionCodes(value) {
    var values = Array.isArray(value) ? value : [value];
    return values.reduce(function (codes, item) {
      var code = positionCode(item);
      if (code && codes.indexOf(code) === -1) codes.push(code);
      return codes;
    }, []);
  }

  function samePositionCodes(left, right) {
    return left.length === right.length && left.every(function (code) {
      return right.indexOf(code) !== -1;
    });
  }

  function nodePositionCodes(node) {
    return positionCodes((node.dataset.positionCodes || "").split(" "));
  }

  function positionBaseState(position) {
    if (isPlainObject(position) && position.principal) return "primary";
    if (
      isPlainObject(position) &&
      position.nivel !== null &&
      position.nivel !== undefined &&
      Number.isFinite(Number(position.nivel)) &&
      Number(position.nivel) > 0
    ) {
      return "allowed";
    }
    return "absent";
  }

  function playablePositionCount(positions) {
    var map = new Map(asArray(positions).map(function (item) {
      return [positionCode(item), item];
    }));
    return PITCH_POSITION_ROWS.reduce(function (total, row) {
      return total + row.filter(function (code) {
        return positionBaseState(map.get(code)) !== "absent";
      }).length;
    }, 0);
  }

  function applyLinkedSelection(value, buildKey, source) {
    var codes = positionCodes(value);
    linkedSelection = {
      source: source || null,
      positionCodes: codes,
      buildKey: buildKey || null
    };
    document.querySelectorAll("#pitch .pos").forEach(function (node) {
      var selected = codes.indexOf(node.dataset.positionCode) !== -1;
      node.classList.toggle("selected", selected);
      node.setAttribute("aria-pressed", selected ? "true" : "false");
    });
    document.querySelectorAll("#builds-list .build").forEach(function (node) {
      var matches = source === "build"
        ? Boolean(buildKey) && node.dataset.buildKey === buildKey
        : source === "pitch" && codes.length > 0 && nodePositionCodes(node).some(function (code) {
          return codes.indexOf(code) !== -1;
        });
      node.classList.toggle("position-match", matches);
      node.setAttribute("aria-pressed", matches ? "true" : "false");
    });
  }

  function togglePitchPosition(value) {
    var codes = positionCodes(value);
    var availableCodes = Array.from(document.querySelectorAll("#pitch .pos")).filter(function (node) {
      return !node.disabled && !node.classList.contains("absent");
    }).map(function (node) { return node.dataset.positionCode; });
    if (!codes.length || codes.some(function (code) { return availableCodes.indexOf(code) === -1; })) return;
    var clear = linkedSelection.source === "pitch" &&
      samePositionCodes(codes, linkedSelection.positionCodes);
    applyLinkedSelection(clear ? [] : codes, null, clear ? null : "pitch");
  }

  function lineIdText(value) {
    if (value === null || value === undefined) return null;
    var normalized = String(value).trim();
    return /^[1-9]\d*$/.test(normalized) ? normalized : null;
  }

  function lineForBuildSelection(group) {
    var preferredCodes = linkedSelection.source === "pitch"
      ? linkedSelection.positionCodes
      : [];
    var preferred = asArray(group.lines).find(function (line) {
      return preferredCodes.indexOf(line.positionCode) !== -1;
    });
    return (preferred && preferred.lineId) || group.selectedLineId || group.lineIds[0] || null;
  }

  function buildUrl(cardId, lineId) {
    var target = new URL(window.location.href);
    target.searchParams.set("card", cardId);
    target.searchParams.delete("card_id");
    target.searchParams.set("linha", lineId);
    target.searchParams.delete("linha_id");
    return target.toString();
  }

  function conditionalDegree(data) {
    var conditional = asArray(data && data.build && data.build.impetos).find(function (item) {
      return [1, 2, 3].indexOf(Number(item && item.condicao_nivel)) !== -1;
    });
    return conditional ? Number(conditional.condicao_nivel) : null;
  }

  function conditionalLine(data, degree) {
    var target = asArray(data && data.degraus_condicionais).find(function (item) {
      return Number(item && item.nivel) === Number(degree) && lineIdText(item && item.linha_id);
    });
    return target ? Number(target.linha_id) : null;
  }

  function synchronizeConditionalDegree(data) {
    var degree = conditionalDegree(data);
    if (degree && window.SiteNovoDegrau && typeof window.SiteNovoDegrau.sync === "function") {
      window.SiteNovoDegrau.sync(degree);
    }
  }

  function selectConditionalDegree(degree) {
    var data = viewState.envelope && viewState.envelope.dados;
    if (!data || conditionalDegree(data) === Number(degree)) return;
    var lineId = conditionalLine(data, degree);
    var cardId = data.card ? String(data.card.card_id || "").trim() : "";
    if (!lineId || !cardId) return;
    loadFicha({ p_card_id: cardId, p_linha_id: lineId }, {
      mode: "switch", targetUrl: buildUrl(cardId, String(lineId))
    });
  }

  function selectPublishedBuild(data, group) {
    var lineId = lineIdText(lineForBuildSelection(group));
    var cardId = data && data.card ? String(data.card.card_id || "").trim() : "";
    if (!lineId || !cardId) return;

    var currentBuildLine = lineIdText(data.build && data.build.linha_id);
    var targetUrl = buildUrl(cardId, lineId);
    if (currentBuildLine === lineId && !personalState.selected) {
      if (window.location.href !== targetUrl) {
        window.history.pushState(null, "", targetUrl);
        viewState.successfulUrl = targetUrl;
      }
      applyLinkedSelection(group.positions, group.identity, "build");
      return;
    }

    loadFicha(
      { p_card_id: cardId, p_linha_id: Number(lineId) },
      { mode: "switch", targetUrl: targetUrl }
    );
  }

  function groupPublishedBuilds(items) {
    var groups = [];
    var byIdentity = new Map();
    asArray(items).forEach(function (item) {
      var functionObject = isPlainObject(item.funcao) ? item.funcao : {};
      var functionLabel = functionObject.rotulo || "Especialidade não publicada";
      var functionKey = functionObject.id !== null && functionObject.id !== undefined
        ? "id:" + String(functionObject.id)
        : "rotulo:" + functionLabel;
      var identity = functionKey;
      var group = byIdentity.get(identity);
      if (!group) {
        group = {
          identity: identity,
          functionLabel: functionLabel,
          notaFinal: item.nota_final,
          reguaVigente: item.regua_vigente !== false,
          positions: [],
          lineIds: [],
          lines: [],
          selectedLineId: null,
          selected: false
        };
        byIdentity.set(identity, group);
        groups.push(group);
      }
      var code = positionCode(item.posicao);
      if (code && group.positions.indexOf(code) === -1) group.positions.push(code);
      var itemLineId = lineIdText(item.linha_id);
      if (itemLineId) {
        group.lineIds.push(itemLineId);
        group.lines.push({ lineId: itemLineId, positionCode: code });
      }
      if (item.selecionada) {
        group.selected = true;
        group.selectedLineId = itemLineId;
      }
    });
    return groups;
  }

  function renderBuildModes(data, build) {
    var hasBuild = isPlainObject(build);
    var personalizeButton = byId("personalize-build-action");

    setText(
      "selected-function-name",
      String(personalState.selected ? personalState.selected.rotulo : hasBuild && build.funcao && build.funcao.rotulo ? build.funcao.rotulo : "NENHUMA BUILD PUBLICADA")
        .toLocaleUpperCase("pt-BR")
    );
    setText(
      "selected-function-meta",
      hasBuild
        ? ((build.posicao && build.posicao.codigo ? build.posicao.codigo : "—") + " · " + formatNumber(build.nota_final, 2))
        : "—"
    );
    if (personalizeButton) {
      personalizeButton.disabled = !hasBuild || !window.FichaEditor;
      personalizeButton.setAttribute("aria-disabled", String(personalizeButton.disabled));
      personalizeButton.setAttribute("aria-label", "Editar build: abrir a distribuição atual no editor.");
      personalizeButton.title = hasBuild
        ? "Abrir uma cópia no editor. A build original não será alterada."
        : "Selecione uma build publicada para abrir no editor.";
      personalizeButton.onclick = function () { window.FichaEditor.open("edit", data, personalState.selected); };
    }
    var newBuildButton = byId("new-build-action");
    newBuildButton.disabled = !data.card || !window.FichaEditor;
    newBuildButton.setAttribute("aria-disabled", String(newBuildButton.disabled));
    newBuildButton.onclick = function () { window.FichaEditor.open("new", data); };

  }

  function validateEnvelope(payload) {
    if (!isPlainObject(payload)) throw new Error("Resposta pública não é um objeto.");
    if (payload.contrato !== CONFIG.contract) throw new Error("Contrato público inesperado.");
    if (payload.versao !== CONFIG.version) throw new Error("Versão pública inesperada.");
    if (!ALL_STATUSES.has(payload.status)) throw new Error("Estado público desconhecido.");
    if (typeof payload.mensagem !== "string") throw new Error("Mensagem pública ausente.");
    if (CARD_STATUSES.has(payload.status)) {
      if (!isPlainObject(payload.dados) || !isPlainObject(payload.dados.card)) {
        throw new Error("Dados do card ausentes.");
      }
    }
    return payload;
  }

  function readParams() {
    var params = new URLSearchParams(window.location.search);
    var cardRaw = params.has("card") ? params.get("card") : params.get("card_id");
    var lineRaw = params.has("linha") ? params.get("linha") : params.get("linha_id");
    var cardId = (cardRaw || "").trim() || null;
    lineRaw = (lineRaw || "").trim();
    var lineId = null;
    if (lineRaw) {
      var parsed = Number(lineRaw);
      if (!Number.isSafeInteger(parsed) || parsed <= 0) {
        throw new Error("linha_id inválida.");
      }
      lineId = parsed;
    }
    return { p_card_id: cardId, p_linha_id: lineId };
  }

  async function fetchFicha(params, signal) {
    var payload = await window.SiteNovoCommon.request('/rest/v1/rpc/site_novo_ficha_v2',params,{signal});
    return validateEnvelope(payload);
  }

  function renderMessage(envelope) {
    var message = byId("screen-message");
    message.textContent = envelope.mensagem;
    message.hidden = envelope.status === "pronto";
  }

  function renderLayoutState(status) {
    var ficha = byId("ficha");
    if (!ficha) return;
    ficha.classList.toggle("layout-incomplete", status !== "pronto");
  }

  function preparePhoto(card, signal) {
    if (!card || typeof card.foto_url !== "string" || card.foto_url.indexOf("https://") !== 0) {
      return Promise.resolve(null);
    }
    return new Promise(function (resolve) {
      var image = create("img");
      var settled = false;
      var timer;
      function finish(value) {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        image.onload = null;
        image.onerror = null;
        signal.removeEventListener("abort", abort);
        resolve(value);
      }
      function abort() { finish(null); }
      if (signal.aborted) { finish(null); return; }
      signal.addEventListener("abort", abort, { once: true });
      // Limite só da imagem: uma origem indisponível não prende a Ficha.
      timer = setTimeout(function () { finish(null); }, 6000);
      image.alt = card.nome ? "Card de " + card.nome : "Imagem do card";
      image.referrerPolicy = "no-referrer";
      image.onerror = function () { finish(null); };
      image.onload = function () {
        if (typeof image.decode === "function") {
          image.decode().then(function () { finish(image); }, function () { finish(null); });
        } else {
          finish(image);
        }
      };
      image.src = card.foto_url;
      if (image.complete && image.naturalWidth > 0) image.onload();
    });
  }

  function renderPhoto(card, preparedPhoto) {
    var box = byId("card-photo");
    box.replaceChildren();
    if (preparedPhoto) {
      box.appendChild(preparedPhoto);
    } else {
      box.appendChild(create("span", "", "sem imagem"));
    }
  }

  function renderPitch(positions) {
    var map = new Map(asArray(positions).map(function (item) {
      return [positionCode(item), item];
    }));
    var rowNodes = PITCH_POSITION_ROWS.map(function (codes) {
      var row = create("div", "pitch-row");
      codes.forEach(function (code) {
        var position = map.get(code);
        var baseState = positionBaseState(position);
        var node = create("button", "pos " + baseState, code);
        node.type = "button";
        node.disabled = baseState === "absent";
        node.dataset.positionCode = code;
        node.setAttribute("aria-disabled", node.disabled ? "true" : "false");
        node.setAttribute("aria-pressed", "false");
        var stateLabel = baseState === "primary"
          ? "posição nativa"
          : (baseState === "allowed" ? "posição permitida" : "posição indisponível");
        var positionName = position && position.nome ? position.nome : code;
        var aptitude = baseState === "allowed" ? " · aptidão " + position.nivel : "";
        node.title = positionName + " · " + stateLabel + aptitude;
        node.setAttribute("aria-label", positionName + ", " + stateLabel + (node.disabled ? ". Não pode ser selecionada para este card." : ". Alternar destaque das builds de " + code + "."));
        if (!node.disabled) {
          node.addEventListener("click", function () {
            togglePitchPosition(code);
          });
        }
        row.appendChild(node);
      });
      return row;
    });
    replaceChildren("pitch", rowNodes);
  }

  function chipNodes(items, className, emptyText) {
    var list = asArray(items);
    if (!list.length) return [create("span", "empty", emptyText || "nenhuma")];
    return list.map(function (item) {
      var chip = create("span", "chip" + (className ? " " + className : ""), item.nome || "Nome não publicado");
      if (item.id !== null && item.id !== undefined) chip.dataset.skillId = String(item.id);
      if (item.complementar === true) {
        chip.dataset.complementar = "true";
        chip.title = "Complementar";
        chip.tabIndex = 0;
        chip.setAttribute("aria-label", chip.textContent + ". Complementar");
      }
      return chip;
    });
  }

  function renderPlaystyles(card) {
    var defensivePositions = ["GO", "ZC", "LE", "LD", "VOL"];
    var attackingPositions = ["CA", "SA", "PTE", "PTD", "MAT"];
    var position = card.posicao_nativa && card.posicao_nativa.codigo;
    var preferred = defensivePositions.indexOf(position) !== -1 ? "defensivo"
      : (attackingPositions.indexOf(position) !== -1 ? "ofensivo" : null);
    var styles = asArray(card.estilos_jogo).slice();
    styles.sort(function (a, b) {
      return Number(b.tipo === preferred) - Number(a.tipo === preferred) || Number(a.slot) - Number(b.slot);
    });
    var nodes = styles.map(function (style) {
      var knownType = style.tipo === "ofensivo" || style.tipo === "defensivo";
      var primary = style.tipo === preferred;
      var node = create("div", "playstyle" + (primary ? " is-primary" : "") + (!preferred ? " is-balanced" : ""));
      node.title = knownType ? "Estilo " + style.tipo : "Tipo de estilo não publicado";
      if (knownType) {
        var icon = create("img", "playstyle-icon");
        icon.src = PLAYSTYLE_ICONS[style.tipo];
        icon.alt = "";
        icon.setAttribute("aria-hidden", "true");
        node.appendChild(icon);
      }
      node.appendChild(create("span", "playstyle-name", style.nome || "Nome não publicado"));
      node.setAttribute("aria-label", node.title + ": " + (style.nome || "Nome não publicado"));
      return node;
    });
    replaceChildren("playstyle", nodes.length ? nodes : [create("span", "empty", "Estilos não publicados")]);
  }

  function renderCard(card, preparedPhoto) {
    setText("card-name", card.nome, "Nome não publicado");
    renderPhoto(card, preparedPhoto);
    renderPlaystyles(card);
    var native = card.posicao_nativa;
    if (isPlainObject(native)) {
      var node = byId("native-position");
      node.replaceChildren();
      node.appendChild(create("i", "", native.codigo || "—"));
      node.appendChild(document.createTextNode(native.nome || "Nome não publicado"));
    } else {
      setText("native-position", "Não publicada");
    }
    renderPitch(card.posicoes);
    replaceChildren("special-skills", chipNodes(card.habilidades_especiais, "special", "nenhuma habilidade especial"));
    replaceChildren("native-skills", chipNodes(card.habilidades_nativas, "", "nenhuma habilidade nativa"));
    var factorySkills = byId("native-skills").parentElement;
    factorySkills.style.setProperty("--special-count", Math.max(1, asArray(card.habilidades_especiais).length));
    factorySkills.style.setProperty("--native-count", Math.max(1, asArray(card.habilidades_nativas).length));
    replaceChildren("ia-styles", chipNodes(card.estilos_ia, "", "nenhum estilo de IA"));
    replaceChildren("physical", [
      create("span", "chip", (card.altura_cm === null ? "—" : card.altura_cm) + " cm"),
      create("span", "chip", (card.peso_kg === null ? "—" : card.peso_kg) + " kg"),
      create("span", "chip", (card.idade_anos === null ? "—" : card.idade_anos) + " anos"),
      create("span", "chip", "Lesão: " + (card.resistencia_lesao || "—"))
    ]);
    renderFoot(card, null);
  }

  function renderFoot(card, build) {
    var foot = asArray(card && card.pe).map(function (item) {
      var label = item.campo === "pe_dominante" ? "Pé bom" : (item.nome || "Pé");
      var row = create("div", "chip foot-detail");
      row.appendChild(create("span", "foot-label", label));
      row.appendChild(create("b", "foot-value", item.rotulo_valor || "Não publicado"));
      return row;
    });
    replaceChildren("foot", foot.length ? foot : [create("span", "empty", "sem dados de pé")]);
  }

  function renderBuildList(data) {
    var published = asArray(data.builds_publicadas);
    var groups = groupPublishedBuilds(published);
    groups.sort(function(a,b){return Number(b.notaFinal)-Number(a.notaFinal);});
    var scores=groups.map(function(g){return Number(g.notaFinal);}).filter(Number.isFinite);
    var lowest=Math.min.apply(Math,scores),highest=Math.max.apply(Math,scores);
    var playablePositionsTotal = playablePositionCount(data.card && data.card.posicoes);
    replaceChildren("builds-counts", [
      [groups.length, "do Sistema"],
      [playablePositionsTotal, playablePositionsTotal === 1 ? "Posição" : "Posições"],
      [personalState.records.length, personalState.records.length === 1 ? "Salva" : "Salvas"]
    ].map(function(item) {
      var badge = create("span", "builds-count");
      badge.appendChild(create("b", "", String(item[0])));
      badge.appendChild(create("span", "", item[1]));
      return badge;
    }));
    var scoresByNode = new Map();
    function sortableScore(value) {
      if (value === null || value === undefined || value === "") return -Infinity;
      var score = Number(value);
      return Number.isFinite(score) ? score : -Infinity;
    }
    var nodes = groups.map(function (group) {
      var positionLabel = group.positions.length ? group.positions.join("/") : "—";
      var node = create("button", "build");
      scoresByNode.set(node, sortableScore(group.notaFinal));
      var strength=highest>lowest?(Number(group.notaFinal)-lowest)/(highest-lowest):1;
      node.dataset.tone=String(Math.round(Math.max(0,Math.min(1,strength))*4));
      node.type = "button";
      node.appendChild(create("b", "", group.functionLabel));
      node.appendChild(create("em", "", positionLabel));
      node.appendChild(create("i", "", formatNumber(group.notaFinal, 2)));
      if (group.reguaVigente === false) node.appendChild(create("u", "build-regua-antiga", "Régua antiga"));
      node.title = "Linhas " + group.lineIds.join("/") + " · somente leitura" +
        (group.reguaVigente === false ? " · nota da régua anterior" : "");
      if (group.selected&&!personalState.selected) node.setAttribute("aria-current", "true");
      if (group.positions.length) {
        node.dataset.buildKey = group.identity;
        node.dataset.positionCodes = group.positions.join(" ");
        node.setAttribute("aria-pressed", "false");
        node.setAttribute("aria-label", group.functionLabel + ", posições " + group.positions.join(" e ") + ", nota " + formatNumber(group.notaFinal, 2) + ". Abrir esta build e destacar suas posições.");
        node.addEventListener("click", function () {
          selectPublishedBuild(data, group);
        });
      }
      return node;
    });
    personalState.records.forEach(function(record){
      var node=create("button","build saved");node.type="button";
      scoresByNode.set(node,sortableScore(record.resultado.nota_final));
      node.dataset.buildKey=record.id;node.dataset.positionCodes=record.build.posicao.codigo;node.setAttribute("aria-pressed","false");
      node.append(create("b","",record.rotulo),create("em","",record.build.posicao.codigo),create("i","",formatNumber(record.resultado.nota_final,2)));
      node.title=record.nome+" · "+(record.origem==="navegador"?"Neste navegador":"Na sua conta")+" · somente consulta";
      node.onclick=function(){personalState.selected=record;renderBuild(data,"pronto");applyLinkedSelection([record.build.posicao.codigo],record.id,"build");};
      if(personalState.selected&&personalState.selected.id===record.id)node.setAttribute("aria-current","true");
      nodes.push(node);
    });
    // Classificação conjunta pela nota original, antes do recorte de vinte itens.
    // Em empate exato, o modelo do sistema precede a cópia; demais empates são estáveis.
    nodes.sort(function(a,b){
      return scoresByNode.get(b)-scoresByNode.get(a) ||
        Number(a.classList.contains("saved"))-Number(b.classList.contains("saved"));
    });
    var more=byId("more-builds-action");
    if(more){more.hidden=nodes.length<=20;more.textContent=personalState.expanded?"⌃ Ver menos":"⌄ Ver mais builds ("+(nodes.length-20)+")";more.setAttribute("aria-expanded",String(personalState.expanded));more.setAttribute("aria-controls","builds-list");more.onclick=function(){personalState.expanded=!personalState.expanded;rememberBuildExpansion();renderBuildList(data);applyLinkedSelection(linkedSelection.positionCodes,linkedSelection.buildKey,linkedSelection.source);};}
    replaceChildren("builds-list", nodes.length ? (personalState.expanded?nodes:nodes.slice(0,20)) : [create("span", "empty", "nenhuma build publicada")]);
    return groups;
  }

  function renderDistribution(build) {
    var bars = asArray(build && build.barras);
    var nodes = bars.map(function (bar) {
      var row = create("div", "bar");
      row.appendChild(create("span", "bar-name", bar.rotulo || bar.chave));
      row.appendChild(create("span", "bar-value", bar.valor === null ? "—" : bar.valor));
      return row;
    });
    replaceChildren("distribution", nodes.length ? nodes : [create("div", "empty", "sem distribuição publicada")]);
  }

  var technicianResizeObserver = null;
  function fitTechnicianBoosts() {
    var target = byId("technician-boosts");
    if (!target || !target.dataset.full || !target.clientWidth) return;
    target.textContent = target.dataset.full;
    if (target.scrollWidth > target.clientWidth) {
      target.textContent = target.dataset.full.replace(/Talento ofensivo/gi, "T. Ofensivo").replace(/Talento defensivo/gi, "T. Defensivo");
    }
  }
  function renderTechnician(technician) {
    renderSuggestions("suggested-technicians", technician && technician.sugeridos,
      technician && technician.sugeridos_estado === "pronto" ? "nenhum técnico equivalente para esta build" : "nenhum técnico equivalente publicado");
    if (!isPlainObject(technician)) {
      setText("technician", "Não publicado");
      setText("technician-boosts", "—");
      byId("technician-boosts").dataset.full = "";
      return;
    }
    setText("technician", technician.nome, "Nome não publicado");
    var boosts = asArray(technician.atributos).map(function (item) {
      return (item.nome || "Atributo") + " " + formatSigned(item.delta, 0);
    });
    setText("technician-boosts", boosts.join(" · "), "sem bônus de técnico publicado");
    byId("technician-boosts").dataset.full = boosts.join(" · ");
    byId("technician-boosts").title = boosts.join(" · ");
    if (typeof ResizeObserver === "function" && !technicianResizeObserver) {
      technicianResizeObserver = new ResizeObserver(fitTechnicianBoosts);
      technicianResizeObserver.observe(byId("technician-boosts"));
    }
    fitTechnicianBoosts();
  }

  function renderSuggestions(target, items, emptyText) {
    var nodes = asArray(items).map(function (item) {
      var node = create("div", "suggestion");
      node.appendChild(create("b", "suggestion-name", item.nome || "Nome não publicado"));
      var substitutes = asArray(item.substitui).map(function (skill) {
        return skill.nome || "Nome não publicado";
      });
      if (substitutes.length) {
        node.title = "Mantém a nota no lugar de " + substitutes.join(" ou ") + ". Substitua somente uma delas por vez. Build do sistema: somente consulta.";
        node.tabIndex = 0;
        node.setAttribute("aria-label", (item.nome || "Habilidade") + ". " + node.title);
      } else if (target === "suggested-technicians") {
        node.classList.add("technician-substitute");
        node.dataset.technicianId=String(item.id);
        var row=create("div","technician-substitute-row");
        row.appendChild(node.firstElementChild);
        var attributes=Array.isArray(item.atributos)?item.atributos.map(function(a){return (a.nome||"Atributo")+" "+formatSigned(a.delta,0);}).join(" · "):null;
        var effects=create("span","suggestion-boosts",attributes===null?"Atributos não publicados":attributes||"Sem bônus de atributos");
        effects.title=effects.textContent;row.appendChild(effects);node.appendChild(row);
        node.title = (item.nome||"Técnico")+" · "+effects.textContent+". Técnico substituto para esta build.";
      }
      return node;
    });
    replaceChildren(target, nodes.length ? nodes : [create("span", "empty", emptyText)]);
    if (target === "suggested-skills") {
      Array.from(byId("added-skills").children).forEach(function (chip) {
        if (chip.dataset.complementar === "true") return;
        var alternatives = asArray(items).filter(function (item) {
          return asArray(item.substitui).some(function (skill) {
            return String(skill.id) === chip.dataset.skillId;
          });
        }).map(function (item) { return item.nome || "Nome não publicado"; });
        chip.title = alternatives.length
          ? "Pode ser trocada por " + alternatives.join(" ou ") + ". Escolha uma por vez para manter a nota. Build do sistema: somente consulta."
          : "";
        if (alternatives.length) {
          chip.tabIndex = 0;
          chip.setAttribute("aria-label", chip.textContent + ". " + chip.title);
        }
      });
    }
  }

  function renderImpulses(impulses, data) {
    var nodes = asArray(impulses).map(function (item) {
      var type = item.tipo === "adicional" ? "adicional" : "nativo";
      var allowedColors = ["azul", "verde", "roxo", "amarelo", "dourado"];
      var visualColor = allowedColors.indexOf(item.cor_visual) !== -1
        ? item.cor_visual
        : (item.vaga_original && !item.codigo ? "cinza" : "pendente");
      var box = create(
        "div",
        "impulse impulse-color-" + visualColor + (type === "nativo" ? " is-fixed" : "")
      );
      var condition = item.condicao_nivel === null || item.condicao_nivel === undefined
        ? ""
        : " · nível " + item.condicao_nivel;
      box.setAttribute("aria-label", "Ímpeto " + item.slot + " · " + type + condition);
      var title = create("div", "impulse-title");
      title.appendChild(create("b", "", item.nome || (item.vaga_original ? "Vaga sem preenchimento" : "Não publicado")));
      var next = data && data.proximo_degrau;
      var conditional = item.condicao_nivel !== null && item.condicao_nivel !== undefined;
      var boost = create(conditional ? "button" : "span", "boost", conditional ? "+" + item.condicao_nivel : item.delta_uniforme === null ? "—" : formatSigned(item.delta_uniforme, 0));
      if (conditional) {
        boost.type = "button";
        boost.disabled = !next;
        boost.title = next ? "Mostrar ímpeto condicional +" + next.nivel : "Próximo degrau ainda não publicado";
        boost.setAttribute("aria-label", boost.title);
        boost.onclick = function () {
          if (!next) return;
          if (window.SiteNovoDegrau && typeof window.SiteNovoDegrau.set === "function") {
            window.SiteNovoDegrau.set(Number(next.nivel));
          }
        };
      }
      title.appendChild(boost);
      box.appendChild(title);
      var effects = create("div", "mini-chips");
      asArray(item.efeitos).forEach(function (effect) {
        effects.appendChild(create("span", "", (effect.nome || "Atributo") + " " + formatSigned(effect.delta, 0)));
      });
      box.appendChild(effects);
      return box;
    });
    replaceChildren("impulses", nodes.length ? nodes : [create("div", "empty", "sem ímpetos publicados")]);
  }

  function renderAttributes(build, status) {
    var complete = Boolean(build && build.atributos_completos);

    var groupOrder = ["ataque", "atletismo", "fisico", "defesa", "goleiro"];
    var groupLabels = {
      ataque: "ATAQUE",
      atletismo: "ATLETISMO",
      fisico: "FÍSICO",
      defesa: "DEFESA",
      goleiro: "GOLEIRO"
    };
    var attrs = asArray(build && build.atributos);
    var groups = groupOrder.map(function (groupName) {
      var group = create("div", "attribute-group");
      var title = create("div", "group-title");
      title.appendChild(create("span", "group-name", groupLabels[groupName]));
      title.appendChild(create("b", "group-base", "BASE"));
      title.appendChild(create("b", "group-jogo", "JOGO"));
      title.appendChild(create("b", "group-final", "FINAL"));
      group.appendChild(title);
      attrs.filter(function (item) {
        return item.grupo_tela === groupName;
      }).forEach(function (item) {
        var row = create("div", "attribute" + (complete ? "" : " low"));
        row.dataset.attributeCode = item.codigo || item.codigo_atributo;
        row.appendChild(create("span", "attr-name", item.nome || "Atributo não publicado"));
        row.appendChild(create("span", "attr-base", item.valor_base == null ? "—" : item.valor_base));
        row.appendChild(create("span", "attr-jogo", item.valor_jogo == null ? "—" : item.valor_jogo));
        row.appendChild(create("span", "attr-final", item.valor_sistema == null ? "—" : item.valor_sistema));
        var afterEvolution = item.valor_pos_evolucao == null ? "não publicado" : item.valor_pos_evolucao;
        row.title = "Base: " + (item.valor_base == null ? "não publicada" : item.valor_base) +
          " · No jogo: " + (item.valor_jogo == null ? "não publicado" : item.valor_jogo) +
          " · Pós-evolução: " + afterEvolution +
          " · JOGO é o número que a tela do videogame mostra, sem valoração das habilidades. FINAL é o valor interno que o sistema usa na avaliação." +
          (item.valor_sistema == null ? " Valor do sistema não disponível neste registro; para uma build pessoal antiga, reabra no editor e salve a avaliação atual." : "");
        group.appendChild(row);
      });
      return group;
    });
    replaceChildren("attribute-columns", groups);
  }

  function renderBody(card, build) {
    var fullNames = {
      tamBraco: "Tamanho do braço",
      tamPescoco: "Tamanho do pescoço",
      comprPerna: "Comprimento da perna",
      comprBraco: "Comprimento do braço",
      comprPescoco: "Comprimento do pescoço",
      largOmbro: "Largura do ombro",
      altOmbro: "Altura do ombro"
    };
    // Altura primeiro; demais medidas em ordem anatomica, de baixo para cima.
    var bodyOrder = ['altura','panturrilha','coxa','comprPerna','cintura','peito','tamBraco','comprBraco','largOmbro','altOmbro','tamPescoco','comprPescoco'];
    var measures = asArray(card.corpo).slice().sort(function (a, b) {
      var ia = bodyOrder.indexOf(a.chave_bonus), ib = bodyOrder.indexOf(b.chave_bonus);
      return (ia < 0 ? bodyOrder.length : ia) - (ib < 0 ? bodyOrder.length : ib);
    });
    var splitAt = Math.ceil(measures.length / 2);
    var columns = [measures.slice(0, splitAt), measures.slice(splitAt)].map(function (list) {
      var column = create("div");
      var header = create("div", "measure head");
      header.appendChild(create("span", "", "Medida"));
      header.appendChild(create("b", "", "No card"));
      column.appendChild(header);
      list.forEach(function (item) {
        var row = create("div", "measure");
        row.appendChild(create("span", "", fullNames[item.chave_bonus] || item.nome || "Medida"));
        row.appendChild(create("b", "", item.valor === null ? "—" : (item.chave_bonus === "altura" ? item.valor + " cm" : item.valor)));
        column.appendChild(row);
      });
      return column;
    });
    replaceChildren("body-measures", columns);
  }

  function renderSeloRegua(build) {
    var antiga = isPlainObject(build) && build.regua_vigente === false;
    ["score-top", "score-main"].forEach(function (id) {
      var alvo = byId(id);
      if (!alvo || !alvo.parentNode) return;
      var selo = alvo.parentNode.querySelector(".fc-selo-antiga");
      if (!antiga) { if (selo) selo.remove(); return; }
      if (!selo) {
        selo = document.createElement("span");
        selo.className = "fc-selo-antiga";
        alvo.parentNode.insertBefore(selo, alvo.nextSibling);
      }
      selo.textContent = "Régua antiga";
      selo.title = "Esta nota foi calculada com a régua anterior. A linha ainda não passou pelo Otimizador novo.";
    });
  }

  function renderCurrentScore(data, build, currentScore) {
    var score = formatNumber(currentScore, 2);
    var improvement = improvementAgainstReadyBuilds(data, build, currentScore);
    setText("score-top", score);
    setText("score-main", score);
    renderImprove("improve-top", improvement);
    renderImprove("improve-main", improvement);
    renderSeloRegua(build);
    return score;
  }

  function renderBudget(build) {
    var points = build && build.pontos_distribuicao;
    var total = points && points.total !== null && points.total !== undefined ? points.total : (build && build.orcamento_total);
    var knownTotal = typeof total === "number" && Number.isInteger(total) && total >= 0;
    var remaining = points && points.restantes;
    var valid = points && points.estado === "valido" && knownTotal &&
      typeof remaining === "number" && Number.isInteger(remaining) && remaining >= 0 && remaining <= total;
    var text = (valid ? remaining : "—") + "/" + (knownTotal ? total : "—");
    setText("budget-summary", text);
    var node = byId("budget-summary");
    node.title = valid ? remaining + " pontos restantes de " + total + " pontos no total" : "Pontos restantes não publicados";
    node.setAttribute("aria-label", node.title);
  }

  function renderBuild(data, status) {
    if(personalState.selected&&personalState.selected.card_id===data.card.card_id)data=Object.assign({},data,{build:personalState.selected.build});
    var build = data.build;
    var groups = renderBuildList(data);
    renderBuildModes(data, build);
    if (!isPlainObject(build)) {
      renderCurrentScore(data, null, null);
      renderBudget(null);
      renderDistribution(null);
      renderTechnician(null);
      setText("added-skills-label", "HABILIDADES ADICIONADAS · 0 DE 5");
      replaceChildren("added-skills", chipNodes([], "added", "nenhuma"));
      renderSuggestions("suggested-skills", [], "nenhuma sugestão publicada para esta build");
      renderImpulses([]);
      renderAttributes(null, status);
      renderFoot(data.card, null);
      renderBody(data.card, null);
      return;
    }

    renderCurrentScore(data, build, build.nota_final);

    var noEvolution = Boolean(build.evolucao && build.evolucao.sem_evolucao);
    renderBudget(build);
    renderDistribution(build);
    renderTechnician(build.tecnico);
    var added = asArray(build.habilidades_adicionadas);
    setText("added-skills-label", "HABILIDADES ADICIONADAS · " + added.length + " DE 5");
    replaceChildren("added-skills", chipNodes(added, "added", noEvolution ? "não aceita habilidades adicionais" : "nenhuma adicionada"));
    renderSuggestions("suggested-skills", build.habilidades_sugeridas, noEvolution ? "não aceita habilidades adicionais" :
      (build.habilidades_sugeridas_estado === "pronto" ? "nenhuma habilidade gêmea disponível nesta build" : "nenhuma sugestão publicada para esta build"));
    renderImpulses(build.impetos, data);
    renderAttributes(build, status);
    renderFoot(data.card, build);
    renderBody(data.card, build);
  }

  function renderEnvelope(envelope, highlightRequestedBuild, preparedPhoto) {
    if (envelope.status === "parametro_ausente") {
      envelope.mensagem = "Informe ?card=<card_id> na URL para abrir a Ficha.";
    }
    renderLayoutState(envelope.status);
    renderMessage(envelope);
    if (!CARD_STATUSES.has(envelope.status)) return;
    renderCard(envelope.dados.card, preparedPhoto);
    renderBuild(envelope.dados, envelope.status);
    var selectedGroup = highlightRequestedBuild
      ? groupPublishedBuilds(envelope.dados.builds_publicadas).find(function (group) {
        return group.selected;
      })
      : null;
    if (selectedGroup) {
      applyLinkedSelection(selectedGroup.positions, selectedGroup.identity, "build");
    } else {
      applyLinkedSelection(null, null, null);
    }
  }

  function renderFailure(error) {
    renderLayoutState("erro");
    var message = byId("screen-message");
    message.hidden = false;
    message.textContent = error && error.message ? error.message : "Não foi possível consultar a Ficha.";
  }

  function renderSwitchFailure(error) {
    var message = byId("screen-message");
    message.hidden = false;
    message.textContent = "Não foi possível abrir esta build. A build anterior foi mantida. " +
      (error && error.message ? error.message : "Falha na consulta pública.");
  }

  function setLoading(isLoading) {
    var ficha = byId("ficha");
    if (!ficha) return;
    ficha.setAttribute("aria-busy", isLoading ? "true" : "false");
  }

  function revealPopulatedFicha(envelope) {
    // A barreira já existe no HTML: nenhum quadro vazio aparece antes do JS.
    // Não liberar no finally: erro de rede ou resposta sem card não é uma Ficha.
    var visible = CARD_STATUSES.has(envelope.status) && isPlainObject(envelope.dados);
    byId("ficha-content").hidden = !visible;
    byId("ficha").classList.toggle("awaiting-data", !visible);
    if (visible) restoreInitialScroll();
  }

  function selectedGroupForEnvelope(envelope, requestedLine) {
    if (!requestedLine || !envelope || !envelope.dados) return null;
    return groupPublishedBuilds(envelope.dados.builds_publicadas).find(function (group) {
      return group.selected;
    }) || null;
  }

  function assertSwitchResponse(envelope, params) {
    if (!CARD_STATUSES.has(envelope.status) || !isPlainObject(envelope.dados)) {
      throw new Error(envelope.mensagem || "A linha pedida não está disponível.");
    }
    var returnedCard = String(envelope.dados.card && envelope.dados.card.card_id || "").trim();
    if (returnedCard !== String(params.p_card_id || "").trim()) {
      throw new Error("A consulta retornou outro card.");
    }
    var returnedLine = lineIdText(envelope.dados.build && envelope.dados.build.linha_id);
    if (params.p_linha_id !== null && returnedLine !== lineIdText(params.p_linha_id)) {
      throw new Error(envelope.mensagem || "A consulta não retornou a linha pedida.");
    }
  }

  function renderBuildEnvelope(envelope, requestedLine) {
    renderLayoutState(envelope.status);
    renderMessage(envelope);
    renderBuild(envelope.dados, envelope.status);
    var selectedGroup = selectedGroupForEnvelope(envelope, requestedLine);
    if (selectedGroup) {
      applyLinkedSelection(selectedGroup.positions, selectedGroup.identity, "build");
    } else {
      applyLinkedSelection(null, null, null);
    }
  }

  async function loadFicha(params, options) {
    var settings = options || {};
    var requestVersion = ++viewState.requestVersion;
    if (viewState.requestController) viewState.requestController.abort();
    var requestController = new AbortController();
    viewState.requestController = requestController;
    setLoading(true);
    try {
      var envelope = await fetchFicha(params, requestController.signal);
      if (requestVersion !== viewState.requestVersion) return;

      if (settings.mode === "initial" && params.p_linha_id === null &&
          window.SiteNovoDegrau && typeof window.SiteNovoDegrau.get === "function") {
        var initialDegree = window.SiteNovoDegrau.get();
        var initialLine = conditionalLine(envelope.dados, initialDegree);
        if (initialLine && conditionalDegree(envelope.dados) !== initialDegree) {
          params = { p_card_id: params.p_card_id, p_linha_id: initialLine };
          envelope = await fetchFicha(params, requestController.signal);
          if (requestVersion !== viewState.requestVersion) return;
          assertSwitchResponse(envelope, params);
          settings.targetUrl = buildUrl(params.p_card_id, String(initialLine));
          settings.replaceInitialUrl = true;
        }
      }

      if (settings.mode === "switch" || settings.mode === "popstate") {
        assertSwitchResponse(envelope, params);
      }

      var previousCard = viewState.envelope && viewState.envelope.dados
        ? String(viewState.envelope.dados.card.card_id || "")
        : null;
      var nextCard = envelope.dados && envelope.dados.card
        ? String(envelope.dados.card.card_id || "")
        : null;
      var canUpdateBuildOnly = settings.mode !== "initial" && previousCard && previousCard === nextCard;
      personalState.selected=null;
      if(personalState.cardId!==nextCard){personalState.cardId=nextCard;personalState.records=[];personalState.expanded=readBuildExpansion(nextCard);}

      var preparedPhoto = null;
      if (!canUpdateBuildOnly && CARD_STATUSES.has(envelope.status)) {
        // The public content does not wait for the image server.
        preparePhoto(envelope.dados.card, requestController.signal).then(function(photo){
          if(requestVersion===viewState.requestVersion && photo)renderPhoto(envelope.dados.card,photo);
        });
      }

      if (canUpdateBuildOnly) {
        renderBuildEnvelope(envelope, params.p_linha_id);
      } else {
        renderEnvelope(envelope, params.p_linha_id !== null, preparedPhoto);
      }

      if (settings.mode === "switch" && settings.targetUrl) {
        window.history.pushState(null, "", settings.targetUrl);
      } else if (settings.replaceInitialUrl && settings.targetUrl) {
        window.history.replaceState(null, "", settings.targetUrl);
      }
      viewState.envelope = envelope;
      viewState.successfulUrl = settings.targetUrl || window.location.href;
      synchronizeConditionalDegree(envelope.dados);
      refreshPersonalBuilds();
      if(requestVersion!==viewState.requestVersion)return;
      revealPopulatedFicha(envelope);
    } catch (error) {
      if (requestVersion !== viewState.requestVersion) return;
      if (settings.mode === "initial") {
        renderFailure(error);
      } else {
        if (settings.mode === "popstate" && window.location.href !== viewState.successfulUrl) {
          window.history.replaceState(null, "", viewState.successfulUrl);
        }
        renderSwitchFailure(error);
      }
    } finally {
      if (requestVersion === viewState.requestVersion) {
        viewState.requestController = null;
        setLoading(false);
      }
    }
  }

  function start() {
    scrollState.pending = readSavedScroll();
    try {
      var params = readParams();
      loadFicha(params, { mode: "initial", targetUrl: window.location.href });
    } catch (error) {
      renderFailure(error);
      setLoading(false);
    }
  }

  if (window.SiteNovoDegrau && typeof window.SiteNovoDegrau.subscribe === "function") {
    window.SiteNovoDegrau.subscribe(selectConditionalDegree);
  }

  window.addEventListener("popstate", function () {
    try {
      var params = readParams();
      loadFicha(params, { mode: "popstate", targetUrl: window.location.href });
    } catch (error) {
      if (window.location.href !== viewState.successfulUrl) {
        window.history.replaceState(null, "", viewState.successfulUrl);
      }
      renderSwitchFailure(error);
    }
  });

  window.addEventListener("scroll", function () {
    if (!scrollState.ready) return;
    clearTimeout(scrollState.timer);
    scrollState.timer = setTimeout(saveScrollPosition, 150);
  }, { passive: true });
  window.addEventListener("pagehide", saveScrollPosition);

  async function refreshPersonalBuilds(){
    var api=window.FichaEditorAPI,envelope=viewState.envelope;
    if(!api||!envelope||!envelope.dados)return;
    var cardId=envelope.dados.card.card_id,version=++personalState.version;
    try{
      var records=await api.list(cardId);
      if(version!==personalState.version||!viewState.envelope||viewState.envelope.dados.card.card_id!==cardId)return;
      if(!Array.isArray(records)||records.some(function(r){return !r||r.card_id!==cardId||!r.build||!r.build.posicao||!r.resultado;}))throw new Error("Resposta de builds pessoais inválida.");
      var selectedId=personalState.selected&&personalState.selected.id;
      personalState.records=records;personalState.selected=records.find(function(r){return r.id===selectedId;})||null;
      byId("personal-builds-status").hidden=true;
      var data=viewState.envelope.dados;
      if(selectedId)renderBuild(data,viewState.envelope.status);
      else {var groups=renderBuildList(data);renderBuildModes(data,data.build);}
      applyLinkedSelection(personalState.selected?[personalState.selected.build.posicao.codigo]:linkedSelection.positionCodes,personalState.selected?personalState.selected.id:linkedSelection.buildKey,personalState.selected?"build":linkedSelection.source);
    }catch(e){if(version===personalState.version){setText("personal-builds-status","Não foi possível carregar as builds pessoais. "+e.message);byId("personal-builds-status").hidden=false;}}
  }
  window.addEventListener("ficha-builds-changed",refreshPersonalBuilds);
  window.addEventListener("storage",function(e){if(e.key==="clubefut.personal-builds.v1")refreshPersonalBuilds();});
  window.addEventListener("ficha-account-changed",function(){
    personalState.version++;personalState.records=[];personalState.selected=null;
    if(viewState.envelope&&viewState.envelope.dados)renderBuild(viewState.envelope.dados,viewState.envelope.status);
    refreshPersonalBuilds();
  });
  window.FichaView=Object.freeze({renderComparison:function(node,data,functionId,score){
    renderImprove(node,improvementAgainstReadyBuilds(data,{funcao:{id:functionId}},score));
  }});

  start();
}());
