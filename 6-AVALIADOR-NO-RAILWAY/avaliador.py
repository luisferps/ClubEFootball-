# -*- coding: utf-8 -*-
"""
O AVALIADOR — "esta build vale quanto?"

A metade do motor que pode ficar online. Recebe UM estado pronto (barras, impeto,
tecnico+proficiencia, habilidades) e devolve a nota. NAO procura, NAO otimiza.

A conta e a mesma do motor (equacao.py + regua.py), com TODOS os numeros vindos
do banco. Divergir vira impossivel por construcao, e a regua nunca vai ao navegador.

REGRAS
  1. Nenhum literal que mude a nota (fora as leis comprovadas: teto 99 em
     base+barras e proficiencia; piso 40 quando a proficiencia age).
  2. Nenhum default silencioso: falta insumo -> InsumoFaltando com o nome.
"""
import math
from regua_do_banco import Regua, ReguaIncompleta

class InsumoFaltando(Exception):
    pass

TETO = 99      # teto de base+barras e da etapa de proficiencia
PISO = 40      # lei do jogo: com multiplicador agindo, nao cai abaixo de 40


# ------------------------------------------------------------------ a regua
def nota_de(vals, arows, regua):
    """regua.py:notaDe — arows = [(idx, alvo, peso)]."""
    deg  = regua.degraus
    teto = regua.teto_punicao
    pun  = regua.punicao
    if not str(pun.get('incremento','')).startswith('0.25'):
        raise InsumoFaltando('a formula da punicao mudou no banco (%r); este '
                             'avaliador so conhece 0.25*peso/12' % pun.get('incremento'))
    acess_nao_pune = bool(pun.get('acessorio_nao_pune', True))
    s = 0.0
    for idx, alvo, peso in arows:
        if not peso:
            continue
        if idx >= len(vals):
            raise InsumoFaltando('atributo %d fora do vetor de valores' % idx)
        d = vals[idx] - alvo
        if d >= 0:
            k = 1
            while k <= d:
                if k > len(deg): break
                s += deg[k-1] * peso
                k += 1
        else:
            if acess_nao_pune and peso == 1:
                continue
            inc = 0.25 * peso / 12.0
            k, lim = 1, min(-d, teto)
            while k <= lim:
                s -= (1 + (k-1) * inc) * peso
                k += 1
    return round(s * 10) / 10.0


# ------------------------------------------------------------------ a cadeia
def _mult(x, m):
    if m == 1.0:
        return x
    return min(TETO, max(PISO, x + int(x * (m - 1))))


def base_barras(base, lvl, regua):
    v = list(base)
    for b, n in (lvl or {}).items():
        if not n:
            continue
        attrs = regua.barra.get(b)
        if attrs is None:
            raise InsumoFaltando('barra desconhecida: %r' % b)
        for i in attrs:
            v[i] = min(TETO, v[i] + n)
    return v


def buff_de(habs, regua):
    """(pct, flat) por atributo. Comum vencedora inteira, cada perdedora vale a
    fracao que o banco manda; raras somam inteiras por cima."""
    p = regua.p.get('metade_da_habilidade_perdedora')
    if p is None:
        raise InsumoFaltando('regua_parametro.metade_da_habilidade_perdedora')
    fator = float(p['fator'] if isinstance(p, dict) else p)
    pc_com, pc_rar, fl_com, fl_rar = {}, {}, {}, {}
    for h in habs:
        d = regua.hab.get(h)
        if d is None:
            raise InsumoFaltando('habilidade desconhecida: %r' % h)
        ef = d.get('efeito') or {}
        if not ef:
            continue
        rara = not bool(d.get('fabricavel'))
        for i, dd in ef.items():
            i = int(i)
            if 'pct' in dd:  (pc_rar if rara else pc_com).setdefault(i, []).append(dd['pct'])
            else:            (fl_rar if rara else fl_com).setdefault(i, []).append(dd['flat'])
    out = {}
    for i in set(pc_com) | set(pc_rar) | set(fl_com) | set(fl_rar):
        cs = sorted(pc_com.get(i, [0]), reverse=True)
        fs = sorted(fl_com.get(i, [0]), reverse=True)
        pct  = cs[0] + sum(cs[1:]) * fator + sum(pc_rar.get(i, []))
        flat = fs[0] + sum(fs[1:]) * fator + sum(fl_rar.get(i, []))
        if pct or flat:
            out[i] = (pct, flat)
    return out


