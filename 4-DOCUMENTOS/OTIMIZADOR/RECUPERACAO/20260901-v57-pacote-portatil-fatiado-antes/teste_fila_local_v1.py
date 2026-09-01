# -*- coding: utf-8 -*-
"""Provas offline do pacote portátil/local do Otimizador.

Não chama banco, não inicia lote e não roda a fórmula completa. Exercita o
contrato que impede credenciais no pacote, a reserva por identidade canônica e
o envio idempotente de resultados já duráveis no disco local.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[3]
MOTOR = RAIZ / "2-MOTORES" / "OTIMIZADOR"
MIGRACAO = RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3" / "MIGRACAO-PACOTE-LOCAL-V52-CURSOR-PORTATIL.sql"
ROLLBACK = RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3" / "ROLLBACK-PACOTE-LOCAL-V52-CURSOR-PORTATIL.sql"

if str(MOTOR) not in sys.path:
    sys.path.insert(0, str(MOTOR))
spec = importlib.util.spec_from_file_location("fila_local_v1", MOTOR / "fila_local_v1.py")
fila_local = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(fila_local)


LOTE = "00000000-0000-0000-0000-000000000456"


class GatewayPacote:
    def __init__(self):
        self.chamadas = []
        self.lotes_recebidos = []

    @staticmethod
    def _manifesto():
        return {
            "contrato": fila_local.CONTRATO_PACOTE_LOCAL_V2,
            "lote_id": LOTE,
            "formula_fingerprint": fila_local.FORMULA_APROVADA,
            "contrato_fingerprint": "contrato-selado",
            "motor_versao": fila_local.MOTOR_VERSAO,
            "lote_fingerprint": "lote-selado",
            "pode_publicar": False,
            "impetos_condicionais": "desligados",
            "regua": {"contrato": "otimizador_regua_v2", "gate": {"pode_rodar": True}},
            "cartas_total": 1,
            "linhas_total": 2,
        }

    def rpc(self, nome, corpo=None):
        corpo = corpo or {}
        self.chamadas.append((nome, corpo))
        if nome == "otimizador_producao_pacote_local_manifesto_v2":
            return self._manifesto()
        if nome == "otimizador_producao_pacote_local_cartas_v2":
            itens = ([{
                "card_id": "8538111", "carta_nome": "Welington Pauletto",
                "carta_entrada_fingerprint": "carta-selo",
                "carta": {"contrato": "otimizador_entradas_v3", "gate": {"pode_rodar": True}},
            }] if corpo.get("p_depois_de_card_id") is None else [])
            return {
                "contrato": fila_local.CONTRATO_PACOTE_LOCAL_V2,
                "lote_id": LOTE,
                "contagem_no_manifesto": True,
                "proximo_card_id": itens[-1]["card_id"] if itens else None,
                "itens": itens,
            }
        if nome == "otimizador_producao_pacote_local_linhas_v2":
            itens = ([
                {"linha_id": 701, "ordem_fila": 1, "card_id": "8538111", "funcao_id": 1,
                 "posicao_id": 12, "carta_entrada_fingerprint": "carta-selo",
                 "carta_nome": "Welington Pauletto", "funcao_rotulo": "Centroavante fixo",
                 "posicao_rotulo": "Centroavante", "impeto_condicional_codigo": None,
                 "impeto_condicional_nivel": None},
                {"linha_id": 702, "ordem_fila": 2, "card_id": "8538111", "funcao_id": 2,
                 "posicao_id": 12, "carta_entrada_fingerprint": "carta-selo",
                 "carta_nome": "Welington Pauletto", "funcao_rotulo": "Centroavante móvel",
                 "posicao_rotulo": "Centroavante", "impeto_condicional_codigo": None,
                 "impeto_condicional_nivel": None},
            ] if corpo.get("p_depois_de_ordem") is None else [])
            return {
                "contrato": fila_local.CONTRATO_PACOTE_LOCAL_V2,
                "lote_id": LOTE,
                "contagem_no_manifesto": True,
                "proxima_ordem_fila": itens[-1]["ordem_fila"] if itens else None,
                "itens": itens,
            }
        if nome == "otimizador_producao_concluir_lote_local_v1":
            self.lotes_recebidos.append(corpo)
            return {
                "contrato": fila_local.CONTRATO_PACOTE_LOCAL_V1,
                "itens": [{"linha_id": item["linha_id"], "confirmada": True} for item in corpo["p_resultados"]],
            }
        raise AssertionError("RPC inesperada: " + nome)


class GatewayPilotoControlado(GatewayPacote):
    """Contrato falso que prova a pausa antes de uma segunda reserva."""

    def __init__(self):
        super().__init__()
        self.estado = "rodando"
        self.reservas = []
        self.controles = []

    def rpc(self, nome, corpo=None):
        corpo = corpo or {}
        if nome == "otimizador_producao_controle_lote_v1":
            return {"contrato": "otimizador_fila_producao_v3", "estado_lote": self.estado}
        if nome == "otimizador_producao_reservar_linha_local_v1":
            self.reservas.append(int(corpo["p_linha_id"]))
            return {
                "contrato": fila_local.CONTRATO_PACOTE_LOCAL_V1,
                "reservada": True,
                "reserva_token": f"token-{corpo['p_linha_id']}",
                "linha_id": int(corpo["p_linha_id"]),
                "ordem_fila": int(corpo["p_linha_id"]),
            }
        if nome == "otimizador_producao_controlar_lote_v3":
            self.controles.append(corpo["p_acao"])
            if corpo["p_acao"] == "pausar":
                self.estado = "pausando"
            elif corpo["p_acao"] == "confirmar_pausa":
                self.estado = "pausado"
            else:
                raise AssertionError("controle inesperado: " + str(corpo))
            return {"contrato": "otimizador_fila_producao_v3", "estado_lote": self.estado}
        return super().rpc(nome, corpo)


class FilaLocalV1Test(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.raiz = Path(self.temp.name) / "OTIMIZADOR"
        self.gateway = GatewayPacote()
        self.pacote = fila_local.PacoteLocalV1.criar_do_contrato(
            self.gateway, LOTE, self.raiz, tamanho_pagina=1000,
        )

    def test_pacote_portatil_tem_selos_e_nunca_conta_com_credencial(self):
        self.pacote.validar_integridade()
        self.assertTrue((self.pacote.pasta / "manifesto.json").is_file())
        self.assertFalse(any("SUPABASE" in p.read_text(encoding="utf-8") for p in self.pacote.pasta.rglob("*") if p.is_file()))
        self.assertEqual(self.pacote.manifesto["pode_publicar"], False)
        self.assertEqual(self.pacote.manifesto["impetos_condicionais"], "desligados")
        self.assertEqual([linha["linha_id"] for linha in self.pacote.iter_linhas()], [701, 702])
        self.assertEqual(self.pacote.carta_da_linha(next(self.pacote.iter_linhas()))["card_id"], "8538111")

    def test_spool_duravel_envia_lote_sem_recalcular_e_apaga_so_apos_confirmacao(self):
        linhas = list(self.pacote.iter_linhas())
        for linha in linhas:
            reserva = {"linha_id": linha["linha_id"], "ordem_fila": linha["ordem_fila"], "reserva_token": f"token-{linha['linha_id']}"}
            self.pacote.gravar_reserva(reserva)
            self.pacote.gravar_resultado(reserva, {
                "card_id": linha["card_id"], "funcao_id": linha["funcao_id"], "posicao_id": linha["posicao_id"],
                "b1": 104.0, "barras": {}, "tecnico_id": 89, "habilidades": [],
                "builds_comparadas": 1, "builds_possiveis": 1,
                "formula_fingerprint": self.pacote.manifesto["formula_fingerprint"],
                "contrato_fingerprint": self.pacote.manifesto["contrato_fingerprint"],
                "motor_versao": self.pacote.manifesto["motor_versao"],
                "lote_fingerprint": self.pacote.manifesto["lote_fingerprint"],
                "carta_entrada_fingerprint": linha["carta_entrada_fingerprint"],
                "impeto_condicional_codigo": None, "impeto_condicional_nivel": None,
            })
        enviador = fila_local.EnviadorLotesLocalV1(self.gateway, self.pacote)
        self.assertEqual(enviador.enviar_disponiveis(forcar=True), 2)
        self.assertEqual(len(self.gateway.lotes_recebidos), 1)
        self.assertEqual(len(self.gateway.lotes_recebidos[0]["p_resultados"]), 2)
        self.assertEqual(self.pacote.arquivos_pendentes(), [])
        self.assertFalse(any(self.pacote.reservas_path.glob("*.json")))

    def test_piloto_controlado_calcula_uma_linha_e_confirma_pausa_antes_da_proxima(self):
        gateway = GatewayPilotoControlado()
        worker = fila_local.WorkerFilaLocalV1(gateway, self.pacote, esperar=0.01, limite_linhas=1)
        worker._preparar_executor = lambda: None
        worker._calcular = lambda linha, reserva: {
            "card_id": linha["card_id"], "funcao_id": linha["funcao_id"],
            "posicao_id": linha["posicao_id"], "tecnico_id": 89,
            "b1": 104.0, "barras": {}, "habilidades": [],
        }

        final = worker.executar()

        self.assertEqual(final["estado_lote"], "pausado")
        self.assertEqual(gateway.reservas, [701])
        self.assertEqual(gateway.controles, ["pausar", "confirmar_pausa"])
        self.assertEqual(len(gateway.lotes_recebidos), 1)
        self.assertEqual(len(gateway.lotes_recebidos[0]["p_resultados"]), 1)
        self.assertEqual(self.pacote.arquivos_pendentes(), [])

    def test_migracao_expoe_somente_rpcs_de_servico_e_rollback_nao_apaga_lote(self):
        texto = MIGRACAO.read_text(encoding="utf-8").lower()
        rollback = ROLLBACK.read_text(encoding="utf-8").lower()
        for trecho in (
            "otimizador_producao_pacote_local_manifesto_v2",
            "otimizador_producao_pacote_local_cartas_v2",
            "otimizador_producao_pacote_local_linhas_v2",
            "security definer", "set search_path to ''", "to service_role",
            "revoke all on function", "pode_publicar", "impetos_condicionais",
            "otimizador_portal_local_v8",
            "p_depois_de_card_id", "p_depois_de_ordem",
        ):
            self.assertIn(trecho, texto)
        self.assertNotIn("clube.fila", texto)
        self.assertNotIn("clube.build", texto)
        self.assertNotIn("delete from clube_novo", rollback)
        self.assertNotIn("drop table", rollback)


if __name__ == "__main__":
    unittest.main(verbosity=2)
