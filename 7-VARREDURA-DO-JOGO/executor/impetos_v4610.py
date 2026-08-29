"""Validador V4.6.10 de Ímpetos orientado pelo pedido do banco.

A cardinalidade e os códigos esperados são lidos de clube_novo em cada
execução. Ausências, novidades, alterações e duplicidades são relatadas sem
interromper as outras famílias do Extrator.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

CONTRACT = "clubef-impetos-physical-v1"


def _rows(cursor: Any, query: str) -> list[dict[str, Any]]:
    cursor.execute(query)
    names = [column.name for column in cursor.description]
    return [dict(zip(names, values, strict=True)) for values in cursor.fetchall()]


def _first_detail(record: dict[str, Any], role: str) -> dict[str, Any]:
    items = (record.get("source_details") or {}).get(role) or []
    return items[0] if items else {}


def _int_or_none(value: Any) -> int | None:
    try:
        return None if value is None else int(value)
    except (TypeError, ValueError):
        return None


def _sample(values: list[int], limit: int = 50) -> list[int]:
    return values[:limit]


def validate_impetos_v4610(snapshot: dict[str, Any], connection: Any) -> dict[str, Any]:
    if not isinstance(snapshot, dict) or snapshot.get("contract") != CONTRACT:
        raise ValueError("contrato físico de Ímpetos inválido")

    physical_records = snapshot.get("records")
    if not isinstance(physical_records, list):
        raise ValueError("a fotografia física de Ímpetos não contém registros")

    with connection.cursor() as cursor:
        cursor.execute("show transaction_read_only")
        if cursor.fetchone()[0] != "on":
            raise RuntimeError("a validação de Ímpetos não ficou protegida como somente leitura")

        expected_catalog = _rows(
            cursor,
            "select codigo_jogo,tamanho_registro,bit_codigo,largura_codigo,"
            "registro_dt200,registro_dt870_steam,registro_dt870_atualizacao,"
            "presente_dt200,presente_dt870_steam,presente_dt870_atualizacao "
            "from clube_novo.impeto_jogo order by codigo_jogo",
        )
        expected_conditions = _rows(
            cursor,
            "select codigo_impeto,tipo_raw,indice_registro,registro_sha256 "
            "from clube_novo.impeto_condicao_jogo order by codigo_impeto",
        )
        requested_counts = _rows(
            cursor,
            "select "
            "(select count(*) from clube_novo.impeto_jogo)::int as union_catalog,"
            "(select count(*) from clube_novo.impeto_atributo_jogo)::int as effects,"
            "(select count(*) from clube_novo.impeto_condicao_jogo)::int as conditions,"
            "(select count(*) from clube_novo.impeto_condicao_faixa_jogo)::int as ranges,"
            "(select count(*) from clube_novo.impeto_condicao_parametro_faixa_jogo)::int as range_parameters,"
            "(select count(*) from clube_novo.impeto_condicao_nacionalidade_jogo)::int as nationality_targets,"
            "(select count(*) from clube_novo.impeto_condicao_liga_jogo)::int as league_targets,"
            "(select count(*) from clube_novo.impeto_condicao_clube_jogo)::int as club_targets,"
            "(select count(*) from clube_novo.impeto_condicao_classe_jogo)::int as classes,"
            "(select count(*) from clube_novo.impeto_condicao_liga_membro_jogo)::int as competition_unit_members",
        )[0]
        consumer = _rows(
            cursor,
            "select count(*) filter (where pode_rodar)::int as condicoes_aptas,"
            "count(*) filter (where not pode_rodar)::int as condicoes_bloqueadas "
            "from clube_novo.impeto_condicao_jogo",
        )[0]

    ids: list[int] = []
    invalid_records: list[dict[str, Any]] = []
    by_code: dict[int, dict[str, Any]] = {}
    for index, record in enumerate(physical_records):
        if not isinstance(record, dict):
            invalid_records.append({"index": index, "reason": "registro não é objeto"})
            continue
        code = _int_or_none(record.get("id"))
        if code is None:
            invalid_records.append({"index": index, "reason": "id ausente ou inválido"})
            continue
        ids.append(code)
        by_code.setdefault(code, record)

    duplicate_codes = sorted(code for code, total in Counter(ids).items() if total > 1)
    found_codes = set(by_code)
    expected_by_code = {int(row["codigo_jogo"]): row for row in expected_catalog}
    expected_codes = set(expected_by_code)

    missing_codes = sorted(expected_codes - found_codes)
    extra_codes = sorted(found_codes - expected_codes)
    changed_codes: list[int] = []

    record_size = _int_or_none(snapshot.get("record_size"))
    code_field = (snapshot.get("field_contract") or {}).get("codigo") or {}
    code_bit = _int_or_none(code_field.get("bit"))
    code_width = _int_or_none(code_field.get("largura"))

    for code in sorted(expected_codes & found_codes):
        expected = expected_by_code[code]
        record = by_code[code]
        details = record.get("source_details") or {}
        dt200 = _first_detail(record, "dt200")
        original = _first_detail(record, "dt870_original")
        updated = _first_detail(record, "dt870_updated")
        source_signature = (
            record_size,
            code_bit,
            code_width,
            _int_or_none(dt200.get("record_index")),
            _int_or_none(original.get("record_index")),
            _int_or_none(updated.get("record_index")),
            bool(details.get("dt200")),
            bool(details.get("dt870_original")),
            bool(details.get("dt870_updated")),
        )
        expected_signature = (
            _int_or_none(expected.get("tamanho_registro")),
            _int_or_none(expected.get("bit_codigo")),
            _int_or_none(expected.get("largura_codigo")),
            _int_or_none(expected.get("registro_dt200")),
            _int_or_none(expected.get("registro_dt870_steam")),
            _int_or_none(expected.get("registro_dt870_atualizacao")),
            bool(expected.get("presente_dt200")),
            bool(expected.get("presente_dt870_steam")),
            bool(expected.get("presente_dt870_atualizacao")),
        )
        if source_signature != expected_signature:
            changed_codes.append(code)

    current_records = {
        code: record
        for code, record in by_code.items()
        if record.get("preferred_source") == "dt870_updated"
        and record.get("tipo_condicao_status") == "coletado"
    }
    expected_condition_by_code = {
        int(row["codigo_impeto"]): row for row in expected_conditions
    }
    expected_condition_codes = set(expected_condition_by_code)
    found_condition_codes = set(current_records)

    missing_conditions = sorted(expected_condition_codes - found_condition_codes)
    extra_conditions = sorted(found_condition_codes - expected_condition_codes)
    changed_conditions: list[int] = []
    for code in sorted(expected_condition_codes & found_condition_codes):
        expected = expected_condition_by_code[code]
        record = current_records[code]
        detail = _first_detail(record, "dt870_updated")
        source_signature = (
            _int_or_none(record.get("tipo_condicao_raw")),
            _int_or_none(detail.get("record_index")),
            detail.get("record_sha256"),
        )
        expected_signature = (
            _int_or_none(expected.get("tipo_raw")),
            _int_or_none(expected.get("indice_registro")),
            expected.get("registro_sha256"),
        )
        if source_signature != expected_signature:
            changed_conditions.append(code)

    extracted_counts = {
        "raw_records": len(physical_records),
        "valid_records": len(ids),
        "unique_codes": len(found_codes),
        "union_catalog": len(found_codes),
        "effects": sum(len(record.get("efeitos") or []) for record in current_records.values()),
        "conditions": len(current_records),
        "ranges": sum(len(record.get("faixas") or []) for record in current_records.values()),
        "range_parameters": sum(
            1
            for record in current_records.values()
            if _int_or_none(record.get("tipo_condicao_raw")) == 2
        ),
        "nationality_targets": sum(
            1 for record in current_records.values()
            if record.get("alvo_tipo") == "nacionalidade_regiao"
        ),
        "league_targets": sum(
            1 for record in current_records.values()
            if record.get("alvo_tipo") == "liga_categoria"
        ),
        "club_targets": sum(
            1 for record in current_records.values()
            if record.get("alvo_tipo") == "clube_equipe"
            and record.get("alvo_codigo") is not None
        ),
        "classes": sum(
            1 for record in current_records.values()
            if (_int_or_none(record.get("classe_dono")) or 0) > 0
        ),
        "competition_unit_members": len(snapshot.get("liga_membros") or []),
    }

    count_differences = {
        key: {
            "requested": int(requested_counts.get(key) or 0),
            "found": int(extracted_counts.get(key) or 0),
        }
        for key in requested_counts
        if int(requested_counts.get(key) or 0) != int(extracted_counts.get(key) or 0)
    }

    issues: list[dict[str, Any]] = []
    if missing_codes:
        issues.append({"scope": "catalogo", "kind": "missing", "codes": _sample(missing_codes), "total": len(missing_codes)})
    if extra_codes:
        issues.append({"scope": "catalogo", "kind": "extra", "codes": _sample(extra_codes), "total": len(extra_codes)})
    if changed_codes:
        issues.append({"scope": "catalogo", "kind": "changed", "codes": _sample(changed_codes), "total": len(changed_codes)})
    if duplicate_codes:
        issues.append({"scope": "catalogo", "kind": "duplicate", "codes": _sample(duplicate_codes), "total": len(duplicate_codes)})
    if missing_conditions:
        issues.append({"scope": "conditions", "kind": "missing", "codes": _sample(missing_conditions), "total": len(missing_conditions)})
    if extra_conditions:
        issues.append({"scope": "conditions", "kind": "extra", "codes": _sample(extra_conditions), "total": len(extra_conditions)})
    if changed_conditions:
        issues.append({"scope": "conditions", "kind": "changed", "codes": _sample(changed_conditions), "total": len(changed_conditions)})
    if invalid_records:
        issues.append({"scope": "catalogo", "kind": "invalid_records", "samples": invalid_records[:20], "total": len(invalid_records)})
    if count_differences:
        issues.append({"scope": "related_tables", "kind": "count_differences", "differences": count_differences})

    passed = not issues
    return {
        "contract": CONTRACT,
        "authority": "clube_novo",
        "transaction_read_only": True,
        "database_write": False,
        "preserved_schema": "clube",
        "continue_pipeline": True,
        "application_blocked": not passed,
        "requested_by_database": {key: int(value or 0) for key, value in requested_counts.items()},
        "extracted": extracted_counts,
        "code_report": {
            "requested": len(expected_codes),
            "found_unique": len(found_codes),
            "missing": missing_codes,
            "extra": extra_codes,
            "changed": changed_codes,
            "duplicates": duplicate_codes,
            "conditions_requested": len(expected_condition_codes),
            "conditions_found": len(found_condition_codes),
            "conditions_missing": missing_conditions,
            "conditions_extra": extra_conditions,
            "conditions_changed": changed_conditions,
        },
        "issues": issues,
        "checks": {
            "consumer_readiness": consumer,
            "count_differences": count_differences,
        },
        "passed": passed,
        "result": "aprovado" if passed else "divergencias_registradas",
    }
