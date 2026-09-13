"""Sincronização das ofertas da home eFHUB, cruzadas com o radar físico.

Disponibilidade é a home autorizada pelo operador; nomes físicos históricos
não substituem o agrupamento da oferta. Nenhuma pontuação é calculada aqui.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

HOME_URL = "https://efhub.com/pt-BR"


def offer_date(name: str) -> str | None:
    """Data explícita de nome de OFERTA validada; nunca de rótulo físico de card."""
    match = re.search(r"(?:^| )(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) '?(\d{2})$", name)
    if not match:
        return None
    month = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].index(match[2])+1
    try:
        return datetime(2000+int(match[3]),month,int(match[1])).date().isoformat()
    except ValueError:
        return None


class HomeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.heading = False
        self.current = None
        self.boxes = []

    def handle_starttag(self, tag, attrs):
        if tag == "section":
            if self.depth == 0:
                self.current = {"nome": "", "cards": []}
            self.depth += 1
        if not self.current:
            return
        if tag == "h2":
            self.heading = True
        if tag == "a":
            match = re.fullmatch(r"/pt-BR/players/([1-9][0-9]*)", dict(attrs).get("href", ""))
            if match and match[1] not in self.current["cards"]:
                self.current["cards"].append(match[1])

    def handle_data(self, data):
        if self.heading and self.current is not None:
            self.current["nome"] += data

    def handle_endtag(self, tag):
        if tag == "h2":
            self.heading = False
        if tag == "section" and self.depth:
            self.depth -= 1
            if not self.depth:
                if self.current["nome"].strip() and self.current["cards"]:
                    self.current["nome"] = self.current["nome"].strip()
                    self.boxes.append(self.current)
                self.current = None


def prepare(html: str, radar: dict, observed_at: str | None = None) -> dict:
    parser = HomeParser()
    parser.feed(html)
    if parser.depth or "</html>" not in html.lower() or not 1 <= len(parser.boxes) <= 100:
        raise ValueError("Home eFHUB incompleta ou sem boxes; estado anterior preservado")
    names = [b["nome"].casefold() for b in parser.boxes]
    if len(names) != len(set(names)):
        raise ValueError("Home eFHUB contém boxes duplicadas")
    if radar.get("contract") != "clubef-radar-lancamentos-fisicos-v2" or radar.get("evidence_mode") != "physical_runtime":
        raise ValueError("Radar físico produtivo não comprovado")
    provenance = radar.get("provenance") or {}
    if not provenance.get("card_join_checked") or not re.fullmatch("[a-f0-9]{64}", str((provenance.get("source") or {}).get("cpk_sha256", ""))):
        raise ValueError("Radar sem cruzamento com Player.bin ou hash físico")
    physical = {}
    for box in radar["boxes"]:
        for card in box["cartas"]:
            key = str(card["card_id"])
            if key in physical:
                raise ValueError("Card físico duplicado no radar")
            physical[key] = {"card_id": key, "box_fisica": box["nome_box"], "record_sha256": card["record_sha256"]}
    missing = sorted({c for b in parser.boxes for c in b["cards"] if c not in physical})
    if missing:
        raise ValueError("Cards da home ausentes da extração salva: " + ", ".join(missing))
    return {
        "source_url": HOME_URL,
        "observed_at": observed_at or datetime.now(timezone.utc).isoformat(),
        "html_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        "radar_fingerprint": radar["radar_fingerprint"],
        "physical_generated_at": radar["generated_at"],
        "physical_provenance": provenance,
        "boxes": [{"nome": b["nome"], "data_oferta": offer_date(b["nome"]), "cards": [physical[c] for c in b["cards"]]} for b in parser.boxes],
    }


def synchronize(run_dir: Path, runtime, emit) -> dict:
    """Usada também para corrigir uma rodada salva, sem reextrair o jogo."""
    radar = json.loads((run_dir / "radar-lancamentos.json").read_text(encoding="utf-8"))
    emit("progress", stage="boxes", message="Consultando boxes atuais na home eFHUB")
    request = Request(HOME_URL, headers={"User-Agent": "ClubEfootball-Extractor/1.0", "Accept": "text/html"})
    with urlopen(request, timeout=25) as response:
        if response.geturl() != HOME_URL or "text/html" not in response.headers.get("Content-Type", ""):
            raise ValueError("Fonte eFHUB redirecionada ou formato inesperado")
        raw = response.read(5_000_001)
        if len(raw) > 5_000_000:
            raise ValueError("Home eFHUB acima do limite de leitura")
        html = raw.decode("utf-8")
    payload = prepare(html, radar)
    (run_dir / "boxes-home.html").write_text(html, encoding="utf-8")
    (run_dir / "boxes-sincronizacao.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    psycopg, _, _ = runtime.import_psycopg()
    dsn = runtime.connection_string()
    if not dsn:
        raise RuntimeError("Conexão segura indisponível para sincronizar boxes")
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        result = connection.execute("select clube_novo.sincronizar_boxes_efhub_v1(%s::jsonb)", (json.dumps(payload, ensure_ascii=False),)).fetchone()[0]
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        rows = connection.execute("select b.box_nome,m.card_id from clube_novo.box_contexto_contratacao_v1 b join clube_novo.box_card_em_andamento_v1 m using(box_id) where b.estado_box='em_andamento'").fetchall()
    expected = {(b["nome"], c["card_id"]) for b in payload["boxes"] for c in b["cards"]}
    if set(rows) != expected:
        raise RuntimeError("Conferência independente das boxes divergiu após a gravação")
    result["independent_readback"] = True
    (run_dir / "boxes-resultado.json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    emit("family", family="Boxes em andamento", state="ready", message=f"{len(payload['boxes'])} boxes e {len(expected)} vínculos conferidos no banco", database_write=True)
    return result


def synchronize_report(run_dir: Path, runtime, emit) -> dict:
    try:
        result = synchronize(run_dir, runtime, emit)
    except Exception as error:
        reason = str(error) if isinstance(error, ValueError) else "Sincronização das boxes não confirmada; confira a conexão e o relatório da rodada."
        result = {"state": "pending", "reason": reason, "database_write": None}
        emit("family", family="Boxes em andamento", state="error", message=reason, database_write=None)
    (run_dir / "boxes-resultado.json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return result
