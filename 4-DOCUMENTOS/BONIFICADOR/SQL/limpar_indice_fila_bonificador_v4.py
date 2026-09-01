"""Remove o índice GIN provisório substituído pelo índice parcial V4."""
from __future__ import annotations

import os


def main() -> int:
    import psycopg
    with psycopg.connect(os.environ["BONIFICADOR_ADMIN_DATABASE_URL"], autocommit=True) as con:
        with con.cursor() as cur:
            cur.execute("drop index concurrently if exists clube_novo.build_linha_card_bonificador_pendente_gin")
    print("INDICE_PROVISORIO_REMOVIDO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
