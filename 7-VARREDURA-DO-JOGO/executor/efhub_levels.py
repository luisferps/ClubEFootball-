"""Coleta levelCap no eFHUB em lotes planejados pelo clube_novo.

O banco escolhe os card_ids e preserva o antes/depois. Este cliente apenas
abre uma sessao oficial do site, valida a identidade da resposta e devolve o
lote completo (sucessos e falhas) para uma aplicacao transacional.
"""
from __future__ import annotations

import hashlib
import html
import http.cookiejar
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, Request, build_opener

TOKEN_URL = "https://efhub.com/api/auth/token"
PLAYER_URL = "https://efhub.com/api/public/players/{card_id}"
CONTRACT = "clubef-efhub-level-v1"
USER_AGENT = "ClubEfootball-Extractor/5.3 (level-cap batch)"
MAIN_LOT_FALLBACK_NAMESPACE = uuid.UUID("2dd4e997-cb68-4ee1-aa04-25861f35b03a")


def canonical_json(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def normalize_player_response(card_id: str, payload: dict, raw: bytes, fetched_at: str) -> dict:
    expected = str(card_id)
    if not expected.isdigit() or int(expected) <= 0:
        raise ValueError("card_id planejado invalido")
    if not isinstance(payload, dict):
        raise ValueError("eFHUB devolveu um documento que nao e objeto")
    response_id = str(payload.get("id", ""))
    player_id = str(payload.get("playerId", ""))
    if response_id != expected or player_id != expected:
        raise ValueError(f"identidade divergente: esperado {expected}; id={response_id}; playerId={player_id}")
    level = payload.get("levelCap")
    if isinstance(level, bool) or not isinstance(level, int) or not 1 <= level <= 99:
        raise ValueError("levelCap ausente ou fora do intervalo 1..99")
    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("nome do jogador ausente")
    player_type = payload.get("playerType")
    datapack_id = payload.get("datapackId")
    if isinstance(player_type, bool) or not isinstance(player_type, int):
        raise ValueError("playerType invalido")
    if isinstance(datapack_id, bool) or not isinstance(datapack_id, int):
        raise ValueError("datapackId invalido")
    digest = hashlib.sha256(raw).hexdigest()
    return {
        "card_id": expected,
        "id": response_id,
        "player_id": player_id,
        "name": name.strip(),
        "player_type": player_type,
        "datapack_id": datapack_id,
        "level_cap": level,
        "orcamento_real": 2 * level - 2,
        "source_url": PLAYER_URL.format(card_id=expected),
        "http_status": 200,
        "response_sha256": digest,
        "prova_json": {
            "contrato": CONTRACT,
            "card_id": expected,
            "id": response_id,
            "playerId": player_id,
            "levelCap": level,
            "orcamento": 2 * level - 2,
            "name": name.strip(),
            "playerType": player_type,
            "datapackId": datapack_id,
            "overallRating": payload.get("overallRating"),
            "response_sha256": digest,
            "source_url": PLAYER_URL.format(card_id=expected),
            "fetched_at": fetched_at,
        },
    }


class EfhubSession:
    def __init__(self, timeout: int = 25):
        self.timeout = timeout
        self.cookies = http.cookiejar.CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(self.cookies))

    def _request(self, url: str, accept: str):
        return Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept, "Referer": "https://efhub.com/"})

    def authenticate(self) -> None:
        with self.opener.open(self._request(TOKEN_URL, "application/json,*/*"), timeout=self.timeout) as response:
            if response.status != 204 or response.geturl() != TOKEN_URL:
                raise RuntimeError(f"token eFHUB recusado: HTTP {response.status}")
            response.read(1024)
        if not any(cookie.name == "__hub_req" for cookie in self.cookies):
            raise RuntimeError("cookie de requisicao do eFHUB nao foi emitido")

    def player(self, card_id: str) -> dict:
        url = PLAYER_URL.format(card_id=card_id)
        last_error = None
        for attempt in range(1, 4):
            try:
                with self.opener.open(self._request(url, "application/json"), timeout=self.timeout) as response:
                    if response.status != 200 or response.geturl() != url:
                        raise RuntimeError(f"HTTP inesperado {response.status}")
                    content_type = response.headers.get("Content-Type", "").lower()
                    if "application/json" not in content_type:
                        raise RuntimeError("eFHUB devolveu formato inesperado")
                    raw = response.read(200_001)
                    if len(raw) > 200_000:
                        raise RuntimeError("resposta eFHUB acima do limite")
                fetched_at = datetime.now(timezone.utc).isoformat()
                return normalize_player_response(card_id, json.loads(raw.decode("utf-8")), raw, fetched_at)
            except HTTPError as error:
                last_error = error
                if error.code in (401, 403) and attempt < 3:
                    self.cookies.clear()
                    self.authenticate()
            except (URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError, RuntimeError, ValueError) as error:
                last_error = error
            if attempt < 3:
                time.sleep(0.5 * attempt)
        status = last_error.code if isinstance(last_error, HTTPError) else None
        detail = f"HTTP {status}" if status else str(last_error)
        raise RuntimeError(f"falha ao consultar card {card_id}: {detail}")


