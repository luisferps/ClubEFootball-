"""Hotfix operacional da V4.6.12.

Mantém a leitura orientada pelo banco e a conferência antes da escrita, mas
impede que Cartas e Metadados iniciem juntos assim que a página abre. A abertura
faz apenas descoberta leve das fontes; a varredura pesada começa por botão e
roda uma família por vez.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path


EXECUTOR_DIR = Path(__file__).resolve().parent
ROOT = EXECUTOR_DIR.parent
VENDOR = EXECUTOR_DIR / "vendor"

if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

os.environ["PYTHONPATH"] = str(VENDOR)
os.environ.setdefault("PYTHONUNBUFFERED", "1")
# Porta nova para não reutilizar uma execução travada da tentativa anterior.
os.environ["CLUBEF_EXTRACTOR_PORT"] = "8779"
os.environ.setdefault("CLUBEF_EXTRACTOR_RUNTIME_VERSION", "4.6.12")
os.environ.setdefault(
    "CLUBEF_EXTRACTOR_LOG",
    str(ROOT / "logs" / "extrator-v46.log"),
)

# A descoberta das fontes continua sendo feita pelo próprio Extrator.
for key in (
    "CLUBEF_SOURCE_DT870_UPDATED",
    "CLUBEF_SOURCE_DT200",
    "CLUBEF_SOURCE_DT870_ORIGINAL",
    "CLUBEF_SOURCE_DT261_BRA",
    "CLUBEF_ENABLE_REAL_WRITE",
):
    os.environ.pop(key, None)

import servidor_v4612 as runtime  # noqa: E402


_original_replace_literal_once = runtime._replace_literal_once


def _replace_literal_once_compatible(
    source: str,
    old: str,
    new: str,
    label: str,
) -> str:
    """Aceita o formato real do bloco isolado de Dimensões."""
    if label == "validação responsiva de Dimensões" and source.count(old) == 0:
        alternative_old = (
            "  dimensionStructure = "
            "core.validateCardDimensionsSnapshot(dimensionSnapshot);"
        )
        alternative_new = (
            "  dimensionStructure = await "
            "core.validateCardDimensionsSnapshotResponsive(dimensionSnapshot);"
        )
        count = source.count(alternative_old)
        if count != 1:
            raise RuntimeError(
                "patch V4.6.12 não encontrou o bloco real de Dimensões "
                f"(encontrados={count})"
            )
        return source.replace(alternative_old, alternative_new, 1)

    return _original_replace_literal_once(source, old, new, label)


runtime._replace_literal_once = _replace_literal_once_compatible
_original_patched_ui_source = runtime.patched_ui_source


def _replace_regex_once(
    source: str,
    pattern: str,
    replacement: str,
    label: str,
) -> str:
    updated, count = re.subn(
        pattern,
        lambda _match: replacement,
        source,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        raise RuntimeError(
            f"hotfix de interface não encontrou trecho único: {label} "
            f"(encontrados={count})"
        )
    return updated


_MANUAL_SUMMARY = r'''  function renderAutomaticSummary() {
    const cards = state.automatic.cards || { state: 'idle' };
    const metadata = state.automatic.metadata || { state: 'idle' };
    const renderOne = (name, item) => {
      const badge = $(`${name}-update-badge`);
      const summary = $(`${name}-auto-summary`);
      const currentState = item.state || 'idle';
      badge.className = `update-badge ${currentState === 'ready' ? (item.pending ? 'pending' : 'ok') : (currentState === 'error' ? 'error' : (currentState === 'idle' ? 'ok' : 'loading'))}`;
      badge.textContent = currentState === 'loading'
        ? 'Verificando…'
        : currentState === 'error'
          ? 'Atenção necessária'
          : currentState === 'idle'
            ? 'Pronto para iniciar'
            : (item.pending ? 'Divergências encontradas' : 'Conferido');
      summary.textContent = item.message || (currentState === 'idle' ? 'Fonte localizada; aguardando sua ordem para comparar.' : '');
    };
    renderOne('cards', cards);
    renderOne('metadata', metadata);
    const running = cards.state === 'loading' || metadata.state === 'loading';
    const failed = cards.state === 'error' || metadata.state === 'error';
    const idle = cards.state === 'idle' || metadata.state === 'idle';
    const pending = Boolean(cards.pending || metadata.pending);
    const badge = $('overall-update-badge');
    badge.className = `update-badge ${running ? 'loading' : (failed || pending ? 'pending' : 'ok')}`;
    badge.textContent = running ? 'Verificando…' : (failed ? 'Atenção necessária' : (idle ? 'Pronto para iniciar' : (pending ? 'Conferência disponível' : 'Concluído')));
    if (running) {
      setOperationStatus('automatic-summary-status', 'loading', 'Varredura em andamento', 'Uma operação por vez para manter a interface respondendo. Nada será enviado automaticamente.');
    } else if (failed) {
      setOperationStatus('automatic-summary-status', 'error', 'A varredura terminou com avisos', 'Abra os detalhes. Nenhuma escrita foi feita.');
    } else if (idle) {
      setOperationStatus('automatic-summary-status', 'success', 'Fontes localizadas — pronto para iniciar', 'Clique em “Iniciar varredura”. Metadados e Cartas serão processados em sequência, nunca ao mesmo tempo.');
    } else if (pending) {
      setOperationStatus('automatic-summary-status', 'error', 'Conferência disponível', 'Revise as divergências abaixo. O envio continua manual e separado.');
    } else {
      setOperationStatus('automatic-summary-status', 'success', 'Varredura concluída', 'As famílias executadas foram conferidas e nenhuma escrita automática ocorreu.');
    }
  }
'''


_LIGHT_REFRESH_SOURCES = r'''  async function refreshSources() {
    if (state.sourcesRunning || state.applying || state.incrementalRunning || state.metadataRunning) return;
    if (state.readingContract.status !== 'ready') {
      updateRunAvailability();
      return;
    }
    state.sourcesRunning = true;
    $('refresh-sources').disabled = true;
    $('refresh-sources').textContent = 'Procurando…';
    state.incremental = null;
    state.metadata = null;
    state.cardPackage = null;
    $('result-incremental').hidden = true;
    $('result-metadata').hidden = true;
    $('apply-card-package').hidden = true;
    state.automatic.cards = { state: 'loading', pending: false, message: 'Localizando a fonte de cartas, sem iniciar a leitura pesada…' };
    state.automatic.metadata = { state: 'loading', pending: false, message: 'Localizando as fontes de metadados, sem iniciar a leitura pesada…' };
    renderAutomaticSummary();
    for (const role of Object.keys(SOURCE_SPECS)) state.sources[role] = { status: 'loading' };
    renderSources();
    try {
      const response = await fetchWithContract('/api/sources/status', { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const discovery = await response.json();
      for (const role of Object.keys(SOURCE_SPECS)) {
        const found = discovery.sources && discovery.sources[role];
        if (!found || !found.found) {
          state.sources[role] = { status: 'missing', reason: found && found.reason ? found.reason : 'Fonte não encontrada nos locais conhecidos.' };
        } else {
          state.sources[role] = {
            status: 'ready',
            bytes: null,
            byteLength: Number(found.bytes || 0),
            name: found.filename,
            modifiedAt: found.modified_at,
            origin: 'automatic',
            sha256: null,
            validation: { valid_container: true, discovery_only: true }
          };
        }
        renderSources();
        await new Promise((resolve) => setTimeout(resolve, 0));
      }
      await refreshCardReference();
      state.automatic.cards = {
        state: operationIsReady(CARD_SOURCE_ROLES) ? 'idle' : 'error',
        pending: false,
        message: operationIsReady(CARD_SOURCE_ROLES)
          ? 'DT870 localizado. Aguardando você iniciar a comparação.'
          : 'O DT870 atualizado não foi localizado.'
      };
      state.automatic.metadata = {
        state: operationIsReady(METADATA_SOURCE_ROLES) ? 'idle' : 'error',
        pending: false,
        message: operationIsReady(METADATA_SOURCE_ROLES)
          ? 'As quatro fontes foram localizadas. Aguardando você iniciar a comparação.'
          : 'Uma ou mais fontes de metadados não foram localizadas.'
      };
    } catch (error) {
      for (const role of Object.keys(SOURCE_SPECS)) {
        state.sources[role] = { status: 'missing', reason: `A busca automática não respondeu: ${error.message}` };
      }
      state.automatic.cards = { state: 'error', pending: false, message: `Fontes: ${error.message}` };
      state.automatic.metadata = { state: 'error', pending: false, message: `Fontes: ${error.message}` };
      renderSources();
    } finally {
      state.sourcesRunning = false;
      $('refresh-sources').disabled = false;
      $('refresh-sources').textContent = 'Procurar novamente';
      updateRunAvailability();
      if (operationIsReady(CARD_SOURCE_ROLES)) {
        setOperationStatus('incremental-status', 'success', 'Cartas prontas para comparar', 'Clique em “Comparar agora” ou use “Iniciar varredura”.');
      }
      if (operationIsReady(METADATA_SOURCE_ROLES)) {
        setOperationStatus('metadata-status', 'success', 'Metadados prontos para comparar', 'A leitura pesada só começará quando você mandar.');
      }
      renderAutomaticSummary();
    }
  }
'''


_NO_AUTO_INCREMENTAL = r'''  async function maybeStartIncrementalComparison(trigger) {
    if (state.incremental || state.incrementalRunning) return;
    updateRunAvailability();
    if (state.sourcesRunning) {
      setOperationStatus('incremental-status', 'loading', 'Localizando a fonte de cartas', 'Aguarde somente a descoberta dos arquivos.');
      return;
    }
    if (state.executor.online && state.executor.database_configured && operationIsReady(CARD_SOURCE_ROLES)) {
      setOperationStatus('incremental-status', 'success', 'Cartas prontas para comparar', 'A comparação não começa sozinha. Clique em “Comparar agora” ou em “Iniciar varredura”.');
      state.automatic.cards = { state: 'idle', pending: false, message: 'Fonte localizada; aguardando sua ordem para comparar.' };
      renderAutomaticSummary();
    }
  }
'''


_MANUAL_BUTTON = r'''  function installManualScanButton() {
    if ($('run-complete-scan')) return;
    const summary = $('automatic-summary');
    if (!summary) return;
    const holder = document.createElement('div');
    holder.className = 'toolbar';
    holder.style.marginTop = '14px';
    holder.innerHTML = '<button id="run-complete-scan" class="primary" type="button">Iniciar varredura</button><small id="run-complete-scan-note" style="display:block;opacity:.78;margin-top:8px">Primeiro Metadados; depois Cartas. Uma operação por vez.</small>';
    summary.appendChild(holder);
    const button = $('run-complete-scan');
    button.addEventListener('click', async () => {
      if (state.sourcesRunning || state.metadataRunning || state.incrementalRunning || state.applying) return;
      button.disabled = true;
      button.textContent = 'Varredura em andamento…';
      try {
        if (state.readingContract.status !== 'ready') await refreshExecutorStatus();
        if (!operationIsReady(METADATA_SOURCE_ROLES)) await refreshSources();
        if (!operationIsReady(METADATA_SOURCE_ROLES)) throw new Error('As quatro fontes oficiais não estão prontas.');
        await refreshMetadataAutomatically('botão Iniciar varredura');
        if (!operationIsReady(CARD_SOURCE_ROLES)) throw new Error('A fonte de cartas não está pronta.');
        await runIncrementalComparison('botão Iniciar varredura');
      } catch (error) {
        setOperationStatus('automatic-summary-status', 'error', 'Não foi possível concluir a varredura', `${error.message} Nenhuma escrita foi feita.`);
      } finally {
        button.disabled = false;
        button.textContent = 'Iniciar nova varredura';
      }
    });
  }
'''


def patched_ui_source_sequential() -> str:
    source = _original_patched_ui_source()

    source = _replace_regex_once(
        source,
        r"  function renderAutomaticSummary\(\) \{.*?\n  function download\(",
        _MANUAL_SUMMARY + "  function download(",
        "resumo manual da abertura",
    )
    source = _replace_regex_once(
        source,
        r"  async function refreshSources\(\) \{.*?\n  \$\('refresh-sources'\)\.addEventListener",
        _LIGHT_REFRESH_SOURCES + "  $('refresh-sources').addEventListener",
        "descoberta leve das fontes",
    )
    source = _replace_regex_once(
        source,
        r"  async function maybeStartIncrementalComparison\(trigger\) \{.*?\n  async function runIncrementalComparison\(trigger\) \{",
        _NO_AUTO_INCREMENTAL + "  async function runIncrementalComparison(trigger) {",
        "remoção da comparação automática",
    )

    source = source.replace(
        "  async function runIncrementalComparison(trigger) {\n    if (state.incrementalRunning) return;",
        "  async function runIncrementalComparison(trigger) {\n    if (state.incrementalRunning || state.metadataRunning || state.sourcesRunning || state.applying) return;",
        1,
    )
    source = source.replace(
        "  async function refreshMetadataAutomatically(trigger = 'abertura automática') {\n    if (state.metadataRunning) return;",
        "  async function refreshMetadataAutomatically(trigger = 'ação manual') {\n    if (state.metadataRunning || state.incrementalRunning || state.sourcesRunning || state.applying) return;",
        1,
    )
    source = source.replace(
        "      const source = state.sources.dt870_updated;\n      const baseline = await fetchCurrentCardBaseline();",
        "      await ensureSourceBytes('dt870_updated');\n      const source = state.sources.dt870_updated;\n      const baseline = await fetchCurrentCardBaseline();",
        1,
    )

    if "await ensureSourceBytes('dt870_updated');" not in source:
        raise RuntimeError("hotfix não inseriu a leitura sob demanda do DT870")
    if "state.incrementalRunning || state.metadataRunning" not in source:
        raise RuntimeError("hotfix não serializou a comparação de cartas")

    source = source.replace(
        "  refreshExecutorStatus().then(async () => {",
        _MANUAL_BUTTON + "  installManualScanButton();\n  refreshExecutorStatus().then(async () => {",
        1,
    )
    if "run-complete-scan" not in source:
        raise RuntimeError("hotfix não instalou o botão de varredura sequencial")

    return source.replace(
        "//# sourceURL=/app/extrator-ui-v4612.js",
        "//# sourceURL=/app/extrator-ui-v4612-sequencial.js",
    )


runtime.patched_ui_source = patched_ui_source_sequential


if __name__ == "__main__":
    runtime.main()