def cadeia(estado, carta, regua):
    """base -> barras -> proficiencia -> boosts -> impetos -> habilidade.
    A habilidade le a REFERENCIA (base+barras) e soma no fim, sem trava de 99."""
    base = carta.get('atributos')
    if not base:
        raise InsumoFaltando('a carta nao tem os 26 atributos')
    if len(base) != len(regua.attr):
        raise InsumoFaltando('a carta tem %d atributos; o dicionario tem %d'
                             % (len(base), len(regua.attr)))
    etapas = {'base': list(base)}

    lvl = estado.get('barras') or {}
    if any(lvl.values()):
        orc = carta.get('orcamento')
        if orc is None:
            raise InsumoFaltando('a carta nao tem orcamento e o estado pede barras')
        gasto = 0
        for n in lvl.values():
            if not n: continue
            c = regua.custo.get(int(n))
            if c is None:
                raise InsumoFaltando('nivel de barra %r fora da tabela de custo' % n)
            gasto += c
        if gasto > orc:
            raise InsumoFaltando('a build gasta %d pontos e a carta so tem %d' % (gasto, orc))
    ref = base_barras(base, lvl, regua)
    etapas['barras'] = list(ref)

    v = list(ref)
    tid = estado.get('tecnico_id')
    if tid is not None:
        t = regua.tec.get(tid)
        if t is None:
            raise InsumoFaltando('tecnico %r nao esta no catalogo' % tid)
        prof = estado.get('proficiencia')
        if prof is None:
            prof = t.get('proficiencia')
        if prof is None:
            raise InsumoFaltando('o tecnico foi escolhido mas a proficiencia nao veio')
        m = regua.mult.get(int(round(float(prof))))
        if m is None:
            raise InsumoFaltando('proficiencia %r fora da tabela de multiplicador' % prof)
        v = [_mult(x, m) for x in v]
        etapas['proficiencia'] = list(v)
        for i in (t.get('boosts') or []):
            if i is None: continue
            i = int(i)
            if 0 <= i < len(v):
                v[i] = v[i] + 1          # o +1 passa de 99
    etapas['tecnico'] = list(v)

    for imp in (estado.get('impetos') or []):
        efeito = regua.imp.get(int(imp))
        if efeito is None:
            raise InsumoFaltando('impeto %r nao esta no catalogo' % imp)
        for i, d in efeito.items():
            v[int(i)] = v[int(i)] + int(d)
    etapas['impeto'] = list(v)

    buff = estado.get('buff')
    if buff is None:
        buff = buff_de(estado.get('habilidades') or [], regua)
    for i, (pct, flat) in buff.items():
        i = int(i)
        v[i] = v[i] + math.ceil(ref[i] * pct / 100.0 + flat)
    etapas['habilidades'] = list(v)
    return v, etapas


# ------------------------------------------------------------------- a porta
def avalia(estado, carta, funcao_id, regua):
    """A unica funcao que o servico expoe. Devolve nota e etapas —
    NUNCA o alvo, NUNCA o peso, NUNCA a regua."""
    funcao_id = int(funcao_id)
    regua.molde_completo(funcao_id)
    m = regua.molde[funcao_id]
    arows = [(i, m[i][0], m[i][1]) for i in sorted(m)]
    vals, etapas = cadeia(estado, carta, regua)
    return {
        'b1': nota_de(vals, arows, regua),
        'valores': vals,
        'ganho_por_etapa': etapas,
        'versao_molde': regua.versao_molde,
    }
