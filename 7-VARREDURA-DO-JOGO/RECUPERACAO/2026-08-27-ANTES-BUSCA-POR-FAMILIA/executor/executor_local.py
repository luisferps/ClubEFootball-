"""Executor local seguro do Extrator ClubEfootball.

Serve a interface em 127.0.0.1 e concentra toda interação com PostgreSQL/Supabase.
O navegador nunca recebe credenciais. A configuração distribuída nasce em dry-run.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sys
import threading
import time
import uuid
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CONFIG_LOCAL = ROOT / "configuracao.local.json"
CONFIG_EXAMPLE = ROOT / "configuracao.exemplo.json"
ARTIFACTS = ROOT / "artefatos" / "aplicacoes"
CONTRACT = "clubef-extrator-v3"
CARD_COLUMNS = [
    "card_id", "tipo", "overall", "roda_motor", "nome", "posicao",
    "slot_ofensivo_id", "slot_ofensivo_confirmado", "slot_defensivo_id",
    "slot_defensivo_confirmado", "pe", "altura", "peso", "idade",
    "nacionalidade", "pe_ruim_uso", "pe_ruim_precisao", "resistencia_lesao",
    "forma", "impeto_s1", "impeto_s2_cond", "vaga_s1", "vaga_s2", "box",
    "atributos", "habilidades", "aptidoes", "estilos_ia", "corpo",
]
INTEGER_COLUMNS = {
    "overall", "slot_ofensivo_id", "slot_defensivo_id", "altura", "peso",
    "idade", "pe_ruim_uso", "pe_ruim_precisao", "forma", "impeto_s1",
    "impeto_s2_cond",
}
BOOLEAN_COLUMNS = {
    "roda_motor", "slot_ofensivo_confirmado", "slot_defensivo_confirmado",
    "vaga_s1", "vaga_s2",
}
JSON_COLUMNS = {"atributos", "habilidades", "aptidoes", "estilos_ia", "corpo"}
ALLOWED_MODES = {"card_diff", "metadata_diff"}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def parse_iso(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def load_config() -> dict[str, Any]:
    path = CONFIG_LOCAL if CONFIG_LOCAL.exists() else CONFIG_EXAMPLE
    with path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    config["_source"] = path.name
    return config


def connection_string() -> str | None:
    return os.environ.get("CLUBEF_SUPABASE_DB_URL")


def write_is_enabled(config: dict[str, Any]) -> bool:
    return bool(config.get("write_enabled")) and os.environ.get("CLUBEF_ENABLE_REAL_WRITE") == "EU_AUTORIZO_ESCRITA_REAL"


def import_psycopg():
    try:
        import psycopg  # type: ignore
        from psycopg import sql  # type: ignore
        from psycopg.types.json import Jsonb  # type: ignore
    except ImportError as error:
        raise RuntimeError("psycopg não está instalado; execute INSTALAR-DEPENDENCIAS.cmd") from error
    return psycopg, sql, Jsonb


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any]) -> None:
    if manifest.get("contract") != CONTRACT:
        raise ValueError("manifesto incompatível com esta versão do executor")
    if manifest.get("mode") not in ALLOWED_MODES:
        raise ValueError("modo de manifesto não aplicável")
    try:
        uuid.UUID(str(manifest["execution_id"]))
    except (KeyError, ValueError):
        raise ValueError("execution_id inválido") from None
    received_hash = manifest.get("manifest_sha256")
    body = dict(manifest)
    body.pop("manifest_sha256", None)
    if not secrets.compare_digest(str(received_hash or ""), sha256_json(body)):
        raise ValueError("hash do manifesto não confere")
    now = datetime.now(timezone.utc)
    generated = parse_iso(manifest["generated_at"])
    expires = parse_iso(manifest["expires_at"])
    max_age = int(config.get("max_manifest_age_minutes", 60))
    if generated > now or (now - generated).total_seconds() > max_age * 60 or now >= expires:
        raise ValueError("diff obsoleto; extraia e compare novamente")
    if manifest.get("database_write") is not False:
        raise ValueError("manifesto de extração inválido: estado de escrita inesperado")


def normalize_csv_value(column: str, value: Any) -> str:
    if value is None:
        return ""
    if column in BOOLEAN_COLUMNS:
        if isinstance(value, str):
            if value == "":
                return ""
            if value.lower() not in {"true", "false"}:
                raise ValueError(f"booleano inválido em {column}")
            return value.lower()
        return "true" if bool(value) else "false"
    if column in JSON_COLUMNS:
        if isinstance(value, str):
            if value == "":
                return ""
            value = json.loads(value)
        return canonical(value)
    return str(value)


def parse_csv_value(column: str, value: Any, Jsonb: Any) -> Any:
    if value in (None, ""):
        return None
    if column in INTEGER_COLUMNS:
        return int(value)
    if column in BOOLEAN_COLUMNS:
        if str(value).lower() not in {"true", "false"}:
            raise ValueError(f"booleano inválido em {column}")
        return str(value).lower() == "true"
    if column in JSON_COLUMNS:
        return Jsonb(json.loads(value))
    return str(value)


def selected_summary(selection: dict[str, Any]) -> dict[str, int]:
    items = selection.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("nenhum item foi selecionado")
    keys = {
        str(item.get("card_id")) if item.get("card_id") is not None else f"{item.get('catalog')}:{item.get('id')}"
        for item in items
    }
    if len(keys) != len(items):
        raise ValueError("seleção contém chave canônica duplicada")
    return {
        "insert": sum(item.get("action") == "insert" or item.get("action") == "new" for item in items),
        "update": sum(item.get("action") == "update" or item.get("action") == "change" for item in items),
        "inactive": sum(item.get("action") in {"inactive", "absent"} for item in items),
    }


def validate_selection_counts(manifest: dict[str, Any], summary: dict[str, int]) -> None:
    counts = manifest.get("counts") or {}
    expected = {
        "insert": int(counts.get("new", 0)),
        "update": int(counts.get("changed", 0)),
        "inactive": int(counts.get("possibly_inactive", 0)),
    }
    if any(summary[action] > expected[action] for action in expected):
        raise ValueError(f"seleção excede o diff selado: disponível {expected}, recebido {summary}")


def normalized_selection_item(item: dict[str, Any], kind: str) -> dict[str, Any]:
    if kind == "cards":
        keys = ["action", "card_id", "row", "fields"]
    else:
        keys = ["catalog", "action", "id", "record", "before", "after"]
    return {key: item[key] for key in keys if key in item}


def selection_item_key(item: dict[str, Any], kind: str) -> str:
    if kind == "cards":
        return f"{item.get('action')}:{item.get('card_id')}"
    return f"{item.get('catalog')}:{item.get('action')}:{item.get('id')}"


def validate_selection_contract(manifest: dict[str, Any], selection: dict[str, Any]) -> None:
    contract = manifest.get("selection_contract") or {}
    allowed = {str(item.get("key")): str(item.get("sha256")) for item in contract.get("items", [])}
    if not allowed:
        raise ValueError("manifesto não contém contrato selado dos itens aplicáveis")
    kind = str(selection.get("kind"))
    for item in selection["items"]:
        key = selection_item_key(item, kind)
        expected = allowed.get(key)
        received = sha256_json(normalized_selection_item(item, kind))
        if expected is None or not secrets.compare_digest(expected, received):
            raise ValueError(f"item selecionado não pertence integralmente ao diff selado: {key}")


def recovery_plan(selection: dict[str, Any]) -> dict[str, Any]:
    if selection.get("kind") != "cards":
        return {"automatic": False, "reason": "catálogo exige adaptador e plano próprio"}
    return {
        "automatic": False,
        "inserted_card_ids_to_review_for_removal": [str(item["card_id"]) for item in selection["items"] if item.get("action") == "insert"],
        "changed_fields_to_restore": [
            {
                "card_id": str(item["card_id"]),
                "fields": [{"field": field["field"], "restore": field.get("before", ""), "applied": field.get("after", "")} for field in item.get("fields", [])],
            }
            for item in selection["items"]
            if item.get("action") == "update"
        ],
        "instruction": "gerar e revisar um novo diff inverso; nunca executar remoção/restauração automaticamente",
    }


def fetch_card_rows(connection: Any, card_ids: list[str], config: dict[str, Any]) -> dict[str, dict[str, str]]:
    _, sql, _ = import_psycopg()
    schema = config["database"]["schema"]
    table = config["database"]["cards_table"]
    query = sql.SQL("select {} from {}.{} where card_id = any(%s)").format(
        sql.SQL(",").join(sql.Identifier(column) for column in CARD_COLUMNS),
        sql.Identifier(schema),
        sql.Identifier(table),
    )
    with connection.cursor() as cursor:
        cursor.execute(query, (card_ids,))
        return {
            str(values[0]): {column: normalize_csv_value(column, values[index]) for index, column in enumerate(CARD_COLUMNS)}
            for values in cursor.fetchall()
        }


def check_card_preconditions(rows: dict[str, dict[str, str]], items: list[dict[str, Any]]) -> dict[str, int]:
    ready = 0
    already_applied = 0
    for item in items:
        card_id = str(item["card_id"])
        action = item["action"]
        current = rows.get(card_id)
        if action == "inactive":
            raise ValueError("possível inativação bloqueada: carta_jogo não possui coluna canônica de ativo; revise fora deste lote")
        if action == "insert":
            desired = item["row"]
            if current is None:
                ready += 1
            elif all(normalize_csv_value(column, desired.get(column, "")) == current.get(column, "") for column in CARD_COLUMNS):
                already_applied += 1
            else:
                raise ValueError(f"conflito: card_id novo {card_id} já existe com conteúdo diferente")
        elif action == "update":
            if current is None:
                raise ValueError(f"conflito: card_id alterado {card_id} não existe mais")
            fields = item.get("fields") or []
            before_matches = all(normalize_csv_value(field["field"], field.get("before", "")) == current.get(field["field"], "") for field in fields)
            after_matches = all(normalize_csv_value(field["field"], field.get("after", "")) == current.get(field["field"], "") for field in fields)
            if after_matches:
                already_applied += 1
            elif before_matches:
                ready += 1
            else:
                raise ValueError(f"conflito: card_id {card_id} mudou no banco depois da geração do diff")
        else:
            raise ValueError(f"ação de carta não suportada: {action}")
    return {"ready": ready, "already_applied": already_applied}


def readonly_preflight(selection: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    dsn = connection_string()
    if not dsn:
        if config.get("require_database_on_prepare", True):
            raise RuntimeError("CLUBEF_SUPABASE_DB_URL não foi fornecida ao executor")
        return {"database_checked": False, "reason": "conexão não configurada"}
    psycopg, _, _ = import_psycopg()
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        connection.read_only = True
        with connection.cursor() as cursor:
            cursor.execute("show transaction_read_only")
            if cursor.fetchone()[0] != "on":
                raise RuntimeError("preflight não ficou em modo somente leitura")
        if selection["kind"] == "cards":
            items = selection["items"]
            rows = fetch_card_rows(connection, [str(item["card_id"]) for item in items], config)
            preconditions = check_card_preconditions(rows, items)
            return {"database_checked": True, "transaction_read_only": True, **preconditions}
        adapters = config.get("catalog_adapters", {})
        blocked = [item.get("catalog") for item in selection["items"] if not adapters.get(item.get("catalog"), {}).get("enabled")]
        if blocked:
            raise ValueError(f"catálogo sem adaptador canônico habilitado: {', '.join(sorted(set(blocked)))}")
        return {"database_checked": True, "transaction_read_only": True, "ready": len(selection["items"]), "already_applied": 0}


def write_new_card(cursor: Any, item: dict[str, Any], config: dict[str, Any], sql: Any, Jsonb: Any) -> None:
    row = item["row"]
    schema = config["database"]["schema"]
    table = config["database"]["cards_table"]
    query = sql.SQL("insert into {}.{} ({}) values ({}) on conflict (card_id) do nothing").format(
        sql.Identifier(schema),
        sql.Identifier(table),
        sql.SQL(",").join(sql.Identifier(column) for column in CARD_COLUMNS),
        sql.SQL(",").join(sql.Placeholder() for _ in CARD_COLUMNS),
    )
    cursor.execute(query, [parse_csv_value(column, row.get(column, ""), Jsonb) for column in CARD_COLUMNS])
    if cursor.rowcount != 1:
        raise RuntimeError(f"inserção concorrente ou inesperada para card_id {item['card_id']}")


def write_changed_card(cursor: Any, item: dict[str, Any], config: dict[str, Any], sql: Any, Jsonb: Any) -> None:
    fields = [field for field in item.get("fields", []) if field["field"] in CARD_COLUMNS and field["field"] != "card_id"]
    if not fields:
        return
    schema = config["database"]["schema"]
    table = config["database"]["cards_table"]
    query = sql.SQL("update {}.{} set {} where card_id=%s").format(
        sql.Identifier(schema),
        sql.Identifier(table),
        sql.SQL(",").join(sql.SQL("{}=%s").format(sql.Identifier(field["field"])) for field in fields),
    )
    values = [parse_csv_value(field["field"], field.get("after", ""), Jsonb) for field in fields]
    cursor.execute(query, values + [str(item["card_id"])])
    if cursor.rowcount != 1:
        raise RuntimeError(f"update inesperado para card_id {item['card_id']}")


def apply_cards(selection: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    psycopg, sql, Jsonb = import_psycopg()
    dsn = connection_string()
    if not dsn:
        raise RuntimeError("conexão do banco não configurada")
    items = sorted(selection["items"], key=lambda item: int(str(item["card_id"])))
    card_ids = [str(item["card_id"]) for item in items]
    changed = 0
    already_applied = 0
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        with connection.transaction():
            with connection.cursor() as cursor:
                cursor.execute("set transaction isolation level serializable")
                cursor.execute("set local statement_timeout = '120s'")
                lock_name = f"clubef_extractor:{config['database']['schema']}.{config['database']['cards_table']}"
                cursor.execute("select pg_advisory_xact_lock(hashtext(%s))", (lock_name,))
                before = fetch_card_rows(connection, card_ids, config)
                check_card_preconditions(before, items)
                for item in items:
                    current = before.get(str(item["card_id"]))
                    if item["action"] == "insert":
                        desired = item["row"]
                        if current is not None and all(normalize_csv_value(column, desired.get(column, "")) == current.get(column, "") for column in CARD_COLUMNS):
                            already_applied += 1; continue
                        write_new_card(cursor, item, config, sql, Jsonb); changed += 1
                    elif item["action"] == "update":
                        fields = item.get("fields") or []
                        if current is not None and all(normalize_csv_value(field["field"], field.get("after", "")) == current.get(field["field"], "") for field in fields):
                            already_applied += 1; continue
                        write_changed_card(cursor, item, config, sql, Jsonb); changed += 1
                inside = fetch_card_rows(connection, card_ids, config)
                for item in items:
                    row = inside.get(str(item["card_id"]))
                    if row is None:
                        raise RuntimeError(f"readback transacional não encontrou {item['card_id']}")
                    expected_fields = CARD_COLUMNS if item["action"] == "insert" else [field["field"] for field in item.get("fields", [])]
                    expected_row = item["row"]
                    for field in expected_fields:
                        if normalize_csv_value(field, expected_row.get(field, "")) != row.get(field, ""):
                            raise RuntimeError(f"readback transacional divergiu em {item['card_id']}.{field}")
    with psycopg.connect(dsn, connect_timeout=20) as verification:
        verification.read_only = True
        committed = fetch_card_rows(verification, card_ids, config)
        if len(committed) != len(set(card_ids)):
            raise RuntimeError("readback pós-commit não encontrou todos os card_ids")
    return {"changed": changed, "already_applied": already_applied, "readback_count": len(committed), "readback_sha256": sha256_json(committed)}


def apply_selection(selection: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    if selection["kind"] == "cards":
        return apply_cards(selection, config)
    raise ValueError("aplicação real de catálogo bloqueada: configure e teste um adaptador canônico específico")


class ApprovalStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._items: dict[str, dict[str, Any]] = {}
        self._used_executions: set[str] = set()

    def create(self, manifest: dict[str, Any], selection: dict[str, Any], summary: dict[str, int], preflight: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        execution_id = manifest["execution_id"]
        with self._lock:
            if execution_id in self._used_executions:
                raise ValueError("esta execução já foi consumida; gere um novo diff")
            token = secrets.token_urlsafe(32)
            phrase = f"APLICAR {execution_id[-8:].upper()}"
            self._items[token] = {
                "manifest": manifest,
                "selection": selection,
                "selection_sha256": sha256_json(selection),
                "summary": summary,
                "preflight": preflight,
                "confirmation_phrase": phrase,
                "expires_at": time.time() + int(config.get("approval_ttl_minutes", 10)) * 60,
            }
            return {"token": token, "phrase": phrase}

    def consume(self, token: str, confirmation: str) -> dict[str, Any]:
        with self._lock:
            item = self._items.pop(token, None)
            if not item:
                raise ValueError("aprovação inexistente ou já consumida")
            if time.time() >= item["expires_at"]:
                raise ValueError("aprovação expirada")
            if not secrets.compare_digest(confirmation, item["confirmation_phrase"]):
                raise ValueError("frase de confirmação incorreta")
            execution_id = item["manifest"]["execution_id"]
            if execution_id in self._used_executions:
                raise ValueError("execução já aplicada")
            self._used_executions.add(execution_id)
            return item


APPROVALS = ApprovalStore()


def save_manifest(prefix: str, manifest: dict[str, Any]) -> Path:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    final = ARTIFACTS / f"{prefix}-{manifest['execution_id']}.json"
    temporary = final.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    temporary.replace(final)
    return final


class Handler(SimpleHTTPRequestHandler):
    server_version = "ClubEfootballLocal/3"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        super().end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        sys.stdout.write(f"[{self.log_date_time_string()}] {format % args}\n")

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 100 * 1024 * 1024:
            raise ValueError("tamanho de requisição inválido")
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/api/status":
            config = load_config()
            self.send_json(HTTPStatus.OK, {
                "online": True,
                "mode": "write-enabled" if write_is_enabled(config) else "dry-run",
                "write_enabled": write_is_enabled(config),
                "database_configured": bool(connection_string()),
                "config_source": config["_source"],
            })
            return
        if self.path in {"/", ""}:
            self.path = "/Extrator-ClubEfootball.html"
        super().do_GET()

    def do_POST(self) -> None:
        try:
            path = urlparse(self.path).path
            config = load_config()
            if path == "/api/prepare":
                payload = self.read_json()
                manifest = payload.get("manifest") or {}
                selection = payload.get("selection") or {}
                validate_manifest(manifest, config)
                if selection.get("kind") not in {"cards", "metadata"}:
                    raise ValueError("tipo de seleção inválido")
                if manifest["mode"] == "card_diff" and selection["kind"] != "cards":
                    raise ValueError("seleção não corresponde ao manifesto")
                if manifest["mode"] == "metadata_diff" and selection["kind"] != "metadata":
                    raise ValueError("seleção não corresponde ao manifesto")
                summary = selected_summary(selection)
                validate_selection_counts(manifest, summary)
                validate_selection_contract(manifest, selection)
                if len(selection["items"]) > int(config.get("max_selected_items", 50000)):
                    raise ValueError("seleção excede o limite configurado")
                preflight = readonly_preflight(selection, config)
                approval = APPROVALS.create(manifest, selection, summary, preflight, config)
                dry_run_manifest = {
                    "contract": "clubef-application-dry-run-v1",
                    "execution_id": manifest["execution_id"],
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "manifest_sha256": manifest["manifest_sha256"],
                    "selection_sha256": sha256_json(selection),
                    "summary": summary,
                    "selected_items": selection["items"],
                    "preflight": preflight,
                    "recovery_plan": recovery_plan(selection),
                    "database_write": False,
                    "result": "ready_for_final_confirmation" if write_is_enabled(config) else "dry_run_only",
                }
                save_manifest("DRY-RUN", dry_run_manifest)
                self.send_json(HTTPStatus.OK, {
                    "approval_token": approval["token"],
                    "confirmation_phrase": approval["phrase"],
                    "summary": summary,
                    "preflight": preflight,
                    "mode": "write-enabled" if write_is_enabled(config) else "dry-run",
                    "write_enabled": write_is_enabled(config),
                    "dry_run_manifest": dry_run_manifest,
                })
                return
            if path == "/api/apply":
                if not write_is_enabled(config):
                    raise PermissionError("escrita real bloqueada pela configuração e pelo selo de ambiente")
                payload = self.read_json()
                approved = APPROVALS.consume(str(payload.get("approval_token", "")), str(payload.get("confirmation", "")))
                validate_manifest(approved["manifest"], config)
                result = apply_selection(approved["selection"], config)
                application_manifest = {
                    "contract": "clubef-application-manifest-v1",
                    "execution_id": approved["manifest"]["execution_id"],
                    "applied_at": datetime.now(timezone.utc).isoformat(),
                    "source_manifest_sha256": approved["manifest"]["manifest_sha256"],
                    "selection_sha256": approved["selection_sha256"],
                    "summary": approved["summary"],
                    "selected_items": approved["selection"]["items"],
                    "preflight": approved["preflight"],
                    "recovery_plan": recovery_plan(approved["selection"]),
                    "result": result,
                    "database_write": True,
                    "idempotent_keys": "card_id/chave canônica",
                    "transaction": "serializable_fail_closed",
                    "readback": True,
                }
                save_manifest("APLICACAO", application_manifest)
                self.send_json(HTTPStatus.OK, {"application_manifest": application_manifest})
                return
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "rota inexistente"})
        except PermissionError as error:
            self.send_json(HTTPStatus.FORBIDDEN, {"error": str(error)})
        except (ValueError, KeyError, json.JSONDecodeError) as error:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
        except Exception as error:
            self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"falha fechada: {error}"})


def main() -> None:
    host = "127.0.0.1"
    port = int(os.environ.get("CLUBEF_EXTRACTOR_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}/Extrator-ClubEfootball.html"
    print(f"Extrator ClubEfootball disponível em {url}")
    print("Credenciais ficam somente no processo local; nenhuma chave é enviada ao HTML.")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
