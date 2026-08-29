"""Adaptador canônico e fail-closed para clube_novo.texto_do_jogo.

O módulo não descobre arquivos nem aplica nada sozinho. Ele recebe somente o pacote
selado pelo Extrator, verifica o estado corrente e escreve apenas depois da
confirmação manual administrada por executor_local.py.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


TEXT_COLUMNS = [
    "secao", "secao_idx", "id_texto", "texto", "idioma", "origem",
    "arquivo", "cpk", "secao_offset", "entrada_idx", "entrada_offset",
    "texto_offset", "tamanho_armazenado", "tamanho_visivel",
    "fonte_cpk_sha256", "fonte_arquivo_sha256", "presente_na_fonte",
    "extraido_em",
]
REQUIRED_SCHEMA_COLUMNS = set(TEXT_COLUMNS)
UPSERT_BATCH_SIZE = 500
SECTION_RELOCATION = {
    "Amg1T": "Amg1W", "Any1T": "Any1W", "Any2T": "Any2W",
    "Any3T": "Any3W", "E13W": "E15W", "E5T": "E5W",
    "E6T": "E6W", "Lcm2W": "Lcm4W", "T2T": "T2W",
    "PlayC": "Po1C",
}
CATALOG_REFERENCES = [
    ("atributo_jogo", "secao_texto", ["id_texto"]),
    ("estilo_ia", "secao_texto", ["id_texto"]),
    ("habilidade_jogo", "secao_texto", ["id_texto"]),
    ("impeto_jogo", "secao_texto", ["id_texto"]),
    ("pe", "secao_texto", ["id_texto"]),
    ("playstyle", "secao_texto", ["id_texto"]),
    ("posicao_jogo", "secao_texto", ["id_texto_sigla", "id_texto_nome"]),
]


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _key(row: dict[str, Any]) -> str:
    return f"{row.get('secao')}:{int(row.get('id_texto'))}"


def _table_columns(connection: Any, schema: str, table: str) -> list[str]:
    with connection.cursor() as cursor:
        cursor.execute(
            "select column_name from information_schema.columns "
            "where table_schema=%s and table_name=%s order by ordinal_position",
            (schema, table),
        )
        return [str(row[0]) for row in cursor.fetchall()]


def assert_text_schema(connection: Any, schema: str = "clube_novo") -> list[str]:
    columns = _table_columns(connection, schema, "texto_do_jogo")
    missing = sorted(REQUIRED_SCHEMA_COLUMNS - set(columns))
    if missing:
        raise ValueError(f"contrato estrutural de texto ainda não foi instalado: faltam {', '.join(missing)}")
    return columns


def fetch_text_rows(connection: Any, schema: str = "clube_novo", require_full_schema: bool = False) -> list[dict[str, Any]]:
    from psycopg import sql  # type: ignore

    available = _table_columns(connection, schema, "texto_do_jogo")
    if require_full_schema:
        assert_text_schema(connection, schema)
    selected = [column for column in TEXT_COLUMNS if column in available]
    minimum = {"secao", "secao_idx", "id_texto", "texto", "idioma", "arquivo", "cpk"}
    if not minimum.issubset(selected):
        raise ValueError("texto_do_jogo não possui nem o contrato mínimo legado")
    query = sql.SQL("select {} from {}.{} order by secao,id_texto").format(
        sql.SQL(",").join(sql.Identifier(column) for column in selected),
        sql.Identifier(schema), sql.Identifier("texto_do_jogo"),
    )
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = [dict(zip(selected, values)) for values in cursor.fetchall()]
    for row in rows:
        row["id"] = _key(row)
        row["fingerprint"] = _sha256({column: row.get(column) for column in selected})
    return rows


def baseline_snapshot(connection: Any, schema: str = "clube_novo") -> dict[str, Any]:
    rows = fetch_text_rows(connection, schema, require_full_schema=False)
    keys = {_key(row) for row in rows}
    references = _catalog_reference_rows(connection, schema)
    resolved, unresolved = _catalog_reference_plan(references, keys)
    reference_tables = [table for table, _, _ in CATALOG_REFERENCES]
    with connection.cursor() as cursor:
        cursor.execute(
            "select count(*)::int, count(*) filter (where not constraint_row.convalidated)::int "
            "from pg_constraint constraint_row "
            "join pg_class source_table on source_table.oid=constraint_row.conrelid "
            "join pg_namespace source_schema on source_schema.oid=source_table.relnamespace "
            "join pg_class target_table on target_table.oid=constraint_row.confrelid "
            "join pg_namespace target_schema on target_schema.oid=target_table.relnamespace "
            "where constraint_row.contype='f' and source_schema.nspname=%s "
            "and source_table.relname=any(%s) and target_schema.nspname=%s "
            "and target_table.relname='texto_do_jogo'",
            (schema, reference_tables, schema),
        )
        foreign_keys, unvalidated_foreign_keys = cursor.fetchone()
    return {
        "contract": "clubef-text-database-baseline-v1",
        "source": f"{schema}.texto_do_jogo",
        "transaction_read_only": True,
        "database_write": False,
        "preserved_schema": "clube",
        "schema_ready": REQUIRED_SCHEMA_COLUMNS.issubset(_table_columns(connection, schema, "texto_do_jogo")),
        "records": len(rows),
        "unique_official_keys": len(keys),
        "duplicate_official_keys": len(rows) - len(keys),
        "catalog_references_checked": len(references),
        "resolved_catalog_references": len(resolved),
        "unresolved_catalog_references": len(unresolved),
        "validated_foreign_keys": int(foreign_keys) - int(unvalidated_foreign_keys),
        "unvalidated_foreign_keys": int(unvalidated_foreign_keys),
        "sha256": _sha256(rows),
        "rows": rows,
    }


def _normalized_record(record: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column in TEXT_COLUMNS:
        if column == "extraido_em":
            result[column] = record.get(column) or None
        elif column in {"secao_idx", "id_texto", "secao_offset", "entrada_idx", "entrada_offset", "texto_offset", "tamanho_armazenado", "tamanho_visivel"}:
            result[column] = int(record[column]) if record.get(column) is not None else None
        elif column == "presente_na_fonte":
            if not isinstance(record.get(column), bool):
                raise ValueError("presente_na_fonte deve ser booleano no pacote canônico")
            result[column] = record[column]
        else:
            result[column] = record.get(column)
    if not result["secao"] or result["id_texto"] is None:
        raise ValueError("pacote de texto contém chave oficial incompleta")
    if result["origem"] != "jogo_fisico" or result["arquivo"] != "all.str" or result["cpk"] != "dt261_bra_console_win.cpk":
        raise ValueError(f"procedência de {_key(result)} não corresponde à fonte oficial autorizada")
    if result["idioma"] != "pt-BR" or not isinstance(result["texto"], str) or result["presente_na_fonte"] is not True:
        raise ValueError(f"conteúdo ou presença de {_key(result)} não corresponde ao all.str português atual")
    for numeric_column in ("secao_idx", "id_texto", "secao_offset", "entrada_idx", "entrada_offset", "texto_offset", "tamanho_armazenado", "tamanho_visivel"):
        if result[numeric_column] is None or result[numeric_column] < 0:
            raise ValueError(f"{numeric_column} inválido em {_key(result)}")
    for hash_column in ("fonte_cpk_sha256", "fonte_arquivo_sha256"):
        value = str(result.get(hash_column) or "")
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value.lower()):
            raise ValueError(f"{hash_column} inválido em {_key(result)}")
        result[hash_column] = value.lower()
    result["extraido_em"] = result["extraido_em"] or datetime.now(timezone.utc)
    return result


def _selection_items(selection: dict[str, Any]) -> list[dict[str, Any]]:
    items = selection.get("items") or []
    if not items or any(item.get("catalog") != "textos" for item in items):
        raise ValueError("o adaptador aceita somente o pacote canônico de textos")
    if any(item.get("action") not in {"new", "change", "insert", "update"} for item in items):
        raise ValueError("pacote de textos contém uma ação não suportada")
    keys = [str(item.get("id") or "") for item in items]
    if len(keys) != len(set(keys)) or any(not key for key in keys):
        raise ValueError("pacote de textos contém chave de destino duplicada ou vazia")
    for item in items:
        record = item.get("record") or item.get("after") or {}
        if record.get("secao") is None or record.get("id_texto") is None or str(item.get("id")) != _key(record):
            raise ValueError("a identidade do item não corresponde à chave oficial do registro")
    return items


def _row_matches(current: dict[str, Any], expected: dict[str, Any], fields: list[str] | None = None) -> bool:
    compare = fields or [column for column in TEXT_COLUMNS if column != "extraido_em"]
    return all(_canonical(current.get(column)) == _canonical(expected.get(column)) for column in compare)


def _catalog_reference_rows(connection: Any, schema: str) -> list[dict[str, Any]]:
    from psycopg import sql  # type: ignore

    found = []
    available_tables = set()
    with connection.cursor() as cursor:
        cursor.execute("select table_name from information_schema.tables where table_schema=%s", (schema,))
        available_tables = {str(row[0]) for row in cursor.fetchall()}
    for table, section_column, id_columns in CATALOG_REFERENCES:
        if table not in available_tables:
            raise ValueError(f"catálogo obrigatório ausente no schema novo: {table}")
        columns = set(_table_columns(connection, schema, table))
        if section_column not in columns or any(column not in columns for column in id_columns):
            raise ValueError(f"{schema}.{table} não possui o contrato de referência textual esperado")
        for id_column in id_columns:
            query = sql.SQL("select {},{} from {}.{} where {} is not null and {} is not null").format(
                sql.Identifier(section_column), sql.Identifier(id_column),
                sql.Identifier(schema), sql.Identifier(table),
                sql.Identifier(section_column), sql.Identifier(id_column),
            )
            with connection.cursor() as cursor:
                cursor.execute(query)
                for section, text_id in cursor.fetchall():
                    found.append({"table": table, "section_column": section_column, "id_column": id_column, "secao": str(section), "id_texto": int(text_id)})
    return found


def _simulate_final_keys(current_rows: list[dict[str, Any]], items: list[dict[str, Any]]) -> set[str]:
    keys = {_key(row) for row in current_rows}
    for item in items:
        before = item.get("before") or {}
        record = _normalized_record(item.get("record") or item.get("after") or {})
        if before.get("secao") is not None and before.get("id_texto") is not None:
            keys.discard(_key(before))
        keys.add(_key(record))
    return keys


def _catalog_reference_plan(references: list[dict[str, Any]], final_keys: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Resolve cada referência priorizando a chave física exata e só então a relocação comprovada."""
    resolved: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    grouped_targets: dict[tuple[str, str, str], set[str]] = {}
    for reference in references:
        exact_key = f"{reference['secao']}:{reference['id_texto']}"
        relocated_section = SECTION_RELOCATION.get(reference["secao"], reference["secao"])
        relocated_key = f"{relocated_section}:{reference['id_texto']}"
        if exact_key in final_keys:
            target_section, target_key = reference["secao"], exact_key
        elif relocated_key in final_keys:
            target_section, target_key = relocated_section, relocated_key
        else:
            unresolved.append({**reference, "target_key": relocated_key})
            continue
        result = {**reference, "target_section": target_section, "target_key": target_key}
        resolved.append(result)
        group_key = (reference["table"], reference["section_column"], reference["secao"])
        grouped_targets.setdefault(group_key, set()).add(target_section)
    conflicts = [(group, targets) for group, targets in grouped_targets.items() if len(targets) > 1]
    if conflicts:
        (table, section_column, section), targets = conflicts[0]
        raise ValueError(f"referências de {table}.{section_column} em {section} exigem seções incompatíveis: {', '.join(sorted(targets))}")
    return resolved, unresolved


