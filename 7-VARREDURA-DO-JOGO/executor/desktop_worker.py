"""Coordenador sem interface do Extrator Desktop.

O processo recebe o pedido de leitura do banco em transação read-only, chama o
leitor físico isolado e compara cada família sem permitir qualquer aplicação.
Ele fala JSONL somente com a janela WinForms; não inicia HTTP nem navegador.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import executor_local as runtime


def emit(event_type: str, **payload: Any) -> None:
    print(json.dumps({"type": event_type, "at": datetime.now(timezone.utc).isoformat(), **payload}, ensure_ascii=False), flush=True)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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


def sources() -> dict[str, dict[str, Any]]:
    discovered: dict[str, dict[str, Any]] = {}
    for role, definition in runtime.source_definitions().items():
        item = runtime.inspect_source(role, definition)
        if item.get("found"):
            item["sha256"] = None  # o hash físico é conferido pelo contrato no leitor.
        discovered[role] = item
    return discovered


def summarize(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "passed": bool(value.get("passed")),
        "database_write": False,
        "counts": value.get("counts") or value.get("comparisons") or value.get("summary") or {},
        "error": value.get("error"),
    }


def compare_family(name: str, action: Callable[[], dict[str, Any]], result: dict[str, Any]) -> None:
    emit("family", family=name, state="running", message="Comparação com clube_novo em transação somente leitura.")
    try:
        value = action()
        passed = bool(value.get("passed", False))
        result["comparisons"][name] = summarize(value)
        result["families"][name] = {"state": "equal" if passed else "divergent", "database_write": False}
        emit("family", family=name, state="equal" if passed else "divergent", message="Conferido com o banco; nenhuma escrita foi feita.")
    except Exception as error:  # Uma família nunca impede a comparação das próximas.
        message = str(error)
        result["comparisons"][name] = {"passed": False, "database_write": False, "error": message}
        result["families"][name] = {"state": "error", "database_write": False, "error": message}
        emit("family", family=name, state="error", message=message)


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
    discovered = sources()
    missing = [role for role, item in discovered.items() if not item.get("found")]
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
    baseline_path = run_dir / "baseline-cartas.csv"
    physical_path = run_dir / "fisico.json"
    write_json(plan_path, contract)
    write_json(source_path, discovered)
    try:
        baseline, baseline_info = runtime.current_card_baseline(config, contract)
        baseline_path.write_bytes(baseline)
        emit("log", message=f"Baseline read-only: {baseline_info.get('records', 0)} cartas.")
    except Exception as error:
        # Cartas pode falhar, mas a leitura física das demais famílias continua.
        baseline_path.write_text("card_id\n", encoding="utf-8")
        emit("family", family="Cartas", state="error", message=f"Baseline indisponível: {error}")

    command = [find_node() or "node", str(root / "executor" / "desktop_physical_worker.js"), "--root", str(root), "--plan", str(plan_path), "--sources", str(source_path), "--baseline", str(baseline_path), "--output", str(physical_path), "--cancel", str(cancel_path)]
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
    result: dict[str, Any] = {**physical, "state": "completed", "database_write": False, "comparisons": {}}
    cards_path = Path(str((physical.get("artifacts") or {}).get("cards_csv", "")))
    dimensions_path = Path(str((physical.get("artifacts") or {}).get("dimensions", "")))
    metadata_path = Path(str((physical.get("artifacts") or {}).get("metadata", "")))
    if cards_path.is_file():
        card_csv = cards_path.read_text(encoding="utf-8-sig")
        compare_family("Relações", lambda: runtime.current_card_relations_validation(card_csv, config), result)
        compare_family("Ímpetos", lambda: runtime.current_card_impetus_validation(card_csv, config, contract), result)
    if dimensions_path.is_file():
        snapshot = json.loads(dimensions_path.read_text(encoding="utf-8"))
        compare_family("Dimensões", lambda: runtime.current_card_dimensions_validation(snapshot, config), result)
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        catalogs = metadata.get("catalogs") or {}
        if isinstance(catalogs.get("impetos"), dict):
            compare_family("Ímpetos", lambda: runtime.current_impetos_validation(catalogs["impetos"], config), result)
        if isinstance(catalogs.get("tecnicos"), dict):
            compare_family("Técnicos", lambda: runtime.current_tecnicos_validation({"catalogs": catalogs}, config), result)
        if isinstance(catalogs.get("textos"), dict):
            compare_family("Textos", lambda: runtime.current_text_baseline(config), result)
    write_json(result_path, result)
    emit("progress", stage="Conferência concluída", percent=100)
    emit("complete", state="completed", result_path=str(result_path), database_write=False)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--cancel", required=True)
    args = parser.parse_args()
    try:
        return run(args)
    except Exception as error:
        emit("fatal", message=str(error), traceback=traceback.format_exc(), database_write=False)
        return 130 if str(error) == "cancelled_by_user" else 1


if __name__ == "__main__":
    raise SystemExit(main())
