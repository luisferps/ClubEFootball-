"""Runtime V4.6.12: varredura responsiva e conferência antes da escrita."""
from __future__ import annotations

import re
import threading
import webbrowser
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlparse

import servidor_v4610 as previous


RUNTIME_VERSION = "4.6.12"
DEFAULT_PORT = 8776

previous.RUNTIME_VERSION = RUNTIME_VERSION
previous.DEFAULT_PORT = DEFAULT_PORT
previous.legacy.RUNTIME_VERSION = RUNTIME_VERSION
previous.legacy.DEFAULT_PORT = DEFAULT_PORT


def _replace_literal_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(
            f"patch V4.6.12 não encontrou trecho único: {label} "
            f"(encontrados={count})"
        )
    return source.replace(old, new, 1)


def _replace_literal_count(
    source: str,
    old: str,
    new: str,
    expected: int,
    label: str,
) -> str:
    count = source.count(old)
    if count != expected:
        raise RuntimeError(
            f"patch V4.6.12 encontrou quantidade inesperada: {label} "
            f"(esperados={expected}; encontrados={count})"
        )
    return source.replace(old, new)


def patched_contract_reader_source() -> str:
    path = Path(previous.legacy.base.ROOT) / "app" / "leitura-contrato.js"
    source = path.read_text(encoding="utf-8-sig")

    marker = "  async function decodeFile(plan, fileName, bytes, fieldKeys = null) {"
    helper = """  let clubefLastResponsiveYield = 0;
  async function clubefResponsiveYield(force = false) {
    const now = performance.now();
    if (!force && now - clubefLastResponsiveYield < 12) return;
    clubefLastResponsiveYield = now;
    await new Promise((resolve) => setTimeout(resolve, 0));
  }

  async function decodeFile(plan, fileName, bytes, fieldKeys = null) {"""
    source = _replace_literal_once(
        source,
        marker,
        helper,
        "helper cooperativo do leitor contratual",
    )

    old_loop = """    const records = [];
    for (let base = 0, recordIndex = 0; base < bytes.length; base += file.tamanho_registro, recordIndex += 1) {
      const values = {};
      for (const field of fields.filter((item) => item.tipo_leitura !== 'id_mask')) values[field.chave_campo] = transformed(rawValue(bytes, base, field, values), field);
      for (const field of fields.filter((item) => item.tipo_leitura === 'id_mask')) values[field.chave_campo] = transformed(rawValue(bytes, base, field, values), field);
      records.push({ record_index: recordIndex, values });
    }"""
    new_loop = """    const directFields = fields.filter((item) => item.tipo_leitura !== 'id_mask');
    const maskFields = fields.filter((item) => item.tipo_leitura === 'id_mask');
    const records = [];
    for (let base = 0, recordIndex = 0; base < bytes.length; base += file.tamanho_registro, recordIndex += 1) {
      if ((recordIndex & 127) === 0) await clubefResponsiveYield();
      const values = {};
      for (const field of directFields) values[field.chave_campo] = transformed(rawValue(bytes, base, field, values), field);
      for (const field of maskFields) values[field.chave_campo] = transformed(rawValue(bytes, base, field, values), field);
      records.push({ record_index: recordIndex, values });
    }"""
    source = _replace_literal_once(
        source,
        old_loop,
        new_loop,
        "decodificação contratual em lotes responsivos",
    )
    return source + "\n//# sourceURL=/app/leitura-contrato-v4612.js\n"


def _responsive_core_helpers() -> str:
    return r"""
  let clubefLastCoreYield = 0;
  async function cooperativeYield(force = false) {
    const now = performance.now();
    if (!force && now - clubefLastCoreYield < 12) return;
    clubefLastCoreYield = now;
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
  async function cooperativeMap(items, mapper, chunkSize = 128) {
    const output = new Array(items.length);
    for (let index = 0; index < items.length; index += 1) {
      output[index] = mapper(items[index], index);
      if ((index + 1) % chunkSize === 0) await cooperativeYield(true);
    }
    return output;
  }

  async function unpackWesys(data) {"""


