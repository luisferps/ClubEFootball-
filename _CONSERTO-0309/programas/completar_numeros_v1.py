# -*- coding: utf-8 -*-
"""Relê os JSONs já enviados e completa no banco os 26 atributos finais.

Por que este programa existe:

    Ate 02/09 a porta de importacao do banco lia seis campos do resultado
    (b1, barras, tecnico_id, habilidades, builds_comparadas, builds_possiveis)
    e ignorava o resto. O motor SEMPRE mandou tambem `vals_tela` — os 26
    atributos como o jogo os mostra — e `cadeia`, com peso e alvo de cada um.
    Esses dois sao insumo obrigatorio da tela V2, e ficaram de fora de todos os
    Builds gravados antes da correcao.

    A porta corrigida completa esses campos quando recebe de novo um resultado
    identico, byte a byte, de uma linha ja concluida. O ENVIAR-RESULTADOS
    normal nao serve para isso: ele so percorre PENDENTES, e o recibo local
    marca como confirmada qualquer linha ja aceita, entao ele nunca reenvia.

    Este programa faz so isso: percorre ENVIADOS e PENDENTES, manda cada item
    de novo pela mesma porta, e conta quantos Builds foram completados. Nao
    calcula nada, nao escolhe Build, nao publica, nao apaga arquivo nenhum.

Seguranca:

    A porta so aceita o reenvio quando o resultado bate byte a byte com o que
    ja esta selado. Se bater, ela preenche apenas os campos que estao vazios.
    Qualquer divergencia e recusada pelo proprio banco.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

NOME_PASTA = "OPERACAO-LOCAL-JSON"
CONTRATO = "otimizador_importacao_json_local_v1"


class Falha(RuntimeError):
    pass


def _raiz() -> Path:
    """Acha OPERACAO-LOCAL-JSON pelo diretorio atual, depois pelo do arquivo.

    O .bat da pasta de conserto faz `pushd` para OPERACAO-LOCAL-JSON e chama
    este programa de outro lugar, entao o diretorio atual e a pista boa. Se
    ele nao servir, cai para a pasta do proprio arquivo, que e como funciona
    quando o .py mora dentro de programas/.
    """
    candidatas = (Path.cwd().resolve(), Path(__file__).resolve().parent)
    for inicio in candidatas:
        for base in (inicio, *inicio.parents):
            if base.name == NOME_PASTA:
                return base
            if (base / NOME_PASTA).is_dir():
                return base / NOME_PASTA
    raise Falha(
        "nao encontrei a pasta " + NOME_PASTA + " a partir de " +
        str(Path.cwd()) + " nem de " + str(Path(__file__).resolve().parent))


def _config(operacao: Path) -> tuple[str, str]:
    candidatas = (
        operacao / "config.txt",
        operacao.parent / "config.txt",
        operacao.parent.parent / "config.txt",
    )
    for caminho in candidatas:
        if not caminho.is_file():
            continue
        valores: dict[str, str] = {}
        for texto in caminho.read_text(encoding="utf-8").splitlines():
            texto = texto.strip()
            if texto and not texto.startswith("#") and "=" in texto:
                chave, valor = texto.split("=", 1)
                valores[chave.strip()] = valor.strip()
        url = valores.get("SUPABASE_URL", "").strip().strip("[]")
        chave = valores.get("SUPABASE_KEY", "").strip()
        if url and chave and "COLE_AQUI" not in chave:
            return url.rstrip("/"), chave
    raise Falha("config.txt sem SUPABASE_URL e SUPABASE_KEY")


def _envelopes(pasta: Path) -> list[Path]:
    if not pasta.is_dir():
        return []
    return sorted(
        caminho for caminho in pasta.iterdir()
        if caminho.is_file()
        and caminho.name.startswith("resultado-")
        and caminho.suffix == ".json"
        and not caminho.name.endswith(".resumo.json")
    )


def _chamar(url: str, chave: str, lote: str, item: dict[str, Any]) -> dict[str, Any]:
    corpo = {
        "p_lote_id": lote,
        "p_linha_id": int(item["linha_id"]),
        "p_resultado": item["resultado"],
        "p_calculado_em_utc": item["calculado_em_utc"],
    }
    cabecalhos = {
        "apikey": chave,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "ClubEfootballCompletarNumerosV1/1.0",
    }
    if not chave.startswith("sb_"):
        cabecalhos["Authorization"] = "Bearer " + chave
    pedido = urllib.request.Request(
        url + "/rest/v1/rpc/otimizador_producao_importar_json_local_v1",
        data=json.dumps(corpo, ensure_ascii=False).encode("utf-8"),
        headers=cabecalhos,
        method="POST",
    )
    with urllib.request.urlopen(pedido, timeout=60) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


def main() -> int:
    operacao = _raiz()
    url, chave = _config(operacao)

    base = operacao / "RESULTADOS-JSON"
    if not base.is_dir():
        raise Falha("nao ha RESULTADOS-JSON nesta copia")

    lotes = sorted(p.name for p in base.iterdir() if p.is_dir())
    if len(sys.argv) > 1:
        lotes = [sys.argv[1]]
    if not lotes:
        raise Falha("nenhum lote em RESULTADOS-JSON")

    print("")
    print("=" * 62)
    print(" COMPLETAR OS 26 NUMEROS DOS RESULTADOS JA ENVIADOS")
    print("=" * 62)
    print("")

    total = completados = ja_tinha = recusados = 0
    inicio = time.monotonic()

    for lote in lotes:
        saida = base / lote
        arquivos = _envelopes(saida / "ENVIADOS") + _envelopes(saida / "PENDENTES")
        if not arquivos:
            continue
        print("Lote %s — %d arquivo(s)" % (lote[:8], len(arquivos)))

        for arquivo in arquivos:
            try:
                envelope = json.loads(arquivo.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as erro:
                print("  %s: nao consegui ler (%s)" % (arquivo.name, erro))
                continue
            itens = envelope.get("itens") or []
            if not itens:
                continue
            lote_do_arquivo = str(envelope.get("lote_id") or lote)

            for item in itens:
                total += 1
                try:
                    resposta = _chamar(url, chave, lote_do_arquivo, item)
                except urllib.error.HTTPError as erro:
                    recusados += 1
                    detalhe = erro.read().decode("utf-8", "replace")[:160]
                    print("  linha %s recusada (HTTP %d): %s"
                          % (item.get("linha_id"), erro.code, detalhe))
                    continue
                except (urllib.error.URLError, TimeoutError, OSError) as erro:
                    recusados += 1
                    print("  linha %s: rede incerta (%s)" % (item.get("linha_id"), erro))
                    continue

                if resposta.get("contrato") != CONTRATO:
                    recusados += 1
                    continue
                if resposta.get("numeros_completados") is True:
                    completados += 1
                else:
                    ja_tinha += 1

                if total % 250 == 0:
                    print("  ... %d conferidas, %d completadas (%.0fs)"
                          % (total, completados, time.monotonic() - inicio))

    print("")
    print("=" * 62)
    print(" RESULTADO")
    print("=" * 62)
    print(" Linhas conferidas ................ %d" % total)
    print(" Builds completados agora ......... %d" % completados)
    print(" Ja estavam completos ............. %d" % ja_tinha)
    print(" Recusados pelo banco ............. %d" % recusados)
    print(" Tempo ............................ %.0fs" % (time.monotonic() - inicio))
    print("")
    print(" Nenhum calculo foi refeito e nenhum arquivo foi apagado.")
    print("")
    return 0 if recusados == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Falha as erro:
        print("ERRO:", erro, file=sys.stderr)
        raise SystemExit(2)
