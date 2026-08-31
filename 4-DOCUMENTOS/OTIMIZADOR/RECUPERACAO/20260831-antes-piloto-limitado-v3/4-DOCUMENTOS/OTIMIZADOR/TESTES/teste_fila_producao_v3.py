# -*- coding: utf-8 -*-
"""Testes offline da fila produtiva V3, sem banco nem execução em lote.

O teste exercita a sequência reserva -> cálculo selado -> conclusão -> pausa
com um dublê de RPC. Ele não chama o motor completo e não cria linha alguma.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[3]
MOTOR = RAIZ / "2-MOTORES" / "OTIMIZADOR"
MIGRACAO = RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3" / "MIGRACAO-FILA-PRODUCAO-V3.sql"
ROLLBACK = RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3" / "ROLLBACK-FILA-PRODUCAO-V3.sql"

spec = importlib.util.spec_from_file_location("fila_producao_v3", MOTOR / "fila_producao_v3.py")
fila = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(fila)


class GatewayDaFila:
    """Dublê determinístico: uma linha concluída, depois pausa confirmada."""

    def __init__(self):
        self.chamadas = []
        self.resultados = []

    def rpc(self, nome, corpo=None):
        corpo = corpo or {}
        self.chamadas.append((nome, corpo))
        if nome == "otimizador_producao_contexto_lote_v3":
            return {
                "contrato": fila.CONTRATO, "lote_id": "00000000-0000-0000-0000-000000000123",
                "formula_fingerprint": fila.FORMULA_APROVADA,
                "motor_versao": fila.MOTOR_VERSAO, "impetos_condicionais": "desligados",
                "pode_publicar": False,
                "regua": {"contrato": "otimizador_regua_v2", "gate": {"pode_rodar": True}},
            }
        if nome == "otimizador_producao_reservar_linha_v3":
            return {
                "contrato": fila.CONTRATO, "reservada": True,
                "linha_id": 7001, "reserva_token": "00000000-0000-0000-0000-000000000321",
                "card_id": "8538111", "funcao_id": 1, "posicao_id": 12,
                "impeto_condicional_codigo": None, "impeto_condicional_nivel": None,
                "carta": {"contrato": "otimizador_entradas_v3", "gate": {"pode_rodar": True}},
                "carta_entrada_fingerprint": "entrada-fp", "formula_fingerprint": fila.FORMULA_APROVADA,
                "contrato_fingerprint": "contrato-fp", "motor_versao": fila.MOTOR_VERSAO,
                "lote_fingerprint": "lote-fp", "impetos_condicionais": "desligados",
            }
        if nome == "otimizador_producao_concluir_linha_v3":
            self.resultados.append(corpo["p_resultado"])
            return {"contrato": fila.CONTRATO, "linha_id": 7001, "pode_publicar": False}
        if nome == "otimizador_producao_status_v3":
            return {"contrato": fila.CONTRATO, "estado_lote": "pausando", "corrente": []}
        if nome == "otimizador_producao_controlar_lote_v3":
            self.assert_confirmacao_de_pausa(corpo)
            return {"contrato": fila.CONTRATO, "estado_lote": "pausado"}
        raise AssertionError("RPC inesperada: " + nome)

    @staticmethod
    def assert_confirmacao_de_pausa(corpo):
        if corpo.get("p_acao") != "confirmar_pausa" or corpo.get("p_confirmado") is not False:
            raise AssertionError("pausa atômica foi confirmada com ação incorreta")


class WorkerControlado(fila.WorkerFilaProducaoV3):
    def _preparar_executor(self, _contexto):
        self._runner = object()

    def _calcular(self, item):
        # O teste não recalcula nada: apenas confirma os selos que a RPC deverá
        # validar ao persistir a saída real do Otimizador.
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


class FilaProducaoV3Test(unittest.TestCase):
    def test_formula_aprovada_continua_selada(self):
        self.assertEqual(fila.formula_fingerprint(), fila.FORMULA_APROVADA)

    def test_worker_reserva_uma_linha_conclui_e_confirma_pausa_sem_publicar(self):
        gateway = GatewayDaFila()
        worker = WorkerControlado(gateway, "00000000-0000-0000-0000-000000000123", esperar=0.01)
        final = worker.executar()
        self.assertEqual(final["estado_lote"], "pausado")
        self.assertEqual(len(gateway.resultados), 1)
        resultado = gateway.resultados[0]
        self.assertEqual(resultado["card_id"], "8538111")
        self.assertEqual(resultado["formula_fingerprint"], fila.FORMULA_APROVADA)
        self.assertIsNone(resultado["impeto_condicional_codigo"])
        nomes = [nome for nome, _ in gateway.chamadas]
        self.assertEqual(nomes[:3], [
            "otimizador_producao_contexto_lote_v3",
            "otimizador_producao_reservar_linha_v3",
            "otimizador_producao_concluir_linha_v3",
        ])
        self.assertNotIn("otimizador_proxima_fila_v1", nomes)
        self.assertNotIn("otimizador_fila_teste_v2", nomes)
        self.assertNotIn("gravar_build", nomes)

    def test_migracao_declara_snapshot_rsl_ids_e_gates_sem_legado(self):
        texto = MIGRACAO.read_text(encoding="utf-8")
        for trecho in (
            "otimizador_lote_producao_v3", "otimizador_lote_producao_carta_v3",
            "otimizador_lote_producao_linha_v3", "otimizador_evento_producao_v3",
            "enable row level security", "grant execute", "to service_role",
            "for update of q,l skip locked", "order by b.overall desc,b.card_id,b.funcao_id,b.posicao_id",
            "impetos_condicionais','desligados", "pode_publicar',false",
            "otimizador_producao_reservar_linha_v3", "otimizador_producao_concluir_linha_v3",
        ):
            self.assertIn(trecho, texto.lower())
        self.assertNotIn("clube.fila", texto.lower())
        self.assertNotIn("clube.build", texto.lower())
        self.assertNotIn("publicação autorizada", texto.lower())

    def test_executor_v3_nao_recarrega_carta_ou_regua_no_meio_do_lote(self):
        worker = (MOTOR / "fila_producao_v3.py").read_text(encoding="utf-8")
        lote = (MOTOR / "roda_lote_v6.py").read_text(encoding="utf-8")
        self.assertIn("prepara_lote_producao_v3(contexto[\"regua\"])", worker)
        self.assertIn("carrega_carta_snapshot_producao_v3(carta)", worker)
        self.assertNotIn("otimizador_proxima_fila_v1", worker)
        self.assertIn("_carrega_no_processo([], carregar_cartas=False)", lote)
        self.assertIn("_W['snapshot_only'] = True", lote)
        self.assertIn("if not c0 and not _W.get('snapshot_only')", lote)

    def test_rollback_recusa_apagar_lote_que_ja_tenha_sido_criado(self):
        texto = ROLLBACK.read_text(encoding="utf-8").lower()
        self.assertIn("if exists", texto)
        self.assertIn("rollback recusado", texto)
        self.assertIn("otimizador_lote_producao_v3", texto)


if __name__ == "__main__":
    unittest.main(verbosity=2)
