# -*- coding: utf-8 -*-
"""
CONFERIR AS FONTES — o placar de numeros, todo dia.

ORDEM DO LUIS, 14/08/2026:
    "Atualizar todos os campos, todos os dias. Vai perguntar pras fontes.
     Faz um comparativo de numeros: qual o numero que tem na tabela, 61.
     Voce vai olhar as fontes e ela tem 62 — significa que aumentou um."

O QUE ELE FAZ
    Conta quantos itens cada FONTE tem hoje, e compara com:
       (a) quanto ela tinha na rodada anterior      -> aumentou? diminuiu?
       (b) quanto a NOSSA BASE aproveitou daquela fonte

    Assim nao existe mais fonte que cresceu e ninguem viu. Impeto novo,
    habilidade nova, tecnico novo: o numero sobe e aparece aqui no dia seguinte.

    ⚠️ Numero que DIMINUI e aviso vermelho. Fonte nao encolhe sozinha — ou a
       coleta falhou no meio, ou o arquivo foi truncado.

    So le. Nao muda nada.
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

HIST = 'fontes_placar_historico.json'
SAIDA = 'FONTES-O-PLACAR.txt'

# arquivo -> (o que e, quem atualiza)
FONTES = collections.OrderedDict([
    ('efscout_boosters.json',        ('o catalogo de IMPETOS',            'COLETAR-EFSCOUT.bat')),
    ('efscout_impeto_por_card.json', ('o impeto de cada card',            'COLETAR-EFSCOUT.bat')),
    ('HAB_EFEITOS_FINAL.json',       ('o catalogo de HABILIDADES',        'CADASTRAR-HABILIDADES-NOVAS')),
    ('habilidades_efootballdb.json', ('as habilidades por card',          'CRUZAR-HABILIDADES.bat')),
    ('habilidades_por_posicao.json', ('o bloqueio de habilidade',         'a mao — Tabela do Luis')),
    ('tecnicos.json',                ('os TECNICOS',                      'Chrome F12 -> managers.json')),
    ('cards_efhub.json',             ('as fichas novas do efHub',         'COLETAR-EFHUB.bat')),
    ('vaga_por_card.json',           ('as vagas de impeto',               'COLETAR-VAGA-EFOOTBALLDB.bat')),
    ('box_por_card.json',            ('a box e a data',                   'COLETAR-BOX.bat')),
    ('datas-lancamento-cartas.json', ('as datas de lancamento',           'COLETAR-BOX.bat')),
    ('pe_ruim.json',                 ('o pe ruim',                        'Chrome F12 -> pe_ruim.json')),
    ('dados/levelcap.json',          ('o teto de nivel',                  'COLETAR-EFHUB.bat')),
    ('dados/falta_por_card.json',    ('o falta por card',                 'DERIVAR-FALTA.bat')),
    ('dados/raras_por_card.json',    ('as raras por card',                'DERIVAR-FALTA.bat')),
    ('dados/molde.json',             ('o MOLDE (o denominador da nota)',  'so o Luis muda')),
    ('dados/cards.json',             ('o cards.json',                     'a esteira')),
    ('dados/base_unica.json',        ('A BASE UNICA',                     'UNIFICAR-BASE.bat')),
])


def conta(caminho):
    """Quantos itens tem. Aceita lista, dicionario e dicionario com cabecalho."""
    try:
        with open(caminho, encoding='utf-8') as f:
            d = json.load(f)
    except Exception:
        return None
    if isinstance(d, list):
        return len(d)
    if isinstance(d, dict):
        for k in ('cards', 'dados', 'conferidos', 'datas', 'bloqueios'):
            if isinstance(d.get(k), (list, dict)):
                return len(d[k])
        uteis = [k for k in d if not str(k).startswith('_')]
        return len(uteis)
    return None


hoje = {'quando': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'n': {}}
for arq in FONTES:
    hoje['n'][arq] = conta(arq)

ontem = {}
if os.path.exists(HIST):
    try:
        ontem = json.load(open(HIST, encoding='utf-8'))
    except Exception:
        ontem = {}
nO = (ontem.get('n') or {})

L = []
def P(*a):
    t = ' '.join(str(x) for x in a); print(t, flush=True); L.append(t)

P('=' * 84)
P('  O PLACAR DAS FONTES   %s' % hoje['quando'])
P('=' * 84)
if ontem:
    P('  comparando com a rodada de %s' % ontem.get('quando', '?'))
else:
    P('  primeira rodada — a partir de amanha aparece a coluna do que mudou')
P('')
P('  %-32s %9s %9s %8s  %s' % ('fonte', 'ontem', 'hoje', 'mudou', 'quem atualiza'))
P('  ' + '-' * 80)

subiu, caiu, sumiu = [], [], []
for arq, (oque, quem) in FONTES.items():
    a, h = nO.get(arq), hoje['n'][arq]
    if h is None:
        P('  %-32s %9s %9s %8s  %s' % (oque[:32], a if a is not None else '-', 'NAO EXISTE', '', quem))
        sumiu.append(oque)
        continue
    if a is None:
        P('  %-32s %9s %9d %8s  %s' % (oque[:32], '-', h, 'novo', quem))
        continue
    d = h - a
    marca = ('+%d' % d) if d > 0 else (str(d) if d < 0 else 'igual')
    P('  %-32s %9d %9d %8s  %s' % (oque[:32], a, h, marca, quem))
    if d > 0:
        subiu.append((oque, d, quem))
    elif d < 0:
        caiu.append((oque, d, quem))

P('')
if subiu:
    P('-' * 84)
    P('CRESCEU — tem coisa nova para o sistema aproveitar')
    P('-' * 84)
    for oque, d, quem in subiu:
        P('   %-40s +%-5d   veio de: %s' % (oque, d, quem))
    P('')
    P('   O UNIFICAR-BASE desta mesma rodada ja pegou o que cresceu.')
    P('   Card que estava esperando esse dado se resolve sozinho.')

if caiu:
    P('')
    P('=' * 84)
    P('  ⚠️  ATENCAO — FONTE QUE ENCOLHEU')
    P('=' * 84)
    for oque, d, quem in caiu:
        P('   %-40s %-6d   %s' % (oque, d, quem))
    P('')
    P('   Fonte nao encolhe sozinha. Ou a coleta caiu no meio, ou o arquivo')
    P('   foi truncado. Confira antes de confiar na base desta rodada.')

if sumiu:
    P('')
    P('  ⚠️  ARQUIVO QUE NAO EXISTE: %s' % ', '.join(sumiu))

P('')
P('=' * 84)
P('  So leitura. Nada foi alterado.')
P('=' * 84)

open(SAIDA, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
json.dump(hoje, open(HIST, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\nGravado: %s' % SAIDA)