def preflight_text_selection(connection: Any, selection: dict[str, Any], schema: str = "clube_novo") -> dict[str, Any]:
    assert_text_schema(connection, schema)
    items = _selection_items(selection)
    current_rows = fetch_text_rows(connection, schema, require_full_schema=True)
    current = {_key(row): row for row in current_rows}
    ready_keys: list[str] = []
    already_applied_keys: list[str] = []
    source_hashes = set()
    for item in items:
        record = _normalized_record(item.get("record") or item.get("after") or {})
        target_key = _key(record)
        source_hashes.add((record["fonte_cpk_sha256"], record["fonte_arquivo_sha256"]))
        target = current.get(target_key)
        before = item.get("before") or {}
        before_key = _key(before) if before.get("secao") is not None and before.get("id_texto") is not None else None
        old = current.get(before_key) if before_key else None
        if target and _row_matches(target, record):
            if before_key and before_key != target_key and old is not None:
                if not _row_matches(old, before, ["secao", "id_texto", "texto"]):
                    raise ValueError(f"conflito em {before_key}: a chave histórica mudou depois da geração do diff")
                ready_keys.append(target_key)
            else:
                already_applied_keys.append(target_key)
        elif target is None:
            if before_key is None:
                ready_keys.append(target_key)
            elif old is not None and _row_matches(old, before, ["secao", "id_texto", "texto"]):
                ready_keys.append(target_key)
            else:
                raise ValueError(f"conflito em {before_key}: a chave original mudou ou desapareceu depois da geração do diff")
        elif before_key == target_key and old is not None and _row_matches(old, before, ["secao", "id_texto", "texto"]):
            ready_keys.append(target_key)
        else:
            raise ValueError(f"conflito em {target_key}: o banco mudou depois da geração do diff")
    if len(source_hashes) != 1:
        raise ValueError("o pacote mistura mais de uma versão física de all.str")
    final_keys = _simulate_final_keys(current_rows, items)
    references = _catalog_reference_rows(connection, schema)
    _, unresolved = _catalog_reference_plan(references, final_keys)
    if unresolved:
        first = unresolved[0]
        raise ValueError(f"aplicação bloqueada: {len(unresolved)} referência(s) de catálogo não resolve(m); primeira em {first['table']}.{first['id_column']} -> {first['target_key']}")
    return {
        "database_checked": True,
        "transaction_read_only": True,
        "ready": len(ready_keys),
        "already_applied": len(already_applied_keys),
        "ready_keys": sorted(ready_keys),
        "already_applied_keys": sorted(already_applied_keys),
        "current_rows": len(current_rows),
        "final_rows": len(final_keys),
        "catalog_references_checked": len(references),
        "unresolved_catalog_references": 0,
        "source_fingerprints": [{"cpk_sha256": item[0], "all_str_sha256": item[1]} for item in source_hashes],
    }