def _responsive_card_functions() -> str:
    return r"""
  async function prepareCardRowsResponsive(cards, chunkSize = 96) {
    const rows = new Array(cards.length);
    const seen = new Set();
    const duplicates = new Set();
    const missingByField = Object.fromEntries(CARD_COLUMNS.map((column) => [column, 0]));
    const typeCounts = { base: 0, colecionavel: 0, teste: 0 };
    const positionCounts = new Map();

    for (let index = 0; index < cards.length; index += 1) {
      const row = cardToRow(cards[index]);
      rows[index] = row;
      const id = String(row.card_id);
      if (seen.has(id)) duplicates.add(id); else seen.add(id);
      for (const column of CARD_COLUMNS) if (row[column] === '') missingByField[column] += 1;
      typeCounts[row.tipo] = (typeCounts[row.tipo] || 0) + 1;
      positionCounts.set(row.posicao, (positionCounts.get(row.posicao) || 0) + 1);
      if ((index + 1) % chunkSize === 0) await cooperativeYield(true);
    }

    const sortIds = (left, right) => BigInt(left) < BigInt(right) ? -1 : 1;
    const positions = Object.fromEntries([...positionCounts].sort(([left], [right]) => String(left).localeCompare(String(right))));
    return {
      rows,
      validation: {
        records: rows.length,
        unique_card_ids: seen.size,
        duplicate_card_ids: [...duplicates].sort(sortIds),
        schema: CARD_COLUMNS,
        missing_by_field: missingByField,
        types: typeCounts,
        positions
      }
    };
  }

  async function rowsToCsvResponsive(rows, chunkSize = 96) {
    const lines = new Array(rows.length + 1);
    lines[0] = CARD_COLUMNS.join(',');
    for (let index = 0; index < rows.length; index += 1) {
      const row = rows[index];
      lines[index + 1] = CARD_COLUMNS.map((column) => quoteCsv(row[column] || '')).join(',');
      if ((index + 1) % chunkSize === 0) await cooperativeYield(true);
    }
    return `\uFEFF${lines.join('\n')}`;
  }

  async function cardsToCsvResponsive(cards, chunkSize = 96) {
    const prepared = await prepareCardRowsResponsive(cards, chunkSize);
    return rowsToCsvResponsive(prepared.rows, chunkSize);
  }

  async function compareCardRowsResponsive(currentRows, baselineRows, chunkSize = 64) {
    const current = new Map();
    const baseline = new Map();
    const currentDuplicates = new Set();
    const baselineDuplicates = new Set();

    for (let index = 0; index < currentRows.length; index += 1) {
      const row = currentRows[index];
      const id = String(row.card_id);
      if (current.has(id)) currentDuplicates.add(id); else current.set(id, row);
      if ((index + 1) % chunkSize === 0) await cooperativeYield(true);
    }
    for (let index = 0; index < baselineRows.length; index += 1) {
      const row = baselineRows[index];
      const id = String(row.card_id);
      if (baseline.has(id)) baselineDuplicates.add(id); else baseline.set(id, row);
      if ((index + 1) % chunkSize === 0) await cooperativeYield(true);
    }
    if (currentDuplicates.size || baselineDuplicates.size) {
      throw new Error(`Comparação bloqueada: card_id duplicado (atual ${currentDuplicates.size}, base ${baselineDuplicates.size}).`);
    }

    const newCards = [];
    const changedCards = [];
    const inactiveCards = [];
    let processed = 0;
    for (const [id, row] of current) {
      const before = baseline.get(id);
      if (!before) {
        newCards.push(row);
      } else {
        const fields = [];
        for (const column of CARD_COLUMNS) {
          if (column === 'card_id') continue;
          if (comparableCardValue(column, before[column]) !== comparableCardValue(column, row[column])) {
            fields.push({ field: column, before: before[column] || '', after: row[column] || '' });
          }
        }
        if (fields.length) changedCards.push({ card_id: id, fields, row });
      }
      processed += 1;
      if (processed % chunkSize === 0) await cooperativeYield(true);
    }

    processed = 0;
    for (const [id, row] of baseline) {
      if (!current.has(id)) inactiveCards.push({ card_id: id, name: row.nome || '', type: row.tipo || '', row });
      processed += 1;
      if (processed % chunkSize === 0) await cooperativeYield(true);
    }

    const sortById = (left, right) => BigInt(left.card_id) < BigInt(right.card_id) ? -1 : 1;
    newCards.sort(sortById);
    changedCards.sort(sortById);
    inactiveCards.sort(sortById);
    return {
      new_cards: newCards,
      changed_cards: changedCards,
      possibly_inactive: inactiveCards,
      unchanged: currentRows.length - newCards.length - changedCards.length
    };
  }

  async function validateCardDimensionsSnapshotResponsive(snapshot, chunkSize = 128) {
    if (!snapshot || snapshot.contract !== CARD_DIMENSIONS_CONTRACT_VERSION) throw new Error('Contrato físico de Dimensões incompatível.');
    const cards = snapshot.cards;
    const catalogs = snapshot.catalogs || {};
    if (!Array.isArray(cards) || !cards.length) throw new Error('A fotografia de Dimensões não contém cartas.');
    for (const name of ['nationalities', 'clubs', 'leagues', 'types']) {
      if (!Array.isArray(catalogs[name]) || !catalogs[name].length) throw new Error(`Catálogo físico ausente: ${name}.`);
    }

    const nationalityIds = new Set(catalogs.nationalities.map((record) => Number(record.codigo_jogo)));
    const clubIds = new Set(catalogs.clubs.map((record) => Number(record.codigo_jogo)));
    const leagueIds = new Set(catalogs.leagues.map((record) => Number(record.codigo_jogo)));
    const typeIds = new Set(catalogs.types.map((record) => record.tipo_carta_id));
    const ids = new Set();
    let invalidCount = 0;

    for (let index = 0; index < cards.length; index += 1) {
      const card = cards[index];
      const id = String(card.card_id);
      if (ids.has(id)) throw new Error('A fotografia de Dimensões contém card_id duplicado.');
      ids.add(id);
      if (!nationalityIds.has(card.codigo_nacionalidade)
        || (card.codigo_clube !== null && !clubIds.has(card.codigo_clube))
        || (card.codigo_liga !== null && !leagueIds.has(card.codigo_liga))
        || !typeIds.has(card.tipo_carta_id)) invalidCount += 1;
      if ((card.tipo_carta_id === 'player_type_4_subtype_0' || card.tipo_carta_id === 'player_type_7_subtype_0')
        && card.chave_tipo_carta !== null) {
        throw new Error('Tipo provisório recebeu chave oficial indevida.');
      }
      if ((index + 1) % chunkSize === 0) await cooperativeYield(true);
    }
    if (invalidCount) throw new Error(`A fotografia de Dimensões contém ${invalidCount} vínculo(s) órfão(s).`);
    return {
      contract: CARD_DIMENSIONS_CONTRACT_VERSION,
      passed: true,
      cards: cards.length,
      unique_card_ids: ids.size,
      counts: snapshot.counts,
      orphan_count: 0,
      database_write: false
    };
  }

"""


