"""Confere o seed V1 materializado a partir do snapshot salvo, sem banco."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executor"))

import motor_protection_seed as seed  # noqa: E402


RUN = ROOT / "artefatos" / "desktop" / "run-20260830-132440"
OUTPUT = ROOT / "artefatos" / "preparacao-protecao-motores" / "run-20260830-132440-seed-v1"


def main() -> None:
    manifest_path = OUTPUT / "manifest-seed-completude-motores.json"
    seed_path = OUTPUT / "seed-completude-motores.ndjson"
    if not manifest_path.is_file() or not seed_path.is_file():
        raise AssertionError("seed do snapshot ainda não foi materializado pelo módulo offline")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema"] == seed.SCHEMA
    assert manifest["database_write"] is False
    assert manifest["contem_segredos"] is False
    assert manifest["execucao_local"]["run_dir"] == str(RUN.resolve())
    assert manifest["estado_materializacao_banco"] == "preparado_para_instalador_explicito_sem_application_id_previo"
    assert manifest["aplicacao_id"]["valor_no_seed"] is None
    assert manifest["vinculo_instalador"]["application_id_previo_proibido"] is True
    assert manifest["vinculo_instalador"]["pacote_sha256"] == manifest["seed"]["sha256"]
    assert manifest["contagens"]["envelopes"] == 43_072
    assert manifest["contagens"]["componentes"] == 43_072 * 11
    assert manifest["contagens"]["playstyles_defensivos_presentes"] == 4_166
    assert manifest["contagens"]["playstyles_defensivos_resolvidos"] == 4_166
    assert manifest["contagens"]["playstyles_defensivos_sem_resolucao"] == 0
    assert manifest["contagens"]["dimensoes_orfas_nao_bloqueantes"] == 354
    assert manifest["contagens"]["bloqueados_por_marcacao_manual"] == 0
    assert manifest["componentes_obrigatorios"] == list(seed.REQUIRED_COMPONENTS)

    digest = hashlib.sha256()
    rows = 0
    for line in seed_path.open("rb"):
        digest.update(line)
        envelope = json.loads(line)
        assert envelope["database_write"] is False
        assert envelope["aplicacao_id_binding"] == "aplicacao_id_criado_pelo_instalador_na_mesma_transacao_do_seed"
        assert [item["componente"] for item in envelope["componentes"]] == list(seed.REQUIRED_COMPONENTS)
        rows += 1
    assert rows == 43_072
    assert digest.hexdigest() == manifest["seed"]["sha256"]

    # Os cinco índices que originaram o falso aviso defensivo têm resolução
    # física conhecida e nunca podem voltar a ser tratados como tradução ausente.
    expected = {9: 329, 17: 337, 25: 345, 30: 350, 33: 353}
    metadata = json.loads((RUN / "metadados-fisicos.json").read_text(encoding="utf-8"))
    catalog = seed.card_completeness._build_playstyle_catalog(metadata["catalogs"]["playstyles"]["records"], None)
    assert {index: catalog[index]["id_jogo"] for index in expected} == expected

    print("OK: snapshot 43.072 envelopes, 11 componentes e zero falso playstyle defensivo")


if __name__ == "__main__":
    main()