def _update_catalog_sections(connection: Any, schema: str, final_keys: set[str]) -> list[dict[str, Any]]:
    from psycopg import sql  # type: ignore

    changes = []
    references = _catalog_reference_rows(connection, schema)
    resolved, unresolved = _catalog_reference_plan(references, final_keys)
    if unresolved:
        first = unresolved[0]
        raise RuntimeError(f"atualização de catálogo bloqueada: referência sem destino em {first['table']}.{first['id_column']} -> {first['target_key']}")
    updates = sorted({(item["table"], item["section_column"], item["secao"], item["target_section"]) for item in resolved if item["target_section"] != item["secao"]})
    for table, section_column, old, new in updates:
        query = sql.SQL("update {}.{} set {}=%s where {}=%s").format(
            sql.Identifier(schema), sql.Identifier(table),
            sql.Identifier(section_column), sql.Identifier(section_column),
        )
        with connection.cursor() as cursor:
            cursor.execute(query, (new, old))
            if cursor.rowcount:
                changes.append({"table": table, "from": old, "to": new, "rows": cursor.rowcount})
    return changes


def _assert_references_resolve(connection: Any, schema: str) -> int:
    rows = fetch_text_rows(connection, schema, require_full_schema=True)
    keys = {_key(row) for row in rows}
    references = _catalog_reference_rows(connection, schema)
    unresolved = [reference for reference in references if f"{reference['secao']}:{reference['id_texto']}" not in keys]
    if unresolved:
        first = unresolved[0]
        raise RuntimeError(f"readback bloqueado: {len(unresolved)} referência(s) textual(is) não resolve(m); primeira em {first['table']}.{first['id_column']}")
    return len(references)


