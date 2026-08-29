"""Pré-voo somente leitura da normalização de ímpetos em clube_novo."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path


def load_executor(executor_path: Path):
    vendor = executor_path.parent / "vendor"
    sys.path.insert(0, str(vendor))
    spec = importlib.util.spec_from_file_location("clubef_executor", executor_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Não foi possível carregar o executor local.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fingerprint(rows: list[dict], include_order: bool = True) -> str:
    parts = []
    for row in sorted(rows, key=lambda item: (int(item["codigo_impeto"]), item["codigo_atributo"])):
        values = [str(row["codigo_impeto"]), row["codigo_atributo"]]
        if include_order:
            values.append(str(row["ordem"]))
        parts.append("|".join(values))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def fetch_dicts(cursor, query: str, params=None) -> list[dict]:
    cursor.execute(query, params)
    columns = [description.name for description in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit(
            "Uso: preflight-banco-impetos.py <executor_local.py> "
            "<MATRIZ-RECEITAS-CANDIDATAS.csv> <manifesto-fisico.json> <saida.json>"
        )

    executor_path = Path(sys.argv[1]).resolve()
    matrix_path = Path(sys.argv[2]).resolve()
    physical_manifest_path = Path(sys.argv[3]).resolve()
    output_path = Path(sys.argv[4]).resolve()

    executor = load_executor(executor_path)
    dsn = executor.connection_string()
    if not dsn:
        raise RuntimeError("A configuração local segura do banco não está disponível.")
    psycopg, _, _ = executor.import_psycopg()

    with matrix_path.open("r", encoding="utf-8-sig", newline="") as handle:
        candidates = list(csv.DictReader(handle))
    physical_manifest = json.loads(physical_manifest_path.read_text(encoding="utf-8"))

    for row in candidates:
        row["codigo_impeto"] = int(row["codigo_impeto"])
        row["ordem"] = int(row["ordem"])
        row["delta_fisico"] = int(row["delta_fisico"])
        row["bit_delta"] = int(row["bit_delta"]) if row["bit_delta"] else None
        row["largura_delta"] = int(row["largura_delta"])
        row["registro_origem"] = int(row["registro_origem"])
        row["aplicavel_agora"] = row["aplicavel_agora"].lower() == "true"

    with psycopg.connect(dsn, connect_timeout=20) as connection:
        connection.read_only = True
        with connection.cursor() as cursor:
            cursor.execute("show transaction_read_only")
            read_only = cursor.fetchone()[0] == "on"
            if not read_only:
                raise RuntimeError("O pré-voo não ficou protegido como somente leitura.")

            columns = fetch_dicts(
                cursor,
                """
                select table_name,column_name,data_type,is_nullable,column_default
                from information_schema.columns
                where table_schema='clube_novo'
                  and table_name in ('atributo_jogo','impeto_jogo','impeto_atributo_jogo','carta_impeto_jogo')
                order by table_name,ordinal_position
                """,
            )
            constraints = fetch_dicts(
                cursor,
                """
                select rel.relname table_name,con.conname constraint_name,con.contype constraint_type,
                       pg_get_constraintdef(con.oid) definition
                from pg_constraint con
                join pg_class rel on rel.oid=con.conrelid
                join pg_namespace ns on ns.oid=rel.relnamespace
                where ns.nspname='clube_novo'
                  and rel.relname in ('atributo_jogo','impeto_jogo','impeto_atributo_jogo','carta_impeto_jogo')
                order by rel.relname,con.conname
                """,
            )
            indexes = fetch_dicts(
                cursor,
                """
                select tablename table_name,indexname index_name,indexdef definition
                from pg_indexes
                where schemaname='clube_novo'
                  and tablename in ('atributo_jogo','impeto_jogo','impeto_atributo_jogo','carta_impeto_jogo')
                order by tablename,indexname
                """,
            )
            counts = fetch_dicts(
                cursor,
                """
                select 'atributo_jogo' tabela,count(*) total,count(distinct codigo) chaves from clube_novo.atributo_jogo
                union all
                select 'impeto_jogo',count(*),count(distinct codigo_jogo) from clube_novo.impeto_jogo
                union all
                select 'impeto_atributo_jogo',count(*),count(distinct (codigo_impeto,codigo_atributo)) from clube_novo.impeto_atributo_jogo
                union all
                select 'carta_impeto_jogo',count(*),count(distinct (card_id,slot)) from clube_novo.carta_impeto_jogo
                order by tabela
                """,
            )
            relations = fetch_dicts(
                cursor,
                """
                select codigo_impeto,codigo_atributo,ordem,arquivo_origem
                from clube_novo.impeto_atributo_jogo
                order by codigo_impeto,codigo_atributo
                """,
            )
            attributes = fetch_dicts(
                cursor,
                "select codigo,idx_casa,nome_pt from clube_novo.atributo_jogo order by idx_casa",
            )
            legacy = fetch_dicts(
                cursor,
                "select impeto_id,atributo_idx,delta from clube.impeto_efeito order by impeto_id,atributo_idx",
            )
            catalog = fetch_dicts(
                cursor,
                """
                select codigo_jogo,registro_dt200,registro_dt870_steam,registro_dt870_atualizacao,
                       presente_dt200,presente_dt870_steam,presente_dt870_atualizacao,
                       nome_pt,pode_rodar,falta_o_que
                from clube_novo.impeto_jogo
                order by codigo_jogo
                """,
            )
            orphans = fetch_dicts(
                cursor,
                """
                select
                  count(*) filter(where i.codigo_jogo is null) orphan_impeto,
                  count(*) filter(where a.codigo is null) orphan_atributo,
                  count(*) - count(distinct (r.codigo_impeto,r.codigo_atributo)) duplicadas,
                  count(*) - count(distinct (r.codigo_impeto,r.ordem)) ordens_duplicadas
                from clube_novo.impeto_atributo_jogo r
                left join clube_novo.impeto_jogo i on i.codigo_jogo=r.codigo_impeto
                left join clube_novo.atributo_jogo a on a.codigo=r.codigo_atributo
                """,
            )[0]
            card_stats = fetch_dicts(
                cursor,
                """
                select count(*) cartas,
                       count(*) filter(where impeto_s1 is not null) slot1_preenchido,
                       count(*) filter(where impeto_s2_cond is not null) slot2_preenchido,
                       count(distinct impeto_s1) filter(where impeto_s1 is not null) slot1_codigos,
                       count(distinct impeto_s2_cond) filter(where impeto_s2_cond is not null) slot2_codigos
                from clube_novo.carta_jogo
                """,
            )[0]

    current_by_pair = {
        (int(row["codigo_impeto"]), row["codigo_atributo"]): row for row in relations
    }
    candidate_by_pair = {
        (row["codigo_impeto"], row["codigo_atributo"]): row for row in candidates
    }
    candidate_pairs = set(candidate_by_pair)
    current_pairs = set(current_by_pair)
    missing_in_db = sorted(candidate_pairs - current_pairs)
    extra_in_db = sorted(current_pairs - candidate_pairs)
    order_mismatches = [
        {
            "codigo_impeto": key[0],
            "codigo_atributo": key[1],
            "ordem_fisica": candidate_by_pair[key]["ordem"],
            "ordem_banco": current_by_pair[key]["ordem"],
        }
        for key in sorted(candidate_pairs & current_pairs)
        if candidate_by_pair[key]["ordem"] != current_by_pair[key]["ordem"]
    ]

    attribute_by_index = {int(row["idx_casa"]): row["codigo"] for row in attributes}
    legacy_by_pair = {
        (int(row["impeto_id"]), attribute_by_index.get(int(row["atributo_idx"]))): int(row["delta"])
        for row in legacy
        if attribute_by_index.get(int(row["atributo_idx"])) is not None
    }
    physical_legacy_mismatches = []
    for key, candidate in candidate_by_pair.items():
        legacy_delta = legacy_by_pair.get(key)
        if legacy_delta != candidate["delta_fisico"]:
            physical_legacy_mismatches.append(
                {
                    "codigo_impeto": key[0],
                    "codigo_atributo": key[1],
                    "delta_fisico": candidate["delta_fisico"],
                    "delta_legado": legacy_delta,
                }
            )

    catalog_by_code = {int(row["codigo_jogo"]): row for row in catalog}
    applicable = [row for row in candidates if row["aplicavel_agora"]]
    applicable_missing_source = [
        row["codigo_impeto"]
        for row in applicable
        if not catalog_by_code.get(row["codigo_impeto"], {}).get("presente_dt870_atualizacao")
        or catalog_by_code.get(row["codigo_impeto"], {}).get("registro_dt870_atualizacao") is None
    ]

    reason_counts = Counter(row["falta_o_que"] or "nenhuma" for row in candidates)
    sample_nesta = [
        {
            "codigo_impeto": row["codigo_impeto"],
            "codigo_atributo": row["codigo_atributo"],
            "delta": row["delta_fisico"],
            "bit_delta": row["bit_delta"],
            "registro": row["registro_origem"],
        }
        for row in candidates
        if row["codigo_impeto"] == 30
    ]

    preflight_ok = all(
        [
            read_only,
            len(candidates) == 1542,
            len(candidate_pairs) == 1542,
            not missing_in_db,
            not extra_in_db,
            not order_mismatches,
            not physical_legacy_mismatches,
            not applicable_missing_source,
            all(int(value) == 0 for value in orphans.values()),
            physical_manifest["catalog"]["mapped_checks_divergent"] == 0,
            physical_manifest["cards"]["counters"]["codigos_preenchidos_sem_catalogo"] == 0,
        ]
    )

    report = {
        "contract": "clube_novo-impeto-preflight-v1",
        "generated_at_database": "consultado na execução; sem escrita",
        "target_schema": "clube_novo",
        "legacy_schema_write": False,
        "transaction_read_only": read_only,
        "preflight_ok": preflight_ok,
        "schema": {"columns": columns, "constraints": constraints, "indexes": indexes},
        "counts": counts,
        "integrity": orphans,
        "cards_current_database": card_stats,
        "physical_contract": {
            "union_codes": physical_manifest["catalog"]["union_codes"],
            "mapped_checks_ok": physical_manifest["catalog"]["mapped_checks_ok"],
            "mapped_checks_divergent": physical_manifest["catalog"]["mapped_checks_divergent"],
            "valid_cards": physical_manifest["cards"]["counters"]["cartas_validas"],
            "assignments_above_255": physical_manifest["cards"]["counters"]["atribuicoes_acima_255"],
            "filled_codes_missing_catalog": physical_manifest["cards"]["counters"]["codigos_preenchidos_sem_catalogo"],
        },
        "relation_comparison": {
            "candidate_rows": len(candidates),
            "candidate_codes": len({row["codigo_impeto"] for row in candidates}),
            "database_rows": len(relations),
            "database_codes": len({int(row["codigo_impeto"]) for row in relations}),
            "candidate_fingerprint": fingerprint(candidates),
            "database_fingerprint": fingerprint(relations),
            "missing_in_database": missing_in_db,
            "extra_in_database": extra_in_db,
            "order_mismatches": order_mismatches,
        },
        "delta_crosscheck": {
            "legacy_rows": len(legacy),
            "physical_rows": len(candidates),
            "mismatches": physical_legacy_mismatches,
            "physical_delta_min": min(row["delta_fisico"] for row in candidates),
            "physical_delta_max": max(row["delta_fisico"] for row in candidates),
        },
        "partial_load": {
            "applicable_rows": len(applicable),
            "applicable_codes": len({row["codigo_impeto"] for row in applicable}),
            "blocked_rows": len(candidates) - len(applicable),
            "blocked_reason_counts": dict(sorted(reason_counts.items())),
            "applicable_missing_preferred_source": sorted(set(applicable_missing_source)),
        },
        "sample_nesta_duelo_mais_3": sample_nesta,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "preflight_ok": preflight_ok,
        "relation_rows": len(relations),
        "applicable_rows": len(applicable),
        "delta_mismatches": len(physical_legacy_mismatches),
        "pair_mismatches": len(missing_in_db) + len(extra_in_db),
        "order_mismatches": len(order_mismatches),
        "transaction_read_only": read_only,
        "report": str(output_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
