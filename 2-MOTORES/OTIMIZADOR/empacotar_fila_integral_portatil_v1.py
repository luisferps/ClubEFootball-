# -*- coding: utf-8 -*-
"""Converte uma fotografia selada V2 em pacote portátil fatiado V3.

O pacote produzido fica dentro de ``PACOTE-FILA-INTEGRAL`` e contém somente
entrada canônica, régua, selos e catálogos da fila. Não copia ``config.txt``,
reservas, resultados, ou qualquer credencial. O estado de execução é criado
em ``runtime/fila-local`` na máquina que efetivamente rodar o Otimizador.

Cada arquivo físico tem no máximo mil registros: a máquina de destino só
precisa receber a pasta inteira, sem refazer uma exportação da fila no banco.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path

from fila_local_v1 import (
    CONTRATO_PACOTE_LOCAL_V2,
    PASTA_PACOTE_PORTATIL,
    PacoteLocalV1,
    TAMANHO_BLOCO_PORTATIL,
    VERSAO_PACOTE_LOCAL_V2,
    VERSAO_PACOTE_LOCAL_V3,
    _gravar_json_atomico,
)


def _fatiar_jsonl(origem: Path, destino: Path, tamanho: int) -> dict:
    """Copia bytes já selados sem parse/reformatação, em fatias ordenadas."""
    destino.mkdir(parents=True, exist_ok=True)
    agregado = hashlib.sha256()
    fatias: list[dict] = []
    total = 0
    indice = 0
    entrada = origem.open("rb")
    try:
        while True:
            linhas = []
            for _ in range(tamanho):
                linha = entrada.readline()
                if not linha:
                    break
                linhas.append(linha)
            if not linhas:
                break
            indice += 1
            nome = f"{indice:06d}.jsonl"
            caminho = destino / nome
            temporario = caminho.with_name(caminho.name + ".tmp-" + uuid.uuid4().hex)
            digest = hashlib.sha256()
            try:
                with temporario.open("wb") as saida:
                    for linha in linhas:
                        saida.write(linha)
                        digest.update(linha)
                        agregado.update(linha)
                os.replace(temporario, caminho)
            finally:
                if temporario.exists():
                    temporario.unlink(missing_ok=True)
            fatias.append({"nome": nome, "total": len(linhas), "sha256": digest.hexdigest()})
            total += len(linhas)
    finally:
        entrada.close()
    return {
        "diretorio": destino.name,
        "total": total,
        "sha256": agregado.hexdigest(),
        "tamanho_maximo": tamanho,
        "fatias": fatias,
    }


def empacotar(raiz: Path, lote_id: str, tamanho: int = TAMANHO_BLOCO_PORTATIL) -> Path:
    raiz = Path(raiz).resolve()
    if tamanho != TAMANHO_BLOCO_PORTATIL:
        raise ValueError(f"o pacote portátil usa exatamente {TAMANHO_BLOCO_PORTATIL} linhas por bloco")
    origem = raiz / "runtime" / "fila-local" / str(lote_id)
    fonte = PacoteLocalV1(origem)
    fonte.validar_integridade()
    if int(fonte.manifesto.get("versao_pacote") or 0) != VERSAO_PACOTE_LOCAL_V2:
        raise ValueError("a origem precisa ser a fotografia V2 selada, não um pacote já fatiado")
    destino = raiz / PASTA_PACOTE_PORTATIL / str(lote_id)
    if destino.exists():
        existente = PacoteLocalV1(destino)
        existente.validar_integridade()
        if existente.manifesto.get("lote_fingerprint") != fonte.manifesto.get("lote_fingerprint"):
            raise ValueError("já existe pacote portátil de outro selo para este lote")
        return destino

    temporario = destino.with_name(destino.name + ".preparando-" + uuid.uuid4().hex)
    temporario.mkdir(parents=True, exist_ok=False)
    try:
        arquivos = {}
        for chave in ("cartas", "linhas"):
            meta = fonte.manifesto["arquivos"][chave]
            origem_arquivo = origem / str(meta["nome"])
            arquivos[chave] = _fatiar_jsonl(origem_arquivo, temporario / chave, tamanho)
            if arquivos[chave]["total"] != int(meta["total"]):
                raise ValueError(f"contagem de {chave} divergiu ao fatiar")
            if arquivos[chave]["sha256"] != str(meta["sha256"]):
                raise ValueError(f"hash de {chave} divergiu ao fatiar")

        manifesto = dict(fonte.manifesto)
        manifesto.update({
            "versao_pacote": VERSAO_PACOTE_LOCAL_V3,
            "formato": "fatias-1000-v1",
            "arquivos": arquivos,
            "portabilidade": {
                "entrada_inclusa": True,
                "credenciais_inclusas": False,
                "estado_de_execucao": "runtime/fila-local/<lote_id>",
                "envio": "processo separado; RPC idempotente em sublotes de até 100",
            },
        })
        _gravar_json_atomico(temporario / "manifesto.json", manifesto)
        _gravar_json_atomico(temporario / "LEIA-ME.json", {
            "lote_id": str(lote_id),
            "mensagem": "Copie a pasta OTIMIZADOR inteira. Este pacote já contém a fila e não contém credenciais.",
            "linhas_por_bloco": TAMANHO_BLOCO_PORTATIL,
            "cartas": arquivos["cartas"]["total"],
            "linhas": arquivos["linhas"]["total"],
        })
        PacoteLocalV1(temporario).validar_integridade()
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporario.rename(destino)
        return destino
    except Exception:
        shutil.rmtree(temporario, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Empacota a fila selada para cópia integral entre computadores.")
    parser.add_argument("lote_id", help="UUID do lote integral já fotografado")
    parser.add_argument("--raiz", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    destino = empacotar(args.raiz, args.lote_id)
    pacote = PacoteLocalV1(destino)
    print(json.dumps({
        "ok": True,
        "pasta": str(destino),
        "lote_id": pacote.lote_id,
        "cartas": pacote.manifesto["arquivos"]["cartas"]["total"],
        "linhas": pacote.manifesto["arquivos"]["linhas"]["total"],
        "blocos_linhas": len(pacote.manifesto["arquivos"]["linhas"]["fatias"]),
        "linhas_por_bloco": TAMANHO_BLOCO_PORTATIL,
        "credenciais_inclusas": False,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
