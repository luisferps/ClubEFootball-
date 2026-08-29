"""Aplicação segura das dimensões físicas do Extrator V4.

Ordem obrigatória: catálogos primeiro, vínculos das cartas depois. A rotina não
apaga registros ausentes da fonte e nunca escreve fora de clube_novo.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from card_dimensions import (
    CONTRACT,
    DATABASE_CONTRACT,
    _source_cards,
    _source_clubs,
    _source_leagues,
    _source_nationalities,
    _source_types,
    validate_card_dimensions,
)


def _stable_hash(row: dict[str, Any]) -> str:
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _assert_snapshot(snapshot: dict[str, Any]) -> None:
    if not isinstance(snapshot, dict) or snapshot.get("contract") != CONTRACT:
        raise ValueError("fotografia física de Dimensões ausente ou incompatível")
    if snapshot.get("database_write") is not False:
        raise ValueError("a fotografia de Dimensões não está selada como somente leitura")
    if not isinstance(snapshot.get("cards"), list) or not snapshot["cards"]:
        raise ValueError("a fotografia física de Dimensões não contém cartas")
    catalogs = snapshot.get("catalogs") or {}
    for name in ("nationalities", "clubs", "leagues", "types"):
        if not isinstance(catalogs.get(name), list) or not catalogs[name]:
            raise ValueError(f"catálogo físico ausente: {name}")


def _upsert_rows(cursor: Any, sql: Any, schema: str, table: str, key: str, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    changed = 0
    for row in rows:
        columns = list(row)
        update_columns = [column for column in columns if column != key]
        query = sql.SQL("insert into {}.{} ({}) values ({}) on conflict ({}) do update set {}").format(
            sql.Identifier(schema),
            sql.Identifier(table),
            sql.SQL(",").join(sql.Identifier(column) for column in columns),
            sql.SQL(",").join(sql.Placeholder() for _ in columns),
            sql.Identifier(key),
            sql.SQL(",").join(
                sql.SQL("{}=excluded.{}").format(sql.Identifier(column), sql.Identifier(column))
                for column in update_columns
            ),
        )
        cursor.execute(query, [row[column] for column in columns])
        changed += 1
    return changed


def _apply_types(cursor: Any, sql: Any, schema: str, rows: list[dict[str, Any]]) -> int:
    """Tipos novos exigem prova nominal/procedência antes de inserção automática."""
    cursor.execute(sql.SQL("select tipo_carta_id from {}.tipo_carta_jogo").format(sql.Identifier(schema)))
    existing = {str(row[0]) for row in cursor.fetchall()}
    missing = [str(row["tipo_carta_id"]) for row in rows if str(row["tipo_carta_id"]) not in existing]
    if missing:
        raise ValueError(
            "tipo de carta físico novo sem registro canônico prévio: " + ", ".join(missing[:20])
        )
    changed = 0
    for row in rows:
        columns = [column for column in row if column != "tipo_carta_id"]
        query = sql.SQL("update {}.tipo_carta_jogo set {} where tipo_carta_id=%s").format(
            sql.Identifier(schema),
            sql.SQL(",").join(
                sql.SQL("{}=%s").format(sql.Identifier(column)) for column in columns
            ),
        )
        cursor.execute(query, [row[column] for column in columns] + [row["tipo_carta_id"]])
        if cursor.rowcount != 1:
            raise RuntimeError(f"tipo de carta não pôde ser atualizado: {row['tipo_carta_id']}")
        changed += 1
    return changed


def _apply_cards(cursor: Any, sql: Any, schema: str, rows: list[dict[str, Any]]) -> dict[str, int]:
    fields = [
        "registro_vinculos_jogo", "codigo_nacionalidade_player_raw", "codigo_nacionalidade",
        "codigo_clube", "codigo_liga", "codigo_tipo_carta_fisico",
        "marcador_subtipo_tipo_carta", "jogador_indisponivel", "tipo_carta_id",
        "chave_tipo_carta", "pode_rodar_vinculos", "falta_o_que_vinculos",
        "fonte_vinculos_jogo", "cpk_vinculos_jogo", "arquivo_vinculos_jogo",
        "hash_player_bin_vinculos", "contrato_vinculos_jogo",
    ]
    updated = 0
    pending_insert = 0
    query = sql.SQL("update {}.carta_jogo set {}, carregado_vinculos_em=clock_timestamp() where card_id=%s").format(
        sql.Identifier(schema),
        sql.SQL(",").join(sql.SQL("{}=%s").format(sql.Identifier(field)) for field in fields),
    )
    for row in rows:
        cursor.execute(query, [row.get(field) for field in fields] + [str(row["card_id"])])
        if cursor.rowcount == 1:
            updated += 1
        else:
            pending_insert += 1
    return {"updated": updated, "pending_card_insert": pending_insert}


def apply_card_dimensions(snapshot: dict[str, Any], connection: Any, schema: str, sql: Any) -> dict[str, Any]:
    """Aplica catálogos e vínculos em uma única transação já aberta pelo chamador."""
    if schema != "clube_novo":
        raise ValueError("aplicação de Dimensões bloqueada fora de clube_novo")
    _assert_snapshot(snapshot)

    clubs = _source_clubs(snapshot)
    leagues = _source_leagues(snapshot)
    nationalities = _source_nationalities(snapshot)
    types = _source_types(snapshot)
    cards = _source_cards(snapshot)

    for row in clubs:
        row["hash_pacote"] = _stable_hash(row)
        row["contrato_extracao"] = DATABASE_CONTRACT
        row["carregado_em"] = None
    for row in leagues:
        row["hash_pacote"] = _stable_hash(row)
        row["contrato_extracao"] = DATABASE_CONTRACT
        row["carregado_em"] = None
    for row in nationalities:
        row["contrato_extracao"] = DATABASE_CONTRACT
        row["carregado_em"] = None

    with connection.cursor() as cursor:
        cursor.execute("show transaction_read_only")
        if cursor.fetchone()[0] == "on":
            raise RuntimeError("aplicação de Dimensões abriu em modo somente leitura")
        cursor.execute("set local statement_timeout = '10min'")
        cursor.execute("select pg_advisory_xact_lock(hashtext(%s))", ("clubef_extractor:clube_novo.card_dimensions",))

        # clock_timestamp() é usado no banco para não depender do relógio do cliente.
        for rows in (clubs, leagues, nationalities):
            for row in rows:
                row.pop("carregado_em", None)

        catalog_counts = {
            "nationalities": _upsert_rows(cursor, sql, schema, "nacionalidade_jogo", "codigo_jogo", nationalities),
            "clubs": _upsert_rows(cursor, sql, schema, "clube_jogo", "codigo_jogo", clubs),
            "leagues": _upsert_rows(cursor, sql, schema, "liga_jogo", "codigo_jogo", leagues),
            "types": _apply_types(cursor, sql, schema, types),
        }

        # Marca a data da aplicação depois dos upserts, sem alterar a prova física.
        cursor.execute(sql.SQL("update {}.nacionalidade_jogo set carregado_em=clock_timestamp() where codigo_jogo = any(%s)").format(sql.Identifier(schema)), ([row["codigo_jogo"] for row in nationalities],))
        cursor.execute(sql.SQL("update {}.clube_jogo set carregado_em=clock_timestamp() where codigo_jogo = any(%s)").format(sql.Identifier(schema)), ([row["codigo_jogo"] for row in clubs],))
        cursor.execute(sql.SQL("update {}.liga_jogo set carregado_em=clock_timestamp() where codigo_jogo = any(%s)").format(sql.Identifier(schema)), ([row["codigo_jogo"] for row in leagues],))
        cursor.execute(sql.SQL("update {}.tipo_carta_jogo set carregado_em=clock_timestamp() where tipo_carta_id = any(%s)").format(sql.Identifier(schema)), ([row["tipo_carta_id"] for row in types],))

        card_counts = _apply_cards(cursor, sql, schema, cards)

    return {
        "contract": "clubef-card-dimensions-apply-v1",
        "database_write": True,
        "catalogs": catalog_counts,
        "cards": card_counts,
        "rule": "catalogos_primeiro_vinculos_depois_sem_exclusao_automatica",
    }


def readback_card_dimensions(snapshot: dict[str, Any], connection: Any, schema: str, sql: Any) -> dict[str, Any]:
    """Readback pós-commit usando o mesmo comparador canônico."""
    connection.read_only = True
    return validate_card_dimensions(snapshot, connection, schema, sql)
