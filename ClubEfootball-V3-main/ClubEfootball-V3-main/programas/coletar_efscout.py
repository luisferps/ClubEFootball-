# -*- coding: utf-8 -*-
"""
COLETA DO efSCOUT — a fonte nova (09/08/2026).

POR QUE: a API do efHub morreu (403 ate no navegador logado). O efscout.app usa o
MESMO id numerico da Konami e entrega o que faltava:
   · a CAMPANHA (box) de cada card          -> konamiSections[].title
   · a CLASSE do card (player_type)         -> a TRAVA 2 do ACHADO-0708
   · o catalogo de impetos                  -> referenceData.allBoosters
   · e a base inteira em dois arquivos      -> players.bin / metadata.bin

O QUE ESTE SCRIPT FAZ (so baixa e organiza, nao mexe em nada do sistema):
   1. baixa o boot.json e grava efscout_boot.json
   2. extrai as campanhas -> efscout_campanhas.json  (campanha -> ids + player_type)
   3. extrai o catalogo de impetos -> efscout_boosters.json
   4. baixa players.bin e metadata.bin (binarios, para decodificar depois)
   5. cruza os ids com o nosso dados/cards.json e diz quantos casaram

Rode e deixe rodando. Nao precisa fechar o motor.
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
import json, os, sys, io, time, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(_CASA or os.path.dirname(os.path.abspath(__file__)))

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36')
CAB = {'User-Agent': UA, 'Accept': '*/*',
       'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
       'Referer': 'https://efscout.app/'}


def pega(url, tentativas=6):
    ultimo = None
    for k in range(tentativas):
        try:
            req = urllib.request.Request(url, headers=CAB)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:
            ultimo = e
            print('   tentativa %d falhou (%s) — esperando...' % (k + 1, e))
            time.sleep(2.0 * (k + 1))
    raise IOError('%s -> %s' % (url, ultimo))


print('=' * 70)
print('  COLETA DO efSCOUT')
print('=' * 70)

print('[1/5] boot.json ...')
b = pega('https://efscout.app/data/boot.json')
open('efscout_boot.json', 'wb').write(b)
J = json.loads(b.decode('utf-8'))
ver = J.get('dataVersion')
print('      gravado: efscout_boot.json (%.1f MB) · dataVersion %s'
      % (len(b) / 1048576.0, ver))

print('      chaves da raiz: %s' % ', '.join(list(J.keys())[:14]))
for _k, _v in J.items():
    if isinstance(_v, dict):
        print('        %s -> %s' % (_k, ', '.join(list(_v.keys())[:12])))

print('[2/5] campanhas (konamiSections) ...')


def acha(o, chave, prof=0):
    """procura a chave em qualquer nivel do JSON — o konamiSections nao esta na raiz."""
    if prof > 4: return None
    if isinstance(o, dict):
        if chave in o: return o[chave]
        for v in o.values():
            r = acha(v, chave, prof + 1)
            if r is not None: return r
    elif isinstance(o, list):
        for v in o[:50]:
            r = acha(v, chave, prof + 1)
            if r is not None: return r
    return None


secs = acha(J, 'konamiSections') or []
print('      achei konamiSections: %d secoes' % (len(secs) if hasattr(secs, '__len__') else 0))
if not secs:
    # plano B: as `variations` da home costumam trazer os cards com player_type
    var = acha(J, 'variations')
    if var:
        print('      konamiSections vazio — usando `variations` (%d itens)'
              % (len(var) if hasattr(var, '__len__') else 0))
        secs = [{'title': 'variations (home)', 'players': var}]
camp, tipos = {}, {}
for s in secs:
    t = s.get('title') or '?'
    ids = []
    for p in (s.get('players') or s.get('cards') or []):
        pid = str(p.get('player_id') or p.get('id') or p.get('playerId') or '')
        if not pid or pid == 'None': continue
        ids.append(pid)
        _t = p.get('player_type', p.get('playerType', p.get('type')))
        if _t is not None:
            tipos[pid] = _t
    camp[t] = ids
json.dump({'dataVersion': ver, 'campanhas': camp, 'player_type': tipos},
          open('efscout_campanhas.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('      campanhas: %d · cards: %d · com classe (player_type): %d'
      % (len(camp), sum(len(v) for v in camp.values()), len(tipos)))
for t, ids in list(camp.items())[:14]:
    print('        %-44s %d cards' % (t[:44], len(ids)))

print('[3/5] catalogo de impetos (referenceData.allBoosters) ...')
ref = (J.get('referenceData') or {})
bo = ref.get('allBoosters')
if bo is not None:
    json.dump(bo, open('efscout_boosters.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    n = len(bo) if hasattr(bo, '__len__') else '?'
    print('      gravado: efscout_boosters.json (%s itens)' % n)
else:
    print('      nao achei allBoosters no boot.json')

print('[4/5] players.bin e metadata.bin (binarios, para decodificar depois) ...')
for nome in ('metadata.bin', 'players.bin'):
    url = 'https://efscout.app/data/%s?v=%s' % (nome, ver)
    d = pega(url)
    open('efscout_' + nome, 'wb').write(d)
    print('      efscout_%-14s %.1f MB' % (nome, len(d) / 1048576.0))

print('[5/5] cruzando com o nosso cards.json ...')
try:
    nossos = {str(c['id']).split('@')[0] for c in
              json.load(open('dados/cards.json', encoding='utf-8'))}
    todos = {i for v in camp.values() for i in v}
    print('      ids do efscout nas campanhas .. %d' % len(todos))
    print('      desses, ja temos na base ...... %d' % len(todos & nossos))
    print('      NOVOS (nao temos) ............. %d' % len(todos - nossos))
except Exception as e:
    print('      nao consegui cruzar: %s' % e)

print()
print('PRONTO. Me avise e me diga os numeros que apareceram.')
try:
    if sys.stdin and sys.stdin.isatty(): input('Enter para fechar...')
except Exception: pass
