# -*- coding: utf-8 -*-
"""
COLETAR BOX E DATA — de onde cada carta saiu, e quando.

SO LE a internet e o cards.json. NAO altera o cards.json, NAO mexe na fila,
NAO manda nada pro banco. Escreve um arquivo NOVO: box_por_card.json

POR QUE (medido em 10/08):
    boxes registradas na fila ..... 11
    cards com data (campo dt) ..... 0 de 2.589   <- o campo existe e esta VAZIO
Sem data nao da pra separar box ATIVA de box ENCERRADA, nem montar a tabela de
"qual carta saiu em qual box". E a box nova (Encored AC Milan) nem chegou a ter
o nome gravado nas cartas.

A FONTE, na mesma rota da vaga de impeto:
    api.efootballdb.com/api/2022/players/{id}
      "variation_details": { "name": "Big Time France 9 Jul '26",
                             "release_date": "2026-07-23" }

Nome da box E data, por carta. ~2.589 cartas, ~20 min.
Pode fechar e reabrir: retoma de onde parou.
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
import json, os, sys, io, time, urllib.request, collections


def P(*a):
    print(*a, flush=True)


os.chdir(_CASA or os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors='replace', line_buffering=True)
except Exception:
    pass

ROTA = 'https://api.efootballdb.com/api/2022/players/%s'
CAB = {'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'),
       'Accept': 'application/json', 'Referer': 'https://www.efootballdb.com/'}
SAIDA = 'box_por_card.json'
CARDS = 'dados/cards.json'
PAUSA = 0.15


def pega(pid):
    req = urllib.request.Request(ROTA % pid, headers=CAB)
    with urllib.request.urlopen(req, timeout=25) as r:
        j = json.loads(r.read().decode('utf-8', 'replace'))
    d = j.get('data', j) if isinstance(j, dict) else j
    if isinstance(d, list):
        d = d[0] if d else None
    return d if isinstance(d, dict) else None


if not os.path.exists(CARDS):
    P('NAO ACHEI %s. Rode da pasta do motor.' % CARDS); raise SystemExit
C = json.load(open(CARDS, encoding='utf-8'))
BASE = {}
for c in C:
    BASE.setdefault(str(c['id']).split('@')[0], c)
IDS = [b for b in BASE if b.isdigit()]

P('=' * 76)
P('  COLETA DE BOX E DATA DE LANCAMENTO')
P('=' * 76)
P('cartas base ............. %d' % len(IDS))

B = {}
if os.path.exists(SAIDA):
    try:
        B = json.load(open(SAIDA, encoding='utf-8'))
        P('ja coletadas ............ %d' % len(B))
    except Exception:
        B = {}
faltam = [b for b in IDS if b not in B]

if faltam:
    P('faltam .................. %d  (~%d min)' % (len(faltam), int(len(faltam) * .5 / 60 + 1)))
    P('-' * 76)
    erros = 0
    for k, pid in enumerate(faltam, 1):
        try:
            x = pega(pid)
        except Exception:
            x = None; erros += 1
        if x:
            vd = x.get('variation_details') or {}
            if not isinstance(vd, dict):
                vd = {}
            B[pid] = {'box': vd.get('name'), 'dt': vd.get('release_date'),
                      'nm': x.get('player_name')}
        else:
            B[pid] = {'box': None, 'dt': None}
        if k % 25 == 0:
            json.dump(B, open(SAIDA, 'w', encoding='utf-8'), ensure_ascii=False)
            P('   %5d / %5d   erros %d' % (k, len(faltam), erros))
        time.sleep(PAUSA)
    json.dump(B, open(SAIDA, 'w', encoding='utf-8'), ensure_ascii=False)
    P('coletado. %s tem %d cartas.' % (SAIDA, len(B)))
else:
    P('coleta ja completa (apague o %s para refazer)' % SAIDA)

# ------------------------------------------------------------------ relatorio
com_box = sum(1 for r in B.values() if r.get('box'))
com_dt = sum(1 for r in B.values() if r.get('dt'))
P()
P('cartas com NOME da box .. %d de %d' % (com_box, len(B)))
P('cartas com DATA ......... %d de %d' % (com_dt, len(B)))

cx = collections.defaultdict(lambda: {'n': 0, 'dts': set()})
for b, r in B.items():
    if not r.get('box'):
        continue
    cx[r['box']]['n'] += 1
    if r.get('dt'):
        cx[r['box']]['dts'].add(r['dt'])

P()
P('BOXES ENCONTRADAS: %d' % len(cx))
P('%-44s %6s  %s' % ('BOX', 'cards', 'lancamento'))
linhas = []
for nome, d in cx.items():
    dt = min(d['dts']) if d['dts'] else ''
    linhas.append((dt, nome, d['n']))
for dt, nome, n in sorted(linhas, reverse=True):
    P('%-44s %6d  %s' % (nome[:44], n, dt or '— sem data —'))

with open('BOXES.csv', 'w', encoding='utf-8') as f:
    f.write('box;cards;lancamento\n')
    for dt, nome, n in sorted(linhas, reverse=True):
        f.write('%s;%d;%s\n' % (nome, n, dt))
P()
P('gravado: %s  ·  BOXES.csv' % SAIDA)
P('NADA foi alterado no cards.json nem na fila. Manda a tela pro Claude.')
try:
    if sys.stdin and sys.stdin.isatty(): input('Enter para fechar...')
except Exception: pass
