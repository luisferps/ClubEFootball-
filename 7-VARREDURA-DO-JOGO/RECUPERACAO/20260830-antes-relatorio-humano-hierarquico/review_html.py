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


SCHEMA = "clubef-result-review-html-v1"
SAMPLE_LIMIT_PER_CHECK_AND_TYPE = 50
DEFAULT_SCAN_TIMEOUT_SECONDS = 40.0
DIVERGENCE_KINDS = ("new", "removed", "altered", "repeated", "invalid")
TYPE_LABELS = {
    "new": "novo",
    "removed": "removido",
    "altered": "alterado",
    "repeated": "repetido",
    "invalid": "inválido",
}
FAMILY_LABELS = {
    "cartas": "Cartas",
    "relacoes": "Relações",
    "dimensoes": "Dimensões",
    "impetos": "Ímpetos",
    "tecnicos": "Técnicos",
    "textos": "Textos",
    "catalogos": "Catálogos",
    "metadados": "Metadados",
}
STATE_LABELS = {
    "review": "Revisão necessária",
    "observed": "Conferido sem diferenças",
    "ready": "Leitura física concluída",
    "technical_issue": "Atenção técnica",
    "error": "Erro na conferência",
}
CATALOG_LABELS = {
    "clube_novo.estilo_ia": "Catálogo de estilos de IA",
    "clube_novo.habilidade_jogo": "Catálogo de habilidades",
    "clube_novo.atributo_jogo": "Catálogo de atributos",
    "clube_novo.posicao_jogo": "Catálogo de posições",
    "clube_novo.impeto_jogo": "Catálogo de ímpetos",
    "clube_novo.texto_do_jogo": "Catálogo de textos do jogo",
    "clube_novo.tecnico_jogo": "Catálogo de técnicos",
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
_BUCKET_LINE = re.compile(r'^\s{8}"(new|removed|altered|repeated|invalid)": \[\s*$')


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
    )
    with result_path.open("rb") as handle:
        with mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as raw:
            return {key: _top_level_value(raw, key) for key in keys}


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
    for key in ("procedencia", "proveniencia"):
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


def _scan_classification_samples(result_path: Path, sample_limit: int, timeout_seconds: float) -> tuple[dict[str, dict[str, int]], list[dict[str, Any]], bool]:
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
    capture_collect = False
    complete = True

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
                if capture_collect:
                    capture_lines.append(line)
                capture_depth += _brace_delta(line)
                if capture_depth != 0:
                    continue
                assert current_kind is not None
                counts[report_key][current_kind] += 1
                if capture_collect:
                    try:
                        entry = json.loads("\n".join(capture_lines).rstrip().rstrip(","))
                    except json.JSONDecodeError:
                        entry = None
                    if isinstance(entry, dict):
                        family_key = _report_family(report_key)
                        samples.append({
                            "report": report_key,
                            "family": _family_label(family_key),
                            "family_key": family_key,
                            "scope": entry.get("escopo") or entry.get("family"),
                            "type": TYPE_LABELS[current_kind],
                            "type_key": current_kind,
                            "identity": _entry_identity(entry),
                            "detail": _entry_detail(entry),
                            "provenance": _entry_provenance(entry),
                            "raw_entry": entry,
                        })
                        key = (report_key, current_kind)
                        samples_per_bucket[key] = samples_per_bucket.get(key, 0) + 1
                capture_lines = []
                capture_collect = False
                continue
            if stripped in ("]", "],"):
                current_kind = None
                continue
            if stripped.startswith("{"):
                key = (report_key, current_kind)
                capture_collect = samples_per_bucket.get(key, 0) < sample_limit
                capture_depth = _brace_delta(line)
                capture_lines = [line] if capture_collect else []
                if capture_depth == 0:
                    counts[report_key][current_kind] += 1
                    if capture_collect:
                        try:
                            entry = json.loads(line.rstrip().rstrip(","))
                        except json.JSONDecodeError:
                            entry = None
                        if isinstance(entry, dict):
                            family_key = _report_family(report_key)
                            samples.append({
                                "report": report_key,
                                "family": _family_label(family_key),
                                "family_key": family_key,
                                "scope": entry.get("escopo") or entry.get("family"),
                                "type": TYPE_LABELS[current_kind],
                                "type_key": current_kind,
                                "identity": _entry_identity(entry),
                                "detail": _entry_detail(entry),
                                "provenance": _entry_provenance(entry),
                                "raw_entry": entry,
                            })
                            samples_per_bucket[key] = samples_per_bucket.get(key, 0) + 1
                    capture_lines = []
                    capture_collect = False
    return counts, samples, complete


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


