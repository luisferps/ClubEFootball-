"""Extrator V4.6.11: fotografia local e revisão obrigatória antes da escrita."""
from __future__ import annotations

import json
import threading
import traceback
import webbrowser
from http import HTTPStatus
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import servidor_v4610 as previous
from revisao_v4611 import (
    ACKNOWLEDGEMENT_PHRASE,
    acknowledge_review,
    get_review,
    latest_review,
    stage_review,
    verify_review,
)

RUNTIME_VERSION = "4.6.11"
DEFAULT_PORT = 8775

previous.RUNTIME_VERSION = RUNTIME_VERSION
previous.DEFAULT_PORT = DEFAULT_PORT
previous.legacy.RUNTIME_VERSION = RUNTIME_VERSION
previous.legacy.DEFAULT_PORT = DEFAULT_PORT


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(
            f"patch V4.6.11 não encontrou trecho único: {label} "
            f"(encontrados={count})"
        )
    return source.replace(old, new, 1)


def _card_relation_summary_js() -> str:
    return """      const relationsReadback = await postJsonReport('/api/card-relations/validate', { card_csv: core.rowsToCsv(currentRows) }, 600000);
      const relationsExact = Boolean(relationsReadback.passed && relationsReadback.transaction_read_only && relationsReadback.database_write === false);
      if (relationsExact) {
        log('log-incremental', `Relações aprovadas em leitura protegida: ${Object.values(relationsReadback.relations || {}).map((item) => Number(item.database_rows || 0).toLocaleString('pt-BR')).join(' · ')} linhas.`);
      } else {
        const relationIssues = Object.entries(relationsReadback.relations || {}).filter(([, item]) => !item.exact).map(([name, item]) => `${name}: ${Number(item.mismatch_count || 0).toLocaleString('pt-BR')} divergências`);
        log('log-incremental', `AVISO — relações de cartas divergentes (${relationIssues.join(' · ') || 'consulte o relatório'}). A fotografia e o diff continuarão, mas a aplicação de Cartas ficará bloqueada.`);
      }"""


