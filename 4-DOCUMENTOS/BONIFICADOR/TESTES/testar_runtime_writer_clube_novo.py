#!/usr/bin/env python3
"""Teste offline do writer do Bonificador. Não abre rede nem banco."""
from __future__ import annotations

import ast
import decimal
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MOTOR = ROOT / "2-MOTORES" / "BONIFICADOR" / "motor_bonus.py"
SOURCE = MOTOR.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE, filename=str(MOTOR))
FUNCTIONS = {
    "nota_da_medida",
    "bonus_do_corpo",
    "bonus_do_corpo_writer",
    "_por_id",
    "bonus_do_estilo",
    "bonus_do_estilo_componentes",
    "preparar_payload_writer",
    "validar_retorno_writer",
    "gravar_resultados_canonicos",
}
selected = []
for node in TREE.body:
    if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == "WRITER_BONUS"
        for target in node.targets
    ):
        selected.append(node)
    elif isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS:
        selected.append(node)
namespace: dict = {"decimal": decimal}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(MOTOR), "exec"), namespace)


def apt_row() -> dict:
    return {
        "build_linha_card_id": 991,
        "card_id": "176844",
        "funcao_id": 10,
        "funcao_codigo": "ZAG",
        "posicao_id": 3,
        "carta_versao": "completude-v1",
        "carta_fingerprint": "c" * 64,
        "contrato_versao": "bonificador-carta-v1",
        "contrato_fingerprint": "d" * 64,
        "formula_fingerprint": "e" * 64,
        "motor_bonus": "v9-3108-clube-novo-writer-v1",
        "b_corpo": 0.4,
        "b_pe_ruim": 0.2,
        "b_estilo": 1.5,
        "b_estilo_slot1": 1.0,
        "b_estilo_slot2": 0.5,
        "b_ia": 0.25,
        "b_total": 2.35,
        "detalhe": {"altura": 0.4},
        "faltou": [],
    }


def run() -> None:
    body_result = namespace["bonus_do_corpo_writer"](
        {"10": {
            "altura": {"idx": 0, "cortes": [170, 175, 180, 185], "peso": 2},
            "peso": {"idx": 1, "cortes": [60, 70, 80, 90], "peso": 1},
        }},
        [182, 76], 10, 1.5,
    )
    assert body_result is not None
    body_bonus, _body_sum, _body_pct, body_detail = body_result
    assert body_bonus == 0.5 and _body_sum == 2.0 and _body_pct == 0.6667
    assert body_detail and all(isinstance(value, (int, float)) for value in body_detail.values())
    assert sum(Decimal(str(value)) for value in body_detail.values()) == Decimal(str(body_bonus))

    bonus = namespace["bonus_do_estilo"]
    components = namespace["bonus_do_estilo_componentes"]
    base = {
        "parametro": {"estilo_ativo": 1.0, "estilo_ativo_secundario": 0.5},
        "casa": {"101": {"3": 10}, "202": {"3": 10}},
        "liga": {"101": [3], "202": [3]},
        "posicao_slot": {"3": "ofensivo"},
    }
    cases = [
        (base, 101, 202, (1.5, 1.0, 0.5)),
        ({**base, "posicao_slot": {"3": "defensivo"}}, 101, 202, (1.5, 0.5, 1.0)),
        (base, None, 202, (1.0, 0.0, 1.0)),
        ({**base, "posicao_slot": {"3": "defensivo"}}, 101, None, (1.0, 1.0, 0.0)),
    ]
    for rule, slot1, slot2, expected in cases:
        detail = components(rule, slot1, slot2, 10, 3)
        assert detail == expected
        assert bonus(rule, slot1, slot2, 10, 3) == detail[0]
        assert detail[0] == round(detail[1] + detail[2], 4)

    # Cobertura integral das combinações estruturais da fórmula: slot que
    # manda, slot vazio/preenchido, casa verdadeira/falsa e ativação secundária.
    for leading in ("ofensivo", "defensivo"):
        rule = {**base, "posicao_slot": {"3": leading}}
        for slot1 in (None, 101, 202, 303):
            for slot2 in (None, 101, 202, 303):
                for function_id in (10, 99):
                    detail = components(rule, slot1, slot2, function_id, 3)
                    assert bonus(rule, slot1, slot2, function_id, 3) == detail[0]
                    assert detail[0] == round(detail[1] + detail[2], 4)

    calls: list[tuple] = []

    def fake_rpc(name, body):
        calls.append((name, body))
        assert name == "gravar_build_bonificador_v4"
        payload = body["p_resultado"]
        assert set(payload) == {
            "build_linha_card_id", "card_id", "funcao_id", "posicao_id",
            "carta_versao", "carta_fingerprint", "contrato_versao",
            "contrato_fingerprint", "formula_fingerprint", "motor_versao",
            "bonus_pe", "bonus_fisico_total", "bonus_fisico_detalhe",
            "bonus_posicao", "bonus_playstyle_1", "bonus_playstyle_2",
            "bonus_ia", "bonus_outros", "bonus_total",
        }
        assert payload["bonus_posicao"] == 0.0
        assert payload["bonus_outros"] == {}
        assert payload["bonus_total"] == 2.35
        return {
            "gravado": True,
            "idempotente": False,
            "build_linha_card_id": payload["build_linha_card_id"],
            "build_bonificador_id": 1234,
            "resultado_fingerprint": "a" * 64,
            "carta_versao": payload["carta_versao"],
            "carta_fingerprint": payload["carta_fingerprint"],
            "readback": "ok",
        }

    blocked = apt_row()
    blocked["faltou"] = ["completude vigente nao esta apta para motor"]
    result = namespace["gravar_resultados_canonicos"]([blocked], fake_rpc)
    assert result == [] and calls == [], "resultado bloqueado tentou escrever"

    missing_seal = apt_row()
    missing_seal["formula_fingerprint"] = ""
    try:
        namespace["gravar_resultados_canonicos"]([missing_seal], fake_rpc)
    except RuntimeError as error:
        assert "selo obrigatorio" in str(error)
    else:
        raise AssertionError("resultado sem fingerprint tentou escrever")
    assert calls == [], "resultado sem fingerprint chamou o writer"

    result = namespace["gravar_resultados_canonicos"]([apt_row()], fake_rpc)
    assert len(result) == 1 and len(calls) == 1
    assert all(call[0] != "gravar_bonus" for call in calls)

    def divergent_rpc(name, body):
        assert name == "gravar_build_bonificador_v4"
        payload = body["p_resultado"]
        return {
            "gravado": True,
            "idempotente": False,
            "build_linha_card_id": payload["build_linha_card_id"] + 1,
            "build_bonificador_id": 1234,
            "resultado_fingerprint": "a" * 64,
            "carta_versao": payload["carta_versao"],
            "carta_fingerprint": payload["carta_fingerprint"],
            "readback": "ok",
        }

    try:
        namespace["gravar_resultados_canonicos"]([apt_row()], divergent_rpc)
    except RuntimeError as error:
        assert "outra identidade" in str(error)
    else:
        raise AssertionError("retorno divergente do writer foi aceito")

    assert "rpc('gravar_bonus'" not in SOURCE
    assert "rpc('bonificador_pares_v1'" not in SOURCE
    assert "bonificador_contexto_fila_v4" in SOURCE
    assert "Content-Profile" not in SOURCE and "Accept-Profile" not in SOURCE
    print("OK: bloqueado não escreve; apto usa somente writer público para clube_novo; retorno divergente falha fechado")


if __name__ == "__main__":
    run()
