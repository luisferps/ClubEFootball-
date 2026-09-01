# -*- coding: utf-8 -*-
"""Lança o Bonificador sem rede nem escrita produtiva.

A simulação devolve régua apta e zero pares. Assim, prova o bootstrap do executável
novo, a descoberta da configuração compartilhada e a parada antes de gravar bônus.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[3]
MOTOR = RAIZ / "2-MOTORES" / "BONIFICADOR" / "motor_bonus.py"


def main():
    assert MOTOR.is_file()
    harness = f"""
import json
import os
import runpy
import urllib.request

chamadas = []
class Resposta:
    def __init__(self, valor): self.valor = valor
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return json.dumps(self.valor).encode('utf-8')

def abrir(req, timeout=0):
    nome = req.full_url.rsplit('/', 1)[-1]
    chamadas.append(nome)
    if nome == 'bonificador_regua_v2':
        return Resposta({{
            'pode_rodar': True, 'falta_o_que': [], 'parametro': {{}},
            'molde_corpo': {{}}, 'corpo_ordem': {{}}, 'casa': {{}},
            'liga': {{}}, 'posicao_slot': {{}}
        }})
    if nome == 'bonificador_contexto_fila_v4':
        return Resposta([])
    raise AssertionError('RPC não permitida no smoke test: ' + nome)

urllib.request.urlopen = abrir
os.environ['CLUBEF_BONIFICADOR_MAX_RODADAS'] = '1'
try:
    runpy.run_path({str(MOTOR)!r}, run_name='__main__')
except SystemExit as erro:
    assert erro.code == 0, erro.code
assert chamadas == ['bonificador_regua_v2', 'bonificador_contexto_fila_v4'], chamadas
print('LANCAMENTO_ISOLADO_OK pipeline=max_rodadas_1 regua,contexto_v2 sem_pendencia=sucesso gravacao=nao')
"""
    resultado = subprocess.run(
        [sys.executable, "-c", harness],
        cwd=RAIZ,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "LANCAMENTO_ISOLADO_OK" in resultado.stdout, resultado.stdout
    print(resultado.stdout.strip().splitlines()[-1])


if __name__ == "__main__":
    main()
