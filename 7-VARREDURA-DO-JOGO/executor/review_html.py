"""Renderização leve e somente leitura do resultado do Extrator.

O resultado técnico pode ser grande porque preserva todas as diferenças por
chave e procedência. Este módulo nunca abre fontes do jogo ou o banco: ele
percorre ``resultado.json`` já salvo, materializa um HTML limitado para leitura
humana e registra um manifesto rastreável da execução.
"""
from __future__ import annotations

import html
import json
import mmap
import re
import time
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from card_impetus import resolve_impetus_presentation_label


SCHEMA = "clubef-result-review-html-v5-radar-e-motores"
SAMPLE_LIMIT_PER_CHECK_AND_TYPE = 50
DEFAULT_SCAN_TIMEOUT_SECONDS = 40.0
DIVERGENCE_KINDS = (
    "new",
    "removed",
    "altered",
    "repeated",
    "invalid",
    "known_pending",
    "historical_unresolved",
)
TYPE_LABELS = {
    "new": "Novo no jogo",
    "removed": "Não apareceu no jogo atual",
    "altered": "Mudou no jogo",
    "repeated": "Registro duplicado",
    "invalid": "Não foi possível conferir",
    "known_pending": "Pendência já conhecida",
    "historical_unresolved": "Registro antigo guardado como referência",
}
FAMILY_LABELS = {
    "cartas": "Cartas e jogadores",
    "relacoes": "Dados das cartas: habilidades, posições e estilos",
    "dimensoes": "Altura, peso e outros dados dos jogadores",
    "impetos": "Ímpetos",
    "tecnicos": "Técnicos",
    "textos": "Textos do jogo",
    "catalogos": "Listas e nomes usados pelo jogo",
    "metadados": "Arquivos necessários para a leitura",
}
STATE_LABELS = {
    "review": "Precisa de atenção",
    "observed": "Sem mudança",
    "ready": "Leitura concluída",
    "technical_issue": "Não foi possível concluir",
    "error": "Falha na leitura",
}
CATALOG_LABELS = {
    "clube_novo.estilo_ia": "Estilos de IA",
    "clube_novo.habilidade_jogo": "Habilidades",
    "clube_novo.atributo_jogo": "Atributos dos jogadores",
    "clube_novo.posicao_jogo": "Posições dos jogadores",
    "clube_novo.impeto_jogo": "Ímpetos",
    "clube_novo.texto_do_jogo": "Textos do jogo",
    "clube_novo.tecnico_jogo": "Técnicos",
}
FIELD_LABELS = {
    "altura": "altura",
    "peso": "peso",
    "idade": "idade",
    "forma": "forma física",
    "pe": "pé dominante",
    "pe_ruim_uso": "uso do pé não dominante",
    "pe_ruim_precisao": "precisão do pé não dominante",
    "resistencia_lesao": "resistência a lesões",
    "tipo": "tipo da carta",
    "nacionalidade": "nacionalidade",
    "clube": "clube",
    "liga": "liga",
    "ordem": "ordem na lista",
}
_REPORT_LINE = re.compile(r'^\s{4}"([^"]+)": \{\s*$')
_ROOT_CLASSIFICATION_LINE = re.compile(r'^\s{6}"classification": \{\s*$')
_BUCKET_LINE = re.compile(
    r'^\s{8}"(new|removed|altered|repeated|invalid|known_pending|historical_unresolved)": \[\s*$'
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compact(value: Any, limit: int = 700) -> str:
    if value is None:
        return "—"
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _json_value_bytes(raw: mmap.mmap, start: int) -> bytes:
    """Lê um único valor JSON sem carregar o resultado inteiro na memória."""
    size = len(raw)
    while start < size and raw[start] in b" \t\r\n":
        start += 1
    if start >= size:
        raise ValueError("valor JSON ausente")

    opening = raw[start]
    if opening not in (ord("{"), ord("["), ord('"')):
        end = start
        while end < size and raw[end] not in (ord(","), ord("\r"), ord("\n"), ord("}")):
            end += 1
        return raw[start:end]

    in_string = opening == ord('"')
    escaped = False
    depth = 0 if in_string else 1
    index = start + 1
    while index < size:
        char = raw[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == ord("\\"):
                escaped = True
            elif char == ord('"'):
                in_string = False
                if depth == 0:
                    return raw[start : index + 1]
        else:
            if char == ord('"'):
                in_string = True
            elif char in (ord("{"), ord("[")):
                depth += 1
            elif char in (ord("}"), ord("]")):
                depth -= 1
                if depth == 0:
                    return raw[start : index + 1]
        index += 1
    raise ValueError("valor JSON sem fechamento")


def _top_level_value(raw: mmap.mmap, key: str) -> Any:
    marker = b'\n  "' + key.encode("utf-8") + b'": '
    position = raw.find(marker)
    if position < 0:
        return None
    value_start = position + len(marker)
    return json.loads(_json_value_bytes(raw, value_start))


def _read_result_header(result_path: Path) -> dict[str, Any]:
    keys = (
        "contract_seal",
        "database_write",
        "physical_reader",
        "families",
        "artifacts",
        "state",
        "launcher_protocol_version",
        "comparisons",
        "review_gate",
        "application_status",
        "radar_lancamentos",
        "motor_readiness",
    )
    with result_path.open("rb") as handle:
        with mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as raw:
            return {key: _top_level_value(raw, key) for key in keys}


def _optional_json(path: Path, *, max_bytes: int = 64 * 1024 * 1024) -> dict[str, Any]:
    """Lê um artefato auxiliar limitado, sem transformar ausência em falha."""
    if not path.is_file() or path.stat().st_size > max_bytes:
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _launch_radar_context(run_dir: Path, header: dict[str, Any]) -> dict[str, Any]:
    summary = header.get("radar_lancamentos") if isinstance(header.get("radar_lancamentos"), dict) else {}
    artifact = _optional_json(run_dir / "radar-lancamentos.json")
    boxes = artifact.get("boxes") if isinstance(artifact.get("boxes"), list) else []
    interesting = [
        box for box in boxes
        if isinstance(box, dict)
        and (box.get("estado") == "nova" or box.get("conteudo_alterado") is True)
    ]
    comparison = artifact.get("comparison") if isinstance(artifact.get("comparison"), dict) else {}
    if not interesting and comparison.get("status") != "comparado":
        # Na primeira rodada não se inventa novidade: mostramos só uma amostra
        # da referência local, claramente identificada como tal.
        interesting = [box for box in boxes if isinstance(box, dict)][:12]
    return {
        "available": bool(artifact or summary),
        "counts": artifact.get("counts") if isinstance(artifact.get("counts"), dict) else {
            "boxes": summary.get("boxes"),
            "cards_mapped": summary.get("cards_mapped"),
            "records_ignored": summary.get("records_ignored"),
            "ignored_absent_from_current_player": summary.get("ignored_absent_from_current_player"),
            "ignored_by_classification": summary.get("ignored_by_classification") or {},
            "by_state": summary.get("by_state") or {},
        },
        "comparison": comparison if comparison else {
            "status": summary.get("comparison_status"),
            "reason": None,
        },
        "integration": artifact.get("integration_contract") if isinstance(artifact.get("integration_contract"), dict) else {},
        "meaning": artifact.get("meaning"),
        "interesting_boxes": interesting[:30],
        "interesting_total": len(interesting),
        "ignored_records": artifact.get("ignored_records")[:80] if isinstance(artifact.get("ignored_records"), list) else [],
        "database_write": False,
        "publication_independent": True,
    }


def _motor_readiness_context(run_dir: Path, header: dict[str, Any]) -> dict[str, Any]:
    result_summary = header.get("motor_readiness") if isinstance(header.get("motor_readiness"), dict) else {}
    compact_summary = _optional_json(run_dir / "resumo-prontidao-motores.json", max_bytes=8 * 1024 * 1024)
    artifact_path = run_dir / "prontidao-motores.json"
    artifact_header: dict[str, Any] = {}
    if not compact_summary and artifact_path.is_file():
        try:
            with artifact_path.open("rb") as handle:
                with mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as raw:
                    artifact_header = {
                        "schema": _top_level_value(raw, "schema"),
                        "regra_completude": _top_level_value(raw, "regra_completude"),
                        "summary": _top_level_value(raw, "summary"),
                        "semantica_ausencia": _top_level_value(raw, "semantica_ausencia"),
                    }
        except (OSError, ValueError, json.JSONDecodeError):
            artifact_header = {}
    # O artefato pode ter sido recalculado depois que o operador marcou uma
    # carta como incompleta. Nesse caso ele é a fotografia mais recente; o
    # resultado físico original permanece imutável.
    summary = compact_summary.get("summary") if isinstance(compact_summary.get("summary"), dict) else artifact_header.get("summary") if isinstance(artifact_header.get("summary"), dict) else result_summary.get("summary")
    state = result_summary.get("state")
    if compact_summary or artifact_header:
        waiting = int((summary or {}).get("aguardando_insumos") or 0)
        waiting_resolution = int((summary or {}).get("aguardando_decisao_de_vinculo") or 0)
        state = "pronto" if waiting + waiting_resolution == 0 else "parcial_fail_closed_para_motores"
    if artifact_header.get("schema") == "clubef-prontidao-motores-indisponivel-v1":
        state = "indisponivel_fail_closed"
    return {
        "available": bool(result_summary or compact_summary or artifact_header),
        "state": state,
        "summary": summary if isinstance(summary, dict) else {},
        "reason": result_summary.get("reason"),
        "rule": compact_summary.get("regra_completude") or artifact_header.get("regra_completude"),
        "database_write": False,
        "publication_independent": True,
        "publication_blocked": False,
    }


def _brace_delta(text: str) -> int:
    depth = 0
    in_string = False
    escaped = False
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        else:
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
    return depth


def _entry_identity(entry: dict[str, Any]) -> dict[str, Any]:
    for key in ("chave_canonica", "vinculo_banco"):
        value = entry.get(key)
        if isinstance(value, dict) and value:
            return value
    catalog = entry.get("catalogo")
    if isinstance(catalog, str) and catalog:
        return {"catalogo": catalog}
    physical = entry.get("fonte_fisica")
    if isinstance(physical, dict):
        stable = {
            key: value
            for key, value in physical.items()
            if key.endswith("_id") or key in ("bit", "registro", "campo_id", "ordem_fisica")
        }
        if stable:
            return stable
    return {}


def _entry_provenance(entry: dict[str, Any]) -> Any:
    physical = entry.get("fonte_fisica")
    if isinstance(physical, dict):
        selected = {
            key: value
            for key, value in physical.items()
            if key in ("fotografia", "artefato", "arquivo", "registro", "hash", "campo_id", "bit", "largura", "ordem_fisica", "procedencia")
        }
        if selected:
            return selected
    for key in ("procedencia_fisica", "procedencia", "proveniencia"):
        value = entry.get(key)
        if value is not None:
            return value
    changed = entry.get("campos_alterados")
    if isinstance(changed, list):
        provenance = [item.get("proveniencia") for item in changed if isinstance(item, dict) and item.get("proveniencia")]
        if provenance:
            return provenance[:3]
    return None


def _entry_detail(entry: dict[str, Any]) -> str:
    reason = entry.get("motivo") or entry.get("reason")
    if reason:
        return str(reason)
    changed = entry.get("campos_alterados")
    if isinstance(changed, list) and changed:
        parts: list[str] = []
        for item in changed[:3]:
            if not isinstance(item, dict):
                continue
            destination = item.get("destino") or item.get("chave_campo") or "campo"
            physical = item.get("fisico", item.get("valor_fisico"))
            database = item.get("banco", item.get("valor_banco"))
            parts.append(f"{destination}: físico={_compact(physical, 120)}; banco={_compact(database, 120)}")
        if parts:
            suffix = " (+ campos)" if len(changed) > len(parts) else ""
            return "; ".join(parts) + suffix
    if "valor_fisico" in entry or "valor_banco" in entry:
        return "físico=" + _compact(entry.get("valor_fisico"), 180) + "; banco=" + _compact(entry.get("valor_banco"), 180)
    scope = entry.get("escopo") or entry.get("family")
    return f"Divergência classificada no escopo {scope}." if scope else "Divergência classificada por chave/procedência."


def _report_family(report_key: str) -> str:
    return report_key.split(":", 1)[0]


def _family_label(value: str) -> str:
    return FAMILY_LABELS.get(value, value.replace("_", " ").title())


def _canonical_family_key(value: Any) -> str:
    normalized = str(value or "").strip().casefold()
    aliases = {
        "cartas": "cartas",
        "cartas e jogadores": "cartas",
        "relações": "relacoes",
        "relacoes": "relacoes",
        "habilidades, posições e atributos dos jogadores": "relacoes",
        "dimensões": "dimensoes",
        "dimensoes": "dimensoes",
        "dados físicos dos jogadores": "dimensoes",
        "ímpetos": "impetos",
        "impetos": "impetos",
        "técnicos": "tecnicos",
        "tecnicos": "tecnicos",
        "textos": "textos",
        "textos do jogo": "textos",
        "catálogos": "catalogos",
        "catalogos": "catalogos",
        "metadados": "metadados",
    }
    return aliases.get(normalized, normalized)


def _stable_key(value: Any) -> str | None:
    """Normaliza uma chave somente para consulta de apresentação.

    A chave original continua no envelope técnico. Esta função jamais une ou
    classifica dados: ela apenas permite obter um rótulo já existente para uma
    identidade canônica que o resultado já traz.
    """
    if value is None:
        return None
    return str(value).strip()


def _sample_identity_value(sample: dict[str, Any], *keys: str) -> Any:
    identity = sample.get("identity")
    if isinstance(identity, dict):
        for key in keys:
            if identity.get(key) is not None:
                return identity[key]
    raw = sample.get("raw_entry")
    if isinstance(raw, dict):
        for key in keys:
            if raw.get(key) is not None:
                return raw[key]
    return None


def _first_human_label(row: Any) -> str | None:
    if not isinstance(row, dict):
        return None
    for key in ("nome_tela", "nome_pt", "nome_en", "texto", "nome", "nome_antigo"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _card_presentation(row: Any) -> str | None:
    if not isinstance(row, dict):
        return None
    name = row.get("nome")
    if not isinstance(name, str) or not name.strip():
        return None
    descriptors = [
        value.strip()
        for value in (row.get("posicao"), row.get("nacionalidade"))
        if isinstance(value, str) and value.strip()
    ]
    suffix = " · ".join(descriptors)
    return f"{name.strip()} ({suffix})" if suffix else name.strip()


def _presentation_context(run_dir: Path, samples: list[dict[str, Any]]) -> dict[str, Any]:
    """Carrega rótulos já declarados, por chaves exatas, só para a interface.

    ``pedido-leitura.json`` e ``cartas-fisicas.csv`` pertencem à mesma
    execução. Nenhum nome é usado para descobrir, identificar, mesclar ou
    classificar registros; o HTML só consulta rótulos depois que a comparação
    por chave/procedência já terminou.
    """
    wanted_cards = {
        key
        for sample in samples
        for key in (_stable_key(_sample_identity_value(sample, "card_id")),)
        if key is not None
    }
    cards: dict[str, dict[str, str]] = {}
    cards_path = run_dir / "cartas-fisicas.csv"
    if wanted_cards and cards_path.is_file():
        try:
            with cards_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
                for row in csv.DictReader(handle):
                    key = _stable_key(row.get("card_id"))
                    if key in wanted_cards:
                        cards[key] = {
                            name: str(row.get(name) or "")
                            for name in ("nome", "posicao", "nacionalidade", "tipo")
                        }
        except OSError:
            pass

    catalog_rows: dict[str, dict[str, dict[str, Any]]] = {
        "habilidade_jogo": {},
        "estilo_ia": {},
        "impeto_jogo": {},
        "atributo_jogo": {},
        "posicao_jogo": {},
        "tecnico_jogo": {},
        "texto_do_jogo": {},
    }
    reading_contract: dict[str, Any] = {}
    plan_path = run_dir / "pedido-leitura.json"
    if plan_path.is_file():
        try:
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            if isinstance(plan, dict):
                reading_contract = plan
            catalogs = reading_contract.get("catalogos")
            if isinstance(catalogs, list):
                key_columns = {
                    "habilidade_jogo": "skill_id",
                    "estilo_ia": "bit",
                    "impeto_jogo": "codigo_jogo",
                    "atributo_jogo": "codigo",
                    "posicao_jogo": "id",
                    "tecnico_jogo": "id",
                }
                for catalog in catalogs:
                    if not isinstance(catalog, dict):
                        continue
                    table = catalog.get("table")
                    rows = catalog.get("rows")
                    if not isinstance(table, str) or not isinstance(rows, list):
                        continue
                    if table == "texto_do_jogo":
                        for row in rows:
                            if isinstance(row, dict):
                                section = _stable_key(row.get("secao"))
                                text_id = _stable_key(row.get("id_texto"))
                                if section is not None and text_id is not None:
                                    catalog_rows[table][f"{section}:{text_id}"] = row
                        continue
                    column = key_columns.get(table)
                    if column is None:
                        continue
                    for row in rows:
                        if isinstance(row, dict):
                            key = _stable_key(row.get(column))
                            if key is not None:
                                catalog_rows[table][key] = row
        except (OSError, json.JSONDecodeError):
            pass
    return {"cards": cards, "catalogs": catalog_rows, "reading_contract": reading_contract}


def _presentation_row(context: dict[str, Any], table: str, key: Any) -> dict[str, Any] | None:
    stable = _stable_key(key)
    rows = context.get("catalogs", {}).get(table, {})
    return rows.get(stable) if stable is not None and isinstance(rows, dict) else None


def _human_entity_title(sample: dict[str, Any], context: dict[str, Any]) -> str:
    raw = sample.get("raw_entry") if isinstance(sample.get("raw_entry"), dict) else {}
    family_key = sample.get("family_key")
    card_id = _sample_identity_value(sample, "card_id")
    card = _card_presentation(context.get("cards", {}).get(_stable_key(card_id) or ""))
    skill_id = _sample_identity_value(sample, "skill_id")
    skill = _first_human_label(_presentation_row(context, "habilidade_jogo", skill_id))
    style_bit = _sample_identity_value(sample, "bit", "estilo_ia_bit")
    style = _first_human_label(_presentation_row(context, "estilo_ia", style_bit))
    impulse_code = _sample_identity_value(sample, "codigo_impeto", "codigo_jogo", "impeto_id")
    impulse_label = resolve_impetus_presentation_label(context.get("reading_contract", {}), impulse_code)
    impulse = impulse_label["rotulo"]
    catalog = raw.get("catalogo") or _sample_identity_value(sample, "catalogo")

    if skill is not None:
        return f"Habilidade “{skill}”" + (f" de {card}" if card else "")
    if style is not None:
        return f"Estilo de IA “{style}”" + (f" de {card}" if card else "")
    if impulse_code is not None:
        return f"Ímpeto “{impulse}”" if impulse else "Ímpeto com rótulo do jogo ainda não comprovado"
    if isinstance(catalog, str) and catalog:
        return CATALOG_LABELS.get(catalog, "Catálogo em revisão")
    if family_key == "cartas":
        return f"Carta de {card}" if card else "Carta sem rótulo disponível no artefato de apresentação"
    if family_key == "relacoes":
        return f"Relação da carta {card}" if card else "Relação de carta em revisão"
    if family_key == "impetos":
        return "Relação de ímpeto em revisão"
    return _family_label(str(family_key or sample.get("family") or "dados"))


def _human_field_name(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value.rsplit(".", 1)[-1]
    return FIELD_LABELS.get(normalized, normalized.replace("_", " "))


def _human_change_description(sample: dict[str, Any]) -> str:
    raw = sample.get("raw_entry") if isinstance(sample.get("raw_entry"), dict) else {}
    kind = sample.get("type_key")
    if kind == "new":
        return "Um novo registro físico foi encontrado nesta leitura e precisa passar pela revisão do Extrator antes de qualquer aplicação."
    if kind == "removed":
        return "O registro ainda existe na base, mas não apareceu nesta leitura física; a diferença precisa ser revisada antes de qualquer aplicação."
    if kind == "repeated":
        return "A mesma identidade apareceu mais de uma vez na leitura física e precisa ser revisada antes de qualquer aplicação."
    if kind == "invalid":
        catalog = raw.get("catalogo") or _sample_identity_value(sample, "catalogo")
        if catalog == "clube_novo.estilo_ia":
            return "A lista observada de estilos de IA está em monitoramento: qualquer padrão ainda não reconhecido exige investigação e não é aplicado automaticamente."
        return "A conferência encontrou uma pendência técnica que precisa ser resolvida antes de aplicar este item."
    if kind == "known_pending":
        return (
            "Esta é uma pendência conhecida, monitorada e ainda não resolvida. "
            "Ela continua aparecendo em toda auditoria, mas não representa erro "
            "nem divergência comprovada nos dados atuais."
        )
    if kind == "historical_unresolved":
        return (
            "Este registro pertence ao arquivo histórico Steam e foi preservado "
            "fora da comparação com o catálogo atual. Ele não representa uma "
            "mudança no jogo nem uma divergência do banco enquanto o formato "
            "histórico não tiver um leitor semanticamente comprovado."
        )
    changed = raw.get("campos_alterados")
    if isinstance(changed, list) and changed:
        fields = [
            name
            for name in (_human_field_name(item.get("destino") or item.get("chave_campo")) for item in changed if isinstance(item, dict))
            if name
        ]
        if fields:
            joined = ", ".join(f"“{name}”" for name in fields[:3])
            suffix = " e outros campos" if len(fields) > 3 else ""
            return f"Há diferença entre a leitura do jogo e o registro atual no campo {joined}{suffix}."
    physical = raw.get("valor_fisico")
    database = raw.get("valor_banco")
    skill_id = _sample_identity_value(sample, "skill_id")
    if skill_id is not None and isinstance(physical, list) and isinstance(database, list) and physical and database:
        if len(physical) >= 3 and len(database) >= 3:
            return "A ordem desta habilidade é diferente entre a leitura física e o registro atual."
    return "O valor lido no jogo é diferente do valor registrado na base e precisa ser revisado antes de qualquer aplicação."


def _human_presentation(sample: dict[str, Any], context: dict[str, Any]) -> dict[str, str]:
    return {
        "title": _human_entity_title(sample, context),
        "change": _human_change_description(sample),
    }


def _scan_classification_samples(result_path: Path, sample_limit: int, timeout_seconds: float) -> tuple[dict[str, dict[str, int]], list[dict[str, Any]], bool, dict[str, dict[str, int]]]:
    """Conta classes e mantém só uma amostra limitada de cada verificação.

    O leitor reconhece apenas a classificação de raiz de cada relatório. Assim,
    não duplica as listas internas de uma relação e não precisa desserializar o
    JSON técnico inteiro, que pode ter centenas de megabytes.
    """
    deadline = time.monotonic() + timeout_seconds
    counts: dict[str, dict[str, int]] = {}
    samples: list[dict[str, Any]] = []
    samples_per_bucket: dict[tuple[str, str], int] = {}
    inside_reports = False
    report_key: str | None = None
    inside_root_classification = False
    current_kind: str | None = None
    capture_depth = 0
    capture_lines: list[str] = []
    capture_sample = False
    complete = True
    family_totals: dict[str, dict[str, Any]] = {}

    def append_sample(report: str, kind: str, entry: dict[str, Any]) -> None:
        family_key = _report_family(report)
        samples.append({
            "report": report,
            "family": _family_label(family_key),
            "family_key": family_key,
            "scope": entry.get("escopo") or entry.get("family"),
            "type": TYPE_LABELS[kind],
            "type_key": kind,
            "identity": _entry_identity(entry),
            "detail": _entry_detail(entry),
            "provenance": _entry_provenance(entry),
            "raw_entry": entry,
        })
        key = (report, kind)
        samples_per_bucket[key] = samples_per_bucket.get(key, 0) + 1

    def register_total(report: str, entry: dict[str, Any]) -> None:
        """Calcula totais reais sem reter o JSON técnico inteiro em memória."""
        family_key = _report_family(report)
        total = family_totals.setdefault(family_key, {
            "entities": set(),
            "field_keys": set(),
            "differences": 0,
        })
        identity = _entry_identity(entry)
        if identity:
            total["entities"].add(json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        changed = entry.get("campos_alterados")
        if isinstance(changed, list) and changed:
            total["differences"] += len(changed)
            for item in changed:
                if isinstance(item, dict):
                    field_key = item.get("destino") or item.get("chave_campo")
                    if field_key:
                        total["field_keys"].add(str(field_key))
        else:
            total["differences"] += 1

    with result_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            if time.monotonic() > deadline:
                complete = False
                break
            line = raw_line.rstrip("\r\n")
            if not inside_reports:
                if line == '  "comparison_reports": {':
                    inside_reports = True
                continue
            if line.startswith('  "review_gate":'):
                break

            report_match = _REPORT_LINE.match(line)
            if report_match:
                report_key = report_match.group(1)
                counts.setdefault(report_key, {kind: 0 for kind in DIVERGENCE_KINDS})
                inside_root_classification = False
                current_kind = None
                continue
            if report_key is None:
                continue
            if _ROOT_CLASSIFICATION_LINE.match(line):
                inside_root_classification = True
                current_kind = None
                continue
            if not inside_root_classification:
                continue

            bucket_match = _BUCKET_LINE.match(line)
            if bucket_match:
                current_kind = bucket_match.group(1)
                continue
            if current_kind is None:
                if line in ("      }", "      },"):
                    inside_root_classification = False
                continue

            stripped = line.strip()
            if capture_depth:
                capture_lines.append(line)
                capture_depth += _brace_delta(line)
                if capture_depth != 0:
                    continue
                assert current_kind is not None
                counts[report_key][current_kind] += 1
                try:
                    entry = json.loads("\n".join(capture_lines).rstrip().rstrip(","))
                except json.JSONDecodeError:
                    entry = None
                if isinstance(entry, dict):
                    register_total(report_key, entry)
                    if capture_sample:
                        append_sample(report_key, current_kind, entry)
                capture_lines = []
                capture_sample = False
                continue
            if stripped in ("]", "],"):
                current_kind = None
                continue
            if stripped.startswith("{"):
                key = (report_key, current_kind)
                capture_sample = samples_per_bucket.get(key, 0) < sample_limit
                capture_depth = _brace_delta(line)
                capture_lines = [line]
                if capture_depth == 0:
                    counts[report_key][current_kind] += 1
                    try:
                        entry = json.loads(line.rstrip().rstrip(","))
                    except json.JSONDecodeError:
                        entry = None
                    if isinstance(entry, dict):
                        register_total(report_key, entry)
                        if capture_sample:
                            append_sample(report_key, current_kind, entry)
                    capture_lines = []
                    capture_sample = False
    serialized_totals = {
        family: {
            "entities_affected": len(total["entities"]),
            "field_differences": int(total["differences"]),
            "information_count": len(total["field_keys"]),
        }
        for family, total in family_totals.items()
    }
    return counts, samples, complete, serialized_totals


def _artifact_references(run_dir: Path) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for artifact in sorted(run_dir.iterdir(), key=lambda item: item.name.lower()):
        if artifact.is_file():
            info = artifact.stat()
            output.append({
                "name": artifact.name,
                "bytes": info.st_size,
                "modified_at": datetime.fromtimestamp(info.st_mtime, timezone.utc).isoformat(),
            })
    return output


def _sources_from_run(run_dir: Path) -> dict[str, Any]:
    source_path = run_dir / "fontes.json"
    if not source_path.is_file():
        return {}
    try:
        raw = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {
        str(role): {
            "found": bool(value.get("found")) if isinstance(value, dict) else False,
            "location": value.get("location") if isinstance(value, dict) else None,
            "reason": value.get("reason") if isinstance(value, dict) else None,
        }
        for role, value in raw.items()
    }


def _family_summaries(header: dict[str, Any], report_counts: dict[str, dict[str, int]], complete: bool, real_totals: dict[str, dict[str, int]]) -> list[dict[str, Any]]:
    raw_families = header.get("families") if isinstance(header.get("families"), dict) else {}
    comparisons = header.get("comparisons") if isinstance(header.get("comparisons"), dict) else {}
    review_gate = header.get("review_gate") if isinstance(header.get("review_gate"), dict) else {}
    gate_families = review_gate.get("families") if isinstance(review_gate.get("families"), dict) else {}
    source_by_key: dict[str, tuple[str, dict[str, Any]]] = {}
    for raw_label, source in raw_families.items():
        key = _canonical_family_key(raw_label)
        source_by_key[key] = (str(raw_label), source if isinstance(source, dict) else {})
    report_by_key: dict[str, list[str]] = {}
    for report in report_counts:
        report_by_key.setdefault(_report_family(report), []).append(report)
    order = list(source_by_key) + [key for key in report_by_key if key not in source_by_key]
    summaries: list[dict[str, Any]] = []
    for family_key in order:
        raw_label, source = source_by_key.get(family_key, (family_key, {}))
        label = _family_label(family_key)
        totals = {kind: 0 for kind in DIVERGENCE_KINDS}
        reports = report_by_key.get(family_key, [])
        for report in reports:
            for kind in DIVERGENCE_KINDS:
                totals[kind] += int((report_counts.get(report) or {}).get(kind, 0))
        comparison = comparisons.get(raw_label) if isinstance(comparisons.get(raw_label), dict) else {}
        total = sum(totals.values())
        state = str(source.get("state") or "observed")
        canonical_changes = sum(int(totals[kind]) for kind in ("new", "removed", "altered"))
        technical_problems = sum(int(totals[kind]) for kind in ("repeated", "invalid"))
        gate_family = gate_families.get(family_key) if isinstance(gate_families.get(family_key), dict) else {}
        blocks_application = gate_family.get("approved") is False
        gate_reasons = gate_family.get("reasons") if isinstance(gate_family.get("reasons"), list) else []
        style_catalog_pending = any("estilo_ia" in str(reason) for reason in gate_reasons)
        if totals["known_pending"] or style_catalog_pending:
            blocks_application = False
        if not complete:
            state_label = "Resumo incompleto"
            status_tone = "error"
            detail = "O arquivo do resultado não pôde ser lido até o fim; as quantidades desta linha podem estar incompletas."
            operator_action = "Não envie alterações ao banco. Abra o log do Extrator e gere novamente este relatório a partir do resultado salvo."
        elif technical_problems or state in ("technical_issue", "error"):
            state_label = "Não foi possível conferir tudo"
            status_tone = "error"
            detail = "A leitura encontrou um problema que impede confiar nesta parte do resultado."
            operator_action = "Não envie alterações desta parte ao banco. Abra os itens vermelhos e consulte o log."
        elif canonical_changes:
            state_label = "Mudança encontrada"
            status_tone = "warning"
            detail = f"O jogo apresenta {_amount(canonical_changes, 'mudança que ainda não está refletida', 'mudanças que ainda não estão refletidas')} no banco."
            operator_action = "Confira os itens abaixo. Só aprove e envie ao banco se cada mudança estiver correta."
        elif totals["known_pending"] and total == totals["known_pending"]:
            state_label = "Pendência já conhecida"
            status_tone = "warning"
            detail = f"Há {_amount(totals['known_pending'], 'assunto que o programa já acompanha', 'assuntos que o programa já acompanha')} e continuará mostrando até ser resolvido. Não é falha desta extração."
            operator_action = "Este aviso não entra no pacote de envio. Se aparecer outra mudança comprovada, ela poderá ser marcada separadamente."
        elif totals["historical_unresolved"] and total == totals["historical_unresolved"]:
            state_label = "Sem mudança atual; há referência antiga"
            status_tone = "info"
            detail = f"Os dados atuais conferem. {_amount(totals['historical_unresolved'], 'registro de uma versão antiga foi guardado', 'registros de uma versão antiga foram guardados')} só para referência e não contam como mudança de hoje."
            operator_action = "Nada a corrigir hoje. Não use esses registros antigos para alterar o banco; o programa continuará guardando o aviso."
        elif blocks_application and style_catalog_pending:
            state_label = "Conferido, com uma pendência conhecida"
            status_tone = "warning"
            detail = "Os dados encontrados nas cartas conferem, mas o jogo ainda não forneceu uma lista completa e comprovada de todos os Estilos de IA possíveis."
            operator_action = "Mantenha a observação no relatório. Ela fica fora do pacote; outras mudanças comprovadas podem ser marcadas separadamente."
        elif blocks_application:
            state_label = "Conferido, mas não pode ser enviado"
            status_tone = "warning"
            detail = "A leitura terminou, porém existe uma pendência que impede enviar alterações desta parte ao banco."
            operator_action = "Leia o aviso correspondente antes de qualquer ação."
        elif state == "ready":
            state_label = "Arquivos lidos"
            status_tone = "success"
            detail = "Os arquivos necessários foram encontrados e lidos."
            operator_action = "Nada a fazer."
        else:
            state_label = "Sem mudança"
            status_tone = "success"
            detail = "O que foi encontrado no jogo corresponde ao que já está salvo."
            operator_action = "Nada a fazer."
        if blocks_application:
            detail += " O programa não libera o envio de alterações desta parte enquanto a pendência continuar aberta."
        summaries.append({
            "family_key": family_key,
            "family": label,
            "state": state,
            "state_label": state_label,
            "status_tone": status_tone,
            "blocks_application": blocks_application,
            "operator_action": operator_action,
            "counts": totals,
            "reports": reports,
            "classification_complete": comparison.get("classification_complete"),
            "technical_integrity": comparison.get("technical_integrity"),
            "exact_match": comparison.get("exact_match"),
            "entities_affected": int((real_totals.get(family_key) or {}).get("entities_affected", 0)),
            "field_differences": int((real_totals.get(family_key) or {}).get("field_differences", 0)),
            "information_count": int((real_totals.get(family_key) or {}).get("information_count", 0)),
            "detail": detail,
        })
    return summaries


def _build_model(result_path: Path, sample_limit: int, timeout_seconds: float) -> dict[str, Any]:
    header = _read_result_header(result_path)
    report_counts, samples, scan_complete, real_totals = _scan_classification_samples(result_path, sample_limit, timeout_seconds)
    run_dir = result_path.parent
    presentation = _presentation_context(run_dir, samples)
    for sample in samples:
        sample["presentation"] = _human_presentation(sample, presentation)
    result_info = result_path.stat()
    family_summary = _family_summaries(header, report_counts, scan_complete, real_totals)
    total_classified = sum(sum(bucket.values()) for bucket in report_counts.values())
    execution = {
        "execution_id": run_dir.name,
        "result": result_path.name,
        "review_html": "resultado.html",
        "manifest": "manifesto-execucao.json",
    }
    model = {
        "schema": SCHEMA,
        "generated_at": _utc_now(),
        "source_result": {
            "name": result_path.name,
            "bytes": result_info.st_size,
            "modified_at": datetime.fromtimestamp(result_info.st_mtime, timezone.utc).isoformat(),
        },
        "execution": execution,
        "state": header.get("state"),
        "database_write": bool(header.get("database_write")),
        "program": {
            "physical_reader": header.get("physical_reader"),
            "launcher_protocol_version": header.get("launcher_protocol_version"),
        },
        "contract": header.get("contract_seal") if isinstance(header.get("contract_seal"), dict) else {},
        "sources": _sources_from_run(run_dir),
        "family_summary": family_summary,
        "divergence_summary": {
            "counts_by_report": report_counts,
            "total_classified": total_classified,
            "real_totals_by_family": real_totals,
            "sample_limit_per_check_and_type": sample_limit,
            "scan_complete": scan_complete,
            "technical_json_preserved": True,
        },
        "divergence_samples": samples,
        "review_gate": header.get("review_gate") if isinstance(header.get("review_gate"), dict) else {},
        "application_status": header.get("application_status") if isinstance(header.get("application_status"), dict) else {},
        "launch_radar": _launch_radar_context(run_dir, header),
        "motor_readiness": _motor_readiness_context(run_dir, header),
        "artifacts": _artifact_references(run_dir),
    }
    model["operator_summary"] = _overall_verdict(model)
    model["operator_warnings"] = _operator_warning_cards(model)
    model["manifest"] = {
        "schema": "clubef-execution-manifest-v1",
        "review_renderer_schema": model["schema"],
        "generated_at": model["generated_at"],
        "execution": execution,
        "result": model["source_result"],
        "program": model["program"],
        "contract": model["contract"],
        "sources": model["sources"],
        "families": family_summary,
        "review_gate": model["review_gate"],
        "launch_radar": model["launch_radar"],
        "motor_readiness": model["motor_readiness"],
        "database_write": model["database_write"],
        "artifacts": model["artifacts"],
    }
    return model


def _tag(value: Any) -> str:
    return re.sub(r"[^a-z0-9_-]", "-", str(value).lower())


def _amount(value: Any, singular: str, plural: str) -> str:
    count = int(value or 0)
    formatted = f"{count:,}".replace(",", ".")
    return f"{formatted} {singular if count == 1 else plural}"


def _number(value: Any) -> str:
    return f"{int(value or 0):,}".replace(",", ".")


def _operator_guidance(type_key: str, sample: dict[str, Any] | None = None) -> dict[str, str]:
    """Traduz uma classificação interna em instruções completas ao operador."""
    sample = sample if isinstance(sample, dict) else {}
    raw = sample.get("raw_entry") if isinstance(sample.get("raw_entry"), dict) else {}
    catalog = raw.get("catalogo") or _sample_identity_value(sample, "catalogo")
    if type_key == "known_pending" and catalog == "clube_novo.estilo_ia":
        return {
            "title": "Estilos de IA: a lista completa ainda não foi localizada",
            "meaning": "O programa consegue ler os Estilos de IA usados em cada carta, mas ainda não encontrou no jogo um arquivo que apresente a lista completa de todos os estilos possíveis.",
            "today": "Não foi encontrada diferença nos estilos usados pelas cartas atuais. Mesmo assim, a lista completa continua sem comprovação e a pendência permanece aberta.",
            "blocks": "Não bloqueia outras mudanças. Este aviso não é um dado novo e fica fora do pacote; dados novos comprovados aparecem separadamente para você marcar.",
            "action": "Não marque nem cadastre nada por causa deste aviso. Continue executando a varredura normalmente e, quando houver dados novos, marque somente os itens que deseja enviar.",
        }
    if type_key == "known_pending":
        return {
            "title": "Pendência já conhecida e ainda não resolvida",
            "meaning": "Este assunto já era conhecido antes desta varredura. O programa continuará mostrando o aviso até existir prova suficiente para encerrá-lo.",
            "today": "Não é uma mudança descoberta hoje, mas continua sendo uma informação incompleta que não pode ser escondida.",
            "blocks": "Não bloqueia outras mudanças. A pendência fica visível no relatório, mas não vira item de envio.",
            "action": "Não preencha nem corrija o dado por tentativa. Quando houver mudanças novas, marque apenas os itens comprovados que deseja enviar.",
        }
    if type_key == "historical_unresolved":
        return {
            "title": "Registros antigos de Ímpeto guardados como referência",
            "meaning": "São registros de uma versão antiga do jogo. Eles foram preservados, mas o formato antigo ainda não pode ser traduzido por completo com segurança.",
            "today": "Não. Eles não são tratados como mudança do jogo atual e não indicam diferença no banco de hoje.",
            "blocks": "Não por si só. Este aviso histórico não impede o envio de uma mudança atual que tenha sido comprovada por outras verificações.",
            "action": "Não altere o banco usando esses registros antigos. Nenhuma ação é necessária hoje; o programa continuará mantendo-os como referência.",
        }
    if type_key == "invalid":
        return {
            "title": "O programa não conseguiu conferir este item",
            "meaning": "Faltou uma informação obrigatória ou o conteúdo lido não pôde ser entendido com segurança.",
            "today": "Pode afetar os dados de hoje porque esta parte da leitura ficou sem confirmação.",
            "blocks": "Este item não pode ser marcado para envio. Outros itens válidos continuam disponíveis separadamente.",
            "action": "Deixe este item fora do envio. Abra os detalhes técnicos e o log para localizar a causa e execute a conferência novamente depois da correção.",
        }
    if type_key == "repeated":
        return {
            "title": "O mesmo item apareceu mais de uma vez",
            "meaning": "A leitura encontrou duas entradas com o mesmo código, por isso não pode escolher uma delas automaticamente.",
            "today": "Pode afetar os dados de hoje porque existe mais de uma versão para a mesma identidade.",
            "blocks": "Este item duplicado não pode ser marcado. Outros itens válidos continuam disponíveis separadamente.",
            "action": "Deixe este item fora do envio. Investigue a origem mostrada nos detalhes e repita a leitura após a correção.",
        }
    if type_key == "removed":
        return {
            "title": "Um item salvo não apareceu no jogo atual",
            "meaning": "O item existe no banco, mas não foi encontrado nesta leitura do jogo.",
            "today": "Sim. Pode ser uma remoção do jogo ou uma leitura incompleta e precisa de conferência humana.",
            "blocks": "Sim. O Extrator nunca apaga dados automaticamente por ausência.",
            "action": "Confirme a ausência no jogo. Se for real, trate a remoção em um procedimento próprio; não tente enviá-la como atualização comum.",
        }
    if type_key == "new":
        return {
            "title": "Novo item encontrado no jogo",
            "meaning": "O jogo contém um item que ainda não existe no banco.",
            "today": "Sim. É uma possível novidade desta versão do jogo.",
            "blocks": "Não necessariamente. Ele só poderá ser enviado se possuir destino, código e origem comprovados e se todas as travas estiverem liberadas.",
            "action": "Confira o nome e os valores. Só aprove o pacote no Extrator se o item estiver correto.",
        }
    return {
        "title": "Informação alterada no jogo",
        "meaning": "O valor encontrado no jogo é diferente do que está salvo no banco.",
        "today": "Sim. É uma diferença da leitura atual que precisa ser conferida.",
        "blocks": "Não necessariamente. O envio só fica disponível depois que todas as verificações e travas forem aprovadas.",
        "action": "Compare os valores mostrados. Só aprove o pacote no Extrator se a mudança estiver correta.",
    }


def _overall_verdict(model: dict[str, Any]) -> dict[str, Any]:
    families = model.get("family_summary") if isinstance(model.get("family_summary"), list) else []
    totals = {kind: sum(int((row.get("counts") or {}).get(kind) or 0) for row in families) for kind in DIVERGENCE_KINDS}
    changes = sum(totals[kind] for kind in ("new", "removed", "altered"))
    problems = sum(totals[kind] for kind in ("repeated", "invalid"))
    family_failures = sum(1 for row in families if row.get("status_tone") == "error")
    pending = totals["known_pending"]
    historical = totals["historical_unresolved"]
    application = model.get("application_status") if isinstance(model.get("application_status"), dict) else {}
    selectable = len(application.get("selectable_items") or [])
    not_selectable = int(application.get("not_selectable_count") or 0)
    blocked = bool(application.get("blockers"))
    if not model.get("divergence_summary", {}).get("scan_complete") or problems or family_failures:
        if selectable:
            action = f"Há {_amount(selectable, 'item válido disponível', 'itens válidos disponíveis')}. No Extrator, clique ESCOLHER O QUE ENVIAR e marque somente o que deseja subir; os itens com problema ficam fora da seleção."
        else:
            action = "Abra os avisos vermelhos e o log do Extrator. Nenhum item com problema pode ser marcado para envio."
        return {
            "tone": "error",
            "verdict": "A conferência terminou com um problema",
            "explanation": "Parte do resultado não pôde ser confirmada. Esses itens ficam visíveis, mas não entram no pacote selecionável.",
            "action": action,
            "changes": changes,
            "pending": pending,
            "historical": historical,
            "blocked": True,
        }
    if changes:
        if selectable:
            action = f"No Extrator, clique ESCOLHER O QUE ENVIAR. Nada vem marcado: escolha somente os {_amount(selectable, 'item válido que deseja subir', 'itens válidos que deseja subir')}, depois aprove e aplique o pacote separado."
        elif not_selectable:
            action = "As mudanças encontradas não podem ser enviadas automaticamente. Leia o motivo em cada item e não tente incluí-las por fora do Extrator."
        else:
            action = "Revise as mudanças abaixo. O Extrator só mostrará caixas para os itens que puderem ser enviados com segurança."
        return {
            "tone": "warning",
            "verdict": f"Foram encontradas {_amount(changes, 'mudança no jogo', 'mudanças no jogo')}",
            "explanation": "Essas mudanças ainda não foram enviadas ao banco. Os avisos e as travas continuam valendo.",
            "action": action,
            "changes": changes,
            "pending": pending,
            "historical": historical,
            "blocked": blocked,
        }
    if pending or historical or blocked:
        parts = []
        if pending:
            parts.append(_amount(pending, "pendência já conhecida", "pendências já conhecidas"))
        if historical:
            parts.append(_amount(historical, "registro antigo guardado como referência", "registros antigos guardados como referência"))
        warning_text = " e ".join(parts) if parts else "uma pendência em acompanhamento"
        return {
            "tone": "warning",
            "verdict": "Nenhuma mudança atual foi encontrada",
            "explanation": f"Os dados atuais conferem, mas o relatório mantém {warning_text}. Esses avisos não são falhas desta extração e também não foram escondidos.",
            "action": "Não há dados novos para enviar hoje. Leia os avisos abaixo; não faça correções manuais para tentar encerrá-los.",
            "changes": 0,
            "pending": pending,
            "historical": historical,
            "blocked": blocked,
        }
    return {
        "tone": "success",
        "verdict": "Tudo conferido; nenhuma mudança foi encontrada",
        "explanation": "O que foi lido no jogo corresponde ao que já está salvo.",
        "action": "Nada a fazer. Feche o relatório e execute uma nova varredura quando o jogo for atualizado.",
        "changes": 0,
        "pending": 0,
        "historical": 0,
        "blocked": False,
    }


def _operator_warning_cards(model: dict[str, Any]) -> list[dict[str, Any]]:
    samples = model.get("divergence_samples") if isinstance(model.get("divergence_samples"), list) else []
    cards: list[dict[str, Any]] = []
    warning_types = ("invalid", "repeated", "known_pending", "historical_unresolved")
    for summary in model.get("family_summary", []):
        counts = summary.get("counts") if isinstance(summary.get("counts"), dict) else {}
        for type_key in warning_types:
            count = int(counts.get(type_key) or 0)
            if not count:
                continue
            sample = next((item for item in samples if item.get("family_key") == summary.get("family_key") and item.get("type_key") == type_key), None)
            cards.append({
                "family": summary.get("family"),
                "family_key": summary.get("family_key"),
                "type_key": type_key,
                "count": count,
                "tone": "error" if type_key in ("invalid", "repeated") else "warning" if type_key == "known_pending" else "info",
                **_operator_guidance(type_key, sample),
            })
    priority = {"invalid": 0, "repeated": 1, "known_pending": 2, "historical_unresolved": 3}
    return sorted(cards, key=lambda item: (priority.get(str(item.get("type_key")), 9), str(item.get("family"))))


def _render_html(model: dict[str, Any]) -> str:
    esc = lambda value: html.escape(_compact(value), quote=True)
    def count_text(counts: dict[str, Any]) -> str:
        return " · ".join(f"{TYPE_LABELS[key]}: {int(counts.get(key, 0))}" for key in DIVERGENCE_KINDS)

    family_rows = "\n".join(
        "<tr><td>" + esc(row["family"]) + "</td><td><span class=\"state " + _tag(row["state"]) + "\">" + esc(row["state"]) + "</span></td><td>" + esc(count_text(row["counts"])) + "</td><td>" + esc(row["detail"]) + "</td></tr>"
        for row in model["family_summary"]
    )
    family_options = "<option value=\"all\">Todas</option>" + "".join(
        "<option value=\"" + esc(row["family"]) + "\">" + esc(row["family"]) + "</option>"
        for row in model["family_summary"]
    )
    type_options = "<option value=\"all\">Todos</option>" + "".join(
        "<option value=\"" + esc(label) + "\">" + esc(label) + "</option>" for label in TYPE_LABELS.values()
    )
    blocks: list[str] = []
    for sample in model["divergence_samples"]:
        blocks.append(
            "<article class=\"divergence\" data-family=\"" + esc(sample["family"]) + "\" data-type=\"" + esc(sample["type"]) + "\">"
            "<header><span class=\"pill " + _tag(sample["type_key"]) + "\">" + esc(sample["type"]) + "</span><strong>" + esc(sample["family"]) + "</strong><small>" + esc(sample["report"]) + "</small></header>"
            "<dl><dt>Chave canônica</dt><dd><code>" + esc(sample["identity"]) + "</code></dd>"
            "<dt>Detalhe</dt><dd>" + esc(sample["detail"]) + "</dd>"
            "<dt>Procedência</dt><dd><code>" + esc(sample["provenance"]) + "</code></dd></dl></article>"
        )
    if not blocks:
        blocks.append("<p id=\"empty-state\">Não há divergências classificadas para exibir nesta execução.</p>")
    artifacts = "\n".join(
        "<li><code>" + esc(item["name"]) + "</code> — " + esc(item["bytes"]) + " bytes</li>" for item in model["artifacts"]
    )
    source_rows = "\n".join(
        "<li><code>" + esc(role) + "</code> — " + ("encontrada" if value.get("found") else "ausente") + ("; " + esc(value.get("location")) if value.get("location") else "") + "</li>"
        for role, value in sorted(model["sources"].items())
    ) or "<li>Sem fotografia de fontes disponível.</li>"
    contract = model["contract"]
    review_gate = model["review_gate"]
    return f"""<!doctype html>
<html lang=\"pt-BR\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Divergências — {esc(model['execution']['execution_id'])}</title>
<style>
:root{{color-scheme:light;font-family:Segoe UI,Arial,sans-serif;color:#16202a;background:#f4f7fa}}body{{margin:0;background:#f4f7fa}}main{{max-width:1260px;margin:auto;padding:28px}}section{{background:#fff;border:1px solid #d8e1ea;border-radius:10px;padding:20px;margin:16px 0;box-shadow:0 1px 3px #16202a12}}h1{{margin:0 0 6px}}h2{{margin-top:0}}.muted{{color:#526372}}.notice{{border-left:4px solid #2563eb;padding:10px 12px;background:#eff6ff}}table{{width:100%;border-collapse:collapse}}th,td{{padding:10px;border-bottom:1px solid #e5eaf0;text-align:left;vertical-align:top}}th{{background:#f8fafc}}.state,.pill{{display:inline-block;border-radius:999px;padding:3px 8px;font-weight:600;font-size:.86em;background:#e5e7eb}}.review,.altered{{background:#fef3c7;color:#854d0e}}.observed,.ready{{background:#dcfce7;color:#166534}}.technical_issue,.invalid,.repeated{{background:#fee2e2;color:#991b1b}}.new{{background:#dbeafe;color:#1d4ed8}}.removed{{background:#fce7f3;color:#9d174d}}.filters{{display:flex;gap:12px;flex-wrap:wrap;margin:12px 0}}label{{font-weight:600}}select{{margin-left:6px;padding:6px}}.divergence{{border:1px solid #d8e1ea;border-radius:8px;padding:14px;margin:10px 0;background:#fff}}.divergence header{{display:flex;gap:10px;align-items:center;flex-wrap:wrap}}.divergence small{{color:#526372}}dl{{display:grid;grid-template-columns:150px 1fr;gap:8px;margin:12px 0 0}}dt{{font-weight:700}}dd{{margin:0;overflow-wrap:anywhere}}code{{font-family:Consolas,monospace;font-size:.9em}}.hidden{{display:none}}ul{{padding-left:22px;overflow-wrap:anywhere}}@media(max-width:700px){{main{{padding:14px}}table{{font-size:.9em}}dl{{grid-template-columns:1fr}}}}
</style></head><body><main>
<h1>Divergências da execução</h1><p class=\"muted\">Execução <code>{esc(model['execution']['execution_id'])}</code> · resultado técnico <code>{esc(model['source_result']['name'])}</code> preservado sem abertura automática.</p>
<section><h2>Resumo</h2><p class=\"notice\"><b>Modo somente leitura:</b> nenhuma escrita de domínio foi feita. O HTML foi gerado do JSON já salvo, para leitura humana.</p>
<p>Estado: <b>{esc(model.get('state'))}</b> · protocolo: <code>{esc(model['program'].get('launcher_protocol_version'))}</code> · leitor físico: <code>{esc(model['program'].get('physical_reader'))}</code>.</p>
<table><thead><tr><th>Família</th><th>Estado</th><th>Contagens</th><th>Leitura</th></tr></thead><tbody>{family_rows}</tbody></table></section>
<section><h2>Divergências</h2><p class=\"muted\">Mostrando até {sample_limit_text(model)} por verificação e tipo; contagens são {"completas" if model['divergence_summary']['scan_complete'] else "parciais porque a leitura do resultado atingiu o limite seguro"}. Filtros atuam apenas sobre os blocos mostrados.</p>
<div class=\"filters\"><label>Família <select id=\"family-filter\">{family_options}</select></label><label>Tipo <select id=\"type-filter\">{type_options}</select></label></div><p id=\"visible-count\"></p><div id=\"divergence-list\">{''.join(blocks)}</div></section>
<section><h2>Rastreabilidade da execução</h2><p>Contrato: <code>{esc(contract.get('contrato_id'))}</code> · versão do jogo: <code>{esc(contract.get('versao_jogo'))}</code> · fingerprint de contrato: <code>{esc(contract.get('fingerprint_contrato_sha256'))}</code> · fingerprint de fontes: <code>{esc(contract.get('fingerprint_fontes_sha256'))}</code>.</p>
<p>Gate de revisão: <code>{esc(review_gate.get('state'))}</code> · aplicação habilitada: <code>{esc(review_gate.get('application_enabled'))}</code>.</p><h3>Fontes declaradas</h3><ul>{source_rows}</ul><h3>Artefatos desta execução</h3><ul>{artifacts}</ul><p class=\"muted\">Manifesto técnico desta execução: <code>{esc(model['execution']['manifest'])}</code>. Qualquer aprovação/aplicação futura deve referenciar esta execução e o pacote selado correspondente.</p></section>
</main><script>
function filterDivergences(){{const family=document.getElementById('family-filter').value;const type=document.getElementById('type-filter').value;let shown=0;document.querySelectorAll('.divergence').forEach(function(item){{const visible=(family==='all'||item.dataset.family===family)&&(type==='all'||item.dataset.type===type);item.classList.toggle('hidden',!visible);if(visible)shown++;}});document.getElementById('visible-count').textContent=shown+' bloco(s) exibido(s).';const empty=document.getElementById('empty-state');if(empty)empty.classList.toggle('hidden',shown!==0);}}document.getElementById('family-filter').addEventListener('change',filterDivergences);document.getElementById('type-filter').addEventListener('change',filterDivergences);filterDivergences();
</script></body></html>"""


PRESENTATION_PAGE_SIZE = 10


def _grouped_samples(model: dict[str, Any]) -> list[tuple[str, list[tuple[str, str, list[dict[str, Any]]]]]]:
    """Organiza exemplos sem alterar a comparação que os originou."""
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for sample in model.get("divergence_samples", []):
        family = str(sample.get("family") or "Informações técnicas para investigar")
        type_key = str(sample.get("type_key") or "invalid")
        grouped.setdefault(family, {}).setdefault(type_key, []).append(sample)
    family_order = [row["family"] for row in model.get("family_summary", [])]
    family_order.extend(name for name in grouped if name not in family_order)
    output: list[tuple[str, list[tuple[str, str, list[dict[str, Any]]]]]] = []
    for family in family_order:
        types = grouped.get(family)
        if not types:
            continue
        ordered_types = [key for key in DIVERGENCE_KINDS if key in types]
        output.append((family, [(key, TYPE_LABELS[key], types[key]) for key in ordered_types]))
    return output


def _render_divergence_block(sample: dict[str, Any]) -> str:
    esc = lambda value: html.escape(_compact(value), quote=True)
    presentation = sample.get("presentation") if isinstance(sample.get("presentation"), dict) else {}
    title = presentation.get("title") or sample.get("family") or "Informação para investigar"
    guidance = _operator_guidance(str(sample.get("type_key") or "invalid"), sample)
    return (
        "<article class=\"divergence\">"
        "<h5>" + esc(title) + "</h5>"
        "<div class=\"answer-grid\">"
        "<div><b>O que significa</b><p>" + esc(guidance["meaning"]) + "</p></div>"
        "<div><b>Afeta os dados de hoje?</b><p>" + esc(guidance["today"]) + "</p></div>"
        "<div><b>Impede enviar alterações ao banco?</b><p>" + esc(guidance["blocks"]) + "</p></div>"
        "<div><b>O que você deve fazer</b><p>" + esc(guidance["action"]) + "</p></div>"
        "</div>"
        "<details class=\"technical-details\"><summary>Detalhes técnicos</summary>"
        "<dl><dt>Código interno do item</dt><dd><code>" + esc(sample.get("identity")) + "</code></dd>"
        "<dt>Registro completo da comparação</dt><dd><code>" + esc(sample.get("detail")) + "</code></dd>"
        "<dt>Arquivo e posição de origem</dt><dd><code>" + esc(sample.get("provenance")) + "</code></dd>"
        "<dt>Etapa interna que gerou este item</dt><dd><code>" + esc(sample.get("report")) + "</code></dd>"
        "</dl></details></article>"
    )


def _render_grouped_divergences(model: dict[str, Any]) -> str:
    esc = lambda value: html.escape(_compact(value), quote=True)
    summary_by_label = {
        str(row.get("family")): row
        for row in model.get("family_summary", [])
        if isinstance(row, dict)
    }

    def quantity(value: Any) -> str:
        return f"{int(value or 0):,}".replace(",", ".")

    def family_total_text(summary: dict[str, Any]) -> str:
        counts = summary.get("counts") or {}
        historical = int(counts.get("historical_unresolved") or 0)
        known_pending = int(counts.get("known_pending") or 0)
        canonical = sum(
            int(counts.get(key) or 0)
            for key in DIVERGENCE_KINDS
            if key not in ("historical_unresolved", "known_pending")
        )
        if known_pending and not canonical and not historical:
            return f"{_amount(known_pending, 'pendência já conhecida', 'pendências já conhecidas')}; nenhuma mudança de hoje nesta parte."
        if historical and not canonical:
            return f"{_amount(historical, 'registro antigo guardado como referência', 'registros antigos guardados como referência')}; nenhuma mudança de hoje nesta parte."
        entities = int(summary.get("entities_affected") or 0)
        differences = int(summary.get("field_differences") or 0)
        information = int(summary.get("information_count") or 0)
        if summary.get("family_key") == "cartas" and entities and differences and information:
            return f"Total real: {quantity(entities)} cartas afetadas; {quantity(differences)} diferenças em {quantity(information)} informações."
        if entities and differences:
            info_text = f" em {quantity(information)} informações" if information else ""
            return f"Total real: {quantity(entities)} itens afetados; {quantity(differences)} diferenças{info_text}."
        classified = canonical + historical + known_pending
        return _amount(classified, "item para conferir", "itens para conferir") + "."

    groups: list[str] = []
    for family, types in _grouped_samples(model):
        summary = summary_by_label.get(family, {})
        type_html: list[str] = []
        for type_key, type_label, samples in types:
            initial = samples[:PRESENTATION_PAGE_SIZE]
            remaining = samples[PRESENTATION_PAGE_SIZE:]
            visible_blocks = "".join(_render_divergence_block(sample) for sample in initial)
            deferred = "".join(_render_divergence_block(sample) for sample in remaining)
            more = ""
            if remaining:
                more = (
                    "<template class=\"more-items\">" + deferred + "</template>"
                    "<button class=\"show-more\" type=\"button\">Ver mais "
                    + _amount(min(PRESENTATION_PAGE_SIZE, len(remaining)), "exemplo", "exemplos")
                    + " desta página</button>"
                )
            type_total = int((summary.get("counts") or {}).get(type_key, 0))
            type_real = "Total nesta categoria: " + _amount(type_total, "item", "itens") + "."
            if summary.get("family_key") == "cartas" and type_key == "altered":
                type_real = family_total_text(summary)
            type_html.append(
                "<details class=\"type-group\" data-type=\"" + esc(type_key) + "\">"
                "<summary><span class=\"pill " + esc(_tag(type_key)) + "\">" + esc(type_label) + "</span>"
                "<span>" + esc(type_real) + "</span>"
                "<span>Mostrando " + _amount(len(samples), "exemplo", "exemplos") + " nesta página</span></summary>"
                "<div class=\"sample-list\">" + visible_blocks + "</div>" + more + "</details>"
            )
        groups.append(
            "<details class=\"family-group\" data-family=\"" + esc(family) + "\">"
            "<summary><strong>" + esc(family) + "</strong><span>" + esc(family_total_text(summary)) + "</span>"
            "<span>Abra para ver a explicação e os exemplos</span></summary>" + "".join(type_html) + "</details>"
        )
    return "".join(groups) or "<p id=\"empty-state\">Não há mudanças nem avisos para exibir nesta execução.</p>"


def _render_html(model: dict[str, Any]) -> str:
    esc = lambda value: html.escape(_compact(value), quote=True)

    def count_text(counts: dict[str, Any]) -> str:
        labels = {
            "new": "Novos no jogo",
            "removed": "Não apareceram no jogo atual",
            "altered": "Mudaram no jogo",
            "repeated": "Duplicados",
            "invalid": "Não foi possível conferir",
            "known_pending": "Pendências já conhecidas",
            "historical_unresolved": "Registros antigos de referência",
        }
        parts = [f"{labels[key]}: {int(counts.get(key, 0))}" for key in DIVERGENCE_KINDS if int(counts.get(key, 0))]
        return " · ".join(parts) if parts else "Nada diferente"

    family_rows = "\n".join(
        "<tr><td><strong>" + esc(row["family"]) + "</strong></td><td><span class=\"state " + esc(row.get("status_tone")) + "\">"
        + esc(row.get("state_label")) + "</span></td><td><b>" + esc(count_text(row["counts"])) + "</b><br>" + esc(row["detail"])
        + "</td><td>" + esc(row["operator_action"]) + "</td></tr>"
        for row in model["family_summary"]
    )
    family_options = "<option value=\"all\">Todas</option>" + "".join(
        "<option value=\"" + esc(row["family"]) + "\">" + esc(row["family"]) + "</option>"
        for row in model["family_summary"]
    )
    type_options = "<option value=\"all\">Todos</option>" + "".join(
        "<option value=\"" + esc(key) + "\">" + esc(label) + "</option>" for key, label in TYPE_LABELS.items()
    )
    warning_cards = "".join(
        "<article class=\"warning-card " + esc(item["tone"]) + "\">"
        "<header><div><p class=\"eyebrow\">" + esc(item["family"]) + "</p><h3>" + esc(item["title"]) + "</h3></div>"
        "<span class=\"count-badge\">" + esc(_amount(item["count"], "item", "itens")) + "</span></header>"
        "<div class=\"answer-grid\">"
        "<div><b>O que significa</b><p>" + esc(item["meaning"]) + "</p></div>"
        "<div><b>Afeta os dados de hoje?</b><p>" + esc(item["today"]) + "</p></div>"
        "<div><b>Impede enviar alterações ao banco?</b><p>" + esc(item["blocks"]) + "</p></div>"
        "<div><b>O que você deve fazer</b><p>" + esc(item["action"]) + "</p></div>"
        "</div></article>"
        for item in model.get("operator_warnings", [])
    )
    if not warning_cards:
        warning_cards = "<p class=\"all-clear\">Nenhum aviso ficou pendente nesta execução.</p>"
    artifacts = "\n".join(
        "<li><code>" + esc(item["name"]) + "</code> — " + esc(item["bytes"]) + " bytes</li>" for item in model["artifacts"]
    )
    source_rows = "\n".join(
        "<li><code>" + esc(role) + "</code> — " + ("encontrada" if value.get("found") else "ausente")
        + ("; " + esc(value.get("location")) if value.get("location") else "") + "</li>"
        for role, value in sorted(model["sources"].items())
    ) or "<li>Sem fotografia de fontes disponível.</li>"
    contract = model["contract"]
    review_gate = model["review_gate"]
    operator = model["operator_summary"]
    radar = model.get("launch_radar") if isinstance(model.get("launch_radar"), dict) else {}
    motor = model.get("motor_readiness") if isinstance(model.get("motor_readiness"), dict) else {}
    radar_counts = radar.get("counts") if isinstance(radar.get("counts"), dict) else {}
    radar_comparison = radar.get("comparison") if isinstance(radar.get("comparison"), dict) else {}
    radar_integration = radar.get("integration") if isinstance(radar.get("integration"), dict) else {}
    motor_summary = motor.get("summary") if isinstance(motor.get("summary"), dict) else {}
    motor_cards = int(motor_summary.get("cards") or 0)
    motor_ready = int(motor_summary.get("motor_eligible") or 0)
    motor_waiting = int(motor_summary.get("aguardando_insumos") or 0)
    motor_waiting_resolution = int(motor_summary.get("aguardando_decisao_de_vinculo") or 0)
    motor_not_applicable = int(motor_summary.get("nao_aplicavel_aos_motores") or 0)
    motor_known_total = int(motor_summary.get("pendencias_conhecidas_total") or 0)

    if motor.get("available"):
        motor_tone = "warning" if motor_waiting or motor_waiting_resolution or motor.get("state") == "indisponivel_fail_closed" else "success"
        motor_title = (
            "A conferência de uso nos motores não pôde ser concluída"
            if motor.get("state") == "indisponivel_fail_closed"
            else f"{_amount(motor_ready, 'carta está pronta', 'cartas estão prontas')} para os motores"
        )
        motor_today = (
            "Sim. As cartas ainda sem prova completa ficam aguardando; as cartas já comprovadas permanecem separadas."
            if motor_waiting or motor_waiting_resolution
            else "Não há carta aplicável aguardando dados nesta leitura."
        )
        motor_action = (
            "Abra REVISAR USO NOS MOTORES no Extrator. Confira as cartas que aguardam insumos e não rode Otimizador ou Bonificador nelas até a pendência ser resolvida."
            if motor_waiting or motor_waiting_resolution
            else "Nenhuma revisão de completude é necessária nesta rodada."
        )
        motor_known_html = ""
        known_counts = motor_summary.get("pendencias_conhecidas_por_tipo") if isinstance(motor_summary.get("pendencias_conhecidas_por_tipo"), dict) else {}
        known_examples = motor_summary.get("pendencias_conhecidas_exemplos_por_tipo") if isinstance(motor_summary.get("pendencias_conhecidas_exemplos_por_tipo"), dict) else {}
        for pending_type, count in known_counts.items():
            examples = known_examples.get(pending_type) if isinstance(known_examples.get(pending_type), list) else []
            example_text = ", ".join(
                str(item.get("nome") or ("card " + str(item.get("card_id"))))
                for item in examples[:6] if isinstance(item, dict)
            ) or "exemplos disponíveis no arquivo de prontidão"
            if pending_type == "clube_sem_vinculo_atual_por_licenca":
                known_title = "Cards antigos cujo clube não existe mais no catálogo atual"
                known_meaning = "O código original do clube foi lido, mas o clube saiu do jogo atual por licença. O card ficou órfão; não ficou incompleto."
                known_today = "Não. É uma situação histórica conhecida. O código do card foi preservado e não será ligado a outro clube por tentativa."
                known_blocks = "Não bloqueia publicação nem os motores. Um cálculo que dependa de clube atual trata o card como sem vínculo atual."
                known_action = "Nenhuma correção manual é necessária. Continue mantendo o aviso para explicar por que o card não possui clube atual."
            else:
                known_title = "Observação conhecida que não torna o card incompleto"
                known_meaning = "O dado bruto foi conferido; existe apenas uma observação de catálogo ou de apresentação que continua acompanhada."
                known_today = "Não há falta de coleta comprovada por esta observação."
                known_blocks = "Não bloqueia publicação nem os motores."
                known_action = "Não complete o dado por tentativa. O Extrator continuará mostrando a observação até existir nova prova."
            motor_known_html += (
                "<article class=\"warning-card info\"><header><div><p class=\"eyebrow\">Observação conhecida</p><h3>" + esc(known_title) + "</h3></div>"
                "<span class=\"count-badge\">" + esc(_amount(count, "card", "cards")) + "</span></header><p><b>Exemplos:</b> " + esc(example_text) + ".</p>"
                "<div class=\"answer-grid\"><div><b>O que significa</b><p>" + esc(known_meaning) + "</p></div>"
                "<div><b>Afeta os dados de hoje?</b><p>" + esc(known_today) + "</p></div>"
                "<div><b>O que fica bloqueado?</b><p>" + esc(known_blocks) + "</p></div>"
                "<div><b>O que você deve fazer</b><p>" + esc(known_action) + "</p></div></div></article>"
            )
        motor_section = (
            "<section><h2>Quais cartas podem entrar nos motores</h2>"
            "<article class=\"warning-card " + esc(motor_tone) + "\"><header><div><p class=\"eyebrow\">Otimizador e Bonificador</p><h3>" + esc(motor_title) + "</h3></div>"
            "<span class=\"count-badge\">" + esc(_amount(motor_cards, "carta conferida", "cartas conferidas")) + "</span></header>"
            "<div class=\"answer-grid\"><div><b>O que significa</b><p>Cada parte necessária foi classificada como conferida com valor, conferida sem valor, ainda não conferida ou leitura com problema. Sem valor, quando foi realmente conferido, é uma resposta completa.</p></div>"
            "<div><b>Afeta os dados de hoje?</b><p>" + esc(motor_today) + "</p></div>"
            "<div><b>O que fica bloqueado?</b><p>Somente o uso das cartas afetadas no Otimizador e no Bonificador. Enviar a carta ao banco, mostrar no site ou anunciar uma novidade continua sendo uma decisão independente.</p></div>"
            "<div><b>O que você deve fazer</b><p>" + esc(motor_action) + "</p></div></div>"
            "<div class=\"stats compact\"><div class=\"stat\"><strong>" + esc(_number(motor_ready)) + "</strong><span>prontas para os motores</span></div>"
            "<div class=\"stat\"><strong>" + esc(_number(motor_waiting + motor_waiting_resolution)) + "</strong><span>aguardando insumo ou decisão</span></div>"
            "<div class=\"stat\"><strong>" + esc(_number(motor_not_applicable)) + "</strong><span>não se aplicam aos motores</span></div>"
            "<div class=\"stat\"><strong>" + esc(_number(motor_known_total)) + "</strong><span>observações conhecidas não bloqueantes</span></div></div></article>" + motor_known_html +
            "<p class=\"read-only\"><b>Atenção à instalação:</b> esta rodada apenas gerou a prova local. A proteção só passa a valer dentro dos motores depois que a migração do banco e as duas conferências dos consumidores forem instaladas e validadas com leitura de volta.</p></section>"
        )
    else:
        motor_tone = "warning"
        motor_title = "Esta rodada ainda não possui a conferência de uso nos motores"
        motor_section = (
            "<section><h2>Quais cartas podem entrar nos motores</h2><article class=\"warning-card\"><header><div><p class=\"eyebrow\">Otimizador e Bonificador</p><h3>Conferência de completude indisponível nesta rodada</h3></div></header>"
            "<div class=\"answer-grid\"><div><b>O que significa</b><p>O relatório não possui a prova necessária para separar cartas completas de cartas ainda não conferidas. Um espaço realmente conferido e vazio significa que o card não possui aquele item; não significa falta.</p></div>"
            "<div><b>Afeta os dados de hoje?</b><p>Não muda nem esconde cartas, mas impede afirmar que elas podem alimentar os motores com segurança.</p></div>"
            "<div><b>O que fica bloqueado?</b><p>O uso desta rodada no Otimizador e no Bonificador. A publicação no site continua independente.</p></div>"
            "<div><b>O que você deve fazer</b><p>Faça uma nova varredura com a versão atual do Extrator antes de usar cartas novas nos motores.</p></div></div></article></section>"
        )

    radar_box_html = ""
    for box in radar.get("interesting_boxes") or []:
        cards = box.get("cartas") if isinstance(box.get("cartas"), list) else []
        examples = ", ".join(
            str(card.get("nome_card") or ("card " + str(card.get("card_id"))))
            for card in cards[:5] if isinstance(card, dict)
        ) or "nomes dos cards disponíveis nos detalhes técnicos"
        state = str(box.get("estado") or "sem_historico")
        if state == "nova":
            state_label = "Nova em relação à última varredura"
            today = "Sim. O nome desta box não existia na rodada anterior comparável. Isso pode ser uma pré-carga e ainda não prova que já apareceu na tela do jogo."
        else:
            state_label = "Referência local desta rodada"
            today = "Ainda não é possível chamá-la de nova, porque não havia uma rodada anterior comparável. Esta leitura passa a ser a referência para a próxima varredura."
        radar_box_html += (
            "<article class=\"box-card\"><header><div><p class=\"eyebrow\">" + esc(state_label) + "</p><h3>" + esc(box.get("nome_box")) + "</h3></div>"
            "<span class=\"count-badge\">" + esc(_amount(box.get("quantidade_cartas"), "card", "cards")) + "</span></header>"
            "<p><b>Exemplos:</b> " + esc(examples) + ".</p><div class=\"answer-grid\"><div><b>O que significa</b><p>O arquivo físico do jogo liga estes cards a este nome de box.</p></div>"
            "<div><b>Afeta os dados de hoje?</b><p>" + esc(today) + "</p></div>"
            "<div><b>O que fica bloqueado?</b><p>Nada é bloqueado para publicação. O radar também não envia a box ao banco sozinho e não libera card para os motores.</p></div>"
            "<div><b>O que você deve fazer</b><p>Use como sinal de lançamento, confira a completude dos cards e decida separadamente o que deseja publicar ou enviar.</p></div></div></article>"
        )
    radar_ignored_html = ""
    ignored_total = int(radar_counts.get("records_ignored") or 0)
    ignored_by_classification = radar_counts.get("ignored_by_classification") if isinstance(radar_counts.get("ignored_by_classification"), dict) else {}
    cards_without_box = int(ignored_by_classification.get("card_without_box_name") or 0)
    if cards_without_box:
        ignored_examples = []
        for record in radar.get("ignored_records") or []:
            if not isinstance(record, dict) or record.get("classification") != "card_without_box_name":
                continue
            ignored_examples.append(
                "registro " + str(record.get("record_index"))
                + " — card " + str(record.get("card_id"))
                + " — prova " + str(record.get("record_sha256") or "")[:12] + "…"
            )
            if len(ignored_examples) >= 8:
                break
        technical_examples = "".join("<li>" + esc(example) + "</li>" for example in ignored_examples)
        radar_ignored_html = (
            "<article class=\"warning-card\"><header><div><p class=\"eyebrow\">Aviso acompanhado, não é falha da varredura</p>"
            "<h3>" + esc(_amount(cards_without_box, "registro físico possui card, mas ainda não possui nome de box", "registros físicos possuem card, mas ainda não possuem nome de box")) + "</h3></div>"
            "<span class=\"count-badge\">" + esc(_amount(cards_without_box, "card isolado", "cards isolados")) + "</span></header>"
            "<div class=\"answer-grid\"><div><b>O que significa</b><p>O arquivo do jogo trouxe o identificador do card, mas deixou completamente vazio o espaço do nome da box. O Extrator não inventou um nome e não tratou isso como lançamento.</p></div>"
            "<div><b>Afeta os dados de hoje?</b><p>Afeta somente a conclusão de box destes cards. As relações completas entre card e box continuam válidas e foram conferidas normalmente.</p></div>"
            "<div><b>O que fica bloqueado?</b><p>Somente usar estes registros como anúncio de box ou enviá-los em um pacote. Eles não bloqueiam o envio de outras mudanças comprovadas e não entram no banco.</p></div>"
            "<div><b>O que você deve fazer</b><p>Nada manualmente. Continue observando o aviso; em uma futura varredura, se a Konami preencher o nome, o card entrará normalmente no Radar.</p></div></div>"
            + ("<details><summary>Detalhes técnicos</summary><p>Índice, card e início do hash físico dos primeiros casos:</p><ul>" + technical_examples + "</ul></details>" if technical_examples else "")
            + "</article>"
        )
    historical_relations = int(ignored_by_classification.get("box_relation_card_absent_from_current_player") or 0)
    if historical_relations:
        historical_examples = []
        for record in radar.get("ignored_records") or []:
            if not isinstance(record, dict) or record.get("classification") != "box_relation_card_absent_from_current_player":
                continue
            historical_examples.append(
                str(record.get("nome_box_fisico") or "box sem nome")
                + " — card " + str(record.get("card_id"))
                + " — registro " + str(record.get("record_index"))
            )
            if len(historical_examples) >= 8:
                break
        historical_details = "".join("<li>" + esc(example) + "</li>" for example in historical_examples)
        radar_ignored_html += (
            "<article class=\"warning-card info\"><header><div><p class=\"eyebrow\">Referência física antiga, fora dos lançamentos atuais</p>"
            "<h3>" + esc(_amount(historical_relations, "ligação de box aponta para um card que não existe no jogo atual", "ligações de box apontam para cards que não existem no jogo atual")) + "</h3></div>"
            "<span class=\"count-badge\">" + esc(_amount(historical_relations, "relação isolada", "relações isoladas")) + "</span></header>"
            "<div class=\"answer-grid\"><div><b>O que significa</b><p>O arquivo de boxes ainda guarda a ligação completa, mas o mesmo identificador não aparece no Player.bin atual. Por isso ela é mantida apenas como referência física antiga.</p></div>"
            "<div><b>Afeta os dados de hoje?</b><p>Não. Estes cards não fazem parte da lista física atual e não são tratados como lançamento.</p></div>"
            "<div><b>O que fica bloqueado?</b><p>Somente esta ligação antiga fica fora do Radar atual, da publicação e do pacote. As boxes e os cards atuais continuam normalmente.</p></div>"
            "<div><b>O que você deve fazer</b><p>Nenhuma correção manual. Não recrie o card nem troque o identificador; o Extrator continuará conferindo a relação em futuras varreduras.</p></div></div>"
            + ("<details><summary>Detalhes técnicos</summary><ul>" + historical_details + "</ul></details>" if historical_details else "")
            + "</article>"
        )
    if radar.get("available"):
        comparison_status = radar_comparison.get("status")
        new_boxes = int((radar_counts.get("by_state") or {}).get("nova") or 0) if isinstance(radar_counts.get("by_state"), dict) else 0
        radar_intro = (
            f"Foram encontradas {_amount(radar_counts.get('boxes'), 'box física', 'boxes físicas')} ligadas a {_amount(radar_counts.get('cards_mapped'), 'card', 'cards')}. "
            + (f"{_amount(new_boxes, 'box não existia', 'boxes não existiam')} na rodada anterior comparável." if comparison_status == "comparado" else "Como ainda não havia uma rodada comparável, esta leitura é a primeira referência local e não chama todas as boxes de novas.")
            + (f" Além disso, {_amount(ignored_total, 'registro sem relação card/box comprovada foi isolado e não entrou nas boxes', 'registros sem relação card/box comprovada foram isolados e não entraram nas boxes')}." if ignored_total else "")
        )
        integration_warning = ""
        if radar_integration.get("status") == "prepared_not_enabled":
            integration_warning = (
                "<article class=\"warning-card\"><header><div><p class=\"eyebrow\">Integração com o banco</p><h3>As ligações entre box e card ainda não são gravadas no banco</h3></div></header>"
                "<div class=\"answer-grid\"><div><b>O que significa</b><p>O Extrator já possui identidade, conteúdo e origem para preparar essa integração, mas a tabela e o contrato de escrita ainda não foram instalados.</p></div>"
                "<div><b>Afeta os dados de hoje?</b><p>Sim, apenas para guardar a box como informação durável. Os demais dados das cartas continuam sendo tratados normalmente.</p></div>"
                "<div><b>O que fica bloqueado?</b><p>Somente o envio automático da ligação box/card ao banco. Publicar ou anunciar a carta não é bloqueado.</p></div>"
                "<div><b>O que você deve fazer</b><p>Não tente cadastrar a ligação por fora. Instale e valide a migração própria antes de habilitar este campo no pacote do Extrator.</p></div></div></article>"
            )
        radar_section = "<section><h2>Radar de boxes e possíveis lançamentos</h2><p>" + esc(radar_intro) + "</p>" + radar_ignored_html + (radar_box_html or "<p class=\"all-clear\">Nenhuma box nova nem alteração de conteúdo apareceu em relação à rodada anterior.</p>") + integration_warning + "</section>"
        radar_overview = f"{_amount(new_boxes, 'box nova', 'boxes novas')}" if comparison_status == "comparado" else "primeira referência de boxes"
    else:
        radar_overview = "radar não disponível nesta rodada"
        radar_section = (
            "<section><h2>Radar de boxes e possíveis lançamentos</h2><article class=\"warning-card\"><header><div><p class=\"eyebrow\">Boxes físicas</p><h3>Esta rodada não possui o radar de boxes</h3></div></header>"
            "<div class=\"answer-grid\"><div><b>O que significa</b><p>Este resultado foi criado antes de o radar entrar no Extrator ou a leitura desse arquivo não terminou.</p></div>"
            "<div><b>Afeta os dados de hoje?</b><p>Pode impedir perceber uma nova box nesta rodada, mas não altera os dados já conferidos das cartas.</p></div>"
            "<div><b>O que fica bloqueado?</b><p>Apenas a conclusão sobre boxes novas. Publicação e envio de outras mudanças continuam separados.</p></div>"
            "<div><b>O que você deve fazer</b><p>Na próxima atualização, execute uma nova varredura com a versão atual do Extrator.</p></div></div></article></section>"
        )

    system_overview = (
        "<div class=\"system-grid\"><div class=\"system-card\"><b>Boxes e lançamentos</b><strong>" + esc(radar_overview) + "</strong><span>não decide publicação sozinho</span></div>"
        "<div class=\"system-card " + esc(motor_tone) + "\"><b>Uso nos motores</b><strong>" + esc(motor_title) + "</strong><span>publicação continua independente</span></div></div>"
    )
    application_status = model.get("application_status") if isinstance(model.get("application_status"), dict) else {}
    gate_state = str(application_status.get("state") or "")
    selection_available = bool(
        application_status.get("selection_available") is True
        or application_status.get("enabled") is True
        or application_status.get("application_enabled") is True
    )
    application_blockers = application_status.get("blockers") if isinstance(application_status.get("blockers"), list) else []
    gate_label = {
        "selection_available": "Há itens válidos disponíveis para seleção no Extrator",
        "ready_to_select": "Há itens válidos disponíveis para seleção no Extrator",
        "ready_to_apply": "Pacote disponível somente após aprovação no Extrator",
        "approval_required": "Pacote aguardando aprovação explícita no Extrator",
        "approved": "Pacote aprovado e aguardando aplicação explícita",
        "applied": "Pacote aplicado e conferido por leitura de volta",
        "no_changes": "Nenhum dado novo ou alterado para enviar",
        "blocked": "Envio indisponível por uma trava desta execução",
        "incomplete": "Envio ao banco indisponível porque a conferência não terminou",
    }.get(
        gate_state,
        "Há itens válidos disponíveis para seleção no Extrator"
        if selection_available and not application_blockers
        else "Envio ao banco indisponível nesta execução",
    )
    return f"""<!doctype html>
<html lang=\"pt-BR\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Relatório da varredura</title>
<style>
:root{{color-scheme:light;font-family:Segoe UI,Arial,sans-serif;color:#18212a;background:#f3f6f8}}*{{box-sizing:border-box}}body{{margin:0;background:#f3f6f8}}main{{max-width:1180px;margin:auto;padding:28px}}h1{{font-size:2rem;margin:4px 0 10px;line-height:1.15}}h2{{margin:0 0 10px;font-size:1.35rem}}h3{{margin:3px 0 0;font-size:1.1rem}}p{{line-height:1.5}}section{{background:#fff;border:1px solid #d7e0e7;border-radius:14px;padding:22px;margin:18px 0;box-shadow:0 2px 8px #16202a0d}}.hero{{border-top:7px solid #d89b13;padding:26px}}.hero.success{{border-color:#23804b}}.hero.error{{border-color:#c93a3a}}.eyebrow{{margin:0;color:#526372;text-transform:uppercase;letter-spacing:.06em;font-size:.78rem;font-weight:700}}.hero-text{{font-size:1.08rem;max-width:850px;margin:0 0 18px}}.next-action{{background:#fff7da;border:1px solid #efd37b;border-radius:10px;padding:16px 18px;margin:14px 0}}.hero.error .next-action{{background:#fff0f0;border-color:#efb5b5}}.hero.success .next-action{{background:#edfaF2;border-color:#a9dfbd}}.next-action h2{{font-size:1.05rem;margin:0 0 5px}}.read-only{{background:#edf6ff;border-left:5px solid #2774b8;padding:12px 14px;border-radius:6px;margin-top:14px}}.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:16px}}.stats.compact{{grid-template-columns:repeat(4,1fr)}}.stat{{background:#f7f9fb;border:1px solid #dce4ea;border-radius:10px;padding:12px}}.stat strong{{display:block;font-size:1.35rem}}.stat span{{color:#526372;font-size:.9rem}}.system-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px}}.system-card{{display:flex;flex-direction:column;gap:4px;background:#f2f8fd;border:1px solid #9bc5e8;border-radius:10px;padding:14px}}.system-card.warning{{background:#fffaf0;border-color:#e2c76f}}.system-card.success{{background:#edfaf2;border-color:#a9dfbd}}.system-card strong{{font-size:1.05rem}}.system-card span{{color:#526372}}.warning-card,.box-card{{border:1px solid #e2c76f;border-left:7px solid #d89b13;border-radius:12px;padding:18px;margin:14px 0;background:#fffaf0}}.box-card{{border-color:#9bc5e8;border-left-color:#2e79b7;background:#f2f8fd}}.warning-card.success{{border-color:#a9dfbd;border-left-color:#23804b;background:#edfaf2}}.warning-card.info{{border-color:#9bc5e8;border-left-color:#2e79b7;background:#f2f8fd}}.warning-card.error{{border-color:#efaaaa;border-left-color:#c93a3a;background:#fff3f3}}.warning-card header,.box-card header{{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}}.count-badge,.state,.pill{{display:inline-block;border-radius:999px;padding:5px 10px;font-weight:700;font-size:.82rem;background:#e9eef2;white-space:nowrap}}.answer-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px}}.answer-grid>div{{background:#fff;border:1px solid #e0e6eb;border-radius:9px;padding:12px}}.answer-grid p{{margin:5px 0 0}}.state.success{{background:#dcfce7;color:#166534}}.state.warning,.pill.known_pending,.pill.altered{{background:#fef3c7;color:#854d0e}}.state.info,.pill.historical_unresolved,.pill.new{{background:#e0f2fe;color:#075985}}.state.error,.pill.invalid,.pill.repeated{{background:#fee2e2;color:#991b1b}}.pill.removed{{background:#fce7f3;color:#9d174d}}table{{width:100%;border-collapse:collapse;margin-top:12px}}th,td{{padding:12px;border-bottom:1px solid #e4e9ed;text-align:left;vertical-align:top}}th{{background:#f7f9fb;color:#41515f;font-size:.88rem}}.table-wrap{{overflow-x:auto}}.muted{{color:#526372}}.filters{{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0}}label{{font-weight:700}}select{{margin-left:6px;padding:7px;border:1px solid #aebbc5;border-radius:6px;background:#fff}}.family-group,.type-group,.technical-details{{border:1px solid #d8e1e8;border-radius:10px;background:#fff;margin:10px 0}}.family-group>summary,.type-group>summary{{cursor:pointer;padding:14px;display:flex;justify-content:space-between;gap:12px;align-items:center}}.family-group>summary{{background:#f7f9fb;font-size:1.02em}}.type-group{{margin:10px 12px}}.type-group>summary{{background:#fcfdff}}.sample-list{{padding:0 12px}}.divergence{{border-left:5px solid #d89b13;padding:14px;margin:12px 0;background:#fffaf3;border-radius:8px}}.divergence h5{{margin:0;font-size:1.02em}}.technical-details{{margin:12px 0 0;background:#f7f9fb}}.technical-details summary{{cursor:pointer;padding:10px 12px;font-weight:700}}.technical-details dl{{padding:0 12px 12px}}dl{{display:grid;grid-template-columns:220px 1fr;gap:8px;margin:0}}dt{{font-weight:700}}dd{{margin:0;overflow-wrap:anywhere}}code{{font-family:Consolas,monospace;font-size:.88em}}.show-more{{margin:0 12px 14px;padding:9px 12px;border:1px solid #2774b8;border-radius:7px;background:#fff;color:#1d5e92;font-weight:700;cursor:pointer}}.hidden{{display:none!important}}ul{{padding-left:22px;overflow-wrap:anywhere}}.all-clear{{background:#edfaf2;border:1px solid #a9dfbd;padding:12px;border-radius:8px}}@media(max-width:760px){{main{{padding:12px}}h1{{font-size:1.6rem}}section,.hero{{padding:16px}}.stats,.stats.compact,.system-grid{{grid-template-columns:1fr 1fr}}.answer-grid{{grid-template-columns:1fr}}table{{font-size:.9em;min-width:760px}}dl{{grid-template-columns:1fr}}.family-group>summary,.type-group>summary,.warning-card header,.box-card header{{align-items:flex-start;flex-direction:column}}}}
</style></head><body><main>
<section class=\"hero {esc(operator['tone'])}\"><p class=\"eyebrow\">Resultado geral da varredura</p><h1>{esc(operator['verdict'])}</h1><p class=\"hero-text\">{esc(operator['explanation'])}</p>
<div class=\"next-action\"><h2>O que você deve fazer agora</h2><p>{esc(operator['action'])}</p></div>
<div class=\"read-only\"><b>Esta varredura foi somente leitura.</b> Ela não alterou o banco de dados, as cartas nem os arquivos do jogo.</div>{system_overview}
<div class=\"stats\"><div class=\"stat\"><strong>{len(model['family_summary'])}</strong><span>partes do jogo conferidas</span></div><div class=\"stat\"><strong>{esc(operator['changes'])}</strong><span>mudanças atuais</span></div><div class=\"stat\"><strong>{esc(operator['pending'])}</strong><span>pendências já conhecidas</span></div><div class=\"stat\"><strong>{esc(operator['historical'])}</strong><span>registros antigos de referência</span></div></div></section>
{radar_section}
{motor_section}
<section><h2>Avisos que continuam importantes</h2><p class=\"muted\">Cada aviso abaixo explica o que significa, se afeta os dados de hoje, se impede o envio ao banco e o que você deve fazer.</p>{warning_cards}</section>
<section><h2>O que foi conferido</h2><p class=\"muted\">Esta tabela resume cada parte do jogo sem misturar pendências antigas com mudanças encontradas hoje.</p><div class=\"table-wrap\"><table><thead><tr><th>Parte do jogo</th><th>Resultado de hoje</th><th>O que apareceu</th><th>O que você deve fazer</th></tr></thead><tbody>{family_rows}</tbody></table></div></section>
<section><h2>Mudanças, avisos e exemplos</h2><p class=\"muted\">Abra os grupos para ver exemplos. Códigos, nomes de arquivos, posições internas e assinaturas digitais ficam recolhidos em <b>Detalhes técnicos</b>.</p>
<div class=\"filters\"><label>Parte do jogo <select id=\"family-filter\">{family_options}</select></label><label>O que aconteceu <select id=\"type-filter\">{type_options}</select></label></div><p id=\"visible-count\"></p><div id=\"divergence-list\">{_render_grouped_divergences(model)}</div></section>
<section><details><summary><b>Informações para suporte e auditoria (opcional)</b></summary><p>Identificação da execução: <code>{esc(model['execution']['execution_id'])}</code> · arquivo de resultado: <code>{esc(model['source_result']['name'])}</code>.</p><p>Contrato de leitura: <code>{esc(contract.get('contrato_id'))}</code> · versão dos arquivos do jogo: <code>{esc(contract.get('versao_jogo'))}</code>.</p><p>Assinatura digital do contrato: <code>{esc(contract.get('fingerprint_contrato_sha256'))}</code> · assinatura digital das fontes: <code>{esc(contract.get('fingerprint_fontes_sha256'))}</code>.</p><p>Situação interna: <b>{esc(gate_label)}</b> · há itens disponíveis para selecionar nesta execução: <b>{'sim' if selection_available and not application_blockers else 'não'}</b>.</p><h3>Arquivos do jogo usados na leitura</h3><ul>{source_rows}</ul><h3>Arquivos gerados nesta execução</h3><ul>{artifacts}</ul><p class=\"muted\">Arquivo de conferência técnica: <code>{esc(model['execution']['manifest'])}</code>.</p></details></section>
</main><script>
const PAGE_SIZE={PRESENTATION_PAGE_SIZE};
function filterDivergences(){{const family=document.getElementById('family-filter').value;const type=document.getElementById('type-filter').value;let groups=0;document.querySelectorAll('.family-group').forEach(function(group){{const familyMatch=family==='all'||group.dataset.family===family;let typeMatch=false;group.querySelectorAll('.type-group').forEach(function(typeGroup){{const visible=type==='all'||typeGroup.dataset.type===type;typeGroup.classList.toggle('hidden',!visible);if(visible)typeMatch=true;}});const visible=familyMatch&&typeMatch;group.classList.toggle('hidden',!visible);if(visible)groups++;}});document.getElementById('visible-count').textContent=groups+(groups===1?' grupo exibido.':' grupos exibidos.');}}
function revealMore(button){{const group=button.closest('.type-group');const template=group.querySelector('template.more-items');const list=group.querySelector('.sample-list');const items=Array.from(template.content.querySelectorAll('.divergence')).slice(0,PAGE_SIZE);items.forEach(function(item){{list.appendChild(item);}});const left=template.content.querySelectorAll('.divergence').length;if(!left){{button.remove();}}else{{const amount=Math.min(PAGE_SIZE,left);button.textContent='Ver mais '+amount+(amount===1?' exemplo':' exemplos');}}}}
document.addEventListener('click',function(event){{if(event.target.matches('.show-more'))revealMore(event.target);}});document.getElementById('family-filter').addEventListener('change',filterDivergences);document.getElementById('type-filter').addEventListener('change',filterDivergences);filterDivergences();
</script></body></html>"""


def sample_limit_text(model: dict[str, Any]) -> str:
    return str(model["divergence_summary"]["sample_limit_per_check_and_type"])


def render_saved_result(result_path: Path, *, sample_limit: int = SAMPLE_LIMIT_PER_CHECK_AND_TYPE, timeout_seconds: float = DEFAULT_SCAN_TIMEOUT_SECONDS) -> dict[str, Any]:
    """Produz os artefatos de leitura humana sem modificar ``resultado.json``."""
    result_path = result_path.resolve()
    if not result_path.is_file():
        raise FileNotFoundError(f"resultado inexistente: {result_path}")
    model = _build_model(result_path, sample_limit, timeout_seconds)
    run_dir = result_path.parent
    html_path = run_dir / "resultado.html"
    manifest_path = run_dir / "manifesto-execucao.json"
    # Os dois artefatos gerados não participam da primeira renderização. Isso
    # evita a circularidade de um HTML tentar listar o próprio tamanho e, mais
    # importante, impede que o manifesto registre um HTML que será regravado.
    generated_names = {html_path.name, manifest_path.name}
    model["artifacts"] = [
        item for item in _artifact_references(run_dir)
        if item["name"] not in generated_names
    ]
    html_path.write_text(_render_html(model), encoding="utf-8")
    # O manifesto lista o HTML final e todos os demais artefatos, mas não lista
    # a si próprio; assim suas medições permanecem estáveis e verificáveis.
    model["artifacts"] = [
        item for item in _artifact_references(run_dir)
        if item["name"] != manifest_path.name
    ]
    model["manifest"]["artifacts"] = model["artifacts"]
    manifest_path.write_text(json.dumps(model["manifest"], ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "review_html_path": str(html_path),
        "manifest_path": str(manifest_path),
        "sample_count": len(model["divergence_samples"]),
        "classified_total": model["divergence_summary"]["total_classified"],
        "scan_complete": model["divergence_summary"]["scan_complete"],
        "database_write": False,
    }
