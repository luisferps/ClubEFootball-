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
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Iterator, Mapping, Sequence


CONTRACT = "clubef-card-relations-readback-v2"
REQUIRED_CARD_COLUMNS = {
    "card_id",
    "atributos",
    "corpo",
    "aptidoes",
}


@dataclass(frozen=True)
class RelationSpec:
    name: str
    table: str
    columns: tuple[str, ...]
    key_kind: tuple[str, ...]
    source_artifact: str = "cartas-fisicas.csv"
    comparison_identity_columns: tuple[str, ...] | None = None
    presentation_only_columns: tuple[str, ...] = ()


RELATIONS = (
    RelationSpec("atributos", "carta_atributo_jogo", ("card_id", "codigo_atributo", "valor"), ("str", "str", "int")),
    RelationSpec("corpo", "carta_corpo_jogo", ("card_id", "codigo_corpo", "valor"), ("str", "str", "int")),
    RelationSpec(
        "habilidades",
        "carta_habilidade_jogo",
        ("card_id", "skill_id", "ordem"),
        ("str", "int", "int"),
        "cartas-fisicas-canonicas.json",
        comparison_identity_columns=("card_id", "skill_id"),
        presentation_only_columns=("ordem",),
    ),
    RelationSpec("estilos_ia", "carta_estilo_ia_jogo", ("card_id", "bit_estilo_ia"), ("str", "int"), "cartas-fisicas-canonicas.json"),
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
    # O banco ordena card_id como texto; a fotografia precisa usar a mesma
    # ordenação determinística antes do comparador streaming.
    rows.sort(key=lambda item: item["card_id"])
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


def fetch_catalog_maps(
    connection: Any,
    schema: str,
    sql: Any,
    required_positions: set[str],
) -> dict[str, dict[Any, Any]]:
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
        "posicoes": _fetch_unique_map(
            connection,
            sql.SQL("select codigo_en,id from {}.posicao_jogo where codigo_en is not null").format(ident),
            0,
            1,
            "posicao_jogo.codigo_en",
        ),
    }
    unresolved_positions = sorted(required_positions - set(maps["posicoes"]))
    if unresolved_positions:
        raise ValueError(f"aptidão física sem chave canônica: {unresolved_positions[0]}")
    # posicao_jogo também contém GK como posição principal. Player.bin possui
    # somente as 12 aptidões de campo; o goleiro não é uma 13ª aptidão.
    maps["posicoes"] = {
        code: position_id
        for code, position_id in maps["posicoes"].items()
        if code in required_positions
    }
    return maps


def _expected_for_card(row: dict[str, str], family: str, maps: dict[str, dict[Any, Any]]) -> list[tuple[Any, ...]]:
    card_id = row["card_id"]
    if family == "atributos":
        values = _json_array(row["atributos"], "atributos", card_id)
        if len(values) != len(maps[family]):
            raise ValueError(f"{card_id}.atributos tem {len(values)} valores; contrato/catálogo declara {len(maps[family])}")
        output = [(card_id, str(maps[family][index]), int(value)) for index, value in enumerate(values)]
        if any(value < 40 or value > 99 for _, _, value in output):
            raise ValueError(f"{card_id}.atributos contém valor fora de 40..99")
        return sorted(output, key=lambda item: item[1])
    if family == "corpo":
        values = _json_array(row["corpo"], "corpo", card_id)
        if len(values) != len(maps[family]):
            raise ValueError(f"{card_id}.corpo tem {len(values)} valores; contrato/catálogo declara {len(maps[family])}")
        return sorted(((card_id, str(maps[family][index]), int(value)) for index, value in enumerate(values)), key=lambda item: item[1])
    if family == "posicoes":
        aptitudes = _json_object(row["aptidoes"], "aptidoes", card_id)
        if len(aptitudes) != len(maps[family]):
            raise ValueError(f"{card_id}.aptidoes tem {len(aptitudes)} posições; contrato/catálogo declara {len(maps[family])}")
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


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} precisa ser inteiro, não booleano")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} precisa ser inteiro") from error
    if str(parsed) != str(value).strip() and not isinstance(value, int):
        raise ValueError(f"{label} não é inteiro canônico")
    return parsed


