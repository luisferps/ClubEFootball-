# -*- coding: utf-8 -*-
"""Worker local da fila produtiva V3.

O browser nunca chama este módulo. Ele só é criado pelo servidor loopback após
o operador clicar em Iniciar/Retomar e fala exclusivamente com as RPCs V3
seladas. Não lê ``clube.*``, não grava direto no banco e não publica nada.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path


PASTA = Path(__file__).resolve().parent
CONTRATO = "otimizador_fila_producao_v3"
MOTOR_VERSAO = "otimizador-fila-producao-v3-local-20260831"
FORMULA_APROVADA = "7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad"


class FalhaFilaProducao(RuntimeError):
    """Falha fechada: não inicia uma linha com selo ou contrato divergente."""


def formula_fingerprint() -> str:
    """Assina as três peças matemáticas aprovadas, sem inferir nada da UI."""
    h = hashlib.sha256()
    for nome in ("equacao.py", "motor.py", "regua.py"):
        h.update(nome.encode("utf-8"))
        h.update((PASTA / nome).read_bytes())
    return h.hexdigest()


def _texto_erro(excecao: BaseException) -> str:
    texto = str(excecao).strip() or type(excecao).__name__
    return texto[:1000]


class WorkerFilaProducaoV3:
    """Uma reserva por vez; o banco decide exclusividade e estados."""

    def __init__(self, gateway, lote_id: str, ao_encerrar=None, esperar: float = 0.25,
                 esteira: bool = False, ao_progresso=None):
        self.gateway = gateway
        self.lote_id = str(lote_id)
        self.worker_id = str(uuid.uuid4())
        self.ao_encerrar = ao_encerrar
        self.esperar = max(0.05, float(esperar))
        self.esteira = bool(esteira)
        self.ao_progresso = ao_progresso
        self._runner = None

    def _progresso(self, etapa: str, item: dict | None = None, detalhe=None) -> None:
        """Espelha marcos já existentes para o painel local; nunca muda o cálculo."""
        if not self.ao_progresso:
            return
        try:
            self.ao_progresso(self, etapa, item, detalhe)
        except Exception:
            # Observabilidade não pode derrubar nem alterar uma linha da fila.
            pass

    def _rpc(self, nome: str, corpo: dict | None = None):
        return self.gateway.rpc(nome, corpo or {}) or {}

    def _contexto(self) -> dict:
        contexto = self._rpc("otimizador_producao_contexto_lote_v3", {
            "p_lote_id": self.lote_id,
        })
        if contexto.get("contrato") != CONTRATO or str(contexto.get("lote_id")) != self.lote_id:
            raise FalhaFilaProducao("contrato de contexto V3 inesperado")
        if contexto.get("formula_fingerprint") != FORMULA_APROVADA:
            raise FalhaFilaProducao("o lote não está selado com a fórmula aprovada")
        if formula_fingerprint() != contexto.get("formula_fingerprint"):
            raise FalhaFilaProducao("a fórmula local mudou depois do selo do lote")
        if contexto.get("motor_versao") != MOTOR_VERSAO:
            raise FalhaFilaProducao("a versão local do worker diverge do lote")
        if (contexto.get("impetos_condicionais") != "desligados"
                or contexto.get("pode_publicar") is not False):
            raise FalhaFilaProducao("o contexto V3 tentou habilitar uma saída não autorizada")
        regua = contexto.get("regua")
        if not isinstance(regua, dict) or (regua.get("gate") or {}).get("pode_rodar") is not True:
            raise FalhaFilaProducao("a fotografia da régua não está apta")
        return contexto

    def _preparar_executor(self, contexto: dict) -> None:
        import roda_lote_v6 as runner
        runner.prepara_lote_producao_v3(contexto["regua"])
        self._runner = runner

    def _reservar(self) -> dict:
        rpc = ("otimizador_producao_reservar_linha_v6"
               if self.esteira else "otimizador_producao_reservar_linha_v3")
        resposta = self._rpc(rpc, {
            "p_lote_id": self.lote_id,
            "p_worker_id": self.worker_id,
        })
        if resposta.get("contrato") != CONTRATO:
            raise FalhaFilaProducao("reserva retornou contrato inesperado")
        return resposta

    def _calcular(self, item: dict) -> dict:
        if item.get("impeto_condicional_codigo") is not None or item.get("impeto_condicional_nivel") is not None:
            raise FalhaFilaProducao("Ímpeto condicional chegou em uma linha V3")
        if self._runner is None:
            raise FalhaFilaProducao("executor V3 não foi preparado")
        carta = item.get("carta")
        if not isinstance(carta, dict):
            raise FalhaFilaProducao("a reserva não trouxe snapshot da carta")
        self._runner.carrega_carta_snapshot_producao_v3(carta)
        saida = self._runner.trabalha({
            "n": item["linha_id"], "card_id": item["card_id"],
            "funcao_id": item["funcao_id"], "posicao_id": item["posicao_id"],
            "impeto_condicional_codigo": None, "impeto_condicional_nivel": None,
            "origem": "fila_producao_v3",
        })
        if not isinstance(saida, dict):
            raise FalhaFilaProducao("o Otimizador não devolveu resultado")
        if saida.get("ERRO"):
            raise FalhaFilaProducao(str(saida["ERRO"]))
        saida.update({
            "card_id": str(item["card_id"]), "funcao_id": int(item["funcao_id"]),
            "posicao_id": int(item["posicao_id"]),
            "formula_fingerprint": item["formula_fingerprint"],
            "contrato_fingerprint": item["contrato_fingerprint"],
            "motor_versao": item["motor_versao"],
            "lote_fingerprint": item["lote_fingerprint"],
            "carta_entrada_fingerprint": item["carta_entrada_fingerprint"],
            "impeto_condicional_codigo": None,
            "impeto_condicional_nivel": None,
        })
        return saida

    def _concluir(self, item: dict, resultado: dict) -> dict:
        rpc = ("otimizador_producao_concluir_linha_v6"
               if self.esteira else "otimizador_producao_concluir_linha_v3")
        return self._rpc(rpc, {
            "p_lote_id": self.lote_id,
            "p_linha_id": item["linha_id"],
            "p_reserva_token": item["reserva_token"],
            "p_resultado": resultado,
        })

    def _bloquear(self, item: dict, motivo: str) -> dict:
        return self._rpc("otimizador_producao_bloquear_linha_v3", {
            "p_lote_id": self.lote_id,
            "p_linha_id": item["linha_id"],
            "p_reserva_token": item["reserva_token"],
            "p_motivo": motivo,
        })

    def _fechar_pausa_ou_encerramento(self) -> dict:
        estado = self._rpc("otimizador_producao_status_v3", {"p_lote_id": self.lote_id})
        if estado.get("contrato") != CONTRATO:
            raise FalhaFilaProducao("status do lote retornou contrato inesperado")
        lote_estado = estado.get("estado_lote")
        if lote_estado == "pausando" and not (estado.get("corrente") or []):
            return self._rpc("otimizador_producao_controlar_lote_v3", {
                "p_lote_id": self.lote_id, "p_acao": "confirmar_pausa", "p_confirmado": False,
            })
        if lote_estado == "encerrando" and not (estado.get("corrente") or []):
            return self._rpc("otimizador_producao_controlar_lote_v3", {
                "p_lote_id": self.lote_id, "p_acao": "confirmar_encerramento", "p_confirmado": True,
            })
        return estado

    def executar(self) -> dict:
        """Roda até concluir/pausar/encerrar, sempre uma linha reservada por vez."""
        final: dict = {}
        try:
            self._progresso("conferindo_selo")
            contexto = self._contexto()
            self._progresso("preparando_executor")
            self._preparar_executor(contexto)
            self._progresso("aguardando_linha")
            while True:
                item = self._reservar()
                if item.get("reservada") is not True:
                    estado = item.get("estado_lote")
                    if estado == "rodando":
                        # Outro worker pode estar terminando uma linha. Não calcula
                        # nem duplica; aguarda nova decisão atômica do banco.
                        self._progresso("aguardando_linha")
                        time.sleep(self.esperar)
                        continue
                    final = self._fechar_pausa_ou_encerramento()
                    self._progresso("encerrando", detalhe=final.get("estado_lote") or final.get("estado"))
                    break
                self._progresso("linha_reservada", item)
                try:
                    self._progresso("calculando", item)
                    resultado = self._calcular(item)
                except Exception as erro:
                    motivo = _texto_erro(erro)
                    self._progresso("bloqueando_linha", item, motivo)
                    self._bloquear(item, motivo)
                else:
                    self._progresso("gravando_resultado", item)
                    self._concluir(item, resultado)
                    self._progresso("linha_concluida", item)
                final = self._fechar_pausa_ou_encerramento()
                estado = final.get("estado_lote") or final.get("estado")
                if estado in {"pausado", "encerrado", "concluido", "falhou"}:
                    self._progresso("encerrando", detalhe=estado)
                    break
            return final
        except Exception as erro:
            motivo = _texto_erro(erro)
            self._progresso("falha_worker", detalhe=motivo)
            try:
                final = self._rpc("otimizador_producao_falhar_lote_v3", {
                    "p_lote_id": self.lote_id, "p_motivo": motivo,
                })
            except Exception:
                final = {"ok": False, "estado_lote": "falhou", "erro": motivo}
            return final
        finally:
            if self.ao_encerrar:
                self.ao_encerrar(self, final)


def resultado_serializavel(valor: dict) -> str:
    """Auxiliar de teste: garante que telemetria não leve objetos locais ao RPC."""
    return json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
