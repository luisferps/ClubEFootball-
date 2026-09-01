"""Cria o login local mínimo do Bonificador e registra somente sua URL no config."""
from __future__ import annotations

import os
import secrets
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit


FUNCOES = (
    "public.bonificador_regua_v2()",
    "public.bonificador_carta_v2(text)",
    "public.bonificador_contexto_fila_v4(integer,integer)",
    "public.gravar_build_bonificador_v4(jsonb)",
)


def atualizar_config(caminho: Path, url: str) -> None:
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    linhas = [x for x in linhas if not x.startswith("BONIFICADOR_DATABASE_URL=")]
    linhas.append(f"BONIFICADOR_DATABASE_URL={url}")
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main() -> int:
    import psycopg
    from psycopg import sql

    admin_url = os.environ["BONIFICADOR_ADMIN_DATABASE_URL"]
    config = Path(os.environ["BONIFICADOR_CONFIG_PATH"])
    senha = secrets.token_urlsafe(32)
    with psycopg.connect(admin_url, autocommit=True, options="-c statement_timeout=0") as con:
        with con.cursor() as cur:
            cur.execute("select 1 from pg_roles where rolname='bonificador_runtime'")
            if cur.fetchone():
                cur.execute(sql.SQL("alter role bonificador_runtime login password {}").format(sql.Literal(senha)))
            else:
                cur.execute(sql.SQL(
                    "create role bonificador_runtime login password {} nosuperuser nocreatedb nocreaterole noinherit noreplication"
                ).format(sql.Literal(senha)))
            cur.execute("grant connect on database postgres to bonificador_runtime")
            cur.execute("grant usage on schema public to bonificador_runtime")
            for funcao in FUNCOES:
                cur.execute(sql.SQL("grant execute on function {} to bonificador_runtime").format(sql.SQL(funcao)))

    partes = urlsplit(admin_url)
    usuario, _, sufixo = partes.username.partition(".")
    usuario_runtime = "bonificador_runtime" + ("." + sufixo if sufixo else "")
    host = partes.hostname or ""
    porta = f":{partes.port}" if partes.port else ""
    url_runtime = urlunsplit((partes.scheme, f"{usuario_runtime}:{quote(senha, safe='')}@{host}{porta}", partes.path, partes.query, ""))
    atualizar_config(config, url_runtime)
    print("ACESSO_LOCAL_CONFIGURADO|role=bonificador_runtime|funcoes=4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