def _atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".novo")
    temporary.write_bytes(canonical_json(value))
    temporary.replace(path)


def _write_report_html(path: Path, result: dict, items: list[dict]) -> None:
    comparison = result.get("comparacao") or {}
    repair = result.get("reparo_fila") or {}
    rows = []
    for item in items:
        rows.append("<tr>" + "".join(
            f"<td>{html.escape(str(value if value is not None else ''))}</td>" for value in (
                item.get("ordem"), item.get("card_id"), item.get("name"), item.get("level_cap"),
                item.get("orcamento_real"), item.get("estado"), item.get("erro"),
            )
        ) + "</tr>")
    document = """<!doctype html><meta charset=utf-8><title>Lote de níveis eFHUB</title>
<style>body{{font:15px Segoe UI,Arial;margin:32px;color:#17202a}}h1{{margin-bottom:8px}}.cards{{display:flex;gap:12px;flex-wrap:wrap}}.k{{background:#f2f5f7;padding:14px 18px;border-radius:8px}}.n{{font-size:26px;font-weight:700}}table{{border-collapse:collapse;width:100%;margin-top:24px}}th,td{{border:1px solid #ccd3d8;padding:7px;text-align:left}}th{{background:#202b38;color:white}}.ok{{color:#08783e}}.warn{{color:#a45b00}}</style>
<h1>Lote de níveis eFHUB</h1><p>Lote <code>{batch}</code> — estado <strong class="{klass}">{state}</strong></p>
<div class=cards>{cards}</div>
<p>Os números abaixo são os coletados no eFHUB. Correções manuais registradas prevalecem no cadastro; a prova coletada permanece preservada. Divergências sem correção registrada continuam sendo erro de conferência.</p>
<table><thead><tr><th>Ordem</th><th>card_id</th><th>Nome eFHUB</th><th>Nível</th><th>Orçamento</th><th>Coleta</th><th>Erro</th></tr></thead><tbody>{rows}</tbody></table>
""".format(
        batch=html.escape(str(result.get("lote_id", ""))), state=html.escape(str(result.get("state", ""))),
        klass="ok" if result.get("state") == "aplicado" else "warn",
        cards="".join(f"<div class=k><div>{html.escape(label)}</div><div class=n>{int(value or 0)}</div></div>" for label, value in (
            ("Planejadas", result.get("planejadas")), ("Alteradas", comparison.get("cartas_alteradas")),
            ("Inalteradas", comparison.get("cartas_inalteradas")), ("Falhas", comparison.get("falhas")),
            ("Conflitos físicos", comparison.get("conflitos_fisicos")), ("Linhas repostas", repair.get("novas")),
            ("Publicações retiradas", repair.get("publicacoes_retiradas")),
        )), rows="".join(rows),
    )
    path.write_text(document, encoding="utf-8")


def _db_value(row):
    value = row[0]
    if isinstance(value, str):
        return json.loads(value)
    return value