def patched_ui_source_v4611() -> str:
    source = previous.patched_ui_source()

    old_relations = """      const relationsReadback = await postJson('/api/card-relations/validate', { card_csv: core.rowsToCsv(currentRows) }, 600000);
      if (!relationsReadback.passed || !relationsReadback.transaction_read_only || relationsReadback.database_write !== false) {
        throw new Error('A comparação integral das relações normalizadas de cartas não foi aprovada.');
      }
      log('log-incremental', `Relações aprovadas em leitura protegida: ${Object.values(relationsReadback.relations).map((item) => item.database_rows.toLocaleString('pt-BR')).join(' · ')} linhas.`);"""
    source = _replace_once(
        source,
        old_relations,
        _card_relation_summary_js(),
        "relações de cartas não bloqueantes",
    )

    card_state = """      state.incremental = { baseline, cards, currentRows, relationsReadback, diff, manifest, selection: defaultCardSelection(diff), allItems: applicableItems };"""
    card_stage = card_state + """
      try {
        const relationReport = Object.fromEntries(Object.entries(relationsReadback.relations || {}).map(([name, item]) => [name, {
          expected_rows: Number(item.expected_rows || 0),
          database_rows: Number(item.database_rows || 0),
          mismatch_count: Number(item.mismatch_count || 0),
          exact: Boolean(item.exact),
          mismatches: (item.mismatches || []).slice(0, 120)
        }]));
        await global.CLUBEF_REVIEW.stage({
          kind: 'cards',
          execution_id: manifest.execution_id,
          manifest,
          summary: {
            cartas: {
              status: relationsExact ? 'validado_banco' : 'divergente',
              current: currentRows.length,
              baseline_active: baseline.rows.length,
              new: diff.new_cards.length,
              changed: diff.changed_cards.length,
              absent: diff.possibly_inactive.length
            },
            relacoes_cartas: {
              status: relationsExact ? 'validado_banco' : 'divergente',
              current: Object.values(relationsReadback.relations || {}).reduce((total, item) => total + Number(item.expected_rows || 0), 0),
              baseline_active: Object.values(relationsReadback.relations || {}).reduce((total, item) => total + Number(item.database_rows || 0), 0),
              new: 0,
              changed: Object.values(relationsReadback.relations || {}).reduce((total, item) => total + Number(item.mismatch_count || 0), 0),
              absent: 0
            }
          },
          differences: {
            cards: manifest.changes,
            relations: relationReport
          },
          application: {
            allowed_families: relationsExact ? ['cards'] : [],
            blocked_families: relationsExact ? [] : ['cards']
          },
          database_write: false
        });
      } catch (reviewError) {
        log('log-incremental', `AVISO — não foi possível salvar a revisão local de Cartas: ${reviewError.message}. A escrita continuará bloqueada.`);
      }"""
    source = _replace_once(source, card_state, card_stage, "revisão de Cartas")

    activate_incremental = """      await activateCardPackage('incremental', manifest, { items: applicableItems, counts: { insert: diff.new_cards.length, update: diff.changed_cards.length, inactive: diff.possibly_inactive.length } });"""
    activate_incremental_new = activate_incremental + """
      if (!relationsExact) {
        state.cardPackage.application_blocked = true;
        $('prepare-card-package').disabled = true;
        $('prepare-card-package').textContent = 'Aplicação de Cartas bloqueada — revisar divergências';
        $('card-package-summary').textContent += ' A família Cartas possui divergências nas relações normalizadas e não pode ser enviada nesta rodada.';
      }"""
    source = _replace_once(
        source,
        activate_incremental,
        activate_incremental_new,
        "bloqueio de aplicação de Cartas divergentes",
    )

    metadata_state = """      state.metadata = { reference, baseline, physical, textCatalog, textItems, technicianReadback, impetusReadback, dimensionReadback, diff, summary, manifest, selection: new Set(textItems.map((item) => item.key)) };"""
    metadata_stage = metadata_state + """
      try {
        const blockedFamilies = [...new Set([
          ...familyWarnings.map((item) => item.family),
          ...(dimensionReadback.passed ? [] : ['dimensoes_cartas']),
          ...(baseline.schema_ready ? [] : ['textos'])
        ])];
        const allowedFamilies = [];
        if (dimensionReadback.passed) allowedFamilies.push('dimensoes_cartas');
        if (baseline.schema_ready && !blockedFamilies.includes('textos')) allowedFamilies.push('textos');
        await global.CLUBEF_REVIEW.stage({
          kind: 'metadata',
          execution_id: manifest.execution_id,
          manifest,
          summary,
          differences: Object.fromEntries(Object.entries(diff).map(([name, item]) => [name, {
            status: item.status,
            reason: item.reason || null,
            new_entries: item.new_entries || [],
            changed_entries: item.changed_entries || [],
            absent_entries: item.absent_entries || [],
            duplicate_ids: item.duplicate_ids || []
          }])),
          warnings: familyWarnings,
          application: {
            allowed_families: allowedFamilies,
            blocked_families: blockedFamilies
          },
          database_write: false
        });
      } catch (reviewError) {
        familyWarnings.push({ family: 'revisao_local', reason: reviewError.message });
        log('log-metadata', `AVISO — não foi possível salvar a revisão local: ${reviewError.message}. Nenhuma aplicação será liberada.`);
      }"""
    source = _replace_once(source, metadata_state, metadata_stage, "revisão de Metadados")

    full_unchanged = """        state.full = { cards: [], baseline: null, diff: null, manifest, fullCsv: null };"""
    full_unchanged_stage = full_unchanged + """
        try {
          await global.CLUBEF_REVIEW.stage({
            kind: 'full', execution_id: manifest.execution_id, manifest,
            summary: { cartas: { status: 'validado_banco', current: Number(reference.output.records || 0), baseline_active: Number(reference.output.records || 0), new: 0, changed: 0, absent: 0 } },
            differences: { new_cards: [], changed_cards: [], possibly_inactive: [] },
            application: { allowed_families: [], blocked_families: [] },
            database_write: false
          });
        } catch (reviewError) {
          log('log-full', `AVISO — revisão local não foi salva: ${reviewError.message}.`);
        }"""
    source = _replace_once(source, full_unchanged, full_unchanged_stage, "revisão de recarga sem mudanças")

    full_changed = """      state.full = { cards, baseline, diff, manifest: { ...manifest, reference_promotion: promotion.manifest || null }, fullCsv: null };"""
    full_changed_stage = full_changed + """
      try {
        await global.CLUBEF_REVIEW.stage({
          kind: 'full', execution_id: manifest.execution_id,
          manifest: state.full.manifest,
          summary: { cartas: { status: 'comparado', current: cards.length, baseline_active: baseline.rows.length, new: diff.new_cards.length, changed: diff.changed_cards.length, absent: diff.possibly_inactive.length } },
          differences: {
            new_cards: diff.new_cards,
            changed_cards: diff.changed_cards,
            possibly_inactive: diff.possibly_inactive
          },
          application: { allowed_families: ['cards'], blocked_families: [] },
          database_write: false
        });
      } catch (reviewError) {
        log('log-full', `AVISO — revisão local não foi salva: ${reviewError.message}. A escrita continuará bloqueada.`);
      }"""
    source = _replace_once(source, full_changed, full_changed_stage, "revisão de recarga completa")

    metadata_apply = """        result = await postJson('/api/apply', { approval_token: prepared.approval_token, confirmation: $('approval-text-metadata').value.trim(), request_id: executionId }, 180000);"""
    metadata_apply_new = """        result = await postJson('/api/apply', { approval_token: prepared.approval_token, confirmation: $('approval-text-metadata').value.trim(), request_id: executionId, ...global.CLUBEF_REVIEW.requireCredentials('metadata') }, 180000);"""
    source = _replace_once(source, metadata_apply, metadata_apply_new, "autorização final de Textos")

    card_apply = """        result = await postJson('/api/apply', { approval_token: prepared.approval_token, confirmation: $('approval-text-card-package').value.trim(), request_id: executionId });"""
    card_apply_new = """        result = await postJson('/api/apply', { approval_token: prepared.approval_token, confirmation: $('approval-text-card-package').value.trim(), request_id: executionId, ...global.CLUBEF_REVIEW.requireCredentials(state.cardPackage.type === 'full' ? 'full' : 'cards') });"""
    source = _replace_once(source, card_apply, card_apply_new, "autorização final de Cartas")

    if "CLUBEF_REVIEW.stage" not in source or "requireCredentials" not in source:
        raise RuntimeError("patch V4.6.11 não inseriu a camada de revisão na UI")
    return source + "\n//# sourceURL=/app/extrator-ui-v4611.js\n"


