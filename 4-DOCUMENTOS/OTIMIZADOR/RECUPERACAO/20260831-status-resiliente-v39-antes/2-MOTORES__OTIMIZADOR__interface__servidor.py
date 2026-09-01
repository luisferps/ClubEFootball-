# -*- coding: utf-8 -*-
"""Painel local do Otimizador, restrito a 127.0.0.1 e contratos selados."""

from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# O executável portátil informa a raiz externa para continuar usando a mesma
# configuração e os mesmos módulos do Otimizador, mesmo sem Python instalado.
RAIZ_OPERACIONAL = os.environ.get("CLUBEF_OTIMIZADOR_ROOT", "").strip()
if RAIZ_OPERACIONAL:
    MOTOR_DIR = Path(RAIZ_OPERACIONAL).expanduser().resolve()
    PASTA = MOTOR_DIR / "interface"
else:
    PASTA = Path(__file__).resolve().parent
    MOTOR_DIR = PASTA.parent
# A configuração própria do aplicativo tem precedência sobre a compartilhada.
# Isso permite levar a pasta OTIMIZADOR a outro Windows e configurá-la uma vez
# pelo próprio ícone, sem depender do caminho absoluto da cópia anterior.
CONFIG_CANDIDATAS = (MOTOR_DIR / "config.txt", MOTOR_DIR.parent / "config.txt")
CARD_ID_VALIDO = re.compile(r"^[A-Za-z0-9@_-]{1,64}$")
APLICATIVO_ID = "otimizador_clubefootball"
INTERFACE_VERSAO = "20260831-v38"
JANELA_CACHE_STATUS_SEGUNDOS = 2.0
INTERVALO_RECONEXAO_BANCO_SEGUNDOS = 30.0
FILA_V5_AGUARDANDO_APLICACAO = (
    "A fila integral V5 está preparada localmente, mas a migração ainda não foi "
    "aplicada em clube_novo. Nenhuma carta será criada ou processada até essa "
    "aplicação explícita."
)
RPC_PERMITIDAS = {
    "otimizador_regua_v2", "otimizador_carta_v3",
    "otimizador_catalogos_apresentacao_v1", "otimizador_carta_apresentacao_v1",
    "otimizador_producao_status_v3", "otimizador_producao_contexto_lote_v3",
    "otimizador_producao_controlar_lote_v3",
    "otimizador_producao_recuperar_reserva_orfa_v9",
    "otimizador_producao_reservar_linha_v3", "otimizador_producao_concluir_linha_v3",
    "otimizador_producao_bloquear_linha_v3", "otimizador_producao_falhar_lote_v3",
    "otimizador_producao_status_v5", "otimizador_producao_prevoo_integral_v5",
    "otimizador_producao_criar_lote_integral_v5", "otimizador_producao_preparar_fatia_v5",
    "otimizador_producao_controlar_preparo_v5", "otimizador_producao_fila_paginada_v5",
    "otimizador_producao_eventos_paginados_v5", "otimizador_cartas_apresentacao_v2",
    "otimizador_producao_iniciar_esteira_v6", "otimizador_producao_preparar_fatia_v6",
    "otimizador_producao_reservar_linha_v6", "otimizador_producao_concluir_linha_v6",
}


class ErroDaInterface(Exception):
    def __init__(self, mensagem: str, status: int = 400):
        super().__init__(mensagem)
        self.status = status


def ler_config() -> tuple[str, str]:
    valores = {}
    config = next((candidata for candidata in CONFIG_CANDIDATAS if candidata.is_file()), None)
    if config is None:
        raise ErroDaInterface("configuração local não encontrada (config.txt)", 503)
    for linha in config.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            chave, valor = linha.split("=", 1)
            valores[chave.strip()] = valor.strip()
    url, chave = valores.get("SUPABASE_URL", "").rstrip("/"), valores.get("SUPABASE_KEY", "")
    if not url or not chave or "COLE_AQUI" in chave:
        raise ErroDaInterface("configuração local do Otimizador está incompleta", 503)
    return url, chave


def cabecalhos_supabase(chave: str) -> dict[str, str]:
    """Monta cabeçalhos de backend sem enviar uma chave opaca ``sb_*`` como JWT."""
    cabecalhos = {
        "apikey": chave,
        "Content-Type": "application/json",
        "User-Agent": "ClubEfootballOtimizadorLocal/1.2",
    }
    # Chaves atuais sb_secret/sb_publishable não são JWTs. As chaves JWT legadas
    # continuam precisando de Authorization para preservar a compatibilidade local.
    if not chave.startswith("sb_"):
        cabecalhos["Authorization"] = "Bearer " + chave
    return cabecalhos


