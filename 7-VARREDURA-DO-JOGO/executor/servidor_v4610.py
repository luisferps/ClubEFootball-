"""Runtime V4.6.11: varredura por família e conferência antes da escrita."""
from __future__ import annotations

import re
import threading
import time
import uuid
import webbrowser
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlparse

import servidor_v46 as legacy
from impetos_v4610 import validate_impetos_v4610
from tecnicos_v4610 import validate_tecnicos_v4610


RUNTIME_VERSION = "4.6.11"
DEFAULT_PORT = 8775
PATCH_DIR = Path(legacy.base.ROOT) / "app" / "patches-v4610"
LAST_DIMENSIONS_REPORT: dict | None = None
LAST_DIMENSIONS_REVIEW: dict | None = None
DIMENSIONS_REVIEW_LOCK = threading.Lock()
REVIEW_TTL_SECONDS = 30 * 60

legacy.RUNTIME_VERSION = RUNTIME_VERSION
legacy.DEFAULT_PORT = DEFAULT_PORT
legacy.base.validate_impetos = validate_impetos_v4610
legacy.base.validate_tecnicos = validate_tecnicos_v4610


def _fragment(name: str) -> str:
    path = PATCH_DIR / name
    if not path.is_file():
        raise RuntimeError(f"fragmento obrigatório ausente: {path}")
    return path.read_text(encoding="utf-8-sig")


def _replace_once(source: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, source, count=1)
    if count != 1:
        raise RuntimeError(
            f"patch V4.6.11 não encontrou trecho único: {label} "
            f"(encontrados={count})"
        )
    return updated


def patched_metadata_runtime_source() -> str:
    source_path = Path(legacy.base.ROOT) / "app" / "metadata-v46-runtime.js"
    source = source_path.read_text(encoding="utf-8-sig")
    source = _replace_once(
        source,
        r"  async function extractMetadataByFamilyV46\(sourceBytes,sourceDescriptors,log=\(\)=>\{\}\)\{"
        r"[\s\S]*?\n\n  async function captureValidate",
        _fragment("metadata-family-safe.jsfrag").rstrip()
        + "\n\n  async function captureValidate",
        "extração física isolada por família",
    )
    return source + "\n//# sourceURL=/app/metadata-v46-runtime-v4611.js\n"


def patched_ui_source() -> str:
    source_path = Path(legacy.base.ROOT) / "app" / "extrator-ui.js"
    source = source_path.read_text(encoding="utf-8-sig")

    source = _replace_once(
        source,
        r"  async function postJson\(url, body, timeoutMs = 0\) \{",
        _fragment("post-json-report.jsfrag")
        + "  async function postJson(url, body, timeoutMs = 0) {",
        "helper postJsonReport",
    )
    source = _replace_once(
        source,
        r"      log\('log-incremental', 'Conferindo atributos,[\s\S]*?"
        r"      const diff = core\.compareCardRows\(currentRows, baseline\.rows\);",
        _fragment("card-relations-block.jsfrag").rstrip(),
        "relações de cartas como relatório revisável",
    )
    source = _replace_once(
        source,
        r"      state\.incremental = \{ baseline, cards, currentRows, relationsReadback,[\s\S]*?"
        r"      log\('log-incremental', 'Concluído: somente o diff foi preparado; nenhum dado foi aplicado\.'\);",
        _fragment("card-result-block.jsfrag").rstrip(),
        "resultado de cartas com conferência intermediária",
    )
    source = _replace_once(
        source,
        r"      const textSource = state\.sources\.dt261_bra;"
        r"[\s\S]*?      const selectionContract = \{",
        _fragment("family-block.jsfrag")
        + "\n      const selectionContract = {",
        "isolamento das famílias de metadados",
    )
    source = source.replace(
        "        technicians_validation: technicianReadback, "
        "impetus_validation: impetusReadback,\n"
        "        card_dimensions_validation: dimensionReadback, summary",
        "        technicians_validation: technicianReadback, "
        "impetus_validation: impetusReadback,\n"
        "        card_dimensions_validation: dimensionReadback, "
        "family_warnings: familyWarnings,\n"
        "        scan_completed: true, summary",
        1,
    )
    if "family_warnings: familyWarnings" not in source:
        raise RuntimeError("patch V4.6.11 não inseriu avisos no manifesto")

    source = source.replace(
        ": item.status === 'bloqueado_fonte_alterada'",
        ": ['bloqueado_fonte_alterada', 'divergente', "
        "'erro_leitura'].includes(item.status)",
        1,
    )
    source = source.replace("— Verificação bloqueada.", "— Atenção.", 1)
    source = _replace_once(
        source,
        r"      const blockedRoles = \[\.\.\.changedRoles\]"
        r"\.filter\(\(role\) => role !== 'dt261_bra'\);"
        r"[\s\S]*?      log\('log-metadata', `Concluído:[^\n]*\);",
        _fragment("status-block.jsfrag").rstrip(),
        "resumo final não bloqueante",
    )
    return source + "\n//# sourceURL=/app/extrator-ui-v4611.js\n"


