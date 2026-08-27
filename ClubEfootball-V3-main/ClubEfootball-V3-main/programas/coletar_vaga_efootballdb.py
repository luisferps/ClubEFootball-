# -*- coding: utf-8 -*-
"""
COLETOR DA VAGA DE IMPETO — efootballdb, rota players/{id}

SO LE a internet. NAO altera cards.json, NAO mexe na fila, NAO manda pro banco.
Escreve UM arquivo novo:  vaga_por_card.json

REGRA MEDIDA (sonda 4 e 5, 09/08 — 8 de 8 conferidas no jogo):
  VAGA LIVRE ..... pes_id 136 · booster_type 4 · todas as 26 flags = 0
  NATIVO ......... booster_type 0/1/2/3 · pelo menos uma flag = 1
  NADA ........... campo null

Pode fechar e reabrir: ele retoma de onde parou (vaga_por_card.json).
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

os.chdir(_CASA or os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

ROTA = 'https://api.efootballdb.com/api/2022/players/%s'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36')
CAB = {'User-Agent': UA, 'Accept': 'application/json',
       'Referer': 'https://www.efootballdb.com/'}
SAIDA = 'vaga_por_card.json'
PAUSA = 0.15

FLAGS = ['low_pass', 'attacking_prowess', 'body_control', 'place_kicking', 'jump',
         'catching', 'aggression', 'physical_contact', 'speed', 'swerve', 'clearing',
         'reflexes', 'stamina', 'explosive_power', 'coverage', 'lofted_pass',
         'tackling', 'dribbling', 'finishing', 'kicking_power', 'goalkeeping',
         'defensive_awareness', 'defensive_engagement', 'tight_possession',
         'ball_control', 'header']


def tipo(b):
    if not isinstance(b, dict):
        return None
    if sum(b.get(f) or 0 for f in FLAGS) == 0:
        if b.get('booster_type') == 4 or b.get('pes_id') == 136:
            return 'VAGA'
        return 'ZERADO?'
    return 'NATIVO'


def pega(pid):
    req = urllib.request.Request(ROTA % pid, headers=CAB)
    with urllib.request.urlopen(req, timeout=25) as r:
        j = json.loads(r.read().decode('utf-8', 'replace'))
    d = j.get('data', j) if isinstance(j, dict) else j
    if isinstance(d, list):
        d = d[0] if d else None
    return d if isinstance(d, dict) else None


# ------------------------------------------------------------- ids
ids = []
for cam in ('dados/cards.json', 'cards.json'):
    if os.path.exists(cam):
        d = json.load(open(cam, encoding='utf-8'))
        ids = list(d.keys()) if isinstance(d, dict) else \
              [str(c.get('id') or c.get('pes_id')) for c in d]
        print('cards.json ....... %s — %d ids' % (cam, len(ids)))
        break
ids = [str(i) for i in ids if i and str(i).isdigit()]
if not ids:
    print('NAO ACHEI o cards.json. Abortando.'); raise SystemExit

feito = {}
if os.path.exists(SAIDA):
    try:
        feito = json.load(open(SAIDA, encoding='utf-8'))
        print('retomando ........ %d ja coletados' % len(feito))
    except Exception:
        feito = {}

faltam = [i for i in ids if i not in feito]
print('faltam ........... %d' % len(faltam))
print('tempo estimado ... %d min' % int(len(faltam) * (PAUSA + 0.35) / 60 + 1))
print('-' * 70)

erros = 0
for k, pid in enumerate(faltam, 1):
    try:
        x = pega(pid)
    except Exception:
        x = None; erros += 1
    if x is None:
        feito[pid] = {'v': None}
    else:
        feito[pid] = {
            'v': [tipo(x.get('booster')), tipo(x.get('booster2')), tipo(x.get('booster3'))],
            'nm': x.get('player_name'),
        }
    if k % 100 == 0:
        json.dump(feito, open(SAIDA, 'w', encoding='utf-8'), ensure_ascii=False)
        print('  %5d / %5d   erros %d' % (k, len(faltam), erros))
    time.sleep(PAUSA)

json.dump(feito, open(SAIDA, 'w', encoding='utf-8'), ensure_ascii=False)

# ------------------------------------------------------------- resumo
comb = collections.Counter()
livres = 0
for r in feito.values():
    v = r.get('v')
    if not v:
        comb['NAO RESPONDEU'] += 1; continue
    comb[' / '.join(str(t) for t in v)] += 1
    livres += sum(1 for t in v if t == 'VAGA')

print('-' * 70)
print('GRAVADO: %s   (%d cards)' % (SAIDA, len(feito)))
print()
print('COMBINACOES slot1 / slot2 / slot3:')
for k, v in comb.most_common():
    print('   %-34s %6d' % (k, v))
print()
print('TOTAL DE VAGAS DE IMPETO LIVRES: %d' % livres)
duas = sum(v for k, v in comb.items() if k.count('VAGA') > 1)
print('CARTAS COM DUAS VAGAS LIVRES:    %d   (tem que ser 0)' % duas)
print()
print('Manda a tela pro Claude. Nada foi alterado no cards.json.')
try:
    if sys.stdin and sys.stdin.isatty(): input('Enter para fechar...')
except Exception: pass
