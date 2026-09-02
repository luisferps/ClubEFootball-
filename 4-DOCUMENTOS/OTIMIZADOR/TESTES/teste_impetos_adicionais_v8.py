# -*- coding: utf-8 -*-
"""Provas offline do catálogo oficial de Ímpetos adicionais V8.

Nada aqui consulta o banco, prepara pacote ou inicia a fila. O teste protege
precisamente as vagas físicas 1/2, a exceção Pacote total e o desempate que não
pode devolver uma vaga vazia quando há candidato válido.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import types
import unittest

import numpy as np


RAIZ = pathlib.Path(__file__).resolve().parents[3]
OTIMIZADOR = RAIZ / "2-MOTORES" / "OTIMIZADOR"
MIGRACAO = (RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "MIGRACAO-ENTRADAS" /
            "MIGRACAO-OTIMIZADOR-IMPETOS-ADICIONAIS-V14.sql")


def carregar(nome: str, caminho: pathlib.Path):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    modulo = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[nome] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def regua_minima(adicionais):
    return {
        "contrato": "otimizador_regua_v2",
        "gate": {"pode_rodar": True},
        "molde": [], "funcoes": [], "habilidades": [], "bloqueios": [],
        "incidencias": [], "tecnicos": [], "atributos": [], "parametros": {},
        "barras": {}, "custo_nivel": {}, "multiplicadores": {},
        # Um Ímpeto já equipado entra na fotografia da carta, não no catálogo.
        "impetos": [{"codigo_impeto": 999, "condicional": False, "efeitos": []}],
        "impetos_adicionais": adicionais,
    }


def adicional(codigo, regra, efeitos, slots=(1, 2), nome=""):
    return {
        "codigo_impeto": codigo,
        "nome_pt": nome,
        "regra": regra,
        "slots": list(slots),
        "efeitos": [
            {"indice_otimizador": indice, "delta": delta}
            for indice, delta in efeitos
        ],
    }


fonte_real = carregar("fonte_unica_impetos_v8", OTIMIZADOR / "fonte_unica.py")
CATALOGO = fonte_real._traduz_regua_v2(regua_minima([
    adicional(10, "delta_mais_um", [(0, 1), (1, 1)]),
    adicional(96, "pacote_total_excecao", [(0, 3), (1, 3)], nome="Pacote total"),
]))["impetos_adicionais"]


fonte_motor = types.ModuleType("fonte_unica")
fonte_motor.tabela_multiplicador = lambda: {0: 1.0, 99: 1.0}
fonte_motor.catalogo_habilidades = lambda: {}
fonte_motor.catalogo_fabricaveis = lambda: CATALOGO
sys.modules["fonte_unica"] = fonte_motor

equacao = carregar("equacao", OTIMIZADOR / "equacao.py")
regua = types.ModuleType("regua")
regua.DEG = [1.0] * 200
regua.K = 1.0
regua.TETO_PUN = 9
regua.VMAX = 200
regua.pts_table = lambda alvo, peso: np.arange(201, dtype=float)
regua.pts_regua = lambda alvo, peso: np.arange(201, dtype=float)
regua.notaDe = lambda valores, arows: 0.0  # força empate entre candidatos
regua.nota_por_tabela = lambda *args, **kwargs: 0.0
regua.tabela_com_buff = lambda *args, **kwargs: np.arange(201, dtype=float)
sys.modules["regua"] = regua
motor = carregar("motor_impetos_adicionais_v8", OTIMIZADOR / "motor.py")


def carta(slots):
    return {
        "base": [40] * 26,
        "orc": 0,
        "arows": [(0, 1, 0)],
        "sl": list(slots),
        "nm": [],
    }


class ImpetosAdicionaisV8Test(unittest.TestCase):
    def test_traducao_separa_catalogo_adicional_do_impeto_equipado(self):
        self.assertEqual(
            CATALOGO,
            [
                [10, 0, [[0, 1], [1, 1]]],
                [96, 0, [[0, 3], [1, 3]]],
                [10, 1, [[0, 1], [1, 1]]],
                [96, 1, [[0, 3], [1, 3]]],
            ],
        )
        self.assertNotIn(999, [int(item[0]) for item in CATALOGO])

    def test_pacote_total_e_excecao_explicita(self):
        self.assertIn([96, 0, [[0, 3], [1, 3]]], CATALOGO)
        with self.assertRaises(SystemExit):
            fonte_real._traduz_regua_v2(regua_minima([
                adicional(96, "pacote_total_excecao", [(0, 1)], nome="Pacote total"),
            ]))

    def test_slot_1_livre_nao_permite_opcao_vazia(self):
        candidatos = motor._cands_impeto(motor.Card(carta([1, 0])))
        self.assertEqual([10, 96], [nome for _efeito, nome in candidatos])
        self.assertNotIn((None, None), candidatos)

    def test_slot_2_livre_nao_permite_opcao_vazia(self):
        candidatos = motor._cands_impeto(motor.Card(carta([0, 1])))
        self.assertEqual([10, 96], [nome for _efeito, nome in candidatos])
        self.assertNotIn((None, None), candidatos)

    def test_dois_slots_livres_tem_desempate_estavel_no_slot_1(self):
        candidatos = motor._cands_impeto(motor.Card(carta([1, 1])))
        self.assertEqual([10, 96, 10, 96], [nome for _efeito, nome in candidatos])
        uteis = motor.impetos_uteis(motor.Card(carta([1, 1])))
        self.assertEqual([10, 96], [nome for _efeito, nome in uteis])
        self.assertNotIn((None, None), uteis)

    def test_sem_slot_livre_mantem_sem_impeto_adicional(self):
        self.assertEqual([(None, None)], motor._cands_impeto(motor.Card(carta([0, 0]))))

    def test_empate_nao_pode_reter_vaga_vazia(self):
        resultado = motor.Card(carta([1, 0])).build()
        self.assertEqual([10], resultado["fab"])

    def test_migracao_usa_somente_catalogo_canonico(self):
        sql = MIGRACAO.read_text(encoding="utf-8")
        self.assertIn("'impetos_adicionais'", sql)
        self.assertIn("a.delta<>1", sql)
        self.assertIn("a.delta<>3", sql)
        self.assertIn("'Pacote total'", sql)
        bloco = sql.split("'impetos_adicionais'", 1)[1]
        self.assertNotIn("carta_impeto_jogo", bloco)


if __name__ == "__main__":
    unittest.main(verbosity=2)
