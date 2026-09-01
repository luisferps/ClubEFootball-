# -*- coding: utf-8 -*-
"""Bootstrap do serviço portátil do Otimizador.

É compilado em ``runtime/OtimizadorServico.exe``. O executável não contém segredo:
ele recebe a raiz operacional do lançador e lê ``config.txt`` apenas localmente.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# O empacotador declara NumPy como dependência do runtime. Não o importamos no
# boot: o painel de acompanhamento não depende da fórmula e precisa abrir mesmo
# quando o banco estiver em recuperação. A primeira simulação/linha autorizada
# carrega o módulo matemático aprovado sob demanda.


def raiz_operacional() -> Path:
    """Localiza a pasta ``OTIMIZADOR`` sem depender de uma máquina específica.

    O lançador normal informa a raiz por ambiente. Alguns modos legítimos de
    abertura do Windows, porém, podem não transportar esse valor ao processo
    empacotado. Em vez de concluir que o pacote está incompleto, procuramos o
    mesmo contrato físico a partir do executável, do diretório de trabalho e
    do próprio bootstrap. Isso não procura configurações nem dados fora do
    aplicativo; só aceita uma pasta que contenha ``interface/servidor.py``.
    """
    candidatas: list[Path] = []
    informada = os.environ.get("CLUBEF_OTIMIZADOR_ROOT", "").strip()
    if informada:
        candidatas.append(Path(informada).expanduser())
    if getattr(sys, "frozen", False):
        # O serviço fica em ``OTIMIZADOR/runtime``; a raiz usual é a pasta pai.
        candidatas.append(Path(sys.executable).resolve().parent.parent)
    candidatas.extend((Path.cwd(), Path(__file__).resolve().parent))

    primeira = None
    vistos: set[Path] = set()
    for base in candidatas:
        try:
            base = base.resolve()
        except OSError:
            continue
        if primeira is None:
            primeira = base
        # Uma cópia pode ser aberta por atalho, IDE ou executável portátil.
        # Em todos os casos, a raiz está no próprio caminho ou em algum pai.
        for candidata in (base, *base.parents):
            if candidata in vistos:
                continue
            vistos.add(candidata)
            if (candidata / "interface" / "servidor.py").is_file():
                return candidata
    return primeira or Path.cwd().resolve()


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
