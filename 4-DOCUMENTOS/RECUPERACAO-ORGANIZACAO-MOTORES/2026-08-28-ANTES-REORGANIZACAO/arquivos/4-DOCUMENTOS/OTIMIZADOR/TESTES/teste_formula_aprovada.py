"""Regressao permanente da formula aprovada em 28/08/2026.

Executa as implementacoes reais sem consultar nem escrever no banco. Os modulos de
catalogo sao substituidos por insumos minimos deterministas do proprio teste.
"""

from __future__ import annotations

import importlib.util
import math
import pathlib
import sys
import types

import numpy as np


RAIZ = pathlib.Path(__file__).resolve().parents[3]
MOTORES = RAIZ / "2-MOTORES"
SERVIDOR = RAIZ / "6-AVALIADOR-NO-RAILWAY"


def carregar(nome: str, caminho: pathlib.Path):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nome] = modulo
    assert spec.loader is not None
    spec.loader.exec_module(modulo)
    return modulo


fonte = types.ModuleType("fonte_unica")
fonte.tabela_multiplicador = lambda: {0: 1.0, 89: 1.036, 99: 1.036}
fonte.catalogo_habilidades = lambda: {}
fonte.catalogo_fabricaveis = lambda: []
sys.modules["fonte_unica"] = fonte

equacao = carregar("equacao", MOTORES / "equacao.py")

regua_motor = types.ModuleType("regua")
regua_motor.DEG = [1.0] * 200
regua_motor.K = 1.0
regua_motor.TETO_PUN = 9
regua_motor.VMAX = 200
regua_motor.pts_table = lambda alvo, peso: np.arange(201, dtype=float)
regua_motor.pts_regua = lambda alvo, peso: np.arange(201, dtype=float)
regua_motor.notaDe = lambda vals, arows: float(sum(vals[i] * p for i, p, _ in arows))
regua_motor.nota_por_tabela = lambda *args, **kwargs: 0.0
regua_motor.tabela_com_buff = lambda *args, **kwargs: np.arange(201, dtype=float)
sys.modules["regua"] = regua_motor
motor = carregar("motor_formula_aprovada", MOTORES / "motor.py")

regua_servidor = types.ModuleType("regua_do_banco")
regua_servidor.Regua = object


class ReguaIncompleta(Exception):
    pass


regua_servidor.ReguaIncompleta = ReguaIncompleta
sys.modules["regua_do_banco"] = regua_servidor
avaliador = carregar("avaliador_formula_aprovada", SERVIDOR / "avaliador.py")
otimizador = carregar("otimizador_formula_aprovada", SERVIDOR / "otimizador.py")


def vetor(valor: int, indice: int = 10):
    out = [40] * 26
    out[indice] = valor
    return out


def zeros():
    return [0] * 26


def validar_equacao_e_otimizador_local():
    imp = zeros()
    imp[10] = 4
    boost = zeros()
    boost[10] = 1
    nivel = {b: 0 for b in equacao.MBK}

    assert equacao._mult(98, 1.036) == 99
    assert equacao._mult(99, 1.036) == 99
    assert equacao.alvo_util(1.036) == math.ceil(99 / 1.036)
    assert equacao.cadeia(vetor(99), nivel, 1.036, imp, boost)[10] == 104

    carta = {
        "base": vetor(99),
        "orc": 0,
        "arows": [(10, 1, 0)],
        "sl": [0, 0],
        "nm": [(10, 4)],
    }
    card = motor.Card(carta, m=1.036)
    assert card.aplicar(nivel, imp, boost)[10] == 104
    assert card.vals_finais(nivel, imp, boost)[10] == 104


class ReguaFake:
    attr = list(range(26))
    barra = {}
    custo = {i: i for i in range(26)}
    imp = {1: {10: 3}, 2: {10: 1}}
    tec = {7: {"proficiencia": 89, "boosts": [10]}}
    mult = {89: 1.036}
    p = {"metade_da_habilidade_perdedora": {"fator": 0.5}}
    hab = {}
    vmax = 200
    degraus = [1.0] * 200
    teto_punicao = 9
    punicao = {"incremento": "0.25*peso/12", "acessorio_nao_pune": True}


