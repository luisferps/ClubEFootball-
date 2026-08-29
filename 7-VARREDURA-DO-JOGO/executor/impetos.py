"""Validação read-only, integral e com proveniência dos Ímpetos.

O validador não conhece endereços físicos próprios. Tamanho de registro, bits,
larguras e arquivos são consumidos da fotografia/field_contract produzida pelo
Extrator a partir das referências canônicas de clube_novo.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any, Iterable

CONTRACT = "clubef-impetos-physical-v1"


def _rows(cursor: Any, query: str) -> list[dict[str, Any]]:
    cursor.execute(query)
    names = [description.name for description in cursor.description]
    return [dict(zip(names, values, strict=True)) for values in cursor.fetchall()]


def _order_key(row: tuple[Any, ...]) -> str:
    return json.dumps(row, ensure_ascii=False, separators=(",", ":"), default=str)


def _sha256(rows: Iterable[tuple[Any, ...]]) -> str:
    digest = hashlib.sha256()
    for row in sorted(rows, key=_order_key):
        digest.update(_order_key(row).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _compare(source: set[tuple[Any, ...]], database: set[tuple[Any, ...]]) -> dict[str, Any]:
    missing = sorted(source - database, key=_order_key)
    extra = sorted(database - source, key=_order_key)
    return {
        "source": len(source), "database": len(database),
        "missing_in_database": len(missing), "extra_in_database": len(extra),
        "source_sha256": _sha256(source), "database_sha256": _sha256(database),
        "samples": {"missing": missing[:10], "extra": extra[:10]},
        "exact": not missing and not extra,
    }


def _detail(record: dict[str, Any], role: str) -> dict[str, Any]:
    details = (record.get("source_details") or {}).get(role) or []
    return details[0] if details else {}


def _int(value: Any, label: str) -> int:
    if not isinstance(value, int):
        raise ValueError(f"{label} ausente na fotografia física")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} ausente na fotografia física")
    return value


def _field(snapshot: dict[str, Any], name: str) -> dict[str, Any]:
    row = (snapshot.get("field_contract") or {}).get(name)
    if not isinstance(row, dict):
        raise ValueError(f"field_contract de Ímpetos sem {name}")
    return row


def validate_impetos(snapshot: dict[str, Any], connection: Any) -> dict[str, Any]:
    if snapshot.get("contract") != CONTRACT:
        raise ValueError("contrato físico de Ímpetos inválido")

    union = snapshot.get("records") or []
    if len(union) != 440 or len({str(record.get("id")) for record in union}) != 440:
        raise ValueError("a união física de Ímpetos não contém 440 códigos únicos")
    current = [record for record in union if record.get("preferred_source") == "dt870_updated" and record.get("tipo_condicao_status") == "coletado"]
    if len(current) != 407:
        raise ValueError(f"a fonte atual contém {len(current)} condições reais; esperado 407")

    record_size = _int(snapshot.get("record_size"), "tamanho de registro de PlayerBooster")
    source_file = _text(snapshot.get("file"), "arquivo do catálogo de Ímpetos")
    code_contract = _field(snapshot, "codigo")
    type_contract = _field(snapshot, "tipo")
    type_mirror_contract = _field(snapshot, "tipo_espelho")
    nationality_contract = _field(snapshot, "nacionalidade")
    league_contract = _field(snapshot, "liga")
    candidate_contract = _field(snapshot, "classe_candidato")
    owner_contract = _field(snapshot, "classe_dono")
    cutoff_contract = _field(snapshot, "corte")
    max_contract = _field(snapshot, "efeito_maximo")
    league_members_contract = _field(snapshot, "liga_membros")
    member_source_file = _text(league_members_contract.get("arquivo"), "arquivo de membros de liga")

    source_union = {
        (
            int(record["id"]), record_size, _int(code_contract.get("bit"), "bit do código do ímpeto"),
            _int(code_contract.get("largura"), "largura do código do ímpeto"),
            _detail(record, "dt200").get("record_index"),
            _detail(record, "dt870_original").get("record_index"),
            _detail(record, "dt870_updated").get("record_index"),
            bool((record.get("source_details") or {}).get("dt200")),
            bool((record.get("source_details") or {}).get("dt870_original")),
            bool((record.get("source_details") or {}).get("dt870_updated")),
        )
        for record in union
    }

    source_effects = {
        (
            int(record["id"]), effect["codigo_atributo"], int(effect["delta"]),
            _int(effect.get("bit_delta"), "bit_delta do efeito"), _int(effect.get("largura_delta"), "largura_delta do efeito"),
            int(_detail(record, "dt870_updated")["record_index"]),
            _text(effect.get("arquivo_origem"), "arquivo de origem do efeito"),
            _text(effect.get("fonte_origem"), "fonte de origem do efeito"),
        )
        for record in current for effect in record.get("efeitos") or []
    }

    source_conditions = {
        (
            int(record["id"]), record.get("criterio_codigo"), int(record["tipo_condicao_raw"]),
            source_file, record_size,
            int(_detail(record, "dt870_updated")["record_index"]), _detail(record, "dt870_updated").get("record_sha256"),
            _int(type_contract.get("bit"), "bit do tipo de condição"), _int(type_contract.get("largura"), "largura do tipo de condição"),
            _int(type_mirror_contract.get("bit"), "bit espelho do tipo"), _int(type_mirror_contract.get("largura"), "largura espelho do tipo"),
        )
        for record in current
    }

    source_ranges = {
        (int(record["id"]), order, int(item["quantidade_minima"]), int(item["quantidade_maxima"]), int(item["delta"]))
        for record in current for order, item in enumerate(record.get("faixas") or [], start=1)
    }
    source_parameters = {
        (
            int(record["id"]), int(record["corte_raw"]), _int(cutoff_contract.get("bit"), "bit do corte"),
            _int(cutoff_contract.get("largura"), "largura do corte"), int(record["efeito_maximo"]),
            _int(max_contract.get("bit"), "bit do efeito máximo"), _int(max_contract.get("largura"), "largura do efeito máximo"),
            _detail(record, "dt870_updated").get("record_sha256"),
        )
        for record in current if int(record["tipo_condicao_raw"]) == 2
    }
    source_nationality_targets = {
        (
            int(record["id"]), int(record["alvo_codigo"]), source_file, record_size,
            int(_detail(record, "dt870_updated")["record_index"]), _int(nationality_contract.get("bit"), "bit do alvo nacionalidade"),
            _int(nationality_contract.get("largura"), "largura do alvo nacionalidade"), _detail(record, "dt870_updated").get("record_sha256"),
        )
        for record in current if record.get("alvo_tipo") == "nacionalidade_regiao"
    }
    source_league_targets = {
        (
            int(record["id"]), int(record["alvo_codigo"]), source_file, record_size,
            int(_detail(record, "dt870_updated")["record_index"]), _int(league_contract.get("bit"), "bit do alvo liga"),
            _int(league_contract.get("largura"), "largura do alvo liga"), _detail(record, "dt870_updated").get("record_sha256"),
        )
        for record in current if record.get("alvo_tipo") == "liga_categoria"
    }
    source_club_targets = {(int(record["id"]), int(record["alvo_codigo"])) for record in current if record.get("alvo_tipo") == "clube_equipe"}
    source_classes = {
        (
            int(record["id"]), int(record["classe_dono"]), _int(owner_contract.get("bit"), "bit classe dono"),
            _int(owner_contract.get("largura"), "largura classe dono"), _int(candidate_contract.get("bit"), "bit classe candidato"),
            _int(candidate_contract.get("largura"), "largura classe candidato"),
        )
        for record in current if int(record.get("classe_dono") or 0) > 0
    }

    league_targets = {int(record["id"]): int(record["alvo_codigo"]) for record in current if record.get("alvo_tipo") == "liga_categoria"}
    current_by_code = {int(record["id"]): record for record in current}
    source_members: set[tuple[Any, ...]] = set()
    member_record_size = _int(league_members_contract.get("tamanho_registro"), "tamanho de CompetitionUnit")
    for code, target in league_targets.items():
        booster_detail = _detail(current_by_code[code], "dt870_updated")
        for member in snapshot.get("liga_membros") or []:
            if int(member["codigo_liga_alvo_base"]) != target:
                continue
            if member["papel_fisico"] == "alvo_base":
                provenance = (
                    source_file, record_size, int(booster_detail["record_index"]),
                    _int(league_contract.get("bit"), "bit do alvo liga"), _int(league_contract.get("largura"), "largura do alvo liga"), booster_detail.get("record_sha256"),
                )
            else:
                provenance = (
                    member_source_file, member_record_size, int(member["record_index"]),
                    int(member["bit_inicial"]), int(member["largura"]), member.get("record_sha256"),
                )
            source_members.add((code, int(member["codigo_liga_membro"]), int(member["ordem_fisica"]), int(member["codigo_liga_alvo_base"]), member["papel_fisico"], *provenance))

    with connection.cursor() as cursor:
        cursor.execute("show transaction_read_only")
        if cursor.fetchone()[0] != "on":
            raise RuntimeError("a validação de Ímpetos não ficou protegida como somente leitura")
        database_union_rows = _rows(cursor, "select codigo_jogo,tamanho_registro,bit_codigo,largura_codigo,registro_dt200,registro_dt870_steam,registro_dt870_atualizacao,presente_dt200,presente_dt870_steam,presente_dt870_atualizacao from clube_novo.impeto_jogo")
        database_effect_rows = _rows(cursor, "select codigo_impeto,codigo_atributo,delta,bit_delta,largura_delta,registro_origem,arquivo_origem,fonte_origem from clube_novo.impeto_atributo_jogo")
        database_condition_rows = _rows(cursor, "select codigo_impeto,criterio_codigo,tipo_raw,arquivo_origem,tamanho_registro,indice_registro,registro_sha256,bit_tipo,largura_tipo,bit_tipo_espelho,largura_tipo_espelho from clube_novo.impeto_condicao_jogo")
        database_range_rows = _rows(cursor, "select codigo_impeto,ordem,quantidade_minima,quantidade_maxima,delta from clube_novo.impeto_condicao_faixa_jogo")
        database_parameter_rows = _rows(cursor, "select codigo_impeto,corte_raw,bit_corte,largura_corte,efeito_maximo,bit_efeito_maximo,largura_efeito_maximo,registro_sha256 from clube_novo.impeto_condicao_parametro_faixa_jogo")
        database_nationality_rows = _rows(cursor, "select codigo_impeto,codigo_nacionalidade,arquivo_origem,tamanho_registro,indice_registro,bit_alvo,largura_alvo,registro_sha256 from clube_novo.impeto_condicao_nacionalidade_jogo")
        database_league_rows = _rows(cursor, "select codigo_impeto,codigo_liga_categoria,arquivo_origem,tamanho_registro,indice_registro,bit_alvo,largura_alvo,registro_sha256 from clube_novo.impeto_condicao_liga_jogo")
        database_club_rows = _rows(cursor, "select codigo_impeto,codigo_clube from clube_novo.impeto_condicao_clube_jogo")
        database_class_rows = _rows(cursor, "select codigo_impeto,classe_dono,bit_classe_dono,largura_classe_dono,bit_classe_candidato,largura_classe_candidato from clube_novo.impeto_condicao_classe_jogo")
        database_member_rows = _rows(cursor, "select codigo_impeto,codigo_liga_membro,ordem_fisica,codigo_liga_alvo_base,papel_fisico,arquivo_origem,tamanho_registro,indice_registro,bit_inicial,largura,registro_sha256 from clube_novo.impeto_condicao_liga_membro_jogo")
        slots = _rows(cursor, "select count(*)::int as total,count(*) filter (where codigo_impeto is not null)::int as preenchidos,count(*) filter (where vaga)::int as vagas from clube_novo.carta_impeto_jogo")[0]
        consumer = _rows(cursor, "select count(*) filter (where pode_rodar)::int as condicoes_aptas,count(*) filter (where not pode_rodar)::int as condicoes_bloqueadas from clube_novo.impeto_condicao_jogo")[0]
        provenance = _rows(cursor, "select (select count(*) from clube_novo.impeto_atributo_jogo where endereco_origem is not null and bit_delta is not null and registro_origem is not null)::int as efeitos_com_endereco,(select count(*) from clube_novo.impeto_condicao_jogo where registro_sha256 is not null and indice_registro is not null)::int as condicoes_com_registro,(select count(*) from clube_novo.impeto_condicao_liga_membro_jogo where registro_sha256 is not null and indice_registro is not null)::int as membros_com_registro")[0]
        preserved = _rows(cursor, "select (select count(*) from clube_novo.texto_do_jogo)::int as textos,(select count(*) from clube_novo.tecnico_jogo where fonte_autoritativa='dt870_updated')::int as tecnicos,(select count(*) from clube_novo.carta_jogo)::int as cartas")[0]

    database_union = {(int(row["codigo_jogo"]), int(row["tamanho_registro"]), int(row["bit_codigo"]), int(row["largura_codigo"]), row["registro_dt200"], row["registro_dt870_steam"], row["registro_dt870_atualizacao"], bool(row["presente_dt200"]), bool(row["presente_dt870_steam"]), bool(row["presente_dt870_atualizacao"])) for row in database_union_rows}
    database_effects = {(int(row["codigo_impeto"]), row["codigo_atributo"], int(row["delta"]), int(row["bit_delta"]), int(row["largura_delta"]), int(row["registro_origem"]), row["arquivo_origem"], row["fonte_origem"]) for row in database_effect_rows}
    database_conditions = {(int(row["codigo_impeto"]), row["criterio_codigo"], int(row["tipo_raw"]), row["arquivo_origem"], int(row["tamanho_registro"]), int(row["indice_registro"]), row["registro_sha256"], int(row["bit_tipo"]), int(row["largura_tipo"]), int(row["bit_tipo_espelho"]), int(row["largura_tipo_espelho"])) for row in database_condition_rows}
    database_ranges = {(int(row["codigo_impeto"]), int(row["ordem"]), int(row["quantidade_minima"]), int(row["quantidade_maxima"]), int(row["delta"])) for row in database_range_rows}
    database_parameters = {(int(row["codigo_impeto"]), int(row["corte_raw"]), int(row["bit_corte"]), int(row["largura_corte"]), int(row["efeito_maximo"]), int(row["bit_efeito_maximo"]), int(row["largura_efeito_maximo"]), row["registro_sha256"]) for row in database_parameter_rows}
    database_nationality_targets = {(int(row["codigo_impeto"]), int(row["codigo_nacionalidade"]), row["arquivo_origem"], int(row["tamanho_registro"]), int(row["indice_registro"]), int(row["bit_alvo"]), int(row["largura_alvo"]), row["registro_sha256"]) for row in database_nationality_rows}
    database_league_targets = {(int(row["codigo_impeto"]), int(row["codigo_liga_categoria"]), row["arquivo_origem"], int(row["tamanho_registro"]), int(row["indice_registro"]), int(row["bit_alvo"]), int(row["largura_alvo"]), row["registro_sha256"]) for row in database_league_rows}
    database_club_targets = {(int(row["codigo_impeto"]), int(row["codigo_clube"])) for row in database_club_rows}
    database_classes = {(int(row["codigo_impeto"]), int(row["classe_dono"]), int(row["bit_classe_dono"]), int(row["largura_classe_dono"]), int(row["bit_classe_candidato"]), int(row["largura_classe_candidato"])) for row in database_class_rows}
    database_members = {(int(row["codigo_impeto"]), int(row["codigo_liga_membro"]), int(row["ordem_fisica"]), int(row["codigo_liga_alvo_base"]), row["papel_fisico"], row["arquivo_origem"], int(row["tamanho_registro"]), int(row["indice_registro"]), int(row["bit_inicial"]), int(row["largura"]), row["registro_sha256"]) for row in database_member_rows}

    source_type_counts = dict(sorted(Counter(int(record["tipo_condicao_raw"]) for record in current).items()))
    database_type_counts = dict(sorted(Counter(int(row["tipo_raw"]) for row in database_condition_rows).items()))
    comparisons = {
        "union_catalog": _compare(source_union, database_union), "effects": _compare(source_effects, database_effects),
        "conditions": _compare(source_conditions, database_conditions), "ranges": _compare(source_ranges, database_ranges),
        "range_parameters": _compare(source_parameters, database_parameters), "nationality_targets": _compare(source_nationality_targets, database_nationality_targets),
        "league_targets": _compare(source_league_targets, database_league_targets), "club_targets": _compare(source_club_targets, database_club_targets),
        "classes": _compare(source_classes, database_classes), "competition_unit_members": _compare(source_members, database_members),
    }
    expected_types = {0: 131, 1: 30, 2: 232, 3: 8, 5: 6}
    counts_ok = (
        len(source_effects) == 2072 and len(source_conditions) == 407 and len(source_ranges) == 696
        and len(source_nationality_targets) == 203 and len(source_league_targets) == 19
        and len(source_classes) == 10 and len(source_members) == 35 and not source_club_targets
        and source_type_counts == expected_types and database_type_counts == expected_types
        and slots == {"total": 3748, "preenchidos": 2381, "vagas": 1367}
        and provenance == {"efeitos_com_endereco": 2072, "condicoes_com_registro": 407, "membros_com_registro": 35}
        and preserved == {"textos": 11679, "tecnicos": 1478, "cartas": 43072}
    )
    passed = all(item["exact"] for item in comparisons.values()) and counts_ok and consumer["condicoes_aptas"] == 0
    return {
        "contract": CONTRACT, "transaction_read_only": True, "database_write": False, "preserved_schema": "clube",
        "checks": {**comparisons, "type_counts": {"source": source_type_counts, "database": database_type_counts, "exact": source_type_counts == database_type_counts}, "slots": slots, "address_and_provenance": provenance, "consumer_readiness": consumer, "preserved_fronts": preserved},
        "passed": passed, "result": "aprovado" if passed else "reabrir_frente",
    }
