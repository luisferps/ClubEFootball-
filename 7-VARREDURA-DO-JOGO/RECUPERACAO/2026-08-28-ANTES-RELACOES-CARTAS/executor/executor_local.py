"""Executor local seguro do Extrator eFootball.

Serve a interface em 127.0.0.1 e concentra toda interação com PostgreSQL/Supabase.
O navegador nunca recebe credenciais. A configuração distribuída nasce sem escrita automática.
"""

from __future__ import annotations

import csv
import hashlib
import io
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
from urllib.parse import parse_qs, quote, urlparse

from texto_do_jogo import (
    apply_text_selection,
    baseline_snapshot as text_baseline_snapshot,
    preflight_text_selection,
)


EXECUTOR_DIR = Path(__file__).resolve().parent
VENDOR_DIR = EXECUTOR_DIR / "vendor"
if VENDOR_DIR.is_dir() and str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

ROOT = EXECUTOR_DIR.parent
CONFIG_LOCAL = ROOT / "configuracao.local.json"
CONFIG_EXAMPLE = ROOT / "configuracao.exemplo.json"
ARTIFACTS = ROOT / "artefatos" / "aplicacoes"
REFERENCE_ROOT = Path(os.environ.get("CLUBEF_REFERENCE_ROOT", str(ROOT / "artefatos" / "referencias-cartas")))
REFERENCE_VERSIONS = REFERENCE_ROOT / "versoes"
REFERENCE_POINTER = REFERENCE_ROOT / "referencia-vigente.json"
REFERENCE_LOCK = threading.Lock()
METADATA_REFERENCE_ROOT = Path(os.environ.get("CLUBEF_METADATA_REFERENCE_ROOT", str(ROOT / "artefatos" / "referencias-metadados")))
METADATA_REFERENCE_VERSIONS = METADATA_REFERENCE_ROOT / "versoes"
METADATA_REFERENCE_POINTER = METADATA_REFERENCE_ROOT / "referencia-vigente.json"
CONTRACT = "clubef-extrator-v4"
REFERENCE_CONTRACT = "clubef-card-reference-v1"
REFERENCE_POINTER_CONTRACT = "clubef-card-reference-pointer-v1"
METADATA_REFERENCE_CONTRACT = "clubef-metadata-reference-v1"
METADATA_REFERENCE_POINTER_CONTRACT = "clubef-metadata-reference-pointer-v1"
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
ALLOWED_MODES = {"card_diff", "card_full", "metadata_diff"}


def default_source_definitions() -> dict[str, dict[str, Any]]:
    program_data = Path(os.environ.get("ProgramData", r"C:\ProgramData"))
    program_files_x86 = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    steam_cpk = program_files_x86 / "Steam" / "steamapps" / "common" / "eFootball" / "cpk"
    return {
        "dt870_updated": {
            "label": "DT870 da atualização",
            "filename": "dt870_console_win.cpk",
            "purpose": "cartas atuais; habilidades; ímpetos atuais; overlay de playstyles",
            "operations": ["cards", "metadata"],
            "candidates": [program_data / "KONAMI" / "eFootball" / "ST" / "Download" / "dt870_console_win.cpk"],
        },
        "dt200": {
            "label": "DT200 base",
            "filename": "dt200_console_all.cpk",
            "purpose": "base semântica de playstyles e ímpetos legados",
            "operations": ["metadata"],
            "candidates": [steam_cpk / "dt200_console_all.cpk"],
        },
        "dt870_original": {
            "label": "DT870 original",
            "filename": "dt870_console_win.cpk",
            "purpose": "ímpetos legados exclusivos e conferência histórica",
            "operations": ["metadata"],
            "candidates": [steam_cpk / "dt870_console_win.cpk"],
        },
        "dt261_bra": {
            "label": "Textos em português",
            "filename": "dt261_bra_console_win.cpk",
            "purpose": "all.str e catálogos textuais",
            "operations": ["metadata"],
            "candidates": [steam_cpk / "dt261_bra_console_win.cpk"],
        },
    }


def source_definitions() -> dict[str, dict[str, Any]]:
    definitions = default_source_definitions()
    overrides = {
        "dt870_updated": "CLUBEF_SOURCE_DT870_UPDATED",
        "dt200": "CLUBEF_SOURCE_DT200",
        "dt870_original": "CLUBEF_SOURCE_DT870_ORIGINAL",
        "dt261_bra": "CLUBEF_SOURCE_DT261_BRA",
    }
    for role, variable in overrides.items():
        configured = os.environ.get(variable)
        if configured:
            definitions[role]["candidates"] = [Path(configured)]
    return definitions


def inspect_source(role: str, definition: dict[str, Any]) -> dict[str, Any]:
    invalid: list[dict[str, str]] = []
    for candidate in definition["candidates"]:
        path = Path(candidate)
        try:
            if not path.is_file():
                continue
            with path.open("rb") as handle:
                magic = handle.read(4)
            if magic != b"CPK ":
                invalid.append({"location": str(path), "reason": "arquivo não é um CPK válido"})
                continue
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
            }
        except OSError as error:
            invalid.append({"location": str(path), "reason": str(error)})
    return {
        "role": role,
        "label": definition["label"],
        "filename": definition["filename"],
        "purpose": definition["purpose"],
        "operations": definition["operations"],
        "found": False,
        "valid_container": False,
        "reason": invalid[0]["reason"] if invalid else "fonte não encontrada nos locais conhecidos",
        "invalid_candidates": invalid,
    }


