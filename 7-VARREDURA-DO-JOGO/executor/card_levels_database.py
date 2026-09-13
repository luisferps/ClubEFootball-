"""Contrato e envio explícito dos níveis; a coleta habitual permanece sem apply.

Reutiliza a conexão local do executor. O nível ausente nunca vira 1 ou zero.
O arquivo de prova contém apenas os campos permitidos, sem dump ou máscara.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import html
import json
from pathlib import Path
import uuid

import card_levels_runtime as reader
import executor_local as runtime

EXPECTED_LAYOUT = {
    "raiz_rva": "0x86c9fc0", "raiz_cadeia": ["deref", "0x28", "deref"],
    "proprias": {"offset": "0x08", "stride": "0xf0", "header_offsets": ["0x00", "0x08", "0x10"]},
    "boxes": {"offset": "0x20", "agent_stride": "0x238", "listas": [
        {"nome": "pickup_list", "offset": "0xe8", "stride": "0xf8"},
        {"nome": "banner_a_pickup_list", "offset": "0x200", "stride": "0xf0"},
        {"nome": "banner_c_pickup_list", "offset": "0x218", "stride": "0xf0"}]},
    "decodificador": {"tipo": "xor_u32", "mascara_rva": "0x8686608", "persistir_mascara": False},
    "formula": "2 * nivel_maximo - 2", "cobertura": "somente_colecoes_carregadas", "nivel_ausente": "nao_observado",
    "lista_recrutamento": {"offset": "0x380", "stride": "0xf0", "total_offset": "0x398", "indice_inicial_offset": "0x3d4", "tamanho_pagina_offset": "0x3d0", "tipo_contadores": "u32_le"},
}
EXPECTED_FIELDS = {
    "card_id": (8, 64, 64, "u64_le", {}, "clube_novo.carta_jogo.card_id"),
    "nivel_atual": (40, 320, 32, "xor_u32_le", {"decoder": "xor_u32", "mask_rva": "0x8686608", "persist_mask": False}, "instancia_da_carta_apenas"),
    "nivel_maximo": (44, 352, 32, "xor_u32_le", {"decoder": "xor_u32", "mask_rva": "0x8686608", "persist_mask": False}, "clube_novo.carta_jogo.level_cap"),
    "orcamento_maximo": (None, None, None, "derivado", {"expression": "2 * nivel_maximo - 2", "zero_valid_if_max": 1}, "clube_novo.carta_jogo.orcamento"),
    "recrutamento_indice_inicial": (980, 7840, 32, "u32_le", {"meaning": "indice_da_pagina", "relative_to": "B=[A+0x20]"}, "coleta.cobertura"),
    "recrutamento_total_reportado": (920, 7360, 32, "u32_le", {"meaning": "total_reportado_na_resposta", "relative_to": "B=[A+0x20]"}, "coleta.cobertura"),
}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf8")).hexdigest()


def validate_contract(envelope):
    contract = envelope.get("contrato") or {}
    if (contract.get("contrato_id") != "clubef-card-level-runtime-v1" or contract.get("ativo") is not True
            or contract.get("fonte") != "memoria_jogo" or contract.get("leitor_versao") != reader.READER_VERSION
            or reader.SUPPORTED_EXE.get(contract.get("executavel_sha256")) != contract.get("executavel_versao")
            or contract.get("layout") != EXPECTED_LAYOUT):
        raise ValueError("Contrato de níveis incompatível com este leitor; atualize o extrator antes de coletar.")
    fields = envelope.get("campos") or []
    if len(fields) != len(EXPECTED_FIELDS): raise ValueError("Campos do contrato de níveis mudaram.")
    found = {}
    keys = ("byte_offset", "bit_inicio", "largura_bits", "tipo_leitura", "transformacao", "destino")
    for field in fields:
        name = field.get("chave_campo")
        if name in found or field.get("contrato_id") != contract["contrato_id"]: raise ValueError("Identidade dos campos do contrato inválida.")
        found[name] = tuple(field.get(k) for k in keys)
    if found != EXPECTED_FIELDS: raise ValueError("Offsets, tipos ou destinos do contrato de níveis mudaram.")
    return contract


def connect(read_only):
    runtime.assert_card_target(runtime.load_config())
    dsn = runtime.connection_string()
    if not dsn: raise RuntimeError("Configure a conexão existente do extrator para conferir os níveis.")
    psycopg, _, _ = runtime.import_psycopg()
    connection = psycopg.connect(dsn, connect_timeout=10)
    connection.read_only = read_only
    return connection


def fetch_contract(connection):
    envelope = connection.execute("select public.extrator_contrato_niveis_runtime_v1()").fetchone()[0]
    if not isinstance(envelope, dict): raise ValueError("O banco ainda não publicou o contrato físico de níveis.")
    validate_contract(envelope)
    return envelope


def baseline(connection, ids):
    if not ids: return {}
    rows = connection.execute("""select c.card_id,c.level_cap,c.orcamento,c.cap_estimado,
        e.nivel_maximo,e.orcamento_real,e.captura_id::text,
        (select coalesce(jsonb_object_agg(d.coluna,d.valor),'{}'::jsonb)
         from clube_novo.valor_do_dono d where d.destino_schema='clube_novo'
         and d.destino_tabela='carta_jogo' and d.chave=jsonb_build_object('card_id',c.card_id)
         and d.coluna in ('level_cap','orcamento','cap_estimado')) as valores_manuais
        from clube_novo.carta_jogo c left join clube_novo.carta_nivel_evidencia_v1 e using(card_id)
        where c.card_id=any(%s::text[])""", (ids,)).fetchall()
    return {str(r[0]): dict(zip(("nivel_cadastro", "orcamento_cadastro", "estimado", "nivel_comprovado", "orcamento_comprovado", "captura_id", "valores_manuais"), r[1:])) for r in rows}


def effective_levels(captured, current):
    """A prova permanece física; só o valor esperado no cadastro recebe a decisão manual."""
    expected = {"level_cap": captured["nivel_maximo"], "orcamento": captured["orcamento_real"], "cap_estimado": False}
    manual = current.get("valores_manuais") or {}
    expected.update({key: manual[key] for key in expected if key in manual})
    return expected


class ApplyConfirmationError(RuntimeError):
    database_write = True
    commit_status = "confirmed_readback_pending"


class ApplyCommitUncertainError(ApplyConfirmationError):
    commit_status = "unknown"


class WriteTransaction:
    """Não anuncia rollback quando a conexão falha ao confirmar o commit."""
    def __enter__(self):
        self.connection = connect(False)
        return self.connection.__enter__()

    def __exit__(self, error_type, error, trace):
        try:
            return self.connection.__exit__(error_type, error, trace)
        except Exception as commit_error:
            if error_type is None:
                raise ApplyCommitUncertainError("A confirmação do commit foi interrompida. O banco pode ter concluído a gravação; repita Atualizar níveis com a mesma captura para conferir sem duplicar.") from commit_error
            raise


def verify_readback(checked, cards, capture_ids):
    for row in cards:
        old = checked.get(row["card_id"]) or {}
        expected = effective_levels(row, old)
        if (old.get("nivel_cadastro") != expected["level_cap"] or old.get("orcamento_cadastro") != expected["orcamento"]
                or old.get("estimado") is not expected["cap_estimado"] or old.get("nivel_comprovado") != row["nivel_maximo"]
                or old.get("orcamento_comprovado") != row["orcamento_real"] or old.get("captura_id") not in capture_ids):
            raise RuntimeError("Nível, orçamento ou prova divergem na conferência do banco.")


def validate_report(report, envelope):
    contract = validate_contract(envelope)
    if report.get("schema") != reader.SCHEMA or report.get("state") != "coletado": raise ValueError("Não há captura validada para aplicar.")
    body = dict(report); supplied = body.pop("artifact_sha256", None)
    if supplied != digest(body): raise ValueError("A prova da captura foi alterada; faça nova varredura.")
    if report.get("leitor_versao") != reader.READER_VERSION or report.get("layout") != reader.LAYOUT: raise ValueError("Leitor/layout da captura incompatível.")
    uuid.UUID(report["captura_id"])
    if datetime.fromisoformat(report["capturado_em"]).tzinfo is None: raise ValueError("Captura sem fuso horário.")
    session = report.get("session") or {}
    if session.get("executable_sha256") != contract["executavel_sha256"] or session.get("executable_version") != contract["executavel_versao"]: raise ValueError("Executável da captura diferente do contrato ativo.")
    if report.get("game_write") is not False or report.get("representacao_salva") is not False: raise ValueError("Proveniência da captura inválida.")
    if (report.get("coverage") or {}).get("catalogo_completo") is not False: raise ValueError("Cobertura da captura não declarada.")
    ids = set()
    for row in report.get("cards", []):
        cid, maximum, budget = row.get("card_id"), row.get("nivel_maximo"), row.get("orcamento_real")
        if not isinstance(cid, str) or not cid.isascii() or not cid.isdecimal() or cid in ids: raise ValueError("ID inválido ou repetido na captura.")
        if type(maximum) is not int or type(budget) is not int or not 1 <= maximum <= 1000 or budget != 2 * maximum - 2: raise ValueError("Nível ou orçamento inválido na captura.")
        if row.get("captura_id") != report["captura_id"] or row.get("origem") != "memoria_jogo": raise ValueError("Origem por carta inválida.")
        proof = row.get("prova_json") or {}
        if any(proof.get(k) is not True for k in ("representacao_estavel", "raizes_estaveis", "limites_conferidos", "id_fisico_confirmado", "maximo_sem_conflito")): raise ValueError("Prova física incompleta.")
        if proof.get("layout") != reader.LAYOUT or proof.get("sessao") != session: raise ValueError("Proveniência física divergente.")
        occurrences = proof.get("ocorrencias") or []
        if not occurrences: raise ValueError("Carta sem ocorrência física.")
        for occurrence in occurrences:
            if occurrence.get("card_id") != cid or occurrence.get("nivel_maximo") != maximum or not 1 <= occurrence.get("nivel_atual", 0) <= maximum or any(occurrence.get(k) is not True for k in ("id_estavel", "niveis_estaveis", "id_fisico_confirmado")): raise ValueError("Ocorrência física inconsistente.")
        ids.add(cid)
    if not ids: raise ValueError("Captura vazia.")
    return contract


def render_review(package, path):
    rows = []
    for row in package.get("comparison", []):
        old = row.get("cadastro") or {}
        cells = [row["card_id"], row["nivel_maximo"], row["orcamento_real"], old.get("nivel_cadastro"), old.get("orcamento_cadastro"), row["estado"]]
        rows.append("<tr>" + "".join("<td>" + html.escape(str(x) if x is not None else "pendente") + "</td>" for x in cells) + "</tr>")
    collection_rows = []
    for collection in (package.get("capture") or {}).get("collections", []):
        cells = [collection["colecao"], collection.get("agente_id"), collection["ocorrencias"], collection.get("total_reportado"), collection.get("indice_inicial_reportado"), collection.get("tamanho_pagina_reportado")]
        collection_rows.append("<tr>" + "".join("<td>" + html.escape(str(x) if x is not None else "—") + "</td>" for x in cells) + "</tr>")
    text = """<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Níveis reais — Extrator</title>
    <style>body{font:16px Segoe UI,sans-serif;max-width:1100px;margin:40px auto;color:#172332}table{border-collapse:collapse;width:100%}td,th{padding:9px;border-bottom:1px solid #ddd;text-align:left}h1{font-size:26px}</style>
    <h1>Níveis reais das cartas observadas</h1><p>""" + html.escape(package["message"]) + "</p><p>O jogo precisa estar aberto com as coleções carregadas. Cartas não observadas continuam pendentes. Máximo 1 tem orçamento 0. A atualização é feita pelo botão Atualizar níveis do extrator.</p><table><thead><tr><th>Card ID</th><th>Máximo observado</th><th>Orçamento real</th><th>Máximo no cadastro</th><th>Orçamento no cadastro</th><th>Conferência</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></html>"
    text = text.replace("</html>", "<p>Correções manuais registradas prevalecem no cadastro. A prova mantém os números observados no jogo, mesmo quando diferentes do valor manual.</p><h2>Coleções carregadas</h2><p>Contagens físicas desta captura. Total e página informados pelo jogo não comprovam que todas as cartas do catálogo foram carregadas.</p><table><thead><tr><th>Coleção</th><th>Agente</th><th>Ocorrências lidas</th><th>Total informado</th><th>Índice inicial</th><th>Tamanho de página</th></tr></thead><tbody>" + "".join(collection_rows) + "</tbody></table></html>")
    path.write_text(text, encoding="utf8")


def collect(canonical_path, run_dir, emit, cancel):
    path = run_dir / "niveis-runtime-pacote.json"
    package = {"schema": "clubef-pacote-niveis-runtime-v1", "ready": False, "database_write": False, "comparison": []}
    try:
        with connect(True) as connection: envelope = fetch_contract(connection)
        package["contract"] = envelope
        collected = reader.collect_for_desktop(canonical_path, run_dir, emit, cancel)
        report = collected["report"]
        package.update(capture=report, capture_artifact=collected["artifact"], message=collected["message"])
        if report.get("state") == "coletado":
            validate_report(report, envelope)
            with connect(True) as connection:
                fetch_contract(connection)
                existing = baseline(connection, [r["card_id"] for r in report["cards"]])
            for row in report["cards"]:
                old = existing.get(row["card_id"])
                state = "identidade ainda não cadastrada" if old is None else "confirmado" if old["nivel_cadastro"] == row["nivel_maximo"] and old["orcamento_cadastro"] == row["orcamento_real"] and old["estimado"] is False and old["nivel_comprovado"] == row["nivel_maximo"] else "atualizar nível/orçamento e prova"
                if old and old.get("valores_manuais"):
                    state = "preservar correção manual; conferir prova coletada"
                package["comparison"].append({"card_id": row["card_id"], "nivel_maximo": row["nivel_maximo"], "orcamento_real": row["orcamento_real"], "cadastro": old, "estado": state})
            eligible = [r["card_id"] for r in report["cards"] if r["card_id"] in existing]
            package.update(eligible_ids=eligible, ready=bool(eligible), canonical_path=str(canonical_path.resolve()), canonical_sha256=reader.sha256_file(canonical_path))
            package["message"] += f" {len(eligible)} IDs cadastrados disponíveis para Atualizar níveis."
    except Exception as error:
        cancel()
        # Erros de conexão não propagam connection strings ao artefato.
        package["message"] = str(error) if isinstance(error, (ValueError, reader.LevelsUnavailable)) else "Não foi possível conferir o contrato/cadastro dos níveis. Verifique a conexão configurada e tente novamente."
        emit("log", message=package["message"])
    package["package_sha256"] = digest(package)
    path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf8")
    review_path = run_dir / "niveis-runtime.html"; render_review(package, review_path)
    emit("family", family="Níveis reais", state="ready" if package["ready"] else "pending", message=package["message"], database_write=False)
    return {"package_path": str(path), "review_html_path": str(review_path), "ready": package["ready"], "cards": len(package.get("eligible_ids", [])), "message": package["message"]}


def apply_saved(path, run_dir, cancel, emit):
    path, run_dir = Path(path).resolve(), Path(run_dir).resolve()
    if path.parent != run_dir or path.name != "niveis-runtime-pacote.json": raise ValueError("Pacote de níveis fora da rodada selecionada.")
    package = json.loads(path.read_text(encoding="utf8")); supplied = package.pop("package_sha256", None)
    if supplied != digest(package) or package.get("schema") != "clubef-pacote-niveis-runtime-v1" or package.get("ready") is not True: raise ValueError("Pacote de níveis inválido ou alterado; refaça a varredura.")
    physical_path = Path(package["canonical_path"]).resolve()
    if not physical_path.is_relative_to(run_dir) or reader.sha256_file(physical_path) != package["canonical_sha256"]: raise ValueError("Identidades físicas mudaram; refaça a varredura.")
    physical_ids = {str(r["card_id"]) for r in json.loads(physical_path.read_text(encoding="utf-8-sig"))}
    report = package["capture"]
    validate_report(report, package["contract"])
    eligible = package.get("eligible_ids") or []
    cards = [{k: row[k] for k in ("card_id", "nivel_maximo", "orcamento_real", "prova_json")} for row in report["cards"] if row["card_id"] in eligible]
    if len(eligible) != len(cards) or any(r["card_id"] not in physical_ids for r in cards): raise ValueError("IDs selecionados não correspondem à captura física.")
    _, _, Jsonb = runtime.import_psycopg()
    batches = []; capture_ids = []
    # Todas as partes ficam na mesma transação: falha/cancelamento não aplica metade.
    with WriteTransaction() as connection:
        current = fetch_contract(connection); validate_report(report, current)
        if current != package["contract"]: raise ValueError("O contrato mudou após a coleta; refaça a varredura.")
        for start in range(0, len(cards), 1000):
            cancel()
            subset = cards[start:start + 1000]
            capture_id = report["captura_id"] if len(cards) <= 1000 else str(uuid.uuid5(uuid.UUID(report["captura_id"]), "lote-" + str(start // 1000)))
            capture = {"captura_id": capture_id, "leitor_versao": report["leitor_versao"], "executavel_sha256": report["session"]["executable_sha256"], "executavel_versao": report["session"]["executable_version"], "capturado_em": report["capturado_em"],
                       "prova_json": {"captura_origem": report["captura_id"], "pacote_sha256": supplied, "artefato_sha256": report["artifact_sha256"], "sessao": report["session"], "layout": report["layout"], "cobertura": report["coverage"], "colecoes": report["collections"], "identidade_fisica_sha256": package["canonical_sha256"], "representacao_salva": False}}
            response = connection.execute("select public.extrator_aplicar_niveis_runtime_v1(%s::jsonb,%s::jsonb)", (Jsonb(capture), Jsonb(subset))).fetchone()[0]
            if not isinstance(response, dict) or response.get("ok") is not True or response.get("aplicadas") != len(subset): raise RuntimeError("O banco não confirmou a quantidade de níveis aplicada.")
            batches.append(response); capture_ids.append(capture_id)
        cancel()
        checked = baseline(connection, eligible)
        verify_readback(checked, cards, capture_ids)
    try:
        # Conexão nova confirma que os dados persistiram além da transação.
        with connect(True) as connection: verify_readback(baseline(connection, eligible), cards, capture_ids)
        result = {"schema": "clubef-aplicacao-niveis-runtime-v1", "state": "aplicado", "database_write": True, "aplicadas": len(cards), "readback": True, "independent_readback": True, "batches": batches, "package_sha256": supplied}
        result_path = run_dir / "niveis-runtime-aplicacao.json"
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    except Exception as error:
        raise ApplyConfirmationError("O banco concluiu a gravação, mas a confirmação independente ou o recibo local falhou. Repita Atualizar níveis para conferir a mesma captura sem duplicá-la.") from error
    emit("complete", state="runtime_levels_applied", applied=len(cards), database_write=True, readback=True, result_path=str(result_path), message=f"{len(cards)} cartas com nível, orçamento e prova conferidos no banco.")
    return 0
