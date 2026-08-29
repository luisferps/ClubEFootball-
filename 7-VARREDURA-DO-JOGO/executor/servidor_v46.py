"""Servidor operacional do Extrator eFootball V4.6.7.

Estende o servidor base sem duplicar sua lógica. Esta versão usa uma porta
exclusiva, valida a própria versão de runtime e registra falhas de transporte,
exceções HTTP e erros do navegador em um log persistente.
"""

from __future__ import annotations

import json
import os
import threading
import traceback
import webbrowser
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import executor_local as base
from card_dimensions_apply import apply_card_dimensions, readback_card_dimensions


RUNTIME_VERSION = "4.6.7"
DEFAULT_PORT = 8771


def runtime_log(message: str) -> None:
    """Escreve em stderr; o launcher Windows persiste a saída no log único."""
    try:
        print(f"[V{RUNTIME_VERSION}] {message}", file=base.sys.stderr, flush=True)
    except Exception:
        pass


def _thread_exception_hook(args: threading.ExceptHookArgs) -> None:
    try:
        detail = "".join(
            traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)
        ).strip()
        runtime_log(
            f"EXCECAO-THREAD | {args.thread.name if args.thread else 'sem-thread'} | {detail}"
        )
    except Exception:
        pass


threading.excepthook = _thread_exception_hook


class LoggedThreadingHTTPServer(ThreadingHTTPServer):
    """Registra exceções que o socketserver captura fora do Handler."""

    daemon_threads = True

    def handle_error(self, request: Any, client_address: Any) -> None:
        detail = traceback.format_exc().strip()
        runtime_log(f"EXCECAO-REQUISICAO | cliente={client_address} | {detail}")
        super().handle_error(request, client_address)


_BASE_CONTRACT_CATALOGS = base.contract_catalogs
_V46_CANONICAL_CATALOGS: dict[str, tuple[str, ...]] = {
    "afinidade_tecnico_jogo": ("codigo_jogo",),
    "atributo_ordem_otimizador": ("indice_otimizador",),
    "estilo_jogo_tecnico": ("ordem",),
    "impeto_jogo": ("codigo_jogo",),
    "impeto_atributo_jogo": ("codigo_impeto", "ordem"),
    "tipo_impeto_jogo": ("codigo_raw",),
    "impeto_condicao_jogo": ("codigo_impeto",),
    "impeto_condicao_nacionalidade_jogo": ("codigo_impeto", "codigo_nacionalidade"),
    "impeto_condicao_liga_jogo": ("codigo_impeto", "codigo_liga_categoria"),
    "impeto_condicao_classe_jogo": ("codigo_impeto",),
    "impeto_condicao_parametro_faixa_jogo": ("codigo_impeto",),
    "impeto_condicao_liga_membro_jogo": ("codigo_impeto", "ordem_fisica"),
    "posicao_jogo": ("id",),
}


def contract_catalogs_v46(connection: Any, contract: dict[str, Any], sql: Any) -> list[dict[str, Any]]:
    """Entrega ao Extrator as próprias linhas canônicas usadas pelos acessórios."""
    catalogs = _BASE_CONTRACT_CATALOGS(connection, contract, sql)
    existing = {(str(item.get("schema")), str(item.get("table"))) for item in catalogs}
    with connection.cursor() as cursor:
        for table, keys in sorted(_V46_CANONICAL_CATALOGS.items()):
            identity = ("clube_novo", table)
            if identity in existing:
                continue
            query = sql.SQL("select row_to_json(source) from clube_novo.{} source order by {}").format(
                sql.Identifier(table),
                sql.SQL(",").join(sql.Identifier(key) for key in keys),
            )
            cursor.execute(query)
            rows = [item[0] for item in cursor.fetchall()]
            if not rows or any(not isinstance(row, dict) for row in rows):
                raise RuntimeError(f"catálogo canônico clube_novo.{table} não retornou linhas utilizáveis")
            catalogs.append({"schema": "clube_novo", "table": table, "keys": list(keys), "rows": rows})
            existing.add(identity)
    return sorted(catalogs, key=lambda item: (str(item.get("schema")), str(item.get("table"))))


base.contract_catalogs = contract_catalogs_v46
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


def diagnostic_log_path() -> Path:
    configured = os.environ.get("CLUBEF_EXTRACTOR_LOG")
    if configured:
        return Path(configured)
    return Path(base.ROOT) / "logs" / "extrator-v46.log"


def read_log_tail(max_lines: int = 350, max_chars: int = 80_000) -> str:
    path = diagnostic_log_path()
    try:
        if not path.is_file():
            return f"Log ainda não existe: {path}"
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()[-max_lines:]
        tail = "\n".join(lines)
        return tail[-max_chars:]
    except Exception as error:
        return f"Não foi possível ler o log {path}: {type(error).__name__}: {error}"