def patched_core_source() -> str:
    path = Path(previous.legacy.base.ROOT) / "app" / "extrator-core.js"
    source = path.read_text(encoding="utf-8-sig")

    source = _replace_literal_once(
        source,
        "  async function unpackWesys(data) {",
        _responsive_core_helpers(),
        "helpers cooperativos do núcleo",
    )
    source = _replace_literal_once(
        source,
        "    for (let offset = 0; offset < aligned; offset += 4) {",
        "    for (let offset = 0; offset < aligned; offset += 4) {\n      if ((offset & 0x3ffff) === 0) await cooperativeYield();",
        "desofuscação WESYS responsiva",
    )
    source = _replace_literal_once(
        source,
        "      for (let offset = 0; offset < raw.length; offset += 168) {",
        "      for (let offset = 0; offset < raw.length; offset += 168) {\n        if ((offset % (168 * 256)) === 0) await cooperativeYield();",
        "boxes em lotes",
    )
    source = _replace_literal_once(
        source,
        "    for (let offset = 0; offset < rawPlayers.length; offset += K.RECORD_SIZE) {",
        "    for (let offset = 0; offset < rawPlayers.length; offset += K.RECORD_SIZE) {\n      if ((offset % (K.RECORD_SIZE * 128)) === 0) await cooperativeYield();",
        "cartas em lotes",
    )
    source = _replace_literal_once(
        source,
        "    const contractSlots = await extractCardSlotsByContract(bytes, readingContract);\n    for (const card of cards) {",
        "    const contractSlots = await extractCardSlotsByContract(bytes, readingContract);\n    for (let cardIndex = 0; cardIndex < cards.length; cardIndex += 1) {\n      if ((cardIndex & 127) === 0) await cooperativeYield();\n      const card = cards[cardIndex];",
        "vínculo de slots em lotes",
    )
    source = _replace_literal_once(
        source,
        "    ]);\n    for (const card of cards) {\n      card.attrs = contractAttributes.get(String(card.card_id));",
        "    ]);\n    for (let cardIndex = 0; cardIndex < cards.length; cardIndex += 1) {\n      if ((cardIndex & 127) === 0) await cooperativeYield();\n      const card = cards[cardIndex];\n      card.attrs = contractAttributes.get(String(card.card_id));",
        "composição final das cartas em lotes",
    )
    source = _replace_literal_once(
        source,
        "    for (let offset = 0, recordIndex = 0; offset < rawPlayers.length; offset += K.RECORD_SIZE, recordIndex += 1) {",
        "    for (let offset = 0, recordIndex = 0; offset < rawPlayers.length; offset += K.RECORD_SIZE, recordIndex += 1) {\n      if ((recordIndex & 127) === 0) await cooperativeYield();",
        "dimensões por carta em lotes",
    )
    source = _replace_literal_once(
        source,
        "    const cards = physicalCards.map((physical) => {",
        "    const cards = await cooperativeMap(physicalCards, (physical) => {",
        "resolução das dimensões em lotes",
    )

    source = _replace_literal_once(
        source,
        "  function bytesToHex(bytes) { return [...bytes].map((value) => value.toString(16).padStart(2, '0')).join(''); }",
        _responsive_card_functions()
        + "  function bytesToHex(bytes) { return [...bytes].map((value) => value.toString(16).padStart(2, '0')).join(''); }",
        "funções responsivas de cartas",
    )

    export_marker = """    validateCardDimensionsSnapshot,
    rowsToCsv,
    cardsToCsv,
    duplicateIds,
    missingCounts,
    validateCards,
    compareCardRows,"""
    export_replacement = """    validateCardDimensionsSnapshot,
    validateCardDimensionsSnapshotResponsive,
    rowsToCsv,
    rowsToCsvResponsive,
    cardsToCsv,
    cardsToCsvResponsive,
    duplicateIds,
    missingCounts,
    validateCards,
    prepareCardRowsResponsive,
    compareCardRows,
    compareCardRowsResponsive,"""
    source = _replace_literal_once(
        source,
        export_marker,
        export_replacement,
        "exports responsivos do núcleo",
    )
    return source + "\n//# sourceURL=/app/extrator-core-v4612.js\n"


