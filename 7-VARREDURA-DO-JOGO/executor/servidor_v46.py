"""Servidor operacional do Extrator eFootball V4.6.

Extende o servidor V4.5 sem duplicar sua lógica: reabilita a escrita manual já
autorizada e acrescenta a aplicação segura de Dimensões (catálogos primeiro,
vínculos das cartas depois).
"""

from __future__ import annotations

import json
import threading
import webbrowser
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import servidor_local as base
from card_dimensions_apply import apply_card_dimensions, readback_card_dimensions


# A V4.5 foi entregue deliberadamente travada. A V4.6 é a entrega posterior
# explicitamente autorizada para voltar a escrever de forma manual e auditada.
base.PRODUCTIVE_WRITES_LOCKED = False

LAST_DIMENSIONS: dict | None = None
DIMENSIONS_LOCK = threading.Lock()
REQUIRED_CONFIRMATION = "APLICAR METADADOS PRIMEIRO"


def dimensions_apply_allowed(config: dict) -> bool:
    database = config.get("database") or {}
    explicit = config.get("allow_manual_dimensions_apply")
    if explicit is None:
        explicit = config.get("allow_manual_card_apply", False)
    return (
        database.get("schema") == "clube_novo"
        and database.get("cards_table") == "carta_jogo"
        and bool(explicit)
        and bool(base.connection_string())
    )


class Handler(base.Handler):
    server_version = "ClubEfootballLocal/4.6"

    def _serve_injected_ui(self) -> None:
        html_path = Path(base.ROOT) / "Extrator-ClubEfootball.html"
        html = html_path.read_text(encoding="utf-8-sig")
        marker = '<script src="/app/metadados-v46.js" defer></script>'
        if marker not in html:
            html = html.replace("</body>", f"  {marker}\n</body>")
        data = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/Extrator-ClubEfootball.html"}:
            self._serve_injected_ui()
            return
        if parsed.path == "/api/card-dimensions/cached-status":
            config = base.load_config()
            self._reading_contract = base.current_reading_contract(config)
            snapshot = LAST_DIMENSIONS
            self.send_json(HTTPStatus.OK, {
                "ready": snapshot is not None,
                "apply_available": dimensions_apply_allowed(config),
                "source_counts": snapshot.get("counts") if snapshot else None,
                "required_confirmation": REQUIRED_CONFIRMATION,
                "database_write": False,
            })
            return
        super().do_GET()

    def do_POST(self) -> None:
        global LAST_DIMENSIONS
        path = urlparse(self.path).path
        if path == "/api/card-dimensions/validate":
            try:
                config = base.load_config()
                self._reading_contract = base.current_reading_contract(config)
                payload = self.read_json()
                snapshot = payload.get("snapshot")
                if not isinstance(snapshot, dict):
                    raise ValueError("a fotografia física de Dimensões não foi recebida")
                result = base.current_card_dimensions_validation(snapshot, config)
                # A fotografia só é guardada depois de passar pelo comparador estrutural.
                # Divergência com o banco é justamente o que a aplicação deve corrigir.
                if result.get("source_contract") != snapshot.get("contract"):
                    raise ValueError("o readback não corresponde à fotografia física recebida")
                LAST_DIMENSIONS = snapshot
                status = HTTPStatus.OK if result.get("passed") else HTTPStatus.CONFLICT
                self.send_json(status, {**result, "snapshot_cached_for_manual_apply": True})
            except (RuntimeError, ValueError, OSError, json.JSONDecodeError) as error:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(error), "database_write": False})
            return

        if path == "/api/card-dimensions/apply-cached":
            if not DIMENSIONS_LOCK.acquire(blocking=False):
                self.send_json(HTTPStatus.CONFLICT, {"error": "uma aplicação de metadados já está em andamento"})
                return
            try:
                config = base.load_config()
                self._reading_contract = base.current_reading_contract(config)
                payload = self.read_json()
                if str(payload.get("confirmation") or "").strip() != REQUIRED_CONFIRMATION:
                    raise PermissionError("confirmação de metadados incorreta")
                if not dimensions_apply_allowed(config):
                    raise PermissionError("aplicação manual de Dimensões não está habilitada")
                snapshot = LAST_DIMENSIONS
                if snapshot is None:
                    raise ValueError("execute primeiro a comparação de Metadados para gerar a fotografia física")

                psycopg, sql, _ = base.import_psycopg()
                dsn = base.connection_string()
                if not dsn:
                    raise RuntimeError("conexão segura com clube_novo indisponível")

                with psycopg.connect(dsn, connect_timeout=20) as connection:
                    with connection.transaction():
                        with connection.cursor() as cursor:
                            cursor.execute("set transaction isolation level serializable")
                        result = apply_card_dimensions(snapshot, connection, "clube_novo", sql)

                with psycopg.connect(dsn, connect_timeout=20) as verification:
                    verification.read_only = True
                    readback = readback_card_dimensions(snapshot, verification, "clube_novo", sql)

                self.send_json(HTTPStatus.OK, {
                    "applied": True,
                    "result": result,
                    "readback": readback,
                    "database_write": True,
                    "next": "aplicar_cards_depois_dos_metadados",
                })
            except PermissionError as error:
                self.send_json(HTTPStatus.FORBIDDEN, {"error": str(error), "database_write": False})
            except (RuntimeError, ValueError, OSError, json.JSONDecodeError) as error:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(error), "database_write": False})
            except Exception as error:
                self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"falha fechada: {error}", "database_write": False})
            finally:
                DIMENSIONS_LOCK.release()
            return

        super().do_POST()


def main() -> None:
    host = "127.0.0.1"
    port = int(base.os.environ.get("CLUBEF_EXTRACTOR_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}/Extrator-ClubEfootball.html"
    if base.sys.stdout is not None:
        print(f"Extrator eFootball V4.6 disponível em {url}")
        print("Fluxo produtivo: Metadados/Dimensões -> Cartas. Escrita continua manual e confirmada.")
    if "--no-browser" not in base.sys.argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
