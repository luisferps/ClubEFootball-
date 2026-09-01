# -*- coding: utf-8 -*-
"""Prova local, sem rede e sem escrita, da organização física do Bonificador."""

from __future__ import annotations

import ast
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[3]
MOTOR = RAIZ / "2-MOTORES" / "BONIFICADOR" / "motor_bonus.py"
ANTIGO = RAIZ / "2-MOTORES" / "motor_bonus.py"
CONFIG_COMPARTILHADO = RAIZ / "2-MOTORES" / "config.txt"


def main():
    assert MOTOR.is_file(), f"motor operacional ausente: {MOTOR}"
    assert not ANTIGO.exists(), f"caminho antigo ainda alcançável: {ANTIGO}"
    assert CONFIG_COMPARTILHADO.is_file(), "configuração compartilhada ausente"
    assert not (MOTOR.parent / "config.txt").exists(), "configuração foi copiada para o runtime"

    texto = MOTOR.read_text(encoding="utf-8")
    arvore = ast.parse(texto, filename=str(MOTOR))
    imports_locais = [
        no for no in ast.walk(arvore)
        if isinstance(no, ast.ImportFrom) and no.module and not no.level
    ]
    assert not imports_locais, "o motor ganhou dependência local inesperada"
    assert "_acha_a_casa" in texto and "config.txt" in texto
    assert "_executar_pipeline_vivo" in texto
    assert "bonificador_contexto_fila_v4" in texto
    print("ORGANIZACAO_OK motor=2-MOTORES/BONIFICADOR/motor_bonus.py config=compartilhado")


if __name__ == "__main__":
    main()
