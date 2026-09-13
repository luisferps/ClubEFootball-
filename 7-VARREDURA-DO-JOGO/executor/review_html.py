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
SAMPLE_LIMIT_PER_CHECK_AND_TYPE = 10
FIELD_EXAMPLE_LIMIT = 3
FIELD_ROW_LIMIT = 60
DEFAULT_SCAN_TIMEOUT_SECONDS = 900.0
DIVERGENCE_KINDS = (
    "new",
    "removed",
    "altered",
    "repeated",
    "invalid",
    "known_pending",
    "historical_unresolved",
    "deferred",
)
TYPE_LABELS = {
    "new": "Novo no jogo",
    "removed": "Não apareceu no jogo atual",
    "altered": "Mudou no jogo",
    "repeated": "Registro duplicado",
    "invalid": "Não foi possível conferir",
    "known_pending": "Pendência já conhecida",
    "historical_unresolved": "Registro antigo guardado como referência",
    "deferred": "Adiado para a próxima varredura",
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
    "proficiencia": "proficiência no estilo",
    "clube_id": "clube",
    "nacionalidade_codigo": "nacionalidade",
    "codigo_nacionalidade": "nacionalidade",
    "posicao_id": "posição",
    "nome_pt": "nome em português",
    "nome_en": "nome em inglês",
    "efeito_maximo": "efeito máximo",
    "delta": "variação do atributo",
    "codigo_atributo": "atributo",
    "codigo_estilo": "estilo tático",
    "codigo_impeto": "ímpeto",
    "valor": "valor do atributo",
    "skill_id": "habilidade",
    "bit_estilo_ia": "estilo de IA",
    "nivel_aptidao": "nível de aptidão na posição",
    "registro_vinculos_jogo": "endereço da carta dentro do arquivo do jogo",
    "indice_registro": "endereço do registro dentro do arquivo do jogo",
    "ordem_fisica": "ordem em que aparece no arquivo do jogo",
    "codigo_clube": "clube",
    "codigo_liga": "liga",
    "jogador_indisponivel": "jogador indisponível",
    "impeto_s1": "ímpeto do slot 1",
    "impeto_s2": "ímpeto do slot 2",
    "impeto_s2_cond": "ímpeto do slot 2 (condicional)",
    "vaga_s1": "vaga do slot 1",
    "vaga_s2": "vaga do slot 2",
    "tipo_carta_id": "tipo da carta",
    "chave_tipo_carta": "tipo da carta",
    "condicional": "é ímpeto condicional",
    "condicao_estado": "condição para o ímpeto valer",
    "tipo_condicao_raw": "código da condição do ímpeto",
    "id_jogo": "código do estilo de jogo",
    "nome_jp": "nome em japonês",
    "nome_tela": "nome que aparece na tela",
    "overall": "nota geral",
    "pe_bom": "pé dominante",
}
TABELA_NA_TELA = {
    "carta_jogo": "ficha da carta",
    "carta_atributo_jogo": "atributos da carta",
    "carta_habilidade_jogo": "habilidades da carta",
    "carta_posicao_jogo": "posições da carta",
    "carta_estilo_ia_jogo": "estilos de IA da carta",
    "carta_playstyle_jogo": "estilo de jogo da carta",
    "carta_corpo_jogo": "medidas do corpo da carta",
    "carta_impeto_jogo": "ímpetos da carta",
    "clube_jogo": "clubes",
    "liga_jogo": "ligas",
    "nacionalidade_jogo": "nacionalidades",
    "tecnico_jogo": "ficha do técnico",
    "tecnico_estilo_jogo": "estilos do técnico",
    "tecnico_atributo_jogo": "atributos do técnico",
    "afinidade_tecnico_jogo": "afinidade do técnico",
    "impeto_jogo": "catálogo de ímpetos",
    "impeto_atributo_jogo": "efeitos do ímpeto",
    "habilidade_jogo": "catálogo de habilidades",
    "playstyle": "catálogo de estilos de jogo",
    "estilo_ia": "catálogo de estilos de IA",
    "posicao_jogo": "catálogo de posições",
    "atributo_jogo": "catálogo de atributos",
}
_REPORT_LINE = re.compile(r'^\s{4}"([^"]+)": \{\s*$')
_ROOT_CLASSIFICATION_LINE = re.compile(r'^\s{6}"classification": \{\s*$')
_BUCKET_LINE = re.compile(
    r'^\s{8}"(new|removed|altered|repeated|invalid|known_pending|historical_unresolved|deferred)": \[\s*$'
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
        "engine_inputs",
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


def _tabela_do_registro(entry: dict[str, Any]) -> str:
    """Nome curto da tabela de destino do registro comparado."""
    destino = entry.get("destino_tabela")
    if isinstance(destino, str) and destino:
        return destino.rsplit(".", 1)[-1]
    escopo = entry.get("escopo")
    return str(escopo or "")


def _campos_que_mudaram(entry: dict[str, Any]) -> list[dict[str, Any]]:
    """Lista o que mudou num registro, seja qual for o formato do comparador.

    Cada comparador do sistema grava a diferenca de um jeito. Antes so um
    formato era lido e as familias inteiras sumiam do relatorio. Aqui os cinco
    formatos viram a mesma lista: campo, o que o banco tem, o que o jogo traz.
    """
    tabela = _tabela_do_registro(entry)
    prefixo = (tabela + ".") if tabela else ""
    saida: list[dict[str, Any]] = []
    mudou = entry.get("campos_alterados")
    if isinstance(mudou, list) and mudou:
        for item in mudou:
            if not isinstance(item, dict):
                continue
            nome = item.get("destino") or item.get("chave_campo")
            if not nome:
                continue
            saida.append({
                "campo": str(nome),
                "banco": item.get("banco", item.get("valor_banco")),
                "jogo": item.get("fisico", item.get("valor_fisico")),
            })
        return saida
    if isinstance(mudou, dict) and mudou:
        for nome, valores in mudou.items():
            if isinstance(valores, dict):
                saida.append({
                    "campo": prefixo + str(nome),
                    "banco": valores.get("database", valores.get("banco")),
                    "jogo": valores.get("source", valores.get("fisico")),
                })
        return saida
    campo_unico = entry.get("campo")
    if isinstance(campo_unico, str) and campo_unico:
        return [{
            "campo": prefixo + campo_unico,
            "banco": entry.get("valor_banco"),
            "jogo": entry.get("valor_fisico"),
        }]
    colunas = entry.get("colunas_fisicas")
    fisico = entry.get("valor_fisico")
    banco = entry.get("valor_banco")
    if isinstance(colunas, list) and isinstance(fisico, list) and isinstance(banco, list):
        apresentacao = set(entry.get("colunas_apresentacao") or [])
        limite = min(len(colunas), len(fisico), len(banco))
        for indice in range(limite):
            nome = colunas[indice]
            if nome in apresentacao:
                continue
            if fisico[indice] != banco[indice]:
                saida.append({"campo": prefixo + str(nome), "banco": banco[indice], "jogo": fisico[indice]})
        return saida
    if isinstance(fisico, dict) and isinstance(banco, dict):
        for nome in sorted(set(fisico) | set(banco)):
            if fisico.get(nome) != banco.get(nome):
                saida.append({"campo": prefixo + str(nome), "banco": banco.get(nome), "jogo": fisico.get(nome)})
        return saida
    return saida


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
    for key in ("nome_tela", "nome_pt", "nome_pt_br", "nome_en", "texto", "nome", "nome_antigo"):
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


_IDENTITY_LOOKUPS = (
    ("card_id", "cards", "Carta"),
    ("tecnico_id", "tecnico_jogo", "T\u00e9cnico"),
    ("skill_id", "habilidade_jogo", "Habilidade"),
    ("codigo_impeto", "impeto_jogo", "\u00cdmpeto"),
    ("codigo_atributo", "atributo_jogo", "Atributo"),
    ("codigo_estilo", "estilo_jogo_tecnico", "Estilo t\u00e1tico"),
    ("clube_id", "clube_jogo", "Clube"),
    ("codigo_jogo", "impeto_jogo", "\u00cdmpeto"),
    ("id_jogo", "playstyle", "Playstyle"),
    ("posicao_id", "posicao_jogo", "Posi\u00e7\u00e3o"),
)


_VALUE_CATALOGS = {
    "clube": "clube_jogo",
    "clube_id": "clube_jogo",
    "nacionalidade": "nacionalidade_jogo",
    "nacionalidade_codigo": "nacionalidade_jogo",
    "codigo_nacionalidade": "nacionalidade_jogo",
    "posicao": "posicao_jogo",
    "posicao_id": "posicao_jogo",
    "codigo_impeto": "impeto_jogo",
    "skill_id": "habilidade_jogo",
    "codigo_atributo": "atributo_jogo",
    "codigo_estilo": "estilo_jogo_tecnico",
    "tecnico_id": "tecnico_jogo",
}


def _value_label(campo: str, valor: Any, context: dict[str, Any]) -> str:
    """Valor cru mais o nome que aparece na tela, quando o campo aponta catalogo."""
    if valor is None or isinstance(valor, (list, dict)):
        return _compact(valor, 200)
    tabela = _VALUE_CATALOGS.get(campo.rsplit(".", 1)[-1])
    if tabela is None:
        return _compact(valor, 200)
    nome = _first_human_label(_presentation_row(context, tabela, valor))
    return f"{valor} ({nome})" if nome else _compact(valor, 200)


def _identity_label(identity: Any, context: dict[str, Any]) -> str:
    """Traduz a chave tecnica para o que aparece na tela do jogo, com o id junto.

    Ordem do Luis (04/09/2026): o relatorio pode mostrar o id, mas nunca so o
    id. Quem le a tela conhece o nome, nao o codigo.
    """
    if not isinstance(identity, dict) or not identity:
        return _compact(identity, 120)
    partes: list[str] = []
    for chave, fonte, rotulo in _IDENTITY_LOOKUPS:
        valor = identity.get(chave)
        if valor is None:
            continue
        nome = None
        if fonte == "cards":
            nome = _card_presentation(context.get("cards", {}).get(_stable_key(valor) or ""))
        elif fonte == "impeto_jogo":
            try:
                nome = resolve_impetus_presentation_label(context.get("reading_contract", {}), int(valor))["rotulo"]
            except (TypeError, ValueError):
                nome = None
            if not nome:
                nome = _first_human_label(_presentation_row(context, "impeto_jogo", valor))
        elif fonte:
            nome = _first_human_label(_presentation_row(context, fonte, valor))
        if nome:
            partes.append(f"{rotulo} {nome} ({valor})")
        else:
            partes.append(f"{rotulo} {valor}")
    if not partes:
        return _compact(identity, 120)
    return " \u00b7 ".join(partes)


def _estado_no_motor(run_dir: Path) -> dict[str, Any]:
    """O que o Extrator ja levantou sobre onde cada carta esta no motor."""
    caminho = run_dir / "insumos-motores.json"
    if not caminho.is_file():
        return {}
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    estado = dados.get("estado_das_cartas_no_motor")
    return estado if isinstance(estado, dict) else {}


def _cartas_para_rerodar(run_dir: Path, cartas_com_mudanca_de_nota: dict[str, list[str]]) -> dict[str, Any]:
    """Das cartas cujo dado de nota mudou, quais o motor realmente roda.

    Carta base fora do motor pode mudar a vontade que nenhuma nota fica velha.
    Tudo sai do proprio artefato da rodada, sem consultar o banco.
    """
    if not cartas_com_mudanca_de_nota:
        return {"total": 0, "listadas": [], "sem_cadastro": 0, "fora_do_motor": 0}
    caminho = run_dir / "cartas-fisicas.csv"
    ficha: dict[str, dict[str, str]] = {}
    if caminho.is_file():
        try:
            with caminho.open("r", encoding="utf-8-sig", errors="replace", newline="") as arquivo:
                for linha in csv.DictReader(arquivo):
                    identificador = str(linha.get("card_id") or "").strip()
                    if identificador in cartas_com_mudanca_de_nota:
                        ficha[identificador] = {
                            "nome": str(linha.get("nome") or "").strip(),
                            "tipo": str(linha.get("tipo") or "").strip(),
                            "roda_motor": str(linha.get("roda_motor") or "").strip().lower(),
                        }
        except OSError:
            pass
    estado = _estado_no_motor(run_dir)
    ja_rodaram = set(estado.get("ja_rodaram") or [])
    na_fila = estado.get("na_fila") if isinstance(estado.get("na_fila"), dict) else {}
    listadas: list[dict[str, Any]] = []
    sem_cadastro = 0
    fora_do_motor = 0
    for identificador, motivos in cartas_com_mudanca_de_nota.items():
        dados = ficha.get(identificador)
        if dados is None:
            sem_cadastro += 1
            continue
        if dados["roda_motor"] not in ("true", "1", "sim", "t"):
            fora_do_motor += 1
            continue
        if identificador in ja_rodaram:
            situacao = "j\u00e1 rodou"
            recado = "tem nota publicada; d\u00e1 para rodar um lote avulso agora"
            if identificador in na_fila:
                recado = ("tem nota, MAS tamb\u00e9m est\u00e1 no lote " + str(na_fila[identificador].get("lote"))
                          + " (" + str(na_fila[identificador].get("estado_do_lote")) + "): "
                          + "se rodar avulso, a fila apaga quando voltar")
        elif identificador in na_fila:
            situacao = "est\u00e1 na fila"
            recado = ("no lote " + str(na_fila[identificador].get("lote")) + " ("
                      + str(na_fila[identificador].get("estado_do_lote"))
                      + "); esperar a fila, lote avulso seria sobrescrito")
        else:
            situacao = "nunca rodou"
            recado = "n\u00e3o tem nota nem est\u00e1 em lote; entra na primeira rodada"
        listadas.append({
            "card_id": identificador,
            "nome": dados["nome"] or ("carta " + identificador),
            "tipo": dados["tipo"],
            "motivos": motivos,
            "situacao": situacao,
            "recado": recado,
        })
    listadas.sort(key=lambda c: str(c["nome"]))
    return {
        "total": len(listadas),
        "listadas": listadas[:LISTA_MAXIMA_RERODAR],
        "sem_cadastro": sem_cadastro,
        "fora_do_motor": fora_do_motor,
    }


LIMITE_EXEMPLOS_NOVIDADE = 40


def _cartas_que_o_banco_conhece(run_dir: Path) -> set[str]:
    """Os card_id que o banco ja tinha antes desta leitura.

    Ordem do Luis (04/09/2026): carta que o banco nao conhece e NOVA, e tudo
    que ela traz e novo. Ela nunca pode aparecer como "mudou" - nao existe
    valor anterior para ter mudado. O baseline desta rodada e a lista do banco.
    """
    caminho = run_dir / "baseline-cartas-canonico.csv"
    conhecidas: set[str] = set()
    if not caminho.is_file():
        return conhecidas
    try:
        with caminho.open("r", encoding="utf-8-sig", errors="replace", newline="") as arquivo:
            for linha in csv.DictReader(arquivo):
                identificador = str(linha.get("card_id") or "").strip()
                if identificador:
                    conhecidas.add(identificador)
    except OSError:
        return set()
    return conhecidas


_LIMITE_EXEMPLOS_USO = 6


def _quem_usa_os_insumos(run_dir: Path, pedidos: dict[str, set[str]], nomes_de_habilidade: dict[str, str]) -> dict[str, dict[str, dict[str, Any]]]:
    """Para cada insumo citado no relatorio, quais cartas estao ligadas a ele hoje.

    Ordem do Luis (04/09/2026): todo insumo que pode estar preso a um card tem
    de vir com a resposta - esta ligado a alguma carta? quantas? quais? Sem
    isso nao da para saber se a pendencia e urgente ou se e so catalogo. Tudo
    sai do cartas-fisicas.csv desta rodada; nada vem do banco.
    """
    saida: dict[str, dict[str, dict[str, Any]]] = {
        grupo: {codigo: {"total": 0, "exemplos": []} for codigo in codigos}
        for grupo, codigos in pedidos.items()
    }
    if not any(pedidos.values()):
        return saida
    caminho = run_dir / "cartas-fisicas.csv"
    if not caminho.is_file():
        return saida
    por_nome = {str(nome).strip().casefold(): str(codigo) for codigo, nome in nomes_de_habilidade.items() if nome}

    def registrar(grupo: str, codigo: str, rotulo: str) -> None:
        alvo = saida.get(grupo, {}).get(codigo)
        if alvo is None:
            return
        alvo["total"] += 1
        if len(alvo["exemplos"]) < _LIMITE_EXEMPLOS_USO:
            alvo["exemplos"].append(rotulo)

    try:
        with caminho.open("r", encoding="utf-8-sig", errors="replace", newline="") as arquivo:
            for linha in csv.DictReader(arquivo):
                identificador = str(linha.get("card_id") or "").strip()
                nome = str(linha.get("nome") or "").strip() or ("carta " + identificador)
                rotulo = f"{nome} ({identificador})"
                if saida.get("impetos"):
                    for coluna in ("impeto_s1", "impeto_s2_cond"):
                        codigo = str(linha.get(coluna) or "").strip()
                        if codigo:
                            registrar("impetos", codigo, rotulo)
                if saida.get("habilidades") and por_nome:
                    try:
                        lista = json.loads(linha.get("habilidades") or "[]")
                    except (TypeError, ValueError):
                        lista = []
                    for item in lista if isinstance(lista, list) else []:
                        codigo = por_nome.get(str(item).strip().casefold())
                        if codigo:
                            registrar("habilidades", codigo, rotulo)
                if saida.get("playstyles"):
                    for coluna in ("slot_ofensivo_id", "slot_defensivo_id"):
                        codigo = str(linha.get(coluna) or "").strip()
                        if codigo:
                            registrar("playstyles", codigo, rotulo)
    except OSError:
        pass
    return saida


def _texto_do_uso(dados: Any) -> str:
    """Frase curta e direta: tem carta usando isto agora, ou nao tem."""
    if not isinstance(dados, dict):
        return ""
    total = int(dados.get("total") or 0)
    if not total:
        return " \u2014 <b>nenhuma carta usa</b>"
    exemplos = dados.get("exemplos") or []
    quem = "; ".join(str(item) for item in exemplos)
    reticencia = "\u2026" if total > len(exemplos) else ""
    return f" \u2014 <b>{total} carta(s)</b>: {quem}{reticencia}"


def _completar_novidades(run_dir: Path, novidades: dict[str, Any], model_inputs: Any = None) -> dict[str, Any]:
    """Fecha as perguntas do dono sobre o que entrou de novo.

    Duas coisas que o relatorio nao respondia: relacao nova entrou em carta que
    ja existia ou em carta que chegou agora, e ímpeto novo tem alguma carta
    usando ele para conferir na tela. As duas saem da propria leitura, do
    arquivo cartas-fisicas.csv desta rodada. Nada vem do banco.
    """
    cartas_novas = set(novidades.get("cartas_novas") or [])
    impetos_novos = set(novidades.get("impetos_novos") or [])
    fichas: dict[str, dict[str, str]] = {}
    uso_impeto: dict[str, list[str]] = {codigo: [] for codigo in impetos_novos}
    caminho = run_dir / "cartas-fisicas.csv"
    if caminho.is_file():
        interessa = set(cartas_novas)
        for dados in (novidades.get("relacoes_novas") or {}).values():
            interessa.update((dados.get("cartas") or [])[:LIMITE_EXEMPLOS_NOVIDADE * 4])
        try:
            with caminho.open("r", encoding="utf-8-sig", errors="replace", newline="") as arquivo:
                for linha in csv.DictReader(arquivo):
                    identificador = str(linha.get("card_id") or "").strip()
                    if identificador in interessa:
                        fichas[identificador] = {
                            "nome": str(linha.get("nome") or "").strip(),
                            "posicao": str(linha.get("posicao") or "").strip(),
                            "nacionalidade": str(linha.get("nacionalidade") or "").strip(),
                        }
                    if impetos_novos:
                        for coluna in ("impeto_s1", "impeto_s2_cond"):
                            codigo = str(linha.get(coluna) or "").strip()
                            if codigo and codigo in uso_impeto and len(uso_impeto[codigo]) < 8:
                                nome = str(linha.get("nome") or "").strip() or ("carta " + identificador)
                                uso_impeto[codigo].append(f"{nome} ({identificador})")
        except OSError:
            pass

    def rotulo(identificador: str) -> str:
        ficha = fichas.get(identificador)
        if not ficha or not ficha.get("nome"):
            return "carta " + identificador
        partes = [valor for valor in (ficha.get("posicao"), ficha.get("nacionalidade")) if valor]
        sufixo = " \u00b7 ".join(partes)
        return f"{ficha['nome']} ({sufixo})" if sufixo else ficha["nome"]

    relacoes: list[dict[str, Any]] = []
    for tabela, dados in sorted((novidades.get("relacoes_novas") or {}).items(), key=lambda par: -par[1]["total"]):
        cartas = dados.get("cartas") or []
        em_carta_nova = [c for c in cartas if c in cartas_novas]
        em_carta_antiga = [c for c in cartas if c not in cartas_novas]
        relacoes.append({
            "tabela": tabela,
            "rotulo": TABELA_NA_TELA.get(tabela, tabela.replace("_", " ")),
            "total": int(dados.get("total") or 0),
            "cartas_novas": len(em_carta_nova),
            "cartas_antigas": len(em_carta_antiga),
            "exemplos_carta_antiga": [rotulo(c) for c in em_carta_antiga[:LIMITE_EXEMPLOS_NOVIDADE]],
        })
    novidades = dict(novidades)
    novidades["relacoes_detalhe"] = relacoes
    novidades["cartas_novas_rotuladas"] = [rotulo(c) for c in (novidades.get("cartas_novas") or [])[:LIMITE_EXEMPLOS_NOVIDADE]]
    novidades["uso_impeto"] = uso_impeto
    return novidades


def _presentation_context(run_dir: Path, samples: list[dict[str, Any]], extra_card_ids: Any = ()) -> dict[str, Any]:
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
    wanted_cards.update(key for key in (_stable_key(item) for item in extra_card_ids) if key is not None)
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
        "clube_jogo": {},
        "estilo_jogo_tecnico": {},
        "playstyle": {},
        "nacionalidade_jogo": {},
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
                    "clube_jogo": "codigo_jogo",
                    "estilo_jogo_tecnico": "codigo",
                    "playstyle": "id_jogo",
                    "nacionalidade_jogo": "codigo_jogo",
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
    identidade = sample.get("identity")
    if isinstance(identidade, dict) and identidade:
        rotulo = _identity_label(identidade, context)
        if rotulo:
            return rotulo
    return _family_label(str(family_key or sample.get("family") or "dados"))


def _human_field_name(value: Any) -> str | None:
    """Sempre o nome de tela, e o nome tecnico entre parenteses junto.

    Ordem do Luis (04/09/2026): quem le o relatorio nao decora nome de coluna.
    O rotulo em portugues vem primeiro; o nome tecnico fica ao lado para quem
    for conferir no banco.
    """
    if not isinstance(value, str) or not value:
        return None
    partes = value.split(".")
    coluna = partes[-1]
    tabela = partes[-2] if len(partes) >= 2 else ""
    rotulo = FIELD_LABELS.get(coluna) or coluna.replace("_", " ")
    onde = TABELA_NA_TELA.get(tabela)
    if onde:
        return f"{rotulo} \u00b7 {onde} ({tabela}.{coluna})"
    if tabela:
        return f"{rotulo} ({tabela}.{coluna})"
    return f"{rotulo} ({coluna})"


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
    if kind == "deferred":
        return (
            str(raw.get("motivo") or "")
            or "O item foi lido no jogo, mas ainda não tem referência canônica no banco. "
            "Ele fica de fora desta rodada, sem travar o resto, e volta a ser conferido na próxima varredura."
        )
    if kind == "historical_unresolved":
        return (
            "Este registro pertence ao arquivo histórico Steam e foi preservado "
            "fora da comparação com o catálogo atual. Ele não representa uma "
            "mudança no jogo nem uma divergência do banco enquanto o formato "
            "histórico não tiver um leitor semanticamente comprovado."
        )
    changed = _campos_que_mudaram(raw)
    if changed:
        fields = [name for name in (_human_field_name(item.get("campo")) for item in changed) if name]
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


def _scan_classification_samples(result_path: Path, sample_limit: int, timeout_seconds: float, cartas_do_banco: set[str] | None = None) -> dict[str, Any]:
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
    rerodar: dict[str, set[str]] = {}
    cartas_novas: set[str] = set()
    relacoes_novas: dict[str, dict[str, Any]] = {}
    impetos_novos: set[str] = set()
    tecnicos_novos: set[str] = set()
    novos_avulsos: dict[str, int] = {}
    cartas_conhecidas = cartas_do_banco or set()
    linhas_de_carta_nova: dict[str, int] = {}
    descontos: dict[str, dict[str, int]] = {}

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

    def register_total(report: str, entry: dict[str, Any], kind: str = "") -> None:
        """Calcula totais reais sem reter o JSON técnico inteiro em memória."""
        family_key = _report_family(report)
        total = family_totals.setdefault(family_key, {
            "entities": set(),
            "campos": {},
            "differences": 0,
        })
        identity = _entry_identity(entry)
        if identity:
            total["entities"].add(json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        carta_alterada = identity.get("card_id") if isinstance(identity, dict) else None
        tabela_destino = _tabela_do_registro(entry)
        # Carta que o banco nao conhece e nova por inteiro. Se algum comparador
        # classificou uma linha dela como "alterada", isso e ruido: nao existe
        # valor anterior. A linha vira novidade e sai da secao do que mudou.
        if (
            cartas_conhecidas
            and carta_alterada is not None
            and str(carta_alterada) not in cartas_conhecidas
            and kind in ("altered", "removed")
        ):
            rotulo_tabela = tabela_destino or family_key
            linhas_de_carta_nova[rotulo_tabela] = linhas_de_carta_nova.get(rotulo_tabela, 0) + 1
            alvo_desconto = descontos.setdefault(report, {})
            alvo_desconto[kind] = alvo_desconto.get(kind, 0) + 1
            cartas_novas.add(str(carta_alterada))
            return
        if kind == "new":
            if family_key == "cartas" and carta_alterada is not None:
                cartas_novas.add(str(carta_alterada))
            elif family_key == "relacoes":
                alvo = relacoes_novas.setdefault(tabela_destino or "relacao", {"total": 0, "cartas": set()})
                alvo["total"] += 1
                if carta_alterada is not None:
                    alvo["cartas"].add(str(carta_alterada))
            elif family_key == "impetos":
                codigo = identity.get("codigo_impeto") if isinstance(identity, dict) else None
                if codigo is not None:
                    impetos_novos.add(str(codigo))
                else:
                    novos_avulsos[family_key] = novos_avulsos.get(family_key, 0) + 1
            elif family_key == "tecnicos":
                alvo_id = None
                if isinstance(identity, dict):
                    for chave in ("tecnico_id", "id", "coach_id"):
                        if identity.get(chave) is not None:
                            alvo_id = identity[chave]
                            break
                if alvo_id is not None:
                    tecnicos_novos.add(str(alvo_id))
                else:
                    novos_avulsos[family_key] = novos_avulsos.get(family_key, 0) + 1
            else:
                novos_avulsos[family_key] = novos_avulsos.get(family_key, 0) + 1
        changed = _campos_que_mudaram(entry)
        if changed:
            total["differences"] += len(changed)
            for item in changed:
                field_key = item.get("campo")
                if not field_key:
                    continue
                campo = total["campos"].setdefault(str(field_key), {"linhas": 0, "exemplos": []})
                campo["linhas"] += 1
                if len(campo["exemplos"]) < FIELD_EXAMPLE_LIMIT:
                    campo["exemplos"].append({
                        "chave": identity,
                        "banco": item.get("banco"),
                        "jogo": item.get("jogo"),
                    })
                # Carta que teve MEXIDA numa coluna que entra na nota precisa ser
                # rodada de novo. Endereco, hash e rotulo nao contam.
                if carta_alterada is None:
                    continue
                partes = str(field_key).split(".")
                tabela_do_campo = partes[-2] if len(partes) >= 2 else tabela_destino
                coluna = partes[-1]
                motivo = COLUNAS_QUE_MUDAM_NOTA.get(tabela_do_campo, {}).get(coluna)
                if motivo:
                    alvo = rerodar.setdefault(str(carta_alterada), set())
                    alvo.add(motivo)
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
                    register_total(report_key, entry, current_kind)
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
                        register_total(report_key, entry, current_kind)
                        if capture_sample:
                            append_sample(report_key, current_kind, entry)
                    capture_lines = []
                    capture_sample = False
    serialized_totals = {
        family: {
            "entities_affected": len(total["entities"]),
            "field_differences": int(total["differences"]),
            "information_count": len(total["campos"]),
            "campos_divergentes": [
                {"campo": nome, "linhas": dados["linhas"], "exemplos": dados["exemplos"]}
                for nome, dados in sorted(total["campos"].items(), key=lambda par: (-par[1]["linhas"], par[0]))
                if not _e_endereco(nome)
            ][:FIELD_ROW_LIMIT],
            "campos_de_endereco": [
                {"campo": nome, "linhas": dados["linhas"], "exemplos": dados["exemplos"]}
                for nome, dados in sorted(total["campos"].items(), key=lambda par: (-par[1]["linhas"], par[0]))
                if _e_endereco(nome)
            ][:FIELD_ROW_LIMIT],
        }
        for family, total in family_totals.items()
    }
    novidades = {
        "cartas_novas": sorted(cartas_novas),
        "relacoes_novas": {
            tabela: {"total": dados["total"], "cartas": sorted(dados["cartas"])}
            for tabela, dados in relacoes_novas.items()
        },
        "impetos_novos": sorted(impetos_novos),
        "tecnicos_novos": sorted(tecnicos_novos),
        "novos_avulsos": novos_avulsos,
        "linhas_de_carta_nova": linhas_de_carta_nova,
    }
    for relatorio, baldes in descontos.items():
        alvo = counts.get(relatorio)
        if not alvo:
            continue
        for kind, quantos in baldes.items():
            alvo[kind] = max(0, int(alvo.get(kind) or 0) - quantos)
            alvo["new"] = int(alvo.get("new") or 0) + quantos
    return {
        "counts": counts,
        "samples": samples,
        "complete": complete,
        "real_totals": serialized_totals,
        "rerodar": {k: sorted(v) for k, v in rerodar.items()},
        "novidades": novidades,
    }


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
    cartas_do_banco = _cartas_que_o_banco_conhece(result_path.parent)
    varredura = _scan_classification_samples(result_path, sample_limit, timeout_seconds, cartas_do_banco)
    report_counts = varredura["counts"]
    samples = varredura["samples"]
    scan_complete = varredura["complete"]
    real_totals = varredura["real_totals"]
    cartas_com_mudanca_de_nota = varredura["rerodar"]
    novidades = varredura["novidades"]
    run_dir = result_path.parent
    exemplo_card_ids = [
        (exemplo.get("chave") or {}).get("card_id")
        for total in real_totals.values()
        for campo in (total.get("campos_divergentes") or [])
        for exemplo in (campo.get("exemplos") or [])
        if isinstance(exemplo.get("chave"), dict)
    ]
    cartas_para_rotular = list(exemplo_card_ids)
    cartas_para_rotular.extend(novidades.get("cartas_novas") or [])
    for dados in (novidades.get("relacoes_novas") or {}).values():
        cartas_para_rotular.extend((dados.get("cartas") or [])[:60])
    presentation = _presentation_context(run_dir, samples, cartas_para_rotular)
    rerodar = _cartas_para_rerodar(run_dir, cartas_com_mudanca_de_nota)
    novidades = _completar_novidades(run_dir, novidades, model_inputs=header.get("engine_inputs"))
    insumos_do_motor = header.get("engine_inputs") if isinstance(header.get("engine_inputs"), dict) else {}
    pedidos_de_uso: dict[str, set[str]] = {}
    for grupo in insumos_do_motor.get("grupos") or []:
        if not isinstance(grupo, dict):
            continue
        chave = str(grupo.get("chave") or "")
        alvo = pedidos_de_uso.setdefault(chave, set())
        for campo in ("ausente_do_banco", "sem_valoracao", "sem_nome", "sem_etiqueta_do_jogo"):
            for item in grupo.get(campo) or []:
                alvo.add(str(item.get("id") if isinstance(item, dict) else item))
    nomes_de_habilidade = {
        str(chave): str(_first_human_label(linha) or "")
        for chave, linha in (presentation.get("catalogs", {}).get("habilidade_jogo") or {}).items()
    }
    nomes_de_habilidade.update({
        str(chave): str(linha.get("nome_en") or "")
        for chave, linha in (presentation.get("catalogs", {}).get("habilidade_jogo") or {}).items()
        if isinstance(linha, dict) and linha.get("nome_en")
    })
    uso_dos_insumos = _quem_usa_os_insumos(run_dir, pedidos_de_uso, nomes_de_habilidade)
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
        "engine_inputs": header.get("engine_inputs") if isinstance(header.get("engine_inputs"), dict) else {},
        "rerodar": rerodar,
        "novidades": novidades,
        "uso_dos_insumos": uso_dos_insumos,
        "artifacts": _artifact_references(run_dir),
        "presentation": presentation,
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
        "engine_inputs": model["engine_inputs"],
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
    if type_key == "deferred":
        return {
            "title": "Item adiado para a próxima varredura",
            "meaning": "O jogo trouxe este item, mas ele ainda não tem referência no banco, então a procedência do vínculo não pôde ser montada nesta rodada.",
            "today": "Não. Ele fica de fora desta conferência sem derrubar o resto: as demais partes continuam sendo conferidas e liberadas normalmente.",
            "blocks": "Não bloqueia nada. Ele simplesmente não entra no pacote desta rodada.",
            "action": "Depende do motivo. Se o que falta é a própria linha no banco, ele não se resolve sozinho: sai daqui quando o item que ele depende for cadastrado. Rodar a varredura de novo, por si, não muda nada.",
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


_INPUT_ABSENT_WHOLE = (
    "{total} novo(s) que o jogo entrega completo(s), com nome e pontua\u00e7\u00e3o no pr\u00f3prio arquivo. "
    "Sobe e a pend\u00eancia acaba."
)
_INPUT_ABSENT_MIXED = (
    "{total} ainda n\u00e3o existe(m) no banco: {completos} vem(v\u00eam) completo(s) e "
    "{incompletos} vem(v\u00eam) incompleto(s) do pr\u00f3prio jogo."
)
_INPUT_ABSENT_BLIND = (
    "{total} ainda n\u00e3o existe(m) em <code>{tabela}</code>. O cat\u00e1logo f\u00edsico n\u00e3o publica nome nem "
    "pontua\u00e7\u00e3o, ent\u00e3o s\u00f3 d\u00e1 para conferir depois que subir."
)

_INPUT_SITUATIONS = (
    {
        "chave": "ausente_do_banco",
        "decisao": "Aprovo que suba",
        "texto": "",
    },
    {
        "chave": "ausente_incompleto_no_jogo",
        "decisao": "Sobe e continua pendente",
        "texto": (
            "{total} item{plural} que o pr\u00f3prio jogo j\u00e1 entrega sem nome ou sem pontua\u00e7\u00e3o. "
            "Sobe assim e volta a ser apontado em toda varredura at\u00e9 o jogo publicar o que falta."
        ),
    },
    {
        "chave": "sem_valoracao",
        "decisao": "Corrigir no banco antes de subir",
        "texto": (
            "{total} {verbo} no banco sem pontua\u00e7\u00e3o definida ({criterio}). "
            "Se rodar assim, o motor trata como zero."
        ),
    },
    {
        "chave": "sem_nome",
        "decisao": "Preencher \u00e0 m\u00e3o no banco",
        "texto": (
            "{total} {verbo} no banco sem nome de exibi\u00e7\u00e3o. "
            "A tela mostra o c\u00f3digo cru no lugar da etiqueta."
        ),
    },
    {
        "chave": "sem_etiqueta_do_jogo",
        "decisao": "Estou ciente, n\u00e3o trava",
        "texto": (
            "{total} {verbo} sem chave de texto oficial do jogo (se\u00e7\u00e3o + id do all.str). "
            "O nome, quando existir, tem de vir de fora ou da m\u00e3o do dono."
        ),
    },
)


_INPUT_CATALOGS = {
    "habilidades": "habilidade_jogo",
    "impetos": "impeto_jogo",
    "tecnicos": "tecnico_jogo",
    "playstyles": "playstyle",
}


def _input_code_label(grupo: str, codigo: Any, context: dict[str, Any], rotulos: dict[str, Any] | None = None) -> str:
    """Codigo do insumo com o nome que aparece na tela do jogo ao lado.

    Insumo que o banco ainda nao conhece nao tem rotulo canonico para consultar;
    nesse caso vale o nome que o proprio arquivo do jogo publicou na leitura.
    """
    tabela = _INPUT_CATALOGS.get(grupo)
    nome = None
    if tabela == "impeto_jogo":
        try:
            nome = resolve_impetus_presentation_label(context.get("reading_contract", {}), int(codigo))["rotulo"]
        except (TypeError, ValueError):
            nome = None
    if not nome and tabela:
        nome = _first_human_label(_presentation_row(context, tabela, codigo))
    if not nome and isinstance(rotulos, dict):
        do_jogo = rotulos.get(str(codigo))
        if isinstance(do_jogo, str) and do_jogo.strip():
            nome = do_jogo.strip()
    if nome:
        return f"{nome} ({codigo})"
    # Ordem do Luis: nunca mostrar codigo cru sozinho. Se nao ha nome em lugar
    # nenhum, o relatorio diz isso com todas as letras.
    generico = _INPUT_GROUP_LABELS.get(grupo, "item")
    return f"{generico} {codigo} \u2014 sem nome em lugar nenhum ainda"


# Fonte: resposta do ChatGPT trazida pelo Luis em 04/09/2026 -
# "0 significa ausencia; 136 significa vaga livre". O 136 nao e impeto: e a marca de
# que o slot esta vago. Cobrar nome ou pontuacao dele e cobrar para sempre uma coisa
# que nunca vai existir.
CODIGO_DE_VAGA_LIVRE = "136"


_INPUT_GROUP_LABELS = {
    "impetos": "\u00cdmpeto",
    "habilidades": "Habilidade",
    "tecnicos": "T\u00e9cnico",
    "playstyles": "Estilo de jogo",
}


_CHANGE_KIND_LABELS = {
    "new": "NOVO no jogo \u2014 o banco ainda n\u00e3o conhece",
    "altered": "ALTERADO \u2014 j\u00e1 existia no banco e o jogo mudou",
    "removed": "N\u00c3O APARECEU no jogo atual",
    "new+altered": "NOVO no jogo (tamb\u00e9m classificado como alterado)",
    "altered+new": "NOVO no jogo (tamb\u00e9m classificado como alterado)",
    "?": "classifica\u00e7\u00e3o n\u00e3o declarada nesta varredura",
}


def _render_rerodar(model: dict[str, Any]) -> str:
    """Pergunta 3: precisa rodar o motor de novo?"""
    esc = lambda value: html.escape(_compact(value), quote=True)
    dados = model.get("rerodar") if isinstance(model.get("rerodar"), dict) else {}
    total = int(dados.get("total") or 0)
    fora_do_motor = int(dados.get("fora_do_motor") or 0)
    novidades = model.get("novidades") if isinstance(model.get("novidades"), dict) else {}
    cartas_novas = len(novidades.get("cartas_novas") or [])
    primeira_rodada = ""
    if cartas_novas:
        primeira_rodada = (
            "<p class=\"muted\"><b>" + esc(cartas_novas) + " carta(s) novas</b> desta leitura nunca rodaram "
            "e n\u00e3o est\u00e3o em lote nenhum. Depois de cadastradas, elas entram na primeira rodada \u2014 "
            "n\u00e3o \u00e9 refazer nota, \u00e9 calcular pela primeira vez.</p>"
        )
    nota_fora = ""
    if fora_do_motor:
        nota_fora = ("<p class=\"muted\">Outras " + esc(fora_do_motor) + " carta(s) tiveram dado de nota mexido, "
                     "mas o motor n\u00e3o roda essas cartas, ent\u00e3o n\u00e3o h\u00e1 nota velha para refazer.</p>")
    if not total:
        return (
            "<section class=\"pergunta ok\">"
            "<h2>E o motor, precisa rodar de novo?</h2>"
            "<p class=\"veredito ok\">N\u00c3O</p>"
            "<p>Nada do que mudou no jogo atinge carta que o motor roda. "
            "As notas j\u00e1 calculadas continuam valendo.</p>" + primeira_rodada + nota_fora + "</section>"
        )
    listadas = dados.get("listadas") or []
    linhas = "".join(
        "<tr><td><b>" + esc(c.get("nome")) + "</b></td><td>" + esc(c.get("tipo")) + "</td>"
        "<td>" + esc("; ".join(c.get("motivos") or [])) + "</td>"
        "<td><b>" + esc(c.get("situacao") or "?") + "</b><br><span class=\"muted\">"
        + esc(c.get("recado") or "") + "</span></td>"
        "<td><code class=\"muted\">" + esc(c.get("card_id")) + "</code></td></tr>"
        for c in listadas
    )
    corte = ("<p class=\"muted\">Mostrando " + esc(len(listadas)) + " de " + esc(total) + ".</p>") if total > len(listadas) else ""
    return (
        "<section class=\"pergunta alerta\">"
        "<h2>E o motor, precisa rodar de novo?</h2>"
        "<p class=\"veredito alerta\">SIM \u2014 " + esc(total) + " carta(s)</p>"
        "<p>O jogo mudou dado que entra na nota destas cartas. Rode-as de novo depois que a fila atual terminar.</p>"
        "<div class=\"table-wrap\"><table><thead><tr><th>Carta</th><th>Tipo</th>"
        "<th>O que mudou nela</th><th>Onde ela est\u00e1 no motor</th><th>c\u00f3digo</th>"
        "</tr></thead><tbody>" + linhas + "</tbody></table></div>"
        + corte + primeira_rodada + nota_fora + "</section>"
    )


def _render_o_que_e_novo(model: dict[str, Any]) -> str:
    """Pergunta 2: o que entrou de novo no jogo.

    Uma linha por assunto, com o nome que aparece na tela do jogo. Ordem do
    Luis (04/09/2026): nao repetir o mesmo assunto em duas linhas, nao mostrar
    codigo sozinho e dizer, para cada coisa nova, se existe carta usando ela
    para ele conferir na tela.
    """
    esc = lambda value: html.escape(_compact(value), quote=True)
    context = model.get("presentation") if isinstance(model.get("presentation"), dict) else {}
    novidades = model.get("novidades") if isinstance(model.get("novidades"), dict) else {}
    inputs = model.get("engine_inputs") if isinstance(model.get("engine_inputs"), dict) else {}
    grupos_insumo = {
        str(grupo.get("chave")): grupo
        for grupo in (inputs.get("grupos") or [])
        if isinstance(grupo, dict)
    }
    linhas: list[str] = []

    def bloco(titulo: str, quantos: Any, resumo: str, detalhe: str = "") -> None:
        corpo = ""
        if detalhe:
            corpo = ("<details><summary>ver a lista</summary><p class=\"muted\">" + detalhe + "</p></details>")
        linhas.append(
            "<tr><td><b>" + esc(titulo) + "</b></td><td>" + esc(quantos) + "</td>"
            "<td>" + resumo + corpo + "</td></tr>"
        )

    # ------------------------------------------------------------ cartas novas
    cartas_novas = novidades.get("cartas_novas") or []
    if cartas_novas:
        rotuladas = novidades.get("cartas_novas_rotuladas") or []
        resumo = "Cartas que o jogo passou a ter e o banco ainda n\u00e3o conhece."
        detalhe = esc("; ".join(rotuladas))
        if len(cartas_novas) > len(rotuladas):
            detalhe += esc(f" \u2026 (mostrando {len(rotuladas)} de {len(cartas_novas)})")
        bloco("Cartas novas", len(cartas_novas), resumo, detalhe)

    # ------------------------------------------------------------ impetos novos
    impetos_novos = novidades.get("impetos_novos") or []
    grupo_impeto = grupos_insumo.get("impetos") or {}
    ausentes_impeto = [str(item) for item in (grupo_impeto.get("ausente_do_banco") or [])]
    codigos_impeto = sorted({*(str(c) for c in impetos_novos), *ausentes_impeto}, key=lambda v: (len(v), v))
    if codigos_impeto:
        rotulos_impeto = grupo_impeto.get("rotulos_do_jogo") if isinstance(grupo_impeto.get("rotulos_do_jogo"), dict) else {}
        uso = novidades.get("uso_impeto") if isinstance(novidades.get("uso_impeto"), dict) else {}
        pedacos: list[str] = []
        for codigo in codigos_impeto:
            nome = _input_code_label("impetos", codigo, context, rotulos_impeto)
            cartas = uso.get(codigo) or []
            if cartas:
                quem = "cartas que j\u00e1 usam ele nesta leitura: " + esc("; ".join(cartas))
            else:
                quem = "<b>nenhuma carta desta leitura usa ele</b> \u2014 entrou s\u00f3 na lista do jogo, n\u00e3o d\u00e1 para conferir numa carta ainda"
            pedacos.append("<div class=\"before-after\"><b>" + esc(nome) + "</b><br>" + quem + "</div>")
        bloco(
            "\u00cdmpetos novos",
            len(codigos_impeto),
            "\u00cdmpeto que passou a existir na lista do jogo.",
            "".join(pedacos),
        )

    # ----------------------------------------------------------- tecnicos novos
    grupo_tecnico = grupos_insumo.get("tecnicos") or {}
    ausentes_tecnico = [str(item) for item in (grupo_tecnico.get("ausente_do_banco") or [])]
    if ausentes_tecnico:
        rotulos_tecnico = grupo_tecnico.get("rotulos_do_jogo") if isinstance(grupo_tecnico.get("rotulos_do_jogo"), dict) else {}
        nomes = "; ".join(_input_code_label("tecnicos", item, context, rotulos_tecnico) for item in ausentes_tecnico)
        forca = grupo_tecnico.get("forca") if isinstance(grupo_tecnico.get("forca"), dict) else {}
        resumo = "T\u00e9cnico que o jogo passou a ter. T\u00e9cnico n\u00e3o fica preso a carta: entra no bolo que qualquer carta pode usar."
        if forca:
            if forca.get("muda_nota"):
                resumo += (" <b>Algum deles \u00e9 melhor que o melhor t\u00e9cnico que o banco j\u00e1 tem"
                           " (" + esc(forca.get("melhor_novo")) + " contra " + esc(forca.get("teto_atual")) + "),"
                           " ent\u00e3o carta j\u00e1 rodada pode mudar de nota.</b>")
            else:
                resumo += (" O melhor deles tem " + esc(forca.get("melhor_novo")) + " de "
                           + esc(forca.get("rotulo") or "for\u00e7a") + " e o banco j\u00e1 tem "
                           + esc(forca.get("teto_atual")) + ", ent\u00e3o <b>nenhuma nota j\u00e1 calculada muda por causa deles</b>.")
        linhas_tecnico = int((novidades.get("novos_avulsos") or {}).get("tecnicos") or 0) + len(novidades.get("tecnicos_novos") or [])
        if linhas_tecnico:
            resumo += (" No arquivo do jogo isso apareceu como " + esc(linhas_tecnico)
                       + " linha(s) nova(s): a ficha de cada um mais os dados de estilo, atributo e afinidade.")
        bloco("T\u00e9cnicos novos", len(ausentes_tecnico), resumo, esc(nomes))

    # ------------------------------------------------- habilidades e playstyles
    for chave, titulo in (("habilidades", "Habilidades novas"), ("playstyles", "Estilos de jogo novos")):
        grupo = grupos_insumo.get(chave) or {}
        ausentes = [str(item) for item in (grupo.get("ausente_do_banco") or [])]
        if not ausentes:
            continue
        rotulos = grupo.get("rotulos_do_jogo") if isinstance(grupo.get("rotulos_do_jogo"), dict) else {}
        nomes = "; ".join(_input_code_label(chave, item, context, rotulos) for item in ausentes)
        bloco(titulo, len(ausentes), "Item novo na lista do jogo.", esc(nomes))

    # ------------------------------------------------------ relacoes das cartas
    relacoes = novidades.get("relacoes_detalhe") or []
    total_relacoes = sum(int(item.get("total") or 0) for item in relacoes)
    if total_relacoes:
        partes: list[str] = []
        for item in relacoes:
            texto = ("<div class=\"before-after\"><b>" + esc(item.get("rotulo")) + "</b> \u2014 "
                     + esc(item.get("total")) + " linha(s) nova(s)<br>"
                     "em cartas que chegaram agora: " + esc(item.get("cartas_novas")) + " carta(s)<br>"
                     "em cartas que <b>j\u00e1 estavam no banco</b>: " + esc(item.get("cartas_antigas")) + " carta(s)")
            exemplos = item.get("exemplos_carta_antiga") or []
            if exemplos:
                texto += "<br><span class=\"muted\">" + esc("; ".join(exemplos)) + "</span>"
            partes.append(texto + "</div>")
        bloco(
            "Habilidades, posi\u00e7\u00f5es, atributos e estilos dentro das cartas",
            total_relacoes,
            "Linha nova dentro de uma carta. A parte que interessa \u00e9 a que caiu em carta que <b>j\u00e1 existia</b>: "
            "carta nova chega com tudo, ent\u00e3o o n\u00famero grande \u00e9 esperado.",
            "".join(partes),
        )

    # ------------------------------ linhas de carta nova que vieram mal rotuladas
    mal_rotuladas = novidades.get("linhas_de_carta_nova") or {}
    total_mal = sum(int(v or 0) for v in mal_rotuladas.values())
    if total_mal:
        partes = [
            "<div class=\"before-after\"><b>" + esc(TABELA_NA_TELA.get(tabela, tabela.replace("_", " ")))
            + "</b> \u2014 " + esc(quantos) + " linha(s)</div>"
            for tabela, quantos in sorted(mal_rotuladas.items(), key=lambda par: -par[1])
        ]
        bloco(
            "Outras linhas dessas cartas novas",
            total_mal,
            "Linhas que um comparador tinha marcado como <b>mudou</b>, mas s\u00e3o de carta que o banco "
            "n\u00e3o tem. Carta que o banco n\u00e3o conhece n\u00e3o pode ter mudado: entram como novas, junto com o resto da carta.",
            "".join(partes),
        )

    # -------------------------------------------------------- o que sobrou solto
    for familia, quantos in sorted((novidades.get("novos_avulsos") or {}).items(), key=lambda par: -par[1]):
        if familia in ("tecnicos", "relacoes", "cartas", "impetos"):
            continue
        bloco(_family_label(familia), quantos, "Registro novo nesta parte do jogo.")

    if not linhas:
        return (
            "<section class=\"pergunta ok\"><p class=\"eyebrow\">2 de 4</p>"
            "<h2>O que entrou de novo</h2><p class=\"veredito ok\">NADA</p>"
            "<p>Nenhuma carta, \u00edmpeto, t\u00e9cnico ou habilidade nova nesta leitura.</p></section>"
        )
    return (
        "<section class=\"pergunta\"><p class=\"eyebrow\">2 de 4</p>"
        "<h2>O que entrou de novo</h2>"
        "<p class=\"muted\">O jogo tem e o banco ainda n\u00e3o conhece. "
        "Um assunto por linha; clique em <b>ver a lista</b> para os nomes.</p>"
        "<div class=\"table-wrap\"><table><thead><tr><th>O que \u00e9</th><th>Quantos</th>"
        "<th>Quem, e d\u00e1 para conferir na tela?</th></tr></thead><tbody>" + "".join(linhas) + "</tbody></table></div></section>"
    )


def _render_deu_erro(model: dict[str, Any]) -> str:
    """Pergunta 1: a leitura travou em alguma coisa?"""
    esc = lambda value: html.escape(_compact(value), quote=True)
    totais = {kind: 0 for kind in DIVERGENCE_KINDS}
    for linha in model.get("family_summary") or []:
        for kind in DIVERGENCE_KINDS:
            totais[kind] += int((linha.get("counts") or {}).get(kind) or 0)
    aplicacao = model.get("application_status") if isinstance(model.get("application_status"), dict) else {}
    travas = [b for b in (aplicacao.get("blockers") or []) if isinstance(b, dict)]
    problemas = totais["repeated"] + totais["invalid"]
    leitura_completa = bool(model.get("divergence_summary", {}).get("scan_complete"))
    if not travas and not problemas and leitura_completa:
        return (
            "<section class=\"pergunta ok\"><p class=\"eyebrow\">1 de 4</p>"
            "<h2>Deu algum erro?</h2><p class=\"veredito ok\">N\u00c3O</p>"
            "<p>A leitura foi at\u00e9 o fim e nenhum registro ficou inv\u00e1lido ou repetido. "
            "Nada foi escrito no banco nesta etapa.</p></section>"
        )
    itens = []
    if not leitura_completa:
        itens.append("<li>A leitura n\u00e3o terminou: o arquivo de resultado atingiu o limite de tempo.</li>")
    if problemas:
        itens.append("<li>" + esc(problemas) + " registro(s) inv\u00e1lido(s) ou repetido(s) na leitura.</li>")
    for trava in travas:
        itens.append("<li>" + esc(trava.get("motivo") or "trava sem motivo declarado") + "</li>")
    return (
        "<section class=\"pergunta alerta\"><p class=\"eyebrow\">1 de 4</p>"
        "<h2>Deu algum erro?</h2><p class=\"veredito alerta\">SIM</p>"
        "<ul>" + "".join(itens) + "</ul></section>"
    )


def _render_field_divergences(model: dict[str, Any]) -> str:
    """Campo a campo: o que o banco tem hoje e o que o jogo traz nesta leitura.

    Ordem do Luis (04/09/2026): divergencia entre o jogo e o banco tem de
    aparecer no relatorio com os dois valores lado a lado, para ele decidir se
    substitui ou nao. Quem substitui e a selecao do Extrator; esta secao so
    mostra o que esta em jogo.
    """
    esc = lambda value: html.escape(_compact(value), quote=True)
    totals = model.get("divergence_summary", {}).get("real_totals_by_family") or {}
    context = model.get("presentation") if isinstance(model.get("presentation"), dict) else {}
    blocos: list[str] = []
    for family_key in sorted(totals):
        campos = (totals.get(family_key) or {}).get("campos_divergentes") or []
        if not campos:
            continue
        linhas: list[str] = []
        for campo in campos:
            exemplos = campo.get("exemplos") or []
            partes = []
            campo_tecnico = str(campo.get("campo") or "")
            for exemplo in exemplos:
                partes.append(
                    "<div class=\"before-after\"><b>" + esc(_identity_label(exemplo.get("chave"), context)) + "</b>"
                    "<br>o banco tem: " + esc(_value_label(campo_tecnico, exemplo.get("banco"), context))
                    + "<br>o jogo traz: " + esc(_value_label(campo_tecnico, exemplo.get("jogo"), context)) + "</div>"
                )
            campo_humano = _human_field_name(campo_tecnico) or campo_tecnico
            corpo = "".join(partes) if partes else "<span class=\"muted\">sem exemplo capturado</span>"
            linhas.append(
                "<tr><td>" + esc(campo_humano) + "</td>"
                "<td>" + esc(campo.get("linhas")) + "</td>"
                "<td><details><summary>ver exemplos</summary>" + corpo + "</details></td></tr>"
            )
        blocos.append(
            "<details class=\"family-group\"><summary><b>" + esc(_family_label(family_key)) + "</b>"
            "<span class=\"count-badge\">" + esc(len(campos)) + " campo(s)</span></summary>"
            "<div class=\"table-wrap\"><table><thead><tr><th>O que mudou</th><th>Linhas</th>"
            "<th>Antes e depois</th></tr></thead><tbody>"
            + "".join(linhas) + "</tbody></table></div></details>"
        )
    # O endereco fica embaixo, fechado. Ordem do Luis (04/09/2026): mudanca de lugar
    # dentro do arquivo do jogo nao e decisao, e atualizar e pronto - nao pode ocupar
    # a tela junto com o que mudou de verdade.
    linhas_endereco = 0
    detalhe_endereco: list[str] = []
    for family_key in sorted(totals):
        for campo in ((totals.get(family_key) or {}).get("campos_de_endereco") or []):
            linhas_endereco += int(campo.get("linhas") or 0)
            nome = _human_field_name(str(campo.get("campo") or "")) or campo.get("campo")
            detalhe_endereco.append(
                "<tr><td>" + esc(nome) + "</td><td>" + esc(campo.get("linhas")) + "</td>"
                "<td>" + esc(_family_label(family_key)) + "</td></tr>"
            )
    bloco_endereco = ""
    if linhas_endereco:
        bloco_endereco = (
            "<details class=\"family-group\"><summary><b>S\u00f3 mudou de lugar dentro do arquivo do jogo</b>"
            "<span class=\"count-badge\">" + esc(linhas_endereco) + " linha(s)</span></summary>"
            "<p class=\"muted\">A atualiza\u00e7\u00e3o empurrou os registros: o dado \u00e9 o mesmo, mudou o "
            "endere\u00e7o onde ele mora. N\u00e3o \u00e9 decis\u00e3o sua \u2014 s\u00f3 precisa ser atualizado.</p>"
            "<div class=\"table-wrap\"><table><thead><tr><th>O que</th><th>Linhas</th>"
            "<th>Parte do jogo</th></tr></thead><tbody>" + "".join(detalhe_endereco) + "</tbody></table></div></details>"
        )

    if not blocos:
        return (
            "<section class=\"pergunta ok\"><p class=\"eyebrow\">3 de 4</p>"
            "<h2>O que mudou no que j\u00e1 existia</h2><p class=\"veredito ok\">NADA</p>"
            "<p>Nenhum valor do jogo ficou diferente do que o banco tem.</p>" + bloco_endereco + "</section>"
        )
    return (
        "<section class=\"pergunta\"><p class=\"eyebrow\">3 de 4</p>"
        "<h2>O que mudou no que j\u00e1 existia</h2>"
        "<p class=\"muted\">Campo a campo, quantas linhas mudaram e o valor dos dois lados. "
        "Nada troca sozinho: sobe s\u00f3 o que voc\u00ea marcar. O que voc\u00ea preencheu \u00e0 m\u00e3o nunca \u00e9 sobrescrito.</p>"
        + "".join(blocos) + bloco_endereco + "</section>"
    )


def _decision_board(model: dict[str, Any]) -> str:
    """Lista numerada do que o dono decide nesta rodada.

    Cada bloco desta lista corresponde ao que aparece marcável na janela
    ESCOLHER O QUE ENVIAR do Extrator. Pendência aceita e item adiado ficam
    listados como ciência: não sobem e voltam na varredura seguinte.
    """
    esc = lambda value: html.escape(_compact(value), quote=True)
    context = model.get("presentation") if isinstance(model.get("presentation"), dict) else {}
    uso_dos_insumos = model.get("uso_dos_insumos") if isinstance(model.get("uso_dos_insumos"), dict) else {}
    application = model.get("application_status") if isinstance(model.get("application_status"), dict) else {}
    groups: dict[tuple[str, str, str], dict[str, int]] = {}
    for item in application.get("selectable_items") or []:
        if not isinstance(item, dict):
            continue
        tipos = item.get("tipos") if isinstance(item.get("tipos"), list) else []
        tipo = "+".join(str(t) for t in tipos) if tipos else "?"
        key = (str(item.get("familia") or "?"), str(item.get("tabela") or "?"), tipo)
        alvo = groups.setdefault(key, {"linhas": 0, "cartas": 0, "em_branco": set()})
        alvo["em_branco"].update(str(c) for c in (item.get("colunas_em_branco") or []))
        # A janela do Extrator ja vem agrupada em blocos: o que conta e quantas
        # linhas o bloco carrega, nao quantos blocos existem.
        alvo["linhas"] += int(item.get("itens_no_bloco") or 1)
        alvo["cartas"] += int(item.get("cartas_no_bloco") or 0)
    # Ordem do Luis (04/09/2026): item que nao pode subir tambem tem de dizer o que e,
    # com nome, e se tem carta ligada a ele. "278 itens" nao explica nada.
    reasons: dict[str, int] = {}
    recusados: dict[str, dict[str, Any]] = {}
    for item in application.get("not_selectable_items") or []:
        if isinstance(item, dict):
            motive = str(item.get("motivo") or "sem motivo declarado")
            reasons[motive] = reasons.get(motive, 0) + 1
            alvo = recusados.setdefault(motive, {"familias": set(), "identidades": [], "cartas": set()})
            alvo["familias"].add(str(item.get("familia") or ""))
            chave = item.get("chave") if isinstance(item.get("chave"), dict) else {}
            if chave.get("card_id") is not None:
                alvo["cartas"].add(str(chave["card_id"]))
            if len(alvo["identidades"]) < 6 and chave:
                alvo["identidades"].append(chave)
    deferred: dict[str, int] = {}
    for item in application.get("deferred_items") or []:
        if isinstance(item, dict):
            motive = str(item.get("motivo") or "adiado para a próxima varredura")
            deferred[motive] = deferred.get(motive, 0) + 1
    blocked = application.get("blocked_families") if isinstance(application.get("blocked_families"), dict) else {}
    accepted = [item for item in (application.get("report_observations") or []) if isinstance(item, dict)]
    inputs = model.get("engine_inputs") if isinstance(model.get("engine_inputs"), dict) else {}

    rows: list[str] = []
    number = 0
    for group in inputs.get("grupos") or []:
        if not isinstance(group, dict) or group.get("conferido") is not True:
            continue
        rotulo = esc(group.get("rotulo"))
        tabela = esc(group.get("tabela"))
        criterio = esc(group.get("criterio_valoracao"))
        for situacao in _INPUT_SITUATIONS:
            total = int(group.get(situacao["chave"] + "_total") or 0)
            if not total:
                continue
            decisao = situacao["decisao"]
            if situacao["chave"] == "ausente_do_banco":
                completos = int(group.get("ausente_completo_no_jogo_total") or 0)
                incompletos = int(group.get("ausente_incompleto_no_jogo_total") or 0)
                if group.get("confere_ausente_no_jogo") is not True:
                    detalhe = _INPUT_ABSENT_BLIND.format(total=total, tabela=tabela)
                elif incompletos:
                    detalhe = _INPUT_ABSENT_MIXED.format(total=total, tabela=tabela, completos=completos, incompletos=incompletos)
                else:
                    detalhe = _INPUT_ABSENT_WHOLE.format(total=total)
                    decisao = "Aprovo que suba"
            else:
                detalhe = situacao["texto"].format(
                    total=total,
                    plural="" if total == 1 else "s",
                    verbo="est\u00e1" if total == 1 else "est\u00e3o",
                    tabela=tabela,
                    criterio=criterio,
                )
            listados = group.get(situacao["chave"]) or []
            grupo_chave = str(group.get("chave") or "")
            if grupo_chave == "impetos":
                listados = [
                    item for item in listados
                    if str(item.get("id") if isinstance(item, dict) else item) != CODIGO_DE_VAGA_LIVRE
                ]
                if not listados:
                    continue
                total = len(listados)
            rotulos_do_jogo = group.get("rotulos_do_jogo") if isinstance(group.get("rotulos_do_jogo"), dict) else {}
            uso_do_grupo = uso_dos_insumos.get(grupo_chave) or {}
            linhas_de_codigo: list[str] = []
            for item in listados[:12]:
                codigo = item.get("id") if isinstance(item, dict) else item
                nome = _input_code_label(grupo_chave, codigo, context, rotulos_do_jogo)
                linhas_de_codigo.append("<div>" + esc(nome) + _texto_do_uso(uso_do_grupo.get(str(codigo))) + "</div>")
            reticencia = "<div class=\"muted\">\u2026 e mais " + esc(len(listados) - 12) + "</div>" if len(listados) > 12 else ""
            exemplo = ""
            if linhas_de_codigo:
                exemplo = "<div class=\"muted\">" + "".join(linhas_de_codigo) + reticencia + "</div>"
            number += 1
            rows.append(
                f"<tr><td><b>{number}</b></td><td>{esc(decisao)}</td><td>{rotulo}</td>"
                f"<td>{detalhe}{exemplo}</td></tr>"
            )
    for (family, table, tipo), dados in sorted(groups.items(), key=lambda par: -par[1]["linhas"]):
        number += 1
        count = dados["linhas"]
        cartas = dados["cartas"]
        rotulo_tipo = _CHANGE_KIND_LABELS.get(tipo, "mudan\u00e7a classificada como " + tipo)
        onde = TABELA_NA_TELA.get(str(table).rsplit(".", 1)[-1], str(table).replace("_", " "))
        quanto = f"{count} linha(s)" + (f" em {cartas} carta(s)" if cartas else "")
        # Ordem do Luis (04/09/2026): novo e alterado tem destino diferente
        # depois de subir. Novo entra como linha nova e nao ha nota velha para
        # refazer; alterado pode deixar velha a nota de carta ja rodada.
        if tipo == "new":
            destino = ("<b>Entra como linha nova.</b> Nada para rodar de novo no motor: "
                       "n\u00e3o existe nota anterior dessas linhas.")
        elif tipo == "altered":
            destino = ("<b>Sobrescreve o que o banco tem.</b> Carta que j\u00e1 tem nota e cujo dado de nota "
                       "mudou entra na fila do motor \u2014 a lista est\u00e1 no fim deste relat\u00f3rio.")
        else:
            destino = "Classifica\u00e7\u00e3o mista; confira as linhas antes de marcar."
        branco = ""
        if dados["em_branco"]:
            faltando = sorted(dados["em_branco"])
            nomes = ", ".join((_human_field_name(str(table).rsplit(".", 1)[-1] + "." + c) or c) for c in faltando[:6])
            branco = ("<br><span class=\"muted\">Nasce com estes campos em branco, porque o arquivo do jogo "
                      "n\u00e3o os entrega: " + esc(nomes) + "</span>")
        rows.append(
            f"<tr><td><b>{number}</b></td><td>Aprovo que suba</td>"
            f"<td>{esc(onde)}<br><span class=\"muted\">{esc(_family_label(family))} &middot; <code>{esc(table)}</code></span>"
            f"<br><b>{esc(rotulo_tipo)}</b></td>"
            f"<td>{esc(quanto)}, com destino, chave e proced\u00eancia conferidos.<br>{destino}{branco}</td></tr>"
        )
    for item in accepted:
        number += 1
        rows.append(
            f"<tr><td><b>{number}</b></td><td>Estou ciente, não sobe</td><td>{esc(item.get('catalogo'))}</td>"
            f"<td>{esc(item.get('motivo'))}<br><span class=\"muted\">Aceite registrado no contrato: {esc(item.get('aceita_motivo') or 'sem motivo gravado')}</span></td></tr>"
        )
    for motive, count in sorted(deferred.items(), key=lambda pair: -pair[1]):
        number += 1
        # Ordem do Luis (04/09/2026): nao escrever que volta na proxima varredura
        # quando o item depende de um cadastro que so o dono pode aprovar. Isso e
        # falso e o item ficaria preso para sempre sem ninguem perceber.
        depende_de_cadastro = "sem referência canônica" in motive
        recado = (
            "Preso até o item de que ele depende ser cadastrado. Rodar a varredura de novo não muda isto."
            if depende_de_cadastro else
            "Volta a ser conferido na próxima varredura."
        )
        rows.append(
            f"<tr><td><b>{number}</b></td><td>Fica pendente</td><td>{esc(count)} {'item adiado' if count == 1 else 'itens adiados'}</td>"
            f"<td>{esc(motive)}<br><span class=\"muted\">{esc(recado)}</span></td></tr>"
        )
    for family, family_reasons in sorted(blocked.items()):
        number += 1
        rows.append(
            f"<tr><td><b>{number}</b></td><td>Não entra nesta rodada</td><td>{esc(family)}</td>"
            f"<td>{esc('; '.join(str(reason) for reason in family_reasons))}</td></tr>"
        )
    for motive, count in sorted(reasons.items(), key=lambda pair: -pair[1]):
        number += 1
        info = recusados.get(motive) or {"familias": set(), "identidades": [], "cartas": set()}
        familias = ", ".join(_family_label(f) for f in sorted(info["familias"]) if f)
        cartas = len(info["cartas"])
        quem = ""
        if info["identidades"]:
            linhas_quem = [
                "<div>" + esc(_identity_label(chave, context)) + "</div>"
                for chave in info["identidades"]
            ]
            resto = ("<div class=\"muted\">\u2026 e mais " + esc(count - len(linhas_quem)) + "</div>") if count > len(linhas_quem) else ""
            quem = "<div class=\"muted\">" + "".join(linhas_quem) + resto + "</div>"
        onde = ""
        if familias:
            onde = "<br><span class=\"muted\">Parte do jogo: " + esc(familias)
            if cartas:
                onde += " \u00b7 " + esc(cartas) + " carta(s) envolvida(s)"
            onde += "</span>"
        rows.append(
            f"<tr><td><b>{number}</b></td><td>Não pode subir</td>"
            f"<td>{esc(count)} {'linha' if count == 1 else 'linhas'}{onde}</td>"
            f"<td>{esc(motive)}{quem}</td></tr>"
        )
    owner_total = int(inputs.get("valores_do_dono_total") or 0)
    if owner_total:
        number += 1
        tables = sorted({str(item.get("tabela")) for item in (inputs.get("valores_do_dono") or []) if isinstance(item, dict)})
        detalhes: list[str] = []
        for item in (inputs.get("valores_do_dono") or []):
            if not isinstance(item, dict):
                continue
            chave = item.get("chave") if isinstance(item.get("chave"), dict) else {}
            codigo = next((str(v) for v in chave.values()), "")
            uso = (uso_dos_insumos.get("impetos") or {}).get(codigo) if codigo else None
            # O nome vem do catalogo desta rodada, pela chave. O artefato de insumos
            # nao carrega o valor gravado - carrega tabela, chave, coluna e o porque.
            nome = _input_code_label("impetos", codigo, context) if codigo else ""
            detalhes.append(
                "<div><b>" + esc(nome) + "</b> \u00b7 " + esc(_human_field_name(str(item.get("tabela")) + "." + str(item.get("coluna"))) or item.get("coluna"))
                + _texto_do_uso(uso)
                + "<br><span class=\"muted\">" + esc(item.get("porque")) + "</span></div>"
            )
        lista = ("<div class=\"muted\">" + "".join(detalhes) + "</div>") if detalhes else ""
        rows.append(
            f"<tr><td><b>{number}</b></td><td>Protegido, nada a fazer</td>"
            f"<td>Valor preenchido à mão &middot; {esc(owner_total)} {esc('campo' if owner_total == 1 else 'campos')}</td>"
            f"<td>Em {esc(', '.join(tables))}. Sua correção manual prevalece mesmo quando o jogo informa outro valor. O envio de outros campos preserva essa escolha.{lista}</td></tr>"
        )

    inputs_note = ""
    if inputs.get("tudo_pronto") is True:
        inputs_note = "<p class=\"all-clear\">Insumos conferidos: habilidade, ímpeto, playstyle e técnico lidos do jogo já têm pontuação e nome definidos em clube_novo.</p>"
    if not rows:
        return "<section class=\"pergunta ok\"><p class=\"eyebrow\">4 de 4</p><h2>O que fazer com isso</h2>" + inputs_note + "<p class=\"veredito ok\">NADA</p></section>"
    return (
        "<section class=\"pergunta\"><p class=\"eyebrow\">4 de 4</p><h2>O que fazer com isso</h2>"
        "<p class=\"muted\">Cada linha abaixo corresponde a um bloco da janela <b>ESCOLHER O QUE ENVIAR</b> do Extrator. "
        "O que você marcar sobe; o que deixar em branco fica pendente e volta na próxima varredura.</p>"
        "<div class=\"table-wrap\"><table><thead><tr><th>#</th><th>Decisão</th><th>Item</th><th>O que é</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
        + inputs_note
        + "</section>"
    )


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


# O que entra na regua do otimizador, COLUNA a coluna. Endereco, procedencia e
# rotulo mudam a cada atualizacao da Konami e nao mexem em nota nenhuma.
# Coluna de endereco/procedencia: diz ONDE o dado mora dentro do arquivo do jogo,
# nao O QUE ele vale. Toda atualizacao do jogo empurra registros e mexe em dezenas de
# milhares dessas. Ordem do Luis (04/09/2026): endereco se atualiza e pronto, nao e
# decisao. Medido nesta rodada: 42.676 cartas e 207 impetos so mudaram de lugar.
_ENDERECO = re.compile(
    r"^(registro|bit|largura|arquivo|cpk|hash|endereco|fonte|presente|tamanho"
    r"|indice_registro|ordem_fisica|record_index|proveniencia|procedencia)"
)


def _e_endereco(campo: Any) -> bool:
    coluna = str(campo or "").rsplit(".", 1)[-1]
    return bool(_ENDERECO.match(coluna))


COLUNAS_QUE_MUDAM_NOTA = {
    "carta_jogo": {
        "altura": "altura", "peso": "peso", "pe": "pe dominante",
        "pe_ruim_uso": "uso do pe ruim", "pe_ruim_precisao": "precisao do pe ruim",
        "resistencia_lesao": "resistencia a lesoes", "forma": "forma fisica",
        "codigo_clube": "clube (liga o impeto condicional)",
        "codigo_liga": "liga (liga o impeto condicional)",
        "codigo_nacionalidade": "nacionalidade (liga o impeto condicional)",
        "codigo_nacionalidade_player_raw": "nacionalidade (liga o impeto condicional)",
    },
    "carta_atributo_jogo": {"valor": "valor de atributo"},
    "carta_habilidade_jogo": {"skill_id": "habilidade"},
    "carta_posicao_jogo": {"posicao_id": "posicao", "nivel_aptidao": "aptidao na posicao"},
    "carta_estilo_ia_jogo": {"bit_estilo_ia": "estilo de IA"},
    "carta_playstyle_jogo": {"playstyle_id": "estilo de jogo"},
    "carta_impeto_jogo": {"codigo_impeto": "impeto", "slot": "slot do impeto",
                          "condicional": "impeto condicional", "vaga": "vaga de impeto"},
}


LISTA_MAXIMA_RERODAR = 200
PRESENTATION_PAGE_SIZE = 10


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
            "deferred": "Adiados para a próxima varredura",
        }
        parts = [f"{labels.get(key, key)}: {int(counts.get(key, 0))}" for key in DIVERGENCE_KINDS if int(counts.get(key, 0))]
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
            "<section><details><summary><h2 style=\"display:inline\">Quais cartas podem entrar nos motores</h2></summary>"
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
            "<p class=\"read-only\"><b>Atenção à instalação:</b> esta rodada apenas gerou a prova local. A proteção só passa a valer dentro dos motores depois que a migração do banco e as duas conferências dos consumidores forem instaladas e validadas com leitura de volta.</p></details></section>"
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
            state_label = "Variação nova em relação à última varredura"
            today = "Sim. Este rótulo de variação da carta não existia na rodada anterior comparável. Isso pode ser uma pré-carga, mas não identifica uma box comercial."
        else:
            state_label = "Referência local desta rodada"
            today = "Ainda não é possível chamá-la de nova, porque não havia uma rodada anterior comparável. Esta leitura passa a ser a referência para a próxima varredura."
        radar_box_html += (
            "<article class=\"box-card\"><header><div><p class=\"eyebrow\">" + esc(state_label) + "</p><h3>" + esc(box.get("nome_box")) + "</h3></div>"
            "<span class=\"count-badge\">" + esc(_amount(box.get("quantidade_cartas"), "card", "cards")) + "</span></header>"
            "<p><b>Exemplos:</b> " + esc(examples) + ".</p><div class=\"answer-grid\"><div><b>O que significa</b><p>O arquivo físico liga estes cards a este rótulo de variação individual.</p></div>"
            "<div><b>Afeta os dados de hoje?</b><p>" + esc(today) + "</p></div>"
            "<div><b>O que fica bloqueado?</b><p>Este rótulo nunca é enviado como box e não libera card para os motores.</p></div>"
            "<div><b>O que você deve fazer</b><p>Use apenas como inventário técnico de variações pré-carregadas.</p></div></div></article>"
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
            "<h3>" + esc(_amount(cards_without_box, "registro físico possui card, mas não possui rótulo de variação", "registros físicos possuem card, mas não possuem rótulo de variação")) + "</h3></div>"
            "<span class=\"count-badge\">" + esc(_amount(cards_without_box, "card isolado", "cards isolados")) + "</span></header>"
            "<div class=\"answer-grid\"><div><b>O que significa</b><p>O arquivo trouxe o identificador do card, mas deixou vazio o rótulo da variação. O Extrator não inventou um texto.</p></div>"
            "<div><b>Afeta os dados de hoje?</b><p>Afeta somente este inventário técnico de variações.</p></div>"
            "<div><b>O que fica bloqueado?</b><p>Somente usar estes registros como variação conhecida. Eles não bloqueiam outras mudanças comprovadas e não entram no banco como box.</p></div>"
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
                str(record.get("nome_box_fisico") or "variação sem nome")
                + " — card " + str(record.get("card_id"))
                + " — registro " + str(record.get("record_index"))
            )
            if len(historical_examples) >= 8:
                break
        historical_details = "".join("<li>" + esc(example) + "</li>" for example in historical_examples)
        radar_ignored_html += (
            "<article class=\"warning-card info\"><header><div><p class=\"eyebrow\">Referência física antiga, fora dos lançamentos atuais</p>"
            "<h3>" + esc(_amount(historical_relations, "ligação de variação aponta para um card que não existe no jogo atual", "ligações de variação apontam para cards que não existem no jogo atual")) + "</h3></div>"
            "<span class=\"count-badge\">" + esc(_amount(historical_relations, "relação isolada", "relações isoladas")) + "</span></header>"
            "<div class=\"answer-grid\"><div><b>O que significa</b><p>O arquivo de variações ainda guarda a ligação completa, mas o mesmo identificador não aparece no Player.bin atual. Por isso ela é mantida apenas como referência física antiga.</p></div>"
            "<div><b>Afeta os dados de hoje?</b><p>Não. Estes cards não fazem parte da lista física atual e não são tratados como lançamento.</p></div>"
            "<div><b>O que fica bloqueado?</b><p>Somente esta ligação antiga fica fora do inventário atual, da publicação e do pacote. As boxes comerciais e os cards atuais continuam normalmente.</p></div>"
            "<div><b>O que você deve fazer</b><p>Nenhuma correção manual. Não recrie o card nem troque o identificador; o Extrator continuará conferindo a relação em futuras varreduras.</p></div></div>"
            + ("<details><summary>Detalhes técnicos</summary><ul>" + historical_details + "</ul></details>" if historical_details else "")
            + "</article>"
        )
    if radar.get("available"):
        comparison_status = radar_comparison.get("status")
        new_boxes = int((radar_counts.get("by_state") or {}).get("nova") or 0) if isinstance(radar_counts.get("by_state"), dict) else 0
        radar_intro = (
            f"Foram encontradas {_amount(radar_counts.get('boxes'), 'variação física', 'variações físicas')} ligadas a {_amount(radar_counts.get('cards_mapped'), 'card', 'cards')}. "
            + (f"{_amount(new_boxes, 'variação não existia', 'variações não existiam')} na rodada anterior comparável." if comparison_status == "comparado" else "Como ainda não havia uma rodada comparável, esta leitura é a primeira referência local e não chama todas as variações de novas.")
            + (f" Além disso, {_amount(ignored_total, 'registro sem relação card/variação comprovada foi isolado e não entrou no inventário', 'registros sem relação card/variação comprovada foram isolados e não entraram no inventário')}." if ignored_total else "")
        )
        integration_warning = ""
        if radar_integration.get("status") == "prepared_not_enabled":
            integration_warning = (
                "<article class=\"warning-card\"><header><div><p class=\"eyebrow\">Integração com o banco</p><h3>As ligações entre variação e card ainda não são gravadas no banco</h3></div></header>"
                "<div class=\"answer-grid\"><div><b>O que significa</b><p>O Extrator já possui identidade, conteúdo e origem para preparar essa integração, mas a tabela e o contrato de escrita ainda não foram instalados.</p></div>"
                "<div><b>Afeta os dados de hoje?</b><p>Sim, apenas para guardar a variação como informação durável. Os demais dados das cartas continuam sendo tratados normalmente.</p></div>"
                "<div><b>O que fica bloqueado?</b><p>Somente o envio automático da ligação variação/card ao banco. Publicar ou anunciar a carta não é bloqueado.</p></div>"
                "<div><b>O que você deve fazer</b><p>Não tente cadastrar a ligação por fora. Instale e valide a migração própria antes de habilitar este campo no pacote do Extrator.</p></div></div></article>"
            )
        radar_section = "<section><details><summary><h2 style=\"display:inline\">Inventário de variações de carta</h2></summary><p>" + esc(radar_intro) + "</p>" + radar_ignored_html + (radar_box_html or "<p class=\"all-clear\">Nenhum rótulo novo apareceu em relação à rodada anterior.</p>") + integration_warning + "</details></section>"
        radar_overview = f"{_amount(new_boxes, 'variação nova', 'variações novas')}" if comparison_status == "comparado" else "primeira referência de variações"
    else:
        radar_overview = "radar não disponível nesta rodada"
        radar_section = (
            "<section><h2>Inventário de variações de carta</h2><article class=\"warning-card\"><header><div><p class=\"eyebrow\">Variações físicas</p><h3>Esta rodada não possui o inventário de variações</h3></div></header>"
            "<div class=\"answer-grid\"><div><b>O que significa</b><p>Este resultado foi criado antes de o radar entrar no Extrator ou a leitura desse arquivo não terminou.</p></div>"
            "<div><b>Afeta os dados de hoje?</b><p>Pode impedir perceber uma nova variação nesta rodada, mas não altera os dados já conferidos das cartas.</p></div>"
            "<div><b>O que fica bloqueado?</b><p>Apenas a conclusão sobre variações novas. Publicação e envio de outras mudanças continuam separados.</p></div>"
            "<div><b>O que você deve fazer</b><p>Na próxima atualização, execute uma nova varredura com a versão atual do Extrator.</p></div></div></article></section>"
        )

    system_overview = (
        "<div class=\"system-grid\"><div class=\"system-card\"><b>Variações de carta</b><strong>" + esc(radar_overview) + "</strong><span>não identifica boxes comerciais</span></div>"
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
    decision_board = _decision_board(model)
    deu_erro = _render_deu_erro(model)
    o_que_e_novo = _render_o_que_e_novo(model)
    precisa_rodar = _render_rerodar(model)
    field_divergences = _render_field_divergences(model)
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
:root{{color-scheme:light;font-family:Segoe UI,Arial,sans-serif;color:#18212a;background:#f3f6f8}}*{{box-sizing:border-box}}body{{margin:0;background:#f3f6f8}}main{{max-width:1180px;margin:auto;padding:28px}}h1{{font-size:2rem;margin:4px 0 10px;line-height:1.15}}h2{{margin:0 0 10px;font-size:1.35rem}}h3{{margin:3px 0 0;font-size:1.1rem}}p{{line-height:1.5}}section{{background:#fff;border:1px solid #d7e0e7;border-radius:14px;padding:22px;margin:18px 0;box-shadow:0 2px 8px #16202a0d}}.hero{{border-top:7px solid #d89b13;padding:26px}}.hero.success{{border-color:#23804b}}.hero.error{{border-color:#c93a3a}}.eyebrow{{margin:0;color:#526372;text-transform:uppercase;letter-spacing:.06em;font-size:.78rem;font-weight:700}}.hero-text{{font-size:1.08rem;max-width:850px;margin:0 0 18px}}.next-action{{background:#fff7da;border:1px solid #efd37b;border-radius:10px;padding:16px 18px;margin:14px 0}}.hero.error .next-action{{background:#fff0f0;border-color:#efb5b5}}.hero.success .next-action{{background:#edfaF2;border-color:#a9dfbd}}.next-action h2{{font-size:1.05rem;margin:0 0 5px}}.read-only{{background:#edf6ff;border-left:5px solid #2774b8;padding:12px 14px;border-radius:6px;margin-top:14px}}.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:16px}}.stats.compact{{grid-template-columns:repeat(4,1fr)}}.stat{{background:#f7f9fb;border:1px solid #dce4ea;border-radius:10px;padding:12px}}.stat strong{{display:block;font-size:1.35rem}}.stat span{{color:#526372;font-size:.9rem}}.system-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px}}.system-card{{display:flex;flex-direction:column;gap:4px;background:#f2f8fd;border:1px solid #9bc5e8;border-radius:10px;padding:14px}}.system-card.warning{{background:#fffaf0;border-color:#e2c76f}}.system-card.success{{background:#edfaf2;border-color:#a9dfbd}}.system-card strong{{font-size:1.05rem}}.system-card span{{color:#526372}}.warning-card,.box-card{{border:1px solid #e2c76f;border-left:7px solid #d89b13;border-radius:12px;padding:18px;margin:14px 0;background:#fffaf0}}.box-card{{border-color:#9bc5e8;border-left-color:#2e79b7;background:#f2f8fd}}.warning-card.success{{border-color:#a9dfbd;border-left-color:#23804b;background:#edfaf2}}.warning-card.info{{border-color:#9bc5e8;border-left-color:#2e79b7;background:#f2f8fd}}.warning-card.error{{border-color:#efaaaa;border-left-color:#c93a3a;background:#fff3f3}}.warning-card header,.box-card header{{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}}.count-badge,.state,.pill{{display:inline-block;border-radius:999px;padding:5px 10px;font-weight:700;font-size:.82rem;background:#e9eef2;white-space:nowrap}}.answer-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px}}.answer-grid>div{{background:#fff;border:1px solid #e0e6eb;border-radius:9px;padding:12px}}.answer-grid p{{margin:5px 0 0}}.state.success{{background:#dcfce7;color:#166534}}.state.warning,.pill.known_pending,.pill.altered{{background:#fef3c7;color:#854d0e}}.state.info,.pill.historical_unresolved,.pill.new{{background:#e0f2fe;color:#075985}}.state.error,.pill.invalid,.pill.repeated{{background:#fee2e2;color:#991b1b}}.pill.removed{{background:#fce7f3;color:#9d174d}}table{{width:100%;border-collapse:collapse;margin-top:12px}}th,td{{padding:12px;border-bottom:1px solid #e4e9ed;text-align:left;vertical-align:top}}th{{background:#f7f9fb;color:#41515f;font-size:.88rem}}.table-wrap{{overflow-x:auto}}.muted{{color:#526372}}.filters{{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0}}label{{font-weight:700}}select{{margin-left:6px;padding:7px;border:1px solid #aebbc5;border-radius:6px;background:#fff}}.family-group,.type-group,.technical-details{{border:1px solid #d8e1e8;border-radius:10px;background:#fff;margin:10px 0}}.family-group>summary,.type-group>summary{{cursor:pointer;padding:14px;display:flex;justify-content:space-between;gap:12px;align-items:center}}.family-group>summary{{background:#f7f9fb;font-size:1.02em}}.type-group{{margin:10px 12px}}.type-group>summary{{background:#fcfdff}}.sample-list{{padding:0 12px}}.divergence{{border-left:5px solid #d89b13;padding:14px;margin:12px 0;background:#fffaf3;border-radius:8px}}.divergence h5{{margin:0;font-size:1.02em}}.technical-details{{margin:12px 0 0;background:#f7f9fb}}.technical-details summary{{cursor:pointer;padding:10px 12px;font-weight:700}}.technical-details dl{{padding:0 12px 12px}}dl{{display:grid;grid-template-columns:220px 1fr;gap:8px;margin:0}}dt{{font-weight:700}}dd{{margin:0;overflow-wrap:anywhere}}code{{font-family:Consolas,monospace;font-size:.88em}}.show-more{{margin:0 12px 14px;padding:9px 12px;border:1px solid #2774b8;border-radius:7px;background:#fff;color:#1d5e92;font-weight:700;cursor:pointer}}.hidden{{display:none!important}}ul{{padding-left:22px;overflow-wrap:anywhere}}.all-clear{{background:#edfaf2;border:1px solid #a9dfbd;padding:12px;border-radius:8px}}.before-after{{background:#f7f9fb;border:1px solid #e0e6eb;border-radius:7px;padding:8px;margin:6px 0;overflow-wrap:anywhere}}.capa{{border-top:8px solid #2774b8}}summary{{cursor:pointer;color:#1d5e92;font-weight:600}}td>details{{border:0;background:none;margin:0}}.pergunta{{border-left:8px solid #aebbc5}}.pergunta.ok{{border-left-color:#23804b}}.pergunta.alerta{{border-left-color:#c93a3a}}.veredito{{font-size:2rem;font-weight:800;margin:6px 0 10px;letter-spacing:.02em}}.veredito.ok{{color:#186c3e}}.veredito.alerta{{color:#a32020}}.score-alert{{border:3px solid #c93a3a;border-top-width:10px;background:#fff5f5}}.score-alert.ok{{border-color:#23804b;background:#f2fbf6}}.score-alert-title{{font-size:2.1rem;font-weight:800;letter-spacing:.02em;color:#a32020;margin:2px 0 12px;text-transform:uppercase}}.score-alert.ok .score-alert-title{{color:#186c3e}}.score-alert .count-badge{{background:#c93a3a;color:#fff;font-size:.86rem}}.score-alert .warning-card.success .count-badge{{background:#23804b}}.score-alert .warning-card:not(.success):not(.error) .count-badge{{background:#d89b13;color:#fff}}@media(max-width:760px){{main{{padding:12px}}h1{{font-size:1.6rem}}section,.hero{{padding:16px}}.stats,.stats.compact,.system-grid{{grid-template-columns:1fr 1fr}}.answer-grid{{grid-template-columns:1fr}}table{{font-size:.9em;min-width:760px}}dl{{grid-template-columns:1fr}}.family-group>summary,.type-group>summary,.warning-card header,.box-card header{{align-items:flex-start;flex-direction:column}}}}
</style></head><body><main>
<section class=\"capa\"><p class=\"eyebrow\">Leitura do jogo &middot; somente leitura, nada foi escrito no banco</p><h1>O que o jogo trouxe de diferente</h1><p class=\"hero-text\">Vers\u00e3o do jogo lida: <b>{esc(contract.get('versao_jogo'))}</b>.</p></section>
{deu_erro}
{o_que_e_novo}
{field_divergences}
{decision_board}
{precisa_rodar}
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
    boxes_path = run_dir / "boxes-resultado.json"
    boxes = None
    if boxes_path.is_file():
        boxes = json.loads(boxes_path.read_text(encoding="utf-8"))
        model["execution"]["database_write"] = boxes.get("database_write")
    rendered = _render_html(model)
    levels_path = run_dir / "niveis-runtime-pacote.json"
    if levels_path.is_file():
        levels = json.loads(levels_path.read_text(encoding="utf-8"))
        message = html.escape(str(levels.get("message", "Coleta de níveis pendente.")), quote=True)
        application_path = run_dir / "niveis-runtime-aplicacao.json"
        if application_path.is_file():
            application = json.loads(application_path.read_text(encoding="utf-8"))
            if application.get("readback") and application.get("database_write") and application.get("package_sha256") == levels.get("package_sha256"):
                message += " Atualização confirmada no banco: " + str(int(application.get("aplicadas", 0))) + " cartas."
                rendered = rendered.replace("Leitura do jogo &middot; somente leitura, nada foi escrito no banco", "Leitura do jogo &middot; atualização de níveis conferida no banco")
        rendered = rendered.replace("<main>", '<main><section><h2>Níveis reais</h2><p>' + message + '</p><p><a href="niveis-runtime.html">Conferir níveis e orçamentos por carta</a></p><p>As cartas ainda não observadas continuam pendentes. Use Atualizar níveis no extrator para gravar a captura conferida.</p></section>', 1)
    if boxes is not None:
        if boxes.get("independent_readback"):
            message = f"{boxes['boxes']} boxes e {boxes['vinculos']} vínculos atualizados e conferidos no banco. Referência: home eFHUB, cruzada com os cards físicos."
        else:
            message = boxes.get("reason") or "Atualização de boxes não confirmada."
        rendered = rendered.replace("<main>", "<main><section><h2>Boxes em andamento</h2><p>" + html.escape(str(message), quote=True) + "</p></section>", 1)
        model["manifest"]["boxes_sync"] = boxes
    html_path.write_text(rendered, encoding="utf-8")
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
