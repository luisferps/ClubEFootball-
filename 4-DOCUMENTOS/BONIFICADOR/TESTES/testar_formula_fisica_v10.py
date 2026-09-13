#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Provas offline, por valores esperados, da regra física V10 aprovada."""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MOTOR = ROOT / "2-MOTORES" / "BONIFICADOR" / "motor_bonus.py"
SOURCE = MOTOR.read_text(encoding="utf-8")
FUNCTIONS = {"nota_da_medida", "bonus_do_corpo", "bonus_do_corpo_writer", "_por_id"}


def load_functions() -> dict:
    tree = ast.parse(SOURCE, filename=str(MOTOR))
    selected = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS
    ]
    assert {node.name for node in selected} == FUNCTIONS
    namespace: dict = {}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(MOTOR), "exec"), namespace)
    return namespace


def rule(idx: int, direction: int, weight: int | float = 1,
         cuts: list[int] | None = None) -> dict:
    return {
        "idx": idx,
        "direcao": direction,
        "peso": weight,
        "cortes": cuts or [10, 20, 30, 40],
    }


def assert_exact_detail(total: float, detail: dict) -> None:
    assert sum(Decimal(str(value)) for value in detail.values()) == Decimal(str(total))


def run() -> None:
    scope = load_functions()
    note = scope["nota_da_medida"]
    body = scope["bonus_do_corpo"]
    writer = scope["bonus_do_corpo_writer"]

    # As quatro bordas pertencem à faixa de baixo: <=, exatamente como no JS aprovado.
    cuts = [10, 20, 30, 40]
    expected_notes = {
        9: -2, 10: -2, 11: -1, 20: -1, 21: 0,
        30: 0, 31: 1, 40: 1, 41: 2,
    }
    for value, expected in expected_notes.items():
        assert note(value, cuts) == expected, (value, note(value, cuts), expected)

    positive = {"1": {"medida": rule(0, +1)}}
    negative = {"1": {"medida": rule(0, -1)}}
    assert body(positive, [41], 1, 1.5)[:3] == (1.5, 2.0, 1.0)
    assert body(positive, [9], 1, 1.5)[:3] == (-1.5, -2.0, -1.0)
    assert body(negative, [9], 1, 1.5)[:3] == (1.5, 2.0, 1.0)
    assert body(negative, [41], 1, 1.5)[:3] == (-1.5, -2.0, -1.0)

    # Direção zero fica fora tanto do numerador quanto do máximo possível.
    neutral = {"1": {
        "ativa": rule(0, +1, 1),
        "neutra_peso_enorme": rule(1, 0, 999),
    }}
    neutral_result = writer(neutral, [41, 9], 1, 1.5)
    assert neutral_result is not None
    assert neutral_result[:3] == (1.5, 2.0, 1.0)
    assert neutral_result[3]["ativa"] == 1.5
    assert neutral_result[3]["neutra_peso_enorme"] == 0.0
    assert_exact_detail(neutral_result[0], neutral_result[3])

    # Altura pesa 5. O máximo varia por função e conta somente regras ativas.
    variable = {
        "10": {"altura": rule(0, +1, 5), "outra": rule(1, +1, 1)},
        "11": {"altura": rule(0, 0, 5), "outra": rule(1, +1, 1)},
    }
    func10 = body(variable, [41, 9], 10, 1.5)
    func11 = body(variable, [41, 9], 11, 1.5)
    assert func10 is not None and func10[:3] == (1.0, 8.0, 0.6667)
    assert func11 is not None and func11[:3] == (-1.5, -2.0, -1.0)

    # Caso ouro do banco: Messi atual, Atacante criador, funcao_id 14.
    names = [
        "altura", "coxa", "panturrilha", "cintura", "peito", "tamBraco",
        "tamPescoco", "comprPerna", "comprBraco", "comprPescoco",
        "largOmbro", "altOmbro",
    ]
    directions = [-1, 0, 0, 0, 0, 0, +1, 0, -1, +1, -1, -1]
    weights = [5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    all_cuts = [
        [171, 178, 184, 191], [5, 7, 8, 10], [4, 6, 8, 10],
        [3, 5, 7, 8], [3, 5, 7, 9], [4, 6, 7, 9],
        [5, 7, 9, 11], [5, 7, 10, 12], [3, 5, 7, 9],
        [4, 5, 7, 8], [5, 7, 9, 11], [3, 6, 8, 11],
    ]
    messi_mold = {"14": {
        name: rule(index, directions[index], weights[index], all_cuts[index])
        for index, name in enumerate(names)
    }}
    messi_body = [170, 9, 10, 7, 9, 8, 9, 3, 5, 6, 9, 2]
    messi = writer(messi_mold, messi_body, 14, 1.5)
    assert messi is not None
    assert messi[:3] == (0.975, 13.0, 0.65)
    assert messi[3]["altura"] == 0.75
    assert all(messi[3][name] == 0.0 for name, direction in zip(names, directions) if direction == 0)
    assert_exact_detail(messi[0], messi[3])

    # A formula fisica V10 permanece igual; o envelope atual inclui estilos V12.
    assert "v12-0909-estilo-funcao-ativacao-v1" in SOURCE
    assert "4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8" in SOURCE
    print("FORMULA_FISICA_V10_OK Messi=0.9750 soma=13 maximo=20 altura=0.75000000")


if __name__ == "__main__":
    run()
