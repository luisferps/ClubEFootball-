# -*- coding: utf-8 -*-
"""Interface local do Otimizador: leitura/simulação em 127.0.0.1 somente."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
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
RPC_PERMITIDAS = {"otimizador_regua_v1", "otimizador_carta_v1"}


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
    """A única saída do processo local: duas RPCs v1 de leitura."""

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
    """Usa exatamente o cálculo aprovado, recebendo IDs do contrato v1."""

    def __init__(self, gateway=None):
        if str(MOTOR_DIR) not in sys.path:
            sys.path.insert(0, str(MOTOR_DIR))
        import fonte_unica as fonte
        import equacao as equacao
        import motor as motor
        self.gateway = gateway or GatewayOtimizador()
        self.fonte, self.equacao, self.motor = fonte, equacao, motor

    def regua(self):
        pacote = self.gateway.rpc("otimizador_regua_v1") or {}
        if pacote.get("contrato") != "otimizador_regua_v1":
            raise ErroDaInterface("versão inesperada do contrato da régua", 503)
        return pacote

    @staticmethod
    def funcoes(regua):
        return sorted([
            {"funcao_id": int(x["funcao_id"]),
             "nome": x.get("rotulo_apresentacao") or "Sem rótulo"}
            for x in regua.get("funcoes") or []
        ], key=lambda x: (x["nome"], x["funcao_id"]))

    @staticmethod
    def tecnicos(regua):
        itens = []
        for x in regua.get("tecnicos") or []:
            if x.get("tecnico_id") is None or not (x.get("boosts") or []):
                continue
            itens.append({
                "tecnico_id": int(x["tecnico_id"]),
                "nome": x.get("nome_apresentacao") or "Sem nome",
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

    @staticmethod
    def _carta_apresentacao(bruto):
        ap, esc = bruto.get("apresentacao") or {}, bruto.get("escalares") or {}
        return {
            "card_id": bruto.get("card_id"), "nome": ap.get("nome"),
            "posicao": ap.get("posicao"), "overall": esc.get("overall"),
            "orcamento": esc.get("orcamento"), "atributos": bruto.get("atributos") or [],
            "habilidades": bruto.get("habilidades") or [], "dimensoes": bruto.get("dimensoes") or {},
            "cardinalidades": bruto.get("cardinalidades") or {},
        }

    def simular(self, card_id, funcao_id, tecnico_id):
        if not CARD_ID_VALIDO.fullmatch(card_id):
            raise ErroDaInterface("card_id inválido")
        regua = self.regua()
        funcoes = {x["funcao_id"]: x for x in self.funcoes(regua)}
        catalogo_ui = {x["tecnico_id"]: x for x in self.tecnicos(regua)}
        if funcao_id not in funcoes:
            raise ErroDaInterface("função canônica não disponível")
        if tecnico_id not in catalogo_ui:
            raise ErroDaInterface("técnico canônico não disponível")

        bruto = self.gateway.rpc("otimizador_carta_v1", {"p_card_id": card_id}) or {}
        carta = self.fonte._traduz(bruto)
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
            {"nome": "Ímpetos condicionais", "ok": True, "detalhe": "desligados deliberadamente"},
        ]
        comum = {
            "modo": "simulação local segura — sem lote e sem escrita",
            "carta": self._carta_apresentacao(bruto), "funcao": funcoes[funcao_id],
            "tecnico": catalogo_ui[tecnico_id], "gates": gates,
            "regua": {"contrato": regua.get("contrato"), "versao_molde": regua.get("versao_molde"),
                      "cardinalidades": bruto.get("cardinalidades") or {}},
            "proveniencia": "navegador -> servidor local -> RPCs otimizador_*_v1 -> cálculo Python aprovado",
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
                "gasto": gasto,
            },
        }

    def validar(self, card_id, funcao_id, tecnico_id):
        simulacao = self.simular(card_id, funcao_id, tecnico_id)
        if not simulacao.get("ok"):
            return {"ok": False, "simulacao": simulacao, "paridade": None}
        bruto = self.gateway.rpc("otimizador_carta_v1", {"p_card_id": card_id}) or {}
        entrada = self.fonte._traduz(bruto)
        tec = self._tecnico_motor(self.fonte.carrega_tecnicos_do_banco(), tecnico_id)
        r = simulacao["resultado"]
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

    def saude(self):
        regua = self.regua()
        return {
            "ok": True, "contrato": regua.get("contrato"),
            "pode_rodar": bool((regua.get("gate") or {}).get("pode_rodar")),
            "modo": "somente leitura",
            "bloqueios": ["lote", "escrita", "Ímpetos condicionais", "acesso direto ao schema"],
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
            self.send_header("Content-Length", str(len(corpo))); self.end_headers(); self.wfile.write(corpo)

        def do_POST(self):
            self.responder_json(HTTPStatus.METHOD_NOT_ALLOWED, {"ok": False, "erro": "interface somente leitura"})

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
                if caminho.path in {"/api/simular", "/api/validar"}:
                    card = (params.get("card_id") or [""])[0]
                    funcao = int((params.get("funcao_id") or [""])[0])
                    tecnico = int((params.get("tecnico_id") or [""])[0])
                    dados = servico.validar(card, funcao, tecnico) if caminho.path.endswith("validar") else servico.simular(card, funcao, tecnico)
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
