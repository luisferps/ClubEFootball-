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
import review_html


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
            "application_eligible": value.get("application_eligible", True),
            "application_blockers": value.get("application_blockers", []),
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
            if (not isinstance(report, dict) or report.get("supported") is not False
                    or report.get("status") != state or report.get("application_eligible") is not False):
                buckets["invalid"].append({"classificacao": "inválido", "escopo": "catalogos", "catalogo": f"{schema}.{table}", "motivo": "runtime não devolveu a pendência de cobertura declarada"}); continue
            blocker = {
                "catalogo": f"{schema}.{table}",
                "estado_cobertura": state,
                "familias_impactadas": impacted,
                "motivo": mapping.get("motivo_cobertura"),
                "procedencia": mapping.get("proveniencia"),
                "origem_fisica_comprovada": report.get("origem_fisica_comprovada"),
                "artefato_fisico_declarado": report.get("artefato_fisico_declarado"),
            }
            application_blockers.append(blocker)
            coverage.append({"catalogo": blocker["catalogo"], "modo": mapping.get("modo_validacao"), "estado_cobertura": state, "coberto": False, "application_eligible": False, "familias_impactadas": impacted, "motivo": blocker["motivo"]})
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
    return {"classification_complete": True, "technical_integrity": technical, "exact_match": not any(buckets[k] for k in buckets), "classification": buckets, "coverage": coverage, "coverage_complete": not application_blockers, "application_eligible": not application_blockers, "application_blockers": application_blockers, "database_write": False}


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
    review_package = {
        "contract": "clubef-pacote-revisao-v1",
        "reading_contract": runtime.reading_contract_seal(contract),
        "database_write": False,
        "contract_families": result.get("contract_families") or {},
        "comparison_reports": result.get("comparison_reports") or {},
        # O pacote precisa expor a pendência declarada, não apenas recusar o
        # aplicador depois. Leitura das outras famílias continua disponível.
        "review_gate": result["review_gate"],
        "application_status": {
            "enabled": result["review_gate"].get("application_enabled") is True,
            "blocked_by_contract_coverage": bool(result["review_gate"].get("application_blockers")),
            "application_blockers": result["review_gate"].get("application_blockers") or [],
        },
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
    # O HTML é derivado do resultado já gravado. Ele não relê jogo, contrato
    # nem banco, e mantém o JSON apenas como artefato técnico interno.
    rendered_review = review_html.render_saved_result(result_path)
    emit("progress", stage="Conferência concluída", percent=100)
    emit("complete", state="completed", result_path=str(result_path), review_html_path=rendered_review["review_html_path"], manifest_path=rendered_review["manifest_path"], database_write=False)
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


def render_review_html(args: argparse.Namespace) -> int:
    """Gera a leitura humana de um resultado existente sem iniciar varredura."""
    rendered = review_html.render_saved_result(Path(args.render_review_html))
    emit("complete", state="review_html_generated", result_path=args.render_review_html, **rendered)
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
    parser.add_argument("--render-review-html")
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
        if args.render_review_html: return render_review_html(args)
        if args.smoke_stage_habilidades: return smoke_stage_skill_envelopes(args)
        if args.approve_review: return approve_review(args)
        if args.apply_review: return apply_review(args)
        if args.reset_test_approval: return reset_test_approval(args)
        return run(args)
    except Exception as error:
        emit("fatal", message=str(error), traceback=traceback.format_exc(), database_write=False)
        return 130 if str(error) == "cancelled_by_user" else 1


if __name__ == "__main__":
    raise SystemExit(main())
