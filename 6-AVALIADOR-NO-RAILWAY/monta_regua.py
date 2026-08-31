# -*- coding: utf-8 -*-
"""Traduz o pacote json da RPC para a Regua, sem inventar nada pelo caminho."""
from regua_do_banco import Regua, ReguaIncompleta

def da_rpc(pac, tatica=None):
    if not pac:
        raise ReguaIncompleta('a RPC otimizador_regua_v2() nao devolveu nada')
    if pac.get('contrato') != 'otimizador_regua_v2':
        raise ReguaIncompleta('versao inesperada do contrato da regua')
    if not (pac.get('gate') or {}).get('pode_rodar'):
        raise ReguaIncompleta('gate do contrato V2 recusou a regua')
    faltou = [k for k in ('parametros','atributos','barras','custo_nivel','multiplicadores',
                          'funcoes','molde','habilidades','tecnicos','impetos','versao_molde')
              if pac.get(k) in (None, {}, [])]
    if faltou:
        raise ReguaIncompleta('o pacote veio sem: ' + ', '.join(faltou))

    tec = {}
    for t in pac['tecnicos']:
        boosts = []
        for b in (t.get('boosts') or []):
            if float(b.get('delta') or 0) != 1.0:
                raise ReguaIncompleta('tecnico %s com delta diferente de +1' % t.get('tecnico_id'))
            boosts.append(int(b['indice_otimizador']))
        tid = int(t['tecnico_id'])
        profs = {str(x['codigo_estilo']): float(x['valor'])
                 for x in (t.get('proficiencias') or [])}
        tec[tid] = {'boosts': boosts,
                    'proficiencia': float(t['proficiencia_maxima']),
                    'proficiencias': profs,
                    'estilos_principais': t.get('estilos_principais') or []}

    habilidades = {}
    for h in pac['habilidades']:
        efeitos = {}
        for e in (h.get('efeitos') or []):
            d = {}
            if e.get('pct'): d['pct'] = float(e['pct'])
            if e.get('flat'): d['flat'] = float(e['flat'])
            if d: efeitos[int(e['indice_otimizador'])] = d
        sid = int(h['skill_id'])
        habilidades[sid] = {'fabricavel': bool(h.get('fabricavel')),
                            'vetada': bool(h.get('vetada')), 'efeito': efeitos}

    impetos,impetos_meta = {},{}
    for impeto in pac.get('impetos') or []:
        codigo = int(impeto['codigo_impeto'])
        efeitos = {int(e['indice_otimizador']): int(e['delta'])
                   for e in (impeto.get('efeitos') or [])}
        impetos[codigo] = efeitos
        impetos_meta[codigo] = {
            'condicional': bool(impeto.get('condicional')),
            'nivel_maximo': impeto.get('nivel_maximo'),
            'efeitos': efeitos,
        }

    molde = {}
    for x in pac['molde']:
        molde.setdefault(int(x['funcao_id']), {})[int(x['indice_otimizador'])] = \
            (float(x['alvo']), int(x['peso']))

    dados = {
      'parametro'    : pac['parametros'],
      'atributo'     : {int(x['indice_otimizador']): x['codigo'] for x in pac['atributos']},
      'barra'        : {k: [int(i) for i in v] for k, v in pac['barras'].items()},
      'custo_nivel'  : {int(k): int(v) for k, v in pac['custo_nivel'].items()},
      'multiplicador': {int(k): float(v) for k, v in pac['multiplicadores'].items()},
      'molde'        : molde,
      'habilidade'   : habilidades,
      'tecnico'      : tec,
      'impeto'       : impetos,
      'impeto_meta'  : impetos_meta,
      'funcoes'      : {int(x['funcao_id']): x for x in pac['funcoes']},
      'skill_names'  : {},
      'gate'         : pac['gate'],
    }
    return Regua(dados, int(pac['versao_molde']))