class GatewayOtimizador:
    """A única saída do processo local: contratos permitidos e selados."""

    def __init__(self):
        self.url, self.chave = ler_config()

    def rpc(
        self,
        nome: str,
        corpo: dict | None = None,
        ausente_ok: bool = False,
        timeout_segundos: float = 45,
    ):
        if nome not in RPC_PERMITIDAS:
            raise ErroDaInterface("contrato não permitido nesta interface", 403)
        pedido = urllib.request.Request(
            f"{self.url}/rest/v1/rpc/{nome}",
            data=json.dumps(corpo or {}).encode("utf-8"),
            headers=cabecalhos_supabase(self.chave),
            method="POST",
        )
        try:
            # A consulta de estado não pode deixar a interface inteira parada
            # por 45 segundos. Chamadores de acompanhamento usam um limite
            # curto e recebem um estado local seguro; simulações continuam
            # podendo usar o limite padrão mais generoso.
            timeout = max(1.0, min(float(timeout_segundos), 60.0))
            with urllib.request.urlopen(pedido, timeout=timeout) as resposta:
                texto = resposta.read().decode("utf-8")
        except urllib.error.HTTPError as erro:
            detalhe = erro.read().decode("utf-8", "replace")
            if (ausente_ok and erro.code in {400, 404}
                    and "otimizador_producao_" in detalhe
                    and ("does not exist" in detalhe or "Could not find" in detalhe)):
                return None
            if erro.code == 500 and '"code":"57014"' in detalhe:
                raise ErroDaInterface(
                    "o banco excedeu o tempo da consulta de acompanhamento (57014); "
                    "nenhuma linha foi iniciada",
                    503,
                ) from erro
            if erro.code in {502, 503, 504} and any(
                codigo in detalhe for codigo in ("PGRST000", "PGRST001", "PGRST002", "PGRST003")
            ):
                raise ErroDaInterface(
                    "o banco está restabelecendo o contrato de leitura; "
                    "nenhuma linha foi iniciada",
                    503,
                ) from erro
            raise ErroDaInterface(f"contrato recusou a consulta ({erro.code})", 503) from erro
        except (TimeoutError, socket.timeout):
            raise ErroDaInterface(
                "o banco demorou a responder à consulta de acompanhamento; "
                "nenhuma linha foi iniciada",
                503,
            ) from None
        except Exception as erro:
            raise ErroDaInterface(f"não foi possível consultar o contrato ({type(erro).__name__})", 503) from erro
        return json.loads(texto) if texto.strip() else None


