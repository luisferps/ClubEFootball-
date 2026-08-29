# -*- coding: utf-8 -*-
"""Smoke test sem rede da interface local do Otimizador."""

from __future__ import annotations

import http.client
import importlib.util
import json
import threading
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[3]
SERVIDOR = RAIZ / "2-MOTORES" / "OTIMIZADOR" / "interface" / "servidor.py"
spec = importlib.util.spec_from_file_location("interface_otimizador", SERVIDOR)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class ServicoFalso:
    LOTE = "912c518e-091c-4583-ae91-97b3e717517e"

    def regua(self):
        return {"contrato": "otimizador_regua_v1"}

    def funcoes(self, regua):
        return [{"funcao_id": 1, "nome": "Teste"}]

    def tecnicos(self, regua):
        return [{"tecnico_id": 7, "nome": "Técnico", "proficiencia": 89, "boosts": []}]

    def saude(self):
        return {"ok": True, "contrato": "otimizador_regua_v1", "pode_rodar": True}

    def simular(self, card, funcao, tecnico):
        assert (card, funcao, tecnico) == ("89138556575063", 1, 7)
        return {"ok": True, "modo": "somente leitura"}

    def validar(self, card, funcao, tecnico):
        return {"ok": True, "simulacao": self.simular(card, funcao, tecnico),
                "paridade": {"ok": True}}

    def painel_fila(self):
        return {
            "ok": True, "disponivel": True, "lote_id": self.LOTE,
            "fingerprint": "026fbb294092b6f618b2122ea126b3afa2314da6363cf303674459ca1f85a0dc",
            "estado": "pausado", "estado_lote": "pausado", "execucao": {"estado": "pausado"},
            "modo": "teste_nao_publicado", "pode_publicar": False,
            "acoes": {"criar": False, "iniciar": True, "pausar": False, "parar": True, "retomar": True, "console": True},
            "confirmacao": {"parar_exige_confirmacao": True},
            "totais": {"cartas_selecionadas": 100, "linhas_geradas": 896, "pendentes": 895,
                       "em_processamento": 0, "concluidas": 1, "bloqueadas": 0, "interrompidas": 0, "falhas": 0},
            "linha_atual": None,
            "itens": [{"linha_id": 924, "card_id": "8538111", "funcao_id": 1,
                       "posicao_id": 12, "carta_rotulo": "8538111 · Welington Pauletto",
                       "funcao_rotulo": "Centroavante fixo", "posicao_rotulo": "Centroavante",
                       "pontuacao_final": "42.25", "duracao_segundos": 5,
                       "otimizador_iniciado_em": "2026-08-28T10:00:00Z",
                       "otimizador_finalizado_em": "2026-08-28T10:00:05Z", "estado": "concluido"}],
        }

    def eventos_fila(self):
        return {"ok": True, "disponivel": True, "lote_id": self.LOTE,
                "itens": [{"ordem": 1, "linha_id": 924, "card_id": "8538111",
                            "funcao_id": 1, "posicao_id": 12, "estado": "concluido"}]}

    def resultados_fila(self):
        dados = self.painel_fila()
        return {"ok": True, "disponivel": True, "lote_id": self.LOTE,
                "mensagem": "Resultados reais do lote de teste selado.", "itens": dados["itens"]}

    def iniciar_fila(self):
        return self.painel_fila()

    def pausar_fila(self):
        return self.painel_fila()

    def parar_fila(self, confirmado):
        if confirmado is not True:
            raise mod.ErroDaInterface("encerramento exige confirmação explícita nesta interface", 409)
        return self.painel_fila()

    def abrir_console_fila(self):
        return self.painel_fila()


class GatewayRotulosCanonicos:
    def rpc(self, nome, corpo=None):
        if nome == "otimizador_regua_v1":
            return {"contrato": "otimizador_regua_v1", "funcoes": [
                {"funcao_id": 1, "rotulo_apresentacao": "Centroavante fixo"},
                {"funcao_id": 4, "rotulo_apresentacao": "Goleiro defensivo"},
            ]}
        if nome == "otimizador_carta_v1":
            return {"apresentacao": {"nome": "Welington Pauletto"}, "posicoes": [
                {"posicao_id": 12, "nome_apresentacao": "Centroavante"},
            ]}
        raise AssertionError(nome)


