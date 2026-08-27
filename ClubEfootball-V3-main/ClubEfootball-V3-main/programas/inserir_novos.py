# -*- coding: utf-8 -*-
"""
INSERE OS CARDS NOVOS DA PAGINA INICIAL DO efHUB no dados/cards.json.

Fonte: cards_efhub.json — coletado da API do efHub em 08/08/2026 pelo navegador
(/api/public/players/<id>). Os codigos (posicao, estilo, habilidade) foram cruzados
por id com o proprio cards.json: nada foi adivinhado.

Como eles vao rodar PRIMEIRO: os ids estao no lancamento_agora.json, e o
monta_fila.py poe `lancamento` como primeira chave da ordenacao — eles furam a fila
antes dos S+, exatamente a ordem que o Luis pediu.

Nao deixa entrar card meia-boca:
  - card com impeto de fabrica (sl com 0) e SEM `nm` fica FORA. O `nm` e o efeito
    do impeto de fabrica — provado na base: sl [1,1] tem nm vazio em 503/503, e
    sl [0,1] tem nm cheio em 732/732. Sem o nm a nota sai subestimada.
  - card que ja existe no cards.json nao e sobrescrito.
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
import json, os, shutil, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(_CASA or os.path.dirname(os.path.abspath(__file__)))

CARDS = 'dados/cards.json'
NOVOS = 'cards_efhub.json'


def pausa(msg='Enter para fechar...'):
    try:
        if sys.stdin and sys.stdin.isatty(): input(msg)
    except Exception: pass


for p in (CARDS, NOVOS):
    if not os.path.exists(p):
        print('NAO ACHEI', p); pausa(); sys.exit(1)

C = json.load(open(CARDS, encoding='utf-8'))
N = json.load(open(NOVOS, encoding='utf-8'))
tem = {str(c['id']).split('@')[0] for c in C}

entram, fora = [], []
for c in N:
    b = str(c['id']).split('@')[0]
    if b in tem:
        fora.append((b, c.get('nome'), 'ja estava no cards.json')); continue
    if isinstance(c.get('sl'), list) and any(x == 0 for x in c['sl']) and not c.get('nm'):
        fora.append((b, c.get('nome'), 'impeto de fabrica sem o nm — nota sairia subestimada'))
        continue
    if not c.get('base') or len(c['base']) != 26:
        fora.append((b, c.get('nome'), 'base nao tem 26 atributos')); continue
    if not c.get('np') or not c.get('modelo'):
        fora.append((b, c.get('nome'), 'sem posicao ou sem estilo')); continue
    entram.append(c)

print('no cards_efhub.json ....', len(N))
print('ENTRAM .................', len(entram))
print('ficam de fora ..........', len(fora))
for b, n, m in fora: print('   -', b, n, '|', m)
print()
if not entram:
    print('Nada para inserir.'); pausa(); sys.exit(0)

bkp = CARDS.replace('.json', '-ANTES-DOS-NOVOS.json')
if not os.path.exists(bkp):
    shutil.copy2(CARDS, bkp); print('backup ->', bkp)

C.extend(entram)
tmp = CARDS + '.tmp'
json.dump(C, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False)
os.replace(tmp, CARDS)

print('cards.json agora .......', len(C), 'registros')
for c in entram:
    print('   +', c['id'], c.get('nome'), '|', c['np'], '|', c['modelo'],
          '| orc', c['orc'], '| ovr', c['ovr'])
print()
print('PRONTO. Agora o COMECAR-TUDO.bat — eles furam a fila e rodam primeiro.')
pausa()