def _pending_queue_groups(connection, limit_cards: int = 5000) -> list[dict]:
    """Lista revisoes ainda pendentes, inclusive de lotes eFHUB anteriores.

    Isto permite que uma coleta feita enquanto o Otimizador estava ativo seja
    reconciliada assim que houver um lote-modelo pausado, sem SQL manual.
    """
    rows = connection.execute(
        "select b.card_id,jsonb_agg(b.id order by b.id) linhas "
        "from clube_novo.build_linha_card b "
        "join clube_novo.otimizador_lote_producao_carta_v3 s "
        "  on s.lote_id=b.lote_producao_id and s.card_id=b.card_id "
        "join clube_novo.carta_nivel_evidencia_v1 e on e.card_id=b.card_id "
        "join clube_novo.otimizador_prioridade_orcamento_v1 p on p.card_id=b.card_id "
        "where b.execucao_tipo='producao' and b.estado<>'invalida' "
        "  and b.estado_otimizador<>'processando' "
        "  and (s.entrada_otimizador#>>'{escalares,orcamento}')::integer is distinct from p.orcamento_real "
        "  and not exists(select 1 from clube_novo.orcamento_revisao_linha_v1 r where r.linha_anterior_id=b.id) "
        "group by b.card_id,p.prioridade_grupo,p.overall "
        "order by p.prioridade_grupo,p.overall desc nulls first,b.card_id collate \"C\" "
        "limit %s",
        (int(limit_cards),),
    ).fetchall()
    return [{"card_id": str(row[0]), "linhas": list(row[1] or [])} for row in rows]


def _merge_queue_groups(*collections) -> list[dict]:
    merged: dict[str, set[int]] = {}
    order: list[str] = []
    for collection in collections:
        for group in collection or []:
            card_id = str(group["card_id"])
            if card_id not in merged:
                merged[card_id] = set()
                order.append(card_id)
            merged[card_id].update(int(value) for value in (group.get("linhas") or []))
    return [{"card_id": card_id, "linhas": sorted(merged[card_id])} for card_id in order if merged[card_id]]


def _repair_queue(connection, comparison: dict, include_pending: bool = True) -> dict:
    current = comparison.get("linhas_por_card") or []
    pending = _pending_queue_groups(connection) if include_pending else []
    groups = _merge_queue_groups(current, pending)
    if not groups:
        return {"cards": 0, "linhas": 0, "novas": 0, "ja_revisadas": 0, "publicacoes_retiradas": 0,
                "falhas": 0, "detalhes_falha": [], "pendencias_anteriores_incluidas": 0, "aguardando_pausa": False}
    model = connection.execute(
        "select id::text from clube_novo.otimizador_lote_producao_v3 "
        "where estado='pausado' and pode_publicar=false order by linhas desc,criado_em limit 1"
    ).fetchone()
    if not model:
        return {"cards": len(groups), "linhas": sum(len(g["linhas"]) for g in groups), "novas": 0,
                "ja_revisadas": 0, "publicacoes_retiradas": 0, "falhas": len(groups),
                "detalhes_falha": [{"card_id": g["card_id"], "erro": "nenhum lote modelo pausado"} for g in groups],
                "pendencias_anteriores_incluidas": max(0, len(groups) - len(current)), "aguardando_pausa": True}
    # Uma rodada corretiva precisa de lote próprio. Reaproveitar lote anterior
    # colide quando a mesma carta recebe uma nova revisão de entrada.
    corrective_id = str(uuid.uuid4())
    report = {"cards": len(groups), "linhas": 0, "novas": 0, "ja_revisadas": 0, "publicacoes_retiradas": 0,
              "falhas": 0, "detalhes_falha": [], "pendencias_anteriores_incluidas": max(0, len(groups) - len(current)),
              "aguardando_pausa": False}
    for group in groups:
        card_id = str(group["card_id"])
        line_ids = [int(value) for value in group["linhas"]]
        report["linhas"] += len(line_ids)
        try:
            with connection.transaction():
                for start in range(0, len(line_ids), 500):
                    piece = line_ids[start:start + 500]
                    prepared = _db_value(connection.execute(
                        "select public.otimizador_preparar_revisao_orcamento_v1(%s::uuid,%s::uuid,%s::bigint[])",
                        (model[0], corrective_id, piece),
                    ).fetchone())
                    removed = _db_value(connection.execute(
                        "select public.otimizador_manter_publicacao_ate_substituicao_v1(%s::bigint[])", (piece,)
                    ).fetchone())
                    report["novas"] += int(prepared.get("novas") or 0)
                    report["ja_revisadas"] += int(prepared.get("ja_revisadas") or 0)
                    report["publicacoes_retiradas"] += int(removed.get("publicacoes_retiradas") or 0)
                    report["publicacoes_mantidas_ate_substituicao"] = (
                        int(report.get("publicacoes_mantidas_ate_substituicao") or 0)
                        + int(removed.get("publicacoes_mantidas_ate_substituicao") or 0)
                    )
        except Exception as error:
            report["falhas"] += 1
            report["detalhes_falha"].append({"card_id": card_id, "erro": str(error)[:500]})
    report["lote_modelo"] = model[0]
    report["lote_corretivo"] = corrective_id
    return report


