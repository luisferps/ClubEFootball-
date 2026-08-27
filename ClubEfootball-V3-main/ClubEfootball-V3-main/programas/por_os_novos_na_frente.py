# -*- coding: utf-8 -*-
"""OS CARDS DAS BOXES NOVAS NA PONTA DA FILA — 14/08/2026

Reescreve o fila_PRIORIDADE.json:
  1o  as linhas dos 136 cards de lancamento que ainda faltam (do fila_EXTRA.json)
  2o  todo o resto que falta, do maior OVR para o menor

O motor le esse arquivo UMA VEZ, quando comeca. Entao: pare o motor, rode isto,
e comece de novo.

NAO tira nada, NAO refaz nada — so muda a ORDEM de quem ainda falta.
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
import os, sys, io, json, shutil, datetime, collections

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(_CASA or os.path.dirname(os.path.abspath(__file__)))

print('=' * 66)
print('  OS DAS BOXES NOVAS NA PONTA DA FILA')
print('=' * 66)

for a in ('fila_v6.json', 'fila_EXTRA.json', 'feitos.txt'):
    if not os.path.exists(a):
        print('\n  nao achei o %s. Nada foi alterado.' % a)
        input('\nEnter para fechar...')
        raise SystemExit

FILA = json.load(open('fila_v6.json', encoding='utf-8'))
EXTRA = json.load(open('fila_EXTRA.json', encoding='utf-8'))
feitos = set(l.strip() for l in open('feitos.txt', encoding='utf-8') if l.strip())


def chave(r):
    return '%s|%s' % (str(r['card_id']).split('@')[0], r['funcao'])


novos, vistos = [], set()
for r in EXTRA:
    k = chave(r)
    if k in feitos or k in vistos:
        continue
    vistos.add(k)
    novos.append(r)
novos.sort(key=lambda r: -(r.get('ovr') or 0))

resto = []
for r in FILA:
    k = chave(r)
    if k in feitos or k in vistos:
        continue
    vistos.add(k)
    resto.append(r)
resto.sort(key=lambda r: -(r.get('ovr') or 0))

ordem = [chave(r) for r in novos] + [chave(r) for r in resto]

carimbo = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
if os.path.exists('fila_PRIORIDADE.json'):
    shutil.copy2('fila_PRIORIDADE.json', 'fila_PRIORIDADE.json.ANTES-DOS-NOVOS-' + carimbo)
json.dump(ordem, open('fila_PRIORIDADE.json', 'w', encoding='utf-8'), ensure_ascii=False)

print()
print('  lancamentos que faltam ... %d linhas  (vao na frente)' % len(novos))
print('  o resto que falta ........ %d linhas  (por OVR, maior primeiro)' % len(resto))
print('  fila_PRIORIDADE.json ..... %d chaves' % len(ordem))
print('  copia .................... fila_PRIORIDADE.json.ANTES-DOS-NOVOS-%s' % carimbo)
print()
print('  os 10 primeiros:')
for r in novos[:10]:
    print('     %-24s %-26s ovr %s' % ((r.get('nome') or '')[:24], r['funcao'], r.get('ovr')))
print()
print('  por box, o que ainda falta:')
c = collections.Counter(r.get('box') or '?' for r in novos)
for b, n in c.most_common():
    print('     %-46s %3d' % (b[:46], n))
print()
print('=' * 66)
print('  AGORA: rode o COMECAR-TUDO.bat.')
print('=' * 66)
input('\nEnter para fechar...')
