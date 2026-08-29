"""Projeção e readback somente leitura dos slots de Ímpeto por carta."""

from __future__ import annotations

import csv
import hashlib
import io
from collections import defaultdict
from typing import Any


SLOT_COLUMNS = ("impeto_s1", "impeto_s2_cond", "vaga_s1", "vaga_s2")
CONTRACT = "clubef-card-impetus-readback-v1"


def _rows(cursor: Any, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cursor.execute(query, params)
    names = [description.name for description in cursor.description]
    return [dict(zip(names, values, strict=True)) for values in cursor.fetchall()]


def _bool(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"1", "true", "t", "sim", "yes"}


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _slot_projection(connection: Any) -> tuple[dict[str, dict[str, str]], list[dict[str, Any]]]:
    with connection.cursor() as cursor:
        cursor.execute("show transaction_read_only")
        if cursor.fetchone()[0] != "on":
            raise RuntimeError("a projeção de slots não ficou protegida como somente leitura")
        relation = _rows(cursor, """
            select card_id,slot,codigo_impeto,vaga,ordem,condicional
            from clube_novo.carta_impeto_jogo order by card_id,slot
        """)
    projection: dict[str, dict[str, str]] = {}
    seen: set[tuple[str, int]] = set()
    for item in relation:
        card_id, slot = str(item["card_id"]), int(item["slot"])
        key = (card_id, slot)
        if key in seen:
            raise RuntimeError(f"relação duplicada para carta/slot: {card_id}/{slot}")
        seen.add(key)
        if slot not in (1, 2):
            raise RuntimeError(f"slot normalizado inválido: {card_id}/{slot}")
        vacancy = bool(item["vaga"])
        code = item["codigo_impeto"]
        if vacancy == (code is not None):
            raise RuntimeError(f"estado contraditório em carta/slot: {card_id}/{slot}")
        row = projection.setdefault(card_id, {
            "impeto_s1": "", "impeto_s2_cond": "", "vaga_s1": "false", "vaga_s2": "false",
        })
        if slot == 1:
            row["impeto_s1"] = "" if vacancy else str(code)
            row["vaga_s1"] = "true" if vacancy else "false"
        else:
            row["impeto_s2_cond"] = "" if vacancy else str(code)
            row["vaga_s2"] = "true" if vacancy else "false"
    return projection, relation


def apply_normalized_slot_projection(rows: dict[str, dict[str, str]], connection: Any) -> dict[str, Any]:
    """Substitui somente os quatro campos-resumo pela relação normalizada canônica."""
    projection, relation = _slot_projection(connection)
    orphan = sorted(set(projection) - set(rows))
    if orphan:
        raise RuntimeError(f"há {len(orphan)} cartas órfãs em carta_impeto_jogo")
    changed_cards = 0
    changed_fields = {column: 0 for column in SLOT_COLUMNS}
    before_lines: list[str] = []
    empty = {"impeto_s1": "", "impeto_s2_cond": "", "vaga_s1": "false", "vaga_s2": "false"}
    for card_id, row in rows.items():
        projected = projection.get(card_id) or empty
        changed = False
        for column in SLOT_COLUMNS:
            old = _text(row.get(column)).lower()
            new = projected[column]
            if old != new:
                changed = True
                changed_fields[column] += 1
                before_lines.append(f"{card_id}|{column}|{old}|{new}")
            row[column] = new
        changed_cards += int(changed)
    fingerprint = hashlib.sha256("\n".join(sorted(before_lines)).encode("utf-8")).hexdigest()
    return {
        "source": "clube_novo.carta_impeto_jogo", "relation_rows": len(relation),
        "relation_cards": len(projection), "changed_cards_from_stored_summary": changed_cards,
        "changed_fields_from_stored_summary": changed_fields,
        "stored_difference_sha256": fingerprint, "projection_difference": 0,
    }


def validate_physical_slot_projection(csv_text: str, connection: Any) -> dict[str, Any]:
    projection, relation = _slot_projection(connection)
    source: dict[str, dict[str, str]] = {}
    for row in csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff"))):
        card_id = _text(row.get("card_id"))
        if not card_id or card_id in source:
            raise ValueError("CSV físico contém card_id ausente ou duplicado")
        source[card_id] = {
            "impeto_s1": _text(row.get("impeto_s1")), "impeto_s2_cond": _text(row.get("impeto_s2_cond")),
            "vaga_s1": "true" if _bool(row.get("vaga_s1")) else "false",
            "vaga_s2": "true" if _bool(row.get("vaga_s2")) else "false",
        }
    differences: list[tuple[str, str, str, str]] = []
    empty = {"impeto_s1": "", "impeto_s2_cond": "", "vaga_s1": "false", "vaga_s2": "false"}
    for card_id, physical in source.items():
        normalized = projection.get(card_id) or empty
        for column in SLOT_COLUMNS:
            if physical[column] != normalized[column]:
                differences.append((card_id, column, physical[column], normalized[column]))
    missing_cards = sorted(set(projection) - set(source))
    with connection.cursor() as cursor:
        coverage = _rows(cursor, """
            select
              count(*)::int total_slots,
              count(*) filter(where r.codigo_impeto is not null)::int filled_slots,
              count(*) filter(where r.vaga)::int vacancies,
              count(*) filter(where r.condicional)::int conditional_slots,
              count(*) filter(where r.condicional=false)::int always_active_slots,
              count(*) filter(where r.codigo_impeto is not null and i.codigo_jogo is null)::int missing_catalog,
              count(*) filter(where r.codigo_impeto is not null and c.codigo_impeto is null)::int missing_condition,
              count(*) filter(where r.condicional is distinct from i.condicional)::int conditional_mismatch,
              count(*) filter(where r.codigo_impeto is not null and not exists(select 1 from clube_novo.impeto_atributo_jogo a where a.codigo_impeto=r.codigo_impeto))::int missing_effects,
              count(*) filter(where r.condicional and c.tipo_raw=2 and not exists(select 1 from clube_novo.impeto_condicao_faixa_jogo f where f.codigo_impeto=r.codigo_impeto))::int missing_ranges,
              count(*) filter(where c.criterio_codigo='quantidade_jogadores_nacionalidade_regiao' and not exists(select 1 from clube_novo.impeto_condicao_nacionalidade_jogo n where n.codigo_impeto=r.codigo_impeto))::int missing_nationality_target,
              count(*) filter(where c.criterio_codigo='quantidade_jogadores_liga_categoria' and not exists(select 1 from clube_novo.impeto_condicao_liga_jogo l where l.codigo_impeto=r.codigo_impeto))::int missing_league_target,
              count(*) filter(where c.criterio_codigo='quantidade_jogadores_liga_categoria' and not exists(select 1 from clube_novo.impeto_condicao_liga_membro_jogo m where m.codigo_impeto=r.codigo_impeto))::int missing_league_members,
              count(*) filter(where c.criterio_codigo='quantidade_jogadores_classe_impeto' and not exists(select 1 from clube_novo.impeto_condicao_classe_jogo k where k.codigo_impeto=r.codigo_impeto))::int missing_class_recipe
            from clube_novo.carta_impeto_jogo r
            left join clube_novo.impeto_jogo i on i.codigo_jogo=r.codigo_impeto
            left join clube_novo.impeto_condicao_jogo c on c.codigo_impeto=r.codigo_impeto
        """)[0]
    digest = hashlib.sha256()
    for item in sorted(differences):
        digest.update(("|".join(item) + "\n").encode("utf-8"))
    coverage_ok = coverage == {
        "total_slots": 3_748, "filled_slots": 2_381, "vacancies": 1_367,
        "conditional_slots": 1_170, "always_active_slots": 1_211,
        "missing_catalog": 0, "missing_condition": 0, "conditional_mismatch": 0,
        "missing_effects": 0, "missing_ranges": 0, "missing_nationality_target": 0,
        "missing_league_target": 0, "missing_league_members": 0, "missing_class_recipe": 0,
    }
    passed = not differences and not missing_cards and len(source) == 43_072 and coverage_ok
    return {
        "contract": CONTRACT, "transaction_read_only": True, "database_write": False,
        "physical_cards": len(source), "relation_rows": len(relation), "relation_cards": len(projection),
        "differences": len(differences), "missing_physical_cards": len(missing_cards),
        "difference_sha256": digest.hexdigest(),
        "functional_recipe_coverage": coverage,
        "samples": [dict(zip(("card_id", "field", "physical", "normalized"), item, strict=True)) for item in differences[:20]],
        "passed": passed, "result": "aprovado" if passed else "reabrir_frente",
    }


def readback_card_slots(connection: Any, card_ids: list[str]) -> dict[str, Any]:
    if not card_ids or len(card_ids) > 100:
        raise ValueError("informe de 1 a 100 card_ids")
    clean_ids = list(dict.fromkeys(str(value).strip() for value in card_ids if str(value).strip()))
    with connection.cursor() as cursor:
        cursor.execute("show transaction_read_only")
        if cursor.fetchone()[0] != "on":
            raise RuntimeError("o readback de Ímpetos não ficou protegido como somente leitura")
        cards = _rows(cursor, "select card_id,nome,codigo_nacionalidade,codigo_liga,codigo_clube from clube_novo.carta_jogo where card_id=any(%s)", (clean_ids,))
        slots = _rows(cursor, """
            select r.card_id,r.slot,r.codigo_impeto,r.vaga,r.ordem,r.condicional,
                   i.nome_pt,i.nome_en,i.tipo_condicao_raw,i.pode_rodar,i.falta_o_que,
                   c.criterio_codigo,c.campo_alvo,c.alvo_origem,c.avaliacao_minima,c.avaliacao_maxima,
                   c.status_validacao,c.transformacao_regra,c.arquivo_origem,c.indice_registro,c.registro_sha256
            from clube_novo.carta_impeto_jogo r
            left join clube_novo.impeto_jogo i on i.codigo_jogo=r.codigo_impeto
            left join clube_novo.impeto_condicao_jogo c on c.codigo_impeto=r.codigo_impeto
            where r.card_id=any(%s) order by r.card_id,r.slot
        """, (clean_ids,))
        codes = sorted({int(row["codigo_impeto"]) for row in slots if row["codigo_impeto"] is not None})
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
    grouped: dict[str, dict[int, list[dict[str, Any]]]] = {}
    for name, items in details.items():
        grouped[name] = defaultdict(list)
        for item in items:
            grouped[name][int(item.pop("codigo_impeto"))].append(item)
    slot_by_card = defaultdict(dict)
    for row in slots:
        code = int(row["codigo_impeto"]) if row["codigo_impeto"] is not None else None
        vacancy = bool(row["vaga"])
        conditional = bool(row["condicional"]) if row["condicional"] is not None else None
        recipe = None
        if code is not None:
            recipe = {
                "criterio": row["criterio_codigo"], "tipo_raw": row["tipo_condicao_raw"], "campo_alvo": row["campo_alvo"],
                "alvo_origem": row["alvo_origem"], "avaliacao_minima": row["avaliacao_minima"], "avaliacao_maxima": row["avaliacao_maxima"],
                "transformacao_regra": row["transformacao_regra"], "status_validacao": row["status_validacao"],
                "efeitos": grouped["efeitos"].get(code, []), "faixas": grouped["faixas"].get(code, []),
                "parametros_faixa": grouped["parametros_faixa"].get(code, []),
                "alvos": {name: grouped[name].get(code, []) for name in ("nacionalidades", "ligas", "membros_liga", "clubes", "classes", "candidatos_classe", "outros")},
                "proveniencia": {"arquivo": row["arquivo_origem"], "registro": row["indice_registro"], "sha256_registro": row["registro_sha256"]},
            }
        slot_by_card[str(row["card_id"])][int(row["slot"])] = {
            "slot": int(row["slot"]), "estado": "vaga" if vacancy else "preenchido", "codigo_impeto": code,
            "nome": row["nome_pt"] or row["nome_en"], "ativacao": None if vacancy else ("condicional" if conditional else "sempre_ativo"),
            "condicional": conditional, "receita": recipe,
            "consumidor": {"pode_rodar": bool(row["pode_rodar"]) if code is not None else False, "falta_o_que": row["falta_o_que"]},
        }
    results = []
    for card in sorted(cards, key=lambda item: int(item["card_id"])):
        card_id = str(card["card_id"])
        card_slots = []
        for slot in (1, 2):
            card_slots.append(slot_by_card[card_id].get(slot) or {
                "slot": slot, "estado": "ausente_no_jogo", "codigo_impeto": None, "nome": None,
                "ativacao": None, "condicional": None, "receita": None,
                "consumidor": {"pode_rodar": False, "falta_o_que": "slot não presente na relação física"},
            })
        results.append({**card, "slots": card_slots})
    missing = sorted(set(clean_ids) - {str(card["card_id"]) for card in cards})
    return {"contract": CONTRACT, "transaction_read_only": True, "database_write": False, "consumer_enabled": False, "cards": results, "missing_card_ids": missing}
