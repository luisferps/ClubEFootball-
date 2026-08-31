# -*- coding: utf-8 -*-
"""Smoke test sem rede da interface local e da fronteira paginada V5."""

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
    def regua(self):
        return {"contrato": "otimizador_regua_v2"}

    def funcoes(self, regua):
        return [{"funcao_id": 1, "nome": "Teste"}]

    def tecnicos(self, regua):
        return [{"tecnico_id": 7, "nome": "Técnico", "proficiencia": 89, "boosts": []}]

    def saude(self):
        return {"ok": True, "contrato": "otimizador_regua_v2", "pode_rodar": True,
                "versao_interface": "teste", "modo": "consulta_local_v3"}

    def simular(self, card, funcao, tecnico, nivel_impeto=None):
        assert (card, funcao, tecnico) == ("89138556575063", 1, 7)
        return {"ok": True, "modo": "somente leitura"}

    def validar(self, card, funcao, tecnico, nivel_impeto=None):
        return {"ok": True, "simulacao": self.simular(card, funcao, tecnico, nivel_impeto),
                "paridade": {"ok": True}}

    @staticmethod
    def _fila():
        return {
            "ok": True, "disponivel": False,
            "estado": "aguardando_aplicacao_fila_v5", "estado_lote": "aguardando_aplicacao_fila_v5",
            "acoes": {"criar": False, "iniciar": False, "pausar": False,
                        "parar": False, "retomar": False, "preparar": False, "console": False},
            "confirmacao": {"parar_exige_confirmacao": True},
            "totais": {"cartas_selecionadas": 0, "linhas_geradas": 0,
                       "pendentes": 0, "em_processamento": 0, "concluidas": 0,
                       "bloqueadas": 0, "interrompidas": 0, "falhas": 0},
            "linha_atual": None, "itens": [], "pode_publicar": False,
            "preparo": {"estado": "nao_iniciado", "total": 0, "concluido": 0, "pendentes": 0},
            "mensagem": "A fila integral V5 aguarda aplicação explícita da migração.",
            "origem": "clube_novo somente; migração de fila V5 ainda ausente",
        }

    def painel_fila(self, *_, **__):
        return self._fila()

    def eventos_fila(self, *_, **__):
        dados = self._fila()
        return {"ok": True, "disponivel": False, "estado": dados["estado"],
                "itens": [], "mensagem": dados["mensagem"], "origem": dados["origem"]}

    def resultados_fila(self, *_, **__):
        dados = self._fila()
        return {"ok": True, "disponivel": False, "estado": dados["estado"],
                "itens": [], "mensagem": dados["mensagem"], "publicacao": "SEM PUBLICAÇÃO"}

    @staticmethod
    def _bloqueia():
        raise mod.ErroDaInterface("A fila integral V5 aguarda aplicação explícita da migração.", 409)

    def criar_fila(self): self._bloqueia()
    def iniciar_fila(self): self._bloqueia()
    def pausar_fila(self): self._bloqueia()
    def parar_fila(self, confirmado): self._bloqueia()
    def abrir_console_fila(self): self._bloqueia()


class GatewayRotulosCanonicos:
    def rpc(self, nome, corpo=None):
        if nome == "otimizador_regua_v2":
            return {"contrato": "otimizador_regua_v2", "funcoes": [
                {"funcao_id": 1}, {"funcao_id": 4},
            ]}
        if nome == "otimizador_catalogos_apresentacao_v1":
            return {"contrato": nome,
                    "funcoes": [{"funcao_id": 1, "rotulo": "Centroavante fixo"},
                                {"funcao_id": 4, "rotulo": "Goleiro defensivo"}],
                    "posicoes": [{"posicao_id": 12, "rotulo": "Centroavante"},
                                 {"posicao_id": 0, "rotulo": "Goleiro"}],
                    "tecnicos": [], "habilidades": [],
                    "impetos": [{"codigo_impeto": 301, "rotulo": "Ímpeto 301"}]}
        if nome == "otimizador_carta_apresentacao_v1":
            return {"card_id": corpo["p_card_id"], "nome": "Welington Pauletto"}
        if nome == "otimizador_cartas_apresentacao_v2":
            return {"contrato": "otimizador_apresentacao_v2", "itens": [
                {"card_id": card_id, "nome": "Welington Pauletto"}
                for card_id in corpo["p_card_ids"]
            ]}
        raise AssertionError(nome)


