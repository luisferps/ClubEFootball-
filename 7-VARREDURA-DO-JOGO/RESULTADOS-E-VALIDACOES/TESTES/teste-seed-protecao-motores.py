"""Testes offline da ponte entre a leitura física e o contrato SQL."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executor"))

import card_completeness as readiness  # noqa: E402
import motor_protection_seed as seed  # noqa: E402


def _card(card_id: str, *, defensive: int = 0) -> dict:
    return {
        "card_id": card_id,
        "name": f"Carta {card_id}",
        "height": 180,
        "weight": 75,
        "age": 25,
        "position": "CMF",
        "primary_style_id": 8,
        "primary_style_unknown": False,
        "defensive_style_id": defensive,
        "defensive_style_confirmed": True,
        "weak_foot_usage": 2,
        "weak_foot_accuracy": 2,
        "foot": "Direito",
        "form": 2,
        "injury": "Baixa",
        "attrs": [70] * 26,
        "corpo": [180] + [7] * 11,
        "aptitudes": {name: 0 for name in ("AMF", "CB", "CF", "CMF", "DMF", "LB", "LMF", "LWF", "RB", "RMF", "RWF", "SS")},
        "skills": [],
        "habilidades_fisicas": [],
        "ai_styles": [],
        "estilos_ia_fisicos": [],
        "booster_primary": {"state": "sem"},
        "booster_conditional": {"state": "vaga"},
        "tipo": "colecionavel",
        "roda_motor": True,
    }


def _dimension(card_id: str, *, orphan: bool = False) -> dict:
    return {
        "card_id": card_id,
        "registro_vinculos_jogo": int(card_id),
        "codigo_nacionalidade": 13,
        "codigo_clube": 999 if orphan else 10,
        "codigo_liga": None if orphan else 20,
        "tipo_carta_id": "player_type_6_subtype_1",
        "pode_rodar_vinculos": not orphan,
        "falta_o_que_vinculos": "codigo_clube sem definicao em Team.bin: 999" if orphan else None,
    }


def _metadata() -> dict:
    return {"contract": "teste", "catalogs": {
        "impetos": {"records": [{
            "id": "42",
            "tipo_condicao_status": "coletado",
            "criterio_codigo": "sempre_ativo",
            "efeitos": [{"codigo_atributo": "PB:434:6", "delta": 4}],
        }]},
        "playstyles": {"records": [
            {"id": "256", "record_index": 0, "record_sha256": "ps0", "source_file_sha256": "ps-file", "source_role": "dt870_updated"},
            {"id": "350", "record_index": 30, "record_sha256": "ps30", "source_file_sha256": "ps-file", "source_role": "dt870_updated"},
        ]},
    }}


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def _fixture(run_dir: Path) -> None:
    cards = [_card("100", defensive=30), _card("101")]
    dimensions = [_dimension("100"), _dimension("101", orphan=True)]
    metadata = _metadata()
    contract = {
        "contrato_id": "offline-test",
        "versao_jogo": "fixture",
        "versao_contrato": "fixture-v1",
        "fingerprint_contrato_sha256": "a" * 64,
        "fingerprint_fontes_sha256": "b" * 64,
        "fingerprint_catalogos_sha256": "c" * 64,
    }
    source = {"family_fingerprints": {"cartas": "cartas-fp", "dimensoes": "dim-fp", "catalogos": "cat-fp"}}
    overrides = {
        "schema": readiness.OVERRIDE_SCHEMA,
        "cards": [{
            "card_id": "101",
            "estado": "incompleto_confirmado",
            "motivo": "insumo visual ainda parcial",
            "componentes": ["impetos"],
            "marcado_em": "2026-08-31T12:00:00+00:00",
        }],
    }
    ready = readiness.build_artifact(
        cards,
        {"cards": dimensions},
        metadata,
        contract_seal=contract,
        source_seal=source,
        operator_overrides=overrides,
        generated_at="2026-08-31T12:00:00+00:00",
    )
    dimensions_artifact = {
        "contract": "fixture-dimensions",
        "database_write": False,
        "source_files": {"dt870_updated:Player.bin": "player-fixture", "dt870_updated:Team.bin": "team-fixture"},
        "cards": dimensions,
    }
    result = {
        "state": "completed",
        "database_write": False,
        "physical_reader": "fixture-reader",
        "launcher_protocol_version": "test",
        "contract_seal": contract,
        "family_seals": {
            "cartas": {"fingerprint_familia": "cartas-fp"},
            "dimensoes": {"fingerprint_familia": "dim-fp"},
            "catalogos": {"fingerprint_familia": "cat-fp"},
        },
    }
    _write(run_dir / "cartas-fisicas-canonicas.json", cards)
    _write(run_dir / "dimensoes-fisicas.json", dimensions_artifact)
    _write(run_dir / "metadados-fisicos.json", metadata)
    _write(run_dir / "prontidao-motores.json", ready)
    _write(run_dir / "resultado.json", result)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="clubef-seed-test-") as folder:
        root = Path(folder)
        run_dir = root / "run"
        output_dir = root / "output"
        run_dir.mkdir()
        _fixture(run_dir)
        manifest = seed.build_seed(run_dir, output_dir, generated_at="2026-08-31T13:00:00+00:00")

        assert manifest["database_write"] is False
        assert manifest["contem_segredos"] is False
        assert manifest["estado_materializacao_banco"] == "preparado_para_instalador_explicito_sem_application_id_previo"
        assert manifest["aplicacao_id"]["valor_no_seed"] is None
        assert manifest["vinculo_instalador"]["application_id_previo_proibido"] is True
        assert manifest["vinculo_instalador"]["pacote_sha256"] == manifest["seed"]["sha256"]
        assert manifest["contagens"]["envelopes"] == 2
        assert manifest["contagens"]["componentes"] == 22
        assert manifest["contagens"]["playstyles_defensivos_presentes"] == 1
        assert manifest["contagens"]["playstyles_defensivos_resolvidos"] == 1
        assert manifest["contagens"]["playstyles_defensivos_sem_resolucao"] == 0
        assert manifest["contagens"]["dimensoes_orfas_nao_bloqueantes"] == 1
        assert manifest["contagens"]["bloqueados_por_marcacao_manual"] == 1

        seed_path = Path(manifest["seed"]["arquivo"])
        assert hashlib.sha256(seed_path.read_bytes()).hexdigest() == manifest["seed"]["sha256"]
        rows = [json.loads(line) for line in seed_path.read_text(encoding="utf-8").splitlines()]
        assert all([item["componente"] for item in row["componentes"]] == list(seed.REQUIRED_COMPONENTS) for row in rows)
        first = rows[0]
        assert next(item for item in first["componentes"] if item["componente"] == "habilidades")["estado_coleta"] == "conferido_sem_valor"
        playstyles = next(item for item in first["componentes"] if item["componente"] == "playstyles")
        assert playstyles["evidencia"]["resolucao_estilo_defensivo"]["id_jogo"] == 350
        second = rows[1]
        dimensions = next(item for item in second["componentes"] if item["componente"] == "dimensoes")
        assert dimensions["estado_resolucao"] == "orfao_catalogo_atual"
        assert dimensions["apto_motor"] is True
        impetus = next(item for item in second["componentes"] if item["componente"] == "impetos")
        assert impetus["estado_coleta"] == "conferido_sem_valor"
        assert impetus["apto_motor"] is False
        assert impetus["evidencia"]["decisao_motor"]["tipo"] == "incompleto_confirmado_operador"

        # A ausência de prova física não pode ser convertida em vazio completo.
        bad = json.loads((run_dir / "cartas-fisicas-canonicas.json").read_text(encoding="utf-8"))
        bad[0].pop("habilidades_fisicas")
        _write(run_dir / "cartas-fisicas-canonicas.json", bad)
        try:
            seed.build_seed(run_dir, root / "bad-output")
        except seed.SeedError as exc:
            assert "não corresponde aos insumos físicos" in str(exc)
        else:
            raise AssertionError("seed aceitou alteração física não refletida na prontidão")

    print("OK: seed offline com 11 componentes, ausência confirmada e bloqueio manual")


if __name__ == "__main__":
    main()
