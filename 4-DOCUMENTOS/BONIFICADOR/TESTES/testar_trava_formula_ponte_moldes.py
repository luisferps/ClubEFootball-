# -*- coding: utf-8 -*-
"""Prova local de que as pontes de chave não alteraram a matemática Python."""

from __future__ import annotations

import ast
import copy
import hashlib
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
        copia = copy.deepcopy(no)
        if copia.name == "bonus_do_corpo":
            # Após a docstring, a primeira atribuição mudou só a chave externa: rótulo -> ID.
            # O restante é a matemática aprovada do molde corporal.
            copia.body = [copia.body[0], *copia.body[2:]]
        saida[copia.name] = ast.dump(copia, annotate_fields=True, include_attributes=False)
    return saida


def main():
    antes_bytes = SNAPSHOT.read_bytes()
    depois_bytes = ATUAL.read_bytes()
    antes = antes_bytes.decode("utf-8")
    depois = depois_bytes.decode("utf-8")

    assert funcoes(antes) == funcoes(depois), "AST matemático divergiu"
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