def _write_many_report_html(path: Path, result: dict) -> None:
    rows = []
    for batch in result.get("lotes") or []:
        rows.append("<tr>" + "".join(
            f"<td>{html.escape(str(value if value is not None else ''))}</td>" for value in (
                batch.get("numero"), batch.get("lote_id"), batch.get("planejadas"), batch.get("coletadas"),
                batch.get("alteradas"), batch.get("inalteradas"), batch.get("falhas_coleta"),
                batch.get("linhas_repostas"), batch.get("falhas_reparo"), batch.get("estado"),
            )
        ) + "</tr>")
    document = """<!doctype html><meta charset=utf-8><title>Extração de níveis eFHUB</title>
<style>body{{font:15px Segoe UI,Arial;margin:32px;color:#17202a}}h1{{margin-bottom:8px}}.cards{{display:flex;gap:12px;flex-wrap:wrap}}.k{{background:#f2f5f7;padding:14px 18px;border-radius:8px}}.n{{font-size:26px;font-weight:700}}table{{border-collapse:collapse;width:100%;margin-top:24px}}th,td{{border:1px solid #ccd3d8;padding:7px;text-align:left}}th{{background:#202b38;color:white}}</style>
<h1>Extração de níveis eFHUB</h1><p>Estado: <strong>{state}</strong></p><div class=cards>{cards}</div>
<table><thead><tr><th>#</th><th>Lote</th><th>Planejadas</th><th>Coletadas</th><th>Alteradas</th><th>Inalteradas</th><th>Falhas coleta</th><th>Linhas repostas</th><th>Falhas reparo</th><th>Estado</th></tr></thead><tbody>{rows}</tbody></table>
""".format(
        state=html.escape(str(result.get("state", ""))),
        cards="".join(f"<div class=k><div>{html.escape(label)}</div><div class=n>{int(value or 0)}</div></div>" for label, value in (
            ("Solicitadas", result.get("solicitadas")), ("Processadas", result.get("processadas")),
            ("Coletadas", result.get("coletadas")), ("Alteradas", result.get("cartas_alteradas")),
            ("Linhas repostas", result.get("linhas_repostas")), ("Falhas", result.get("falhas_coleta")),
        )), rows="".join(rows),
    )
    path.write_text(document, encoding="utf-8")


