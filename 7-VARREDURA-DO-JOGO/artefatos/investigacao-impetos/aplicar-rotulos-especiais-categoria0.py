"""Aplica os 14 rótulos operacionais especiais de categoria 0 autorizados.

O script falha fechado se o nome pré-existente não corresponder ao rótulo
confirmado, se o código não estiver em um único slot 1 ou se qualquer coluna
fora de ``nome_pt``/``falta_o_que`` mudar. A ponte oficial de texto continua
deliberadamente nula e ``pode_rodar`` continua falso.
"""
from __future__ import annotations

import argparse
import csv
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


HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / "snapshot-antes-rotulos-especiais-categoria0-final.json"
READBACK = HERE / "readback-rotulos-especiais-categoria0-final.json"
ROLLBACK = HERE / "ROLLBACK-ROTULOS-ESPECIAIS-CATEGORIA0-FINAL.sql"

# Os oito rótulos de slot 1 foram confirmados individualmente pelo usuário.
# Nos seis registros de atributo único +6, o rótulo operacional é o nome do
# atributo físico comprovado. Nenhum deles cria secao_texto/id_texto.
CONFIRMED = {
    56: "Better of Fate",
    57: "Son of God",
    58: "King of Football",
    134: "The Undisputed",
    135: "Le Petit Prince",
    142: "Medical",
    143: "Striking",
    144: "Natural-Born",
    250: "Controle de bola",
    261: "Agressividade",
    263: "Velocidade",
    265: "Contato físico",
    266: "Equilíbrio",
    267: "Salto",
}
ALLOWED_CURRENT_LABELS = {
    56: ("Bearer of Fate", "Better of Fate"),
    57: ("Son of God",),
    58: ("King of Football",),
    134: ("The Undisputed",),
    135: ("Le Petit Prince",),
    142: ("Magical", "Medical"),
    143: ("Striking",),
    144: ("Natural-born", "Natural-Born"),
    250: ("Ball Control", "Controle de bola"),
    261: (None, "Agressividade"),
    263: ("Velocidade",),
    265: ("Physical Contact", "Contato físico"),
    266: (None, "Equilíbrio"),
    267: ("Salto",),
}
EXPECTED_SLOT = {
    56: 1, 57: 1, 58: 1, 134: 1, 135: 1, 142: 1, 143: 1, 144: 1,
    250: 2, 261: 2, 263: 2, 265: 2, 266: 2, 267: 2,
}
EXPECTED_CARD = {
    56: ("89129161334103", "Lionel Messi"),
    57: ("89129429769559", "Lionel Messi"),
    58: ("89129698205015", "Lionel Messi"),
    134: ("89133187865943", "Lionel Messi"),
    135: ("89132919465292", "Antoine Griezmann"),
    142: ("89133456301399", "Lionel Messi"),
    143: ("89134261635137", "Luis Suárez"),
    144: ("89133993205152", "Neymar Jr"),
    250: ("106785772021264", "Elliot Anderson"),
    261: ("106799999081317", "Maeda Daizen"),
    263: ("88045487392207", "Tijani Babangida"),
    265: ("88045487427597", "Diego Costa"),
    266: ("106799730668598", "Karim Adeyemi"),
    267: ("88045755964133", "Fabio Cannavaro"),
}
EXPECTED_EFFECT = {
    250: ("Ball Control", 6),
    261: ("Aggression", 6),
    263: ("Speed", 6),
    265: ("Physical Contact", 6),
    266: ("Balance", 6),
    267: ("Jumping", 6),
}
MARKERS = (
    "rotulo_operacional_confirmado_usuario",
    "especial_exclusivo_nao_replicavel",
    "ponte_fisica_texto_codigo_pendente",
)


def rows(cursor, query: str, params=()):
    cursor.execute(query, params)
    names = [column.name for column in cursor.description]
    return [dict(zip(names, values, strict=True)) for values in cursor.fetchall()]


def catalog_rows(cursor, codes: list[int]):
    return rows(
        cursor,
        "select codigo_jogo,nome_pt,nome_en,secao_texto,id_texto,falta_o_que,"
        "pode_rodar,condicional,condicao_estado,tipo_condicao_raw,arquivo_catalogo,"
        "registro_dt870_atualizacao,presente_dt870_atualizacao "
        "from clube_novo.impeto_jogo where codigo_jogo=any(%s) order by codigo_jogo",
        (codes,),
    )


def slot_fingerprint(cursor):
    cursor.execute(
        "select count(*),md5(coalesce(string_agg(concat_ws('|',card_id,slot,"
        "codigo_impeto,vaga,ordem,condicional),'#' order by card_id,slot),'')) "
        "from clube_novo.carta_impeto_jogo"
    )
    count, digest = cursor.fetchone()
    return {"rows": count, "md5": digest}


