"""
REGUA e BUSSOLA — A LEI DO VALOR.

Manda neste arquivo: NAO-MEXER-formula-do-molde-e-do-motor.md, partes 2.4 e 2.5

Esta peca diz quanto VALE estar acima do alvo e quanto CUSTA estar abaixo.
Nao e regra do jogo — e valoracao declarada do Luis. A medicao no videogame
nao toca em nada daqui.

Tres coisas moram aqui:

  REGUA   `notaDe`      -> o numero que aparece. Punicao x 1, teto no 9o ponto.
  REGUA   `pts_regua`   -> A MESMA REGUA, por atributo, no formato de tabela.
  BUSSOLA `pts_table`   -> punicao x 100 (K), sem teto.

=========================================================================
⚠️ 05/08/2026 — O DP DO MOTOR PASSOU A MAXIMIZAR A REGUA.

Ate 04/08 o DP das barras maximizava a BUSSOLA e a REGUA so pontuava o
resultado. Sao FUNCOES DIFERENTES: a bussola pune x100 e nao tem teto, a
regua pune x1 e para no 9o ponto. Logo o maximo de uma NAO e o maximo da
outra — o DP entregava UMA distribuicao de barras e a regua nao tinha o que
escolher. Medido no Lisandro Martinez: 179,8 (bussola) contra 227,3 (regua),
no mesmo motor, so trocando a tabela.

`notaDe` e SEPARAVEL por atributo, exatamente como a bussola:
      notaDe(vals) = ARRED( SOMA_i  pts_regua(alvo_i, peso_i)[vals_i] , 0.1 )
Entao o DP roda nela direto, EXATO. Nao e heuristica, e trocar a tabela.

Efeito colateral que precisa ficar escrito: com o teto de punicao no 9o
ponto, a regua nao distingue um atributo 10 abaixo do alvo de um 30 abaixo.
Buraco fundo deixa de puxar o motor. Isso e o que a valoracao do Luis diz —
a bussola existia para forcar tapar buraco, mas ela nao e o placar.
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
import numpy as np
from equacao import aplica_buff

# nove degraus acima do alvo; do 10o ponto em diante: ZERO
DEG = [1, .88, .76, .64, .52, .40, .28, .16, .04]

K = 100        # o x100 da BUSSOLA. Nunca entra na nota.
TETO_PUN = 9   # 04/08: a punicao para no 9o ponto. SO na regua.
VMAX = 260     # valor final maximo indexavel

_cache = {}
_cache_r = {}


def _pts_table(alvo, peso):
    """BUSSOLA. PTS[v] = pontos do atributo, com a punicao x K e SEM teto.
    Laco k<=d, IGUAL ao HTML (alvo com meio ponto preservado)."""
    t = np.zeros(VMAX + 1)
    for v in range(VMAX + 1):
        d = v - alvo
        if d >= 0:
            s = 0.0; k = 1
            while k <= d:
                if k > len(DEG): break
                s += DEG[k - 1] * peso; k += 1
            t[v] = s
        else:
            if peso == 1: t[v] = 0.0      # acessorio NAO pune
            else:
                inc = .25 * peso / 12; s = 0.0; k = 1
                while k <= -d: s += (1 + (k - 1) * inc) * peso; k += 1
                t[v] = -K * s
    return t


def pts_table(alvo, peso):
    key = (round(alvo, 2), peso)
    if key not in _cache: _cache[key] = _pts_table(alvo, peso)
    return _cache[key]


def _pts_regua(alvo, peso):
    """A REGUA, por atributo, no MESMO formato da bussola.
    Punicao x1 (sem o K) e COM teto no 9o ponto — identica a notaDe.
    E esta a tabela que o DP do motor maximiza desde 05/08/2026."""
    t = np.zeros(VMAX + 1)
    for v in range(VMAX + 1):
        d = v - alvo
        if d >= 0:
            s = 0.0; k = 1
            while k <= d:
                if k > len(DEG): break
                s += DEG[k - 1] * peso; k += 1
            t[v] = s
        else:
            if peso == 1: t[v] = 0.0      # acessorio NAO pune
            else:
                inc = .25 * peso / 12; s = 0.0; k = 1; lim = min(int(-d), TETO_PUN)
                while k <= lim: s += (1 + (k - 1) * inc) * peso; k += 1
                t[v] = -s
    return t


def pts_regua(alvo, peso):
    key = (round(alvo, 2), peso)
    if key not in _cache_r: _cache_r[key] = _pts_regua(alvo, peso)
    return _cache_r[key]


def notaDe(vals, arows):
    """REGUA. O numero que aparece. Punicao x1 e COM teto no 9o ponto."""
    s = 0.0
    for r in arows:
        if not r[1]: continue
        d = vals[r[0]] - r[2]
        if d >= 0:
            k = 1
            while k <= d:
                if k > len(DEG): break
                s += DEG[k - 1] * r[1]; k += 1
        elif r[1] != 1:
            inc = .25 * r[1] / 12; k = 1; lim = min(-d, TETO_PUN)
            while k <= lim: s -= (1 + (k - 1) * inc) * r[1]; k += 1
    return round(s * 10) / 10


def nota_por_tabela(vals, arows):
    """a MESMA nota, somando as tabelas. Existe so para provar a identidade
    com notaDe (o DP soma tabela, entao as duas tem que fechar)."""
    s = 0.0
    for r in arows:
        if not r[1]: continue
        v = int(min(VMAX, max(0, vals[r[0]])))
        s += float(pts_regua(r[2], r[1])[v])
    return round(s * 10) / 10


def tabela_com_buff(alvo, peso, pct, flat):
    """a bussola do atributo, ja com o efeito da habilidade dentro."""
    base = pts_table(alvo, peso)
    t = np.zeros(VMAX + 1)
    for v in range(VMAX + 1):
        t[v] = base[min(VMAX, aplica_buff(v, pct, flat))]
    return t
