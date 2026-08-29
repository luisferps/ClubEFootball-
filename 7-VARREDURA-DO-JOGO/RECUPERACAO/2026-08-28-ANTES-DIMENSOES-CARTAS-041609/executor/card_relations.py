"""Validação somente leitura das cinco relações normalizadas de cartas.

O módulo recebe a fotografia de cartas produzida pelo núcleo a partir do CPK
atual, resolve somente chaves canônicas comprovadas nos catálogos de
``clube_novo`` e compara, linha a linha, com as relações já carregadas.

Não contém DDL, INSERT, UPDATE, DELETE, TRUNCATE nem caminhos de aplicação.
``carta_impeto_jogo`` e as dimensões de carta estão deliberadamente fora deste
contrato.
"""

from __future__ import annotations

import csv
import hashlib
import io
import itertools
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Iterator, Sequence


CONTRACT = "clubef-card-relations-readback-v1"
REQUIRED_CARD_COLUMNS = {
    "card_id",
    "atributos",
    "corpo",
    "habilidades",
    "estilos_ia",
    "aptidoes",
}


@dataclass(frozen=True)
class RelationSpec:
    name: str
    table: str
    columns: tuple[str, ...]
    key_kind: tuple[str, ...]


RELATIONS = (
    RelationSpec("atributos", "carta_atributo_jogo", ("card_id", "codigo_atributo", "valor"), ("str", "str", "int")),
    RelationSpec("corpo", "carta_corpo_jogo", ("card_id", "codigo_corpo", "valor"), ("str", "str", "int")),
    RelationSpec("habilidades", "carta_habilidade_jogo", ("card_id", "skill_id", "ordem"), ("str", "int", "int")),
    RelationSpec("estilos_ia", "carta_estilo_ia_jogo", ("card_id", "bit_estilo_ia"), ("str", "int")),
    RelationSpec("posicoes", "carta_posicao_jogo", ("card_id", "posicao_id", "nivel_aptidao"), ("str", "int", "int")),
)


def _json_array(value: str, field: str, card_id: str) -> list[Any]:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError(f"{card_id}.{field} não é JSON válido") from error
    if not isinstance(parsed, list):
        raise ValueError(f"{card_id}.{field} não é uma lista")
    return parsed


