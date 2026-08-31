# -*- coding: utf-8 -*-
"""Preparador local da fila integral do Otimizador.

Este processo não chama ``roda_lote_v6`` e não calcula nenhuma build. Ele só
solicita ao contrato V5 uma fatia pequena de snapshots de entrada e linhas
canônicas, sempre por IDs. Quando a última fatia estiver pronta, o banco muda o
lote para ``parado``; uma segunda ação explícita é necessária para o worker V3
começar a calcular.
"""

from __future__ import annotations

import time
from typing import Callable


CONTRATO = "otimizador_fila_producao_v5"
TAMANHO_FATIA_PADRAO = 10


class FalhaPreparoIntegral(RuntimeError):
    """O contrato devolveu algo incompatível com a preparação selada."""


class PreparadorFilaIntegralV5:
    """Monta a fila integral em fatias sem iniciar o motor matemático."""

    def __init__(
        self,
        gateway,
        lote_id: str,
        ao_encerrar: Callable | None = None,
        tamanho_fatia: int = TAMANHO_FATIA_PADRAO,
        esperar: float = 0.05,
    ):
        self.gateway = gateway
        self.lote_id = str(lote_id)
        self.ao_encerrar = ao_encerrar
        self.tamanho_fatia = max(1, min(20, int(tamanho_fatia)))
        self.esperar = max(0.01, float(esperar))

    def _rpc(self, nome: str, corpo: dict | None = None) -> dict:
        return self.gateway.rpc(nome, corpo or {}) or {}

    def _status(self) -> dict:
        status = self._rpc("otimizador_producao_status_v5", {"p_lote_id": self.lote_id})
        if status.get("contrato") != CONTRATO or str(status.get("lote_id")) != self.lote_id:
            raise FalhaPreparoIntegral("contrato de status V5 inesperado")
        if status.get("pode_publicar") is not False:
            raise FalhaPreparoIntegral("o contrato V5 tentou habilitar publicação")
        return status

    def executar(self) -> dict:
        """Prepara até finalizar, pausar, falhar ou perder a conexão local."""
        final: dict = {}
        try:
            while True:
                status = self._status()
                estado = status.get("estado_lote") or status.get("estado")
                if estado != "preparando":
                    final = status
                    break
                resposta = self._rpc("otimizador_producao_preparar_fatia_v5", {
                    "p_lote_id": self.lote_id,
                    "p_limite": self.tamanho_fatia,
                })
                if resposta.get("contrato") != CONTRATO:
                    raise FalhaPreparoIntegral("fatia V5 retornou contrato inesperado")
                final = resposta
                estado = resposta.get("estado_lote") or resposta.get("estado")
                if estado != "preparando":
                    break
                # Cede o processo local para a atualização visual, sem inventar
                # progresso nem reexecutar nenhuma fatia.
                time.sleep(self.esperar)
            return final
        finally:
            if self.ao_encerrar:
                self.ao_encerrar(self, final)
