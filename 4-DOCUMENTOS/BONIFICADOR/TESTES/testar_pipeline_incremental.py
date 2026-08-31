#!/usr/bin/env python3
"""Prova offline do pipeline vivo; não abre rede, banco nem cria arquivo local."""
from __future__ import annotations

import builtins
import io
import json
import os
import runpy
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MOTOR = ROOT / "2-MOTORES" / "BONIFICADOR" / "motor_bonus.py"


def regua() -> dict:
    return {
        "pode_rodar": True,
        "falta_o_que": [],
        "contrato": "bonificador-regua-v1",
        "contrato_fingerprint": "r" * 64,
        "parametro": {"bonus_corpo_max": 1.5, "estilo_ativo": 1.0,
                      "estilo_ativo_secundario": 0.5, "pe_ruim_teto": 1.0,
                      "pe_ruim_frequencia_0": 0.0, "pe_ruim_precisao_0": 0.0,
                      "estilo_ia_ponto": 1.0, "estilo_ia_teto": 4},
        "molde_corpo": {"1": {"altura": {"cortes": [170, 175, 180, 185],
                                            "peso": 1.0, "direcao": "+"}}},
        "corpo_ordem": {"0": {"nosso": "altura"}},
        "casa": {}, "liga": {}, "posicao_slot": {"3": "ofensivo"},
    }


def contexto() -> dict:
    return {"build_linha_card_id": 99, "card_id": "cardo-1", "funcao_id": 1,
            "funcao_codigo": "f-1", "posicao_id": 3, "carta_versao": "cv-1",
            "carta_fingerprint": "c" * 64, "contrato_versao": "bonificador-regua-v1",
            "contrato_fingerprint": "r" * 64, "formula_fingerprint": "f" * 64}


def carta(apta: bool) -> dict:
    return {"pode_rodar": apta, "falta_o_que": [] if apta else ["corpo incompleto"],
            "card_id": "cardo-1", "completude_motor": {"apto_motor": apta,
            "fingerprint": "c" * 64}, "carta_versao": "cv-1",
            "carta_fingerprint": "c" * 64, "contrato_versao": "bonificador-regua-v1",
            "corpo": [182], "pe_ruim_uso": 0, "pe_ruim_precisao": 0,
            "slot1_id_jogo": None, "slot2_id_jogo": None, "posicao_id": 3,
            "estilos_ia": []}


def executar(sequencia_contexto: list[list[dict]], apta: bool):
    chamadas, esperas, escritas = [], [], []
    original_urlopen, original_open, original_sleep = urllib.request.urlopen, builtins.open, time.sleep

    class Resposta:
        def __init__(self, valor): self.valor = valor
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return json.dumps(self.valor).encode("utf-8")

    def abrir(req, timeout=0):
        nome = req.full_url.rsplit("/", 1)[-1]
        corpo = json.loads(req.data.decode("utf-8"))
        chamadas.append(nome)
        if nome == "bonificador_regua_v1": return Resposta(regua())
        if nome == "bonificador_contexto_escrita_v2":
            return Resposta(sequencia_contexto.pop(0) if sequencia_contexto else [])
        if nome == "bonificador_carta_v1": return Resposta(carta(apta))
        if nome == "gravar_build_bonificador_v1":
            payload = corpo["p_resultado"]
            escritas.append(payload)
            return Resposta({"gravado": True, "idempotente": False,
                "build_linha_card_id": payload["build_linha_card_id"],
                "build_bonificador_id": 123, "resultado_fingerprint": "a" * 64,
                "carta_versao": payload["carta_versao"],
                "carta_fingerprint": payload["carta_fingerprint"], "readback": "ok"})
        raise AssertionError("RPC inesperada: " + nome)

    def abrir_arquivo(nome, modo="r", *args, **kwargs):
        if Path(nome).name == "NAO-SEI.txt" and "w" in modo:
            return io.StringIO()
        return original_open(nome, modo, *args, **kwargs)

    urllib.request.urlopen, builtins.open, time.sleep = abrir, abrir_arquivo, lambda segundos: esperas.append(segundos)
    os.environ["CLUBEF_BONIFICADOR_MAX_RODADAS"] = str(len(sequencia_contexto))
    os.environ["CLUBEF_BONIFICADOR_INTERVALO_SEGUNDOS"] = "1"
    try:
        try:
            runpy.run_path(str(MOTOR), run_name="__main__")
        except SystemExit as erro:
            assert erro.code == 0, erro.code
    finally:
        urllib.request.urlopen, builtins.open, time.sleep = original_urlopen, original_open, original_sleep
        os.environ.pop("CLUBEF_BONIFICADOR_MAX_RODADAS", None)
        os.environ.pop("CLUBEF_BONIFICADOR_INTERVALO_SEGUNDOS", None)
    return chamadas, esperas, escritas


def main():
    chamadas, esperas, escritas = executar([[], [contexto()], []], apta=True)
    assert chamadas.count("bonificador_contexto_escrita_v2") == 3, chamadas
    assert chamadas.count("bonificador_regua_v1") == 3, chamadas
    assert len(escritas) == 1 and escritas[0]["build_linha_card_id"] == 99

    chamadas, esperas, escritas = executar([[contexto()], []], apta=False)
    assert chamadas.count("bonificador_contexto_escrita_v2") == 2, chamadas
    assert escritas == [], "linha incompleta chamou o writer"
    assert "parar.wait(espera)" in MOTOR.read_text(encoding="utf-8")
    print("PIPELINE_INCREMENTAL_OK vazio_espera_reconsulta=sim apto_grava=1 incompleto_grava=0")


if __name__ == "__main__":
    main()