class GatewayStatusV5ComDefault:
    def __init__(self):
        self.chamadas = []

    def rpc(self, nome, corpo=None, ausente_ok=False):
        self.chamadas.append((nome, corpo, ausente_ok))
        if nome != "otimizador_producao_status_v5":
            raise AssertionError(nome)
        return {"contrato": "otimizador_fila_producao_v5", "lote_id": "lote-ativo"}


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

    def test_pagina_e_consulta_individual_continuam_disponiveis(self):
        status, corpo = self.requisicao("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"Otimizador", corpo)
        self.assertIn(b"Testar uma carta", corpo)
        self.assertIn(b"Resultados", corpo)
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

    def test_fila_e_resultados_ficam_honestamente_indisponiveis_sem_migracao_v5(self):
        for rota in ("/api/fila/status", "/api/fila/eventos", "/api/resultados"):
            status, corpo = self.requisicao("GET", rota)
            self.assertEqual(status, 200)
            resposta = json.loads(corpo)
            self.assertFalse(resposta["disponivel"])
            self.assertEqual(resposta["estado"], "aguardando_aplicacao_fila_v5")
            self.assertIn("V5", resposta["mensagem"])
        for rota in ("/api/fila/criar", "/api/fila/iniciar", "/api/fila/pausar", "/api/fila/retomar", "/api/fila/console"):
            status, corpo = self.requisicao("POST", rota)
            self.assertEqual(status, 409)
            self.assertFalse(json.loads(corpo)["ok"])
        status, corpo = self.requisicao("POST", "/api/fila/parar", {"confirmado": True})
        self.assertEqual(status, 409)
        self.assertFalse(json.loads(corpo)["ok"])

    def test_fronteira_tem_apenas_contratos_de_clube_novo_e_sem_fila_historica(self):
        self.assertEqual(mod.RPC_PERMITIDAS, {
            "otimizador_regua_v2", "otimizador_carta_v3",
            "otimizador_catalogos_apresentacao_v1", "otimizador_carta_apresentacao_v1",
            "otimizador_producao_status_v3", "otimizador_producao_contexto_lote_v3",
            "otimizador_producao_controlar_lote_v3",
            "otimizador_producao_reservar_linha_v3", "otimizador_producao_concluir_linha_v3",
            "otimizador_producao_bloquear_linha_v3", "otimizador_producao_falhar_lote_v3",
            "otimizador_producao_status_v5", "otimizador_producao_prevoo_integral_v5",
            "otimizador_producao_criar_lote_integral_v5", "otimizador_producao_preparar_fatia_v5",
            "otimizador_producao_controlar_preparo_v5", "otimizador_producao_fila_paginada_v5",
            "otimizador_producao_eventos_paginados_v5", "otimizador_cartas_apresentacao_v2",
            "otimizador_producao_iniciar_esteira_v6", "otimizador_producao_preparar_fatia_v6",
            "otimizador_producao_reservar_linha_v6", "otimizador_producao_concluir_linha_v6",
        })
        texto = SERVIDOR.read_text(encoding="utf-8")
        self.assertNotIn("otimizador_status_teste_v2", texto)
        self.assertNotIn("otimizador_fila_teste_v2", texto)
        self.assertNotIn("otimizador_eventos_teste_v2", texto)
        self.assertNotIn("otimizador_controlar_lote_teste_v2", texto)
        self.assertNotIn("fila_comparacao_legado_50", texto)
        self.assertNotIn("gravar_build", texto)
        self.assertNotIn("clube.fila", texto)
        self.assertNotIn("clube.build", texto)

    def test_chave_secreta_atual_fica_somente_no_apikey(self):
        atual = mod.cabecalhos_supabase("sb_secret_teste_sem_valor_real")
        self.assertEqual(atual["apikey"], "sb_secret_teste_sem_valor_real")
        self.assertNotIn("Authorization", atual)
        self.assertIn("User-Agent", atual)

        legado = mod.cabecalhos_supabase("jwt_legado_de_teste")
        self.assertEqual(legado["Authorization"], "Bearer jwt_legado_de_teste")

    def test_rotulos_continuam_resolvidos_por_ids_canonicos(self):
        servico = object.__new__(mod.ServicoOtimizador)
        servico.gateway = GatewayRotulosCanonicos()
        servico._nomes_cartas = {}
        servico._funcoes_por_id = {}
        servico._posicoes_por_id = {}
        servico._tecnicos_por_id = {}
        servico._habilidades_por_id = {}
        servico._impetos_por_id = {}
        servico._catalogos_apresentacao = None
        linhas = servico._linhas_com_rotulos([
            {"linha_id": 924, "card_id": "8538111", "funcao_id": 1, "posicao_id": 12,
             "impeto_condicional_codigo": 301, "impeto_condicional_nivel": 3,
             "builds_comparadas": 33830, "builds_possiveis": 357074384925258000},
            {"linha_id": 1116, "card_id": "8538147", "funcao_id": 4, "posicao_id": 0},
            {"linha_id": 999, "card_id": "8538111", "funcao_id": 99, "posicao_id": 98},
        ])
        self.assertEqual(linhas[0]["carta_rotulo"], "8538111 · Welington Pauletto")
        self.assertEqual(linhas[0]["funcao_rotulo"], "Centroavante fixo")
        self.assertEqual(linhas[0]["posicao_rotulo"], "Centroavante")
        self.assertEqual(linhas[1]["funcao_rotulo"], "Goleiro defensivo")
        self.assertEqual(linhas[1]["posicao_rotulo"], "Goleiro")
        self.assertEqual(linhas[2]["funcao_rotulo"], "ID 99 · catálogo ausente")
        self.assertEqual(linhas[2]["posicao_rotulo"], "ID 98 · catálogo ausente")
        js = (SERVIDOR.parent / "app.js").read_text(encoding="utf-8")
        self.assertIn("aguardando_aplicacao_fila_v5", js)
        self.assertIn("Iniciar fila integral", js)
        self.assertIn("otimizador_producao_fila_paginada_v5", SERVIDOR.read_text(encoding="utf-8"))
        self.assertIn("a.criar===true", js)
        self.assertIn("a.iniciar===true", js)
        self.assertIn("a.pausar!==true", js)
        self.assertIn("confirmarParar", js)
        interface = (SERVIDOR.parent / "index.html").read_text(encoding="utf-8")
        self.assertIn("Build campeã", interface)
        self.assertIn("<th>Tempo</th>", interface)
        self.assertIn("ESTEIRA V6 · SEM PUBLICAÇÃO", interface)
        self.assertNotIn('id="abrir-console"', interface)
        self.assertIn("pontuacao_final", js)
        self.assertIn("duracao_segundos", js)
        self.assertIn("Em processamento há", js)
        css = (SERVIDOR.parent / "style.css").read_text(encoding="utf-8")
        self.assertIn("position: sticky", css)

    def test_servico_real_recusa_controles_sem_consultar_gateway(self):
        servico = object.__new__(mod.ServicoOtimizador)
        status = servico._status_fila()
        self.assertFalse(status["disponivel"])
        self.assertEqual(status["estado"], "aguardando_aplicacao_fila_v5")
        for chamada in (servico.criar_fila, servico.iniciar_fila, servico.pausar_fila,
                         lambda: servico.parar_fila(True), servico.abrir_console_fila):
            with self.assertRaises(mod.ErroDaInterface) as erro:
                chamada()
            self.assertEqual(erro.exception.status, 409)

    def test_status_v5_envia_null_para_o_default_do_contrato(self):
        servico = object.__new__(mod.ServicoOtimizador)
        gateway = GatewayStatusV5ComDefault()
        servico.gateway = gateway
        status = servico._status_fila()
        self.assertTrue(status["disponivel"])
        self.assertEqual(gateway.chamadas, [
            ("otimizador_producao_status_v5", {"p_lote_id": None}, True),
        ])

    def test_saude_local_nao_dependa_de_regua_ou_fila(self):
        servico = object.__new__(mod.ServicoOtimizador)
        saude = servico.saude()
        self.assertTrue(saude["ok"])
        self.assertEqual(saude["contrato"], "controle_local_loopback_v1")
        self.assertIsNone(saude["pode_rodar"])

    def test_executavel_portatil_reconhece_a_interface_v26(self):
        raiz_motor = SERVIDOR.parent.parent
        launcher = (raiz_motor / "windows-app" / "ClubEfootballOtimizadorLauncher.cs").read_text(encoding="utf-8")
        compilador = (raiz_motor / "windows-app" / "COMPILAR-APLICATIVO.ps1").read_text(encoding="utf-8")
        compilador_servico = (raiz_motor / "windows-app" / "COMPILAR-SERVICO-PORTATIL.ps1").read_text(encoding="utf-8")
        bootstrap = (raiz_motor / "servico_portatil.py").read_text(encoding="utf-8")
        atalho = (raiz_motor / "RODAR-OTIMIZADOR.bat").read_text(encoding="utf-8")
        self.assertIn('ExpectedApp = "\\\"aplicativo\\\": \\"otimizador_clubefootball\\\""', launcher)
        self.assertIn('ExpectedVersion = "\\\"versao_interface\\\": \\"20260831-v27\\\""', launcher)
        self.assertIn("OtimizadorServico.exe", launcher)
        self.assertIn("CLUBEF_OTIMIZADOR_ROOT", launcher)
        self.assertNotIn("FindPythonW", launcher)
        self.assertIn("8769", launcher)
        self.assertIn("precisaCompilar", compilador)
        self.assertIn("COMPILAR-SERVICO-PORTATIL.ps1", compilador)
        self.assertIn("PyInstaller", compilador_servico)
        self.assertIn("CLUBEF_OTIMIZADOR_ROOT", bootstrap)
        self.assertIn("Otimizador ClubEfootball.exe", atalho)
        self.assertNotIn("COMPILAR-APLICATIVO.ps1", atalho)


if __name__ == "__main__":
    unittest.main(verbosity=2)
