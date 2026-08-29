"""Comparador read-only das dimensões físicas de carta com clube_novo."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable


CONTRACT = "clubef-card-dimensions-physical-v2"
DATABASE_CONTRACT = "clubef-card-dimensions-v2"


def _canonical_hash(rows: Iterable[dict[str, Any]]) -> str:
    payload = json.dumps(list(rows), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _index(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = str(row[key])
        if value in indexed:
            raise ValueError(f"chave duplicada na fotografia física: {key}={value}")
        indexed[value] = row
    return indexed


def _compare(
    source_rows: list[dict[str, Any]],
    database_rows: list[dict[str, Any]],
    key: str,
    fields: list[str],
) -> dict[str, Any]:
    source = _index(source_rows, key)
    database = _index(database_rows, key)
    missing_in_database = sorted(set(source) - set(database))
    missing_in_source = sorted(set(database) - set(source))
    changed: list[dict[str, Any]] = []
    for row_id in sorted(set(source) & set(database)):
        differences = {
            field: {"source": source[row_id].get(field), "database": database[row_id].get(field)}
            for field in fields
            if source[row_id].get(field) != database[row_id].get(field)
        }
        if differences:
            changed.append({"id": row_id, "fields": differences})
    normalized_source = [
        {key: row_id, **{field: source[row_id].get(field) for field in fields}}
        for row_id in sorted(source)
    ]
    normalized_database = [
        {key: row_id, **{field: database[row_id].get(field) for field in fields}}
        for row_id in sorted(database)
    ]
    return {
        "source": len(source),
        "database": len(database),
        "missing_in_database": len(missing_in_database),
        "missing_in_source": len(missing_in_source),
        "changed": len(changed),
        "difference_samples": {
            "missing_in_database": missing_in_database[:20],
            "missing_in_source": missing_in_source[:20],
            "changed": changed[:20],
        },
        "source_sha256": _canonical_hash(normalized_source),
        "database_sha256": _canonical_hash(normalized_database),
        "passed": not missing_in_database and not missing_in_source and not changed,
    }


def _fetch_dicts(cursor: Any, query: Any) -> list[dict[str, Any]]:
    cursor.execute(query)
    names = [description.name for description in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def _source_clubs(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    role_names = {
        "dt870_updated": "dt870_atualizacao",
        "dt200": "dt200",
        "dt870_original": "dt870_original",
    }
    rows = []
    for record in snapshot["catalogs"]["clubs"]:
        rows.append({
            "codigo_jogo": record["codigo_jogo"],
            "nome_pt_br": record.get("nome_pt_br"),
            "nome_en": record.get("nome_en"),
            "sigla": record.get("sigla"),
            "fonte_autoritativa": role_names.get(record["source_role"], record["source_role"]),
            "arquivo": record["arquivo"],
            "registro": record.get("record_index"),
            "registro_primeira_carta": record.get("registro_primeira_carta"),
            "tamanho_registro": record["record_size"],
            "offset_codigo": record["codigo_offset"],
            "largura_codigo": record["codigo_largura"],
            "offset_nome_pt_br": record.get("nome_pt_br_offset"),
            "largura_nome_pt_br": record.get("nome_pt_br_largura"),
            "offset_nome_en": record.get("nome_en_offset"),
            "largura_nome_en": record.get("nome_en_largura"),
            "offset_sigla": record.get("sigla_offset"),
            "largura_sigla": record.get("sigla_largura"),
            "presente_dt870_atualizacao": record["presente_dt870_atualizacao"],
            "presente_dt200": record["presente_dt200"],
            "presente_dt870_original": record["presente_dt870_original"],
            "pode_rodar": record["pode_rodar"],
            "falta_o_que": record.get("falta_o_que"),
        })
    return rows


def _source_leagues(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    role_names = {
        "dt870_updated": "dt870_atualizacao",
        "dt200": "dt200",
        "dt870_original": "dt870_original",
    }
    rows = []
    for record in snapshot["catalogs"]["leagues"]:
        has_name = bool(record.get("nome_pt_br") or record.get("nome_en"))
        rows.append({
            "codigo_jogo": record["codigo_jogo"],
            "codigo_pai": record.get("codigo_pai"),
            "nome_pt_br": record.get("nome_pt_br"),
            "nome_en": record.get("nome_en"),
            "fonte_autoritativa": role_names.get(record["source_role"], record["source_role"]),
            "arquivo": record["arquivo"],
            "registro": record["record_index"],
            "tamanho_registro": record["record_size"],
            "offset_codigo": record["codigo_offset"],
            "largura_codigo": record["codigo_largura"],
            "offset_codigo_pai": record["codigo_pai_offset"],
            "largura_codigo_pai": record["codigo_pai_largura"],
            "offset_nome_pt_br": record["nome_pt_br_offset"],
            "largura_nome_pt_br": record["nome_pt_br_largura"],
            "offset_nome_en": record["nome_en_offset"],
            "largura_nome_en": record["nome_en_largura"],
            "presente_dt870_atualizacao": record["presente_dt870_atualizacao"],
            "presente_dt200": record["presente_dt200"],
            "presente_dt870_original": record["presente_dt870_original"],
            "pode_rodar": has_name,
            "falta_o_que": None if has_name else "competição/liga sem nome físico comprovado",
        })
    return rows


def _source_nationalities(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "codigo_jogo": record["codigo_jogo"],
            "nome_pt_br": record["nome_pt_br"],
            "sigla": record["sigla"],
            "arquivo": "Country.bin",
            "cpk_origem": "dt870_console_win.cpk",
            "fonte_autoritativa": "dt870_updated",
            "registro": record["record_index"],
            "tamanho_registro": record["record_size"],
            "bit_codigo": record["codigo_bit"],
            "largura_codigo": record["codigo_largura"],
            "offset_nome_pt_br": record["nome_offset"],
            "largura_nome_pt_br": record["nome_largura"],
            "codificacao_nome_pt_br": "utf-8",
            "offset_sigla": record["sigla_offset"],
            "largura_sigla": record["sigla_largura"],
            "hash_country_bin": record["source_file_sha256"],
            "presente_dt200": record["presente_dt200"],
            "presente_dt870_steam": record["presente_dt870_original"],
            "presente_dt870_atualizacao": record["presente_dt870_atualizacao"],
            "pode_rodar": True,
            "falta_o_que": None,
        }
        for record in snapshot["catalogs"]["nationalities"]
    ]


def _source_types(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for record in snapshot["catalogs"]["types"]:
        delete_list = bool(record["usa_player_delete_list"])
        rows.append({
            "tipo_carta_id": record["tipo_carta_id"],
            "chave_texto": record.get("chave_texto"),
            "secao_texto": record.get("secao_texto"),
            "id_texto": record.get("id_texto"),
            "nome_pt_br": record.get("nome_pt_br"),
            "nome_exibicao": record["nome_exibicao"],
            "codigo_tipo_fisico": record["codigo_tipo_fisico"],
            "marcador_subtipo": record["marcador_subtipo"],
            "usa_player_delete_list": delete_list,
            "arquivo_tipo": "PlayerDeleteList.bin" if delete_list else "Player.bin",
            "campo_tipo": "card_id u64 membership" if delete_list else "card_id bits 44-47 + registro bit 104",
            "bit_subtipo": None if delete_list else 104,
            "arquivo_texto": record.get("arquivo_texto"),
            "cpk_texto": record.get("cpk_texto"),
            "entrada_texto": record.get("entrada_texto"),
            "entrada_offset": record.get("entrada_offset"),
            "texto_offset": record.get("texto_offset"),
            "tamanho_armazenado": record.get("tamanho_armazenado"),
            "hash_all_str": record.get("hash_all_str"),
            "contrato_extracao": DATABASE_CONTRACT,
            "pode_rodar": True,
            "status_associacao": record["status_associacao"],
            "tipo_provisorio": record["tipo_provisorio"],
        })
    return rows


def _source_cards(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    player_hash = snapshot["source_files"]["dt870_updated:Player.bin"]
    return [
        {
            **record,
            "fonte_vinculos_jogo": "dt870_atualizacao",
            "cpk_vinculos_jogo": "dt870_console_win.cpk",
            "arquivo_vinculos_jogo": "Player.bin",
            "hash_player_bin_vinculos": player_hash,
            "contrato_vinculos_jogo": DATABASE_CONTRACT,
        }
        for record in snapshot["cards"]
    ]


def validate_card_dimensions(snapshot: dict[str, Any], connection: Any, schema: str, sql: Any) -> dict[str, Any]:
    if schema != "clube_novo":
        raise ValueError("comparação de Dimensões bloqueada fora de clube_novo")
    if not isinstance(snapshot, dict) or snapshot.get("contract") != CONTRACT:
        raise ValueError("fotografia física de Dimensões ausente ou incompatível")
    if snapshot.get("database_write") is not False:
        raise ValueError("a fotografia de Dimensões não declara o modo somente leitura")
    if not isinstance(snapshot.get("cards"), list) or not snapshot["cards"]:
        raise ValueError("a fotografia física de Dimensões não contém cartas")

    tables = {
        "cards": "carta_jogo",
        "nationalities": "nacionalidade_jogo",
        "clubs": "clube_jogo",
        "leagues": "liga_jogo",
        "types": "tipo_carta_jogo",
    }
    with connection.cursor() as cursor:
        cursor.execute("show transaction_read_only")
        if cursor.fetchone()[0] != "on":
            raise RuntimeError("a comparação de Dimensões não ficou protegida por READ ONLY")

        for table in tables.values():
            cursor.execute("select to_regclass(%s)", (f"{schema}.{table}",))
            if cursor.fetchone()[0] is None:
                raise ValueError(f"tabela canônica ausente: {schema}.{table}")

        database_cards = _fetch_dicts(cursor, sql.SQL("""
            select card_id,registro_vinculos_jogo,codigo_nacionalidade_player_raw,
                   codigo_nacionalidade,codigo_clube,codigo_liga,
                   codigo_tipo_carta_fisico,marcador_subtipo_tipo_carta,
                   jogador_indisponivel,tipo_carta_id,chave_tipo_carta,
                   pode_rodar_vinculos,falta_o_que_vinculos,
                   fonte_vinculos_jogo,cpk_vinculos_jogo,arquivo_vinculos_jogo,
                   hash_player_bin_vinculos,contrato_vinculos_jogo
            from {}.{}
        """).format(sql.Identifier(schema), sql.Identifier(tables["cards"])))
        database_nationalities = _fetch_dicts(cursor, sql.SQL("""
            select codigo_jogo,nome_pt_br,sigla,arquivo,cpk_origem,fonte_autoritativa,
                   registro,tamanho_registro,bit_codigo,largura_codigo,
                   offset_nome_pt_br,largura_nome_pt_br,codificacao_nome_pt_br,
                   offset_sigla,largura_sigla,hash_country_bin,presente_dt200,
                   presente_dt870_steam,presente_dt870_atualizacao,pode_rodar,falta_o_que
            from {}.{}
        """).format(sql.Identifier(schema), sql.Identifier(tables["nationalities"])))
        database_clubs = _fetch_dicts(cursor, sql.SQL("""
            select codigo_jogo,nome_pt_br,nome_en,sigla,fonte_autoritativa,arquivo,
                   registro,registro_primeira_carta,tamanho_registro,offset_codigo,
                   largura_codigo,offset_nome_pt_br,largura_nome_pt_br,offset_nome_en,
                   largura_nome_en,offset_sigla,largura_sigla,presente_dt870_atualizacao,
                   presente_dt200,presente_dt870_original,pode_rodar,falta_o_que
            from {}.{}
        """).format(sql.Identifier(schema), sql.Identifier(tables["clubs"])))
        database_leagues = _fetch_dicts(cursor, sql.SQL("""
            select codigo_jogo,codigo_pai,nome_pt_br,nome_en,fonte_autoritativa,arquivo,
                   registro,tamanho_registro,offset_codigo,largura_codigo,
                   offset_codigo_pai,largura_codigo_pai,offset_nome_pt_br,
                   largura_nome_pt_br,offset_nome_en,largura_nome_en,
                   presente_dt870_atualizacao,presente_dt200,presente_dt870_original,
                   pode_rodar,falta_o_que
            from {}.{}
        """).format(sql.Identifier(schema), sql.Identifier(tables["leagues"])))
        database_types = _fetch_dicts(cursor, sql.SQL("""
            select tipo_carta_id,chave_texto,secao_texto,id_texto,nome_pt_br,
                   nome_exibicao,codigo_tipo_fisico,marcador_subtipo,
                   usa_player_delete_list,arquivo_tipo,campo_tipo,bit_subtipo,
                   arquivo_texto,cpk_texto,entrada_texto,entrada_offset,texto_offset,
                   tamanho_armazenado,hash_all_str,contrato_extracao,pode_rodar,
                   status_associacao,tipo_provisorio
            from {}.{}
        """).format(sql.Identifier(schema), sql.Identifier(tables["types"])))

        cursor.execute("""
            select count(*)
            from pg_constraint c
            where c.connamespace = %s::regnamespace
              and c.convalidated is false
              and c.conrelid in (
                %s::regclass,%s::regclass,%s::regclass,%s::regclass,%s::regclass
              )
        """, (schema, *(f"{schema}.{table}" for table in tables.values())))
        unvalidated_constraints = cursor.fetchone()[0]

        cursor.execute("""
            select count(*)
            from pg_constraint c
            where c.contype='f'
              and c.confrelid=%s::regclass
              and c.conrelid in (%s::regclass,%s::regclass)
        """, (f"{schema}.nacionalidade_jogo", f"{schema}.carta_jogo", f"{schema}.tecnico_jogo"))
        shared_nationality_fks = cursor.fetchone()[0]

        cursor.execute(sql.SQL("""
            select
              count(*) filter (where n.codigo_jogo is null),
              count(*) filter (where c.codigo_clube is not null and cl.codigo_jogo is null),
              count(*) filter (where c.codigo_liga is not null and l.codigo_jogo is null),
              count(*) filter (where t.tipo_carta_id is null),
              count(*) filter (where c.chave_tipo_carta is distinct from t.chave_texto)
            from {}.{} c
            left join {}.{} n on n.codigo_jogo=c.codigo_nacionalidade
            left join {}.{} cl on cl.codigo_jogo=c.codigo_clube
            left join {}.{} l on l.codigo_jogo=c.codigo_liga
            left join {}.{} t on t.tipo_carta_id=c.tipo_carta_id
        """).format(
            sql.Identifier(schema), sql.Identifier("carta_jogo"),
            sql.Identifier(schema), sql.Identifier("nacionalidade_jogo"),
            sql.Identifier(schema), sql.Identifier("clube_jogo"),
            sql.Identifier(schema), sql.Identifier("liga_jogo"),
            sql.Identifier(schema), sql.Identifier("tipo_carta_jogo"),
        ))
        orphan_counts = list(cursor.fetchone())

    card_fields = [
        "registro_vinculos_jogo", "codigo_nacionalidade_player_raw", "codigo_nacionalidade",
        "codigo_clube", "codigo_liga", "codigo_tipo_carta_fisico",
        "marcador_subtipo_tipo_carta", "jogador_indisponivel", "tipo_carta_id",
        "chave_tipo_carta", "pode_rodar_vinculos", "falta_o_que_vinculos",
        "fonte_vinculos_jogo", "cpk_vinculos_jogo", "arquivo_vinculos_jogo",
        "hash_player_bin_vinculos", "contrato_vinculos_jogo",
    ]
    nationality_fields = [field for field in database_nationalities[0] if field != "codigo_jogo"]
    club_fields = [field for field in database_clubs[0] if field != "codigo_jogo"]
    league_fields = [field for field in database_leagues[0] if field != "codigo_jogo"]
    type_fields = [field for field in database_types[0] if field != "tipo_carta_id"]
    comparisons = {
        "cards": _compare(_source_cards(snapshot), database_cards, "card_id", card_fields),
        "nationalities": _compare(_source_nationalities(snapshot), database_nationalities, "codigo_jogo", nationality_fields),
        "clubs": _compare(_source_clubs(snapshot), database_clubs, "codigo_jogo", club_fields),
        "leagues": _compare(_source_leagues(snapshot), database_leagues, "codigo_jogo", league_fields),
        "types": _compare(_source_types(snapshot), database_types, "tipo_carta_id", type_fields),
    }
    passed = (
        all(comparison["passed"] for comparison in comparisons.values())
        and not any(orphan_counts)
        and unvalidated_constraints == 0
        and shared_nationality_fks == 2
    )
    return {
        "contract": "clubef-card-dimensions-readback-extractor-v2",
        "source_contract": snapshot["contract"],
        "passed": passed,
        "transaction_read_only": True,
        "database_write": False,
        "source_counts": snapshot.get("counts"),
        "comparisons": comparisons,
        "database_integrity": {
            "orphan_counts": {
                "nationality": orphan_counts[0], "club": orphan_counts[1],
                "league": orphan_counts[2], "type": orphan_counts[3],
                "type_key_mismatch": orphan_counts[4],
            },
            "unvalidated_constraints": unvalidated_constraints,
            "shared_nationality_foreign_keys": shared_nationality_fks,
        },
    }
