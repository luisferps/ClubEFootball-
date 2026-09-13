# -*- coding: utf-8 -*-
"""Renova fotografias pausadas; nunca reserva, calcula, envia ou publica."""
from __future__ import annotations
import json
import os
import shutil
import urllib.error
import urllib.request
import uuid
from pathlib import Path


class GatewayFotografia:
    PERMITIDAS = {
        "otimizador_producao_pacote_local_manifesto_v2",
        "otimizador_producao_pacote_local_cartas_v2",
        "otimizador_producao_pacote_local_linhas_v2",
    }

    def __init__(self, url, chave):
        self.url, self.chave = url, chave

    def rpc(self, nome, corpo=None):
        if nome not in self.PERMITIDAS:
            raise RuntimeError("renovação permite somente leitura das fotografias")
        headers = {"apikey": self.chave, "Content-Type": "application/json"}
        if not self.chave.startswith("sb_"):
            headers["Authorization"] = "Bearer " + self.chave
        pedido = urllib.request.Request(
            self.url + "/rest/v1/rpc/" + nome,
            data=json.dumps(corpo or {}).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(pedido, timeout=90) as resposta:
                return json.loads(resposta.read())
        except urllib.error.HTTPError as erro:
            raise RuntimeError(f"fotografia recusada pelo banco: HTTP {erro.code}") from erro


def _conferir_caminho(caminho: Path, raiz: Path) -> None:
    if not caminho.resolve().is_relative_to(raiz.resolve()):
        raise RuntimeError("caminho de renovação escapou da pasta do Otimizador")


def renovar(raiz: Path, lotes: list[str], api, gateway=None, *, antepor=False, preservar_ordem=False):
    from fila_local_v1 import PacoteLocalV1
    from empacotar_fila_integral_portatil_v1 import empacotar
    operacao = api.pasta_operacao(raiz)
    lotes = [str(uuid.UUID(lote)) for lote in lotes]
    if not lotes or len(lotes) != len(set(lotes)):
        raise api.FalhaOperacao("informe lotes distintos para renovar")
    if gateway is None:
        url, chave, _ = api._ler_config(raiz, operacao)
        gateway = GatewayFotografia(url, chave)
    revisao = uuid.uuid4().hex
    staging = operacao / "RENOVACOES" / revisao
    staging.mkdir(parents=True, exist_ok=False)
    ativos, preparados, vazios = [], [], []
    # A trava usada pelo processador explícito e global impede troca em uso.
    with api.trava_exclusiva(operacao / "PROCESSADOR-GLOBAL.lock", "renovação de pacotes"):
        arquivo_selecao = operacao / "FILA-ATIVA.json"
        selecao_anterior = api.ler_json(arquivo_selecao) if arquivo_selecao.exists() else {}
        antigos = selecao_anterior.get("lotes", [])
        if preservar_ordem and (antepor or lotes != antigos):
            raise api.FalhaOperacao("renovacao sem reordenar exige exatamente a fila existente")
        if antepor and (selecao_anterior.get("contrato") != "prioridade_orcamento_v1"
                       or not isinstance(antigos, list) or not antigos
                       or len(set(antigos)) != len(antigos) or set(antigos) & set(lotes)):
            raise api.FalhaOperacao("anteposição exige fila anterior válida e lotes corretivos novos")
        for lote in lotes:
            manifesto = gateway.rpc("otimizador_producao_pacote_local_manifesto_v2", {"p_lote_id": lote})
            if manifesto.get("prioridade_contrato") != "prioridade_orcamento_v1":
                raise api.FalhaOperacao("banco ainda não disponibilizou o contrato de prioridade física")
            if not manifesto.get("prioridade_fingerprint"):
                raise api.FalhaOperacao("banco não disponibilizou o selo da prioridade; renovação recusada")
            if int(manifesto.get("linhas_total") or 0) == 0:
                vazios.append(lote)
                continue
            print(f'Baixando fotografia do lote {lote}...', flush=True)
            fonte = PacoteLocalV1.criar_do_contrato(
                gateway, lote, staging,
                ao_progresso=lambda etapa, feitas, total: print(
                    f'{etapa}: {feitas}/{total}', flush=True))
            destino = empacotar(staging, lote)
            pacote = PacoteLocalV1(destino)
            pacote.validar_integridade()
            api.ordenar_fila_global([pacote], {})
            depois = gateway.rpc("otimizador_producao_pacote_local_manifesto_v2", {"p_lote_id": lote})
            for campo in ("lote_fingerprint", "formula_fingerprint", "contrato_fingerprint",
                          "motor_versao", "linhas_total", "cartas_total", "prioridade_contrato", "prioridade_fingerprint"):
                if depois.get(campo) != fonte.manifesto.get(campo):
                    raise api.FalhaOperacao(f"fotografia mudou durante a renovação: {lote}")
            preparados.append((lote, destino))
            ativos.append(lote)
        if not ativos and not preservar_ordem:
            raise api.FalhaOperacao("nenhuma linha com orçamento comprovado está pendente nos lotes informados")
        prioritarios = selecao_anterior.get("lotes_prioritarios", [])
        if preservar_ordem:
            ativos = list(antigos)
        if antepor:
            prioritarios = ativos + prioritarios
            ativos = ativos + antigos
            # Os lotes antigos sem pendencias continuam sem pendencias.
            # A renovacao acima consultou apenas o prefixo novo; nao pode
            # reativar fotografias antigas de lotes ja encerrados.
            vazios += [lote for lote in selecao_anterior.get("lotes_sem_pendentes", [])
                       if lote in antigos and lote not in vazios]
        else:
            prioritarios = [lote for lote in prioritarios if lote in ativos]
        # Valida todos antes de ativar qualquer um; versões anteriores ficam
        # preservadas. RESULTADOS-JSON e seus recibos não participam da troca.
        anteriores = staging / "ANTERIORES"
        anteriores.mkdir()
        trocados = []
        try:
            for lote, fonte in preparados:
                for base_nome, base in (("operacao", operacao), ("raiz", raiz)):
                    destino = base / "PACOTE-FILA-INTEGRAL" / lote
                    destino.parent.mkdir(parents=True, exist_ok=True)
                    copia = staging / ("instalar-" + base_nome + "-" + lote)
                    shutil.copytree(fonte, copia)
                    anterior = anteriores / (base_nome + "-" + lote)
                    for caminho in (destino, copia, anterior):
                        _conferir_caminho(caminho, raiz)
                    if destino.exists():
                        destino.rename(anterior)
                    try:
                        copia.rename(destino)
                    except BaseException:
                        if anterior.exists():
                            anterior.rename(destino)
                        raise
                    trocados.append((destino, anterior))
            selecao = operacao / "FILA-ATIVA.json"
            if selecao.exists():
                shutil.copy2(selecao, anteriores / "FILA-ATIVA.json")
            api.gravar_json_atomico(selecao, {
                "contrato": "prioridade_orcamento_v1", "revisao": revisao,
                "lotes": ativos, "lotes_sem_pendentes": vazios, "renovado_em_utc": api.agora_utc(),
                "lotes_prioritarios": prioritarios,
                "worker_iniciado": False,
            })
        except BaseException:
            # Move as cópias novas para staging e restaura as antigas.
            for destino, anterior in reversed(trocados):
                _conferir_caminho(destino, raiz)
                _conferir_caminho(anterior, raiz)
                destino.rename(staging / ("rejeitado-" + uuid.uuid4().hex))
                if anterior.exists():
                    anterior.rename(destino)
            raise
    resultado = {"revisao": revisao, "lotes": ativos, "sem_pendentes": vazios,
                 "anteriores": str(anteriores), "worker_iniciado": False}
    api.gravar_json_atomico(staging / "RENOVACAO.json", resultado)
    print(json.dumps(resultado, ensure_ascii=False), flush=True)
    return 0
