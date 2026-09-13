"""Extrai as boxes carregadas pelo próprio eFootball e publica no clube_novo.

A origem é a resposta convertida de CmdGetMyclubAgentlist mantida pelo jogo em
memória.  PlayerVariationDetail.bin não participa deste fluxo: aquele arquivo
descreve a variação individual da carta, não o agrupamento comercial da box.
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
import uuid

import card_levels_runtime

SCHEMA = "clubef-boxes-jogo-runtime-v1"
READER_VERSION = "boxes-cmd-get-myclub-agentlist-detalhes-v2"
SOURCE = "jogo:CmdGetMyclubAgentlist"
AGENT_STRIDE = 0x238
AGENT_ID_OFFSET = 0x08
TITLE_OFFSET = 0x68
START_DATE_OFFSET = 0x1C
EXPIRATION_DATE_OFFSET = 0x24
LISTS = (("pickup_list", 0xE8, 0xF8),
         ("banner_a_pickup_list", 0x200, 0xF0),
         ("banner_c_pickup_list", 0x218, 0xF0))


def _read_pointer(reader: Any, address: int, purpose: str) -> tuple[int, bytes]:
    raw = reader.read(address, 8, purpose)
    return struct.unpack("<Q", raw)[0], raw


def _read_msvc_string(reader: Any, address: int, purpose: str) -> tuple[str, bytes]:
    """Lê std::string MSVC x64 (SSO de 16 bytes) com limites estritos."""
    raw = reader.read(address, 32, purpose + "_objeto")
    length, capacity = struct.unpack_from("<QQ", raw, 16)
    if length > 2048 or capacity > 65535 or capacity < length:
        raise ValueError("Texto da box fora dos limites do objeto do jogo.")
    if capacity < 16:
        encoded = raw[:length]
    else:
        pointer = struct.unpack_from("<Q", raw, 0)[0]
        if pointer < 0x10000 or pointer >= 0x7FFFFFFFFFFF:
            raise ValueError("Ponteiro do título da box fora do espaço de usuário.")
        encoded = reader.read(pointer, int(length), purpose + "_conteudo") if length else b""
    try:
        value = encoded.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError("Título da box não é UTF-8 válido.") from error
    value = re.sub(r"\s+", " ", value).strip()
    if not value or any(ord(char) < 32 for char in value):
        raise ValueError("Título comercial da box está vazio ou contém controle.")
    return value, raw


def read_loaded_boxes(reader: Any, physical_ids: set[str], *, capture_id: str,
                      captured_at: str, catalog_only: bool = False) -> dict[str, Any]:
    """Parser testável do vetor convertido de CmdGetMyclubAgentlist."""
    base = reader.base
    g, g_raw = _read_pointer(reader, base + card_levels_runtime.ROOT_RVA, "raiz_cartas_boxes")
    if not g:
        raise card_levels_runtime.LevelsUnavailable(
            "colecoes_nao_carregadas", "O jogo está aberto, mas ainda não carregou a lista de boxes."
        )
    manager, manager_raw = _read_pointer(reader, g + 0x28, "gerenciador_boxes")
    if not manager:
        raise card_levels_runtime.LevelsUnavailable(
            "colecoes_nao_carregadas", "O jogo ainda não carregou o gerenciador das boxes."
        )
    owner, owner_raw = _read_pointer(reader, manager + 0x20, "dono_lista_agentes")
    if not owner:
        raise card_levels_runtime.LevelsUnavailable(
            "boxes_nao_carregadas", "Abra a área de contratos do eFootball para carregar as boxes."
        )
    outer = reader.read(owner, 24, "cabecalho_lista_agentes")
    begin, _, _, count = card_levels_runtime.vector_bounds(outer, AGENT_STRIDE, 1000)
    if count == 0:
        raise card_levels_runtime.LevelsUnavailable(
            "boxes_nao_carregadas", "A lista de agentes está vazia; abra a área de contratos e repita."
        )

    boxes: list[dict[str, Any]] = []
    ignored: list[dict[str, Any]] = []
    seen_agents: set[str] = set()
    for index in range(count):
        address = begin + index * AGENT_STRIDE
        agent_raw = reader.read(address + AGENT_ID_OFFSET, 8, "id_agente")
        agent_id = str(struct.unpack("<Q", agent_raw)[0])
        if agent_id == "0" or agent_id in seen_agents:
            raise ValueError("Identidade de agente vazia ou duplicada na resposta do jogo.")
        seen_agents.add(agent_id)
        title, title_object = _read_msvc_string(reader, address + TITLE_OFFSET, "titulo_box")
        dates_raw = reader.read(address + START_DATE_OFFSET, 12, "datas_box")
        start_date, _, expiration_date = struct.unpack("<III", dates_raw)
        total_raw = reader.read(address + 0x128, 4, "total_participantes_agente")
        agent_total = struct.unpack("<I", total_raw)[0]
        if catalog_only:
            boxes.append({"agente_id": agent_id, "titulo": title,
                          "inicio_epoch": start_date or None,
                          "fim_epoch": expiration_date or None, "total_jogo": agent_total})
            for off, original in ((AGENT_ID_OFFSET, agent_raw), (TITLE_OFFSET, title_object),
                                  (START_DATE_OFFSET, dates_raw), (0x128, total_raw)):
                if reader.read(address + off, len(original), "releitura_catalogo") != original:
                    raise card_levels_runtime.LevelsUnavailable("sessao_alterada", "O catálogo mudou durante a captura.")
            continue
        cards_by_id: dict[str, dict[str, Any]] = {}
        lists: list[dict[str, Any]] = []
        for list_name, offset, stride in LISTS:
            header_address = address + offset
            header = reader.read(header_address, 24, "cabecalho_" + list_name)
            first, _, _, total = card_levels_runtime.vector_bounds(header, stride, 20000)
            ids: list[str] = []
            for position in range(total):
                card_address = first + position * stride
                card_raw = reader.read(card_address + 8, 8, "id_carta_box")
                card_id = str(struct.unpack("<Q", card_raw)[0])
                if not re.fullmatch(r"[1-9][0-9]*", card_id):
                    raise ValueError("A lista da box contém uma identidade de carta inválida.")
                ids.append(card_id)
                card = cards_by_id.setdefault(card_id, {
                    "card_id": card_id, "listas": [], "id_fisico_confirmado": card_id in physical_ids,
                })
                card["listas"].append({"nome": list_name, "indice": position})
            if reader.read(header_address, 24, "releitura_cabecalho_" + list_name) != header:
                raise card_levels_runtime.LevelsUnavailable(
                    "sessao_alterada", "Uma lista da box mudou durante a leitura."
                )
            digest = hashlib.sha256(b"".join(struct.pack("<Q", int(value)) for value in ids)).hexdigest()
            lists.append({"nome": list_name, "offset": hex(offset), "stride": hex(stride),
                          "quantidade": total, "ids_sha256": digest})
        missing = sorted(card_id for card_id, card in cards_by_id.items() if not card["id_fisico_confirmado"])
        if missing:
            raise ValueError("A box aponta para cards ausentes da extração física atual: " + ", ".join(missing[:10]))
        if not cards_by_id:
            ignored.append({"agente_id": agent_id, "titulo": title, "motivo": "agente_sem_cartas"})
        else:
            boxes.append({
                "agente_id": agent_id,
                "titulo": title,
                "inicio_epoch": start_date or None,
                "fim_epoch": expiration_date or None,
                "cartas": sorted(cards_by_id.values(), key=lambda item: int(item["card_id"])),
                "listas": lists,
                "total_jogo": agent_total,
            })
        if reader.read(address + AGENT_ID_OFFSET, 8, "releitura_id_agente") != agent_raw:
            raise card_levels_runtime.LevelsUnavailable("sessao_alterada", "A identidade de uma box mudou durante a leitura.")
        if reader.read(address + TITLE_OFFSET, 32, "releitura_titulo_box") != title_object:
            raise card_levels_runtime.LevelsUnavailable("sessao_alterada", "O título de uma box mudou durante a leitura.")
        if reader.read(address + 0x128, 4, "releitura_total_agente") != total_raw:
            raise card_levels_runtime.LevelsUnavailable("sessao_alterada", "O total de participantes mudou durante a leitura.")

    if not catalog_only:
        # O vetor de recrutamento contém a resposta de detalhes, não os banners.
        # Só vinculamos quando a lista inteira contém todos os destaques de um único agente.
        selected_agent, selected_raw = _read_pointer(reader, owner + 0x280, "agente_consultado")
        detail_header = reader.read(owner + 0x380, 24, "cabecalho_participantes_completos")
        detail_begin, _, _, detail_count = card_levels_runtime.vector_bounds(detail_header, 0xF0, 20000)
        counters = reader.read(owner + 0x398, 0x40, "contadores_participantes_completos")
        declared_total = struct.unpack_from("<I", counters, 0)[0]
        first_index = struct.unpack_from("<I", counters, 0x3D4 - 0x398)[0]
        complete_ids = []
        if detail_count and detail_count == declared_total and first_index == 0:
            detail_raw = reader.read(detail_begin, detail_count * 0xF0, "participantes_completos")
            complete_ids = [str(struct.unpack_from("<Q", detail_raw, i * 0xF0 + 8)[0])
                            for i in range(detail_count)]
            if len(set(complete_ids)) != detail_count or any(cid not in physical_ids for cid in complete_ids):
                raise ValueError("Participantes completos duplicados ou ausentes da referência física.")
            if reader.read(detail_begin, len(detail_raw), "releitura_participantes_completos") != detail_raw:
                raise card_levels_runtime.LevelsUnavailable("sessao_alterada", "Os participantes mudaram durante a captura.")
        candidates = [box for box in boxes if complete_ids and
                      {card["card_id"] for card in box["cartas"]}.issubset(set(complete_ids))]
        for box in boxes:
            complete_detail = (len(candidates) == 1 and box is candidates[0]
                               and box["agente_id"] == str(selected_agent)
                               and declared_total == box["total_jogo"])
            complete_agent = 0 < box["total_jogo"] == len(box["cartas"])
            box["participantes_completos"] = complete_detail or complete_agent
            if complete_detail:
                box["destaques"] = box["cartas"]
                box["cartas"] = [{"card_id": cid} for cid in complete_ids]
                box["origem_participantes"] = "detalhes_do_agente"
            elif complete_agent:
                box["origem_participantes"] = "listas_do_agente_conferidas_com_player_list_total"
        if (reader.read(owner + 0x280, 8, "releitura_agente_consultado") != selected_raw
                or reader.read(owner + 0x380, 24, "releitura_cabecalho_participantes") != detail_header
                or reader.read(owner + 0x398, 0x40, "releitura_contadores_participantes") != counters):
            raise card_levels_runtime.LevelsUnavailable("sessao_alterada", "A lista de participantes mudou durante a captura.")

    if reader.read(owner, 24, "releitura_lista_agentes") != outer:
        raise card_levels_runtime.LevelsUnavailable("sessao_alterada", "A lista de boxes mudou durante a leitura.")
    for at, raw, purpose in ((base + card_levels_runtime.ROOT_RVA, g_raw, "raiz_cartas_boxes"),
                             (g + 0x28, manager_raw, "gerenciador_boxes"),
                             (manager + 0x20, owner_raw, "dono_lista_agentes")):
        if reader.read(at, len(raw), "releitura_" + purpose) != raw:
            raise card_levels_runtime.LevelsUnavailable("sessao_alterada", "A raiz das boxes mudou durante a leitura.")
    if not boxes:
        raise card_levels_runtime.LevelsUnavailable("boxes_sem_cartas", "Nenhuma box com cartas foi carregada pelo jogo.")
    return {
        "schema": SCHEMA,
        "leitor_versao": READER_VERSION,
        "fonte": SOURCE,
        "captura_id": capture_id,
        "capturado_em": captured_at,
        "cobertura": "catalogo_agentes_carregado" if catalog_only else "participantes_completos_do_agente_carregado",
        "agentes_retornados": count,
        "boxes": boxes,
        "agentes_ignorados": ignored,
    }


def capture(physical_ids: set[str], *, catalog_only: bool = False, cancel: Callable[[], None] | None = None) -> dict[str, Any]:
    capture_id = str(uuid.uuid4())
    captured_at = datetime.now(timezone.utc).isoformat()
    game = card_levels_runtime.discover_game()
    with card_levels_runtime.WindowsMemoryReader(game, cancel) as reader:
        result = read_loaded_boxes(reader, physical_ids, capture_id=capture_id, captured_at=captured_at, catalog_only=catalog_only)
        result["jogo"] = {
            "pid": game["pid"], "executavel_sha256": game["executable_sha256"],
            "versao": game["executable_version"], "base": hex(game["image_base"]),
        }
        result["bytes_lidos"] = reader.total
    return result


def _public_payload(capture_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": capture_result["schema"],
        "leitor_versao": capture_result["leitor_versao"],
        "fonte": capture_result["fonte"],
        "captura_id": capture_result["captura_id"],
        "capturado_em": capture_result["capturado_em"],
        "cobertura": capture_result["cobertura"],
        "executavel_sha256": capture_result["jogo"]["executavel_sha256"],
        "participantes_completos": True,
        "boxes": [{
            "total_jogo": box["total_jogo"],
            "agente_id": box["agente_id"], "titulo": box["titulo"],
            "inicio_epoch": box["inicio_epoch"], "fim_epoch": box["fim_epoch"],
            "cartas": [card["card_id"] for card in box["cartas"]],
        } for box in capture_result["boxes"] if box.get("participantes_completos")],
    }


def record_offer_catalog(run_dir: Path, runtime: Any, cancel=None) -> dict[str, Any]:
    """Registra IDs, títulos e datas sem consultar ou substituir vínculos carta-box."""
    catalog = capture(set(), catalog_only=True, cancel=cancel)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "boxes-catalogo-jogo.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    payload = json.dumps(catalog, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    result = {"estado": "catalogo_registrado", "agentes": len(catalog["boxes"]),
              "captura_id": catalog["captura_id"], "vinculos_alterados": False}
    psycopg, _, _ = runtime.import_psycopg()
    dsn = runtime.connection_string()
    if not dsn:
        raise RuntimeError("Conexão segura indisponível para registrar o catálogo de ofertas.")
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        connection.execute(
            "insert into clube_novo.box_captura_jogo_v1 "
            "(captura_id,capturado_em,executavel_sha256,leitor_versao,payload_sha256,payload,estado_anterior,resultado) "
            "values (%s,%s,%s,%s,%s,%s::jsonb,'[]'::jsonb,%s::jsonb)",
            (catalog["captura_id"], catalog["capturado_em"], catalog["jogo"]["executavel_sha256"],
             READER_VERSION, digest, payload, json.dumps(result)))
        for box in catalog["boxes"]:
            connection.execute(
                "insert into clube_novo.box_agente_captura_jogo_v1 "
                "(captura_id,agente_jogo_id,titulo,inicio_epoch,fim_epoch) values (%s,%s,%s,%s,%s)",
                (catalog["captura_id"], box["agente_id"], box["titulo"], box["inicio_epoch"], box["fim_epoch"]))
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        rows = connection.execute(
            "select agente_jogo_id::text,titulo,inicio_epoch,fim_epoch "
            "from clube_novo.box_agente_captura_jogo_v1 where captura_id=%s",
            (catalog["captura_id"],)).fetchall()
    expected = {(b["agente_id"], b["titulo"], b["inicio_epoch"], b["fim_epoch"]) for b in catalog["boxes"]}
    if set(rows) != expected:
        raise RuntimeError("A leitura independente do catálogo divergiu da captura.")
    return {**result, "independent_readback": True}


def collect_and_apply(canonical_cards_path: Path, run_dir: Path, runtime: Any,
                      emit: Callable[..., None], cancel: Callable[[], None]) -> dict[str, Any]:
    """Captura, grava pela RPC canônica e confirma por uma leitura independente."""
    try:
        catalog_result = record_offer_catalog(run_dir, runtime, cancel)
        emit("progress", stage="boxes", message=f"{catalog_result['agentes']} ofertas do jogo registradas e conferidas")
        canonical = json.loads(canonical_cards_path.read_text(encoding="utf-8"))
        records = canonical.get("records") if isinstance(canonical, dict) else canonical
        physical_ids = {str(item["card_id"]) for item in records if isinstance(item, dict) and item.get("card_id")}
        if not physical_ids:
            raise RuntimeError("A extração física atual não forneceu identidades de cartas para conferir as boxes.")
        emit("progress", stage="boxes", message="Lendo títulos e cartas das boxes no eFootball")
        captured = capture(physical_ids, cancel=cancel)
        capture_path = run_dir / "boxes-jogo-captura.json"
        capture_path.write_text(json.dumps(captured, ensure_ascii=False, indent=2), encoding="utf-8")
        payload = _public_payload(captured)
        if not payload["boxes"]:
            raise card_levels_runtime.LevelsUnavailable("detalhes_box_pendentes", "Abra os jogadores disponíveis de uma box para capturar os participantes completos.")
        payload_path = run_dir / "boxes-jogo-envio.json"
        payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        psycopg, _, _ = runtime.import_psycopg()
        dsn = runtime.connection_string()
        if not dsn:
            raise RuntimeError("Conexão segura indisponível para publicar as boxes extraídas do jogo.")
        with psycopg.connect(dsn, connect_timeout=20) as connection:
            result = connection.execute(
                "select clube_novo.sincronizar_boxes_jogo_v1(%s::jsonb)",
                (json.dumps(payload, ensure_ascii=False),),
            ).fetchone()[0]
        expected = {(box["agente_id"], card) for box in payload["boxes"] for card in box["cartas"]}
        with psycopg.connect(dsn, connect_timeout=20) as connection:
            rows = connection.execute(
                "select agente_jogo_id::text,card_id "
                "from clube_novo.box_agente_card_captura_jogo_v1 where captura_id=%s",
                (payload["captura_id"],),
            ).fetchall()
        if set(rows) != expected:
            raise RuntimeError("A leitura independente da captura de boxes divergiu depois da gravação.")
        read_total = int(result.get("boxes_lidas", result.get("boxes", 0)))
        classified_total = sum(int(result.get(key, 0)) for key in (
            "boxes_novas", "boxes_reconhecidas", "boxes_atualizadas",
        ))
        if read_total != len(payload["boxes"]) or classified_total != read_total:
            raise RuntimeError("O banco não classificou todas as boxes lidas pelo jogo.")
        outcome = {**result, "boxes_com_detalhes_pendentes": len(captured["boxes"])-len(payload["boxes"]), "state": "published", "database_write": True,
                   "independent_readback": True, "capture_path": str(capture_path),
                   "payload_path": str(payload_path)}
        emit("family", family="Boxes do jogo", state="ready",
             message=(f"{read_total} boxes lidas: {result.get('boxes_novas', 0)} novas, "
                      f"{result.get('boxes_reconhecidas', 0)} já cadastradas e "
                      f"{result.get('boxes_atualizadas', 0)} atualizadas; "
                      f"{len(expected)} vínculos conferidos; "
                      f"{len(captured['boxes'])-len(payload['boxes'])} ofertas aguardam detalhes completos."),
             database_write=True)
        return outcome
    except card_levels_runtime.LevelsUnavailable as error:
        outcome = {"state": error.state, "reason": str(error), "database_write": False}
        emit("family", family="Boxes do jogo", state="waiting", message=str(error), database_write=False)
        return outcome
    except Exception as error:
        outcome = {"state": "failed", "reason": str(error), "database_write": False}
        emit("family", family="Boxes do jogo", state="error", message=str(error), database_write=False)
        return outcome


def extract_only(root: Path, run_dir: Path, runtime: Any, emit: Callable[..., None],
                 cancel: Callable[[], None]) -> dict[str, Any]:
    """Consulta dedicada às ofertas: dispensa cadastro físico e abertura de detalhes."""
    result = record_offer_catalog(run_dir, runtime, cancel)
    result = {**result, "state": "catalog_registered", "database_write": True}
    (run_dir / "boxes-resultado.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    emit("complete", state=result["state"], result_path=str(run_dir / "boxes-resultado.json"), database_write=True)
    return result


def apply_saved(run_dir: Path, runtime: Any, emit: Callable[..., None]) -> dict[str, Any]:
    """Reaplica a captura da mesma rodada após a inclusão de cartas novas."""
    payload_path = run_dir / "boxes-jogo-envio.json"
    if not payload_path.is_file():
        return {"state": "not_captured", "database_write": False}
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    if payload.get("schema") != SCHEMA or payload.get("fonte") != SOURCE:
        raise RuntimeError("A captura salva das boxes não pertence ao leitor do jogo.")
    psycopg, _, _ = runtime.import_psycopg()
    dsn = runtime.connection_string()
    if not dsn:
        raise RuntimeError("Conexão segura indisponível para publicar as boxes extraídas do jogo.")
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        result = connection.execute(
            "select clube_novo.sincronizar_boxes_jogo_v1(%s::jsonb)",
            (json.dumps(payload, ensure_ascii=False),),
        ).fetchone()[0]
    emit("family", family="Boxes do jogo", state="ready", message="Captura física da rodada reaplicada e conferida.", database_write=True)
    return {**result, "state": "published", "database_write": True}
