"""Camada local de revisão do Extrator V4.6.11.

Toda rodada é registrada em disco antes de qualquer escrita. O token devolvido
após a confirmação do usuário só autoriza a família explicitamente revisada.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

REVIEW_CONTRACT = "clubef-extractor-review-v1"
ACKNOWLEDGEMENT_PHRASE = "REVISEI AS DIVERGENCIAS"
_ALLOWED_KINDS = {"metadata", "cards", "full", "family"}
_LOCK = RLock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _safe_identifier(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value or "")).strip("-._")
    return (cleaned or fallback)[:120]


def review_root(root: Path) -> Path:
    path = Path(root) / "revisoes-pendentes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _review_path(root: Path, review_id: str) -> Path:
    return review_root(root) / f"{_safe_identifier(review_id, 'revisao')}.json"


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            if os.path.exists(temporary):
                os.unlink(temporary)
        except OSError:
            pass


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("contract") != REVIEW_CONTRACT:
        raise ValueError("arquivo de revisão local incompatível")
    return data


def _public(record: dict[str, Any]) -> dict[str, Any]:
    result = dict(record)
    result.pop("review_token_sha256", None)
    result["review_file"] = str(record.get("review_file") or "")
    return result


def stage_review(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("pacote de revisão ausente")
    kind = str(payload.get("kind") or "").strip()
    if kind not in _ALLOWED_KINDS:
        raise ValueError(f"tipo de revisão inválido: {kind or 'ausente'}")
    manifest = payload.get("manifest")
    if payload.get("database_write") is True:
        raise ValueError("uma revisão local nunca pode declarar escrita no banco")
    if isinstance(manifest, dict) and manifest.get("database_write") is True:
        raise ValueError("manifesto de revisão declarou escrita no banco")

    execution_id = _safe_identifier(
        str(
            payload.get("execution_id")
            or (manifest or {}).get("execution_id")
            or secrets.token_hex(8)
        ),
        secrets.token_hex(8),
    )
    payload_for_hash = {
        key: value
        for key, value in payload.items()
        if key not in {"leitura_contrato", "review_token", "review_id"}
    }
    payload_sha256 = _sha256(payload_for_hash)
    review_id = _safe_identifier(
        str(payload.get("review_id") or f"{kind}-{execution_id}-{payload_sha256[:12]}"),
        f"{kind}-{payload_sha256[:12]}",
    )
    path = _review_path(root, review_id)

    with _LOCK:
        previous: dict[str, Any] | None = None
        if path.is_file():
            try:
                previous = _load(path)
            except Exception:
                previous = None

        record: dict[str, Any] = {
            "contract": REVIEW_CONTRACT,
            "review_id": review_id,
            "kind": kind,
            "execution_id": execution_id,
            "created_at": (
                previous.get("created_at")
                if previous and previous.get("payload_sha256") == payload_sha256
                else _now()
            ),
            "updated_at": _now(),
            "status": (
                previous.get("status")
                if previous
                and previous.get("payload_sha256") == payload_sha256
                and previous.get("status") == "reviewed"
                else "pending_review"
            ),
            "database_write": False,
            "payload_sha256": payload_sha256,
            "payload": payload_for_hash,
            "review_file": str(path),
        }
        if record["status"] == "reviewed" and previous:
            record["reviewed_at"] = previous.get("reviewed_at")
            record["review_token_sha256"] = previous.get("review_token_sha256")
        _atomic_write(path, record)

    return _public(record)


def get_review(root: Path, review_id: str) -> dict[str, Any]:
    path = _review_path(root, review_id)
    if not path.is_file():
        raise FileNotFoundError(f"revisão local não encontrada: {review_id}")
    with _LOCK:
        return _public(_load(path))


def latest_review(root: Path, kind: str | None = None) -> dict[str, Any] | None:
    candidates: list[dict[str, Any]] = []
    with _LOCK:
        for path in review_root(root).glob("*.json"):
            try:
                record = _load(path)
            except Exception:
                continue
            if kind and record.get("kind") != kind:
                continue
            candidates.append(record)
    if not candidates:
        return None
    candidates.sort(
        key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""),
        reverse=True,
    )
    return _public(candidates[0])


def acknowledge_review(
    root: Path,
    review_id: str,
    phrase: str,
) -> dict[str, Any]:
    if str(phrase or "").strip() != ACKNOWLEDGEMENT_PHRASE:
        raise PermissionError(
            f"confirmação de revisão incorreta; digite {ACKNOWLEDGEMENT_PHRASE}"
        )
    path = _review_path(root, review_id)
    if not path.is_file():
        raise FileNotFoundError(f"revisão local não encontrada: {review_id}")

    token = secrets.token_urlsafe(32)
    with _LOCK:
        record = _load(path)
        record["status"] = "reviewed"
        record["reviewed_at"] = _now()
        record["updated_at"] = record["reviewed_at"]
        record["review_token_sha256"] = hashlib.sha256(token.encode("utf-8")).hexdigest()
        _atomic_write(path, record)

    public = _public(record)
    public["review_token"] = token
    public["acknowledgement_phrase"] = ACKNOWLEDGEMENT_PHRASE
    return public


def verify_review(
    root: Path,
    review_id: str,
    review_token: str,
    *,
    expected_kind: str | None = None,
    family: str | None = None,
) -> dict[str, Any]:
    if not review_id or not review_token:
        raise PermissionError(
            "envio bloqueado: abra a revisão, confira as divergências e confirme a leitura"
        )
    path = _review_path(root, review_id)
    if not path.is_file():
        raise PermissionError("envio bloqueado: revisão local não encontrada")

    with _LOCK:
        record = _load(path)
    if record.get("status") != "reviewed":
        raise PermissionError("envio bloqueado: esta rodada ainda não foi revisada")
    expected_hash = str(record.get("review_token_sha256") or "")
    received_hash = hashlib.sha256(str(review_token).encode("utf-8")).hexdigest()
    if not expected_hash or not secrets.compare_digest(expected_hash, received_hash):
        raise PermissionError("envio bloqueado: autorização da revisão é inválida")
    if expected_kind and record.get("kind") != expected_kind:
        raise PermissionError(
            f"envio bloqueado: revisão {record.get('kind')} não autoriza {expected_kind}"
        )

    application = (record.get("payload") or {}).get("application") or {}
    blocked = {str(item) for item in application.get("blocked_families") or []}
    allowed = {str(item) for item in application.get("allowed_families") or []}
    if family and family in blocked:
        raise PermissionError(
            f"envio bloqueado: a família {family} possui divergências nesta rodada"
        )
    if family and allowed and family not in allowed:
        raise PermissionError(
            f"envio bloqueado: a família {family} não foi liberada pela revisão"
        )
    return _public(record)
