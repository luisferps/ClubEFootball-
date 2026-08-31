#!/usr/bin/env python3
"""Testes offline do instalador explícito; nunca abre banco ou fonte do jogo."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executor"))

import motor_protection_installer as installer  # noqa: E402
import desktop_worker as desktop_worker_module  # noqa: E402


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha_value(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def sha_file(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_package(base: Path, count: int = 2):
    root = base / "7-VARREDURA-DO-JOGO"
    run_dir = root / "artefatos" / "desktop" / "run-test"
    protection_dir = run_dir / "protecao-motores"
    (root / "executor").mkdir(parents=True)
    protection_dir.mkdir(parents=True)
    producer = root / "executor" / "motor_protection_seed.py"
    producer.write_text("# gerador sintético offline\n", encoding="utf-8")
    seal = {
        "contrato_id": "contrato-teste",
        "versao_jogo": "jogo-teste",
        "versao_contrato": "contrato-v1",
        "fingerprint_contrato_sha256": "1" * 64,
        "fingerprint_fontes_sha256": "2" * 64,
        "fingerprint_catalogos_sha256": "3" * 64,
    }
    source_payloads = {
        "resultado.json": {
            "state": "completed",
            "database_write": False,
            "application_status": {
                "state": "no_changes",
                "selection_available": False,
            },
        },
        "prontidao-motores.json": {"teste": "prontidao"},
        "cartas-fisicas-canonicas.json": [],
        "dimensoes-fisicas.json": {"cards": []},
        "metadados-fisicos.json": {"catalogs": {}},
    }
    sources = {}
    for name, payload in source_payloads.items():
        path = run_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        sources[name] = {"arquivo": str(path.resolve()), "sha256": sha_file(path)}

    seed_path = protection_dir / "seed-completude-motores.ndjson"
    with seed_path.open("wb") as stream:
        for number in range(1, count + 1):
            components = [
                {
                    "componente": name,
                    "estado_coleta": "conferido_com_valor",
                    "estado_resolucao": "resolvido",
                    "apto_motor": True,
                    "quantidade_valores": 1,
                    "proveniencia": {"arquivo": "fixture", "card_id": str(number)},
                    "evidencia": {},
                }
                for name in installer.REQUIRED_COMPONENTS
            ]
            envelope = {
                "schema": installer.ENVELOPE_SCHEMA,
                "regra_versao": installer.RULE_VERSION,
                "card_id": str(number),
                "input_fingerprint_local_sha256": "a" * 64,
                "componentes_fingerprint_sha256": sha_value(components),
                "aplicacao_id_binding": "aplicacao_id_criado_pelo_instalador_na_mesma_transacao_do_seed",
                "rpc": "clube_novo.registrar_completude_motor_v1(text,bigint,jsonb)",
                "database_write": False,
                "componentes": components,
            }
            stream.write((canonical(envelope) + "\n").encode("utf-8"))
    manifest = {
        "schema": installer.MANIFEST_SCHEMA,
        "versao": 1,
        "database_write": False,
        "publicacao_independente": True,
        "componentes_obrigatorios": list(installer.REQUIRED_COMPONENTS),
        "contract_seal": seal,
        "gerador": {"arquivo": str(producer.resolve()), "sha256": sha_file(producer)},
        "fontes": sources,
        "arquivos_fisicos_sha256": {},
        "seed": {
            "arquivo": str(seed_path.resolve()),
            "sha256": sha_file(seed_path),
            "bytes": seed_path.stat().st_size,
        },
        "contagens": {"envelopes": count, "componentes": count * 11},
        "aplicacao_id": {"valor_no_seed": None},
        "vinculo_instalador": {"idempotency_key_sha256": "b" * 64},
    }
    manifest["manifest_payload_sha256"] = sha_value(manifest)
    manifest_path = protection_dir / "manifest-seed-completude-motores.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    repo_root = root.parent
    for relative in (installer.COMPLETENESS_SQL, installer.BONUS_WRITER_SQL):
        path = repo_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("select 1;\n", encoding="utf-8")
    return root, run_dir, manifest_path, seal


class FakeConnection:
    def __init__(self, read_only: bool, fail_commit: bool = False):
        self.read_only = read_only
        self.fail_commit = fail_commit
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def commit(self):
        if self.fail_commit:
            raise OSError("resposta do COMMIT perdida")
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class FakeBackend:
    def __init__(self, fail_install: bool = False, mode: str = "initial_install", fail_commit: bool = False, recovery: str = "committed_candidate"):
        self.fail_install = fail_install
        self.mode = mode
        self.fail_commit = fail_commit
        self.recovery = recovery
        self.connections = []
        self.preview_calls = 0
        self.install_calls = 0
        self.readback_calls = 0

    def open(self, *, read_only: bool):
        should_fail_commit = self.fail_commit and not read_only and len(self.connections) == 1
        connection = FakeConnection(read_only, should_fail_commit)
        self.connections.append(connection)
        return connection

    def preview(self, connection, package, *, require_read_only: bool):
        assert connection.read_only is require_read_only
        self.preview_calls += 1
        changed = [] if self.mode == "already_up_to_date" else [str(index) for index in range(1, package.count + 1)]
        return {
            "transaction_read_only": require_read_only,
            "protection_state": "ausente",
            "operation_mode": self.mode,
            "database_card_count": package.count,
            "cards_to_register": len(changed),
            "changed_card_ids": changed,
            "changed_card_ids_sha256": sha_value(changed),
            "database_state_sha256": "d" * 64,
            "active_result_count": 7,
            "results_to_invalidate": 5,
            "results_preserved_as_identical_history": 2,
            "invalidated_ids_sha256": sha_value([11, 12, 13, 14, 15]),
            "invalidated_ids": [11, 12, 13, 14, 15],
            "preserved_ids": [16, 17],
            "unaffected_ids": [],
            "confirmation_sha256": "c" * 64,
        }

    def install(self, connection, package, preview, scripts):
        assert not connection.read_only
        if self.mode == "initial_install":
            assert set(scripts) == {"completude", "writer_bonificador"}
        else:
            assert scripts == {}
        self.install_calls += 1
        if self.fail_install:
            raise RuntimeError("falha sintética depois de iniciar a transação")
        return {
            "execution_id": 91,
            "application_id": 92,
            "operation_mode": self.mode,
            "cards_registered": preview["cards_to_register"],
            "database_cards": package.count,
            "components": package.count * 11,
            "results_invalidated": preview["results_to_invalidate"],
            "results_preserved_as_identical_history": preview["results_preserved_as_identical_history"],
            "seed_sha256": package.package_sha256,
            "scripts": {},
            "idempotency_key": "motor-protection-seed:" + "b" * 64,
        }

    def independent_readback(self, connection, package, installed, preview):
        assert connection.read_only
        self.readback_calls += 1
        return {
            "transaction_read_only": True,
            "new_connection": True,
            "application_id": installed["application_id"],
            "cards": package.count,
            "components": package.count * 11,
            "results_invalidated": preview["results_to_invalidate"],
            "package_sha256": package.package_sha256,
            "application_state": "aplicado",
            "bonus_writer_present": True,
        }

    def recover_commit_status(self, connection, installed):
        assert not connection.read_only
        return self.recovery


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="clubef-protecao-offline-") as temporary:
        root, run_dir, manifest, seal = make_package(Path(temporary))
        backend = FakeBackend()
        preview = installer.preview_motor_protection(
            root, run_dir, manifest, seal, "segredo-nao-deve-aparecer",
            backend=backend, expected_card_count=2,
        )
        assert preview["database_write"] is False
        assert preview["transaction_read_only"] is True
        assert preview["preview"]["results_to_invalidate"] == 5
        assert preview["confirmation_sha256"] == "c" * 64
        assert backend.preview_calls == 1 and backend.install_calls == 0
        assert len(backend.connections) == 1
        assert backend.connections[0].read_only and backend.connections[0].rolled_back

        blocked_backend = FakeBackend()
        try:
            installer.install_motor_protection(
                root, run_dir, manifest, seal, "segredo",
                confirmed_preview_sha256="c" * 64,
                operator_authorization_sha256="a" * 64,
                backend=blocked_backend, expected_card_count=2, write_enabled=False,
            )
            raise AssertionError("instalação sem ação explícita não foi bloqueada")
        except installer.MotorProtectionError as error:
            assert "botão" in str(error)
        assert blocked_backend.connections == []

        success_backend = FakeBackend()
        installed = installer.install_motor_protection(
            root, run_dir, manifest, seal, "segredo",
            confirmed_preview_sha256="c" * 64,
            operator_authorization_sha256="a" * 64,
            backend=success_backend, expected_card_count=2, write_enabled=True,
        )
        assert installed["state"] == "installed_or_updated_and_independently_verified"
        assert success_backend.preview_calls == 1
        assert success_backend.install_calls == 1
        assert success_backend.readback_calls == 1
        assert success_backend.connections[0].read_only and success_backend.connections[0].rolled_back
        assert success_backend.connections[1].committed and not success_backend.connections[1].rolled_back
        assert success_backend.connections[2].read_only and success_backend.connections[2].rolled_back

        failing_backend = FakeBackend(fail_install=True)
        try:
            installer.install_motor_protection(
                root, run_dir, manifest, seal, "segredo",
                confirmed_preview_sha256="c" * 64,
                operator_authorization_sha256="a" * 64,
                backend=failing_backend, expected_card_count=2, write_enabled=True,
            )
            raise AssertionError("falha sintética não interrompeu a instalação")
        except RuntimeError as error:
            assert "falha sintética" in str(error)
        assert failing_backend.install_calls == 1 and failing_backend.readback_calls == 0
        assert failing_backend.connections[1].rolled_back
        assert not failing_backend.connections[1].committed

        update_backend = FakeBackend(mode="incremental_update")
        updated = installer.install_motor_protection(
            root, run_dir, manifest, seal, "segredo",
            confirmed_preview_sha256="c" * 64,
            operator_authorization_sha256="a" * 64,
            backend=update_backend, expected_card_count=2, write_enabled=True,
        )
        assert updated["installed"]["operation_mode"] == "incremental_update"
        assert update_backend.install_calls == 1

        current_backend = FakeBackend(mode="already_up_to_date")
        current = installer.install_motor_protection(
            root, run_dir, manifest, seal, "segredo",
            confirmed_preview_sha256="c" * 64,
            operator_authorization_sha256="a" * 64,
            backend=current_backend, expected_card_count=2, write_enabled=True,
        )
        assert current["state"] == "already_up_to_date" and current["database_write"] is False
        assert current_backend.install_calls == 0 and len(current_backend.connections) == 1

        recovered_backend = FakeBackend(fail_commit=True, recovery="committed_candidate")
        recovered = installer.install_motor_protection(
            root, run_dir, manifest, seal, "segredo",
            confirmed_preview_sha256="c" * 64,
            operator_authorization_sha256="a" * 64,
            backend=recovered_backend, expected_card_count=2, write_enabled=True,
        )
        assert recovered["state"] == "committed_verified_after_uncertain_commit"
        assert recovered_backend.readback_calls == 1

        unknown_backend = FakeBackend(fail_commit=True, recovery="commit_status_unknown")
        try:
            installer.install_motor_protection(
                root, run_dir, manifest, seal, "segredo",
                confirmed_preview_sha256="c" * 64,
                operator_authorization_sha256="a" * 64,
                backend=unknown_backend, expected_card_count=2, write_enabled=True,
            )
            raise AssertionError("COMMIT incerto não bloqueou a repetição")
        except installer.MotorProtectionCommitStatusError as error:
            assert error.commit_status == "commit_status_unknown" and error.database_write is True
        uncertain = json.loads((run_dir / "instalacao-protecao-motores.json").read_text(encoding="utf-8"))
        assert uncertain["state"] == "commit_status_unknown" and uncertain["may_have_written"] is True

        no_report_backend = FakeBackend(fail_commit=True, recovery="commit_status_unknown")
        real_atomic_json = installer._atomic_json
        installer._atomic_json = lambda *args, **kwargs: (_ for _ in ()).throw(OSError("disco indisponível"))
        try:
            try:
                installer.install_motor_protection(
                    root, run_dir, manifest, seal, "segredo",
                    confirmed_preview_sha256="c" * 64,
                    operator_authorization_sha256="a" * 64,
                    backend=no_report_backend, expected_card_count=2, write_enabled=True,
                )
                raise AssertionError("COMMIT incerto perdeu o alerta quando o relatório local falhou")
            except installer.MotorProtectionCommitStatusError as error:
                assert error.commit_status == "commit_status_unknown" and error.database_write is True
        finally:
            installer._atomic_json = real_atomic_json

        authorization_path = run_dir / "autorizacao-protecao-motores-teste.json"
        issued = datetime.now(timezone.utc)
        authorization_path.write_text(json.dumps({
            "schema": "clubef-autorizacao-escrita-ui-v1",
            "action": "install_motor_protection",
            "protocol_version": desktop_worker_module.DESKTOP_WORKER_PROTOCOL_VERSION,
            "manifest_path": str(manifest.resolve()),
            "confirmation_sha256": "c" * 64,
            "launcher_pid": 1234,
            "launcher_executable": str((root / "Extrator eFootball.exe").resolve()),
            "issued_at": issued.isoformat(),
            "expires_at": (issued + timedelta(minutes=5)).isoformat(),
            "nonce": "d" * 64,
            "database_write_authorized": True,
        }), encoding="utf-8")
        real_ancestry_check = desktop_worker_module._windows_launcher_is_ancestor
        desktop_worker_module._windows_launcher_is_ancestor = lambda pid, executable: pid == 1234
        try:
            consumed = desktop_worker_module.consume_operator_write_authorization(
                root, run_dir, manifest, "c" * 64, str(authorization_path)
            )
        finally:
            desktop_worker_module._windows_launcher_is_ancestor = real_ancestry_check
        assert len(consumed["sha256"]) == 64
        assert Path(consumed["consumed_path"]).is_file() and not authorization_path.exists()

    launcher = (ROOT / "windows-app" / "ClubEfootballExtractorLauncher.cs").read_text(encoding="utf-8")
    worker = (ROOT / "executor" / "desktop_worker.py").read_text(encoding="utf-8")
    for fragment in (
        'installMotorProtection.Text = "INSTALAR/ATUALIZAR PROTEÇÃO DOS MOTORES"',
        'BuildWorkerCommand("--preview-motor-protection", motorProtectionManifestPath, false)',
        'BuildWorkerCommand("--install-motor-protection", motorProtectionManifestPath, true,',
        '"--confirmation-sha256 " + Quote(preview.ConfirmationSha256)',
        '" --operator-write-authorization " + Quote(authorizationPath)',
        "A instalação protege somente o Otimizador e o Bonificador",
        "Ela NÃO impede inserir, exibir ou publicar cartas",
        "Esta ação é separada de APLICAR PACOTE",
        "o aviso continua válido mesmo se o arquivo local de resultado não pôde ser gravado",
    ):
        assert fragment in launcher, fragment
    assert "613 resultado" not in launcher
    assert "43.072 cartas serão tratados" not in launcher
    assert 'parser.add_argument("--preview-motor-protection")' in worker
    assert 'parser.add_argument("--install-motor-protection")' in worker
    assert 'parser.add_argument("--confirmation-sha256")' in worker
    assert 'parser.add_argument("--operator-write-authorization")' in worker
    assert "consume_operator_write_authorization" in worker
    assert "application_status.get(\"state\") == \"no_changes\"" in worker
    assert "revalidate_saved_no_changes" in worker
    source = (ROOT / "executor" / "motor_protection_installer.py").read_text(encoding="utf-8")
    assert "current_user" in source and "pg_has_role" not in source
    assert "lock table {}.{} in share mode" in source
    assert "already_up_to_date" in source and "incremental_update" in source
    assert "commit_status_unknown" in source and "active_rows_snapshot" in source
    assert "readback anterior ao COMMIT" in source
    for unsafe_sql in (
        "commit /*comentario*/;",
        "select 1; rollback; select 2;",
        "start transaction;",
        "abort;",
        "end;",
    ):
        try:
            installer._assert_no_transaction_control(unsafe_sql, "sintetico.sql")
            raise AssertionError("controle transacional disfarçado não foi recusado")
        except installer.MotorProtectionError:
            pass
    installer._assert_no_transaction_control(
        "do $$ begin raise notice 'commit;'; end $$; select 'rollback;'::text;",
        "sintetico-valido.sql",
    )
    print("OK: instalar/atualizar, prévia vinculada, rollback, COMMIT incerto e readback integral comprovados offline")


if __name__ == "__main__":
    main()