def patched_review_source() -> str:
    path = Path(previous.legacy.base.ROOT) / "app" / "revisao-intermediaria.js"
    source = path.read_text(encoding="utf-8-sig")

    source = _replace_literal_once(
        source,
        """  const originalCompareCardRows = originalCore.compareCardRows.bind(originalCore);
  const originalCompareTextCatalog = typeof originalCore.compareTextCatalog === 'function'""",
        """  const originalCompareCardRows = originalCore.compareCardRows.bind(originalCore);
  const originalCompareCardRowsResponsive = typeof originalCore.compareCardRowsResponsive === 'function'
    ? originalCore.compareCardRowsResponsive.bind(originalCore)
    : null;
  const originalCompareTextCatalog = typeof originalCore.compareTextCatalog === 'function'""",
        "captura do comparador responsivo",
    )

    async_wrapper = """
  async function compareCardRowsResponsiveWithReview(currentRows, baselineRows) {
    const diff = await originalCompareCardRowsResponsive(currentRows, baselineRows);
    review.generation += 1;
    review.generatedAt = new Date().toISOString();
    review.cardDiff = diff;
    review.currentById = new Map(currentRows.map((row) => [String(row.card_id), row]));
    review.baselineById = new Map(baselineRows.map((row) => [String(row.card_id), row]));
    global.CLUBEF_INTERMEDIATE_REVIEW = review;
    scheduleRender();
    return diff;
  }

"""
    source = _replace_literal_once(
        source,
        "  function compareTextCatalogWithReview(currentCatalog, baselineRows) {",
        async_wrapper + "  function compareTextCatalogWithReview(currentCatalog, baselineRows) {",
        "revisão do comparador responsivo",
    )
    source = _replace_literal_once(
        source,
        """    compareCardRows: compareCardRowsWithReview,
    ...(originalCompareTextCatalog ? { compareTextCatalog: compareTextCatalogWithReview } : {})""",
        """    compareCardRows: compareCardRowsWithReview,
    ...(originalCompareCardRowsResponsive ? { compareCardRowsResponsive: compareCardRowsResponsiveWithReview } : {}),
    ...(originalCompareTextCatalog ? { compareTextCatalog: compareTextCatalogWithReview } : {})""",
        "export do comparador responsivo revisável",
    )
    return source + "\n//# sourceURL=/app/revisao-intermediaria-v4612.js\n"