def effect_fingerprint(cursor):
    cursor.execute(
        "select count(*),md5(coalesce(string_agg(concat_ws('|',codigo_impeto,"
        "codigo_atributo,ordem,arquivo_origem,delta,bit_delta,largura_delta,"
        "registro_origem,fonte_origem,endereco_origem,status_validacao),'#' "
        "order by codigo_impeto,ordem,codigo_atributo),'')) "
        "from clube_novo.impeto_atributo_jogo"
    )
    count, digest = cursor.fetchone()
    return {"rows": count, "md5": digest}


def condition_fingerprint(cursor):
    cursor.execute(
        "select count(*),md5(coalesce(string_agg(concat_ws('|',codigo_impeto,"
        "criterio_codigo,campo_alvo,alvo_origem,tipo_raw,arquivo_origem,pacote_origem,"
        "hash_pacote,tamanho_registro,indice_registro,registro_sha256,bit_tipo,"
        "largura_tipo,bit_tipo_espelho,largura_tipo_espelho,texto_regra_secao,"
        "texto_regra_id,texto_regra_offset,avaliacao_minima,avaliacao_maxima,"
        "status_validacao,pode_rodar,falta_o_que,chave_texto_hex,rotina_condicao_va,"
        "transformacao_regra),'#' order by codigo_impeto,criterio_codigo,"
        "coalesce(indice_registro,-1)),'')) from clube_novo.impeto_condicao_jogo"
    )
    count, digest = cursor.fetchone()
    return {"rows": count, "md5": digest}


def protected_fingerprints(cursor):
    return {
        "carta_impeto_jogo": slot_fingerprint(cursor),
        "impeto_atributo_jogo": effect_fingerprint(cursor),
        "impeto_condicao_jogo": condition_fingerprint(cursor),
    }


def stable_json_sha(value) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def merge_markers(current: str | None) -> str:
    parts = [
        part.strip()
        for part in (current or "").split(";")
        if part.strip() and part.strip() != "nome_pt"
    ]
    for marker in MARKERS:
        if marker not in parts:
            parts.append(marker)
    return "; ".join(parts)


def sql_literal(value) -> str:
    if value is None:
        return "null"
    return "'" + str(value).replace("'", "''") + "'"


def write_rollback(before: list[dict]) -> None:
    statements = [
        "-- Rollback dos rótulos especiais categoria 0; gerado antes da transação.",
        "begin;",
    ]
    for item in before:
        statements.append(
            "update clube_novo.impeto_jogo set nome_pt="
            f"{sql_literal(item['nome_pt'])}, falta_o_que={sql_literal(item['falta_o_que'])} "
            f"where codigo_jogo={int(item['codigo_jogo'])};"
        )
    statements.extend(["commit;", ""])
    ROLLBACK.write_text("\n".join(statements), encoding="utf-8")


def assert_preconditions(cursor, before: list[dict]) -> None:
    by_code = {int(item["codigo_jogo"]): item for item in before}
    if set(by_code) != set(CONFIRMED):
        raise RuntimeError("readback não retornou exatamente os 14 pares confirmados")
    for code, label in CONFIRMED.items():
        item = by_code[code]
        allowed = ALLOWED_CURRENT_LABELS[code]
        if item["nome_pt"] is None:
            valid_label = None in allowed
        else:
            valid_label = any(
                isinstance(value, str) and item["nome_pt"].casefold() == value.casefold()
                for value in allowed
            )
        if not valid_label:
            raise RuntimeError(f"código {code}: rótulo pré-existente fora da lista fail-closed {allowed!r}")
        if item["secao_texto"] is not None or item["id_texto"] is not None:
            raise RuntimeError(f"código {code}: ponte textual deixou de estar pendente")
        if item["pode_rodar"] is not False:
            raise RuntimeError(f"código {code}: pode_rodar deveria permanecer falso")
    usage = rows(
        cursor,
        "select codigo_impeto,count(*) as usos,min(slot) as slot_min,max(slot) as slot_max,"
        "min(card_id) as card_id "
        "from clube_novo.carta_impeto_jogo where codigo_impeto=any(%s) and not vaga "
        "group by codigo_impeto order by codigo_impeto",
        (list(CONFIRMED),),
    )
    if len(usage) != len(CONFIRMED):
        raise RuntimeError("nem todos os 14 códigos têm uso individual comprovado")
    for item in usage:
        code = int(item["codigo_impeto"])
        expected_slot = EXPECTED_SLOT[code]
        if item["usos"] != 1 or item["slot_min"] != expected_slot or item["slot_max"] != expected_slot:
            raise RuntimeError(f"uso inesperado para código {item['codigo_impeto']}: {item}")
        if code in EXPECTED_CARD and str(item["card_id"]) != EXPECTED_CARD[code][0]:
            raise RuntimeError(f"card_id inesperado para código {code}: {item['card_id']}")
    physical_names: dict[str, str] = {}
    physical_csv = ROOT / "artefatos" / "desktop" / "run-20260830-005609" / "cartas-fisicas.csv"
    with physical_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("card_id") in {value[0] for value in EXPECTED_CARD.values()}:
                physical_names[row["card_id"]] = row.get("nome") or ""
    for code, (card_id, player_name) in EXPECTED_CARD.items():
        if physical_names.get(card_id) != player_name:
            raise RuntimeError(f"nome físico inesperado para código {code}: {physical_names.get(card_id)!r}")
    effects = rows(
        cursor,
        "select e.codigo_impeto,a.nome_en,e.delta,e.arquivo_origem,e.registro_origem,e.status_validacao "
        "from clube_novo.impeto_atributo_jogo e left join clube_novo.atributo_jogo a "
        "on a.codigo=e.codigo_atributo where e.codigo_impeto=any(%s) order by e.codigo_impeto,e.ordem",
        (list(EXPECTED_EFFECT),),
    )
    if len(effects) != len(EXPECTED_EFFECT):
        raise RuntimeError("efeitos +6 não retornaram exatamente uma linha por código")
    for effect in effects:
        code = int(effect["codigo_impeto"])
        if (effect["nome_en"], effect["delta"]) != EXPECTED_EFFECT[code]:
            raise RuntimeError(f"efeito físico inesperado para código {code}: {effect}")


