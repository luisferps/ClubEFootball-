# -*- coding: utf-8 -*-
"""Bootstrap do serviço portátil do Otimizador.

É compilado em ``runtime/OtimizadorServico.exe``. O executável não contém segredo:
ele recebe a raiz operacional do lançador e lê ``config.txt`` apenas localmente.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Import explícito: garante que o runtime portátil carregue o NumPy de que a
# equação aprovada precisa, sem depender de Python ou pacotes no outro computador.
import numpy as _numpy  # noqa: F401


def raiz_operacional() -> Path:
    informada = os.environ.get("CLUBEF_OTIMIZADOR_ROOT", "").strip()
    if informada:
        return Path(informada).expanduser().resolve()
    if getattr(sys, "frozen", False):
        # O serviço fica em ``OTIMIZADOR/runtime``; a raiz é a pasta pai.
        return Path(sys.executable).resolve().parent.parent
    return Path(__file__).resolve().parent


def main() -> int:
    raiz = raiz_operacional()
    interface = raiz / "interface"
    if not (interface / "servidor.py").is_file():
        raise RuntimeError("pacote do Otimizador incompleto: interface\\servidor.py não encontrada")
    os.environ["CLUBEF_OTIMIZADOR_ROOT"] = str(raiz)
    if str(interface) not in sys.path:
        sys.path.insert(0, str(interface))
    import servidor

    porta = int(os.environ.get("CLUBEF_OTIMIZADOR_PORT") or "8769")
    print(f"Serviço portátil do Otimizador: http://127.0.0.1:{porta}", flush=True)
    servidor.criar_servidor(porta=porta).serve_forever()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(0)
    except Exception as erro:
        print(f"ERRO DO SERVIÇO PORTÁTIL: {erro}", file=sys.stderr, flush=True)
        raise SystemExit(2)
