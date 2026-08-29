"""Hotfix de inicialização da V4.6.12.

Corrige a compatibilidade entre o bloco por família da V4.6.11 e a camada
responsiva da V4.6.12, sem alterar a lógica de extração ou de escrita.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


EXECUTOR_DIR = Path(__file__).resolve().parent
ROOT = EXECUTOR_DIR.parent
VENDOR = EXECUTOR_DIR / "vendor"

if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

os.environ["PYTHONPATH"] = str(VENDOR)
os.environ.setdefault("PYTHONUNBUFFERED", "1")
os.environ.setdefault("CLUBEF_EXTRACTOR_PORT", "8778")
os.environ.setdefault("CLUBEF_EXTRACTOR_RUNTIME_VERSION", "4.6.12")
os.environ.setdefault(
    "CLUBEF_EXTRACTOR_LOG",
    str(ROOT / "logs" / "extrator-v46.log"),
)

# A descoberta das fontes continua sendo feita pelo Extrator.
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
    """Aceita o formato real do bloco isolado de Dimensões.

    A V4.6.12 procurava a declaração original com ``const``. A V4.6.11 já
    havia substituído esse trecho por uma atribuição à variável externa
    ``dimensionStructure``. O hotfix troca exatamente essa atribuição pela
    versão assíncrona e mantém todos os demais patches fechados e validados.
    """
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


if __name__ == "__main__":
    runtime.main()
