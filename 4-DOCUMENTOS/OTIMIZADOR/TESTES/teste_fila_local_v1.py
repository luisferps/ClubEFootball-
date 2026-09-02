# -*- coding: utf-8 -*-
"""Provas offline do pacote portátil/local do Otimizador.

Não chama banco, não inicia lote e não roda a fórmula completa. Exercita o
contrato que impede credenciais no pacote, a reserva por identidade canônica e
o envio idempotente de resultados já duráveis no disco local.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[3]
MOTOR = RAIZ / "2-MOTORES" / "OTIMIZADOR"
MIGRACAO = RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3" / "MIGRACAO-PACOTE-LOCAL-V52-CURSOR-PORTATIL.sql"
ROLLBACK = RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3" / "ROLLBACK-PACOTE-LOCAL-V52-CURSOR-PORTATIL.sql"
MIGRACAO_STATUS_V54 = RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3" / "MIGRACAO-STATUS-LEVE-V54.sql"
ROLLBACK_STATUS_V54 = RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3" / "ROLLBACK-STATUS-LEVE-V54.sql"

if str(MOTOR) not in sys.path:
    sys.path.insert(0, str(MOTOR))
spec = importlib.util.spec_from_file_location("fila_local_v1", MOTOR / "fila_local_v1.py")
fila_local = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(fila_local)
spec_empacotador = importlib.util.spec_from_file_location(
    "empacotar_fila_integral_portatil_v1", MOTOR / "empacotar_fila_integral_portatil_v1.py"
)
empacotador = importlib.util.module_from_spec(spec_empacotador)
assert spec_empacotador.loader is not None
spec_empacotador.loader.exec_module(empacotador)


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
        self.bloqueadas = []
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
        if nome == "otimizador_producao_bloquear_linha_v3":
            self.bloqueadas.append(int(corpo["p_linha_id"]))
            return {"contrato": "otimizador_fila_producao_v3", "bloqueada": True}
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

    def test_copia_portatil_fatia_a_fila_em_mil_e_separa_o_estado_mutavel(self):
        destino = empacotador.empacotar(self.raiz, LOTE)
        pacote = fila_local.PacoteLocalV1(destino)
        pacote.validar_integridade()

        self.assertEqual(destino.parent.name, fila_local.PASTA_PACOTE_PORTATIL)
        self.assertEqual(pacote.manifesto["versao_pacote"], fila_local.VERSAO_PACOTE_LOCAL_V3)
        self.assertEqual(pacote.manifesto["formato"], "fatias-1000-v1")
        self.assertTrue(pacote.manifesto["portabilidade"]["entrada_inclusa"])
        self.assertFalse(pacote.manifesto["portabilidade"]["credenciais_inclusas"])
        self.assertNotEqual(pacote.pasta_estado, pacote.pasta)
        self.assertEqual(pacote.pasta_estado.parent, (self.raiz / "runtime" / "fila-local" / LOTE).resolve())
        self.assertRegex(pacote.pasta_estado.name, r"^[0-9a-f-]{36}$")
        self.assertEqual([len(linhas) for _, linhas in pacote.iter_blocos_linhas()], [2])
        self.assertEqual([linha["linha_id"] for linha in pacote.iter_linhas()], [701, 702])
        self.assertFalse(any("SUPABASE" in p.read_text(encoding="utf-8") for p in destino.rglob("*") if p.is_file()))

    def test_copia_do_pacote_nunca_reutiliza_estado_de_outra_maquina(self):
        destino = empacotador.empacotar(self.raiz, LOTE)
        pacote_origem = fila_local.PacoteLocalV1(destino)
        with mock.patch.object(fila_local.platform, "node", return_value="OUTRO-WINDOWS"):
            pacote_destino = fila_local.PacoteLocalV1(destino)

        self.assertNotEqual(pacote_origem.pasta_estado, pacote_destino.pasta_estado)
        self.assertEqual(pacote_origem.pasta_estado.parent, pacote_destino.pasta_estado.parent)

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

    def test_saida_de_bloco_so_fica_disponivel_ao_enviador_depois_do_marco_pronto(self):
        linha = next(self.pacote.iter_linhas())
        reserva = {"linha_id": linha["linha_id"], "ordem_fila": linha["ordem_fila"], "reserva_token": "token-bloco"}
        self.pacote.gravar_reserva(reserva)
        self.pacote.gravar_resultado(reserva, {"b1": 104.0, "tecnico_id": 89}, bloco_id="000001")
        self.assertEqual(self.pacote.arquivos_pendentes(somente_blocos_prontos=True), [])
        self.pacote.marcar_bloco_pronto("000001", 1)
        self.assertEqual(len(self.pacote.arquivos_pendentes(somente_blocos_prontos=True)), 1)

    def test_enviador_confirma_cem_sem_esperar_o_fim_do_bloco_de_mil(self):
        for numero in range(1, fila_local.TAMANHO_LOTE_ENVIO + 1):
            reserva = {
                "linha_id": 10_000 + numero,
                "ordem_fila": numero,
                "reserva_token": f"token-{numero}",
            }
            self.pacote.gravar_reserva(reserva)
            self.pacote.gravar_resultado(
                reserva,
                {"b1": 104.0, "tecnico_id": 89},
                bloco_id="000001",
            )

        enviador = fila_local.EnviadorLotesLocalV1(self.gateway, self.pacote)
        self.assertEqual(enviador.enviar_disponiveis(forcar=False), fila_local.TAMANHO_LOTE_ENVIO)
        self.assertEqual(len(self.gateway.lotes_recebidos), 1)
        self.assertEqual(
            len(self.gateway.lotes_recebidos[0]["p_resultados"]),
            fila_local.TAMANHO_LOTE_ENVIO,
        )
        self.assertEqual(self.pacote.arquivos_pendentes(), [])

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

    def test_piloto_controlado_para_apos_uma_linha_bloqueada_sem_tentar_a_seguinte(self):
        gateway = GatewayPilotoControlado()
        worker = fila_local.WorkerFilaLocalV1(gateway, self.pacote, esperar=0.01, limite_linhas=1)
        worker._preparar_executor = lambda: None

        def falhar(linha, reserva):
            raise fila_local.FalhaPacoteLocal("falha controlada da primeira linha")

        worker._calcular = falhar
        final = worker.executar()

        self.assertEqual(final["estado_lote"], "pausado")
        self.assertEqual(gateway.reservas, [701])
        self.assertEqual(gateway.bloqueadas, [701])
        self.assertEqual(gateway.controles, ["pausar", "confirmar_pausa"])
        self.assertEqual(gateway.lotes_recebidos, [])

    def test_worker_ler_pacote_fatiado_sem_nova_exportacao_do_banco(self):
        pacote = fila_local.PacoteLocalV1(empacotador.empacotar(self.raiz, LOTE))
        gateway = GatewayPilotoControlado()
        worker = fila_local.WorkerFilaLocalV1(gateway, pacote, esperar=0.01, limite_linhas=1)
        worker._preparar_executor = lambda: None
        worker._calcular = lambda linha, reserva: {
            "card_id": linha["card_id"], "funcao_id": linha["funcao_id"],
            "posicao_id": linha["posicao_id"], "tecnico_id": 89,
            "b1": 104.0, "barras": {}, "habilidades": [],
        }

        final = worker.executar()

        self.assertEqual(final["estado_lote"], "pausado")
        self.assertEqual(gateway.reservas, [701])
        self.assertEqual(len(gateway.lotes_recebidos), 1)
        self.assertFalse(any("pacote_local_" in nome for nome, _ in gateway.chamadas))
        self.assertTrue((pacote.pasta / "linhas" / "000001.jsonl").is_file())

    def test_aplicativo_portatil_recusa_download_oculto_se_a_fotografia_nao_foi_copiada(self):
        with mock.patch.dict(os.environ, {
            fila_local.AMBIENTE_PACOTE_LOCAL_OBRIGATORIO: "1",
        }, clear=False):
            with self.assertRaisesRegex(fila_local.FalhaPacoteLocal, "PACOTE-FILA-INTEGRAL"):
                fila_local.PacoteLocalV1.criar_do_contrato(self.gateway, LOTE, self.raiz)

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

    def test_status_v54_preserva_contrato_e_evitar_varredura_quando_o_resumo_e_zero(self):
        texto = MIGRACAO_STATUS_V54.read_text(encoding="utf-8").lower()
        rollback = ROLLBACK_STATUS_V54.read_text(encoding="utf-8").lower()
        for trecho in (
            "otimizador_producao_status_v6", "security definer", "set search_path to ''",
            "coalesce(v_resumo.processando, 0) > 0",
            "between 1 and 100", "statement_timeout to '5s'",
            "pode_publicar',false", "impeto_condicional_desligado",
        ):
            self.assertIn(trecho, texto)
        self.assertNotIn("roda_lote_v6", texto)
        self.assertNotIn("delete from", texto)
        self.assertNotIn("update clube_novo.build_linha_card", texto)
        self.assertIn("v11 recusada", rollback)
        self.assertIn("reset statement_timeout", rollback)
        self.assertNotIn("delete from", rollback)


if __name__ == "__main__":
    unittest.main(verbosity=2)