def run_batch(run_dir: Path, runtime, emit, limit: int = 100, cancel=lambda: False, delay: float = 0.25,
              repair_queue: bool = True) -> dict:
    if not 1 <= int(limit) <= 1000:
        raise ValueError("O lote eFHUB deve conter entre 1 e 1.000 cartas")
    dsn = runtime.connection_string()
    if not dsn:
        raise RuntimeError("conexao protegida indisponivel; use CONFIGURAR CONEXAO")
    psycopg, _, _ = runtime.import_psycopg()
    run_dir.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        plan = _db_value(connection.execute("select public.extrator_efhub_planejar_lote_v1(%s)", (int(limit),)).fetchone())
    _atomic_json(run_dir / "efhub-plano.json", plan)
    if plan.get("concluido"):
        result = {"ok": True, "state": "catalogo_concluido", "planejadas": 0, "restantes": 0, "database_write": False}
        _atomic_json(run_dir / "efhub-resultado.json", result)
        _write_report_html(run_dir / "resultado.html", result, [])
        emit("complete", **result, report_path=str(run_dir / "efhub-resultado.json"))
        return result
    batch_id = str(plan["lote_id"])
    items = []
    session = EfhubSession()
    emit("progress", stage="efhub_levels", current=0, total=len(plan["itens"]), message=f"Abrindo lote eFHUB {batch_id}")
    session.authenticate()
    for index, planned in enumerate(plan["itens"], 1):
        if cancel():
            raise RuntimeError("cancelled_by_user")
        card_id = str(planned["card_id"])
        try:
            item = session.player(card_id)
            item.update({"estado": "coletado", "ordem": int(planned["ordem"]), "tentativas": 1})
        except Exception as error:
            item = {"estado": "falhou", "ordem": int(planned["ordem"]), "card_id": card_id,
                    "tentativas": 3, "http_status": None, "erro": str(error)[:1000]}
        items.append(item)
        _atomic_json(run_dir / "efhub-checkpoint.json", {"lote_id": batch_id, "itens": items})
        emit("progress", stage="efhub_levels", current=index, total=len(plan["itens"]),
             message=f"eFHUB: {index}/{len(plan['itens'])} cartas consultadas")
        if delay and index < len(plan["itens"]):
            time.sleep(delay)
    manifest = hashlib.sha256(canonical_json({"lote_id": batch_id, "itens": items})).hexdigest()
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        comparison = _db_value(connection.execute(
            "select public.extrator_efhub_aplicar_lote_v1(%s::uuid,%s,%s::jsonb)",
            (batch_id, manifest, json.dumps(items, ensure_ascii=False, separators=(",", ":"))),
        ).fetchone())
    if repair_queue:
        with psycopg.connect(dsn, connect_timeout=20) as connection:
            repair = _repair_queue(connection, comparison)
    else:
        repair = {"cards": 0, "linhas": int(comparison.get("linhas_divergentes") or 0), "novas": 0,
                  "ja_revisadas": 0, "publicacoes_retiradas": 0, "falhas": 0,
                  "detalhes_falha": [], "reparo_adiado": True,
                  "motivo": "extracao_integral_grava_somente_nivel_e_orcamento"}
        emit("progress", stage="database", message="Níveis e orçamentos confirmados; seguindo sem processar a fila do Otimizador.")
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        finalized = _db_value(connection.execute(
            "select public.extrator_efhub_finalizar_lote_v1(%s::uuid,%s::jsonb)",
            (batch_id, json.dumps(repair, ensure_ascii=False, separators=(",", ":"))),
        ).fetchone())
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        readback = connection.execute(
            """select count(*),count(*) filter(where i.estado<>'conflito_fisico'
               and c.level_cap is not distinct from (m.esperado->>'level_cap')::integer
               and c.orcamento is not distinct from (m.esperado->>'orcamento')::integer
               and c.cap_estimado is not distinct from (m.esperado->>'cap_estimado')::boolean
               and a.nivel_maximo=i.nivel_maximo and a.orcamento_real=i.orcamento_real)
            from clube_novo.efhub_nivel_atual_v1 a
            join clube_novo.carta_jogo c using(card_id)
            join clube_novo.efhub_nivel_lote_item_v1 i on i.card_id=a.card_id and i.lote_id=a.lote_id
            cross join lateral (
              select jsonb_build_object('level_cap',a.nivel_maximo,'orcamento',a.orcamento_real,'cap_estimado',false)
                || coalesce(jsonb_object_agg(d.coluna,d.valor),'{}'::jsonb) as esperado
              from clube_novo.valor_do_dono d where d.destino_schema='clube_novo'
                and d.destino_tabela='carta_jogo' and d.chave=jsonb_build_object('card_id',c.card_id)
                and d.coluna in ('level_cap','orcamento','cap_estimado')
            ) m where a.lote_id=%s::uuid""",
            (batch_id,),
        ).fetchone()
    if int(readback[0]) != int(comparison.get("coletadas") or 0) or int(readback[1]) + int(comparison.get("conflitos_fisicos") or 0) != int(readback[0]):
        raise RuntimeError("conferencia independente do lote eFHUB divergiu")
    result = {"ok": True, "state": finalized.get("estado"), "lote_id": batch_id, "manifesto_sha256": manifest,
              "planejadas": len(items), "restantes_antes_do_lote": plan.get("restantes"), "comparacao": comparison,
              "reparo_fila": repair, "readback": {"efhub": int(readback[0]), "carta_jogo": int(readback[1]),
              "conflitos_fisicos": int(comparison.get("conflitos_fisicos") or 0)}, "database_write": True}
    _atomic_json(run_dir / "efhub-resultado.json", result)
    try:
        _write_report_html(run_dir / "resultado.html", result, items)
    except Exception as error:
        (run_dir / "relatorio-html-erro.txt").write_text(str(error), encoding="utf-8")
        emit("progress", stage="report", message="O lote foi gravado e conferido; somente o HTML falhou: " + str(error))
    emit("complete", state="efhub_levels_batch_" + str(finalized.get("estado")), lote_id=batch_id,
         planejadas=len(items), coletadas=comparison.get("coletadas"), cartas_alteradas=comparison.get("cartas_alteradas"),
         cartas_inalteradas=comparison.get("cartas_inalteradas"), conflitos_fisicos=comparison.get("conflitos_fisicos"),
         falhas_coleta=comparison.get("falhas"), linhas_repostas=repair.get("novas"), publicacoes_retiradas=repair.get("publicacoes_retiradas"),
         falhas_reparo=repair.get("falhas"), restantes_antes_do_lote=plan.get("restantes"), independent_readback=True,
         database_write=True, report_path=str(run_dir / "efhub-resultado.json"))
    return result


