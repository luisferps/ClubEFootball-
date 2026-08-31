#!/usr/bin/env python3
"""Teste offline da conexão protegida. Nunca abre uma conexão real."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
EXECUTOR = ROOT / "executor"
sys.path.insert(0, str(EXECUTOR))
spec = importlib.util.spec_from_file_location("desktop_worker_secure_test", EXECUTOR / "desktop_worker.py")
assert spec and spec.loader
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class FakeCursor:
    def __init__(self) -> None:
        self.last = ""

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query: str) -> None:
        self.last = query.lower()

    def fetchone(self):
        return ("on",) if "transaction_read_only" in self.last else (1,)


class FakeConnection:
    def __init__(self) -> None:
        self.read_only = False
        self.rolled_back = False

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def cursor(self):
        return FakeCursor()

    def rollback(self) -> None:
        self.rolled_back = True


class FakePsycopg:
    def __init__(self, expected: str, failure: Exception | None = None) -> None:
        self.expected = expected
        self.failure = failure
        self.connection: FakeConnection | None = None

    def connect(self, dsn: str, connect_timeout: int):
        assert dsn == self.expected
        assert connect_timeout == 20
        if self.failure:
            raise self.failure
        self.connection = FakeConnection()
        return self.connection


def run() -> None:
    launcher = (ROOT / "windows-app" / "ClubEfootballExtractorLauncher.cs").read_text(encoding="utf-8")
    compiler = (ROOT / "windows-app" / "COMPILAR-APLICATIVO.ps1").read_text(encoding="utf-8")
    required_launcher_fragments = (
        'configureConnection.Text = "CONFIGURAR CONEXÃO"',
        'Text = "TESTAR E SALVAR"',
        "UseSystemPasswordChar = true",
        "ProtectedData.Protect(clear, CredentialEntropyV1, DataProtectionScope.CurrentUser)",
        "ProtectedData.Unprotect(encrypted, CredentialEntropyV1, DataProtectionScope.CurrentUser)",
        'CredentialEntropyV1 = Encoding.UTF8.GetBytes("ClubEfootball Extrator V5.2 database credential")',
        '"credencial-banco.windows-dpapi.json"',
        'info.EnvironmentVariables.Remove("SUPABASE_DB_PASSWORD")',
        'info.EnvironmentVariables["CLUBEF_SUPABASE_DB_URL"] = dsn',
        "File.Replace(temporary, path, null)",
        "FileAttributes.ReparsePoint",
        "--test-database-connection",
    )
    for fragment in required_launcher_fragments:
        assert fragment in launcher, fragment
    assert "/reference:System.Security.dll" in compiler
    assert "File.WriteAllText(CredentialPath, dsn" not in launcher

    secret = "postgresql://postgres.example:senha-super-secreta@aws-0.pooler.supabase.com:5432/postgres?sslmode=require"
    original_connection_string = worker.runtime.connection_string
    original_import_psycopg = worker.runtime.import_psycopg
    original_emit = worker.emit
    events: list[dict] = []
    try:
        with tempfile.TemporaryDirectory(prefix="clubef-db-test-") as temporary:
            run_dir = Path(temporary)
            fake = FakePsycopg(secret)
            worker.runtime.connection_string = lambda: secret
            worker.runtime.import_psycopg = lambda: (fake, None, None)
            worker.emit = lambda event_type, **payload: events.append({"type": event_type, **payload})
            code = worker.test_database_connection(SimpleNamespace(run_dir=str(run_dir)))
            assert code == 0
            assert fake.connection and fake.connection.read_only and fake.connection.rolled_back
            report_text = (run_dir / "teste-conexao-banco.json").read_text(encoding="utf-8")
            report = json.loads(report_text)
            assert report["state"] == "connected_read_only"
            assert report["transaction_read_only"] is True
            assert report["database_write"] is False
            assert secret not in report_text
            assert secret not in json.dumps(events, ensure_ascii=False)

        events.clear()
        with tempfile.TemporaryDirectory(prefix="clubef-db-failure-") as temporary:
            run_dir = Path(temporary)
            fake = FakePsycopg(secret, RuntimeError("password authentication failed for " + secret))
            worker.runtime.import_psycopg = lambda: (fake, None, None)
            code = worker.test_database_connection(SimpleNamespace(run_dir=str(run_dir)))
            assert code == 2
            persisted = (run_dir / "teste-conexao-banco.json").read_text(encoding="utf-8")
            assert "senha do banco foi recusada" in persisted.lower()
            assert secret not in persisted
            assert secret not in json.dumps(events, ensure_ascii=False)
    finally:
        worker.runtime.connection_string = original_connection_string
        worker.runtime.import_psycopg = original_import_psycopg
        worker.emit = original_emit

    print("OK: conexão segura usa DPAPI; teste é read-only; segredo não aparece em artefato ou evento")


if __name__ == "__main__":
    run()
