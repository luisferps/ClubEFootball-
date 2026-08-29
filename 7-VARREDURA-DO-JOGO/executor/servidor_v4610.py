"""Runtime V4.6.10 do Extrator: varredura orientada pelo banco e não bloqueante.

Mantém o servidor V4.6.9 como base, mas:
- usa porta própria para impedir reaproveitamento de processo antigo;
- serve uma UI corrigida que isola divergências por família;
- deixa o relatório de cada família disponível e continua a varredura.
"""
from __future__ import annotations

import re
import threading
import webbrowser
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlparse

import servidor_v46 as legacy
from impetos_v4610 import validate_impetos_v4610


RUNTIME_VERSION = "4.6.10"
DEFAULT_PORT = 8774

legacy.RUNTIME_VERSION = RUNTIME_VERSION
legacy.DEFAULT_PORT = DEFAULT_PORT
legacy.base.validate_impetos = validate_impetos_v4610

POST_JSON_REPORT = '\nasync function postJsonReport(url, body, timeoutMs = 0) {\n  const controller = timeoutMs ? new AbortController() : null;\n  const timeout = controller ? setTimeout(() => controller.abort(), timeoutMs) : null;\n  let response;\n  try {\n    response = await fetchWithContract(url, {\n      method: \'POST\',\n      headers: { \'content-type\': \'application/json\' },\n      body: JSON.stringify({ ...body, leitura_contrato: contractSeal() }),\n      signal: controller ? controller.signal : undefined\n    });\n  } catch (error) {\n    if (error && error.name === \'AbortError\') {\n      throw new Error(\'A família demorou além do limite seguro; o restante da varredura continuará.\');\n    }\n    throw error;\n  } finally {\n    if (timeout) clearTimeout(timeout);\n  }\n  const payload = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));\n  assertContractResponse(response, payload);\n  if (!response.ok && typeof payload.passed !== \'boolean\' && payload.continue_pipeline !== true) {\n    throw new Error(payload.error || `HTTP ${response.status}`);\n  }\n  return payload;\n}\n\n'
FAMILY_BLOCK = '\nconst familyWarnings = [];\nconst textCatalog = physical.catalogs.textos;\nlet textStructure = { official_keys: 0, sections: 0 };\nlet baseline = {\n  rows: [], records: 0, sha256: null,\n  transaction_read_only: true, database_write: false,\n  schema_ready: false, catalog_references_checked: 0,\n  unresolved_catalog_references: 0, validated_foreign_keys: 0,\n  unvalidated_foreign_keys: 0\n};\nlet textDiff = {\n  current: Number((textCatalog.records || []).length),\n  baseline_active: 0,\n  new_entries: [], changed_entries: [], absent_entries: [],\n  validation: {}, status: \'erro_leitura\'\n};\n\ntry {\n  const textSource = state.sources.dt261_bra;\n  if (!textSource || !textSource.bytes) {\n    throw new Error(\'O CPK de textos foi localizado, mas seus bytes não ficaram disponíveis para a comparação.\');\n  }\n  log(\'log-metadata\', \'Extraindo all.str e validando chaves oficiais…\');\n  textStructure = core.validateTextCatalogStructure(textCatalog);\n  log(\'log-metadata\', `Estrutura válida: ${textStructure.official_keys.toLocaleString(\'pt-BR\')} chaves oficiais em ${textStructure.sections.toLocaleString(\'pt-BR\')} seções.`);\n  const baselineResponse = await fetchWithContract(\'/api/text-baseline/current.json\', { cache: \'no-store\' });\n  baseline = await baselineResponse.json().catch(() => ({ error: `HTTP ${baselineResponse.status}` }));\n  if (!baselineResponse.ok || !baseline.transaction_read_only || baseline.database_write !== false) {\n    throw new Error(baseline.error || \'A fotografia atual de clube_novo.texto_do_jogo não pôde ser lida de modo protegido.\');\n  }\n  if (baseline.duplicate_official_keys) {\n    throw new Error(\'clube_novo.texto_do_jogo contém chave oficial duplicada.\');\n  }\n  if (Number(baseline.unresolved_catalog_references || 0) > 0) {\n    throw new Error(`${baseline.unresolved_catalog_references} referência(s) textual(is) do banco não foi(ram) resolvida(s).`);\n  }\n  if (Number(baseline.unvalidated_foreign_keys || 0) > 0) {\n    throw new Error(`${baseline.unvalidated_foreign_keys} FK(s) canônica(s) de Texto ainda não foi(ram) validada(s).`);\n  }\n  textDiff = core.compareTextCatalog(textCatalog, baseline.rows || []);\n  diff.textos = textDiff;\n  summary.textos = {\n    ...summary.textos,\n    status: \'validado_banco\',\n    reason: baseline.schema_ready ? null : \'contrato estrutural ainda não instalado; comparação disponível e aplicação bloqueada\',\n    current: textDiff.current,\n    baseline_active: textDiff.baseline_active,\n    new: textDiff.new_entries.length,\n    changed: textDiff.changed_entries.length,\n    absent: 0,\n    without_previous_fingerprint: 0,\n    duplicate_ids: 0,\n    source_roles: [\'dt261_bra\']\n  };\n} catch (error) {\n  const reason = `Textos: ${error.message}`;\n  familyWarnings.push({ family: \'textos\', reason });\n  summary.textos = {\n    ...(summary.textos || {}),\n    status: \'erro_leitura\',\n    reason,\n    current: Number((textCatalog.records || []).length),\n    baseline_active: Number(baseline.records || 0),\n    new: 0, changed: 0, absent: 0,\n    without_previous_fingerprint: 0,\n    duplicate_ids: 0,\n    source_roles: [\'dt261_bra\']\n  };\n  diff.textos = {\n    status: \'erro_leitura\', reason,\n    current: Number((textCatalog.records || []).length),\n    baseline_active: Number(baseline.records || 0),\n    new_entries: [], changed_entries: [], absent_entries: [],\n    without_previous_fingerprint: 0, duplicate_ids: []\n  };\n  log(\'log-metadata\', `AVISO — ${reason}. A varredura continuará nas outras famílias.`);\n}\n\nconst technicianSnapshot = {\n  ...physical.catalogs.tecnicos,\n  nationalities: physical.catalogs.nacionalidades.records,\n  affinities: physical.catalogs.afinidades_tecnico.records\n};\nlet technicianReadback = {\n  passed: false, continue_pipeline: true, application_blocked: true,\n  error: \'validação de Técnicos não executada\'\n};\ntry {\n  technicianReadback = await postJsonReport(\'/api/tecnicos/validate\', { snapshot: technicianSnapshot }, 600000);\n  const techFound = Number((physical.catalogs.tecnicos.records || []).length);\n  const techExpected = Number(technicianReadback.checks?.technicians?.database ?? summary.tecnicos?.baseline_active ?? techFound);\n  const natFound = Number((physical.catalogs.nacionalidades.records || []).length);\n  const natExpected = Number(technicianReadback.checks?.nationalities?.database ?? summary.nacionalidades?.baseline_active ?? natFound);\n  const affinityFound = Number((physical.catalogs.afinidades_tecnico.records || []).length);\n  const affinityExpected = Number(technicianReadback.checks?.affinities?.database ?? summary.afinidades_tecnico?.baseline_active ?? affinityFound);\n  const exact = Boolean(technicianReadback.passed && technicianReadback.transaction_read_only && technicianReadback.database_write === false);\n  const reason = exact ? null : \'A releitura de Técnicos terminou com divergências; consulte o relatório desta família.\';\n  summary.tecnicos = { ...(summary.tecnicos || {}), status: exact ? \'validado_banco\' : \'divergente\', reason, current: techFound, baseline_active: techExpected, new: 0, changed: 0, absent: Math.max(0, techExpected - techFound) };\n  summary.nacionalidades = { ...(summary.nacionalidades || {}), status: exact ? \'validado_banco\' : \'divergente\', reason, current: natFound, baseline_active: natExpected, new: 0, changed: 0, absent: Math.max(0, natExpected - natFound) };\n  summary.afinidades_tecnico = { ...(summary.afinidades_tecnico || {}), status: exact ? \'validado_banco\' : \'divergente\', reason, current: affinityFound, baseline_active: affinityExpected, new: 0, changed: 0, absent: Math.max(0, affinityExpected - affinityFound) };\n  for (const name of [\'tecnicos\', \'nacionalidades\', \'afinidades_tecnico\']) {\n    diff[name] = { ...(diff[name] || {}), status: exact ? \'validado_banco\' : \'divergente\', reason };\n  }\n  if (exact) {\n    log(\'log-metadata\', `Técnicos conferidos: ${techFound.toLocaleString(\'pt-BR\')} técnicos · ${natFound.toLocaleString(\'pt-BR\')} nacionalidades · ${affinityFound.toLocaleString(\'pt-BR\')} afinidades.`);\n  } else {\n    familyWarnings.push({ family: \'tecnicos\', reason, report: technicianReadback });\n    log(\'log-metadata\', `AVISO — ${reason} A varredura continuará.`);\n  }\n} catch (error) {\n  const reason = `Técnicos: ${error.message}`;\n  technicianReadback = { passed: false, continue_pipeline: true, application_blocked: true, error: error.message };\n  familyWarnings.push({ family: \'tecnicos\', reason });\n  for (const name of [\'tecnicos\', \'nacionalidades\', \'afinidades_tecnico\']) {\n    summary[name] = { ...(summary[name] || {}), status: \'erro_leitura\', reason, new: 0, changed: 0, absent: 0 };\n    diff[name] = { ...(diff[name] || {}), status: \'erro_leitura\', reason };\n  }\n  log(\'log-metadata\', `AVISO — ${reason}. A varredura continuará.`);\n}\n\nlet impetusReadback = {\n  passed: false, continue_pipeline: true, application_blocked: true,\n  error: \'validação de Ímpetos não executada\'\n};\ntry {\n  impetusReadback = await postJsonReport(\'/api/impetos/validate\', { snapshot: physical.catalogs.impetos }, 600000);\n  const requested = Number(impetusReadback.code_report?.requested ?? impetusReadback.requested_by_database?.union_catalog ?? 0);\n  const found = Number(impetusReadback.code_report?.found_unique ?? impetusReadback.extracted?.unique_codes ?? (physical.catalogs.impetos.records || []).length);\n  const missing = impetusReadback.code_report?.missing || [];\n  const extra = impetusReadback.code_report?.extra || [];\n  const changed = impetusReadback.code_report?.changed || [];\n  const duplicates = impetusReadback.code_report?.duplicates || [];\n  const exact = Boolean(impetusReadback.passed && impetusReadback.transaction_read_only && impetusReadback.database_write === false);\n  const reason = exact\n    ? null\n    : `O banco pediu ${requested.toLocaleString(\'pt-BR\')} código(s); foram encontrados ${found.toLocaleString(\'pt-BR\')}. Ausentes: ${missing.length}; novos: ${extra.length}; alterados: ${changed.length}; duplicados: ${duplicates.length}.`;\n  summary.impetos = {\n    ...(summary.impetos || {}),\n    status: exact ? \'validado_banco\' : \'divergente\',\n    reason,\n    current: found,\n    baseline_active: requested,\n    new: extra.length,\n    changed: changed.length,\n    absent: missing.length\n  };\n  diff.impetos = {\n    ...(diff.impetos || {}),\n    status: exact ? \'validado_banco\' : \'divergente\',\n    reason,\n    current: found,\n    baseline_active: requested,\n    new_entries: extra.map((id) => ({ id: String(id), origins: [\'fonte_fisica\'] })),\n    changed_entries: changed.map((id) => ({ id: String(id), record: { id: String(id) } })),\n    absent_entries: missing.map((id) => ({ id: String(id), record: { id: String(id) } })),\n    duplicate_ids: duplicates\n  };\n  if (exact) {\n    const requestedRows = impetusReadback.requested_by_database || {};\n    log(\'log-metadata\', `Ímpetos conferidos pelo pedido do banco: ${found.toLocaleString(\'pt-BR\')} códigos · ${Number(requestedRows.effects || 0).toLocaleString(\'pt-BR\')} efeitos · ${Number(requestedRows.conditions || 0).toLocaleString(\'pt-BR\')} condições.`);\n  } else {\n    familyWarnings.push({ family: \'impetos\', reason, report: impetusReadback });\n    log(\'log-metadata\', `AVISO — Ímpetos: ${reason} A varredura continuará para Dimensões e cartas.`);\n  }\n} catch (error) {\n  const reason = `Ímpetos: ${error.message}`;\n  impetusReadback = { passed: false, continue_pipeline: true, application_blocked: true, error: error.message };\n  familyWarnings.push({ family: \'impetos\', reason });\n  summary.impetos = { ...(summary.impetos || {}), status: \'erro_leitura\', reason, current: Number((physical.catalogs.impetos.records || []).length), baseline_active: 0, new: 0, changed: 0, absent: 0 };\n  diff.impetos = { ...(diff.impetos || {}), status: \'erro_leitura\', reason, new_entries: [], changed_entries: [], absent_entries: [], duplicate_ids: [] };\n  log(\'log-metadata\', `AVISO — ${reason}. A varredura continuará para Dimensões e cartas.`);\n}\n\nlog(\'log-metadata\', \'Relendo país, clube, liga e tipo para todas as cartas…\');\nlet dimensionSnapshot = null;\nlet dimensionStructure = { cards: 0, clubs: 0, leagues: 0, nationalities: 0, types: 0 };\nlet dimensionReadback = {\n  passed: false, continue_pipeline: true, application_blocked: true,\n  error: \'validação de Dimensões não executada\'\n};\ntry {\n  dimensionSnapshot = await core.extractCardDimensionsByFamily(\n    familySourceBytes,\n    familySourceDescriptors,\n    (message) => log(\'log-metadata\', message)\n  );\n  dimensionStructure = core.validateCardDimensionsSnapshot(dimensionSnapshot);\n  dimensionReadback = await postJsonReport(\'/api/card-dimensions/validate\', { snapshot: dimensionSnapshot }, 600000);\n  const exact = Boolean(dimensionReadback.passed && dimensionReadback.transaction_read_only && dimensionReadback.database_write === false);\n  const expectedCards = Number(dimensionReadback.comparisons?.cards?.database ?? 0);\n  const foundCards = Number(dimensionStructure.cards || 0);\n  const reason = exact ? null : \'País, clube, liga, tipo ou vínculos apresentam diferenças; consulte o relatório de Dimensões.\';\n  diff.dimensoes_cartas = {\n    status: exact ? \'validado_banco\' : \'divergente\',\n    reason,\n    current: foundCards,\n    baseline_active: expectedCards,\n    new_entries: [], changed_entries: [], absent_entries: [],\n    without_previous_fingerprint: 0, duplicate_ids: []\n  };\n  summary.dimensoes_cartas = {\n    status: exact ? \'validado_banco\' : \'divergente\',\n    reason,\n    current: foundCards,\n    baseline_active: expectedCards,\n    new: 0,\n    changed: Number(dimensionReadback.comparisons?.cards?.changed || 0),\n    absent: Number(dimensionReadback.comparisons?.cards?.missing_in_source || 0),\n    without_previous_fingerprint: 0,\n    duplicate_ids: 0,\n    source_roles: [...METADATA_SOURCE_ROLES]\n  };\n  if (exact) {\n    log(\'log-metadata\', `Dimensões conferidas: ${foundCards.toLocaleString(\'pt-BR\')} cartas; país, clube, liga e tipo iguais ao pedido do banco.`);\n  } else {\n    familyWarnings.push({ family: \'dimensoes_cartas\', reason, report: dimensionReadback });\n    log(\'log-metadata\', `AVISO — ${reason} A varredura foi concluída e os demais resultados foram preservados.`);\n  }\n} catch (error) {\n  const reason = `Dimensões: ${error.message}`;\n  dimensionReadback = { passed: false, continue_pipeline: true, application_blocked: true, error: error.message };\n  familyWarnings.push({ family: \'dimensoes_cartas\', reason });\n  diff.dimensoes_cartas = { status: \'erro_leitura\', reason, current: Number(dimensionStructure.cards || 0), baseline_active: 0, new_entries: [], changed_entries: [], absent_entries: [], without_previous_fingerprint: 0, duplicate_ids: [] };\n  summary.dimensoes_cartas = { status: \'erro_leitura\', reason, current: Number(dimensionStructure.cards || 0), baseline_active: 0, new: 0, changed: 0, absent: 0, without_previous_fingerprint: 0, duplicate_ids: 0, source_roles: [...METADATA_SOURCE_ROLES] };\n  log(\'log-metadata\', `AVISO — ${reason}. Os resultados das outras famílias foram preservados.`);\n}\n\nconst textItems = [\n  ...textDiff.new_entries.map((record) => ({ key: `textos:new:${record.id}`, catalog: \'textos\', action: \'new\', id: record.id, record })),\n  ...textDiff.changed_entries.map((entry) => ({ key: `textos:change:${entry.id}`, catalog: \'textos\', action: \'change\', id: entry.id, record: entry.record, before: entry.before, after: entry.after }))\n];\n'
STATUS_BLOCK = '\nconst blockedRoles = [...changedRoles].filter((role) => role !== \'dt261_bra\');\nconst applicationBlocked = blockedRoles.length > 0 || !baseline.schema_ready || familyWarnings.length > 0;\nconst changes = totals.new + totals.changed + totals.absent;\nif (applicationBlocked) {\n  const details = [];\n  if (!baseline.schema_ready) details.push(\'Textos sem contrato estrutural pronto para aplicação\');\n  if (blockedRoles.length) details.push(`fontes alteradas: ${blockedRoles.join(\', \')}`);\n  if (familyWarnings.length) details.push(`${familyWarnings.length} família(s) com aviso`);\n  const reason = `${details.join(\' · \')}. A varredura terminou e somente as aplicações afetadas ficaram bloqueadas.`;\n  setOperationStatus(\'metadata-status\', \'error\', \'Varredura concluída com avisos\', reason);\n  state.automatic.metadata = { state: \'ready\', pending: true, message: reason };\n} else {\n  setOperationStatus(\'metadata-status\', \'success\', changes ? \'Atualização de metadados disponível\' : \'Metadados conferidos — nada para atualizar\', changes ? `${totals.new} novas · ${totals.changed} alteradas · ${totals.absent} ausentes.` : \'As fontes são as mesmas da referência interna vigente.\');\n  state.automatic.metadata = { state: \'ready\', pending: Boolean(changes), message: changes ? `${totals.new} novas · ${totals.changed} alteradas · ${totals.absent} ausentes.` : \'Nada para atualizar nas famílias suportadas; as demais continuam identificadas como não suportadas.\' };\n}\nrenderAutomaticSummary();\nlog(\'log-metadata\', `Concluído: ${Number(textDiff.current || 0).toLocaleString(\'pt-BR\')} chaves de texto · ${Number((physical.catalogs.tecnicos.records || []).length).toLocaleString(\'pt-BR\')} técnicos · ${Number(impetusReadback.extracted?.unique_codes ?? (physical.catalogs.impetos.records || []).length).toLocaleString(\'pt-BR\')} códigos de ímpeto · ${Number(dimensionStructure.cards || 0).toLocaleString(\'pt-BR\')} cartas em Dimensões. Avisos: ${familyWarnings.length}. Nenhuma escrita foi feita.`);\n'