class ServicoOtimizador:
    """Usa o cálculo aprovado; motor por IDs e apresentação em porta separada."""

    def __init__(self, gateway=None):
        if str(MOTOR_DIR) not in sys.path:
            sys.path.insert(0, str(MOTOR_DIR))
        self.gateway = gateway or GatewayOtimizador()
        # Não importar a fórmula/motor ao levantar o painel. Os módulos do
        # cálculo carregam a régua selada durante o import; se a conexão cair,
        # isso não pode derrubar a porta local nem impedir a recuperação
        # automática da fila. O carregamento ocorre só quando há simulação ou
        # trabalho efetivamente autorizado.
        self.fonte = None
        self.equacao = None
        self.motor = None
        self._motor_modulos_lock = threading.RLock()
        self._nomes_cartas = {}
        self._funcoes_por_id = {}
        self._posicoes_por_id = {}
        self._tecnicos_por_id = {}
        self._habilidades_por_id = {}
        self._impetos_por_id = {}
        self._catalogos_apresentacao = None
        self._worker_lock = threading.RLock()
        self._worker_thread = None
        self._worker_lote_id = None
        self._preparo_thread = None
        self._preparo_lote_id = None
        # Última resposta completa por página. Ela não substitui dados do
        # banco nem habilita ações: serve exclusivamente para manter a tela
        # informativa durante uma indisponibilidade temporária do contrato.
        self._paineis_fila_confirmados = {}
        self._paineis_fila_lock = threading.RLock()
        # Uma atualização do painel pede status, eventos e resultados quase ao
        # mesmo tempo. Reutilizar a mesma leitura por poucos segundos evita
        # três RPCs iguais e reduz pressão sobre o contrato sem transformar
        # dado remoto em fonte local de decisão.
        self._status_fila_confirmado = None
        self._status_fila_confirmado_ate = 0.0
        self._status_fila_lock = threading.RLock()
        # Ao falhar, o circuito impede que cliques, abas e atualizações em
        # paralelo convertam uma única indisponibilidade do Data API em uma
        # tempestade de requisições. Enquanto estiver aberto, só devolvemos
        # a resposta local fail-closed; nenhum comando é aceito.
        self._banco_indisponivel_ate = 0.0
        self._ultima_falha_banco = None
        self._circuito_banco_lock = threading.RLock()
        # Este estado pertence apenas ao processo local. Ele não substitui os
        # estados selados da fila no banco; existe para que a tela e o ícone
        # do Windows digam com honestidade se este computador ainda calcula
        # uma linha depois que a janela do navegador foi fechada.
        self._servidor_iniciado_em = time.time()
        self._worker_estado = self._estado_local("aguardando")
        self._preparo_estado = self._estado_local("aguardando")

    def _carregar_modulos_do_motor(self):
        """Carrega a fórmula aprovada sob demanda, nunca durante o boot.

        O isolamento não altera fórmula, pesos ou ordem. Ele apenas impede que
        uma indisponibilidade transitória do contrato derrube o serviço de
        acompanhamento antes de a tela poder se recuperar.
        """
        if self.fonte is not None and self.equacao is not None and self.motor is not None:
            return
        with self._motor_modulos_lock:
            if self.fonte is not None and self.equacao is not None and self.motor is not None:
                return
            try:
                import fonte_unica as fonte
                import equacao as equacao
                import motor as motor
            except SystemExit as erro:
                # fonte_unica é fail-closed e usa SystemExit para sinalizar
                # contrato inacessível. No painel, convertemos isso em erro
                # HTTP local controlado, mantendo a porta de saúde viva.
                for nome in ("motor", "equacao", "fonte_unica"):
                    sys.modules.pop(nome, None)
                raise ErroDaInterface(
                    "os insumos do cálculo ainda não responderam; a tela continuará disponível "
                    "e nenhuma linha será iniciada",
                    503,
                ) from erro
            self.fonte, self.equacao, self.motor = fonte, equacao, motor

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
        self._carregar_modulos_do_motor()
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

    def _status_fila(self):
        """Lê só o contrato V5; ausência da migração é honesta e fechada."""
        if not hasattr(self, "gateway"):
            return self._fila_v5_aguardando_aplicacao()
        if not hasattr(self, "_status_fila_lock"):
            self._status_fila_lock = threading.RLock()
            self._status_fila_confirmado = None
            self._status_fila_confirmado_ate = 0.0
        with self._status_fila_lock:
            agora = time.monotonic()
            if (self._status_fila_confirmado is not None
                    and agora < self._status_fila_confirmado_ate):
                return self._copia_json(self._status_fila_confirmado)
            try:
                # O RPC V5 declara ``p_lote_id uuid DEFAULT NULL``. PostgREST não
                # aplica esse default se o corpo vier vazio: ele procura uma
                # sobrecarga sem argumentos e devolve 500. Enviar NULL preserva a
                # seleção canônica do lote ativo no próprio contrato, sem a UI
                # consultar tabelas nem guardar/adivinhar IDs locais.
                bruto = self.gateway.rpc(
                    "otimizador_producao_status_v5", {"p_lote_id": None},
                    ausente_ok=True, timeout_segundos=5,
                )
            except TypeError:
                return self._fila_v5_aguardando_aplicacao()
            if bruto is None:
                return self._fila_v5_aguardando_aplicacao()
            if bruto.get("contrato") != "otimizador_fila_producao_v5":
                raise ErroDaInterface("contrato da fila integral V5 inesperado", 503)
            resposta = dict(bruto)
            resposta["disponivel"] = True
            resposta["conexao_banco"] = True
            resposta["dados_em_cache"] = False
            self._status_fila_confirmado = self._copia_json(resposta)
            self._status_fila_confirmado_ate = agora + JANELA_CACHE_STATUS_SEGUNDOS
            return resposta

    def _verificar_circuito_banco(self):
        """Falha fechado enquanto a reconexão remota tem janela ativa."""
        if not hasattr(self, "_circuito_banco_lock"):
            self._circuito_banco_lock = threading.RLock()
            self._banco_indisponivel_ate = 0.0
            self._ultima_falha_banco = None
        with self._circuito_banco_lock:
            restantes = self._banco_indisponivel_ate - time.monotonic()
            if restantes > 0:
                raise ErroDaInterface(
                    "o banco continua em reconexão; nova tentativa automática em "
                    f"até {max(1, int(restantes + 0.999))} s; nenhuma linha foi iniciada",
                    503,
                )

    def _registrar_indisponibilidade_banco(self, erro):
        if not hasattr(self, "_circuito_banco_lock"):
            self._circuito_banco_lock = threading.RLock()
            self._banco_indisponivel_ate = 0.0
            self._ultima_falha_banco = None
        with self._circuito_banco_lock:
            self._ultima_falha_banco = str(erro)
            self._banco_indisponivel_ate = (
                time.monotonic() + INTERVALO_RECONEXAO_BANCO_SEGUNDOS
            )

    def _confirmar_banco_disponivel(self):
        if not hasattr(self, "_circuito_banco_lock"):
            return
        with self._circuito_banco_lock:
            self._banco_indisponivel_ate = 0.0
            self._ultima_falha_banco = None

    @staticmethod
    def _chave_painel_fila(offset, limite, somente_finais):
        return (bool(somente_finais), max(0, int(offset)), max(1, int(limite)))

    @staticmethod
    def _copia_json(valor):
        """Cópia sem referência compartilhada para o cache puramente visual."""
        return json.loads(json.dumps(valor, ensure_ascii=False))

    def _guardar_painel_confirmado(self, chave, painel):
        # Alguns testes de contrato constroem o serviço sem executar __init__.
        # A inicialização preguiçosa mantém essa prova isolada sem alterar o
        # comportamento da instância real.
        if not hasattr(self, "_paineis_fila_lock"):
            self._paineis_fila_lock = threading.RLock()
            self._paineis_fila_confirmados = {}
        with self._paineis_fila_lock:
            self._paineis_fila_confirmados[chave] = {
                "painel": self._copia_json(painel),
                "confirmado_em_epoch": time.time(),
            }

    def _painel_banco_indisponivel(self, erro, offset, limite, somente_finais):
        """Resposta 200, fail-closed, para indisponibilidade transitória.

        O browser nunca recebe a credencial e não deve decidir se pode iniciar
        algo quando o banco está inacessível. Se houver uma leitura anterior
        exatamente desta página, ela é mostrada como cache datado; sem cache,
        a tela continua honesta e vazia, mas pronta para tentar novamente.
        """
        chave = self._chave_painel_fila(offset, limite, somente_finais)
        if not hasattr(self, "_paineis_fila_lock"):
            self._paineis_fila_lock = threading.RLock()
            self._paineis_fila_confirmados = {}
        with self._paineis_fila_lock:
            registro = self._paineis_fila_confirmados.get(chave)
            registro = self._copia_json(registro) if registro else None
        mensagem = (
            "A conexão segura com o banco está temporariamente indisponível. "
            "A tela tentará novamente sozinha, de forma espaçada; nenhum comando "
            "da fila será enviado enquanto isso."
        )
        if registro:
            resposta = registro["painel"]
            resposta["disponivel"] = True
            resposta["dados_em_cache"] = True
            resposta["ultima_leitura_banco_em_epoch"] = registro["confirmado_em_epoch"]
        else:
            resposta = self._fila_v5_aguardando_aplicacao()
            resposta["disponivel"] = False
            resposta["dados_em_cache"] = False
            resposta["itens"] = []
            resposta["linha_atual"] = None
            resposta["paginacao"] = {
                "total": 0, "offset": max(0, int(offset)), "limite": max(1, int(limite)),
                "somente_finais": bool(somente_finais), "ordem": "mais_recentes_primeiro",
            }
        resposta["ok"] = True
        resposta["conexao_banco"] = False
        resposta["estado"] = "banco_indisponivel"
        resposta["estado_lote"] = "banco_indisponivel"
        resposta["execucao"] = {"estado": "banco_indisponivel"}
        resposta["mensagem"] = mensagem
        resposta["origem"] = "última leitura local confirmada; contratos de clube_novo em reconexão"
        resposta["publicacao"] = "SEM PUBLICAÇÃO"
        resposta["pode_publicar"] = False
        resposta["acoes"] = {
            "criar": False, "iniciar": False, "pausar": False, "parar": False,
            "retomar": False, "preparar": False, "console": False,
            "recuperar": False, "reassumir_worker_local": False,
        }
        resposta["confirmacao"] = {"parar_exige_confirmacao": True, "recuperar_exige_confirmacao": True}
        return resposta

    @staticmethod
    def _totais_fila(status):
        return {
            "cartas_selecionadas": status.get("cards", 0), "linhas_geradas": status.get("linhas", 0),
            "pendentes": status.get("pendentes", 0), "em_processamento": status.get("processando", 0),
            "concluidas": status.get("concluidas", 0), "bloqueadas": status.get("bloqueadas", 0),
            "interrompidas": status.get("interrompidas", 0),
            "falhas": status.get("falhas", 0),
            "bonificador_pendentes": status.get("bonificador_pendentes", 0),
            "preparo_total": (status.get("preparo") or {}).get("total", 0),
            "preparo_concluido": (status.get("preparo") or {}).get("concluido", 0),
            "preparo_pendentes": (status.get("preparo") or {}).get("pendentes", 0),
        }

    @staticmethod
    def _fila_v5_aguardando_aplicacao():
        totais = {
            "cartas_selecionadas": 0, "linhas_geradas": 0, "pendentes": 0,
            "em_processamento": 0, "concluidas": 0, "bloqueadas": 0,
            "interrompidas": 0, "falhas": 0, "bonificador_pendentes": 0,
            "preparo_total": 0, "preparo_concluido": 0, "preparo_pendentes": 0,
        }
        return {
            "ok": True, "disponivel": False,
            "estado": "aguardando_aplicacao_fila_v5", "estado_lote": "aguardando_aplicacao_fila_v5",
            "acoes": {"criar": False, "iniciar": False, "pausar": False,
                        "parar": False, "retomar": False, "preparar": False, "console": False},
            "confirmacao": {"parar_exige_confirmacao": True},
            "corrente": [], "linha_atual": None, "itens": [], "totais": totais,
            "preparo": {"estado": "nao_iniciado", "total": 0, "concluido": 0, "pendentes": 0},
            "mensagem": FILA_V5_AGUARDANDO_APLICACAO,
            "origem": "clube_novo somente; aguardando aplicação explícita da migração V5",
            "publicacao": "SEM PUBLICAÇÃO", "pode_publicar": False,
        }

    def _carregar_nomes_cartas(self, itens):
        faltantes = sorted({str(x.get("card_id")) for x in itens
                            if x.get("card_id") is not None} - set(self._nomes_cartas))
        if not faltantes:
            return
        pacote = self.gateway.rpc("otimizador_cartas_apresentacao_v2", {
            "p_card_ids": faltantes,
        }) or {}
        if pacote.get("contrato") != "otimizador_apresentacao_v2":
            raise ErroDaInterface("catálogo de cartas V2 indisponível", 503)
        encontrados = {str(x.get("card_id")): x.get("nome")
                      for x in pacote.get("itens") or [] if x.get("card_id") is not None}
        for card_id in faltantes:
            # A ausência fica explícita: jamais se recorre a fonte legada ou texto
            # inventado para completar um card_id canônico.
            self._nomes_cartas[card_id] = encontrados.get(card_id)

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
        self._carregar_nomes_cartas(itens)
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

    @staticmethod
    def _plano_pagina_mais_recente(total, offset, limite):
        """Converte a paginação canônica crescente em uma página visual decrescente.

        A fila continua imutável e é sempre executada pela sua ``ordem_fila``
        crescente. Isto só muda a janela que o painel lê: página visual 0 mostra
        as últimas linhas, e as páginas seguintes caminham para as mais antigas.
        """
        total = max(0, int(total or 0))
        offset = max(0, int(offset or 0))
        limite = int(limite or 0)
        if limite not in range(1, 201):
            raise ErroDaInterface("limite de paginação fora da faixa", 400)
        quantidade = min(limite, max(0, total - offset))
        return {
            "total": total,
            "offset_visual": offset,
            "limite": limite,
            "quantidade": quantidade,
            "offset_canonico": max(0, total - offset - quantidade),
        }

    def _ler_pagina_mais_recente(self, lote_id, offset, limite, somente_finais, total_esperado):
        """Lê o contrato V5 sem alterá-lo e devolve o recorte mais recente primeiro.

        O RPC canônico só expõe ``ordem_fila`` crescente. Usamos o total selado
        no status para pedir o intervalo equivalente e inverter exclusivamente
        a resposta de apresentação. Se a fila mudou entre status e leitura,
        fazemos uma única releitura com o total que o próprio contrato devolveu.
        """
        plano = self._plano_pagina_mais_recente(total_esperado, offset, limite)

        def consultar(plano_atual):
            if plano_atual["quantidade"] == 0:
                return None
            resposta = self.gateway.rpc("otimizador_producao_fila_paginada_v5", {
                "p_lote_id": lote_id,
                "p_offset": plano_atual["offset_canonico"],
                "p_limite": plano_atual["quantidade"],
                "p_somente_finais": bool(somente_finais),
            }) or {}
            if resposta.get("contrato") != "otimizador_fila_producao_v5":
                raise ErroDaInterface("leitura paginada da fila V5 inesperada", 503)
            return resposta

        fila = consultar(plano)
        if fila is None:
            # Não há página naquela posição. O próximo refresh de status traz
            # linhas recém-gravadas sem fazer uma leitura de tabela paralela.
            return [], {
                "total": plano["total"], "offset": plano["offset_visual"],
                "limite": plano["limite"], "somente_finais": bool(somente_finais),
                "ordem": "mais_recentes_primeiro",
            }

        total_observado = max(0, int(fila.get("total") or 0))
        if total_observado != plano["total"]:
            # No máximo uma tentativa de alinhamento: evita um loop de leitura
            # quando o worker conclui uma linha enquanto o painel atualiza.
            plano = self._plano_pagina_mais_recente(total_observado, offset, limite)
            fila = consultar(plano)
            if fila is None:
                return [], {
                    "total": plano["total"], "offset": plano["offset_visual"],
                    "limite": plano["limite"], "somente_finais": bool(somente_finais),
                    "ordem": "mais_recentes_primeiro",
                }
            total_observado = max(0, int(fila.get("total") or 0))

        itens = list(reversed((fila.get("itens") or [])[:plano["quantidade"]]))
        return itens, {
            "total": total_observado, "offset": plano["offset_visual"],
            "limite": plano["limite"], "somente_finais": bool(somente_finais),
            "ordem": "mais_recentes_primeiro",
        }

    def painel_fila(self, offset=0, limite=100, somente_finais=False):
        try:
            self._verificar_circuito_banco()
            status = dict(self._status_fila())
            if not status.get("disponivel"):
                return status
            self._confirmar_banco_disponivel()
            acoes = dict(status.get("acoes") or {})
            confirmacao = dict(status.get("confirmacao") or {})
            acoes["recuperar"] = self._recuperacao_reserva_orfa_disponivel(status)
            acoes["reassumir_worker_local"] = self._reassumir_esteira_local_disponivel(status)
            confirmacao["recuperar_exige_confirmacao"] = True
            status["acoes"] = acoes
            status["confirmacao"] = confirmacao
            lote_id = status.get("lote_id")
            itens = []
            pagina = {"total": 0, "offset": int(offset), "limite": int(limite),
                      "somente_finais": bool(somente_finais),
                      "ordem": "mais_recentes_primeiro"}
            if lote_id:
                if somente_finais:
                    total_esperado = sum(
                        int(status.get(chave) or 0)
                        for chave in ("concluidas", "bloqueadas", "interrompidas", "falhas")
                    )
                else:
                    total_esperado = int(status.get("linhas") or 0)
                bruto, pagina = self._ler_pagina_mais_recente(
                    lote_id, offset, limite, somente_finais, total_esperado
                )
                itens = self._linhas_com_rotulos(bruto)
            por_id = {str(x.get("linha_id")): x for x in itens}
            correntes = status.get("corrente") or []
            linha_atual = None
            if correntes:
                corrente = correntes[0]
                linha_atual = por_id.get(str(corrente.get("linha_id")))
                if linha_atual is None:
                    linha_atual = self._linhas_com_rotulos([corrente])[0]
                else:
                    linha_atual.update({k: v for k, v in corrente.items() if k not in linha_atual})
            resposta = {
                **status, "ok": True, "itens": itens, "linha_atual": linha_atual,
                "paginacao": pagina,
                "totais": self._totais_fila(status),
                "publicacao": "SEM PUBLICAÇÃO", "pode_publicar": False,
                "origem": "clube_novo -> contrato V5 paginado -> worker local V3 -> Bonificador",
            }
            self._guardar_painel_confirmado(
                self._chave_painel_fila(offset, limite, somente_finais), resposta
            )
            return resposta
        except ErroDaInterface as erro:
            if erro.status >= 500:
                self._registrar_indisponibilidade_banco(erro)
                return self._painel_banco_indisponivel(erro, offset, limite, somente_finais)
            raise

    def eventos_fila(self, offset=0, limite=100):
        status = self._status_fila()
        if not status.get("disponivel"):
            return {"ok": True, "disponivel": False, "estado": status["estado"],
                    "itens": [], "mensagem": status["mensagem"], "origem": status["origem"]}
        lote_id = status.get("lote_id")
        if not lote_id:
            return {"ok": True, "disponivel": True, "estado": status["estado"], "itens": []}
        eventos = self.gateway.rpc("otimizador_producao_eventos_paginados_v5", {
            "p_lote_id": lote_id, "p_offset": int(offset), "p_limite": int(limite),
        }) or {}
        if eventos.get("contrato") != "otimizador_fila_producao_v5":
            raise ErroDaInterface("eventos paginados da fila V5 inesperados", 503)
        return {"ok": True, "disponivel": True, "estado": status["estado"],
                "itens": eventos.get("itens") or [], "total": eventos.get("total", 0),
                "offset": eventos.get("offset", offset), "limite": eventos.get("limite", limite),
                "origem": "eventos persistidos em clube_novo"}

    def resultados_fila(self, offset=0, limite=100):
        painel = self.painel_fila(offset=offset, limite=limite, somente_finais=True)
        if not painel.get("disponivel"):
            return {"ok": True, "disponivel": False, "estado": painel["estado"],
                    "mensagem": painel["mensagem"], "itens": [], "publicacao": "SEM PUBLICAÇÃO"}
        return {"ok": True, "disponivel": True, "estado": painel["estado"],
                "mensagem": painel.get("mensagem"), "itens": painel.get("itens") or [],
                "paginacao": painel.get("paginacao") or {},
                "publicacao": "SEM PUBLICAÇÃO", "pode_publicar": False,
                "lote_id": painel.get("lote_id"), "contrato": painel.get("contrato")}

    def _acao_de_inicio(self, status):
        acoes = status["acoes"]
        if acoes.get("iniciar") is True:
            return "iniciar"
        if acoes.get("retomar") is True:
            return "retomar"
        raise ErroDaInterface("o selo do contrato não autoriza iniciar nem retomar este lote", 409)

    def _recuperacao_reserva_orfa_disponivel(self, status):
        """Só expõe recuperação manual se este serviço local não está trabalhando.

        O banco repete todos os selos e bloqueios pela RPC V9. Esta sondagem não
        muda a fila; ela só evita oferecer recuperação enquanto este mesmo
        computador ainda possui worker ou preparador ativo.
        """
        if self._worker_ativo() or self._preparador_ativo():
            return False
        if (status.get("estado_lote") or status.get("estado")) not in {"pausando", "encerrando"}:
            return False
        correntes = status.get("corrente") or []
        return (len(correntes) == 1
                and correntes[0].get("estado") == "processando"
                and correntes[0].get("linha_id") is not None)

    def _reassumir_esteira_local_disponivel(self, status):
        """Permite retomar somente o worker perdido deste computador.

        Um lote permanece ``rodando`` no banco quando o aplicativo local foi
        fechado ou reiniciado. A retomada só é oferecida sem reserva ativa, para
        não disputar uma linha calculada em outro computador. A reserva V6 do
        banco continua sendo a autoridade final de exclusividade.
        """
        estado = status.get("estado_lote") or status.get("estado")
        try:
            pendentes = int(status.get("pendentes") or 0)
            processando = int(status.get("processando") or 0)
        except (TypeError, ValueError):
            return False
        return (
            status.get("tipo_lote") == "integral"
            and estado == "rodando"
            and status.get("pode_publicar") is False
            and pendentes > 0
            and processando == 0
            and not self._worker_ativo()
            and not self._preparador_ativo()
        )

    @staticmethod
    def _estado_local(etapa, lote_id=None, item=None, detalhe=None):
        item = item or {}
        agora = time.time()
        estado = {
            "etapa": str(etapa or "aguardando"),
            "lote_id": str(lote_id) if lote_id else None,
            "linha_id": item.get("linha_id"),
            "card_id": str(item["card_id"]) if item.get("card_id") is not None else None,
            "funcao_id": item.get("funcao_id"),
            "posicao_id": item.get("posicao_id"),
            "atualizado_em_epoch": agora,
            "inicio_linha_epoch": None,
            "detalhe": str(detalhe)[:1000] if detalhe else None,
        }
        return estado

    @staticmethod
    def _copia_estado_local(estado):
        return dict(estado or {})

    def _progresso_worker(self, worker, etapa, item=None, detalhe=None):
        """Recebe marcos reais do worker, sem consultar nem mudar a fila."""
        trava = getattr(self, "_worker_lock", None)
        if trava is None:
            return
        with trava:
            if getattr(self, "_worker_lote_id", None) != worker.lote_id:
                return
            anterior = self._copia_estado_local(getattr(self, "_worker_estado", {}))
            atual = self._estado_local(etapa, worker.lote_id, item, detalhe)
            if item is None:
                atual.update({
                    "linha_id": anterior.get("linha_id"),
                    "card_id": anterior.get("card_id"),
                    "funcao_id": anterior.get("funcao_id"),
                    "posicao_id": anterior.get("posicao_id"),
                    "inicio_linha_epoch": anterior.get("inicio_linha_epoch"),
                })
            elif etapa in {"linha_reservada", "calculando"}:
                atual["inicio_linha_epoch"] = time.time()
            self._worker_estado = atual

    def _worker_ativo(self):
        thread = getattr(self, "_worker_thread", None)
        return bool(thread and thread.is_alive())

    def _preparador_ativo(self):
        thread = getattr(self, "_preparo_thread", None)
        return bool(thread and thread.is_alive())

    def _worker_encerrado(self, worker, _resultado):
        with self._worker_lock:
            if self._worker_lote_id == worker.lote_id:
                self._progresso_worker(worker, "encerrado")
                self._worker_thread = None
                self._worker_lote_id = None

    def _preparador_encerrado(self, preparador, _resultado):
        with self._worker_lock:
            if self._preparo_lote_id == preparador.lote_id:
                self._preparo_thread = None
                self._preparo_lote_id = None

    def _iniciar_worker_producao(self, lote_id, esteira=False):
        with self._worker_lock:
            if self._preparador_ativo():
                if self._preparo_lote_id != str(lote_id) or not esteira:
                    raise ErroDaInterface("a preparação integral ativa pertence a outro modo/lote", 409)
            if self._worker_ativo():
                if self._worker_lote_id != str(lote_id):
                    raise ErroDaInterface("já existe worker local para outro lote V3", 409)
                return
            from fila_producao_v3 import WorkerFilaProducaoV3
            worker = WorkerFilaProducaoV3(
                self.gateway, str(lote_id), self._worker_encerrado, esteira=esteira,
                ao_progresso=self._progresso_worker,
            )
            thread = threading.Thread(target=worker.executar, name="otimizador-fila-v3", daemon=True)
            self._worker_lote_id = str(lote_id)
            self._worker_thread = thread
            self._worker_estado = self._estado_local("iniciando", lote_id)
            thread.start()

    def _iniciar_preparador_integral(self, lote_id, esteira=False):
        with self._worker_lock:
            if self._worker_ativo():
                if self._worker_lote_id != str(lote_id) or not esteira:
                    raise ErroDaInterface("o worker ativo pertence a outro modo/lote", 409)
            if self._preparador_ativo():
                if self._preparo_lote_id != str(lote_id):
                    raise ErroDaInterface("já existe preparação local para outro lote", 409)
                return
            from preparo_fila_integral_v5 import PreparadorFilaIntegralV5
            preparador = PreparadorFilaIntegralV5(
                self.gateway, str(lote_id), self._preparador_encerrado, esteira=esteira,
            )
            thread = threading.Thread(
                target=preparador.executar,
                name="otimizador-esteira-preparo-v6" if esteira else "otimizador-preparo-v5",
                daemon=True,
            )
            self._preparo_lote_id = str(lote_id)
            self._preparo_thread = thread
            thread.start()

    def _iniciar_esteira_integral(self, lote_id):
        """Liga produtor e consumidor do mesmo lote integral, por IDs selados."""
        resposta = self.gateway.rpc("otimizador_producao_iniciar_esteira_v6", {
            "p_lote_id": lote_id,
        }) or {}
        if resposta.get("contrato") != "otimizador_fila_producao_v5":
            raise ErroDaInterface("o contrato não confirmou o início da esteira V6", 503)
        if resposta.get("pode_publicar") is not False:
            raise ErroDaInterface("a esteira tentou habilitar publicação", 409)
        self._iniciar_preparador_integral(lote_id, esteira=True)
        self._iniciar_worker_producao(lote_id, esteira=True)
        return resposta

    @staticmethod
    def _formula_e_versao_local():
        from fila_producao_v3 import FORMULA_APROVADA, MOTOR_VERSAO, formula_fingerprint
        if formula_fingerprint() != FORMULA_APROVADA:
            raise ErroDaInterface("a fórmula local não confere com o selo aprovado", 409)
        return FORMULA_APROVADA, MOTOR_VERSAO

    def criar_fila(self):
        status = self._status_fila()
        if not status.get("disponivel"):
            raise ErroDaInterface(status["mensagem"], 409)
        if status.get("acoes", {}).get("criar") is not True:
            raise ErroDaInterface("o contrato não autoriza criar outro lote integral", 409)
        formula, motor_versao = self._formula_e_versao_local()
        import uuid
        prevoo = self.gateway.rpc("otimizador_producao_prevoo_integral_v5", {}) or {}
        if (prevoo.get("contrato") != "otimizador_fila_producao_v5"
                or not (prevoo.get("gate_regua") or {}).get("pode_rodar")):
            raise ErroDaInterface("pré-voo integral recusou a criação da fila", 409)
        criada = self.gateway.rpc("otimizador_producao_criar_lote_integral_v5", {
            "p_lote_id": str(uuid.uuid4()), "p_formula_fingerprint": formula,
            "p_motor_versao": motor_versao,
        }) or {}
        if criada.get("contrato") != "otimizador_fila_producao_v5" or not criada.get("lote_id"):
            raise ErroDaInterface("o contrato não confirmou a criação da fila integral", 503)
        self._iniciar_esteira_integral(criada["lote_id"])
        return self.painel_fila()

    def iniciar_fila(self):
        status = self._status_fila()
        if not status.get("disponivel"):
            raise ErroDaInterface(status["mensagem"], 409)
        if status.get("acoes", {}).get("criar") is True:
            status = self.criar_fila()
            return status
        estado = status.get("estado_lote") or status.get("estado")
        if estado in {"preparando", "preparo_pausado"}:
            self._iniciar_esteira_integral(status.get("lote_id"))
            return self.painel_fila()
        if estado == "rodando" and status.get("tipo_lote") == "integral":
            if not self._reassumir_esteira_local_disponivel(status):
                raise ErroDaInterface(
                    "a esteira já está rodando, mas não há retomada local segura "
                    "enquanto existir uma reserva ou worker ativo",
                    409,
                )
            self._iniciar_preparador_integral(status.get("lote_id"), esteira=True)
            self._iniciar_worker_producao(status.get("lote_id"), esteira=True)
            return self.painel_fila()
        acao = self._acao_de_inicio(status)
        lote_id = status.get("lote_id")
        resposta = self.gateway.rpc("otimizador_producao_controlar_lote_v3", {
            "p_lote_id": lote_id, "p_acao": acao, "p_confirmado": False,
        }) or {}
        if resposta.get("contrato") != "otimizador_fila_producao_v3":
            raise ErroDaInterface("o contrato não confirmou o início da fila V3", 503)
        preparo_pendente = int((status.get("preparo") or {}).get("pendentes") or 0)
        if status.get("tipo_lote") == "integral" and preparo_pendente > 0:
            self._iniciar_preparador_integral(lote_id, esteira=True)
            self._iniciar_worker_producao(lote_id, esteira=True)
        else:
            self._iniciar_worker_producao(lote_id)
        return self.painel_fila()

    def pausar_fila(self):
        status = self._status_fila()
        if not status.get("disponivel") or status.get("acoes", {}).get("pausar") is not True:
            raise ErroDaInterface("o contrato não autoriza pausar este lote", 409)
        if (status.get("estado_lote") or status.get("estado")) == "preparando":
            self.gateway.rpc("otimizador_producao_controlar_preparo_v5", {
                "p_lote_id": status.get("lote_id"), "p_acao": "pausar",
            })
            return self.painel_fila()
        self.gateway.rpc("otimizador_producao_controlar_lote_v3", {
            "p_lote_id": status.get("lote_id"), "p_acao": "pausar", "p_confirmado": False,
        })
        return self.painel_fila()

    def recuperar_reserva_orfa(self, confirmado):
        """Devolve uma única reserva abandonada ao lote pausado, pela RPC V9."""
        if confirmado is not True:
            raise ErroDaInterface("Recuperar exige confirmação explícita", 409)
        status = self._status_fila()
        if not status.get("disponivel") or not self._recuperacao_reserva_orfa_disponivel(status):
            raise ErroDaInterface("não existe reserva órfã local elegível para recuperação", 409)
        corrente = (status.get("corrente") or [None])[0]
        if not corrente:
            raise ErroDaInterface("a linha órfã não foi localizada no contrato", 409)
        resposta = self.gateway.rpc("otimizador_producao_recuperar_reserva_orfa_v9", {
            "p_lote_id": status.get("lote_id"),
            "p_linha_id": int(corrente["linha_id"]),
            "p_confirmado": True,
        }) or {}
        if resposta.get("contrato") != "otimizador_fila_producao_v5":
            raise ErroDaInterface("o contrato não confirmou a recuperação da reserva", 503)
        if (resposta.get("estado_lote") or resposta.get("estado")) != "pausado":
            raise ErroDaInterface("a reserva foi tratada, mas o lote não ficou pausado", 503)
        return self.painel_fila()

    def parar_fila(self, confirmado):
        if confirmado is not True:
            raise ErroDaInterface("Parar exige confirmação explícita", 409)
        status = self._status_fila()
        if (status.get("estado_lote") or status.get("estado")) in {"preparando", "preparo_pausado"}:
            raise ErroDaInterface("a preparação não calcula cartas; pause-a e não há lote a encerrar", 409)
        if not status.get("disponivel") or status.get("acoes", {}).get("parar") is not True:
            raise ErroDaInterface("o contrato não autoriza encerrar este lote", 409)
        self.gateway.rpc("otimizador_producao_controlar_lote_v3", {
            "p_lote_id": status.get("lote_id"), "p_acao": "parar", "p_confirmado": True,
        })
        return self.painel_fila()

    def abrir_console_fila(self):
        raise ErroDaInterface("a fila integral é operada pelo painel; não existe lançador .bat produtivo", 409)

    def saude(self):
        # Esta rota é usada pelo ícone para reencontrar um serviço que já está
        # executando. Ela precisa responder mesmo quando uma consulta extensa
        # de régua/fila estiver em curso; os gates completos continuam nas
        # rotas próprias do painel.
        trava = getattr(self, "_worker_lock", None)
        if trava is None:
            worker_ativo = False
            preparador_ativo = False
            worker = self._copia_estado_local(getattr(self, "_worker_estado", {}))
            preparador = self._copia_estado_local(getattr(self, "_preparo_estado", {}))
            iniciado_em = getattr(self, "_servidor_iniciado_em", None)
        else:
            with trava:
                worker_ativo = self._worker_ativo()
                preparador_ativo = self._preparador_ativo()
                worker = self._copia_estado_local(getattr(self, "_worker_estado", {}))
                preparador = self._copia_estado_local(getattr(self, "_preparo_estado", {}))
                iniciado_em = getattr(self, "_servidor_iniciado_em", None)
        agora = time.time()
        inicio_linha = worker.get("inicio_linha_epoch")
        decorrido = (max(0, int(agora - inicio_linha))
                     if worker_ativo and isinstance(inicio_linha, (int, float)) else None)
        if worker_ativo:
            linha = worker.get("linha_id")
            etapa = worker.get("etapa") or "trabalhando"
            resumo = (f"Worker ativo · linha {linha} · {etapa}"
                      if linha is not None else f"Worker ativo · {etapa}")
        elif preparador_ativo:
            resumo = "Preparador ativo · montando a fila"
        else:
            resumo = "Servidor local ativo · nenhum worker local"
        return {
            "ok": True, "aplicativo": APLICATIVO_ID,
            "versao_interface": INTERFACE_VERSAO,
            "contrato": "controle_local_loopback_v1",
            "pode_rodar": None,
            "modo": "consulta_local_v3; esteira_integral_v6_sem_publicacao",
            "acesso": "somente contratos selados",
            "servidor_iniciado_em_epoch": iniciado_em,
            "worker_ativo": worker_ativo,
            "worker": worker,
            "worker_resumo": resumo,
            "worker_decorrido_segundos": decorrido,
            "preparador_ativo": preparador_ativo,
            "preparador": preparador,
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
                    return self.responder_json(200, servico.criar_fila())
                if caminho.path == "/api/fila/preparar":
                    return self.responder_json(200, servico.iniciar_fila())
                if caminho.path == "/api/fila/iniciar":
                    return self.responder_json(200, servico.iniciar_fila())
                if caminho.path == "/api/fila/pausar":
                    return self.responder_json(200, servico.pausar_fila())
                if caminho.path == "/api/fila/recuperar":
                    return self.responder_json(200, servico.recuperar_reserva_orfa(corpo.get("confirmado") is True))
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
                    offset = int((params.get("offset") or ["0"])[0])
                    limite = int((params.get("limite") or ["100"])[0])
                    return self.responder_json(200, servico.painel_fila(offset=offset, limite=limite))
                if caminho.path == "/api/fila/eventos":
                    offset = int((params.get("offset") or ["0"])[0])
                    limite = int((params.get("limite") or ["100"])[0])
                    return self.responder_json(200, servico.eventos_fila(offset=offset, limite=limite))
                if caminho.path == "/api/resultados":
                    offset = int((params.get("offset") or ["0"])[0])
                    limite = int((params.get("limite") or ["100"])[0])
                    return self.responder_json(200, servico.resultados_fila(offset=offset, limite=limite))
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