def _set_contract(handler: previous.Handler) -> dict:
    config = previous.legacy.base.load_config()
    handler._reading_contract = previous.legacy.base.current_reading_contract(config)
    return config


def _review_kind_for_approval(approved: dict) -> str:
    selection_kind = (approved.get("selection") or {}).get("kind")
    manifest_mode = str((approved.get("manifest") or {}).get("mode") or "")
    if selection_kind == "metadata":
        return "metadata"
    if manifest_mode == "card_full":
        return "full"
    return "cards"


def _apply_approved(handler: previous.Handler, payload: dict, config: dict) -> None:
    base = previous.legacy.base
    if not (base.manual_card_apply_allowed(config) or base.manual_text_apply_allowed(config)):
        raise PermissionError(
            "envio manual bloqueado: conexão segura ou permissão local indisponível"
        )
    request_id = str(payload.get("request_id", ""))
    decision = base.APPROVALS.begin(
        str(payload.get("approval_token", "")),
        str(payload.get("confirmation", "")),
        request_id,
    )
    if decision["state"] == "completed":
        handler.send_json(HTTPStatus.OK, decision["response"])
        return
    if decision["state"] == "applying":
        handler.send_json(
            HTTPStatus.ACCEPTED,
            {
                "state": "applying",
                "execution_id": decision["execution_id"],
                "message": "esta carga já está sendo aplicada; aguarde o resultado",
            },
        )
        return

    approved = decision["item"]
    execution_id = decision["execution_id"]
    review_kind = _review_kind_for_approval(approved)
    review = verify_review(
        Path(base.ROOT),
        str(payload.get("review_id") or ""),
        str(payload.get("review_token") or ""),
        expected_kind=review_kind,
        family="textos" if review_kind == "metadata" else "cards",
    )
    if str(review.get("execution_id") or "") != str(
        (approved.get("manifest") or {}).get("execution_id") or ""
    ):
        raise PermissionError(
            "envio bloqueado: a revisão não corresponde ao pacote preparado"
        )

    try:
        selection_kind = approved.get("selection", {}).get("kind")
        if selection_kind == "cards":
            base.assert_card_target(config)
        elif not (
            selection_kind == "metadata"
            and approved.get("selection", {}).get("items")
            and all(
                item.get("catalog") == "textos"
                for item in approved["selection"]["items"]
            )
        ):
            raise PermissionError(
                "somente pacotes validados de cartas ou textos canônicos podem usar o envio manual"
            )
        base.validate_manifest(approved["manifest"], config)
        result = base.apply_selection(approved["selection"], config)
        target_table = "carta_jogo" if selection_kind == "cards" else "texto_do_jogo"
        application_manifest = {
            "contract": "clubef-application-manifest-v1",
            "execution_id": execution_id,
            "applied_at": base.datetime.now(base.timezone.utc).isoformat(),
            "source_manifest_sha256": approved["manifest"]["manifest_sha256"],
            "selection_sha256": approved["selection_sha256"],
            "summary": approved["summary"],
            "target": {
                "schema": "clube_novo",
                "table": target_table,
                "preserved_schema": "clube",
            },
            "review": {
                "review_id": review["review_id"],
                "reviewed_at": review.get("reviewed_at"),
                "payload_sha256": review.get("payload_sha256"),
                "kind": review_kind,
            },
            "selected_items": approved["selection"]["items"],
            "preflight": approved["preflight"],
            "recovery_plan": base.recovery_plan(approved["selection"]),
            "result": result,
            "database_write": True,
            "idempotent_keys": "execution_id + selection_sha256 + card_id/chave canônica",
            "transaction": "serializable_fail_closed",
            "readback": True,
        }
        base.save_manifest("APLICACAO", application_manifest)
        response = {
            "application_manifest": application_manifest,
            "idempotent_reuse": False,
        }
        base.APPROVALS.complete(execution_id, response)
        handler.send_json(HTTPStatus.OK, response)
    except Exception as error:
        base.APPROVALS.fail(execution_id, str(error))
        raise


