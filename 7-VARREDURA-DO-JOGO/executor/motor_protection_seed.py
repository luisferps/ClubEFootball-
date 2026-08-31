"""Materializa, sem banco, a prontidão física no contrato dos motores.

O arquivo de saída é NDJSON para que as 43 mil cartas possam ser produzidas e
consumidas em fluxo. Cada linha contém exatamente os onze componentes aceitos
por ``clube_novo.registrar_completude_motor_v1``. Este módulo nunca abre uma
conexão e nunca conhece credenciais; a vinculação do ``aplicacao_id`` pertence
ao passo explícito de aplicação no banco.
"""
from __future__ import annotations

import argparse
import codecs
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from itertools import zip_longest
from pathlib import Path
from typing import Any, Iterator

import card_completeness


SCHEMA = "clubef-completude-motores-seed-v1"
ENVELOPE_SCHEMA = "clubef-completude-motores-seed-envelope-v1"
RULE_VERSION = "completude-motores-carta-v1"
REQUIRED_COMPONENTS = (
    "dados_basicos",
    "dimensoes",
    "atributos",
    "corpo",
    "posicoes",
    "posicao_principal",
    "habilidades",
    "estilos_ia",
    "pes",
    "playstyles",
    "impetos",
)
_ARRAY_MARKER = re.compile(rb'"(?P<key>[^"\\]+)"\s*:\s*\[')
_MISSING = object()