def _comparison_review(report: dict) -> dict:
    families: dict[str, dict] = {}
    for name, item in (report.get("comparisons") or {}).items():
        if not isinstance(item, dict):
            continue
        families[name] = {
            "source": int(item.get("source") or 0),
            "database": int(item.get("database") or 0),
            "missing_in_database": int(item.get("missing_in_database") or 0),
            "missing_in_source": int(item.get("missing_in_source") or 0),
            "changed": int(item.get("changed") or 0),
            "passed": bool(item.get("passed")),
            "difference_samples": item.get("difference_samples") or {},
        }
    return families


def _build_dimensions_review(snapshot: dict, report: dict, apply_available: bool) -> dict:
    return {
        "scope": "dimensoes_e_vinculos",
        "title": "Nacionalidades, clubes, ligas, tipos e vínculos das cartas",
        "source_counts": snapshot.get("counts") or {},
        "families": _comparison_review(report),
        "database_integrity": report.get("database_integrity") or {},
        "validation_passed": bool(report.get("passed")),
        "application_allowed": bool(report.get("passed")) and apply_available,
        "included_tables": [
            "clube_novo.nacionalidade_jogo",
            "clube_novo.clube_jogo",
            "clube_novo.liga_jogo",
            "clube_novo.tipo_carta_jogo",
            "vínculos físicos em clube_novo.carta_jogo",
        ],
        "excluded_families": [
            "ímpetos",
            "técnicos",
            "textos",
            "habilidades",
            "relações normalizadas de cartas",
        ],
        "delete_rows": False,
        "database_write": False,
    }


def _review_is_current(review: dict | None) -> bool:
    if not review or review.get("used"):
        return False
    if time.monotonic() - float(review.get("created_monotonic") or 0) > REVIEW_TTL_SECONDS:
        return False
    if review.get("snapshot_marker") != id(legacy.LAST_DIMENSIONS):
        return False
    if review.get("report_marker") != id(LAST_DIMENSIONS_REPORT):
        return False
    return True


def validate_runtime_patches() -> None:
    metadata_source = patched_metadata_runtime_source()
    ui_source = patched_ui_source()
    required = (
        (metadata_source, "family_errors", "runtime físico por família"),
        (ui_source, "familyWarnings", "UI por família"),
        (ui_source, "continue_pipeline", "continuidade do relatório"),
        (ui_source, "relationDivergences", "conferência das relações de cartas"),
        (ui_source, "clubef:metadata-scan-ready", "evento de metadados para a conferência"),
        (ui_source, "clubef:card-scan-ready", "evento de cartas para a conferência"),
    )
    for source, marker, label in required:
        if marker not in source:
            raise RuntimeError(f"patch V4.6.11 incompleto: {label} sem {marker}")
    legacy.runtime_log(
        "Patches V4.6.11 validados antes da abertura: "
        f"metadata_js={len(metadata_source)} bytes; ui_js={len(ui_source)} bytes"
    )


