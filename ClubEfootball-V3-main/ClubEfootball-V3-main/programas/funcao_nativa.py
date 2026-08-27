"""
FUNCAO NATIVA — a peca que faltava para o molde.

O QUE E: cada card tem UMA e SO UMA funcao nativa, decidida por POSICAO + ESTILO.
E ela que parte a familia em duas populacoes diferentes. Sem isso, as duas funcoes
da familia recebem os mesmos cards e o molde sai IDENTICO nos dois lados.

=========================================================================
DE ONDE VEIO — medido, nao escolhido
=========================================================================
Extraida de `carga/builds.json` (a receita em pedra de 02/08), campo `migrado`:

    cards com linha nativa ......... 6.201
    funcoes nativas por card ....... {1: 6201}     <- UMA, sem excecao
    combinacoes (posicao, estilo) ..   177 puras · 0 ambiguas
    a regra comprimida abaixo reproduz .... 6.201 de 6.201, ZERO erro

E o documento MOLDE-19-FUNCOES (02/08) fecha por outro caminho:
    355 + 91 + 172 + 170 + 95 + 208 + 179 + 44 + 178 + 203 = 1.695
    cabecalho do documento: "1.767 cards puxados, 1695 com build"
Cada card contado exatamente uma vez. E uma PARTICAO.

⚠️ NAO CONFUNDIR com `refazer_molde()` do atualizar.py. Aquela funcao NAO parte
   nada: o mesmo objeto `c` entra nas duas funcoes da familia, o filtro de elite
   e o mesmo e a mediana sai igual. Prova: `carga/estilo_valor.json`, que ela
   gera, vem byte a byte identico nos dois lados de TODAS as 9 familias.
   O molde vigente (carga/molde.json) NAO saiu dela.

=========================================================================
A FORMA DA REGRA — minoria explicita, e o resto cai no default
=========================================================================
Em toda familia, UM lado e definido por uma lista curta de estilos e o outro
lado recebe todo o resto. Nao e simetrico e nao e por argmax de estilo_valor.
=========================================================================
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

# posicao -> (estilos da MINORIA, funcao da minoria, funcao default)
# nomenclatura de 18 funcoes (Meia ofensivo infiltrador -> Segundo atacante,
#                             Centroavante de referencia -> Centroavante fixo)
REGRA = {
    'GK':  ({'Goleiro defensivo'},
            'Goleiro defensivo',        'Goleiro ofensivo'),
    'ZC':  ({'O destruidor'},
            'Zagueiro de combate',      'Zagueiro de saída'),
    'LD':  ({'Zagueiro defensivo'},
            'Lateral defensivo',        'Lateral ofensivo'),
    'LE':  ({'Zagueiro defensivo'},
            'Lateral defensivo',        'Lateral ofensivo'),
    'VOL': ({'Meia versátil', 'Orquestrador'},
            'Volante de construção',    'Volante de contenção'),
    'MC':  ({'Jog. de infiltração', 'Meia versátil'},
            'Meia central de chegada',  'Meia central armador'),
    'MLD': ({'Especialista em cruz.', 'Lateral móvel', 'Meia versátil'},
            'Meia de lado por fora',    'Meia de lado por dentro'),
    'MLE': ({'Especialista em cruz.', 'Lateral móvel', 'Meia versátil'},
            'Meia de lado por fora',    'Meia de lado por dentro'),
    'MO':  ({'Jog. de infiltração', 'Puxa marcação'},
            'Segundo atacante',         'Meia ofensivo armador'),
    'PD':  ({'Armador criativo', 'Especialista em cruz.', 'Lateral móvel'},
            'Ponta criadora',           'Ponta finalizadora'),
    'PE':  ({'Armador criativo', 'Especialista em cruz.', 'Lateral móvel'},
            'Ponta criadora',           'Ponta finalizadora'),
    'CA':  ({'Homem de área', 'Pivô'},
            'Centroavante fixo',        'Centroavante móvel'),
}

# ---------------------------------------------------------------------
# SA / SS — a posicao foi DISSOLVIDA em 02/08. Nao tem par proprio: cada card
# vai para a familia MEIA OFENSIVO ou CENTROAVANTE conforme o estilo, e la a
# regra da familia decide o lado.
# ✅ As 6 primeiras linhas sao o REALOC_SA ja provado: 22 · 21 · 14 nos 57
#    cards de SA do encaixe_B_v158, contados por `sec = None`. Zero erro.
# As demais estendem o mesmo criterio para os estilos que ainda nao apareceram
# em SA no elite, para que card novo nunca fique sem destino.
# ---------------------------------------------------------------------
SA_FAMILIA = {
    'Jog. de infiltração':   'MO',   # -> Segundo atacante        (21 provados)
    'Armador criativo':      'MO',   # -> Meia ofensivo armador   (14 provados)
    'Clássica nº 10':        'MO',   # -> Meia ofensivo armador   ( 8 provados)
    'Atacante Pivô':         'CA',   # -> Centroavante móvel      ( 6 provados)
    'Puxa marcação':         'CA',   # -> Centroavante móvel      ( 4 provados)
    'Artilheiro':            'CA',   # -> Centroavante móvel      ( 4 provados)

    'Homem de área':         'CA',   # -> Centroavante fixo
    'Pivô':                  'CA',   # -> Centroavante fixo
    'Orquestrador':          'MO',   # -> Meia ofensivo armador
    'Meia versátil':         'MO',   # -> Meia ofensivo armador
    'Ala produtivo':         'MO',   # -> Meia ofensivo armador
    'Especialista em cruz.': 'MO',   # -> Meia ofensivo armador
    'Lateral móvel':         'MO',   # -> Meia ofensivo armador
    'Zagueiro ofensivo':     'MO',   # -> Meia ofensivo armador
    'Zagueiro defensivo':    'MO',   # -> Meia ofensivo armador
    'Lateral atacante':      'MO',   # -> Meia ofensivo armador
    'Primeiro volante':      'MO',   # -> Meia ofensivo armador
    'O destruidor':          'MO',   # -> Meia ofensivo armador
    'Provocador':            'MO',   # -> Meia ofensivo armador
    'Atacante surpresa':     'CA',   # -> Centroavante móvel
    'Goleiro ofensivo':      'MO',
    'Goleiro defensivo':     'MO',
}

# ---------------------------------------------------------------------
# a ficha do eFHUB vem em ingles e com outro codigo de posicao
# ---------------------------------------------------------------------
ESTILO_EN2PT = {
    'Offensive Goalkeeper': 'Goleiro ofensivo',
    'Defensive Goalkeeper': 'Goleiro defensivo',
    'Build Up':             'Provocador',
    'Destroyer':            'O destruidor',
    'Extra Frontman':       'Atacante surpresa',
    'Offensive Wingback':   'Zagueiro ofensivo',
    'Defensive Full-back':  'Zagueiro defensivo',
    'Full-back Finisher':   'Lateral atacante',
    'Cross Specialist':     'Especialista em cruz.',
    'Anchor Man':           'Primeiro volante',
    'Orchestrator':         'Orquestrador',
    'Box To Box':           'Meia versátil',
    'Hole Player':          'Jog. de infiltração',
    'Creative Playmaker':   'Armador criativo',
    'Classic No. 10':       'Clássica nº 10',
    'Prolific Winger':      'Ala produtivo',
    'Roaming Flank':        'Lateral móvel',
    'Goal Poacher':         'Artilheiro',
    'Deep-Lying Forward':   'Atacante Pivô',
    'Fox In The Box':       'Homem de área',
    'Target Man':           'Pivô',
    'Dummy Runner':         'Puxa marcação',
}

POS_EN2PT = {'GK':'GK', 'CB':'ZC', 'RB':'LD', 'LB':'LE', 'DMF':'VOL', 'CMF':'MC',
             'RMF':'MLD', 'LMF':'MLE', 'AMF':'MO', 'RWF':'PD', 'LWF':'PE',
             'CF':'CA', 'SS':'SA', 'SA':'SA'}


def normaliza(pos, estilo):
    """aceita ficha do eFHUB (EN) ou card do sistema (PT). Devolve (pos_pt, estilo_pt)."""
    p = (pos or '').upper()
    p = POS_EN2PT.get(p, p)
    e = estilo or ''
    return p, ESTILO_EN2PT.get(e, e)


def funcao_nativa(pos, estilo):
    """A UNICA funcao em que este card e nativo. None = estilo desconhecido, avisar o Luis.

    ✅ 6.201 de 6.201 contra carga/builds.json (campo migrado=false). Zero erro."""
    p, e = normaliza(pos, estilo)
    if p == 'SA':
        p = SA_FAMILIA.get(e)
        if not p: return None
    r = REGRA.get(p)
    if not r: return None
    if p == 'CA' and e == 'Atacante Pivô':
        return 'Falso nove'
    minoria, fa, fb = r
    return fa if e in minoria else fb


def familia(pos):
    """as DUAS funcoes que um card desta posicao disputa (nativa + migrada dentro da casa)."""
    p, _ = normaliza(pos, None)
    if p == 'SA':
        return sorted({funcao_nativa('SA', e) for e in SA_FAMILIA} - {None})
    r = REGRA.get(p)
    if not r: return []
    if p == 'CA':
        return [r[1], r[2], 'Falso nove']
    return [r[1], r[2]]


FUNCOES_19 = FUNCOES_18 = sorted({f for (_, a, b) in REGRA.values() for f in (a, b)} | {'Falso nove'})