def _family_summaries(header: dict[str, Any], report_counts: dict[str, dict[str, int]], complete: bool) -> list[dict[str, Any]]:
    raw_families = header.get("families") if isinstance(header.get("families"), dict) else {}
    comparisons = header.get("comparisons") if isinstance(header.get("comparisons"), dict) else {}
    report_by_label: dict[str, list[str]] = {}
    for report in report_counts:
        report_by_label.setdefault(_family_label(_report_family(report)), []).append(report)
    order = list(raw_families) + [label for label in report_by_label if label not in raw_families]
    summaries: list[dict[str, Any]] = []
    for label in order:
        source = raw_families.get(label) if isinstance(raw_families.get(label), dict) else {}
        totals = {kind: 0 for kind in DIVERGENCE_KINDS}
        reports = report_by_label.get(label, [])
        for report in reports:
            for kind in DIVERGENCE_KINDS:
                totals[kind] += int((report_counts.get(report) or {}).get(kind, 0))
        comparison = comparisons.get(label) if isinstance(comparisons.get(label), dict) else {}
        total = sum(totals.values())
        state = str(source.get("state") or "observed")
        if not complete:
            detail = "Leitura parcial do resultado técnico; contagens de divergência podem estar incompletas."
        elif total == 0 and state != "technical_issue":
            detail = "Nenhuma divergência classificada nesta família."
        elif state == "technical_issue":
            detail = "Há uma pendência técnica a revisar; consulte os blocos classificados abaixo."
        else:
            detail = f"{total} divergência(s) classificada(s) por chave e procedência."
        summaries.append({
            "family": label,
            "state": state,
            "counts": totals,
            "reports": reports,
            "classification_complete": comparison.get("classification_complete"),
            "technical_integrity": comparison.get("technical_integrity"),
            "exact_match": comparison.get("exact_match"),
            "detail": detail,
        })
    return summaries


def _build_model(result_path: Path, sample_limit: int, timeout_seconds: float) -> dict[str, Any]:
    header = _read_result_header(result_path)
    report_counts, samples, scan_complete = _scan_classification_samples(result_path, sample_limit, timeout_seconds)
    run_dir = result_path.parent
    result_info = result_path.stat()
    family_summary = _family_summaries(header, report_counts, scan_complete)
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
            "sample_limit_per_check_and_type": sample_limit,
            "scan_complete": scan_complete,
            "technical_json_preserved": True,
        },
        "divergence_samples": samples,
        "review_gate": header.get("review_gate") if isinstance(header.get("review_gate"), dict) else {},
        "artifacts": _artifact_references(run_dir),
    }
    model["manifest"] = {
        "schema": "clubef-execution-manifest-v1",
        "generated_at": model["generated_at"],
        "execution": execution,
        "result": model["source_result"],
        "program": model["program"],
        "contract": model["contract"],
        "sources": model["sources"],
        "families": family_summary,
        "review_gate": model["review_gate"],
        "database_write": model["database_write"],
        "artifacts": model["artifacts"],
    }
    return model


def _tag(value: Any) -> str:
    return re.sub(r"[^a-z0-9_-]", "-", str(value).lower())


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
    html_path.write_text(_render_html(model), encoding="utf-8")
    model["artifacts"] = _artifact_references(run_dir)
    model["manifest"]["artifacts"] = model["artifacts"]
    manifest_path.write_text(json.dumps(model["manifest"], ensure_ascii=False, indent=2), encoding="utf-8")
    model["artifacts"] = _artifact_references(run_dir)
    model["manifest"]["artifacts"] = model["artifacts"]
    html_path.write_text(_render_html(model), encoding="utf-8")
    return {
        "review_html_path": str(html_path),
        "manifest_path": str(manifest_path),
        "sample_count": len(model["divergence_samples"]),
        "classified_total": model["divergence_summary"]["total_classified"],
        "scan_complete": model["divergence_summary"]["scan_complete"],
        "database_write": False,
    }
