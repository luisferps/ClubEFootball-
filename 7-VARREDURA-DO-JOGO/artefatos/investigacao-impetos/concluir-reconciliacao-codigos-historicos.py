"""Consolida, sem escrita, o limite factual dos códigos históricos deslocados."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXECUTOR = ROOT / "executor"
if str(EXECUTOR) not in sys.path:
    sys.path.insert(0, str(EXECUTOR))
import executor_local as ex  # noqa: E402


HERE = Path(__file__).resolve().parent
LAYOUT = HERE / "diagnostico-layout-playerbooster-original.json"
OUTPUT = HERE / "conclusao-reconciliacao-codigos-historicos.json"
TARGETS = [204,209,214,219,224,229,234,239,244,249,254,259,269,274,279,284,289,294,299,309,334,369]


def rows(cursor, query: str, params=()):
    cursor.execute(query, params)
    names = [column.name for column in cursor.description]
    return [dict(zip(names, values, strict=True)) for values in cursor.fetchall()]


def main() -> None:
    layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
    by_target = {item["database_code"]: item for item in layout["historical_displacement_candidates"]}
    # O alvo 334 é o quinto caso em que o mesmo código canônico também possui
    # conteúdo atual; ele não estava na lista "missing" do relatório antigo.
    if 334 not in by_target:
        raise RuntimeError("o diagnóstico físico precisa ser regenerado incluindo o alvo 334")
    psycopg, _, _ = ex.import_psycopg()
    dsn = ex.connection_string()
    evidence = []
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        with connection.cursor() as cursor:
            cursor.execute("set transaction read only")
            for target in TARGETS:
                physical = by_target[target]
                catalog = rows(
                    cursor,
                    "select codigo_jogo,registro_dt870_steam,registro_dt870_atualizacao,"
                    "presente_dt870_steam,presente_dt870_atualizacao from "
                    "clube_novo.impeto_jogo where codigo_jogo=%s",
                    (target,),
                )
                if len(catalog) != 1:
                    raise RuntimeError(f"alvo {target} sem uma linha canônica única")
                cursor.execute("select count(*) from clube_novo.impeto_atributo_jogo where codigo_impeto=%s", (target,))
                effect_count = cursor.fetchone()[0]
                cursor.execute("select count(*) from clube_novo.impeto_condicao_jogo where codigo_impeto=%s", (target,))
                condition_count = cursor.fetchone()[0]
                cursor.execute("select count(*) from clube_novo.impeto_condicao_faixa_jogo where codigo_impeto=%s", (target,))
                range_count = cursor.fetchone()[0]
                cursor.execute("select count(*),count(distinct card_id) from clube_novo.carta_impeto_jogo where codigo_impeto=%s and not vaga", (target,))
                target_slots, target_cards = cursor.fetchone()
                raw_code = int(physical["raw_code_bit112_w10"])
                cursor.execute("select exists(select 1 from clube_novo.impeto_jogo where codigo_jogo=%s)", (raw_code,))
                raw_code_exists_in_catalog = cursor.fetchone()[0]
                cursor.execute("select count(*),count(distinct card_id) from clube_novo.carta_impeto_jogo where codigo_impeto=%s and not vaga", (raw_code,))
                raw_slots, raw_cards = cursor.fetchone()
                db = catalog[0]
                provenance_matches = int(db["registro_dt870_steam"]) == int(physical["mapped_record_number_one_based"])
                plus_one_observed = target == raw_code + 1
                evidence.append({
                    "database_code": target,
                    "raw_code": raw_code,
                    "record_number_one_based": physical["mapped_record_number_one_based"],
                    "record_sha256": physical["record_sha256"],
                    "provenance_record_matches": provenance_matches,
                    "plus_one_observed": plus_one_observed,
                    "database_content_available": {
                        "effects": effect_count,
                        "conditions": condition_count,
                        "ranges": range_count,
                    },
                    "usage": {
                        "database_code": {"slots": target_slots, "cards": target_cards},
                        "raw_code": {"slots": raw_slots, "cards": raw_cards},
                    },
                    "has_current_updated_variant": bool(db["presente_dt870_atualizacao"]),
                    "raw_code_also_exists_in_catalog": raw_code_exists_in_catalog,
                    "semantic_collision_risk": raw_code_exists_in_catalog or bool(db["presente_dt870_atualizacao"]),
                    "status": "alerta_sem_prova_semantica_completa",
                    "missing_proof": [
                        "decodificador físico validado para condição/alvos/efeitos/faixas do formato legado",
                        "conteúdo histórico normalizado/fingerprint no clube_novo para comparação independente",
                    ],
                })
    report = {
        "schema": "clubef-conclusao-reconciliacao-codigos-historicos-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "database_write": False,
        "rule_global_plus_one_applied": False,
        "source": {
            "cpk": layout["original"]["cpk_path"],
            "cpk_sha256": layout["original"]["cpk_sha256"],
            "player_booster_sha256": layout["original"]["player_booster_sha256"],
            "layout_observed": "prefixo 24 bytes + 165 blocos de 40 bytes",
        },
        "pairs_examined": len(evidence),
        "records_with_exact_provenance_and_plus_one": sum(
            item["provenance_record_matches"] and item["plus_one_observed"] for item in evidence
        ),
        "pairs_with_complete_semantic_proof": 0,
        "decision": "nenhum_par_promovido; manter_novo_removido_alterado_como_alerta",
        "reason": (
            "o padrão de código e registro é físico, mas condição, alvos, efeitos e faixas "
            "do layout legado não têm decodificador comprovado; aplicar o deslocamento "
            "misturaria variantes atuais reais nos códigos 208, 268, 308, 334 e 368"
        ),
        "evidence": evidence,
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT),
        "pairs_examined": report["pairs_examined"],
        "exact_provenance_plus_one": report["records_with_exact_provenance_and_plus_one"],
        "complete_semantic_proof": report["pairs_with_complete_semantic_proof"],
        "decision": report["decision"],
        "semantic_collision_pairs": [
            {"raw_code": item["raw_code"], "database_code": item["database_code"]}
            for item in evidence if item["semantic_collision_risk"]
        ],
        "target_slots": sum(item["usage"]["database_code"]["slots"] for item in evidence),
        "raw_code_slots": sum(item["usage"]["raw_code"]["slots"] for item in evidence),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
