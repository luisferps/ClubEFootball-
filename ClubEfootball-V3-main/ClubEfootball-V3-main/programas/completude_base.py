# -*- coding: utf-8 -*-
"""
COMPLETUDE DA BASE UNICA — "nao deixar linha faltando nada".

POR QUE ESTE ARQUIVO EXISTE
---------------------------
O `unificar_base.py` ja diz QUANTOS cards tem cada campo. O que faltava era o
outro lado da moeda: olhar CARD POR CARD e dizer o que falta NAQUELE card, e
QUAL coleta traz aquele dado. Sem isso, "faltam 3.809 boxes" nao vira tarefa.

Este script NAO altera nada. Le a base unica e escreve um relatorio.
(Nome proposital: existe um `conferir_base.py` antigo na pasta, com outra
funcao. Este aqui e outro bicho e nao encosta nele.)

COMO RODAR
----------
    python completude_base.py
    python completude_base.py --tudo   -> lista TODOS os cards incompletos na tela

Saida: RELATORIO-COMPLETUDE.txt (a lista completa, sempre)
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
import json
import os
import sys
import io
from collections import Counter, OrderedDict

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors='replace', line_buffering=True)
except Exception:
    pass

os.chdir(_CASA or os.path.dirname(os.path.abspath(__file__)))
TUDO_NA_TELA = '--tudo' in sys.argv

BASE = os.path.join('dados', 'base_unica.json')
SAIDA = 'RELATORIO-COMPLETUDE.txt'

# ---------------------------------------------------------------------------
# O MAPA: campo -> (nome em portugues, de qual coleta ele deveria vir, peso)
#
# peso 'essencial' = sem ele o motor calcula ERRADO ou nem calcula.
# peso 'desejavel' = melhora a nota/organizacao, mas o motor anda sem.
#
# A coluna "de onde vem" e o que transforma o relatorio em tarefa: o Luis le
# "falta box" e ja sabe que o botao e o COLETAR-BOX.
# ---------------------------------------------------------------------------
CAMPOS = OrderedDict([
    ('nome',     ('nome do jogador',            'dados/cards.json (base do sistema)',      'essencial')),
    ('ovr',      ('OVR',                        'dados/cards.json / cards_efhub.json',     'essencial')),
    ('pos',      ('posicao',                    'cards_efhub.json / efScout',              'essencial')),
    ('np',       ('posicao nativa',             'cards_efhub.json / POSICOES-DO-EFSCOUT',  'essencial')),
    ('base',     ('os 26 atributos base',       'dados/cards.json / cards_efhub.json',     'essencial')),
    ('orc',      ('orcamento de progressao',    'cards_efhub.json',                        'essencial')),
    ('sl',       ('vagas (impeto/habilidade)',  'cards_efhub.json + CONSERTAR-SL',         'essencial')),
    ('fab',      ('habilidades de fabrica',     'cards_efhub.json / efHub',                'essencial')),
    ('corpo',    ('os 12 numeros do fisico',    'CORPO-PARA-CARDS (efHub)',                'essencial')),
    ('modelo',   ('estilo de jogo da IA',       'cards_efhub.json / efScout',              'essencial')),
    ('max_ovr',  ('OVR maximo',                 'cards_efhub.json',                        'desejavel')),
    ('tier',     ('classe (S+/S/A)',            'cards_efhub.json',                        'desejavel')),
    ('nm',       ('efeito do impeto de fabrica', 'efScout (COLETAR-EFSCOUT + impeto_do_efscout)', 'desejavel')),
    ('vaga',     ('vagas de impeto, uma a uma', 'efootballdb (COLETAR-VAGA-EFOOTBALLDB)',  'desejavel')),
    ('box',      ('box/campanha de origem',     'efootballdb (COLETAR-BOX)',               'desejavel')),
    ('dt',       ('data de lancamento',         'efootballdb (COLETAR-BOX)',               'desejavel')),
    ('pe_ruim',  ('pe ruim (frequencia/precisao)', 'efHub pelo Chrome (F12) -> pe_ruim.json', 'desejavel')),
    ('levelCap', ('teto de nivel',              'cards_efhub.json / levelcap.json',        'desejavel')),
])

# Campos que NAO entram na conta de falta, e por que:
#   raras -> lista vazia e um dado legitimo ("esse card nao tem rara")
#   sec   -> tem card sem posicao secundaria nenhuma
#   nx    -> so existe quando o impeto e condicional
#   falta -> ⛔ SAIU DA CONTA EM 14/08/2026. Era cobrado como ESSENCIAL desde a
#            epoca em que o pool do motor vinha dele. Em 08/08 o Luis mudou a
#            regra: POOL='regra' (roda_lote_v6.py). O pool passou a ser
#            "as 44 habilidades COMUNS menos (fabrica + raras) menos o bloqueio
#            da posicao" — o `falta` nao e mais lido pelo motor.
#            MEDIDO em 14/08 nos 241 cards com o falta vazio dos dois lados,
#            985 linhas na fila: pool real minimo 10, mediana 28, maximo 40.
#            Linhas com pool < 5: ZERO. O caso do Musiala (-135,5 com pool 0)
#            nao pode mais acontecer. Cobrar `falta` inflava o buraco em 450.
NAO_COBRAR = ('raras', 'sec', 'nx', 'nmn', 'falta')


def vazio(valor):
    """Mesma regra do unificar_base.py: 0 e False SAO dados; None, "", [] nao."""
    if valor is None:
        return True
    if isinstance(valor, str) and valor.strip() in ('', '?'):
        return True
    if isinstance(valor, (list, dict, tuple)) and len(valor) == 0:
        return True
    return False


if not os.path.exists(BASE):
    print('Nao achei o %s.' % BASE)
    print('Rode antes o UNIFICAR-BASE.bat (ou o BAIXAR-BASE.bat).')
    sys.exit(1)

with open(BASE, 'r', encoding='utf-8') as f:
    base = json.load(f)

cards = base.get('cards') or []
total = len(cards)

# ---------------------------------------------------------------------------
# A CONTA
# ---------------------------------------------------------------------------
falta_por_campo = Counter()
incompletos = []          # (id, nome, [campos essenciais], [campos desejaveis])
so_essencial_ok = 0
completos = 0

# CONFERIDO: campo que ja foi checado e fechado nao se cobra mais, nem que o
# valor seja vazio. "Esse card nao tem" e resposta, nao buraco. (Luis, 14/08)
conferido_total = 0

for c in cards:
    ess, des = [], []
    fdc = c.get('fonte_de_cada_campo') or {}
    for campo, (_rotulo, _fonte, peso) in CAMPOS.items():
        if vazio(c.get(campo)):
            if fdc.get(campo) == 'CONFERIDO':
                conferido_total += 1
                continue
            falta_por_campo[campo] += 1
            (ess if peso == 'essencial' else des).append(campo)
    if not ess and not des:
        completos += 1
    else:
        incompletos.append((str(c.get('id')), c.get('nome') or '?', ess, des))
    if not ess:
        so_essencial_ok += 1

# ---------------------------------------------------------------------------
# O RELATORIO
# ---------------------------------------------------------------------------
L = []
L.append('RELATORIO DE COMPLETUDE DA BASE UNICA')
L.append('=' * 74)
L.append('')
L.append('Cards na base ............................ %d' % total)
L.append('COMPLETOS (nao falta nada) ............... %d' % completos)
L.append('Faltando algum dado ...................... %d' % len(incompletos))
L.append('Com TODOS os essenciais (da para calcular) %d' % so_essencial_ok)
L.append('Vazios CONFERIDOS (resposta, nao buraco) . %d' % conferido_total)
L.append('Sem algum essencial (calculo fica torto) . %d' % (total - so_essencial_ok))
L.append('')

L.append('O QUE FALTA, E DE ONDE ESSE DADO DEVERIA VIR')
L.append('-' * 74)
L.append('  %-10s %-8s %7s   %s' % ('campo', 'peso', 'faltam', 'de onde vem / que botao resolve'))
for campo, (rotulo, fonte, peso) in CAMPOS.items():
    n = falta_por_campo.get(campo, 0)
    if not n:
        L.append('  %-10s %-8s %7s   OK, nenhum card sem esse dado' % (campo, peso, '0'))
    else:
        L.append('  %-10s %-8s %7d   %s' % (campo, peso, n, fonte))
        L.append('  %-10s %-8s %7s   (%s)' % ('', '', '', rotulo))
L.append('')
L.append('Campos que NAO sao cobrados (vazio ali e dado, nao falta): %s'
         % ', '.join(NAO_COBRAR))
L.append('')

L.append('CARD POR CARD — o que falta em cada um (%d cards)' % len(incompletos))
L.append('-' * 74)
if not incompletos:
    L.append('  Nenhum. Toda linha esta completa.')
else:
    # os que estao piores primeiro: primeiro quem perde essencial, depois quem
    # perde mais campos. E a ordem de quem deve ser resolvido antes.
    incompletos.sort(key=lambda x: (-len(x[2]), -len(x[3]), x[1]))
    for cid, nome, ess, des in incompletos:
        pedacos = []
        if ess:
            pedacos.append('ESSENCIAL: ' + ', '.join(ess))
        if des:
            pedacos.append('desejavel: ' + ', '.join(des))
        L.append('  %-16s %-28s %s' % (cid, nome[:28], ' | '.join(pedacos)))
L.append('')

L.append('COMO RESOLVER, NA ORDEM QUE COSTUMA RESOLVER MAIS DE UMA VEZ')
L.append('-' * 74)
L.append('  1. ALIMENTAR-TUDO.bat  — roda todas as coletas e refaz a base.')
L.append('  2. O que sobrar de `pe_ruim` e de tecnico so vem pelo Chrome (F12),')
L.append('     porque a API do efHub devolve 403 fora do navegador.')
L.append('  3. O que sobrar de `nm` (impeto) com boostId orfao esta listado no')
L.append('     RELATORIO-BASE-UNICA.txt — e coleta nova do efScout.')
L.append('  4. Card muito antigo pode simplesmente nao ter box nem data na fonte.')
L.append('     Isso nao e erro do sistema: e limite da fonte.')

relatorio = '\n'.join(L)

with open(SAIDA, 'w', encoding='utf-8') as f:
    f.write(relatorio + '\n')

# ---------------------------------------------------------------------------
# NA TELA: o resumo. A lista card a card so com --tudo (senao rolam 6 mil linhas)
# ---------------------------------------------------------------------------
corte = relatorio.split('CARD POR CARD')[0]
print(corte)
if TUDO_NA_TELA:
    print(relatorio.split('CARD POR CARD', 1)[1])
else:
    print('CARD POR CARD — os 25 mais furados (a lista completa esta no %s)' % SAIDA)
    print('-' * 74)
    for cid, nome, ess, des in incompletos[:25]:
        pedacos = []
        if ess:
            pedacos.append('ESSENCIAL: ' + ', '.join(ess))
        if des:
            pedacos.append('desejavel: ' + ', '.join(des))
        print('  %-16s %-28s %s' % (cid, nome[:28], ' | '.join(pedacos)))
    print('')
print('Gravado: %s' % SAIDA)
