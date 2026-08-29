"""Validador V4.6.10 de Técnicos orientado pelo conteúdo atual do banco.

Não fixa quantidades de técnicos, nacionalidades ou afinidades no código.
Divergências são devolvidas como relatório e não interrompem outras famílias.
"""
from __future__ import annotations

from typing import Any

import tecnicos as legacy


CONTRACT = "clubef-tecnicos-carga-v4-sobreposicao"


def _issue(name: str, comparison: dict[str, Any]) -> dict[str, Any] | None:
    if comparison.get("exact"):
        return None
    return {
        "family": name,
        "missing_in_database": int(comparison.get("missing_in_database") or 0),
        "extra_in_database": int(comparison.get("extra_in_database") or 0),
        "samples": comparison.get("samples") or {},
    }


def validate_tecnicos_v4610(snapshot: dict[str, Any], connection: Any) -> dict[str, Any]:
    if not isinstance(snapshot, dict) or snapshot.get("contract") != CONTRACT:
        raise ValueError("contrato físico de Técnicos incompatível")

    records = snapshot.get("records") or []
    nationalities = snapshot.get("nationalities") or []
    affinities = snapshot.get("affinities") or []
    if not isinstance(records, list) or not isinstance(nationalities, list) or not isinstance(affinities, list):
        raise ValueError("fotografia física de Técnicos possui catálogos inválidos")

    source_technicians = {
        (
            int(row["id"]),
            row.get("nome_en") or None,
            row.get("nome_jp") or None,
            row.get("nome_cn") or None,
            int(row["idade"]),
            int(row["nacionalidade_codigo"]),
            int(row["afinidade_codigo"]),
            int(row["record_index"]),
            str(row["source_file_sha256"]),
        )
        for row in records
    }
    source_nationalities = {
        (
            int(row["codigo_jogo"]),
            row.get("nome_pt_br"),
            row.get("sigla"),
            int(row["record_index"]),
            int(row["record_size"]),
            int(row["codigo_bit"]),
            int(row["codigo_largura"]),
            int(row["nome_offset"]),
            int(row["nome_largura"]),
            int(row["sigla_offset"]),
            int(row["sigla_largura"]),
            str(row["source_file_sha256"]),
        )
        for row in nationalities
    }
    source_affinities = {
        (
            int(row["codigo_jogo"]),
            row.get("nome_pt"),
            row.get("nome_tela"),
            bool(row.get("ausencia_legitima")),
            bool(row.get("rotulo_confirmado")),
            int(row["bit"]),
            int(row["largura"]),
            str(row["source_file_sha256"]),
            bool(row.get("pode_rodar")),
            row.get("falta_o_que"),
        )
        for row in affinities
    }

    source_styles: set[tuple[Any, ...]] = set()
    pending_boosts: list[tuple[Any, ...]] = []
    for row in records:
        record_file = legacy._source_file(row, f"técnico {row.get('id')}")
        for code, value in (row.get("proficiencias") or {}).items():
            evidence = (row.get("proficiencias_fisico") or {}).get(code) or {}
            bit, width = legacy._physical(evidence, f"proficiência {code}")
            source_styles.add(
                (
                    int(row["id"]),
                    code,
                    int(value),
                    str(evidence.get("arquivo") or record_file),
                    int(row["record_index"]),
                    bit,
                    width,
                    str(row["source_file_sha256"]),
                    True,
                )
            )
        for boost in row.get("boosts") or []:
            bit, width = legacy._physical(boost, "boost de técnico")
            pending_boosts.append(
                (
                    int(row["id"]),
                    int(boost["ordem"]),
                    int(boost["atributo_idx_canonico"]),
                    int(boost["delta"]),
                    str(boost.get("arquivo") or record_file),
                    int(row["record_index"]),
                    bit,
                    width,
                    str(row["source_file_sha256"]),
                    True,
                )
            )

    with connection.cursor() as cursor:
        cursor.execute("show transaction_read_only")
        if cursor.fetchone()[0] != "on":
            raise RuntimeError("a validação de Técnicos não ficou protegida como somente leitura")

        attrs = legacy._rows(
            cursor,
            "select indice_otimizador,codigo_atributo codigo "
            "from clube_novo.atributo_ordem_otimizador "
            "where indice_otimizador between 0 and 25",
        )
        tech = legacy._rows(
            cursor,
            "select id,nome_en,nome_jp,nome_cn,idade,codigo_nacionalidade,"
            "codigo_afinidade,registro_campos_apresentacao,hash_campos_apresentacao "
            "from clube_novo.tecnico_jogo "
            "where fonte_autoritativa='dt870_updated' "
            "and presente_dt870_atualizacao is true",
        )
        nat = legacy._rows(
            cursor,
            "select codigo_jogo,nome_pt_br,sigla,registro,tamanho_registro,"
            "bit_codigo,largura_codigo,offset_nome_pt_br,largura_nome_pt_br,"
            "offset_sigla,largura_sigla,hash_country_bin "
            "from clube_novo.nacionalidade_jogo",
        )
        aff = legacy._rows(
            cursor,
            "select codigo_jogo,nome_pt,nome_tela,ausencia_legitima,"
            "rotulo_confirmado,bit,largura,hash_coach_bin,pode_rodar,falta_o_que "
            "from clube_novo.afinidade_tecnico_jogo",
        )
        styles = legacy._rows(
            cursor,
            "select relation.tecnico_id,relation.codigo_estilo,relation.proficiencia,"
            "relation.arquivo,relation.registro,relation.bit,relation.largura,"
            "relation.hash_coach_bin,relation.confirmado "
            "from clube_novo.tecnico_estilo_jogo relation "
            "join clube_novo.tecnico_jogo tecnico on tecnico.id=relation.tecnico_id "
            "where tecnico.fonte_autoritativa='dt870_updated' "
            "and tecnico.presente_dt870_atualizacao is true",
        )
        boosts = legacy._rows(
            cursor,
            "select relation.tecnico_id,relation.ordem,relation.codigo_atributo,"
            "relation.delta,relation.arquivo,relation.registro,relation.bit,"
            "relation.largura,relation.hash_coach_bin,relation.confirmado "
            "from clube_novo.tecnico_atributo_jogo relation "
            "join clube_novo.tecnico_jogo tecnico on tecnico.id=relation.tecnico_id "
            "where tecnico.fonte_autoritativa='dt870_updated' "
            "and tecnico.presente_dt870_atualizacao is true",
        )
        orphans = legacy._rows(
            cursor,
            "select "
            "(select count(*) from clube_novo.tecnico_jogo t "
            " left join clube_novo.nacionalidade_jogo n "
            " on n.codigo_jogo=t.codigo_nacionalidade "
            " where t.fonte_autoritativa='dt870_updated' and n.codigo_jogo is null)::int nacionalidade,"
            "(select count(*) from clube_novo.tecnico_jogo t "
            " left join clube_novo.afinidade_tecnico_jogo a "
            " on a.codigo_jogo=t.codigo_afinidade "
            " where t.fonte_autoritativa='dt870_updated' and a.codigo_jogo is null)::int afinidade,"
            "(select count(*) from clube_novo.tecnico_estilo_jogo r "
            " left join clube_novo.tecnico_jogo t on t.id=r.tecnico_id "
            " where t.id is null)::int estilo_tecnico,"
            "(select count(*) from clube_novo.tecnico_atributo_jogo r "
            " left join clube_novo.tecnico_jogo t on t.id=r.tecnico_id "
            " where t.id is null)::int boost_tecnico",
        )[0]

    attr_codes = {int(row["indice_otimizador"]): str(row["codigo"]) for row in attrs}
    unresolved = sorted({row[2] for row in pending_boosts} - set(attr_codes))
    if unresolved:
        raise ValueError(f"boost de Técnico sem atributo canônico: {unresolved[0]}")
    source_boosts = {
        (row[0], row[1], attr_codes[row[2]], *row[3:]) for row in pending_boosts
    }

    database_technicians = {
        (
            int(row["id"]), row["nome_en"], row["nome_jp"], row["nome_cn"],
            int(row["idade"]), int(row["codigo_nacionalidade"]),
            int(row["codigo_afinidade"]), int(row["registro_campos_apresentacao"]),
            str(row["hash_campos_apresentacao"]),
        )
        for row in tech
    }
    database_nationalities = {
        (
            int(row["codigo_jogo"]), row["nome_pt_br"], row["sigla"],
            int(row["registro"]), int(row["tamanho_registro"]),
            int(row["bit_codigo"]), int(row["largura_codigo"]),
            int(row["offset_nome_pt_br"]), int(row["largura_nome_pt_br"]),
            int(row["offset_sigla"]), int(row["largura_sigla"]),
            str(row["hash_country_bin"]),
        )
        for row in nat
    }
    database_affinities = {
        (
            int(row["codigo_jogo"]), row["nome_pt"], row["nome_tela"],
            bool(row["ausencia_legitima"]), bool(row["rotulo_confirmado"]),
            int(row["bit"]), int(row["largura"]), str(row["hash_coach_bin"]),
            bool(row["pode_rodar"]), row["falta_o_que"],
        )
        for row in aff
    }
    database_styles = {
        (
            int(row["tecnico_id"]), row["codigo_estilo"], int(row["proficiencia"]),
            row["arquivo"], int(row["registro"]), int(row["bit"]),
            int(row["largura"]), str(row["hash_coach_bin"]), bool(row["confirmado"]),
        )
        for row in styles
    }
    database_boosts = {
        (
            int(row["tecnico_id"]), int(row["ordem"]), row["codigo_atributo"],
            int(row["delta"]), row["arquivo"], int(row["registro"]),
            int(row["bit"]), int(row["largura"]), str(row["hash_coach_bin"]),
            bool(row["confirmado"]),
        )
        for row in boosts
    }

    checks = {
        "technicians": legacy._compare(source_technicians, database_technicians),
        "nationalities": legacy._compare(source_nationalities, database_nationalities),
        "affinities": legacy._compare(source_affinities, database_affinities),
        "proficiencies_and_overload": legacy._compare(source_styles, database_styles),
        "boosts": legacy._compare(source_boosts, database_boosts),
        "foreign_key_orphans": orphans,
    }
    issues = [
        issue
        for name in (
            "technicians", "nationalities", "affinities",
            "proficiencies_and_overload", "boosts",
        )
        if (issue := _issue(name, checks[name])) is not None
    ]
    if any(int(value or 0) for value in orphans.values()):
        issues.append({"family": "foreign_key_orphans", "counts": orphans})

    passed = not issues
    return {
        "contract": CONTRACT,
        "authority": "clube_novo",
        "transaction_read_only": True,
        "database_write": False,
        "preserved_schema": "clube",
        "continue_pipeline": True,
        "application_blocked": not passed,
        "requested_by_database": {
            "technicians": len(database_technicians),
            "nationalities": len(database_nationalities),
            "affinities": len(database_affinities),
            "proficiencies_and_overload": len(database_styles),
            "boosts": len(database_boosts),
        },
        "extracted": {
            "technicians": len(source_technicians),
            "nationalities": len(source_nationalities),
            "affinities": len(source_affinities),
            "proficiencies_and_overload": len(source_styles),
            "boosts": len(source_boosts),
        },
        "checks": checks,
        "issues": issues,
        "passed": passed,
        "result": "aprovado" if passed else "divergencias_registradas",
    }
