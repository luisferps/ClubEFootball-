# -*- coding: utf-8 -*-
"""
O OTIMIZADOR DE BARRAS — a melhor distribuicao para UM cenario dado.

O que ele faz (na palavra do Luis, 25/08):
  "o otimizador e pra ele pegar os impetos, tecnico e habilidades adicionadas e
   pegar a melhor combinacao de barrinhas possivel pra aquele cenario."

Ou seja: o usuario escolhe impeto, tecnico e habilidades; ISSO FICA FIXO; e o
servidor acha onde por cada ponto de barra para a nota ser a maior possivel.

⛔ Isto e PORTE FIEL do `motor.py:Card.dist` — a mesma programacao dinamica, a
   mesma tabela da regua, o mesmo par aereo+gk1, a mesma trava do nivel maximo.
   Nao e uma versao "parecida". Se divergir do motor, e defeito, nao escolha.

⛔ NENHUM numero da regua mora aqui: degraus, teto da punicao, valor maximo,
   custo por nivel e barras vem todos do banco, pela Regua.
"""
import math
import numpy as np

TETO = 99
PISO = 40


def _mult(x, m):
    if m == 1.0:
        return x
    return min(TETO, max(PISO, x + int(x * (m - 1))))


def _multv(a, m):
    if m == 1.0:
        return a.astype(int)
    return np.minimum(TETO, np.maximum(PISO, a + np.trunc(a * (m - 1)))).astype(int)


