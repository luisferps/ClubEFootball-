"""
MOTOR — O EXECUTOR. A unica peca que AGE.

Manda neste arquivo: NAO-MEXER-formula-do-molde-e-do-motor.md, partes 2.6 e 2.7

Ele escolhe QUATRO coisas ao mesmo tempo — barras, impeto, tecnico e as 5 habilidades —
para BATER OU PASSAR o molde, sem violar a equacao, guiado pela bussola.

Ele nunca ve o alvo direto: ve nota. As tres leis (equacao, molde, regua) nao fazem
nada; este arquivo e quem faz.

⚠️ PASSO 1 (04/08): este arquivo e uma SEPARACAO do motor3.py, nao uma correcao.
Nenhuma formula mudou. As restricoes novas da medicao (D: o jogo bloqueia o nivel
quando o menor atributo da barra chega em 99; E: alvo util = ceil(99/m)) entram DEPOIS.
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
import json, math, itertools
import numpy as np

from equacao import (MB, MBK, ACCU, ATTRS_EF, POS, AM, TABM, mult_de, _mult, _multv,
                     carrega_tecnicos, HAB, POR_NOME, TEM_EFEITO, buff_de, aplica_buff,
                     nivel_max_barra)
from regua import (DEG, K, TETO_PUN, VMAX, pts_table, pts_regua, notaDe,
                   nota_por_tabela, tabela_com_buff)

# =========================================================================
# 05/08/2026 — QUAL TABELA O DP MAXIMIZA.
#
# Ate 04/08 era a BUSSOLA (punicao x100, sem teto) e a REGUA so pontuava
# o que o DP entregava. Sao funcoes diferentes: o maximo de uma nao e o
# maximo da outra. O DP devolvia UMA distribuicao de barras por candidato,
# entao a regua nao tinha o que escolher — ela so assinava embaixo.
#
# MEDIDO, mesmo motor, so trocando a tabela:
#     Lisandro Martinez   bussola 179,8   regua 227,3   (+47,5)
#     Allan Saint-Maximin bussola -89,7   regua -67,7   (+22,0)
#
# `notaDe` e SEPARAVEL por atributo igual a bussola, entao o DP roda nela
# EXATO. Nao e heuristica: e trocar a tabela.
#
# De quebra, as podas passam a valer: `dmax` e `MARG` saem de card.tab, e
# antes vinham em bussola x100 comparados com `lb` em regua x1 — por isso
# nenhum corte cortava nada.
#
# TABELA_DP = 'regua' (padrao) | 'bussola' (comportamento ate 04/08)
# =========================================================================
TABELA_DP = 'regua'
CORTE8 = True                       # False desliga a dedup por efeito (so para medir)

# 16/08 — encoding='utf-8' EXPLICITO. Antes era open('CAT_dom.json') e so nao
# quebrava porque os .bat do motor setam PYTHONUTF8=1. No Windows, sem essa
# variavel, o open() usa cp1252 e este arquivo tem 56 bytes nao-ASCII (o primeiro
# e um 'a' com til) — da UnicodeDecodeError e o motor NAO RODA. Mesmo defeito que
# derrubou o import do equacao.py e escondeu a conta do motor da tela por dias.
# ⛔ NAO MUDA A CONTA: o dado lido e byte por byte o mesmo.
CAT = json.load(open('CAT_dom.json', encoding='utf-8'))   # catalogo de impetos fabricaveis


def expand(pairs):
    v = [0] * 26
    for i, x in (pairs or []): v[i] = x
    return v


class Card:
    """pre-computa tudo que nao depende do impeto/tecnico.
    m = multiplicador tatico do tecnico. A cadeia:
        base + barras  TRAVA 99  ->  x multiplicador  TRAVA 99  ->  + boost e impeto  PASSA de 99

    ⚠️ `aplicar` e `sem_add` sao a COPIA INLINE da cadeia de equacao.py, mantida aqui
    por velocidade (o laco quente roda isto milhoes de vezes). `prova_cadeia.py`
    garante que as duas nunca divirjam."""
    def __init__(self, c, m=1.0, bf=None):
        self.c = c; self.base = c['base']; self.orc = c.get('orc') or 0; self.m = m
        self.bf = bf or {}
        self.arows = [r for r in c['arows'] if r[1]]
        self.R = {r[0]: (r[2], r[1]) for r in self.arows}
        _tb = pts_table if globals().get('TABELA_DP') == 'bussola' else pts_regua
        self.tab = {i: _tb(a, p) for i, (a, p) in self.R.items()}
        self.pes = set(self.R)
        sl = c.get('sl') or [0, 0]
        self.L  = [x for x in CAT if x[1] == 0 and any(i in self.pes for i, _ in x[2])] if sl[0] else []
        self.Rr = [x for x in CAT if x[1] == 1 and any(i in self.pes for i, _ in x[2])] if sl[1] else []
        self.nm = expand(c.get('nm'))
        self.vb = {i: _multv(np.minimum(99, self.base[i] + np.arange(26)), self.m) for i in self.R}
        # CONSERTO DA BUSSOLA (04/08): a escada de BASE+BARRAS por nivel. E dela
        # que sai a % da habilidade (Equacao 2), nao do valor final.
        self.bb = {i: np.minimum(99, self.base[i] + np.arange(26)) for i in self.R}
        # MUDANCA D — o jogo BLOQUEIA o nivel quando o MENOR atributo da barra
        # chega em 99. Nao e so travar o atributo: ele nao deixa nem gastar o ponto.
        # Medido no Messi: 19 niveis no Chute levaram a Finalizacao a 99, e o jogo
        # recusou o 20o com 7 pontos sobrando.
        self.nmax_barra = {b: nivel_max_barra(self.base, b) for b in MBK}

    def _buff_esc(self, i):
        """ganho da habilidade no atributo i, por nivel de barra. Le base+barras."""
        pct, flat = self.bf[i]
        return np.ceil(self.bb[i] * pct / 100.0 + flat).astype(int)   # v5: ceil sobre o total

    def ganho(self, i, add):
        """array de 26 posicoes: ganho de por o nivel n na barra, para o atributo i.
        CONSERTO: o buff entra aqui, lendo base+barras — antes ele estava assado
        dentro da tabela de pontos, calculado sobre o valor FINAL, e a bussola
        prometia mais do que a regua pagava."""
        t = self.tab[i]; v = self.vb[i] + add
        if i in self.bf: v = v + self._buff_esc(i)
        g = t[np.clip(v, 0, VMAX)]
        return g - g[0]

    def vals_finais(self, lvl, add):
        """os 26 numeros que a REGUA vai pontuar: Equacao 1 + termo das habilidades,
        com a % lendo base+barras e SEM trava de 99."""
        bb = self.base_barras(lvl)
        v = [_mult(x, self.m) for x in bb]
        v = [v[i] + add[i] for i in range(26)]
        if not self.bf: return v
        return [aplica_buff(v[i], *self.bf[i], ref=bb[i]) if i in self.bf else v[i] for i in range(26)]

    def nota_final(self, lvl, add):
        return notaDe(self.vals_finais(lvl, add), self.arows)

    def grupos_de(self, i):
        g = []
        for b in MBK:
            if i in MB[b]: g.append(b)
        return g

    def dist(self, add):
        orc = self.orc
        grupos = []
        for b in MBK:
            if b in ("aerialStrength", "gk1"): continue
            ids = [i for i in MB[b] if i in self.R]
            if not ids: grupos.append((b, None, None)); continue
            g = np.zeros(26)
            for i in ids: g += self.ganho(i, add[i])
            nmax = int(np.searchsorted(ACCU, orc, side='right'))
            nmax = min(nmax, self.nmax_barra[b] + 1)          # MUDANCA D
            grupos.append((b, ACCU[:nmax], g[:nmax]))
        ga = np.zeros(26)
        for i in (7, 14):
            if i in self.R: ga += self.ganho(i, add[i])
        gk = self.ganho(21, add[21]) if 21 in self.R else np.zeros(26)
        t13 = self.tab.get(13); v13 = self.vb.get(13)
        NEG = -1e18
        dp = np.full(orc + 1, NEG); dp[0] = 0.0; tr = []
        for b, costs, gains in grupos:
            if costs is None: tr.append(None); continue
            nd = np.full(orc + 1, NEG); ch = np.full(orc + 1, -1, dtype=np.int16); pc = np.full(orc + 1, -1, dtype=np.int32)
            for n in range(len(costs)):
                cst = int(costs[n])
                if cst > orc: break
                cand = dp[:orc + 1 - cst] + gains[n]
                mask = cand > nd[cst:orc + 1]
                idx = np.nonzero(mask)[0]
                if len(idx):
                    nd[cst + idx] = cand[idx]; ch[cst + idx] = n; pc[cst + idx] = idx
            tr.append((b, ch, pc)); dp = nd
        opts = []
        MA = self.nmax_barra['aerialStrength']; MK = self.nmax_barra['gk1']    # MUDANCA D
        for a in range(MA + 1):
            ca = int(ACCU[a])
            if ca > orc: break
            for k in range(MK + 1):
                cst = ca + int(ACCU[k])
                if cst > orc: break
                val = ga[a] + gk[k]
                if t13 is not None:
                    b1 = min(99, self.base[13] + a + k); b0 = min(99, self.base[13])
                    vv = _mult(b1, self.m) + add[13]; v0 = _mult(b0, self.m) + add[13]
                    if 13 in self.bf:
                        p13, f13 = self.bf[13]
                        vv += math.ceil(b1 * p13 / 100 + f13)
                        v0 += math.ceil(b0 * p13 / 100 + f13)
                    val += t13[min(VMAX, max(0, vv))] - t13[min(VMAX, max(0, v0))]
                opts.append((cst, val, a, k))
        nd = np.full(orc + 1, NEG); ch = np.full(orc + 1, -1, dtype=np.int32); pc = np.full(orc + 1, -1, dtype=np.int32)
        for oi, (cst, val, a, k) in enumerate(opts):
            cand = dp[:orc + 1 - cst] + val
            mask = cand > nd[cst:orc + 1]
            idx = np.nonzero(mask)[0]
            if len(idx):
                nd[cst + idx] = cand[idx]; ch[cst + idx] = oi; pc[cst + idx] = idx
        tr.append(('PAR', ch, pc, opts)); dp = nd
        bc = int(np.argmax(dp))
        lvl = {b: 0 for b in MBK}; cc = bc
        for e in reversed(tr):
            if e is None: continue
            if e[0] == 'PAR':
                _, ch, pc, opts = e
                if ch[cc] >= 0:
                    cst, val, a, k = opts[ch[cc]]; lvl['aerialStrength'] = a; lvl['gk1'] = k; cc = int(pc[cc])
            else:
                b, ch, pc = e
                if ch[cc] >= 0: lvl[b] = int(ch[cc]); cc = int(pc[cc])
        return lvl, float(dp[bc])

    def aplicar(self, lvl, add):
        v = list(self.base)
        for b in MBK:
            n = lvl.get(b, 0)
            if n:
                for i in MB[b]: v[i] = min(99, v[i] + n)
        v = [_mult(x, self.m) for x in v]
        return [v[i] + add[i] for i in range(26)]

    def sem_add(self, lvl):
        """o valor pos-multiplicador, antes do boost do tecnico e dos impetos."""
        v = self.base_barras(lvl)
        return [_mult(x, self.m) for x in v]

    def base_barras(self, lvl):
        """MUDANCA F — PASSO 2 da Equacao 1: base + barras, travado em 99.
        SEM multiplicador, SEM tecnico, SEM impeto.
        E DAQUI que sai a % da habilidade (AS-DUAS-EQUACOES, Equacao 2)."""
        v = list(self.base)
        for b in MBK:
            n = lvl.get(b, 0)
            if n:
                for i in MB[b]: v[i] = min(99, v[i] + n)
        return v

    def gasto(self, lvl): return int(sum(ACCU[lvl.get(b, 0)] for b in MBK))

    def build(self, extra_add=None):
        best = None
        cands = [(None, None)]
        for x in self.L: cands.append((expand(x[2]), x[0]))
        for x in self.Rr: cands.append((expand(x[2]), x[0]))
        for a in self.L:
            va = expand(a[2])
            for b2 in self.Rr:
                vb = expand(b2[2]); cands.append(([va[i] + vb[i] for i in range(26)], a[0] + " + " + b2[0]))
        for ex, nome in cands:
            add = [self.nm[i] + (ex[i] if ex else 0) + (extra_add[i] if extra_add else 0) for i in range(26)]
            lvl, _ = self.dist(add)
            vals = self.aplicar(lvl, add)
            n = notaDe(vals, self.arows)
            if best is None or n > best['nota']:
                best = {'nota': n, 'lvl': lvl, 'vals': vals, 'fab': [nome] if nome else [], 'add': add}
        if best:
            g = self.orc - self.gasto(best['lvl'])
            if g > 0:
                pw = {b: max([r[1] for r in self.arows if r[0] in MB[b]] or [0]) for b in MBK}
                for b in sorted(MBK, key=lambda x: -pw[x]):
                    while best['lvl'][b] < self.nmax_barra[b]:  # MUDANCA D (era 25)
                        c2 = int(ACCU[best['lvl'][b] + 1] - ACCU[best['lvl'][b]])
                        if c2 > g: break
                        best['lvl'][b] += 1; g -= c2
                    if g <= 0: break
                best['vals'] = self.aplicar(best['lvl'], best['add'])
        return best


# ===================== ENTRADAS ANTIGAS — todas delegam =====================
def build_com_tecnico(card, TECS):
    r = build_turbo(card, TECS)
    return r, r.get('_aval', 0)

def build_completo(c, TECS, fila_incid=None):
    return build_completo2(c, TECS, fila_incid)

def build_tec_rapido(card, TECS, extra_add=None):
    return build_turbo(card, TECS)

def build_tec_inc(card, TECS):
    return build_turbo(card, TECS)

def build_filtrado(card, TECS):
    return build_turbo(card, TECS)


def fila_incidencia(path_html, tipo):
    s = open(path_html, encoding='utf-8').read()
    i = s.find('const FILA=') + 11; j = s.find('};', i)
    F = json.loads(s[i:j + 1])
    return {h: v for h, v in F.get(tipo, [])}


# ============ BUSCA CONJUNTA IMPETO x TECNICO — poda exata ============
def _cands_impeto(card):
    c = [(None, None)]
    for x in card.L: c.append((expand(x[2]), x[0]))
    for x in card.Rr: c.append((expand(x[2]), x[0]))
    for a in card.L:
        va = expand(a[2])
        for b in card.Rr:
            vb = expand(b[2]); c.append(([va[i] + vb[i] for i in range(26)], a[0] + " + " + b[0]))
    return c

def _por_m(TECS):
    from collections import defaultdict
    d = defaultdict(list)
    for t in TECS: d[t['m']].append(t)
    return d

def _assina(base, m, pes=None, nmax=26):
    """a escada de valores que ESTE multiplicador produz NESTE card. Escada igual, resultado igual."""
    ids = sorted(pes) if pes else range(26)
    return tuple(tuple(_mult(min(99, int(base[i])+ n), m) for n in range(nmax)) for i in ids)

def _grupos_de_m(base, TECS, pes=None, nmax=26):
    from collections import defaultdict
    porm = _por_m(TECS); g = defaultdict(lambda: [None, []])
    for m, tecs in porm.items():
        k = _assina(base, m, pes, nmax)
        if g[k][0] is None or m > g[k][0]: g[k][0] = m
        g[k][1].extend(tecs)
    return sorted(g.values(), key=lambda x: -x[0])


def build_mult(card_base, TECS, bf=None, tab=None, grupos=None, TU=None, piso_global=None):
    """OTIMO EXATO sobre barras x impeto x tecnico, COM o multiplicador tatico.

    O multiplicador e MONOTONO: maior nunca produz atributo menor, e a regua nunca
    piora com atributo maior. Entao o MAIOR multiplicador da um LIMITE SUPERIOR exato
    para todos os outros. Roda inteiro uma vez no maior e so reotimiza quem pode ganhar."""
    c = card_base
    cards = {}; bases = {}
    def pega(m):
        if m not in cards:
            card = Card(c, m=m, bf=bf)
            cards[m] = card; bases[m] = _base_turbo(card, TU=TU)
        return cards[m], bases[m]

    if TU is None:
        TU = tecnicos_uteis(Card(c, m=1.0), TECS)
    if not TU:
        card = Card(c, m=max(t['m'] for t in TECS) if TECS else 1.0, bf=bf)
        base, GR = _base_turbo(card, TU=TU)
        b0 = base[0]
        r = _sobra(card, {'nota': b0['n'], 'lvl': b0['lvl'], 'vals': b0['vals'],
                          'fab': [b0['nome']] if b0['nome'] else [], 'add': b0['add'],
                          'tecnico': None, 'tecnico_id': None, 'boost': []})
        r['m'] = card.m; r['arows'] = card.arows
        return r

    mmax = max(t['m'] for t in TU)
    cardM, (baseM, GRM) = pega(mmax)
    CANDS = impetos_uteis(cardM)
    porm = {}
    for t in TU: porm.setdefault(t['m'], []).append(t)
    dmaxM = {}
    for i, t in cardM.tab.items():
        lo = int(_mult(min(99, cardM.base[i]), cardM.m)); hi = int(min(VMAX - 1, _mult(min(99, cardM.base[i] + 25), cardM.m) + 40))
        dd = np.diff(t[lo:hi + 1]); dmaxM[i] = float(dd.max()) if len(dd) else 0.0
    ubimp = {b['k']: b['n'] for b in baseM}
    best = dict(_melhor_tecnico(cardM, baseM, GRM, porm[mmax], piso_global=piso_global))
    best['m'] = mmax; best['arows'] = cardM.arows
    for m in sorted(porm, reverse=True):
        if m == mmax: continue
        tecs = porm[m]
        dmx = max(sum(dmaxM.get(i, 0.0) for i in t['boost']) for t in tecs)
        _lim = best['nota'] if piso_global is None else max(best['nota'], piso_global)
        vivos = [CANDS[k] for k in range(len(CANDS)) if ubimp.get(k, -1e18) + dmx >= _lim - 1e-9]
        if not vivos: continue
        card = cards.get(m)
        if card is None:
            card = Card(c, m=m, bf=bf)
            cards[m] = card
        bs, gr = _base_turbo(card, vivos, TU=TU)
        r = dict(_melhor_tecnico(card, bs, gr, tecs, piso_global=piso_global))
        r['m'] = m; r['arows'] = card.arows
        if r['nota'] > best['nota']: best = r
    return best


def build_completo2(c, TECS, fila_incid=None):
    """OTIMO EXATO sobre barras x impeto x tecnico x habilidades.

    MUDANCA G (04/08) — AS RARAS ENTRAM.
    A rara e INERENTE ao card: ninguem adiciona, ou tem ou nao tem. Logo ela
    pertence a parte FIXA (`fab`), nunca ao pool de escolha (`falta`).
    Antes ela morava num campo `raras` separado que o motor nunca lia — 30% da
    base (1.847 de 6.201 cards) tem rara, e o motor via ZERO delas.
    As comuns competem entre si; as raras somam por cima (regra ja no buff_de)."""
    fab = list(c.get('fab') or []) + list(c.get('raras') or [])
    pes = {r[0] for r in c['arows'] if r[1]}
    def util(h):
        v = POR_NOME.get(h)
        return bool(v and v['efeito'] and any(int(i) in pes for i in v['efeito']))
    cand = [h for h in (c.get('falta') or []) if util(h)]
    outros = [h for h in (c.get('falta') or []) if not util(h)]
    # ===== REGRA DO EMPATE (Luis, 08/08) =====
    # "no caso de empate utiliza a que e mais utilizada pela comunidade. E as outras
    #  que empatam com ela vao pra sugestao."
    # `_pop` = quanto a comunidade usa aquela habilidade NESTA funcao (a tabela FILA
    # do encaixe, entregue em fila_incid). Ela NAO decide nota — so desempata, e o
    # desempate passa a ser DETERMINISTICO em vez de "quem apareceu primeiro".
    _inc = fila_incid or {}
    def _pop(hs):
        return sum(_inc.get(h, 0) for h in hs)
    cand = sorted(cand, key=lambda h: (-_inc.get(h, 0), h))
    # ===================== CORTE 8 — DEDUPLICACAO POR EFEITO =====================
    # ✅ CHANCE ZERO. Nao e heuristica: nao corta candidato nenhum.
    #
    # O motor rodava o DP inteiro das barras para CADA combinacao de 5 habilidades.
    # Com o pool antigo isso nao doia (media de 1,16 combinacao por card) porque o
    # campo `falta` estava furado. Com o pool consertado vira C(33,5) = 237.336 DPs.
    #
    # A SACADA: as comuns COMPETEM por atributo (vale a maior) e as raras SOMAM.
    # Logo combinacoes DIFERENTES produzem o MESMO vetor de buff — e buff igual da
    # nota igual, porque o DP so enxerga o buff. Basta rodar uma por efeito distinto.
    #
    # A assinatura so considera atributo COM PESO: atributo de peso zero e invisivel
    # ao motor (regra ja fechada), entao diferenca ali nao muda nada.
    #
    # MEDIDO: reducao de 7x a 19x, crescendo com o tamanho do pool.
    #   cand 10 -> 252 combos, 36 distintos     (7,0x)
    #   cand 11 -> 462 combos, 24 distintos    (19,2x)
    #   cand 12 -> 792 combos, 90 distintos     (8,8x)
    #   cand 13 -> 1.287 combos, 168 distintos  (7,7x)
    # O custo de calcular a assinatura e desprezivel perto do DP.
    #
    # ⚠️ UNICA consequencia: entre combinacoes de efeito IDENTICO o motor passa a
    #    devolver uma representante fixa. A NOTA e a mesma; a lista de habilidades
    #    pode variar entre empates exatos. E o mesmo caso ja documentado de
    #    "divergencia so em empate exato".
    # CORTE8 = False desliga a deduplicacao (so para medir o corte contra ele mesmo)
    # ============== CORTE 11 — GRUPOS DE EFEITO IDENTICO (08/08) ==============
    # ✅ CHANCE ZERO. Nao e poda: e nao enumerar duas vezes a MESMA coisa.
    #
    # `buff_de` depende SO do multiset de (tipo, efeito) das habilidades. Duas
    # habilidades com o MESMO tipo e o MESMO efeito nos 26 atributos sao, para o
    # calculo, a mesma habilidade — inclusive na regra da metade, que enxerga
    # valores, nao nomes. Logo o que importa e QUANTAS de cada grupo entram, nao
    # quais. Enumerar por grupo cobre exatamente as mesmas assinaturas.
    #
    # PROVA MEDIDA (08/08): 320 pares card x funcao, enumeracao completa contra a
    # agrupada. Conjunto de assinaturas IDENTICO em 320 de 320, zero divergencia.
    #
    # Por que nos 26 atributos e nao so nos de peso: agrupando pelos de peso corta
    # mais (9,2x contra 6,9x), mas duas do grupo poderiam diferir num atributo sem
    # peso — a nota seria a mesma e os valores MOSTRADOS na ficha, nao. Nos 26 as
    # representantes sao identicas em tudo. Escolha do Luis: "vai entregar a melhor
    # combinacao possivel" — na duvida, a versao sem efeito colateral nenhum.
    #
    # ⚠️ Isto NAO substitui o CORTE 8: ele continua deduplicando o que sobra (grupos
    #    diferentes podem colidir na assinatura restrita aos pesos).
    # CORTE11 = False desliga (so para medir o corte contra ele mesmo)
    def _combos_por_grupo(cs):
        g = {}
        for h in cs:
            v = POR_NOME.get(h) or {}
            e = v.get('efeito') or {}
            k = (v.get('tipo'),) + tuple(sorted(
                (int(i), d.get('pct', 0), d.get('flat', 0)) for i, d in e.items()))
            g.setdefault(k, []).append(h)
        # dentro do grupo, o representante e o MAIS USADO pela comunidade
        reps = [sorted(v, key=lambda h: (-_inc.get(h, 0), h)) for v in g.values()]

        def rec(i, falta, at):
            if falta == 0:
                yield tuple(at); return
            if i >= len(reps):
                return
            gg = reps[i]
            for t in range(min(len(gg), falta), -1, -1):
                yield from rec(i + 1, falta - t, at + gg[:t])
        return rec(0, 5, [])

    _enum = (_combos_por_grupo(cand) if globals().get('CORTE11', True)
             else itertools.combinations(cand, 5))

    if len(cand) <= 5:
        combos = [tuple(cand)]
    elif not globals().get('CORTE8', True):
        combos = list(_enum)
    else:
        _vistos = {}
        for _e in _enum:
            _bf = buff_de(fab + list(_e))
            _sig = tuple(sorted((i, p, f) for i, (p, f) in _bf.items() if i in pes))
            _ant = _vistos.get(_sig)
            if _ant is None or _pop(_e) > _pop(_ant):
                _vistos[_sig] = _e
        # ============== CORTE 9 — PODA POR DOMINANCIA (05/08 noite) ==============
        # ✅ CHANCE ZERO. Nao e heuristica: nao pode perder o otimo. A prova:
        #
        #   1. buff maior nunca abaixa atributo: ganho = ceil(ref*pct/100 + flat)
        #      e crescente em pct e em flat, e o ganho SOMA no atributo.
        #   2. a regua e crescente em cada atributo: acima do alvo _bon so soma,
        #      abaixo do alvo _fal so encolhe. Nunca paga menos por valor maior.
        #   3. as habilidades nao gastam orcamento (sao 5 vagas, sempre as 5), entao
        #      trocar de combinacao NAO tira ponto de barra de lugar nenhum.
        #
        #   Logo, se a assinatura A tem (pct,flat) >= B em TODO atributo com peso,
        #   entao para QUALQUER escolha de barra/impeto/tecnico a nota de A e >= a
        #   de B. B nunca pode ser a unica dona do otimo — pode no maximo empatar.
        #
        # POR QUE PRECISOU: ate 04/08 a dedup do CORTE 8 sozinha cortava de 7x a
        # 19x, porque habilidades de mesmo efeito colidiam na mesma assinatura.
        # A REGRA DA METADE acabou com a colisao (a segunda do mesmo efeito soma
        # meio), as assinaturas viraram quase todas distintas e o lote passou de
        # ~80 s para mais de 900 s. A dominancia recupera o corte por outro
        # caminho: combinacao que carrega a habilidade fraca no lugar da forte
        # e dominada pela troca.
        #
        # ⚠️ MESMA consequencia ja documentada do CORTE 8: entre EMPATES EXATOS a
        #    representante devolvida pode mudar. A NOTA e a mesma.
        # CORTE9 = False desliga a poda (so para medir a poda contra ela mesma)
        if globals().get('CORTE9', True) and len(_vistos) > 1:
            _ordem = sorted(pes)
            def _vet(_sig):
                _d = {i: (p, f) for i, p, f in _sig}
                return tuple(x for i in _ordem for x in _d.get(i, (0, 0)))
            _itens = [(_vet(s), e) for s, e in _vistos.items()]
            # do mais "forte" para o mais fraco: quem domina aparece antes
            _itens.sort(key=lambda t: -sum(t[0]))
            # ===== CORTE 9 VETORIZADO (10/08/2026) =====
            # MESMA poda, MESMA resposta — so deixou de ser um-contra-um em Python.
            # MEDIDO no perfil: com 24 mil candidatos a versao antiga fazia 196
            # MILHOES de comparacoes e comia ~20% do tempo da linha. Aqui a
            # comparacao vira uma operacao de matriz do numpy.
            # A ordem de visita e identica, entao o representante escolhido entre
            # empates tambem e o mesmo. Nao e aproximacao.
            _V = np.asarray([t[0] for t in _itens], dtype=np.int32)
            _K = np.empty((len(_itens), _V.shape[1]), dtype=np.int32)
            _nk = 0
            _mant = []
            for _j in range(len(_itens)):
                _v = _V[_j]
                if _nk and bool((_K[:_nk] >= _v).all(axis=1).any()):
                    continue
                _K[_nk] = _v; _nk += 1
                _mant.append(_itens[_j])
            combos = [e for _, e in _mant]
        else:
            combos = list(_vistos.values())
    TU = tecnicos_uteis(Card(c, m=1.0), TECS)
    # CORTE 13 — a melhor nota ja encontrada vira piso para as combinacoes seguintes.
    # A ORDEM de visita nao muda, entao o desempate por popularidade fica intacto.
    _pg = [None] if not globals().get('CORTE13', True) else [-1e18]
    best = None
    for esc in combos:
        hs = fab + list(esc); bf = buff_de(hs)
        r = build_mult(c, TECS, bf if bf else None, TU=TU,
                       piso_global=(None if _pg[0] is None else _pg[0]))
        if _pg[0] is not None and r['nota'] > _pg[0]: _pg[0] = r['nota']
        # o buff JA esta dentro de r['vals'] e de r['nota'] — o otimizador inteiro
        # passou a pontuar o objetivo final. Nao reaplicar.
        vf = r['vals']; n = r['nota']
        vagas = 5 - len(esc); extra = []
        if vagas > 0 and outros:
            key = (lambda h: -fila_incid.get(h, 0)) if fila_incid else (lambda h: 0)
            extra = sorted(outros, key=key)[:vagas]
        _melhor = (best is None or n > best['nota'] or
                   (n == best['nota'] and
                    _pop(list(esc) + extra) > _pop(best.get('habilidades') or [])))
        if _melhor:
            best = dict(r); best['nota'] = n; best['vals'] = vf
            best['habilidades'] = list(esc) + extra; best['buff'] = bf
            # as TRES PROFUNDIDADES da mesma build, para conferir contra o jogo:
            cd = Card(c, m=r.get('m', 1.0), bf=bf)
            best['vals_carta'] = cd.base_barras(r['lvl'])          # so base + barrinhas
            best['vals_tela']  = cd.aplicar(r['lvl'], r['add'])    # EQUACAO 1 = a tela do eF
            # best['vals'] ja e a EQUACAO 2 = com as habilidades
    return best


# ============ DP INCREMENTAL ============
def _grupos(card, add, quais=None):
    # ============== CORTE 12 — EQUIVALENCIA DE GRUPO (10/08/2026) ==============
    # Ordem do Luis: "se uma coisa e igual a outra, a gente corta e faz uma soma so".
    # MEDIDO (Messi, Centroavante fixo, orc 62): _grupos e chamado 5.729 vezes e o
    # bloco PAR tem so 11 chaves distintas. O resto e trabalho identico repetido.
    # Um grupo `b` so depende de add[i] dos atributos DELE; o PAR so depende de
    # add[7], add[14], add[21] e add[13]. Mesma chave -> mesmo resultado, exato.
    # Isto NAO e aproximacao: a saida e bit a bit a mesma. So nao recalcula.
    orc = card.orc; G = {}
    C = card.__dict__.get('_gcache')
    if C is None: C = card._gcache = {}
    for b in MBK:
        if b in ("aerialStrength", "gk1"): continue
        if quais is not None and b not in quais: continue
        ids = [i for i in MB[b] if i in card.R]
        if not ids: G[b] = None; continue
        ck = (b,) + tuple(add[i] for i in ids)
        v = C.get(ck)
        if v is None:
            g = np.zeros(26)
            for i in ids: g += card.ganho(i, add[i])
            nmax = int(np.searchsorted(ACCU, orc, side='right'))
            nmax = min(nmax, card.nmax_barra[b] + 1)              # MUDANCA D
            v = C[ck] = (ACCU[:nmax].astype(int), g[:nmax])
        G[b] = v
    if quais is not None and 'PAR' not in quais: return G
    ck = ('PAR', add[7], add[14], add[21], add[13])
    v = C.get(ck)
    if v is not None:
        G['PAR'] = v
        return G
    ga = np.zeros(26)
    for i in (7, 14):
        if i in card.R: ga += card.ganho(i, add[i])
    gk = card.ganho(21, add[21]) if 21 in card.R else np.zeros(26)
    t13 = card.tab.get(13)
    opts = []
    MA = card.nmax_barra['aerialStrength']; MK = card.nmax_barra['gk1']        # MUDANCA D
    for a in range(MA + 1):
        ca = int(ACCU[a])
        if ca > orc: break
        for k in range(MK + 1):
            cst = ca + int(ACCU[k])
            if cst > orc: break
            val = ga[a] + gk[k]
            if t13 is not None:
                b1 = min(99, card.base[13] + a + k); b0 = min(99, card.base[13])
                vv = _mult(b1, card.m) + add[13]; v0 = _mult(b0, card.m) + add[13]
                if 13 in card.bf:
                    p13, f13 = card.bf[13]
                    vv += math.ceil(b1 * p13 / 100 + f13)
                    v0 += math.ceil(b0 * p13 / 100 + f13)
                val += t13[min(VMAX, max(0, vv))] - t13[min(VMAX, max(0, v0))]
            opts.append((cst, val, a, k))
    melhor = {}
    for cst, val, a, k in opts:
        if cst not in melhor or val > melhor[cst][0]: melhor[cst] = (val, a, k)
    G['PAR'] = C[ck] = [(c2, v2, a2, k2) for c2, (v2, a2, k2) in sorted(melhor.items())]
    return G

def _dp(card, G):
    orc = card.orc; NEG = -1e18
    dp = np.full(orc + 1, NEG); dp[0] = 0.0; tr = []
    for b in MBK:
        if b in ("aerialStrength", "gk1"): continue
        g = G[b]
        if g is None: tr.append(None); continue
        costs, gains = g
        nd = np.full(orc + 1, NEG); ch = np.full(orc + 1, -1, dtype=np.int16); pc = np.full(orc + 1, -1, dtype=np.int32)
        for n in range(len(costs)):
            cst = int(costs[n])
            if cst > orc: break
            cand = dp[:orc + 1 - cst] + gains[n]
            idx = np.nonzero(cand > nd[cst:orc + 1])[0]
            if len(idx): nd[cst + idx] = cand[idx]; ch[cst + idx] = n; pc[cst + idx] = idx
        tr.append((b, ch, pc)); dp = nd
    opts = G['PAR']
    nd = np.full(orc + 1, NEG); ch = np.full(orc + 1, -1, dtype=np.int32); pc = np.full(orc + 1, -1, dtype=np.int32)
    for oi, (cst, val, a, k) in enumerate(opts):
        cand = dp[:orc + 1 - cst] + val
        idx = np.nonzero(cand > nd[cst:orc + 1])[0]
        if len(idx): nd[cst + idx] = cand[idx]; ch[cst + idx] = oi; pc[cst + idx] = idx
    tr.append(('PAR', ch, pc, opts)); dp = nd
    bc = int(np.argmax(dp)); lvl = {b: 0 for b in MBK}; cc = bc
    for e in reversed(tr):
        if e is None: continue
        if e[0] == 'PAR':
            _, ch2, pc2, op = e
            if ch2[cc] >= 0:
                cst, val, a, k = op[ch2[cc]]; lvl['aerialStrength'] = a; lvl['gk1'] = k; cc = int(pc2[cc])
        else:
            b, ch2, pc2 = e
            if ch2[cc] >= 0: lvl[b] = int(ch2[cc]); cc = int(pc2[cc])
    return lvl


# ============ FILTROS: so quem tem chance de ser topo ============
def tecnicos_uteis(card, TECS):
    """CORTE 3: agrupa tecnicos equivalentes (mesmo par de atributos COM PESO) e fica
    com o de MAIOR TATICA de cada grupo."""
    from collections import defaultdict
    pes = set(card.R); g = defaultdict(list)
    for t in TECS:
        k = tuple(sorted(i for i in t['boost'] if i in pes))
        g[k].append(t)
    out = []
    for k, v in g.items():
        if not k: continue
        v = sorted(v, key=lambda x: (-x['tat'], x['nome']))
        r = dict(v[0]); r['boost'] = list(k)
        r['equivalentes'] = [x['nome'] for x in v]
        out.append(r)
    return out

def impetos_uteis(card):
    """deduplica impetos pelo efeito nos atributos COM PESO."""
    pes = set(card.R); vis = {}; out = []
    for ex, nome in _cands_impeto(card):
        k = tuple((i, ex[i]) for i in range(26) if ex and ex[i] and i in pes)
        if k in vis: continue
        vis[k] = 1; out.append((ex, nome))
    return out


# ============ DP com PREFIXO CACHEADO ============
def _dp_seq(card, G, ordem):
    orc = card.orc; NEG = -1e18
    dp = np.full(orc + 1, NEG); dp[0] = 0.0; tr = []
    for b in ordem:
        g = G.get(b)
        if g is None: tr.append(None); continue
        if b == 'PAR':
            nd = np.full(orc + 1, NEG); ch = np.full(orc + 1, -1, dtype=np.int32); pc = np.full(orc + 1, -1, dtype=np.int32)
            for oi, (cst, val, a, k) in enumerate(g):
                cand = dp[:orc + 1 - cst] + val
                idx = np.nonzero(cand > nd[cst:orc + 1])[0]
                if len(idx): nd[cst + idx] = cand[idx]; ch[cst + idx] = oi; pc[cst + idx] = idx
            tr.append(('PAR', ch, pc, g)); dp = nd
        else:
            costs, gains = g
            nd = np.full(orc + 1, NEG); ch = np.full(orc + 1, -1, dtype=np.int16); pc = np.full(orc + 1, -1, dtype=np.int32)
            for n in range(len(costs)):
                cst = int(costs[n])
                if cst > orc: break
                cand = dp[:orc + 1 - cst] + gains[n]
                idx = np.nonzero(cand > nd[cst:orc + 1])[0]
                if len(idx): nd[cst + idx] = cand[idx]; ch[cst + idx] = n; pc[cst + idx] = idx
            tr.append((b, ch, pc)); dp = nd
    return dp, tr

def _recupera(card, tr, bc):
    lvl = {b: 0 for b in MBK}; cc = bc
    for e in reversed(tr):
        if e is None: continue
        if e[0] == 'PAR':
            _, ch, pc, op = e
            if ch[cc] >= 0:
                cst, val, a, k = op[ch[cc]]; lvl['aerialStrength'] = a; lvl['gk1'] = k; cc = int(pc[cc])
        else:
            b, ch, pc = e
            if ch[cc] >= 0: lvl[b] = int(ch[cc]); cc = int(pc[cc])
    return lvl

def _base_turbo(card, cands=None, TU=None):
    """a parte que NAO depende do tecnico: o melhor DP de cada impeto. E o pedaco caro."""
    if cands is None: cands = impetos_uteis(card)
    GRUPOS = [b for b in MBK if b not in ("aerialStrength", "gk1")] + ['PAR']
    base = []
    for k, (ex, nome) in enumerate(cands):
        add = [card.nm[i] + (ex[i] if ex else 0) for i in range(26)]
        G = _grupos(card, add)
        dp, tr = _dp_seq(card, G, GRUPOS)
        bc = int(np.argmax(dp)); lvl = _recupera(card, tr, bc)
        vals = card.vals_finais(lvl, add)
        e = {'nota': notaDe(vals, card.arows), 'lvl': lvl, 'vals': vals, 'add': add}
        e = _sobra(card, e)
        base.append({'n': e['nota'], 'add': add, 'G': G, 'lvl': e['lvl'], 'vals': e['vals'], 'nome': nome, 'k': k})
    base.sort(key=lambda x: -x['n'])
    # CORTE DE MARGEM (autorizado pelo Luis, 02/08): o tecnico nunca virou mais que 16,2
    # pontos em medicao exata; margem de 50 = 3x a maior virada observada.
    # ⚠️ ESTE E O UNICO CORTE NAO-EXATO DO MOTOR.
    # Autorizado pelo Luis em 02/08 ("pode cortar quem tem 0,9% abaixo"), com a
    # medicao de que o tecnico nunca virou mais que 16,2 pontos. Margem de 50 = 3x.
    #
    # 🔴 AVISO DA SESSAO QUE O CRIOU (04/08): "isso foi medido com o `falta` furado.
    #    Com pool de mediana 12 a habilidade pode virar muito mais que 16,2.
    #    REMECAM essa margem, ou o motor novo vai cortar impeto bom em silencio."
    #
    # REMEDIDO em 04/08 com o pool novo, cada card com corte e SEM corte nenhum:
    #    4 de 4 identicas, delta 0,0000 (Darmian e Carreras, pool atual e pool novo)
    # ⚠️ 4 cards NAO fecham nada — a margem original foi validada em 24.
    #    Antes de rodar em producao com o pool novo, refazer com amostra de verdade.
    #
    # MARG_OVERRIDE existe so para esse teste: None = 50, 1e18 = sem corte.
    # ================= MARGEM EXATA (04/08/2026) =================
    # ❌ ANTES: MARG = 50.0, chutado como 3x a maior virada observada (16,2).
    #    A sessao que o criou avisou: "foi medido com o `falta` furado; remecam".
    #    REMEDIDO com o pool novo, 30 cards aleatorios, cada um com e SEM corte:
    #       PERDEU O OTIMO em 1 de 30 (Pape Gueye, Meia central armador, -6,2)
    #    Ordem do Luis, 04/08: "no final das contas, otimizado ou nao, eu preciso
    #    do melhor resultado possivel. Disso eu nao abro mao."
    #
    # ✅ AGORA: limite CALCULADO, nao chutado. O tecnico mexe em no maximo 2
    #    atributos, +1 em cada. Entao o ganho maximo que qualquer tecnico pode
    #    dar e a soma dos DOIS MAIORES ganhos marginais da tabela de pontos:
    #
    #        para qualquer build fixa:  nota_com_tecnico <= nota_sem + d1 + d2
    #        e nota_sem(impeto) <= n do impeto. Logo o impeto que estiver mais
    #        de (d1+d2) abaixo do melhor NAO TEM COMO virar.  ✅ CHANCE ZERO.
    #
    #    `dmax[i]` sai do np.diff da tabela real, na faixa alcancavel — o mesmo
    #    numero que o corte 6 ja usa para o tecnico. Nao e formula analitica
    #    (foi tentando deduzir isso na mao que eu errei duas vezes antes).
    _dmax = {}
    for _i, _t in card.tab.items():
        _lo = int(_mult(min(99, card.base[_i]), card.m))
        _hi = int(min(VMAX - 1, _mult(min(99, card.base[_i] + 25), card.m) + 40))
        _d = np.diff(_t[_lo:_hi + 1])
        _dmax[_i] = float(_d.max()) if len(_d) else 0.0
    if TU:
        # ✅ APERTADO: o teto dos tecnicos que REALMENTE existem, nao os dois
        #    maiores da tabela inteira. Cada tecnico mexe num par especifico.
        MARG = max((sum(_dmax.get(_i, 0.0) for _i in _t['boost']) for _t in TU), default=0.0)
    else:
        _dm = sorted(_dmax.values(), reverse=True)
        MARG = float(sum(_dm[:2]))
    if globals().get('MARG_OVERRIDE') is not None:
        MARG = globals()['MARG_OVERRIDE']
    corte = base[0]['n'] - MARG
    base = [b for b in base if b['n'] >= corte]
    return base, GRUPOS

def _sobra(card, best):
    """REGRA DE OURO: nunca sobra ponto de barra.
    ⚠️ copia o lvl antes de mexer — senao mexe no lvl guardado no `base` dos impetos,
    que e reaproveitado entre tecnicos e entre multiplicadores. (bug de aliasing, 04/08)"""
    best['lvl'] = dict(best['lvl'])
    g = card.orc - card.gasto(best['lvl'])
    if g > 0:
        pw = {b: max([r[1] for r in card.arows if r[0] in MB[b]] or [0]) for b in MBK}
        for b in sorted(MBK, key=lambda x: -pw[x]):
            while best['lvl'][b] < card.nmax_barra[b]:          # MUDANCA D (era 25)
                c2 = int(ACCU[best['lvl'][b] + 1] - ACCU[best['lvl'][b]])
                if c2 > g: break
                best['lvl'][b] += 1; g -= c2
            if g <= 0: break
        best['vals'] = card.vals_finais(best['lvl'], best['add'])
        best['nota'] = notaDe(best['vals'], card.arows)
    return best

def _melhor_tecnico(card, base, GRUPOS, TU, por_tecnico=False, piso_global=None):
    """percorre os tecnicos reaproveitando o prefixo do DP."""
    def grupos_de_attr(i):
        s2 = set()
        for b in MBK:
            if i in MB[b]: s2.add('PAR' if b in ('aerialStrength', 'gk1') else b)
        return s2
    dmax = {}
    for i, t in card.tab.items():
        lo = int(_mult(min(99, card.base[i]), card.m)); hi = int(min(VMAX - 1, _mult(min(99, card.base[i] + 25), card.m) + 40))
        d = np.diff(t[lo:hi + 1]); dmax[i] = float(d.max()) if len(d) else 0.0
    porconj = {}
    for t in TU:
        cj = frozenset().union(*[grupos_de_attr(i) for i in t['boost']]) if t['boost'] else frozenset()
        porconj.setdefault(cj, []).append(t)
    lb = base[0]['n']
    for t in TU:
        for b0 in base:
            lv2 = dict(b0['lvl']); a2 = list(b0['add'])
            for i in t['boost']: a2[i] += 1
            n = card.nota_final(lv2, a2)
            if n > lb: lb = n
    best = None; aval = 0; porT = {}
    # ===== TRAVA DINAMICA (10/08/2026) — ordem do Luis =====
    # "se voce ve que do quinquagesimo pra tras ele nao alcanca, nao tem por que
    #  fazer cruzamento com ele".
    # A trava ja existia, mas usava um piso FIXO calculado no comeco: mesmo depois
    # de achar uma nota melhor no meio do caminho, ela continuava comparando com o
    # piso velho. Agora o piso sobe junto com a melhor nota ja encontrada.
    # E poda por LIMITE SUPERIOR: `dmax` e o teto do que aquele tecnico pode somar.
    # Se o teto nao alcanca o que ja foi achado, aquele cruzamento nao pode ganhar.
    # O otimo e o mesmo — nao e heuristica, nao e amostragem.
    # Ordena do mais promissor pro menos, para o piso subir cedo.
    # ===== CORTE 13 (10/08/2026) — o piso vem de FORA, nao so desta combinacao =====
    # Ordem do Luis: "se voce ve que ele nao vai conseguir alcancar, nao tem por que
    # fazer cruzamento com ele" — agora valendo ENTRE combinacoes de habilidade, nao
    # so dentro de uma.
    # A trava aqui ja e por LIMITE SUPERIOR (`dmax` = teto do que o tecnico soma).
    # Passando a melhor nota ja encontrada no card inteiro, uma combinacao que nao
    # alcanca nem tenta a varredura dos tecnicos. O otimo global nao pode ser podado:
    # o teto dele e >= a nota dele, que e >= o piso.
    _piso = [lb if piso_global is None else max(lb, piso_global)]
    _tdmax = {id(t): sum(dmax.get(i, 0.0) for i in t['boost']) for t in TU}
    _conj = sorted(porconj.items(),
                   key=lambda kv: -max(_tdmax.get(id(t), 0.0) for t in kv[1]))
    for cj, tecs in _conj:
        tecs = sorted(tecs, key=lambda t: -_tdmax.get(id(t), 0.0))
        ordem = [b for b in GRUPOS if b not in cj] + [b for b in GRUPOS if b in cj]
        for b0 in sorted(base, key=lambda x: -x['n']):
            dmx = max(_tdmax.get(id(t), 0.0) for t in tecs)
            if b0['n'] + dmx < _piso[0] - 1e-9: continue
            dp0, tr0 = _dp_seq(card, b0['G'], [b for b in ordem if b not in cj])
            for t in tecs:
                delta = _tdmax.get(id(t), 0.0)
                if b0['n'] + delta < _piso[0] - 1e-9: continue
                aval += 1
                badd = [0] * 26
                for i in t['boost']: badd[i] += 1
                add = [b0['add'][i] + badd[i] for i in range(26)]
                Gn = _grupos(card, add, cj)
                dp = dp0; tr = list(tr0); orc = card.orc; NEG = -1e18
                for b in [x for x in ordem if x in cj]:
                    g = Gn.get(b)
                    if g is None: tr.append(None); continue
                    if b == 'PAR':
                        nd = np.full(orc + 1, NEG); ch = np.full(orc + 1, -1, dtype=np.int32); pc = np.full(orc + 1, -1, dtype=np.int32)
                        for oi, (cst, val, a, k) in enumerate(g):
                            cand = dp[:orc + 1 - cst] + val
                            idx = np.nonzero(cand > nd[cst:orc + 1])[0]
                            if len(idx): nd[cst + idx] = cand[idx]; ch[cst + idx] = oi; pc[cst + idx] = idx
                        tr.append(('PAR', ch, pc, g)); dp = nd
                    else:
                        costs, gains = g
                        nd = np.full(orc + 1, NEG); ch = np.full(orc + 1, -1, dtype=np.int16); pc = np.full(orc + 1, -1, dtype=np.int32)
                        for n2 in range(len(costs)):
                            cst = int(costs[n2])
                            if cst > orc: break
                            cand = dp[:orc + 1 - cst] + gains[n2]
                            idx = np.nonzero(cand > nd[cst:orc + 1])[0]
                            if len(idx): nd[cst + idx] = cand[idx]; ch[cst + idx] = n2; pc[cst + idx] = idx
                        tr.append((b, ch, pc)); dp = nd
                bc = int(np.argmax(dp)); lvl = _recupera(card, tr, bc)
                vals = card.vals_finais(lvl, add); n = notaDe(vals, card.arows)
                r = {'nota': n, 'lvl': lvl, 'vals': vals, 'fab': [b0['nome']] if b0['nome'] else [], 'add': add,
                     # ⛔ 14/08: vai o ID junto. Sao 1.664 tecnicos e 1.528 nomes —
                     # 5 "Jose Mourinho" diferentes. So o nome nao diz qual entrou.
                     'tecnico': t['nome'], 'tecnico_id': t.get('id'),
                     'tat': t['tat'], 'boost': [ATTRS_EF[i] for i in t['boost']],
                     'tec_equivalentes': t.get('equivalentes', [])}
                if por_tecnico and (t['nome'] not in porT or n > porT[t['nome']]['nota']):
                    porT[t['nome']] = r
                if best is None or n > best['nota']:
                    best = r
                    if n > _piso[0]: _piso[0] = n
    if best is None:
        b0 = base[0]; best = {'nota': b0['n'], 'lvl': b0['lvl'], 'vals': b0['vals'],
                              'fab': [b0['nome']] if b0['nome'] else [], 'add': b0['add'], 'tecnico': None, 'tecnico_id': None, 'boost': []}
    best = _sobra(card, dict(best)); best['_aval'] = aval
    if por_tecnico:
        return best, {k: _sobra(card, dict(v)) for k, v in porT.items()}
    return best

def build_turbo(card, TECS):
    """otimo exato sobre (impeto x tecnico), com prefixo do DP reaproveitado."""
    TU_ = tecnicos_uteis(card, TECS)
    base, GRUPOS = _base_turbo(card, TU=TU_)
    return _melhor_tecnico(card, base, GRUPOS, TU_)
