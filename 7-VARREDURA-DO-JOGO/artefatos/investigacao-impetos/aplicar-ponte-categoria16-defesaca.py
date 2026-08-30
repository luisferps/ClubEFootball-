"""Aplica e prova a ponte categoria física 16 -> Any3W:65.

O script falha fechado, fotografa o antes, altera somente as duas colunas de
FK textual e realiza readback independente. Nenhum slot de carta é alterado.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
EXTRACTOR_ROOT = HERE.parents[1]
sys.path.insert(0, str(EXTRACTOR_ROOT / "executor" / "vendor"))

import psycopg  # noqa: E402


EVIDENCE_PATH = HERE / "prova-categoria-texto-impeto.json"
EVIDENCE_SHA256 = "9e5d83f5481b905af50d7dfe00ead9e06d9ad4bcf31e149fa5320bfa677174d9"
BEFORE_PATH = HERE / "snapshot-antes-ponte-categoria16-defesaca.json"
READBACK_PATH = HERE / "readback-ponte-categoria16-defesaca.json"
TARGET_CODES = [67, 73, 79, 85, 91, 118, 315, 360, 381, 411, 420, 455, 464, 490]
TEXT_KEY = ("Any3W", 65)
TEXT_VALUE = "Defesaça"
TEXT_CPK_SHA256 = "2419045a081a151f8a0cdcc70a9ca0c4ca1ca265b8467b9c182623baa05338db"
TEXT_FILE_SHA256 = "306741adab8376ed64620b618ae9721d316ae548b126419730b9bd5ff5f525a9"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def connect(*, read_only: bool = False) -> Any:
    password = os.environ.get("SUPABASE_DB_PASSWORD")
    if not password:
        raise RuntimeError("SUPABASE_DB_PASSWORD não está disponível")
    connection = psycopg.connect(
        host="db.trqqpsnafpbudtvvicch.supabase.co",
        dbname="postgres",
        user="postgres",
        password=password,
        sslmode="require",
    )
    connection.read_only = read_only
    return connection


def query_rows(cursor: Any) -> list[dict[str, Any]]:
    cursor.execute(
        "select codigo_jogo,nome_pt,secao_texto,id_texto,pode_rodar,falta_o_que "
        "from clube_novo.impeto_jogo where codigo_jogo=any(%s) order by codigo_jogo",
        (TARGET_CODES,),
    )
    names = [column.name for column in cursor.description]
    return [dict(zip(names, values, strict=True)) for values in cursor.fetchall()]


def slot_fingerprint(cursor: Any) -> dict[str, Any]:
    cursor.execute(
        "select count(*)::int,"
        "md5(string_agg(card_id||':'||slot::text||':'||codigo_impeto::text||':'||vaga::text,"
        "'|' order by card_id,slot)) from clube_novo.carta_impeto_jogo"
    )
    count, digest = cursor.fetchone()
    return {"rows": count, "md5": digest}


def text_row(cursor: Any) -> dict[str, Any]:
    cursor.execute(
        "select secao,id_texto,texto,arquivo,cpk,entrada_offset,texto_offset,"
        "fonte_cpk_sha256,fonte_arquivo_sha256 "
        "from clube_novo.texto_do_jogo where secao=%s and id_texto=%s",
        TEXT_KEY,
    )
    values = cursor.fetchone()
    if values is None:
        raise RuntimeError("texto Any3W:65 ausente")
    return dict(zip((column.name for column in cursor.description), values, strict=True))


def validate_evidence() -> dict[str, Any]:
    if sha256(EVIDENCE_PATH) != EVIDENCE_SHA256:
        raise RuntimeError("a prova física foi alterada depois da validação")
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    anchor = evidence.get("anchor_code_79") or {}
    if (
        anchor.get("codigo_jogo") != 79
        or anchor.get("categoria_raw_bit137_w5") != 16
        or anchor.get("secao_texto") != "Any3W"
        or anchor.get("id_texto") != 65
        or anchor.get("texto_fisico") != TEXT_VALUE
    ):
        raise RuntimeError("a âncora física de Vózinha/código 79 não confere")
    codes = sorted(
        int(item["codigo_jogo"])
        for item in evidence.get("mapped_records", [])
        if item.get("categoria_raw_bit137_w5") == 16
    )
    if codes != TARGET_CODES:
        raise RuntimeError(f"grupo físico 16 divergiu: {codes}")
    return evidence


def main() -> None:
    evidence = validate_evidence()
    connection = connect()
    try:
        with connection.cursor() as cursor:
            cursor.execute("set local lock_timeout='5s'")
            cursor.execute("set local statement_timeout='30s'")
            cursor.execute(
                "select codigo_jogo from clube_novo.impeto_jogo "
                "where codigo_jogo=any(%s) order by codigo_jogo for update",
                (TARGET_CODES,),
            )
            locked = [row[0] for row in cursor.fetchall()]
            if locked != TARGET_CODES:
                raise RuntimeError(f"grupo de destino incompleto: {locked}")
            before_rows = query_rows(cursor)
            if any(row["secao_texto"] is not None or row["id_texto"] is not None for row in before_rows):
                raise RuntimeError("há vínculo textual prévio; aplicação cancelada")
            before_text = text_row(cursor)
            if (
                before_text["texto"] != TEXT_VALUE
                or before_text["fonte_cpk_sha256"] != TEXT_CPK_SHA256
                or before_text["fonte_arquivo_sha256"] != TEXT_FILE_SHA256
            ):
                raise RuntimeError("texto físico/procedência não confere")
            slots_before = slot_fingerprint(cursor)
            snapshot = {
                "schema": "clubef-snapshot-ponte-categoria16-defesaca-v1",
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "evidence_sha256": EVIDENCE_SHA256,
                "target_codes": TARGET_CODES,
                "text": before_text,
                "impeto_jogo_before": before_rows,
                "carta_impeto_jogo_before": slots_before,
            }
            BEFORE_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            cursor.execute(
                "update clube_novo.impeto_jogo set secao_texto=%s,id_texto=%s "
                "where codigo_jogo=any(%s) and secao_texto is null and id_texto is null",
                (*TEXT_KEY, TARGET_CODES),
            )
            if cursor.rowcount != len(TARGET_CODES):
                raise RuntimeError(f"esperadas 14 atualizações; recebidas {cursor.rowcount}")
            after_rows = query_rows(cursor)
            if any((row["secao_texto"], row["id_texto"]) != TEXT_KEY for row in after_rows):
                raise RuntimeError("readback transacional divergiu")
            slots_after = slot_fingerprint(cursor)
            if slots_after != slots_before:
                raise RuntimeError("carta_impeto_jogo mudou; transação cancelada")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    verify = connect(read_only=True)
    try:
        with verify.cursor() as cursor:
            cursor.execute("show transaction_read_only")
            if cursor.fetchone()[0] != "on":
                raise RuntimeError("readback independente não ficou somente leitura")
            rows = query_rows(cursor)
            text = text_row(cursor)
            slots = slot_fingerprint(cursor)
            cursor.execute(
                "select i.codigo_jogo,t.texto,t.secao,t.id_texto "
                "from clube_novo.impeto_jogo i join clube_novo.texto_do_jogo t "
                "on (t.secao,t.id_texto)=(i.secao_texto,i.id_texto) "
                "where i.codigo_jogo=any(%s) order by i.codigo_jogo",
                (TARGET_CODES,),
            )
            joined = cursor.fetchall()
        verify.rollback()
    finally:
        verify.close()

    before = json.loads(BEFORE_PATH.read_text(encoding="utf-8"))
    if slots != before["carta_impeto_jogo_before"]:
        raise RuntimeError("slots divergiram no readback independente")
    if len(joined) != len(TARGET_CODES) or any(row[1:] != (TEXT_VALUE, *TEXT_KEY) for row in joined):
        raise RuntimeError("FK texto não resolveu no readback independente")
    readback = {
        "schema": "clubef-readback-ponte-categoria16-defesaca-v1",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "transaction_read_only": True,
        "evidence_sha256": EVIDENCE_SHA256,
        "updated_columns": ["clube_novo.impeto_jogo.secao_texto", "clube_novo.impeto_jogo.id_texto"],
        "rows": rows,
        "resolved_text": text,
        "resolved_join_count": len(joined),
        "resolved_join_sample": [list(row) for row in joined[:5]],
        "carta_impeto_jogo": slots,
        "carta_impeto_jogo_unchanged": True,
        "domain_tables_touched": ["clube_novo.impeto_jogo"],
        "untouched": ["clube_novo.carta_impeto_jogo", "jogo", "motor", "UI", "legado"],
        "unresolved_current_records": evidence["coverage"]["registros_sem_ponte_estrutural_suficiente"],
    }
    READBACK_PATH.write_text(json.dumps(readback, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "applied": True,
        "rows": len(rows),
        "text": f"{TEXT_KEY[0]}:{TEXT_KEY[1]}={TEXT_VALUE}",
        "code_79": next(row for row in rows if row["codigo_jogo"] == 79),
        "slots": slots,
        "snapshot": str(BEFORE_PATH),
        "readback": str(READBACK_PATH),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