def _canonical_cards(cards: Any) -> list[dict[str, Any]]:
    if not isinstance(cards, list):
        raise ValueError("cartas-fisicas-canonicas.json precisa conter uma lista")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, card in enumerate(cards):
        if not isinstance(card, dict):
            raise ValueError(f"artefato canônico: carta {index} inválida")
        card_id = str(card.get("card_id") or "").strip()
        if not card_id or not card_id.isdigit():
            raise ValueError(f"artefato canônico: card_id inválido na posição {index}")
        if card_id in seen:
            raise ValueError(f"artefato canônico: card_id duplicado: {card_id}")
        seen.add(card_id)
        copied = dict(card)
        copied["card_id"] = card_id
        result.append(copied)
    return sorted(result, key=lambda item: item["card_id"])


def _contract_fields(reading_contract: Mapping[str, Any], prefix: str) -> list[dict[str, Any]]:
    fields = [item for item in reading_contract.get("campos") or [] if isinstance(item, dict) and str(item.get("chave_campo") or "").startswith(prefix)]
    if not fields:
        raise ValueError(f"pedido tipado sem campos para {prefix}")
    return fields


def _canonical_skill_rows(cards: Sequence[dict[str, Any]], reading_contract: Mapping[str, Any]) -> tuple[list[tuple[Any, ...]], dict[tuple[Any, ...], dict[str, Any]]]:
    mappings = {
        _integer(item.get("campo_id"), "mapeamento.campo_id"): item
        for item in reading_contract.get("mapeamentos_envelope") or []
        if isinstance(item, dict) and item.get("status") == "comprovado" and item.get("grupo_repeticao") == "habilidades_player_bin"
    }
    if not mappings:
        raise ValueError("pedido tipado sem membros comprovados de habilidades")
    fields = _contract_fields(reading_contract, "carta.habilidade.")
    field_by_signature: dict[tuple[int, int, int], dict[str, Any]] = {}
    for field in fields:
        transform = field.get("transformacao") or {}
        signature = (_integer(transform.get("skill_id"), "campo habilidade.skill_id"), _integer(field.get("bit_inicio"), "campo habilidade.bit_inicio"), _integer(field.get("largura_bits"), "campo habilidade.largura_bits"))
        if signature in field_by_signature:
            raise ValueError(f"campo de habilidade duplicado no contrato: {signature}")
        field_by_signature[signature] = field
    result: list[tuple[Any, ...]] = []
    provenance: dict[tuple[Any, ...], dict[str, Any]] = {}
    for card in cards:
        card_id = card["card_id"]
        members = card.get("habilidades_fisicas")
        if not isinstance(members, list):
            raise ValueError(f"{card_id}.habilidades_fisicas ausente no artefato canônico")
        active: list[tuple[int, int, int, int, dict[str, Any], dict[str, Any]]] = []
        for member in members:
            if not isinstance(member, dict):
                raise ValueError(f"{card_id}.habilidades_fisicas contém item inválido")
            if member.get("ativo") is not True:
                continue
            campo_id = _integer(member.get("campo_id"), f"{card_id}.habilidades_fisicas.campo_id")
            skill_id = _integer(member.get("skill_id"), f"{card_id}.habilidades_fisicas.skill_id")
            bit = _integer(member.get("bit"), f"{card_id}.habilidades_fisicas.bit")
            width = _integer(member.get("largura"), f"{card_id}.habilidades_fisicas.largura")
            physical_order = _integer(member.get("ordem"), f"{card_id}.habilidades_fisicas.ordem")
            mapping = mappings.get(campo_id)
            if not mapping:
                raise ValueError(f"{card_id}.habilidades_fisicas sem mapeamento declarado: campo_id {campo_id}")
            rule = mapping.get("regra_decomposicao") or {}
            expected_key = f"skill_id={skill_id}"
            if rule.get("tipo") != "lista_filtrada_bit" or str(rule.get("chave") or "") != expected_key or _integer(rule.get("bit"), "regra habilidade.bit") != bit or _integer(rule.get("largura"), "regra habilidade.largura") != width:
                raise ValueError(f"{card_id}.habilidades_fisicas diverge do mapeamento declarado: campo_id {campo_id}")
            if (skill_id, bit, width) not in field_by_signature:
                raise ValueError(f"{card_id}.habilidades_fisicas sem campo físico declarado: skill_id {skill_id}")
            for required in ("registro", "arquivo", "hash", "procedencia"):
                if member.get(required) in (None, ""):
                    raise ValueError(f"{card_id}.habilidades_fisicas sem procedência: {required}")
            active.append((physical_order, skill_id, bit, width, member, mapping))
        if len({skill_id for _, skill_id, _, _, _, _ in active}) != len(active):
            raise ValueError(f"{card_id}.habilidades_fisicas contém skill_id duplicado")
        # A ordem é uma informação física opcional para apresentação e
        # rastreabilidade; a identidade validada é sempre card_id + skill_id.
        # Não sintetizamos nem reordenamos a lista para tentar impor uma ordem
        # visual que o contrato não declarou.
        for physical_order, skill_id, bit, width, member, mapping in sorted(active):
            row = (card_id, skill_id, physical_order)
            result.append(row)
            provenance[(card_id, skill_id)] = {
                "fotografia": "cartas-fisicas-canonicas.json",
                "registro": _integer(member["registro"], "habilidade.registro"),
                "arquivo": str(member["arquivo"]),
                "hash": str(member["hash"]),
                "campo_id": _integer(member["campo_id"], "habilidade.campo_id"),
                "bit": bit,
                "largura": width,
                "ordem_fisica": physical_order,
                "regra_decomposicao": mapping.get("regra_decomposicao"),
                "procedencia": member["procedencia"],
            }
    return sorted(result, key=lambda item: (item[0], item[1], item[2])), provenance


