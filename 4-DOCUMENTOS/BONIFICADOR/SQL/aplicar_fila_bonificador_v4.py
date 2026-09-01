"""Aplicador local transacional da fila V4; exige BONIFICADOR_DB_URL no ambiente."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    url = os.environ.get("BONIFICADOR_DB_URL", "")
    if not url:
        print("ERRO: BONIFICADOR_DB_URL não foi definido.")
        return 2
    try:
        import psycopg
    except ImportError:
        print("ERRO: psycopg não está disponível no ambiente do aplicador.")
        return 2
    pasta = Path(__file__).resolve().parent
    sql = (pasta / "APLICAR-FILA-BONIFICADOR-V4.sql").read_text(encoding="utf-8")
    escritor = (pasta / "APLICAR-ESCRITOR-FILA-BONIFICADOR-V4.sql").read_text(encoding="utf-8")
    try:
        with psycopg.connect(url, connect_timeout=15) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql)
                cursor.execute(escritor)
        print("APLICADO|contratos_v4_criados")
        return 0
    except Exception as erro:
        print(f"FALHOU|{type(erro).__name__}|{erro}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
