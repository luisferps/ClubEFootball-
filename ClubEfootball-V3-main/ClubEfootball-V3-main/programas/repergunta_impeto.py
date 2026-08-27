# -*- coding: utf-8 -*-
"""
REPERGUNTA O IMPETO — o que ficou sem resposta volta a ser perguntado.

ORDEM DO LUIS, 14/08/2026:
    "Pode ser que apareca ou nao apareca o impeto na hora. O pessoal demora pra
     atualizar as vezes. Eu preciso consultar em varios pontos."
    "Se ele for atualizando todo dia, se aparecer um impeto novo ele pega tambem."

O PROBLEMA QUE ISSO RESOLVE
    Fonte em branco hoje nao quer dizer "esse card nao tem impeto". Quer dizer
    "hoje eu nao sei". Card novo entra no efHub antes de o efScout catalogar o
    impeto dele. Se o sistema tratar isso como resposta final, o card fica com a
    nota por baixo PARA SEMPRE, e ninguem nunca mais pergunta.

O QUE ELE FAZ (so leitura + um arquivo de pendencia)
    1. le a base unica ja refeita, com o catalogo do dia
    2. separa os cards sem impeto resolvido em TRES caixas:

       ORFAO      o card tem numero de impeto e o catalogo nao conhece
                  -> resolve conferindo UMA vez no jogo. O numero serve para
                     TODOS os cards que usam esse mesmo impeto.
                  (foi o caso do Eden Hazard: boostId 1834 = Rompe-barreira +4)

       EM BRANCO  nenhuma fonte sabe. Pode nao ter, pode ser atraso da fonte.
                  -> pergunta de novo amanha. Nao vira resposta.

       CONFERIDO  o Luis ja olhou no jogo. Sai da lista para sempre.

    3. compara com a rodada de ontem e diz o que se RESOLVEU no dia
    4. grava IMPETO-PERGUNTAR-DE-NOVO.txt

    Nao muda card, nao muda fila, nao roda motor.
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
import json, os, sys, io, collections, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(_CASA or os.path.dirname(os.path.abspath(__file__)))

BASE = os.path.join('dados', 'base_unica.json')
HIST = 'impeto_pendencia_historico.json'
SAIDA = 'IMPETO-PERGUNTAR-DE-NOVO.txt'

if not os.path.exists(BASE):
    print('nao achei o %s. Rode o UNIFICAR-BASE antes.' % BASE)
    raise SystemExit(1)

B = json.load(open(BASE, encoding='utf-8'))
cards = [c for c in (B.get('cards') or []) if '@' not in str(c.get('id'))]

# o catalogo de impetos, recem-atualizado pela coleta do dia
CAT = {}
try:
    for b in json.load(open('efscout_boosters.json', encoding='utf-8')):
        if isinstance(b, dict) and 'id' in b:
            CAT[int(b['id'])] = b.get('name')
except Exception:
    pass

orfaos = collections.defaultdict(list)   # boostId -> [(id, nome, ovr)]
branco = []
conferido = []

for c in cards:
    fdc = c.get('fonte_de_cada_campo') or {}
    if fdc.get('nm') == 'CONFERIDO':
        conferido.append(c)
        continue
    if c.get('nm'):
        continue                                    # resolvido
    if not (c.get('sl') and c['sl'][1] == 1):
        continue                                    # nem vaga tem
    bid = c.get('boostId') or 0
    try:
        bid = int(bid)
    except Exception:
        bid = 0
    if bid and bid not in CAT:
        orfaos[bid].append((str(c['id']), c.get('nome'), c.get('ovr') or 0))
    else:
        branco.append((str(c['id']), c.get('nome'), c.get('ovr') or 0, bid))

ontem = {}
if os.path.exists(HIST):
    try:
        ontem = json.load(open(HIST, encoding='utf-8'))
    except Exception:
        ontem = {}

hoje = {
    'quando': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
    'orfaos': sorted(orfaos),
    'n_orfaos_cards': sum(len(v) for v in orfaos.values()),
    'n_branco': len(branco),
    'n_conferido': len(conferido),
    'ids_pendentes': sorted([x[0] for x in branco] + [x[0] for v in orfaos.values() for x in v]),
}

L = []
def P(*a):
    t = ' '.join(str(x) for x in a); print(t, flush=True); L.append(t)

P('=' * 74)
P('  IMPETO — O QUE AINDA NAO TEM RESPOSTA   %s' % hoje['quando'])
P('=' * 74)
P('')
P('  ⛔ Fonte em branco NAO e resposta. Card novo demora a aparecer nas')
P('     fontes; por isso estes voltam a ser perguntados todo dia.')
P('')
P('  IMPETO ORFAO (o card tem impeto, o catalogo nao conhece) ... %d cards'
  % hoje['n_orfaos_cards'])
P('     em %d impetos diferentes — conferir UM resolve todos os cards dele'
  % len(orfaos))
P('  EM BRANCO (nenhuma fonte sabe; pergunta de novo amanha) ... %d cards'
  % hoje['n_branco'])
P('  JA CONFERIDO NO JOGO (sai da lista para sempre) ........... %d cards'
  % hoje['n_conferido'])

if ontem:
    antes = set(ontem.get('ids_pendentes') or [])
    agora = set(hoje['ids_pendentes'])
    resolvidos = antes - agora
    novos = agora - antes
    P('')
    P('-' * 74)
    P('DESDE A RODADA ANTERIOR (%s)' % ontem.get('quando', '?'))
    P('-' * 74)
    P('  resolvidos ..... %d' % len(resolvidos))
    P('  entraram novos . %d' % len(novos))
    if resolvidos:
        P('  (a coleta do dia trouxe a resposta destes — nada a fazer)')

if orfaos:
    P('')
    P('-' * 74)
    P('OS IMPETOS ORFAOS — conferir UM no jogo resolve TODOS os cards dele')
    P('-' * 74)
    for bid, li in sorted(orfaos.items(), key=lambda t: -len(t[1])):
        li.sort(key=lambda x: -x[2])
        P('')
        P('  impeto numero %s ..... %d cards' % (bid, len(li)))
        P('     abra um destes no jogo e me diga o nome e o numero:')
        for i, n, o in li[:5]:
            P('        %-17s %-26s ovr %s' % (i, (n or '?')[:26], o))
        if len(li) > 5:
            P('        ... e mais %d que usam o mesmo impeto' % (len(li) - 5))

if branco:
    P('')
    P('-' * 74)
    P('EM BRANCO — os 20 melhores (a lista inteira esta neste arquivo)')
    P('-' * 74)
    branco.sort(key=lambda x: -x[2])
    for i, n, o, bid in branco[:20]:
        P('   %-17s %-26s ovr %-3s' % (i, (n or '?')[:26], o))
    P('')
    P('   ... %d no total.' % len(branco))

P('')
P('=' * 74)
P('  Nada foi alterado. Isto e so a lista do que perguntar de novo.')
P('=' * 74)

open(SAIDA, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
json.dump(hoje, open(HIST, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\nGravado: %s' % SAIDA)