class Otimizador:
    """Pre-computa o que nao muda e roda o DP. Um por avaliacao."""

    def __init__(self, regua, base, orcamento, arows, add, buff, m):
        self.r     = regua
        self.base  = list(base)
        self.orc   = int(orcamento or 0)
        self.m     = float(m)
        self.add   = list(add)          # nm + impeto + tecnico, ja somados
        self.bf    = dict(buff or {})   # {idx: (pct, flat)}
        self.arows = [t for t in arows if t[2]]           # (idx, alvo, peso), peso != 0
        self.R     = {i: (alvo, peso) for i, alvo, peso in self.arows}

        self.VMAX  = self.r.vmax
        self.DEG   = self.r.degraus
        self.TPUN  = self.r.teto_punicao
        self.MB    = self.r.barra
        self.MBK   = list(self.MB)
        self.ACCU  = self._accu()

        self.tab = {i: self._pts_regua(a, p) for i, (a, p) in self.R.items()}
        self.vb  = {i: _multv(np.minimum(TETO, self.base[i] + np.arange(26)), self.m) for i in self.R}
        self.bb  = {i: np.minimum(TETO, self.base[i] + np.arange(26)) for i in self.R}
        self.nmax_barra = {b: self._nivel_max(b) for b in self.MBK}

    # ---------------------------------------------------------------- insumos
    def _accu(self):
        """acumulado de custo por nivel, do banco. ACCU[0]=0."""
        a = [0] * 26
        for n in range(1, 26):
            v = self.r.custo.get(n)
            if v is None:
                raise ValueError('custo_nivel sem o nivel %d' % n)
            a[n] = int(v)
        return np.array(a)

    def _nivel_max(self, barra):
        """o jogo BLOQUEIA o nivel quando o MENOR atributo da barra chega a 99 —
        nao deixa nem gastar o ponto (medido no Messi, 15/08)."""
        ids = self.MB[barra]
        return max(0, min(25, TETO - min(int(self.base[i]) for i in ids)))

    def _pts_regua(self, alvo, peso):
        t = np.zeros(self.VMAX + 1)
        for v in range(self.VMAX + 1):
            d = v - alvo
            if d >= 0:
                s = 0.0
                k = 1
                while k <= d:
                    if k > len(self.DEG):
                        break
                    s += self.DEG[k - 1] * peso
                    k += 1
                t[v] = s
            else:
                if peso == 1:
                    t[v] = 0.0            # acessorio NAO pune
                else:
                    inc = 0.25 * peso / 12
                    s = 0.0
                    k = 1
                    lim = min(int(-d), self.TPUN)
                    while k <= lim:
                        s += (1 + (k - 1) * inc) * peso
                        k += 1
                    t[v] = -s
        return t

    def _buff_esc(self, i):
        pct, flat = self.bf[i]
        return np.ceil(self.bb[i] * pct / 100.0 + flat).astype(int)

    def _ganho(self, i, add_i):
        t = self.tab[i]
        v = self.vb[i] + add_i
        if i in self.bf:
            v = v + self._buff_esc(i)
        g = t[np.clip(v, 0, self.VMAX)]
        return g - g[0]

    # ------------------------------------------------------------------- o DP
    def melhor(self):
        """Devolve (lvl, ganho). O par aereo+gk1 anda junto porque os dois mexem
        no atributo 13 (Salto) — otimizar separado dava conta errada."""
        orc = self.orc
        if orc <= 0:
            return {b: 0 for b in self.MBK}, 0.0
        add = self.add
        PAR = ('aerialStrength', 'gk1')
        grupos = []
        for b in self.MBK:
            if b in PAR:
                continue
            ids = [i for i in self.MB[b] if i in self.R]
            if not ids:
                grupos.append((b, None, None))
                continue
            g = np.zeros(26)
            for i in ids:
                g += self._ganho(i, add[i])
            nmax = int(np.searchsorted(self.ACCU, orc, side='right'))
            nmax = min(nmax, self.nmax_barra[b] + 1)
            grupos.append((b, self.ACCU[:nmax], g[:nmax]))

        ga = np.zeros(26)
        for i in (7, 14):
            if i in self.R:
                ga += self._ganho(i, add[i])
        gk = self._ganho(21, add[21]) if 21 in self.R else np.zeros(26)
        t13 = self.tab.get(13)

        NEG = -1e18
        dp = np.full(orc + 1, NEG)
        dp[0] = 0.0
        tr = []
        for b, costs, gains in grupos:
            if costs is None:
                tr.append(None)
                continue
            nd = np.full(orc + 1, NEG)
            ch = np.full(orc + 1, -1, dtype=np.int16)
            pc = np.full(orc + 1, -1, dtype=np.int32)
            for n in range(len(costs)):
                cst = int(costs[n])
                if cst > orc:
                    break
                cand = dp[:orc + 1 - cst] + gains[n]
                mask = cand > nd[cst:orc + 1]
                idx = np.nonzero(mask)[0]
                if len(idx):
                    nd[cst + idx] = cand[idx]
                    ch[cst + idx] = n
                    pc[cst + idx] = idx
            tr.append((b, ch, pc))
            dp = nd

        opts = []
        MA = self.nmax_barra['aerialStrength']
        MK = self.nmax_barra['gk1']
        for a in range(MA + 1):
            ca = int(self.ACCU[a])
            if ca > orc:
                break
            for k in range(MK + 1):
                cst = ca + int(self.ACCU[k])
                if cst > orc:
                    break
                val = ga[a] + gk[k]
                if t13 is not None:
                    b1 = min(TETO, self.base[13] + a + k)
                    b0 = min(TETO, self.base[13])
                    vv = _mult(b1, self.m) + add[13]
                    v0 = _mult(b0, self.m) + add[13]
                    if 13 in self.bf:
                        p13, f13 = self.bf[13]
                        vv += math.ceil(b1 * p13 / 100 + f13)
                        v0 += math.ceil(b0 * p13 / 100 + f13)
                    val += t13[min(self.VMAX, max(0, vv))] - t13[min(self.VMAX, max(0, v0))]
                opts.append((cst, val, a, k))

        nd = np.full(orc + 1, NEG)
        ch = np.full(orc + 1, -1, dtype=np.int32)
        pc = np.full(orc + 1, -1, dtype=np.int32)
        for oi, (cst, val, a, k) in enumerate(opts):
            cand = dp[:orc + 1 - cst] + val
            mask = cand > nd[cst:orc + 1]
            idx = np.nonzero(mask)[0]
            if len(idx):
                nd[cst + idx] = cand[idx]
                ch[cst + idx] = oi
                pc[cst + idx] = idx
        tr.append(('PAR', ch, pc, opts))
        dp = nd

        bc = int(np.argmax(dp))
        lvl = {b: 0 for b in self.MBK}
        cc = bc
        for e in reversed(tr):
            if e is None:
                continue
            if e[0] == 'PAR':
                _, ch, pc, opts = e
                if ch[cc] >= 0:
                    cst, val, a, k = opts[ch[cc]]
                    lvl['aerialStrength'] = a
                    lvl['gk1'] = k
                    cc = int(pc[cc])
            else:
                b, ch, pc = e
                if ch[cc] >= 0:
                    lvl[b] = int(ch[cc])
                    cc = int(pc[cc])
        return lvl, float(dp[bc])

    def gasto(self, lvl):
        return int(sum(self.ACCU[lvl.get(b, 0)] for b in self.MBK))

    def sobra_para_o_maior_peso(self, lvl):
        """A regra de ouro do motor: nunca sobra ponto — o resto vai para a barra
        de maior peso que ainda aceita nivel."""
        g = self.orc - self.gasto(lvl)
        if g <= 0:
            return lvl
        pw = {}
        for b in self.MBK:
            pesos = [p for i, a, p in self.arows if i in self.MB[b]]
            pw[b] = max(pesos) if pesos else 0
        for b in sorted(self.MBK, key=lambda x: -pw[x]):
            while lvl.get(b, 0) < min(25, self.nmax_barra[b]):
                cst = int(self.ACCU[lvl.get(b, 0) + 1] - self.ACCU[lvl.get(b, 0)])
                if cst > g:
                    break
                lvl[b] = lvl.get(b, 0) + 1
                g -= cst
            if g <= 0:
                break
        return lvl
