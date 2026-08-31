"""Coordenador sem interface do Extrator Desktop.

O processo recebe o pedido de leitura do banco em transação read-only, chama o
leitor físico isolado e compara cada família sem permitir qualquer aplicação.
Ele fala JSONL somente com a janela WinForms; não inicia HTTP nem navegador.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

import executor_local as runtime
import review_html
import card_completeness
import motor_protection_installer
import motor_protection_seed


DESKTOP_WORKER_PROTOCOL_VERSION = "5.3.0"


def _safe_database_connection_error(error: Exception) -> str:
    """Traduz a falha sem devolver DSN, senha, usuário ou endereço ao launcher."""
    lowered = str(error).lower()
    if "password authentication failed" in lowered or "authentication failed" in lowered:
        return (
            "A senha do banco foi recusada. No Supabase, abra Connect, copie novamente "
            "a connection string completa e confirme que ela já contém a senha atual."
        )
    if "timeout" in lowered or "timed out" in lowered:
        return (
            "O banco não respondeu dentro do tempo esperado. Verifique a internet e, "
            "se sua rede for somente IPv4, copie no Supabase a opção Session pooler."
        )
    if "name or service not known" in lowered or "getaddrinfo" in lowered or "could not translate host" in lowered:
        return (
            "O endereço do banco não pôde ser encontrado. Copie novamente a connection "
            "string pelo botão Connect do projeto no Supabase."
        )
    if "connection refused" in lowered or "could not connect" in lowered or "network is unreachable" in lowered:
        return (
            "Não foi possível alcançar o banco. Verifique a internet e use a connection "
            "string Session pooler quando a conexão direta não funcionar nesta rede."
        )
    if "ssl" in lowered or "certificate" in lowered:
        return (
            "A conexão segura SSL foi recusada. Copie uma connection string atual pelo "
            "botão Connect do Supabase e tente novamente."
        )
    return (
        "O banco recusou o teste de conexão. A credencial não foi exibida nem salva. "
        "Copie novamente a connection string pelo botão Connect do Supabase."
    )


def emit(event_type: str, **payload: Any) -> None:
    print(json.dumps({"type": event_type, "at": datetime.now(timezone.utc).isoformat(), **payload}, ensure_ascii=False), flush=True)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_compact_json(path: Path, payload: Any) -> None:
    """Grava JSON grande sem criar uma segunda cópia integral em memória."""
    temporary = path.with_name(path.name + ".novo")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as stream:
            json.dump(payload, stream, ensure_ascii=False, separators=(",", ":"))
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _windows_launcher_is_ancestor(expected_pid: int, expected_executable: Path) -> bool:
    """Confirma que este worker nasceu do EXE operacional, inclusive via py.exe."""
    if os.name != "nt":
        return False
    import ctypes
    from ctypes import wintypes

    class ProcessEntry32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * 260),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.argtypes = (wintypes.DWORD, wintypes.DWORD)
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Process32FirstW.argtypes = (wintypes.HANDLE, ctypes.POINTER(ProcessEntry32W))
    kernel32.Process32FirstW.restype = wintypes.BOOL
    kernel32.Process32NextW.argtypes = (wintypes.HANDLE, ctypes.POINTER(ProcessEntry32W))
    kernel32.Process32NextW.restype = wintypes.BOOL
    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = (
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    )
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL

    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    invalid_handle = ctypes.c_void_p(-1).value
    if snapshot == invalid_handle:
        return False
    parents: dict[int, int] = {}
    try:
        entry = ProcessEntry32W()
        entry.dwSize = ctypes.sizeof(entry)
        ok = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while ok:
            parents[int(entry.th32ProcessID)] = int(entry.th32ParentProcessID)
            ok = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)

    current_pid = os.getpid()
    for _depth in range(4):
        parent_pid = parents.get(current_pid, 0)
        if parent_pid <= 0:
            return False
        if parent_pid == expected_pid:
            handle = kernel32.OpenProcess(0x1000, False, parent_pid)
            if not handle:
                return False
            try:
                buffer = ctypes.create_unicode_buffer(32768)
                size = wintypes.DWORD(len(buffer))
                if not kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                    return False
                observed = Path(buffer.value)
                return os.path.normcase(os.path.abspath(observed)) == os.path.normcase(
                    os.path.abspath(expected_executable)
                )
            finally:
                kernel32.CloseHandle(handle)
        current_pid = parent_pid
    return False


def consume_operator_write_authorization(
    root: Path,
    run_dir: Path,
    manifest_path: Path,
    confirmation_sha256: str,
    authorization_path: str | None,
) -> dict[str, str]:
    """Consome uma autorização curta criada pelo clique no EXE desktop."""
    if not authorization_path:
        raise RuntimeError("a instalação exige a confirmação criada pela janela do Extrator")
    candidate = Path(os.path.abspath(authorization_path))
    if candidate.parent.resolve() != run_dir.resolve() or not candidate.name.startswith(
        "autorizacao-protecao-motores-"
    ) or candidate.suffix.lower() != ".json":
        raise RuntimeError("a autorização da janela não pertence a esta execução")
    try:
        stat = candidate.stat(follow_symlinks=False)
    except OSError as error:
        raise RuntimeError("a autorização da janela não existe mais") from error
    if (
        not candidate.is_file()
        or candidate.is_symlink()
        or bool(getattr(stat, "st_file_attributes", 0) & 0x400)
        or stat.st_size <= 0
        or stat.st_size > 65536
    ):
        raise RuntimeError("a autorização da janela não é um arquivo local íntegro")
    consumed = candidate.with_name(candidate.stem + ".consumida.json")
    if consumed.exists():
        raise RuntimeError("a autorização da janela já foi consumida")
    os.replace(candidate, consumed)
    raw = consumed.read_bytes()
    try:
        envelope = json.loads(raw.decode("utf-8-sig"))
    except Exception as error:
        raise RuntimeError("a autorização da janela está inválida") from error
    expected_keys = {
        "schema",
        "action",
        "protocol_version",
        "manifest_path",
        "confirmation_sha256",
        "launcher_pid",
        "launcher_executable",
        "issued_at",
        "expires_at",
        "nonce",
        "database_write_authorized",
    }
    if not isinstance(envelope, dict) or set(envelope) != expected_keys:
        raise RuntimeError("a autorização da janela tem formato incompatível")
    launcher_executable = (root / "Extrator eFootball.exe").resolve()
    try:
        issued = datetime.fromisoformat(str(envelope["issued_at"]).replace("Z", "+00:00"))
        expires = datetime.fromisoformat(str(envelope["expires_at"]).replace("Z", "+00:00"))
    except Exception as error:
        raise RuntimeError("a autorização da janela não contém prazo válido") from error
    now = datetime.now(timezone.utc)
    launcher_pid = envelope.get("launcher_pid")
    valid = (
        envelope.get("schema") == "clubef-autorizacao-escrita-ui-v1"
        and envelope.get("action") == "install_motor_protection"
        and envelope.get("protocol_version") == DESKTOP_WORKER_PROTOCOL_VERSION
        and Path(str(envelope.get("manifest_path") or "")).resolve() == manifest_path.resolve()
        and envelope.get("confirmation_sha256") == confirmation_sha256
        and envelope.get("database_write_authorized") is True
        and isinstance(launcher_pid, int)
        and not isinstance(launcher_pid, bool)
        and str(envelope.get("launcher_executable") or "") == str(launcher_executable)
        and re.fullmatch(r"[0-9a-f]{64}", str(envelope.get("nonce") or "")) is not None
        and issued.tzinfo is not None
        and expires.tzinfo is not None
        and now - timedelta(minutes=10) <= issued <= now + timedelta(minutes=1)
        and now < expires <= now + timedelta(minutes=10)
        and expires > issued
    )
    if not valid or not _windows_launcher_is_ancestor(int(launcher_pid or 0), launcher_executable):
        raise RuntimeError("a instalação não veio da confirmação atual da janela do Extrator")
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "consumed_path": str(consumed),
    }


def iter_json_array_file(path: Path, *, chunk_size: int = 1024 * 1024) -> Iterator[Any]:
    """Lê um array JSON de qualquer tamanho mantendo só um item por vez.

    O artefato de cartas passa de 150 MB numa rodada normal. ``json.load``
    multiplicava esse volume em objetos Python antes mesmo de criar a revisão.
    Este leitor incremental preserva o mesmo contrato JSON sem depender de
    biblioteca externa e falha fechado diante de lixo, truncamento ou cauda.
    """
    decoder = json.JSONDecoder()
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        buffer = ""
        cursor = 0
        eof = False

        def refill() -> bool:
            nonlocal buffer, cursor, eof
            if eof:
                return False
            if cursor:
                buffer = buffer[cursor:]
                cursor = 0
            chunk = stream.read(chunk_size)
            if not chunk:
                eof = True
                return False
            buffer += chunk
            return True

        def skip_space() -> None:
            nonlocal cursor
            while True:
                while cursor < len(buffer) and buffer[cursor].isspace():
                    cursor += 1
                if cursor < len(buffer) or not refill():
                    return

        refill()
        skip_space()
        if cursor >= len(buffer) or buffer[cursor] != "[":
            raise ValueError(f"artefato não contém array JSON: {path.name}")
        cursor += 1
        expect_value = True
        while True:
            skip_space()
            if cursor >= len(buffer):
                raise ValueError(f"array JSON truncado: {path.name}")
            if buffer[cursor] == "]":
                cursor += 1
                break
            if not expect_value:
                if buffer[cursor] != ",":
                    raise ValueError(f"separador inválido no array JSON: {path.name}")
                cursor += 1
                skip_space()
            while True:
                try:
                    value, end = decoder.raw_decode(buffer, cursor)
                    cursor = end
                    break
                except json.JSONDecodeError as error:
                    if not refill():
                        raise ValueError(f"item JSON truncado ou inválido em {path.name}: {error}") from error
            yield value
            expect_value = False
        skip_space()
        if cursor < len(buffer):
            raise ValueError(f"conteúdo inesperado após o array JSON: {path.name}")


def cancelled(path: Path) -> None:
    if path.exists():
        raise RuntimeError("cancelled_by_user")


def find_node() -> str | None:
    candidates = [
        Path(os.environ.get("CLUBEF_NODE", "")),
        Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "bin" / "node.exe",
    ]
    for candidate in candidates:
        if str(candidate) and candidate.is_file():
            return str(candidate)
    return "node"  # deixa o Windows localizar um Node instalado pelo usuário.


def sources(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    discovered: dict[str, dict[str, Any]] = {}
    for role, definition in runtime.contract_source_definitions(contract).items():
        item = runtime.inspect_source(role, definition)
        if item.get("found"):
            item["sha256"] = None  # o hash físico é conferido pelo contrato no leitor.
        discovered[role] = item
    return discovered


def summarize(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "database_write": False,
        "counts": value.get("counts") or value.get("comparisons") or value.get("summary") or {},
        "classification_complete": bool(value.get("classification_complete", False)),
        "technical_integrity": bool(value.get("technical_integrity", not bool(value.get("error")))),
        "exact_match": value.get("exact_match"),
        "error": value.get("error"),
    }


def compare_family(name: str, action: Callable[[], dict[str, Any]], result: dict[str, Any], contract_key: str, check_key: str) -> None:
    contract_families = result.setdefault("contract_families", {})
    contract_family = contract_families.setdefault(contract_key, {"physical_state": "not_started", "comparison_checks": {}, "database_write": False})
    checks = contract_family.setdefault("comparison_checks", {})
    emit("family", family=name, state="running", message="Comparação com clube_novo em transação somente leitura.")
    try:
        value = action()
        result["comparisons"][name] = summarize(value)
        result.setdefault("comparison_reports", {})[f"{contract_key}:{check_key}"] = value
        # Validadores ainda em transição podem expor apenas ``passed``. Esse
        # campo antigo mistura igualdade de conteúdo com erro; não o usamos
        # para decidir integridade. Falta de classificação mantém o gate
        # fechado, mas não inventa uma rejeição a partir de contagem.
        technical_integrity = bool(value.get("technical_integrity", not bool(value.get("error"))))
        classification_complete = bool(value.get("classification_complete", False))
        unresolved_pending_count = int(value.get("unresolved_pending_count") or 0)
        state = (
            "technical_issue"
            if not technical_integrity
            else "review"
            if unresolved_pending_count or (classification_complete and value.get("exact_match") is not True)
            else "observed"
        )
        result["families"][name] = {"state": state, "database_write": False}
        checks[check_key] = {
            "completed": True,
            "classification_complete": classification_complete,
            "technical_integrity": technical_integrity,
            "application_eligible": value.get("application_eligible", True),
            "application_blockers": value.get("application_blockers", []),
            "unresolved_pending_count": unresolved_pending_count,
            "database_write": False,
        }
        emit("family", family=name, state=state, message="Conferido por chave/procedência; nenhuma escrita foi feita.")
    except Exception as error:  # Uma família nunca impede a comparação das próximas.
        message = str(error)
        result["comparisons"][name] = {"database_write": False, "error": message}
        result["families"][name] = {"state": "error", "database_write": False, "error": message}
        checks[check_key] = {"completed": False, "classification_complete": False, "technical_integrity": False, "database_write": False, "error": message}
        emit("family", family=name, state="error", message=message)


def _canonical_value(value: Any, expected_type: str) -> str | None:
    if value is None or value == "":
        return None
    if expected_type == "integer":
        return str(int(value))
    if expected_type == "boolean":
        if isinstance(value, bool):
            return "true" if value else "false"
        parsed = str(value).strip().lower()
        if parsed in ("true", "1"): return "true"
        if parsed in ("false", "0"): return "false"
        raise ValueError(f"booleano inválido: {value!r}")
    return str(value)


def classify_canonical_cards(cards_path: Path, dimensions_path: Path, baseline_path: Path, contract: dict[str, Any]) -> dict[str, Any]:
    """Compara Cartas por card_id e pelos campos físicos declarados pelo banco.

    ``box``, título e rótulos de catálogos não são lidos aqui: pertencem à
    apresentação. A projeção que liga artefato físico a coluna de carta vem do
    pedido selado, portanto não há mapa alternativo em Python.
    """
    buckets: dict[str, list[dict[str, Any]]] = {kind: [] for kind in ("new", "removed", "altered", "repeated", "invalid")}
    projections = contract.get("projecoes_cartas")
    if not isinstance(projections, list) or not projections:
        raise RuntimeError("pedido do banco sem projeções canônicas de cartas")
    with cards_path.open("r", encoding="utf-8-sig", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    with baseline_path.open("r", encoding="utf-8-sig", newline="") as handle:
        baseline_rows = list(csv.DictReader(handle))
    dimensions = json.loads(dimensions_path.read_text(encoding="utf-8"))
    dimension_rows = dimensions.get("cards") if isinstance(dimensions, dict) else None
    if not isinstance(dimension_rows, list):
        raise RuntimeError("fotografia de dimensões sem lista física de cartas")

    def index(rows: list[dict[str, Any]], artifact: str) -> dict[str, dict[str, Any]]:
        indexed: dict[str, dict[str, Any]] = {}
        for row in rows:
            card_id = str(row.get("card_id") or "")
            if not card_id:
                buckets["invalid"].append({"classificacao": "inválido", "escopo": "cartas", "motivo": f"{artifact} sem card_id", "fonte_fisica": {"artefato": artifact}})
            elif card_id in indexed:
                buckets["repeated"].append({"classificacao": "repetido", "escopo": "cartas", "chave_canonica": {"card_id": card_id}, "fonte_fisica": {"artefato": artifact, "card_id": card_id}})
            else:
                indexed[card_id] = row
        return indexed

    sources = {"cartas_fisicas": index(csv_rows, "cartas-fisicas.csv"), "dimensoes_fisicas": index(dimension_rows, "dimensoes-fisicas.json"), "banco": index(baseline_rows, "clube_novo.carta_jogo")}
    physical_ids = set(sources["cartas_fisicas"]) | set(sources["dimensoes_fisicas"])
    database_ids = set(sources["banco"])

    def physical_projection(card_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        values: dict[str, Any] = {"card_id": card_id}
        provenance: dict[str, Any] = {}
        seen_targets: set[tuple[str, str]] = set()
        for projection in projections:
            if not isinstance(projection, dict):
                raise RuntimeError("projeção de carta inválida no pedido")
            artifact, source_column = projection.get("artefato_fisico"), projection.get("coluna_fisica")
            target, expected_type = projection.get("destino_coluna"), projection.get("tipo_valor")
            if artifact not in ("cartas_fisicas", "dimensoes_fisicas") or not all(isinstance(value, str) and value for value in (source_column, target, expected_type)):
                raise RuntimeError("projeção do pedido incompleta")
            source = sources[artifact].get(card_id)
            if source is None or source_column not in source:
                raise RuntimeError(f"campo físico solicitado ausente: {artifact}.{source_column}")
            target_key = (str(artifact), target)
            if target_key in seen_targets:
                continue
            seen_targets.add(target_key)
            values[target] = _canonical_value(source.get(source_column), expected_type)
            provenance[target] = projection.get("proveniencia")
        return values, provenance

    for card_id in sorted(physical_ids - database_ids, key=int):
        try:
            values, provenance = physical_projection(card_id)
            buckets["new"].append({"classificacao": "novo", "escopo": "cartas", "destino_tabela": "carta_jogo", "chave_canonica": {"card_id": card_id}, "fonte_fisica": {"card_id": card_id, "campos": provenance}, "valor_fisico": values})
        except Exception as error:
            buckets["invalid"].append({"classificacao": "inválido", "escopo": "cartas", "chave_canonica": {"card_id": card_id}, "motivo": str(error)})
    for card_id in sorted(database_ids - physical_ids, key=int):
        buckets["removed"].append({"classificacao": "removido", "escopo": "cartas", "chave_canonica": {"card_id": card_id}, "vinculo_banco": {"card_id": card_id}})

    for card_id in sorted(physical_ids & database_ids, key=int):
        changed: list[dict[str, Any]] = []
        seen_targets: set[tuple[str, str]] = set()
        for projection in projections:
            if not isinstance(projection, dict):
                buckets["invalid"].append({"classificacao": "inválido", "escopo": "cartas", "motivo": "projeção de carta inválida no pedido"})
                continue
            artifact, source_column = projection.get("artefato_fisico"), projection.get("coluna_fisica")
            target = projection.get("destino_coluna")
            expected_type = projection.get("tipo_valor")
            if artifact not in ("cartas_fisicas", "dimensoes_fisicas") or not all(isinstance(value, str) and value for value in (source_column, target, expected_type)):
                buckets["invalid"].append({"classificacao": "inválido", "escopo": "cartas", "chave_canonica": {"card_id": card_id}, "motivo": "projeção do pedido incompleta", "projecao": projection})
                continue
            source = sources[artifact].get(card_id)
            if source is None or source_column not in source:
                buckets["invalid"].append({"classificacao": "inválido", "escopo": "cartas", "chave_canonica": {"card_id": card_id}, "motivo": "campo físico solicitado ausente", "projecao": projection})
                continue
            target_key = (str(artifact), target)
            if target_key in seen_targets:
                continue
            seen_targets.add(target_key)
            try:
                physical_value = _canonical_value(source.get(source_column), expected_type)
                database_value = _canonical_value(sources["banco"][card_id].get(target), expected_type)
            except (TypeError, ValueError) as error:
                buckets["invalid"].append({"classificacao": "inválido", "escopo": "cartas", "chave_canonica": {"card_id": card_id}, "motivo": str(error), "projecao": projection})
                continue
            if physical_value != database_value:
                changed.append({"chave_campo": projection.get("chave_campo"), "destino": f"clube_novo.carta_jogo.{target}", "fisico": physical_value, "banco": database_value, "proveniencia": projection.get("proveniencia")})
        if changed:
            buckets["altered"].append({"classificacao": "alterado", "escopo": "cartas", "destino_tabela": "carta_jogo", "chave_canonica": {"card_id": card_id}, "fonte_fisica": {"card_id": card_id}, "vinculo_banco": {"card_id": card_id}, "campos_alterados": changed})
    technical = not buckets["repeated"] and not buckets["invalid"]
    return {"classification_complete": True, "technical_integrity": technical, "exact_match": not any(buckets[kind] for kind in ("new", "removed", "altered", "repeated", "invalid")), "classification": buckets, "normalization": {"identidade": "card_id", "fks": "códigos físicos de dimensões", "apresentacao_excluida": ["box", "títulos", "rótulos de nacionalidade/tipo/posição"]}, "database_write": False}


def classify_catalogs(metadata: dict[str, Any], contract: dict[str, Any], family_states: dict[str, Any]) -> dict[str, Any]:
    """Executa a cobertura de catálogos exatamente como o banco declarou."""
    mappings = contract.get("catalogos_fisicos")
    if not isinstance(mappings, list) or not mappings:
        raise RuntimeError("pedido do banco sem cobertura de catálogos")
    physical = metadata.get("catalogs") if isinstance(metadata, dict) else None
    physical = physical if isinstance(physical, dict) else {}
    database = {(item.get("schema"), item.get("table")): item for item in contract.get("catalogos", []) if isinstance(item, dict)}
    buckets: dict[str, list[dict[str, Any]]] = {
        kind: []
        for kind in ("new", "removed", "altered", "repeated", "invalid", "known_pending")
    }
    coverage: list[dict[str, Any]] = []
    application_blockers: list[dict[str, Any]] = []
    for mapping in mappings:
        schema, table = mapping.get("schema"), mapping.get("table")
        key = (schema, table)
        db = database.get(key)
        if db is None:
            buckets["invalid"].append({"classificacao": "inválido", "escopo": "catalogos", "motivo": "catálogo solicitado ausente do pedido", "catalogo": f"{schema}.{table}"}); continue
        application_allowed = mapping.get("aprovacao_aplicacao_habilitada", True)
        impacted = mapping.get("familias_impactadas") or []
        if not isinstance(application_allowed, bool) or not isinstance(impacted, list) or not all(isinstance(item, str) and item for item in impacted):
            buckets["invalid"].append({"classificacao": "inválido", "escopo": "catalogos", "catalogo": f"{schema}.{table}", "motivo": "gate de cobertura inválido no contrato"}); continue
        if application_allowed is False:
            report_key = mapping.get("chave_resultado_leitura")
            state = mapping.get("estado_cobertura")
            report = physical.get(report_key) if isinstance(report_key, str) else None
            runtime_state = report.get("status") if isinstance(report, dict) else None
            declared_state = report.get("declared_coverage_state") if isinstance(report, dict) else None
            if (not isinstance(report, dict) or report.get("supported") is not False
                    or declared_state != state or not isinstance(runtime_state, str) or not runtime_state
                    or report.get("coverage_complete") is not False
                    or report.get("application_eligible") is not False):
                buckets["invalid"].append({"classificacao": "inválido", "escopo": "catalogos", "catalogo": f"{schema}.{table}", "motivo": "runtime não devolveu a pendência de cobertura declarada"}); continue
            pending_reason = report.get("reason") or mapping.get("motivo_cobertura")
            buckets["known_pending"].append({
                "classificacao": "pendência conhecida",
                "escopo": "catalogos",
                "catalogo": f"{schema}.{table}",
                "estado_contrato": state,
                "estado_monitoramento": runtime_state,
                "motivo": pending_reason,
                "resolvida": False,
                "familias_impactadas": impacted,
            })
            blocker = {
                "catalogo": f"{schema}.{table}",
                "estado_cobertura": state,
                "estado_monitoramento": runtime_state,
                "familias_impactadas": impacted,
                "motivo": pending_reason,
                "procedencia": mapping.get("proveniencia"),
                "origem_fisica_comprovada": report.get("origem_fisica_comprovada"),
                "artefato_fisico_declarado": report.get("artefato_fisico_declarado"),
            }
            application_blockers.append(blocker)
            coverage.append({"catalogo": blocker["catalogo"], "modo": mapping.get("modo_validacao"), "estado_cobertura": state, "estado_monitoramento": runtime_state, "coberto": False, "pendencia_conhecida": True, "pendencia_resolvida": False, "application_eligible": False, "familias_impactadas": impacted, "motivo": blocker["motivo"]})
            continue
        mode = mapping.get("modo_validacao")
        if mode == "dependencia_normalizada":
            family = family_states.get(mapping.get("familia_dependencia"), {})
            check = (family.get("comparison_checks") or {}).get(mapping.get("check_dependencia"), {})
            ok = bool(check.get("completed")) and bool(check.get("classification_complete")) and bool(check.get("technical_integrity"))
            coverage.append({"catalogo": f"{schema}.{table}", "modo": mode, "dependencia": f"{mapping.get('familia_dependencia')}:{mapping.get('check_dependencia')}", "coberto": ok})
            if not ok: buckets["invalid"].append({"classificacao": "inválido", "escopo": "catalogos", "catalogo": f"{schema}.{table}", "motivo": "dependência normalizada ainda não íntegra"})
            continue
        artifact = physical.get(mapping.get("artefato_fisico"))
        records = artifact.get("records") if isinstance(artifact, dict) else None
        source_key = mapping.get("coluna_chave_fisica")
        canonical_keys = mapping.get("colunas_chave_canonica") or []
        if not isinstance(records, list) or not isinstance(source_key, str) or len(canonical_keys) != 1:
            buckets["invalid"].append({"classificacao": "inválido", "escopo": "catalogos", "catalogo": f"{schema}.{table}", "motivo": "fotografia física ou chave declarada ausente"}); continue
        observed: set[str] = set()
        for record in records:
            raw = record.get(source_key) if isinstance(record, dict) else None
            if raw is None or str(raw) == "": buckets["invalid"].append({"classificacao": "inválido", "escopo": "catalogos", "catalogo": f"{schema}.{table}", "motivo": "registro físico sem chave"}); continue
            value = str(raw)
            if value in observed: buckets["repeated"].append({"classificacao": "repetido", "escopo": "catalogos", "catalogo": f"{schema}.{table}", "chave_canonica": {canonical_keys[0]: value}})
            observed.add(value)
        expected = {str(row.get(canonical_keys[0])) for row in db.get("rows", []) if isinstance(row, dict) and row.get(canonical_keys[0]) is not None}
        for value in sorted(observed - expected): buckets["new"].append({"classificacao": "novo", "escopo": "catalogos", "catalogo": f"{schema}.{table}", "chave_canonica": {canonical_keys[0]: value}, "fonte_fisica": mapping.get("proveniencia")})
        for value in sorted(expected - observed): buckets["removed"].append({"classificacao": "removido", "escopo": "catalogos", "catalogo": f"{schema}.{table}", "chave_canonica": {canonical_keys[0]: value}})
        coverage.append({"catalogo": f"{schema}.{table}", "modo": mode, "coberto": True, "chave": canonical_keys[0]})
    technical = not buckets["repeated"] and not buckets["invalid"]
    canonical_kinds = ("new", "removed", "altered", "repeated", "invalid")
    return {"classification_complete": True, "technical_integrity": technical, "exact_match": not any(buckets[k] for k in canonical_kinds), "classification": buckets, "coverage": coverage, "coverage_complete": not application_blockers, "application_eligible": not application_blockers, "application_blockers": application_blockers, "unresolved_pending_count": len(buckets["known_pending"]), "database_write": False}


CLASSIFIED_CHANGE_KINDS = {"new", "removed", "altered", "repeated", "invalid", "known_pending", "historical_unresolved"}


def _iter_classified_entries(classification: Any, path: tuple[str, ...] = ()) -> Any:
    if not isinstance(classification, dict):
        return
    for key, value in classification.items():
        if key in CLASSIFIED_CHANGE_KINDS and isinstance(value, list):
            for entry in value:
                if isinstance(entry, dict):
                    yield key, entry, path
        elif isinstance(value, dict):
            yield from _iter_classified_entries(value, (*path, str(key)))


def _cast_application_value(value: Any, declared: str, label: str) -> Any:
    if value is None:
        return None
    if declared in ("smallint", "integer", "bigint"):
        if isinstance(value, bool):
            raise RuntimeError(f"booleano não aceito como inteiro em {label}")
        return int(value)
    if declared in ("text", "character varying"):
        return str(value)
    if declared == "boolean":
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in ("true", "1", "sim"):
            return True
        if text in ("false", "0", "não", "nao", ""):
            return False
        raise RuntimeError(f"booleano inválido em {label}: {value!r}")
    if declared in ("json", "jsonb", "ARRAY"):
        if not isinstance(value, (dict, list)):
            raise RuntimeError(f"valor estruturado inválido em {label}")
        return value
    return value


def _entry_source_values(entry: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    physical = entry.get("valor_fisico")
    if isinstance(physical, dict):
        values.update(physical)
    elif isinstance(physical, (list, tuple)) and isinstance(entry.get("colunas_fisicas"), list):
        columns = entry["colunas_fisicas"]
        if len(columns) == len(physical) and all(isinstance(column, str) for column in columns):
            values.update(dict(zip(columns, physical, strict=True)))
    changed = entry.get("campos_alterados")
    if isinstance(changed, dict):
        for column, detail in changed.items():
            if not isinstance(column, str) or not isinstance(detail, dict):
                continue
            if "fisico" in detail:
                values[column] = detail.get("fisico")
            elif "source" in detail:
                values[column] = detail.get("source")
    elif isinstance(changed, list):
        for detail in changed:
            if not isinstance(detail, dict):
                continue
            destination = detail.get("destino")
            column = destination.rsplit(".", 1)[-1] if isinstance(destination, str) and "." in destination else detail.get("coluna")
            if isinstance(column, str) and column:
                values[column] = detail.get("fisico", detail.get("source"))
    identity = entry.get("chave_canonica")
    if isinstance(identity, dict):
        values.update(identity)
    return values


def _entry_provenance(entry: dict[str, Any]) -> dict[str, Any] | None:
    physical = entry.get("fonte_fisica")
    provenance: dict[str, Any] = {}
    if isinstance(physical, dict):
        provenance["fonte_fisica"] = physical
    elif physical is not None:
        provenance["fonte_fisica"] = {"descricao": str(physical)}
    changed = entry.get("campos_alterados")
    if isinstance(changed, list):
        fields = [
            {"destino": item.get("destino"), "proveniencia": item.get("proveniencia")}
            for item in changed if isinstance(item, dict) and item.get("proveniencia")
        ]
        if fields:
            provenance["campos"] = fields
    if isinstance(changed, dict) and changed:
        provenance["campos"] = sorted(str(key) for key in changed)
    return provenance or None


def _target_hint(entry: dict[str, Any]) -> str | None:
    direct = entry.get("destino_tabela")
    if isinstance(direct, str) and direct:
        return direct
    catalog = entry.get("catalogo")
    if isinstance(catalog, str) and catalog.startswith("clube_novo."):
        return catalog.split(".", 1)[1]
    changed = entry.get("campos_alterados")
    if isinstance(changed, list):
        tables = {
            item["destino"].split(".")[-2]
            for item in changed
            if isinstance(item, dict) and isinstance(item.get("destino"), str) and item["destino"].count(".") >= 2
        }
        if len(tables) == 1:
            return next(iter(tables))
    return None


def _selection_description(family: str, table: str, identity: dict[str, Any]) -> str:
    identity_text = ", ".join(f"{key}={identity[key]}" for key in sorted(identity))
    return f"{family} | {table} | {identity_text}"


def _selection_coverage_observations(review_gate: dict[str, Any], reports: dict[str, Any]) -> dict[str, Any]:
    """Separa avisos já visíveis de falhas estruturais reais.

    A regra é derivada do próprio resultado: somente um bloqueio de catálogo que
    também aparece como ``known_pending`` pode ficar fora do pacote selecionado.
    Nenhum nome de exceção é cadastrado no código.
    """
    pending_catalogs: set[str] = set()
    for report in reports.values():
        if not isinstance(report, dict):
            continue
        for kind, entry, _ in _iter_classified_entries(report.get("classification")):
            catalog = entry.get("catalogo")
            if kind == "known_pending" and isinstance(catalog, str) and catalog:
                pending_catalogs.add(catalog)
    observations: list[dict[str, Any]] = []
    fatal_blockers: list[dict[str, Any]] = []
    observed_reasons: set[str] = set()
    for blocker in review_gate.get("application_blockers") or []:
        if not isinstance(blocker, dict):
            fatal_blockers.append({"motivo": "bloqueio de cobertura inválido"})
            continue
        catalog = str(blocker.get("catalogo") or "")
        if catalog and catalog in pending_catalogs:
            observations.append(blocker)
            observed_reasons.add("cobertura física não verificável: " + catalog)
        else:
            fatal_blockers.append(blocker)
    fatal_family_reasons: dict[str, list[str]] = {}
    for family, details in (review_gate.get("families") or {}).items():
        if not isinstance(details, dict) or details.get("approved") is True:
            continue
        remaining = [str(reason) for reason in details.get("reasons") or [] if str(reason) not in observed_reasons]
        if remaining:
            fatal_family_reasons[str(family)] = remaining
    return {
        "observations": observations,
        "fatal_blockers": fatal_blockers,
        "fatal_family_reasons": fatal_family_reasons,
        "selection_scope_ready": not fatal_blockers and not fatal_family_reasons,
    }


def _application_contract(contract: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    writers = contract.get("escritores_dominio")
    if not isinstance(writers, list) or not writers:
        raise RuntimeError("pedido ativo sem escritores declarativos")
    payload_families: list[dict[str, Any]] = []
    targets_by_family: dict[str, list[dict[str, Any]]] = {}
    for writer in writers:
        if not isinstance(writer, dict) or not isinstance(writer.get("familia"), str) or not isinstance(writer.get("escritor_id"), str):
            raise RuntimeError("escritor declarativo inválido no pedido")
        targets = writer.get("destinos")
        if not isinstance(targets, list) or not targets:
            raise RuntimeError(f"escritor sem destinos: {writer.get('escritor_id')}")
        normalized_targets: list[dict[str, Any]] = []
        payload_targets: list[dict[str, Any]] = []
        for target in targets:
            if not isinstance(target, dict) or target.get("schema") != "clube_novo" or not isinstance(target.get("tabela"), str):
                raise RuntimeError("destino declarativo inválido ou fora de clube_novo")
            normalized_targets.append(target)
            payload_targets.append({"destino_id": target.get("destino_id"), "tabela": target.get("tabela"), "envelopes": []})
        targets_by_family[writer["familia"]] = normalized_targets
        payload_families.append({"familia": writer["familia"], "escritor_id": writer["escritor_id"], "destinos": payload_targets})
    return payload_families, targets_by_family


def build_application_payload(contract: dict[str, Any], result: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Materializa somente mudanças com destino, chave, tipo e procedência declarados.

    Avisos e pendências continuam no relatório, mas não são convertidos em
    dados. Mudanças materializáveis ficam disponíveis para uma seleção
    explícita do operador; nada é pré-selecionado.
    """
    payload_families, targets_by_family = _application_contract(contract)
    payload_by_family = {item["familia"]: item for item in payload_families}
    blockers: list[dict[str, Any]] = []
    not_selectable_items: list[dict[str, Any]] = []
    historical_warnings = 0
    unresolved_pending = 0
    changed_entries = 0
    eligible_changed_entries = 0
    envelope_index: dict[tuple[str, Any, str], dict[str, Any]] = {}
    reports = result.get("comparison_reports")
    if not isinstance(reports, dict):
        reports = {}
    review_gate = result.get("review_gate") if isinstance(result.get("review_gate"), dict) else {}
    coverage = _selection_coverage_observations(review_gate, reports)

    for report_key, report in reports.items():
        if not isinstance(report, dict):
            continue
        family = str(report_key).split(":", 1)[0]
        classification = report.get("classification")
        for kind, entry, nested_path in _iter_classified_entries(classification):
            identity = entry.get("chave_canonica")
            identity_for_log = identity if isinstance(identity, (dict, list)) else None
            if kind == "historical_unresolved":
                historical_warnings += 1
                continue
            if kind == "known_pending":
                unresolved_pending += 1
                continue
            if kind in ("repeated", "invalid"):
                not_selectable_items.append({"familia": family, "relatorio": str(report_key), "tipo": kind, "chave": identity_for_log, "motivo": "não selecionável: integridade técnica pendente"})
                continue
            if kind == "removed":
                changed_entries += 1
                not_selectable_items.append({"familia": family, "relatorio": str(report_key), "tipo": kind, "chave": identity_for_log, "motivo": "não selecionável: remoção exige operação declarativa explícita no contrato; UPSERT não apaga linhas"})
                continue
            if kind not in ("new", "altered"):
                continue
            changed_entries += 1
            if not isinstance(identity, dict) or not identity:
                not_selectable_items.append({"familia": family, "relatorio": str(report_key), "tipo": kind, "chave": identity_for_log, "motivo": "não selecionável: mudança sem identidade estável"})
                continue
            family_targets = targets_by_family.get(family) or []
            hint = _target_hint(entry)
            candidates = [target for target in family_targets if target.get("tabela") == hint] if hint else []
            if not candidates:
                identity_keys = set(identity)
                compatible = [target for target in family_targets if set(target.get("colunas_chave") or []) == identity_keys]
                if len(compatible) == 1:
                    candidates = compatible
                elif compatible:
                    source_values = _entry_source_values(entry)
                    scored = []
                    for target in compatible:
                        writable = set(target.get("colunas_escrita") or []) - set(target.get("colunas_chave") or [])
                        scored.append((len(writable & set(source_values)), target))
                    best = max((score for score, _ in scored), default=0)
                    candidates = [target for score, target in scored if score == best and score > 0]
            if len(candidates) != 1:
                not_selectable_items.append({"familia": family, "relatorio": str(report_key), "tipo": kind, "chave": identity, "motivo": "não selecionável: destino ausente ou ambíguo para a mudança física"})
                continue
            target = candidates[0]
            keys = [str(column) for column in target.get("colunas_chave") or []]
            writable = [str(column) for column in target.get("colunas_escrita") or []]
            types = target.get("tipos_colunas") if isinstance(target.get("tipos_colunas"), dict) else {}
            allowed = set(keys) | set(writable)
            source_values = _entry_source_values(entry)
            values: dict[str, Any] = {}
            try:
                for column in allowed:
                    if column in source_values:
                        declared = types.get(column)
                        if not isinstance(declared, str):
                            raise RuntimeError(f"tipo não declarado para {target['tabela']}.{column}")
                        values[column] = _cast_application_value(source_values[column], declared, f"{target['tabela']}.{column}")
                canonical_identity = {
                    column: _cast_application_value(identity[column], str(types.get(column) or ""), f"{target['tabela']}.{column}")
                    for column in keys
                }
            except Exception as error:
                not_selectable_items.append({"familia": family, "relatorio": str(report_key), "tipo": kind, "chave": identity, "motivo": "não selecionável: " + str(error)})
                continue
            values.update(canonical_identity)
            missing_keys = [column for column in keys if values.get(column) is None]
            required_for_new = [column for column in writable if column not in keys]
            if missing_keys or (kind == "new" and any(column not in values for column in required_for_new)):
                not_selectable_items.append({"familia": family, "relatorio": str(report_key), "tipo": kind, "chave": identity, "motivo": "não selecionável: faltam campos físicos exigidos para uma linha nova"})
                continue
            if kind == "altered" and required_for_new and not any(column in values for column in required_for_new):
                not_selectable_items.append({"familia": family, "relatorio": str(report_key), "tipo": kind, "chave": identity, "motivo": "não selecionável: diferença sem campo gravável no destino"})
                continue
            provenance = _entry_provenance(entry)
            if target.get("exige_procedencia") and not provenance:
                not_selectable_items.append({"familia": family, "relatorio": str(report_key), "tipo": kind, "chave": identity, "motivo": "não selecionável: mudança sem procedência física persistida"})
                continue
            serialized_identity = json.dumps(canonical_identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            index_key = (family, target.get("destino_id"), serialized_identity)
            envelope = envelope_index.get(index_key)
            if envelope is None:
                selection_id = runtime.sha256_json({"familia": family, "destino_id": target.get("destino_id"), "identidade": canonical_identity})[:24]
                envelope = {
                    "selecao_id": selection_id,
                    "descricao_operador": _selection_description(family, str(target.get("tabela")), canonical_identity),
                    "operacao": "upsert",
                    "identidade": canonical_identity,
                    "valores": {},
                    "procedencia": provenance or {},
                    "origens_alteracao": [],
                }
                envelope_index[index_key] = envelope
                payload_target = next(item for item in payload_by_family[family]["destinos"] if item.get("destino_id") == target.get("destino_id"))
                payload_target["envelopes"].append(envelope)
                eligible_changed_entries += 1
            origin = {"relatorio": str(report_key), "tipo": kind}
            if origin not in envelope["origens_alteracao"]:
                envelope["origens_alteracao"].append(origin)
            conflicts = [column for column, value in values.items() if column in envelope["valores"] and envelope["valores"][column] != value]
            if conflicts:
                not_selectable_items.append({"familia": family, "relatorio": str(report_key), "tipo": kind, "chave": identity, "motivo": "não selecionável: valores físicos conflitantes para " + ", ".join(conflicts)})
                payload_target = next(item for item in payload_by_family[family]["destinos"] if item.get("destino_id") == target.get("destino_id"))
                payload_target["envelopes"] = [item for item in payload_target["envelopes"] if item is not envelope]
                envelope_index.pop(index_key, None)
                eligible_changed_entries = max(0, eligible_changed_entries - 1)
                continue
            envelope["valores"].update(values)

    if not coverage["selection_scope_ready"]:
        blockers.append({
            "familia": "contrato",
            "tipo": "coverage",
            "motivo": "há falha estrutural fora das pendências já mostradas no relatório",
            "detalhes": {
                "bloqueios": coverage["fatal_blockers"],
                "familias": coverage["fatal_family_reasons"],
            },
        })

    envelope_count = sum(len(target["envelopes"]) for family in payload_families for target in family["destinos"])
    selectable_items = sorted([
        {
            "selecao_id": envelope["selecao_id"],
            "descricao": envelope["descricao_operador"],
            "familia": family["familia"],
            "tabela": target.get("tabela"),
            "identidade": envelope["identidade"],
        }
        for family in payload_families
        for target in family["destinos"]
        for envelope in target["envelopes"]
    ], key=lambda item: (str(item["familia"]), str(item["tabela"]), str(item["descricao"])))
    selection_available = envelope_count > 0 and not blockers
    state = "selection_required" if selection_available else "blocked" if blockers else "no_changes"
    payload = {"schema": "clubef-envelopes-aplicacao-v1", "familias": payload_families, "state": state}
    status = {
        "contract": "clubef-application-plan-v1",
        "enabled": False,
        "state": state,
        "database_write": False,
        "explicit_operator_action_required": True,
        "changed_entry_count": changed_entries,
        "eligible_changed_entry_count": eligible_changed_entries,
        "envelope_count": envelope_count,
        "selection_required": selection_available,
        "selection_available": selection_available,
        "selectable_items": selectable_items,
        "historical_warning_count": historical_warnings,
        "unresolved_pending_count": unresolved_pending,
        "report_observation_count": len(coverage["observations"]),
        "report_observations": coverage["observations"],
        "not_selectable_count": len(not_selectable_items),
        "not_selectable_items": not_selectable_items,
        "blockers": blockers,
        "transaction_plan": "uma única transação; qualquer erro ou readback divergente executa rollback antes do commit",
        "rollback_plan": "rollback automático antes do commit; nenhuma remoção é inferida por ausência",
        "readback_plan": "SELECT independente de todas as colunas gravadas antes do commit e nova conexão somente leitura após o commit",
    }
    return payload, status


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _skill_stage_contract(contract: dict[str, Any]) -> tuple[dict[int, dict[str, Any]], dict[int, dict[str, Any]]]:
    """Lê membros repetidos exclusivamente do pedido tipado atual."""
    destinations: dict[int, dict[str, Any]] = {}
    for writer in contract.get("escritores_dominio") or []:
        if not isinstance(writer, dict):
            raise RuntimeError("escritor inválido no contrato")
        for target in writer.get("destinos") or []:
            if not isinstance(target, dict) or not _is_int(target.get("destino_id")):
                raise RuntimeError("destino inválido no contrato")
            destinations[int(target["destino_id"])] = target
    mappings = [
        item for item in (contract.get("mapeamentos_envelope") or [])
        if isinstance(item, dict)
        and item.get("status") == "comprovado"
        and item.get("artefato_fisico") == "cartas_fisicas"
        and item.get("coluna_fisica") == "habilidades"
        and (item.get("regra_decomposicao") or {}).get("tipo") == "lista_filtrada_bit"
    ]
    if not mappings:
        raise RuntimeError("pedido sem membros físicos comprovados de habilidades")
    by_field: dict[int, dict[str, Any]] = {}
    covered_field_keys: set[str] = set()
    expected_field_keys: set[str] = set()
    for mapping in mappings:
        destination_id, field_id, column = mapping.get("destino_id"), mapping.get("campo_id"), mapping.get("coluna_destino")
        target = destinations.get(destination_id) if _is_int(destination_id) else None
        rule = mapping.get("regra_decomposicao") or {}
        if (not _is_int(field_id) or field_id in by_field or not isinstance(column, str) or not isinstance(target, dict)
                or column not in (target.get("colunas_chave") or []) or column not in (target.get("colunas_escrita") or [])
                or not _is_int(mapping.get("mapeamento_id")) or not _is_int(mapping.get("ordem_regra"))
                or not isinstance(mapping.get("normalizador_id"), str) or not isinstance(mapping.get("versao_normalizador"), str)
                or not isinstance(mapping.get("proveniencia"), str)):
            raise RuntimeError("membro de habilidade incompleto no pedido")
        match = re.fullmatch(rf"{re.escape(column)}=(-?\d+)", str(rule.get("chave") or ""))
        if not match or not _is_int(rule.get("bit")) or not _is_int(rule.get("largura")) or int(rule["largura"]) <= 0:
            raise RuntimeError("regra declarativa de habilidade inválida")
        expected_value = int(match.group(1))
        candidates = [
            field for field in contract.get("campos") or []
            if isinstance(field, dict)
            and field.get("entidade_destino") == f"{target.get('tabela')}.{column}"
            and _is_int(field.get("bit_inicio")) and int(field["bit_inicio"]) == int(rule["bit"])
            and _is_int(field.get("largura_bits")) and int(field["largura_bits"]) == int(rule["largura"])
            and _is_int((field.get("transformacao") or {}).get(column))
            and int((field.get("transformacao") or {})[column]) == expected_value
        ]
        if len(candidates) != 1:
            raise RuntimeError(f"mapeamento de habilidade sem campo físico único: campo_id {field_id}")
        by_field[int(field_id)] = mapping
        covered_field_keys.add(str(candidates[0].get("chave_campo")))
        for field in contract.get("campos") or []:
            if isinstance(field, dict) and field.get("entidade_destino") == f"{target.get('tabela')}.{column}":
                expected_field_keys.add(str(field.get("chave_campo")))
    if not covered_field_keys or covered_field_keys != expected_field_keys:
        raise RuntimeError("cobertura de campos físicos de habilidade incompleta ou duplicada")
    return by_field, destinations


def materialize_skill_envelopes_from_artifact(contract: dict[str, Any], cards_path: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Monta envelopes reais de ``lista_filtrada_bit`` sem lista local de IDs."""
    if not cards_path.is_file():
        raise RuntimeError("artefato canônico de cartas não encontrado")
    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    if not isinstance(cards, list) or not cards:
        raise RuntimeError("artefato canônico de cartas inválido")
    by_field, destinations = _skill_stage_contract(contract)
    envelopes: list[dict[str, Any]] = []
    seen: set[tuple[int, str, int]] = set()
    for card in cards:
        if not isinstance(card, dict) or card.get("card_id") in (None, ""):
            raise RuntimeError("artefato sem card_id canônico")
        card_id = str(card["card_id"])
        members = card.get("habilidades_fisicas")
        if not isinstance(members, list):
            raise RuntimeError(f"artefato sem habilidades_fisicas: {card_id}")
        for member in members:
            if not isinstance(member, dict) or member.get("ativo") is not True or not _is_int(member.get("campo_id")):
                raise RuntimeError(f"membro físico inválido em {card_id}")
            mapping = by_field.get(int(member["campo_id"]))
            if mapping is None:
                raise RuntimeError(f"membro físico sem mapeamento declarado em {card_id}")
            rule, column = mapping["regra_decomposicao"], str(mapping["coluna_destino"])
            match = re.fullmatch(rf"{re.escape(column)}=(-?\d+)", str(rule.get("chave") or ""))
            expected_value = int(match.group(1)) if match else None
            if (member.get(column) != expected_value or member.get("bit") != rule.get("bit")
                    or member.get("largura") != rule.get("largura") or not _is_int(member.get("registro"))
                    or not isinstance(member.get("arquivo"), str) or not isinstance(member.get("hash"), str)
                    or not isinstance(member.get("procedencia"), str)):
                raise RuntimeError(f"membro físico divergente do contrato em {card_id}/campo {member['campo_id']}")
            destination_id = int(mapping["destino_id"])
            target = destinations[destination_id]
            identity: dict[str, Any] = {}
            for key in target.get("colunas_chave") or []:
                if key == "card_id": identity[key] = card_id
                elif key == column: identity[key] = expected_value
                else: raise RuntimeError(f"chave de destino sem origem declarada: {key}")
            values = dict(identity)
            types = target.get("tipos_colunas") or {}
            if any(not _type_matches(value, str(types.get(key, ""))) for key, value in values.items()):
                raise RuntimeError(f"tipo de envelope divergente em {card_id}/campo {member['campo_id']}")
            unique = (destination_id, card_id, expected_value)
            if unique in seen:
                raise RuntimeError(f"duplicidade física de card_id/FK em {card_id}/{expected_value}")
            seen.add(unique)
            envelopes.append({
                "destino_id": destination_id, "identidade": identity, "valores": values,
                "procedencia": {
                    "arquivo": member["arquivo"], "sha256_arquivo": member["hash"], "registro": member["registro"],
                    "campo_id": member["campo_id"], "mapeamento_id": mapping["mapeamento_id"], "bit": member["bit"],
                    "largura": member["largura"], "ordem": member.get("ordem"), "regra_decomposicao": rule,
                    "normalizador": {"id": mapping["normalizador_id"], "versao": mapping["versao_normalizador"]},
                    "proveniencia_contrato": mapping["proveniencia"],
                },
            })
    return envelopes, {"mapeamentos_comprovados": len(by_field), "cartas_lidas": len(cards), "envelopes": len(envelopes), "duplicidades": 0}


def smoke_stage_skill_envelopes(args: argparse.Namespace) -> int:
    """Insere somente no estágio de revisão e sempre reverte a transação."""
    run_dir = Path(args.run_dir).resolve()
    cards_path, plan_path = run_dir / "cartas-fisicas-canonicas.json", run_dir / "pedido-leitura.json"
    if not plan_path.is_file():
        raise RuntimeError("pedido selado da fotografia não encontrado")
    artifact_plan = json.loads(plan_path.read_text(encoding="utf-8"))
    config = runtime.load_config()
    contract = runtime.current_reading_contract(config)
    seal = runtime.reading_contract_seal(contract)
    if runtime.reading_contract_seal(artifact_plan) != seal:
        raise RuntimeError("artefato físico vencido: selo do contrato não confere")
    envelopes, coverage = materialize_skill_envelopes_from_artifact(contract, cards_path)
    if not envelopes:
        raise RuntimeError("nenhum envelope de habilidade materializado")
    # A leitura e a validação continuam integrais; o limite só reduz o lote
    # transacional de smoke e é selado no pacote para não parecer carga completa.
    limit = int(getattr(args, "smoke_stage_habilidades_limite", 0) or 0)
    if limit < 0:
        raise RuntimeError("limite do smoke de habilidades inválido")
    ordered = sorted(
        envelopes,
        key=lambda item: (
            int(item["destino_id"]),
            int(str(item["identidade"].get("card_id"))),
            int(item["identidade"].get("skill_id")),
        ),
    )
    staged_envelopes = ordered
    represented_fields: set[int] = set()
    if limit:
        representatives: list[dict[str, Any]] = []
        for item in ordered:
            field_id = int(item["procedencia"]["campo_id"])
            if field_id not in represented_fields:
                represented_fields.add(field_id)
                representatives.append(item)
        if limit < len(representatives):
            raise RuntimeError("limite do smoke menor que a cobertura física de habilidades")
        selected = {(int(item["destino_id"]), str(item["identidade"]["card_id"]), int(item["identidade"]["skill_id"])) for item in representatives}
        staged_envelopes = representatives + [
            item for item in ordered
            if (int(item["destino_id"]), str(item["identidade"]["card_id"]), int(item["identidade"]["skill_id"])) not in selected
        ][:limit - len(representatives)]
    else:
        represented_fields = {int(item["procedencia"]["campo_id"]) for item in staged_envelopes}
    coverage = {
        **coverage,
        "envelopes_fisicos_total": len(envelopes),
        "envelopes_estagiados_no_smoke": len(staged_envelopes),
        "limite_solicitado": limit or None,
        "campos_fisicos_representados_no_smoke": len(represented_fields),
    }
    artifact_sha256 = runtime.sha256_file(cards_path)
    stage_seal = {**seal, "artefato": cards_path.name, "artefato_sha256": artifact_sha256, "modo": "smoke_rollback", "limite_envelopes": limit or None}
    package_sha256 = runtime.sha256_json({"schema": "clubef-envelopes-estagio-v1", "selo": stage_seal, "envelopes": staged_envelopes})
    psycopg, sql, Jsonb = runtime.import_psycopg()
    dsn = runtime.connection_string()
    if not dsn:
        raise RuntimeError("conexão segura com clube_novo indisponível")
    target_ids = {int(item["destino_id"]) for item in staged_envelopes}
    targets = {int(target["destino_id"]): target for writer in contract.get("escritores_dominio") or [] for target in writer.get("destinos") or [] if isinstance(target, dict) and _is_int(target.get("destino_id")) and int(target["destino_id"]) in target_ids}
    if set(targets) != target_ids:
        raise RuntimeError("destino de envelope não declarado no pedido atual")
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        before_stage = int(connection.execute("select count(*) from clube_novo.envelope_revisao_extrator_estagio where pacote_sha256=%s", (package_sha256,)).fetchone()[0])
        before_domain = {str(key): int(connection.execute(sql.SQL("select count(*) from {}.{}").format(sql.Identifier(str(target["schema"])), sql.Identifier(str(target["tabela"])))).fetchone()[0]) for key, target in targets.items()}
        insert = "insert into clube_novo.envelope_revisao_extrator_estagio (contrato_id,pacote_sha256,destino_id,identidade,valores,procedencia,selo,estado) values (%s,%s,%s,%s,%s,%s,%s,'revisao')"
        with connection.cursor() as cursor:
            for start in range(0, len(staged_envelopes), 2000):
                batch = staged_envelopes[start:start + 2000]
                cursor.executemany(insert, [(contract["contrato_id"], package_sha256, item["destino_id"], Jsonb(item["identidade"]), Jsonb(item["valores"]), Jsonb(item["procedencia"]), Jsonb(stage_seal)) for item in batch])
                emit(
                    "stage_progress",
                    completed=min(start + len(batch), len(staged_envelopes)),
                    total=len(staged_envelopes),
                    stage_write_in_transaction=True,
                    database_write_committed=False,
                    data_domain_write=False,
                )
        staged = connection.execute("select count(*),count(distinct identidade) from clube_novo.envelope_revisao_extrator_estagio where pacote_sha256=%s", (package_sha256,)).fetchone()
        if staged != (len(staged_envelopes), len(staged_envelopes)):
            raise RuntimeError("readback do estágio de habilidades divergente")
        connection.rollback()
        after_stage = int(connection.execute("select count(*) from clube_novo.envelope_revisao_extrator_estagio where pacote_sha256=%s", (package_sha256,)).fetchone()[0])
        after_domain = {str(key): int(connection.execute(sql.SQL("select count(*) from {}.{}").format(sql.Identifier(str(target["schema"])), sql.Identifier(str(target["tabela"])))).fetchone()[0]) for key, target in targets.items()}
        connection.rollback()
    if after_stage != before_stage or after_domain != before_domain:
        raise RuntimeError("rollback do estágio não preservou o estado anterior")
    report = {"stage_write_in_transaction": True, "database_write_committed": False, "data_domain_write": False, "transaction": "rollback_obrigatorio", "artifact": str(cards_path), "artifact_sha256": artifact_sha256, "selo": stage_seal, "pacote_sha256": package_sha256, "coverage": coverage, "stage": {"antes": before_stage, "readback": int(staged[0]), "identidades_distintas": int(staged[1]), "apos_rollback": after_stage}, "domain": {"antes": before_domain, "apos_rollback": after_domain}}
    report_path = run_dir / "smoke-estagio-habilidades-rollback.json"
    write_json(report_path, report)
    emit("complete", state="skill_stage_test_rolled_back", stage_write_in_transaction=True, database_write_committed=False, data_domain_write=False, report_path=str(report_path), envelopes=len(staged_envelopes), envelopes_fisicos_total=len(envelopes), pacote_sha256=package_sha256)
    return 0


def persist_motor_readiness(
    root: Path,
    run_dir: Path,
    result: dict[str, Any],
    contract: dict[str, Any],
    physical: dict[str, Any],
    canonical_cards_path: Path,
    dimensions_path: Path,
    metadata_path: Path,
) -> None:
    """Persiste o gate dos motores sem interferir em publicação ou aplicação."""
    output_path = run_dir / "prontidao-motores.json"
    summary_path = run_dir / "resumo-prontidao-motores.json"
    operator_review_path = run_dir / "revisao-prontidao-motores.json"
    override_path = root / "artefatos" / "estado-operador" / "prontidao-motores-operador.json"
    required = {
        "cartas-fisicas-canonicas.json": canonical_cards_path,
        "dimensoes-fisicas.json": dimensions_path,
        "metadados-fisicos.json": metadata_path,
    }
    try:
        missing = [name for name, path in required.items() if not path.is_file()]
        if missing:
            raise RuntimeError("artefatos físicos ausentes: " + ", ".join(missing))
        cards = json.loads(canonical_cards_path.read_text(encoding="utf-8-sig"))
        dimensions = json.loads(dimensions_path.read_text(encoding="utf-8-sig"))
        metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
        overrides = json.loads(override_path.read_text(encoding="utf-8-sig")) if override_path.is_file() else None
        family_fingerprints = {
            name: seal.get("fingerprint_familia")
            for name, seal in (physical.get("family_seals") or {}).items()
            if isinstance(seal, dict) and seal.get("fingerprint_familia")
        }
        artifact = card_completeness.build_artifact(
            cards,
            dimensions,
            metadata,
            contract_seal=runtime.reading_contract_seal(contract),
            source_seal={
                "physical_reader": physical.get("physical_reader"),
                "family_fingerprints": family_fingerprints,
            },
            operator_overrides=overrides,
        )
        summary = artifact.get("summary") or {}
        waiting = int(summary.get("aguardando_insumos") or 0)
        waiting_resolution = int(summary.get("aguardando_decisao_de_vinculo") or 0)
        blocked_cards = waiting + waiting_resolution
        state = "pronto" if blocked_cards == 0 else "parcial_fail_closed_para_motores"
        write_compact_json(output_path, artifact)
        write_compact_json(operator_review_path, card_completeness.build_operator_review(artifact))
        write_json(summary_path, {
            "schema": "clubef-prontidao-motores-resumo-v1",
            "regra_completude": artifact.get("regra_completude"),
            "gerado_em": artifact.get("gerado_em"),
            "database_write": False,
            "publicacao_independente": True,
            "publicacao_bloqueada_por_este_gate": False,
            "semantica_ausencia": artifact.get("semantica_ausencia"),
            "summary": summary,
        })
        result["motor_readiness"] = {
            "state": state,
            "summary": summary,
            "motor_fail_closed": blocked_cards > 0,
            "database_write": False,
            "publicacao_independente": True,
            "publicacao_bloqueada_por_este_gate": False,
            "operator_override_loaded": override_path.is_file(),
            "operator_review_path": str(operator_review_path),
        }
        emit(
            "family",
            family="Prontidão dos motores",
            state="ready" if blocked_cards == 0 else "review",
            message=(
                "Todas as cartas aplicáveis estão prontas para os motores."
                if blocked_cards == 0
                else f"{blocked_cards} carta(s) aguardam insumos ou decisão para Motor/Otimizador/Bonificador; publicação continua independente."
            ),
            database_write=False,
        )
    except Exception as error:
        message = str(error)
        failure = {
            "schema": "clubef-prontidao-motores-indisponivel-v1",
            "gerado_em": datetime.now(timezone.utc).isoformat(),
            "database_write": False,
            "state": "indisponivel_fail_closed",
            "motor_fail_closed": True,
            "publicacao_independente": True,
            "publicacao_bloqueada_por_este_gate": False,
            "reason": message,
            "summary": {
                "cards": 0,
                "motor_eligible": 0,
                "aguardando_insumos": None,
            },
        }
        write_json(output_path, failure)
        result["motor_readiness"] = {
            "state": "indisponivel_fail_closed",
            "summary": failure["summary"],
            "motor_fail_closed": True,
            "reason": message,
            "database_write": False,
            "publicacao_independente": True,
            "publicacao_bloqueada_por_este_gate": False,
            "operator_override_loaded": override_path.is_file(),
        }
        emit(
            "family",
            family="Prontidão dos motores",
            state="error",
            message=f"Prontidão indisponível para os motores: {message}. Publicação continua independente.",
            database_write=False,
        )
    result.setdefault("artifacts", {})["motor_readiness"] = str(output_path)
    if summary_path.is_file():
        result.setdefault("artifacts", {})["motor_readiness_summary"] = str(summary_path)
    if operator_review_path.is_file():
        result.setdefault("artifacts", {})["motor_readiness_operator_review"] = str(operator_review_path)


def prepare_motor_protection_seed(run_dir: Path) -> dict[str, Any]:
    """Materializa o seed local selado que habilita somente o botão dedicado."""
    output_dir = run_dir / "protecao-motores"
    manifest_path = output_dir / "manifest-seed-completude-motores.json"
    # Uma revisão local da prontidão torna qualquer manifesto anterior obsoleto.
    # Remover apenas este derivado impede que a UI ofereça um seed antigo.
    manifest_path.unlink(missing_ok=True)
    emit(
        "progress",
        stage="Preparando conferência selada para a proteção dos motores",
        percent=98,
        database_write=False,
    )
    manifest = motor_protection_seed.build_seed(run_dir, output_dir)
    return {
        "ready": True,
        "manifest_path": str(manifest_path),
        "seed_path": str(output_dir / "seed-completude-motores.ndjson"),
        "seed_sha256": manifest["seed"]["sha256"],
        "cards": int(manifest["contagens"]["envelopes"]),
        "components": int(manifest["contagens"]["componentes"]),
        "database_write": False,
    }


def revalidate_saved_no_changes(
    root: Path,
    run_dir: Path,
    config: dict[str, Any],
    contract: dict[str, Any],
    *,
    reason: str,
) -> dict[str, Any]:
    """Repete no banco atual todas as comparações do run físico salvo.

    A proteção nunca aceita apenas IDs iguais. Relações, cartas, ímpetos,
    dimensões, catálogos, técnicos e textos são relidos por SELECT usando os
    mesmos validadores da varredura. O artefato físico não é reextraído nem
    alterado.
    """
    required = {
        "resultado.json": run_dir / "resultado.json",
        "cartas-fisicas.csv": run_dir / "cartas-fisicas.csv",
        "cartas-fisicas-canonicas.json": run_dir / "cartas-fisicas-canonicas.json",
        "dimensoes-fisicas.json": run_dir / "dimensoes-fisicas.json",
        "metadados-fisicos.json": run_dir / "metadados-fisicos.json",
    }
    missing = [name for name, path in required.items() if not path.is_file()]
    if missing:
        raise RuntimeError(
            "a reconferência antes da proteção não encontrou: " + ", ".join(missing)
        )
    saved_result = json.loads(required["resultado.json"].read_text(encoding="utf-8-sig"))
    old_status = saved_result.get("application_status") or {}
    if (
        saved_result.get("state") != "completed"
        or saved_result.get("database_write") is not False
        or old_status.get("state") != "no_changes"
        or old_status.get("selection_available") is not False
    ):
        raise RuntimeError("a execução salva não terminou íntegra e sem mudanças")

    card_csv = required["cartas-fisicas.csv"].read_text(encoding="utf-8-sig")
    canonical_cards = json.loads(
        required["cartas-fisicas-canonicas.json"].read_text(encoding="utf-8-sig")
    )
    dimensions = json.loads(
        required["dimensoes-fisicas.json"].read_text(encoding="utf-8-sig")
    )
    metadata = json.loads(
        required["metadados-fisicos.json"].read_text(encoding="utf-8-sig")
    )
    baseline, baseline_info = runtime.current_card_canonical_baseline(config, contract)
    comparison: dict[str, Any] = {
        "state": "completed",
        "database_write": False,
        "comparisons": {},
        "contract_seal": runtime.reading_contract_seal(contract),
    }
    with tempfile.TemporaryDirectory(prefix="clubef-revalidacao-motores-") as temporary:
        baseline_path = Path(temporary) / "baseline-cartas-canonico.csv"
        baseline_path.write_bytes(baseline)
        compare_family(
            "Relações",
            lambda: runtime.current_card_relations_validation(card_csv, canonical_cards, config, contract),
            comparison,
            "relacoes",
            "relacoes_normalizadas",
        )
        compare_family(
            "Cartas",
            lambda: classify_canonical_cards(
                required["cartas-fisicas.csv"],
                required["dimensoes-fisicas.json"],
                baseline_path,
                contract,
            ),
            comparison,
            "cartas",
            "baseline",
        )
    compare_family(
        "Ímpetos",
        lambda: runtime.current_card_impetus_validation(card_csv, config, contract),
        comparison,
        "impetos",
        "slots_normalizados",
    )
    compare_family(
        "Dimensões",
        lambda: runtime.current_card_dimensions_validation(dimensions, config),
        comparison,
        "dimensoes",
        "dimensoes_normalizadas",
    )
    catalogs = metadata.get("catalogs") or {}
    if not isinstance(catalogs.get("impetos"), dict):
        raise RuntimeError("metadados salvos sem catálogo de ímpetos")
    compare_family(
        "Ímpetos",
        lambda: runtime.current_impetos_validation(catalogs["impetos"], config, contract),
        comparison,
        "impetos",
        "catalogo_normalizado",
    )
    if not isinstance(catalogs.get("tecnicos"), dict):
        raise RuntimeError("metadados salvos sem catálogo de técnicos")
    technician_snapshot = {
        **catalogs["tecnicos"],
        "nationalities": (catalogs.get("nacionalidades") or {}).get("records") or [],
        "affinities": (catalogs.get("afinidades_tecnico") or {}).get("records") or [],
    }
    compare_family(
        "Técnicos",
        lambda: runtime.current_tecnicos_validation(technician_snapshot, config, contract),
        comparison,
        "tecnicos",
        "tecnicos_normalizados",
    )
    if not isinstance(catalogs.get("textos"), dict):
        raise RuntimeError("metadados salvos sem catálogo de textos")
    compare_family(
        "Textos",
        lambda: runtime.current_text_validation(catalogs["textos"], config),
        comparison,
        "textos",
        "textos_normalizados",
    )
    compare_family(
        "Catálogos",
        lambda: classify_catalogs(metadata, contract, comparison.get("contract_families") or {}),
        comparison,
        "catalogos",
        "catalogos_normalizados",
    )
    comparison["review_gate"] = runtime.evaluate_sync_readiness(
        contract, comparison.get("contract_families") or {}
    )
    _payload, status = build_application_payload(contract, comparison)
    proof = {
        "schema": "clubef-revalidacao-no-changes-protecao-motores-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "database_write": False,
        "baseline_records": int(baseline_info.get("records") or 0),
        "reading_contract": runtime.reading_contract_seal(contract),
        "comparison_reports_sha256": runtime.sha256_json(
            comparison.get("comparison_reports") or {}
        ),
        "contract_families": comparison.get("contract_families") or {},
        "application_status": status,
    }
    write_json(run_dir / ("revalidacao-protecao-motores-" + reason + ".json"), proof)
    if status.get("state") != "no_changes" or status.get("selection_available") is not False:
        raise RuntimeError(
            "o banco atual não corresponde mais aos artefatos salvos; faça uma nova varredura e resolva as mudanças"
        )
    return proof


def run(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    run_dir = Path(args.run_dir).resolve()
    cancel_path = Path(args.cancel).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    result_path = run_dir / "resultado.json"
    emit("status", database="connecting", sources="checking", database_write=False, message="Abrindo somente a leitura canônica do banco.")

    try:
        config = runtime.load_config()
        contract = runtime.current_reading_contract(config)
    except Exception as error:
        message = str(error)
        failure = {"database_write": False, "state": "blocked", "reason": message, "families": {}}
        write_json(result_path, failure)
        emit("status", database="disconnected", sources="unknown", database_write=False, message=message)
        emit("complete", state="blocked", result_path=str(result_path), database_write=False)
        return 2

    emit("status", database="connected_read_only", sources="checking", database_write=False, message="Contrato canônico selado recebido.")
    discovered = sources(contract)
    missing = [role for role, item in discovered.items() if item.get("required", True) and not item.get("found")]
    for role, item in discovered.items():
        emit("source", role=role, found=bool(item.get("found")), message=item.get("reason") or item.get("location"))
    if missing:
        failure = {"database_write": False, "state": "blocked", "reason": "fontes ausentes: " + ", ".join(missing), "families": {}}
        write_json(result_path, failure)
        emit("status", database="connected_read_only", sources="missing", database_write=False, message=failure["reason"])
        emit("complete", state="blocked", result_path=str(result_path), database_write=False)
        return 3

    cancelled(cancel_path)
    plan_path = run_dir / "pedido-leitura.json"
    source_path = run_dir / "fontes.json"
    canonical_baseline_path = run_dir / "baseline-cartas-canonico.csv"
    physical_path = run_dir / "fisico.json"
    write_json(plan_path, contract)
    write_json(source_path, discovered)
    try:
        canonical_baseline, canonical_info = runtime.current_card_canonical_baseline(config, contract)
        canonical_baseline_path.write_bytes(canonical_baseline)
        emit("log", message=f"Baseline canônica read-only: {canonical_info.get('records', 0)} cartas.")
    except Exception as error:
        # Cartas pode falhar, mas a leitura física das demais famílias continua.
        canonical_baseline_path.write_text("card_id\n", encoding="utf-8")
        emit("family", family="Cartas", state="error", message=f"Baseline indisponível: {error}")

    command = [find_node() or "node", str(root / "executor" / "desktop_physical_worker.js"), "--root", str(root), "--plan", str(plan_path), "--sources", str(source_path), "--output", str(physical_path), "--cancel", str(cancel_path)]
    emit("status", database="connected_read_only", sources="found", database_write=False, message="Worker físico separado iniciado.")
    try:
        child = subprocess.Popen(command, cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    except OSError as error:
        write_json(result_path, {"database_write": False, "state": "failed", "reason": str(error), "families": {}})
        emit("complete", state="failed", result_path=str(result_path), database_write=False)
        return 4
    assert child.stdout is not None
    for line in child.stdout:
        cancelled(cancel_path)
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            emit("log", message=line)
            continue
        event_type = str(event.pop("type", "log"))
        emit(event_type, **event)
    code = child.wait()
    if code:
        state = "cancelled" if code == 130 or cancel_path.exists() else "failed"
        write_json(result_path, {"database_write": False, "state": state, "reason": "worker físico encerrado: " + str(code), "families": {}})
        emit("complete", state=state, result_path=str(result_path), database_write=False)
        return code

    physical = json.loads(physical_path.read_text(encoding="utf-8"))
    result: dict[str, Any] = {
        **physical,
        "state": "completed",
        "database_write": False,
        "launcher_protocol_version": DESKTOP_WORKER_PROTOCOL_VERSION,
        "comparisons": {},
    }
    cards_path = Path(str((physical.get("artifacts") or {}).get("cards_csv", "")))
    canonical_cards_path = Path(str((physical.get("artifacts") or {}).get("cards_canonical", "")))
    dimensions_path = Path(str((physical.get("artifacts") or {}).get("dimensions", "")))
    metadata_path = Path(str((physical.get("artifacts") or {}).get("metadata", "")))
    persist_motor_readiness(
        root,
        run_dir,
        result,
        contract,
        physical,
        canonical_cards_path,
        dimensions_path,
        metadata_path,
    )
    if cards_path.is_file():
        card_csv = cards_path.read_text(encoding="utf-8-sig")
        if not canonical_cards_path.is_file():
            # Não há retorno à projeção CSV: habilidades e estilos IA precisam
            # preservar FKs/bit/procedência no artefato canônico.
            compare_family(
                "Relações",
                lambda: (_ for _ in ()).throw(RuntimeError("artefato canônico de cartas ausente; comparação de relações bloqueada")),
                result,
                "relacoes",
                "relacoes_normalizadas",
            )
        else:
            canonical_cards = json.loads(canonical_cards_path.read_text(encoding="utf-8"))
            compare_family(
                "Relações",
                lambda: runtime.current_card_relations_validation(card_csv, canonical_cards, config, contract),
                result,
                "relacoes",
                "relacoes_normalizadas",
            )
        if dimensions_path.is_file() and canonical_baseline_path.is_file():
            compare_family("Cartas", lambda: classify_canonical_cards(cards_path, dimensions_path, canonical_baseline_path, contract), result, "cartas", "baseline")
        compare_family("Ímpetos", lambda: runtime.current_card_impetus_validation(card_csv, config, contract), result, "impetos", "slots_normalizados")
    if dimensions_path.is_file():
        snapshot = json.loads(dimensions_path.read_text(encoding="utf-8"))
        compare_family("Dimensões", lambda: runtime.current_card_dimensions_validation(snapshot, config), result, "dimensoes", "dimensoes_normalizadas")
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        catalogs = metadata.get("catalogs") or {}
        if isinstance(catalogs.get("impetos"), dict):
            compare_family("Ímpetos", lambda: runtime.current_impetos_validation(catalogs["impetos"], config, contract), result, "impetos", "catalogo_normalizado")
        if isinstance(catalogs.get("tecnicos"), dict):
            technician_snapshot = {**catalogs["tecnicos"], "nationalities": (catalogs.get("nacionalidades") or {}).get("records") or [], "affinities": (catalogs.get("afinidades_tecnico") or {}).get("records") or []}
            compare_family("Técnicos", lambda: runtime.current_tecnicos_validation(technician_snapshot, config, contract), result, "tecnicos", "tecnicos_normalizados")
        if isinstance(catalogs.get("textos"), dict):
            compare_family("Textos", lambda: runtime.current_text_validation(catalogs["textos"], config), result, "textos", "textos_normalizados")
        compare_family("Catálogos", lambda: classify_catalogs(metadata, contract, result.get("contract_families") or {}), result, "catalogos", "catalogos_normalizados")
    result["review_gate"] = runtime.evaluate_sync_readiness(contract, result.get("contract_families") or {})
    application_payload, application_status = build_application_payload(contract, result)
    application_plan_path = run_dir / "plano-aplicacao.json"
    application_plan = {
        **application_status,
        "reading_contract": runtime.reading_contract_seal(contract),
        "payload_sha256": runtime.sha256_json(application_payload),
    }
    write_json(application_plan_path, application_plan)
    result["application_status"] = application_status
    if isinstance(result.get("artifacts"), dict):
        result["artifacts"]["application_plan"] = str(application_plan_path)
    review_package = {
        "contract": "clubef-pacote-revisao-v1",
        "reading_contract": runtime.reading_contract_seal(contract),
        "database_write": False,
        "contract_families": result.get("contract_families") or {},
        "comparison_reports": result.get("comparison_reports") or {},
        # O pacote precisa expor a pendência declarada, não apenas recusar o
        # aplicador depois. Leitura das outras famílias continua disponível.
        "review_gate": result["review_gate"],
        "application_status": application_status,
        "application_payload": application_payload,
    }
    package = {"database_write": False, "pacote_revisao": review_package, "pacote_sha256": runtime.sha256_json(review_package)}
    package_path = run_dir / "pacote-revisao.json"
    write_json(package_path, package)
    result["pacote_revisao"] = {"path": str(package_path), "pacote_sha256": package["pacote_sha256"], "database_write": False}
    write_json(result_path, result)
    motor_protection: dict[str, Any]
    if application_status.get("state") == "no_changes":
        try:
            motor_protection = prepare_motor_protection_seed(run_dir)
            emit(
                "family",
                family="Proteção dos motores",
                state="ready",
                message="Seed local conferido; a instalação continua separada e nunca é automática.",
                database_write=False,
            )
        except Exception as error:
            motor_protection = {"ready": False, "reason": str(error), "database_write": False}
            emit(
                "family",
                family="Proteção dos motores",
                state="error",
                message="A preparação local da proteção falhou; a instalação permanece bloqueada.",
                database_write=False,
            )
    else:
        motor_protection = {
            "ready": False,
            "reason": "há dados novos ou alterados que precisam ser resolvidos antes de certificar a base dos motores",
            "database_write": False,
        }
        emit(
            "family",
            family="Proteção dos motores",
            state="review",
            message="Resolva primeiro os dados novos ou alterados; a instalação permanece bloqueada.",
            database_write=False,
        )
    # O HTML é derivado do resultado já gravado. Ele não relê jogo, contrato
    # nem banco, e mantém o JSON apenas como artefato técnico interno.
    rendered_review = review_html.render_saved_result(result_path)
    emit("progress", stage="Conferência concluída", percent=100)
    emit(
        "complete",
        state="completed",
        result_path=str(result_path),
        review_html_path=rendered_review["review_html_path"],
        manifest_path=rendered_review["manifest_path"],
        application_plan_path=str(application_plan_path),
        application_ready=application_status["enabled"],
        application_state=application_status["state"],
        application_envelopes=application_status["envelope_count"],
        application_blockers=len(application_status["blockers"]),
        selection_available=application_status["selection_available"],
        selectable_count=len(application_status["selectable_items"]),
        not_selectable_count=application_status["not_selectable_count"],
        unresolved_pending_count=application_status["unresolved_pending_count"],
        historical_warning_count=application_status["historical_warning_count"],
        motor_protection_seed_ready=motor_protection["ready"],
        motor_protection_manifest_path=motor_protection.get("manifest_path"),
        database_write=False,
    )
    return 0


def load_review_package(path: str) -> tuple[dict[str, Any], dict[str, Any], str]:
    package = json.loads(Path(path).read_text(encoding="utf-8"))
    review = package.get("pacote_revisao") if isinstance(package, dict) else None
    supplied_sha = package.get("pacote_sha256") if isinstance(package, dict) else None
    if not isinstance(review, dict) or not isinstance(supplied_sha, str) or runtime.sha256_json(review) != supplied_sha:
        raise RuntimeError("pacote de revisão inválido ou hash divergente")
    return package, review, supplied_sha


def _payload_selection_index(payload: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, dict) or payload.get("schema") != "clubef-envelopes-aplicacao-v1":
        raise RuntimeError("pacote sem lista selecionável válida")
    found: dict[str, dict[str, Any]] = {}
    for family in payload.get("familias") or []:
        if not isinstance(family, dict):
            raise RuntimeError("família inválida na lista selecionável")
        for target in family.get("destinos") or []:
            if not isinstance(target, dict):
                raise RuntimeError("destino inválido na lista selecionável")
            for envelope in target.get("envelopes") or []:
                if not isinstance(envelope, dict) or not isinstance(envelope.get("selecao_id"), str):
                    raise RuntimeError("item sem código de seleção")
                selection_id = envelope["selecao_id"]
                if selection_id in found:
                    raise RuntimeError("código de seleção duplicado")
                found[selection_id] = {
                    "familia": family.get("familia"),
                    "destino_id": target.get("destino_id"),
                    "tabela": target.get("tabela"),
                    "envelope": envelope,
                }
    return found


def build_selected_review_package(package: dict[str, Any], selected_ids: list[str]) -> dict[str, Any]:
    review = package.get("pacote_revisao") if isinstance(package, dict) else None
    supplied_sha = package.get("pacote_sha256") if isinstance(package, dict) else None
    if not isinstance(review, dict) or not isinstance(supplied_sha, str) or runtime.sha256_json(review) != supplied_sha:
        raise RuntimeError("pacote-base inválido ou hash divergente")
    if not selected_ids or not all(isinstance(value, str) and value for value in selected_ids):
        raise RuntimeError("selecione pelo menos um item para enviar")
    if len(set(selected_ids)) != len(selected_ids):
        raise RuntimeError("a seleção contém itens repetidos")
    status = review.get("application_status")
    if not isinstance(status, dict) or status.get("selection_available") is not True or status.get("state") != "selection_required":
        raise RuntimeError("pacote-base não possui mudanças disponíveis para seleção")
    selected = set(selected_ids)
    payload = copy.deepcopy(review.get("application_payload"))
    available = _payload_selection_index(payload)
    unknown = sorted(selected - set(available))
    if unknown:
        raise RuntimeError("seleção contém item que não pertence ao pacote: " + ", ".join(unknown))
    for family in payload.get("familias") or []:
        for target in family.get("destinos") or []:
            target["envelopes"] = [item for item in target.get("envelopes") or [] if item.get("selecao_id") in selected]
    payload["state"] = "ready"
    selected_index = _payload_selection_index(payload)
    if set(selected_index) != selected:
        raise RuntimeError("a seleção gravada não confere com os itens pedidos")
    selected_status = {
        **copy.deepcopy(status),
        "enabled": True,
        "state": "ready",
        "selection_required": False,
        "selection_available": False,
        "selected_count": len(selected),
        "excluded_by_operator_count": len(available) - len(selected),
        "selected_ids": sorted(selected),
        "envelope_count": len(selected_index),
        "selectable_items": [item for item in status.get("selectable_items") or [] if item.get("selecao_id") in selected],
    }
    selected_review = {
        **copy.deepcopy(review),
        "application_payload": payload,
        "application_status": selected_status,
        "operator_selection": {
            "schema": "clubef-selecao-operador-v1",
            "base_package_sha256": supplied_sha,
            "selected_ids": sorted(selected),
            "selected_count": len(selected),
            "excluded_count": len(available) - len(selected),
            "database_write": False,
        },
    }
    return {
        "database_write": False,
        "pacote_revisao": selected_review,
        "pacote_sha256": runtime.sha256_json(selected_review),
    }


def select_review(args: argparse.Namespace) -> int:
    package, _, _, = load_review_package(args.select_review)
    selection = json.loads(Path(args.selection_file).read_text(encoding="utf-8"))
    if not isinstance(selection, dict) or selection.get("schema") != "clubef-selecao-operador-v1" or not isinstance(selection.get("selected_ids"), list):
        raise RuntimeError("arquivo de seleção do operador inválido")
    selected_package = build_selected_review_package(package, selection["selected_ids"])
    output_path = Path(args.run_dir) / "pacote-selecionado.json"
    plan_path = Path(args.run_dir) / "plano-selecionado.json"
    write_json(output_path, selected_package)
    selected_review = selected_package["pacote_revisao"]
    write_json(plan_path, {
        **selected_review["application_status"],
        "operator_selection": selected_review["operator_selection"],
        "payload_sha256": runtime.sha256_json(selected_review["application_payload"]),
        "database_write": False,
    })
    emit("complete", state="selection_saved", selected_package_path=str(output_path), selection_plan_path=str(plan_path), selected_count=len(selection["selected_ids"]), database_write=False)
    return 0


def validate_current_package(path: str, allow_controlled: bool = False) -> tuple[dict[str, Any], dict[str, Any], str, dict[str, Any], dict[str, str]]:
    package, review, supplied_sha = load_review_package(path)
    config = runtime.load_config(); contract = runtime.current_reading_contract(config)
    seal = runtime.reading_contract_seal(contract)
    if review.get("reading_contract") != seal: raise RuntimeError("pacote desatualizado: contrato/fontes divergentes")
    current_readiness = runtime.evaluate_sync_readiness(contract, review.get("contract_families") or {})
    missing = [role for role, item in sources(contract).items() if item.get("required", True) and not item.get("found")]
    if missing:
        raise RuntimeError("pacote não pode ser aplicado: fonte atual ausente: " + ", ".join(missing))
    if not allow_controlled:
        status = review.get("application_status")
        if not isinstance(status, dict) or status.get("enabled") is not True or status.get("state") != "ready":
            reason = "pacote sem mudanças aplicáveis"
            if isinstance(status, dict) and isinstance(status.get("blockers"), list) and status["blockers"]:
                reason = str(status["blockers"][0].get("motivo") or reason)
            raise RuntimeError("aplicação não habilitada no pacote: " + reason)
        selection = review.get("operator_selection")
        if not isinstance(selection, dict) or selection.get("schema") != "clubef-selecao-operador-v1" or not isinstance(selection.get("selected_ids"), list) or not selection["selected_ids"]:
            raise RuntimeError("pacote sem seleção explícita do operador")
        expected_payload, expected_status = build_application_payload(contract, {
            "comparison_reports": review.get("comparison_reports") or {},
            "review_gate": current_readiness,
        })
        if expected_status.get("selection_available") is not True:
            raise RuntimeError("as mudanças selecionadas deixaram de ser aplicáveis no contrato atual")
        expected_index = _payload_selection_index(expected_payload)
        actual_index = _payload_selection_index(review.get("application_payload"))
        selected_ids = set(str(value) for value in selection["selected_ids"])
        if set(actual_index) != selected_ids:
            raise RuntimeError("itens do pacote não conferem com a seleção do operador")
        for selection_id, actual in actual_index.items():
            expected = expected_index.get(selection_id)
            if expected is None or runtime.sha256_json(actual) != runtime.sha256_json(expected):
                raise RuntimeError("item selecionado não confere com a comparação física atual: " + selection_id)
        planned, _ = validate_application_payload(contract, review.get("application_payload"))
        if len(planned) != int(status.get("envelope_count") or -1) or not planned:
            raise RuntimeError("contagem de envelopes do plano não confere com o pacote")
    return package, review, supplied_sha, contract, seal


def _policy_decision(connection: Any, contract_id: str) -> dict[str, Any]:
    row = connection.execute(
        "select cobertura_aprovada,carga_autorizada,decisao from clube_novo.contrato_leitura_politica_revisao where contrato_id=%s for update",
        (contract_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("política de revisão ausente do contrato ativo")
    return {"cobertura_aprovada": row[0], "carga_autorizada": row[1], "decisao": row[2] if isinstance(row[2], dict) else {}}


def approve_review(args: argparse.Namespace) -> int:
    _, _, supplied_sha, contract, seal = validate_current_package(args.approve_review)
    psycopg, _, _ = runtime.import_psycopg(); dsn = runtime.connection_string()
    if not dsn: raise RuntimeError("conexão segura com clube_novo indisponível")
    decision = {"estado":"aprovado_no_extrator","pacote_sha256":supplied_sha,"contrato":seal}
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        connection.execute("update clube_novo.contrato_leitura_politica_revisao set cobertura_aprovada=true,carga_autorizada=true,decisao=%s::jsonb,atualizado_em=now() where contrato_id=%s", (json.dumps(decision, ensure_ascii=False), contract["contrato_id"]))
        readback = _policy_decision(connection, contract["contrato_id"])
        if readback["decisao"] != decision or not readback["cobertura_aprovada"] or not readback["carga_autorizada"]:
            raise RuntimeError("readback da decisão de aprovação divergente")
        if args.test_rollback:
            connection.rollback()
            emit("complete", state="approval_test_rolled_back", database_write=False, metadata_contract_write=False, package_sha256=supplied_sha)
            return 0
        connection.commit()
    emit("complete", state="approved_for_application", database_write=False, metadata_contract_write=True, package_sha256=supplied_sha)
    return 0


def reset_test_approval(args: argparse.Namespace) -> int:
    _, _, supplied_sha, contract, _ = validate_current_package(args.reset_test_approval)
    psycopg, _, _ = runtime.import_psycopg(); dsn = runtime.connection_string()
    if not dsn: raise RuntimeError("conexão segura com clube_novo indisponível")
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        current = _policy_decision(connection, contract["contrato_id"])
        decision = current["decisao"]
        if decision.get("estado") != "aprovado_no_extrator" or decision.get("pacote_sha256") != supplied_sha:
            raise RuntimeError("recusa restaurar: a decisão atual não pertence a este pacote")
        waiting = {"estado": "aguarda_aprovacao_no_extrator", "regra": "a UI do Extrator apresenta o pacote de revisão; aceite interno autoriza somente o pacote selado"}
        connection.execute("update clube_novo.contrato_leitura_politica_revisao set cobertura_aprovada=false,carga_autorizada=false,decisao=%s::jsonb,atualizado_em=now() where contrato_id=%s", (json.dumps(waiting, ensure_ascii=False), contract["contrato_id"]))
        if _policy_decision(connection, contract["contrato_id"])["decisao"] != waiting:
            raise RuntimeError("readback da restauração de teste divergente")
        connection.commit()
    emit("complete", state="test_approval_restored", database_write=False, metadata_contract_write=True, package_sha256=supplied_sha)
    return 0


IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]{1,62}$")


def control_payload_from_contract(contract: dict[str, Any]) -> dict[str, Any]:
    """Pacote vazio, mas estruturalmente completo, para ensaio com rollback."""
    families: list[dict[str, Any]] = []
    for writer in contract.get("escritores_dominio") or []:
        if not isinstance(writer, dict):
            raise RuntimeError("pedido contém escritor declarativo inválido")
        targets = writer.get("destinos")
        if not isinstance(targets, list) or not targets:
            raise RuntimeError(f"escritor sem destinos: {writer.get('escritor_id')}")
        families.append({
            "familia": writer.get("familia"),
            "escritor_id": writer.get("escritor_id"),
            "destinos": [{"destino_id": target.get("destino_id"), "envelopes": []} for target in targets if isinstance(target, dict)],
        })
    return {"schema": "clubef-envelopes-aplicacao-v1", "familias": families, "state": "controlled_rollback_only"}


def _type_matches(value: Any, declared: str) -> bool:
    if value is None:
        return True
    if declared in ("smallint", "integer", "bigint"):
        return isinstance(value, int) and not isinstance(value, bool)
    if declared in ("text", "character varying"):
        return isinstance(value, str)
    if declared == "boolean":
        return isinstance(value, bool)
    if declared in ("json", "jsonb"):
        return isinstance(value, (dict, list))
    if declared == "ARRAY":
        return isinstance(value, list)
    return True  # tipos de data/hora só são aceitos pelo adaptador PostgreSQL.


def validate_application_payload(contract: dict[str, Any], payload: Any) -> tuple[list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]], dict[str, Any]]:
    """Valida envelope contra o plano retornado pelo banco, sem tabela/família fixa.

    Retorna triplas (escritor, destino, envelope) para o executor genérico.
    """
    if not isinstance(payload, dict) or payload.get("schema") != "clubef-envelopes-aplicacao-v1":
        raise RuntimeError("payload de aplicação sem schema de envelope suportado")
    declared = contract.get("escritores_dominio")
    received = payload.get("familias")
    if not isinstance(declared, list) or not declared or not isinstance(received, list):
        raise RuntimeError("payload sem escritores/famílias declarados pelo contrato")
    by_family = {str(item.get("familia")): item for item in declared if isinstance(item, dict)}
    by_received = {str(item.get("familia")): item for item in received if isinstance(item, dict)}
    if len(by_received) != len(received) or set(by_received) != set(by_family):
        raise RuntimeError("payload não cobre exatamente as famílias de escritores declaradas")
    planned: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    audit: dict[str, Any] = {"familias": {}}
    for family, writer in by_family.items():
        supplied = by_received[family]
        if supplied.get("escritor_id") != writer.get("escritor_id"):
            raise RuntimeError(f"payload selecionou escritor divergente para família {family}")
        targets = writer.get("destinos")
        supplied_targets = supplied.get("destinos")
        if not isinstance(targets, list) or not isinstance(supplied_targets, list):
            raise RuntimeError(f"destinos ausentes para família {family}")
        planned_targets = {str(target.get("destino_id")): target for target in targets if isinstance(target, dict)}
        received_targets = {str(target.get("destino_id")): target for target in supplied_targets if isinstance(target, dict)}
        if len(received_targets) != len(supplied_targets) or set(received_targets) != set(planned_targets):
            raise RuntimeError(f"payload não cobre exatamente os destinos declarados da família {family}")
        family_count = 0
        for target_id, target in planned_targets.items():
            if target.get("schema") != "clube_novo" or not IDENTIFIER_RE.fullmatch(str(target.get("tabela") or "")):
                raise RuntimeError(f"destino não permitido pelo contrato: {target_id}")
            item = received_targets[target_id]
            envelopes = item.get("envelopes")
            if not isinstance(envelopes, list):
                raise RuntimeError(f"envelopes inválidos para destino {target_id}")
            keys = target.get("colunas_chave")
            writable = target.get("colunas_escrita")
            types = target.get("tipos_colunas")
            if not isinstance(keys, list) or not isinstance(writable, list) or not isinstance(types, dict):
                raise RuntimeError(f"contrato incompleto para destino {target_id}")
            allowed = set(writable) | set(keys)
            for envelope in envelopes:
                if not isinstance(envelope, dict):
                    raise RuntimeError(f"envelope não-objeto em {family}/{target_id}")
                identity, values, provenance = envelope.get("identidade"), envelope.get("valores"), envelope.get("procedencia")
                if envelope.get("operacao") != "upsert":
                    raise RuntimeError(f"operação não autorizada em {family}/{target_id}")
                if not isinstance(identity, dict) or not isinstance(values, dict) or (target.get("exige_procedencia") and (not isinstance(provenance, dict) or not provenance)):
                    raise RuntimeError(f"envelope sem identidade/valores/procedência em {family}/{target_id}")
                if not values or not set(values).issubset(allowed):
                    raise RuntimeError(f"envelope contém coluna não autorizada ou não possui valores em {family}/{target_id}")
                for key in keys:
                    if key not in identity or key not in values or identity[key] != values[key]:
                        raise RuntimeError(f"chave canônica divergente ou ausente ({key}) em {family}/{target_id}")
                for column, value in values.items():
                    declared_type = types.get(column)
                    if not isinstance(declared_type, str) or not _type_matches(value, declared_type):
                        raise RuntimeError(f"tipo incompatível para {family}/{target_id}/{column}: esperado {declared_type}")
                planned.append((writer, target, envelope)); family_count += 1
        audit["familias"][family] = {"escritor_id": writer.get("escritor_id"), "destinos": len(planned_targets), "envelopes": family_count}
    return planned, audit


def apply_declared_envelopes(connection: Any, sql: Any, planned: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]) -> dict[str, int]:
    """UPSERT genérico: identificadores e colunas vêm apenas do contrato já validado."""
    applied: dict[str, int] = {}
    for _, target, envelope in sorted(planned, key=lambda item: (int(item[1].get("ordem_lote", 100)), str(item[1].get("destino_id")))):
        table = str(target["tabela"]); keys = [str(key) for key in target["colunas_chave"]]
        values = envelope["valores"]
        columns = sorted(values)
        updates = [column for column in columns if column not in keys]
        insert = sql.SQL("insert into {}.{} ({}) values ({}) on conflict ({}) do {}")
        if updates:
            update_clause = sql.SQL("update set {}").format(sql.SQL(", ").join(sql.SQL("{} = excluded.{}").format(sql.Identifier(column), sql.Identifier(column)) for column in updates))
        else:
            update_clause = sql.SQL("nothing")
        query = insert.format(
            sql.Identifier(str(target["schema"])), sql.Identifier(table),
            sql.SQL(", ").join(sql.Identifier(column) for column in columns),
            sql.SQL(", ").join(sql.Placeholder() for _ in columns),
            sql.SQL(", ").join(sql.Identifier(key) for key in keys),
            update_clause,
        )
        connection.execute(query, tuple(values[column] for column in columns))
        applied[table] = applied.get(table, 0) + 1
    return applied


def readback_declared_envelopes(connection: Any, sql: Any, planned: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]) -> dict[str, Any]:
    """Relê por SELECT todas as colunas gravadas e compara valor por valor."""
    digest = hashlib.sha256()
    rows_checked = 0
    by_table: dict[str, int] = {}
    for _, target, envelope in sorted(planned, key=lambda item: (str(item[1].get("destino_id")), json.dumps(item[2].get("identidade"), sort_keys=True, default=str))):
        table = str(target["tabela"]); keys = [str(key) for key in target["colunas_chave"]]
        values = envelope["valores"]
        columns = sorted(values)
        query = sql.SQL("select {} from {}.{} where {}")
        query = query.format(
            sql.SQL(", ").join(sql.Identifier(column) for column in columns),
            sql.Identifier(str(target["schema"])),
            sql.Identifier(table),
            sql.SQL(" and ").join(sql.SQL("{} = {}").format(sql.Identifier(key), sql.Placeholder()) for key in keys),
        )
        rows = connection.execute(query, tuple(envelope["identidade"][key] for key in keys)).fetchall()
        if len(rows) != 1:
            raise RuntimeError(f"readback independente não encontrou uma linha única em {target['destino_id']}")
        observed = dict(zip(columns, rows[0], strict=True))
        differences = [column for column in columns if observed[column] != values[column]]
        if differences:
            raise RuntimeError(f"readback independente divergiu em {target['destino_id']}: {', '.join(differences)}")
        canonical = {"destino_id": target.get("destino_id"), "identidade": envelope["identidade"], "valores": observed}
        digest.update(json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8"))
        digest.update(b"\n")
        rows_checked += 1
        by_table[table] = by_table.get(table, 0) + 1
    return {"rows_checked": rows_checked, "tables": by_table, "sha256": digest.hexdigest()}


def apply_review(args: argparse.Namespace) -> int:
    """Aplica exclusivamente um pacote aprovado, numa única transação.

    Os dados de domínio ainda entram somente por envelopes tipados por família.
    Assim, pacote que contenha apenas relatório de comparação não pode causar
    uma escrita parcial ou uma dedução de destino/rótulo pelo código.
    """
    _, review, supplied_sha, contract, seal = validate_current_package(args.apply_review, allow_controlled=bool(args.test_rollback))
    readiness = runtime.evaluate_sync_readiness(contract, review.get("contract_families") or {})
    psycopg, sql, _ = runtime.import_psycopg(); dsn = runtime.connection_string()
    if not dsn: raise RuntimeError("conexão segura com clube_novo indisponível")
    source_manifest = {role: {"found": bool(item.get("found")), "contract_fingerprint": seal["fingerprint_fontes_sha256"]} for role, item in sources(contract).items()}
    idempotency_key = "extractor-review:" + supplied_sha
    family_audit = {"families": review.get("contract_families") or {}, "comparison_report_sha256": runtime.sha256_json(review.get("comparison_reports") or {})}
    controlled = bool(args.test_rollback)
    payload = review.get("application_payload") if isinstance(review.get("application_payload"), dict) else None
    if controlled and (not isinstance(payload, dict) or not payload.get("familias")):
        payload = control_payload_from_contract(contract)
    planned, writer_audit = validate_application_payload(contract, payload)
    if not controlled:
        if runtime.PRODUCTIVE_WRITES_LOCKED:
            raise RuntimeError("aplicação produtiva permanece bloqueada no desenvolvimento")
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        policy = _policy_decision(connection, contract["contrato_id"])
        decision = policy["decisao"]
        if not policy["cobertura_aprovada"] or not policy["carga_autorizada"] or decision.get("estado") != "aprovado_no_extrator" or decision.get("pacote_sha256") != supplied_sha or decision.get("contrato") != seal:
            raise RuntimeError("aplicação recusada: aprovação interna não corresponde ao pacote/contrato atual")
        staged = connection.execute(
            "select (clube_novo.estagiar_execucao_leitura_contrato(%s,%s,%s,%s,%s,%s,%s::jsonb)).execucao_id",
            (idempotency_key, contract["contrato_id"], seal["versao_jogo"], seal["fingerprint_contrato_sha256"], seal["fingerprint_fontes_sha256"], supplied_sha, json.dumps(source_manifest, ensure_ascii=False)),
        ).fetchone()
        if staged is None or staged[0] is None:
            raise RuntimeError("estágio transacional do pacote não retornou execução")
        family_audit["escritores"] = writer_audit
        family_audit["payload_sha256"] = runtime.sha256_json(payload)
        application = connection.execute(
            """insert into clube_novo.aplicacao_pacote_revisao_extrator
               (idempotency_key,execucao_id,contrato_id,pacote_sha256,selo_contrato,manifesto_fontes,cobertura_familias,auditoria_familias,estado)
               values (%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,'aplicado') returning aplicacao_id""",
            (idempotency_key, staged[0], contract["contrato_id"], supplied_sha, json.dumps(seal, ensure_ascii=False), json.dumps(source_manifest, ensure_ascii=False), json.dumps(readiness["families"], ensure_ascii=False), json.dumps(family_audit, ensure_ascii=False)),
        ).fetchone()
        readback = connection.execute("select pacote_sha256,contrato_id,estado from clube_novo.aplicacao_pacote_revisao_extrator where aplicacao_id=%s", (application[0],)).fetchone()
        if readback != (supplied_sha, contract["contrato_id"], "aplicado"):
            raise RuntimeError("readback de auditoria de aplicação divergente")
        if controlled:
            connection.rollback()
            emit("complete", state="application_test_rolled_back", database_write=False, data_domain_write=False, package_sha256=supplied_sha, audit_readback=True, writers=writer_audit)
            return 0
        applied = apply_declared_envelopes(connection, sql, planned)
        precommit_readback = readback_declared_envelopes(connection, sql, planned)
        connection.commit()
    with psycopg.connect(dsn, connect_timeout=20) as verify_connection:
        postcommit_readback = readback_declared_envelopes(verify_connection, sql, planned)
    if precommit_readback != postcommit_readback:
        raise RuntimeError("readback pós-commit divergiu da conferência transacional")
    emit(
        "complete",
        state="applied",
        database_write=True,
        package_sha256=supplied_sha,
        audit_readback=True,
        envelopes_applied=applied,
        independent_readback=postcommit_readback,
    )
    return 0


def render_review_html(args: argparse.Namespace) -> int:
    """Gera a leitura humana de um resultado existente sem iniciar varredura."""
    rendered = review_html.render_saved_result(Path(args.render_review_html))
    emit("complete", state="review_html_generated", result_path=args.render_review_html, **rendered)
    return 0


def test_database_connection(args: argparse.Namespace) -> int:
    """Confirma credencial em uma transação que o próprio Postgres marca read-only."""
    run_dir = Path(args.run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    report_path = run_dir / "teste-conexao-banco.json"
    dsn = runtime.connection_string()
    if not dsn:
        message = (
            "Nenhuma connection string protegida foi entregue ao processo. "
            "Use CONFIGURAR CONEXÃO na janela do Extrator."
        )
        write_compact_json(
            report_path,
            {
                "schema": "clubef-teste-conexao-banco-v1",
                "tested_at": datetime.now(timezone.utc).isoformat(),
                "state": "blocked",
                "transaction_read_only": False,
                "database_write": False,
                "message": message,
            },
        )
        emit("connection_test", ok=False, message=message, database_write=False)
        return 2

    try:
        psycopg, _, _ = runtime.import_psycopg()
        with psycopg.connect(dsn, connect_timeout=20) as connection:
            connection.read_only = True
            with connection.cursor() as cursor:
                cursor.execute("show transaction_read_only")
                read_only = str(cursor.fetchone()[0]).lower() == "on"
                if not read_only:
                    raise RuntimeError("o Postgres não confirmou a transação somente leitura")
                cursor.execute("select 1")
                readback = int(cursor.fetchone()[0])
                if readback != 1:
                    raise RuntimeError("a leitura de confirmação não devolveu o valor esperado")
            connection.rollback()
        payload = {
            "schema": "clubef-teste-conexao-banco-v1",
            "tested_at": datetime.now(timezone.utc).isoformat(),
            "state": "connected_read_only",
            "transaction_read_only": True,
            "readback": 1,
            "database_write": False,
            "message": "Conexão confirmada em modo somente leitura. Nenhum dado foi alterado.",
        }
        write_compact_json(report_path, payload)
        emit(
            "connection_test",
            ok=True,
            transaction_read_only=True,
            readback=1,
            database_write=False,
            message=payload["message"],
        )
        return 0
    except Exception as error:
        message = _safe_database_connection_error(error)
        write_compact_json(
            report_path,
            {
                "schema": "clubef-teste-conexao-banco-v1",
                "tested_at": datetime.now(timezone.utc).isoformat(),
                "state": "failed",
                "transaction_read_only": True,
                "database_write": False,
                "message": message,
            },
        )
        emit(
            "connection_test",
            ok=False,
            transaction_read_only=True,
            database_write=False,
            message=message,
        )
        return 2


def refresh_saved_motor_readiness(args: argparse.Namespace) -> int:
    """Recalcula apenas o gate local após uma marcação do operador.

    A fotografia física e ``resultado.json`` permanecem imutáveis. Somente os
    artefatos derivados de prontidão e o HTML são refeitos; não há conexão nem
    escrita no banco.
    """
    root = Path(args.root).resolve()
    run_dir = Path(args.run_dir).resolve()
    result_path = run_dir / "resultado.json"
    physical_path = run_dir / "fisico.json"
    required = {
        "resultado.json": result_path,
        "fisico.json": physical_path,
        "cartas-fisicas-canonicas.json": run_dir / "cartas-fisicas-canonicas.json",
        "dimensoes-fisicas.json": run_dir / "dimensoes-fisicas.json",
        "metadados-fisicos.json": run_dir / "metadados-fisicos.json",
    }
    missing = [name for name, path in required.items() if not path.is_file()]
    if missing:
        raise RuntimeError("não foi possível atualizar a prontidão; artefatos ausentes: " + ", ".join(missing))
    original_result = json.loads(result_path.read_text(encoding="utf-8-sig"))
    physical = json.loads(physical_path.read_text(encoding="utf-8-sig"))
    cards = iter_json_array_file(required["cartas-fisicas-canonicas.json"])
    dimensions = json.loads(required["dimensoes-fisicas.json"].read_text(encoding="utf-8-sig"))
    metadata = json.loads(required["metadados-fisicos.json"].read_text(encoding="utf-8-sig"))
    override_path = root / "artefatos" / "estado-operador" / "prontidao-motores-operador.json"
    overrides = json.loads(override_path.read_text(encoding="utf-8-sig")) if override_path.is_file() else None
    family_fingerprints = {
        name: seal.get("fingerprint_familia")
        for name, seal in (physical.get("family_seals") or {}).items()
        if isinstance(seal, dict) and seal.get("fingerprint_familia")
    }
    artifact = card_completeness.build_artifact(
        cards,
        dimensions,
        metadata,
        contract_seal=original_result.get("contract_seal") if isinstance(original_result.get("contract_seal"), dict) else {},
        source_seal={
            "physical_reader": physical.get("physical_reader"),
            "family_fingerprints": family_fingerprints,
        },
        operator_overrides=overrides,
    )
    readiness_path = run_dir / "prontidao-motores.json"
    summary_path = run_dir / "resumo-prontidao-motores.json"
    operator_review_path = run_dir / "revisao-prontidao-motores.json"
    write_compact_json(readiness_path, artifact)
    write_compact_json(operator_review_path, card_completeness.build_operator_review(artifact))
    summary = artifact.get("summary") or {}
    write_json(summary_path, {
        "schema": "clubef-prontidao-motores-resumo-v1",
        "regra_completude": artifact.get("regra_completude"),
        "gerado_em": artifact.get("gerado_em"),
        "database_write": False,
        "publicacao_independente": True,
        "publicacao_bloqueada_por_este_gate": False,
        "semantica_ausencia": artifact.get("semantica_ausencia"),
        "summary": summary,
    })
    application_status = original_result.get("application_status") or {}
    motor_protection: dict[str, Any]
    if application_status.get("state") == "no_changes":
        try:
            motor_protection = prepare_motor_protection_seed(run_dir)
        except Exception as error:
            motor_protection = {"ready": False, "reason": str(error), "database_write": False}
    else:
        motor_protection = {
            "ready": False,
            "reason": "a execução não terminou sem mudanças de dados",
            "database_write": False,
        }
    rendered = review_html.render_saved_result(result_path)
    emit(
        "complete",
        state="motor_readiness_refreshed",
        source_result_unchanged=True,
        motor_readiness_path=str(readiness_path),
        operator_review_path=str(operator_review_path),
        motor_eligible=int(summary.get("motor_eligible") or 0),
        aguardando_insumos=int(summary.get("aguardando_insumos") or 0),
        marcacoes_operador=int(summary.get("marcacoes_operador") or 0),
        motor_protection_seed_ready=motor_protection["ready"],
        motor_protection_manifest_path=motor_protection.get("manifest_path"),
        **rendered,
    )
    return 0


def preview_motor_protection(args: argparse.Namespace) -> int:
    """Confirma contrato, cartas e impacto atual sem permitir escrita."""
    root = Path(args.root).resolve()
    run_dir = Path(args.run_dir).resolve()
    dsn = runtime.connection_string()
    if not dsn:
        raise RuntimeError("conexão protegida indisponível; use CONFIGURAR CONEXÃO")
    config = runtime.load_config()
    contract = runtime.current_reading_contract(config)
    revalidate_saved_no_changes(root, run_dir, config, contract, reason="previa")
    report = motor_protection_installer.preview_motor_protection(
        root,
        run_dir,
        Path(args.preview_motor_protection),
        contract,
        dsn,
    )
    emit(
        "complete",
        state=(
            "motor_protection_already_up_to_date"
            if report["state"] == "already_up_to_date"
            else "motor_protection_preview_ready"
        ),
        database_write=False,
        transaction_read_only=True,
        publication_blocked=False,
        results_to_invalidate=report["preview"]["results_to_invalidate"],
        cards=report["cards"],
        cards_to_register=report["preview"]["cards_to_register"],
        operation_mode=report["preview"]["operation_mode"],
        confirmation_sha256=report["confirmation_sha256"],
        report_path=report["report_path"],
    )
    return 0


def install_motor_protection(args: argparse.Namespace) -> int:
    """Executa somente a ação produtiva separada confirmada pela UI."""
    if runtime.PRODUCTIVE_WRITES_LOCKED:
        raise RuntimeError("instalação produtiva bloqueada fora do botão dedicado")
    root = Path(args.root).resolve()
    run_dir = Path(args.run_dir).resolve()
    if not args.confirmation_sha256:
        raise RuntimeError("a prévia confirmada não foi informada")
    manifest_path = Path(args.install_motor_protection).resolve()
    authorization = consume_operator_write_authorization(
        root,
        run_dir,
        manifest_path,
        args.confirmation_sha256,
        args.operator_write_authorization,
    )
    dsn = runtime.connection_string()
    if not dsn:
        raise RuntimeError("conexão protegida indisponível; use CONFIGURAR CONEXÃO")
    config = runtime.load_config()
    contract = runtime.current_reading_contract(config)
    revalidate_saved_no_changes(root, run_dir, config, contract, reason="instalacao")
    report = motor_protection_installer.install_motor_protection(
        root,
        run_dir,
        manifest_path,
        contract,
        dsn,
        confirmed_preview_sha256=args.confirmation_sha256,
        operator_authorization_sha256=authorization["sha256"],
    )
    if report["state"] == "already_up_to_date":
        emit(
            "complete",
            state="motor_protection_already_up_to_date",
            database_write=False,
            publication_blocked=False,
            cards_to_register=0,
            report_path=report["report_path"],
        )
        return 0
    emit(
        "complete",
        state="motor_protection_installed_or_updated",
        database_write=True,
        publication_blocked=False,
        separate_from_data_package_apply=True,
        application_id=report["installed"]["application_id"],
        operation_mode=report["installed"]["operation_mode"],
        cards_registered=report["installed"]["cards_registered"],
        results_invalidated=report["installed"]["results_invalidated"],
        independent_readback=True,
        report_path=report["report_path"],
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--cancel", required=True)
    parser.add_argument("--protocol-version", required=True)
    parser.add_argument("--approve-review")
    parser.add_argument("--apply-review")
    parser.add_argument("--select-review")
    parser.add_argument("--selection-file")
    parser.add_argument("--reset-test-approval")
    parser.add_argument("--render-review-html")
    parser.add_argument("--refresh-motor-readiness", action="store_true")
    parser.add_argument("--test-database-connection", action="store_true")
    parser.add_argument("--preview-motor-protection")
    parser.add_argument("--install-motor-protection")
    parser.add_argument("--confirmation-sha256")
    parser.add_argument("--operator-write-authorization")
    parser.add_argument("--smoke-stage-habilidades", action="store_true")
    parser.add_argument("--smoke-stage-habilidades-limite", type=int, default=0)
    parser.add_argument("--test-rollback", action="store_true")
    args = parser.parse_args()
    if args.protocol_version != DESKTOP_WORKER_PROTOCOL_VERSION:
        emit(
            "fatal",
            message=(
                "versão incompatível entre launcher e worker: launcher="
                + args.protocol_version
                + "; worker="
                + DESKTOP_WORKER_PROTOCOL_VERSION
            ),
            database_write=False,
        )
        return 1
    try:
        if args.test_database_connection: return test_database_connection(args)
        if args.preview_motor_protection: return preview_motor_protection(args)
        if args.install_motor_protection: return install_motor_protection(args)
        if args.render_review_html: return render_review_html(args)
        if args.refresh_motor_readiness: return refresh_saved_motor_readiness(args)
        if args.smoke_stage_habilidades: return smoke_stage_skill_envelopes(args)
        if args.select_review:
            if not args.selection_file: raise RuntimeError("arquivo de seleção não informado")
            return select_review(args)
        if args.approve_review: return approve_review(args)
        if args.apply_review: return apply_review(args)
        if args.reset_test_approval: return reset_test_approval(args)
        return run(args)
    except Exception as error:
        emit(
            "fatal",
            message=str(error),
            traceback=traceback.format_exc(),
            database_write=bool(getattr(error, "database_write", False)),
            commit_status=getattr(error, "commit_status", None),
        )
        return 130 if str(error) == "cancelled_by_user" else 1


if __name__ == "__main__":
    raise SystemExit(main())