class InterfaceOtimizadorTest(unittest.TestCase):
    def setUp(self):
        self.httpd = mod.criar_servidor(ServicoFalso(), 0)
        self.porta = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.thread.join(timeout=3)
        self.httpd.server_close()

    def requisicao(self, metodo, caminho, dados=None):
        conexao = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=5)
        corpo = json.dumps(dados).encode("utf-8") if dados is not None else None
        conexao.request(metodo, caminho, body=corpo,
                         headers={"Content-Type": "application/json"} if corpo else {})
        resposta = conexao.getresponse()
        corpo = resposta.read()
        conexao.close()
        return resposta.status, corpo

    def test_pagina_e_rotas_de_leitura(self):
        status, corpo = self.requisicao("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"Otimizador", corpo)
        self.assertIn(b"Fila automatizada", corpo)
        self.assertIn(b"Teste unit", corpo)
        self.assertIn(b"Resultados", corpo)
        self.assertIn(b">Iniciar<", corpo)
        self.assertIn(b">Pausar<", corpo)
        self.assertIn(b">Parar<", corpo)
        status, corpo = self.requisicao("GET", "/api/catalogos")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(corpo)["tecnicos"][0]["tecnico_id"], 7)
        status, corpo = self.requisicao("GET", "/api/simular?card_id=89138556575063&funcao_id=1&tecnico_id=7")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(corpo)["ok"])

    def test_valida_e_recusa_escrita(self):
        status, corpo = self.requisicao("GET", "/api/validar?card_id=89138556575063&funcao_id=1&tecnico_id=7")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(corpo)["paridade"]["ok"])
        status, corpo = self.requisicao("POST", "/api/simular")
        self.assertEqual(status, 405)
        self.assertFalse(json.loads(corpo)["ok"])

    def test_fila_real_e_controles_somente_pelo_selo(self):
        status, corpo = self.requisicao("GET", "/api/fila/status")
        resposta = json.loads(corpo)
        self.assertEqual(status, 200)
        self.assertTrue(resposta["disponivel"])
        self.assertEqual(resposta["lote_id"], ServicoFalso.LOTE)
        self.assertEqual(resposta["estado_lote"], "pausado")
        self.assertEqual(resposta["totais"]["linhas_geradas"], 896)
        self.assertTrue(resposta["acoes"]["iniciar"])
        self.assertTrue(resposta["acoes"]["parar"])
        self.assertTrue(resposta["confirmacao"]["parar_exige_confirmacao"])
        for rota in ("/api/fila/eventos", "/api/resultados"):
            status, corpo = self.requisicao("GET", rota)
            self.assertEqual(status, 200)
            resposta_rota = json.loads(corpo)
            self.assertTrue(resposta_rota["disponivel"])
            if rota == "/api/resultados":
                linha = resposta_rota["itens"][0]
                self.assertEqual(linha["carta_rotulo"], "8538111 · Welington Pauletto")
                self.assertEqual(linha["funcao_rotulo"], "Centroavante fixo")
                self.assertEqual(linha["posicao_rotulo"], "Centroavante")
                self.assertEqual(linha["pontuacao_final"], "42.25")
                self.assertEqual(linha["duracao_segundos"], 5)
                self.assertEqual(linha["otimizador_finalizado_em"], "2026-08-28T10:00:05Z")
        for rota in ("/api/fila/iniciar", "/api/fila/pausar", "/api/fila/retomar", "/api/fila/console"):
            status, corpo = self.requisicao("POST", rota)
            self.assertEqual(status, 200)
            self.assertTrue(json.loads(corpo)["ok"])
        for rota in ("/api/fila/criar", "/api/fila/parar"):
            status, corpo = self.requisicao("POST", rota)
            self.assertEqual(status, 409)
            self.assertFalse(json.loads(corpo)["ok"])
        status, corpo = self.requisicao("POST", "/api/fila/parar", {"confirmado": True})
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(corpo)["ok"])

    def test_fronteira_tem_apenas_contratos_selados(self):
        self.assertEqual(mod.RPC_PERMITIDAS, {
            "otimizador_regua_v1", "otimizador_carta_v1", "otimizador_status_teste_v1",
            "otimizador_fila_teste_v1", "otimizador_eventos_teste_v1",
            "otimizador_controlar_lote_teste_v2",
        })
        texto = SERVIDOR.read_text(encoding="utf-8")
        self.assertNotIn("gravar_build", texto)

    def test_rotulos_de_fila_vem_de_catalogos_por_id(self):
        servico = object.__new__(mod.ServicoOtimizador)
        servico.gateway = GatewayRotulosCanonicos()
        servico._nomes_cartas = {}
        servico._funcoes_por_id = {}
        servico._posicoes_por_id = {}
        servico._habilidades_por_id = {}
        linhas = servico._linhas_com_rotulos([
            {"linha_id": 924, "card_id": "8538111", "funcao_id": 1, "posicao_id": 12},
            {"linha_id": 1116, "card_id": "8538147", "funcao_id": 4, "posicao_id": 0,
             "posicao_nome": "Goleiro"},
            {"linha_id": 999, "card_id": "8538111", "funcao_id": 99, "posicao_id": 98},
        ])
        self.assertEqual(linhas[0]["carta_rotulo"], "8538111 · Welington Pauletto")
        self.assertEqual(linhas[0]["funcao_rotulo"], "Centroavante fixo")
        self.assertEqual(linhas[0]["posicao_rotulo"], "Centroavante")
        self.assertEqual(linhas[1]["funcao_rotulo"], "Goleiro defensivo")
        self.assertEqual(linhas[1]["posicao_rotulo"], "Goleiro")
        self.assertEqual(linhas[2]["funcao_rotulo"], "ID 99 · catálogo ausente")
        self.assertEqual(linhas[2]["posicao_rotulo"], "ID 98 · catálogo ausente")
        texto = SERVIDOR.read_text(encoding="utf-8")
        js = (SERVIDOR.parent / "app.js").read_text(encoding="utf-8")
        self.assertIn("a.iniciar===true", js)
        self.assertIn("a.pausar!==true", js)
        self.assertIn("acaoFila('pausar')", js)
        self.assertIn("confirmarParar", js)
        self.assertIn("Pontuação final", (SERVIDOR.parent / "index.html").read_text(encoding="utf-8"))
        interface = (SERVIDOR.parent / "index.html").read_text(encoding="utf-8")
        self.assertIn("<th>Tempo</th>", interface)
        self.assertIn("Build campeã", interface)
        self.assertIn("pontuacao_final", js)
        self.assertIn("duracao_segundos", js)
        self.assertIn("otimizador_finalizado_em", js)
        self.assertIn("Em processamento há", js)
        self.assertIn("Ver build campeã", js)
        self.assertNotIn("Detalhe não exposto pelo contrato da fila", js)
        self.assertNotIn("proxima_fila", texto)
        self.assertNotIn("cartas_do_motor", texto)
        self.assertNotIn("gravar_build", texto)


if __name__ == "__main__":
    unittest.main(verbosity=2)