def validar_avaliador_e_otimizador_servidor():
    regua = ReguaFake()
    estado = {
        "barras": {},
        "impetos": [1, 2],
        "habilidades": [],
        "tecnico_id": 7,
        "proficiencia": 89,
    }
    valores, etapas = avaliador.cadeia(
        estado, {"atributos": vetor(99), "orcamento": 0}, regua
    )
    assert etapas["proficiencia"][10] == 99
    assert etapas["tecnico"][10] == 100
    assert etapas["impeto"][10] == 104
    assert valores[10] == 104

    imp = zeros()
    imp[10] = 4
    boost = zeros()
    boost[10] = 1
    o = otimizador.Otimizador(
        regua, vetor(99), 0, [(10, 0, 1)], imp, boost, {}, 1.036
    )
    assert int(o.vb[10][0]) == 104


def validar_contrato_canonico_do_tecnico():
    class ReguaPacoteFake:
        def __init__(self, dados, versao):
            self.tec = dados["tecnico"]
            self.versao = versao

    regua_servidor.Regua = ReguaPacoteFake
    monta_regua = carregar("monta_regua_formula_aprovada", SERVIDOR / "monta_regua.py")
    pac = {
        "contrato": "otimizador_regua_v1",
        "gate": {"pode_rodar": True},
        "parametros": {"x": 1},
        "atributos": [{"indice_otimizador": i, "codigo": str(i)} for i in range(26)],
        "barras": {"x": [0]},
        "custo_nivel": {"0": 0},
        "multiplicadores": {"89": 1.036},
        "funcoes": [{"funcao_id": 1, "codigo_compatibilidade": "x"}],
        "molde": [{"funcao_id": 1, "indice_otimizador": 0, "alvo": 90, "peso": 1}],
        "habilidades": [{"skill_id": 1, "fabricavel": True, "vetada": False,
                           "nome_apresentacao": "teste", "efeitos": []}],
        "versao_molde": 1,
        "tecnicos": [{
                "tecnico_id": 17601312850052,
                "nome_apresentacao": "Fabio Capello",
                "proficiencias": [
                    {"codigo_estilo": "possessionGame", "valor": 46},
                    {"codigo_estilo": "longBallCounter", "valor": 89},
                    {"codigo_estilo": "quickCounter", "valor": 57},
                    {"codigo_estilo": "longBall", "valor": 89},
                    {"codigo_estilo": "outWide", "valor": 64},
                ],
                "proficiencia_maxima": 89,
                "estilos_principais": ["longBallCounter", "longBall"],
                "boosts": [
                    {"indice_otimizador": 6, "delta": 1},
                    {"indice_otimizador": 10, "delta": 1},
                ],
            }],
    }
    regua = monta_regua.da_rpc(pac, tatica="possessionGame")
    capello = regua.tec[17601312850052]
    assert capello["proficiencia"] == 89
    assert capello["boosts"] == [6, 10]
    assert capello["estilos_principais"] == ["longBallCounter", "longBall"]


def validar_servicos_e_encaminhamento_separado():
    servidor = (SERVIDOR / "servidor.py").read_text(encoding="utf-8")
    app = (SERVIDOR / "app.py").read_text(encoding="utf-8")
    lote = (MOTORES / "roda_lote_v6.py").read_text(encoding="utf-8")

    ordem_servidor = [
        "v = [AV._mult(ref[i], d['m']) for i in range(len(ref))]",
        "v = [v[i] + d['boost_add'][i] for i in range(len(v))]",
        "v = [v[i] + d['impeto_add'][i] for i in range(len(v))]",
    ]
    posicoes = [servidor.index(linha) for linha in ordem_servidor]
    assert posicoes == sorted(posicoes)
    assert "d['impeto_add'], d['boost_add'], d['buff'], d['m']" in servidor
    assert "impeto_add, boost_add, buff, m" in app
    assert "vals_finais(b['lvl'], _impeto_add, _boost_add)" in lote


if __name__ == "__main__":
    validar_equacao_e_otimizador_local()
    validar_avaliador_e_otimizador_servidor()
    validar_contrato_canonico_do_tecnico()
    validar_servicos_e_encaminhamento_separado()
    print("OK: Messi 99 -> proficiencia 99 -> boost 100 -> Precisao 104; Capello canonico preservado")
