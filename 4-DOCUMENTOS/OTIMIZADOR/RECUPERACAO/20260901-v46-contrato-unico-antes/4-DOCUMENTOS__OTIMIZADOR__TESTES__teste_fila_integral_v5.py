# -*- coding: utf-8 -*-
"""Guardas offline do preparo integral V5.

Nenhum teste desta unidade chama Supabase, cria lote ou executa o cálculo. Ele
verifica que a preparação é uma fase distinta e que o worker só continua V3
quando o lote já estiver parado e selado.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest import mock


RAIZ = Path(__file__).resolve().parents[3]
MOTOR = RAIZ / "2-MOTORES" / "OTIMIZADOR"
FILA = RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3"
MIGRACAO = FILA / "MIGRACAO-FILA-PRODUCAO-INTEGRAL-V5.sql"
ROLLBACK = FILA / "ROLLBACK-FILA-PRODUCAO-INTEGRAL-V5.sql"

spec = importlib.util.spec_from_file_location(
    "preparo_fila_integral_v5", MOTOR / "preparo_fila_integral_v5.py",
)
preparo = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(preparo)


class GatewayPreparoFalso:
    def __init__(self):
        self.chamadas = []
        self.estado = "preparando"

    def rpc(self, nome, corpo=None):
        corpo = corpo or {}
        self.chamadas.append((nome, corpo))
        if nome == "otimizador_producao_status_v5":
            return {
                "contrato": preparo.CONTRATO_V5,
                "lote_id": "00000000-0000-0000-0000-000000000555",
                "estado": self.estado, "estado_lote": self.estado,
                "pode_publicar": False,
            }
        if nome == "otimizador_producao_preparar_fatia_v5":
            self.estado = "parado"
            return {
                "contrato": preparo.CONTRATO_V5,
                "lote_id": "00000000-0000-0000-0000-000000000555",
                "estado": "parado", "estado_lote": "parado",
                "pode_publicar": False,
                "preparo": {"total": 10, "concluido": 10, "pendentes": 0},
            }
        raise AssertionError("RPC inesperada: " + nome)


class ErroDeConexaoFalso(RuntimeError):
    recuperavel = True


class GatewayPreparoComQueda(GatewayPreparoFalso):
    """Uma queda antes da fatia deve reconectar, não criar outra fila."""

    def __init__(self):
        super().__init__()
        self.primeira_consulta = True

    def rpc(self, nome, corpo=None):
        if nome == "otimizador_producao_status_v5" and self.primeira_consulta:
            self.primeira_consulta = False
            self.chamadas.append((nome, corpo or {}))
            raise ErroDeConexaoFalso("conexão temporariamente indisponível")
        return super().rpc(nome, corpo)


class GatewayPreparoComContratoInvalido(GatewayPreparoFalso):
    """Erro determinístico não pode ficar em loop de reconexão."""

    def rpc(self, nome, corpo=None):
        self.chamadas.append((nome, corpo or {}))
        return {"contrato": "contrato_errado", "lote_id": "outro", "pode_publicar": False}


class FilaIntegralV5Test(unittest.TestCase):
    def test_preparador_pede_fatia_e_nunca_chama_o_motor(self):
        gateway = GatewayPreparoFalso()
        final = preparo.PreparadorFilaIntegralV5(
            gateway, "00000000-0000-0000-0000-000000000555", tamanho_fatia=10,
        ).executar()
        self.assertEqual(final["estado_lote"], "parado")
        self.assertEqual([x[0] for x in gateway.chamadas], [
            "otimizador_producao_status_v5",
            "otimizador_producao_preparar_fatia_v5",
        ])
        texto = (MOTOR / "preparo_fila_integral_v5.py").read_text(encoding="utf-8")
        self.assertNotIn("import roda_lote_v6", texto)
        self.assertNotIn("trabalha(", texto)
        self.assertNotIn("clube.fila", texto)
        self.assertNotIn("clube.build", texto)

    def test_queda_de_conexao_reconecta_sem_fingir_erro_de_contrato(self):
        gateway = GatewayPreparoComQueda()
        eventos = []
        preparador = preparo.PreparadorFilaIntegralV5(
            gateway, "00000000-0000-0000-0000-000000000555", tamanho_fatia=10,
            ao_progresso=lambda _preparador, etapa, detalhe: eventos.append((etapa, detalhe)),
        )
        with mock.patch.object(preparo.time, "sleep"):
            final = preparador.executar()
        self.assertEqual(final["estado_lote"], "parado")
        self.assertEqual([nome for nome, _ in gateway.chamadas], [
            "otimizador_producao_status_v5",
            "otimizador_producao_status_v5",
            "otimizador_producao_preparar_fatia_v5",
        ])
        self.assertTrue(any(etapa == "reconectando_preparo" for etapa, _ in eventos))

    def test_erro_deterministico_para_com_motivo_em_vez_de_loop_infinito(self):
        gateway = GatewayPreparoComContratoInvalido()
        eventos = []
        final = preparo.PreparadorFilaIntegralV5(
            gateway, "00000000-0000-0000-0000-000000000555", tamanho_fatia=10,
            ao_progresso=lambda _preparador, etapa, detalhe: eventos.append((etapa, detalhe)),
        ).executar()
        self.assertFalse(final["ok"])
        self.assertFalse(final["recuperavel"])
        self.assertIn("contrato de status", final["erro"])
        self.assertEqual(len(gateway.chamadas), 1)
        self.assertIn(("falha_preparo", final["erro"]), eventos)

    def test_migracao_fatia_a_fila_e_preserva_linhagem_por_lote(self):
        texto = MIGRACAO.read_text(encoding="utf-8")
        for trecho in (
            "otimizador_lote_producao_candidata_v5",
            "lote_producao_id",
            "otimizador_lote_producao_linha_v5_linhagem_fk",
            "otimizador_producao_criar_lote_integral_v5",
            "otimizador_producao_preparar_fatia_v5",
            "coalesce(p_limite,0) not between 1 and 20",
            "otimizador_producao_fila_paginada_v5",
            "otimizador_cartas_apresentacao_v2",
            "enable row level security",
            "from public,anon,authenticated,service_role",
            "impetos_condicionais','desligados",
            "pode_publicar',false",
        ):
            self.assertIn(trecho, texto.lower())
        self.assertNotIn("clube.fila", texto.lower())
        self.assertNotIn("clube.build", texto.lower())
        self.assertNotIn("roda_lote_v6", texto.lower())

    def test_preparo_falha_fechado_se_a_carta_mudar(self):
        texto = MIGRACAO.read_text(encoding="utf-8")
        self.assertIn("carta_versao_snapshot", texto)
        self.assertIn("versão física da carta mudou durante o preparo", texto)
        self.assertIn("estado='falhou'", texto)
        self.assertIn("recrie a fotografia do lote", texto)

    def test_rollback_recusa_apagar_evidencia_integral(self):
        texto = ROLLBACK.read_text(encoding="utf-8").lower()
        self.assertIn("tipo_lote='integral'", texto)
        self.assertIn("rollback v5 recusado", texto)
        self.assertNotIn("delete from", texto)

    def test_servidor_usa_paginacao_v5_sem_fallback_da_fila_completa(self):
        servidor = (MOTOR / "interface" / "servidor.py").read_text(encoding="utf-8")
        self.assertIn("otimizador_producao_fila_paginada_v5", servidor)
        self.assertIn("otimizador_producao_criar_lote_integral_v5", servidor)
        self.assertIn("PreparadorFilaIntegralV5", servidor)
        self.assertNotIn('rpc("otimizador_producao_fila_v3"', servidor)
        self.assertNotIn('rpc("otimizador_producao_criar_lote_v3"', servidor)
        self.assertIn("formula_fingerprint() != FORMULA_APROVADA", servidor)


if __name__ == "__main__":
    unittest.main(verbosity=2)