def patched_ui_source() -> str:
    source = previous.patched_ui_source()

    source = _replace_literal_count(
        source,
        "      const validation = core.validateCards(cards);",
        "      const cardPreparation = await core.prepareCardRowsResponsive(cards);\n      const validation = cardPreparation.validation;",
        2,
        "preparação responsiva das cartas",
    )
    source = _replace_literal_count(
        source,
        "      const currentRows = cards.map(core.cardToRow);",
        "      const currentRows = cardPreparation.rows;",
        2,
        "reutilização das linhas responsivas",
    )
    source = _replace_literal_count(
        source,
        "core.rowsToCsv(currentRows)",
        "await core.rowsToCsvResponsive(currentRows)",
        1,
        "CSV responsivo das relações",
    )
    source = _replace_literal_count(
        source,
        "      const diff = core.compareCardRows(currentRows, baseline.rows);",
        "      const diff = await core.compareCardRowsResponsive(currentRows, baseline.rows);",
        2,
        "comparação responsiva de cartas",
    )
    source = _replace_literal_once(
        source,
        "      const dimensionStructure = core.validateCardDimensionsSnapshot(dimensionSnapshot);",
        "      const dimensionStructure = await core.validateCardDimensionsSnapshotResponsive(dimensionSnapshot);",
        "validação responsiva de Dimensões",
    )
    source = _replace_literal_once(
        source,
        "      const fullCsv = core.cardsToCsv(cards);",
        "      const fullCsv = await core.rowsToCsvResponsive(cardPreparation.rows);",
        "CSV responsivo da recarga completa",
    )
    source = source.replace("extrator-ui-v4611.js", "extrator-ui-v4612.js")
    return source + "\n//# sourceURL=/app/extrator-ui-v4612.js\n"


def patched_metadata_runtime_source() -> str:
    source = previous.patched_metadata_runtime_source()
    return source.replace(
        "metadata-v46-runtime-v4611.js",
        "metadata-v46-runtime-v4612.js",
    )


def validate_runtime_patches() -> None:
    contract_source = patched_contract_reader_source()
    core_source = patched_core_source()
    review_source = patched_review_source()
    metadata_source = patched_metadata_runtime_source()
    ui_source = patched_ui_source()
    required = (
        (contract_source, "clubefResponsiveYield", "leitor contratual cooperativo"),
        (core_source, "compareCardRowsResponsive", "comparador responsivo"),
        (core_source, "prepareCardRowsResponsive", "preparação responsiva"),
        (review_source, "compareCardRowsResponsiveWithReview", "revisão responsiva"),
        (metadata_source, "family_errors", "runtime físico por família"),
        (ui_source, "await core.compareCardRowsResponsive", "UI responsiva"),
        (ui_source, "await core.rowsToCsvResponsive", "CSV responsivo"),
    )
    for source, marker, label in required:
        if marker not in source:
            raise RuntimeError(f"patch V4.6.12 incompleto: {label} sem {marker}")
    previous.legacy.runtime_log(
        "Patches V4.6.12 validados antes da abertura: "
        f"contrato_js={len(contract_source)} bytes; core_js={len(core_source)} bytes; "
        f"review_js={len(review_source)} bytes; metadata_js={len(metadata_source)} bytes; "
        f"ui_js={len(ui_source)} bytes"
    )