class Handler(previous.Handler):
    server_version = f"ClubEfootballLocal/{RUNTIME_VERSION}"

    def _serve_injected_ui(self) -> None:
        html_path = Path(previous.legacy.base.ROOT) / "Extrator-ClubEfootball.html"
        html = html_path.read_text(encoding="utf-8-sig")

        core_marker = '<script src="app/extrator-core.js"></script>'
        runtime_marker = '<script src="app/contrato-v46-runtime.js"></script>'
        if runtime_marker not in html:
            html = html.replace(core_marker, f"{core_marker}\n  {runtime_marker}")

        html = html.replace(
            '<script src="app/metadata-v46-runtime.js"></script>',
            '<script src="/app/metadata-v46-runtime-v4610.js?v=4.6.11"></script>',
        )
        html = html.replace(
            '<script src="app/extrator-ui.js"></script>',
            '<script src="/app/extrator-ui-v4611.js?v=4.6.11"></script>',
        )
        patched_ui = '<script src="/app/extrator-ui-v4611.js?v=4.6.11"></script>'
        bridge = '<script src="/app/source-local-bridge.js"></script>'
        review = '<script src="/app/revisao-v4611.js?v=4.6.11"></script>'
        diagnostic = '<script src="/app/diagnostico-v467.js?v=4.6.11"></script>'
        if bridge not in html:
            html = html.replace(patched_ui, f"{bridge}\n  {patched_ui}")
        if review not in html:
            html = html.replace(patched_ui, f"{review}\n  {patched_ui}")
        if diagnostic not in html:
            html = html.replace(patched_ui, f"{diagnostic}\n  {patched_ui}")
        metadata = '<script src="/app/metadados-v46.js" defer></script>'
        if metadata not in html:
            html = html.replace("</body>", f"  {metadata}\n</body>")

        data = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/app/extrator-ui-v4611.js":
            data = patched_ui_source_v4611().encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path == "/app/revisao-v4611.js":
            file_path = Path(previous.legacy.base.ROOT) / "app" / "revisao-v4611.js"
            data = file_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path in {"/api/review/latest", "/api/review/current", "/api/review/file"}:
            try:
                _set_contract(self)
                query = parse_qs(urlparse(self.path).query)
                if path == "/api/review/latest":
                    kind = (query.get("kind") or [None])[0]
                    result = latest_review(Path(previous.legacy.base.ROOT), kind)
                    if result is None:
                        self.send_json(
                            HTTPStatus.NOT_FOUND,
                            {"error": "nenhuma revisão local encontrada", "database_write": False},
                        )
                    else:
                        self.send_json(HTTPStatus.OK, result)
                    return
                review_id = str((query.get("review_id") or [""])[0])
                result = get_review(Path(previous.legacy.base.ROOT), review_id)
                self.send_json(HTTPStatus.OK, result)
            except FileNotFoundError as error:
                self.send_json(
                    HTTPStatus.NOT_FOUND,
                    {"error": str(error), "database_write": False},
                )
            except Exception as error:
                self.send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": str(error), "database_write": False},
                )
            return
        super()._do_GET()

    def _do_POST(self) -> None:
        path = urlparse(self.path).path

        if path == "/api/review/stage":
            try:
                _set_contract(self)
                payload = self.read_json()
                result = stage_review(Path(previous.legacy.base.ROOT), payload)
                previous.legacy.runtime_log(
                    f"REVISAO-SALVA | id={result['review_id']} | tipo={result['kind']} | "
                    f"arquivo={result['review_file']} | database_write=false"
                )
                self.send_json(HTTPStatus.OK, result)
            except Exception as error:
                self.send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": str(error), "database_write": False},
                )
            return

        if path == "/api/review/acknowledge":
            try:
                _set_contract(self)
                payload = self.read_json()
                result = acknowledge_review(
                    Path(previous.legacy.base.ROOT),
                    str(payload.get("review_id") or ""),
                    str(payload.get("phrase") or ""),
                )
                previous.legacy.runtime_log(
                    f"REVISAO-CONFIRMADA | id={result['review_id']} | tipo={result['kind']}"
                )
                self.send_json(HTTPStatus.OK, result)
            except PermissionError as error:
                self.send_json(
                    HTTPStatus.FORBIDDEN,
                    {"error": str(error), "database_write": False},
                )
            except Exception as error:
                self.send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": str(error), "database_write": False},
                )
            return

        if path == "/api/apply":
            try:
                config = _set_contract(self)
                payload = self.read_json()
                _apply_approved(self, payload, config)
            except PermissionError as error:
                self.send_json(
                    HTTPStatus.FORBIDDEN,
                    {"error": str(error), "database_write": False},
                )
            except (RuntimeError, ValueError, KeyError, json.JSONDecodeError) as error:
                self.send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": str(error), "database_write": False},
                )
            except Exception as error:
                previous.legacy.runtime_log(
                    "APLICACAO-FALHA-FECHADA | "
                    + "".join(
                        traceback.format_exception(type(error), error, error.__traceback__)
                    ).strip()
                )
                self.send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": f"falha fechada: {error}", "database_write": False},
                )
            return

        if path == "/api/card-dimensions/apply-cached":
            lock = previous.legacy.DIMENSIONS_LOCK
            if not lock.acquire(blocking=False):
                self.send_json(
                    HTTPStatus.CONFLICT,
                    {"error": "uma aplicação de metadados já está em andamento", "database_write": False},
                )
                return
            try:
                config = _set_contract(self)
                payload = self.read_json()
                if str(payload.get("confirmation") or "").strip() != previous.legacy.REQUIRED_CONFIRMATION:
                    raise PermissionError("confirmação de metadados incorreta")
                if not previous.LAST_DIMENSIONS_REPORT or not previous.LAST_DIMENSIONS_REPORT.get("passed"):
                    raise PermissionError(
                        "aplicação de Dimensões bloqueada: a comparação desta família não foi aprovada"
                    )
                review = verify_review(
                    Path(previous.legacy.base.ROOT),
                    str(payload.get("review_id") or ""),
                    str(payload.get("review_token") or ""),
                    expected_kind="metadata",
                    family="dimensoes_cartas",
                )
                if not previous.legacy.dimensions_apply_allowed(config):
                    raise PermissionError("aplicação manual de Dimensões não está habilitada")
                snapshot = previous.legacy.LAST_DIMENSIONS
                if snapshot is None:
                    raise ValueError(
                        "execute primeiro a comparação de Metadados para gerar a fotografia física"
                    )

                base = previous.legacy.base
                psycopg, sql, _ = base.import_psycopg()
                dsn = base.connection_string()
                if not dsn:
                    raise RuntimeError("conexão segura com clube_novo indisponível")
                with psycopg.connect(dsn, connect_timeout=20) as connection:
                    with connection.transaction():
                        with connection.cursor() as cursor:
                            cursor.execute("set transaction isolation level serializable")
                        result = previous.legacy.apply_card_dimensions(
                            snapshot, connection, "clube_novo", sql
                        )
                with psycopg.connect(dsn, connect_timeout=20) as verification:
                    verification.read_only = True
                    readback = previous.legacy.readback_card_dimensions(
                        snapshot, verification, "clube_novo", sql
                    )
                self.send_json(
                    HTTPStatus.OK,
                    {
                        "applied": True,
                        "result": result,
                        "readback": readback,
                        "review": {
                            "review_id": review["review_id"],
                            "reviewed_at": review.get("reviewed_at"),
                            "payload_sha256": review.get("payload_sha256"),
                        },
                        "database_write": True,
                        "next": "aplicar_cards_depois_dos_metadados",
                    },
                )
            except PermissionError as error:
                self.send_json(
                    HTTPStatus.FORBIDDEN,
                    {"error": str(error), "database_write": False},
                )
            except (RuntimeError, ValueError, OSError, json.JSONDecodeError) as error:
                self.send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": str(error), "database_write": False},
                )
            except Exception as error:
                previous.legacy.runtime_log(
                    "DIMENSOES-FALHA-FECHADA | "
                    + "".join(
                        traceback.format_exception(type(error), error, error.__traceback__)
                    ).strip()
                )
                self.send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": f"falha fechada: {error}", "database_write": False},
                )
            finally:
                lock.release()
            return

        super()._do_POST()


