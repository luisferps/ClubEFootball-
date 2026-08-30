"""Smoke read-only do resolvedor código de Ímpeto -> texto oficial."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
EXTRACTOR_ROOT = HERE.parents[1]
sys.path.insert(0, str(EXTRACTOR_ROOT / "executor"))
sys.path.insert(0, str(EXTRACTOR_ROOT / "executor" / "vendor"))

import psycopg  # noqa: E402
from card_impetus import resolve_impetus_presentation_label  # noqa: E402


OUTPUT = HERE / "teste-resolvedor-ponte-categoria16-defesaca.json"


def rows(cursor: Any, query: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
    cursor.execute(query, params)
    names = [column.name for column in cursor.description]
    return [dict(zip(names, values, strict=True)) for values in cursor.fetchall()]


def main() -> None:
    connection = psycopg.connect(
        host="db.trqqpsnafpbudtvvicch.supabase.co",
        dbname="postgres",
        user="postgres",
        password=os.environ["SUPABASE_DB_PASSWORD"],
        sslmode="require",
    )
    connection.read_only = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("show transaction_read_only")
            if cursor.fetchone()[0] != "on":
                raise RuntimeError("smoke não ficou somente leitura")
            impulses = rows(
                cursor,
                "select codigo_jogo,secao_texto,id_texto,nome_pt from clube_novo.impeto_jogo "
                "where codigo_jogo in (38,49,79) order by codigo_jogo",
                (),
            )
            texts = rows(
                cursor,
                "select secao,id_texto,texto,origem,arquivo,cpk,entrada_offset,texto_offset,"
                "fonte_cpk_sha256,fonte_arquivo_sha256,presente_na_fonte "
                "from clube_novo.texto_do_jogo where secao='Any3W' and id_texto=65",
                (),
            )
            cursor.execute(
                "select count(*)::int,"
                "md5(string_agg(card_id||':'||slot::text||':'||codigo_impeto::text||':'||vaga::text,"
                "'|' order by card_id,slot)) from clube_novo.carta_impeto_jogo"
            )
            slot_rows, slot_md5 = cursor.fetchone()
        connection.rollback()
    finally:
        connection.close()

    contract = {
        "catalogos": [
            {"table": "impeto_jogo", "rows": impulses},
            {"table": "texto_do_jogo", "rows": texts},
        ]
    }
    result = {
        "schema": "clubef-smoke-resolvedor-rotulo-impeto-v1",
        "transaction_read_only": True,
        "database_write": False,
        "codigo_79": resolve_impetus_presentation_label(contract, 79),
        "controle_codigo_38": resolve_impetus_presentation_label(contract, 38),
        "controle_codigo_49": resolve_impetus_presentation_label(contract, 49),
        "carta_impeto_jogo": {"rows": slot_rows, "md5": slot_md5},
    }
    if result["codigo_79"]["rotulo"] != "Defesaça":
        raise RuntimeError("código 79 não resolveu para Defesaça")
    if result["codigo_79"]["rotulo_status"] != "rotulo_fisico_comprovado":
        raise RuntimeError("código 79 não recebeu status físico comprovado")
    if result["controle_codigo_38"]["rotulo"] is not None or result["controle_codigo_49"]["rotulo"] is not None:
        raise RuntimeError("variantes 38/49 receberam rótulo sem ponte aprovada")
    if (slot_rows, slot_md5) != (3748, "2b78ded34a46ab83e84570ba5578dd4f"):
        raise RuntimeError("slots de cartas divergiram")
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