def apply(dry_run: bool) -> dict:
    psycopg, _, _ = ex.import_psycopg()
    dsn = ex.connection_string()
    if not dsn:
        raise RuntimeError("conexão segura com clube_novo indisponível")
    codes = sorted(CONFIRMED)
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        with connection.cursor() as cursor:
            before = catalog_rows(cursor, codes)
            assert_preconditions(cursor, before)
            protected_before = protected_fingerprints(cursor)
            snapshot = {
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "mode": "dry_run" if dry_run else "apply",
                "confirmed_before": before,
                "all_fourteen_before": before,
                "protected_tables": protected_before,
            }
            SNAPSHOT.write_text(
                json.dumps(snapshot, ensure_ascii=False, indent=2, default=str) + "\n",
                encoding="utf-8",
            )
            write_rollback(before)
            for code, label in CONFIRMED.items():
                current = next(x for x in before if x["codigo_jogo"] == code)
                cursor.execute(
                    "update clube_novo.impeto_jogo set nome_pt=%s,falta_o_que=%s "
                    "where codigo_jogo=%s and nome_pt is not distinct from %s "
                    "and secao_texto is null and id_texto is null and not pode_rodar",
                    (label, merge_markers(current["falta_o_que"]), code, current["nome_pt"]),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError(f"código {code}: update fail-closed não afetou exatamente uma linha")
            after = catalog_rows(cursor, codes)
            protected_after = protected_fingerprints(cursor)
            if protected_after != protected_before:
                raise RuntimeError("slots, efeitos ou condições mudaram; transação cancelada")
            immutable = {
                "nome_en", "secao_texto", "id_texto", "pode_rodar", "condicional",
                "condicao_estado", "tipo_condicao_raw", "arquivo_catalogo",
                "registro_dt870_atualizacao", "presente_dt870_atualizacao",
            }
            by_before = {x["codigo_jogo"]: x for x in before}
            for item in after:
                old = by_before[item["codigo_jogo"]]
                if any(item[key] != old[key] for key in immutable):
                    raise RuntimeError(f"código {item['codigo_jogo']}: coluna imutável mudou")
                if not all(marker in (item["falta_o_que"] or "") for marker in MARKERS):
                    raise RuntimeError(f"código {item['codigo_jogo']}: proveniência operacional incompleta")
            result = {
                "dry_run": dry_run,
                "updated": after,
                "physical_text_bridge": "pendente",
                "unreleased_reference": {"codigo_impeto": 261, "card_id": EXPECTED_CARD[261][0], "nome": "Maeda Daizen"},
                "protected_tables_unchanged": True,
                "protected_fingerprints": protected_after,
                "before_sha256": stable_json_sha(before),
                "after_sha256": stable_json_sha(after),
            }
            if dry_run:
                connection.rollback()
            else:
                connection.commit()
            return result


def independent_readback(expected: dict) -> dict:
    psycopg, _, _ = ex.import_psycopg()
    dsn = ex.connection_string()
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        with connection.cursor() as cursor:
            cursor.execute("set transaction read only")
            confirmed = catalog_rows(cursor, sorted(CONFIRMED))
            protected = protected_fingerprints(cursor)
    if confirmed != expected["updated"] or protected != expected["protected_fingerprints"]:
        raise RuntimeError("readback independente não coincide com a transação")
    result = {
        "read_at": datetime.now(timezone.utc).isoformat(),
        "updated_columns": ["clube_novo.impeto_jogo.nome_pt", "clube_novo.impeto_jogo.falta_o_que"],
        "confirmed": confirmed,
        "physical_text_bridge": "pendente",
        "protected_tables": protected,
        "domain_tables_touched": ["clube_novo.impeto_jogo"],
        "untouched": [
            "clube_novo.carta_impeto_jogo", "clube_novo.impeto_atributo_jogo",
            "clube_novo.impeto_condicao_jogo", "jogo", "legado",
        ],
    }
    READBACK.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="confirma a transação real")
    args = parser.parse_args()
    result = apply(dry_run=not args.apply)
    if args.apply:
        result["independent_readback"] = independent_readback(result)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
