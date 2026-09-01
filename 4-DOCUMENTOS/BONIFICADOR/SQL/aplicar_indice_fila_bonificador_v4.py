"""Aplica somente o índice físico V4; exige BONIFICADOR_DB_URL no ambiente."""
from __future__ import annotations

import os
from pathlib import Path


def main() -> int:
    import psycopg
    try:
        with psycopg.connect(
            os.environ["BONIFICADOR_DB_URL"], connect_timeout=30, autocommit=True,
        ) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("set statement_timeout = 0")
                cursor.execute("set lock_timeout = 0")
                cursor.execute(
                    "drop index concurrently if exists "
                    "clube_novo.build_linha_card_bonificador_pronta_v4_idx"
                )
                cursor.execute((Path(__file__).parent / "APLICAR-INDICE-FILA-BONIFICADOR-V4.sql").read_text(encoding="utf-8"))
        print("INDICE_V4_APLICADO")
        return 0
    except Exception as erro:
        print(f"INDICE_V4_FALHOU|{type(erro).__name__}|{erro}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