def _style_contract(reading_contract: Mapping[str, Any]) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    by_bit: dict[int, dict[str, Any]] = {}
    for field in _contract_fields(reading_contract, "carta.estilo_ia."):
        transform = field.get("transformacao") or {}
        bit = _integer(transform.get("bit_estilo_ia"), f"{field.get('chave_campo')}.bit_estilo_ia")
        width = _integer(field.get("largura_bits"), f"{field.get('chave_campo')}.largura_bits")
        if bit != _integer(field.get("bit_inicio"), f"{field.get('chave_campo')}.bit_inicio") or width <= 0 or bit in by_bit:
            raise ValueError(f"campo estilo_ia inválido ou duplicado no contrato: {field.get('chave_campo')}")
        if str(field.get("entidade_destino") or "") != "carta_estilo_ia_jogo.bit_estilo_ia":
            raise ValueError(f"destino não declarado para estilo_ia: {field.get('chave_campo')}")
        by_bit[bit] = field
    coverage = next((item for item in reading_contract.get("catalogos_fisicos") or [] if isinstance(item, dict) and item.get("schema") == "clube_novo" and item.get("table") == "estilo_ia"), None)
    if not isinstance(coverage, dict) or not str(coverage.get("estado_cobertura") or ""):
        raise ValueError("pedido sem estado de cobertura física de clube_novo.estilo_ia")
    return by_bit, coverage