def _run_sequence(run_dir: Path, runtime, emit, total, cancel=lambda: False, delay: float = 0.25,
                  repair_queue: bool = True, batch_size: int = 100) -> dict:
    """Executa uma quantidade ou catálogo em commits do tamanho informado."""
    batch_size = int(batch_size)
    if not 1 <= batch_size <= 1000:
        raise ValueError("A unidade de gravação deve estar entre 1 e 1.000 cartas")
    all_catalog = total is None
    if not all_catalog:
        total = int(total)
        if not 1 <= total <= 10000:
            raise ValueError("A extração eFHUB deve conter entre 1 e 10.000 cartas")
    target = 0 if all_catalog else total
    run_dir.mkdir(parents=True, exist_ok=True)
    batches = []
    processed = 0
    catalog_finished = False

    def batch_emit(batch_number: int, offset: int):
        def scoped(event_type: str, **payload):
            if event_type == "progress":
                current = int(payload.get("current") or 0)
                batch_total = int(payload.get("total") or 0)
                progress_total = target if target > 0 else 0
                emit("progress", stage="efhub_levels", current=min(progress_total, offset + current) if progress_total else offset + current, total=progress_total,
                     batch=batch_number, batch_current=current, batch_total=batch_total,
                     message=payload.get("message") or f"Lote {batch_number}: {current}/{batch_total}")
            elif event_type == "complete":
                emit("batch_complete", batch=batch_number, processed=offset + int(payload.get("planejadas") or 0),
                     requested=target if target else "catalogo_inteiro", **payload)
            else:
                emit(event_type, **payload)
        return scoped

    while all_catalog or processed < target:
        if cancel():
            raise RuntimeError("cancelled_by_user")
        batch_number = len(batches) + 1
        batch_limit = batch_size if all_catalog else min(batch_size, target - processed)
        batch_dir = run_dir / f"lote-{batch_number:04d}"
        emit("progress", stage="efhub_levels", current=processed, total=target, batch=batch_number,
             message=f"Preparando lote {batch_number} de até {batch_limit} cartas")
        batch = run_batch(batch_dir, runtime, batch_emit(batch_number, processed), batch_limit, cancel, delay, repair_queue)
        if batch.get("state") == "catalogo_concluido":
            catalog_finished = True
            break
        comparison = batch.get("comparacao") or {}
        repair = batch.get("reparo_fila") or {}
        planned = int(batch.get("planejadas") or 0)
        if planned <= 0:
            raise RuntimeError("lote eFHUB sem cartas e sem indicação de catálogo concluído")
        if all_catalog and target == 0:
            target = max(planned, int(batch.get("restantes_antes_do_lote") or 0))
        processed += planned
        batches.append({
            "numero": batch_number, "lote_id": batch.get("lote_id"), "estado": batch.get("state"),
            "planejadas": planned, "coletadas": int(comparison.get("coletadas") or 0),
            "alteradas": int(comparison.get("cartas_alteradas") or 0),
            "inalteradas": int(comparison.get("cartas_inalteradas") or 0),
            "conflitos_fisicos": int(comparison.get("conflitos_fisicos") or 0),
            "falhas_coleta": int(comparison.get("falhas") or 0),
            "linhas_repostas": int(repair.get("novas") or 0),
            "publicacoes_retiradas": int(repair.get("publicacoes_retiradas") or 0),
            "falhas_reparo": int(repair.get("falhas") or 0),
            "aguardando_pausa": bool(repair.get("aguardando_pausa")),
            "diretorio": str(batch_dir),
        })
        # Conflito físico continua fechando a rodada: ele representa dado
        # incompatível, não uma indisponibilidade transitória do eFHUB.
        if int(comparison.get("conflitos_fisicos") or 0) > 0:
            break
        # No modo de catálogo inteiro, uma falha isolada não deve abandonar
        # milhares de cartas ainda não tentadas. O card sem evidência volta a
        # ser elegível no lote seguinte. Se o lote inteiro não avançou, pare
        # para não repetir indefinidamente uma falha persistente.
        if int(comparison.get("falhas") or 0) > 0:
            if not all_catalog or int(comparison.get("coletadas") or 0) <= 0:
                break

    totals = {
        "coletadas": sum(row["coletadas"] for row in batches),
        "cartas_alteradas": sum(row["alteradas"] for row in batches),
        "cartas_inalteradas": sum(row["inalteradas"] for row in batches),
        "conflitos_fisicos": sum(row["conflitos_fisicos"] for row in batches),
        "falhas_coleta": sum(row["falhas_coleta"] for row in batches),
        "linhas_repostas": sum(row["linhas_repostas"] for row in batches),
        "publicacoes_retiradas": sum(row["publicacoes_retiradas"] for row in batches),
        "falhas_reparo": sum(row["falhas_reparo"] for row in batches),
    }
    complete = catalog_finished if all_catalog else (processed >= target or catalog_finished)
    # Falhas transitórias já recuperadas ficam no histórico, mas não tornam a
    # execução parcial quando uma consulta final prova que o catálogo acabou.
    state = "concluido" if complete and totals["conflitos_fisicos"] == 0 else "parcial"
    result = {
        "ok": complete, "state": state, "solicitadas": target, "processadas": processed,
        "lotes_concluidos": len(batches), "catalogo_concluido": catalog_finished,
        "gravacao": f"cada_lote_de_ate_{batch_size}", "tamanho_lote": batch_size, "lotes": batches, **totals,
        "database_write": bool(batches), "independent_readback_each_batch": True,
        "fila_pendente_aguardando_pausa": any(row["aguardando_pausa"] for row in batches),
    }
    _atomic_json(run_dir / "resultado-geral.json", result)
    _write_many_report_html(run_dir / "resultado.html", result)
    emit("complete", **result, report_path=str(run_dir / "resultado-geral.json"))
    return result


def run_many(run_dir: Path, runtime, emit, total: int, cancel=lambda: False, delay: float = 0.25) -> dict:
    """Executa o total pedido em lotes transacionais de no máximo 100 cartas."""
    return _run_sequence(run_dir, runtime, emit, total, cancel, delay, True, 100)


def run_all(run_dir: Path, runtime, emit, cancel=lambda: False, delay: float = 0.25) -> dict:
    """Executa todas as cartas; fila do Otimizador permanece em etapa separada."""
    return _run_sequence(run_dir, runtime, emit, None, cancel, delay, False, 1000)
