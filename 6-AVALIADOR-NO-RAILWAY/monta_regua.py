# -*- coding: utf-8 -*-
"""Traduz o pacote json da RPC para a Regua, sem inventar nada pelo caminho."""
from regua_do_banco import Regua, ReguaIncompleta

def da_rpc(pac, tatica=None):
    if not pac:
        raise ReguaIncompleta('a RPC regua_pacote() nao devolveu nada')
    faltou = [k for k in ('parametro','atributo','barra','custo_nivel','multiplicador',
                          'ordem_boost','molde','habilidade','tecnico','impeto',
                          'versao_molde') if pac.get(k) in (None, {}, [])]
    if faltou:
        raise ReguaIncompleta('o pacote veio sem: ' + ', '.join(faltou))

    ordem = {int(k): int(v) for k, v in pac['ordem_boost'].items()}
    tec = {}
    for tid, t in pac['tecnico'].items():
        prof = t.get('proficiencias') or {}
        if tatica and tatica in prof:      v = prof[tatica]
        elif prof:                          v = max(prof.values())
        else:                               v = None
        boosts = []
        for b in (t.get('boosts') or []):
            b = int(b)
            if b not in ordem:
                raise ReguaIncompleta('tecnico %s com boost %d fora da ordem do efHub' % (tid, b))
            boosts.append(ordem[b])
        tec[int(tid)] = {'boosts': boosts, 'proficiencia': v}

    dados = {
      'parametro'    : pac['parametro'],
      'atributo'     : {int(k): v for k, v in pac['atributo'].items()},
      'barra'        : {k: [int(i) for i in v] for k, v in pac['barra'].items()},
      'custo_nivel'  : {int(k): int(v) for k, v in pac['custo_nivel'].items()},
      'multiplicador': {int(k): float(v) for k, v in pac['multiplicador'].items()},
      'ordem_boost'  : ordem,
      'molde'        : {f: {int(i): (float(av[0]), int(av[1])) for i, av in m.items()}
                        for f, m in pac['molde'].items()},
      'habilidade'   : pac['habilidade'],
      'tecnico'      : tec,
      'impeto'       : {int(k): {int(i): int(d) for i, d in v.items()}
                        for k, v in pac['impeto'].items()},
    }
    return Regua(dados, int(pac['versao_molde']))
