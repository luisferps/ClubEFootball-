# -*- coding: utf-8 -*-
"""
REPERGUNTA TUDO — nenhum insumo em branco vira resposta.

ORDEM DO LUIS, 14/08/2026:
    "Nao e so o impeto nao, e TUDO. As habilidades tambem podem ser alteradas,
     tudo que a gente precisar de insumo, tecnicos, tudo."
    "Pode aparecer ou nao aparecer na hora. O pessoal demora pra atualizar."

A REGRA
    Campo vazio tem TRES significados, e ate hoje o sistema escrevia os tres
    igual:

      CONFERIDO   alguem checou e a resposta e "esse card nao tem".
                  -> fechado para sempre. Nunca mais se pergunta.

      NAO SEI     nenhuma fonte respondeu ainda.
                  -> NAO e resposta. Volta a ser perguntado amanha, todo dia,
                     ate alguma fonte responder.

      PREENCHIDO  tem valor.

    Card novo entra nas fontes antes de os catalogos serem atualizados. Tratar
    "nao sei" como "nao tem" congela o card com a nota errada para sempre.

O QUE ELE FAZ
    So le a base unica e escreve INSUMOS-PERGUNTAR-DE-NOVO.txt, campo por campo,
    com o botao que resolve cada um e o que se resolveu desde a rodada anterior.
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
HIST = 'insumos_pendencia_historico.json'
SAIDA = 'INSUMOS-PERGUNTAR-DE-NOVO.txt'

# campo -> (o que e, quem responde, muda a nota?)
INSUMOS = collections.OrderedDict([
    ('base',     ('os 26 atributos',            'COLETAR-EFHUB.bat',              True)),
    ('fab',      ('habilidades de fabrica',     'COLETAR-EFHUB.bat',              True)),
    ('raras',    ('habilidades raras',          'DERIVAR-FALTA.bat / efHub',      True)),
    ('nm',       ('o impeto de fabrica',        'COLETAR-EFSCOUT.bat',            True)),
    ('sl',       ('as vagas de impeto',         'COLETAR-VAGA-EFOOTBALLDB.bat',   True)),
    ('orc',      ('o orcamento de progressao',  'COLETAR-EFHUB.bat',              True)),
    ('modelo',   ('o estilo de jogo da IA',     'COLETAR-EFHUB.bat',              False)),
    ('corpo',    ('os 12 numeros do fisico',    'CORPO-PARA-CARDS.bat',           False)),
    ('pe_ruim',  ('o pe ruim',                  'Chrome F12 -> pe_ruim.json',     False)),
    ('vaga',     ('a vaga de impeto, uma a uma','COLETAR-VAGA-EFOOTBALLDB.bat',   False)),
    ('box',      ('a box de origem',            'COLETAR-BOX.bat',                False)),
    ('dt',       ('a data de lancamento',       'COLETAR-BOX.bat',                False)),
    ('levelCap', ('o teto de nivel',            'COLETAR-EFHUB.bat',              False)),
    ('max_ovr',  ('o OVR maximo',               'COLETAR-EFHUB.bat',              False)),
    ('tier',     ('a classe (S+/S/A)',          'ninguem ainda — regra nao derivada', False)),
])

# campos em que vazio e resposta legitima e nao se cobra de ninguem
NUNCA_COBRAR = {'sec', 'nx', 'nmn'}


def vazio(v):
    return v is None or v == [] or v == '' or v == {}


if not os.path.exists(BASE):
    print('nao achei o %s. Rode o UNIFICAR-BASE antes.' % BASE)
    raise SystemExit(1)

B = json.load(open(BASE, encoding='utf-8'))
cards = [c for c in (B.get('cards') or []) if '@' not in str(c.get('id'))]

pend = collections.defaultdict(list)     # campo -> [(id, nome, ovr)]
conferido = collections.Counter()        # campo -> quantos fechados
for c in cards:
    fdc = c.get('fonte_de_cada_campo') or {}
    for campo in INSUMOS:
        if fdc.get(campo) == 'CONFERIDO':
            conferido[campo] += 1
            continue
        if vazio(c.get(campo)):
            pend[campo].append((str(c['id']), c.get('nome'), c.get('ovr') or 0))

hoje = {
    'quando': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
    'por_campo': {k: len(v) for k, v in pend.items()},
    'conferido': dict(conferido),
    'chaves': sorted({'%s|%s' % (campo, i) for campo, li in pend.items() for i, _n, _o in li}),
}

ontem = {}
if os.path.exists(HIST):
    try:
        ontem = json.load(open(HIST, encoding='utf-8'))
    except Exception:
        ontem = {}

L = []
def P(*a):
    t = ' '.join(str(x) for x in a); print(t, flush=True); L.append(t)

P('=' * 78)
P('  OS INSUMOS QUE AINDA NAO TEM RESPOSTA   %s' % hoje['quando'])
P('=' * 78)
P('')
P('  ⛔ FONTE EM BRANCO NAO E RESPOSTA. Tudo que esta aqui volta a ser')
P('     perguntado na proxima rodada — e em todas as seguintes — ate alguma')
P('     fonte responder ou o Luis conferir no jogo.')
P('')
P('  cards na base .............. %d' % len(cards))
P('')
P('  %-10s %8s %10s  %-34s %s' % ('insumo', 'falta', 'conferido', 'quem responde', 'nota?'))
P('  ' + '-' * 74)
for campo, (oque, botao, muda) in INSUMOS.items():
    n = len(pend.get(campo) or [])
    P('  %-10s %8d %10d  %-34s %s'
      % (campo, n, conferido.get(campo, 0), botao, 'SIM' if muda else '-'))
P('')
P('  (%s: vazio ali e dado, nunca se cobra)' % ', '.join(sorted(NUNCA_COBRAR)))

if ontem:
    antes = set(ontem.get('chaves') or [])
    agora = set(hoje['chaves'])
    P('')
    P('-' * 78)
    P('DESDE A RODADA ANTERIOR (%s)' % ontem.get('quando', '?'))
    P('-' * 78)
    P('  responderam ...... %d' % len(antes - agora))
    P('  entraram novos ... %d' % len(agora - antes))
    if antes - agora:
        por = collections.Counter(k.split('|')[0] for k in (antes - agora))
        P('  o que se resolveu: %s'
          % ', '.join('%s %d' % (k, v) for k, v in por.most_common()))

P('')
P('=' * 78)
P('QUEM PERGUNTAR PRIMEIRO — so o que MUDA A NOTA, melhores primeiro')
P('=' * 78)
algum = False
for campo, (oque, botao, muda) in INSUMOS.items():
    li = pend.get(campo) or []
    if not muda or not li:
        continue
    algum = True
    li.sort(key=lambda x: -x[2])
    P('')
    P('  %s — %s   (%d cards)   -> %s' % (campo, oque, len(li), botao))
    for i, n, o in li[:10]:
        P('     %-17s %-28s ovr %s' % (i, (n or '?')[:28], o))
    if len(li) > 10:
        P('     ... e mais %d' % (len(li) - 10))
if not algum:
    P('')
    P('  Nenhum. Todo insumo que mexe na nota esta respondido ou conferido.')

P('')
P('=' * 78)
P('  Nada foi alterado. Isto e a lista do que perguntar de novo.')
P('=' * 78)

open(SAIDA, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
json.dump(hoje, open(HIST, 'w', encoding='utf-8'), ensure_ascii=False)
print('\nGravado: %s' % SAIDA)
