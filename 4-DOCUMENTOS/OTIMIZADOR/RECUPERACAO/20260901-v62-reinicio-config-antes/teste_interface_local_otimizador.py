# -*- coding: utf-8 -*-
"""Smoke test sem rede da interface local e da fronteira operacional V7."""

from __future__ import annotations

import http.client
import importlib.util
import json
import tempfile
import threading
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[3]
SERVIDOR = RAIZ / "2-MOTORES" / "OTIMIZADOR" / "interface" / "servidor.py"
APP = RAIZ / "2-MOTORES" / "OTIMIZADOR" / "interface" / "app.js"
INDEX = RAIZ / "2-MOTORES" / "OTIMIZADOR" / "interface" / "index.html"
spec = importlib.util.spec_from_file_location("interface_otimizador", SERVIDOR)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)
PREPARADOR = RAIZ / "2-MOTORES" / "OTIMIZADOR" / "preparo_fila_integral_v5.py"
MIGRACAO_TRANSPORTE_V18 = (
    RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3"
    / "MIGRACAO-RESILIENCIA-TRANSPORTE-V18.sql"
)
MIGRACAO_CONTRATO_UNICO_V19 = (
    RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3"
    / "MIGRACAO-CONTRATO-UNICO-V19.sql"
)
MIGRACAO_RECUPERACAO_RETOMADA_V20 = (
    RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3"
    / "MIGRACAO-RECUPERACAO-RETOMADA-INTEGRAL-V20.sql"
)
spec_preparador = importlib.util.spec_from_file_location("preparo_integral_otimizador", PREPARADOR)
preparo_mod = importlib.util.module_from_spec(spec_preparador)
assert spec_preparador.loader is not None
spec_preparador.loader.exec_module(preparo_mod)


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

    def status_fila_rapido(self):
        dados = self._fila()
        dados["linhas_carregando"] = True
        return dados

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
    def recuperar_reserva_orfa(self, confirmado): self._bloqueia()
    def parar_fila(self, confirmado): self._bloqueia()
    def abrir_console_fila(self): self._bloqueia()


class GatewayRotulosCanonicos:
    def rpc(self, nome, corpo=None):
        if nome == "otimizador_rotulos_fila_v1":
            return {"contrato": nome,
                    "funcoes": [{"funcao_id": 1, "rotulo": "Centroavante fixo"},
                                 {"funcao_id": 4, "rotulo": "Goleiro defensivo"}],
                    "posicoes": [{"posicao_id": 12, "rotulo": "Centroavante"},
                                  {"posicao_id": 0, "rotulo": "Goleiro"}]}
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
        if nome == "otimizador_rotulos_cartas_fila_v1":
            return {"contrato": "otimizador_rotulos_cartas_fila_v1", "itens": [
                {"card_id": card_id, "nome": "Welington Pauletto"}
                for card_id in corpo["p_card_ids"]
            ]}
        raise AssertionError(nome)


class GatewayStatusV6ComDefault:
    def __init__(self):
        self.chamadas = []

    def rpc(self, nome, corpo=None, ausente_ok=False, timeout_segundos=45):
        self.chamadas.append((nome, corpo, ausente_ok, timeout_segundos))
        if nome != "otimizador_producao_status_v6":
            raise AssertionError(nome)
        return {"contrato": "otimizador_fila_producao_v6", "lote_id": "lote-ativo"}


class GatewayStatusFalhaTransporte:
    def __init__(self):
        self.chamadas = []

    def rpc(self, nome, corpo=None, ausente_ok=False, timeout_segundos=45):
        self.chamadas.append((nome, corpo, ausente_ok, timeout_segundos))
        if nome == "otimizador_producao_status_v6":
            return {
                "contrato": "otimizador_fila_producao_v6",
                "lote_id": "lote-transporte", "tipo_lote": "integral",
                "estado": "falhou", "estado_lote": "falhou",
                "falha_lote": mod.FALHA_TRANSPORTE_RECUPERAVEL_V18,
                "pendentes": 8, "processando": 0, "pode_publicar": False,
                "acoes": {"retomar": False},
            }
        if nome == "otimizador_producao_status_v7":
            return {
                "contrato": "otimizador_fila_producao_v6",
                "lote_id": "lote-transporte", "tipo_lote": "integral",
                "estado": "falhou", "estado_lote": "falhou",
                "falha_lote": mod.FALHA_TRANSPORTE_RECUPERAVEL_V18,
                "pendentes": 8, "processando": 0, "pode_publicar": False,
                "acoes": {"retomar": True},
            }
        raise AssertionError(nome)


