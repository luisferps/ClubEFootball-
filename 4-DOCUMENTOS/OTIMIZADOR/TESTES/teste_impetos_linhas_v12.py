# -*- coding: utf-8 -*-
"""Provas locais da identidade por nível e da contagem do universo da linha."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[3]
OTIMIZADOR = RAIZ / "2-MOTORES" / "OTIMIZADOR"
MIGRACAO = (RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "MIGRACAO-ENTRADAS" /
            "MIGRACAO-OTIMIZADOR-CLUBE-NOVO-IMPETOS-V12.sql")
MIGRACAO_CONTADORES = (
    RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "MIGRACAO-ENTRADAS" /
    "MIGRACAO-OTIMIZADOR-CONTADORES-OBRIGATORIOS-V13.sql"
)
FILA_LEGADO = OTIMIZADOR / "fila_comparacao_legado_50.py"
LANCADOR_FILA_HISTORICA = OTIMIZADOR / "RODAR-COMPARACAO-LEGADO-50-CARDS.bat"


def carrega(nome, caminho):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    modulo = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(modulo)
    return modulo


fonte = carrega("fonte_unica_v12_teste", OTIMIZADOR / "fonte_unica.py")
runner = carrega("roda_lote_v7_teste", OTIMIZADOR / "roda_lote_v6.py")


class MotorFalso:
    MBK = ("a", "b")
    ACCU = (0, 1, 2)

    class Card:
        def __init__(self, carta, m=1.0):
            self.orc = 2
            self.nmax_barra = {"a": 2, "b": 2}

    @staticmethod
    def _cands_impeto(card):
        return [(None, None), ([1], 99)]


class MotorContagemFalso:
    chamadas = 0

    @staticmethod
    def _melhor_tecnico(*args, **kwargs):
        MotorContagemFalso.chamadas += 1
        return {"_aval": 4 if MotorContagemFalso.chamadas == 1 else 3}

    @staticmethod
    def build_completo2(carta, tecnicos, fila):
        MotorContagemFalso._melhor_tecnico()
        MotorContagemFalso._melhor_tecnico()
        return {"nota": 1}


class ImpetosLinhasV12Test(unittest.TestCase):
    def setUp(self):
        self.carta = {
            "impetos": [
                {"codigo_impeto": 10, "condicional": False,
                 "efeitos": [{"indice_otimizador": 1, "delta": 2}]},
                {"codigo_impeto": 20, "condicional": True, "nivel_maximo": 5,
                 "efeitos": [{"indice_otimizador": 1, "delta": 5},
                              {"indice_otimizador": 3, "delta": 5}]},
            ]
        }

    def test_mesma_receita_materializa_cada_nivel(self):
        nivel_1 = dict(fonte.vetor_impetos_da_linha(self.carta, 20, 1))
        nivel_5 = dict(fonte.vetor_impetos_da_linha(self.carta, 20, 5))
        self.assertEqual(nivel_1, {1: 3, 3: 1})
        self.assertEqual(nivel_5, {1: 7, 3: 5})

    def test_codigo_nivel_sao_obrigatorios_e_limitados(self):
        with self.assertRaises(ValueError):
            fonte.vetor_impetos_da_linha(self.carta)
        with self.assertRaises(ValueError):
            fonte.vetor_impetos_da_linha(self.carta, 20, 6)
        with self.assertRaises(ValueError):
            fonte.vetor_impetos_da_linha(self.carta, 21, 1)

    def test_contagem_do_universo_e_separada_das_comparacoes(self):
        carta = {"arows": [[1, 12, 90]], "orc": 2}
        tecnicos = [{"boost": [1]}, {"boost": [1, 2]}, {"boost": [9]}]
        # 6 distribuições de barras x 2 ímpetos adicionais x 2 técnicos úteis
        # x C(6,5) escolhas de habilidade = 144 builds possíveis.
        self.assertEqual(
            runner._conta_builds_possiveis(carta, MotorFalso, tecnicos, list(range(6))),
            144,
        )

    def test_comparadas_soma_avaliacoes_internas_e_nao_rodadas_grandes(self):
        MotorContagemFalso.chamadas = 0
        build, comparadas = runner._executa_busca_contando_builds(
            MotorContagemFalso, {}, [], None)
        self.assertEqual(build, {"nota": 1})
        self.assertEqual(comparadas, 7)

    def test_saida_sem_boost_util_persiste_o_tecnico_do_mesmo_multiplicador(self):
        # Não escolhe por nome nem recalcula: o adaptador só identifica, por
        # ID canônico, qual técnico já forneceu o multiplicador da busca.
        tecnicos = [
            {"id": "900", "m": 1.036},
            {"id": "14", "m": 1.036},
            {"id": "7", "m": 1.020},
        ]
        self.assertEqual(
            runner._tecnico_id_canonico_do_multiplicador(tecnicos, 1.036), 14
        )
        self.assertIsNone(
            runner._tecnico_id_canonico_do_multiplicador(tecnicos, 1.050)
        )

    def test_banco_identifica_nivel_e_guarda_os_dois_contadores(self):
        sql = MIGRACAO.read_text(encoding="utf-8")
        contadores = MIGRACAO_CONTADORES.read_text(encoding="utf-8")
        self.assertIn("coalesce(impeto_condicional_codigo,-1)", sql)
        self.assertIn("coalesce(impeto_condicional_nivel,0)", sql)
        self.assertIn("alter column builds_comparadas set not null", contadores)
        self.assertIn("alter column builds_possiveis set not null", contadores)
        self.assertIn("builds_comparadas <= builds_possiveis", contadores)
        self.assertIn("coalesce(p_resultado->>'builds_comparadas','')", contadores)
        self.assertIn("coalesce(p_resultado->>'builds_possiveis','')", contadores)
        operacional = sql.split("create or replace function public.otimizador_regua_v2", 1)[1]
        self.assertNotIn("from clube.", operacional.lower())
        self.assertNotIn("join clube.", operacional.lower())

    def test_entrada_historica_esta_encerrada(self):
        worker = FILA_LEGADO.read_text(encoding="utf-8")
        lancador = LANCADOR_FILA_HISTORICA.read_text(encoding="utf-8")
        self.assertIn("frente de legado foi encerrada", worker)
        self.assertIn("raise SystemExit(MENSAGEM)", worker)
        self.assertNotIn("otimizador_", worker)
        self.assertIn("exit /b 1", lancador.lower())
        self.assertNotIn("python", lancador.lower())
        self.assertFalse((OTIMIZADOR / "teste_fila_100.py").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