def _canonical_style_rows(
    cards: Sequence[dict[str, Any]],
    reading_contract: Mapping[str, Any],
) -> tuple[
    list[tuple[Any, ...]],
    dict[tuple[Any, ...], dict[str, Any]],
    dict[str, Any],
    list[dict[str, Any]],
    list[int],
]:
    """Return only declared style relations and flag unexpected physical members.

    The monitored bits are an observed projection, not an assertion that the
    game has a complete enumerable style catalog.  A physical member outside
    that projection therefore never becomes a domain relation automatically:
    it is preserved as an alert with its card identity and provenance.
    """
    fields, coverage = _style_contract(reading_contract)
    result: list[tuple[Any, ...]] = []
    provenance: dict[tuple[Any, ...], dict[str, Any]] = {}
    alerts: list[dict[str, Any]] = []
    for card in cards:
        card_id = card["card_id"]
        members = card.get("estilos_ia_fisicos")
        if not isinstance(members, list):
            raise ValueError(f"{card_id}.estilos_ia_fisicos ausente no artefato canônico")
        seen: set[int] = set()
        for member in members:
            if not isinstance(member, dict):
                raise ValueError(f"{card_id}.estilos_ia_fisicos contém item inválido")
            if member.get("ativo") is not True:
                continue
            bit = _integer(member.get("bit"), f"{card_id}.estilos_ia_fisicos.bit")
            width = _integer(member.get("largura"), f"{card_id}.estilos_ia_fisicos.largura")
            if width <= 0:
                raise ValueError(f"{card_id}.estilos_ia_fisicos contém largura inválida: {width}")
            if bit in seen:
                raise ValueError(f"{card_id}.estilos_ia_fisicos contém bit duplicado: {bit}")
            seen.add(bit)
            for required in ("registro", "arquivo", "hash", "procedencia"):
                if member.get(required) in (None, ""):
                    raise ValueError(f"{card_id}.estilos_ia_fisicos sem procedência: {required}")
            field = fields.get(bit)
            if field is None:
                alerts.append({
                    "classification": "padrao_fisico_nao_projetado",
                    "family": "estilos_ia",
                    "reason": "bit físico ativo não pertence à projeção observada do contrato",
                    "chave_canonica": {"card_id": card_id, "bit_estilo_ia": bit},
                    "valor_fisico": {
                        "chave_campo": member.get("chave_campo"),
                        "bit": bit,
                        "largura": width,
                        "ativo": True,
                    },
                    "fonte_fisica": {
                        "fotografia": "cartas-fisicas-canonicas.json",
                        "registro": _integer(member["registro"], "estilo_ia.registro"),
                        "arquivo": str(member["arquivo"]),
                        "hash": str(member["hash"]),
                        "procedencia": member["procedencia"],
                    },
                    "application_enabled": False,
                })
                continue
            if member.get("chave_campo") != field.get("chave_campo") or width != _integer(field.get("largura_bits"), f"{field.get('chave_campo')}.largura_bits"):
                raise ValueError(f"{card_id}.estilos_ia_fisicos diverge do campo declarado: bit {bit}")
            row = (card_id, bit)
            result.append(row)
            provenance[(card_id, bit)] = {
                "fotografia": "cartas-fisicas-canonicas.json",
                "registro": _integer(member["registro"], "estilo_ia.registro"),
                "arquivo": str(member["arquivo"]),
                "hash": str(member["hash"]),
                "campo": str(member["chave_campo"]),
                "bit": bit,
                "largura": width,
                "procedencia": member["procedencia"],
            }
    return sorted(result, key=lambda item: (item[0], item[1])), provenance, coverage, alerts, sorted(fields)


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


def _identity_columns(spec: RelationSpec) -> tuple[str, ...]:
    if spec.comparison_identity_columns is not None:
        return spec.comparison_identity_columns
    # Relações com valor têm identidade composta por carta e FK; a última
    # coluna é o conteúdo comparável. Relações puras usam todas as colunas.
    return spec.columns if len(spec.columns) == 2 else spec.columns[:-1]


def _identity(spec: RelationSpec, row: tuple[Any, ...]) -> tuple[Any, ...]:
    indexes = {column: index for index, column in enumerate(spec.columns)}
    return tuple(row[indexes[column]] for column in _identity_columns(spec))


def _comparison_projection(spec: RelationSpec, row: tuple[Any, ...]) -> tuple[Any, ...]:
    """Retorna somente os valores materiais para a comparação declarada."""
    presentation_only = set(spec.presentation_only_columns)
    return tuple(value for column, value in zip(spec.columns, row, strict=True) if column not in presentation_only)


