# -*- coding: utf-8 -*-
"""Componente local do Bonificador, em loopback e sem expor credenciais.

A janela nativa fala somente com este servidor em 127.0.0.1. Consultas seguem
somente leitura; o pipeline, quando o operador o inicia, roda como processo local
separado e usa exclusivamente os contratos canônicos do próprio motor.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


PASTA = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
if getattr(sys, "frozen", False):
    MOTOR = Path(sys._MEIPASS) / "motor_bonus.py"
else:
    MOTOR = PASTA.parent / "motor_bonus.py"
if getattr(sys, "frozen", False) and "--pipeline" in sys.argv:
    import runpy
    runpy.run_path(str(MOTOR), run_name="__main__")
    raise SystemExit(0)
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


def ler_config() -> tuple[str, str, str]:
    config_fornecida = os.environ.get("CLUBEF_BONIFICADOR_CONFIG", "")
    config = Path(config_fornecida) if config_fornecida else achar_raiz() / "2-MOTORES" / "config.txt"
    valores: dict[str, str] = {}
    for linha in config.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            chave, valor = linha.split("=", 1)
            valores[chave.strip()] = valor.strip()
    url = valores.get("SUPABASE_URL", "").rstrip("/")
    chave = valores.get("SUPABASE_KEY", "")
    banco = valores.get("BONIFICADOR_DATABASE_URL", "")
    if banco:
        return url, chave, banco
    if not url or not chave or "COLE_AQUI" in chave:
        raise ErroDaInterface("configuração local do Bonificador está incompleta", 503)
    return url, chave, ""


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
        self.url, self.chave, self.banco = ler_config()

    def _rpc_banco(self, nome: str, corpo: dict | None):
        """Executa apenas a allowlist de contratos via login local restrito."""
        try:
            import psycopg
        except ImportError as erro:
            raise ErroDaInterface("componente local sem dependência de banco", 503) from erro
        try:
            with psycopg.connect(self.banco, connect_timeout=15) as conexao:
                with conexao.cursor() as cursor:
                    if nome == "bonificador_regua_v2":
                        cursor.execute("select public.bonificador_regua_v2()")
                        return cursor.fetchone()[0]
                    if nome == "bonificador_carta_v2":
                        cursor.execute("select public.bonificador_carta_v2(%s)", ((corpo or {}).get("p_card_id"),))
                        return cursor.fetchone()[0]
                    if nome == "bonificador_contexto_fila_v5":
                        cursor.execute("select * from public.bonificador_contexto_fila_v5(%s,%s)", (
                            (corpo or {}).get("p_limit", 1000), (corpo or {}).get("p_offset", 0)))
                        colunas = [d.name for d in cursor.description]
                        return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
                    if nome == "bonificador_resultados_v1":
                        cursor.execute("select * from public.bonificador_resultados_v1(%s,%s)", (
                            (corpo or {}).get("p_limit", 1000), (corpo or {}).get("p_offset", 0)))
                        colunas = [d.name for d in cursor.description]
                        return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
                    cursor.execute("select public.gravar_build_bonificador_v4(%s::jsonb)", (json.dumps((corpo or {}).get("p_resultado")),))
                    return cursor.fetchone()[0]
        except Exception as erro:
            raise ErroDaInterface(f"contrato local indisponível ({type(erro).__name__})", 503) from erro

    def rpc(self, nome: str, corpo: dict | None = None):
        if nome not in {
            "bonificador_regua_v2",
            "bonificador_carta_v2",
            "bonificador_contexto_fila_v5",
            "bonificador_resultados_v1",
            "gravar_build_bonificador_v4",
        }:
            raise ErroDaInterface("contrato não permitido", 403)
        if self.banco:
            return self._rpc_banco(nome, corpo)
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
            detalhe = erro.read().decode("utf-8", errors="replace").strip()
            detalhe = re.sub(r"\s+", " ", detalhe)[:300]
            sufixo = f": {detalhe}" if detalhe else ""
            raise ErroDaInterface(f"contrato recusou a consulta ({erro.code}){sufixo}", 503) from erro
        except Exception as erro:
            raise ErroDaInterface(
                f"não foi possível consultar o contrato ({type(erro).__name__})", 503
            ) from erro
        return json.loads(texto) if texto.strip() else None


class ServicoBonificador:
    def __init__(self, gateway: GatewayBonificador | None = None):
        self._gateway = gateway
        self.funcoes = carregar_funcoes_puras()

    @property
    def gateway(self) -> GatewayBonificador:
        # A janela deve abrir mesmo sem configuração de banco; a consulta falha
        # de modo explícito apenas quando o operador pede dados canônicos.
        if self._gateway is None:
            self._gateway = GatewayBonificador()
        return self._gateway

    def regua(self) -> dict:
        regua = self.gateway.rpc("bonificador_regua_v2") or {}
        if regua.get("contrato") != "bonificador-regua-v2":
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

    def fila_pendente(self, limite: int = 5000) -> dict:
        """Lê a fila operacional do contrato, sem tabela direta nem escrita."""
        limite = max(1, min(int(limite), 5000))
        bruto = self.gateway.rpc("bonificador_contexto_fila_v5", {
            "p_limit": limite, "p_offset": 0,
        }) or []
        if not isinstance(bruto, list):
            raise ErroDaInterface("contrato da fila do Bonificador devolveu formato inesperado", 503)
        itens = []
        for dado in bruto:
            try:
                funcao_id = int(dado["funcao_id"])
                linha_id = int(dado["build_linha_card_id"])
                posicao_id = int(dado["posicao_id"])
            except (KeyError, TypeError, ValueError) as erro:
                raise ErroDaInterface("contrato da fila sem identidade canônica", 503) from erro
            itens.append({
                "linha_id": linha_id,
                "card_id": str(dado.get("card_id") or ""),
                "carta_nome": str(dado.get("carta_nome") or "Carta sem nome canônico"),
                "carta_tipo": str(dado.get("carta_tipo") or "Coleção não informada"),
                "carta_box": str(dado.get("carta_box") or ""),
                "carta_overall": dado.get("carta_overall"),
                "funcao_id": funcao_id,
                "funcao_codigo": str(dado.get("funcao_codigo") or ""),
                "funcao_nome": str(dado.get("funcao_nome") or "Função canônica sem rótulo"),
                "posicao_id": posicao_id,
                "posicao_codigo": str(dado.get("posicao_codigo") or ""),
                "posicao_nome": str(dado.get("posicao_nome") or "Posição canônica sem nome"),
                "carta_versao": dado.get("carta_versao"),
                "carta_fingerprint": dado.get("carta_fingerprint"),
            })
        return {
            "contrato": "bonificador_contexto_fila_v5",
            "itens": itens,
            "total": len(itens),
            "total_exato": len(itens) < limite,
            "limite": limite,
        }

    def resultados_persistidos(self, limite: int = 5000) -> dict:
        """Lê resultados já confirmados por contrato próprio, sem depender da fila pendente."""
        limite = max(1, min(int(limite), 5000))
        bruto = self.gateway.rpc("bonificador_resultados_v1", {
            "p_limit": limite, "p_offset": 0,
        }) or []
        if not isinstance(bruto, list):
            raise ErroDaInterface("contrato de resultados devolveu formato inesperado", 503)
        return {"contrato": "bonificador_resultados_v1", "itens": bruto, "total": len(bruto)}

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
        carta = self.gateway.rpc("bonificador_carta_v2", {"p_card_id": card_id}) or {}
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
            "modo": "simulação somente leitura; controle local do pipeline em processo separado",
            "contrato": regua.get("contrato"), "regua_apta": regua.get("pode_rodar"),
            "falta_o_que": regua.get("falta_o_que") or [],
            "cardinalidades": regua.get("cardinalidades"), "proveniencia": regua.get("proveniencia"),
            "motor_sha256": hashlib.sha256(texto).hexdigest(),
            "paridade": "a simulação executa as funções puras extraídas do próprio motor; não replica fórmula no navegador",
            "acesso": "navegador -> servidor local -> RPCs bonificador_*_v1; nenhuma tabela clube_novo é exposta",
        }


class PipelineBonificador:
    """Controla um processo do motor sem guardar fila ou credencial no navegador."""

    def __init__(self, popen_factory=None):
        self._popen = popen_factory or subprocess.Popen
        self._lock = threading.RLock()
        self._processo = None
        self._parada_solicitada = False
        self._arquivo_parada: Path | None = None
        self._estado = {"estado": "parado", "mensagem": "Pipeline não iniciado.",
                        "aguardando": False, "confirmados": 0, "calculados": 0,
                        "total_rodada": 0, "linha_atual": None, "eventos": [],
                        "resultados": {}, "codigo_saida": None}

    def estado(self) -> dict:
        with self._lock:
            return {**self._estado, "ativo": self._processo is not None and self._processo.poll() is None}

    def _atualizar(self, **campos) -> None:
        with self._lock:
            self._estado.update(campos)

    def _evento(self, texto: str) -> None:
        with self._lock:
            eventos = list(self._estado.get("eventos") or [])
            eventos.append(texto)
            self._estado["eventos"] = eventos[-30:]

    def iniciar(self) -> dict:
        with self._lock:
            if self._processo is not None and self._processo.poll() is None:
                return self.estado()
            opcoes = {"cwd": str(MOTOR.parent), "stdin": subprocess.DEVNULL,
                       "stdout": subprocess.PIPE, "stderr": subprocess.STDOUT,
                       "text": True, "encoding": "utf-8", "errors": "replace", "bufsize": 1,
                       "env": {**os.environ, "PYTHONUTF8": "1"}}
            arquivo_parada = Path(tempfile.gettempdir()) / ("clubef-bonificador-parar-" + uuid.uuid4().hex + ".flag")
            opcoes["env"]["CLUBEF_BONIFICADOR_STOP_FILE"] = str(arquivo_parada)
            if ler_config()[2]:
                opcoes["env"]["CLUBEF_BONIFICADOR_USAR_BANCO_DIRETO"] = "1"
            if os.name == "nt":
                opcoes["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            comando = ([sys.executable, "--pipeline"] if getattr(sys, "frozen", False)
                       else [sys.executable, "-u", str(MOTOR)])
            self._processo = self._popen(comando, **opcoes)
            self._parada_solicitada = False
            self._arquivo_parada = arquivo_parada
            self._estado = {"estado": "iniciando", "mensagem": "Iniciando o pipeline canônico...",
                            "aguardando": False, "confirmados": 0, "calculados": 0,
                            "total_rodada": 0, "linha_atual": None, "eventos": [],
                            "resultados": {}, "codigo_saida": None}
            processo = self._processo
        threading.Thread(target=self._ler_saida, args=(processo,), daemon=True).start()
        threading.Thread(target=self._aguardar_saida, args=(processo,), daemon=True).start()
        return self.estado()

    def parar(self) -> dict:
        with self._lock:
            processo = self._processo
            if processo is None or processo.poll() is not None:
                return self.estado()
            self._parada_solicitada = True
            self._estado.update(estado="parando", mensagem="Parada solicitada; terminando a rodada atual.")
            arquivo_parada = self._arquivo_parada
        try:
            if arquivo_parada is None:
                raise RuntimeError("sinal cooperativo ausente")
            arquivo_parada.touch(exist_ok=True)
        except Exception as erro:
            self._atualizar(estado="erro", mensagem="Não foi possível solicitar a parada: %s" % type(erro).__name__)
        return self.estado()

    def _ler_saida(self, processo) -> None:
        for linha in getattr(processo, "stdout", ()):
            texto = linha.strip()
            if not texto:
                continue
            campos = {"mensagem": texto}
            if texto.startswith("FILA_TOTAL:"):
                try:
                    campos["total_rodada"] = int(texto.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif texto.startswith("FILA_LINHA:"):
                partes = dict(
                    campo.split("=", 1) for campo in texto.split(":", 1)[1].strip().split()
                    if "=" in campo
                )
                campos["linha_atual"] = {
                    "linha_id": partes.get("linha"), "card_id": partes.get("card"),
                    "funcao_id": partes.get("funcao"), "posicao_id": partes.get("posicao"),
                }
                campos.update(estado="processando", aguardando=False)
            elif texto.startswith("FILA_CALCULADA:"):
                campos["calculados"] = int(self.estado().get("calculados") or 0) + 1
            elif texto.startswith("FILA_RESULTADO:"):
                try:
                    resultado = json.loads(texto.split(":", 1)[1].strip())
                    linha_id = str(resultado["linha_id"])
                    resultados = dict(self.estado().get("resultados") or {})
                    resultados[linha_id] = resultado
                    campos["resultados"] = resultados
                except (ValueError, KeyError, TypeError):
                    campos["mensagem"] = "resultado de fila inválido"
            elif texto.startswith("FILA_CONFIRMADA:"):
                campos["confirmados"] = int(self.estado().get("confirmados") or 0) + 1
            if "AGUARDANDO NOVAS LINHAS" in texto:
                campos.update(estado="aguardando", aguardando=True)
            elif "CONTINUANDO:" in texto or "[2/4]" in texto or "[3/4]" in texto or "[4/4]" in texto:
                campos.update(estado="processando", aguardando=False)
            elif "PARADA NORMAL" in texto:
                campos.update(estado="parado", aguardando=False)
            elif "PAREI:" in texto or "ERRO" in texto:
                campos.update(estado="erro", aguardando=False)
            self._atualizar(**campos)
            if texto.startswith("FILA_") or "PAREI:" in texto or "ERRO" in texto:
                self._evento(texto)

    def _aguardar_saida(self, processo) -> None:
        codigo = processo.wait()
        with self._lock:
            if processo is not self._processo:
                return
            arquivo_parada = self._arquivo_parada
            self._arquivo_parada = None
            self._estado.update(codigo_saida=codigo, aguardando=False)
            if self._parada_solicitada or codigo == 0:
                self._estado.update(estado="parado", mensagem="Pipeline parado normalmente.")
            else:
                detalhe = self._estado.get("mensagem")
                mensagem = "Pipeline terminou com código %s." % codigo
                if detalhe and detalhe not in {"Iniciando o pipeline canônico...", mensagem}:
                    mensagem += " Detalhe: %s" % detalhe
                self._estado.update(estado="erro", mensagem=mensagem)
        if arquivo_parada:
            try:
                arquivo_parada.unlink(missing_ok=True)
            except OSError:
                pass


def criar_servidor(servico: ServicoBonificador | None = None, porta: int = 8766,
                  pipeline: PipelineBonificador | None = None) -> ThreadingHTTPServer:
    servico = servico or ServicoBonificador()
    pipeline = pipeline or PipelineBonificador()

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

        def do_POST(self):
            caminho = urllib.parse.urlparse(self.path)
            try:
                tamanho = int(self.headers.get("Content-Length") or "0")
                if tamanho > 8192:
                    raise ErroDaInterface("pedido local muito grande", 413)
                if tamanho:
                    self.rfile.read(tamanho)
                if caminho.path == "/api/pipeline/iniciar":
                    return self.responder_json(200, {"ok": True, "pipeline": pipeline.iniciar()})
                if caminho.path == "/api/pipeline/parar":
                    return self.responder_json(200, {"ok": True, "pipeline": pipeline.parar()})
                return self.responder_json(HTTPStatus.METHOD_NOT_ALLOWED, {"ok": False, "erro": "ação local não permitida"})
            except ErroDaInterface as erro:
                return self.responder_json(erro.status, {"ok": False, "erro": str(erro)})
            except Exception as erro:
                return self.responder_json(500, {"ok": False, "erro": "falha local no controle do pipeline: %s" % type(erro).__name__})

        def do_GET(self):
            caminho = urllib.parse.urlparse(self.path)
            parametros = urllib.parse.parse_qs(caminho.query)
            try:
                if caminho.path == "/api/ping":
                    return self.responder_json(200, {"ok": True, "aplicativo": "bonificador_clubefootball", "versao_interface": "20260831-v2-native"})
                if caminho.path == "/api/saude":
                    regua = servico.regua()
                    return self.responder_json(200, {"ok": True, "aplicativo": "bonificador_clubefootball", "versao_interface": "20260831-v2-native", "contrato": regua.get("contrato"), "pode_rodar": regua.get("pode_rodar"), "falta_o_que": regua.get("falta_o_que") or []})
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
                if caminho.path == "/api/resultados":
                    return self.responder_json(200, {"ok": True, "resultados": servico.resultados_persistidos()})
                if caminho.path == "/api/fila/status":
                    fila = servico.fila_pendente()
                    estado = pipeline.estado()
                    atual = estado.get("linha_atual") or {}
                    resultados = estado.get("resultados") or {}
                    for item in fila["itens"]:
                        resultado = resultados.get(str(item["linha_id"]))
                        if resultado:
                            item.update({
                                "estado": resultado.get("estado") or "calculada",
                                "b_corpo": resultado.get("b_corpo"),
                                "b_pe_ruim": resultado.get("b_pe_ruim"),
                                "b_estilo": resultado.get("b_estilo"),
                                "b_ia": resultado.get("b_ia"),
                                "b_total": resultado.get("b_total"),
                                "faltou": resultado.get("faltou") or [],
                            })
                        else:
                            item["estado"] = "calculando" if str(item["linha_id"]) == str(atual.get("linha_id")) else "pendente"
                    fila["pipeline"] = estado
                    return self.responder_json(200, {"ok": True, "fila": fila})
                if caminho.path == "/api/pipeline/estado":
                    return self.responder_json(200, {"ok": True, "pipeline": pipeline.estado()})
                return self.responder_json(404, {"ok": False, "erro": "rota local não encontrada"})
            except ErroDaInterface as erro:
                return self.responder_json(erro.status, {"ok": False, "erro": str(erro)})
            except Exception:
                return self.responder_json(500, {"ok": False, "erro": "falha local ao montar a resposta"})

    return ThreadingHTTPServer(("127.0.0.1", porta), Manipulador)


if __name__ == "__main__":
    argumento_porta = next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--porta=")), "")
    porta = int(argumento_porta or os.environ.get("CLUBEF_BONIFICADOR_PORT") or "8766")
    print(f"Interface do Bonificador: http://127.0.0.1:{porta}")
    print("Modo somente leitura. Ctrl+C para encerrar.")
    criar_servidor(porta=porta).serve_forever()
