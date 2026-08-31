"""Avalia, sem escrever no banco, se cada carta pode alimentar os motores.

Ausência confirmada é um dado válido.  O gate só considera incompleto aquilo
que não foi lido, não pôde ser resolvido ou foi marcado pelo operador como uma
pré-carga sabidamente parcial.  Publicação/exibição não faz parte deste gate.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Iterable


RULE_VERSION = "clubef-prontidao-motores-v1"
OVERRIDE_SCHEMA = "clubef-prontidao-motores-operador-v1"
VALID_STATES = {
    "conferido_com_valor",
    "conferido_sem_valor",
    "conferido_sem_vinculo_atual",
    "nao_conferido",
    "leitura_com_problema",
}
COMPLETE_STATES = {"conferido_com_valor", "conferido_sem_valor", "conferido_sem_vinculo_atual"}
SLOT_STATES = {"sem", "vaga", "preench"}


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _component(
    state: str,
    *,
    meaning: str,
    source: str,
    quantity: int | None = None,
    reason: str | None = None,
    known_pending: dict[str, Any] | None = None,
    resolution_pending: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if state not in VALID_STATES:
        raise ValueError(f"estado de coleta inválido: {state}")
    return {
        "estado": state,
        "completo": state in COMPLETE_STATES,
        "significado": meaning,
        "fonte": source,
        "quantidade": quantity,
        "motivo": reason,
        "pendencia_conhecida": known_pending,
        "pendencia_de_resolucao": resolution_pending,
    }


def _missing(name: str, component: dict[str, Any]) -> dict[str, Any] | None:
    if component.get("completo") is True:
        return None
    return {
        "componente": name,
        "estado": component.get("estado"),
        "motivo": component.get("motivo") or component.get("significado"),
    }


def _basic_component(card: dict[str, Any]) -> dict[str, Any]:
    required = {
        "card_id": str,
        "name": str,
        "height": int,
        "weight": int,
        "age": int,
        "position": str,
        "weak_foot_usage": int,
        "weak_foot_accuracy": int,
        "foot": str,
        "form": int,
        "injury": str,
    }
    absent = [key for key in required if key not in card]
    if absent:
        return _component(
            "nao_conferido",
            meaning="Os dados básicos não foram todos devolvidos pelo leitor.",
            source="Player.bin / contrato ativo",
            reason="campos não lidos: " + ", ".join(absent),
        )
    invalid = [
        key for key, expected in required.items()
        if isinstance(card.get(key), bool) or not isinstance(card.get(key), expected)
        or (expected is str and not str(card.get(key)).strip())
    ]
    if invalid:
        return _component(
            "leitura_com_problema",
            meaning="Os dados básicos foram lidos, mas há valor inválido.",
            source="Player.bin / contrato ativo",
            reason="campos inválidos: " + ", ".join(invalid),
        )
    ranges = {
        "height": (145, 210),
        "weight": (35, 150),
        "age": (14, 47),
        "weak_foot_usage": (0, 3),
        "weak_foot_accuracy": (0, 3),
    }
    outside = [key for key, (low, high) in ranges.items() if not low <= int(card[key]) <= high]
    if outside:
        return _component(
            "leitura_com_problema",
            meaning="Os dados básicos foram lidos, mas saíram do intervalo aceito.",
            source="Player.bin / contrato ativo",
            reason="fora do intervalo: " + ", ".join(outside),
        )
    return _component(
        "conferido_com_valor",
        meaning="Identidade e dados básicos foram lidos e validados.",
        source="Player.bin / contrato ativo",
        quantity=len(required),
    )


def _fixed_integer_collection(
    card: dict[str, Any], field: str, expected_count: int, low: int, high: int, label: str
) -> dict[str, Any]:
    if field not in card:
        return _component(
            "nao_conferido",
            meaning=f"{label} não foram devolvidos pelo leitor.",
            source=f"Player.bin / {field}",
            reason="campo físico não lido",
        )
    values = card.get(field)
    if not isinstance(values, list):
        return _component(
            "leitura_com_problema",
            meaning=f"{label} foram devolvidos em formato inválido.",
            source=f"Player.bin / {field}",
            reason="formato diferente de lista",
        )
    if len(values) != expected_count:
        return _component(
            "leitura_com_problema",
            meaning=f"A leitura de {label.lower()} não trouxe a quantidade completa.",
            source=f"Player.bin / {field}",
            quantity=len(values),
            reason=f"esperado {expected_count}; encontrado {len(values)}",
        )
    invalid = [value for value in values if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high]
    if invalid:
        return _component(
            "leitura_com_problema",
            meaning=f"A leitura de {label.lower()} contém valor fora do intervalo.",
            source=f"Player.bin / {field}",
            quantity=len(values),
            reason=f"valor aceito: {low}..{high}",
        )
    return _component(
        "conferido_com_valor",
        meaning=f"{label} foram todos lidos e validados.",
        source=f"Player.bin / {field}",
        quantity=len(values),
    )


def _aptitudes_component(card: dict[str, Any]) -> dict[str, Any]:
    if "aptitudes" not in card:
        return _component(
            "nao_conferido",
            meaning="As aptidões de posição não foram devolvidas pelo leitor.",
            source="Player.bin / aptitudes",
            reason="campo físico não lido",
        )
    values = card.get("aptitudes")
    if not isinstance(values, dict) or len(values) != 12:
        return _component(
            "leitura_com_problema",
            meaning="A leitura das aptidões não trouxe as 12 posições esperadas.",
            source="Player.bin / aptitudes",
            quantity=len(values) if isinstance(values, dict) else None,
            reason="esperadas 12 aptidões",
        )
    invalid = [key for key, value in values.items() if not isinstance(key, str) or isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2]
    if invalid:
        return _component(
            "leitura_com_problema",
            meaning="Há aptidão com valor inválido.",
            source="Player.bin / aptitudes",
            quantity=len(values),
            reason="posições inválidas: " + ", ".join(map(str, invalid)),
        )
    return _component(
        "conferido_com_valor",
        meaning="As 12 aptidões foram lidas; nível zero também é uma resposta válida.",
        source="Player.bin / aptitudes",
        quantity=12,
    )


def _optional_relation_component(
    card: dict[str, Any],
    *,
    raw_field: str,
    proof_field: str,
    label: str,
    identity_key: str,
) -> dict[str, Any]:
    if raw_field not in card or proof_field not in card:
        return _component(
            "nao_conferido",
            meaning=f"{label} ainda não foram conferidos neste card.",
            source=f"Player.bin / {proof_field}",
            reason="campo ou prova física não devolvida",
        )
    values, proof = card.get(raw_field), card.get(proof_field)
    if not isinstance(values, list) or not isinstance(proof, list):
        return _component(
            "leitura_com_problema",
            meaning=f"A leitura de {label.lower()} voltou em formato inválido.",
            source=f"Player.bin / {proof_field}",
            reason="listas físicas inválidas",
        )
    if len(values) != len(proof):
        return _component(
            "leitura_com_problema",
            meaning=f"A lista de {label.lower()} não confere com sua prova física.",
            source=f"Player.bin / {proof_field}",
            quantity=len(proof),
            reason=f"lista exibida={len(values)}; membros físicos={len(proof)}",
        )
    identities: list[str] = []
    for item in proof:
        if not isinstance(item, dict) or item.get("ativo") is not True or item.get(identity_key) is None:
            return _component(
                "leitura_com_problema",
                meaning=f"Um membro de {label.lower()} não possui identidade/prova completa.",
                source=f"Player.bin / {proof_field}",
                quantity=len(proof),
                reason="membro físico sem identidade ou sem estado ativo",
            )
        if not item.get("arquivo") or item.get("registro") is None or not item.get("hash"):
            return _component(
                "leitura_com_problema",
                meaning=f"Um membro de {label.lower()} não possui procedência física completa.",
                source=f"Player.bin / {proof_field}",
                quantity=len(proof),
                reason="arquivo, registro ou hash ausente",
            )
        identities.append(str(item[identity_key]))
    if len(set(identities)) != len(identities):
        return _component(
            "leitura_com_problema",
            meaning=f"A leitura de {label.lower()} contém membro repetido.",
            source=f"Player.bin / {proof_field}",
            quantity=len(proof),
            reason="identidade física duplicada",
        )
    if not proof:
        return _component(
            "conferido_sem_valor",
            meaning=f"{label} foram conferidos e o card não possui nenhum item.",
            source=f"Player.bin / {proof_field}",
            quantity=0,
        )
    return _component(
        "conferido_com_valor",
        meaning=f"{label} foram conferidos com identidade e procedência física.",
        source=f"Player.bin / {proof_field}",
        quantity=len(proof),
    )


def _normalize_catalog_id(value: Any) -> Any:
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, int):
        return value
    text = str(value).strip()
    return int(text) if text.isdigit() else text


def _contract_playstyle_rows(value: Any) -> list[dict[str, Any]]:
    """Aceita o catálogo isolado ou o pedido-leitura inteiro."""
    if isinstance(value, list):
        rows = value
    elif isinstance(value, dict):
        rows = value.get("rows")
        if rows is None:
            rows = value.get("records")
        if rows is None and isinstance(value.get("catalogos"), list):
            matches = [entry for entry in value["catalogos"] if isinstance(entry, dict) and entry.get("table") == "playstyle"]
            if len(matches) != 1:
                raise ValueError("contrato deve conter exatamente um catálogo playstyle")
            rows = matches[0].get("rows")
        if rows is None and isinstance(value.get("catalogs"), dict):
            entry = value["catalogs"].get("playstyles") or value["catalogs"].get("playstyle")
            if isinstance(entry, dict):
                rows = entry.get("records") if entry.get("records") is not None else entry.get("rows")
    else:
        rows = None
    if not isinstance(rows, list):
        raise ValueError("catálogo playstyle do contrato inválido")
    return rows


def _build_playstyle_catalog(
    metadata_rows: Any,
    contract_catalog: Any = None,
) -> dict[int, dict[str, Any]]:
    sources: list[tuple[str, list[dict[str, Any]]]] = []
    if metadata_rows is not None:
        if not isinstance(metadata_rows, list):
            raise ValueError("catálogo físico de playstyles inválido")
        sources.append(("metadados-fisicos.json/catalogs.playstyles", metadata_rows))
    if contract_catalog is not None:
        sources.append(("pedido-leitura.json/catalogo.playstyle", _contract_playstyle_rows(contract_catalog)))
    if not sources or not any(rows for _, rows in sources):
        raise ValueError("catálogo playstyle ausente nos metadados e no contrato")

    output: dict[int, dict[str, Any]] = {}
    seen_by_source: set[tuple[str, int]] = set()
    for source, rows in sources:
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError(f"catálogo playstyle contém registro inválido em {source}")
            raw_index = row.get("indice") if "indice" in row else row.get("record_index")
            if isinstance(raw_index, bool) or not isinstance(raw_index, int) or raw_index < 0:
                raise ValueError(f"catálogo playstyle sem índice válido em {source}")
            source_key = (source, raw_index)
            if source_key in seen_by_source:
                raise ValueError(f"índice playstyle repetido em {source}: {raw_index}")
            seen_by_source.add(source_key)

            game_id = _normalize_catalog_id(row.get("id_jogo") if "id_jogo" in row else row.get("id"))
            current = output.setdefault(raw_index, {
                "indice": raw_index,
                "id_jogo": game_id,
                "nome_pt": row.get("nome_pt"),
                "proveniencia": [],
            })
            if current.get("id_jogo") is not None and game_id is not None and current["id_jogo"] != game_id:
                raise ValueError(
                    f"catálogo playstyle diverge no índice {raw_index}: "
                    f"{current['id_jogo']} != {game_id}"
                )
            if current.get("id_jogo") is None:
                current["id_jogo"] = game_id
            if current.get("nome_pt") is None and row.get("nome_pt") is not None:
                current["nome_pt"] = row.get("nome_pt")
            current["proveniencia"].append({
                "fonte": source,
                "indice": raw_index,
                "id_jogo": game_id,
                "nome_pt": row.get("nome_pt"),
                "record_sha256": row.get("record_sha256"),
                "source_file_sha256": row.get("source_file_sha256"),
                "source_role": row.get("source_role"),
                "bit": row.get("bit"),
            })
    return output


def _playstyles_component(
    card: dict[str, Any],
    catalog_by_index: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    required = ("primary_style_id", "primary_style_unknown", "defensive_style_id")
    absent = [key for key in required if key not in card]
    if absent:
        return _component(
            "nao_conferido",
            meaning="Os estilos de jogo não foram totalmente devolvidos pelo leitor.",
            source="Player.bin / slots de estilo",
            reason="campos não lidos: " + ", ".join(absent),
        )
    primary = card.get("primary_style_id")
    defensive = card.get("defensive_style_id")
    invalid = [
        key for key, value in (("primary_style_id", primary), ("defensive_style_id", defensive))
        if isinstance(value, bool) or not isinstance(value, int) or value < 0
    ]
    if invalid:
        return _component(
            "leitura_com_problema",
            meaning="Os códigos brutos dos estilos foram devolvidos em formato inválido.",
            source="Player.bin / slots de estilo",
            reason="campos inválidos: " + ", ".join(invalid),
        )
    if card.get("primary_style_unknown") is True:
        return _component(
            "leitura_com_problema",
            meaning="O estilo principal foi lido, mas o código ainda não foi resolvido.",
            source="Player.bin / playstyle",
            reason=f"código principal {primary}",
        )
    if defensive == 0:
        return _component(
            "conferido_com_valor",
            meaning="O estilo principal foi conferido e a ausência de estilo defensivo foi confirmada.",
            source="Player.bin / slots de estilo",
            quantity=1,
        )
    catalog_record = catalog_by_index.get(defensive)
    if catalog_record is None:
        return _component(
            "conferido_com_valor",
            meaning="Os códigos brutos dos estilos principal e defensivo foram conferidos.",
            source="Player.bin / slots de estilo",
            quantity=2,
            known_pending={
                "tipo": "indice_estilo_defensivo_ausente_catalogo",
                "indice": defensive,
                "significado": "O índice defensivo foi lido no card, mas não existe no catálogo playstyle desta leitura.",
                "afeta_coleta": False,
                "bloqueia_motores": False,
                "bloqueia_publicacao": False,
                "acao": "Manter o índice bruto e conferir o catálogo playstyle da próxima leitura; não inventar um rótulo.",
            },
        )
    result = _component(
        "conferido_com_valor",
        meaning="Os estilos principal e defensivo foram conferidos; o defensivo foi resolvido pelo índice do catálogo.",
        source="Player.bin / slots de estilo + catálogo playstyle por índice",
        quantity=2,
    )
    result["prova_indice_defensivo"] = {
        "indice": defensive,
        "id_jogo": catalog_record.get("id_jogo"),
        "nome_pt": catalog_record.get("nome_pt"),
        "proveniencia": catalog_record.get("proveniencia") or [],
    }
    return result


def _impetus_component(card: dict[str, Any], catalog: dict[str, dict[str, Any]]) -> dict[str, Any]:
    fields = ("booster_primary", "booster_conditional")
    absent = [field for field in fields if field not in card]
    if absent:
        return _component(
            "nao_conferido",
            meaning="Os dois espaços de Ímpeto não foram totalmente lidos.",
            source="Player.bin + PlayerBooster.bin",
            reason="slots não lidos: " + ", ".join(absent),
        )
    filled: list[int] = []
    for field in fields:
        slot = card.get(field)
        if not isinstance(slot, dict) or slot.get("state") not in SLOT_STATES:
            return _component(
                "leitura_com_problema",
                meaning="Um espaço de Ímpeto voltou sem estado físico válido.",
                source="Player.bin / slots de Ímpeto",
                reason=f"slot inválido: {field}",
            )
        if slot.get("state") == "preench":
            try:
                code = int(slot["id"])
            except (KeyError, TypeError, ValueError):
                return _component(
                    "leitura_com_problema",
                    meaning="Um Ímpeto preenchido voltou sem código válido.",
                    source="Player.bin / slots de Ímpeto",
                    reason=f"código ausente: {field}",
                )
            record = catalog.get(str(code))
            if not record:
                return _component(
                    "leitura_com_problema",
                    meaning="O card aponta para um Ímpeto que não foi encontrado no catálogo físico atual.",
                    source="Player.bin + PlayerBooster.bin",
                    reason=f"Ímpeto {code} não resolvido",
                )
            effects = record.get("efeitos")
            if record.get("tipo_condicao_status") != "coletado" or not isinstance(effects, list) or not effects:
                return _component(
                    "leitura_com_problema",
                    meaning="O Ímpeto existe, mas os dados necessários ao cálculo ainda não estão completos.",
                    source="PlayerBooster.bin",
                    reason=f"Ímpeto {code} sem condição/efeitos computáveis",
                )
            if any(not isinstance(effect, dict) or not effect.get("codigo_atributo") or isinstance(effect.get("delta"), bool) or not isinstance(effect.get("delta"), int) for effect in effects):
                return _component(
                    "leitura_com_problema",
                    meaning="O Ímpeto existe, mas há efeito sem atributo ou valor calculável.",
                    source="PlayerBooster.bin",
                    reason=f"Ímpeto {code} com efeito inválido",
                )
            filled.append(code)
    if not filled:
        return _component(
            "conferido_sem_valor",
            meaning="Os dois espaços foram conferidos e o card não possui Ímpeto.",
            source="Player.bin / slots de Ímpeto",
            quantity=0,
        )
    return _component(
        "conferido_com_valor",
        meaning="Os espaços e os dados de cálculo dos Ímpetos foram conferidos.",
        source="Player.bin + PlayerBooster.bin",
        quantity=len(filled),
    )


def _dimensions_component(row: dict[str, Any] | None) -> dict[str, Any]:
    if row is None:
        return _component(
            "nao_conferido",
            meaning="Os vínculos de nacionalidade, clube, liga e tipo não foram lidos para este card.",
            source="dimensoes-fisicas.json",
            reason="card ausente da fotografia de dimensões",
        )
    if "pode_rodar_vinculos" not in row:
        return _component(
            "nao_conferido",
            meaning="A leitura dos vínculos não devolveu o resultado de validação.",
            source="dimensoes-fisicas.json",
            reason="pode_rodar_vinculos não informado",
        )
    unresolved_reason = str(row.get("falta_o_que_vinculos") or "vínculo físico não resolvido")
    club_code = row.get("codigo_clube")
    unresolved_club = (
        row.get("pode_rodar_vinculos") is not True
        and isinstance(club_code, int)
        and not isinstance(club_code, bool)
        and "codigo_clube sem definicao em Team.bin" in unresolved_reason
    )
    if unresolved_club:
        values = [row.get("codigo_nacionalidade"), club_code, row.get("tipo_carta_id")]
        return _component(
            "conferido_sem_vinculo_atual",
            meaning="Os códigos brutos foram lidos e a ausência atual do clube no Team.bin foi confirmada.",
            source="Player.bin + Country.bin + Team.bin + CompetitionEntry.bin",
            quantity=sum(value is not None for value in values),
            known_pending={
                "tipo": "clube_sem_vinculo_atual_por_licenca",
                "codigo_clube": club_code,
                "significado": "O card antigo preserva o código bruto do clube, mas a ligação atual sumiu após perda de licença.",
                "afeta_coleta": False,
                "bloqueia_motores": False,
                "bloqueia_publicacao": False,
                "acao": "Manter o aviso e o código bruto; não inventar um clube substituto.",
            },
        )
    if row.get("pode_rodar_vinculos") is not True:
        return _component(
            "leitura_com_problema",
            meaning="Os vínculos foram lidos, mas um código necessário ainda não foi resolvido.",
            source="Country.bin + Team.bin + CompetitionEntry.bin",
            reason=unresolved_reason,
        )
    values = [row.get("codigo_nacionalidade"), row.get("codigo_clube"), row.get("codigo_liga"), row.get("tipo_carta_id")]
    count = sum(value is not None for value in values)
    return _component(
        "conferido_com_valor" if count else "conferido_sem_valor",
        meaning="Os vínculos foram conferidos; códigos fisicamente ausentes continuam sendo respostas válidas.",
        source="Country.bin + Team.bin + CompetitionEntry.bin",
        quantity=count,
    )


def normalize_operator_overrides(value: Any) -> dict[str, dict[str, Any]]:
    if value in (None, {}):
        return {}
    if not isinstance(value, dict) or value.get("schema") != OVERRIDE_SCHEMA:
        raise ValueError("arquivo de marcações de prontidão inválido")
    rows = value.get("cards")
    if not isinstance(rows, list):
        raise ValueError("arquivo de marcações sem lista de cards")
    output: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not str(row.get("card_id") or ""):
            raise ValueError("marcação de prontidão sem card_id")
        card_id = str(row["card_id"])
        if card_id in output:
            raise ValueError(f"marcação de prontidão repetida: {card_id}")
        if row.get("estado") != "incompleto_confirmado":
            raise ValueError(f"estado manual não permitido para {card_id}")
        if not str(row.get("motivo") or "").strip():
            raise ValueError(f"marcação sem motivo para {card_id}")
        output[card_id] = dict(row)
    return output


def evaluate_card(
    card: dict[str, Any],
    *,
    dimension: dict[str, Any] | None,
    impetus_catalog: dict[str, dict[str, Any]],
    playstyle_catalog: dict[int, dict[str, Any]],
    operator_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    card_id = str(card.get("card_id") or "")
    components = {
        "dados_basicos": _basic_component(card),
        "atributos": _fixed_integer_collection(card, "attrs", 26, 40, 99, "Os 26 atributos"),
        "corpo": _fixed_integer_collection(card, "corpo", 12, 0, 255, "As 12 medidas corporais"),
        "posicoes": _aptitudes_component(card),
        "habilidades": _optional_relation_component(
            card,
            raw_field="skills",
            proof_field="habilidades_fisicas",
            label="Habilidades",
            identity_key="skill_id",
        ),
        "estilos_ia": _optional_relation_component(
            card,
            raw_field="ai_styles",
            proof_field="estilos_ia_fisicos",
            label="Estilos de IA",
            identity_key="bit",
        ),
        "estilos_de_jogo": _playstyles_component(card, playstyle_catalog),
        "impetos": _impetus_component(card, impetus_catalog),
        "vinculos": _dimensions_component(dimension),
    }
    missing = [item for name, component in components.items() if (item := _missing(name, component))]
    known_pending = [
        {"componente": name, **pending}
        for name, component in components.items()
        if isinstance((pending := component.get("pendencia_conhecida")), dict)
    ]
    resolution_pending = [
        {"componente": name, **pending}
        for name, component in components.items()
        if isinstance((pending := component.get("pendencia_de_resolucao")), dict)
    ]
    fingerprint_payload = {
        "regra": RULE_VERSION,
        "card_id": card_id,
        "card": {
            key: card.get(key)
            for key in (
                "name", "height", "weight", "age", "position", "weak_foot_usage",
                "weak_foot_accuracy", "foot", "form", "injury", "primary_style_id",
                "primary_style_unknown", "defensive_style_id",
                "attrs", "corpo", "aptitudes", "skills",
                "habilidades_fisicas", "ai_styles", "estilos_ia_fisicos",
                "booster_primary", "booster_conditional", "tipo", "roda_motor",
            )
        },
        "dimension": dimension,
        "impetos_usados": {
            str(code): impetus_catalog.get(str(code))
            for slot in (card.get("booster_primary"), card.get("booster_conditional"))
            if isinstance(slot, dict) and slot.get("state") == "preench"
            for code in [slot.get("id")]
        },
        "playstyle_defensivo_usado": playstyle_catalog.get(card.get("defensive_style_id")),
    }
    input_fingerprint = _sha256(fingerprint_payload)
    manual = None
    if operator_override:
        manual = {
            "estado": "incompleto_confirmado",
            "motivo": str(operator_override.get("motivo")),
            "componentes": list(operator_override.get("componentes") or []),
            "evidencia": operator_override.get("evidencia"),
            "marcado_em": operator_override.get("marcado_em"),
            "fingerprint_marcado": operator_override.get("input_fingerprint"),
            "insumos_mudaram_desde_marcacao": bool(operator_override.get("input_fingerprint") and operator_override.get("input_fingerprint") != input_fingerprint),
        }
        missing.append({
            "componente": "confirmacao_do_operador",
            "estado": "incompleto_confirmado",
            "motivo": manual["motivo"],
        })
    structurally_complete = not missing
    applicable = card.get("roda_motor") is True
    resolution_blocks_motor = any(item.get("bloqueia_motores") is True for item in resolution_pending)
    motor_eligible = structurally_complete and applicable and not resolution_blocks_motor
    if not applicable:
        state = "nao_aplicavel_aos_motores"
    elif not structurally_complete:
        state = "aguardando_insumos"
    elif resolution_blocks_motor:
        state = "aguardando_decisao_de_vinculo"
    else:
        state = "pronto_para_motores"
    return {
        "card_id": card_id,
        "nome": card.get("name"),
        "tipo": card.get("tipo"),
        "regra_completude": RULE_VERSION,
        "estado": state,
        "coleta_completa": structurally_complete,
        "motor_eligible": motor_eligible,
        "publicacao_independente": True,
        "publicacao_bloqueada_por_este_gate": False,
        "input_fingerprint": input_fingerprint,
        "faltando_coleta": missing,
        "faltando": missing,
        "pendencias_conhecidas": known_pending,
        "pendencias_de_resolucao": resolution_pending,
        "componentes": components,
        "marcacao_operador": manual,
    }


def build_artifact(
    cards: Iterable[dict[str, Any]],
    dimensions: dict[str, Any],
    metadata: dict[str, Any],
    *,
    contract_seal: dict[str, Any] | None = None,
    source_seal: dict[str, Any] | None = None,
    playstyle_catalog: Any = None,
    operator_overrides: Any = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    if isinstance(cards, (str, bytes, dict)) or not hasattr(cards, "__iter__"):
        raise ValueError("artefato de cartas inválido")
    dimension_rows = dimensions.get("cards") if isinstance(dimensions, dict) else None
    if not isinstance(dimension_rows, list):
        raise ValueError("fotografia de dimensões inválida")
    catalogs = metadata.get("catalogs") if isinstance(metadata, dict) else None
    impetus_rows = ((catalogs or {}).get("impetos") or {}).get("records") if isinstance(catalogs, dict) else None
    if not isinstance(impetus_rows, list):
        raise ValueError("catálogo físico de Ímpetos inválido")
    metadata_playstyle_rows = ((catalogs or {}).get("playstyles") or {}).get("records") if isinstance(catalogs, dict) else None
    playstyles_by_index = _build_playstyle_catalog(metadata_playstyle_rows, playstyle_catalog)
    dimensions_by_id: dict[str, dict[str, Any]] = {}
    for row in dimension_rows:
        if not isinstance(row, dict) or not str(row.get("card_id") or ""):
            raise ValueError("fotografia de dimensões sem card_id")
        card_id = str(row["card_id"])
        if card_id in dimensions_by_id:
            raise ValueError(f"dimensão repetida para card_id {card_id}")
        dimensions_by_id[card_id] = row
    impetus_catalog: dict[str, dict[str, Any]] = {}
    for row in impetus_rows:
        if not isinstance(row, dict) or row.get("id") is None:
            raise ValueError("catálogo físico de Ímpetos sem identidade")
        code = str(row["id"])
        if code in impetus_catalog:
            raise ValueError(f"Ímpeto físico repetido: {code}")
        impetus_catalog[code] = row
    overrides = normalize_operator_overrides(operator_overrides)
    seen: set[str] = set()
    evaluations: list[dict[str, Any]] = []
    for card in cards:
        if not isinstance(card, dict) or not str(card.get("card_id") or ""):
            raise ValueError("artefato canônico contém carta sem card_id")
        card_id = str(card["card_id"])
        if card_id in seen:
            raise ValueError(f"carta repetida no artefato canônico: {card_id}")
        seen.add(card_id)
        evaluations.append(evaluate_card(
            card,
            dimension=dimensions_by_id.get(card_id),
            impetus_catalog=impetus_catalog,
            playstyle_catalog=playstyles_by_index,
            operator_override=overrides.get(card_id),
        ))
    orphan_overrides = sorted(set(overrides) - seen, key=lambda value: int(value) if value.isdigit() else value)
    state_counts: dict[str, int] = {}
    component_counts: dict[str, dict[str, int]] = {}
    known_pending_type_counts: dict[str, int] = {}
    resolution_pending_type_counts: dict[str, int] = {}
    known_pending_examples: dict[str, list[dict[str, Any]]] = {}
    for row in evaluations:
        state_counts[row["estado"]] = state_counts.get(row["estado"], 0) + 1
        for pending in row.get("pendencias_conhecidas") or []:
            pending_type = str(pending.get("tipo") or "sem_tipo")
            known_pending_type_counts[pending_type] = known_pending_type_counts.get(pending_type, 0) + 1
            bucket = known_pending_examples.setdefault(pending_type, [])
            if len(bucket) < 12:
                bucket.append({
                    "card_id": row["card_id"],
                    "nome": row.get("nome"),
                    "tipo": pending_type,
                    "tipo_carta": row.get("tipo"),
                    "componente": pending.get("componente"),
                    "motivo": pending.get("significado") or pending.get("acao"),
                })
        for pending in row.get("pendencias_de_resolucao") or []:
            pending_type = str(pending.get("tipo") or "sem_tipo")
            resolution_pending_type_counts[pending_type] = resolution_pending_type_counts.get(pending_type, 0) + 1
        for name, component in row["componentes"].items():
            bucket = component_counts.setdefault(name, {})
            state = str(component["estado"])
            bucket[state] = bucket.get(state, 0) + 1
    return {
        "schema": "clubef-prontidao-motores-v1",
        "regra_completude": RULE_VERSION,
        "gerado_em": generated_at or datetime.now(timezone.utc).isoformat(),
        "database_write": False,
        "escopo": "todas_as_cartas_da_leitura",
        "publicacao_independente": True,
        "publicacao_bloqueada_por_este_gate": False,
        "semantica_ausencia": "conferido_sem_valor e conferido_sem_vinculo_atual são completos; nao_conferido é incompleto",
        "contract_seal": contract_seal or {},
        "source_seal": source_seal or {},
        "summary": {
            "cards": len(evaluations),
            "motor_eligible": sum(row["motor_eligible"] is True for row in evaluations),
            "aguardando_insumos": sum(row["estado"] == "aguardando_insumos" for row in evaluations),
            "aguardando_decisao_de_vinculo": sum(row["estado"] == "aguardando_decisao_de_vinculo" for row in evaluations),
            "nao_aplicavel_aos_motores": sum(row["estado"] == "nao_aplicavel_aos_motores" for row in evaluations),
            "coleta_incompleta_total": sum(row["coleta_completa"] is False for row in evaluations),
            "pendencias_conhecidas_total": sum(len(row.get("pendencias_conhecidas") or []) for row in evaluations),
            "cartas_com_pendencia_conhecida": sum(bool(row.get("pendencias_conhecidas")) for row in evaluations),
            "pendencias_conhecidas_por_tipo": known_pending_type_counts,
            "pendencias_conhecidas_exemplos_por_tipo": known_pending_examples,
            "pendencias_de_resolucao_total": sum(len(row.get("pendencias_de_resolucao") or []) for row in evaluations),
            "cartas_com_pendencia_de_resolucao": sum(bool(row.get("pendencias_de_resolucao")) for row in evaluations),
            "pendencias_de_resolucao_por_tipo": resolution_pending_type_counts,
            "marcacoes_operador": len(overrides),
            "marcacoes_sem_card_atual": orphan_overrides,
            "estados": state_counts,
            "componentes": component_counts,
        },
        "cards": evaluations,
    }


def build_operator_review(artifact: dict[str, Any]) -> dict[str, Any]:
    """Reduz o artefato integral ao envelope usado pela tela do operador."""
    if not isinstance(artifact, dict) or artifact.get("schema") != "clubef-prontidao-motores-v1":
        raise ValueError("artefato de prontidão inválido para revisão do operador")
    rows = artifact.get("cards")
    if not isinstance(rows, list):
        raise ValueError("artefato de prontidão sem lista de cartas")
    review_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("artefato de prontidão contém carta inválida")
        if row.get("tipo") != "colecionavel":
            continue
        review_rows.append({
            "card_id": row.get("card_id"),
            "nome": row.get("nome"),
            "estado": row.get("estado"),
            "coleta_completa": row.get("coleta_completa"),
            "motor_eligible": row.get("motor_eligible"),
            "input_fingerprint": row.get("input_fingerprint"),
            "faltando": list(row.get("faltando_coleta") or []),
            "pendencias_conhecidas": list(row.get("pendencias_conhecidas") or []),
            "marcacao_operador": row.get("marcacao_operador"),
        })
    return {
        "schema": "clubef-prontidao-motores-revisao-operador-v1",
        "regra_completude": artifact.get("regra_completude"),
        "gerado_em": artifact.get("gerado_em"),
        "database_write": False,
        "publicacao_independente": True,
        "publicacao_bloqueada_por_este_gate": False,
        "summary": {
            "cartas_colecionaveis": len(review_rows),
            "motor_eligible": sum(row.get("motor_eligible") is True for row in review_rows),
            "aguardando_insumos": sum(row.get("estado") == "aguardando_insumos" for row in review_rows),
            "aguardando_decisao_de_vinculo": sum(row.get("estado") == "aguardando_decisao_de_vinculo" for row in review_rows),
            "marcacoes_operador": sum(row.get("marcacao_operador") is not None for row in review_rows),
        },
        "cards": review_rows,
    }