def _upsert_text_records(connection: Any, records: list[dict[str, Any]], schema: str) -> int:
    """Grava o pacote em lotes para manter a transação curta e o SQL idempotente."""
    from psycopg import sql  # type: ignore

    if not records:
        return 0
    columns = TEXT_COLUMNS
    update_clause = sql.SQL(",").join(
        sql.SQL("{}=excluded.{}").format(sql.Identifier(column), sql.Identifier(column))
        for column in columns
        if column not in {"secao", "id_texto"}
    )
    row_placeholders = sql.SQL("({})").format(
        sql.SQL(",").join(sql.Placeholder() for _ in columns)
    )
    written = 0
    for start in range(0, len(records), UPSERT_BATCH_SIZE):
        batch = records[start:start + UPSERT_BATCH_SIZE]
        query = sql.SQL("insert into {}.{} ({}) values {} on conflict (secao,id_texto) do update set {}").format(
            sql.Identifier(schema),
            sql.Identifier("texto_do_jogo"),
            sql.SQL(",").join(sql.Identifier(column) for column in columns),
            sql.SQL(",").join(row_placeholders for _ in batch),
            update_clause,
        )
        values = [record[column] for record in batch for column in columns]
        with connection.cursor() as cursor:
            cursor.execute(query, values)
        written += len(batch)
    return written