class Handler(base.Handler):
    server_version = f"ClubEfootballLocal/{RUNTIME_VERSION}"

    def log_message(self, format: str, *args: Any) -> None:
        try:
            runtime_log(f"HTTP | {self.client_address[0]} | {format % args}")
        except Exception:
            pass

    def send_json(self, status: HTTPStatus | int, payload: Any) -> None:
        try:
            code = int(status)
            if code >= 400:
                detail = json.dumps(payload, ensure_ascii=False, default=str, separators=(",", ":"))
                runtime_log(f"HTTP-ERRO | {self.command} {self.path} | status={code} | {detail[:12000]}")
        except Exception as error:
            runtime_log(f"FALHA-AO-REGISTRAR-HTTP | {error}")
        super().send_json(status, payload)

    def _serve_injected_ui(self) -> None:
        html_path = Path(base.ROOT) / "Extrator-ClubEfootball.html"
        html = html_path.read_text(encoding="utf-8-sig")
        core_marker = '<script src="app/extrator-core.js"></script>'
        runtime_marker = '<script src="app/contrato-v46-runtime.js"></script>'
        if runtime_marker not in html:
            html = html.replace(core_marker, f"{core_marker}\n  {runtime_marker}")

        bridge_marker = '<script src="/app/source-local-bridge.js"></script>'
        ui_marker = '<script src="app/extrator-ui.js"></script>'
        if bridge_marker not in html:
            html = html.replace(ui_marker, f"{bridge_marker}\n  {ui_marker}")

        diagnostic_marker = '<script src="/app/diagnostico-v467.js"></script>'
        if diagnostic_marker not in html:
            html = html.replace(ui_marker, f"{diagnostic_marker}\n  {ui_marker}")

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

    def _serve_local_source_file(self, role: str) -> None:
        try:
            source_path = base.discovered_source_path(role)
            size = source_path.stat().st_size
            runtime_log(f"ARQUIVO-INICIO | role={role} | arquivo={source_path} | bytes={size}")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(size))
            self.send_header("Content-Disposition", f'attachment; filename="{source_path.name}"')
            self.end_headers()
            total = 0
            with source_path.open("rb") as handle:
                while chunk := handle.read(1024 * 1024):
                    self.wfile.write(chunk)
                    total += len(chunk)
            runtime_log(f"ARQUIVO-FIM | role={role} | bytes_enviados={total}")
        except (ValueError, FileNotFoundError, OSError) as error:
            runtime_log(f"ARQUIVO-ERRO | role={role} | {type(error).__name__}: {error}")
            self.send_json(HTTPStatus.NOT_FOUND, {"error": str(error), "database_write": False})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/Extrator-ClubEfootball.html"}:
            self._serve_injected_ui()
            return

        if parsed.path == "/api/runtime-version":
            try:
                config_source = base.load_config().get("_source")
            except Exception as error:
                config_source = f"erro: {type(error).__name__}: {error}"
            self.send_json(HTTPStatus.OK, {
                "online": True,
                "version": RUNTIME_VERSION,
                "port": self.server.server_address[1],
                "config_source": config_source,
                "database_write": False,
            })
            return

        if parsed.path == "/api/diagnostico":
            try:
                config_source = base.load_config().get("_source")
            except Exception as error:
                config_source = f"erro: {type(error).__name__}: {error}"
            try:
                connection_source = base.connection_source()
            except Exception as error:
                connection_source = f"erro: {type(error).__name__}: {error}"
            self.send_json(HTTPStatus.OK, {
                "runtime_version": RUNTIME_VERSION,
                "pid": os.getpid(),
                "port": self.server.server_address[1],
                "root": str(base.ROOT),
                "config_source": config_source,
                "connection_source": connection_source,
                "log_path": str(diagnostic_log_path()),
                "log_tail": read_log_tail(),
                "database_write": False,
            })
            return

        if parsed.path == "/local-sources/status":
            self.send_json(HTTPStatus.OK, base.discover_sources())
            return
        if parsed.path == "/local-sources/file":
            role = (parse_qs(parsed.query).get("role") or [""])[0]
            self._serve_local_source_file(role)
            return

        if parsed.path == "/api/card-dimensions/cached-status":
            config = base.load_config()
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

        if path == "/api/client-log":
            try:
                payload = self.read_json()
                detail = json.dumps(payload, ensure_ascii=False, default=str, separators=(",", ":"))
                runtime_log(f"CLIENTE | {detail[:12000]}")
                self.send_json(HTTPStatus.OK, {"logged": True, "database_write": False})
            except Exception as error:
                runtime_log(f"CLIENTE-LOG-ERRO | {type(error).__name__}: {error}")
                self.send_json(HTTPStatus.BAD_REQUEST, {"logged": False, "error": str(error), "database_write": False})
            return

        if path == "/api/card-dimensions/validate":
            try:
                config = base.load_config()
                self._reading_contract = base.current_reading_contract(config)
                payload = self.read_json()
                snapshot = payload.get("snapshot")
                if not isinstance(snapshot, dict):
                    raise ValueError("a fotografia física de Dimensões não foi recebida")
                result = base.current_card_dimensions_validation(snapshot, config)
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
                runtime_log("FALHA-FECHADA | " + "".join(traceback.format_exception(type(error), error, error.__traceback__)).strip())
                self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"falha fechada: {error}", "database_write": False})
            finally:
                DIMENSIONS_LOCK.release()
            return

        super().do_POST()


def main() -> None:
    host = "127.0.0.1"
    port = int(base.os.environ.get("CLUBEF_EXTRACTOR_PORT", str(DEFAULT_PORT)))
    server = LoggedThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}/Extrator-ClubEfootball.html"
    try:
        config_source = base.load_config().get("_source")
    except Exception as error:
        config_source = f"erro: {type(error).__name__}: {error}"
    runtime_log(
        f"Servidor iniciado em {url}; pid={os.getpid()}; raiz={base.ROOT}; config={config_source}; log={diagnostic_log_path()}"
    )
    if base.sys.stdout is not None:
        print(f"Extrator eFootball V{RUNTIME_VERSION} disponível em {url}")
        print("Fluxo produtivo: Metadados/Dimensões -> Cartas. Escrita continua manual e confirmada.")
    if "--no-browser" not in base.sys.argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        runtime_log("Servidor encerrado por KeyboardInterrupt.")
    except Exception as error:
        runtime_log("FALHA-SERVIDOR | " + "".join(traceback.format_exception(type(error), error, error.__traceback__)).strip())
        raise
    finally:
        server.server_close()
        runtime_log("Servidor local encerrado.")


if __name__ == "__main__":
    main()
