# -*- coding: utf-8 -*-
"""
BACKUP DA BASE UNICA — copia antes de qualquer escrita.

POR QUE ESTE ARQUIVO EXISTE
---------------------------
O `unificar_base.py` reescreve o dados/base_unica.json, e o `baixar_base.py`
reescreve por cima com o que veio do banco. Se um dia uma coleta vier torta, a
base boa some junto. Este script guarda uma copia datada ANTES de qualquer
escrita, e mantem as ultimas 30 pastas.

E o mesmo padrao do `backup_horario.py` que ja roda aqui — a diferenca e que
este e um TIRO SO (roda, copia, fecha), porque ele e chamado no meio do
ALIMENTAR-TUDO, e nao um vigia que fica ligado de hora em hora.

COMO RODAR
----------
    python backup_base.py           -> faz o backup e fecha
Tambem da para chamar de outro script:  from backup_base import uma_rodada
"""

# ===========================================================================
#  ⛔ 19/08 — ESTE PROGRAMA MORA NO ClubEfootball\programas.
#     "Nao existe mais essa pasta pro futebol. A pasta agora e ClubEfootball.
#      E tudo la." (Luis, 19/08)
#
#  ⛔ ESTE BLOCO VEM ANTES DOS IMPORTS, E POR MEDIDA. Quando ele ficava
#     DEPOIS, o `from equacao import ...` la de cima ja tinha rodado e pegava
#     o arquivo errado — o programa nem chegava a saber onde estava a casa.
#
#     Ele faz duas coisas, e as duas importam:
#       1. acha a pasta que tem o config.txt e trabalha LA (os dados nao se
#          mudaram: dados\, saida_v6\, encaixe\ continuam na casa);
#       2. poe `programas\` na frente do caminho de busca, para os modulos
#          vizinhos serem achados aqui e nao na raiz.
# ===========================================================================
import os as _os, sys as _sys

def _acha_a_casa(inicio):
    p = inicio
    for _ in range(5):
        if _os.path.exists(_os.path.join(p, 'config.txt')):
            return p
        pai = _os.path.dirname(p)
        if pai == p:
            break
        p = pai
    return None

_MEU_LUGAR = _os.path.dirname(_os.path.abspath(__file__))
_CASA = _acha_a_casa(_MEU_LUGAR) or _acha_a_casa(_os.getcwd())
if _CASA:
    if _os.path.abspath(_os.getcwd()) != _os.path.abspath(_CASA):
        _os.chdir(_CASA)
    if _CASA not in _sys.path:
        _sys.path.append(_CASA)          # a casa vem DEPOIS
if _MEU_LUGAR in _sys.path:
    _sys.path.remove(_MEU_LUGAR)
_sys.path.insert(0, _MEU_LUGAR)          # `programas` vem PRIMEIRO
# --------------------------------------------------------------------------
import datetime
import os
import shutil
import sys
import io

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors='replace', line_buffering=True)
except Exception:
    pass

os.chdir(_CASA or os.path.dirname(os.path.abspath(__file__)))

# O que nao pode ser perdido quando a base e reescrita.
# Caminho relativo a pasta do motor; o que nao existir e simplesmente pulado.
ALVO = [
    'dados/base_unica.json',        # a base
    'RELATORIO-BASE-UNICA.txt',     # o relatorio da unificacao
    'RELATORIO-COMPLETUDE.txt',     # o relatorio de completude
    'precedencia.json',             # a regra de quem manda (muda pouco, pesa nada)
]
PASTA = 'backups_base'
GUARDA = 30                          # quantas pastas datadas ficam guardadas


def P(*a):
    print(*a, flush=True)


def uma_rodada(silencioso=False):
    """Copia os alvos para backups_base\\AAAA-MM-DD_HHhMM\\ e limpa as velhas.

    Devolve o caminho da pasta criada. Nunca levanta excecao por causa de um
    arquivo: se um nao copiar, avisa e continua com os outros — backup pela
    metade e melhor que backup nenhum.
    """
    os.makedirs(PASTA, exist_ok=True)
    nome = datetime.datetime.now().strftime('%Y-%m-%d_%Hh%M')
    destino = os.path.join(PASTA, nome)
    os.makedirs(destino, exist_ok=True)

    copiados = 0
    bytes_totais = 0
    for rel in ALVO:
        if not os.path.exists(rel):
            continue
        # a barra vira underline para tudo ficar plano dentro da pasta do backup
        alvo = os.path.join(destino, rel.replace('/', '_'))
        try:
            shutil.copy2(rel, alvo)
            copiados += 1
            bytes_totais += os.path.getsize(alvo)
        except Exception as erro:
            P('   nao consegui copiar %s: %s' % (rel, erro))

    if not silencioso:
        P('backup em %s  (%d arquivos, %.1f MB)'
          % (destino, copiados, bytes_totais / 1024.0 / 1024.0))

    # limpeza: como o nome e AAAA-MM-DD_HHhMM, a ordem alfabetica JA e a
    # cronologica. Sobram as GUARDA ultimas.
    velhas = sorted(d for d in os.listdir(PASTA)
                    if os.path.isdir(os.path.join(PASTA, d)))
    for d in velhas[:-GUARDA]:
        shutil.rmtree(os.path.join(PASTA, d), ignore_errors=True)
        if not silencioso:
            P('   apaguei o backup velho %s' % d)

    return destino


if __name__ == '__main__':
    P('=' * 68)
    P('  BACKUP DA BASE UNICA')
    P('=' * 68)
    P('guarda as ultimas %d copias em %s\\' % (GUARDA, PASTA))
    uma_rodada()
    P('pronto.')
