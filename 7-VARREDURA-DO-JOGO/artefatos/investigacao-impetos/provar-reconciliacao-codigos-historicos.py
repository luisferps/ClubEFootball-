"""Prova read-only de pares código físico histórico -> código canônico antigo.

Cada par é aceito somente quando o registro de PlayerBooster da fonte Steam
original é localizado pelo índice de procedência e condição, alvos, efeitos e
faixas normalizados coincidem. Não existe regra global +1 neste diagnóstico.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXECUTOR = ROOT / "executor"
if str(EXECUTOR) not in sys.path:
    sys.path.insert(0, str(EXECUTOR))

import executor_local as ex  # noqa: E402


RUN = ROOT / "artefatos" / "desktop" / "run-20260830-005609"
PHYSICAL = RUN / "metadados-fisicos.json"
OUTPUT = Path(__file__).resolve().parent / "prova-reconciliacao-codigos-historicos.json"
MISSING_TARGETS = [
    204, 209, 214, 219, 224, 229, 234, 239, 244, 249, 254,
    259, 269, 274, 279, 284, 289, 294, 299, 309, 369,
]


def rows(cursor, query: str, params=()):
    cursor.execute(query, params)
    names = [column.name for column in cursor.description]
    return [dict(zip(names, values, strict=True)) for values in cursor.fetchall()]


def effects(cursor, code: int):
    result = rows(
        cursor,
        "select codigo_atributo,delta,bit_delta,largura_delta from "
        "clube_novo.impeto_atributo_jogo where codigo_impeto=%s "
        "order by codigo_atributo,delta,bit_delta,largura_delta",
        (code,),
    )
    return [tuple(item[key] for key in ("codigo_atributo", "delta", "bit_delta", "largura_delta")) for item in result]


def ranges(cursor, code: int):
    result = rows(
        cursor,
        "select quantidade_minima,quantidade_maxima,delta from "
        "clube_novo.impeto_condicao_faixa_jogo where codigo_impeto=%s "
        "order by ordem",
        (code,),
    )
    return [tuple(item[key] for key in ("quantidade_minima", "quantidade_maxima", "delta")) for item in result]


def target_rows(cursor, code: int):
    return {
        "nacionalidade_regiao": rows(
            cursor,
            "select codigo_nacionalidade from clube_novo.impeto_condicao_nacionalidade_jogo "
            "where codigo_impeto=%s order by codigo_nacionalidade",
            (code,),
        ),
        "liga_categoria": rows(
            cursor,
            "select codigo_liga_categoria from clube_novo.impeto_condicao_liga_jogo "
            "where codigo_impeto=%s order by codigo_liga_categoria",
            (code,),
        ),
        "clube": rows(
            cursor,
            "select codigo_clube from clube_novo.impeto_condicao_clube_jogo "
            "where codigo_impeto=%s order by ordem,codigo_clube",
            (code,),
        ),
        "classe": rows(
            cursor,
            "select classe_dono from clube_novo.impeto_condicao_classe_jogo where codigo_impeto=%s",
            (code,),
        ),
        "outro": rows(
            cursor,
            "select seletor_raw from clube_novo.impeto_condicao_outro_jogo where codigo_impeto=%s",
            (code,),
        ),
    }


def expected_targets(detail: dict):
    result = {"nacionalidade_regiao": [], "liga_categoria": [], "clube": [], "classe": [], "outro": []}
    target_type = detail.get("alvo_tipo")
    target_code = detail.get("alvo_codigo")
    if target_type == "nacionalidade_regiao" and target_code:
        result[target_type] = [{"codigo_nacionalidade": target_code}]
    elif target_type == "liga_categoria" and target_code:
        result[target_type] = [{"codigo_liga_categoria": target_code}]
    elif target_type == "clube" and target_code:
        result[target_type] = [{"codigo_clube": target_code}]
    return result


def main() -> None:
    physical = json.loads(PHYSICAL.read_text(encoding="utf-8"))
    catalog = {int(item["id"]): item for item in physical["catalogs"]["impetos"]["records"]}
    psycopg, _, _ = ex.import_psycopg()
    dsn = ex.connection_string()
    if not dsn:
        raise RuntimeError("conexão segura com clube_novo indisponível")
    proof = []
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        with connection.cursor() as cursor:
            cursor.execute("set transaction read only")
            for target in MISSING_TARGETS:
                physical_code = target - 1
                db_rows = rows(
                    cursor,
                    "select codigo_jogo,registro_dt870_steam,registro_dt870_atualizacao,"
                    "presente_dt870_steam,presente_dt870_atualizacao,condicional,"
                    "tipo_condicao_raw,condicao_estado,nome_pt,falta_o_que "
                    "from clube_novo.impeto_jogo where codigo_jogo=%s",
                    (target,),
                )
                if len(db_rows) != 1:
                    raise RuntimeError(f"código canônico {target} não retornou exatamente uma linha")
                db = db_rows[0]
                candidates = [
                    detail
                    for detail in catalog.get(physical_code, {}).get("source_details", {}).get("dt870_original", [])
                    if detail["record_index"] + 1 == db["registro_dt870_steam"]
                ]
                if len(candidates) != 1:
                    proof.append({
                        "physical_code": physical_code,
                        "database_code": target,
                        "status": "sem_registro_fisico_unico_pela_procedencia",
                        "candidate_count": len(candidates),
                        "db": db,
                    })
                    continue
                detail = candidates[0]
                physical_effects = sorted(
                    (
                        item["codigo_atributo"], item["delta"],
                        item["bit_delta"], item["largura_delta"],
                    )
                    for item in detail["efeitos"]
                )
                db_effects = effects(cursor, target)
                physical_ranges = sorted(
                    (item["quantidade_minima"], item["quantidade_maxima"], item["delta"])
                    for item in detail["faixas"]
                )
                db_ranges = ranges(cursor, target)
                db_conditions = rows(
                    cursor,
                    "select criterio_codigo,tipo_raw from clube_novo.impeto_condicao_jogo "
                    "where codigo_impeto=%s order by criterio_codigo",
                    (target,),
                )
                expected_condition = (
                    not db["condicional"]
                    and detail["criterio_codigo"] == "sempre_ativo"
                    and not db_conditions
                ) or (
                    db["condicional"]
                    and len(db_conditions) == 1
                    and db_conditions[0]["criterio_codigo"] == detail["criterio_codigo"]
                    and db_conditions[0]["tipo_raw"] == detail["tipo_condicao_raw"]
                )
                actual_targets = target_rows(cursor, target)
                wanted_targets = expected_targets(detail)
                checks = {
                    "provenance_record": detail["record_index"] + 1 == db["registro_dt870_steam"],
                    "source_role": detail["source_role"] == "dt870_original",
                    "condition_raw": db["tipo_condicao_raw"] == detail["tipo_condicao_raw"],
                    "condition_semantics": expected_condition,
                    "targets": actual_targets == wanted_targets,
                    "effects": db_effects == physical_effects,
                    "ranges": db_ranges == physical_ranges,
                }
                proof.append({
                    "physical_code": physical_code,
                    "database_code": target,
                    "status": "comprovado" if all(checks.values()) else "divergente",
                    "checks": checks,
                    "physical_provenance": {
                        "source_role": detail["source_role"],
                        "source_file_sha256": detail["source_file_sha256"],
                        "record_index_zero_based": detail["record_index"],
                        "record_number_one_based": detail["record_index"] + 1,
                        "record_sha256": detail["record_sha256"],
                    },
                    "condition": {
                        "physical": {"criterio": detail["criterio_codigo"], "tipo_raw": detail["tipo_condicao_raw"]},
                        "database": {"condicional": db["condicional"], "tipo_raw": db["tipo_condicao_raw"], "rows": db_conditions},
                    },
                    "targets": {"physical": wanted_targets, "database": actual_targets},
                    "effects": {"physical": physical_effects, "database": db_effects},
                    "ranges": {"physical": physical_ranges, "database": db_ranges},
                })
    proven = [item for item in proof if item["status"] == "comprovado"]
    report = {
        "schema": "clubef-prova-reconciliacao-codigos-historicos-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "rule_global_plus_one_used": False,
        "physical_artifact": str(PHYSICAL),
        "physical_artifact_sha256": hashlib.sha256(PHYSICAL.read_bytes()).hexdigest(),
        "pairs_tested": len(proof),
        "pairs_proven": len(proven),
        "pairs_divergent_or_unproven": len(proof) - len(proven),
        "proof": proof,
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT),
        "pairs_tested": report["pairs_tested"],
        "pairs_proven": report["pairs_proven"],
        "unproven": [
            {"physical": item["physical_code"], "database": item["database_code"], "status": item["status"], "checks": item.get("checks")}
            for item in proof if item["status"] != "comprovado"
        ],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
