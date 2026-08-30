"""Gera relatório estático, somente leitura, dos especiais lançados.

Identidade e junções usam apenas codigo_jogo/card_id. Rótulos operacionais são
apresentação confirmada, nunca vínculo físico do catálogo ao texto.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXECUTOR = ROOT / "executor"
if str(EXECUTOR) not in sys.path:
    sys.path.insert(0, str(EXECUTOR))

import executor_local as ex  # noqa: E402


CODES = [56, 57, 58, 134, 135, 142, 143, 144, 250, 263, 265, 266, 267]
UNRELEASED_CODE = 261
RUN = ROOT / "artefatos" / "desktop" / "run-20260830-005609"
PROOF = ROOT / "artefatos" / "investigacao-impetos" / "prova-categoria-texto-impeto.json"
OUTPUT = Path(r"C:\Users\Luis Fernando\Documents\Codex\2026-08-30\realtime-voice-chat\outputs\impetos-especiais-sem-rotulo-confirmado.html")


def rows(cursor, query: str, params=()):
    cursor.execute(query, params)
    names = [column.name for column in cursor.description]
    return [dict(zip(names, values, strict=True)) for values in cursor.fetchall()]


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def display_label(pt, en, fallback="Informação sem rótulo legível") -> str:
    if isinstance(pt, str) and pt.strip() and "�" not in pt:
        return pt.strip()
    if isinstance(en, str) and en.strip():
        return en.strip()
    return fallback


def load_physical_card_names() -> dict[str, str]:
    result: dict[str, str] = {}
    with (RUN / "cartas-fisicas.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            card_id = row.get("card_id")
            if card_id:
                result[card_id] = row.get("nome") or "Jogador sem nome disponível"
    return result


def main() -> None:
    proof = json.loads(PROOF.read_text(encoding="utf-8"))
    physical = {
        int(item["codigo_jogo"]): item
        for item in proof["unresolved_records"]
        if int(item.get("categoria_raw_bit137_w5", -1)) == 0
        and int(item["codigo_jogo"]) in CODES
    }
    if sorted(physical) != CODES:
        raise RuntimeError("a prova física não contém exatamente os códigos lançados esperados")

    psycopg, _, _ = ex.import_psycopg()
    dsn = ex.connection_string()
    if not dsn:
        raise RuntimeError("conexão segura com clube_novo indisponível")
    with psycopg.connect(dsn, connect_timeout=20) as connection:
        with connection.cursor() as cursor:
            cursor.execute("set transaction read only")
            catalog = rows(
                cursor,
                "select i.codigo_jogo,i.nome_pt,i.nome_en,i.id_texto,i.secao_texto,"
                "i.condicional,i.tipo_condicao_raw,i.fonte_condicao,i.falta_o_que,"
                "c.criterio_codigo,c.status_validacao,c.arquivo_origem,c.indice_registro,c.registro_sha256 "
                "from clube_novo.impeto_jogo i "
                "left join clube_novo.impeto_condicao_jogo c on c.codigo_impeto=i.codigo_jogo "
                "where i.codigo_jogo=any(%s) order by i.codigo_jogo",
                (CODES,),
            )
            effects = rows(
                cursor,
                "select e.codigo_impeto,e.codigo_atributo,a.nome_pt,a.nome_en,e.delta,e.bit_delta,"
                "e.largura_delta,e.arquivo_origem,e.registro_origem,e.fonte_origem,"
                "e.endereco_origem,e.status_validacao "
                "from clube_novo.impeto_atributo_jogo e "
                "left join clube_novo.atributo_jogo a on a.codigo=e.codigo_atributo "
                "where e.codigo_impeto=any(%s) order by e.codigo_impeto,e.ordem",
                (CODES,),
            )
            cards = rows(
                cursor,
                "select c.codigo_impeto,c.slot,c.ordem,c.card_id "
                "from clube_novo.carta_impeto_jogo c "
                "where c.codigo_impeto=any(%s) and not c.vaga "
                "order by c.codigo_impeto,c.card_id",
                (CODES,),
            )

    if len(catalog) != len(CODES) or len(cards) != len(CODES):
        raise RuntimeError("readback não retornou exatamente os especiais lançados")
    by_effect: dict[int, list[dict]] = defaultdict(list)
    by_card: dict[int, list[dict]] = defaultdict(list)
    for item in effects:
        by_effect[int(item["codigo_impeto"])].append(item)
    for item in cards:
        by_card[int(item["codigo_impeto"])].append(item)
    names = load_physical_card_names()

    patterns: dict[str, list[int]] = defaultdict(list)
    for code in CODES:
        current = by_effect[code]
        deltas = sorted({int(item["delta"]) for item in current})
        if len(deltas) != 1:
            pattern = f"{len(current)} atributos · deltas mistos"
        else:
            noun = "atributo" if len(current) == 1 else "atributos"
            pattern = f"{len(current)} {noun} · +{deltas[0]}"
        patterns[pattern].append(code)

    sections = []
    catalog_by_code = {int(item["codigo_jogo"]): item for item in catalog}
    for code in CODES:
        item = catalog_by_code[code]
        code_effects = by_effect[code]
        code_cards = by_card[code]
        raw_label = item.get("nome_pt") or item.get("nome_en")
        label = raw_label if raw_label else "Sem rótulo atual"
        attrs = "".join(
            f"<li><strong>{esc(display_label(effect.get('nome_pt'), effect.get('nome_en'), effect['codigo_atributo']))}</strong> <span class='delta'>+{int(effect['delta'])}</span></li>"
            for effect in code_effects
        )
        players = "".join(
            f"<li><strong>{esc(names.get(card['card_id'], 'Jogador sem nome disponível'))}</strong> <span class='muted'>card_id {esc(card['card_id'])}</span></li>"
            for card in code_cards
        )
        slots = sorted({int(card["slot"]) for card in code_cards})
        physical_item = physical[code]
        tech_effects = "".join(
            "<li>"
            f"{esc(effect['codigo_atributo'])} · bit {esc(effect['bit_delta'])}/w{esc(effect['largura_delta'])} · "
            f"registro {esc(effect['registro_origem'])} · {esc(effect['endereco_origem'])}"
            "</li>"
            for effect in code_effects
        )
        search = " ".join(
            [str(code), str(label), *(names.get(card["card_id"], "") for card in code_cards), *(display_label(effect.get("nome_pt"), effect.get("nome_en"), effect["codigo_atributo"]) for effect in code_effects)]
        ).lower()
        sections.append(f"""
        <article class="booster" data-search="{esc(search)}">
          <header>
            <div><span class="code">Código {code}</span><h2>{esc(label)}</h2></div>
            <span class="pending">Rótulo operacional confirmado</span>
          </header>
          <p class="warning">O nome acima foi confirmado para apresentação. A ligação física oficial código → texto continua pendente e o nome não participa da identidade.</p>
          <div class="facts">
            <div><span>Categoria física</span><strong>0</strong></div>
            <div><span>Slot observado</span><strong>{', '.join('slot '+str(slot) for slot in slots)}</strong></div>
            <div><span>Ativação</span><strong>Sempre ativo</strong></div>
            <div><span>Padrão comprovado</span><strong>{len(code_effects)} {'atributo' if len(code_effects)==1 else 'atributos'} · +{code_effects[0]['delta']}</strong></div>
          </div>
          <h3>Atributos afetados</h3><ul class="attributes">{attrs}</ul>
          <h3>Cartas que usam este Ímpeto</h3><ul>{players}</ul>
          <details><summary>Detalhes técnicos e procedência</summary>
            <dl>
              <dt>Arquivo físico</dt><dd>PlayerBooster.bin — DT870 da atualização</dd>
              <dt>Registro</dt><dd>{esc(physical_item['registro'])}</dd>
              <dt>SHA-256 do registro</dt><dd>{esc(physical_item['registro_sha256'])}</dd>
              <dt>SHA-256 do arquivo</dt><dd>{esc(physical_item['arquivo_sha256'])}</dd>
              <dt>Campo da categoria</dt><dd>bit 137, largura 5, valor 0</dd>
              <dt>Condição</dt><dd>{esc(item.get('criterio_codigo'))} · tipo raw {esc(item.get('tipo_condicao_raw'))}</dd>
              <dt>Ponte textual</dt><dd>secao_texto={esc(item.get('secao_texto')) or 'nulo'}; id_texto={esc(item.get('id_texto')) or 'nulo'}</dd>
            </dl>
            <h4>Campos físicos dos efeitos</h4><ul>{tech_effects}</ul>
          </details>
        </article>""")

    summary = "".join(
        f"<div class='summary-card'><strong>{len(codes)}</strong><span>{esc(pattern)}</span><small>Códigos: {', '.join(map(str, codes))}</small></div>"
        for pattern, codes in sorted(patterns.items())
    )
    document = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ímpetos Especiais sem Rótulo Confirmado</title>
<style>
:root{{--bg:#0b1220;--panel:#121c2e;--line:#26344e;--text:#eef4ff;--muted:#a8b5ca;--accent:#5eead4;--warn:#fbbf24}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 system-ui,Segoe UI,sans-serif}}
main{{max-width:1120px;margin:auto;padding:32px 20px 72px}}h1{{font-size:clamp(2rem,5vw,3.3rem);margin:.2em 0}}.lead{{color:var(--muted);max-width:900px}}
.notice{{border-left:5px solid var(--warn);background:#241e12;padding:14px 18px;border-radius:10px;margin:22px 0}}
.summary{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:24px 0}}.summary-card{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px;display:grid;gap:5px}}.summary-card strong{{font-size:2rem;color:var(--accent)}}.summary-card small,.muted{{color:var(--muted)}}
input{{width:100%;padding:14px 16px;border-radius:12px;border:1px solid var(--line);background:#0e1728;color:var(--text);font-size:1rem;margin:10px 0 24px}}
.booster{{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:20px;margin:16px 0}}.booster header{{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}}h2{{margin:3px 0 0}}h3{{margin-bottom:6px}}.code{{color:var(--accent);font-weight:700}}.pending{{background:#3a2810;color:#ffd978;padding:6px 10px;border-radius:999px;font-size:.85rem;white-space:nowrap}}.warning{{color:#ffd978}}
.facts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:16px 0}}.facts div{{background:#0e1728;border-radius:10px;padding:10px 12px}}.facts span{{display:block;color:var(--muted);font-size:.85rem}}.delta{{color:var(--accent);font-weight:800}}li{{margin:.3em 0}}details{{margin-top:18px;border-top:1px solid var(--line);padding-top:12px}}summary{{cursor:pointer;color:var(--accent);font-weight:700}}dl{{display:grid;grid-template-columns:minmax(140px,220px) 1fr;gap:6px 12px}}dt{{color:var(--muted)}}dd{{margin:0;overflow-wrap:anywhere}}.hidden{{display:none}}
@media(max-width:600px){{.booster header{{display:block}}.pending{{display:inline-block;margin-top:8px}}dl{{grid-template-columns:1fr}}}}
</style></head><body><main>
<p class="code">Relatório somente leitura · 30/08/2026</p><h1>Ímpetos Especiais sem Rótulo Confirmado</h1>
<p class="lead">{len(CODES)} códigos usados por {len(cards)} cartas lançadas. Este relatório exclui os 346 casos “Pacote total” e também o registro futuro de Maeda Daizen.</p>
<div class="notice"><strong>Pendência ativa:</strong> os rótulos operacionais estão confirmados, mas a ponte física código → texto não foi localizada. O código {UNRELEASED_CODE} (Agressividade, Maeda Daizen) permanece no catálogo da atualização e não é apresentado como carta atual.</div>
<section class="summary">{summary}<div class="summary-card"><strong>8 / 5</strong><span>slot 1 / slot 2</span><small>{len(cards)} cartas lançadas</small></div></section>
<label for="search">Pesquisar por jogador, card_id, código ou atributo</label><input id="search" type="search" placeholder="Ex.: Messi, 134, velocidade…">
<section id="results">{''.join(sections)}</section>
<p id="empty" class="notice hidden">Nenhum item corresponde à pesquisa.</p>
<script>const q=document.querySelector('#search'),items=[...document.querySelectorAll('.booster')],empty=document.querySelector('#empty');q.addEventListener('input',()=>{{const s=q.value.trim().toLowerCase();let n=0;for(const el of items){{const show=!s||el.dataset.search.includes(s);el.classList.toggle('hidden',!show);if(show)n++}}empty.classList.toggle('hidden',n!==0)}});</script>
</main></body></html>"""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(document, encoding="utf-8")
    print(json.dumps({
        "path": str(OUTPUT),
        "sha256": hashlib.sha256(document.encode("utf-8")).hexdigest(),
        "codes": len(CODES),
        "cards": len(cards),
        "effects": len(effects),
        "patterns": patterns,
        "slot_counts": {str(slot): sum(1 for card in cards if int(card["slot"]) == slot) for slot in (1, 2)},
        "database_write": False,
    }, ensure_ascii=False, indent=2, default=list))


if __name__ == "__main__":
    main()
