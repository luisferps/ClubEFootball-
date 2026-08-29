"""Runtime V4.6.10: varredura por família sem bloqueio em cadeia."""
from __future__ import annotations

import re
import threading
import webbrowser
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlparse

import servidor_v46 as legacy
from impetos_v4610 import validate_impetos_v4610
from tecnicos_v4610 import validate_tecnicos_v4610


RUNTIME_VERSION = "4.6.10"
DEFAULT_PORT = 8774
PATCH_DIR = Path(legacy.base.ROOT) / "app" / "patches-v4610"
LAST_DIMENSIONS_REPORT: dict | None = None

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
            f"patch V4.6.10 não encontrou trecho único: {label} "
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
    return source + "\n//# sourceURL=/app/metadata-v46-runtime-v4610.js\n"


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
        raise RuntimeError("patch V4.6.10 não inseriu avisos no manifesto")

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
    return source + "\n//# sourceURL=/app/extrator-ui-v4610.js\n"


def validate_runtime_patches() -> None:
    metadata_source = patched_metadata_runtime_source()
    ui_source = patched_ui_source()
    required = (
        (metadata_source, "family_errors", "runtime físico por família"),
        (ui_source, "familyWarnings", "UI por família"),
        (ui_source, "continue_pipeline", "continuidade do relatório"),
    )
    for source, marker, label in required:
        if marker not in source:
            raise RuntimeError(f"patch V4.6.10 incompleto: {label} sem {marker}")
    legacy.runtime_log(
        "Patches V4.6.10 validados antes da abertura: "
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
            '<script src="/app/metadata-v46-runtime-v4610.js?v=4.6.10"></script>'
        )
        html = html.replace(original_metadata_runtime, patched_metadata_runtime)

        original_ui = '<script src="app/extrator-ui.js"></script>'
        patched_ui = '<script src="/app/extrator-ui-v4610.js?v=4.6.10"></script>'
        html = html.replace(original_ui, patched_ui)

        bridge = '<script src="/app/source-local-bridge.js"></script>'
        if bridge not in html:
            html = html.replace(patched_ui, f"{bridge}\n  {patched_ui}")

        diagnostic = '<script src="/app/diagnostico-v467.js?v=4.6.10"></script>'
        if diagnostic not in html:
            html = html.replace(patched_ui, f"{diagnostic}\n  {patched_ui}")

        metadata = '<script src="/app/metadados-v46.js" defer></script>'
        if metadata not in html:
            html = html.replace("</body>", f"  {metadata}\n</body>")

        data = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/app/metadata-v46-runtime-v4610.js":
            data = patched_metadata_runtime_source().encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path == "/app/extrator-ui-v4610.js":
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
            self.send_json(
                HTTPStatus.OK,
                {
                    "ready": snapshot is not None,
                    "approved": approved,
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
        global LAST_DIMENSIONS_REPORT
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
                response = {
                    **result,
                    "continue_pipeline": True,
                    "application_blocked": not bool(result.get("passed")),
                    "snapshot_cached_for_manual_apply": True,
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
                self.send_json(
                    HTTPStatus.BAD_REQUEST,
                    LAST_DIMENSIONS_REPORT,
                )
            return

        if path == "/api/card-dimensions/apply-cached":
            if not LAST_DIMENSIONS_REPORT or not LAST_DIMENSIONS_REPORT.get("passed"):
                self.send_json(
                    HTTPStatus.CONFLICT,
                    {
                        "error": (
                            "aplicação de Dimensões bloqueada: a família possui "
                            "divergências ou erro de leitura; as outras famílias "
                            "continuam disponíveis"
                        ),
                        "validation": LAST_DIMENSIONS_REPORT,
                        "database_write": False,
                    },
                )
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
            "Divergência de uma família é registrada e não interrompe "
            "as demais leituras."
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
