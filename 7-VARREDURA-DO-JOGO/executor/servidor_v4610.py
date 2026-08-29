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


RUNTIME_VERSION = "4.6.10"
DEFAULT_PORT = 8774
PATCH_DIR = Path(legacy.base.ROOT) / "app" / "patches-v4610"

legacy.RUNTIME_VERSION = RUNTIME_VERSION
legacy.DEFAULT_PORT = DEFAULT_PORT
legacy.base.validate_impetos = validate_impetos_v4610


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
        if urlparse(self.path).path == "/app/extrator-ui-v4610.js":
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
    port = int(
        legacy.base.os.environ.get(
            "CLUBEF_EXTRACTOR_PORT",
            str(DEFAULT_PORT),
        )
    )
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