def _json_object(value: str, field: str, card_id: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError(f"{card_id}.{field} não é JSON válido") from error
    if not isinstance(parsed, dict):
        raise ValueError(f"{card_id}.{field} não é um objeto")
    return parsed


def parse_card_csv(csv_text: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff"), newline=""))
    headers = set(reader.fieldnames or [])
    missing = sorted(REQUIRED_CARD_COLUMNS - headers)
    if missing:
        raise ValueError(f"fotografia de cartas sem campos obrigatórios: {', '.join(missing)}")
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for line_number, row in enumerate(reader, start=2):
        card_id = str(row.get("card_id") or "").strip()
        if not card_id or not card_id.isdigit():
            raise ValueError(f"card_id inválido na linha {line_number}")
        if card_id in seen:
            raise ValueError(f"card_id duplicado na fotografia física: {card_id}")
        seen.add(card_id)
        row["card_id"] = card_id
        rows.append(row)
    rows.sort(key=lambda item: int(item["card_id"]))
    return rows


def _fetch_unique_map(connection: Any, query: Any, key_index: int, value_index: int, label: str) -> dict[Any, Any]:
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
    result: dict[Any, Any] = {}
    for row in rows:
        key, value = row[key_index], row[value_index]
        if key in result and result[key] != value:
            raise ValueError(f"catálogo ambíguo para {label}: {key}")
        result[key] = value
    return result


def fetch_catalog_maps(connection: Any, schema: str, sql: Any) -> dict[str, dict[Any, Any]]:
    ident = sql.Identifier(schema)
    maps = {
        "atributos": _fetch_unique_map(
            connection,
            sql.SQL("select idx_casa,codigo from {}.atributo_jogo where idx_casa between 0 and 25 order by idx_casa").format(ident),
            0,
            1,
            "atributo_jogo.idx_casa",
        ),
        "corpo": _fetch_unique_map(
            connection,
            sql.SQL("select pos,codigo from {}.corpo_ordem where pos between 0 and 11 order by pos").format(ident),
            0,
            1,
            "corpo_ordem.pos",
        ),
        "habilidades": _fetch_unique_map(
            connection,
            sql.SQL("select nome_en,skill_id from {}.habilidade_jogo where nome_en is not null").format(ident),
            0,
            1,
            "habilidade_jogo.nome_en",
        ),
        "estilos_ia": _fetch_unique_map(
            connection,
            sql.SQL("select nome_en,bit from {}.estilo_ia where nome_en is not null").format(ident),
            0,
            1,
            "estilo_ia.nome_en",
        ),
        "posicoes": _fetch_unique_map(
            connection,
            sql.SQL("select codigo_en,id from {}.posicao_jogo where codigo_en is not null").format(ident),
            0,
            1,
            "posicao_jogo.codigo_en",
        ),
    }
    expected_sizes = {"atributos": 26, "corpo": 12, "estilos_ia": 7, "posicoes": 12}
    for family, expected in expected_sizes.items():
        if len(maps[family]) != expected:
            raise ValueError(f"catálogo {family} fora do contrato: {len(maps[family])}; esperado {expected}")
    return maps


def _expected_for_card(row: dict[str, str], family: str, maps: dict[str, dict[Any, Any]]) -> list[tuple[Any, ...]]:
    card_id = row["card_id"]
    if family == "atributos":
        values = _json_array(row["atributos"], "atributos", card_id)
        if len(values) != 26:
            raise ValueError(f"{card_id}.atributos tem {len(values)} valores; esperado 26")
        output = [(card_id, str(maps[family][index]), int(value)) for index, value in enumerate(values)]
        if any(value < 40 or value > 99 for _, _, value in output):
            raise ValueError(f"{card_id}.atributos contém valor fora de 40..99")
        return sorted(output, key=lambda item: item[1])
    if family == "corpo":
        values = _json_array(row["corpo"], "corpo", card_id)
        if len(values) != 12:
            raise ValueError(f"{card_id}.corpo tem {len(values)} valores; esperado 12")
        return sorted(((card_id, str(maps[family][index]), int(value)) for index, value in enumerate(values)), key=lambda item: item[1])
    if family == "habilidades":
        names = _json_array(row["habilidades"], "habilidades", card_id)
        if len(names) != len(set(names)):
            raise ValueError(f"{card_id}.habilidades contém item duplicado")
        unresolved = [name for name in names if name not in maps[family]]
        if unresolved:
            raise ValueError(f"{card_id}.habilidades sem chave canônica: {unresolved[0]}")
        return sorted(((card_id, int(maps[family][name]), order) for order, name in enumerate(names)), key=lambda item: item[1])
    if family == "estilos_ia":
        names = _json_array(row["estilos_ia"], "estilos_ia", card_id)
        if len(names) != len(set(names)):
            raise ValueError(f"{card_id}.estilos_ia contém item duplicado")
        unresolved = [name for name in names if name not in maps[family]]
        if unresolved:
            raise ValueError(f"{card_id}.estilos_ia sem chave canônica: {unresolved[0]}")
        return sorted(((card_id, int(maps[family][name])) for name in names), key=lambda item: item[1])
    if family == "posicoes":
        aptitudes = _json_object(row["aptidoes"], "aptidoes", card_id)
        if len(aptitudes) != 12:
            raise ValueError(f"{card_id}.aptidoes tem {len(aptitudes)} posições; esperado 12")
        unresolved = [name for name in aptitudes if name not in maps[family]]
        if unresolved:
            raise ValueError(f"{card_id}.aptidoes sem chave canônica: {unresolved[0]}")
        output = [(card_id, int(maps[family][name]), int(value)) for name, value in aptitudes.items()]
        if any(value < 0 or value > 2 for _, _, value in output):
            raise ValueError(f"{card_id}.aptidoes contém nível fora de 0..2")
        return sorted(output, key=lambda item: item[1])
    raise ValueError(f"família desconhecida: {family}")


def iter_expected(rows: Sequence[dict[str, str]], family: str, maps: dict[str, dict[Any, Any]]) -> Iterator[tuple[Any, ...]]:
    for row in rows:
        yield from _expected_for_card(row, family, maps)


def _normalize_tuple(values: Sequence[Any], kinds: Sequence[str]) -> tuple[Any, ...]:
    return tuple(str(value) if kind == "str" else int(value) for value, kind in zip(values, kinds))


def iter_database(connection: Any, schema: str, spec: RelationSpec, sql: Any) -> Iterator[tuple[Any, ...]]:
    query = sql.SQL("select {} from {}.{} order by card_id, {}").format(
        sql.SQL(",").join(sql.Identifier(column) for column in spec.columns),
        sql.Identifier(schema),
        sql.Identifier(spec.table),
        sql.Identifier(spec.columns[1]),
    )
    with connection.cursor(name=f"readback_{spec.table}") as cursor:
        cursor.itersize = 10_000
        cursor.execute(query)
        for row in cursor:
            yield _normalize_tuple(row, spec.key_kind)


def _fingerprint_row(digest: Any, row: tuple[Any, ...]) -> None:
    digest.update(json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    digest.update(b"\n")


def compare_relation(
    expected: Iterable[tuple[Any, ...]],
    actual: Iterable[tuple[Any, ...]],
) -> dict[str, Any]:
    expected_sha = hashlib.sha256()
    actual_sha = hashlib.sha256()
    expected_count = 0
    actual_count = 0
    mismatch_count = 0
    mismatches: list[dict[str, Any]] = []
    missing = object()
    for index, (left, right) in enumerate(itertools.zip_longest(expected, actual, fillvalue=missing)):
        if left is not missing:
            expected_count += 1
            _fingerprint_row(expected_sha, left)
        if right is not missing:
            actual_count += 1
            _fingerprint_row(actual_sha, right)
        if left != right:
            mismatch_count += 1
            if len(mismatches) < 100:
                mismatches.append({
                    "index": index,
                    "expected": None if left is missing else list(left),
                    "database": None if right is missing else list(right),
                })
    expected_fingerprint = expected_sha.hexdigest()
    actual_fingerprint = actual_sha.hexdigest()
    return {
        "expected_rows": expected_count,
        "database_rows": actual_count,
        "mismatch_count": mismatch_count,
        "mismatches": mismatches,
        "expected_sha256": expected_fingerprint,
        "database_sha256": actual_fingerprint,
        "exact": mismatch_count == 0 and expected_fingerprint == actual_fingerprint,
    }


def _sample(rows: Sequence[dict[str, str]], maps: dict[str, dict[Any, Any]]) -> list[dict[str, Any]]:
    by_id = {row["card_id"]: row for row in rows}
    preferred = ["84", "4522", "7511", "60754", "108959"]
    selected = [card_id for card_id in preferred if card_id in by_id]
    if rows:
        selected.extend([rows[0]["card_id"], rows[len(rows) // 2]["card_id"], rows[-1]["card_id"]])
    unique = list(dict.fromkeys(selected))[:8]
    return [
        {
            "card_id": card_id,
            "nome": by_id[card_id].get("nome", ""),
            "relations": {
                spec.name: [list(item) for item in _expected_for_card(by_id[card_id], spec.name, maps)]
                for spec in RELATIONS
            },
        }
        for card_id in unique
    ]


def validate_card_relations(csv_text: str, connection: Any, schema: str, sql: Any) -> dict[str, Any]:
    if schema != "clube_novo":
        raise ValueError("validação bloqueada: somente o schema clube_novo")
    with connection.cursor() as cursor:
        cursor.execute("show transaction_read_only")
        if cursor.fetchone()[0] != "on":
            raise RuntimeError("a validação das relações não ficou protegida como somente leitura")
    rows = parse_card_csv(csv_text)
    maps = fetch_catalog_maps(connection, schema, sql)
    results: dict[str, Any] = {}
    for spec in RELATIONS:
        results[spec.name] = compare_relation(
            iter_expected(rows, spec.name, maps),
            iter_database(connection, schema, spec, sql),
        )
    passed = len(rows) == 43_072 and all(item["exact"] for item in results.values())
    return {
        "contract": CONTRACT,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_schema": schema,
        "source": "fotografia extraída do DT870 atualizado",
        "cards": len(rows),
        "unique_card_ids": len(rows),
        "transaction_read_only": True,
        "database_write": False,
        "relations": results,
        "samples": _sample(rows, maps),
        "excluded": ["carta_impeto_jogo", "dimensoes_de_carta", "clube"],
        "passed": passed,
    }