def _replace_once(source: str, pattern: str, replacement: str, label: str, flags: int = 0) -> str:
    updated, count = re.subn(pattern, replacement, source, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f"patch V4.6.10 não encontrou trecho único: {label} (encontrados={count})")
    return updated


def patched_ui_source() -> str:
    path = Path(legacy.base.ROOT) / "app" / "extrator-ui.js"
    source = path.read_text(encoding="utf-8-sig")

    source = _replace_once(
        source,
        r"  async function postJson\(url, body, timeoutMs = 0\) \{",
        POST_JSON_REPORT + "  async function postJson(url, body, timeoutMs = 0) {",
        "helper postJsonReport",
    )
    source = _replace_once(
        source,
        r"      const textSource = state\.sources\.dt261_bra;[\s\S]*?      const selectionContract = \{",
        FAMILY_BLOCK + "\n      const selectionContract = {",
        "isolamento das famílias de metadados",
    )
    source = source.replace(
        "        technicians_validation: technicianReadback, impetus_validation: impetusReadback,\n"
        "        card_dimensions_validation: dimensionReadback, summary",
        "        technicians_validation: technicianReadback, impetus_validation: impetusReadback,\n"
        "        card_dimensions_validation: dimensionReadback, family_warnings: familyWarnings,\n"
        "        scan_completed: true, summary",
        1,
    )
    if "family_warnings: familyWarnings" not in source:
        raise RuntimeError("patch V4.6.10 não inseriu family_warnings no manifesto")

    source = source.replace(
        ": item.status === 'bloqueado_fonte_alterada'",
        ": ['bloqueado_fonte_alterada', 'divergente', 'erro_leitura'].includes(item.status)",
        1,
    )
    source = source.replace("— Verificação bloqueada.", "— Atenção.", 1)
    source = _replace_once(
        source,
        r"      const blockedRoles = \[\.\.\.changedRoles\]\.filter\(\(role\) => role !== 'dt261_bra'\);[\s\S]*?      log\('log-metadata', `Concluído:[^\n]*\);",
        STATUS_BLOCK.rstrip(),
        "resumo final não bloqueante",
    )
    return source + "\n//# sourceURL=/app/extrator-ui-v4610.js\n"


