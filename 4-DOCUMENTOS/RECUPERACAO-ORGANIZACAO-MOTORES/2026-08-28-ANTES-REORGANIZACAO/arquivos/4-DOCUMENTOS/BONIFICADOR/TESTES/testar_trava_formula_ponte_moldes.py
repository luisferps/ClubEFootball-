# -*- coding: utf-8 -*-
"""Prova local de que a ponte de moldes não alterou a matemática Python."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[3]
ATUAL = RAIZ / "2-MOTORES" / "motor_bonus.py"
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
    return {
        no.name: ast.dump(no, annotate_fields=True, include_attributes=False)
        for no in arvore.body
        if isinstance(no, ast.FunctionDef) and no.name in FUNCOES_MATEMATICAS
    }


def main():
    antes_bytes = SNAPSHOT.read_bytes()
    depois_bytes = ATUAL.read_bytes()
    antes = antes_bytes.decode("utf-8")
    depois = depois_bytes.decode("utf-8")

    assert antes_bytes == depois_bytes, "runtime foi alterado durante a ponte"
    assert funcoes(antes) == funcoes(depois), "AST de função matemática divergiu"
    assert set(funcoes(depois)) == set(FUNCOES_MATEMATICAS)

    formula = "\n".join(funcoes(depois)[nome] for nome in FUNCOES_MATEMATICAS)
    print(
        "FORMULA_LOCK_OK runtime_sha256="
        + hashlib.sha256(depois_bytes).hexdigest()
        + " ast_sha256="
        + hashlib.sha256(formula.encode("utf-8")).hexdigest()
    )


if __name__ == "__main__":
    main()