class GatewayPreparadorEsteiraRapido:
    def __init__(self):
        self.chamadas = []

    def rpc(self, nome, corpo=None):
        self.chamadas.append((nome, corpo))
        if nome != "otimizador_producao_status_v6":
            raise AssertionError(nome)
        return {
            "contrato": "otimizador_fila_producao_v6",
            "lote_id": "lote-ativo",
            "pode_publicar": False,
            "preparo": {"total": 19363, "concluido": 19350, "pendentes": 13},
        }


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
        for rota in ("/api/fila/status", "/api/fila/linhas", "/api/fila/eventos", "/api/resultados"):
            status, corpo = self.requisicao("GET", rota)
            self.assertEqual(status, 200)
            resposta = json.loads(corpo)
            self.assertFalse(resposta["disponivel"])
            self.assertEqual(resposta["estado"], "aguardando_aplicacao_fila_v5")
            self.assertIn("V5", resposta["mensagem"])
        for rota in ("/api/fila/criar", "/api/fila/iniciar", "/api/fila/pausar", "/api/fila/recuperar", "/api/fila/retomar", "/api/fila/console"):
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
            "otimizador_producao_status_v3", "otimizador_producao_status_v6",
            "otimizador_producao_status_v7",
            "otimizador_producao_controle_lote_v1",
            "otimizador_producao_fila_operacional_v1",
            "otimizador_producao_fila_operacional_v2",
            "otimizador_producao_fila_operacional_v3",
            "otimizador_producao_fila_operacional_v4",
            "otimizador_rotulos_fila_v1",
            "otimizador_producao_contexto_lote_v3",
            "otimizador_producao_controlar_lote_v3",
            "otimizador_producao_recuperar_reserva_orfa_v9",
            "otimizador_producao_recuperar_falha_retomada_integral_v1",
            "otimizador_producao_recuperar_falha_transporte_v1",
            "otimizador_producao_recuperar_falha_pre_reserva_v2",
            "otimizador_producao_reservar_linha_v3", "otimizador_producao_concluir_linha_v3",
            "otimizador_producao_bloquear_linha_v3", "otimizador_producao_falhar_lote_v3",
            "otimizador_producao_status_v5", "otimizador_producao_prevoo_integral_v5",
            "otimizador_producao_criar_lote_integral_v5", "otimizador_producao_preparar_fatia_v5",
            "otimizador_producao_controlar_preparo_v5", "otimizador_producao_fila_paginada_v5",
            "otimizador_producao_eventos_paginados_v5", "otimizador_rotulos_cartas_fila_v1",
            "otimizador_producao_iniciar_esteira_v6", "otimizador_producao_preparar_fatia_v6",
            "otimizador_producao_reservar_linha_v6", "otimizador_producao_concluir_linha_v6",
            "otimizador_producao_reservar_entrada_v7",
            "otimizador_producao_pacote_local_manifesto_v1",
            "otimizador_producao_pacote_local_cartas_v1",
            "otimizador_producao_pacote_local_linhas_v1",
            "otimizador_producao_pacote_local_manifesto_v2",
            "otimizador_producao_pacote_local_cartas_v2",
            "otimizador_producao_pacote_local_linhas_v2",
            "otimizador_producao_reservar_linha_local_v1",
            "otimizador_producao_concluir_lote_local_v1",
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

    def test_preparador_da_esteira_usa_status_v6_resumido(self):
        gateway = GatewayPreparadorEsteiraRapido()
        preparador = preparo_mod.PreparadorFilaIntegralV5(
            gateway, "lote-ativo", esteira=True,
        )
        status = preparador._status()
        self.assertEqual(status["preparo"]["pendentes"], 13)
        self.assertEqual(gateway.chamadas, [
            ("otimizador_producao_status_v6", {"p_lote_id": "lote-ativo"}),
        ])

    def test_inicio_confirma_sem_esperar_paginacao_e_atualiza_em_segundo_plano(self):
        confirmado = mod.ServicoOtimizador._inicio_esteira_confirmado("lote-ativo")
        self.assertTrue(confirmado["ok"])
        self.assertEqual(confirmado["estado_lote"], "rodando")
        self.assertFalse(confirmado["pode_publicar"])
        js = (SERVIDOR.parent / "app.js").read_text(encoding="utf-8")
        self.assertIn("window.setTimeout(()=>atualizarFila(),0);", js)

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
        servico._rotulos_fila = None
        servico._catalogos_apresentacao = None
        linhas = servico._linhas_com_rotulos([
            {"linha_id": 924, "card_id": "8538111", "funcao_id": 1, "posicao_id": 12,
             "impeto_condicional_codigo": 301, "impeto_condicional_nivel": 3,
             "builds_comparadas": 33830, "builds_possiveis": 357074384925258000},
            {"linha_id": 1116, "card_id": "8538147", "funcao_id": 4, "posicao_id": 0},
            {"linha_id": 999, "card_id": "8538111", "funcao_id": 99, "posicao_id": 98},
        ], detalhes=True)
        self.assertEqual(linhas[0]["carta_rotulo"], "Welington Pauletto")
        self.assertEqual(linhas[0]["funcao_rotulo"], "Centroavante fixo")
        self.assertEqual(linhas[0]["posicao_rotulo"], "Centroavante")
        self.assertEqual(linhas[1]["funcao_rotulo"], "Goleiro defensivo")
        self.assertEqual(linhas[1]["posicao_rotulo"], "Goleiro")
        self.assertEqual(linhas[2]["funcao_rotulo"], "Função sem catálogo")
        self.assertEqual(linhas[2]["posicao_rotulo"], "Posição sem catálogo")
        js = (SERVIDOR.parent / "app.js").read_text(encoding="utf-8")
        self.assertIn("aguardando_aplicacao_fila_v5", js)
        self.assertIn("Iniciar fila integral", js)
        self.assertIn("otimizador_producao_fila_operacional_v4", SERVIDOR.read_text(encoding="utf-8"))
        self.assertIn("otimizador_rotulos_fila_v1", SERVIDOR.read_text(encoding="utf-8"))
        self.assertIn("a.criar===true", js)
        self.assertIn("a.iniciar===true", js)
        self.assertIn("a.pausar!==true", js)
        self.assertIn("confirmarParar", js)
        interface = (SERVIDOR.parent / "index.html").read_text(encoding="utf-8")
        self.assertIn("Build campeã", interface)
        self.assertIn("<th>Tempo</th>", interface)
        self.assertIn("ESTEIRA V6 · SEM PUBLICAÇÃO", interface)
        self.assertIn("Mais recentes", interface)
        self.assertIn("Mais antigas", interface)
        self.assertNotIn('id="abrir-console"', interface)
        self.assertIn("pontuacao_final", js)
        self.assertIn("duracao_segundos", js)
        self.assertIn("Em processamento há", js)
        self.assertIn("Painel conectado", js)
        self.assertIn("atualizarSaudeLocal", js)
        self.assertNotIn("worker_resumo", js)
        self.assertIn("fechar esta janela só esconde o painel", js)
        self.assertIn("workerLocalAusente", js)
        self.assertIn("reassumir_worker_local", js)
        self.assertIn("Retomar worker local", js)
        self.assertIn("Reserva sem worker local", js)
        self.assertIn("window.setInterval(atualizarTemposEmProcessamento,1000)", js)
        self.assertIn("consulta_indisponivel", js)
        self.assertIn("atrasoConsultaIndisponivel", js)
        self.assertIn("falhasConsultaFila", js)
        self.assertIn("nova tentativa em", js)
        self.assertIn("proximas_primeiro_finais_por_ultimo", js)
        self.assertIn("function abaAtiva", js)
        self.assertIn("if(!abaAtiva('resultados')", js)
        self.assertIn("recuperar-fila", js)
        self.assertIn("confirmarRecuperar", js)
        self.assertIn("/api/fila/recuperar", SERVIDOR.read_text(encoding="utf-8"))
        self.assertIn("estado-local", interface)
        self.assertNotIn('id="linha-atual"', interface)
        self.assertNotIn('id="detalhes-lote"', interface)
        self.assertNotIn('id="eventos-fila"', interface)
        self.assertIn("Carta sem nome no catálogo", js)
        self.assertIn("Função sem catálogo", js)
        self.assertIn("Posição sem catálogo", js)
        css = (SERVIDOR.parent / "style.css").read_text(encoding="utf-8")
        self.assertIn("position: sticky", css)

    def test_recuperacao_orfa_exige_confirmacao_e_condicoes_locais(self):
        class Gateway:
            def __init__(self):
                self.chamadas = []

            def rpc(self, nome, corpo=None):
                self.chamadas.append((nome, corpo))
                return {"contrato": "otimizador_fila_producao_v5", "estado_lote": "pausado"}

        status = {
            "disponivel": True, "lote_id": "lote-recuperavel", "estado_lote": "encerrando",
            "corrente": [{"linha_id": 3389, "estado": "processando"}],
        }
        servico = object.__new__(mod.ServicoOtimizador)
        servico._worker_thread = None
        servico._preparo_thread = None
        servico.gateway = Gateway()
        servico._status_fila = lambda: status
        servico.painel_fila = lambda: {"estado_lote": "pausado"}
        self.assertTrue(servico._recuperacao_reserva_orfa_disponivel(status))
        with self.assertRaises(mod.ErroDaInterface):
            servico.recuperar_reserva_orfa(False)
        retorno = servico.recuperar_reserva_orfa(True)
        self.assertEqual(retorno["estado_lote"], "pausado")
        self.assertEqual(servico.gateway.chamadas, [(
            "otimizador_producao_recuperar_reserva_orfa_v9",
            {"p_lote_id": "lote-recuperavel", "p_linha_id": 3389, "p_confirmado": True},
        )])
        status["estado_lote"] = "rodando"
        self.assertFalse(servico._recuperacao_reserva_orfa_disponivel(status))

    def test_lote_rodando_sem_reserva_expoe_e_reassume_worker_local(self):
        status = {
            "disponivel": True, "lote_id": "lote-em-andamento", "tipo_lote": "integral",
            "estado_lote": "rodando", "pode_publicar": False,
            "pendentes": 184457, "processando": 0,
            "preparo": {"total": 19363, "concluido": 19350, "pendentes": 13},
        }
        chamadas = []
        servico = object.__new__(mod.ServicoOtimizador)
        servico._worker_lock = threading.RLock()
        servico._worker_thread = None
        servico._worker_lote_id = None
        servico._preparo_thread = None
        servico._preparo_lote_id = None
        servico._pacote_apos_preparo_lote_id = None
        servico._status_fila = lambda: status
        servico._iniciar_preparador_integral = (
            lambda lote_id, esteira=False: chamadas.append(("preparador", lote_id, esteira))
        )
        servico._iniciar_worker_producao = (
            lambda lote_id, esteira=False: chamadas.append(("worker", lote_id, esteira))
        )
        servico.painel_fila = lambda: {"ok": True, "estado_lote": "rodando"}

        self.assertTrue(servico._reassumir_esteira_local_disponivel(status))
        retorno = servico.iniciar_fila()
        self.assertTrue(retorno["ok"])
        self.assertEqual(chamadas, [
            ("preparador", "lote-em-andamento", True),
        ])

        status["processando"] = 1
        self.assertFalse(servico._reassumir_esteira_local_disponivel(status))
        with self.assertRaises(mod.ErroDaInterface) as erro:
            servico.iniciar_fila()
        self.assertEqual(erro.exception.status, 409)

    def test_retoma_integral_ja_preparada_com_worker_esteira_v7(self):
        class Gateway:
            def __init__(self):
                self.chamadas = []

            def rpc(self, nome, corpo=None):
                self.chamadas.append((nome, corpo))
                if nome != "otimizador_producao_controlar_lote_v3":
                    raise AssertionError(nome)
                return {"contrato": "otimizador_fila_producao_v3", "estado_lote": "rodando", "pode_publicar": False}

        status = {
            "disponivel": True, "lote_id": "lote-integral-pronto", "tipo_lote": "integral",
            "estado": "pausado", "estado_lote": "pausado", "pode_publicar": False,
            "pendentes": 12, "processando": 0,
            "preparo": {"total": 3, "concluido": 3, "pendentes": 0},
            "acoes": {"criar": False, "iniciar": False, "retomar": True},
        }
        chamadas = []
        servico = object.__new__(mod.ServicoOtimizador)
        servico._worker_lock = threading.RLock()
        servico._worker_thread = None
        servico._preparo_thread = None
        servico.gateway = Gateway()
        servico._status_fila = lambda: status
        servico._iniciar_preparador_integral = lambda lote_id, esteira=False: chamadas.append(
            ("preparador", lote_id, esteira)
        )
        servico._iniciar_worker_producao = lambda lote_id, esteira=False: chamadas.append(
            ("worker", lote_id, esteira)
        )
        servico._estado_pacote_local = lambda lote_id: (False, {})
        servico._abrir_pacote_local = lambda lote_id, validar=False: object()
        servico._invalidar_cache_status_fila = lambda: None

        # A retomada V52 só é válida quando a fotografia selada existe nesta
        # máquina. Criamos apenas a pasta de teste; a abertura do pacote e o
        # worker continuam substituídos para não tocar banco ou motor.
        raiz_original = mod.MOTOR_DIR
        with tempfile.TemporaryDirectory() as temporario:
            mod.MOTOR_DIR = Path(temporario)
            try:
                from fila_local_v1 import PacoteLocalV1
                PacoteLocalV1.pasta_do_lote(mod.MOTOR_DIR, "lote-integral-pronto").mkdir(parents=True)
                retorno = servico.iniciar_fila()
            finally:
                mod.MOTOR_DIR = raiz_original
        self.assertEqual(retorno["estado_lote"], "rodando")
        self.assertEqual(chamadas, [("worker", "lote-integral-pronto", True)])
        self.assertEqual(servico.gateway.chamadas, [(
            "otimizador_producao_controlar_lote_v3",
            {"p_lote_id": "lote-integral-pronto", "p_acao": "retomar", "p_confirmado": False},
        )])

    def test_recupera_somente_a_falha_v20_pos_preparo_sem_resultado(self):
        class Gateway:
            def __init__(self):
                self.chamadas = []

            def rpc(self, nome, corpo=None):
                self.chamadas.append((nome, corpo))
                if nome != "otimizador_producao_recuperar_falha_retomada_integral_v1":
                    raise AssertionError(nome)
                return {"contrato": "otimizador_fila_producao_v5", "estado_lote": "pausado"}

        status = {
            "disponivel": True, "lote_id": "lote-v20", "tipo_lote": "integral",
            "estado": "falhou", "estado_lote": "falhou", "pode_publicar": False,
            "falha_lote": mod.FALHA_RETOMADA_INTEGRAL_POS_PREPARO_V20,
            "pendentes": 8, "processando": 1,
            "preparo": {"total": 3, "concluido": 3, "pendentes": 0},
            "corrente": [{"linha_id": 3675, "estado": "processando"}],
        }
        servico = object.__new__(mod.ServicoOtimizador)
        servico._worker_thread = None
        servico._preparo_thread = None
        servico.gateway = Gateway()
        servico._status_fila = lambda: status
        servico.painel_fila = lambda: {"estado_lote": "pausado", "pode_publicar": False}

        self.assertTrue(servico._recuperacao_falha_retomada_integral_v20_disponivel(status))
        with self.assertRaises(mod.ErroDaInterface):
            servico.recuperar_reserva_orfa(False)
        retorno = servico.recuperar_reserva_orfa(True)
        self.assertEqual(retorno["estado_lote"], "pausado")
        self.assertEqual(servico.gateway.chamadas, [(
            "otimizador_producao_recuperar_falha_retomada_integral_v1",
            {"p_lote_id": "lote-v20", "p_linha_id": 3675, "p_confirmado": True},
        )])

    def test_migracao_v20_e_cirurgica_e_nao_muda_formula_ou_publicacao(self):
        texto = MIGRACAO_RECUPERACAO_RETOMADA_V20.read_text(encoding="utf-8").lower()
        self.assertEqual(texto.count("begin;"), 1)
        self.assertEqual(texto.count("commit;"), 1)
        self.assertIn("otimizador_producao_recuperar_falha_retomada_integral_v1", texto)
        self.assertIn("contrato recusou a consulta (400)", texto)
        self.assertIn("formula_alterada', false", texto)
        self.assertIn("pode_publicar', false", texto)
        self.assertIn("l.build_otimizador_id is null", texto)
        self.assertIn("revoke all", texto)
        self.assertIn("to service_role", texto)
        self.assertNotIn("delete from", texto)
        self.assertNotIn("clube.build", texto)
        self.assertNotIn("clube.fila", texto)

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

    def test_status_v6_envia_null_para_o_default_do_contrato(self):
        servico = object.__new__(mod.ServicoOtimizador)
        gateway = GatewayStatusV6ComDefault()
        servico.gateway = gateway
        status = servico._status_fila()
        self.assertTrue(status["disponivel"])
        self.assertEqual(gateway.chamadas, [
            ("otimizador_producao_status_v6", {"p_lote_id": None}, True, 5),
        ])

    def test_falha_de_transporte_pre_reserva_so_usa_v7_com_selo_exato(self):
        servico = object.__new__(mod.ServicoOtimizador)
        gateway = GatewayStatusFalhaTransporte()
        servico.gateway = gateway
        status = servico._status_fila()
        self.assertTrue(status["acoes"]["retomar"])
        self.assertTrue(mod.ServicoOtimizador._recuperacao_falha_transporte_disponivel(status))
        self.assertEqual([x[0] for x in gateway.chamadas], [
            "otimizador_producao_status_v6", "otimizador_producao_status_v7",
        ])

    def test_retoma_falha_de_transporte_so_pelo_contrato_v18(self):
        class Gateway:
            def __init__(self):
                self.chamadas = []

            def rpc(self, nome, corpo=None):
                self.chamadas.append((nome, corpo))
                self.assertEqual(nome, "otimizador_producao_recuperar_falha_transporte_v1")
                return {
                    "contrato": "otimizador_fila_producao_v6",
                    "estado_lote": "rodando", "pode_publicar": False,
                }

            def assertEqual(self, atual, esperado):
                if atual != esperado:
                    raise AssertionError((atual, esperado))

        status = {
            "disponivel": True, "lote_id": "lote-transporte", "tipo_lote": "integral",
            "estado": "falhou", "estado_lote": "falhou",
            "falha_lote": mod.FALHA_TRANSPORTE_RECUPERAVEL_V18,
            "pendentes": 8, "processando": 0, "pode_publicar": False,
            "acoes": {"criar": False, "retomar": True},
        }
        servico = object.__new__(mod.ServicoOtimizador)
        servico.gateway = Gateway()
        servico._status_fila = lambda: status
        chamadas = []
        servico._iniciar_preparador_integral = lambda lote_id, esteira=False: chamadas.append(
            ("preparador", lote_id, esteira)
        )
        servico._iniciar_worker_producao = lambda lote_id, esteira=False: chamadas.append(
            ("worker", lote_id, esteira)
        )
        servico._retomar_worker_do_pacote = lambda lote_id: {
            "ok": True, "lote_id": lote_id, "estado_lote": "rodando", "pode_publicar": False,
        }
        retorno = servico.iniciar_fila()
        self.assertEqual(retorno["estado_lote"], "rodando")
        self.assertEqual(chamadas, [
        ])
        self.assertEqual(servico.gateway.chamadas, [(
            "otimizador_producao_recuperar_falha_transporte_v1",
            {"p_lote_id": "lote-transporte"},
        )])

    def test_recupera_a_falha_pre_reserva_v19_somente_pelo_contrato_exato(self):
        class Gateway:
            def __init__(self):
                self.chamadas = []

            def rpc(self, nome, corpo=None):
                self.chamadas.append((nome, corpo))
                if nome != "otimizador_producao_recuperar_falha_pre_reserva_v2":
                    raise AssertionError(nome)
                return {
                    "contrato": "otimizador_fila_producao_v6",
                    "estado_lote": "rodando", "pode_publicar": False,
                }

        status = {
            "disponivel": True, "lote_id": "lote-v19", "tipo_lote": "integral",
            "estado": "falhou", "estado_lote": "falhou",
            "falha_lote": mod.FALHA_PRE_RESERVA_RECUPERAVEL_V19,
            "pendentes": 8, "processando": 0, "pode_publicar": False,
            "acoes": {"criar": False, "iniciar": False},
        }
        servico = object.__new__(mod.ServicoOtimizador)
        servico.gateway = Gateway()
        servico._status_fila = lambda: status
        chamadas = []
        servico._iniciar_preparador_integral = lambda lote_id, esteira=False: chamadas.append(
            ("preparador", lote_id, esteira)
        )
        servico._iniciar_worker_producao = lambda lote_id, esteira=False: chamadas.append(
            ("worker", lote_id, esteira)
        )
        servico._retomar_worker_do_pacote = lambda lote_id: {
            "ok": True, "lote_id": lote_id, "estado_lote": "rodando", "pode_publicar": False,
        }
        self.assertTrue(servico._recuperacao_falha_pre_reserva_v19_disponivel(status))
        servico._oferecer_recuperacao_pre_reserva_v19(status)
        self.assertTrue(status["acoes"]["iniciar"])
        retorno = servico.iniciar_fila()
        self.assertEqual(retorno["estado_lote"], "rodando")
        self.assertEqual(chamadas, [
        ])
        self.assertEqual(servico.gateway.chamadas, [(
            "otimizador_producao_recuperar_falha_pre_reserva_v2", {"p_lote_id": "lote-v19"},
        )])

    def test_migracao_v18_nao_muda_formula_nem_publica_e_tem_porta_fechada(self):
        texto = MIGRACAO_TRANSPORTE_V18.read_text(encoding="utf-8").lower()
        self.assertIn("otimizador_producao_recuperar_falha_transporte_v1", texto)
        self.assertIn("otimizador_producao_status_v7", texto)
        self.assertIn("otimizador_portal_local_v5", texto)
        self.assertIn("formula_alterada', false", texto)
        self.assertIn("pode_publicar', false", texto)
        self.assertIn("revoke all", texto)
        self.assertIn("to service_role", texto)
        self.assertNotIn("delete from", texto)
        self.assertNotIn("clube.build", texto)

    def test_status_rapido_nao_le_pagina_nem_rotulos(self):
        class Gateway:
            def __init__(self):
                self.chamadas = []

            def rpc(self, nome, corpo=None, ausente_ok=False, timeout_segundos=45):
                self.chamadas.append(nome)
                if nome != "otimizador_producao_status_v6":
                    raise AssertionError(nome)
                return {
                    "contrato": "otimizador_fila_producao_v6",
                    "lote_id": "lote-rapido", "estado": "rodando",
                    "acoes": {"iniciar": False, "retomar": False, "pausar": True, "parar": True},
                    "confirmacao": {"parar_exige_confirmacao": True},
                    "corrente": [], "cards": 10, "linhas": 99,
                    "pendentes": 90, "processando": 0, "concluidas": 9,
                    "bloqueadas": 0, "interrompidas": 0, "falhas": 0,
                    "pode_publicar": False,
                }

        servico = object.__new__(mod.ServicoOtimizador)
        gateway = Gateway()
        servico.gateway = gateway
        servico._recuperacao_reserva_orfa_disponivel = lambda _: False
        servico._recuperacao_falha_retomada_integral_v20_disponivel = lambda _: False
        servico._reassumir_esteira_local_disponivel = lambda _: False
        painel = servico.status_fila_rapido()
        self.assertTrue(painel["disponivel"])
        self.assertTrue(painel["linhas_carregando"])
        self.assertEqual(painel["itens"], [])
        self.assertEqual(painel["paginacao"]["total"], 99)
        self.assertEqual(gateway.chamadas, ["otimizador_producao_status_v6"])

    def test_indisponibilidade_do_banco_mantem_painel_honesto_e_fail_closed(self):
        class GatewayIndisponivel:
            def __init__(self):
                self.chamadas = 0

            def rpc(self, *_, **__):
                self.chamadas += 1
                raise mod.ErroDaInterface("banco em recuperação", 503)

        servico = object.__new__(mod.ServicoOtimizador)
        gateway = GatewayIndisponivel()
        servico.gateway = gateway
        painel = servico.painel_fila(offset=0, limite=100)
        self.assertTrue(painel["ok"])
        self.assertFalse(painel["disponivel"])
        self.assertFalse(painel["conexao_banco"])
        self.assertEqual(painel["estado"], "banco_indisponivel")
        self.assertEqual(painel["itens"], [])
        self.assertFalse(any(painel["acoes"].values()))
        self.assertIn("tentará novamente sozinha", painel["mensagem"])
        # A repetição imediata da mesma tela não abre outra chamada externa:
        # o circuito local responde fail-closed durante a reconexão.
        segundo = servico.painel_fila(offset=0, limite=100)
        self.assertEqual(gateway.chamadas, 1)
        self.assertEqual(segundo["estado"], "banco_indisponivel")

    def test_interface_inicia_a_fila_sem_esperar_catalogos(self):
        fonte = (RAIZ / "2-MOTORES" / "OTIMIZADOR" / "interface" / "app.js").read_text(encoding="utf-8")
        self.assertIn("async function carregarCatalogos()", fonte)
        # A fila operacional não pode disputar o mesmo gateway com o catálogo
        # completo de técnicos/régua. O catálogo só é lido ao abrir a aba
        # Individual; a primeira página da fila precisa renderizar sozinha.
        self.assertIn("async function carregar(){await atualizarSaudeLocal();atualizarFila();", fonte)
        self.assertIn("if(x.dataset.aba==='individual')carregarCatalogos();", fonte)
        self.assertNotIn("atualizarFila();carregarCatalogos();", fonte)
        self.assertIn("s.conexao_banco===false", fonte)
        self.assertIn("banco_indisponivel", fonte)
        self.assertIn("/api/fila/status", fonte)
        self.assertIn("/api/fila/linhas?offset=", fonte)
        self.assertIn("window.setTimeout(carregarDetalhesFila,0)", fonte)
        self.assertIn("Carregando linhas da fila em segundo plano", fonte)

    def test_paginacao_operacional_mostra_proximas_primeiro_sem_mudar_a_ordem_canonica(self):
        class Gateway:
            def __init__(self):
                self.chamadas = []
                self.abertas = [
                    {"linha_id": indice, "ordem_fila": indice, "card_id": str(indice),
                     "funcao_id": 1, "posicao_id": 12, "estado": "pendente"}
                    for indice in range(1, 3)
                ]
                self.finais = [
                    {"linha_id": indice, "ordem_fila": indice, "card_id": str(indice),
                     "funcao_id": 1, "posicao_id": 12, "estado": "concluido"}
                    for indice in range(3, 6)
                ]

            def rpc(self, nome, corpo=None):
                self.chamadas.append((nome, corpo))
                if nome != "otimizador_producao_fila_operacional_v4":
                    raise AssertionError(nome)
                inicio = corpo["p_offset"]
                fim = inicio + corpo["p_limite"]
                itens = self.abertas if corpo["p_grupo"] == "abertas" else self.finais
                return {
                    "contrato": "otimizador_fila_producao_v7",
                    "fonte": "clube_novo.otimizador_entrada_linha_v1", "total": len(itens),
                    "offset": inicio, "limite": corpo["p_limite"],
                    "itens": itens[inicio:fim],
                }

        status = {
            "disponivel": True, "lote_id": "lote-visual", "estado": "rodando",
            "acoes": {}, "confirmacao": {}, "corrente": [], "linhas": 5,
            "pendentes": 2, "processando": 0,
            "concluidas": 3, "bloqueadas": 0, "interrompidas": 0, "falhas": 0,
        }
        servico = object.__new__(mod.ServicoOtimizador)
        servico.gateway = Gateway()
        servico._status_fila = lambda: status
        servico._recuperacao_reserva_orfa_disponivel = lambda _: False
        servico._linhas_com_rotulos = lambda itens, detalhes=False: itens

        primeira = servico.painel_fila(offset=0, limite=2)
        self.assertEqual([x["linha_id"] for x in primeira["itens"]], [1, 2])
        self.assertEqual(primeira["paginacao"], {
            "total": 5, "offset": 0, "limite": 2, "somente_finais": False,
            "ordem": "proximas_primeiro_finais_por_ultimo",
            "abertas": 2, "finais": 3,
        })
        segunda = servico.painel_fila(offset=2, limite=2)
        self.assertEqual([x["linha_id"] for x in segunda["itens"]], [3, 4])
        ultima = servico.painel_fila(offset=4, limite=2)
        self.assertEqual([x["linha_id"] for x in ultima["itens"]], [5])
        resultados = servico.resultados_fila(offset=0, limite=2)
        self.assertEqual([x["linha_id"] for x in resultados["itens"]], [5, 4])

        chamadas = servico.gateway.chamadas
        self.assertEqual([x[1]["p_offset"] for x in chamadas], [0, 0, 2, 1])
        self.assertEqual([x[1]["p_grupo"] for x in chamadas], ["abertas", "finais", "finais", "finais"])

    def test_saude_local_nao_dependa_de_regua_ou_fila(self):
        servico = object.__new__(mod.ServicoOtimizador)
        saude = servico.saude()
        self.assertTrue(saude["ok"])
        self.assertEqual(saude["contrato"], "controle_local_loopback_v1")
        self.assertIsNone(saude["pode_rodar"])
        self.assertFalse(saude["worker_ativo"])
        self.assertFalse(saude["preparador_ativo"])
        self.assertIn("servidor local ativo", saude["worker_resumo"].lower())

    def test_saude_local_reflete_a_linha_ativa_do_worker_sem_banco(self):
        class ThreadAtiva:
            @staticmethod
            def is_alive():
                return True

        class WorkerFalso:
            lote_id = "lote-local"

        servico = object.__new__(mod.ServicoOtimizador)
        servico._worker_lock = threading.RLock()
        servico._worker_lote_id = "lote-local"
        servico._worker_thread = ThreadAtiva()
        servico._preparo_thread = None
        servico._worker_estado = mod.ServicoOtimizador._estado_local("iniciando", "lote-local")
        servico._preparo_estado = mod.ServicoOtimizador._estado_local("aguardando")
        servico._progresso_worker(WorkerFalso(), "calculando", {
            "linha_id": 3389, "card_id": "52781926899717", "funcao_id": 1, "posicao_id": 12,
        })
        saude = servico.saude()
        self.assertTrue(saude["worker_ativo"])
        self.assertEqual(saude["worker"]["linha_id"], 3389)
        self.assertEqual(saude["worker"]["card_id"], "52781926899717")
        self.assertEqual(saude["worker"]["etapa"], "calculando")
        self.assertIn("linha 3389", saude["worker_resumo"])
        self.assertIsInstance(saude["worker_decorrido_segundos"], int)

    def test_executavel_portatil_mantem_o_estado_local_da_interface_v52(self):
        raiz_motor = SERVIDOR.parent.parent
        launcher = (raiz_motor / "windows-app" / "ClubEfootballOtimizadorLauncher.cs").read_text(encoding="utf-8")
        compilador = (raiz_motor / "windows-app" / "COMPILAR-APLICATIVO.ps1").read_text(encoding="utf-8")
        compilador_servico = (raiz_motor / "windows-app" / "COMPILAR-SERVICO-PORTATIL.ps1").read_text(encoding="utf-8")
        bootstrap = (raiz_motor / "servico_portatil.py").read_text(encoding="utf-8")
        atalho = (raiz_motor / "RODAR-OTIMIZADOR.bat").read_text(encoding="utf-8")
        self.assertIn('ExpectedApp = "\\\"aplicativo\\\": \\"otimizador_clubefootball\\\""', launcher)
        self.assertIn('MinimumInterfaceVersion = "20260901-v52"', launcher)
        self.assertIn('AssemblyFileVersion("1.8.2.0")', launcher)
        self.assertIn('Local\\ClubEfootballOtimizadorLauncherV54', launcher)
        self.assertIn('SupportedInterfaceVersion(ReadJsonString(status, "versao_interface"))', launcher)
        self.assertIn("OtimizadorServico.exe", launcher)
        self.assertIn("CLUBEF_OTIMIZADOR_ROOT", launcher)
        self.assertNotIn("FindPythonW", launcher)
        self.assertIn("8769", launcher)
        self.assertIn("NotifyIcon", launcher)
        self.assertIn("TrayController", launcher)
        self.assertIn("LauncherMutex", launcher)
        self.assertIn("PortaInternaOcupada", launcher)
        self.assertIn("request.Timeout = 1500", launcher)
        self.assertIn("Icon.ExtractAssociatedIcon", launcher)
        self.assertIn("CanReplaceIdlePreviousService", launcher)
        self.assertIn("StopPreviousIdleService()", launcher)
        self.assertIn("startup.Dispose();", launcher)
        self.assertLess(launcher.index("startup.Dispose();"), launcher.index("Application.Run(controller);"))
        self.assertIn('GetProcessesByName("Otimizador ClubEfootball")', launcher)
        self.assertIn("WaitForServer(75, startup)", launcher)
        self.assertIn("EnsureConfiguration(root)", launcher)
        self.assertIn("Configurar conexão do Otimizador", launcher)
        self.assertIn("File.WriteAllText(target", launcher)
        self.assertIn("StartupNotice", launcher)
        self.assertIn("Abrindo o Otimizador", launcher)
        self.assertIn('"runtime", "_internal"', launcher)
        self.assertIn('"base_library.zip"', launcher)
        self.assertIn("Uri.TryCreate(connectionUrl", launcher)
        self.assertIn("Fechar a janela não interrompe a fila", launcher)
        self.assertIn("precisaCompilar", compilador)
        self.assertIn("System.Drawing.dll", compilador)
        self.assertIn("COMPILAR-SERVICO-PORTATIL.ps1", compilador)
        self.assertIn("PyInstaller", compilador_servico)
        self.assertIn("--onedir", compilador_servico)
        self.assertIn("--collect-all psycopg", compilador_servico)
        self.assertIn("--collect-all psycopg_binary", compilador_servico)
        self.assertNotIn("--onefile", compilador_servico)
        self.assertIn("CLUBEF_OTIMIZADOR_ROOT", bootstrap)
        self.assertIn("CLUBEF_OTIMIZADOR_PACOTE_LOCAL_OBRIGATORIO", bootstrap)
        self.assertIn("Path.cwd()", bootstrap)
        self.assertIn('"interface" / "servidor.py"', bootstrap)
        self.assertIn("Otimizador ClubEfootball.exe", atalho)
        self.assertNotIn("COMPILAR-APLICATIVO.ps1", atalho)
        gitignore = (RAIZ / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("!2-MOTORES/OTIMIZADOR/runtime/_internal/base_library.zip", gitignore)

    def test_ponte_privada_v17_e_fechada_por_allowlist(self):
        pasta = RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3"
        migracao = (pasta / "MIGRACAO-PONTE-LOCAL-PRIVADA-V13.sql").read_text(encoding="utf-8")
        rollback = (pasta / "ROLLBACK-PONTE-LOCAL-PRIVADA-V13.sql").read_text(encoding="utf-8")
        painel_rapido = (pasta / "MIGRACAO-PAINEL-RAPIDO-V16.sql").read_text(encoding="utf-8")
        rollback_painel = (pasta / "ROLLBACK-PAINEL-RAPIDO-V16.sql").read_text(encoding="utf-8")
        rotulos_cartas = (pasta / "MIGRACAO-ROTULOS-CARTAS-RAPIDOS-V17.sql").read_text(encoding="utf-8")
        rollback_rotulos = (pasta / "ROLLBACK-ROTULOS-CARTAS-RAPIDOS-V17.sql").read_text(encoding="utf-8")
        servidor = SERVIDOR.read_text(encoding="utf-8")
        self.assertIn("security definer", migracao.lower())
        self.assertIn("otimizador_portal_local_v1", migracao)
        self.assertIn("revoke all", migracao.lower())
        self.assertIn("grant execute", migracao.lower())
        self.assertIn("bonificador_runtime", migracao)
        self.assertNotIn("clube.build", migracao)
        self.assertNotIn("clube.fila", migracao)
        self.assertIn("drop function if exists public.otimizador_portal_local_v1", rollback)
        self.assertIn("_rpc_privado", servidor)
        self.assertIn("otimizador_portal_local_v4", servidor)
        self.assertIn("otimizador_portal_local_v6", servidor)
        self.assertIn("otimizador_producao_fila_operacional_v3", painel_rapido)
        self.assertIn("otimizador_rotulos_fila_v1", painel_rapido)
        self.assertIn("revoke all", painel_rapido.lower())
        self.assertIn("drop function if exists public.otimizador_portal_local_v3", rollback_painel)
        self.assertIn("otimizador_rotulos_cartas_fila_v1", rotulos_cartas)
        self.assertIn("clube_novo.carta_jogo", rotulos_cartas)
        self.assertIn("security definer", rotulos_cartas.lower())
        self.assertIn("set search_path to ''", rotulos_cartas.lower())
        self.assertIn("revoke all", rotulos_cartas.lower())
        self.assertIn("grant execute", rotulos_cartas.lower())
        self.assertNotIn("clube.build", rotulos_cartas)
        self.assertNotIn("clube.fila", rotulos_cartas)
        self.assertIn("drop function if exists public.otimizador_portal_local_v4", rollback_rotulos)
        self.assertIn("otimizador_rotulos_cartas_fila_v1", servidor)
        self.assertNotIn('self.gateway.rpc("otimizador_cartas_apresentacao_v2"', servidor)
        self.assertNotIn("execute_sql", servidor)

    def test_status_rapido_v10_mantem_contratos_e_tem_rollback(self):
        pasta = RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3"
        migracao = (pasta / "MIGRACAO-STATUS-RAPIDO-V10.sql").read_text(encoding="utf-8")
        rollback = (pasta / "ROLLBACK-STATUS-RAPIDO-V10.sql").read_text(encoding="utf-8")
        for texto in (migracao, rollback):
            self.assertEqual(texto.lower().count("begin;"), 1)
            self.assertEqual(texto.lower().count("commit;"), 1)
            self.assertIn("otimizador_producao_status_v5", texto)
            self.assertIn("otimizador_producao_status_v3", texto)
            self.assertIn("pode_publicar", texto)
            self.assertNotIn("otimizador_producao_reservar_linha", texto)
            self.assertNotIn("otimizador_producao_concluir_linha", texto)
        self.assertIn("where l.lote_producao_id=v_lote.id", migracao)
        self.assertIn("v_cards:=v_lote.cards", migracao)
        self.assertIn("build_linha_card_lote_producao_v5_idx", migracao)
        self.assertIn("count(distinct q.card_id)", rollback)

    def test_leitura_operacional_v12_so_busca_detalhes_da_pagina_e_tem_rollback(self):
        pasta = RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3"
        migracao = (pasta / "MIGRACAO-LEITURA-PAGINA-RAPIDA-V12.sql").read_text(encoding="utf-8")
        rollback = (pasta / "ROLLBACK-LEITURA-PAGINA-RAPIDA-V12.sql").read_text(encoding="utf-8")
        for texto in (migracao, rollback):
            self.assertEqual(texto.lower().count("begin;"), 1)
            self.assertEqual(texto.lower().count("commit;"), 1)
        self.assertIn("otimizador_producao_fila_operacional_v2", migracao)
        self.assertIn("join lateral", migracao.lower())
        self.assertIn("offset p_offset limit p_limite", migracao.lower())
        self.assertIn("otimizador_lote_producao_status_v1", migracao)
        self.assertNotIn("otimizador_producao_reservar_linha", migracao)
        self.assertNotIn("otimizador_producao_concluir_linha", migracao)
        self.assertIn("drop function if exists public.otimizador_producao_fila_operacional_v2", rollback)

    def test_resultados_v14_nao_varrem_as_pendencias(self):
        pasta = RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3"
        migracao = (pasta / "MIGRACAO-RESULTADOS-PAGINADOS-RAPIDOS-V14.sql").read_text(encoding="utf-8")
        rollback = (pasta / "ROLLBACK-RESULTADOS-PAGINADOS-RAPIDOS-V14.sql").read_text(encoding="utf-8")
        servidor = SERVIDOR.read_text(encoding="utf-8")
        self.assertEqual(migracao.lower().count("begin;"), 1)
        self.assertEqual(migracao.lower().count("commit;"), 1)
        self.assertIn("otimizador_producao_fila_operacional_v3", migracao)
        self.assertIn("from clube_novo.build_linha_card l", migracao)
        self.assertIn("l.lote_producao_id = p_lote_id", migracao)
        self.assertIn("otimizador_portal_local_v2", migracao)
        self.assertIn("drop function if exists public.otimizador_producao_fila_operacional_v3", rollback)
        self.assertIn("otimizador_producao_fila_operacional_v4", servidor)

    def test_contrato_unico_v19_mantem_tela_e_worker_na_mesma_view_privada(self):
        texto = MIGRACAO_CONTRATO_UNICO_V19.read_text(encoding="utf-8").lower()
        servidor = SERVIDOR.read_text(encoding="utf-8")
        self.assertIn("clube_novo.otimizador_entrada_linha_v1", texto)
        self.assertIn("security_invoker = true", texto)
        self.assertIn("otimizador_producao_reservar_entrada_v7", texto)
        self.assertIn("otimizador_producao_fila_operacional_v4", texto)
        self.assertIn("otimizador_producao_recuperar_falha_pre_reserva_v2", texto)
        self.assertIn("otimizador_producao_fila_operacional_v4", servidor)
        self.assertIn("Data API com chave de serviço é o caminho padrão", servidor)
        self.assertNotIn("clube.build", texto)
        self.assertNotIn("clube.fila", texto)

    def test_painel_nao_esconde_falha_da_lista_ou_resultados_e_invalida_js_antigo(self):
        app = APP.read_text(encoding="utf-8")
        index = INDEX.read_text(encoding="utf-8")
        self.assertIn("AbortController", app)
        self.assertIn("Não foi possível carregar a lista da fila:", app)
        self.assertIn("Não foi possível atualizar Resultados:", app)
        self.assertIn("let linhasFilaCarregando=false", app)
        self.assertIn("window.setInterval(atualizarTemposEmProcessamento,1000)", app)
        self.assertNotIn("}catch(_){\n    // O usuário continua vendo o estado real", app)
        self.assertIn('/app.js?v=20260901-v48', index)


if __name__ == "__main__":
    unittest.main(verbosity=2)
