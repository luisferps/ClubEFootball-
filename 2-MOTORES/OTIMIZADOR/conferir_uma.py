# -*- coding: utf-8 -*-
"""CONFERIR UMA LINHA — abre a caixa preta de um card x funcao.

Nao grava nada, nao mexe na fila. So imprime o que o motor tem em maos e a
conta que ele faz. Rode dentro de 2-MOTORES (ele acha o config.txt sozinho).
"""
import sys, io, json

CARD = sys.argv[1] if len(sys.argv) > 1 else None
try:
    FUNCAO_ID = int(sys.argv[2]) if len(sys.argv) > 2 else 2
except (TypeError, ValueError):
    print('funcao_id precisa ser um numero canonico'); raise SystemExit(1)
try:
    IMPETO_NIVEL = int(sys.argv[3]) if len(sys.argv) > 3 else None
except (TypeError, ValueError):
    print('nivel do impeto precisa ser um numero'); raise SystemExit(1)

import fonte_unica as FU
import equacao as EQ
import motor as M
import regua as RG

if not CARD:
    print('informe card_id, funcao_id e, se houver, nivel do impeto'); raise SystemExit(1)

c = FU.carta(CARD)
if not c:
    print('carta', CARD, 'nao veio do banco'); raise SystemExit(1)

ins = FU.carrega_tudo()
molde = [r for r in ins['molde'] if int(r['funcao_id']) == FUNCAO_ID]
if not molde:
    print('a funcao_id', FUNCAO_ID, 'nao tem molde'); raise SystemExit(1)

arows = [[r['attr'], r['peso'], r['alvo'], 0, 0, 0] for r in sorted(molde, key=lambda r: r['attr'])]
condicionais = [x for x in c.get('impetos') or [] if x.get('codigo_impeto') is not None and x.get('condicional')]
codigo_condicional = int(condicionais[0]['codigo_impeto']) if condicionais else None
c = FU.aplica_impetos_da_linha(c,codigo_condicional,IMPETO_NIVEL)
c['arows'] = arows
c['raras'] = c.get('raras') or []
if not (c.get('orc') or 0):
    c['falta'] = []

TECS = FU.carrega_tecnicos_do_banco()

print('=' * 78)
print('  card_id %s · funcao_id %s · impeto_id %s · nivel %s'
      % (CARD,FUNCAO_ID,codigo_condicional,IMPETO_NIVEL))
print('  card_id %s' % CARD)
print('=' * 78)
print('orcamento ....... %s   (level_cap %s%s)'
      % (c.get('orc'), c.get('level_cap'), ' ESTIMADO' if c.get('cap_estimado') else ''))
print('nm (impeto) ..... %s' % (c.get('nm') or []))
print('sl (vagas) ...... %s' % (c.get('sl'),))
print('raras ........... %s' % (c.get('raras') or []))
print('fab (nativas) ... %s' % (c.get('fab') or []))
print('falta (pool) .... %s' % (c.get('falta') or []))
print('tecnicos na lista %d' % len(TECS))
print()
print('BASE — os 26 na ordem da casa')
por_indice = {int(x['indice_otimizador']): x for x in (ins.get('atributo') or [])}
NOMES = [(por_indice.get(i) or {}).get('codigo') or str(i) for i in range(26)]
print('  %-3s %-24s %5s %6s %5s' % ('#', 'atributo', 'base', 'alvo', 'peso'))
R = {r[0]: (r[2], r[1]) for r in arows if r[1]}
for i in range(26):
    a, p = R.get(i, (None, 0))
    print('  %-3d %-24s %5s %6s %5s' % (i, NOMES[i][:24], c['base'][i],
          '' if a is None else a, p or ''))
print()
print('MOLDE: %d atributos com peso · soma dos pesos %d'
      % (len(R), sum(p for _, p in R.values())))

b = M.build_completo2(dict(c), TECS, None)
if not b:
    print('build vazia'); raise SystemExit(1)

print()
print('=' * 78)
print('  RESULTADO')
print('=' * 78)
print('b1 .............. %.2f' % b['nota'])
print('tecnico ......... %s  (id %s · tatica %s · m %.5f)'
      % (b.get('tecnico'), b.get('tecnico_id'), b.get('tat'),
         EQ.mult_de(b.get('tat') or 0)))
print('boost do tecnico  %s' % (b.get('boost') or []))
print('impeto fabricado  %s' % (b.get('fab') or []))
print('barras .......... %s' % (b.get('lvl') or {}))
print('habilidades ..... %s' % (b.get('hab') or b.get('habilidades') or []))
print('sobra ........... %s' % b.get('sobra'))
print()
print('VALS FINAIS x ALVO (so os que tem peso)')
vals = b.get('vals') or []
print('  %-3s %-24s %6s %6s %6s %5s' % ('#', 'atributo', 'val', 'alvo', 'delta', 'peso'))
for i in sorted(R):
    a, p = R[i]
    v = vals[i] if i < len(vals) else None
    print('  %-3d %-24s %6s %6s %6s %5s'
          % (i, NOMES[i][:24], v, a, ('' if v is None else round(v - float(a), 1)), p))
print()
print('=' * 78)
