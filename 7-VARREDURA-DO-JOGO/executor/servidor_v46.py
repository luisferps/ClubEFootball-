"""Servidor operacional do Extrator eFootball V4.6.

Estende o servidor V4.5 sem duplicar sua lógica: preserva o fluxo existente e
faz o runtime V4.6 receber diretamente as tabelas/catálogos canônicos que já
contêm as referências físicas usadas na extração.
"""

from __future__ import annotations

import json
import threading
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import executor_local as base
from card_dimensions_apply import apply_card_dimensions, readback_card_dimensions


_BASE_CONTRACT_CATALOGS = base.contract_catalogs
_BASE_DEFAULT_SOURCE_DEFINITIONS = base.default_source_definitions
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
            query = sql.SQL("select row_to_json(source) from clube_novo.{} source order by {}") .format(
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


def default_source_definitions_v46() -> dict[str, dict[str, Any]]:
    """Acrescenta ao executor as raízes reais conhecidas da instalação Windows."""
    definitions = _BASE_DEFAULT_SOURCE_DEFINITIONS()
    program_data = Path(base.os.environ.get("ProgramData", r"C:\ProgramData"))
    program_files_x86 = Path(base.os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    program_files = Path(base.os.environ.get("ProgramFiles", r"C:\Program Files"))

    download_root = program_data / "KONAMI" / "eFootball" / "ST" / "Download"
    steam_roots = [
        program_files_x86 / "Steam" / "steamapps" / "common" / "eFootball",
        program_files / "Steam" / "steamapps" / "common" / "eFootball",
    ]

    # Candidatos diretos conhecidos. Eles independem do launcher .cmd.
    definitions["dt870_updated"]["candidates"] = [
        download_root / "dt870_console_win.cpk",
        *[Path(value) for value in definitions["dt870_updated"].get("candidates", [])],
    ]
    definitions["dt870_updated"]["search_roots"] = [download_root]

    direct_names = {
        "dt200": "dt200_console_all.cpk",
        "dt870_original": "dt870_console_win.cpk",
        "dt261_bra": "dt261_bra_console_win.cpk",
    }
    for role, filename in direct_names.items():
        explicit = [root / "cpk" / filename for root in steam_roots]
        definitions[role]["candidates"] = explicit + [Path(value) for value in definitions[role].get("candidates", [])]
        definitions[role]["search_roots"] = steam_roots
    return definitions


def inspect_source_v46(role: str, definition: dict[str, Any]) -> dict[str, Any]:
    """Localiza o arquivo físico; a validação autoritativa fica no contrato.

    O executor antigo recusava a fonte antes mesmo da validação contratual com
    base apenas nos quatro bytes iniciais do contêiner. Isso fazia arquivos reais
    existentes aparecerem como 'não encontrados'. Aqui a descoberta responde só
    à pergunta 'onde está o arquivo?'. Depois de servido, o runtime valida
    fingerprint/tamanho/contrato antes de considerar a fonte pronta.
    """
    filename = str(definition.get("filename") or "").strip()
    matches: list[Path] = []
    seen: set[str] = set()
    errors: list[dict[str, str]] = []

    def add(path_value: Any) -> None:
        path = Path(path_value)
        key = str(path).lower()
        if key in seen:
            return
        seen.add(key)
        try:
            if path.is_file():
                matches.append(path)
        except OSError as error:
            errors.append({"location": str(path), "reason": str(error)})

    for candidate in definition.get("candidates") or []:
        add(candidate)

    if filename:
        for root_value in definition.get("search_roots") or []:
            root = Path(root_value)
            try:
                if not root.is_dir():
                    continue
                # Primeiro o local normal da Steam; depois busca recursiva para
                # ST\\Download e instalações fora da estrutura mais comum.
                add(root / "cpk" / filename)
                add(root / filename)
                for path in root.rglob(filename):
                    add(path)
            except OSError as error:
                errors.append({"location": str(root), "reason": str(error)})

    if matches:
        # Para o DT870 atualizado podem coexistir cópias históricas; a mais nova
        # é tentada primeiro. O fingerprint do contrato ainda decide se ela vale.
        matches.sort(key=lambda path: path.stat().st_mtime, reverse=True)
        path = matches[0]
        stat = path.stat()
        return {
            "role": role,
            "label": definition["label"],
            "filename": definition["filename"],
            "purpose": definition["purpose"],
            "operations": definition["operations"],
            "found": True,
            "valid_container": True,
            "location": str(path),
            "bytes": stat.st_size,
            "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            "discovery_mode": "filesystem_known_root",
            "matches_found": len(matches),
        }

    return {
        "role": role,
        "label": definition["label"],
        "filename": definition["filename"],
        "purpose": definition["purpose"],
        "operations": definition["operations"],
        "found": False,
        "valid_container": False,
        "reason": "fonte não encontrada automaticamente nas pastas conhecidas; use seleção manual",
        "invalid_candidates": errors,
        "discovery_mode": "manual_fallback_required",
    }


base.contract_catalogs = contract_catalogs_v46
base.default_source_definitions = default_source_definitions_v46
base.inspect_source = inspect_source_v46
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
        core_marker = '<script src="app/extrator-core.js"></script>'
        runtime_marker = '<script src="app/contrato-v46-runtime.js"></script>'
        if runtime_marker not in html:
            html = html.replace(core_marker, f"{core_marker}\n  {runtime_marker}")
        metadata_marker = '<script src="/app/metadados-v46.js" defer></script>'
        if metadata_marker not in html:
            html = html.replace("</body>", f"  {metadata_marker}\n</body>")
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
        discovery = base.discover_sources()
        print("Fontes físicas detectadas:")
        for role, source in discovery.get("sources", {}).items():
            print(f"  {role}: {source.get('location') if source.get('found') else 'NÃO ENCONTRADO'}")
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
