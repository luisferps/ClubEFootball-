# -*- coding: utf-8 -*-
"""Guardas locais para a troca V2 -> V3 e o fecho do legado do Otimizador."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[3]
MOTOR = RAIZ / "2-MOTORES" / "OTIMIZADOR"
FONTE = MOTOR / "fonte_unica.py"
FILA = MOTOR / "fila_comparacao_legado_50.py"
INTERFACE = MOTOR / "interface" / "servidor.py"
BANCO = RAIZ / "6-AVALIADOR-NO-RAILWAY" / "banco.py"
AUDITOR = MOTOR / "auditar_entradas_v1.py"
MIGRACOES = RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "MIGRACAO-ENTRADAS"


def carrega(nome: str, caminho: Path):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    modulo = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(modulo)
    return modulo


class ContratoV3MigracaoTest(unittest.TestCase):
    def test_consumidores_ativos_de_carta_usam_v3_e_falham_fechados(self):
        fonte = FONTE.read_text(encoding="utf-8")
        interface = INTERFACE.read_text(encoding="utf-8")
        railway = BANCO.read_text(encoding="utf-8")
        self.assertIn("otimizador_carta_v3", fonte)
        self.assertIn("otimizador_cartas_v3", fonte)
        self.assertIn("otimizador_carta_v3", interface)
        self.assertIn("otimizador_carta_v3", railway)
        self.assertIn("otimizador_pool_habilidades_v3", railway)
        self.assertNotIn("otimizador_carta_v2", fonte)
        self.assertNotIn("otimizador_cartas_v2", fonte)
        self.assertNotIn("otimizador_carta_v2", interface)
        self.assertNotIn("otimizador_carta_v2", railway)
        self.assertNotIn("otimizador_pool_habilidades_v2", railway)
        self.assertIn("contrato de carta inesperado", fonte)
        self.assertIn("contrato de carta inesperado", railway)

    def test_servico_railway_ler_carta_e_pool_por_ids_v3(self):
        banco = carrega("banco_otimizador_v3_teste", BANCO)
        chamadas = []

        def falso(caminho, corpo=None, timeout=30):
            chamadas.append((caminho, corpo))
            if caminho.endswith("otimizador_carta_v3"):
                return {
                    "contrato": "otimizador_entradas_v3", "card_id": "10",
                    "atributos": [{"indice_otimizador": 0, "valor": 80}],
                    "escalares": {"orcamento": 1}, "habilidades": [{"skill_id": 7}],
                    "impetos": [], "gate": {"pode_rodar": True},
                }
            if caminho.endswith("otimizador_pool_habilidades_v3"):
                return {"gate": {"pode_rodar": True}, "skill_ids": [7, 9]}
            raise AssertionError(caminho)

        banco._post = falso
        carta = banco.carta_para_simular("10")
        pool = banco.pool_da_funcao("10", 1)
        self.assertEqual(carta["atributos"], [80])
        self.assertEqual(pool, [7, 9])
        self.assertEqual(
            [x[0].rsplit("/", 1)[-1] for x in chamadas],
            ["otimizador_carta_v3", "otimizador_pool_habilidades_v3"],
        )

    def test_fila_nova_sela_v3_e_relacao_funcao_posicao_por_fk(self):
        fila = FILA.read_text(encoding="utf-8")
        v17 = (MIGRACOES / "MIGRACAO-FILA-SNAPSHOT-CARTA-V3-V17.sql").read_text(encoding="utf-8")
        v18 = (MIGRACOES / "MIGRACAO-FUNCAO-POSICAO-IDS-V18.sql").read_text(encoding="utf-8")
        self.assertIn('"carta_contrato":"otimizador_entradas_v3"', fila)
        self.assertIn('MOTOR_VERSAO="v8-clube_novo-v3-teste-legado-50"', fila)
        self.assertIn("public.otimizador_carta_v3(", v17)
        self.assertIn("otimizador_funcao_posicao", v18)
        self.assertIn("foreign key (funcao_id)", v18)
        self.assertIn("foreign key (posicao_id)", v18)
        self.assertIn("p.codigo_pt=any(fs.posicoes)", v18)  # somente tradução/rollback, nunca o consumidor final
        self.assertIn("fp.funcao_id=fs.id and fp.posicao_id=p.id", v18)

    def test_portas_historicas_recebem_fecho_e_rollback_isolado(self):
        v19 = (MIGRACOES / "MIGRACAO-BLOQUEIO-RPCS-LEGADAS-V19.sql").read_text(encoding="utf-8")
        v20 = (MIGRACOES / "MIGRACAO-FECHO-POOL-LEGADO-V20.sql").read_text(encoding="utf-8")
        rollback = (MIGRACOES / "ROLLBACK-BLOQUEIO-RPCS-LEGADAS-V19.sql").read_text(encoding="utf-8")
        for assinatura in ("otimizador_proxima_fila_v1", "gravar_build", "fila_do_motor",
                           "cartas_da_fila", "proxima_da_fila"):
            self.assertIn(assinatura, v19)
            self.assertIn(assinatura, rollback)
        self.assertIn("from public, anon, authenticated, service_role", v20)
        self.assertIn("use a fila selada de clube_novo", FONTE.read_text(encoding="utf-8"))
        self.assertIn("gravacao historica desativada", FONTE.read_text(encoding="utf-8"))

    def test_auditoria_compara_legado_somente_em_leitura_e_le_novo_v3(self):
        auditor = AUDITOR.read_text(encoding="utf-8")
        self.assertIn("otimizador_cartas_v3", auditor)
        self.assertIn("otimizador_entradas_v3", auditor)
        self.assertIn("cartas_do_motor", auditor)  # comparador, nunca executor
        self.assertIn("--todos-da-fila foi desativado", auditor)
        self.assertNotIn("otimizador_cartas_v1", auditor)
        self.assertNotIn("otimizador_cartas_v2", auditor)
        self.assertNotIn("otimizador_proxima_fila_v1", auditor)


if __name__ == "__main__":
    unittest.main(verbosity=2)