def discover_sources() -> dict[str, Any]:
    definitions = source_definitions()
    sources = {role: inspect_source(role, definition) for role, definition in definitions.items()}
    requirements = {
        "cards": ["dt870_updated"],
        "metadata": ["dt870_updated", "dt200", "dt870_original", "dt261_bra"],
    }
    operations = {}
    for operation, required in requirements.items():
        missing = [role for role in required if not sources[role]["found"]]
        operations[operation] = {"required": required, "missing": missing, "ready": not missing}
    return {
        "contract": "clubef-source-discovery-v1",
        "sources": sources,
        "operations": operations,
        "rules": {
            "cards": "somente DT870 da atualização, obrigatório e autoritativo",
            "metadata": "fontes separadas por família; nenhuma fusão genérica de CPKs",
        },
    }


def discovered_source_path(role: str) -> Path:
    definitions = source_definitions()
    if role not in definitions:
        raise ValueError("papel de fonte desconhecido")
    source = inspect_source(role, definitions[role])
    if not source["found"]:
        raise FileNotFoundError(source.get("reason") or "fonte não encontrada")
    return Path(source["location"])


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def validate_reference_csv(csv_text: str) -> dict[str, Any]:
    clean_text = csv_text.lstrip("\ufeff")
    reader = csv.DictReader(io.StringIO(clean_text, newline=""))
    headers = reader.fieldnames or []
    if headers != CARD_COLUMNS:
        raise ValueError("a carga extraída não possui os 29 campos esperados")
    ids: set[str] = set()
    duplicate_ids: list[str] = []
    missing_by_field = {column: 0 for column in CARD_COLUMNS}
    invalid_structured = {column: 0 for column in JSON_COLUMNS}
    records = 0
    for row in reader:
        if None in row:
            raise ValueError("a carga extraída contém colunas inesperadas")
        records += 1
        card_id = str(row.get("card_id") or "").strip()
        if not card_id:
            raise ValueError("a carga extraída contém card_id vazio")
        if card_id in ids and len(duplicate_ids) < 100:
            duplicate_ids.append(card_id)
        ids.add(card_id)
        for column in CARD_COLUMNS:
            if str(row.get(column) or "").strip() == "":
                missing_by_field[column] += 1
        for column in JSON_COLUMNS:
            try:
                json.loads(row.get(column) or "")
            except (TypeError, json.JSONDecodeError):
                invalid_structured[column] += 1
    if records <= 0:
        raise ValueError("a carga extraída está vazia")
    if duplicate_ids:
        raise ValueError(f"a carga extraída contém card_id duplicado: {duplicate_ids[0]}")
    invalid_columns = [column for column, count in invalid_structured.items() if count]
    if invalid_columns:
        raise ValueError(f"campos estruturados inválidos: {', '.join(invalid_columns)}")
    return {
        "records": records,
        "unique_card_ids": len(ids),
        "duplicate_card_ids": duplicate_ids,
        "schema": headers,
        "missing_by_field": missing_by_field,
        "invalid_structured": invalid_structured,
    }


def compare_reference_csv(current_text: str, previous_text: str) -> dict[str, int]:
    def keyed(text: str) -> dict[str, dict[str, str]]:
        reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff"), newline=""))
        return {str(row["card_id"]): row for row in reader}

    current = keyed(current_text)
    previous = keyed(previous_text)
    new_ids = current.keys() - previous.keys()
    inactive_ids = previous.keys() - current.keys()
    common_ids = current.keys() & previous.keys()
    changed = sum(1 for card_id in common_ids if any(current[card_id].get(column, "") != previous[card_id].get(column, "") for column in CARD_COLUMNS))
    return {
        "previous": len(previous),
        "current": len(current),
        "new": len(new_ids),
        "changed": changed,
        "possibly_inactive": len(inactive_ids),
        "unchanged": len(common_ids) - changed,
    }


def _verified_reference() -> tuple[dict[str, Any], Path, dict[str, Any]]:
    if not REFERENCE_POINTER.is_file():
        raise FileNotFoundError("a referência interna de cartas ainda não foi instalada")
    pointer = json.loads(REFERENCE_POINTER.read_text(encoding="utf-8-sig"))
    if pointer.get("contract") != REFERENCE_POINTER_CONTRACT or not pointer.get("reference_id"):
        raise ValueError("o apontador da referência interna é inválido")
    version_dir = REFERENCE_VERSIONS / str(pointer["reference_id"])
    manifest_path = version_dir / "manifesto.json"
    csv_path = version_dir / "carta_jogo.csv"
    if not manifest_path.is_file() or not csv_path.is_file():
        raise FileNotFoundError("os arquivos da referência interna estão incompletos")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if manifest.get("contract") != REFERENCE_CONTRACT:
        raise ValueError("o manifesto da referência interna é incompatível")
    sealed = dict(manifest)
    declared_manifest_sha = sealed.pop("manifest_sha256", "")
    actual_manifest_sha = sha256_json(sealed)
    if declared_manifest_sha != actual_manifest_sha or pointer.get("manifest_sha256") != actual_manifest_sha:
        raise ValueError("o selo da referência interna não confere")
    actual_csv_sha = sha256_file(csv_path)
    if manifest.get("output", {}).get("sha256") != actual_csv_sha:
        raise ValueError("o arquivo da referência interna foi alterado")
    validation = validate_reference_csv(csv_path.read_text(encoding="utf-8-sig"))
    if validation["records"] != manifest.get("output", {}).get("records"):
        raise ValueError("a contagem da referência interna não confere")
    return manifest, csv_path, validation


def reference_status() -> dict[str, Any]:
    try:
        manifest, csv_path, validation = _verified_reference()
        result = {
            "ready": True,
            "reference_id": manifest["reference_id"],
            "created_at": manifest.get("created_at"),
            "source": manifest.get("source"),
            "output": manifest.get("output"),
            "validation": validation,
            "reference_file": str(csv_path.relative_to(ROOT)) if csv_path.is_relative_to(ROOT) else str(csv_path),
            "database_write": False,
        }
        try:
            source_path = discovered_source_path("dt870_updated")
            physical_sha = sha256_file(source_path)
            result["physical_source"] = {"file": source_path.name, "bytes": source_path.stat().st_size, "sha256": physical_sha}
            result["source_matches_current_reference"] = physical_sha == manifest.get("source", {}).get("sha256")
        except (FileNotFoundError, ValueError, OSError) as error:
            result["physical_source"] = None
            result["source_matches_current_reference"] = None
            result["physical_source_error"] = str(error)
        return result
    except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError) as error:
        return {"ready": False, "error": str(error), "database_write": False}