def validate_runtime() -> None:
    previous.validate_runtime_patches()
    source = patched_ui_source_v4611()
    for marker in (
        "CLUBEF_REVIEW.stage",
        "requireCredentials",
        "relationsExact",
    ):
        if marker not in source:
            raise RuntimeError(f"patch V4.6.11 incompleto: {marker}")
    review_script = Path(previous.legacy.base.ROOT) / "app" / "revisao-v4611.js"
    if not review_script.is_file():
        raise RuntimeError(f"painel de revisão ausente: {review_script}")
    previous.legacy.runtime_log(
        f"Camada de revisão V4.6.11 validada: ui_js={len(source)} bytes; "
        f"frase={ACKNOWLEDGEMENT_PHRASE}; database_write=false até confirmação"
    )


def main() -> None:
    host = "127.0.0.1"
    port = int(
        previous.legacy.base.os.environ.get(
            "CLUBEF_EXTRACTOR_PORT",
            str(DEFAULT_PORT),
        )
    )
    validate_runtime()
    server = previous.legacy.LoggedThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}/Extrator-ClubEfootball.html"
    try:
        config_source = previous.legacy.base.load_config().get("_source")
    except Exception as error:
        config_source = f"erro: {type(error).__name__}: {error}"
    previous.legacy.runtime_log(
        f"Servidor iniciado em {url}; pid={previous.legacy.os.getpid()}; "
        f"raiz={previous.legacy.base.ROOT}; config={config_source}; "
        f"revisoes={Path(previous.legacy.base.ROOT) / 'revisoes-pendentes'}"
    )
    if previous.legacy.base.sys.stdout is not None:
        print(f"Extrator eFootball V{RUNTIME_VERSION} disponível em {url}")
        print("A fotografia é salva localmente e precisa ser revisada antes de qualquer escrita.")
    if "--no-browser" not in previous.legacy.base.sys.argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        previous.legacy.runtime_log("Servidor encerrado por KeyboardInterrupt.")
    finally:
        server.server_close()
        previous.legacy.runtime_log("Servidor local encerrado.")


if __name__ == "__main__":
    main()
