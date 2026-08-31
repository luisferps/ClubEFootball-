"""Smoke offline do fluxo diário do Extrator Desktop.

Não abre fontes do jogo, não conecta ao banco e não executa aplicação.
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executor"))

import desktop_worker  # noqa: E402
import executor_local  # noqa: E402
import review_html  # noqa: E402


def contract() -> dict:
    return {
        "escritores_dominio": [
            {
                "familia": "cartas",
                "escritor_id": "extrator.envelope.cartas.teste",
                "destinos": [
                    {
                        "destino_id": 1,
                        "schema": "clube_novo",
                        "tabela": "carta_jogo",
                        "colunas_chave": ["card_id"],
                        "colunas_escrita": ["nome"],
                        "tipos_colunas": {"card_id": "text", "nome": "text"},
                        "exige_procedencia": True,
                        "ordem_lote": 100,
                    }
                ],
            }
        ]
    }


def result_with(classification: dict, structural: bool = True) -> dict:
    return {
        "comparison_reports": {"cartas:baseline": {"classification": classification}},
        "review_gate": {
            "structural_coverage_complete": structural,
            "families": {
                "cartas": {
                    "approved": structural,
                    "reasons": [] if structural else ["comparação incompleta"],
                }
            },
        },
    }


def main() -> None:
    safe_change = {
        "new": [],
        "removed": [],
        "altered": [
            {
                "classificacao": "alterado",
                "escopo": "cartas",
                "destino_tabela": "carta_jogo",
                "chave_canonica": {"card_id": "84"},
                "fonte_fisica": {"arquivo": "Player.bin", "registro": 0, "hash": "abc"},
                "campos_alterados": [
                    {
                        "destino": "clube_novo.carta_jogo.nome",
                        "fisico": "Yamamoto Hideomi",
                        "banco": "Nome anterior",
                        "proveniencia": "Player.bin: nome",
                    }
                ],
            }
        ],
        "repeated": [],
        "invalid": [],
        "known_pending": [],
        "historical_unresolved": [],
    }
    payload, status = desktop_worker.build_application_payload(contract(), result_with(safe_change))
    assert status["enabled"] is False
    assert status["state"] == "selection_required"
    assert status["selection_available"] is True
    assert status["selection_required"] is True
    assert status["envelope_count"] == 1
    base_review = {"application_status": status, "application_payload": payload}
    base_package = {"database_write": False, "pacote_revisao": base_review, "pacote_sha256": executor_local.sha256_json(base_review)}
    selection_id = status["selectable_items"][0]["selecao_id"]
    selected_package = desktop_worker.build_selected_review_package(base_package, [selection_id])
    selected_review = selected_package["pacote_revisao"]
    assert selected_review["application_status"]["enabled"] is True
    assert selected_review["application_status"]["state"] == "ready"
    assert selected_review["application_status"]["selected_count"] == 1
    assert selected_review["operator_selection"]["selected_ids"] == [selection_id]
    planned, audit = desktop_worker.validate_application_payload(contract(), selected_review["application_payload"])
    assert len(planned) == 1
    assert audit["familias"]["cartas"]["envelopes"] == 1
    envelope = planned[0][2]
    assert envelope["operacao"] == "upsert"
    assert envelope["identidade"] == {"card_id": "84"}
    assert envelope["valores"] == {"card_id": "84", "nome": "Yamamoto Hideomi"}
    assert envelope["procedencia"]

    two_changes = copy.deepcopy(safe_change)
    second_change = copy.deepcopy(two_changes["altered"][0])
    second_change["chave_canonica"] = {"card_id": "85"}
    second_change["campos_alterados"][0]["fisico"] = "Segundo Jogador"
    two_changes["altered"].append(second_change)
    two_payload, two_status = desktop_worker.build_application_payload(contract(), result_with(two_changes))
    assert two_status["envelope_count"] == 2
    chosen = next(item["selecao_id"] for item in two_status["selectable_items"] if item["identidade"] == {"card_id": "84"})
    two_review = {"application_status": two_status, "application_payload": two_payload}
    two_package = {"database_write": False, "pacote_revisao": two_review, "pacote_sha256": executor_local.sha256_json(two_review)}
    one_selected = desktop_worker.build_selected_review_package(two_package, [chosen])["pacote_revisao"]
    assert one_selected["application_status"]["selected_count"] == 1
    assert one_selected["application_status"]["excluded_by_operator_count"] == 1
    one_planned, _ = desktop_worker.validate_application_payload(contract(), one_selected["application_payload"])
    assert len(one_planned) == 1
    assert one_planned[0][2]["identidade"] == {"card_id": "84"}

    removed = copy.deepcopy(safe_change)
    removed["altered"] = []
    removed["removed"] = [{"chave_canonica": {"card_id": "84"}, "escopo": "cartas"}]
    _, removed_status = desktop_worker.build_application_payload(contract(), result_with(removed))
    assert removed_status["state"] == "no_changes"
    assert removed_status["selection_available"] is False
    assert removed_status["not_selectable_count"] == 1
    assert "remoção exige operação declarativa" in removed_status["not_selectable_items"][0]["motivo"]
    assert removed_status["blockers"] == []

    historical = copy.deepcopy(safe_change)
    historical["altered"] = []
    historical["historical_unresolved"] = [{"chave_canonica": {"codigo_impeto": 79}}]
    _, historical_status = desktop_worker.build_application_payload(contract(), result_with(historical))
    assert historical_status["state"] == "no_changes"
    assert historical_status["historical_warning_count"] == 1
    assert historical_status["unresolved_pending_count"] == 0
    assert historical_status["blockers"] == []

    known_pending = copy.deepcopy(safe_change)
    known_pending["altered"] = []
    known_pending["known_pending"] = [{"catalogo": "clube_novo.estilo_ia", "resolvida": False}]
    _, pending_status = desktop_worker.build_application_payload(contract(), result_with(known_pending))
    assert pending_status["state"] == "no_changes"
    assert pending_status["historical_warning_count"] == 0
    assert pending_status["unresolved_pending_count"] == 1
    assert pending_status["blockers"] == []

    mixed_result = result_with(safe_change)
    mixed_result["comparison_reports"]["catalogos:catalogos_normalizados"] = {
        "classification": {
            "new": [], "removed": [], "altered": [], "repeated": [], "invalid": [],
            "known_pending": [{"catalogo": "clube_novo.estilo_ia", "resolvida": False}],
            "historical_unresolved": [],
        }
    }
    mixed_result["review_gate"] = {
        "structural_coverage_complete": False,
        "application_blockers": [{"catalogo": "clube_novo.estilo_ia", "familias_impactadas": ["catalogos", "relacoes"]}],
        "families": {
            "cartas": {"approved": True, "reasons": []},
            "catalogos": {"approved": False, "reasons": ["cobertura física não verificável: clube_novo.estilo_ia"]},
            "relacoes": {"approved": False, "reasons": ["cobertura física não verificável: clube_novo.estilo_ia"]},
        },
    }
    _, mixed_status = desktop_worker.build_application_payload(contract(), mixed_result)
    assert mixed_status["state"] == "selection_required"
    assert mixed_status["selection_available"] is True
    assert mixed_status["report_observation_count"] == 1
    assert mixed_status["unresolved_pending_count"] == 1
    assert mixed_status["blockers"] == []

    catalog_contract = {
        "catalogos_fisicos": [{
            "schema": "clube_novo",
            "table": "estilo_ia",
            "aprovacao_aplicacao_habilitada": False,
            "familias_impactadas": ["catalogos", "relacoes"],
            "chave_resultado_leitura": "estilos_ia",
            "estado_cobertura": "coverage_nao_verificavel",
            "modo_validacao": "monitoramento",
            "motivo_cobertura": "catálogo físico integral ainda não localizado",
        }],
        "catalogos": [{"schema": "clube_novo", "table": "estilo_ia", "rows": []}],
    }
    monitored_metadata = {"catalogs": {"estilos_ia": {
        "supported": False,
        "status": "observado_nas_cartas_monitorado",
        "declared_coverage_state": "coverage_nao_verificavel",
        "coverage_complete": False,
        "application_eligible": False,
        "reason": "bits observados nas cartas; catálogo integral ainda não localizado",
    }}}
    catalog_result = desktop_worker.classify_catalogs(monitored_metadata, catalog_contract, {})
    assert catalog_result["technical_integrity"] is True
    assert catalog_result["exact_match"] is True
    assert catalog_result["unresolved_pending_count"] == 1
    assert catalog_result["classification"]["invalid"] == []
    assert catalog_result["classification"]["known_pending"][0]["resolvida"] is False
    assert catalog_result["application_eligible"] is False
    family_result = {"comparisons": {}, "families": {}, "contract_families": {}}
    desktop_worker.compare_family(
        "Catálogos",
        lambda: catalog_result,
        family_result,
        "catalogos",
        "catalogos_normalizados",
    )
    assert family_result["families"]["Catálogos"]["state"] == "review"
    assert review_html.TYPE_LABELS["known_pending"] == "Pendência já conhecida"
    pending_text = review_html._human_change_description({
        "type_key": "known_pending",
        "raw_entry": catalog_result["classification"]["known_pending"][0],
    })
    assert "não representa erro" in pending_text
    assert "ainda não resolvida" in pending_text

    with tempfile.TemporaryDirectory(prefix="clubef-review-offline-") as temp_dir:
        run_dir = Path(temp_dir)
        result_path = run_dir / "resultado.json"
        pending_entry = catalog_result["classification"]["known_pending"][0]
        historical_entry = {
            "classificacao": "histórico não comparável",
            "escopo": "impetos",
            "chave_canonica": {"codigo_impeto": 79},
            "motivo": "registro antigo ainda sem leitor completo",
            "procedencia_fisica": {"arquivo": "PlayerBooster.bin", "registro": 78, "registro_sha256": "abc"},
        }
        synthetic_result = {
            "contract_seal": {"contrato_id": "teste-offline"},
            "database_write": False,
            "physical_reader": "teste-offline",
            "families": {
                "Catálogos": {"state": "review", "database_write": False},
                "Ímpetos": {"state": "review", "database_write": False},
            },
            "artifacts": {},
            "state": "completed",
            "launcher_protocol_version": "teste",
            "comparisons": {
                "Catálogos": {"classification_complete": True, "technical_integrity": True, "exact_match": True},
                "Ímpetos": {"classification_complete": True, "technical_integrity": True, "exact_match": False},
            },
            "comparison_reports": {
                "catalogos:catalogos_normalizados": {"classification": {
                    "new": [], "removed": [], "altered": [], "repeated": [], "invalid": [],
                    "known_pending": [pending_entry], "historical_unresolved": [],
                }},
                "impetos:catalogo_normalizado": {"classification": {
                    "new": [], "removed": [], "altered": [], "repeated": [], "invalid": [],
                    "known_pending": [], "historical_unresolved": [historical_entry],
                }},
            },
            "review_gate": {
                "state": "coverage_blocked",
                "application_enabled": False,
                "families": {
                    "catalogos": {"approved": False, "reasons": ["cobertura física não verificável: clube_novo.estilo_ia"]},
                    "impetos": {"approved": True, "reasons": []},
                },
            },
            "application_status": {
                "state": "no_changes",
                "selection_available": False,
                "selectable_items": [],
                "not_selectable_count": 0,
                "blockers": [],
            },
        }
        result_path.write_text(json.dumps(synthetic_result, ensure_ascii=False, indent=2), encoding="utf-8")
        (run_dir / "radar-lancamentos.json").write_text(json.dumps({
            "meaning": "fixture local somente leitura",
            "counts": {
                "boxes": 0,
                "cards_mapped": 0,
                "records_ignored": 2,
                "ignored_by_classification": {
                    "card_without_box_name": 1,
                    "box_relation_card_absent_from_current_player": 1,
                },
                "by_state": {"nova": 0, "ja_conhecida": 0, "sem_historico": 0},
            },
            "comparison": {"status": "comparado", "reason": "fixture"},
            "integration_contract": {"status": "prepared_not_enabled"},
            "ignored_records": [
                {
                    "classification": "card_without_box_name",
                    "card_id": "105639015776029",
                    "record_index": 3168,
                    "record_sha256": "d72b757f46225a51ff97d8540c0048183654af2d0b4712180d6422f9e3402db5",
                },
                {
                    "classification": "box_relation_card_absent_from_current_player",
                    "card_id": "87961467093288",
                    "nome_box_fisico": "Yokohama FC 2017",
                    "record_index": 475,
                    "record_sha256": "11" * 32,
                },
            ],
            "boxes": [],
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        rendered = review_html.render_saved_result(result_path)
        html_path = Path(rendered["review_html_path"])
        manifest_path = Path(rendered["manifest_path"])
        html_text = html_path.read_text(encoding="utf-8")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        html_artifact = next(item for item in manifest["artifacts"] if item["name"] == "resultado.html")
        assert html_artifact["bytes"] == html_path.stat().st_size
        for required_text in (
            "Nenhuma mudança atual foi encontrada",
            "O que você deve fazer agora",
            "Esta varredura foi somente leitura",
            "O que significa",
            "Afeta os dados de hoje?",
            "Impede enviar alterações ao banco?",
            "O que você deve fazer",
            "Estilos de IA: a lista completa ainda não foi localizada",
            "O programa consegue ler os Estilos de IA usados em cada carta",
            "Não foi encontrada diferença nos estilos usados pelas cartas atuais",
            "Não bloqueia outras mudanças",
            "dados novos comprovados aparecem separadamente para você marcar",
            "Registros antigos de Ímpeto guardados como referência",
            "Eles não são tratados como mudança do jogo atual",
            "Nenhuma ação é necessária hoje",
            "Informações para suporte e auditoria (opcional)",
            "Detalhes técnicos",
            "Radar de boxes e possíveis lançamentos",
            "registro físico possui card, mas ainda não possui nome de box",
            "O Extrator não inventou um nome",
            "Eles não bloqueiam o envio de outras mudanças comprovadas",
            "ligação de box aponta para um card que não existe no jogo atual",
            "Referência física antiga, fora dos lançamentos atuais",
            "Quais cartas podem entrar nos motores",
            "Um espaço realmente conferido e vazio",
        ):
            assert required_text in html_text, required_text
        for rejected_visible_wording in (
            "Histórico não comparável",
            "Identidade canônica",
            "Leitura física concluída",
            "Informações técnicas para investigar",
            "0 divergências canônicas",
            "<th>Família</th>",
            "<th>Integridade técnica</th>",
        ):
            assert rejected_visible_wording not in html_text, rejected_visible_wording
        assert "codigo_impeto" in html_text
        assert "registro_sha256" in html_text
        assert "Nenhum dado novo ou alterado para enviar" in html_text
        assert "há itens disponíveis para selecionar nesta execução: <b>não</b>" in html_text
        assert "Envio ao banco bloqueado por pendência conhecida" not in html_text

    with tempfile.TemporaryDirectory() as temp_dir:
        stream_path = Path(temp_dir) / "cartas-grandes.json"
        expected_rows = [
            {"card_id": "1", "nome": "João", "valores": [1, 2, 3]},
            {"card_id": "2", "nome": "María", "aninhado": {"ok": True}},
        ]
        stream_path.write_text(json.dumps(expected_rows, ensure_ascii=False), encoding="utf-8")
        assert list(desktop_worker.iter_json_array_file(stream_path, chunk_size=7)) == expected_rows
        compact_path = Path(temp_dir) / "compacto.json"
        desktop_worker.write_compact_json(compact_path, {"cards": expected_rows})
        assert json.loads(compact_path.read_text(encoding="utf-8")) == {"cards": expected_rows}
        assert not compact_path.with_name(compact_path.name + ".novo").exists()

    _, coverage_status = desktop_worker.build_application_payload(contract(), result_with(safe_change, structural=False))
    assert coverage_status["state"] == "blocked"
    assert any(item["tipo"] == "coverage" for item in coverage_status["blockers"])

    launcher = (ROOT / "windows-app" / "ClubEfootballExtractorLauncher.cs").read_text(encoding="utf-8")
    assert 'EnvironmentVariables.Remove("CLUBEF_ENABLE_REAL_WRITE")' in launcher
    assert 'EnvironmentVariables["CLUBEF_ENABLE_REAL_WRITE"] = "1"' in launcher
    assert "File.AppendAllText(sessionLogPath" in launcher
    assert 'openLog.Text = "ABRIR LOG"' in launcher
    assert 'selectItems.Text = "ESCOLHER O QUE ENVIAR"' in launcher
    assert 'reviewMotors.Text = "REVISAR USO NOS MOTORES"' in launcher
    assert '"clubef-prontidao-motores-operador-v1"' in launcher
    assert "Esta tela nunca declara um card completo por decisão manual" in launcher
    assert 'list.Items.Add(choice, false)' in launcher
    assert '"pacote-selecionado.json"' in launcher
    assert '"clubef-selecao-operador-v1"' in launcher
    assert 'DesktopProtocolVersion = "5.3.0"' in launcher
    assert desktop_worker.DESKTOP_WORKER_PROTOCOL_VERSION == "5.3.0"
    opener = (ROOT / "ABRIR-EXTRATOR.cmd").read_text(encoding="utf-8")
    assert '"5.3.0"' in opener
    active_runtime = (ROOT / "app" / "contrato-v46-runtime.js").read_text(encoding="utf-8")
    assert "playstylesByBit" in active_runtime and "playstylesByIndex" in active_runtime
    assert "defensive_style_confirmed:secondaryId === 0 || playstylesByIndex.has(secondaryId)" in active_runtime
    assert executor_local.PRODUCTIVE_WRITES_LOCKED is True
    print("OK: fluxo autônomo offline, fail-closed, log persistente e aplicação separada")


if __name__ == "__main__":
    main()
