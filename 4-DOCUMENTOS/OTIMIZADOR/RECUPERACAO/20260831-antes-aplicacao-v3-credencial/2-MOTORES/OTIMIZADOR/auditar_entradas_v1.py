# -*- coding: utf-8 -*-
"""Auditoria somente leitura da ficha canônica V3 do Otimizador.

Esta ferramenta não abre fila, não calcula build e não consulta fonte histórica.
Cada aprovação decorre exclusivamente de IDs, cardinalidades e gates devolvidos
por ``public.otimizador_cartas_v3`` sobre ``clube_novo``.
"""

from __future__ import print_function

import argparse
import copy
import hashlib
import json
import sys
import urllib.error
import urllib.request


FONTE_NOVA = "public.otimizador_cartas_v3 -> clube_novo normalizado por IDs"
CONTRATO = "otimizador_entradas_v3"
CARDINALIDADES_ESPERADAS = {
    "atributos": 26,
    "corpo": 12,
    "posicoes": 12,
    "posicao_principal": 1,
    "pes": 3,
    "playstyles": 2,
}


def _json_canonico(valor):
    return json.dumps(valor, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def fingerprint(valor):
    return hashlib.sha256(_json_canonico(valor).encode("utf-8")).hexdigest()


def _ordenados(linhas, chaves):
    def chave(x):
        return tuple(x.get(k) for k in chaves)
    return sorted((linhas or []), key=chave)


def assinatura_calculo(carta):
    """Retrato dos insumos por ID; nunca inclui texto de apresentação."""
    return {
        "card_id": str(carta.get("card_id")),
        "atributos": _ordenados([
            {"indice_otimizador": x.get("indice_otimizador"),
             "codigo": x.get("codigo"), "bit": x.get("bit"),
             "valor": x.get("valor")}
            for x in (carta.get("atributos") or [])
        ], ("indice_otimizador",)),
        "corpo": _ordenados([
            {"pos": x.get("pos"), "codigo": x.get("codigo"),
             "valor": x.get("valor")}
            for x in (carta.get("corpo") or [])
        ], ("pos",)),
        "posicao_principal_id": carta.get("posicao_principal_id"),
        "posicoes": _ordenados([
            {"posicao_id": x.get("posicao_id"),
             "nivel_aptidao": x.get("nivel_aptidao")}
            for x in (carta.get("posicoes") or [])
        ], ("posicao_id",)),
        "habilidades": _ordenados([
            {"skill_id": h.get("skill_id"), "ordem": h.get("ordem"),
             "bit_na_carta": h.get("bit_na_carta"), "tipo": h.get("tipo"),
             "fabricavel": h.get("fabricavel"), "vetada": h.get("vetada")}
            for h in (carta.get("habilidades") or [])
        ], ("skill_id",)),
        "estilos_ia": _ordenados([
            {"bit_estilo_ia": x.get("bit_estilo_ia")}
            for x in (carta.get("estilos_ia") or [])
        ], ("bit_estilo_ia",)),
        "pes": _ordenados([
            {"campo": x.get("campo"), "valor": x.get("valor"),
             "codigo": x.get("codigo")}
            for x in (carta.get("pes") or [])
        ], ("campo",)),
        "playstyles": _ordenados([
            {"slot_fisico": x.get("slot_fisico"),
             "playstyle_id": x.get("playstyle_id")}
            for x in (carta.get("playstyles") or [])
        ], ("slot_fisico",)),
        "dimensoes": carta.get("dimensoes") or {},
        "escalares": carta.get("escalares") or {},
        "impetos": _ordenados([
            {"slot": x.get("slot"), "codigo_impeto": x.get("codigo_impeto"),
             "vaga": x.get("vaga"), "condicional": x.get("condicional")}
            for x in (carta.get("impetos") or [])
        ], ("slot",)),
    }


def _valida_cardinalidades(carta):
    atuais = carta.get("cardinalidades") or {}
    return {k: {"esperado": v, "atual": atuais.get(k)}
            for k, v in CARDINALIDADES_ESPERADAS.items()
            if atuais.get(k) != v}


def prova_renomeacao(carta):
    """Muda somente rótulos e confirma que a assinatura calculável não muda."""
    alterada = copy.deepcopy(carta)
    apresentacao = alterada.setdefault("apresentacao", {})
    for chave in list(apresentacao):
        if isinstance(apresentacao[chave], str):
            apresentacao[chave] = "RENOMEADO:" + apresentacao[chave]
    for colecao in ("atributos", "corpo", "habilidades", "posicoes",
                    "estilos_ia", "pes", "playstyles", "impetos"):
        for item in alterada.get(colecao) or []:
            for chave in list(item):
                if ("nome" in chave or "rotulo" in chave) and isinstance(item[chave], str):
                    item[chave] = "RENOMEADO:" + item[chave]
    return fingerprint(assinatura_calculo(carta)) == fingerprint(assinatura_calculo(alterada))


def audita_cartas_v3(pedidos, cartas):
    """Valida o contrato V3 por card_id, sem comparar com outra fonte."""
    ids = sorted(set(str(x).split("@")[0] for x in pedidos))
    por_id = {str(x.get("card_id")): x for x in (cartas or [])
               if isinstance(x, dict) and x.get("card_id") is not None}
    ocorrencias, cards, motivos = [], [], {}
    aptos = bloqueados = 0

    for card_id in ids:
        carta = por_id.get(card_id)
        if carta is None:
            ocorrencias.append({"card_id": card_id, "campo": "$card",
                                "status": "ausente_no_contrato_v3",
                                "origem": FONTE_NOVA})
            continue
        if carta.get("contrato") != CONTRATO:
            ocorrencias.append({"card_id": card_id, "campo": "$contrato",
                                "status": "contrato_inesperado",
                                "origem": FONTE_NOVA,
                                "valor": carta.get("contrato")})
            continue
        gate = carta.get("gate") or {}
        invalidas = _valida_cardinalidades(carta)
        if invalidas:
            ocorrencias.append({"card_id": card_id, "campo": "$cardinalidades",
                                "status": "cardinalidade_invalida",
                                "origem": FONTE_NOVA, "valor": invalidas})
        if gate.get("pode_rodar"):
            aptos += 1
        else:
            bloqueados += 1
            lista_motivos = gate.get("motivos") or ["gate_sem_motivo"]
            ocorrencias.append({"card_id": card_id, "campo": "$gate",
                                "status": "bloqueado_gate_v3",
                                "origem": FONTE_NOVA, "valor": lista_motivos})
            for motivo in lista_motivos:
                motivos[motivo] = motivos.get(motivo, 0) + 1
        assinatura = assinatura_calculo(carta)
        cards.append({
            "card_id": card_id,
            "gate": gate,
            "cardinalidades": carta.get("cardinalidades") or {},
            "fingerprint_calculo_por_ids": fingerprint(assinatura),
            "fingerprints_colecoes": {
                chave: fingerprint(assinatura[chave]) for chave in
                ("atributos", "corpo", "posicoes", "habilidades", "estilos_ia",
                 "pes", "playstyles", "impetos")
            },
        })

    falhas = [x for x in ocorrencias if x["status"] in {
        "ausente_no_contrato_v3", "contrato_inesperado", "cardinalidade_invalida"}]
    return {
        "contrato_auditado": CONTRATO,
        "somente_leitura": True,
        "origem": FONTE_NOVA,
        "regra_identidade": "card_id e IDs/códigos físicos; rótulos excluídos da assinatura",
        "quantidades": {"pedidos": len(ids), "devolvidos": len(por_id),
                          "aptos": aptos, "bloqueados": bloqueados,
                          "falhas_contrato": len(falhas)},
        "gates": {"motivos": motivos},
        "cards": cards,
        "ocorrencias": ocorrencias,
        "aprovado_para_leitura": not falhas and len(por_id) == len(ids),
        "todos_aptos_para_motor": not falhas and bloqueados == 0 and len(por_id) == len(ids),
    }


def le_config(caminho):
    cfg = {}
    with open(caminho, encoding="utf-8") as arquivo:
        for linha in arquivo:
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                chave, valor = linha.split("=", 1)
                cfg[chave.strip()] = valor.strip()
    return cfg


def rpc(url, chave, nome, corpo, timeout=180):
    req = urllib.request.Request(
        url.rstrip("/") + "/rest/v1/rpc/" + nome,
        data=json.dumps(corpo).encode("utf-8"), method="POST",
        headers={"apikey": chave, "Authorization": "Bearer " + chave,
                 "Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resposta:
            texto = resposta.read().decode("utf-8")
            return json.loads(texto) if texto.strip() else None
    except urllib.error.HTTPError as erro:
        raise RuntimeError("RPC %s falhou com HTTP %s; sem fallback" % (nome, erro.code))


def cartas_novas_v3(url, chave, ids):
    """Lê somente o contrato V3; uma versão estranha é falha fechada."""
    cartas = rpc(url, chave, "otimizador_cartas_v3", {"p_ids": ids}) or []
    for carta in cartas:
        if carta.get("contrato") != CONTRATO:
            raise RuntimeError("contrato inesperado; esperado %s" % CONTRATO)
    return cartas


def audita_em_lotes(url, chave, ids, tamanho=200):
    ids = sorted(set(str(x).split("@")[0] for x in ids))
    cartas = []
    tamanho = max(1, tamanho)
    for inicio in range(0, len(ids), tamanho):
        pedaco = ids[inicio:inicio + tamanho]
        cartas.extend(cartas_novas_v3(url, chave, pedaco))
        print("auditados %d/%d" % (min(inicio + len(pedaco), len(ids)), len(ids)),
              file=sys.stderr)
    return audita_cartas_v3(ids, cartas)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", nargs="+", required=True,
                        help="card_id(s) a auditar no contrato V3")
    parser.add_argument("--lote", type=int, default=200)
    parser.add_argument("--config", default="config.txt")
    parser.add_argument("--saida")
    args = parser.parse_args(argv)
    cfg = le_config(args.config)
    url, chave = cfg.get("SUPABASE_URL", ""), cfg.get("SUPABASE_KEY", "")
    if not url or not chave:
        raise SystemExit("faltam SUPABASE_URL/SUPABASE_KEY; sem fallback")
    relatorio = audita_em_lotes(url, chave, args.ids, max(1, args.lote))
    relatorio["universo"] = "IDs explícitos no contrato V3 de clube_novo"
    texto = json.dumps(relatorio, ensure_ascii=False, indent=2, sort_keys=True)
    if args.saida:
        with open(args.saida, "w", encoding="utf-8") as arquivo:
            arquivo.write(texto + "\n")
    print(texto)
    return 0 if relatorio["aprovado_para_leitura"] else 2


if __name__ == "__main__":
    sys.exit(main())
