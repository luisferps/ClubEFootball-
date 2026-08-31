# -*- coding: utf-8 -*-
"""Entrada histórica desativada.

O código anterior foi preservado somente no snapshot de recuperação anterior ao
fecho. Esta entrada não abre arquivos, não consulta banco e não executa fila.
"""

from __future__ import annotations

import sys


MENSAGEM = (
    "PAROU: a frente de legado foi encerrada. O Otimizador opera somente "
    "por contratos de clube_novo; esta entrada não pode ser reativada."
)


def main(argv=None):
    raise SystemExit(MENSAGEM)


if __name__ == "__main__":
    main(sys.argv[1:])
