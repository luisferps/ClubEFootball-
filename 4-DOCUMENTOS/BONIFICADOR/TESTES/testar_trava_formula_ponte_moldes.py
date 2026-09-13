# -*- coding: utf-8 -*-
"""Trava V10: a correção autorizada mudou a matemática e tem casos ouro próprios."""

from __future__ import annotations

import ast
import hashlib
import runpy
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[3]
ATUAL = RAIZ / "2-MOTORES" / "BONIFICADOR" / "motor_bonus.py"
SNAPSHOT = (
    RAIZ
    / "4-DOCUMENTOS"
    / "BONIFICADOR"
    / "RECUPERACAO"
    / "2026-08-28-ANTES-PONTE-CANONICA-MOLDES"
    / "motor_bonus.py"
)
FUNCOES_MATEMATICAS = (
    "nota_da_medida",
    "bonus_do_corpo",
    "bonus_do_pe_ruim",
    "_por_id",
    "bonus_do_estilo",
    "bonus_do_estilo_ia",
)


def funcoes(texto: str):
    arvore = ast.parse(texto)
    saida = {}
    for no in arvore.body:
        if not isinstance(no, ast.FunctionDef) or no.name not in FUNCOES_MATEMATICAS:
            continue
        saida[no.name] = ast.dump(no, annotate_fields=True, include_attributes=False)
    return saida


def main():
    antes_bytes = SNAPSHOT.read_bytes()
    depois_bytes = ATUAL.read_bytes()
    antes = antes_bytes.decode("utf-8")
    depois = depois_bytes.decode("utf-8")

    assert funcoes(antes)["bonus_do_corpo"] != funcoes(depois)["bonus_do_corpo"], (
        "a trava antiga ainda está congelando o defeito físico"
    )
    assert set(funcoes(depois)) == set(FUNCOES_MATEMATICAS)
    assert "v11-0709-estilo-posicao-oficial-v1" in depois
    assert "2e80a07d51f2bc8f456f9710c82717d38e3142cb3d52fd325b7b587c58ed2879" in depois

    teste_formula = Path(__file__).with_name("testar_formula_fisica_v10.py")
    runpy.run_path(str(teste_formula), run_name="__main__")

    formula = "\n".join(funcoes(depois)[nome] for nome in FUNCOES_MATEMATICAS)
    print(
        "FORMULA_LOCK_V10_OK runtime_sha256="
        + hashlib.sha256(depois_bytes).hexdigest()
        + " ast_sha256="
        + hashlib.sha256(formula.encode("utf-8")).hexdigest()
    )


if __name__ == "__main__":
    main()