class Handler(legacy.Handler):
    server_version = f"ClubEfootballLocal/{RUNTIME_VERSION}"

    def _serve_injected_ui(self) -> None:
        html_path = Path(legacy.base.ROOT) / "Extrator-ClubEfootball.html"
        html = html_path.read_text(encoding="utf-8-sig")

        core_marker = '<script src="app/extrator-core.js"></script>'
        runtime_marker = '<script src="app/contrato-v46-runtime.js"></script>'
        if runtime_marker not in html:
            html = html.replace(core_marker, f"{core_marker}\n  {runtime_marker}")

        original_ui = '<script src="app/extrator-ui.js"></script>'
        patched_ui = '<script src="/app/extrator-ui-v4610.js?v=4.6.10"></script>'
        html = html.replace(original_ui, patched_ui)

        bridge_marker = '<script src="/app/source-local-bridge.js"></script>'
        if bridge_marker not in html:
            html = html.replace(patched_ui, f"{bridge_marker}\n  {patched_ui}")

        diagnostic_marker = '<script src="/app/diagnostico-v467.js?v=4.6.10"></script>'
        if diagnostic_marker not in html:
            html = html.replace(patched_ui, f"{diagnostic_marker}\n  {patched_ui}")

        metadata_marker = '<script src="/app/metadados-v46.js" defer></script>'
        if metadata_marker not in html:
            html = html.replace("</body>", f"  {metadata_marker}\n</body>")

        data = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/app/extrator-ui-v4610.js":
            data = patched_ui_source().encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        super()._do_GET()