class Handler(previous.Handler):
    server_version = f"ClubEfootballLocal/{RUNTIME_VERSION}"

    def _serve_javascript(self, source: str) -> None:
        data = source.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_injected_ui(self) -> None:
        html_path = Path(previous.legacy.base.ROOT) / "Extrator-ClubEfootball.html"
        html = html_path.read_text(encoding="utf-8-sig")

        html = html.replace(
            '<script src="app/leitura-contrato.js"></script>',
            '<script src="/app/leitura-contrato-v4612.js?v=4.6.12"></script>',
        )
        html = html.replace(
            '<script src="app/extrator-core.js"></script>',
            '<script src="/app/extrator-core-v4612.js?v=4.6.12"></script>',
        )
        html = html.replace(
            '<script src="app/metadata-v46-runtime.js"></script>',
            '<script src="/app/metadata-v46-runtime-v4612.js?v=4.6.12"></script>',
        )
        html = html.replace(
            '<script src="app/revisao-intermediaria.js"></script>',
            '<script src="/app/revisao-intermediaria-v4612.js?v=4.6.12"></script>',
        )
        html = html.replace(
            '<script src="app/extrator-ui.js"></script>',
            '<script src="/app/extrator-ui-v4612.js?v=4.6.12"></script>',
        )

        patched_ui = '<script src="/app/extrator-ui-v4612.js?v=4.6.12"></script>'
        bridge = '<script src="/app/source-local-bridge.js"></script>'
        if bridge not in html:
            html = html.replace(patched_ui, f"{bridge}\n  {patched_ui}")
        diagnostic = '<script src="/app/diagnostico-v467.js?v=4.6.12"></script>'
        if diagnostic not in html:
            html = html.replace(patched_ui, f"{diagnostic}\n  {patched_ui}")

        metadata = '<script src="/app/metadados-v46.js?v=4.6.12" defer></script>'
        if "app/metadados-v46.js" not in html:
            html = html.replace("</body>", f"  {metadata}\n</body>")
        else:
            html = re.sub(
                r'<script src="/app/metadados-v46\.js[^\"]*" defer></script>',
                metadata,
                html,
                count=1,
            )

        data = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/app/leitura-contrato-v4612.js":
            self._serve_javascript(patched_contract_reader_source())
            return
        if path == "/app/extrator-core-v4612.js":
            self._serve_javascript(patched_core_source())
            return
        if path == "/app/revisao-intermediaria-v4612.js":
            self._serve_javascript(patched_review_source())
            return
        if path == "/app/metadata-v46-runtime-v4612.js":
            self._serve_javascript(patched_metadata_runtime_source())
            return
        if path == "/app/extrator-ui-v4612.js":
            self._serve_javascript(patched_ui_source())
            return
        super()._do_GET()


def main() -> None:
    host = "127.0.0.1"
    port = int(
        previous.legacy.base.os.environ.get(
            "CLUBEF_EXTRACTOR_PORT",
            str(DEFAULT_PORT),
        )
    )
    validate_runtime_patches()
    server = previous.legacy.LoggedThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}/Extrator-ClubEfootball.html"

    try:
        config_source = previous.legacy.base.load_config().get("_source")
    except Exception as error:
        config_source = f"erro: {type(error).__name__}: {error}"

    previous.legacy.runtime_log(
        f"Servidor iniciado em {url}; pid={previous.legacy.os.getpid()}; "
        f"raiz={previous.legacy.base.ROOT}; config={config_source}; "
        f"log={previous.legacy.diagnostic_log_path()}"
    )
    if previous.legacy.base.sys.stdout is not None:
        print(f"Extrator eFootball V{RUNTIME_VERSION} disponível em {url}")
        print(
            "Leitura física executada em lotes cooperativos; a interface permanece "
            "responsiva durante a varredura."
        )

    if "--no-browser" not in previous.legacy.base.sys.argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        previous.legacy.runtime_log("Servidor encerrado por KeyboardInterrupt.")
    except Exception as error:
        previous.legacy.runtime_log(
            "FALHA-SERVIDOR | "
            + "".join(
                previous.legacy.traceback.format_exception(
                    type(error),
                    error,
                    error.__traceback__,
                )
            ).strip()
        )
        raise
    finally:
        server.server_close()
        previous.legacy.runtime_log("Servidor local encerrado.")


if __name__ == "__main__":
    main()