class SeedError(RuntimeError):
    """Entrada não selada ou prova física insuficiente."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_value(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _array_offset(path: Path, key: str | None) -> int:
    """Retorna o byte logo depois do ``[`` sem carregar o JSON inteiro."""
    if key is None:
        with path.open("rb") as stream:
            offset = 0
            while chunk := stream.read(64 * 1024):
                for index, value in enumerate(chunk):
                    if chr(value).isspace():
                        continue
                    if value != ord("["):
                        raise SeedError(f"{path.name}: lista JSON esperada")
                    return offset + index + 1
                offset += len(chunk)
        raise SeedError(f"{path.name}: arquivo vazio")

    wanted = key.encode("utf-8")
    carry = b""
    absolute = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            block = carry + chunk
            for match in _ARRAY_MARKER.finditer(block):
                if match.group("key") == wanted:
                    return absolute - len(carry) + match.end()
            carry = block[-256:]
            absolute += len(chunk)
    raise SeedError(f'{path.name}: lista "{key}" não encontrada')


def iter_json_array(path: Path, key: str | None = None, chunk_size: int = 256 * 1024) -> Iterator[Any]:
    """Itera uma lista JSON de modo incremental usando apenas a biblioteca padrão."""
    decoder = json.JSONDecoder()
    offset = _array_offset(path, key)
    with path.open("rb") as raw:
        raw.seek(offset)
        utf8 = codecs.getincrementaldecoder("utf-8")()

        def read_text() -> str:
            data = raw.read(chunk_size)
            return utf8.decode(data, final=not data)

        buffer = ""
        position = 0
        ended = False
        while not ended:
            if position >= len(buffer):
                incoming = read_text()
                if not incoming:
                    raise SeedError(f"{path.name}: lista JSON interrompida")
                buffer = buffer[position:] + incoming
                position = 0

            while True:
                while position < len(buffer) and (buffer[position].isspace() or buffer[position] == ","):
                    position += 1
                if position < len(buffer):
                    break
                incoming = read_text()
                if not incoming:
                    raise SeedError(f"{path.name}: lista JSON sem fechamento")
                buffer = incoming
                position = 0

            if buffer[position] == "]":
                ended = True
                continue

            while True:
                try:
                    value, end = decoder.raw_decode(buffer, position)
                    position = end
                    yield value
                    if position > chunk_size:
                        buffer = buffer[position:]
                        position = 0
                    break
                except json.JSONDecodeError:
                    incoming = read_text()
                    if not incoming:
                        raise SeedError(f"{path.name}: item JSON inválido ou incompleto")
                    buffer += incoming


def load_prefix(path: Path, key: str) -> dict[str, Any]:
    """Lê somente o cabeçalho de um objeto cujo grande array é o último campo."""
    offset = _array_offset(path, key)
    with path.open("rb") as stream:
        prefix = stream.read(offset - 1).decode("utf-8")
    try:
        value = json.loads(prefix + "null}")
    except json.JSONDecodeError as exc:
        raise SeedError(f"{path.name}: cabeçalho antes de {key} não é selável") from exc
    if not isinstance(value, dict):
        raise SeedError(f"{path.name}: objeto de cabeçalho esperado")
    return value


def _load_object(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise SeedError(f"{path.name}: JSON não pôde ser lido") from exc
    if not isinstance(value, dict):
        raise SeedError(f"{path.name}: objeto JSON esperado")
    return value


def _source_provenance(
    *,
    component: str,
    card_id: str,
    ordinal: int,
    artifact_name: str,
    artifact_sha256: str,
    source_files: dict[str, Any],
    contract_seal: dict[str, Any],
    physical_fields: list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    provenance: dict[str, Any] = {
        "artefato": artifact_name,
        "artefato_sha256": artifact_sha256,
        "card_id": card_id,
        "registro_ordinal": ordinal,
        "campos_fisicos": physical_fields,
        "componente": component,
        "contrato_id": contract_seal.get("contrato_id"),
        "versao_contrato": contract_seal.get("versao_contrato"),
        "arquivos_fonte_fingerprint_sha256": _sha256_value(source_files),
        "player_bin_atual_sha256": source_files.get("dt870_updated:Player.bin"),
    }
    if extra:
        provenance.update(extra)
    return provenance


def _validate_readiness_component(name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SeedError(f"componente local ausente: {name}")
    state = value.get("estado")
    if state not in (
        "conferido_com_valor",
        "conferido_sem_valor",
        "conferido_sem_vinculo_atual",
        "nao_conferido",
        "leitura_com_problema",
    ):
        raise SeedError(f"estado local desconhecido em {name}: {state!r}")
    quantity = value.get("quantidade")
    if state == "conferido_com_valor" and (isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0):
        raise SeedError(f"{name}: leitura com valor sem quantidade positiva")
    if state in ("conferido_sem_valor",) and quantity != 0:
        raise SeedError(f"{name}: ausência confirmada sem zero explícito")
    return value


def _component(
    name: str,
    readiness_component: dict[str, Any],
    provenance: dict[str, Any],
    *,
    quantity: int | None = None,
    resolution: str | None = None,
    force_state: str | None = None,
    evidence: dict[str, Any] | None = None,
    problem: str | None = None,
    operator_block: dict[str, Any] | None = None,
) -> dict[str, Any]:
    local_state = readiness_component["estado"]
    state = force_state or ("conferido_com_valor" if local_state == "conferido_sem_vinculo_atual" else local_state)
    complete = state in ("conferido_com_valor", "conferido_sem_valor")
    resolved = resolution or ("resolvido" if complete else "nao_resolvido")
    output: dict[str, Any] = {
        "componente": name,
        "estado_coleta": state,
        "estado_resolucao": resolved,
        "apto_motor": bool(complete and resolved != "nao_resolvido" and operator_block is None),
        "proveniencia": provenance,
        "evidencia": evidence or {},
    }
    resolved_quantity = readiness_component.get("quantidade") if quantity is None else quantity
    if state in ("conferido_com_valor", "conferido_sem_valor"):
        output["quantidade_valores"] = resolved_quantity
    if not complete:
        output["problema"] = problem or readiness_component.get("motivo") or "prova física insuficiente"
    if operator_block is not None:
        output["evidencia"] = dict(output["evidencia"])
        previous_decision = output["evidencia"].get("decisao_motor")
        if isinstance(previous_decision, dict):
            operator_block = dict(operator_block)
            operator_block["contexto_decisao_anterior"] = previous_decision
        output["evidencia"]["decisao_motor"] = operator_block
    return output


def _manual_targets(mark: Any) -> tuple[set[str], dict[str, Any] | None]:
    if mark is None:
        return set(), None
    if not isinstance(mark, dict) or mark.get("estado") != "incompleto_confirmado":
        raise SeedError("marcação manual inválida na prontidão selada")
    reason = str(mark.get("motivo") or "").strip()
    if not reason:
        raise SeedError("marcação manual sem motivo")
    aliases = {"estilos_de_jogo": "playstyles", "vinculos": "dimensoes"}
    requested = {
        aliases.get(str(item), str(item))
        for item in (mark.get("componentes") or [])
        if aliases.get(str(item), str(item)) in REQUIRED_COMPONENTS
    }
    if not requested:
        requested = {"dados_basicos"}
    decision = {
        "tipo": "incompleto_confirmado_operador",
        "motivo": reason,
        "marcado_em": mark.get("marcado_em"),
        "fingerprint_marcado": mark.get("fingerprint_marcado"),
        "insumos_mudaram_desde_marcacao": bool(mark.get("insumos_mudaram_desde_marcacao")),
        "evidencia_operador": mark.get("evidencia"),
    }
    return requested, decision


def materialize_components(
    card: dict[str, Any],
    dimension: dict[str, Any],
    readiness_row: dict[str, Any],
    *,
    ordinal: int,
    artifact_hashes: dict[str, str],
    source_files: dict[str, Any],
    contract_seal: dict[str, Any],
) -> list[dict[str, Any]]:
    card_id = str(card.get("card_id") or "")
    local = readiness_row.get("componentes")
    if not isinstance(local, dict):
        raise SeedError(f"{card_id}: prontidão sem componentes")
    for name in (
        "dados_basicos", "atributos", "corpo", "posicoes", "habilidades",
        "estilos_ia", "estilos_de_jogo", "impetos", "vinculos",
    ):
        _validate_readiness_component(name, local.get(name))

    targets, manual_decision = _manual_targets(readiness_row.get("marcacao_operador"))

    def provenance(name: str, artifact: str, fields: list[str], extra: dict[str, Any] | None = None) -> dict[str, Any]:
        return _source_provenance(
            component=name,
            card_id=card_id,
            ordinal=ordinal,
            artifact_name=artifact,
            artifact_sha256=artifact_hashes[artifact],
            source_files=source_files,
            contract_seal=contract_seal,
            physical_fields=fields,
            extra=extra,
        )

    def block(name: str) -> dict[str, Any] | None:
        return manual_decision if name in targets else None

    output: list[dict[str, Any]] = []
    output.append(_component("dados_basicos", local["dados_basicos"], provenance(
        "dados_basicos", "cartas-fisicas-canonicas.json",
        ["card_id", "name", "height", "weight", "age", "form", "injury", "tipo", "roda_motor"],
    ), operator_block=block("dados_basicos")))

    dim_local = local["vinculos"]
    orphan = dim_local["estado"] == "conferido_sem_vinculo_atual"
    dim_evidence: dict[str, Any] = {
        "codigo_nacionalidade": dimension.get("codigo_nacionalidade"),
        "codigo_clube_bruto": dimension.get("codigo_clube"),
        "codigo_liga": dimension.get("codigo_liga"),
        "tipo_carta_id": dimension.get("tipo_carta_id"),
    }
    if orphan:
        pending = dim_local.get("pendencia_conhecida")
        if not isinstance(pending, dict) or pending.get("tipo") != "clube_sem_vinculo_atual_por_licenca":
            raise SeedError(f"{card_id}: órfão de clube sem decisão local explícita")
        dim_evidence["decisao_motor"] = {
            "tipo": "orfao_clube_atual_nao_bloqueante",
            "motivo": str(pending.get("significado") or pending.get("acao") or "código bruto preservado; clube não existe no catálogo atual"),
            "codigo_clube_bruto": dimension.get("codigo_clube"),
            "acao": "preservar o código bruto e não inventar vínculo substituto",
        }
    dim_component = _component(
        "dimensoes", dim_local,
        provenance("dimensoes", "dimensoes-fisicas.json", [
            "codigo_nacionalidade", "codigo_clube", "codigo_liga", "tipo_carta_id", "pode_rodar_vinculos",
        ], {"registro_vinculos_jogo": dimension.get("registro_vinculos_jogo")}),
        resolution="orfao_catalogo_atual" if orphan else None,
        evidence=dim_evidence,
        operator_block=block("dimensoes"),
    )
    output.append(dim_component)

    for name, fields in (
        ("atributos", ["attrs"]),
        ("corpo", ["corpo"]),
        ("posicoes", ["aptitudes"]),
        ("habilidades", ["skills", "habilidades_fisicas"]),
        ("estilos_ia", ["ai_styles", "estilos_ia_fisicos"]),
    ):
        proof_rows = card.get(fields[-1]) if name in ("habilidades", "estilos_ia") else None
        extra = {}
        if isinstance(proof_rows, list) and proof_rows:
            extra["provas_fisicas_quantidade"] = len(proof_rows)
            extra["provas_fisicas_fingerprint_sha256"] = _sha256_value(proof_rows)
        elif name in ("habilidades", "estilos_ia"):
            # A lista vazia só é aceita porque o estado selado confirma que o
            # campo físico correspondente foi efetivamente lido.
            extra["ausencia_confirmada_pelo_leitor"] = True
        output.append(_component(
            name, local[name], provenance(name, "cartas-fisicas-canonicas.json", fields, extra),
            operator_block=block(name),
        ))

    pos_local = local["posicoes"]
    position = card.get("position")
    if pos_local["estado"] in ("conferido_com_valor", "conferido_sem_valor") and isinstance(position, str) and position.strip():
        pos_primary_state = "conferido_com_valor"
        pos_primary_qty = 1
        pos_problem = None
    else:
        pos_primary_state = "nao_conferido"
        pos_primary_qty = None
        pos_problem = "posição principal sem prova física suficiente"
    primary_readiness = {"estado": pos_primary_state, "quantidade": pos_primary_qty, "motivo": pos_problem}
    output.append(_component(
        "posicao_principal", primary_readiness,
        provenance("posicao_principal", "cartas-fisicas-canonicas.json", ["position"]),
        force_state=pos_primary_state, quantity=pos_primary_qty, problem=pos_problem,
        evidence={"posicao_principal": position} if pos_primary_state == "conferido_com_valor" else {},
        operator_block=block("posicao_principal"),
    ))

    foot_values = (card.get("foot", _MISSING), card.get("weak_foot_usage", _MISSING), card.get("weak_foot_accuracy", _MISSING))
    foot_valid = (
        isinstance(foot_values[0], str) and bool(foot_values[0].strip())
        and all(isinstance(value, int) and not isinstance(value, bool) for value in foot_values[1:])
        and local["dados_basicos"]["estado"] == "conferido_com_valor"
    )
    foot_readiness = {
        "estado": "conferido_com_valor" if foot_valid else "nao_conferido",
        "quantidade": 3 if foot_valid else None,
        "motivo": None if foot_valid else "pé e uso/precisão do pé fraco sem prova física completa",
    }
    output.append(_component(
        "pes", foot_readiness,
        provenance("pes", "cartas-fisicas-canonicas.json", ["foot", "weak_foot_usage", "weak_foot_accuracy"]),
        evidence={"pe": card.get("foot"), "uso_pe_fraco": card.get("weak_foot_usage"), "precisao_pe_fraco": card.get("weak_foot_accuracy")} if foot_valid else {},
        operator_block=block("pes"),
    ))

    play_local = local["estilos_de_jogo"]
    play_evidence = {
        "estilo_principal_id": card.get("primary_style_id"),
        "estilo_principal_desconhecido": card.get("primary_style_unknown"),
        "indice_estilo_defensivo": card.get("defensive_style_id"),
        "estilo_defensivo_confirmado": card.get("defensive_style_confirmed"),
    }
    defensive_proof = play_local.get("prova_indice_defensivo")
    if defensive_proof is not None:
        if not isinstance(defensive_proof, dict) or defensive_proof.get("indice") != card.get("defensive_style_id") or defensive_proof.get("id_jogo") is None:
            raise SeedError(f"{card_id}: índice defensivo sem resolução física coerente")
        play_evidence["resolucao_estilo_defensivo"] = defensive_proof
    output.append(_component(
        "playstyles", play_local,
        provenance("playstyles", "cartas-fisicas-canonicas.json", [
            "position", "primary_style_id", "primary_style_unknown", "defensive_style_id", "defensive_style_confirmed",
        ], {"catalogo": "metadados-fisicos.json/catalogs.playstyles"}),
        evidence=play_evidence,
        operator_block=block("playstyles"),
    ))

    impetus_extra: dict[str, Any] = {}
    if local["impetos"]["estado"] == "conferido_sem_valor":
        impetus_extra["ausencia_confirmada_pelo_leitor"] = True
    output.append(_component(
        "impetos", local["impetos"],
        provenance("impetos", "cartas-fisicas-canonicas.json", ["booster_primary", "booster_conditional"], impetus_extra),
        evidence={"slot_primario": card.get("booster_primary"), "slot_condicional": card.get("booster_conditional")},
        operator_block=block("impetos"),
    ))

    by_name = {row["componente"]: row for row in output}
    if set(by_name) != set(REQUIRED_COMPONENTS) or len(output) != len(REQUIRED_COMPONENTS):
        raise SeedError(f"{card_id}: conjunto dos onze componentes divergente")
    return [by_name[name] for name in REQUIRED_COMPONENTS]


def _atomic_json(path: Path, value: Any) -> None:
    temp = path.with_name(path.name + ".novo")
    with temp.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(_canonical_json(value))
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def build_seed(run_dir: Path, output_dir: Path, *, generated_at: str | None = None) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    output_dir = output_dir.resolve()
    paths = {
        "cartas-fisicas-canonicas.json": run_dir / "cartas-fisicas-canonicas.json",
        "dimensoes-fisicas.json": run_dir / "dimensoes-fisicas.json",
        "metadados-fisicos.json": run_dir / "metadados-fisicos.json",
        "prontidao-motores.json": run_dir / "prontidao-motores.json",
        "resultado.json": run_dir / "resultado.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise SeedError("artefatos obrigatórios ausentes: " + ", ".join(missing))

    result = _load_object(paths["resultado.json"])
    readiness_header = load_prefix(paths["prontidao-motores.json"], "cards")
    dimension_header = load_prefix(paths["dimensoes-fisicas.json"], "cards")
    metadata = _load_object(paths["metadados-fisicos.json"])
    if result.get("state") != "completed" or result.get("database_write") is not False:
        raise SeedError("resultado não é uma execução concluída e somente leitura")
    if readiness_header.get("schema") != "clubef-prontidao-motores-v1" or readiness_header.get("database_write") is not False:
        raise SeedError("prontidão local inválida ou não somente leitura")
    contract_seal = result.get("contract_seal")
    if not isinstance(contract_seal, dict) or readiness_header.get("contract_seal") != contract_seal:
        raise SeedError("selo do resultado diverge da prontidão")
    source_seal = readiness_header.get("source_seal")
    family_seals = result.get("family_seals")
    if not isinstance(source_seal, dict) or not isinstance(family_seals, dict):
        raise SeedError("selos de família ausentes")
    for family, fingerprint in (source_seal.get("family_fingerprints") or {}).items():
        if (family_seals.get(family) or {}).get("fingerprint_familia") != fingerprint:
            raise SeedError(f"selo de família divergente: {family}")

    artifact_hashes = {name: sha256_file(path) for name, path in paths.items()}
    source_files = dimension_header.get("source_files")
    if not isinstance(source_files, dict) or not source_files.get("dt870_updated:Player.bin"):
        raise SeedError("dimensões sem hash físico do Player.bin atual")

    catalogs = metadata.get("catalogs")
    impetus_rows = ((catalogs or {}).get("impetos") or {}).get("records") if isinstance(catalogs, dict) else None
    playstyle_rows = ((catalogs or {}).get("playstyles") or {}).get("records") if isinstance(catalogs, dict) else None
    if not isinstance(impetus_rows, list) or not isinstance(playstyle_rows, list):
        raise SeedError("metadados sem catálogos físicos de Ímpetos/playstyles")
    impetus_catalog = {str(row.get("id")): row for row in impetus_rows if isinstance(row, dict) and row.get("id") is not None}
    playstyle_catalog = card_completeness._build_playstyle_catalog(playstyle_rows, None)

    dimensions: dict[str, dict[str, Any]] = {}
    for row in iter_json_array(paths["dimensoes-fisicas.json"], "cards"):
        if not isinstance(row, dict) or not str(row.get("card_id") or ""):
            raise SeedError("dimensões contêm linha sem card_id")
        card_id = str(row["card_id"])
        if card_id in dimensions:
            raise SeedError(f"dimensão repetida: {card_id}")
        dimensions[card_id] = row

    output_dir.mkdir(parents=True, exist_ok=True)
    seed_path = output_dir / "seed-completude-motores.ndjson"
    temp_seed = seed_path.with_name(seed_path.name + ".novo")
    digest = hashlib.sha256()
    counters = {
        "envelopes": 0,
        "componentes": 0,
        "aptos_por_cobertura_local": 0,
        "bloqueados_por_marcacao_manual": 0,
        "dimensoes_orfas_nao_bloqueantes": 0,
        "playstyles_defensivos_presentes": 0,
        "playstyles_defensivos_resolvidos": 0,
        "playstyles_defensivos_sem_resolucao": 0,
    }
    observed_states: dict[str, dict[str, int]] = {name: {} for name in REQUIRED_COMPONENTS}
    seen: set[str] = set()

    card_rows = iter_json_array(paths["cartas-fisicas-canonicas.json"])
    readiness_rows = iter_json_array(paths["prontidao-motores.json"], "cards")
    try:
        with temp_seed.open("wb") as stream:
            for ordinal, pair in enumerate(zip_longest(card_rows, readiness_rows, fillvalue=_MISSING), start=1):
                card, ready = pair
                if card is _MISSING or ready is _MISSING:
                    raise SeedError("quantidade de cartas diverge entre leitura física e prontidão")
                if not isinstance(card, dict) or not isinstance(ready, dict):
                    raise SeedError(f"linha {ordinal}: envelope de entrada inválido")
                card_id = str(card.get("card_id") or "")
                if not card_id or card_id != str(ready.get("card_id") or ""):
                    raise SeedError(f"linha {ordinal}: identidade diverge entre leitura e prontidão")
                if card_id in seen:
                    raise SeedError(f"carta repetida: {card_id}")
                seen.add(card_id)
                dimension = dimensions.get(card_id)
                if dimension is None:
                    raise SeedError(f"{card_id}: sem fotografia de dimensões")

                recomputed = card_completeness.evaluate_card(
                    card,
                    dimension=dimension,
                    impetus_catalog=impetus_catalog,
                    playstyle_catalog=playstyle_catalog,
                )
                if recomputed.get("input_fingerprint") != ready.get("input_fingerprint"):
                    raise SeedError(f"{card_id}: prontidão não corresponde aos insumos físicos atuais")
                if recomputed.get("componentes") != ready.get("componentes"):
                    raise SeedError(f"{card_id}: componentes da prontidão não correspondem à releitura local")

                components = materialize_components(
                    card, dimension, ready,
                    ordinal=ordinal,
                    artifact_hashes=artifact_hashes,
                    source_files=source_files,
                    contract_seal=contract_seal,
                )
                component_fp = _sha256_value(components)
                envelope = {
                    "schema": ENVELOPE_SCHEMA,
                    "regra_versao": RULE_VERSION,
                    "card_id": card_id,
                    "input_fingerprint_local_sha256": ready.get("input_fingerprint"),
                    "componentes_fingerprint_sha256": component_fp,
                    "aplicacao_id_binding": "aplicacao_id_criado_pelo_instalador_na_mesma_transacao_do_seed",
                    "rpc": "clube_novo.registrar_completude_motor_v1(text,bigint,jsonb)",
                    "database_write": False,
                    "componentes": components,
                }
                line = (_canonical_json(envelope) + "\n").encode("utf-8")
                stream.write(line)
                digest.update(line)

                counters["envelopes"] += 1
                counters["componentes"] += len(components)
                counters["aptos_por_cobertura_local"] += int(all(row["apto_motor"] for row in components))
                counters["bloqueados_por_marcacao_manual"] += int(ready.get("marcacao_operador") is not None)
                counters["dimensoes_orfas_nao_bloqueantes"] += int(
                    next(row for row in components if row["componente"] == "dimensoes")["estado_resolucao"] == "orfao_catalogo_atual"
                )
                defensive = card.get("defensive_style_id")
                defensive_present = isinstance(defensive, int) and not isinstance(defensive, bool) and defensive != 0
                counters["playstyles_defensivos_presentes"] += int(defensive_present)
                proof = (ready.get("componentes") or {}).get("estilos_de_jogo", {}).get("prova_indice_defensivo")
                resolved = defensive_present and isinstance(proof, dict) and proof.get("indice") == defensive and proof.get("id_jogo") is not None
                counters["playstyles_defensivos_resolvidos"] += int(resolved)
                counters["playstyles_defensivos_sem_resolucao"] += int(defensive_present and not resolved)
                for item in components:
                    bucket = observed_states[item["componente"]]
                    state = item["estado_coleta"]
                    bucket[state] = bucket.get(state, 0) + 1
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_seed, seed_path)
    except Exception:
        try:
            temp_seed.unlink()
        except FileNotFoundError:
            pass
        raise

    expected = (readiness_header.get("summary") or {}).get("cards")
    if expected != counters["envelopes"]:
        seed_path.unlink(missing_ok=True)
        raise SeedError(f"resumo selado esperava {expected} cartas; materializadas {counters['envelopes']}")
    if counters["playstyles_defensivos_sem_resolucao"]:
        seed_path.unlink(missing_ok=True)
        raise SeedError("há playstyle defensivo presente sem resolução por índice")

    generated = generated_at or datetime.now(timezone.utc).isoformat()
    producer_path = Path(__file__).resolve()
    producer_sha256 = sha256_file(producer_path)
    installer_identity = {
        "run_dir": str(run_dir),
        "contrato_id": contract_seal.get("contrato_id"),
        "fingerprint_contrato_sha256": contract_seal.get("fingerprint_contrato_sha256"),
        "fingerprint_fontes_sha256": contract_seal.get("fingerprint_fontes_sha256"),
        "fingerprint_catalogos_sha256": contract_seal.get("fingerprint_catalogos_sha256"),
        "artefatos_sha256": artifact_hashes,
        "pacote_seed_sha256": digest.hexdigest(),
    }
    installer_idempotency_key_sha256 = _sha256_value(installer_identity)
    package_identity = _sha256_value({
        "schema": SCHEMA,
        "regra": RULE_VERSION,
        "contract_seal": contract_seal,
        "artifact_hashes": artifact_hashes,
        "producer_sha256": producer_sha256,
        "seed_sha256": digest.hexdigest(),
    })
    manifest = {
        "schema": SCHEMA,
        "versao": 1,
        "pacote_id": f"completude-motores-{package_identity[:24]}",
        "gerado_em": generated,
        "database_write": False,
        "contem_segredos": False,
        "modo": "snapshot_integral_incremental_em_fluxo",
        "gerador": {"arquivo": str(producer_path), "sha256": producer_sha256},
        "estado_materializacao_banco": "preparado_para_instalador_explicito_sem_application_id_previo",
        "publicacao_independente": True,
        "destino_preparado": "clube_novo.registrar_completude_motor_v1(text,bigint,jsonb)",
        "aplicacao_id": {
            "valor_no_seed": None,
            "binding_obrigatorio": "aplicacao_id_criado_pelo_instalador_na_mesma_transacao_do_seed",
            "regra": "o instalador explícito deve registrar a execução aceita e a aplicação aplicada antes das RPCs, tudo na mesma transação",
        },
        "vinculo_instalador": {
            "application_id_previo_proibido": True,
            "idempotency_key_sha256": installer_idempotency_key_sha256,
            "idempotency_key_material": installer_identity,
            "pacote_sha256": digest.hexdigest(),
            "precondicoes": [
                "registrar execução local como aceita com os hashes deste manifesto",
                "registrar aplicação deste pacote como aplicada na mesma transação",
                "usar o aplicacao_id retornado somente nas RPCs desta transação",
                "rollback integral se qualquer RPC ou readback falhar",
            ],
        },
        "execucao_local": {
            "run_dir": str(run_dir),
            "resultado_state": result.get("state"),
            "launcher_protocol_version": result.get("launcher_protocol_version"),
            "physical_reader": result.get("physical_reader"),
            "resultado_database_write": result.get("database_write"),
        },
        "componentes_obrigatorios": list(REQUIRED_COMPONENTS),
        "contract_seal": contract_seal,
        "source_seal": source_seal,
        "arquivos_fisicos_sha256": source_files,
        "fontes": {
            name: {"arquivo": str(path), "sha256": artifact_hashes[name]}
            for name, path in paths.items()
        },
        "seed": {
            "arquivo": str(seed_path),
            "formato": "ndjson; um envelope por carta",
            "sha256": digest.hexdigest(),
            "bytes": seed_path.stat().st_size,
        },
        "contagens": counters,
        "estados_por_componente": observed_states,
        "validacoes": {
            "resultado_concluido_somente_leitura": True,
            "selo_prontidao_igual_resultado": True,
            "fingerprints_familias_conferidos": True,
            "fingerprint_local_recalculado_por_carta": True,
            "onze_componentes_exatos_por_envelope": True,
            "ausencia_confirmada_conta_como_completa": True,
            "null_lista_vazia_zero_sem_procedencia_proibidos": True,
            "orfao_clube_decisao_explicita": True,
            "marcacao_manual_bloqueia_aptidao": True,
            "playstyle_defensivo_resolvido_por_indice": counters["playstyles_defensivos_sem_resolucao"] == 0,
        },
    }
    manifest["manifest_payload_sha256"] = _sha256_value(manifest)
    manifest_path = output_dir / "manifest-seed-completude-motores.json"
    _atomic_json(manifest_path, manifest)
    return {**manifest, "manifest_path": str(manifest_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepara offline o seed de proteção dos motores.")
    parser.add_argument("--run-dir", type=Path, required=True, help="pasta de uma execução concluída")
    parser.add_argument("--output-dir", type=Path, required=True, help="pasta nova para seed e manifesto")
    parser.add_argument("--generated-at", help="data ISO fixa para teste reproduzível")
    args = parser.parse_args(argv)
    try:
        manifest = build_seed(args.run_dir, args.output_dir, generated_at=args.generated_at)
    except SeedError as exc:
        print(f"ERRO FECHADO: {exc}", file=sys.stderr)
        return 2
    print(_canonical_json({
        "state": "seed_preparado_offline",
        "database_write": False,
        "manifest": manifest["manifest_path"],
        "seed": manifest["seed"]["arquivo"],
        "contagens": manifest["contagens"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
