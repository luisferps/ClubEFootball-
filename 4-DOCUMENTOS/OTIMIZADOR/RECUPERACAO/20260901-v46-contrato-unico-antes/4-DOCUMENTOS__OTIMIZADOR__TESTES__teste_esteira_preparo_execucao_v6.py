# -*- coding: utf-8 -*-
"""Guardas offline da esteira V6 do Otimizador.

Nenhum teste toca o banco, cria lote ou calcula uma build real. A intenção é
provar o contrato: o preparador só sela entradas, o worker só consome linha já
selada, e a conclusão não pode acontecer antes do último cartão preparado.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[3]
MOTOR = RAIZ / "2-MOTORES" / "OTIMIZADOR"
FILA = RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3"
MIGRACAO = FILA / "MIGRACAO-ESTEIRA-PREPARO-EXECUCAO-V6.sql"
ROLLBACK = FILA / "ROLLBACK-ESTEIRA-PREPARO-EXECUCAO-V6.sql"
IDENTITY_V7 = FILA / "MIGRACAO-ESTEIRA-PREPARO-EXECUCAO-V7-IDENTITY.sql"
TRANSPORTE_V18 = FILA / "MIGRACAO-RESILIENCIA-TRANSPORTE-V18.sql"


def carregar(nome: str, arquivo: Path):
    spec = importlib.util.spec_from_file_location(nome, arquivo)
    modulo = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(modulo)
    return modulo


preparo = carregar("preparo_fila_integral_v5_esteira", MOTOR / "preparo_fila_integral_v5.py")
fila = carregar("fila_producao_v3_esteira", MOTOR / "fila_producao_v3.py")


class GatewayPreparoEsteira:
    def __init__(self):
        self.chamadas = []
        self.pendentes = 2

    def rpc(self, nome, corpo=None):
        self.chamadas.append((nome, corpo or {}))
        if nome == "otimizador_producao_status_v6":
            return {
                "contrato": preparo.CONTRATO_V6,
                "lote_id": "00000000-0000-0000-0000-000000000606",
                "estado": "rodando", "estado_lote": "rodando",
                "pode_publicar": False,
                "preparo": {"total": 2, "concluido": 2 - self.pendentes, "pendentes": self.pendentes},
            }
        if nome == "otimizador_producao_preparar_fatia_v6":
            self.pendentes = 0
            return {
                "contrato": preparo.CONTRATO_V5,
                "lote_id": "00000000-0000-0000-0000-000000000606",
                "estado": "rodando", "estado_lote": "rodando",
                "pode_publicar": False,
                "preparo": {"total": 2, "concluido": 2, "pendentes": 0},
            }
        raise AssertionError("RPC inesperada: " + nome)


class GatewayWorkerEsteira:
    def __init__(self):
        self.chamadas = []
        self.resultados = []
        self.reservas = 0

    def rpc(self, nome, corpo=None):
        corpo = corpo or {}
        self.chamadas.append((nome, corpo))
        if nome == "otimizador_producao_contexto_lote_v3":
            return {
                "contrato": fila.CONTRATO,
                "lote_id": "00000000-0000-0000-0000-000000000606",
                "formula_fingerprint": fila.FORMULA_APROVADA,
                "motor_versao": fila.MOTOR_VERSAO,
                "impetos_condicionais": "desligados", "pode_publicar": False,
                "regua": {"contrato": "otimizador_regua_v2", "gate": {"pode_rodar": True}},
            }
        if nome == "otimizador_producao_reservar_linha_v6":
            self.reservas += 1
            if self.reservas == 1:
                return {
                    "contrato": fila.CONTRATO, "reservada": True,
                    "linha_id": 8001, "reserva_token": "00000000-0000-0000-0000-000000000606",
                    "card_id": "8538111", "funcao_id": 1, "posicao_id": 12,
                    "impeto_condicional_codigo": None, "impeto_condicional_nivel": None,
                    "carta": {"gate": {"pode_rodar": True}},
                    "carta_entrada_fingerprint": "entrada-fp",
                    "formula_fingerprint": fila.FORMULA_APROVADA,
                    "contrato_fingerprint": "contrato-fp", "motor_versao": fila.MOTOR_VERSAO,
                    "lote_fingerprint": "seed-fp", "impetos_condicionais": "desligados",
                }
            return {"contrato": fila.CONTRATO, "reservada": False, "estado_lote": "pausado"}
        if nome == "otimizador_producao_concluir_linha_v6":
            self.resultados.append(corpo["p_resultado"])
            return {"contrato": fila.CONTRATO, "linha_id": 8001, "pode_publicar": False}
        if nome == "otimizador_producao_controle_lote_v1":
            return {"contrato": fila.CONTRATO, "estado_lote": "pausado", "corrente": []}
        raise AssertionError("RPC inesperada: " + nome)


class WorkerEsteiraControlado(fila.WorkerFilaProducaoV3):
    def _preparar_executor(self, _contexto):
        self._runner = object()

    def _calcular(self, item):
        return {
            "card_id": item["card_id"], "funcao_id": item["funcao_id"],
            "posicao_id": item["posicao_id"], "b1": 104.0,
            "barras": {"shooting": 19}, "tecnico_id": 89, "habilidades": [],
            "builds_comparadas": 1, "builds_possiveis": 1,
            "formula_fingerprint": item["formula_fingerprint"],
            "contrato_fingerprint": item["contrato_fingerprint"],
            "motor_versao": item["motor_versao"], "lote_fingerprint": item["lote_fingerprint"],
            "carta_entrada_fingerprint": item["carta_entrada_fingerprint"],
            "impeto_condicional_codigo": None, "impeto_condicional_nivel": None,
        }


class FalhaTransporteControlada(Exception):
    recuperavel = True
    repetivel = False


class WorkerComTransporteInterrompido(fila.WorkerFilaProducaoV3):
    def _contexto_com_reconexao(self):
        raise FalhaTransporteControlada("rede interrompida antes da reserva")


class GatewaySemFalhaDeLote:
    def __init__(self):
        self.chamadas = []

    def rpc(self, nome, corpo=None):
        self.chamadas.append((nome, corpo or {}))
        raise AssertionError("não deve chamar RPC após a queda pré-reserva: " + nome)


class EsteiraV6Test(unittest.TestCase):
    def test_preparador_da_esteira_usa_v6_e_para_quando_nao_resta_candidata(self):
        gateway = GatewayPreparoEsteira()
        final = preparo.PreparadorFilaIntegralV5(
            gateway, "00000000-0000-0000-0000-000000000606", esteira=True,
        ).executar()
        self.assertEqual(final["preparo"]["pendentes"], 0)
        self.assertEqual([nome for nome, _ in gateway.chamadas], [
            "otimizador_producao_status_v6",
            "otimizador_producao_preparar_fatia_v6",
        ])
        self.assertEqual(gateway.chamadas[1][1]["p_limite"], 20)

    def test_worker_da_esteira_consume_reserva_v6_e_persiste_sem_publicar(self):
        gateway = GatewayWorkerEsteira()
        worker = WorkerEsteiraControlado(
            gateway, "00000000-0000-0000-0000-000000000606", esperar=0.01, esteira=True,
        )
        final = worker.executar()
        self.assertEqual(final["estado_lote"], "pausado")
        self.assertEqual(len(gateway.resultados), 1)
        nomes = [nome for nome, _ in gateway.chamadas]
        self.assertIn("otimizador_producao_reservar_linha_v6", nomes)
        self.assertIn("otimizador_producao_concluir_linha_v6", nomes)
        self.assertNotIn("otimizador_proxima_fila_v1", nomes)
        self.assertNotIn("gravar_build", nomes)

    def test_migracao_mantem_selo_estavel_e_adia_conclusao_ate_fim_do_preparo(self):
        texto = MIGRACAO.read_text(encoding="utf-8").lower()
        for trecho in (
            "otimizador_producao_iniciar_esteira_v6",
            "otimizador_producao_preparar_fatia_v6",
            "otimizador_producao_reservar_linha_v6",
            "otimizador_producao_concluir_linha_v6",
            "preparo_fingerprint_final",
            "v_lote.preparo_concluido < v_lote.preparo_total",
            "fingerprint = v_seed_fingerprint",
            "impetos_condicionais', 'desligados",
            "pode_publicar', false",
            "to service_role",
        ):
            self.assertIn(trecho, texto)
        self.assertNotIn("clube.fila", texto)
        self.assertNotIn("clube.build", texto)
        self.assertNotIn("roda_lote_v6", texto)
        self.assertNotIn("build_otimizador_id_seq", texto)

    def test_correcao_identity_v7_deixa_o_banco_gerar_o_id_e_recupera_so_a_linha_reservada(self):
        texto = IDENTITY_V7.read_text(encoding="utf-8").lower()
        self.assertIn("otimizador_producao_concluir_linha_v6", texto)
        self.assertIn("otimizador_producao_recuperar_esteira_v7", texto)
        self.assertIn("always identity", texto)
        self.assertIn("estado_otimizador = 'pendente'", texto)
        self.assertIn("formula_alterada', false", texto)
        self.assertIn("'preparo_pausado'", texto)
        self.assertNotIn("build_otimizador_id_seq", texto)
        self.assertNotIn("delete from", texto)

    def test_rollback_recusa_esteira_ativa_e_nao_apaga_resultados(self):
        texto = ROLLBACK.read_text(encoding="utf-8").lower()
        self.assertIn("rollback v6 recusado", texto)
        self.assertIn("preparo_concluido < preparo_total", texto)
        self.assertNotIn("delete from", texto)

    def test_formula_aprovada_permanece_exatamente_a_mesma(self):
        self.assertEqual(fila.formula_fingerprint(), fila.FORMULA_APROVADA)

    def test_queda_de_transporte_pre_reserva_nao_marca_lote_como_falho(self):
        gateway = GatewaySemFalhaDeLote()
        worker = WorkerComTransporteInterrompido(
            gateway, "00000000-0000-0000-0000-000000000606", esperar=0.01, esteira=True,
        )
        final = worker.executar()
        self.assertTrue(final["recuperavel"])
        self.assertEqual(final["estado_lote"], "rodando")
        self.assertFalse(gateway.chamadas)

    def test_migracao_v18_recupera_so_o_incidente_transitorio_sem_tocar_formula(self):
        texto = TRANSPORTE_V18.read_text(encoding="utf-8").lower()
        self.assertIn("nenhum contrato seguro respondeu", texto)
        self.assertIn("estado_otimizador = 'processando'", texto)
        self.assertIn("formula_fingerprint", texto)
        self.assertIn("pode_publicar is not false", texto)
        self.assertIn("otimizador_portal_local_v5", texto)
        self.assertNotIn("delete from", texto)
        self.assertNotIn("update clube_novo.build_linha_card", texto)


if __name__ == "__main__":
    unittest.main(verbosity=2)
