"""Coordenador sem interface do Extrator Desktop.

O processo recebe o pedido de leitura do banco em transação read-only, chama o
leitor físico isolado e compara cada família sem permitir qualquer aplicação.
Ele fala JSONL somente com a janela WinForms; não inicia HTTP nem navegador.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import executor_local as runtime


DESKTOP_WORKER_PROTOCOL_VERSION = "5.0.0"


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
        state = "technical_issue" if not technical_integrity else "review" if classification_complete and value.get("exact_match") is not True else "observed"
        result["families"][name] = {"state": state, "database_write": False}
        checks[check_key] = {
            "completed": True,
            "classification_complete": classification_complete,
            "technical_integrity": technical_integrity,
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
    for card_id in sorted(physical_ids - database_ids, key=int):
        buckets["new"].append({"classificacao": "novo", "escopo": "cartas", "chave_canonica": {"card_id": card_id}, "fonte_fisica": {"card_id": card_id}})
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
            buckets["altered"].append({"classificacao": "alterado", "escopo": "cartas", "chave_canonica": {"card_id": card_id}, "fonte_fisica": {"card_id": card_id}, "vinculo_banco": {"card_id": card_id}, "campos_alterados": changed})
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
    buckets: dict[str, list[dict[str, Any]]] = {kind: [] for kind in ("new", "removed", "altered", "repeated", "invalid")}
    coverage: list[dict[str, Any]] = []
    for mapping in mappings:
        schema, table = mapping.get("schema"), mapping.get("table")
        key = (schema, table)
        db = database.get(key)
        if db is None:
            buckets["invalid"].append({"classificacao": "inválido", "escopo": "catalogos", "motivo": "catálogo solicitado ausente do pedido", "catalogo": f"{schema}.{table}"}); continue
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
    return {"classification_complete": True, "technical_integrity": technical, "exact_match": not any(buckets[k] for k in buckets), "classification": buckets, "coverage": coverage, "database_write": False}


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
    dimensions_path = Path(str((physical.get("artifacts") or {}).get("dimensions", "")))
    metadata_path = Path(str((physical.get("artifacts") or {}).get("metadata", "")))
    if cards_path.is_file():
        card_csv = cards_path.read_text(encoding="utf-8-sig")
        if dimensions_path.is_file() and canonical_baseline_path.is_file():
            compare_family("Cartas", lambda: classify_canonical_cards(cards_path, dimensions_path, canonical_baseline_path, contract), result, "cartas", "baseline")
        compare_family("Relações", lambda: runtime.current_card_relations_validation(card_csv, config), result, "relacoes", "relacoes_normalizadas")
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
    review_package = {
        "contract": "clubef-pacote-revisao-v1",
        "reading_contract": runtime.reading_contract_seal(contract),
        "database_write": False,
        "contract_families": result.get("contract_families") or {},
        "comparison_reports": result.get("comparison_reports") or {},
        # A comparação não é, por si, um conjunto de comandos de escrita.
        # Quando cada família passar a emitir envelopes aplicáveis, eles entram
        # aqui; a ausência é deliberadamente recusada pelo aplicador real.
        "application_payload": {
            "schema": "clubef-envelopes-aplicacao-v1",
            "familias": {},
            "state": "pending_normalized_domain_envelopes",
        },
    }
    package = {"database_write": False, "pacote_revisao": review_package, "pacote_sha256": runtime.sha256_json(review_package)}
    package_path = run_dir / "pacote-revisao.json"
    write_json(package_path, package)
    result["pacote_revisao"] = {"path": str(package_path), "pacote_sha256": package["pacote_sha256"], "database_write": False}
    write_json(result_path, result)
    emit("progress", stage="Conferência concluída", percent=100)
    emit("complete", state="completed", result_path=str(result_path), database_write=False)
    return 0


def load_review_package(path: str) -> tuple[dict[str, Any], dict[str, Any], str]:
    package = json.loads(Path(path).read_text(encoding="utf-8"))
    review = package.get("pacote_revisao") if isinstance(package, dict) else None
    supplied_sha = package.get("pacote_sha256") if isinstance(package, dict) else None
    if not isinstance(review, dict) or not isinstance(supplied_sha, str) or runtime.sha256_json(review) != supplied_sha:
        raise RuntimeError("pacote de revisão inválido ou hash divergente")
    return package, review, supplied_sha


def validate_current_package(path: str) -> tuple[dict[str, Any], dict[str, Any], str, dict[str, Any], dict[str, str]]:
    package, review, supplied_sha = load_review_package(path)
    config = runtime.load_config(); contract = runtime.current_reading_contract(config)
    seal = runtime.reading_contract_seal(contract)
    if review.get("reading_contract") != seal: raise RuntimeError("pacote desatualizado: contrato/fontes divergentes")
    if not runtime.evaluate_sync_readiness(contract, review.get("contract_families") or {}).get("structural_coverage_complete"):
        raise RuntimeError("pacote sem cobertura técnica integral")
    missing = [role for role, item in sources(contract).items() if item.get("required", True) and not item.get("found")]
    if missing:
        raise RuntimeError("pacote não pode ser aplicado: fonte atual ausente: " + ", ".join(missing))
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
            allowed = set(writable)
            for envelope in envelopes:
                if not isinstance(envelope, dict):
                    raise RuntimeError(f"envelope não-objeto em {family}/{target_id}")
                identity, values, provenance = envelope.get("identidade"), envelope.get("valores"), envelope.get("procedencia")
                if not isinstance(identity, dict) or not isinstance(values, dict) or (target.get("exige_procedencia") and not isinstance(provenance, dict)):
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
        insert = sql.SQL("insert into {}.{} ({}) values ({}) on conflict ({}) do {} returning {}")
        if updates:
            update_clause = sql.SQL("update set {} ").format(sql.SQL(", ").join(sql.SQL("{} = excluded.{}").format(sql.Identifier(column), sql.Identifier(column)) for column in updates))
        else:
            update_clause = sql.SQL("nothing ")
        query = insert.format(
            sql.Identifier(str(target["schema"])), sql.Identifier(table),
            sql.SQL(", ").join(sql.Identifier(column) for column in columns),
            sql.SQL(", ").join(sql.Placeholder() for _ in columns),
            sql.SQL(", ").join(sql.Identifier(key) for key in keys),
            update_clause,
            sql.SQL(", ").join(sql.Identifier(key) for key in keys),
        )
        readback = connection.execute(query, tuple(values[column] for column in columns)).fetchone()
        if readback is None or any(readback[index] != envelope["identidade"][key] for index, key in enumerate(keys)):
            raise RuntimeError(f"readback de chave divergente em {target['destino_id']}")
        applied[table] = applied.get(table, 0) + 1
    return applied


def apply_review(args: argparse.Namespace) -> int:
    """Aplica exclusivamente um pacote aprovado, numa única transação.

    Os dados de domínio ainda entram somente por envelopes tipados por família.
    Assim, pacote que contenha apenas relatório de comparação não pode causar
    uma escrita parcial ou uma dedução de destino/rótulo pelo código.
    """
    _, review, supplied_sha, contract, seal = validate_current_package(args.apply_review)
    readiness = runtime.evaluate_sync_readiness(contract, review.get("contract_families") or {})
    if not readiness.get("structural_coverage_complete"):
        raise RuntimeError("aplicação recusada: cobertura integral não confirmada")
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
        connection.commit()
    emit("complete", state="applied", database_write=True, package_sha256=supplied_sha, audit_readback=True, envelopes_applied=applied)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--cancel", required=True)
    parser.add_argument("--protocol-version", required=True)
    parser.add_argument("--approve-review")
    parser.add_argument("--apply-review")
    parser.add_argument("--reset-test-approval")
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
        if args.approve_review: return approve_review(args)
        if args.apply_review: return apply_review(args)
        if args.reset_test_approval: return reset_test_approval(args)
        return run(args)
    except Exception as error:
        emit("fatal", message=str(error), traceback=traceback.format_exc(), database_write=False)
        return 130 if str(error) == "cancelled_by_user" else 1


if __name__ == "__main__":
    raise SystemExit(main())