def _classified_relation(
    kind: str,
    spec: RelationSpec,
    source: tuple[Any, ...] | None,
    database: tuple[Any, ...] | None,
    source_provenance: Mapping[tuple[Any, ...], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    row = source if source is not None else database
    assert row is not None
    identity = _identity(spec, row)
    source_reference = None
    if source is not None:
        source_reference = {"fotografia": spec.source_artifact, "card_id": source[0]}
        if source_provenance:
            source_reference.update(source_provenance.get(_identity(spec, source), {}))
    return {
        "classificacao": kind,
        "escopo": spec.name,
        "destino_tabela": spec.table,
        "colunas_fisicas": list(spec.columns),
        "colunas_apresentacao": list(spec.presentation_only_columns),
        "chave_canonica": dict(zip(_identity_columns(spec), identity, strict=True)),
        "fonte_fisica": source_reference,
        "vinculo_banco": None if database is None else dict(zip(_identity_columns(spec), identity, strict=True)),
        "valor_fisico": None if source is None else list(source),
        "valor_banco": None if database is None else list(database),
    }


def compare_relation(
    spec: RelationSpec,
    expected: Iterable[tuple[Any, ...]],
    actual: Iterable[tuple[Any, ...]],
    source_provenance: Mapping[tuple[Any, ...], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    expected_sha = hashlib.sha256()
    actual_sha = hashlib.sha256()
    expected_count = 0
    actual_count = 0
    source_rows = list(expected)
    database_rows = list(actual)
    fingerprint_source_rows = [_comparison_projection(spec, row) for row in source_rows]
    fingerprint_database_rows = [_comparison_projection(spec, row) for row in database_rows]
    # Uma relação com campos só de apresentação não pode produzir um hash
    # dependente da ordem. A cardinalidade ainda entra no hash e duplicatas
    # continuam classificadas como falha pela chave canônica.
    if spec.presentation_only_columns:
        fingerprint_source_rows.sort(key=lambda row: json.dumps(row, ensure_ascii=False, separators=(",", ":")))
        fingerprint_database_rows.sort(key=lambda row: json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    for row in fingerprint_source_rows:
        expected_count += 1
        _fingerprint_row(expected_sha, row)
    for row in fingerprint_database_rows:
        actual_count += 1
        _fingerprint_row(actual_sha, row)
    def keyed(rows: list[tuple[Any, ...]], origin: str) -> tuple[dict[tuple[Any, ...], tuple[Any, ...]], list[dict[str, Any]]]:
        out: dict[tuple[Any, ...], tuple[Any, ...]] = {}
        repeated: list[dict[str, Any]] = []
        for row in rows:
            key = _identity(spec, row)
            if key in out:
                repeated.append(_classified_relation("repetido", spec, row if origin == "fisico" else None, row if origin == "banco" else None, source_provenance))
            else:
                out[key] = row
        return out, repeated
    source_by_key, repeated_source = keyed(source_rows, "fisico")
    database_by_key, repeated_database = keyed(database_rows, "banco")
    classification: dict[str, list[dict[str, Any]]] = {"new": [], "removed": [], "altered": [], "repeated": repeated_source + repeated_database, "invalid": []}
    for key in sorted(set(source_by_key) | set(database_by_key), key=lambda value: json.dumps(value, default=str)):
        left, right = source_by_key.get(key), database_by_key.get(key)
        if right is None:
            classification["new"].append(_classified_relation("novo", spec, left, None, source_provenance))
        elif left is None:
            classification["removed"].append(_classified_relation("removido", spec, None, right, source_provenance))
        elif _comparison_projection(spec, left) != _comparison_projection(spec, right):
            classification["altered"].append(_classified_relation("alterado", spec, left, right, source_provenance))
    mismatch_count = sum(len(items) for items in classification.values())
    mismatches = (classification["new"] + classification["removed"] + classification["altered"] + classification["repeated"] + classification["invalid"])[:100]
    expected_fingerprint = expected_sha.hexdigest()
    actual_fingerprint = actual_sha.hexdigest()
    return {
        "expected_rows": expected_count,
        "database_rows": actual_count,
        "mismatch_count": mismatch_count,
        "mismatches": mismatches,
        "classification": classification,
        "expected_sha256": expected_fingerprint,
        "database_sha256": actual_fingerprint,
        "exact_match": mismatch_count == 0 and expected_fingerprint == actual_fingerprint,
    }


def _sample(rows: Sequence[dict[str, str]], expected_by_relation: Mapping[str, Sequence[tuple[Any, ...]]]) -> list[dict[str, Any]]:
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
                spec.name: [list(item) for item in expected_by_relation[spec.name] if item[0] == card_id]
                for spec in RELATIONS
            },
        }
        for card_id in unique
    ]


def validate_card_relations(
    csv_text: str,
    canonical_cards: Any,
    reading_contract: Mapping[str, Any],
    connection: Any,
    schema: str,
    sql: Any,
) -> dict[str, Any]:
    if schema != "clube_novo":
        raise ValueError("validação bloqueada: somente o schema clube_novo")
    with connection.cursor() as cursor:
        cursor.execute("show transaction_read_only")
        if cursor.fetchone()[0] != "on":
            raise RuntimeError("a validação das relações não ficou protegida como somente leitura")
    if not isinstance(reading_contract, Mapping) or not reading_contract.get("versao_contrato"):
        raise ValueError("validação bloqueada: pedido tipado ausente ou sem versão")
    rows = parse_card_csv(csv_text)
    canonical = _canonical_cards(canonical_cards)
    csv_ids = {row["card_id"] for row in rows}
    canonical_ids = {card["card_id"] for card in canonical}
    if csv_ids != canonical_ids:
        missing_canonical = sorted(csv_ids - canonical_ids)
        missing_csv = sorted(canonical_ids - csv_ids)
        raise ValueError(
            "artefatos físicos divergentes por card_id: "
            f"sem canônico={missing_canonical[:1]}; sem CSV={missing_csv[:1]}"
        )
    required_positions: set[str] = set()
    for row in rows:
        required_positions.update(_json_object(row["aptidoes"], "aptidoes", row["card_id"]).keys())
    maps = fetch_catalog_maps(connection, schema, sql, required_positions)
    results: dict[str, Any] = {}
    expected_by_relation: dict[str, list[tuple[Any, ...]]] = {}
    provenance_by_relation: dict[str, dict[tuple[Any, ...], dict[str, Any]]] = {}
    style_coverage: dict[str, Any] | None = None
    style_alerts: list[dict[str, Any]] = []
    projected_style_bits: list[int] = []
    for spec in RELATIONS:
        if spec.name == "habilidades":
            expected, provenance = _canonical_skill_rows(canonical, reading_contract)
        elif spec.name == "estilos_ia":
            expected, provenance, style_coverage, style_alerts, projected_style_bits = _canonical_style_rows(canonical, reading_contract)
        else:
            expected, provenance = list(iter_expected(rows, spec.name, maps)), {}
        expected_by_relation[spec.name] = expected
        provenance_by_relation[spec.name] = provenance
        results[spec.name] = compare_relation(
            spec,
            expected,
            iter_database(connection, schema, spec, sql),
            provenance,
        )
    assert style_coverage is not None
    observed_style_match = results["estilos_ia"]["exact_match"]
    coverage_state = str(style_coverage.get("estado_cobertura"))
    coverage_complete = coverage_state in {"coverage_completa", "cobertura_completa", "completa"}
    style_application_enabled = coverage_complete and observed_style_match and not style_alerts
    results["estilos_ia"].update({
        "observed_relation_exact_match": observed_style_match,
        "monitoring_state": "observado_nas_cartas_monitorado",
        "observed_projection_bits": projected_style_bits,
        "unknown_physical_pattern_count": len(style_alerts),
        "unknown_physical_patterns": style_alerts[:100],
        "coverage_state": coverage_state,
        "coverage_complete": coverage_complete,
        "coverage_reason": style_coverage.get("motivo_cobertura"),
        "coverage_provenance": {
            "modo_validacao": style_coverage.get("modo_validacao"),
            "familias_impactadas": style_coverage.get("familias_impactadas"),
            "aprovacao_aplicacao_habilitada": style_coverage.get("aprovacao_aplicacao_habilitada"),
        },
        # A relação observada é comparável por bit/FK, mas a ausência de uma
        # enumeração física completa continua bloqueando a promoção do catálogo.
        "application_enabled": style_application_enabled,
        "exact_match": style_application_enabled,
    })
    classification = {kind: [] for kind in ("new", "removed", "altered", "repeated", "invalid")}
    for item in results.values():
        for kind, entries in item["classification"].items():
            classification[kind].extend(entries)
    application_blockers: list[dict[str, Any]] = []
    if not coverage_complete:
        application_blockers.append({
            "family": "estilos_ia",
            "state": coverage_state,
            "reason": style_coverage.get("motivo_cobertura") or "catálogo físico não enumerável no contrato atual",
        })
    if style_alerts:
        application_blockers.append({
            "family": "estilos_ia",
            "state": "padrao_fisico_nao_projetado",
            "reason": "membro físico fora da projeção observada requer investigação; a relação afetada não é aplicada",
            "alerts": style_alerts[:100],
        })
    return {
        "contract": CONTRACT,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_schema": schema,
        "source": "fotografia física DT870: CSV de apresentação + JSON canônico de FKs/procedência",
        "cards": len(rows),
        "unique_card_ids": len(rows),
        "transaction_read_only": True,
        "database_write": False,
        "relations": results,
        "classification_complete": True,
        "technical_integrity": not classification["repeated"] and not classification["invalid"],
        "exact_match": not any(classification[kind] for kind in classification) and results["estilos_ia"]["exact_match"],
        "application_enabled": not any(classification[kind] for kind in classification) and results["estilos_ia"]["application_enabled"],
        "application_blockers": application_blockers,
        "classification": classification,
        "samples": _sample(rows, expected_by_relation),
        "excluded": ["carta_impeto_jogo", "dimensoes_de_carta", "clube"],
    }