def main() -> None:
    host = "127.0.0.1"
    port = int(legacy.base.os.environ.get("CLUBEF_EXTRACTOR_PORT", str(DEFAULT_PORT)))
    server = legacy.LoggedThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}/Extrator-ClubEfootball.html"

    try:
        config_source = legacy.base.load_config().get("_source")
    except Exception as error:
        config_source = f"erro: {type(error).__name__}: {error}"

    legacy.runtime_log(
        f"Servidor iniciado em {url}; pid={legacy.os.getpid()}; raiz={legacy.base.ROOT}; "
        f"config={config_source}; log={legacy.diagnostic_log_path()}"
    )
    if legacy.base.sys.stdout is not None:
        print(f"Extrator eFootball V{RUNTIME_VERSION} disponível em {url}")
        print("Varredura por família: divergência é registrada e não interrompe as demais leituras.")

    if "--no-browser" not in legacy.base.sys.argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        legacy.runtime_log("Servidor encerrado por KeyboardInterrupt.")
    except Exception as error:
        legacy.runtime_log(
            "FALHA-SERVIDOR | "
            + "".join(
                legacy.traceback.format_exception(
                    type(error),
                    error,
                    error.__traceback__,
                )
            ).strip()
        )
        raise
    finally:
        server.server_close()
        legacy.runtime_log("Servidor local encerrado.")


if __name__ == "__main__":
    main()