def _verified_metadata_reference() -> tuple[dict[str, Any], Path]:
    if not METADATA_REFERENCE_POINTER.is_file():
        raise FileNotFoundError("a referência interna de metadados ainda não foi instalada")
    pointer = json.loads(METADATA_REFERENCE_POINTER.read_text(encoding="utf-8-sig"))
    if pointer.get("contract") != METADATA_REFERENCE_POINTER_CONTRACT or not pointer.get("reference_id"):
        raise ValueError("o apontador da referência de metadados é inválido")
    version_dir = METADATA_REFERENCE_VERSIONS / str(pointer["reference_id"])
    manifest_path = version_dir / "manifesto.json"
    snapshot_path = version_dir / "snapshot.json"
    if not manifest_path.is_file() or not snapshot_path.is_file():
        raise FileNotFoundError("os arquivos da referência de metadados estão incompletos")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if manifest.get("contract") != METADATA_REFERENCE_CONTRACT:
        raise ValueError("o manifesto da referência de metadados é incompatível")
    sealed = dict(manifest)
    declared_manifest_sha = sealed.pop("manifest_sha256", "")
    actual_manifest_sha = sha256_json(sealed)
    if declared_manifest_sha != actual_manifest_sha or pointer.get("manifest_sha256") != actual_manifest_sha:
        raise ValueError("o selo da referência de metadados não confere")
    if manifest.get("snapshot", {}).get("sha256") != sha256_file(snapshot_path):
        raise ValueError("a fotografia interna de metadados foi alterada")
    return manifest, snapshot_path


def metadata_reference_status() -> dict[str, Any]:
    try:
        manifest, _ = _verified_metadata_reference()
        discovery = discover_sources()
        expected = manifest.get("source_identity") or {}
        current = {}
        changed_roles = []
        missing_roles = []
        for role, expected_item in expected.items():
            found = (discovery.get("sources") or {}).get(role) or {}
            if not found.get("found"):
                missing_roles.append(role)
                changed_roles.append(role)
                continue
            current_item = {
                "filename": found.get("filename"),
                "bytes": found.get("bytes"),
                "modified_at": found.get("modified_at"),
                "valid_container": found.get("valid_container"),
            }
            current[role] = current_item
            if current_item != expected_item:
                changed_roles.append(role)
        summary = manifest.get("summary") or {}
        totals = {
            "new": sum(int(item.get("new", 0)) for item in summary.values()),
            "changed": sum(int(item.get("changed", 0)) for item in summary.values()),
            "absent": sum(int(item.get("absent", 0)) for item in summary.values()),
        }
        return {
            "ready": True,
            "reference_id": manifest["reference_id"],
            "created_at": manifest.get("created_at"),
            "source_matches_current_reference": not changed_roles,
            "changed_roles": changed_roles,
            "missing_roles": missing_roles,
            "summary": summary,
            "totals": totals,
            "source_policy": manifest.get("source_policy"),
            "database_write": False,
        }
    except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError) as error:
        return {"ready": False, "error": str(error), "database_write": False}


