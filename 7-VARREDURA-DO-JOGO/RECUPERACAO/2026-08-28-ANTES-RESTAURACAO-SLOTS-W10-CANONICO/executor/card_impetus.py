"""Leitura física e comparação read-only dos slots de Ímpeto por carta.

O CSV físico é a única origem dos quatro campos de slot. As relações do banco
são consultadas apenas para comparação e para enriquecer uma receita já
identificada pelo código físico.
"""

from __future__ import annotations

import csv
import hashlib
import io
from collections import defaultdict
from typing import Any

SLOT_COLUMNS = ("impeto_s1", "impeto_s2_cond", "vaga_s1", "vaga_s2")
CONTRACT = "clubef-card-impetus-physical-w8-v2"
EMPTY = {"impeto_s1": "", "impeto_s2_cond": "", "vaga_s1": "false", "vaga_s2": "false"}


def _rows(cursor: Any, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cursor.execute(query, params)
    names = [description.name for description in cursor.description]
    return [dict(zip(names, values, strict=True)) for values in cursor.fetchall()]


def _bool(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"1", "true", "t", "sim", "yes"}


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def physical_slots_from_csv(csv_text: str, require_complete: bool = False) -> dict[str, dict[str, str]]:
    source: dict[str, dict[str, str]] = {}
    for row in csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff"))):
        card_id = _text(row.get("card_id"))
        if not card_id or card_id in source:
            raise ValueError("CSV físico contém card_id ausente ou duplicado")
        slots = {
            "impeto_s1": _text(row.get("impeto_s1")), "impeto_s2_cond": _text(row.get("impeto_s2_cond")),
            "vaga_s1": "true" if _bool(row.get("vaga_s1")) else "false",
            "vaga_s2": "true" if _bool(row.get("vaga_s2")) else "false",
        }
        if (slots["impeto_s1"] != "") and (slots["vaga_s1"] == "true"):
            raise ValueError(f"estado físico contraditório no slot 1: {card_id}")
        if (slots["impeto_s2_cond"] != "") and (slots["vaga_s2"] == "true"):
            raise ValueError(f"estado físico contraditório no slot 2: {card_id}")
        source[card_id] = slots
    if require_complete and len(source) != 43_072:
        raise ValueError(f"CSV físico contém {len(source)} cartas; esperado 43072")
    return source


def _relation_projection(connection: Any, card_ids: list[str] | None = None) -> tuple[dict[str, dict[str, str]], list[dict[str, Any]]]:
    with connection.cursor() as cursor:
        cursor.execute("show transaction_read_only")
        if cursor.fetchone()[0] != "on":
            raise RuntimeError("a comparação de slots não ficou protegida como somente leitura")
        query = "select card_id,slot,codigo_impeto,vaga,ordem,condicional from clube_novo.carta_impeto_jogo"
        relation = _rows(cursor, query + (" where card_id=any(%s)" if card_ids is not None else "") + " order by card_id,slot", (card_ids,) if card_ids is not None else ())
    projection: dict[str, dict[str, str]] = {}
    seen: set[tuple[str, int]] = set()
    for item in relation:
        card_id, slot = str(item["card_id"]), int(item["slot"])
        if slot not in (1, 2) or (card_id, slot) in seen:
            raise RuntimeError(f"relação inválida para carta/slot: {card_id}/{slot}")
        seen.add((card_id, slot))
        vacancy, code = bool(item["vaga"]), item["codigo_impeto"]
        if vacancy == (code is not None):
            raise RuntimeError(f"estado contraditório em carta_impeto_jogo: {card_id}/{slot}")
        row = projection.setdefault(card_id, dict(EMPTY))
        if slot == 1:
            row["impeto_s1"], row["vaga_s1"] = ("", "true") if vacancy else (str(code), "false")
        else:
            row["impeto_s2_cond"], row["vaga_s2"] = ("", "true") if vacancy else (str(code), "false")
    return projection, relation


def _state(row: dict[str, str], slot: int) -> tuple[str, int | None]:
    code = row["impeto_s1" if slot == 1 else "impeto_s2_cond"]
    vacancy = row["vaga_s1" if slot == 1 else "vaga_s2"] == "true"
    if code:
        return "preenchido", int(code)
    return ("vaga", None) if vacancy else ("vazio", None)


def validate_physical_slot_projection(csv_text: str, connection: Any) -> dict[str, Any]:
    """Compara fonte física w8 ao banco, nunca usa banco como entrada."""
    physical = physical_slots_from_csv(csv_text, require_complete=True)
    relation_projection, relation = _relation_projection(connection)
    differences: list[tuple[str, str, str, str]] = []
    for card_id, slots in physical.items():
        database = relation_projection.get(card_id, EMPTY)
        for field in SLOT_COLUMNS:
            if slots[field] != database[field]:
                differences.append((card_id, field, slots[field], database[field]))
    filled = vacancies = empty = 0
    for slots in physical.values():
        for slot in (1, 2):
            state, _ = _state(slots, slot)
            filled += state == "preenchido"
            vacancies += state == "vaga"
            empty += state == "vazio"
    digest = hashlib.sha256()
    for item in sorted(differences):
        digest.update(("|".join(item) + "\n").encode("utf-8"))
    physical_ok = len(physical) == 43_072 and filled == 2_378 and vacancies == 1_369 and empty == 82_397
    return {
        "contract": CONTRACT, "transaction_read_only": True, "database_write": False,
        "source": {"file": "Player.bin", "slot_1": "bit308/w8", "slot_2": "bit288/w8"},
        "physical": {"cards": len(physical), "slots": 86_144, "filled": filled, "vacancies": vacancies, "empty": empty},
        "extractor_projection": {"differences_from_physical": 0, "source": "CSV físico w8"},
        "database_relation": {"rows": len(relation), "cards": len(relation_projection), "differences_from_physical": len(differences), "difference_sha256": digest.hexdigest(), "samples": [dict(zip(("card_id", "field", "physical", "database"), item, strict=True)) for item in differences[:20]]},
        "physical_passed": physical_ok, "passed": physical_ok,
        "result": "aprovado_fonte_fisica_relacao_divergente" if physical_ok and differences else ("aprovado" if physical_ok else "reabrir_leitor_fisico"),
    }


def readback_card_slots(connection: Any, card_ids: list[str], csv_text: str) -> dict[str, Any]:
    if not card_ids or len(card_ids) > 100:
        raise ValueError("informe de 1 a 100 card_ids")
    physical = physical_slots_from_csv(csv_text)
    clean_ids = list(dict.fromkeys(str(value).strip() for value in card_ids if str(value).strip()))
    if sorted(set(clean_ids) - set(physical)):
        raise ValueError("a fotografia física não contém todos os card_ids solicitados")
    relation_projection, _ = _relation_projection(connection, clean_ids)
    codes = sorted({code for card_id in clean_ids for slot in (1, 2) for _, code in [_state(physical[card_id], slot)] if code is not None})
    with connection.cursor() as cursor:
        cursor.execute("show transaction_read_only")
        if cursor.fetchone()[0] != "on":
            raise RuntimeError("o readback de Ímpetos não ficou protegido como somente leitura")
        cards = _rows(cursor, "select card_id,nome,codigo_nacionalidade,codigo_liga,codigo_clube from clube_novo.carta_jogo where card_id=any(%s)", (clean_ids,))
        catalog = _rows(cursor, """select i.codigo_jogo,i.nome_pt,i.nome_en,i.condicional,i.tipo_condicao_raw,i.pode_rodar,i.falta_o_que,c.criterio_codigo,c.campo_alvo,c.alvo_origem,c.avaliacao_minima,c.avaliacao_maxima,c.status_validacao,c.transformacao_regra,c.arquivo_origem,c.indice_registro,c.registro_sha256 from clube_novo.impeto_jogo i left join clube_novo.impeto_condicao_jogo c on c.codigo_impeto=i.codigo_jogo where i.codigo_jogo=any(%s)""", (codes,)) if codes else []
        detail_queries = {
            "efeitos": "select codigo_impeto,codigo_atributo,ordem,delta,endereco_origem,status_validacao from clube_novo.impeto_atributo_jogo where codigo_impeto=any(%s) order by codigo_impeto,ordem",
            "faixas": "select codigo_impeto,ordem,quantidade_minima,quantidade_maxima,delta,status_validacao,fonte_prova from clube_novo.impeto_condicao_faixa_jogo where codigo_impeto=any(%s) order by codigo_impeto,ordem",
            "nacionalidades": "select n.codigo_impeto,n.codigo_nacionalidade,n.modo_alvo,d.nome_pt_br from clube_novo.impeto_condicao_nacionalidade_jogo n left join clube_novo.nacionalidade_jogo d on d.codigo_jogo=n.codigo_nacionalidade where n.codigo_impeto=any(%s)",
            "ligas": "select l.codigo_impeto,l.codigo_liga_categoria,l.modo_alvo,d.nome_pt_br from clube_novo.impeto_condicao_liga_jogo l left join clube_novo.liga_jogo d on d.codigo_jogo=l.codigo_liga_categoria where l.codigo_impeto=any(%s)",
            "membros_liga": "select m.codigo_impeto,m.codigo_liga_membro,m.ordem_fisica,m.papel_fisico,d.nome_pt_br,m.status_validacao from clube_novo.impeto_condicao_liga_membro_jogo m left join clube_novo.liga_jogo d on d.codigo_jogo=m.codigo_liga_membro where m.codigo_impeto=any(%s) order by m.codigo_impeto,m.ordem_fisica",
            "clubes": "select c.codigo_impeto,c.ordem,c.modo_alvo,c.codigo_clube,d.nome_pt_br,c.status_validacao from clube_novo.impeto_condicao_clube_jogo c left join clube_novo.clube_jogo d on d.codigo_jogo=c.codigo_clube where c.codigo_impeto=any(%s) order by c.codigo_impeto,c.ordem",
            "classes": "select codigo_impeto,classe_dono,operador,regra_contagem,procedencia,status_validacao,pode_rodar,falta_o_que from clube_novo.impeto_condicao_classe_jogo where codigo_impeto=any(%s)",
            "candidatos_classe": "select codigo_impeto,classe_candidato,status_validacao,pode_rodar from clube_novo.impeto_classe_candidato_jogo where codigo_impeto=any(%s) order by codigo_impeto,classe_candidato",
            "parametros_faixa": "select codigo_impeto,corte_raw,efeito_maximo,faixas_derivadas,status_validacao,formula_faixa from clube_novo.impeto_condicao_parametro_faixa_jogo where codigo_impeto=any(%s)",
            "outros": "select codigo_impeto,seletor_raw,semantica,status_validacao from clube_novo.impeto_condicao_outro_jogo where codigo_impeto=any(%s)",
        }
        details = {name: (_rows(cursor, query, (codes,)) if codes else []) for name, query in detail_queries.items()}
    catalog_by_code = {int(item.pop("codigo_jogo")): item for item in catalog}
    grouped: dict[str, dict[int, list[dict[str, Any]]]] = {}
    for name, items in details.items():
        grouped[name] = defaultdict(list)
        for item in items:
            grouped[name][int(item.pop("codigo_impeto"))].append(item)
    cards_by_id = {str(item["card_id"]): item for item in cards}
    results = []
    for card_id in clean_ids:
        if card_id not in cards_by_id:
            continue
        source, database, slots = physical[card_id], relation_projection.get(card_id, EMPTY), []
        for slot in (1, 2):
            state, code = _state(source, slot)
            item = catalog_by_code.get(code) if code is not None else None
            recipe = None if not item else {
                "criterio": item["criterio_codigo"], "tipo_raw": item["tipo_condicao_raw"], "campo_alvo": item["campo_alvo"], "alvo_origem": item["alvo_origem"], "avaliacao_minima": item["avaliacao_minima"], "avaliacao_maxima": item["avaliacao_maxima"], "transformacao_regra": item["transformacao_regra"], "status_validacao": item["status_validacao"], "efeitos": grouped["efeitos"].get(code, []), "faixas": grouped["faixas"].get(code, []), "parametros_faixa": grouped["parametros_faixa"].get(code, []), "alvos": {name: grouped[name].get(code, []) for name in ("nacionalidades", "ligas", "membros_liga", "clubes", "classes", "candidatos_classe", "outros")}, "proveniencia": {"arquivo": item["arquivo_origem"], "registro": item["indice_registro"], "sha256_registro": item["registro_sha256"]}}
            source_fields = {"impeto_s1": source["impeto_s1"], "vaga_s1": source["vaga_s1"]} if slot == 1 else {"impeto_s2_cond": source["impeto_s2_cond"], "vaga_s2": source["vaga_s2"]}
            database_fields = {key: database[key] for key in source_fields}
            slots.append({"slot": slot, "origem_fisica": "Player.bin bit308/w8" if slot == 1 else "Player.bin bit288/w8", "estado": state, "codigo_impeto": code, "nome": (item or {}).get("nome_pt") or (item or {}).get("nome_en"), "ativacao": None if not item else ("condicional" if item["condicional"] else "sempre_ativo"), "condicional": None if not item else bool(item["condicional"]), "receita": recipe, "relacao_banco_confere": source_fields == database_fields, "relacao_banco": database_fields, "consumidor": {"pode_rodar": bool(item["pode_rodar"]) if item else False, "falta_o_que": item["falta_o_que"] if item else None}})
        results.append({**cards_by_id[card_id], "slots": slots})
    missing_database = sorted(set(clean_ids) - set(cards_by_id))
    mismatches = sum(not slot["relacao_banco_confere"] for card in results for slot in card["slots"])
    return {"contract": CONTRACT, "transaction_read_only": True, "database_write": False, "consumer_enabled": False, "slot_source": "Player.bin w8 via fotografia física", "cards": results, "missing_card_ids": missing_database, "database_relation_slot_mismatches": mismatches}
