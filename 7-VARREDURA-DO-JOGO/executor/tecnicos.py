"""Validação integral e somente leitura de Técnicos contra clube_novo."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable


CONTRACT = "clubef-tecnicos-carga-v4-sobreposicao"
STYLE_BITS = {
    "possessionGame": 206,
    "longBallCounter": 238,
    "quickCounter": 224,
    "longBall": 199,
    "outWide": 213,
    "overload": 135,
}


def _rows(cursor: Any, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cursor.execute(query, params)
    names = [description.name for description in cursor.description]
    return [dict(zip(names, values, strict=True)) for values in cursor.fetchall()]


def _sha256(rows: Iterable[tuple[Any, ...]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        digest.update(json.dumps(row, ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _compare(source: set[tuple[Any, ...]], database: set[tuple[Any, ...]]) -> dict[str, Any]:
    order_key = lambda row: json.dumps(row, ensure_ascii=False, separators=(",", ":"), default=str)
    source_sorted = sorted(source, key=order_key)
    database_sorted = sorted(database, key=order_key)
    missing = sorted(source - database, key=order_key)
    extra = sorted(database - source, key=order_key)
    return {
        "source": len(source),
        "database": len(database),
        "missing_in_database": len(missing),
        "extra_in_database": len(extra),
        "source_sha256": _sha256(source_sorted),
        "database_sha256": _sha256(database_sorted),
        "samples": {"missing": missing[:10], "extra": extra[:10]},
        "exact": not missing and not extra,
    }


def validate_tecnicos(snapshot: dict[str, Any], connection: Any) -> dict[str, Any]:
    if snapshot.get("contract") != CONTRACT:
        raise ValueError("contrato físico de Técnicos incompatível")
    records = snapshot.get("records") or []
    nationalities = snapshot.get("nationalities") or []
    affinities = snapshot.get("affinities") or []
    if len(records) != 1_478 or len({str(row.get("id")) for row in records}) != 1_478:
        raise ValueError("a fotografia física não contém 1.478 técnicos únicos")
    if len(nationalities) != 214 or len(affinities) != 8:
        raise ValueError("catálogos compartilhados de nacionalidade/afinidade incompletos")

    source_technicians = {
        (
            int(row["id"]), row.get("nome_en") or None, row.get("nome_jp") or None, row.get("nome_cn") or None,
            int(row["idade"]), int(row["nacionalidade_codigo"]), int(row["afinidade_codigo"]),
            int(row["record_index"]), str(row["source_file_sha256"]),
        )
        for row in records
    }
    source_nationalities = {
        (
            int(row["codigo_jogo"]), row.get("nome_pt_br"), row.get("sigla"), int(row["record_index"]),
            int(row["record_size"]), int(row["codigo_bit"]), int(row["codigo_largura"]),
            int(row["nome_offset"]), int(row["nome_largura"]), int(row["sigla_offset"]),
            int(row["sigla_largura"]), str(row["source_file_sha256"]),
        )
        for row in nationalities
    }
    source_affinities = {
        (
            int(row["codigo_jogo"]), row.get("nome_pt"), row.get("nome_tela"),
            bool(row.get("ausencia_legitima")), bool(row.get("rotulo_confirmado")),
            int(row["bit"]), int(row["largura"]), str(row["source_file_sha256"]),
            bool(row.get("pode_rodar")), row.get("falta_o_que"),
        )
        for row in affinities
    }
    source_styles: set[tuple[Any, ...]] = set()
    source_boosts_pending: list[tuple[Any, ...]] = []
    for row in records:
        for code, value in (row.get("proficiencias") or {}).items():
            if code not in STYLE_BITS:
                raise ValueError(f"estilo de Técnico sem contrato físico: {code}")
            source_styles.add((
                int(row["id"]), code, int(value), "Coach.bin", int(row["record_index"]),
                STYLE_BITS[code], 7, str(row["source_file_sha256"]), True,
            ))
        for boost in row.get("boosts") or []:
            source_boosts_pending.append((
                int(row["id"]), int(boost["ordem"]), int(boost["atributo_idx_canonico"]),
                int(boost["delta"]), "Coach.bin", int(row["record_index"]), int(boost["bit"]),
                int(boost["largura"]), str(row["source_file_sha256"]), True,
            ))

    with connection.cursor() as cursor:
        cursor.execute("show transaction_read_only")
        if cursor.fetchone()[0] != "on":
            raise RuntimeError("a validação de Técnicos não ficou protegida como somente leitura")
        attribute_rows = _rows(cursor, """
            select indice_otimizador,codigo_atributo codigo
            from clube_novo.atributo_ordem_otimizador
            where indice_otimizador between 0 and 25
        """)
        attribute_codes = {int(row["indice_otimizador"]): str(row["codigo"]) for row in attribute_rows}
        database_technician_rows = _rows(cursor, """
            select id,nome_en,nome_jp,nome_cn,idade,codigo_nacionalidade,codigo_afinidade,
                   registro_campos_apresentacao,hash_campos_apresentacao
            from clube_novo.tecnico_jogo
            where fonte_autoritativa='dt870_updated' and presente_dt870_atualizacao is true
        """)
        database_nationality_rows = _rows(cursor, """
            select codigo_jogo,nome_pt_br,sigla,registro,tamanho_registro,bit_codigo,largura_codigo,
                   offset_nome_pt_br,largura_nome_pt_br,offset_sigla,largura_sigla,hash_country_bin
            from clube_novo.nacionalidade_jogo
        """)
        database_affinity_rows = _rows(cursor, """
            select codigo_jogo,nome_pt,nome_tela,ausencia_legitima,rotulo_confirmado,bit,largura,
                   hash_coach_bin,pode_rodar,falta_o_que
            from clube_novo.afinidade_tecnico_jogo
        """)
        database_style_rows = _rows(cursor, """
            select relation.tecnico_id,relation.codigo_estilo,relation.proficiencia,relation.arquivo,
                   relation.registro,relation.bit,relation.largura,relation.hash_coach_bin,relation.confirmado
            from clube_novo.tecnico_estilo_jogo relation
            join clube_novo.tecnico_jogo technician on technician.id=relation.tecnico_id
            where technician.fonte_autoritativa='dt870_updated' and technician.presente_dt870_atualizacao is true
        """)
        database_boost_rows = _rows(cursor, """
            select relation.tecnico_id,relation.ordem,relation.codigo_atributo,relation.delta,relation.arquivo,
                   relation.registro,relation.bit,relation.largura,relation.hash_coach_bin,relation.confirmado
            from clube_novo.tecnico_atributo_jogo relation
            join clube_novo.tecnico_jogo technician on technician.id=relation.tecnico_id
            where technician.fonte_autoritativa='dt870_updated' and technician.presente_dt870_atualizacao is true
        """)
        orphan_rows = _rows(cursor, """
            select
              (select count(*) from clube_novo.tecnico_jogo t left join clube_novo.nacionalidade_jogo n on n.codigo_jogo=t.codigo_nacionalidade where t.fonte_autoritativa='dt870_updated' and n.codigo_jogo is null)::int as nacionalidade,
              (select count(*) from clube_novo.tecnico_jogo t left join clube_novo.afinidade_tecnico_jogo a on a.codigo_jogo=t.codigo_afinidade where t.fonte_autoritativa='dt870_updated' and a.codigo_jogo is null)::int as afinidade,
              (select count(*) from clube_novo.tecnico_estilo_jogo r left join clube_novo.tecnico_jogo t on t.id=r.tecnico_id where t.id is null)::int as estilo_tecnico,
              (select count(*) from clube_novo.tecnico_estilo_jogo r left join clube_novo.estilo_jogo_tecnico e on e.codigo=r.codigo_estilo where e.codigo is null)::int as estilo_catalogo,
              (select count(*) from clube_novo.tecnico_atributo_jogo r left join clube_novo.tecnico_jogo t on t.id=r.tecnico_id where t.id is null)::int as boost_tecnico,
              (select count(*) from clube_novo.tecnico_atributo_jogo r left join clube_novo.atributo_jogo a on a.codigo=r.codigo_atributo where a.codigo is null)::int as boost_atributo
        """)[0]
        readiness = _rows(cursor, """
            select
              count(*) filter (where fonte_autoritativa='dt870_updated')::int as tecnicos_atuais,
              count(*) filter (where fonte_autoritativa='dt870_updated' and pode_rodar)::int as tecnicos_aptos,
              (select count(*) filter (where pode_rodar) from clube_novo.afinidade_tecnico_jogo)::int as afinidades_aptas
            from clube_novo.tecnico_jogo
        """)[0]
        preserved = _rows(cursor, """
            select
              (select count(*) from clube_novo.texto_do_jogo)::int as textos,
              (select count(*) from clube_novo.carta_jogo)::int as cartas,
              (select count(*) from clube_novo.impeto_atributo_jogo)::int as efeitos_impeto
        """)[0]

    unresolved_attribute_indexes = sorted({row[2] for row in source_boosts_pending} - set(attribute_codes))
    if unresolved_attribute_indexes:
        raise ValueError(f"boost de Técnico sem atributo canônico: {unresolved_attribute_indexes[0]}")
    source_boosts = {
        (row[0], row[1], attribute_codes[row[2]], *row[3:])
        for row in source_boosts_pending
    }
    database_technicians = {
        (int(row["id"]), row["nome_en"], row["nome_jp"], row["nome_cn"], int(row["idade"]),
         int(row["codigo_nacionalidade"]), int(row["codigo_afinidade"]),
         int(row["registro_campos_apresentacao"]), str(row["hash_campos_apresentacao"]))
        for row in database_technician_rows
    }
    database_nationalities = {
        (int(row["codigo_jogo"]), row["nome_pt_br"], row["sigla"], int(row["registro"]),
         int(row["tamanho_registro"]), int(row["bit_codigo"]), int(row["largura_codigo"]),
         int(row["offset_nome_pt_br"]), int(row["largura_nome_pt_br"]), int(row["offset_sigla"]),
         int(row["largura_sigla"]), str(row["hash_country_bin"]))
        for row in database_nationality_rows
    }
    database_affinities = {
        (int(row["codigo_jogo"]), row["nome_pt"], row["nome_tela"], bool(row["ausencia_legitima"]),
         bool(row["rotulo_confirmado"]), int(row["bit"]), int(row["largura"]), str(row["hash_coach_bin"]),
         bool(row["pode_rodar"]), row["falta_o_que"])
        for row in database_affinity_rows
    }
    database_styles = {
        (int(row["tecnico_id"]), row["codigo_estilo"], int(row["proficiencia"]), row["arquivo"],
         int(row["registro"]), int(row["bit"]), int(row["largura"]), str(row["hash_coach_bin"]),
         bool(row["confirmado"]))
        for row in database_style_rows
    }
    database_boosts = {
        (int(row["tecnico_id"]), int(row["ordem"]), row["codigo_atributo"], int(row["delta"]),
         row["arquivo"], int(row["registro"]), int(row["bit"]), int(row["largura"]),
         str(row["hash_coach_bin"]), bool(row["confirmado"]))
        for row in database_boost_rows
    }
    checks = {
        "technicians": _compare(source_technicians, database_technicians),
        "nationalities": _compare(source_nationalities, database_nationalities),
        "affinities": _compare(source_affinities, database_affinities),
        "proficiencies_and_overload": _compare(source_styles, database_styles),
        "boosts": _compare(source_boosts, database_boosts),
        "foreign_key_orphans": orphan_rows,
        "consumer_readiness": readiness,
        "preserved_fronts": preserved,
    }
    exact = all(checks[name]["exact"] for name in (
        "technicians", "nationalities", "affinities", "proficiencies_and_overload", "boosts"
    ))
    expected_counts = (
        len(source_styles) == 7_391 and len(source_boosts) == 104
        and preserved == {"textos": 11_679, "cartas": 43_072, "efeitos_impeto": 2_072}
    )
    passed = exact and expected_counts and not any(orphan_rows.values())
    return {
        "contract": CONTRACT,
        "transaction_read_only": True,
        "database_write": False,
        "preserved_schema": "clube",
        "checks": checks,
        "passed": passed,
        "result": "aprovado" if passed else "reabrir_frente",
    }