def promote_reference(payload: dict[str, Any]) -> dict[str, Any]:
    csv_text = payload.get("csv")
    candidate = payload.get("manifest") or {}
    if not isinstance(csv_text, str) or not csv_text:
        raise ValueError("a nova carga integral não foi recebida")
    if candidate.get("database_write") is not False:
        raise ValueError("a promoção da referência deve declarar banco sem escrita")
    with REFERENCE_LOCK:
        current_manifest, current_csv_path, _ = _verified_reference()
        if payload.get("previous_reference_id") != current_manifest.get("reference_id"):
            raise ValueError("a referência mudou durante a validação; execute novamente")
        candidate_source = candidate.get("source") or {}
        try:
            source_path = discovered_source_path("dt870_updated")
            physical_source_sha = sha256_file(source_path)
            if candidate_source.get("sha256") != physical_source_sha:
                raise ValueError("a fonte física mudou durante a validação; execute novamente")
            source_name = source_path.name
            source_size = source_path.stat().st_size
        except FileNotFoundError:
            if candidate_source.get("origin") != "manual" or not candidate_source.get("validation"):
                raise ValueError("a fonte automática ficou indisponível; escolha somente a pasta do DT870 da atualização e tente novamente")
            physical_source_sha = str(candidate_source.get("sha256") or "")
            source_name = str(candidate_source.get("file") or "dt870_console_win.cpk")
            source_size = int(candidate_source.get("bytes") or 0)
            if len(physical_source_sha) != 64 or source_size <= 0:
                raise ValueError("a fonte escolhida manualmente não pôde ser comprovada")
        if physical_source_sha == current_manifest.get("source", {}).get("sha256"):
            return {"promoted": False, "reused": True, "reference": reference_status()}
        validation = validate_reference_csv(csv_text)
        csv_bytes = csv_text.encode("utf-8")
        csv_sha = hashlib.sha256(csv_bytes).hexdigest()
        declared_validation = candidate.get("validation") or {}
        if declared_validation.get("records") != validation["records"] or declared_validation.get("unique_card_ids") != validation["unique_card_ids"]:
            raise ValueError("a validação local não confere com a carga recebida")
        if candidate.get("extracted_csv_sha256") != csv_sha:
            raise ValueError("o selo da carga extraída não confere")
        comparison = candidate.get("comparison_to_previous") or {}
        required_counts = ("current", "new", "changed", "possibly_inactive")
        if any(not isinstance(comparison.get(key), int) or comparison[key] < 0 for key in required_counts):
            raise ValueError("o resumo de comparação da nova carga é inválido")
        if comparison["current"] != validation["records"]:
            raise ValueError("a contagem comparada não confere com a nova carga")
        verified_comparison = compare_reference_csv(csv_text, current_csv_path.read_text(encoding="utf-8-sig"))
        if any(comparison.get(key) != value for key, value in verified_comparison.items()):
            raise ValueError("o diff informado não confere com a comparação integral da referência anterior")
        reference_id = f"ref-{physical_source_sha[:12]}-{csv_sha[:12]}"
        final_dir = REFERENCE_VERSIONS / reference_id
        created_at = datetime.now(timezone.utc).isoformat()
        manifest = {
            "contract": REFERENCE_CONTRACT,
            "reference_id": reference_id,
            "created_at": created_at,
            "promoted_by": "validacao_automatica_local",
            "previous_reference_id": current_manifest.get("reference_id"),
            "database_write": False,
            "source": {"role": "dt870_updated", "file": source_name, "bytes": source_size, "sha256": physical_source_sha, "origin": candidate_source.get("origin", "automatic")},
            "output": {"file": "carta_jogo.csv", "bytes": len(csv_bytes), "records": validation["records"], "unique_card_ids": validation["unique_card_ids"], "sha256": csv_sha, "schema": CARD_COLUMNS},
            "validation": validation,
            "comparison_to_previous": verified_comparison,
            "client_manifest_sha256": candidate.get("manifest_sha256"),
        }
        manifest["manifest_sha256"] = sha256_json(manifest)
        REFERENCE_VERSIONS.mkdir(parents=True, exist_ok=True)
        if not final_dir.exists():
            staging = REFERENCE_VERSIONS / f".{reference_id}.{uuid.uuid4().hex}.tmp"
            staging.mkdir(parents=False)
            (staging / "carta_jogo.csv").write_bytes(csv_bytes)
            (staging / "manifesto.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            os.replace(staging, final_dir)
        pointer = {"contract": REFERENCE_POINTER_CONTRACT, "reference_id": reference_id, "manifest_sha256": manifest["manifest_sha256"], "updated_at": created_at}
        atomic_write_json(REFERENCE_POINTER, pointer)
        return {"promoted": True, "reused": False, "reference": reference_status(), "manifest": manifest}


def parse_iso(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def load_config() -> dict[str, Any]:
    path = CONFIG_LOCAL if CONFIG_LOCAL.exists() else CONFIG_EXAMPLE
    with path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    config["_source"] = path.name
    return config


def existing_project_url() -> str | None:
    candidates = []
    configured = os.environ.get("CLUBEF_PROJECT_CONFIG")
    if configured:
        candidates.append(Path(configured))
    candidates.extend([ROOT.parent / "config.txt", ROOT.parent / "2-MOTORES" / "config.txt"])
    for path in candidates:
        try:
            for line in path.read_text(encoding="utf-8-sig").splitlines():
                if line.startswith("SUPABASE_URL="):
                    value = line.split("=", 1)[1].strip()
                    if value.startswith("https://") and value.endswith(".supabase.co"):
                        return value
        except OSError:
            continue
    return None


def connection_string() -> str | None:
    explicit = os.environ.get("CLUBEF_SUPABASE_DB_URL")
    if explicit:
        return explicit
    password = os.environ.get("SUPABASE_DB_PASSWORD")
    project_url = existing_project_url()
    if password and project_url:
        project_ref = urlparse(project_url).hostname.split(".")[0]
        encoded = quote(password, safe="")
        return f"postgresql://postgres:{encoded}@db.{project_ref}.supabase.co:5432/postgres?sslmode=require&application_name=extrator_efootball"
    return None


def connection_source() -> str:
    if os.environ.get("CLUBEF_SUPABASE_DB_URL"):
        return "process_connection_string"
    if os.environ.get("SUPABASE_DB_PASSWORD") and existing_project_url():
        return "existing_project_config_and_user_environment"
    return "not_configured"


def write_is_enabled(config: dict[str, Any]) -> bool:
    return bool(config.get("write_enabled")) and os.environ.get("CLUBEF_ENABLE_REAL_WRITE") == "EU_AUTORIZO_ESCRITA_REAL"


def manual_card_apply_allowed(config: dict[str, Any]) -> bool:
    try:
        assert_card_target(config)
    except ValueError:
        return False
    return bool(config.get("allow_manual_card_apply")) and bool(connection_string())


def manual_text_apply_allowed(config: dict[str, Any]) -> bool:
    database = config.get("database") or {}
    adapter = (config.get("catalog_adapters") or {}).get("textos") or {}
    return (
        database.get("schema") == "clube_novo"
        and bool(config.get("allow_manual_text_apply"))
        and bool(adapter.get("enabled"))
        and bool(connection_string())
    )


def assert_card_target(config: dict[str, Any]) -> None:
    database = config.get("database") or {}
    if database.get("schema") != "clube_novo" or database.get("cards_table") != "carta_jogo":
        raise ValueError("destino bloqueado: este aplicativo só pode preparar cartas para clube_novo.carta_jogo; clube permanece intocado")


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
    if selection.get("kind") == "metadata" and selection.get("items") and all(item.get("catalog") == "textos" for item in selection["items"]):
        return {
            "automatic": False,
            "catalog": "textos",
            "inserted_keys_to_review_for_removal": [str(item.get("id")) for item in selection["items"] if item.get("action") in {"new", "insert"}],
            "rows_to_restore": [item.get("before") for item in selection["items"] if item.get("before")],
            "instruction": "gerar um pacote inverso, revisar as referências de catálogo e confirmar manualmente; nunca restaurar automaticamente",
        }
    if selection.get("kind") != "cards":
        return {"automatic": False, "reason": "catálogo sem adaptador de rollback específico"}
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


def fetch_all_card_rows(connection: Any, config: dict[str, Any]) -> dict[str, dict[str, str]]:
    _, sql, _ = import_psycopg()
    schema = config["database"]["schema"]
    table = config["database"]["cards_table"]
    query = sql.SQL("select {} from {}.{}").format(
        sql.SQL(",").join(sql.Identifier(column) for column in CARD_COLUMNS),
        sql.Identifier(schema),
        sql.Identifier(table),
    )
    with connection.cursor() as cursor:
        cursor.execute(query)
        return {
            str(values[0]): {column: normalize_csv_value(column, values[index]) for index, column in enumerate(CARD_COLUMNS)}
            for values in cursor.fetchall()
        }


def current_card_baseline(config: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    """Exporta a base atual do alvo em uma transação estritamente somente leitura."""
    assert_card_target(config)
    dsn = connection_string()
    if not dsn:
        raise RuntimeError("a conexão segura com clube_novo não está disponível")
    psycopg, _, _ = import_psycopg()
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        connection.read_only = True
        with connection.cursor() as cursor:
            cursor.execute("show transaction_read_only")
            if cursor.fetchone()[0] != "on":
                raise RuntimeError("a leitura da base atual não ficou protegida")
        rows = fetch_all_card_rows(connection, config)
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CARD_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for card_id in sorted(rows, key=lambda value: int(value)):
        writer.writerow(rows[card_id])
    data = ("\ufeff" + output.getvalue()).encode("utf-8")
    return data, {
        "source": "clube_novo.carta_jogo",
        "records": len(rows),
        "unique_card_ids": len(rows),
        "sha256": hashlib.sha256(data).hexdigest(),
        "transaction_read_only": True,
        "database_write": False,
        "preserved_schema": "clube",
    }


def current_text_baseline(config: dict[str, Any]) -> dict[str, Any]:
    """Lê o dicionário canônico atual sem abrir uma transação gravável."""
    schema = (config.get("database") or {}).get("schema")
    if schema != "clube_novo":
        raise ValueError("destino textual bloqueado: somente clube_novo.texto_do_jogo")
    dsn = connection_string()
    if not dsn:
        raise RuntimeError("a conexão segura com clube_novo não está disponível")
    psycopg, _, _ = import_psycopg()
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        connection.read_only = True
        with connection.cursor() as cursor:
            cursor.execute("show transaction_read_only")
            if cursor.fetchone()[0] != "on":
                raise RuntimeError("a leitura dos textos não ficou protegida")
        return text_baseline_snapshot(connection, schema)


def csv_rows_by_id(csv_text: str) -> dict[str, dict[str, str]]:
    reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff"), newline=""))
    return {
        str(row["card_id"]): {column: normalize_csv_value(column, row.get(column, "")) for column in CARD_COLUMNS}
        for row in reader
    }


def build_full_selection(desired_rows: dict[str, dict[str, str]], target_rows: dict[str, dict[str, str]]) -> tuple[dict[str, Any], list[str]]:
    items: list[dict[str, Any]] = []
    for card_id, desired in desired_rows.items():
        current = target_rows.get(card_id)
        if current is None:
            items.append({"action": "insert", "card_id": card_id, "row": desired})
            continue
        fields = [
            {"field": column, "before": current.get(column, ""), "after": normalize_csv_value(column, desired.get(column, ""))}
            for column in CARD_COLUMNS
            if column != "card_id" and normalize_csv_value(column, desired.get(column, "")) != current.get(column, "")
        ]
        if fields:
            items.append({"action": "update", "card_id": card_id, "row": desired, "fields": fields})
    inactive_ids = sorted(target_rows.keys() - desired_rows.keys(), key=int)
    return {"kind": "cards", "items": items}, inactive_ids


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
        if selection.get("kind") == "metadata" and selection.get("items") and all(item.get("catalog") == "textos" for item in selection["items"]):
            if not manual_text_apply_allowed(config):
                raise ValueError("o adaptador canônico de textos ainda não está habilitado")
            result = preflight_text_selection(connection, selection, "clube_novo")
            result["transaction_read_only"] = True
            return result
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
    assert_card_target(config)
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
    if selection.get("kind") == "metadata" and selection.get("items") and all(item.get("catalog") == "textos" for item in selection["items"]):
        if not manual_text_apply_allowed(config):
            raise PermissionError("aplicação manual de textos não está habilitada")
        psycopg, _, _ = import_psycopg()
        dsn = connection_string()
        if not dsn:
            raise RuntimeError("conexão do banco não configurada")
        with psycopg.connect(dsn, connect_timeout=20) as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    cursor.execute("set transaction isolation level serializable")
                    cursor.execute("set local statement_timeout = '180s'")
                    cursor.execute("select pg_advisory_xact_lock(hashtext(%s))", ("clubef_extractor:clube_novo.texto_do_jogo",))
                result = apply_text_selection(connection, selection, "clube_novo")
        with psycopg.connect(dsn, connect_timeout=20) as verification:
            verification.read_only = True
            readback = text_baseline_snapshot(verification, "clube_novo")
        result["post_commit_readback"] = {
            "records": readback["records"],
            "unique_official_keys": readback["unique_official_keys"],
            "sha256": readback["sha256"],
            "transaction_read_only": True,
        }
        return result
    raise ValueError("aplicação real de catálogo bloqueada: configure e teste um adaptador canônico específico")


def application_manifest(execution_id: str) -> dict[str, Any] | None:
    try:
        uuid.UUID(str(execution_id))
    except (ValueError, TypeError, AttributeError):
        return None
    path = ARTIFACTS / f"APLICACAO-{execution_id}.json"
    if not path.is_file():
        return None
    try:
        manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    if manifest.get("execution_id") != execution_id or manifest.get("target", {}).get("schema") != "clube_novo":
        return None
    return manifest


class ApprovalStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._items: dict[str, dict[str, Any]] = {}
        self._executions: dict[str, dict[str, Any]] = {}

    def create(self, manifest: dict[str, Any], selection: dict[str, Any], summary: dict[str, int], preflight: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        execution_id = manifest["execution_id"]
        selection_sha256 = sha256_json(selection)
        with self._lock:
            persisted = application_manifest(execution_id)
            if persisted:
                if persisted.get("selection_sha256") != selection_sha256:
                    raise ValueError("esta execução já foi aplicada com outro conteúdo")
                raise ValueError("esta execução já foi aplicada e conferida")
            existing = self._executions.get(execution_id)
            if existing and existing.get("state") in {"ready", "applying"}:
                existing_item = self._items.get(existing.get("token"))
                if existing_item and existing_item.get("selection_sha256") == selection_sha256 and time.time() < existing_item["expires_at"]:
                    return {"token": existing["token"], "phrase": existing_item["confirmation_phrase"], "reused": True}
            token = secrets.token_urlsafe(32)
            phrase = f"APLICAR {execution_id[-8:].upper()}"
            self._items[token] = {
                "manifest": manifest,
                "selection": selection,
                "selection_sha256": selection_sha256,
                "summary": summary,
                "preflight": preflight,
                "confirmation_phrase": phrase,
                "expires_at": time.time() + int(config.get("approval_ttl_minutes", 10)) * 60,
            }
            self._executions[execution_id] = {"state": "ready", "token": token, "updated_at": time.time()}
            return {"token": token, "phrase": phrase, "reused": False}

    def begin(self, token: str, confirmation: str, request_id: str) -> dict[str, Any]:
        with self._lock:
            item = self._items.get(token)
            if not item:
                raise ValueError("aprovação inexistente ou já consumida")
            if time.time() >= item["expires_at"]:
                raise ValueError("aprovação expirada")
            if not secrets.compare_digest(confirmation, item["confirmation_phrase"]):
                raise ValueError("frase de confirmação incorreta")
            execution_id = item["manifest"]["execution_id"]
            if request_id != execution_id:
                raise ValueError("identificador desta aplicação não corresponde ao pacote selado")
            persisted = application_manifest(execution_id)
            if persisted:
                if persisted.get("selection_sha256") != item["selection_sha256"]:
                    raise ValueError("execução já registrada com outro conteúdo")
                return {"state": "completed", "response": {"application_manifest": persisted, "idempotent_reuse": True}}
            current = self._executions.get(execution_id) or {}
            if current.get("state") == "applying":
                return {"state": "applying", "execution_id": execution_id}
            if current.get("state") == "completed" and current.get("response"):
                return {"state": "completed", "response": current["response"]}
            self._executions[execution_id] = {"state": "applying", "token": token, "updated_at": time.time()}
            return {"state": "start", "item": item, "execution_id": execution_id}

    def complete(self, execution_id: str, response: dict[str, Any]) -> None:
        with self._lock:
            current = self._executions.get(execution_id) or {}
            self._executions[execution_id] = {**current, "state": "completed", "response": response, "updated_at": time.time()}

    def fail(self, execution_id: str, error: str) -> None:
        with self._lock:
            current = self._executions.get(execution_id) or {}
            self._executions[execution_id] = {**current, "state": "failed", "error": error, "updated_at": time.time()}

    def status(self, execution_id: str) -> dict[str, Any]:
        with self._lock:
            persisted = application_manifest(execution_id)
            if persisted:
                return {"state": "completed", "application_manifest": persisted, "idempotent": True}
            current = self._executions.get(execution_id)
            if not current:
                return {"state": "unknown"}
            return {key: value for key, value in current.items() if key not in {"token", "response"}}


APPROVALS = ApprovalStore()


def save_manifest(prefix: str, manifest: dict[str, Any]) -> Path:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    final = ARTIFACTS / f"{prefix}-{manifest['execution_id']}.json"
    temporary = final.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    temporary.replace(final)
    return final


def prepare_card_package(payload: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    assert_card_target(config)
    manifest = payload.get("manifest") or {}
    package = payload.get("package") or {}
    validate_manifest(manifest, config)
    package_type = str(package.get("type") or "")
    if package_type not in {"incremental", "full"}:
        raise ValueError("tipo de carga validada desconhecido")

    if package_type == "incremental":
        if manifest.get("mode") != "card_diff":
            raise ValueError("o pacote incremental não corresponde ao manifesto validado")
        selection = {"kind": "cards", "items": package.get("items") or []}
        summary = selected_summary(selection)
        validate_selection_counts(manifest, summary)
        expected = {
            "insert": int((manifest.get("counts") or {}).get("new", 0)),
            "update": int((manifest.get("counts") or {}).get("changed", 0)),
            "inactive": int((manifest.get("counts") or {}).get("possibly_inactive", 0)),
        }
        if summary != expected:
            raise ValueError("o pacote incremental deve conter integralmente o diff validado")
        validate_selection_contract(manifest, selection)
        approval_manifest = manifest
    else:
        if manifest.get("mode") != "card_full":
            raise ValueError("a recarga integral não corresponde ao manifesto validado")
        reference_manifest, reference_csv_path, validation = _verified_reference()
        if package.get("reference_id") != reference_manifest.get("reference_id") or manifest.get("reference_id") != reference_manifest.get("reference_id"):
            raise ValueError("a referência integral mudou; valide a carga novamente")
        expected_csv_sha = reference_manifest.get("output", {}).get("sha256")
        if package.get("reference_csv_sha256") != expected_csv_sha or manifest.get("reference_csv_sha256") != expected_csv_sha:
            raise ValueError("o pacote integral não corresponde à referência selada")
        if int(package.get("records") or 0) != validation["records"]:
            raise ValueError("a contagem do pacote integral não confere")
        dsn = connection_string()
        if not dsn:
            raise RuntimeError("o banco ainda não foi configurado no executor local; nenhuma escrita foi liberada")
        psycopg, _, _ = import_psycopg()
        with psycopg.connect(dsn, connect_timeout=20) as connection:
            connection.read_only = True
            with connection.cursor() as cursor:
                cursor.execute("show transaction_read_only")
                if cursor.fetchone()[0] != "on":
                    raise RuntimeError("o pré-voo não ficou em modo somente leitura")
            target_rows = fetch_all_card_rows(connection, config)
        desired_rows = csv_rows_by_id(reference_csv_path.read_text(encoding="utf-8-sig"))
        selection, inactive_ids = build_full_selection(desired_rows, target_rows)
        if inactive_ids:
            raise ValueError(f"carga bloqueada: {len(inactive_ids)} carta(s) do clube_novo ficaram ausentes e carta_jogo não possui inativação canônica segura")
        summary = selected_summary(selection) if selection["items"] else {"insert": 0, "update": 0, "inactive": 0}
        derived = {
            "contract": CONTRACT,
            "mode": "card_diff",
            "execution_id": manifest["execution_id"],
            "generated_at": manifest["generated_at"],
            "expires_at": manifest["expires_at"],
            "database_write": False,
            "source_package": {"type": "full", "manifest_sha256": manifest["manifest_sha256"], "reference_id": reference_manifest["reference_id"], "reference_csv_sha256": expected_csv_sha},
            "counts": {"current": validation["records"], "new": summary["insert"], "changed": summary["update"], "possibly_inactive": 0},
            "selection_contract": {"algorithm": "sha256/canonical-json", "items": [{"key": selection_item_key(item, "cards"), "sha256": sha256_json(normalized_selection_item(item, "cards"))} for item in selection["items"]]},
        }
        derived["manifest_sha256"] = sha256_json(derived)
        approval_manifest = derived
        if selection["items"]:
            validate_selection_contract(approval_manifest, selection)

    if len(selection["items"]) > int(config.get("max_selected_items", 50000)):
        raise ValueError("o pacote excede o limite configurado")
    preflight = readonly_preflight(selection, config) if selection["items"] else {"database_checked": True, "transaction_read_only": True, "ready": 0, "already_applied": 0}
    target = {"schema": "clube_novo", "table": "carta_jogo", "display": "clube_novo.carta_jogo", "preserved_schema": "clube"}
    if not selection["items"]:
        return {"no_changes": True, "execution_id": approval_manifest["execution_id"], "package_type": package_type, "summary": summary, "preflight": preflight, "target": target, "write_enabled": False}
    approval = APPROVALS.create(approval_manifest, selection, summary, preflight, config)
    dry_run_manifest = {
        "contract": "clubef-card-package-dry-run-v1",
        "execution_id": approval_manifest["execution_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_manifest_sha256": manifest["manifest_sha256"],
        "approval_manifest_sha256": approval_manifest["manifest_sha256"],
        "selection_sha256": sha256_json(selection),
        "package_type": package_type,
        "summary": summary,
        "target": target,
        "preflight": preflight,
        "recovery_plan": recovery_plan(selection),
        "database_write": False,
        "result": "ready_for_final_confirmation" if manual_card_apply_allowed(config) else "dry_run_only",
    }
    save_manifest("DRY-RUN-CARGA-CARTAS", dry_run_manifest)
    return {
        "approval_token": approval["token"],
        "confirmation_phrase": approval["phrase"],
        "execution_id": approval_manifest["execution_id"],
        "package_type": package_type,
        "summary": summary,
        "preflight": preflight,
        "target": target,
        "mode": "manual-confirmation" if manual_card_apply_allowed(config) else "dry-run",
        "write_enabled": manual_card_apply_allowed(config),
        "dry_run_manifest": dry_run_manifest,
    }


class Handler(SimpleHTTPRequestHandler):
    server_version = "ClubEfootballLocal/4"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        super().end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        if sys.stdout is not None:
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
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            config = load_config()
            card_apply = manual_card_apply_allowed(config)
            text_apply = manual_text_apply_allowed(config)
            self.send_json(HTTPStatus.OK, {
                "online": True,
                "mode": "manual-confirmation" if (card_apply or text_apply) else "dry-run",
                "write_enabled": False,
                "manual_apply_available": card_apply or text_apply,
                "manual_card_apply_available": card_apply,
                "manual_text_apply_available": text_apply,
                "database_configured": bool(connection_string()),
                "connection_source": connection_source(),
                "targets": ["clube_novo.carta_jogo", "clube_novo.texto_do_jogo"],
                "config_source": config["_source"],
            })
            return
        if parsed.path == "/api/sources/status":
            self.send_json(HTTPStatus.OK, discover_sources())
            return
        if parsed.path == "/api/sources/file":
            role = (parse_qs(parsed.query).get("role") or [""])[0]
            try:
                source_path = discovered_source_path(role)
                size = source_path.stat().st_size
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(size))
                self.send_header("Content-Disposition", f'attachment; filename="{source_path.name}"')
                self.end_headers()
                with source_path.open("rb") as handle:
                    while chunk := handle.read(1024 * 1024):
                        self.wfile.write(chunk)
            except (ValueError, FileNotFoundError) as error:
                self.send_json(HTTPStatus.NOT_FOUND, {"error": str(error)})
            return
        if parsed.path == "/api/card-reference/status":
            status = reference_status()
            self.send_json(HTTPStatus.OK if status.get("ready") else HTTPStatus.CONFLICT, status)
            return
        if parsed.path == "/api/metadata-reference/status":
            status = metadata_reference_status()
            self.send_json(HTTPStatus.OK if status.get("ready") else HTTPStatus.CONFLICT, status)
            return
        if parsed.path == "/api/apply/status":
            execution_id = (parse_qs(parsed.query).get("execution_id") or [""])[0]
            if not execution_id:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": "identificador da execução ausente"})
                return
            self.send_json(HTTPStatus.OK, APPROVALS.status(execution_id))
            return
        if parsed.path == "/api/card-reference/current.csv":
            try:
                _, csv_path, _ = _verified_reference()
                size = csv_path.stat().st_size
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Length", str(size))
                self.end_headers()
                with csv_path.open("rb") as handle:
                    while chunk := handle.read(1024 * 1024):
                        self.wfile.write(chunk)
            except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError) as error:
                self.send_json(HTTPStatus.CONFLICT, {"error": str(error)})
            return
        if parsed.path == "/api/card-baseline/current.csv":
            try:
                config = load_config()
                data, details = current_card_baseline(config)
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("X-Clubef-Records", str(details["records"]))
                self.send_header("X-Clubef-Sha256", details["sha256"])
                self.send_header("X-Clubef-Read-Only", "true")
                self.end_headers()
                self.wfile.write(data)
            except (RuntimeError, ValueError, OSError) as error:
                self.send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": str(error)})
            return
        if parsed.path == "/api/text-baseline/current.json":
            try:
                config = load_config()
                self.send_json(HTTPStatus.OK, current_text_baseline(config))
            except (RuntimeError, ValueError, OSError) as error:
                self.send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": str(error), "database_write": False})
            return
        if self.path in {"/", ""}:
            self.path = "/Extrator-ClubEfootball.html"
        super().do_GET()

    def do_POST(self) -> None:
        try:
            path = urlparse(self.path).path
            config = load_config()
            if path == "/api/card-reference/promote":
                result = promote_reference(self.read_json())
                self.send_json(HTTPStatus.OK, result)
                return
            if path == "/api/card-package/prepare":
                result = prepare_card_package(self.read_json(), config)
                self.send_json(HTTPStatus.OK, result)
                return
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
                text_package = selection.get("kind") == "metadata" and selection.get("items") and all(item.get("catalog") == "textos" for item in selection["items"])
                if text_package:
                    expected = {
                        "insert": int((manifest.get("counts") or {}).get("new", 0)),
                        "update": int((manifest.get("counts") or {}).get("changed", 0)),
                        "inactive": int((manifest.get("counts") or {}).get("possibly_inactive", 0)),
                    }
                    if summary != expected:
                        raise ValueError("o pacote textual deve conter integralmente todas as diferenças seguras desta execução")
                can_write = manual_text_apply_allowed(config) if text_package else write_is_enabled(config)
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
                    "result": "ready_for_final_confirmation" if can_write else "dry_run_only",
                }
                save_manifest("DRY-RUN", dry_run_manifest)
                self.send_json(HTTPStatus.OK, {
                    "approval_token": approval["token"],
                    "confirmation_phrase": approval["phrase"],
                    "summary": summary,
                    "preflight": preflight,
                    "mode": "write-enabled" if can_write else "dry-run",
                    "write_enabled": can_write,
                    "dry_run_manifest": dry_run_manifest,
                })
                return
            if path == "/api/apply":
                if not (manual_card_apply_allowed(config) or manual_text_apply_allowed(config)):
                    raise PermissionError("envio manual bloqueado: conexão segura ou permissão local indisponível")
                payload = self.read_json()
                request_id = str(payload.get("request_id", ""))
                decision = APPROVALS.begin(str(payload.get("approval_token", "")), str(payload.get("confirmation", "")), request_id)
                if decision["state"] == "completed":
                    self.send_json(HTTPStatus.OK, decision["response"])
                    return
                if decision["state"] == "applying":
                    self.send_json(HTTPStatus.ACCEPTED, {"state": "applying", "execution_id": decision["execution_id"], "message": "esta carga já está sendo aplicada; aguarde o resultado"})
                    return
                approved = decision["item"]
                execution_id = decision["execution_id"]
                try:
                    selection_kind = approved.get("selection", {}).get("kind")
                    if selection_kind == "cards":
                        assert_card_target(config)
                    elif not (selection_kind == "metadata" and approved.get("selection", {}).get("items") and all(item.get("catalog") == "textos" for item in approved["selection"]["items"])):
                        raise PermissionError("somente pacotes validados de cartas ou textos canônicos podem usar o envio manual")
                    validate_manifest(approved["manifest"], config)
                    result = apply_selection(approved["selection"], config)
                    target_table = "carta_jogo" if selection_kind == "cards" else "texto_do_jogo"
                    application_manifest = {
                        "contract": "clubef-application-manifest-v1",
                        "execution_id": execution_id,
                        "applied_at": datetime.now(timezone.utc).isoformat(),
                        "source_manifest_sha256": approved["manifest"]["manifest_sha256"],
                        "selection_sha256": approved["selection_sha256"],
                        "summary": approved["summary"],
                        "target": {"schema": "clube_novo", "table": target_table, "preserved_schema": "clube"},
                        "selected_items": approved["selection"]["items"],
                        "preflight": approved["preflight"],
                        "recovery_plan": recovery_plan(approved["selection"]),
                        "result": result,
                        "database_write": True,
                        "idempotent_keys": "execution_id + selection_sha256 + card_id/chave canônica",
                        "transaction": "serializable_fail_closed",
                        "readback": True,
                    }
                    save_manifest("APLICACAO", application_manifest)
                    response = {"application_manifest": application_manifest, "idempotent_reuse": False}
                    APPROVALS.complete(execution_id, response)
                    self.send_json(HTTPStatus.OK, response)
                except Exception as error:
                    APPROVALS.fail(execution_id, str(error))
                    raise
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
    if sys.stdout is not None:
        print(f"Extrator eFootball disponível em {url}")
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