class Handler(legacy.Handler):
    server_version = f"ClubEfootballLocal/{RUNTIME_VERSION}"

    def _serve_injected_ui(self) -> None:
        html_path = Path(legacy.base.ROOT) / "Extrator-ClubEfootball.html"
        html = html_path.read_text(encoding="utf-8-sig")

        core_marker = '<script src="app/extrator-core.js"></script>'
        runtime_marker = '<script src="app/contrato-v46-runtime.js"></script>'
        if runtime_marker not in html:
            html = html.replace(core_marker, f"{core_marker}\n  {runtime_marker}")

        original_metadata_runtime = '<script src="app/metadata-v46-runtime.js"></script>'
        patched_metadata_runtime = (
            '<script src="/app/metadata-v46-runtime-v4611.js?v=4.6.11"></script>'
        )
        html = html.replace(original_metadata_runtime, patched_metadata_runtime)

        original_ui = '<script src="app/extrator-ui.js"></script>'
        patched_ui = '<script src="/app/extrator-ui-v4611.js?v=4.6.11"></script>'
        html = html.replace(original_ui, patched_ui)

        bridge = '<script src="/app/source-local-bridge.js"></script>'
        if bridge not in html:
            html = html.replace(patched_ui, f"{bridge}\n  {patched_ui}")

        diagnostic = '<script src="/app/diagnostico-v467.js?v=4.6.11"></script>'
        if diagnostic not in html:
            html = html.replace(patched_ui, f"{diagnostic}\n  {patched_ui}")

        metadata = '<script src="/app/metadados-v46.js?v=4.6.11" defer></script>'
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
        if path == "/app/metadata-v46-runtime-v4611.js":
            data = patched_metadata_runtime_source().encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path == "/app/extrator-ui-v4611.js":
            data = patched_ui_source().encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path == "/api/card-dimensions/cached-status":
            config = legacy.base.load_config()
            snapshot = legacy.LAST_DIMENSIONS
            report = LAST_DIMENSIONS_REPORT
            approved = bool(report and report.get("passed"))
            with DIMENSIONS_REVIEW_LOCK:
                review_prepared = _review_is_current(LAST_DIMENSIONS_REVIEW)
                review_id = (
                    LAST_DIMENSIONS_REVIEW.get("review_id")
                    if review_prepared and LAST_DIMENSIONS_REVIEW
                    else None
                )
            self.send_json(
                HTTPStatus.OK,
                {
                    "ready": snapshot is not None,
                    "approved": approved,
                    "review_required": True,
                    "review_prepared": review_prepared,
                    "review_id": review_id,
                    "apply_available": (
                        approved and legacy.dimensions_apply_allowed(config)
                    ),
                    "source_counts": snapshot.get("counts") if snapshot else None,
                    "validation": report,
                    "required_confirmation": legacy.REQUIRED_CONFIRMATION,
                    "database_write": False,
                },
            )
            return
        super()._do_GET()

    def _do_POST(self) -> None:
        global LAST_DIMENSIONS_REPORT, LAST_DIMENSIONS_REVIEW
        path = urlparse(self.path).path

        if path == "/api/card-dimensions/validate":
            snapshot = None
            try:
                config = legacy.base.load_config()
                self._reading_contract = legacy.base.current_reading_contract(config)
                payload = self.read_json()
                snapshot = payload.get("snapshot")
                if not isinstance(snapshot, dict):
                    raise ValueError("a fotografia física de Dimensões não foi recebida")
                result = legacy.base.current_card_dimensions_validation(snapshot, config)
                if result.get("source_contract") != snapshot.get("contract"):
                    raise ValueError("o readback não corresponde à fotografia física recebida")

                legacy.LAST_DIMENSIONS = snapshot
                LAST_DIMENSIONS_REPORT = result
                with DIMENSIONS_REVIEW_LOCK:
                    LAST_DIMENSIONS_REVIEW = None
                response = {
                    **result,
                    "continue_pipeline": True,
                    "application_blocked": not bool(result.get("passed")),
                    "snapshot_cached_for_manual_apply": True,
                    "review_required_before_apply": True,
                }
                status = HTTPStatus.OK if result.get("passed") else HTTPStatus.CONFLICT
                self.send_json(status, response)
            except Exception as error:
                if isinstance(snapshot, dict):
                    legacy.LAST_DIMENSIONS = snapshot
                LAST_DIMENSIONS_REPORT = {
                    "passed": False,
                    "continue_pipeline": True,
                    "application_blocked": True,
                    "error": str(error),
                    "database_write": False,
                }
                with DIMENSIONS_REVIEW_LOCK:
                    LAST_DIMENSIONS_REVIEW = None
                self.send_json(
                    HTTPStatus.BAD_REQUEST,
                    LAST_DIMENSIONS_REPORT,
                )
            return

        if path == "/api/card-dimensions/prepare-cached":
            try:
                config = legacy.base.load_config()
                self._reading_contract = legacy.base.current_reading_contract(config)
                self.read_json()
                snapshot = legacy.LAST_DIMENSIONS
                report = LAST_DIMENSIONS_REPORT
                if snapshot is None or not isinstance(report, dict):
                    raise ValueError(
                        "execute primeiro a comparação de Metadados para gerar a conferência"
                    )
                apply_available = legacy.dimensions_apply_allowed(config)
                review_payload = _build_dimensions_review(snapshot, report, apply_available)
                with DIMENSIONS_REVIEW_LOCK:
                    review_id = uuid.uuid4().hex
                    LAST_DIMENSIONS_REVIEW = {
                        "review_id": review_id,
                        "created_monotonic": time.monotonic(),
                        "snapshot_marker": id(snapshot),
                        "report_marker": id(report),
                        "used": False,
                        "review": review_payload,
                    }
                self.send_json(
                    HTTPStatus.OK,
                    {
                        "prepared": True,
                        "review_id": review_id,
                        "expires_in_seconds": REVIEW_TTL_SECONDS,
                        "required_confirmation": legacy.REQUIRED_CONFIRMATION,
                        "application_allowed": review_payload["application_allowed"],
                        "review": review_payload,
                        "database_write": False,
                    },
                )
            except (RuntimeError, ValueError, OSError) as error:
                self.send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": str(error), "database_write": False},
                )
            return

        if path == "/api/card-dimensions/apply-cached":
            if not legacy.DIMENSIONS_LOCK.acquire(blocking=False):
                self.send_json(
                    HTTPStatus.CONFLICT,
                    {"error": "uma aplicação de metadados já está em andamento"},
                )
                return
            try:
                config = legacy.base.load_config()
                self._reading_contract = legacy.base.current_reading_contract(config)
                payload = self.read_json()
                review_id = str(payload.get("review_id") or "").strip()
                acknowledged = payload.get("acknowledged") is True
                confirmation = str(payload.get("confirmation") or "").strip()

                with DIMENSIONS_REVIEW_LOCK:
                    review = LAST_DIMENSIONS_REVIEW
                    if not _review_is_current(review):
                        raise PermissionError(
                            "a conferência expirou ou não corresponde à fotografia atual; abra a conferência novamente"
                        )
                    if review_id != str(review.get("review_id")):
                        raise PermissionError("identificador da conferência incorreto")
                    if not acknowledged:
                        raise PermissionError("confirme que revisou as divergências antes da aplicação")
                    if confirmation != legacy.REQUIRED_CONFIRMATION:
                        raise PermissionError("confirmação de metadados incorreta")
                    if not LAST_DIMENSIONS_REPORT or not LAST_DIMENSIONS_REPORT.get("passed"):
                        raise PermissionError(
                            "aplicação de Dimensões bloqueada: esta família possui divergências"
                        )

                if not legacy.dimensions_apply_allowed(config):
                    raise PermissionError("aplicação manual de Dimensões não está habilitada")
                snapshot = legacy.LAST_DIMENSIONS
                if snapshot is None:
                    raise ValueError(
                        "execute primeiro a comparação de Metadados para gerar a fotografia física"
                    )

                psycopg, sql, _ = legacy.base.import_psycopg()
                dsn = legacy.base.connection_string()
                if not dsn:
                    raise RuntimeError("conexão segura com clube_novo indisponível")

                with psycopg.connect(dsn, connect_timeout=20) as connection:
                    with connection.transaction():
                        with connection.cursor() as cursor:
                            cursor.execute("set transaction isolation level serializable")
                        result = legacy.apply_card_dimensions(
                            snapshot,
                            connection,
                            "clube_novo",
                            sql,
                        )

                with psycopg.connect(dsn, connect_timeout=20) as verification:
                    verification.read_only = True
                    readback = legacy.readback_card_dimensions(
                        snapshot,
                        verification,
                        "clube_novo",
                        sql,
                    )

                with DIMENSIONS_REVIEW_LOCK:
                    if LAST_DIMENSIONS_REVIEW:
                        LAST_DIMENSIONS_REVIEW["used"] = True

                self.send_json(
                    HTTPStatus.OK,
                    {
                        "applied": True,
                        "review_id": review_id,
                        "result": result,
                        "readback": readback,
                        "database_write": True,
                        "next": "aplicar_cards_depois_dos_metadados",
                    },
                )
            except PermissionError as error:
                self.send_json(
                    HTTPStatus.FORBIDDEN,
                    {"error": str(error), "database_write": False},
                )
            except (RuntimeError, ValueError, OSError) as error:
                self.send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": str(error), "database_write": False},
                )
            except Exception as error:
                legacy.runtime_log(
                    "FALHA-FECHADA-CONFERENCIA | "
                    + "".join(
                        legacy.traceback.format_exception(
                            type(error),
                            error,
                            error.__traceback__,
                        )
                    ).strip()
                )
                self.send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": f"falha fechada: {error}", "database_write": False},
                )
            finally:
                legacy.DIMENSIONS_LOCK.release()
            return

        super()._do_POST()


def main() -> None:
    host = "127.0.0.1"
    port = int(
        legacy.base.os.environ.get(
            "CLUBEF_EXTRACTOR_PORT",
            str(DEFAULT_PORT),
        )
    )
    validate_runtime_patches()
    server = legacy.LoggedThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}/Extrator-ClubEfootball.html"

    try:
        config_source = legacy.base.load_config().get("_source")
    except Exception as error:
        config_source = f"erro: {type(error).__name__}: {error}"

    legacy.runtime_log(
        f"Servidor iniciado em {url}; pid={legacy.os.getpid()}; "
        f"raiz={legacy.base.ROOT}; config={config_source}; "
        f"log={legacy.diagnostic_log_path()}"
    )
    if legacy.base.sys.stdout is not None:
        print(f"Extrator eFootball V{RUNTIME_VERSION} disponível em {url}")
        print(
            "Toda leitura termina em uma conferência; nenhuma escrita é liberada "
            "sem revisão explícita."
        )

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
