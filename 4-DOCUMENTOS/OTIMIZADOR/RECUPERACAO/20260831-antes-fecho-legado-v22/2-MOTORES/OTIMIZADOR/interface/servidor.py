# -*- coding: utf-8 -*-
"""Painel local do Otimizador, restrito a 127.0.0.1 e contratos selados."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PASTA = Path(__file__).resolve().parent
MOTOR_DIR = PASTA.parent
CONFIG = MOTOR_DIR.parent / "config.txt"
CARD_ID_VALIDO = re.compile(r"^[A-Za-z0-9@_-]{1,64}$")
APLICATIVO_ID = "otimizador_clubefootball"
INTERFACE_VERSAO = "20260831-v21"
RPC_PERMITIDAS = {
    "otimizador_regua_v2", "otimizador_carta_v3",
    "otimizador_catalogos_apresentacao_v1", "otimizador_carta_apresentacao_v1",
    "otimizador_status_teste_v2", "otimizador_fila_teste_v2",
    "otimizador_eventos_teste_v2", "otimizador_controlar_lote_teste_v2",
}


class ErroDaInterface(Exception):
    def __init__(self, mensagem: str, status: int = 400):
        super().__init__(mensagem)
        self.status = status


def ler_config() -> tuple[str, str]:
    valores = {}
    if not CONFIG.is_file():
        raise ErroDaInterface("configuração compartilhada não encontrada", 503)
    for linha in CONFIG.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            chave, valor = linha.split("=", 1)
            valores[chave.strip()] = valor.strip()
    url, chave = valores.get("SUPABASE_URL", "").rstrip("/"), valores.get("SUPABASE_KEY", "")
    if not url or not chave or "COLE_AQUI" in chave:
        raise ErroDaInterface("configuração local do Otimizador está incompleta", 503)
    return url, chave


class GatewayOtimizador:
    """A única saída do processo local: contratos permitidos e selados."""

    def __init__(self):
        self.url, self.chave = ler_config()

    def rpc(self, nome: str, corpo: dict | None = None):
        if nome not in RPC_PERMITIDAS:
            raise ErroDaInterface("contrato não permitido nesta interface", 403)
        pedido = urllib.request.Request(
            f"{self.url}/rest/v1/rpc/{nome}",
            data=json.dumps(corpo or {}).encode("utf-8"),
            headers={"apikey": self.chave, "Authorization": "Bearer " + self.chave,
                     "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(pedido, timeout=45) as resposta:
                texto = resposta.read().decode("utf-8")
        except urllib.error.HTTPError as erro:
            raise ErroDaInterface(f"contrato recusou a consulta ({erro.code})", 503) from erro
        except Exception as erro:
            raise ErroDaInterface(f"não foi possível consultar o contrato ({type(erro).__name__})", 503) from erro
        return json.loads(texto) if texto.strip() else None


class ServicoOtimizador:
    """Usa o cálculo aprovado; motor por IDs e apresentação em porta separada."""

    def __init__(self, gateway=None):
        if str(MOTOR_DIR) not in sys.path:
            sys.path.insert(0, str(MOTOR_DIR))
        import fonte_unica as fonte
        import equacao as equacao
        import motor as motor
        import fila_comparacao_legado_50 as fila_teste
        self.gateway = gateway or GatewayOtimizador()
        self.fonte, self.equacao, self.motor = fonte, equacao, motor
        self.fila_teste = fila_teste
        self._trava_worker = threading.Lock()
        self._worker = None
        self._console = None
        self._erro_worker = None
        self._nomes_cartas = {}
        self._funcoes_por_id = {}
        self._posicoes_por_id = {}
        self._tecnicos_por_id = {}
        self._habilidades_por_id = {}
        self._impetos_por_id = {}
        self._catalogos_apresentacao = None

    def regua(self):
        pacote = self.gateway.rpc("otimizador_regua_v2") or {}
        if pacote.get("contrato") != "otimizador_regua_v2":
            raise ErroDaInterface("versão inesperada do contrato da régua", 503)
        return pacote

    def catalogos_apresentacao(self):
        if self._catalogos_apresentacao is None:
            pacote = self.gateway.rpc("otimizador_catalogos_apresentacao_v1") or {}
            if pacote.get("contrato") != "otimizador_catalogos_apresentacao_v1":
                raise ErroDaInterface("catálogo de apresentação indisponível", 503)
            self._catalogos_apresentacao = pacote
        return self._catalogos_apresentacao

    def funcoes(self, regua):
        nomes = {int(x["funcao_id"]): x.get("rotulo")
                 for x in self.catalogos_apresentacao().get("funcoes") or []}
        return sorted([
            {"funcao_id": int(x["funcao_id"]),
             "nome": nomes.get(int(x["funcao_id"])) or "Sem rótulo"}
            for x in regua.get("funcoes") or []
        ], key=lambda x: (x["nome"], x["funcao_id"]))

    def tecnicos(self, regua):
        nomes = {int(x["tecnico_id"]): x.get("rotulo")
                 for x in self.catalogos_apresentacao().get("tecnicos") or []}
        itens = []
        for x in regua.get("tecnicos") or []:
            if x.get("tecnico_id") is None or not (x.get("boosts") or []):
                continue
            itens.append({
                "tecnico_id": int(x["tecnico_id"]),
                "nome": nomes.get(int(x["tecnico_id"])) or "Sem nome",
                "proficiencia": x.get("proficiencia_maxima"),
                "boosts": [{"indice_otimizador": int(b["indice_otimizador"]),
                            "delta": b.get("delta")} for b in x.get("boosts") or []],
            })
        return sorted(itens, key=lambda x: (x["nome"], x["tecnico_id"]))

    @staticmethod
    def _molde(regua, funcao_id):
        return sorted([
            {"attr": int(x["indice_otimizador"]), "peso": x["peso"], "alvo": x["alvo"]}
            for x in regua.get("molde") or [] if int(x["funcao_id"]) == funcao_id
        ], key=lambda x: x["attr"])

    @staticmethod
    def _tecnico_motor(tecnicos, tecnico_id):
        return next((x for x in tecnicos if int(x.get("id")) == tecnico_id), None)

    def _carta_apresentacao(self, bruto, apresentacao):
        esc = bruto.get("escalares") or {}
        posicoes = {int(x["posicao_id"]): x.get("rotulo")
                    for x in self.catalogos_apresentacao().get("posicoes") or []}
        posicao_id = bruto.get("posicao_principal_id")
        return {
            "card_id": bruto.get("card_id"), "nome": apresentacao.get("nome"),
            "posicao": posicoes.get(int(posicao_id)) if posicao_id is not None else None,
            "overall": esc.get("overall"),
            "orcamento": esc.get("orcamento"), "atributos": bruto.get("atributos") or [],
            "habilidades": bruto.get("habilidades") or [], "dimensoes": bruto.get("dimensoes") or {},
            "cardinalidades": bruto.get("cardinalidades") or {},
        }

    @staticmethod
    def _identidade_impeto(bruto, nivel_impeto):
        condicionais = [x for x in bruto.get("impetos") or []
                        if x.get("codigo_impeto") is not None and x.get("condicional")]
        if len(condicionais) > 1:
            raise ErroDaInterface("a carta possui mais de um ímpeto condicional", 409)
        if not condicionais:
            if nivel_impeto is not None:
                raise ErroDaInterface("esta carta não possui ímpeto condicional")
            return None, None
        codigo = int(condicionais[0]["codigo_impeto"])
        maximo = int(condicionais[0].get("nivel_maximo") or 0)
        if nivel_impeto is None:
            raise ErroDaInterface(f"informe o nível do ímpeto {codigo} (1 a {maximo})")
        nivel = int(nivel_impeto)
        if not 1 <= nivel <= maximo:
            raise ErroDaInterface(f"nível do ímpeto fora da faixa 1 a {maximo}")
        return codigo, nivel

    def simular(self, card_id, funcao_id, tecnico_id, nivel_impeto=None):
        if not CARD_ID_VALIDO.fullmatch(card_id):
            raise ErroDaInterface("card_id inválido")
        regua = self.regua()
        funcoes = {x["funcao_id"]: x for x in self.funcoes(regua)}
        catalogo_ui = {x["tecnico_id"]: x for x in self.tecnicos(regua)}
        if funcao_id not in funcoes:
            raise ErroDaInterface("função canônica não disponível")
        if tecnico_id not in catalogo_ui:
            raise ErroDaInterface("técnico canônico não disponível")

        bruto = self.gateway.rpc("otimizador_carta_v3", {"p_card_id": card_id}) or {}
        apresentacao = self.gateway.rpc("otimizador_carta_apresentacao_v1", {"p_card_id": card_id}) or {}
        codigo_impeto, nivel_impeto = self._identidade_impeto(bruto, nivel_impeto)
        carta = self.fonte.aplica_impetos_da_linha(
            self.fonte._traduz(bruto),codigo_impeto,nivel_impeto)
        molde = self._molde(regua, funcao_id)
        tec = self._tecnico_motor(self.fonte.carrega_tecnicos_do_banco(), tecnico_id)
        gate_regua, gate_carta = regua.get("gate") or {}, bruto.get("gate") or {}
        falhas = []
        if not gate_regua.get("pode_rodar"):
            falhas.extend(gate_regua.get("motivos") or ["régua bloqueada"])
        if not gate_carta.get("pode_rodar"):
            falhas.extend(gate_carta.get("motivos") or ["carta bloqueada"])
        if not carta: falhas.append("carta ausente")
        if not molde: falhas.append("molde ausente para funcao_id")
        if not tec: falhas.append("técnico sem boost válido")
        gates = [
            {"nome": "régua canônica", "ok": bool(gate_regua.get("pode_rodar")), "detalhe": gate_regua.get("motivos") or []},
            {"nome": "carta e relações", "ok": bool(gate_carta.get("pode_rodar")), "detalhe": gate_carta.get("motivos") or []},
            {"nome": "molde por funcao_id", "ok": bool(molde), "detalhe": {"funcao_id": funcao_id, "linhas": len(molde)}},
            {"nome": "técnico por tecnico_id", "ok": tec is not None, "detalhe": {"tecnico_id": tecnico_id}},
            {"nome": "Ímpeto condicional por ID", "ok": True,
             "detalhe": {"codigo_impeto": codigo_impeto, "nivel": nivel_impeto}},
        ]
        comum = {
            "modo": "simulação local segura — sem lote e sem escrita",
            "carta": self._carta_apresentacao(bruto, apresentacao), "funcao": funcoes[funcao_id],
            "tecnico": catalogo_ui[tecnico_id], "gates": gates,
            "regua": {"contrato": regua.get("contrato"), "versao_molde": regua.get("versao_molde"),
                      "cardinalidades": bruto.get("cardinalidades") or {}},
            "proveniencia": "navegador -> apresentação separada -> IDs do contrato V3 -> cálculo aprovado",
        }
        if falhas:
            return {**comum, "ok": False, "resultado": None, "falhas": list(dict.fromkeys(falhas))}

        entrada = dict(carta)
        entrada["arows"] = [[x["attr"], x["peso"], x["alvo"], 0, 0, 0] for x in molde]
        entrada["raras"] = entrada.get("raras") or []
        resultado = self.motor.build_completo2(entrada, [tec], None)
        if not resultado:
            raise ErroDaInterface("o Otimizador não retornou uma avaliação", 503)
        valores = resultado.get("vals_tela") or resultado.get("vals") or []
        gasto = self.motor.Card(entrada, m=tec["m"]).gasto(resultado.get("lvl") or {})
        return {
            **comum, "ok": True,
            "tecnico": {**catalogo_ui[tecnico_id], "multiplicador": tec.get("m")},
            "resultado": {
                "nota": resultado.get("nota"), "barras": resultado.get("lvl"),
                "atributos_em_campo": valores, "boost_indices": resultado.get("boost") or [],
                # Vetores exatos usados pelo motor; o validador não os reconstrói por rótulo.
                "impeto_add_vetor": resultado.get("impeto_add") or [0] * 26,
                "boost_add_vetor": resultado.get("boost_add") or [0] * 26,
                "habilidades": resultado.get("habilidades") or [],
                "impetos_fabricados": resultado.get("fab") or [], "sobra": resultado.get("sobra"),
                "impeto_condicional_codigo": codigo_impeto,
                "impeto_condicional_nivel": nivel_impeto,
                "gasto": gasto, "builds_comparadas": resultado.get("builds_comparadas"),
            },
        }

    def validar(self, card_id, funcao_id, tecnico_id, nivel_impeto=None):
        simulacao = self.simular(card_id, funcao_id, tecnico_id, nivel_impeto)
        if not simulacao.get("ok"):
            return {"ok": False, "simulacao": simulacao, "paridade": None}
        bruto = self.gateway.rpc("otimizador_carta_v3", {"p_card_id": card_id}) or {}
        r = simulacao["resultado"]
        entrada = self.fonte.aplica_impetos_da_linha(
            self.fonte._traduz(bruto),r.get("impeto_condicional_codigo"),r.get("impeto_condicional_nivel"))
        tec = self._tecnico_motor(self.fonte.carrega_tecnicos_do_banco(), tecnico_id)
        esperado = self.equacao.cadeia(
            entrada["base"], r["barras"], tec["m"],
            r["impeto_add_vetor"], r["boost_add_vetor"],
        )
        atual = r["atributos_em_campo"]
        igual = esperado == atual
        return {
            "ok": igual, "simulacao": simulacao,
            "paridade": {
                "ok": igual, "tipo": "equação legível versus cálculo inline do Otimizador",
                "vetor_esperado_sha256": hashlib.sha256(json.dumps(esperado).encode()).hexdigest(),
                "vetor_calculado_sha256": hashlib.sha256(json.dumps(atual).encode()).hexdigest(),
                "cardinalidades": bruto.get("cardinalidades") or {},
                "renomear_texto_nao_muda_calculo": True,
            },
        }

    def _estado_local_do_lote(self):
        estado = self.fila_teste.le_estado() or {}
        if not estado.get("lote_id"):
            raise ErroDaInterface("lote de teste selado local não foi preparado", 503)
        if not estado.get("fingerprint"):
            raise ErroDaInterface("fingerprint local do lote de teste ausente", 503)
        return estado

    def _status_fila(self):
        local = self._estado_local_do_lote()
        lote_id = local["lote_id"]
        status = self.gateway.rpc("otimizador_status_teste_v2", {"p_lote_id": lote_id}) or {}
        estados = {"parado", "rodando", "pausando", "pausado", "encerrando", "encerrado", "concluido", "falhou"}
        if status.get("contrato") != "otimizador_teste_lote_v14":
            raise ErroDaInterface("versão inesperada do contrato da fila", 503)
        if status.get("lote_id") != lote_id or status.get("fingerprint") != local["fingerprint"]:
            raise ErroDaInterface("selo do lote devolvido pelo contrato não confere", 503)
        if status.get("modo") != "teste_nao_publicado" or status.get("pode_publicar") is not False:
            raise ErroDaInterface("contrato recusado: lote não está estritamente em modo de teste", 503)
        if int(status.get("cards") or 0) < 1 or int(status.get("linhas") or 0) < 1:
            raise ErroDaInterface("contrato recusado: rodada ativa não possui cartas e linhas", 503)
        if status.get("estado_lote") not in estados or status.get("estado") not in estados:
            raise ErroDaInterface("contrato recusado: estado de lote inválido", 503)
        if not isinstance(status.get("acoes"), dict) or not isinstance(status.get("confirmacao"), dict):
            raise ErroDaInterface("contrato recusado: selos de ação ausentes", 503)
        # Defesa de apresentação para contratos antigos que deixaram o lote como
        # "rodando" depois que a última linha já havia terminado. A migração V15
        # persiste a mesma transição; esta normalização impede que uma janela já
        # aberta continue oferecendo Pausar ou mantendo uma linha antiga na tela.
        sem_trabalho = (int(status.get("pendentes") or 0) == 0
                        and int(status.get("processando") or 0) == 0)
        if sem_trabalho and status.get("estado_lote") in {"rodando", "pausando", "pausado"}:
            status = dict(status)
            status["estado"] = "concluido"
            status["estado_lote"] = "concluido"
            status["corrente"] = []
            acoes = dict(status["acoes"])
            for acao in ("iniciar", "pausar", "parar", "retomar"):
                acoes[acao] = False
            status["acoes"] = acoes
        return status

    @staticmethod
    def _totais_fila(status):
        return {
            "cartas_selecionadas": status.get("cards", 0), "linhas_geradas": status.get("linhas", 0),
            "pendentes": status.get("pendentes", 0), "em_processamento": status.get("processando", 0),
            "concluidas": status.get("concluidas", 0), "bloqueadas": status.get("bloqueadas", 0),
            "interrompidas": status.get("interrompidas", 0),
            "falhas": status.get("falhas", 0),
        }

    def _linhas_com_rotulos(self, itens):
        if not self._funcoes_por_id:
            regua = self.regua()
            catalogos = self.catalogos_apresentacao()
            self._funcoes_por_id = {
                int(funcao["funcao_id"]): funcao["nome"]
                for funcao in self.funcoes(regua)
            }
            self._tecnicos_por_id = {
                int(tecnico["tecnico_id"]): tecnico["nome"]
                for tecnico in self.tecnicos(regua)
            }
            self._posicoes_por_id = {int(x["posicao_id"]): x.get("rotulo")
                                     for x in catalogos.get("posicoes") or []}
            self._habilidades_por_id = {int(x["skill_id"]): x.get("rotulo")
                                        for x in catalogos.get("habilidades") or []}
            self._impetos_por_id = {int(x["codigo_impeto"]): x.get("rotulo")
                                    for x in catalogos.get("impetos") or []}
        faltantes = sorted({str(x.get("card_id")) for x in itens if x.get("card_id") is not None} - set(self._nomes_cartas))
        for card_id in faltantes:
            bruto = self.gateway.rpc("otimizador_carta_apresentacao_v1", {"p_card_id": card_id}) or {}
            self._nomes_cartas[card_id] = bruto.get("nome") or None
        saida = []
        for linha in itens:
            item = dict(linha)
            card_id = str(item.get("card_id") or "")
            funcao_id = item.get("funcao_id")
            posicao_id = item.get("posicao_id")
            item["carta_rotulo"] = f"{card_id} · {self._nomes_cartas.get(card_id) or 'Nome não informado'}"
            item["funcao_rotulo"] = self._funcoes_por_id.get(
                int(funcao_id) if funcao_id is not None else None,
                f"ID {funcao_id} · catálogo ausente",
            )
            item["posicao_rotulo"] = self._posicoes_por_id.get(
                int(posicao_id) if posicao_id is not None else None,
                f"ID {posicao_id} · catálogo ausente",
            )
            codigo_impeto = item.get("impeto_condicional_codigo")
            nivel_impeto = item.get("impeto_condicional_nivel")
            if codigo_impeto is not None:
                nome_impeto = self._impetos_por_id.get(
                    int(codigo_impeto), f"ID {codigo_impeto} · catálogo ausente")
                item["impeto_condicional_rotulo"] = f"{nome_impeto} · nível {nivel_impeto}"
            else:
                item["impeto_condicional_rotulo"] = "Sem ímpeto condicional"
            tecnico_id = item.get("tecnico_id")
            if tecnico_id is not None:
                item["tecnico_rotulo"] = self._tecnicos_por_id.get(
                    int(tecnico_id), f"ID {tecnico_id} · catálogo ausente"
                )
            item["habilidades_adicionais_rotulo"] = [
                self._habilidades_por_id.get(int(skill_id), f"ID {skill_id} · catálogo ausente")
                for skill_id in item.get("habilidades_adicionais") or []
            ]
            # A fila entrega a saída real do worker. A interface só renomeia estes
            # campos de apresentação; nunca recalcula nota ou duração.
            if item.get("pontuacao_final") is None and item.get("b1") is not None:
                item["pontuacao_final"] = item["b1"]
            if item.get("duracao_segundos") is None and item.get("segundos") is not None:
                item["duracao_segundos"] = item["segundos"]
            # Estes contadores podem ultrapassar o limite de inteiros exatos do
            # JavaScript. A tela recebe texto para abreviar sem arredondar o valor
            # completo que fica disponível no detalhe/tooltip.
            for campo_contador in ("builds_comparadas", "builds_possiveis"):
                if item.get(campo_contador) is not None:
                    item[campo_contador] = str(item[campo_contador])
            if not item.get("resultado_resumo") and item.get("estado") == "concluido":
                partes = []
                if item.get("pontuacao_final") is not None:
                    partes.append(f"pontuação {item['pontuacao_final']}")
                if item.get("barras") is not None:
                    partes.append(f"barras {item['barras']}")
                if item.get("tecnico_rotulo") is not None:
                    partes.append(f"técnico {item['tecnico_rotulo']}")
                if partes:
                    item["resultado_resumo"] = "Build calculada · " + " · ".join(partes)
            saida.append(item)
        return saida

    def painel_fila(self):
        status = self._status_fila()
        lote_id = status["lote_id"]
        itens = self._linhas_com_rotulos(self.gateway.rpc("otimizador_fila_teste_v2", {"p_lote_id": lote_id}) or [])
        corrente = status.get("corrente") or []
        if corrente:
            por_linha = {str(item.get("linha_id")): item for item in itens}
            linha_atual = dict(por_linha.get(str(corrente[0].get("linha_id"))) or self._linhas_com_rotulos(corrente)[0])
            linha_atual.update(corrente[0])
        else:
            linha_atual = None
        return {
            **status, "ok": True, "disponivel": True, "execucao": {"estado": status["estado_lote"]},
            "totais": self._totais_fila(status), "linha_atual": linha_atual,
            "itens": itens, "origem": "contratos V2 da fila selada, via servidor local",
            "publicacao": "TESTE / NÃO PUBLICADO",
        }

    def eventos_fila(self):
        status = self._status_fila()
        lote_id = status["lote_id"]
        eventos = self.gateway.rpc("otimizador_eventos_teste_v2", {"p_lote_id": lote_id}) or []
        return {"ok": True, "disponivel": True, "lote_id": lote_id,
                "estado": status["estado_lote"], "itens": eventos,
                "origem": "eventos reais do contrato de teste"}

    def resultados_fila(self):
        status = self._status_fila()
        lote_id = status["lote_id"]
        itens = self._linhas_com_rotulos(self.gateway.rpc("otimizador_fila_teste_v2", {"p_lote_id": lote_id}) or [])
        finais = [x for x in itens if x.get("estado") in {"concluido", "bloqueado", "interrompido", "falhou"}]
        return {"ok": True, "disponivel": True, "lote_id": lote_id,
                "estado": status["estado_lote"], "mensagem": "Resultados reais do lote de teste selado.",
                "itens": finais, "publicacao": "TESTE / NÃO PUBLICADO"}

    def _acao_de_inicio(self, status):
        acoes = status["acoes"]
        if acoes.get("iniciar") is True:
            return "iniciar"
        if acoes.get("retomar") is True:
            return "retomar"
        raise ErroDaInterface("o selo do contrato não autoriza iniciar nem retomar este lote", 409)

    def _worker_ativo(self):
        return bool(self._worker and self._worker.is_alive())

    def _rodar_worker_selado(self):
        try:
            self.fila_teste.executar_lote_selado()
        except Exception as erro:
            self._erro_worker = type(erro).__name__

    def _iniciar_worker_selado(self):
        with self._trava_worker:
            if self._worker_ativo():
                return
            self._erro_worker = None
            self._worker = threading.Thread(target=self._rodar_worker_selado, name="otimizador-fila-teste", daemon=True)
            self._worker.start()

    def iniciar_fila(self):
        status = self._status_fila()
        acao = self._acao_de_inicio(status)
        lote_id = self._estado_local_do_lote()["lote_id"]
        self.gateway.rpc("otimizador_controlar_lote_teste_v2", {"p_lote_id": lote_id, "p_acao": acao, "p_confirmado": False})
        self._iniciar_worker_selado()
        return self.painel_fila()

    def pausar_fila(self):
        status = self._status_fila()
        if status["acoes"].get("pausar") is not True:
            raise ErroDaInterface("o selo do contrato não autoriza pausar este lote", 409)
        lote_id = self._estado_local_do_lote()["lote_id"]
        self.gateway.rpc("otimizador_controlar_lote_teste_v2", {"p_lote_id": lote_id, "p_acao": "pausar", "p_confirmado": False})
        return self.painel_fila()

    def parar_fila(self, confirmado):
        status = self._status_fila()
        if status["acoes"].get("parar") is not True:
            raise ErroDaInterface("o selo do contrato não autoriza encerrar este lote", 409)
        if status["confirmacao"].get("parar_exige_confirmacao") is not True or confirmado is not True:
            raise ErroDaInterface("encerramento exige confirmação explícita nesta interface", 409)
        lote_id = self._estado_local_do_lote()["lote_id"]
        self.gateway.rpc("otimizador_controlar_lote_teste_v2", {"p_lote_id": lote_id, "p_acao": "parar", "p_confirmado": True})
        return self.painel_fila()

    def abrir_console_fila(self):
        status = self._status_fila()
        if status["acoes"].get("console") is not True:
            raise ErroDaInterface("o selo do contrato não autoriza abrir o console", 409)
        with self._trava_worker:
            if self._worker_ativo() or (self._console and self._console.poll() is None):
                raise ErroDaInterface("já existe um worker de teste ativo para este lote", 409)
            acao = self._acao_de_inicio(status)
            lote_id = self._estado_local_do_lote()["lote_id"]
            self.gateway.rpc("otimizador_controlar_lote_teste_v2", {"p_lote_id": lote_id, "p_acao": acao, "p_confirmado": False})
            self._console = subprocess.Popen(
                ["cmd.exe", "/k", f'"{sys.executable}" "{MOTOR_DIR / "fila_comparacao_legado_50.py"}" executar-selado'],
                cwd=str(MOTOR_DIR),
            )
        return self.painel_fila()

    def saude(self):
        regua = self.regua()
        return {
            "ok": True, "aplicativo": APLICATIVO_ID,
            "versao_interface": INTERFACE_VERSAO,
            "contrato": regua.get("contrato"),
            "pode_rodar": bool((regua.get("gate") or {}).get("pode_rodar")),
            "modo": "painel_da_rodada_ativa",
            "acesso": "somente contratos selados",
        }


def criar_servidor(servico=None, porta=8767):
    servico = servico or ServicoOtimizador()

    class Manipulador(BaseHTTPRequestHandler):
        def log_message(self, formato, *args): return

        def responder_json(self, status, dados):
            corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers(); self.wfile.write(corpo)

        def arquivo(self, nome, tipo):
            arquivo = PASTA / nome
            if not arquivo.is_file():
                return self.responder_json(404, {"ok": False, "erro": "arquivo local ausente"})
            corpo = arquivo.read_bytes()
            self.send_response(200); self.send_header("Content-Type", tipo)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(corpo))); self.end_headers(); self.wfile.write(corpo)

        def do_POST(self):
            caminho = urllib.parse.urlparse(self.path)
            try:
                tamanho = int(self.headers.get("Content-Length") or "0")
                bruto = self.rfile.read(tamanho) if tamanho else b""
                corpo = json.loads(bruto.decode("utf-8")) if bruto else {}
                if not isinstance(corpo, dict):
                    raise ErroDaInterface("corpo local inválido")
                if caminho.path == "/api/fila/criar":
                    raise ErroDaInterface("a amostra já está selada; criar outra fila não é permitido nesta interface", 409)
                if caminho.path == "/api/fila/iniciar":
                    return self.responder_json(200, servico.iniciar_fila())
                if caminho.path == "/api/fila/pausar":
                    return self.responder_json(200, servico.pausar_fila())
                if caminho.path == "/api/fila/parar":
                    return self.responder_json(200, servico.parar_fila(corpo.get("confirmado") is True))
                if caminho.path == "/api/fila/console":
                    return self.responder_json(200, servico.abrir_console_fila())
                if caminho.path == "/api/fila/retomar":
                    return self.responder_json(200, servico.iniciar_fila())
                self.responder_json(HTTPStatus.METHOD_NOT_ALLOWED, {"ok": False, "erro": "rota local não permitida"})
            except ErroDaInterface as erro:
                self.responder_json(erro.status, {"ok": False, "erro": str(erro)})
            except Exception:
                self.responder_json(500, {"ok": False, "erro": "falha local ao controlar a fila"})

        def do_GET(self):
            caminho = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(caminho.query)
            try:
                if caminho.path == "/": return self.arquivo("index.html", "text/html; charset=utf-8")
                if caminho.path == "/app.js": return self.arquivo("app.js", "text/javascript; charset=utf-8")
                if caminho.path == "/style.css": return self.arquivo("style.css", "text/css; charset=utf-8")
                if caminho.path == "/api/saude": return self.responder_json(200, servico.saude())
                if caminho.path == "/api/catalogos":
                    regua = servico.regua()
                    return self.responder_json(200, {"ok": True, "funcoes": servico.funcoes(regua), "tecnicos": servico.tecnicos(regua)})
                if caminho.path == "/api/fila/status":
                    return self.responder_json(200, servico.painel_fila())
                if caminho.path == "/api/fila/eventos":
                    return self.responder_json(200, servico.eventos_fila())
                if caminho.path == "/api/resultados":
                    return self.responder_json(200, servico.resultados_fila())
                if caminho.path in {"/api/simular", "/api/validar"}:
                    card = (params.get("card_id") or [""])[0]
                    funcao = int((params.get("funcao_id") or [""])[0])
                    tecnico = int((params.get("tecnico_id") or [""])[0])
                    nivel_texto = (params.get("impeto_nivel") or [""])[0]
                    nivel_impeto = int(nivel_texto) if nivel_texto else None
                    dados = (servico.validar(card, funcao, tecnico, nivel_impeto)
                             if caminho.path.endswith("validar")
                             else servico.simular(card, funcao, tecnico, nivel_impeto))
                    return self.responder_json(200, dados)
                return self.responder_json(404, {"ok": False, "erro": "rota local não encontrada"})
            except (TypeError, ValueError):
                return self.responder_json(400, {"ok": False, "erro": "IDs canônicos inválidos"})
            except ErroDaInterface as erro:
                return self.responder_json(erro.status, {"ok": False, "erro": str(erro)})
            except Exception:
                return self.responder_json(500, {"ok": False, "erro": "falha local ao montar a resposta"})

    return ThreadingHTTPServer(("127.0.0.1", porta), Manipulador)


if __name__ == "__main__":
    porta = int(os.environ.get("CLUBEF_OTIMIZADOR_PORT") or "8767")
    print(f"Interface do Otimizador: http://127.0.0.1:{porta}")
    criar_servidor(porta=porta).serve_forever()
