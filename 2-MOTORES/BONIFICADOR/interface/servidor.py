# -*- coding: utf-8 -*-
"""Interface local, somente leitura, do Bonificador.

O navegador fala apenas com este servidor em 127.0.0.1. A credencial fica no
config.txt compartilhado dos motores e só este processo chama os contratos v1.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


PASTA = Path(__file__).resolve().parent
MOTOR = PASTA.parent / "motor_bonus.py"
CARD_ID_VALIDO = re.compile(r"^[A-Za-z0-9@_-]{1,64}$")
FUNCOES_PURAS = {
    "nota_da_medida",
    "bonus_do_corpo",
    "bonus_do_pe_ruim",
    "_por_id",
    "bonus_do_estilo",
    "bonus_do_estilo_ia",
}


class ErroDaInterface(Exception):
    def __init__(self, mensagem: str, status: int = 400):
        super().__init__(mensagem)
        self.status = status


def achar_raiz() -> Path:
    for pasta in (PASTA, *PASTA.parents):
        if (pasta / "2-MOTORES" / "config.txt").is_file():
            return pasta
    raise ErroDaInterface("configuração compartilhada não encontrada", 503)


def ler_config() -> tuple[str, str]:
    config = achar_raiz() / "2-MOTORES" / "config.txt"
    valores: dict[str, str] = {}
    for linha in config.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            chave, valor = linha.split("=", 1)
            valores[chave.strip()] = valor.strip()
    url = valores.get("SUPABASE_URL", "").rstrip("/")
    chave = valores.get("SUPABASE_KEY", "")
    if not url or not chave or "COLE_AQUI" in chave:
        raise ErroDaInterface("configuração local do Bonificador está incompleta", 503)
    return url, chave


def carregar_funcoes_puras() -> dict[str, object]:
    texto = MOTOR.read_text(encoding="utf-8")
    arvore = ast.parse(texto, filename=str(MOTOR))
    nos = [
        no for no in arvore.body
        if isinstance(no, ast.FunctionDef) and no.name in FUNCOES_PURAS
    ]
    encontrados = {no.name for no in nos}
    if encontrados != FUNCOES_PURAS:
        raise RuntimeError("motor do Bonificador não contém as funções aprovadas")
    modulo = ast.Module(body=nos, type_ignores=[])
    ast.fix_missing_locations(modulo)
    escopo: dict[str, object] = {}
    exec(compile(modulo, str(MOTOR), "exec"), escopo)
    return escopo


class GatewayBonificador:
    """Fronteira única para RPCs; não expõe schema ou credencial ao navegador."""

    def __init__(self):
        self.url, self.chave = ler_config()

    def rpc(self, nome: str, corpo: dict | None = None):
        if nome not in {
            "bonificador_regua_v1",
            "bonificador_carta_v1",
        }:
            raise ErroDaInterface("contrato não permitido", 403)
        pedido = urllib.request.Request(
            f"{self.url}/rest/v1/rpc/{nome}",
            data=json.dumps(corpo or {}).encode("utf-8"),
            headers={
                "apikey": self.chave,
                "Authorization": "Bearer " + self.chave,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(pedido, timeout=30) as resposta:
                texto = resposta.read().decode("utf-8")
        except urllib.error.HTTPError as erro:
            raise ErroDaInterface(f"contrato recusou a consulta ({erro.code})", 503) from erro
        except Exception as erro:
            raise ErroDaInterface(
                f"não foi possível consultar o contrato ({type(erro).__name__})", 503
            ) from erro
        return json.loads(texto) if texto.strip() else None


class ServicoBonificador:
    def __init__(self, gateway: GatewayBonificador | None = None):
        self.gateway = gateway or GatewayBonificador()
        self.funcoes = carregar_funcoes_puras()

    def regua(self) -> dict:
        regua = self.gateway.rpc("bonificador_regua_v1") or {}
        if regua.get("contrato") != "bonificador-regua-v1":
            raise ErroDaInterface("versão inesperada da régua", 503)
        return regua

    @staticmethod
    def catalogo_funcoes(regua: dict) -> list[dict]:
        itens = []
        for codigo, dado in (regua.get("funcao_molde") or {}).items():
            if dado.get("pode_rodar"):
                itens.append({
                    "id": int(dado["id"]), "codigo": codigo, "nome": dado.get("rotulo") or codigo,
                })
        return sorted(itens, key=lambda x: (x["nome"], x["id"]))

    @staticmethod
    def _preparar_regua(regua: dict) -> dict:
        copia = copy.deepcopy(regua)
        ordem = copia.get("corpo_ordem") or {}
        indice = {
            (dado or {}).get("nosso"): int(pos)
            for pos, dado in ordem.items()
            if (dado or {}).get("nosso") is not None
        }
        for molde in (copia.get("molde_corpo") or {}).values():
            for medida, regra in molde.items():
                regra["idx"] = indice.get(medida, regra.get("idx"))
        return copia

    @staticmethod
    def _por_id(mapa: dict, chave):
        if chave is None or not isinstance(mapa, dict):
            return None
        return mapa.get(str(chave), mapa.get(chave))

    def simular(self, card_id: str, funcao_id: int) -> dict:
        if not CARD_ID_VALIDO.fullmatch(card_id):
            raise ErroDaInterface("card_id inválido")
        regua_original = self.regua()
        funcoes = {item["id"]: item for item in self.catalogo_funcoes(regua_original)}
        if funcao_id not in funcoes:
            raise ErroDaInterface("função não disponível na régua")
        carta = self.gateway.rpc("bonificador_carta_v1", {"p_card_id": card_id}) or {}
        regua = self._preparar_regua(regua_original)

        falhas = list(regua.get("falta_o_que") or []) + list(carta.get("falta_o_que") or [])
        apta = bool(regua.get("pode_rodar")) and bool(carta.get("pode_rodar"))
        par = regua.get("parametro") or {}
        corpo = self.funcoes["bonus_do_corpo"](
            regua.get("molde_corpo"), carta.get("corpo"), funcao_id,
            float(par.get("bonus_corpo_max") or 1.5),
        ) if apta else None
        pe = self.funcoes["bonus_do_pe_ruim"](
            par, carta.get("pe_ruim_uso"), carta.get("pe_ruim_precisao"),
        ) if apta else None
        estilo = self.funcoes["bonus_do_estilo"](
            regua, carta.get("slot1_id_jogo"), carta.get("slot2_id_jogo"),
            funcao_id, carta.get("posicao_id"),
        ) if apta else None
        ia = self.funcoes["bonus_do_estilo_ia"](
            par, carta.get("estilos_ia"),
        ) if apta else None
        componentes = {"corpo": corpo[0] if corpo else None, "pe_ruim": pe, "estilo": estilo, "ia": ia}
        faltantes = [nome for nome, valor in componentes.items() if not isinstance(valor, (int, float))]
        falhas = list(dict.fromkeys([*falhas, *faltantes]))
        total = round(sum(componentes.values()), 4) if not falhas else None

        posicao = carta.get("posicao_id")
        slot_manda = self._por_id(regua.get("posicao_slot") or {}, posicao) or "ofensivo"
        dono, outro = (
            (carta.get("slot1_id_jogo"), carta.get("slot2_id_jogo"))
            if slot_manda == "ofensivo"
            else (carta.get("slot2_id_jogo"), carta.get("slot1_id_jogo"))
        )
        if not dono:
            dono, outro = outro, None
        casa = self._por_id(self._por_id(regua.get("casa") or {}, dono) or {}, posicao)
        liga = self._por_id(regua.get("liga") or {}, outro) or []
        molde = self._por_id(regua.get("molde_corpo") or {}, funcao_id) or {}

        gates = [
            {"nome": "régua canônica", "ok": bool(regua.get("pode_rodar")), "detalhe": regua.get("falta_o_que") or []},
            {"nome": "carta e relações", "ok": bool(carta.get("pode_rodar")), "detalhe": carta.get("falta_o_que") or []},
            {"nome": "função e molde", "ok": bool(molde), "detalhe": f"função {funcao_id}"},
            {"nome": "parcelas numéricas", "ok": not faltantes, "detalhe": faltantes},
        ]
        return {
            "ok": not falhas,
            "modo": "simulação somente leitura",
            "carta": {
                "card_id": carta.get("card_id"), "nome": carta.get("nome"),
                "corpo": carta.get("corpo"), "pe_ruim_uso": carta.get("pe_ruim_uso"),
                "pe_ruim_precisao": carta.get("pe_ruim_precisao"),
                "posicao": {"id": posicao, "codigo": carta.get("posicao_codigo"), "raw": carta.get("posicao_raw")},
                "playstyles": [
                    {"slot": 1, "id": carta.get("slot1_id_jogo"), "nome": carta.get("slot1_nome")},
                    {"slot": 2, "id": carta.get("slot2_id_jogo"), "nome": carta.get("slot2_nome")},
                ],
                "estilos_ia": carta.get("estilos_ia") or [],
                "cardinalidades": {
                    "corpo": carta.get("corpo_cardinalidade"), "pe": carta.get("pe_relacao_cardinalidade"),
                    "posicao": carta.get("posicao_relacao_cardinalidade"), "playstyles": carta.get("playstyle_relacao_cardinalidade"),
                    "ia": carta.get("estilos_ia_cardinalidade"),
                },
            },
            "funcao": funcoes[funcao_id],
            "bonus": {**componentes, "total": total, "corpo_detalhe": corpo[3] if corpo else None},
            "gates": gates,
            "regua": {
                "contrato": regua.get("contrato"), "parametros": par,
                "cardinalidades": regua.get("cardinalidades"), "proveniencia": regua.get("proveniencia"),
            },
            "molde": molde,
            "regra_estilo": {
                "slot_que_manda": slot_manda, "playstyle_dono": dono, "playstyle_complementar": outro,
                "funcao_casa_id": casa, "complementar_ativa_na_posicao": posicao in liga,
            },
            "falhas": falhas,
        }

    def auditoria(self) -> dict:
        regua = self.regua()
        texto = MOTOR.read_bytes()
        return {
            "modo": "somente leitura — não existe endpoint de lote ou gravação",
            "contrato": regua.get("contrato"), "regua_apta": regua.get("pode_rodar"),
            "falta_o_que": regua.get("falta_o_que") or [],
            "cardinalidades": regua.get("cardinalidades"), "proveniencia": regua.get("proveniencia"),
            "motor_sha256": hashlib.sha256(texto).hexdigest(),
            "paridade": "a simulação executa as funções puras extraídas do próprio motor; não replica fórmula no navegador",
            "acesso": "navegador -> servidor local -> RPCs bonificador_*_v1; nenhuma tabela clube_novo é exposta",
        }


def criar_servidor(servico: ServicoBonificador | None = None, porta: int = 8766) -> ThreadingHTTPServer:
    servico = servico or ServicoBonificador()

    class Manipulador(BaseHTTPRequestHandler):
        def log_message(self, formato, *args):
            return

        def responder_json(self, status: int, dados: dict):
            corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def responder_arquivo(self, nome: str, tipo: str):
            arquivo = PASTA / nome
            if not arquivo.is_file():
                self.responder_json(404, {"ok": False, "erro": "arquivo local ausente"})
                return
            corpo = arquivo.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def do_POST(self):
            self.responder_json(HTTPStatus.METHOD_NOT_ALLOWED, {"ok": False, "erro": "interface somente leitura"})

        def do_GET(self):
            caminho = urllib.parse.urlparse(self.path)
            parametros = urllib.parse.parse_qs(caminho.query)
            try:
                if caminho.path == "/":
                    return self.responder_arquivo("index.html", "text/html; charset=utf-8")
                if caminho.path == "/app.js":
                    return self.responder_arquivo("app.js", "text/javascript; charset=utf-8")
                if caminho.path == "/style.css":
                    return self.responder_arquivo("style.css", "text/css; charset=utf-8")
                if caminho.path == "/api/saude":
                    regua = servico.regua()
                    return self.responder_json(200, {"ok": True, "contrato": regua.get("contrato"), "pode_rodar": regua.get("pode_rodar"), "falta_o_que": regua.get("falta_o_que") or []})
                if caminho.path == "/api/funcoes":
                    return self.responder_json(200, {"ok": True, "funcoes": servico.catalogo_funcoes(servico.regua())})
                if caminho.path == "/api/simular":
                    card_id = (parametros.get("card_id") or [""])[0]
                    try:
                        funcao_id = int((parametros.get("funcao_id") or [""])[0])
                    except ValueError as erro:
                        raise ErroDaInterface("funcao_id inválido") from erro
                    return self.responder_json(200, servico.simular(card_id, funcao_id))
                if caminho.path == "/api/auditoria":
                    return self.responder_json(200, {"ok": True, "auditoria": servico.auditoria()})
                return self.responder_json(404, {"ok": False, "erro": "rota local não encontrada"})
            except ErroDaInterface as erro:
                return self.responder_json(erro.status, {"ok": False, "erro": str(erro)})
            except Exception:
                return self.responder_json(500, {"ok": False, "erro": "falha local ao montar a resposta"})

    return ThreadingHTTPServer(("127.0.0.1", porta), Manipulador)


if __name__ == "__main__":
    porta = int(os.environ.get("CLUBEF_BONIFICADOR_PORT") or "8766")
    print(f"Interface do Bonificador: http://127.0.0.1:{porta}")
    print("Modo somente leitura. Ctrl+C para encerrar.")
    criar_servidor(porta=porta).serve_forever()
