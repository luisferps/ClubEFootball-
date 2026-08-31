# -*- coding: utf-8 -*-
"""Testes sem rede da auditoria exclusiva do contrato V3."""

import importlib.util
import os
import unittest


RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CAMINHO = os.path.join(RAIZ, "2-MOTORES", "OTIMIZADOR", "auditar_entradas_v1.py")
SPEC = importlib.util.spec_from_file_location("auditar_entradas_v3", CAMINHO)
AUD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUD)


def carta_v3(card_id="1", atributo=80, gate=True, contrato=AUD.CONTRATO):
    return {
        "contrato": contrato,
        "card_id": card_id,
        "apresentacao": {"nome": "Teste", "posicao": "Centroavante"},
        "escalares": {"overall": 90, "altura": 180, "peso": 75, "idade": 30,
                      "level_cap": 20, "orcamento": 40, "cap_estimado": False},
        "dimensoes": {"nacionalidade_id": 1, "clube_id": 2, "liga_id": 3,
                      "tipo_carta_id": "1/0"},
        "posicao_principal_id": 12,
        "atributos": [{"indice_otimizador": i, "codigo": "A%d" % i,
                        "bit": i, "valor": atributo} for i in range(26)],
        "corpo": [{"pos": i, "codigo": "C%d" % i, "valor": i} for i in range(12)],
        "posicoes": [{"posicao_id": i, "nivel_aptidao": 2} for i in range(12)],
        "habilidades": [{"skill_id": 3, "ordem": 0, "bit_na_carta": 621,
                           "tipo": "comum", "fabricavel": True, "vetada": False,
                           "nome_apresentacao": "Habilidade A"}],
        "estilos_ia": [{"bit_estilo_ia": 10, "nome_apresentacao": "IA A"}],
        "pes": [{"campo": "pe_dominante", "valor": 0, "codigo": "PD0",
                   "nome_apresentacao": "Direito"},
                 {"campo": "pe_ruim_uso", "valor": 2, "codigo": "PU2"},
                 {"campo": "pe_ruim_precisao", "valor": 2, "codigo": "PP2"}],
        "playstyles": [{"slot_fisico": 1, "playstyle_id": 260,
                          "nome_apresentacao": "Estilo A"},
                         {"slot_fisico": 2, "playstyle_id": 256,
                          "nome_apresentacao": "Estilo B"}],
        "impetos": [],
        "gate": {"pode_rodar": gate, "motivos": [] if gate else ["bloqueado"]},
        "cardinalidades": {"atributos": 26, "corpo": 12, "posicoes": 12,
                             "posicao_principal": 1, "pes": 3, "playstyles": 2},
    }


class AuditoriaEntradasTest(unittest.TestCase):
    def test_contrato_v3_apto_aprova_leitura(self):
        relatorio = AUD.audita_cartas_v3(["1"], [carta_v3()])
        self.assertTrue(relatorio["aprovado_para_leitura"])
        self.assertTrue(relatorio["todos_aptos_para_motor"])
        self.assertEqual(relatorio["contrato_auditado"], AUD.CONTRATO)

    def test_ausente_no_v3_reprova_sem_fallback(self):
        relatorio = AUD.audita_cartas_v3(["1"], [])
        self.assertFalse(relatorio["aprovado_para_leitura"])
        self.assertEqual(relatorio["ocorrencias"][0]["status"], "ausente_no_contrato_v3")

    def test_gate_fechado_fica_visivel(self):
        relatorio = AUD.audita_cartas_v3(["1"], [carta_v3(gate=False)])
        self.assertTrue(relatorio["aprovado_para_leitura"])
        self.assertFalse(relatorio["todos_aptos_para_motor"])
        self.assertTrue(any(x["status"] == "bloqueado_gate_v3"
                            for x in relatorio["ocorrencias"]))

    def test_cardinalidade_invalida_reprova(self):
        carta = carta_v3()
        carta["cardinalidades"]["atributos"] = 25
        relatorio = AUD.audita_cartas_v3(["1"], [carta])
        self.assertFalse(relatorio["aprovado_para_leitura"])
        self.assertTrue(any(x["status"] == "cardinalidade_invalida"
                            for x in relatorio["ocorrencias"]))

    def test_versao_inesperada_reprova(self):
        relatorio = AUD.audita_cartas_v3(["1"], [carta_v3(contrato="outra")])
        self.assertFalse(relatorio["aprovado_para_leitura"])
        self.assertEqual(relatorio["ocorrencias"][0]["status"], "contrato_inesperado")

    def test_renomear_rotulos_nao_muda_assinatura(self):
        self.assertTrue(AUD.prova_renomeacao(carta_v3()))

    def test_mudar_skill_id_muda_assinatura(self):
        a, b = carta_v3(), carta_v3()
        b["habilidades"][0]["skill_id"] = 99
        self.assertNotEqual(AUD.fingerprint(AUD.assinatura_calculo(a)),
                            AUD.fingerprint(AUD.assinatura_calculo(b)))


if __name__ == "__main__":
    unittest.main()