def apply_text_selection(connection: Any, selection: dict[str, Any], schema: str = "clube_novo") -> dict[str, Any]:
    from psycopg import sql  # type: ignore

    items = _selection_items(selection)
    before_rows = fetch_text_rows(connection, schema, require_full_schema=True)
    before = {_key(row): row for row in before_rows}
    preflight = preflight_text_selection(connection, selection, schema)
    normalized = [(_normalized_record(item.get("record") or item.get("after") or {}), item) for item in items]
    final_keys = _simulate_final_keys(before_rows, items)
    ready_key_values = preflight.get("ready_keys")
    ready_keys = set(ready_key_values if ready_key_values is not None else [_key(record) for record, _ in normalized])
    _upsert_text_records(connection, [record for record, _ in normalized if _key(record) in ready_keys], schema)
    catalog_changes = _update_catalog_sections(connection, schema, final_keys)
    deleted = []
    for record, item in normalized:
        if _key(record) not in ready_keys:
            continue
        old = item.get("before") or {}
        if old.get("secao") is None or old.get("id_texto") is None or _key(old) == _key(record):
            continue
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("delete from {}.{} where secao=%s and id_texto=%s and texto=%s").format(
                    sql.Identifier(schema), sql.Identifier("texto_do_jogo")
                ),
                (old["secao"], int(old["id_texto"]), old.get("texto")),
            )
            if cursor.rowcount not in {0, 1}:
                raise RuntimeError(f"remoção de chave histórica inesperada em {_key(old)}")
            if cursor.rowcount == 1:
                deleted.append(_key(old))
    references_checked = _assert_references_resolve(connection, schema)
    inside_rows = fetch_text_rows(connection, schema, require_full_schema=True)
    inside = {_key(row): row for row in inside_rows}
    for record, _ in normalized:
        target = inside.get(_key(record))
        if not target or not _row_matches(target, record):
            raise RuntimeError(f"readback transacional divergiu em {_key(record)}")
    rollback = {
        "contract": "clubef-text-rollback-plan-v1",
        "automatic": False,
        "inserted_keys_to_remove_after_review": sorted([_key(record) for record, item in normalized if not (item.get("before") or {}).get("secao")]),
        "rows_to_restore": [before[_key(item["before"])] for _, item in normalized if (item.get("before") or {}).get("secao") and _key(item["before"]) in before],
        "catalog_section_changes_to_reverse": catalog_changes,
        "instruction": "executar somente como novo pacote inverso revisado; nunca restaurar automaticamente",
    }
    return {
        "changed": preflight["ready"],
        "already_applied": preflight["already_applied"],
        "readback_count": len(inside_rows),
        "readback_sha256": _sha256(inside_rows),
        "catalog_references_checked": references_checked,
        "unresolved_catalog_references": 0,
        "relocated_old_keys_removed": len(deleted),
        "catalog_section_changes": catalog_changes,
        "rollback": rollback,
    }
