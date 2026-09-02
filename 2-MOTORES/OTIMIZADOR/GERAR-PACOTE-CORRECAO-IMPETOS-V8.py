# -*- coding: utf-8 -*-
"""Baixa e empacota uma correção já selada, sem iniciar cálculo ou envio.

Este utilitário é usado somente no computador que tem o ``config.txt`` local.
Ele gera uma pasta portátil dentro de ``PACOTE-FILA-INTEGRAL`` para ser copiada
ao computador dos motores. Não toca ``RESULTADOS-JSON`` e não chama as portas
de reservar, calcular, concluir ou publicar.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


RAIZ_MOTOR = Path(__file__).resolve().parent
if str(RAIZ_MOTOR) not in sys.path:
    sys.path.insert(0, str(RAIZ_MOTOR))

from empacotar_fila_integral_portatil_v1 import empacotar  # noqa: E402
from fila_local_v1 import PacoteLocalV1  # noqa: E402


class ErroPacoteCorrecao(RuntimeError):
    pass


def _config_local() -> tuple[str, str]:
    candidatos = (
        RAIZ_MOTOR / "OPERACAO-LOCAL-JSON" / "config.txt",
        RAIZ_MOTOR / "config.txt",
        RAIZ_MOTOR.parent / "config.txt",
    )
    for caminho in candidatos:
        if not caminho.is_file():
            continue
        valores: dict[str, str] = {}
        for texto in caminho.read_text(encoding="utf-8").splitlines():
            linha = texto.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                chave, valor = linha.split("=", 1)
                valores[chave.strip()] = valor.strip()
        url = valores.get("SUPABASE_URL", "").rstrip("/")
        chave = valores.get("SUPABASE_KEY", "")
        if url and chave and "COLE_AQUI" not in chave:
            return url, chave
    raise ErroPacoteCorrecao(
        "config.txt local não encontrado ou incompleto; ele pode ficar em "
        "OPERACAO-LOCAL-JSON, OTIMIZADOR ou 2-MOTORES"
    )


class GatewaySomenteFotografia:
    """Allowlist mínima: não contém nenhuma chamada que altere a fila."""

    PERMITIDAS = {
        "otimizador_producao_pacote_local_manifesto_v2",
        "otimizador_producao_pacote_local_cartas_v2",
        "otimizador_producao_pacote_local_linhas_v2",
    }

    def __init__(self, url: str, chave: str):
        self.url = url
        self.chave = chave

    def rpc(self, nome: str, corpo: dict[str, Any] | None = None) -> Any:
        if nome not in self.PERMITIDAS:
            raise ErroPacoteCorrecao("esta rotina não permite alterar a fila")
        cabecalhos = {
            "apikey": self.chave,
            "Content-Type": "application/json",
            "User-Agent": "ClubEfootballOtimizadorPacoteCorrecaoV8/1.0",
        }
        if not self.chave.startswith("sb_"):
            cabecalhos["Authorization"] = "Bearer " + self.chave
        pedido = urllib.request.Request(
            self.url + "/rest/v1/rpc/" + nome,
            data=json.dumps(corpo or {}, ensure_ascii=False).encode("utf-8"),
            headers=cabecalhos,
            method="POST",
        )
        try:
            with urllib.request.urlopen(pedido, timeout=60) as resposta:
                texto = resposta.read().decode("utf-8")
        except urllib.error.HTTPError as erro:
            raise ErroPacoteCorrecao(
                f"o banco recusou a fotografia do pacote (HTTP {erro.code})"
            ) from erro
        except (TimeoutError, OSError) as erro:
            raise ErroPacoteCorrecao(
                "não foi possível baixar a fotografia do pacote agora"
            ) from erro
        return json.loads(texto) if texto.strip() else None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera apenas um pacote local selado para uma correção do Otimizador."
    )
    parser.add_argument("lote_id", help="UUID do lote corretivo já pausado")
    args = parser.parse_args()

    url, chave = _config_local()
    gateway = GatewaySomenteFotografia(url, chave)
    pacote_v2 = PacoteLocalV1.criar_do_contrato(gateway, args.lote_id, RAIZ_MOTOR)
    destino = empacotar(RAIZ_MOTOR, args.lote_id)
    pacote = PacoteLocalV1(destino)
    pacote.validar_integridade()
    print(json.dumps({
        "ok": True,
        "lote_id": pacote.lote_id,
        "pasta": str(destino),
        "cartas": pacote.manifesto["arquivos"]["cartas"]["total"],
        "linhas": pacote.manifesto["arquivos"]["linhas"]["total"],
        "fotografia_v2": str(pacote_v2.pasta),
        "alterou_fila": False,
        "iniciou_processamento": False,
        "enviou_resultados": False,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ErroPacoteCorrecao as erro:
        print("ERRO:", erro, file=sys.stderr)
        raise SystemExit(2)
