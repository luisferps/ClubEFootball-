"""Testes offline da distinção entre ausência confirmada e dado não coletado."""
from __future__ import annotations

import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executor"))

import card_completeness as readiness  # noqa: E402


def card(card_id: str = "100") -> dict:
    return {
        "card_id": card_id,
        "name": "Carta Teste",
        "height": 180,
        "weight": 75,
        "age": 25,
        "position": "CMF",
        "weak_foot_usage": 2,
        "weak_foot_accuracy": 2,
        "foot": "Direito",
        "form": 2,
        "injury": "Baixa",
        "primary_style_id": 8,
        "primary_style_unknown": False,
        "defensive_style_id": 0,
        "defensive_style_confirmed": True,
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


def dimension(card_id: str = "100") -> dict:
    return {
        "card_id": card_id,
        "codigo_nacionalidade": 13,
        "codigo_clube": None,
        "codigo_liga": None,
        "tipo_carta_id": "player_type_6_subtype_1",
        "pode_rodar_vinculos": True,
        "falta_o_que_vinculos": None,
    }


def metadata() -> dict:
    return {"catalogs": {
        "impetos": {"records": [{
            "id": "42",
            "tipo_condicao_status": "coletado",
            "criterio_codigo": "sempre_ativo",
            "efeitos": [{"codigo_atributo": "PB:434:6", "delta": 4}],
        }]},
        "playstyles": {"records": [
            {
                "id": "256",
                "record_index": 0,
                "record_sha256": "playstyle-0",
                "source_file_sha256": "playstyle-file",
                "source_role": "dt870_updated",
            },
            {
                "id": "350",
                "record_index": 30,
                "record_sha256": "playstyle-30",
                "source_file_sha256": "playstyle-file",
                "source_role": "dt870_updated",
            },
        ]},
    }}


def artifact(
    cards: list[dict],
    dimensions: list[dict],
    overrides=None,
    *,
    metadata_value: dict | None = None,
    playstyle_catalog=None,
) -> dict:
    return readiness.build_artifact(
        cards,
        {"cards": dimensions},
        metadata() if metadata_value is None else metadata_value,
        contract_seal={"contrato_id": "offline"},
        source_seal={"fingerprint_familia": "abc"},
        playstyle_catalog=playstyle_catalog,
        operator_overrides=overrides,
        generated_at="2026-08-31T12:00:00+00:00",
    )


def main() -> None:
    # Lista vazia e slot sem/vaga foram fisicamente lidos: são respostas, não faltas.
    complete = artifact([card()], [dimension()])
    row = complete["cards"][0]
    assert row["coleta_completa"] is True
    assert row["motor_eligible"] is True
    assert row["componentes"]["habilidades"]["estado"] == "conferido_sem_valor"
    assert row["componentes"]["estilos_ia"]["estado"] == "conferido_sem_valor"
    assert row["componentes"]["impetos"]["estado"] == "conferido_sem_valor"
    assert row["publicacao_bloqueada_por_este_gate"] is False

    # Campo ausente é desconhecido: não pode ser transformado em lista vazia.
    unread = card("101")
    unread.pop("habilidades_fisicas")
    unread_result = artifact([unread], [dimension("101")])["cards"][0]
    assert unread_result["motor_eligible"] is False
    assert unread_result["estado"] == "aguardando_insumos"
    assert unread_result["componentes"]["habilidades"]["estado"] == "nao_conferido"
    assert any(item["componente"] == "habilidades" for item in unread_result["faltando"])
    assert unread_result["faltando_coleta"] == unread_result["faltando"]

    # Ímpeto preenchido só fica apto quando código, condição e efeitos estão presentes.
    boosted = card("102")
    boosted["booster_primary"] = {"state": "preench", "id": 42}
    boosted_result = artifact([boosted], [dimension("102")])["cards"][0]
    assert boosted_result["componentes"]["impetos"]["estado"] == "conferido_com_valor"
    assert boosted_result["motor_eligible"] is True
    unknown_booster = copy.deepcopy(boosted)
    unknown_booster["card_id"] = "103"
    unknown_booster["booster_primary"] = {"state": "preench", "id": 999}
    unknown_result = artifact([unknown_booster], [dimension("103")])["cards"][0]
    assert unknown_result["motor_eligible"] is False
    assert "não resolvido" in unknown_result["componentes"]["impetos"]["motivo"]

    # Zero é ausência confirmada. O slot defensivo usa o índice do catálogo;
    # o indicador derivado antigo não pode criar um falso aviso.
    no_defensive = artifact([card("104")], [dimension("104")])["cards"][0]
    assert no_defensive["componentes"]["estilos_de_jogo"]["completo"] is True
    unknown_style = card("105")
    unknown_style["defensive_style_id"] = 30
    unknown_style["defensive_style_confirmed"] = False
    style_artifact = artifact([unknown_style], [dimension("105")])
    style_result = style_artifact["cards"][0]
    assert style_result["motor_eligible"] is True
    assert style_result["coleta_completa"] is True
    assert style_result["componentes"]["estilos_de_jogo"]["estado"] == "conferido_com_valor"
    assert not any(item["componente"] == "estilos_de_jogo" for item in style_result["faltando"])
    assert style_result["pendencias_conhecidas"] == []
    assert style_result["componentes"]["estilos_de_jogo"]["prova_indice_defensivo"]["indice"] == 30
    assert style_result["componentes"]["estilos_de_jogo"]["prova_indice_defensivo"]["id_jogo"] == 350
    assert style_artifact["summary"]["pendencias_conhecidas_total"] == 0
    assert style_artifact["summary"]["cartas_com_pendencia_conhecida"] == 0
    assert style_artifact["summary"]["pendencias_conhecidas_por_tipo"] == {}

    unlabelled_style = copy.deepcopy(unknown_style)
    unlabelled_style["card_id"] = "1051"
    unlabelled_style.pop("defensive_style_confirmed")
    unlabelled_result = artifact([unlabelled_style], [dimension("1051")])["cards"][0]
    assert unlabelled_result["motor_eligible"] is True
    assert unlabelled_result["pendencias_conhecidas"] == []

    # O mesmo catálogo pode vir do contrato integral/isolado. Só um índice que
    # realmente não exista em nenhuma fonte permanece como observação.
    contract_only_metadata = metadata()
    contract_only_metadata["catalogs"].pop("playstyles")
    from_contract = artifact(
        [unknown_style],
        [dimension("105")],
        metadata_value=contract_only_metadata,
        playstyle_catalog={
            "table": "playstyle",
            "rows": [{"indice": 30, "id_jogo": 350, "nome_pt": "Mestre da linha alta", "bit": 120}],
        },
    )["cards"][0]
    assert from_contract["motor_eligible"] is True
    assert from_contract["pendencias_conhecidas"] == []
    assert from_contract["componentes"]["estilos_de_jogo"]["prova_indice_defensivo"]["nome_pt"] == "Mestre da linha alta"

    absent_index = copy.deepcopy(unknown_style)
    absent_index["card_id"] = "1052"
    absent_index["defensive_style_id"] = 35
    absent_artifact = artifact([absent_index], [dimension("1052")])
    absent_result = absent_artifact["cards"][0]
    assert absent_result["motor_eligible"] is True
    assert absent_result["coleta_completa"] is True
    assert absent_result["pendencias_conhecidas"][0]["tipo"] == "indice_estilo_defensivo_ausente_catalogo"
    assert absent_result["pendencias_conhecidas"][0]["indice"] == 35
    assert absent_artifact["summary"]["pendencias_conhecidas_por_tipo"] == {
        "indice_estilo_defensivo_ausente_catalogo": 1,
    }

    # A marca humana bloqueia motores, não publicação, e continua aberta após mudança.
    seed = artifact([card("106")], [dimension("106")])["cards"][0]
    overrides = {
        "schema": readiness.OVERRIDE_SCHEMA,
        "cards": [{
            "card_id": "106",
            "estado": "incompleto_confirmado",
            "motivo": "Konami ainda não liberou as habilidades finais",
            "componentes": ["habilidades"],
            "evidencia": "conferido na tela",
            "input_fingerprint": seed["input_fingerprint"],
            "marcado_em": "2026-08-31T09:00:00-03:00",
        }],
    }
    blocked = artifact([card("106")], [dimension("106")], overrides)["cards"][0]
    assert blocked["motor_eligible"] is False
    assert blocked["coleta_completa"] is False
    assert blocked["marcacao_operador"]["insumos_mudaram_desde_marcacao"] is False
    changed = card("106")
    changed["attrs"][0] = 71
    changed_blocked = artifact([changed], [dimension("106")], overrides)["cards"][0]
    assert changed_blocked["motor_eligible"] is False
    assert changed_blocked["marcacao_operador"]["insumos_mudaram_desde_marcacao"] is True

    # A regra percorre cartas antigas e novas sem usar idade de entrada no banco.
    old_card, new_card = card("84"), card("106799999081317")
    all_rows = artifact([old_card, new_card], [dimension("84"), dimension("106799999081317")])
    assert all_rows["summary"]["cards"] == 2
    assert all_rows["summary"]["motor_eligible"] == 2
    assert all_rows["escopo"] == "todas_as_cartas_da_leitura"
    assert all_rows["semantica_ausencia"].startswith("conferido_sem_valor")

    # Carta base pode estar totalmente coletada e ainda ser não aplicável ao motor.
    base = card("107")
    base["tipo"] = "base"
    base["roda_motor"] = False
    base_result = artifact([base], [dimension("107")])["cards"][0]
    assert base_result["coleta_completa"] is True
    assert base_result["motor_eligible"] is False
    assert base_result["estado"] == "nao_aplicavel_aos_motores"

    # Uma carta fora dos motores continua não aplicável mesmo se sua coleta
    # estiver incompleta; a falta continua registrada separadamente.
    base_unread = card("108")
    base_unread["tipo"] = "base"
    base_unread["roda_motor"] = False
    base_unread.pop("habilidades_fisicas")
    base_unread_artifact = artifact([base_unread], [dimension("108")])
    base_unread_result = base_unread_artifact["cards"][0]
    assert base_unread_result["estado"] == "nao_aplicavel_aos_motores"
    assert base_unread_result["coleta_completa"] is False
    assert base_unread_result["motor_eligible"] is False
    assert base_unread_artifact["summary"]["aguardando_insumos"] == 0
    assert base_unread_artifact["summary"]["nao_aplicavel_aos_motores"] == 1
    assert base_unread_artifact["summary"]["coleta_incompleta_total"] == 1

    # Clube bruto lido que perdeu a ligação atual por licença é uma ausência
    # confirmada: fica visível, mas não vira falta nem bloqueio dos motores.
    unresolved_dimension = dimension("109")
    unresolved_dimension["pode_rodar_vinculos"] = False
    unresolved_dimension["codigo_clube"] = 4085
    unresolved_dimension["codigo_liga"] = None
    unresolved_dimension["falta_o_que_vinculos"] = "codigo_clube sem definicao em Team.bin dos tres CPKs"
    unresolved_artifact = artifact([card("109")], [unresolved_dimension])
    unresolved_result = unresolved_artifact["cards"][0]
    assert unresolved_result["estado"] == "pronto_para_motores"
    assert unresolved_result["coleta_completa"] is True
    assert unresolved_result["motor_eligible"] is True
    assert unresolved_result["componentes"]["vinculos"]["estado"] == "conferido_sem_vinculo_atual"
    assert unresolved_result["faltando_coleta"] == []
    assert unresolved_result["faltando"] == []
    assert unresolved_result["pendencias_de_resolucao"] == []
    assert unresolved_result["pendencias_conhecidas"] == [{
        "componente": "vinculos",
        "tipo": "clube_sem_vinculo_atual_por_licenca",
        "codigo_clube": 4085,
        "significado": "O card antigo preserva o código bruto do clube, mas a ligação atual sumiu após perda de licença.",
        "afeta_coleta": False,
        "bloqueia_motores": False,
        "bloqueia_publicacao": False,
        "acao": "Manter o aviso e o código bruto; não inventar um clube substituto.",
    }]
    assert unresolved_artifact["summary"]["aguardando_insumos"] == 0
    assert unresolved_artifact["summary"]["aguardando_decisao_de_vinculo"] == 0
    assert unresolved_artifact["summary"]["coleta_incompleta_total"] == 0
    assert unresolved_artifact["summary"]["motor_eligible"] == 1
    assert unresolved_artifact["summary"]["pendencias_de_resolucao_total"] == 0
    assert unresolved_artifact["summary"]["pendencias_de_resolucao_por_tipo"] == {}
    assert unresolved_artifact["summary"]["pendencias_conhecidas_total"] == 1
    assert unresolved_artifact["summary"]["pendencias_conhecidas_por_tipo"] == {
        "clube_sem_vinculo_atual_por_licenca": 1,
    }
    assert unresolved_artifact["summary"]["pendencias_conhecidas_exemplos_por_tipo"]["clube_sem_vinculo_atual_por_licenca"] == [{
        "card_id": "109",
        "nome": "Carta Teste",
        "tipo": "clube_sem_vinculo_atual_por_licenca",
        "tipo_carta": "colecionavel",
        "componente": "vinculos",
        "motivo": "O card antigo preserva o código bruto do clube, mas a ligação atual sumiu após perda de licença.",
    }]

    # Outro tipo de vínculo problemático, sem prova de código bruto coletado,
    # continua sendo falta real de coleta.
    other_unresolved_dimension = dimension("110")
    other_unresolved_dimension["pode_rodar_vinculos"] = False
    other_unresolved_dimension["falta_o_que_vinculos"] = "nacionalidade não lida"
    other_unresolved = artifact([card("110")], [other_unresolved_dimension])
    assert other_unresolved["cards"][0]["estado"] == "aguardando_insumos"
    assert other_unresolved["cards"][0]["coleta_completa"] is False
    assert any(item["componente"] == "vinculos" for item in other_unresolved["cards"][0]["faltando_coleta"])

    # O resumo guarda no máximo 12 exemplos por tipo, mesmo que haja mais cards.
    orphan_cards = [card(str(200 + index)) for index in range(13)]
    orphan_dimensions = []
    for index in range(13):
        row = dimension(str(200 + index))
        row.update({
            "pode_rodar_vinculos": False,
            "codigo_clube": 5000 + index,
            "falta_o_que_vinculos": "codigo_clube sem definicao em Team.bin dos tres CPKs",
        })
        orphan_dimensions.append(row)
    orphan_summary = artifact(orphan_cards, orphan_dimensions)["summary"]
    assert orphan_summary["pendencias_conhecidas_total"] == 13
    assert len(orphan_summary["pendencias_conhecidas_exemplos_por_tipo"]["clube_sem_vinculo_atual_por_licenca"]) == 12

    # A revisão compacta contém todas e somente as cartas colecionáveis, sem
    # detalhes de componentes e sem criar marcações para o operador.
    review_base = card("111")
    review_base["tipo"] = "base"
    review_base["roda_motor"] = False
    review_artifact = artifact([card("112"), review_base], [dimension("112"), dimension("111")])
    review = readiness.build_operator_review(review_artifact)
    assert review["schema"] == "clubef-prontidao-motores-revisao-operador-v1"
    assert review["database_write"] is False
    assert review["summary"]["cartas_colecionaveis"] == 1
    assert review["summary"]["marcacoes_operador"] == 0
    assert len(review["cards"]) == 1
    assert review["cards"][0]["card_id"] == "112"
    assert review["cards"][0]["marcacao_operador"] is None
    assert review["cards"][0]["faltando"] == []
    assert review["cards"][0]["pendencias_conhecidas"] == []
    assert "componentes" not in review["cards"][0]

    print("OK: ausência conferida não vira falta; playstyle usa índice físico; revisão começa sem marcações")


if __name__ == "__main__":
    main()
